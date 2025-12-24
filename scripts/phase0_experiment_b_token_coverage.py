"""
Phase 0 - Experiment B: Token覆盖率测量
Token Coverage Measurement

目标：测量当前26个token覆盖了多少短语

判断标准：
- 覆盖率≥80% → token够用，暂不需要扩展
- 覆盖率≤60% → 需要实施Phase 2.2模板-变量迭代扩展

创建日期：2025-12-23
"""

import json
import io
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set
from collections import Counter
import sys

# Set UTF-8 encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.repository import PhraseRepository, TokenRepository
from storage.models import Phrase


def check_phrase_coverage(phrase: str, tokens: Set[str]) -> List[str]:
    """
    检查短语是否被tokens覆盖

    Args:
        phrase: 短语文本
        tokens: token集合

    Returns:
        匹配到的tokens列表
    """
    phrase_lower = phrase.lower()
    matched_tokens = []

    for token in tokens:
        if token.lower() in phrase_lower:
            matched_tokens.append(token)

    return matched_tokens


def analyze_uncovered_phrases(uncovered_phrases: List[str], top_k: int = 50) -> Dict:
    """
    分析未覆盖短语的特征

    Args:
        uncovered_phrases: 未覆盖的短语列表
        top_k: 提取top K个高频词

    Returns:
        分析结果字典
    """
    # 提取所有词
    all_words = []
    for phrase in uncovered_phrases:
        words = phrase.lower().split()
        all_words.extend(words)

    # 统计词频
    word_counter = Counter(all_words)

    # 过滤停用词
    BASIC_STOP_WORDS = {
        'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at',
        'to', 'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were'
    }

    filtered_words = [
        (word, freq) for word, freq in word_counter.most_common()
        if word not in BASIC_STOP_WORDS and len(word) > 2
    ]

    return {
        'top_words': filtered_words[:top_k],
        'total_unique_words': len(word_counter),
        'uncovered_sample': uncovered_phrases[:20]  # 前20个样本
    }


def run_experiment_b() -> Dict:
    """
    执行实验B：Token覆盖率测量

    Returns:
        实验结果字典
    """
    print("\n" + "="*70)
    print("Phase 0 - Experiment B: Token覆盖率测量")
    print("="*70)

    # 1. 加载所有短语
    print("\n1. 加载短语数据...")

    with PhraseRepository() as phrase_repo:
        all_phrases = phrase_repo.session.query(Phrase).all()

    total_phrases = len(all_phrases)
    print(f"✓ 短语总数: {total_phrases:,}")

    # 2. 加载当前tokens
    print("\n2. 加载Token词库...")

    with TokenRepository() as token_repo:
        tokens = token_repo.get_all_tokens()

    token_set = {token.token_text for token in tokens}
    token_count = len(token_set)

    print(f"✓ Token总数: {token_count}")
    print(f"\nToken列表:")
    for i, token in enumerate(sorted(token_set), 1):
        print(f"  {i:2d}. {token}")

    # 3. 检查覆盖率
    print(f"\n3. 检查Token覆盖率...")
    print("   (这可能需要几分钟...)")

    covered_phrases = []
    uncovered_phrases = []
    phrase_token_mapping = {}  # {phrase: [matched_tokens]}

    for phrase_obj in all_phrases:
        phrase = phrase_obj.phrase
        matched_tokens = check_phrase_coverage(phrase, token_set)

        if matched_tokens:
            covered_phrases.append(phrase)
            phrase_token_mapping[phrase] = matched_tokens
        else:
            uncovered_phrases.append(phrase)

    covered_count = len(covered_phrases)
    uncovered_count = len(uncovered_phrases)
    coverage_rate = covered_count / total_phrases if total_phrases > 0 else 0

    print(f"\n✓ 覆盖统计:")
    print(f"  - 被覆盖短语: {covered_count:,} ({coverage_rate:.1%})")
    print(f"  - 未覆盖短语: {uncovered_count:,} ({1-coverage_rate:.1%})")

    # 4. Token使用频率统计
    print("\n4. Token使用频率统计...")

    token_usage = Counter()
    for matched_tokens in phrase_token_mapping.values():
        token_usage.update(matched_tokens)

    print(f"\nTop 10 高频Token:")
    for i, (token, count) in enumerate(token_usage.most_common(10), 1):
        percentage = count / covered_count * 100 if covered_count > 0 else 0
        print(f"  {i:2d}. '{token:20s}' - {count:6,}次 ({percentage:5.1f}% of covered)")

    # 5. 分析未覆盖短语
    print("\n5. 分析未覆盖短语特征...")

    uncovered_analysis = analyze_uncovered_phrases(uncovered_phrases, top_k=50)

    print(f"\n未覆盖短语中的高频词（Top 20）:")
    for i, (word, freq) in enumerate(uncovered_analysis['top_words'][:20], 1):
        print(f"  {i:2d}. '{word:20s}' - {freq:6,}次")

    print(f"\n未覆盖短语样本（前10个）:")
    for i, phrase in enumerate(uncovered_analysis['uncovered_sample'][:10], 1):
        print(f"  {i:2d}. {phrase}")

    # 6. 生成结果
    result = {
        'experiment': 'B',
        'name': 'Token覆盖率',
        'timestamp': datetime.now().isoformat(),
        'total_phrases': total_phrases,
        'token_count': token_count,
        'tokens': sorted(list(token_set)),
        'covered_count': covered_count,
        'uncovered_count': uncovered_count,
        'coverage_rate': round(coverage_rate, 4),
        'token_usage': dict(token_usage.most_common()),
        'uncovered_top_words': uncovered_analysis['top_words'][:50],
        'uncovered_sample': uncovered_analysis['uncovered_sample']
    }

    # 7. 判断是否需要扩展
    if coverage_rate >= 0.80:
        result['recommendation'] = 'sufficient'
        result['recommendation_detail'] = f'Token覆盖率{coverage_rate:.1%}，词库充足，暂不需要扩展'
    elif coverage_rate <= 0.60:
        result['recommendation'] = 'need_expansion'
        result['recommendation_detail'] = f'Token覆盖率{coverage_rate:.1%}，词库不足，建议实施Phase 2.2模板-变量迭代扩展'
    else:
        result['recommendation'] = 'moderate'
        result['recommendation_detail'] = f'Token覆盖率{coverage_rate:.1%}，词库中等，可考虑适度扩展'

    # 8. 保存结果
    output_dir = project_root / 'data' / 'phase0_results'
    output_dir.mkdir(parents=True, exist_ok=True)

    result_file = output_dir / 'experiment_b_result.json'
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 9. 显示结果
    print("\n" + "="*70)
    print("实验B结果")
    print("="*70)
    print(f"短语总数:       {result['total_phrases']:,}")
    print(f"Token总数:      {result['token_count']}")
    print(f"被覆盖短语:     {result['covered_count']:,}")
    print(f"未覆盖短语:     {result['uncovered_count']:,}")
    print(f"覆盖率:         {result['coverage_rate']:.1%}")
    print(f"\n判断结果:       {result['recommendation']}")
    print(f"建议:           {result['recommendation_detail']}")
    print(f"\n结果已保存到: {result_file}")
    print("="*70)

    return result


if __name__ == "__main__":
    try:
        result = run_experiment_b()

        print("\n✅ 实验B完成！")
        print(f"\n📌 下一步：运行实验C（同义冗余率测量）")
        print(f"   命令: python scripts/phase0_experiment_c_redundancy.py")

    except KeyboardInterrupt:
        print("\n\n⚠️  实验被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 实验执行出错: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
