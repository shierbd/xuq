# 快速开始指南

## 🚀 5分钟上手

### 前提条件
- Python 3.8+
- MySQL/MariaDB 或 SQLite
- LLM API密钥（OpenAI/Anthropic/Deepseek任选一个）

### 安装步骤

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置数据库和API（编辑config/settings.py）
# 填写数据库连接信息和LLM API密钥

# 3. 初始化数据库
python -c "from storage.models import create_all_tables; create_all_tables()"

# 4. 准备数据
# 将CSV文件放到 data/raw/ 目录
```

---

## 📋 完整工作流（一键命令）

### 测试模式（免费，10分钟）

```bash
# Phase 1: 导入1000条测试数据
python scripts/run_phase1_import.py --limit 1000

# Phase 2: 大组聚类
python scripts/run_phase2_clustering.py

# Phase 3: 标记2个聚类为选中（手动编辑CSV或运行）
python scripts/import_selection.py

# Phase 4: 小组聚类（跳过LLM）
python scripts/run_phase4_demands.py --skip-llm --test-limit 2

# Phase 5: Token提取（跳过LLM）
python scripts/run_phase5_tokens.py --skip-llm --sample-size 1000 --min-frequency 5
```

**成本**: $0（跳过所有LLM调用）

---

### 生产模式（完整流程）

```bash
# Phase 1: 导入所有数据
python scripts/run_phase1_import.py

# Phase 2: 大组聚类（首次运行会生成embeddings）
python scripts/run_phase2_clustering.py

# Phase 3: 导出报告 → 人工筛选 → 导入
python scripts/import_selection.py data/output/clusters_levelA.csv

# Phase 4: 生成需求卡片（包含LLM）
python scripts/run_phase4_demands.py

# Phase 5: Token提取与分类（包含LLM）
python scripts/run_phase5_tokens.py --sample-size 10000 --min-frequency 3
```

**成本**: 约$1-2（OpenAI GPT-4o-mini）

---

## 🔧 关键配置

### config/settings.py 最小配置

```python
# 数据库配置
DATABASE_CONFIG = {
    'host': 'localhost',
    'user': 'your_user',
    'password': 'your_password',
    'database': 'search_demand_mining',
}

# LLM配置
LLM_PROVIDER = "openai"
LLM_CONFIG = {
    "openai": {
        "api_key": "sk-your-api-key",
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": 2000
    }
}

# Embedding配置
EMBEDDING_CONFIG = {
    "provider": "openai",
    "model": "text-embedding-3-small",
}
```

---

## 📊 输出文件速查

| Phase | 输出文件 | 用途 |
|-------|---------|------|
| Phase 1 | - | 数据导入到数据库 |
| Phase 2 | `data/output/clusters_levelA.csv` | 大组聚类CSV（待筛选） |
| Phase 2 | `data/cache/embeddings_round1.npz` | Embeddings缓存（重要！） |
| Phase 3 | `clusters_levelA.csv` (编辑后) | 筛选结果（is_selected列） |
| Phase 4 | `data/output/demands_draft.csv` | 需求卡片CSV（待审核） |
| Phase 5 | `data/output/tokens_extracted.csv` | Token CSV（待审核） |

---

## 🎯 常用命令速查

### 数据库操作

```bash
# 查看短语数量
python -c "from storage.repository import PhraseRepository; repo = PhraseRepository(); print(f'总短语数: {repo.get_phrase_count()}')"

# 查看聚类数量
python -c "from storage.repository import ClusterMetaRepository; repo = ClusterMetaRepository(); clusters = repo.get_all_clusters('A'); print(f'大组数: {len(clusters)}')"

# 查看选中的聚类
python -c "from storage.repository import ClusterMetaRepository; repo = ClusterMetaRepository(); selected = repo.get_selected_clusters('A'); print(f'选中: {len(selected)}个'); [print(f'  {c.cluster_id}: {c.main_theme} ({c.size}条)') for c in selected[:10]]"
```

### Phase 2 聚类参数调整

```bash
# 聚类太多（>100个）→ 增大最小聚类大小
# 编辑 config/settings.py:
LARGE_CLUSTER_CONFIG = {
    "min_cluster_size": 40,  # 从30增加到40
    "min_samples": 5,        # 从3增加到5
}

# 聚类太少（<40个）→ 减小最小聚类大小
LARGE_CLUSTER_CONFIG = {
    "min_cluster_size": 20,  # 从30减少到20
    "min_samples": 2,        # 从3减少到2
}

# 然后重新运行
python scripts/run_phase2_clustering.py --use-cache
```

### Phase 4 参数调整

```bash
# 测试单个大组
python scripts/run_phase4_demands.py --skip-llm --test-limit 1

