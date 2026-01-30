"""
[REQ-001] 数据导入功能 - API 路由
提供数据导入、预览等 API 端点
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.services.import_service import ImportService
from typing import Dict, Optional, List as TypingList
from pydantic import BaseModel
import io

router = APIRouter(prefix="/api/products", tags=["products"])

@router.post("/import", response_model=Dict)
async def import_products(
    file: UploadFile = File(...),
    platform: str = "etsy",
    field_mapping: str = "{}",
    skip_duplicates: bool = True,
    db: Session = Depends(get_db)
):
    """
    [REQ-001] 导入商品数据

    支持 Excel (.xlsx, .xls) 和 CSV (.csv) 格式
    支持自定义字段映射
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
        # 解析字段映射
        import json
        mapping = json.loads(field_mapping) if field_mapping else {}

        # 创建导入服务
        import_service = ImportService(db)

        # 执行导入
        result = import_service.import_from_file(
            file_obj,
            file.filename,
            field_mapping=mapping,
            skip_duplicates=skip_duplicates
        )

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

@router.get("/stats/summary", response_model=Dict)
def get_stats_summary(db: Session = Depends(get_db)):
    """
    获取商品统计摘要
    """
    from backend.models.product import Product
    from sqlalchemy import func

    # 基础统计
    total_products = db.query(Product).filter(Product.is_deleted == False).count()

    # 评分统计
    rating_stats = db.query(
        func.avg(Product.rating).label('avg_rating'),
        func.min(Product.rating).label('min_rating'),
        func.max(Product.rating).label('max_rating')
    ).filter(
        Product.is_deleted == False,
        Product.rating.isnot(None)
    ).first()

    # 价格统计
    price_stats = db.query(
        func.avg(Product.price).label('avg_price'),
        func.min(Product.price).label('min_price'),
        func.max(Product.price).label('max_price')
    ).filter(
        Product.is_deleted == False,
        Product.price.isnot(None)
    ).first()

    # 评价数统计
    review_stats = db.query(
        func.sum(Product.review_count).label('total_reviews'),
        func.avg(Product.review_count).label('avg_reviews')
    ).filter(
        Product.is_deleted == False,
        Product.review_count.isnot(None)
    ).first()

    return {
        "success": True,
        "data": {
            "total_products": total_products,
            "rating_stats": {
                "avg": float(rating_stats.avg_rating) if rating_stats.avg_rating else 0,
                "min": float(rating_stats.min_rating) if rating_stats.min_rating else 0,
                "max": float(rating_stats.max_rating) if rating_stats.max_rating else 0
            } if rating_stats else {},
            "price_stats": {
                "avg": float(price_stats.avg_price) if price_stats.avg_price else 0,
                "min": float(price_stats.min_price) if price_stats.min_price else 0,
                "max": float(price_stats.max_price) if price_stats.max_price else 0
            } if price_stats else {},
            "review_stats": {
                "total": int(review_stats.total_reviews) if review_stats.total_reviews else 0,
                "avg": float(review_stats.avg_reviews) if review_stats.avg_reviews else 0
            } if review_stats else {}
        }
    }

@router.get("/tags/unique", response_model=Dict)
def get_unique_tags(db: Session = Depends(get_db)):
    """
    获取所有唯一的标签

    注意：当前 Product 模型不包含 tags 字段，返回空列表
    """
    # Product 模型目前不包含 tags 字段
    # 返回空列表，避免错误
    return {
        "success": True,
        "data": {
            "tags": [],
            "message": "Product 模型当前不包含 tags 字段"
        }
    }

