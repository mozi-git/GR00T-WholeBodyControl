# GR00T 三大模型体系完整梳理

本文档用中文详细说明GR00T-WholeBodyControl项目中的三个核心模型的架构、训练方法、部署流程和数据格式。

---

## 1. 下身运动控制（Decoupled WBC）

### 1.1 模型概述

Decoupled WBC（解耦式全身控制）是NVIDIA GR00T N1.5和N1.6版本中使用的下身运动控制系统。采用分层控制架构：
- **下身（腿部）**：使用强化学习(RL)训练的策略，实现行走、跑步等基础运动
- **上身（躯干+手臂）**：使用逆运动学(IK)跟踪目标姿态

### 1.2 预训练模型

| 模型版本 | 位置 | 用途 | 说明 |
|---------|------|------|------|
| GR00T N1.5 | 已发布 | 基础下身控制 | 早期版本，支持基本行走 |
| GR00T N1.6 | 已发布 | 增强下身控制 | 改进版本，支持更复杂动作 |

**获取预训练权重：**
```bash
# 从HuggingFace下载（如果有发布）
python download_from_hf.py --decoupled-wbc
```

如果没有找到预训练权重，需要从原始论文或NVIDIA官方渠道获取。

### 1.3 数据与格式

Decoupled WBC 使用 **Isaac Lab** 在 MuJoCo 仿真环境中收集数据。

**数据格式特点：**
- 输入：当前机器人关节状态 + 期望速度命令
- 输出：下身关节力矩控制信号
- 数据存储：PPO训练数据在线生成，不需要预先采集

### 1.4 训练流程

#### 前置条件
- 安装 Isaac Lab（单独安装，不包含在本仓库）
- 配置 MuJoCo 仿真环境
- GPU 支持（推荐 A100 或更高）

#### 基础训练命令

```bash
# 安装Isaac Lab和训练依赖
# 参考: docs/source/getting_started/installation_training.md

# 启动下身控制训练（RL）
python decoupled_wbc/train_lower_body_rl.py \
    --config <config_path> \
    --num_envs 4096 \
    --device cuda:0
```

#### 训练配置关键参数

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| `num_envs` | 4096+ | 并行仿真环境数 |
| `num_iterations` | 50K+ | 训练迭代次数 |
| `learning_rate` | 1e-4 | RL 学习率 |
| `reward_scale` | 调整中 | 根据任务调整 |

#### 训练监测

```bash
# 使用 Weights & Biases (W&B) 监控训练
WANDB_PROJECT=decoupled_wbc python decoupled_wbc/train_lower_body_rl.py ...
```

**关键指标：**
- `reward/total` > 0.8：任务回报合理
- `success_rate` > 0.95：行走成功率
- `tracking_error` < 0.2：速度跟踪误差（m/s）

### 1.5 模型导出与部署

#### 导出为部署格式

```bash
# 导出为 ONNX（C++ 部署需要）
python decoupled_wbc/export_to_onnx.py \
    --checkpoint logs/model_step_50000.pt \
    --output policy/lower_body_controller.onnx
```

#### 部署到真实机器人

```bash
# 启动 C++ 推理栈
cd gear_sonic_deploy
./deploy.sh \
    --lower-body policy/lower_body_controller.onnx \
    --input-type zmq_manager \
    real
```

**部署要求：**
- Jetson Orin 或更高配置（运行在机器人上）
- TensorRT 8.0+（用于 ONNX 加速推理）
- ZMQ 通信（与上层规划器通信）

### 1.6 评估与验证

```bash
# 评估模型性能
python decoupled_wbc/eval_lower_body.py \
    --checkpoint policy/lower_body_controller.pt \
    --num_episodes 100 \
    --render True

# 生成评估视频
python decoupled_wbc/eval_lower_body.py \
    --checkpoint policy/lower_body_controller.pt \
    --num_episodes 10 \
    --render True \
    --save_video logs/eval_videos/
```

**评估指标：**
- 直线行走误差
- 转向精度
- 转向反应时间
- 在不规则地形上的稳定性

---

## 2. 全身动作模型（SONIC）

### 2.1 模型概述

SONIC（Supersizing mOtion tracking for Natural humanoid whole-body control）是NVIDIA最新的全身控制基础模型，具有以下特点：

- **通用架构**：支持多种输入模态（SMPL人体模型、G1机器人、VR遥操、SOMA骨架）
- **基于运动追踪**：从大规模人类运动数据学习自然运动
- **64维潜在令牌**：使用量化向量（FSQ）表示运动
- **实时控制**：50 Hz 控制频率
- **多模态融合**：单一解码器支持所有输入类型

