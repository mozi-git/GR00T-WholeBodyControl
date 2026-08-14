# GR00T 全身控制中文文档

欢迎查看GR00T-WholeBodyControl项目的中文文档。本目录提供了针对中文用户的详细说明。

## 📚 核心文档

### [三大模型体系完整梳理](models_overview.md)

这是最核心的文档，从三个维度系统地讲解GR00T项目：

#### 1. **下身运动控制 (Decoupled WBC)**
- 模型架构：RL+IK分层控制
- 预训练权重获取
- 训练方法和硬件要求
- 部署流程
- 评估指标

#### 2. **全身动作模型 (SONIC)**
- 多模态输入支持（SMPL、G1、VR、SOMA）
- 三个官方预训练版本及适用场景
- **详细数据格式说明**：
  - motion_lib PKL格式
  - SMPL参数规范
  - 与BeyondMimic的区别
- 完整训练流程（从数据准备到评估）
- ONNX导出和C++部署
- 实时监控指标

#### 3. **遥操模仿学习 (VLA-SONIC)**
- 硬件要求（工作站+机器人）
- **数据收集全流程**
- LeRobot数据集格式
- Isaac-GR00T VLA微调
- 推理部署和验证
- 故障排查指南

### [Unitree H2 机器人完整指南](h2_models_guide.md)

针对Unitree H2人形机器人的SONIC模型详细说明：

- **H2硬件规格**：31 DOF vs G1的29 DOF
- **SONIC H2配置**：关节映射、参数调整
- **数据准备**：SMPL→H2的retarget流程
- **训练指南**：从头训练H2专用模型
- **评估部署**：ONNX导出和真实机器人部署
- **G1↔H2对比**：兼容性和性能差异

### 快速查找

根据你的使用场景，选择对应章节：

