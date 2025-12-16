# 基准输出指标（Baseline Metrics）

**创建时间**: 2025-12-16
**用途**: 重构前的基准输出，用于重构后对比验证

---

## A阶段聚类结果

**输入数据**: `merged_keywords_all.csv`
- 总短语数: 6,565条
- 预处理后: 6,344条

**聚类参数**:
- embedding_model: all-MiniLM-L6-v2
- clustering_method: hdbscan
- min_cluster_size: 13 (动态计算)
- min_samples: 3

**聚类结果**:
- 有效簇数: 63个
- 噪音点数: 3,786个
- 噪音比例: 59.7%
- 平均簇大小: 40.6条

**Top 5 最大的簇**:
1. cluster_id_A=42: 502条 (code - area codes)
2. cluster_id_A=39: 306条 (Best - promo codes)
3. cluster_id_A=35: 92条 (Best - cooking)
4. cluster_id_A=56: 79条 (Best - travel/beaches)
5. cluster_id_A=54: 77条 (Best - beauty/grooming)

**关键字段**:
- cluster_id_A: 0-63 + (-1噪音)
- cluster_size: 平均40.6
- example_phrases: 每个簇5个代表性短语
- total_frequency: 累计频次

---

## B阶段聚类结果

**输入数据**: `direction_keywords.csv`
- 选择方向数: 5个
- 实际处理: 2个方向 (code, Best)

**聚类参数**:
- 与A阶段相同
- 在方向内部进行二次聚类

**聚类结果**:
- 总短语数: 1,056条
- 子簇数: 9个
- 方向分布:
  - Best: 6个子簇，554条短语
  - code: 3个子簇，502条短语

**Top 5 子簇**:
1. code_B0: 480条 (area codes查询)
2. best_B0: 334条 (promo codes聚合)
3. best_B1: 38条 (cooking/dress)
4. best_B3: 35条 (cooking steak)
5. best_B2: 28条 (boiling)

**关键字段**:
- cluster_id_B: "direction_B{id}" 格式
- direction_keyword: 方向名称
- example_phrases: 每个子簇5个代表性短语

---

## 重构后对比检查清单

### A阶段核心指标
- [ ] 有效簇数: 应该在 60-70 之间
- [ ] 噪音比例: 应该在 55-65% 之间
- [ ] cluster_id=42 (code簇): 大小应该约500条
- [ ] cluster_id=39 (Best簇): 大小应该约300条
- [ ] example_phrases字段: 每个簇应该有5个代表性短语

### B阶段核心指标
- [ ] 子簇数: 应该在 8-10 之间
- [ ] 总短语数: 应该约1,000条
- [ ] code_B0子簇: 大小应该约480条
- [ ] best_B0子簇: 大小应该约330条
- [ ] cluster_id_B格式: "direction_B{id}"

### HTML输出
- [ ] cluster_summary_A3.html: 能正常打开，显示63个簇
- [ ] cluster_summary_B3.html: 能正常打开，显示9个子簇
- [ ] direction_keywords.html: 能正常打开，显示5个方向

---

## 对比方法

### 自动对比（推荐）
```python
import pandas as pd

# 对比A阶段
baseline_A = pd.read_csv('data/baseline/cluster_summary_A3.csv')
new_A = pd.read_csv('data/results/cluster_summary_A3.csv')

print(f"簇数变化: {len(baseline_A)} -> {len(new_A)}")
print(f"噪音簇检查: {(baseline_A['cluster_id_A']==-1).sum()} -> {(new_A['cluster_id_A']==-1).sum()}")

# 对比关键簇
key_clusters = [42, 39, 35, 56, 54]
for cid in key_clusters:
    old_size = baseline_A[baseline_A['cluster_id_A']==cid]['cluster_size'].values[0]
    new_size = new_A[new_A['cluster_id_A']==cid]['cluster_size'].values[0]
    diff = abs(new_size - old_size)
    status = "✅" if diff < 10 else "⚠️"
    print(f"{status} cluster {cid}: {old_size} -> {new_size} (diff: {diff})")
```

### 手工对比
1. 打开两个Excel文件
2. 检查Top 10簇的example_phrases是否基本一致
3. 检查总体统计指标（簇数、噪音比例）

---

**重要提示**:
- 由于聚类算法有随机性，完全一致的结果不太可能
- 关键是验证：簇数相近、主要簇的语义稳定、整体分布没有大变化
- 如果差异过大（>20%），需要检查参数是否被意外修改
