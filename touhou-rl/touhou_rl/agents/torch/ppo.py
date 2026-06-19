"""PyTorch PPO 训练循环（单环境，端到端纯视觉）。

这是「开始训练」要调用的入口。脚手架已就绪、可直接运行；本仓库默认不替你启动。

    from touhou_rl.config import load_config
    from touhou_rl.agents.torch.ppo import train
    train(load_config("configs/sim.yaml"))
"""
from __future__ import annotations

import os

import numpy as np
import torch
import torch.nn as nn

from ...config import Config, to_dict
from ...common.logger import Logger
from ...common.utils import resolve_torch_device, set_global_seed
from ...envs import make_env
from .networks import ActorCritic
from .rollout import RolloutBuffer


def train(cfg: Config) -> None:
    set_global_seed(cfg.run.seed)
    device = resolve_torch_device(cfg.run.device)
    print(f"[torch-ppo] device = {device}")

    env = make_env(cfg.env)
    obs_shape = env.observation_space.shape
    n_actions = env.action_space.n

    agent = ActorCritic(obs_shape, n_actions).to(device)
    optimizer = torch.optim.Adam(agent.parameters(), lr=cfg.ppo.lr, eps=1e-5)
    buffer = RolloutBuffer(cfg.ppo.rollout_steps, obs_shape, device)

    logger = Logger(cfg.run.log_dir, cfg.run.exp_name)
    logger.save_config(to_dict(cfg))
    os.makedirs(cfg.run.save_dir, exist_ok=True)

    obs_np, _ = env.reset(seed=cfg.run.seed)
    obs = torch.as_tensor(obs_np, device=device)
    done = False

    num_updates = cfg.ppo.total_steps // cfg.ppo.rollout_steps
    global_step = 0
    ep_return, ep_len = 0.0, 0
    recent_returns: list = []

    for update in range(1, num_updates + 1):
        if cfg.ppo.anneal_lr:
            frac = 1.0 - (update - 1) / num_updates
            for g in optimizer.param_groups:
                g["lr"] = frac * cfg.ppo.lr

        # ---- 收集 rollout ----
        buffer.reset()
        for _ in range(cfg.ppo.rollout_steps):
            with torch.no_grad():
                action, logprob, value = agent.act(obs.unsqueeze(0))
            action_i = int(action.item())
            next_obs_np, reward, terminated, truncated, info = env.step(action_i)
            done = terminated or truncated

            buffer.add(obs, action_i, logprob.squeeze(0), float(reward), done, value.squeeze(0))
            global_step += 1
            ep_return += reward
            ep_len += 1

            obs = torch.as_tensor(next_obs_np, device=device)
            if done:
                recent_returns.append(ep_return)
                recent_returns = recent_returns[-50:]
                ep_return, ep_len = 0.0, 0
                obs_np, _ = env.reset()
                obs = torch.as_tensor(obs_np, device=device)

        # ---- bootstrap + GAE ----
        with torch.no_grad():
            _, last_value = agent.forward(obs.unsqueeze(0))
        returns, advantages = buffer.compute_gae(
            last_value.squeeze(0), done, cfg.ppo.gamma, cfg.ppo.gae_lambda
        )

        # ---- PPO 更新 ----
        b_obs = buffer.obs
        b_actions = buffer.actions
        b_logprobs = buffer.logprobs
        b_returns = returns
        b_advantages = advantages
        b_values = buffer.values

        idx = np.arange(cfg.ppo.rollout_steps)
        pg_loss = v_loss = ent = 0.0
        for _ in range(cfg.ppo.num_epochs):
            np.random.shuffle(idx)
            for start in range(0, cfg.ppo.rollout_steps, cfg.ppo.minibatch_size):
                mb = idx[start:start + cfg.ppo.minibatch_size]
                mb_t = torch.as_tensor(mb, device=device)

                new_logprob, entropy, new_value = agent.evaluate(b_obs[mb_t], b_actions[mb_t])
                ratio = (new_logprob - b_logprobs[mb_t]).exp()

                adv = b_advantages[mb_t]
                if cfg.ppo.norm_adv:
                    adv = (adv - adv.mean()) / (adv.std() + 1e-8)

                pg1 = -adv * ratio
                pg2 = -adv * torch.clamp(ratio, 1 - cfg.ppo.clip_coef, 1 + cfg.ppo.clip_coef)
                policy_loss = torch.max(pg1, pg2).mean()
                value_loss = 0.5 * (new_value - b_returns[mb_t]).pow(2).mean()
                entropy_loss = entropy.mean()
                loss = policy_loss - cfg.ppo.ent_coef * entropy_loss + cfg.ppo.vf_coef * value_loss

                optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(agent.parameters(), cfg.ppo.max_grad_norm)
                optimizer.step()

                pg_loss, v_loss, ent = policy_loss.item(), value_loss.item(), entropy_loss.item()

        if update % cfg.run.log_every_updates == 0:
            mean_ret = float(np.mean(recent_returns)) if recent_returns else float("nan")
            logger.log(global_step, {
                "update": update,
                "ep_return_mean50": mean_ret,
                "policy_loss": pg_loss,
                "value_loss": v_loss,
                "entropy": ent,
                "lr": optimizer.param_groups[0]["lr"],
            })

        if update % cfg.run.save_every_updates == 0:
            path = os.path.join(cfg.run.save_dir, f"{cfg.run.exp_name}_u{update}.pt")
            torch.save({"model": agent.state_dict(), "update": update}, path)
            print(f"[torch-ppo] 保存检查点 -> {path}")

    env.close()
    logger.close()
