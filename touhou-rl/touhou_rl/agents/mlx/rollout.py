"""向量化 rollout 缓冲 + GAE（MLX 版，缓冲用 numpy，更新时转 mx.array）。

形状 [steps, num_envs, ...]，与 PyTorch 版约定一致（CleanRL 风格）。
MLX 统一内存下 numpy <-> mx.array 转换开销小，故缓冲保持 numpy 简单可靠。
"""
from __future__ import annotations

import numpy as np


class RolloutBuffer:
    def __init__(self, steps: int, num_envs: int, obs_shape):
        self.steps = steps
        self.num_envs = num_envs
        self.obs = np.zeros((steps, num_envs, *obs_shape), dtype=np.uint8)
        self.actions = np.zeros((steps, num_envs), dtype=np.int32)
        self.logprobs = np.zeros((steps, num_envs), dtype=np.float32)
        self.rewards = np.zeros((steps, num_envs), dtype=np.float32)
        self.dones = np.zeros((steps, num_envs), dtype=np.float32)
        self.values = np.zeros((steps, num_envs), dtype=np.float32)

    def compute_gae(self, last_value, last_done, gamma: float, gae_lambda: float):
        """向量化 GAE。

        last_value / last_done: 形状 [num_envs]。
        返回 (returns, advantages)，形状均为 [steps, num_envs]。
        """
        last_value = np.asarray(last_value, dtype=np.float32)
        last_done = np.asarray(last_done, dtype=np.float32)
        advantages = np.zeros_like(self.rewards)
        last_gae = np.zeros(self.num_envs, dtype=np.float32)
        for t in reversed(range(self.steps)):
            if t == self.steps - 1:
                next_nonterminal = 1.0 - last_done
                next_value = last_value
            else:
                next_nonterminal = 1.0 - self.dones[t + 1]
                next_value = self.values[t + 1]
            delta = self.rewards[t] + gamma * next_value * next_nonterminal - self.values[t]
            last_gae = delta + gamma * gae_lambda * next_nonterminal * last_gae
            advantages[t] = last_gae
        returns = advantages + self.values
        return returns, advantages
