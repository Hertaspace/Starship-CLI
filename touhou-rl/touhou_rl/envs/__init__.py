"""环境工厂：根据配置组装「环境 + 预处理」。

两套后端（torch / mlx）都调用 make_env，拿到完全一致的观测/动作空间。
"""
from __future__ import annotations

import gymnasium as gym

from ..config import EnvConfig
from .wrappers import ActionRepeat, FrameStack, GrayResizeFrame


def make_base_env(cfg: EnvConfig) -> gym.Env:
    if cfg.kind == "sim":
        from .simulator import BulletHellSim
        return BulletHellSim(cfg)
    if cfg.kind == "real":
        from .real_game import TouhouRealEnv
        return TouhouRealEnv(cfg)
    raise ValueError(f"未知环境类型 env.kind={cfg.kind!r}（应为 'sim' 或 'real'）")


def make_env(cfg: EnvConfig) -> gym.Env:
    """组装完整环境：原始环境 → 动作重复 → 灰度+缩放 → 帧堆叠。

    返回的环境观测形如 (frame_stack*C, H, W) uint8，动作为 Discrete。
    """
    env = make_base_env(cfg)
    if cfg.obs.frame_skip > 1:
        env = ActionRepeat(env, cfg.obs.frame_skip)
    env = GrayResizeFrame(env, width=cfg.obs.width, height=cfg.obs.height, grayscale=cfg.obs.grayscale)
    env = FrameStack(env, k=cfg.obs.frame_stack)
    return env


def make_vector_env(cfg: EnvConfig, num_envs: int, async_mode: bool = True):
    """构建向量化（并行）环境，每个子环境与 make_env 完全一致。"""
    from .vector import make_vector_env as _mk
    return _mk(cfg, num_envs=num_envs, async_mode=async_mode)


__all__ = ["make_env", "make_base_env", "make_vector_env"]
