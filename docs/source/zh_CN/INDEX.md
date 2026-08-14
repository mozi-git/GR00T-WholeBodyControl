# 📚 GR00T 中文文档索引

欢迎使用GR00T-WholeBodyControl项目的中文文档。本索引帮助你快速找到所需的信息。

---

## 🎯 按使用场景快速导航

### "我想快速上手"
→ 阅读 **[README.md](README.md)** 的"快速开始"部分（5分钟）

### "我需要理解整个项目架构"
→ 阅读 **[models_overview.md](models_overview.md)** 的"总结对比表"（10分钟）

### "我想训练SONIC模型"
→ 阅读 **[models_overview.md](models_overview.md)** 的第2章"全身动作模型(SONIC)" (30分钟)

### "我想从零收集VR演示数据"
→ 阅读 **[models_overview.md](models_overview.md)** 的第3章"遥操模仿学习(VLA-SONIC)" (45分钟)

### "我需要查看具体命令"
→ 查阅 **[quick_reference.md](quick_reference.md)** (快速查询)

### "我需要理解数据格式"
→ 阅读 **[data_formats_comparison.md](data_formats_comparison.md)** (深入理解)

### "我遇到了错误"
→ 查看对应章节的"故障排查"部分，或查阅 **[quick_reference.md](quick_reference.md)** 的"常见故障排查"

---

## 📖 文档详细说明

### 1. [README.md](README.md) - 主导航文档
**用途**：中文文档的主入口  
**内容**：
- 核心文档导航
- 快速开始（3种场景）
- 关键配置速查表
- 模型对比表
- FAQ常见问题

**阅读时间**：5-10分钟  
**适合人群**：第一次接触GR00T项目的用户

---

### 2. [models_overview.md](models_overview.md) - 完整系统梳理
**用途**：深入理解三大模型的完整文档  
**内容**：

#### 第1章：下身运动控制（Decoupled WBC）
- 模型架构与原理
- 预训练模型获取
- 完整训练流程
- 数据格式
- 部署方法
- 评估指标

#### 第2章：全身动作模型（SONIC）
- 模型概述与特点
- 三个官方版本对比
- **详细数据格式说明**
  - motion_lib PKL格式
  - SMPL参数规范
  - 与BeyondMimic的区别
  - 数据过滤规则
- 完整训练流程（数据准备→训练→评估）
- ONNX导出与C++部署
- 实时监控指标

#### 第3章：遥操模仿学习（VLA-SONIC）
- 硬件要求详细列表
- 网络拓扑架构图
- 完整数据收集流程
- LeRobot数据集格式
- VLA微调命令
- 推理部署与验证
- 故障排查指南

#### 总结部分
- 三模型对比表
- 快速开始检查清单
- 常见问题解答

**阅读时间**：30-60分钟（全部）或按章节选读（10-20分钟/章）  
**适合人群**：
- 需要微调模型的用户
- 需要理解数据流的用户
- 需要完整部署的用户

---

### 3. [quick_reference.md](quick_reference.md) - 快速参考卡片
**用途**：查询具体命令和配置参数  
**内容**：
- 模型下载命令
- 快速启动命令（仿真/真实机器人）
- SONIC完整训练工作流
- 评估和导出命令
- 数据收集步骤
- VLA微调与推理
- 常见故障排查表
- 文件路径速查
- 关键概念解释

**查询方式**：
- 使用Ctrl+F搜索关键词
- 按章节浏览
- 参考对应的"快速查询表"

**阅读时间**：查询时间（通常1-5分钟/条目）  
**适合人群**：已了解基础，需要快速查询命令的用户

---

### 4. [h2_models_guide.md](h2_models_guide.md) - Unitree H2 完整指南
**用途**：针对Unitree H2机器人的SONIC模型说明  
**内容**：
- H2硬件规格对比（31 DOF vs G1的29 DOF）
- SONIC H2配置详解
- H2的关节映射（32个body）
- 数据准备（SMPL→H2 retarget）
- 训练指南（从头训练）
- 评估与部署
- G1↔H2完整对比

**阅读时间**：30-40分钟  
**适合人群**：使用Unitree H2机器人的用户

