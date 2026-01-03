"""
聚类引擎模块
使用HDBSCAN进行大组和小组聚类
"""
import numpy as np
from typing import List, Dict, Tuple, Optional
from collections import Counter

import hdbscan
from sklearn.metrics import silhouette_score

from config.settings import (
    LARGE_CLUSTER_CONFIG,
    SMALL_CLUSTER_CONFIG,
)
from utils.logger import get_logger

logger = get_logger(__name__)


class ClusteringEngine:
    """聚类引擎类"""

    def __init__(self, config: Dict = None, cluster_level: str = 'A'):
        """
        初始化聚类引擎

        Args:
            config: 聚类配置参数
            cluster_level: 聚类级别（'A'=大组，'B'=小组）
        """
        self.cluster_level = cluster_level
        if config is None:
            config = LARGE_CLUSTER_CONFIG if cluster_level == 'A' else SMALL_CLUSTER_CONFIG
        self.config = config

        logger.info(f"初始化{cluster_level}级聚类引擎，参数: {config}")

    def fit_predict(self, embeddings: np.ndarray) -> np.ndarray:
        """
        执行HDBSCAN聚类

        Args:
            embeddings: 向量矩阵 (n_samples, n_features)

        Returns:
            聚类标签数组 (n_samples,)，-1表示噪音点
        """
        logger.info(f"执行HDBSCAN聚类，数据形状: {embeddings.shape}")

        # 如果使用cosine距离，需要先归一化向量
        # 归一化后使用euclidean等价于cosine相似度
        metric = self.config['metric']
        if metric == 'cosine':
            logger.info("预处理: L2归一化（cosine -> euclidean）")
            from sklearn.preprocessing import normalize
            embeddings_normalized = normalize(embeddings, norm='l2')
            metric = 'euclidean'
        else:
            embeddings_normalized = embeddings

        # 创建HDBSCAN聚类器
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=self.config['min_cluster_size'],
            min_samples=self.config['min_samples'],
            metric=metric,
            cluster_selection_epsilon=self.config.get('cluster_selection_epsilon', 0.0),
            cluster_selection_method=self.config.get('cluster_selection_method', 'eom'),
            prediction_data=True  # 用于增量更新
        )

        # 执行聚类
        labels = clusterer.fit_predict(embeddings_normalized)

        # 统计结果
        unique_labels = set(labels)
        n_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)
        n_noise = list(labels).count(-1)

        logger.info(f"聚类完成: {n_clusters}个聚类, {n_noise}个噪音点 ({n_noise/len(labels)*100:.1f}%)")

        # 计算轮廓系数（如果簇数>1且有非噪音点）
        if n_clusters > 1 and n_noise < len(labels):
            try:
                # 只计算非噪音点的轮廓系数
                mask = labels != -1
                if mask.sum() > 1:
                    score = silhouette_score(embeddings_normalized[mask], labels[mask], metric='euclidean')
                    logger.info(f"轮廓系数: {score:.3f}")
            except Exception as e:
                logger.warning(f"轮廓系数计算失败: {str(e)}")

        return labels, clusterer

    def analyze_clusters(self, labels: np.ndarray, phrases: List[Dict]) -> Dict:
        """
        分析聚类结果

        Args:
            labels: 聚类标签
            phrases: 短语列表（包含phrase, phrase_id等）

        Returns:
            聚类分析结果
        """
        logger.info("分析聚类结果...")

        cluster_info = {}
        label_counts = Counter(labels)

        # 统计每个聚类
        for label in sorted(set(labels)):
            if label == -1:
                continue  # 跳过噪音点

            # 找到该聚类的所有短语
            indices = np.where(labels == label)[0]
            cluster_phrases = [phrases[i] for i in indices]

            # 计算统计信息
            total_frequency = sum(p.get('frequency', 1) for p in cluster_phrases)
            total_volume = sum(p.get('volume', 0) for p in cluster_phrases)

            # 选择代表短语（按频次排序）
            sorted_phrases = sorted(
                cluster_phrases,
                key=lambda x: x.get('frequency', 1),
                reverse=True
            )
            example_phrases = [p['phrase'] for p in sorted_phrases[:10]]

            cluster_info[label] = {
                'cluster_id': label,
                'size': len(cluster_phrases),
                'phrase_ids': [p['phrase_id'] for p in cluster_phrases],
                'total_frequency': total_frequency,
                'total_volume': total_volume,
                'example_phrases': example_phrases,
                'all_phrases': [p['phrase'] for p in cluster_phrases],
            }

        # 噪音点统计
        noise_count = label_counts.get(-1, 0)

        logger.info(f"有效聚类数: {len(cluster_info)}, 噪音点数: {noise_count}")

        # 聚类大小分布
        sizes = [info['size'] for info in cluster_info.values()]
        if sizes:
            logger.info(f"聚类大小分布 - 最小: {min(sizes)}, 最大: {max(sizes)}, "
                       f"平均: {np.mean(sizes):.1f}, 中位数: {np.median(sizes):.1f}")

            # Top 10 最大聚类
            sorted_clusters = sorted(
                cluster_info.items(),
                key=lambda x: x[1]['size'],
                reverse=True
            )
            logger.info("Top 10 最大聚类:")
            for rank, (label, info) in enumerate(sorted_clusters[:10], 1):
                examples = ', '.join(info['example_phrases'][:3])
                logger.info(f"  {rank}. 聚类{label}: {info['size']}个短语 - {examples}...")

        return cluster_info

    def assign_cluster_ids(self, labels: np.ndarray) -> np.ndarray:
        """
        将聚类标签转换为连续的cluster_id（0, 1, 2, ...）
        噪音点(-1)保持为-1

        Args:
            labels: 原始聚类标签

        Returns:
            重新编号的cluster_id
        """
        unique_labels = sorted(set(labels))
        if -1 in unique_labels:
            unique_labels.remove(-1)

        # 创建映射：原始label -> 新cluster_id
        label_map = {-1: -1}  # 噪音点保持-1
        for new_id, old_label in enumerate(unique_labels):
            label_map[old_label] = new_id

        # 应用映射
        cluster_ids = np.array([label_map[label] for label in labels])

        return cluster_ids


