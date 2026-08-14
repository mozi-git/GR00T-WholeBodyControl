# SONIC 数据格式详解与与其他模型的对比

本文档详细说明SONIC模型的数据格式，以及与BeyondMimic等其他模型的关键区别。

---

## 1. SONIC 数据格式体系

### 1.1 motion_lib PKL 格式（核心训练数据）

SONIC 的核心训练数据存储为 **motion_lib PKL 格式**，这是 Isaac Lab 定义的运动库标准。

#### 文件结构

```
motion_lib_bones_seed/
├── robot/                    # 原始G1关节轨迹（142K动作）
│   ├── 00001.pkl           # 单个动作，PKL序列化
│   ├── 00002.pkl
│   └── ...
├── robot_filtered/          # 过滤后的G1轨迹（~130K）
│   ├── 00001.pkl
│   └── ...
└── soma_filtered/           # SOMA骨架轨迹（可选，~130K）
    ├── 00001.pkl
    └── ...
```

#### 单个PKL文件内容

```python
# 打开PKL文件查看内容
import pickle

with open('00001.pkl', 'rb') as f:
    motion_data = pickle.load(f)

# motion_data 是一个字典，包含以下关键字段：
print(motion_data.keys())
# dict_keys(['joint_pos', 'joint_vel', 'root_pos', 'root_rot', 
#            'fps', 'motion_name', 'body_pose', 'global_orient', ...])
```

#### 详细字段说明

| 字段 | 数据类型 | 形状 | 值范围 | 说明 |
|------|---------|------|--------|------|
| `joint_pos` | float32 | (T, 29) | [-2π, 2π] | G1机器人29个关节的位置 |
| `joint_vel` | float32 | (T, 29) | [-10, 10] rad/s | 关节速度 |
| `root_pos` | float32 | (T, 3) | 任意 (m) | 根节点（腰部）的XYZ位置 |
| `root_rot` | float32 | (T, 4) | 正规化 | 根节点的四元数旋转 [w, x, y, z] |
| `fps` | int | 标量 | 30 | 帧率（固定30fps） |
| `motion_name` | str | - | - | 运动名称（如"walk"） |

#### G1 关节映射

G1有29个关节，顺序如下：

```python
# G1关节顺序（遵循URDF定义）
joints_29 = [
    # 腰部（根节点）
    "floating_base_x", "floating_base_y", "floating_base_z",  # 根节点位置
    "floating_base_qx", "floating_base_qy", "floating_base_qz", "floating_base_qw",  # 根节点旋转（四元数）
    
    # 左腿（7个关节）
    "l_hip_roll", "l_hip_pitch", "l_hip_yaw",   # 髋关节
    "l_knee_pitch",                             # 膝关节
    "l_ankle_pitch", "l_ankle_roll",            # 踝关节
    "l_foot_contact",                           # 脚接触（虚拟）
    
    # 右腿（7个关节）
    "r_hip_roll", "r_hip_pitch", "r_hip_yaw",   # 髋关节
    "r_knee_pitch",                             # 膝关节
    "r_ankle_pitch", "r_ankle_roll",            # 踝关节
    "r_foot_contact",                           # 脚接触（虚拟）
    
    # 躯干和头（5个关节）
    "torso_pitch", "torso_roll",                # 躯干
    "neck_pitch", "neck_roll", "neck_yaw",      # 颈部
]

# 实际关节（排除根节点的浮动基座）
actual_joint_positions = joint_pos[:, 7:]  # 形状 (T, 22)，对应上面的22个关节
```

**注意**：PKL中的 `joint_pos` 形状是 (T, 29)，包括了浮动基座的3个位置 + 4个旋转 + 22个实际关节 = 29维。

#### SMPL 字段

同时包含原始SMPL参数（用于多模态编码器）：

