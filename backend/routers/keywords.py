"""
词根聚类系统 - API 路由
提供关键词数据的导入、查询、聚类等功能
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.keyword import Keyword, ClusterSummary
from typing import List, Optional, Dict
import pandas as pd
import io

router = APIRouter(prefix="/api/keywords", tags=["keywords"])


@router.post("/import")
async def import_keywords(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    导入关键词数据（CSV格式）

    支持的CSV格式：
    - merged_keywords_all.csv（SEMrush格式）
    - stageA_clusters.csv（聚类结果格式）
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="只支持CSV文件")

    try:
        # 读取CSV文件
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))

        # 检测CSV格式
        if 'Keyword' in df.columns:
            # SEMrush格式
            return await _import_semrush_format(df, db)
        elif 'keyword' in df.columns and 'cluster_id' in df.columns:
            # 聚类结果格式（格式1）
            return await _import_cluster_format(df, db)
        elif 'phrase' in df.columns and 'cluster_id_A' in df.columns:
            # 聚类结果格式（格式2：stageA_clusters.csv）
            return await _import_cluster_format_v2(df, db)
        else:
            raise HTTPException(status_code=400, detail="不支持的CSV格式")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


async def _import_semrush_format(df: pd.DataFrame, db: Session) -> Dict:
    """导入SEMrush格式的数据"""
    imported = 0
    duplicates = 0

    for _, row in df.iterrows():
        # 检查是否已存在
        existing = db.query(Keyword).filter(
            Keyword.keyword == row['Keyword'],
            Keyword.seed_word == row.get('seed_word', ''),
            Keyword.is_deleted == False
        ).first()

        if existing:
            duplicates += 1
            continue

        # 创建新记录
        keyword = Keyword(
            keyword=row['Keyword'],
            seed_word=row.get('seed_word', ''),
            seed_group=row.get('seed_group', ''),
            source=row.get('source', 'semrush'),
            intent=row.get('Intent', ''),
            volume=int(row['Volume']) if pd.notna(row.get('Volume')) else None,
            trend=row.get('Trend', ''),
            keyword_difficulty=int(row['Keyword Difficulty']) if pd.notna(row.get('Keyword Difficulty')) else None,
            cpc_usd=float(row['CPC (USD)']) if pd.notna(row.get('CPC (USD)')) else None,
            competitive_density=float(row['Competitive Density']) if pd.notna(row.get('Competitive Density')) else None,
            serp_features=row.get('SERP Features', ''),
            number_of_results=float(row['Number of Results']) if pd.notna(row.get('Number of Results')) else None,
            source_file=row.get('source_file', ''),
            word_count=len(row['Keyword'].split()),
            phrase_length=len(row['Keyword'])
        )

        db.add(keyword)
        imported += 1

    db.commit()

    return {
        "success": True,
        "message": "数据导入成功",
        "data": {
            "total": len(df),
            "imported": imported,
            "duplicates": duplicates
        }
    }


async def _import_cluster_format(df: pd.DataFrame, db: Session) -> Dict:
    """导入聚类结果格式的数据"""
    updated = 0

    for _, row in df.iterrows():
        # 查找对应的关键词记录
        keyword_obj = db.query(Keyword).filter(
            Keyword.keyword == row['keyword'],
            Keyword.is_deleted == False
        ).first()

        if keyword_obj:
            # 更新聚类信息
            keyword_obj.cluster_id_a = int(row['cluster_id']) if pd.notna(row.get('cluster_id')) else None
            keyword_obj.cluster_size = int(row['cluster_size']) if pd.notna(row.get('cluster_size')) else None
            keyword_obj.is_noise = row.get('is_noise', False)
            updated += 1

    db.commit()

    return {
        "success": True,
        "message": "聚类结果导入成功",
        "data": {
            "total": len(df),
            "updated": updated
        }
    }


async def _import_cluster_format_v2(df: pd.DataFrame, db: Session) -> Dict:
    """导入聚类结果格式的数据（stageA_clusters.csv格式）"""
    updated = 0

    for _, row in df.iterrows():
        # 查找对应的关键词记录（使用phrase列匹配keyword）
        keyword_obj = db.query(Keyword).filter(
            Keyword.keyword == row['phrase'],
            Keyword.is_deleted == False
        ).first()

        if keyword_obj:
            # 更新聚类信息
            keyword_obj.cluster_id_a = int(row['cluster_id_A']) if pd.notna(row.get('cluster_id_A')) else None
            keyword_obj.cluster_size = int(row['cluster_size']) if pd.notna(row.get('cluster_size')) else None
            keyword_obj.is_noise = row.get('is_noise', False)
            updated += 1

    db.commit()

    return {
        "success": True,
        "message": "聚类结果导入成功",
        "data": {
            "total": len(df),
            "updated": updated
        }
    }


@router.get("/")
def get_keywords(
    page: int = 1,
    page_size: int = 50,
    search: Optional[str] = None,
    seed_word: Optional[str] = None,
    cluster_id: Optional[int] = None,
    is_noise: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    获取关键词列表

    支持分页、搜索、筛选
    """
    query = db.query(Keyword).filter(Keyword.is_deleted == False)

    # 搜索
    if search:
        query = query.filter(Keyword.keyword.like(f"%{search}%"))

    # 筛选
    if seed_word:
        query = query.filter(Keyword.seed_word == seed_word)

    if cluster_id is not None:
        query = query.filter(Keyword.cluster_id_a == cluster_id)

    if is_noise is not None:
        query = query.filter(Keyword.is_noise == is_noise)

    # 总数
    total = query.count()

    # 分页
    keywords = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "success": True,
        "data": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [
                {
                    "keyword_id": k.keyword_id,
                    "keyword": k.keyword,
                    "seed_word": k.seed_word,
                    "volume": k.volume,
                    "cluster_id_a": k.cluster_id_a,
                    "cluster_size": k.cluster_size,
                    "is_noise": k.is_noise
                }
                for k in keywords
            ]
        }
    }