### 2.2 预训练模型

SONIC 有三个官方发布版本，均可从 HuggingFace 直接下载使用：

| 模型版本 | 位置 | 输入参考 | 适用场景 | 特点 |
|---------|------|---------|---------|------|
| **默认SONIC** | `model_encoder.onnx`, `model_decoder.onnx` | 10帧SMPL（200ms前瞻） | 通用运动追踪、规划 | 兼容性最好 |
| **低延迟版本** | `low_latency/` | 4帧SMPL（80ms前瞻） | VR遥操、VLA推理 | 响应速度快 |
| **SONIC v1.1** | `sonic_v1_1/` | 10帧SMPL（200ms前瞻） | 3点遥操、VLA策略 | 机器人朝向归一化 |

**下载预训练模型：**

```bash
# 默认版本
python download_from_hf.py

# 低延迟版本
python download_from_hf.py --low-latency

# SONIC v1.1
python download_from_hf.py --sonic-v1-1

# 包含训练数据
python download_from_hf.py --training
```

### 2.3 SONIC 的数据格式

#### 2.3.1 运动数据格式 - motion_lib PKL

SONIC 的核心训练数据格式是 **motion_lib PKL 格式**。

**数据结构：**
```
data/
├── motion_lib_bones_seed/
│   ├── robot/                    # 原始G1关节轨迹
│   │   ├── motion_001.pkl
│   │   ├── motion_002.pkl
│   │   └── ...
│   ├── robot_filtered/           # 过滤后的G1轨迹（~130K）
│   │   ├── motion_001.pkl
│   │   └── ...
│   ├── soma_filtered/            # SOMA骨架轨迹（可选）
│   │   ├── motion_001.pkl
│   │   └── ...
└── smpl_filtered/                # SMPL人体模型参数（~131K）
    ├── motion_001.pkl
    └── ...
```

**每个PKL文件包含的数据：**

| 字段 | 数据类型 | 维度 | 说明 |
|------|---------|------|------|
| `joint_pos` | float32 | (T, 29) | G1机器人29个关节位置 |
| `joint_vel` | float32 | (T, 29) | G1关节速度 |
| `root_pos` | float32 | (T, 3) | 根节点（腰部）位置 |
| `root_rot` | float32 | (T, 4) | 根节点四元数旋转 |
| `smpl_body_pose` | float32 | (T, 63) | SMPL身体姿态（21个关节×3） |
| `smpl_global_orient` | float32 | (T, 3) | SMPL全局朝向 |
| `fps` | int | 标量 | 帧率（30 fps） |

**与 BeyondMimic 的区别：**

| 特性 | SONIC | BeyondMimic |
|------|-------|-----------|
| 输入模态 | 多模态（G1+SMPL+Teleop+SOMA） | 单模态（SMPL） |
| 数据格式 | motion_lib PKL | NPZ |
| 编码器架构 | 4个独立编码器+FSQ量化 | 单一编码器 |
| 控制频率 | 50 Hz | 30 Hz |
| 训练方法 | PPO+运动追踪 | 演示学习 |
| 输出 | 64维潜在令牌 | 直接关节控制 |

#### 2.3.2 SMPL 数据格式

**SMPL 输入规格：**
```python
# 每帧SMPL数据结构
smpl_data = {
    'body_pose': (63,),           # 21个关节的轴角表示
    'global_orient': (3,),         # 全局朝向（轴角）
    'betas': (10,),                # 身体形状参数
    'trans': (3,),                 # 全局平移
    'expression': (10,)            # 面部表情（可选）
}

# 时间序列：每个运动动作
# T帧，其中T = 运动持续时间 × 30fps
# 典型范围：100-1000帧
```

**获取SMPL数据：**

```bash
# 从Bones-SEED数据集提取SMPL参数
python gear_sonic/data_process/extract_smpl_from_bvh.py \
    --input /path/to/bones_seed/bvh/ \
    --output data/smpl_filtered \
    --fps 30 --num_workers 16
```

#### 2.3.3 数据过滤规则

**过滤标准（移除G1无法执行的动作）：**

```bash
# 过滤不适合的运动
python gear_sonic/data_process/filter_and_copy_bones_data.py \
    --source data/motion_lib_bones_seed/robot \
    --dest data/motion_lib_bones_seed/robot_filtered \
    --workers 16
```

