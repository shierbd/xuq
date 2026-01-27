"""
[REQ-006] 聚类结果展示 - 查询服务
提供聚类结果的查询和展示功能
"""
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from backend.models.product import Product


class ClusterViewService:
    """[REQ-006] 聚类结果展示服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_clusters_overview(
        self,
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
        exclude_noise: bool = True
    ) -> List[Dict]:
        """
        获取所有簇的概览信息

        Args:
            min_size: 最小簇大小
            max_size: 最大簇大小
            exclude_noise: 是否排除噪音点（cluster_id=-1）

        Returns:
            簇概览列表
        """
        # 查询已聚类的商品
        query = self.db.query(Product).filter(
            Product.is_deleted == False,
            Product.cluster_id.isnot(None)
        )

        # 排除噪音点
        if exclude_noise:
            query = query.filter(Product.cluster_id != -1)

        products = query.all()

        # 按簇分组统计
        cluster_data = {}
        for product in products:
            cluster_id = product.cluster_id
            if cluster_id not in cluster_data:
                cluster_data[cluster_id] = {
                    'cluster_id': cluster_id,
                    'cluster_size': 0,
                    'ratings': [],
                    'prices': [],
                    'total_reviews': 0,
                    'products': []
                }

            cluster_data[cluster_id]['cluster_size'] += 1

            if product.rating:
                cluster_data[cluster_id]['ratings'].append(product.rating)

            if product.price:
                cluster_data[cluster_id]['prices'].append(product.price)

            if product.review_count:
                cluster_data[cluster_id]['total_reviews'] += product.review_count

            cluster_data[cluster_id]['products'].append({
                'product_id': product.product_id,
                'product_name': product.product_name,
                'rating': product.rating,
                'review_count': product.review_count,
                'price': product.price
            })

        # 计算统计值并筛选
        clusters = []
        for cluster_id, data in cluster_data.items():
            # 应用大小筛选
            if min_size and data['cluster_size'] < min_size:
                continue
            if max_size and data['cluster_size'] > max_size:
                continue

            cluster_info = {
                'cluster_id': cluster_id,
                'cluster_size': data['cluster_size'],
                'avg_rating': sum(data['ratings']) / len(data['ratings']) if data['ratings'] else None,
                'min_rating': min(data['ratings']) if data['ratings'] else None,
                'max_rating': max(data['ratings']) if data['ratings'] else None,
                'avg_price': sum(data['prices']) / len(data['prices']) if data['prices'] else None,
                'min_price': min(data['prices']) if data['prices'] else None,
                'max_price': max(data['prices']) if data['prices'] else None,
                'total_reviews': data['total_reviews'],
                'top_products': sorted(
                    data['products'],
                    key=lambda x: x['review_count'] or 0,
                    reverse=True
                )[:5]  # 前5个最受欢迎的商品
            }
            clusters.append(cluster_info)

        # 按簇大小排序
        clusters.sort(key=lambda x: x['cluster_size'], reverse=True)

        return clusters

    def get_cluster_detail(self, cluster_id: int) -> Optional[Dict]:
        """
        获取单个簇的详细信息

        Args:
            cluster_id: 簇 ID

        Returns:
            簇详细信息
        """
        # 查询该簇的所有商品
        products = self.db.query(Product).filter(
            Product.is_deleted == False,
            Product.cluster_id == cluster_id
        ).all()

        if not products:
            return None

        # 统计信息
        ratings = [p.rating for p in products if p.rating]
        prices = [p.price for p in products if p.price]
        review_counts = [p.review_count for p in products if p.review_count]

        # 商品列表
        product_list = []
        for product in products:
            product_list.append({
                'product_id': product.product_id,
                'product_name': product.product_name,
                'rating': product.rating,
                'review_count': product.review_count,
                'shop_name': product.shop_name,
                'price': product.price,
                'delivery_type': product.delivery_type,
                'delivery_format': product.delivery_format,
                'delivery_platform': product.delivery_platform,
                'import_time': product.import_time.isoformat() if product.import_time else None
            })

        # 按评价数排序
        product_list.sort(key=lambda x: x['review_count'] or 0, reverse=True)

        return {
            'cluster_id': cluster_id,
            'cluster_size': len(products),
            'statistics': {
                'avg_rating': sum(ratings) / len(ratings) if ratings else None,
                'min_rating': min(ratings) if ratings else None,
                'max_rating': max(ratings) if ratings else None,
                'avg_price': sum(prices) / len(prices) if prices else None,
                'min_price': min(prices) if prices else None,
                'max_price': max(prices) if prices else None,
                'total_reviews': sum(review_counts),
                'avg_reviews': sum(review_counts) / len(review_counts) if review_counts else None
            },
            'products': product_list
        }

    def search_clusters(
        self,
        keyword: str,
        min_size: Optional[int] = None,
        max_size: Optional[int] = None
    ) -> List[Dict]:
        """
        搜索包含关键词的簇

        Args:
            keyword: 搜索关键词
            min_size: 最小簇大小
            max_size: 最大簇大小

        Returns:
            匹配的簇列表
        """
        # 查询包含关键词的商品
        products = self.db.query(Product).filter(
            Product.is_deleted == False,
            Product.cluster_id.isnot(None),
            Product.cluster_id != -1,
            Product.product_name.like(f"%{keyword}%")
        ).all()

        # 获取匹配的簇 ID
        cluster_ids = set(p.cluster_id for p in products)

        # 获取这些簇的完整信息
        clusters = self.get_clusters_overview(
            min_size=min_size,
            max_size=max_size,
            exclude_noise=True
        )

        # 筛选匹配的簇
        matched_clusters = [c for c in clusters if c['cluster_id'] in cluster_ids]

        # 为每个簇添加匹配的商品数量
        for cluster in matched_clusters:
            matched_count = sum(
                1 for p in products if p.cluster_id == cluster['cluster_id']
            )
            cluster['matched_products'] = matched_count

        # 按匹配商品数排序
        matched_clusters.sort(key=lambda x: x['matched_products'], reverse=True)

        return matched_clusters

    def get_cluster_statistics(self) -> Dict:
        """
        获取整体聚类统计信息

        Returns:
            统计信息字典
        """
        # 查询所有已聚类的商品
        products = self.db.query(Product).filter(
            Product.is_deleted == False,
            Product.cluster_id.isnot(None)
        ).all()

        if not products:
            return {
                'total_products': 0,
                'total_clusters': 0,
                'clustered_products': 0,
                'noise_products': 0,
                'noise_ratio': 0.0
            }

        # 统计
        cluster_ids = set(p.cluster_id for p in products)
        noise_products = [p for p in products if p.cluster_id == -1]
        clustered_products = [p for p in products if p.cluster_id != -1]

        # 簇大小分布
        cluster_sizes = {}
        for product in clustered_products:
            cluster_id = product.cluster_id
            cluster_sizes[cluster_id] = cluster_sizes.get(cluster_id, 0) + 1

        sizes = list(cluster_sizes.values())

        return {
            'total_products': len(products),
            'total_clusters': len(cluster_ids) - (1 if -1 in cluster_ids else 0),
            'clustered_products': len(clustered_products),
            'noise_products': len(noise_products),
            'noise_ratio': len(noise_products) / len(products) * 100 if products else 0.0,
            'avg_cluster_size': sum(sizes) / len(sizes) if sizes else 0.0,
            'min_cluster_size': min(sizes) if sizes else 0,
            'max_cluster_size': max(sizes) if sizes else 0,
            'cluster_size_distribution': cluster_sizes
        }

    def get_noise_products(self) -> List[Dict]:
        """
        获取所有噪音点商品

        Returns:
            噪音点商品列表
        """
        products = self.db.query(Product).filter(
            Product.is_deleted == False,
            Product.cluster_id == -1
        ).all()

        return [{
            'product_id': p.product_id,
            'product_name': p.product_name,
            'rating': p.rating,
            'review_count': p.review_count,
            'shop_name': p.shop_name,
            'price': p.price
        } for p in products]
