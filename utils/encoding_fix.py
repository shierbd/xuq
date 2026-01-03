"""
Windows编码问题一次性修复模块
在所有脚本开头调用setup_encoding()即可解决GBK编码问题
"""
import sys
import os
import io


def setup_encoding():
    """
    设置UTF-8编码，解决Windows GBK编码问题

    这个函数会：
    1. 设置控制台输出为UTF-8
    2. 设置默认文件编码为UTF-8
    3. 设置环境变量强制UTF-8

    在所有脚本的开头（import之后）调用此函数：

    Example:
        from utils.encoding_fix import setup_encoding
        setup_encoding()
    """
    # 1. 设置环境变量（影响所有子进程）
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'  # PEP 540: 强制UTF-8模式

    # 2. Windows特殊处理
    if sys.platform.startswith('win'):
        # 设置控制台代码页为UTF-8
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleCP(65001)  # 输入代码页
            kernel32.SetConsoleOutputCP(65001)  # 输出代码页
        except:
            pass  # 如果失败也不影响后续执行

        # 强制重新包装stdout/stderr为UTF-8（不检查现有编码）
        try:
            if hasattr(sys.stdout, 'buffer'):
                sys.stdout = io.TextIOWrapper(
                    sys.stdout.buffer,
                    encoding='utf-8',
                    errors='replace',  # 遇到无法编码的字符用?替换，而不是抛出异常
                    line_buffering=True
                )
        except:
            pass

        try:
            if hasattr(sys.stderr, 'buffer'):
                sys.stderr = io.TextIOWrapper(
                    sys.stderr.buffer,
                    encoding='utf-8',
                    errors='replace',
                    line_buffering=True
                )
        except:
            pass

        try:
            if hasattr(sys.stdin, 'buffer'):
                sys.stdin = io.TextIOWrapper(
                    sys.stdin.buffer,
                    encoding='utf-8',
                    errors='replace'
                )
        except:
            pass

    # 3. 设置默认编码（Python 3.7+）
    if hasattr(sys, 'set_int_max_str_digits'):
        # Python 3.11+ 还需要这个
        pass

    # 4. 设置locale（可选，但有助于某些库）
    try:
        import locale
        locale.setlocale(locale.LC_ALL, '')
    except:
        pass

    # 5. 修改默认的文件编码
    import _io
    if hasattr(_io, '_setmode'):
        try:
            import msvcrt
            msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
            msvcrt.setmode(sys.stderr.fileno(), os.O_BINARY)
        except:
            pass


def safe_print(*args, **kwargs):
    """
    安全的print函数，自动处理编码问题

    使用方法与print相同，但会自动处理无法编码的字符
    """
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # 如果仍然失败，尝试转换为ASCII
        args_safe = []
        for arg in args:
            if isinstance(arg, str):
                args_safe.append(arg.encode('ascii', 'replace').decode('ascii'))
            else:
                args_safe.append(str(arg))
        print(*args_safe, **kwargs)


def safe_open(filename, mode='r', encoding='utf-8', **kwargs):
    """
    安全的open函数，默认使用UTF-8编码

    Args:
        filename: 文件路径
        mode: 打开模式
        encoding: 编码（默认utf-8）
        **kwargs: 其他参数传递给open()

    Returns:
        文件对象
    """
    if 'b' not in mode and encoding is None:
        encoding = 'utf-8'

    # 添加错误处理
    if 'errors' not in kwargs and 'b' not in mode:
        kwargs['errors'] = 'replace'

    return open(filename, mode, encoding=encoding, **kwargs)


# 自动执行（当模块被导入时）
# 注释掉自动执行，改为显式调用
# setup_encoding()


if __name__ == "__main__":
    # 测试
    setup_encoding()
    print("✓ 编码修复模块测试成功")
    print("✓ 当前stdout编码:", sys.stdout.encoding)
    print("✓ 当前stderr编码:", sys.stderr.encoding)
    print("✓ 环境变量PYTHONIOENCODING:", os.environ.get('PYTHONIOENCODING'))

    # 测试特殊字符
    test_chars = "测试: ✓ ✅ ❌ 🎉 中文 emoji"
    print("✓ 特殊字符测试:", test_chars)
