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
    从word_segments表提取Tokens（统一的1-6-gram）

    Args:
        min_frequency: 最小频次（过滤低频词）

    Returns:
        [(token, frequency), ...] 按频次降序排列
    """
    print(f"\n从word_segments提取Tokens（最小频次: {min_frequency}）...")

    with WordSegmentRepository() as ws_repo:
        # 使用新的统一加载方法（load_all_tokens）
        token_counter, _, _, _ = ws_repo.load_all_tokens(
            min_frequency=min_frequency
        )

    print(f"  发现 {len(token_counter):,} 个Tokens（1-6词统一分词）")

    # 返回排序列表
    return token_counter.most_common()
