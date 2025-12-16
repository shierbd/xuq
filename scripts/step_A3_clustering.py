"""
步骤A3：语义聚类（完整优化版）
功能：将短语通过embedding和聚类算法分组成语义簇
输入：merged_keywords_all.csv（合并后的数据）
输出：
  - stageA_clusters.csv（带簇标签的短语）
  - cluster_summary_A3.csv（簇级统计，带example_phrases）

新增功能：
  - A3.1 预处理：文本标准化、去重合并、标记无效数据
  - A3.2 基础特征：word_count, phrase_length, query_type
  - A3.3 动态参数：根据数据量自动计算聚类参数
  - A3.4 输出增强：example_phrases, is_noise, cluster_size回填
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import re
from typing import Tuple

# 导入配置和工具
from config import A3_CONFIG, GENERAL_CONFIG
from utils import (
    setup_logging,
    load_csv,
    save_csv,
    print_section,
    print_subsection,
    print_stats,
    check_dependencies
)


# ==================== A3.3 动态参数计算 ====================

def calculate_cluster_params(phrase_count: int) -> Tuple[int, int]:
    """
    根据短语数量动态计算聚类参数

    参数:
        phrase_count: 短语总数

    返回:
        (min_cluster_size, min_samples)
    """
    # 启发式规则：min_cluster_size ≈ max(10, round(N / 500))
    min_cluster_size = max(10, round(phrase_count / 500))

    # min_samples根据数据量调整
    if phrase_count > 5000:
        min_samples = 3
    elif phrase_count > 2000:
        min_samples = 2
    else:
        min_samples = 2

    return min_cluster_size, min_samples


# ==================== A3.1 预处理功能 ====================

def preprocess_phrases(df: pd.DataFrame) -> pd.DataFrame:
    """
    A3.1 预处理：文本标准化、去重合并

    参数:
        df: 原始DataFrame

    返回:
        预处理后的DataFrame
    """
    logger = setup_logging()
    logger.info("A3.1 开始预处理...")

    original_count = len(df)

    # 1. 文本标准化（小写、去除多余空格）
    df['phrase'] = df['phrase'].str.lower().str.strip()
    df['phrase'] = df['phrase'].str.replace(r'\s+', ' ', regex=True)

    # 2. 标记无效数据
    df['is_invalid'] = False

    # 无效条件：空字符串、过长、过短
    df.loc[df['phrase'].str.len() == 0, 'is_invalid'] = True
    df.loc[df['phrase'].str.len() > 100, 'is_invalid'] = True
    df.loc[df['phrase'].str.len() < 3, 'is_invalid'] = True

    invalid_count = df['is_invalid'].sum()
    logger.info(f"  标记无效数据: {invalid_count} 条")

    # 过滤无效数据
    df = df[~df['is_invalid']].copy()

    # 3. 去重合并（保留frequency）
    logger.info(f"  去重前: {len(df)} 条")

    # 按phrase分组，合并frequency
    agg_dict = {
        'frequency': 'sum',  # 累加频次
    }

    # 只添加存在的列
    if 'seed_word' in df.columns:
        agg_dict['seed_word'] = 'first'  # 保留第一个种子词

    if 'source_type' in df.columns:
        agg_dict['source_type'] = 'first'  # 保留第一个来源类型

    if 'Volume' in df.columns:
        agg_dict['Volume'] = 'sum'  # 累加搜索量

    df_grouped = df.groupby('phrase', as_index=False).agg(agg_dict)

    # 如果没有seed_word列，添加一个空列
    if 'seed_word' not in df_grouped.columns:
        df_grouped['seed_word'] = 'unknown'

    # 如果没有source_type列，添加一个空列
    if 'source_type' not in df_grouped.columns:
        df_grouped['source_type'] = 'keyword_tool'

    logger.info(f"  去重后: {len(df_grouped)} 条")
    logger.info(f"  预处理完成，保留 {len(df_grouped)}/{original_count} 条短语")

    return df_grouped


# ==================== A3.2 基础特征 ====================

def add_basic_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    A3.2 添加基础特征字段

    参数:
        df: DataFrame

    返回:
        添加特征后的DataFrame
    """
    logger = setup_logging()
    logger.info("A3.2 添加基础特征...")

    # 1. word_count（单词数）
    df['word_count'] = df['phrase'].str.split().str.len()

    # 2. phrase_length（字符长度）
    df['phrase_length'] = df['phrase'].str.len()

    # 3. has_question_word（是否包含疑问词）
    question_words = ['how', 'what', 'why', 'where', 'when', 'who', 'which']
    pattern = r'\b(' + '|'.join(question_words) + r')\b'
    df['has_question_word'] = df['phrase'].str.contains(pattern, regex=True, case=False)

    # 4. has_best_or_top（是否包含best/top）
    df['has_best_or_top'] = df['phrase'].str.contains(r'\b(best|top)\b', regex=True, case=False)

    # 5. is_question_like（是否问句）
    df['is_question_like'] = (
        df['has_question_word'] |
        df['phrase'].str.contains(r'\?$', regex=True)
    )

    # 6. query_type（查询类型）
    def classify_query_type(row):
        if row['is_question_like']:
            return 'question'
        elif row['has_best_or_top']:
            return 'best_list'
        elif row['has_question_word']:
            return 'tutorial'
        else:
            return 'normal'

    df['query_type'] = df.apply(classify_query_type, axis=1)

    logger.info(f"  特征添加完成")
    logger.info(f"  - 平均单词数: {df['word_count'].mean():.1f}")
    logger.info(f"  - 平均字符长度: {df['phrase_length'].mean():.1f}")
    logger.info(f"  - 问句比例: {df['is_question_like'].mean()*100:.1f}%")

    return df


