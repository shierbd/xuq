"""
Graph construction utilities for Louvain clustering
构建相似度图用于Louvain社区发现
"""
import sys
from pathlib import Path

# 添加项目根目录到路径（用于直接运行测试）
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

import numpy as np
import networkx as nx
from typing import Tuple, List, Dict
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors
from tqdm import tqdm
from utils.logger import get_logger

logger = get_logger(__name__)


def build_knn_graph(
    embeddings: np.ndarray,
    k_neighbors: int = 20,
    similarity_threshold: float = 0.6,
    metric: str = 'cosine',
    verbose: bool = True
) -> Tuple[nx.Graph, Dict]:
    """
    构建K近邻相似度图

    Args:
        embeddings: 向量矩阵 (n_samples, n_features)
        k_neighbors: 每个节点的K近邻数量
        similarity_threshold: 边权重阈值（只保留相似度>=此值的边）
        metric: 距离度量（'cosine' or 'euclidean'）
        verbose: 是否显示进度

    Returns:
        (graph, stats)
        - graph: NetworkX无向图
        - stats: 统计信息字典
    """
    n_samples = len(embeddings)

    if verbose:
        logger.info(f"构建K近邻图: n_samples={n_samples}, k={k_neighbors}, "
                   f"threshold={similarity_threshold}")

    # 1. 归一化向量（对于cosine距离）
    if metric == 'cosine':
        from sklearn.preprocessing import normalize
        embeddings_norm = normalize(embeddings, norm='l2')
        # 使用欧氏距离代替cosine（归一化后等价）
        knn_metric = 'euclidean'
    else:
        embeddings_norm = embeddings
        knn_metric = metric

    # 2. 构建K近邻索引
    if verbose:
        logger.info("构建K近邻索引...")

    knn = NearestNeighbors(
        n_neighbors=min(k_neighbors + 1, n_samples),  # +1因为包含自己
        metric=knn_metric,
        algorithm='auto',
        n_jobs=-1  # 使用所有CPU核心
    )
    knn.fit(embeddings_norm)

    # 3. 查找K近邻
    if verbose:
        logger.info("查找K近邻...")

    distances, indices = knn.kneighbors(embeddings_norm)

    # 4. 构建图
    if verbose:
        logger.info("构建NetworkX图...")

    G = nx.Graph()
    G.add_nodes_from(range(n_samples))

    edge_count = 0
    filtered_edge_count = 0

    # 将距离转换为相似度
    if metric == 'cosine':
        # 欧氏距离 -> cosine相似度
        # similarity = 1 - (distance^2 / 2)
        similarities = 1 - (distances ** 2) / 2
    else:
        # 对于欧氏距离，使用高斯核转换
        similarities = np.exp(-distances ** 2)

    # 添加边
    iterator = tqdm(range(n_samples), desc="添加边") if verbose else range(n_samples)

    for i in iterator:
        for j_idx, j in enumerate(indices[i]):
            if i == j:
                continue  # 跳过自己

            similarity = similarities[i, j_idx]
            edge_count += 1

            # 过滤低相似度的边
            if similarity >= similarity_threshold:
                # 添加无向边（只添加一次）
                if i < j:  # 避免重复
                    G.add_edge(i, j, weight=similarity)
                    filtered_edge_count += 1

    # 统计信息
    stats = {
        'n_nodes': G.number_of_nodes(),
        'n_edges': G.number_of_edges(),
        'total_potential_edges': edge_count // 2,  # 除以2因为无向图
        'filtered_edges': filtered_edge_count,
        'filter_rate': 1 - (filtered_edge_count / (edge_count // 2)) if edge_count > 0 else 0,
        'avg_degree': sum(dict(G.degree()).values()) / G.number_of_nodes() if G.number_of_nodes() > 0 else 0,
        'density': nx.density(G),
        'n_connected_components': nx.number_connected_components(G),
    }

    if verbose:
        logger.info(f"图构建完成:")
        logger.info(f"  节点数: {stats['n_nodes']}")
        logger.info(f"  边数: {stats['n_edges']}")
        logger.info(f"  平均度: {stats['avg_degree']:.2f}")
        logger.info(f"  密度: {stats['density']:.6f}")
        logger.info(f"  连通分量数: {stats['n_connected_components']}")
        logger.info(f"  边过滤率: {stats['filter_rate']*100:.1f}%")

    return G, stats


def test_graph_construction():
    """测试图构建"""
    logger.info("测试K近邻图构建...")

    # 生成测试数据（3个明显的簇）
    np.random.seed(42)
    cluster1 = np.random.randn(100, 10) + np.array([5, 5, 0, 0, 0, 0, 0, 0, 0, 0])
    cluster2 = np.random.randn(80, 10) + np.array([-5, -5, 0, 0, 0, 0, 0, 0, 0, 0])
    cluster3 = np.random.randn(60, 10) + np.array([0, 0, 5, 5, 0, 0, 0, 0, 0, 0])

    embeddings = np.vstack([cluster1, cluster2, cluster3])

    # 构建图
    G, stats = build_knn_graph(
        embeddings,
        k_neighbors=15,
        similarity_threshold=0.5,
        verbose=True
    )

    # 验证
    assert G.number_of_nodes() == len(embeddings), "节点数量不匹配"
    assert G.number_of_edges() > 0, "没有边"
    assert stats['avg_degree'] > 0, "平均度为0"

    logger.info("OK: 图构建测试通过！")
    return G, stats


if __name__ == "__main__":
    test_graph_construction()
