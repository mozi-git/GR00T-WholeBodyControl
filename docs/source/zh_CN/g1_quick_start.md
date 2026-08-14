# G1 机器人用户快速开始指南

如果你已经拥有 Unitree G1 机器人，本指南帮助你快速上手 SONIC 模型。

---

## 🚀 我有 G1 机器人，现在能干什么？

### 情景 1：我想直接用预训练的模型控制 G1（最简单）

**需要的东西：**
- ✅ G1 机器人一台
- ✅ 工作站（有网卡连接到机器人）
- ⏱️ 时间：30分钟

**步骤：**

```bash
# 第1步：下载预训练模型（到工作站）
python download_from_hf.py

# 第2步：编译并启动C++控制器（在工作站）
cd gear_sonic_deploy
./deploy.sh --input-type zmq_manager real

# 第3步：启动推理客户端（在工作站的另一个终端）
python gear_sonic/scripts/launch_inference.py \
    --camera-host 192.168.123.161 \
    --prompt "walk forward 2 meters"
```

**结果：** G1 执行你的文本指令

---

### 情景 2：我想用 VR 头显远程操控 G1（遥操）

**需要的东西：**
- ✅ G1 机器人
- ✅ PICO VR 头显
- ✅ 工作站（RTX 4090 级别）
- ⏱️ 时间：1小时

**步骤：**

```bash
# 第1步：安装VR遥操环境（工作站）
bash install_scripts/install_pico.sh

# 第2步：启动C++控制器（工作站）
cd gear_sonic_deploy
./deploy.sh --input-type zmq_manager real

# 第3步：启动VR遥操服务（工作站）
source .venv_teleop/bin/activate
python gear_sonic/scripts/pico_manager_thread_server.py \
    --input-source vive

# 第4步：戴上 PICO 头显进行远程操控
# （此时 G1 会跟随你的身体动作）
```

**结果：** 实时 VR 遥操，延迟 ~200-300ms

---

### 情景 3：我想收集演示数据来训练自己的任务模型

**需要的东西：**
- ✅ G1 机器人 + 摄像头（OAK-D 推荐）
- ✅ PICO VR 头显
- ✅ 工作站（GPU）
- ⏱️ 时间：3-5 天（收集 + 训练）

**步骤：**

```bash
# 第1步：在机器人上安装摄像头服务
ssh <robot_user>@<robot_ip>
bash install_scripts/install_camera_server.sh

# 第2步：在工作站安装数据收集环境
bash install_scripts/install_data_collection.sh
bash install_scripts/install_inference.sh

# 第3步：启动数据收集（所有栈都在工作站运行）
python gear_sonic/scripts/launch_data_collection.py \
    --robot-ip 192.168.123.161 \
    --camera-server-ip 192.168.123.161:5555 \
    --output-dir data/collected_demos_task_001 \
    --dataset-name pick_and_place \
    --duration-minutes 120 \
    --fps 20

# 第4步：通过VR头显演示任务（重复 50-100 次）
# （戴上 PICO，执行"拿起红色杯子放到桌子上"的动作）

# 第5步：验证数据集
python gear_sonic/scripts/process_dataset.py \
    --dataset-path data/collected_demos_task_001 \
    --validate

# 第6步：微调 VLA 模型
# （需要安装 Isaac-GR00T，单独进行）
uv run python gr00t/train/run_gr00t_train.py \
    --model-name gr00t-n1.7 \
    --embodiment-tag UNITREE_G1_SONIC \
    --dataset-path data/collected_demos_task_001 \
    --output-dir logs/vla_task_001_finetuned \
    --num-epochs 10 --batch-size 8 --learning-rate 1e-5

# 第7步：部署并测试
python gear_sonic/scripts/launch_inference.py \
    --camera-host 192.168.123.161 \
    --gr00t-server-ip 127.0.0.1:5550 \
    --prompt "pick up the red cup and place it on the table"
```

**结果：** G1 可以执行自定义任务

---

### 情景 4：我想进一步优化/微调预训练模型

**需要的东西：**
- ✅ G1 机器人
- ✅ 8+ GPUs（A100/H100）
- ✅ 特定任务的运动数据
- ⏱️ 时间：1-2 周

**步骤：**

```bash
# 第1步：安装训练环境（需要 Isaac Lab）
# 参考官方文档安装 Isaac Lab
pip install -e "gear_sonic/[training]"

# 第2步：准备数据（使用 Bones-SEED 或自己收集的数据）
python download_from_hf.py --training
# 或使用你收集的数据

# 第3步：微调预训练模型
accelerate launch --num_processes=8 gear_sonic/train_agent_trl.py \
    +exp=manager/universal_token/all_modes/sonic_release \
    +checkpoint=sonic_release/last.pt \
    num_envs=4096 headless=True \
    ++manager_env.commands.motion.motion_lib_cfg.motion_file=data/your_motions \
    ++manager_env.commands.motion.motion_lib_cfg.smpl_motion_file=data/smpl_filtered

# 第4步：评估新模型
python gear_sonic/eval_agent_trl.py \
    +checkpoint=logs_rl/.../model_step_100000.pt \
    +headless=True ++eval_callbacks=im_eval

# 第5步：导出部署
python gear_sonic/eval_agent_trl.py \
    +checkpoint=logs_rl/.../model_step_100000.pt \
    +export_onnx_only=true

# 第6步：部署到 G1
cp exported/* policy/my_custom_model/
./deploy.sh --cp policy/my_custom_model/model real
```