@router.get("/count")
def get_keyword_count(db: Session = Depends(get_db)):
    """获取关键词总数"""
    total = db.query(Keyword).filter(Keyword.is_deleted == False).count()

    return {
        "success": True,
        "data": {
            "total": total
        }
    }


@router.get("/clusters/overview")
def get_clusters_overview(
    stage: str = "A",
    min_size: Optional[int] = None,
    max_size: Optional[int] = None,
    exclude_noise: bool = True,
    db: Session = Depends(get_db)
):
    """
    获取所有簇的概览信息
    """
    # 查询关键词
    query = db.query(Keyword).filter(Keyword.is_deleted == False)

    if stage == "A":
        query = query.filter(Keyword.cluster_id_a.isnot(None))
        if exclude_noise:
            query = query.filter(Keyword.cluster_id_a != -1)
    else:
        query = query.filter(Keyword.cluster_id_b.isnot(None))
        if exclude_noise:
            query = query.filter(Keyword.cluster_id_b != -1)

    keywords = query.all()

    # 按簇分组统计
    cluster_data = {}
    for keyword in keywords:
        cluster_id = keyword.cluster_id_a if stage == "A" else keyword.cluster_id_b

        if cluster_id not in cluster_data:
            cluster_data[cluster_id] = {
                'cluster_id': cluster_id,
                'cluster_size': 0,
                'keywords': [],
                'seed_words': set(),
                'total_volume': 0
            }

        cluster_data[cluster_id]['cluster_size'] += 1
        cluster_data[cluster_id]['keywords'].append(keyword.keyword)
        cluster_data[cluster_id]['seed_words'].add(keyword.seed_word)
        if keyword.volume:
            cluster_data[cluster_id]['total_volume'] += keyword.volume

    # 筛选并格式化
    clusters = []
    for cluster_id, data in cluster_data.items():
        # 应用大小筛选
        if min_size and data['cluster_size'] < min_size:
            continue
        if max_size and data['cluster_size'] > max_size:
            continue

        clusters.append({
            'cluster_id': cluster_id,
            'cluster_size': data['cluster_size'],
            'seed_words': list(data['seed_words']),
            'top_keywords': data['keywords'][:5],
            'total_volume': data['total_volume']
        })

    # 按簇大小排序
    clusters.sort(key=lambda x: x['cluster_size'], reverse=True)

    return {
        "success": True,
        "total": len(clusters),
        "data": clusters
    }


@router.get("/clusters/{cluster_id}")
def get_cluster_detail(
    cluster_id: int,
    stage: str = "A",
    db: Session = Depends(get_db)
):
    """
    获取单个簇的详细信息
    """
    # 查询该簇的所有关键词
    if stage == "A":
        keywords = db.query(Keyword).filter(
            Keyword.is_deleted == False,
            Keyword.cluster_id_a == cluster_id
        ).all()
    else:
        keywords = db.query(Keyword).filter(
            Keyword.is_deleted == False,
            Keyword.cluster_id_b == cluster_id
        ).all()

    if not keywords:
        raise HTTPException(status_code=404, detail="簇不存在或无关键词")

    # 统计信息
    volumes = [k.volume for k in keywords if k.volume]
    seed_words = list(set(k.seed_word for k in keywords))

    return {
        "success": True,
        "data": {
            "cluster_id": cluster_id,
            "cluster_size": len(keywords),
            "seed_words": seed_words,
            "statistics": {
                "total_volume": sum(volumes) if volumes else 0,
                "avg_volume": sum(volumes) / len(volumes) if volumes else 0,
                "max_volume": max(volumes) if volumes else 0,
                "min_volume": min(volumes) if volumes else 0
            },
            "keywords": [
                {
                    "keyword_id": k.keyword_id,
                    "keyword": k.keyword,
                    "seed_word": k.seed_word,
                    "volume": k.volume,
                    "intent": k.intent
                }
                for k in sorted(keywords, key=lambda x: x.volume or 0, reverse=True)
            ]
        }
    }


@router.get("/seed-words")
def get_seed_words(db: Session = Depends(get_db)):
    """
    获取所有种子词列表
    """
    seed_words = db.query(Keyword.seed_word).filter(
        Keyword.is_deleted == False
    ).distinct().all()

    return {
        "success": True,
        "data": {
            "seed_words": [sw[0] for sw in seed_words if sw[0]]
        }
    }
