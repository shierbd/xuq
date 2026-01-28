# API 接口设计 v4.3

**创建日期**: 2026-01-28
**目标版本**: v4.3
**API版本**: v2.0

---

## 📋 新增API概述

为支持聚类增强和商品属性提取功能，需要新增以下API接口：

| 编号 | 接口 | 方法 | 功能 | 对应需求 |
|------|------|------|------|----------|
| 1 | `/api/products/clusters/generate-names` | POST | 生成类别名称 | P4.1 |
| 2 | `/api/products/filter` | POST | 复杂筛选 | P4.2 |
| 3 | `/api/products/extract-attributes` | POST | 提取商品属性 | P5.1 |
| 4 | `/api/products/analyze-top` | POST | 分析Top商品 | P5.2 |
| 5 | `/api/products/ai-fallback` | POST | AI辅助兜底 | P5.3 |
| 6 | `/api/products/stats` | GET | 数据统计 | P6.1 |

---

## 🔴 P0 优先级：修复现有API

### 1. 修复商品列表API

**接口**: `GET /api/products`

**问题**: 排序、筛选、翻页、搜索功能不可用

**修复内容**:

```python
@router.get("/products")
async def get_products(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    sort_by: Optional[str] = Query(None, description="排序字段"),
    sort_order: Optional[str] = Query("asc", description="排序方向: asc/desc"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="最低评分"),
    max_rating: Optional[float] = Query(None, ge=0, le=5, description="最高评分"),
    min_price: Optional[float] = Query(None, ge=0, description="最低价格"),
    max_price: Optional[float] = Query(None, ge=0, description="最高价格"),
    cluster_id: Optional[int] = Query(None, description="簇ID"),
    db: Session = Depends(get_db)
):
    """
    获取商品列表（支持分页、搜索、筛选、排序）
    """
    query = db.query(Product).filter(Product.is_deleted == False)

    # 搜索
    if search:
        query = query.filter(Product.product_name.ilike(f"%{search}%"))

    # 筛选
    if min_rating is not None:
        query = query.filter(Product.rating >= min_rating)
    if max_rating is not None:
        query = query.filter(Product.rating <= max_rating)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if cluster_id is not None:
        query = query.filter(Product.cluster_id == cluster_id)

    # 排序
    if sort_by:
        if sort_order == "desc":
            query = query.order_by(desc(getattr(Product, sort_by)))
        else:
            query = query.order_by(asc(getattr(Product, sort_by)))

    # 总数
    total = query.count()

    # 分页
    offset = (page - 1) * page_size
    products = query.offset(offset).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "data": products
    }
```

**响应示例**:
```json
{
  "total": 345,
  "page": 1,
  "page_size": 50,
  "total_pages": 7,
  "data": [
    {
      "product_id": 1,
      "product_name": "Budget Planner Template",
      "rating": 4.8,
      "review_count": 2300,
      "shop_name": "ShopA",
      "price": 7.99,
      "cluster_id": 1,
      "cluster_name": "Budget & Finance Planning",
      "delivery_type": "Template",
      "key_keywords": "Budget, Planner, Finance",
      "user_need": "帮助用户管理个人或家庭预算"
    }
  ]
}
```

---

## 🟠 P1 优先级：类别名称生成

### API 1: 生成类别名称

**接口**: `POST /api/products/clusters/generate-names`

**功能**: 为所有簇生成类别名称

**请求参数**:
```json
{
  "cluster_ids": [1, 2, 3],  // 可选，指定簇ID，不传则处理所有簇
  "force_regenerate": false   // 是否强制重新生成（覆盖已有的）
}
```

**响应**:
```json
{
  "success": true,
  "message": "成功生成63个簇的类别名称",
  "data": {
    "total_clusters": 63,
    "processed": 63,
    "failed": 0,
    "cost_usd": 0.45,
    "results": [
      {
        "cluster_id": 1,
        "cluster_name": "Budget & Finance Planning",
        "cluster_size": 15,
        "top_products": [
          "Budget Planner Template",
          "Monthly Budget Tracker",
          "Financial Planner"
        ]
      }
    ]
  }
}
```

