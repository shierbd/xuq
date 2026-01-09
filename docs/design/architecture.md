# 系统架构设计文档

> **文档说明**: 本文档基于代码分析自动生成，描述了词根聚类需求挖掘系统的架构设计。

## 1. 架构概述

**架构模式**: 分层架构 + Repository模式

**技术栈**:
- **后端**: Python 3.8+
- **数据库**: MySQL/MariaDB (推荐) 或 SQLite
- **机器学习**: sentence-transformers, scikit-learn, hdbscan, networkx
- **LLM集成**: OpenAI API, Anthropic API, DeepSeek API
- **Web框架**: Streamlit
- **ORM**: SQLAlchemy 2.0+

**设计原则**:
- 模块化：清晰的职责划分
- 可扩展：支持多种数据库、LLM提供商、聚类算法
- 可测试：Repository模式便于单元测试
- 可维护：统一的配置管理和日志记录

---

## 2. 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      Web UI Layer                            │
│                    (Streamlit)                               │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │ Phase 0  │ Phase 1  │ Phase 2  │ Phase 3  │ Phase 4  │  │
│  │ 词根管理  │ 数据导入  │ 聚类执行  │ 聚类筛选  │ 需求生成  │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Business Logic Layer                       │
│                      (core/)                                 │
│  ┌──────────────┬──────────────┬──────────────┬─────────┐  │
│  │ data_        │ clustering.py│ embedding.py │ llm_    │  │
│  │ integration  │              │              │ service │  │
│  │              │              │              │         │  │
│  ├──────────────┼──────────────┼──────────────┼─────────┤  │
│  │ token_       │ template_    │ product_     │ junyan_ │  │
│  │ extraction   │ discovery    │ identifier   │ method  │  │
│  └──────────────┴──────────────┴──────────────┴─────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Data Access Layer                           │
│                   (storage/)                                 │
│  ┌──────────────┬──────────────┬──────────────┬─────────┐  │
│  │ Phrase       │ ClusterMeta  │ Demand       │ Token   │  │
│  │ Repository   │ Repository   │ Repository   │ Repo    │  │
│  └──────────────┴──────────────┴──────────────┴─────────┘  │
│                    models.py (SQLAlchemy ORM)                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Database Layer                            │
│              MySQL/MariaDB or SQLite                         │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │ phrases  │ cluster_ │ demands  │ tokens   │ seed_    │  │
│  │          │ meta     │          │          │ words    │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   External Services                          │
│  ┌──────────────┬──────────────┬──────────────┐            │
│  │ OpenAI API   │ Anthropic    │ DeepSeek API │            │
│  │              │ API          │              │            │
│  └──────────────┴──────────────┴──────────────┘            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   Configuration & Utils                      │
│  ┌──────────────┬──────────────┬──────────────┐            │
│  │ config/      │ utils/       │ ai/          │            │
│  │ settings.py  │ helpers.py   │ client.py    │            │
│  └──────────────┴──────────────┴──────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 分层架构详解

### 3.1 Web UI Layer (ui/)

**职责**: 用户交互界面

**技术**: Streamlit

**主要组件**:
- `web_ui.py`: 主入口，仪表盘
- `ui/pages/phase0_*.py`: Phase 0 词根管理页面
- `ui/pages/phase1_import.py`: Phase 1 数据导入页面
- `ui/pages/phase2_clustering.py`: Phase 2 聚类执行页面
- `ui/pages/phase3_selection.py`: Phase 3 聚类筛选页面
- `ui/pages/phase4_demands.py`: Phase 4 需求生成页面
- `ui/pages/phase5_tokens.py`: Phase 5 Token管理页面
- `ui/pages/config_page.py`: 配置管理页面
- `ui/pages/documentation.py`: 文档查看器

**特性**:
- 实时日志输出
- 进度条显示
- 数据表格编辑
- 参数配置保存
- 一键导出报告

---

### 3.2 Business Logic Layer (core/)

**职责**: 核心业务逻辑

**主要模块**:

#### 3.2.1 数据整合 (data_integration.py)
- 从多个数据源导入数据
- 数据清洗和去重
- 数据格式转换

#### 3.2.2 聚类引擎 (clustering.py)
- HDBSCAN聚类
- K-Means聚类（备选）
- 聚类质量评估

#### 3.2.3 图聚类 (graph_clustering.py)
- Louvain社区发现
- 图构建和优化

#### 3.2.4 Embedding服务 (embedding.py)
- Sentence Transformers向量化
- Embedding缓存管理
- 批量计算优化

