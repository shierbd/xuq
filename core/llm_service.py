"""
LLM服务包装器
简化LLM调用接口
"""
from typing import List, Dict
from ai.client import LLMClient


class LLMService:
    """LLM服务简化包装器"""

    def __init__(self, provider: str = None):
        """
        初始化LLM服务

        Args:
            provider: LLM提供商（默认使用配置文件设置）
        """
        self.client = LLMClient(provider=provider)

    def generate(self, prompt: str, temperature: float = None, max_tokens: int = None) -> str:
        """
        生成文本

        Args:
            prompt: 提示文本
            temperature: 温度参数
            max_tokens: 最大token数

        Returns:
            生成的文本
        """
        messages = [{"role": "user", "content": prompt}]
        return self.client._call_llm(messages, temperature=temperature, max_tokens=max_tokens)

    def generate_with_system(self, system_prompt: str, user_prompt: str,
                            temperature: float = None, max_tokens: int = None) -> str:
        """
        使用系统提示生成文本

        Args:
            system_prompt: 系统提示
            user_prompt: 用户提示
            temperature: 温度参数
            max_tokens: 最大token数

        Returns:
            生成的文本
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        return self.client._call_llm(messages, temperature=temperature, max_tokens=max_tokens)
