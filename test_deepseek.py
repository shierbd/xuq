"""测试 DeepSeek API 连接"""
import sys
import io

# Windows UTF-8 编码设置
if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from openai import OpenAI

def test_deepseek():
    """测试 DeepSeek API"""
    print("Testing DeepSeek API...")

    try:
        client = OpenAI(
            api_key='sk-6ab029906d3e4fda811eda5dc0f546b1',
            base_url='https://api.deepseek.com/v1'
        )

        response = client.chat.completions.create(
            model='deepseek-chat',
            messages=[{'role': 'user', 'content': 'Hello, reply with just OK'}],
            max_tokens=10,
            timeout=15
        )

        result = response.choices[0].message.content
        print(f"✅ DeepSeek API connection successful!")
        print(f"Response: {result}")
        return True

    except Exception as e:
        print(f"❌ DeepSeek API connection failed:")
        print(f"Error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    success = test_deepseek()
    sys.exit(0 if success else 1)
