"""
需求溯源系统 - 数据库模型扩展

新增4个表:
1. DemandPhraseMapping - 需求与短语的多对多关联
2. DemandProductMapping - 需求与商品的多对多关联
3. DemandTokenMapping - 需求与Token的多对多关联
4. DemandProvenance - 需求溯源审计表

同时扩展Demand表,添加溯源字段
"""
from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Text,
    Boolean,
    TIMESTAMP,
    DECIMAL,
    ForeignKey,
    Index,
)
from storage.models import Base, enum_column


# ==================== 扩展Demand表的溯源字段 ====================
# 注意: 这些字段需要通过ALTER TABLE添加到现有的demands表中
#
# ALTER TABLE demands ADD COLUMN source_phase VARCHAR(20);
# ALTER TABLE demands ADD COLUMN source_method VARCHAR(50);
# ALTER TABLE demands ADD COLUMN source_data_ids TEXT;
# ALTER TABLE demands ADD COLUMN confidence_score DECIMAL(3,2) DEFAULT 0.50;
# ALTER TABLE demands ADD COLUMN confidence_history TEXT;
# ALTER TABLE demands ADD COLUMN discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
# ALTER TABLE demands ADD COLUMN last_validated_at TIMESTAMP;
# ALTER TABLE demands ADD COLUMN validation_count INT DEFAULT 0;
# ALTER TABLE demands ADD COLUMN is_validated BOOLEAN DEFAULT FALSE;
# ALTER TABLE demands ADD COLUMN validated_by VARCHAR(100);
# ALTER TABLE demands ADD COLUMN validation_notes TEXT;
#
# CREATE INDEX idx_demand_source_phase ON demands(source_phase);
# CREATE INDEX idx_demand_source_method ON demands(source_method);
# CREATE INDEX idx_demand_is_validated ON demands(is_validated);


