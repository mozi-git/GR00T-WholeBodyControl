# VR遥操技术详解：从人体追踪到机器人控制

本文档详细解释：**人穿着VR设备（PICO+手环+脚环）移动，机器人如何实时跟随的完整技术过程。**

---

## 🎯 核心问题：机器人怎么知道你的动作？

### 完整数据流

```
人体动作捕捉
    ↓
PICO头显 + 手环/脚环
    └─ 9个追踪点
    ↓
提取人体骨架 (SMPL 参数)
    ├─ 21个关节的3D位置
    ├─ 每个关节的旋转
    └─ 身体形状
    ↓
动作转换与平滑
    ├─ 噪声过滤
    ├─ 速度平滑
    └─ 重力补偿
    ↓
映射到机器人关节 (Retargeting)
    ├─ 尺度调整 (人 170cm → G1 150cm)
    ├─ 关节映射 (人21关节 → G1 29 DOF)
    └─ 物理约束
    ↓
SONIC 解码器
    ├─ 输入：SMPL参数
    ├─ 处理：编码→解码
    └─ 输出：64维动作令牌
    ↓
G1 机器人执行
    ├─ 接收关节目标位置
    ├─ 执行动作
    └─ 闭环控制 (50Hz)
```

---

## 1️⃣ 第一步：VR设备追踪（9个追踪点）

### PICO 头显和配件的追踪

```
PICO VR 系统
├─ 头显 (1个)
│  ├─ 头部位置 (X, Y, Z)
│  ├─ 头部朝向 (四元数)
│  └─ 眼睛方向 (可选)
│
├─ 左手控制器 (1个)
│  ├─ 手腕位置
│  ├─ 手腕朝向
│  └─ 按键状态
│
└─ 右手控制器 (1个)
   ├─ 手腕位置
   ├─ 手腕朝向
   └─ 按键状态

可选配件：
├─ 腰部追踪器 (Pico Band)
│  ├─ 腰部位置
│  └─ 腰部朝向
│
├─ 脚环追踪器 (如有)
│  ├─ 左脚位置
│  ├─ 右脚位置
│  └─ 脚朝向
│
└─ 膝盖追踪 (如有)
   ├─ 左膝位置
   └─ 右膝位置

总计：9个追踪点 (头 + 两手 + 腰 + 两脚 + 可选膝盖)
```

### 追踪数据格式

```python
# PICO 追踪数据结构
pico_tracking_data = {
    # 位置追踪
    'head_pos': np.array([x, y, z]),        # 头部3D位置
    'left_wrist_pos': np.array([x, y, z]),  # 左腕3D位置
    'right_wrist_pos': np.array([x, y, z]), # 右腕3D位置
    'waist_pos': np.array([x, y, z]),       # 腰部3D位置
    'left_foot_pos': np.array([x, y, z]),   # 左脚3D位置
    'right_foot_pos': np.array([x, y, z]),  # 右脚3D位置
    
    # 朝向追踪（四元数）
    'head_rot': np.array([qx, qy, qz, qw]),        # 头部旋转
    'left_wrist_rot': np.array([qx, qy, qz, qw]),  # 左腕旋转
    'right_wrist_rot': np.array([qx, qy, qz, qw]), # 右腕旋转
    'waist_rot': np.array([qx, qy, qz, qw]),       # 腰部旋转
    'left_foot_rot': np.array([qx, qy, qz, qw]),   # 左脚旋转
    'right_foot_rot': np.array([qx, qy, qz, qw]),  # 右脚旋转
    
    # 按键状态
    'buttons': {
        'left_grip': bool,
        'right_grip': bool,
        'left_trigger': float,  # 0-1
        'right_trigger': float,
    },
    
    # 时间戳
    'timestamp': float,  # 毫秒
}

# 更新频率：90 Hz (PICO 标准)
# 即每 11ms 更新一次追踪数据
```

### 追踪精度

| 追踪点 | 精度 | 延迟 | 可靠性 |
|------|------|------|-------|
| 头部 | ±2cm | 5-10ms | 99% |
| 手腕 | ±5cm | 10-15ms | 95% |
| 腰部 | ±5cm | 10-15ms | 90% |
| 脚部 | ±10cm | 20-30ms | 80% |

---

## 2️⃣ 第二步：提取人体骨架（SMPL参数化）

### 从 9 个追踪点恢复完整人体

这是一个**逆向运动学（IK）问题**：

```
已知：9个追踪点的位置和朝向
未知：21个SMPL关节的位置和旋转

求解方法：
1. 使用预训练的IK模型
2. 或使用启发式算法 + 物理约束
3. 或混合方法（两者结合）
```

