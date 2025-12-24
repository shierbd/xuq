"""
词性标注模块
使用NLTK进行英文词性标注（Part-of-Speech Tagging）
"""
from typing import List, Tuple, Dict
from collections import Counter

# 尝试导入NLTK，如果失败则标记为不可用
try:
    import nltk
    from nltk import pos_tag
    from nltk.tokenize import word_tokenize

    # 尝试使用averaged_perceptron_tagger，如果不存在则下载
    try:
        nltk.data.find('taggers/averaged_perceptron_tagger')
    except LookupError:
        print("正在下载NLTK词性标注器...")
        nltk.download('averaged_perceptron_tagger', quiet=True)
        nltk.download('averaged_perceptron_tagger_eng', quiet=True)

    POS_TAGGING_AVAILABLE = True
except ImportError:
    POS_TAGGING_AVAILABLE = False
    pos_tag = None


# Penn Treebank POS标签到中文的映射
POS_TAG_NAMES = {
    # 名词类
    'NN': '名词（单数）',
    'NNS': '名词（复数）',
    'NNP': '专有名词（单数）',
    'NNPS': '专有名词（复数）',

    # 动词类
    'VB': '动词（原形）',
    'VBD': '动词（过去式）',
    'VBG': '动词（现在分词/动名词）',
    'VBN': '动词（过去分词）',
    'VBP': '动词（非第三人称单数）',
    'VBZ': '动词（第三人称单数）',

    # 形容词类
    'JJ': '形容词',
    'JJR': '形容词（比较级）',
    'JJS': '形容词（最高级）',

    # 副词类
    'RB': '副词',
    'RBR': '副词（比较级）',
    'RBS': '副词（最高级）',

    # 代词类
    'PRP': '人称代词',
    'PRP$': '所有格代词',
    'WP': '疑问代词',
    'WP$': '所有格疑问代词',

    # 限定词
    'DT': '限定词',
    'PDT': '前位限定词',
    'WDT': '疑问限定词',

    # 介词和连词
    'IN': '介词/从属连词',
    'CC': '并列连词',

    # 数词
    'CD': '基数词',

    # 其他
    'MD': '情态动词',
    'TO': 'to',
    'UH': '感叹词',
    'FW': '外来词',
    'SYM': '符号',
}

# 简化的词性分类
POS_CATEGORIES = {
    'Noun': ['NN', 'NNS', 'NNP', 'NNPS'],
    'Verb': ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ'],
    'Adjective': ['JJ', 'JJR', 'JJS'],
    'Adverb': ['RB', 'RBR', 'RBS'],
    'Pronoun': ['PRP', 'PRP$', 'WP', 'WP$'],
    'Determiner': ['DT', 'PDT', 'WDT'],
    'Preposition': ['IN'],
    'Conjunction': ['CC'],
    'Number': ['CD'],
    'Modal': ['MD'],
    'Other': ['TO', 'UH', 'FW', 'SYM']
}

# 中文名称映射
POS_CATEGORY_NAMES = {
    'Noun': '名词',
    'Verb': '动词',
    'Adjective': '形容词',
    'Adverb': '副词',
    'Pronoun': '代词',
    'Determiner': '限定词',
    'Preposition': '介词',
    'Conjunction': '连词',
    'Number': '数词',
    'Modal': '情态动词',
    'Other': '其他'
}


def get_pos_tag(word: str) -> Tuple[str, str, str]:
    """
    获取单个词的词性标注

    Args:
        word: 英文单词

    Returns:
        (详细标签, 简化分类, 中文名称)
        例如: ('VBG', 'Verb', '动词')

    Example:
        >>> get_pos_tag('running')
        ('VBG', 'Verb', '动词')
        >>> get_pos_tag('calculator')
        ('NN', 'Noun', '名词')
    """
    if not POS_TAGGING_AVAILABLE:
        return ('UNKNOWN', 'Other', '未知')

    try:
        # NLTK词性标注
        tagged = pos_tag([word])
        pos = tagged[0][1]

        # 找到简化分类
        category = 'Other'
        for cat, tags in POS_CATEGORIES.items():
            if pos in tags:
                category = cat
                break

        # 获取中文名称
        chinese_name = POS_CATEGORY_NAMES.get(category, '其他')

        return (pos, category, chinese_name)

    except Exception as e:
        print(f"⚠️  词性标注失败: {word} - {str(e)}")
        return ('UNKNOWN', 'Other', '未知')


