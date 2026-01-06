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
                                        extract_ngrams: bool = True,
                                        min_ngram_frequency: int = 2) -> Tuple[Counter, Dict[str, Set[str]], Counter, Dict[str, Set[str]]]:
    """
    将关键词短语分词并统计词频，同时追踪每个词和短语来源于哪些seed_word

    ⚠️ 此函数已重构为调用segment_keywords_unified()的wrapper函数，以保持向后兼容。
    推荐新代码直接使用 segment_keywords_unified() 函数。

    Args:
        phrases_objects: Phrase对象列表（需要有phrase和seed_word属性）
        stopwords: 停用词集合
        extract_ngrams: 已废弃参数，现在总是提取n-grams（保留此参数仅为向后兼容）
        min_ngram_frequency: 最小频次阈值（应用于所有1-6-gram）

    Returns:
        (word_counter, word_to_seeds, ngram_counter, ngram_to_seeds)
        - word_counter: Counter对象，包含1-gram（单词）词频统计
        - word_to_seeds: {word: {seed1, seed2, ...}} 每个单词对应的所有原始词根集合
        - ngram_counter: Counter对象，包含2-6-gram（短语）频次统计
        - ngram_to_seeds: {ngram: {seed1, seed2, ...}} 每个短语对应的所有原始词根集合

    Example:
        >>> phrases = [Phrase(phrase="best running shoes", seed_word="running")]
        >>> stopwords = {"for"}
        >>> counter, word_seeds, ngrams, ngram_seeds = segment_keywords_with_seed_tracking(phrases, stopwords)
        >>> word_seeds['running']
        {'running'}
        >>> ngram_seeds['best running']
        {'running'}

    Note:
        现在内部使用segment_keywords_unified()进行穷尽式n-gram提取，
        然后拆分为word_counter（1-gram）和ngram_counter（2-6-gram）以保持向后兼容。
        extract_ngrams参数已被忽略，总是提取所有n-grams。
    """
    # 调用新的统一分词函数
    token_counter, token_to_seeds = segment_keywords_unified(
        phrases_objects,
        stopwords,
        min_frequency=min_ngram_frequency,
        max_ngram_length=6
    )

    # 为了向后兼容，拆分为word_counter（1-gram）和ngram_counter（2-6-gram）
    word_counter = Counter()
    word_to_seeds = {}
    ngram_counter = Counter()
    ngram_to_seeds = {}

    for token, count in token_counter.items():
        word_count = len(token.split())

        if word_count == 1:
            # 1-gram（单词）
            word_counter[token] = count
            word_to_seeds[token] = token_to_seeds[token]
        else:
            # 2-6-gram（短语）
            ngram_counter[token] = count
            ngram_to_seeds[token] = token_to_seeds[token]

    return word_counter, word_to_seeds, ngram_counter, ngram_to_seeds


def segment_keywords_unified(
    phrases_objects: list,
    stopwords: Set[str],
    min_frequency: int = 2,
    max_ngram_length: int = 6
) -> Tuple[Counter, Dict[str, Set[str]]]:
    """
    统一提取1-6词的所有n-gram（穷尽式分词）

    这是推荐使用的新函数，实现了完整的穷尽式n-gram提取。
    不区分"单词"和"短语"，统一提取所有1-6词组合。

    Args:
        phrases_objects: Phrase对象列表（需要有phrase和seed_word属性）
        stopwords: 停用词集合
        min_frequency: 最小频次阈值（适用于所有n-gram，无论1词还是多词）
        max_ngram_length: 最大n-gram长度（默认6）

    Returns:
        (token_counter, token_to_seeds)
        - token_counter: Counter对象，包含所有tokens的统一频次统计（1-6词）
        - token_to_seeds: {token: {seed1, seed2, ...}} 每个token对应的所有原始词根集合

    Example:
        >>> phrases = [Phrase(phrase="best running shoes", seed_word="running")]
        >>> stopwords = {"for", "the"}
        >>> tokens, seeds = segment_keywords_unified(phrases, stopwords, min_frequency=2)
        >>> tokens.most_common(5)
        [('running', 3), ('shoes', 3), ('running shoes', 3), ...]

    Note:
        这个函数实现了完整的穷尽式n-gram提取：
        - 提取所有1-gram（单词）
        - 提取所有2-gram（2词短语）
        - 提取所有3-gram（3词短语）
        - ...直到max_ngram_length

        然后用min_frequency统一过滤所有结果。
    """
    token_counter = Counter()
    token_to_seeds = defaultdict(set)

    for phrase_obj in phrases_objects:
        keyword = phrase_obj.phrase
        seed_word = phrase_obj.seed_word or "unknown"

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

        if not filtered_words:
            continue

        # 穷尽提取1-gram到max_ngram_length-gram
        for n in range(1, min(max_ngram_length + 1, len(filtered_words) + 1)):
            for i in range(len(filtered_words) - n + 1):
                if n == 1:
                    # 1-gram（单词）
                    token = filtered_words[i]
                else:
                    # n-gram（短语）
                    token = ' '.join(filtered_words[i:i+n])

                token_counter[token] += 1
                token_to_seeds[token].add(seed_word)

    # 应用频次阈值过滤
    filtered_tokens = {
        token: count
        for token, count in token_counter.items()
        if count >= min_frequency
    }

    # 只保留被保留的token的seeds信息
    filtered_token_to_seeds = {
        token: seeds
        for token, seeds in token_to_seeds.items()
        if token in filtered_tokens
    }

    return Counter(filtered_tokens), dict(filtered_token_to_seeds)


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