---

### 5. [data_formats_comparison.md](data_formats_comparison.md) - 数据格式详解
**用途**：深入理解SONIC数据格式和格式转换  
**内容**：

#### 第1章：SONIC数据格式体系
- motion_lib PKL格式详解
- 单个文件内容说明
- G1关节映射（29个关节顺序）
- SMPL字段说明
- G1运动参考格式
- VR遥操格式
- SOMA骨架格式

#### 第2章：SONIC vs BeyondMimic对比
- 核心差异对照表
- 输入数据格式对比
- 数据准备流程对比
- 技术栈对比

#### 第3章：实际工作示例
- 读取和验证PKL文件的Python代码
- 将NPZ转换为PKL的转换函数
- 批量验证数据集的脚本
- 从SMPL生成motion_lib的代码
- 数据重采样函数

#### 第4章：存储成本
- 单个运动的大小估计
- 完整数据集的存储成本
- 存储优化建议

#### 第5章：常见错误修复
- 维度不匹配错误
- 四元数未归一化
- 轴角与四元数混淆
- 帧率不一致

**阅读时间**：20-40分钟（全部）或按需查阅  
**适合人群**：
- 需要理解数据格式的开发者
- 需要进行数据预处理的用户
- 需要调试数据问题的用户

---

## 🔍 按知识点查找

