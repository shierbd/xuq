# Stage 2/3 重新设计方案

**日期**: 2026-02-02
**目标**: 消除677个微型簇，将簇数量从1,349降低到400-600

---

## 🎯 核心思路

### 当前问题

**Stage 2/3 制造微型簇**：
```
Stage 1: 生成215个主要簇 + 10,957个噪音点
Stage 2: 对噪音点聚类 → 创建461个次级簇 + 7,299个噪音点
Stage 3: 对噪音点聚类 → 创建677个微型簇 + 4,631个噪音点

结果: 1,349个簇（太多！）
```

### 新设计

**归并 + 质量门控**：
```
Stage 1: 生成主要簇（保持不变）
Stage 2: 归并到最近主题簇（不创建新簇）
Stage 3: 质量门控（只保留可命名簇）

预期: 300-500个簇
```

---

## 📐 Stage 2: 归并策略

### 算法设计

**目标**: 将噪音点归并到最近的主题簇，而不是创建新簇

**步骤**:

1. **计算簇中心（Centroids）**
   ```python
   for cluster_id in stage1_clusters:
       cluster_points = embeddings[labels == cluster_id]
       centroid = np.mean(cluster_points, axis=0)
       centroids[cluster_id] = centroid
   ```

2. **对每个噪音点找最近簇**
   ```python
   for noise_point in stage1_noise:
       # 计算与所有簇中心的相似度
       similarities = cosine_similarity(noise_point, centroids)

       # 找到最相似的簇
       nearest_cluster = argmax(similarities)
       max_similarity = similarities[nearest_cluster]

       # 如果相似度足够高，归并
       if max_similarity > threshold:
           assign_to_cluster(noise_point, nearest_cluster)
       else:
           keep_as_noise(noise_point)
   ```

3. **阈值设置**
   - **高阈值 (0.7-0.8)**: 严格归并，保留更多噪音
   - **中阈值 (0.5-0.6)**: 平衡归并，推荐
   - **低阈值 (0.3-0.4)**: 激进归并，可能误归并

   **建议**: 从 0.5 开始，根据结果调整

### 预期效果

**归并前**:
- Stage 1: 215个主要簇 + 10,957个噪音点

**归并后** (阈值=0.5):
- 预计归并: 6,000-8,000个点
- 剩余噪音: 3,000-5,000个点
- 不再创建461+677=1,138个新簇

---

## 🔍 Stage 3: 质量门控

### 算法设计

**目标**: 只保留"可命名"的高质量簇

**质量指标**:

#### 1. 簇内一致性（Cohesion）

**定义**: 簇内点之间的平均相似度

```python
def calculate_cohesion(cluster_points):
    """计算簇内一致性"""
    n = len(cluster_points)
    if n < 2:
        return 0.0

    # 计算所有点对之间的相似度
    similarities = []
    for i in range(n):
        for j in range(i+1, n):
            sim = cosine_similarity(cluster_points[i], cluster_points[j])
            similarities.append(sim)

    return np.mean(similarities)
```

**阈值**: cohesion > 0.5（中等一致性）

#### 2. 簇大小（Size）

**定义**: 簇中的商品数量

```python
def check_size(cluster_size, min_size=3):
    """检查簇大小"""
    return cluster_size >= min_size
```

**阈值**: size >= 3（至少3个商品）

#### 3. 簇区分度（Separation）

**定义**: 簇中心与最近簇中心的距离

```python
def calculate_separation(cluster_centroid, all_centroids):
    """计算簇区分度"""
    # 计算与所有其他簇中心的距离
    distances = []
    for other_centroid in all_centroids:
        if not np.array_equal(cluster_centroid, other_centroid):
            dist = 1 - cosine_similarity(cluster_centroid, other_centroid)
            distances.append(dist)

    # 返回最近距离
    return min(distances) if distances else 1.0
```

**阈值**: separation > 0.3（与最近簇有明显区分）

### 质量门控流程

```python
def quality_gate(cluster_id, cluster_points, all_centroids):
    """质量门控"""
    # 检查簇大小
    if len(cluster_points) < 3:
        return False, "size_too_small"

    # 检查簇内一致性
    cohesion = calculate_cohesion(cluster_points)
    if cohesion < 0.5:
        return False, "low_cohesion"

    # 检查簇区分度
    centroid = np.mean(cluster_points, axis=0)
    separation = calculate_separation(centroid, all_centroids)
    if separation < 0.3:
        return False, "low_separation"

    return True, "passed"
```

### 预期效果

**门控前**:
- 215个主要簇（Stage 1）

**门控后**:
- 预计保留: 150-200个高质量簇
- 淘汰: 15-65个低质量簇
- 淘汰的簇中的商品标记为噪音

---

## 📊 整体流程

### 完整流程图

```
输入: 15,792个商品

↓

[Stage 1] 主要聚类 (min_size=10)
  → 215个主要簇
  → 10,957个噪音点

↓

[Stage 2] 归并策略 (threshold=0.5)
  → 归并 6,000-8,000个点到主要簇
  → 剩余 3,000-5,000个噪音点
  → 不创建新簇

↓

[Stage 3] 质量门控
  → 检查215个簇的质量
  → 保留 150-200个高质量簇
  → 淘汰 15-65个低质量簇

↓

输出: 150-200个高质量簇 + 3,000-5,000个噪音点
```