### 算法流程

```python
# 伪代码：从PICO追踪到SMPL
def pico_to_smpl(pico_data):
    """
    从PICO追踪数据生成SMPL参数
    """
    
    # 第1步：建立追踪点与关节的对应关系
    tracking_to_joints = {
        'head': smpl_joints[15, 16],              # 头部两个关节
        'left_wrist': smpl_joints[9],            # 左腕
        'right_wrist': smpl_joints[10],          # 右腕
        'waist': smpl_joints[0],                 # 根节点（骨盆）
        'left_foot': smpl_joints[10, 11],        # 左脚
        'right_foot': smpl_joints[22, 23],       # 右脚
    }
    
    # 第2步：IK求解（关键步骤）
    # 使用神经网络或优化算法
    ik_solver = IKSolver(model='vibe')  # 预训练IK模型
    
    smpl_joints_3d = ik_solver.solve(
        tracking_points=pico_data,
        constraints=['no_penetration', 'joint_limits'],
    )
    # 输出：21个关节的3D位置
    
    # 第3步：提取SMPL参数
    smpl_params = extract_smpl_params(smpl_joints_3d)
    
    return {
        'body_pose': smpl_params['body_pose'],        # (63,) 轴角
        'global_orient': smpl_params['global_orient'],# (3,) 轴角
        'transl': smpl_params['transl'],              # (3,) 位置
        'betas': smpl_params['betas'],                # (10,) 形状
    }
```

### 关键技术：VIBE (Video Inference for Human Body Pose Estimation)

```
VIBE 是一个深度学习模型，用于从视频或追踪点恢复SMPL参数

输入：
├─ 追踪点序列 (时间序列)
├─ 前几帧的SMPL参数 (上文信息)
└─ 身体约束 (关节范围等)

处理：
├─ LSTM 处理时间序列
├─ 解决关节歧义
├─ 平滑运动
└─ 应用物理约束

输出：
├─ body_pose (63,)
├─ global_orient (3,)
├─ transl (3,)
└─ betas (10,)

特点：
✅ 从少量追踪点恢复完整身体
✅ 处理关节歧义
✅ 自然的运动平滑
❌ 需要预训练
❌ 计算量中等
```

### 代码实现

```python
# 使用 VIBE 从 PICO 追踪恢复人体
from vibe.model import VIBE
from vibe.utils import process_image

# 加载预训练 VIBE 模型
vibe_model = VIBE.load_pretrained('vibe_model.pt')

# 处理 PICO 追踪序列
tracking_sequence = [pico_data[t] for t in range(num_frames)]

# 运行推理（批量处理时间序列）
with torch.no_grad():
    smpl_params_sequence = vibe_model(tracking_sequence)
    # 输出：T 帧的 SMPL 参数
    # shape: body_pose (T, 63)
    #        global_orient (T, 3)
    #        transl (T, 3)
    #        betas (10,)
```

---

## 3️⃣ 第三步：动作平滑和优化

### 为什么需要平滑？

VR 追踪数据有噪声：

```
原始 PICO 数据（噪声）
    ↓
抖动、跳跃、突变
    ↓
如果直接送给机器人 → 机器人抖动、不稳定
    ↓
需要平滑处理
    ↓
光滑、自然的运动
```

### 平滑算法

```python
# 方法1：低通滤波器（简单）
from scipy import signal

def smooth_pico_data(raw_data, cutoff_freq=5.0, sample_freq=90.0):
    """
    使用低通滤波器平滑追踪数据
    """
    # 设计 Butterworth 低通滤波器
    sos = signal.butter(4, cutoff_freq, fs=sample_freq, output='sos')
    
    # 应用滤波器到每个追踪点
    smoothed_positions = {}
    for point_name, positions in raw_data.items():
        # positions: (T, 3) 时间序列
        smoothed = signal.sosfilt(sos, positions, axis=0)
        smoothed_positions[point_name] = smoothed
    
    return smoothed_positions

# 方法2：卡尔曼滤波器（更好）
from filterpy.kalman import KalmanFilter

def kalman_smooth(raw_data, process_noise=0.01, measure_noise=0.1):
    """
    使用卡尔曼滤波器追踪动作
    """
    kf = KalmanFilter(dim_x=6, dim_z=3)  # 6维状态：位置+速度，3维观测：位置
    
    smoothed_trajectory = []
    
    for t, observation in enumerate(raw_data):
        # 预测步
        kf.predict()
        
        # 更新步
        kf.update(observation)
        
        # 取出平滑后的位置
        smoothed_trajectory.append(kf.x[:3])  # 前3维是位置
    
    return np.array(smoothed_trajectory)

# 方法3：LSTM平滑（最好）
class LSTMSmoother(nn.Module):
    def __init__(self, input_dim=3, hidden_dim=64):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, input_dim)
    
    def forward(self, x):
        # x: (T, input_dim) 追踪序列
        lstm_out, _ = self.lstm(x.unsqueeze(0))  # (1, T, hidden_dim)
        smoothed = self.fc(lstm_out)  # (1, T, input_dim)
        return smoothed.squeeze(0)
```

