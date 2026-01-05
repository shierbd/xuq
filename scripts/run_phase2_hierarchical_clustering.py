"""
Phase 2: 层次聚类 + LLM优化
使用Agglomerative Clustering生成初步聚类，然后用LLM验证和优化

方案优势：
1. 层次结构更符合语义关系
2. LLM可以验证聚类的语义一致性
3. 自动识别和分裂不一致的聚类
4. 生成有意义的聚类主题标签

运行方式：
    python scripts/run_phase2_hierarchical_clustering.py [选项]

参数：
    --round-id: 数据轮次ID（默认为1）
    --n-clusters: 目标聚类数量（默认120）
    --distance-threshold: 距离阈值（None=使用n_clusters）
    --linkage: 链接方法（ward, complete, average, single）
    --verify-with-llm: 是否使用LLM验证（默认True）
    --consistency-threshold: LLM一致性得分阈值（默认0.7）
"""
import sys
import argparse
import json
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.preprocessing import normalize
from sklearn.metrics import silhouette_score, davies_bouldin_score

# 添加项目根目录
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 编码修复
from utils.encoding_fix import setup_encoding
setup_encoding()

from config.settings import CACHE_DIR, OUTPUT_DIR, LLM_PROVIDER
from storage.repository import PhraseRepository, ClusterMetaRepository
from storage.models import Phrase
from core.llm_service import LLMService


def load_embeddings_and_phrases(round_id=1):
    """加载embeddings和短语信息（从数据库和缓存）"""
    print(f"\n加载数据...")

    # 1. 从数据库加载短语
    with PhraseRepository() as repo:
        phrases_db = repo.session.query(Phrase).all()
        phrases = [{
            'phrase_id': p.phrase_id,
            'phrase': p.phrase,
            'frequency': p.frequency,
            'volume': p.volume,
        } for p in phrases_db]

    print(f"  从数据库加载了 {len(phrases):,} 条短语")

    # 2. 从缓存加载embeddings
    cache_file = CACHE_DIR / f"embeddings_round{round_id}.npz"
    print(f"  从缓存加载embeddings: {cache_file.name}")

    import hashlib
    data = np.load(cache_file, allow_pickle=True)
    cache_dict = data['cache'].item()

    # 3. 按照phrase顺序构建embeddings矩阵
    embeddings = []
    valid_phrases = []

    for p in phrases:
        cache_key = hashlib.md5(p['phrase'].encode('utf-8')).hexdigest()
        if cache_key in cache_dict:
            embeddings.append(cache_dict[cache_key])
            valid_phrases.append(p)

    embeddings = np.array(embeddings)

    print(f"  成功匹配 {len(valid_phrases):,}/{len(phrases):,} 条短语的embeddings")
    print(f"  Embeddings形状: {embeddings.shape}")

    return embeddings, valid_phrases


