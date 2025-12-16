# 词根聚类需求挖掘系统

## 📋 项目简介

这是一个基于语义聚类的需求挖掘方法论系统，用于从英文单词种子（word roots）发现产品机会方向。

**核心理念**：从单词 → 短语 → 语义簇 → 需求方向 → MVP验证

---

## 🚀 快速开始

### 第一次使用（3步上手）

1. **阅读快速指南**
   ```bash
   打开：docs/04_快速开始指南.md
   ```

2. **运行聚类分析**
   ```bash
   cd scripts
   python step_A3_clustering.py
   ```

3. **查看质量报告**
   ```bash
   python cluster_stats.py
   ```

---

## 📁 项目结构

```
词根聚类需求挖掘/
│
├── 📂 scripts/              # 可执行脚本
│   ├── step_A2_merge_csv.py      # 合并CSV文件
│   ├── step_A3_clustering.py     # 聚类分析（核心）
│   ├── cluster_stats.py          # 结果统计分析
│   ├── validation.py             # 字段验证工具
│   ├── config.py                 # 全局配置
│   └── utils.py                  # 工具函数
│
├── 📂 docs/                 # 方法论文档
│   ├── 01_需求挖掘方法论.md       # 完整方法论（必读）
│   ├── 02_字段命名规范.md         # 字段命名标准
│   ├── 03_实施优先级指南.md       # Phase 1/2/3规划
│   ├── 04_快速开始指南.md         # 新手教程
│   │
│   ├── 📂 tutorials/        # 操作教程
│   │   ├── step_A2_使用说明.md
│   │   └── step_A3_使用说明.md
│   │
│   ├── 📂 analysis/         # 历史分析记录
│   │   ├── 第一次聚类分析.md
│   │   ├── GPT原始反馈.md
│   │   ├── GPT反馈总结.md
│   │   └── 修复记录.md
│   │
│   └── 📂 technical/        # 技术文档
│       ├── 聚类原理讲解.md
│       └── 长度影响分析.md
│
├── 📂 data/                 # 数据文件
│   ├── merged_keywords_all.csv
│   ├── stageA_clusters.csv
│   └── cluster_summary_A3.csv
│
└── 📂 output/               # 输出结果
```

---

## 📖 文档导航

### ⭐⭐⭐ 必读（开始前）

1. **[需求挖掘方法论](docs/01_需求挖掘方法论.md)** - 完整的A1-A5, B1-B8流程
2. **[实施优先级指南](docs/03_实施优先级指南.md)** - Phase 1/2/3分阶段计划
3. **[字段命名规范](docs/02_字段命名规范.md)** - CSV字段标准

### ⭐⭐ 重要（第一次使用）

4. **[快速开始指南](docs/04_快速开始指南.md)** - 快速上手教程
5. **[step_A3使用说明](docs/tutorials/step_A3_使用说明.md)** - 聚类脚本教程

### ⭐ 可选（深入理解）

6. **[聚类原理讲解](docs/technical/聚类原理讲解.md)** - HDBSCAN算法原理
7. **[GPT反馈总结](docs/analysis/GPT反馈总结.md)** - GPT的方法论反馈

---

## 🎯 使用场景指南

### 场景1：我想运行聚类分析

```bash
# Step 1: 查看配置
cd scripts
cat config.py

# Step 2: 运行聚类
python step_A3_clustering.py

# Step 3: 分析结果质量
python cluster_stats.py

# Step 4: 验证字段规范
python validation.py
```

**预期结果**：
- 生成 `data/stageA_clusters.csv`（带簇标签的短语）
- 生成 `data/cluster_summary_A3.csv`（簇级汇总）
- 簇数量：60-100个
- 噪音比例：15-25%

---

### 场景2：我想了解完整方法论

```
阅读顺序：
1. docs/01_需求挖掘方法论.md（完整流程）
2. docs/03_实施优先级指南.md（分阶段实施）
3. docs/02_字段命名规范.md（开发规范）
```

---

### 场景3：我想开发新功能

```
参考文档：
1. docs/02_字段命名规范.md（必读）
2. docs/03_实施优先级指南.md（了解Phase）
3. scripts/step_A3_clustering.py（代码示例）
4. scripts/config.py（配置规范）
```

---

## 🔧 核心工具说明

### 1. step_A3_clustering.py（核心聚类脚本）

**功能**：对短语进行语义聚类

**输入**：`data/merged_keywords_all.csv`

**输出**：
- `data/stageA_clusters.csv`（短语级，带cluster_id）
- `data/cluster_summary_A3.csv`（簇级汇总）

**关键参数**（在config.py中配置）：
- `min_cluster_size`: 15（最小簇大小）
- `min_samples`: 3（最小邻居数）

---

### 2. cluster_stats.py（质量分析工具）

**功能**：分析聚类结果质量，提供调优建议

**使用**：
```bash
cd scripts
python cluster_stats.py
```

**输出**：
- ✅ 簇数量是否合理（60-100）
- ✅ 噪音比例是否合理（<25%）
- ✅ 簇大小分布统计
- 💡 参数调优建议

---

### 3. validation.py（字段验证工具）

**功能**：验证CSV文件是否符合字段命名规范

**使用**：
```bash
cd scripts
python validation.py
```

