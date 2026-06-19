"""纯视觉预处理 wrappers：灰度 + 缩放 + 帧堆叠 + 动作重复。

输入：原始 RGB 帧 (H, W, 3) uint8。
输出：通道在前的堆叠帧 (C, H, W) uint8，C = frame_stack * (1 灰度 | 3 彩色)。
归一化（/255）放在智能体网络里做，环境保持 uint8 以省内存。
"""
from __future__ import annotations

from collections import deque

import cv2
import numpy as np
import gymnasium as gym
from gymnasium import spaces


class GrayResizeFrame(gym.ObservationWrapper):
    """转灰度并缩放到 (height, width)。输出 (H, W, C) uint8。"""

    def __init__(self, env: gym.Env, width: int, height: int, grayscale: bool = True):
        super().__init__(env)
        self.width = width
        self.height = height
        self.grayscale = grayscale
        channels = 1 if grayscale else 3
        self.observation_space = spaces.Box(
            low=0, high=255, shape=(height, width, channels), dtype=np.uint8
        )

    def observation(self, obs: np.ndarray) -> np.ndarray:
        if self.grayscale:
            obs = cv2.cvtColor(obs, cv2.COLOR_RGB2GRAY)
        resized = cv2.resize(obs, (self.width, self.height), interpolation=cv2.INTER_AREA)
        if self.grayscale:
            resized = resized[:, :, None]
        return resized.astype(np.uint8)


class FrameStack(gym.Wrapper):
    """堆叠最近 k 帧，输出通道在前 (k*C, H, W) uint8。"""

    def __init__(self, env: gym.Env, k: int):
        super().__init__(env)
        self.k = k
        self.frames: deque = deque(maxlen=k)
        h, w, c = env.observation_space.shape
        self.observation_space = spaces.Box(
            low=0, high=255, shape=(k * c, h, w), dtype=np.uint8
        )

    def _stack(self) -> np.ndarray:
        # 每帧 (H, W, C) -> (C, H, W)，再沿通道拼接
        chans = [np.transpose(f, (2, 0, 1)) for f in self.frames]
        return np.concatenate(chans, axis=0)

    def reset(self, **kwargs):
        obs, info = self.env.reset(**kwargs)
        for _ in range(self.k):
            self.frames.append(obs)
        return self._stack(), info

    def step(self, action):
        obs, reward, terminated, truncated, info = self.env.step(action)
        self.frames.append(obs)
        return self._stack(), reward, terminated, truncated, info


class ActionRepeat(gym.Wrapper):
    """每个动作重复 n 帧（frame skip），奖励累加，期间触发终止则提前返回。"""

    def __init__(self, env: gym.Env, n: int):
        super().__init__(env)
        self.n = max(1, n)

    def step(self, action):
        total_reward = 0.0
        terminated = truncated = False
        info: dict = {}
        obs = None
        for _ in range(self.n):
            obs, reward, terminated, truncated, info = self.env.step(action)
            total_reward += reward
            if terminated or truncated:
                break
        return obs, total_reward, terminated, truncated, info
