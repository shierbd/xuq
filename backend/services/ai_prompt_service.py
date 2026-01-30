"""
[AI1.4] AI提示词管理服务
管理AI提示词模板，支持版本控制和变量替换
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from backend.models.ai_config import AIPrompt, AIScenario
import json


class AIPromptService:
    """AI提示词管理服务"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== CRUD操作 ====================

    def create_prompt(
        self,
        scenario_id: int,
        prompt_name: str,
        prompt_template: str,
        variables: Optional[List[str]] = None,
        version: int = 1,
        is_active: bool = True
    ) -> AIPrompt:
        """
        创建提示词模板

        Args:
            scenario_id: 场景ID
            prompt_name: 提示词名称
            prompt_template: 提示词模板
            variables: 变量列表
            version: 版本号
            is_active: 是否激活

        Returns:
            创建的提示词对象
        """
        # 验证场景存在
        scenario = self.db.query(AIScenario).filter(
            AIScenario.scenario_id == scenario_id
        ).first()
        if not scenario:
            raise ValueError(f"场景 ID {scenario_id} 不存在")

        # 如果设置为激活，将同场景的其他提示词设为非激活
        if is_active:
            self.db.query(AIPrompt).filter(
                AIPrompt.scenario_id == scenario_id
            ).update({"is_active": False})

        # 转换变量列表为JSON字符串
        variables_json = None
        if variables:
            variables_json = json.dumps(variables, ensure_ascii=False)

        # 创建提示词
        prompt = AIPrompt(
            scenario_id=scenario_id,
            prompt_name=prompt_name,
            prompt_template=prompt_template,
            version=version,
            variables=variables_json,
            is_active=is_active
        )

        self.db.add(prompt)
        self.db.commit()
        self.db.refresh(prompt)

        return prompt

    def get_prompt(self, prompt_id: int) -> Optional[AIPrompt]:
        """获取单个提示词"""
        return self.db.query(AIPrompt).filter(
            AIPrompt.prompt_id == prompt_id
        ).first()

    def get_active_prompt_by_scenario(self, scenario_id: int) -> Optional[AIPrompt]:
        """
        获取场景的激活提示词

        Args:
            scenario_id: 场景ID

        Returns:
            激活的提示词对象
        """
        return self.db.query(AIPrompt).filter(
            and_(
                AIPrompt.scenario_id == scenario_id,
                AIPrompt.is_active == True
            )
        ).first()

    def list_prompts_by_scenario(
        self,
        scenario_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[AIPrompt]:
        """
        获取场景的所有提示词

        Args:
            scenario_id: 场景ID
            skip: 跳过数量
            limit: 返回数量

        Returns:
            提示词列表
        """
        return self.db.query(AIPrompt).filter(
            AIPrompt.scenario_id == scenario_id
        ).order_by(AIPrompt.version.desc()).offset(skip).limit(limit).all()

    def list_all_prompts(
        self,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AIPrompt]:
        """
        获取所有提示词列表

        Args:
            is_active: 筛选激活状态
            skip: 跳过数量
            limit: 返回数量

        Returns:
            提示词列表
        """
        query = self.db.query(AIPrompt)

        if is_active is not None:
            query = query.filter(AIPrompt.is_active == is_active)

        return query.order_by(AIPrompt.created_time.desc()).offset(skip).limit(limit).all()

    def update_prompt(
        self,
        prompt_id: int,
        **kwargs
    ) -> Optional[AIPrompt]:
        """
        更新提示词信息

        Args:
            prompt_id: 提示词ID
            **kwargs: 要更新的字段

        Returns:
            更新后的提示词对象
        """
        prompt = self.get_prompt(prompt_id)
        if not prompt:
            return None

        # 如果更新为激活状态，将同场景的其他提示词设为非激活
        if 'is_active' in kwargs and kwargs['is_active']:
            self.db.query(AIPrompt).filter(
                and_(
                    AIPrompt.scenario_id == prompt.scenario_id,
                    AIPrompt.prompt_id != prompt_id
                )
            ).update({"is_active": False})

        # 处理变量列表
        if 'variables' in kwargs and kwargs['variables']:
            if isinstance(kwargs['variables'], list):
                kwargs['variables'] = json.dumps(kwargs['variables'], ensure_ascii=False)

        # 更新字段
        for key, value in kwargs.items():
            if hasattr(prompt, key):
                setattr(prompt, key, value)

        self.db.commit()
        self.db.refresh(prompt)

        return prompt

    def delete_prompt(self, prompt_id: int) -> bool:
        """
        删除提示词

        Args:
            prompt_id: 提示词ID

        Returns:
            是否删除成功
        """
        prompt = self.get_prompt(prompt_id)
        if not prompt:
            return False

        self.db.delete(prompt)
        self.db.commit()

        return True

    # ==================== 特殊功能 ====================

    def activate_prompt(self, prompt_id: int) -> Optional[AIPrompt]:
        """
        激活提示词（同时将同场景的其他提示词设为非激活）

        Args:
            prompt_id: 提示词ID

        Returns:
            激活的提示词对象
        """
        prompt = self.get_prompt(prompt_id)
        if not prompt:
            return None

        # 将同场景的其他提示词设为非激活
        self.db.query(AIPrompt).filter(
            and_(
                AIPrompt.scenario_id == prompt.scenario_id,
                AIPrompt.prompt_id != prompt_id
            )
        ).update({"is_active": False})

        # 激活当前提示词
        prompt.is_active = True
        self.db.commit()
        self.db.refresh(prompt)

        return prompt

    def create_new_version(
        self,
        prompt_id: int,
        prompt_template: str,
        variables: Optional[List[str]] = None
    ) -> AIPrompt:
        """
        创建提示词的新版本

        Args:
            prompt_id: 原提示词ID
            prompt_template: 新的提示词模板
            variables: 新的变量列表

        Returns:
            新版本的提示词对象
        """
        old_prompt = self.get_prompt(prompt_id)
        if not old_prompt:
            raise ValueError(f"提示词 ID {prompt_id} 不存在")

        # 获取同场景的最大版本号
        max_version = self.db.query(AIPrompt).filter(
            AIPrompt.scenario_id == old_prompt.scenario_id
        ).order_by(AIPrompt.version.desc()).first()

        new_version = (max_version.version + 1) if max_version else 1

        # 创建新版本
        return self.create_prompt(
            scenario_id=old_prompt.scenario_id,
            prompt_name=old_prompt.prompt_name,
            prompt_template=prompt_template,
            variables=variables,
            version=new_version,
            is_active=True  # 新版本默认激活
        )

    def get_prompt_with_scenario(self, prompt_id: int) -> Optional[Dict[str, Any]]:
        """
        获取提示词及其关联的场景信息

        Args:
            prompt_id: 提示词ID

        Returns:
            包含提示词和场景信息的字典
        """
        prompt = self.get_prompt(prompt_id)
        if not prompt:
            return None

        # 获取场景信息
        scenario = self.db.query(AIScenario).filter(
            AIScenario.scenario_id == prompt.scenario_id
        ).first()

        # 解析变量列表
        variables = None
        if prompt.variables:
            try:
                variables = json.loads(prompt.variables)
            except:
                variables = []

        return {
            "prompt_id": prompt.prompt_id,
            "prompt_name": prompt.prompt_name,
            "prompt_template": prompt.prompt_template,
            "version": prompt.version,
            "variables": variables,
            "is_active": prompt.is_active,
            "created_time": prompt.created_time.isoformat(),
            "scenario": {
                "scenario_id": scenario.scenario_id,
                "scenario_name": scenario.scenario_name,
                "scenario_desc": scenario.scenario_desc
            } if scenario else None
        }

    def render_prompt(
        self,
        prompt_id: int,
        variables_values: Dict[str, Any]
    ) -> str:
        """
        渲染提示词模板（替换变量）

        Args:
            prompt_id: 提示词ID
            variables_values: 变量值字典

        Returns:
            渲染后的提示词
        """
        prompt = self.get_prompt(prompt_id)
        if not prompt:
            raise ValueError(f"提示词 ID {prompt_id} 不存在")

        # 简单的变量替换（使用 {variable_name} 格式）
        rendered = prompt.prompt_template
        for key, value in variables_values.items():
            rendered = rendered.replace(f"{{{key}}}", str(value))

        return rendered

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取提示词统计信息

        Returns:
            统计信息字典
        """
        total = self.db.query(AIPrompt).count()
        active = self.db.query(AIPrompt).filter(
            AIPrompt.is_active == True
        ).count()
        inactive = total - active

        # 按场景统计
        scenarios_with_prompts = self.db.query(
            AIPrompt.scenario_id
        ).distinct().count()

        return {
            "total_prompts": total,
            "active_prompts": active,
            "inactive_prompts": inactive,
            "scenarios_with_prompts": scenarios_with_prompts
        }
