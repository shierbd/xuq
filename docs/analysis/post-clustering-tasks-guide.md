# 聚类后生成任务完整指南

**创建日期**: 2026-01-29
**当前状态**: 聚类优化已完成（77.8% 覆盖率），进入后处理阶段
**簇数量**: 675 个

---

## 📋 任务总览

聚类完成后，需要对 675 个簇和 15,792 个商品进行以下增强处理：

| 任务编号 | 任务名称 | 优先级 | 实现方式 | 预计成本 | 预计时间 |
|---------|---------|--------|---------|---------|---------|
| **P4.1** | 类别名称生成 | 🟠 P1 高 | AI分析 | $3-5 | 2-3小时 |
| **P5.1** | 商品属性提取 | 🟢 P3 中 | 代码规则 | $0 | 1-2小时 |
| **P5.2** | Top商品AI分析 | 🔵 P4 中低 | AI分析 | $10-15 | 3-4小时 |
| **P3.1** | 需求分析 | 🟡 P2 中高 | AI分析 | 包含在P5.2 | - |
| **P3.2** | 交付产品识别 | 🟢 P3 中 | 包含在P5.1 | $0 | - |

**推荐实施顺序**: P4.1 → P5.1 → P5.2

---

## 🎯 任务一：P4.1 类别名称生成

### 任务描述

为 675 个聚类簇生成可读的类别名称，让用户能够快速理解每个簇代表的产品类别。

### 当前状态

- ✅ 聚类完成：675 个簇
- ❌ 类别名称：未生成（cluster_name 字段为空）
- 📊 数据规模：675 个簇需要命名

### 实现方案

#### 方法：AI 分析簇内商品

```python
# 伪代码示例
for cluster_id in range(675):
    # 1. 获取簇内 Top 5 商品（按评价数排序）
    top_products = get_top_products(cluster_id, limit=5)

    # 2. 构建 Prompt
    prompt = f"""
    分析以下商品名称，生成一个简洁的类别名称（英文，2-4个词）：

    商品列表：
    {top_products}

    要求：
    - 类别名称要准确反映商品共性
    - 使用英文，首字母大写
    - 2-4个词，例如："Budget Planning Template"
    - 只返回类别名称，不要解释
    """

    # 3. 调用 AI API
    category_name = call_ai_api(prompt)

    # 4. 存储到数据库
    update_cluster_name(cluster_id, category_name)
```

#### 数据流程

```
簇ID → 查询Top 5商品 → 构建Prompt → 调用AI → 解析结果 → 存储到数据库
  ↓                                                              ↓
cluster_id                                            cluster_summaries.cluster_name
                                                      products.cluster_name (关联更新)
```

### 技术实现

#### 1. 后端 API 设计

**路由**: `POST /api/clusters/generate-names`

**请求参数**:
```json
{
  "cluster_ids": [1, 2, 3],  // 可选，不传则处理所有簇
  "batch_size": 10,           // 批次大小
  "ai_provider": "deepseek"   // 或 "claude"
}
```

**响应**:
```json
{
  "success": true,
  "total_clusters": 675,
  "processed": 675,
  "failed": 0,
  "results": [
    {
      "cluster_id": 1,
      "cluster_name": "Budget Planning Template",
      "top_products": ["...", "...", "..."]
    }
  ],
  "cost_estimate": "$3.50"
}
```

#### 2. 数据库更新

```sql
-- 更新 cluster_summaries 表
UPDATE cluster_summaries
SET cluster_name = 'Budget Planning Template'
WHERE cluster_id = 1;

-- 同步更新 products 表（可选，用于快速查询）
UPDATE products
SET cluster_name = 'Budget Planning Template'
WHERE cluster_id = 1;
```

#### 3. Prompt 设计

**版本 1: 简洁版**
```
分析以下 Etsy 商品名称，生成一个类别名称：

1. Budget Planner Template Notion
2. Monthly Budget Tracker Excel
3. Finance Planning Spreadsheet
4. Budget Worksheet Printable
5. Expense Tracker Template

要求：
- 2-4个英文单词
- 首字母大写
- 准确反映商品共性
- 只返回类别名称

类别名称：
```

