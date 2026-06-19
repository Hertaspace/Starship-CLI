"""通用小工具：随机种子、设备选择、计时。"""
from __future__ import annotations

import os
import random
import time
from contextlib import contextmanager

import numpy as np


def set_global_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass


def resolve_torch_device(pref: str = "auto"):
    """把配置里的 device 字符串解析成 torch.device。"""
    import torch
    if pref == "auto":
        if torch.cuda.is_available():
            return torch.device("cuda")
        if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")
    return torch.device(pref)


@contextmanager
def timer(name: str = "block"):
    t0 = time.time()
    yield
    print(f"[timer] {name}: {time.time() - t0:.3f}s")
