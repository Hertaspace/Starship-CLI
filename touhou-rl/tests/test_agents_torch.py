"""PyTorch 智能体前向/评估冒烟测试（需要 torch）。"""
import pytest


def test_actor_critic_forward():
    torch = pytest.importorskip("torch")
    from touhou_rl.agents.torch.networks import ActorCritic

    obs_shape = (4, 84, 84)
    n_actions = 18
    agent = ActorCritic(obs_shape, n_actions)

    obs = torch.zeros(3, *obs_shape, dtype=torch.uint8)
    logits, value = agent(obs)
    assert logits.shape == (3, n_actions)
    assert value.shape == (3,)


def test_act_and_evaluate():
    torch = pytest.importorskip("torch")
    from touhou_rl.agents.torch.networks import ActorCritic

    obs_shape = (4, 84, 84)
    agent = ActorCritic(obs_shape, 18)
    obs = torch.randint(0, 255, (5, *obs_shape), dtype=torch.uint8)

    action, logprob, value = agent.act(obs)
    assert action.shape == (5,)
    assert logprob.shape == (5,)

    logp, entropy, val = agent.evaluate(obs, action)
    assert logp.shape == (5,)
    assert entropy.shape == (5,)
    assert val.shape == (5,)


def test_vectorized_gae_shapes():
    torch = pytest.importorskip("torch")
    from touhou_rl.agents.torch.rollout import RolloutBuffer

    steps, num_envs, obs_shape = 16, 4, (4, 84, 84)
    buf = RolloutBuffer(steps, num_envs, obs_shape, device=torch.device("cpu"))
    buf.rewards[:] = 1.0
    buf.values[:] = 0.5
    buf.dones[5, 1] = 1.0  # 某个环境中途终止

    returns, advantages = buf.compute_gae(
        last_value=torch.zeros(num_envs),
        last_done=torch.zeros(num_envs),
        gamma=0.99, gae_lambda=0.95,
    )
    assert returns.shape == (steps, num_envs)
    assert advantages.shape == (steps, num_envs)


def test_gae_masks_episode_boundary():
    torch = pytest.importorskip("torch")
    from touhou_rl.agents.torch.rollout import RolloutBuffer

    # 单环境、常数奖励：在 done 处自举应被切断，使该步优势更小。
    steps, num_envs = 8, 1
    buf = RolloutBuffer(steps, num_envs, (1,), device=torch.device("cpu"))
    buf.rewards[:] = 1.0
    buf.values[:] = 0.0
    buf.dones[4, 0] = 1.0  # 第 4 步是新回合首帧
    _, adv = buf.compute_gae(torch.zeros(1), torch.zeros(1), gamma=0.99, gae_lambda=0.95)
    # 第 3 步的优势不应把第 4 步（新回合）的未来回报算进来 -> 等于即时 delta=1.0
    assert abs(adv[3, 0].item() - 1.0) < 1e-5