#### 3.2.5 LLM服务 (llm_service.py)
- 聚类主题生成
- 需求卡片生成
- Token分类
- 意图分析

#### 3.2.6 Token提取 (token_extraction.py)
- N-gram提取（1-4 gram）
- 停用词过滤
- 频率统计

#### 3.2.7 模板发现 (template_discovery.py)
- 短语模板识别
- 变量提取
- 模板频率统计

#### 3.2.8 产品识别 (product_identifier.py)
- 产品名称识别
- 产品相关短语提取

#### 3.2.9 君言方法 (junyan_method.py)
- 君言方法论实现
- 模板化产品提取

#### 3.2.10 聚类标注 (cluster_labeling.py)
- 聚类主题标签生成
- 聚类质量评分

#### 3.2.11 意图分类 (intent_classification.py)
- 搜索意图分析
- 意图类型分类

---

### 3.3 Data Access Layer (storage/)

**职责**: 数据库访问封装

**设计模式**: Repository模式

**主要组件**:

#### 3.3.1 ORM模型 (models.py)
- `Phrase`: 短语总库
- `ClusterMeta`: 聚类元数据
- `Demand`: 需求卡片
- `Token`: Token词库
- `SeedWord`: 种子词管理
- `WordSegment`: 分词结果缓存

#### 3.3.2 Repository层
- `PhraseRepository`: 短语CRUD操作
- `ClusterMetaRepository`: 聚类元数据操作
- `DemandRepository`: 需求卡片操作
- `TokenRepository`: Token操作
- `WordSegmentRepository`: 分词结果操作

**优势**:
- 隔离业务逻辑和数据库细节
- 便于单元测试（可mock Repository）
- 统一的事务管理
- 批量操作优化

---

### 3.4 Database Layer

**数据库选择**:
- **生产环境**: MySQL/MariaDB（推荐）
- **开发测试**: SQLite

**数据表**:
- `phrases`: 短语总库（55,275条）
- `cluster_meta`: 聚类元数据（307个大组）
- `demands`: 需求卡片（20-50个）
- `tokens`: Token词库（数千个）
- `seed_words`: 种子词管理
- `word_segments`: 分词结果缓存

---

### 3.5 External Services

**LLM集成 (ai/client.py)**:
- OpenAI API（GPT-4, GPT-3.5）
- Anthropic API（Claude）
- DeepSeek API

**功能**:
- 统一的LLM调用接口
- 自动重试机制
- 错误处理
- 成本控制

---

### 3.6 Configuration & Utils

**配置管理 (config/settings.py)**:
- 数据库配置
- Embedding配置
- 聚类参数配置
- LLM配置
- 路径配置

**工具函数 (utils/)**:
- `helpers.py`: 文本处理、导出等
- `token_extractor.py`: Token提取工具
- `logger.py`: 日志管理

---

## 4. 模块划分

### 4.1 核心模块 (core/)

```
core/
├── __init__.py
├── data_integration.py      # 数据整合清洗
├── clustering.py            # HDBSCAN聚类引擎
├── graph_clustering.py      # Louvain图聚类
├── embedding.py             # Embedding服务（带缓存）
├── llm_service.py           # LLM服务封装
├── token_extraction.py      # Token提取
├── template_discovery.py    # 模板发现
├── product_identifier.py    # 产品识别
├── junyan_method.py         # 君言方法论
├── cluster_labeling.py      # 聚类标注
├── cluster_scoring.py       # 聚类评分
├── cluster_llm_assessment.py # LLM质量评估
├── intent_classification.py # 意图分类
└── variable_extractor.py    # 变量提取
```

---

### 4.2 数据访问模块 (storage/)

```
storage/
├── __init__.py
├── models.py                # SQLAlchemy ORM模型
├── repository.py            # Repository封装
└── word_segment_repository.py # 分词结果Repository
```

---

### 4.3 Web UI模块 (ui/)

```
ui/
├── __init__.py
├── components/              # 可复用组件
└── pages/                   # 各Phase页面
    ├── phase0_root_management.py
    ├── phase0_pos_tagging.py
    ├── phase0_translation.py
    ├── phase1_import.py
    ├── phase2_clustering.py
    ├── phase2_cluster_view.py
    ├── phase3_selection.py
    ├── phase3_intent_analysis.py
    ├── phase4_demands.py
    ├── phase5_tokens.py
    ├── config_page.py
    └── documentation.py
```

---

### 4.4 脚本模块 (scripts/)

