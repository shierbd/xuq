"""
Phase 0 - Experiment C: 同义冗余率测量
Redundancy Rate Measurement

目标：测量同一需求的不同表达占比

判断标准：
- 冗余率<10% → 暂不需要词级规范化去重
- 冗余率>20% → 需要实施Phase 2.1词级规范化去重

创建日期：2025-12-23
"""

import json
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.repository import PhraseRepository


def group_synonyms_interactive(sample_phrases: List[str]) -> List[List[int]]:
    """
    交互式同义词分组

    Args:
        sample_phrases: 抽样短语列表

    Returns:
        同义组列表，每组包含短语的索引
        示例: [[0, 5, 12], [3, 8], ...]
    """
    print("\n" + "="*70)
    print("同义词分组说明")
    print("="*70)
    print("""
您需要识别"相同需求的不同表达"。

示例：
  - "best calculator" 和 "calculator best" → 同义（词序不同）
  - "image compressor" 和 "compress image" → 同义（词形变化）
  - "best calculator" 和 "free calculator" → 不同义（意图不同：推荐 vs 免费）

判断标准：
  ✓ 同义：去掉停用词后，核心词相同且意图相同
  ✗ 不同义：意图不同、对象不同、或限定条件不同

操作说明：
  1. 每次显示一个短语
  2. 如果它与之前某个短语同义，输入那个短语的编号
  3. 如果它是新的独立需求，直接按Enter
  4. 输入 'q' 提前结束
    """)

    input("\n准备好了吗？按 Enter 键开始...")

    # 存储同义组：{group_id: [phrase_indices]}
    synonym_groups = {}
    phrase_to_group = {}  # {phrase_idx: group_id}
    next_group_id = 1

    for idx, phrase in enumerate(sample_phrases):
        print("\n" + "="*70)
        print(f"进度: {idx + 1}/{len(sample_phrases)}")
        print("="*70)
        print(f"\n当前短语 [{idx}]: {phrase}")

        # 显示已有的相似短语（供参考）
        if phrase_to_group:
            print("\n已标记的短语（前20个）：")
            displayed_count = 0
            for prev_idx in range(idx):
                if displayed_count >= 20:
                    print("  ...")
                    break
                if prev_idx in phrase_to_group:
                    group_id = phrase_to_group[prev_idx]
                    print(f"  [{prev_idx}] {sample_phrases[prev_idx]} (组{group_id})")
                    displayed_count += 1

        # 用户输入
        user_input = input("\n与哪个短语同义？输入编号，或按Enter跳过，或'q'退出: ").strip().lower()

        if user_input == 'q':
            print("\n提前结束标注")
            break

        if user_input == '':
            # 新的独立需求，不标记为同义组
            continue

        try:
            # 用户指定了同义短语
            synonym_idx = int(user_input)

            if synonym_idx < 0 or synonym_idx >= idx:
                print(f"⚠️  无效编号，跳过")
                continue

            # 找到或创建同义组
            if synonym_idx in phrase_to_group:
                # 加入已有组
                group_id = phrase_to_group[synonym_idx]
            else:
                # 创建新组，包含两个短语
                group_id = next_group_id
                next_group_id += 1
                synonym_groups[group_id] = [synonym_idx]
                phrase_to_group[synonym_idx] = group_id

            # 将当前短语加入组
            synonym_groups[group_id].append(idx)
            phrase_to_group[idx] = group_id

            print(f"✓ 已标记为同义（组{group_id}）")

        except ValueError:
            print(f"⚠️  无效输入，跳过")
            continue

    # 转换为列表格式
    result = list(synonym_groups.values())
    return result


