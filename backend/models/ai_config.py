"""
[AI1.1, AI1.2, AI1.3, AI1.4, AI1.5] AI配置管理模块 - 数据库模型
包含5个表：AI提供商、AI模型、使用场景、提示词模板、使用日志
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from backend.database import Base


class AIProvider(Base):
    """
    [AI1.1] AI提供商表
    存储AI服务提供商的配置信息
    """
    __tablename__ = "ai_providers"

    provider_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    provider_name = Column(String(100), nullable=False, unique=True, comment="提供商名称（Claude、DeepSeek等）")
    api_key = Column(String(500), nullable=False, comment="API密钥（加密存储）")
    api_endpoint = Column(String(500), nullable=False, comment="API端点URL")
    timeout = Column(Integer, default=30, comment="请求超时时间（秒）")
    max_retries = Column(Integer, default=3, comment="最大重试次数")
    is_enabled = Column(Boolean, default=True, nullable=False, comment="是否启用")
    created_time = Column(DateTime, default=func.now(), nullable=False, comment="创建时间")
    updated_time = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")

    def __repr__(self):
        return f"<AIProvider(id={self.provider_id}, name={self.provider_name}, enabled={self.is_enabled})>"


class AIModel(Base):
    """
    [AI1.2] AI模型表
    存储不同提供商的AI模型配置
    """
    __tablename__ = "ai_models"

    model_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    provider_id = Column(Integer, ForeignKey("ai_providers.provider_id"), nullable=False, comment="提供商ID")
    model_name = Column(String(200), nullable=False, comment="模型名称")
    model_version = Column(String(100), comment="模型版本")
    temperature = Column(Float, default=0.7, comment="温度参数")
    max_tokens = Column(Integer, default=4096, comment="最大token数")
    input_price = Column(Float, comment="输入价格（$/1M tokens）")
    output_price = Column(Float, comment="输出价格（$/1M tokens）")
    capabilities = Column(Text, comment="能力标签（JSON数组）")
    is_default = Column(Boolean, default=False, nullable=False, comment="是否默认模型")
    is_enabled = Column(Boolean, default=True, nullable=False, comment="是否启用")
    created_time = Column(DateTime, default=func.now(), nullable=False, comment="创建时间")

    def __repr__(self):
        return f"<AIModel(id={self.model_id}, name={self.model_name}, default={self.is_default})>"


class AIScenario(Base):
    """
    [AI1.3] 使用场景表
    定义不同的AI使用场景及其配置
    """
    __tablename__ = "ai_scenarios"

    scenario_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    scenario_name = Column(String(200), nullable=False, unique=True, comment="场景名称")
    scenario_desc = Column(Text, comment="场景描述")
    primary_model_id = Column(Integer, ForeignKey("ai_models.model_id"), nullable=False, comment="主模型ID")
    fallback_model_id = Column(Integer, ForeignKey("ai_models.model_id"), comment="回退模型ID")
    custom_params = Column(Text, comment="自定义参数（JSON）")
    is_enabled = Column(Boolean, default=True, nullable=False, comment="是否启用")
    created_time = Column(DateTime, default=func.now(), nullable=False, comment="创建时间")

    def __repr__(self):
        return f"<AIScenario(id={self.scenario_id}, name={self.scenario_name})>"


class AIPrompt(Base):
    """
    [AI1.4] 提示词模板表
    管理AI提示词模板，支持版本控制
    """
    __tablename__ = "ai_prompts"

    prompt_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    scenario_id = Column(Integer, ForeignKey("ai_scenarios.scenario_id"), nullable=False, comment="场景ID")
    prompt_name = Column(String(200), nullable=False, comment="提示词名称")
    prompt_template = Column(Text, nullable=False, comment="提示词模板")
    version = Column(Integer, default=1, nullable=False, comment="版本号")
    variables = Column(Text, comment="变量列表（JSON）")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否激活")
    created_time = Column(DateTime, default=func.now(), nullable=False, comment="创建时间")

    def __repr__(self):
        return f"<AIPrompt(id={self.prompt_id}, name={self.prompt_name}, version={self.version})>"


class AIUsageLog(Base):
    """
    [AI1.5] 使用日志表
    记录所有AI API调用，用于成本监控
    """
    __tablename__ = "ai_usage_logs"

    log_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    scenario_id = Column(Integer, ForeignKey("ai_scenarios.scenario_id"), nullable=False, comment="场景ID")
    model_id = Column(Integer, ForeignKey("ai_models.model_id"), nullable=False, comment="模型ID")
    prompt_id = Column(Integer, ForeignKey("ai_prompts.prompt_id"), comment="提示词ID")
    input_tokens = Column(Integer, nullable=False, comment="输入token数")
    output_tokens = Column(Integer, nullable=False, comment="输出token数")
    cost = Column(Float, nullable=False, comment="成本（美元）")
    duration = Column(Float, nullable=False, comment="耗时（秒）")
    status = Column(String(50), nullable=False, comment="状态（success/error）")
    error_message = Column(Text, comment="错误信息")
    created_time = Column(DateTime, default=func.now(), nullable=False, comment="创建时间")

    def __repr__(self):
        return f"<AIUsageLog(id={self.log_id}, status={self.status}, cost=${self.cost:.4f})>"
