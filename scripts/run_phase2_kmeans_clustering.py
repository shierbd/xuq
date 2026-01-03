"""
使用K-Means替代HDBSCAN进行聚类
基于深度分析报告的推荐方案
"""
import sys
from pathlib import Path
import numpy as np
from sklearn.cluster import KMeans, MiniBatchKMeans
from sklearn.preprocessing import normalize
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score

# 添加项目根目录
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 编码修复
from utils.encoding_fix import setup_encoding
setup_encoding()

from config.settings import CACHE_DIR, OUTPUT_DIR
from storage.repository import PhraseRepository, ClusterMetaRepository
from storage.models import Phrase


def load_embeddings_and_phrases(round_id=1):
    """加载embeddings和短语信息（从数据库）"""
    print(f"\n加载数据...")

    # 1. 从数据库加载短语
    with PhraseRepository() as repo:
        # 加载所有短语（不过滤状态，因为可能已被HDBSCAN处理过）
        phrases_db = repo.session.query(Phrase).all()

        phrases = [{
            'phrase_id': p.phrase_id,
            'phrase': p.phrase,
            'frequency': p.frequency,
            'volume': p.volume,
        } for p in phrases_db]

    print(f"  从数据库加载了 {len(phrases):,} 条短语")

    # 2. 从缓存加载embeddings
    cache_file = CACHE_DIR / f"embeddings_round{round_id}.npz"
    print(f"  从缓存加载embeddings: {cache_file.name}")

    import hashlib
    data = np.load(cache_file, allow_pickle=True)
    cache_dict = data['cache'].item()

    # 3. 按照phrase顺序构建embeddings矩阵
    embeddings = []
    valid_phrases = []

    for p in phrases:
        # 计算缓存键（与EmbeddingService._get_cache_key保持一致）
        cache_key = hashlib.md5(p['phrase'].encode('utf-8')).hexdigest()
        if cache_key in cache_dict:
            embeddings.append(cache_dict[cache_key])
            valid_phrases.append(p)

    embeddings = np.array(embeddings)

    print(f"  成功匹配 {len(valid_phrases):,}/{len(phrases):,} 条短语的embeddings")
    print(f"  Embeddings形状: {embeddings.shape}")

    return embeddings, valid_phrases


def find_optimal_k(embeddings_norm, k_values, sample_size=10000):
    """找到最优K值"""
    print("\n【寻找最优K值】")

    # 采样加速
    if len(embeddings_norm) > sample_size:
        print(f"  使用{sample_size}个样本快速评估...")
        indices = np.random.choice(len(embeddings_norm), sample_size, replace=False)
        sample_embeddings = embeddings_norm[indices]
    else:
        sample_embeddings = embeddings_norm

    results = []

    for k in k_values:
        print(f"\n  测试 K={k}...")

        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=300)
        labels = kmeans.fit_predict(sample_embeddings)

        # 计算评估指标
        silhouette = silhouette_score(sample_embeddings, labels)
        davies_bouldin = davies_bouldin_score(sample_embeddings, labels)
        calinski_harabasz = calinski_harabasz_score(sample_embeddings, labels)

        print(f"    轮廓系数: {silhouette:.4f}")
        print(f"    Davies-Bouldin: {davies_bouldin:.4f} (越小越好)")
        print(f"    Calinski-Harabasz: {calinski_harabasz:.2f} (越大越好)")

        results.append({
            'k': k,
            'silhouette': silhouette,
            'davies_bouldin': davies_bouldin,
            'calinski_harabasz': calinski_harabasz
        })

    # 选择最优K
    best_result = max(results, key=lambda x: x['silhouette'])
    print(f"\n  ✓ 最优K值: {best_result['k']} (轮廓系数={best_result['silhouette']:.4f})")

    return best_result['k'], results


def run_kmeans_clustering(k, embeddings_norm, use_minibatch=True):
    """执行K-Means聚类"""
    print(f"\n【执行K-Means聚类】")
    print(f"  K={k}, 样本数={len(embeddings_norm):,}")

    if use_minibatch and len(embeddings_norm) > 50000:
        print(f"  使用MiniBatch K-Means加速大数据集聚类...")
        kmeans = MiniBatchKMeans(
            n_clusters=k,
            random_state=42,
            batch_size=1024,
            max_iter=100,
            n_init=10,
            verbose=1
        )
    else:
        print(f"  使用标准K-Means...")
        kmeans = KMeans(
            n_clusters=k,
            random_state=42,
            n_init=20,
            max_iter=300,
            verbose=1
        )

    cluster_ids = kmeans.fit_predict(embeddings_norm)

    print(f"\n  ✓ 聚类完成！")

    # 统计聚类大小
    unique, counts = np.unique(cluster_ids, return_counts=True)
    print(f"\n  聚类数量: {len(unique)}")
    print(f"  最小聚类: {counts.min()}")
    print(f"  最大聚类: {counts.max()}")
    print(f"  平均聚类: {counts.mean():.1f}")
    print(f"  中位聚类: {np.median(counts):.1f}")

    return cluster_ids, kmeans


