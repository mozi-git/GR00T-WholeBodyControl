# VR遥操验证与调试完全指南

你已经有PICO设备和G1机器人，本指南帮助你一步步验证和调试VR遥操系统。

---

## ✅ 快速检查清单

在开始之前，确认你有：

- [ ] **PICO VR头显** (最新版本)
- [ ] **Unitree G1 机器人** (可以通电、能移动)
- [ ] **工作站** (Ubuntu 20.04+, 网卡)
- [ ] **Pico Band 腰部追踪器** (可选，但推荐)
- [ ] **网络连接** (工作站和G1在同一局域网)
- [ ] **模型文件** (已下载 SONIC 模型)
- [ ] **项目代码** (GR00T 仓库已克隆)

---

## 🔧 第一步：硬件和网络验证

### 1.1 检查 PICO 设备

**在 PICO 头显上操作：**

```
1. 戴上 PICO 头显
2. 进入设置 → 系统 → 关于本机
3. 查看 PICO 的 IP 地址 (记下来)
4. 启用开发者模式：设置 → 开发者选项
5. 启用 USB 调试
6. 测试头显追踪：
   - 看周围环境是否正确渲染
   - 转头、转身检查追踪是否灵敏
   - 手柄是否能检测到
```

**在工作站上检查 PICO：**

```bash
# 连接 PICO（USB）
adb devices

# 应该看到类似输出
# List of attached devices
# XXXXXX                device

# 查看 PICO 的网络信息
adb shell ip addr show

# 记下 PICO 的局域网 IP（通常 192.168.x.x）
```

### 1.2 检查 G1 机器人

**关键信息要获取：**

```bash
# 1. G1 的 IP 地址（通常 192.168.123.161）
ping 192.168.123.161

# 2. SSH 连接测试
ssh unitree@192.168.123.161

# 3. 检查 G1 的状态
# 在 G1 的终端上
rosnode list
rostopic list
```

**G1 应该显示的信息：**

```
✅ 能 ping 通 G1
✅ 能 SSH 连接到 G1
✅ ROS 节点运行正常
✅ 能看到运动控制话题
✅ 机器人状态良好（电池充足、无报错）
```

### 1.3 网络拓扑验证

```
工作站                PICO 头显              G1 机器人
192.168.1.X    <-->  192.168.1.Y  <-->  192.168.123.161
(本地网络)      (WiFi)           (WiFi/以太网)
```

**验证网络连接：**

```bash
# 从工作站 ping PICO（获取IP后）
ping 192.168.1.Y

# 从工作站 ping G1
ping 192.168.123.161

# 检查延迟（应该 < 50ms）
ping -c 10 192.168.123.161
```

**期望延迟：**
- PICO ↔ 工作站：< 20ms
- G1 ↔ 工作站：< 10ms
- 总网络延迟：< 50ms

---

## 🚀 第二步：环境安装与配置

### 2.1 工作站环境准备

```bash
# 进入项目目录
cd GR00T-WholeBodyControl

# 第1步：安装 VR 遥操环境
bash install_scripts/install_pico.sh

# 这会自动：
# ✓ 创建 .venv_teleop 虚拟环境
# ✓ 安装 PICO SDK
# ✓ 安装 ZMQ 和其他依赖
# ✓ 验证安装

# 第2步：验证安装
source .venv_teleop/bin/activate
python -c "import pico; print('✅ PICO SDK installed')"

# 第3步：下载模型（如果还没有）
python download_from_hf.py --sonic-v1-1

# v1.1 版本对 VR 遥操优化最好
```

### 2.2 配置文件检查

检查以下配置文件是否存在：

```bash
# 检查 SONIC v1.1 配置
ls -la policy/sonic_v1_1/
# 应该包含：
# - model_encoder.onnx
# - model_decoder.onnx
# - observation_config.yaml

# 检查 PICO 配置
ls -la gear_sonic/config/pico/
# 应该包含各种输入源配置
```

### 2.3 调整配置参数

编辑 `gear_sonic/config/pico/teleop_config.yaml`：

