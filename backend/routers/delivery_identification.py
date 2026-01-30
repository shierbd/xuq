"""
[REQ-005] P3.2: 交付产品识别 - API 路由
提供交付产品识别相关的 API 端点
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.services.delivery_identification_service import DeliveryIdentificationService
from typing import Dict, Optional, List
from pydantic import BaseModel

router = APIRouter(prefix="/api/delivery-identification", tags=["delivery-identification"])


class IdentifyProductsRequest(BaseModel):
    """交付产品识别请求"""
    product_ids: Optional[List[int]] = None  # 可选，不传则处理所有商品
    use_ai_for_unmatched: bool = False  # 对规则无法识别的商品使用 AI
    batch_size: int = 100  # 批次大小
    ai_provider: str = "deepseek"  # AI 提供商


@router.post("/identify", response_model=Dict)
async def identify_products(
    request: IdentifyProductsRequest,
    db: Session = Depends(get_db)
):
    """
    [REQ-005] P3.2: 批量识别商品的交付形式

    使用关键词规则 + AI 识别商品的交付类型

    Args:
        request: 识别请求参数
        db: 数据库会话

    Returns:
        识别结果统计
    """
    try:
        # 创建服务
        service = DeliveryIdentificationService(db, ai_provider=request.ai_provider)

        # 批量识别
        result = await service.identify_all_products(
            product_ids=request.product_ids,
            use_ai_for_unmatched=request.use_ai_for_unmatched,
            batch_size=request.batch_size
        )

        return {
            "success": True,
            "message": "交付产品识别完成",
            "data": result
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"识别失败: {str(e)}")


@router.post("/identify/{product_id}", response_model=Dict)
async def identify_single_product(
    product_id: int,
    use_ai: bool = False,
    ai_provider: str = "deepseek",
    db: Session = Depends(get_db)
):
    """
    [REQ-005] P3.2: 识别单个商品的交付形式

    Args:
        product_id: 商品ID
        use_ai: 是否使用 AI（如果规则无法识别）
        ai_provider: AI 提供商
        db: 数据库会话

    Returns:
        识别结果
    """
    try:
        # 创建服务
        service = DeliveryIdentificationService(db, ai_provider=ai_provider)

        # 识别单个商品
        result = await service.identify_product(product_id, use_ai=use_ai)

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "识别失败"))

        return {
            "success": True,
            "message": "交付产品识别成功",
            "data": result
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"识别失败: {str(e)}")


@router.get("/statistics", response_model=Dict)
async def get_identification_statistics(db: Session = Depends(get_db)):
    """
    [REQ-005] P3.2: 获取交付产品识别统计

    返回商品的交付产品识别情况统计

    Args:
        db: 数据库会话

    Returns:
        统计信息
    """
    try:
        # 创建服务（不需要 AI provider，只查询数据库）
        service = DeliveryIdentificationService(db)

        # 获取统计
        stats = service.get_identification_statistics()

        return {
            "success": True,
            "message": "统计信息获取成功",
            "data": stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")