**实现逻辑**:
```python
@router.post("/clusters/generate-names")
async def generate_cluster_names(
    request: GenerateNamesRequest,
    db: Session = Depends(get_db)
):
    """
    为簇生成类别名称（AI）
    """
    # 获取需要处理的簇
    if request.cluster_ids:
        clusters = db.query(ClusterSummary).filter(
            ClusterSummary.cluster_id.in_(request.cluster_ids)
        ).all()
    else:
        if request.force_regenerate:
            clusters = db.query(ClusterSummary).all()
        else:
            # 只处理没有类别名的簇
            clusters = db.query(ClusterSummary).filter(
                ClusterSummary.cluster_name.is_(None)
            ).all()

    results = []
    failed = 0
    total_cost = 0

    for cluster in clusters:
        try:
            # 获取Top 5商品
            top_products = db.query(Product).filter(
                Product.cluster_id == cluster.cluster_id,
                Product.is_deleted == False
            ).order_by(desc(Product.review_count)).limit(5).all()

            # 调用AI生成类别名
            cluster_name, cost = await ai_generate_cluster_name(
                [p.product_name for p in top_products]
            )

            # 更新数据库
            cluster.cluster_name = cluster_name
            db.commit()

            # 同步更新products表
            db.query(Product).filter(
                Product.cluster_id == cluster.cluster_id
            ).update({"cluster_name": cluster_name})
            db.commit()

            total_cost += cost
            results.append({
                "cluster_id": cluster.cluster_id,
                "cluster_name": cluster_name,
                "cluster_size": cluster.cluster_size,
                "top_products": [p.product_name for p in top_products[:3]]
            })
        except Exception as e:
            failed += 1
            logger.error(f"Failed to generate name for cluster {cluster.cluster_id}: {e}")

    return {
        "success": True,
        "message": f"成功生成{len(results)}个簇的类别名称",
        "data": {
            "total_clusters": len(clusters),
            "processed": len(results),
            "failed": failed,
            "cost_usd": round(total_cost, 2),
            "results": results
        }
    }
```

---

## 🟡 P2 优先级：复杂筛选

### API 2: 复杂筛选

**接口**: `POST /api/products/filter`

**功能**: 支持多条件组合筛选

**请求参数**:
```json
{
  "cluster_name": "Budget & Finance Planning",  // 类别名称
  "min_review_count": 1000,                     // 最低评价数
  "max_review_count": 5000,                     // 最高评价数
  "min_rating": 4.0,                            // 最低评分
  "max_rating": 5.0,                            // 最高评分
  "min_price": 5.0,                             // 最低价格
  "max_price": 10.0,                            // 最高价格
  "delivery_types": ["Template", "Planner"],    // 交付形式（多选）
  "search": "budget",                           // 搜索关键词
  "page": 1,
  "page_size": 50,
  "sort_by": "review_count",                    // 排序字段
  "sort_order": "desc"                          // 排序方向
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "total": 25,
    "page": 1,
    "page_size": 50,
    "total_pages": 1,
    "filters_applied": {
      "cluster_name": "Budget & Finance Planning",
      "review_count_range": [1000, 5000],
      "rating_range": [4.0, 5.0],
      "price_range": [5.0, 10.0],
      "delivery_types": ["Template", "Planner"]
    },
    "products": [...]
  }
}
```

**实现逻辑**:
```python
@router.post("/filter")
async def filter_products(
    request: FilterRequest,
    db: Session = Depends(get_db)
):
    """
    复杂筛选商品
    """
    query = db.query(Product).filter(Product.is_deleted == False)

    # 按类别名称筛选
    if request.cluster_name:
        query = query.filter(Product.cluster_name == request.cluster_name)

    # 按评价数范围筛选
    if request.min_review_count is not None:
        query = query.filter(Product.review_count >= request.min_review_count)
    if request.max_review_count is not None:
        query = query.filter(Product.review_count <= request.max_review_count)

    # 按评分范围筛选
    if request.min_rating is not None:
        query = query.filter(Product.rating >= request.min_rating)
    if request.max_rating is not None:
        query = query.filter(Product.rating <= request.max_rating)

    # 按价格范围筛选
    if request.min_price is not None:
        query = query.filter(Product.price >= request.min_price)
    if request.max_price is not None:
        query = query.filter(Product.price <= request.max_price)

    # 按交付形式筛选（多选）
    if request.delivery_types:
        query = query.filter(Product.delivery_type.in_(request.delivery_types))

    # 搜索
    if request.search:
        query = query.filter(Product.product_name.ilike(f"%{request.search}%"))

    # 排序
    if request.sort_by:
        if request.sort_order == "desc":
            query = query.order_by(desc(getattr(Product, request.sort_by)))
        else:
            query = query.order_by(asc(getattr(Product, request.sort_by)))

    # 分页
    total = query.count()
    offset = (request.page - 1) * request.page_size
    products = query.offset(offset).limit(request.page_size).all()

    return {
        "success": True,
        "data": {
            "total": total,
            "page": request.page,
            "page_size": request.page_size,
            "total_pages": (total + request.page_size - 1) // request.page_size,
            "filters_applied": {
                "cluster_name": request.cluster_name,
                "review_count_range": [request.min_review_count, request.max_review_count],
                "rating_range": [request.min_rating, request.max_rating],
                "price_range": [request.min_price, request.max_price],
                "delivery_types": request.delivery_types
            },
            "products": products
        }
    }
```