# ==================== 增量分词支持 ====================

def segment_new_phrases_incrementally(
    new_phrases: list,
    existing_word_counter: Counter,
    existing_ngram_counter: Counter,
    existing_word_to_seeds: Dict[str, Set[str]],
    existing_ngram_to_seeds: Dict[str, Set[str]],
    stopwords: Set[str],
    extract_ngrams: bool = False,
    min_ngram_frequency: int = 2
) -> Tuple[Counter, Dict[str, Set[str]], Counter, Dict[str, Set[str]]]:
    """
    增量分词：只对新phrases进行分词，然后与已有结果合并

    Args:
        new_phrases: 新的Phrase对象列表
        existing_word_counter: 已有的单词频次Counter
        existing_ngram_counter: 已有的短语频次Counter
        existing_word_to_seeds: 已有的单词到seeds映射
        existing_ngram_to_seeds: 已有的短语到seeds映射
        stopwords: 停用词集合
        extract_ngrams: 是否提取n-gram短语
        min_ngram_frequency: n-gram最小频次阈值

    Returns:
        (merged_word_counter, merged_word_to_seeds, merged_ngram_counter, merged_ngram_to_seeds)
        - 合并后的单词频次
        - 合并后的单词到seeds映射
        - 合并后的短语频次
        - 合并后的短语到seeds映射
    """
    # 1. 对新phrases进行分词
    new_word_counter, new_word_to_seeds, new_ngram_counter, new_ngram_to_seeds = \
        segment_keywords_with_seed_tracking(
            new_phrases,
            stopwords,
            extract_ngrams=extract_ngrams,
            min_ngram_frequency=min_ngram_frequency
        )

    # 2. 合并单词频次
    merged_word_counter = Counter(existing_word_counter)
    merged_word_counter.update(new_word_counter)

    # 3. 合并单词到seeds映射
    merged_word_to_seeds = defaultdict(set)
    for word, seeds in existing_word_to_seeds.items():
        merged_word_to_seeds[word].update(seeds)
    for word, seeds in new_word_to_seeds.items():
        merged_word_to_seeds[word].update(seeds)

    # 4. 合并短语频次
    merged_ngram_counter = Counter(existing_ngram_counter)
    merged_ngram_counter.update(new_ngram_counter)

    # 5. 合并短语到seeds映射
    merged_ngram_to_seeds = defaultdict(set)
    for ngram, seeds in existing_ngram_to_seeds.items():
        merged_ngram_to_seeds[ngram].update(seeds)
    for ngram, seeds in new_ngram_to_seeds.items():
        merged_ngram_to_seeds[ngram].update(seeds)

    return (
        merged_word_counter,
        dict(merged_word_to_seeds),
        merged_ngram_counter,
        dict(merged_ngram_to_seeds)
    )


def load_and_segment_incrementally(
    round_ids: List[int],
    stopwords: Set[str],
    extract_ngrams: bool = False,
    min_ngram_frequency: int = 2
) -> Tuple[Counter, Dict[str, Set[str]], Counter, Dict[str, Set[str]], int]:
    """
    增量分词：从数据库加载指定轮次的phrases并分词，与已有结果合并

    Args:
        round_ids: 要处理的轮次ID列表（例如：[2] 只处理第2轮新数据）
        stopwords: 停用词集合
        extract_ngrams: 是否提取n-gram短语
        min_ngram_frequency: n-gram最小频次阈值

    Returns:
        (word_counter, word_to_seeds, ngram_counter, ngram_to_seeds, phrases_count)
        - 合并后的单词频次
        - 合并后的单词到seeds映射
        - 合并后的短语频次
        - 合并后的短语到seeds映射
        - 处理的phrases数量
    """
    from storage.word_segment_repository import WordSegmentRepository

    with WordSegmentRepository() as repo:
        # 1. 加载已有的分词结果
        (
            existing_word_counter,
            existing_ngram_counter,
            _,  # pos_tags
            _,  # translations
            _,  # ngram_translations
            _   # latest_batch
        ) = repo.load_segmentation_results()

        # 转换为dict格式（因为load返回的可能没有seed信息）
        existing_word_to_seeds = {}
        existing_ngram_to_seeds = {}

        # 2. 加载指定轮次的新phrases
        new_phrases = repo.get_phrases_by_rounds(round_ids)

        if not new_phrases:
            # 没有新数据，返回已有结果
            return (
                existing_word_counter,
                existing_word_to_seeds,
                existing_ngram_counter,
                existing_ngram_to_seeds,
                0
            )

        # 3. 增量分词
        (
            merged_word_counter,
            merged_word_to_seeds,
            merged_ngram_counter,
            merged_ngram_to_seeds
        ) = segment_new_phrases_incrementally(
            new_phrases,
            existing_word_counter,
            existing_ngram_counter,
            existing_word_to_seeds,
            existing_ngram_to_seeds,
            stopwords,
            extract_ngrams=extract_ngrams,
            min_ngram_frequency=min_ngram_frequency
        )

        return (
            merged_word_counter,
            merged_word_to_seeds,
            merged_ngram_counter,
            merged_ngram_to_seeds,
            len(new_phrases)
        )

