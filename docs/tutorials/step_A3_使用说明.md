# 步骤A3使用说明（语义聚类）

## 🎯 功能说明

步骤A3将合并后的6,565条短语，通过语义聚类自动分组成40-60个需求方向簇。

**输入**：`merged_keywords_all.csv`（步骤A2的输出）
**输出**：
- `stageA_clusters.csv`（带簇标签的完整数据）
- `clusters_summary_stageA.csv`（簇级统计信息）

---

## 📋 前提条件

### 1. 确保步骤A2已完成

检查是否存在输入文件：
```bash
# 查看文件是否存在
dir D:\xiangmu\词根聚类需求挖掘\data\merged_keywords_all.csv
```

如果不存在，请先运行步骤A2：
```bash
python step_A2_merge_csv.py
```

### 2. 确保依赖已安装

如果还没安装依赖，运行：
```bash
# 方式1：使用批处理脚本（推荐）
install_dependencies.bat

# 方式2：使用requirements文件
pip install -r requirements.txt
```

---

## 🚀 基本使用（三步走）

### **第1步：进入工作目录**

```bash
cd D:\xiangmu\词根聚类需求挖掘\功能实现
```

### **第2步：运行聚类脚本**

```bash
python step_A3_clustering.py
```

### **第3步：等待完成**

预计耗时：**5-10分钟**（CPU）或 **1-2分钟**（GPU）

---

## 📺 运行过程示例

运行后会显示以下进度：

```
==================================================
              步骤A3：语义聚类
==================================================

配置信息:
  输入文件: D:\xiangmu\词根聚类需求挖掘\data\merged_keywords_all.csv
  Embedding模型: all-MiniLM-L6-v2
  聚类方法: hdbscan
  最小簇大小: 5
  最小样本数: 2

--------------------------------------------------
1. 加载数据
--------------------------------------------------
加载文件: D:\xiangmu\词根聚类需求挖掘\data\merged_keywords_all.csv
成功读取 6,565 行数据

--------------------------------------------------
2. 数据预处理
--------------------------------------------------
待聚类短语数: 6,565

--------------------------------------------------
3. 生成Embeddings
--------------------------------------------------
正在加载embedding模型: all-MiniLM-L6-v2
模型加载完成，使用设备: cpu
正在生成 6,565 条短语的embedding...

Batches: 100%|███████████████████| 206/206 [02:15<00:00,  1.52it/s]

Embedding生成完成，维度: (6565, 384)

--------------------------------------------------
4. 执行聚类
--------------------------------------------------
正在使用HDBSCAN聚类...
  min_cluster_size=5
  min_samples=2
聚类完成:
  簇数量: 52
  噪音点数: 892 (13.6%)

--------------------------------------------------
5. 计算簇级统计
--------------------------------------------------
簇级统计完成，共 53 个簇

--------------------------------------------------
6. 保存结果
--------------------------------------------------
保存文件: D:\xiangmu\词根聚类需求挖掘\data\stageA_clusters.csv
保存文件: D:\xiangmu\词根聚类需求挖掘\data\clusters_summary_stageA.csv

==================================================
              聚类结果摘要
==================================================
总短语数: 6,565
簇数量: 53
噪音点数: 892 (13.6%)

--------------------------------------------------
Top 10 最大的簇
--------------------------------------------------
  簇   5:   234 条短语, 频次=  456, 种子词=[compress,convert]...
  簇  12:   198 条短语, 频次=  389, 种子词=[compress,edit]...
  簇   3:   167 条短语, 频次=  312, 种子词=[convert]...
  ...

==================================================
            步骤A3执行成功！
==================================================

下一步：运行 step_A4_llm_cluster_summary.py 进行簇级理解
```

---

## 📂 输出文件说明

### **文件1：stageA_clusters.csv**

带簇标签的完整数据（所有原始信息都保留）

