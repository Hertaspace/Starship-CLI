"""PyTorch PPO 训练循环（向量化多环境，端到端纯视觉）。

用 N 个并行环境采集经验，再展平成一个大 batch 做 PPO 更新。
这是「开始训练」要调用的入口；脚手架已就绪、可直接运行。

    from touhou_rl.config import load_config
    from touhou_rl.agents.torch.ppo import train
    train(load_config("configs/sim.yaml"))
"""
from __future__ import annotations

import os
import time

import numpy as np
import torch
import torch.nn as nn

from ...config import Config, to_dict
from ...common.logger import Logger
from ...common.utils import resolve_torch_device, set_global_seed
from ...envs import make_vector_env
from .networks import ActorCritic
from .rollout import RolloutBuffer


def train(cfg: Config) -> None:
    set_global_seed(cfg.run.seed)
    device = resolve_torch_device(cfg.run.device)

    num_envs = cfg.ppo.num_envs if cfg.env.kind != "real" else 1
    envs = make_vector_env(cfg.env, num_envs=num_envs, async_mode=cfg.ppo.async_envs)
    num_envs = envs.num_envs  # 真实游戏会被强制为 1
    obs_shape = envs.single_observation_space.shape
    n_actions = envs.single_action_space.n
    print(f"[torch-ppo] device={device} num_envs={num_envs} "
          f"({'async' if cfg.ppo.async_envs and num_envs > 1 else 'sync'})")

    agent = ActorCritic(obs_shape, n_actions).to(device)
    optimizer = torch.optim.Adam(agent.parameters(), lr=cfg.ppo.lr, eps=1e-5)
    buffer = RolloutBuffer(cfg.ppo.rollout_steps, num_envs, obs_shape, device)

    logger = Logger(cfg.run.log_dir, cfg.run.exp_name)
    logger.save_config(to_dict(cfg))
    os.makedirs(cfg.run.save_dir, exist_ok=True)

    batch_size = cfg.ppo.rollout_steps * num_envs
    minibatch_size = min(cfg.ppo.minibatch_size, batch_size)
    steps_per_update = batch_size
    num_updates = cfg.ppo.total_steps // steps_per_update

    next_obs = torch.as_tensor(envs.reset(seed=cfg.run.seed)[0], device=device)
    next_done = torch.zeros(num_envs, device=device)
    global_step = 0
    ep_returns = np.zeros(num_envs, dtype=np.float64)
    ep_lengths = np.zeros(num_envs, dtype=np.int64)
    recent_returns: list = []
    recent_lengths: list = []
    t_start = time.time()

    for update in range(1, num_updates + 1):
        if cfg.ppo.anneal_lr:
            frac = 1.0 - (update - 1) / num_updates
            for g in optimizer.param_groups:
                g["lr"] = frac * cfg.ppo.lr

        # ---- 采集 rollout（向量化）----
        for t in range(cfg.ppo.rollout_steps):
            buffer.obs[t] = next_obs
            buffer.dones[t] = next_done
            with torch.no_grad():
                action, logprob, value = agent.act(next_obs)
            buffer.actions[t] = action
            buffer.logprobs[t] = logprob
            buffer.values[t] = value

            obs_np, reward, terminated, truncated, infos = envs.step(action.cpu().numpy())
            done = np.logical_or(terminated, truncated)
            buffer.rewards[t] = torch.as_tensor(reward, device=device)

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

            next_obs = torch.as_tensor(obs_np, device=device)
            next_done = torch.as_tensor(done.astype(np.float32), device=device)

        # ---- bootstrap + GAE ----
        with torch.no_grad():
            _, last_value = agent.forward(next_obs)
        returns, advantages = buffer.compute_gae(
            last_value, next_done, cfg.ppo.gamma, cfg.ppo.gae_lambda
        )

        # ---- 展平 [steps, num_envs, ...] -> [batch, ...] ----
        b_obs = buffer.obs.reshape((-1, *obs_shape))
        b_actions = buffer.actions.reshape(-1)
        b_logprobs = buffer.logprobs.reshape(-1)
        b_returns = returns.reshape(-1)
        b_advantages = advantages.reshape(-1)

        # ---- PPO 更新 ----
        idx = np.arange(batch_size)
        pg_loss = v_loss = ent = clipfrac = 0.0
        for _ in range(cfg.ppo.num_epochs):
            np.random.shuffle(idx)
            for start in range(0, batch_size, minibatch_size):
                mb = torch.as_tensor(idx[start:start + minibatch_size], device=device)
                new_logprob, entropy, new_value = agent.evaluate(b_obs[mb], b_actions[mb])
                logratio = new_logprob - b_logprobs[mb]
                ratio = logratio.exp()

                adv = b_advantages[mb]
                if cfg.ppo.norm_adv:
                    adv = (adv - adv.mean()) / (adv.std() + 1e-8)

                pg1 = -adv * ratio
                pg2 = -adv * torch.clamp(ratio, 1 - cfg.ppo.clip_coef, 1 + cfg.ppo.clip_coef)
                policy_loss = torch.max(pg1, pg2).mean()
                value_loss = 0.5 * (new_value - b_returns[mb]).pow(2).mean()
                entropy_loss = entropy.mean()
                loss = policy_loss - cfg.ppo.ent_coef * entropy_loss + cfg.ppo.vf_coef * value_loss

                optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(agent.parameters(), cfg.ppo.max_grad_norm)
                optimizer.step()

                with torch.no_grad():
                    clipfrac = ((ratio - 1.0).abs() > cfg.ppo.clip_coef).float().mean().item()
                pg_loss, v_loss, ent = policy_loss.item(), value_loss.item(), entropy_loss.item()

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
                "entropy": ent,
                "clipfrac": clipfrac,
                "lr": optimizer.param_groups[0]["lr"],
                "sps": sps,
            })

        if update % cfg.run.save_every_updates == 0:
            path = os.path.join(cfg.run.save_dir, f"{cfg.run.exp_name}_u{update}.pt")
            torch.save({"model": agent.state_dict(), "update": update}, path)
            print(f"[torch-ppo] 保存检查点 -> {path}")

    envs.close()
    logger.close()