**结果：** 自定义优化的 SONIC 模型

---

## 📋 快速决策表

根据你的需求选择方案：

| 你的需求 | 方案 | 难度 | 时间 | 所需硬件 |
|---------|------|------|------|---------|
| 试一下模型效果 | 情景1 | ⭐ | 30分钟 | 工作站 |
| 远程控制 G1 | 情景2 | ⭐⭐ | 1小时 | 工作站+VR |
| 让 G1 学习新任务 | 情景3 | ⭐⭐⭐ | 3-5天 | 工作站+VR+摄像头 |
| 优化模型性能 | 情景4 | ⭐⭐⭐⭐ | 1-2周 | 8+ GPUs |

---

## 🔧 实际步骤详解

### 方案1：最快体验（30分钟）

```bash
# 确保在项目根目录
cd /path/to/GR00T-WholeBodyControl

# 1. 下载模型（~2GB）
pip install huggingface_hub
python download_from_hf.py

# 2. 进入部署目录
cd gear_sonic_deploy

# 3. 启动 C++ 控制器（连接真实 G1）
./deploy.sh --input-type zmq_manager real

# 4. 在另一个终端，启动推理客户端
cd /path/to/GR00T-WholeBodyControl
python gear_sonic/scripts/launch_inference.py \
    --camera-host <G1的IP地址> \
    --prompt "stand up and wave"

# 5. 观察 G1 执行动作
```

**预期结果：**
```
✓ C++ 控制器运行于 50 Hz
✓ G1 接收到控制信号
✓ G1 执行自然运动（站立、挥手等）
```

---

### 方案2：VR 遥操（1小时）

```bash
# 前置：完成方案1的下载步骤

# 1. 安装 VR 依赖
bash install_scripts/install_pico.sh

# 2. 激活 VR 环境
source .venv_teleop/bin/activate

# 3. 标定 PICO 头显
python gear_sonic/scripts/pico_calibration.py

# 4. 在工作站启动 C++ 控制器
cd gear_sonic_deploy
./deploy.sh --input-type zmq_manager real

# 5. 在另一个工作站终端启动 VR 服务
source .venv_teleop/bin/activate
python gear_sonic/scripts/pico_manager_thread_server.py

# 6. 戴上 PICO 头显
# 你的动作会直接映射到 G1
```

**实际使用：**
```
头部动作  →  G1 头部跟随
双臂动作  →  G1 双臂跟随
身体倾斜  →  G1 身体倾斜
走路      →  G1 走路
```

---

### 方案3：数据收集 + VLA 训练（3-5 天）

#### 第1天：准备环境

```bash
# 工作站
bash install_scripts/install_data_collection.sh
bash install_scripts/install_inference.sh

# 机器人（SSH 连接）
ssh <robot_user>@<robot_ip>
bash install_scripts/install_camera_server.sh
# 脚本会自动检测摄像头并创建 systemd 服务
```

#### 第2-4天：收集数据

```bash
# 启动完整数据收集栈
python gear_sonic/scripts/launch_data_collection.py \
    --robot-ip 192.168.123.161 \
    --camera-server-ip 192.168.123.161:5555 \
    --output-dir data/my_task_demos \
    --dataset-name pick_cup_task \
    --duration-minutes 180 \
    --fps 20

# 在工作站的另一个终端：看摄像头画面
python gear_sonic/camera/view_cameras.py \
    --robot-ip 192.168.123.161 \
    --display
```

**数据收集流程：**
```
1. 启动数据收集脚本
2. 穿上 PICO VR 头显
3. 执行任务（比如"拿起红杯子放在桌子上"）
4. 重复 50-100 次
5. 脚本自动生成 LeRobot 数据集
```

#### 第5天：微调并部署

```bash
# 数据验证
python gear_sonic/scripts/process_dataset.py \
    --dataset-path data/my_task_demos \
    --stats --output report.json

# 微调 VLA（需要 Isaac-GR00T）
uv run python gr00t/train/run_gr00t_train.py \
    --model-name gr00t-n1.7 \
    --embodiment-tag UNITREE_G1_SONIC \
    --dataset-path data/my_task_demos \
    --num-epochs 10 --batch-size 8 --learning-rate 1e-5

# 部署验证
python gear_sonic/scripts/launch_inference.py \
    --camera-host 192.168.123.161 \
    --gr00t-server-ip 127.0.0.1:5550 \
    --prompt "pick up the red cup and place it on the table"
```

---

## ⚠️ 常见问题

### Q1: 我没有 VR 头显，能用吗？

