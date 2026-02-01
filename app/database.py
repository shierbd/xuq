"""
数据库配置和模型
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# 数据库路径
DATABASE_URL = "sqlite:///data/products.db"

# 创建引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# 创建会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 基础模型
Base = declarative_base()

# 商品模型（映射到现有数据库）
class Product(Base):
    __tablename__ = "products"

    product_id = Column("product_id", Integer, primary_key=True, index=True)
    product_name = Column("product_name", String(500), nullable=False)
    rating = Column("rating", Float)
    review_count = Column("review_count", Integer)
    shop_name = Column("shop_name", String(200))
    price = Column("price", Float)
    cluster_id = Column("cluster_id", Integer)
    delivery_type = Column("delivery_type", String(100))
    delivery_format = Column("delivery_format", String(100))
    delivery_platform = Column("delivery_platform", String(100))
    import_time = Column("import_time", DateTime, nullable=False, default=datetime.utcnow)
    is_deleted = Column("is_deleted", Boolean, nullable=False, default=False)
    cluster_name = Column("cluster_name", String(200))
    user_need = Column("user_need", Text)
    cluster_name_cn = Column("cluster_name_cn", String(200))
    cluster_type = Column("cluster_type", String(50))

    # 为了兼容模板，添加属性映射
    @property
    def id(self):
        return self.product_id

    @property
    def name(self):
        return self.product_name

    @property
    def category(self):
        return self.cluster_name_cn or self.cluster_name or "未分类"

    @property
    def status(self):
        return "inactive" if self.is_deleted else "active"

    @property
    def description(self):
        return self.user_need or ""

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.product_id,
            "name": self.product_name,
            "category": self.category,
            "price": self.price,
            "status": self.status,
            "description": self.description,
            "rating": self.rating,
            "review_count": self.review_count,
            "shop_name": self.shop_name,
            "cluster_id": self.cluster_id,
            "import_time": self.import_time.isoformat() if self.import_time else None,
        }

# 聚类摘要模型（映射到现有数据库）
class ClusterSummary(Base):
    __tablename__ = "cluster_summaries"

    summary_id = Column("summary_id", Integer, primary_key=True, index=True)
    cluster_id = Column("cluster_id", Integer, nullable=False, index=True)
    stage = Column("stage", String(10), nullable=False)
    cluster_size = Column("cluster_size", Integer, nullable=False)
    seed_words_in_cluster = Column("seed_words_in_cluster", Text)
    top_keywords = Column("top_keywords", Text)
    example_phrases = Column("example_phrases", Text)
    cluster_label = Column("cluster_label", String(200))
    cluster_explanation = Column("cluster_explanation", Text)
    avg_volume = Column("avg_volume", Float)
    total_volume = Column("total_volume", Float)
    is_direction = Column("is_direction", Boolean)
    priority = Column("priority", String(20))
    created_time = Column("created_time", DateTime, nullable=False, default=datetime.utcnow)
    updated_time = Column("updated_time", DateTime)

    # 属性映射
    @property
    def id(self):
        return self.summary_id

    @property
    def label(self):
        return self.cluster_label or f"Cluster {self.cluster_id}"

    @property
    def explanation(self):
        return self.cluster_explanation or ""

    @property
    def keywords_list(self):
        """将关键词字符串转换为列表"""
        if self.top_keywords:
            return [kw.strip() for kw in self.top_keywords.split(',')]
        return []

    @property
    def examples_list(self):
        """将示例短语字符串转换为列表"""
        if self.example_phrases:
            return [ex.strip() for ex in self.example_phrases.split(',')]
        return []

    @property
    def seed_words_list(self):
        """将种子词字符串转换为列表"""
        if self.seed_words_in_cluster:
            return [sw.strip() for sw in self.seed_words_in_cluster.split(',')]
        return []

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.summary_id,
            "cluster_id": self.cluster_id,
            "stage": self.stage,
            "cluster_size": self.cluster_size,
            "label": self.label,
            "explanation": self.explanation,
            "keywords": self.keywords_list,
            "examples": self.examples_list,
            "seed_words": self.seed_words_list,
            "avg_volume": self.avg_volume,
            "total_volume": self.total_volume,
            "is_direction": self.is_direction,
            "priority": self.priority,
            "created_time": self.created_time.isoformat() if self.created_time else None,
            "updated_time": self.updated_time.isoformat() if self.updated_time else None,
        }

# 依赖注入：获取数据库会话
def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 初始化数据库（不需要创建表，使用现有表）
def init_db():
    """初始化数据库（检查连接）"""
    try:
        # 测试连接
        db = SessionLocal()
        count = db.query(Product).count()
        print(f"[数据库] 连接成功，当前有 {count} 条商品数据")
        db.close()
    except Exception as e:
        print(f"[数据库] 连接失败: {e}")
