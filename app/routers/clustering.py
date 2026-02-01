"""
聚类管理路由
"""
from fastapi import APIRouter, Request, Query, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
import sys
from pathlib import Path

# 添加 backend 到路径以导入 ClusteringService
backend_path = Path(__file__).parent.parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.database import get_db, ClusterSummary, Product

router = APIRouter(prefix="/clustering", tags=["clustering"])
templates = Jinja2Templates(directory="app/templates")

@router.get("", response_class=HTMLResponse)
async def clustering_page(request: Request):
    """聚类管理页面"""
    return templates.TemplateResponse("clustering.html", {
        "request": request,
        "title": "聚类分析"
    })

@router.get("/list", response_class=HTMLResponse)
async def clustering_list(
    request: Request,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    stage: Optional[str] = None,
    priority: Optional[str] = None,
    is_direction: Optional[bool] = None,
    search: Optional[str] = None
):
    """获取聚类列表（HTMX）"""

    # 构建查询
    query = db.query(ClusterSummary)

    # 阶段筛选
    if stage:
        query = query.filter(ClusterSummary.stage == stage)

    # 优先级筛选
    if priority:
        query = query.filter(ClusterSummary.priority == priority)

    # 方向筛选
    if is_direction is not None:
        query = query.filter(ClusterSummary.is_direction == is_direction)

    # 搜索
    if search:
        query = query.filter(
            (ClusterSummary.cluster_label.contains(search)) |
            (ClusterSummary.cluster_explanation.contains(search)) |
            (ClusterSummary.top_keywords.contains(search))
        )

    # 按创建时间倒序
    query = query.order_by(ClusterSummary.created_time.desc())

    # 总数
    total = query.count()

    # 分页
    total_pages = max(1, (total + per_page - 1) // per_page)
    clusters = query.offset((page - 1) * per_page).limit(per_page).all()

    return templates.TemplateResponse("clustering_table.html", {
        "request": request,
        "clusters": clusters,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "range": range
    })

@router.get("/{cluster_id}", response_class=HTMLResponse)
async def cluster_detail(
    request: Request,
    cluster_id: int,
    db: Session = Depends(get_db)
):
    """聚类详情页面"""
    # 获取聚类摘要
    cluster = db.query(ClusterSummary).filter(
        ClusterSummary.cluster_id == cluster_id
    ).first()

    if not cluster:
        return "<div class='text-red-600'>聚类不存在</div>"

    # 获取该聚类下的商品
    products = db.query(Product).filter(
        Product.cluster_id == cluster_id,
        Product.is_deleted == False
    ).limit(100).all()

    return templates.TemplateResponse("cluster_detail.html", {
        "request": request,
        "cluster": cluster,
        "products": products,
        "title": f"聚类详情 - {cluster.label}"
    })

@router.get("/stats/overview", response_class=JSONResponse)
async def clustering_stats(db: Session = Depends(get_db)):
    """聚类统计信息（JSON）"""

    # 总聚类数
    total_clusters = db.query(ClusterSummary).count()

    # 按阶段统计
    stage_stats = db.query(
        ClusterSummary.stage,
        func.count(ClusterSummary.summary_id)
    ).group_by(ClusterSummary.stage).all()

    # 按优先级统计
    priority_stats = db.query(
        ClusterSummary.priority,
        func.count(ClusterSummary.summary_id)
    ).group_by(ClusterSummary.priority).all()

    # 方向聚类数
    direction_count = db.query(ClusterSummary).filter(
        ClusterSummary.is_direction == True
    ).count()

    # 平均聚类大小
    avg_size = db.query(func.avg(ClusterSummary.cluster_size)).scalar() or 0

    # 总商品数
    total_products = db.query(Product).filter(
        Product.is_deleted == False
    ).count()

    # 已聚类商品数
    clustered_products = db.query(Product).filter(
        Product.cluster_id.isnot(None),
        Product.is_deleted == False
    ).count()

    return {
        "total_clusters": total_clusters,
        "direction_count": direction_count,
        "avg_cluster_size": round(avg_size, 2),
        "total_products": total_products,
        "clustered_products": clustered_products,
        "clustering_rate": round(clustered_products / total_products * 100, 2) if total_products > 0 else 0,
        "stage_stats": {stage: count for stage, count in stage_stats},
        "priority_stats": {priority: count for priority, count in priority_stats}
    }

@router.get("/stats/chart", response_class=JSONResponse)
async def clustering_chart_data(db: Session = Depends(get_db)):
    """聚类图表数据（JSON）"""

    # 获取Top 20聚类（按大小）
    top_clusters = db.query(ClusterSummary).order_by(
        ClusterSummary.cluster_size.desc()
    ).limit(20).all()

    # 准备图表数据
    chart_data = {
        "labels": [c.label for c in top_clusters],
        "sizes": [c.cluster_size for c in top_clusters],
        "volumes": [c.total_volume or 0 for c in top_clusters],
        "priorities": [c.priority or "unknown" for c in top_clusters]
    }

    return chart_data

@router.post("/execute", response_class=JSONResponse)
async def execute_clustering(
    request: Request,
    db: Session = Depends(get_db),
    min_cluster_size: int = Form(10),
    use_three_stage: bool = Form(True),
    stage1_min_size: int = Form(10),
    stage2_min_size: int = Form(5),
    stage3_min_size: int = Form(3)
):
    """
    执行聚类分析

    使用 Sentence Transformers + HDBSCAN 进行语义聚类
    """
    try:
        # 导入 ClusteringService
        from services.clustering_service import ClusteringService

        # 创建聚类服务
        clustering_service = ClusteringService(db, model_name="all-mpnet-base-v2")

        # 执行聚类
        result = clustering_service.cluster_all_products(
            min_cluster_size=min_cluster_size,
            use_three_stage=use_three_stage,
            stage1_min_size=stage1_min_size,
            stage2_min_size=stage2_min_size,
            stage3_min_size=stage3_min_size
        )

        if result["success"]:
            # 生成簇级汇总
            summary = clustering_service.generate_cluster_summary()

            # 保存到 cluster_summaries 表
            # 先清空旧数据
            db.query(ClusterSummary).delete()

            # 插入新数据
            for item in summary:
                cluster_summary = ClusterSummary(
                    cluster_id=item['cluster_id'],
                    stage='P',  # Product clustering stage
                    cluster_size=item['cluster_size'],
                    cluster_label=item.get('cluster_name_cn') or item.get('cluster_name'),
                    top_keywords=', '.join(item['example_products'][:3]),
                    example_phrases=', '.join(item['example_products'][:5]),
                    avg_volume=item.get('total_reviews', 0),
                    total_volume=item.get('total_reviews', 0),
                    is_direction=True if item['cluster_size'] >= 20 else False,
                    priority='high' if item['cluster_size'] >= 50 else 'medium' if item['cluster_size'] >= 20 else 'low'
                )
                db.add(cluster_summary)

            db.commit()

            return {
                "success": True,
                "message": f"聚类完成！生成了 {result['n_clusters']} 个簇",
                "data": {
                    "total_products": result['total_products'],
                    "n_clusters": result['n_clusters'],
                    "n_noise": result['n_noise'],
                    "noise_ratio": round(result['noise_ratio'], 2),
                    "clustering_mode": result.get('clustering_mode', 'single_stage')
                }
            }
        else:
            return {
                "success": False,
                "message": result.get("message", "聚类失败")
            }

    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Clustering error: {error_detail}")
        return {
            "success": False,
            "message": f"聚类执行失败: {str(e)}",
            "error": error_detail
        }
