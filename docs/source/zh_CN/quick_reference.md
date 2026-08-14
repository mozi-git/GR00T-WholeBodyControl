# GR00T 快速参考卡片

这份文档包含所有常用命令、配置和参数的快速查询。

---

## 📦 模型下载

```bash
# 默认SONIC（通用版）
python download_from_hf.py

# 默认 + 训练数据
python download_from_hf.py --training

# 低延迟版本（VR遥操优先）
python download_from_hf.py --low-latency

# SONIC v1.1（3点遥操）
python download_from_hf.py --sonic-v1-1

# Decoupled WBC（如果有发布）
python download_from_hf.py --decoupled-wbc
```

---

## 🚀 快速启动

### 仿真测试（无硬件）

```bash
# 启动MuJoCo仿真 + 默认SONIC控制器
cd gear_sonic_deploy
./deploy.sh --input-type zmq_manager sim

# 在另一个终端：启动推理客户端
python gear_sonic/scripts/launch_inference.py \
    --camera-host 127.0.0.1 \
    --prompt "walk forward 2 meters"
```

### 真实机器人部署

```bash
# 基础部署
cd gear_sonic_deploy
./deploy.sh --input-type zmq_manager real

# 低延迟版本
./deploy.sh \
    --cp policy/low_latency/model \
    --obs-config policy/low_latency/observation_config.yaml \
    --input-type zmq_manager real

# SONIC v1.1
./deploy.sh \
    --cp policy/sonic_v1_1/model \
    --obs-config policy/sonic_v1_1/observation_config.yaml \
    --input-type zmq_manager real
```

---

## 📊 SONIC 训练

### 环境准备

```bash
# 安装Isaac Lab（单独进行，参考官方文档）
# https://isaac-sim.github.io/IsaacLab/

# 在Isaac Lab环境中安装训练依赖
pip install -e "gear_sonic/[training]"

# 创建MuJoCo仿真环境
bash install_scripts/install_mujoco_sim.sh

# 激活仿真环境
source .venv_sim/bin/activate
```

### 数据准备

```bash
# 下载原始数据集（Bones-SEED）
# https://huggingface.co/datasets/bones-studio/seed

# 下载训练用的检查点和SMPL数据
python download_from_hf.py --training

# 转换数据格式
python gear_sonic/data_process/convert_soma_csv_to_motion_lib.py \
    --input /path/to/bones_seed/g1/csv/ \
    --output data/motion_lib_bones_seed/robot \
    --fps 30 --fps_source 120 --individual --num_workers 16

# 过滤数据（移除G1无法执行的动作）
python gear_sonic/data_process/filter_and_copy_bones_data.py \
    --source data/motion_lib_bones_seed/robot \
    --dest data/motion_lib_bones_seed/robot_filtered \
    --workers 16

# （可选）提取SOMA骨架
python gear_sonic/data_process/extract_soma_joints_from_bvh.py \
    --input /path/to/bones_seed/bvh/ \
    --output data/motion_lib_bones_seed/soma \
    --fps 30 --num_workers 16
```

### 从头训练（64+ GPUs）

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

### 微调预训练模型

```bash
# 单机 8 GPU
accelerate launch --num_processes=8 gear_sonic/train_agent_trl.py \
    +exp=manager/universal_token/all_modes/sonic_release \
    +checkpoint=sonic_release/last.pt \
    num_envs=4096 headless=True \
    ++manager_env.commands.motion.motion_lib_cfg.motion_file=data/motion_lib_bones_seed/robot_filtered \
    ++manager_env.commands.motion.motion_lib_cfg.smpl_motion_file=data/smpl_filtered

# 多机 64 GPU
accelerate launch \
    --multi_gpu --num_machines=8 --num_processes=64 \
    --machine_rank=$MACHINE_RANK \
    --main_process_ip=$MASTER_ADDR \
    --main_process_port=$MASTER_PORT \
    gear_sonic/train_agent_trl.py \
    +exp=manager/universal_token/all_modes/sonic_release \
    +checkpoint=sonic_release/last.pt \
    num_envs=4096 headless=True \
    ++manager_env.commands.motion.motion_lib_cfg.motion_file=data/motion_lib_bones_seed/robot_filtered \
    ++manager_env.commands.motion.motion_lib_cfg.smpl_motion_file=data/smpl_filtered
```

