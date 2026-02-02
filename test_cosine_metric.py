#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
实验 1: 测试 cosine vs euclidean metric

对比两种距离度量对聚类结果的影响
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.services.clustering_service import ClusteringService
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json
from datetime import datetime

# 数据库配置
DATABASE_URL = "sqlite:///./data/products.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def run_experiment():
    """运行实验"""
    print("=" * 80)
    print("实验 1: cosine vs euclidean metric")
    print("=" * 80)
    print()

    # 创建数据库会话
    db = SessionLocal()

    try:
        # 创建聚类服务
        print("初始化聚类服务...")
        service = ClusteringService(db, model_name="all-mpnet-base-v2")

        # 执行三阶段聚类（使用新的 cosine metric）
        print("\n开始执行三阶段聚类（metric=cosine）...")
        print("-" * 80)

        result = service.cluster_all_products(
            use_three_stage=True,
            stage1_min_size=10,
            stage2_min_size=5,
            stage3_min_size=3
        )

        print("\n" + "=" * 80)
        print("聚类完成！")
        print("=" * 80)

        # 输出结果
        print("\n【聚类结果统计】")
        print(f"  总商品数: {result['total_products']:,}")
        print(f"  生成簇数: {result['n_clusters']:,}")
        print(f"  噪音点数: {result['n_noise']:,}")
        print(f"  噪音比例: {result['noise_ratio']:.2f}%")
        print(f"  聚类模式: {result['clustering_mode']}")

        if 'stage_stats' in result:
            print("\n【各阶段统计】")
            for stage_name, stats in result['stage_stats'].items():
                print(f"\n  {stage_name}:")
                print(f"    簇数量: {stats['n_clusters']}")
                print(f"    噪音点: {stats['n_noise']}")
                print(f"    噪音比例: {stats['noise_ratio']:.2f}%")

        # 生成对比报告
        print("\n" + "=" * 80)
        print("与之前结果对比（euclidean metric）")
        print("=" * 80)

        # 之前的结果（euclidean）
        previous_results = {
            'total_products': 15792,
            'n_clusters': 1412,
            'n_noise': 4620,
            'noise_ratio': 29.26,
            'primary_clusters': 335,
            'secondary_clusters': 502,
            'micro_clusters': 575
        }

        print("\n【对比表】")
        print(f"{'指标':<20} {'Euclidean':<15} {'Cosine':<15} {'变化':<15}")
        print("-" * 70)
        print(f"{'总商品数':<20} {previous_results['total_products']:<15,} {result['total_products']:<15,} {'-':<15}")
        print(f"{'生成簇数':<20} {previous_results['n_clusters']:<15,} {result['n_clusters']:<15,} {result['n_clusters'] - previous_results['n_clusters']:+,}")
        print(f"{'噪音点数':<20} {previous_results['n_noise']:<15,} {result['n_noise']:<15,} {result['n_noise'] - previous_results['n_noise']:+,}")
        print(f"{'噪音比例':<20} {previous_results['noise_ratio']:<15.2f}% {result['noise_ratio']:<15.2f}% {result['noise_ratio'] - previous_results['noise_ratio']:+.2f}%")

        # 保存结果到文件
        output_file = f"experiment_results/exp1_cosine_metric_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs("experiment_results", exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'experiment': 'cosine_vs_euclidean',
                'timestamp': datetime.now().isoformat(),
                'metric': 'cosine',
                'results': result,
                'previous_results': previous_results,
                'comparison': {
                    'cluster_diff': result['n_clusters'] - previous_results['n_clusters'],
                    'noise_diff': result['n_noise'] - previous_results['n_noise'],
                    'noise_ratio_diff': result['noise_ratio'] - previous_results['noise_ratio']
                }
            }, f, indent=2, ensure_ascii=False)

        print(f"\n结果已保存到: {output_file}")

        # 分析结果
        print("\n" + "=" * 80)
        print("结果分析")
        print("=" * 80)

        cluster_diff = result['n_clusters'] - previous_results['n_clusters']
        noise_diff = result['n_noise'] - previous_results['n_noise']

        if cluster_diff < 0:
            print(f"\n✅ 簇数量减少了 {abs(cluster_diff)} 个（{abs(cluster_diff)/previous_results['n_clusters']*100:.1f}%）")
            print("   → 说明 cosine metric 生成了更稳定、更大的簇")
        elif cluster_diff > 0:
            print(f"\n⚠️ 簇数量增加了 {cluster_diff} 个（{cluster_diff/previous_results['n_clusters']*100:.1f}%）")
            print("   → 可能需要进一步调整参数")
        else:
            print("\n➡️ 簇数量没有变化")

        if noise_diff < 0:
            print(f"\n✅ 噪音点减少了 {abs(noise_diff)} 个（{abs(noise_diff)/previous_results['n_noise']*100:.1f}%）")
            print("   → 更多商品被成功聚类")
        elif noise_diff > 0:
            print(f"\n⚠️ 噪音点增加了 {noise_diff} 个（{noise_diff/previous_results['n_noise']*100:.1f}%）")
            print("   → 聚类更保守，但可能主题质量更高")
        else:
            print("\n➡️ 噪音点数量没有变化")

        print("\n" + "=" * 80)
        print("实验完成！")
        print("=" * 80)

        return result

    except Exception as e:
        print(f"\n❌ 实验失败: {e}")
        import traceback
        traceback.print_exc()
        return None

    finally:
        db.close()

if __name__ == "__main__":
    run_experiment()
