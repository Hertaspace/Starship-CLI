"""向量化环境：并行运行多个环境以加速 PPO 采集。

提供两种实现，统一接口（classic autoreset 约定）：

- SyncVectorEnv ：进程内串行 step 所有环境。简单、确定性强，但受 GIL 限制无真正并行，
  主要用于调试/测试，以及把多个 obs 批量喂给 GPU 网络（前向仍能批处理加速）。
- AsyncVectorEnv：每个环境跑在独立子进程（spawn），真正并行 step，对 CPU 密集的
  Pygame 模拟器有显著加速。

autoreset 约定（与 CleanRL / Gymnasium<1.0 一致）：某个环境 terminated/truncated 时，
立即 reset，并把**新一局的首帧**作为该环境的 next obs 返回；原终止帧放进
info["final_observation"]。PPO 用返回的 done 标志在 GAE 里切断跨回合的自举。

接口::

    venv = make_vector_env(env_cfg, num_envs=8, async_mode=True)
    obs, infos = venv.reset(seed=0)              # obs: [N, *obs_shape]
    obs, rew, term, trunc, infos = venv.step(actions)   # actions: [N]
    venv.close()
"""
from __future__ import annotations

import multiprocessing as mp
from typing import Callable, List, Optional

import numpy as np

from ..config import EnvConfig


class EnvFactory:
    """可picklable 的环境构造器（spawn 子进程需要可序列化，故用类而非 lambda）。"""

    def __init__(self, env_cfg: EnvConfig):
        self.env_cfg = env_cfg

    def __call__(self):
        from . import make_env  # 延迟导入，避免子进程导入环路
        return make_env(self.env_cfg)


# --------------------------------------------------------------------------- #
# 进程内同步向量环境
# --------------------------------------------------------------------------- #
class SyncVectorEnv:
    def __init__(self, env_fns: List[Callable]):
        self.envs = [fn() for fn in env_fns]
        self.num_envs = len(self.envs)
        self.single_observation_space = self.envs[0].observation_space
        self.single_action_space = self.envs[0].action_space

    def reset(self, seed: Optional[int] = None):
        obs_list, infos = [], []
        for i, env in enumerate(self.envs):
            s = None if seed is None else seed + i
            obs, info = env.reset(seed=s)
            obs_list.append(obs)
            infos.append(info)
        return np.stack(obs_list), infos

    def step(self, actions):
        obs_list, rews, terms, truncs, infos = [], [], [], [], []
        for env, action in zip(self.envs, actions):
            obs, reward, terminated, truncated, info = env.step(int(action))
            if terminated or truncated:
                info = dict(info)
                info["final_observation"] = obs
                obs, _ = env.reset()
            obs_list.append(obs)
            rews.append(reward)
            terms.append(terminated)
            truncs.append(truncated)
            infos.append(info)
        return (
            np.stack(obs_list),
            np.asarray(rews, dtype=np.float32),
            np.asarray(terms, dtype=np.bool_),
            np.asarray(truncs, dtype=np.bool_),
            infos,
        )

    def close(self):
        for env in self.envs:
            env.close()


# --------------------------------------------------------------------------- #
# 多进程异步向量环境
# --------------------------------------------------------------------------- #
def _worker(remote, parent_remote, env_fn: EnvFactory):
    parent_remote.close()
    env = env_fn()
    try:
        while True:
            cmd, data = remote.recv()
            if cmd == "step":
                obs, reward, terminated, truncated, info = env.step(int(data))
                if terminated or truncated:
                    info = dict(info)
                    info["final_observation"] = obs
                    obs, _ = env.reset()
                remote.send((obs, reward, terminated, truncated, info))
            elif cmd == "reset":
                obs, info = env.reset(seed=data)
                remote.send((obs, info))
            elif cmd == "spaces":
                remote.send((env.observation_space, env.action_space))
            elif cmd == "close":
                break
            else:
                raise RuntimeError(f"未知指令: {cmd}")
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        env.close()
        remote.close()


class AsyncVectorEnv:
    def __init__(self, env_fns: List[EnvFactory]):
        self.num_envs = len(env_fns)
        ctx = mp.get_context("spawn")  # 跨平台一致（macOS/Windows 默认即 spawn）
        self._remotes, self._work_remotes = zip(*[ctx.Pipe() for _ in range(self.num_envs)])
        self._procs = []
        for work_remote, remote, fn in zip(self._work_remotes, self._remotes, env_fns):
            p = ctx.Process(target=_worker, args=(work_remote, remote, fn), daemon=True)
            p.start()
            work_remote.close()
            self._procs.append(p)

        self._remotes[0].send(("spaces", None))
        self.single_observation_space, self.single_action_space = self._remotes[0].recv()
        self._closed = False

    def reset(self, seed: Optional[int] = None):
        for i, remote in enumerate(self._remotes):
            remote.send(("reset", None if seed is None else seed + i))
        results = [remote.recv() for remote in self._remotes]
        obs_list, infos = zip(*results)
        return np.stack(obs_list), list(infos)

    def step(self, actions):
        for remote, action in zip(self._remotes, actions):
            remote.send(("step", int(action)))
        results = [remote.recv() for remote in self._remotes]
        obs_list, rews, terms, truncs, infos = zip(*results)
        return (
            np.stack(obs_list),
            np.asarray(rews, dtype=np.float32),
            np.asarray(terms, dtype=np.bool_),
            np.asarray(truncs, dtype=np.bool_),
            list(infos),
        )

    def close(self):
        if self._closed:
            return
        for remote in self._remotes:
            try:
                remote.send(("close", None))
            except (BrokenPipeError, EOFError):
                pass
        for p in self._procs:
            p.join(timeout=2.0)
            if p.is_alive():
                p.terminate()
        self._closed = True

    def __del__(self):
        self.close()


# --------------------------------------------------------------------------- #
# 工厂
# --------------------------------------------------------------------------- #
def make_vector_env(env_cfg: EnvConfig, num_envs: int, async_mode: bool = True):
    """根据配置构建向量化环境。真实游戏只能有一个实例，强制 num_envs=1。"""
    if env_cfg.kind == "real" and num_envs != 1:
        print(f"[vector] 真实游戏只能单实例运行，num_envs {num_envs} -> 1")
        num_envs = 1
    fns = [EnvFactory(env_cfg) for _ in range(num_envs)]
    if async_mode and num_envs > 1:
        return AsyncVectorEnv(fns)
    return SyncVectorEnv(fns)


__all__ = ["SyncVectorEnv", "AsyncVectorEnv", "EnvFactory", "make_vector_env"]
