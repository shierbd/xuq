# 设计变更记录

> 本文档记录系统设计的所有变更历史

---

## [v1.1] - 2026-01-14

### 新增功能：Phase 7 - 商品筛选与AI标注系统

#### 变更类型
- 新增数据表
- 新增业务模块
- 新增Web UI页面

#### 变更内容

**1. 数据库设计变更**

新增3张数据表：

- **products** (商品主表)
  - 17个字段，包含核心字段、AI生成字段、动态字段
  - 支持Etsy、Gumroad等电商平台
  - 使用JSON字段存储动态自定义字段
  - 唯一索引：url（防止重复导入）

- **product_field_definitions** (字段定义表)
  - 10个字段，支持动态字段管理
  - 类似飞书多维表格的字段定义
  - 支持8种字段类型：text/number/date/url/tags/select/multi_select/textarea

- **product_import_logs** (导入日志表)
  - 12个字段，记录导入历史
  - 存储字段映射配置（JSON格式）
  - 支持导入性能监控和错误追踪

**2. 架构设计变更**

新增模块：

- **core/product_management.py**
  - 商品数据导入和清理
  - 字段映射配置管理
  - AI标注调度
  - 动态字段管理

- **storage/product_repository.py**
  - ProductRepository: 商品CRUD操作
  - ProductFieldDefinitionRepository: 字段定义操作
  - ProductImportLogRepository: 导入日志操作

- **ui/pages/phase7_products.py**
  - 商品数据导入界面
  - 字段映射配置界面
  - 商品筛选和排序界面
  - AI标注配置和执行界面
  - 动态字段管理界面
  - 数据导出界面

**3. 数据流设计**

新增Phase 7数据流：
```
商品数据文件 (CSV/Excel)
    ↓
product_management.py (字段映射、清洗、去重)
    ↓
ProductRepository.bulk_insert_products()
    ↓
products表
    ↓
llm_service.py (AI标注：标签生成、需求判断)
    ↓
ProductRepository.update_ai_analysis()
    ↓
products.tags, products.demand_analysis 更新
    ↓
导出筛选结果
```

#### 影响范围

**数据库层**:
- 新增3张表
- 新增4个枚举类型
- 新增6个索引

**业务逻辑层**:
- 新增1个核心模块（product_management.py）
- 复用现有LLM服务（llm_service.py）

**数据访问层**:
- 新增3个ORM模型
- 新增3个Repository类

**Web UI层**:
- 新增1个页面（phase7_products.py）
- 更新主导航菜单

**配置层**:
- 复用ai_prompt_configs表
- 新增2个feature_name值：product_tagging, product_demand_analysis

#### 设计决策

**1. 动态字段存储方案**

选择：**混合方案（固定字段 + JSON动态字段 + 元数据表）**

理由：
- 避免频繁ALTER TABLE操作
- 保持核心字段的查询性能
- 支持灵活的字段扩展
- 类似飞书多维表格的实现方式

备选方案：
- 方案A：纯JSON存储（查询性能差）
- 方案B：预设通用字段（不够灵活）
- 方案C：动态ALTER TABLE（复杂且有风险）

**2. 去重策略**

选择：**按URL去重（优先）+ 按名称+店铺去重（备选）**

理由：
- URL是商品的唯一标识
- 同一商品可能有多个数据源
- 保留最新的记录

**3. AI标注方式**

选择：**批量标注（每批10条）+ 异步处理**

理由：
- 提高API调用效率
- 支持大规模数据处理
- 便于错误重试和断点续传

**4. 字段映射配置**

选择：**导入时手动指定 + 配置保存复用**

理由：
- 每个平台的数据格式可能不同
- 支持无列名文件导入
- 配置可保存供下次导入复用

#### 迁移建议

**数据库迁移**:

```sql
-- MySQL
CREATE TABLE products (
    product_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(500) NOT NULL,
    description TEXT,
    price DECIMAL(10,2),
    sales INT DEFAULT 0,
    rating DECIMAL(3,2),
    review_count INT DEFAULT 0,
    url VARCHAR(1000) UNIQUE,
    shop_name VARCHAR(200),
    platform ENUM('etsy', 'gumroad') NOT NULL,
    source_file VARCHAR(255),
    tags TEXT,
    demand_analysis TEXT,
    ai_analysis_status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
    custom_fields JSON,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_product_name (product_name),
    INDEX idx_review_count (review_count),
    INDEX idx_shop_name (shop_name),
    INDEX idx_platform (platform),
    INDEX idx_ai_status (ai_analysis_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE product_field_definitions (
    field_id INT AUTO_INCREMENT PRIMARY KEY,
    field_name VARCHAR(100) NOT NULL,
    field_key VARCHAR(100) UNIQUE NOT NULL,
    field_type ENUM('text', 'number', 'date', 'url', 'tags', 'select', 'multi_select', 'textarea') NOT NULL,
    is_required BOOLEAN DEFAULT FALSE,
    default_value VARCHAR(500),
    field_options TEXT,
    field_order INT DEFAULT 0,
    field_description VARCHAR(500),
    is_system_field BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_field_order (field_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE product_import_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    source_file VARCHAR(255) NOT NULL,
    platform ENUM('etsy', 'gumroad') NOT NULL,
    total_rows INT NOT NULL,
    imported_rows INT NOT NULL,
    skipped_rows INT DEFAULT 0,
    duplicate_rows INT DEFAULT 0,
    field_mapping TEXT,
    import_status ENUM('in_progress', 'completed', 'failed') DEFAULT 'in_progress',
    error_message TEXT,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_seconds INT,
    INDEX idx_platform (platform),
    INDEX idx_status (import_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**SQLite迁移**:
- 将ENUM替换为VARCHAR + CHECK约束
- 将JSON替换为TEXT

**代码修改**:

1. 创建ORM模型（storage/models.py）
2. 创建Repository类（storage/product_repository.py）
3. 创建业务逻辑（core/product_management.py）
4. 创建Web UI页面（ui/pages/phase7_products.py）
5. 更新主导航菜单（web_ui.py）

**测试建议**:

1. 单元测试：
   - ProductRepository CRUD操作
   - 字段映射逻辑
   - 数据清洗和去重逻辑
   - AI标注调度逻辑

2. 集成测试：
   - 完整的导入流程
   - AI标注流程
   - 筛选和排序功能
   - 动态字段管理

3. 性能测试：
   - 导入10万条商品数据
   - 批量AI标注性能
   - 复杂筛选查询性能

#### 文档更新

- ✅ docs/requirements.md (v1.2)
- ✅ docs/design/database-design.md (v1.1)
- ✅ docs/design/architecture.md (v1.1)
- ✅ docs/design/CHANGELOG.md (新建)

#### 相关需求

- 需求文档：docs/requirements.md - 2.7 商品筛选与AI标注系统 (Phase 7)
- 需求版本：v1.2
- 需求添加日期：2026-01-14

---

## [v1.0] - 2026-01-08

### 初始版本

#### 变更内容

- 创建数据库设计文档
- 创建架构设计文档
- 定义7张核心数据表
- 定义分层架构
- 定义数据流

---

**文档维护**: 每次设计变更都应更新此文档
**文档格式**: 遵循 [Keep a Changelog](https://keepachangelog.com/) 规范