**A:** 可以，但功能受限：
- ✅ 可以用预训练模型控制 G1（文本指令）
- ✅ 可以用键盘/手柄控制
- ❌ 无法进行高质量的遥操演示收集
- ❌ 无法训练需要演示的 VLA 模型

**替代方案：**
```bash
# 用键盘控制
python gear_sonic/examples/keyboard_control.py \
    --robot-ip 192.168.123.161

# 用手柄控制
python gear_sonic/examples/gamepad_control.py \
    --robot-ip 192.168.123.161
```

### Q2: 我没有 OAK 摄像头，能收集数据吗？

**A:** 可以，但要修改配置：
- OAK 摄像头是推荐的（RGB-D）
- RealSense 也支持但未最近测试
- USB 摄像头支持但质量可能差

```bash
# 使用 RealSense 替代
source .venv_camera/bin/activate
pip install pyrealsense2
# 修改 camera server 配置
python gear_sonic/camera/camera_server.py --camera-type realsense
```

### Q3: 我的工作站 GPU 不够怎么办？

**A:** 根据 GPU 选择方案：

| GPU 配置 | 能做什么 |
|---------|--------|
| RTX 4090 | ✅ 所有方案（推荐） |
| RTX 3090 | ✅ 方案1-3（速度慢）|
| RTX 4080 | ✅ 方案1-2，方案3较慢 |
| 无 GPU | ✅ 方案1-2（使用 CPU，很慢） |

### Q4: 第一次连接 G1 机器人，怎么设置网络？

**A:** 假设 G1 的 IP 是 `192.168.123.161`：

```bash
# 1. 测试连接
ping 192.168.123.161

# 2. 如果 ping 不通，检查网络
# G1 和工作站应该在同一个局域网

# 3. 查看 G1 当前状态
ssh unitree@192.168.123.161
# 或查看 G1 的显示屏获取 IP

# 4. 如果 SSH 出问题，直接指定 IP 即可
python gear_sonic/scripts/launch_inference.py \
    --camera-host 192.168.123.161 \
    --robot-ip 192.168.123.161 \
    --prompt "test"
```

### Q5: 控制延迟太高怎么办？

**A:** 优化步骤：

```bash
# 1. 使用低延迟模型
python download_from_hf.py --low-latency

cd gear_sonic_deploy
./deploy.sh \
    --cp policy/low_latency/model \
    --obs-config policy/low_latency/observation_config.yaml \
    --input-type zmq_manager real

# 2. 检查网络延迟
ping -c 10 192.168.123.161
# 应该 < 10ms

# 3. 调整其他参数
# 减少 SMPL 处理延迟
# 优化相机帧率
```

**期望延迟分解：**
- 相机延迟: 30-50ms
- 网络延迟: 5-20ms
- VLA 推理: 200-300ms
- 控制执行: 20-50ms
- **总计: 250-450ms**

---

## 📊 选择你的路径

```
我有 G1 机器人
    ↓
    ├─ "我只想试试" → 方案1（30分钟）
    │
    ├─ "我想远程控制" → 方案2（1小时 + VR）
    │
    ├─ "我想教它新任务" → 方案3（3-5天）
    │
    └─ "我想深度优化" → 方案4（1-2周）
```

---

## 📚 相关文档速查

| 你想干什么 | 查看文档 |
|----------|--------|
| 理解 SONIC 模型 | [models_overview.md](models_overview.md#2-全身动作模型sonic) |
| 查询具体命令 | [quick_reference.md](quick_reference.md) |
| 理解数据格式 | [data_formats_comparison.md](data_formats_comparison.md) |
| VR 遥操设置 | [models_overview.md 第3章](models_overview.md#3-遥操模仿学习模型vla-sonic) |
| 故障排查 | [quick_reference.md 常见故障](quick_reference.md#-常见故障排查) |

---

## ✅ 验收清单

### 方案1 完成标志
- [ ] 模型下载成功（~2GB）
- [ ] C++ 控制器编译成功
- [ ] 能连接到 G1（ping 通）
- [ ] 看到 G1 执行动作
- [ ] 能使用文本指令

### 方案2 完成标志
- [ ] 方案1 的所有项
- [ ] PICO 头显标定成功
- [ ] VR 服务启动正常
- [ ] 能用 VR 遥操 G1
- [ ] 延迟可接受（< 500ms）

### 方案3 完成标志
- [ ] 摄像头服务在机器人上运行
- [ ] 数据收集脚本正常运行
- [ ] 收集了 50+ 条演示
- [ ] LeRobot 数据集生成成功
- [ ] 微调完成，模型能执行新任务

---

## 🎯 下一步

1. **立即开始**：选择方案1，30分钟体验
2. **深入学习**：阅读 [models_overview.md](models_overview.md)
3. **遇到问题**：查阅 [quick_reference.md](quick_reference.md#-常见故障排查)
4. **想要优化**：参考方案4的微调指南

---

**准备好了吗？** 现在就选择你的方案开始吧！🚀

更新时间：2026-08-14