@router.get("/visualization/data")
def get_visualization_data(db: Session = Depends(get_db)):
    """
    [REQ-013] P6.1: 获取数据可视化所需的数据

    返回用于图表展示的统计数据
    """
    from backend.models.product import Product
    from sqlalchemy import func

    # 1. 类别大小分布（簇大小分布）
    cluster_distribution = db.query(
        Product.cluster_name,
        func.count(Product.product_id).label('count')
    ).filter(
        Product.is_deleted == False,
        Product.cluster_name.isnot(None)
    ).group_by(Product.cluster_name).order_by(func.count(Product.product_id).desc()).limit(20).all()

    # 2. 评分分布
    rating_distribution = db.query(
        Product.rating,
        func.count(Product.product_id).label('count')
    ).filter(
        Product.is_deleted == False,
        Product.rating.isnot(None)
    ).group_by(Product.rating).order_by(Product.rating).all()

    # 3. 价格分布（分段统计）
    price_ranges = [
        (0, 10, "$0-10"),
        (10, 20, "$10-20"),
        (20, 30, "$20-30"),
        (30, 50, "$30-50"),
        (50, 100, "$50-100"),
        (100, float('inf'), "$100+")
    ]

    price_distribution = []
    for min_price, max_price, label in price_ranges:
        if max_price == float('inf'):
            count = db.query(Product).filter(
                Product.is_deleted == False,
                Product.price >= min_price
            ).count()
        else:
            count = db.query(Product).filter(
                Product.is_deleted == False,
                Product.price >= min_price,
                Product.price < max_price
            ).count()

        if count > 0:
            price_distribution.append({
                'range': label,
                'count': count
            })

    # 4. 交付形式分布
    delivery_type_distribution = db.query(
        Product.delivery_type,
        func.count(Product.product_id).label('count')
    ).filter(
        Product.is_deleted == False,
        Product.delivery_type.isnot(None)
    ).group_by(Product.delivery_type).order_by(func.count(Product.product_id).desc()).limit(15).all()

    # 5. 评价数分布（分段统计）
    review_ranges = [
        (0, 100, "0-100"),
        (100, 500, "100-500"),
        (500, 1000, "500-1K"),
        (1000, 5000, "1K-5K"),
        (5000, 10000, "5K-10K"),
        (10000, float('inf'), "10K+")
    ]

    review_distribution = []
    for min_reviews, max_reviews, label in review_ranges:
        if max_reviews == float('inf'):
            count = db.query(Product).filter(
                Product.is_deleted == False,
                Product.review_count >= min_reviews
            ).count()
        else:
            count = db.query(Product).filter(
                Product.is_deleted == False,
                Product.review_count >= min_reviews,
                Product.review_count < max_reviews
            ).count()

        if count > 0:
            review_distribution.append({
                'range': label,
                'count': count
            })

    return {
        "success": True,
        "data": {
            "cluster_distribution": [
                {"name": name or "未分类", "value": count}
                for name, count in cluster_distribution
            ],
            "rating_distribution": [
                {"rating": float(rating), "count": count}
                for rating, count in rating_distribution
            ],
            "price_distribution": price_distribution,
            "delivery_type_distribution": [
                {"type": dtype, "count": count}
                for dtype, count in delivery_type_distribution
            ],
            "review_distribution": review_distribution
        }
    }

# [REQ-002] 数据管理功能 - API 路由扩展

from backend.services.product_service import ProductService
from backend.schemas.product_schema import (
    ProductResponse, ProductListResponse, ProductUpdate, ProductQueryParams
)
from typing import List, Optional

