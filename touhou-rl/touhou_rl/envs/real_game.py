"""真实《东方永夜抄》环境（Gymnasium）。

把三块解耦能力组装成一个标准 RL 环境：
- 捕获  capture.ScreenCapture  → 纯视觉观测
- 控制  control.KeyboardController → 下发动作按键
- 感知  perception.HUDReader   → 从画面读残机/分数，转成奖励与终止

⚠️ 本环境需要在装有游戏的机器上、按你的窗口分辨率**校准**后才能正常工作，
   所有需要校准的地方都标了 TODO(real-game)。无法离线在 CI 跑通，单元测试会跳过它。

交互节流：通过 target_fps 控制每步耗时，避免抢占游戏主循环导致丢帧。
"""
from __future__ import annotations

import time
from typing import Optional, Tuple

import numpy as np
import gymnasium as gym
from gymnasium import spaces

from ..config import EnvConfig
from ..common.spaces import build_action_table


class TouhouRealEnv(gym.Env):
    metadata = {"render_modes": ["rgb_array"]}

    def __init__(self, cfg: EnvConfig):
        super().__init__()
        self.cfg = cfg
        self.real = cfg.real

        from ..capture.screen import ScreenCapture, find_window_region
        from ..control.keyboard import KeyboardController
        from ..perception.hud import HUDReader

        # 1) 定位捕获区域：优先手动 region，其次按窗口标题自动定位。
        region = self.real.capture_region
        if region is None:
            region = find_window_region(self.real.window_title)
        if region is None:
            raise RuntimeError(
                "无法定位游戏窗口。请在 configs/real_game.yaml 里设置 "
                "real.capture_region = [left, top, width, height]，"
                "或确认 real.window_title 与游戏窗口标题匹配。"
                "可先运行 `python -m scripts.check_capture` 查看可见窗口。"
            )
        self._full_region = region
        self._capture = ScreenCapture(region)
        self._controller = KeyboardController()
        self._hud = HUDReader(self.real, use_ocr=self.real.score_roi is not None)

        # 动作空间
        self.action_table = build_action_table(
            include_focus=cfg.action.include_focus,
            include_bomb=cfg.action.include_bomb,
            always_shoot=cfg.action.always_shoot,
        )
        self.action_space = spaces.Discrete(len(self.action_table))

        # 观测空间：裁出 playfield 后的原始 RGB（尺寸取一帧实测）
        probe = self._grab_playfield()
        h, w = probe.shape[:2]
        self.observation_space = spaces.Box(low=0, high=255, shape=(h, w, 3), dtype=np.uint8)

        self._min_dt = 1.0 / max(1e-3, self.real.target_fps)
        self._last_step_t = 0.0
        self._prev = {"score": None, "lives": None}

    # ------------------------------------------------------------------ #
    def _grab_playfield(self) -> np.ndarray:
        frame = self._capture.grab()
        x0, y0, x1, y1 = self.real.playfield_roi
        h, w = frame.shape[:2]
        self._last_full_frame = frame
        return frame[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)].copy()

    def reset(self, *, seed: Optional[int] = None, options=None):
        super().reset(seed=seed)
        # TODO(real-game): 在这里自动重开一局（按确定键穿过菜单 / 续关）。
        # 流程高度依赖游戏菜单，需用模板匹配判断当前界面后按相应键。占位：仅松开按键。
        self._controller.release_all()
        self._prev = {"score": None, "lives": None}
        obs = self._grab_playfield()
        return obs, {"lives": None, "score": None}

    def step(self, action: int):
        # 节流到目标帧率
        now = time.time()
        wait = self._min_dt - (now - self._last_step_t)
        if wait > 0:
            time.sleep(wait)
        self._last_step_t = time.time()

        btn = self.action_table[int(action)]
        self._controller.apply(btn)

        obs = self._grab_playfield()
        hud = self._hud.read(self._last_full_frame)

        reward = self.cfg.reward_survive
        terminated = False

        # 分数增量 → 奖励
        if hud["score"] is not None and self._prev["score"] is not None:
            delta = hud["score"] - self._prev["score"]
            if delta > 0:
                reward += delta * self.cfg.reward_score_scale

        # 残机减少 → 死亡惩罚
        if hud["lives"] is not None and self._prev["lives"] is not None:
            if hud["lives"] < self._prev["lives"]:
                reward += self.cfg.reward_death
            if hud["lives"] <= 0:
                terminated = True

        if self._hud.detect_game_over(self._last_full_frame):
            terminated = True

        self._prev = {"score": hud["score"], "lives": hud["lives"]}
        info = {"lives": hud["lives"], "score": hud["score"], "bombs": hud["bombs"]}
        return obs, float(reward), terminated, False, info

    def render(self):
        return self._last_full_frame

    def close(self):
        try:
            self._controller.release_all()
            self._capture.close()
        except Exception:
            pass
