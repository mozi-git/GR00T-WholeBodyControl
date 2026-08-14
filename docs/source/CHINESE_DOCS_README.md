# 中文文档指南 | Chinese Documentation Guide

## 📖 完整的中文文档已准备就绪！

我们为GR00T项目创建了详细的中文文档，涵盖整个项目的三大核心模型系统。

---

## 🚀 快速访问

所有中文文档都在 `docs/source/zh_CN/` 目录下，包括：

### 📚 核心文档（必读）

1. **[INDEX.md](zh_CN/INDEX.md)** - 中文文档总索引
   - 快速导航表
   - 按场景和知识点查找
   - 推荐阅读路径

2. **[README.md](zh_CN/README.md)** - 中文文档主入口
   - 核心模型介绍
   - 快速开始指南
   - FAQ常见问题
   - 模型对比表

3. **[models_overview.md](zh_CN/models_overview.md)** - 三大模型完整梳理 ⭐️
   - **1. 下身运动控制（Decoupled WBC）**
   - **2. 全身动作模型（SONIC）** - 包括详细的数据格式说明
   - **3. 遥操模仿学习（VLA-SONIC）** - 从数据收集到部署
   - 模型对比与总结

4. **[quick_reference.md](zh_CN/quick_reference.md)** - 快速参考卡片
   - 所有常用命令汇总
   - 配置参数速查表
   - 故障排查指南

5. **[data_formats_comparison.md](zh_CN/data_formats_comparison.md)** - 数据格式详解
   - SONIC数据格式体系
   - 与BeyondMimic的对比
   - 数据处理代码示例
   - 常见错误修复

---

## 🎯 按场景选择文档

