"""
Phase 0 - Experiment A: 聚类审核效率测量
Cluster Review Efficiency Measurement

目标：测量从60-100个簇中筛选10-15个所需的时间和准确率

判断标准：
- 时间<60min 且 遗漏率<10% → 不需要聚类质量评分优化
- 时间>120min 或 遗漏率>30% → 需要实施Phase 1.2聚类质量评分

创建日期：2025-12-23
"""

import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.repository import ClusterRepository, PhraseRepository


def display_cluster_summary(cluster_id: int, phrases: List[str], max_display: int = 10) -> None:
    """
    显示簇摘要信息

    Args:
        cluster_id: 簇ID
        phrases: 簇内短语列表
        max_display: 最多显示多少个短语
    """
    print(f"\n{'='*70}")
    print(f"簇 ID: {cluster_id}")
    print(f"大小: {len(phrases)} 个短语")
    print(f"\n代表短语（前{min(max_display, len(phrases))}个）：")
    for i, phrase in enumerate(phrases[:max_display], 1):
        print(f"  {i:2d}. {phrase}")

    if len(phrases) > max_display:
        print(f"  ... 还有 {len(phrases) - max_display} 个短语")


def run_experiment_a() -> Dict:
    """
    执行实验A：聚类审核效率测量

    Returns:
        实验结果字典
    """
    print("\n" + "="*70)
    print("Phase 0 - Experiment A: 聚类审核效率测量")
    print("="*70)

    # 1. 加载大组聚类结果
    print("\n1. 加载大组聚类数据...")

    with PhraseRepository() as phrase_repo:
        # 获取所有已聚类的短语
        phrases_with_cluster = phrase_repo.session.execute(
            "SELECT cluster_id_A, phrase FROM phrases WHERE cluster_id_A IS NOT NULL AND cluster_id_A != -1"
        ).fetchall()

    # 按簇组织
    clusters_data = {}
    for cluster_id, phrase in phrases_with_cluster:
        if cluster_id not in clusters_data:
            clusters_data[cluster_id] = []
        clusters_data[cluster_id].append(phrase)

    cluster_count = len(clusters_data)
    total_phrases = len(phrases_with_cluster)

    print(f"✓ 加载完成")
    print(f"  - 簇数量: {cluster_count}")
    print(f"  - 总短语数: {total_phrases}")

    # 2. 任务说明
    print(f"\n" + "="*70)
    print("📋 实验任务说明")
    print("="*70)
    print("""
任务：从所有聚类簇中筛选出10-15个你认为最有价值的簇

步骤：
1. 接下来会依次显示每个簇的摘要信息
2. 浏览每个簇，判断是否值得深入分析
3. 记录你选中的簇ID
4. 完成后，系统会询问是否有遗漏的重要簇

评估维度：
- 簇大小是否合理（不太大不太小）
- 短语主题是否清晰
- 商业价值潜力
- 是否值得进一步拆分成小组

⏱️  计时将从你按下Enter键开始
""")

    input("准备好了吗？按 Enter 键开始...")

    # 3. 开始计时
    start_time = time.time()

    # 4. 显示簇供审核
    print("\n" + "="*70)
    print("开始浏览聚类簇")
    print("="*70)

    selected_clusters = []

    for idx, (cluster_id, phrases) in enumerate(sorted(clusters_data.items()), 1):
        display_cluster_summary(cluster_id, phrases, max_display=10)

        print(f"\n进度: {idx}/{cluster_count}")
        action = input("操作: [s]选中 / [Enter]跳过 / [q]完成审核: ").strip().lower()

        if action == 's':
            selected_clusters.append(cluster_id)
            print(f"✓ 已选中簇 {cluster_id}")
        elif action == 'q':
            print("\n提前结束审核")
            break

    # 5. 记录结束时间
    end_time = time.time()
    elapsed_minutes = (end_time - start_time) / 60

    print(f"\n✓ 审核完成")
    print(f"  - 选中簇数: {len(selected_clusters)}")
    print(f"  - 用时: {elapsed_minutes:.1f} 分钟")

    # 6. 收集主观感受
    print("\n" + "="*70)
    print("主观评估")
    print("="*70)

    while True:
        subjective = input("审核过程的主观感受 (easy/medium/hard): ").strip().lower()
        if subjective in ['easy', 'medium', 'hard']:
            break
        print("请输入 easy、medium 或 hard")

    # 7. 检查遗漏
    print("\n" + "="*70)
    print("遗漏检查")
    print("="*70)
    print("""
现在请快速回顾一遍所有簇，看是否有遗漏的重要簇。

如果发现有遗漏的簇，请输入簇ID（多个用逗号分隔）。
如果没有遗漏，直接按Enter。
""")

    missed_input = input("遗漏的簇ID（如有）: ").strip()
    missed_clusters = []

    if missed_input:
        try:
            missed_clusters = [int(cid.strip()) for cid in missed_input.split(',')]
        except ValueError:
            print("输入格式错误，将忽略")
            missed_clusters = []

    missed_count = len(missed_clusters)
    missed_rate = missed_count / max(len(selected_clusters) + missed_count, 1)

    # 8. 生成结果
    result = {
        'experiment': 'A',
        'name': '聚类审核效率',
        'timestamp': datetime.now().isoformat(),
        'cluster_count': cluster_count,
        'reviewed_count': idx if 'idx' in locals() else cluster_count,
        'selected_count': len(selected_clusters),
        'selected_clusters': selected_clusters,
        'time_minutes': round(elapsed_minutes, 2),
        'subjective': subjective,
        'missed_count': missed_count,
        'missed_clusters': missed_clusters,
        'missed_rate': round(missed_rate, 3),
    }

    # 9. 判断是否需要优化
    if elapsed_minutes < 60 and missed_rate < 0.1:
        result['recommendation'] = 'ok'
        result['recommendation_detail'] = '审核效率良好，暂不需要聚类质量评分优化'
    elif elapsed_minutes > 120 or missed_rate > 0.3:
        result['recommendation'] = 'need_optimization'
        result['recommendation_detail'] = '审核效率较低，建议实施Phase 1.2聚类质量评分辅助'
    else:
        result['recommendation'] = 'moderate'
        result['recommendation_detail'] = '审核效率中等，可考虑聚类质量评分优化'

    # 10. 保存结果
    output_dir = project_root / 'data' / 'phase0_results'
    output_dir.mkdir(parents=True, exist_ok=True)

    result_file = output_dir / 'experiment_a_result.json'
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 11. 显示结果
    print("\n" + "="*70)
    print("实验A结果")
    print("="*70)
    print(f"簇总数:     {result['cluster_count']}")
    print(f"审核簇数:   {result['reviewed_count']}")
    print(f"选中簇数:   {result['selected_count']}")
    print(f"审核时间:   {result['time_minutes']:.1f} 分钟")
    print(f"主观感受:   {result['subjective']}")
    print(f"遗漏簇数:   {result['missed_count']}")
    print(f"遗漏率:     {result['missed_rate']:.1%}")
    print(f"\n判断结果:   {result['recommendation']}")
    print(f"建议:       {result['recommendation_detail']}")
    print(f"\n结果已保存到: {result_file}")
    print("="*70)

    return result


if __name__ == "__main__":
    try:
        result = run_experiment_a()

        print("\n✅ 实验A完成！")
        print(f"\n📌 下一步：运行实验B（Token覆盖率测量）")
        print(f"   命令: python scripts/phase0_experiment_b_token_coverage.py")

    except KeyboardInterrupt:
        print("\n\n⚠️  实验被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 实验执行出错: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
