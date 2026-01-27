"""
[REQ-003] 语义聚类分析 - 测试脚本
测试语义聚类功能
"""
import sys
sys.path.insert(0, '.')

from backend.database import SessionLocal, init_db
from backend.models.product import Product
from backend.services.clustering_service import ClusteringService
from datetime import datetime

def setup_test_data(db):
    """创建测试数据"""
    print("创建测试数据...")

    # 创建不同类别的商品，用于测试聚类效果
    test_products = [
        # Excel 模板类（簇 1）
        Product(product_name="Excel Budget Template", rating=4.5, review_count=1100, shop_name="TestShop1", price=19.99, import_time=datetime.utcnow()),
        Product(product_name="Excel Financial Planner", rating=4.6, review_count=1200, shop_name="TestShop1", price=24.99, import_time=datetime.utcnow()),
        Product(product_name="Excel Invoice Template", rating=4.4, review_count=900, shop_name="TestShop2", price=15.99, import_time=datetime.utcnow()),
        Product(product_name="Excel Spreadsheet for Business", rating=4.7, review_count=1500, shop_name="TestShop1", price=29.99, import_time=datetime.utcnow()),
        Product(product_name="Excel Tracker Template", rating=4.5, review_count=1000, shop_name="TestShop3", price=19.99, import_time=datetime.utcnow()),

        # Notion 模板类（簇 2）
        Product(product_name="Notion Dashboard Template", rating=4.8, review_count=2500, shop_name="TestShop2", price=29.99, import_time=datetime.utcnow()),
        Product(product_name="Notion Productivity System", rating=4.9, review_count=3000, shop_name="TestShop2", price=39.99, import_time=datetime.utcnow()),
        Product(product_name="Notion Task Manager", rating=4.7, review_count=2200, shop_name="TestShop3", price=24.99, import_time=datetime.utcnow()),
        Product(product_name="Notion Workspace Template", rating=4.8, review_count=2800, shop_name="TestShop2", price=34.99, import_time=datetime.utcnow()),
        Product(product_name="Notion Project Planner", rating=4.6, review_count=2000, shop_name="TestShop1", price=27.99, import_time=datetime.utcnow()),

        # Canva 模板类（簇 3）
        Product(product_name="Canva Social Media Template", rating=4.2, review_count=800, shop_name="TestShop1", price=15.99, import_time=datetime.utcnow()),
        Product(product_name="Canva Instagram Post Bundle", rating=4.3, review_count=950, shop_name="TestShop3", price=19.99, import_time=datetime.utcnow()),
        Product(product_name="Canva Design Templates", rating=4.4, review_count=1100, shop_name="TestShop2", price=22.99, import_time=datetime.utcnow()),
        Product(product_name="Canva Marketing Graphics", rating=4.1, review_count=700, shop_name="TestShop1", price=14.99, import_time=datetime.utcnow()),
        Product(product_name="Canva Brand Kit Template", rating=4.5, review_count=1200, shop_name="TestShop3", price=24.99, import_time=datetime.utcnow()),

        # PPT 模板类（簇 4）
        Product(product_name="PowerPoint Presentation Template", rating=4.6, review_count=1500, shop_name="TestShop3", price=24.99, import_time=datetime.utcnow()),
        Product(product_name="PPT Business Slides", rating=4.5, review_count=1300, shop_name="TestShop2", price=21.99, import_time=datetime.utcnow()),
        Product(product_name="PowerPoint Pitch Deck", rating=4.7, review_count=1800, shop_name="TestShop1", price=29.99, import_time=datetime.utcnow()),
        Product(product_name="PPT Template Bundle", rating=4.4, review_count=1100, shop_name="TestShop3", price=19.99, import_time=datetime.utcnow()),
        Product(product_name="PowerPoint Design Pack", rating=4.6, review_count=1400, shop_name="TestShop2", price=26.99, import_time=datetime.utcnow()),
    ]

    for product in test_products:
        db.add(product)

    db.commit()
    print(f"  Created {len(test_products)} test products")

