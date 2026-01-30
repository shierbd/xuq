"""
[REQ-011] P5.2: Top商品AI深度分析路由
提供Top商品分析的API端点
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from backend.database import get_db
from backend.services.top_product_analysis_service import TopProductAnalysisService

router = APIRouter(
    prefix="/api/top-product-analysis",
    tags=["top-product-analysis"]
)

@router.post("/analyze")
def analyze_all_top_products(
    top_n: int = Query(3, description="每个簇取Top N个商品"),
    ai_provider: str = Query("deepseek", description="AI提供商 (claude/deepseek)"),
    db: Session = Depends(get_db)
):
    """
    [REQ-011] P5.2: 批量分析所有簇的Top商品

    对每个簇的Top N商品进行AI深度分析，包括：
    1. 满足的用户需求
    2. 验证交付形式
    3. 补充关键词

    其他商品会自动继承所属簇的分析结果
    """
    try:
        service = TopProductAnalysisService(db, ai_provider=ai_provider)
        result = service.analyze_top_products(top_n=top_n, ai_provider=ai_provider)

        return {
            "success": True,
            "message": "Top商品分析完成",
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")

@router.post("/analyze/{cluster_id}")
def analyze_single_cluster_top_products(
    cluster_id: int,
    top_n: int = Query(3, description="Top N个商品"),
    ai_provider: str = Query("deepseek", description="AI提供商 (claude/deepseek)"),
    db: Session = Depends(get_db)
):
    """
    [REQ-011] P5.2: 分析单个簇的Top商品

    对指定簇的Top N商品进行AI深度分析
    """
    try:
        service = TopProductAnalysisService(db, ai_provider=ai_provider)
        result = service.analyze_single_cluster(
            cluster_id=cluster_id,
            top_n=top_n,
            ai_provider=ai_provider
        )

        return {
            "success": True,
            "message": f"簇 {cluster_id} 的Top商品分析完成",
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")

@router.get("/statistics")
def get_analysis_statistics(db: Session = Depends(get_db)):
    """
    [REQ-011] P5.2: 获取分析统计信息

    返回：
    - 总商品数
    - 已分析商品数
    - 未分析商品数
    - 分析覆盖率
    """
    try:
        service = TopProductAnalysisService(db)
        stats = service.get_analysis_statistics()

        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

@router.get("/top-products")
def get_top_products_by_cluster(
    top_n: int = Query(3, description="每个簇取Top N个商品"),
    db: Session = Depends(get_db)
):
    """
    [REQ-011] P5.2: 获取每个簇的Top商品列表

    返回每个簇的Top N商品（按评价数排序）
    """
    try:
        service = TopProductAnalysisService(db)
        top_products = service.get_top_products_by_cluster(top_n=top_n)

        # 转换为可序列化的格式
        result = {}
        for cluster_id, products in top_products.items():
            result[str(cluster_id)] = [
                {
                    "product_id": p.product_id,
                    "product_name": p.product_name,
                    "review_count": p.review_count,
                    "rating": p.rating,
                    "price": p.price,
                    "cluster_name": p.cluster_name,
                    "delivery_type": p.delivery_type,
                    "user_need": p.user_need
                }
                for p in products
            ]

        return {
            "success": True,
            "data": {
                "total_clusters": len(result),
                "top_products": result
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Top商品失败: {str(e)}")