def run_agglomerative_clustering(embeddings_norm, n_clusters=120, linkage='ward'):
    """执行Agglomerative层次聚类"""
    print(f"\n【执行Agglomerative层次聚类】")
    print(f"  目标聚类数: {n_clusters}")
    print(f"  链接方法: {linkage}")
    print(f"  样本数: {len(embeddings_norm):,}")

    # 对于大数据集，使用采样评估最优聚类数
    if len(embeddings_norm) > 10000:
        print(f"\n  数据集较大，采样评估最优聚类数...")
        sample_indices = np.random.choice(len(embeddings_norm), 10000, replace=False)
        sample_embeddings = embeddings_norm[sample_indices]

        # 测试不同聚类数
        test_n_clusters = [80, 100, 120, 150, 180]
        scores = []

        for n in test_n_clusters:
            print(f"    测试 n={n}...", end='')
            clusterer = AgglomerativeClustering(n_clusters=n, linkage=linkage)
            labels = clusterer.fit_predict(sample_embeddings)
            silhouette = silhouette_score(sample_embeddings, labels)
            scores.append((n, silhouette))
            print(f" 轮廓系数={silhouette:.4f}")

        # 选择最佳n_clusters
        best_n = max(scores, key=lambda x: x[1])[0]
        print(f"\n  ✓ 推荐聚类数: {best_n}")
        n_clusters = best_n

    # 执行聚类
    print(f"\n  开始聚类（这可能需要几分钟）...")
    clusterer = AgglomerativeClustering(
        n_clusters=n_clusters,
        linkage=linkage,
        compute_distances=False
    )

    cluster_ids = clusterer.fit_predict(embeddings_norm)

    print(f"\n  ✓ 聚类完成！")

    # 统计聚类大小
    unique, counts = np.unique(cluster_ids, return_counts=True)
    print(f"\n  聚类数量: {len(unique)}")
    print(f"  最小聚类: {counts.min()}")
    print(f"  最大聚类: {counts.max()}")
    print(f"  平均聚类: {counts.mean():.1f}")
    print(f"  中位聚类: {np.median(counts):.1f}")

    # 评估质量
    if len(embeddings_norm) <= 50000:
        print(f"\n  计算聚类质量指标...")
        silhouette = silhouette_score(embeddings_norm, cluster_ids, sample_size=10000)
        davies_bouldin = davies_bouldin_score(embeddings_norm, cluster_ids)
        print(f"    轮廓系数: {silhouette:.4f}")
        print(f"    Davies-Bouldin指数: {davies_bouldin:.4f}")

    return cluster_ids, clusterer


def verify_cluster_consistency_with_llm(phrases: List[str], cluster_id: int, llm_service: LLMService) -> Dict:
    """
    使用LLM验证聚类的语义一致性

    Returns:
        {
            'is_consistent': bool,
            'consistency_score': float (0-1),
            'main_theme': str,
            'subclusters': List[Dict] or None,  # 如果不一致，建议的子聚类
            'reasoning': str
        }
    """
    # 采样短语（最多30个）
    sample_size = min(30, len(phrases))
    sample_phrases = np.random.choice(phrases, sample_size, replace=False).tolist()

    prompt = f"""分析以下{len(sample_phrases)}个搜索短语，判断它们是否属于同一个语义类别。

短语列表：
{chr(10).join(f'{i+1}. {p}' for i, p in enumerate(sample_phrases))}

请分析：
1. 这些短语是否有共同的主题或意图？
2. 一致性得分（0-1，1表示完全一致）
3. 如果不一致（得分<0.7），建议如何分成2-3个子类别

请以JSON格式回答：
{{
    "is_consistent": true/false,
    "consistency_score": 0.0-1.0,
    "main_theme": "主题描述（3-5个词）",
    "subclusters": [  // 仅当is_consistent=false时提供
        {{"theme": "子主题1", "example_indices": [0, 1, 5]}},
        {{"theme": "子主题2", "example_indices": [2, 3, 4]}}
    ],
    "reasoning": "分析理由"
}}"""

    try:
        response = llm_service.generate(prompt, temperature=0.3, max_tokens=1000)

        # 提取JSON
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            return result
        else:
            print(f"  ⚠️ 聚类{cluster_id}: LLM返回格式错误")
            return {
                'is_consistent': True,
                'consistency_score': 0.5,
                'main_theme': 'Unknown',
                'reasoning': 'Parse error'
            }
    except Exception as e:
        print(f"  ⚠️ 聚类{cluster_id}: LLM验证失败 - {str(e)}")
        return {
            'is_consistent': True,
            'consistency_score': 0.5,
            'main_theme': 'Unknown',
            'reasoning': f'Error: {str(e)}'
        }


def split_inconsistent_cluster(cluster_phrases: List[Dict], embeddings: np.ndarray,
                                subclusters_info: List[Dict]) -> List[int]:
    """
    根据LLM建议分裂不一致的聚类

    Returns:
        新的子聚类标签列表
    """
    if not subclusters_info or len(subclusters_info) < 2:
        # 如果LLM没有提供分裂建议，使用KMeans分成2个
        from sklearn.cluster import KMeans
        kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
        return kmeans.fit_predict(embeddings)

    # 使用LLM建议的分组（基于相似度重新分配）
    n_subclusters = len(subclusters_info)

    # 对于小聚类，直接使用KMeans
    if len(cluster_phrases) < 100 or n_subclusters > 5:
        from sklearn.cluster import KMeans
        kmeans = KMeans(n_clusters=n_subclusters, random_state=42, n_init=10)
        return kmeans.fit_predict(embeddings)

    # 否则使用Agglomerative
    clusterer = AgglomerativeClustering(n_clusters=n_subclusters, linkage='ward')
    return clusterer.fit_predict(embeddings)


