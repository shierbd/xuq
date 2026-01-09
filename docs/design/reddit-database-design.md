# Reddit板块分析与标注系统 - 数据库设计文档

**版本**: v1.0
**创建日期**: 2026-01-09
**作者**: Claude Code
**状态**: 设计完成

---

## 目录

1. [概述](#概述)
2. [数据表设计](#数据表设计)
3. [ER关系图](#er关系图)
4. [索引设计](#索引设计)
5. [SQL脚本](#sql脚本)
6. [数据字典](#数据字典)
7. [字段映射](#字段映射)

---

## 概述

### 设计目标

Reddit板块分析与标注系统需要两张核心数据表：
1. **reddit_subreddits** - 存储Reddit板块数据及AI分析结果
2. **ai_prompt_configs** - 存储AI提示词配置

### 设计原则

- **兼容性**: 同时支持MySQL和SQLite
- **可扩展性**: 预留扩展字段
- **性能优化**: 合理设计索引
- **数据完整性**: 使用约束保证数据质量
- **UTF-8编码**: 全面支持中文

---

## 数据表设计

### 表1: reddit_subreddits

Reddit板块数据表，存储板块基本信息和AI分析结果。

#### 表结构

| 字段名 | 数据类型 | 约束 | 默认值 | 说明 |
|--------|---------|------|--------|------|
| subreddit_id | INT | PRIMARY KEY, AUTO_INCREMENT | - | 主键ID |
| name | VARCHAR(255) | NOT NULL, UNIQUE | - | 板块名称（唯一） |
| description | TEXT | NULL | NULL | 板块描述 |
| subscribers | BIGINT | NULL | 0 | 订阅人数 |
| tag1 | VARCHAR(100) | NULL | NULL | AI生成标签1（中文） |
| tag2 | VARCHAR(100) | NULL | NULL | AI生成标签2（中文） |
| tag3 | VARCHAR(100) | NULL | NULL | AI生成标签3（中文） |
| importance_score | INT | NULL, CHECK(1-5) | NULL | 重要性评分(1-5) |
| ai_analysis_status | VARCHAR(20) | NOT NULL | 'pending' | AI分析状态 |
| ai_analysis_timestamp | TIMESTAMP | NULL | NULL | AI分析时间戳 |
| ai_model_used | VARCHAR(100) | NULL | NULL | 使用的AI模型 |
| ai_confidence | INT | NULL, CHECK(0-100) | NULL | AI置信度(0-100) |
| notes | TEXT | NULL | NULL | 备注信息 |
| import_batch_id | VARCHAR(50) | NULL | NULL | 导入批次ID |
| created_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | 更新时间 |

#### 枚举值说明

**ai_analysis_status** 可选值：
- `pending`: 待分析
- `processing`: 分析中
- `completed`: 已完成
- `failed`: 分析失败
- `skipped`: 已跳过（描述为空）

---

### 表2: ai_prompt_configs

AI提示词配置表，存储不同场景的提示词模板。

#### 表结构

| 字段名 | 数据类型 | 约束 | 默认值 | 说明 |
|--------|---------|------|--------|------|
| config_id | INT | PRIMARY KEY, AUTO_INCREMENT | - | 主键ID |
| config_name | VARCHAR(100) | NOT NULL, UNIQUE | - | 配置名称（唯一） |
| config_type | VARCHAR(50) | NOT NULL | 'reddit_analysis' | 配置类型 |
| prompt_template | TEXT | NOT NULL | - | 提示词模板 |
| system_message | TEXT | NULL | NULL | 系统消息 |
| temperature | DECIMAL(3,2) | NULL, CHECK(0-2) | 0.7 | 温度参数(0-2) |
| max_tokens | INT | NULL | 500 | 最大token数 |
| is_active | BOOLEAN | NOT NULL | TRUE | 是否启用 |
| is_default | BOOLEAN | NOT NULL | FALSE | 是否默认配置 |
| description | TEXT | NULL | NULL | 配置说明 |
| created_by | VARCHAR(100) | NULL | 'system' | 创建者 |
| created_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | 更新时间 |

---

## ER关系图

```
┌─────────────────────────────┐
│   reddit_subreddits         │
├─────────────────────────────┤
│ PK subreddit_id (INT)       │
│    name (VARCHAR) UNIQUE    │
│    description (TEXT)       │
│    subscribers (BIGINT)     │
│    tag1 (VARCHAR)           │
│    tag2 (VARCHAR)           │
│    tag3 (VARCHAR)           │
│    importance_score (INT)   │
│    ai_analysis_status       │
│    ai_analysis_timestamp    │
│    ai_model_used            │
│    ai_confidence            │
│    notes (TEXT)             │
│    import_batch_id          │
│    created_at               │
│    updated_at               │
└─────────────────────────────┘
         │
         │ (使用配置)
         │ 逻辑关联
         ▼
┌─────────────────────────────┐
│   ai_prompt_configs         │
├─────────────────────────────┤
│ PK config_id (INT)          │
│    config_name (VARCHAR)    │
│    config_type (VARCHAR)    │
│    prompt_template (TEXT)   │
│    system_message (TEXT)    │
│    temperature (DECIMAL)    │
│    max_tokens (INT)         │
│    is_active (BOOLEAN)      │
│    is_default (BOOLEAN)     │
│    description (TEXT)       │
│    created_by (VARCHAR)     │
│    created_at               │
│    updated_at               │
└─────────────────────────────┘
```

### 关系说明

- **reddit_subreddits** 和 **ai_prompt_configs** 之间是**逻辑关联**（非外键）
- 分析时通过 `config_type='reddit_analysis'` 和 `is_active=TRUE` 查询配置
- 支持多个配置共存，通过 `is_default` 标识默认配置

---

## 索引设计

### reddit_subreddits 表索引

```sql
-- 主键索引（自动创建）
PRIMARY KEY (subreddit_id)

-- 唯一索引
UNIQUE INDEX idx_subreddit_name (name)

-- 普通索引
INDEX idx_analysis_status (ai_analysis_status)
INDEX idx_importance_score (importance_score)
INDEX idx_import_batch (import_batch_id)
INDEX idx_created_at (created_at)

-- 复合索引
INDEX idx_status_score (ai_analysis_status, importance_score)
INDEX idx_batch_status (import_batch_id, ai_analysis_status)
```

### ai_prompt_configs 表索引

```sql
-- 主键索引（自动创建）
PRIMARY KEY (config_id)

-- 唯一索引
UNIQUE INDEX idx_config_name (config_name)

-- 普通索引
INDEX idx_config_type (config_type)
INDEX idx_is_active (is_active)
INDEX idx_is_default (is_default)

-- 复合索引
INDEX idx_type_active (config_type, is_active)
INDEX idx_type_default (config_type, is_default)
```

---

## SQL脚本

### MySQL创建脚本

```sql
-- ==================== MySQL版本 ====================

-- 1. 创建reddit_subreddits表
CREATE TABLE IF NOT EXISTS reddit_subreddits (
    subreddit_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    name VARCHAR(255) NOT NULL UNIQUE COMMENT '板块名称',
    description TEXT COMMENT '板块描述',
    subscribers BIGINT DEFAULT 0 COMMENT '订阅人数',
    tag1 VARCHAR(100) COMMENT 'AI生成标签1',
    tag2 VARCHAR(100) COMMENT 'AI生成标签2',
    tag3 VARCHAR(100) COMMENT 'AI生成标签3',
    importance_score INT COMMENT '重要性评分(1-5)',
    ai_analysis_status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT 'AI分析状态',
    ai_analysis_timestamp TIMESTAMP NULL COMMENT 'AI分析时间戳',
    ai_model_used VARCHAR(100) COMMENT '使用的AI模型',
    ai_confidence INT COMMENT 'AI置信度(0-100)',
    notes TEXT COMMENT '备注信息',
    import_batch_id VARCHAR(50) COMMENT '导入批次ID',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    -- 约束
    CONSTRAINT chk_importance_score CHECK (importance_score IS NULL OR (importance_score >= 1 AND importance_score <= 5)),
    CONSTRAINT chk_ai_confidence CHECK (ai_confidence IS NULL OR (ai_confidence >= 0 AND ai_confidence <= 100)),
    CONSTRAINT chk_subscribers CHECK (subscribers >= 0),

    -- 索引
    INDEX idx_analysis_status (ai_analysis_status),
    INDEX idx_importance_score (importance_score),
    INDEX idx_import_batch (import_batch_id),
    INDEX idx_created_at (created_at),
    INDEX idx_status_score (ai_analysis_status, importance_score),
    INDEX idx_batch_status (import_batch_id, ai_analysis_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Reddit板块数据表';

-- 2. 创建ai_prompt_configs表
CREATE TABLE IF NOT EXISTS ai_prompt_configs (
    config_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    config_name VARCHAR(100) NOT NULL UNIQUE COMMENT '配置名称',
    config_type VARCHAR(50) NOT NULL DEFAULT 'reddit_analysis' COMMENT '配置类型',
    prompt_template TEXT NOT NULL COMMENT '提示词模板',
    system_message TEXT COMMENT '系统消息',
    temperature DECIMAL(3,2) DEFAULT 0.7 COMMENT '温度参数(0-2)',
    max_tokens INT DEFAULT 500 COMMENT '最大token数',
    is_active BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否启用',
    is_default BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否默认配置',
    description TEXT COMMENT '配置说明',
    created_by VARCHAR(100) DEFAULT 'system' COMMENT '创建者',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    -- 约束
    CONSTRAINT chk_temperature CHECK (temperature >= 0 AND temperature <= 2),
    CONSTRAINT chk_max_tokens CHECK (max_tokens > 0 AND max_tokens <= 10000),

    -- 索引
    INDEX idx_config_type (config_type),
    INDEX idx_is_active (is_active),
    INDEX idx_is_default (is_default),
    INDEX idx_type_active (config_type, is_active),
    INDEX idx_type_default (config_type, is_default)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI提示词配置表';

-- 3. 插入默认配置
INSERT INTO ai_prompt_configs (
    config_name,
    config_type,
    prompt_template,
    system_message,
    is_default,
    description
) VALUES (
    'Reddit板块分析默认配置',
    'reddit_analysis',
    '请分析以下Reddit板块信息，生成3个中文标签和重要性评分(1-5)：

板块名称：{name}
板块描述：{description}
订阅人数：{subscribers}

要求：
1. 生成3个简洁的中文标签（每个2-4个字）
2. 评估重要性评分（1=不重要，5=非常重要）
3. 返回JSON格式：{{"tag1": "标签1", "tag2": "标签2", "tag3": "标签3", "importance_score": 评分, "confidence": 置信度}}',
    '你是一个专业的Reddit社区分析专家，擅长理解社区主题和评估其重要性。',
    TRUE,
    '默认的Reddit板块分析配置，用于生成标签和重要性评分'
);
```

### SQLite创建脚本

```sql
-- ==================== SQLite版本 ====================

-- 1. 创建reddit_subreddits表
CREATE TABLE IF NOT EXISTS reddit_subreddits (
    subreddit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    subscribers INTEGER DEFAULT 0,
    tag1 TEXT,
    tag2 TEXT,
    tag3 TEXT,
    importance_score INTEGER,
    ai_analysis_status TEXT NOT NULL DEFAULT 'pending'
        CHECK(ai_analysis_status IN ('pending', 'processing', 'completed', 'failed', 'skipped')),
    ai_analysis_timestamp TEXT,
    ai_model_used TEXT,
    ai_confidence INTEGER,
    notes TEXT,
    import_batch_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),

    -- 约束
    CHECK (importance_score IS NULL OR (importance_score >= 1 AND importance_score <= 5)),
    CHECK (ai_confidence IS NULL OR (ai_confidence >= 0 AND ai_confidence <= 100)),
    CHECK (subscribers >= 0)
);

-- 创建索引
CREATE INDEX idx_analysis_status ON reddit_subreddits(ai_analysis_status);
CREATE INDEX idx_importance_score ON reddit_subreddits(importance_score);
CREATE INDEX idx_import_batch ON reddit_subreddits(import_batch_id);
CREATE INDEX idx_created_at ON reddit_subreddits(created_at);
CREATE INDEX idx_status_score ON reddit_subreddits(ai_analysis_status, importance_score);
CREATE INDEX idx_batch_status ON reddit_subreddits(import_batch_id, ai_analysis_status);

-- 创建更新时间触发器
CREATE TRIGGER update_reddit_subreddits_timestamp
AFTER UPDATE ON reddit_subreddits
BEGIN
    UPDATE reddit_subreddits SET updated_at = datetime('now') WHERE subreddit_id = NEW.subreddit_id;
END;

-- 2. 创建ai_prompt_configs表
CREATE TABLE IF NOT EXISTS ai_prompt_configs (
    config_id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_name TEXT NOT NULL UNIQUE,
    config_type TEXT NOT NULL DEFAULT 'reddit_analysis',
    prompt_template TEXT NOT NULL,
    system_message TEXT,
    temperature REAL DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 500,
    is_active INTEGER NOT NULL DEFAULT 1,
    is_default INTEGER NOT NULL DEFAULT 0,
    description TEXT,
    created_by TEXT DEFAULT 'system',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),

    -- 约束
    CHECK (temperature >= 0 AND temperature <= 2),
    CHECK (max_tokens > 0 AND max_tokens <= 10000),
    CHECK (is_active IN (0, 1)),
    CHECK (is_default IN (0, 1))
);

-- 创建索引
CREATE INDEX idx_config_type ON ai_prompt_configs(config_type);
CREATE INDEX idx_is_active ON ai_prompt_configs(is_active);
CREATE INDEX idx_is_default ON ai_prompt_configs(is_default);
CREATE INDEX idx_type_active ON ai_prompt_configs(config_type, is_active);
CREATE INDEX idx_type_default ON ai_prompt_configs(config_type, is_default);

-- 创建更新时间触发器
CREATE TRIGGER update_ai_prompt_configs_timestamp
AFTER UPDATE ON ai_prompt_configs
BEGIN
    UPDATE ai_prompt_configs SET updated_at = datetime('now') WHERE config_id = NEW.config_id;
END;

-- 3. 插入默认配置
INSERT INTO ai_prompt_configs (
    config_name,
    config_type,
    prompt_template,
    system_message,
    is_default,
    description
) VALUES (
    'Reddit板块分析默认配置',
    'reddit_analysis',
    '请分析以下Reddit板块信息，生成3个中文标签和重要性评分(1-5)：

板块名称：{name}
板块描述：{description}
订阅人数：{subscribers}

要求：
1. 生成3个简洁的中文标签（每个2-4个字）
2. 评估重要性评分（1=不重要，5=非常重要）
3. 返回JSON格式：{"tag1": "标签1", "tag2": "标签2", "tag3": "标签3", "importance_score": 评分, "confidence": 置信度}',
    '你是一个专业的Reddit社区分析专家，擅长理解社区主题和评估其重要性。',
    1,
    '默认的Reddit板块分析配置，用于生成标签和重要性评分'
);
```

---

## 数据字典

### reddit_subreddits 表字典

| 字段名 | 中文名 | 数据类型 | 长度 | 必填 | 默认值 | 说明 |
|--------|--------|---------|------|------|--------|------|
| subreddit_id | 板块ID | INT | - | 是 | AUTO | 主键，自增 |
| name | 板块名称 | VARCHAR | 255 | 是 | - | 唯一，如"python" |
| description | 板块描述 | TEXT | 65535 | 否 | NULL | 板块简介 |
| subscribers | 订阅人数 | BIGINT | - | 否 | 0 | 订阅者数量 |
| tag1 | 标签1 | VARCHAR | 100 | 否 | NULL | AI生成的第1个标签 |
| tag2 | 标签2 | VARCHAR | 100 | 否 | NULL | AI生成的第2个标签 |
| tag3 | 标签3 | VARCHAR | 100 | 否 | NULL | AI生成的第3个标签 |
| importance_score | 重要性评分 | INT | - | 否 | NULL | 1-5分，5最重要 |
| ai_analysis_status | 分析状态 | VARCHAR | 20 | 是 | pending | 见枚举值说明 |
| ai_analysis_timestamp | 分析时间 | TIMESTAMP | - | 否 | NULL | AI分析完成时间 |
| ai_model_used | AI模型 | VARCHAR | 100 | 否 | NULL | 如"gpt-4o-mini" |
| ai_confidence | AI置信度 | INT | - | 否 | NULL | 0-100，100最高 |
| notes | 备注 | TEXT | 65535 | 否 | NULL | 人工备注 |
| import_batch_id | 导入批次 | VARCHAR | 50 | 否 | NULL | 批次标识 |
| created_at | 创建时间 | TIMESTAMP | - | 是 | NOW() | 记录创建时间 |
| updated_at | 更新时间 | TIMESTAMP | - | 是 | NOW() | 记录更新时间 |

### ai_prompt_configs 表字典

| 字段名 | 中文名 | 数据类型 | 长度 | 必填 | 默认值 | 说明 |
|--------|--------|---------|------|------|--------|------|
| config_id | 配置ID | INT | - | 是 | AUTO | 主键，自增 |
| config_name | 配置名称 | VARCHAR | 100 | 是 | - | 唯一 |
| config_type | 配置类型 | VARCHAR | 50 | 是 | reddit_analysis | 配置类型 |
| prompt_template | 提示词模板 | TEXT | 65535 | 是 | - | 支持变量占位符 |
| system_message | 系统消息 | TEXT | 65535 | 否 | NULL | AI系统角色设定 |
| temperature | 温度参数 | DECIMAL | 3,2 | 否 | 0.7 | 0-2，控制随机性 |
| max_tokens | 最大Token数 | INT | - | 否 | 500 | 1-10000 |
| is_active | 是否启用 | BOOLEAN | - | 是 | TRUE | TRUE/FALSE |
| is_default | 是否默认 | BOOLEAN | - | 是 | FALSE | TRUE/FALSE |
| description | 配置说明 | TEXT | 65535 | 否 | NULL | 配置用途描述 |
| created_by | 创建者 | VARCHAR | 100 | 否 | system | 用户名或"system" |
| created_at | 创建时间 | TIMESTAMP | - | 是 | NOW() | 记录创建时间 |
| updated_at | 更新时间 | TIMESTAMP | - | 是 | NOW() | 记录更新时间 |

---

## 字段映射

### 数据库 ↔ Python对象 ↔ UI字段

#### reddit_subreddits 映射

| 数据库字段 | Python属性 | UI显示名称 | UI组件类型 | 备注 |
|-----------|-----------|-----------|-----------|------|
| subreddit_id | subreddit_id | ID | text_input (disabled) | 只读 |
| name | name | 板块名称 | text_input | 必填 |
| description | description | 板块描述 | text_area | 可选 |
| subscribers | subscribers | 订阅人数 | number_input | 可选 |
| tag1 | tag1 | 标签1 | text_input | AI生成 |
| tag2 | tag2 | 标签2 | text_input | AI生成 |
| tag3 | tag3 | 标签3 | text_input | AI生成 |
| importance_score | importance_score | 重要性评分 | slider (1-5) | AI生成 |
| ai_analysis_status | ai_analysis_status | 分析状态 | selectbox | 状态选择 |
| notes | notes | 备注 | text_area | 可编辑 |

---

**文档版本**: v1.0
**最后更新**: 2026-01-09
