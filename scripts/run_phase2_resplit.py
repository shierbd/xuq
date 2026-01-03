"""
Phase 2B: 二次聚类（拆分大簇）
对指定的大簇进行二次聚类，生成更细粒度的子簇

运行方式：
    python scripts/run_phase2_resplit.py --cluster-id 5 [--round-id 1]

参数：
    --cluster-id: 要拆分的簇ID（默认为5）
    --round-id: 数据轮次ID（默认为1）
"""
import sys
import argparse
import numpy as np
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ========== 编码修复（必须在所有其他导入之前）==========
from utils.encoding_fix import setup_encoding
setup_encoding()
# ======================================================

from config.settings import OUTPUT_DIR, CACHE_DIR
from core.clustering import ClusteringEngine
from storage.repository import PhraseRepository, ClusterMetaRepository
from storage.models import Phrase


# 二次聚类专用参数（更aggressive，用于拆分大簇）
RESPLIT_CONFIG = {
    "min_cluster_size": 20,      # 降低最小簇大小
    "min_samples": 1,             # 降低核心点要求
    "metric": "cosine",           # 保持一致
    "cluster_selection_epsilon": 0.0,
    "cluster_selection_method": "leaf",  # 改用leaf方法，更容易产生更多簇
}


def load_embeddings_for_cluster(cluster_id: int, round_id: int = 1):
    """
    加载指定簇的短语及其embeddings

    Args:
        cluster_id: 要拆分的簇ID
        round_id: 轮次ID

    Returns:
        (phrases, embeddings, phrase_ids)
    """
    print(f"\n【步骤1】加载簇 {cluster_id} 的数据...")

    # 1. 从数据库加载该簇的所有短语
    with PhraseRepository() as repo:
        phrases_db = repo.session.query(Phrase).filter(
            Phrase.cluster_id_A == cluster_id
        ).all()

        if not phrases_db:
            print(f"\n❌ 簇 {cluster_id} 中没有找到短语！")
            return None, None, None

        # 转换为字典列表
        phrases = [{
            'phrase_id': p.phrase_id,
            'phrase': p.phrase,
            'frequency': p.frequency,
            'volume': p.volume,
            'seed_word': p.seed_word,
            'source_type': p.source_type,
        } for p in phrases_db]

        phrase_ids = [p['phrase_id'] for p in phrases]

        print(f"✓ 加载了 {len(phrases)} 条短语")
        print(f"  示例短语: {', '.join([p['phrase'] for p in phrases[:5]])}...")

    # 2. 从缓存加载所有embeddings
    cache_file = CACHE_DIR / f'embeddings_round{round_id}.npz'
    if not cache_file.exists():
        print(f"\n❌ Embedding缓存文件不存在: {cache_file}")
        return None, None, None

    print(f"\n📂 加载embedding缓存: {cache_file.name}")
    data = np.load(cache_file, allow_pickle=True)
    cache_dict = data['cache'].item()

    # 3. 提取该簇短语的embeddings
    embeddings = []
    missing_count = 0

    for phrase in phrases:
        import hashlib
        cache_key = hashlib.md5(phrase['phrase'].encode('utf-8')).hexdigest()
        if cache_key in cache_dict:
            embeddings.append(cache_dict[cache_key])
        else:
            missing_count += 1
            print(f"⚠️  缺失embedding: {phrase['phrase']}")

    if missing_count > 0:
        print(f"\n⚠️  警告: {missing_count} 条短语缺失embedding")

    embeddings = np.array(embeddings)
    print(f"✓ 加载embeddings完成: {embeddings.shape}")

    return phrases, embeddings, phrase_ids


