"""
深入分析HDBSCAN聚类效果差的根本原因

分析内容：
1. Embeddings向量分布特征
2. 距离统计（最近邻、中位数、方差等）
3. 密度分析（局部密度分布）
4. 降维可视化分析
5. HDBSCAN参数敏感性分析
6. 与其他算法对比（K-Means, GMM）
"""
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import normalize
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
from sklearn.neighbors import NearestNeighbors
from scipy.spatial.distance import pdist, squareform
from scipy.stats import describe
import hdbscan
import warnings
warnings.filterwarnings('ignore')

# 添加项目根目录
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ========== 编码修复（必须在所有其他导入之前）==========
from utils.encoding_fix import setup_encoding
setup_encoding()
# ======================================================

from config.settings import CACHE_DIR, OUTPUT_DIR

# 设置中文字体（Windows）
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False


def load_embeddings(round_id=1):
    """加载embeddings数据"""
    cache_file = CACHE_DIR / f"embeddings_round{round_id}.npz"
    print(f"\n加载embeddings: {cache_file}")

    if not cache_file.exists():
        raise FileNotFoundError(f"Embeddings缓存不存在: {cache_file}")

    data = np.load(cache_file, allow_pickle=True)
    cache_dict = data['cache'].item()  # 从字典格式提取

    print(f"  缓存中的embedding数量: {len(cache_dict)}")

    # 转换为numpy数组
    embeddings_list = list(cache_dict.values())
    embeddings = np.array(embeddings_list)

    print(f"  Embeddings形状: {embeddings.shape}")
    print(f"  向量维度: {embeddings.shape[1]}")

    return embeddings


def analyze_vector_distribution(embeddings):
    """分析向量分布特征"""
    print("\n" + "="*70)
    print("1. 向量分布分析")
    print("="*70)

    # 基本统计
    print("\n【向量统计】")
    print(f"  平均范数: {np.linalg.norm(embeddings, axis=1).mean():.4f}")
    print(f"  范数标准差: {np.linalg.norm(embeddings, axis=1).std():.4f}")
    print(f"  范数最小值: {np.linalg.norm(embeddings, axis=1).min():.4f}")
    print(f"  范数最大值: {np.linalg.norm(embeddings, axis=1).max():.4f}")

    # 归一化向量
    embeddings_norm = normalize(embeddings, norm='l2')

    # 计算所有维度的统计
    print("\n【各维度统计】")
    dim_stats = {
        'mean': embeddings_norm.mean(axis=0),
        'std': embeddings_norm.std(axis=0),
        'min': embeddings_norm.min(axis=0),
        'max': embeddings_norm.max(axis=0)
    }

    print(f"  平均值的均值: {dim_stats['mean'].mean():.4f}")
    print(f"  平均值的标准差: {dim_stats['mean'].std():.4f}")
    print(f"  标准差的均值: {dim_stats['std'].mean():.4f}")
    print(f"  标准差的标准差: {dim_stats['std'].std():.4f}")

    return embeddings_norm, dim_stats


def analyze_distance_distribution(embeddings_norm, sample_size=10000):
    """分析距离分布（使用采样以节省时间）"""
    print("\n" + "="*70)
    print("2. 距离分布分析")
    print("="*70)

    n_samples = len(embeddings_norm)

    # 采样分析（如果数据太大）
    if n_samples > sample_size:
        print(f"\n⚠️  数据量较大，采样 {sample_size} 个样本进行距离分析")
        indices = np.random.choice(n_samples, sample_size, replace=False)
        sample_embeddings = embeddings_norm[indices]
    else:
        sample_embeddings = embeddings_norm

    # 计算成对距离（欧几里得距离，归一化后等价于余弦距离）
    print("\n计算成对距离...")
    distances = pdist(sample_embeddings, metric='euclidean')

    print("\n【距离统计】")
    dist_stats = describe(distances)
    print(f"  样本数: {dist_stats.nobs:,}")
    print(f"  最小距离: {dist_stats.minmax[0]:.4f}")
    print(f"  最大距离: {dist_stats.minmax[1]:.4f}")
    print(f"  平均距离: {dist_stats.mean:.4f}")
    print(f"  方差: {dist_stats.variance:.4f}")
    print(f"  标准差: {np.sqrt(dist_stats.variance):.4f}")
    print(f"  偏度: {dist_stats.skewness:.4f}")
    print(f"  峰度: {dist_stats.kurtosis:.4f}")

    # 距离分位数
    percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    print("\n【距离分位数】")
    for p in percentiles:
        val = np.percentile(distances, p)
        print(f"  {p:2d}%: {val:.4f}")

    return distances, dist_stats


