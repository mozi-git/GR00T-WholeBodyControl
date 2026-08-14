# SMPL 详解：理解参数化人体模型

SMPL 是 GR00T 项目中最重要的概念之一。本文档从零开始讲解 SMPL 是什么、为什么用它、以及如何使用。

---

## 1. SMPL 是什么？

### 1.1 简单定义

**SMPL = Skinned Multi-Person Linear (Model)**

中文翻译：**蒙皮多人线性模型**

**核心概念：** SMPL 是一个参数化的人体3D模型，用**少量参数就能精确表示任何人的身体姿态和形状**。

### 1.2 类比理解

想象你有一个"虚拟人偶"：

```
┌─────────────────────────────────────┐
│      SMPL 人体模型                  │
│                                     │
│   参数输入                          │
│   ├─ 身体形状参数 (10个)           │
│   ├─ 身体姿态参数 (63个)           │
│   ├─ 全局朝向 (3个)                │
│   └─ 位置 (3个)                    │
│                                     │
│         ↓ 计算                      │
│                                     │
│   输出：人体的每个关节位置          │
│   ├─ 21个关节的3D坐标              │
│   ├─ 每个关节的旋转                │
│   └─ 整个身体的网格                │
└─────────────────────────────────────┘
```

**实际应用：** 从 Motion Capture（动捕）数据中提取 SMPL 参数，用少量数字就能完整表示一个人的动作。

---

## 2. SMPL 的三个核心参数

### 2.1 身体形状参数 (shape parameters)

**变量名：** `betas`

**维度：** (10,)

**作用：** 描述一个人的身体形状

```python
# 例子
betas = np.array([
    0.5,    # 0: 整体肥胖度
    -0.3,   # 1: 肌肉发达度
    0.2,    # 2: 身体宽度
    -0.1,   # 3: 胸部
    0.15,   # 4: 腰部
    -0.05,  # 5: 臀部
    0.1,    # 6: 腿长
    -0.2,   # 7: 腿粗
    0.05,   # 8: 手臂
    -0.08,  # 9: 其他
])
```

**含义：**
- 负值 → 该特征较小
- 0 → 平均身体
- 正值 → 该特征较大

**特点：**
- 10个参数就能表示无限多种不同身体
- 这10个参数是从大量人体扫描数据统计得出
- 每个参数都有明确的物理含义

### 2.2 身体姿态参数 (pose parameters)

**变量名：** `body_pose` + `global_orient`

**维度：** 
- `body_pose`: (63,)  ← 21个关节 × 3 (轴角表示)
- `global_orient`: (3,)  ← 全局朝向

**作用：** 描述身体的姿态（每个关节的旋转）

```python
# SMPL 的 21 个关节
joints = [
    0: pelvis (根节点),
    1-2: left leg,
    3-4: right leg,
    5-6: spine/torso,
    7-8: left arm,
    9-10: right arm,
    11-12: left hand,
    13-14: right hand,
    15-16: head,
    17-20: fingers,
]

# 每个关节用轴角 (3维向量) 表示旋转
body_pose = np.array([
    # 左大腿
    0.1, 0.05, 0.02,    # 旋转轴 × 旋转角度
    
    # 左小腿
    -0.15, 0.02, 0.01,
    
    # ... 共21个关节 × 3 = 63维
])

# 全局朝向（根节点旋转）
global_orient = np.array([0.05, 0.1, 0.02])  # (3,)
```

**轴角表示 (Axis-Angle)：**

一个3维向量 `[rx, ry, rz]` 表示旋转：
- **方向** → 旋转轴（单位向量方向）
- **大小** → 旋转角度（弧度）

```python
# 例子：绕Z轴旋转 90 度
angle = np.pi / 2
axis = np.array([0, 0, 1])  # Z轴
axis_angle = axis * angle  # [0, 0, 1.57]
```

### 2.3 位置参数 (translation)

**变量名：** `transl`

**维度：** (3,)

**作用：** 人体在世界坐标系中的位置

```python
# 位置 (X, Y, Z)
transl = np.array([
    1.5,   # X: 前后
    0.0,   # Y: 左右
    0.9,   # Z: 上下
])
```

---

## 3. SMPL 的参数总结表

