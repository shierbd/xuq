"""
[REQ-003] 语义聚类分析 - 聚类服务
使用 Sentence Transformers + HDBSCAN 进行语义聚类
"""
import os
import pickle
import hashlib
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from sentence_transformers import SentenceTransformer
import hdbscan
import numpy as np
from backend.models.product import Product


class ClusteringService:
    """[REQ-003] 语义聚类服务"""

    def __init__(self, db: Session, model_name: str = "all-MiniLM-L6-v2"):
        self.db = db
        self.model_name = model_name
        self.model = None
        self.cache_dir = "data/cache/embeddings"
        os.makedirs(self.cache_dir, exist_ok=True)

        # 配置国内镜像和代理
        self._setup_mirror_and_proxy()

    def _setup_mirror_and_proxy(self):
        """配置国内镜像源和代理"""
        # 直接设置代理环境变量（优先使用代理）
        os.environ['HTTP_PROXY'] = 'http://127.0.0.1:1080'
        os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:1080'
        os.environ['http_proxy'] = 'http://127.0.0.1:1080'
        os.environ['https_proxy'] = 'http://127.0.0.1:1080'

        # 设置 HuggingFace 镜像（作为备选）
        os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

        print(f"Proxy configured: http://127.0.0.1:1080")
        print(f"HuggingFace mirror: {os.environ.get('HF_ENDPOINT')}")

    def load_model(self):
        """加载 Sentence Transformers 模型"""
        if self.model is None:
            print(f"Loading model: {self.model_name}...")
            print("Using proxy: http://127.0.0.1:1080")

            try:
                self.model = SentenceTransformer(self.model_name)
                print("Model loaded successfully!")
            except Exception as e:
                print(f"Failed to load model: {e}")
                raise Exception(
                    "Failed to load model. Please check:\n"
                    "1. Proxy is running on port 1080\n"
                    "2. Network connection is available\n"
                    "3. Or manually download the model to ~/.cache/torch/sentence_transformers/"
                )
        return self.model

    def _get_cache_key(self, text: str) -> str:
        """生成缓存键（MD5 哈希）"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def _get_cache_path(self, cache_key: str) -> str:
        """获取缓存文件路径"""
        return os.path.join(self.cache_dir, f"{cache_key}.pkl")

    def _load_from_cache(self, cache_key: str) -> Optional[np.ndarray]:
        """从缓存加载向量"""
        cache_path = self._get_cache_path(cache_key)
        if os.path.exists(cache_path):
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        return None

    def _save_to_cache(self, cache_key: str, embedding: np.ndarray):
        """保存向量到缓存"""
        cache_path = self._get_cache_path(cache_key)
        with open(cache_path, 'wb') as f:
            pickle.dump(embedding, f)

    def vectorize_products(
        self,
        products: List[Product],
        use_cache: bool = True
    ) -> Tuple[np.ndarray, List[int]]:
        """
        向量化商品名称

        Args:
            products: 商品列表
            use_cache: 是否使用缓存

        Returns:
            (embeddings, product_ids): 向量矩阵和商品 ID 列表
        """
        self.load_model()

        embeddings = []
        product_ids = []
        texts_to_encode = []
        indices_to_encode = []

        for i, product in enumerate(products):
            product_ids.append(product.product_id)

            if use_cache:
                cache_key = self._get_cache_key(product.product_name)
                cached_embedding = self._load_from_cache(cache_key)

                if cached_embedding is not None:
                    embeddings.append(cached_embedding)
                else:
                    texts_to_encode.append(product.product_name)
                    indices_to_encode.append(i)
            else:
                texts_to_encode.append(product.product_name)
                indices_to_encode.append(i)

        # 批量编码未缓存的文本
        if texts_to_encode:
            print(f"Encoding {len(texts_to_encode)} new products...")
            new_embeddings = self.model.encode(
                texts_to_encode,
                show_progress_bar=True,
                batch_size=32
            )

            # 保存到缓存
            if use_cache:
                for text, embedding in zip(texts_to_encode, new_embeddings):
                    cache_key = self._get_cache_key(text)
                    self._save_to_cache(cache_key, embedding)

            # 插入到正确的位置
            for idx, embedding in zip(indices_to_encode, new_embeddings):
                embeddings.insert(idx, embedding)

        return np.array(embeddings), product_ids

    def perform_clustering(
        self,
        embeddings: np.ndarray,
        min_cluster_size: int = 8,
        min_samples: int = 3,
        metric: str = 'euclidean'
    ) -> np.ndarray:
        """
        执行 HDBSCAN 聚类

        Args:
            embeddings: 向量矩阵
            min_cluster_size: 最小簇大小
            min_samples: 最小样本数
            metric: 距离度量

        Returns:
            cluster_labels: 聚类标签数组
        """
        print(f"Performing HDBSCAN clustering...")
        print(f"  min_cluster_size: {min_cluster_size}")
        print(f"  min_samples: {min_samples}")
        print(f"  metric: {metric}")

        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            metric=metric,
            cluster_selection_method='eom'
        )

        cluster_labels = clusterer.fit_predict(embeddings)

        # 统计聚类结果
        n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
        n_noise = list(cluster_labels).count(-1)

        print(f"Clustering completed:")
        print(f"  Total clusters: {n_clusters}")
        print(f"  Noise points: {n_noise}")
        print(f"  Noise ratio: {n_noise / len(cluster_labels) * 100:.2f}%")

        return cluster_labels

    def cluster_all_products(
        self,
        min_cluster_size: int = 8,
        min_samples: int = 3,
        use_cache: bool = True
    ) -> Dict:
        """
        对所有商品进行聚类

        Args:
            min_cluster_size: 最小簇大小
            min_samples: 最小样本数
            use_cache: 是否使用缓存

        Returns:
            聚类结果统计
        """
        # 查询所有未删除的商品
        products = self.db.query(Product).filter(
            Product.is_deleted == False
        ).all()

        if not products:
            return {
                "success": False,
                "message": "没有可聚类的商品"
            }

        print(f"Found {len(products)} products to cluster")

        # 向量化
        embeddings, product_ids = self.vectorize_products(products, use_cache)

        # 聚类
        cluster_labels = self.perform_clustering(
            embeddings,
            min_cluster_size=min_cluster_size,
            min_samples=min_samples
        )

        # 更新数据库
        print("Updating database...")
        for product_id, cluster_id in zip(product_ids, cluster_labels):
            product = self.db.query(Product).filter(
                Product.product_id == product_id
            ).first()

            if product:
                product.cluster_id = int(cluster_id)

        self.db.commit()
        print("Database updated successfully")

        # 生成统计信息
        n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
        n_noise = list(cluster_labels).count(-1)

        return {
            "success": True,
            "total_products": len(products),
            "n_clusters": n_clusters,
            "n_noise": n_noise,
            "noise_ratio": n_noise / len(products) * 100
        }

    def generate_cluster_summary(self) -> List[Dict]:
        """
        生成簇级汇总

        Returns:
            簇级统计信息列表
        """
        # 查询已聚类的商品
        products = self.db.query(Product).filter(
            Product.is_deleted == False,
            Product.cluster_id.isnot(None)
        ).all()

        # 按簇分组统计
        cluster_data = {}
        for product in products:
            cluster_id = product.cluster_id
            if cluster_id not in cluster_data:
                cluster_data[cluster_id] = {
                    'cluster_id': cluster_id,
                    'cluster_name': product.cluster_name,  # 添加类别名称（英文）
                    'cluster_name_cn': product.cluster_name_cn,  # 添加类别名称（中文）
                    'cluster_size': 0,
                    'ratings': [],
                    'prices': [],
                    'total_reviews': 0,
                    'example_products': []
                }

            cluster_data[cluster_id]['cluster_size'] += 1

            if product.rating:
                cluster_data[cluster_id]['ratings'].append(product.rating)

            if product.price:
                cluster_data[cluster_id]['prices'].append(product.price)

            if product.review_count:
                cluster_data[cluster_id]['total_reviews'] += product.review_count

            # 保存前5个商品作为示例
            if len(cluster_data[cluster_id]['example_products']) < 5:
                cluster_data[cluster_id]['example_products'].append(product.product_name)

        # 计算统计值
        summary = []
        for cluster_id, data in cluster_data.items():
            summary.append({
                'cluster_id': cluster_id,
                'cluster_name': data['cluster_name'],  # 添加类别名称（英文）
                'cluster_name_cn': data['cluster_name_cn'],  # 添加类别名称（中文）
                'cluster_size': data['cluster_size'],
                'avg_rating': sum(data['ratings']) / len(data['ratings']) if data['ratings'] else None,
                'avg_price': sum(data['prices']) / len(data['prices']) if data['prices'] else None,
                'total_reviews': data['total_reviews'],
                'example_products': data['example_products']
            })

        # 按簇大小排序
        summary.sort(key=lambda x: x['cluster_size'], reverse=True)

        return summary

    def get_cluster_quality_report(self) -> Dict:
        """
        获取聚类质量报告

        Returns:
            质量指标字典
        """
        # 查询所有已聚类的商品
        products = self.db.query(Product).filter(
            Product.is_deleted == False,
            Product.cluster_id.isnot(None)
        ).all()

        if not products:
            return {
                "success": False,
                "message": "没有聚类结果"
            }

        cluster_labels = [p.cluster_id for p in products]

        # 统计指标
        n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
        n_noise = cluster_labels.count(-1)
        n_total = len(cluster_labels)

        # 簇大小分布
        cluster_sizes = {}
        for label in cluster_labels:
            if label != -1:
                cluster_sizes[label] = cluster_sizes.get(label, 0) + 1

        sizes = list(cluster_sizes.values())

        return {
            "success": True,
            "total_products": n_total,
            "n_clusters": n_clusters,
            "n_noise": n_noise,
            "noise_ratio": n_noise / n_total * 100,
            "avg_cluster_size": sum(sizes) / len(sizes) if sizes else 0,
            "min_cluster_size": min(sizes) if sizes else 0,
            "max_cluster_size": max(sizes) if sizes else 0,
            "cluster_size_distribution": cluster_sizes
        }
