# 实验 1: Cosine Metric 测试结果

**实验日期**: 2026-02-02
**实验目的**: 测试 L2 归一化 + euclidean（等价于 cosine）对聚类结果的影响

---

## 实验设置

### 方法
- **之前**: metric='euclidean'（无归一化）
- **现在**: L2 归一化 + metric='euclidean'（等价于 cosine）

### 参数
- 三阶段聚类
- stage1_min_size: 10
- stage2_min_size: 5
- stage3_min_size: 3
- cluster_selection_method: leaf
- cluster_selection_epsilon: 0.3

---

## 实验结果

### 对比表

| 指标 | Euclidean (无归一化) | Cosine (L2归一化) | 变化 |
|------|---------------------|-------------------|------|
| 总商品数 | 15,792 | 15,792 | - |
| 生成簇数 | 1,412 | 1,416 | +4 (+0.28%) |
| 噪音点数 | 4,620 | 4,645 | +25 (+0.54%) |
| 噪音比例 | 29.26% | 29.41% | +0.15% |

### 各阶段对比

| 阶段 | Euclidean 簇数 | Cosine 簇数 | 变化 |
|------|---------------|-------------|------|
| Stage 1 (主要簇) | 224 | 224 | 0 |
| Stage 2 (次级簇) | 463 | 462 | -1 |
| Stage 3 (微型簇) | 725 | 730 | +5 |

---

## 结果分析

### 1. 几乎没有变化

**关键发现**: L2 归一化（cosine-equivalent）对聚类结果的影响**极小**

- 簇数量变化: +4 (0.28%)
- 噪音点变化: +25 (0.54%)
- 各阶段簇数基本相同

### 2. 为什么没有显著改善？

可能的原因:

1. **Sentence Transformers 的向量已经接近归一化**
   - all-mpnet-base-v2 模型可能输出的向量本身就接近单位向量
   - 因此额外的 L2 归一化影响不大

2. **问题不在 metric，而在其他参数**
   - cluster_selection_method='leaf' 太激进
   - cluster_selection_epsilon=0.3 可能不合适
   - min_cluster_size 参数可能需要调整

3. **数据特性**
   - 商品名称的语义分布可能本身就很分散
   - 无论用什么距离度量，都难以形成大簇

### 3. 与 GPT 预期的对比

**GPT 预期**:
- 簇更稳定
- 微簇减少
- 聚类质量提升

**实际结果**:
- ❌ 簇数量几乎没变
- ❌ 微簇数量反而略增（+5）
- ❌ 没有显著质量提升

---

## 结论

### 主要结论

> **Metric 不是主要问题**。L2 归一化（cosine-equivalent）对聚类结果影响极小，说明问题的根源在其他地方。

### 下一步行动

根据 GPT 的分析，应该重点关注:

1. **✅ 优先**: cluster_selection_method='leaf' → 'eom'
   - 这是 GPT 认为的第二大问题
   - leaf 太激进，导致微簇爆炸
   - eom 更保守，生成更稳定的主题簇

2. **✅ 优先**: cluster_selection_epsilon=0.3 → 0.0
   - 关闭这个不可靠的参数
   - 只靠 min_cluster_size/min_samples 控制

3. **✅ 重要**: 实现双文本策略
   - 去除颜色/材质/风格词
   - 按需求主题聚类，而非属性聚类

---

## 实验数据

### 完整输出

```
Total products: 15792
Clusters: 1416
  - Primary clusters (>=10): 224
  - Secondary clusters (5-9): 462
  - Micro clusters (3-4): 730
Noise points: 4645
Noise ratio: 29.41%
```

### 与之前对比

```
Previous (euclidean):
  Clusters: 1412
  Noise: 4620 (29.26%)

Current (cosine-equivalent):
  Clusters: 1416 (+4)
  Noise: 4645 (+25)
```

---

## 下一个实验

**实验 2**: 测试 stage1 eom vs leaf

**假设**: 将 Stage 1 的 cluster_selection_method 从 'leaf' 改为 'eom' 会显著减少微簇数量，提升主题簇质量。

---

**创建者**: Claude Sonnet 4.5
**实验时间**: 2026-02-02
