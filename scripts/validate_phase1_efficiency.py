"""
Phase 1效果验证脚本
Validation Script for Phase 1 Effectiveness

功能：
- 模拟基于质量评分的审核流程
- 计算审核时间节省
- 评估质量评分的准确性

创建日期：2025-12-23
"""

import sys
from pathlib import Path
from typing import Dict, List
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.repository import ClusterMetaRepository, PhraseRepository
from sqlalchemy import text


def simulate_review_process():
    """
    模拟审核流程，对比有无质量评分的效率差异
    """
    print("\n" + "="*80)
    print("Phase 1效果验证 - 审核效率提升测试")
    print("="*80)

    with ClusterMetaRepository() as repo:
        clusters_A = repo.get_all_clusters('A')

        print("\n[基本信息]")
        print(f"总聚类数: {len(clusters_A)}")

        # 统计评分情况
        scored_clusters = [c for c in clusters_A if c.quality_score is not None]
        print(f"已评分聚类数: {len(scored_clusters)}")

        # 质量等级分布
        quality_counts = {
            'excellent': sum(1 for c in scored_clusters if c.quality_level == 'excellent'),
            'good': sum(1 for c in scored_clusters if c.quality_level == 'good'),
            'fair': sum(1 for c in scored_clusters if c.quality_level == 'fair'),
            'poor': sum(1 for c in scored_clusters if c.quality_level == 'poor')
        }

        print("\n[质量等级分布]")
        print(f"  [Excellent] {quality_counts['excellent']} 个 ({quality_counts['excellent']/len(scored_clusters)*100:.1f}%)")
        print(f"  [Good]      {quality_counts['good']} 个 ({quality_counts['good']/len(scored_clusters)*100:.1f}%)")
        print(f"  [Fair]      {quality_counts['fair']} 个 ({quality_counts['fair']/len(scored_clusters)*100:.1f}%)")
        print(f"  [Poor]      {quality_counts['poor']} 个 ({quality_counts['poor']/len(scored_clusters)*100:.1f}%)")

        # 按质量分排序
        sorted_clusters = sorted(scored_clusters, key=lambda x: x.quality_score, reverse=True)

        print("\n" + "="*80)
        print("审核策略对比")
        print("="*80)

        # Phase 0基线数据
        baseline_time = 381  # 分钟
        baseline_clusters = len(clusters_A)
        avg_time_per_cluster = baseline_time / baseline_clusters

        print(f"\n[Phase 0 - 无质量评分]")
        print(f"  审核方式: 逐个审核所有聚类")
        print(f"  总时间: {baseline_time} 分钟")
        print(f"  平均每簇: {avg_time_per_cluster:.2f} 分钟")
        print(f"  审核簇数: {baseline_clusters} 个")

        # Phase 1优化策略：只审核高分聚类（Excellent + Good）
        high_quality_count = quality_counts['excellent'] + quality_counts['good']
        estimated_time_phase1 = high_quality_count * avg_time_per_cluster
        time_saved = baseline_time - estimated_time_phase1
        time_saved_percentage = (time_saved / baseline_time) * 100

        print(f"\n[Phase 1 - 基于质量评分（策略1：只审核Excellent+Good）]")
        print(f"  审核方式: 只审核高分聚类（Excellent + Good）")
        print(f"  预计时间: {estimated_time_phase1:.1f} 分钟")
        print(f"  审核簇数: {high_quality_count} 个")
        print(f"  节省时间: {time_saved:.1f} 分钟 ({time_saved_percentage:.1f}%)")

        if estimated_time_phase1 <= 120:
            print(f"  [OK] 预计时间{estimated_time_phase1:.1f}分钟 < 120分钟阈值")
        else:
            print(f"  [WARN] 预计时间{estimated_time_phase1:.1f}分钟 > 120分钟阈值")

        # 策略2：优先审核前15个高分聚类（目标是选出10-15个有价值的）
        target_review_count = 20  # 审核前20个，预计选出10-15个
        estimated_time_phase1_strategy2 = target_review_count * avg_time_per_cluster
        time_saved_strategy2 = baseline_time - estimated_time_phase1_strategy2
        time_saved_percentage_strategy2 = (time_saved_strategy2 / baseline_time) * 100

        print(f"\n[Phase 1 - 基于质量评分（策略2：优先审核Top 20）]")
        print(f"  审核方式: 按质量分降序，优先审核前20个")
        print(f"  预计时间: {estimated_time_phase1_strategy2:.1f} 分钟")
        print(f"  审核簇数: {target_review_count} 个")
        print(f"  节省时间: {time_saved_strategy2:.1f} 分钟 ({time_saved_percentage_strategy2:.1f}%)")

        if estimated_time_phase1_strategy2 <= 120:
            print(f"  [OK] 预计时间{estimated_time_phase1_strategy2:.1f}分钟 < 120分钟阈值")
        else:
            print(f"  [WARN] 预计时间{estimated_time_phase1_strategy2:.1f}分钟 > 120分钟阈值")

        # 显示Top 20推荐审核的聚类
        print("\n" + "="*80)
        print("推荐优先审核的聚类（Top 20）")
        print("="*80)

        top_20 = sorted_clusters[:20]

        print("\n排名 | 簇ID | 质量 | 评分 | 大小 | 主题")
        print("-" * 80)

        for i, cluster in enumerate(top_20, 1):
            quality_mark = {
                'excellent': '[***]',
                'good': '[** ]',
                'fair': '[*  ]',
                'poor': '[   ]'
            }.get(cluster.quality_level, '[???]')

            theme = cluster.main_theme[:30] if cluster.main_theme else "(未生成)"

            print(f"{i:2d}   | {cluster.cluster_id:4d} | {quality_mark} | {cluster.quality_score:2d}/100 | {cluster.size:4d} | {theme}")

        # 总结
        print("\n" + "="*80)
        print("效果评估总结")
        print("="*80)

        print(f"\n[时间效率]")
        print(f"  Phase 0基线: {baseline_time} 分钟")
        print(f"  Phase 1策略1: {estimated_time_phase1:.1f} 分钟 (节省 {time_saved_percentage:.1f}%)")
        print(f"  Phase 1策略2: {estimated_time_phase1_strategy2:.1f} 分钟 (节省 {time_saved_percentage_strategy2:.1f}%)")

        print(f"\n[质量保证]")
        print(f"  高质量簇（Excellent+Good）: {high_quality_count} 个")
        print(f"  覆盖率: {high_quality_count/len(clusters_A)*100:.1f}%")

        print(f"\n[推荐策略]")
        if estimated_time_phase1_strategy2 <= 120:
            print(f"  [推荐] 采用策略2：优先审核Top 20高分聚类")
            print(f"  - 预计时间: {estimated_time_phase1_strategy2:.1f} 分钟 < 120分钟阈值")
            print(f"  - 节省时间: {time_saved_strategy2:.1f} 分钟 ({time_saved_percentage_strategy2:.1f}%)")
            print(f"  - 预计可选出10-15个有价值的聚类")
        else:
            print(f"  [建议] 可能需要进一步优化评分算法或调整审核策略")

        print("\n" + "="*80)


