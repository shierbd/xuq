"""检查并完成cluster_meta更新"""
import sys
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from storage.repository import PhraseRepository, ClusterMetaRepository
from storage.models import Phrase, ClusterMeta
from collections import Counter, defaultdict

print("\n" + "="*70)
print("检查聚类分布并更新cluster_meta")
print("="*70)

# 1. 统计当前聚类分布
print("\n【步骤1】统计聚类分布...")
with PhraseRepository() as repo:
    phrases = repo.session.query(Phrase).all()
    cluster_counts = Counter([p.cluster_id_A for p in phrases])

    # 按簇组织短语
    cluster_phrases = defaultdict(list)
    for p in phrases:
        cluster_phrases[p.cluster_id_A].append(p)

    print(f"✓ 总短语数: {len(phrases):,}")
    print(f"✓ 聚类数量: {len([c for c in cluster_counts if c != -1])}")
    noise_count = cluster_counts.get(-1, 0)
    print(f"✓ 噪音点数: {noise_count:,} ({noise_count/len(phrases)*100:.1f}%)")

# 2. 检查cluster_meta表
print("\n【步骤2】检查cluster_meta表...")
with ClusterMetaRepository() as repo:
    existing_metas = repo.session.query(ClusterMeta).filter(
        ClusterMeta.cluster_level == 'A'
    ).all()
    existing_ids = {meta.cluster_id for meta in existing_metas}

    print(f"  现有元数据记录: {len(existing_ids)} 条")
    print(f"  现有簇ID: {sorted(existing_ids)}")

# 3. 找出缺失的cluster_meta
needed_ids = set([c for c in cluster_counts.keys() if c != -1])
missing_ids = needed_ids - existing_ids

print(f"\n【步骤3】找出缺失的元数据...")
print(f"  需要的簇ID数: {len(needed_ids)}")
print(f"  缺失的簇ID数: {len(missing_ids)}")
if len(missing_ids) <= 20:
    print(f"  缺失的簇ID: {sorted(missing_ids)}")

# 4. 为缺失的簇创建元数据
if missing_ids:
    print(f"\n【步骤4】创建缺失的元数据...")
    with ClusterMetaRepository() as repo:
        for cluster_id in sorted(missing_ids):
            phrases_in_cluster = cluster_phrases[cluster_id]

            # 计算统计信息
            size = len(phrases_in_cluster)
            total_frequency = sum(p.frequency for p in phrases_in_cluster)

            # 选择示例短语（按频次排序）
            sorted_phrases = sorted(phrases_in_cluster, key=lambda x: x.frequency, reverse=True)
            example_phrases = [p.phrase for p in sorted_phrases[:10]]
            example_phrases_str = '; '.join(example_phrases)

            # 创建元数据
            repo.create_or_update_cluster(
                cluster_id=cluster_id,
                cluster_level='A',
                size=size,
                example_phrases=example_phrases_str,
                main_theme=f"[二次聚类生成]" if cluster_id >= 1001 else None,
                total_frequency=total_frequency
            )

        print(f"  ✓ 已创建 {len(missing_ids)} 条元数据记录")

# 5. 显示最终聚类分布
print(f"\n【步骤5】最终聚类分布...")
print(f"\n前30个最大的簇:")
print(f"{'排名':<5} {'簇ID':<10} {'大小':<8}")
print("-" * 30)

sorted_clusters = sorted(
    [(c, count) for c, count in cluster_counts.items() if c != -1],
    key=lambda x: x[1],
    reverse=True
)

for rank, (cluster_id, count) in enumerate(sorted_clusters[:30], 1):
    print(f"{rank:<5} {cluster_id:<10} {count:<8}")

print("\n" + "="*70)
print("✅ 完成！")
print("="*70)
