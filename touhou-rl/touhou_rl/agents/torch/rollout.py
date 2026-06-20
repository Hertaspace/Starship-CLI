"""向量化 rollout 缓冲 + GAE（PyTorch）。

形状约定为 [steps, num_envs, ...]（CleanRL 风格）。dones[t] 表示「obs[t] 是否为
某回合的首帧」（即上一步是否终止），GAE 用它切断跨回合的自举。
"""
from __future__ import annotations

import torch


class RolloutBuffer:
    def __init__(self, steps: int, num_envs: int, obs_shape, device):
        self.steps = steps
        self.num_envs = num_envs
        self.device = device
        self.obs = torch.zeros((steps, num_envs, *obs_shape), dtype=torch.uint8, device=device)
        self.actions = torch.zeros((steps, num_envs), dtype=torch.long, device=device)
        self.logprobs = torch.zeros((steps, num_envs), device=device)
        self.rewards = torch.zeros((steps, num_envs), device=device)
        self.dones = torch.zeros((steps, num_envs), device=device)
        self.values = torch.zeros((steps, num_envs), device=device)

    def compute_gae(self, last_value, last_done, gamma: float, gae_lambda: float):
        """向量化 GAE。

        last_value: [num_envs]  —— rollout 结束后 next_obs 的价值估计。
        last_done : [num_envs]  —— next_obs 是否为新回合首帧。
        返回 (returns, advantages)，形状均为 [steps, num_envs]。
        """
        advantages = torch.zeros_like(self.rewards)
        last_gae = torch.zeros(self.num_envs, device=self.device)
        for t in reversed(range(self.steps)):
            if t == self.steps - 1:
                next_nonterminal = 1.0 - last_done.float()
                next_value = last_value
            else:
                next_nonterminal = 1.0 - self.dones[t + 1]
                next_value = self.values[t + 1]
            delta = self.rewards[t] + gamma * next_value * next_nonterminal - self.values[t]
            last_gae = delta + gamma * gae_lambda * next_nonterminal * last_gae
            advantages[t] = last_gae
        returns = advantages + self.values
        return returns, advantages
