"""
[AI1.2] AI模型管理服务
提供AI模型的CRUD操作和配置管理功能
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from backend.models.ai_config import AIModel, AIProvider
from datetime import datetime
import json


class AIModelService:
    """AI模型管理服务"""

    def __init__(self, db: Session):
        self.db = db

    def create_model(
        self,
        provider_id: int,
        model_name: str,
        model_version: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        input_price: Optional[float] = None,
        output_price: Optional[float] = None,
        capabilities: Optional[List[str]] = None,
        is_default: bool = False,
        is_enabled: bool = True
    ) -> AIModel:
        """
        创建AI模型

        Args:
            provider_id: 提供商ID
            model_name: 模型名称
            model_version: 模型版本
            temperature: 温度参数
            max_tokens: 最大token数
            input_price: 输入价格（$/1M tokens）
            output_price: 输出价格（$/1M tokens）
            capabilities: 能力标签列表
            is_default: 是否默认模型
            is_enabled: 是否启用

        Returns:
            创建的模型对象
        """
        # 检查提供商是否存在
        provider = self.db.query(AIProvider).filter(
            AIProvider.provider_id == provider_id
        ).first()

        if not provider:
            raise ValueError(f"提供商ID {provider_id} 不存在")

        # 如果设置为默认模型，取消其他默认模型
        if is_default:
            self.db.query(AIModel).filter(
                and_(
                    AIModel.provider_id == provider_id,
                    AIModel.is_default == True
                )
            ).update({"is_default": False}, synchronize_session=False)

        # 转换capabilities为JSON字符串
        capabilities_json = json.dumps(capabilities) if capabilities else None

        model = AIModel(
            provider_id=provider_id,
            model_name=model_name,
            model_version=model_version,
            temperature=temperature,
            max_tokens=max_tokens,
            input_price=input_price,
            output_price=output_price,
            capabilities=capabilities_json,
            is_default=is_default,
            is_enabled=is_enabled
        )

        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)

        return model

    def get_model(self, model_id: int) -> Optional[AIModel]:
        """
        获取单个模型

        Args:
            model_id: 模型ID

        Returns:
            模型对象或None
        """
        return self.db.query(AIModel).filter(
            AIModel.model_id == model_id
        ).first()

    def get_model_by_name(
        self,
        provider_id: int,
        model_name: str
    ) -> Optional[AIModel]:
        """
        根据提供商和名称获取模型

        Args:
            provider_id: 提供商ID
            model_name: 模型名称

        Returns:
            模型对象或None
        """
        return self.db.query(AIModel).filter(
            and_(
                AIModel.provider_id == provider_id,
                AIModel.model_name == model_name
            )
        ).first()

    def list_models(
        self,
        provider_id: Optional[int] = None,
        is_enabled: Optional[bool] = None,
        is_default: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AIModel]:
        """
        获取模型列表

        Args:
            provider_id: 提供商ID（None表示全部）
            is_enabled: 是否启用（None表示全部）
            is_default: 是否默认（None表示全部）
            skip: 跳过数量
            limit: 返回数量

        Returns:
            模型列表
        """
        query = self.db.query(AIModel)

        if provider_id is not None:
            query = query.filter(AIModel.provider_id == provider_id)

        if is_enabled is not None:
            query = query.filter(AIModel.is_enabled == is_enabled)

        if is_default is not None:
            query = query.filter(AIModel.is_default == is_default)

        return query.offset(skip).limit(limit).all()

    def update_model(
        self,
        model_id: int,
        **kwargs
    ) -> Optional[AIModel]:
        """
        更新模型信息

        Args:
            model_id: 模型ID
            **kwargs: 要更新的字段

        Returns:
            更新后的模型对象或None
        """
        model = self.get_model(model_id)
        if not model:
            return None

        # 如果要设置为默认模型，取消同提供商的其他默认模型
        if kwargs.get('is_default') == True:
            self.db.query(AIModel).filter(
                and_(
                    AIModel.provider_id == model.provider_id,
                    AIModel.model_id != model_id,
                    AIModel.is_default == True
                )
            ).update({"is_default": False}, synchronize_session=False)

        # 处理capabilities字段
        if 'capabilities' in kwargs and isinstance(kwargs['capabilities'], list):
            kwargs['capabilities'] = json.dumps(kwargs['capabilities'])

        # 更新字段
        for key, value in kwargs.items():
            if hasattr(model, key):
                setattr(model, key, value)

        self.db.commit()
        self.db.refresh(model)

        return model

    def delete_model(self, model_id: int) -> bool:
        """
        删除模型

        Args:
            model_id: 模型ID

        Returns:
            是否删除成功
        """
        model = self.get_model(model_id)
        if not model:
            return False

        self.db.delete(model)
        self.db.commit()

        return True

    def toggle_model(self, model_id: int) -> Optional[AIModel]:
        """
        切换模型启用状态

        Args:
            model_id: 模型ID

        Returns:
            更新后的模型对象或None
        """
        model = self.get_model(model_id)
        if not model:
            return None

        model.is_enabled = not model.is_enabled
        self.db.commit()
        self.db.refresh(model)

        return model

    def set_default_model(
        self,
        model_id: int
    ) -> Optional[AIModel]:
        """
        设置默认模型

        Args:
            model_id: 模型ID

        Returns:
            更新后的模型对象或None
        """
        model = self.get_model(model_id)
        if not model:
            return None

        # 取消同提供商的其他默认模型
        self.db.query(AIModel).filter(
            and_(
                AIModel.provider_id == model.provider_id,
                AIModel.model_id != model_id,
                AIModel.is_default == True
            )
        ).update({"is_default": False}, synchronize_session=False)

        # 设置为默认
        model.is_default = True
        self.db.commit()
        self.db.refresh(model)

        return model

    def get_default_model(
        self,
        provider_id: int
    ) -> Optional[AIModel]:
        """
        获取提供商的默认模型

        Args:
            provider_id: 提供商ID

        Returns:
            默认模型对象或None
        """
        return self.db.query(AIModel).filter(
            and_(
                AIModel.provider_id == provider_id,
                AIModel.is_default == True,
                AIModel.is_enabled == True
            )
        ).first()

    def calculate_cost(
        self,
        model_id: int,
        input_tokens: int,
        output_tokens: int
    ) -> Optional[float]:
        """
        计算API调用成本

        Args:
            model_id: 模型ID
            input_tokens: 输入token数
            output_tokens: 输出token数

        Returns:
            成本（美元）或None
        """
        model = self.get_model(model_id)
        if not model or not model.input_price or not model.output_price:
            return None

        # 价格单位是 $/1M tokens
        input_cost = (input_tokens / 1_000_000) * model.input_price
        output_cost = (output_tokens / 1_000_000) * model.output_price

        return input_cost + output_cost

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取模型统计信息

        Returns:
            统计信息字典
        """
        total = self.db.query(AIModel).count()
        enabled = self.db.query(AIModel).filter(
            AIModel.is_enabled == True
        ).count()
        disabled = total - enabled

        # 按提供商统计
        by_provider = {}
        providers = self.db.query(AIProvider).all()
        for provider in providers:
            count = self.db.query(AIModel).filter(
                AIModel.provider_id == provider.provider_id
            ).count()
            by_provider[provider.provider_name] = count

        return {
            "total_models": total,
            "enabled_models": enabled,
            "disabled_models": disabled,
            "by_provider": by_provider
        }

    def get_model_with_provider(self, model_id: int) -> Optional[Dict[str, Any]]:
        """
        获取模型及其提供商信息

        Args:
            model_id: 模型ID

        Returns:
            包含模型和提供商信息的字典或None
        """
        model = self.get_model(model_id)
        if not model:
            return None

        provider = self.db.query(AIProvider).filter(
            AIProvider.provider_id == model.provider_id
        ).first()

        # 解析capabilities
        capabilities = None
        if model.capabilities:
            try:
                capabilities = json.loads(model.capabilities)
            except:
                capabilities = []

        return {
            "model_id": model.model_id,
            "model_name": model.model_name,
            "model_version": model.model_version,
            "temperature": model.temperature,
            "max_tokens": model.max_tokens,
            "input_price": model.input_price,
            "output_price": model.output_price,
            "capabilities": capabilities,
            "is_default": model.is_default,
            "is_enabled": model.is_enabled,
            "provider": {
                "provider_id": provider.provider_id,
                "provider_name": provider.provider_name,
                "is_enabled": provider.is_enabled
            } if provider else None
        }