**版本 2: 结构化版**
```json
{
  "task": "category_naming",
  "products": [
    "Budget Planner Template Notion",
    "Monthly Budget Tracker Excel",
    "Finance Planning Spreadsheet",
    "Budget Worksheet Printable",
    "Expense Tracker Template"
  ],
  "requirements": {
    "length": "2-4 words",
    "language": "English",
    "format": "Title Case",
    "output": "category name only"
  }
}

请返回 JSON 格式：
{
  "category_name": "Budget Planning Template",
  "confidence": 0.95
}
```

### 成本估算

- **API 调用次数**: 675 次
- **每次调用成本**:
  - DeepSeek: ~$0.005
  - Claude Haiku: ~$0.008
- **总成本**: $3-5

### 预期结果

```
簇ID 1  → "Budget Planning Template"
簇ID 2  → "Wedding Planning Checklist"
簇ID 3  → "Meal Prep Tracker"
簇ID 4  → "Fitness Workout Planner"
...
簇ID 675 → "Digital Art Printable"
```

### 验收标准

- [ ] 675 个簇全部生成类别名称
- [ ] 类别名称准确反映簇内商品共性
- [ ] 类别名称格式统一（Title Case，2-4词）
- [ ] 数据库字段正确更新
- [ ] 前端能够显示类别名称
- [ ] 支持人工修正类别名称
- [ ] 总处理时间 < 30 分钟

---

## 🔧 任务二：P5.1 商品属性提取（代码规则）

### 任务描述

使用代码规则从 15,792 个商品名称中提取：
1. **交付形式**（delivery_type）
2. **交付平台**（delivery_platform）
3. **关键词**（key_keywords）

### 当前状态

- ✅ 商品数据：15,792 条
- ❌ 交付形式：未提取
- ❌ 交付平台：未提取
- ❌ 关键词：未提取

### 实现方案

#### 1. 交付形式提取规则

```python
DELIVERY_TYPE_RULES = {
    # 基础类型
    "template": "Template",
    "planner": "Planner",
    "tracker": "Tracker",
    "worksheet": "Worksheet",
    "printable": "Printable",
    "bundle": "Bundle",
    "kit": "Kit",
    "guide": "Guide",
    "checklist": "Checklist",
    "calendar": "Calendar",
    "journal": "Journal",
    "organizer": "Organizer",
    "workbook": "Workbook",
    "spreadsheet": "Spreadsheet",

    # 组合类型（优先级更高）
    "notion template": "Notion Template",
    "canva template": "Canva Template",
    "excel template": "Excel Template",
    "google sheets template": "Google Sheets Template",
    "powerpoint template": "PowerPoint Template",
    "pdf template": "PDF Template",
}

def extract_delivery_type(product_name: str) -> str:
    """提取交付形式"""
    name_lower = product_name.lower()

    # 优先匹配组合类型
    for keyword, delivery_type in sorted(
        DELIVERY_TYPE_RULES.items(),
        key=lambda x: len(x[0]),
        reverse=True
    ):
        if keyword in name_lower:
            return delivery_type

    return "Unknown"
```

#### 2. 交付平台提取规则

```python
PLATFORM_RULES = {
    "notion": "Notion",
    "canva": "Canva",
    "excel": "Excel",
    "google sheets": "Google Sheets",
    "google sheet": "Google Sheets",
    "powerpoint": "PowerPoint",
    "ppt": "PowerPoint",
    "pdf": "PDF",
    "word": "Word",
    "figma": "Figma",
    "trello": "Trello",
    "airtable": "Airtable",
}

def extract_platform(product_name: str) -> str:
    """提取交付平台"""
    name_lower = product_name.lower()

    for keyword, platform in PLATFORM_RULES.items():
        if keyword in name_lower:
            return platform

    return "Unknown"
```

#### 3. 关键词提取

