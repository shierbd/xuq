# CLAUDE.md

> 项目知识库，供 Claude Code 使用

## 项目概述

**词根聚类需求挖掘系统** 是一个基于语义聚类的需求挖掘方法论系统，用于从英文关键词种子（word roots）发现产品机会方向。

**核心价值**: 将"单词 → 短语 → 语义簇 → 需求方向"的分析流程自动化，从5万个关键词中快速发现10-20个可落地的产品需求。

**当前版本**: MVP v1.0（Phase 1-5 已完成）

---

## 技术栈

### 后端
- Python 3.8+
- SQLAlchemy 2.0+ (ORM)
- MySQL/MariaDB 或 SQLite

### 机器学习
- sentence-transformers (语义向量)
- HDBSCAN (密度聚类)
- Louvain (图聚类)
- scikit-learn

### LLM集成
- OpenAI API (GPT-4, GPT-3.5)
- Anthropic API (Claude)
- DeepSeek API

### Web框架
- Streamlit (可视化界面)

---

## 核心功能

### Phase 0: 词根管理
- 词根标注和分类（Token框架）
- 词性标注（NLTK）
- 翻译服务（deep-translator）

### Phase 1: 数据导入
- 从SEMRUSH、下拉词、相关搜索导入数据
- 数据清洗和去重
- 批量插入数据库（55,275条短语）

### Phase 2: 大组聚类
- 生成语义向量（all-MiniLM-L6-v2）
- 执行聚类（HDBSCAN/Louvain）
- 生成307个大组
- Embedding缓存优化

### Phase 3: 大组筛选
- AI生成聚类主题标签
- 意图分析（informational/transactional/navigational）
- 人工打分筛选（1-5分）
- 导出HTML/CSV报告

### Phase 4: 小组聚类 + 需求卡片
- 对选中大组执行小组聚类
- LLM生成需求卡片
- 需求类型分类（tool/content/service/education）
- 商业价值评估（high/medium/low）

### Phase 5: Token提取
- N-gram提取（1-4 gram）
- 停用词过滤
- LLM分类（intent/action/object/attribute/condition）
- 频率统计

### Phase 6: Reddit板块分析 (新增)
- 导入Reddit板块数据（CSV/Excel，无列名）
- AI生成3个中文标签
- 重要性评分（1-5分）
- 可配置的AI提示词
- 标签分组和筛选
- 数据导出功能

---

## 架构设计

### 分层架构
```
Web UI Layer (ui/)
    ↓
Business Logic Layer (core/)
    ↓
Data Access Layer (storage/)
    ↓
Database Layer (MySQL/SQLite)
```

