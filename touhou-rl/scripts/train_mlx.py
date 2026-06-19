"""MLX 后端训练入口（Apple Silicon GPU）。

    python -m scripts.train_mlx --config configs/sim.yaml
"""
from __future__ import annotations

import argparse

from scripts._common import add_common_args, build_config


def main():
    parser = argparse.ArgumentParser(description="Touhou RL — MLX PPO 训练 (Apple Silicon)")
    add_common_args(parser)
    args = parser.parse_args()
    cfg = build_config(args)
    cfg.run.backend = "mlx"

    from touhou_rl.agents.mlx.ppo import train
    train(cfg)


if __name__ == "__main__":
    main()
