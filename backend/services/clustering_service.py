"""
[REQ-003] 语义聚类分析 - 聚类服务
使用 Sentence Transformers + HDBSCAN 进行语义聚类
优化版本：使用 all-mpnet-base-v2 模型 + 文本预处理

Phase 2 (2026-02-02): 双文本策略 + 数据驱动属性词发现
- 从初始聚类结果中自动发现属性词
- 生成 topic_text（去除属性词）用于聚类
- 保留 full_text（完整文本）用于展示和faceting
"""
import os
import pickle
import hashlib
import re
from typing import List, Dict, Tuple, Optional, Set
from collections import Counter, defaultdict
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

    def extract_keywords_from_text(self, text: str) -> List[str]:
        """
        从文本中提取关键词（单词）

        Args:
            text: 商品名称文本

        Returns:
            关键词列表
        """
        if not text:
            return []

        # 转小写
        text = text.lower()

        # 去除特殊字符，只保留字母和空格
        text = re.sub(r'[^a-z\s]', ' ', text)

        # 分词
        words = text.split()

        # 过滤短词（长度<3）和常见停用词
        common_stopwords = {
            'the', 'and', 'for', 'with', 'from', 'this', 'that',
            'are', 'was', 'were', 'been', 'have', 'has', 'had',
            'can', 'will', 'would', 'could', 'should', 'may', 'might'
        }

        keywords = [
            word for word in words
            if len(word) >= 3 and word not in common_stopwords
        ]

        return keywords

    def extract_cluster_keywords(
        self,
        cluster_labels: np.ndarray,
        product_names: List[str],
        top_n: int = 20
    ) -> Dict[int, List[Tuple[str, int]]]:
        """
        提取每个簇的关键词

        Args:
            cluster_labels: 聚类标签数组
            product_names: 商品名称列表
            top_n: 每个簇返回的top关键词数量

        Returns:
            {cluster_id: [(keyword, count), ...]}
        """
        cluster_keywords = defaultdict(Counter)

        # 统计每个簇的关键词
        for label, name in zip(cluster_labels, product_names):
            if label == -1:  # 跳过噪音点
                continue

            keywords = self.extract_keywords_from_text(name)
            cluster_keywords[int(label)].update(keywords)

        # 转换为排序列表
        result = {}
        for cluster_id, counter in cluster_keywords.items():
            result[cluster_id] = counter.most_common(top_n)

        return result

    def calculate_word_dispersion(
        self,
        cluster_keywords: Dict[int, List[Tuple[str, int]]]
    ) -> Dict[str, float]:
        """
        计算词的分散度（出现在多少个不同簇中）

        分散度 = 出现的簇数量 / 总簇数量

        Args:
            cluster_keywords: {cluster_id: [(keyword, count), ...]}

        Returns:
            {word: dispersion_score}
        """
        if not cluster_keywords:
            return {}

        # 统计每个词出现在哪些簇中
        word_clusters = defaultdict(set)

        for cluster_id, keywords in cluster_keywords.items():
            for word, count in keywords:
                word_clusters[word].add(cluster_id)

        # 计算分散度
        total_clusters = len(cluster_keywords)
        word_dispersion = {}

        for word, clusters in word_clusters.items():
            dispersion = len(clusters) / total_clusters
            word_dispersion[word] = dispersion

        return word_dispersion

    def identify_attribute_words(
        self,
        word_dispersion: Dict[str, float],
        dispersion_threshold: float = 0.3,
        min_word_length: int = 3
    ) -> Set[str]:
        """
        识别属性词（高分散度的词）

        属性词特征：
        - 出现在多个不同簇中（高分散度）
        - 通常是颜色、材质、风格、格式等修饰词

        Args:
            word_dispersion: {word: dispersion_score}
            dispersion_threshold: 分散度阈值（例如0.3表示出现在>30%的簇中）
            min_word_length: 最小词长度

        Returns:
            属性词集合
        """
        attribute_words = set()

        for word, dispersion in word_dispersion.items():
            if dispersion >= dispersion_threshold and len(word) >= min_word_length:
                attribute_words.add(word)

        return attribute_words

    def generate_topic_text(
        self,
        full_text: str,
        attribute_words: Set[str]
    ) -> str:
        """
        生成主题文本（去除属性词）

        Args:
            full_text: 完整商品名称
            attribute_words: 属性词集合

        Returns:
            主题文本（去除属性词后）
        """
        if not full_text:
            return ""

        # 转小写
        text = full_text.lower()

        # 分词
        words = text.split()

        # 去除属性词
        topic_words = [
            word for word in words
            if word.lower() not in attribute_words
        ]

        # 重新组合
        topic_text = ' '.join(topic_words)

        return topic_text.strip()

    def discover_attribute_words_from_clustering(
        self,
        cluster_labels: np.ndarray,
        product_names: List[str],
        dispersion_threshold: float = 0.3,
        top_n_keywords: int = 20,
        verbose: bool = True
    ) -> Tuple[Set[str], Dict]:
        """
        从聚类结果中自动发现属性词

        流程：
        1. 提取每个簇的关键词
        2. 计算词的分散度
        3. 识别高分散度的词作为属性词

        Args:
            cluster_labels: 聚类标签数组
            product_names: 商品名称列表
            dispersion_threshold: 分散度阈值
            top_n_keywords: 每个簇提取的top关键词数量
            verbose: 是否打印详细信息

        Returns:
            (attribute_words, analysis_data)
            - attribute_words: 属性词集合
            - analysis_data: 分析数据（用于调试和展示）
        """
        if verbose:
            print("\n" + "="*60)
            print("[ATTRIBUTE DISCOVERY] Discovering attribute words from clustering")
            print("="*60)

        # 步骤1: 提取每个簇的关键词
        if verbose:
            print(f"\n[STEP 1] Extracting keywords from each cluster...")

        cluster_keywords = self.extract_cluster_keywords(
            cluster_labels,
            product_names,
            top_n=top_n_keywords
        )

        if verbose:
            print(f"  Extracted keywords from {len(cluster_keywords)} clusters")

        # 步骤2: 计算词的分散度
        if verbose:
            print(f"\n[STEP 2] Calculating word dispersion...")

        word_dispersion = self.calculate_word_dispersion(cluster_keywords)

        if verbose:
            print(f"  Calculated dispersion for {len(word_dispersion)} unique words")

        # 步骤3: 识别属性词
        if verbose:
            print(f"\n[STEP 3] Identifying attribute words (threshold={dispersion_threshold})...")

        attribute_words = self.identify_attribute_words(
            word_dispersion,
            dispersion_threshold=dispersion_threshold
        )

        if verbose:
            print(f"  Identified {len(attribute_words)} attribute words")

            # 显示top 20高分散度的词
            sorted_words = sorted(
                word_dispersion.items(),
                key=lambda x: x[1],
                reverse=True
            )[:20]

            print(f"\n[TOP 20 HIGH-DISPERSION WORDS]:")
            for word, dispersion in sorted_words:
                is_attr = "Y" if word in attribute_words else "N"
                print(f"  [{is_attr}] {word:20s} {dispersion:.3f}")

            print(f"\n[ATTRIBUTE WORDS]:")
            print(f"  {', '.join(sorted(attribute_words))}")

        # 准备分析数据
        analysis_data = {
            'cluster_keywords': cluster_keywords,
            'word_dispersion': word_dispersion,
            'attribute_words': list(attribute_words),
            'total_clusters': len(cluster_keywords),
            'total_unique_words': len(word_dispersion),
            'n_attribute_words': len(attribute_words)
        }

        if verbose:
            print("\n" + "="*60)

        return attribute_words, analysis_data

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
        normalize: bool = True,  # 是否归一化（用于模拟 cosine 距离）
        cluster_selection_method: str = 'leaf',  # ✅ 新增：簇选择方法
        cluster_selection_epsilon: float = 0.3   # ✅ 新增：簇合并阈值
    ) -> np.ndarray:
        """
        执行 HDBSCAN 聚类（优化版）

        Args:
            embeddings: 向量矩阵
            min_cluster_size: 最小簇大小
            min_samples: 最小样本数
            metric: 距离度量
            normalize: 是否对向量进行 L2 归一化（归一化后的 euclidean 等价于 cosine）
            cluster_selection_method: 簇选择方法 ('eom' 保守, 'leaf' 激进)
            cluster_selection_epsilon: 簇合并阈值

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
        print(f"  cluster_selection_method: {cluster_selection_method}")  # ✅ 显示实际使用的方法
        print(f"  cluster_selection_epsilon: {cluster_selection_epsilon}")

        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            metric=metric,
            cluster_selection_method=cluster_selection_method,  # ✅ 使用参数
            cluster_selection_epsilon=cluster_selection_epsilon,  # ✅ 使用参数
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

        # ✅ Stage 1 使用 eom（保守，生成稳定的主题簇）
        stage1_labels = self.perform_clustering(
            embeddings,
            min_cluster_size=stage1_min_size,
            min_samples=max(3, stage1_min_size // 2),
            cluster_selection_method='eom',  # ✅ 使用 eom（保守）
            cluster_selection_epsilon=0.0    # ✅ 关闭 epsilon
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

    def perform_three_stage_clustering_with_merge(
        self,
        embeddings: np.ndarray,
        product_ids: List[int],
        stage1_min_size: int = 10,
        merge_threshold: float = 0.5,
        min_cohesion: float = 0.5,
        min_separation: float = 0.3,
        min_cluster_size: int = 3,
        verbose: bool = True
    ) -> Tuple[np.ndarray, Dict]:
        """
        执行三阶段聚类（Stage 2/3 重新设计版本）

        第一阶段：使用较大的 min_cluster_size 获取主要簇
        第二阶段：归并噪音点到最近的主题簇（不创建新簇）
        第三阶段：质量门控（只保留高质量簇）

        Args:
            embeddings: 向量矩阵
            product_ids: 产品ID列表
            stage1_min_size: 第一阶段最小簇大小
            merge_threshold: Stage 2 归并相似度阈值 (0-1)
            min_cohesion: Stage 3 最小簇内一致性
            min_separation: Stage 3 最小簇区分度
            min_cluster_size: Stage 3 最小簇大小
            verbose: 是否打印详细信息

        Returns:
            (final_labels, cluster_info): 最终聚类标签和簇信息字典
        """
        if verbose:
            print("\n" + "="*80)
            print("[THREE-STAGE CLUSTERING V2] Stage 2/3 Redesign with Merge Strategy")
            print("="*80)

        # ============ 第一阶段：主要聚类 ============
        if verbose:
            print(f"\n[STAGE 1] Primary clustering (min_cluster_size={stage1_min_size})")
            print("-" * 80)

        stage1_labels = self.perform_clustering(
            embeddings,
            min_cluster_size=stage1_min_size,
            min_samples=max(3, stage1_min_size // 2),
            cluster_selection_method='eom',
            cluster_selection_epsilon=0.0
        )

        stage1_clusters = set(stage1_labels) - {-1}
        stage1_noise_count = np.sum(stage1_labels == -1)

        if verbose:
            print(f"\n[STAGE 1 RESULTS]:")
            print(f"  Primary clusters: {len(stage1_clusters)}")
            print(f"  Noise points: {stage1_noise_count}")
            print(f"  Noise ratio: {stage1_noise_count / len(stage1_labels) * 100:.2f}%")

        # ============ 第二阶段：归并策略 ============
        if verbose:
            print(f"\n[STAGE 2] Merge Strategy (threshold={merge_threshold})")
            print("-" * 80)

        # 计算簇中心
        centroids = self.calculate_cluster_centroids(embeddings, stage1_labels)

        # 归并噪音点到最近的簇
        stage2_labels = self.merge_noise_to_clusters(
            embeddings,
            stage1_labels,
            centroids,
            threshold=merge_threshold,
            verbose=verbose
        )

        stage2_noise_count = np.sum(stage2_labels == -1)

        if verbose:
            merged_count = stage1_noise_count - stage2_noise_count
            print(f"\n[STAGE 2 RESULTS]:")
            print(f"  Merged to clusters: {merged_count}")
            print(f"  Remaining noise: {stage2_noise_count}")
            print(f"  Merge rate: {merged_count / stage1_noise_count * 100:.1f}%")

        # ============ 第三阶段：质量门控 ============
        if verbose:
            print(f"\n[STAGE 3] Quality Gate")
            print("-" * 80)
            print(f"  Min cohesion: {min_cohesion}")
            print(f"  Min separation: {min_separation}")
            print(f"  Min cluster size: {min_cluster_size}")

        # 应用质量门控
        final_labels = self.apply_quality_gate(
            embeddings,
            stage2_labels,
            min_size=min_cluster_size,
            min_cohesion=min_cohesion,
            min_separation=min_separation,
            verbose=verbose
        )

        # ============ 最终统计 ============
        if verbose:
            print("\n" + "="*80)
            print("[FINAL RESULTS] Three-stage clustering summary (V2)")
            print("="*80)

        final_clusters = set(final_labels) - {-1}
        final_noise_count = np.sum(final_labels == -1)

        # 生成簇信息
        cluster_info = {}
        for cluster_id in final_clusters:
            cluster_mask = final_labels == cluster_id
            cluster_size = np.sum(cluster_mask)
            cluster_info[int(cluster_id)] = {
                'type': 'high_quality',
                'size': int(cluster_size),
                'stage': 'final'
            }

        if verbose:
            print(f"\nOverall statistics:")
            print(f"  Total clusters: {len(final_clusters)}")
            print(f"  Final noise points: {final_noise_count}")
            print(f"  Final noise ratio: {final_noise_count / len(final_labels) * 100:.2f}%")
            print(f"  Cluster reduction: {len(stage1_clusters)} -> {len(final_clusters)}")
            print(f"  Noise reduction: {stage1_noise_count} -> {final_noise_count}")
            print("\n" + "="*80)

        return final_labels, cluster_info

    def calculate_cluster_centroids(
        self,
        embeddings: np.ndarray,
        labels: np.ndarray
    ) -> Dict[int, np.ndarray]:
        """
        计算每个簇的中心向量（质心）

        Args:
            embeddings: 向量矩阵
            labels: 聚类标签

        Returns:
            {cluster_id: centroid_vector}
        """
        centroids = {}
        unique_labels = set(labels) - {-1}

        for label in unique_labels:
            cluster_mask = labels == label
            cluster_points = embeddings[cluster_mask]
            centroid = np.mean(cluster_points, axis=0)
            centroids[int(label)] = centroid

        return centroids

    def merge_noise_to_clusters(
        self,
        embeddings: np.ndarray,
        labels: np.ndarray,
        centroids: Dict[int, np.ndarray],
        threshold: float = 0.5,
        verbose: bool = True
    ) -> np.ndarray:
        """
        将噪音点归并到最近的簇（Stage 2 归并策略）

        Args:
            embeddings: 向量矩阵
            labels: 聚类标签
            centroids: 簇中心字典
            threshold: 相似度阈值（0-1）
            verbose: 是否打印详细信息

        Returns:
            新的聚类标签
        """
        from sklearn.metrics.pairwise import cosine_similarity

        if verbose:
            print("\n[MERGE STRATEGY] Merging noise points to nearest clusters")
            print(f"  Threshold: {threshold}")

        new_labels = labels.copy()
        noise_mask = labels == -1
        noise_indices = np.where(noise_mask)[0]
        noise_count = len(noise_indices)

        if noise_count == 0:
            if verbose:
                print("  No noise points to merge")
            return new_labels

        merged_count = 0

        for idx in noise_indices:
            noise_point = embeddings[idx].reshape(1, -1)

            # 计算与所有簇中心的相似度
            max_sim = -1
            best_cluster = -1

            for cluster_id, centroid in centroids.items():
                centroid_reshaped = centroid.reshape(1, -1)
                sim = cosine_similarity(noise_point, centroid_reshaped)[0][0]

                if sim > max_sim:
                    max_sim = sim
                    best_cluster = cluster_id

            # 如果相似度足够高，归并
            if max_sim > threshold:
                new_labels[idx] = best_cluster
                merged_count += 1

        if verbose:
            print(f"  Noise points: {noise_count}")
            print(f"  Merged: {merged_count} ({merged_count/noise_count*100:.1f}%)")
            print(f"  Remaining noise: {noise_count - merged_count}")

        return new_labels

    def calculate_cohesion(self, cluster_points: np.ndarray) -> float:
        """
        计算簇内一致性（平均相似度）

        Args:
            cluster_points: 簇内所有点的向量

        Returns:
            一致性分数（0-1）
        """
        from sklearn.metrics.pairwise import cosine_similarity

        n = len(cluster_points)
        if n < 2:
            return 0.0

        # 计算所有点对之间的相似度
        similarities = []
        for i in range(n):
            for j in range(i+1, n):
                point_i = cluster_points[i].reshape(1, -1)
                point_j = cluster_points[j].reshape(1, -1)
                sim = cosine_similarity(point_i, point_j)[0][0]
                similarities.append(sim)

        return np.mean(similarities)

    def calculate_separation(
        self,
        cluster_centroid: np.ndarray,
        all_centroids: List[np.ndarray]
    ) -> float:
        """
        计算簇区分度（与最近簇的距离）

        Args:
            cluster_centroid: 当前簇的中心
            all_centroids: 所有簇的中心列表

        Returns:
            区分度分数（0-1）
        """
        from sklearn.metrics.pairwise import cosine_similarity

        # 计算与所有其他簇中心的距离
        distances = []
        centroid_reshaped = cluster_centroid.reshape(1, -1)

        for other_centroid in all_centroids:
            if not np.array_equal(cluster_centroid, other_centroid):
                other_reshaped = other_centroid.reshape(1, -1)
                sim = cosine_similarity(centroid_reshaped, other_reshaped)[0][0]
                dist = 1 - sim  # 距离 = 1 - 相似度
                distances.append(dist)

        # 返回最近距离（最小距离）
        return min(distances) if distances else 1.0

    def apply_quality_gate(
        self,
        embeddings: np.ndarray,
        labels: np.ndarray,
        min_size: int = 3,
        min_cohesion: float = 0.5,
        min_separation: float = 0.3,
        verbose: bool = True
    ) -> np.ndarray:
        """
        应用质量门控，淘汰低质量簇（Stage 3 质量门控）

        Args:
            embeddings: 向量矩阵
            labels: 聚类标签
            min_size: 最小簇大小
            min_cohesion: 最小簇内一致性
            min_separation: 最小簇区分度
            verbose: 是否打印详细信息

        Returns:
            新的聚类标签
        """
        if verbose:
            print("\n[QUALITY GATE] Filtering low-quality clusters")
            print(f"  Min size: {min_size}")
            print(f"  Min cohesion: {min_cohesion}")
            print(f"  Min separation: {min_separation}")

        new_labels = labels.copy()
        unique_labels = set(labels) - {-1}
        initial_cluster_count = len(unique_labels)

        # 计算所有簇中心
        centroids = self.calculate_cluster_centroids(embeddings, labels)
        all_centroids = list(centroids.values())

        rejected_clusters = []

        for cluster_id in unique_labels:
            cluster_mask = labels == cluster_id
            cluster_points = embeddings[cluster_mask]
            cluster_size = len(cluster_points)

            # 检查簇大小
            if cluster_size < min_size:
                new_labels[cluster_mask] = -1
                rejected_clusters.append((cluster_id, "size_too_small", cluster_size))
                continue

            # 检查簇内一致性
            cohesion = self.calculate_cohesion(cluster_points)
            if cohesion < min_cohesion:
                new_labels[cluster_mask] = -1
                rejected_clusters.append((cluster_id, "low_cohesion", cohesion))
                continue

            # 检查簇区分度
            separation = self.calculate_separation(centroids[cluster_id], all_centroids)
            if separation < min_separation:
                new_labels[cluster_mask] = -1
                rejected_clusters.append((cluster_id, "low_separation", separation))
                continue

        final_cluster_count = len(set(new_labels) - {-1})
        rejected_count = len(rejected_clusters)

        if verbose:
            print(f"  Initial clusters: {initial_cluster_count}")
            print(f"  Rejected: {rejected_count}")
            print(f"  Final clusters: {final_cluster_count}")

            if rejected_clusters and verbose:
                print(f"\n  Rejection reasons:")
                reason_counts = {}
                for _, reason, _ in rejected_clusters:
                    reason_counts[reason] = reason_counts.get(reason, 0) + 1
                for reason, count in reason_counts.items():
                    print(f"    - {reason}: {count}")

        return new_labels

    def cluster_all_products_with_dual_text(
        self,
        use_cache: bool = True,
        use_three_stage: bool = True,
        stage1_min_size: int = 10,
        stage2_min_size: int = 5,
        stage3_min_size: int = 3,
        dispersion_threshold: float = 0.3,
        limit: int = None,
        verbose: bool = True
    ) -> Dict:
        """
        使用双文本策略进行聚类（Phase 2 新增）

        流程：
        1. 初始聚类（使用full_text）
        2. 发现属性词
        3. 生成topic_text
        4. 重新聚类（使用topic_text）

        Args:
            use_cache: 是否使用缓存
            use_three_stage: 是否使用三阶段聚类
            stage1_min_size: 第一阶段最小簇大小
            stage2_min_size: 第二阶段最小簇大小
            stage3_min_size: 第三阶段最小簇大小
            dispersion_threshold: 属性词分散度阈值
            limit: 限制处理的商品数量
            verbose: 是否打印详细信息

        Returns:
            聚类结果统计
        """
        if verbose:
            print("\n" + "="*80)
            print("[DUAL TEXT STRATEGY] Phase 2 - Data-Driven Attribute Discovery")
            print("="*80)

        # 查询所有未删除的商品
        query = self.db.query(Product).filter(Product.is_deleted == False)
        if limit is not None:
            query = query.limit(limit)
        products = query.all()

        if not products:
            return {"success": False, "message": "没有可聚类的商品"}

        if verbose:
            print(f"\n[STEP 1] Initial clustering with full_text ({len(products)} products)")
            print("-" * 80)

        # 步骤1: 初始聚类（使用full_text）
        embeddings, product_ids = self.vectorize_products(products, use_cache)

        if use_three_stage:
            initial_labels, cluster_types = self.perform_three_stage_clustering(
                embeddings, product_ids,
                stage1_min_size=stage1_min_size,
                stage2_min_size=stage2_min_size,
                stage3_min_size=stage3_min_size
            )
        else:
            initial_labels = self.perform_clustering(
                embeddings,
                min_cluster_size=stage1_min_size,
                min_samples=max(3, stage1_min_size // 2)
            )
            cluster_types = {}

        # 步骤2: 发现属性词
        if verbose:
            print("\n" + "="*80)
            print("[STEP 2] Discovering attribute words from initial clustering")
            print("="*80)

        product_names = [p.product_name for p in products]
        attribute_words, analysis_data = self.discover_attribute_words_from_clustering(
            initial_labels,
            product_names,
            dispersion_threshold=dispersion_threshold,
            verbose=verbose
        )

        # 步骤3: 生成topic_text
        if verbose:
            print("\n" + "="*80)
            print("[STEP 3] Generating topic_text (removing attribute words)")
            print("="*80)

        topic_texts = []
        for product in products:
            topic_text = self.generate_topic_text(product.product_name, attribute_words)
            topic_texts.append(topic_text)

        if verbose:
            print(f"\n[EXAMPLES] Full text → Topic text:")
            for i in range(min(5, len(products))):
                print(f"  {products[i].product_name}")
                print(f"  → {topic_texts[i]}")
                print()

        # 步骤4: 重新向量化（使用topic_text）
        if verbose:
            print("\n" + "="*80)
            print("[STEP 4] Re-vectorizing with topic_text")
            print("="*80)

        # 临时修改商品名称为topic_text
        original_names = [p.product_name for p in products]
        for i, product in enumerate(products):
            product.product_name = topic_texts[i]

        # 重新向量化
        topic_embeddings, _ = self.vectorize_products(products, use_cache=False)

        # 恢复原始名称
        for i, product in enumerate(products):
            product.product_name = original_names[i]

        # 步骤5: 重新聚类（使用topic_text向量）
        if verbose:
            print("\n" + "="*80)
            print("[STEP 5] Re-clustering with topic_text embeddings")
            print("="*80)

        if use_three_stage:
            final_labels, final_cluster_types = self.perform_three_stage_clustering(
                topic_embeddings, product_ids,
                stage1_min_size=stage1_min_size,
                stage2_min_size=stage2_min_size,
                stage3_min_size=stage3_min_size
            )
        else:
            final_labels = self.perform_clustering(
                topic_embeddings,
                min_cluster_size=stage1_min_size,
                min_samples=max(3, stage1_min_size // 2)
            )
            final_cluster_types = {}

        # 更新数据库
        if verbose:
            print("\n" + "="*80)
            print("[STEP 6] Updating database")
            print("="*80)

        for i, product_id in enumerate(product_ids):
            product = self.db.query(Product).filter(
                Product.product_id == product_id
            ).first()

            if product:
                product.cluster_id = int(final_labels[i])
                product.topic_text = topic_texts[i]  # 保存topic_text

                # 设置簇类型
                if use_three_stage and final_labels[i] != -1:
                    cluster_info = final_cluster_types.get(int(final_labels[i]), {})
                    product.cluster_type = cluster_info.get('type', 'unknown')
                else:
                    product.cluster_type = None

        self.db.commit()

        if verbose:
            print("[DATABASE] Database updated successfully")

        # 生成统计信息
        n_initial_clusters = len(set(initial_labels)) - (1 if -1 in initial_labels else 0)
        n_final_clusters = len(set(final_labels)) - (1 if -1 in final_labels else 0)
        n_initial_noise = list(initial_labels).count(-1)
        n_final_noise = list(final_labels).count(-1)

        result = {
            "success": True,
            "strategy": "dual_text",
            "total_products": len(products),
            "initial_clustering": {
                "n_clusters": n_initial_clusters,
                "n_noise": n_initial_noise,
                "noise_ratio": n_initial_noise / len(products) * 100
            },
            "attribute_discovery": {
                "n_attribute_words": len(attribute_words),
                "attribute_words": list(attribute_words),
                "dispersion_threshold": dispersion_threshold
            },
            "final_clustering": {
                "n_clusters": n_final_clusters,
                "n_noise": n_final_noise,
                "noise_ratio": n_final_noise / len(products) * 100
            },
            "improvement": {
                "cluster_reduction": n_initial_clusters - n_final_clusters,
                "cluster_reduction_pct": (n_initial_clusters - n_final_clusters) / n_initial_clusters * 100 if n_initial_clusters > 0 else 0
            }
        }

        if use_three_stage:
            primary_clusters = [cid for cid, info in final_cluster_types.items() if info['type'] == 'primary']
            secondary_clusters = [cid for cid, info in final_cluster_types.items() if info['type'] == 'secondary']
            micro_clusters = [cid for cid, info in final_cluster_types.items() if info.get('type') == 'micro']

            result["final_clustering"].update({
                "n_primary_clusters": len(primary_clusters),
                "n_secondary_clusters": len(secondary_clusters),
                "n_micro_clusters": len(micro_clusters)
            })

        if verbose:
            print("\n" + "="*80)
            print("[RESULTS SUMMARY]")
            print("="*80)
            print(f"\nInitial clustering (full_text):")
            print(f"  Clusters: {n_initial_clusters}")
            print(f"  Noise: {n_initial_noise} ({n_initial_noise / len(products) * 100:.2f}%)")
            print(f"\nAttribute discovery:")
            print(f"  Attribute words: {len(attribute_words)}")
            print(f"\nFinal clustering (topic_text):")
            print(f"  Clusters: {n_final_clusters}")
            print(f"  Noise: {n_final_noise} ({n_final_noise / len(products) * 100:.2f}%)")
            print(f"\nImprovement:")
            print(f"  Cluster reduction: {n_initial_clusters - n_final_clusters} ({result['improvement']['cluster_reduction_pct']:.1f}%)")
            print("\n" + "="*80)

        return result

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
        limit: int = None,
        use_dual_text: bool = False,  # Phase 2: 是否使用双文本策略
        dispersion_threshold: float = 0.3,  # Phase 2: 属性词分散度阈值
        use_merge_strategy: bool = False,  # Stage 2/3 Redesign: 是否使用归并策略
        merge_threshold: float = 0.5,  # Stage 2/3 Redesign: 归并相似度阈值
        min_cohesion: float = 0.5,  # Stage 2/3 Redesign: 最小簇内一致性
        min_separation: float = 0.3  # Stage 2/3 Redesign: 最小簇区分度
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
            use_dual_text: 是否使用双文本策略（Phase 2新增）
            dispersion_threshold: 属性词分散度阈值（Phase 2新增）
            use_merge_strategy: 是否使用归并策略（Stage 2/3 Redesign）
            merge_threshold: 归并相似度阈值（Stage 2/3 Redesign）
            min_cohesion: 最小簇内一致性（Stage 2/3 Redesign）
            min_separation: 最小簇区分度（Stage 2/3 Redesign）

        Returns:
            聚类结果统计
        """
        # ✅ Phase 2: 如果启用双文本策略，使用新方法
        if use_dual_text:
            return self.cluster_all_products_with_dual_text(
                use_cache=use_cache,
                use_three_stage=use_three_stage,
                stage1_min_size=stage1_min_size,
                stage2_min_size=stage2_min_size,
                stage3_min_size=stage3_min_size,
                dispersion_threshold=dispersion_threshold,
                limit=limit,
                verbose=True
            )
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
        if use_merge_strategy:
            # Stage 2/3 重新设计：归并策略 + 质量门控
            print(f"DEBUG: Using three-stage clustering with merge strategy (V2)")
            cluster_labels, cluster_types = self.perform_three_stage_clustering_with_merge(
                embeddings,
                product_ids,
                stage1_min_size=stage1_min_size,
                merge_threshold=merge_threshold,
                min_cohesion=min_cohesion,
                min_separation=min_separation,
                min_cluster_size=3,
                verbose=True
            )
        elif use_three_stage:
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
