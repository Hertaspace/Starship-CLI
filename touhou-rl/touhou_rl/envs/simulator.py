"""内置弹幕射击模拟器（Gymnasium 环境）。

目的：在**不依赖真实游戏**、跨平台、可 headless 的前提下，提供一个结构与东方
弹幕类似的环境，用来打通「捕获 → 预处理 → 策略 → 动作 → 奖励 → 学习」整条管线。

- 观测：渲染出的 RGB 帧 (H, W, 3) uint8（再交给 wrappers 做灰度/缩放/堆叠）。
- 动作：common.spaces 的离散动作表索引。
- 奖励：每步生存 + 擦弹(graze) 奖励，被弹击中给死亡惩罚并终止。

它**不是**对东方永夜抄的精确复刻，只是一个忠于「躲弹幕」核心循环的代理任务。
"""
from __future__ import annotations

import os
from typing import Optional, Tuple

import numpy as np
import gymnasium as gym
from gymnasium import spaces

from ..config import EnvConfig
from ..common.spaces import build_action_table


class BulletHellSim(gym.Env):
    metadata = {"render_modes": ["rgb_array", "human"], "render_fps": 60}

    def __init__(self, cfg: EnvConfig):
        super().__init__()
        self.cfg = cfg
        self.sim = cfg.sim
        self.W = self.sim.field_width
        self.H = self.sim.field_height
        self.render_mode = self.sim.render_mode

        # headless：没有真实显示时用 dummy 驱动，保证服务器/CI 也能渲染。
        if self.render_mode != "human" and "SDL_VIDEODRIVER" not in os.environ:
            os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
            os.environ.setdefault("SDL_AUDIODRIVER", "dummy")  # headless 下禁用音频，避免 ALSA 噪声
        import pygame  # 延迟导入，避免无图形环境下 import 期报错
        self._pygame = pygame
        pygame.init()
        if self.render_mode == "human":
            self._surface = pygame.display.set_mode((self.W, self.H))
            pygame.display.set_caption("Touhou RL — Bullet Hell Sim")
        else:
            self._surface = pygame.Surface((self.W, self.H))
        self._clock = pygame.time.Clock()

        self.action_table = build_action_table(
            include_focus=cfg.action.include_focus,
            include_bomb=cfg.action.include_bomb,
            always_shoot=cfg.action.always_shoot,
        )
        self.action_space = spaces.Discrete(len(self.action_table))
        self.observation_space = spaces.Box(
            low=0, high=255, shape=(self.H, self.W, 3), dtype=np.uint8
        )

        # 弹幕状态（numpy 向量化）
        self._reset_state(seed=self.sim.seed)

    # ------------------------------------------------------------------ #
    # 状态
    # ------------------------------------------------------------------ #
    def _reset_state(self, seed: Optional[int]):
        self.rng = np.random.default_rng(seed)
        self.px = self.W / 2.0
        self.py = self.H * 0.82          # 玩家初始在偏下位置
        self.steps = 0
        self.score = 0.0
        self.graze_count = 0
        n0 = 0
        self.bx = np.zeros(n0, np.float32)
        self.by = np.zeros(n0, np.float32)
        self.bvx = np.zeros(n0, np.float32)
        self.bvy = np.zeros(n0, np.float32)
        self.br = np.zeros(n0, np.float32)

    def reset(self, *, seed: Optional[int] = None, options=None):
        super().reset(seed=seed)
        self._reset_state(seed=seed if seed is not None else self.sim.seed)
        return self._render_frame(), self._info()

    # ------------------------------------------------------------------ #
    # 弹幕生成
    # ------------------------------------------------------------------ #
    def _append_bullets(self, x, y, vx, vy, r):
        self.bx = np.concatenate([self.bx, np.asarray(x, np.float32)])
        self.by = np.concatenate([self.by, np.asarray(y, np.float32)])
        self.bvx = np.concatenate([self.bvx, np.asarray(vx, np.float32)])
        self.bvy = np.concatenate([self.bvy, np.asarray(vy, np.float32)])
        self.br = np.concatenate([self.br, np.asarray(r, np.float32)])

    def _spawn(self):
        if len(self.bx) >= self.sim.max_bullets:
            return
        # 随难度（步数）缓慢增长的强度
        intensity = self.sim.bullet_spawn_rate * (1.0 + self.steps / 1500.0)

        # 1) 瞄准玩家的直线弹（aimed）
        if self.rng.random() < intensity:
            sx = self.rng.uniform(0, self.W)
            sy = self.rng.uniform(0, self.H * 0.25)
            ang = np.arctan2(self.py - sy, self.px - sx)
            ang += self.rng.normal(0, 0.15)
            speed = self.rng.uniform(2.2, 3.6)
            self._append_bullets([sx], [sy], [np.cos(ang) * speed], [np.sin(ang) * speed], [4.0])

        # 2) 环形弹幕（ring burst）
        if self.rng.random() < intensity * 0.35:
            cx = self.rng.uniform(self.W * 0.2, self.W * 0.8)
            cy = self.rng.uniform(self.H * 0.05, self.H * 0.3)
            n = int(self.rng.integers(8, 18))
            angs = np.linspace(0, 2 * np.pi, n, endpoint=False) + self.rng.uniform(0, np.pi)
            speed = self.rng.uniform(1.8, 2.8)
            self._append_bullets(
                np.full(n, cx), np.full(n, cy),
                np.cos(angs) * speed, np.sin(angs) * speed, np.full(n, 3.5),
            )

        # 3) 顶部下落雨（curtain）
        if self.rng.random() < intensity * 0.6:
            sx = self.rng.uniform(0, self.W)
            self._append_bullets([sx], [0.0], [self.rng.normal(0, 0.4)], [self.rng.uniform(2.0, 3.2)], [3.0])

    # ------------------------------------------------------------------ #
    # step
    # ------------------------------------------------------------------ #
    def step(self, action: int):
        btn = self.action_table[int(action)]
        speed = self.sim.focus_speed if btn.focus else self.sim.player_speed
        self.px = float(np.clip(self.px + btn.dx * speed, 4, self.W - 4))
        self.py = float(np.clip(self.py + btn.dy * speed, 4, self.H - 4))

        self._spawn()

        # 更新弹幕位置
        if len(self.bx):
            self.bx += self.bvx
            self.by += self.bvy
            m = 16.0  # 出界裕度
            keep = (self.bx > -m) & (self.bx < self.W + m) & (self.by > -m) & (self.by < self.H + m)
            self.bx, self.by = self.bx[keep], self.by[keep]
            self.bvx, self.bvy, self.br = self.bvx[keep], self.bvy[keep], self.br[keep]

        # 碰撞 / 擦弹
        hit = False
        graze_now = 0
        if len(self.bx):
            d2 = (self.bx - self.px) ** 2 + (self.by - self.py) ** 2
            hit_r = (self.br + self.sim.player_radius) ** 2
            graze_r = (self.br + self.sim.player_radius + 10.0) ** 2
            hit = bool(np.any(d2 <= hit_r))
            graze_now = int(np.count_nonzero((d2 <= graze_r) & (d2 > hit_r)))

        self.graze_count += graze_now
        self.score += 10.0 + graze_now * 5.0
        self.steps += 1

        reward = self.cfg.reward_survive + graze_now * self.cfg.reward_graze
        terminated = False
        if hit:
            reward += self.cfg.reward_death
            terminated = True
        truncated = self.steps >= self.sim.max_steps

        return self._render_frame(), float(reward), terminated, truncated, self._info()

    # ------------------------------------------------------------------ #
    # 渲染
    # ------------------------------------------------------------------ #
    def _render_frame(self) -> np.ndarray:
        pg = self._pygame
        surf = self._surface
        surf.fill((12, 12, 28))
        # 弹幕（粉色）
        for x, y, r in zip(self.bx, self.by, self.br):
            pg.draw.circle(surf, (255, 120, 180), (int(x), int(y)), int(r))
        # 玩家本体（白）+ 判定点（红）
        pg.draw.circle(surf, (240, 240, 255), (int(self.px), int(self.py)), 6)
        pg.draw.circle(surf, (255, 40, 40), (int(self.px), int(self.py)), int(self.sim.player_radius))
        if self.render_mode == "human":
            pg.display.flip()
            self._clock.tick(self.metadata["render_fps"])
        arr = pg.surfarray.array3d(surf)        # (W, H, 3)
        return np.transpose(arr, (1, 0, 2)).copy()  # -> (H, W, 3)

    def render(self):
        return self._render_frame()

    def _info(self) -> dict:
        return {
            "score": self.score,
            "steps": self.steps,
            "n_bullets": int(len(self.bx)),
            "graze": self.graze_count,
            # 真实游戏环境会提供 lives；模拟器是单命即死，这里恒为 1。
            "lives": 1,
        }

    def close(self):
        try:
            self._pygame.quit()
        except Exception:
            pass
