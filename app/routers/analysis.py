"""
需求分析路由
"""
from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
import httpx
import os

from app.database import get_db, ClusterSummary, Product

router = APIRouter(prefix="/analysis", tags=["analysis"])
templates = Jinja2Templates(directory="app/templates")

@router.get("", response_class=HTMLResponse)
async def analysis_page(request: Request, db: Session = Depends(get_db)):
    """需求分析页面"""
    # 获取统计信息
    total_clusters = db.query(ClusterSummary).count()
    analyzed_clusters = db.query(ClusterSummary).filter(
        ClusterSummary.cluster_explanation.isnot(None)
    ).count()

    return templates.TemplateResponse("analysis.html", {
        "request": request,
        "title": "需求分析",
        "total_clusters": total_clusters,
        "analyzed_clusters": analyzed_clusters
    })

@router.post("/analyze", response_class=HTMLResponse)
async def analyze_cluster(
    request: Request,
    cluster_id: int = Form(...),
    top_n: int = Form(10),
    ai_provider: str = Form("deepseek"),
    db: Session = Depends(get_db)
):
    """分析单个聚类的需求（HTMX）"""
    try:
        # 获取聚类信息
        cluster = db.query(ClusterSummary).filter(
            ClusterSummary.cluster_id == cluster_id
        ).first()

        if not cluster:
            return """
            <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                聚类不存在
            </div>
            """

        # 获取聚类商品
        products = db.query(Product).filter(
            Product.cluster_id == cluster_id,
            Product.is_deleted == False
        ).order_by(
            Product.review_count.desc()
        ).limit(top_n).all()

        if not products:
            return """
            <div class="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded">
                该聚类没有商品数据
            </div>
            """

        # 构建 AI 分析请求
        products_text = "\n".join([
            f"{i+1}. {p.product_name} (评价数: {p.review_count}, 评分: {p.rating})"
            for i, p in enumerate(products)
        ])

        prompt = f"""分析以下 Etsy 商品，识别这些商品满足的用户需求。

类别: {cluster.label}
商品列表：
{products_text}

请用中文回答，包含以下内容：
1. 核心用户需求（1-2句话概括）
2. 目标用户群体
3. 使用场景
4. 产品特点

请简洁回答，每项不超过50字。"""

        # 调用 AI API
        api_key = os.getenv("DEEPSEEK_API_KEY", "sk-fb8318ee2b3c45a39ba642843ed8a287")
        api_url = "https://api.deepseek.com/v1/chat/completions"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                api_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7
                }
            )

            if response.status_code != 200:
                return f"""
                <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                    AI 分析失败: {response.text}
                </div>
                """

            result = response.json()
            analysis = result["choices"][0]["message"]["content"]

        # 返回分析结果
        return templates.TemplateResponse("analysis_result.html", {
            "request": request,
            "cluster": cluster,
            "products": products,
            "analysis": analysis,
            "ai_provider": ai_provider
        })

    except Exception as e:
        return f"""
        <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            分析失败: {str(e)}
        </div>
        """

@router.post("/batch-analyze", response_class=JSONResponse)
async def batch_analyze(
    request: Request,
    max_clusters: int = Form(10),
    top_n: int = Form(10),
    ai_provider: str = Form("deepseek"),
    db: Session = Depends(get_db)
):
    """批量分析聚类需求（JSON）"""
    try:
        # 获取未分析的聚类
        clusters = db.query(ClusterSummary).filter(
            ClusterSummary.cluster_explanation.is_(None)
        ).limit(max_clusters).all()

        if not clusters:
            return {
                "success": True,
                "message": "没有需要分析的聚类",
                "data": {
                    "analyzed_count": 0,
                    "total_count": 0
                }
            }

        analyzed_count = 0
        errors = []

        # 批量分析
        for cluster in clusters:
            try:
                # 获取聚类商品
                products = db.query(Product).filter(
                    Product.cluster_id == cluster.cluster_id,
                    Product.is_deleted == False
                ).order_by(
                    Product.review_count.desc()
                ).limit(top_n).all()

                if not products:
                    continue

                # 构建 AI 分析请求
                products_text = "\n".join([
                    f"{i+1}. {p.product_name}"
                    for i, p in enumerate(products)
                ])

                prompt = f"""分析以下商品，用一句话概括用户需求：

{products_text}

要求：中文回答，不超过30字。"""

                # 调用 AI API
                api_key = os.getenv("DEEPSEEK_API_KEY", "sk-fb8318ee2b3c45a39ba642843ed8a287")
                api_url = "https://api.deepseek.com/v1/chat/completions"

                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        api_url,
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "deepseek-chat",
                            "messages": [
                                {"role": "user", "content": prompt}
                            ],
                            "temperature": 0.7
                        }
                    )

                    if response.status_code == 200:
                        result = response.json()
                        analysis = result["choices"][0]["message"]["content"]

                        # 更新聚类解释
                        cluster.cluster_explanation = analysis
                        db.commit()
                        analyzed_count += 1
                    else:
                        errors.append(f"Cluster {cluster.cluster_id}: API error")

            except Exception as e:
                errors.append(f"Cluster {cluster.cluster_id}: {str(e)}")
                continue

        return {
            "success": True,
            "message": f"批量分析完成，成功分析 {analyzed_count} 个聚类",
            "data": {
                "analyzed_count": analyzed_count,
                "total_count": len(clusters),
                "errors": errors
            }
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"批量分析失败: {str(e)}",
            "data": None
        }

@router.get("/history", response_class=HTMLResponse)
async def analysis_history(
    request: Request,
    db: Session = Depends(get_db)
):
    """分析历史记录（HTMX）"""
    # 获取已分析的聚类
    clusters = db.query(ClusterSummary).filter(
        ClusterSummary.cluster_explanation.isnot(None)
    ).order_by(
        ClusterSummary.updated_time.desc()
    ).limit(50).all()

    return templates.TemplateResponse("analysis_history.html", {
        "request": request,
        "clusters": clusters
    })
