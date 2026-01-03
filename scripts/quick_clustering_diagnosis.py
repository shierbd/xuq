"""
快速诊断HDBSCAN聚类问题 - 简化版
只做关键分析，提高速度
"""
import sys
from pathlib import Path
import numpy as np
from sklearn.preprocessing import normalize
from sklearn.metrics import silhouette_score
from sklearn.neighbors import NearestNeighbors
from scipy.spatial.distance import pdist
from scipy.stats import describe
import hdbscan

# 添加项目根目录
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 编码修复
from utils.encoding_fix import setup_encoding
setup_encoding()

from config.settings import CACHE_DIR, OUTPUT_DIR


def load_embeddings(round_id=1):
    """加载embeddings数据"""
    cache_file = CACHE_DIR / f"embeddings_round{round_id}.npz"
    print(f"\n加载embeddings: {cache_file}")

    data = np.load(cache_file, allow_pickle=True)
    cache_dict = data['cache'].item()

    print(f"  缓存embedding数量: {len(cache_dict)}")

    # 转换为numpy数组
    embeddings_list = list(cache_dict.values())
    embeddings = np.array(embeddings_list)

    print(f"  Embeddings形状: {embeddings.shape}")

    return embeddings


def quick_diagnosis():
    """快速诊断"""
    print("\n" + "="*70)
    print("HDBSCAN聚类问题快速诊断".center(70))
    print("="*70)

    # 1. 加载数据
    print("\n【步骤1】加载数据...")
    embeddings = load_embeddings(round_id=1)
    n_samples = len(embeddings)

    # 2. 归一化
    print("\n【步骤2】归一化向量...")
    embeddings_norm = normalize(embeddings, norm='l2')

    # 3. 采样分析距离分布
    print("\n【步骤3】分析距离分布（采样10000个样本）...")
    sample_size = min(10000, n_samples)
    indices = np.random.choice(n_samples, sample_size, replace=False)
    sample_embeddings = embeddings_norm[indices]

    print(f"  计算 {sample_size} 个样本的成对距离...")
    distances = pdist(sample_embeddings, metric='euclidean')

    dist_stats = describe(distances)
    print(f"\n  距离统计:")
    print(f"    最小距离: {dist_stats.minmax[0]:.4f}")
    print(f"    最大距离: {dist_stats.minmax[1]:.4f}")
    print(f"    平均距离: {dist_stats.mean:.4f}")
    print(f"    标准差: {np.sqrt(dist_stats.variance):.4f}")
    print(f"    中位数: {np.median(distances):.4f}")

    # 关键诊断指标
    print(f"\n  关键诊断:")
    if dist_stats.mean > 1.2:
        print(f"    ❌ 平均距离过大 ({dist_stats.mean:.4f})，数据点严重分散")
    elif dist_stats.mean > 1.0:
        print(f"    ⚠️  平均距离较大 ({dist_stats.mean:.4f})，数据点分散")
    else:
        print(f"    ✓ 平均距离正常 ({dist_stats.mean:.4f})")

    if np.sqrt(dist_stats.variance) < 0.1:
        print(f"    ❌ 距离标准差过小 ({np.sqrt(dist_stats.variance):.4f})，缺乏明显聚集")
    elif np.sqrt(dist_stats.variance) < 0.2:
        print(f"    ⚠️  距离标准差较小 ({np.sqrt(dist_stats.variance):.4f})，聚集不明显")
    else:
        print(f"    ✓ 距离标准差正常 ({np.sqrt(dist_stats.variance):.4f})")

    # 4. K近邻密度分析
    print("\n【步骤4】分析局部密度（K=20近邻）...")
    nbrs = NearestNeighbors(n_neighbors=21, metric='euclidean', n_jobs=-1)
    nbrs.fit(embeddings_norm)
    distances_knn, _ = nbrs.kneighbors(embeddings_norm)

    knn_mean_dist = distances_knn[:, 1:].mean(axis=1)  # 排除自己
    density = 1.0 / (knn_mean_dist + 1e-10)

    print(f"\n  密度统计:")
    print(f"    平均密度: {density.mean():.4f}")
    print(f"    密度标准差: {density.std():.4f}")
    print(f"    密度中位数: {np.median(density):.4f}")
    print(f"    高密度点(>90%): {(density >= np.percentile(density, 90)).sum():,} ({(density >= np.percentile(density, 90)).sum()/n_samples*100:.1f}%)")

    # 5. 快速测试几个HDBSCAN参数
    print("\n【步骤5】测试HDBSCAN参数（快速版）...")

    test_params = [
        {'min_cluster_size': 30, 'min_samples': 3},
        {'min_cluster_size': 50, 'min_samples': 5},
        {'min_cluster_size': 100, 'min_samples': 10},
        {'min_cluster_size': 200, 'min_samples': 20},
    ]

    results = []
    for params in test_params:
        print(f"\n  测试: min_cluster_size={params['min_cluster_size']}, min_samples={params['min_samples']}")

        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=params['min_cluster_size'],
            min_samples=params['min_samples'],
            metric='euclidean',
            cluster_selection_method='eom',
            core_dist_n_jobs=-1
        )

        labels = clusterer.fit_predict(embeddings_norm)

        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise = (labels == -1).sum()
        noise_ratio = n_noise / n_samples * 100

        print(f"    聚类数: {n_clusters}, 噪音点: {n_noise:,} ({noise_ratio:.1f}%)")

        results.append({
            'params': params,
            'n_clusters': n_clusters,
            'noise_ratio': noise_ratio
        })

    # 6. 测试K-Means对比
    print("\n【步骤6】对比K-Means算法（采样10000个样本）...")

    from sklearn.cluster import KMeans

    for k in [60, 80, 100]:
        print(f"\n  K-Means with K={k}:")
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=5)
        labels_km = kmeans.fit_predict(sample_embeddings)

        silhouette = silhouette_score(sample_embeddings, labels_km)
        print(f"    轮廓系数: {silhouette:.4f}")

    # 7. 生成诊断报告
    print("\n" + "="*70)
    print("诊断报告")
    print("="*70)

    print("\n【问题诊断】")
    print(f"1. 数据规模: {n_samples:,} 个短语, {embeddings.shape[1]} 维向量")

    print(f"\n2. 数据分布特征:")
    print(f"   - 平均距离: {dist_stats.mean:.4f}")
    print(f"   - 距离标准差: {np.sqrt(dist_stats.variance):.4f}")

    if dist_stats.mean > 1.2 or np.sqrt(dist_stats.variance) < 0.1:
        print(f"\n   ❌ 数据分布问题严重:")
        if dist_stats.mean > 1.2:
            print(f"      - 数据点过于分散（平均距离={dist_stats.mean:.4f} > 1.2）")
        if np.sqrt(dist_stats.variance) < 0.1:
            print(f"      - 缺乏明显的聚集区域（标准差={np.sqrt(dist_stats.variance):.4f} < 0.1）")

    print(f"\n3. HDBSCAN表现:")
    best_result = max(results, key=lambda x: x['n_clusters'])
    print(f"   - 最好情况: {best_result['n_clusters']} 个聚类 (参数: {best_result['params']})")
    print(f"   - 最多噪音: {max(r['noise_ratio'] for r in results):.1f}%")

    if best_result['n_clusters'] < 10:
        print(f"\n   ❌ HDBSCAN严重失效:")
        print(f"      - 最多只能生成 {best_result['n_clusters']} 个聚类（期望60-100个）")
        print(f"      - 根本原因: 数据缺乏足够的密度分隔")

    print(f"\n【推荐方案】")
    print(f"\n优先级1: 切换到K-Means算法")
    print(f"  - 原因: HDBSCAN依赖密度聚类，当前数据缺乏明显密度分隔")
    print(f"  - K-Means是基于距离的聚类，更适合当前数据分布")
    print(f"  - 建议K值: 60-100")

    print(f"\n优先级2: 改进Embedding质量")
    print(f"  - 考虑更强大的embedding模型（如multilingual-e5-large）")
    print(f"  - 或者使用领域特定的预训练模型")

    print(f"\n优先级3: 降维+聚类")
    print(f"  - PCA降维到50-100维后再聚类")
    print(f"  - 可能提高聚类效果")

    # 保存报告
    OUTPUT_DIR.mkdir(exist_ok=True)
    report_file = OUTPUT_DIR / 'clustering_quick_diagnosis.txt'

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("HDBSCAN聚类问题快速诊断报告\n")
        f.write("="*70 + "\n\n")
        f.write(f"数据规模: {n_samples:,} 个短语\n")
        f.write(f"向量维度: {embeddings.shape[1]}\n\n")
        f.write(f"距离统计:\n")
        f.write(f"  平均距离: {dist_stats.mean:.4f}\n")
        f.write(f"  距离标准差: {np.sqrt(dist_stats.variance):.4f}\n")
        f.write(f"  中位数: {np.median(distances):.4f}\n\n")
        f.write(f"HDBSCAN测试结果:\n")
        for r in results:
            f.write(f"  {r['params']}: {r['n_clusters']}个聚类, {r['noise_ratio']:.1f}%噪音\n")
        f.write(f"\n推荐方案: 切换到K-Means算法（K=60-100）\n")

    print(f"\n💾 报告已保存: {report_file}")

    print("\n" + "="*70)
    print("快速诊断完成！")
    print("="*70)


if __name__ == "__main__":
    quick_diagnosis()
