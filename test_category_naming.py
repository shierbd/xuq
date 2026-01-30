"""
测试脚本：P4.1 类别名称生成功能
测试单个簇和批量生成类别名称
"""
import sys
import os
import asyncio

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath('.'))

# 加载 .env 文件
from dotenv import load_dotenv
load_dotenv()

from backend.database import SessionLocal
from backend.services.category_naming_service import CategoryNamingService


async def test_single_cluster():
    """测试单个簇的类别名称生成"""
    print("=" * 70)
    print("测试 1: 单个簇类别名称生成")
    print("=" * 70)
    print()

    db = SessionLocal()

    try:
        # 创建服务
        service = CategoryNamingService(db, ai_provider="deepseek")

        # 获取第一个簇ID
        from backend.models.product import Product
        first_cluster = db.query(Product.cluster_id).filter(
            Product.cluster_id != -1,
            Product.is_deleted == False
        ).first()

        if not first_cluster:
            print("ERROR: No clusters found")
            return

        cluster_id = first_cluster[0]
        print(f"测试簇ID: {cluster_id}")
        print()

        # 获取 Top 5 商品
        print("获取 Top 5 商品...")
        top_products = service.get_top_products_by_cluster(cluster_id, 5)
        print(f"Top 5 商品:")
        for i, name in enumerate(top_products, 1):
            print(f"  {i}. {name}")
        print()

        # 生成类别名称
        print("调用 AI 生成类别名称...")
        result = await service.generate_category_name(cluster_id, top_n=5)

        if result["success"]:
            print(f"SUCCESS: Category name generated!")
            print(f"Category name: {result['category_name']}")
        else:
            print(f"FAILED: {result['error']}")

    except Exception as e:
        print(f"ERROR: Test failed - {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()

    print()


async def test_batch_generation():
    """测试批量生成（只测试前 3 个簇）"""
    print("=" * 70)
    print("测试 2: 批量生成类别名称（前 3 个簇）")
    print("=" * 70)
    print()

    db = SessionLocal()

    try:
        # 创建服务
        service = CategoryNamingService(db, ai_provider="deepseek")

        # 获取前 3 个簇ID
        from backend.models.product import Product
        cluster_ids = [
            row[0] for row in db.query(Product.cluster_id).filter(
                Product.cluster_id != -1,
                Product.is_deleted == False
            ).distinct().limit(3).all()
        ]

        if not cluster_ids:
            print("ERROR: No clusters found")
            return

        print(f"测试簇ID: {cluster_ids}")
        print()

        # 批量生成
        result = await service.generate_all_category_names(
            cluster_ids=cluster_ids,
            top_n=5,
            batch_size=10
        )

        print()
        print("=" * 70)
        print("批量生成结果汇总")
        print("=" * 70)
        print(f"总簇数: {result['total_clusters']}")
        print(f"已处理: {result['processed']}")
        print(f"成功: {result['success_count']}")
        print(f"失败: {result['failed_count']}")
        print()

        print("详细结果:")
        for r in result['results']:
            if r['success']:
                print(f"  [OK] Cluster {r['cluster_id']}: {r['category_name']}")
            else:
                print(f"  [FAIL] Cluster {r['cluster_id']}: {r['error']}")

    except Exception as e:
        print(f"ERROR: Test failed - {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()

    print()


async def test_statistics():
    """测试统计功能"""
    print("=" * 70)
    print("测试 3: 获取命名统计")
    print("=" * 70)
    print()

    db = SessionLocal()

    try:
        # 创建服务
        service = CategoryNamingService(db, ai_provider="deepseek")

        # 获取统计
        stats = service.get_cluster_statistics()

        print("命名统计:")
        print(f"  总簇数: {stats['total_clusters']}")
        print(f"  已命名: {stats['named_clusters']}")
        print(f"  未命名: {stats['unnamed_clusters']}")
        print(f"  命名率: {stats['naming_rate']:.2f}%")

    except Exception as e:
        print(f"ERROR: Test failed - {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()

    print()


async def main():
    """主测试函数"""
    print()
    print("=" * 70)
    print("P4.1 类别名称生成功能测试")
    print("=" * 70)
    print()

    # 检查环境变量
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("ERROR: DEEPSEEK_API_KEY not found")
        print("Please set DEEPSEEK_API_KEY in .env file")
        return

    print("OK: Environment variables checked")
    print()

    # 运行测试
    await test_statistics()
    await test_single_cluster()
    await test_batch_generation()

    print("=" * 70)
    print("测试完成！")
    print("=" * 70)
    print()


if __name__ == "__main__":
    asyncio.run(main())
