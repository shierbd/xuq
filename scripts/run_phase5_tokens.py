"""
Phase 5: Token提取与分类
从短语中提取候选tokens并使用LLM进行分类，建立需求框架词库

运行方式:
    python scripts/run_phase5_tokens.py [--skip-llm] [--min-frequency N] [--sample-size N]

参数:
    --skip-llm: 跳过LLM分类（仅提取tokens）
    --min-frequency: 最小频次阈值（默认3）
    --sample-size: 采样短语数量（0=全部，默认10000）
    --round-id: 数据轮次ID（默认1）
"""
import sys
import argparse
from pathlib import Path
from typing import List, Dict
import pandas as pd

# 设置UTF-8编码输出（Windows兼容）
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import OUTPUT_DIR
from utils.token_extractor import (
    extract_tokens, extract_bigrams, extract_ngrams,
    extract_demand_patterns, analyze_token_framework
)
from ai.client import LLMClient
from storage.repository import PhraseRepository, TokenRepository


def load_phrases_for_token_extraction(sample_size: int = 0, round_id: int = 1) -> List[str]:
    """
    加载短语用于token提取

    Args:
        sample_size: 采样大小（0=全部）
        round_id: 数据轮次

    Returns:
        短语文本列表
    """
    print(f"\n📥 加载短语数据...")

    with PhraseRepository() as repo:
        # MVP版本：从所有短语中提取
        # 生产版本：仅从已验证需求的短语中提取
        # phrases_db = repo.session.query(Phrase).filter(
        #     Phrase.mapped_demand_id.isnot(None)
        # ).all()

        # 获取指定轮次的短语
        from storage.models import Phrase

        if sample_size > 0:
            phrases_db = repo.session.query(Phrase).limit(sample_size).all()
            print(f"  ✓ 加载了 {len(phrases_db)} 条短语（采样模式）")
        else:
            count = repo.get_phrase_count()
            print(f"  ✓ 准备加载所有 {count} 条短语...")
            phrases_db = repo.session.query(Phrase).all()
            print(f"  ✓ 加载完成")

    # 提取短语文本
    phrases = [p.phrase for p in phrases_db if p.phrase]

    print(f"  ✓ 有效短语: {len(phrases)} 条")

    return phrases


def save_tokens_to_csv(tokens_with_types: List[Dict], output_file: Path):
    """
    保存tokens(包含n-grams)到CSV用于审核

    Args:
        tokens_with_types: token/n-gram数据列表
        output_file: 输出文件路径
    """
    df = pd.DataFrame(tokens_with_types)

    # 重新排序列（增加gram_size列）
    columns = ['token_text', 'gram_size', 'token_type', 'in_phrase_count', 'confidence', 'verified', 'notes']
    df = df[[col for col in columns if col in df.columns]]

    # 按gram_size(降序)和频次(降序)排序
    df = df.sort_values(['gram_size', 'in_phrase_count'], ascending=[False, False])

    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"  ✓ CSV已保存: {output_file}")