# ==================== 1. DemandPhraseMapping 需求-短语关联表 ====================
class DemandPhraseMapping(Base):
    """需求与短语的多对多关联表

    记录需求与短语之间的关联关系,包括:
    - 关联强度(relevance_score)
    - 来源追踪(mapping_source, created_by_phase, created_by_method)
    - 验证状态(is_validated, validated_at, validated_by)
    """

    __tablename__ = "demand_phrase_mappings"

    # 主键
    mapping_id = Column(Integer, primary_key=True, autoincrement=True)

    # 关联关系
    demand_id = Column(
        Integer,
        ForeignKey('demands.demand_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    phrase_id = Column(
        BigInteger,
        ForeignKey('phrases.phrase_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # 关联强度
    relevance_score = Column(DECIMAL(3, 2))  # 0.00-1.00

    # 溯源信息
    mapping_source = Column(String(50), index=True)  # clustering, manual, ai_inference
    created_by_phase = Column(String(20))  # phase1-7, manual
    created_by_method = Column(String(50))  # 具体方法名

    # 验证状态
    is_validated = Column(Boolean, default=False, index=True)
    validated_at = Column(TIMESTAMP)
    validated_by = Column(String(100))  # user, ai, system

    # 元数据
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    notes = Column(Text)

    # 复合索引
    __table_args__ = (
        Index('idx_demand_phrase', 'demand_id', 'phrase_id'),
        Index('idx_source_validated', 'mapping_source', 'is_validated'),
    )

    def __repr__(self):
        return (
            f"<DemandPhraseMapping(id={self.mapping_id}, "
            f"demand={self.demand_id}, phrase={self.phrase_id}, "
            f"score={self.relevance_score})>"
        )


# ==================== 2. DemandProductMapping 需求-商品关联表 ====================
class DemandProductMapping(Base):
    """需求与商品的多对多关联表

    记录需求与商品之间的关联关系,包括:
    - 适配度评分(fit_score, fit_level)
    - 来源追踪(mapping_source, created_by_phase, created_by_method)
    - 验证状态(is_validated, validated_at, validated_by)
    """

    __tablename__ = "demand_product_mappings"

    # 主键
    mapping_id = Column(Integer, primary_key=True, autoincrement=True)

    # 关联关系
    demand_id = Column(
        Integer,
        ForeignKey('demands.demand_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    product_id = Column(
        BigInteger,
        ForeignKey('products.product_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # 适配度评分
    fit_score = Column(DECIMAL(3, 2))  # 0.00-1.00
    fit_level = enum_column(
        "fit_level",
        ["high", "medium", "low"],
        enum_name="fit_level_enum",
        index=True
    )

    # 溯源信息
    mapping_source = Column(String(50), index=True)  # product_analysis, manual, ai_inference
    created_by_phase = Column(String(20))  # phase7, manual
    created_by_method = Column(String(50))  # 具体方法名

    # 验证状态
    is_validated = Column(Boolean, default=False, index=True)
    validated_at = Column(TIMESTAMP)
    validated_by = Column(String(100))  # user, ai, system
    validation_notes = Column(Text)

    # 元数据
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)

    # 复合索引
    __table_args__ = (
        Index('idx_demand_product', 'demand_id', 'product_id'),
        Index('idx_fit_validated', 'fit_level', 'is_validated'),
    )

    def __repr__(self):
        return (
            f"<DemandProductMapping(id={self.mapping_id}, "
            f"demand={self.demand_id}, product={self.product_id}, "
            f"fit={self.fit_level})>"
        )


# ==================== 3. DemandTokenMapping 需求-词根关联表 ====================
class DemandTokenMapping(Base):
    """需求与Token的多对多关联表

    记录需求与Token(词根)之间的关联关系,包括:
    - 词根角色(token_role: core/supporting/context)
    - 重要性评分(importance_score)
    - 来源追踪(mapping_source, created_by_phase, created_by_method)
    - 验证状态(is_validated, validated_at)
    """

    __tablename__ = "demand_token_mappings"

    # 主键
    mapping_id = Column(Integer, primary_key=True, autoincrement=True)

    # 关联关系
    demand_id = Column(
        Integer,
        ForeignKey('demands.demand_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    token_id = Column(
        Integer,
        ForeignKey('tokens.token_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # 关联类型
    token_role = enum_column(
        "token_role",
        ["core", "supporting", "context"],
        enum_name="token_role_enum",
        index=True
    )  # core=核心词, supporting=支撑词, context=上下文词

    # 重要性评分
    importance_score = Column(DECIMAL(3, 2))  # 0.00-1.00

    # 溯源信息
    mapping_source = Column(String(50), index=True)  # token_extraction, manual, ai_inference
    created_by_phase = Column(String(20))  # phase5, manual
    created_by_method = Column(String(50))  # 具体方法名

    # 验证状态
    is_validated = Column(Boolean, default=False, index=True)
    validated_at = Column(TIMESTAMP)

    # 元数据
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)

    # 复合索引
    __table_args__ = (
        Index('idx_demand_token', 'demand_id', 'token_id'),
        Index('idx_role_validated', 'token_role', 'is_validated'),
    )

    def __repr__(self):
        return (
            f"<DemandTokenMapping(id={self.mapping_id}, "
            f"demand={self.demand_id}, token={self.token_id}, "
            f"role={self.token_role})>"
        )


# ==================== 4. DemandProvenance 需求溯源审计表 ====================
class DemandProvenance(Base):
    """需求溯源审计表 - 记录需求的所有变更历史

    记录需求生命周期中的所有关键事件:
    - 创建(created)
    - 更新(updated)
    - 验证(validated)
    - 合并(merged)
    - 拆分(split)
    - 关联短语/商品/词根(linked_phrase/linked_product/linked_token)
    - 置信度变化(confidence_changed)
    - 状态变化(status_changed)

    每个事件记录:
    - 事件类型和描述
    - 变更前后的值
    - 触发者信息(phase, method, user)
    - 关联数据信息
    - 时间戳
    """

    __tablename__ = "demand_provenance"

    # 主键
    provenance_id = Column(Integer, primary_key=True, autoincrement=True)

    # 关联需求
    demand_id = Column(
        Integer,
        ForeignKey('demands.demand_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # 事件类型
    event_type = enum_column(
        "event_type",
        [
            "created",            # 创建
            "updated",            # 更新
            "validated",          # 验证
            "merged",             # 合并
            "split",              # 拆分
            "linked_phrase",      # 关联短语
            "linked_product",     # 关联商品
            "linked_token",       # 关联词根
            "confidence_changed", # 置信度变化
            "status_changed"      # 状态变化
        ],
        enum_name="event_type_enum",
        nullable=False,
        index=True
    )

    # 事件详情
    event_description = Column(Text)
    old_value = Column(Text)  # JSON格式: 变更前的值
    new_value = Column(Text)  # JSON格式: 变更后的值

    # 溯源信息
    triggered_by_phase = Column(String(20))  # phase1-7, manual
    triggered_by_method = Column(String(50))  # 具体方法名
    triggered_by_user = Column(String(100))  # user, ai, system

    # 关联数据
    related_data_type = Column(String(50))  # phrase, product, token, cluster
    related_data_id = Column(Integer)

    # 元数据
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow, index=True)

    # 索引
    __table_args__ = (
        Index('idx_demand_event', 'demand_id', 'event_type'),
        Index('idx_demand_time', 'demand_id', 'created_at'),
        Index('idx_event_time', 'event_type', 'created_at'),
    )

    def __repr__(self):
        return (
            f"<DemandProvenance(id={self.provenance_id}, "
            f"demand={self.demand_id}, event='{self.event_type}', "
            f"time={self.created_at})>"
        )


# ==================== 便捷导入 ====================
__all__ = [
    "DemandPhraseMapping",
    "DemandProductMapping",
    "DemandTokenMapping",
    "DemandProvenance",
]