```csv
phrase,seed_word,Volume,frequency,source_file,cluster_id
compress pdf,compress,12100,3,compress_broad-match_us_2025-12-12.csv,5
pdf compressor,compress,8100,2,compress_broad-match_us_2025-12-12.csv,5
compress video,compress,5400,1,compress_broad-match_us_2025-12-12.csv,12
video compressor,compress,4100,1,compress_broad-match_us_2025-12-12.csv,12
random phrase,other,100,1,other_broad-match_us_2025-12-12.csv,-1
```

**说明**：
- 只是比步骤A2多了一列 `cluster_id`
- 所有原始短语、搜索量、种子词等信息100%保留
- `cluster_id = -1` 表示噪音点（未分类的短语）

### **文件2：clusters_summary_stageA.csv**

簇级统计信息

```csv
cluster_id,cluster_size,total_frequency,seed_words_in_cluster,total_volume
5,234,456,compress,450000
12,198,389,"compress,edit",380000
3,167,312,convert,310000
-1,892,1023,"compress,convert,edit,other",120000
```

**说明**：
- `cluster_size`：簇中短语数量
- `total_frequency`：簇中所有短语的频次总和
- `seed_words_in_cluster`：簇中包含哪些种子词
- `total_volume`：簇中所有短语的搜索量总和
- 按 `total_frequency` 降序排列

---

## ⚙️ 自定义配置

### 调整聚类参数

编辑 `config.py` 中的 `A3_CONFIG`：

```python
A3_CONFIG = {
    # 聚类参数
    "clustering_method": "hdbscan",  # hdbscan 或 kmeans
    "min_cluster_size": 5,  # 簇的最小大小（调大→簇更少更大）
    "min_samples": 2,       # 核心点邻居数（调大→噪音点更多）

    # 数据预处理
    "min_volume": 0,        # 过滤低搜索量短语（0=不过滤）
    "max_phrases": None,    # 限制处理数量（None=全部处理）

    # 性能配置
    "batch_size": 32,       # embedding批处理大小
    "use_gpu": False,       # 是否使用GPU（需要CUDA）
}
```

### 常见调整场景

#### **场景1：簇太多（>100个）**

```python
"min_cluster_size": 10,  # 从5改为10
```

#### **场景2：簇太少（<10个）**

```python
"min_cluster_size": 3,   # 从5改为3
```

#### **场景3：噪音点太多（>30%）**

```python
"min_samples": 1,        # 从2改为1
```

#### **场景4：只想处理高搜索量短语**

```python
"min_volume": 100,       # 只处理搜索量>=100的短语
```

#### **场景5：测试运行（加快速度）**

```python
"max_phrases": 1000,     # 只处理前1000条
```

#### **场景6：使用GPU加速**

```python
"use_gpu": True,         # 前提：已安装CUDA和GPU版本的PyTorch
```

---

## 🔍 验证聚类结果

### 方法1：查看簇内短语

```python
import pandas as pd

# 读取聚类结果
df = pd.read_csv('D:/xiangmu/词根聚类需求挖掘/data/stageA_clusters.csv')

# 查看簇5的所有短语
cluster_5 = df[df['cluster_id'] == 5]
print("簇5的短语：")
print(cluster_5[['phrase', 'Volume']].head(20))

# 看看是否语义相关
```

### 方法2：查看簇统计

```python
# 读取簇统计
summary = pd.read_csv('D:/xiangmu/词根聚类需求挖掘/data/clusters_summary_stageA.csv')

# 查看最大的10个簇
print(summary.head(10))

# 查看噪音点
noise = summary[summary['cluster_id'] == -1]
print(f"\n噪音点：{noise['cluster_size'].values[0]} 条")
```

### 方法3：分析长度分布

```python
# 看看不同长度的短语如何聚类
df['phrase_length'] = df['phrase'].str.split().str.len()

# 各簇的长度分布
print(df.groupby('cluster_id')['phrase_length'].describe())

# 噪音点的长度分布
noise_df = df[df['cluster_id'] == -1]
print("\n噪音点的长度分布：")
print(noise_df['phrase_length'].value_counts().head(10))
```

### 方法4：验证数据完整性