### 核心模块
- **core/**: 业务逻辑（聚类、embedding、LLM服务）
- **storage/**: 数据访问（Repository模式）
- **ai/**: LLM集成
- **ui/**: Streamlit Web界面
- **scripts/**: 命令行脚本
- **utils/**: 工具函数

---

## 数据库设计

### 9张核心表
1. **phrases**: 短语总库（55,275条）
2. **cluster_meta**: 聚类元数据（307个大组）
3. **demands**: 需求卡片（20-50个）
4. **tokens**: Token词库（数千个）
5. **seed_words**: 种子词管理
6. **word_segments**: 分词结果缓存
7. **segmentation_batches**: 分词批次记录
8. **reddit_subreddits**: Reddit板块数据（新增）
9. **ai_prompt_configs**: AI提示词配置（新增）

### 关键字段
- **phrases.cluster_id_A**: 大组ID
- **phrases.cluster_id_B**: 小组ID
- **phrases.mapped_demand_id**: 关联需求ID
- **cluster_meta.is_selected**: 是否被选中
- **cluster_meta.main_theme**: AI生成的主题标签

---

## 开发指南

### 代码规范
- 遵循 PEP 8
- 使用类型注解
- 添加 docstring
- 单元测试覆盖率 > 55%

### 提交规范
```
feat: 新功能
fix: 修复bug
docs: 文档更新
refactor: 重构代码
test: 测试相关
chore: 构建/工具相关
```

### 数据安全
- ⚠️ **所有数据文件不推送到GitHub**
- data/ 目录已在 .gitignore 中排除
- .env 文件不提交
- 推送前运行安全检查脚本

---

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，填写数据库和API密钥
```

### 3. 创建数据库表
```python
from storage.models import create_all_tables
create_all_tables()
```

### 4. 启动Web UI
```bash
streamlit run web_ui.py
# 访问 http://localhost:8501
```

---

## 重要文档索引

### 核心文档
- [README.md](README.md) - 项目概述和快速开始
- [需求文档](docs/requirements.md) - 功能需求和用户故事
- [架构设计](docs/design/architecture.md) - 系统架构和模块划分
- [数据库设计](docs/design/database-design.md) - 数据表结构和关系

### 实施文档
- [MVP版本实施方案](docs/MVP版本实施方案.md) - 完整的MVP开发计划
- [Phase4实施摘要](docs/Phase4_Implementation_Summary.md) - 小组聚类+需求卡片
- [Phase5实施摘要](docs/Phase5_Implementation_Summary.md) - Token提取与分类

### 使用指南
- [Web UI使用说明](WEB_UI_README.md) - Web界面操作指南
- [完整使用流程指南](docs/完整使用流程指南.md) - 端到端使用流程
- [数据安全保护说明](docs/数据安全保护说明.md) - Git数据保护策略

---

## 常用命令

### 运行Web UI
```bash
streamlit run web_ui.py
```

### 运行命令行脚本
```bash
# Phase 1: 数据导入
python scripts/run_phase1_import.py

# Phase 2: 大组聚类
python scripts/run_phase2_clustering.py

# Phase 3: 导出大组报告
python scripts/run_phase3_selection.py

# Phase 4: 小组聚类 + 需求卡片
python scripts/run_phase4_demands.py

# Phase 5: Token提取
python scripts/run_phase5_tokens.py
```

### 测试
```bash
# 运行所有测试
pytest

# 生成覆盖率报告
pytest --cov=core --cov=storage --cov=ai --cov=utils
```

---

## 配置说明

### 数据库配置 (.env)
```bash
DB_TYPE=mysql          # mysql 或 sqlite
DB_HOST=localhost
DB_PORT=3306
DB_NAME=keyword_clustering
DB_USER=root
DB_PASSWORD=your_password
```

### LLM配置 (.env)
```bash
LLM_PROVIDER=openai    # openai, anthropic, deepseek
OPENAI_API_KEY=your_key_here
```

### 聚类参数 (config/settings.py)
```python
# 大组聚类
LARGE_CLUSTER_CONFIG = {
    "min_cluster_size": 30,
    "min_samples": 3,
}

# 小组聚类
SMALL_CLUSTER_CONFIG = {
    "min_cluster_size": 5,
    "min_samples": 2,
}
```

---

## 性能优化

### Embedding缓存
- 首次计算后缓存到NPZ文件
- 增量更新时只计算新短语
- 使用GPU加速（可选）

### 批量操作
- 使用 bulk_insert_mappings 批量插入
- 批次大小：1000条/批

### 数据库索引
- phrase字段：UNIQUE索引
- cluster_id_A, cluster_id_B: 普通索引
- source_type, first_seen_round: 普通索引

---

## 常见问题

### Q: 如何切换数据库？
A: 修改 .env 文件中的 DB_TYPE（mysql 或 sqlite）

### Q: 如何切换LLM提供商？
A: 修改 .env 文件中的 LLM_PROVIDER（openai, anthropic, deepseek）

### Q: 聚类结果太多/太少怎么办？
A: 调整 config/settings.py 中的 min_cluster_size 和 min_samples

### Q: Embedding计算很慢怎么办？
A: 1) 使用GPU加速 2) 调整batch_size 3) 使用缓存

---

## MVP成功标准

### 数据验证
- [x] phrases表有55,275条数据
- [x] cluster_meta表有307个大组（Level A）
- [x] 选中2个目标大组（测试）
- [x] cluster_meta表有6个小组（Level B，测试）
- [x] tokens表有79个tokens（测试）
- [ ] 生成10-20个validated需求卡片
- [ ] AI生成的需求卡片准确率 > 70%

### 可用性验证
- [ ] 从5万词产出10-20个可落地的需求想法
- [ ] 每个需求下有真实的搜索短语支撑
- [ ] 能够快速定位"哪些词属于同一需求"

---

## 未来迭代方向

### 第二轮迭代（+2周）
- Phase 5完整版：tokens词库完善
- Phase 7完整版：增量小组重聚类
- 数据表字段扩展：添加tags, main_tokens (JSON)

### 第三轮迭代（+2周）
- Web UI增强：ClusterSelector, DemandEditor
- 批量操作功能：合并需求、批量标记
- 导出工具：SEO词表、Landing Page素材

### 第四轮迭代（有产品后）
- Phase 6：商业化字段（revenue, landing_url）
- 数据可视化：需求地图、词云、趋势图
- 自动化Pipeline：定期扫描新词、自动推送报告

---

**文档版本**: v1.0
**更新日期**: 2026-01-08
**生成方式**: 基于代码分析自动生成

---

## Reddit板块分析功能设计决策 (Phase 6)

### 设计目标
- **独立性**: 完全独立的功能模块，不影响现有功能
- **复用性**: 复用现有LLM集成和数据库连接
- **可扩展性**: 支持未来添加更多分析维度

### 数据库设计
- **reddit_subreddits表**: 16个字段，存储板块信息和AI分析结果
- **ai_prompt_configs表**: 13个字段，存储可配置的AI提示词
- **标签存储**: 使用3个独立字段（tag1, tag2, tag3）而非JSON数组
  - 优点：便于索引和查询，支持全文搜索
  - 缺点：字段数量固定

### 核心功能
1. **数据导入**: 支持CSV/Excel无列名文件，自动按列顺序解析
2. **AI分析**: 批量分析（每批10条），生成标签和评分
3. **标签管理**: 支持按标签分组、筛选、编辑
4. **配置管理**: 在Web UI中配置AI提示词，支持多版本

### 技术选型
- **文件处理**: pandas（已有依赖）
- **数据验证**: pydantic（已有依赖）
- **UI组件**: Streamlit内置组件
- **去重策略**: 按板块名称去重，保留订阅数最多的记录

### 设计文档
- [数据库设计](docs/design/reddit-database-design.md)
- [API设计](docs/design/reddit-api-design.md)
- [系统架构](docs/design/reddit-architecture.md)

