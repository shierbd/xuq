"""
MVP版本数据库模型
使用SQLAlchemy ORM定义四张核心表：
1. Phrase - 短语总库
2. Demand - 需求卡片
3. Token - 需求框架词库
4. ClusterMeta - 聚类元数据

注意：兼容MySQL和SQLite
- MySQL使用ENUM类型
- SQLite使用String + CheckConstraint
"""
from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    BigInteger,
    String,
    Text,
    Enum as SQLEnum,
    Boolean,
    TIMESTAMP,
    DECIMAL,
    Index,
    CheckConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config.settings import DATABASE_URL, DATABASE_CONFIG

Base = declarative_base()

# 判断数据库类型
IS_SQLITE = DATABASE_CONFIG["type"] == "sqlite"


def enum_column(name, values, **kwargs):
    """
    创建兼容MySQL和SQLite的枚举列

    Args:
        name: 列名
        values: 枚举值列表
        **kwargs: 其他列参数

    Returns:
        Column对象
    """
    if IS_SQLITE:
        # SQLite使用String + CheckConstraint
        check_name = f"check_{name}"
        check_constraint = CheckConstraint(
            f"{name} IN ({', '.join(repr(v) for v in values)})",
            name=check_name
        )
        return Column(String(50), CheckConstraint(
            f"{name} IN ({', '.join(repr(v) for v in values)})"
        ), **kwargs)
    else:
        # MySQL使用原生ENUM
        enum_name = kwargs.pop('enum_name', f"{name}_enum")
        return Column(SQLEnum(*values, name=enum_name), **kwargs)


# ==================== 1. Phrase 短语总库 ====================
class Phrase(Base):
    """短语总库 - 存储所有搜索关键词短语"""

    __tablename__ = "phrases"

    # 主键
    phrase_id = Column(BigInteger, primary_key=True, autoincrement=True)
    phrase = Column(String(255), unique=True, nullable=False, index=True)

    # 来源信息
    seed_word = Column(String(100))
    source_type = enum_column(
        "source_type",
        ["semrush", "dropdown", "related_search"],
        enum_name="source_type_enum",
        index=True
    )
    first_seen_round = Column(Integer, nullable=False, index=True)

    # 统计数据
    frequency = Column(BigInteger, default=1)
    volume = Column(BigInteger, default=0)

    # 聚类分配
    cluster_id_A = Column(Integer, index=True)  # 大组ID
    cluster_id_B = Column(Integer)              # 小组ID

    # 需求关联
    mapped_demand_id = Column(Integer, index=True)

    # 处理状态
    processed_status = enum_column(
        "processed_status",
        ["unseen", "reviewed", "assigned", "archived"],
        enum_name="processed_status_enum",
        default="unseen",
        index=True
    )

    # 元数据
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<Phrase(id={self.phrase_id}, phrase='{self.phrase}', cluster_A={self.cluster_id_A})>"


# ==================== 2. Demand 需求卡片 ====================
class Demand(Base):
    """需求卡片库 - 存储挖掘出的用户需求"""

    __tablename__ = "demands"

    # 主键
    demand_id = Column(Integer, primary_key=True, autoincrement=True)

    # 需求描述（核心）
    title = Column(String(255), nullable=False)
    description = Column(Text)
    user_scenario = Column(Text)

    # 分类
    demand_type = enum_column(
        "demand_type",
        ["tool", "content", "service", "education", "other"],
        enum_name="demand_type_enum",
        index=True
    )

    # 关联信息
    source_cluster_A = Column(Integer, index=True)
    source_cluster_B = Column(Integer)
    related_phrases_count = Column(Integer, default=0)

    # 商业评估（简化）
    business_value = enum_column(
        "business_value",
        ["high", "medium", "low", "unknown"],
        enum_name="business_value_enum",
        default="unknown",
        index=True
    )

    # 状态追踪
    status = enum_column(
        "status",
        ["idea", "validated", "in_progress", "archived"],
        enum_name="demand_status_enum",
        default="idea",
        index=True
    )

    # 元数据
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<Demand(id={self.demand_id}, title='{self.title}', status='{self.status}')>"