def analyze_nearest_neighbors(embeddings_norm, k_values=[5, 10, 20, 50]):
    """分析最近邻距离分布"""
    print("\n" + "="*70)
    print("3. 最近邻距离分析")
    print("="*70)

    results = {}

    for k in k_values:
        print(f"\n【K={k} 最近邻】")

        # 计算K最近邻
        nbrs = NearestNeighbors(n_neighbors=k+1, metric='euclidean', n_jobs=-1)
        nbrs.fit(embeddings_norm)
        distances, indices = nbrs.kneighbors(embeddings_norm)

        # 排除自己（第一个邻居）
        knn_distances = distances[:, 1:]

        # 统计
        mean_dist = knn_distances.mean(axis=1)
        max_dist = knn_distances.max(axis=1)

        print(f"  平均K近邻距离的均值: {mean_dist.mean():.4f}")
        print(f"  平均K近邻距离的标准差: {mean_dist.std():.4f}")
        print(f"  平均K近邻距离的中位数: {np.median(mean_dist):.4f}")
        print(f"  最远K近邻距离的均值: {max_dist.mean():.4f}")
        print(f"  最远K近邻距离的标准差: {max_dist.std():.4f}")

        results[k] = {
            'mean_dist': mean_dist,
            'max_dist': max_dist,
            'knn_distances': knn_distances
        }

    return results


def analyze_density_distribution(embeddings_norm, k=20):
    """分析密度分布"""
    print("\n" + "="*70)
    print("4. 密度分布分析")
    print("="*70)

    print(f"\n使用 K={k} 估计局部密度...")

    # 使用K近邻距离估计密度
    nbrs = NearestNeighbors(n_neighbors=k+1, metric='euclidean', n_jobs=-1)
    nbrs.fit(embeddings_norm)
    distances, _ = nbrs.kneighbors(embeddings_norm)

    # 密度 = 1 / K近邻平均距离
    knn_mean_dist = distances[:, 1:].mean(axis=1)
    density = 1.0 / (knn_mean_dist + 1e-10)

    print("\n【密度统计】")
    print(f"  最小密度: {density.min():.4f}")
    print(f"  最大密度: {density.max():.4f}")
    print(f"  平均密度: {density.mean():.4f}")
    print(f"  密度标准差: {density.std():.4f}")
    print(f"  密度中位数: {np.median(density):.4f}")

    # 密度分位数
    percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    print("\n【密度分位数】")
    for p in percentiles:
        val = np.percentile(density, p)
        print(f"  {p:2d}%: {val:.4f}")

    # 高密度区域统计
    high_density_threshold = np.percentile(density, 90)
    high_density_count = (density >= high_density_threshold).sum()
    print(f"\n【高密度区域】（> 90分位数）")
    print(f"  高密度点数: {high_density_count:,} ({high_density_count/len(density)*100:.2f}%)")

    # 低密度区域统计
    low_density_threshold = np.percentile(density, 10)
    low_density_count = (density <= low_density_threshold).sum()
    print(f"\n【低密度区域】（< 10分位数）")
    print(f"  低密度点数: {low_density_count:,} ({low_density_count/len(density)*100:.2f}%)")

    return density, knn_mean_dist


def perform_pca_analysis(embeddings_norm, n_components=50):
    """PCA降维分析"""
    print("\n" + "="*70)
    print("5. PCA降维分析")
    print("="*70)

    print(f"\n执行PCA降维到 {n_components} 维...")
    pca = PCA(n_components=n_components)
    embeddings_pca = pca.fit_transform(embeddings_norm)

    # 方差解释率
    explained_variance = pca.explained_variance_ratio_
    cumulative_variance = np.cumsum(explained_variance)

    print("\n【主成分方差解释率】")
    print(f"  PC1: {explained_variance[0]*100:.2f}%")
    print(f"  PC2: {explained_variance[1]*100:.2f}%")
    print(f"  PC3: {explained_variance[2]*100:.2f}%")
    print(f"  前10个PC累计: {cumulative_variance[9]*100:.2f}%")
    print(f"  前20个PC累计: {cumulative_variance[19]*100:.2f}%")
    print(f"  前50个PC累计: {cumulative_variance[-1]*100:.2f}%")

    # 找到累计方差达到90%需要的维度
    n_dims_90 = np.argmax(cumulative_variance >= 0.9) + 1
    n_dims_95 = np.argmax(cumulative_variance >= 0.95) + 1
    print(f"\n  达到90%方差需要: {n_dims_90} 维")
    print(f"  达到95%方差需要: {n_dims_95} 维")

    return embeddings_pca, pca, explained_variance