```yaml
# PICO 遥操配置
pico:
  # PICO 设备信息
  device_name: "pico"
  ip_address: "192.168.1.Y"      # 改成你的 PICO IP
  port: 9999
  
  # 追踪参数
  tracking:
    frequency: 90                 # PICO 追踪频率（90Hz）
    enable_hand_tracking: true
    enable_body_tracking: true    # 需要 Pico Band
    
  # 映射参数
  mapping:
    scale_factor: 0.833          # 人身体到 G1 的尺度
    smooth_alpha: 0.7            # 平滑系数（0-1）
    enable_ik_smoothing: true
    
  # 网络参数
  network:
    zmq_host: "127.0.0.1"        # 本地主机（工作站）
    zmq_port: 5555               # ZMQ 通信端口
    robot_ip: "192.168.123.161"  # G1 的 IP
```

---

## 📋 第三步：分步验证

### 3.1 验证1：PICO 追踪正常工作

```bash
# 激活环境
source .venv_teleop/bin/activate

# 运行 PICO 追踪测试
python gear_sonic/scripts/test_pico_tracking.py \
    --pico-ip 192.168.1.Y \
    --verbose
```

**预期输出：**

```
✅ Connected to PICO
✅ Receiving tracking data
  - Head position: [x, y, z]
  - Left hand: [x, y, z]
  - Right hand: [x, y, z]
  - Waist: [x, y, z]
  - Tracking frequency: 90 Hz
  - Latency: 15ms
```

**如果失败，检查：**

```
❌ Connection refused
   → PICO IP 错误或 PICO 未开启追踪
   → 解决：重新获取 PICO IP，重启头显

❌ No tracking data
   → 追踪器未激活或信号丢失
   → 解决：在 PICO 设置中启用追踪，重启应用

❌ High latency (> 100ms)
   → 网络延迟过高或干扰
   → 解决：检查 WiFi 信号，减少距离
```

### 3.2 验证2：IK 求解（SMPL 恢复）正常工作

```bash
# 运行 IK 测试
python gear_sonic/scripts/test_ik_solver.py \
    --pico-ip 192.168.1.Y \
    --num-frames 100 \
    --save-smpl smpl_output.npy
```

**预期结果：**

```
✅ IK Solver initialized
✅ Processing 100 frames...
  Frame 1: body_pose (63,), global_orient (3,), transl (3,)
  Frame 2: ...
  ...
✅ Average processing time: 12ms
✅ SMPL parameters saved
```

**验证 SMPL 输出：**

```python
# 检查 SMPL 数据是否合理
import numpy as np

smpl = np.load('smpl_output.npy', allow_pickle=True).item()

print(f"Body pose shape: {smpl['body_pose'].shape}")  # (T, 63)
print(f"Global orient shape: {smpl['global_orient'].shape}")  # (T, 3)
print(f"Translation shape: {smpl['transl'].shape}")  # (T, 3)
print(f"Betas shape: {smpl['betas'].shape}")  # (10,)

# 检查数值范围
print(f"Body pose range: [{smpl['body_pose'].min():.2f}, {smpl['body_pose'].max():.2f}]")
# 应该在 [-1.5, 1.5] 弧度范围内

print(f"Translation range: [{smpl['transl'].min():.2f}, {smpl['transl'].max():.2f}]")
# 应该是合理的身体位置（米）
```

### 3.3 验证3：Retargeting（人体到G1映射）正常工作

```bash
# 运行 Retargeting 测试
python gear_sonic/scripts/test_retargeting.py \
    --pico-ip 192.168.1.Y \
    --num-frames 100 \
    --save-g1-targets g1_targets.npy \
    --verbose
```

**预期输出：**

```
✅ Retargeting initialized
✅ Processing 100 frames...
  Frame 1: G1 targets (29,) angles
  Frame 2: ...
✅ Average processing time: 5ms
✅ G1 joint targets saved

✅ Joint angles within limits:
  - All 29 joints: OK
  - No violations detected
```

**检查 G1 关节目标：**

```python
import numpy as np

g1_targets = np.load('g1_targets.npy')  # (T, 29)

print(f"Shape: {g1_targets.shape}")  # 应该是 (T, 29)
print(f"Min: {g1_targets.min():.2f}, Max: {g1_targets.max():.2f}")
# 应该在 [-3, 3] 弧度范围内

# 检查是否平滑
diff = np.diff(g1_targets, axis=0)
max_jump = np.max(np.abs(diff))
print(f"Max joint jump: {max_jump:.3f} rad")
# 应该 < 0.1 rad（很平滑）
```

