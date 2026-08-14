# 仿真测试完全指南

这个仓库内置了 **MuJoCo 仿真环境**，可以在没有真实机器人的情况下测试所有开源模型。

---

## ✅ 快速答案

**Q: 开源的模型可以仿真测试吗？**

**A: 可以！** 所有开源模型都支持 MuJoCo 仿真：
- ✅ SONIC（全部3个版本）
- ✅ Decoupled WBC
- ✅ MotionBricks
- ⚠️ VLA（需要修改配置）

**最快体验（5分钟）：**
```bash
# 安装仿真环境
bash install_scripts/install_mujoco_sim.sh

# 启动仿真
cd gear_sonic_deploy
./deploy.sh --input-type zmq_manager sim

# 在另一个终端发送指令
python gear_sonic/scripts/launch_inference.py \
    --camera-host 127.0.0.1 \
    --prompt "walk forward"
```

---

## 🏗️ 仿真环境支持

### 支持的仿真引擎

| 引擎 | 支持 | 用途 | 性能 |
|------|------|------|------|
| **MuJoCo** | ✅ | SONIC/Decoupled WBC 推理 | 实时 |
| **Isaac Lab** | ✅ | SONIC/Decoupled WBC 训练 | 快速并行 |
| **RoboCasa** | ✅ | 操纵任务仿真 | 逼真 |

### 仿真 vs 真实机器人

```
┌──────────────────────────────────────┐
│ 纯仿真测试（推荐先从这开始）        │
├──────────────────────────────────────┤
│ 优点：                               │
│ ✅ 无需硬件                          │
│ ✅ 无崩溃风险                        │
│ ✅ 快速迭代                          │
│ ✅ 可视化调试                        │
│                                      │
│ 缺点：                               │
│ ❌ 物理可能不完全匹配真实            │
│ ❌ 控制延迟特性不同                  │
│ ❌ 传感器噪声仿真有限                │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ 仿真后部署到真实机器人               │
├──────────────────────────────────────┤
│ 最佳实践流程：                       │
│ 1. 在 MuJoCo 中开发测试             │
│ 2. 验证基本逻辑                      │
│ 3. 部署到真实 G1                     │
│ 4. 监控性能差异                      │
└──────────────────────────────────────┘
```

---

## 🚀 快速开始（5 种方式）

### 方式 1：最快体验（不需要 GPU）

```bash
# 第1步：安装仿真环境
bash install_scripts/install_mujoco_sim.sh

# 第2步：启动仿真服务
cd gear_sonic_deploy
./deploy.sh --input-type zmq_manager sim

# 第3步：发送控制指令（另一个终端）
python gear_sonic/scripts/launch_inference.py \
    --camera-host 127.0.0.1 \
    --prompt "stand up"

# ✅ 完成！观看仿真 G1 执行动作
```

**需要什么：** 
- 下载好的模型（~2GB）
- Python 环境
- 不需要 GPU

**效果：** 
- 仿真中 G1 根据文本指令执行运动
- 延迟：~100-200ms
- 视觉：MuJoCo 渲染窗口

**时间：** 5分钟

---

### 方式 2：测试低延迟模型

```bash
# 下载低延迟版本
python download_from_hf.py --low-latency

# 启动仿真（使用低延迟模型）
cd gear_sonic_deploy
./deploy.sh \
    --cp policy/low_latency/model \
    --obs-config policy/low_latency/observation_config.yaml \
    --input-type zmq_manager sim

# 测试推理延迟
python gear_sonic/scripts/launch_inference.py \
    --deploy-checkpoint policy/low_latency/model \
    --deploy-obs-config policy/low_latency/observation_config.yaml \
    --camera-host 127.0.0.1 \
    --prompt "walk"
```

**对比三个版本的延迟差异**

---

### 方式 3：键盘控制仿真

```bash
# 启动仿真
cd gear_sonic_deploy && ./deploy.sh --input-type zmq_manager sim

# 启用键盘控制（另一个终端）
python gear_sonic/scripts/run_keyboard_control.py \
    --camera-host 127.0.0.1

# 键盘快捷键
# W - 向前走
# A - 左转
# S - 向后走
# D - 右转
# Space - 停止
# Q - 跳舞
# E - 挥手
```

---

### 方式 4：运动追踪评估（需要 Isaac Lab）

```bash
# 评估 SONIC 在仿真中的运动追踪
python gear_sonic/eval_agent_trl.py \
    +checkpoint=sonic_release/last.pt \
    +headless=False \
    ++num_envs=4 \
    ++manager_env.config.render_results=True \
    "++manager_env.config.save_rendering_dir=/tmp/renders" \
    ++eval_mode=motion_tracking

# 生成的视频在 /tmp/renders/ 中
```

---

### 方式 5：MotionBricks 实时生成（仿真）

