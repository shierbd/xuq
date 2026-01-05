"""
Token提取 - 从word_segments表提取并分类
"""
from collections import Counter
from typing import List, Tuple
from storage.word_segment_repository import WordSegmentRepository


def extract_tokens_from_word_segments(
    min_frequency: int = 3
) -> List[Tuple[str, int]]:
    """
    从word_segments表提取Tokens（单词+短语）

    Args:
        min_frequency: 最小频次（过滤低频词）

    Returns:
        [(token, frequency), ...] 按频次降序排列
    """
    print(f"\n从word_segments提取Tokens（最小频次: {min_frequency}）...")

    with WordSegmentRepository() as ws_repo:
        # 加载单词和短语
        word_counter, ngram_counter, _, _, _, _ = ws_repo.load_segmentation_results(
            min_word_frequency=min_frequency,
            min_ngram_frequency=min_frequency
        )

    # 合并单词和短语
    all_tokens = Counter()
    all_tokens.update(word_counter)
    all_tokens.update(ngram_counter)

    print(f"  发现 {len(word_counter):,} 个单词")
    print(f"  发现 {len(ngram_counter):,} 个短语")
    print(f"  合计 {len(all_tokens):,} 个Tokens")

    # 返回排序列表
    return all_tokens.most_common()