### "我只想快速试用"（5分钟）
→ 阅读 [README.md](zh_CN/README.md#快速开始) 的快速开始部分

### "我想理解整个项目"（1小时）
→ 完整阅读 [models_overview.md](zh_CN/models_overview.md)

### "我需要查找特定命令"（实时）
→ 搜索 [quick_reference.md](zh_CN/quick_reference.md)

### "我想训练SONIC模型"（2小时）
→ 按顺序阅读：
1. [models_overview.md - 第2章](zh_CN/models_overview.md#2-全身动作模型sonic)
2. [quick_reference.md - SONIC训练章节](zh_CN/quick_reference.md#-sonic-训练)

### "我想从零收集VR数据并训练VLA"（1周）
→ 按顺序阅读：
1. [models_overview.md - 第3章](zh_CN/models_overview.md#3-遥操模仿学习模型vla-sonic)
2. [quick_reference.md - 数据收集章节](zh_CN/quick_reference.md#-数据收集遥操演示)

### "我需要理解数据格式"（1小时）
→ 完整阅读 [data_formats_comparison.md](zh_CN/data_formats_comparison.md)

### "我遇到了问题"（即时）
→ 查看 [quick_reference.md - 故障排查](zh_CN/quick_reference.md#-常见故障排查)

---

## 📊 文档内容梗概

### 中文文档覆盖了什么

✅ **三大模型的完整说明**
- 模型架构
- 预训练权重获取
- 数据格式详解
- 训练流程
- 评估方法
- 部署步骤

✅ **SONIC数据格式的深入讲解**
- motion_lib PKL格式详解
- SMPL参数规范
- 与BeyondMimic的对比
- 数据转换代码示例
- 常见错误修复

✅ **完整的工程应用指南**
- 硬件要求列表
- 网络拓扑架构图
- 环境安装步骤
- 详细的命令行示例
- 故障排查方法

✅ **实用的代码示例**
- 数据读取和验证
- 格式转换脚本
- 批量处理工具
- 参数配置范例

---

## 🔗 文档关系图

```
INDEX.md (总索引)
    ↓
README.md (快速入门)
    ├─→ models_overview.md (详细说明)
    │   ├─→ 第1章：Decoupled WBC
    │   ├─→ 第2章：SONIC
    │   │   ├─→ 查看数据格式 → data_formats_comparison.md
    │   │   ├─→ 查看命令 → quick_reference.md
    │   │   └─→ 查看故障 → quick_reference.md
    │   └─→ 第3章：VLA-SONIC
    │       ├─→ 查看命令 → quick_reference.md
    │       └─→ 查看故障 → quick_reference.md
    │
    ├─→ quick_reference.md (快速查询)
    │   ├─→ 模型下载
    │   ├─→ 训练命令
    │   ├─→ 部署方法
    │   ├─→ 故障排查
    │   └─→ 文件路径
    │
    └─→ data_formats_comparison.md (数据格式)
        ├─→ 格式详解
        ├─→ 模型对比
        ├─→ 代码示例
        └─→ 错误修复
```

---

## 📈 文档统计

| 文档 | 长度 | 阅读时间 | 适用人群 |
|------|------|---------|--------|
| README.md | ~3000字 | 5-10分钟 | 所有人 |
| models_overview.md | ~20000字 | 30-60分钟 | 深度用户 |
| quick_reference.md | ~5000字 | 查询用 | 开发者 |
| data_formats_comparison.md | ~8000字 | 20-40分钟 | 数据工程师 |
| **总计** | ~36000字 | ~2小时 | - |

---

## 🎓 使用建议

### 第一次使用
1. 花5分钟阅读 [README.md](zh_CN/README.md)
2. 根据场景选择对应文档
3. 按照步骤执行

### 日常开发
1. 使用 [quick_reference.md](zh_CN/quick_reference.md) 查询命令
2. 根据需要参考 [models_overview.md](zh_CN/models_overview.md)
3. 遇到问题查看"故障排查"

### 深度学习
1. 完整阅读 [models_overview.md](zh_CN/models_overview.md)
2. 学习 [data_formats_comparison.md](zh_CN/data_formats_comparison.md)
3. 参考官方英文文档进行补充

---

## 🔑 关键知识点概览

### 三大模型一句话总结

1. **Decoupled WBC** - 机器人下身的强化学习控制器
2. **SONIC** - 学习人类动作的全身运动基础模型
3. **VLA-SONIC** - 从VR演示数据学习任务的视觉-语言-动作模型

### 核心概念速查

| 概念 | 说明 | 文档位置 |
|------|------|---------|
| motion_lib PKL | SONIC的训练数据格式 | data_formats_comparison.md § 1.1 |
| SMPL | 参数化人体模型 | data_formats_comparison.md § 1.2 |
| FSQ | 有限标量量化，用于生成64维潜在令牌 | models_overview.md § 2.1 |
| LeRobot | HuggingFace的机器人数据集格式 | models_overview.md § 3.4 |
| 多模态编码器 | SONIC支持4种输入类型的编码器 | models_overview.md § 2.1 |

---

## ❓ 快速问答

**Q: 中文文档与英文官方文档的区别是什么？**
A: 中文文档聚焦于三大模型的完整梳理、详细的数据格式说明和实操步骤。英文官方文档涵盖更多API细节。两者互补使用最佳。

**Q: 我应该从哪个文档开始？**
A: 从 [INDEX.md](zh_CN/INDEX.md) 开始，它会根据你的场景推荐合适的文档。

**Q: 文档多久更新一次？**
A: 主要版本发布时更新。当前版本是基于SONIC v1.1的。

**Q: 如何报告文档错误？**
A: 通过 gear-wbc@nvidia.com 反馈，或在GitHub上提交issue。

---

## 📚 完整文档列表

```
docs/source/zh_CN/
├── INDEX.md                          # 📍 总索引（从这里开始！）
├── README.md                         # 📖 主导航文档
├── models_overview.md               # 🎯 三大模型完整梳理（核心）
├── quick_reference.md               # ⚡ 快速参考卡片
├── data_formats_comparison.md       # 📊 数据格式详解
└── 本文件 (CHINESE_DOCS_README.md)
```

---

## 🌟 特色内容

### 在models_overview.md中
- ✨ 详细的npz与motion_lib格式对比
- ✨ 与BeyondMimic的技术对比
- ✨ 完整的硬件和网络拓扑说明
- ✨ 从零开始的VLA工作流

### 在quick_reference.md中
- ✨ 所有常用命令（复制即用）
- ✨ 训练参数速查表
- ✨ 故障排查决策树
- ✨ 文件路径快速导航

### 在data_formats_comparison.md中
- ✨ PKL格式的完整字段说明
- ✨ SMPL参数的详细规范
- ✨ NPZ→PKL转换代码
- ✨ 数据验证和重采样脚本

---

## 🚀 立即开始

### 选项1：5分钟快速了解
```bash
# 读这个文件的"快速访问"部分
# 然后打开 zh_CN/README.md
```

### 选项2：完整学习（1-2小时）
```bash
# 1. 打开 zh_CN/INDEX.md
# 2. 选择推荐路径
# 3. 按顺序阅读文档
```

### 选项3：快速查询（实时）
```bash
# 打开 zh_CN/quick_reference.md
# 使用 Ctrl+F 搜索关键词
```

---

## 📞 需要帮助？

- **找不到某个信息**：使用 INDEX.md 的按知识点查找功能
- **需要查看命令**：打开 quick_reference.md，Ctrl+F搜索
- **需要理解概念**：查阅 models_overview.md 对应章节
- **遇到错误**：查看相应章节的"故障排查"部分
- **想要官方支持**：gear-wbc@nvidia.com

---

**中文文档总结**：6份文档，36000字，涵盖SONIC模型的所有方面 📚

**推荐阅读顺序**：INDEX.md → README.md → models_overview.md/quick_reference.md

**最后更新**：2026-08-14

---

现在就开始阅读中文文档吧！👉 [打开INDEX.md](zh_CN/INDEX.md)