@router.get("/", response_model=ProductListResponse)
def get_products(
    page: int = 1,
    page_size: int = 50,
    search: Optional[str] = None,
    shop_name: Optional[str] = None,
    cluster_name: Optional[str] = None,
    min_rating: Optional[float] = None,
    max_rating: Optional[float] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_review_count: Optional[int] = None,
    max_review_count: Optional[int] = None,
    sort_by: str = "import_time",
    sort_order: str = "desc",
    db: Session = Depends(get_db)
):
    """
    [REQ-002] 获取商品列表
    [REQ-009] P4.2: 支持复杂筛选（类别名称、评价数范围等）

    支持分页、搜索、筛选、排序
    """
    # 构建查询参数
    params = ProductQueryParams(
        page=page,
        page_size=page_size,
        search=search,
        shop_name=shop_name,
        cluster_name=cluster_name,
        min_rating=min_rating,
        max_rating=max_rating,
        min_price=min_price,
        max_price=max_price,
        min_review_count=min_review_count,
        max_review_count=max_review_count,
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


class GenerateNamesRequest(BaseModel):
    cluster_ids: Optional[TypingList[int]] = None
    force_regenerate: bool = False

@router.post("/generate-cluster-names")
async def generate_cluster_names(
    request: GenerateNamesRequest,
    db: Session = Depends(get_db)
):
    """
    [REQ-008] P4.1: 为簇生成类别名称（AI）

    参数：
    - cluster_ids: 可选，指定簇ID列表，不传则处理所有簇
    - force_regenerate: 是否强制重新生成（覆盖已有的）
    """
    from backend.models.product import Product
    from sqlalchemy import func, desc
    import logging

    logger = logging.getLogger(__name__)

    # 获取需要处理的簇
    if request.cluster_ids:
        # 获取指定的簇
        cluster_query = db.query(Product.cluster_id).filter(
            Product.cluster_id.in_(request.cluster_ids),
            Product.cluster_id.isnot(None),
            Product.cluster_id != -1,  # 排除噪音点
            Product.is_deleted == False
        ).group_by(Product.cluster_id)
    else:
        if request.force_regenerate:
            # 处理所有簇
            cluster_query = db.query(Product.cluster_id).filter(
                Product.cluster_id.isnot(None),
                Product.cluster_id != -1,  # 排除噪音点
                Product.is_deleted == False
            ).group_by(Product.cluster_id)
        else:
            # 只处理没有类别名的簇
            cluster_query = db.query(Product.cluster_id).filter(
                Product.cluster_id.isnot(None),
                Product.cluster_id != -1,  # 排除噪音点
                Product.cluster_name.is_(None),
                Product.is_deleted == False
            ).group_by(Product.cluster_id)

    clusters = [row[0] for row in cluster_query.all()]

    if not clusters:
        return {
            "success": True,
            "message": "没有需要处理的簇",
            "data": {
                "total_clusters": 0,
                "processed": 0,
                "failed": 0,
                "cost_usd": 0,
                "results": []
            }
        }

    results = []
    failed = 0
    total_cost = 0

    for cluster_id in clusters:
        try:
            # 获取Top 5商品
            top_products = db.query(Product).filter(
                Product.cluster_id == cluster_id,
                Product.is_deleted == False
            ).order_by(desc(Product.review_count)).limit(5).all()

            if not top_products:
                logger.warning(f"Cluster {cluster_id} has no products")
                failed += 1
                continue

            # 简单生成类别名（基于商品名称的关键词）
            # TODO: 后续可以接入AI API
            product_names = [p.product_name for p in top_products]
            cluster_name = generate_simple_cluster_name(product_names)

            # 获取簇大小
            cluster_size = db.query(func.count(Product.product_id)).filter(
                Product.cluster_id == cluster_id,
                Product.is_deleted == False
            ).scalar()

            # 更新数据库 - 更新该簇的所有商品
            db.query(Product).filter(
                Product.cluster_id == cluster_id
            ).update({"cluster_name": cluster_name})
            db.commit()

            results.append({
                "cluster_id": cluster_id,
                "cluster_name": cluster_name,
                "cluster_size": cluster_size,
                "top_products": [p.product_name for p in top_products[:3]]
            })

        except Exception as e:
            failed += 1
            logger.error(f"Failed to generate name for cluster {cluster_id}: {e}")
            db.rollback()

    return {
        "success": True,
        "message": f"成功生成{len(results)}个簇的类别名称",
        "data": {
            "total_clusters": len(clusters),
            "processed": len(results),
            "failed": failed,
            "cost_usd": round(total_cost, 2),
            "results": results
        }
    }

def generate_simple_cluster_name(product_names: TypingList[str]) -> str:
    """
    基于商品名称生成简单的类别名称

    提取最常见的关键词作为类别名
    """
    from collections import Counter
    import re

    # 提取所有单词
    all_words = []
    for name in product_names:
        # 转小写，提取单词
        words = re.findall(r'\b[a-zA-Z]{3,}\b', name.lower())
        all_words.extend(words)

    # 过滤常见停用词
    stop_words = {'the', 'and', 'for', 'with', 'template', 'digital', 'printable',
                  'download', 'pdf', 'instant', 'editable', 'customizable', 'bundle'}
    filtered_words = [w for w in all_words if w not in stop_words]

    # 统计词频
    word_counts = Counter(filtered_words)

    # 获取最常见的2-3个词
    top_words = [word for word, count in word_counts.most_common(3)]

    if not top_words:
        return "Uncategorized"

    # 首字母大写
    cluster_name = " & ".join([w.capitalize() for w in top_words[:2]])

    return cluster_name


# [REQ-010] P5.1: 商品属性提取 - API 路由扩展

from backend.services.attribute_extraction_service import AttributeExtractionService

@router.post("/extract-attributes")
async def extract_product_attributes(
    product_ids: Optional[List[int]] = None,
    batch_size: int = 100,
    db: Session = Depends(get_db)
):
    """
    [REQ-010] P5.1: 批量提取商品属性

    从商品名称中提取交付形式、格式、平台等属性

    参数：
    - product_ids: 可选，指定商品ID列表，不传则处理所有商品
    - batch_size: 批处理大小（默认100）
    """
    extraction_service = AttributeExtractionService(db)

    if product_ids:
        # 处理指定商品
        processed = 0
        failed = 0

        for product_id in product_ids:
            success, message = extraction_service.process_product(product_id)
            if success:
                processed += 1
            else:
                failed += 1

        return {
            "success": True,
            "message": f"成功处理 {processed} 个商品",
            "data": {
                "total": len(product_ids),
                "processed": processed,
                "failed": failed
            }
        }
    else:
        # 处理所有商品
        result = extraction_service.process_all_products(batch_size=batch_size)

        return {
            "success": True,
            "message": f"批量属性提取完成，成功率 {result['success_rate']}%",
            "data": result
        }

@router.get("/extraction-statistics")
def get_extraction_statistics(db: Session = Depends(get_db)):
    """
    [REQ-010] P5.1: 获取属性提取统计信息

    返回属性提取的覆盖率和分布情况
    """
    extraction_service = AttributeExtractionService(db)
    stats = extraction_service.get_extraction_statistics()

    return {
        "success": True,
        "data": stats
    }


# [REQ-011] P5.2: Top商品AI深度分析 - API 路由扩展

from backend.services.ai_analysis_service import AIAnalysisService

@router.post("/analyze-top-products")
async def analyze_top_products(
    cluster_ids: Optional[List[int]] = None,
    top_n: int = 3,
    db: Session = Depends(get_db)
):
    """
    [REQ-011] P5.2: 分析簇的Top商品

    使用AI分析每个簇的Top商品，提取用户需求等信息

    参数：
    - cluster_ids: 可选，指定簇ID列表，不传则处理所有簇
    - top_n: 每个簇分析的Top商品数量（默认3）
    """
    analysis_service = AIAnalysisService(db)

    if cluster_ids:
        # 处理指定簇
        processed = 0
        failed = 0
        results = []

        for cluster_id in cluster_ids:
            success, message, analysis = analysis_service.analyze_cluster_top_products(cluster_id, top_n)
            if success:
                processed += 1
                results.append({
                    "cluster_id": cluster_id,
                    "analysis": analysis
                })
            else:
                failed += 1

        return {
            "success": True,
            "message": f"成功分析 {processed} 个簇",
            "data": {
                "total": len(cluster_ids),
                "processed": processed,
                "failed": failed,
                "results": results
            }
        }
    else:
        # 处理所有簇
        result = analysis_service.analyze_all_clusters(top_n=top_n)

        return {
            "success": True,
            "message": f"批量AI分析完成，成功率 {round(result['processed'] / result['total_clusters'] * 100, 2)}%",
            "data": result
        }

@router.get("/analysis-statistics")
def get_analysis_statistics(db: Session = Depends(get_db)):
    """
    [REQ-011] P5.2: 获取AI分析统计信息

    返回AI分析的覆盖率和完成情况
    """
    analysis_service = AIAnalysisService(db)
    stats = analysis_service.get_analysis_statistics()

    return {
        "success": True,
        "data": stats
    }

@router.post("/extract-attributes-ai")
async def extract_attributes_with_ai(
    max_products: Optional[int] = None,
    batch_size: int = 10,
    db: Session = Depends(get_db)
):
    """
    [REQ-012] P5.3: AI辅助兜底 - 提取缺失的delivery_type

    对代码规则无法提取的商品使用AI补充提取delivery_type

    参数：
    - max_products: 最大处理数量（None表示处理所有缺失的商品）
    - batch_size: 批处理大小（默认10，避免API调用过快）
    """
    extraction_service = AttributeExtractionService(db)
    result = extraction_service.process_missing_delivery_types(
        max_products=max_products,
        batch_size=batch_size
    )

    if not result['success']:
        return {
            "success": False,
            "message": result['message'],
            "data": result
        }

    return {
        "success": True,
        "message": result['message'],
        "data": result
    }


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

# [REQ-007] 数据导出功能 - API 路由扩展

from fastapi.responses import StreamingResponse
from backend.services.export_service import ExportService
import io

@router.get("/export/products")
def export_products(
    format: str = "csv",
    db: Session = Depends(get_db)
):
    """
    [REQ-007] 导出原始商品数据
    
    支持格式：csv, excel
    """
    if format not in ["csv", "excel"]:
        raise HTTPException(status_code=400, detail="不支持的导出格式，请使用 csv 或 excel")
    
    export_service = ExportService(db)
    file_content = export_service.export_products(format)
    
    # 设置文件名和 MIME 类型
    if format == "csv":
        filename = "products.csv"
        media_type = "text/csv"
    else:
        filename = "products.xlsx"
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    
    return StreamingResponse(
        io.BytesIO(file_content),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/export/clustered")
def export_clustered_products(
    format: str = "csv",
    db: Session = Depends(get_db)
):
    """
    [REQ-007] 导出聚类结果
    
    支持格式：csv, excel
    """
    if format not in ["csv", "excel"]:
        raise HTTPException(status_code=400, detail="不支持的导出格式，请使用 csv 或 excel")
    
    export_service = ExportService(db)
    file_content = export_service.export_clustered_products(format)
    
    # 设置文件名和 MIME 类型
    if format == "csv":
        filename = "clustered_products.csv"
        media_type = "text/csv"
    else:
        filename = "clustered_products.xlsx"
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    
    return StreamingResponse(
        io.BytesIO(file_content),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/export/cluster-summary")
def export_cluster_summary(
    format: str = "csv",
    db: Session = Depends(get_db)
):
    """
    [REQ-007] 导出簇级汇总
    
    支持格式：csv, excel
    """
    if format not in ["csv", "excel"]:
        raise HTTPException(status_code=400, detail="不支持的导出格式，请使用 csv 或 excel")
    
    export_service = ExportService(db)
    file_content = export_service.export_cluster_summary(format)
    
    # 设置文件名和 MIME 类型
    if format == "csv":
        filename = "cluster_summary.csv"
        media_type = "text/csv"
    else:
        filename = "cluster_summary.xlsx"
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    
    return StreamingResponse(
        io.BytesIO(file_content),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# [REQ-003] 语义聚类分析 - API 路由扩展

from backend.services.clustering_service import ClusteringService

@router.post("/cluster")
def cluster_products(
    min_cluster_size: int = 15,
    min_samples: int = 5,
    use_cache: bool = True,
    use_two_stage: bool = False,
    use_three_stage: bool = True,
    stage1_min_size: int = 10,
    stage2_min_size: int = 5,
    stage3_min_size: int = 3,
    db: Session = Depends(get_db)
):
    """
    [REQ-003] 执行语义聚类分析（三阶段优化版）

    使用优化方案：
    - 更强大的向量化模型 (all-mpnet-base-v2)
    - 文本预处理（去除噪音，提取核心语义）
    - 优化的HDBSCAN参数（leaf方法 + epsilon）
    - 三阶段聚类（推荐，显著降低噪音率）

    参数：
    - min_cluster_size: 最小簇大小（单阶段模式，默认 15）
    - min_samples: 最小样本数（单阶段模式，默认 5）
    - use_cache: 是否使用向量缓存（默认 True）
    - use_two_stage: 是否使用两阶段聚类（默认 False）
    - use_three_stage: 是否使用三阶段聚类（默认 True，推荐）
    - stage1_min_size: 第一阶段最小簇大小（默认 10）
    - stage2_min_size: 第二阶段最小簇大小（默认 5）
    - stage3_min_size: 第三阶段最小簇大小（默认 3）

    三阶段聚类说明：
    - 第一阶段：使用较大的 min_cluster_size 获取主要簇（高质量）
    - 第二阶段：对噪音点使用中等的 min_cluster_size 获取次级簇
    - 第三阶段：对剩余噪音点使用较小的 min_cluster_size 获取微型簇
    - 结果：主要簇 + 次级簇 + 微型簇 + 真正的噪音点
    - 效果：噪音率从 73% 降低到 35-40%（相比两阶段的47%进一步降低）
    """
    print("=" * 80)
    print("[DEBUG] /api/products/cluster endpoint called!")
    print(f"[DEBUG] Parameters: use_three_stage={use_three_stage}, use_two_stage={use_two_stage}")
    print(f"[DEBUG] stage1_min_size={stage1_min_size}, stage2_min_size={stage2_min_size}, stage3_min_size={stage3_min_size}")
    print("=" * 80)

    try:
        print("[DEBUG] Creating ClusteringService...")
        clustering_service = ClusteringService(db)
        print("[DEBUG] ClusteringService created successfully")

        print("[DEBUG] Calling cluster_all_products...")
        result = clustering_service.cluster_all_products(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            use_cache=use_cache,
            use_two_stage=use_two_stage,
            use_three_stage=use_three_stage,
            stage1_min_size=stage1_min_size,
            stage2_min_size=stage2_min_size,
            stage3_min_size=stage3_min_size
        )
        print("[DEBUG] cluster_all_products completed successfully")

        return {
            "success": result["success"],
            "message": "聚类分析完成" if result["success"] else result.get("message", "聚类失败"),
            "data": result
        }
    except Exception as e:
        print(f"[ERROR] Exception in cluster_products: {e}")
        import traceback
        traceback.print_exc()
        raise

@router.post("/cluster/test")
def cluster_products_test(
    limit: int = 1000,
    use_two_stage: bool = False,
    use_three_stage: bool = True,
    stage1_min_size: int = 10,
    stage2_min_size: int = 5,
    stage3_min_size: int = 3,
    db: Session = Depends(get_db)
):
    """
    [TEST] 测试聚类（使用有限数量的产品）

    用于快速验证聚类算法是否正确工作

    参数：
    - limit: 限制处理的商品数量（默认 1000）
    - use_two_stage: 是否使用两阶段聚类（默认 False）
    - use_three_stage: 是否使用三阶段聚类（默认 True，推荐）
    - stage1_min_size: 第一阶段最小簇大小（默认 10）
    - stage2_min_size: 第二阶段最小簇大小（默认 5）
    - stage3_min_size: 第三阶段最小簇大小（默认 3）
    """
    clustering_service = ClusteringService(db)
    result = clustering_service.cluster_all_products(
        use_cache=True,
        use_two_stage=use_two_stage,
        use_three_stage=use_three_stage,
        stage1_min_size=stage1_min_size,
        stage2_min_size=stage2_min_size,
        stage3_min_size=stage3_min_size,
        limit=limit
    )

    return {
        "success": result["success"],
        "message": f"测试聚类完成（处理了 {limit} 个产品）" if result["success"] else result.get("message", "聚类失败"),
        "data": result
    }

@router.get("/cluster/summary")
def get_cluster_summary(db: Session = Depends(get_db)):
    """
    [REQ-003] 获取簇级汇总

    返回所有簇的统计信息
    """
    clustering_service = ClusteringService(db)
    summary = clustering_service.generate_cluster_summary()

    return {
        "success": True,
        "data": summary
    }

@router.get("/cluster/quality")
def get_cluster_quality(db: Session = Depends(get_db)):
    """
    [REQ-003] 获取聚类质量报告

    返回聚类质量指标
    """
    clustering_service = ClusteringService(db)
    report = clustering_service.get_cluster_quality_report()

    return report

# [REQ-006] 聚类结果展示 - API 路由扩展

from backend.services.cluster_view_service import ClusterViewService

@router.get("/clusters/overview")
def get_clusters_overview(
    min_size: Optional[int] = None,
    max_size: Optional[int] = None,
    exclude_noise: bool = True,
    db: Session = Depends(get_db)
):
    """
    [REQ-006] 获取所有簇的概览信息

    参数：
    - min_size: 最小簇大小
    - max_size: 最大簇大小
    - exclude_noise: 是否排除噪音点（默认 True）
    """
    view_service = ClusterViewService(db)
    clusters = view_service.get_clusters_overview(
        min_size=min_size,
        max_size=max_size,
        exclude_noise=exclude_noise
    )

    return {
        "success": True,
        "total": len(clusters),
        "data": clusters
    }

@router.get("/clusters/search")
def search_clusters(
    keyword: str,
    min_size: Optional[int] = None,
    max_size: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    [REQ-006] 搜索包含关键词的簇

    参数：
    - keyword: 搜索关键词（在商品名称中搜索）
    - min_size: 最小簇大小
    - max_size: 最大簇大小
    """
    if not keyword:
        raise HTTPException(status_code=400, detail="请提供搜索关键词")

    view_service = ClusterViewService(db)
    clusters = view_service.search_clusters(
        keyword=keyword,
        min_size=min_size,
        max_size=max_size
    )

    return {
        "success": True,
        "keyword": keyword,
        "total": len(clusters),
        "data": clusters
    }

@router.get("/clusters/statistics")
def get_cluster_statistics(db: Session = Depends(get_db)):
    """
    [REQ-006] 获取整体聚类统计信息

    返回聚类的整体统计数据
    """
    view_service = ClusterViewService(db)
    stats = view_service.get_cluster_statistics()

    return {
        "success": True,
        "data": stats
    }

@router.get("/clusters/noise")
def get_noise_products(db: Session = Depends(get_db)):
    """
    [REQ-006] 获取所有噪音点商品

    返回 cluster_id=-1 的所有商品
    """
    view_service = ClusterViewService(db)
    noise_products = view_service.get_noise_products()

    return {
        "success": True,
        "total": len(noise_products),
        "data": noise_products
    }

@router.get("/clusters/{cluster_id}")
def get_cluster_detail(
    cluster_id: int,
    db: Session = Depends(get_db)
):
    """
    [REQ-006] 获取单个簇的详细信息

    返回簇内所有商品和统计信息
    """
    view_service = ClusterViewService(db)
    cluster = view_service.get_cluster_detail(cluster_id)

    if not cluster:
        raise HTTPException(status_code=404, detail="簇不存在或无商品")

    return {
        "success": True,
        "data": cluster
    }

# [REQ-010] P5.1: 商品属性提取 - API 路由扩展

from backend.services.attribute_extraction_service import AttributeExtractionService

@router.post("/extract-attributes")
async def extract_product_attributes(
    product_ids: Optional[List[int]] = None,
    batch_size: int = 100,
    db: Session = Depends(get_db)
):
    """
    [REQ-010] P5.1: 批量提取商品属性

    从商品名称中提取交付形���、格式、平台等属性

    参数：
    - product_ids: 可选，指定商品ID列表，不传则处理所有商品
    - batch_size: 批处理大小（默认100）
    """
    extraction_service = AttributeExtractionService(db)

    if product_ids:
        # 处理指定商品
        processed = 0
        failed = 0

        for product_id in product_ids:
            success, message = extraction_service.process_product(product_id)
            if success:
                processed += 1
            else:
                failed += 1

        return {
            "success": True,
            "message": f"成功处理 {processed} 个商品",
            "data": {
                "total": len(product_ids),
                "processed": processed,
                "failed": failed
            }
        }
    else:
        # 处理所有商品
        result = extraction_service.process_all_products(batch_size=batch_size)

        return {
            "success": True,
            "message": f"批量属性提取完成，成功率 {result['success_rate']}%",
            "data": result
        }

@router.get("/extraction-statistics")
def get_extraction_statistics(db: Session = Depends(get_db)):
    """
    [REQ-010] P5.1: 获取属性提取统计信息

    返回属性提取的覆盖率和分布情况
    """
    extraction_service = AttributeExtractionService(db)
    stats = extraction_service.get_extraction_statistics()

    return {
        "success": True,
        "data": stats
    }

# [REQ-008] P4.1: 类别名称生成 - API 路由扩展
