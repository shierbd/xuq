# 数据库迁移方案 v4.3

**创建日期**: 2026-01-28
**目标版本**: v4.3
**迁移类型**: 字段新增

---

## 📋 变更概述

为支持聚类增强和商品属性提取功能，需要在现有数据表中新增字段。

---

## 🗄️ 数据表变更

### 1. products 表（商品表）

#### 新增字段

| 字段名 | 类型 | 默认值 | 可空 | 索引 | 说明 | 对应需求 |
|--------|------|--------|------|------|------|----------|
| cluster_name | VARCHAR(200) | NULL | YES | NO | 类别名称 | P4.1 |
| delivery_type | VARCHAR(100) | NULL | YES | YES | 交付形式 | P5.1 |
| key_keywords | TEXT | NULL | YES | NO | 关键词（逗号分隔） | P5.1 |
| user_need | TEXT | NULL | YES | NO | 满足的用户需求 | P5.2 |

#### SQL 迁移脚本

```sql
-- 添加 cluster_name 字段
ALTER TABLE products ADD COLUMN cluster_name VARCHAR(200) DEFAULT NULL;

-- 添加 delivery_type 字段（带索引，用于筛选）
ALTER TABLE products ADD COLUMN delivery_type VARCHAR(100) DEFAULT NULL;
CREATE INDEX idx_products_delivery_type ON products(delivery_type);

-- 添加 key_keywords 字段
ALTER TABLE products ADD COLUMN key_keywords TEXT DEFAULT NULL;

-- 添加 user_need 字段
ALTER TABLE products ADD COLUMN user_need TEXT DEFAULT NULL;
```

#### 字段说明

**cluster_name**（类别名称）:
- 来源：从 cluster_summaries 表继承
- 填充方式：JOIN cluster_summaries 表
- 示例：`"Budget & Finance Planning"`
- 用途：表格显示、筛选

**delivery_type**（交付形式）:
- 来源：代码规则提取 + AI辅助
- 填充方式：
  1. 代码规则匹配（70-80%）
  2. AI辅助兜底（10-20%）
- 示例：`"Template"`, `"Planner"`, `"Notion Template"`
- 用途：表格显示、筛选、统计

**key_keywords**（关键词）:
- 来源：NLP提取 + AI补充
- 填充方式：
  1. NLP提取名词短语
  2. Top商品AI补充
- 示例：`"Budget, Planner, Finance"`
- 格式：逗号分隔
- 用途：搜索、分析

**user_need**（满足的需求）:
- 来源：AI分析 + 簇级继承
- 填充方式：
  1. Top商品AI分析
  2. 其他商品继承簇的分析结果
- 示例：`"帮助用户管理个人或家庭预算，追踪收支情况"`
- 用途：需求分析、产品定位

---

### 2. cluster_summaries 表（簇汇总表）

#### 新增字段

| 字段名 | 类型 | 默认值 | 可空 | 索引 | 说明 | 对应需求 |
|--------|------|--------|------|------|----------|----------|
| cluster_name | VARCHAR(200) | NULL | YES | NO | 类别名称 | P4.1 |
| common_delivery_type | VARCHAR(100) | NULL | YES | NO | 常见交付形式 | P5.2 |
| user_need | TEXT | NULL | YES | NO | 满足的用户需求 | P5.2 |

#### SQL 迁移脚本

```sql
-- 添加 cluster_name 字段
ALTER TABLE cluster_summaries ADD COLUMN cluster_name VARCHAR(200) DEFAULT NULL;

-- 添加 common_delivery_type 字段
ALTER TABLE cluster_summaries ADD COLUMN common_delivery_type VARCHAR(100) DEFAULT NULL;

-- 添加 user_need 字段
ALTER TABLE cluster_summaries ADD COLUMN user_need TEXT DEFAULT NULL;
```

#### 字段说明

**cluster_name**（类别名称）:
- 来源：AI生成
- 填充方式：调用AI，输入Top 5商品名称
- 示例：`"Budget & Finance Planning"`
- 用途：簇标识、表格显示

**common_delivery_type**（常见交付形式）:
- 来源：统计簇内商品的delivery_type
- 填充方式：取簇内最常见的交付形式
- 示例：`"Template"`
- 用途：簇级统计

**user_need**（满足的需求）:
- 来源：AI分析Top商品
- 填充方式：调用AI分析Top 3商品
- 示例：`"帮助用户管理个人或家庭预算"`
- 用途：需求分析、商品继承

---

## 🔄 数据填充流程

### 阶段1：填充 cluster_summaries.cluster_name（P4.1）

```python
# 伪代码
for cluster in cluster_summaries:
    top_5_products = get_top_products(cluster.cluster_id, limit=5)
    cluster_name = call_ai_generate_name(top_5_products)
    update_cluster_name(cluster.cluster_id, cluster_name)
```

**预计时间**: 5分钟（63个簇）
**成本**: $0.3-0.5

---

### 阶段2：填充 products.cluster_name（P4.1）

```sql
-- 从 cluster_summaries 继承类别名称
UPDATE products p
SET cluster_name = (
    SELECT cluster_name
    FROM cluster_summaries cs
    WHERE cs.cluster_id = p.cluster_id
)
WHERE cluster_id IS NOT NULL;
```

