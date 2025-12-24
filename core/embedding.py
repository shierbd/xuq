"""
Embedding服务模块
使用Sentence Transformers进行文本向量化，支持缓存
"""
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import hashlib
from tqdm import tqdm
import torch

from sentence_transformers import SentenceTransformer
from config.settings import (
    EMBEDDING_MODEL,
    EMBEDDING_MODEL_VERSION,
    EMBEDDING_DIM,
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_CACHE_FILE,
    MODEL_VERSION_FILE,
    CACHE_DIR
)
from utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """文本向量化服务"""

    def __init__(self, model_name: str = EMBEDDING_MODEL, use_cache: bool = True, device: str = None):
        """
        初始化Embedding服务

        Args:
            model_name: 模型名称
            use_cache: 是否使用缓存
            device: 计算设备 ('cuda', 'cpu', None=自动检测)
        """
        # 自动检测GPU
        if device is None:
            if torch.cuda.is_available():
                device = 'cuda'
                gpu_name = torch.cuda.get_device_name(0)
                logger.info(f"检测到GPU: {gpu_name}")
            else:
                device = 'cpu'
                logger.info("使用CPU计算")

        self.device = device
        self.model_name = model_name
        self.use_cache = use_cache
        self.model = None
        self.cache = {}
        self.cache_file = None

        logger.info(f"初始化Embedding服务 - 模型: {model_name}, 版本: {EMBEDDING_MODEL_VERSION}, "
                   f"维度: {EMBEDDING_DIM}, 批次大小: {EMBEDDING_BATCH_SIZE}, "
                   f"缓存: {'启用' if use_cache else '禁用'}, 设备: {device}")

    def load_model(self):
        """加载Sentence Transformer模型"""
        if self.model is None:
            logger.info(f"加载Sentence Transformer模型到 {self.device}...")
            try:
                self.model = SentenceTransformer(self.model_name)
                self.model = self.model.to(self.device)
                logger.info("模型加载成功")
            except Exception as e:
                logger.error(f"模型加载失败: {str(e)}")
                raise

    def _get_cache_key(self, text: str) -> str:
        """
        生成缓存键（文本的MD5哈希）

        Args:
            text: 输入文本

        Returns:
            MD5哈希字符串
        """
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def _save_model_version(self):
        """保存模型版本信息"""
        CACHE_DIR.mkdir(exist_ok=True)
        with open(MODEL_VERSION_FILE, 'w', encoding='utf-8') as f:
            f.write(f"{self.model_name}\n")
            f.write(f"{EMBEDDING_MODEL_VERSION}\n")
            f.write(f"{EMBEDDING_DIM}\n")

    def _check_model_version(self) -> bool:
        """
        检查缓存的模型版本是否匹配

        Returns:
            是否匹配
        """
        if not MODEL_VERSION_FILE.exists():
            return False

        try:
            with open(MODEL_VERSION_FILE, 'r', encoding='utf-8') as f:
                cached_model = f.readline().strip()
                cached_version = f.readline().strip()
                cached_dim = f.readline().strip()

            return (cached_model == self.model_name and
                    cached_version == EMBEDDING_MODEL_VERSION and
                    cached_dim == str(EMBEDDING_DIM))
        except Exception:
            return False

    def load_cache(self, round_id: int = 1):
        """
        加载缓存的embeddings

        Args:
            round_id: 轮次ID
        """
        self.cache_file = Path(str(EMBEDDING_CACHE_FILE).format(round_id=round_id))

        if not self.use_cache:
            logger.warning("缓存已禁用")
            return

        # 检查模型版本
        if not self._check_model_version():
            logger.warning("模型版本不匹配，将重新生成embeddings")
            self.cache = {}
            return

        # 加载缓存
        if self.cache_file.exists():
            logger.info(f"加载embedding缓存: {self.cache_file.name}")
            try:
                data = np.load(self.cache_file, allow_pickle=True)
                self.cache = data['cache'].item()
                logger.info(f"已加载 {len(self.cache)} 个缓存embeddings")
            except Exception as e:
                logger.warning(f"缓存加载失败: {str(e)}")
                self.cache = {}
        else:
            logger.info(f"缓存文件不存在，将创建新缓存")
            self.cache = {}

    def save_cache(self):
        """保存embeddings缓存"""
        if not self.use_cache or self.cache_file is None:
            return

        logger.info("保存embedding缓存...")
        CACHE_DIR.mkdir(exist_ok=True)

        try:
            np.savez_compressed(
                self.cache_file,
                cache=self.cache
            )
            # 保存模型版本
            self._save_model_version()
            logger.info(f"已保存 {len(self.cache)} 个embeddings到 {self.cache_file.name}")
        except Exception as e:
            logger.warning(f"缓存保存失败: {str(e)}")

    def embed_texts(self, texts: List[str], show_progress: bool = True) -> np.ndarray:
        """
        批量计算文本embeddings（支持缓存）

        Args:
            texts: 文本列表
            show_progress: 是否显示进度条

        Returns:
            embeddings矩阵 (n_texts, embedding_dim)
        """
        # 确保模型已加载
        if self.model is None:
            self.load_model()

        logger.info("计算embeddings...")
        logger.info(f"文本数量: {len(texts)}")

        # 检查缓存
        embeddings = []
        texts_to_compute = []
        indices_to_compute = []

        for idx, text in enumerate(texts):
            cache_key = self._get_cache_key(text)
            if cache_key in self.cache:
                embeddings.append(self.cache[cache_key])
            else:
                embeddings.append(None)
                texts_to_compute.append(text)
                indices_to_compute.append(idx)

        cached_count = len(texts) - len(texts_to_compute)
        if cached_count > 0:
            logger.info(f"缓存命中: {cached_count}/{len(texts)} ({cached_count/len(texts)*100:.1f}%)")

        # 计算未缓存的embeddings
        if texts_to_compute:
            logger.info(f"需要计算: {len(texts_to_compute)}")

            new_embeddings = []
            batch_size = EMBEDDING_BATCH_SIZE

            iterator = range(0, len(texts_to_compute), batch_size)
            if show_progress:
                iterator = tqdm(iterator, desc="计算embeddings")

            for i in iterator:
                batch = texts_to_compute[i:i + batch_size]
                batch_embeddings = self.model.encode(
                    batch,
                    batch_size=batch_size,
                    show_progress_bar=False,
                    convert_to_numpy=True
                )
                new_embeddings.append(batch_embeddings)

            new_embeddings = np.vstack(new_embeddings)

            # 更新缓存和结果
            for idx, text_idx in enumerate(indices_to_compute):
                embedding = new_embeddings[idx]
                cache_key = self._get_cache_key(texts[text_idx])
                self.cache[cache_key] = embedding
                embeddings[text_idx] = embedding

        # 转换为numpy数组
        embeddings = np.array(embeddings)

        logger.info(f"Embeddings计算完成: {embeddings.shape}")
        return embeddings

    def embed_phrases_from_db(self, phrases: List[Dict], round_id: int = 1) -> Tuple[np.ndarray, List[int]]:
        """
        从数据库短语列表计算embeddings

        Args:
            phrases: 短语字典列表（包含phrase和phrase_id）
            round_id: 轮次ID

        Returns:
            (embeddings矩阵, phrase_id列表)
        """
        logger.info("=" * 70)
        logger.info("开始计算短语Embeddings")
        logger.info("=" * 70)

        # 加载缓存
        self.load_cache(round_id)

        # 提取文本和ID
        texts = [p['phrase'] for p in phrases]
        phrase_ids = [p['phrase_id'] for p in phrases]

        # 计算embeddings
        embeddings = self.embed_texts(texts, show_progress=True)

        # 保存缓存
        self.save_cache()

        logger.info("=" * 70)
        logger.info("Embeddings计算完成")
        logger.info("=" * 70)

        return embeddings, phrase_ids


