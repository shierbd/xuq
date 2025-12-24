"""
Phase 4: 小组聚类 + 需求卡片生成
对选中的大组进行小组聚类，并使用LLM生成需求卡片初稿

运行方式:
    python scripts/run_phase4_demands.py [--skip-llm] [--test-limit N]

参数:
    --skip-llm: 跳过LLM需求卡片生成（仅做聚类）
    --test-limit: 仅处理前N个选中的聚类（用于测试）
"""
import sys
import argparse
import numpy as np
from pathlib import Path
from collections import defaultdict

# 设置UTF-8编码输出（Windows兼容）
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import OUTPUT_DIR, CACHE_DIR, DEMAND_CARD_PHRASE_SAMPLE_SIZE
from core.clustering import cluster_phrases_small
from core.embedding import EmbeddingService
from ai.client import LLMClient
from storage.repository import (
    PhraseRepository,
    ClusterMetaRepository,
    DemandRepository,
    TokenRepository
)
from storage.models import Phrase, ClusterMeta, Demand
import pandas as pd
from utils.token_extractor import extract_tokens_from_phrase


def load_token_framework() -> dict:
    """
    从数据库加载Token框架词库

    Returns:
        tokens_classified: {token_text: token_type} 字典
    """
    print("\n📚 加载Token框架词库...")

    with TokenRepository() as repo:
        tokens = repo.get_all_tokens()

    if not tokens:
        print("  ⚠️  未找到Token框架，请先运行Phase 5提取Token")
        return {}

    tokens_classified = {
        token.token_text: token.token_type
        for token in tokens
    }

    print(f"  ✓ 加载了 {len(tokens_classified)} 个已分类tokens")

    # 按类型统计
    type_counts = {}
    for token_type in tokens_classified.values():
        type_counts[token_type] = type_counts.get(token_type, 0) + 1

    print(f"  分类统计:")
    for token_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"    - {token_type}: {count} 个")

    return tokens_classified


def extract_cluster_framework(phrases: list, tokens_classified: dict) -> dict:
    """
    提取小组的需求框架（intent/action/object tokens）

    Args:
        phrases: 短语文本列表
        tokens_classified: Token分类字典

    Returns:
        框架信息字典，包含各类型tokens及其频次
    """
    if not tokens_classified:
        return {}

    # 统计各类型tokens在此小组中的出现频次
    framework = {
        'intent': {},    # 意图词: {token: count}
        'action': {},    # 动作词: {token: count}
        'object': {},    # 对象词: {token: count}
        'other': {}      # 其他: {token: count}
    }

    for phrase in phrases:
        tokens = extract_tokens_from_phrase(phrase)
        for token in tokens:
            token_type = tokens_classified.get(token, 'other')
            if token_type in framework:
                framework[token_type][token] = framework[token_type].get(token, 0) + 1

    # 为每个类型排序并取Top 10
    for token_type in framework:
        sorted_tokens = sorted(framework[token_type].items(),
                              key=lambda x: x[1], reverse=True)
        framework[token_type] = sorted_tokens[:10]

    return framework


def format_framework_for_prompt(framework: dict) -> str:
    """
    将框架信息格式化为LLM prompt的一部分

    Args:
        framework: 框架信息字典

    Returns:
        格式化的文本
    """
    if not framework:
        return ""

    lines = ["\n【需求框架分析】"]
    lines.append("该小组的关键词分析结果：")

    if framework.get('intent'):
        intent_tokens = [f"{token}({count}次)" for token, count in framework['intent'][:5]]
        lines.append(f"  意图词: {', '.join(intent_tokens)}")

    if framework.get('action'):
        action_tokens = [f"{token}({count}次)" for token, count in framework['action'][:5]]
        lines.append(f"  动作词: {', '.join(action_tokens)}")

    if framework.get('object'):
        object_tokens = [f"{token}({count}次)" for token, count in framework['object'][:5]]
        lines.append(f"  对象词: {', '.join(object_tokens)}")

    lines.append("\n请基于以上框架分析，结合示例短语生成需求卡片。")

    return "\n".join(lines)


