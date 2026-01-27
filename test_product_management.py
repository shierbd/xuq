"""
[REQ-002] 数据管理功能 - 测试脚本
测试商品查询、编辑、删除功能
"""
import sys
sys.path.insert(0, '.')

from backend.database import SessionLocal, init_db
from backend.models.product import Product
from backend.services.product_service import ProductService
from backend.schemas.product_schema import ProductQueryParams, ProductUpdate
from datetime import datetime

def setup_test_data(db):
    """创建测试数据"""
    print("创建测试数据...")
    
    test_products = [
        Product(
            product_name="Excel Template for Project Management",
            rating=4.5,
            review_count=1100,
            shop_name="TestShop1",
            price=19.99,
            import_time=datetime.utcnow()
        ),
        Product(
            product_name="Notion Template for Task Tracking",
            rating=4.8,
            review_count=2500,
            shop_name="TestShop2",
            price=29.99,
            import_time=datetime.utcnow()
        ),
        Product(
            product_name="Canva Template Bundle",
            rating=4.2,
            review_count=800,
            shop_name="TestShop1",
            price=15.99,
            import_time=datetime.utcnow()
        ),
    ]
    
    for product in test_products:
        db.add(product)
    
    db.commit()
    print(f"  Created {len(test_products)} test products")

def test_get_products(service):
    """测试获取商品列表"""
    print("\n测试获取商品列表...")
    
    params = ProductQueryParams(page=1, page_size=10)
    products, total = service.get_products(params)
    
    print(f"  [PASS] Total products: {total}")
    print(f"  [PASS] Retrieved: {len(products)} products")

def test_search_products(service):
    """测试搜索功能"""
    print("\n测试搜索功能...")
    
    params = ProductQueryParams(page=1, page_size=10, search="Template")
    products, total = service.get_products(params)
    
    print(f"  [PASS] Search 'Template': found {total} products")

def test_filter_products(service):
    """测试筛选功能"""
    print("\n测试筛选功能...")
    
    # 按店铺筛选
    params = ProductQueryParams(page=1, page_size=10, shop_name="TestShop1")
    products, total = service.get_products(params)
    print(f"  [PASS] Filter by shop 'TestShop1': found {total} products")
    
    # 按评分筛选
    params = ProductQueryParams(page=1, page_size=10, min_rating=4.5)
    products, total = service.get_products(params)
    print(f"  [PASS] Filter by rating >= 4.5: found {total} products")
    
    # 按价格筛选
    params = ProductQueryParams(page=1, page_size=10, min_price=20.0)
    products, total = service.get_products(params)
    print(f"  [PASS] Filter by price >= 20.0: found {total} products")

def test_sort_products(service):
    """测试排序功能"""
    print("\n测试排序功能...")
    
    # 按评分排序
    params = ProductQueryParams(page=1, page_size=10, sort_by="rating", sort_order="desc")
    products, total = service.get_products(params)
    
    if products:
        print(f"  [PASS] Sort by rating (desc): highest rating = {products[0].rating}")

def test_update_product(service):
    """测试更新商品"""
    print("\n测试更新商品...")
    
    # 获取第一个商品
    params = ProductQueryParams(page=1, page_size=1)
    products, _ = service.get_products(params)
    
    if products:
        product_id = products[0].product_id
        update_data = ProductUpdate(rating=5.0)
        
        updated = service.update_product(product_id, update_data)
        
        if updated and updated.rating == 5.0:
            print(f"  [PASS] Updated product {product_id}: rating = {updated.rating}")
        else:
            print(f"  [FAIL] Failed to update product {product_id}")

def test_delete_product(service):
    """测试删除商品"""
    print("\n测试删除商品...")
    
    # 获取第一个商品
    params = ProductQueryParams(page=1, page_size=1)
    products, _ = service.get_products(params)
    
    if products:
        product_id = products[0].product_id
        success = service.delete_product(product_id)
        
        if success:
            print(f"  [PASS] Deleted product {product_id}")
            
            # 验证已删除
            deleted = service.get_product_by_id(product_id)
            if deleted is None:
                print(f"  [PASS] Product {product_id} is no longer accessible")
        else:
            print(f"  [FAIL] Failed to delete product {product_id}")

def test_batch_delete(service):
    """测试批量删除"""
    print("\n测试批量删除...")
    
    # 获取前2个商品
    params = ProductQueryParams(page=1, page_size=2)
    products, _ = service.get_products(params)
    
    if len(products) >= 2:
        product_ids = [p.product_id for p in products]
        count = service.batch_delete_products(product_ids)
        
        print(f"  [PASS] Batch deleted {count} products")

if __name__ == "__main__":
    print("=" * 60)
    print("[REQ-002] Data Management Function - Tests")
    print("=" * 60)
    
    # 初始化数据库
    init_db()
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # 创建测试数据
        setup_test_data(db)
        
        # 创建服务
        service = ProductService(db)
        
        # 运行测试
        test_get_products(service)
        test_search_products(service)
        test_filter_products(service)
        test_sort_products(service)
        test_update_product(service)
        test_delete_product(service)
        test_batch_delete(service)
        
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
        
    finally:
        db.close()
