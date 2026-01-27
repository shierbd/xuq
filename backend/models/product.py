"""
[REQ-001] 数据导入功能 - 数据库模型
商品数据模型定义
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Product(Base):
    """
    [REQ-001] 商品数据模型
    对应 Etsy 平台商品数据
    """
    __tablename__ = "products"

    # 主键
    product_id = Column(Integer, primary_key=True, autoincrement=True, comment="商品ID")
    
    # [REQ-001] 必填字段
    product_name = Column(String(500), nullable=False, index=True, comment="商品名称")
    
    # [REQ-001] 可选字段
    rating = Column(Float, nullable=True, comment="评分 (0-5)")
    review_count = Column(Integer, nullable=True, comment="评价数量（已转换为整数）")
    shop_name = Column(String(200), nullable=True, index=True, comment="店铺名称")
    price = Column(Float, nullable=True, comment="价格")
    
    # [REQ-003] 聚类相关字段
    cluster_id = Column(Integer, nullable=True, index=True, comment="簇ID（-1表示噪音点）")
    
    # [REQ-005] 交付产品识别字段
    delivery_type = Column(String(100), nullable=True, comment="交付类型")
    delivery_format = Column(String(100), nullable=True, comment="交付格式")
    delivery_platform = Column(String(100), nullable=True, comment="交付平台")
    
    # [REQ-001] 系统字段
    import_time = Column(DateTime, nullable=False, default=datetime.utcnow, comment="导入时间")
    is_deleted = Column(Boolean, nullable=False, default=False, comment="是否删除（软删除）")
    
    def __repr__(self):
        return f"<Product(id={self.product_id}, name={self.product_name[:30]}...)>"
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "rating": self.rating,
            "review_count": self.review_count,
            "shop_name": self.shop_name,
            "price": self.price,
            "cluster_id": self.cluster_id,
            "delivery_type": self.delivery_type,
            "delivery_format": self.delivery_format,
            "delivery_platform": self.delivery_platform,
            "import_time": self.import_time.isoformat() if self.import_time else None,
            "is_deleted": self.is_deleted
        }