def load_embeddings_for_phrases(phrase_ids: list, round_id: int = 1) -> np.ndarray:
    """
    从缓存加载指定短语的embeddings

    Args:
        phrase_ids: 短语ID列表
        round_id: 轮次ID

    Returns:
        embeddings数组
    """
    # 加载缓存
    cache_file = CACHE_DIR / f'embeddings_round{round_id}.npz'
    if not cache_file.exists():
        raise FileNotFoundError(f"Embedding缓存文件不存在: {cache_file}")

    data = np.load(cache_file, allow_pickle=True)
    cache_dict = data['cache'].item()

    # 获取短语文本
    with PhraseRepository() as repo:
        phrases_db = repo.session.query(Phrase).filter(
            Phrase.phrase_id.in_(phrase_ids)
        ).all()

        phrase_map = {p.phrase_id: p.phrase for p in phrases_db}

    # 提取embeddings
    embeddings = []
    import hashlib
    for phrase_id in phrase_ids:
        if phrase_id not in phrase_map:
            raise ValueError(f"Phrase ID {phrase_id} 不存在")

        phrase = phrase_map[phrase_id]
        cache_key = hashlib.md5(phrase.encode('utf-8')).hexdigest()

        if cache_key not in cache_dict:
            raise ValueError(f"短语 '{phrase}' 的embedding不在缓存中")

        embeddings.append(cache_dict[cache_key])

    return np.array(embeddings)


