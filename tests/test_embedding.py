"""
Embedding服务测试
"""
import pytest
import numpy as np
from core.embedding import EmbeddingService


class TestEmbeddingService:
    """测试EmbeddingService类"""

    def test_init_cpu(self):
        """测试CPU初始化"""
        service = EmbeddingService(use_cache=False, device='cpu')
        assert service.model_name == "all-MiniLM-L6-v2"
        assert service.use_cache == False
        assert service.device == 'cpu'

    def test_init_with_cache(self):
        """测试启用缓存初始化"""
        service = EmbeddingService(use_cache=True)
        assert service.use_cache == True
        assert service.cache == {}

    def test_cache_key_generation(self):
        """测试缓存键生成"""
        service = EmbeddingService(use_cache=False)
        key1 = service._get_cache_key("test")
        key2 = service._get_cache_key("test")
        key3 = service._get_cache_key("different")

        assert key1 == key2  # 相同文本应生成相同键
        assert key1 != key3  # 不同文本应生成不同键
        assert len(key1) == 32  # MD5哈希长度为32

    @pytest.mark.slow
    def test_embed_texts_basic(self):
        """测试基本文本向量化"""
        service = EmbeddingService(use_cache=False, device='cpu')
        texts = ["hello world", "machine learning"]
        embeddings = service.embed_texts(texts, show_progress=False)

        assert embeddings.shape == (2, 384)  # all-MiniLM-L6-v2 维度为384
        assert embeddings.dtype == np.float32

    @pytest.mark.slow
    def test_embed_texts_with_cache(self):
        """测试缓存功能"""
        service = EmbeddingService(use_cache=True, device='cpu')
        texts = ["test phrase for caching"]

        # 第一次计算
        emb1 = service.embed_texts(texts, show_progress=False)

        # 手动添加到缓存
        cache_key = service._get_cache_key(texts[0])
        assert cache_key in service.cache

        # 第二次应该命中缓存
        emb2 = service.embed_texts(texts, show_progress=False)

        np.testing.assert_array_almost_equal(emb1, emb2)

    @pytest.mark.slow
    def test_embed_texts_batch(self):
        """测试批量文本向量化"""
        service = EmbeddingService(use_cache=False, device='cpu')
        texts = [f"test text {i}" for i in range(10)]
        embeddings = service.embed_texts(texts, show_progress=False)

        assert embeddings.shape == (10, 384)
        assert not np.any(np.isnan(embeddings))  # 没有NaN值

    def test_model_version_check(self):
        """测试模型版本检查"""
        service = EmbeddingService(use_cache=False)

        # 没有版本文件时应返回False
        is_match = service._check_model_version()
        assert isinstance(is_match, bool)

    @pytest.mark.slow
    def test_embed_phrases_from_db_format(self):
        """测试数据库格式的短语向量化"""
        service = EmbeddingService(use_cache=False, device='cpu')

        phrases = [
            {'phrase_id': 1, 'phrase': 'test phrase 1'},
            {'phrase_id': 2, 'phrase': 'test phrase 2'},
        ]

        embeddings, phrase_ids = service.embed_phrases_from_db(phrases, round_id=999)

        assert embeddings.shape == (2, 384)
        assert phrase_ids == [1, 2]

    @pytest.mark.slow
    def test_similarity_coherence(self):
        """测试相似文本的向量相似度"""
        service = EmbeddingService(use_cache=False, device='cpu')

        # 相似的文本
        texts = [
            "running shoes for women",
            "women's running shoes",
            "cat food recipes"
        ]

        embeddings = service.embed_texts(texts, show_progress=False)

        # 计算余弦相似度
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = cosine_similarity(embeddings)

        # 前两个文本应该比第三个更相似
        sim_0_1 = similarities[0][1]
        sim_0_2 = similarities[0][2]

        assert sim_0_1 > sim_0_2  # 相似文本的相似度应该更高
        assert sim_0_1 > 0.5  # 相似文本的相似度应该足够高


class TestEmbeddingEdgeCases:
    """测试边界情况"""

    @pytest.mark.slow
    def test_empty_list(self):
        """测试空列表"""
        service = EmbeddingService(use_cache=False, device='cpu')
        embeddings = service.embed_texts([], show_progress=False)

        assert embeddings.shape[0] == 0

    @pytest.mark.slow
    def test_single_text(self):
        """测试单个文本"""
        service = EmbeddingService(use_cache=False, device='cpu')
        embeddings = service.embed_texts(["single text"], show_progress=False)

        assert embeddings.shape == (1, 384)

    @pytest.mark.slow
    def test_special_characters(self):
        """测试特殊字符"""
        service = EmbeddingService(use_cache=False, device='cpu')
        texts = ["text with emoji 😀", "text with symbols !@#$%"]
        embeddings = service.embed_texts(texts, show_progress=False)

        assert embeddings.shape == (2, 384)
        assert not np.any(np.isnan(embeddings))