# ==================== 原有功能（保持不变） ====================

def load_embedding_model(model_name: str, use_gpu: bool = False):
    """
    加载embedding模型

    参数:
        model_name: 模型名称
        use_gpu: 是否使用GPU

    返回:
        SentenceTransformer模型
    """
    from sentence_transformers import SentenceTransformer

    logger = setup_logging()
    logger.info(f"正在加载embedding模型: {model_name}")

    device = 'cuda' if use_gpu else 'cpu'
    model = SentenceTransformer(model_name, device=device)

    logger.info(f"模型加载完成，使用设备: {device}")
    return model


def generate_embeddings(
    phrases: list,
    model,
    batch_size: int = 32
) -> np.ndarray:
    """
    为短语生成embedding向量

    参数:
        phrases: 短语列表
        model: embedding模型
        batch_size: 批处理大小

    返回:
        embedding矩阵 (n_samples, embedding_dim)
    """
    logger = setup_logging()
    logger.info(f"正在生成 {len(phrases):,} 条短语的embedding...")

    embeddings = model.encode(
        phrases,
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True
    )

    logger.info(f"Embedding生成完成，维度: {embeddings.shape}")
    return embeddings


def cluster_hdbscan(
    embeddings: np.ndarray,
    min_cluster_size: int = 5,
    min_samples: int = 2
) -> np.ndarray:
    """
    使用HDBSCAN进行聚类

    参数:
        embeddings: embedding矩阵
        min_cluster_size: 最小簇大小
        min_samples: 最小样本数

    返回:
        簇标签数组
    """
    import hdbscan

    logger = setup_logging()
    logger.info(f"正在使用HDBSCAN聚类...")
    logger.info(f"  min_cluster_size={min_cluster_size}")
    logger.info(f"  min_samples={min_samples}")

    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric='euclidean',
        cluster_selection_method='eom'
    )

    cluster_labels = clusterer.fit_predict(embeddings)

    # 统计聚类结果
    n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
    n_noise = list(cluster_labels).count(-1)

    logger.info(f"聚类完成:")
    logger.info(f"  簇数量: {n_clusters}")
    logger.info(f"  噪音点数: {n_noise} ({n_noise/len(cluster_labels)*100:.1f}%)")

    return cluster_labels


# ==================== A3.4 输出增强 ====================

def add_cluster_size_to_phrases(df: pd.DataFrame) -> pd.DataFrame:
    """
    A3.4 将cluster_size回填到短语表

    参数:
        df: 包含cluster_id_A的DataFrame

    返回:
        添加cluster_size的DataFrame
    """
    logger = setup_logging()
    logger.info("A3.4 回填cluster_size...")

    # 计算每个簇的大小
    cluster_sizes = df.groupby('cluster_id_A').size().to_dict()

    # 回填到短语表
    df['cluster_size'] = df['cluster_id_A'].map(cluster_sizes)

    # 添加is_noise标志
    df['is_noise'] = df['cluster_id_A'] == -1

    logger.info(f"  cluster_size回填完成")

    return df