def analyze_score_distribution():
    """
    分析评分分布的合理性
    """
    print("\n" + "="*80)
    print("评分分布分析")
    print("="*80)

    with ClusterMetaRepository() as repo:
        clusters_A = repo.get_all_clusters('A')
        scored_clusters = [c for c in clusters_A if c.quality_score is not None]

        # 按评分段统计
        score_ranges = {
            '85-100': 0,
            '75-84': 0,
            '65-74': 0,
            '60-64': 0,
            '<60': 0
        }

        for c in scored_clusters:
            score = c.quality_score
            if score >= 85:
                score_ranges['85-100'] += 1
            elif score >= 75:
                score_ranges['75-84'] += 1
            elif score >= 65:
                score_ranges['65-74'] += 1
            elif score >= 60:
                score_ranges['60-64'] += 1
            else:
                score_ranges['<60'] += 1

        print("\n[评分段分布]")
        for range_name, count in score_ranges.items():
            percentage = count / len(scored_clusters) * 100
            bar = '=' * int(percentage / 2)
            print(f"  {range_name:8s}: {count:3d} 个 ({percentage:5.1f}%) {bar}")

        # 大小与评分的关系
        print("\n[大小vs评分分析]")
        size_categories = {
            'small (<15)': [],
            'optimal (15-150)': [],
            'large (>150)': []
        }

        for c in scored_clusters:
            if c.size < 15:
                size_categories['small (<15)'].append(c.quality_score)
            elif c.size <= 150:
                size_categories['optimal (15-150)'].append(c.quality_score)
            else:
                size_categories['large (>150)'].append(c.quality_score)

        for category, scores in size_categories.items():
            if scores:
                avg_score = sum(scores) / len(scores)
                print(f"  {category:20s}: 平均分 {avg_score:.1f}, 数量 {len(scores)}")
            else:
                print(f"  {category:20s}: (无数据)")


def main():
    """主函数"""
    try:
        simulate_review_process()
        analyze_score_distribution()

    except KeyboardInterrupt:
        print("\n\n[WARN] 操作被中断")
        sys.exit(1)

    except Exception as e:
        print(f"\n[ERROR] 验证失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
