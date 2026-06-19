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


def test_gae_shapes():
    torch = pytest.importorskip("torch")
    from touhou_rl.agents.torch.rollout import RolloutBuffer

    steps, obs_shape = 16, (4, 84, 84)
    buf = RolloutBuffer(steps, obs_shape, device=torch.device("cpu"))
    for i in range(steps):
        buf.add(
            torch.zeros(obs_shape, dtype=torch.uint8),
            action=i % 18, logprob=torch.tensor(0.0),
            reward=1.0, done=(i == steps - 1), value=torch.tensor(0.5),
        )
    returns, advantages = buf.compute_gae(
        last_value=torch.tensor(0.0), last_done=True, gamma=0.99, gae_lambda=0.95
    )
    assert returns.shape == (steps,)
    assert advantages.shape == (steps,)
