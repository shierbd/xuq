"""
[REQ-002] 数据管理功能 - 数据模型 Schema
定义 API 请求和响应的数据结构
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ProductBase(BaseModel):
    """[REQ-002] 商品基础信息"""
    product_name: str = Field(..., description="商品名称")
    rating: Optional[float] = Field(None, description="评分 (0-5)")
    review_count: Optional[int] = Field(None, description="评价数量")
    shop_name: Optional[str] = Field(None, description="店铺名称")
    price: Optional[float] = Field(None, description="价格")

class ProductCreate(ProductBase):
    """[REQ-002] 创建商品"""
    pass

class ProductUpdate(BaseModel):
    """[REQ-002] 更新商品"""
    product_name: Optional[str] = None
    rating: Optional[float] = Field(None, ge=0, le=5, description="评分 (0-5)")
    review_count: Optional[int] = Field(None, ge=0, description="评价数量")
    shop_name: Optional[str] = None
    price: Optional[float] = Field(None, ge=0, description="价格")

class ProductResponse(ProductBase):
    """[REQ-002] 商品响应"""
    product_id: int
    cluster_id: Optional[int] = None
    cluster_name: Optional[str] = None
    cluster_name_cn: Optional[str] = None  # [REQ-008] P4.1: 类别名称中文翻译
    delivery_type: Optional[str] = None
    delivery_format: Optional[str] = None
    delivery_platform: Optional[str] = None
    user_need: Optional[str] = None
    import_time: datetime
    is_deleted: bool

    class Config:
        from_attributes = True

class ProductListResponse(BaseModel):
    """[REQ-002] 商品列表响应"""
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    items: List[ProductResponse] = Field(..., description="商品列表")

class ProductQueryParams(BaseModel):
    """[REQ-002] 商品查询参数"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(50, ge=1, le=100, description="每页数量")
    search: Optional[str] = Field(None, description="搜索关键词")
    shop_name: Optional[str] = Field(None, description="店铺名称筛选")
    cluster_id: Optional[int] = Field(None, description="簇ID筛选")
    cluster_name: Optional[str] = Field(None, description="类别名称筛选")
    min_rating: Optional[float] = Field(None, ge=0, le=5, description="最低评分")
    max_rating: Optional[float] = Field(None, ge=0, le=5, description="最高评分")
    min_price: Optional[float] = Field(None, ge=0, description="最低价格")
    max_price: Optional[float] = Field(None, ge=0, description="最高价格")
    min_review_count: Optional[int] = Field(None, ge=0, description="最小评价数")
    max_review_count: Optional[int] = Field(None, ge=0, description="最大评价数")
    sort_by: Optional[str] = Field("import_time", description="排序字段")
    sort_order: Optional[str] = Field("desc", description="排序方向 (asc/desc)")
