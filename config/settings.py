"""
MVP版本配置文件
统一管理数据库、聚类、LLM等配置
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ==================== 项目路径 ====================
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
OUTPUT_DIR = DATA_DIR / "output"
CACHE_DIR = DATA_DIR / "cache"

# 确保目录存在
CACHE_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ==================== 数据库配置 ====================
# MVP阶段推荐使用 MySQL / MariaDB
DATABASE_CONFIG = {
    "type": os.getenv("DB_TYPE", "mysql"),  # mysql 或 sqlite
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "database": os.getenv("DB_NAME", "keyword_clustering"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "charset": "utf8mb4",
}

# SQLAlchemy连接字符串
if DATABASE_CONFIG["type"] == "mysql":
    DATABASE_URL = (
        f"mysql+pymysql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}"
        f"@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"
        f"?charset={DATABASE_CONFIG['charset']}"
    )
else:  # sqlite
    DATABASE_URL = f"sqlite:///{DATA_DIR / 'keywords.db'}"

# ==================== Embedding配置 ====================
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_MODEL_VERSION = "2.2.0"
EMBEDDING_DIM = 384
EMBEDDING_BATCH_SIZE = 256

# Embedding缓存
EMBEDDING_CACHE_FILE = CACHE_DIR / "embeddings_round{round_id}.npz"
MODEL_VERSION_FILE = CACHE_DIR / "model_version.txt"

# ==================== 聚类配置 ====================
# 大组聚类参数（Phase 2）
LARGE_CLUSTER_CONFIG = {
    "min_cluster_size": 30,  # 最小聚类大小
    "min_samples": 3,        # 最小样本数
    "metric": "cosine",      # 距离度量
    "cluster_selection_epsilon": 0.0,
    "cluster_selection_method": "eom",
}

# 小组聚类参数（Phase 4）
SMALL_CLUSTER_CONFIG = {
    "min_cluster_size": 5,   # 小组允许更小
    "min_samples": 2,
    "metric": "cosine",
    "cluster_selection_epsilon": 0.0,
}

# 增量更新：新短语分配到大组的KNN参数
INCREMENTAL_KNN_K = 5
INCREMENTAL_DISTANCE_THRESHOLD = 0.5  # 余弦距离阈值

# ==================== LLM配置 ====================
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # openai, anthropic, deepseek

LLM_CONFIG = {
    "openai": {
        "api_key": os.getenv("OPENAI_API_KEY", ""),
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        "temperature": 0.3,
        "max_tokens": 2000,
    },
    "anthropic": {
        "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
        "model": os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
        "temperature": 0.3,
        "max_tokens": 2000,
    },
    "deepseek": {
        "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
        "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        "temperature": 0.3,
        "max_tokens": 2000,
    },
}

# ==================== 数据源配置 ====================
DATA_SOURCES = {
    "semrush": {
        "dir": RAW_DATA_DIR / "semrush",
        "pattern": "*.csv",
        "source_type": "semrush",
    },
    "dropdown": {
        "dir": RAW_DATA_DIR / "dropdown",
        "pattern": "*.csv",
        "source_type": "dropdown",
    },
    "related_search": {
        "dir": RAW_DATA_DIR / "related_search",
        "pattern": "*.xlsx",
        "source_type": "related_search",
    },
}

# ==================== Phase 3: 大组筛选配置 ====================
# 生成报告时每个大组展示的示例短语数量
CLUSTER_EXAMPLE_PHRASES_COUNT = 10

# 大组筛选阈值
CLUSTER_SELECTION_THRESHOLD = 4  # selection_score >= 4 表示选中

# ==================== Phase 4: 需求卡片配置 ====================
# 每个小组生成需求卡片时提供的短语样本数量
DEMAND_CARD_PHRASE_SAMPLE_SIZE = 20

# ==================== Phase 5: Tokens配置 ====================
# Token分类类型
TOKEN_TYPES = ["intent", "action", "object", "attribute", "condition", "other"]

# Token提取最小频次
TOKEN_MIN_FREQUENCY = 3

# ==================== 增量更新配置 ====================
# 低频噪音阈值（频次低于此值且cluster_id_A=-1会被archived）
LOW_FREQUENCY_THRESHOLD = 10

# 需求状态：已稳定不再处理
STABLE_DEMAND_STATUS = ["validated", "in_progress", "launched", "profitable"]

# ==================== 日志配置 ====================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": LOG_LEVEL,
            "formatter": "standard",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.FileHandler",
            "level": LOG_LEVEL,
            "formatter": "standard",
            "filename": LOG_DIR / "mvp.log",
            "mode": "a",
            "encoding": "utf-8",
        },
    },
    "root": {
        "level": LOG_LEVEL,
        "handlers": ["console", "file"]
    },
}

# ==================== 版本信息 ====================
MVP_VERSION = "1.0"
LAST_UPDATED = "2024-12-19"