### 3.4 验证4：G1 机器人连接

```bash
# 测试与 G1 的通信
python gear_sonic/scripts/test_g1_connection.py \
    --robot-ip 192.168.123.161
```

**预期输出：**

```
✅ Connected to G1
✅ G1 status:
  - State: IDLE
  - Battery: 85%
  - Temperature: Normal
  - Joints: 29 (all responsive)
✅ Can send commands
✅ Latency: 25ms
```

**如果失败，检查：**

```
❌ Connection refused
   → G1 IP 错误或机器人未通电
   → 解决：检查 IP，确保 G1 开启且在网络上

❌ Joints not responsive
   → G1 电机未启动或故障
   → 解决：SSH 到 G1，检查电机状态

❌ High latency (> 200ms)
   → 网络问题或 G1 处理缓慢
   → 解决：检查网络，确认 G1 无其他任务
```

### 3.5 验证5：完整系统集成测试

```bash
# 第1步：启动 C++ 控制器
cd gear_sonic_deploy
./deploy.sh --input-type zmq_manager real &

# 等待服务启动（30秒左右）
sleep 30

# 第2步：启动 PICO 遥操服务（在另一个终端）
cd /path/to/GR00T-WholeBodyControl
source .venv_teleop/bin/activate

python gear_sonic/scripts/pico_manager_thread_server.py \
    --input-source vive \
    --robot-ip 192.168.123.161 \
    --pico-ip 192.168.1.Y \
    --verbose

# 预期输出
# ✅ PICO connected
# ✅ G1 connected
# ✅ Streaming tracking data
# ✅ Publishing robot commands (50 Hz)
```

---

## 🎮 第四步：实际VR遥操测试

### 4.1 基础动作测试

**戴上 PICO 头显，逐一测试以下动作：**

```
1. 静止站立 (5 秒)
   ✅ G1 应该保持站立状态
   ✅ 不应该有抖动

2. 抬起双手 (3 次)
   ✅ G1 手臂跟随上升
   ✅ 延迟 < 500ms

3. 转头 (左/右各 90°)
   ✅ G1 头部跟随转动
   ✅ 不应该转过头

4. 走向前方 (2米)
   ✅ G1 向前行走
   ✅ 步伐自然、稳定

5. 左转圈
   ✅ G1 向左转身
   ✅ 平衡良好

6. 蹲下再站起
   ✅ G1 能蹲下
   ✅ 能顺利站起

7. 挥手
   ✅ G1 手臂摆动
   ✅ 运动自然
```

### 4.2 记录测试结果

创建测试日志：

```bash
# 运行完整测试脚本
python gear_sonic/scripts/test_vr_teleop_full.py \
    --pico-ip 192.168.1.Y \
    --robot-ip 192.168.123.161 \
    --duration 300 \
    --output test_log.json
```

**测试日志会包含：**

```json
{
  "timestamp": "2026-08-14 10:30:00",
  "hardware": {
    "pico_ip": "192.168.1.Y",
    "robot_ip": "192.168.123.161",
    "network_latency_ms": 25
  },
  "tracking": {
    "pico_frequency": 90,
    "tracking_points": 9,
    "dropout_rate": 0.0,
    "average_latency_ms": 15
  },
  "ik_solver": {
    "processing_time_ms": 12,
    "smpl_valid_frames": 300,
    "smpl_invalid_frames": 0
  },
  "retargeting": {
    "processing_time_ms": 5,
    "joint_limit_violations": 0,
    "smoothness_score": 0.95
  },
  "robot_control": {
    "command_frequency": 50,
    "delivery_success_rate": 100,
    "average_response_latency_ms": 80
  },
  "overall": {
    "end_to_end_latency_ms": 120,
    "user_perception": "smooth",
    "status": "PASS"
  }
}
```

---

## 📊 第五步：性能评估

### 5.1 延迟测试

