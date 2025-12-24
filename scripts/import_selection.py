"""
Phase 3B: 导入筛选结果
读取人工评分的CSV文件，更新数据库中的selection_score和is_selected字段

运行方式:
    python scripts/import_selection.py [--csv-file path/to/csv]

参数:
    --csv-file: CSV文件路径（默认为data/output/cluster_selection_report.csv）
"""
import sys
import argparse
from pathlib import Path

# 设置UTF-8编码输出（Windows兼容）
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import OUTPUT_DIR, CLUSTER_SELECTION_THRESHOLD
from storage.repository import ClusterMetaRepository
from storage.models import ClusterMeta
import pandas as pd


def validate_csv_file(csv_file: Path) -> bool:
    """
    验证CSV文件格式

    Args:
        csv_file: CSV文件路径

    Returns:
        是否验证通过
    """
    if not csv_file.exists():
        print(f"❌ CSV文件不存在: {csv_file}")
        return False

    try:
        df = pd.read_csv(csv_file, encoding='utf-8-sig')
    except Exception as e:
        print(f"❌ 读取CSV文件失败: {str(e)}")
        return False

    # 检查必需列
    required_columns = ['cluster_id', 'selection_score']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"❌ CSV文件缺少必需列: {missing_columns}")
        return False

    # 检查是否有评分
    if df['selection_score'].isna().all():
        print("⚠️  警告: selection_score列全部为空，没有任何评分")
        return False

    return True


def import_selections(csv_file: Path):
    """
    导入筛选结果到数据库

    Args:
        csv_file: CSV文件路径

    Returns:
        是否成功
    """
    print("\n【步骤1】读取CSV文件...")
    print(f"  文件: {csv_file}")

    # 读取CSV
    df = pd.read_csv(csv_file, encoding='utf-8-sig')
    print(f"✓ 读取了 {len(df)} 条记录")

    # 统计评分情况
    scored_count = df['selection_score'].notna().sum()
    print(f"  已评分: {scored_count}/{len(df)} ({scored_count/len(df)*100:.1f}%)")

    if scored_count == 0:
        print("\n❌ 没有任何评分，无法导入")
        return False

    # 过滤出已评分的记录
    df_scored = df[df['selection_score'].notna()].copy()

    # 转换selection_score为整数
    try:
        df_scored['selection_score'] = df_scored['selection_score'].astype(int)
    except ValueError as e:
        print(f"\n❌ selection_score必须是整数: {str(e)}")
        return False

    # 验证评分范围
    invalid_scores = df_scored[
        (df_scored['selection_score'] < 1) | (df_scored['selection_score'] > 5)
    ]
    if len(invalid_scores) > 0:
        print(f"\n⚠️  警告: {len(invalid_scores)} 条记录的评分不在1-5范围内")
        print("  这些记录将被跳过:")
        for _, row in invalid_scores.iterrows():
            print(f"    簇ID {row['cluster_id']}: {row['selection_score']}")
        df_scored = df_scored[
            (df_scored['selection_score'] >= 1) & (df_scored['selection_score'] <= 5)
        ]

    # 计算is_selected
    df_scored['is_selected'] = df_scored['selection_score'] >= CLUSTER_SELECTION_THRESHOLD

    selected_count = df_scored['is_selected'].sum()
    print(f"\n  选中标准: selection_score >= {CLUSTER_SELECTION_THRESHOLD}")
    print(f"  将被选中: {selected_count}/{len(df_scored)} ({selected_count/len(df_scored)*100:.1f}%)")

    # 分数分布
    print(f"\n  评分分布:")
    for score in range(1, 6):
        count = (df_scored['selection_score'] == score).sum()
        print(f"    {score}分: {count} 个聚类")

    # 更新数据库
    print("\n【步骤2】更新数据库...")

    with ClusterMetaRepository() as repo:
        updated_count = 0
        not_found_count = 0

        for _, row in df_scored.iterrows():
            cluster_id = int(row['cluster_id'])
            selection_score = int(row['selection_score'])
            is_selected = bool(row['is_selected'])

            # 查找聚类
            cluster = repo.session.query(ClusterMeta).filter(
                ClusterMeta.cluster_id == cluster_id,
                ClusterMeta.cluster_level == 'A'
            ).first()

            if cluster:
                cluster.selection_score = selection_score
                cluster.is_selected = is_selected
                updated_count += 1
            else:
                not_found_count += 1
                print(f"  ⚠️  簇ID {cluster_id} 在数据库中不存在")

        repo.session.commit()

    print(f"\n✓ 更新完成")
    print(f"  成功更新: {updated_count} 个聚类")
    if not_found_count > 0:
        print(f"  未找到: {not_found_count} 个聚类")

    return True