---

## 🟢 P3 优先级：商品属性提取

### API 3: 提取商品属性

**接口**: `POST /api/products/extract-attributes`

**功能**: 使用代码规则提取交付形式和关键词

**请求参数**:
```json
{
  "product_ids": [1, 2, 3],  // 可选，指定商品ID，不传则处理所有商品
  "force_reextract": false    // 是否强制重新提取
}
```

**响应**:
```json
{
  "success": true,
  "message": "成功提取345个商品的属性",
  "data": {
    "total_products": 345,
    "processed": 345,
    "delivery_type_extracted": 310,  // 成功提取交付形式的数量
    "delivery_type_failed": 35,      // 未能提取的数量（需要AI辅助）
    "keywords_extracted": 345,
    "processing_time_seconds": 12.5
  }
}
```

**实现逻辑**:
```python
@router.post("/extract-attributes")
async def extract_product_attributes(
    request: ExtractAttributesRequest,
    db: Session = Depends(get_db)
):
    """
    提取商品属性（代码规则）
    """
    # 获取需要处理的商品
    if request.product_ids:
        products = db.query(Product).filter(
            Product.product_id.in_(request.product_ids)
        ).all()
    else:
        if request.force_reextract:
            products = db.query(Product).all()
        else:
            # 只处理没有提取过的商品
            products = db.query(Product).filter(
                Product.delivery_type.is_(None)
            ).all()

    delivery_type_extracted = 0
    delivery_type_failed = 0
    keywords_extracted = 0

    start_time = time.time()

    for product in products:
        # 提取交付形式（代码规则）
        delivery_type = extract_delivery_type_by_rules(product.product_name)
        if delivery_type:
            product.delivery_type = delivery_type
            delivery_type_extracted += 1
        else:
            delivery_type_failed += 1

        # 提取关键词（NLP）
        keywords = extract_keywords_by_nlp(product.product_name)
        product.key_keywords = ", ".join(keywords)
        keywords_extracted += 1

    db.commit()

    processing_time = time.time() - start_time

    return {
        "success": True,
        "message": f"成功提取{len(products)}个商品的属性",
        "data": {
            "total_products": len(products),
            "processed": len(products),
            "delivery_type_extracted": delivery_type_extracted,
            "delivery_type_failed": delivery_type_failed,
            "keywords_extracted": keywords_extracted,
            "processing_time_seconds": round(processing_time, 2)
        }
    }
```

---

## 🔵 P4 优先级：Top商品AI分析

### API 4: 分析Top商品

**接口**: `POST /api/products/analyze-top`

**功能**: 对每个簇的Top商品进行AI深度分析

**请求参数**:
```json
{
  "cluster_ids": [1, 2, 3],  // 可选，指定簇ID
  "top_n": 3,                 // 每个簇分析Top N个商品
  "force_reanalyze": false    // 是否强制重新分析
}
```

**响应**:
```json
{
  "success": true,
  "message": "成功分析189个Top商品",
  "data": {
    "total_clusters": 63,
    "total_products_analyzed": 189,
    "cost_usd": 2.35,
    "processing_time_minutes": 18.5,
    "results": [
      {
        "cluster_id": 1,
        "cluster_name": "Budget & Finance Planning",
        "user_need": "帮助用户管理个人或家庭预算，追踪收支情况，实现财务目标",
        "top_products_analyzed": 3,
        "common_delivery_type": "Template"
      }
    ]
  }
}
```

