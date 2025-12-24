"""
LLM客户端测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from ai.client import LLMClient
from utils.exceptions import LLMException


class TestLLMClientInit:
    """测试LLM客户端初始化"""

    def test_init_invalid_provider(self):
        """测试无效提供商"""
        with pytest.raises(ValueError, match="不支持的LLM提供商"):
            LLMClient(provider='invalid_provider')

    @patch.dict('os.environ', {}, clear=True)
    def test_init_missing_api_key(self):
        """测试缺少API密钥"""
        # 模拟配置但没有API密钥
        with patch('ai.client.LLM_CONFIG', {'openai': {'api_key': None, 'model': 'gpt-4o-mini'}}):
            with pytest.raises(ValueError, match="API密钥未配置"):
                LLMClient(provider='openai')

    @pytest.mark.llm
    @patch('ai.client.OpenAI')
    def test_init_openai_success(self, mock_openai):
        """测试OpenAI客户端初始化成功"""
        mock_client = Mock()
        mock_openai.return_value = mock_client

        # 模拟配置
        with patch('ai.client.LLM_CONFIG', {
            'openai': {
                'api_key': 'test-key',
                'model': 'gpt-4o-mini',
                'temperature': 0.7,
                'max_tokens': 500,
                'base_url': None
            }
        }):
            client = LLMClient(provider='openai')

            assert client.provider == 'openai'
            assert client.client == mock_client
            mock_openai.assert_called_once_with(api_key='test-key', base_url=None)


class TestLLMClientCalls:
    """测试LLM调用"""

    @patch('ai.client.OpenAI')
    def test_call_llm_openai(self, mock_openai):
        """测试OpenAI API调用"""
        # Mock响应
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        with patch('ai.client.LLM_CONFIG', {
            'openai': {
                'api_key': 'test-key',
                'model': 'gpt-4o-mini',
                'temperature': 0.7,
                'max_tokens': 500
            }
        }):
            client = LLMClient(provider='openai')
            messages = [{"role": "user", "content": "Hello"}]
            response = client._call_llm(messages)

            assert response == "Test response"
            mock_client.chat.completions.create.assert_called_once()

    @patch('ai.client.OpenAI')
    def test_call_llm_failure(self, mock_openai):
        """测试API调用失败"""
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client

        with patch('ai.client.LLM_CONFIG', {
            'openai': {
                'api_key': 'test-key',
                'model': 'gpt-4o-mini',
                'temperature': 0.7,
                'max_tokens': 500
            }
        }):
            client = LLMClient(provider='openai')
            messages = [{"role": "user", "content": "Hello"}]

            # 由于有@retry装饰器，会重试3次后抛出LLMException
            with pytest.raises(LLMException):
                client._call_llm(messages)


class TestGenerateClusterTheme:
    """测试生成聚类主题"""

    @patch('ai.client.OpenAI')
    def test_generate_cluster_theme_success(self, mock_openai):
        """测试成功生成主题"""
        # Mock响应
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"theme": "跑鞋推荐", "confidence": "high"}'

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        with patch('ai.client.LLM_CONFIG', {
            'openai': {
                'api_key': 'test-key',
                'model': 'gpt-4o-mini',
                'temperature': 0.7,
                'max_tokens': 500
            }
        }):
            client = LLMClient(provider='openai')
            result = client.generate_cluster_theme(
                example_phrases=["running shoes", "best running shoes"],
                cluster_size=100,
                cluster_id=1
            )

            assert result['theme'] == "跑鞋推荐"
            assert result['confidence'] == "high"

    @patch('ai.client.OpenAI')
    def test_generate_cluster_theme_invalid_json(self, mock_openai):
        """测试JSON解析失败时的降级处理"""
        # Mock响应（非JSON）
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Just plain text response"

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        with patch('ai.client.LLM_CONFIG', {
            'openai': {
                'api_key': 'test-key',
                'model': 'gpt-4o-mini',
                'temperature': 0.7,
                'max_tokens': 500
            }
        }):
            client = LLMClient(provider='openai')
            result = client.generate_cluster_theme(
                example_phrases=["test"],
                cluster_size=10
            )

            assert result['theme'] == "Just plain text response"
            assert result['confidence'] == "medium"


class TestGenerateDemandCard:
    """测试生成需求卡片"""

    @patch('ai.client.OpenAI')
    def test_generate_demand_card_success(self, mock_openai):
        """测试成功生成需求卡片"""
        # Mock响应
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''{
            "demand_title": "跑步装备需求",
            "demand_description": "用户寻找高质量跑步装备",
            "user_intent": "购买跑鞋",
            "pain_points": ["选择困难", "价格敏感"],
            "target_audience": "跑步爱好者",
            "priority": "high",
            "confidence_score": 85
        }'''

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        with patch('ai.client.LLM_CONFIG', {
            'openai': {
                'api_key': 'test-key',
                'model': 'gpt-4o-mini',
                'temperature': 0.7,
                'max_tokens': 500
            }
        }):
            client = LLMClient(provider='openai')
            result = client.generate_demand_card(
                cluster_id_A=1,
                cluster_id_B=10,
                main_theme="运动装备",
                phrases=["running shoes", "best shoes"],
                total_frequency=1000,
                total_volume=50000
            )

            assert result['demand_title'] == "跑步装备需求"
            assert result['priority'] == "high"
            assert result['confidence_score'] == 85

    @patch('ai.client.OpenAI')
    def test_generate_demand_card_json_failure(self, mock_openai):
        """测试JSON解析失败时的降级处理"""
        # Mock响应（非JSON）
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Invalid JSON response"

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        with patch('ai.client.LLM_CONFIG', {
            'openai': {
                'api_key': 'test-key',
                'model': 'gpt-4o-mini',
                'temperature': 0.7,
                'max_tokens': 500
            }
        }):
            client = LLMClient(provider='openai')
            result = client.generate_demand_card(
                cluster_id_A=1,
                cluster_id_B=10,
                main_theme="测试主题",
                phrases=["test"],
                total_frequency=100,
                total_volume=1000
            )

            # 应该返回默认结构
            assert "需求卡片生成失败" in result['demand_description']
            assert result['confidence_score'] == 50


class TestBatchClassifyTokens:
    """测试批量分类Tokens"""

    @patch('ai.client.OpenAI')
    def test_batch_classify_tokens_success(self, mock_openai):
        """测试成功批量分类"""
        # Mock响应
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''[
            {"token": "best", "token_type": "intent", "confidence": "high"},
            {"token": "shoes", "token_type": "object", "confidence": "high"}
        ]'''

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        with patch('ai.client.LLM_CONFIG', {
            'openai': {
                'api_key': 'test-key',
                'model': 'gpt-4o-mini',
                'temperature': 0.7,
                'max_tokens': 500
            }
        }):
            client = LLMClient(provider='openai')
            results = client.batch_classify_tokens(["best", "shoes"], batch_size=50)

            assert len(results) == 2
            assert results[0]['token'] == "best"
            assert results[0]['token_type'] == "intent"
            assert results[1]['token'] == "shoes"
            assert results[1]['token_type'] == "object"

    @patch('ai.client.OpenAI')
    def test_batch_classify_tokens_failure_fallback(self, mock_openai):
        """测试批次失败时的降级处理"""
        # Mock失败响应
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client

        with patch('ai.client.LLM_CONFIG', {
            'openai': {
                'api_key': 'test-key',
                'model': 'gpt-4o-mini',
                'temperature': 0.7,
                'max_tokens': 500
            }
        }):
            client = LLMClient(provider='openai')
            # 由于有@retry，会重试后最终失败并使用默认分类
            results = client.batch_classify_tokens(["test"], batch_size=50)

            # 应该返回默认分类
            assert len(results) == 1
            assert results[0]['token_type'] == 'other'
            assert results[0]['confidence'] == 'low'
