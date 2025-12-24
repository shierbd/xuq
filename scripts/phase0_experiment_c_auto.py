"""
Phase 0 - Experiment C (自动化版本): 同义冗余率测量
Redundancy Rate Measurement (Automated)

自动化策略：
- 使用文本相似度算法（基于词袋和编辑距离）
- 自动识别同义组
- 估算冗余率

创建日期：2025-12-23
"""

import json
import io
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set
import sys
import random
from difflib import SequenceMatcher

# Set UTF-8 encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.repository import PhraseRepository
from storage.models import Phrase
from sqlalchemy import text


def normalize_phrase(phrase: str) -> str:
    """
    规范化短语（用于相似度比较）
    - 转小写
    - 排序词序（忽略词序差异）
    """
    words = phrase.lower().split()
    return ' '.join(sorted(words))


def calculate_similarity(phrase1: str, phrase2: str) -> float:
    """
    计算两个短语的相似度（0-1）

    策略：
    1. 规范化后完全相同 -> 1.0
    2. SequenceMatcher 相似度 > 0.8 -> 视为同义
    3. 词袋交集比例 > 0.8 -> 视为同义
    """
    # 规范化
    norm1 = normalize_phrase(phrase1)
    norm2 = normalize_phrase(phrase2)

    # 完全相同
    if norm1 == norm2:
        return 1.0

    # 序列相似度
    seq_similarity = SequenceMatcher(None, norm1, norm2).ratio()

    # 词袋相似度
    words1 = set(phrase1.lower().split())
    words2 = set(phrase2.lower().split())

    if len(words1) == 0 or len(words2) == 0:
        return 0.0

    intersection = words1 & words2
    union = words1 | words2

    word_similarity = len(intersection) / len(union) if union else 0.0

    # 综合相似度
    return max(seq_similarity, word_similarity)


def auto_find_synonyms(sample_phrases: List[str],
                       similarity_threshold: float = 0.85) -> List[List[int]]:
    """
    自动识别同义组

    Args:
        sample_phrases: 短语列表
        similarity_threshold: 相似度阈值

    Returns:
        同义组列表，每个组是短语索引的列表
    """
    print(f"\n📊 自动识别同义组（阈值={similarity_threshold}）...")

    synonym_groups = []
    phrase_to_group = {}  # {phrase_idx: group_idx}

    for i, phrase1 in enumerate(sample_phrases):
        if i in phrase_to_group:
            continue  # 已在某个组中

        # 创建新组
        current_group = [i]
        phrase_to_group[i] = len(synonym_groups)

        # 查找同义短语
        for j in range(i + 1, len(sample_phrases)):
            if j in phrase_to_group:
                continue

            phrase2 = sample_phrases[j]
            similarity = calculate_similarity(phrase1, phrase2)

            if similarity >= similarity_threshold:
                current_group.append(j)
                phrase_to_group[j] = len(synonym_groups)

        # 只保存有多个成员的组（真正的同义组）
        if len(current_group) > 1:
            synonym_groups.append(current_group)

    return synonym_groups


def run_experiment_c_auto() -> Dict:
    """
    自动化运行实验C
    """
    print("\n" + "="*70)
    print("Phase 0 - Experiment C (自动化): 同义冗余率测量")
    print("="*70)

    # 1. 加载所有短语
    print("\n1. 加载短语数据...")

    with PhraseRepository() as phrase_repo:
        all_phrases_objs = phrase_repo.session.query(Phrase).all()

    all_phrases = [p.phrase for p in all_phrases_objs]
    print(f"✓ 短语总数: {len(all_phrases):,}")

    # 2. 随机抽样（固定种子以确保可复现）
    sample_size = min(1000, len(all_phrases))
    random.seed(42)
    sample_indices = random.sample(range(len(all_phrases)), sample_size)
    sample_phrases = [all_phrases[i] for i in sample_indices]

    print(f"✓ 抽样数量: {sample_size:,}")

    # 3. 自动识别同义组
    print(f"\n2. 自动识别同义组...")

    synonym_groups = auto_find_synonyms(sample_phrases)

    synonym_groups_count = len(synonym_groups)
    phrases_in_groups = sum(len(g) for g in synonym_groups)
    redundancy_rate = (phrases_in_groups - synonym_groups_count) / sample_size if sample_size > 0 else 0.0

    print(f"\n✓ 识别完成")
    print(f"  同义组数: {synonym_groups_count}")
    print(f"  同义短语数: {phrases_in_groups}")
    print(f"  冗余率: {redundancy_rate:.1%}")

    # 显示前几个同义组示例
    if synonym_groups:
        print(f"\n📋 同义组示例（前3个）:")
        for i, group in enumerate(synonym_groups[:3], 1):
            print(f"\n  组{i} ({len(group)}个短语):")
            for idx in group[:5]:  # 最多显示5个
                print(f"    - {sample_phrases[idx]}")

    # 4. 生成结果
    result = {
        'experiment': 'C',
        'name': '同义冗余率',
        'timestamp': datetime.now().isoformat(),
        'sample_size': sample_size,
        'synonym_groups_count': synonym_groups_count,
        'phrases_in_groups': phrases_in_groups,
        'redundancy_rate': redundancy_rate,
        'automation_note': '此结果由自动化脚本生成，基于文本相似度算法识别同义组'
    }

    # 5. 决策逻辑
    if redundancy_rate < 0.10:
        result['recommendation'] = 'ok'
        result['recommendation_detail'] = f'冗余率{redundancy_rate:.1%}可接受，无需特殊处理'
    elif redundancy_rate > 0.20:
        result['recommendation'] = 'need_canonicalization'
        result['recommendation_detail'] = f'冗余率{redundancy_rate:.1%}较高，建议实施词级规范化去重'
    else:
        result['recommendation'] = 'moderate'
        result['recommendation_detail'] = f'冗余率{redundancy_rate:.1%}中等，可考虑轻量级去重'

    print(f"\n" + "="*70)
    print("实验C结果")
    print("="*70)
    print(f"抽样数量: {sample_size:,}")
    print(f"同义组数: {synonym_groups_count}")
    print(f"冗余率: {redundancy_rate:.1%}")
    print(f"\n判断: {result['recommendation']}")
    print(f"详情: {result['recommendation_detail']}")

    # 6. 保存结果
    output_dir = project_root / 'data' / 'phase0_results'
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / 'experiment_c_result.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n✓ 结果已保存到: {output_file}")

    return result


if __name__ == "__main__":
    try:
        result = run_experiment_c_auto()

        print("\n✅ 实验C (自动化版本) 完成！")
        print(f"\n📊 建议: {result['recommendation']}")

    except KeyboardInterrupt:
        print("\n\n⚠️  操作被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 实验执行出错: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