**检查**：
- 必需字段是否存在
- 字段名是否符合规范
- 是否有冗余字段

---

## ⚙️ 配置说明

所有配置在 `scripts/config.py` 中管理：

```python
A3_CONFIG = {
    "min_cluster_size": 15,  # 最小簇大小
    "min_samples": 3,        # 最小邻居数
    "embedding_model": "all-MiniLM-L6-v2",  # Embedding模型
    "clustering_method": "hdbscan",  # 聚类算法
}
```

**参数调优指南**：
- 簇太多（>100）→ 增大 `min_cluster_size` 到 20-25
- 簇太少（<40）→ 减小 `min_cluster_size` 到 10-12
- 噪音太多（>30%）→ 考虑按seed_group分组聚类

---

## 📊 数据流程图

```
种子词（seed_words）
    ↓
[A1] 种子词准备
    ↓
[A2] 扩展短语（影刀RPA/手动）
    ↓
data/merged_keywords_all.csv
    ↓
[A3] 语义聚类 ← step_A3_clustering.py
    ↓
data/stageA_clusters.csv（带cluster_id）
    ↓
cluster_stats.py → 质量报告
    ↓
[A5] 人工筛选方向（5-10个）
    ↓
data/direction_keywords.csv
    ↓
[B1] 方向扩展
    ↓
[B3] 方向内聚类
    ↓
[B6] 需求分析
    ↓
MVP实验
```

---

## 🚨 常见问题

### Q1: 聚类结果簇太多（>100个）怎么办？

**解决方案**：
```python
# 修改 scripts/config.py
A3_CONFIG = {
    "min_cluster_size": 20,  # 从15改为20
    "min_samples": 3,
}
```

然后重新运行：
```bash
cd scripts
python step_A3_clustering.py
```

---

### Q2: 噪音点比例很高（>40%）正常吗？

**回答**：如果使用了46个跨度很大的种子词，40-60%的噪音是正常的。

**关键问题**：56个有效簇的质量如何？

**验证方法**：
1. 运行 `python cluster_stats.py`
2. 查看 Top 10 最大的簇
3. 人工审查 `data/cluster_summary_A3.csv`
4. 如果能找到5-10个清晰的方向 → 成功

---

### Q3: 如何人工筛选方向？

**推荐流程**（轻量版）：
1. 打开 `data/cluster_summary_A3.csv`
2. 查看 `seed_words_in_cluster` 列
3. 人工挑选5-10个语义清晰的簇
4. 手动创建 `data/direction_keywords.csv`
5. 进入阶段B

**完整版**：参考 `docs/01_需求挖掘方法论.md` 的A4-A5步骤

---

## 📚 学习路径

### 新手路径（1-2小时）

```
1. 阅读：docs/04_快速开始指南.md（10分钟）
2. 阅读：docs/tutorials/step_A3_使用说明.md（10分钟）
3. 运行：python scripts/step_A3_clustering.py（20分钟）
4. 分析：python scripts/cluster_stats.py（5分钟）
5. 人工筛选：从cluster_summary_A3.csv挑5个方向（30分钟）
```

### 深入理解路径（半天）

```
1. 完整方法论：docs/01_需求挖掘方法论.md（1小时）
2. 实施规划：docs/03_实施优先级指南.md（30分钟）
3. 技术原理：docs/technical/聚类原理讲解.md（30分钟）
4. 字段规范：docs/02_字段命名规范.md（20分钟）
5. 历史总结：docs/analysis/GPT反馈总结.md（30分钟）
```

---

## 🎯 核心原则

### 1. 只分组，不删除

系统提供视图，人工做决策。

- ✅ A3聚类：只分组，不过滤
- ✅ A5筛选：标记low priority，不删除
- ✅ 噪音点：保留，人工决定是否使用

### 2. 轻量版起步，避免复杂度压垮

- Phase 1（必须）：A2 → A3 → 人工筛选
- Phase 2（重要）：B1 → B3 → B6
- Phase 3（可选）：大模型 + Trends + 需求库

### 3. 大模型输出是假设，不是事实

- A4的簇解释：需要SERP验证
- B3的5维框架：需要访谈验证
- 决策优先级：SERP+访谈 > BI > 经验 > 模型

---

## 🔗 相关资源

- **HDBSCAN官方文档**: https://hdbscan.readthedocs.io/
- **Sentence Transformers**: https://www.sbert.net/
- **影刀RPA**: https://www.yingdao.com/

---

## 📝 更新日志

### 2025-12-15
- ✅ 项目结构重组（代码与文档分离）
- ✅ 创建6个核心脚本（scripts目录）
- ✅ 整理4类文档（方法论、教程、分析、技术）
- ✅ 优化聚类参数（248簇 → 56簇）
- ✅ 创建质量分析工具（cluster_stats.py）
- ✅ 创建字段验证工具（validation.py）

---

## 💬 需要帮助？

- **快速问题**：查看 `docs/04_快速开始指南.md`
- **方法论问题**：查看 `docs/01_需求挖掘方法论.md`
- **技术问题**：查看 `docs/technical/`
- **历史参考**：查看 `docs/analysis/`

---

**开始使用**：`docs/04_快速开始指南.md`

**祝你挖掘出好需求！** 🚀
