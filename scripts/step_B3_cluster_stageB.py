"""
步骤B3：方向内聚类（Stage B）
功能：对每个筛选出的方向进行二次聚类，发现方向内的需求分组
输入：
  - direction_keywords.csv（筛选出的方向）
  - stageA_clusters.csv（带A阶段簇标签的短语）
  - merged_keywords_all.csv（全量短语数据，用于扩展）
输出：
  - stageB_clusters.csv（带B阶段簇标签的短语）
  - cluster_summary_B3.csv（B阶段簇级统计）

流程：
  B3.1 加载方向列表
  B3.2 对每个方向，提取相关短语
  B3.3 对方向内短语进行二次聚类
  B3.4 生成B阶段簇标签（direction_keyword + cluster_id_B）
  B3.5 输出方向内的需求分组
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
from typing import Tuple

# 导入配置和工具
from config import A3_CONFIG, GENERAL_CONFIG
from utils import (
    setup_logging,
    load_csv,
    save_csv,
    print_section,
    print_subsection,
    print_stats
)


# ==================== B3.1 数据加载 ====================

def load_direction_data():
    """
    加载方向列表和短语数据

    返回:
        (df_directions, df_phrases) 元组
    """
    logger = setup_logging()

    # 加载direction_keywords.csv
    direction_file = Path(A3_CONFIG['output_summary']).parent / 'direction_keywords.csv'

    if not direction_file.exists():
        raise FileNotFoundError(
            f"未找到方向列表文件: {direction_file}\n"
            f"请先运行 manual_direction_selector.py 筛选方向"
        )

    df_directions = load_csv(direction_file)
    logger.info(f"加载了 {len(df_directions)} 个方向")

    # 加载stageA_clusters.csv（带A阶段簇标签）
    clusters_file = A3_CONFIG['output_clusters']

    df_phrases = load_csv(clusters_file)
    logger.info(f"加载了 {len(df_phrases):,} 条短语")

    return df_directions, df_phrases


# ==================== B3.2 提取方向相关短语 ====================

def extract_direction_phrases(df_phrases: pd.DataFrame, cluster_id_A: int) -> pd.DataFrame:
    """
    提取指定方向（cluster_id_A）的所有短语

    参数:
        df_phrases: 全量短语数据
        cluster_id_A: A阶段簇ID

    返回:
        该方向的短语DataFrame
    """
    df_direction = df_phrases[df_phrases['cluster_id_A'] == cluster_id_A].copy()
    return df_direction


# ==================== B3.3 方向内聚类 ====================

def cluster_within_direction(
    phrases: list,
    direction_name: str,
    min_cluster_size: int = 5,
    min_samples: int = 2
) -> np.ndarray:
    """
    对单个方向内的短语进行二次聚类

    参数:
        phrases: 短语列表
        direction_name: 方向名称（用于日志）
        min_cluster_size: 最小簇大小
        min_samples: 最小样本数

    返回:
        簇标签数组
    """
    from sentence_transformers import SentenceTransformer
    import hdbscan

    logger = setup_logging()

    # 如果短语数太少，不进行聚类
    if len(phrases) < min_cluster_size * 2:
        logger.info(f"  方向 '{direction_name}': 短语数太少 ({len(phrases)})，不进行聚类")
        return np.zeros(len(phrases), dtype=int)  # 全部归为簇0

    # 1. 生成embeddings
    logger.info(f"  方向 '{direction_name}': 生成embeddings...")

    model = SentenceTransformer(
        A3_CONFIG['embedding_model'],
        device='cpu'
    )

    embeddings = model.encode(
        phrases,
        batch_size=32,
        show_progress_bar=False,
        convert_to_numpy=True
    )

    # 2. HDBSCAN聚类
    logger.info(f"  方向 '{direction_name}': 执行HDBSCAN聚类...")

    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric='euclidean',
        cluster_selection_method='eom'
    )

    cluster_labels = clusterer.fit_predict(embeddings)

    # 统计
    n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
    n_noise = list(cluster_labels).count(-1)

    logger.info(f"  方向 '{direction_name}': 生成 {n_clusters} 个子簇, 噪音 {n_noise} 条")

    return cluster_labels


# ==================== B3.4 生成B阶段标签 ====================

def generate_cluster_id_B(direction_keyword: str, cluster_label: int) -> str:
    """
    生成B阶段簇ID

    格式: {direction_keyword}_B{cluster_id}
    示例: productivity_B0, productivity_B1, ...

    参数:
        direction_keyword: 方向关键词
        cluster_label: 簇标签

    返回:
        B阶段簇ID字符串
    """
    # 处理方向关键词（去空格，转小写）
    direction_key = direction_keyword.replace(' ', '_').lower()

    return f"{direction_key}_B{cluster_label}"


# ==================== B3.5 计算B阶段簇级统计 ====================

def compute_stageB_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    计算B阶段簇级统计

    参数:
        df: 包含cluster_id_B的DataFrame

    返回:
        B阶段簇级统计DataFrame
    """
    logger = setup_logging()
    logger.info("计算B阶段簇级统计...")

    def get_example_phrases(group, n=5):
        """获取簇的代表性短语"""
        examples = group.nlargest(n, 'frequency')['phrase'].tolist()
        return '; '.join(examples)

    # 分组聚合
    summary = df.groupby(['direction_keyword', 'cluster_id_B']).apply(lambda g: pd.Series({
        'cluster_size': len(g),
        'total_frequency': g['frequency'].sum(),
        'avg_frequency': g['frequency'].mean(),
        'seed_words_in_cluster': ','.join(sorted(set(g['seed_word']))),
        'total_search_volume': g['Volume'].sum() if 'Volume' in g.columns else 0,
        'example_phrases': get_example_phrases(g, n=5),
        'avg_word_count': g['word_count'].mean() if 'word_count' in g.columns else 0,
        'question_ratio': g['is_question_like'].mean() if 'is_question_like' in g.columns else 0,
    })).reset_index()

    # 添加is_noise标志
    summary['is_noise'] = summary['cluster_id_B'].str.endswith('_B-1')

    # 排序（按方向+总频次）
    summary = summary.sort_values(
        ['direction_keyword', 'total_frequency'],
        ascending=[True, False]
    )

    logger.info(f"B阶段簇级统计完成，共 {len(summary)} 个子簇")

    return summary