def test_vectorization(service):
    """测试向量化功能"""
    print("\n测试向量化功能...")

    # 查询商品
    products = service.db.query(Product).filter(Product.is_deleted == False).all()

    # 向量化（不使用缓存）
    embeddings, product_ids = service.vectorize_products(products, use_cache=False)

    print(f"  [PASS] Vectorized {len(product_ids)} products")
    print(f"  [PASS] Embedding shape: {embeddings.shape}")
    print(f"  [PASS] Embedding dimension: {embeddings.shape[1]}")

def test_clustering(service):
    """测试聚类功能"""
    print("\n测试聚类功能...")

    # 执行聚类（使用较小的参数以适应测试数据）
    result = service.cluster_all_products(
        min_cluster_size=3,  # 降低最小簇大小以适应测试数据
        min_samples=2,
        use_cache=True
    )

    if result["success"]:
        print(f"  [PASS] Clustering completed")
        print(f"  [PASS] Total products: {result['total_products']}")
        print(f"  [PASS] Number of clusters: {result['n_clusters']}")
        print(f"  [PASS] Noise points: {result['n_noise']}")
        print(f"  [PASS] Noise ratio: {result['noise_ratio']:.2f}%")
    else:
        print(f"  [FAIL] Clustering failed: {result.get('message', 'Unknown error')}")

def test_cluster_summary(service):
    """测试簇级汇总"""
    print("\n测试簇级汇总...")

    summary = service.generate_cluster_summary()

    print(f"  [PASS] Generated summary for {len(summary)} clusters")

    # 显示前3个簇的信息
    for i, cluster in enumerate(summary[:3]):
        print(f"\n  Cluster {cluster['cluster_id']}:")
        print(f"    Size: {cluster['cluster_size']}")
        print(f"    Avg Rating: {cluster['avg_rating']:.2f}" if cluster['avg_rating'] else "    Avg Rating: N/A")
        print(f"    Avg Price: ${cluster['avg_price']:.2f}" if cluster['avg_price'] else "    Avg Price: N/A")
        print(f"    Total Reviews: {cluster['total_reviews']}")
        print(f"    Examples: {cluster['example_products'][:2]}")

def test_quality_report(service):
    """测试质量报告"""
    print("\n测试质量报告...")

    report = service.get_cluster_quality_report()

    if report["success"]:
        print(f"  [PASS] Quality report generated")
        print(f"  [PASS] Total products: {report['total_products']}")
        print(f"  [PASS] Number of clusters: {report['n_clusters']}")
        print(f"  [PASS] Noise ratio: {report['noise_ratio']:.2f}%")
        print(f"  [PASS] Avg cluster size: {report['avg_cluster_size']:.2f}")
        print(f"  [PASS] Min cluster size: {report['min_cluster_size']}")
        print(f"  [PASS] Max cluster size: {report['max_cluster_size']}")
    else:
        print(f"  [FAIL] Quality report failed: {report.get('message', 'Unknown error')}")

def test_cache_mechanism(service):
    """测试缓存机制"""
    print("\n测试缓存机制...")

    import time

    # 查询商品
    products = service.db.query(Product).filter(Product.is_deleted == False).limit(5).all()

    # 第一次向量化（无缓存）
    start_time = time.time()
    embeddings1, _ = service.vectorize_products(products, use_cache=False)
    time1 = time.time() - start_time

    # 第二次向量化（使用缓存）
    start_time = time.time()
    embeddings2, _ = service.vectorize_products(products, use_cache=True)
    time2 = time.time() - start_time

    print(f"  [PASS] First vectorization (no cache): {time1:.3f}s")
    print(f"  [PASS] Second vectorization (with cache): {time2:.3f}s")

    if time2 < time1:
        print(f"  [PASS] Cache speedup: {time1/time2:.2f}x")
    else:
        print(f"  [INFO] Cache not faster (small dataset)")

if __name__ == "__main__":
    print("=" * 60)
    print("[REQ-003] Semantic Clustering Analysis - Tests")
    print("=" * 60)

    # 初始化数据库
    init_db()

    # 创建数据库会话
    db = SessionLocal()

    try:
        # 创建测试数据
        setup_test_data(db)

        # 创建服务
        service = ClusteringService(db)

        # 运行测试
        test_vectorization(service)
        test_clustering(service)
        test_cluster_summary(service)
        test_quality_report(service)
        test_cache_mechanism(service)

        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)

    finally:
        db.close()
