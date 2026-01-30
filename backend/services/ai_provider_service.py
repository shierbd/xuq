"""
[AI1.1] AI提供商管理服务
提供AI提供商的CRUD操作和连接测试功能
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from backend.models.ai_config import AIProvider
import requests
from datetime import datetime


class AIProviderService:
    """AI提供商管理服务"""

    def __init__(self, db: Session):
        self.db = db

    def create_provider(
        self,
        provider_name: str,
        api_key: str,
        api_endpoint: str,
        timeout: int = 30,
        max_retries: int = 3,
        is_enabled: bool = True
    ) -> AIProvider:
        """
        创建AI提供商

        Args:
            provider_name: 提供商名称
            api_key: API密钥
            api_endpoint: API端点
            timeout: 超时时间（秒）
            max_retries: 最大重试次数
            is_enabled: 是否启用

        Returns:
            创建的提供商对象
        """
        # 检查是否已存在
        existing = self.db.query(AIProvider).filter(
            AIProvider.provider_name == provider_name
        ).first()

        if existing:
            raise ValueError(f"提供商 '{provider_name}' 已存在")

        provider = AIProvider(
            provider_name=provider_name,
            api_key=api_key,
            api_endpoint=api_endpoint,
            timeout=timeout,
            max_retries=max_retries,
            is_enabled=is_enabled
        )

        self.db.add(provider)
        self.db.commit()
        self.db.refresh(provider)

        return provider

    def get_provider(self, provider_id: int) -> Optional[AIProvider]:
        """
        获取单个提供商

        Args:
            provider_id: 提供商ID

        Returns:
            提供商对象或None
        """
        return self.db.query(AIProvider).filter(
            AIProvider.provider_id == provider_id
        ).first()

    def get_provider_by_name(self, provider_name: str) -> Optional[AIProvider]:
        """
        根据名称获取提供商

        Args:
            provider_name: 提供商名称

        Returns:
            提供商对象或None
        """
        return self.db.query(AIProvider).filter(
            AIProvider.provider_name == provider_name
        ).first()

    def list_providers(
        self,
        is_enabled: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AIProvider]:
        """
        获取提供商列表

        Args:
            is_enabled: 是否启用（None表示全部）
            skip: 跳过数量
            limit: 返回数量

        Returns:
            提供商列表
        """
        query = self.db.query(AIProvider)

        if is_enabled is not None:
            query = query.filter(AIProvider.is_enabled == is_enabled)

        return query.offset(skip).limit(limit).all()

    def update_provider(
        self,
        provider_id: int,
        **kwargs
    ) -> Optional[AIProvider]:
        """
        更新提供商信息

        Args:
            provider_id: 提供商ID
            **kwargs: 要更新的字段

        Returns:
            更新后的提供商对象或None
        """
        provider = self.get_provider(provider_id)
        if not provider:
            return None

        # 更新字段
        for key, value in kwargs.items():
            if hasattr(provider, key):
                setattr(provider, key, value)

        provider.updated_time = datetime.now()
        self.db.commit()
        self.db.refresh(provider)

        return provider

    def delete_provider(self, provider_id: int) -> bool:
        """
        删除提供商

        Args:
            provider_id: 提供商ID

        Returns:
            是否删除成功
        """
        provider = self.get_provider(provider_id)
        if not provider:
            return False

        self.db.delete(provider)
        self.db.commit()

        return True

    def toggle_provider(self, provider_id: int) -> Optional[AIProvider]:
        """
        切换提供商启用状态

        Args:
            provider_id: 提供商ID

        Returns:
            更新后的提供商对象或None
        """
        provider = self.get_provider(provider_id)
        if not provider:
            return None

        provider.is_enabled = not provider.is_enabled
        provider.updated_time = datetime.now()
        self.db.commit()
        self.db.refresh(provider)

        return provider

    def test_connection(self, provider_id: int) -> Dict[str, Any]:
        """
        测试提供商连接

        Args:
            provider_id: 提供商ID

        Returns:
            测试结果字典
        """
        provider = self.get_provider(provider_id)
        if not provider:
            return {
                "success": False,
                "message": "提供商不存在"
            }

        try:
            # 根据不同提供商进行不同的测试
            if "claude" in provider.provider_name.lower():
                return self._test_claude_connection(provider)
            elif "deepseek" in provider.provider_name.lower():
                return self._test_deepseek_connection(provider)
            else:
                return {
                    "success": False,
                    "message": f"不支持的提供商类型: {provider.provider_name}"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"连接测试失败: {str(e)}"
            }

    def _test_claude_connection(self, provider: AIProvider) -> Dict[str, Any]:
        """测试Claude API连接"""
        try:
            headers = {
                "x-api-key": provider.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }

            # 发送一个简单的测试请求
            response = requests.post(
                f"{provider.api_endpoint}/messages",
                headers=headers,
                json={
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 10,
                    "messages": [{"role": "user", "content": "test"}]
                },
                timeout=provider.timeout
            )

            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "连接成功",
                    "status_code": response.status_code
                }
            else:
                return {
                    "success": False,
                    "message": f"连接失败: {response.status_code}",
                    "status_code": response.status_code,
                    "error": response.text
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"连接异常: {str(e)}"
            }

    def _test_deepseek_connection(self, provider: AIProvider) -> Dict[str, Any]:
        """测试DeepSeek API连接"""
        try:
            headers = {
                "Authorization": f"Bearer {provider.api_key}",
                "Content-Type": "application/json"
            }

            # 发送一个简单的测试请求
            response = requests.post(
                f"{provider.api_endpoint}/chat/completions",
                headers=headers,
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 10
                },
                timeout=provider.timeout
            )

            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "连接成功",
                    "status_code": response.status_code
                }
            else:
                return {
                    "success": False,
                    "message": f"连接失败: {response.status_code}",
                    "status_code": response.status_code,
                    "error": response.text
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"连接异常: {str(e)}"
            }

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取提供商统计信息

        Returns:
            统计信息字典
        """
        total = self.db.query(AIProvider).count()
        enabled = self.db.query(AIProvider).filter(
            AIProvider.is_enabled == True
        ).count()
        disabled = total - enabled

        return {
            "total_providers": total,
            "enabled_providers": enabled,
            "disabled_providers": disabled
        }
