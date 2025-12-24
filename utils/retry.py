"""
重试装饰器和工具函数
用于处理临时性失败（网络问题、API限流等）
"""
import time
import functools
from typing import Callable, Type, Tuple
from utils.logger import get_logger

logger = get_logger(__name__)


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    重试装饰器

    Args:
        max_attempts: 最大尝试次数
        delay: 初始延迟时间（秒）
        backoff: 延迟时间的倍数因子
        exceptions: 需要重试的异常类型元组

    Example:
        >>> @retry(max_attempts=3, delay=1, exceptions=(ConnectionError,))
        >>> def call_api():
        >>>     ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.error(
                            f"{func.__name__} 失败，已重试 {max_attempts} 次: {str(e)}"
                        )
                        raise

                    logger.warning(
                        f"{func.__name__} 第 {attempt} 次尝试失败: {str(e)}. "
                        f"{current_delay:.1f}秒后重试..."
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff

            # 不应到达这里，但为了类型检查器满意
            raise last_exception

        return wrapper
    return decorator


def safe_execute(func: Callable, default_value=None, log_error: bool = True):
    """
    安全执行函数，捕获异常并返回默认值

    Args:
        func: 要执行的函数
        default_value: 异常时返回的默认值
        log_error: 是否记录错误日志

    Returns:
        函数返回值或默认值

    Example:
        >>> result = safe_execute(lambda: risky_operation(), default_value=[])
    """
    try:
        return func()
    except Exception as e:
        if log_error:
            logger.error(f"执行 {func.__name__ if hasattr(func, '__name__') else 'function'} 时出错: {str(e)}")
        return default_value
