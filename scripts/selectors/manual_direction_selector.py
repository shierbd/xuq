"""
步骤A5：人工筛选方向（交互式工具）
功能：从cluster_summary_A3.csv中交互式筛选方向
输入：cluster_summary_A3.csv
输出：direction_keywords.csv

使用方法：
    python manual_direction_selector.py
"""

import pandas as pd
import sys
from pathlib import Path

# 导入配置和工具
from lib.config import A3_CONFIG, GENERAL_CONFIG
from lib.utils import (
    setup_logging,
    load_csv,
    save_csv,
    print_section,
    print_subsection
)


def display_cluster_info(row, index):
    """
    显示单个簇的详细信息

    参数:
        row: DataFrame行
        index: 簇序号
    """
    print(f"\n{'='*70}")
    print(f"簇 #{index + 1}")
    print(f"{'='*70}")
    print(f"📊 簇ID: {row['cluster_id_A']}")
    print(f"📏 簇大小: {row['cluster_size']} 条短语")
    print(f"🔢 总频次: {row['total_frequency']:.0f}")

    if 'total_search_volume' in row.index and row['total_search_volume'] > 0:
        print(f"🔍 总搜索量: {row['total_search_volume']:.0f}")

    print(f"\n🌱 种子词: {row['seed_words_in_cluster']}")

    # 显示example_phrases（最重要）
    if 'example_phrases' in row.index and pd.notna(row['example_phrases']):
        print(f"\n💡 代表性短语:")
        examples = row['example_phrases'].split('; ')
        for i, phrase in enumerate(examples[:5], 1):
            print(f"   {i}. {phrase}")

    # 显示统计特征
    if 'avg_word_count' in row.index:
        print(f"\n📝 平均单词数: {row['avg_word_count']:.1f}")

    if 'question_ratio' in row.index:
        print(f"❓ 问句比例: {row['question_ratio']*100:.1f}%")


def get_user_choice(cluster_count):
    """
    获取用户选择

    参数:
        cluster_count: 当前簇序号

    返回:
        (action, direction_keyword) 元组
        action: 'keep', 'skip', 'stop'
        direction_keyword: 用户输入的方向关键词（仅在action='keep'时有效）
    """
    print(f"\n{'='*70}")
    print("请选择操作:")
    print("  [K] Keep   - 保留这个簇并输入方向关键词")
    print("  [S] Skip   - 跳过这个簇")
    print("  [Q] Quit   - 结束筛选，保存结果")
    print(f"{'='*70}")

    while True:
        choice = input("\n你的选择 [K/S/Q]: ").strip().upper()

        if choice == 'Q':
            return 'stop', None

        elif choice == 'S':
            return 'skip', None

        elif choice == 'K':
            print("\n请输入方向关键词（用于后续扩展）:")
            print("  提示: 选择最能代表这个方向的1-3个核心词")
            print("  格式: 单个词（如 'productivity'）或多个词用空格分隔（如 'time management'）")

            direction_keyword = input("\n方向关键词: ").strip()

            if not direction_keyword:
                print("❌ 方向关键词不能为空，请重新输入")
                continue

            return 'keep', direction_keyword

        else:
            print("❌ 无效选择，请输入 K, S 或 Q")


def main():
    """主函数"""
    print_section("步骤A5：人工筛选方向（交互式）")

    logger = setup_logging()

    # 1. 加载cluster_summary_A3.csv
    print_subsection("1. 加载簇级汇总数据")

    # 使用正确的输出文件名
    summary_file = Path(str(A3_CONFIG['output_summary']).replace('clusters_summary_stageA.csv', 'cluster_summary_A3.csv'))

    try:
        df_summary = load_csv(summary_file)
    except FileNotFoundError:
        print(f"\n❌ 文件不存在: {summary_file}")
        print("\n请先运行 step_A3_clustering.py 生成簇级汇总")
        return 1

    print(f"加载了 {len(df_summary)} 个簇")

    # 2. 过滤噪音簇
    print_subsection("2. 过滤数据")

    # 过滤噪音簇（cluster_id_A == -1）
    df_valid = df_summary[df_summary['cluster_id_A'] != -1].copy()

    print(f"有效簇数: {len(df_valid)}")
    print(f"噪音簇数: {len(df_summary) - len(df_valid)}")

    # 按total_frequency降序排列（最重要的簇排在前面）
    df_valid = df_valid.sort_values('total_frequency', ascending=False).reset_index(drop=True)

    # 3. 交互式筛选
    print_section("开始交互式筛选")
    print("\n说明:")
    print("  - 系统将逐个显示簇的信息")
    print("  - 你可以选择保留（K）、跳过（S）或结束（Q）")
    print("  - 对于保留的簇，需要输入方向关键词")
    print("  - 建议筛选 5-10 个清晰的方向")

    input("\n按 Enter 键开始...")

    # 存储筛选结果
    selected_directions = []

    for idx, row in df_valid.iterrows():
        # 显示簇信息
        display_cluster_info(row, idx)

        # 获取用户选择
        action, direction_keyword = get_user_choice(idx + 1)

        if action == 'stop':
            print("\n✅ 用户选择结束筛选")
            break

        elif action == 'keep':
            # 保存方向
            selected_directions.append({
                'direction_keyword': direction_keyword,
                'cluster_id_A': row['cluster_id_A'],
                'cluster_size': row['cluster_size'],
                'total_frequency': row['total_frequency'],
                'seed_words_in_cluster': row['seed_words_in_cluster'],
                'example_phrases': row.get('example_phrases', ''),
            })

            print(f"\n✅ 已保留方向: {direction_keyword}")
            print(f"   当前已选 {len(selected_directions)} 个方向")

        elif action == 'skip':
            print(f"\n⏭️  已跳过簇 #{idx + 1}")

    # 4. 保存结果
    print_section("保存筛选结果")

    if not selected_directions:
        print("\n⚠️  没有选择任何方向")
        print("未生成 direction_keywords.csv")
        return 0

    # 创建DataFrame
    df_directions = pd.DataFrame(selected_directions)

    # 保存到direction_keywords.csv
    output_file = Path(A3_CONFIG['output_summary']).parent / 'direction_keywords.csv'
    save_csv(df_directions, output_file)

    # 5. 显示总结
    print_section("筛选完成")

    print(f"\n✅ 共筛选出 {len(selected_directions)} 个方向")
    print(f"\n方向列表:")

    for i, direction in enumerate(selected_directions, 1):
        print(f"  {i}. {direction['direction_keyword']}")
        print(f"     簇ID={direction['cluster_id_A']}, "
              f"大小={direction['cluster_size']}, "
              f"频次={direction['total_frequency']:.0f}")

    print(f"\n📁 输出文件: {output_file}")
    print(f"\n下一步: 运行 step_B1_expand_direction.py 扩展方向短语")

    return 0


if __name__ == "__main__":
    sys.exit(main())
