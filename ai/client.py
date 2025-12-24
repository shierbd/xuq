"""
LLM客户端模块
支持OpenAI, Anthropic, Deepseek等多种LLM提供商
用于生成聚类主题和需求卡片
"""
import os
from typing import List, Dict, Optional
import json
import re

from config.settings import LLM_PROVIDER, LLM_CONFIG
from utils.logger import get_logger
from utils.retry import retry
from utils.exceptions import LLMException

logger = get_logger(__name__)


class LLMClient:
    """LLM客户端类"""

    def __init__(self, provider: str = None):
        """
        初始化LLM客户端

        Args:
            provider: LLM提供商 ('openai', 'anthropic', 'deepseek')
                      默认使用config.settings中的配置
        """
        self.provider = provider or LLM_PROVIDER
        self.config = LLM_CONFIG.get(self.provider)

        if not self.config:
            raise ValueError(f"不支持的LLM提供商: {self.provider}")

        if not self.config.get("api_key"):
            raise ValueError(f"{self.provider} API密钥未配置")

        # 初始化客户端
        self.client = self._init_client()

        logger.info(f"LLM客户端初始化完成: {self.provider} / {self.config['model']}")

    def _init_client(self):
        """初始化具体的LLM客户端"""
        if self.provider == "openai":
            from openai import OpenAI
            return OpenAI(
                api_key=self.config["api_key"],
                base_url=self.config.get("base_url")
            )
        elif self.provider == "anthropic":
            from anthropic import Anthropic
            return Anthropic(api_key=self.config["api_key"])
        elif self.provider == "deepseek":
            from openai import OpenAI  # Deepseek使用OpenAI兼容接口
            return OpenAI(
                api_key=self.config["api_key"],
                base_url=self.config.get("base_url")
            )
        else:
            raise ValueError(f"不支持的提供商: {self.provider}")

    @retry(max_attempts=3, delay=1, backoff=2, exceptions=(ConnectionError, TimeoutError, Exception))
    def _call_llm(self, messages: List[Dict[str, str]],
                  temperature: float = None,
                  max_tokens: int = None) -> str:
        """
        调用LLM API

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            temperature: 温度参数
            max_tokens: 最大token数

        Returns:
            LLM响应文本
        """
        temperature = temperature or self.config["temperature"]
        max_tokens = max_tokens or self.config["max_tokens"]

        try:
            if self.provider in ["openai", "deepseek"]:
                response = self.client.chat.completions.create(
                    model=self.config["model"],
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content

            elif self.provider == "anthropic":
                # Anthropic API格式不同
                system_message = ""
                user_messages = []
                for msg in messages:
                    if msg["role"] == "system":
                        system_message = msg["content"]
                    else:
                        user_messages.append(msg)

                response = self.client.messages.create(
                    model=self.config["model"],
                    system=system_message,
                    messages=user_messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.content[0].text

        except Exception as e:
            logger.error(f"LLM API调用失败: {str(e)}")
            raise LLMException(f"LLM API调用失败: {str(e)}")

    def generate_cluster_theme(self,
                               example_phrases: List[str],
                               cluster_size: int,
                               cluster_id: int = None) -> Dict:
        """
        生成聚类主题标签

        Args:
            example_phrases: 示例短语列表（10条左右）
            cluster_size: 聚类大小
            cluster_id: 聚类ID（可选，用于日志）

        Returns:
            {'theme': '主题标签', 'confidence': 'high/medium/low'}
        """
        # 构建prompt
        phrases_str = "\n".join([f"- {phrase}" for phrase in example_phrases[:10]])

        prompt = f"""你是一个搜索关键词分析专家。请根据以下搜索短语聚类，生成一个简洁的主题标签。

【聚类信息】
- 聚类大小: {cluster_size} 条短语
- 示例短语（前10条）:
{phrases_str}

【要求】
1. 主题标签应该是2-6个词，简洁清晰
2. 用中文描述该聚类的核心意图或主题
3. 标签应该能够概括大部分示例短语的共同点
4. 返回JSON格式: {{"theme": "主题标签", "confidence": "high|medium|low"}}

【示例】
示例输入: "best running shoes", "top rated running shoes", "comfortable running shoes"
示例输出: {{"theme": "跑鞋推荐", "confidence": "high"}}

请为上述聚类生成主题标签:"""

        messages = [
            {"role": "user", "content": prompt}
        ]

        # 调用LLM
        response = self._call_llm(messages, temperature=0.3)

        # 解析响应
        try:
            # 尝试解析JSON
            result = json.loads(response.strip())
            theme = result.get("theme", "未分类")
            confidence = result.get("confidence", "medium")
        except json.JSONDecodeError:
            # 如果不是JSON，直接使用响应文本作为主题
            theme = response.strip()
            confidence = "medium"

        if cluster_id is not None:
            logger.info(f"簇{cluster_id}: {theme} ({confidence})")

        return {
            "theme": theme,
            "confidence": confidence
        }

    def generate_demand_card(self,
                            cluster_id_A: int,
                            cluster_id_B: int,
                            main_theme: str,
                            phrases: List[str],
                            total_frequency: int,
                            total_volume: int,
                            framework: Dict = None) -> Dict:
        """
        生成需求卡片初稿

        Args:
            cluster_id_A: 大组ID
            cluster_id_B: 小组ID
            main_theme: 大组主题
            phrases: 小组内的短语列表（20-50条）
            total_frequency: 总频次
            total_volume: 总搜索量
            framework: 需求框架信息（可选，包含intent/action/object tokens）

        Returns:
            需求卡片字典
        """
        # 限制短语数量
        phrases_sample = phrases[:30]
        phrases_str = "\n".join([f"- {phrase}" for phrase in phrases_sample])

        # 构建框架信息部分
        framework_section = ""
        if framework:
            framework_parts = []

            if framework.get('intent'):
                intent_tokens = [f"{token}({count}次)" for token, count in framework['intent'][:5]]
                framework_parts.append(f"  意图词: {', '.join(intent_tokens)}")

            if framework.get('action'):
                action_tokens = [f"{token}({count}次)" for token, count in framework['action'][:5]]
                framework_parts.append(f"  动作词: {', '.join(action_tokens)}")

            if framework.get('object'):
                object_tokens = [f"{token}({count}次)" for token, count in framework['object'][:5]]
                framework_parts.append(f"  对象词: {', '.join(object_tokens)}")

            if framework_parts:
                framework_section = "\n【需求框架分析】\n该小组的关键词分析结果：\n" + "\n".join(framework_parts) + "\n"

        prompt = f"""你是一个产品需求分析专家。请根据以下搜索短语聚类，生成一个用户需求卡片。

【聚类信息】
- 大组主题: {main_theme}
- 小组ID: {cluster_id_B}
- 短语数量: {len(phrases)} 条
- 总频次: {total_frequency:,}
- 总搜索量: {total_volume:,}
{framework_section}
【示例短语（前30条）】
{phrases_str}

【要求】
请基于上述框架分析（如有）和示例短语，生成一个JSON格式的需求卡片，包含以下字段：

{{
  "demand_title": "需求标题（5-15字，简洁有力）",
  "demand_description": "需求描述（50-200字，描述用户意图和痛点）",
  "user_intent": "用户意图（20-50字，用户想要做什么）",
  "pain_points": ["痛点1", "痛点2", "痛点3"],
  "target_audience": "目标用户（20-50字）",
  "priority": "优先级（high/medium/low）",
  "confidence_score": 置信度（0-100，整数）
}}

请直接返回JSON，不要其他说明:"""

        messages = [
            {"role": "user", "content": prompt}
        ]

        # 调用LLM
        response = self._call_llm(messages, temperature=0.5, max_tokens=1000)

        # 解析响应
        try:
            result = json.loads(response.strip())
        except json.JSONDecodeError:
            # 如果解析失败，返回默认结构
            result = {
                "demand_title": f"{main_theme} - 小组{cluster_id_B}",
                "demand_description": "需求卡片生成失败",
                "user_intent": "",
                "pain_points": [],
                "target_audience": "",
                "priority": "medium",
                "confidence_score": 50
            }

        logger.info(f"生成需求卡片: 大组{cluster_id_A} - 小组{cluster_id_B}: {result['demand_title']}")

        return result

    def batch_classify_tokens(self,
                             tokens: List[str],
                             batch_size: int = 50) -> List[Dict]:
        """
        批量分类tokens的类型

        Args:
            tokens: token文本列表
            batch_size: 批次大小

        Returns:
            分类结果列表，每个元素包含 {'token': ..., 'token_type': ..., 'confidence': ...}
        """
        logger.info(f"批量分类 {len(tokens)} 个tokens (batch_size={batch_size})...")

        all_results = []

        # 分批处理
        for i in range(0, len(tokens), batch_size):
            batch = tokens[i:i + batch_size]

            # 构建prompt
            tokens_str = "\n".join([f"{idx+1}. {token}" for idx, token in enumerate(batch)])

            prompt = f"""你是一个NLP专家，负责将搜索关键词中的token分类。

【Token分类标准】
- intent: 意图词（如 "best", "top", "how to", "cheap", "free"）
- action: 动作词（如 "download", "buy", "make", "create", "install"）
- object: 对象词（如 "shoes", "phone", "tutorial", "recipe", "software"）
- other: 其他（数字、品牌名、地名等）

【待分类Tokens】（共{len(batch)}个）
{tokens_str}

【要求】
1. 为每个token判断其类型（intent/action/object/other）
2. 返回JSON数组格式
3. 每个元素格式: {{"token": "...", "token_type": "...", "confidence": "high|medium|low"}}

请直接返回JSON数组，不要其他说明:"""

            messages = [{"role": "user", "content": prompt}]

            try:
                # 调用LLM
                response = self._call_llm(messages, temperature=0.3)

                # 解析响应
                # 尝试提取JSON数组
                json_match = re.search(r'\[.*\]', response, re.DOTALL)
                if json_match:
                    results = json.loads(json_match.group())
                else:
                    results = json.loads(response.strip())

                # 验证结果
                for result in results:
                    if 'token' in result and 'token_type' in result:
                        all_results.append(result)

                logger.info(f"批次 {i//batch_size + 1}: 分类了 {len(results)} 个tokens")

            except Exception as e:
                logger.error(f"批次 {i//batch_size + 1} 失败: {str(e)}")
                # 对失败的token使用默认分类
                for token in batch:
                    all_results.append({
                        'token': token,
                        'token_type': 'other',
                        'confidence': 'low'
                    })

        logger.info(f"完成分类: {len(all_results)} 个tokens")

        return all_results

    def batch_translate_seed_words(self,
                                   seed_words: List[str],
                                   batch_size: int = 50) -> Dict[str, str]:
        """
        批量翻译词根（seed_words）
        使用AI进行更准确、更符合SEO语境的翻译

        Args:
            seed_words: 词根列表
            batch_size: 批次大小

        Returns:
            翻译结果字典 {word: translation}
        """
        logger.info(f"批量翻译 {len(seed_words)} 个词根 (batch_size={batch_size})...")

        all_translations = {}

        # 分批处理
        for i in range(0, len(seed_words), batch_size):
            batch = seed_words[i:i + batch_size]

            # 构建prompt
            words_str = "\n".join([f"{idx+1}. {word}" for idx, word in enumerate(batch)])

            prompt = f"""你是一个专业的翻译专家，专门翻译英文SEO关键词和搜索词根。

【翻译原则】
1. 提供精准、简洁的中文翻译（2-4个字为佳）
2. 考虑SEO和需求挖掘的语境
3. 保持词根的核心含义
4. 避免重复翻译（相同翻译应对应不同含义的词）
5. 区分近义词的细微差别

【示例】
- best → 最佳
- top → 顶级
- cheap → 便宜
- affordable → 实惠
- free → 免费
- download → 下载
- buy → 购买
- create → 创建
- shoes → 鞋子
- tutorial → 教程

【待翻译词根】（共{len(batch)}个）
{words_str}

【要求】
1. 为每个词根提供准确的中文翻译
2. 返回JSON对象格式
3. 格式: {{"word1": "翻译1", "word2": "翻译2", ...}}

请直接返回JSON对象，不要其他说明:"""

            messages = [{"role": "user", "content": prompt}]

            try:
                # 调用LLM
                response = self._call_llm(messages, temperature=0.3)

                # 解析响应
                # 尝试提取JSON对象
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    translations = json.loads(json_match.group())
                else:
                    translations = json.loads(response.strip())

                # 验证并添加结果
                for word, trans in translations.items():
                    if word in batch:  # 确保是本批次的词
                        all_translations[word] = trans

                logger.info(f"批次 {i//batch_size + 1}: 翻译了 {len(translations)} 个词根")

            except Exception as e:
                logger.error(f"批次 {i//batch_size + 1} 翻译失败: {str(e)}")
                # 对失败的词使用默认翻译
                for word in batch:
                    if word not in all_translations:
                        all_translations[word] = f"[{word}]"  # 标记为未翻译

        logger.info(f"完成翻译: {len(all_translations)} 个词根")

        return all_translations


def test_llm_client():
    """测试LLM客户端"""
    print("\n" + "="*70)
    print("测试LLM客户端")
    print("="*70)

    # 测试示例短语
    example_phrases = [
        "best running shoes for women",
        "top rated running shoes",
        "comfortable running shoes",
        "affordable running shoes",
        "durable running shoes",
    ]

    try:
        # 初始化客户端
        llm = LLMClient()

        # 测试生成主题
        print("\n【测试1】生成聚类主题...")
        result = llm.generate_cluster_theme(
            example_phrases=example_phrases,
            cluster_size=100,
            cluster_id=1
        )
        print(f"  主题: {result['theme']}")
        print(f"  置信度: {result['confidence']}")

        print("\n✅ LLM客户端测试通过！")

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_llm_client()