```
scripts/
├── run_phase1_import.py         # Phase 1: 数据导入
├── run_phase1_scoring.py        # Phase 1: 质量评分
├── run_phase2_clustering.py     # Phase 2: HDBSCAN聚类
├── run_phase2_louvain.py        # Phase 2: Louvain聚类
├── run_phase2_label_clusters.py # Phase 2: 聚类标注
├── run_phase3_selection.py      # Phase 3: 导出大组报告
├── run_phase3_intent_analysis.py # Phase 3: 意图分析
├── run_phase4_demands.py        # Phase 4: 小组+需求卡片
├── run_phase5_tokens.py         # Phase 5: Token提取
├── import_selection.py          # Phase 3b: 导入人工选择
├── import_demand_reviews.py     # Phase 4b: 导入需求审核
├── import_token_reviews.py      # Phase 5b: 导入Token审核
└── migrate_*.py                 # 数据库迁移脚本
```

---

### 4.5 配置模块 (config/)

```
config/
├── __init__.py
└── settings.py              # 统一配置文件
```

---

### 4.6 工具模块 (utils/)

```
utils/
├── __init__.py
├── helpers.py               # 文本处理、导出等
├── token_extractor.py       # Token提取工具
└── logger.py                # 日志管理
```

---

### 4.7 AI模块 (ai/)

```
ai/
├── __init__.py
└── client.py                # LLM API调用封装
```

---

## 5. 数据流

### 5.1 Phase 1: 数据导入

```
原始数据文件 (CSV/Excel)
    ↓
data_integration.py (清洗、去重)
    ↓
PhraseRepository.bulk_insert_phrases()
    ↓
phrases表
```

---

### 5.2 Phase 2: 大组聚类

```
phrases表 (所有短语)
    ↓
embedding.py (生成向量)
    ↓
Embedding缓存 (embeddings_round1.npz)
    ↓
clustering.py / graph_clustering.py (聚类)
    ↓
PhraseRepository.update_cluster_assignments()
    ↓
phrases.cluster_id_A 更新
    ↓
ClusterMetaRepository.save_cluster_meta()
    ↓
cluster_meta表 (Level A)
```

---

### 5.3 Phase 3: 大组筛选

```
cluster_meta表 (Level A)
    ↓
llm_service.py (生成主题标签)
    ↓
导出HTML/CSV报告
    ↓
人工打分 (CSV编辑)
    ↓
import_selection.py
    ↓
cluster_meta.is_selected 更新
```

---

### 5.4 Phase 4: 小组聚类 + 需求卡片

```
选中的大组
    ↓
clustering.py (小组聚类)
    ↓
phrases.cluster_id_B 更新
    ↓
cluster_meta表 (Level B)
    ↓
llm_service.py (生成需求卡片)
    ↓
DemandRepository.save_demand()
    ↓
demands表
    ↓
导出CSV供人工审核
```

---

### 5.5 Phase 5: Token提取

```
phrases表 (所有短语)
    ↓
token_extraction.py (N-gram提取)
    ↓
停用词过滤 + 频率统计
    ↓
llm_service.py (Token分类)
    ↓
TokenRepository.save_token()
    ↓
tokens表
    ↓
导出CSV供人工审核
```

---

## 6. 技术选型

### 6.1 为什么选择Streamlit？

**优势**:
- 快速开发：Python代码直接生成Web界面
- 无需前端知识：专注业务逻辑
- 实时交互：自动刷新和状态管理
- 丰富组件：表格、图表、文件上传等

**劣势**:
- 性能限制：不适合高并发场景
- 定制化受限：UI样式定制有限

**适用场景**: 内部工具、数据分析平台、MVP快速验证

---

### 6.2 为什么选择SQLAlchemy？

**优势**:
- ORM抽象：面向对象操作数据库
- 数据库无关：支持MySQL、SQLite等
- 类型安全：Python类型检查
- 事务管理：自动事务处理

**劣势**:
- 学习曲线：需要理解ORM概念
- 性能开销：相比原生SQL有一定开销

---

### 6.3 为什么选择HDBSCAN？

**优势**:
- 无需指定聚类数量：自动发现聚类
- 处理噪音点：-1标签表示噪音
- 密度聚类：适合不规则形状的聚类
- 层次结构：支持多层聚类

**劣势**:
- 参数敏感：min_cluster_size和min_samples需要调优
- 计算复杂度：O(n log n)

**备选方案**:
- Louvain：图聚类，适合大规模数据
- K-Means：质心聚类，速度快但需要指定K