**被过滤的动作类型：**
- 家具交互（坐、躺）
- 车辆操作（开车）
- 杂技动作（翻滚、后空翻）
- 高空站立（超过0.5m高度）
- 爬行动作（仅限某些类型）

**过滤效果：** ~130K 动作保留（总计142K中移除~8.7%）

### 2.4 SONIC 训练流程

#### 2.4.1 前置条件

| 要求 | 规格 | 说明 |
|------|------|------|
| Isaac Lab | 最新版本 | 单独安装，参考官方文档 |
| GPU | 64+张 | 推荐A100/H100 |
| 内存 | 512GB+ | 并行环境需求 |
| 存储 | 500GB+ | 运动数据集 |

#### 2.4.2 数据准备

**步骤1：下载原始数据**
```bash
# 从HuggingFace下载Bones-SEED（142K+动作）
# 地址：https://huggingface.co/datasets/bones-studio/seed
```

**步骤2：转换为motion_lib格式**
```bash
python gear_sonic/data_process/convert_soma_csv_to_motion_lib.py \
    --input /path/to/bones_seed/g1/csv/ \
    --output data/motion_lib_bones_seed/robot \
    --fps 30 \
    --fps_source 120 \
    --individual \
    --num_workers 16
```

**步骤3：过滤运动**
```bash
python gear_sonic/data_process/filter_and_copy_bones_data.py \
    --source data/motion_lib_bones_seed/robot \
    --dest data/motion_lib_bones_seed/robot_filtered \
    --workers 16
```

**步骤4：（可选）提取SOMA骨架**
```bash
python gear_sonic/data_process/extract_soma_joints_from_bvh.py \
    --input /path/to/bones_seed/bvh/ \
    --output data/motion_lib_bones_seed/soma \
    --fps 30 --num_workers 16 --skip_existing

# 过滤SOMA数据
python gear_sonic/data_process/filter_and_copy_bones_data.py \
    --source data/motion_lib_bones_seed/soma \
    --dest data/motion_lib_bones_seed/soma_filtered \
    --workers 16
```

#### 2.4.3 训练命令

**从头训练（推荐64+GPU）**
```bash
accelerate launch \
    --multi_gpu \
    --num_machines=8 \
    --num_processes=64 \
    --machine_rank=$MACHINE_RANK \
    --main_process_ip=$MASTER_ADDR \
    --main_process_port=$MASTER_PORT \
    gear_sonic/train_agent_trl.py \
    +exp=manager/universal_token/all_modes/sonic_release \
    num_envs=4096 headless=True \
    ++manager_env.commands.motion.motion_lib_cfg.motion_file=data/motion_lib_bones_seed/robot_filtered \
    ++manager_env.commands.motion.motion_lib_cfg.smpl_motion_file=data/smpl_filtered
```

**微调预训练模型**
```bash
accelerate launch --num_processes=8 gear_sonic/train_agent_trl.py \
    +exp=manager/universal_token/all_modes/sonic_release \
    +checkpoint=sonic_release/last.pt \
    num_envs=4096 headless=True \
    ++manager_env.commands.motion.motion_lib_cfg.motion_file=data/motion_lib_bones_seed/robot_filtered \
    ++manager_env.commands.motion.motion_lib_cfg.smpl_motion_file=data/smpl_filtered
```

**单机小规模调试**
```bash
python gear_sonic/train_agent_trl.py \
    +exp=manager/universal_token/all_modes/sonic_release \
    num_envs=16 headless=False \
    ++algo.config.num_learning_iterations=100 \
    ++manager_env.commands.motion.motion_lib_cfg.motion_file=sample_data/robot_filtered \
    ++manager_env.commands.motion.motion_lib_cfg.smpl_motion_file=sample_data/smpl_filtered
```

#### 2.4.4 训练监测

使用 Weights & Biases (W&B) 实时监控训练进度：

```bash
# 离线模式
WANDB_MODE=offline python gear_sonic/train_agent_trl.py ...

# 自定义项目
python gear_sonic/train_agent_trl.py ... \
    wandb.wandb_project=my_project \
    wandb.wandb_entity=my_team
```

**关键监控指标：**

| 指标 | 良好范围 | 说明 |
|------|---------|------|
| `rewards/total` | > 3.0 | 总回报 |
| `rewards/anchor_pos_err` | < 0.15 m | 根节点位置误差 |
| `rewards/body_pos_err` | < 0.10 m | 躯干位置误差 |
| `rewards/tracking_vr_5point` | > 0.80 | 5点追踪质量 |
| `rewards/time_out` | > 0.90 | 完成率 |
| `throughput/fps` | > 4000 | 训练吞吐量 |

