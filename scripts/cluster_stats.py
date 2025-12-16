# cluster_stats.py
# 聚类结果统计分析工具

import pandas as pd
import os

def analyze_clustering_result(clusters_file, summary_file):
    """分析聚类结果质量"""

    # 检查文件是否存在
    if not os.path.exists(clusters_file):
        print(f"❌ 文件不存在: {clusters_file}")
        return

    if not os.path.exists(summary_file):
        print(f"❌ 文件不存在: {summary_file}")
        return

    # 读取数据
    clusters = pd.read_csv(clusters_file)
    summary = pd.read_csv(summary_file)

    # 基础统计
    total_phrases = len(clusters)

    # 检测使用哪个簇ID字段
    cluster_id_col = 'cluster_id_A' if 'cluster_id_A' in clusters.columns else 'cluster_id'

    noise_count = len(clusters[clusters[cluster_id_col] == -1])
    noise_ratio = noise_count / total_phrases * 100

    # 检测summary中的簇ID字段
    summary_cluster_col = 'cluster_id_A' if 'cluster_id_A' in summary.columns else 'cluster_id'

    valid_clusters = summary[summary[summary_cluster_col] != -1]
    cluster_count = len(valid_clusters)

    # 簇大小分布
    avg_size = valid_clusters['cluster_size'].mean()
    median_size = valid_clusters['cluster_size'].median()
    max_size = valid_clusters['cluster_size'].max()
    min_size = valid_clusters['cluster_size'].min()

    # 输出报告
    print(f"""
========== 聚类结果分析 ==========
总短语数: {total_phrases}
有效簇数: {cluster_count}
噪音点数: {noise_count} ({noise_ratio:.1f}%)

簇大小统计:
- 平均: {avg_size:.1f}
- 中位数: {median_size:.1f}
- 最大: {max_size}
- 最小: {min_size}

质量评估:
{"[OK] 簇数量合理 (60-100)" if 60 <= cluster_count <= 100 else "[!] 簇数量不合理"}
{"[OK] 噪音比例合理 (<25%)" if noise_ratio < 25 else "[!] 噪音比例过高"}
{"[OK] 簇大小合理 (50-150)" if 50 <= avg_size <= 150 else "[!] 簇大小需调整"}
==================================
    """)

    # 显示Top 10最大的簇
    print("\n========== Top 10 最大的簇 ==========")
    top10 = valid_clusters.nlargest(10, 'cluster_size')
    for idx, row in top10.iterrows():
        seed_words = row.get('seed_words_in_cluster', 'N/A')
        print(f"簇 {row[summary_cluster_col]} | 大小: {row['cluster_size']} | 种子词: {seed_words}")

    # 参数调优建议
    print("\n========== 参数调优建议 ==========")
    if cluster_count > 100:
        print("[!] 簇数量过多，建议：")
        print("   - 增大 min_cluster_size 到 20-25")
        print("   - 保持 min_samples = 3")
    elif cluster_count < 40:
        print("[!] 簇数量过少，建议：")
        print("   - 减小 min_cluster_size 到 10-12")
        print("   - 减小 min_samples 到 2")
    else:
        print("[OK] 簇数量在合理范围内")

    if noise_ratio > 30:
        print("[!] 噪音比例较高，可能原因：")
        print("   - 种子词语义跨度太大（考虑按 seed_group 分组聚类）")
        print("   - 数据质量问题（检查短语是否有大量无效数据）")
        print("   - 参数过于严格（可适当减小 min_cluster_size）")
    elif noise_ratio < 15:
        print("[!] 噪音比例过低，参数可能过于宽松")
        print("   - 建议增大 min_cluster_size")
    else:
        print("[OK] 噪音比例在合理范围内")

    # 人工审查建议
    print("\n========== 人工审查建议 ==========")
    print(f"[*] 建议从 cluster_summary_A3.csv 查看以下内容：")
    print(f"   1. 查看 example_phrases 字段（如果有）")
    print(f"   2. 人工审查前 20 个最大的簇")
    print(f"   3. 挑选 5-10 个清晰的方向进入阶段B")
    print(f"   4. 忽略 cluster_id=-1 的噪音点（人工筛选时再决定是否保留）")

    return {
        'total_phrases': total_phrases,
        'cluster_count': cluster_count,
        'noise_count': noise_count,
        'noise_ratio': noise_ratio,
        'avg_size': avg_size,
        'median_size': median_size,
    }


if __name__ == "__main__":
    # 默认文件路径
    clusters_file = "D:/xiangmu/词根聚类需求挖掘/data/stageA_clusters.csv"
    summary_file = "D:/xiangmu/词根聚类需求挖掘/data/cluster_summary_A3.csv"

    print("开始分析聚类结果...\n")
    result = analyze_clustering_result(clusters_file, summary_file)
