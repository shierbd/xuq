# API 使用示例

本文档提供需求挖掘系统 v2.0 的常见 API 使用示例。

---

## 📋 目录

1. [基础操作](#基础操作)
2. [词根聚类模块](#词根聚类模块)
3. [商品管理模块](#商品管理模块)
4. [高级查询](#高级查询)
5. [数据分析](#数据分析)

---

## 基础操作

### 1. 检查系统状态

```bash
# 获取系统信息
curl http://127.0.0.1:8000/

# 响应示例
{
  "message": "需求挖掘系统 API",
  "version": "2.0.0",
  "modules": {
    "keywords": "词根聚类模块",
    "products": "商品管理模块"
  },
  "docs": "/docs"
}
```

### 2. 健康检查

```bash
curl http://127.0.0.1:8000/health

# 响应示例
{
  "status": "healthy"
}
```

### 3. 查看 API 文档

访问浏览器: http://127.0.0.1:8000/docs

---

## 词根聚类模块

### 1. 导入关键词数据

```bash
# 导入 SEMrush 格式的关键词数据
curl -X POST "http://127.0.0.1:8000/api/keywords/import" \
  -F "file=@data/merged_keywords_all.csv"

# 响应示例
{
  "success": true,
  "message": "数据导入成功",
  "data": {
    "total": 6565,
    "imported": 6565,
    "duplicates": 0
  }
}
```

```bash
# 导入聚类结果数据
curl -X POST "http://127.0.0.1:8000/api/keywords/import" \
  -F "file=@data/stageA_clusters.csv"

# 响应示例
{
  "success": true,
  "message": "聚类结果导入成功",
  "data": {
    "total": 6344,
    "updated": 6344
  }
}
```

### 2. 获取关键词总数

```bash
curl http://127.0.0.1:8000/api/keywords/count

# 响应示例
{
  "success": true,
  "data": {
    "total": 6565
  }
}
```

### 3. 获取关键词列表

```bash
# 基础查询（第1页，每页50条）
curl "http://127.0.0.1:8000/api/keywords/?page=1&page_size=50"

# 搜索关键词
curl "http://127.0.0.1:8000/api/keywords/?search=best"

# 按种子词筛选
curl "http://127.0.0.1:8000/api/keywords/?seed_word=code"

# 按簇ID筛选
curl "http://127.0.0.1:8000/api/keywords/?cluster_id=42"

# 只查看非噪音点
curl "http://127.0.0.1:8000/api/keywords/?is_noise=false"

# 组合查询
curl "http://127.0.0.1:8000/api/keywords/?seed_word=Best&is_noise=false&page=1&page_size=20"

# 响应示例
{
  "success": true,
  "data": {
    "total": 6565,
    "page": 1,
    "page_size": 50,
    "items": [
      {
        "keyword_id": 1,
        "keyword": "best buy coupon code",
        "seed_word": "Best",
        "volume": 49500,
        "cluster_id_a": 39,
        "cluster_size": 306,
        "is_noise": false
      },
      // ... 更多记录
    ]
  }
}
```

### 4. 获取所有种子词

```bash
curl http://127.0.0.1:8000/api/keywords/seed-words

# 响应示例
{
  "success": true,
  "data": {
    "seed_words": [
      "Best",
      "code",
      "How-to",
      "top",
      "maker",
      // ... 更多种子词
    ]
  }
}
```

### 5. 获取簇概览

```bash
# 获取所有簇的概览（阶段A）
curl "http://127.0.0.1:8000/api/keywords/clusters/overview?stage=A"

# 排除噪音点
curl "http://127.0.0.1:8000/api/keywords/clusters/overview?stage=A&exclude_noise=true"

# 按簇大小筛选
curl "http://127.0.0.1:8000/api/keywords/clusters/overview?stage=A&min_size=20&max_size=100"

# 响应示例
{
  "success": true,
  "total": 63,
  "data": [
    {
      "cluster_id": 42,
      "cluster_size": 502,
      "seed_words": ["code"],
      "top_keywords": [
        "213 area code",
        "646 area code",
        "929 area code",
        "209 area code",
        "323 area code"
      ],
      "total_volume": 17257200
    },
    // ... 更多簇
  ]
}
```

### 6. 获取单个簇的详细信息

```bash
# 获取簇 #42 的详细信息
curl "http://127.0.0.1:8000/api/keywords/clusters/42?stage=A"

# 响应示例
{
  "success": true,
  "data": {
    "cluster_id": 42,
    "cluster_size": 502,
    "seed_words": ["code"],
    "statistics": {
      "total_volume": 17257200,
      "avg_volume": 34367,
      "max_volume": 1220000,
      "min_volume": 10
    },
    "keywords": [
      {
        "keyword_id": 1234,
        "keyword": "213 area code",
        "seed_word": "code",
        "volume": 1220000,
        "intent": "Informational"
      },
      // ... 更多关键词（按搜索量降序排列）
    ]
  }
}
```

---

## 商品管理模块

### 1. 获取商品总数

```bash
curl http://127.0.0.1:8000/api/products/count

# 响应示例
{
  "success": true,
  "data": {
    "total": 345
  }
}
```

### 2. 获取商品列表

```bash
# 基础查询
curl "http://127.0.0.1:8000/api/products/?page=1&page_size=20"

# 搜索商品名称
curl "http://127.0.0.1:8000/api/products/?search=planner"

# 按店铺筛选
curl "http://127.0.0.1:8000/api/products/?shop_name=DigitalPlannerShop"

# 按簇ID筛选
curl "http://127.0.0.1:8000/api/products/?cluster_id=5"

# 按评分筛选
curl "http://127.0.0.1:8000/api/products/?min_rating=4.5"

# 按价格范围筛选
curl "http://127.0.0.1:8000/api/products/?min_price=10&max_price=50"

# 响应示例
{
  "success": true,
  "data": {
    "total": 345,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "product_id": 1,
        "product_name": "Digital Planner 2024",
        "rating": 4.8,
        "review_count": 1250,
        "shop_name": "DigitalPlannerShop",
        "price": 29.99,
        "cluster_id": 5
      },
      // ... 更多商品
    ]
  }
}
```

### 3. 获取单个商品详情

```bash
curl http://127.0.0.1:8000/api/products/1

# 响应示例
{
  "success": true,
  "data": {
    "product_id": 1,
    "product_name": "Digital Planner 2024",
    "rating": 4.8,
    "review_count": 1250,
    "shop_name": "DigitalPlannerShop",
    "price": 29.99,
    "cluster_id": 5,
    "delivery_type": "Digital Download",
    "delivery_format": "PDF",
    "delivery_platform": "GoodNotes",
    "import_time": "2024-01-15T10:30:00",
    "is_deleted": false
  }
}
```

### 4. 更新商品信息

```bash
curl -X PUT "http://127.0.0.1:8000/api/products/1" \
  -H "Content-Type: application/json" \
  -d '{
    "cluster_id": 10,
    "delivery_type": "Digital Download",
    "delivery_format": "PDF"
  }'

# 响应示例
{
  "success": true,
  "message": "商品更新成功",
  "data": {
    "product_id": 1,
    // ... 更新后的商品信息
  }
}
```

### 5. 删除商品（软删除）

```bash
curl -X DELETE "http://127.0.0.1:8000/api/products/1"

# 响应示例
{
  "success": true,
  "message": "商品删除成功"
}
```

---

## 高级查询

### 1. 查找高搜索量的关键词

```bash
# 获取簇概览，按总搜索量排序（默认）
curl "http://127.0.0.1:8000/api/keywords/clusters/overview?stage=A&exclude_noise=true"

# 然后查看特定簇的详细信息
curl "http://127.0.0.1:8000/api/keywords/clusters/42?stage=A"
```

### 2. 分析特定种子词的表现

```bash
# 获取特定种子词的所有关键词
curl "http://127.0.0.1:8000/api/keywords/?seed_word=Best&page_size=100"

# 获取该种子词相关的簇
curl "http://127.0.0.1:8000/api/keywords/clusters/overview?stage=A" | grep -A 5 "Best"
```

### 3. 查找大簇（潜在的热门方向）

```bash
# 只查看簇大小 >= 50 的簇
curl "http://127.0.0.1:8000/api/keywords/clusters/overview?stage=A&min_size=50"
```

### 4. 查找小而精的簇

```bash
# 查看簇大小在 10-20 之间的簇
curl "http://127.0.0.1:8000/api/keywords/clusters/overview?stage=A&min_size=10&max_size=20"
```

---

## 数据分析

### 1. 统计分析示例

```bash
# 获取所有簇的概览数据
curl "http://127.0.0.1:8000/api/keywords/clusters/overview?stage=A" > clusters.json

# 使用 jq 进行数据分析（需要安装 jq）
# 计算平均簇大小
cat clusters.json | jq '.data | map(.cluster_size) | add / length'

# 找出搜索量最高的5个簇
cat clusters.json | jq '.data | sort_by(.total_volume) | reverse | .[0:5]'

# 统计每个种子词出现的次数
cat clusters.json | jq '.data | map(.seed_words[]) | group_by(.) | map({seed: .[0], count: length})'
```

### 2. 导出数据示例

```bash
# 导出所有关键词（分页获取）
for i in {1..132}; do
  curl "http://127.0.0.1:8000/api/keywords/?page=$i&page_size=50" >> all_keywords.json
  sleep 0.1
done

# 导出特定簇的数据
curl "http://127.0.0.1:8000/api/keywords/clusters/42?stage=A" > cluster_42.json
```

### 3. 交叉分析示例

```bash
# 1. 获取高搜索量的簇
curl "http://127.0.0.1:8000/api/keywords/clusters/overview?stage=A&min_size=30" > high_volume_clusters.json

# 2. 对于每个簇，查找相关的商品
# （需要根据簇的关键词手动匹配商品）
curl "http://127.0.0.1:8000/api/products/?search=planner"
```

---

## Python 示例

### 使用 requests 库

```python
import requests

# 基础配置
BASE_URL = "http://127.0.0.1:8000"

# 1. 获取关键词总数
response = requests.get(f"{BASE_URL}/api/keywords/count")
data = response.json()
print(f"关键词总数: {data['data']['total']}")

# 2. 搜索关键词
params = {
    "search": "best",
    "is_noise": False,
    "page": 1,
    "page_size": 20
}
response = requests.get(f"{BASE_URL}/api/keywords/", params=params)
keywords = response.json()['data']['items']
for kw in keywords:
    print(f"{kw['keyword']} - 搜索量: {kw['volume']}")

# 3. 获取簇概览
params = {
    "stage": "A",
    "exclude_noise": True,
    "min_size": 30
}
response = requests.get(f"{BASE_URL}/api/keywords/clusters/overview", params=params)
clusters = response.json()['data']
for cluster in clusters[:5]:
    print(f"簇 #{cluster['cluster_id']}: {cluster['cluster_size']} 个关键词, "
          f"总搜索量: {cluster['total_volume']:,}")

# 4. 导入数据
with open('data/merged_keywords_all.csv', 'rb') as f:
    files = {'file': f}
    response = requests.post(f"{BASE_URL}/api/keywords/import", files=files)
    print(response.json())
```

---

## JavaScript 示例

### 使用 fetch API

```javascript
const BASE_URL = 'http://127.0.0.1:8000';

// 1. 获取关键词总数
async function getKeywordCount() {
  const response = await fetch(`${BASE_URL}/api/keywords/count`);
  const data = await response.json();
  console.log(`关键词总数: ${data.data.total}`);
}

// 2. 搜索关键词
async function searchKeywords(searchTerm) {
  const params = new URLSearchParams({
    search: searchTerm,
    is_noise: false,
    page: 1,
    page_size: 20
  });

  const response = await fetch(`${BASE_URL}/api/keywords/?${params}`);
  const data = await response.json();

  data.data.items.forEach(kw => {
    console.log(`${kw.keyword} - 搜索量: ${kw.volume}`);
  });
}

// 3. 获取簇概览
async function getClustersOverview() {
  const params = new URLSearchParams({
    stage: 'A',
    exclude_noise: true,
    min_size: 30
  });

  const response = await fetch(`${BASE_URL}/api/keywords/clusters/overview?${params}`);
  const data = await response.json();

  data.data.slice(0, 5).forEach(cluster => {
    console.log(`簇 #${cluster.cluster_id}: ${cluster.cluster_size} 个关键词, ` +
                `总搜索量: ${cluster.total_volume.toLocaleString()}`);
  });
}

// 4. 导入数据
async function importKeywords(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${BASE_URL}/api/keywords/import`, {
    method: 'POST',
    body: formData
  });

  const data = await response.json();
  console.log(data);
}

// 调用示例
getKeywordCount();
searchKeywords('best');
getClustersOverview();
```

---

## 常见问题

### Q1: 如何处理大量数据的分页？

```bash
# 使用循环获取所有页面
total_pages=132  # 根据 total / page_size 计算

for page in $(seq 1 $total_pages); do
  curl "http://127.0.0.1:8000/api/keywords/?page=$page&page_size=50" \
    >> all_keywords.json
  sleep 0.1  # 避免请求过快
done
```

### Q2: 如何批量更新数据？

目前 API 不支持批量更新，需要逐个更新：

```python
import requests

BASE_URL = "http://127.0.0.1:8000"

# 批量更新商品的簇ID
products_to_update = [
    {"product_id": 1, "cluster_id": 10},
    {"product_id": 2, "cluster_id": 10},
    {"product_id": 3, "cluster_id": 15},
]

for item in products_to_update:
    response = requests.put(
        f"{BASE_URL}/api/products/{item['product_id']}",
        json={"cluster_id": item['cluster_id']}
    )
    print(f"更新商品 {item['product_id']}: {response.json()}")
```

### Q3: 如何导出数据到 Excel？

```python
import requests
import pandas as pd

BASE_URL = "http://127.0.0.1:8000"

# 获取所有关键词（分页）
all_keywords = []
page = 1
while True:
    response = requests.get(
        f"{BASE_URL}/api/keywords/",
        params={"page": page, "page_size": 100}
    )
    data = response.json()['data']
    all_keywords.extend(data['items'])

    if len(data['items']) < 100:
        break
    page += 1

# 转换为 DataFrame 并导出
df = pd.DataFrame(all_keywords)
df.to_excel('keywords_export.xlsx', index=False)
print(f"导出完成: {len(all_keywords)} 条记录")
```

---

## 更多资源

- **API 文档**: http://127.0.0.1:8000/docs
- **项目文档**: `docs/`
- **系统架构**: `docs/项目合并完成总结.md`
- **快速开始**: `README.md`

---

**最后更新**: 2026-01-27
**版本**: v2.0.0
