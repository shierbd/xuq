"""
统一日志模块
提供全局日志配置和便捷的logger获取方法
"""
import logging
import logging.config
from pathlib import Path
from config.settings import LOG_CONFIG, LOG_DIR


def setup_logging():
    """初始化日志配置"""
    # 确保日志目录存在
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # 应用日志配置
    logging.config.dictConfig(LOG_CONFIG)


def get_logger(name: str) -> logging.Logger:
    """
    获取logger实例

    Args:
        name: logger名称，通常使用 __name__

    Returns:
        Logger实例

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing started")
    """
    return logging.getLogger(name)


# 全局初始化
setup_logging()