```python
import re
from collections import Counter

# 停用词列表
STOP_WORDS = {
    "template", "planner", "tracker", "printable", "digital",
    "instant", "download", "editable", "customizable", "pdf",
    "notion", "canva", "excel", "google", "sheets"
}

def extract_keywords(product_name: str, max_keywords: int = 5) -> str:
    """提取关键词"""
    # 1. 清理文本
    name_lower = product_name.lower()

    # 2. 分词（按空格和特殊字符）
    words = re.findall(r'\b[a-z]+\b', name_lower)

    # 3. 过滤停用词和短词
    filtered_words = [
        word for word in words
        if word not in STOP_WORDS and len(word) > 2
    ]

    # 4. 统计词频
    word_counts = Counter(filtered_words)

    # 5. 提取 Top N 关键词
    top_keywords = [word for word, _ in word_counts.most_common(max_keywords)]

    return ", ".join(top_keywords)
```

### 技术实现

#### 后端 API 设计

**路由**: `POST /api/products/extract-attributes`

**请求参数**:
```json
{
  "batch_size": 1000,
  "extract_delivery_type": true,
  "extract_platform": true,
  "extract_keywords": true
}
```

**响应**:
```json
{
  "success": true,
  "total_products": 15792,
  "processed": 15792,
  "results": {
    "delivery_type_extracted": 14200,
    "platform_extracted": 12500,
    "keywords_extracted": 15792
  },
  "coverage": {
    "delivery_type": "89.9%",
    "platform": "79.2%",
    "keywords": "100%"
  }
}
```

#### 批量处理代码

```python
def batch_extract_attributes(db: Session, batch_size: int = 1000):
    """批量提取商品属性"""
    products = db.query(Product).filter(
        Product.is_deleted == False
    ).all()

    total = len(products)
    processed = 0

    for i in range(0, total, batch_size):
        batch = products[i:i+batch_size]

        for product in batch:
            # 提取交付形式
            product.delivery_type = extract_delivery_type(product.product_name)

            # 提取交付平台
            product.delivery_platform = extract_platform(product.product_name)

            # 提取关键词
            product.key_keywords = extract_keywords(product.product_name)

        db.commit()
        processed += len(batch)
        print(f"进度: {processed}/{total} ({processed/total*100:.1f}%)")

    return {
        "total": total,
        "processed": processed
    }
```

### 预期结果示例

| 商品名称 | delivery_type | delivery_platform | key_keywords |
|---------|--------------|------------------|--------------|
| Budget Planner Template Notion | Notion Template | Notion | budget, planner |
| Wedding Checklist Printable PDF | Printable | PDF | wedding, checklist |
| Meal Prep Tracker Excel | Tracker | Excel | meal, prep |
| Fitness Workout Planner Canva | Planner | Canva | fitness, workout |

### 成本估算

- **实现方式**: 纯代码规则
- **成本**: $0
- **处理时间**: 5-10 分钟（15,792 条商品）

### 验收标准

- [ ] 15,792 个商品全部处理
- [ ] 交付形式提取覆盖率 > 70%
- [ ] 交付平台提取覆盖率 > 60%
- [ ] 关键词提取覆盖率 = 100%
- [ ] 数据库字段正确更新
- [ ] 前端能够按交付形式筛选
- [ ] 前端能够按交付平台筛选
- [ ] 处理时间 < 10 分钟

---

## 🤖 任务三：P5.2 Top商品AI深度分析

### 任务描述

对每个簇的 Top 3 商品进行 AI 深度分析，提取：
1. **满足的用户需求**（user_need）
2. **验证交付形式**（验证 P5.1 的提取结果）
3. **补充关键词**

### 当前状态

- ✅ 簇数量：675 个
- ✅ 每簇 Top 3 商品：2,025 个商品需要分析
- ❌ 用户需求：未分析

### 实现方案

#### 分析策略

```
675 个簇 × Top 3 商品 = 2,025 个商品需要 AI 分析

策略：
1. 只分析 Top 3 商品（高质量商品）
2. 其他商品继承所属簇的分析结果
3. 批量处理，支持断点续传
```

