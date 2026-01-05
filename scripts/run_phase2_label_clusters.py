"""
Phase 2C: DeepSeek语义标注脚本
为Louvain聚类结果添加语义标签和需求分类

运行方式:
    python scripts/run_phase2_label_clusters.py [选项]

参数:
    --round-id: 数据轮次ID（默认为1）
    --limit: 限制标注的聚类数量（0=全部）
    --min-cluster-size: 仅标注大小>=此值的聚类（默认10）

示例:
    # 标注所有聚类
    python scripts/run_phase2_label_clusters.py

    # 仅标注前20个最大聚类
    python scripts/run_phase2_label_clusters.py --limit=20

    # 仅标注大小>=20的聚类
    python scripts/run_phase2_label_clusters.py --min-cluster-size=20
"""
import sys
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 编码修复
from utils.encoding_fix import setup_encoding
setup_encoding()

from config.settings import OUTPUT_DIR
from core.cluster_labeling import ClusterLabeler
from storage.repository import ClusterMetaRepository, PhraseRepository
from storage.models import ClusterMeta

def run_phase2_label_clusters(
    round_id: int = 1,
    limit: int = 0,
    min_cluster_size: int = 10
):
    """执行Phase 2C DeepSeek语义标注"""
    print("\n" + "="*70)
    print("Phase 2C: DeepSeek语义标注".center(70))
    print("="*70)

    # 1. 从数据库加载聚类
    print("\n【步骤1】从数据库加载聚类...")
    with ClusterMetaRepository() as meta_repo:
        query = meta_repo.session.query(ClusterMeta).filter(
            ClusterMeta.cluster_level == 'A',
            ClusterMeta.size >= min_cluster_size
        ).order_by(ClusterMeta.size.desc())  # 按大小降序

        if limit > 0:
            query = query.limit(limit)
            print(f"⚠️  限制模式：仅标注前 {limit} 个聚类")

        clusters_db = query.all()

        if not clusters_db:
            print("\n❌ 没有待标注的聚类！")
            return False

        print(f"✓ 加载了 {len(clusters_db)} 个待标注聚类")

    # 2. 加载每个聚类的短语
    print("\n【步骤2】加载聚类短语...")
    clusters_to_label = []

    with PhraseRepository() as phrase_repo:
        for cluster in clusters_db:
            # 查询该聚类的所有短语
            phrases_db = phrase_repo.session.query(phrase_repo.model).filter(
                phrase_repo.model.cluster_id_A == cluster.cluster_id
            ).all()

            phrases = [p.phrase for p in phrases_db]

            clusters_to_label.append({
                'cluster_id': cluster.cluster_id,
                'phrases': phrases,
                'size': cluster.size
            })

    print(f"✓ 已加载 {len(clusters_to_label)} 个聚类的短语数据")

    # 3. 初始化DeepSeek标注器
    print("\n【步骤3】初始化DeepSeek标注器...")
    try:
        labeler = ClusterLabeler(provider="deepseek")
        print("✓ DeepSeek标注器初始化成功")
    except Exception as e:
        print(f"\n❌ 标注器初始化失败: {str(e)}")
        return False

    # 4. 批量标注
    print("\n【步骤4】执行批量标注...")
    print(f"  共 {len(clusters_to_label)} 个聚类待标注")

    labeling_results = {}
    success_count = 0
    fail_count = 0

    for i, cluster in enumerate(clusters_to_label, 1):
        cluster_id = cluster['cluster_id']
        phrases = cluster['phrases']

        print(f"\n[{i}/{len(clusters_to_label)}] 标注聚类 {cluster_id} ({cluster['size']} phrases)...")

        try:
            result = labeler.label_cluster(cluster_id, phrases)
            labeling_results[cluster_id] = result

            print(f"  ✓ 标签: {result['llm_label']}")
            print(f"  ✓ 需求类型: {result['primary_demand_type']}")
            print(f"  ✓ 置信度: {result['labeling_confidence']}")

            success_count += 1

        except Exception as e:
            print(f"  ✗ 标注失败: {str(e)}")
            fail_count += 1
            continue

    # 5. 更新数据库
    print("\n【步骤5】更新数据库...")
    update_count = 0

    with ClusterMetaRepository() as repo:
        for cluster_id, result in labeling_results.items():
            # 转换secondary_demand_types为JSON字符串
            import json
            secondary_types_json = json.dumps(result['secondary_demand_types'])

            # 更新cluster_meta表
            success = repo.update_cluster_labeling(
                cluster_id=cluster_id,
                llm_label=result['llm_label'],
                llm_summary=result['llm_summary'],
                primary_demand_type=result['primary_demand_type'],
                secondary_demand_types=secondary_types_json,
                labeling_confidence=result['labeling_confidence']
            )

            if success:
                update_count += 1

    print(f"  ✓ 已更新 {update_count}/{len(labeling_results)} 个聚类的标注数据")

    # 6. 生成标注报告
    print("\n【步骤6】生成标注报告...")

    report_lines = []
    report_lines.append("="*70)
    report_lines.append("Phase 2C DeepSeek语义标注报告")
    report_lines.append("="*70)
    report_lines.append("")

    # 标注概况
    report_lines.append("【标注概况】")
    report_lines.append(f"  待标注聚类数: {len(clusters_to_label)}")
    report_lines.append(f"  标注成功数: {success_count}")
    report_lines.append(f"  标注失败数: {fail_count}")
    report_lines.append(f"  成功率: {success_count/(success_count+fail_count)*100:.1f}%")
    report_lines.append("")

    # 需求类型分布
    report_lines.append("【需求类型分布】")
    type_counts = {}
    for result in labeling_results.values():
        dtype = result['primary_demand_type']
        type_counts[dtype] = type_counts.get(dtype, 0) + 1

    for dtype, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        pct = count / len(labeling_results) * 100
        report_lines.append(f"  {dtype}: {count} ({pct:.1f}%)")
    report_lines.append("")

    # 置信度统计
    confidences = [r['labeling_confidence'] for r in labeling_results.values()]
    if confidences:
        report_lines.append("【置信度统计】")
        report_lines.append(f"  最低: {min(confidences)}")
        report_lines.append(f"  最高: {max(confidences)}")
        report_lines.append(f"  平均: {sum(confidences)/len(confidences):.1f}")
        report_lines.append(f"  中位数: {sorted(confidences)[len(confidences)//2]}")
        report_lines.append("")

    # Top 10 最大聚类及其标注
    report_lines.append("【Top 10 最大聚类标注结果】")
    sorted_clusters = sorted(clusters_to_label, key=lambda x: x['size'], reverse=True)

    for i, cluster in enumerate(sorted_clusters[:10], 1):
        cluster_id = cluster['cluster_id']
        if cluster_id in labeling_results:
            result = labeling_results[cluster_id]
            report_lines.append(f"\n{i}. 聚类 {cluster_id} (size={cluster['size']})")
            report_lines.append(f"   标签: {result['llm_label']}")
            report_lines.append(f"   描述: {result['llm_summary']}")
            report_lines.append(f"   需求类型: {result['primary_demand_type']}")
            report_lines.append(f"   置信度: {result['labeling_confidence']}")

    report_lines.append("")
    report_lines.append("="*70)
    report_lines.append("✅ 语义标注完成！")
    report_lines.append("")
    report_lines.append("下一步:")
    report_lines.append("  1. 检查标注质量，修正明显错误")
    report_lines.append("  2. 在UI中筛选高价值聚类")
    report_lines.append("  3. 运行Phase 3: 人工筛选和评分")
    report_lines.append("="*70)

    # 输出报告
    report_text = '\n'.join(report_lines)
    print('\n' + report_text)

    # 保存报告
    OUTPUT_DIR.mkdir(exist_ok=True)
    report_file = OUTPUT_DIR / f'phase2c_labeling_report_round{round_id}.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_text)

    print(f"\n💾 报告已保存到: {report_file}")

    # 7. 完成
    print("\n" + "="*70)
    print("✅ Phase 2C DeepSeek语义标注完成！".center(70))
    print("="*70)

    print(f"\n📊 标注摘要:")
    print(f"  - 标注聚类数: {success_count}/{len(clusters_to_label)}")
    print(f"  - 平均置信度: {sum(confidences)/len(confidences):.1f}" if confidences else "  - 平均置信度: N/A")

    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Phase 2C: DeepSeek语义标注')
    parser.add_argument('--round-id', type=int, default=1, help='数据轮次ID')
    parser.add_argument('--limit', type=int, default=0, help='限制标注数量（0=全部）')
    parser.add_argument('--min-cluster-size', type=int, default=10, help='最小聚类大小')

    args = parser.parse_args()

    try:
        success = run_phase2_label_clusters(
            round_id=args.round_id,
            limit=args.limit,
            min_cluster_size=args.min_cluster_size
        )
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        sys.exit(1)
    except Exception as e:
        import traceback
        print(f"\n\n❌ 发生错误: {str(e)}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
