"""集中式配置：dataclass 定义 + YAML 加载/合并。

所有模块（环境、智能体、训练脚本）都从这里取配置，保证单一事实来源。

用法::

    from touhou_rl.config import load_config
    cfg = load_config("configs/sim.yaml")
    print(cfg.env.kind, cfg.ppo.lr)
"""
# 注意：此模块刻意不使用 `from __future__ import annotations`，
# 否则 dataclass 字段的 .type 会变成字符串，下面的递归解析无法识别嵌套 dataclass。
from dataclasses import dataclass, field, fields, is_dataclass
from typing import Any, Dict, List, Optional, Tuple

import yaml


# --------------------------------------------------------------------------- #
# 子配置
# --------------------------------------------------------------------------- #
@dataclass
class ActionConfig:
    """离散动作表的构造参数（见 common/spaces.py）。"""
    include_focus: bool = True      # 是否包含「低速移动」开/关变体
    include_bomb: bool = False      # 是否包含一个专门的 Bomb 动作
    always_shoot: bool = True       # 射击是否常按（弹幕游戏通常常按）


@dataclass
class ObsConfig:
    """纯视觉观测的预处理参数。"""
    width: int = 84                 # 缩放后宽
    height: int = 84                # 缩放后高
    grayscale: bool = True          # 是否转灰度
    frame_stack: int = 4            # 帧堆叠数（让网络感知速度/方向）
    frame_skip: int = 2             # 动作重复帧数（每个动作维持 N 帧）


@dataclass
class SimConfig:
    """内置 Pygame 弹幕模拟器参数。"""
    field_width: int = 384          # 弹幕区像素宽（仿东方竖屏比例）
    field_height: int = 448         # 弹幕区像素高
    player_speed: float = 4.0       # 正常移速（像素/帧）
    focus_speed: float = 1.8        # 低速移速
    player_radius: float = 3.0      # 玩家判定点半径（弹幕游戏判定极小）
    max_steps: int = 3600           # 单局最大帧数（截断）
    bullet_spawn_rate: float = 0.18 # 每帧新弹幕生成概率系数
    max_bullets: int = 400          # 同屏弹幕上限
    seed: Optional[int] = None
    render_mode: str = "rgb_array"  # rgb_array | human


@dataclass
class RealGameConfig:
    """真实游戏对接参数（需按你的机器校准 —— 见 envs/real_game.py）。"""
    window_title: str = "東方永夜抄"        # 游戏窗口标题（用于定位）
    # 若无法按标题定位，可手动指定捕获区域 (left, top, width, height)，单位像素
    capture_region: Optional[Tuple[int, int, int, int]] = None
    # 弹幕区（playfield）在捕获画面内的相对 ROI: (x0, y0, x1, y1)，比例 0~1
    playfield_roi: Tuple[float, float, float, float] = (0.0, 0.0, 1.0, 1.0)
    # HUD 各信息在捕获画面内的相对 ROI（用于读分/读残机），按需校准
    score_roi: Optional[Tuple[float, float, float, float]] = None
    lives_roi: Optional[Tuple[float, float, float, float]] = None
    bombs_roi: Optional[Tuple[float, float, float, float]] = None
    target_fps: float = 30.0        # 目标交互帧率（节流，避免抢占游戏）
    key_press_seconds: float = 0.0  # 0 表示按住到下次动作再改（推荐），>0 为点按时长


@dataclass
class EnvConfig:
    kind: str = "sim"               # sim | real
    action: ActionConfig = field(default_factory=ActionConfig)
    obs: ObsConfig = field(default_factory=ObsConfig)
    sim: SimConfig = field(default_factory=SimConfig)
    real: RealGameConfig = field(default_factory=RealGameConfig)
    # 奖励整形
    reward_survive: float = 0.01    # 每存活一步的奖励
    reward_death: float = -1.0      # 死亡惩罚
    reward_graze: float = 0.002     # 擦弹（graze）奖励，鼓励贴近躲避
    reward_score_scale: float = 1e-5  # 分数增量 → 奖励 的缩放（真实游戏用）


