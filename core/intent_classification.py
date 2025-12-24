"""
意图分类模块
Intent Classification Module

功能：
- 识别英文搜索短语的用户意图
- 采用均衡策略，支持多意图并存
- 基于关键词模式和LLM辅助

创建日期：2025-12-23
"""

import re
from typing import List, Dict, Optional
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai.client import LLMClient


class IntentClassifier:
    """
    意图分类器

    支持的意图类型：
    - find_tool: 寻找工具/软件
    - learn_how: 学习如何做某事
    - solve_problem: 解决问题
    - find_free: 寻找免费资源
    - compare: 比较选择
    - other: 其他意图
    """

    # 意图识别规则（基于关键词模式）
    INTENT_PATTERNS = {
        'find_tool': {
            'keywords': [
                r'\btool\b', r'\bsoftware\b', r'\bapp\b', r'\bplatform\b',
                r'\bwebsite\b', r'\bprogram\b', r'\bextension\b', r'\bplugin\b',
                r'\bcalculator\b', r'\bconverter\b', r'\bgenerator\b', r'\beditor\b'
            ],
            'prefixes': [r'^best\s+', r'^top\s+', r'^good\s+'],
            'suffixes': [r'\sfor\s+', r'\sto\s+'],
            'weight': 1.0
        },

        'learn_how': {
            'keywords': [
                r'\bhow\s+to\b', r'\btutorial\b', r'\bguide\b', r'\blearn\b',
                r'\bsteps\b', r'\bway\s+to\b', r'\bmethod\b', r'\btips\b'
            ],
            'prefixes': [r'^how\s+', r'^learn\s+', r'^tutorial\s+'],
            'weight': 1.2
        },

        'solve_problem': {
            'keywords': [
                r'\bfix\b', r'\bsolve\b', r'\brepair\b', r'\btroubleshoot\b',
                r'\berror\b', r'\bissue\b', r'\bproblem\b', r'\bnot\s+working\b',
                r'\bfailed\b', r'\bwhy\b'
            ],
            'prefixes': [r'^fix\s+', r'^solve\s+', r'^why\s+'],
            'weight': 1.1
        },

        'find_free': {
            'keywords': [
                r'\bfree\b', r'\bopen\s+source\b', r'\bno\s+cost\b',
                r'\bgratis\b', r'\bfreeware\b'
            ],
            'weight': 1.3
        },

        'compare': {
            'keywords': [
                r'\bvs\b', r'\bversus\b', r'\bcompare\b', r'\bdifference\b',
                r'\bwhich\b', r'\bbetter\b', r'\balternative\b', r'\bor\b'
            ],
            'prefixes': [r'^which\s+', r'^compare\s+'],
            'weight': 1.2
        }
    }

    def __init__(self, use_llm: bool = False, llm_client: Optional[LLMClient] = None):
        """
        初始化意图分类器

        Args:
            use_llm: 是否使用LLM辅助分类
            llm_client: LLM客户端实例
        """
        self.use_llm = use_llm
        self.llm_client = llm_client if use_llm else None

    def classify_phrase(self, phrase: str) -> Dict:
        """
        分类单个短语的意图

        Args:
            phrase: 英文搜索短语

        Returns:
            {
                'primary_intent': 'find_tool',
                'confidence': 0.85,
                'all_intents': {
                    'find_tool': 0.85,
                    'learn_how': 0.15
                }
            }
        """
        phrase_lower = phrase.lower()

        # 计算每个意图的得分
        intent_scores = {}

        for intent_name, patterns in self.INTENT_PATTERNS.items():
            score = 0.0

            # 关键词匹配
            if 'keywords' in patterns:
                for keyword_pattern in patterns['keywords']:
                    if re.search(keyword_pattern, phrase_lower):
                        score += patterns['weight']

            # 前缀匹配
            if 'prefixes' in patterns:
                for prefix_pattern in patterns['prefixes']:
                    if re.search(prefix_pattern, phrase_lower):
                        score += patterns['weight'] * 1.5  # 前缀权重更高

            # 后缀匹配
            if 'suffixes' in patterns:
                for suffix_pattern in patterns['suffixes']:
                    if re.search(suffix_pattern, phrase_lower):
                        score += patterns['weight'] * 0.5  # 后缀权重较低

            if score > 0:
                intent_scores[intent_name] = score

        # 如果没有匹配任何意图，归类为'other'
        if not intent_scores:
            return {
                'primary_intent': 'other',
                'confidence': 1.0,
                'all_intents': {'other': 1.0}
            }

        # 归一化得分
        total_score = sum(intent_scores.values())
        normalized_scores = {
            intent: score / total_score
            for intent, score in intent_scores.items()
        }

        # 确定主要意图
        primary_intent = max(normalized_scores.items(), key=lambda x: x[1])

        return {
            'primary_intent': primary_intent[0],
            'confidence': primary_intent[1],
            'all_intents': normalized_scores
        }

    def classify_batch(self, phrases: List[str]) -> List[Dict]:
        """
        批量分类短语意图

        Args:
            phrases: 短语列表

        Returns:
            分类结果列表
        """
        results = []

        for phrase in phrases:
            result = self.classify_phrase(phrase)
            results.append(result)

        return results

    def analyze_cluster_intent(self, phrases: List[str], sample_size: int = 50) -> Dict:
        """
        分析聚类簇的整体意图分布

        Args:
            phrases: 簇中的短语列表
            sample_size: 抽样大小

        Returns:
            {
                'dominant_intent': 'find_tool',
                'dominant_confidence': 0.65,
                'intent_distribution': {
                    'find_tool': 0.65,
                    'learn_how': 0.25,
                    'other': 0.10
                },
                'is_balanced': False,  # 是否意图均衡
                'sample_size': 50
            }
        """
        # 限制样本大小
        sample_size = min(sample_size, len(phrases))

        if len(phrases) <= sample_size:
            sample_phrases = phrases
        else:
            # 取前N个（按重要性排序）
            sample_phrases = phrases[:sample_size]

        # 批量分类
        classifications = self.classify_batch(sample_phrases)

        # 统计意图分布
        intent_counts = {}
        for classification in classifications:
            primary_intent = classification['primary_intent']
            intent_counts[primary_intent] = intent_counts.get(primary_intent, 0) + 1

        # 计算分布
        total_count = len(classifications)
        intent_distribution = {
            intent: count / total_count
            for intent, count in intent_counts.items()
        }

        # 确定主导意图
        dominant_intent = max(intent_distribution.items(), key=lambda x: x[1])

        # 判断是否均衡（主导意图<60%视为均衡）
        is_balanced = dominant_intent[1] < 0.6

        return {
            'dominant_intent': dominant_intent[0],
            'dominant_confidence': dominant_intent[1],
            'intent_distribution': intent_distribution,
            'is_balanced': is_balanced,
            'sample_size': total_count
        }

    def get_intent_label(self, intent_code: str) -> str:
        """
        获取意图的中文标签

        Args:
            intent_code: 意图代码

        Returns:
            中文标签
        """
        labels = {
            'find_tool': '寻找工具',
            'learn_how': '学习教程',
            'solve_problem': '解决问题',
            'find_free': '寻找免费资源',
            'compare': '比较选择',
            'other': '其他意图'
        }

        return labels.get(intent_code, '未知意图')

    def get_intent_description(self, intent_code: str) -> str:
        """
        获取意图的详细描述

        Args:
            intent_code: 意图代码

        Returns:
            详细描述
        """
        descriptions = {
            'find_tool': '用户正在寻找工具、软件、应用程序或在线平台',
            'learn_how': '用户想学习如何做某事，寻找教程或指南',
            'solve_problem': '用户遇到问题，需要解决方案或故障排除',
            'find_free': '用户特别关注免费或开源的选项',
            'compare': '用户想比较不同选项，做出选择',
            'other': '其他类型的搜索意图'
        }

        return descriptions.get(intent_code, '未知意图类型')