### 平滑参数调整

```yaml
# 平滑配置
smoothing:
  method: kalman  # or butterworth, lstm
  
  # 低通滤波参数
  butterworth:
    cutoff_frequency: 5.0 Hz  # 截止频率（越低越平滑）
    order: 4
  
  # 卡尔曼滤波参数
  kalman:
    process_noise: 0.01       # 过程噪声（越小越信任预测）
    measurement_noise: 0.1    # 测量噪声（越小越信任观测）
  
  # LSTM 平滑参数
  lstm:
    hidden_size: 64
    num_layers: 2
    dropout: 0.2
```

---

## 4️⃣ 第四步：映射到机器人（Retargeting）

### 核心问题：人和机器人的差异

```
人体特征 → G1 机器人特征

人体：
├─ 身高：160-190cm
├─ 关节：21个
├─ DOF：多达 100+
├─ 物理特性：软、灵活
└─ 约束：有限

G1 机器人：
├─ 身高：~150cm
├─ 关节：29个 DOF
├─ DOF：29
├─ 物理特性：刚性、电机驱动
└─ 约束：严格的关节范围
```

### Retargeting 算法

```python
def human_to_g1_retargeting(smpl_params):
    """
    将人体SMPL参数映射到G1机器人关节
    """
    
    # 第1步：尺度调整
    # 人身高 180cm → G1 身高 150cm
    scale_factor = 150 / 180  # ~0.833
    
    smpl_params['transl'] *= scale_factor  # 缩放位置
    # 关节朝向不需要缩放（都是旋转）
    
    # 第2步：关节映射（IK → FK）
    # 从 SMPL 21个关节 → G1 29个DOF
    
    # 获取 SMPL 关节位置（从body_pose恢复）
    smpl_joints_3d = forward_kinematics_smpl(
        body_pose=smpl_params['body_pose'],
        global_orient=smpl_params['global_orient'],
        transl=smpl_params['transl'],
        betas=smpl_params['betas'],
    )
    # 输出：(21, 3) SMPL 21个关节的3D位置
    
    # 映射策略
    mapping = {
        # 下身（腿）
        'left_hip': smpl_joints_3d[1],
        'left_knee': smpl_joints_3d[4],
        'left_ankle': smpl_joints_3d[7],
        'right_hip': smpl_joints_3d[2],
        'right_knee': smpl_joints_3d[5],
        'right_ankle': smpl_joints_3d[8],
        
        # 躯干
        'spine': smpl_joints_3d[0],
        
        # 头
        'neck': smpl_joints_3d[15],
        'head': smpl_joints_3d[16],
        
        # 上身
        'left_shoulder': smpl_joints_3d[16],
        'left_elbow': smpl_joints_3d[18],
        'left_wrist': smpl_joints_3d[20],
        'right_shoulder': smpl_joints_3d[17],
        'right_elbow': smpl_joints_3d[19],
        'right_wrist': smpl_joints_3d[21],
    }
    
    # 第3步：解IK得到关节角度
    g1_joint_targets = solve_ik_g1(mapping)
    # 输出：G1 29个关节的目标角度
    
    # 第4步：应用约束
    g1_joint_targets = apply_joint_limits(g1_joint_targets, g1_limits)
    
    # 第5步：平滑（避免跳变）
    g1_joint_targets = smooth_joint_trajectory(g1_joint_targets)
    
    return g1_joint_targets  # (29,) 或 (T, 29)
```

### 约束应用

```python
# G1 关节范围约束
g1_joint_limits = {
    'left_hip_roll': [-1.5, 1.5],      # 弧度
    'left_hip_pitch': [-2.0, 2.0],
    'left_hip_yaw': [-0.5, 0.5],
    # ... 等等 29 个关节
}

def apply_joint_limits(angles, limits):
    """
    将关节角度限制在有效范围内
    """
    clipped_angles = angles.copy()
    for i, (min_angle, max_angle) in enumerate(limits.values()):
        clipped_angles[i] = np.clip(angles[i], min_angle, max_angle)
    return clipped_angles

# 平滑关节轨迹（避免震颤）
def smooth_joint_trajectory(trajectory, alpha=0.7):
    """
    使用指数平均平滑关节轨迹
    """
    smoothed = np.zeros_like(trajectory)
    smoothed[0] = trajectory[0]
    
    for t in range(1, len(trajectory)):
        smoothed[t] = alpha * trajectory[t] + (1 - alpha) * smoothed[t-1]
    
    return smoothed
```

