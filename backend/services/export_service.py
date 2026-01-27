"""
[REQ-007] 数据导出功能 - 导出服务
支持导出原始数据、聚类结果、簇级汇总
"""
import pandas as pd
from sqlalchemy.orm import Session
from backend.models.product import Product
from typing import List
import io

class ExportService:
    """[REQ-007] 数据导出服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def export_products(self, format: str = "csv") -> bytes:
        """
        [REQ-007] 导出原始商品数据
        
        Args:
            format: 导出格式（csv 或 excel）
            
        Returns:
            bytes: 文件内容
        """
        # 查询所有未删除的商品
        products = self.db.query(Product).filter(
            Product.is_deleted == False
        ).all()
        
        # 转换为字典列表
        data = [p.to_dict() for p in products]
        
        # 创建 DataFrame
        df = pd.DataFrame(data)
        
        # 选择导出的列
        columns = [
            'product_id', 'product_name', 'rating', 'review_count',
            'shop_name', 'price', 'import_time'
        ]
        df = df[columns]
        
        # 导出为指定格式
        return self._export_dataframe(df, format)
    
    def export_clustered_products(self, format: str = "csv") -> bytes:
        """
        [REQ-007] 导出聚类结果
        
        Args:
            format: 导出格式（csv 或 excel）
            
        Returns:
            bytes: 文件内容
        """
        # 查询已聚类的商品
        products = self.db.query(Product).filter(
            Product.is_deleted == False,
            Product.cluster_id.isnot(None)
        ).all()
        
        # 转换为字典列表
        data = [p.to_dict() for p in products]
        
        # 创建 DataFrame
        df = pd.DataFrame(data)
        
        # 选择导出的列
        columns = [
            'product_id', 'product_name', 'cluster_id', 'rating',
            'review_count', 'shop_name', 'price'
        ]
        df = df[columns]
        
        # 按簇 ID 排序
        df = df.sort_values('cluster_id')
        
        # 导出为指定格式
        return self._export_dataframe(df, format)
    
    def export_cluster_summary(self, format: str = "csv") -> bytes:
        """
        [REQ-007] 导出簇级汇总
        
        Args:
            format: 导出格式（csv 或 excel）
            
        Returns:
            bytes: 文件内容
        """
        # 查询已聚类的商品
        products = self.db.query(Product).filter(
            Product.is_deleted == False,
            Product.cluster_id.isnot(None)
        ).all()
        
        # 按簇分组统计
        cluster_data = {}
        for product in products:
            cluster_id = product.cluster_id
            if cluster_id not in cluster_data:
                cluster_data[cluster_id] = {
                    'cluster_id': cluster_id,
                    'cluster_size': 0,
                    'avg_rating': [],
                    'avg_price': [],
                    'total_reviews': 0,
                    'example_products': []
                }
            
            cluster_data[cluster_id]['cluster_size'] += 1
            
            if product.rating:
                cluster_data[cluster_id]['avg_rating'].append(product.rating)
            
            if product.price:
                cluster_data[cluster_id]['avg_price'].append(product.price)
            
            if product.review_count:
                cluster_data[cluster_id]['total_reviews'] += product.review_count
            
            # 保存前3个商品作为示例
            if len(cluster_data[cluster_id]['example_products']) < 3:
                cluster_data[cluster_id]['example_products'].append(product.product_name)
        
        # 计算平均值
        summary = []
        for cluster_id, data in cluster_data.items():
            summary.append({
                'cluster_id': cluster_id,
                'cluster_size': data['cluster_size'],
                'avg_rating': sum(data['avg_rating']) / len(data['avg_rating']) if data['avg_rating'] else None,
                'avg_price': sum(data['avg_price']) / len(data['avg_price']) if data['avg_price'] else None,
                'total_reviews': data['total_reviews'],
                'example_products': '; '.join(data['example_products'])
            })
        
        # 创建 DataFrame
        df = pd.DataFrame(summary)
        
        # 按簇 ID 排序
        df = df.sort_values('cluster_id')
        
        # 导出为指定格式
        return self._export_dataframe(df, format)
    
    def _export_dataframe(self, df: pd.DataFrame, format: str) -> bytes:
        """
        [REQ-007] 导出 DataFrame 为指定格式
        
        Args:
            df: DataFrame
            format: 导出格式（csv 或 excel）
            
        Returns:
            bytes: 文件内容
        """
        buffer = io.BytesIO()
        
        if format == "csv":
            df.to_csv(buffer, index=False, encoding='utf-8-sig')
        elif format == "excel":
            df.to_excel(buffer, index=False, engine='openpyxl')
        else:
            raise ValueError(f"不支持的导出格式: {format}")
        
        buffer.seek(0)
        return buffer.getvalue()
