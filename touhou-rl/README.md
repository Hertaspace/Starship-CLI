# Touhou RL — 纯视觉端到端弹幕射击强化学习

一个用强化学习从**纯像素输入**端到端学习游玩弹幕射击游戏（目标：**东方永夜抄 / Imperishable Night**）的项目脚手架。

智能体只看屏幕画面（不读内存、不解析游戏内部状态），输出键盘动作（移动 / 射击 / 低速 / 符卡 Bomb），通过试错学习躲弹幕与生存。

> 状态：**脚手架完成，整条训练管线已打通，可直接开训**。本仓库刻意停在「按下开始训练之前」的那一步——`scripts/train_torch.py` / `scripts/train_mlx.py` 已经可运行，但默认不会自动启动长时间训练。

---

## 设计要点

| 维度 | 方案 |
|------|------|
| 输入 | 纯视觉：屏幕画面 → 灰度 → 缩放 84×84 → 帧堆叠 (4 帧) |
| 动作 | 离散动作表：9 向移动 × {低速开/关} (+ 可选 Bomb)，射击默认常按 |
| 算法 | PPO（近端策略优化），Actor-Critic + NatureCNN 编码器 |
| 后端 | **两套实现**：① PyTorch（CUDA/CPU）② **MLX（Apple Silicon GPU）** |
| 环境 | **两套**：① 内置 Pygame 弹幕模拟器（跨平台、免游戏即可跑通）② 真实游戏截屏+按键 |
| 接口 | 全部遵循 [Gymnasium](https://gymnasium.farama.org/) `Env` API |
| 加速 | **向量化多环境**：N 个环境并行采集（多进程 spawn），批量喂给 GPU |

为什么做两套环境：真实游戏只能在装有《东方永夜抄》的机器上调试，而**内置模拟器**让你在任何机器上立刻验证「捕获 → 预处理 → 策略 → 动作 → 奖励 → 学习」整条链路是否打通，再无缝切到真实游戏。

为什么做两套算法后端：PyTorch 通用且生态成熟；**MLX** 让你在 Mac（M 系列芯片）的统一内存 GPU 上原生加速训练，二者共用同一套环境与动作空间，便于对比。

---

## 目录结构

```
touhou-rl/
├── configs/                  # YAML 配置（模拟器 / 真实游戏 / 默认超参）
├── touhou_rl/
│   ├── config.py             # dataclass 配置 + YAML 加载
│   ├── common/               # 动作空间、日志、工具
│   ├── envs/                 # 模拟器环境、真实游戏环境、预处理 wrappers、向量化(并行)环境、make_env 工厂
│   ├── capture/              # 屏幕/窗口捕获（mss）
│   ├── control/              # 键盘动作下发（pynput / pydirectinput）
│   ├── perception/           # HUD 读分/读残机（模板匹配/OCR）→ 奖励信号
│   └── agents/
│       ├── torch/            # PyTorch: networks / ppo / rollout buffer
│       └── mlx/              # MLX:    networks / ppo / rollout buffer
├── scripts/                  # 训练入口 + 健康检查脚本
└── tests/                    # 不依赖真实游戏的单元测试（pytest）
```

---

## 快速开始

### 1. 安装

```bash
cd touhou-rl
python3 -m venv .venv && source .venv/bin/activate

# 基础依赖（环境 + 预处理 + PyTorch 后端）
pip install -r requirements.txt

# 仅 Apple Silicon：MLX 后端
pip install -r requirements-mlx.txt
```

### 2. 冒烟测试（不需要真实游戏，不需要 GPU）

```bash
# 跑单元测试：动作空间、模拟器环境、智能体前向
pytest -q

# 用随机动作驱动内置弹幕模拟器，确认整条 env 链路正常
python -m scripts.play_random --config configs/sim.yaml --steps 500
```

### 3. （可选）检查真实游戏捕获

在装有《东方永夜抄》的机器上，先启动游戏，再：

```bash
python -m scripts.check_capture --config configs/real_game.yaml
```

它会列出可见窗口、抓一帧保存为 `capture_preview.png`，方便你校准窗口标题与 HUD ROI。

### 4. 开始训练（这一步留给你）

```bash
# PyTorch 后端 + 模拟器环境
python -m scripts.train_torch --config configs/sim.yaml

# MLX 后端（Apple Silicon）+ 模拟器环境
python -m scripts.train_mlx --config configs/sim.yaml

# 切到真实游戏：把 --config 换成 configs/real_game.yaml
```

---

## 向量化多环境加速

模拟器的瓶颈是 CPU 上的 Pygame 渲染与弹幕更新（纯 Python，受 GIL 限制）。
PPO 用 **N 个并行环境**同时采集经验来加速：每步把 N 帧观测**批量**喂给 GPU 网络，
再展平成一个大 batch 做更新。

- `ppo.num_envs`：并行环境数（`configs/sim.yaml` 默认 8）。
- `ppo.async_envs`：`true` 用多进程（`AsyncVectorEnv`，spawn）真正并行；`false` 用进程内
  串行（`SyncVectorEnv`，便于调试/断点）。
- `batch_size = rollout_steps × num_envs`；`rollout_steps` 现在是**每个环境**每次更新的步数。
- **真实游戏**只能有一个游戏窗口，`num_envs` 会被自动强制为 1（与 `async` 无关）。

命令行可直接覆盖，无需改 YAML：

```bash
python -m scripts.train_torch --config configs/sim.yaml --num-envs 16      # 16 个并行环境
python -m scripts.train_torch --config configs/sim.yaml --num-envs 4 --sync-envs  # 串行调试
```

实现见 `touhou_rl/envs/vector.py`；采集与 GAE 采用 CleanRL 风格的 `[steps, num_envs]`
张量与 classic-autoreset 约定（终止即自动重开，原终止帧放进 `info["final_observation"]`）。

---

## 从模拟器切到真实游戏

真实游戏环境 (`touhou_rl/envs/real_game.py`) 把三件事解耦成可替换模块：

1. **捕获** `capture/screen.py` — 用 `mss` 抓取游戏窗口区域；
2. **控制** `control/keyboard.py` — 把离散动作翻译成按键的按下/抬起；
3. **感知** `perception/hud.py` — 从画面 HUD 区域读取分数/残机/Bomb，转成奖励与终止信号。

这三处都标了 `TODO(real-game)`，需要你按自己机器上的窗口标题、分辨率、HUD 坐标做一次校准。校准方法见各文件顶部注释与 `scripts/check_capture.py`。

---

## 法律与使用须知

- 《东方永夜抄》版权归上海爱丽丝幻乐团 (Team Shanghai Alice / ZUN) 所有。本项目**不包含任何游戏本体、ROM 或美术资源**，仅提供与你**合法持有**的游戏副本交互的代码。
- 自动化操作游戏请遵守游戏的二次创作/使用守则，仅用于个人学习研究，请勿用于排行榜作弊或商业用途。