def tag_words_batch(words: List[str]) -> Dict[str, Tuple[str, str, str]]:
    """
    批量标注词性

    Args:
        words: 单词列表

    Returns:
        {单词: (详细标签, 简化分类, 中文名称)}

    Example:
        >>> words = ['calculator', 'running', 'fast']
        >>> tag_words_batch(words)
        {
            'calculator': ('NN', 'Noun', '名词'),
            'running': ('VBG', 'Verb', '动词'),
            'fast': ('JJ', 'Adjective', '形容词')
        }
    """
    if not POS_TAGGING_AVAILABLE:
        return {word: ('UNKNOWN', 'Other', '未知') for word in words}

    result = {}

    try:
        # NLTK批量标注
        tagged = pos_tag(words)

        for word, pos in tagged:
            # 找到简化分类
            category = 'Other'
            for cat, tags in POS_CATEGORIES.items():
                if pos in tags:
                    category = cat
                    break

            # 获取中文名称
            chinese_name = POS_CATEGORY_NAMES.get(category, '其他')

            result[word] = (pos, category, chinese_name)

    except Exception as e:
        print(f"❌ 批量词性标注失败: {str(e)}")
        # 失败时返回未知
        for word in words:
            result[word] = ('UNKNOWN', 'Other', '未知')

    return result


def get_pos_statistics(word_counter: Counter,
                       pos_tags: Dict[str, Tuple[str, str, str]]) -> Dict:
    """
    获取词性统计信息

    Args:
        word_counter: 词频计数器
        pos_tags: 词性标注字典

    Returns:
        统计信息字典

    Example:
        >>> stats = get_pos_statistics(word_counter, pos_tags)
        >>> stats['by_category']
        {'Noun': 150, 'Verb': 80, 'Adjective': 45, ...}
    """
    if not pos_tags:
        return {}

    # 按简化分类统计
    category_counts = Counter()
    category_frequencies = Counter()

    for word, freq in word_counter.items():
        if word in pos_tags:
            _, category, _ = pos_tags[word]
            category_counts[category] += 1
            category_frequencies[category] += freq

    # 按详细标签统计
    detailed_counts = Counter()
    for word in word_counter:
        if word in pos_tags:
            pos, _, _ = pos_tags[word]
            detailed_counts[pos] += 1

    return {
        'by_category': dict(category_counts),
        'by_category_freq': dict(category_frequencies),
        'by_detailed_tag': dict(detailed_counts),
        'total_words': len(word_counter)
    }


def get_available_categories() -> List[Tuple[str, str]]:
    """
    获取所有可用的词性分类

    Returns:
        [(英文类别, 中文名称), ...]

    Example:
        >>> get_available_categories()
        [('Noun', '名词'), ('Verb', '动词'), ...]
    """
    return [(cat, POS_CATEGORY_NAMES[cat]) for cat in POS_CATEGORIES.keys()]


# 测试代码
if __name__ == "__main__":
    print("=== 词性标注测试 ===\n")

    if not POS_TAGGING_AVAILABLE:
        print("❌ NLTK不可用，无法进行词性标注")
        exit(1)

    # 1. 测试单词标注
    print("【测试1】单词标注")
    test_words = ["calculator", "running", "fast", "quickly", "data", "search"]

    for word in test_words:
        pos, category, chinese = get_pos_tag(word)
        print(f"  {word:15} → {pos:8} | {category:12} | {chinese}")

    # 2. 测试批量标注
    print("\n【测试2】批量标注")
    tags = tag_words_batch(test_words)
    print("  结果:")
    for word, (pos, cat, cn) in tags.items():
        print(f"    {word:15} → {pos:8} | {cat:12} | {cn}")

    # 3. 测试统计
    print("\n【测试3】词性统计")
    word_counter = Counter({
        "calculator": 10,
        "running": 8,
        "fast": 5,
        "data": 12,
        "search": 7
    })

    stats = get_pos_statistics(word_counter, tags)
    print("  按类别统计:")
    for cat, count in stats['by_category'].items():
        chinese_name = POS_CATEGORY_NAMES.get(cat, cat)
        print(f"    {chinese_name:10} → {count} 个词")

    # 4. 测试可用分类
    print("\n【测试4】可用分类")
    categories = get_available_categories()
    print("  支持的词性分类:")
    for eng, cn in categories:
        print(f"    {eng:15} → {cn}")