```bash
# 启动 MotionBricks 交互式演示
cd motionbricks
python demo_interactive.py --use-mujoco

# 键盘控制实时运动生成
# 按方向键改变运动风格
# 看仿真中 G1 实时响应
```

---

## 📦 仿真环境安装

### 标准安装（推荐）

```bash
# 一键安装仿真环境
bash install_scripts/install_mujoco_sim.sh

# 脚本会自动：
# 1. 创建 .venv_sim 虚拟环境
# 2. 安装 MuJoCo
# 3. 安装相关依赖
# 4. 验证安装

# 激活环境
source .venv_sim/bin/activate
```

### 手动安装（如需自定义）

```bash
# 创建虚拟环境
python -m venv .venv_sim
source .venv_sim/bin/activate

# 安装 MuJoCo
pip install mujoco>=3.0.0

# 安装项目依赖
pip install -e "gear_sonic/[sim]"

# 验证安装
python -c "import mujoco; print(mujoco.__version__)"
```

### 验证安装

```bash
# 测试 MuJoCo 是否正常
python -c "from mujoco import MuJoCo; print('✅ MuJoCo installed')"

# 测试 G1 模型加载
python gear_sonic/scripts/run_sim_loop.py --help
```

---

## 🎮 仿真控制方式

### 1. 文本指令控制

```python
# 通过文本指令控制仿真 G1
prompts = [
    "walk forward 2 meters",
    "turn left 90 degrees",
    "jump",
    "dance",
    "wave your hand",
    "sit down",
    "stand up",
]

for prompt in prompts:
    python gear_sonic/scripts/launch_inference.py \
        --camera-host 127.0.0.1 \
        --prompt "$prompt"
```

### 2. 键盘/手柄控制

```bash
# 键盘
python gear_sonic/scripts/run_keyboard_control.py --camera-host 127.0.0.1

# 游戏手柄（Joystick）
python gear_sonic/scripts/run_gamepad_control.py --camera-host 127.0.0.1
```

**键盘映射：**
```
W/A/S/D - 前后左右移动
Space - 停止
Q/E - 特殊动作
↑/↓/←/→ - 细致调整
```

### 3. 程序化控制

```python
# Python API 直接控制
from gear_sonic.inference.client import InferenceClient

client = InferenceClient(host="127.0.0.1")

# 发送一系列指令
commands = [
    {"prompt": "walk forward", "duration": 2.0},
    {"prompt": "turn right", "duration": 1.0},
    {"prompt": "wave hand", "duration": 1.0},
]

for cmd in commands:
    client.execute(cmd["prompt"], duration=cmd["duration"])
    print(f"✅ Executed: {cmd['prompt']}")
```

---

## 📊 仿真中的关键指标

### 仿真可视化窗口显示的信息

```
MuJoCo 仿真窗口
├─ 左侧：G1 机器人 3D 模型
├─ 右侧：实时数据面板
│  ├─ 关节位置 (29 DOF)
│  ├─ 脚接触力 (接地检测)
│  ├─ 根节点速度
│  ├─ 能量消耗
│  └─ 实时帧率 (FPS)
└─ 底部：控制参数
   └─ 追踪误差、能量等
```

### 性能指标

| 指标 | 仿真中预期值 | 说明 |
|------|-----------|------|
| **控制频率** | 50 Hz | SONIC 标准频率 |
| **运动追踪误差** | < 50mm | 相比真实会更好 |
| **计算延迟** | 20-50ms | 包含推理 |
| **总系统延迟** | 50-100ms | 仿真中较低 |

---

## 🧪 典型仿真测试场景

### 场景 1：验证基本功能

```bash
# 下载模型
python download_from_hf.py

# 启动仿真
bash install_scripts/install_mujoco_sim.sh
cd gear_sonic_deploy && ./deploy.sh sim

# 测试一系列基本动作
python -c "
from gear_sonic.inference.client import InferenceClient
client = InferenceClient('127.0.0.1')

for prompt in ['stand up', 'walk forward', 'turn left', 'sit down']:
    client.execute(prompt)
    print(f'✅ {prompt}')
"
```

### 场景 2：测试三个 SONIC 版本的差异

```bash
# 逐一测试三个版本
for version in "default" "low_latency" "sonic_v1_1"; do
    echo "Testing $version..."
    
    # 下载对应版本
    if [ "$version" = "default" ]; then
        python download_from_hf.py
    elif [ "$version" = "low_latency" ]; then
        python download_from_hf.py --low-latency
    else
        python download_from_hf.py --sonic-v1-1
    fi
    
    # 启动仿真测试
    cd gear_sonic_deploy && ./deploy.sh sim
    
    # 记录性能指标
    python measure_performance.py --model $version
done
```

### 场景 3：调试数据管道