def process_cluster_small_grouping(cluster_A: ClusterMeta,
                                    skip_llm: bool = False,
                                    round_id: int = 1,
                                    min_cluster_size_B: int = None,
                                    min_samples_B: int = None,
                                    tokens_classified: dict = None,
                                    use_framework: bool = False) -> list:
    """
    对单个大组进行小组聚类和需求卡片生成

    Args:
        cluster_A: 大组元数据
        skip_llm: 是否跳过LLM生成
        round_id: 数据轮次
        min_cluster_size_B: 小组最小聚类大小
        min_samples_B: 小组最小样本数
        tokens_classified: Token框架词库（如果使用框架模式）
        use_framework: 是否使用框架指导需求生成

    Returns:
        生成的需求卡片列表
    """
    cluster_id = cluster_A.cluster_id
    print(f"\n{'='*70}")
    print(f"处理大组 {cluster_id}: {cluster_A.main_theme}")
    print(f"{'='*70}")

    # 1. 加载该大组的所有短语
    print(f"\n【步骤1】加载大组短语...")
    with PhraseRepository() as repo:
        phrases_db = repo.get_phrases_by_cluster(cluster_id, cluster_level='A')

        if not phrases_db:
            print(f"  ⚠️  大组 {cluster_id} 没有短语，跳过")
            return []

        print(f"  ✓ 加载了 {len(phrases_db)} 条短语")

        # 转换为字典列表
        phrases = [{
            'phrase_id': p.phrase_id,
            'phrase': p.phrase,
            'frequency': p.frequency,
            'volume': p.volume,
            'seed_word': p.seed_word,
            'source_type': p.source_type,
        } for p in phrases_db]

        phrase_ids = [p['phrase_id'] for p in phrases]

    # 2. 加载embeddings
    print(f"\n【步骤2】加载embeddings...")
    try:
        embeddings = load_embeddings_for_phrases(phrase_ids, round_id)
        print(f"  ✓ 加载了 {embeddings.shape} embeddings")
    except Exception as e:
        print(f"  ❌ 加载embeddings失败: {str(e)}")
        return []

    # 3. 小组聚类
    print(f"\n【步骤3】执行小组聚类...")
    cluster_ids_B, cluster_info, clusterer = cluster_phrases_small(
        embeddings,
        phrases,
        parent_cluster_id=cluster_id,
        min_cluster_size=min_cluster_size_B,
        min_samples=min_samples_B
    )

    # 4. 更新数据库 - cluster_id_B
    print(f"\n【步骤4】更新数据库...")
    with PhraseRepository() as repo:
        success_count = 0
        for i, phrase_id in enumerate(phrase_ids):
            cluster_id_B = int(cluster_ids_B[i])
            if repo.update_cluster_assignment(phrase_id, cluster_id_B=cluster_id_B):
                success_count += 1

        print(f"  ✓ 已更新 {success_count}/{len(phrase_ids)} 条记录的cluster_id_B")

    # 5. 保存小组元数据
    print(f"\n【步骤5】保存小组元数据...")
    with ClusterMetaRepository() as repo:
        for label, info in cluster_info.items():
            # 为小组生成全局唯一的cluster_id_B
            # 格式: cluster_A * 10000 + local_label
            cluster_id_B = cluster_id * 10000 + label

            example_phrases_str = '; '.join(info['example_phrases'])

            repo.create_or_update_cluster(
                cluster_id=cluster_id_B,
                cluster_level='B',
                size=info['size'],
                example_phrases=example_phrases_str,
                main_theme=None,  # AI将生成
                total_frequency=info['total_frequency'],
                parent_cluster_id=cluster_id
            )

        print(f"  ✓ 已保存 {len(cluster_info)} 个小组的元数据")

    # 6. 生成需求卡片
    print(f"\n【步骤6】生成需求卡片...")

    demands = []

    if skip_llm:
        print("  ⚠️  跳过LLM需求卡片生成")
    else:
        try:
            llm = LLMClient()

            for label, info in cluster_info.items():
                cluster_id_B = cluster_id * 10000 + label

                # 采样短语（最多30条）
                phrases_sample = info['all_phrases'][:DEMAND_CARD_PHRASE_SAMPLE_SIZE]

                # 【新增】如果启用框架模式，提取小组框架
                framework_info = None
                if use_framework and tokens_classified:
                    framework_info = extract_cluster_framework(
                        phrases=info['all_phrases'],  # 使用全部短语提取框架
                        tokens_classified=tokens_classified
                    )

                    # 打印框架信息（调试用）
                    print(f"\n  小组{label}框架分析:")
                    if framework_info.get('intent'):
                        top_intent = [f"{t}({c})" for t, c in framework_info['intent'][:3]]
                        print(f"    意图: {', '.join(top_intent)}")
                    if framework_info.get('action'):
                        top_action = [f"{t}({c})" for t, c in framework_info['action'][:3]]
                        print(f"    动作: {', '.join(top_action)}")
                    if framework_info.get('object'):
                        top_object = [f"{t}({c})" for t, c in framework_info['object'][:3]]
                        print(f"    对象: {', '.join(top_object)}")

                # 调用LLM生成需求卡片
                demand_draft = llm.generate_demand_card(
                    cluster_id_A=cluster_id,
                    cluster_id_B=cluster_id_B,
                    main_theme=cluster_A.main_theme,
                    phrases=phrases_sample,
                    total_frequency=info['total_frequency'],
                    total_volume=info['total_volume'],
                    framework=framework_info  # 传入框架信息
                )

                # 保存到数据库
                # 将priority正确映射到business_value，demand_type默认为other
                priority_to_business = {
                    'high': 'high',
                    'medium': 'medium',
                    'low': 'low'
                }
                business_val = priority_to_business.get(
                    demand_draft.get('priority', 'medium').lower(),
                    'unknown'
                )

                with DemandRepository() as demand_repo:
                    demand = demand_repo.create_demand(
                        title=demand_draft['demand_title'],
                        description=demand_draft['demand_description'],
                        user_scenario=demand_draft['user_intent'],
                        demand_type='other',  # 默认为other，后续可人工标注为tool/content/service/education
                        source_cluster_A=cluster_id,
                        source_cluster_B=cluster_id_B,
                        related_phrases_count=info['size'],
                        business_value=business_val,  # 使用LLM生成的priority作为商业价值
                        status='idea'
                    )
                    # 在会话关闭前，使对象与会话分离但保留已加载的属性
                    demand_repo.session.expunge(demand)
                    demands.append(demand)

            print(f"  ✓ 已生成 {len(demands)} 个需求卡片")

        except Exception as e:
            print(f"  ❌ LLM需求卡片生成失败: {str(e)}")
            print(f"  提示: 使用 --skip-llm 参数跳过此步骤")

    # 7. 生成小组聚类统计
    print(f"\n【步骤7】小组聚类统计:")
    print(f"  - 小组数量: {len(cluster_info)}")
    noise_count = (cluster_ids_B == -1).sum()
    print(f"  - 噪音点数: {noise_count} ({noise_count/len(phrases)*100:.1f}%)")

    sizes = [info['size'] for info in cluster_info.values()]
    if sizes:
        print(f"  - 小组大小: 最小={min(sizes)}, 最大={max(sizes)}, 平均={np.mean(sizes):.1f}")

    return demands


