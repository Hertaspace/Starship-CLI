"""模拟器环境冒烟测试（不依赖真实游戏；需要 pygame）。"""
import numpy as np
import pytest

from touhou_rl.config import Config


def _make_cfg():
    cfg = Config()
    cfg.env.kind = "sim"
    cfg.env.sim.max_steps = 50
    cfg.env.obs.frame_skip = 1
    return cfg


def test_raw_simulator_step():
    pytest.importorskip("pygame")
    from touhou_rl.envs.simulator import BulletHellSim

    cfg = _make_cfg()
    env = BulletHellSim(cfg.env)
    obs, info = env.reset(seed=0)
    assert obs.shape == (cfg.env.sim.field_height, cfg.env.sim.field_width, 3)
    assert obs.dtype == np.uint8

    obs, reward, term, trunc, info = env.step(env.action_space.sample())
    assert isinstance(reward, float)
    assert "score" in info and "lives" in info
    env.close()


def test_wrapped_env_shapes():
    pytest.importorskip("pygame")
    pytest.importorskip("cv2")
    from touhou_rl.envs import make_env

    cfg = _make_cfg()
    env = make_env(cfg.env)
    obs, _ = env.reset(seed=0)
    # 帧堆叠 + 灰度 -> (frame_stack, H, W)
    assert obs.shape == (cfg.env.obs.frame_stack, cfg.env.obs.height, cfg.env.obs.width)
    assert obs.dtype == np.uint8

    for _ in range(5):
        obs, reward, term, trunc, info = env.step(env.action_space.sample())
        assert obs.shape == (cfg.env.obs.frame_stack, cfg.env.obs.height, cfg.env.obs.width)
        if term or trunc:
            obs, _ = env.reset()
    env.close()


def test_episode_terminates_or_truncates():
    pytest.importorskip("pygame")
    pytest.importorskip("cv2")
    from touhou_rl.envs import make_env

    cfg = _make_cfg()
    cfg.env.sim.max_steps = 30
    env = make_env(cfg.env)
    env.reset(seed=1)
    ended = False
    for _ in range(200):
        _, _, term, trunc, _ = env.step(env.action_space.sample())
        if term or trunc:
            ended = True
            break
    assert ended
    env.close()
