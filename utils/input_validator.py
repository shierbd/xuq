# -*- coding: utf-8 -*-
"""
输入验证工具
用于验证CSV文件、用户输入等，防止安全风险
"""
from pathlib import Path
from typing import Optional, Tuple
import pandas as pd


# 配置常量
MAX_CSV_SIZE_MB = 100  # CSV文件最大大小（MB）
MAX_CSV_ROWS = 1_000_000  # CSV最大行数
ALLOWED_CSV_EXTENSIONS = {'.csv', '.CSV'}


def validate_csv_file(
    file_path: Path,
    max_size_mb: int = MAX_CSV_SIZE_MB,
    max_rows: int = MAX_CSV_ROWS,
    required_columns: Optional[list] = None
) -> Tuple[bool, str]:
    """
    验证CSV文件的安全性和有效性

    Args:
        file_path: CSV文件路径
        max_size_mb: 最大文件大小（MB）
        max_rows: 最大行数
        required_columns: 必需的列名列表

    Returns:
        (是否通过, 错误消息)
    """
    # 1. 检查文件是否存在
    if not file_path.exists():
        return False, f"文件不存在: {file_path}"

    # 2. 检查文件扩展名
    if file_path.suffix.lower() not in ALLOWED_CSV_EXTENSIONS:
        return False, f"不支持的文件类型: {file_path.suffix}。仅支持 .csv 文件"

    # 3. 检查文件大小
    file_size_mb = file_path.stat().st_size / (1024 * 1024)
    if file_size_mb > max_size_mb:
        return False, f"文件过大: {file_size_mb:.1f}MB（最大允许 {max_size_mb}MB）"

    # 4. 尝试读取CSV
    try:
        # 先只读取前几行检查格式
        df_sample = pd.read_csv(file_path, encoding='utf-8-sig', nrows=5)
    except UnicodeDecodeError:
        # 尝试其他编码
        try:
            df_sample = pd.read_csv(file_path, encoding='gbk', nrows=5)
        except Exception as e:
            return False, f"无法读取CSV文件（编码错误）: {str(e)}"
    except Exception as e:
        return False, f"无法读取CSV文件: {str(e)}"

    # 5. 检查必需列
    if required_columns:
        missing_columns = [col for col in required_columns if col not in df_sample.columns]
        if missing_columns:
            return False, f"CSV文件缺少必需列: {', '.join(missing_columns)}"

    # 6. 检查行数（使用行计数器，不加载全部数据）
    try:
        # 快速行数统计
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            row_count = sum(1 for _ in f) - 1  # 减去表头

        if row_count > max_rows:
            return False, f"文件行数过多: {row_count:,}行（最大允许 {max_rows:,}行）"

        if row_count == 0:
            return False, "CSV文件为空（没有数据行）"

    except Exception as e:
        # 如果快速统计失败，使用pandas统计（较慢）
        try:
            df_full = pd.read_csv(file_path, encoding='utf-8-sig')
            if len(df_full) > max_rows:
                return False, f"文件行数过多: {len(df_full):,}行（最大允许 {max_rows:,}行）"
            if len(df_full) == 0:
                return False, "CSV文件为空（没有数据行）"
        except Exception as e2:
            return False, f"无法统计文件行数: {str(e2)}"

    # 所有检查通过
    return True, "验证通过"


def sanitize_html_content(text: str) -> str:
    """
    清理HTML内容，防止XSS攻击

    Args:
        text: 待清理的文本

    Returns:
        清理后的文本
    """
    import html
    if text is None:
        return ""
    return html.escape(str(text))


def validate_file_path(
    file_path: Path,
    allowed_extensions: set,
    base_dir: Optional[Path] = None
) -> Tuple[bool, str]:
    """
    验证文件路径，防止路径遍历攻击

    Args:
        file_path: 要验证的文件路径
        allowed_extensions: 允许的文件扩展名集合（如{'.csv', '.xlsx'}）
        base_dir: 基础目录（如果提供，文件必须在此目录下）

    Returns:
        (是否通过, 错误消息)
    """
    # 1. 检查文件扩展名
    if file_path.suffix.lower() not in allowed_extensions:
        return False, f"不支持的文件类型: {file_path.suffix}"

    # 2. 规范化路径（防止../等路径遍历）
    try:
        resolved_path = file_path.resolve()
    except Exception as e:
        return False, f"无效的文件路径: {str(e)}"

    # 3. 检查是否在允许的目录下
    if base_dir:
        try:
            resolved_base = base_dir.resolve()
            # 检查文件是否在基础目录下
            resolved_path.relative_to(resolved_base)
        except ValueError:
            return False, f"文件路径超出允许范围"
        except Exception as e:
            return False, f"路径验证失败: {str(e)}"

    return True, "验证通过"


def validate_string_input(
    text: str,
    max_length: int = 1000,
    allow_html: bool = False,
    field_name: str = "输入"
) -> Tuple[bool, str]:
    """
    验证字符串输入

    Args:
        text: 输入文本
        max_length: 最大长度
        allow_html: 是否允许HTML标签
        field_name: 字段名称（用于错误消息）

    Returns:
        (是否通过, 错误消息)
    """
    if text is None:
        return False, f"{field_name}不能为空"

    # 检查长度
    if len(text) > max_length:
        return False, f"{field_name}长度超过限制（最大{max_length}字符）"

    # 如果不允许HTML，检查是否包含HTML标签
    if not allow_html:
        if '<' in text and '>' in text:
            return False, f"{field_name}不允许包含HTML标签"

    return True, "验证通过"
