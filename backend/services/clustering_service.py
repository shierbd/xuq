"""
[REQ-003] 语义聚类分析 - 聚类服务
使用 Sentence Transformers + HDBSCAN 进行语义聚类
优化版本：使用 all-mpnet-base-v2 模型 + 文本预处理
"""
import os
import pickle
import hashlib
import re
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from sentence_transformers import SentenceTransformer
import hdbscan
import numpy as np
from backend.models.product import Product


class ClusteringService:
    """[REQ-003] 语义聚类服务"""

    def __init__(self, db: Session, model_name: str = "all-mpnet-base-v2"):
        self.db = db
        self.model_name = model_name
        self.model = None
        self.cache_dir = "data/cache/embeddings"
        os.makedirs(self.cache_dir, exist_ok=True)

        # 强制设置离线模式（在初始化时就设置，避免网络请求）
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
        os.environ['HF_HUB_OFFLINE'] = '1'
        os.environ['HF_DATASETS_OFFLINE'] = '1'

        # 配置国内镜像和代理（作为备选）
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
            print("Loading from local cache (offline mode)...")

            try:
                self.model = SentenceTransformer(self.model_name)
                print("Model loaded successfully from local cache!")
            except Exception as e:
                print(f"Failed to load model: {e}")
                raise Exception(
                    "Failed to load model from local cache. Please check:\n"
                    "1. Model exists in cache: ~/.cache/huggingface/hub/\n"
                    "2. Model name is correct: all-mpnet-base-v2\n"
                    f"3. Error details: {str(e)}"
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

    def preprocess_text(self, text: str) -> str:
        """
        预处理商品名称文本

        清洗步骤：
        1. 转小写
        2. 去除特殊字符
        3. 去除尺寸信息
        4. 去除常见停用词
        5. 清理多余空格
        """
        if not text:
            return ""

        # 1. 转小写
        text = text.lower()

        # 2. 去除特殊字符（保留字母、数字、空格）
        text = re.sub(r'[|/\\()\[\]{}<>]', ' ', text)

        # 3. 去除尺寸信息
        text = re.sub(r'\d+x\d+', '', text)  # 8x10, 5x7
        text = re.sub(r'\d+\s*(mm|cm|inch|in|ft|px)', '', text)  # 50mm, 8in

        # 4. 去除常见停用词（只移除真正的噪音词，保留产品类型标识符）
        # 保留: template, digital, printable, editable（这些是重要的产品类型词）
        stop_words = [
            'instant', 'download',  # 时效性词汇
            'file', 'files',  # 格式词汇
        ]
        for word in stop_words:
            text = re.sub(rf'\b{word}\b', '', text, flags=re.IGNORECASE)

        # 5. 清理多余空格
        text = ' '.join(text.split())

        return text.strip()

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

        # 创建固定大小的列表，用None占位
        embeddings = [None] * len(products)
        product_ids = []
        texts_to_encode = []
        indices_to_encode = []

        for i, product in enumerate(products):
            product_ids.append(product.product_id)

            # 预处理商品名称
            processed_name = self.preprocess_text(product.product_name)

            if use_cache:
                cache_key = self._get_cache_key(processed_name)
                cached_embedding = self._load_from_cache(cache_key)

                if cached_embedding is not None:
                    embeddings[i] = cached_embedding
                else:
                    texts_to_encode.append(processed_name)
                    indices_to_encode.append(i)
            else:
                texts_to_encode.append(processed_name)
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

            # 放到正确的位置
            for idx, embedding in zip(indices_to_encode, new_embeddings):
                embeddings[idx] = embedding

        # 调试：检查是否有 None 值
        none_count = sum(1 for e in embeddings if e is None)
        if none_count > 0:
            print(f"WARNING: Found {none_count} None values in embeddings!")
            # 找出哪些索引是 None
            none_indices = [i for i, e in enumerate(embeddings) if e is None]
            print(f"None indices: {none_indices[:10]}...")  # 只打印前10个

        # 调试：检查形状
        if embeddings:
            shapes = set()
            for i, e in enumerate(embeddings):
                if e is not None:
                    if isinstance(e, np.ndarray):
                        shapes.add(e.shape)
                    else:
                        print(f"WARNING: embeddings[{i}] is not ndarray, type: {type(e)}")
            print(f"Unique embedding shapes: {shapes}")

        return np.array(embeddings), product_ids

    def perform_clustering(
        self,
        embeddings: np.ndarray,
        min_cluster_size: int = 8,
        min_samples: int = 3,
        metric: str = 'euclidean',
        normalize: bool = True  # ✅ 新增：是否归一化（用于模拟 cosine 距离）
    ) -> np.ndarray:
        """
        执行 HDBSCAN 聚类（优化版）

        Args:
            embeddings: 向量矩阵
            min_cluster_size: 最小簇大小
            min_samples: 最小样本数
            metric: 距离度量
            normalize: 是否对向量进行 L2 归一化（归一化后的 euclidean 等价于 cosine）

        Returns:
            cluster_labels: 聚类标签数组
        """
        from sklearn.preprocessing import normalize as sklearn_normalize

        # ✅ 对文本向量进行 L2 归一化（等价于使用 cosine 距离）
        if normalize:
            print(f"Normalizing embeddings (L2 norm) for cosine-equivalent distance...")
            embeddings = sklearn_normalize(embeddings, norm='l2')

        print(f"Performing HDBSCAN clustering (optimized)...")
        print(f"  min_cluster_size: {min_cluster_size}")
        print(f"  min_samples: {min_samples}")
        print(f"  metric: {metric} {'(with L2 normalization → cosine-equivalent)' if normalize else ''}")
        print(f"  cluster_selection_method: leaf")
        print(f"  cluster_selection_epsilon: 0.3")

        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            metric=metric,
            cluster_selection_method='leaf',  # 使用leaf方法（更激进，减少噪点）
            cluster_selection_epsilon=0.3,     # 允许距离在0.3内的簇合并
            core_dist_n_jobs=-1                # 使用所有CPU核心加速
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

    def perform_two_stage_clustering(
        self,
        embeddings: np.ndarray,
        product_ids: List[int],
        stage1_min_size: int = 10,
        stage2_min_size: int = 5
    ) -> Tuple[np.ndarray, Dict]:
        """
        执行两阶段聚类

        第一阶段：使用较大的 min_cluster_size 获取主要簇
        第二阶段：对噪音点使用较小的 min_cluster_size 获取次级簇

        Args:
            embeddings: 向量矩阵
            product_ids: 产品ID列表
            stage1_min_size: 第一阶段最小簇大小
            stage2_min_size: 第二阶段最小簇大小

        Returns:
            (final_labels, cluster_types): 最终聚类标签和簇类型字典
        """
        print("\n" + "="*60)
        print("[TWO-STAGE CLUSTERING] Starting two-stage clustering")
        print("="*60)

        # ============ 第一阶段 ============
        print(f"\n[STAGE 1] Primary clustering (min_cluster_size={stage1_min_size})")
        print("-" * 60)

        stage1_labels = self.perform_clustering(
            embeddings,
            min_cluster_size=stage1_min_size,
            min_samples=max(3, stage1_min_size // 2)
        )

        # 统计第一阶段结果
        stage1_clusters = set(stage1_labels) - {-1}
        stage1_noise_mask = stage1_labels == -1
        stage1_noise_count = np.sum(stage1_noise_mask)

        print(f"\n[STAGE 1 RESULTS]:")
        print(f"  Primary clusters: {len(stage1_clusters)}")
        print(f"  Noise points: {stage1_noise_count}")
        print(f"  Noise ratio: {stage1_noise_count / len(stage1_labels) * 100:.2f}%")

        # ============ 第二阶段 ============
        if stage1_noise_count > 0:
            print(f"\n[STAGE 2] Secondary clustering (min_cluster_size={stage2_min_size})")
            print("-" * 60)

            # 提取噪音点的向量
            noise_embeddings = embeddings[stage1_noise_mask]
            noise_indices = np.where(stage1_noise_mask)[0]

            print(f"对 {len(noise_embeddings)} 个噪音点进行二次聚类...")

            # 对噪音点重新聚类
            stage2_labels = self.perform_clustering(
                noise_embeddings,
                min_cluster_size=stage2_min_size,
                min_samples=max(2, stage2_min_size // 2)
            )

            # 统计第二阶段结果
            stage2_clusters = set(stage2_labels) - {-1}
            stage2_noise_count = np.sum(stage2_labels == -1)

            print(f"\n[STAGE 2 RESULTS]:")
            print(f"  Secondary clusters: {len(stage2_clusters)}")
            print(f"  Remaining noise: {stage2_noise_count}")
            print(f"  Noise ratio: {stage2_noise_count / len(stage2_labels) * 100:.2f}%")

            # ============ 合并结果 ============
            print(f"\n[MERGING] Merging two-stage results")
            print("-" * 60)

            # 创建最终标签数组
            final_labels = stage1_labels.copy()

            # 为第二阶段的簇分配新的ID（从第一阶段最大ID+1开始）
            max_stage1_id = max(stage1_labels) if len(stage1_labels) > 0 else -1
            next_cluster_id = max_stage1_id + 1

            # 更新噪音点的标签
            for i, noise_idx in enumerate(noise_indices):
                if stage2_labels[i] != -1:
                    # 这是一个次级簇，分配新ID
                    final_labels[noise_idx] = next_cluster_id + stage2_labels[i]
                # 否则保持为 -1（真正的噪音点）

            # 统计簇类型
            cluster_types = {}

            # 主要簇（第一阶段）
            for cluster_id in stage1_clusters:
                cluster_size = np.sum(final_labels == cluster_id)
                cluster_types[int(cluster_id)] = {
                    'type': 'primary',
                    'size': int(cluster_size),
                    'stage': 1
                }

            # 次级簇（第二阶段）
            for cluster_id in stage2_clusters:
                final_cluster_id = next_cluster_id + cluster_id
                cluster_size = np.sum(final_labels == final_cluster_id)
                cluster_types[int(final_cluster_id)] = {
                    'type': 'secondary',
                    'size': int(cluster_size),
                    'stage': 2
                }

        else:
            print("\n[STAGE 1 COMPLETE] No noise points, skipping stage 2")
            final_labels = stage1_labels
            cluster_types = {}
            for cluster_id in stage1_clusters:
                cluster_size = np.sum(final_labels == cluster_id)
                cluster_types[int(cluster_id)] = {
                    'type': 'primary',
                    'size': int(cluster_size),
                    'stage': 1
                }

        # ============ 最终统计 ============
        print("\n" + "="*60)
        print("[FINAL RESULTS] Two-stage clustering summary")
        print("="*60)

        final_clusters = set(final_labels) - {-1}
        final_noise_count = np.sum(final_labels == -1)
        primary_clusters = [cid for cid, info in cluster_types.items() if info['type'] == 'primary']
        secondary_clusters = [cid for cid, info in cluster_types.items() if info['type'] == 'secondary']

        print(f"\nOverall statistics:")
        print(f"  Total clusters: {len(final_clusters)}")
        print(f"    - Primary clusters (>={stage1_min_size} products): {len(primary_clusters)}")
        print(f"    - Secondary clusters ({stage2_min_size}-{stage1_min_size-1} products): {len(secondary_clusters)}")
        print(f"  Final noise points: {final_noise_count}")
        print(f"  Final noise ratio: {final_noise_count / len(final_labels) * 100:.2f}%")
        print(f"  Noise reduction: {stage1_noise_count - final_noise_count} products re-clustered")

        print("\n" + "="*60)

        return final_labels, cluster_types

    def perform_three_stage_clustering(
        self,
        embeddings: np.ndarray,
        product_ids: List[int],
        stage1_min_size: int = 10,
        stage2_min_size: int = 5,
        stage3_min_size: int = 3
    ) -> Tuple[np.ndarray, Dict]:
        """
        执行三阶段聚类

        第一阶段：使用较大的 min_cluster_size 获取主要簇
        第二阶段：对噪音点使用中等的 min_cluster_size 获取次级簇
        第三阶段：对剩余噪音点使用较小的 min_cluster_size 获取微型簇

        Args:
            embeddings: 向量矩阵
            product_ids: 产品ID列表
            stage1_min_size: 第一阶段最小簇大小
            stage2_min_size: 第二阶段最小簇大小
            stage3_min_size: 第三阶段最小簇大小

        Returns:
            (final_labels, cluster_types): 最终聚类标签和簇类型字典
        """
        print("\n" + "="*60)
        print("[THREE-STAGE CLUSTERING] Starting three-stage clustering")
        print("="*60)

        # ============ 第一阶段 ============
        print(f"\n[STAGE 1] Primary clustering (min_cluster_size={stage1_min_size})")
        print("-" * 60)

        stage1_labels = self.perform_clustering(
            embeddings,
            min_cluster_size=stage1_min_size,
            min_samples=max(3, stage1_min_size // 2)
        )

        stage1_clusters = set(stage1_labels) - {-1}
        stage1_noise_mask = stage1_labels == -1
        stage1_noise_count = np.sum(stage1_noise_mask)

        print(f"\n[STAGE 1 RESULTS]:")
        print(f"  Primary clusters: {len(stage1_clusters)}")
        print(f"  Noise points: {stage1_noise_count}")
        print(f"  Noise ratio: {stage1_noise_count / len(stage1_labels) * 100:.2f}%")

        # ============ 第二阶段 ============
        final_labels = stage1_labels.copy()
        cluster_types = {}

        # 记录主要簇
        for cluster_id in stage1_clusters:
            cluster_size = np.sum(final_labels == cluster_id)
            cluster_types[int(cluster_id)] = {
                'type': 'primary',
                'size': int(cluster_size),
                'stage': 1
            }

        if stage1_noise_count > 0:
            print(f"\n[STAGE 2] Secondary clustering (min_cluster_size={stage2_min_size})")
            print("-" * 60)

            noise_embeddings = embeddings[stage1_noise_mask]
            noise_indices = np.where(stage1_noise_mask)[0]

            print(f"Processing {len(noise_embeddings)} noise points from stage 1...")

            stage2_labels = self.perform_clustering(
                noise_embeddings,
                min_cluster_size=stage2_min_size,
                min_samples=max(2, stage2_min_size // 2)
            )

            stage2_clusters = set(stage2_labels) - {-1}
            stage2_noise_mask = stage2_labels == -1
            stage2_noise_count = np.sum(stage2_noise_mask)

            print(f"\n[STAGE 2 RESULTS]:")
            print(f"  Secondary clusters: {len(stage2_clusters)}")
            print(f"  Remaining noise: {stage2_noise_count}")
            print(f"  Noise ratio: {stage2_noise_count / len(stage2_labels) * 100:.2f}%")

            # 分配次级簇ID
            max_stage1_id = max(stage1_labels) if len(stage1_labels) > 0 else -1
            next_cluster_id = max_stage1_id + 1

            for i, noise_idx in enumerate(noise_indices):
                if stage2_labels[i] != -1:
                    final_labels[noise_idx] = next_cluster_id + stage2_labels[i]

            # 记录次级簇
            for cluster_id in stage2_clusters:
                final_cluster_id = next_cluster_id + cluster_id
                cluster_size = np.sum(final_labels == final_cluster_id)
                cluster_types[int(final_cluster_id)] = {
                    'type': 'secondary',
                    'size': int(cluster_size),
                    'stage': 2
                }

            # ============ 第三阶段 ============
            if stage2_noise_count > 0:
                print(f"\n[STAGE 3] Micro clustering (min_cluster_size={stage3_min_size})")
                print("-" * 60)

                # 获取第二阶段的噪音点
                stage2_noise_indices_in_original = noise_indices[stage2_noise_mask]
                stage2_noise_embeddings = embeddings[stage2_noise_indices_in_original]

                print(f"Processing {len(stage2_noise_embeddings)} noise points from stage 2...")

                stage3_labels = self.perform_clustering(
                    stage2_noise_embeddings,
                    min_cluster_size=stage3_min_size,
                    min_samples=max(2, stage3_min_size // 2)
                )

                stage3_clusters = set(stage3_labels) - {-1}
                stage3_noise_count = np.sum(stage3_labels == -1)

                print(f"\n[STAGE 3 RESULTS]:")
                print(f"  Micro clusters: {len(stage3_clusters)}")
                print(f"  Final noise: {stage3_noise_count}")
                print(f"  Noise ratio: {stage3_noise_count / len(stage3_labels) * 100:.2f}%")

                # 分配微型簇ID
                max_stage2_id = max(final_labels) if len(final_labels) > 0 else -1
                next_cluster_id_stage3 = max_stage2_id + 1

                for i, noise_idx in enumerate(stage2_noise_indices_in_original):
                    if stage3_labels[i] != -1:
                        final_labels[noise_idx] = next_cluster_id_stage3 + stage3_labels[i]

                # 记录微型簇
                for cluster_id in stage3_clusters:
                    final_cluster_id = next_cluster_id_stage3 + cluster_id
                    cluster_size = np.sum(final_labels == final_cluster_id)
                    cluster_types[int(final_cluster_id)] = {
                        'type': 'micro',
                        'size': int(cluster_size),
                        'stage': 3
                    }

        # ============ 最终统计 ============
        print("\n" + "="*60)
        print("[FINAL RESULTS] Three-stage clustering summary")
        print("="*60)

        final_clusters = set(final_labels) - {-1}
        final_noise_count = np.sum(final_labels == -1)
        primary_clusters = [cid for cid, info in cluster_types.items() if info['type'] == 'primary']
        secondary_clusters = [cid for cid, info in cluster_types.items() if info['type'] == 'secondary']
        micro_clusters = [cid for cid, info in cluster_types.items() if info.get('type') == 'micro']

        print(f"\nOverall statistics:")
        print(f"  Total clusters: {len(final_clusters)}")
        print(f"    - Primary clusters (>={stage1_min_size} products): {len(primary_clusters)}")
        print(f"    - Secondary clusters ({stage2_min_size}-{stage1_min_size-1} products): {len(secondary_clusters)}")
        print(f"    - Micro clusters ({stage3_min_size}-{stage2_min_size-1} products): {len(micro_clusters)}")
        print(f"  Final noise points: {final_noise_count}")
        print(f"  Final noise ratio: {final_noise_count / len(final_labels) * 100:.2f}%")
        print(f"  Noise reduction: {stage1_noise_count - final_noise_count} products re-clustered")

        print("\n" + "="*60)

        return final_labels, cluster_types

    def cluster_all_products(
        self,
        min_cluster_size: int = 8,
        min_samples: int = 3,
        use_cache: bool = True,
        use_two_stage: bool = False,
        use_three_stage: bool = True,
        stage1_min_size: int = 10,
        stage2_min_size: int = 5,
        stage3_min_size: int = 3,
        limit: int = None
    ) -> Dict:
        """
        对所有商品进行聚类

        Args:
            min_cluster_size: 最小簇大小（单阶段模式）
            min_samples: 最小样本数（单阶段模式）
            use_cache: 是否使用缓存
            use_two_stage: 是否使用两阶段聚类
            use_three_stage: 是否使用三阶段聚类（推荐）
            stage1_min_size: 第一阶段最小簇大小
            stage2_min_size: 第二阶段最小簇大小
            stage3_min_size: 第三阶段最小簇大小
            limit: 限制处理的商品数量（用于测试，None表示处理所有）

        Returns:
            聚类结果统计
        """
        # 查询所有未删除的商品
        query = self.db.query(Product).filter(
            Product.is_deleted == False
        )

        if limit is not None:
            query = query.limit(limit)

        products = query.all()

        if not products:
            return {
                "success": False,
                "message": "没有可聚类的商品"
            }

        print(f"Found {len(products)} products to cluster")
        print(f"DEBUG: use_three_stage={use_three_stage}, use_two_stage={use_two_stage}")
        print(f"DEBUG: stage1_min_size={stage1_min_size}, stage2_min_size={stage2_min_size}, stage3_min_size={stage3_min_size}")

        # 向量化
        embeddings, product_ids = self.vectorize_products(products, use_cache)

        # 选择聚类模式
        if use_three_stage:
            # 三阶段聚类（推荐）
            print(f"DEBUG: Using three-stage clustering")
            cluster_labels, cluster_types = self.perform_three_stage_clustering(
                embeddings,
                product_ids,
                stage1_min_size=stage1_min_size,
                stage2_min_size=stage2_min_size,
                stage3_min_size=stage3_min_size
            )
        elif use_two_stage:
            # 两阶段聚类
            print(f"DEBUG: Using two-stage clustering")
            cluster_labels, cluster_types = self.perform_two_stage_clustering(
                embeddings,
                product_ids,
                stage1_min_size=stage1_min_size,
                stage2_min_size=stage2_min_size
            )
        else:
            # 单阶段聚类
            print(f"DEBUG: Using single-stage clustering")
            cluster_labels = self.perform_clustering(
                embeddings,
                min_cluster_size=min_cluster_size,
                min_samples=min_samples
            )
            cluster_types = {}

        # 更新数据库
        print("\nUpdating database...")
        for product_id, cluster_id in zip(product_ids, cluster_labels):
            product = self.db.query(Product).filter(
                Product.product_id == product_id
            ).first()

            if product:
                product.cluster_id = int(cluster_id)

                # 如果使用多阶段聚类，添加簇类型标记
                if (use_three_stage or use_two_stage) and cluster_id != -1:
                    cluster_info = cluster_types.get(int(cluster_id), {})
                    cluster_type = cluster_info.get('type', 'unknown')

                    # 设置簇类型
                    if cluster_type == 'primary':
                        product.cluster_type = 'primary'  # 主要簇
                    elif cluster_type == 'secondary':
                        product.cluster_type = 'secondary'  # 次级簇
                    elif cluster_type == 'micro':
                        product.cluster_type = 'micro'  # 微型簇
                else:
                    product.cluster_type = None

        self.db.commit()
        print("[DATABASE] Database updated successfully")

        # 生成统计信息
        n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
        n_noise = list(cluster_labels).count(-1)

        result = {
            "success": True,
            "total_products": len(products),
            "n_clusters": n_clusters,
            "n_noise": n_noise,
            "noise_ratio": n_noise / len(products) * 100
        }

        # 如果使用多阶段聚类，添加详细统计
        if use_three_stage:
            primary_clusters = [cid for cid, info in cluster_types.items() if info['type'] == 'primary']
            secondary_clusters = [cid for cid, info in cluster_types.items() if info['type'] == 'secondary']
            micro_clusters = [cid for cid, info in cluster_types.items() if info.get('type') == 'micro']

            result.update({
                "clustering_mode": "three_stage",
                "n_primary_clusters": len(primary_clusters),
                "n_secondary_clusters": len(secondary_clusters),
                "n_micro_clusters": len(micro_clusters),
                "stage1_min_size": stage1_min_size,
                "stage2_min_size": stage2_min_size,
                "stage3_min_size": stage3_min_size,
                "cluster_types": cluster_types
            })
        elif use_two_stage:
            primary_clusters = [cid for cid, info in cluster_types.items() if info['type'] == 'primary']
            secondary_clusters = [cid for cid, info in cluster_types.items() if info['type'] == 'secondary']

            result.update({
                "clustering_mode": "two_stage",
                "n_primary_clusters": len(primary_clusters),
                "n_secondary_clusters": len(secondary_clusters),
                "stage1_min_size": stage1_min_size,
                "stage2_min_size": stage2_min_size,
                "cluster_types": cluster_types
            })
        else:
            result["clustering_mode"] = "single_stage"

        return result

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

# Trigger reload at 1769804077.8539455