def compute_cluster_summary_enhanced(df: pd.DataFrame) -> pd.DataFrame:
    """
    A3.4 计算簇级统计信息（增强版，包含example_phrases）

    参数:
        df: 包含cluster_id_A的DataFrame

    返回:
        簇级统计DataFrame
    """
    logger = setup_logging()
    logger.info("正在计算簇级统计（增强版）...")

    def get_example_phrases(group, n=5):
        """获取簇的代表性短语"""
        # 按频次排序，取前n个
        examples = group.nlargest(n, 'frequency')['phrase'].tolist()
        return '; '.join(examples)

    # 分组聚合
    summary = df.groupby('cluster_id_A').apply(lambda g: pd.Series({
        'cluster_size': len(g),
        'total_frequency': g['frequency'].sum(),
        'avg_frequency': g['frequency'].mean(),
        'seed_words_in_cluster': ','.join(sorted(set(g['seed_word']))),
        'total_search_volume': g['Volume'].sum() if 'Volume' in g.columns else 0,
        'avg_search_volume': g['Volume'].mean() if 'Volume' in g.columns else 0,
        'example_phrases': get_example_phrases(g, n=5),
        'avg_word_count': g['word_count'].mean() if 'word_count' in g.columns else 0,
        'question_ratio': g['is_question_like'].mean() if 'is_question_like' in g.columns else 0,
    })).reset_index()

    # 添加noise_flag
    summary['noise_flag'] = summary['cluster_id_A'] == -1

    # 排序（按总频次降序，噪音簇放最后）
    summary = summary.sort_values(
        ['noise_flag', 'total_frequency'],
        ascending=[True, False]
    )

    logger.info(f"簇级统计完成，共 {len(summary)} 个簇")

    return summary


# ==================== 主函数 ====================

