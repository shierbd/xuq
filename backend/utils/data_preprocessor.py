"""
[REQ-001] 数据导入功能 - 数据预处理工具
实现评价数量转换、空格处理等数据清洗功能
"""
import re
import pandas as pd
from typing import Optional, Union

def parse_review_count(value: Union[str, int, float]) -> Optional[int]:
    """
    [REQ-001] 解析评价数量字符串
    
    转换规则:
    - (1.1k) -> 1100
    - (19.1k) -> 19100
    - (15) -> 15
    - (2.5m) -> 2500000
    
    Args:
        value: 评价数量原始值
        
    Returns:
        Optional[int]: 转换后的整数值（无效则为 None）
    """
    if pd.isna(value):
        return None
    
    # 转换为字符串
    value_str = str(value).strip()
    if value_str == "":
        return None
    
    # 去除括号
    value_str = value_str.replace('(', '').replace(')', '')
    
    # 识别单位
    multiplier = 1
    if value_str.lower().endswith('k'):
        multiplier = 1000
        value_str = value_str[:-1]
    elif value_str.lower().endswith('m'):
        multiplier = 1000000
        value_str = value_str[:-1]
    
    try:
        return int(float(value_str) * multiplier)
    except (ValueError, TypeError):
        return None

def clean_product_name(name: str) -> str:
    """
    [REQ-001] 清洗商品名称
    
    - 去除前后空格
    - 压缩内部多余空格为单个空格
    - 保留括号
    
    Args:
        name: 商品名称
        
    Returns:
        str: 清洗后的商品名称
    """
    if pd.isna(name):
        return ""
    
    name = str(name).strip()
    name = re.sub(r'\s+', ' ', name)
    
    return name

def clean_price(price: Union[str, float]) -> Optional[float]:
    """
    [REQ-001] 清洗价格数据
    
    Args:
        price: 价格原始值
        
    Returns:
        Optional[float]: 清洗后的价格
    """
    if pd.isna(price):
        return None
    
    price_str = str(price).strip()
    price_str = re.sub(r'[$€£¥]', '', price_str)
    
    try:
        price_float = float(price_str)
        if price_float <= 0:
            return None
        return price_float
    except (ValueError, TypeError):
        return None

def clean_rating(rating: Union[str, float]) -> Optional[float]:
    """
    [REQ-001] 清洗评分数据
    
    Args:
        rating: 评分原始值
        
    Returns:
        Optional[float]: 清洗后的评分
    """
    if pd.isna(rating):
        return None
    
    try:
        rating_float = float(rating)
        if rating_float < 0 or rating_float > 5:
            return None
        return rating_float
    except (ValueError, TypeError):
        return None

def preprocess_etsy_data(df: pd.DataFrame) -> tuple:
    """
    [REQ-001] 预处理 Etsy 数据

    Args:
        df: 原始数据框

    Returns:
        tuple: (处理后的数据框, 统计信息字典，所有数值转换为 Python 原生类型)
    """
    if len(df.columns) != 5:
        raise ValueError(f"文件列数不正确，期望 5 列，实际 {len(df.columns)} 列")

    df.columns = ['product_name', 'rating', 'review_count', 'shop_name', 'price']

    stats = {
        'total': int(len(df)),
        'success': 0,
        'failed': 0,
        'warnings': []
    }

    # 数据清洗
    df['product_name'] = df['product_name'].apply(clean_product_name)
    df['review_count'] = df['review_count'].apply(parse_review_count)
    df['price'] = df['price'].apply(clean_price)
    df['rating'] = df['rating'].apply(clean_rating)
    df['shop_name'] = df['shop_name'].apply(lambda x: str(x).strip() if pd.notna(x) else None)

    # 数据验证
    valid_mask = df['product_name'].str.len() > 0
    failed_count = int((~valid_mask).sum())

    if failed_count > 0:
        stats['warnings'].append(f"跳过 {failed_count} 条商品名称为空的数据")
        stats['failed'] = failed_count

    df = df[valid_mask].copy()
    stats['success'] = int(len(df))

    return df, stats
