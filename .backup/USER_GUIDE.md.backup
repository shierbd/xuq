# 词根聚类需求挖掘系统 - 完整使用说明

## 📋 目录

1. [项目简介](#项目简介)
2. [系统架构](#系统架构)
3. [环境配置](#环境配置)
4. [使用方式选择](#使用方式选择)
   - [Web UI（推荐）](#web-ui推荐)
   - [命令行（高级）](#命令行高级)
5. [快速开始](#快速开始)
6. [完整工作流](#完整工作流)
7. [配置说明](#配置说明)
8. [输出文件说明](#输出文件说明)
9. [API成本管理](#api成本管理)
10. [常见问题](#常见问题)
11. [最佳实践](#最佳实践)
12. [项目结构](#项目结构)

---

## 项目简介

### 什么是词根聚类需求挖掘？

这是一个基于NLP和机器学习的需求挖掘系统，通过分析大量搜索关键词来发现用户需求模式。系统采用分层聚类策略，将数万条关键词短语组织成有意义的需求主题，并自动生成需求卡片。

### 核心功能

- **智能聚类**: 使用HDBSCAN算法对短语进行语义聚类
- **AI主题生成**: 使用LLM自动生成聚类主题标签
- **需求卡片生成**: 自动生成结构化需求卡片初稿
- **Token提取**: 建立需求框架词库，支持需求模板化
- **增量更新**: 支持新数据导入和历史数据管理

### 适用场景

- 产品需求挖掘
- 市场趋势分析
- 内容策略规划
- SEO关键词分析
- 用户意图研究

---

## 系统架构

### 六阶段工作流

```
Phase 1: 数据导入           Phase 2: 大组聚类           Phase 3: 人工筛选
   原始CSV文件        →     语义聚类（Level A）    →    选择有价值的聚类
   (55,275条)              (307个大组)                 (20-40个大组)
         ↓                        ↓                          ↓
Phase 4: 小组聚类 + 需求卡片生成                 Phase 5: Token提取
   细粒度聚类（Level B）                          提取关键词并分类
   LLM生成需求卡片                                建立需求词库
   (100-600个需求)                                (1000-5000个tokens)
         ↓
Phase 6: 增量更新（未来）
   新数据导入
   噪音点重新分配
```

### 技术栈

- **数据库**: MySQL 8.0+ / MariaDB 10.5+
- **Python**: 3.8+
- **NLP框架**: OpenAI Embeddings, HDBSCAN
- **LLM**: OpenAI / Anthropic / Deepseek
- **数据处理**: Pandas, NumPy, SQLAlchemy

---

## 环境配置

### 1. 系统要求

- **操作系统**: Windows 10/11, macOS, Linux
- **Python版本**: 3.8 或更高
- **内存**: 建议 8GB+（处理大规模数据时）
- **磁盘空间**: 5GB+（包含embeddings缓存）

### 2. 安装Python依赖

```bash
# 克隆或下载项目
cd 词根聚类需求挖掘

# 安装依赖
pip install -r requirements.txt
```

**主要依赖包:**
```
sqlalchemy>=2.0.0
pymysql>=1.0.0
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
hdbscan>=0.8.33
openai>=1.0.0
anthropic>=0.7.0
python-dotenv>=1.0.0
tqdm>=4.65.0
```

### 3. 配置数据库

#### 方法A: MySQL/MariaDB（推荐生产环境）

```bash
# 1. 创建数据库
mysql -u root -p
CREATE DATABASE search_demand_mining CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'demand_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON search_demand_mining.* TO 'demand_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;

# 2. 配置连接
# 编辑 config/settings.py
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'demand_user',
    'password': 'your_password',
    'database': 'search_demand_mining',
    'charset': 'utf8mb4'
}
```

#### 方法B: SQLite（推荐开发/测试）

```python
# config/settings.py
DATABASE_CONFIG = {
    'type': 'sqlite',
    'database': 'data/search_demand.db'
}
```

### 4. 配置LLM API

#### OpenAI（推荐，性价比高）

```python
# config/settings.py
LLM_PROVIDER = "openai"

LLM_CONFIG = {
    "openai": {
        "api_key": "sk-your-api-key",
        "model": "gpt-4o-mini",  # 或 gpt-4o
        "base_url": None,
        "temperature": 0.7,
        "max_tokens": 2000
    }
}
```

**获取API密钥**: https://platform.openai.com/api-keys

#### Anthropic Claude

```python
LLM_PROVIDER = "anthropic"

LLM_CONFIG = {
    "anthropic": {
        "api_key": "sk-ant-your-api-key",
        "model": "claude-3-5-sonnet-20241022",
        "temperature": 0.7,
        "max_tokens": 2000
    }
}
```

**获取API密钥**: https://console.anthropic.com/

#### Deepseek（最低成本）

```python
LLM_PROVIDER = "deepseek"

LLM_CONFIG = {
    "deepseek": {
        "api_key": "your-deepseek-key",
        "model": "deepseek-chat",
        "base_url": "https://api.deepseek.com",
        "temperature": 0.7,
        "max_tokens": 2000
    }
}
```

**获取API密钥**: https://platform.deepseek.com/

### 5. 配置Embedding服务

```python
# config/settings.py
EMBEDDING_CONFIG = {
    "provider": "openai",  # 或 "sentence_transformers"
    "model": "text-embedding-3-small",  # OpenAI embedding模型
    "batch_size": 100,
    "cache_enabled": True
}
```

### 6. 初始化数据库

```bash
# 创建所有数据表
python scripts/init_database.py
```

**输出示例:**
```
✓ 数据库连接成功
✓ 创建表: phrases
✓ 创建表: cluster_meta
✓ 创建表: demands
✓ 创建表: tokens
✅ 数据库初始化完成
```

---

## 使用方式选择

本系统提供**两种使用方式**：Web UI（图形界面）和命令行（CLI）。

### Web UI（推荐）

**适合人群**：所有用户，特别是不熟悉命令行的用户

**优势**：
- ✅ **可视化操作**：点击按钮即可完成所有操作
- ✅ **实时监控**：查看实时日志和进度
- ✅ **数据查看**：在线浏览聚类、需求卡片、Tokens
- ✅ **HTML导出**：支持浏览器翻译（Chrome/Edge右键翻译）
- ✅ **参数调整**：可视化调整聚类参数
- ✅ **配置测试**：测试数据库和LLM连接
- ✅ **集成文档**：内置完整使用文档

**启动方式**：

```bash
# 1. 安装Streamlit（首次使用）
pip install streamlit

# 2. 启动Web UI
streamlit run web_ui.py

# 3. 浏览器访问
# 自动打开，或手动访问: http://localhost:8501
```

**界面功能**：

| 页面 | 功能 |
|------|------|
| 🏠 首页概览 | 工作流程图、数据统计、快速操作 |
| 📥 Phase 1: 数据导入 | CSV文件导入、数据源选择、实时日志 |
| 🔄 Phase 2: 大组聚类 | 参数调整、聚类执行、结果统计 |
| ✅ Phase 3: 聚类筛选 | 导出CSV/HTML、在线查看、导入标记 |
| 📊 Phase 4: 需求生成 | 小组聚类、需求卡片生成、查看详情 |
| 🏷️ Phase 5: Token提取 | 参数设置、Token查看、词云生成 |
| 📋 数据查看与管理 | **HTML导出（支持浏览器翻译）**、数据筛选 |
| ⚙️ 配置管理 | 配置查看、连接测试、API成本估算 |
| 📖 使用说明 | 内置文档、快速参考、外部资源 |

**💡 特别功能：HTML导出 + 浏览器翻译**

如果你不懂英语，可以使用这个功能：
1. 在"数据查看与管理"页面点击 **"📤 导出为HTML"**
2. 在浏览器中打开生成的HTML文件
3. **右键点击页面** → 选择"翻译为中文"（Chrome/Edge）
4. 所有英文短语和需求会自动翻译成中文！

**详细文档**：[WEB_UI_README.md](../WEB_UI_README.md)

---

### 命令行（高级）

**适合人群**：熟悉命令行、需要自动化脚本、批量处理的高级用户

**优势**：
- ✅ **自动化**：可编写脚本批量处理
- ✅ **灵活性**：高级参数控制
- ✅ **远程执行**：SSH远程运行
- ✅ **CI/CD集成**：可集成到自动化流程

**使用方式**：

```bash
# Phase 1: 数据导入
python scripts/run_phase1_import.py

# Phase 2: 大组聚类
python scripts/run_phase2_clustering.py

# Phase 3: 聚类筛选（需手动编辑CSV）
# 导出 → 编辑 → 导入

# Phase 4: 需求生成
python scripts/run_phase4_demands.py

# Phase 5: Token提取
python scripts/run_phase5_tokens.py
```

**详细说明**：见下方"完整工作流"章节

---

### 如何选择？

| 场景 | 推荐方式 |
|------|----------|
| **首次使用** | Web UI - 可视化引导 |
| **日常使用** | Web UI - 方便快捷 |
| **数据查看** | Web UI - 在线浏览 + HTML导出翻译 |
| **参数调试** | Web UI - 实时反馈 |
| **自动化脚本** | 命令行 - 灵活控制 |
| **远程服务器** | 命令行 - SSH执行 |
| **批量处理** | 命令行 - 脚本化 |

**💡 提示**：大多数用户建议使用Web UI，只有在需要自动化或远程执行时才使用命令行。

---

## 快速开始

### 方式1: Web UI 快速体验（推荐）

**10分钟完成测试流程：**

```bash
# 1. 启动Web UI
streamlit run web_ui.py

# 浏览器会自动打开 http://localhost:8501
```

**操作步骤**：

1. **📥 Phase 1: 数据导入**
   - 选择CSV文件（或使用测试数据）
   - 勾选"使用测试限制"（只导入1000条）
   - 点击"开始导入"
   - 等待完成（约30秒）

2. **🔄 Phase 2: 大组聚类**
   - 勾选"使用缓存"
   - 勾选"测试模式"
   - 点击"开始聚类"
   - 等待完成（约2分钟）

3. **✅ Phase 3: 聚类筛选**
   - 点击"导出聚类报告（CSV + HTML）"
   - 在Excel/浏览器中查看聚类
   - 标记3-5个聚类为"selected"
   - 上传修改后的CSV文件

4. **📊 Phase 4: 需求生成**
   - 勾选"跳过LLM"和"限制处理大组数"
   - 点击"开始处理"
   - 查看生成的需求卡片

5. **📋 数据查看**
   - 进入"数据查看与管理"页面
   - 点击"导出为HTML"
   - 在浏览器中打开HTML文件
   - **右键翻译为中文**（Chrome/Edge）

**测试模式成本**: $0（跳过所有LLM调用）

---

### 方式2: 命令行快速体验

**30分钟完成测试流程：**

```bash
# 1. 准备测试数据（1000条）
# 将测试数据放到 data/raw/ 目录

# 2. 导入数据
python scripts/run_phase1_import.py --test-mode --limit 1000

# 3. 大组聚类（跳过embedding，使用缓存）
python scripts/run_phase2_clustering.py --use-cache

# 4. 标记几个聚类为选中
python scripts/import_selection.py

# 5. 小组聚类（跳过LLM）
python scripts/run_phase4_demands.py --skip-llm --test-limit 2

# 6. Token提取（跳过LLM）
python scripts/run_phase5_tokens.py --skip-llm --sample-size 1000
```

**测试模式成本**: $0（跳过所有LLM调用）

---

## 完整工作流

> **💡 说明**：本章节详细介绍**命令行方式**的完整工作流程。
>
> 如果使用**Web UI**，所有操作都可以在界面上完成，更加直观：
> - 启动: `streamlit run web_ui.py`
> - 详细说明: 见 [WEB_UI_README.md](../WEB_UI_README.md)

### Phase 1: 数据导入

#### 1.1 准备数据文件

将原始CSV文件放到 `data/raw/` 目录，支持的格式：

**文件类型:**
- `semrush_*.csv` - Semrush导出数据
- `dropdown_*.csv` - Google下拉词数据
- `related_search_*.csv` - 相关搜索数据

**必需列:**
- `Keyword`: 短语文本
- `Search Volume`: 搜索量（可选）
- `Seed Word`: 种子词（可选）

**CSV示例:**
```csv
Keyword,Search Volume,Seed Word
best running shoes,10000,running shoes
affordable running shoes,5000,running shoes
how to choose running shoes,3000,running shoes
```

#### 1.2 运行导入脚本

```bash
# 完整导入（所有CSV文件）
python scripts/run_phase1_import.py

# 指定单个文件
python scripts/run_phase1_import.py --file data/raw/semrush_keywords.csv

# 指定轮次（用于增量更新）
python scripts/run_phase1_import.py --round-id 2
```

**参数说明:**
- `--file`: 指定单个CSV文件路径
- `--round-id`: 数据轮次ID（默认1）
- `--test-mode`: 测试模式（限制数量）
- `--limit N`: 限制导入N条记录

**输出示例:**
```
======================================================================
                           Phase 1: 数据导入
======================================================================

【发现CSV文件】
  1. data/raw/semrush_processed.csv
  2. data/raw/dropdown_processed.csv
  3. data/raw/related_search_processed.csv

【导入数据】
  📥 导入 semrush_processed.csv...
  ✓ 读取了 20000 条记录
  ✓ 成功插入 19845 条记录

  📥 导入 dropdown_processed.csv...
  ✓ 读取了 15000 条记录
  ✓ 成功插入 14923 条记录

【统计信息】
  总导入: 55,275 条短语
  按来源分布:
    - semrush: 35,123 (63.5%)
    - dropdown: 15,234 (27.6%)
    - related_search: 4,918 (8.9%)

✅ Phase 1 完成！
```

#### 1.3 验证导入结果

```bash
# 查看数据库统计
python -c "from storage.repository import PhraseRepository; repo = PhraseRepository(); stats = repo.get_statistics(); print(f'总短语数: {stats[\"total_count\"]}')"
```

---

### Phase 2: 大组聚类

#### 2.1 生成Embeddings

```bash
# 首次运行（生成embeddings）
python scripts/run_phase2_clustering.py

# 使用已有缓存（快速）
python scripts/run_phase2_clustering.py --use-cache
```

**重要提示:**
- 首次运行会调用Embedding API，生成embeddings缓存
- embeddings缓存保存在 `data/cache/embeddings_round1.npz`
- 后续运行使用 `--use-cache` 跳过embedding生成

**Embedding成本估算:**
- 模型: text-embedding-3-small
- 55,275条短语 ≈ 1.5M tokens
- 成本: ~$0.03

#### 2.2 执行聚类

聚类过程完全自动化，包括：
1. 加载短语和embeddings
2. 执行HDBSCAN聚类（Level A）
3. 更新phrases表的cluster_id_A
4. 保存聚类元数据到cluster_meta表
5. 生成聚类报告和CSV

**输出示例:**
```
======================================================================
                        Phase 2: 大组聚类 (Level A)
======================================================================

【阶段1】加载短语数据...
  ✓ 加载了 55,275 条短语

【阶段2】计算Embeddings...
  ✓ 使用缓存的embeddings: (55275, 1536)

【阶段3】执行HDBSCAN聚类...
  ✓ 聚类完成
  - 聚类数量: 307
  - 噪音点: 15234 (27.5%)
  - 聚类大小: 最小=30, 最大=3452, 平均=130.2

【阶段4】更新数据库...
  ✓ 已更新 55275/55275 条记录的cluster_id_A

【阶段5】保存聚类元数据...
  ✓ 已保存 307 个聚类的元数据

✅ Phase 2 完成！
  - 生成聚类: 307 个
  - 聚类CSV: data/output/clusters_levelA.csv
  - 统计报告: data/output/phase2_clustering_report.txt
```

#### 2.3 查看聚类结果

**CSV文件:** `data/output/clusters_levelA.csv`

| cluster_id | size | example_phrases | main_theme |
|------------|------|-----------------|------------|
| 1174 | 222 | dashboard, online dashboard, salesforce dashboard | Dashboard相关 |
| 1244 | 201 | pdf converter, online pdf converter, pdf to word | PDF工具 |
| 892 | 156 | running shoes, best running shoes, running shoes for women | 跑鞋购买 |

---

### Phase 3: 人工筛选聚类

#### 3.1 审核聚类CSV

打开 `data/output/clusters_levelA.csv`，审核每个聚类：

**筛选标准:**
1. ✅ **保留**: 主题明确、有商业价值、短语数量适中（50-500）
2. ❌ **过滤**: 主题模糊、噪音多、过于宽泛或狭窄

**操作步骤:**
1. 在CSV中添加 `is_selected` 列
2. 标记选中的聚类为 `TRUE`
3. 标记过滤的聚类为 `FALSE`

**示例:**
```csv
cluster_id,size,example_phrases,main_theme,is_selected
1174,222,dashboard; online dashboard; salesforce dashboard,Dashboard相关,TRUE
1244,201,pdf converter; online pdf converter; pdf to word,PDF工具,TRUE
892,156,running shoes; best running shoes,跑鞋购买,TRUE
...
```

#### 3.2 导入筛选结果

```bash
# 导入审核后的CSV
python scripts/import_selection.py data/output/clusters_levelA.csv

# 或使用默认路径
python scripts/import_selection.py
```

**输出示例:**
```
✓ 读取CSV: 307 条记录
✓ 更新数据库...
  - 选中: 28 个聚类
  - 未选中: 279 个聚类

✅ 筛选结果已导入数据库
```

#### 3.3 验证筛选结果

```bash
# 查看选中的聚类
python -c "from storage.repository import ClusterMetaRepository; repo = ClusterMetaRepository(); selected = repo.get_selected_clusters('A'); print(f'选中聚类: {len(selected)}个'); [print(f'  {c.cluster_id}: {c.main_theme} ({c.size}条)') for c in selected[:5]]"
```

---

### Phase 4: 小组聚类 + 需求卡片生成

#### 4.1 测试运行（无LLM成本）

```bash
# 测试聚类效果（跳过需求卡片生成）
python scripts/run_phase4_demands.py --skip-llm --test-limit 2
```

**目的:**
- 验证小组聚类参数是否合理
- 检查cluster_id_B编码是否正确
- 评估噪音率是否在可接受范围（40-60%）

#### 4.2 完整运行（生成需求卡片）

```bash
# 处理所有选中的大组
python scripts/run_phase4_demands.py

# 仅处理前N个大组
python scripts/run_phase4_demands.py --test-limit 5
```

**处理过程:**
```
对每个选中的大组:
  1. 加载大组的所有短语
  2. 加载对应的embeddings（从缓存）
  3. 执行小组聚类（Level B, min_size=5）
  4. 更新phrases.cluster_id_B
  5. 保存cluster_meta (Level B)
  6. 对每个小组:
     - 调用LLM生成需求卡片
     - 保存到demands表
  7. 生成小组统计
```

**输出示例:**
```
======================================================================
                   Phase 4: 小组聚类 + 需求卡片生成
======================================================================

【阶段1】加载选中的大组...
✓ 加载了 28 个选中的大组

【阶段2】小组聚类和需求卡片生成...

进度: 1/28
======================================================================
处理大组 1174: Dashboard相关
======================================================================

【步骤1】加载大组短语...
  ✓ 加载了 222 条短语

【步骤2】加载embeddings...
  ✓ 加载了 (222, 1536) embeddings

【步骤3】执行小组聚类...
  ✓ 聚类完成: 6个小组

【步骤4】更新数据库...
  ✓ 已更新 222/222 条记录的cluster_id_B

【步骤5】保存小组元数据...
  ✓ 已保存 6 个小组的元数据

【步骤6】生成需求卡片...
  簇11740000: 生成需求卡片...
  ✓ 生成需求卡片: Dashboard符号说明

  簇11740001: 生成需求卡片...
  ✓ 生成需求卡片: Home Assistant Dashboard

  ... (共6个)
  ✓ 已生成 6 个需求卡片

✅ Phase 4 完成！
  - 处理大组: 28/28
  - 生成小组: 156
  - 生成需求: 156
  - 需求CSV: data/output/demands_draft.csv
```

#### 4.3 审核需求卡片

打开 `data/output/demands_draft.csv`:

**审核内容:**
1. ✏️ 修改 `title` 使其更准确
2. ✏️ 修改 `description` 使其更清晰
3. ✏️ 补充 `user_scenario`
4. ✏️ 修正 `demand_type` (tool/content/service/education/other)
5. ✏️ **必填** `business_value` (high/medium/low)
6. ✏️ **必填** `status` (validated/archived)

**不要修改:**
- 🔒 demand_id
- 🔒 source_cluster_A, source_cluster_B
- 🔒 related_phrases_count

**CSV示例:**
```csv
demand_id,title,description,user_scenario,demand_type,business_value,status
1,Dashboard符号含义说明,用户需要了解仪表盘上各种符号的含义,汽车驾驶,content,medium,validated
2,在线Dashboard工具,用户需要在线创建和管理数据可视化Dashboard,数据分析,tool,high,validated
...
```

#### 4.4 导入审核结果（待实现）

```bash
# TODO: 实现导入脚本
python scripts/import_demands.py data/output/demands_draft.csv
```

---

### Phase 5: Token提取与分类

#### 5.1 测试运行（无LLM成本）

```bash
# 1000条采样，跳过LLM分类
python scripts/run_phase5_tokens.py --skip-llm --sample-size 1000 --min-frequency 5
```

**目的:**
- 验证token提取逻辑
- 查看高频词分布
- 评估停用词过滤效果

#### 5.2 完整运行（使用LLM分类）

```bash
# 10000条采样（推荐）
python scripts/run_phase5_tokens.py --sample-size 10000 --min-frequency 3

# 全量运行（所有短语）
python scripts/run_phase5_tokens.py --sample-size 0 --min-frequency 2
```

**输出示例:**
```
======================================================================
                         Phase 5: Token提取与分类
======================================================================

【阶段1】加载短语数据...
  ✓ 加载了 10,000 条短语（采样模式）

【阶段2】提取候选tokens...
  ✓ 提取到 3,245 个唯一tokens
  ✓ 过滤后保留 856 个tokens (频次>=3)

【阶段3】提取二元词组...
  ✓ 唯一bigrams: 245

【阶段4】LLM批量分类...
  ✓ 批次 1: 分类了 50 个tokens
  ✓ 批次 2: 分类了 50 个tokens
  ...
  ✓ 成功分类 856 个tokens

  分类统计:
    - intent: 124 个 (14.5%)
    - action: 89 个 (10.4%)
    - object: 532 个 (62.1%)
    - other: 111 个 (13.0%)

【阶段5】保存到数据库...
  ✓ 成功保存 856 个tokens到数据库

✅ Phase 5 完成！
  - Token CSV: data/output/tokens_extracted.csv
  - 统计报告: data/output/phase5_tokens_report.txt
```

#### 5.3 审核Token分类

打开 `data/output/tokens_extracted.csv`:

**审核内容:**
1. 检查 `token_type` 是否正确
2. 修改错误的分类
3. 标记 `verified=TRUE` 表示已审核

**分类标准:**
- **intent**: 意图词（best, top, how to, cheap, free, affordable）
- **action**: 动作词（download, buy, make, create, install, convert）
- **object**: 对象词（shoes, phone, tutorial, recipe, software, dashboard）
- **other**: 其他（品牌名、地名、数字）

**CSV示例:**
```csv
token_text,token_type,in_phrase_count,confidence,verified,notes
best,intent,856,high,TRUE,
download,action,423,high,TRUE,
shoes,object,345,high,TRUE,
nike,other,234,high,TRUE,品牌名
dashboard,object,222,high,TRUE,
```

---

## 配置说明

### config/settings.py 完整配置

```python
from pathlib import Path

# ============================================================================
# 项目路径配置
# ============================================================================
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
RAW_DATA_DIR = DATA_DIR / 'raw'
OUTPUT_DIR = DATA_DIR / 'output'
CACHE_DIR = DATA_DIR / 'cache'

# 确保目录存在
for dir_path in [DATA_DIR, RAW_DATA_DIR, OUTPUT_DIR, CACHE_DIR]:
    dir_path.mkdir(exist_ok=True)

# ============================================================================
# 数据库配置
# ============================================================================
DATABASE_CONFIG = {
    # MySQL/MariaDB配置
    'host': 'localhost',
    'port': 3306,
    'user': 'demand_user',
    'password': 'your_password',
    'database': 'search_demand_mining',
    'charset': 'utf8mb4',

    # 或使用SQLite（开发/测试）
    # 'type': 'sqlite',
    # 'database': str(DATA_DIR / 'search_demand.db')
}

# ============================================================================
# LLM配置
# ============================================================================
LLM_PROVIDER = "openai"  # 可选: "openai", "anthropic", "deepseek"

LLM_CONFIG = {
    "openai": {
        "api_key": "sk-your-openai-key",
        "model": "gpt-4o-mini",  # 性价比最高
        "base_url": None,
        "temperature": 0.7,
        "max_tokens": 2000
    },
    "anthropic": {
        "api_key": "sk-ant-your-key",
        "model": "claude-3-5-sonnet-20241022",
        "temperature": 0.7,
        "max_tokens": 2000
    },
    "deepseek": {
        "api_key": "your-deepseek-key",
        "model": "deepseek-chat",
        "base_url": "https://api.deepseek.com",
        "temperature": 0.7,
        "max_tokens": 2000
    }
}

# ============================================================================
# Embedding配置
# ============================================================================
EMBEDDING_CONFIG = {
    "provider": "openai",
    "model": "text-embedding-3-small",  # 推荐，性价比高
    "batch_size": 100,
    "cache_enabled": True,
    "cache_dir": CACHE_DIR
}

# ============================================================================
# 聚类配置
# ============================================================================

# 大组聚类配置（Level A）
LARGE_CLUSTER_CONFIG = {
    "min_cluster_size": 30,      # 最小聚类大小
    "min_samples": 10,            # 最小样本数
    "metric": "cosine",           # 距离度量
    "cluster_selection_epsilon": 0.0,
    "cluster_selection_method": "eom"
}

# 小组聚类配置（Level B）
SMALL_CLUSTER_CONFIG = {
    "min_cluster_size": 5,        # 更小的聚类
    "min_samples": 2,             # 更少的样本
    "metric": "cosine",
    "cluster_selection_epsilon": 0.0
}

# ============================================================================
# Phase 4 需求卡片配置
# ============================================================================
DEMAND_CARD_PHRASE_SAMPLE_SIZE = 30  # LLM生成时采样的短语数

# ============================================================================
# Phase 5 Token提取配置
# ============================================================================
TOKEN_EXTRACTION_CONFIG = {
    "min_frequency": 3,           # 最小频次
    "min_token_length": 2,        # 最小token长度
    "max_token_length": 30,       # 最大token长度
    "batch_size": 50              # LLM分类批次大小
}
```

---

## 输出文件说明

### Phase 1 输出

```
data/output/
  └── phase1_import_report.txt      # 导入统计报告
```

### Phase 2 输出

```
data/output/
  ├── clusters_levelA.csv            # 大组聚类CSV（待人工筛选）
  ├── phase2_clustering_report.txt   # 聚类统计报告
  └── phase2_secondary_clusters.csv  # 二次聚类结果（如果执行）

data/cache/
  └── embeddings_round1.npz          # Embeddings缓存（重要！）
```

### Phase 3 输出

无新文件，直接更新数据库的 `cluster_meta.is_selected` 字段。

### Phase 4 输出

```
data/output/
  ├── demands_draft.csv              # 需求卡片CSV（待人工审核）
  └── phase4_demands_report.txt      # 需求生成统计报告
```

### Phase 5 输出

```
data/output/
  ├── tokens_extracted.csv           # Token CSV（待人工审核）
  └── phase5_tokens_report.txt       # Token提取统计报告
```

---

## API成本管理

### 成本估算工具

```bash
# 估算Phase 2 embedding成本
python scripts/estimate_cost.py --phase 2 --count 55275

# 估算Phase 4 LLM成本（假设28个大组，平均6个小组）
python scripts/estimate_cost.py --phase 4 --clusters 28 --avg-subgroups 6

# 估算Phase 5 LLM成本（假设1000个tokens）
python scripts/estimate_cost.py --phase 5 --tokens 1000
```

### 典型项目成本（55,275条短语，28个选中大组）

| Phase | API调用 | OpenAI | Anthropic | Deepseek |
|-------|---------|--------|-----------|----------|
| Phase 2 (Embedding) | 55,275短语 | $0.03 | N/A | N/A |
| Phase 2 (AI主题，可选) | 307次 | $0.60 | $12.00 | $0.08 |
| Phase 4 (需求卡片) | ~168次 | $0.50 | $10.00 | $0.07 |
| Phase 5 (Token分类) | ~1000 tokens | $0.05 | $1.00 | $0.01 |
| **总计** | - | **$1.18** | **$23.00** | **$0.16** |

**推荐配置:**
- **Embedding**: OpenAI text-embedding-3-small（唯一选择）
- **LLM**: OpenAI GPT-4o-mini 或 Deepseek（性价比高）
- **高质量要求**: Anthropic Claude（最贵但质量最好）

### 成本优化策略

1. **使用缓存**
   - Phase 2 embedding缓存可重复使用
   - 避免重复计算embeddings

2. **分阶段测试**
   - 使用 `--skip-llm` 测试流程
   - 使用 `--test-limit` 限制处理数量
   - 验证后再全量运行

3. **选择性处理**
   - Phase 3 筛选高价值聚类
   - 只对选中的聚类生成需求卡片

4. **批量处理**
   - Token分类批量处理（50个/批）
   - 减少API调用次数

---

## 常见问题

### Q1: 数据库连接失败

**错误:**
```
pymysql.err.OperationalError: (2003, "Can't connect to MySQL server")
```

**解决方案:**
1. 检查MySQL服务是否启动
2. 验证 `config/settings.py` 中的数据库配置
3. 确认用户权限
4. 测试连接: `python scripts/test_db_connection.py`

### Q2: Embedding缓存损坏

**错误:**
```
FileNotFoundError: embeddings_round1.npz not found
```

**解决方案:**
```bash
# 重新生成embeddings（不使用缓存）
python scripts/run_phase2_clustering.py
```

### Q3: LLM API调用失败

**错误:**
```
openai.error.RateLimitError: Rate limit exceeded
```

**解决方案:**
1. 检查API密钥是否有效
2. 检查API配额是否用尽
3. 降低并发量（减少batch_size）
4. 等待几分钟后重试

### Q4: 内存不足

**错误:**
```
MemoryError: Unable to allocate array
```

**解决方案:**
1. 使用采样模式: `--sample-size 10000`
2. 分批处理: `--test-limit 5`
3. 增加系统内存
4. 使用数据库分页查询

### Q5: 聚类结果不理想

**问题:** 聚类太大/太小，主题不明确

**解决方案:**
1. 调整 `LARGE_CLUSTER_CONFIG.min_cluster_size`
   - 太大 → 减小 min_cluster_size
   - 太小 → 增大 min_cluster_size
2. 执行二次聚类: `python scripts/run_phase2_resplit.py --cluster-id XXX`
3. 在Phase 3人工筛选时过滤掉不好的聚类

### Q6: 需求卡片质量不高

**问题:** LLM生成的需求描述不准确

**解决方案:**
1. 调整LLM temperature（降低到0.3-0.5）
2. 使用更高级的模型（GPT-4o, Claude Sonnet）
3. 在 `ai/client.py` 中优化prompt
4. 人工审核修改CSV

### Q7: Token分类错误率高

**问题:** LLM将intent词误分类为object

**解决方案:**
1. 在 `ai/client.py` 的prompt中添加更多示例
2. 人工审核修改 `tokens_extracted.csv`
3. 使用更准确的模型
4. 调整停用词列表

### Q8: 如何处理增量数据？

**场景:** 有新的关键词数据需要导入

**方案:**
```bash
# 1. 导入新数据（指定新轮次）
python scripts/run_phase1_import.py --round-id 2 --file data/raw/new_keywords.csv

# 2. 为新数据生成embeddings
python scripts/run_phase2_clustering.py --round-id 2

# 3. 合并到现有聚类或创建新聚类
# （Phase 6增量更新，待实现）
```

### Q9: 如何备份数据？

**方案:**
```bash
# 备份MySQL数据库
mysqldump -u demand_user -p search_demand_mining > backup_$(date +%Y%m%d).sql

# 备份embeddings缓存
cp -r data/cache/ backup/cache_$(date +%Y%m%d)/

# 备份输出文件
cp -r data/output/ backup/output_$(date +%Y%m%d)/
```

### Q10: 如何导出最终需求清单？

**方案:**
```bash
# 导出已验证的需求
python scripts/export_demands.py --status validated --output final_demands.xlsx

# 或直接查询数据库
python -c "from storage.repository import DemandRepository; import pandas as pd; repo = DemandRepository(); demands = repo.get_validated_demands(); df = pd.DataFrame([{'id': d.demand_id, 'title': d.title, 'description': d.description} for d in demands]); df.to_excel('final_demands.xlsx', index=False)"
```

---

## 最佳实践

### 1. 项目启动检查清单

- [ ] 数据库已创建并连接成功
- [ ] LLM API密钥已配置并测试
- [ ] Embedding API密钥已配置
- [ ] 所有Python依赖已安装
- [ ] 数据表已初始化
- [ ] 原始CSV数据已准备

### 2. 测试驱动开发

**建议流程:**
```bash
# 第1天: 小规模测试（免费）
python scripts/run_phase1_import.py --limit 1000
python scripts/run_phase2_clustering.py
python scripts/import_selection.py  # 手工标记2-3个聚类
python scripts/run_phase4_demands.py --skip-llm --test-limit 1
python scripts/run_phase5_tokens.py --skip-llm --sample-size 500

# 第2天: 中等规模测试（低成本 <$1）
python scripts/run_phase1_import.py --limit 10000
python scripts/run_phase2_clustering.py
python scripts/import_selection.py  # 标记5-10个聚类
python scripts/run_phase4_demands.py --test-limit 5
python scripts/run_phase5_tokens.py --sample-size 5000

# 第3天: 全量运行（正式）
python scripts/run_phase1_import.py
python scripts/run_phase2_clustering.py
python scripts/import_selection.py  # 标记20-40个聚类
python scripts/run_phase4_demands.py
python scripts/run_phase5_tokens.py
```

### 3. 数据质量保证

**Phase 1数据导入:**
- 检查CSV格式是否正确
- 验证必需列是否存在
- 确认数据无重复

**Phase 2聚类质量:**
- 查看聚类大小分布是否合理
- 检查示例短语是否语义相关
- 评估噪音率（20-40%正常）

**Phase 3筛选标准:**
- 聚类主题是否明确
- 短语数量是否适中（50-500）
- 是否有商业价值

**Phase 4需求审核:**
- 需求标题是否简洁有力
- 需求描述是否清晰完整
- 用户场景是否真实
- 必填字段是否完整

**Phase 5 Token审核:**
- 分类是否正确
- 是否遗漏重要token
- 停用词是否需要调整

### 4. 性能优化

**大规模数据处理:**
- 使用批量插入（bulk_insert_mappings）
- 启用embedding缓存
- 合理设置batch_size
- 考虑分批处理

**API调用优化:**
- 使用批量分类（50个/批）
- 设置合理的timeout
- 实现错误重试机制
- 监控API配额

### 5. 成本控制

**开发阶段:**
- 始终使用 `--skip-llm` 测试流程
- 使用 `--test-limit` 限制数量
- 优先使用缓存

**生产阶段:**
- 选择性处理高价值聚类
- 使用性价比高的模型（GPT-4o-mini, Deepseek）
- 批量处理Token分类
- 监控成本，设置预算警报

### 6. 版本管理

**数据轮次管理:**
```
Round 1: 初始数据导入（2024-01-15）
Round 2: 增量数据导入（2024-02-15）
Round 3: 增量数据导入（2024-03-15）
```

**备份策略:**
- 每个Phase完成后备份数据库
- 保存embeddings缓存
- 归档输出CSV文件
- Git提交配置变更

---

## 项目结构

```
词根聚类需求挖掘/
├── config/
│   └── settings.py                 # 核心配置文件
│
├── data/
│   ├── raw/                        # 原始CSV数据
│   │   ├── semrush_*.csv
│   │   ├── dropdown_*.csv
│   │   └── related_search_*.csv
│   │
│   ├── cache/                      # Embeddings缓存
│   │   └── embeddings_round1.npz
│   │
│   └── output/                     # 输出文件
│       ├── clusters_levelA.csv
│       ├── demands_draft.csv
│       └── tokens_extracted.csv
│
├── scripts/                        # 执行脚本
│   ├── run_phase1_import.py       # Phase 1: 数据导入
│   ├── run_phase2_clustering.py   # Phase 2: 大组聚类
│   ├── run_phase2_resplit.py      # Phase 2: 二次聚类
│   ├── import_selection.py        # Phase 3: 导入筛选结果
│   ├── run_phase4_demands.py      # Phase 4: 小组聚类 + 需求卡片
│   └── run_phase5_tokens.py       # Phase 5: Token提取
│
├── core/                           # 核心算法
│   ├── clustering.py              # 聚类算法（HDBSCAN）
│   ├── embedding.py               # Embedding服务
│   └── utils.py                   # 工具函数
│
├── ai/                             # AI服务
│   └── client.py                  # LLM客户端（统一接口）
│
├── storage/                        # 数据持久化
│   ├── models.py                  # SQLAlchemy模型
│   └── repository.py              # Repository层（CRUD）
│
├── utils/                          # 工具模块
│   └── token_extractor.py         # Token提取工具
│
├── docs/                           # 文档
│   ├── USER_GUIDE.md              # 本文档
│   ├── Phase2_Implementation_Summary.md
│   ├── Phase4_Implementation_Summary.md
│   └── Phase5_Implementation_Summary.md
│
├── requirements.txt                # Python依赖
└── README.md                       # 项目说明
```

---

## 快速参考

### 常用命令速查

```bash
# Phase 1: 数据导入
python scripts/run_phase1_import.py

# Phase 2: 大组聚类
python scripts/run_phase2_clustering.py --use-cache

# Phase 3: 导入筛选（编辑CSV后）
python scripts/import_selection.py

# Phase 4: 完整运行
python scripts/run_phase4_demands.py

# Phase 4: 测试运行
python scripts/run_phase4_demands.py --skip-llm --test-limit 2

# Phase 5: 完整运行
python scripts/run_phase5_tokens.py --sample-size 10000

# Phase 5: 测试运行
python scripts/run_phase5_tokens.py --skip-llm --sample-size 1000

# 数据库统计
python -c "from storage.repository import PhraseRepository; repo = PhraseRepository(); stats = repo.get_statistics(); print(stats)"

# 查看聚类
python -c "from storage.repository import ClusterMetaRepository; repo = ClusterMetaRepository(); clusters = repo.get_all_clusters('A'); print(f'{len(clusters)} clusters')"
```

### 关键配置路径

```
数据库配置: config/settings.py → DATABASE_CONFIG
LLM配置: config/settings.py → LLM_PROVIDER, LLM_CONFIG
聚类参数: config/settings.py → LARGE_CLUSTER_CONFIG, SMALL_CLUSTER_CONFIG
输出目录: data/output/
缓存目录: data/cache/
```

---

## 联系与支持

### 获取帮助

1. 查看文档: `docs/` 目录下的详细文档
2. 查看代码注释: 所有核心函数都有详细的docstring
3. 查看测试示例: 每个脚本都有 `--help` 参数

### 贡献指南

欢迎贡献代码、文档和建议！

---

**文档版本:** 1.0
**最后更新:** 2024-12-19
**作者:** Claude Code

---

## 附录

### A. 数据表结构

#### phrases 表
```sql
CREATE TABLE phrases (
    phrase_id INT PRIMARY KEY AUTO_INCREMENT,
    phrase VARCHAR(500) NOT NULL UNIQUE,
    frequency INT DEFAULT 1,
    volume INT DEFAULT 0,
    seed_word VARCHAR(255),
    source_type VARCHAR(50),
    cluster_id_A INT,
    cluster_id_B INT,
    mapped_demand_id INT,
    processed_status VARCHAR(50) DEFAULT 'unseen',
    first_seen_round INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### cluster_meta 表
```sql
CREATE TABLE cluster_meta (
    id INT PRIMARY KEY AUTO_INCREMENT,
    cluster_id INT NOT NULL,
    cluster_level CHAR(1) NOT NULL,
    size INT NOT NULL,
    example_phrases TEXT,
    main_theme VARCHAR(255),
    parent_cluster_id INT,
    total_frequency INT DEFAULT 0,
    is_selected BOOLEAN DEFAULT FALSE,
    selection_score INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(cluster_id, cluster_level)
);
```

#### demands 表
```sql
CREATE TABLE demands (
    demand_id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    user_scenario TEXT,
    demand_type VARCHAR(50),
    source_cluster_A INT,
    source_cluster_B INT,
    related_phrases_count INT DEFAULT 0,
    business_value VARCHAR(20),
    status VARCHAR(50) DEFAULT 'idea',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### tokens 表
```sql
CREATE TABLE tokens (
    token_id INT PRIMARY KEY AUTO_INCREMENT,
    token_text VARCHAR(100) NOT NULL UNIQUE,
    token_type VARCHAR(20) NOT NULL,
    in_phrase_count INT DEFAULT 0,
    first_seen_round INT DEFAULT 1,
    verified BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### B. API价格参考（2024年12月）

#### OpenAI
- text-embedding-3-small: $0.02 / 1M tokens
- gpt-4o-mini: $0.15 / 1M input, $0.60 / 1M output
- gpt-4o: $2.50 / 1M input, $10.00 / 1M output

#### Anthropic
- claude-3-5-sonnet: $3.00 / 1M input, $15.00 / 1M output
- claude-3-opus: $15.00 / 1M input, $75.00 / 1M output

#### Deepseek
- deepseek-chat: $0.14 / 1M input, $0.28 / 1M output

### C. 性能基准

**测试环境:**
- CPU: Intel i7-12700K
- RAM: 32GB DDR4
- 数据量: 55,275条短语

**运行时间:**
- Phase 1 (导入): ~2分钟
- Phase 2 (聚类，有缓存): ~5分钟
- Phase 2 (聚类，无缓存): ~15分钟
- Phase 4 (28个大组，含LLM): ~30分钟
- Phase 5 (10000采样，含LLM): ~10分钟

**API调用次数:**
- Phase 2 embedding: 553次（batch_size=100）
- Phase 4 LLM: ~168次（28个大组 × 平均6个小组）
- Phase 5 LLM: ~20次（1000 tokens / batch_size=50）

---

🎉 **恭喜！您已完成使用说明的阅读。祝您使用愉快！**
