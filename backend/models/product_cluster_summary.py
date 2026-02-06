"""
Product clustering summary model.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from backend.database import Base


class ProductClusterSummary(Base):
    """Summary for product clusters."""
    __tablename__ = "product_cluster_summaries"

    summary_id = Column(Integer, primary_key=True, autoincrement=True, comment="Summary ID")
    cluster_id = Column(Integer, nullable=False, index=True, comment="Cluster ID")
    cluster_name = Column(String(200), comment="Cluster name")
    cluster_name_cn = Column(String(200), comment="Cluster name (CN)")
    cluster_size = Column(Integer, nullable=False, comment="Cluster size")
    avg_rating = Column(Float, comment="Average rating")
    avg_price = Column(Float, comment="Average price")
    total_reviews = Column(Integer, comment="Total review count")
    example_products = Column(Text, comment="Example products")
    top_keywords = Column(Text, comment="Top keywords")
    created_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_time = Column(DateTime, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<ProductClusterSummary(cluster_id={self.cluster_id}, size={self.cluster_size})>"
