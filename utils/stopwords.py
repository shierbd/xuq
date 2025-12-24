"""
停用词管理模块
提供停用词的加载、保存、增删改等操作
"""
from pathlib import Path
from typing import Set

# 默认英文停用词列表（约60个常见语法词）
DEFAULT_STOPWORDS = {
    # 冠词
    "a", "an", "the",

    # 介词
    "at", "by", "for", "from", "in", "into", "of", "on", "to", "with",
    "about", "above", "across", "after", "against", "along", "among",
    "around", "before", "behind", "below", "beneath", "beside", "between",
    "beyond", "during", "inside", "near", "outside", "over", "through",
    "under", "until", "up", "upon", "within", "without",

    # 连词
    "and", "but", "or", "nor", "so", "yet",

    # 代词
    "i", "me", "my", "we", "our", "you", "your", "he", "him", "his",
    "she", "her", "it", "its", "they", "them", "their",

    # be动词
    "am", "is", "are", "was", "were", "be", "been", "being",

    # 助动词
    "do", "does", "did", "have", "has", "had",

    # 其他常见停用词
    "this", "that", "these", "those", "what", "which", "who", "when",
    "where", "why", "how", "will", "can", "could", "would", "should",
    "may", "might", "must", "shall"
}


def load_stopwords(file_path: Path = None) -> Set[str]:
    """
    从文件加载停用词，如果文件不存在则返回默认停用词

    Args:
        file_path: 停用词文件路径（默认为None，使用默认停用词）

    Returns:
        停用词集合

    Example:
        >>> from pathlib import Path
        >>> stopwords = load_stopwords(Path('config/stopwords_en.txt'))
        >>> 'the' in stopwords
        True
    """
    if file_path is None or not file_path.exists():
        # 返回默认停用词的副本
        return DEFAULT_STOPWORDS.copy()

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # 读取所有行，去除空白并转小写
            stopwords = {line.strip().lower() for line in f if line.strip()}

        # 如果文件为空，返回默认停用词
        if not stopwords:
            return DEFAULT_STOPWORDS.copy()

        return stopwords

    except Exception as e:
        print(f"⚠️  加载停用词文件失败: {str(e)}，使用默认停用词")
        return DEFAULT_STOPWORDS.copy()


def save_stopwords(stopwords: Set[str], file_path: Path) -> bool:
    """
    保存停用词到文件

    Args:
        stopwords: 停用词集合
        file_path: 保存路径

    Returns:
        是否保存成功

    Example:
        >>> from pathlib import Path
        >>> stopwords = {'the', 'a', 'an'}
        >>> save_stopwords(stopwords, Path('config/custom_stopwords.txt'))
        True
    """
    try:
        # 确保目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # 排序后保存（方便人工查看和编辑）
        sorted_stopwords = sorted(stopwords)

        with open(file_path, 'w', encoding='utf-8') as f:
            for word in sorted_stopwords:
                f.write(f"{word}\n")

        return True

    except Exception as e:
        print(f"❌ 保存停用词文件失败: {str(e)}")
        return False


def add_stopword(stopwords: Set[str], word: str) -> Set[str]:
    """
    添加停用词

    Args:
        stopwords: 当前停用词集合
        word: 要添加的词（会自动转为小写）

    Returns:
        更新后的停用词集合

    Example:
        >>> stopwords = {'the', 'a'}
        >>> stopwords = add_stopword(stopwords, 'new')
        >>> 'new' in stopwords
        True
    """
    word_lower = word.strip().lower()

    if not word_lower:
        print("⚠️  停用词不能为空")
        return stopwords

    if word_lower in stopwords:
        print(f"⚠️  停用词 '{word_lower}' 已存在")
        return stopwords

    stopwords.add(word_lower)
    print(f"✓ 已添加停用词: {word_lower}")
    return stopwords


def add_stopwords_batch(stopwords: Set[str], words: list) -> Set[str]:
    """
    批量添加停用词

    Args:
        stopwords: 当前停用词集合
        words: 要添加的词列表

    Returns:
        更新后的停用词集合

    Example:
        >>> stopwords = {'the'}
        >>> stopwords = add_stopwords_batch(stopwords, ['new', 'word', 'test'])
        >>> len(stopwords)
        4
    """
    added_count = 0

    for word in words:
        word_lower = word.strip().lower()
        if word_lower and word_lower not in stopwords:
            stopwords.add(word_lower)
            added_count += 1

    print(f"✓ 批量添加成功: {added_count}/{len(words)} 个停用词")
    return stopwords