**检查点保存位置：**
```
logs_rl/TRL_G1_Track/<experiment_name>-<timestamp>/
├── model_step_002000.pt
├── model_step_004000.pt
├── config.yaml
└── ...
```

### 2.5 SONIC 评估与验证

#### 2.5.1 评估模型

**评估指标模式：**
```bash
python gear_sonic/eval_agent_trl.py \
    +checkpoint=<path_to_checkpoint.pt> \
    +headless=True \
    ++eval_callbacks=im_eval \
    ++run_eval_loop=False \
    ++num_envs=128 \
    "+manager_env/terminations=tracking/eval" \
    "++manager_env.commands.motion.motion_lib_cfg.max_unique_motions=512"
```

**视频渲染模式：**
```bash
python gear_sonic/eval_agent_trl.py \
    +checkpoint=<path_to_checkpoint.pt> \
    +headless=True \
    ++eval_callbacks=im_eval \
    ++run_eval_loop=False \
    ++num_envs=8 \
    ++manager_env.config.render_results=True \
    "++manager_env.config.save_rendering_dir=/tmp/renders" \
    ++manager_env.config.env_spacing=10.0 \
    "~manager_env/recorders=empty" "+manager_env/recorders=render"
```

#### 2.5.2 评估指标

**期望收敛值：**

| 指标 | 训练值 | 评估值 | 说明 |
|------|--------|--------|------|
| `success_rate` | - | > 0.97 | 成功完成无异常终止 |
| `mpjpe_l` | - | < 30 mm | 本地关节位置误差 |
| `mpjpe_g` | - | < 200 mm | 全局关节位置误差 |
| `tracking_vr_5point` | > 0.80 | - | 5点追踪质量 |
| `tracking_relative_body_pos` | > 0.44 | - | 上身位置追踪 |

**良好收敛标志：** 100K迭代后，`success_rate` > 0.98，`mpjpe_l` < 29 mm

### 2.6 SONIC 导出与部署

#### 2.6.1 导出为ONNX

```bash
# 从PyTorch检查点导出
python gear_sonic/eval_agent_trl.py \
    +checkpoint=<path_to_checkpoint.pt> \
    +headless=True ++num_envs=1 \
    +export_onnx_only=true
```

**导出文件列表：**

| 文件 | 用途 | 说明 |
|------|------|------|
| `model_encoder.onnx` | C++推理 | 所有编码器合并 |
| `model_decoder.onnx` | C++推理 | 动作解码 |
| `model_smpl.onnx` | 姿态估计输入 | SMPL编码+解码 |
| `model_g1.onnx` | 机器人关节输入 | G1编码+解码 |
| `model_teleop.onnx` | VR遥操输入 | 遥操编码+解码 |
| `observation_config.yaml` | 配置 | 编码器参数 |

输出位置：`exported/` 文件夹（与检查点同目录）

#### 2.6.2 部署到机器人

**启动C++推理栈：**

```bash
cd gear_sonic_deploy

# 默认模型
./deploy.sh --input-type zmq_manager real

# 低延迟模型
./deploy.sh \
    --cp policy/low_latency/model \
    --obs-config policy/low_latency/observation_config.yaml \
    --input-type zmq_manager \
    real

# SONIC v1.1
./deploy.sh \
    --cp policy/sonic_v1_1/model \
    --obs-config policy/sonic_v1_1/observation_config.yaml \
    --input-type zmq_manager \
    real
```

**部署环境要求：**
- Jetson Orin 或更高配置
- TensorRT 8.0+
- CUDA 11.8+
- 100GB+ 存储空间

#### 2.6.3 Python推理框架

```bash
# VLA推理启动
python gear_sonic/scripts/launch_inference.py \
    --camera-host 192.168.123.164 \
    --prompt "pick up the cup"

# 低延迟版本
python gear_sonic/scripts/launch_inference.py \
    --deploy-checkpoint policy/low_latency/model \
    --deploy-obs-config policy/low_latency/observation_config.yaml \
    --camera-host 192.168.123.164 \
    --prompt "pick up the cup"

# SONIC v1.1
python gear_sonic/scripts/launch_inference.py \
    --deploy-checkpoint policy/sonic_v1_1/model \
    --deploy-obs-config policy/sonic_v1_1/observation_config.yaml \
    --camera-host 192.168.123.164 \
    --prompt "pick up the cup"
```

---

## 3. 遥操模仿学习模型（VLA-SONIC）

