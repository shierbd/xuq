"""
[AI1.1, AI1.2, AI1.3] AI配置管理模块 - API路由
提供AI提供商、AI模型和使用场景的管理接口
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from backend.database import get_db
from backend.services.ai_provider_service import AIProviderService
from backend.services.ai_model_service import AIModelService
from backend.services.ai_scenario_service import AIScenarioService


router = APIRouter(prefix="/api/ai-config", tags=["AI配置管理"])


# ==================== Pydantic模型 ====================

class AIProviderCreate(BaseModel):
    """创建AI提供商的请求模型"""
    provider_name: str = Field(..., description="提供商名称")
    api_key: str = Field(..., description="API密钥")
    api_endpoint: str = Field(..., description="API端点URL")
    timeout: int = Field(30, description="超时时间（秒）")
    max_retries: int = Field(3, description="最大重试次数")
    is_enabled: bool = Field(True, description="是否启用")


class AIProviderUpdate(BaseModel):
    """更新AI提供商的请求模型"""
    provider_name: Optional[str] = Field(None, description="提供商名称")
    api_key: Optional[str] = Field(None, description="API密钥")
    api_endpoint: Optional[str] = Field(None, description="API端点URL")
    timeout: Optional[int] = Field(None, description="超时时间（秒）")
    max_retries: Optional[int] = Field(None, description="最大重试次数")
    is_enabled: Optional[bool] = Field(None, description="是否启用")


class AIProviderResponse(BaseModel):
    """AI提供商响应模型"""
    provider_id: int
    provider_name: str
    api_endpoint: str
    timeout: int
    max_retries: int
    is_enabled: bool
    created_time: str
    updated_time: str

    class Config:
        from_attributes = True


class AIModelCreate(BaseModel):
    """创建AI模型的请求模型"""
    provider_id: int = Field(..., description="提供商ID")
    model_name: str = Field(..., description="模型名称")
    model_version: Optional[str] = Field(None, description="模型版本")
    temperature: float = Field(0.7, description="温度参数")
    max_tokens: int = Field(4096, description="最大token数")
    input_price: Optional[float] = Field(None, description="输入价格（$/1M tokens）")
    output_price: Optional[float] = Field(None, description="输出价格（$/1M tokens）")
    capabilities: Optional[List[str]] = Field(None, description="能力标签")
    is_default: bool = Field(False, description="是否默认模型")
    is_enabled: bool = Field(True, description="是否启用")


class AIModelUpdate(BaseModel):
    """更新AI模型的请求模型"""
    model_name: Optional[str] = Field(None, description="模型名称")
    model_version: Optional[str] = Field(None, description="模型版本")
    temperature: Optional[float] = Field(None, description="温度参数")
    max_tokens: Optional[int] = Field(None, description="最大token数")
    input_price: Optional[float] = Field(None, description="输入价格（$/1M tokens）")
    output_price: Optional[float] = Field(None, description="输出价格（$/1M tokens）")
    capabilities: Optional[List[str]] = Field(None, description="能力标签")
    is_default: Optional[bool] = Field(None, description="是否默认模型")
    is_enabled: Optional[bool] = Field(None, description="是否启用")


class AIModelResponse(BaseModel):
    """AI模型响应模型"""
    model_id: int
    provider_id: int
    model_name: str
    model_version: Optional[str]
    temperature: float
    max_tokens: int
    input_price: Optional[float]
    output_price: Optional[float]
    capabilities: Optional[str]
    is_default: bool
    is_enabled: bool
    created_time: str

    class Config:
        from_attributes = True


class AIScenarioCreate(BaseModel):
    """创建AI场景的请求模型"""
    scenario_name: str = Field(..., description="场景名称")
    scenario_desc: Optional[str] = Field(None, description="场景描述")
    primary_model_id: int = Field(..., description="主模型ID")
    fallback_model_id: Optional[int] = Field(None, description="回退模型ID")
    custom_params: Optional[Dict[str, Any]] = Field(None, description="自定义参数")
    is_enabled: bool = Field(True, description="是否启用")


class AIScenarioUpdate(BaseModel):
    """更新AI场景的请求模型"""
    scenario_name: Optional[str] = Field(None, description="场景名称")
    scenario_desc: Optional[str] = Field(None, description="场景描述")
    primary_model_id: Optional[int] = Field(None, description="主模型ID")
    fallback_model_id: Optional[int] = Field(None, description="回退模型ID")
    custom_params: Optional[Dict[str, Any]] = Field(None, description="自定义参数")
    is_enabled: Optional[bool] = Field(None, description="是否启用")


# ==================== AI提供商管理接口 ====================

@router.post("/providers", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_provider(
    provider: AIProviderCreate,
    db: Session = Depends(get_db)
):
    """
    [AI1.1] 创建AI提供商
    """
    try:
        service = AIProviderService(db)
        result = service.create_provider(
            provider_name=provider.provider_name,
            api_key=provider.api_key,
            api_endpoint=provider.api_endpoint,
            timeout=provider.timeout,
            max_retries=provider.max_retries,
            is_enabled=provider.is_enabled
        )

        return {
            "success": True,
            "message": "提供商创建成功",
            "data": {
                "provider_id": result.provider_id,
                "provider_name": result.provider_name
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.get("/providers/statistics", response_model=dict)
def get_provider_statistics(
    db: Session = Depends(get_db)
):
    """
    [AI1.1] 获取AI提供商统计信息
    """
    try:
        service = AIProviderService(db)
        stats = service.get_statistics()

        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@router.get("/providers", response_model=dict)
def list_providers(
    is_enabled: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    [AI1.1] 获取AI提供商列表
    """
    try:
        service = AIProviderService(db)
        providers = service.list_providers(
            is_enabled=is_enabled,
            skip=skip,
            limit=limit
        )

        return {
            "success": True,
            "data": {
                "providers": [
                    {
                        "provider_id": p.provider_id,
                        "provider_name": p.provider_name,
                        "api_endpoint": p.api_endpoint,
                        "timeout": p.timeout,
                        "max_retries": p.max_retries,
                        "is_enabled": p.is_enabled,
                        "created_time": p.created_time.isoformat(),
                        "updated_time": p.updated_time.isoformat()
                    }
                    for p in providers
                ],
                "total": len(providers)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取列表失败: {str(e)}")


@router.get("/providers/{provider_id}", response_model=dict)
def get_provider(
    provider_id: int,
    db: Session = Depends(get_db)
):
    """
    [AI1.1] 获取单个AI提供商
    """
    try:
        service = AIProviderService(db)
        provider = service.get_provider(provider_id)

        if not provider:
            raise HTTPException(status_code=404, detail="提供商不存在")

        return {
            "success": True,
            "data": {
                "provider_id": provider.provider_id,
                "provider_name": provider.provider_name,
                "api_endpoint": provider.api_endpoint,
                "timeout": provider.timeout,
                "max_retries": provider.max_retries,
                "is_enabled": provider.is_enabled,
                "created_time": provider.created_time.isoformat(),
                "updated_time": provider.updated_time.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.put("/providers/{provider_id}", response_model=dict)
def update_provider(
    provider_id: int,
    provider: AIProviderUpdate,
    db: Session = Depends(get_db)
):
    """
    [AI1.1] 更新AI提供商
    """
    try:
        service = AIProviderService(db)

        # 只更新非None的字段
        update_data = {k: v for k, v in provider.dict().items() if v is not None}

        result = service.update_provider(provider_id, **update_data)

        if not result:
            raise HTTPException(status_code=404, detail="提供商不存在")

        return {
            "success": True,
            "message": "提供商更新成功",
            "data": {
                "provider_id": result.provider_id,
                "provider_name": result.provider_name
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.delete("/providers/{provider_id}", response_model=dict)
def delete_provider(
    provider_id: int,
    db: Session = Depends(get_db)
):
    """
    [AI1.1] 删除AI提供商
    """
    try:
        service = AIProviderService(db)
        success = service.delete_provider(provider_id)

        if not success:
            raise HTTPException(status_code=404, detail="提供商不存在")

        return {
            "success": True,
            "message": "提供商删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.post("/providers/{provider_id}/toggle", response_model=dict)
def toggle_provider(
    provider_id: int,
    db: Session = Depends(get_db)
):
    """
    [AI1.1] 切换AI提供商启用状态
    """
    try:
        service = AIProviderService(db)
        result = service.toggle_provider(provider_id)

        if not result:
            raise HTTPException(status_code=404, detail="提供商不存在")

        return {
            "success": True,
            "message": f"提供商已{'启用' if result.is_enabled else '禁用'}",
            "data": {
                "provider_id": result.provider_id,
                "is_enabled": result.is_enabled
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"切换失败: {str(e)}")


@router.post("/providers/{provider_id}/test", response_model=dict)
def test_provider_connection(
    provider_id: int,
    db: Session = Depends(get_db)
):
    """
    [AI1.1] 测试AI提供商连接
    """
    try:
        service = AIProviderService(db)
        result = service.test_connection(provider_id)

        return {
            "success": result["success"],
            "message": result["message"],
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试失败: {str(e)}")


# ==================== AI模型管理接口 ====================

@router.get("/models/statistics", response_model=dict)
def get_model_statistics(
    db: Session = Depends(get_db)
):
    """
    [AI1.2] 获取AI模型统计信息
    """
    try:
        service = AIModelService(db)
        stats = service.get_statistics()

        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@router.post("/models", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_model(
    model: AIModelCreate,
    db: Session = Depends(get_db)
):
    """
    [AI1.2] 创建AI模型
    """
    try:
        service = AIModelService(db)
        result = service.create_model(
            provider_id=model.provider_id,
            model_name=model.model_name,
            model_version=model.model_version,
            temperature=model.temperature,
            max_tokens=model.max_tokens,
            input_price=model.input_price,
            output_price=model.output_price,
            capabilities=model.capabilities,
            is_default=model.is_default,
            is_enabled=model.is_enabled
        )

        return {
            "success": True,
            "message": "模型创建成功",
            "data": {
                "model_id": result.model_id,
                "model_name": result.model_name
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.get("/models", response_model=dict)
def list_models(
    provider_id: Optional[int] = None,
    is_enabled: Optional[bool] = None,
    is_default: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    [AI1.2] 获取AI模型列表
    """
    try:
        service = AIModelService(db)
        models = service.list_models(
            provider_id=provider_id,
            is_enabled=is_enabled,
            is_default=is_default,
            skip=skip,
            limit=limit
        )

        import json

        return {
            "success": True,
            "data": {
                "models": [
                    {
                        "model_id": m.model_id,
                        "provider_id": m.provider_id,
                        "model_name": m.model_name,
                        "model_version": m.model_version,
                        "temperature": m.temperature,
                        "max_tokens": m.max_tokens,
                        "input_price": m.input_price,
                        "output_price": m.output_price,
                        "capabilities": json.loads(m.capabilities) if m.capabilities else [],
                        "is_default": m.is_default,
                        "is_enabled": m.is_enabled,
                        "created_time": m.created_time.isoformat()
                    }
                    for m in models
                ],
                "total": len(models)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取列表失败: {str(e)}")


@router.get("/models/{model_id}", response_model=dict)
def get_model(
    model_id: int,
    db: Session = Depends(get_db)
):
    """
    [AI1.2] 获取单个AI模型（包含提供商信息）
    """
    try:
        service = AIModelService(db)
        model_data = service.get_model_with_provider(model_id)

        if not model_data:
            raise HTTPException(status_code=404, detail="模型不存在")

        return {
            "success": True,
            "data": model_data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.put("/models/{model_id}", response_model=dict)
def update_model(
    model_id: int,
    model: AIModelUpdate,
    db: Session = Depends(get_db)
):
    """
    [AI1.2] 更新AI模型
    """
    try:
        service = AIModelService(db)

        # 只更新非None的字段
        update_data = {k: v for k, v in model.dict().items() if v is not None}

        result = service.update_model(model_id, **update_data)

        if not result:
            raise HTTPException(status_code=404, detail="模型不存在")

        return {
            "success": True,
            "message": "模型更新成功",
            "data": {
                "model_id": result.model_id,
                "model_name": result.model_name
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.delete("/models/{model_id}", response_model=dict)
def delete_model(
    model_id: int,
    db: Session = Depends(get_db)
):
    """
    [AI1.2] 删除AI模型
    """
    try:
        service = AIModelService(db)
        success = service.delete_model(model_id)

        if not success:
            raise HTTPException(status_code=404, detail="模型不存在")

        return {
            "success": True,
            "message": "模型删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.post("/models/{model_id}/toggle", response_model=dict)
def toggle_model(
    model_id: int,
    db: Session = Depends(get_db)
):
    """
    [AI1.2] 切换AI模型启用状态
    """
    try:
        service = AIModelService(db)
        result = service.toggle_model(model_id)

        if not result:
            raise HTTPException(status_code=404, detail="模型不存在")

        return {
            "success": True,
            "message": f"模型已{'启用' if result.is_enabled else '禁用'}",
            "data": {
                "model_id": result.model_id,
                "is_enabled": result.is_enabled
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"切换失败: {str(e)}")


@router.post("/models/{model_id}/set-default", response_model=dict)
def set_default_model(
    model_id: int,
    db: Session = Depends(get_db)
):
    """
    [AI1.2] 设置默认AI模型
    """
    try:
        service = AIModelService(db)
        result = service.set_default_model(model_id)

        if not result:
            raise HTTPException(status_code=404, detail="模型不存在")

        return {
            "success": True,
            "message": "默认模型设置成功",
            "data": {
                "model_id": result.model_id,
                "model_name": result.model_name
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"设置失败: {str(e)}")


@router.get("/models/statistics", response_model=dict)
def get_model_statistics(
    db: Session = Depends(get_db)
):
    """
    [AI1.2] 获取AI模型统计信息
    """
    try:
        service = AIModelService(db)
        stats = service.get_statistics()

        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


# ==================== AI场景管理接口 ====================

@router.post("/scenarios", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_scenario(
    scenario: AIScenarioCreate,
    db: Session = Depends(get_db)
):
    """
    [AI1.3] 创建AI场景
    """
    try:
        service = AIScenarioService(db)
        result = service.create_scenario(
            scenario_name=scenario.scenario_name,
            scenario_desc=scenario.scenario_desc,
            primary_model_id=scenario.primary_model_id,
            fallback_model_id=scenario.fallback_model_id,
            custom_params=scenario.custom_params,
            is_enabled=scenario.is_enabled
        )

        return {
            "success": True,
            "message": "场景创建成功",
            "data": {
                "scenario_id": result.scenario_id,
                "scenario_name": result.scenario_name
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.get("/scenarios/statistics", response_model=dict)
def get_scenario_statistics(
    db: Session = Depends(get_db)
):
    """
    [AI1.3] 获取AI场景统计信息
    """
    try:
        service = AIScenarioService(db)
        stats = service.get_statistics()

        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@router.get("/scenarios", response_model=dict)
def list_scenarios(
    is_enabled: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    [AI1.3] 获取AI场景列表
    """
    try:
        service = AIScenarioService(db)
        scenarios = service.list_scenarios(
            is_enabled=is_enabled,
            skip=skip,
            limit=limit
        )

        return {
            "success": True,
            "data": {
                "scenarios": [
                    {
                        "scenario_id": s.scenario_id,
                        "scenario_name": s.scenario_name,
                        "scenario_desc": s.scenario_desc,
                        "primary_model_id": s.primary_model_id,
                        "fallback_model_id": s.fallback_model_id,
                        "is_enabled": s.is_enabled,
                        "created_time": s.created_time.isoformat()
                    }
                    for s in scenarios
                ],
                "total": len(scenarios)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取列表失败: {str(e)}")


@router.get("/scenarios/{scenario_id}", response_model=dict)
def get_scenario(
    scenario_id: int,
    db: Session = Depends(get_db)
):
    """
    [AI1.3] 获取单个AI场景
    """
    try:
        service = AIScenarioService(db)
        scenario = service.get_scenario(scenario_id)

        if not scenario:
            raise HTTPException(status_code=404, detail="场景不存在")

        return {
            "success": True,
            "data": {
                "scenario_id": scenario.scenario_id,
                "scenario_name": scenario.scenario_name,
                "scenario_desc": scenario.scenario_desc,
                "primary_model_id": scenario.primary_model_id,
                "fallback_model_id": scenario.fallback_model_id,
                "is_enabled": scenario.is_enabled,
                "created_time": scenario.created_time.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get("/scenarios/{scenario_id}/with-models", response_model=dict)
def get_scenario_with_models(
    scenario_id: int,
    db: Session = Depends(get_db)
):
    """
    [AI1.3] 获取AI场景及其关联的模型信息
    """
    try:
        service = AIScenarioService(db)
        scenario_data = service.get_scenario_with_models(scenario_id)

        if not scenario_data:
            raise HTTPException(status_code=404, detail="场景不存在")

        return {
            "success": True,
            "data": scenario_data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.put("/scenarios/{scenario_id}", response_model=dict)
def update_scenario(
    scenario_id: int,
    scenario: AIScenarioUpdate,
    db: Session = Depends(get_db)
):
    """
    [AI1.3] 更新AI场景
    """
    try:
        service = AIScenarioService(db)

        # 只更新非None的字段
        update_data = {k: v for k, v in scenario.dict().items() if v is not None}

        result = service.update_scenario(scenario_id, **update_data)

        if not result:
            raise HTTPException(status_code=404, detail="场景不存在")

        return {
            "success": True,
            "message": "场景更新成功",
            "data": {
                "scenario_id": result.scenario_id,
                "scenario_name": result.scenario_name
            }
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.delete("/scenarios/{scenario_id}", response_model=dict)
def delete_scenario(
    scenario_id: int,
    db: Session = Depends(get_db)
):
    """
    [AI1.3] 删除AI场景
    """
    try:
        service = AIScenarioService(db)
        success = service.delete_scenario(scenario_id)

        if not success:
            raise HTTPException(status_code=404, detail="场景不存在")

        return {
            "success": True,
            "message": "场景删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.post("/scenarios/{scenario_id}/toggle", response_model=dict)
def toggle_scenario(
    scenario_id: int,
    db: Session = Depends(get_db)
):
    """
    [AI1.3] 切换AI场景启用状态
    """
    try:
        service = AIScenarioService(db)
        result = service.toggle_scenario(scenario_id)

        if not result:
            raise HTTPException(status_code=404, detail="场景不存在")

        return {
            "success": True,
            "message": f"场景已{'启用' if result.is_enabled else '禁用'}",
            "data": {
                "scenario_id": result.scenario_id,
                "is_enabled": result.is_enabled
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"切换失败: {str(e)}")


# ==================== 统一AI调用接口 ====================

from backend.services.ai_call_service import AICallService
from backend.services.ai_prompt_service import AIPromptService

class AICallRequest(BaseModel):
    """AI调用请求模型"""
    scenario_name: str = Field(..., description="场景名称")
    prompt: str = Field(..., description="用户提示词")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    temperature: Optional[float] = Field(None, description="温度参数")
    max_tokens: Optional[int] = Field(None, description="最大token数")


@router.post("/call", response_model=dict)
async def call_ai_by_scenario(
    request: AICallRequest,
    db: Session = Depends(get_db)
):
    """
    [AI1.3扩展] 根据场景调用AI
    
    支持主模型和回退模型的自动切换
    """
    try:
        service = AICallService(db)
        result = await service.call_by_scenario(
            scenario_name=request.scenario_name,
            prompt=request.prompt,
            system_prompt=request.system_prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )

        return {
            "success": True,
            "message": "AI调用成功",
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI调用失败: {str(e)}")


# ==================== AI提示词管理接口 ====================

class AIPromptCreate(BaseModel):
    """创建AI提示词的请求模型"""
    scenario_id: int = Field(..., description="场景ID")
    prompt_name: str = Field(..., description="提示词名称")
    prompt_template: str = Field(..., description="提示词模板")
    variables: Optional[List[str]] = Field(None, description="变量列表")
    version: int = Field(1, description="版本号")
    is_active: bool = Field(True, description="是否激活")


class AIPromptUpdate(BaseModel):
    """更新AI提示词的请求模型"""
    prompt_name: Optional[str] = Field(None, description="提示词名称")
    prompt_template: Optional[str] = Field(None, description="提示词模板")
    variables: Optional[List[str]] = Field(None, description="变量列表")
    is_active: Optional[bool] = Field(None, description="是否激活")


class AIPromptNewVersion(BaseModel):
    """创建提示词新版本的请求模型"""
    prompt_template: str = Field(..., description="新的提示词模板")
    variables: Optional[List[str]] = Field(None, description="新的变量列表")


class AIPromptRenderRequest(BaseModel):
    """渲染提示词的请求模型"""
    variables_values: Dict[str, Any] = Field(..., description="变量值字典")


@router.post("/prompts", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_prompt(
    prompt: AIPromptCreate,
    db: Session = Depends(get_db)
):
    """
    [AI1.4] 创建AI提示词
    """
    try:
        service = AIPromptService(db)
        result = service.create_prompt(
            scenario_id=prompt.scenario_id,
            prompt_name=prompt.prompt_name,
            prompt_template=prompt.prompt_template,
            variables=prompt.variables,
            version=prompt.version,
            is_active=prompt.is_active
        )

        return {
            "success": True,
            "message": "提示词创建成功",
            "data": {
                "prompt_id": result.prompt_id,
                "prompt_name": result.prompt_name
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.get("/prompts", response_model=dict)
def list_prompts(
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    [AI1.4] 获取AI提示词列表
    """
    try:
        service = AIPromptService(db)
        prompts = service.list_all_prompts(
            is_active=is_active,
            skip=skip,
            limit=limit
        )

        import json

        return {
            "success": True,
            "data": {
                "prompts": [
                    {
                        "prompt_id": p.prompt_id,
                        "scenario_id": p.scenario_id,
                        "prompt_name": p.prompt_name,
                        "prompt_template": p.prompt_template,
                        "version": p.version,
                        "variables": json.loads(p.variables) if p.variables else [],
                        "is_active": p.is_active,
                        "created_time": p.created_time.isoformat()
                    }
                    for p in prompts
                ],
                "total": len(prompts)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取列表失败: {str(e)}")


@router.get("/scenarios/{scenario_id}/prompts", response_model=dict)
def list_prompts_by_scenario(
    scenario_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    [AI1.4] 获取场景的所有提示词
    """
    try:
        service = AIPromptService(db)
        prompts = service.list_prompts_by_scenario(
            scenario_id=scenario_id,
            skip=skip,
            limit=limit
        )

        import json

        return {
            "success": True,
            "data": {
                "prompts": [
                    {
                        "prompt_id": p.prompt_id,
                        "scenario_id": p.scenario_id,
                        "prompt_name": p.prompt_name,
                        "prompt_template": p.prompt_template,
                        "version": p.version,
                        "variables": json.loads(p.variables) if p.variables else [],
                        "is_active": p.is_active,
                        "created_time": p.created_time.isoformat()
                    }
                    for p in prompts
                ],
                "total": len(prompts)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取列表失败: {str(e)}")


@router.get("/scenarios/{scenario_id}/prompts/active", response_model=dict)
def get_active_prompt(
    scenario_id: int,
    db: Session = Depends(get_db)
):
    """
    [AI1.4] 获取场景的激活提示词
    """
    try:
        service = AIPromptService(db)
        prompt = service.get_active_prompt_by_scenario(scenario_id)

        if not prompt:
            return {
                "success": True,
                "data": None,
                "message": "该场景暂无激活的提示词"
            }

        import json

        return {
            "success": True,
            "data": {
                "prompt_id": prompt.prompt_id,
                "scenario_id": prompt.scenario_id,
                "prompt_name": prompt.prompt_name,
                "prompt_template": prompt.prompt_template,
                "version": prompt.version,
                "variables": json.loads(prompt.variables) if prompt.variables else [],
                "is_active": prompt.is_active,
                "created_time": prompt.created_time.isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get("/prompts/{prompt_id}", response_model=dict)
def get_prompt(
    prompt_id: int,
    db: Session = Depends(get_db)
):
    """
    [AI1.4] 获取单个AI提示词（包含场景信息）
    """
    try:
        service = AIPromptService(db)
        prompt_data = service.get_prompt_with_scenario(prompt_id)

        if not prompt_data:
            raise HTTPException(status_code=404, detail="提示词不存在")

        return {
            "success": True,
            "data": prompt_data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.put("/prompts/{prompt_id}", response_model=dict)
def update_prompt(
    prompt_id: int,
    prompt: AIPromptUpdate,
    db: Session = Depends(get_db)
):
    """
    [AI1.4] 更新AI提示词
    """
    try:
        service = AIPromptService(db)

        # 只更新非None的字段
        update_data = {k: v for k, v in prompt.dict().items() if v is not None}

        result = service.update_prompt(prompt_id, **update_data)

        if not result:
            raise HTTPException(status_code=404, detail="提示词不存在")

        return {
            "success": True,
            "message": "提示词更新成功",
            "data": {
                "prompt_id": result.prompt_id,
                "prompt_name": result.prompt_name
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.delete("/prompts/{prompt_id}", response_model=dict)
def delete_prompt(
    prompt_id: int,
    db: Session = Depends(get_db)
):
    """
    [AI1.4] 删除AI提示词
    """
    try:
        service = AIPromptService(db)
        success = service.delete_prompt(prompt_id)

        if not success:
            raise HTTPException(status_code=404, detail="提示词不存在")

        return {
            "success": True,
            "message": "提示词删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.post("/prompts/{prompt_id}/activate", response_model=dict)
def activate_prompt(
    prompt_id: int,
    db: Session = Depends(get_db)
):
    """
    [AI1.4] 激活提示词（同时将同场景的其他提示词设为非激活）
    """
    try:
        service = AIPromptService(db)
        result = service.activate_prompt(prompt_id)

        if not result:
            raise HTTPException(status_code=404, detail="提示词不存在")

        return {
            "success": True,
            "message": "提示词已激活",
            "data": {
                "prompt_id": result.prompt_id,
                "is_active": result.is_active
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"激活失败: {str(e)}")


@router.post("/prompts/{prompt_id}/new-version", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_new_version(
    prompt_id: int,
    request: AIPromptNewVersion,
    db: Session = Depends(get_db)
):
    """
    [AI1.4] 创建提示词的新版本
    """
    try:
        service = AIPromptService(db)
        result = service.create_new_version(
            prompt_id=prompt_id,
            prompt_template=request.prompt_template,
            variables=request.variables
        )

        return {
            "success": True,
            "message": "新版本创建成功",
            "data": {
                "prompt_id": result.prompt_id,
                "version": result.version
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.post("/prompts/{prompt_id}/render", response_model=dict)
def render_prompt(
    prompt_id: int,
    request: AIPromptRenderRequest,
    db: Session = Depends(get_db)
):
    """
    [AI1.4] 渲染提示词模板（替换变量）
    """
    try:
        service = AIPromptService(db)
        rendered = service.render_prompt(
            prompt_id=prompt_id,
            variables_values=request.variables_values
        )

        return {
            "success": True,
            "data": {
                "rendered_prompt": rendered
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"渲染失败: {str(e)}")


@router.get("/prompts/statistics", response_model=dict)
def get_prompt_statistics(
    db: Session = Depends(get_db)
):
    """
    [AI1.4] 获取AI提示词统计信息
    """
    try:
        service = AIPromptService(db)
        stats = service.get_statistics()

        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")
