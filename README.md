# 词根聚类需求挖掘系统

## 📋 项目简介

这是一个基于语义聚类的需求挖掘方法论系统，用于从英文单词种子（word roots）发现产品机会方向。

**核心理念**：从单词 → 短语 → 语义簇 → 需求方向 → MVP验证

---

## 🚀 快速开始

### 安装依赖

```bash
# 安装完整依赖
pip install -r requirements.txt

# 或只安装核心依赖（仅A2/A3步骤）
pip install -r scripts/requirements_minimal.txt
```

### 第一次使用（3步上手）

1. **验证项目结构**
   ```bash
   python verify_structure.py
   ```

2. **运行聚类分析**
   ```bash
   cd scripts
   python -m core.step_A3_clustering
   ```

3. **查看质量报告**
   ```bash
   python -m tools.cluster_stats
   ```

---

## 📁 项目结构（重构后）

```
词根聚类需求挖掘/
│
├── 📂 scripts/               # 所有Python脚本
│   ├── core/                 # 核心流程脚本
│   │   ├── step_A2_merge_csv.py      # A2：合并CSV文件
│   │   ├── step_A3_clustering.py     # A3：语义聚类（核心）
│   │   └── step_B3_cluster_stageB.py # B3：方向内聚类
│   │
│   ├── tools/                # 工具脚本
│   │   ├── cluster_stats.py          # 聚类统计分析
│   │   ├── validation.py             # 字段验证
│   │   ├── generate_html_viewer.py   # HTML查看器生成
│   │   └── plot_clusters.py          # 聚类可视化
│   │
│   ├── selectors/            # 方向选择器
│   │   ├── manual_direction_selector.py  # 交互式方向筛选
│   │   └── auto_select_directions.py     # 自动方向选择（测试用）
│   │
│   └── lib/                  # 共享库
│       ├── config.py         # 全局配置
│       └── utils.py          # 工具函数
│
├── 📂 data/                  # 数据目录
│   ├── raw/                  # 原始数据（A2输出）
│   │   └── merged_keywords_all.csv
│   ├── processed/            # 处理后的数据（A3, B3输出）
│   │   ├── stageA_clusters.csv
│   │   └── stageB_clusters.csv
│   ├── results/              # 最终结果（汇总统计）
│   │   ├── cluster_summary_A3.csv
│   │   ├── cluster_summary_B3.csv
│   │   └── direction_keywords.csv
│   └── baseline/             # 基准输出（用于回归测试）
│       └── BASELINE_METRICS.md
│
├── 📂 docs/                  # 文档
│   ├── README.md             # 文档导航
│   ├── 01_需求挖掘方法论.md    # 完整方法论（必读）
│   ├── 02_字段命名规范.md      # 字段命名标准
│   ├── 03_实施优先级指南.md    # Phase 1/2/3规划
│   ├── 04_快速开始指南.md      # 新手教程
│   │
│   ├── tutorials/            # 操作教程
│   │   ├── step_A2_使用说明.md
│   │   └── step_A3_使用说明.md
│   │
│   ├── guides/               # 工具指南
│   │   └── 05_HTML查看器使用说明.md
│   │
│   ├── technical/            # 技术文档
│   │   ├── 聚类原理讲解.md
│   │   └── 长度影响分析.md
│   │
│   ├── analysis/             # 分析记录
│   │   ├── 第一次聚类分析.md
│   │   ├── GPT原始反馈.md
│   │   └── 修复记录.md
│   │
│   └── history/              # 历史文档（归档）
│
├── 📂 output/                # HTML查看器输出
│
├── README.md                 # 本文件
├── CONTRIBUTING.md           # 开发者指南
├── CHANGELOG.md              # 更新日志
├── requirements.txt          # Python依赖
├── verify_structure.py       # 项目结构验证脚本
└── .gitignore                # Git忽略规则
```

---

## 📖 文档导航

### ⭐⭐⭐ 必读（开始前）

1. **[需求挖掘方法论](docs/01_需求挖掘方法论.md)** - 完整的A1-A5, B1-B8流程
2. **[实施优先级指南](docs/03_实施优先级指南.md)** - Phase 1/2/3分阶段计划
3. **[快速开始指南](docs/04_快速开始指南.md)** - 快速上手教程

### ⭐⭐ 重要（第一次使用）

4. **[字段命名规范](docs/02_字段命名规范.md)** - CSV字段标准
5. **[step_A3使用说明](docs/tutorials/step_A3_使用说明.md)** - 聚类脚本教程

### ⭐ 可选（深入理解）

6. **[聚类原理讲解](docs/technical/聚类原理讲解.md)** - HDBSCAN算法原理
7. **[开发者指南](CONTRIBUTING.md)** - 项目开发规范

---

## 🎯 使用场景指南

### 场景1：我想运行聚类分析

