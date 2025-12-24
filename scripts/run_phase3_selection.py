"""
Phase 3: 大组筛选
生成聚类分析报告，使用LLM生成主题标签，供人工筛选

运行方式:
    python scripts/run_phase3_selection.py [--skip-llm]

参数:
    --skip-llm: 跳过LLM主题生成（用于测试或API额度不足时）
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

from config.settings import OUTPUT_DIR, CLUSTER_EXAMPLE_PHRASES_COUNT
from ai.client import LLMClient
from storage.repository import ClusterMetaRepository
from storage.models import ClusterMeta
import pandas as pd


def generate_cluster_themes(skip_llm: bool = False):
    """
    为所有聚类生成主题标签

    Args:
        skip_llm: 是否跳过LLM调用（用于测试）

    Returns:
        clusters列表
    """
    print("\n【步骤1】加载聚类元数据...")

    with ClusterMetaRepository() as repo:
        clusters = repo.session.query(ClusterMeta).filter(
            ClusterMeta.cluster_level == 'A'
        ).order_by(ClusterMeta.size.desc()).all()

        if not clusters:
            print("\n❌ 没有找到Level A的聚类！")
            return None

        print(f"✓ 加载了 {len(clusters)} 个聚类")
        print(f"  最大聚类: {max(c.size for c in clusters)} 个短语")
        print(f"  最小聚类: {min(c.size for c in clusters)} 个短语")

    # 生成主题
    print("\n【步骤2】生成聚类主题标签...")

    if skip_llm:
        print("⚠️  跳过LLM主题生成")
        # 使用默认主题
        for cluster in clusters:
            if not cluster.main_theme or cluster.main_theme == "":
                # 从示例短语中提取前3个作为简单主题
                examples = cluster.example_phrases.split('; ')[:3]
                cluster.main_theme = ', '.join(examples)
    else:
        # 使用LLM生成主题
        try:
            llm = LLMClient()

            # 批量处理
            for i, cluster in enumerate(clusters, 1):
                # 解析示例短语
                example_phrases = cluster.example_phrases.split('; ')

                # 调用LLM生成主题
                result = llm.generate_cluster_theme(
                    example_phrases=example_phrases,
                    cluster_size=cluster.size,
                    cluster_id=cluster.cluster_id
                )

                # 更新主题
                cluster.main_theme = result['theme']

                # 显示进度
                if i % 10 == 0:
                    print(f"  进度: {i}/{len(clusters)} ({i/len(clusters)*100:.1f}%)")

            print(f"\n✓ 已生成 {len(clusters)} 个聚类的主题标签")

        except Exception as e:
            print(f"\n❌ LLM主题生成失败: {str(e)}")
            print("  使用--skip-llm参数跳过LLM生成")
            return None

    # 保存主题到数据库
    print("\n【步骤3】保存主题到数据库...")
    with ClusterMetaRepository() as repo:
        for cluster in clusters:
            repo.session.query(ClusterMeta).filter(
                ClusterMeta.cluster_id == cluster.cluster_id,
                ClusterMeta.cluster_level == 'A'
            ).update({
                'main_theme': cluster.main_theme
            })
        repo.session.commit()

    print(f"✓ 已保存 {len(clusters)} 个主题到数据库")

    return clusters


def generate_selection_report(clusters):
    """
    生成聚类筛选报告（HTML + CSV）

    Args:
        clusters: 聚类列表
    """
    print("\n【步骤4】生成筛选报告...")

    # 准备数据
    data = []
    for cluster in clusters:
        # 截断example_phrases以便在表格中显示
        examples = cluster.example_phrases
        if len(examples) > 150:
            examples = examples[:147] + '...'

        data.append({
            'cluster_id': cluster.cluster_id,
            'size': cluster.size,
            'total_frequency': cluster.total_frequency if cluster.total_frequency else 0,
            'main_theme': cluster.main_theme,
            'example_phrases': examples,
            'selection_score': '',  # 空白，供人工填写
        })

    df = pd.DataFrame(data)

    # 生成HTML报告
    OUTPUT_DIR.mkdir(exist_ok=True)
    html_file = OUTPUT_DIR / 'cluster_selection_report.html'

    # 自定义HTML样式
    html_style = """
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th { background-color: #4CAF50; color: white; padding: 12px; text-align: left; }
        td { border: 1px solid #ddd; padding: 8px; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        tr:hover { background-color: #ddd; }
        .stats { background-color: #e7f3fe; padding: 15px; border-left: 6px solid #2196F3; margin-bottom: 20px; }
    </style>
    """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>聚类筛选报告</title>
        {html_style}
    </head>
    <body>
        <h1>Phase 3: 大组聚类筛选报告</h1>
        <div class="stats">
            <h2>统计概览</h2>
            <p><strong>总聚类数:</strong> {len(clusters)}</p>
            <p><strong>总短语数:</strong> {sum(c.size for c in clusters):,}</p>
            <p><strong>最大聚类:</strong> {max(c.size for c in clusters)} 个短语</p>
            <p><strong>平均聚类大小:</strong> {sum(c.size for c in clusters) / len(clusters):.1f} 个短语</p>
        </div>
        <h2>聚类列表</h2>
        {df.to_html(index=False, escape=False)}
        <div style="margin-top: 30px; padding: 15px; background-color: #fff3cd; border-left: 6px solid #ffc107;">
            <h3>📝 下一步操作</h3>
            <ol>
                <li>在 <code>cluster_selection_report.csv</code> 文件中的 <code>selection_score</code> 列填写分数 (1-5)</li>
                <li>评分标准:
                    <ul>
                        <li><strong>5分:</strong> 非常有价值的需求，必须做</li>
                        <li><strong>4分:</strong> 有价值的需求，应该做</li>
                        <li><strong>3分:</strong> 一般需求，可以做</li>
                        <li><strong>2分:</strong> 价值较低，不优先</li>
                        <li><strong>1分:</strong> 无价值或不相关</li>
                    </ul>
                </li>
                <li>选中标准: <code>selection_score >= 4</code> 的聚类将被选中进入 Phase 4</li>
                <li>保存CSV后，运行: <code>python scripts/import_selection.py</code></li>
            </ol>
        </div>
    </body>
    </html>
    """

    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"  ✓ HTML报告: {html_file}")

    # 生成CSV文件
    csv_file = OUTPUT_DIR / 'cluster_selection_report.csv'
    df.to_csv(csv_file, index=False, encoding='utf-8-sig')  # utf-8-sig for Excel
    print(f"  ✓ CSV文件: {csv_file}")

    return html_file, csv_file


def generate_statistics_report(clusters):
    """
    生成统计报告

    Args:
        clusters: 聚类列表
    """
    print("\n【步骤5】生成统计报告...")

    report_lines = []
    report_lines.append("="*70)
    report_lines.append("Phase 3 大组筛选报告 - 统计摘要")
    report_lines.append("="*70)
    report_lines.append("")

    # 基本统计
    report_lines.append("【基本统计】")
    report_lines.append(f"  总聚类数: {len(clusters)}")
    report_lines.append(f"  总短语数: {sum(c.size for c in clusters):,}")
    report_lines.append(f"  总频次: {sum(c.total_frequency or 0 for c in clusters):,}")
    report_lines.append("")

    # 聚类大小分布
    sizes = [c.size for c in clusters]
    report_lines.append("【聚类大小分布】")
    report_lines.append(f"  最小: {min(sizes)}")
    report_lines.append(f"  最大: {max(sizes)}")
    report_lines.append(f"  平均: {sum(sizes)/len(sizes):.1f}")
    report_lines.append(f"  中位数: {sorted(sizes)[len(sizes)//2]}")
    report_lines.append("")

    # Top 30聚类
    report_lines.append("【Top 30 最大聚类】")
    report_lines.append(f"{'排名':<6} {'簇ID':<10} {'大小':<8} {'频次总和':<12} {'主题'}")
    report_lines.append("-" * 70)

    sorted_clusters = sorted(clusters, key=lambda x: x.size, reverse=True)
    for rank, cluster in enumerate(sorted_clusters[:30], 1):
        theme = cluster.main_theme[:40] if cluster.main_theme else "未命名"
        report_lines.append(
            f"{rank:<6} {cluster.cluster_id:<10} {cluster.size:<8} "
            f"{cluster.total_frequency or 0:<12} {theme}"
        )

    report_lines.append("")
    report_lines.append("="*70)
    report_lines.append("下一步: 在CSV中填写selection_score并运行import_selection.py")
    report_lines.append("="*70)

    # 输出报告
    report_text = '\n'.join(report_lines)
    print('\n' + report_text)

    # 保存到文件
    report_file = OUTPUT_DIR / 'phase3_statistics_report.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_text)

    print(f"\n💾 统计报告已保存: {report_file}")

    return report_file


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Phase 3: 大组筛选')
    parser.add_argument(
        '--skip-llm',
        action='store_true',
        help='跳过LLM主题生成（用于测试或API额度不足时）'
    )

    args = parser.parse_args()

    print("\n" + "="*70)
    print("Phase 3: 大组筛选".center(70))
    print("="*70)

    try:
        # 1. 生成聚类主题
        clusters = generate_cluster_themes(skip_llm=args.skip_llm)
        if not clusters:
            return False

        # 2. 生成筛选报告
        html_file, csv_file = generate_selection_report(clusters)

        # 3. 生成统计报告
        stats_file = generate_statistics_report(clusters)

        # 4. 完成
        print("\n" + "="*70)
        print("✅ Phase 3 大组筛选报告生成完成！".center(70))
        print("="*70)

        print("\n📊 输出文件:")
        print(f"  - HTML报告: {html_file}")
        print(f"  - CSV文件: {csv_file}")
        print(f"  - 统计报告: {stats_file}")

        print("\n📌 下一步操作:")
        print("  1. 打开HTML报告浏览聚类")
        print("  2. 在CSV文件的selection_score列填写分数 (1-5)")
        print("  3. 保存CSV后运行: python scripts/import_selection.py")
        print("  4. 选中标准: selection_score >= 4")

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
