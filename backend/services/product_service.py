"""
[REQ-002] 数据管理功能 - 商品管理服务
提供商品查询、编辑、删除等业务逻辑
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from backend.models.product import Product
from backend.schemas.product_schema import ProductQueryParams, ProductUpdate
from typing import List, Tuple

class ProductService:
    """[REQ-002] 商品管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_products(self, params: ProductQueryParams) -> Tuple[List[Product], int]:
        """
        [REQ-002] 获取商品列表（分页、搜索、筛选、排序）
        
        Args:
            params: 查询参数
            
        Returns:
            Tuple[List[Product], int]: (商品列表, 总数量)
        """
        # 基础查询
        query = self.db.query(Product).filter(Product.is_deleted == False)
        
        # [REQ-002] 搜索功能（商品名称）
        if params.search:
            search_pattern = f"%{params.search}%"
            query = query.filter(Product.product_name.like(search_pattern))
        
        # [REQ-002] 筛选功能
        if params.shop_name:
            query = query.filter(Product.shop_name == params.shop_name)
        
        if params.min_rating is not None:
            query = query.filter(Product.rating >= params.min_rating)
        
        if params.max_rating is not None:
            query = query.filter(Product.rating <= params.max_rating)
        
        if params.min_price is not None:
            query = query.filter(Product.price >= params.min_price)
        
        if params.max_price is not None:
            query = query.filter(Product.price <= params.max_price)
        
        # 获取总数
        total = query.count()
        
        # [REQ-002] 排序功能
        sort_column = getattr(Product, params.sort_by, Product.import_time)
        if params.sort_order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())
        
        # [REQ-002] 分页功能
        offset = (params.page - 1) * params.page_size
        query = query.offset(offset).limit(params.page_size)
        
        products = query.all()
        
        return products, total
    
    def get_product_by_id(self, product_id: int) -> Product:
        """
        [REQ-002] 根据 ID 获取商品
        
        Args:
            product_id: 商品 ID
            
        Returns:
            Product: 商品对象
        """
        return self.db.query(Product).filter(
            Product.product_id == product_id,
            Product.is_deleted == False
        ).first()
    
    def update_product(self, product_id: int, update_data: ProductUpdate) -> Product:
        """
        [REQ-002] 更新商品信息
        
        Args:
            product_id: 商品 ID
            update_data: 更新数据
            
        Returns:
            Product: 更新后的商品对象
        """
        product = self.get_product_by_id(product_id)
        if not product:
            return None
        
        # 更新字段
        update_dict = update_data.dict(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(product, key, value)
        
        self.db.commit()
        self.db.refresh(product)
        
        return product
    
    def delete_product(self, product_id: int) -> bool:
        """
        [REQ-002] 删除商品（软删除）
        
        Args:
            product_id: 商品 ID
            
        Returns:
            bool: 是否删除成功
        """
        product = self.get_product_by_id(product_id)
        if not product:
            return False
        
        # 软删除
        product.is_deleted = True
        self.db.commit()
        
        return True
    
    def batch_delete_products(self, product_ids: List[int]) -> int:
        """
        [REQ-002] 批量删除商品（软删除）
        
        Args:
            product_ids: 商品 ID 列表
            
        Returns:
            int: 删除的数量
        """
        count = self.db.query(Product).filter(
            Product.product_id.in_(product_ids),
            Product.is_deleted == False
        ).update({"is_deleted": True}, synchronize_session=False)
        
        self.db.commit()
        
        return count