def resplit_cluster(cluster_id: int, round_id: int = 1, new_id_start: int = 1001):
    """
    对指定簇进行二次聚类

    Args:
        cluster_id: 要拆分的簇ID
        round_id: 数据轮次ID
        new_id_start: 新簇ID的起始值
    """
    print("\n" + "="*70)
    print(f"Phase 2B: 二次聚类（拆分簇 {cluster_id}）".center(70))
    print("="*70)

    # 1. 加载数据
    phrases, embeddings, phrase_ids = load_embeddings_for_cluster(cluster_id, round_id)

    if phrases is None:
        return False

    # 2. 执行二次聚类
    print(f"\n【步骤2】执行二次聚类...")
    print(f"  使用参数: {RESPLIT_CONFIG}")

    engine = ClusteringEngine(config=RESPLIT_CONFIG, cluster_level='A-resplit')
    labels, clusterer = engine.fit_predict(embeddings)

    # 分析结果
    cluster_info = engine.analyze_clusters(labels, phrases)

    # 3. 重新编号 - 从new_id_start开始
    unique_labels = sorted(set(labels))
    if -1 in unique_labels:
        unique_labels.remove(-1)

    # 创建映射：旧label -> 新cluster_id
    label_to_new_id = {-1: -1}  # 噪音点保持-1
    for idx, old_label in enumerate(unique_labels):
        label_to_new_id[old_label] = new_id_start + idx

    # 应用映射
    new_cluster_ids = np.array([label_to_new_id[label] for label in labels])

    print(f"\n✓ 簇ID重新编号完成:")
    print(f"  原始簇 {cluster_id} -> {len(unique_labels)} 个新簇 (ID: {new_id_start}~{new_id_start+len(unique_labels)-1})")
    print(f"  噪音点: {(new_cluster_ids == -1).sum()} 条")

    # 4. 更新数据库
    print(f"\n【步骤3】更新数据库...")

    # 4.1 更新phrases表
    print(f"\n  更新phrases表...")
    with PhraseRepository() as repo:
        success_count = 0
        for i, phrase_id in enumerate(phrase_ids):
            new_cluster_id = int(new_cluster_ids[i])
            if repo.update_cluster_assignment(phrase_id, cluster_id_A=new_cluster_id):
                success_count += 1

        print(f"  ✓ 已更新 {success_count}/{len(phrase_ids)} 条记录的cluster_id_A")

    # 4.2 删除旧的cluster_meta记录
    print(f"\n  删除旧的聚类元数据（簇 {cluster_id}）...")
    from storage.models import ClusterMeta
    with ClusterMetaRepository() as repo:
        old_meta = repo.session.query(ClusterMeta).filter(
            ClusterMeta.cluster_id == cluster_id,
            ClusterMeta.cluster_level == 'A'
        ).first()
        if old_meta:
            repo.session.delete(old_meta)
            repo.session.commit()
            print(f"  ✓ 已删除簇 {cluster_id} 的元数据")

    # 4.3 保存新的cluster_meta记录
    print(f"\n  保存新聚类元数据...")
    with ClusterMetaRepository() as repo:
        saved_count = 0
        for old_label, info in cluster_info.items():
            new_cluster_id = label_to_new_id[old_label]

            # 准备示例短语
            example_phrases_str = '; '.join(info['example_phrases'])

            # 创建聚类元数据
            repo.create_or_update_cluster(
                cluster_id=new_cluster_id,
                cluster_level='A',
                size=info['size'],
                example_phrases=example_phrases_str,
                main_theme=f"[由簇{cluster_id}拆分]",  # 标记来源
                total_frequency=info['total_frequency']
            )
            saved_count += 1

        print(f"  ✓ 已保存 {saved_count} 个新簇的元数据")

    # 5. 生成统计报告
    print(f"\n【步骤4】生成统计报告...")

    report_lines = []
    report_lines.append("="*70)
    report_lines.append(f"Phase 2B 二次聚类报告 - 簇 {cluster_id}")
    report_lines.append("="*70)
    report_lines.append("")

    report_lines.append("【聚类概况】")
    report_lines.append(f"  原始簇ID: {cluster_id}")
    report_lines.append(f"  总短语数: {len(phrases):,}")
    report_lines.append(f"  新簇数量: {len(cluster_info)}")
    noise_count = (new_cluster_ids == -1).sum()
    report_lines.append(f"  噪音点数: {noise_count} ({noise_count/len(phrases)*100:.1f}%)")
    report_lines.append(f"  新簇ID范围: {new_id_start}~{new_id_start+len(cluster_info)-1}")
    report_lines.append("")

    # 新簇大小分布
    sizes = [info['size'] for info in cluster_info.values()]
    if sizes:
        report_lines.append("【新簇大小分布】")
        report_lines.append(f"  最小: {min(sizes)}")
        report_lines.append(f"  最大: {max(sizes)}")
        report_lines.append(f"  平均: {sum(sizes)/len(sizes):.1f}")
        report_lines.append(f"  中位数: {sorted(sizes)[len(sizes)//2]}")
        report_lines.append("")

    # Top 20 新簇
    report_lines.append("【Top 20 新簇】")
    sorted_clusters = sorted(
        [(label_to_new_id[label], info) for label, info in cluster_info.items()],
        key=lambda x: x[1]['size'],
        reverse=True
    )

    report_lines.append(f"{'排名':<5} {'新簇ID':<10} {'大小':<8} {'频次总和':<12} {'示例短语'}")
    report_lines.append("-" * 70)

    for rank, (new_id, info) in enumerate(sorted_clusters[:20], 1):
        examples = ', '.join(info['example_phrases'][:3])
        if len(examples) > 40:
            examples = examples[:37] + '...'
        report_lines.append(
            f"{rank:<5} {new_id:<10} {info['size']:<8} "
            f"{info['total_frequency']:<12} {examples}"
        )

    report_lines.append("")
    report_lines.append("="*70)
    report_lines.append(f"下一步: 验证整体聚类分布是否合理")
    report_lines.append("="*70)

    # 输出报告
    report_text = '\n'.join(report_lines)
    print('\n' + report_text)

    # 保存报告到文件
    OUTPUT_DIR.mkdir(exist_ok=True)
    report_file = OUTPUT_DIR / f'phase2b_resplit_cluster{cluster_id}_report.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_text)
    print(f"\n💾 报告已保存到: {report_file}")

    # 6. 完成
    print("\n" + "="*70)
    print(f"✅ 簇 {cluster_id} 二次聚类完成！".center(70))
    print("="*70)

    print(f"\n📊 二次聚类摘要:")
    print(f"  - 原始簇: {cluster_id} ({len(phrases):,} 条短语)")
    print(f"  - 新簇数: {len(cluster_info)}")
    print(f"  - 新簇ID范围: {new_id_start}~{new_id_start+len(cluster_info)-1}")
    print(f"  - 噪音点: {noise_count}")
    print(f"  - 统计报告: {report_file}")

    print(f"\n📌 下一步:")
    print(f"  1. 检查所有cluster_id_A的整体分布")
    print(f"  2. 如果分布合理（30-150个簇），进入Phase 3")
    print(f"  3. 如果还有其他大簇需要拆分，重复运行此脚本")

    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Phase 2B: 二次聚类（拆分大簇）')
    parser.add_argument(
        '--cluster-id',
        type=int,
        default=5,
        help='要拆分的簇ID（默认为5）'
    )
    parser.add_argument(
        '--round-id',
        type=int,
        default=1,
        help='数据轮次ID（默认为1）'
    )
    parser.add_argument(
        '--new-id-start',
        type=int,
        default=1001,
        help='新簇ID的起始值（默认为1001）'
    )

    args = parser.parse_args()

    try:
        success = resplit_cluster(
            cluster_id=args.cluster_id,
            round_id=args.round_id,
            new_id_start=args.new_id_start
        )
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
