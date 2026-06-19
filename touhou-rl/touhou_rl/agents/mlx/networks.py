"""MLX Actor-Critic 网络（Apple Silicon GPU）。

与 PyTorch 版结构一致：NatureCNN 编码器 + 策略头 + 价值头。
注意 MLX 卷积使用 NHWC 布局，而环境给的观测是 (C, H, W)，需在内部转置。
"""
from __future__ import annotations

import mlx.core as mx
import mlx.nn as nn


def _conv_out(size: int, kernel: int, stride: int) -> int:
    return (size - kernel) // stride + 1


class ActorCritic(nn.Module):
    def __init__(self, obs_shape, n_actions: int):
        super().__init__()
        c, h, w = obs_shape
        self.conv1 = nn.Conv2d(c, 32, 8, stride=4)
        self.conv2 = nn.Conv2d(32, 64, 4, stride=2)
        self.conv3 = nn.Conv2d(64, 64, 3, stride=1)

        h1, w1 = _conv_out(h, 8, 4), _conv_out(w, 8, 4)
        h2, w2 = _conv_out(h1, 4, 2), _conv_out(w1, 4, 2)
        h3, w3 = _conv_out(h2, 3, 1), _conv_out(w2, 3, 1)
        flat = h3 * w3 * 64

        self.fc = nn.Linear(flat, 512)
        self.policy = nn.Linear(512, n_actions)
        self.value = nn.Linear(512, 1)

    def _features(self, obs: mx.array) -> mx.array:
        x = obs.astype(mx.float32) / 255.0       # (N, C, H, W)
        x = mx.transpose(x, (0, 2, 3, 1))        # -> NHWC
        x = nn.relu(self.conv1(x))
        x = nn.relu(self.conv2(x))
        x = nn.relu(self.conv3(x))
        x = x.reshape(x.shape[0], -1)
        return nn.relu(self.fc(x))

    def __call__(self, obs: mx.array):
        feat = self._features(obs)
        return self.policy(feat), self.value(feat).squeeze(-1)


# --------- Categorical 辅助函数（MLX 无内置分布类）--------- #
def log_softmax(logits: mx.array) -> mx.array:
    return logits - mx.logsumexp(logits, axis=-1, keepdims=True)


def action_log_probs(logits: mx.array, actions: mx.array) -> mx.array:
    logp = log_softmax(logits)
    return mx.take_along_axis(logp, actions[:, None], axis=-1).squeeze(-1)


def entropy(logits: mx.array) -> mx.array:
    logp = log_softmax(logits)
    p = mx.exp(logp)
    return -mx.sum(p * logp, axis=-1)


def sample_action(logits: mx.array) -> mx.array:
    return mx.random.categorical(logits)