| 参数 | 变量名 | 形状 | 说明 |
|------|--------|------|------|
| **形状** | betas | (10,) | 身体形状（共享，不随时间变化） |
| **姿态** | body_pose | (T, 63) | 21个关节的旋转（每帧） |
| **全局朝向** | global_orient | (T, 3) | 根节点旋转（每帧） |
| **位置** | transl | (T, 3) | 身体位置（每帧） |
| **面部表情** | expression | (T, 10) | 可选，面部表情（每帧） |

**其中 T 是时间步（帧数）**

---

## 4. SMPL 数据的完整例子

### 4.1 一个简单的动作数据

```python
import numpy as np

# 一个 2 秒的行走动作（30fps）
T = 60  # 60帧

smpl_data = {
    # 身体形状（所有帧相同）
    'betas': np.random.randn(10).astype(np.float32) * 0.1,
    
    # 姿态参数（每帧不同）
    'body_pose': np.random.randn(T, 63).astype(np.float32) * 0.2,
    'global_orient': np.random.randn(T, 3).astype(np.float32) * 0.1,
    
    # 位置
    'transl': np.zeros((T, 3), dtype=np.float32),
    
    # 设置行走轨迹（X 方向）
    for t in range(T):
        smpl_data['transl'][t, 0] = t * 0.05  # 每帧向前 0.05m
    
    # 可选：面部表情
    'expression': np.zeros((T, 10), dtype=np.float32),
}

print(f"数据形状：")
print(f"  betas: {smpl_data['betas'].shape}")          # (10,)
print(f"  body_pose: {smpl_data['body_pose'].shape}")  # (60, 63)
print(f"  global_orient: {smpl_data['global_orient'].shape}")  # (60, 3)
print(f"  transl: {smpl_data['transl'].shape}")        # (60, 3)
```

### 4.2 可视化

```
时间轴：
t=0     t=10    t=20    t=30    t=40    t=50    t=60
|       |       |       |       |       |       |
👤      👣      👥      👤      👣      👥      👤
(站立) (抬腿) (跨步) (站立) (抬腿) (跨步) (完成)

SMPL 参数随时间变化：
body_pose[0]    ≠  body_pose[10]  ≠  body_pose[20]  ...
global_orient[0] ≠ global_orient[10] ≠ ...
transl[0]       ≠  transl[10]     ≠  transl[20]     ...
```

---

## 5. SMPL 在 GR00T 项目中的作用

### 5.1 数据流

```
动捕数据（CMU Mocap, Bones-SEED）
    ↓
提取 SMPL 参数
    ├─ 使用 VIBE 或其他方法
    └─ 得到每帧的 (betas, body_pose, global_orient, transl)
    ↓
SMPL 编码器（在 SONIC 中）
    ├─ 输入：SMPL 参数序列
    ├─ 处理：通过神经网络编码
    └─ 输出：64 维潜在向量
    ↓
SONIC 控制策略
    ├─ 输入：64 维潜在向量
    ├─ 计算：使用 PPO 策略
    └─ 输出：G1 关节命令
    ↓
G1 机器人执行动作
```

### 5.2 为什么用 SMPL？

**优点：**

1. **紧凑表示**
   - 用 76 个数字（betas×1 + body_pose×63 + global_orient×3 + transl×3）表示整个身体
   - 相比直接存储关节位置（21×3 = 63）更高效

2. **人体先验**
   - SMPL 包含了人体生物学约束
   - 自动处理关节之间的依赖关系

3. **标准化**
   - 所有人体数据都用相同的表示方式
   - 便于跨数据集使用

4. **可微分**
   - SMPL 是可微分的（PyTorch/TensorFlow）
   - 可以在反向传播中优化

5. **易于转移**
   - SMPL 是标准格式
   - 可以从任何人体数据源提取
   - 与特定机器人无关

### 5.3 具体工作流

```bash
# 1. 获得原始人类运动数据（BVH 或动捕）
data/bones_seed/bvh/walk_001.bvh

# 2. 提取 SMPL 参数
python gear_sonic/data_process/extract_smpl_from_bvh.py \
    --input data/bones_seed/bvh/walk_001.bvh \
    --output data/smpl_filtered/walk_001.pkl

# 3. PKL 文件包含 SMPL 参数
with open('walk_001.pkl', 'rb') as f:
    data = pickle.load(f)
    # data['body_pose']     → (T, 63)
    # data['global_orient'] → (T, 3)
    # data['transl']        → (T, 3)
    # data['betas']         → (10,)

# 4. SONIC 编码器处理
encoder_input = {
    'body_pose': data['body_pose'],
    'global_orient': data['global_orient'],
    'transl': data['transl'],
    'betas': data['betas'],
}
latent_token = smpl_encoder(encoder_input)  # → (T, 64)

# 5. 策略生成机器人动作
robot_action = policy(latent_token)  # → (T, 29) for G1
```