# 小组太多/太小 → 调整 SMALL_CLUSTER_CONFIG
# 编辑 config/settings.py:
SMALL_CLUSTER_CONFIG = {
    "min_cluster_size": 10,  # 从5增加（减少小组数）
    "min_samples": 3,        # 从2增加
}
```

---

## 🐛 常见问题快速修复

### 问题1: 数据库连接失败

```bash
# 测试连接
python -c "from storage.repository import test_database_connection; test_database_connection()"

# 检查配置
# 1. MySQL服务是否启动
# 2. config/settings.py 中的用户名密码是否正确
# 3. 数据库是否已创建
```

### 问题2: LLM API调用失败

```bash
# 测试LLM连接
python -c "from ai.client import test_llm_client; test_llm_client()"

# 检查：
# 1. API密钥是否正确
# 2. API配额是否用尽
# 3. 网络连接是否正常
```

### 问题3: Embedding缓存损坏

```bash
# 重新生成embeddings（不使用缓存）
python scripts/run_phase2_clustering.py
```

### 问题4: 内存不足

```bash
# 使用采样模式
python scripts/run_phase5_tokens.py --sample-size 5000  # 从10000减少

# 或分批处理
python scripts/run_phase4_demands.py --test-limit 3  # 每次处理3个大组
```

---

## 📖 详细文档

### 核心文档

1. **[完整使用说明 USER_GUIDE.md](docs/USER_GUIDE.md)**
   - 从安装到运行的完整指南
   - 每个Phase的详细说明
   - 配置参数详解
   - API成本管理

2. **[Phase 4 实施摘要](docs/Phase4_Implementation_Summary.md)**
   - 小组聚类技术细节
   - cluster_id_B编码方案
   - 需求卡片生成流程

3. **[Phase 5 实施摘要](docs/Phase5_Implementation_Summary.md)**
   - Token提取算法
   - 停用词过滤
   - LLM分类标准

### 配置文档

- [MVP版本实施方案](docs/MVP版本实施方案.md)
- [数据安全保护说明](docs/数据安全保护说明.md)

---

## 💰 成本参考

### 典型项目（55,275条短语）

| 项目 | OpenAI | Anthropic | Deepseek |
|------|--------|-----------|----------|
| Phase 2 Embedding | $0.03 | N/A | N/A |
| Phase 4 需求卡片（28个大组×6个小组） | $0.50 | $10.00 | $0.07 |
| Phase 5 Token分类（1000个tokens） | $0.05 | $1.00 | $0.01 |
| **总计** | **$0.58** | **$11.00** | **$0.08** |

**推荐配置**: OpenAI GPT-4o-mini（性价比最高）

---

## ✅ 验证检查清单

运行完毕后，确认：

- [ ] phrases表有50,000+条数据
- [ ] cluster_meta表有Level A聚类（60-100个）
- [ ] cluster_meta表有Level B聚类（已选中大组的小组）
- [ ] 至少选中10-15个大组（is_selected=True）
- [ ] demands表有20-50个需求卡片
- [ ] tokens表有500-2000个tokens
- [ ] data/output/目录有CSV报告
- [ ] data/cache/目录有embeddings缓存

---

## 🆘 获取帮助

### 出现问题？

1. **查看错误日志** - 脚本会输出详细的错误信息
2. **查阅文档** - [USER_GUIDE.md](docs/USER_GUIDE.md) 有常见问题解答
3. **检查配置** - 确认 config/settings.py 配置正确
4. **测试模式** - 使用 `--skip-llm` 和 `--test-limit` 快速定位问题

### 需要更多帮助？

- 查看 [Phase 4 实施摘要](docs/Phase4_Implementation_Summary.md) 的FAQ部分
- 查看 [Phase 5 实施摘要](docs/Phase5_Implementation_Summary.md) 的FAQ部分
- 查看 [MVP版本实施方案](docs/MVP版本实施方案.md) 的详细说明

---

## 🎉 成功标志

当你看到以下输出，说明系统运行成功：

```
✅ Phase 1 完成！
  - 导入短语: 55,275
  - 数据报告: data/output/phase1_import_report.txt

✅ Phase 2 完成！
  - 生成聚类: 307 个
  - 聚类CSV: data/output/clusters_levelA.csv

✅ Phase 4 完成！
  - 处理大组: 28/28
  - 生成需求: 156
  - 需求CSV: data/output/demands_draft.csv

✅ Phase 5 完成！
  - 提取tokens: 856
  - Token CSV: data/output/tokens_extracted.csv
```

---

**下一步**: 打开 `data/output/clusters_levelA.csv` 开始人工筛选！

**祝你挖掘出好需求！** 🚀