#### Prompt 设计

```
分析以下 Etsy 商品，提取关键信息：

商品名称：Budget Planner Template Notion - Monthly Finance Tracker

请提取：
1. 满足的用户需求（用户想解决什么问题？）
2. 交付形式（Template/Planner/Tracker等）
3. 交付平台（Notion/Canva/Excel等）
4. 核心关键词（3-5个）

返回 JSON 格式：
{
  "user_need": "帮助用户管理个人或家庭预算，追踪收入和支出",
  "delivery_type": "Planner",
  "delivery_platform": "Notion",
  "keywords": ["budget", "finance", "tracker", "monthly", "planner"]
}
```

#### 数据流程

```
簇ID → 查询Top 3商品 → 逐个调用AI分析 → 解析结果 → 存储到数据库
  ↓                                                        ↓
cluster_id                                      products.user_need
                                                products.delivery_type (验证)
                                                products.key_keywords (补充)
  ↓
其他商品继承簇的 user_need
```

### 技术实现

#### 后端 API 设计

**路由**: `POST /api/products/analyze-top-products`

**请求参数**:
```json
{
  "top_n": 3,
  "batch_size": 10,
  "ai_provider": "deepseek"
}
```

**响应**:
```json
{
  "success": true,
  "total_clusters": 675,
  "total_products_analyzed": 2025,
  "processed": 2025,
  "failed": 0,
  "cost_estimate": "$12.50"
}
```

#### 批量处理代码

```python
async def analyze_top_products(db: Session, top_n: int = 3):
    """分析每个簇的 Top N 商品"""

    # 1. 获取所有簇
    clusters = db.query(Product.cluster_id).distinct().all()

    results = []

    for cluster_id in clusters:
        # 2. 获取簇内 Top N 商品
        top_products = db.query(Product).filter(
            Product.cluster_id == cluster_id,
            Product.is_deleted == False
        ).order_by(
            Product.review_count.desc()
        ).limit(top_n).all()

        cluster_needs = []

        # 3. 逐个分析
        for product in top_products:
            analysis = await analyze_product_with_ai(product.product_name)

            # 4. 更新商品信息
            product.user_need = analysis["user_need"]
            product.delivery_type = analysis["delivery_type"]  # 验证
            product.key_keywords = ", ".join(analysis["keywords"])

            cluster_needs.append(analysis["user_need"])

        # 5. 为簇生成统一的需求描述
        cluster_need = merge_needs(cluster_needs)

        # 6. 其他商品继承簇的需求
        db.query(Product).filter(
            Product.cluster_id == cluster_id,
            Product.product_id.notin_([p.product_id for p in top_products])
        ).update({
            "user_need": cluster_need
        })

        db.commit()

        results.append({
            "cluster_id": cluster_id,
            "cluster_need": cluster_need,
            "analyzed_products": len(top_products)
        })

    return results
```

### 成本估算

- **分析商品数**: 2,025 个（675 簇 × 3 商品）
- **每次调用成本**:
  - DeepSeek: ~$0.006
  - Claude Haiku: ~$0.010
- **总成本**: $10-15

### 预期结果

```
簇ID 1 (Budget Planning Template):
  Top 1: Budget Planner Notion
    → user_need: "帮助用户管理个人或家庭预算，追踪收入和支出"
  Top 2: Monthly Budget Tracker
    → user_need: "帮助用户按月追踪预算执行情况"
  Top 3: Finance Planning Spreadsheet
    → user_need: "帮助用户进行财务规划和分析"

  → 簇统一需求: "预算管理和财务规划"
  → 其他 228 个商品继承此需求
```

### 验收标准

- [ ] 2,025 个 Top 商品全部分析完成
- [ ] 每个商品有 user_need 字段
- [ ] 每个簇有统一的需求描述
- [ ] 其他商品成功继承簇的需求
- [ ] 分析结果准确且有价值
- [ ] 支持断点续传
- [ ] 总处理时间 < 2 小时

---

