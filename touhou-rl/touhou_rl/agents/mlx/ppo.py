"""MLX PPO 训练循环（Apple Silicon GPU，向量化多环境，端到端纯视觉）。

与 PyTorch 版逻辑一一对应：N 个并行环境采集 → 展平成大 batch → PPO 更新。

    from touhou_rl.config import load_config
    from touhou_rl.agents.mlx.ppo import train
    train(load_config("configs/sim.yaml"))
"""
from __future__ import annotations

import os
import time

import numpy as np
import mlx.core as mx
import mlx.nn as nn
import mlx.optimizers as optim

from ...config import Config, to_dict
from ...common.logger import Logger
from ...common.utils import set_global_seed
from ...envs import make_vector_env
from .networks import ActorCritic, action_log_probs, entropy, sample_action
from .rollout import RolloutBuffer


def _resolve_device(pref: str):
    if pref == "cpu":
        return mx.cpu
    return mx.gpu  # Apple Silicon 默认 GPU；auto/gpu/mps 都走这里


def train(cfg: Config) -> None:
    set_global_seed(cfg.run.seed)
    mx.random.seed(cfg.run.seed)
    mx.set_default_device(_resolve_device(cfg.run.device))

    num_envs = cfg.ppo.num_envs if cfg.env.kind != "real" else 1
    envs = make_vector_env(cfg.env, num_envs=num_envs, async_mode=cfg.ppo.async_envs)
    num_envs = envs.num_envs
    obs_shape = envs.single_observation_space.shape
    n_actions = envs.single_action_space.n
    print(f"[mlx-ppo] num_envs={num_envs} "
          f"({'async' if cfg.ppo.async_envs and num_envs > 1 else 'sync'})")

    agent = ActorCritic(obs_shape, n_actions)
    mx.eval(agent.parameters())
    optimizer = optim.Adam(learning_rate=cfg.ppo.lr, eps=1e-5)
    buffer = RolloutBuffer(cfg.ppo.rollout_steps, num_envs, obs_shape)

    logger = Logger(cfg.run.log_dir, cfg.run.exp_name)
    logger.save_config(to_dict(cfg))
    os.makedirs(cfg.run.save_dir, exist_ok=True)

    batch_size = cfg.ppo.rollout_steps * num_envs
    minibatch_size = min(cfg.ppo.minibatch_size, batch_size)
    num_updates = cfg.ppo.total_steps // batch_size

    def loss_fn(model, obs, actions, old_logp, returns, adv):
        logits, value = model(obs)
        new_logp = action_log_probs(logits, actions)
        ratio = mx.exp(new_logp - old_logp)
        if cfg.ppo.norm_adv:
            adv = (adv - adv.mean()) / (adv.std() + 1e-8)
        pg1 = -adv * ratio
        pg2 = -adv * mx.clip(ratio, 1 - cfg.ppo.clip_coef, 1 + cfg.ppo.clip_coef)
        policy_loss = mx.maximum(pg1, pg2).mean()
        value_loss = 0.5 * mx.square(value - returns).mean()
        ent = entropy(logits).mean()
        loss = policy_loss - cfg.ppo.ent_coef * ent + cfg.ppo.vf_coef * value_loss
        return loss, (policy_loss, value_loss, ent)

    loss_and_grad = nn.value_and_grad(agent, loss_fn)

    next_obs = envs.reset(seed=cfg.run.seed)[0]            # [N, *obs_shape] uint8
    next_done = np.zeros(num_envs, dtype=np.float32)
    global_step = 0
    ep_returns = np.zeros(num_envs, dtype=np.float64)
    ep_lengths = np.zeros(num_envs, dtype=np.int64)
    recent_returns: list = []
    recent_lengths: list = []
    t_start = time.time()

    for update in range(1, num_updates + 1):
        if cfg.ppo.anneal_lr:
            frac = 1.0 - (update - 1) / num_updates
            optimizer.learning_rate = frac * cfg.ppo.lr

        # ---- 采集 rollout（向量化）----
        for t in range(cfg.ppo.rollout_steps):
            buffer.obs[t] = next_obs
            buffer.dones[t] = next_done

            obs_mx = mx.array(next_obs)
            logits, value = agent(obs_mx)
            action = sample_action(logits)
            logp = action_log_probs(logits, action)
            mx.eval(action, logp, value)

            action_np = np.asarray(action)
            buffer.actions[t] = action_np
            buffer.logprobs[t] = np.asarray(logp)
            buffer.values[t] = np.asarray(value)

            obs_np, reward, terminated, truncated, infos = envs.step(action_np)
            done = np.logical_or(terminated, truncated)
            buffer.rewards[t] = reward

            global_step += num_envs
            ep_returns += reward
            ep_lengths += 1
            for i in range(num_envs):
                if done[i]:
                    recent_returns.append(ep_returns[i])
                    recent_lengths.append(int(ep_lengths[i]))
                    ep_returns[i] = 0.0
                    ep_lengths[i] = 0
            recent_returns = recent_returns[-100:]
            recent_lengths = recent_lengths[-100:]

            next_obs = obs_np
            next_done = done.astype(np.float32)

        # ---- bootstrap + GAE ----
        _, last_value = agent(mx.array(next_obs))
        mx.eval(last_value)
        returns_np, adv_np = buffer.compute_gae(
            np.asarray(last_value), next_done, cfg.ppo.gamma, cfg.ppo.gae_lambda
        )

        # ---- 展平 [steps, num_envs, ...] -> [batch, ...] ----
        b_obs = buffer.obs.reshape((-1, *obs_shape))
        b_actions = buffer.actions.reshape(-1)
        b_logprobs = buffer.logprobs.reshape(-1)
        b_returns = returns_np.reshape(-1)
        b_advantages = adv_np.reshape(-1)

        # ---- PPO 更新 ----
        idx = np.arange(batch_size)
        pg_loss = v_loss = ent_val = 0.0
        for _ in range(cfg.ppo.num_epochs):
            np.random.shuffle(idx)
            for start in range(0, batch_size, minibatch_size):
                mb = idx[start:start + minibatch_size]
                obs_mb = mx.array(b_obs[mb])
                act_mb = mx.array(b_actions[mb])
                logp_mb = mx.array(b_logprobs[mb])
                ret_mb = mx.array(b_returns[mb])
                adv_mb = mx.array(b_advantages[mb])

                (loss, aux), grads = loss_and_grad(agent, obs_mb, act_mb, logp_mb, ret_mb, adv_mb)
                grads = optim.clip_grad_norm(grads, cfg.ppo.max_grad_norm)[0]
                optimizer.update(agent, grads)
                mx.eval(agent.parameters(), optimizer.state)
                pg_loss, v_loss, ent_val = float(aux[0].item()), float(aux[1].item()), float(aux[2].item())

        if update % cfg.run.log_every_updates == 0:
            sps = int(global_step / (time.time() - t_start))
            mean_ret = float(np.mean(recent_returns)) if recent_returns else float("nan")
            mean_len = float(np.mean(recent_lengths)) if recent_lengths else float("nan")
            logger.log(global_step, {
                "update": update,
                "ep_return_mean": mean_ret,
                "ep_len_mean": mean_len,
                "policy_loss": pg_loss,
                "value_loss": v_loss,
                "entropy": ent_val,
                "lr": float(optimizer.learning_rate),
                "sps": sps,
            })

        if update % cfg.run.save_every_updates == 0:
            path = os.path.join(cfg.run.save_dir, f"{cfg.run.exp_name}_u{update}.safetensors")
            agent.save_weights(path)
            print(f"[mlx-ppo] 保存检查点 -> {path}")

    envs.close()
    logger.close()
