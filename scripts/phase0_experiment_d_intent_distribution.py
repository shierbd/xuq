"""
Phase 0 - Experiment D: 搜索意图分布统计
Search Intent Distribution Analysis

目标：统计英文关键词的搜索意图分布

判断标准：
- find_tool占比>70% → 类似君言"寻找类占主导"，采用意图分类框架
- 分布较均匀 → 英文场景不同，需要调整策略

创建日期：2025-12-23
"""

import json
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from collections import Counter
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.repository import PhraseRepository


# 意图分类框架
INTENT_CATEGORIES = {
    'find_tool': {
        'name': '寻找工具/服务',
        'description': '寻找、推荐、对比工具/服务/产品',
        'keywords': ['best', 'top', 'tool', 'software', 'app', 'recommend', 'vs', 'versus', 'alternative'],
        'examples': [
            'best image compressor',
            'top photo editor',
            'photoshop vs gimp'
        ]
    },
    'learn_how': {
        'name': '学习使用/教程',
        'description': '学习如何使用、教程、指南',
        'keywords': ['how to', 'tutorial', 'guide', 'learn', 'steps', 'tips'],
        'examples': [
            'how to compress images',
            'excel tutorial',
            'learn python'
        ]
    },
    'solve_problem': {
        'name': '解决问题',
        'description': '修复错误、解决故障',
        'keywords': ['fix', 'error', 'not working', 'problem', 'issue', 'troubleshoot'],
        'examples': [
            'chrome not working',
            'fix wifi connection',
            'excel error'
        ]
    },
    'find_free': {
        'name': '寻找免费',
        'description': '寻找免费资源/工具',
        'keywords': ['free', 'open source', 'no cost', 'without payment'],
        'examples': [
            'free video editor',
            'open source CRM',
            'free image hosting'
        ]
    },
    'compare': {
        'name': '对比评估',
        'description': '对比不同选项',
        'keywords': ['compare', 'difference', 'which', 'or', 'better'],
        'examples': [
            'compare photo editors',
            'mac vs pc',
            'which is better'
        ]
    },
    'other': {
        'name': '其他',
        'description': '不属于以上任何类别',
        'keywords': [],
        'examples': []
    }
}


def display_intent_guide():
    """
    显示意图分类指南
    """
    print("\n" + "="*70)
    print("搜索意图分类指南")
    print("="*70)
    print("\n请为每个短语选择一个最匹配的意图类别：\n")

    for i, (intent_key, config) in enumerate(INTENT_CATEGORIES.items(), 1):
        print(f"{i}. {intent_key} - {config['name']}")
        print(f"   描述: {config['description']}")
        if config['keywords']:
            print(f"   关键词: {', '.join(config['keywords'][:5])}")
        if config['examples']:
            print(f"   示例: {config['examples'][0]}")
        print()


def classify_intent_interactive(sample_phrases: List[str]) -> List[str]:
    """
    交互式意图分类

    Args:
        sample_phrases: 抽样短语列表

    Returns:
        意图列表，与sample_phrases一一对应
    """
    display_intent_guide()

    intent_keys = list(INTENT_CATEGORIES.keys())
    intent_mapping = {str(i+1): key for i, key in enumerate(intent_keys)}

    print("操作说明：")
    print("  - 输入数字1-6选择意图类别")
    print("  - 输入 'q' 提前结束")
    print("  - 输入 's' 显示分类指南")
    print()

    input("准备好了吗？按 Enter 键开始...")

    results = []

    for idx, phrase in enumerate(sample_phrases):
        print("\n" + "="*70)
        print(f"进度: {idx + 1}/{len(sample_phrases)}")
        print("="*70)
        print(f"\n短语: {phrase}")

        while True:
            user_input = input("\n选择意图 (1-6, 's'=指南, 'q'=退出): ").strip().lower()

            if user_input == 'q':
                print("\n提前结束标注")
                # 剩余的标为other
                results.extend(['other'] * (len(sample_phrases) - len(results)))
                return results

            if user_input == 's':
                display_intent_guide()
                continue

            if user_input in intent_mapping:
                intent = intent_mapping[user_input]
                results.append(intent)
                print(f"✓ 已标记为: {intent}")
                break
            else:
                print("⚠️  无效输入，请输入1-6")

    return results


