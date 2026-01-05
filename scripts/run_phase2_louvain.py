"""
Phase 2B: Louvain聚类（替代K-Means）
使用图社区发现算法生成语义干净的大组聚类

运行方式:
    python scripts/run_phase2_louvain.py [选项]

参数:
    --round-id: 数据轮次ID（默认为1）
    --limit: 限制处理的短语数量，用于测试（0=全部）
    --k-neighbors: K近邻数量（默认20）
    --similarity-threshold: 相似度阈值（默认0.6）
    --resolution: Louvain分辨率参数（默认1.0）

示例:
    # 测试模式（1000条短语）
    python scripts/run_phase2_louvain.py --limit=1000

    # 使用默认参数
    python scripts/run_phase2_louvain.py
"""
import sys
import argparse
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 编码修复
from utils.encoding_fix import setup_encoding
setup_encoding()

from config.settings import OUTPUT_DIR, LOUVAIN_CONFIG
from core.embedding import EmbeddingService
from core.graph_clustering import cluster_phrases_louvain
from storage.repository import PhraseRepository, ClusterMetaRepository
from storage.models import Phrase


def run_phase2_louvain(
    round_id: int = 1,
    limit: int = 0,
    k_neighbors: int = None,
    similarity_threshold: float = None,
    resolution: float = None
):
    """执行Phase 2B Louvain聚类"""
    print("\n" + "="*70)
    print("Phase 2B: Louvain图聚类（替代K-Means）".center(70))
    print("="*70)

    # 1. 从数据库加载短语
    print("\n【步骤1】从数据库加载短语...")
    with PhraseRepository() as repo:
        query = repo.session.query(Phrase)

        if limit > 0:
            query = query.limit(limit)
            print(f"⚠️  测试模式：仅处理前 {limit} 条短语")

        phrases_db = query.all()

        if not phrases_db:
            print("\n❌ 没有待处理的短语！")
            return False

        phrases = [{
            'phrase_id': p.phrase_id,
            'phrase': p.phrase,
            'frequency': p.frequency,
            'volume': p.volume,
        } for p in phrases_db]

        print(f"✓ 加载了 {len(phrases)} 条待聚类短语")

    # 2. 计算Embeddings
    print("\n【步骤2】计算Embeddings...")
    embedding_service = EmbeddingService(use_cache=True)
    embeddings, phrase_ids = embedding_service.embed_phrases_from_db(phrases, round_id)

    assert len(embeddings) == len(phrases), "Embeddings数量不匹配"

    # 3. 准备聚类配置
    print("\n【步骤3】准备Louvain聚类配置...")
    config = LOUVAIN_CONFIG.copy()

    if k_neighbors is not None:
        config['k_neighbors'] = k_neighbors
    if similarity_threshold is not None:
        config['similarity_threshold'] = similarity_threshold
    if resolution is not None:
        config['resolution'] = resolution

    print(f"  K近邻数: {config['k_neighbors']}")
    print(f"  相似度阈值: {config['similarity_threshold']}")
    print(f"  Louvain分辨率: {config['resolution']}")

    # 4. 执行Louvain聚类
    print("\n【步骤4】执行Louvain聚类...")
    cluster_ids, cluster_info, metadata = cluster_phrases_louvain(
        embeddings, phrases, config=config
    )

    # 5. 更新数据库
    print("\n【步骤5】更新数据库...")

    # 5.1 更新phrases表
    print("  更新phrases表...")
    with PhraseRepository() as repo:
        success_count = 0
        for i, phrase_id in enumerate(phrase_ids):
            cluster_id = int(cluster_ids[i])
            if repo.update_cluster_assignment(phrase_id, cluster_id_A=cluster_id):
                success_count += 1

        print(f"  ✓ 已更新 {success_count}/{len(phrase_ids)} 条记录的cluster_id_A")

    # 5.2 保存cluster_meta表
    print("  保存聚类元数据...")
    with ClusterMetaRepository() as repo:
        for cluster_id, info in cluster_info.items():
            example_phrases_str = '; '.join(info['example_phrases'])

            repo.create_or_update_cluster(
                cluster_id=cluster_id,
                cluster_level='A',
                size=info['size'],
                example_phrases=example_phrases_str,
                main_theme=None,  # Phase 2C会用DeepSeek生成
                total_frequency=info['total_frequency']
            )

        print(f"  ✓ 已保存 {len(cluster_info)} 个聚类的元数据")

    # 6. 生成统计报告
    print("\n【步骤6】生成统计报告...")

    report_lines = []
    report_lines.append("="*70)
    report_lines.append("Phase 2B Louvain聚类报告")
    report_lines.append("="*70)
    report_lines.append("")

    # 聚类概况
    report_lines.append("【聚类概况】")
    report_lines.append(f"  总短语数: {len(phrases):,}")
    report_lines.append(f"  有效聚类数: {len(cluster_info)}")
    noise_count = (cluster_ids == -1).sum()
    report_lines.append(f"  噪音点数: {noise_count} ({noise_count/len(phrases)*100:.1f}%)")
    report_lines.append(f"  模块度 (Modularity): {metadata['modularity']:.4f}")
    report_lines.append("")

    # 配置参数
    report_lines.append("【配置参数】")
    report_lines.append(f"  K近邻数: {config['k_neighbors']}")
    report_lines.append(f"  相似度阈值: {config['similarity_threshold']}")
    report_lines.append(f"  Louvain分辨率: {config['resolution']}")
    report_lines.append("")

    # 图统计
    report_lines.append("【图统计信息】")
    graph_stats = metadata['graph_stats']
    report_lines.append(f"  节点数: {graph_stats['n_nodes']}")
    report_lines.append(f"  边数: {graph_stats['n_edges']}")
    report_lines.append(f"  平均度: {graph_stats['avg_degree']:.2f}")
    report_lines.append(f"  图密度: {graph_stats['density']:.6f}")
    report_lines.append("")

    # 聚类大小分布
    sizes = [info['size'] for info in cluster_info.values()]
    report_lines.append("【聚类大小分布】")
    report_lines.append(f"  最小: {min(sizes)}")
    report_lines.append(f"  最大: {max(sizes)}")
    report_lines.append(f"  平均: {sum(sizes)/len(sizes):.1f}")
    report_lines.append(f"  中位数: {sorted(sizes)[len(sizes)//2]}")
    report_lines.append("")

    # Top 20 最大聚类
    report_lines.append("【Top 20 最大聚类】")
    sorted_clusters = sorted(
        cluster_info.items(),
        key=lambda x: x[1]['size'],
        reverse=True
    )

    report_lines.append(f"{'ID':<6} {'大小':<8} {'频次':<10} {'示例短语'}")
    report_lines.append("-" * 70)

    for cluster_id, info in sorted_clusters[:20]:
        examples = ', '.join(info['example_phrases'][:3])
        if len(examples) > 40:
            examples = examples[:37] + '...'
        report_lines.append(
            f"{cluster_id:<6} {info['size']:<8} "
            f"{info['total_frequency']:<10} {examples}"
        )

    report_lines.append("")
    report_lines.append("="*70)
    report_lines.append("✅ 聚类完成！质量评估：")
    if metadata['modularity'] > 0.6:
        report_lines.append("  模块度优秀 (>0.6)：聚类边界非常清晰")
    elif metadata['modularity'] > 0.4:
        report_lines.append("  模块度良好 (>0.4)：聚类质量较好")
    else:
        report_lines.append("  模块度一般：建议调整参数")
    report_lines.append("")
    report_lines.append("下一步:")
    report_lines.append("  1. 查看Top 20聚类，人工评估语义一致性")
    report_lines.append("  2. 如果聚类数量不在60-100范围，运行参数调优")
    report_lines.append("  3. 运行DeepSeek语义标注: python scripts/run_phase2_label_clusters.py")
    report_lines.append("="*70)

    # 输出报告
    report_text = '\n'.join(report_lines)
    print('\n' + report_text)

    # 保存报告
    OUTPUT_DIR.mkdir(exist_ok=True)
    report_file = OUTPUT_DIR / f'phase2b_louvain_report_round{round_id}.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_text)

    print(f"\n💾 报告已保存到: {report_file}")

    # 7. 完成
    print("\n" + "="*70)
    print("✅ Phase 2B Louvain聚类完成！".center(70))
    print("="*70)

    print("\n📊 聚类摘要:")
    print(f"  - 处理短语数: {len(phrases):,}")
    print(f"  - 生成聚类数: {len(cluster_info)}")
    print(f"  - 模块度: {metadata['modularity']:.4f}")

    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Phase 2B: Louvain聚类')
    parser.add_argument('--round-id', type=int, default=1, help='数据轮次ID')
    parser.add_argument('--limit', type=int, default=0, help='限制处理数量（0=全部）')
    parser.add_argument('--k-neighbors', type=int, default=None, help='K近邻数量')
    parser.add_argument('--similarity-threshold', type=float, default=None, help='相似度阈值')
    parser.add_argument('--resolution', type=float, default=None, help='Louvain分辨率参数')

    args = parser.parse_args()

    try:
        success = run_phase2_louvain(
            round_id=args.round_id,
            limit=args.limit,
            k_neighbors=args.k_neighbors,
            similarity_threshold=args.similarity_threshold,
            resolution=args.resolution
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