### 预期结果

| 指标 | 当前 (Phase 2) | 预期 (Stage 2/3重新设计) | 改善 |
|------|---------------|------------------------|------|
| **总簇数** | 1,349 | 150-200 | -85% to -89% |
| **主要簇** | 211 (15.6%) | 150-200 (100%) | +84% |
| **微型簇** | 677 (50.2%) | 0 (0%) | -100% |
| **噪音点** | 4,631 (29.3%) | 3,000-5,000 (19-32%) | 可接受 |

---

## 🔧 实现细节

### 关键函数

#### 1. 计算簇中心
```python
def calculate_cluster_centroids(
    embeddings: np.ndarray,
    labels: np.ndarray
) -> Dict[int, np.ndarray]:
    """计算每个簇的中心向量"""
    centroids = {}
    unique_labels = set(labels) - {-1}

    for label in unique_labels:
        cluster_mask = labels == label
        cluster_points = embeddings[cluster_mask]
        centroid = np.mean(cluster_points, axis=0)
        centroids[label] = centroid

    return centroids
```

#### 2. 归并噪音点
```python
def merge_noise_to_clusters(
    embeddings: np.ndarray,
    labels: np.ndarray,
    centroids: Dict[int, np.ndarray],
    threshold: float = 0.5
) -> np.ndarray:
    """将噪音点归并到最近的簇"""
    from sklearn.metrics.pairwise import cosine_similarity

    new_labels = labels.copy()
    noise_mask = labels == -1
    noise_indices = np.where(noise_mask)[0]

    for idx in noise_indices:
        noise_point = embeddings[idx].reshape(1, -1)

        # 计算与所有簇中心的相似度
        max_sim = -1
        best_cluster = -1

        for cluster_id, centroid in centroids.items():
            centroid_reshaped = centroid.reshape(1, -1)
            sim = cosine_similarity(noise_point, centroid_reshaped)[0][0]

            if sim > max_sim:
                max_sim = sim
                best_cluster = cluster_id

        # 如果相似度足够高，归并
        if max_sim > threshold:
            new_labels[idx] = best_cluster

    return new_labels
```

#### 3. 质量门控
```python
def apply_quality_gate(
    embeddings: np.ndarray,
    labels: np.ndarray,
    min_size: int = 3,
    min_cohesion: float = 0.5,
    min_separation: float = 0.3
) -> np.ndarray:
    """应用质量门控，淘汰低质量簇"""
    from sklearn.metrics.pairwise import cosine_similarity

    new_labels = labels.copy()
    unique_labels = set(labels) - {-1}

    # 计算所有簇中心
    centroids = calculate_cluster_centroids(embeddings, labels)

    for cluster_id in unique_labels:
        cluster_mask = labels == cluster_id
        cluster_points = embeddings[cluster_mask]

        # 检查簇大小
        if len(cluster_points) < min_size:
            new_labels[cluster_mask] = -1
            continue

        # 检查簇内一致性
        cohesion = calculate_cohesion(cluster_points)
        if cohesion < min_cohesion:
            new_labels[cluster_mask] = -1
            continue

        # 检查簇区分度
        separation = calculate_separation(
            centroids[cluster_id],
            list(centroids.values())
        )
        if separation < min_separation:
            new_labels[cluster_mask] = -1
            continue

    return new_labels
```

---

## 🎯 参数调优

### 关键参数

| 参数 | 默认值 | 调优范围 | 影响 |
|------|--------|---------|------|
| **merge_threshold** | 0.5 | 0.4-0.7 | 归并严格程度 |
| **min_cohesion** | 0.5 | 0.4-0.6 | 簇内一致性要求 |
| **min_separation** | 0.3 | 0.2-0.4 | 簇区分度要求 |
| **min_size** | 3 | 3-5 | 最小簇大小 |

### 调优策略

**如果簇太多** (>500):
- 提高 merge_threshold (0.5 → 0.6)
- 提高 min_cohesion (0.5 → 0.6)
- 提高 min_separation (0.3 → 0.4)

**如果簇太少** (<300):
- 降低 merge_threshold (0.5 → 0.4)
- 降低 min_cohesion (0.5 → 0.4)
- 降低 min_separation (0.3 → 0.2)

---

## 📋 实施计划

### 第一步：实现核心函数
- [ ] calculate_cluster_centroids()
- [ ] merge_noise_to_clusters()
- [ ] calculate_cohesion()
- [ ] calculate_separation()
- [ ] apply_quality_gate()

### 第二步：集成到聚类服务
- [ ] 修改 perform_three_stage_clustering()
- [ ] 添加 use_merge_strategy 参数
- [ ] 添加 use_quality_gate 参数

### 第三步：测试验证
- [ ] 运行测试（默认参数）
- [ ] 分析结果
- [ ] 调优参数（如需要）

### 第四步：文档和提交
- [ ] 更新文档
- [ ] 生成测试报告
- [ ] 提交到Git

---

**创建者**: Claude Sonnet 4.5
**创建日期**: 2026-02-02
**预计实施时间**: 2-3小时
