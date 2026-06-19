"""PyTorch Actor-Critic 网络：NatureCNN 编码器 + 策略头 + 价值头。

输入：堆叠帧 (N, C, H, W) uint8（C = frame_stack * 通道数）。
内部归一化 /255。端到端纯视觉，无任何手工特征。
"""
from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
from torch.distributions import Categorical


def _orthogonal(layer: nn.Module, gain: float = np.sqrt(2)) -> nn.Module:
    nn.init.orthogonal_(layer.weight, gain)
    if getattr(layer, "bias", None) is not None:
        nn.init.constant_(layer.bias, 0.0)
    return layer


class ActorCritic(nn.Module):
    def __init__(self, obs_shape, n_actions: int):
        super().__init__()
        c, h, w = obs_shape
        self.encoder = nn.Sequential(
            _orthogonal(nn.Conv2d(c, 32, 8, stride=4)), nn.ReLU(),
            _orthogonal(nn.Conv2d(32, 64, 4, stride=2)), nn.ReLU(),
            _orthogonal(nn.Conv2d(64, 64, 3, stride=1)), nn.ReLU(),
            nn.Flatten(),
        )
        with torch.no_grad():
            flat = self.encoder(torch.zeros(1, c, h, w)).shape[1]
        self.fc = nn.Sequential(_orthogonal(nn.Linear(flat, 512)), nn.ReLU())
        self.policy = _orthogonal(nn.Linear(512, n_actions), gain=0.01)
        self.value = _orthogonal(nn.Linear(512, 1), gain=1.0)

    def _features(self, obs: torch.Tensor) -> torch.Tensor:
        x = obs.float() / 255.0
        return self.fc(self.encoder(x))

    def forward(self, obs: torch.Tensor):
        feat = self._features(obs)
        return self.policy(feat), self.value(feat).squeeze(-1)

    @torch.no_grad()
    def act(self, obs: torch.Tensor):
        """采样动作，返回 (action, logprob, value)。用于收集 rollout。"""
        logits, value = self.forward(obs)
        dist = Categorical(logits=logits)
        action = dist.sample()
        return action, dist.log_prob(action), value

    def evaluate(self, obs: torch.Tensor, actions: torch.Tensor):
        """对给定动作求 (logprob, entropy, value)。用于 PPO 更新。"""
        logits, value = self.forward(obs)
        dist = Categorical(logits=logits)
        return dist.log_prob(actions), dist.entropy(), value
