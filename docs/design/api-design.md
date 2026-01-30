# API 设计文档

**项目名称**: 需求挖掘系统
**文档版本**: v1.0
**创建日期**: 2026-01-28
**文档类型**: API 设计

---

## 1. API 概述

**Base URL**: `http://localhost:8000`
**API 文档**: `http://localhost:8000/docs`
**认证方式**: 暂无（待实现）
**数据格式**: JSON

---

## 2. 词根聚类模块 API

### 2.1 导入关键词数据

**端点**: `POST /api/keywords/import`

**功能**: 从 CSV 文件导入关键词数据

**请求参数**:
- `file`: 文件对象（multipart/form-data）

**响应**:
```json
{
  "message": "成功导入 6565 条关键词",
  "count": 6565
}
```

---

### 2.2 获取关键词列表

**端点**: `GET /api/keywords/`

**功能**: 分页获取关键词列表

**查询参数**:
- `page`: 页码（默认 1）
- `page_size`: 每页数量（默认 50）
- `seed_word`: 种子词筛选（可选）
- `cluster_id`: 簇ID筛选（可选）

**响应**:
```json
{
  "total": 6565,
  "page": 1,
  "page_size": 50,
  "data": [
    {
      "keyword_id": 1,
      "keyword": "compress pdf online",
      "seed_word": "compress",
      "cluster_id_a": 5,
      "volume": 12000
    }
  ]
}
```

---

### 2.3 获取关键词总数

**端点**: `GET /api/keywords/count`

**功能**: 获取关键词总数

**响应**:
```json
{
  "total": 6565
}
```

---

### 2.4 获取簇概览

**端点**: `GET /api/keywords/clusters/overview`

**功能**: 获取所有簇的概览信息

**响应**:
```json
{
  "total_clusters": 63,
  "clusters": [
    {
      "cluster_id": 5,
      "cluster_size": 45,
      "top_keywords": ["compress pdf", "compress image"],
      "avg_volume": 8500
    }
  ]
}
```

---

### 2.5 获取簇详情

**端点**: `GET /api/keywords/clusters/{cluster_id}`

**功能**: 获取指定簇的详细信息

**路径参数**:
- `cluster_id`: 簇ID

**响应**:
```json
{
  "cluster_id": 5,
  "cluster_size": 45,
  "keywords": [
    {
      "keyword": "compress pdf online",
      "volume": 12000
    }
  ]
}
```

---

### 2.6 获取种子词列表

**端点**: `GET /api/keywords/seed-words`

**功能**: 获取所有种子词列表

**响应**:
```json
{
  "seed_words": ["compress", "convert", "generate", "track"]
}
```

---

## 3. 商品管理模块 API

### 3.1 导入商品数据

**端点**: `POST /api/products/import`

**功能**: 从 Excel/CSV 文件导入商品数据

**请求参数**:
- `file`: 文件对象（multipart/form-data）

**文件格式**:
- 无表头，固定5列
- 列0: 商品名称（必填）
- 列1: 评分（可选）
- 列2: 评价数量（可选）
- 列3: 店铺名称（可选）
- 列4: 价格（可选）

**响应**:
```json
{
  "message": "成功导入 345 条商品",
  "count": 345
}
```

---

### 3.2 获取商品列表

**端点**: `GET /api/products/`

**功能**: 分页获取商品列表

**查询参数**:
- `page`: 页码（默认 1）
- `page_size`: 每页数量（默认 50）
- `search`: 搜索关键词（可选）
- `min_rating`: 最低评分（可选）
- `max_rating`: 最高评分（可选）
- `shop_name`: 店铺名称（可选）
- `cluster_id`: 簇ID（可选）

**响应**:
```json
{
  "total": 345,
  "page": 1,
  "page_size": 50,
  "data": [
    {
      "product_id": 1,
      "product_name": "Digital Planner Template",
      "rating": 4.8,
      "review_count": 1200,
      "shop_name": "DigitalShop",
      "price": 9.99,
      "cluster_id": 3
    }
  ]
}
```

---

### 3.3 获取商品总数

**端点**: `GET /api/products/count`

**功能**: 获取商品总数

**响应**:
```json
{
  "total": 345
}
```

---

### 3.4 获取商品详情

**端点**: `GET /api/products/{product_id}`

**功能**: 获取指定商品的详细信息

**路径参数**:
- `product_id`: 商品ID

**响应**:
```json
{
  "product_id": 1,
  "product_name": "Digital Planner Template",
  "rating": 4.8,
  "review_count": 1200,
  "shop_name": "DigitalShop",
  "price": 9.99,
  "cluster_id": 3,
  "import_time": "2026-01-28T10:00:00"
}
```

---

### 3.5 更新商品信息

**端点**: `PUT /api/products/{product_id}`

**功能**: 更新商品信息

**路径参数**:
- `product_id`: 商品ID

**请求体**:
```json
{
  "product_name": "Updated Name",
  "rating": 4.9,
  "price": 12.99
}
```

**响应**:
```json
{
  "message": "商品更新成功",
  "product_id": 1
}
```

---

### 3.6 删除商品

**端点**: `DELETE /api/products/{product_id}`

**功能**: 删除商品（软删除）

**路径参数**:
- `product_id`: 商品ID

**响应**:
```json
{
  "message": "商品删除成功",
  "product_id": 1
}
```

---

### 3.7 批量删除商品

**端点**: `POST /api/products/batch-delete`

**功能**: 批量删除商品

**请求体**:
```json
{
  "product_ids": [1, 2, 3, 4, 5]
}
```

**响应**:
```json
{
  "message": "成功删除 5 条商品",
  "count": 5
}
```

---

## 4. 批量导入模块 API

### 4.1 批量导入商品

**端点**: `POST /api/batch-import/products`

**功能**: 批量导入商品数据

**请求参数**:
- `file`: 文件对象（multipart/form-data）

**响应**:
```json
{
  "message": "批量导入成功",
  "total": 345,
  "success": 340,
  "failed": 5
}
```

---

## 5. 系统 API

### 5.1 根路径

**端点**: `GET /`

**功能**: 获取 API 基本信息

**响应**:
```json
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

---

### 5.2 健康检查

**端点**: `GET /health`

**功能**: 检查服务健康状态

**响应**:
```json
{
  "status": "healthy"
}
```

---

## 6. 错误码

| 错误码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

**错误响应格式**:
```json
{
  "detail": "错误信息描述"
}
```

---

## 7. API 使用示例

### 7.1 导入关键词

```bash
curl -X POST "http://localhost:8000/api/keywords/import" \
  -F "file=@data/merged_keywords_all.csv"
```

### 7.2 获取关键词列表

```bash
curl "http://localhost:8000/api/keywords/?page=1&page_size=20"
```

### 7.3 导入商品

```bash
curl -X POST "http://localhost:8000/api/products/import" \
  -F "file=@data/products.xlsx"
```

### 7.4 搜索商品

```bash
curl "http://localhost:8000/api/products/?search=planner&min_rating=4.5"
```

---

*文档创建者: Claude Sonnet 4.5*
*最后更新: 2026-01-28*
