"""
Cluster Semantic Labeling using DeepSeek LLM
使用DeepSeek LLM对聚类进行语义标注
"""
import sys
from pathlib import Path
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

import json
import random
from typing import List, Dict, Optional
from openai import OpenAI

from config.settings import LLM_CONFIG, CLUSTER_LABELING_CONFIG
from utils.logger import get_logger

logger = get_logger(__name__)


class ClusterLabeler:
    """聚类语义标注器"""

    def __init__(self, provider: str = "deepseek"):
        """初始化DeepSeek标注器"""
        self.provider = provider

        if provider == "deepseek":
            config = LLM_CONFIG["deepseek"]
            self.client = OpenAI(
                api_key=config["api_key"],
                base_url=config["base_url"]
            )
            self.model = config["model"]
            self.temperature = CLUSTER_LABELING_CONFIG["temperature"]
            self.max_tokens = CLUSTER_LABELING_CONFIG["max_tokens"]
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        logger.info(f"初始化ClusterLabeler - Provider: {provider}, Model: {self.model}")

    def label_cluster(
        self,
        cluster_id: int,
        phrases: List[str],
        sample_size: Optional[int] = None
    ) -> Dict:
        """
        为单个聚类生成语义标注

        Args:
            cluster_id: 聚类ID
            phrases: 聚类中的所有短语
            sample_size: 抽样数量（None表示使用配置值）

        Returns:
            标注结果字典:
            {
                'llm_label': 简短标签 (String, 1-5个词)
                'llm_summary': 详细描述 (Text, 1-2句话)
                'primary_demand_type': 主需求类型 (tool/content/service/education/other)
                'secondary_demand_types': 次要需求类型列表 (List[str])
                'labeling_confidence': 标注置信度 (0-100)
            }
        """
        # 1. 抽样短语
        if sample_size is None:
            sample_size = CLUSTER_LABELING_CONFIG["sample_size_per_cluster"]

        if len(phrases) > sample_size:
            sampled_phrases = random.sample(phrases, sample_size)
        else:
            sampled_phrases = phrases

        # 2. 构建Prompt
        prompt = self._build_labeling_prompt(cluster_id, sampled_phrases)

        # 3. 调用DeepSeek API
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing search intent and categorizing user needs from keyword data."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )

            # 4. 解析响应
            result_text = response.choices[0].message.content
            result = json.loads(result_text)

            # 5. 验证并规范化输出
            validated_result = self._validate_result(result)

            logger.info(f"聚类 {cluster_id} 标注完成: {validated_result['llm_label']}")
            return validated_result

        except Exception as e:
            logger.error(f"聚类 {cluster_id} 标注失败: {str(e)}")
            # 返回默认值
            return {
                'llm_label': f"Cluster {cluster_id}",
                'llm_summary': "Labeling failed",
                'primary_demand_type': "other",
                'secondary_demand_types': [],
                'labeling_confidence': 0
            }

    def _build_labeling_prompt(self, cluster_id: int, phrases: List[str]) -> str:
        """构建标注Prompt"""
        phrases_text = "\n".join(f"- {p}" for p in phrases[:40])  # 最多40条

        prompt = f"""Analyze the following keyword cluster and provide semantic labeling.

Cluster ID: {cluster_id}
Phrases in this cluster:
{phrases_text}

Please analyze the search intent and user needs behind these keywords, then provide:

1. **llm_label**: A concise label (1-5 words) that captures the main theme
2. **llm_summary**: A detailed description (1-2 sentences) explaining what users are looking for
3. **primary_demand_type**: The primary type of user need (choose ONE):
   - "tool": Users need a tool/software/application
   - "content": Users need information/articles/guides
   - "service": Users need a professional service
   - "education": Users want to learn/study something
   - "other": Doesn't fit above categories
4. **secondary_demand_types**: List of additional applicable types (empty if none)
5. **labeling_confidence**: Your confidence in this labeling (0-100)

Return ONLY a JSON object with these exact keys:
{{
  "llm_label": "...",
  "llm_summary": "...",
  "primary_demand_type": "...",
  "secondary_demand_types": [...],
  "labeling_confidence": ...
}}"""

        return prompt

    def _validate_result(self, result: Dict) -> Dict:
        """验证并规范化LLM输出"""
        validated = {
            'llm_label': str(result.get('llm_label', 'Unknown'))[:100],  # 限制长度
            'llm_summary': str(result.get('llm_summary', ''))[:500],
            'primary_demand_type': self._validate_demand_type(
                result.get('primary_demand_type', 'other')
            ),
            'secondary_demand_types': [
                self._validate_demand_type(t)
                for t in result.get('secondary_demand_types', [])
            ],
            'labeling_confidence': max(0, min(100, int(result.get('labeling_confidence', 50))))
        }

        return validated

    def _validate_demand_type(self, dtype: str) -> str:
        """验证需求类型"""
        valid_types = ["tool", "content", "service", "education", "other"]
        dtype_lower = str(dtype).lower()
        return dtype_lower if dtype_lower in valid_types else "other"

    def label_clusters_batch(
        self,
        clusters: List[Dict],
        max_clusters_per_batch: Optional[int] = None
    ) -> Dict[int, Dict]:
        """
        批量标注多个聚类

        Args:
            clusters: 聚类列表，每个元素为 {'cluster_id': int, 'phrases': List[str]}
            max_clusters_per_batch: 每批处理的聚类数（None表示全部处理）

        Returns:
            {cluster_id: labeling_result}
        """
        if max_clusters_per_batch is None:
            max_clusters_per_batch = CLUSTER_LABELING_CONFIG["max_clusters_per_batch"]

        results = {}
        total = len(clusters)

        logger.info(f"开始批量标注 {total} 个聚类...")

        for i, cluster in enumerate(clusters, 1):
            cluster_id = cluster['cluster_id']
            phrases = cluster['phrases']

            logger.info(f"[{i}/{total}] 标注聚类 {cluster_id} ({len(phrases)} phrases)...")

            result = self.label_cluster(cluster_id, phrases)
            results[cluster_id] = result

            # 批次控制（避免过载）
            if max_clusters_per_batch > 0 and i >= max_clusters_per_batch:
                logger.info(f"达到批次限制 ({max_clusters_per_batch})，停止标注")
                break

        logger.info(f"批量标注完成: {len(results)}/{total} 个聚类")
        return results


