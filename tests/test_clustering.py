"""
测试聚类引擎模块
"""
import pytest
import numpy as np
from core.clustering import ClusteringEngine, cluster_phrases_large, cluster_phrases_small


class TestClusteringEngine:
    """测试ClusteringEngine类"""

    def test_init_large_cluster(self):
        """测试大组聚类引擎初始化"""
        engine = ClusteringEngine(cluster_level='A')
        assert engine.cluster_level == 'A'
        assert engine.config['min_cluster_size'] == 30

    def test_init_small_cluster(self):
        """测试小组聚类引擎初始化"""
        engine = ClusteringEngine(cluster_level='B')
        assert engine.cluster_level == 'B'
        assert engine.config['min_cluster_size'] == 5

    def test_fit_predict(self, sample_embeddings):
        """测试聚类预测"""
        engine = ClusteringEngine(cluster_level='A')
        labels, clusterer = engine.fit_predict(sample_embeddings)

        assert len(labels) == len(sample_embeddings)
        assert hasattr(clusterer, 'labels_')
        # 应该至少有1个聚类
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        assert n_clusters >= 1

    def test_analyze_clusters(self, sample_embeddings, sample_phrases):
        """测试聚类分析"""
        engine = ClusteringEngine(cluster_level='A')
        labels, _ = engine.fit_predict(sample_embeddings)

        cluster_info = engine.analyze_clusters(labels, sample_phrases)

        assert isinstance(cluster_info, dict)
        # 验证聚类信息结构
        for cluster_id, info in cluster_info.items():
            assert 'size' in info
            assert 'phrase_ids' in info
            assert 'example_phrases' in info
            assert info['size'] > 0

    def test_assign_cluster_ids(self, sample_embeddings):
        """测试聚类ID重新编号"""
        engine = ClusteringEngine(cluster_level='A')
        labels, _ = engine.fit_predict(sample_embeddings)

        cluster_ids = engine.assign_cluster_ids(labels)

        assert len(cluster_ids) == len(labels)
        # 噪音点应该保持为-1
        assert all(cluster_ids[labels == -1] == -1)
        # 非噪音点应该从0开始连续编号
        non_noise_ids = cluster_ids[cluster_ids != -1]
        if len(non_noise_ids) > 0:
            assert min(non_noise_ids) == 0


class TestClusteringFunctions:
    """测试聚类辅助函数"""

    def test_cluster_phrases_large(self, sample_embeddings, sample_phrases):
        """测试大组聚类函数"""
        cluster_ids, cluster_info, clusterer = cluster_phrases_large(
            sample_embeddings,
            sample_phrases
        )

        assert len(cluster_ids) == len(sample_embeddings)
        assert isinstance(cluster_info, dict)
        assert hasattr(clusterer, 'labels_')

    def test_cluster_phrases_small(self, sample_embeddings, sample_phrases):
        """测试小组聚类函数"""
        parent_cluster_id = 1

        cluster_ids, cluster_info, clusterer = cluster_phrases_small(
            sample_embeddings,
            sample_phrases,
            parent_cluster_id
        )

        assert len(cluster_ids) == len(sample_embeddings)
        assert isinstance(cluster_info, dict)


@pytest.mark.slow
class TestClusteringQuality:
    """测试聚类质量"""

    def test_clustering_consistency(self, sample_embeddings, sample_phrases):
        """测试聚类一致性（相同输入应产生相同结果）"""
        engine = ClusteringEngine(cluster_level='A')

        # 第一次聚类
        labels1, _ = engine.fit_predict(sample_embeddings)

        # 第二次聚类（相同数据）
        labels2, _ = engine.fit_predict(sample_embeddings)

        # HDBSCAN应该产生相同结果
        assert np.array_equal(labels1, labels2)

    def test_min_cluster_size_constraint(self, sample_embeddings, sample_phrases):
        """测试最小聚类大小约束"""
        engine = ClusteringEngine(cluster_level='A')
        labels, _ = engine.fit_predict(sample_embeddings)
        cluster_info = engine.analyze_clusters(labels, sample_phrases)

        # 所有聚类应该满足最小大小要求
        min_size = engine.config['min_cluster_size']
        for info in cluster_info.values():
            assert info['size'] >= min_size