| 字段 | 数据类型 | 形状 | 说明 |
|------|---------|------|------|
| `body_pose` | float32 | (T, 63) | 21个关节的轴角表示 (3×21=63) |
| `global_orient` | float32 | (T, 3) | 全局朝向的轴角表示 |
| `betas` | float32 | (10,) | SMPL身体形状参数（共享） |
| `trans` | float32 | (T, 3) | 全局平移 |
| `expression` | float32 | (T, 10) | 面部表情（可选） |

---

### 1.2 SMPL 数据格式

SMPL 是参数化人体模型，SONIC 使用它作为视觉输入。

#### SMPL 参数规范

```python
# SMPL模型定义（由Chumpy或PyTorch实现）
smpl_params = {
    # 形状参数（共享）
    'betas': shape (10,),            # 身体形状系数
    
    # 姿态参数（逐帧）
    'global_orient': shape (3,),     # 全局朝向（轴角）
    'body_pose': shape (63,),        # 21个关节 × 3轴角 = 63
    
    # 位置参数（逐帧）
    'transl': shape (3,),            # 全局XYZ位移
    
    # 可选参数
    'expression': shape (10,),       # 面部表情系数
}

# 时间序列：T帧 (T, param_dim)
```

#### SMPL 的21个关节

```
0: pelvis (根节点)
1-2: left leg (hip, knee)
3-4: right leg (hip, knee)
5-6: spine/torso
7-8: left arm (shoulder, elbow)
9-10: right arm (shoulder, elbow)
11-12: left hand (wrist, thumb)
13-14: right hand (wrist, thumb)
15-16: head
17-20: fingers (可选)
```

#### 轴角表示

```python
# 轴角表示 (3维向量)
# 方向: 旋转轴方向（单位向量）
# 大小: 旋转角度（弧度）
# 合并: 3维向量 = 方向 × 角度

import numpy as np
from scipy.spatial.transform import Rotation as R

# 从轴角转换为四元数
axis_angle = np.array([0.1, 0.2, 0.3])  # (3,)
rot = R.from_rotvec(axis_angle)
quaternion = rot.as_quat()  # (4,) [x, y, z, w]

# 从轴角转换为旋转矩阵
rotation_matrix = rot.as_matrix()  # (3, 3)
```

#### SMPL 编码器输入规范

SONIC的SMPL编码器期望的输入格式：

```python
# 输入: 时间序列SMPL姿态
T = 100  # 时间步
smpl_input = {
    'body_pose': np.zeros((T, 63), dtype=np.float32),      # 身体
    'global_orient': np.zeros((T, 3), dtype=np.float32),   # 全局朝向
    'betas': np.zeros(10, dtype=np.float32),               # 形状
    'transl': np.zeros((T, 3), dtype=np.float32),          # 位移
}

# 编码器输出: 64维潜在令牌
latent_token = encoder(smpl_input)  # shape: (T, 64)
```

---

### 1.3 G1 运动参考格式

当使用机器人关节作为输入时：

```python
# G1 运动参考输入
g1_input = {
    'joint_pos': np.zeros((T, 22), dtype=np.float32),   # 实际关节位置
    'joint_vel': np.zeros((T, 22), dtype=np.float32),   # 实际关节速度
    'root_pos': np.zeros((T, 3), dtype=np.float32),     # 根节点位置
    'root_rot': np.zeros((T, 4), dtype=np.float32),     # 根节点旋转（四元数）
}

# 或简化版本（仅位置和旋转）
g1_simple = {
    'root_pos': np.zeros((T, 3), dtype=np.float32),
    'root_rot': np.zeros((T, 4), dtype=np.float32),
    'joint_pos': np.zeros((T, 22), dtype=np.float32),
}
```

---

### 1.4 VR 遥操格式

VR遥操使用3点追踪（头部 + 两只手腕）：