### 小规模调试

```bash
python gear_sonic/train_agent_trl.py \
    +exp=manager/universal_token/all_modes/sonic_release \
    num_envs=16 headless=False \
    ++algo.config.num_learning_iterations=100 \
    ++manager_env.commands.motion.motion_lib_cfg.motion_file=sample_data/robot_filtered \
    ++manager_env.commands.motion.motion_lib_cfg.smpl_motion_file=sample_data/smpl_filtered
```

### 训练配置快速查询

| 参数 | 值 | 用途 |
|------|-----|------|
| `num_envs` | 4096 | 并行环境数（对应GPU内存） |
| `num_learning_iterations` | 100000 | 训练迭代总数 |
| `learning_rate` | 2e-5 | PPO学习率 |
| `entropy_coef` | 0.01 | 探索系数 |
| `gamma` | 0.99 | 折扣因子 |
| `gae_lambda` | 0.95 | GAE系数 |

### 监测训练（W&B）

```bash
# 启用W&B在线监控
python gear_sonic/train_agent_trl.py ... \
    wandb.wandb_project=my_project \
    wandb.wandb_entity=my_team

# 离线模式（本地保存）
WANDB_MODE=offline python gear_sonic/train_agent_trl.py ...

# 禁用W&B
python gear_sonic/train_agent_trl.py ... \
    use_wandb=false
```

**关键监控指标：**
- `rewards/total` > 3.0 ✓
- `rewards/tracking_vr_5point` > 0.80 ✓
- `rewards/time_out` > 0.90 ✓
- `throughput/fps` > 4000 ✓

---

## 📈 评估

### 评估模型（指标）

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

### 评估模型（渲染视频）

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

### 预查看参考运动

```bash
python gear_sonic/train_agent_trl.py \
    +exp=manager/universal_token/all_modes/sonic_release \
    ++replay=True \
    num_envs=4 \
    headless=False
```

**期望评估指标：**

| 指标 | 良好 | 优秀 |
|------|------|------|
| `success_rate` | > 0.95 | > 0.98 |
| `mpjpe_l` (mm) | < 35 | < 30 |
| `mpjpe_g` (mm) | < 250 | < 200 |

---

## 🔄 ONNX导出

### 导出部署文件

```bash
python gear_sonic/eval_agent_trl.py \
    +checkpoint=<path_to_checkpoint.pt> \
    +headless=True ++num_envs=1 \
    +export_onnx_only=true
```

**输出文件：**
```
exported/
├── model_encoder.onnx        # 所有编码器
├── model_decoder.onnx        # 解码器
├── model_smpl.onnx          # SMPL编码+解码
├── model_g1.onnx            # G1编码+解码  
├── model_teleop.onnx        # 遥操编码+解码
└── observation_config.yaml   # 编码器配置
```

### 复制到部署位置

```bash
# 复制ONNX文件到部署文件夹
cp exported/* policy/model_encoder.onnx policy/
cp exported/* policy/model_decoder.onnx policy/
cp exported/observation_config.yaml policy/

# 或指定其他模型版本
mkdir -p policy/my_model_v2
cp exported/* policy/my_model_v2/
```

---

## 📹 数据收集（遥操演示）

### 环境安装

```bash
# 工作站
bash install_scripts/install_data_collection.sh
bash install_scripts/install_inference.sh

# 机器人（SSH连接）
ssh <robot_user>@<robot_ip>
bash install_scripts/install_camera_server.sh

# VR遥操设置
bash install_scripts/install_pico.sh
```