# ==================== 3. Token 需求框架词库 ====================
class Token(Base):
    """需求框架词库 - 存储意图词、动作词、对象词等"""

    __tablename__ = "tokens"

    # 主键
    token_id = Column(Integer, primary_key=True, autoincrement=True)
    token_text = Column(String(100), unique=True, nullable=False, index=True)

    # 分类（核心）
    token_type = enum_column(
        "token_type",
        ["intent", "action", "object", "attribute", "condition", "other"],
        enum_name="token_type_enum",
        nullable=False,
        index=True
    )

    # 统计信息
    in_phrase_count = Column(Integer, default=0, index=True)

    # 来源追踪
    first_seen_round = Column(Integer, nullable=False)

    # 验证状态
    verified = Column(Boolean, default=False, index=True)
    notes = Column(Text)

    # 元数据
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    def __repr__(self):
        return f"<Token(id={self.token_id}, text='{self.token_text}', type='{self.token_type}')>"


# ==================== 4. WordSegment 分词结果库 ====================
class WordSegment(Base):
    """分词结果库 - 存储关键词分词后的单词和短语统计

    支持存储：
    - 单词（word_count=1）：如 'free', 'best'
    - 短语（word_count>1）：如 'best free', 'how to'
    """

    __tablename__ = "word_segments"

    # 主键
    word_id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String(255), unique=True, nullable=False, index=True)  # 扩展长度支持短语

    # 统计信息
    frequency = Column(Integer, default=1, index=True)  # 出现频次
    word_count = Column(Integer, default=1, index=True)  # 词数（1=单词，>1=短语）

    # 词性信息（仅对单词有效，短语为NULL）
    pos_tag = Column(String(20))  # 详细词性标签（如NN, VBG）
    pos_category = Column(String(20), index=True)  # 词性分类（如Noun, Verb）
    pos_chinese = Column(String(50))  # 中文词性名称

    # 翻译
    translation = Column(String(200))  # 中文翻译

    # 词根标记
    is_root = Column(Boolean, default=False, index=True)  # 是否为词根
    root_round = Column(Integer)  # 标记为词根的轮次
    root_source = Column(String(50))  # 词根来源：initial_import, user_selected

    # 元数据
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def __repr__(self):
        root_mark = "⭐" if self.is_root else ""
        token_type = "短语" if self.word_count > 1 else "单词"
        return f"<WordSegment({token_type}: '{self.word}', freq={self.frequency}{root_mark})>"


# ==================== 5. SegmentationBatch 分词批次记录 ====================
class SegmentationBatch(Base):
    """分词批次记录 - 记录每次分词的元数据"""

    __tablename__ = "segmentation_batches"

    # 主键
    batch_id = Column(Integer, primary_key=True, autoincrement=True)

    # 批次信息
    batch_date = Column(TIMESTAMP, default=datetime.utcnow)
    phrase_count = Column(Integer)  # 处理了多少个短语
    word_count = Column(Integer)  # 生成了多少个单词
    new_word_count = Column(Integer)  # 新增了多少个单词
    duration_seconds = Column(Integer)  # 耗时（秒）

    # 状态
    status = enum_column(
        "status",
        ["completed", "failed", "in_progress"],
        enum_name="batch_status_enum",
        default="in_progress",
        index=True
    )

    # 备注
    notes = Column(Text)

    def __repr__(self):
        return f"<SegmentationBatch(id={self.batch_id}, phrases={self.phrase_count}, status='{self.status}')>"


# ==================== 6. SeedWord 词根管理 ====================
class SeedWord(Base):
    """词根管理表 - 管理所有seed_word的分类、定义和关联

    使用Token框架进行分类（intent/action/object/other）
    """

    __tablename__ = "seed_words"

    # 主键
    seed_id = Column(Integer, primary_key=True, autoincrement=True)
    seed_word = Column(String(100), unique=True, nullable=False, index=True)

    # Token框架分类（核心）- 支持多分类
    token_types = Column(Text)  # JSON格式数组: ["intent", "action"]
    primary_token_type = enum_column(
        "primary_token_type",
        ["intent", "action", "object", "other"],
        enum_name="seed_primary_token_type_enum",
        index=True
    )  # 主要类别（用于快速筛选和排序）

    # 定义与描述
    definition = Column(Text)  # 词根定义/含义
    business_value = Column(Text)  # 商业价值说明
    user_scenario = Column(Text)  # 用户使用场景

    # 层级关系（用于构建词根树）
    parent_seed_word = Column(String(100), index=True)  # 父词根
    level = Column(Integer, default=1)  # 层级：1=根节点, 2=二级节点...

    # 统计信息（从phrases表聚合）
    expansion_count = Column(Integer, default=0)  # 扩展的phrase数量
    total_volume = Column(BigInteger, default=0)  # 关联phrases的总搜索量
    avg_frequency = Column(Integer, default=0)  # 平均频次

    # 状态管理
    status = enum_column(
        "status",
        ["active", "paused", "archived"],
        enum_name="seed_status_enum",
        default="active",
        index=True
    )
    priority = enum_column(
        "priority",
        ["high", "medium", "low"],
        enum_name="seed_priority_enum",
        default="medium",
        index=True
    )

    # 需求关联
    related_demand_ids = Column(Text)  # JSON格式：关联的demand_id列表
    primary_demand_id = Column(Integer, index=True)  # 主要关联的需求ID

    # 标签系统
    tags = Column(Text)  # JSON格式：自定义标签数组

    # 来源追踪
    source = Column(String(100))  # 词根来源：initial_import, user_created, ai_suggested
    first_seen_round = Column(Integer)

    # 人工审核
    verified = Column(Boolean, default=False, index=True)  # 是否已审核
    confidence = enum_column(
        "confidence",
        ["high", "medium", "low"],
        enum_name="seed_confidence_enum",
        default="medium"
    )  # 分类置信度

    # 元数据
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    notes = Column(Text)  # 备注

    def __repr__(self):
        return f"<SeedWord(id={self.seed_id}, word='{self.seed_word}', primary_type='{self.primary_token_type}', expansions={self.expansion_count})>"