---

### 6.4 为什么选择Sentence Transformers？

**优势**:
- 预训练模型：无需训练即可使用
- 语义理解：捕捉短语语义相似度
- 多语言支持：支持100+语言
- 轻量级：all-MiniLM-L6-v2仅80MB

**劣势**:
- 计算开销：需要GPU加速
- 模型固定：无法针对特定领域微调（MVP阶段）

---

## 7. 扩展性设计

### 7.1 支持多种数据库

通过`DATABASE_CONFIG["type"]`切换：
- MySQL/MariaDB（生产环境）
- SQLite（开发测试）

**实现方式**:
- 使用SQLAlchemy的数据库无关API
- ENUM类型兼容处理（MySQL用ENUM，SQLite用String+CheckConstraint）

---

### 7.2 支持多种LLM提供商

通过`LLM_PROVIDER`切换：
- OpenAI（GPT-4, GPT-3.5）
- Anthropic（Claude）
- DeepSeek

**实现方式**:
- 统一的LLM调用接口（ai/client.py）
- 配置驱动的提供商选择

---

### 7.3 支持多种聚类算法

通过配置切换：
- HDBSCAN（密度聚类）
- Louvain（图聚类）
- K-Means（质心聚类）

**实现方式**:
- 统一的聚类接口（ClusteringEngine）
- 算法特定的参数配置

---

### 7.4 增量更新支持

**设计**:
- 记录数据轮次（first_seen_round）
- Embedding缓存按轮次存储
- KNN算法分配新短语到现有聚类

---

## 8. 性能优化

### 8.1 Embedding缓存

**问题**: Embedding计算耗时（5万条短语需要5-10分钟）

**解决方案**:
- 首次计算后缓存到NPZ文件
- 增量更新时只计算新短语
- 使用GPU加速（可选）

---

### 8.2 批量操作

**问题**: 逐条插入数据库慢

**解决方案**:
- 使用`bulk_insert_mappings`批量插入
- 批次大小：1000条/批

---

### 8.3 数据库索引

**优化**:
- phrase字段：UNIQUE索引
- cluster_id_A, cluster_id_B: 普通索引
- source_type, first_seen_round: 普通索引

---

## 9. 安全性设计

### 9.1 数据保护

- 所有数据文件不推送到GitHub（.gitignore配置）
- 敏感信息使用.env文件管理
- 数据库密码不硬编码

---

### 9.2 SQL注入防护

- 使用SQLAlchemy ORM（参数化查询）
- 不拼接SQL字符串

---

### 9.3 输入验证

- 文件上传类型检查
- 数据格式验证
- 异常处理和错误提示

---

## 10. 可维护性设计

### 10.1 日志记录

- 统一的日志管理（utils/logger.py）
- 日志级别：DEBUG, INFO, WARNING, ERROR
- 日志文件按日期轮转

---

### 10.2 配置管理

- 统一的配置文件（config/settings.py）
- 环境变量管理（.env）
- 配置验证脚本（scripts/validate_config.py）

---

### 10.3 代码规范

- 遵循PEP 8规范
- 使用类型注解
- 添加docstring
- 单元测试覆盖率 > 55%

---

## 11. 部署架构

### 11.1 开发环境

```
本地开发机
├── Python 3.8+
├── MySQL/SQLite
├── Streamlit (localhost:8501)
└── LLM API (OpenAI/Anthropic/DeepSeek)
```

---

### 11.2 生产环境（未来）

```
云服务器
├── Python 3.8+
├── MySQL/MariaDB (RDS)
├── Streamlit (Nginx反向代理)
├── Redis (缓存)
└── LLM API (OpenAI/Anthropic/DeepSeek)
```

---

## 12. 总结

### 12.1 架构优势

- **模块化**: 清晰的分层架构，职责明确
- **可扩展**: 支持多种数据库、LLM、聚类算法
- **可测试**: Repository模式便于单元测试
- **可维护**: 统一的配置管理和日志记录
- **快速开发**: Streamlit快速构建Web界面

---

### 12.2 技术亮点

- **Embedding缓存**: 避免重复计算，提升性能
- **Repository模式**: 隔离业务逻辑和数据库细节
- **统一LLM接口**: 支持多种LLM提供商切换
- **增量更新**: 支持多轮数据导入和聚类更新
- **批量操作**: 优化数据库插入性能

---

**文档版本**: v1.0
**生成日期**: 2026-01-08
**生成方式**: 基于代码分析自动生成
