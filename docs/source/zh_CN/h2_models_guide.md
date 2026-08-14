# Unitree H2 机器人 SONIC 模型完整指南

本文档详细说明如何在 Unitree H2 机器人上使用和训练 SONIC 全身控制模型。

---

## 1. Unitree H2 机器人基础信息

### 1.1 硬件规格对比

| 特性 | Unitree G1 | Unitree H2 |
|------|-----------|-----------|
| **身体自由度 (DOF)** | 29 | **31** |
| **身体数量** | 23 | **32** |
| **躯干设计** | 单腰部 | **双腰部（pitch + roll + yaw）** |
| **头部** | 简化（2 DOF） | **完整（3 DOF）** |
| **腕部** | 简化（2×2 DOF） | **完整（2×3 DOF）** |
| **关节配置** | 较紧凑 | **更人形化** |
| **高度** | ~1.5m | ~1.7m |
| **质量** | ~55kg | ~65kg |
| **应用场景** | 通用人形 | 高精度操作 |

### 1.2 关键区别

**H2 比 G1 多2个自由度：**

| 增加的关节 | 位置 | 作用 |
|----------|------|------|
| `waist_pitch_link` | 躯干 | 躯干前后弯曲 |
| `waist_roll_link` | 躯干 | 躯干左右倾斜 |

**H2 腕部更复杂：**
- G1: 每只手腕 2 个关节（roll + pitch）
- H2: 每只手腕 3 个关节（roll + pitch + yaw）

**H2 头部更灵活：**
- G1: 头部 2 个关节（pitch + yaw）
- H2: 头部 3 个关节（pitch + roll + yaw）

---

## 2. H2 的 SONIC 模型

### 2.1 可用的 H2 模型

目前 GR00T 项目中对 H2 的支持情况：

| 模型 | 发布状态 | 预训练权重 | 配置文件 | 说明 |
|------|---------|---------|---------|------|
| **SONIC H2** | ✅ 支持 | ❌ 未发布 | ✅ 有 | 基于 SONIC 架构但为 H2 优化 |

### 2.2 SONIC H2 配置详解

**位置：** `gear_sonic/config/exp/manager/universal_token/all_modes/sonic_h2.yaml`

**核心参数：**

```yaml
# 机器人类型指定
manager_env:
  config:
    robot:
      type: h2              # 指定为H2机器人
    terrain_type: trimesh   # 地形类型

# 运动跟踪参数
  commands:
    motion:
      # 追踪点（与G1不同的设置）
      reward_point_body: ["torso_link", "left_wrist_yaw_link", "right_wrist_yaw_link"]
      reward_point_body_offset: [[0.0, 0.0, 0.5], [0.0, -0.0, 0.0], [0.0, -0.0, 0.0]]
      
      # 参考帧设置（与G1相同）
      num_future_frames: 10              # 10帧SMPL前瞻
      dt_future_ref_frames: 0.1          # 20ms间隔
      smpl_num_future_frames: 10
      smpl_dt_future_ref_frames: 0.02
      
      # 数据增强
      cat_upper_body_poses: true         # 连接上身姿态
      cat_upper_body_poses_prob: 0.5     # 50%概率
      freeze_frame_aug: true             # 冻结帧增强
      teleop_sample_prob_when_smpl: 0.5  # SMPL时遥操采样概率

# 数据集配置
      motion_lib_cfg:
        motion_file: null                # 运动数据路径（需指定）
        smpl_motion_file: dummy          # SMPL数据路径
        smpl_y_up: true                  # SMPL坐标系
        asset:
          assetFileName: "h2.xml"        # 物理模型

# 算法配置
algo:
  config:
    num_envs: 4096          # 并行环境（可调）
    num_steps_per_env: 24   # 每环境步数
    learning_rate: 2e-5     # PPO学习率
```

### 2.3 H2 的关节映射

**H2 有 31 个自由度（相比 G1 的 29 个）**