# ==================== 主函数 ====================

def main():
    """主函数"""
    print_section("步骤B3：方向内聚类（Stage B）")

    logger = setup_logging()

    try:
        # 1. 加载数据
        print_subsection("1. 加载数据")
        df_directions, df_phrases = load_direction_data()

        print(f"方向数: {len(df_directions)}")
        print(f"短语数: {len(df_phrases):,}")

        # 2. 对每个方向进行二次聚类
        print_subsection("2. 方向内聚类")

        all_results = []

        for idx, row in df_directions.iterrows():
            direction_keyword = row['direction_keyword']
            cluster_id_A = row['cluster_id_A']

            print(f"\n处理方向 {idx + 1}/{len(df_directions)}: {direction_keyword}")

            # B3.2 提取方向相关短语
            df_direction = extract_direction_phrases(df_phrases, cluster_id_A)

            print(f"  短语数: {len(df_direction)}")

            if len(df_direction) == 0:
                logger.warning(f"  方向 '{direction_keyword}' 没有短语，跳过")
                continue

            # B3.3 方向内聚类
            phrases = df_direction['phrase'].tolist()

            # 根据短语数量调整参数
            if len(phrases) < 50:
                min_cluster_size = 3
                min_samples = 2
            else:
                min_cluster_size = 5
                min_samples = 2

            cluster_labels_B = cluster_within_direction(
                phrases,
                direction_keyword,
                min_cluster_size=min_cluster_size,
                min_samples=min_samples
            )

            # B3.4 生成cluster_id_B
            df_direction['cluster_label_B'] = cluster_labels_B
            df_direction['cluster_id_B'] = df_direction['cluster_label_B'].apply(
                lambda x: generate_cluster_id_B(direction_keyword, x)
            )
            df_direction['direction_keyword'] = direction_keyword

            all_results.append(df_direction)

        # 3. 合并所有结果
        print_subsection("3. 合并结果")

        if not all_results:
            print("\n❌ 没有生成任何B阶段聚类结果")
            return 1

        df_stageB = pd.concat(all_results, ignore_index=True)

        print(f"B阶段短语总数: {len(df_stageB):,}")

        # 4. 计算B阶段簇级统计
        print_subsection("4. 计算簇级统计")

        df_summary_B = compute_stageB_summary(df_stageB)

        # 5. 保存结果
        print_subsection("5. 保存结果")

        # 保存stageB_clusters.csv
        output_clusters = Path(A3_CONFIG['output_clusters']).parent / 'stageB_clusters.csv'
        save_csv(df_stageB, output_clusters)

        # 保存cluster_summary_B3.csv
        output_summary = Path(A3_CONFIG['output_summary']).parent / 'cluster_summary_B3.csv'
        save_csv(df_summary_B, output_summary)

        # 5.5 自动生成HTML查看器
        print_subsection("5.5 生成HTML查看器")
        try:
            from generate_html_viewer import generate_html_for_file

            output_dir = output_summary.parent.parent / 'output'
            output_dir.mkdir(exist_ok=True)

            # 生成B阶段汇总的HTML
            html_file_B = output_dir / 'cluster_summary_B3.html'
            success_B = generate_html_for_file(
                csv_file=output_summary,
                output_html=html_file_B,
                title='B阶段聚类汇总 - Cluster Summary B3'
            )

            # 生成方向列表的HTML
            direction_file = Path(A3_CONFIG['output_summary']).parent / 'direction_keywords.csv'
            html_file_dir = output_dir / 'direction_keywords.html'
            success_dir = generate_html_for_file(
                csv_file=direction_file,
                output_html=html_file_dir,
                title='筛选的方向 - Selected Directions'
            )

            if success_B:
                print(f"[OK] B阶段HTML: {html_file_B}")
            if success_dir:
                print(f"[OK] 方向列表HTML: {html_file_dir}")
            if success_B or success_dir:
                print(f"     提示: 双击打开，右键翻译为中文")
        except Exception as e:
            print(f"[!] HTML生成失败（不影响主流程）: {e}")

        # 6. 显示结果摘要
        print_section("B阶段聚类结果摘要")

        print(f"\n总短语数: {len(df_stageB):,}")
        print(f"处理方向数: {df_directions['direction_keyword'].nunique()}")
        print(f"生成子簇数: {len(df_summary_B)}")

        # 按方向汇总
        print_subsection("按方向汇总")

        direction_stats = df_summary_B.groupby('direction_keyword').agg({
            'cluster_size': 'sum',
            'total_frequency': 'sum',
            'cluster_id_B': 'count'
        }).rename(columns={'cluster_id_B': 'sub_cluster_count'})

        direction_stats = direction_stats.sort_values('total_frequency', ascending=False)

        for direction, stats in direction_stats.iterrows():
            print(f"\n  {direction}:")
            print(f"    子簇数: {stats['sub_cluster_count']}")
            print(f"    短语数: {stats['cluster_size']}")
            print(f"    总频次: {stats['total_frequency']:.0f}")

        # Top 10 子簇示例
        print_subsection("Top 10 最大的子簇")

        top_clusters = df_summary_B[~df_summary_B['is_noise']].nlargest(10, 'total_frequency')

        for idx, row in top_clusters.iterrows():
            print(f"\n  子簇: {row['cluster_id_B']}")
            print(f"    方向: {row['direction_keyword']}")
            print(f"    大小: {row['cluster_size']} 条短语")
            print(f"    频次: {row['total_frequency']:.0f}")
            print(f"    示例: {row['example_phrases'][:80]}...")

        print("\n" + "=" * 60)
        print("步骤B3执行成功！".center(60))
        print("=" * 60)
        print(f"\n输出文件:")
        print(f"  - {output_clusters}")
        print(f"  - {output_summary}")
        print(f"\n下一步：人工查看 {output_summary} 分析方向内的需求分组")

        return 0

    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