```bash
# 运行延迟测试工具
python gear_sonic/scripts/measure_teleop_latency.py \
    --pico-ip 192.168.1.Y \
    --robot-ip 192.168.123.161 \
    --num-samples 100
```

**期望的延迟分解：**

```
PICO 追踪     : 5-10 ms
IK 求解       : 10-15 ms
平滑处理      : 5-10 ms
Retargeting   : 2-5 ms
SONIC 处理    : 15-25 ms
网络传输      : 20-50 ms
G1 响应       : 20-30 ms
____________________
总计          : 80-150 ms (目标)
```

**评价标准：**

```
< 100ms   : 优秀 ⭐⭐⭐
100-200ms : 良好 ⭐⭐
200-300ms : 可接受 ⭐
> 300ms   : 不可接受 ❌
```

### 5.2 稳定性测试

```bash
# 运行 10 分钟稳定性测试
python gear_sonic/scripts/test_stability.py \
    --pico-ip 192.168.1.Y \
    --robot-ip 192.168.123.161 \
    --duration 600 \
    --output stability_report.txt
```

**关键指标：**

```
✅ 连接掉线次数: 0
✅ 追踪丢失比例: < 1%
✅ 关节限制违反: 0
✅ 平均延迟: 85ms
✅ 延迟波动: ± 10ms
✅ G1 稳定性: 无抖动/不稳定
```

---

## 🐛 第六步：常见问题排查

### 问题1：PICO 无法连接

```
症状：ConnectionRefused 或 Connection timeout
检查清单：
☐ PICO 的 IP 地址是否正确？
☐ PICO 是否连接到 WiFi？
☐ 工作站和 PICO 是否在同一网络？
☐ 防火墙是否阻止连接？
☐ PICO 是否已启用开发者模式？

解决方案：
1. adb devices 查看 PICO
2. adb shell "getprop ro.wifi.ip.address" 确认IP
3. ping <PICO_IP> 从工作站测试
4. 重启 PICO 和工作站
5. 重新运行 install_pico.sh
```

### 问题2：G1 追踪延迟高或不稳定

```
症状：G1 抖动、延迟波动大
检查清单：
☐ WiFi 信号强度如何？
☐ 有其他设备占用网络吗？
☐ G1 CPU 负载是否过高？
☐ 是否有其他任务运行？

解决方案：
1. 在 G1 上运行：top
   → 确认 CPU 使用率 < 50%
2. 增加 smooth_alpha：0.7 → 0.9
   → 牺牲响应速度获得稳定性
3. 检查 WiFi：iwconfig
   → 信号强度应该 > -70 dBm
4. 靠近 WiFi 路由器
5. 检查是否有 5GHz WiFi（更稳定）
```

### 问题3：G1 不跟随人的动作

```
症状：G1 不动或动作不对
检查清单：
☐ C++ 控制器是否启动？(./deploy.sh real)
☐ ZMQ 通信是否正常？
☐ G1 电机是否启动？
☐ SONIC 模型文件是否存在？
☐ 命令是否正确发送？

解决方案：
1. 检查控制器日志：
   tail -f logs/deploy.log
   
2. 验证命令接收：
   python -c "import zmq; ..."
   
3. 检查 G1 状态：
   ssh unitree@192.168.123.161
   rostopic echo /g1_robot_state
   
4. 查看 SONIC 是否加载：
   查看 deploy.sh 输出的 "Model loaded" 消息
   
5. 手动发送测试命令：
   python test_send_command.py
```

### 问题4：SMPL 数据看起来不对

```
症状：人体骨架恢复不准确或扭曲
检查清单：
☐ PICO 追踪数据是否有效？
☐ Pico Band 是否贴身佩戴？
☐ 是否有足够的光线？（某些追踪器需要）
☐ IK 模型是否正确加载？

解决方案：
1. 可视化 SMPL 数据：
   python visualize_smpl.py --input smpl_output.npy
   
2. 检查追踪点是否合理：
   python visualize_tracking.py --pico-ip <IP>
   
3. 调整 IK 求解参数：
   在配置文件中调整 ik_max_iterations, ik_tolerance
   
4. 重新标定 PICO：
   在 PICO 设置中重新校准追踪
   
5. 检查 Pico Band：
   - 是否与头显配对？
   - 电池是否充足？
   - 是否正确贴身？
```