```bash
# 在仿真中测试数据收集管道
python gear_sonic/scripts/launch_data_collection.py \
    --camera-host 127.0.0.1 \
    --output-dir data/sim_test \
    --fps 20

# 观察摄像头数据是否正确
python gear_sonic/camera/view_cameras.py \
    --camera-host 127.0.0.1 \
    --display
```

---

## ⚙️ 仿真配置调整

### 物理参数

```yaml
# gear_sonic/config/env/sim/g1_sim.yaml

physics:
  gravity: 9.81
  dt: 0.001              # 仿真时间步
  solver: PGS            # 物理求解器
  
contact:
  friction: 0.5          # 摩擦系数
  damping: 0.01          # 阻尼
  
rendering:
  fps: 60                # 渲染帧率
  width: 1280
  height: 720
```

### 控制延迟

```yaml
# 仿真中的延迟参数
delay:
  sensor_delay: 0        # 关闭传感器延迟（仿真）
  control_delay: 0       # 关闭控制延迟
  network_delay: 0       # 无网络延迟
  
# 真实机器人
delay:
  sensor_delay: 20ms
  control_delay: 10ms
  network_delay: 50ms
```

---

## 🔍 调试仿真

### 启用详细日志

```bash
# 启用调试日志
MUJOCO_GL=osmesa python gear_sonic/scripts/launch_inference.py \
    --camera-host 127.0.0.1 \
    --prompt "walk" \
    --verbose DEBUG
```

### 常见问题

| 问题 | 解决方案 |
|------|--------|
| MuJoCo 窗口崩溃 | 尝试 `MUJOCO_GL=osmesa` |
| 仿真很慢 | 减少 `num_envs`，关闭可视化 |
| 连接拒绝 | 确保先启动 `deploy.sh sim` |
| 模型加载失败 | 检查 ONNX 文件路径 |

---

## 📈 仿真 → 真实的转移学习

### 验证仿真中的模型是否能在真实机器人上工作

```bash
# 步骤 1：在仿真中充分测试
./deploy.sh sim
python launch_inference.py --camera-host 127.0.0.1

# 步骤 2：监控以下指标
# - 运动追踪误差
# - 稳定性
# - 计算延迟
# - 能量消耗

# 步骤 3：记录最佳参数
export BEST_CONFIG="sonic_v1_1"

# 步骤 4：部署到真实 G1
./deploy.sh --cp policy/$BEST_CONFIG/model real

# 步骤 5：对比性能差异
# 观察：
# - 真实延迟 vs 仿真延迟
# - 真实稳定性 vs 仿真
# - 传感器噪声影响
```

### 期望的差异

| 方面 | 仿真 | 真实 | 原因 |
|------|------|------|------|
| **延迟** | 50-100ms | 200-400ms | 网络、传感器处理 |
| **追踪误差** | < 50mm | ~100mm | 传感器噪声 |
| **稳定性** | 极好 | 较好 | 控制延迟、地面不平 |
| **能量** | ~100W | ~150-200W | 摩擦、空气阻力 |

---

## 🎯 推荐的测试流程

### 第一阶段：验证（1天）
```
1. 安装仿真环境
2. 下载预训练模型
3. 运行基本测试
4. 验证文本指令、键盘控制
5. 记录性能指标
```

### 第二阶段：深度测试（2-3天）
```
1. 对比三个 SONIC 版本
2. 测试各种动作
3. 测试 MotionBricks
4. 测试 Decoupled WBC
5. 调整仿真参数
```

### 第三阶段：优化（1周）
```
1. 微调模型
2. 测试自定义数据
3. 优化控制参数
4. 性能基准测试
5. 准备部署到真实机器人
```

---

## 📚 相关文档

| 文档 | 用途 |
|------|------|
| [g1_quick_start.md](g1_quick_start.md) | G1 使用指南（包含仿真部分） |
| [quick_reference.md](quick_reference.md) | 仿真相关命令速查 |
| [models_overview.md](models_overview.md) | 模型评估部分 |

---

## ✅ 仿真测试完成检查列表

- [ ] 仿真环境安装成功
- [ ] MuJoCo 窗口能打开
- [ ] 模型下载成功
- [ ] 文本指令控制正常
- [ ] 观察到 G1 执行动作
- [ ] 键盘控制正常
- [ ] 性能指标在预期范围
- [ ] 无报错和警告
- [ ] 已测试所有 3 个 SONIC 版本
- [ ] 已测试 Decoupled WBC
- [ ] 已测试 MotionBricks
- [ ] 延迟、精度、稳定性符合预期
- [ ] 准备好部署到真实机器人

---

**总结：仓库内置完整的 MuJoCo 仿真支持，所有开源模型都可以先在仿真中充分测试，再部署到真实 G1 机器人。** 🚀

更新时间：2026-08-14
