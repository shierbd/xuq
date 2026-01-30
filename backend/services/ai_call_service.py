"""
[AI1.3扩展] 统一AI调用服务
提供统一的AI调用接口，支持场景化配置和回退机制
"""
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from datetime import datetime
import json
import httpx
from backend.services.ai_scenario_service import AIScenarioService
from backend.services.ai_model_service import AIModelService
from backend.services.ai_provider_service import AIProviderService


class AICallService:
    """统一AI调用服务"""

    def __init__(self, db: Session):
        self.db = db
        self.scenario_service = AIScenarioService(db)
        self.model_service = AIModelService(db)
        self.provider_service = AIProviderService(db)

    async def call_by_scenario(
        self,
        scenario_name: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        根据场景名称调用AI

        Args:
            scenario_name: 场景名称
            prompt: 用户提示词
            system_prompt: 系统提示词（可选）
            temperature: 温度参数（可选，覆盖模型默认值）
            max_tokens: 最大token数（可选，覆盖模型默认值）
            **kwargs: 其他参数

        Returns:
            调用结果字典
        """
        # 1. 获取场景配置
        scenario = self.scenario_service.get_scenario_by_name(scenario_name)
        if not scenario:
            raise ValueError(f"场景 '{scenario_name}' 不存在")

        if not scenario.is_enabled:
            raise ValueError(f"场景 '{scenario_name}' 已禁用")

        # 2. 获取场景及模型信息
        scenario_data = self.scenario_service.get_scenario_with_models(scenario.scenario_id)

        # 3. 尝试调用主模型
        primary_model = scenario_data["primary_model"]
        try:
            result = await self._call_model(
                model_id=primary_model["model_id"],
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            # 记录成功调用
            self._log_call(
                scenario_id=scenario.scenario_id,
                model_id=primary_model["model_id"],
                prompt=prompt,
                response=result["content"],
                success=True,
                is_fallback=False,
                error_message=None
            )

            return {
                "success": True,
                "content": result["content"],
                "model_used": primary_model["model_name"],
                "is_fallback": False,
                "usage": result.get("usage", {}),
                "scenario_name": scenario_name
            }

        except Exception as primary_error:
            # 4. 主模型失败，尝试回退模型
            fallback_model = scenario_data.get("fallback_model")

            if not fallback_model:
                # 没有回退模型，记录失败并抛出异常
                self._log_call(
                    scenario_id=scenario.scenario_id,
                    model_id=primary_model["model_id"],
                    prompt=prompt,
                    response=None,
                    success=False,
                    is_fallback=False,
                    error_message=str(primary_error)
                )
                raise Exception(f"主模型调用失败且无回退模型: {str(primary_error)}")

            # 尝试调用回退模型
            try:
                result = await self._call_model(
                    model_id=fallback_model["model_id"],
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )

                # 记录回退模型成功调用
                self._log_call(
                    scenario_id=scenario.scenario_id,
                    model_id=fallback_model["model_id"],
                    prompt=prompt,
                    response=result["content"],
                    success=True,
                    is_fallback=True,
                    error_message=f"主模型失败: {str(primary_error)}"
                )

                return {
                    "success": True,
                    "content": result["content"],
                    "model_used": fallback_model["model_name"],
                    "is_fallback": True,
                    "primary_error": str(primary_error),
                    "usage": result.get("usage", {}),
                    "scenario_name": scenario_name
                }

            except Exception as fallback_error:
                # 回退模型也失败，记录失败
                self._log_call(
                    scenario_id=scenario.scenario_id,
                    model_id=fallback_model["model_id"],
                    prompt=prompt,
                    response=None,
                    success=False,
                    is_fallback=True,
                    error_message=f"主模型失败: {str(primary_error)}, 回退模型失败: {str(fallback_error)}"
                )
                raise Exception(
                    f"主模型和回退模型均失败 - "
                    f"主模型: {str(primary_error)}, "
                    f"回退模型: {str(fallback_error)}"
                )

    async def _call_model(
        self,
        model_id: int,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        调用具体的AI模型

        Args:
            model_id: 模型ID
            prompt: 用户提示词
            system_prompt: 系统提示词
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数

        Returns:
            调用结果
        """
        # 获取模型及提供商信息
        model_data = self.model_service.get_model_with_provider(model_id)
        if not model_data:
            raise ValueError(f"模型 ID {model_id} 不存在")

        model = model_data["model"]
        provider = model_data["provider"]

        # 使用模型默认值或传入的参数
        final_temperature = temperature if temperature is not None else model["temperature"]
        final_max_tokens = max_tokens if max_tokens is not None else model["max_tokens"]

        # 根据提供商类型调用不同的API
        provider_name = provider["provider_name"].lower()

        if "claude" in provider_name:
            return await self._call_claude(
                provider=provider,
                model_name=model["model_name"],
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=final_temperature,
                max_tokens=final_max_tokens,
                **kwargs
            )
        elif "deepseek" in provider_name:
            return await self._call_deepseek(
                provider=provider,
                model_name=model["model_name"],
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=final_temperature,
                max_tokens=final_max_tokens,
                **kwargs
            )
        else:
            raise ValueError(f"不支持的提供商类型: {provider_name}")

    async def _call_claude(
        self,
        provider: Dict[str, Any],
        model_name: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> Dict[str, Any]:
        """调用Claude API"""
        headers = {
            "x-api-key": provider["api_key"],
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        data = {
            "model": model_name,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

        if system_prompt:
            data["system"] = system_prompt

        async with httpx.AsyncClient(timeout=provider["timeout"]) as client:
            response = await client.post(
                f"{provider['api_endpoint']}/v1/messages",
                headers=headers,
                json=data
            )

            if response.status_code != 200:
                raise Exception(f"Claude API调用失败: {response.status_code} - {response.text}")

            result = response.json()
            return {
                "content": result["content"][0]["text"],
                "usage": {
                    "input_tokens": result["usage"]["input_tokens"],
                    "output_tokens": result["usage"]["output_tokens"]
                }
            }

    async def _call_deepseek(
        self,
        provider: Dict[str, Any],
        model_name: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> Dict[str, Any]:
        """调用DeepSeek API"""
        headers = {
            "Authorization": f"Bearer {provider['api_key']}",
            "Content-Type": "application/json"
        }

        messages = []
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        messages.append({
            "role": "user",
            "content": prompt
        })

        data = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        async with httpx.AsyncClient(timeout=provider["timeout"]) as client:
            response = await client.post(
                f"{provider['api_endpoint']}/v1/chat/completions",
                headers=headers,
                json=data
            )

            if response.status_code != 200:
                raise Exception(f"DeepSeek API调用失败: {response.status_code} - {response.text}")

            result = response.json()
            return {
                "content": result["choices"][0]["message"]["content"],
                "usage": {
                    "input_tokens": result["usage"]["prompt_tokens"],
                    "output_tokens": result["usage"]["completion_tokens"]
                }
            }

    def _log_call(
        self,
        scenario_id: int,
        model_id: int,
        prompt: str,
        response: Optional[str],
        success: bool,
        is_fallback: bool,
        error_message: Optional[str]
    ) -> None:
        """
        记录AI调用日志

        Args:
            scenario_id: 场景ID
            model_id: 模型ID
            prompt: 提示词
            response: 响应内容
            success: 是否成功
            is_fallback: 是否使用回退模型
            error_message: 错误信息
        """
        # TODO: 实现日志记录到数据库
        # 这里先简单打印日志，后续可以扩展到数据库记录
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "scenario_id": scenario_id,
            "model_id": model_id,
            "prompt_length": len(prompt),
            "response_length": len(response) if response else 0,
            "success": success,
            "is_fallback": is_fallback,
            "error_message": error_message
        }
        print(f"[AI调用日志] {json.dumps(log_entry, ensure_ascii=False)}")
