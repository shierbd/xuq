# 数据库设计文档

**项目名称**: 需求挖掘系统
**文档版本**: v1.0
**创建日期**: 2026-01-28
**文档类型**: 数据库设计

---

## 1. 数据库概述

**数据库类型**: SQLite (开发) / PostgreSQL (生产)
**数据库位置**: `data/products.db`
**ORM 框架**: SQLAlchemy 2.0
**数据表数量**: 3 个

---

## 2. 数据表设计

### 2.1 keywords（关键词表）

**用途**: 存储词根聚类模块的关键词短语数据

**表结构**:

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| keyword_id | INTEGER | PRIMARY KEY, AUTOINCREMENT | 关键词ID |
| keyword | VARCHAR(500) | NOT NULL, INDEX | 关键词短语 |
| seed_word | VARCHAR(100) | NOT NULL, INDEX | 来源种子词 |
| seed_group | VARCHAR(100) | NULL | 种子词分组 |
| source | VARCHAR(50) | NULL | 数据来源（semrush/reddit/related_search） |
| intent | VARCHAR(100) | NULL | 搜索意图 |
| volume | INTEGER | NULL | 搜索量 |
| trend | TEXT | NULL | 趋势数据 |
| keyword_difficulty | INTEGER | NULL | 关键词难度 |
| cpc_usd | FLOAT | NULL | CPC（美元） |
| competitive_density | FLOAT | NULL | 竞争密度 |
| serp_features | TEXT | NULL | SERP特征 |
| number_of_results | FLOAT | NULL | 搜索结果数 |
| source_file | VARCHAR(200) | NULL | 来源文件 |
| cluster_id_a | INTEGER | NULL, INDEX | 阶段A聚类ID（-1表示噪音） |
| cluster_id_b | INTEGER | NULL, INDEX | 阶段B聚类ID（-1表示噪音） |
| cluster_size | INTEGER | NULL | 所属簇的大小 |
| is_noise | BOOLEAN | DEFAULT FALSE | 是否为噪音点 |
| word_count | INTEGER | NULL | 单词数量 |
| phrase_length | INTEGER | NULL | 短语长度（字符数） |
| is_selected | BOOLEAN | DEFAULT FALSE | 是否被选为方向 |
| is_low_priority | BOOLEAN | DEFAULT FALSE | 是否标记为低优先级 |
| notes | TEXT | NULL | 备注 |
| import_time | DATETIME | NOT NULL, DEFAULT NOW() | 导入时间 |
| is_deleted | BOOLEAN | NOT NULL, DEFAULT FALSE | 是否已删除（软删除） |

**索引**:
- PRIMARY KEY (keyword_id)
- INDEX (keyword)
- INDEX (seed_word)
- INDEX (cluster_id_a)
- INDEX (cluster_id_b)

**数据示例**:
```sql
INSERT INTO keywords (keyword, seed_word, seed_group, source, volume, cluster_id_a)
VALUES ('compress pdf online', 'compress', 'tools', 'semrush', 12000, 5);
```

---

### 2.2 cluster_summaries（簇汇总表）

**用途**: 存储聚类结果的汇总信息

**表结构**:

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| summary_id | INTEGER | PRIMARY KEY, AUTOINCREMENT | 汇总ID |
| cluster_id | INTEGER | NOT NULL, INDEX | 簇ID |
| stage | VARCHAR(10) | NOT NULL | 阶段（A/B） |
| cluster_size | INTEGER | NOT NULL | 簇大小 |
| seed_words_in_cluster | TEXT | NULL | 簇内种子词列表（逗号分隔） |
| top_keywords | TEXT | NULL | 代表性短语（前5个，逗号分隔） |
| example_phrases | TEXT | NULL | 示例短语 |
| cluster_label | VARCHAR(200) | NULL | 簇标签（AI生成） |
| cluster_explanation | TEXT | NULL | 簇解释（AI生成） |
| avg_volume | FLOAT | NULL | 平均搜索量 |
| total_volume | FLOAT | NULL | 总搜索量 |
| is_direction | BOOLEAN | DEFAULT FALSE | 是否被选为方向 |
| priority | VARCHAR(20) | NULL | 优先级（high/medium/low） |
| created_time | DATETIME | NOT NULL, DEFAULT NOW() | 创建时间 |
| updated_time | DATETIME | NULL | 更新时间 |

**索引**:
- PRIMARY KEY (summary_id)
- INDEX (cluster_id)

**数据示例**:
```sql
INSERT INTO cluster_summaries (cluster_id, stage, cluster_size, top_keywords)
VALUES (5, 'A', 45, 'compress pdf, compress image, compress video, compress file, compress zip');
```

---

### 2.3 products（商品表）

**用途**: 存储商品管理模块的 Etsy 商品数据