```python
# VR遥操输入（3点追踪）
teleop_input = {
    'head_pos': np.zeros((T, 3), dtype=np.float32),       # 头部位置
    'head_rot': np.zeros((T, 4), dtype=np.float32),       # 头部旋转
    'left_wrist_pos': np.zeros((T, 3), dtype=np.float32), # 左腕位置
    'left_wrist_rot': np.zeros((T, 4), dtype=np.float32), # 左腕旋转
    'right_wrist_pos': np.zeros((T, 3), dtype=np.float32),# 右腕位置
    'right_wrist_rot': np.zeros((T, 4), dtype=np.float32),# 右腕旋转
}

# SONIC将其转换为SMPL姿态，然后通过SMPL编码器处理
```

---

### 1.5 SOMA 骨架格式

SOMA 是BVH文件的骨架表示，SONIC支持作为可选的第4编码器：

```python
# SOMA 骨架输入
soma_input = {
    'joint_pos': np.zeros((T, N_joints), dtype=np.float32),  # BVH关节位置
    'joint_rot': np.zeros((T, N_joints, 3), dtype=np.float32), # 逐关节旋转
}

# N_joints 取决于BVH文件的结构（通常20-50个关节）
```

---

## 2. SONIC vs BeyondMimic 对比

### 2.1 核心差异对照表

| 特性 | SONIC | BeyondMimic |
|------|-------|-----------|
| **模型架构** | 4个独立编码器 + FSQ量化 + 单解码器 | 单个编码器 + 解码器 |
| **输入类型** | 多模态（SMPL + G1 + VR + SOMA） | 单模态（SMPL） |
| **数据格式** | motion_lib PKL | NPZ |
| **编码器输出** | 64维量化令牌 | 连续向量 |
| **训练方法** | PPO + 运动追踪奖励 | 演示学习 |
| **控制频率** | 50 Hz | 30 Hz |
| **部署** | C++ + TensorRT | Python |
| **开源状态** | 已开源（2026年）| GitHub可得 |

### 2.2 输入数据格式对比

#### SONIC - motion_lib PKL

```
单个文件结构：
data/robot/00001.pkl
├─ joint_pos: (T, 29) float32   ← 包括浮动基座
├─ joint_vel: (T, 29) float32
├─ root_pos: (T, 3) float32
├─ root_rot: (T, 4) float32
├─ body_pose: (T, 63) float32   ← SMPL
├─ global_orient: (T, 3) float32
├─ betas: (10,) float32
├─ fps: int (30)
└─ motion_name: str

多个动作组合：
data/smpl_filtered/
├─ 00001.pkl (包含SMPL参数)
├─ 00002.pkl
└─ ... × ~130K
```

#### BeyondMimic - NPZ

```
单个NPZ文件结构：
data/motion_00001.npz
├─ poses: (T, 63) float32        ← SMPL body_pose
├─ root_orient: (T, 3) float32   ← SMPL global_orient
├─ root_pos: (T, 3) float32
├─ fps: int (30或120)
└─ metadata: dict

特点：
- 单个NPZ包含一个完整动作
- 主要存储SMPL参数
- 可能有不同的帧率（需转换）
```

### 2.3 数据准备流程对比

#### SONIC 数据准备

```
原始数据（Bones-SEED）
    ↓
csv/bvh 转换
    ↓
motion_lib PKL 格式
    ├─ robot/           (G1关节轨迹)
    ├─ smpl_filtered/   (SMPL参数)
    └─ soma_filtered/   (可选SOMA骨架)
    ↓
过滤（移除G1无法执行的动作）
    ↓
最终数据集（~130K动作）
```

#### BeyondMimic 数据准备

```
原始数据（CMU Mocap/其他）
    ↓
NPZ 转换
    ├─ 提取SMPL参数
    ├─ 设置fps
    └─ 保存元数据
    ↓
最终数据集（NPZ文件集合）
```

### 2.4 技术栈对比

| 组件 | SONIC | BeyondMimic |
|------|-------|-----------|
| **模型框架** | PyTorch | PyTorch |
| **训练引擎** | Isaac Lab + PPO (TRL) | 标准PyTorch |
| **仿真环境** | MuJoCo (Isaac Lab) | MuJoCo |
| **部署** | C++ + ONNX + TensorRT | Python |
| **运行频率** | 50 Hz | 30 Hz |
| **GPU支持** | 64+ GPUs推荐 | 8+ GPUs可用 |

