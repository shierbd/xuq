"""
商品管理模块 - 簇关键词数据模型
用于存储每个商品簇的关键词/词根结果
"""
from sqlalchemy import Column, Integer, String, Float, DateTime
from backend.database import Base
from datetime import datetime


class ProductClusterKeyword(Base):
    """
    商品簇关键词表
    """
    __tablename__ = "product_cluster_keywords"

    keyword_id = Column(Integer, primary_key=True, autoincrement=True, comment="关键词ID")
    cluster_id = Column(Integer, nullable=False, index=True, comment="簇ID")
    keyword = Column(String(100), nullable=False, index=True, comment="关键词/词根")
    count = Column(Integer, nullable=True, comment="出现次数")
    score = Column(Float, nullable=True, comment="权重/得分")
    method = Column(String(50), nullable=False, default="tf", comment="提取方法(tf/tfidf)")
    created_time = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")

    def __repr__(self):
        return f"<ProductClusterKeyword(id={self.keyword_id}, cluster_id={self.cluster_id}, keyword='{self.keyword}')>"