---

## 6. SMPL 参数详细解释

### 6.1 身体形状参数的具体含义

```python
# SMPL betas 的 10 个维度（基于统计学习）
betas = {
    0: "整体身体大小（肥胖度）",
    1: "肌肉发达程度（athletic vs. slim）",
    2: "身体宽度（宽肩 vs. 窄肩）",
    3: "胸部大小",
    4: "腰部厚度",
    5: "臀部大小",
    6: "腿部长度",
    7: "腿部厚度",
    8: "手臂长度",
    9: "其他身体特征（手、脚等）",
}

# 实际例子
small_person = np.array([-0.5, -0.5, -0.5, -0.3, -0.3, -0.3, 0.0, -0.3, -0.3, 0.0])
large_person = np.array([0.5, 0.5, 0.5, 0.3, 0.3, 0.3, 0.5, 0.3, 0.3, 0.5])
athletic_person = np.array([0.0, 0.5, 0.0, -0.2, -0.3, -0.2, 0.0, -0.5, 0.0, 0.0])
```

### 6.2 轴角旋转的详细说明

```python
import numpy as np
from scipy.spatial.transform import Rotation as R

# 轴角表示法（Axis-Angle / Rodrigues）
# 一个 3D 向量表示旋转

# 例 1：绕 Z 轴旋转 90 度
angle = np.pi / 2  # 90 度 = π/2 弧度
axis = np.array([0, 0, 1])  # Z 轴
axis_angle = axis * angle  # [0, 0, 1.57]

# 转换为旋转矩阵
rot = R.from_rotvec(axis_angle)
rot_matrix = rot.as_matrix()
# [[0.0, -1.0, 0.0],
#  [1.0,  0.0, 0.0],
#  [0.0,  0.0, 1.0]]

# 例 2：绕 X 轴旋转 45 度
angle = np.pi / 4  # 45 度
axis = np.array([1, 0, 0])  # X 轴
axis_angle = axis * angle  # [0.785, 0, 0]

# 为什么用轴角？
# ✅ 紧凑（3个数字表示旋转）
# ✅ 可微分（可反向传播）
# ✅ 直观（方向是旋转轴，大小是旋转角）

# 转换关系
# 轴角 ←→ 四元数 ←→ 旋转矩阵
axis_angle = np.array([0.1, 0.2, 0.3])
rot = R.from_rotvec(axis_angle)

quat = rot.as_quat()  # [x, y, z, w]
rot_matrix = rot.as_matrix()  # (3, 3)
euler_angles = rot.as_euler('xyz')  # [roll, pitch, yaw]
```

---

## 7. SMPL 与机器人的关系

### 7.1 SMPL → 机器人关节的映射

```
SMPL 人体模型
    ↓
    21 个关节的 3D 位置和旋转
    ├─ Pelvis（骨盆）
    ├─ Left Hip
    ├─ Right Hip
    ├─ ... (等等21个)
    └─ (关节位置)
    ↓
    Retargeting（关键步骤！）
    ├─ 从人体关节提取想要的信息
    ├─ 映射到机器人的关节空间
    └─ 处理尺度不匹配、关节数量差异等
    ↓
机器人命令
    ├─ G1: 29 个 DOF
    └─ H2: 31 个 DOF
```

### 7.2 G1 Retargeting 例子

```python
def smpl_to_g1(smpl_data):
    """
    从 SMPL 参数生成 G1 命令
    """
    T = smpl_data['body_pose'].shape[0]
    
    # G1 有 29 个自由度
    g1_commands = np.zeros((T, 29), dtype=np.float32)
    
    # 从 SMPL 中提取关键关节
    smpl_joints = extract_joints_from_smpl(smpl_data)
    # smpl_joints: (T, 21, 3)
    
    # 映射到 G1 关节
    for t in range(T):
        # 腿部
        g1_commands[t, 0:6] = smpl_to_g1_leg_left(smpl_joints[t])
        g1_commands[t, 6:12] = smpl_to_g1_leg_right(smpl_joints[t])
        
        # 躯干
        g1_commands[t, 12:14] = smpl_to_g1_torso(smpl_joints[t])
        
        # 头部
        g1_commands[t, 14:16] = smpl_to_g1_head(smpl_joints[t])
        
        # 双臂
        g1_commands[t, 16:22] = smpl_to_g1_arms(smpl_joints[t])
        
        # 手腕
        g1_commands[t, 22:29] = smpl_to_g1_wrists(smpl_joints[t])
    
    return g1_commands
```

