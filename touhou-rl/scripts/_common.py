"""脚本共享的命令行解析：--config + 常用覆盖项。"""
from __future__ import annotations

import argparse
from typing import Dict

from touhou_rl.config import Config, load_config


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", type=str, default="configs/sim.yaml", help="YAML 配置路径")
    parser.add_argument("--backend", choices=["torch", "mlx"], default=None, help="覆盖 run.backend")
    parser.add_argument("--device", type=str, default=None, help="覆盖 run.device (auto|cpu|cuda|mps|gpu)")
    parser.add_argument("--total-steps", type=int, default=None, help="覆盖 ppo.total_steps")
    parser.add_argument("--num-envs", type=int, default=None, help="覆盖 ppo.num_envs（并行环境数）")
    parser.add_argument("--sync-envs", action="store_true", help="禁用多进程并行，走进程内串行")
    parser.add_argument("--seed", type=int, default=None, help="覆盖 run.seed")
    parser.add_argument("--exp-name", type=str, default=None, help="覆盖 run.exp_name")


def build_config(args: argparse.Namespace) -> Config:
    overrides: Dict[str, object] = {}
    if args.backend is not None:
        overrides["run.backend"] = args.backend
    if args.device is not None:
        overrides["run.device"] = args.device
    if getattr(args, "total_steps", None) is not None:
        overrides["ppo.total_steps"] = args.total_steps
    if getattr(args, "num_envs", None) is not None:
        overrides["ppo.num_envs"] = args.num_envs
    if getattr(args, "sync_envs", False):
        overrides["ppo.async_envs"] = False
    if args.seed is not None:
        overrides["run.seed"] = args.seed
    if getattr(args, "exp_name", None) is not None:
        overrides["run.exp_name"] = args.exp_name
    return load_config(args.config, overrides=overrides)
