"""
分层聚类服务 - 多层聚类策略
使用不同参数对不同层级的数据进行聚类，以提高覆盖率
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


class HierarchicalClusteringService:
    """分层聚类服务"""

    def __init__(self, db: Session, model_name: str = "all-mpnet-base-v2"):
        self.db = db
        self.model_name = model_name
        self.model = None

        # 根据模型名称使用不同的缓存目录
        if "mpnet" in model_name.lower():
            self.cache_dir = "data/cache/embeddings_mpnet"
        else:
            self.cache_dir = "data/cache/embeddings"

        os.makedirs(self.cache_dir, exist_ok=True)

        # 配置国内镜像和代理
        self._setup_mirror_and_proxy()

    def _setup_mirror_and_proxy(self):
        """配置国内镜像源和代理"""
        # 优先使用国内镜像（已验证可用）
        os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

        # 代理配置（可选，如果镜像不可用时启用）
        # os.environ['HTTP_PROXY'] = 'http://127.0.0.1:1080'
        # os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:1080'
        # os.environ['http_proxy'] = 'http://127.0.0.1:1080'
        # os.environ['https_proxy'] = 'http://127.0.0.1:1080'

    def load_model(self):
        """加载 Sentence Transformers 模型"""
        if self.model is None:
            print(f"Loading model: {self.model_name}...")
            try:
                self.model = SentenceTransformer(self.model_name)
                print("Model loaded successfully!")
            except Exception as e:
                print(f"Failed to load model: {e}")
                raise
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
        """向量化商品名称"""
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
        """执行 HDBSCAN 聚类"""
        print(f"  Performing HDBSCAN clustering...")
        print(f"    min_cluster_size: {min_cluster_size}")
        print(f"    min_samples: {min_samples}")
        print(f"    metric: {metric}")

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

        print(f"  Clustering completed:")
        print(f"    Total clusters: {n_clusters}")
        print(f"    Noise points: {n_noise}")
        print(f"    Noise ratio: {n_noise / len(cluster_labels) * 100:.2f}%")

        return cluster_labels

    def hierarchical_cluster_all_products(
        self,
        layer_configs: List[Dict] = None,
        use_cache: bool = True
    ) -> Dict:
        """
        分层聚类所有商品

        Args:
            layer_configs: 每层的配置，格式:
                [
                    {"min_cluster_size": 20, "min_samples": 5, "name": "主流类别"},
                    {"min_cluster_size": 8, "min_samples": 3, "name": "小众类别"},
                    {"min_cluster_size": 5, "min_samples": 2, "name": "长尾类别"}
                ]
            use_cache: 是否使用缓存

        Returns:
            聚类结果统计
        """
        # 默认配置
        if layer_configs is None:
            layer_configs = [
                {"min_cluster_size": 20, "min_samples": 5, "name": "第一层(主流类别)"},
                {"min_cluster_size": 8, "min_samples": 3, "name": "第二层(小众类别)"},
                {"min_cluster_size": 5, "min_samples": 2, "name": "第三层(长尾类别)"}
            ]

        print('=' * 70)
        print('开始分层聚类')
        print('=' * 70)
        print()
        print(f'总层数: {len(layer_configs)}')
        for i, config in enumerate(layer_configs, 1):
            print(f'  第{i}层: {config["name"]}')
            print(f'    min_cluster_size: {config["min_cluster_size"]}')
            print(f'    min_samples: {config["min_samples"]}')
        print()

        # 查询所有未删除的商品
        all_products = self.db.query(Product).filter(
            Product.is_deleted == False
        ).all()

        if not all_products:
            return {
                "success": False,
                "message": "没有可聚类的商品"
            }

        print(f"商品总数: {len(all_products)}")
        print()

        # 向量化所有商品（只做一次）
        print("向量化所有商品...")
        all_embeddings, all_product_ids = self.vectorize_products(all_products, use_cache)
        print(f"向量化完成: {len(all_embeddings)} 个商品")
        print()

        # 创建商品ID到索引的映射
        product_id_to_idx = {pid: idx for idx, pid in enumerate(all_product_ids)}

        # 初始化所有商品的cluster_id为-1（噪音点）
        cluster_assignments = {pid: -1 for pid in all_product_ids}

        # 用于分配全局唯一的cluster_id
        next_cluster_id = 0

        # 记录每层的统计信息
        layer_stats = []

        # 待聚类的商品（初始为所有商品）
        remaining_product_ids = set(all_product_ids)

        # 逐层聚类
        for layer_idx, config in enumerate(layer_configs):
            print('=' * 70)
            print(f'执行 {config["name"]}')
            print('=' * 70)
            print()

            if not remaining_product_ids:
                print("没有剩余商品需要聚类，跳过此层")
                print()
                continue

            print(f"待聚类商品数: {len(remaining_product_ids)}")

            # 获取待聚类商品的向量
            remaining_indices = [product_id_to_idx[pid] for pid in remaining_product_ids]
            remaining_embeddings = all_embeddings[remaining_indices]
            remaining_ids_list = list(remaining_product_ids)

            # 执行聚类
            cluster_labels = self.perform_clustering(
                remaining_embeddings,
                min_cluster_size=config["min_cluster_size"],
                min_samples=config["min_samples"]
            )

            # 统计本层结果
            n_clusters_this_layer = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
            n_noise_this_layer = list(cluster_labels).count(-1)
            n_clustered_this_layer = len(cluster_labels) - n_noise_this_layer

            # 分配全局cluster_id
            # 创建本层cluster_id到全局cluster_id的映射
            local_to_global = {}
            for local_id in set(cluster_labels):
                if local_id != -1:
                    local_to_global[local_id] = next_cluster_id
                    next_cluster_id += 1

            # 更新cluster_assignments
            for i, local_cluster_id in enumerate(cluster_labels):
                product_id = remaining_ids_list[i]
                if local_cluster_id != -1:
                    global_cluster_id = local_to_global[local_cluster_id]
                    cluster_assignments[product_id] = global_cluster_id
                    remaining_product_ids.discard(product_id)

            # 记录本层统计
            layer_stats.append({
                "layer": layer_idx + 1,
                "name": config["name"],
                "input_products": len(remaining_ids_list),
                "n_clusters": n_clusters_this_layer,
                "clustered_products": n_clustered_this_layer,
                "noise_products": n_noise_this_layer,
                "noise_ratio": n_noise_this_layer / len(remaining_ids_list) * 100 if remaining_ids_list else 0
            })

            print()
            print(f"本层统计:")
            print(f"  输入商品: {len(remaining_ids_list)}")
            print(f"  生成簇数: {n_clusters_this_layer}")
            print(f"  已聚类: {n_clustered_this_layer}")
            print(f"  噪音点: {n_noise_this_layer}")
            print(f"  本层噪音率: {n_noise_this_layer / len(remaining_ids_list) * 100:.2f}%")
            print(f"  剩余待聚类: {len(remaining_product_ids)}")
            print()

        # 更新数据库
        print('=' * 70)
        print("更新数据库...")
        print('=' * 70)
        for product_id, cluster_id in cluster_assignments.items():
            product = self.db.query(Product).filter(
                Product.product_id == product_id
            ).first()
            if product:
                product.cluster_id = int(cluster_id)

        self.db.commit()
        print("数据库更新完成")
        print()

        # 生成总体统计
        total_clustered = sum([cluster_id != -1 for cluster_id in cluster_assignments.values()])
        total_noise = len(cluster_assignments) - total_clustered
        total_clusters = next_cluster_id

        print('=' * 70)
        print('分层聚类完成！')
        print('=' * 70)
        print()
        print("总体统计:")
        print(f"  商品总数: {len(all_products)}")
        print(f"  总簇数: {total_clusters}")
        print(f"  已聚类商品: {total_clustered} ({total_clustered / len(all_products) * 100:.2f}%)")
        print(f"  噪音点: {total_noise} ({total_noise / len(all_products) * 100:.2f}%)")
        print()

        print("各层统计:")
        for stat in layer_stats:
            print(f"  {stat['name']}:")
            print(f"    输入: {stat['input_products']} 商品")
            print(f"    输出: {stat['n_clusters']} 簇, {stat['clustered_products']} 已聚类, {stat['noise_products']} 噪音")
            print(f"    本层噪音率: {stat['noise_ratio']:.2f}%")

        return {
            "success": True,
            "total_products": len(all_products),
            "total_clusters": total_clusters,
            "clustered_products": total_clustered,
            "noise_products": total_noise,
            "clustering_rate": total_clustered / len(all_products) * 100,
            "noise_ratio": total_noise / len(all_products) * 100,
            "layer_stats": layer_stats,
            "embeddings": all_embeddings,
            "product_ids": all_product_ids,
            "cluster_assignments": cluster_assignments
        }

    def post_assign_noise_points(
        self,
        embeddings: np.ndarray,
        product_ids: List[int],
        cluster_assignments: Dict[int, int],
        similarity_threshold: float = 0.7
    ) -> Dict:
        """
        噪音点后分配：将噪音点分配到最近的簇

        Args:
            embeddings: 所有商品的向量
            product_ids: 商品ID列表
            cluster_assignments: 当前的簇分配 {product_id: cluster_id}
            similarity_threshold: 相似度阈值（余弦相似度）

        Returns:
            后分配统计信息
        """
        print('=' * 70)
        print('开始噪音点后分配')
        print('=' * 70)
        print()
        print(f'相似度阈值: {similarity_threshold}')
        print()

        # 创建商品ID到索引的映射
        product_id_to_idx = {pid: idx for idx, pid in enumerate(product_ids)}

        # 找出所有噪音点
        noise_point_ids = [pid for pid, cid in cluster_assignments.items() if cid == -1]
        print(f'噪音点数量: {len(noise_point_ids)}')

        if not noise_point_ids:
            print('没有噪音点需要处理')
            return {
                "success": True,
                "assigned_count": 0,
                "remaining_noise": 0
            }

        # 找出所有已聚类的点，按簇分组
        cluster_points = {}
        for pid, cid in cluster_assignments.items():
            if cid != -1:
                if cid not in cluster_points:
                    cluster_points[cid] = []
                cluster_points[cid].append(pid)

        print(f'已有簇数量: {len(cluster_points)}')
        print()

        # 计算每个簇的中心向量
        print('计算簇中心向量...')
        cluster_centers = {}
        for cluster_id, point_ids in cluster_points.items():
            indices = [product_id_to_idx[pid] for pid in point_ids]
            cluster_embeddings = embeddings[indices]
            cluster_centers[cluster_id] = np.mean(cluster_embeddings, axis=0)

        print(f'簇中心计算完成: {len(cluster_centers)} 个簇')
        print()

        # 对每个噪音点，找到最近的簇
        print('开始分配噪音点...')
        assigned_count = 0
        assignment_details = []

        for noise_pid in noise_point_ids:
            noise_idx = product_id_to_idx[noise_pid]
            noise_embedding = embeddings[noise_idx]

            # 计算与所有簇中心的余弦相似度
            max_similarity = -1
            best_cluster_id = -1

            for cluster_id, center in cluster_centers.items():
                # 余弦相似度
                similarity = np.dot(noise_embedding, center) / (
                    np.linalg.norm(noise_embedding) * np.linalg.norm(center)
                )

                if similarity > max_similarity:
                    max_similarity = similarity
                    best_cluster_id = cluster_id

            # 如果相似度超过阈值，分配到该簇
            if max_similarity >= similarity_threshold:
                cluster_assignments[noise_pid] = best_cluster_id
                assigned_count += 1
                assignment_details.append({
                    "product_id": noise_pid,
                    "cluster_id": best_cluster_id,
                    "similarity": max_similarity
                })

        print(f'后分配完成:')
        print(f'  成功分配: {assigned_count} 个噪音点')
        print(f'  剩余噪音: {len(noise_point_ids) - assigned_count} 个')
        print(f'  分配率: {assigned_count / len(noise_point_ids) * 100:.2f}%')
        print()

        # 更新数据库
        print('更新数据库...')
        for detail in assignment_details:
            product = self.db.query(Product).filter(
                Product.product_id == detail["product_id"]
            ).first()
            if product:
                product.cluster_id = int(detail["cluster_id"])

        self.db.commit()
        print('数据库更新完成')
        print()

        return {
            "success": True,
            "assigned_count": assigned_count,
            "remaining_noise": len(noise_point_ids) - assigned_count,
            "assignment_rate": assigned_count / len(noise_point_ids) * 100,
            "assignment_details": assignment_details
        }
