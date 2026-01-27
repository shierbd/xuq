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