def remove_stopword(stopwords: Set[str], word: str) -> Set[str]:
    """
    删除停用词

    Args:
        stopwords: 当前停用词集合
        word: 要删除的词

    Returns:
        更新后的停用词集合

    Example:
        >>> stopwords = {'the', 'a', 'an'}
        >>> stopwords = remove_stopword(stopwords, 'a')
        >>> 'a' in stopwords
        False
    """
    word_lower = word.strip().lower()

    if word_lower in stopwords:
        stopwords.remove(word_lower)
        print(f"✓ 已删除停用词: {word_lower}")
    else:
        print(f"⚠️  停用词 '{word_lower}' 不存在")

    return stopwords


def remove_stopwords_batch(stopwords: Set[str], words: list) -> Set[str]:
    """
    批量删除停用词

    Args:
        stopwords: 当前停用词集合
        words: 要删除的词列表

    Returns:
        更新后的停用词集合

    Example:
        >>> stopwords = {'the', 'a', 'an', 'test'}
        >>> stopwords = remove_stopwords_batch(stopwords, ['a', 'an'])
        >>> len(stopwords)
        2
    """
    removed_count = 0

    for word in words:
        word_lower = word.strip().lower()
        if word_lower in stopwords:
            stopwords.remove(word_lower)
            removed_count += 1

    print(f"✓ 批量删除成功: {removed_count}/{len(words)} 个停用词")
    return stopwords


def reset_to_default(file_path: Path = None) -> Set[str]:
    """
    重置为默认停用词

    Args:
        file_path: 如果提供，会将默认停用词保存到此文件

    Returns:
        默认停用词集合

    Example:
        >>> from pathlib import Path
        >>> stopwords = reset_to_default(Path('config/stopwords_en.txt'))
        >>> len(stopwords) > 50
        True
    """
    default_copy = DEFAULT_STOPWORDS.copy()

    if file_path:
        if save_stopwords(default_copy, file_path):
            print(f"✓ 已重置为默认停用词并保存到: {file_path}")
        else:
            print("⚠️  重置成功但保存失败")
    else:
        print("✓ 已重置为默认停用词")

    return default_copy


def get_stopwords_info(stopwords: Set[str]) -> dict:
    """
    获取停用词统计信息

    Args:
        stopwords: 停用词集合

    Returns:
        统计信息字典

    Example:
        >>> stopwords = {'the', 'a', 'an'}
        >>> info = get_stopwords_info(stopwords)
        >>> info['total']
        3
    """
    return {
        'total': len(stopwords),
        'sample': sorted(list(stopwords))[:10],  # 前10个示例
        'is_default': stopwords == DEFAULT_STOPWORDS
    }


# 测试代码
if __name__ == "__main__":
    from pathlib import Path

    print("=== 停用词管理模块测试 ===\n")

    # 1. 加载默认停用词
    print("【测试1】加载默认停用词")
    stopwords = load_stopwords()
    print(f"  默认停用词数量: {len(stopwords)}")
    print(f"  示例: {sorted(list(stopwords))[:10]}\n")

    # 2. 添加停用词
    print("【测试2】添加停用词")
    stopwords = add_stopword(stopwords, "test")
    stopwords = add_stopword(stopwords, "example")
    print(f"  当前停用词数量: {len(stopwords)}\n")

    # 3. 批量添加
    print("【测试3】批量添加停用词")
    stopwords = add_stopwords_batch(stopwords, ["word1", "word2", "word3"])
    print(f"  当前停用词数量: {len(stopwords)}\n")

    # 4. 删除停用词
    print("【测试4】删除停用词")
    stopwords = remove_stopword(stopwords, "test")
    print(f"  当前停用词数量: {len(stopwords)}\n")

    # 5. 保存到文件
    print("【测试5】保存到文件")
    test_file = Path("config/test_stopwords.txt")
    if save_stopwords(stopwords, test_file):
        print(f"  ✓ 已保存到: {test_file}\n")

    # 6. 从文件加载
    print("【测试6】从文件加载")
    loaded = load_stopwords(test_file)
    print(f"  加载的停用词数量: {len(loaded)}")
    print(f"  是否与保存前一致: {loaded == stopwords}\n")

    # 7. 重置为默认
    print("【测试7】重置为默认")
    stopwords = reset_to_default()
    print(f"  重置后停用词数量: {len(stopwords)}\n")

    # 8. 获取统计信息
    print("【测试8】获取统计信息")
    info = get_stopwords_info(stopwords)
    print(f"  总数: {info['total']}")
    print(f"  是否为默认: {info['is_default']}")
    print(f"  示例: {info['sample']}")