---

## 3. 实际工作中的数据处理示例

### 3.1 读取和验证motion_lib PKL

```python
import pickle
import numpy as np
from pathlib import Path

# 读取单个PKL文件
pkl_path = Path("data/motion_lib_bones_seed/robot/00001.pkl")
with open(pkl_path, 'rb') as f:
    motion = pickle.load(f)

# 验证数据结构
print("Motion keys:", motion.keys())
print("Joint positions shape:", motion['joint_pos'].shape)  # (T, 29)
print("Root position shape:", motion['root_pos'].shape)     # (T, 3)
print("Root rotation shape:", motion['root_rot'].shape)     # (T, 4)
print("SMPL body pose shape:", motion['body_pose'].shape)   # (T, 63)
print("FPS:", motion['fps'])

# 验证数值范围
print("\nValue ranges:")
print(f"Joint positions: [{motion['joint_pos'].min():.2f}, {motion['joint_pos'].max():.2f}]")
print(f"Root position: [{motion['root_pos'].min():.2f}, {motion['root_pos'].max():.2f}]")

# 验证时间一致性
assert motion['joint_pos'].shape[0] == motion['body_pose'].shape[0], \
    "Temporal mismatch between joint_pos and body_pose"

print("✓ Data validation passed!")
```

### 3.2 转换NPZ为motion_lib PKL（如需混用）

```python
import numpy as np
import pickle
from pathlib import Path
from scipy.spatial.transform import Rotation as R

def npz_to_motion_lib_pkl(npz_path, output_pkl_path, fps=30):
    """
    将BeyondMimic风格NPZ转换为SONIC motion_lib PKL
    """
    # 读取NPZ
    data = np.load(npz_path)
    
    # 提取SMPL参数
    poses = data['poses']  # (T, 63)
    root_orient = data['root_orient']  # (T, 3) 轴角
    root_pos = data['root_pos']  # (T, 3)
    
    # 转换根节点旋转：轴角 → 四元数
    quaternions = []
    for i in range(len(root_orient)):
        rot = R.from_rotvec(root_orient[i])
        quat = rot.as_quat()  # [x, y, z, w]
        quaternions.append(quat)
    root_rot = np.array(quaternions)  # (T, 4)
    
    # 创建motion_lib格式
    motion_lib = {
        # G1关节（需要通过SMPL→G1映射，这里简化为零）
        'joint_pos': np.zeros((len(poses), 29), dtype=np.float32),
        'joint_vel': np.zeros((len(poses), 29), dtype=np.float32),
        
        # 根节点
        'root_pos': root_pos.astype(np.float32),
        'root_rot': root_rot.astype(np.float32),
        
        # SMPL参数
        'body_pose': poses.astype(np.float32),
        'global_orient': root_orient.astype(np.float32),
        'betas': data.get('betas', np.zeros(10, dtype=np.float32)),
        
        # 元数据
        'fps': fps,
        'motion_name': Path(npz_path).stem,
    }
    
    # 保存为PKL
    with open(output_pkl_path, 'wb') as f:
        pickle.dump(motion_lib, f)
    
    print(f"✓ Converted {npz_path} → {output_pkl_path}")
    return motion_lib
```

### 3.3 批量验证motion_lib PKL数据集