def test_hdbscan_parameters(embeddings_norm, param_grid):
    """测试不同的HDBSCAN参数"""
    print("\n" + "="*70)
    print("6. HDBSCAN参数敏感性分析")
    print("="*70)

    results = []

    for params in param_grid:
        min_cluster_size = params['min_cluster_size']
        min_samples = params['min_samples']

        print(f"\n测试参数: min_cluster_size={min_cluster_size}, min_samples={min_samples}")

        try:
            clusterer = hdbscan.HDBSCAN(
                min_cluster_size=min_cluster_size,
                min_samples=min_samples,
                metric='euclidean',
                cluster_selection_method='eom',
                core_dist_n_jobs=-1
            )

            labels = clusterer.fit_predict(embeddings_norm)

            # 统计
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
            n_noise = (labels == -1).sum()
            noise_ratio = n_noise / len(labels) * 100

            # 聚类大小
            cluster_sizes = []
            for label in set(labels):
                if label != -1:
                    cluster_sizes.append((labels == label).sum())

            # 轮廓系数
            silhouette = None
            if n_clusters > 1 and n_noise < len(labels):
                mask = labels != -1
                if mask.sum() > 1:
                    try:
                        silhouette = silhouette_score(embeddings_norm[mask], labels[mask])
                    except:
                        pass

            result = {
                'min_cluster_size': min_cluster_size,
                'min_samples': min_samples,
                'n_clusters': n_clusters,
                'n_noise': n_noise,
                'noise_ratio': noise_ratio,
                'min_size': min(cluster_sizes) if cluster_sizes else 0,
                'max_size': max(cluster_sizes) if cluster_sizes else 0,
                'mean_size': np.mean(cluster_sizes) if cluster_sizes else 0,
                'silhouette': silhouette
            }

            results.append(result)

            print(f"  聚类数: {n_clusters}, 噪音: {n_noise} ({noise_ratio:.1f}%), "
                  f"轮廓系数: {silhouette:.3f if silhouette else 'N/A'}")
            if cluster_sizes:
                print(f"  聚类大小: 最小={min(cluster_sizes)}, 最大={max(cluster_sizes)}, "
                      f"平均={np.mean(cluster_sizes):.1f}")

        except Exception as e:
            print(f"  ❌ 失败: {e}")
            continue

    return results


def compare_clustering_algorithms(embeddings_norm, sample_size=10000):
    """对比不同聚类算法"""
    print("\n" + "="*70)
    print("7. 聚类算法对比分析")
    print("="*70)

    # 如果数据太大，采样
    if len(embeddings_norm) > sample_size:
        print(f"\n⚠️  采样 {sample_size} 个样本进行算法对比")
        indices = np.random.choice(len(embeddings_norm), sample_size, replace=False)
        sample_embeddings = embeddings_norm[indices]
    else:
        sample_embeddings = embeddings_norm

    results = {}

    # K-Means (测试不同K值)
    print("\n【K-Means】")
    from sklearn.cluster import KMeans

    for k in [50, 75, 100, 150]:
        print(f"\n  K={k}:")
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(sample_embeddings)

        silhouette = silhouette_score(sample_embeddings, labels)
        davies_bouldin = davies_bouldin_score(sample_embeddings, labels)
        calinski_harabasz = calinski_harabasz_score(sample_embeddings, labels)

        print(f"    轮廓系数: {silhouette:.4f}")
        print(f"    Davies-Bouldin: {davies_bouldin:.4f} (越小越好)")
        print(f"    Calinski-Harabasz: {calinski_harabasz:.2f} (越大越好)")

        results[f'kmeans_k{k}'] = {
            'n_clusters': k,
            'silhouette': silhouette,
            'davies_bouldin': davies_bouldin,
            'calinski_harabasz': calinski_harabasz
        }

    # GMM (测试不同成分数)
    print("\n【高斯混合模型 GMM】")
    from sklearn.mixture import GaussianMixture

    for n_components in [50, 75, 100]:
        print(f"\n  n_components={n_components}:")
        gmm = GaussianMixture(n_components=n_components, random_state=42, covariance_type='diag')
        labels = gmm.fit_predict(sample_embeddings)

        silhouette = silhouette_score(sample_embeddings, labels)
        davies_bouldin = davies_bouldin_score(sample_embeddings, labels)

        print(f"    轮廓系数: {silhouette:.4f}")
        print(f"    Davies-Bouldin: {davies_bouldin:.4f}")
        print(f"    BIC: {gmm.bic(sample_embeddings):.2f} (越小越好)")
        print(f"    AIC: {gmm.aic(sample_embeddings):.2f} (越小越好)")

        results[f'gmm_{n_components}'] = {
            'n_clusters': n_components,
            'silhouette': silhouette,
            'davies_bouldin': davies_bouldin,
            'bic': gmm.bic(sample_embeddings),
            'aic': gmm.aic(sample_embeddings)
        }

    return results


