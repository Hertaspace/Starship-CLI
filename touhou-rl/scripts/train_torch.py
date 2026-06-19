"""PyTorch 后端训练入口。

    python -m scripts.train_torch --config configs/sim.yaml
    python -m scripts.train_torch --config configs/real_game.yaml --device cuda
"""
from __future__ import annotations

import argparse

from scripts._common import add_common_args, build_config


def main():
    parser = argparse.ArgumentParser(description="Touhou RL — PyTorch PPO 训练")
    add_common_args(parser)
    args = parser.parse_args()
    cfg = build_config(args)
    cfg.run.backend = "torch"

    from touhou_rl.agents.torch.ppo import train
    train(cfg)


if __name__ == "__main__":
    main()