def test_cluster_labeler():
    """测试聚类标注器"""
    logger.info("="*70)
    logger.info("测试ClusterLabeler")
    logger.info("="*70)

    # 创建测试数据
    test_cluster = {
        'cluster_id': 1,
        'phrases': [
            'how to learn python',
            'python tutorial for beginners',
            'python programming course',
            'learn python online',
            'python basics',
            'python for data science',
            'python coding tutorial',
            'best way to learn python',
        ]
    }

    # 初始化标注器
    try:
        labeler = ClusterLabeler(provider="deepseek")

        # 标注单个聚类
        result = labeler.label_cluster(
            test_cluster['cluster_id'],
            test_cluster['phrases']
        )

        # 验证结果
        assert 'llm_label' in result, "缺少llm_label"
        assert 'llm_summary' in result, "缺少llm_summary"
        assert 'primary_demand_type' in result, "缺少primary_demand_type"
        assert result['primary_demand_type'] in ['tool', 'content', 'service', 'education', 'other']

        logger.info("\nOK: ClusterLabeler测试通过！")
        logger.info(f"  标签: {result['llm_label']}")
        logger.info(f"  描述: {result['llm_summary']}")
        logger.info(f"  主需求: {result['primary_demand_type']}")
        logger.info(f"  置信度: {result['labeling_confidence']}")

        return True

    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_cluster_labeler()
