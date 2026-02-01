"""
[REQ-004] P3.1: 需求分析 - API 路由
提供需求分析相关的 API 端点
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.services.demand_analysis_service import DemandAnalysisService
from typing import Dict, Optional, List
from pydantic import BaseModel

router = APIRouter(prefix="/api/demand-analysis", tags=["demand-analysis"])


class AnalyzeDemandRequest(BaseModel):
    """需求分析请求"""
    cluster_ids: Optional[List[int]] = None  # 可选，不传则处理所有簇
    top_n: int = 10  # 使用 Top N 商品
    batch_size: int = 5  # 批次大小
    ai_provider: str = "deepseek"  # AI 提供商
    max_clusters: Optional[int] = None  # 最多分析的簇数量（None 表示不限制）
    skip_analyzed: bool = True  # 是否跳过已分析的簇（默认 True）
    force_reanalyze: bool = False  # 是否强制重新分析已分析的簇（默认 False）


@router.post("/analyze", response_model=Dict)
async def analyze_cluster_demands(
    request: AnalyzeDemandRequest,
    db: Session = Depends(get_db)
):
    """
    [REQ-004] P3.1: 批量分析簇的用户需求

    使用 AI 分析每个簇的商品，识别满足的用户需求

    Args:
        request: 分析请求参数
        db: 数据库会话

    Returns:
        分析结果统计
    """
    try:
        # 调试日志：打印接收到的参数
        print(f"[DEBUG] Router received parameters:")
        print(f"  - max_clusters: {request.max_clusters} (type: {type(request.max_clusters)})")
        print(f"  - skip_analyzed: {request.skip_analyzed}")
        print(f"  - force_reanalyze: {request.force_reanalyze}")

        # 创建服务
        service = DemandAnalysisService(db, ai_provider=request.ai_provider)

        # 批量分析
        result = await service.analyze_all_clusters(
            cluster_ids=request.cluster_ids,
            top_n=request.top_n,
            batch_size=request.batch_size,
            max_clusters=request.max_clusters,
            skip_analyzed=request.skip_analyzed,
            force_reanalyze=request.force_reanalyze
        )

        return {
            "success": True,
            "message": "需求分析完成",
            "data": result
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.post("/analyze/{cluster_id}", response_model=Dict)
async def analyze_single_cluster_demand(
    cluster_id: int,
    top_n: int = 10,
    ai_provider: str = "deepseek",
    db: Session = Depends(get_db)
):
    """
    [REQ-004] P3.1: 分析单个簇的用户需求

    Args:
        cluster_id: 簇ID
        top_n: 使用 Top N 商品
        ai_provider: AI 提供商
        db: 数据库会话

    Returns:
        分析结果
    """
    try:
        # 创建服务
        service = DemandAnalysisService(db, ai_provider=ai_provider)

        # 分析单个簇
        result = await service.analyze_cluster_demand(cluster_id, top_n)

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "分析失败"))

        return {
            "success": True,
            "message": "需求分析成功",
            "data": result
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.get("/statistics", response_model=Dict)
async def get_analysis_statistics(db: Session = Depends(get_db)):
    """
    [REQ-004] P3.1: 获取需求分析统计

    返回簇的需求分析情况统计

    Args:
        db: 数据库会话

    Returns:
        统计信息
    """
    try:
        # 创建服务（不需要 AI provider，只查询数据库）
        service = DemandAnalysisService(db)

        # 获取统计
        stats = service.get_analysis_statistics()

        return {
            "success": True,
            "message": "统计信息获取成功",
            "data": stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@router.get("/cluster-products/{cluster_id}", response_model=Dict)
async def get_cluster_products(
    cluster_id: int,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    [REQ-004] P3.1: 获取簇内商品信息

    返回指定簇的商品信息（用于需求分析）

    Args:
        cluster_id: 簇ID
        limit: 返回商品数量
        db: 数据库会话

    Returns:
        商品信息列表
    """
    try:
        # 创建服务（不需要 AI provider，只查询数据库）
        service = DemandAnalysisService(db)

        # 获取商品信息
        products = service.get_cluster_products(cluster_id, limit)

        return {
            "success": True,
            "message": "商品信息获取成功",
            "data": {
                "cluster_id": cluster_id,
                "product_count": len(products),
                "products": products
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")
