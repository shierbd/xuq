# 项目上下文

> 本文档为 Claude Code 提供项目背景和开发上下文信息

## 项目背景

**项目名称**: 词根聚类需求挖掘系统 (Keyword Clustering & Demand Mining System)

**项目目标**: 从大量英文关键词中通过语义聚类自动发现产品需求方向

**核心理念**: 单词 → 短语 → 语义簇 → 需求方向 → MVP验证

**当前版本**: MVP v1.0

**开发状态**: Phase 1-5 已完成并测试验证

---

## 技术栈

### 后端
- **语言**: Python 3.8+
- **数据库**: MySQL/MariaDB (推荐) 或 SQLite
- **ORM**: SQLAlchemy 2.0+
- **Web框架**: Streamlit

### 机器学习
- **语义向量**: sentence-transformers (all-MiniLM-L6-v2)
- **聚类算法**:
  - HDBSCAN (密度聚类)
  - Louvain (图聚类)
  - K-Means (质心聚类)
- **科学计算**: numpy, pandas, scikit-learn

### LLM集成
- OpenAI API (GPT-4, GPT-3.5)
- Anthropic API (Claude)
- DeepSeek API

### 自然语言处理
- NLTK (词性标注)
- deep-translator (翻译服务)

---

## 项目结构

```
词根聚类需求挖掘/
├── config/              # 统一配置
│   └── settings.py      # 数据库、聚类、LLM配置
├── core/                # 核心业务逻辑
│   ├── data_integration.py
│   ├── clustering.py
│   ├── embedding.py
│   ├── llm_service.py
│   ├── token_extraction.py
│   └── ...
├── storage/             # 数据库访问层
│   ├── models.py        # SQLAlchemy模型
│   └── repository.py    # CRUD封装
├── ai/                  # LLM集成
│   └── client.py        # LLM API调用封装
├── ui/                  # Web UI界面
│   └── pages/           # 各Phase页面模块
├── scripts/             # 入口脚本
│   ├── run_phase1_import.py
│   ├── run_phase2_clustering.py
│   └── ...
├── utils/               # 工具函数
│   ├── helpers.py
│   └── token_extractor.py
├── data/                # 数据目录（.gitignore排除）
│   ├── raw/             # 原始数据
│   ├── processed/       # 处理后数据
│   ├── output/          # 导出报告
│   └── cache/           # Embedding缓存
├── docs/                # 文档
│   ├── requirements.md
│   └── design/
│       ├── architecture.md
│       └── database-design.md
├── tests/               # 测试
├── web_ui.py            # Streamlit Web界面入口
├── requirements.txt     # Python依赖
└── .env                 # 环境变量（不提交）
```

---

## 开发规范

### 代码风格
- 遵循 PEP 8 规范
- 使用类型注解
- 添加 docstring
- 函数名使用 snake_case
- 类名使用 PascalCase

### 提交规范
```
<type>: <subject>

feat: 新功能
fix: 修复bug
docs: 文档更新
refactor: 重构代码
test: 测试相关
chore: 构建/工具相关
```

### 测试要求
- 单元测试覆盖率 > 55%
- 使用 pytest 进行测试
- 测试文件命名: `test_*.py`
- 使用 fixtures 管理测试数据

---

## 常用命令

### 环境设置
```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填写数据库和API密钥

# 创建数据库表
python
>>> from storage.models import create_all_tables
>>> create_all_tables()
>>> exit()
```

### 运行Web UI（推荐）
```bash
# 启动可视化界面
streamlit run web_ui.py

# 访问 http://localhost:8501
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

# 运行特定测试
pytest tests/test_clustering.py

# 生成覆盖率报告
pytest --cov=core --cov=storage --cov=ai --cov=utils
```

### 数据安全检查
```bash
# Windows
powershell -ExecutionPolicy Bypass -File .\scripts\check_before_push.ps1

# Linux/Mac
bash scripts/check_before_push.sh
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
ANTHROPIC_API_KEY=your_key_here
DEEPSEEK_API_KEY=your_key_here
```

### 聚类参数 (config/settings.py)
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

---

## 工作流程

### Phase 0: 词根管理（可选）
- 词根标注和分类
- 词性标注（NLTK）
- 翻译（deep-translator）

### Phase 1: 数据导入
- 从 SEMRUSH、下拉词、相关搜索导入数据
- 数据清洗和去重
- 填充 phrases 表

### Phase 2: 大组聚类
- 生成语义向量（Sentence Transformers）
- 执行聚类（HDBSCAN/Louvain）
- 更新 phrases.cluster_id_A
- 生成 cluster_meta (Level A)

### Phase 3: 大组筛选
- AI生成聚类主题标签
- 导出HTML/CSV报告
- 人工打分筛选（1-5分）
- 导入筛选结果

### Phase 4: 小组聚类 + 需求卡片
- 对选中大组执行小组聚类
- 更新 phrases.cluster_id_B
- 生成 cluster_meta (Level B)
- LLM生成需求卡片
- 导出CSV供人工审核

### Phase 5: Token提取
- N-gram提取（1-4 gram）
- 停用词过滤
- LLM分类（intent/action/object等）
- 导出CSV供人工审核

---

## 数据库表

### 核心表
1. **phrases**: 短语总库（55,275条）
2. **cluster_meta**: 聚类元数据（307个大组）
3. **demands**: 需求卡片（20-50个）
4. **tokens**: Token词库（数千个）
5. **seed_words**: 种子词管理
6. **word_segments**: 分词结果缓存
7. **segmentation_batches**: 分词批次记录

---

## 重要文档索引

### 必读文档
- [README.md](../README.md) - 项目概述和快速开始
- [需求文档](../docs/requirements.md) - 功能需求和用户故事
- [架构设计](../docs/design/architecture.md) - 系统架构和模块划分
- [数据库设计](../docs/design/database-design.md) - 数据表结构和关系

### 实施文档
- [MVP版本实施方案](../docs/MVP版本实施方案.md) - 完整的MVP开发计划
- [Phase4实施摘要](../docs/Phase4_Implementation_Summary.md) - 小组聚类+需求卡片
- [Phase5实施摘要](../docs/Phase5_Implementation_Summary.md) - Token提取与分类

### 使用指南
- [Web UI使用说明](../WEB_UI_README.md) - Web界面操作指南
- [完整使用流程指南](../docs/完整使用流程指南.md) - 端到端使用流程

---

## 开发注意事项

### 数据安全
- ⚠️ **所有数据文件不推送到GitHub**
- data/ 目录已在 .gitignore 中排除
- .env 文件不提交
- 推送前运行安全检查脚本

### 性能优化
- Embedding缓存避免重复计算
- 批量操作使用 bulk_insert_mappings
- 数据库查询使用索引
- 大数据量使用分批处理

### 错误处理
- 使用 try-except 捕获异常
- 记录详细的错误日志
- 提供友好的错误提示
- 数据库操作使用事务

### 日志记录
- 使用 utils/logger.py 统一日志
- 日志级别: DEBUG, INFO, WARNING, ERROR
- 关键操作记录日志
- 日志文件按日期轮转

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

### Q: 如何查看聚类结果？
A: 1) Web UI查看 2) 查看HTML报告 3) 直接查询数据库

---

## 联系方式

- **GitHub**: https://github.com/shierbd/xuq
- **文档**: docs/ 目录

---

**文档版本**: v1.0
**更新日期**: 2026-01-08