def update_database(cluster_ids, phrases, round_id=1):
    """更新数据库"""
    print("\n【更新数据库】")

    # 1. 更新phrases表
    print("\n  更新phrases表的cluster_id_A...")
    with PhraseRepository() as repo:
        success_count = 0
        for i, phrase in enumerate(phrases):
            phrase_id = phrase['phrase_id']
            cluster_id = int(cluster_ids[i])

            if repo.update_cluster_assignment(phrase_id, cluster_id_A=cluster_id):
                success_count += 1

        print(f"  ✓ 已更新 {success_count}/{len(phrases)} 条记录")

    # 2. 保存cluster_meta表
    print("\n  保存聚类元数据...")

    # 统计每个聚类
    cluster_info = {}
    for cluster_id in set(cluster_ids):
        indices = np.where(cluster_ids == cluster_id)[0]
        cluster_phrases = [phrases[i] for i in indices]

        # 统计
        total_frequency = sum(p.get('frequency', 1) for p in cluster_phrases)
        total_volume = sum(p.get('volume', 0) for p in cluster_phrases)

        # 示例短语（按频次排序）
        sorted_phrases = sorted(cluster_phrases, key=lambda x: x.get('frequency', 1), reverse=True)
        example_phrases = [p['phrase'] for p in sorted_phrases[:10]]

        cluster_info[cluster_id] = {
            'size': len(cluster_phrases),
            'total_frequency': total_frequency,
            'total_volume': total_volume,
            'example_phrases': example_phrases
        }

    with ClusterMetaRepository() as repo:
        for cluster_id, info in cluster_info.items():
            example_phrases_str = '; '.join(info['example_phrases'])

            repo.create_or_update_cluster(
                cluster_id=cluster_id,
                cluster_level='A',
                size=info['size'],
                example_phrases=example_phrases_str,
                main_theme=None,
                total_frequency=info['total_frequency']
            )

        print(f"  ✓ 已保存 {len(cluster_info)} 个聚类的元数据")

    return cluster_info


def generate_report(k, cluster_ids, cluster_info, eval_results, output_file):
    """生成聚类报告"""
    print("\n【生成聚类报告】")

    lines = []
    lines.append("="*70)
    lines.append("K-Means聚类报告 (替代HDBSCAN)")
    lines.append("="*70)
    lines.append("")

    lines.append("【聚类概况】")
    lines.append(f"  算法: K-Means")
    lines.append(f"  聚类数(K): {k}")
    lines.append(f"  总样本数: {len(cluster_ids):,}")
    lines.append(f"  噪音点数: 0 (K-Means无噪音点)")
    lines.append("")

    lines.append("【聚类大小分布】")
    sizes = [info['size'] for info in cluster_info.values()]
    lines.append(f"  最小: {min(sizes)}")
    lines.append(f"  最大: {max(sizes)}")
    lines.append(f"  平均: {sum(sizes)/len(sizes):.1f}")
    lines.append(f"  中位数: {sorted(sizes)[len(sizes)//2]}")
    lines.append("")

    lines.append("【K值评估结果】")
    lines.append(f"{'K值':<10} {'轮廓系数':<12} {'DB指数':<12} {'CH指数':<12}")
    lines.append("-" * 70)
    for r in eval_results:
        lines.append(f"{r['k']:<10} {r['silhouette']:<12.4f} {r['davies_bouldin']:<12.4f} {r['calinski_harabasz']:<12.2f}")
    lines.append("")

    lines.append("【Top 20 最大聚类】")
    sorted_clusters = sorted(cluster_info.items(), key=lambda x: x[1]['size'], reverse=True)
    lines.append(f"{'排名':<5} {'聚类ID':<10} {'大小':<8} {'频次总和':<12} {'示例短语'}")
    lines.append("-" * 70)

    for rank, (cluster_id, info) in enumerate(sorted_clusters[:20], 1):
        examples = ', '.join(info['example_phrases'][:3])
        if len(examples) > 40:
            examples = examples[:37] + '...'
        lines.append(f"{rank:<5} {cluster_id:<10} {info['size']:<8} {info['total_frequency']:<12} {examples}")

    lines.append("")
    lines.append("="*70)
    lines.append("说明:")
    lines.append("  - 轮廓系数: 越接近1越好，>0.2为可接受")
    lines.append("  - DB指数: 越小越好")
    lines.append("  - CH指数: 越大越好")
    lines.append("")
    lines.append("下一步: 运行 Phase 3 生成大组筛选报告")
    lines.append("="*70)

    report_text = '\n'.join(lines)
    print(report_text)

    # 保存报告
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_text)

    print(f"\n💾 报告已保存: {output_file}")


def main():
    """主函数"""
    print("\n" + "="*70)
    print("K-Means聚类 (替代HDBSCAN)".center(70))
    print("="*70)

    round_id = 1

    # 1. 加载数据
    print("\n【步骤1】加载数据...")
    embeddings, phrases = load_embeddings_and_phrases(round_id)

    # 2. 归一化
    print("\n【步骤2】归一化向量...")
    embeddings_norm = normalize(embeddings, norm='l2')

    # 3. 寻找最优K
    k_values = [60, 70, 80, 90, 100]
    optimal_k, eval_results = find_optimal_k(embeddings_norm, k_values, sample_size=10000)

    # 4. 执行聚类
    cluster_ids, kmeans = run_kmeans_clustering(optimal_k, embeddings_norm, use_minibatch=True)

    # 5. 更新数据库
    cluster_info = update_database(cluster_ids, phrases, round_id)

    # 6. 生成报告
    OUTPUT_DIR.mkdir(exist_ok=True)
    report_file = OUTPUT_DIR / f'phase2_kmeans_clustering_report_round{round_id}.txt'
    generate_report(optimal_k, cluster_ids, cluster_info, eval_results, report_file)

    print("\n" + "="*70)
    print("✅ K-Means聚类完成！".center(70))
    print("="*70)

    print("\n📊 对比HDBSCAN:")
    print("  HDBSCAN: 2个聚类, 58%噪音, 6小时+")
    print(f"  K-Means: {len(cluster_info)}个聚类, 0%噪音, <1小时")

    print("\n📌 下一步:")
    print("  运行 Phase 3: python scripts/run_phase3_selection.py")


if __name__ == "__main__":
    main()