### 3.1 模型概述

遥操模仿学习模型将用户通过VR设备的动作演示转化为机器人的学习数据，进而训练视觉-语言-动作（VLA）策略。这套系统的核心流程是：

1. **数据收集**：通过VR遥操演示任务
2. **数据处理**：转换为VLA训练格式
3. **模型训练**：微调Isaac-GR00T VLA模型
4. **部署验证**：在真实机器人上执行任务

### 3.2 硬件要求

#### 3.2.1 工作站硬件（运行推理、收集、处理）

| 组件 | 推荐规格 | 说明 |
|------|---------|------|
| GPU | RTX 4090 / A100 | 用于VLA推理 |
| CPU | 16核+ | 数据处理 |
| 内存 | 64GB+ | 处理大型数据集 |
| 存储 | 2TB+ | 视频+参数文件 |
| 网络 | 1Gbps 以太网 | 与机器人通信 |

#### 3.2.2 机器人硬件（Unitree G1）

| 组件 | 规格 | 说明 |
|------|------|------|
| 主控 | Jetson Orin | 关键决策计算 |
| 相机 | Luxonis OAK 相机 | 头部EGO视角+腕部 |
| VR配件 | PICO 头显 | 遥操输入 |

#### 3.2.3 网络拓扑

```
┌─────────────────────────────────────────┐
│      工作站（数据收集、推理、处理）      │
│  ┌─────────────────────────────────────┐ │
│  │  VLA推理服务 (GPU)                  │ │
│  │  Isaac-GR00T PolicyServer          │ │
│  └─────────────────────────────────────┘ │
│  ┌─────────────────────────────────────┐ │
│  │  遥操流传输 (云XR/Isaac Teleop)   │ │
│  │  PICO 头显连接                     │ │
│  └─────────────────────────────────────┘ │
│  ┌─────────────────────────────────────┐ │
│  │  数据收集导出器                      │ │
│  │  LeRobot 数据集生成                │ │
│  └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
           ↑
     ZMQ TCP (1Gbps)
           ↓
┌─────────────────────────────────────────┐
│      机器人（Unitree G1）               │
│  ┌─────────────────────────────────────┐ │
│  │  C++ SONIC 全身控制器               │ │
│  │  50Hz 控制循环                      │ │
│  └─────────────────────────────────────┘ │
│  ┌─────────────────────────────────────┐ │
│  │  摄像头服务                         │ │
│  │  Luxonis OAK → JPEG 发布           │ │
│  └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### 3.3 数据收集流程

#### 3.3.1 前置准备

```bash
# 1. 完成快速开始（包括部署和模型下载）
# docs/source/getting_started/quickstart.md

# 2. 完成VR遥操设置（PICO硬件校准）
# docs/source/getting_started/vr_teleop_setup.md

# 3. 安装数据收集环境
bash install_scripts/install_data_collection.sh

# 4. 机器人上安装摄像头服务
ssh <robot_user>@<robot_ip>
bash install_scripts/install_camera_server.sh
```

#### 3.3.2 摄像头配置

**支持的摄像头类型：**
- Luxonis OAK-D（推荐，RGB-D）
- Luxonis OAK-1（轻量级）
- RealSense（已支持但未最近测试）
- USB 摄像头（已支持但未最近测试）

**3D打印摄像头支架：**
```
hardware/camera_mount/
├── STL文件/
│   ├── head_mount.stl         # 头部EGO摄像头支架
│   └── wrist_mount.stl        # 腕部摄像头支架
├── README                      # 打印参数
└── BOM (Bill of Materials)    # 物料清单
```

**摄像头检测（在机器人上）：**

```bash
source .venv_camera/bin/activate
python -c "import depthai as dai; print(dai.Device.getAllAvailableDevices())"
```

#### 3.3.3 启动数据收集

**工作站环境准备：**

```bash
# 激活数据收集环境
source .venv_data_collection/bin/activate

# 启动摄像头查看器（可选）
python gear_sonic/camera/view_cameras.py \
    --robot-ip <robot_ip> \
    --display
```

**启动数据导出器：**

```bash
python gear_sonic/scripts/run_data_exporter.py \
    --robot-ip 192.168.123.161 \
    --output-dir data/collected_teleop_demos \
    --dataset-name task_001_pick_cube \
    --fps 20 \
    --compress True
