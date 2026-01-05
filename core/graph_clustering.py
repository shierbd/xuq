"""
Graph-based clustering using Louvain community detection
基于图的聚类：使用Louvain社区发现算法
"""
import sys
from pathlib import Path
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

import numpy as np
import networkx as nx
from typing import List, Dict, Tuple
from collections import Counter
import community as community_louvain  # python-louvain
from tqdm import tqdm

from config.settings import LOUVAIN_CONFIG
from utils.logger import get_logger
from utils.graph_utils import build_knn_graph

logger = get_logger(__name__)


class LouvainClusteringEngine:
    """Louvain聚类引擎"""

    def __init__(self, config: Dict = None):
        """初始化Louvain聚类引擎"""
        self.config = config or LOUVAIN_CONFIG.copy()
        logger.info(f"初始化Louvain聚类引擎")

    def fit_predict(self, embeddings: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """执行Louvain聚类"""
        logger.info(f"="*70)
        logger.info(f"执行Louvain聚类，数据形状: {embeddings.shape}")
        logger.info(f"="*70)

        # 1. 构建K近邻图
        logger.info("\n【步骤1】构建K近邻相似度图...")
        G, graph_stats = build_knn_graph(
            embeddings,
            k_neighbors=self.config['k_neighbors'],
            similarity_threshold=self.config['similarity_threshold'],
            metric='cosine',
            verbose=True
        )

        # 2. 运行Louvain算法
        logger.info("\n【步骤2】运行Louvain社区发现...")
        partition = community_louvain.best_partition(
            G,
            weight='weight',
            resolution=self.config['resolution'],
            randomize=self.config.get('randomize', False),
            random_state=self.config.get('random_seed', 42) if not self.config.get('randomize', False) else None
        )

        # 将partition字典转换为标签数组
        labels = np.array([partition[i] for i in range(len(embeddings))])

        # 统计初始聚类结果
        unique_labels = set(labels)
        n_clusters = len(unique_labels)

        logger.info(f"  初始聚类数: {n_clusters}")

        # 计算模块度
        if self.config.get('calculate_modularity', True):
            modularity = community_louvain.modularity(partition, G, weight='weight')
            logger.info(f"  模块度 (Modularity): {modularity:.4f}")
        else:
            modularity = None

        # 3. 后处理
        logger.info("\n【步骤3】聚类后处理...")
        labels, post_stats = self._post_process_clusters(labels, embeddings, G)

        # 最终统计
        unique_labels = set(labels)
        n_clusters_final = len(unique_labels) - (1 if -1 in unique_labels else 0)
        n_noise = (labels == -1).sum()

        logger.info(f"\n最终聚类结果:")
        logger.info(f"  有效聚类数: {n_clusters_final}")
        logger.info(f"  噪音点数: {n_noise} ({n_noise/len(labels)*100:.1f}%)")

        # 准备元数据
        metadata = {
            'graph': G,
            'graph_stats': graph_stats,
            'partition': partition,
            'modularity': modularity,
            'initial_n_clusters': n_clusters,
            'final_n_clusters': n_clusters_final,
            'n_noise': n_noise,
            'post_processing_stats': post_stats,
        }

        return labels, metadata

    def _post_process_clusters(self, labels: np.ndarray, embeddings: np.ndarray,
                                G: nx.Graph) -> Tuple[np.ndarray, Dict]:
        """聚类后处理：合并小聚类、拆分大聚类"""
        stats = {
            'merged_clusters': 0,
            'split_clusters': 0,
            'noise_points': 0,
        }

        labels = labels.copy()
        label_counts = Counter(labels)

        # 1. 处理小聚类
        min_size = self.config.get('min_community_size', 10)
        small_clusters = [label for label, count in label_counts.items()
                         if count < min_size]

        if small_clusters and self.config.get('merge_small_clusters', True):
            logger.info(f"  发现 {len(small_clusters)} 个小聚类（size < {min_size}）")

            # 标记为噪音
            for label in small_clusters:
                mask = labels == label
                labels[mask] = -1
                stats['noise_points'] += mask.sum()

            stats['merged_clusters'] = len(small_clusters)
            logger.info(f"  已将 {stats['merged_clusters']} 个小聚类标记为噪音")

        # 2. 重新编号聚类ID（使其连续）
        unique_labels = sorted(set(labels))
        if -1 in unique_labels:
            unique_labels.remove(-1)

        label_map = {-1: -1}
        for new_id, old_label in enumerate(unique_labels):
            label_map[old_label] = new_id

        labels = np.array([label_map[label] for label in labels])

        return labels, stats

    def analyze_clusters(self, labels: np.ndarray, phrases: List[Dict]) -> Dict:
        """分析聚类结果"""
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

            # 选择代表短语
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
            logger.info(f"聚类大小分布:")
            logger.info(f"  最小: {min(sizes)}, 最大: {max(sizes)}")
            logger.info(f"  平均: {np.mean(sizes):.1f}, 中位数: {np.median(sizes):.1f}")

        return cluster_info


def cluster_phrases_louvain(
    embeddings: np.ndarray,
    phrases: List[Dict],
    config: Dict = None
) -> Tuple[np.ndarray, Dict, Dict]:
    """使用Louvain算法执行聚类"""
    logger.info("="*70)
    logger.info("执行Louvain社区发现聚类")
    logger.info("="*70)

    # 创建聚类引擎
    engine = LouvainClusteringEngine(config=config)

    # 执行聚类
    labels, metadata = engine.fit_predict(embeddings)

    # 分析结果
    cluster_info = engine.analyze_clusters(labels, phrases)

    logger.info("="*70)
    logger.info(f"Louvain聚类完成，生成 {len(cluster_info)} 个聚类")
    logger.info("="*70)

    return labels, cluster_info, metadata


def test_louvain_clustering():
    """测试Louvain聚类"""
    logger.info("="*70)
    logger.info("测试Louvain聚类引擎")
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
    cluster_ids, cluster_info, metadata = cluster_phrases_louvain(embeddings, phrases)

    # 验证结果
    assert len(cluster_ids) == len(embeddings), "聚类标签数量不匹配"
    assert len(cluster_info) >= 2, f"期望至少2个聚类，实际得到{len(cluster_info)}个"
    assert 'modularity' in metadata, "缺少模块度指标"

    logger.info(f"\nOK: Louvain聚类测试通过！")
    logger.info(f"  生成聚类数: {len(cluster_info)}")
    logger.info(f"  噪音点数: {(cluster_ids == -1).sum()}")
    logger.info(f"  模块度: {metadata['modularity']:.4f}")


if __name__ == "__main__":
    test_louvain_clustering()