```python
# H2 IsaacLab 中的关节顺序（32个body）
H2_ISAACLAB_JOINTS = [
    # 根节点
    "pelvis",
    
    # 下身（腿）
    "left_hip_pitch_link",    # 0
    "right_hip_pitch_link",   # 1
    "left_hip_roll_link",     # 2
    "right_hip_roll_link",    # 3
    "left_hip_yaw_link",      # 4
    "right_hip_yaw_link",     # 5
    "left_knee_link",         # 6
    "right_knee_link",        # 7
    "left_ankle_pitch_link",  # 8
    "right_ankle_pitch_link", # 9
    "left_ankle_roll_link",   # 10
    "right_ankle_roll_link",  # 11
    
    # 躯干（H2特有：多了waist关节）
    "waist_roll_link",        # 12 ← H2独有
    "waist_yaw_link",         # 13
    "torso_link",             # 14
    
    # 头部
    "head_pitch_link",        # 15
    "head_yaw_link",          # 16
    "head_roll_link",         # 17 ← H2新增
    
    # 上身（双臂）
    "left_shoulder_pitch_link",   # 18
    "right_shoulder_pitch_link",  # 19
    "left_shoulder_roll_link",    # 20
    "right_shoulder_roll_link",   # 21
    "left_shoulder_yaw_link",     # 22
    "right_shoulder_yaw_link",    # 23
    "left_elbow_link",            # 24
    "right_elbow_link",           # 25
    
    # 手腕（H2有yaw，G1没有）
    "left_wrist_roll_link",       # 26
    "right_wrist_roll_link",      # 27
    "left_wrist_pitch_link",      # 28
    "right_wrist_pitch_link",     # 29
    "left_wrist_yaw_link",        # 30 ← H2新增
    "right_wrist_yaw_link",       # 31 ← H2新增
]

# MuJoCo 中的 DOF 映射
# IsaacLab → MuJoCo 的顺序不同，需要转换
H2_ISAACLAB_TO_MUJOCO_DOF = [
    0,   # pelvis → 0
    3,   # left_hip_pitch → 3
    6,   # right_hip_pitch → 6
    9,   # left_hip_roll → 9
    14,  # right_hip_roll → 14
    19,  # left_hip_yaw → 19
    # ... 等等
]
```

**关键点：**
- H2 有 **31 个自由度**（不含根节点浮动基座）
- 包含 **32 个 body**（包括根节点）
- 与 G1 相比多了：
  - 腰部：waist_pitch（虽然config中没有显示，但结构中有）
  - 头部：head_roll
  - 手腕：left_wrist_yaw, right_wrist_yaw

---

## 3. H2 上的 SONIC 训练

### 3.1 数据准备

H2 需要的数据与 G1 不同，需要为 H2 机器人重新生成运动库。

#### 步骤1：获取原始 SMPL 数据

```bash
# 使用 Bones-SEED 数据集（与 G1 相同）
python download_from_hf.py --training
```

#### 步骤2：Retarget SMPL 到 H2

```bash
# 与 G1 不同，H2 需要专门的 retargeting
# 这一步将 SMPL 人体模型适配到 H2 的关节配置

python gear_sonic/data_process/retarget_smpl_to_h2.py \
    --input /path/to/smpl_data \
    --output data/motion_lib_h2/smpl_h2 \
    --fps 30 \
    --num_workers 16
```

#### 步骤3：从 H2 MuJoCo 模型生成运动库

```bash
# 从 retarget 后的 SMPL 生成 H2 motion_lib
python gear_sonic/data_process/convert_smpl_to_motion_lib_h2.py \
    --input data/motion_lib_h2/smpl_h2 \
    --output data/motion_lib_h2/robot \
    --fps 30 \
    --h2_model_path gear_sonic/data/assets/robot_description/mjcf/h2.xml \
    --num_workers 16
```

#### 步骤4：过滤运动

```bash
# H2 无法执行的动作可能与 G1 不同
python gear_sonic/data_process/filter_and_copy_bones_data.py \
    --source data/motion_lib_h2/robot \
    --dest data/motion_lib_h2/robot_filtered \
    --workers 16 \
    --embodiment h2  # 指定为 H2
```

### 3.2 训练命令

#### 从头训练 H2 SONIC

```bash
# 多机多卡训练（推荐64+ GPUs）
accelerate launch \
    --multi_gpu \
    --num_machines=8 \
    --num_processes=64 \
    --machine_rank=$MACHINE_RANK \
    --main_process_ip=$MASTER_ADDR \
    --main_process_port=$MASTER_PORT \
    gear_sonic/train_agent_trl.py \
    +exp=manager/universal_token/all_modes/sonic_h2 \
    num_envs=4096 headless=True \
    ++manager_env.commands.motion.motion_lib_cfg.motion_file=data/motion_lib_h2/robot_filtered \
    ++manager_env.commands.motion.motion_lib_cfg.smpl_motion_file=data/motion_lib_h2/smpl_h2_filtered
```

