"""
Phase 1: 聚类质量评分
Cluster Quality Scoring Script

功能：
- 对所有聚类簇进行自动质量评分
- 可选择性地使用LLM进行预评估
- 将评分结果保存到数据库

使用方式：
  python scripts/run_phase1_scoring.py --level A
  python scripts/run_phase1_scoring.py --level A --with-llm --top 20

创建日期：2025-12-23
"""

import io
import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.repository import PhraseRepository
from storage.models import ClusterMeta, Phrase
from core.cluster_scoring import ClusterScorer
from core.cluster_llm_assessment import ClusterLLMAssessor
from sqlalchemy import text


def load_cluster_data(level: str = 'A') -> Dict[int, List[str]]:
    """
    从数据库加载聚类数据

    Args:
        level: 聚类级别 ('A' or 'B')

    Returns:
        {cluster_id: [phrases]}
    """
    print(f"\n加载聚类数据 (Level {level})...")

    with PhraseRepository() as phrase_repo:
        if level == 'A':
            phrases_with_cluster = phrase_repo.session.execute(
                text("""
                SELECT cluster_id_A, phrase
                FROM phrases
                WHERE cluster_id_A IS NOT NULL AND cluster_id_A != -1
                """)
            ).fetchall()
        else:
            phrases_with_cluster = phrase_repo.session.execute(
                text("""
                SELECT cluster_id_B, phrase
                FROM phrases
                WHERE cluster_id_B IS NOT NULL AND cluster_id_B != -1
                """)
            ).fetchall()

    # 组织数据
    clusters_data = {}
    for cluster_id, phrase in phrases_with_cluster:
        if cluster_id not in clusters_data:
            clusters_data[cluster_id] = []
        clusters_data[cluster_id].append(phrase)

    print(f"[OK] 加载了 {len(clusters_data)} 个聚类簇")

    return clusters_data