```bash
# Step 1: 查看配置
cd scripts
cat lib/config.py

# Step 2: 运行聚类
python -m core.step_A3_clustering

# Step 3: 分析结果质量
python -m tools.cluster_stats

# Step 4: 验证字段规范
python -m tools.validation
```

**预期结果**：
- 生成 `data/processed/stageA_clusters.csv`（带簇标签的短语）
- 生成 `data/results/cluster_summary_A3.csv`（簇级汇总）
- 自动生成 `output/cluster_summary_A3.html`（HTML查看器）
- 簇数量：60-100个
- 噪音比例：55-65%（基准：59.7%）

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
1. CONTRIBUTING.md（开发者指南，必读）
2. docs/02_字段命名规范.md（字段规范）
3. docs/03_实施优先级指南.md（了解Phase）
4. scripts/core/step_A3_clustering.py（代码示例）
5. scripts/lib/config.py（配置规范）
```

---

## 🔧 核心工具说明

### 1. core/step_A3_clustering.py（核心聚类脚本）

**功能**：对短语进行语义聚类

**运行**：
```bash
cd scripts
python -m core.step_A3_clustering
```

**输入**：`data/raw/merged_keywords_all.csv`

**输出**：
- `data/processed/stageA_clusters.csv`（短语级，带cluster_id_A）
- `data/results/cluster_summary_A3.csv`（簇级汇总，含example_phrases）
- `output/cluster_summary_A3.html`（HTML查看器）

**关键参数**（在`lib/config.py`中配置）：
- `min_cluster_size`: 13（动态计算，基于数据量）
- `min_samples`: 3
- `use_dynamic_params`: True（启用动态参数计算）

---

### 2. tools/cluster_stats.py（质量分析工具）

**功能**：分析聚类结果质量，提供调优建议

**运行**：
```bash
cd scripts
python -m tools.cluster_stats
```

**输出**：
- ✅ 簇数量是否合理（60-70）
- ✅ 噪音比例是否合理（55-65%）
- ✅ 簇大小分布统计
- 💡 参数调优建议

---

### 3. selectors/manual_direction_selector.py（方向筛选工具）

**功能**：交互式筛选方向

**运行**：
```bash
cd scripts
python -m selectors.manual_direction_selector
```

**输出**：`data/results/direction_keywords.csv`（5-10个精选方向）

---

### 4. core/step_B3_cluster_stageB.py（方向内聚类）

**功能**：对选定方向进行二次聚类

**运行**：
```bash
cd scripts
python -m selectors.auto_select_directions  # 快速测试：自动选5个方向
python -m core.step_B3_cluster_stageB       # 方向内聚类
```

**输出**：
- `data/processed/stageB_clusters.csv`（方向内短语，带cluster_id_B）
- `data/results/cluster_summary_B3.csv`（子簇汇总）
- `output/cluster_summary_B3.html`（HTML查看器）

---

## ⚙️ 配置说明

所有配置在 `scripts/lib/config.py` 中管理：

```python
A3_CONFIG = {
    # 聚类参数
    "min_cluster_size": 15,  # 最小簇大小（默认15，启用动态计算后自动调整）
    "min_samples": 3,        # 最小邻居数
    "use_dynamic_params": True,  # 是否启用动态参数计算

    # 模型配置
    "embedding_model": "all-MiniLM-L6-v2",  # Embedding模型
    "clustering_method": "hdbscan",  # 聚类算法

    # 输入输出
    "input_file": MERGED_FILE,
    "output_clusters": CLUSTERS_FILE,
    "output_summary": CLUSTER_SUMMARY_FILE,
}
```

**参数调优指南**：
- 簇太多（>100）→ 增大 `min_cluster_size` 到 20-25
- 簇太少（<40）→ 减小 `min_cluster_size` 到 10-12
- 禁用动态参数 → 设置 `use_dynamic_params: False`

---

## 📊 数据流程图

```
种子词（seed_words）
    ↓
[A1] 种子词准备
    ↓
[A2] 扩展短语（影刀RPA/手动）→ core/step_A2_merge_csv.py
    ↓
data/raw/merged_keywords_all.csv（6,565条）
    ↓
[A3] 语义聚类 → core/step_A3_clustering.py
    ↓
data/processed/stageA_clusters.csv（6,344条，63簇）
data/results/cluster_summary_A3.csv（簇级汇总）
    ↓
tools/cluster_stats.py → 质量报告
    ↓
[A5] 人工筛选方向 → selectors/manual_direction_selector.py
    ↓
data/results/direction_keywords.csv（5个方向）
    ↓
[B1] 方向扩展（可选）
    ↓
[B3] 方向内聚类 → core/step_B3_cluster_stageB.py
    ↓
