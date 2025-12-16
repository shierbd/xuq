"""
简易聚类可视化工具
功能：可视化聚类结果（A阶段或B阶段）
输入：
  - stageA_clusters.csv（A阶段聚类结果）
  - stageB_clusters.csv（B阶段聚类结果，可选）
输出：
  - output/clusters_visualization.html（交互式可视化图表）

使用方法：
    # 可视化A阶段聚类
    python plot_clusters.py --stage A

    # 可视化B阶段聚类
    python plot_clusters.py --stage B

    # 可视化指定方向的B阶段聚类
    python plot_clusters.py --stage B --direction productivity

依赖：
    pip install plotly scikit-learn
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import argparse

# 导入配置和工具
from config import A3_CONFIG, OUTPUT_DIR
from utils import setup_logging, load_csv, print_section


def generate_embeddings_for_viz(phrases: list, model_name: str = "all-MiniLM-L6-v2") -> np.ndarray:
    """
    生成embeddings用于可视化

    参数:
        phrases: 短语列表
        model_name: embedding模型名称

    返回:
        embeddings矩阵
    """
    from sentence_transformers import SentenceTransformer

    logger = setup_logging()
    logger.info(f"正在生成 {len(phrases):,} 条短语的embedding...")

    model = SentenceTransformer(model_name, device='cpu')

    embeddings = model.encode(
        phrases,
        batch_size=32,
        show_progress_bar=True,
        convert_to_numpy=True
    )

    return embeddings


def reduce_dimensions(embeddings: np.ndarray, method: str = 'umap', n_components: int = 2) -> np.ndarray:
    """
    降维到2D用于可视化

    参数:
        embeddings: 高维embedding矩阵
        method: 降维方法（'umap' 或 'tsne'）
        n_components: 目标维度

    返回:
        降维后的坐标矩阵 (n_samples, n_components)
    """
    logger = setup_logging()
    logger.info(f"使用 {method.upper()} 进行降维...")

    if method == 'umap':
        try:
            import umap
            reducer = umap.UMAP(
                n_components=n_components,
                random_state=42,
                n_neighbors=15,
                min_dist=0.1
            )
            coords = reducer.fit_transform(embeddings)
        except ImportError:
            logger.warning("未安装umap-learn，回退到TSNE（较慢）")
            logger.warning("建议安装: pip install umap-learn")
            method = 'tsne'

    if method == 'tsne':
        from sklearn.manifold import TSNE
        reducer = TSNE(
            n_components=n_components,
            random_state=42,
            perplexity=min(30, len(embeddings) - 1)
        )
        coords = reducer.fit_transform(embeddings)

    logger.info("降维完成")
    return coords


def create_interactive_plot(
    df: pd.DataFrame,
    coords: np.ndarray,
    cluster_col: str,
    title: str,
    output_file: Path
):
    """
    创建交互式可视化图表

    参数:
        df: 短语DataFrame
        coords: 2D坐标矩阵
        cluster_col: 簇标签列名
        title: 图表标题
        output_file: 输出HTML文件路径
    """
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    logger = setup_logging()
    logger.info("创建交互式图表...")

    # 添加坐标到DataFrame
    df = df.copy()
    df['x'] = coords[:, 0]
    df['y'] = coords[:, 1]

    # 获取唯一簇标签
    unique_clusters = sorted(df[cluster_col].unique())

    # 过滤噪音点（单独处理）
    is_noise = (df[cluster_col] == -1) | (df[cluster_col].astype(str).str.endswith('_B-1'))
    df_clusters = df[~is_noise]
    df_noise = df[is_noise]

    # 创建图表
    fig = go.Figure()

    # 添加每个簇的散点
    for cluster in unique_clusters:
        if cluster == -1 or (isinstance(cluster, str) and cluster.endswith('_B-1')):
            continue  # 噪音点单独处理

        df_cluster = df_clusters[df_clusters[cluster_col] == cluster]

        if len(df_cluster) == 0:
            continue

        # 生成悬停文本
        hover_texts = []
        for _, row in df_cluster.iterrows():
            text = f"<b>{row['phrase']}</b><br>"
            text += f"Cluster: {row[cluster_col]}<br>"
            text += f"Frequency: {row.get('frequency', 'N/A')}<br>"
            if 'seed_word' in row:
                text += f"Seed: {row['seed_word']}"
            hover_texts.append(text)

        fig.add_trace(go.Scatter(
            x=df_cluster['x'],
            y=df_cluster['y'],
            mode='markers',
            name=f'Cluster {cluster}',
            text=hover_texts,
            hoverinfo='text',
            marker=dict(
                size=8,
                opacity=0.7,
                line=dict(width=0.5, color='white')
            )
        ))

    # 添加噪音点（灰色）
    if len(df_noise) > 0:
        hover_texts = []
        for _, row in df_noise.iterrows():
            text = f"<b>{row['phrase']}</b><br>"
            text += "Cluster: Noise<br>"
            text += f"Frequency: {row.get('frequency', 'N/A')}"
            hover_texts.append(text)

        fig.add_trace(go.Scatter(
            x=df_noise['x'],
            y=df_noise['y'],
            mode='markers',
            name='Noise',
            text=hover_texts,
            hoverinfo='text',
            marker=dict(
                size=5,
                color='lightgray',
                opacity=0.3,
                line=dict(width=0)
            )
        ))

    # 设置布局
    fig.update_layout(
        title=title,
        xaxis_title="Dimension 1",
        yaxis_title="Dimension 2",
        hovermode='closest',
        width=1200,
        height=800,
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )

    # 保存HTML
    fig.write_html(str(output_file))
    logger.info(f"可视化图表已保存: {output_file}")


def visualize_stage_A(output_file: Path = None):
    """
    可视化A阶段聚类结果

    参数:
        output_file: 输出HTML文件路径
    """
    print_section("可视化A阶段聚类结果")

    logger = setup_logging()

    # 1. 加载数据
    clusters_file = A3_CONFIG['output_clusters']

    if not clusters_file.exists():
        print(f"\n❌ 文件不存在: {clusters_file}")
        print("请先运行 step_A3_clustering.py")
        return 1

    df = load_csv(clusters_file)

    print(f"加载了 {len(df):,} 条短语")
    print(f"簇数量: {df['cluster_id_A'].nunique()}")

    # 采样（如果数据量太大）
    if len(df) > 5000:
        print(f"\n数据量较大 ({len(df):,})，采样 5000 条进行可视化")
        df = df.sample(n=5000, random_state=42)

    # 2. 生成embeddings
    phrases = df['phrase'].tolist()
    embeddings = generate_embeddings_for_viz(phrases, A3_CONFIG['embedding_model'])

    # 3. 降维
    coords = reduce_dimensions(embeddings, method='umap')

    # 4. 创建可视化
    if output_file is None:
        output_file = OUTPUT_DIR / 'clusters_visualization_A.html'

    create_interactive_plot(
        df=df,
        coords=coords,
        cluster_col='cluster_id_A',
        title='Stage A Clustering Visualization',
        output_file=output_file
    )

    print(f"\n✅ 可视化完成: {output_file}")
    print(f"请在浏览器中打开该文件查看")

    return 0


def visualize_stage_B(direction: str = None, output_file: Path = None):
    """
    可视化B阶段聚类结果

    参数:
        direction: 指定方向（None=全部方向）
        output_file: 输出HTML文件路径
    """
    print_section(f"可视化B阶段聚类结果 {f'(方向: {direction})' if direction else ''}")

    logger = setup_logging()

    # 1. 加载数据
    clusters_file = Path(A3_CONFIG['output_clusters']).parent / 'stageB_clusters.csv'

    if not clusters_file.exists():
        print(f"\n❌ 文件不存在: {clusters_file}")
        print("请先运行 step_B3_cluster_stageB.py")
        return 1

    df = load_csv(clusters_file)

    print(f"加载了 {len(df):,} 条短语")
    print(f"方向数: {df['direction_keyword'].nunique()}")

    # 过滤指定方向
    if direction:
        df = df[df['direction_keyword'] == direction]
        print(f"过滤到方向 '{direction}': {len(df)} 条短语")

        if len(df) == 0:
            print(f"\n❌ 方向 '{direction}' 没有数据")
            return 1

    # 采样（如果数据量太大）
    if len(df) > 5000:
        print(f"\n数据量较大 ({len(df):,})，采样 5000 条进行可视化")
        df = df.sample(n=5000, random_state=42)

    # 2. 生成embeddings
    phrases = df['phrase'].tolist()
    embeddings = generate_embeddings_for_viz(phrases, A3_CONFIG['embedding_model'])

    # 3. 降维
    coords = reduce_dimensions(embeddings, method='umap')

    # 4. 创建可视化
    if output_file is None:
        if direction:
            output_file = OUTPUT_DIR / f'clusters_visualization_B_{direction}.html'
        else:
            output_file = OUTPUT_DIR / 'clusters_visualization_B.html'

    create_interactive_plot(
        df=df,
        coords=coords,
        cluster_col='cluster_id_B',
        title=f'Stage B Clustering Visualization{f" - {direction}" if direction else ""}',
        output_file=output_file
    )

    print(f"\n✅ 可视化完成: {output_file}")
    print(f"请在浏览器中打开该文件查看")

    return 0


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='可视化聚类结果')
    parser.add_argument(
        '--stage',
        type=str,
        choices=['A', 'B'],
        default='A',
        help='可视化阶段（A或B）'
    )
    parser.add_argument(
        '--direction',
        type=str,
        default=None,
        help='指定方向（仅在stage=B时有效）'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='输出HTML文件路径'
    )

    args = parser.parse_args()

    # 检查依赖
    try:
        import plotly
        import sklearn
    except ImportError as e:
        print(f"\n❌ 缺少依赖库: {e}")
        print("\n请安装:")
        print("  pip install plotly scikit-learn")
        print("\n可选（推荐）:")
        print("  pip install umap-learn")
        return 1

    # 执行可视化
    output_file = Path(args.output) if args.output else None

    if args.stage == 'A':
        return visualize_stage_A(output_file)
    else:
        return visualize_stage_B(args.direction, output_file)


if __name__ == "__main__":
    sys.exit(main())