#### 单机 8 GPU 训练

```bash
accelerate launch --num_processes=8 gear_sonic/train_agent_trl.py \
    +exp=manager/universal_token/all_modes/sonic_h2 \
    num_envs=4096 headless=True \
    ++manager_env.commands.motion.motion_lib_cfg.motion_file=data/motion_lib_h2/robot_filtered \
    ++manager_env.commands.motion.motion_lib_cfg.smpl_motion_file=data/motion_lib_h2/smpl_h2_filtered
```

### 3.3 H2 特定的训练注意事项

| 参数 | H2 推荐值 | 说明 |
|------|---------|------|
| `num_envs` | 4096 | 可根据GPU调整 |
| `learning_rate` | 2e-5 | 与G1相同 |
| `reward_scale_waist` | 1.0 | 腰部追踪权重（新增） |
| `reward_scale_head_roll` | 0.5 | 头部roll权重（新增） |
| `reward_scale_wrist_yaw` | 0.8 | 手腕yaw权重（新增） |

### 3.4 监控指标

```python
# 监控以下H2特定指标
rewards = {
    'tracking_waist_pitch': > 0.7,    # 腰部pitch追踪
    'tracking_waist_roll': > 0.7,     # 腰部roll追踪
    'tracking_waist_yaw': > 0.8,      # 腰部yaw追踪
    'tracking_head_roll': > 0.6,      # 头部roll追踪
    'tracking_wrist_yaw': > 0.75,     # 手腕yaw追踪
    'total': > 3.0,                   # 总回报
}
```

---

## 4. H2 的数据格式

### 4.1 H2 motion_lib PKL 格式

与 G1 相同，但关节维度不同：

```python
# H2 motion_lib PKL 文件内容
motion_lib_h2 = {
    # 关节数据（31 DOF，不含根节点）
    'joint_pos': (T, 31) float32,    # ← 与G1的29不同
    'joint_vel': (T, 31) float32,
    
    # 根节点数据（与G1相同）
    'root_pos': (T, 3) float32,
    'root_rot': (T, 4) float32,      # 四元数
    
    # SMPL数据（与G1相同）
    'body_pose': (T, 63) float32,
    'global_orient': (T, 3) float32,
    'betas': (10,) float32,
    'transl': (T, 3) float32,
    
    # 元数据
    'fps': int (30),
    'motion_name': str,
}
```

### 4.2 关键区别：关节顺序

```python
# G1 的 29 个自由度结构
joint_pos_g1 = [
    # 腿（12个）
    left_hip_roll, left_hip_pitch, left_hip_yaw,
    left_knee, left_ankle_pitch, left_ankle_roll,
    right_hip_roll, right_hip_pitch, right_hip_yaw,
    right_knee, right_ankle_pitch, right_ankle_roll,
    # 躯干（1个）
    torso_pitch, torso_roll,
    # 头（2个）
    neck_pitch, neck_roll, neck_yaw,
    # 双臂（6个）
    left/right_shoulder_pitch/roll/yaw,
    left/right_elbow,
    # 手腕（2个×2）
    left/right_wrist_roll/pitch,
]

# H2 的 31 个自由度结构
joint_pos_h2 = [
    # 腿（12个）
    left_hip_roll, left_hip_pitch, left_hip_yaw,
    left_knee, left_ankle_pitch, left_ankle_roll,
    right_hip_roll, right_hip_pitch, right_hip_yaw,
    right_knee, right_ankle_pitch, right_ankle_roll,
    # 躯干（3个，比G1多）← H2新增
    waist_roll, waist_yaw, torso_pitch,
    # 头（3个，比G1多）← H2新增
    head_pitch, head_yaw, head_roll,
    # 双臂（6个）
    left/right_shoulder_pitch/roll/yaw,
    left/right_elbow,
    # 手腕（3个×2，比G1多）← H2新增yaw
    left/right_wrist_roll/pitch/yaw,
]
```

---

## 5. H2 的数据转换与兼容性

### 5.1 G1 数据是否能用于 H2 训练？

**直接答案：❌ 不行**

**原因：**
- G1 和 H2 的关节数量不同（29 vs 31）
- 关节顺序不同
- 部分关节在不同位置
- 需要重新 retarget

### 5.2 转换流程

```
原始SMPL数据
    ↓
SMPL → G1 Retarget
    ↓
G1 motion_lib PKL（29 DOF）
    ↓
G1 → H2 关节转换（需要映射脚本）
    ↓
H2 motion_lib PKL（31 DOF）
    ↓
训练 SONIC H2
```

