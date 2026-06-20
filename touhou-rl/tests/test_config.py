import os

from touhou_rl.config import Config, apply_overrides, load_config, to_dict


def test_defaults():
    cfg = Config()
    assert cfg.env.kind == "sim"
    assert cfg.ppo.gamma == 0.99
    assert cfg.run.backend == "torch"


def test_load_sim_yaml():
    path = os.path.join(os.path.dirname(__file__), "..", "configs", "sim.yaml")
    cfg = load_config(path)
    assert cfg.env.kind == "sim"
    assert cfg.env.obs.frame_stack == 4
    assert cfg.ppo.num_envs == 8
    assert cfg.ppo.async_envs is True


def test_overrides():
    cfg = Config()
    apply_overrides(cfg, {"ppo.lr": 1e-4, "run.seed": 7, "run.backend": "mlx"})
    assert cfg.ppo.lr == 1e-4
    assert cfg.run.seed == 7
    assert cfg.run.backend == "mlx"


def test_roundtrip_to_dict():
    cfg = Config()
    d = to_dict(cfg)
    assert d["env"]["kind"] == "sim"
    assert isinstance(d["ppo"]["gamma"], float)