---

## 5️⃣ 第五步：SONIC 解码执行

### Retargeting 后的处理

已有：G1 的目标关节位置

下一步：送入 SONIC 解码器

```python
# 将关节目标转换为 SMPL 参数（反向过程）
g1_joint_targets  # (29,) G1 关节
    ↓
执行正向运动学 (FK)
    ↓
得到 G1 关节的3D位置
    ↓
拟合为 SMPL 参数
    ↓
输入 SONIC 编码器
    ↓
得到 64 维潜在向量
    ↓
SONIC 解码器
    ↓
输出平滑的机器人控制信号
```

### 代码流程

```python
# 完整的 VR 遥操到 G1 控制流
def vr_teleop_to_robot_control(pico_data_sequence):
    """
    完整的 VR 遥操工作流
    """
    
    # 1. PICO 追踪 → SMPL
    smpl_sequence = vibe_model(pico_data_sequence)  # (T, 63+3+3+10)
    
    # 2. 人体 → G1 Retargeting
    g1_targets = []
    for t in range(len(smpl_sequence)):
        g1_target = retarget_human_to_g1(smpl_sequence[t])
        g1_targets.append(g1_target)
    g1_targets = np.array(g1_targets)  # (T, 29)
    
    # 3. G1 目标 → SONIC 输入
    # 将 G1 关节转换回 SMPL 表示（SONIC 期望的输入）
    g1_as_smpl = g1_forward_kinematics_to_smpl(g1_targets)
    
    # 4. SONIC 编码-解码
    with torch.no_grad():
        # 编码为潜在向量
        latent_codes = sonic_encoder(g1_as_smpl)  # (T, 64)
        
        # 解码为平滑的机器人命令
        robot_commands = sonic_decoder(latent_codes)  # (T, 29)
    
    return robot_commands
```

---

## 6️⃣ 完整系统架构

```
┌─────────────────────────────────────────────────────┐
│                   VR 遥操系统                       │
└─────────────────────────────────────────────────────┘

┌──────────────────┐
│   PICO VR 设备    │
├──────────────────┤
│ 头显 + 手环 + 脚环 │
│ 9个追踪点         │
│ 90 Hz 更新        │
└────────┬─────────┘
         │ 追踪数据
         ↓
┌─────────────────────────────┐
│   IK 求解 (VIBE)            │
├─────────────────────────────┤
│ 9个追踪点 → 21个关节3D位置  │
│ 恢复 SMPL 参数               │
│ 处理噪声和歧义               │
└────────┬────────────────────┘
         │ SMPL 参数序列
         ↓
┌─────────────────────────────┐
│   平滑处理                   │
├─────────────────────────────┤
│ 卡尔曼滤波 / LSTM             │
│ 去除噪声                     │
│ 生成自然运动                 │
└────────┬────────────────────┘
         │ 平滑 SMPL 参数
         ↓
┌─────────────────────────────┐
│   Retargeting (IK)          │
├─────────────────────────────┤
│ 尺度调整 (180cm → 150cm)    │
│ 关节映射 (21 → 29 DOF)      │
│ 应用约束                     │
└────────┬────────────────────┘
         │ G1 关节目标
         ↓
┌─────────────────────────────┐
│   SONIC 编码-解码           │
├─────────────────────────────┤
│ 编码：G1 关节 → 64维潜在    │
│ 解码：平滑的控制信号         │
└────────┬────────────────────┘
         │ 机器人命令
         ↓
┌──────────────────────────────┐
│   G1 机器人执行              │
├──────────────────────────────┤
│ 50 Hz 控制频率               │
│ 实时动作执行                 │
└──────────────────────────────┘
```

---

## 📊 实时性能指标

### 端到端延迟分解

| 阶段 | 延迟 | 说明 |
|------|------|------|
| PICO 追踪 | 5-10ms | 头显处理 |
| IK 求解 (VIBE) | 10-15ms | 推理 |
| 平滑处理 | 5-10ms | 滤波 |
| Retargeting | 2-5ms | IK 计算 |
| SONIC 编码 | 10-15ms | 神经网络推理 |
| SONIC 解码 | 5-10ms | 神经网络推理 |
| 网络传输 | 20-50ms | ZMQ |
| **总计** | **60-120ms** | 单向延迟 |