# ==================== 7. ClusterMeta 聚类元数据 ====================
class ClusterMeta(Base):
    """聚类元数据 - 存储大组和小组的统计信息"""

    __tablename__ = "cluster_meta"

    # 主键（使用复合主键：cluster_id + cluster_level）
    cluster_id = Column(Integer, primary_key=True)
    cluster_level = enum_column(
        "cluster_level",
        ["A", "B"],
        enum_name="cluster_level_enum",
        primary_key=True
    )

    # 父聚类（仅对小组B有效）
    parent_cluster_id = Column(Integer)

    # 统计信息
    size = Column(Integer)  # 聚类包含的短语数量
    total_frequency = Column(BigInteger)  # 总频次

    # 代表信息
    example_phrases = Column(Text)  # 代表短语，用分号分隔
    main_theme = Column(String(255))  # AI生成的主题标签

    # 选择状态（关键！）
    is_selected = Column(Boolean, default=False, index=True)
    selection_score = Column(Integer)  # 人工打分1-5

    # 自动质量评分（Phase 1新增）
    quality_score = Column(Integer, index=True)  # 总分 0-100
    size_score = Column(Integer)  # 大小得分 0-100
    diversity_score = Column(Integer)  # 多样性得分 0-100
    consistency_score = Column(Integer)  # 一致性得分 0-100
    quality_level = enum_column(
        "quality_level",
        ["excellent", "good", "fair", "poor"],
        enum_name="quality_level_enum",
        index=True
    )
    llm_summary = Column(Text)  # LLM生成的簇主题摘要
    llm_value_assessment = Column(Text)  # LLM的价值评估

    # DeepSeek语义标注（Phase 2C新增）
    llm_label = Column(String(100))  # 简短语义标签
    primary_demand_type = enum_column(
        "primary_demand_type",
        ["tool", "content", "service", "education", "other"],
        enum_name="primary_demand_type_enum",
        index=True
    )
    secondary_demand_types = Column(Text)  # JSON格式的次要需求类型列表
    labeling_confidence = Column(Integer)  # 标注置信度 0-100
    labeling_timestamp = Column(TIMESTAMP)  # 标注时间

    # 意图分类（Phase 3新增）
    dominant_intent = Column(String(50), index=True)  # 主导意图
    dominant_intent_confidence = Column(Integer)  # 主导意图置信度 0-100
    intent_distribution = Column(Text)  # JSON格式的意图分布
    is_intent_balanced = Column(Boolean, default=False)  # 意图是否均衡

    # 元数据
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_level_selected", "cluster_level", "is_selected"),
    )

    def __repr__(self):
        return (
            f"<ClusterMeta(id={self.cluster_id}, level='{self.cluster_level}', "
            f"size={self.size}, selected={self.is_selected})>"
        )