---

## 8. 常见问题

### Q1: SMPL 的 10 个 betas 是如何确定的？

**A:** 通过 PCA（主成分分析）：
1. 收集数千个人的 3D 身体扫描数据
2. 对这些身体进行 PCA 分析
3. 取前 10 个主成分作为 betas
4. 这 10 个维度解释了 ~99% 的身体形状变异

### Q2: 为什么用轴角而不是四元数或欧拉角？

**A:** 优点：
- ✅ 维度最少（3D，而四元数是4D）
- ✅ 可微分且梯度计算简单
- ✅ 物理意义清楚（旋转轴×旋转角）
- ✅ 不会出现万向锁问题（相比欧拉角）

### Q3: SMPL 能表示所有人体动作吗？

**A:** 基本上是的：
- ✅ 正常的人类动作（走路、跳舞、拿东西等）
- ❌ 极端情况（骨折、非自然弯曲等）
- ❌ 服装变形（穿着厚重衣服时精度降低）

### Q4: 如何从视频中提取 SMPL 参数？

**A:** 使用深度学习模型（如 VIBE、SPIN 等）：
```python
# 伪代码
video_frames = load_video('walk.mp4')  # (T, H, W, 3)
smpl_params = vibe_model(video_frames)  # 使用预训练模型
# 输出：T 帧的 betas, body_pose, global_orient, transl
```

### Q5: SMPL 文件通常以什么格式存储？

**A:** 在 GR00T 项目中：
- ✅ **PKL 格式**（Python pickle）- 最常用
- ✅ **NPZ 格式**（NumPy 压缩）
- ✅ **JSON** - 用于元数据
- ❌ 不直接用 SMPL 官方格式

---

## 9. SMPL 在 GR00T 中的具体数值

### 9.1 SONIC 的 SMPL 编码器输入

```python
# SONIC 编码器期望的输入
smpl_input = {
    # 身体形状（共享）
    'betas': np.zeros(10, dtype=np.float32),
    
    # 姿态（每帧）
    'body_pose': np.zeros((T, 63), dtype=np.float32),      # 21 joints × 3
    'global_orient': np.zeros((T, 3), dtype=np.float32),   # 根节点旋转
    
    # 位置（每帧）
    'transl': np.zeros((T, 3), dtype=np.float32),
}

# 输出：64 维潜在向量
latent_code = encoder(smpl_input)  # shape: (T, 64)
```

### 9.2 实际数值范围

```python
# 典型数值范围（基于数据统计）
betas_range = [-3, 3]              # 标准差单位
body_pose_range = [-1.5, 1.5]      # 弧度
global_orient_range = [-0.5, 0.5]  # 弧度
transl_range = [-∞, +∞]            # 米（无限制）

# 标准化示例
betas_normalized = (betas - mean) / std  # 零均值，单位方差
```

---

## 10. 总结：为什么 SMPL 很重要

| 方面 | 为什么 |
|------|-------|
| **数据表示** | 用 76 个数字精确表示整个人体动作 |
| **跨数据集** | 所有人体数据都用同一格式，便于融合 |
| **生物学先验** | 自动编码了人体关节约束 |
| **神经网络友好** | 可微分，易于集成到深度学习模型 |
| **标准化** | SMPL 是计算机视觉和动画领域的标准 |
| **可扩展** | 可以轻松从视频、动捕、BVH 等格式提取 |

---

## 🎯 快速查询

| 你想知道 | 位置 |
|--------|------|
| SMPL 在项目中如何使用 | [models_overview.md - 2.3](models_overview.md#23-sonic-的数据格式) |
| 详细的数据格式说明 | [data_formats_comparison.md - 1.2](data_formats_comparison.md#12-smpl-数据格式) |
| 如何处理 SMPL 数据 | [data_formats_comparison.md - 3](data_formats_comparison.md#3-实际工作中的数据处理示例) |
| SMPL 与 G1/H2 的映射 | [models_overview.md](models_overview.md) |
| 代码示例 | [gear_sonic/data_process/](../../gear_sonic/data_process/) |

---

更新时间：2026-08-14
