"""
Token提取辅助工具
从短语中提取候选tokens并统计频次
"""
import re
from typing import List, Dict, Set
from collections import Counter


# 停用词列表（英文常见停用词）
STOP_WORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
    'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
    'to', 'was', 'will', 'with', 'the', 'this', 'but', 'they', 'have',
    'had', 'what', 'when', 'where', 'who', 'which', 'why', 'how'
}

# 常见介词和冠词
FUNCTION_WORDS = {
    'about', 'after', 'all', 'also', 'any', 'back', 'because', 'but',
    'can', 'come', 'could', 'day', 'do', 'even', 'first', 'get',
    'give', 'go', 'good', 'her', 'him', 'his', 'i', 'if', 'into',
    'just', 'know', 'like', 'look', 'make', 'me', 'more', 'my',
    'new', 'no', 'not', 'now', 'one', 'only', 'or', 'other', 'our',
    'out', 'over', 'people', 'say', 'see', 'she', 'so', 'some',
    'take', 'than', 'them', 'then', 'there', 'these', 'think', 'time',
    'two', 'up', 'use', 'very', 'want', 'way', 'we', 'well', 'were',
    'what', 'when', 'which', 'who', 'will', 'would', 'year', 'you', 'your'
}

# 合并停用词
ALL_STOP_WORDS = STOP_WORDS | FUNCTION_WORDS


def clean_token(text: str) -> str:
    """
    清理token文本

    Args:
        text: 原始文本

    Returns:
        清理后的文本
    """
    # 转小写
    text = text.lower().strip()

    # 移除标点符号
    text = re.sub(r'[^\w\s-]', '', text)

    # 移除多余空格
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def is_valid_token(token: str, min_length: int = 2, max_length: int = 30) -> bool:
    """
    检查token是否有效

    Args:
        token: 待检查的token
        min_length: 最小长度
        max_length: 最大长度

    Returns:
        是否有效
    """
    # 长度检查
    if len(token) < min_length or len(token) > max_length:
        return False

    # 停用词检查
    if token.lower() in ALL_STOP_WORDS:
        return False

    # 纯数字检查
    if token.isdigit():
        return False

    # 包含字母检查（至少包含一个字母）
    if not any(c.isalpha() for c in token):
        return False

    return True


def extract_tokens_from_phrase(phrase: str) -> List[str]:
    """
    从单个短语中提取tokens

    Args:
        phrase: 短语文本

    Returns:
        token列表
    """
    # 清理短语
    cleaned = clean_token(phrase)

    # 分词（按空格和连字符）
    # 保留连字符组合，但也分别提取
    tokens = []

    # 按空格分词
    words = cleaned.split()

    for word in words:
        # 添加完整单词
        if is_valid_token(word):
            tokens.append(word)

        # 如果包含连字符，也分别提取
        if '-' in word:
            parts = word.split('-')
            for part in parts:
                if is_valid_token(part):
                    tokens.append(part)

    return tokens


def suggest_frequency_threshold(token_counter: Counter,
                               target_tokens: int = 1000,
                               show_distribution: bool = True) -> int:
    """
    根据token频次分布自动建议阈值

    Args:
        token_counter: token频次统计
        target_tokens: 目标保留的token数量
        show_distribution: 是否显示分布统计

    Returns:
        建议的最小频次阈值
    """
    freq_distribution = sorted(token_counter.values(), reverse=True)

    if show_distribution:
        print("\n  📊 Token频次分布统计:")
        thresholds = [3, 5, 8, 10, 15, 20, 30]
        for threshold in thresholds:
            count = sum(1 for freq in freq_distribution if freq >= threshold)
            print(f"     频次 >= {threshold:2d}: {count:5d} 个token")

    # 找到最接近目标数量的阈值
    thresholds_to_test = [3, 5, 8, 10, 15, 20, 30, 50]
    suggested = 8  # 默认建议值

    for threshold in thresholds_to_test:
        count = sum(1 for freq in freq_distribution if freq >= threshold)
        if count <= target_tokens:
            suggested = threshold
            break

    print(f"\n  💡 建议阈值: >= {suggested} (保留约 {sum(1 for f in freq_distribution if f >= suggested)} 个token)")
    print(f"     理由: 数据量 {len(freq_distribution)} 个唯一token，建议保留高频核心词")

    return suggested