def run_experiment_d() -> Dict:
    """
    执行实验D：搜索意图分布统计

    Returns:
        实验结果字典
    """
    print("\n" + "="*70)
    print("Phase 0 - Experiment D: 搜索意图分布统计")
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

    random.seed(43)  # 固定种子，便于复现
    sample_phrases_obj = random.sample(all_phrases, sample_size)
    sample_phrases = [p.phrase for p in sample_phrases_obj]

    print(f"✓ 抽样完成")

    # 3. 交互式意图标注
    print("\n3. 开始意图标注...")

    intent_labels = classify_intent_interactive(sample_phrases)

    # 4. 统计结果
    print("\n" + "="*70)
    print("标注结果统计")
    print("="*70)

    intent_counter = Counter(intent_labels)

    print(f"\n意图分布：")
    for intent_key in INTENT_CATEGORIES.keys():
        count = intent_counter[intent_key]
        percentage = count / sample_size * 100 if sample_size > 0 else 0
        print(f"  {intent_key:20s}: {count:4d} ({percentage:5.1f}%)")

    # 显示每个意图的示例
    print(f"\n各意图示例短语（前3个）：")
    for intent_key in INTENT_CATEGORIES.keys():
        examples = [
            sample_phrases[i]
            for i, label in enumerate(intent_labels)
            if label == intent_key
        ][:3]

        if examples:
            print(f"\n  {intent_key}:")
            for ex in examples:
                print(f"    - {ex}")

    # 5. 生成结果
    result = {
        'experiment': 'D',
        'name': '搜索意图分布',
        'timestamp': datetime.now().isoformat(),
        'sample_size': sample_size,
        'total_phrases': total_phrases,
        'intent_distribution': {
            intent: {
                'count': intent_counter[intent],
                'percentage': round(intent_counter[intent] / sample_size, 4) if sample_size > 0 else 0
            }
            for intent in INTENT_CATEGORIES.keys()
        },
        'labeled_samples': [
            {
                'phrase': phrase,
                'intent': intent
            }
            for phrase, intent in zip(sample_phrases, intent_labels)
        ]
    }

    # 6. 判断分布特征
    find_tool_percentage = intent_counter['find_tool'] / sample_size if sample_size > 0 else 0

    if find_tool_percentage > 0.70:
        result['recommendation'] = 'similar_to_junyan'
        result['recommendation_detail'] = (
            f'find_tool占比{find_tool_percentage:.1%}，类似君言"寻找类占主导"模式，'
            f'建议采用意图驱动的分类框架'
        )
    elif find_tool_percentage < 0.40:
        result['recommendation'] = 'different_pattern'
        result['recommendation_detail'] = (
            f'find_tool占比{find_tool_percentage:.1%}，分布较均匀，'
            f'英文场景与君言不同，需要调整策略'
        )
    else:
        result['recommendation'] = 'moderate'
        result['recommendation_detail'] = (
            f'find_tool占比{find_tool_percentage:.1%}，中等分布，'
            f'可考虑混合策略'
        )

    # 7. 保存结果
    output_dir = project_root / 'data' / 'phase0_results'
    output_dir.mkdir(parents=True, exist_ok=True)

    result_file = output_dir / 'experiment_d_result.json'
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 8. 显示结果
    print("\n" + "="*70)
    print("实验D结果")
    print("="*70)
    print(f"抽样数量:       {result['sample_size']:,}")
    print(f"\n意图分布:")
    for intent_key, stats in result['intent_distribution'].items():
        print(f"  {intent_key:20s}: {stats['count']:4d} ({stats['percentage']:.1%})")
    print(f"\n判断结果:       {result['recommendation']}")
    print(f"建议:           {result['recommendation_detail']}")
    print(f"\n结果已保存到: {result_file}")
    print("="*70)

    return result


if __name__ == "__main__":
    try:
        result = run_experiment_d()

        print("\n✅ 实验D完成！")
        print(f"\n📌 下一步：生成Phase 0基线报告")
        print(f"   命令: python scripts/phase0_generate_baseline_report.py")

    except KeyboardInterrupt:
        print("\n\n⚠️  实验被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 实验执行出错: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
