"""
LLM聚类预评估模块
LLM Cluster Pre-assessment Module

功能：
- 使用LLM生成聚类主题摘要
- 评估聚类的业务价值
- 为聚类审核提供AI辅助

创建日期：2025-12-23
"""

import sys
from typing import List, Dict, Optional
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai.client import LLMClient


class ClusterLLMAssessor:
    """
    LLM聚类评估器

    功能：
    1. 生成聚类主题摘要
    2. 评估业务价值
    3. 判断是否值得关注
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        初始化评估器

        Args:
            llm_client: LLM客户端实例，如果为None则创建新实例
        """
        self.llm_client = llm_client or LLMClient()

    def assess_cluster(self, phrases: List[str],
                      sample_size: int = 30) -> Dict:
        """
        对一个聚类簇进行LLM评估

        Args:
            phrases: 簇中的短语列表
            sample_size: 抽样大小（避免token过多）

        Returns:
            评估结果字典，包含：
            - summary: 主题摘要
            - value_assessment: 价值评估
            - recommended: 是否推荐关注
            - confidence: 置信度 (0-1)
        """
        # 限制样本大小
        sample_size = min(sample_size, len(phrases))

        if len(phrases) <= sample_size:
            sample_phrases = phrases
        else:
            # 取前N个（已经是按频率或重要性排序）
            sample_phrases = phrases[:sample_size]

        # 构建prompt
        prompt = self._build_assessment_prompt(sample_phrases)

        try:
            # 调用LLM
            messages = [{"role": "user", "content": prompt}]
            response = self.llm_client._call_llm(messages)

            # 解析响应
            result = self._parse_llm_response(response)

            return result

        except Exception as e:
            print(f"⚠️  LLM评估失败: {e}")
            return {
                'summary': '（评估失败）',
                'value_assessment': f'评估过程出错: {str(e)}',
                'recommended': False,
                'confidence': 0.0
            }

    def _build_assessment_prompt(self, phrases: List[str]) -> str:
        """
        构建LLM评估的prompt

        Args:
            phrases: 短语列表

        Returns:
            prompt文本
        """
        phrases_text = "\n".join(f"{i+1}. {p}" for i, p in enumerate(phrases[:30]))

        prompt = f"""你是一个需求分析专家。请分析以下英文搜索关键词聚类，这些关键词代表用户的搜索意图。

关键词列表（共{len(phrases)}个短语，显示前30个）：
{phrases_text}

请完成以下任务：

1. **主题摘要**（1-2句话）：
   - 用简洁的中文描述这个聚类的核心主题
   - 例如："寻找咖啡机的推荐和评价"

2. **价值评估**（50字以内）：
   - 这个需求是否有商业价值？
   - 是否代表一个明确的用户需求？
   - 是否值得进一步挖掘？

3. **推荐度**（是/否）：
   - 是否推荐优先关注这个聚类？

4. **置信度**（0-1之间的小数）：
   - 你对上述判断的置信度

请按以下格式回复（严格遵守格式）：

摘要：[你的主题摘要]
评估：[你的价值评估]
推荐：[是/否]
置信度：[0-1之间的数字]"""

        return prompt

    def _parse_llm_response(self, response: str) -> Dict:
        """
        解析LLM响应

        Args:
            response: LLM的原始响应

        Returns:
            解析后的字典
        """
        result = {
            'summary': '',
            'value_assessment': '',
            'recommended': False,
            'confidence': 0.5  # 默认中等置信度
        }

        try:
            lines = response.strip().split('\n')

            for line in lines:
                line = line.strip()

                if line.startswith('摘要：') or line.startswith('摘要:'):
                    result['summary'] = line.split('：', 1)[-1].split(':', 1)[-1].strip()

                elif line.startswith('评估：') or line.startswith('评估:'):
                    result['value_assessment'] = line.split('：', 1)[-1].split(':', 1)[-1].strip()

                elif line.startswith('推荐：') or line.startswith('推荐:'):
                    recommend_text = line.split('：', 1)[-1].split(':', 1)[-1].strip()
                    result['recommended'] = recommend_text in ['是', 'Yes', 'yes', 'TRUE', 'True', 'true']

                elif line.startswith('置信度：') or line.startswith('置信度:'):
                    confidence_text = line.split('：', 1)[-1].split(':', 1)[-1].strip()
                    try:
                        result['confidence'] = float(confidence_text)
                    except ValueError:
                        result['confidence'] = 0.5

            # 如果摘要为空，使用整个响应作为摘要
            if not result['summary']:
                result['summary'] = response[:200]  # 取前200字符

        except Exception as e:
            print(f"⚠️  解析LLM响应失败: {e}")
            result['summary'] = response[:200] if response else '（解析失败）'

        return result

    def batch_assess_clusters(self, clusters_data: Dict[int, List[str]],
                             max_count: Optional[int] = None) -> Dict[int, Dict]:
        """
        批量评估多个聚类簇

        Args:
            clusters_data: {cluster_id: [phrases]}
            max_count: 最多评估的簇数量（None表示全部）

        Returns:
            {cluster_id: assessment_result}
        """
        results = {}

        cluster_ids = list(clusters_data.keys())
        if max_count:
            cluster_ids = cluster_ids[:max_count]

        total = len(cluster_ids)

        print(f"\n开始LLM批量评估（共{total}个簇）...")

        for i, cluster_id in enumerate(cluster_ids, 1):
            print(f"  [{i}/{total}] 评估簇 {cluster_id}...", end='')

            phrases = clusters_data[cluster_id]
            assessment = self.assess_cluster(phrases)

            results[cluster_id] = assessment

            print(f" ✓ (推荐: {assessment['recommended']}, 置信度: {assessment['confidence']:.2f})")

        print(f"\n✓ 批量评估完成，共{len(results)}个簇")

        return results


def demo_assessment():
    """
    演示LLM评估功能
    """
    assessor = ClusterLLMAssessor()

    # 测试案例：咖啡机相关搜索
    test_phrases = [
        "best coffee maker",
        "top rated coffee machines",
        "drip coffee maker reviews",
        "espresso machine recommendations",
        "best coffee maker for home",
        "coffee maker with grinder",
        "single serve coffee maker",
        "automatic coffee machine",
        "best budget coffee maker",
        "commercial coffee maker"
    ]

    print("="*70)
    print("LLM聚类评估 - 演示")
    print("="*70)
    print()
    print("测试短语：")
    for i, phrase in enumerate(test_phrases, 1):
        print(f"  {i}. {phrase}")
    print()

    print("正在调用LLM进行评估...")
    print()

    result = assessor.assess_cluster(test_phrases)

    print("评估结果：")
    print("-"*70)
    print(f"主题摘要：{result['summary']}")
    print(f"价值评估：{result['value_assessment']}")
    print(f"推荐关注：{'是' if result['recommended'] else '否'}")
    print(f"置信度：{result['confidence']:.2f}")
    print("-"*70)


if __name__ == "__main__":
    try:
        demo_assessment()
    except KeyboardInterrupt:
        print("\n\n⚠️  操作被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 演示失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