```

#### 3.3.4 遥操演示数据收集

```bash
# 启动完整数据收集栈（C++控制+遥操+导出）
python gear_sonic/scripts/launch_data_collection.py \
    --robot-ip 192.168.123.161 \
    --camera-server-ip 192.168.123.161:5555 \
    --output-dir data/collected_teleop_demos \
    --dataset-name task_001_pick_cube \
    --duration-minutes 120 \
    --fps 20
```

**收集工作流程：**

```
遥操演示开始
    ↓
PICO头显捕获用户动作
    ↓
变换为SMPL姿态（SOMA编码器）
    ↓
送入SONIC全身控制器
    ↓
C++执行关节控制
    ↓
摄像头捕获RGB帧
    ↓
导出为LeRobot数据集
    ↓
收集完成
```

### 3.4 数据处理与验证

#### 3.4.1 数据格式转换

**LeRobot 数据集结构：**

```
data/collected_teleop_demos/task_001_pick_cube/
├── metadata.json              # 数据集元数据
├── train/                     # 训练集
│   ├── episode_0/
│   │   ├── images/
│   │   │   ├── 000000.jpg
│   │   │   └── ...
│   │   ├── states.npy         # 关节状态时间序列
│   │   ├── actions.npy        # 关节动作时间序列
│   │   ├── smpl_poses.npy     # 遥操SMPL姿态
│   │   └── episode_info.json  # 元数据
│   └── episode_1/
│       └── ...
└── val/                       # 验证集
    └── ...
```

**每个episode包含的字段：**

| 字段 | 数据类型 | 形状 | 说明 |
|------|---------|------|------|
| `images` | uint8 | (T, H, W, 3) | RGB摄像头图像 |
| `states` | float32 | (T, 29) | G1关节状态 |
| `actions` | float32 | (T, 29) | G1关节目标位置 |
| `smpl_poses` | float32 | (T, 63) | SMPL身体姿态 |
| `timestamps` | float32 | (T,) | 时间戳 |
| `task_description` | str | - | 任务文本描述 |

#### 3.4.2 数据验证脚本

```bash
# 验证导出的数据集
python gear_sonic/scripts/process_dataset.py \
    --dataset-path data/collected_teleop_demos/task_001_pick_cube \
    --validate \
    --visualize-episodes 0,1,2
```

**验证检查项：**
- 帧数一致性（图像、状态、动作对齐）
- 时间戳连续性
- 关节范围合理性（检测异常值）
- SMPL姿态有效性

#### 3.4.3 数据统计

```bash
# 生成数据集统计报告
python gear_sonic/scripts/process_dataset.py \
    --dataset-path data/collected_teleop_demos/task_001_pick_cube \
    --stats \
    --output report.json
```

**统计内容：**
```json
{
    "total_episodes": 50,
    "total_frames": 50000,
    "total_duration_seconds": 2500,
    "fps": 20,
    "image_resolution": "1280x720",
    "joint_ranges": {
        "left_hip": [-1.57, 1.57],
        ...
    },
    "task_distribution": {
        "pick": 25,
        "place": 15,
        "navigate": 10
    }
}
```

### 3.5 VLA 模型训练

#### 3.5.1 前置要求

| 要求 | 说明 |
|------|------|
| Isaac-GR00T | 单独安装（参考官方文档）|
| GPU | A100/H100（单个足够，多GPU推荐）|
| 数据集 | LeRobot 格式（参考3.4.1）|
| 内存 | 40GB+ VRAM |

#### 3.5.2 VLA 微调命令

**基础微调（单GPU）：**

```bash
# 激活Isaac-GR00T环境
source /path/to/isaac_groot_env/bin/activate

# 微调VLA模型
uv run python gr00t/train/run_gr00t_train.py \
    --model-name gr00t-n1.7 \
    --embodiment-tag UNITREE_G1_SONIC \
    --dataset-path data/collected_teleop_demos/task_001_pick_cube \
    --output-dir logs/vla_finetuned \
    --num-epochs 10 \
    --batch-size 8 \
    --learning-rate 1e-5 \
    --device cuda:0
```

**多GPU分布式训练：**

```bash
uv run accelerate launch \
    --multi_gpu \
    --num_processes 4 \
    gr00t/train/run_gr00t_train.py \
    --model-name gr00t-n1.7 \
    --embodiment-tag UNITREE_G1_SONIC \
    --dataset-path data/collected_teleop_demos/task_001_pick_cube \
    --output-dir logs/vla_finetuned_distributed \
    --num-epochs 10 \
    --batch-size 32 \
    --learning-rate 1e-5