def verify_and_optimize_clusters(cluster_ids: np.ndarray, phrases: List[Dict],
                                  embeddings: np.ndarray,
                                  verify_with_llm: bool = True,
                                  consistency_threshold: float = 0.7) -> Tuple[np.ndarray, Dict]:
    """
    验证和优化聚类结果

    Returns:
        (优化后的cluster_ids, cluster_info字典)
    """
    print(f"\n【验证和优化聚类】")
    print(f"  LLM验证: {'启用' if verify_with_llm else '禁用'}")
    print(f"  一致性阈值: {consistency_threshold}")

    # 初始化LLM服务
    llm_service = None
    if verify_with_llm:
        try:
            llm_service = LLMService()
            print(f"  ✓ LLM服务已初始化（Provider: {LLM_PROVIDER}）")
        except Exception as e:
            print(f"  ⚠️ LLM服务初始化失败: {str(e)}")
            print(f"  将跳过LLM验证")
            verify_with_llm = False

    # 构建初始聚类信息
    unique_clusters = np.unique(cluster_ids)
    print(f"\n  初始聚类数: {len(unique_clusters)}")

    optimized_cluster_ids = cluster_ids.copy()
    cluster_info = {}
    next_cluster_id = max(unique_clusters) + 1

    inconsistent_count = 0
    split_count = 0

    for cluster_id in unique_clusters:
        indices = np.where(cluster_ids == cluster_id)[0]
        cluster_phrases = [phrases[i] for i in indices]
        cluster_embeddings = embeddings[indices]

        # 统计信息
        total_frequency = sum(p.get('frequency', 1) for p in cluster_phrases)
        total_volume = sum(p.get('volume', 0) for p in cluster_phrases)

        # 示例短语
        sorted_phrases = sorted(cluster_phrases, key=lambda x: x.get('frequency', 1), reverse=True)
        example_phrases = [p['phrase'] for p in sorted_phrases[:10]]

        print(f"\n  处理聚类 {cluster_id} (大小: {len(cluster_phrases)})...")

        # LLM验证
        main_theme = None
        is_consistent = True
        consistency_score = 1.0

        if verify_with_llm and llm_service and len(cluster_phrases) >= 5:
            phrase_texts = [p['phrase'] for p in cluster_phrases]
            verification = verify_cluster_consistency_with_llm(
                phrase_texts, cluster_id, llm_service
            )

            is_consistent = verification.get('is_consistent', True)
            consistency_score = verification.get('consistency_score', 1.0)
            main_theme = verification.get('main_theme', None)

            print(f"    一致性得分: {consistency_score:.2f}")
            print(f"    主题: {main_theme}")

            # 如果不一致，分裂聚类
            if not is_consistent or consistency_score < consistency_threshold:
                inconsistent_count += 1
                print(f"    ⚠️ 聚类不一致，尝试分裂...")

                subclusters_info = verification.get('subclusters', None)
                subcluster_labels = split_inconsistent_cluster(
                    cluster_phrases, cluster_embeddings, subclusters_info
                )

                # 更新聚类ID
                unique_sublabels = np.unique(subcluster_labels)
                if len(unique_sublabels) > 1:
                    split_count += len(unique_sublabels)
                    print(f"    ✓ 分裂为 {len(unique_sublabels)} 个子聚类")

                    for sublabel in unique_sublabels:
                        sub_indices = indices[subcluster_labels == sublabel]
                        new_cluster_id = next_cluster_id
                        next_cluster_id += 1

                        optimized_cluster_ids[sub_indices] = new_cluster_id

                        # 保存子聚类信息
                        sub_phrases = [phrases[i] for i in sub_indices]
                        sub_sorted = sorted(sub_phrases, key=lambda x: x.get('frequency', 1), reverse=True)
                        sub_examples = [p['phrase'] for p in sub_sorted[:10]]
                        sub_freq = sum(p.get('frequency', 1) for p in sub_phrases)
                        sub_vol = sum(p.get('volume', 0) for p in sub_phrases)

                        cluster_info[new_cluster_id] = {
                            'size': len(sub_phrases),
                            'total_frequency': sub_freq,
                            'total_volume': sub_vol,
                            'example_phrases': sub_examples,
                            'main_theme': f"{main_theme} (子聚类{sublabel+1})" if main_theme else None,
                            'consistency_score': None,
                            'parent_cluster': cluster_id
                        }

                    continue  # 跳过原聚类的保存

        # 保存聚类信息（一致的聚类或不做LLM验证的聚类）
        cluster_info[cluster_id] = {
            'size': len(cluster_phrases),
            'total_frequency': total_frequency,
            'total_volume': total_volume,
            'example_phrases': example_phrases,
            'main_theme': main_theme,
            'consistency_score': consistency_score,
            'parent_cluster': None
        }

    print(f"\n  ✓ 验证完成")
    print(f"    不一致聚类: {inconsistent_count}")
    print(f"    分裂产生的新聚类: {split_count}")
    print(f"    最终聚类数: {len(cluster_info)}")

    return optimized_cluster_ids, cluster_info


