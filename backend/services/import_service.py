"""
[REQ-001] 数据导入功能 - 导入服务
处理文件上传、数据解析、数据导入的业务逻辑
"""
import pandas as pd
from typing import BinaryIO, Dict
from sqlalchemy.orm import Session
from backend.models.product import Product
from backend.utils.data_preprocessor import preprocess_etsy_data
from datetime import datetime

class ImportService:
    """[REQ-001] 数据导入服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def import_from_file(self, file: BinaryIO, filename: str, field_mapping: Dict = None, skip_duplicates: bool = True) -> Dict:
        """
        [REQ-001] 从文件导入数据

        Args:
            file: 文件对象
            filename: 文件名
            field_mapping: 字段映射 {字段名: 列索引}
            skip_duplicates: 是否跳过重复数据

        Returns:
            Dict: 导入结果统计
        """
        # 读取文件
        if filename.endswith('.csv'):
            df = pd.read_csv(file, header=None)
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file, header=None)
        else:
            raise ValueError("不支持的文件格式，请上传 Excel 或 CSV 文件")

        # 检查文件是否为空
        if len(df) == 0:
            raise ValueError("文件为空，请检查文件内容")

        # 如果提供了字段映射，使用映射；否则使用默认映射
        if field_mapping:
            # 创建新的DataFrame，根据映射提取列
            mapped_data = {}
            for field_name, col_index in field_mapping.items():
                if col_index < len(df.columns):
                    mapped_data[field_name] = df.iloc[:, col_index]
                else:
                    raise ValueError(f"列索引 {col_index} 超出范围，文件只有 {len(df.columns)} 列")

            df_clean = pd.DataFrame(mapped_data)

            # 确保必填字段存在
            if 'product_name' not in df_clean.columns:
                raise ValueError("必须映射 'product_name' 字段")

            # 应用数据清洗函数
            from backend.utils.data_preprocessor import (
                clean_product_name, parse_review_count, clean_price, clean_rating
            )

            df_clean['product_name'] = df_clean['product_name'].apply(clean_product_name)

            if 'review_count' in df_clean.columns:
                df_clean['review_count'] = df_clean['review_count'].apply(parse_review_count)
            else:
                df_clean['review_count'] = 0

            if 'price' in df_clean.columns:
                df_clean['price'] = df_clean['price'].apply(clean_price)
            else:
                df_clean['price'] = 0.0

            if 'rating' in df_clean.columns:
                df_clean['rating'] = df_clean['rating'].apply(clean_rating)
            else:
                df_clean['rating'] = 0.0

            if 'shop_name' in df_clean.columns:
                df_clean['shop_name'] = df_clean['shop_name'].apply(
                    lambda x: str(x).strip() if pd.notna(x) else ''
                )
            else:
                df_clean['shop_name'] = ''

            # 数据验证
            valid_mask = df_clean['product_name'].str.len() > 0
            invalid_count = int((~valid_mask).sum())

            df_clean = df_clean[valid_mask].copy()

            stats = {
                'total_rows': int(len(df)),
                'valid_rows': int(len(df_clean)),
                'invalid_rows': invalid_count
            }
        else:
            # 使用默认预处理（固定5列格式）
            df_clean, stats = preprocess_etsy_data(df)

        # 导入数据库
        import_stats = self._import_to_database(df_clean, filename, skip_duplicates)

        # 合并统计信息
        stats.update(import_stats)

        return stats
    
    def _import_to_database(self, df: pd.DataFrame, filename: str, skip_duplicates: bool = True) -> Dict:
        """
        [REQ-001] 导入数据到数据库

        Args:
            df: 清洗后的数据框
            filename: 文件名
            skip_duplicates: 是否跳过重复数据

        Returns:
            Dict: 导入统计（所有数值转换为 Python 原生类型）
        """
        stats = {
            'imported': 0,
            'duplicates': 0,
            'filename': filename,
            'import_time': datetime.utcnow().isoformat()
        }

        for _, row in df.iterrows():
            if skip_duplicates:
                # 检查是否重复（基于商品名称 + 店铺名称）
                existing = self.db.query(Product).filter(
                    Product.product_name == row['product_name'],
                    Product.shop_name == row['shop_name'],
                    Product.is_deleted == False
                ).first()

                if existing:
                    stats['duplicates'] += 1
                    continue

            # 创建新商品
            product = Product(
                product_name=row['product_name'],
                rating=float(row.get('rating', 0.0)) if row.get('rating') else 0.0,
                review_count=int(row.get('review_count', 0)) if row.get('review_count') else 0,
                shop_name=str(row.get('shop_name', '')),
                price=float(row.get('price', 0.0)) if row.get('price') else 0.0,
                import_time=datetime.utcnow()
            )

            self.db.add(product)
            stats['imported'] += 1

        # 提交事务
        self.db.commit()

        # 确保返回的是 Python 原生类型
        return {
            'imported': int(stats['imported']),
            'duplicates': int(stats['duplicates']),
            'filename': stats['filename'],
            'import_time': stats['import_time']
        }
    
    def get_import_preview(self, file: BinaryIO, filename: str, rows: int = 10) -> Dict:
        """
        [REQ-001] 获取导入预览
        
        Args:
            file: 文件对象
            filename: 文件名
            rows: 预览行数
            
        Returns:
            Dict: 预览数据
        """
        # 读取文件
        if filename.endswith('.csv'):
            df = pd.read_csv(file, header=None, nrows=rows)
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file, header=None, nrows=rows)
        else:
            raise ValueError("不支持的文件格式")
        
        # 列映射
        if len(df.columns) != 5:
            raise ValueError(f"文件列数不正确，期望 5 列，实际 {len(df.columns)} 列")
        
        df.columns = ['product_name', 'rating', 'review_count', 'shop_name', 'price']
        
        return {
            'columns': list(df.columns),
            'data': df.to_dict('records'),
            'total_rows': len(df)
        }