**表结构**:

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| product_id | INTEGER | PRIMARY KEY, AUTOINCREMENT | 商品ID |
| product_name | VARCHAR(500) | NOT NULL, INDEX | 商品名称 |
| rating | FLOAT | NULL | 评分（0-5） |
| review_count | INTEGER | NULL | 评价数量 |
| shop_name | VARCHAR(200) | NULL, INDEX | 店铺名称 |
| price | FLOAT | NULL | 价格 |
| cluster_id | INTEGER | NULL, INDEX | 簇ID（-1表示噪音点） |
| delivery_type | VARCHAR(100) | NULL | 交付类型 |
| delivery_format | VARCHAR(100) | NULL | 交付格式 |
| delivery_platform | VARCHAR(100) | NULL | 交付平台 |
| import_time | DATETIME | NOT NULL, DEFAULT NOW() | 导入时间 |
| is_deleted | BOOLEAN | NOT NULL, DEFAULT FALSE | 是否删除（软删除） |

**索引**:
- PRIMARY KEY (product_id)
- INDEX (product_name)
- INDEX (shop_name)
- INDEX (cluster_id)

**数据示例**:
```sql
INSERT INTO products (product_name, rating, review_count, shop_name, price, cluster_id)
VALUES ('Digital Planner Template for Notion', 4.8, 1200, 'DigitalShop', 9.99, 3);
```

---

## 3. 数据关系图

```
┌─────────────────────┐
│     keywords        │
│─────────────────────│
│ keyword_id (PK)     │
│ keyword             │
│ seed_word           │
│ cluster_id_a        │
│ cluster_id_b        │
│ ...                 │
└──────────┬──────────┘
           │ 1
           │
           │ N
┌──────────┴──────────┐
│ cluster_summaries   │
│─────────────────────│
│ summary_id (PK)     │
│ cluster_id          │
│ stage               │
│ cluster_size        │
│ ...                 │
└─────────────────────┘

┌─────────────────────┐
│     products        │
│─────────────────────│
│ product_id (PK)     │
│ product_name        │
│ cluster_id          │
│ rating              │
│ ...                 │
└─────────────────────┘
```

**说明**:
- keywords 表和 cluster_summaries 表通过 cluster_id 关联
- products 表独立存储，通过 cluster_id 可以与 keywords 表进行关联分析
- 所有表都支持软删除（is_deleted 字段）

---

## 4. 数据字典

### 4.1 关键字段说明

#### cluster_id
- **类型**: INTEGER
- **说明**: 聚类ID，-1 表示噪音点
- **用途**: 关联关键词和簇汇总

#### stage
- **类型**: VARCHAR(10)
- **值域**: 'A' 或 'B'
- **说明**: 
  - 'A': 阶段A（种子词扩展与聚类）
  - 'B': 阶段B（方向深化与需求分析）

#### source
- **类型**: VARCHAR(50)
- **值域**: 'semrush', 'reddit', 'related_search'
- **说明**: 数据来源标识

#### is_deleted
- **类型**: BOOLEAN
- **说明**: 软删除标记，TRUE 表示已删除但保留数据

---

## 5. 数据统计

### 5.1 当前数据规模

**keywords 表**:
- 记录数: 6,565 条
- 聚类完成率: 96.6%
- 噪音比例: 3.4%

**products 表**:
- 记录数: 345 条
- 聚类完成率: 99.1%

**cluster_summaries 表**:
- 记录数: 63 个簇（阶段A）

---

## 6. 数据库操作

### 6.1 创建表

```python
from backend.database import Base, engine

# 创建所有表
Base.metadata.create_all(bind=engine)
```

### 6.2 查询示例

```python
from sqlalchemy.orm import Session
from backend.models.keyword import Keyword

# 查询某个簇的所有关键词
def get_keywords_by_cluster(db: Session, cluster_id: int):
    return db.query(Keyword).filter(
        Keyword.cluster_id_a == cluster_id,
        Keyword.is_deleted == False
    ).all()
```

### 6.3 更新示例

```python
# 更新聚类结果
def update_cluster_id(db: Session, keyword_id: int, cluster_id: int):
    keyword = db.query(Keyword).filter(Keyword.keyword_id == keyword_id).first()
    if keyword:
        keyword.cluster_id_a = cluster_id
        db.commit()
```

---

## 7. 数据迁移

### 7.1 SQLite → PostgreSQL

**步骤**:
1. 导出 SQLite 数据
2. 修改数据库连接配置
3. 创建 PostgreSQL 表结构
4. 导入数据

**工具**: Alembic (数据库迁移工具)

---

## 8. 性能优化

### 8.1 索引优化

- 为高频查询字段建立索引
- 复合索引优化多条件查询

### 8.2 查询优化

- 使用分页查询
- 避免 SELECT *
- 使用连接查询代替多次查询

---

*文档创建者: Claude Sonnet 4.5*
*最后更新: 2026-01-28*
