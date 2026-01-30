"""
AI配置初始化脚本
创建提供商、模型和场景配置
支持常用大模型：Claude、DeepSeek、GPT、Gemini等
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import get_db
from backend.services.ai_provider_service import AIProviderService
from backend.services.ai_model_service import AIModelService
from backend.services.ai_scenario_service import AIScenarioService


# ==================== 提供商配置 ====================
PROVIDERS_CONFIG = [
    {
        'name': 'Claude',
        'env_key': 'CLAUDE_API_KEY',
        'api_endpoint': 'https://api.anthropic.com',
        'timeout': 60,
        'max_retries': 3,
        'description': 'Anthropic Claude API'
    },
    {
        'name': 'OpenAI',
        'env_key': 'OPENAI_API_KEY',
        'api_endpoint': 'https://api.openai.com',
        'timeout': 60,
        'max_retries': 3,
        'description': 'OpenAI GPT API'
    },
    {
        'name': 'DeepSeek',
        'env_key': 'DEEPSEEK_API_KEY',
        'api_endpoint': 'https://api.deepseek.com',
        'timeout': 60,
        'max_retries': 3,
        'description': 'DeepSeek API'
    },
    {
        'name': 'Gemini',
        'env_key': 'GEMINI_API_KEY',
        'api_endpoint': 'https://generativelanguage.googleapis.com',
        'timeout': 60,
        'max_retries': 3,
        'description': 'Google Gemini API'
    },
    {
        'name': 'Moonshot',
        'env_key': 'MOONSHOT_API_KEY',
        'api_endpoint': 'https://api.moonshot.cn',
        'timeout': 60,
        'max_retries': 3,
        'description': 'Moonshot (Kimi) API'
    },
    {
        'name': 'Zhipu',
        'env_key': 'ZHIPU_API_KEY',
        'api_endpoint': 'https://open.bigmodel.cn',
        'timeout': 60,
        'max_retries': 3,
        'description': 'Zhipu (GLM) API'
    }
]


# ==================== 模型配置 ====================
MODELS_CONFIG = [
    # Claude 模型
    {
        'provider': 'Claude',
        'model_name': 'claude-3-5-sonnet-20241022',
        'model_version': '20241022',
        'temperature': 0.7,
        'max_tokens': 8192,
        'input_price': 3.0,
        'output_price': 15.0,
        'capabilities': ['text-generation', 'json-output', 'complex-reasoning', 'long-context'],
        'is_default': True,
        'description': 'Claude 3.5 Sonnet - 最新最强模型，平衡性能和成本'
    },
    {
        'provider': 'Claude',
        'model_name': 'claude-3-haiku-20240307',
        'model_version': '20240307',
        'temperature': 0.7,
        'max_tokens': 4096,
        'input_price': 0.25,
        'output_price': 1.25,
        'capabilities': ['text-generation', 'json-output', 'fast-response'],
        'is_default': False,
        'description': 'Claude 3 Haiku - 快速、低成本'
    },
    {
        'provider': 'Claude',
        'model_name': 'claude-3-opus-20240229',
        'model_version': '20240229',
        'temperature': 0.7,
        'max_tokens': 4096,
        'input_price': 15.0,
        'output_price': 75.0,
        'capabilities': ['text-generation', 'json-output', 'complex-reasoning', 'highest-quality'],
        'is_default': False,
        'description': 'Claude 3 Opus - 最高质量，适合复杂任务'
    },

    # OpenAI GPT 模型
    {
        'provider': 'OpenAI',
        'model_name': 'gpt-4o',
        'model_version': 'latest',
        'temperature': 0.7,
        'max_tokens': 4096,
        'input_price': 2.5,
        'output_price': 10.0,
        'capabilities': ['text-generation', 'json-output', 'vision', 'function-calling'],
        'is_default': True,
        'description': 'GPT-4o - 最新多模态模型'
    },
    {
        'provider': 'OpenAI',
        'model_name': 'gpt-4o-mini',
        'model_version': 'latest',
        'temperature': 0.7,
        'max_tokens': 16384,
        'input_price': 0.15,
        'output_price': 0.6,
        'capabilities': ['text-generation', 'json-output', 'fast-response'],
        'is_default': False,
        'description': 'GPT-4o Mini - 快速、低成本'
    },
    {
        'provider': 'OpenAI',
        'model_name': 'gpt-4-turbo',
        'model_version': 'latest',
        'temperature': 0.7,
        'max_tokens': 4096,
        'input_price': 10.0,
        'output_price': 30.0,
        'capabilities': ['text-generation', 'json-output', 'vision', 'long-context'],
        'is_default': False,
        'description': 'GPT-4 Turbo - 高性能版本'
    },
    {
        'provider': 'OpenAI',
        'model_name': 'gpt-3.5-turbo',
        'model_version': 'latest',
        'temperature': 0.7,
        'max_tokens': 4096,
        'input_price': 0.5,
        'output_price': 1.5,
        'capabilities': ['text-generation', 'json-output', 'fast-response'],
        'is_default': False,
        'description': 'GPT-3.5 Turbo - 经济实惠'
    },

    # DeepSeek 模型
    {
        'provider': 'DeepSeek',
        'model_name': 'deepseek-chat',
        'model_version': 'latest',
        'temperature': 0.7,
        'max_tokens': 4096,
        'input_price': 0.14,
        'output_price': 0.28,
        'capabilities': ['text-generation', 'json-output', 'chinese-support', 'code-generation'],
        'is_default': True,
        'description': 'DeepSeek Chat - 高性价比，支持中文'
    },
    {
        'provider': 'DeepSeek',
        'model_name': 'deepseek-coder',
        'model_version': 'latest',
        'temperature': 0.7,
        'max_tokens': 4096,
        'input_price': 0.14,
        'output_price': 0.28,
        'capabilities': ['code-generation', 'text-generation', 'json-output'],
        'is_default': False,
        'description': 'DeepSeek Coder - 专注代码生成'
    },

    # Gemini 模型
    {
        'provider': 'Gemini',
        'model_name': 'gemini-1.5-pro',
        'model_version': 'latest',
        'temperature': 0.7,
        'max_tokens': 8192,
        'input_price': 1.25,
        'output_price': 5.0,
        'capabilities': ['text-generation', 'json-output', 'vision', 'long-context'],
        'is_default': True,
        'description': 'Gemini 1.5 Pro - 长上下文支持'
    },
    {
        'provider': 'Gemini',
        'model_name': 'gemini-1.5-flash',
        'model_version': 'latest',
        'temperature': 0.7,
        'max_tokens': 8192,
        'input_price': 0.075,
        'output_price': 0.3,
        'capabilities': ['text-generation', 'json-output', 'fast-response'],
        'is_default': False,
        'description': 'Gemini 1.5 Flash - 快速响应'
    },

    # Moonshot (Kimi) 模型
    {
        'provider': 'Moonshot',
        'model_name': 'moonshot-v1-8k',
        'model_version': 'v1',
        'temperature': 0.7,
        'max_tokens': 8192,
        'input_price': 1.0,
        'output_price': 1.0,
        'capabilities': ['text-generation', 'json-output', 'chinese-support'],
        'is_default': True,
        'description': 'Moonshot 8K - 标准版本'
    },
    {
        'provider': 'Moonshot',
        'model_name': 'moonshot-v1-32k',
        'model_version': 'v1',
        'temperature': 0.7,
        'max_tokens': 32768,
        'input_price': 2.0,
        'output_price': 2.0,
        'capabilities': ['text-generation', 'json-output', 'chinese-support', 'long-context'],
        'is_default': False,
        'description': 'Moonshot 32K - 长上下文版本'
    },
    {
        'provider': 'Moonshot',
        'model_name': 'moonshot-v1-128k',
        'model_version': 'v1',
        'temperature': 0.7,
        'max_tokens': 128000,
        'input_price': 5.0,
        'output_price': 5.0,
        'capabilities': ['text-generation', 'json-output', 'chinese-support', 'ultra-long-context'],
        'is_default': False,
        'description': 'Moonshot 128K - 超长上下文版本'
    },

    # Zhipu (GLM) 模型
    {
        'provider': 'Zhipu',
        'model_name': 'glm-4',
        'model_version': 'latest',
        'temperature': 0.7,
        'max_tokens': 4096,
        'input_price': 10.0,
        'output_price': 10.0,
        'capabilities': ['text-generation', 'json-output', 'chinese-support'],
        'is_default': True,
        'description': 'GLM-4 - 智谱最新模型'
    },
    {
        'provider': 'Zhipu',
        'model_name': 'glm-3-turbo',
        'model_version': 'latest',
        'temperature': 0.7,
        'max_tokens': 4096,
        'input_price': 0.5,
        'output_price': 0.5,
        'capabilities': ['text-generation', 'json-output', 'chinese-support', 'fast-response'],
        'is_default': False,
        'description': 'GLM-3 Turbo - 快速版本'
    }
]


# ==================== 场景配置 ====================
SCENARIOS_CONFIG = [
    {
        'name': '类别名称生成',
        'desc': '为聚类簇生成简洁的类别名称（2-4个单词）',
        'primary_model': 'deepseek-chat',
        'fallback_model': 'gpt-4o-mini',
        'params': {'temperature': 0.3, 'max_tokens': 50}
    },
    {
        'name': '需求分析',
        'desc': '分析商品簇，识别用户需求、目标用户、使用场景和价值主张',
        'primary_model': 'deepseek-chat',
        'fallback_model': 'gpt-4o-mini',
        'params': {'temperature': 0.5, 'max_tokens': 500}
    },
    {
        'name': '交付产品识别',
        'desc': '识别商品的交付类型、格式和平台',
        'primary_model': 'deepseek-chat',
        'fallback_model': 'gpt-4o-mini',
        'params': {'temperature': 0.3, 'max_tokens': 200}
    },
    {
        'name': 'Top商品深度分析',
        'desc': '对Top商品进行深度分析，提取用户需求和关键词',
        'primary_model': 'claude-3-5-sonnet-20241022',
        'fallback_model': 'gpt-4o',
        'params': {'temperature': 0.7, 'max_tokens': 1024}
    },
    {
        'name': '属性提取辅助',
        'desc': '辅助提取商品属性（当规则无法识别时）',
        'primary_model': 'gpt-4o-mini',
        'fallback_model': 'deepseek-chat',
        'params': {'temperature': 0.3, 'max_tokens': 100}
    }
]


def setup_ai_config():
    """设置AI配置"""

    print("=" * 80)
    print("AI Configuration Setup - 常用大模型预设")
    print("=" * 80)
    print()
    print("支持的提供商:")
    for config in PROVIDERS_CONFIG:
        print(f"  - {config['name']}: {config['description']}")
    print()

    # 获取数据库会话
    db = next(get_db())

    try:
        provider_service = AIProviderService(db)
        model_service = AIModelService(db)
        scenario_service = AIScenarioService(db)

        # ==================== 第1步: 创建提供商 ====================
        print("Step 1: Creating AI Providers...")
        print("-" * 80)

        providers = {}

        for config in PROVIDERS_CONFIG:
            api_key = os.getenv(config['env_key'])

            if api_key:
                try:
                    provider = provider_service.create_provider(
                        provider_name=config['name'],
                        api_key=api_key,
                        api_endpoint=config['api_endpoint'],
                        timeout=config['timeout'],
                        max_retries=config['max_retries'],
                        is_enabled=True
                    )
                    providers[config['name'].lower()] = provider.provider_id
                    print(f"  [OK] {config['name']} Provider Created (ID: {provider.provider_id})")
                except ValueError as e:
                    if "已存在" in str(e):
                        # 提供商已存在，获取ID
                        existing = provider_service.list_providers()
                        for p in existing:
                            if p.provider_name == config['name']:
                                providers[config['name'].lower()] = p.provider_id
                                print(f"  [SKIP] {config['name']} Provider Already Exists (ID: {p.provider_id})")
                                break
                    else:
                        raise
            else:
                print(f"  [SKIP] {config['name']}: {config['env_key']} not found")

        print()

        if not providers:
            print("[ERROR] No API keys found. Please set at least one API key:")
            for config in PROVIDERS_CONFIG:
                print(f"  - {config['env_key']} for {config['name']}")
            print()
            print("Example .env file:")
            print("  CLAUDE_API_KEY=sk-ant-xxx")
            print("  OPENAI_API_KEY=sk-xxx")
            print("  DEEPSEEK_API_KEY=sk-xxx")
            print("  GEMINI_API_KEY=xxx")
            print("  MOONSHOT_API_KEY=sk-xxx")
            print("  ZHIPU_API_KEY=xxx")
            return False

        # ==================== 第2步: 创建模型 ====================
        print("Step 2: Creating AI Models...")
        print("-" * 80)

        models = {}

        for config in MODELS_CONFIG:
            provider_key = config['provider'].lower()

            # 检查提供商是否已创建
            if provider_key not in providers:
                print(f"  [SKIP] {config['model_name']}: Provider {config['provider']} not available")
                continue

            try:
                model = model_service.create_model(
                    provider_id=providers[provider_key],
                    model_name=config['model_name'],
                    model_version=config['model_version'],
                    temperature=config['temperature'],
                    max_tokens=config['max_tokens'],
                    input_price=config['input_price'],
                    output_price=config['output_price'],
                    capabilities=config['capabilities'],
                    is_default=config['is_default'],
                    is_enabled=True
                )
                models[config['model_name']] = model.model_id
                print(f"  [OK] {config['model_name']} Created (ID: {model.model_id})")
                print(f"       {config['description']}")
            except ValueError as e:
                if "已存在" in str(e):
                    existing = model_service.list_models(provider_id=providers[provider_key])
                    for m in existing:
                        if m.model_name == config['model_name']:
                            models[config['model_name']] = m.model_id
                            print(f"  [SKIP] {config['model_name']} Already Exists (ID: {m.model_id})")
                            break
                else:
                    raise

        print()

        # ==================== 第3步: 创建场景 ====================
        print("Step 3: Creating AI Scenarios...")
        print("-" * 80)

        for config in SCENARIOS_CONFIG:
            # 检查主模型和回退模型是否存在
            primary_model_id = models.get(config['primary_model'])
            fallback_model_id = models.get(config['fallback_model'])

            if not primary_model_id:
                print(f"  [SKIP] {config['name']}: Primary model {config['primary_model']} not available")
                continue

            try:
                scenario = scenario_service.create_scenario(
                    scenario_name=config['name'],
                    scenario_desc=config['desc'],
                    primary_model_id=primary_model_id,
                    fallback_model_id=fallback_model_id,
                    custom_params=config['params'],
                    is_enabled=True
                )
                print(f"  [OK] {config['name']} Created (ID: {scenario.scenario_id})")
                print(f"       Primary: {config['primary_model']}, Fallback: {config.get('fallback_model', 'None')}")
            except ValueError as e:
                if "已存在" in str(e):
                    print(f"  [SKIP] {config['name']} Already Exists")
                else:
                    raise

        print()
        print("=" * 80)
        print("AI Configuration Setup Complete!")
        print("=" * 80)
        print()

        # 显示统计信息
        print("Summary:")
        print(f"  Providers Created: {len(providers)}")
        print(f"  Models Created: {len(models)}")
        print(f"  Scenarios Created: {len(SCENARIOS_CONFIG)}")
        print()

        # 显示已配置的提供商
        print("Configured Providers:")
        for name, provider_id in providers.items():
            print(f"  - {name.capitalize()} (ID: {provider_id})")
        print()

        # 显示已配置的模型
        print("Configured Models:")
        for model_name, model_id in models.items():
            print(f"  - {model_name} (ID: {model_id})")
        print()

        return True

    except Exception as e:
        print(f"\n[ERROR] Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close()


if __name__ == '__main__':
    success = setup_ai_config()
    sys.exit(0 if success else 1)