def main():
    """主函数"""
    print_section("步骤A3：语义聚类（完整优化版）")

    # 检查依赖
    if not check_dependencies():
        return 1

    # 加载配置
    config = A3_CONFIG
    print("\n配置信息:")
    print(f"  输入文件: {config['input_file']}")
    print(f"  Embedding模型: {config['embedding_model']}")
    print(f"  聚类方法: {config['clustering_method']}")

    try:
        # 1. 加载数据
        print_subsection("1. 加载数据")
        df = load_csv(config['input_file'])

        # 重命名Keyword列为phrase（统一命名）
        if 'Keyword' in df.columns and 'phrase' not in df.columns:
            df['phrase'] = df['Keyword']

        # 添加frequency列（如果没有）
        if 'frequency' not in df.columns:
            df['frequency'] = 1

        print_stats(df, "原始数据")

        # 2. A3.1 预处理
        print_subsection("2. A3.1 预处理")
        df = preprocess_phrases(df)

        # 3. A3.2 添加基础特征
        print_subsection("3. A3.2 添加基础特征")
        df = add_basic_features(df)

        # 4. 数据筛选（可选）
        print_subsection("4. 数据筛选")

        # 过滤低搜索量数据
        if config.get('min_volume', 0) > 0 and 'Volume' in df.columns:
            before = len(df)
            df = df[df['Volume'] >= config['min_volume']]
            print(f"过滤低搜索量 (< {config['min_volume']}): {before:,} -> {len(df):,}")

        # 限制最大短语数
        if config.get('max_phrases') and len(df) > config['max_phrases']:
            df = df.nlargest(config['max_phrases'], 'Volume' if 'Volume' in df.columns else 'frequency')
            print(f"限制最大短语数: {config['max_phrases']:,}")

        phrases = df['phrase'].tolist()
        print(f"待聚类短语数: {len(phrases):,}")

        # 5. A3.3 动态计算聚类参数
        print_subsection("5. A3.3 动态计算聚类参数")

        # 如果配置中启用了动态参数
        if config.get('use_dynamic_params', True):
            calc_min_cluster_size, calc_min_samples = calculate_cluster_params(len(phrases))
            print(f"根据数据量 ({len(phrases):,}) 计算参数:")
            print(f"  建议 min_cluster_size: {calc_min_cluster_size}")
            print(f"  建议 min_samples: {calc_min_samples}")

            # 使用计算的参数（除非配置中明确指定）
            if config.get('min_cluster_size') == 15:  # 默认值
                config['min_cluster_size'] = calc_min_cluster_size
                print(f"  → 使用计算的 min_cluster_size: {calc_min_cluster_size}")
            else:
                print(f"  → 使用配置的 min_cluster_size: {config['min_cluster_size']}")
        else:
            print(f"使用配置的固定参数:")
            print(f"  min_cluster_size: {config['min_cluster_size']}")
            print(f"  min_samples: {config['min_samples']}")

        # 6. 生成embeddings
        print_subsection("6. 生成Embeddings")
        model = load_embedding_model(
            config['embedding_model'],
            config.get('use_gpu', False)
        )
        embeddings = generate_embeddings(
            phrases,
            model,
            batch_size=config.get('batch_size', 32)
        )

        # 7. 执行聚类
        print_subsection("7. 执行聚类")
        if config['clustering_method'] == 'hdbscan':
            cluster_labels = cluster_hdbscan(
                embeddings,
                min_cluster_size=config['min_cluster_size'],
                min_samples=config['min_samples']
            )
        else:
            raise ValueError(f"未知的聚类方法: {config['clustering_method']}")

        # 8. A3.4 输出增强
        print_subsection("8. A3.4 输出增强")

        # 添加簇标签（改名为cluster_id_A）
        df['cluster_id_A'] = cluster_labels

        # 回填cluster_size和is_noise
        df = add_cluster_size_to_phrases(df)

        # 9. 计算簇级统计（增强版）
        print_subsection("9. 计算簇级统计")
        cluster_summary = compute_cluster_summary_enhanced(df)

        # 10. 保存结果
        print_subsection("10. 保存结果")

        # 保存短语级数据
        output_clusters = config['output_clusters']
        save_csv(df, output_clusters)

        # 保存簇级统计
        output_summary = Path(str(config['output_summary']).replace('clusters_summary_stageA.csv', 'cluster_summary_A3.csv'))
        save_csv(cluster_summary, output_summary)

        # 10.5 自动生成HTML查看器
        print_subsection("10.5 生成HTML查看器")
        try:
            from generate_html_viewer import generate_html_for_file

            output_dir = output_summary.parent.parent / 'output'
            output_dir.mkdir(exist_ok=True)

            html_file = output_dir / 'cluster_summary_A3.html'
            success = generate_html_for_file(
                csv_file=output_summary,
                output_html=html_file,
                title='A阶段聚类汇总 - Cluster Summary A3'
            )

            if success:
                print(f"[OK] HTML查看器: {html_file}")
                print(f"     提示: 双击打开，右键翻译为中文")
        except Exception as e:
            print(f"[!] HTML生成失败（不影响主流程）: {e}")

        # 11. 显示结果摘要
        print_section("聚类结果摘要")

        print(f"总短语数: {len(df):,}")
        print(f"有效簇数: {(cluster_summary['cluster_id_A'] != -1).sum()}")

        if -1 in df['cluster_id_A'].values:
            noise_count = (df['cluster_id_A'] == -1).sum()
            noise_ratio = noise_count / len(df) * 100
            print(f"噪音点数: {noise_count} ({noise_ratio:.1f}%)")

        print_subsection("Top 10 最大的簇")
        top_clusters = cluster_summary[cluster_summary['cluster_id_A'] != -1].head(10)
        for idx, row in top_clusters.iterrows():
            print(f"  簇 {row['cluster_id_A']:3d}: "
                  f"{row['cluster_size']:4d} 条短语, "
                  f"频次={row['total_frequency']:5.0f}")
            print(f"    种子词: {row['seed_words_in_cluster'][:50]}")
            print(f"    示例: {row['example_phrases'][:100]}...")

        print("\n" + "=" * 60)
        print("步骤A3执行成功！".center(60))
        print("=" * 60)
        print(f"\n输出文件:")
        print(f"  - {output_clusters}")
        print(f"  - {output_summary}")
        print(f"\n下一步：运行 python cluster_stats.py 查看质量报告")
        print(f"或：人工查看 {output_summary} 中的 example_phrases 字段")

        return 0

    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
