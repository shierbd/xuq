"""
词根聚类系统 - 关键词数据模型
用于存储和管理关键词短语数据
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from backend.database import Base
from datetime import datetime


class Keyword(Base):
    """
    关键词数据模型
    对应词根聚类系统的短语数据
    """
    __tablename__ = "keywords"

    # 主键
    keyword_id = Column(Integer, primary_key=True, autoincrement=True, comment="关键词ID")

    # 基础字段
    keyword = Column(String(500), nullable=False, index=True, comment="关键词短语")
    seed_word = Column(String(100), nullable=False, index=True, comment="来源种子词")
    seed_group = Column(String(100), comment="种子词分组")
    source = Column(String(50), comment="数据来源（semrush/reddit/related_search）")

    # SEMrush 数据字段
    intent = Column(String(100), comment="搜索意图")
    volume = Column(Integer, comment="搜索量")
    trend = Column(Text, comment="趋势数据")
    keyword_difficulty = Column(Integer, comment="关键词难度")
    cpc_usd = Column(Float, comment="CPC（美元）")
    competitive_density = Column(Float, comment="竞争密度")
    serp_features = Column(Text, comment="SERP特征")
    number_of_results = Column(Float, comment="搜索结果数")
    source_file = Column(String(200), comment="来源文件")

    # 聚类相关字段
    cluster_id_a = Column(Integer, index=True, comment="阶段A聚类ID（-1表示噪音）")
    cluster_id_b = Column(Integer, index=True, comment="阶段B聚类ID（-1表示噪音）")
    cluster_size = Column(Integer, comment="所属簇的大小")
    is_noise = Column(Boolean, default=False, comment="是否为噪音点")

    # 文本特征
    word_count = Column(Integer, comment="单词数量")
    phrase_length = Column(Integer, comment="短语长度（字符数）")

    # 标记字段
    is_selected = Column(Boolean, default=False, comment="是否被选为方向")
    is_low_priority = Column(Boolean, default=False, comment="是否标记为低优先级")
    notes = Column(Text, comment="备注")

    # 时间戳
    import_time = Column(DateTime, nullable=False, default=datetime.now, comment="导入时间")
    is_deleted = Column(Boolean, nullable=False, default=False, comment="是否已删除（软删除）")

    def __repr__(self):
        return f"<Keyword(id={self.keyword_id}, keyword='{self.keyword}', seed_word='{self.seed_word}')>"


class ClusterSummary(Base):
    """
    簇汇总数据模型
    存储聚类结果的汇总信息
    """
    __tablename__ = "cluster_summaries"

    # 主键
    summary_id = Column(Integer, primary_key=True, autoincrement=True, comment="汇总ID")

    # 簇信息
    cluster_id = Column(Integer, nullable=False, index=True, comment="簇ID")
    stage = Column(String(10), nullable=False, comment="阶段（A/B）")
    cluster_size = Column(Integer, nullable=False, comment="簇大小")

    # 种子词信息
    seed_words_in_cluster = Column(Text, comment="簇内种子词列表（逗号分隔）")

    # 代表性短语
    top_keywords = Column(Text, comment="代表性短语（前5个，逗号分隔）")
    example_phrases = Column(Text, comment="示例短语")

    # AI生成字段（可选）
    cluster_label = Column(String(200), comment="簇标签（AI生成）")
    cluster_explanation = Column(Text, comment="簇解释（AI生成）")

    # 统计信息
    avg_volume = Column(Float, comment="平均搜索量")
    total_volume = Column(Float, comment="总搜索量")

    # 标记字段
    is_direction = Column(Boolean, default=False, comment="是否被选为方向")
    priority = Column(String(20), comment="优先级（high/medium/low）")

    # 时间戳
    created_time = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_time = Column(DateTime, onupdate=datetime.now, comment="更新时间")

    def __repr__(self):
        return f"<ClusterSummary(id={self.summary_id}, cluster_id={self.cluster_id}, stage='{self.stage}', size={self.cluster_size})>"
