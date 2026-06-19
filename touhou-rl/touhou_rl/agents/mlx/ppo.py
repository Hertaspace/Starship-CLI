"""MLX PPO 训练循环（Apple Silicon GPU，单环境，端到端纯视觉）。

与 PyTorch 版逻辑一一对应，便于横向对比。入口：

    from touhou_rl.config import load_config
    from touhou_rl.agents.mlx.ppo import train
    train(load_config("configs/sim.yaml"))
"""
from __future__ import annotations

import os

import numpy as np
import mlx.core as mx
import mlx.nn as nn
import mlx.optimizers as optim

from ...config import Config, to_dict
from ...common.logger import Logger
from ...common.utils import set_global_seed
from ...envs import make_env
from .networks import ActorCritic, action_log_probs, entropy, sample_action
from .rollout import RolloutBuffer


def _resolve_device(pref: str):
    if pref in ("cpu",):
        return mx.cpu
    # MLX 在 Apple Silicon 上默认 gpu；auto/gpu/mps 都走 gpu。
    return mx.gpu


def train(cfg: Config) -> None:
    set_global_seed(cfg.run.seed)
    mx.random.seed(cfg.run.seed)
    device = _resolve_device(cfg.run.device)
    mx.set_default_device(device)
    print(f"[mlx-ppo] device = {device}")

    env = make_env(cfg.env)
    obs_shape = env.observation_space.shape
    n_actions = env.action_space.n

    agent = ActorCritic(obs_shape, n_actions)
    mx.eval(agent.parameters())
    optimizer = optim.Adam(learning_rate=cfg.ppo.lr, eps=1e-5)
    buffer = RolloutBuffer(cfg.ppo.rollout_steps, obs_shape)

    logger = Logger(cfg.run.log_dir, cfg.run.exp_name)
    logger.save_config(to_dict(cfg))
    os.makedirs(cfg.run.save_dir, exist_ok=True)

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

    obs_np, _ = env.reset(seed=cfg.run.seed)
    done = False
    num_updates = cfg.ppo.total_steps // cfg.ppo.rollout_steps
    global_step = 0
    ep_return = 0.0
    recent_returns: list = []

    for update in range(1, num_updates + 1):
        if cfg.ppo.anneal_lr:
            frac = 1.0 - (update - 1) / num_updates
            optimizer.learning_rate = frac * cfg.ppo.lr

        # ---- 收集 rollout ----
        buffer.reset()
        for _ in range(cfg.ppo.rollout_steps):
            obs_mx = mx.array(obs_np[None].astype(np.uint8))
            logits, value = agent(obs_mx)
            action = sample_action(logits)
            logp = action_log_probs(logits, action)
            mx.eval(action, logp, value)

            action_i = int(action.item())
            next_obs_np, reward, terminated, truncated, info = env.step(action_i)
            done = terminated or truncated

            buffer.add(obs_np, action_i, float(logp.item()), float(reward), done, float(value.item()))
            global_step += 1
            ep_return += reward
            obs_np = next_obs_np
            if done:
                recent_returns.append(ep_return)
                recent_returns = recent_returns[-50:]
                ep_return = 0.0
                obs_np, _ = env.reset()

        # ---- bootstrap + GAE ----
        last_obs = mx.array(obs_np[None].astype(np.uint8))
        _, last_value = agent(last_obs)
        mx.eval(last_value)
        returns_np, adv_np = buffer.compute_gae(
            float(last_value.item()), done, cfg.ppo.gamma, cfg.ppo.gae_lambda
        )

        # ---- PPO 更新 ----
        idx = np.arange(cfg.ppo.rollout_steps)
        pg_loss = v_loss = ent_val = 0.0
        for _ in range(cfg.ppo.num_epochs):
            np.random.shuffle(idx)
            for start in range(0, cfg.ppo.rollout_steps, cfg.ppo.minibatch_size):
                mb = idx[start:start + cfg.ppo.minibatch_size]
                obs_mb = mx.array(buffer.obs[mb])
                act_mb = mx.array(buffer.actions[mb])
                logp_mb = mx.array(buffer.logprobs[mb])
                ret_mb = mx.array(returns_np[mb])
                adv_mb = mx.array(adv_np[mb])

                (loss, aux), grads = loss_and_grad(agent, obs_mb, act_mb, logp_mb, ret_mb, adv_mb)
                grads = optim.clip_grad_norm(grads, cfg.ppo.max_grad_norm)[0]
                optimizer.update(agent, grads)
                mx.eval(agent.parameters(), optimizer.state)
                pg_loss, v_loss, ent_val = (float(aux[0].item()), float(aux[1].item()), float(aux[2].item()))

        if update % cfg.run.log_every_updates == 0:
            mean_ret = float(np.mean(recent_returns)) if recent_returns else float("nan")
            logger.log(global_step, {
                "update": update,
                "ep_return_mean50": mean_ret,
                "policy_loss": pg_loss,
                "value_loss": v_loss,
                "entropy": ent_val,
                "lr": float(optimizer.learning_rate),
            })

        if update % cfg.run.save_every_updates == 0:
            path = os.path.join(cfg.run.save_dir, f"{cfg.run.exp_name}_u{update}.safetensors")
            agent.save_weights(path)
            print(f"[mlx-ppo] 保存检查点 -> {path}")

    env.close()
    logger.close()