```python
import pickle
import numpy as np
from pathlib import Path
from collections import defaultdict

def validate_motion_lib_dataset(dataset_dir):
    """
    验证整个motion_lib数据集的完整性
    """
    dataset_path = Path(dataset_dir)
    pkl_files = sorted(dataset_path.glob("*.pkl"))
    
    stats = {
        'total_motions': len(pkl_files),
        'valid_motions': 0,
        'invalid_motions': [],
        'frame_counts': [],
        'fps_values': defaultdict(int),
        'joint_ranges': {'min': float('inf'), 'max': float('-inf')},
    }
    
    for pkl_file in pkl_files:
        try:
            with open(pkl_file, 'rb') as f:
                motion = pickle.load(f)
            
            # 验证必要字段
            required_fields = ['joint_pos', 'root_pos', 'root_rot', 'body_pose', 'fps']
            for field in required_fields:
                assert field in motion, f"Missing field: {field}"
            
            # 验证形状
            T = motion['joint_pos'].shape[0]
            assert motion['joint_pos'].shape == (T, 29)
            assert motion['root_pos'].shape == (T, 3)
            assert motion['root_rot'].shape == (T, 4)
            assert motion['body_pose'].shape == (T, 63)
            
            # 验证数值范围
            assert np.all(np.isfinite(motion['joint_pos']))
            assert np.all(np.isfinite(motion['body_pose']))
            
            # 统计
            stats['valid_motions'] += 1
            stats['frame_counts'].append(T)
            stats['fps_values'][motion['fps']] += 1
            stats['joint_ranges']['min'] = min(
                stats['joint_ranges']['min'],
                motion['joint_pos'].min()
            )
            stats['joint_ranges']['max'] = max(
                stats['joint_ranges']['max'],
                motion['joint_pos'].max()
            )
            
        except Exception as e:
            stats['invalid_motions'].append((pkl_file.name, str(e)))
    
    # 打印报告
    print(f"Dataset Validation Report for {dataset_dir}")
    print("=" * 60)
    print(f"Total motions: {stats['total_motions']}")
    print(f"Valid motions: {stats['valid_motions']} ✓")
    print(f"Invalid motions: {len(stats['invalid_motions'])}")
    
    if stats['invalid_motions']:
        print("\nInvalid motions:")
        for name, error in stats['invalid_motions'][:5]:
            print(f"  - {name}: {error}")
    
    print(f"\nFrame count statistics:")
    print(f"  Min: {min(stats['frame_counts'])} frames")
    print(f"  Max: {max(stats['frame_counts'])} frames")
    print(f"  Mean: {np.mean(stats['frame_counts']):.1f} frames")
    
    print(f"\nFPS distribution: {dict(stats['fps_values'])}")
    
    print(f"\nJoint value ranges:")
    print(f"  Min: {stats['joint_ranges']['min']:.3f}")
    print(f"  Max: {stats['joint_ranges']['max']:.3f}")
    
    return stats
```

### 3.4 从SMPL生成SONIC兼容的motion_lib

```python
def create_motion_lib_from_smpl(
    smpl_params,  # dict with body_pose, global_orient, transl
    motion_name="custom_motion",
    fps=30
):
    """
    从SMPL参数创建SONIC兼容的motion_lib条目
    
    Args:
        smpl_params: 包含以下字段的字典
            - body_pose: (T, 63) SMPL身体姿态
            - global_orient: (T, 3) 全局朝向
            - transl: (T, 3) 平移
            - betas: (10,) 身体形状
    """
    T = smpl_params['body_pose'].shape[0]
    
    # 根节点旋转转换：轴角 → 四元数
    from scipy.spatial.transform import Rotation as R
    
    quaternions = []
    for i in range(T):
        rot = R.from_rotvec(smpl_params['global_orient'][i])
        quat = rot.as_quat()
        quaternions.append(quat)
    
    motion_lib = {
        # G1关节（通常需要通过retargeting从SMPL得到）
        # 这里为演示，使用零矩阵（实际应该使用SMPL→G1映射）
        'joint_pos': np.zeros((T, 29), dtype=np.float32),
        'joint_vel': np.zeros((T, 29), dtype=np.float32),
        
        # 根节点（从SMPL平移和旋转）
        'root_pos': smpl_params['transl'].astype(np.float32),
        'root_rot': np.array(quaternions, dtype=np.float32),
        
        # SMPL参数（直接传递）
        'body_pose': smpl_params['body_pose'].astype(np.float32),
        'global_orient': smpl_params['global_orient'].astype(np.float32),
        'betas': smpl_params['betas'].astype(np.float32),
        
        # 元数据
        'fps': fps,
        'motion_name': motion_name,
    }
    
    return motion_lib
```

