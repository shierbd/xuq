"""
关键词分词模块
提供英文关键词的分词、频次统计、排序等功能
"""
import re
from collections import Counter, defaultdict
from typing import List, Set, Tuple, Dict


def segment_keywords(keywords: List[str], stopwords: Set[str]) -> Counter:
    """
    将关键词短语分词并统计词频

    Args:
        keywords: 关键词短语列表
        stopwords: 停用词集合

    Returns:
        Counter对象，包含词频统计

    Example:
        >>> keywords = ["best running shoes", "running shoes for women"]
        >>> stopwords = {"for"}
        >>> counter = segment_keywords(keywords, stopwords)
        >>> counter.most_common(3)
        [('running', 2), ('shoes', 2), ('best', 1)]
    """
    word_counter = Counter()

    for keyword in keywords:
        # 转小写
        keyword_lower = keyword.lower()

        # 按空格和连字符分词
        words = re.split(r'[\s\-_]+', keyword_lower)

        # 过滤条件：
        # 1. 不在停用词列表中
        # 2. 长度 >= 2 (排除单字母)
        # 3. 仅包含字母 (排除纯数字或特殊符号)
        filtered_words = [
            w for w in words
            if w not in stopwords
            and len(w) >= 2
            and re.match(r'^[a-z]+$', w)
        ]

        word_counter.update(filtered_words)

    return word_counter


def segment_keywords_with_seed_tracking(phrases_objects: list, stopwords: Set[str],
                                        extract_ngrams: bool = False,
                                        min_ngram_frequency: int = 2) -> Tuple[Counter, Dict[str, Set[str]], Counter, Dict[str, Set[str]]]:
    """
    将关键词短语分词并统计词频，同时追踪每个词和短语来源于哪些seed_word
    可选地提取高频短语（n-grams）

    Args:
        phrases_objects: Phrase对象列表（需要有phrase和seed_word属性）
        stopwords: 停用词集合
        extract_ngrams: 是否提取n-gram短语（默认False）
        min_ngram_frequency: n-gram最小频次阈值（默认2，只保留出现2次以上的短语）

    Returns:
        (word_counter, word_to_seeds, ngram_counter, ngram_to_seeds)
        - word_counter: Counter对象，包含单词词频统计
        - word_to_seeds: {word: {seed1, seed2, ...}} 每个词对应的所有原始词根集合
        - ngram_counter: Counter对象，包含n-gram短语频次统计（如果extract_ngrams=False则为空）
        - ngram_to_seeds: {ngram: {seed1, seed2, ...}} 每个短语对应的所有原始词根集合

    Example:
        >>> phrases = [Phrase(phrase="best running shoes", seed_word="running")]
        >>> stopwords = {"for"}
        >>> counter, word_seeds, ngrams, ngram_seeds = segment_keywords_with_seed_tracking(phrases, stopwords, extract_ngrams=True)
        >>> word_seeds['running']
        {'running'}
        >>> ngram_seeds['best running']
        {'running'}
        >>> ngrams.most_common(5)
        [('best running', 10), ('running shoes', 15), ...]

    Note:
        短语提取采用数据驱动的方式，会自动提取2-6词的所有短语组合。
        用户应该在显示阶段根据实际数据筛选感兴趣的短语长度，而不是在提取阶段限制。
    """
    # 内部常量：最大n-gram长度
    # 设为6是合理的上限，大多数有意义的短语不超过6词
    # 例如："how to make money online fast" (6词)
    MAX_NGRAM_LENGTH = 6

    word_counter = Counter()
    word_to_seeds = defaultdict(set)  # 记录每个词对应的所有seed_word
    ngram_counter = Counter()  # 记录n-gram短语频次
    ngram_to_seeds = defaultdict(set)  # 记录每个n-gram对应的所有seed_word

    for phrase_obj in phrases_objects:
        keyword = phrase_obj.phrase
        seed_word = phrase_obj.seed_word or "unknown"  # 如果没有seed_word，标记为unknown

        # 转小写
        keyword_lower = keyword.lower()

        # 按空格和连字符分词
        words = re.split(r'[\s\-_]+', keyword_lower)

        # 过滤条件：
        # 1. 不在停用词列表中
        # 2. 长度 >= 2 (排除单字母)
        # 3. 仅包含字母 (排除纯数字或特殊符号)
        filtered_words = [
            w for w in words
            if w not in stopwords
            and len(w) >= 2
            and re.match(r'^[a-z]+$', w)
        ]

        # 统计词频
        word_counter.update(filtered_words)

        # 记录每个词对应的seed_word
        for word in filtered_words:
            word_to_seeds[word].add(seed_word)

        # 提取n-gram短语（如果启用）
        # 从数据中发现所有可能的短语模式（2词、3词...最多6词）
        if extract_ngrams and len(filtered_words) >= 2:
            for n in range(2, min(MAX_NGRAM_LENGTH + 1, len(filtered_words) + 1)):
                for i in range(len(filtered_words) - n + 1):
                    ngram = ' '.join(filtered_words[i:i+n])
                    ngram_counter[ngram] += 1
                    # 记录该n-gram对应的seed_word
                    ngram_to_seeds[ngram].add(seed_word)

    # 过滤低频n-grams
    if extract_ngrams:
        # 同时过滤counter和seeds字典，保持一致
        filtered_ngrams = {
            ngram: count
            for ngram, count in ngram_counter.items()
            if count >= min_ngram_frequency
        }
        ngram_counter = Counter(filtered_ngrams)

        # 只保留被保留的ngram的seeds信息
        ngram_to_seeds = {
            ngram: seeds
            for ngram, seeds in ngram_to_seeds.items()
            if ngram in ngram_counter
        }

    return word_counter, dict(word_to_seeds), ngram_counter, dict(ngram_to_seeds)


