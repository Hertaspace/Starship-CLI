"""单环境 rollout 缓冲 + GAE（MLX 版，缓冲用 numpy，更新时转 mx.array）。

MLX 是统一内存，numpy <-> mx.array 转换开销小，因此缓冲保持 numpy 简单可靠。
"""
from __future__ import annotations

import numpy as np


class RolloutBuffer:
    def __init__(self, steps: int, obs_shape):
        self.steps = steps
        self.obs = np.zeros((steps, *obs_shape), dtype=np.uint8)
        self.actions = np.zeros(steps, dtype=np.int32)
        self.logprobs = np.zeros(steps, dtype=np.float32)
        self.rewards = np.zeros(steps, dtype=np.float32)
        self.dones = np.zeros(steps, dtype=np.float32)
        self.values = np.zeros(steps, dtype=np.float32)
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

    def compute_gae(self, last_value: float, last_done: bool, gamma: float, gae_lambda: float):
        advantages = np.zeros(self.steps, dtype=np.float32)
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