def run_phase5_tokens(skip_llm: bool = False,
                      min_frequency: int = 8,
                      sample_size: int = 10000,
                      round_id: int = 1):
    """
    执行Phase 5: Token提取与分类

    Args:
        skip_llm: 是否跳过LLM分类
        min_frequency: 最小频次阈值（默认8）
        sample_size: 采样短语数量（0=全部）
        round_id: 数据轮次
    """
    print("\n" + "="*70)
    print("Phase 5: Token提取与分类".center(70))
    print("="*70)

    # 【阶段1】加载短语数据
    print("\n【阶段1】加载短语数据...")
    phrases = load_phrases_for_token_extraction(sample_size, round_id)

    if not phrases:
        print("\n❌ 没有可用的短语数据！")
        return False

    # 【阶段2】提取N-gram词组（优先级模式）
    print("\n【阶段2】提取N-gram词组...")
    print("  策略: 优先级1=原生n-gram(2-4词), 优先级2=单token(补充)")

    candidate_ngrams = extract_ngrams(
        phrases,
        max_gram_size=4,           # 提取 1-4词组合
        min_frequency=min_frequency,
        priority_mode=True          # 启用优先级模式
    )

    if not candidate_ngrams:
        print("\n❌ 没有提取到任何n-grams！")
        return False

    print(f"\n  📊 提取结果统计:")

    # 按gram_size统计
    by_gram_size = {}
    for ng in candidate_ngrams:
        g = ng['gram_size']
        by_gram_size[g] = by_gram_size.get(g, 0) + 1

    for gram_size in sorted(by_gram_size.keys(), reverse=True):
        count = by_gram_size[gram_size]
        print(f"    - {gram_size}-gram: {count} 个")

    # Top 10示例
    print(f"\n  🔝 Top 10 高频词组:")
    for i, ng in enumerate(candidate_ngrams[:10], 1):
        priority_mark = "⭐" if ng['priority'] == 1 else "  "
        print(f"      {priority_mark}{i}. [{ng['gram_size']}-gram] '{ng['text']}' - 出现 {ng['frequency']} 次")

    # 【阶段3】LLM批量分类
    tokens_with_types = []
    tokens_classified = {}  # {token_text: token_type}

    if skip_llm:
        print("\n【阶段3】⚠️  跳过LLM分类")
        # 使用默认类型
        for ng in candidate_ngrams:
            tokens_with_types.append({
                'token_text': ng['text'],
                'token_type': 'other',
                'gram_size': ng['gram_size'],
                'in_phrase_count': ng['frequency'],
                'confidence': 'low',
                'verified': False,
                'notes': '未分类'
            })
            tokens_classified[ng['text']] = 'other'
    else:
        print("\n【阶段3】LLM批量分类...")

        try:
            llm = LLMClient()

            # 提取n-gram文本列表
            ngram_texts = [ng['text'] for ng in candidate_ngrams]

            # 批量分类（对2-4词组合和单词都进行分类）
            classifications = llm.batch_classify_tokens(
                tokens=ngram_texts,
                batch_size=50
            )

            # 合并频次和分类结果
            ngram_data_map = {
                ng['text']: {'freq': ng['frequency'], 'gram_size': ng['gram_size']}
                for ng in candidate_ngrams
            }

            for classification in classifications:
                ngram_text = classification['token']
                token_type = classification.get('token_type', 'other')

                ng_data = ngram_data_map.get(ngram_text, {})

                tokens_with_types.append({
                    'token_text': ngram_text,
                    'token_type': token_type,
                    'gram_size': ng_data.get('gram_size', 1),
                    'in_phrase_count': ng_data.get('freq', 0),
                    'confidence': classification.get('confidence', 'medium'),
                    'verified': False,
                    'notes': None
                })

                tokens_classified[ngram_text] = token_type

            print(f"\n  ✓ 成功分类 {len(tokens_with_types)} 个n-grams")

            # 按类型统计
            type_counts = {}
            for token in tokens_with_types:
                token_type = token['token_type']
                type_counts[token_type] = type_counts.get(token_type, 0) + 1

            print(f"\n  📊 分类统计:")
            for token_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"    - {token_type}: {count} 个")

            # 按gram_size分类统计
            print(f"\n  📏 按词组长度统计:")
            by_gram = {}
            for token in tokens_with_types:
                g = token['gram_size']
                by_gram[g] = by_gram.get(g, 0) + 1

            for gram_size in sorted(by_gram.keys(), reverse=True):
                print(f"    - {gram_size}-gram: {by_gram[gram_size]} 个")

        except Exception as e:
            print(f"\n  ❌ LLM分类失败: {str(e)}")
            print(f"  提示: 使用 --skip-llm 参数跳过此步骤")
            return False

    # 【阶段4】提取需求模式（新增功能）
    demand_patterns = []
    if tokens_classified:
        print("\n【阶段4】提取需求模式...")
        try:
            demand_patterns = extract_demand_patterns(
                phrases=phrases,
                tokens_classified=tokens_classified,
                min_frequency=5
            )

            if demand_patterns:
                print(f"\n  高频需求模式 Top 10:")
                for i, pattern in enumerate(demand_patterns[:10], 1):
                    print(f"    {i}. {pattern['pattern']:40s} - {pattern['frequency']:5d}次")
                    if pattern['examples']:
                        print(f"       示例: {pattern['examples'][0]}")
        except Exception as e:
            print(f"  ⚠️  模式提取失败: {str(e)}")

    # 【阶段6】保存到数据库
    print("\n【阶段6】保存到数据库...")

    with TokenRepository() as repo:
        inserted_count = 0

        for token_data in tokens_with_types:
            try:
                token = repo.create_token(
                    token_text=token_data['token_text'],
                    token_type=token_data['token_type'],
                    in_phrase_count=token_data['in_phrase_count'],
                    first_seen_round=round_id,
                    verified=token_data['verified'],
                    notes=token_data.get('notes')
                )

                inserted_count += 1

            except Exception as e:
                print(f"    ⚠️  保存失败: {token_data['token_text']} - {str(e)}")
                continue

        print(f"  ✓ 成功保存 {inserted_count} 个tokens到数据库")

    # 【阶段7】生成CSV报告
    print("\n【阶段7】生成CSV报告...")

    OUTPUT_DIR.mkdir(exist_ok=True)
    csv_file = OUTPUT_DIR / 'tokens_extracted.csv'

    save_tokens_to_csv(tokens_with_types, csv_file)

    # 【阶段8】生成框架分析报告（新增功能）
    print("\n【阶段8】生成框架分析报告...")

    framework_analysis = analyze_token_framework(tokens_with_types, demand_patterns)

    report_lines = []
    report_lines.append("="*70)
    report_lines.append("Phase 5 需求框架词库分析报告")
    report_lines.append("="*70)
    report_lines.append("")

    report_lines.append("【数据概况】")
    report_lines.append(f"  输入短语数: {len(phrases):,}")
    report_lines.append(f"  最小频次阈值: {min_frequency}")
    report_lines.append(f"  提取n-gram数: {len(candidate_ngrams)}")
    report_lines.append("")

    # Token分类统计
    if not skip_llm and framework_analysis['type_stats']:
        report_lines.append("【Token分类统计】")
        for token_type, stats in sorted(framework_analysis['type_stats'].items(),
                                       key=lambda x: x[1]['count'], reverse=True):
            count = stats['count']
            percentage = count / framework_analysis['total_tokens'] * 100
            report_lines.append(f"  {token_type}: {count} 个 ({percentage:.1f}%)")
        report_lines.append("")

        # 每个类型的Top 10
        report_lines.append("【各类型高频Token Top 10】")
        for token_type in ['intent', 'action', 'object', 'other']:
            if token_type in framework_analysis['type_stats']:
                stats = framework_analysis['type_stats'][token_type]
                report_lines.append(f"\n  {token_type.upper()}:")
                for i, token in enumerate(stats['top_tokens'][:10], 1):
                    freq = token.get('in_phrase_count', 0)
                    report_lines.append(f"    {i:2d}. {token['token_text']:20s} - {freq:5d}次")

        report_lines.append("")

    # 高频N-gram Top 20
    report_lines.append("【高频N-gram Top 20】")
    for i, ng in enumerate(candidate_ngrams[:20], 1):
        token_info = next((t for t in tokens_with_types if t['token_text'] == ng['text']), None)
        token_type = token_info['token_type'] if token_info else 'unknown'
        gram_mark = f"[{ng['gram_size']}-gram]"
        report_lines.append(f"  {i:2d}. {gram_mark:10s} {ng['text']:25s} - {ng['frequency']:5d}次 [{token_type}]")
    report_lines.append("")

    # 需求模式
    if demand_patterns:
        report_lines.append("【高频需求模式 Top 20】")
        for i, pattern in enumerate(demand_patterns[:20], 1):
            report_lines.append(f"  {i:2d}. {pattern['pattern']:50s} - {pattern['frequency']:5d}次")
            if pattern['examples']:
                report_lines.append(f"      示例: {pattern['examples'][0]}")
        report_lines.append("")

    report_lines.append("="*70)
    report_lines.append("输出文件:")
    report_lines.append(f"  - Token CSV: {csv_file}")
    report_lines.append("="*70)

    # 输出报告
    report_text = '\n'.join(report_lines)
    print('\n' + report_text)

    # 保存报告
    report_file = OUTPUT_DIR / 'phase5_framework_report.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_text)

    print(f"\n💾 框架分析报告已保存: {report_file}")

    # 【完成】
    print("\n" + "="*70)
    print("✅ Phase 5 完成！".center(70))
    print("="*70)

    print("\n📊 执行摘要:")
    print(f"  - 处理短语: {len(phrases):,}")
    print(f"  - 提取n-grams: {len(candidate_ngrams)}")
    if not skip_llm:
        print(f"  - 已分类n-grams: {len(tokens_with_types)}")
    if demand_patterns:
        print(f"  - 需求模式: {len(demand_patterns)}")
    print(f"  - 保存到数据库: {inserted_count}")
    print(f"  - Token CSV: {csv_file}")
    print(f"  - 框架分析报告: {report_file}")

    print("\n📌 下一步:")
    print("  1. 审核 tokens_extracted.csv 中的token分类")
    print("  2. 修改错误的token_type")
    print("  3. 标记 verified=True 表示已审核")
    print("  4. 查看需求模式，理解用户搜索意图结构")
    print("  5. Token词库可用于需求模板化和相似度检测")

    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Phase 5: Token提取与分类')
    parser.add_argument(
        '--skip-llm',
        action='store_true',
        help='跳过LLM分类（仅提取tokens）'
    )
    parser.add_argument(
        '--min-frequency',
        type=int,
        default=8,
        help='最小频次阈值（默认8，推荐8-10）'
    )
    parser.add_argument(
        '--sample-size',
        type=int,
        default=10000,
        help='采样短语数量（0=全部，默认10000）'
    )
    parser.add_argument(
        '--round-id',
        type=int,
        default=1,
        help='数据轮次ID（默认1）'
    )

    args = parser.parse_args()

    try:
        success = run_phase5_tokens(
            skip_llm=args.skip_llm,
            min_frequency=args.min_frequency,
            sample_size=args.sample_size,
            round_id=args.round_id
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