def update_database(cluster_ids, phrases, cluster_info, round_id=1):
    """更新数据库"""
    print("\n【更新数据库】")

    # 1. 更新phrases表
    print("\n  更新phrases表的cluster_id_A...")
    with PhraseRepository() as repo:
        success_count = 0
        for i, phrase in enumerate(phrases):
            phrase_id = phrase['phrase_id']
            cluster_id = int(cluster_ids[i])

            if repo.update_cluster_assignment(phrase_id, cluster_id_A=cluster_id):
                success_count += 1

        print(f"  ✓ 已更新 {success_count}/{len(phrases)} 条记录")

    # 2. 保存cluster_meta表
    print("\n  保存聚类元数据...")
    with ClusterMetaRepository() as repo:
        for cluster_id, info in cluster_info.items():
            example_phrases_str = '; '.join(info['example_phrases'])

            repo.create_or_update_cluster(
                cluster_id=cluster_id,
                cluster_level='A',
                size=info['size'],
                example_phrases=example_phrases_str,
                main_theme=info.get('main_theme'),
                total_frequency=info['total_frequency']
            )

        print(f"  ✓ 已保存 {len(cluster_info)} 个聚类的元数据")


def generate_report(cluster_ids, cluster_info, output_file):
    """生成优化聚类报告"""
    print("\n【生成聚类报告】")

    lines = []
    lines.append("="*70)
    lines.append("层次聚类 + LLM优化报告")
    lines.append("="*70)
    lines.append("")

    lines.append("【聚类概况】")
    lines.append(f"  算法: Agglomerative Clustering + LLM验证")
    lines.append(f"  聚类数: {len(cluster_info)}")
    lines.append(f"  总样本数: {len(cluster_ids):,}")
    lines.append("")

    lines.append("【聚类大小分布】")
    sizes = [info['size'] for info in cluster_info.values()]
    lines.append(f"  最小: {min(sizes)}")
    lines.append(f"  最大: {max(sizes)}")
    lines.append(f"  平均: {sum(sizes)/len(sizes):.1f}")
    lines.append(f"  中位数: {sorted(sizes)[len(sizes)//2]}")
    lines.append("")

    # 统计有主题的聚类
    themed_clusters = sum(1 for info in cluster_info.values() if info.get('main_theme'))
    if themed_clusters > 0:
        lines.append("【LLM生成的主题】")
        lines.append(f"  有主题标签的聚类: {themed_clusters}/{len(cluster_info)}")
        lines.append("")

    lines.append("【Top 20 最大聚类】")
    sorted_clusters = sorted(cluster_info.items(), key=lambda x: x[1]['size'], reverse=True)
    lines.append(f"{'排名':<5} {'聚类ID':<10} {'大小':<8} {'一致性':<10} {'主题':<30} {'示例短语'}")
    lines.append("-" * 120)

    for rank, (cluster_id, info) in enumerate(sorted_clusters[:20], 1):
        examples = ', '.join(info['example_phrases'][:3])
        if len(examples) > 35:
            examples = examples[:32] + '...'

        theme = info.get('main_theme', 'N/A')
        if theme and len(theme) > 28:
            theme = theme[:25] + '...'

        consistency = info.get('consistency_score')
        consistency_str = f"{consistency:.2f}" if consistency is not None else "N/A"

        lines.append(
            f"{rank:<5} {cluster_id:<10} {info['size']:<8} "
            f"{consistency_str:<10} {theme:<30} {examples}"
        )

    lines.append("")
    lines.append("="*70)
    lines.append("下一步: 运行 Phase 3 生成大组筛选报告")
    lines.append("="*70)

    report_text = '\n'.join(lines)
    print(report_text)

    # 保存报告
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_text)

    print(f"\n💾 报告已保存: {output_file}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Phase 2: 层次聚类 + LLM优化')
    parser.add_argument('--round-id', type=int, default=1, help='数据轮次ID')
    parser.add_argument('--n-clusters', type=int, default=120, help='目标聚类数量')
    parser.add_argument('--linkage', type=str, default='ward',
                       choices=['ward', 'complete', 'average', 'single'],
                       help='链接方法')
    parser.add_argument('--verify-with-llm', action='store_true', default=True,
                       help='是否使用LLM验证')
    parser.add_argument('--no-llm', dest='verify_with_llm', action='store_false',
                       help='禁用LLM验证')
    parser.add_argument('--consistency-threshold', type=float, default=0.7,
                       help='LLM一致性得分阈值')

    args = parser.parse_args()

    print("\n" + "="*70)
    print("层次聚类 + LLM优化".center(70))
    print("="*70)

    round_id = args.round_id

    # 1. 加载数据
    print("\n【步骤1】加载数据...")
    embeddings, phrases = load_embeddings_and_phrases(round_id)

    # 2. 归一化
    print("\n【步骤2】归一化向量...")
    embeddings_norm = normalize(embeddings, norm='l2')

    # 3. 执行层次聚类
    print("\n【步骤3】执行层次聚类...")
    cluster_ids, clusterer = run_agglomerative_clustering(
        embeddings_norm,
        n_clusters=args.n_clusters,
        linkage=args.linkage
    )

    # 4. LLM验证和优化
    print("\n【步骤4】LLM验证和优化...")
    optimized_cluster_ids, cluster_info = verify_and_optimize_clusters(
        cluster_ids, phrases, embeddings_norm,
        verify_with_llm=args.verify_with_llm,
        consistency_threshold=args.consistency_threshold
    )

    # 5. 更新数据库
    print("\n【步骤5】更新数据库...")
    update_database(optimized_cluster_ids, phrases, cluster_info, round_id)

    # 6. 生成报告
    print("\n【步骤6】生成报告...")
    OUTPUT_DIR.mkdir(exist_ok=True)
    report_file = OUTPUT_DIR / f'phase2_hierarchical_clustering_report_round{round_id}.txt'
    generate_report(optimized_cluster_ids, cluster_info, report_file)

    print("\n" + "="*70)
    print("✅ 层次聚类 + LLM优化完成！".center(70))
    print("="*70)

    print("\n📊 最终结果:")
    print(f"  - 处理短语数: {len(phrases):,}")
    print(f"  - 生成聚类数: {len(cluster_info)}")
    print(f"  - LLM验证: {'启用' if args.verify_with_llm else '禁用'}")
    print(f"  - 统计报告: {report_file}")

    print("\n📌 下一步:")
    print("  运行 Phase 3: python scripts/run_phase3_selection.py")


if __name__ == "__main__":
    main()
