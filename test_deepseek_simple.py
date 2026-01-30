"""
简单测试DeepSeek配置
"""
import asyncio
import httpx


async def test_deepseek_direct():
    """直接测试DeepSeek API"""
    print("=" * 60)
    print("Testing DeepSeek Configuration")
    print("=" * 60)
    print()

    # 从数据库读取API密钥
    from backend.database import get_db
    from backend.services.ai_provider_service import AIProviderService

    db = next(get_db())
    provider_service = AIProviderService(db)
    providers = provider_service.list_providers()
    deepseek = next((p for p in providers if p.provider_name == "DeepSeek"), None)

    if not deepseek:
        print("[ERROR] DeepSeek provider not found!")
        return

    print(f"Provider: {deepseek.provider_name}")
    print(f"API Endpoint: {deepseek.api_endpoint}")
    print(f"Status: {'Enabled' if deepseek.is_enabled else 'Disabled'}")
    print()

    # 测试API调用
    print("Calling DeepSeek API...")
    print("Prompt: Please introduce DeepSeek in one sentence")
    print()

    try:
        headers = {
            "Authorization": f"Bearer {deepseek.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "user",
                    "content": "Please introduce DeepSeek in one sentence"
                }
            ],
            "temperature": 0.7,
            "max_tokens": 100
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{deepseek.api_endpoint}/v1/chat/completions",
                headers=headers,
                json=payload
            )

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]

                print("[OK] Call successful!")
                print()
                print("=" * 60)
                print("AI Response:")
                print("=" * 60)
                # 使用 utf-8 编码输出，避免 gbk 编码问题
                try:
                    print(content.encode('utf-8', errors='ignore').decode('utf-8'))
                except:
                    print(content.encode('ascii', errors='ignore').decode('ascii'))
                print()
                print("=" * 60)
                print("Call Details:")
                print("=" * 60)
                print(f"Model: {result.get('model', 'N/A')}")
                print(f"Tokens used: {result.get('usage', {}).get('total_tokens', 'N/A')}")
                print()
                print("[SUCCESS] DeepSeek configuration is working perfectly!")
            else:
                print(f"[ERROR] API returned status code: {response.status_code}")
                print(f"Response: {response.text}")

    except Exception as e:
        print("[ERROR] Call failed!")
        print(f"Error: {str(e)}")
        print()
        print("Possible reasons:")
        print("1. Invalid API key")
        print("2. Network connection issue")
        print("3. DeepSeek service temporarily unavailable")

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_deepseek_direct())
