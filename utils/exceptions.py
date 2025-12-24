"""
自定义异常类
统一错误处理
"""


class MVPBaseException(Exception):
    """MVP系统基础异常类"""
    pass


class DatabaseException(MVPBaseException):
    """数据库相关异常"""
    pass


class EmbeddingException(MVPBaseException):
    """Embedding计算相关异常"""
    pass


class ClusteringException(MVPBaseException):
    """聚类相关异常"""
    pass


class LLMException(MVPBaseException):
    """LLM调用相关异常"""
    pass


class ConfigurationException(MVPBaseException):
    """配置错误异常"""
    pass


class DataValidationException(MVPBaseException):
    """数据验证异常"""
    pass
