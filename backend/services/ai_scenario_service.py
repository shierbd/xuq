"""
[AI1.3] AI场景管理服务
管理不同的AI使用场景，为每个场景配置最佳模型
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from backend.models.ai_config import AIScenario, AIModel
import json


class AIScenarioService:
    """AI场景管理服务"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== CRUD操作 ====================

    def create_scenario(
        self,
        scenario_name: str,
        primary_model_id: int,
        scenario_desc: Optional[str] = None,
        fallback_model_id: Optional[int] = None,
        custom_params: Optional[Dict[str, Any]] = None,
        is_enabled: bool = True
    ) -> AIScenario:
        """
        创建AI场景

        Args:
            scenario_name: 场景名称
            primary_model_id: 主模型ID
            scenario_desc: 场景描述
            fallback_model_id: 回退模型ID
            custom_params: 自定义参数
            is_enabled: 是否启用

        Returns:
            创建的场景对象
        """
        # 检查场景名称是否已存在
        existing = self.db.query(AIScenario).filter(
            AIScenario.scenario_name == scenario_name
        ).first()
        if existing:
            raise ValueError(f"场景 '{scenario_name}' 已存在")

        # 验证主模型存在
        primary_model = self.db.query(AIModel).filter(
            AIModel.model_id == primary_model_id
        ).first()
        if not primary_model:
            raise ValueError(f"主模型 ID {primary_model_id} 不存在")

        # 验证回退模型存在（如果提供）
        if fallback_model_id:
            fallback_model = self.db.query(AIModel).filter(
                AIModel.model_id == fallback_model_id
            ).first()
            if not fallback_model:
                raise ValueError(f"回退模型 ID {fallback_model_id} 不存在")

        # 转换自定义参数为JSON字符串
        custom_params_json = None
        if custom_params:
            custom_params_json = json.dumps(custom_params, ensure_ascii=False)

        # 创建场景
        scenario = AIScenario(
            scenario_name=scenario_name,
            scenario_desc=scenario_desc,
            primary_model_id=primary_model_id,
            fallback_model_id=fallback_model_id,
            custom_params=custom_params_json,
            is_enabled=is_enabled
        )

        self.db.add(scenario)
        self.db.commit()
        self.db.refresh(scenario)

        return scenario

    def get_scenario(self, scenario_id: int) -> Optional[AIScenario]:
        """获取单个场景"""
        return self.db.query(AIScenario).filter(
            AIScenario.scenario_id == scenario_id
        ).first()

    def get_scenario_by_name(self, scenario_name: str) -> Optional[AIScenario]:
        """根据名称获取场景"""
        return self.db.query(AIScenario).filter(
            AIScenario.scenario_name == scenario_name
        ).first()

    def list_scenarios(
        self,
        is_enabled: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AIScenario]:
        """
        获取场景列表

        Args:
            is_enabled: 筛选启用状态
            skip: 跳过数量
            limit: 返回数量

        Returns:
            场景列表
        """
        query = self.db.query(AIScenario)

        if is_enabled is not None:
            query = query.filter(AIScenario.is_enabled == is_enabled)

        return query.offset(skip).limit(limit).all()

    def update_scenario(
        self,
        scenario_id: int,
        **kwargs
    ) -> Optional[AIScenario]:
        """
        更新场景信息

        Args:
            scenario_id: 场景ID
            **kwargs: 要更新的字段

        Returns:
            更新后的场景对象
        """
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            return None

        # 如果更新场景名称，检查是否重复
        if 'scenario_name' in kwargs:
            existing = self.db.query(AIScenario).filter(
                and_(
                    AIScenario.scenario_name == kwargs['scenario_name'],
                    AIScenario.scenario_id != scenario_id
                )
            ).first()
            if existing:
                raise ValueError(f"场景名称 '{kwargs['scenario_name']}' 已存在")

        # 如果更新主模型，验证存在
        if 'primary_model_id' in kwargs:
            model = self.db.query(AIModel).filter(
                AIModel.model_id == kwargs['primary_model_id']
            ).first()
            if not model:
                raise ValueError(f"主模型 ID {kwargs['primary_model_id']} 不存在")

        # 如果更新回退模型，验证存在
        if 'fallback_model_id' in kwargs and kwargs['fallback_model_id']:
            model = self.db.query(AIModel).filter(
                AIModel.model_id == kwargs['fallback_model_id']
            ).first()
            if not model:
                raise ValueError(f"回退模型 ID {kwargs['fallback_model_id']} 不存在")

        # 处理自定义参数
        if 'custom_params' in kwargs and kwargs['custom_params']:
            if isinstance(kwargs['custom_params'], dict):
                kwargs['custom_params'] = json.dumps(kwargs['custom_params'], ensure_ascii=False)

        # 更新字段
        for key, value in kwargs.items():
            if hasattr(scenario, key):
                setattr(scenario, key, value)

        self.db.commit()
        self.db.refresh(scenario)

        return scenario

    def delete_scenario(self, scenario_id: int) -> bool:
        """
        删除场景

        Args:
            scenario_id: 场景ID

        Returns:
            是否删除成功
        """
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            return False

        self.db.delete(scenario)
        self.db.commit()

        return True

    # ==================== 特殊功能 ====================

    def toggle_scenario(self, scenario_id: int) -> Optional[AIScenario]:
        """
        切换场景启用状态

        Args:
            scenario_id: 场景ID

        Returns:
            更新后的场景对象
        """
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            return None

        scenario.is_enabled = not scenario.is_enabled
        self.db.commit()
        self.db.refresh(scenario)

        return scenario

    def get_scenario_with_models(self, scenario_id: int) -> Optional[Dict[str, Any]]:
        """
        获取场景及其关联的模型信息

        Args:
            scenario_id: 场景ID

        Returns:
            包含场景和模型信息的字典
        """
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            return None

        # 获取主模型信息
        primary_model = self.db.query(AIModel).filter(
            AIModel.model_id == scenario.primary_model_id
        ).first()

        # 获取回退模型信息
        fallback_model = None
        if scenario.fallback_model_id:
            fallback_model = self.db.query(AIModel).filter(
                AIModel.model_id == scenario.fallback_model_id
            ).first()

        # 解析自定义参数
        custom_params = None
        if scenario.custom_params:
            try:
                custom_params = json.loads(scenario.custom_params)
            except:
                custom_params = {}

        return {
            "scenario_id": scenario.scenario_id,
            "scenario_name": scenario.scenario_name,
            "scenario_desc": scenario.scenario_desc,
            "is_enabled": scenario.is_enabled,
            "created_time": scenario.created_time.isoformat(),
            "primary_model": {
                "model_id": primary_model.model_id,
                "model_name": primary_model.model_name,
                "provider_id": primary_model.provider_id
            } if primary_model else None,
            "fallback_model": {
                "model_id": fallback_model.model_id,
                "model_name": fallback_model.model_name,
                "provider_id": fallback_model.provider_id
            } if fallback_model else None,
            "custom_params": custom_params
        }

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取场景统计信息

        Returns:
            统计信息字典
        """
        total = self.db.query(AIScenario).count()
        enabled = self.db.query(AIScenario).filter(
            AIScenario.is_enabled == True
        ).count()
        disabled = total - enabled

        return {
            "total_scenarios": total,
            "enabled_scenarios": enabled,
            "disabled_scenarios": disabled
        }