| 场景 | 推荐阅读 |
|------|--------|
| 我想只用预训练模型 | 跳转到各模型的"预训练模型"和"部署"章节 |
| 我想微调SONIC | [2. 全身动作模型 → 4. 训练流程](models_overview.md#24-sonic-训练流程) |
| 我想收集遥操数据训练VLA | [3. 遥操模仿学习 → 完整流程](models_overview.md#3-遥操模仿学习模型vla-sonic) |
| 我想理解数据格式 | [2.3 SONIC的数据格式](models_overview.md#23-sonic-的数据格式) |
| 我遇到了部署问题 | [故障排查](models_overview.md#37-部署验证与测试) |

---

## 🚀 快速开始

### 场景1：只想用预训练SONIC模型
```bash
# 1. 下载模型
python download_from_hf.py

# 2. 启动仿真
cd gear_sonic_deploy
./deploy.sh --input-type zmq_manager sim

# 3. 运行推理客户端
python gear_sonic/scripts/launch_inference.py \
    --camera-host 127.0.0.1 \
    --prompt "walk forward"
```

### 场景2：微调SONIC进行特定任务
```bash
# 1. 安装训练环境（需Isaac Lab）
pip install -e "gear_sonic/[training]"

# 2. 准备数据
python download_from_hf.py --training
# 下载并处理Bones-SEED数据

# 3. 启动训练（推荐64+ GPUs）
accelerate launch --num_processes=8 gear_sonic/train_agent_trl.py \
    +exp=manager/universal_token/all_modes/sonic_release \
    +checkpoint=sonic_release/last.pt \
    num_envs=4096 headless=True
```

### 场景3：从零开始收集遥操数据训练VLA
```bash
# 1. 硬件准备
# - Unitree G1 机器人
# - PICO VR 头显
# - Luxonis OAK 摄像头
# - 工作站 (GPU)

# 2. 环境安装（机器人）
ssh <robot>
bash install_scripts/install_camera_server.sh

# 3. 环境安装（工作站）
bash install_scripts/install_data_collection.sh
bash install_scripts/install_inference.sh

# 4. 收集演示数据
python gear_sonic/scripts/launch_data_collection.py \
    --robot-ip 192.168.123.161 \
    --output-dir data/collected_demos

# 5. 微调VLA模型
uv run python gr00t/train/run_gr00t_train.py \
    --model-name gr00t-n1.7 \
    --dataset-path data/collected_demos \
    --output-dir logs/vla_finetuned

# 6. 推理验证
python gear_sonic/scripts/launch_inference.py \
    --camera-host 192.168.123.161 \
    --gr00t-server-ip 127.0.0.1:5550 \
    --prompt "pick up the cube"
```

---

## 🔧 关键配置与命令

### 模型选择

SONIC 提供三个版本，根据场景选择：

```bash
# 默认版本（通用）
python download_from_hf.py

# 低延迟版本（VR遥操优先）
python download_from_hf.py --low-latency

# v1.1版本（3点头显追踪）
python download_from_hf.py --sonic-v1-1
```

### 训练关键参数速查

| 参数 | 值范围 | 推荐值 | 影响 |
|------|--------|--------|------|
| `num_envs` | 256-4096 | 4096 | GPU内存用量，更大更快收敛 |
| `num_learning_iterations` | 10K-200K | 100K | 训练轮数，更多更好的策略 |
| `learning_rate` | 1e-5~1e-4 | 2e-5 | 学习速度，太大易发散 |
| `batch_size` | 4-128 | 32 | 每步更新样本数 |

### 部署命令速查

```bash
# 仿真环境测试
./deploy.sh --input-type zmq_manager sim

# 真实机器人部署（默认版本）
./deploy.sh --input-type zmq_manager real

# 真实机器人部署（低延迟版本）
./deploy.sh \
    --cp policy/low_latency/model \
    --obs-config policy/low_latency/observation_config.yaml \
    --input-type zmq_manager real

# 真实机器人部署（v1.1版本）
./deploy.sh \
    --cp policy/sonic_v1_1/model \
    --obs-config policy/sonic_v1_1/observation_config.yaml \
    --input-type zmq_manager real
```

---

## 📊 模型对比速查表

| 特性 | Decoupled WBC | SONIC | VLA-SONIC |
|------|--------------|-------|-----------|
| **控制方式** | RL + IK | 运动追踪 | 视觉+语言指导 |
| **输入信号** | 速度命令 | SMPL/遥操 | RGB图像+文本 |
| **输出** | 下身力矩 | 全身位置 | 全身位置 |
| **实时性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **预训练** | ✓ | ✓ (3版) | ✗ |
| **易用性** | 中等 | 简单 | 复杂 |
| **适用场景** | 基础运动 | 多场景运动 | 复杂任务 |
| **学习成本** | 高 | 中 | 中 |

---

## ❓ FAQ

**Q: 三个模型分别用来干什么？**

A: 
- **Decoupled WBC**：机器人下身运动的基础控制（腿部RL+躯干IK）
- **SONIC**：全身运动模型，可以做多种动作，是上身控制的主力
- **VLA-SONIC**：结合视觉和语言理解，让机器人执行自然语言任务

**Q: 预训练模型在哪里？**

A: 都在 HuggingFace 上，运行 `python download_from_hf.py` 下载即可

**Q: 我是否需要所有三个模型？**

A: 不需要。大多数场景只需要 SONIC。如果需要特定下身控制，才需要 Decoupled WBC。VLA 只在需要执行复杂任务时才用。

**Q: 训练需要多少GPU？**

A:
- SONIC：最少8个，推荐64个以上
- Decoupled WBC：同上
- VLA 微调：1-4个 A100 就够

**Q: 数据格式为什么这么复杂？**

A: SONIC 支持多种输入类型（SMPL、G1、VR、SOMA），每种都有专门的编码器。多模态使得模型更灵活，但数据处理确实需要小心。

**Q: 如何快速验证训练是否有效？**

A: 看 W&B Dashboard：
- `rewards/total` 应该在增加
- `rewards/tracking_*` 应该接近 1
- 没有 NaN 值表示训练稳定

**Q: 部署后响应慢怎么办？**

A: 
- 切换到 `--low-latency` 模型
- 检查网络延迟（应 < 50ms）
- 减少 VLA 模型大小

---

## 📖 相关资源

- **完整文档**：[nvlabs.github.io/GR00T-WholeBodyControl](https://nvlabs.github.io/GR00T-WholeBodyControl/)
- **论文**：[SONIC arxiv 2511.07820](https://arxiv.org/abs/2511.07820)
- **数据集**：[Bones-SEED huggingface](https://huggingface.co/datasets/bones-studio/seed)
- **模型**：[GEAR-SONIC huggingface](https://huggingface.co/nvidia/GEAR-SONIC)
- **视频演示**：[Live Web Demo](https://nvlabs.github.io/GEAR-SONIC/demo.html)

---

## 💡 使用建议

1. **第一次接触**：阅读[三大模型体系完整梳理](models_overview.md)的概述部分
2. **准备训练**：按照对应模型的"数据准备"和"训练流程"章节逐步执行
3. **遇到问题**：查阅该章节的"故障排查"部分，或参考英文官方文档
4. **想要微调**：从预训练模型开始，使用自己的数据进行微调，通常效果更好

---

**最后更新**：2026-08-14  
**维护者**：GR00T 团队  
**反馈**：gear-wbc@nvidia.com