```python
# 对比聚类前后的数据量
df_before = pd.read_csv('D:/xiangmu/词根聚类需求挖掘/data/merged_keywords_all.csv')
df_after = pd.read_csv('D:/xiangmu/词根聚类需求挖掘/data/stageA_clusters.csv')

print(f"聚类前：{len(df_before)} 条")
print(f"聚类后：{len(df_after)} 条")

# 应该完全相等
if len(df_before) == len(df_after):
    print("✅ 数据完整，没有丢失任何短语")
else:
    print("❌ 数据有丢失，请检查！")
```

---

## ❓ 常见问题

### Q1: 运行时提示"找不到模块"

**问题**：`ModuleNotFoundError: No module named 'sentence_transformers'`

**解决**：
```bash
pip install sentence-transformers
# 或运行
install_dependencies.bat
```

### Q2: 第一次运行很慢？

**原因**：第一次运行时，会自动下载embedding模型（约90MB）

**位置**：模型会下载到 `C:\Users\你的用户名\.cache\torch\sentence_transformers\`

**解决**：耐心等待，第二次运行就会很快

### Q3: 内存不足怎么办？

**症状**：`MemoryError` 或程序崩溃

**解决**：
```python
# 在config.py中限制处理数量
"max_phrases": 5000,  # 先处理5000条试试
"batch_size": 16,     # 减小批处理大小
```

### Q4: 想使用GPU加速

**前提**：
1. 电脑有NVIDIA显卡
2. 已安装CUDA
3. 已安装GPU版本的PyTorch

**配置**：
```python
# config.py
"use_gpu": True,
```

### Q5: 聚类结果不满意

**调整建议**：
- 簇太多 → 增大 `min_cluster_size`
- 簇太少 → 减小 `min_cluster_size`
- 噪音点太多 → 减小 `min_samples`

修改后重新运行即可。

### Q6: 如何切换到KMeans聚类？

```python
# config.py
A3_CONFIG = {
    "clustering_method": "kmeans",  # 改为kmeans
    "n_clusters": 50,  # 指定要生成的簇数量
}
```

**HDBSCAN vs KMeans**：
- HDBSCAN：自动确定簇数量，能识别噪音点（推荐）
- KMeans：需要指定簇数量，速度更快，但不能识别噪音点

---

## 📊 预期结果

### 典型输出（6,565条短语）

```
簇数量：40-60个
噪音点：10-20%
大簇（>50条）：5-10个
中簇（10-50条）：20-30个
小簇（5-10条）：10-20个
```

### 好的聚类表现

✅ 簇内短语语义相关、主题明确
✅ 大簇有清晰的需求方向
✅ 中小簇覆盖细分场景
✅ 噪音点比例合理（10-20%）

### 差的聚类表现

❌ 簇内短语杂乱无章
❌ 大簇混杂多个主题
❌ 噪音点过多（>30%）
❌ 大量小簇（<5条）

如果结果不满意，调整参数重新运行。

---

## 🎯 下一步

聚类完成后，运行步骤A4：

```bash
python step_A4_llm_cluster_summary.py
```

步骤A4会使用大模型分析每个簇，生成：
- 簇的标题和描述
- 5维需求框架（who/what/why/how_now/quality_bar）
- 需求优先级评估

---

## 💡 小技巧

### 技巧1：先用小数据测试

第一次运行时，建议先测试：
```python
# config.py
"max_phrases": 1000,  # 只处理1000条
```
确认流程正常后，再改回 `None` 处理全部数据。

### 技巧2：保存不同参数的结果

```bash
# 运行后，重命名输出文件
copy data\stageA_clusters.csv data\stageA_clusters_min5.csv
copy data\clusters_summary_stageA.csv data\clusters_summary_min5.csv

# 修改参数后再次运行，对比效果
```

### 技巧3：查看日志

如果遇到问题，查看日志文件：
```bash
type D:\xiangmu\词根聚类需求挖掘\output\execution.log
```

---

## 🎉 开始使用

现在就运行试试吧！

```bash
cd D:\xiangmu\词根聚类需求挖掘\功能实现
python step_A3_clustering.py
```

有任何问题随时问我！