**实现逻辑**:
```python
@router.post("/analyze-top")
async def analyze_top_products(
    request: AnalyzeTopRequest,
    db: Session = Depends(get_db)
):
    """
    分析Top商品（AI）
    """
    # 获取需要处理的簇
    if request.cluster_ids:
        clusters = db.query(ClusterSummary).filter(
            ClusterSummary.cluster_id.in_(request.cluster_ids)
        ).all()
    else:
        if request.force_reanalyze:
            clusters = db.query(ClusterSummary).all()
        else:
            # 只处理没有分析过的簇
            clusters = db.query(ClusterSummary).filter(
                ClusterSummary.user_need.is_(None)
            ).all()

    total_products_analyzed = 0
    total_cost = 0
    start_time = time.time()
    results = []

    for cluster in clusters:
        # 获取Top N商品
        top_products = db.query(Product).filter(
            Product.cluster_id == cluster.cluster_id,
            Product.is_deleted == False
        ).order_by(desc(Product.review_count)).limit(request.top_n).all()

        # 调用AI分析
        analysis, cost = await ai_analyze_products(
            [p.product_name for p in top_products]
        )

        # 更新簇的用户需求
        cluster.user_need = analysis["user_need"]
        cluster.common_delivery_type = analysis.get("common_delivery_type")
        db.commit()

        # 更新簇内所有商品的用户需求
        db.query(Product).filter(
            Product.cluster_id == cluster.cluster_id
        ).update({"user_need": analysis["user_need"]})
        db.commit()

        total_products_analyzed += len(top_products)
        total_cost += cost

        results.append({
            "cluster_id": cluster.cluster_id,
            "cluster_name": cluster.cluster_name,
            "user_need": analysis["user_need"],
            "top_products_analyzed": len(top_products),
            "common_delivery_type": cluster.common_delivery_type
        })

    processing_time = (time.time() - start_time) / 60

    return {
        "success": True,
        "message": f"成功分析{total_products_analyzed}个Top商品",
        "data": {
            "total_clusters": len(clusters),
            "total_products_analyzed": total_products_analyzed,
            "cost_usd": round(total_cost, 2),
            "processing_time_minutes": round(processing_time, 2),
            "results": results
        }
    }
```

---

## 🟣 P5 优先级：AI辅助兜底

### API 5: AI辅助兜底

**接口**: `POST /api/products/ai-fallback`

**功能**: 对代码规则无法提取交付形式的商品，使用AI补充

**请求参数**:
```json
{
  "limit": 100  // 最多处理多少个商品
}
```

**响应**:
```json
{
  "success": true,
  "message": "成功补充35个商品的交付形式",
  "data": {
    "total_products_without_delivery": 35,
    "processed": 35,
    "cost_usd": 0.28,
    "processing_time_minutes": 8.5
  }
}
```

---

## ⚪ P6 优先级：数据统计

### API 6: 数据统计

**接口**: `GET /api/products/stats`

**功能**: 获取数据统计信息（用于图表）

**响应**:
```json
{
  "success": true,
  "data": {
    "cluster_size_distribution": [
      {"cluster_name": "Budget & Finance", "size": 15},
      {"cluster_name": "Recipe & Cooking", "size": 12}
    ],
    "rating_distribution": {
      "4.0-4.5": 50,
      "4.5-5.0": 295
    },
    "price_distribution": {
      "0-5": 80,
      "5-10": 200,
      "10-20": 50,
      "20+": 15
    },
    "delivery_type_distribution": {
      "Template": 150,
      "Planner": 80,
      "Tracker": 60,
      "Other": 55
    },
    "review_count_stats": {
      "min": 15,
      "max": 23000,
      "avg": 1250,
      "median": 890
    }
  }
}
```

---

## 📝 API文档生成

所有API将自动生成OpenAPI文档，访问地址：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## ✅ 验收标准

1. [ ] 所有API接口实现完成
2. [ ] API文档自动生成
3. [ ] 请求参数验证正确
4. [ ] 响应格式统一
5. [ ] 错误处理完善
6. [ ] 性能测试通过（响应时间<2秒）
7. [ ] 单元测试覆盖率>80%

---

*文档创建者: Claude Sonnet 4.5*
*创建时间: 2026-01-28*
