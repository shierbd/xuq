"""
测试DeepSeek配置是否正常工作
"""
import asyncio
from backend.database import get_db
from backend.services.ai_call_service import AICallService


async def test_deepseek():
    """测试DeepSeek配置"""
    print("=" * 60)
    print("测试 DeepSeek AI 配置")
    print("=" * 60)
    print()

    # 获取数据库会话
    db = next(get_db())

    try:
        # 创建AI调用服务
        ai_service = AICallService(db)

        # 测试简单的AI调用
        print("正在调用 DeepSeek API...")
        print("提示词: 请用一句话介绍DeepSeek")
        print()

        # 先获取DeepSeek提供商
        from backend.services.ai_provider_service import AIProviderService
        provider_service = AIProviderService(db)
        providers = provider_service.list_providers()
        deepseek_provider = next((p for p in providers if p.provider_name == "DeepSeek"), None)

        if not deepseek_provider:
            raise Exception("未找到DeepSeek提供商配置")

        # 调用AI
        result = await ai_service.call_by_provider(
            provider_id=deepseek_provider.provider_id,
            prompt="请用一句话介绍DeepSeek",
            temperature=0.7,
            max_tokens=100
        )

        print("[OK] Call successful!")
        print()
        print("=" * 60)
        print("AI Response:")
        print("=" * 60)
        print(result["content"])
        print()
        print("=" * 60)
        print("Call Details:")
        print("=" * 60)
        print(f"Model used: {result.get('model_used', 'N/A')}")
        print(f"Tokens used: {result.get('tokens_used', 'N/A')}")
        print(f"Call time: {result.get('call_time', 'N/A')}")
        print()
        print("[SUCCESS] DeepSeek configuration is working!")

    except Exception as e:
        print("[ERROR] Call failed!")
        print(f"Error message: {str(e)}")
        print()
        print("Possible reasons:")
        print("1. Invalid API key")
        print("2. Network connection issue")
        print("3. DeepSeek service temporarily unavailable")

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_deepseek())
