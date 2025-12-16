"""
自动化测试脚本：自动选择前5个簇作为方向
用于快速测试B阶段功能
"""

import pandas as pd
import sys
from pathlib import Path

# 导入配置和工具
from config import A3_CONFIG
from utils import load_csv, save_csv, print_section

def auto_select_directions(n=5):
    """
    自动选择前n个最大的簇作为方向

    参数:
        n: 选择的方向数量
    """
    print_section("自动化测试：自动选择方向")

    # 1. 加载cluster_summary_A3.csv
    summary_file = Path(str(A3_CONFIG['output_summary']).replace('clusters_summary_stageA.csv', 'cluster_summary_A3.csv'))

    df_summary = load_csv(summary_file)
    print(f"加载了 {len(df_summary)} 个簇")

    # 2. 过滤噪音簇
    df_valid = df_summary[df_summary['cluster_id_A'] != -1].copy()
    print(f"有效簇数: {len(df_valid)}")

    # 3. 按total_frequency降序排列，取前n个
    df_top = df_valid.nlargest(n, 'total_frequency')

    print(f"\n自动选择前 {n} 个簇作为方向：")

    # 4. 生成方向列表
    directions = []

    for idx, row in df_top.iterrows():
        # 从种子词生成direction_keyword
        seed_words = row.get('seed_words_in_cluster', '').split(',')
        # 取第一个种子词作为方向名
        direction_keyword = seed_words[0].strip() if seed_words else f"direction_{row['cluster_id_A']}"

        directions.append({
            'direction_keyword': direction_keyword,
            'cluster_id_A': row['cluster_id_A'],
            'cluster_size': row['cluster_size'],
            'total_frequency': row['total_frequency'],
            'seed_words_in_cluster': row.get('seed_words_in_cluster', ''),
            'example_phrases': row.get('example_phrases', ''),
        })

        print(f"  {idx + 1}. {direction_keyword} (簇ID={row['cluster_id_A']}, 大小={row['cluster_size']}, 频次={row['total_frequency']:.0f})")

    # 5. 保存结果
    df_directions = pd.DataFrame(directions)

    output_file = Path(A3_CONFIG['output_summary']).parent / 'direction_keywords.csv'
    save_csv(df_directions, output_file)

    print(f"\n[OK] 已保存 {len(directions)} 个方向到: {output_file}")
    print(f"\n下一步: 运行 python step_B3_cluster_stageB.py")

    return 0


if __name__ == "__main__":
    sys.exit(auto_select_directions(n=5))