def demo_intent_classification():
    """
    演示意图分类功能
    """
    classifier = IntentClassifier()

    print("="*80)
    print("意图分类模块 - 演示")
    print("="*80)
    print()

    # 测试案例
    test_phrases = [
        "best calculator for math",           # find_tool
        "how to use calculator",              # learn_how
        "calculator not working fix",         # solve_problem
        "free calculator app",                # find_free + find_tool
        "which calculator vs calculator app", # compare + find_tool
        "calculator reviews",                 # other
    ]

    print("单个短语分类测试:")
    print("-"*80)

    for phrase in test_phrases:
        result = classifier.classify_phrase(phrase)
        print(f"\n短语: {phrase}")
        print(f"主要意图: {result['primary_intent']} ({classifier.get_intent_label(result['primary_intent'])})")
        print(f"置信度: {result['confidence']:.2f}")
        print(f"所有意图: {result['all_intents']}")

    print("\n" + "="*80)
    print("聚类意图分析测试:")
    print("-"*80)

    cluster_phrases = [
        "best coffee maker",
        "top rated coffee machines",
        "coffee maker reviews",
        "which coffee maker to buy",
        "coffee maker for home",
    ] * 4  # 模拟20个短语

    cluster_result = classifier.analyze_cluster_intent(cluster_phrases)

    print(f"\n簇大小: {len(cluster_phrases)}")
    print(f"抽样大小: {cluster_result['sample_size']}")
    print(f"\n主导意图: {cluster_result['dominant_intent']} ({classifier.get_intent_label(cluster_result['dominant_intent'])})")
    print(f"主导置信度: {cluster_result['dominant_confidence']:.2%}")
    print(f"是否均衡: {'是' if cluster_result['is_balanced'] else '否'}")
    print(f"\n意图分布:")
    for intent, percentage in sorted(cluster_result['intent_distribution'].items(), key=lambda x: x[1], reverse=True):
        bar = '=' * int(percentage * 50)
        print(f"  {classifier.get_intent_label(intent):12s} ({intent:15s}): {percentage:6.1%} {bar}")


if __name__ == "__main__":
    try:
        demo_intent_classification()
    except KeyboardInterrupt:
        print("\n\n[WARN] 操作被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] 演示失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
