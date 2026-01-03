"""
Phase 3: 聚类意图分析
Cluster Intent Analysis Script

功能：
- 对所有聚类簇进行意图分析
- 识别主导意图和意图分布
- 将结果保存到数据库

使用方式：
  python scripts/run_phase3_intent_analysis.py --level A
  python scripts/run_phase3_intent_analysis.py --level A --sample-size 30

创建日期：2025-12-23
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import time
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ========== 编码修复（必须在所有其他导入之前）==========
from utils.encoding_fix import setup_encoding
setup_encoding()
# ======================================================

from storage.repository import PhraseRepository
from storage.models import ClusterMeta
from core.intent_classification import IntentClassifier
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


def run_intent_analysis(level: str = 'A', sample_size: int = 50):
    """
    执行Phase 3意图分析

    Args:
        level: 聚类级别 ('A' or 'B')
        sample_size: 每个簇的抽样大小
    """
    print("\n" + "="*70)
    print(f"Phase 3: 聚类意图分析 (Level {level})")
    print("="*70)

    start_time = time.time()

    # 1. 加载聚类数据
    clusters_data = load_cluster_data(level)

    if not clusters_data:
        print("\n[ERROR] 未找到聚类数据，请先运行Phase 2聚类")
        return

    # 2. 初始化意图分类器
    print(f"\n[步骤1/3] 初始化意图分类器...")
    classifier = IntentClassifier()
    print(f"[OK] 分类器初始化完成")

    # 3. 批量分析意图
    print(f"\n[步骤2/3] 批量分析聚类意图（sample_size={sample_size}）...")

    intent_results = {}
    total_clusters = len(clusters_data)

    for i, (cluster_id, phrases) in enumerate(clusters_data.items(), 1):
        if i % 50 == 0 or i == 1:
            print(f"  进度: {i}/{total_clusters} ({i/total_clusters*100:.1f}%)")

        result = classifier.analyze_cluster_intent(phrases, sample_size=sample_size)
        intent_results[cluster_id] = result

    print(f"[OK] 意图分析完成，共分析 {len(intent_results)} 个簇")

    # 统计意图分布
    intent_counts = {}
    balanced_count = 0

    for result in intent_results.values():
        dominant = result['dominant_intent']
        intent_counts[dominant] = intent_counts.get(dominant, 0) + 1

        if result['is_balanced']:
            balanced_count += 1

    print(f"\n意图分布统计:")
    for intent, count in sorted(intent_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = count / len(intent_results) * 100
        label = classifier.get_intent_label(intent)
        print(f"  {label:12s} ({intent:15s}): {count:3d} 个 ({percentage:5.1f}%)")

    print(f"\n均衡簇数量: {balanced_count} 个 ({balanced_count/len(intent_results)*100:.1f}%)")

    # 4. 保存到数据库
    print(f"\n[步骤3/3] 保存意图分析结果到数据库...")

    with PhraseRepository() as phrase_repo:
        saved_count = 0

        for cluster_id, result in intent_results.items():
            # 查找或创建ClusterMeta
            existing_meta = phrase_repo.session.query(ClusterMeta).filter(
                ClusterMeta.cluster_id == cluster_id,
                ClusterMeta.cluster_level == level
            ).first()

            if existing_meta:
                # 更新现有记录
                existing_meta.dominant_intent = result['dominant_intent']
                existing_meta.dominant_intent_confidence = int(result['dominant_confidence'] * 100)
                existing_meta.intent_distribution = json.dumps(result['intent_distribution'])
                existing_meta.is_intent_balanced = result['is_balanced']

                saved_count += 1

            else:
                # 创建新记录（理论上不应该发生，因为Phase 1应该已创建）
                print(f"[WARN] 簇{cluster_id}没有ClusterMeta记录，跳过")

        phrase_repo.session.commit()

    print(f"[OK] 保存完成，共更新 {saved_count} 条记录")

    # 5. 显示Top 10推荐关注的意图多样性簇
    print(f"\n[推荐] 意图最均衡的聚类簇（Top 10）:")
    print("-"*70)

    balanced_clusters = [
        (cluster_id, result)
        for cluster_id, result in intent_results.items()
        if result['is_balanced']
    ]

    # 按置信度降序排序（均衡度越低，置信度越低，说明意图越分散）
    balanced_clusters.sort(key=lambda x: x[1]['dominant_confidence'])

    for i, (cluster_id, result) in enumerate(balanced_clusters[:10], 1):
        dominant_label = classifier.get_intent_label(result['dominant_intent'])

        print(f"{i:2d}. 簇{cluster_id:4d}: 主导意图={dominant_label} ({result['dominant_confidence']:.0%}), 均衡度=高")

        # 显示意图分布
        intent_dist_str = ", ".join([
            f"{classifier.get_intent_label(intent)}:{pct:.0%}"
            for intent, pct in sorted(result['intent_distribution'].items(), key=lambda x: x[1], reverse=True)
        ])
        print(f"     分布: {intent_dist_str}")

    print("-"*70)

    # 统计信息
    elapsed_time = time.time() - start_time

    print(f"\n" + "="*70)
    print(f"Phase 3 意图分析完成")
    print(f"="*70)
    print(f"总簇数: {len(clusters_data)}")
    print(f"已分析: {len(intent_results)}")
    print(f"均衡簇: {balanced_count} ({balanced_count/len(intent_results)*100:.1f}%)")
    print(f"用时: {elapsed_time:.1f} 秒")
    print(f"="*70)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Phase 3: 聚类意图分析",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 对大组进行意图分析
  python scripts/run_phase3_intent_analysis.py --level A

  # 对大组进行意图分析，每簇抽样30个
  python scripts/run_phase3_intent_analysis.py --level A --sample-size 30

  # 对小组进行意图分析
  python scripts/run_phase3_intent_analysis.py --level B
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
        '--sample-size',
        type=int,
        default=50,
        help='每个簇的抽样大小（默认50）'
    )

    args = parser.parse_args()

    try:
        run_intent_analysis(
            level=args.level,
            sample_size=args.sample_size
        )

    except KeyboardInterrupt:
        print("\n\n[WARN] 操作被中断")
        sys.exit(1)

    except Exception as e:
        print(f"\n[ERROR] 意图分析失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