### 5.3 G1 → H2 关节映射脚本示例

```python
def convert_g1_motion_to_h2(g1_motion_lib):
    """
    将 G1 motion_lib 转换为 H2 motion_lib
    需要插值新增关节
    """
    T = g1_motion_lib['joint_pos'].shape[0]
    
    # 新建 H2 格式数组
    h2_joint_pos = np.zeros((T, 31), dtype=np.float32)
    h2_joint_vel = np.zeros((T, 31), dtype=np.float32)
    
    # G1 关节映射到 H2（这里需要具体的映射规则）
    g1_to_h2_mapping = {
        # 腿部（直接复制）
        0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5,
        6: 6, 7: 7, 8: 8, 9: 9, 10: 10, 11: 11,
        # 躯干（G1的2个 → H2的3个）
        12: 12,  # G1 torso_pitch → H2 waist_roll
        13: 13,  # G1 torso_roll → H2 waist_yaw
        # H2 新增 torso_pitch（需要插值）
        # 14: 从头部或SMPL推导
        # ...
    }
    
    # 应用映射
    for g1_idx, h2_idx in g1_to_h2_mapping.items():
        h2_joint_pos[:, h2_idx] = g1_motion_lib['joint_pos'][:, g1_idx]
        h2_joint_vel[:, h2_idx] = g1_motion_lib['joint_vel'][:, g1_idx]
    
    # 新增关节需要从SMPL或运动学推导
    h2_motion_lib = g1_motion_lib.copy()
    h2_motion_lib['joint_pos'] = h2_joint_pos
    h2_motion_lib['joint_vel'] = h2_joint_vel
    
    return h2_motion_lib
```

---

## 6. H2 的评估与部署

### 6.1 评估 H2 模型

```bash
# 评估指标模式
python gear_sonic/eval_agent_trl.py \
    +checkpoint=<path_to_h2_checkpoint.pt> \
    +headless=True \
    ++eval_callbacks=im_eval \
    ++run_eval_loop=False \
    ++num_envs=128 \
    "+manager_env/terminations=tracking/eval" \
    "++manager_env.config.robot.type=h2" \
    "++manager_env.commands.motion.motion_lib_cfg.motion_file=data/motion_lib_h2/robot_filtered"
```

### 6.2 H2 预期评估指标

| 指标 | 推荐范围 | 说明 |
|------|---------|------|
| `success_rate` | > 0.95 | 无异常终止的完成率 |
| `mpjpe_l` | < 35 mm | 局部关节误差 |
| `mpjpe_g` | < 250 mm | 全局关节误差 |
| `waist_tracking_error` | < 0.2 | 腰部追踪（H2特有）|
| `head_roll_tracking_error` | < 0.25 | 头部roll追踪（H2特有）|

### 6.3 导出为 ONNX

```bash
# H2 ONNX 导出
python gear_sonic/eval_agent_trl.py \
    +checkpoint=<path_to_h2_checkpoint.pt> \
    +headless=True ++num_envs=1 \
    +export_onnx_only=true \
    "++manager_env.config.robot.type=h2"
```

**输出文件：**
```
exported/
├── model_encoder.onnx        # 包含 H2 编码器
├── model_decoder.onnx        # H2 解码器（31 DOF 输出）
├── model_h2.onnx            # H2 特定版本
└── observation_config.yaml   # 观测配置
```

### 6.4 部署到 H2 机器人

H2 机器人的部署与 G1 相似，但需要指定 H2 配置：

```bash
# 在 gear_sonic_deploy 中
./deploy.sh \
    --cp policy/sonic_h2/model \
    --obs-config policy/sonic_h2/observation_config.yaml \
    --embodiment h2 \
    --input-type zmq_manager \
    real
```

---

## 7. H2 vs G1 完整对比

### 7.1 模型对比

| 方面 | G1 | H2 |
|------|-----|-----|
| **自由度** | 29 | 31 |
| **追踪点** | 3个（头+两腕） | 3个（躯干+两腕） |
| **腰部控制** | 单DOF | 3DOF（roll/pitch/yaw） |
| **头部灵活性** | 2DOF | 3DOF |
| **手腕灵活性** | 2DOF/只 | 3DOF/只 |
| **运动范围** | 中等 | 更大 |
| **精密操作** | 中等 | 更好 |

