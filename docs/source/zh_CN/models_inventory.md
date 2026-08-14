# GR00T 开源模型清单

一份简洁的清单，说明这个仓库开源了什么模型，每个模型能做什么，以及如何自己训练。

---

## 📊 模型清单总览

| 模型名称 | 类型 | 开源预训练权重 | 自己能训练 | 支持机器人 | 页面跳转 |
|---------|------|-------------|----------|---------|---------|
| **SONIC** | 全身控制 | ✅ 3个版本 | ✅ 是 | G1 | [详情](#1-sonic-全身控制-开源预训练) |
| **Decoupled WBC** | 下身+IK | ✅ N1.5/1.6 | ✅ 是 | G1 | [详情](#2-decoupled-wbc-下身控制) |
| **MotionBricks** | 动作生成 | ✅ 检查点 | ✅ 是 | G1 | [详情](#3-motionbricks-动作生成) |
| **VLA (Isaac-GR00T)** | 视觉语言动作 | ❌ 需自己微调 | ✅ 是 | G1 | [详情](#4-vla-视觉语言动作) |
| **SONIC H2** | 全身控制 | ❌ 配置有，权重无 | ✅ 是 | H2 | [详情](#5-sonic-h2-h2专用) |

---

## 1️⃣ SONIC - 全身控制（✅ 开源预训练）

### 开源了什么

| 版本 | ONNX模型 | PyTorch权重 | 配置文件 |
|------|---------|-----------|--------|
| **默认版本** (Default SONIC) | ✅ | ✅ | ✅ |
| **低延迟版本** (Low-latency) | ✅ | ✅ | ✅ |
| **SONIC v1.1** | ✅ | ✅ | ✅ |

### 这三个版本有什么区别

```
┌────────────────────────────────────────────┐
│ SONIC 三个预训练版本对比                   │
├────────────────────────────────────────────┤
│                                            │
│ 默认版本（通用）                          │
│ ├─ SMPL参考：10帧 (200ms前瞻)             │
│ ├─ 用途：通用运动追踪、规划、遥操         │
│ ├─ 特点：兼容性最好，应用最广            │
│ └─ 推荐：大多数场景首选                  │
│                                            │
│ 低延迟版本（遥操优先）                    │
│ ├─ SMPL参考：4帧 (80ms前瞻)               │
│ ├─ 用途：VR遥操、VLA推理                 │
│ ├─ 特点：响应快，但前瞻短                │
│ └─ 推荐：需要低延迟的场景                │
│                                            │
│ v1.1版本（3点遥操）                       │
│ ├─ SMPL参考：10帧 (200ms前瞻)             │
│ ├─ 用途：头显3点追踪、VLA                │
│ ├─ 特点：机器人朝向归一化+手腕增强       │
│ └─ 推荐：需要稳定朝向控制的场景          │
│                                            │
└────────────────────────────────────────────┘
```

### 能做什么

| 能力 | 描述 |
|------|------|
| 🚶 **行走** | 直线、转弯、各种速度 |
| 🏃 **跑步** | 加速、减速、改变方向 |
| 💃 **跳舞** | 节奏感强的动作 |
| 🧘 **平衡** | 静态平衡、动态平衡 |
| 👐 **手臂动作** | 挥手、指向、拿取 |
| 🧗 **攀爬** | 爬楼梯（受限） |
| 🪑 **坐下** | 坐下、站起 |
| 🎯 **精密控制** | VR遥操、任务执行 |

### 如何使用（不训练）

```bash
# 下载模型
python download_from_hf.py

# 启动部署
cd gear_sonic_deploy && ./deploy.sh --input-type zmq_manager real

# 发送指令（工作站另一个终端）
python gear_sonic/scripts/launch_inference.py \
    --camera-host <G1_IP> \
    --prompt "walk forward 2 meters"
```

### 如何自己训练

**前置要求：**
- Isaac Lab（单独安装）
- 64+ GPUs 或 8+ GPUs (慢)
- Bones-SEED 数据集 (142K+ 运动)

**三种训练方式：**

```bash
# 方式1：从头训练（耗时最长）
accelerate launch --num_processes=64 gear_sonic/train_agent_trl.py \
    +exp=manager/universal_token/all_modes/sonic_release \
    num_envs=4096 headless=True \
    ++manager_env.commands.motion.motion_lib_cfg.motion_file=data/motion_lib_bones_seed/robot_filtered

# 方式2：微调预训练模型（推荐，更快）
accelerate launch --num_processes=8 gear_sonic/train_agent_trl.py \
    +exp=manager/universal_token/all_modes/sonic_release \
    +checkpoint=sonic_release/last.pt \
    num_envs=4096 headless=True \
    ++manager_env.commands.motion.motion_lib_cfg.motion_file=your_data

# 方式3：小规模调试（验证想法）
python gear_sonic/train_agent_trl.py \
    +exp=manager/universal_token/all_modes/sonic_release \
    num_envs=16 headless=False \
    ++algo.config.num_learning_iterations=100
```

### 训练后能做什么

✅ 针对特定场景优化的运动模型
✅ 支持新的运动类型或风格
✅ 融合自己收集的演示数据
✅ 部署到生产环境

**训练时间：** 100K 迭代 ≈ 7 天 (64GPUs)

---

## 2️⃣ Decoupled WBC - 下身控制（✅ 开源预训练）

### 开源了什么

| 版本 | 预训练权重 | ONNX模型 | 配置 |
|------|----------|---------|-----|
| **GR00T N1.5** | ✅ | ✅ | ✅ |
| **GR00T N1.6** | ✅ | ✅ | ✅ |

### 能做什么

| 能力 | 说明 |
|------|------|
| 🚶 **下身运动** | 行走、转弯、各种速度 |
| 📍 **位置控制** | 精确跟踪目标速度 |
| 🧠 **IK求解** | 上身跟随目标姿态 |
| 📐 **地形适应** | 不同地面的步态调整 |

### 架构

```
┌──────────────────────────────────┐
│   速度指令（用户输入）           │
├──────────────────────────────────┤
│ 下身 RL 政策 (训练得到)          │
│ 输出：腿部关节力矩               │
├──────────────────────────────────┤
│ 上身 IK 求解器 (解析解)          │
│ 输出：躯干+头+手臂控制           │
├──────────────────────────────────┤
│ 机器人执行                       │
└──────────────────────────────────┘
```

### 如何使用和训练

```bash
# 预训练模型部署
./deploy.sh --lower-body-checkpoint policy/gr00t_n1.6 real

# 自己训练下身控制
python decoupled_wbc/train_lower_body_rl.py \
    --num_envs 4096 \
    --num_iterations 50000 \
    --learning_rate 1e-4
```

**训练时间：** 50K 迭代 ≈ 5 天 (64GPUs)

---

## 3️⃣ MotionBricks - 实时动作生成（✅ 开源预训练检查点）

### 开源了什么

| 组件 | 状态 |
|------|------|
| **VQVAE检查点** | ✅ |
| **姿态编码器** | ✅ |
| **根节点生成器** | ✅ |
| **推理代码** | ✅ |
| **训练代码** | ✅ |

### 能做什么

| 能力 | 说明 |
|------|------|
| 💨 **实时生成** | 15,000 FPS 的运动生成速度 |
| 🎮 **交互式控制** | 实时响应用户输入 |
| 🧬 **潜空间表示** | 学习到高效的运动编码 |
| 🎨 **零样本生成** | 生成未见过的新运动 |

### 怎么用

```bash
# 激活检查点（可选）
git lfs pull --include="motionbricks/out/**" --exclude=""

# 运行交互式演示
cd motionbricks && python demo_interactive.py

# 用键盘实时控制 G1 的动作生成
```

### 怎么训练

```bash
# 使用合成数据训练
python motionbricks/train_vqvae.py \
    --config motionbricks/config/train.yaml

python motionbricks/train_pose_encoder.py

python motionbricks/train_root_generator.py
```

**特点：** 轻量级，单个 GPU 就能训练

---

## 4️⃣ VLA（Isaac-GR00T）- 视觉语言动作（⚠️ 需自己微调）

### 开源了什么

| 组件 | 开源状态 |
|------|---------|
| **VLA模型架构** | ✅ (Isaac-GR00T) |
| **预训练权重** | ❌ (需向NVIDIA申请或自己训练) |
| **训练代码** | ✅ |
| **推理代码** | ✅ |
| **数据收集工具** | ✅ |

### 能做什么

| 能力 | 说明 |
|------|------|
| 🗣️ **文本指令** | "pick up the cup" |
| 👁️ **视觉理解** | 从摄像头画面理解场景 |
| 🤖 **生成动作** | 执行复杂多步任务 |
| 🎯 **任务完成** | 操作物体、导航等 |

### 架构

```
┌─────────────────────────┐
│ 用户文本指令            │
│ + 摄像头画面            │
├─────────────────────────┤
│ VLA 模型（微调）        │
│ 输入：视觉+语言         │
│ 输出：动作令牌          │
├─────────────────────────┤
│ SONIC 解码器            │
│ 输入：动作令牌          │
│ 输出：机器人关节        │
├─────────────────────────┤
│ G1 执行                 │
└─────────────────────────┘
```

### 怎么使用（微调）

**前置：** 收集演示数据（VR遥操 50-100 次）

```bash
# 1. 收集数据
python gear_sonic/scripts/launch_data_collection.py \
    --robot-ip 192.168.123.161 \
    --output-dir data/pick_cup_demos

# 2. 微调 VLA
uv run python gr00t/train/run_gr00t_train.py \
    --model-name gr00t-n1.7 \
    --dataset-path data/pick_cup_demos \
    --num-epochs 10

# 3. 推理
python gear_sonic/scripts/launch_inference.py \
    --camera-host 192.168.123.161 \
    --gr00t-server-ip 127.0.0.1:5550 \
    --prompt "pick up the cup"
```

**训练时间：** 10 epochs ≈ 4 小时 (单 A100)

---

## 5️⃣ SONIC H2 - H2 专用全身控制（⚠️ 配置有，权重无）

### 开源了什么

| 组件 | 状态 |
|------|------|
| **SONIC H2 配置** | ✅ (sonic_h2.yaml) |
| **关节映射** | ✅ (h2.py) |
| **物理模型** | ✅ (h2.xml, h2.urdf) |
| **预训练权重** | ❌ |

### 能做什么

与 SONIC 相同，但针对 H2 的 31 DOF 优化：
- 更灵活的腰部（3 DOF）
- 更自然的头部（3 DOF）
- 更精准的手腕（3 DOF/只）

### 怎么训练

需要为 H2 重新生成运动库（retarget SMPL→H2）

```bash
# 1. Retarget SMPL 到 H2
python gear_sonic/data_process/retarget_smpl_to_h2.py \
    --input data/smpl_source \
    --output data/motion_lib_h2/smpl_h2

# 2. 生成 H2 motion_lib
python gear_sonic/data_process/convert_smpl_to_motion_lib_h2.py \
    --input data/motion_lib_h2/smpl_h2 \
    --output data/motion_lib_h2/robot

# 3. 过滤
python gear_sonic/data_process/filter_and_copy_bones_data.py \
    --source data/motion_lib_h2/robot \
    --dest data/motion_lib_h2/robot_filtered \
    --embodiment h2

# 4. 训练
accelerate launch --num_processes=64 gear_sonic/train_agent_trl.py \
    +exp=manager/universal_token/all_modes/sonic_h2 \
    ++manager_env.commands.motion.motion_lib_cfg.motion_file=data/motion_lib_h2/robot_filtered
```

**训练时间：** 100K 迭代 ≈ 7 天 (64GPUs)

---

## 📋 模型能力矩阵

```
┌─────────────────┬────────┬────────┬────────┬────────┬────────┐
│ 能力            │ SONIC  │ Decp   │ MB     │ VLA    │ SONIC  │
│                 │        │ WBC    │        │        │ H2     │
├─────────────────┼────────┼────────┼────────┼────────┼────────┤
│ 行走            │   ✅   │   ✅   │   ✅   │   ✅   │   ✅   │
│ 转向/转弯       │   ✅   │   ✅   │   ✅   │   ✅   │   ✅   │
│ 跑步            │   ✅   │   ✅   │   ✅   │   ✅   │   ✅   │
│ 舞蹈/复杂动作   │   ✅   │   ❌   │   ✅   │   ✅   │   ✅   │
│ VR遥操          │   ✅   │   ❌   │   ❌   │   ✅   │   ✅   │
│ 文本指令        │   ✅   │   ❌   │   ❌   │   ✅   │   ✅   │
│ 任务学习        │   ❌   │   ❌   │   ❌   │   ✅   │   ❌   │
│ 实时生成        │   ❌   │   ❌   │   ✅   │   ❌   │   ❌   │
│ 精密操作        │   中   │   低   │   中   │   ✅   │   高   │
├─────────────────┼────────┼────────┼────────┼────────┼────────┤
│ 开源权重        │   ✅   │   ✅   │   ✅   │   ❌   │   ❌   │
│ 难度训练        │   高   │   中   │   低   │   中   │   高   │
│ 所需GPU         │  64+   │  64+   │   1+   │   1+   │  64+   │
└─────────────────┴────────┴────────┴────────┴────────┴────────┘

Decp = Decoupled WBC
MB = MotionBricks
```

---

## 🎯 选择模型的快速指南

### "我想直接用开源模型，不训练"
→ **SONIC** (3个预训练版本都可用)

### "我想要低延迟响应"
→ **SONIC Low-latency** 版本

### "我想要VR遥操"
→ **SONIC v1.1** + VR 头显

### "我想让机器人学习新任务"
→ **VLA** (需收集演示数据并微调)

### "我想要超快速的运动生成"
→ **MotionBricks**

### "我只需要下身走路"
→ **Decoupled WBC** (更简洁)

### "我有H2机器人"
→ **SONIC H2** (需自己训练)

---

## 📥 如何获取模型

### 方式1：HuggingFace (推荐)

```bash
# 下载所有SONIC版本
python download_from_hf.py

# 下载特定版本
python download_from_hf.py --low-latency
python download_from_hf.py --sonic-v1-1

# 下载训练数据
python download_from_hf.py --training

# 下载MotionBricks检查点
git lfs pull --include="motionbricks/out/**" --exclude=""
```

### 方式2：本地编译

```bash
# Decoupled WBC
python decoupled_wbc/eval.py --checkpoint policy/gr00t_n1.6

# MotionBricks
python motionbricks/run_demo.py
```

---

## 🔄 模型之间的关系

```
┌─────────────────────────────────────────────────┐
│  所有模型都针对 Unitree G1（29 DOF）           │
└─────────────────────────────────────────────────┘

通用流程：
  SMPL 人体数据
       ↓
  SONIC 编码器 (所有模型共享)
       ↓
  64维潜在向量
       ├─→ SONIC 解码器 → G1 关节命令
       ├─→ MotionBricks 处理 → 实时控制
       ├─→ VLA 策略 → 任务执行
       └─→ Decoupled WBC → 下身控制

特殊路径：
  VLA 需要：
  摄像头 → 视觉编码 → VLA 模型 → 动作 → SONIC → G1

MotionBricks 是独立的：
  用户输入 → 潜空间采样 → VQVAE 解码 → 运动生成
```

---

## 🎬 快速开始命令速查

### 最快体验（30分钟）
```bash
python download_from_hf.py
cd gear_sonic_deploy && ./deploy.sh --input-type zmq_manager real
python gear_sonic/scripts/launch_inference.py --camera-host <IP> --prompt "walk"
```

### VR遥操（1小时）
```bash
bash install_scripts/install_pico.sh
python gear_sonic/scripts/pico_manager_thread_server.py
# 戴上VR头显
```

### 教新任务（3-5天）
```bash
python gear_sonic/scripts/launch_data_collection.py --robot-ip <IP>
# 通过VR演示 50-100 次
uv run python gr00t/train/run_gr00t_train.py --dataset-path data/demos
python gear_sonic/scripts/launch_inference.py --prompt "custom task"
```

### 从头训练SONIC（1-2周）
```bash
pip install -e "gear_sonic/[training]"
python download_from_hf.py --training
accelerate launch --num_processes=64 gear_sonic/train_agent_trl.py +exp=...
```

---

## 📊 总结：开源了什么

| 模型 | 预训练权重 | 训练代码 | 推理代码 | 部署方案 |
|------|---------|--------|--------|--------|
| SONIC | ✅ (3个版本) | ✅ | ✅ | C++ + ONNX |
| Decoupled WBC | ✅ (2个版本) | ✅ | ✅ | C++ + ONNX |
| MotionBricks | ✅ (3个检查点) | ✅ | ✅ | Python |
| VLA | ❌ (需自己训练) | ✅ | ✅ | Python + C++ |
| SONIC H2 | ❌ (需自己训练) | ✅ | ✅ | C++ + ONNX |

**总结：** 🎉 开源了 5 个模型系列，其中 3 个有完整的预训练权重，全部提供训练和推理代码！

更新时间：2026-08-14