def run_phase1_scoring(level: str = 'A',
                       with_llm: bool = False,
                       llm_top_n: int = 20):
    """
    执行Phase 1质量评分

    Args:
        level: 聚类级别 ('A' or 'B')
        with_llm: 是否使用LLM评估
        llm_top_n: LLM评估的簇数量（仅评估得分最高的N个）
    """
    print("\n" + "="*70)
    print(f"Phase 1: 聚类质量评分 (Level {level})")
    print("="*70)

    start_time = time.time()

    # 1. 加载聚类数据
    clusters_data = load_cluster_data(level)

    if not clusters_data:
        print("\n[ERROR] 未找到聚类数据，请先运行Phase 2聚类")
        return

    # 2. 执行自动评分
    print(f"\n[步骤1/3] 执行自动质量评分...")

    scorer = ClusterScorer()
    scores = scorer.score_multiple_clusters(clusters_data)

    print(f"[OK] 自动评分完成，共评分 {len(scores)} 个簇")

    # 显示评分分布
    excellent_count = sum(1 for s in scores.values() if s['quality_level'] == 'excellent')
    good_count = sum(1 for s in scores.values() if s['quality_level'] == 'good')
    fair_count = sum(1 for s in scores.values() if s['quality_level'] == 'fair')
    poor_count = sum(1 for s in scores.values() if s['quality_level'] == 'poor')

    print(f"\n质量等级分布:")
    print(f"  [Excellent] {excellent_count} 个 ({excellent_count/len(scores)*100:.1f}%)")
    print(f"  [Good]      {good_count} 个 ({good_count/len(scores)*100:.1f}%)")
    print(f"  [Fair]      {fair_count} 个 ({fair_count/len(scores)*100:.1f}%)")
    print(f"  [Poor]      {poor_count} 个 ({poor_count/len(scores)*100:.1f}%)")

    # 3. LLM评估（可选）
    llm_assessments = {}

    if with_llm:
        print(f"\n[步骤2/3] 执行LLM预评估（前{llm_top_n}个高分簇）...")

        # 获取得分最高的N个簇
        top_clusters = scorer.get_top_clusters(clusters_data, top_n=llm_top_n)
        top_cluster_ids = [cluster_id for cluster_id, _ in top_clusters]

        # 过滤clusters_data
        top_clusters_data = {
            cluster_id: phrases
            for cluster_id, phrases in clusters_data.items()
            if cluster_id in top_cluster_ids
        }

        # 执行LLM评估
        assessor = ClusterLLMAssessor()
        llm_assessments = assessor.batch_assess_clusters(top_clusters_data)

        recommended_count = sum(1 for a in llm_assessments.values() if a['recommended'])
        print(f"\n[OK] LLM评估完成，{recommended_count}/{len(llm_assessments)} 个簇被推荐")

    else:
        print(f"\n[步骤2/3] 跳过LLM评估（使用 --with-llm 启用）")

    # 4. 保存到数据库
    print(f"\n[步骤3/3] 保存评分结果到数据库...")

    with PhraseRepository() as phrase_repo:
        saved_count = 0

        for cluster_id, score_dict in scores.items():
            # 检查ClusterMeta是否存在
            existing_meta = phrase_repo.session.query(ClusterMeta).filter(
                ClusterMeta.cluster_id == cluster_id,
                ClusterMeta.cluster_level == level
            ).first()

            if existing_meta:
                # 更新现有记录
                existing_meta.quality_score = int(score_dict['total_score'])
                existing_meta.size_score = int(score_dict['size_score'] * 100)
                existing_meta.diversity_score = int(score_dict['diversity_score'] * 100)
                existing_meta.consistency_score = int(score_dict['consistency_score'] * 100)
                existing_meta.quality_level = score_dict['quality_level']

                # LLM评估结果（如果有）
                if cluster_id in llm_assessments:
                    llm_result = llm_assessments[cluster_id]
                    existing_meta.llm_summary = llm_result['summary']
                    existing_meta.llm_value_assessment = llm_result['value_assessment']

                saved_count += 1

            else:
                # 创建新记录
                new_meta = ClusterMeta(
                    cluster_id=cluster_id,
                    cluster_level=level,
                    size=score_dict['cluster_size'],
                    quality_score=int(score_dict['total_score']),
                    size_score=int(score_dict['size_score'] * 100),
                    diversity_score=int(score_dict['diversity_score'] * 100),
                    consistency_score=int(score_dict['consistency_score'] * 100),
                    quality_level=score_dict['quality_level']
                )

                # LLM评估结果（如果有）
                if cluster_id in llm_assessments:
                    llm_result = llm_assessments[cluster_id]
                    new_meta.llm_summary = llm_result['summary']
                    new_meta.llm_value_assessment = llm_result['value_assessment']

                phrase_repo.session.add(new_meta)
                saved_count += 1

        phrase_repo.session.commit()

    print(f"[OK] 保存完成，共更新/创建 {saved_count} 条记录")

    # 5. 显示推荐簇
    print(f"\n[推荐] 推荐关注的聚类簇（Top 10）:")
    print("-"*70)

    top_10 = scorer.get_top_clusters(clusters_data, top_n=10)

    for i, (cluster_id, score_dict) in enumerate(top_10, 1):
        quality_emoji = {
            'excellent': '[★★★]',
            'good': '[★★ ]',
            'fair': '[★  ]',
            'poor': '[   ]'
        }.get(score_dict['quality_level'], '[???]')

        print(f"{i:2d}. 簇{cluster_id:4d}: {quality_emoji} {score_dict['total_score']:.1f}/100 "
              f"(大小={score_dict['cluster_size']:3d}, "
              f"多样性={score_dict['diversity_score']:.2f}, "
              f"一致性={score_dict['consistency_score']:.2f})")

        # 如果有LLM摘要，显示
        if cluster_id in llm_assessments:
            llm_result = llm_assessments[cluster_id]
            print(f"     [LLM] {llm_result['summary']}")

    print("-"*70)

    # 统计信息
    elapsed_time = time.time() - start_time

    print(f"\n" + "="*70)
    print(f"Phase 1 评分完成")
    print(f"="*70)
    print(f"总簇数: {len(clusters_data)}")
    print(f"已评分: {len(scores)}")
    print(f"LLM评估: {len(llm_assessments)}")
    print(f"用时: {elapsed_time:.1f} 秒")
    print(f"="*70)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Phase 1: 聚类质量评分",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 对大组进行评分（不使用LLM）
  python scripts/run_phase1_scoring.py --level A

  # 对大组进行评分，并对前20个高分簇使用LLM评估
  python scripts/run_phase1_scoring.py --level A --with-llm --top 20

  # 对小组进行评分
  python scripts/run_phase1_scoring.py --level B
        """
    )

    parser.add_argument(
        '--level',
        type=str,
        choices=['A', 'B'],
        default='A',
        help='聚类级别：A (大组) 或 B (小组)'
    )

    parser.add_argument(
        '--with-llm',
        action='store_true',
        help='使用LLM进行预评估'
    )

    parser.add_argument(
        '--top',
        type=int,
        default=20,
        help='LLM评估的簇数量（默认20）'
    )

    args = parser.parse_args()

    try:
        run_phase1_scoring(
            level=args.level,
            with_llm=args.with_llm,
            llm_top_n=args.top
        )

    except KeyboardInterrupt:
        print("\n\n[WARN] 操作被中断")
        sys.exit(1)

    except Exception as e:
        print(f"\n[ERROR] 评分失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