## 📊 任务四：P3.1 需求分析（包含在 P5.2 中）

### 说明

P3.1 的需求分析功能已经包含在 P5.2 的实现中：

- **P5.2** 分析 Top 商品时提取 `user_need`
- **P5.2** 为每个簇生成统一的需求描述
- **P5.2** 其他商品继承簇的需求

因此，**P3.1 不需要单独实现**，完成 P5.2 即可。

---

## 🎯 任务五：P3.2 交付产品识别（包含在 P5.1 中）

### 说明

P3.2 的交付产品识别功能已经包含在 P5.1 的实现中：

- **P5.1** 提取 `delivery_type`（交付类型）
- **P5.1** 提取 `delivery_platform`（交付平台）

因此，**P3.2 不需要单独实现**，完成 P5.1 即可。

---

## 🚀 实施计划

### 推荐实施顺序

```
第一步：P4.1 类别名称生成
  ↓ 原因：让用户能够快速理解每个簇
  ↓ 时间：2-3 小时
  ↓ 成本：$3-5

第二步：P5.1 商品属性提取
  ↓ 原因：0 成本，快速完成
  ↓ 时间：1-2 小时
  ↓ 成本：$0

第三步：P5.2 Top商品AI分析
  ↓ 原因：提供最深入的洞察
  ↓ 时间：3-4 小时
  ↓ 成本：$10-15
```

### 总体时间和成本

- **总时间**: 6-9 小时
- **总成本**: $13-20
- **完成后**: 所有 P3、P4、P5 任务全部完成

---

## 📋 数据库字段映射

### products 表新增字段

| 字段名 | 来源任务 | 数据类型 | 示例值 |
|--------|---------|---------|--------|
| cluster_name | P4.1 | string | "Budget Planning Template" |
| delivery_type | P5.1 | string | "Planner" |
| delivery_platform | P5.1 | string | "Notion" |
| key_keywords | P5.1 | string | "budget, finance, tracker" |
| user_need | P5.2 | string | "帮助用户管理个人或家庭预算" |

### cluster_summaries 表新增字段

| 字段名 | 来源任务 | 数据类型 | 示例值 |
|--------|---------|---------|--------|
| cluster_name | P4.1 | string | "Budget Planning Template" |
| cluster_need | P5.2 | string | "预算管理和财务规划" |

---

## ✅ 验收清单

### P4.1 类别名称生成
- [ ] 675 个簇全部有类别名称
- [ ] 类别名称格式统一
- [ ] 前端能够显示类别名称
- [ ] 支持按类别筛选商品

### P5.1 商品属性提取
- [ ] 15,792 个商品全部处理
- [ ] 交付形式提取覆盖率 > 70%
- [ ] 交付平台提取覆盖率 > 60%
- [ ] 前端能够按交付形式筛选
- [ ] 前端能够按交付平台筛选

### P5.2 Top商品AI分析
- [ ] 2,025 个 Top 商品全部分析
- [ ] 每个商品有用户需求描述
- [ ] 其他商品成功继承簇的需求
- [ ] 前端能够显示用户需求

### 整体验收
- [ ] 所有数据库字段正确更新
- [ ] 前端界面能够展示所有新字段
- [ ] 筛选和搜索功能正常工作
- [ ] 数据导出包含所有新字段

---

## 🎉 完成后的效果

完成所有任务后，系统将具备：

1. **可读的类别名称**: 675 个簇都有易懂的名称
2. **完整的商品属性**: 每个商品都有交付形式、平台、关键词
3. **深入的需求洞察**: 每个商品都有用户需求描述
4. **强大的筛选功能**: 可以按类别、交付形式、平台筛选
5. **完整的数据导出**: 导出的数据包含所有分析结果

**用户价值**:
- 快速找到目标产品类别
- 了解每个类别满足的用户需求
- 按交付形式和平台筛选商品
- 获得完整的商品洞察数据

---

**准备好开始实施了吗？建议从 P4.1 开始！**

---

*文档生成者: Claude Sonnet 4.5*
*生成时间: 2026-01-29*
