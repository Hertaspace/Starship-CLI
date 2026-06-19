"""从画面 HUD 区域提取奖励/终止信号（残机、Bomb、分数）。

强化学习需要奖励信号。本项目坚持「纯视觉」：不读游戏内存，所有信号都从屏幕像素里解析。

东方永夜抄的 HUD 在画面右侧，残机/灵符以一排星形图标显示，分数为数字串。
有两条可选路线：

A. 模板匹配（推荐起步）：截取残机图标 ROI，按亮度/计数估计剩余残机数；
   死亡时残机减少 → 给死亡惩罚并（可选）终止本回合。轻量、无需额外依赖。

B. OCR（可选）：用 pytesseract 读分数数字，按分数增量给正奖励。需安装 tesseract。

下面给出两者的脚手架与 TODO(real-game) 校准点。请按你的窗口分辨率在
configs/real_game.yaml 里填写各 ROI（相对比例 0~1）。
"""
from __future__ import annotations

from typing import Optional, Tuple

import numpy as np

from ..config import RealGameConfig


def _crop_roi(frame: np.ndarray, roi: Tuple[float, float, float, float]) -> np.ndarray:
    h, w = frame.shape[:2]
    x0, y0, x1, y1 = roi
    return frame[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)]


class HUDReader:
    """把一帧 RGB 画面解析成 {score, lives, bombs}。"""

    def __init__(self, cfg: RealGameConfig, use_ocr: bool = False):
        self.cfg = cfg
        self.use_ocr = use_ocr
        self._tess = None
        if use_ocr:
            import pytesseract  # type: ignore
            self._tess = pytesseract

    # ---------------------- 残机 / Bomb：亮度计数法 ---------------------- #
    def _count_icons(self, frame: np.ndarray, roi: Optional[Tuple[float, float, float, float]]) -> Optional[int]:
        """估算一排图标的点亮数量。

        思路：取 ROI → 转灰度 → 沿水平方向求列亮度 → 数「亮块」段数。
        这是一个稳健起步实现；TODO(real-game)：用真实截图标定阈值，或换成
        对单个图标做模板匹配 (cv2.matchTemplate) 以提高准确度。
        """
        if roi is None:
            return None
        patch = _crop_roi(frame, roi)
        if patch.size == 0:
            return None
        gray = patch.mean(axis=2)
        col = gray.mean(axis=0)
        thr = col.max() * 0.5 if col.max() > 0 else 1e9
        bright = col > thr
        # 数上升沿（暗->亮）作为图标个数
        segments = int(np.count_nonzero(bright[1:] & ~bright[:-1])) + int(bright[0])
        return segments

    # ---------------------- 分数：OCR ---------------------- #
    def _read_score(self, frame: np.ndarray) -> Optional[float]:
        if not self.use_ocr or self.cfg.score_roi is None:
            return None
        patch = _crop_roi(frame, self.cfg.score_roi)
        if patch.size == 0:
            return None
        text = self._tess.image_to_string(
            patch, config="--psm 7 -c tessedit_char_whitelist=0123456789",
        )
        digits = "".join(ch for ch in text if ch.isdigit())
        return float(digits) if digits else None

    def read(self, frame: np.ndarray) -> dict:
        return {
            "score": self._read_score(frame),
            "lives": self._count_icons(frame, self.cfg.lives_roi),
            "bombs": self._count_icons(frame, self.cfg.bombs_roi),
        }

    @staticmethod
    def detect_game_over(frame: np.ndarray) -> bool:
        """检测是否进入 Game Over / 续关界面。

        TODO(real-game)：用 Game Over 画面的模板/特征（如大面积变暗、特定文字 ROI）
        来判定。下面给一个占位：整屏极暗时认为可能进入了菜单/死亡黑屏。
        """
        return bool(frame.mean() < 12.0)