```

#### 3.5.3 训练配置

**关键超参数：**

| 参数 | 推荐值 | 范围 | 说明 |
|------|--------|------|------|
| `num_epochs` | 10-20 | 5-50 | 训练轮数 |
| `batch_size` | 8-32 | 4-128 | 批大小 |
| `learning_rate` | 1e-5 | 1e-6～1e-4 | 学习率 |
| `warmup_steps` | 500 | 100-1000 | 预热步数 |
| `weight_decay` | 1e-4 | 0-1e-3 | L2正则化 |

**监控训练进度：**

```bash
# 启用Weights & Biases监控
uv run python gr00t/train/run_gr00t_train.py \
    --use-wandb \
    --wandb-project vla-sonic-finetuning \
    ...
```

**关键训练指标：**
- `loss/total`：总损失（应稳定下降）
- `loss/action`：动作预测损失
- `loss/vision`：视觉编码损失
- `accuracy/top1`：Top-1准确率（> 0.8）

#### 3.5.4 检查点保存

```
logs/vla_finetuned/
├── checkpoint_epoch_01.pt
├── checkpoint_epoch_05.pt
├── checkpoint_epoch_10.pt
├── best_model.pt
├── config.yaml
└── training_log.json
```

### 3.6 VLA 推理与部署

#### 3.6.1 启动推理服务

**在GPU机器上启动PolicyServer：**

```bash
# 激活Isaac-GR00T环境
source /path/to/isaac_groot_env/bin/activate

# 启动推理服务
uv run python gr00t/eval/run_gr00t_server.py \
    --model-path logs/vla_finetuned/best_model.pt \
    --embodiment-tag UNITREE_G1_SONIC \
    --device cuda:0 \
    --port 5550
```

#### 3.6.2 推理环境设置

**在工作站上安装推理环境：**

```bash
bash install_scripts/install_inference.sh

# 激活推理环境
source .venv_inference/bin/activate
```

#### 3.6.3 完整推理栈启动

**启动所有组件：**

```bash
# 终端1：启动C++SONIC控制器
cd gear_sonic_deploy
./deploy.sh \
    --cp policy/sonic_v1_1/model \
    --obs-config policy/sonic_v1_1/observation_config.yaml \
    --input-type zmq_manager \
    real

# 终端2：启动VLA推理客户端
python gear_sonic/scripts/launch_inference.py \
    --camera-host 192.168.123.161 \
    --gr00t-server-ip 127.0.0.1:5550 \
    --prompt "pick up the red cube and place it on the table"
```

#### 3.6.4 通信架构

```
┌─────────────────────────┐
│  VLA Policy Server      │
│  (Isaac-GR00T)          │
│  Port 5550              │
└────────────┬────────────┘
             │ ZMQ REQ/REP
             ▼
┌─────────────────────────────────────┐
│  VLA Inference Client               │
│  (run_vla_inference.py)             │
│  ┌─────────────────────────────────┐│
│  │ 1. 获取摄像头图像                ││
│  │ 2. 编码为SMPL姿态                ││
│  │ 3. 查询VLA策略                  ││
│  │ 4. 发送动作到C++控制器           ││
│  └─────────────────────────────────┘│
└─────────────────────────────────────┘
   ↑                            ↓
   └──ZMQ SUB (状态)  ZMQ PUB (动作)
                                ↓
                    ┌──────────────────────────┐
                    │ C++ SONIC Controller     │
                    │ (gear_sonic_deploy)      │
                    │ 50Hz 控制循环            │
                    └──────────────────────────┘
```

### 3.7 部署验证与测试

#### 3.7.1 仿真环境测试

**在MuJoCo中测试VLA策略：**

```bash
python gear_sonic/eval_agent_trl.py \
    +checkpoint=logs/vla_finetuned/best_model.pt \
    +headless=False \
    ++num_envs=4 \
    ++eval_mode=vla \
    ++vla_prompts="['pick up the cube', 'walk forward', 'kneel down']"
```

#### 3.7.2 真实机器人验证

**测试前检查清单：**

- [ ] C++控制器编译且通信正常
- [ ] 摄像头服务在机器人上运行
- [ ] VLA服务器可连接（网络测试）
- [ ] 安全操作员就位
- [ ] 机器人在清空安全区域

**简单任务测试：**

```bash
# 启动所有栈（如3.6.3所示）

# 执行简单运动测试
python gear_sonic/scripts/launch_inference.py \
    --camera-host 192.168.123.161 \
    --gr00t-server-ip 127.0.0.1:5550 \
    --prompt "stand still" \
    --episode-length 50

