"""
Phase 0 - Experiment D (自动化版本): 搜索意图分布统计
Intent Distribution Measurement (Automated)

自动化策略：
- 基于关键词规则自动分类意图
- 统计各类意图的分布

创建日期：2025-12-23
"""

import json
import io
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import sys
import random

# Set UTF-8 encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.repository import PhraseRepository
from storage.models import Phrase


# 意图分类规则
INTENT_RULES = {
    'find_tool': {
        'name': '寻找工具/服务',
        'keywords': ['best', 'top', 'tool', 'software', 'app', 'recommend', 'good', 'great'],
        'priority': 1
    },
    'learn_how': {
        'name': '学习使用/教程',
        'keywords': ['how to', 'how do', 'tutorial', 'guide', 'learn', 'teach', 'instructions'],
        'priority': 2
    },
    'solve_problem': {
        'name': '解决问题',
        'keywords': ['fix', 'error', 'not working', 'problem', 'issue', 'broken', 'troubleshoot'],
        'priority': 2
    },
    'find_free': {
        'name': '寻找免费',
        'keywords': ['free', 'open source', 'no cost', 'gratis', 'opensource'],
        'priority': 1
    },
    'compare': {
        'name': '对比评估',
        'keywords': ['compare', 'comparison', 'difference', 'vs', 'versus', 'which', 'better'],
        'priority': 2
    },
    'other': {
        'name': '其他',
        'keywords': [],
        'priority': 99
    }
}


def classify_intent_auto(phrase: str) -> str:
    """
    自动分类意图

    策略：
    1. 按优先级顺序匹配关键词
    2. 第一个匹配的意图胜出
    3. 无匹配则归为other

    Args:
        phrase: 短语

    Returns:
        意图类别
    """
    phrase_lower = phrase.lower()

    # 按优先级排序
    sorted_intents = sorted(INTENT_RULES.items(),
                           key=lambda x: x[1]['priority'])

    for intent_key, intent_info in sorted_intents:
        if intent_key == 'other':
            continue

        # 检查关键词
        for keyword in intent_info['keywords']:
            if keyword in phrase_lower:
                return intent_key

    # 默认为other
    return 'other'


def run_experiment_d_auto() -> Dict:
    """
    自动化运行实验D
    """
    print("\n" + "="*70)
    print("Phase 0 - Experiment D (自动化): 搜索意图分布统计")
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

    # 3. 自动分类意图
    print(f"\n2. 自动分类搜索意图...")

    intent_counts = {intent_key: 0 for intent_key in INTENT_RULES.keys()}

    for phrase in sample_phrases:
        intent = classify_intent_auto(phrase)
        intent_counts[intent] += 1

    print(f"\n✓ 分类完成")

    # 计算分布
    intent_distribution = {}
    for intent_key, count in intent_counts.items():
        percentage = count / sample_size if sample_size > 0 else 0.0
        intent_distribution[intent_key] = {
            'name': INTENT_RULES[intent_key]['name'],
            'count': count,
            'percentage': percentage
        }

    # 显示分布
    print(f"\n📊 意图分布:")
    for intent_key, stats in intent_distribution.items():
        print(f"  {intent_key:15s}: {stats['count']:4d} ({stats['percentage']:>5.1%})")

    # 4. 生成结果
    result = {
        'experiment': 'D',
        'name': '搜索意图分布',
        'timestamp': datetime.now().isoformat(),
        'sample_size': sample_size,
        'intent_distribution': intent_distribution,
        'automation_note': '此结果由自动化脚本生成，基于关键词规则自动分类'
    }

    # 5. 决策逻辑
    find_tool_percentage = intent_distribution['find_tool']['percentage']

    if find_tool_percentage > 0.70:
        result['recommendation'] = 'similar_to_junyan'
        result['recommendation_detail'] = f'find_tool占比{find_tool_percentage:.1%}，类似君言模式，建议实施意图分类框架'
    elif find_tool_percentage < 0.40:
        result['recommendation'] = 'different_pattern'
        result['recommendation_detail'] = f'find_tool占比{find_tool_percentage:.1%}，模式较分散，建议均衡策略'
    else:
        result['recommendation'] = 'moderate'
        result['recommendation_detail'] = f'find_tool占比{find_tool_percentage:.1%}，中等分布，可实施意图分类作为辅助'

    print(f"\n" + "="*70)
    print("实验D结果")
    print("="*70)
    print(f"抽样数量: {sample_size:,}")
    print(f"find_tool占比: {find_tool_percentage:.1%}")
    print(f"\n判断: {result['recommendation']}")
    print(f"详情: {result['recommendation_detail']}")

    # 6. 保存结果
    output_dir = project_root / 'data' / 'phase0_results'
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / 'experiment_d_result.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n✓ 结果已保存到: {output_file}")

    return result


if __name__ == "__main__":
    try:
        result = run_experiment_d_auto()

        print("\n✅ 实验D (自动化版本) 完成！")
        print(f"\n📊 建议: {result['recommendation']}")

    except KeyboardInterrupt:
        print("\n\n⚠️  操作被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 实验执行出错: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
