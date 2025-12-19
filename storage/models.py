"""
MVP版本数据库模型
使用SQLAlchemy ORM定义四张核心表：
1. Phrase - 短语总库
2. Demand - 需求卡片
3. Token - 需求框架词库
4. ClusterMeta - 聚类元数据
"""
from datetime import datetime
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
    Index,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config.settings import DATABASE_URL

Base = declarative_base()


# ==================== 1. Phrase 短语总库 ====================
class Phrase(Base):
    """短语总库 - 存储所有搜索关键词短语"""

    __tablename__ = "phrases"

    # 主键
    phrase_id = Column(BigInteger, primary_key=True, autoincrement=True)
    phrase = Column(String(255), unique=True, nullable=False, index=True)

    # 来源信息
    seed_word = Column(String(100))
    source_type = Column(
        SQLEnum("semrush", "dropdown", "related_search", name="source_type_enum"),
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
    processed_status = Column(
        SQLEnum("unseen", "reviewed", "assigned", "archived", name="processed_status_enum"),
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
    demand_type = Column(
        SQLEnum("tool", "content", "service", "education", "other", name="demand_type_enum"),
        index=True
    )

    # 关联信息
    source_cluster_A = Column(Integer, index=True)
    source_cluster_B = Column(Integer)
    related_phrases_count = Column(Integer, default=0)

    # 商业评估（简化）
    business_value = Column(
        SQLEnum("high", "medium", "low", "unknown", name="business_value_enum"),
        default="unknown",
        index=True
    )

    # 状态追踪
    status = Column(
        SQLEnum("idea", "validated", "in_progress", "archived", name="demand_status_enum"),
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
    token_type = Column(
        SQLEnum(
            "intent", "action", "object", "attribute", "condition", "other",
            name="token_type_enum"
        ),
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


# ==================== 4. ClusterMeta 聚类元数据 ====================
class ClusterMeta(Base):
    """聚类元数据 - 存储大组和小组的统计信息"""

    __tablename__ = "cluster_meta"

    # 主键（使用复合主键：cluster_id + cluster_level）
    cluster_id = Column(Integer, primary_key=True)
    cluster_level = Column(
        SQLEnum("A", "B", name="cluster_level_enum"),
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


# ==================== 数据库引擎和会话 ====================
def get_engine():
    """获取数据库引擎"""
    engine = create_engine(
        DATABASE_URL,
        echo=False,  # 设为True可以看到SQL语句
        pool_pre_ping=True,  # 连接池健康检查
        pool_recycle=3600,   # 连接回收时间（秒）
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
    print("✓ 所有数据表创建完成")


def drop_all_tables():
    """删除所有表（危险操作！）"""
    engine = get_engine()
    Base.metadata.drop_all(engine)
    print("✗ 所有数据表已删除")


# ==================== 便捷导入 ====================
__all__ = [
    "Phrase",
    "Demand",
    "Token",
    "ClusterMeta",
    "get_engine",
    "get_session",
    "create_all_tables",
    "drop_all_tables",
]