### 7.2 训练对比

| 方面 | G1 | H2 |
|------|-----|-----|
| **数据准备** | 已有pipeline | ✅ 支持（需retarget） |
| **预训练权重** | ✅ 有多个版本 | ❌ 未发布 |
| **训练时间** | 100K steps | ~110K steps |
| **收敛难度** | 中等 | 稍难（维度更多） |
| **GPU需求** | 64+ | 64+ |

### 7.3 应用对比

| 应用场景 | G1 | H2 |
|---------|-----|-----|
| **通用运动** | ✅ | ✅ |
| **精细操作** | 中等 | ✅ 更好 |
| **双臂协作** | 可以 | ✅ 更精准 |
| **行走稳定性** | 好 | ✅ 相同 |
| **舞蹈/表演** | 好 | ✅ 更灵活 |

---

## 8. H2 训练快速开始

### 8.1 完整流程（假设已有SMPL数据）

```bash
# 1. 为 H2 Retarget SMPL 数据
python gear_sonic/data_process/retarget_smpl_to_h2.py \
    --input data/smpl_source \
    --output data/motion_lib_h2/smpl_h2 \
    --fps 30 --num_workers 16

# 2. 生成 H2 motion_lib
python gear_sonic/data_process/convert_smpl_to_motion_lib_h2.py \
    --input data/motion_lib_h2/smpl_h2 \
    --output data/motion_lib_h2/robot \
    --fps 30 --num_workers 16

# 3. 过滤运动
python gear_sonic/data_process/filter_and_copy_bones_data.py \
    --source data/motion_lib_h2/robot \
    --dest data/motion_lib_h2/robot_filtered \
    --embodiment h2 --workers 16

# 4. 启动训练
accelerate launch --num_processes=8 gear_sonic/train_agent_trl.py \
    +exp=manager/universal_token/all_modes/sonic_h2 \
    num_envs=4096 headless=True \
    ++manager_env.commands.motion.motion_lib_cfg.motion_file=data/motion_lib_h2/robot_filtered \
    ++manager_env.commands.motion.motion_lib_cfg.smpl_motion_file=data/motion_lib_h2/smpl_h2

# 5. 监控训练（W&B）
# 打开 https://wandb.ai 查看 TRL_H2_Track 项目

# 6. 评估
python gear_sonic/eval_agent_trl.py \
    +checkpoint=logs_rl/TRL_H2_Track/sonic_h2_*/model_step_*.pt \
    +headless=True ++eval_callbacks=im_eval

# 7. 导出 ONNX
python gear_sonic/eval_agent_trl.py \
    +checkpoint=logs_rl/TRL_H2_Track/sonic_h2_*/model_step_*.pt \
    +headless=True +export_onnx_only=true
```

### 8.2 故障排查

| 问题 | 可能原因 | 解决方案 |
|------|--------|--------|
| Retarget 失败 | SMPL 格式不匹配 | 检查 SMPL 数据结构 |
| 训练发散 | H2 关节映射错误 | 验证 motion_lib 中的关节顺序 |
| 评估崩溃 | ONNX 维度不对 | 确保导出时指定了 `type=h2` |
| 推理缓慢 | 维度增加导致计算量增加 | 预期的，可接受 |

---

## 9. 总结

### H2 相关模型清单

| 模型 | 类型 | 状态 | 位置 |
|------|------|------|------|
| SONIC H2 | 通用全身控制 | ✅ 支持（配置文件） | `sonic_h2.yaml` |
| SONIC H2（预训练） | 预训练权重 | ❌ 未发布 | - |
| Decoupled WBC H2 | 下身控制+IK | ✅ 可扩展 | 代码中有H2支持 |
| VLA-H2 | 视觉语言动作 | ✅ 可扩展 | 与VLA-SONIC相同管道 |

### 核心结论

1. **H2 是什么**：Unitree H2 是一个 31 DOF 的人形机器人，比 G1（29 DOF）更灵活
2. **目前支持**：SONIC 架构支持 H2，但预训练权重未发布
3. **如何使用**：
   - 使用 `sonic_h2.yaml` 配置从头训练
   - 需要为 H2 重新生成 motion_lib（通过 retarget）
   - 无法直接使用 G1 的预训练权重
4. **训练流程**：与 G1 相同，但数据准备阶段需要 retarget
5. **应用场景**：精细操作、复杂舞蹈、高精度任务

---

**最后更新**：2026-08-14