### 模型相关
- **想了解三个模型的区别**
  → [models_overview.md - 总结对比表](models_overview.md#总结对比表)
  → [quick_reference.md - 模型对比速查表](quick_reference.md)

- **想知道SONIC与BeyondMimic的区别**
  → [data_formats_comparison.md - 第2章](data_formats_comparison.md#2-sonic-vs-beyondmimic-对比)

### 数据相关
- **想理解SONIC的数据格式**
  → [models_overview.md - 2.3 SONIC的数据格式](models_overview.md#23-sonic-的数据格式)
  → [data_formats_comparison.md - 第1章](data_formats_comparison.md#1-sonic-数据格式体系)

- **想知道NPZ和PKL的区别**
  → [data_formats_comparison.md - 2.2 输入数据格式对比](data_formats_comparison.md#22-输入数据格式对比)

- **想看数据处理代码示例**
  → [data_formats_comparison.md - 第3章](data_formats_comparison.md#3-实际工作中的数据处理示例)

### 训练相关
- **想从头训练SONIC**
  → [models_overview.md - 2.4 SONIC训练流程](models_overview.md#24-sonic-训练流程)
  → [quick_reference.md - SONIC训练](quick_reference.md#-sonic-训练)

- **想微调预训练模型**
  → [models_overview.md - 2.4.3 训练命令](models_overview.md#243-训练命令)
  → [quick_reference.md - 微调预训练模型](quick_reference.md#微调预训练模型)

- **想进行小规模测试**
  → [models_overview.md - 2.4.3 小规模调试](models_overview.md#243-训练命令)
  → [quick_reference.md - 小规模调试](quick_reference.md#小规模调试)

### 部署相关
- **想部署到真实机器人**
  → [models_overview.md - 2.6 SONIC导出与部署](models_overview.md#26-sonic-导出与部署)
  → [quick_reference.md - 真实机器人部署](quick_reference.md#真实机器人部署)

- **想在仿真环境测试**
  → [README.md - 快速开始](README.md#快速开始)
  → [quick_reference.md - 仿真测试](quick_reference.md#仿真测试无硬件)

### 数据收集相关
- **想收集VR遥操演示**
  → [models_overview.md - 3.3 数据收集流程](models_overview.md#33-数据收集流程)
  → [quick_reference.md - 数据收集](quick_reference.md#-数据收集遥操演示)

- **想验证收集的数据**
  → [models_overview.md - 3.4 数据处理与验证](models_overview.md#34-数据处理与验证)

### VLA相关
- **想微调VLA模型**
  → [models_overview.md - 3.5 VLA模型训练](models_overview.md#35-vla-模型训练)
  → [quick_reference.md - VLA微调](quick_reference.md#vla-微调与推理)

- **想进行VLA推理**
  → [models_overview.md - 3.6 VLA推理与部署](models_overview.md#36-vla-推理与部署)

### 故障排查相关
- **想排查数据问题**
  → [data_formats_comparison.md - 第5章](data_formats_comparison.md#5-常见数据格式错误及修复)

- **想排查训练问题**
  → [quick_reference.md - 常见故障排查](quick_reference.md#-常见故障排查)
  → [models_overview.md - 3.7 部署验证与测试](models_overview.md#37-部署验证与测试)

---

## ⏱️ 推荐阅读路径

### 路径1：快速体验（30分钟）
1. [README.md - 快速开始场景1](README.md#场景1只想用预训练sonic模型)
2. [quick_reference.md - 快速启动](quick_reference.md#-快速启动)
3. 运行命令体验模型

### 路径2：微调预训练模型（2小时）
1. [README.md](README.md) - 了解全貌
2. [models_overview.md - 第2章](models_overview.md#2-全身动作模型sonic) - 理解SONIC
3. [data_formats_comparison.md](data_formats_comparison.md) - 理解数据格式
4. [quick_reference.md - SONIC训练](quick_reference.md#-sonic-训练) - 获取命令
5. 开始训练

### 路径3：完整VLA工作流（1周）
1. [README.md](README.md) - 了解全貌
2. [models_overview.md - 第3章](models_overview.md#3-遥操模仿学习模型vla-sonic) - 理解VLA系统
3. [quick_reference.md](quick_reference.md) - 查询具体命令
4. 准备硬件和环境
5. 收集演示数据
6. 微调VLA模型
7. 部署验证

### 路径4：深度理解项目（3小时）
1. [models_overview.md](models_overview.md) - 读整个文档
2. [data_formats_comparison.md](data_formats_comparison.md) - 理解数据层面
3. 参考论文和官方文档

---

## 🆘 遇到问题时

### 我找不到某个信息
→ 使用Ctrl+F在 [quick_reference.md](quick_reference.md) 中搜索关键词

### 我需要某个特定命令
→ 查阅 [quick_reference.md](quick_reference.md)

### 我的训练/推理出问题了
→ 查阅对应章节的"故障排查"或搜索 [quick_reference.md - 常见故障排查](quick_reference.md#-常见故障排查)

### 我需要理解数据格式
→ 阅读 [data_formats_comparison.md](data_formats_comparison.md)

### 我需要完整的流程说明
→ 阅读 [models_overview.md](models_overview.md)

### 以上都找不到答案
→ 参考官方文档：https://nvlabs.github.io/GR00T-WholeBodyControl/  
→ 联系支持：gear-wbc@nvidia.com

---

## 📋 文档维护信息

| 文档 | 最后更新 | 适用版本 | 维护状态 |
|------|---------|---------|--------|
| README.md | 2026-08-14 | SONIC v1.1+ | 活跃 |
| models_overview.md | 2026-08-14 | SONIC v1.1+ | 活跃 |
| quick_reference.md | 2026-08-14 | SONIC v1.1+ | 活跃 |
| data_formats_comparison.md | 2026-08-14 | SONIC v1.1+ | 活跃 |

---

## 💡 使用建议

1. **第一次接触**：从[README.md](README.md)开始，5-10分钟快速了解
2. **准备工作**：根据场景选择相应路径，准备环境和数据
3. **具体操作**：查阅[quick_reference.md](quick_reference.md)获取命令
4. **遇到问题**：搜索关键词或查看故障排查部分
5. **深度学习**：阅读[models_overview.md](models_overview.md)和[data_formats_comparison.md](data_formats_comparison.md)

---

## 🔗 相关资源

- **官方英文文档**：https://nvlabs.github.io/GR00T-WholeBodyControl/
- **SONIC论文**：https://arxiv.org/abs/2511.07820
- **HuggingFace模型**：https://huggingface.co/nvidia/GEAR-SONIC
- **Bones-SEED数据集**：https://huggingface.co/datasets/bones-studio/seed
- **项目GitHub**：https://github.com/NVlabs/GR00T-WholeBodyControl
- **支持邮箱**：gear-wbc@nvidia.com

---

**更新日期**：2026-08-14  
**文档版本**：v1.0  
**维护者**：GR00T团队
