"""
[REQ-010] P5.1: 商品属性提取 - API 路由
提供商品属性提取相关的 API 端点
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.services.attribute_extraction_service import AttributeExtractionService
from typing import Dict, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/api/attribute-extraction", tags=["attribute-extraction"])


class ExtractAttributesRequest(BaseModel):
    """属性提取请求"""
    batch_size: int = 100  # 批次大小


class ExtractMissingRequest(BaseModel):
    """AI辅助兜底请求"""
    max_products: Optional[int] = None  # 最大处理数量
    batch_size: int = 10  # 批次大小


@router.post("/extract", response_model=Dict)
async def extract_all_attributes(
    request: ExtractAttributesRequest,
    db: Session = Depends(get_db)
):
    """
    [REQ-010] P5.1: 批量提取所有商品的属性

    使用代码规则提取交付形式和关键词

    Args:
        request: 提取请求参数
        db: 数据库会话

    Returns:
        提取结果统计
    """
    try:
        # 创建服务
        service = AttributeExtractionService(db)

        # 批量提取
        result = service.process_all_products(batch_size=request.batch_size)

        return {
            "success": True,
            "message": "属性提取完成",
            "data": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提取失败: {str(e)}")


@router.post("/extract/{product_id}", response_model=Dict)
async def extract_product_attributes(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    [REQ-010] P5.1: 提取单个商品的属性

    Args:
        product_id: 商品ID
        db: 数据库会话

    Returns:
        提取结果
    """
    try:
        # 创建服务
        service = AttributeExtractionService(db)

        # 提取单个商品
        success, message = service.process_product(product_id)

        if not success:
            raise HTTPException(status_code=400, detail=message)

        return {
            "success": True,
            "message": message,
            "product_id": product_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提取失败: {str(e)}")


@router.post("/extract-missing", response_model=Dict)
async def extract_missing_attributes(
    request: ExtractMissingRequest,
    db: Session = Depends(get_db)
):
    """
    [REQ-012] P5.3: AI辅助兜底 - 处理代码规则无法识别的商品

    对delivery_type为空的商品使用AI识别

    Args:
        request: AI辅助请求参数
        db: 数据库会话

    Returns:
        处理结果统计
    """
    try:
        # 创建服务
        service = AttributeExtractionService(db)

        # AI辅助处理
        result = service.process_missing_delivery_types(
            max_products=request.max_products,
            batch_size=request.batch_size
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message", "处理失败"))

        return {
            "success": True,
            "message": result.get("message"),
            "data": result
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.get("/statistics", response_model=Dict)
async def get_extraction_statistics(db: Session = Depends(get_db)):
    """
    [REQ-010] P5.1: 获取属性提取统计

    返回商品属性提取情况统计

    Args:
        db: 数据库会话

    Returns:
        统计信息
    """
    try:
        # 创建服务
        service = AttributeExtractionService(db)

        # 获取统计
        stats = service.get_extraction_statistics()

        return {
            "success": True,
            "message": "统计信息获取成功",
            "data": stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")
