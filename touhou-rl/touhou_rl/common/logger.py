"""极简训练日志：控制台 + JSONL 文件，无第三方依赖。

若已安装 tensorboard，可自行在此扩展 SummaryWriter；这里保持零额外依赖。
"""
from __future__ import annotations

import json
import os
import time
from typing import Any, Dict


class Logger:
    def __init__(self, log_dir: str, exp_name: str):
        self.dir = os.path.join(log_dir, f"{exp_name}-{time.strftime('%Y%m%d-%H%M%S')}")
        os.makedirs(self.dir, exist_ok=True)
        self._fp = open(os.path.join(self.dir, "metrics.jsonl"), "a", encoding="utf-8")
        self._t0 = time.time()
        print(f"[logger] 日志目录: {self.dir}")

    def log(self, step: int, metrics: Dict[str, Any]) -> None:
        record = {"step": step, "wall_time": round(time.time() - self._t0, 2), **metrics}
        self._fp.write(json.dumps(record, ensure_ascii=False) + "\n")
        self._fp.flush()
        pretty = "  ".join(
            f"{k}={v:.4f}" if isinstance(v, float) else f"{k}={v}"
            for k, v in metrics.items()
        )
        print(f"[step {step:>9}] {pretty}")

    def save_config(self, cfg_dict: Dict[str, Any]) -> None:
        with open(os.path.join(self.dir, "config.json"), "w", encoding="utf-8") as fp:
            json.dump(cfg_dict, fp, ensure_ascii=False, indent=2)

    def close(self) -> None:
        self._fp.close()
