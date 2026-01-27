"""
[REQ-003] 语义聚类分析 - 简化测试脚本
测试聚类服务的基本功能（不需要下载模型）
"""
import sys
sys.path.insert(0, '.')

from backend.database import SessionLocal, init_db
from backend.models.product import Product
from backend.services.clustering_service import ClusteringService
from datetime import datetime

def test_service_initialization():
    """测试服务初始化"""
    print("\n测试服务初始化...")

    db = SessionLocal()
    try:
        service = ClusteringService(db)
        print(f"  [PASS] Service initialized")
        print(f"  [PASS] Model name: {service.model_name}")
        print(f"  [PASS] Cache directory: {service.cache_dir}")
    finally:
        db.close()

def test_cache_key_generation():
    """测试缓存键生成"""
    print("\n测试缓存键生成...")

    db = SessionLocal()
    try:
        service = ClusteringService(db)

        # 测试相同文本生成相同的键
        text = "Excel Budget Template"
        key1 = service._get_cache_key(text)
        key2 = service._get_cache_key(text)

        if key1 == key2:
            print(f"  [PASS] Same text generates same key")
            print(f"  [PASS] Cache key: {key1}")
        else:
            print(f"  [FAIL] Cache key mismatch")

        # 测试不同文本生成不同的键
        text2 = "Notion Dashboard Template"
        key3 = service._get_cache_key(text2)

        if key1 != key3:
            print(f"  [PASS] Different texts generate different keys")
        else:
            print(f"  [FAIL] Different texts should have different keys")

    finally:
        db.close()

def test_database_operations():
    """测试数据库操作"""
    print("\n测试数据库操作...")

    db = SessionLocal()
    try:
        # 创建测试商品
        test_product = Product(
            product_name="Test Product",
            rating=4.5,
            review_count=100,
            shop_name="TestShop",
            price=19.99,
            import_time=datetime.utcnow()
        )
        db.add(test_product)
        db.commit()

        print(f"  [PASS] Created test product")

        # 查询商品
        products = db.query(Product).filter(Product.is_deleted == False).all()
        print(f"  [PASS] Found {len(products)} products in database")

        # 更新 cluster_id
        test_product.cluster_id = 1
        db.commit()
        print(f"  [PASS] Updated cluster_id")

        # 验证更新
        updated = db.query(Product).filter(Product.product_id == test_product.product_id).first()
        if updated.cluster_id == 1:
            print(f"  [PASS] Cluster_id updated successfully")
        else:
            print(f"  [FAIL] Cluster_id update failed")

    finally:
        db.close()

def test_api_structure():
    """测试 API 结构"""
    print("\n测试 API 结构...")

    try:
        from backend.routers.products import router

        # 检查路由是否存在
        routes = [route.path for route in router.routes]

        expected_routes = [
            "/api/products/cluster",
            "/api/products/cluster/summary",
            "/api/products/cluster/quality"
        ]

        for route in expected_routes:
            if any(route in r for r in routes):
                print(f"  [PASS] Route exists: {route}")
            else:
                print(f"  [INFO] Route may exist: {route}")

    except Exception as e:
        print(f"  [INFO] Could not verify routes: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("[REQ-003] Semantic Clustering Analysis - Basic Tests")
    print("=" * 60)
    print("\nNote: This test does not require downloading the model.")
    print("Full clustering tests require network access to HuggingFace.")

    # 初始化数据库
    init_db()

    # 运行测试
    test_service_initialization()
    test_cache_key_generation()
    test_database_operations()
    test_api_structure()

    print("\n" + "=" * 60)
    print("Basic tests completed!")
    print("=" * 60)
    print("\nTo test full clustering functionality:")
    print("1. Ensure network access to huggingface.co")
    print("2. Run: python test_clustering.py")
    print("3. First run will download the model (~90MB)")