def extract_tokens(phrases: List[str],
                  min_frequency: int = 8,
                  auto_suggest: bool = False) -> List[Dict]:
    """
    从短语列表中提取候选tokens并统计频次

    Args:
        phrases: 短语列表
        min_frequency: 最小频次（低于此频次的token会被过滤），默认8
        auto_suggest: 是否自动建议阈值

    Returns:
        候选token列表，每个元素包含 {'text': ..., 'frequency': ...}
    """
    print(f"\n🔍 从 {len(phrases)} 个短语中提取tokens...")

    # 统计所有tokens
    token_counter = Counter()

    for phrase in phrases:
        tokens = extract_tokens_from_phrase(phrase)
        token_counter.update(tokens)

    print(f"  ✓ 提取到 {len(token_counter)} 个唯一tokens")

    # 自动建议阈值
    if auto_suggest:
        suggested_threshold = suggest_frequency_threshold(token_counter)
        print(f"  ℹ️  当前使用阈值: {min_frequency}")
        if min_frequency != suggested_threshold:
            print(f"  ⚠️  建议调整为: {suggested_threshold} (使用 --min-frequency {suggested_threshold})")

    # 过滤低频tokens
    filtered_tokens = [
        {'text': token, 'frequency': count}
        for token, count in token_counter.items()
        if count >= min_frequency
    ]

    # 按频次排序
    filtered_tokens.sort(key=lambda x: x['frequency'], reverse=True)

    print(f"  ✓ 过滤后保留 {len(filtered_tokens)} 个tokens (频次>={min_frequency})")

    return filtered_tokens


def extract_bigrams(phrases: List[str], min_frequency: int = 3) -> List[Dict]:
    """
    提取二元词组（bigrams）

    **已废弃**: 请使用 extract_ngrams() 替代

    Args:
        phrases: 短语列表
        min_frequency: 最小频次

    Returns:
        bigram列表
    """
    print(f"\n🔍 提取二元词组...")

    bigram_counter = Counter()

    for phrase in phrases:
        tokens = extract_tokens_from_phrase(phrase)

        # 生成bigrams
        for i in range(len(tokens) - 1):
            bigram = f"{tokens[i]} {tokens[i+1]}"
            bigram_counter[bigram] += 1

    print(f"  ✓ 提取到 {len(bigram_counter)} 个唯一bigrams")

    # 过滤低频bigrams
    filtered_bigrams = [
        {'text': bigram, 'frequency': count}
        for bigram, count in bigram_counter.items()
        if count >= min_frequency
    ]

    filtered_bigrams.sort(key=lambda x: x['frequency'], reverse=True)

    print(f"  ✓ 过滤后保留 {len(filtered_bigrams)} 个bigrams (频次>={min_frequency})")

    return filtered_bigrams


