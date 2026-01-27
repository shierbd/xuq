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
    
    def import_from_file(self, file: BinaryIO, filename: str) -> Dict:
        """
        [REQ-001] 从文件导入数据
        
        Args:
            file: 文件对象
            filename: 文件名
            
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
        
        # 预处理数据
        df_clean, stats = preprocess_etsy_data(df)
        
        # 导入数据库
        import_stats = self._import_to_database(df_clean, filename)
        
        # 合并统计信息
        stats.update(import_stats)
        
        return stats
    
    def _import_to_database(self, df: pd.DataFrame, filename: str) -> Dict:
        """
        [REQ-001] 导入数据到数据库
        
        Args:
            df: 清洗后的数据框
            filename: 文件名
            
        Returns:
            Dict: 导入统计
        """
        stats = {
            'imported': 0,
            'duplicates': 0,
            'filename': filename,
            'import_time': datetime.utcnow().isoformat()
        }
        
        for _, row in df.iterrows():
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
                rating=row['rating'],
                review_count=row['review_count'],
                shop_name=row['shop_name'],
                price=row['price'],
                import_time=datetime.utcnow()
            )
            
            self.db.add(product)
            stats['imported'] += 1
        
        # 提交事务
        self.db.commit()
        
        return stats
    
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