def test_embedding_service():
    """测试embedding服务"""
    print("\n" + "="*70)
    print("测试Embedding服务")
    print("="*70)

    # 测试数据
    test_texts = [
        "how to change a tire",
        "image search techniques",
        "best connector for automotive wiring",
        "tattoo design ideas",
        "python programming tutorial",
    ]

    # 创建服务
    service = EmbeddingService(use_cache=True)

    # 第一次计算（应该没有缓存）
    print("\n【第一次计算】")
    service.load_cache(round_id=999)
    embeddings1 = service.embed_texts(test_texts)
    service.save_cache()

    print(f"\nEmbeddings形状: {embeddings1.shape}")
    print(f"第一个embedding前5维: {embeddings1[0][:5]}")

    # 第二次计算（应该全部命中缓存）
    print("\n【第二次计算（测试缓存）】")
    service2 = EmbeddingService(use_cache=True)
    service2.load_cache(round_id=999)
    embeddings2 = service2.embed_texts(test_texts)

    # 验证结果一致
    assert np.allclose(embeddings1, embeddings2), "缓存embeddings不一致！"
    print("\n✅ 缓存功能测试通过！")

    # 计算相似度
    print("\n【相似度测试】")
    from sklearn.metrics.pairwise import cosine_similarity
    similarities = cosine_similarity(embeddings1)

    print("\n短语相似度矩阵:")
    for i, text in enumerate(test_texts):
        print(f"\n{text}:")
        for j, other_text in enumerate(test_texts):
            if i != j:
                sim = similarities[i][j]
                print(f"  vs {other_text}: {sim:.3f}")

    print("\n" + "="*70)
    print("测试完成")
    print("="*70)


if __name__ == "__main__":
    test_embedding_service()
