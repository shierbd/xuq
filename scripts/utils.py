"""
通用工具函数
提供各步骤共用的功能
"""

import logging
import sys
from pathlib import Path
import pandas as pd
from typing import List, Dict, Any, Optional


def setup_logging(log_file: Optional[Path] = None, level: str = "INFO"):
    """
    配置日志系统

    参数:
        log_file: 日志文件路径（None则只输出到控制台）
        level: 日志级别
    """
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    handlers = [logging.StreamHandler(sys.stdout)]

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))

    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        handlers=handlers
    )

    return logging.getLogger(__name__)


def load_csv(file_path: Path, encoding: str = 'utf-8') -> pd.DataFrame:
    """
    加载CSV文件

    参数:
        file_path: 文件路径
        encoding: 编码格式

    返回:
        DataFrame
    """
    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    df = pd.read_csv(file_path, encoding=encoding)
    logging.info(f"已加载文件: {file_path}, 行数: {len(df):,}")

    return df


def save_csv(df: pd.DataFrame, file_path: Path, encoding: str = 'utf-8'):
    """
    保存DataFrame为CSV

    参数:
        df: DataFrame
        file_path: 保存路径
        encoding: 编码格式
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(file_path, index=False, encoding=encoding)
    logging.info(f"已保存文件: {file_path}, 行数: {len(df):,}")


def print_section(title: str, width: int = 60):
    """
    打印章节标题

    参数:
        title: 标题文字
        width: 总宽度
    """
    print("\n" + "=" * width)
    print(title.center(width))
    print("=" * width)


def print_subsection(title: str, width: int = 60):
    """
    打印子章节标题

    参数:
        title: 标题文字
        width: 总宽度
    """
    print("\n" + "-" * width)
    print(title)
    print("-" * width)


def print_stats(df: pd.DataFrame, name: str = "数据"):
    """
    打印DataFrame统计信息

    参数:
        df: DataFrame
        name: 数据名称
    """
    print(f"\n{name}统计:")
    print(f"  总行数: {len(df):,}")
    print(f"  列数: {len(df.columns)}")
    print(f"  列名: {', '.join(df.columns[:5])}" + ("..." if len(df.columns) > 5 else ""))

    # 显示空值统计
    null_counts = df.isnull().sum()
    if null_counts.sum() > 0:
        print(f"\n  空值统计:")
        for col, count in null_counts[null_counts > 0].items():
            print(f"    {col}: {count} ({count/len(df)*100:.1f}%)")


def extract_seed_word(filename: str) -> str:
    """
    从文件名提取种子词

    参数:
        filename: 文件名（如 action_broad-match_us_2025-12-12.csv）

    返回:
        种子词（如 action）
    """
    return filename.split('_')[0]


def check_dependencies():
    """
    检查必要的Python包是否已安装
    """
    required_packages = {
        'pandas': 'pandas',
        'sentence_transformers': 'sentence-transformers',
        'hdbscan': 'hdbscan',
        'sklearn': 'scikit-learn',
        'numpy': 'numpy',
    }

    missing = []

    for module_name, package_name in required_packages.items():
        try:
            __import__(module_name)
        except ImportError:
            missing.append(package_name)

    if missing:
        print("缺少以下依赖包:")
        for pkg in missing:
            print(f"  - {pkg}")
        print("\n请运行: pip install " + " ".join(missing))
        return False

    return True


def format_number(num: float, decimals: int = 1) -> str:
    """
    格式化数字显示

    参数:
        num: 数字
        decimals: 小数位数

    返回:
        格式化后的字符串
    """
    if num >= 1_000_000:
        return f"{num/1_000_000:.{decimals}f}M"
    elif num >= 1_000:
        return f"{num/1_000:.{decimals}f}K"
    else:
        return f"{num:.{decimals}f}"


def validate_config(config: Dict[str, Any], required_keys: List[str]) -> bool:
    """
    验证配置是否包含必要的键

    参数:
        config: 配置字典
        required_keys: 必须存在的键列表

    返回:
        是否有效
    """
    missing = [key for key in required_keys if key not in config]

    if missing:
        logging.error(f"配置缺少必要的键: {missing}")
        return False

    return True