def get_sorted_words(word_counter: Counter,
                     sort_by: str = 'frequency',
                     min_frequency: int = 1) -> List[Tuple[str, int]]:
    """
    对词频统计结果进行排序

    Args:
        word_counter: Counter对象
        sort_by: 排序方式
            - 'frequency': 按频次降序（默认）
            - 'alphabetical': 按字母升序
            - 'length': 按词长度降序
        min_frequency: 最小频次阈值（小于此值的词不返回）

    Returns:
        排序后的 (word, count) 元组列表
    """
    # 过滤低频词
    filtered_items = [(w, c) for w, c in word_counter.items() if c >= min_frequency]

    # 排序
    if sort_by == 'frequency':
        return sorted(filtered_items, key=lambda x: x[1], reverse=True)
    elif sort_by == 'alphabetical':
        return sorted(filtered_items, key=lambda x: x[0])
    elif sort_by == 'length':
        return sorted(filtered_items, key=lambda x: len(x[0]), reverse=True)
    else:
        return filtered_items


def clean_keywords(keywords: List[str]) -> List[str]:
    """
    清理关键词列表

    处理步骤：
    1. 去除首尾空格
    2. 去除空行
    3. 去重（保持原有大小写混合）
    4. 去除纯数字或纯符号的行

    Args:
        keywords: 原始关键词列表

    Returns:
        清理后的关键词列表
    """
    cleaned = []
    seen = set()

    for keyword in keywords:
        # 去除首尾空格
        keyword = keyword.strip()

        # 跳过空行
        if not keyword:
            continue

        # 跳过纯数字或纯符号
        if not re.search(r'[a-zA-Z]', keyword):
            continue

        # 去重（不区分大小写）
        keyword_lower = keyword.lower()
        if keyword_lower not in seen:
            seen.add(keyword_lower)
            cleaned.append(keyword)

    return cleaned


def extract_word_combinations(words: List[str],
                               max_length: int = 3) -> Counter:
    """
    从词列表中提取高频词组合（n-grams）

    Args:
        words: 词列表
        max_length: 最大词组合长度（默认3，即三词组合）

    Returns:
        词组合频次统计

    Example:
        >>> words = ["best", "running", "shoes"]
        >>> extract_word_combinations(words, max_length=2)
        Counter({'best running': 1, 'running shoes': 1})
    """
    combinations = Counter()

    # 生成2-gram, 3-gram等组合
    for n in range(2, max_length + 1):
        for i in range(len(words) - n + 1):
            combo = ' '.join(words[i:i+n])
            combinations[combo] += 1

    return combinations


def get_statistics(word_counter: Counter) -> dict:
    """
    获取词频统计信息

    Args:
        word_counter: Counter对象

    Returns:
        统计信息字典
    """
    if not word_counter:
        return {
            'total_unique_words': 0,
            'total_occurrences': 0,
            'avg_frequency': 0,
            'top_10_words': []
        }

    total_unique = len(word_counter)
    total_occurrences = sum(word_counter.values())
    avg_frequency = total_occurrences / total_unique if total_unique > 0 else 0
    top_10 = word_counter.most_common(10)

    return {
        'total_unique_words': total_unique,
        'total_occurrences': total_occurrences,
        'avg_frequency': round(avg_frequency, 2),
        'top_10_words': top_10
    }


# 测试代码
if __name__ == "__main__":
    # 示例数据
    test_keywords = [
        "best running shoes",
        "running shoes for women",
        "cheap running shoes",
        "buy running shoes online",
        "top 10 running shoes 2024"
    ]

    test_stopwords = {"for", "the", "of", "in", "on", "at", "to", "and", "or"}

    # 清理
    cleaned = clean_keywords(test_keywords)
    print(f"清理后: {len(cleaned)} 个关键词\n")

    # 分词
    counter = segment_keywords(cleaned, test_stopwords)
    print("词频统计:")
    for word, count in counter.most_common(10):
        print(f"  {word}: {count}")

    # 统计信息
    stats = get_statistics(counter)
    print(f"\n统计信息:")
    print(f"  唯一词数: {stats['total_unique_words']}")
    print(f"  总出现次数: {stats['total_occurrences']}")
    print(f"  平均频次: {stats['avg_frequency']}")