# ==================== 8. RedditSubreddit Reddit板块数据 ====================
class RedditSubreddit(Base):
    """Reddit板块数据表 - 存储Reddit板块信息及AI分析结果"""

    __tablename__ = "reddit_subreddits"

    # 主键
    subreddit_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False, index=True)

    # 板块信息
    description = Column(Text)
    subscribers = Column(BigInteger, default=0)

    # AI生成的标签（3个独立字段）
    tag1 = Column(String(100))
    tag2 = Column(String(100))
    tag3 = Column(String(100))

    # AI评估
    importance_score = Column(Integer)  # 1-5分
    ai_analysis_status = enum_column(
        "ai_analysis_status",
        ["pending", "processing", "completed", "failed", "skipped"],
        enum_name="ai_analysis_status_enum",
        nullable=False,
        default="pending",
        index=True
    )
    ai_analysis_timestamp = Column(TIMESTAMP)
    ai_model_used = Column(String(100))
    ai_confidence = Column(Integer)  # 0-100

    # 人工备注
    notes = Column(Text)

    # 导入批次
    import_batch_id = Column(String(50), index=True)

    # 元数据
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # 约束
    __table_args__ = (
        CheckConstraint(
            "importance_score IS NULL OR (importance_score >= 1 AND importance_score <= 5)",
            name="chk_importance_score"
        ),
        CheckConstraint(
            "ai_confidence IS NULL OR (ai_confidence >= 0 AND ai_confidence <= 100)",
            name="chk_ai_confidence"
        ),
        CheckConstraint("subscribers >= 0", name="chk_subscribers"),
        Index("idx_status_score", "ai_analysis_status", "importance_score"),
        Index("idx_batch_status", "import_batch_id", "ai_analysis_status"),
    )

    def __repr__(self):
        return f"<RedditSubreddit(id={self.subreddit_id}, name='{self.name}', status='{self.ai_analysis_status}')>"


# ==================== 9. AIPromptConfig AI提示词配置 ====================
class AIPromptConfig(Base):
    """AI提示词配置表 - 存储不同场景的AI提示词模板"""

    __tablename__ = "ai_prompt_configs"

    # 主键
    config_id = Column(Integer, primary_key=True, autoincrement=True)
    config_name = Column(String(100), unique=True, nullable=False)

    # 配置类型
    config_type = Column(String(50), nullable=False, default="reddit_analysis", index=True)

    # 提示词内容
    prompt_template = Column(Text, nullable=False)
    system_message = Column(Text)

    # LLM参数
    temperature = Column(DECIMAL(3, 2), default=Decimal("0.7"))
    max_tokens = Column(Integer, default=500)

    # 状态管理
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    is_default = Column(Boolean, nullable=False, default=False, index=True)

    # 描述
    description = Column(Text)
    created_by = Column(String(100), default="system")

    # 元数据
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # 约束
    __table_args__ = (
        CheckConstraint(
            "temperature >= 0 AND temperature <= 2",
            name="chk_temperature"
        ),
        CheckConstraint(
            "max_tokens > 0 AND max_tokens <= 10000",
            name="chk_max_tokens"
        ),
        Index("idx_type_active", "config_type", "is_active"),
        Index("idx_type_default", "config_type", "is_default"),
    )

    def __repr__(self):
        return f"<AIPromptConfig(id={self.config_id}, name='{self.config_name}', type='{self.config_type}')>"


# ==================== 8. Product 商品主表 (Phase 7) ====================
class Product(Base):
    """
    [REQ-2.7] 商品主表 - 存储从电商平台导入的商品数据
    支持Etsy、Gumroad等平台，包含AI生成的标签和需求分析
    """

    __tablename__ = "products"

    # 主键
    product_id = Column(BigInteger, primary_key=True, autoincrement=True)

    # 核心字段
    product_name = Column(String(500), nullable=False, index=True)
    description = Column(Text)
    price = Column(DECIMAL(10, 2))
    sales = Column(Integer, default=0)
    rating = Column(DECIMAL(3, 2))
    review_count = Column(Integer, default=0, index=True)
    url = Column(String(1000), unique=True)  # 移除index，使用__table_args__定义前缀索引
    shop_name = Column(String(200), index=True)

    # 平台来源
    platform = enum_column(
        "platform",
        ["etsy", "gumroad"],
        enum_name="platform_enum",
        nullable=False,
        index=True
    )

    # 元数据
    source_file = Column(String(255))

    # AI生成字段
    tags = Column(Text)  # JSON数组，3个中文标签
    demand_analysis = Column(Text)  # AI判断的需求描述

    # AI分析状态
    ai_analysis_status = enum_column(
        "ai_analysis_status",
        ["pending", "processing", "completed", "failed"],
        enum_name="ai_analysis_status_enum",
        default="pending",
        index=True
    )

    # 动态字段（JSON格式）
    custom_fields = Column(Text)  # JSON格式存储用户自定义字段

    # 时间戳
    imported_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # 约束和索引
    __table_args__ = (
        Index('idx_url_prefix', 'url', mysql_length=255),  # URL前缀索引
    )

    def __repr__(self):
        return f"<Product(id={self.product_id}, name='{self.product_name[:30]}...', platform='{self.platform}')>"


