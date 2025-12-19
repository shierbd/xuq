"""
全局配置文件
包含所有步骤需要的配置参数
"""

import os
from pathlib import Path

# ==================== 路径配置 ====================

# 项目根目录
# Path(__file__).parent.parent = scripts/lib -> scripts -> PROJECT_ROOT
# 但因为scripts是在项目根目录下，所以需要再向上一级
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Data子目录
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_RESULTS_DIR = DATA_DIR / "results"
DATA_BASELINE_DIR = DATA_DIR / "baseline"

# 输入数据路径（外部原始数据）
EXTERNAL_RAW_DATA_DIR = r"C:\Users\32941\Downloads\合并"

# 输出文件路径 - 更新为新的目录结构
MERGED_FILE = DATA_RAW_DIR / "merged_keywords_all.csv"  # A2输出
CLUSTERS_FILE = DATA_PROCESSED_DIR / "stageA_clusters.csv"  # A3输出
CLUSTER_SUMMARY_FILE = DATA_RESULTS_DIR / "clusters_summary_stageA.csv"  # A3输出
CLUSTER_INSIGHTS_FILE = DATA_RESULTS_DIR / "cluster_insights_stageA.csv"  # A4输出
DIRECTION_KEYWORDS_FILE = DATA_RESULTS_DIR / "direction_keywords.csv"  # A5输出

# 创建必要的目录
for dir_path in [DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_RESULTS_DIR, DATA_BASELINE_DIR, OUTPUT_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# ==================== 步骤A2：合并配置 ====================

A2_CONFIG = {
    "input_folder": EXTERNAL_RAW_DATA_DIR,
    "output_file": "merged_keywords_all.csv",
    "file_pattern": "*_broad-match_*.csv",  # 匹配所有broad-match文件
    "encoding": "utf-8",

    # 数据量控制（重要！避免数据爆炸）
    "max_phrases_per_seed": 150,  # 每个种子词最多抓取多少条短语（推荐 100-200）
    # 首次运行建议：5-10个种子词，每个100条
}

# ==================== 步骤A3：聚类配置 ====================

A3_CONFIG = {
    # 输入文件
    "input_file": MERGED_FILE,

    # 输出文件
    "output_clusters": CLUSTERS_FILE,
    "output_summary": CLUSTER_SUMMARY_FILE,

    # Embedding模型配置
    "embedding_model": "all-MiniLM-L6-v2",  # 轻量快速
    # 其他可选模型：
    # "paraphrase-multilingual-MiniLM-L12-v2"  # 多语言
    # "all-mpnet-base-v2"  # 更高质量，但更慢

    # 聚类参数
    "clustering_method": "hdbscan",  # hdbscan 或 kmeans
    "min_cluster_size": 30,  # HDBSCAN: 每个簇最小样本数（针对55K数据优化）
    "min_samples": 3,  # HDBSCAN: 核心点需要的最小邻居数（从2改为3）
    "n_clusters": 50,  # KMeans: 簇数量（仅在method=kmeans时使用）
    # 📝 参数调优说明：
    #   - 对于 55,278 条短语，min_cluster_size=30 预期生成 60-100 个簇
    #   - 如果簇还是太多（>100），继续增大到 40-50
    #   - 如果簇太少（<40），减小到 20-25
    #   - 之前用动态计算得到111太大，导致只有2个簇

    # 动态参数配置（A3.3新增）
    "use_dynamic_params": False,  # 禁用动态计算，使用固定值30
    # 说明：对于大数据集（>50K），动态公式N/500会导致参数过大
    #       固定使用30可以获得更合理的簇粒度

    # 数据预处理
    "min_volume": 0,  # 最小搜索量（0=不过滤）
    "max_phrases": None,  # 最大处理短语数（None=不限制）

    # 性能配置
    "batch_size": 32,  # embedding批处理大小
    "use_gpu": False,  # 是否使用GPU（需要CUDA支持）
}

# ==================== 步骤A4：LLM配置 ====================

A4_CONFIG = {
    # 输入文件
    "input_clusters": CLUSTERS_FILE,
    "input_summary": CLUSTER_SUMMARY_FILE,

    # 输出文件
    "output_insights": CLUSTER_INSIGHTS_FILE,

    # LLM提供商（openai / anthropic / deepseek）
    "llm_provider": "openai",

    # OpenAI配置
    "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
    "openai_model": "gpt-4o-mini",  # gpt-4o-mini / gpt-4o
    "openai_base_url": None,  # 可选：自定义API端点

    # Anthropic配置
    "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY", ""),
    "anthropic_model": "claude-3-haiku-20240307",

    # DeepSeek配置
    "deepseek_api_key": os.getenv("DEEPSEEK_API_KEY", ""),
    "deepseek_model": "deepseek-chat",

    # 批处理配置
    "batch_size": 5,  # 每批处理的簇数量
    "max_samples_per_cluster": 50,  # 每个簇最多取多少条样本
    "retry_times": 3,  # API调用失败重试次数
}

# ==================== 步骤A5：方向筛选配置 ====================

A5_CONFIG = {
    # 输入文件
    "input_insights": CLUSTER_INSIGHTS_FILE,

    # 输出文件
    "output_directions": DIRECTION_KEYWORDS_FILE,

    # 筛选阈值
    "min_total_frequency": 10,  # 簇的总频次
    "min_cluster_size": 3,  # 簇的最小样本数
    "max_directions": 20,  # 最多保留多少个方向

    # Google Trends配置（可选）
    "enable_trends": False,  # 是否启用Trends验证
    "min_trends_score": 10,  # 最小Trends分数
}

# ==================== 阶段B配置 ====================

B1_CONFIG = {}  # 待补充
B2_CONFIG = {}  # 待补充

# ==================== 日志配置 ====================

LOGGING_CONFIG = {
    "level": "INFO",  # DEBUG / INFO / WARNING / ERROR
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "log_file": OUTPUT_DIR / "execution.log",
}

# ==================== 通用配置 ====================

GENERAL_CONFIG = {
    "random_seed": 42,  # 随机种子，确保可复现
    "verbose": True,  # 是否显示详细输出
}
