"""
Phase 2: 大组聚类
对所有短语进行语义聚类，生成60-100个大组

运行方式：
    python scripts/run_phase2_clustering.py [--round-id 1] [--limit 0]

参数：
    --round-id: 数据轮次ID（默认为1）
    --limit: 限制处理的短语数量，用于测试（0=全部）
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

from config.settings import OUTPUT_DIR
from core.embedding import EmbeddingService
from core.clustering import cluster_phrases_large
from storage.repository import PhraseRepository, ClusterMetaRepository
from storage.models import Phrase


def run_phase2_clustering(round_id: int = 1, limit: int = 0):
    """
    执行Phase 2大组聚类

    Args:
        round_id: 数据轮次ID
        limit: 限制处理数量（0=全部）
    """
    print("\n" + "="*70)
    print("Phase 2: 大组聚类".center(70))
    print("="*70)

    # 1. 从数据库加载短语
    print("\n【步骤1】从数据库加载短语...")
    with PhraseRepository() as repo:
        # 获取未处理的短语
        query = repo.session.query(Phrase).filter(
            Phrase.processed_status == 'unseen'
        )

        if limit > 0:
            query = query.limit(limit)
            print(f"⚠️  测试模式：仅处理前 {limit} 条短语")

        phrases_db = query.all()

        if not phrases_db:
            print("\n❌ 没有待处理的短语！")
            return False

        # 转换为字典列表
        phrases = [{
            'phrase_id': p.phrase_id,
            'phrase': p.phrase,
            'frequency': p.frequency,
            'volume': p.volume,
            'seed_word': p.seed_word,
            'source_type': p.source_type,
        } for p in phrases_db]

        print(f"✓ 加载了 {len(phrases)} 条待聚类短语")

    # 2. 计算Embeddings
    print("\n【步骤2】计算Embeddings...")
    embedding_service = EmbeddingService(use_cache=True)
    embeddings, phrase_ids = embedding_service.embed_phrases_from_db(phrases, round_id)

    # 验证
    assert len(embeddings) == len(phrases), "Embeddings数量不匹配"
    assert len(phrase_ids) == len(phrases), "Phrase IDs数量不匹配"

    # 3. 执行大组聚类
    print("\n【步骤3】执行大组聚类...")
    cluster_ids, cluster_info, clusterer = cluster_phrases_large(embeddings, phrases)

    # 4. 更新数据库
    print("\n【步骤4】更新数据库...")

    # 4.1 更新phrases表的cluster_id_A
    print("\n  更新phrases表...")
    with PhraseRepository() as repo:
        success_count = 0
        for i, phrase_id in enumerate(phrase_ids):
            cluster_id = int(cluster_ids[i])
            if repo.update_cluster_assignment(phrase_id, cluster_id_A=cluster_id):
                success_count += 1

        print(f"  ✓ 已更新 {success_count}/{len(phrase_ids)} 条记录的cluster_id_A")

    # 4.2 保存cluster_meta表
    print("\n  保存聚类元数据...")
    with ClusterMetaRepository() as repo:
        for cluster_id, info in cluster_info.items():
            # 准备示例短语（用分号分隔）
            example_phrases_str = '; '.join(info['example_phrases'])

            # 创建或更新聚类元数据
            repo.create_or_update_cluster(
                cluster_id=cluster_id,
                cluster_level='A',
                size=info['size'],
                example_phrases=example_phrases_str,
                main_theme=None,  # Phase 3会用AI生成
                total_frequency=info['total_frequency']
            )

        print(f"  ✓ 已保存 {len(cluster_info)} 个聚类的元数据")

    # 5. 生成统计报告
    print("\n【步骤5】生成统计报告...")

    report_lines = []
    report_lines.append("="*70)
    report_lines.append("Phase 2 大组聚类报告")
    report_lines.append("="*70)
    report_lines.append("")

    report_lines.append("【聚类概况】")
    report_lines.append(f"  总短语数: {len(phrases):,}")
    report_lines.append(f"  聚类数量: {len(cluster_info)}")
    noise_count = (cluster_ids == -1).sum()
    report_lines.append(f"  噪音点数: {noise_count} ({noise_count/len(phrases)*100:.1f}%)")
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

    report_lines.append(f"{'排名':<5} {'聚类ID':<10} {'大小':<8} {'频次总和':<12} {'示例短语'}")
    report_lines.append("-" * 70)

    for rank, (cluster_id, info) in enumerate(sorted_clusters[:20], 1):
        examples = ', '.join(info['example_phrases'][:3])
        if len(examples) > 40:
            examples = examples[:37] + '...'
        report_lines.append(
            f"{rank:<5} {cluster_id:<10} {info['size']:<8} "
            f"{info['total_frequency']:<12} {examples}"
        )

    report_lines.append("")
    report_lines.append("="*70)
    report_lines.append(f"下一步: 运行 Phase 3 生成大组筛选报告")
    report_lines.append("="*70)

    # 输出报告
    report_text = '\n'.join(report_lines)
    print('\n' + report_text)

    # 保存报告到文件
    OUTPUT_DIR.mkdir(exist_ok=True)
    report_file = OUTPUT_DIR / f'phase2_clustering_report_round{round_id}.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_text)
    print(f"\n💾 报告已保存到: {report_file}")

    # 6. 完成
    print("\n" + "="*70)
    print("✅ Phase 2 大组聚类完成！".center(70))
    print("="*70)

    print("\n📊 聚类摘要:")
    print(f"  - 处理短语数: {len(phrases):,}")
    print(f"  - 生成聚类数: {len(cluster_info)}")
    print(f"  - 噪音点数: {noise_count}")
    print(f"  - Embedding缓存: data/cache/embeddings_round{round_id}.npz")
    print(f"  - 统计报告: {report_file}")

    print("\n📌 下一步:")
    print("  运行 Phase 3: python scripts/run_phase3_selection.py")

    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Phase 2: 大组聚类')
    parser.add_argument(
        '--round-id',
        type=int,
        default=1,
        help='数据轮次ID（默认为1）'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=0,
        help='限制处理的短语数量，用于测试（0=全部，默认0）'
    )

    args = parser.parse_args()

    try:
        success = run_phase2_clustering(round_id=args.round_id, limit=args.limit)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