def extract_ngrams(phrases: List[str],
                  max_gram_size: int = 4,
                  min_frequency: int = 5,
                  priority_mode: bool = True) -> List[Dict]:
    """
    提取N-gram短语（优先级提取模式）

    **优先级策略**:
    - 优先级1: N-gram (2-4词组合，原生词组)
    - 优先级2: 单token (用于补充)

    Args:
        phrases: 短语列表
        max_gram_size: 最大N值（1=unigram, 2=bigram, 3=trigram, 4=4-gram）
        min_frequency: 最小频次阈值
        priority_mode: True=优先模式(高频n-gram+低频单token), False=全部提取

    Returns:
        n-gram列表，每个元素包含:
        {
            'text': str,           # n-gram文本
            'frequency': int,      # 出现频次
            'gram_size': int,      # N值 (1=单词, 2=二元, etc.)
            'priority': int        # 优先级 (1=最高)
        }
    """
    print(f"\n🔍 提取N-gram词组 (max_gram={max_gram_size})...")

    # 按gram_size分别统计
    ngram_counters = {i: Counter() for i in range(1, max_gram_size + 1)}

    for phrase in phrases:
        tokens = extract_tokens_from_phrase(phrase)

        # 提取不同长度的n-grams
        for n in range(1, min(max_gram_size + 1, len(tokens) + 1)):
            for i in range(len(tokens) - n + 1):
                ngram = " ".join(tokens[i:i+n])
                ngram_counters[n][ngram] += 1

    # 统计
    for n in range(1, max_gram_size + 1):
        print(f"  ✓ {n}-gram: {len(ngram_counters[n])} 个唯一组合")

    # 优先级过滤策略
    all_ngrams = []

    if priority_mode:
        print(f"\n  📊 优先级过滤模式:")

        # 优先级1: 高频N-gram (n >= 2)
        for n in range(max_gram_size, 1, -1):  # 从大到小，优先保留长短语
            high_freq_threshold = min_frequency * (1 + (n - 2) * 0.5)  # 长短语允许更低频次

            for ngram, count in ngram_counters[n].items():
                if count >= high_freq_threshold:
                    all_ngrams.append({
                        'text': ngram,
                        'frequency': count,
                        'gram_size': n,
                        'priority': 1  # 最高优先级
                    })

            print(f"    - 优先级1: {n}-gram ≥ {high_freq_threshold:.0f}频次 → {len([x for x in all_ngrams if x['gram_size']==n])} 个")

        # 优先级2: 单token (补充词汇)
        # 降低单token的频次要求，但只保留未在n-gram中出现的
        ngram_tokens_set = set()
        for item in all_ngrams:
            ngram_tokens_set.update(item['text'].split())

        for token, count in ngram_counters[1].items():
            # 如果token已经在高优先级n-gram中出现，提高频次要求
            if token in ngram_tokens_set:
                threshold = min_frequency * 2  # 更高门槛
            else:
                threshold = min_frequency  # 标准门槛

            if count >= threshold:
                all_ngrams.append({
                    'text': token,
                    'frequency': count,
                    'gram_size': 1,
                    'priority': 2  # 次要优先级
                })

        unigram_count = len([x for x in all_ngrams if x['gram_size'] == 1])
        print(f"    - 优先级2: 1-gram(单token) ≥ {min_frequency}频次 → {unigram_count} 个")

    else:
        # 全部提取模式（无优先级区分）
        print(f"\n  📊 全部提取模式 (频次>={min_frequency}):")

        for n in range(1, max_gram_size + 1):
            for ngram, count in ngram_counters[n].items():
                if count >= min_frequency:
                    all_ngrams.append({
                        'text': ngram,
                        'frequency': count,
                        'gram_size': n,
                        'priority': 1
                    })

            count_at_n = len([x for x in all_ngrams if x['gram_size'] == n])
            print(f"    - {n}-gram: {count_at_n} 个")

    # 排序：优先级 > gram_size(降序) > 频次(降序)
    all_ngrams.sort(key=lambda x: (x['priority'], -x['gram_size'], -x['frequency']))

    print(f"\n  ✅ 总计提取: {len(all_ngrams)} 个词组")
    print(f"     - 优先级1 (n-gram): {len([x for x in all_ngrams if x['priority']==1])} 个")
    print(f"     - 优先级2 (单token): {len([x for x in all_ngrams if x['priority']==2])} 个")

    return all_ngrams


def extract_demand_patterns(phrases: List[str],
                           tokens_classified: Dict[str, str],
                           min_frequency: int = 5) -> List[Dict]:
    """
    从短语中提取需求模式（框架）

    Args:
        phrases: 短语列表
        tokens_classified: token分类字典 {token_text: token_type}
        min_frequency: 模式最小频次

    Returns:
        需求模式列表，每个元素包含 {'pattern': ..., 'frequency': ..., 'examples': [...]}
    """
    print(f"\n🔍 从 {len(phrases)} 个短语中提取需求模式...")

    pattern_counter = Counter()
    pattern_examples = {}  # 存储每个模式的示例短语

    for phrase in phrases:
        phrase_tokens = extract_tokens_from_phrase(phrase)

        # 构建模式
        pattern_parts = []
        for token in phrase_tokens:
            token_type = tokens_classified.get(token, 'other')
            pattern_parts.append(f"[{token_type}]")

        pattern = " ".join(pattern_parts)
        pattern_counter[pattern] += 1

        # 记录示例短语（每个模式最多保留5个示例）
        if pattern not in pattern_examples:
            pattern_examples[pattern] = []
        if len(pattern_examples[pattern]) < 5:
            pattern_examples[pattern].append(phrase)

    print(f"  ✓ 发现 {len(pattern_counter)} 种唯一需求模式")

    # 过滤低频模式
    filtered_patterns = [
        {
            'pattern': pattern,
            'frequency': count,
            'examples': pattern_examples.get(pattern, [])[:3]  # 只保留前3个示例
        }
        for pattern, count in pattern_counter.items()
        if count >= min_frequency
    ]

    # 按频次排序
    filtered_patterns.sort(key=lambda x: x['frequency'], reverse=True)

    print(f"  ✓ 过滤后保留 {len(filtered_patterns)} 种高频模式 (频次>={min_frequency})")

    return filtered_patterns