def generate_visualizations(embeddings_norm, embeddings_pca, density, distances, output_dir):
    """生成可视化图表"""
    print("\n" + "="*70)
    print("8. 生成可视化图表")
    print("="*70)

    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    # 1. 距离分布直方图
    print("\n生成距离分布图...")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(distances, bins=100, alpha=0.7, edgecolor='black')
    ax.set_xlabel('欧氏距离（归一化后）')
    ax.set_ylabel('频次')
    ax.set_title('成对距离分布')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / 'distance_distribution.png', dpi=150)
    plt.close()

    # 2. 密度分布直方图
    print("生成密度分布图...")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(density, bins=100, alpha=0.7, edgecolor='black')
    ax.set_xlabel('局部密度（1/K近邻距离）')
    ax.set_ylabel('频次')
    ax.set_title('局部密度分布')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / 'density_distribution.png', dpi=150)
    plt.close()

    # 3. PCA 2D投影（采样）
    print("生成PCA 2D投影图...")
    sample_size = min(5000, len(embeddings_pca))
    indices = np.random.choice(len(embeddings_pca), sample_size, replace=False)

    fig, ax = plt.subplots(figsize=(12, 10))
    scatter = ax.scatter(
        embeddings_pca[indices, 0],
        embeddings_pca[indices, 1],
        c=density[indices],
        cmap='viridis',
        alpha=0.5,
        s=10
    )
    ax.set_xlabel('PC1')
    ax.set_ylabel('PC2')
    ax.set_title(f'PCA 2D投影（按密度着色，采样{sample_size}个点）')
    plt.colorbar(scatter, label='局部密度')
    plt.tight_layout()
    plt.savefig(output_dir / 'pca_2d_projection.png', dpi=150)
    plt.close()

    print(f"\n✓ 可视化图表已保存到: {output_dir}")