def generate_summary_report():
    """
    生成筛选摘要报告
    """
    print("\n【步骤3】生成筛选摘要...")

    with ClusterMetaRepository() as repo:
        all_clusters = repo.session.query(ClusterMeta).filter(
            ClusterMeta.cluster_level == 'A'
        ).all()

        # 统计
        total_count = len(all_clusters)
        scored_clusters = [c for c in all_clusters if c.selection_score is not None]
        scored_count = len(scored_clusters)
        selected_clusters = [c for c in all_clusters if c.is_selected]
        selected_count = len(selected_clusters)

        # 选中聚类的统计
        if selected_clusters:
            selected_phrases = sum(c.size for c in selected_clusters)
            selected_frequency = sum(c.total_frequency or 0 for c in selected_clusters)
        else:
            selected_phrases = 0
            selected_frequency = 0

    report_lines = []
    report_lines.append("="*70)
    report_lines.append("Phase 3 筛选结果摘要")
    report_lines.append("="*70)
    report_lines.append("")

    report_lines.append("【筛选统计】")
    report_lines.append(f"  总聚类数: {total_count}")
    report_lines.append(f"  已评分数: {scored_count} ({scored_count/total_count*100:.1f}%)")
    report_lines.append(f"  选中数量: {selected_count} ({selected_count/total_count*100:.1f}%)")
    report_lines.append("")

    report_lines.append("【选中聚类统计】")
    report_lines.append(f"  总短语数: {selected_phrases:,}")
    report_lines.append(f"  总频次: {selected_frequency:,}")
    if selected_clusters:
        report_lines.append(f"  平均大小: {selected_phrases/selected_count:.1f}")
    report_lines.append("")

    # 评分分布
    if scored_clusters:
        report_lines.append("【评分分布】")
        for score in range(1, 6):
            count = sum(1 for c in scored_clusters if c.selection_score == score)
            report_lines.append(f"  {score}分: {count} 个聚类")
        report_lines.append("")

    # 选中聚类列表
    if selected_clusters:
        report_lines.append("【选中聚类列表】")
        report_lines.append(f"{'簇ID':<10} {'大小':<8} {'频次':<12} {'评分':<6} {'主题'}")
        report_lines.append("-" * 70)

        # 按评分和大小排序
        selected_sorted = sorted(
            selected_clusters,
            key=lambda x: (x.selection_score or 0, x.size),
            reverse=True
        )

        for cluster in selected_sorted:
            theme = cluster.main_theme[:40] if cluster.main_theme else "未命名"
            report_lines.append(
                f"{cluster.cluster_id:<10} {cluster.size:<8} "
                f"{cluster.total_frequency or 0:<12} {cluster.selection_score:<6} {theme}"
            )
        report_lines.append("")

    report_lines.append("="*70)
    report_lines.append("下一步: 运行 Phase 4 进行小组聚类和需求卡片生成")
    report_lines.append("  python scripts/run_phase4_demands.py")
    report_lines.append("="*70)

    # 输出报告
    report_text = '\n'.join(report_lines)
    print('\n' + report_text)

    # 保存到文件
    OUTPUT_DIR.mkdir(exist_ok=True)
    report_file = OUTPUT_DIR / 'phase3_selection_summary.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_text)

    print(f"\n💾 摘要报告已保存: {report_file}")

    return report_file


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Phase 3B: 导入筛选结果')
    parser.add_argument(
        '--csv-file',
        type=str,
        default=None,
        help='CSV文件路径（默认为data/output/cluster_selection_report.csv）'
    )

    args = parser.parse_args()

    print("\n" + "="*70)
    print("Phase 3B: 导入筛选结果".center(70))
    print("="*70)

    try:
        # 确定CSV文件路径
        if args.csv_file:
            csv_file = Path(args.csv_file)
        else:
            csv_file = OUTPUT_DIR / 'cluster_selection_report.csv'

        # 验证文件
        if not validate_csv_file(csv_file):
            return False

        # 导入筛选结果
        if not import_selections(csv_file):
            return False

        # 生成摘要报告
        generate_summary_report()

        # 完成
        print("\n" + "="*70)
        print("✅ 筛选结果导入完成！".center(70))
        print("="*70)

        print("\n📌 下一步:")
        print("  运行 Phase 4: python scripts/run_phase4_demands.py")

        return True

    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        return False
    except Exception as e:
        print(f"\n\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