**预计时间**: <1秒
**成本**: 0

---

### 阶段3：填充 products.delivery_type 和 key_keywords（P5.1）

```python
# 伪代码
for product in products:
    # 代码规则提取交付形式
    delivery_type = extract_delivery_type_by_rules(product.product_name)

    # NLP提取关键词
    key_keywords = extract_keywords_by_nlp(product.product_name)

    update_product(product.product_id, delivery_type, key_keywords)
```

**预计时间**: 5分钟（10,000条）
**成本**: 0

---

### 阶段4：填充 cluster_summaries.user_need（P5.2）

```python
# 伪代码
for cluster in cluster_summaries:
    top_3_products = get_top_products(cluster.cluster_id, limit=3)
    user_need = call_ai_analyze_need(top_3_products)
    update_cluster_user_need(cluster.cluster_id, user_need)
```

**预计时间**: 20分钟（63簇 × 3商品 = 189次调用）
**成本**: $1.5-3

---

### 阶段5：填充 products.user_need（P5.2）

```sql
-- 从 cluster_summaries 继承用户需求
UPDATE products p
SET user_need = (
    SELECT user_need
    FROM cluster_summaries cs
    WHERE cs.cluster_id = p.cluster_id
)
WHERE cluster_id IS NOT NULL;
```

**预计时间**: <1秒
**成本**: 0

---

### 阶段6：AI辅助兜底 products.delivery_type（P5.3）

```python
# 伪代码
# 找出代码规则无法提取的商品
products_without_delivery = get_products_where_delivery_type_is_null()

for product in products_without_delivery:
    delivery_type = call_ai_identify_delivery(product.product_name)
    update_product_delivery_type(product.product_id, delivery_type)
```

**预计时间**: 10分钟（30-60个商品）
**成本**: $0.2-0.5

---

### 阶段7：填充 cluster_summaries.common_delivery_type（P5.2）

```sql
-- 统计每个簇最常见的交付形式
UPDATE cluster_summaries cs
SET common_delivery_type = (
    SELECT delivery_type
    FROM products p
    WHERE p.cluster_id = cs.cluster_id
      AND p.delivery_type IS NOT NULL
    GROUP BY delivery_type
    ORDER BY COUNT(*) DESC
    LIMIT 1
);
```

**预计时间**: <1秒
**成本**: 0

---

## 📊 迁移后数据结构

### products 表（13个字段 → 17个字段）

```
原有字段（13个）:
- product_id, product_name, rating, review_count, shop_name, price
- cluster_id, import_time, is_deleted
- delivery_type（旧，将被覆盖）, delivery_format（废弃）, delivery_platform（废弃）

新增字段（4个）:
- cluster_name（类别名称）
- delivery_type（交付形式，覆盖旧字段）
- key_keywords（关键词）
- user_need（满足的需求）

废弃字段（2个）:
- delivery_format（不再使用）
- delivery_platform（不再使用）
```

### cluster_summaries 表（原字段 + 3个新字段）

```
新增字段（3个）:
- cluster_name（类别名称）
- common_delivery_type（常见交付形式）
- user_need（满足的需求）
```

---

## ⚠️ 注意事项

### 1. 字段可空性
- 所有新增字段都允许NULL
- 填充过程是渐进式的，不影响现有功能

### 2. 索引策略
- delivery_type 添加索引（用于筛选）
- 其他字段暂不添加索引（避免影响写入性能）

### 3. 数据一致性
- cluster_name 和 user_need 通过SQL从 cluster_summaries 继承
- 保证数据一致性

### 4. 回滚方案
```sql
-- 如需回滚，删除新增字段
ALTER TABLE products DROP COLUMN cluster_name;
ALTER TABLE products DROP COLUMN delivery_type;
ALTER TABLE products DROP COLUMN key_keywords;
ALTER TABLE products DROP COLUMN user_need;

ALTER TABLE cluster_summaries DROP COLUMN cluster_name;
ALTER TABLE cluster_summaries DROP COLUMN common_delivery_type;
ALTER TABLE cluster_summaries DROP COLUMN user_need;
```

---

## 📈 预期效果

### 数据完整性

| 字段 | 预期填充率 | 说明 |
|------|-----------|------|
| cluster_name | 100% | 所有有cluster_id的商品都有 |
| delivery_type | 90-95% | 代码规则 + AI辅助 |
| key_keywords | 100% | NLP提取 |
| user_need | 100% | 所有有cluster_id的商品都有 |

### 性能影响

- 表大小增加：约10-15%
- 查询性能：delivery_type有索引，筛选快速
- 写入性能：影响<5%

---

## ✅ 验收标准

1. [ ] 所有字段成功添加
2. [ ] 索引创建成功
3. [ ] cluster_name 填充率 = 100%（有cluster_id的商品）
4. [ ] delivery_type 填充率 > 90%
5. [ ] key_keywords 填充率 = 100%
6. [ ] user_need 填充率 = 100%（有cluster_id的商品）
7. [ ] 数据一致性检查通过
8. [ ] 现有功能不受影响

---

*文档创建者: Claude Sonnet 4.5*
*创建时间: 2026-01-28*