# 验证动作执行
# - 观察：机器人是否保持站立？
# - 检查：关节是否颤抖或异常？
# - 监控：CPU/GPU使用率是否正常？
```

#### 3.7.3 常见故障排查

| 症状 | 可能原因 | 解决方案 |
|------|--------|--------|
| 摄像头无图像 | 相机未连接或驱动问题 | 检查`install_camera_server.sh`日志 |
| VLA推理缓慢 | 网络延迟或GPU内存不足 | 减少批大小，检查网络延迟 |
| 机器人抖动 | 控制延迟或环境不匹配 | 切换到低延迟模型，检查传感器校准 |
| 任务失败 | VLA模型不适合该任务 | 收集更多示范数据，重新微调 |

#### 3.7.4 性能评估

**端到端延迟测试：**

```bash
# 在日志中记录时间戳
# 运行VLA推理并测量：
# T1: 摄像头捕获时间
# T2: VLA预测时间
# T3: 控制执行时间
# 总延迟 = T3 - T1

python gear_sonic/scripts/measure_latency.py \
    --camera-host 192.168.123.161 \
    --num-samples 100
```

**期望性能：**
- 摄像头延迟：30-50ms
- VLA推理：200-500ms（取决于模型大小）
- 控制延迟：20-50ms
- 总延迟：250-600ms

---

## 总结对比表

| 特性 | 下身控制（Decoupled WBC） | 全身模型（SONIC） | 遥操VLA |
|------|--------------------------|------------------|--------|
| **核心方法** | RL + IK | 运动追踪 PPO | 模仿学习 |
| **输入** | 速度命令 | SMPL/G1/遥操/SOMA | RGB视觉+文本 |
| **输出** | 下身关节力矩 | 全身关节位置 | 全身关节位置 |
| **控制频率** | 50Hz | 50Hz | 10-20Hz |
| **预训练权重** | ✓ (N1.5/N1.6) | ✓ (3个版本) | ✗ (需收集数据) |
| **数据格式** | 在线生成 | motion_lib PKL | LeRobot |
| **训练数据量** | 仿真 | 142K+ 人类动作 | 任务特定演示 |
| **训练硬件** | 64+ GPU | 64+ GPU | 单个A100+ |
| **部署复杂度** | 中等 | 中等 | 高（VLA服务）|
| **实时性** | 低延迟 | 低延迟 | 中等延迟 |
| **多模态支持** | 否 | 是（4种） | 否（单VLA） |

---

## 快速开始检查清单

### 仅体验模型
- [ ] 下载模型：`python download_from_hf.py`
- [ ] 启动部署：`cd gear_sonic_deploy && ./deploy.sh --input-type zmq_manager sim`
- [ ] MuJoCo可视化：可选启用

### 微调SONIC模型
- [ ] 安装Isaac Lab
- [ ] 下载数据：`python download_from_hf.py --training`
- [ ] 准备数据集：转换+过滤
- [ ] 运行训练：8+ GPUs最小

### 收集遥操数据
- [ ] 硬件：G1机器人+PICO+OAK相机
- [ ] 工作站设置：`install_data_collection.sh`
- [ ] 机器人设置：`install_camera_server.sh`
- [ ] 启动收集：`launch_data_collection.py`

### 训练VLA模型
- [ ] 安装Isaac-GR00T
- [ ] 准备LeRobot数据集
- [ ] 运行微调：`run_gr00t_train.py`
- [ ] 推理验证：`run_gr00t_server.py` + `launch_inference.py`

---

## 常见问题 (FAQ)

**Q: 能否只使用SMPL作为输入，跳过G1运动数据？**
A: 可以。SONIC支持单编码器配置。使用 `sonic_smpl_only` 配置。

**Q: 遥操VLA模型可以处理除了G1以外的机器人吗？**
A: 理论上可以，但需要为新机器人重新标定SMPL→关节的映射，并收集新的训练数据。

**Q: 如何在边界计算资源上运行？**
A: 
- Decoupled WBC：可在单GPU上进行评估
- SONIC：需要多GPU进行实时训练，但推理可在Jetson Orin上运行
- VLA：微调至少需要一张A100

**Q: 模型部署后如何更新策略？**
A: 
1. 通过新数据微调PyTorch检查点
2. 导出新的ONNX
3. 替换 `policy/model_encoder.onnx` 和 `model_decoder.onnx`
4. 重启C++部署

**Q: 数据隐私和知识产权如何处理？**
A: 所有收集的遥操数据属于用户。预训练的SONIC权重遵循NVIDIA Open Model License。
