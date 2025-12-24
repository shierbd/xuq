"""
测试工具模块
"""
import pytest
from utils.logger import get_logger, setup_logging
from utils.retry import retry, safe_execute
from utils.exceptions import MVPBaseException, LLMException


class TestLogger:
    """测试日志模块"""

    def test_get_logger(self):
        """测试获取logger"""
        logger = get_logger(__name__)
        assert logger is not None
        assert logger.name == __name__

    def test_logger_levels(self):
        """测试不同日志级别"""
        logger = get_logger('test_logger')

        # 这些不应该抛出异常
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")


class TestRetry:
    """测试重试装饰器"""

    def test_retry_success(self):
        """测试成功执行（无需重试）"""
        call_count = []

        @retry(max_attempts=3, delay=0.01)
        def successful_func():
            call_count.append(1)
            return "success"

        result = successful_func()
        assert result == "success"
        assert len(call_count) == 1

    def test_retry_failure_then_success(self):
        """测试失败后成功"""
        call_count = []

        @retry(max_attempts=3, delay=0.01, exceptions=(ValueError,))
        def failing_then_success():
            call_count.append(1)
            if len(call_count) < 2:
                raise ValueError("Temporary failure")
            return "success"

        result = failing_then_success()
        assert result == "success"
        assert len(call_count) == 2

    def test_retry_max_attempts_exceeded(self):
        """测试超过最大重试次数"""
        call_count = []

        @retry(max_attempts=3, delay=0.01, exceptions=(ValueError,))
        def always_fails():
            call_count.append(1)
            raise ValueError("Permanent failure")

        with pytest.raises(ValueError):
            always_fails()

        assert len(call_count) == 3


class TestSafeExecute:
    """测试安全执行函数"""

    def test_safe_execute_success(self):
        """测试成功执行"""
        result = safe_execute(lambda: 1 + 1, default_value=0)
        assert result == 2

    def test_safe_execute_failure(self):
        """测试失败时返回默认值"""
        def failing_func():
            raise ValueError("Error")

        result = safe_execute(failing_func, default_value="default")
        assert result == "default"


class TestExceptions:
    """测试自定义异常"""

    def test_base_exception(self):
        """测试基础异常"""
        with pytest.raises(MVPBaseException):
            raise MVPBaseException("Test error")

    def test_llm_exception(self):
        """测试LLM异常"""
        with pytest.raises(LLMException):
            raise LLMException("LLM API error")

    def test_exception_inheritance(self):
        """测试异常继承关系"""
        assert issubclass(LLMException, MVPBaseException)
        assert issubclass(MVPBaseException, Exception)