---

## 4. 数据尺寸与存储成本

### 4.1 单个运动的大小

```
假设一个50秒的运动（30fps）：
T = 50 × 30 = 1500 帧

motion_lib PKL 包含：
- joint_pos: 1500 × 29 × 4 bytes = 174 KB
- joint_vel: 1500 × 29 × 4 bytes = 174 KB
- root_pos: 1500 × 3 × 4 bytes = 18 KB
- root_rot: 1500 × 4 × 4 bytes = 24 KB
- body_pose: 1500 × 63 × 4 bytes = 378 KB
- global_orient: 1500 × 3 × 4 bytes = 18 KB
- betas: 10 × 4 bytes = 40 bytes
- 其他元数据: ~100 bytes

总计单个PKL: ~790 KB（包括Python序列化开销）

建议: ~1 MB/运动
```

### 4.2 完整数据集大小

```
Bones-SEED 数据集：

原始 CSV/BVH: ~50 GB
转换后 motion_lib PKL:
  - robot/: ~130K × 1 MB = 130 GB
  - smpl_filtered/: ~130K × 1 MB = 130 GB
  - soma_filtered/: ~130K × 1 MB = 130 GB

总计: ~390 GB（完整3编码器配置）

存储优化:
- 仅保留 robot_filtered + smpl_filtered: ~260 GB
- 压缩PKL文件: ~100-150 GB
```

### 4.3 存储建议

| 场景 | 推荐方案 | 存储成本 |
|------|---------|--------|
| 快速测试 | sample_data（少量） | 1-5 GB |
| 微调 | robot_filtered + smpl_filtered | 260 GB |
| 生产训练 | 完整数据集 | 390 GB |

---

## 5. 常见数据格式错误及修复

### 错误1：维度不匹配

```python
# 错误
body_pose = np.zeros((T, 72))  # 应该是63，不是72
# 原因：可能来自其他模型（72 = 24关节×3）

# 修复
body_pose_correct = body_pose[:, :63]  # 或进行适当的映射
```

### 错误2：四元数未归一化

```python
# 错误
quat = np.array([1, 2, 3, 4])  # 未归一化

# 修复
quat_norm = quat / np.linalg.norm(quat)  # 归一化至单位长度
```

### 错误3：轴角与四元数混淆

```python
# 错误：将轴角当作四元数使用
root_rot = body_pose[:3]  # 轴角，长度3
# 实际应该是四元数，长度4

# 修复：转换轴角到四元数
from scipy.spatial.transform import Rotation as R
rot = R.from_rotvec(axis_angle)
quat = rot.as_quat()
```

### 错误4：帧率不一致

```python
# 错误：混合不同帧率的数据
# motion1: 30 fps，motion2: 120 fps

# 修复：统一到目标帧率
def resample_motion(motion, target_fps, source_fps):
    """重采样运动到目标帧率"""
    from scipy import interpolate
    
    T_source = motion.shape[0]
    time_source = np.arange(T_source) / source_fps
    
    T_target = int(T_source * target_fps / source_fps)
    time_target = np.arange(T_target) / target_fps
    
    f = interpolate.interp1d(time_source, motion, axis=0, kind='cubic')
    resampled = f(time_target)
    
    return resampled
```

---

## 总结：何时选择什么格式

| 场景 | 推荐格式 | 原因 |
|------|---------|------|
| SONIC 训练 | motion_lib PKL | 官方标准，多模态支持 |
| BeyondMimic 训练 | NPZ | 官方标准 |
| 数据交换 | NPZ（单模态）+ PKL（多模态） | 通用性 |
| 云存储 | 压缩NPZ/PKL | 节省带宽 |
| 快速原型 | 任意格式（只要一致） | 灵活性 |

---

**最后更新**：2026-08-14
