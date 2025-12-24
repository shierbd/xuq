"""
聚类质量评分模块
Cluster Quality Scoring Module

功能：
- 计算聚类簇的质量评分
- 多维度评估（大小、多样性、语义一致性）
- 为聚类审核提供辅助决策

创建日期：2025-12-23
"""

import sys
from typing import List, Dict, Tuple
from collections import Counter
from difflib import SequenceMatcher


class ClusterScorer:
    """
    聚类质量评分器

    评分维度：
    1. 大小得分 (40%权重) - 15-150个短语为最佳
    2. 多样性得分 (30%权重) - 基于唯一词汇比例
    3. 一致性得分 (30%权重) - 短语之间的语义相似度
    """

    # 权重配置
    WEIGHT_SIZE = 0.40
    WEIGHT_DIVERSITY = 0.30
    WEIGHT_CONSISTENCY = 0.30

    # 大小阈值
    OPTIMAL_SIZE_MIN = 15
    OPTIMAL_SIZE_MAX = 150
    MINIMUM_SIZE = 5

    def __init__(self):
        """初始化评分器"""
        pass

    def calculate_size_score(self, cluster_size: int) -> float:
        """
        计算簇大小得分

        评分规则：
        - size < 5: 0分（太小，无意义）
        - 5 <= size < 15: 线性增长到0.5分
        - 15 <= size <= 150: 1.0分（最佳范围）
        - size > 150: 逐渐降低（太大，难以审核）

        Args:
            cluster_size: 簇中短语数量

        Returns:
            大小得分 (0-1)
        """
        if cluster_size < self.MINIMUM_SIZE:
            return 0.0

        if cluster_size < self.OPTIMAL_SIZE_MIN:
            # 5-15个：线性增长到0.5分
            return (cluster_size - self.MINIMUM_SIZE) / (self.OPTIMAL_SIZE_MIN - self.MINIMUM_SIZE) * 0.5

        if cluster_size <= self.OPTIMAL_SIZE_MAX:
            # 15-150个：满分
            return 1.0

        # >150个：逐渐降低
        # 150-500个：从1.0降到0.3
        # >500个：保持0.3
        if cluster_size <= 500:
            return max(0.3, 1.0 - (cluster_size - self.OPTIMAL_SIZE_MAX) / 350 * 0.7)
        else:
            return 0.3

    def calculate_diversity_score(self, phrases: List[str]) -> float:
        """
        计算短语多样性得分

        策略：
        - 统计所有单词
        - 计算唯一词汇比例
        - 过高的重复度会降低得分

        Args:
            phrases: 短语列表

        Returns:
            多样性得分 (0-1)
        """
        if not phrases:
            return 0.0

        # 收集所有单词
        all_words = []
        for phrase in phrases:
            words = phrase.lower().split()
            all_words.extend(words)

        if not all_words:
            return 0.0

        # 计算唯一词汇比例
        unique_ratio = len(set(all_words)) / len(all_words)

        # 唯一比例越高，多样性越好
        # 但也不能太高（可能说明簇不够聚焦）
        # 最佳范围：0.3-0.7
        if unique_ratio < 0.3:
            # 太重复
            return unique_ratio / 0.3 * 0.5
        elif unique_ratio <= 0.7:
            # 最佳范围
            return 0.5 + (unique_ratio - 0.3) / 0.4 * 0.5
        else:
            # 可能太分散
            return max(0.7, 1.0 - (unique_ratio - 0.7) * 0.5)

    def calculate_consistency_score(self, phrases: List[str], sample_size: int = 20) -> float:
        """
        计算语义一致性得分

        策略：
        - 随机抽样若干短语对
        - 计算它们之间的相似度
        - 平均相似度越高，一致性越好

        Args:
            phrases: 短语列表
            sample_size: 抽样大小

        Returns:
            一致性得分 (0-1)
        """
        if len(phrases) < 2:
            return 0.0

        # 限制抽样大小
        sample_size = min(sample_size, len(phrases))

        # 如果短语太少，使用全部
        if len(phrases) <= 10:
            sample_phrases = phrases
        else:
            # 随机抽样（使用固定种子以保证可复现）
            import random
            random.seed(42)
            sample_phrases = random.sample(phrases, sample_size)

        # 计算短语对的相似度
        similarities = []

        for i in range(len(sample_phrases)):
            for j in range(i + 1, min(i + 6, len(sample_phrases))):  # 限制比较次数
                phrase1 = sample_phrases[i]
                phrase2 = sample_phrases[j]

                similarity = self._calculate_phrase_similarity(phrase1, phrase2)
                similarities.append(similarity)

        if not similarities:
            return 0.5  # 默认中等分数

        # 平均相似度
        avg_similarity = sum(similarities) / len(similarities)

        # 相似度在0.3-0.7为最佳
        # 太低说明簇不够聚焦，太高说明太重复
        if avg_similarity < 0.3:
            return avg_similarity / 0.3 * 0.5
        elif avg_similarity <= 0.7:
            return 0.5 + (avg_similarity - 0.3) / 0.4 * 0.5
        else:
            return max(0.7, 1.0 - (avg_similarity - 0.7) * 0.5)

    def _calculate_phrase_similarity(self, phrase1: str, phrase2: str) -> float:
        """
        计算两个短语的相似度

        策略：
        - 词袋相似度（Jaccard）
        - 序列相似度（SequenceMatcher）
        - 取最大值

        Args:
            phrase1, phrase2: 待比较的短语

        Returns:
            相似度 (0-1)
        """
        # 词袋相似度
        words1 = set(phrase1.lower().split())
        words2 = set(phrase2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        jaccard_sim = len(intersection) / len(union) if union else 0.0

        # 序列相似度
        seq_sim = SequenceMatcher(None, phrase1.lower(), phrase2.lower()).ratio()

        # 返回较高的相似度
        return max(jaccard_sim, seq_sim)

    def score_cluster(self, phrases: List[str]) -> Dict:
        """
        对一个聚类簇进行综合评分

        Args:
            phrases: 簇中的短语列表

        Returns:
            评分结果字典，包含：
            - total_score: 总分 (0-100)
            - size_score: 大小得分 (0-1)
            - diversity_score: 多样性得分 (0-1)
            - consistency_score: 一致性得分 (0-1)
            - cluster_size: 簇大小
            - quality_level: 质量等级 ('excellent'/'good'/'fair'/'poor')
        """
        cluster_size = len(phrases)

        # 计算各维度得分
        size_score = self.calculate_size_score(cluster_size)
        diversity_score = self.calculate_diversity_score(phrases)
        consistency_score = self.calculate_consistency_score(phrases)

        # 加权计算总分
        weighted_score = (
            size_score * self.WEIGHT_SIZE +
            diversity_score * self.WEIGHT_DIVERSITY +
            consistency_score * self.WEIGHT_CONSISTENCY
        )

        # 转换为0-100分
        total_score = weighted_score * 100

        # 确定质量等级
        if total_score >= 75:
            quality_level = 'excellent'
        elif total_score >= 60:
            quality_level = 'good'
        elif total_score >= 40:
            quality_level = 'fair'
        else:
            quality_level = 'poor'

        return {
            'total_score': round(total_score, 2),
            'size_score': round(size_score, 3),
            'diversity_score': round(diversity_score, 3),
            'consistency_score': round(consistency_score, 3),
            'cluster_size': cluster_size,
            'quality_level': quality_level,
            'weights': {
                'size': self.WEIGHT_SIZE,
                'diversity': self.WEIGHT_DIVERSITY,
                'consistency': self.WEIGHT_CONSISTENCY
            }
        }

    def score_multiple_clusters(self, clusters_data: Dict[int, List[str]]) -> Dict[int, Dict]:
        """
        对多个聚类簇进行批量评分

        Args:
            clusters_data: {cluster_id: [phrases]}

        Returns:
            {cluster_id: score_dict}
        """
        results = {}

        for cluster_id, phrases in clusters_data.items():
            results[cluster_id] = self.score_cluster(phrases)

        return results

    def get_top_clusters(self, clusters_data: Dict[int, List[str]],
                        top_n: int = 20) -> List[Tuple[int, Dict]]:
        """
        获取得分最高的N个聚类簇

        Args:
            clusters_data: {cluster_id: [phrases]}
            top_n: 返回前N个

        Returns:
            [(cluster_id, score_dict), ...] 按总分降序排列
        """
        # 批量评分
        scores = self.score_multiple_clusters(clusters_data)

        # 按总分排序
        sorted_clusters = sorted(
            scores.items(),
            key=lambda x: x[1]['total_score'],
            reverse=True
        )

        return sorted_clusters[:top_n]


def demo_scoring():
    """
    演示评分功能
    """
    scorer = ClusterScorer()

    # 测试案例1: 理想簇（大小适中，多样性好）
    test_cluster1 = [
        "best coffee maker",
        "top coffee machines",
        "good espresso maker",
        "best drip coffee maker",
        "coffee maker reviews",
    ] * 5  # 25个短语，有一定多样性

    print("测试案例1: 理想簇")
    score1 = scorer.score_cluster(test_cluster1)
    print(f"  总分: {score1['total_score']:.1f}/100")
    print(f"  质量等级: {score1['quality_level']}")
    print(f"  大小得分: {score1['size_score']:.3f}")
    print(f"  多样性得分: {score1['diversity_score']:.3f}")
    print(f"  一致性得分: {score1['consistency_score']:.3f}")
    print()

    # 测试案例2: 太小的簇
    test_cluster2 = ["best app", "top app", "good app"]

    print("测试案例2: 太小的簇")
    score2 = scorer.score_cluster(test_cluster2)
    print(f"  总分: {score2['total_score']:.1f}/100")
    print(f"  质量等级: {score2['quality_level']}")
    print()

    # 测试案例3: 重复度高的簇
    test_cluster3 = ["best app"] * 30

    print("测试案例3: 重复度高的簇")
    score3 = scorer.score_cluster(test_cluster3)
    print(f"  总分: {score3['total_score']:.1f}/100")
    print(f"  质量等级: {score3['quality_level']}")


if __name__ == "__main__":
    print("="*70)
    print("聚类质量评分模块 - 演示")
    print("="*70)
    print()

    demo_scoring()