def main():
    """主函数"""
    print("\n" + "="*70)
    print("HDBSCAN聚类问题深度分析".center(70))
    print("="*70)

    # 1. 加载数据
    embeddings = load_embeddings(round_id=1)

    # 2. 向量分布分析
    embeddings_norm, dim_stats = analyze_vector_distribution(embeddings)

    # 3. 距离分布分析
    distances, dist_stats = analyze_distance_distribution(embeddings_norm, sample_size=10000)

    # 4. 最近邻分析
    knn_results = analyze_nearest_neighbors(embeddings_norm, k_values=[5, 10, 20, 50])

    # 5. 密度分析
    density, knn_mean_dist = analyze_density_distribution(embeddings_norm, k=20)

    # 6. PCA分析
    embeddings_pca, pca, explained_variance = perform_pca_analysis(embeddings_norm, n_components=50)

    # 7. HDBSCAN参数测试
    param_grid = [
        {'min_cluster_size': 10, 'min_samples': 1},
        {'min_cluster_size': 20, 'min_samples': 2},
        {'min_cluster_size': 30, 'min_samples': 3},
        {'min_cluster_size': 50, 'min_samples': 5},
        {'min_cluster_size': 100, 'min_samples': 10},
        {'min_cluster_size': 200, 'min_samples': 20},
        {'min_cluster_size': 500, 'min_samples': 50},
        {'min_cluster_size': 1000, 'min_samples': 100},
    ]
    hdbscan_results = test_hdbscan_parameters(embeddings_norm, param_grid)

    # 8. 算法对比
    algo_results = compare_clustering_algorithms(embeddings_norm, sample_size=10000)

    # 9. 生成可视化
    output_viz_dir = OUTPUT_DIR / 'clustering_analysis'
    generate_visualizations(embeddings_norm, embeddings_pca, density, distances, output_viz_dir)

    # 10. 生成综合报告
    print("\n" + "="*70)
    print("生成综合分析报告")
    print("="*70)

    report_lines = []
    report_lines.append("="*70)
    report_lines.append("HDBSCAN聚类问题深度分析报告")
    report_lines.append("="*70)
    report_lines.append("")

    # 数据概况
    report_lines.append("【数据概况】")
    report_lines.append(f"  短语数量: {len(embeddings):,}")
    report_lines.append(f"  向量维度: {embeddings.shape[1]}")
    report_lines.append("")

    # 距离统计
    report_lines.append("【距离分布】")
    report_lines.append(f"  平均距离: {dist_stats.mean:.4f}")
    report_lines.append(f"  标准差: {np.sqrt(dist_stats.variance):.4f}")
    report_lines.append(f"  最小距离: {dist_stats.minmax[0]:.4f}")
    report_lines.append(f"  最大距离: {dist_stats.minmax[1]:.4f}")
    report_lines.append(f"  中位数: {np.median(distances):.4f}")
    report_lines.append("")

    # 密度统计
    report_lines.append("【密度分布】")
    report_lines.append(f"  平均密度: {density.mean():.4f}")
    report_lines.append(f"  密度标准差: {density.std():.4f}")
    report_lines.append(f"  密度中位数: {np.median(density):.4f}")
    report_lines.append("")

    # PCA分析
    report_lines.append("【PCA降维】")
    report_lines.append(f"  前10个PC累计方差: {np.cumsum(explained_variance)[9]*100:.2f}%")
    report_lines.append(f"  前20个PC累计方差: {np.cumsum(explained_variance)[19]*100:.2f}%")
    report_lines.append(f"  前50个PC累计方差: {np.cumsum(explained_variance)[-1]*100:.2f}%")
    report_lines.append("")

    # HDBSCAN参数测试结果
    report_lines.append("【HDBSCAN参数测试】")
    report_lines.append(f"{'min_size':<10} {'min_samp':<10} {'n_clust':<10} {'噪音率%':<10} {'轮廓系数':<12}")
    report_lines.append("-" * 70)
    for r in hdbscan_results:
        silh_str = f"{r['silhouette']:.4f}" if r['silhouette'] else "N/A"
        report_lines.append(
            f"{r['min_cluster_size']:<10} {r['min_samples']:<10} "
            f"{r['n_clusters']:<10} {r['noise_ratio']:<10.1f} {silh_str:<12}"
        )
    report_lines.append("")

    # 算法对比
    report_lines.append("【聚类算法对比】")
    report_lines.append(f"{'算法':<20} {'聚类数':<10} {'轮廓系数':<12} {'Davies-Bouldin':<16}")
    report_lines.append("-" * 70)
    for algo_name, r in algo_results.items():
        if 'davies_bouldin' in r:
            report_lines.append(
                f"{algo_name:<20} {r['n_clusters']:<10} "
                f"{r['silhouette']:<12.4f} {r['davies_bouldin']:<16.4f}"
            )
    report_lines.append("")

    # 问题诊断
    report_lines.append("="*70)
    report_lines.append("【问题诊断】")
    report_lines.append("="*70)
    report_lines.append("")

    # 根据分析结果给出诊断
    avg_dist = dist_stats.mean
    std_dist = np.sqrt(dist_stats.variance)

    report_lines.append("1. 数据分布特征：")
    if avg_dist > 1.2:
        report_lines.append(f"   ⚠️  平均距离过大({avg_dist:.4f})，数据点分散")
    if std_dist < 0.1:
        report_lines.append(f"   ⚠️  距离标准差过小({std_dist:.4f})，缺乏明显聚集")

    report_lines.append("")
    report_lines.append("2. HDBSCAN适用性：")
    best_hdbscan = max(hdbscan_results, key=lambda x: x['n_clusters'])
    if best_hdbscan['n_clusters'] < 10:
        report_lines.append(f"   ❌ HDBSCAN最多只能生成{best_hdbscan['n_clusters']}个聚类")
        report_lines.append("   原因：数据缺乏明显的密度分隔，HDBSCAN无法找到足够多的密集区域")

    report_lines.append("")
    report_lines.append("3. 推荐方案：")

    # 找最佳K-Means结果
    best_kmeans = max(
        [(k, v) for k, v in algo_results.items() if k.startswith('kmeans')],
        key=lambda x: x[1]['silhouette']
    )

    report_lines.append(f"   推荐算法: K-Means")
    report_lines.append(f"   推荐K值: {best_kmeans[1]['n_clusters']}")
    report_lines.append(f"   预期轮廓系数: {best_kmeans[1]['silhouette']:.4f}")
    report_lines.append("")

    report_lines.append("="*70)

    # 输出并保存报告
    report_text = '\n'.join(report_lines)
    print('\n' + report_text)

    report_file = OUTPUT_DIR / 'clustering_analysis_report.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_text)

    print(f"\n💾 报告已保存到: {report_file}")
    print(f"📊 可视化图表已保存到: {output_viz_dir}")

    print("\n" + "="*70)
    print("分析完成！")
    print("="*70)


if __name__ == "__main__":
    main()
