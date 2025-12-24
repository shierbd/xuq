"""
测试配置和共享fixtures
"""
import pytest
import numpy as np
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def sample_embeddings():
    """示例embeddings数据"""
    np.random.seed(42)
    # 3个簇 + 噪音
    cluster1 = np.random.randn(30, 10) + np.array([5, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    cluster2 = np.random.randn(25, 10) + np.array([-5, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    cluster3 = np.random.randn(20, 10) + np.array([0, 5, 0, 0, 0, 0, 0, 0, 0, 0])
    noise = np.random.randn(5, 10) * 10

    return np.vstack([cluster1, cluster2, cluster3, noise])


@pytest.fixture
def sample_phrases():
    """示例短语数据"""
    phrases = []
    for i in range(80):
        phrases.append({
            'phrase_id': i + 1,
            'phrase': f'test phrase {i}',
            'frequency': np.random.randint(1, 100),
            'volume': np.random.randint(0, 1000),
            'seed_word': 'test',
            'source_type': 'semrush'
        })
    return phrases


@pytest.fixture
def mock_llm_response():
    """模拟LLM响应"""
    def _mock_response(response_type='theme'):
        if response_type == 'theme':
            return '{"theme": "测试主题", "confidence": "high"}'
        elif response_type == 'demand':
            return '''{
                "demand_title": "测试需求",
                "demand_description": "这是一个测试需求描述",
                "user_intent": "用户想要测试功能",
                "pain_points": ["痛点1", "痛点2"],
                "target_audience": "测试用户",
                "priority": "medium",
                "confidence_score": 75
            }'''
        elif response_type == 'token':
            return '[{"token": "test", "token_type": "object", "confidence": "high"}]'
    return _mock_response