def analyze_token_framework(tokens_with_types: List[Dict],
                            patterns: List[Dict] = None) -> Dict:
    """
    分析需求框架词库的统计信息

    Args:
        tokens_with_types: 分类后的token列表
        patterns: 需求模式列表（可选）

    Returns:
        框架分析统计字典
    """
    print("\n📊 分析需求框架词库...")

    # 按类型分组统计
    type_stats = {}
    for token in tokens_with_types:
        token_type = token['token_type']
        if token_type not in type_stats:
            type_stats[token_type] = {
                'count': 0,
                'total_frequency': 0,
                'top_tokens': []
            }

        type_stats[token_type]['count'] += 1
        type_stats[token_type]['total_frequency'] += token.get('in_phrase_count', 0)

    # 为每个类型找出Top 10高频token
    for token_type in type_stats:
        tokens_of_type = [t for t in tokens_with_types if t['token_type'] == token_type]
        sorted_tokens = sorted(tokens_of_type,
                              key=lambda x: x.get('in_phrase_count', 0),
                              reverse=True)
        type_stats[token_type]['top_tokens'] = sorted_tokens[:10]

    analysis = {
        'total_tokens': len(tokens_with_types),
        'type_stats': type_stats,
        'patterns': patterns or []
    }

    print(f"  ✓ 分析完成")

    return analysis


def group_tokens_by_prefix(tokens: List[Dict], max_groups: int = 100) -> Dict[str, List[Dict]]:
    """
    按前缀分组tokens（用于批量LLM分类时减少重复）

    Args:
        tokens: token列表
        max_groups: 最大分组数

    Returns:
        分组字典 {prefix: [tokens]}
    """
    groups = {}

    for token in tokens:
        text = token['text']

        # 取前3个字符作为前缀
        prefix = text[:3] if len(text) >= 3 else text

        if prefix not in groups:
            groups[prefix] = []

        groups[prefix].append(token)

    # 如果分组太多，合并小分组
    if len(groups) > max_groups:
        sorted_groups = sorted(groups.items(), key=lambda x: len(x[1]), reverse=True)
        groups = dict(sorted_groups[:max_groups])

    return groups


def test_token_extraction():
    """测试token提取功能"""
    print("\n" + "="*70)
    print("测试Token提取")
    print("="*70)

    # 测试短语
    test_phrases = [
        "best running shoes for women",
        "top rated running shoes",
        "comfortable running shoes",
        "affordable running shoes",
        "running shoes for men",
        "how to choose running shoes",
        "running shoe sizing guide",
        "best budget running shoes",
        "nike running shoes",
        "adidas running shoes",
    ]

    # 提取tokens
    tokens = extract_tokens(test_phrases, min_frequency=2)

    print(f"\n提取结果 (Top 10):")
    for i, token in enumerate(tokens[:10], 1):
        print(f"  {i}. '{token['text']}' - 出现{token['frequency']}次")

    # 提取bigrams
    bigrams = extract_bigrams(test_phrases, min_frequency=2)

    print(f"\n二元词组 (Top 5):")
    for i, bigram in enumerate(bigrams[:5], 1):
        print(f"  {i}. '{bigram['text']}' - 出现{bigram['frequency']}次")

    print("\n✅ Token提取测试完成！")


if __name__ == "__main__":
    test_token_extraction()