### 启动数据收集

```bash
# 激活环境
source .venv_data_collection/bin/activate

# 启动完整收集栈
python gear_sonic/scripts/launch_data_collection.py \
    --robot-ip 192.168.123.161 \
    --camera-server-ip 192.168.123.161:5555 \
    --output-dir data/collected_teleop_demos \
    --dataset-name my_task_001 \
    --duration-minutes 120 \
    --fps 20

# 或分步启动
# 终端1：启动C++控制器
cd gear_sonic_deploy
./deploy.sh --input-type zmq_manager real

# 终端2：启动VR遥操
source .venv_teleop/bin/activate
python gear_sonic/scripts/pico_manager_thread_server.py \
    --input-source vive

# 终端3：启动数据导出
source .venv_data_collection/bin/activate
python gear_sonic/scripts/run_data_exporter.py \
    --robot-ip 192.168.123.161 \
    --output-dir data/collected_demos \
    --dataset-name my_task
```

### 数据验证

```bash
# 验证和可视化数据
python gear_sonic/scripts/process_dataset.py \
    --dataset-path data/collected_teleop_demos/my_task_001 \
    --validate \
    --visualize-episodes 0,1,2

# 生成统计报告
python gear_sonic/scripts/process_dataset.py \
    --dataset-path data/collected_teleop_demos/my_task_001 \
    --stats \
    --output report.json
```

---

## 🤖 VLA 微调与推理

### VLA 微调

```bash
# 单GPU微调
uv run python gr00t/train/run_gr00t_train.py \
    --model-name gr00t-n1.7 \
    --embodiment-tag UNITREE_G1_SONIC \
    --dataset-path data/collected_teleop_demos/my_task \
    --output-dir logs/vla_finetuned \
    --num-epochs 10 \
    --batch-size 8 \
    --learning-rate 1e-5 \
    --device cuda:0

# 多GPU微调
uv run accelerate launch \
    --multi_gpu --num_processes 4 \
    gr00t/train/run_gr00t_train.py \
    --model-name gr00t-n1.7 \
    --embodiment-tag UNITREE_G1_SONIC \
    --dataset-path data/collected_teleop_demos/my_task \
    --output-dir logs/vla_finetuned_distributed \
    --num-epochs 10 \
    --batch-size 32 \
    --learning-rate 1e-5
```

### VLA 推理

```bash
# 终端1：启动PolicyServer（GPU机器）
source /path/to/isaac_groot_env/bin/activate
uv run python gr00t/eval/run_gr00t_server.py \
    --model-path logs/vla_finetuned/best_model.pt \
    --embodiment-tag UNITREE_G1_SONIC \
    --device cuda:0 \
    --port 5550

# 终端2：启动C++控制器（机器人或工作站）
cd gear_sonic_deploy
./deploy.sh \
    --cp policy/sonic_v1_1/model \
    --obs-config policy/sonic_v1_1/observation_config.yaml \
    --input-type zmq_manager \
    real

# 终端3：启动推理客户端（工作站）
source .venv_inference/bin/activate
python gear_sonic/scripts/launch_inference.py \
    --camera-host 192.168.123.161 \
    --gr00t-server-ip 127.0.0.1:5550 \
    --prompt "pick up the red cube and place it on the table"
```

### VLA 训练配置

| 参数 | 推荐值 | 范围 |
|------|--------|------|
| `num_epochs` | 10 | 5-50 |
| `batch_size` | 8-32 | 4-128 |
| `learning_rate` | 1e-5 | 1e-6～1e-4 |
| `warmup_steps` | 500 | 100-1000 |
| `weight_decay` | 1e-4 | 0-1e-3 |

---

## 🐛 常见故障排查

### 数据和格式问题

