"""
[REQ-2.7] Phase 7 商品筛选与AI标注系统 - 数据访问层

提供三个Repository类：
1. ProductRepository - 商品数据访问
2. ProductFieldDefinitionRepository - 字段定义数据访问
3. ProductImportLogRepository - 导入日志数据访问
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json
from sqlalchemy import or_, and_, func, desc, asc
from sqlalchemy.orm import Session
from storage.models import (
    get_session,
    Product,
    ProductFieldDefinition,
    ProductImportLog
)


# ==================== ProductRepository ====================
class ProductRepository:
    """[REQ-2.7] 商品数据访问层"""

    def __init__(self, session: Optional[Session] = None):
        """
        初始化Repository

        Args:
            session: SQLAlchemy会话对象（可选，默认创建新会话）
        """
        self.session = session or get_session()
        self._should_close = session is None

    def __enter__(self):
        """支持with语句"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出with语句时关闭session"""
        if self._should_close:
            self.session.close()

    # ==================== 基础CRUD ====================

    def create(self, data: Dict[str, Any]) -> int:
        """
        创建商品记录

        Args:
            data: 商品数据字典

        Returns:
            创建的商品ID
        """
        product = Product(**data)
        self.session.add(product)
        self.session.commit()
        return product.product_id

    def bulk_insert(self, products: List[Dict[str, Any]]) -> int:
        """
        [REQ-2.7] 批量插入商品（优化性能）

        Args:
            products: 商品数据列表

        Returns:
            成功插入的数量
        """
        if not products:
            return 0

        self.session.bulk_insert_mappings(Product, products)
        self.session.commit()
        return len(products)

    def get_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """
        按ID查询商品

        Args:
            product_id: 商品ID

        Returns:
            商品字典，不存在返回None
        """
        product = self.session.query(Product).filter_by(
            product_id=product_id
        ).first()

        if not product:
            return None

        return self._to_dict(product)

    def get_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        [REQ-2.7] 按URL查询商品（用于去重）

        Args:
            url: 商品链接

        Returns:
            商品字典，不存在返回None
        """
        product = self.session.query(Product).filter_by(url=url).first()

        if not product:
            return None

        return self._to_dict(product)

    def update(self, product_id: int, data: Dict[str, Any]) -> bool:
        """
        更新商品记录

        Args:
            product_id: 商品ID
            data: 更新数据字典

        Returns:
            是否更新成功
        """
        result = self.session.query(Product).filter_by(
            product_id=product_id
        ).update(data)
        self.session.commit()
        return result > 0

    def delete(self, product_id: int) -> bool:
        """
        删除商品记录

        Args:
            product_id: 商品ID

        Returns:
            是否删除成功
        """
        result = self.session.query(Product).filter_by(
            product_id=product_id
        ).delete()
        self.session.commit()
        return result > 0

    # ==================== 查询方法 ====================

    def get_all(
        self,
        platform: Optional[str] = None,
        ai_status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "imported_at",
        order_dir: str = "desc"
    ) -> List[Dict[str, Any]]:
        """
        [REQ-2.7] 获取商品列表（支持筛选和排序）

        Args:
            platform: 平台筛选（etsy/gumroad）
            ai_status: AI分析状态筛选
            limit: 返回数量限制
            offset: 偏移量
            order_by: 排序字段
            order_dir: 排序方向（asc/desc）

        Returns:
            商品列表
        """
        query = self.session.query(Product)

        # 筛选条件
        if platform:
            query = query.filter(Product.platform == platform)
        if ai_status:
            query = query.filter(Product.ai_analysis_status == ai_status)

        # 排序
        order_column = getattr(Product, order_by, Product.imported_at)
        if order_dir == "desc":
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(asc(order_column))

        # 分页
        products = query.limit(limit).offset(offset).all()

        return [self._to_dict(p) for p in products]

    def search(
        self,
        keyword: Optional[str] = None,
        platform: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_rating: Optional[float] = None,
        min_review_count: Optional[int] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        [REQ-2.7] 高级搜索（支持多条件组合）

        Args:
            keyword: 关键词（搜索商品名称和描述）
            platform: 平台筛选
            min_price: 最低价格
            max_price: 最高价格
            min_rating: 最低评分
            min_review_count: 最低评价数量
            tags: 标签筛选（包含任一标签）
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            (商品列表, 总数量)
        """
        query = self.session.query(Product)

        # 关键词搜索
        if keyword:
            keyword_filter = or_(
                Product.product_name.like(f"%{keyword}%"),
                Product.description.like(f"%{keyword}%")
            )
            query = query.filter(keyword_filter)

        # 平台筛选
        if platform:
            query = query.filter(Product.platform == platform)

        # 价格范围
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        if max_price is not None:
            query = query.filter(Product.price <= max_price)

        # 评分筛选
        if min_rating is not None:
            query = query.filter(Product.rating >= min_rating)

        # 评价数量筛选
        if min_review_count is not None:
            query = query.filter(Product.review_count >= min_review_count)

        # 标签筛选（JSON字段搜索）
        if tags:
            tag_filters = []
            for tag in tags:
                tag_filters.append(Product.tags.like(f'%"{tag}"%'))
            query = query.filter(or_(*tag_filters))

        # 获取总数
        total = query.count()

        # 分页
        products = query.limit(limit).offset(offset).all()

        return [self._to_dict(p) for p in products], total

    def get_pending_ai_analysis(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        [REQ-2.7] 获取待AI分析的商品

        Args:
            limit: 返回数量限制

        Returns:
            待分析商品列表
        """
        products = self.session.query(Product).filter(
            Product.ai_analysis_status == "pending"
        ).limit(limit).all()

        return [self._to_dict(p) for p in products]

    def update_ai_analysis(
        self,
        product_id: int,
        tags: List[str],
        demand_analysis: str,
        status: str = "completed"
    ) -> bool:
        """
        [REQ-2.7] 更新AI分析结果

        Args:
            product_id: 商品ID
            tags: AI生成的标签列表
            demand_analysis: AI生成的需求分析
            status: AI分析状态

        Returns:
            是否更新成功
        """
        tags_json = json.dumps(tags, ensure_ascii=False)

        result = self.session.query(Product).filter_by(
            product_id=product_id
        ).update({
            "tags": tags_json,
            "demand_analysis": demand_analysis,
            "ai_analysis_status": status,
            "updated_at": datetime.utcnow()
        })
        self.session.commit()
        return result > 0

    def get_statistics(self) -> Dict[str, Any]:
        """
        [REQ-2.7] 获取商品统计信息

        Returns:
            统计信息字典
        """
        total = self.session.query(func.count(Product.product_id)).scalar()

        by_platform = self.session.query(
            Product.platform,
            func.count(Product.product_id)
        ).group_by(Product.platform).all()

        by_ai_status = self.session.query(
            Product.ai_analysis_status,
            func.count(Product.product_id)
        ).group_by(Product.ai_analysis_status).all()

        return {
            "total": total,
            "by_platform": dict(by_platform),
            "by_ai_status": dict(by_ai_status)
        }

    # ==================== 辅助方法 ====================

    def _to_dict(self, product: Product) -> Dict[str, Any]:
        """
        将Product对象转换为字典

        Args:
            product: Product对象

        Returns:
            字典表示
        """
        # 解析JSON字段
        tags = None
        if product.tags:
            try:
                tags = json.loads(product.tags)
            except:
                tags = []

        custom_fields = None
        if product.custom_fields:
            try:
                custom_fields = json.loads(product.custom_fields)
            except:
                custom_fields = {}

        return {
            "product_id": product.product_id,
            "product_name": product.product_name,
            "description": product.description,
            "price": float(product.price) if product.price else None,
            "sales": product.sales,
            "rating": float(product.rating) if product.rating else None,
            "review_count": product.review_count,
            "url": product.url,
            "shop_name": product.shop_name,
            "platform": product.platform,
            "source_file": product.source_file,
            "tags": tags,
            "demand_analysis": product.demand_analysis,
            "ai_analysis_status": product.ai_analysis_status,
            "custom_fields": custom_fields,
            "imported_at": product.imported_at.isoformat() if product.imported_at else None,
            "updated_at": product.updated_at.isoformat() if product.updated_at else None,
        }


# ==================== ProductFieldDefinitionRepository ====================
class ProductFieldDefinitionRepository:
    """[REQ-2.7] 字段定义数据访问层"""

    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_session()
        self._should_close = session is None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._should_close:
            self.session.close()

    def create(self, data: Dict[str, Any]) -> int:
        """创建字段定义"""
        field_def = ProductFieldDefinition(**data)
        self.session.add(field_def)
        self.session.commit()
        return field_def.field_id

    def get_by_id(self, field_id: int) -> Optional[Dict[str, Any]]:
        """按ID查询字段定义"""
        field_def = self.session.query(ProductFieldDefinition).filter_by(
            field_id=field_id
        ).first()

        if not field_def:
            return None

        return self._to_dict(field_def)

    def get_by_key(self, field_key: str) -> Optional[Dict[str, Any]]:
        """按键名查询字段定义"""
        field_def = self.session.query(ProductFieldDefinition).filter_by(
            field_key=field_key
        ).first()

        if not field_def:
            return None

        return self._to_dict(field_def)

    def get_all(self, order_by_order: bool = True) -> List[Dict[str, Any]]:
        """
        [REQ-2.7] 获取所有字段定义

        Args:
            order_by_order: 是否按field_order排序

        Returns:
            字段定义列表
        """
        query = self.session.query(ProductFieldDefinition)

        if order_by_order:
            query = query.order_by(ProductFieldDefinition.field_order)

        field_defs = query.all()
        return [self._to_dict(fd) for fd in field_defs]

    def update(self, field_id: int, data: Dict[str, Any]) -> bool:
        """更新字段定义"""
        result = self.session.query(ProductFieldDefinition).filter_by(
            field_id=field_id
        ).update(data)
        self.session.commit()
        return result > 0

    def delete(self, field_id: int) -> bool:
        """删除字段定义（仅非系统字段）"""
        # 检查是否为系统字段
        field_def = self.session.query(ProductFieldDefinition).filter_by(
            field_id=field_id
        ).first()

        if not field_def or field_def.is_system_field:
            return False

        self.session.delete(field_def)
        self.session.commit()
        return True

    def _to_dict(self, field_def: ProductFieldDefinition) -> Dict[str, Any]:
        """将ProductFieldDefinition对象转换为字典"""
        field_options = None
        if field_def.field_options:
            try:
                field_options = json.loads(field_def.field_options)
            except:
                field_options = []

        return {
            "field_id": field_def.field_id,
            "field_name": field_def.field_name,
            "field_key": field_def.field_key,
            "field_type": field_def.field_type,
            "is_required": field_def.is_required,
            "default_value": field_def.default_value,
            "field_options": field_options,
            "field_order": field_def.field_order,
            "field_description": field_def.field_description,
            "is_system_field": field_def.is_system_field,
            "created_at": field_def.created_at.isoformat() if field_def.created_at else None,
        }


# ==================== ProductImportLogRepository ====================
class ProductImportLogRepository:
    """[REQ-2.7] 导入日志数据访问层"""

    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_session()
        self._should_close = session is None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._should_close:
            self.session.close()

    def create(self, data: Dict[str, Any]) -> int:
        """创建导入日志"""
        log = ProductImportLog(**data)
        self.session.add(log)
        self.session.commit()
        return log.log_id

    def get_by_id(self, log_id: int) -> Optional[Dict[str, Any]]:
        """按ID查询导入日志"""
        log = self.session.query(ProductImportLog).filter_by(
            log_id=log_id
        ).first()

        if not log:
            return None

        return self._to_dict(log)

    def get_all(
        self,
        platform: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        [REQ-2.7] 获取导入日志列表

        Args:
            platform: 平台筛选
            status: 状态筛选
            limit: 返回数量限制

        Returns:
            导入日志列表
        """
        query = self.session.query(ProductImportLog)

        if platform:
            query = query.filter(ProductImportLog.platform == platform)
        if status:
            query = query.filter(ProductImportLog.import_status == status)

        logs = query.order_by(desc(ProductImportLog.imported_at)).limit(limit).all()
        return [self._to_dict(log) for log in logs]

    def update(self, log_id: int, data: Dict[str, Any]) -> bool:
        """更新导入日志"""
        result = self.session.query(ProductImportLog).filter_by(
            log_id=log_id
        ).update(data)
        self.session.commit()
        return result > 0

    def _to_dict(self, log: ProductImportLog) -> Dict[str, Any]:
        """将ProductImportLog对象转换为字典"""
        field_mapping = None
        if log.field_mapping:
            try:
                field_mapping = json.loads(log.field_mapping)
            except:
                field_mapping = {}

        return {
            "log_id": log.log_id,
            "source_file": log.source_file,
            "platform": log.platform,
            "total_rows": log.total_rows,
            "imported_rows": log.imported_rows,
            "skipped_rows": log.skipped_rows,
            "duplicate_rows": log.duplicate_rows,
            "field_mapping": field_mapping,
            "import_status": log.import_status,
            "error_message": log.error_message,
            "imported_at": log.imported_at.isoformat() if log.imported_at else None,
            "duration_seconds": log.duration_seconds,
        }