data/processed/stageB_clusters.csv（1,056条，9个子簇）
data/results/cluster_summary_B3.csv
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
# 修改 scripts/lib/config.py
A3_CONFIG = {
    "min_cluster_size": 20,  # 从15改为20
    "min_samples": 3,
    "use_dynamic_params": False,  # 禁用动态计算，使用固定值
}
```

然后重新运行：
```bash
cd scripts
python -m core.step_A3_clustering
```

---

### Q2: 噪音点比例很高（>60%）正常吗？

**回答**：是的，这是正常的。基准输出显示59.7%的噪音比例。

**原因**：
- 使用了多个跨度很大的种子词（46个）
- HDBSCAN将无法明确归类的短语标记为噪音（cluster_id=-1）
- 噪音点不代表"无用"，而是"需要人工判断"

**关键问题**：有效簇的质量如何？

**验证方法**：
1. 运行 `python -m tools.cluster_stats`
2. 查看 Top 10 最大的簇
3. 打开 `output/cluster_summary_A3.html` 查看 example_phrases
4. 如果能找到5-10个清晰的方向 → 成功！

---

### Q3: 如何查看聚类结果？

**推荐方法**：使用HTML查看器

```bash
# 方法1：自动生成（聚类时会自动生成）
cd scripts
python -m core.step_A3_clustering  # 自动生成 output/cluster_summary_A3.html

# 方法2：手动生成
python -m tools.generate_html_viewer
```

然后打开 `output/cluster_summary_A3.html`，可以：
- 在浏览器中查看表格
- 使用浏览器的"翻译"功能翻译为中文
- 搜索、排序、筛选

---

### Q4: import错误：ModuleNotFoundError

**问题**：`ModuleNotFoundError: No module named 'lib'`

**解决方案**：确保在项目根目录运行，并使用模块形式：

```bash
# 错误方式
cd scripts
python core/step_A3_clustering.py  # ❌

# 正确方式
cd scripts
python -m core.step_A3_clustering  # ✅
```

或设置 PYTHONPATH：
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/scripts"
python scripts/core/step_A3_clustering.py
```

---

## 📚 学习路径

### 新手路径（1-2小时）

```
1. 验证：python verify_structure.py（2分钟）
2. 阅读：docs/04_快速开始指南.md（10分钟）
3. 阅读：docs/tutorials/step_A3_使用说明.md（10分钟）
4. 运行：python -m core.step_A3_clustering（20分钟）
5. 分析：python -m tools.cluster_stats（5分钟）
6. 查看：output/cluster_summary_A3.html（10分钟）
7. 筛选：从cluster_summary挑5个方向（30分钟）
```

### 深入理解路径（半天）

```
1. 完整方法论：docs/01_需求挖掘方法论.md（1小时）
2. 实施规划：docs/03_实施优先级指南.md（30分钟）
3. 技术原理：docs/technical/聚类原理讲解.md（30分钟）
4. 字段规范：docs/02_字段命名规范.md（20分钟）
5. 开发规范：CONTRIBUTING.md（30分钟）
6. 历史总结：docs/analysis/GPT反馈总结.md（30分钟）
```

### 开发者路径（1天）

```
1. 阅读全部文档（上述路径）
2. 阅读源码：scripts/core/step_A3_clustering.py
3. 阅读配置：scripts/lib/config.py
4. 阅读工具：scripts/lib/utils.py
5. 运行测试：python verify_structure.py
6. 开发新功能：参考 CONTRIBUTING.md
7. 提交代码：遵循commit规范
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

详见 [CHANGELOG.md](CHANGELOG.md)

### 2024-12-16 - 项目结构重构 v2

- ✅ 重构项目结构为 Plan B（简化模式）
- ✅ 创建 scripts/{core,tools,selectors,lib} 目录结构
- ✅ 更新所有导入路径为 lib.* 格式
- ✅ 重组 data/ 为 {raw,processed,results,baseline}
- ✅ 添加基准输出快照（data/baseline/）
- ✅ 添加项目验证脚本（verify_structure.py）
- ✅ 添加标准配置文件（.gitignore, CONTRIBUTING.md, CHANGELOG.md）
- ✅ 创建文档导航（docs/README.md）

### 2024-12-15 - 初始完整实现

- ✅ 创建6个核心脚本（scripts目录）
- ✅ 整理4类文档（方法论、教程、分析、技术）
- ✅ 优化聚类参数（248簇 → 63簇）
- ✅ 创建质量分析工具（cluster_stats.py）
- ✅ 创建字段验证工具（validation.py）
- ✅ 自动HTML查看器生成

---

## 💬 需要帮助？

- **快速问题**：查看 `docs/04_快速开始指南.md`
- **方法论问题**：查看 `docs/01_需求挖掘方法论.md`
- **技术问题**：查看 `docs/technical/` 或 `CONTRIBUTING.md`
- **开发问题**：查看 `CONTRIBUTING.md`
- **历史参考**：查看 `docs/history/`

---

## 🤝 贡献

欢迎贡献！请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)

---

**开始使用**：`python verify_structure.py` → `docs/04_快速开始指南.md`

**祝你挖掘出好需求！** 🚀