def run_experiment_c() -> Dict:
    """
    执行实验C：同义冗余率测量

    Returns:
        实验结果字典
    """
    print("\n" + "="*70)
    print("Phase 0 - Experiment C: 同义冗余率测量")
    print("="*70)

    # 1. 加载所有短语
    print("\n1. 加载短语数据...")

    with PhraseRepository() as phrase_repo:
        all_phrases = phrase_repo.get_all()

    total_phrases = len(all_phrases)
    print(f"✓ 短语总数: {total_phrases:,}")

    # 2. 随机抽样1000条
    sample_size = min(1000, total_phrases)

    print(f"\n2. 随机抽样 {sample_size} 条短语...")

    random.seed(42)  # 固定种子，便于复现
    sample_phrases_obj = random.sample(all_phrases, sample_size)
    sample_phrases = [p.phrase for p in sample_phrases_obj]

    print(f"✓ 抽样完成")

    # 3. 交互式同义词标注
    print("\n3. 开始同义词标注...")

    synonym_groups = group_synonyms_interactive(sample_phrases)

    # 4. 统计结果
    print("\n" + "="*70)
    print("标注结果统计")
    print("="*70)

    total_groups = len(synonym_groups)
    phrases_in_groups = sum(len(group) for group in synonym_groups)
    redundancy_rate = phrases_in_groups / sample_size if sample_size > 0 else 0

    print(f"\n同义组数量: {total_groups}")
    print(f"同义组内短语数: {phrases_in_groups}")
    print(f"冗余率: {redundancy_rate:.1%} ({phrases_in_groups}/{sample_size})")

    # 显示同义组示例
    if synonym_groups:
        print(f"\n同义组示例（前5组）：")
        for i, group in enumerate(synonym_groups[:5], 1):
            print(f"\n  组{i}:")
            for idx in group:
                print(f"    [{idx}] {sample_phrases[idx]}")

    # 5. 生成结果
    result = {
        'experiment': 'C',
        'name': '同义冗余率',
        'timestamp': datetime.now().isoformat(),
        'sample_size': sample_size,
        'total_phrases': total_phrases,
        'synonym_groups_count': total_groups,
        'phrases_in_groups': phrases_in_groups,
        'redundancy_rate': round(redundancy_rate, 4),
        'synonym_groups': [
            {
                'group_id': i,
                'phrases': [sample_phrases[idx] for idx in group]
            }
            for i, group in enumerate(synonym_groups, 1)
        ]
    }

    # 6. 判断是否需要规范化
    if redundancy_rate < 0.10:
        result['recommendation'] = 'ok'
        result['recommendation_detail'] = f'冗余率{redundancy_rate:.1%}，暂不需要词级规范化去重'
    elif redundancy_rate > 0.20:
        result['recommendation'] = 'need_canonicalization'
        result['recommendation_detail'] = f'冗余率{redundancy_rate:.1%}，建议实施Phase 2.1词级规范化去重'
    else:
        result['recommendation'] = 'moderate'
        result['recommendation_detail'] = f'冗余率{redundancy_rate:.1%}，可考虑适度规范化'

    # 7. 保存结果
    output_dir = project_root / 'data' / 'phase0_results'
    output_dir.mkdir(parents=True, exist_ok=True)

    result_file = output_dir / 'experiment_c_result.json'
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 8. 显示结果
    print("\n" + "="*70)
    print("实验C结果")
    print("="*70)
    print(f"抽样数量:       {result['sample_size']:,}")
    print(f"同义组数:       {result['synonym_groups_count']}")
    print(f"同义短语数:     {result['phrases_in_groups']}")
    print(f"冗余率:         {result['redundancy_rate']:.1%}")
    print(f"\n判断结果:       {result['recommendation']}")
    print(f"建议:           {result['recommendation_detail']}")
    print(f"\n结果已保存到: {result_file}")
    print("="*70)

    return result


if __name__ == "__main__":
    try:
        result = run_experiment_c()

        print("\n✅ 实验C完成！")
        print(f"\n📌 下一步：运行实验D（搜索意图分布统计）")
        print(f"   命令: python scripts/phase0_experiment_d_intent_distribution.py")

    except KeyboardInterrupt:
        print("\n\n⚠️  实验被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 实验执行出错: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
