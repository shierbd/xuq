"""测试 LLMClient 完整流程"""
import sys
import io

# Windows UTF-8 编码设置
if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from ai.client import LLMClient

def test_llm_client():
    """测试 LLMClient"""
    print("Testing LLMClient...")

    try:
        # 初始化客户端
        client = LLMClient()
        print(f"✅ LLMClient initialized")
        print(f"   Provider: {client.provider}")
        print(f"   Model: {client.config['model']}")
        print(f"   Base URL: {client.config.get('base_url', 'N/A')}")

        # 测试简单调用
        print("\nTesting simple LLM call...")
        messages = [{"role": "user", "content": "Reply with just: Hello"}]
        response = client._call_llm(messages, max_tokens=10)

        print(f"✅ LLM call successful!")
        print(f"Response: {response}")

        # 测试 token 分类
        print("\nTesting batch_classify_tokens...")
        tokens = ["best", "download", "calculator", "free"]
        classifications = client.batch_classify_tokens(tokens, batch_size=4)

        print(f"✅ Token classification successful!")
        for c in classifications:
            print(f"   {c['token']}: {c.get('token_type', 'unknown')}")

        return True

    except Exception as e:
        print(f"❌ Test failed:")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_llm_client()
    sys.exit(0 if success else 1)
