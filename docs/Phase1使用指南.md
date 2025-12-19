# Phase 1 使用指南

## 📊 数据结果位置

### 1. 数据库（主要存储）

**位置**: MySQL数据库
```
数据库名: keyword_clustering
表名: phrases
记录数: 55,275条
```

**查看数据**:
```bash
# 查看总数
mysql -u root -p123456 -e "SELECT COUNT(*) FROM keyword_clustering.phrases;"

# 查看前10条
mysql -u root -p123456 -e "SELECT phrase, frequency, volume, source_type FROM keyword_clustering.phrases LIMIT 10;"

# 按来源统计
mysql -u root -p123456 -e "SELECT source_type, COUNT(*) as count FROM keyword_clustering.phrases GROUP BY source_type;"
```

### 2. CSV文件（备份/查看）

**位置**: `data/processed/integrated_round1.csv`

**查看方式**:
- Excel打开: 双击文件
- 命令行查看: `type data\processed\integrated_round1.csv | more`
- 使用pandas:
  ```python
  import pandas as pd
  df = pd.read_csv('data/processed/integrated_round1.csv')
  print(df.head(20))
  ```

## 📁 运行代码位置

### Phase 1 入口脚本
**文件**: `scripts/run_phase1_import.py`

## 🚀 使用场景

### 场景1: 查看已导入的数据

运行查看脚本:
```bash
python view_phase1_results.py
```

输出包括:
- 总体统计信息
- 按数据源分布
- 高频短语Top 20
- 各数据源样本
- 聚类状态

### 场景2: 重新导入数据（清空重来）

```bash
# 1. 清空数据库表
mysql -u root -p123456 -e "TRUNCATE TABLE keyword_clustering.phrases;"

# 2. 重新运行导入
python scripts/run_phase1_import.py

# 3. 验证导入
python view_phase1_results.py
```

### 场景3: 导入新一轮数据（增量更新）

```bash
# 1. 将新数据放到 data/raw/ 目录

# 2. 运行增量导入（round_id=2）
python scripts/run_phase1_import.py --round-id 2

# 注意：相同短语会被忽略（unique约束），只会导入新短语
```

### 场景4: 测试导入（不写入数据库）

```bash
# 使用dry-run模式
python scripts/run_phase1_import.py --dry-run

# 会显示统计信息但不插入数据库
```

### 场景5: 导出数据到Excel分析

**方法1: 直接使用CSV文件**
```bash
# 文件已经存在
start data\processed\integrated_round1.csv
```

**方法2: 从数据库导出特定数据**
```python
# export_phrases.py
import pandas as pd
from storage.repository import PhraseRepository
from storage.models import Phrase

with PhraseRepository() as repo:
    # 导出SEMRUSH数据（有搜索量）
    semrush = repo.session.query(Phrase).filter(
        Phrase.source_type == 'semrush'
    ).all()

    df = pd.DataFrame([{
        'phrase': p.phrase,
        'frequency': p.frequency,
        'volume': p.volume,
        'seed_word': p.seed_word,
    } for p in semrush])

    df.to_excel('data/output/semrush_phrases.xlsx', index=False)
    print(f"已导出 {len(df)} 条SEMRUSH数据")
```

### 场景6: 查询特定短语

```python
# query_phrase.py
from storage.repository import PhraseRepository

with PhraseRepository() as repo:
    # 查询单个短语
    phrase = repo.get_phrase_by_text("how to change a tire")
    if phrase:
        print(f"短语: {phrase.phrase}")
        print(f"频次: {phrase.frequency}")
        print(f"搜索量: {phrase.volume}")
        print(f"来源: {phrase.source_type}")
        print(f"聚类ID: {phrase.cluster_id_A}")
```

### 场景7: 按种子词查询

```python
# query_by_seed.py
from storage.models import Phrase
from storage.repository import PhraseRepository

with PhraseRepository() as repo:
    # 查询特定种子词的所有短语
    phrases = repo.session.query(Phrase).filter(
        Phrase.seed_word == 'connector'
    ).order_by(Phrase.frequency.desc()).all()

    print(f"种子词 'connector' 的短语数: {len(phrases)}")
    for p in phrases[:10]:
        print(f"  - {p.phrase} (频次:{p.frequency})")
```

## 📊 数据统计摘要

### 导入数据概况
- **总记录数**: 55,275条
- **数据源分布**:
  - SEMRUSH: 8,973条 (16.2%) - 有搜索量数据
  - Dropdown: 45,866条 (83.0%) - 下拉词
  - Related Search: 436条 (0.8%) - 相关搜索

### 高频短语Top 5
1. how to change a tire - 1,830,000
2. image search techniques - 1,000,000
3. list crawler - 550,000
4. online casinos toptiercasinos.com 2025 - 368,000
5. 213 area code - 368,000

### 数据质量
- 有搜索量的记录: 8,973条 (16.2%)
- 平均频次: 2,011
- 当前状态: 全部标记为 `unseen`，等待Phase 2聚类处理

## 🔧 常见问题

### Q1: 如何修改数据库密码？
修改 `.env` 文件中的 `DB_PASSWORD=123456`

### Q2: 如何使用SQLite代替MySQL？
修改 `.env` 文件:
```
DB_TYPE=sqlite
```
然后重新运行 `python init_database.py`

### Q3: 数据导入失败怎么办？
```bash
# 1. 检查数据库连接
mysql -u root -p123456 -e "SELECT 1;"

# 2. 检查数据表是否存在
python init_database.py

# 3. 使用dry-run模式测试
python scripts/run_phase1_import.py --dry-run
```

### Q4: 如何备份数据？
```bash
# 备份数据库
mysqldump -u root -p123456 keyword_clustering > backup.sql

# 或复制CSV文件
copy data\processed\integrated_round1.csv backup\
```

### Q5: 如何恢复数据？
```bash
# 从SQL备份恢复
mysql -u root -p123456 keyword_clustering < backup.sql
```

## 📌 下一步

数据已准备完成，可以进行：
1. **Phase 2**: 运行 `python scripts/run_phase2_clustering.py` 进行大组聚类
2. **数据分析**: 使用 `view_phase1_results.py` 查看统计信息
3. **自定义查询**: 参考上述代码示例编写自己的查询脚本

## 📚 相关文件

- `scripts/run_phase1_import.py` - Phase 1主脚本
- `view_phase1_results.py` - 查看结果脚本
- `core/data_integration.py` - 数据整合模块
- `storage/repository.py` - 数据库操作模块
- `storage/models.py` - 数据表模型
- `.env` - 配置文件（包含数据库密码）
