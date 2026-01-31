"""
[REQ-008] P4.1: 类别名称生成 - API 路由
提供类别名称生成相关的 API 端点
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.services.category_naming_service import CategoryNamingService
from typing import Dict, Optional, List
from pydantic import BaseModel

router = APIRouter(prefix="/api/clusters", tags=["clusters"])


class GenerateNamesRequest(BaseModel):
    """生成类别名称请求"""
    cluster_ids: Optional[List[int]] = None  # 可选，不传则处理所有簇
    top_n: int = 5  # 使用 Top N 商品
    batch_size: int = 10  # 批次大小
    ai_provider: str = "deepseek"  # AI 提供商


@router.post("/generate-names", response_model=Dict)
async def generate_category_names(
    request: GenerateNamesRequest,
    db: Session = Depends(get_db)
):
    """
    [REQ-008] P4.1: 批量生成类别名称

    为聚类簇生成可读的类别名称

    Args:
        request: 生成请求参数
        db: 数据库会话

    Returns:
        生成结果统计
    """
    try:
        # 创建服务
        service = CategoryNamingService(db, ai_provider=request.ai_provider)

        # 批量生成
        result = await service.generate_all_category_names(
            cluster_ids=request.cluster_ids,
            top_n=request.top_n,
            batch_size=request.batch_size
        )

        return {
            "success": True,
            "message": "类别名称生成完成",
            "data": result
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.post("/generate-name/{cluster_id}", response_model=Dict)
async def generate_single_category_name(
    cluster_id: int,
    top_n: int = 5,
    ai_provider: str = "deepseek",
    db: Session = Depends(get_db)
):
    """
    [REQ-008] P4.1: 为单个簇生成类别名称

    Args:
        cluster_id: 簇ID
        top_n: 使用 Top N 商品
        ai_provider: AI 提供商
        db: 数据库会话

    Returns:
        生成结果
    """
    try:
        # 创建服务
        print(f"[DEBUG ROUTER] Creating CategoryNamingService with ai_provider={ai_provider}")
        service = CategoryNamingService(db, ai_provider=ai_provider)
        print(f"[DEBUG ROUTER] CategoryNamingService created successfully")

        # 生成单个类别名称
        print(f"[DEBUG ROUTER] Calling generate_category_name for cluster {cluster_id}")
        result = await service.generate_category_name(cluster_id, top_n)
        print(f"[DEBUG ROUTER] Result: {result}")

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "生成失败"))

        return {
            "success": True,
            "message": "类别名称生成成功",
            "data": result
        }

    except ValueError as e:
        print(f"[DEBUG ROUTER] ValueError caught: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[DEBUG ROUTER] Exception caught: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.get("/naming-statistics", response_model=Dict)
async def get_naming_statistics(db: Session = Depends(get_db)):
    """
    [REQ-008] P4.1: 获取类别命名统计

    返回簇的命名情况统计

    Args:
        db: 数据库会话

    Returns:
        统计信息
    """
    try:
        # 创建服务（不需要 AI provider）
        service = CategoryNamingService(db, ai_provider="deepseek")

        # 获取统计
        stats = service.get_cluster_statistics()

        return {
            "success": True,
            "message": "统计信息获取成功",
            "data": stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@router.get("/top-products/{cluster_id}", response_model=Dict)
async def get_cluster_top_products(
    cluster_id: int,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """
    [REQ-008] P4.1: 获取簇内 Top 商品

    返回指定簇的 Top N 商品（按评价数排序）

    Args:
        cluster_id: 簇ID
        limit: 返回商品数量
        db: 数据库会话

    Returns:
        Top 商品列表
    """
    try:
        # 创建服务
        service = CategoryNamingService(db, ai_provider="deepseek")

        # 获取 Top 商品
        product_names = service.get_top_products_by_cluster(cluster_id, limit)

        return {
            "success": True,
            "message": "Top 商品获取成功",
            "data": {
                "cluster_id": cluster_id,
                "product_count": len(product_names),
                "products": product_names
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")