### 问题5：网络延迟太高

```
症状：延迟 > 200ms
检查清单：
☐ 网络速度？
☐ 是否有其他应用占用带宽？
☐ 是否在 2.4GHz 频段有干扰？
☐ 路由器距离多远？

解决方案：
1. 检查网络延迟：
   ping -c 20 192.168.123.161 192.168.1.Y
   
2. 切换到 5GHz WiFi：
   更稳定、延迟低
   
3. 靠近路由器
   
4. 关闭其他应用（下载、流媒体等）
   
5. 使用有线网络连接 G1（如可能）
   
6. 检查路由器拥塞：
   在路由器管理界面看连接数
```

---

## ✨ 第七步：优化调整

### 7.1 平滑度优化

```yaml
# 如果 G1 动作抖动，增加平滑度
smooth_alpha: 0.9  # 0.7 → 0.9 (更平滑)

# 如果响应慢，降低平滑度
smooth_alpha: 0.5  # 0.7 → 0.5 (更灵敏)

# 平衡点（推荐）
smooth_alpha: 0.7
```

### 7.2 Retargeting 参数调整

```yaml
# 如果 G1 动作太剧烈，减小尺度
scale_factor: 0.7  # 0.833 → 0.7

# 如果 G1 动作太温和，增大尺度
scale_factor: 0.95  # 0.833 → 0.95

# 关节映射权重（如果某些关节不准）
joint_weights:
  hip: 1.0
  knee: 0.9
  ankle: 0.8
```

### 7.3 模型选择优化

```bash
# 当前使用的是 SONIC v1.1（推荐）
./deploy.sh \
    --cp policy/sonic_v1_1/model \
    --obs-config policy/sonic_v1_1/observation_config.yaml \
    real

# 如果需要更低延迟，尝试低延迟版本
./deploy.sh \
    --cp policy/low_latency/model \
    --obs-config policy/low_latency/observation_config.yaml \
    real

# 对比性能差异：
# v1.1: 延迟 120ms, 质量 优秀
# 低延迟: 延迟 80ms, 质量 良好
```

---

## 📝 验证完成检查列表

```
硬件验证
☐ PICO 能通电、能追踪
☐ G1 能通电、能移动
☐ 网络能连通 (ping < 50ms)

环境验证
☐ Python 环境安装成功
☐ 模型文件下载完整
☐ 配置文件正确

功能验证
☐ PICO 追踪正常 (90Hz, < 50ms 延迟)
☐ IK 求解正常 (SMPL 数据有效)
☐ Retargeting 正常 (G1 关节目标合理)
☐ 与 G1 通信正常 (命令能发送)

动作测试
☐ 站立保持稳定
☐ 抬手 G1 跟随
☐ 转头 G1 响应
☐ 行走 G1 走动
☐ 蹲下 G1 蹲下
☐ 挥手 G1 摆动

性能评估
☐ 端到端延迟 < 150ms
☐ 延迟波动 < 50ms
☐ 追踪丢失率 < 1%
☐ 连接稳定性 100%

最终确认
☐ VR 遥操系统完全可用
☐ 可以开始收集数据或其他任务
```

---

## 🎉 验证成功！

当所有检查都通过后，恭喜你！你现在可以：

✅ **使用 VR 遥操控制 G1**
- 实时跟随你的动作
- 完成各种复杂任务
- 演示人体运动

✅ **收集演示数据**
- 进行 VLA 模型微调
- 教机器人新任务

✅ **进行其他研究**
- 运动学研究
- 遥操人机交互
- 机器人学习

---

## 🚨 紧急故障处理

**如果 G1 行为异常（无法停止、持续转动等）：**

```bash
# 立即 SSH 到 G1 停止所有服务
ssh unitree@192.168.123.161

# 停止 ROS 节点
killall rosnode

# 或直接断电
# (按下机器人身上的紧急停止按钮)
```

---

**下一步：** 验证完成后，参考 [vr_teleop_technical.md](vr_teleop_technical.md) 理解技术细节，或开始 [收集演示数据](../zh_CN/g1_quick_start.md#方案3教g1学习新任务3-5天需要vrgpu)。

更新时间：2026-08-14