@dataclass
class PPOConfig:
    total_steps: int = 5_000_000    # 训练总环境步数
    rollout_steps: int = 2048       # 每次更新收集的步数
    num_epochs: int = 4             # 每批数据复用轮数
    minibatch_size: int = 256
    gamma: float = 0.99             # 折扣
    gae_lambda: float = 0.95        # GAE λ
    clip_coef: float = 0.2          # PPO 裁剪
    ent_coef: float = 0.01          # 熵正则（鼓励探索）
    vf_coef: float = 0.5            # 价值损失系数
    lr: float = 2.5e-4
    max_grad_norm: float = 0.5
    anneal_lr: bool = True          # 线性退火学习率
    norm_adv: bool = True           # 优势归一化


@dataclass
class RunConfig:
    backend: str = "torch"          # torch | mlx
    device: str = "auto"            # auto | cpu | cuda | mps | gpu
    seed: int = 0
    exp_name: str = "touhou_ppo"
    log_dir: str = "runs"
    save_dir: str = "checkpoints"
    save_every_updates: int = 50    # 每 N 次更新保存一次
    log_every_updates: int = 1


@dataclass
class Config:
    env: EnvConfig = field(default_factory=EnvConfig)
    ppo: PPOConfig = field(default_factory=PPOConfig)
    run: RunConfig = field(default_factory=RunConfig)


# --------------------------------------------------------------------------- #
# YAML → dataclass（递归、带类型校验的浅合并）
# --------------------------------------------------------------------------- #
def _from_dict(cls, data: Dict[str, Any]):
    if not is_dataclass(cls):
        return data
    kwargs: Dict[str, Any] = {}
    valid = {f.name: f for f in fields(cls)}
    for key, value in (data or {}).items():
        if key not in valid:
            raise KeyError(f"未知配置项 '{key}'（在 {cls.__name__} 中）")
        f = valid[key]
        if is_dataclass(f.type) and isinstance(value, dict):
            kwargs[key] = _from_dict(f.type, value)
        elif isinstance(value, list):
            kwargs[key] = tuple(value) if "Tuple" in str(f.type) else value
        else:
            kwargs[key] = value
    return cls(**kwargs)


def load_config(path: Optional[str] = None, overrides: Optional[Dict[str, Any]] = None) -> Config:
    """从 YAML 文件加载配置，缺省项回落到 dataclass 默认值。

    overrides 是可选的「点路径」字典，例如 {"ppo.lr": 1e-4}，便于命令行覆盖。
    """
    data: Dict[str, Any] = {}
    if path:
        with open(path, "r", encoding="utf-8") as fp:
            data = yaml.safe_load(fp) or {}
    cfg = _from_dict(Config, data)
    if overrides:
        cfg = apply_overrides(cfg, overrides)
    return cfg


def apply_overrides(cfg: Config, overrides: Dict[str, Any]) -> Config:
    """把 {"ppo.lr": 1e-4, "run.seed": 7} 形式的覆盖写入配置对象。"""
    for dotted, value in overrides.items():
        obj = cfg
        parts = dotted.split(".")
        for p in parts[:-1]:
            obj = getattr(obj, p)
        leaf = parts[-1]
        if not hasattr(obj, leaf):
            raise KeyError(f"未知配置路径 '{dotted}'")
        setattr(obj, leaf, value)
    return cfg


def to_dict(obj) -> Any:
    """把配置 dataclass 递归转回普通 dict（用于日志/存档）。"""
    if is_dataclass(obj):
        return {f.name: to_dict(getattr(obj, f.name)) for f in fields(obj)}
    if isinstance(obj, (list, tuple)):
        return [to_dict(x) for x in obj]
    return obj
