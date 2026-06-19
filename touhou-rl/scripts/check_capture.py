"""真实游戏捕获校准助手：列窗口 + 抓一帧预览。

在装有《东方永夜抄》并已启动的机器上运行：

    python -m scripts.check_capture --config configs/real_game.yaml

它会：
1. 枚举当前可见窗口（标题/区域），帮助你确认 window_title 或填 capture_region；
2. 按配置抓一帧，保存为 capture_preview.png，方便你校准 playfield_roi / HUD ROI。
"""
from __future__ import annotations

import argparse

from touhou_rl.config import load_config


def main():
    parser = argparse.ArgumentParser(description="真实游戏捕获校准")
    parser.add_argument("--config", type=str, default="configs/real_game.yaml")
    args = parser.parse_args()
    cfg = load_config(args.config)
    real = cfg.env.real

    from touhou_rl.capture.screen import list_windows, find_window_region, ScreenCapture

    print("=== 可见窗口 ===")
    windows = list_windows()
    if not windows:
        print("（当前平台无法自动枚举窗口，或缺少依赖。请手动设置 capture_region。）")
    for w in windows:
        print(f"  [{w['owner']}] {w['title']!r} region={w['region']}")

    region = real.capture_region or find_window_region(real.window_title)
    if region is None:
        print(f"\n未能按标题 {real.window_title!r} 定位窗口。"
              f"请在配置里设置 real.capture_region = [left, top, width, height]。")
        return

    print(f"\n使用捕获区域: {region}")
    cap = ScreenCapture(region)
    frame = cap.grab()
    print(f"抓帧成功: shape={frame.shape} dtype={frame.dtype}")
    try:
        import cv2
        cv2.imwrite("capture_preview.png", frame[:, :, ::-1])  # RGB->BGR 存盘
        print("已保存 capture_preview.png —— 用它来量取 playfield/HUD 的相对 ROI。")
    except Exception as exc:  # noqa: BLE001
        print(f"保存预览失败: {exc}")
    cap.close()


if __name__ == "__main__":
    main()