def run_phase4_demands(skip_llm: bool = False,
                       test_limit: int = 0,
                       round_id: int = 1,
                       min_cluster_size_B: int = None,
                       min_samples_B: int = None,
                       use_framework: bool = False):
    """
    执行Phase 4: 小组聚类 + 需求卡片生成

    Args:
        skip_llm: 是否跳过LLM生成
        test_limit: 测试模式，仅处理前N个聚类
        round_id: 数据轮次
        min_cluster_size_B: 小组最小聚类大小
        min_samples_B: 小组最小样本数
        use_framework: 是否使用Token框架指导需求生成
    """
    print("\n" + "="*70)
    print("Phase 4: 小组聚类 + 需求卡片生成".center(70))
    print("="*70)

    # 【新增】如果启用框架模式，加载Token框架
    tokens_classified = {}
    if use_framework:
        print("\n⚙️  框架模式: 已启用")
        tokens_classified = load_token_framework()
        if not tokens_classified:
            print("\n⚠️  警告: 未找到Token框架，将使用传统模式")
            use_framework = False
    else:
        print("\n⚙️  传统模式: 不使用框架")

    # 1. 加载选中的大组
    print("\n【阶段1】加载选中的大组...")
    with ClusterMetaRepository() as repo:
        selected_clusters = repo.get_selected_clusters(cluster_level='A')

        if not selected_clusters:
            print("\n❌ 没有选中的大组！")
            print("  请先运行 Phase 3 并完成筛选")
            return False

        print(f"✓ 加载了 {len(selected_clusters)} 个选中的大组")

        # 【新增】断点续传：检查哪些大组已处理
        clusters_B_all = repo.get_all_clusters('B')
        processed_parents = set([c.parent_cluster_id for c in clusters_B_all if c.parent_cluster_id])

        if processed_parents:
            print(f"  已处理的大组: {len(processed_parents)} 个")
            print(f"  进度: {len(processed_parents)}/{len(selected_clusters)} ({len(processed_parents)/len(selected_clusters)*100:.1f}%)")

            # 过滤出未处理的大组
            unprocessed_clusters = [c for c in selected_clusters if c.cluster_id not in processed_parents]

            if not unprocessed_clusters:
                print("\n✅ 所有大组都已处理完成！")
                # 仍然继续，以便生成最终报告
                selected_clusters = selected_clusters
            else:
                print(f"  未处理的大组: {len(unprocessed_clusters)} 个")
                print(f"  ID列表: {sorted([c.cluster_id for c in unprocessed_clusters])}")
                print("\n💡 断点续传: 将只处理未完成的大组")
                selected_clusters = unprocessed_clusters

        # 按大小排序（大的先处理）
        selected_clusters = sorted(selected_clusters, key=lambda x: x.size, reverse=True)

        # 测试模式
        if test_limit > 0:
            print(f"⚠️  测试模式: 仅处理前 {test_limit} 个大组")
            selected_clusters = selected_clusters[:test_limit]

    # 2. 对每个大组进行小组聚类
    print("\n【阶段2】小组聚类和需求卡片生成...")

    all_demands = []
    processed_count = 0
    failed_clusters = []

    for i, cluster_A in enumerate(selected_clusters, 1):
        print(f"\n进度: {i}/{len(selected_clusters)}")

        try:
            demands = process_cluster_small_grouping(
                cluster_A,
                skip_llm=skip_llm,
                round_id=round_id,
                min_cluster_size_B=min_cluster_size_B,
                min_samples_B=min_samples_B,
                tokens_classified=tokens_classified,
                use_framework=use_framework
            )
            all_demands.extend(demands)
            processed_count += 1

        except Exception as e:
            print(f"\n❌ 处理大组 {cluster_A.cluster_id} 时发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
            failed_clusters.append(cluster_A.cluster_id)

    # 3. 生成需求卡片CSV报告
    print("\n【阶段3】生成需求卡片报告...")

    # 【修改】从数据库加载所有需求（不只是本次生成的）
    print("  正在从数据库加载所有需求卡片...")
    with DemandRepository() as demand_repo:
        all_demands_from_db = demand_repo.session.query(Demand).order_by(Demand.demand_id).all()

    if all_demands_from_db:
        # 准备数据
        data = []
        for demand in all_demands_from_db:
            data.append({
                'demand_id': demand.demand_id,
                'title': demand.title,
                'description': demand.description,
                'user_scenario': demand.user_scenario,
                'demand_type': demand.demand_type,
                'source_cluster_A': demand.source_cluster_A,
                'source_cluster_B': demand.source_cluster_B,
                'related_phrases_count': demand.related_phrases_count,
                'business_value': demand.business_value,
                'status': demand.status,
            })

        df = pd.DataFrame(data)

        # 保存CSV
        OUTPUT_DIR.mkdir(exist_ok=True)
        csv_file = OUTPUT_DIR / 'demands_draft.csv'
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')

        print(f"  ✓ CSV文件: {csv_file}")
        print(f"  ✓ 数据库中共有 {len(all_demands_from_db)} 个需求卡片")
        print(f"  ✓ 本次运行新增 {len(all_demands)} 个需求卡片")

    else:
        print("  ⚠️  数据库中没有任何需求卡片")
        csv_file = None

    # 4. 生成统计报告
    print("\n【阶段4】生成统计报告...")

    report_lines = []
    report_lines.append("="*70)
    report_lines.append("Phase 4 小组聚类与需求卡片报告")
    report_lines.append("="*70)
    report_lines.append("")

    report_lines.append("【处理概况】")
    report_lines.append(f"  选中大组数: {len(selected_clusters)}")
    report_lines.append(f"  成功处理: {processed_count}")
    if failed_clusters:
        report_lines.append(f"  失败大组: {failed_clusters}")
    report_lines.append("")

    # 小组统计
    with ClusterMetaRepository() as repo:
        small_clusters = repo.get_all_clusters(cluster_level='B')
        print(f"  生成小组数: {len(small_clusters)}")

    report_lines.append("【小组聚类统计】")
    report_lines.append(f"  总小组数: {len(small_clusters)}")

    # 需求卡片统计
    if all_demands:
        report_lines.append("")
        report_lines.append("【需求卡片统计】")
        report_lines.append(f"  总需求数: {len(all_demands)}")

        # 按大组统计
        demands_by_cluster = defaultdict(int)
        for demand in all_demands:
            demands_by_cluster[demand.source_cluster_A] += 1

        report_lines.append("")
        report_lines.append("【各大组需求数量】")
        for cluster_id, count in sorted(demands_by_cluster.items(), key=lambda x: x[1], reverse=True):
            report_lines.append(f"  大组{cluster_id}: {count} 个需求")

    report_lines.append("")
    report_lines.append("="*70)
    report_lines.append("下一步: 在 demands_draft.csv 中审核并修改需求卡片")
    report_lines.append("="*70)

    # 输出报告
    report_text = '\n'.join(report_lines)
    print('\n' + report_text)

    # 保存报告
    report_file = OUTPUT_DIR / 'phase4_demands_report.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_text)

    print(f"\n💾 统计报告已保存: {report_file}")

    # 5. 完成
    print("\n" + "="*70)
    print("✅ Phase 4 完成！".center(70))
    print("="*70)

    print("\n📊 执行摘要:")
    print(f"  - 处理大组: {processed_count}/{len(selected_clusters)}")
    print(f"  - 生成小组: {len(small_clusters)}")
    if all_demands:
        print(f"  - 生成需求: {len(all_demands)}")
        print(f"  - 需求CSV: {csv_file}")
    print(f"  - 统计报告: {report_file}")

    print("\n📌 下一步:")
    if all_demands:
        print("  1. 在 demands_draft.csv 中审核和修改需求卡片")
        print("  2. 填写 business_value (high/medium/low)")
        print("  3. 修改 status (validated/archived)")
        print("  4. 运行导入脚本（待实现）")
    else:
        print("  重新运行并启用LLM生成需求卡片")

    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Phase 4: 小组聚类 + 需求卡片生成')
    parser.add_argument(
        '--skip-llm',
        action='store_true',
        help='跳过LLM需求卡片生成（仅做聚类）'
    )
    parser.add_argument(
        '--test-limit',
        type=int,
        default=0,
        help='测试模式：仅处理前N个选中的聚类（0=全部）'
    )
    parser.add_argument(
        '--round-id',
        type=int,
        default=1,
        help='数据轮次ID（默认为1）'
    )
    parser.add_argument(
        '--min-cluster-size',
        type=int,
        default=None,
        help='小组最小聚类大小（默认使用配置文件中的值）'
    )
    parser.add_argument(
        '--min-samples',
        type=int,
        default=None,
        help='小组最小样本数（默认使用配置文件中的值）'
    )
    parser.add_argument(
        '--use-framework',
        action='store_true',
        help='使用Token框架指导需求生成（需先运行Phase 5）'
    )

    args = parser.parse_args()

    try:
        success = run_phase4_demands(
            skip_llm=args.skip_llm,
            test_limit=args.test_limit,
            round_id=args.round_id,
            min_cluster_size_B=args.min_cluster_size,
            min_samples_B=args.min_samples,
            use_framework=args.use_framework
        )
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
