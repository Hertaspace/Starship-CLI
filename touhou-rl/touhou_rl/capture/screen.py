"""屏幕/窗口捕获（基于 mss，跨平台）。

真实游戏环境用它抓取游戏窗口区域作为纯视觉观测。

校准流程：
1. 启动游戏；
2. 运行 `python -m scripts.check_capture --config configs/real_game.yaml`；
3. 若按窗口标题定位失败，在 configs/real_game.yaml 里手动填 `capture_region`
   = [left, top, width, height]（像素，整屏坐标）。

注意：精确的「按窗口标题自动定位」依赖各操作系统的窗口管理 API，跨平台实现差异大，
这里给出 macOS / Windows 的最佳努力实现，定位失败时回落到手动 capture_region。
"""
from __future__ import annotations

import platform
from typing import List, Optional, Tuple

import numpy as np


def list_windows() -> List[dict]:
    """列出当前可见窗口（标题 + 边界框），用于校准。返回 [] 表示当前平台不支持自动枚举。"""
    system = platform.system()
    try:
        if system == "Darwin":
            return _list_windows_macos()
        if system == "Windows":
            return _list_windows_windows()
    except Exception as exc:  # noqa: BLE001
        print(f"[capture] 枚举窗口失败（{system}）: {exc}")
    return []


def _list_windows_macos() -> List[dict]:
    # 使用 Quartz（pyobjc）。未安装则抛错由上层兜底。
    from Quartz import (  # type: ignore
        CGWindowListCopyWindowInfo,
        kCGWindowListOptionOnScreenOnly,
        kCGNullWindowID,
    )
    infos = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
    out = []
    for w in infos:
        bounds = w.get("kCGWindowBounds", {})
        out.append({
            "title": w.get("kCGWindowName", "") or "",
            "owner": w.get("kCGWindowOwnerName", "") or "",
            "region": (
                int(bounds.get("X", 0)), int(bounds.get("Y", 0)),
                int(bounds.get("Width", 0)), int(bounds.get("Height", 0)),
            ),
        })
    return out


def _list_windows_windows() -> List[dict]:
    import win32gui  # type: ignore

    out: List[dict] = []

    def _cb(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:
                l, t, r, b = win32gui.GetWindowRect(hwnd)
                out.append({"title": title, "owner": "", "region": (l, t, r - l, b - t)})

    win32gui.EnumWindows(_cb, None)
    return out


def find_window_region(title_substring: str) -> Optional[Tuple[int, int, int, int]]:
    """按标题子串匹配窗口，返回 (left, top, width, height)。找不到返回 None。"""
    for w in list_windows():
        if title_substring and (title_substring in w["title"] or title_substring in w.get("owner", "")):
            region = w["region"]
            if region[2] > 0 and region[3] > 0:
                return region
    return None


class ScreenCapture:
    """对一块屏幕区域反复抓帧，返回 RGB (H, W, 3) uint8。"""

    def __init__(self, region: Tuple[int, int, int, int]):
        import mss  # 延迟导入
        self._mss = mss.mss()
        self.set_region(region)

    def set_region(self, region: Tuple[int, int, int, int]):
        left, top, width, height = region
        self._monitor = {"left": int(left), "top": int(top), "width": int(width), "height": int(height)}

    def grab(self) -> np.ndarray:
        raw = self._mss.grab(self._monitor)        # BGRA
        arr = np.asarray(raw)[:, :, :3]            # 去 alpha -> BGR
        return arr[:, :, ::-1].copy()              # BGR -> RGB

    def close(self):
        try:
            self._mss.close()
        except Exception:
            pass