### 往返延迟（用户感受）

- 用户做动作 → 机器人反应：**120-240ms**
- 人类可接受的延迟阈值：< 300ms
- 这个系统的性能：✅ 良好

---

## 🔧 实现细节代码

### 完整工作流的 Python 实现

```python
class VRTeleop:
    def __init__(self):
        self.vibe_model = load_vibe_model()
        self.sonic_encoder = load_sonic_encoder()
        self.sonic_decoder = load_sonic_decoder()
        self.g1_ik_solver = IKSolverG1()
        
    def process_frame(self, pico_frame):
        """处理单帧 PICO 数据到机器人控制"""
        
        # 1. VIBE: PICO 9点 → SMPL 参数
        smpl = self.vibe_model(pico_frame)
        # smpl: body_pose(63), global_orient(3), transl(3), betas(10)
        
        # 2. 平滑
        smpl = self.smooth_smpl(smpl)
        
        # 3. Retarget: SMPL → G1
        g1_target_joints = self.retarget_human_to_g1(smpl)
        
        # 4. SONIC 编码-解码
        g1_as_smpl = self.g1_fk_to_smpl(g1_target_joints)
        latent = self.sonic_encoder(g1_as_smpl)
        robot_cmd = self.sonic_decoder(latent)
        
        return robot_cmd  # (29,) 关节命令
    
    def retarget_human_to_g1(self, smpl):
        """人体 SMPL → G1 关节"""
        
        # 尺度调整
        scale = 150 / 180
        smpl['transl'] *= scale
        
        # 获取 SMPL 关节3D位置
        smpl_joints = self.smpl_forward_kinematics(smpl)
        
        # IK 求解 G1 关节
        g1_joints = self.g1_ik_solver.solve(
            target_positions=smpl_joints,
            current_joints=self.last_g1_joints,  # 用前一帧作为初值
        )
        
        # 应用约束
        g1_joints = self.apply_joint_limits(g1_joints)
        
        return g1_joints
    
    def smooth_smpl(self, smpl, alpha=0.7):
        """平滑 SMPL 数据"""
        self.prev_smpl = (
            alpha * smpl + 
            (1 - alpha) * self.prev_smpl
        )
        return self.prev_smpl

# 使用
teleop = VRTeleop()

# 实时循环
while True:
    pico_data = pico_interface.get_latest_frame()  # 来自 PICO
    robot_command = teleop.process_frame(pico_data)
    robot.execute_command(robot_command)  # 发送到 G1
    
    time.sleep(0.02)  # 50 Hz (20ms 一帧)
```

---

## 📚 项目中的实现

### GR00T 中的 VR 遥操代码位置

```
gear_sonic/
├─ pico_manager_thread_server.py       # PICO 数据接收
├─ utils/                               
│  ├─ human2g1_retargeting.py          # Retargeting 实现
│  ├─ smpl_processor.py                # SMPL 处理
│  └─ motion_smoother.py               # 平滑
├─ vibe/                               # VIBE 模型（可选）
│  └─ vibe_infer.py
└─ scripts/
   └─ pico_manager_thread_server.py    # 主遥操脚本
```

### 启动 VR 遥操的命令

```bash
# 启动 PICO 遥操服务
python gear_sonic/scripts/pico_manager_thread_server.py \
    --input-source vive

# 也支持其他输入源
# --input-source isaac-teleop   # Isaac Teleop
# --input-source keyboard       # 键盘调试
# --input-source file           # 回放录制数据
```

---

## 🎯 总结：完整的数据流

```
人穿 VR 做动作
    ↓
PICO 追踪 (90Hz)
    └─ 9个追踪点 + 位置 + 朝向
    ↓
VIBE IK 求解
    └─ 恢复 21 个关节的 SMPL 参数
    ↓
平滑处理（卡尔曼/LSTM）
    └─ 去噪、平滑、自然运动
    ↓
Retargeting (尺度+关节映射+IK)
    └─ 人身体 → G1 关节目标 (29 DOF)
    ↓
SONIC 编码-解码
    └─ G1 关节 → 64维潜在 → 平滑控制信号
    ↓
G1 机器人执行 (50Hz)
    └─ 关节电机驱动，跟随人体动作

⏱️ 总延迟：60-120ms（单向）
🎯 用户感受：几乎实时
```

---

**总结：** 这是一个从 VR 追踪、人体骨架恢复、动作平滑、尺度映射、到机器人关节控制的完整系统。GR00T 项目提供了所有这些模块，可以开箱即用！

更新时间：2026-08-14
