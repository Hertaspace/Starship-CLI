"""把离散动作翻译成游戏按键的按下/抬起（基于 pynput，跨平台）。

东方系列默认键位：
- 方向：方向键 ↑↓←→
- 射击/确定：Z
- Bomb/取消：X
- 低速移动：Shift（左 Shift）

不同移植/键位设置可能不同，可在 configs/real_game.yaml 之外直接改 TOUHOU_KEYMAP。

Windows 上若 pynput 的按键无法被游戏识别（部分 DirectInput 游戏会忽略合成按键），
请改用 pydirectinput：把 backend 设为 "pydirectinput"。
"""
from __future__ import annotations

from typing import Dict, Iterable

from ..common.spaces import ButtonState

# 逻辑按键名 -> 物理键
TOUHOU_KEYMAP: Dict[str, str] = {
    "up": "up",
    "down": "down",
    "left": "left",
    "right": "right",
    "shoot": "z",
    "bomb": "x",
    "focus": "shift",
}


class KeyboardController:
    """维护当前按下的键集合，按动作做最小增量的 press/release。"""

    def __init__(self, keymap: Dict[str, str] = None, backend: str = "pynput"):
        self.keymap = keymap or dict(TOUHOU_KEYMAP)
        self.backend = backend
        self._pressed: set = set()
        self._kb = self._make_backend(backend)

    def _make_backend(self, backend: str):
        if backend == "pynput":
            from pynput.keyboard import Controller, Key  # 延迟导入
            self._Key = Key
            return Controller()
        if backend == "pydirectinput":
            import pydirectinput  # type: ignore
            self._Key = None
            return pydirectinput
        raise ValueError(f"未知键盘后端: {backend}")

    # ---- 物理键名解析（pynput 需要把方向/Shift 转成 Key.*）----
    def _resolve(self, name: str):
        if self.backend == "pynput":
            special = {
                "up": self._Key.up, "down": self._Key.down,
                "left": self._Key.left, "right": self._Key.right,
                "shift": self._Key.shift,
            }
            return special.get(name, name)
        return name  # pydirectinput 用字符串键名

    def _press(self, name: str):
        key = self._resolve(name)
        if self.backend == "pynput":
            self._kb.press(key)
        else:
            self._kb.keyDown(key)

    def _release(self, name: str):
        key = self._resolve(name)
        if self.backend == "pynput":
            self._kb.release(key)
        else:
            self._kb.keyUp(key)

    def _desired_keys(self, btn: ButtonState) -> set:
        keys = set()
        if btn.dy < 0:
            keys.add(self.keymap["up"])
        elif btn.dy > 0:
            keys.add(self.keymap["down"])
        if btn.dx < 0:
            keys.add(self.keymap["left"])
        elif btn.dx > 0:
            keys.add(self.keymap["right"])
        if btn.shoot:
            keys.add(self.keymap["shoot"])
        if btn.focus:
            keys.add(self.keymap["focus"])
        if btn.bomb:
            keys.add(self.keymap["bomb"])
        return keys

    def apply(self, btn: ButtonState) -> None:
        """让物理按键状态收敛到 btn 描述的目标（只动有变化的键）。"""
        desired = self._desired_keys(btn)
        for k in self._pressed - desired:
            self._release(k)
        for k in desired - self._pressed:
            self._press(k)
        self._pressed = desired

    def release_all(self) -> None:
        for k in list(self._pressed):
            self._release(k)
        self._pressed = set()
