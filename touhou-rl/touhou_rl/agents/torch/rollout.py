"""单环境 rollout 缓冲 + GAE 优势估计（PyTorch）。"""
from __future__ import annotations

import numpy as np
import torch


class RolloutBuffer:
    def __init__(self, steps: int, obs_shape, device):
        self.steps = steps
        self.device = device
        self.obs = torch.zeros((steps, *obs_shape), dtype=torch.uint8, device=device)
        self.actions = torch.zeros(steps, dtype=torch.long, device=device)
        self.logprobs = torch.zeros(steps, device=device)
        self.rewards = torch.zeros(steps, device=device)
        self.dones = torch.zeros(steps, device=device)
        self.values = torch.zeros(steps, device=device)
        self.ptr = 0

    def add(self, obs, action, logprob, reward, done, value):
        i = self.ptr
        self.obs[i] = obs
        self.actions[i] = action
        self.logprobs[i] = logprob
        self.rewards[i] = reward
        self.dones[i] = float(done)
        self.values[i] = value
        self.ptr += 1

    def reset(self):
        self.ptr = 0

    def compute_gae(self, last_value, last_done, gamma: float, gae_lambda: float):
        """返回 (returns, advantages)，形状 [steps]。"""
        advantages = torch.zeros(self.steps, device=self.device)
        last_gae = 0.0
        for t in reversed(range(self.steps)):
            if t == self.steps - 1:
                next_nonterminal = 1.0 - float(last_done)
                next_value = last_value
            else:
                next_nonterminal = 1.0 - self.dones[t + 1]
                next_value = self.values[t + 1]
            delta = self.rewards[t] + gamma * next_value * next_nonterminal - self.values[t]
            last_gae = delta + gamma * gae_lambda * next_nonterminal * last_gae
            advantages[t] = last_gae
        returns = advantages + self.values
        return returns, advantages
