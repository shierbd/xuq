"""
验证聚类数据的存在性和完整性
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.repository import ClusterMetaRepository

def main():
    print("="*70)
    print("聚类数据验证报告")
    print("="*70)
    print()

    with ClusterMetaRepository() as repo:
        # 大组聚类
        clusters_A = repo.get_all_clusters('A')
        print(f"大组聚类 (Level A): {len(clusters_A)} 个")
        if clusters_A:
            print(f"  示例: cluster_id={clusters_A[0].cluster_id}, size={clusters_A[0].size}")
        print()

        # 小组聚类
        clusters_B = repo.get_all_clusters('B')
        print(f"小组聚类 (Level B): {len(clusters_B)} 个")
        print()

        if clusters_B:
            print("小组详细信息:")
            print("-" * 70)

            # 按父组分组
            by_parent = {}
            for c in clusters_B:
                parent_id = c.cluster_id // 10000
                if parent_id not in by_parent:
                    by_parent[parent_id] = []
                by_parent[parent_id].append(c)

            print(f"\n按大组分布: {len(by_parent)} 个大组包含小组")
            for parent_id in sorted(by_parent.keys()):
                small_count = len(by_parent[parent_id])
                total_size = sum(c.size for c in by_parent[parent_id])
                print(f"  大组 {parent_id}: {small_count} 个小组, 共 {total_size} 个短语")

            print("\n" + "-" * 70)
            print("前5个小组详情:")
            for c in clusters_B[:5]:
                parent_id = c.cluster_id // 10000
                print(f"\n  小组ID: {c.cluster_id}")
                print(f"    父组: {parent_id}")
                print(f"    大小: {c.size}")
                print(f"    主题: {c.main_theme or '(无)'}")
                print(f"    示例: {c.example_phrases[:100] if c.example_phrases else '(无)'}...")
        else:
            print("警告: 没有找到小组聚类数据！")
            print("请运行 Phase 4 生成小组聚类")

        print("\n" + "="*70)
        print("验证完成")
        print("="*70)

if __name__ == "__main__":
    main()
