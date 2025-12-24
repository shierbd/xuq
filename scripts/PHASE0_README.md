# Phase 0 基线测量脚本使用说明

## 📋 概述

Phase 0 包含4个实验脚本和1个报告生成器，用于测量当前系统的基线能力，为后续优化提供证据支持。

## 🎯 实验目标

| 实验 | 脚本文件 | 测量目标 | 判断标准 |
|------|---------|---------|---------|
| **实验A** | `phase0_experiment_a_cluster_review.py` | 聚类审核效率 | <60min且遗漏率<10%=ok；>120min或遗漏率>30%=need optimization |
| **实验B** | `phase0_experiment_b_token_coverage.py` | Token覆盖率 | ≥80%=sufficient；≤60%=need expansion |
| **实验C** | `phase0_experiment_c_redundancy.py` | 同义冗余率 | <10%=ok；>20%=need canonicalization |
| **实验D** | `phase0_experiment_d_intent_distribution.py` | 搜索意图分布 | find_tool>70%=similar to Jun Yan |
| **报告生成** | `phase0_generate_baseline_report.py` | 聚合结果，生成建议 | - |

## 🚀 使用流程

### 1. 按顺序运行4个实验

```bash
# 实验A：聚类审核效率（交互式，需要人工审核簇）
python scripts/phase0_experiment_a_cluster_review.py

# 实验B：Token覆盖率（自动化）
python scripts/phase0_experiment_b_token_coverage.py

# 实验C：同义冗余率（交互式，需要人工标注）
python scripts/phase0_experiment_c_redundancy.py

# 实验D：搜索意图分布（交互式，需要人工标注）
python scripts/phase0_experiment_d_intent_distribution.py
```

### 2. 生成基线报告

```bash
# 聚合所有实验结果，生成最终报告
python scripts/phase0_generate_baseline_report.py
```

## 📊 输出文件

### 实验结果 (JSON格式)

所有实验结果保存在 `data/phase0_results/` 目录：

```
data/phase0_results/
├── experiment_a_result.json  # 实验A结果
├── experiment_b_result.json  # 实验B结果
├── experiment_c_result.json  # 实验C结果
└── experiment_d_result.json  # 实验D结果
```

### 基线报告 (Markdown格式)

最终报告保存在 `docs/` 目录：

```
docs/英文关键词系统基线报告-20251223.md
```

报告包含：
- 执行摘要
- 核心发现
- 优先级建议
- 实验结果详情
- 优化建议详情
- 实施时间线

## 📝 实验说明

### 实验A：聚类审核效率

**操作说明**：
1. 系统会依次显示每个聚类簇的摘要（前10个短语）
2. 判断是否值得深入分析
3. 操作：
   - 输入 `s` 选中该簇
   - 按 `Enter` 跳过
   - 输入 `q` 完成审核
4. 完成后输入主观感受（easy/medium/hard）
5. 最后检查是否有遗漏的重要簇

**评估维度**：
- 簇大小是否合理
- 短语主题是否清晰
- 商业价值潜力
- 是否值得进一步拆分

### 实验B：Token覆盖率

**全自动运行**，无需交互。

**测量内容**：
- 当前26个token覆盖了多少短语
- 每个token的使用频率
- 未覆盖短语的高频词分析

### 实验C：同义冗余率

**操作说明**：
1. 系统随机抽样1000条短语
2. 依次显示每个短语
3. 判断是否与之前某个短语同义
4. 操作：
   - 如果同义：输入那个短语的编号（如 `5`）
   - 如果不同义：直接按 `Enter`
   - 退出：输入 `q`

**同义判断标准**：
- ✅ 同义："best calculator" 和 "calculator best"（词序不同）
- ✅ 同义："image compressor" 和 "compress image"（词形变化）
- ❌ 不同义："best calculator" 和 "free calculator"（意图不同）

### 实验D：搜索意图分布

**操作说明**：
1. 系统随机抽样1000条短语
2. 依次显示每个短语
3. 选择一个最匹配的意图类别
4. 操作：
   - 输入数字 `1-6` 选择意图
   - 输入 `s` 显示分类指南
   - 输入 `q` 退出

**意图类别**：
1. `find_tool` - 寻找工具/服务
2. `learn_how` - 学习使用/教程
3. `solve_problem` - 解决问题
4. `find_free` - 寻找免费
5. `compare` - 对比评估
6. `other` - 其他

## 🎯 决策逻辑

报告生成器会根据实验结果自动生成优化建议：

### Phase 1: 聚类质量评分
- **触发条件**: 实验A结果为 `need_optimization`
- **行动**: 实施聚类质量评分算法、LLM预评估

### Phase 2.1: 词级规范化去重
- **触发条件**: 实验C冗余率 > 20%
- **行动**: 实施词级规范化算法，仅去除articles

### Phase 2.2: 模板-变量迭代扩展
- **触发条件**: 实验B覆盖率 < 60%
- **行动**: 扩展token词库到200-500个

### Phase 3: 搜索意图分类框架
- **触发条件**: 实验D find_tool占比 > 70%
- **行动**: 实施意图分类框架，采用君言式分类体系

## ⚠️ 注意事项

1. **数据库要求**：确保数据库中已有Phase 1和Phase 2的聚类结果
2. **时间预估**：
   - 实验A：30-120分钟（取决于簇数量）
   - 实验B：5-10分钟（自动）
   - 实验C：30-60分钟（1000条标注）
   - 实验D：30-60分钟（1000条标注）
3. **交互式实验**：实验A、C、D需要人工标注，建议集中时间完成
4. **结果复现**：实验使用固定随机种子，可以重复运行得到相同结果

## 📌 下一步

完成Phase 0后，根据基线报告中的**高优先级建议**开始实施优化：

1. 查看报告中的"优先级建议"部分
2. 确定哪些优化是必需的（🔴 高优先级）
3. 按照"实施时间线"开始Phase 1-3的开发

---

**创建日期**: 2025-12-23
**Phase 0状态**: 完成 ✅
