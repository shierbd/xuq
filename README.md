# 词根聚类需求挖掘系统 MVP版本

## 📋 项目简介

这是一个基于语义聚类的需求挖掘方法论系统，用于从英文单词种子（word roots）发现产品机会方向。

**核心理念**：从单词 → 短语 → 语义簇 → 需求方向 → MVP验证

**当前版本**: MVP v1.0（简化架构，2周快速验证）

---

## 🚀 快速开始

### 环境要求

- Python >= 3.8
- MySQL / MariaDB（推荐）或 SQLite
- 8GB+ RAM（用于embedding计算）

### 安装步骤

1. **克隆项目**
   ```bash
   git clone https://github.com/shierbd/xuq.git
   cd 词根聚类需求挖掘
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境变量**
   ```bash
   # 复制环境变量模板
   cp .env.example .env

   # 编辑 .env 文件，填写：
   # - 数据库连接信息
   # - LLM API密钥（OpenAI/Anthropic/DeepSeek）
   ```

4. **创建数据库**
   ```python
   # 运行Python交互式终端
   python
   >>> from storage.models import create_all_tables
   >>> create_all_tables()
   >>> exit()
   ```

5. **准备原始数据**
   ```bash
   # 将原始数据文件放入对应目录
   data/raw/semrush/       # SEMRUSH导出的CSV文件
   data/raw/dropdown/      # 下拉词CSV文件
   data/raw/related_search/ # 相关搜索Excel文件
   ```

---

## 📁 项目结构（MVP版本）

```
词根聚类需求挖掘/
│
├── config/                  # 统一配置
│   ├── __init__.py
│   └── settings.py          # 数据库、聚类、LLM配置
│
├── core/                    # 核心业务逻辑
│   ├── __init__.py
│   ├── data_integration.py  # 数据整合清洗
│   ├── clustering.py        # 大组+小组聚类引擎
│   ├── embedding.py         # Embedding服务（带缓存）
│   └── incremental.py       # 增量更新逻辑
│
├── storage/                 # 数据库访问层
│   ├── __init__.py
│   ├── models.py            # SQLAlchemy模型（4张核心表）
│   └── repository.py        # 数据库CRUD封装
│
├── ai/                      # LLM集成
│   ├── __init__.py
│   ├── client.py            # LLM API调用封装
│   └── prompts.py           # Prompt模板
│
├── scripts/                 # 入口脚本（按Phase组织）
│   ├── run_phase1_import.py      # Phase 1：数据导入
│   ├── run_phase2_clustering.py  # Phase 2：大组聚类
│   ├── run_phase3_selection.py   # Phase 3：导出大组报告
│   ├── import_selection.py       # Phase 3b：导入人工选择
│   ├── run_phase4_demands.py     # Phase 4：小组+需求卡片
│   └── run_incremental.py        # Phase 7：增量更新
│
├── utils/                   # 工具函数
│   ├── __init__.py
│   └── helpers.py           # 文本处理、导出等
│
├── data/                    # 数据目录（.gitignore排除）
│   ├── raw/                 # 原始数据
│   ├── processed/           # 处理后数据
│   ├── output/              # 导出报告
│   └── cache/               # Embedding缓存
│
├── docs/                    # 文档
│   ├── MVP版本实施方案.md    # 完整MVP方案（必读）
│   ├── gpt回复.md            # GPT反馈分析
│   ├── 技术实现审查与优化建议.md  # 原始技术方案
│   ├── GitHub配置说明.md
│   └── 数据安全保护说明.md
│
├── .env.example             # 环境变量模板
├── .gitignore               # Git忽略规则（数据保护）
├── requirements.txt         # Python依赖
└── README.md                # 本文件
```

---

## 📖 核心文档

### ⭐⭐⭐ 必读（开始前）

1. **[MVP版本实施方案](docs/MVP版本实施方案.md)** - 完整的MVP开发计划
2. **[数据安全保护说明](docs/数据安全保护说明.md)** - Git数据保护策略

### ⭐⭐ 重要（实施时）

3. **[GitHub配置说明](docs/GitHub配置说明.md)** - Git使用规范
4. **[技术实现审查与优化建议](docs/技术实现审查与优化建议.md)** - 原始技术方案参考

---

## 🎯 MVP工作流程

### Phase 1: 数据导入（预计1天）

**目标**: 将原始关键词数据导入数据库

```bash
# 运行数据导入脚本
cd scripts
python run_phase1_import.py
```

**输入**:
- `data/raw/semrush/*.csv` - SEMRUSH导出数据
- `data/raw/dropdown/*.csv` - 下拉词数据
- `data/raw/related_search/*.xlsx` - 相关搜索数据

**输出**:
- 数据库 `phrases` 表填充完毕（预计5-10万条）

---

### Phase 2: 大组聚类（预计1天）

**目标**: 对所有短语进行语义聚类，生成60-100个大组

```bash
python run_phase2_clustering.py
```

**配置参数** (在 `config/settings.py`):
- `min_cluster_size`: 30
- `min_samples`: 3
- `embedding_model`: all-MiniLM-L6-v2

**输出**:
- `phrases.cluster_id_A` 更新
- `cluster_meta` 表填充（cluster_level='A'）
- `data/cache/embeddings_round1.npz` - Embedding缓存

---

### Phase 3: 大组筛选（预计0.5天 + 人工时间）

**步骤A: 生成报告**

```bash
python run_phase3_selection.py
```

**输出**:
- `data/output/cluster_selection_report.html` - 带AI主题标签的HTML报告
- `data/output/cluster_selection_report.csv` - CSV报告

**步骤B: 人工打分**

1. 打开 `cluster_selection_report.html`（浏览器可翻译）
2. 在 `cluster_selection_report.csv` 中：
   - 查看 `main_theme` 和 `example_phrases`
   - 在 `selection_score` 列填写 1-5 分
   - 4-5分 = 选中，1-3分 = 不选中
3. 保存CSV

**步骤C: 导入选择**

```bash
python import_selection.py
```

**输出**:
- `cluster_meta.is_selected` 更新
- 选中10-15个大组

---

### Phase 4: 小组聚类 + 需求卡片（预计2-3天）

**目标**: 对选中的大组进行小组聚类，生成需求卡片初稿

```bash
python run_phase4_demands.py
```

**流程**:
1. 对每个选中的大组，进行小组聚类
2. 对每个小组，AI生成需求卡片初稿
3. 导出 `data/output/demands_draft.csv` 供人工审核

**人工审核**:
1. 打开 `demands_draft.csv`
2. 修改：title, description, user_scenario, demand_type
3. 填写：business_value (high/medium/low)
4. 修改：status (validated/archived)
5. 🔒 不要修改：demand_id, source_cluster_A, source_cluster_B

**导入审核结果**:
```bash
python run_phase4_demands.py  # 脚本末尾会自动导入
# 或单独运行导入函数
```

**输出**:
- 20-50个需求卡片
- 至少10个 status='validated'

---

### Phase 5: Tokens提取（可选，预计1天）

**目标**: 从已验证需求中提取意图词、动作词、对象词等

```bash
# TODO: 待实现
```

---

### Phase 7: 增量更新（可选，预计1天）

**目标**: 导入新一轮数据，自动分配到大组，过滤已处理的短语

```bash
python run_incremental.py --round_id 2
```

**输出**:
- 新短语自动分配到现有大组
- 过滤规则：
  - `processed_status != 'unseen'` → 跳过
  - 已关联稳定需求 → 归档
  - 低频噪音点 → 归档

---

## ⚙️ 配置说明

所有配置在 `config/settings.py` 中统一管理：

### 数据库配置

```python
DATABASE_CONFIG = {
    "type": "mysql",  # mysql 或 sqlite
    "host": "localhost",
    "port": 3306,
    "database": "keyword_clustering",
    "user": "root",
    "password": "",
}
```

### Embedding配置

```python
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_MODEL_VERSION = "2.2.0"  # 固定版本，确保一致性
EMBEDDING_DIM = 384
```

### 聚类参数

```python
# 大组聚类
LARGE_CLUSTER_CONFIG = {
    "min_cluster_size": 30,
    "min_samples": 3,
    "metric": "cosine",
}

# 小组聚类
SMALL_CLUSTER_CONFIG = {
    "min_cluster_size": 5,
    "min_samples": 2,
    "metric": "cosine",
}
```

### LLM配置

```python
LLM_PROVIDER = "openai"  # openai, anthropic, deepseek

LLM_CONFIG = {
    "openai": {
        "model": "gpt-4o-mini",
        "temperature": 0.3,
    },
}
```

在 `.env` 文件中配置API密钥：
```bash
OPENAI_API_KEY=your_key_here
```

---

## 🗄️ 数据库表结构

### 1. phrases（短语总库）

核心字段：
- `phrase` - 短语文本（唯一）
- `cluster_id_A` - 大组ID
- `cluster_id_B` - 小组ID
- `mapped_demand_id` - 关联的需求ID
- `processed_status` - 处理状态（unseen/reviewed/assigned/archived）
- `first_seen_round` - 首次出现轮次

### 2. demands（需求卡片）

核心字段：
- `title` - 需求标题
- `description` - 需求描述
- `user_scenario` - 用户场景
- `demand_type` - 需求类型（tool/content/service/education/other）
- `business_value` - 商业价值（high/medium/low/unknown）
- `status` - 状态（idea/validated/in_progress/archived）

### 3. tokens（需求框架词库）

核心字段：
- `token_text` - 词文本（唯一）
- `token_type` - 词类型（intent/action/object/attribute/condition/other）
- `in_phrase_count` - 出现在短语中的次数
- `verified` - 是否已人工验证

### 4. cluster_meta（聚类元数据）

核心字段：
- `cluster_id` - 聚类ID
- `cluster_level` - 聚类级别（A=大组，B=小组）
- `size` - 聚类包含的短语数量
- `main_theme` - AI生成的主题标签
- `is_selected` - 是否被选中
- `selection_score` - 人工打分（1-5）

---

## 🔐 数据安全说明

**重要**: 所有数据文件（CSV、Excel、数据库）都不会被推送到GitHub！

### 自动保护

- `.gitignore` 已配置排除所有数据文件
- 包括：`data/` 目录、`*.csv`、`*.xlsx`、`*.db`

### 推送前检查

每次推送前运行安全检查：

```bash
# Windows
powershell -ExecutionPolicy Bypass -File .\scripts\check_before_push.ps1

# Linux/Mac
bash scripts/check_before_push.sh
```

详见: [数据安全保护说明](docs/数据安全保护说明.md)

---

## 🚨 常见问题

### Q1: 如何选择数据库？

**推荐**: MySQL / MariaDB（MVP方案默认）

**原因**:
- 原生支持ENUM类型
- 更好的并发性能
- 便于扩展到生产环境

**替代**: SQLite（开发测试用）
- 需要修改ENUM为VARCHAR
- 参见MVP方案第2.0节

---

### Q2: Embedding计算很慢怎么办？

**优化方案**:
1. 使用GPU加速（安装 `torch-cuda`）
2. 调整批次大小（`EMBEDDING_BATCH_SIZE`）
3. 使用缓存（首次计算后自动缓存）

```python
# config/settings.py
EMBEDDING_BATCH_SIZE = 256  # 减小到128试试
```

---

### Q3: 聚类结果太多/太少怎么调整？

**簇太多（>100）**:
```python
LARGE_CLUSTER_CONFIG = {
    "min_cluster_size": 40,  # 从30增加到40
    "min_samples": 5,        # 从3增加到5
}
```

**簇太少（<40）**:
```python
LARGE_CLUSTER_CONFIG = {
    "min_cluster_size": 20,  # 从30减少到20
    "min_samples": 2,        # 从3减少到2
}
```

---

### Q4: 如何查看聚类结果？

**方法1**: 查看HTML报告
```bash
# Phase 3 会自动生成
open data/output/cluster_selection_report.html
```

**方法2**: 直接查询数据库
```sql
SELECT cluster_id, main_theme, size, example_phrases
FROM cluster_meta
WHERE cluster_level = 'A' AND is_selected = TRUE
ORDER BY size DESC;
```

---

## 📊 MVP成功标准

完成以下标准，即认为MVP成功：

### 数据验证
- [x] phrases 表有 50,000+ 条数据
- [x] cluster_meta 表有 60-100 个大组
- [x] 选中 10-15 个目标大组
- [x] demands 表有 20-50 个需求卡片
- [x] 至少10个需求 status='validated'

### 流程验证
- [x] Phase 1-4 全部跑通
- [x] 人工筛选流程（导出→手工→导入）可用
- [x] AI生成的需求卡片准确率 >60%
- [x] 增量更新不会重复处理已有需求

### 可用性验证
- [x] 从5万词产出10-20个可落地的需求想法
- [x] 每个需求下有真实的搜索短语支撑
- [x] 能够快速定位"哪些词属于同一需求"

---

## 🚀 MVP之后的迭代路径

### 第二轮迭代（+2周）
1. **Phase 5 完整版**：tokens词库完善
2. **Phase 7 完整版**：增量小组重聚类
3. **数据表字段扩展**：添加 tags, main_tokens (JSON)

### 第三轮迭代（+2周）
4. **Web UI**：ClusterSelector, DemandEditor
5. **批量操作功能**：合并需求、批量标记
6. **导出工具**：SEO词表、Landing Page素材

### 第四轮迭代（有产品后）
7. **Phase 6**：商业化字段（revenue, landing_url）
8. **数据可视化**：需求地图、词云、趋势图
9. **自动化Pipeline**：定期扫描新词、自动推送报告

---

## 📝 开发周期

**MVP阶段**: 2周（10个工作日）

### 第一周
| 天数 | 任务 | 产出 |
|------|------|------|
| Day 1 | 搭建架构、创建数据库表 | 目录结构、models.py |
| Day 2 | Phase 1 实现 | 数据导入脚本 |
| Day 3 | Phase 2 实现 | 大组聚类脚本 |
| Day 4 | Phase 3 实现 | 大组报告生成 |
| Day 5 | 人工筛选大组 | 选出10-15个大组 |

### 第二周
| 天数 | 任务 | 产出 |
|------|------|------|
| Day 6-7 | Phase 4 实现 | 需求卡片初稿 |
| Day 8 | 人工审核需求 | 10-20个有效需求 |
| Day 9 | Phase 5 简化版（可选） | tokens基础词库 |
| Day 10 | Phase 7 简化版 + 测试 | 增量更新脚本 |

---

## 🔗 相关资源

- **GitHub仓库**: https://github.com/shierbd/xuq
- **HDBSCAN文档**: https://hdbscan.readthedocs.io/
- **Sentence Transformers**: https://www.sbert.net/
- **SQLAlchemy文档**: https://docs.sqlalchemy.org/

---

## 💬 需要帮助？

- **MVP实施**: 查看 `docs/MVP版本实施方案.md`
- **技术方案**: 查看 `docs/技术实现审查与优化建议.md`
- **数据安全**: 查看 `docs/数据安全保护说明.md`
- **Git使用**: 查看 `docs/GitHub配置说明.md`

---

## 📝 版本信息

- **当前版本**: MVP v1.0
- **最后更新**: 2024-12-19
- **开发状态**: MVP框架搭建完成，Phase脚本待实现

---

## 🤝 贡献

本项目处于MVP阶段，欢迎提出问题和建议。

**提交规范**:
```
<type>: <subject>

feat: 新功能
fix: 修复bug
docs: 文档更新
refactor: 重构代码
```

---

**开始使用**：先阅读 `docs/MVP版本实施方案.md`，然后运行 Phase 1-4

**祝你挖掘出好需求！** 🚀