# ==================== 9. ProductFieldDefinition 字段定义表 (Phase 7) ====================
class ProductFieldDefinition(Base):
    """
    [REQ-2.7] 字段定义表 - 存储商品表的动态字段元数据
    支持类似飞书多维表格的动态字段管理
    """

    __tablename__ = "product_field_definitions"

    # 主键
    field_id = Column(Integer, primary_key=True, autoincrement=True)

    # 字段信息
    field_name = Column(String(100), nullable=False)  # 显示名称
    field_key = Column(String(100), unique=True, nullable=False, index=True)  # JSON键名

    # 字段类型
    field_type = enum_column(
        "field_type",
        ["text", "number", "date", "url", "tags", "select", "multi_select", "textarea"],
        enum_name="field_type_enum",
        nullable=False
    )

    # 字段配置
    is_required = Column(Boolean, default=False)
    default_value = Column(String(500))
    field_options = Column(Text)  # JSON数组，用于select/multi_select类型
    field_order = Column(Integer, default=0, index=True)
    field_description = Column(String(500))
    is_system_field = Column(Boolean, default=False)  # 系统字段不可删除

    # 时间戳
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<ProductFieldDefinition(id={self.field_id}, key='{self.field_key}', type='{self.field_type}')>"


# ==================== 10. ProductImportLog 导入日志表 (Phase 7) ====================
class ProductImportLog(Base):
    """
    [REQ-2.7] 导入日志表 - 记录商品数据导入的历史和统计信息
    """

    __tablename__ = "product_import_logs"

    # 主键
    log_id = Column(Integer, primary_key=True, autoincrement=True)

    # 导入信息
    source_file = Column(String(255), nullable=False)
    platform = enum_column(
        "platform",
        ["etsy", "gumroad"],
        enum_name="import_platform_enum",
        nullable=False,
        index=True
    )

    # 统计信息
    total_rows = Column(Integer, nullable=False)
    imported_rows = Column(Integer, nullable=False)
    skipped_rows = Column(Integer, default=0)
    duplicate_rows = Column(Integer, default=0)

    # 字段映射配置（JSON格式）
    field_mapping = Column(Text)  # 例如：{"col_0": "product_name", "col_1": "description"}

    # 导入状态
    import_status = enum_column(
        "import_status",
        ["in_progress", "completed", "failed"],
        enum_name="import_status_enum",
        default="in_progress",
        index=True
    )

    # 错误信息
    error_message = Column(Text)

    # 时间戳
    imported_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    duration_seconds = Column(Integer)  # 导入耗时

    def __repr__(self):
        return f"<ProductImportLog(id={self.log_id}, file='{self.source_file}', status='{self.import_status}')>"


# ==================== 数据库引擎和会话 ====================
def get_engine():
    """获取数据库引擎（强制使用UTF-8编码）"""
    # 根据数据库类型添加编码参数
    connect_args = {}

    if IS_SQLITE:
        # SQLite默认使用UTF-8，但显式设置确保一致性
        connect_args = {"check_same_thread": False}
    else:
        # MySQL/MariaDB强制使用UTF-8编码
        connect_args = {"charset": "utf8mb4"}

    engine = create_engine(
        DATABASE_URL,
        echo=False,  # 设为True可以看到SQL语句
        pool_pre_ping=True,  # 连接池健康检查
        pool_recycle=3600,   # 连接回收时间（秒）
        connect_args=connect_args  # 添加编码参数
    )
    return engine


def get_session():
    """获取数据库会话"""
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def create_all_tables():
    """创建所有表（仅首次运行）"""
    engine = get_engine()
    Base.metadata.create_all(engine)
    print("SUCCESS: All tables created")


def drop_all_tables():
    """删除所有表（危险操作！）"""
    engine = get_engine()
    Base.metadata.drop_all(engine)
    print("WARNING: All tables dropped")


# ==================== 便捷导入 ====================
__all__ = [
    "Phrase",
    "Demand",
    "Token",
    "WordSegment",
    "SegmentationBatch",
    "SeedWord",
    "ClusterMeta",
    "RedditSubreddit",
    "AIPromptConfig",
    "Product",
    "ProductFieldDefinition",
    "ProductImportLog",
    "get_engine",
    "get_session",
    "create_all_tables",
    "drop_all_tables",
]
