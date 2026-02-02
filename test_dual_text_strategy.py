"""
Phase 2 实验 3: 双文本策略测试脚本

测试数据驱动的属性词发现和双文本聚类策略

运行方式:
    python test_dual_text_strategy.py
"""
import sys
import os
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import SessionLocal
from backend.services.clustering_service import ClusteringService


def print_section(title: str):
    """打印分节标题"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def test_dual_text_strategy():
    """测试双文本策略"""
    print_section("Phase 2 实验 3: 双文本策略测试")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 创建数据库会话
    db = SessionLocal()

    try:
        # 创建聚类服务
        service = ClusteringService(db)

        print("\n配置参数:")
        print("  - 聚类模式: 三阶段聚类")
        print("  - Stage 1 min_size: 10")
        print("  - Stage 2 min_size: 5")
        print("  - Stage 3 min_size: 3")
        print("  - 属性词分散度阈值: 0.3 (出现在>30%的簇中)")
        print("  - 双文本策略: 启用")

        # 执行双文本策略聚类
        print_section("开始执行双文本策略聚类")

        result = service.cluster_all_products(
            use_three_stage=True,
            stage1_min_size=10,
            stage2_min_size=5,
            stage3_min_size=3,
            use_dual_text=True,  # ✅ 启用双文本策略
            dispersion_threshold=0.3,  # 属性词分散度阈值
            use_cache=True,
            limit=None  # 处理所有商品
        )

        # 打印结果
        print_section("实验结果")

        if result.get("success"):
            print("\n✅ 聚类成功完成！")

            print("\n【初始聚类】(使用 full_text)")
            initial = result["initial_clustering"]
            print(f"  总簇数: {initial['n_clusters']}")
            print(f"  噪音点: {initial['n_noise']} ({initial['noise_ratio']:.2f}%)")

            print("\n【属性词发现】")
            attr = result["attribute_discovery"]
            print(f"  发现属性词数量: {attr['n_attribute_words']}")
            print(f"  分散度阈值: {attr['dispersion_threshold']}")
            print(f"  属性词列表: {', '.join(sorted(attr['attribute_words']))}")

            print("\n【最终聚类】(使用 topic_text)")
            final = result["final_clustering"]
            print(f"  总簇数: {final['n_clusters']}")
            print(f"  噪音点: {final['n_noise']} ({final['noise_ratio']:.2f}%)")

            if "n_primary_clusters" in final:
                print(f"  - 主要簇 (≥10): {final['n_primary_clusters']}")
                print(f"  - 次级簇 (5-9): {final['n_secondary_clusters']}")
                print(f"  - 微型簇 (3-4): {final['n_micro_clusters']}")

            print("\n【改善效果】")
            improvement = result["improvement"]
            print(f"  簇数量减少: {improvement['cluster_reduction']} ({improvement['cluster_reduction_pct']:.1f}%)")

            # 对比 Phase 1 基线
            print("\n【与 Phase 1 基线对比】")
            print(f"  Phase 1 基线: 1,392 个簇")
            print(f"  Phase 2 结果: {final['n_clusters']} 个簇")
            baseline_reduction = (1392 - final['n_clusters']) / 1392 * 100
            print(f"  相比基线减少: {1392 - final['n_clusters']} ({baseline_reduction:.1f}%)")

            # 评估是否达到目标
            print("\n【Phase 2 目标达成情况】")
            target_clusters = (300, 500)
            if target_clusters[0] <= final['n_clusters'] <= target_clusters[1]:
                print(f"  ✅ 簇数量: {final['n_clusters']} (目标: {target_clusters[0]}-{target_clusters[1]})")
            else:
                print(f"  ⚠️ 簇数量: {final['n_clusters']} (目标: {target_clusters[0]}-{target_clusters[1]})")

            if "n_micro_clusters" in final:
                target_micro = (50, 100)
                if final['n_micro_clusters'] <= target_micro[1]:
                    print(f"  ✅ 微型簇: {final['n_micro_clusters']} (目标: <{target_micro[1]})")
                else:
                    print(f"  ⚠️ 微型簇: {final['n_micro_clusters']} (目标: <{target_micro[1]})")

            # 保存结果到文件
            print_section("保存结果")

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            result_file = f"docs/实验结果/实验3_dual_text_strategy_{timestamp}.txt"

            os.makedirs("docs/实验结果", exist_ok=True)

            with open(result_file, 'w', encoding='utf-8') as f:
                f.write("Phase 2 实验 3: 双文本策略测试结果\n")
                f.write("="*80 + "\n\n")
                f.write(f"实验时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                f.write("配置参数:\n")
                f.write("  - 聚类模式: 三阶段聚类\n")
                f.write("  - Stage 1 min_size: 10\n")
                f.write("  - Stage 2 min_size: 5\n")
                f.write("  - Stage 3 min_size: 3\n")
                f.write(f"  - 属性词分散度阈值: {attr['dispersion_threshold']}\n")
                f.write("  - 双文本策略: 启用\n\n")

                f.write("初始聚类 (full_text):\n")
                f.write(f"  总簇数: {initial['n_clusters']}\n")
                f.write(f"  噪音点: {initial['n_noise']} ({initial['noise_ratio']:.2f}%)\n\n")

                f.write("属性词发现:\n")
                f.write(f"  发现属性词数量: {attr['n_attribute_words']}\n")
                f.write(f"  属性词列表: {', '.join(sorted(attr['attribute_words']))}\n\n")

                f.write("最终聚类 (topic_text):\n")
                f.write(f"  总簇数: {final['n_clusters']}\n")
                f.write(f"  噪音点: {final['n_noise']} ({final['noise_ratio']:.2f}%)\n")

                if "n_primary_clusters" in final:
                    f.write(f"  - 主要簇 (≥10): {final['n_primary_clusters']}\n")
                    f.write(f"  - 次级簇 (5-9): {final['n_secondary_clusters']}\n")
                    f.write(f"  - 微型簇 (3-4): {final['n_micro_clusters']}\n")

                f.write("\n改善效果:\n")
                f.write(f"  簇数量减少: {improvement['cluster_reduction']} ({improvement['cluster_reduction_pct']:.1f}%)\n\n")

                f.write("与 Phase 1 基线对比:\n")
                f.write(f"  Phase 1 基线: 1,392 个簇\n")
                f.write(f"  Phase 2 结果: {final['n_clusters']} 个簇\n")
                f.write(f"  相比基线减少: {1392 - final['n_clusters']} ({baseline_reduction:.1f}%)\n")

            print(f"✅ 结果已保存到: {result_file}")

        else:
            print(f"\n❌ 聚类失败: {result.get('message')}")

    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()

    print_section("测试完成")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    test_dual_text_strategy()
