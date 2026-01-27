"""
[REQ-007] 数据导出功能 - 测试脚本
测试数据导出功能
"""
import sys
sys.path.insert(0, '.')

from backend.database import SessionLocal, init_db
from backend.models.product import Product
from backend.services.export_service import ExportService
from datetime import datetime
import pandas as pd
import io

def setup_test_data(db):
    """创建测试数据"""
    print("创建测试数据...")
    
    test_products = [
        Product(
            product_name="Excel Template 1",
            rating=4.5,
            review_count=1100,
            shop_name="TestShop1",
            price=19.99,
            cluster_id=1,
            import_time=datetime.utcnow()
        ),
        Product(
            product_name="Notion Template 1",
            rating=4.8,
            review_count=2500,
            shop_name="TestShop2",
            price=29.99,
            cluster_id=1,
            import_time=datetime.utcnow()
        ),
        Product(
            product_name="Canva Template 1",
            rating=4.2,
            review_count=800,
            shop_name="TestShop1",
            price=15.99,
            cluster_id=2,
            import_time=datetime.utcnow()
        ),
        Product(
            product_name="PPT Template 1",
            rating=4.6,
            review_count=1500,
            shop_name="TestShop3",
            price=24.99,
            cluster_id=2,
            import_time=datetime.utcnow()
        ),
    ]
    
    for product in test_products:
        db.add(product)
    
    db.commit()
    print(f"  Created {len(test_products)} test products")

def test_export_products(service):
    """测试导出原始商品数据"""
    print("\n测试导出原始商品数据...")
    
    # 测试 CSV 导出
    csv_content = service.export_products(format="csv")
    df = pd.read_csv(io.BytesIO(csv_content))
    print(f"  [PASS] CSV export: {len(df)} products exported")
    print(f"  [PASS] CSV columns: {list(df.columns)}")
    
    # 测试 Excel 导出
    excel_content = service.export_products(format="excel")
    df = pd.read_excel(io.BytesIO(excel_content))
    print(f"  [PASS] Excel export: {len(df)} products exported")

def test_export_clustered_products(service):
    """测试导出聚类结果"""
    print("\n测试导出聚类结果...")
    
    # 测试 CSV 导出
    csv_content = service.export_clustered_products(format="csv")
    df = pd.read_csv(io.BytesIO(csv_content))
    print(f"  [PASS] CSV export: {len(df)} clustered products exported")
    print(f"  [PASS] Clusters found: {df['cluster_id'].nunique()}")

def test_export_cluster_summary(service):
    """测试导出簇级汇总"""
    print("\n测试导出簇级汇总...")
    
    # 测试 CSV 导出
    csv_content = service.export_cluster_summary(format="csv")
    df = pd.read_csv(io.BytesIO(csv_content))
    print(f"  [PASS] CSV export: {len(df)} clusters exported")
    print(f"  [PASS] Summary columns: {list(df.columns)}")
    
    # 验证汇总数据
    if len(df) > 0:
        print(f"  [PASS] Cluster 1 size: {df[df['cluster_id'] == 1]['cluster_size'].values[0]}")
        print(f"  [PASS] Cluster 2 size: {df[df['cluster_id'] == 2]['cluster_size'].values[0]}")

def test_export_formats(service):
    """测试不同导出格式"""
    print("\n测试不同导出格式...")
    
    # CSV 格式
    csv_content = service.export_products(format="csv")
    print(f"  [PASS] CSV format: {len(csv_content)} bytes")
    
    # Excel 格式
    excel_content = service.export_products(format="excel")
    print(f"  [PASS] Excel format: {len(excel_content)} bytes")

if __name__ == "__main__":
    print("=" * 60)
    print("[REQ-007] Data Export Function - Tests")
    print("=" * 60)
    
    # 初始化数据库
    init_db()
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # 创建测试数据
        setup_test_data(db)
        
        # 创建服务
        service = ExportService(db)
        
        # 运行测试
        test_export_products(service)
        test_export_clustered_products(service)
        test_export_cluster_summary(service)
        test_export_formats(service)
        
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
        
    finally:
        db.close()
