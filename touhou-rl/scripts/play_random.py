"""用随机动作驱动环境，确认整条 env 链路（捕获→预处理→动作→奖励）正常。

    python -m scripts.play_random --config configs/sim.yaml --steps 500
    python -m scripts.play_random --config configs/sim.yaml --steps 300 --save-frame
"""
from __future__ import annotations

import argparse

import numpy as np

from touhou_rl.config import load_config
from touhou_rl.envs import make_env


def main():
    parser = argparse.ArgumentParser(description="随机动作冒烟测试")
    parser.add_argument("--config", type=str, default="configs/sim.yaml")
    parser.add_argument("--steps", type=int, default=500)
    parser.add_argument("--save-frame", action="store_true", help="保存一帧观测到 obs_preview.png")
    args = parser.parse_args()

    cfg = load_config(args.config)
    env = make_env(cfg.env)
    print(f"观测空间: {env.observation_space}")
    print(f"动作空间: {env.action_space} (n={env.action_space.n})")

    obs, info = env.reset(seed=cfg.run.seed)
    total_reward, episodes, ep_reward, ep_len = 0.0, 0, 0.0, 0
    for t in range(args.steps):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        ep_reward += reward
        ep_len += 1
        if terminated or truncated:
            episodes += 1
            print(f"  回合结束 @step {t}: 长度={ep_len} 回报={ep_reward:.3f} info={info}")
            ep_reward, ep_len = 0.0, 0
            obs, info = env.reset()

    print(f"\n总步数={args.steps} 完成回合={episodes} 累计奖励={total_reward:.3f}")
    print(f"最终观测: shape={obs.shape} dtype={obs.dtype} min={obs.min()} max={obs.max()}")

    if args.save_frame:
        try:
            import cv2
            # obs 是 (C,H,W)；取最后一帧（最近的灰度/彩色帧）保存
            last = obs[-1] if obs.shape[0] in (1, 4) else obs[-3:]
            img = last if last.ndim == 2 else np.transpose(last, (1, 2, 0))
            cv2.imwrite("obs_preview.png", img)
            print("已保存 obs_preview.png")
        except Exception as exc:  # noqa: BLE001
            print(f"保存帧失败: {exc}")

    env.close()


if __name__ == "__main__":
    main()
