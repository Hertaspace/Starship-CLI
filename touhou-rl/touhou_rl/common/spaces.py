"""离散动作空间定义。

弹幕游戏的原始按键是同时按下的组合（方向 + 射击 + 低速 + Bomb）。
我们把「有意义的组合」枚举成一张离散动作表，PPO 只需输出一个 Categorical 索引，
环境再把索引翻译成具体按键状态。模拟器和真实游戏共用同一张表，保证两套后端一致。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

# 9 个移动方向：原地 + 上下左右 + 四对角。
# 约定屏幕坐标系：x 向右为正，y 向下为正（与图像数组一致）。
MOVES: List[Tuple[int, int]] = [
    (0, 0),    # 0 原地
    (0, -1),   # 1 上
    (0, 1),    # 2 下
    (-1, 0),   # 3 左
    (1, 0),    # 4 右
    (-1, -1),  # 5 左上
    (1, -1),   # 6 右上
    (-1, 1),   # 7 左下
    (1, 1),    # 8 右下
]


@dataclass(frozen=True)
class ButtonState:
    """某个离散动作对应的具体按键状态。"""
    dx: int          # -1 / 0 / 1
    dy: int          # -1 / 0 / 1
    shoot: bool
    focus: bool      # 低速（精确移动）
    bomb: bool

    @property
    def move_index(self) -> int:
        return MOVES.index((self.dx, self.dy))


def build_action_table(
    include_focus: bool = True,
    include_bomb: bool = False,
    always_shoot: bool = True,
) -> List[ButtonState]:
    """构造离散动作表。

    默认：9 向移动 × {低速关, 低速开} = 18 个动作，射击常按。
    若 include_bomb，则额外追加一个「原地放 Bomb」动作。
    """
    table: List[ButtonState] = []
    focus_options = [False, True] if include_focus else [False]
    for focus in focus_options:
        for dx, dy in MOVES:
            table.append(ButtonState(dx=dx, dy=dy, shoot=always_shoot, focus=focus, bomb=False))
    if include_bomb:
        table.append(ButtonState(dx=0, dy=0, shoot=always_shoot, focus=False, bomb=True))
    return table