def cluster_phrases_large(embeddings: np.ndarray, phrases: List[Dict],
                          config: Dict = None) -> Tuple[np.ndarray, Dict]:
    """
    执行大组聚类（Phase 2）

    Args:
        embeddings: 短语embeddings
        phrases: 短语列表
        config: 聚类配置参数（可选，默认使用LARGE_CLUSTER_CONFIG）

    Returns:
        (cluster_ids, cluster_info, clusterer)
    """
    logger.info("="*70)
    logger.info("执行大组聚类 (Level A)")
    logger.info("="*70)

    # 使用提供的配置或默认配置
    if config is None:
        config = LARGE_CLUSTER_CONFIG

    # 创建聚类引擎
    engine = ClusteringEngine(config=config, cluster_level='A')

    # 执行聚类
    labels, clusterer = engine.fit_predict(embeddings)

    # 分析结果
    cluster_info = engine.analyze_clusters(labels, phrases)

    # 重新编号
    cluster_ids = engine.assign_cluster_ids(labels)

    logger.info("="*70)
    logger.info(f"大组聚类完成，生成 {len(cluster_info)} 个聚类")
    logger.info("="*70)

    return cluster_ids, cluster_info, clusterer


def cluster_phrases_small(embeddings: np.ndarray, phrases: List[Dict],
                          parent_cluster_id: int,
                          min_cluster_size: int = None,
                          min_samples: int = None) -> Tuple[np.ndarray, Dict]:
    """
    执行小组聚类（Phase 4）

    Args:
        embeddings: 短语embeddings
        phrases: 短语列表
        parent_cluster_id: 父聚类ID（大组ID）
        min_cluster_size: 最小聚类大小（可选，默认使用配置文件）
        min_samples: 最小样本数（可选，默认使用配置文件）

    Returns:
        (cluster_ids, cluster_info)
    """
    logger.info(f"执行小组聚类 (Level B, 父聚类={parent_cluster_id})")

    # 创建聚类配置
    config = SMALL_CLUSTER_CONFIG.copy()
    if min_cluster_size is not None:
        config['min_cluster_size'] = min_cluster_size
        logger.info(f"使用自定义min_cluster_size={min_cluster_size}")
    if min_samples is not None:
        config['min_samples'] = min_samples
        logger.info(f"使用自定义min_samples={min_samples}")

    # 创建聚类引擎
    engine = ClusteringEngine(config=config, cluster_level='B')

    # 执行聚类
    labels, clusterer = engine.fit_predict(embeddings)

    # 分析结果
    cluster_info = engine.analyze_clusters(labels, phrases)

    # 重新编号
    cluster_ids = engine.assign_cluster_ids(labels)

    logger.info(f"小组聚类完成，生成 {len(cluster_info)} 个聚类")

    return cluster_ids, cluster_info, clusterer


def test_clustering():
    """测试聚类功能"""
    logger.info("="*70)
    logger.info("测试聚类引擎")
    logger.info("="*70)

    # 生成测试数据（3个簇）
    np.random.seed(42)

    cluster1 = np.random.randn(100, 10) + np.array([5, 5, 0, 0, 0, 0, 0, 0, 0, 0])
    cluster2 = np.random.randn(80, 10) + np.array([-5, -5, 0, 0, 0, 0, 0, 0, 0, 0])
    cluster3 = np.random.randn(60, 10) + np.array([0, 0, 5, 5, 0, 0, 0, 0, 0, 0])
    noise = np.random.randn(20, 10) * 10

    embeddings = np.vstack([cluster1, cluster2, cluster3, noise])

    # 生成假短语
    phrases = [
        {'phrase_id': i, 'phrase': f'phrase_{i}', 'frequency': np.random.randint(1, 1000)}
        for i in range(len(embeddings))
    ]

    # 执行聚类
    cluster_ids, cluster_info, clusterer = cluster_phrases_large(embeddings, phrases)

    # 验证结果
    assert len(cluster_ids) == len(embeddings), "聚类标签数量不匹配"
    assert len(cluster_info) >= 2, f"期望至少2个聚类，实际得到{len(cluster_info)}个"

    logger.info("✅ 聚类引擎测试通过！")
    logger.info(f"生成聚类数: {len(cluster_info)}, 噪音点数: {(cluster_ids == -1).sum()}")


if __name__ == "__main__":
    test_clustering()
