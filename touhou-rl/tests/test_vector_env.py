"""向量化环境冒烟测试（用 Sync 模式，快速且确定）。

Async（多进程 spawn）在 CI 上较慢/易受沙箱限制，这里只测 Sync 与工厂行为；
Async 与 Sync 共享同一套 autoreset/接口约定，由 Sync 路径覆盖。
"""
import numpy as np
import pytest

from touhou_rl.config import Config


def _make_cfg():
    cfg = Config()
    cfg.env.kind = "sim"
    cfg.env.sim.max_steps = 20
    cfg.env.obs.frame_skip = 1
    return cfg


def test_sync_vector_shapes():
    pytest.importorskip("pygame")
    pytest.importorskip("cv2")
    from touhou_rl.envs import make_vector_env

    cfg = _make_cfg()
    n = 4
    venv = make_vector_env(cfg.env, num_envs=n, async_mode=False)
    assert venv.num_envs == n

    obs, infos = venv.reset(seed=0)
    h, w = cfg.env.obs.height, cfg.env.obs.width
    assert obs.shape == (n, cfg.env.obs.frame_stack, h, w)
    assert obs.dtype == np.uint8
    assert len(infos) == n

    actions = np.array([venv.single_action_space.sample() for _ in range(n)])
    obs, rew, term, trunc, infos = venv.step(actions)
    assert obs.shape == (n, cfg.env.obs.frame_stack, h, w)
    assert rew.shape == (n,)
    assert term.shape == (n,) and trunc.shape == (n,)
    venv.close()


def test_sync_vector_autoreset():
    pytest.importorskip("pygame")
    pytest.importorskip("cv2")
    from touhou_rl.envs import make_vector_env

    cfg = _make_cfg()
    cfg.env.sim.max_steps = 5  # 很快截断 -> 触发 autoreset
    n = 3
    venv = make_vector_env(cfg.env, num_envs=n, async_mode=False)
    venv.reset(seed=1)

    saw_done = False
    for _ in range(40):
        actions = np.array([venv.single_action_space.sample() for _ in range(n)])
        obs, rew, term, trunc, infos = venv.step(actions)
        done = np.logical_or(term, trunc)
        if done.any():
            saw_done = True
            # autoreset：终止的环境其 obs 应已是新一局首帧，且 info 带 final_observation
            for i in range(n):
                if done[i]:
                    assert "final_observation" in infos[i]
            assert obs.shape == (n, cfg.env.obs.frame_stack, cfg.env.obs.height, cfg.env.obs.width)
    assert saw_done
    venv.close()


def test_real_env_forced_single():
    # 真实游戏即使请求多环境也应被钳制为 1（不实际创建真实环境，只验证钳制逻辑）。
    from touhou_rl.envs.vector import make_vector_env as mk

    cfg = Config()
    cfg.env.kind = "real"
    # make_vector_env 在 num_envs>1 时会打印提示并钳制；这里用 monkeypatch 避免真正建环境。
    import touhou_rl.envs.vector as vec

    created = {}

    class _Fake:
        def __init__(self, fns):
            created["n"] = len(fns)

    orig_sync = vec.SyncVectorEnv
    vec.SyncVectorEnv = _Fake
    try:
        mk(cfg.env, num_envs=8, async_mode=True)
    finally:
        vec.SyncVectorEnv = orig_sync
    assert created["n"] == 1
