"""
[REQ-001] 数据导入功能 - API 路由
提供数据导入、预览等 API 端点
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.services.import_service import ImportService
from typing import Dict
import io

router = APIRouter(prefix="/api/products", tags=["products"])

@router.post("/import", response_model=Dict)
async def import_products(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    [REQ-001] 导入商品数据
    
    支持 Excel (.xlsx, .xls) 和 CSV (.csv) 格式
    文件结构：无表头，固定 5 列
    """
    # 验证文件格式
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="不支持的文件格式，请上传 Excel 或 CSV 文件"
        )
    
    # 读取文件内容
    contents = await file.read()
    file_obj = io.BytesIO(contents)
    
    try:
        # 创建导入服务
        import_service = ImportService(db)
        
        # 执行导入
        result = import_service.import_from_file(file_obj, file.filename)
        
        return {
            "success": True,
            "message": "数据导入成功",
            "data": result
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")

@router.post("/preview", response_model=Dict)
async def preview_import(
    file: UploadFile = File(...),
    rows: int = 10,
    db: Session = Depends(get_db)
):
    """
    [REQ-001] 预览导入数据
    
    返回文件前 N 行数据用于预览
    """
    # 验证文件格式
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="不支持的文件格式，请上传 Excel 或 CSV 文件"
        )
    
    # 读取文件内容
    contents = await file.read()
    file_obj = io.BytesIO(contents)
    
    try:
        # 创建导入服务
        import_service = ImportService(db)
        
        # 获取预览
        result = import_service.get_import_preview(file_obj, file.filename, rows)
        
        return {
            "success": True,
            "message": "预览数据获取成功",
            "data": result
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览失败: {str(e)}")

@router.get("/count", response_model=Dict)
def get_product_count(db: Session = Depends(get_db)):
    """
    [REQ-001] 获取商品总数
    """
    from backend.models.product import Product
    
    total = db.query(Product).filter(Product.is_deleted == False).count()
    
    return {
        "success": True,
        "data": {
            "total": total
        }
    }

# [REQ-002] 数据管理功能 - API 路由扩展

from backend.services.product_service import ProductService
from backend.schemas.product_schema import (
    ProductResponse, ProductListResponse, ProductUpdate, ProductQueryParams
)
from typing import List

@router.get("/", response_model=ProductListResponse)
def get_products(
    page: int = 1,
    page_size: int = 50,
    search: Optional[str] = None,
    shop_name: Optional[str] = None,
    min_rating: Optional[float] = None,
    max_rating: Optional[float] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    sort_by: str = "import_time",
    sort_order: str = "desc",
    db: Session = Depends(get_db)
):
    """
    [REQ-002] 获取商品列表
    
    支持分页、搜索、筛选、排序
    """
    # 构建查询参数
    params = ProductQueryParams(
        page=page,
        page_size=page_size,
        search=search,
        shop_name=shop_name,
        min_rating=min_rating,
        max_rating=max_rating,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    # 查询商品
    product_service = ProductService(db)
    products, total = product_service.get_products(params)
    
    return ProductListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[ProductResponse.from_orm(p) for p in products]
    )

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    [REQ-002] 获取单个商品详情
    """
    product_service = ProductService(db)
    product = product_service.get_product_by_id(product_id)
    
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    return ProductResponse.from_orm(product)

@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    update_data: ProductUpdate,
    db: Session = Depends(get_db)
):
    """
    [REQ-002] 更新商品信息
    """
    product_service = ProductService(db)
    product = product_service.update_product(product_id, update_data)
    
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    return ProductResponse.from_orm(product)

@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    [REQ-002] 删除商品（软删除）
    """
    product_service = ProductService(db)
    success = product_service.delete_product(product_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    return {
        "success": True,
        "message": "商品删除成功"
    }

@router.post("/batch-delete")
def batch_delete_products(
    product_ids: List[int],
    db: Session = Depends(get_db)
):
    """
    [REQ-002] 批量删除商品（软删除）
    """
    product_service = ProductService(db)
    count = product_service.batch_delete_products(product_ids)
    
    return {
        "success": True,
        "message": f"成功删除 {count} 个商品",
        "deleted_count": count
    }