| 问题 | 原因 | 解决 |
|------|------|------|
| PKL文件无法读取 | 数据转换失败 | 检查`convert_soma_csv_to_motion_lib.py`日志 |
| SMPL维度不对 | 格式不匹配 | 确认是(T, 63)而非(T, 72) |
| NPZ格式报错 | 与BeyondMimic混淆 | SONIC用PKL，不是NPZ |

### 训练问题

| 问题 | 原因 | 解决 |
|------|------|------|
| GPU内存不足 | `num_envs`太大 | 减少`num_envs`或减少GPU数量 |
| 训练无进展 | 学习率太小 | 增加`learning_rate` |
| 回报为NaN | 学习率太大或数据问题 | 减少学习率，检查数据 |
| 收敛很慢 | GPU数量不足 | 增加GPU或接受更长的训练时间 |

### 部署问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 摄像头无图像 | 相机驱动或USB连接 | 检查`lsusb`，重装驱动 |
| ZMQ连接失败 | 网络或端口占用 | 检查防火墙，尝试其他端口 |
| 推理缓慢 | 网络延迟或模型太大 | 使用`--low-latency`模型，检查网络 |
| 机器人抖动 | 控制延迟或环境偏移 | 切换低延迟模型，校准传感器 |

### 推理问题

| 问题 | 原因 | 解决 |
|------|------|------|
| PolicyServer无响应 | GPU内存或模型路径 | 检查路径，减少批大小 |
| 推理很慢 | 模型大小或GPU繁忙 | 使用更小的VLA模型 |
| 任务执行失败 | VLA不适合该任务 | 收集更多相关演示，重新微调 |

---

## 💾 常用文件路径

```
GR00T-WholeBodyControl/
├── gear_sonic/
│   ├── train_agent_trl.py           # 主训练脚本
│   ├── eval_agent_trl.py            # 评估脚本
│   ├── data_process/                # 数据处理脚本
│   ├── scripts/
│   │   ├── launch_data_collection.py
│   │   ├── launch_inference.py
│   │   ├── run_data_exporter.py
│   │   └── pico_manager_thread_server.py
│   └── configs/                     # 训练配置文件
├── gear_sonic_deploy/
│   ├── deploy.sh                    # 部署启动脚本
│   └── policy/                      # 模型文件夹
├── decoupled_wbc/
│   └── （下身控制脚本）
├── data/
│   ├── motion_lib_bones_seed/       # 运动库
│   ├── smpl_filtered/               # SMPL数据
│   └── collected_teleop_demos/      # 收集的演示
├── logs_rl/                         # 训练日志
├── docs/source/                     # 文档
└── install_scripts/                 # 安装脚本
```

---

## 🔑 关键概念速查

| 概念 | 解释 | 相关文件 |
|------|------|---------|
| **FSQ** | Finite Scalar Quantization，SONIC用来量化运动的技术 | 论文 |
| **motion_lib** | PKL格式的运动库，包含G1关节轨迹 | `convert_soma_csv_to_motion_lib.py` |
| **SMPL** | 参数化人体模型，用于表示人类姿态 | `data_process/` |
| **MuJoCo** | 物理仿真引擎，用于Isaac Lab | `install_mujoco_sim.sh` |
| **LeRobot** | HuggingFace的机器人数据集格式 | `run_data_exporter.py` |
| **ZMQ** | 消息队列系统，用于C++和Python通信 | `deploy.sh` |
| **ONNX** | 开放式神经网络交换格式，用于C++推理 | `eval_agent_trl.py` |
| **TensorRT** | NVIDIA的推理优化框架 | C++部署 |

---

## 📞 获取帮助

- **官方文档**：https://nvlabs.github.io/GR00T-WholeBodyControl/
- **论文**：https://arxiv.org/abs/2511.07820
- **模型**：https://huggingface.co/nvidia/GEAR-SONIC
- **数据集**：https://huggingface.co/datasets/bones-studio/seed
- **反馈**：gear-wbc@nvidia.com

---

**最后更新**：2026-08-14
