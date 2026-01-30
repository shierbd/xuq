"""
全量生成脚本：为所有 675 个簇生成类别名称
使用 DeepSeek API，预计时间 30-40 分钟，成本 $3-5
"""
import sys
import os
import asyncio
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath('.'))

# 加载 .env 文件
from dotenv import load_dotenv
load_dotenv()

from backend.database import SessionLocal
from backend.services.category_naming_service import CategoryNamingService


async def main():
    """主函数：全量生成类别名称"""
    print()
    print("=" * 70)
    print("全量生成类别名称 - 为所有 675 个簇生成类别名称")
    print("=" * 70)
    print()

    # 检查环境变量
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("ERROR: DEEPSEEK_API_KEY not found")
        print("Please set DEEPSEEK_API_KEY in .env file")
        return

    print("OK: Environment variables checked")
    print()

    # 记录开始时间
    start_time = datetime.now()
    print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    db = SessionLocal()

    try:
        # 创建服务
        service = CategoryNamingService(db, ai_provider="deepseek")

        # 获取统计信息
        print("=" * 70)
        print("Before generation - Statistics")
        print("=" * 70)
        stats_before = service.get_cluster_statistics()
        print(f"Total clusters: {stats_before['total_clusters']}")
        print(f"Named clusters: {stats_before['named_clusters']}")
        print(f"Unnamed clusters: {stats_before['unnamed_clusters']}")
        print(f"Naming rate: {stats_before['naming_rate']:.2f}%")
        print()

        # 确认是否继续
        print("=" * 70)
        print("WARNING: This will generate names for ALL clusters")
        print("=" * 70)
        print(f"Total clusters to process: {stats_before['unnamed_clusters']}")
        print(f"Estimated time: 30-40 minutes")
        print(f"Estimated cost: $3-5 (DeepSeek)")
        print()

        # 批量生成
        print("=" * 70)
        print("Starting batch generation...")
        print("=" * 70)
        print()

        result = await service.generate_all_category_names(
            cluster_ids=None,  # 处理所有簇
            top_n=5,
            batch_size=10
        )

        # 记录结束时间
        end_time = datetime.now()
        duration = end_time - start_time

        print()
        print("=" * 70)
        print("Generation completed!")
        print("=" * 70)
        print(f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration: {duration}")
        print()

        print("=" * 70)
        print("Results Summary")
        print("=" * 70)
        print(f"Total clusters: {result['total_clusters']}")
        print(f"Processed: {result['processed']}")
        print(f"Success: {result['success_count']}")
        print(f"Failed: {result['failed_count']}")
        print(f"Success rate: {result['success_count']/result['processed']*100:.2f}%")
        print()

        # 获取更新后的统计信息
        print("=" * 70)
        print("After generation - Statistics")
        print("=" * 70)
        stats_after = service.get_cluster_statistics()
        print(f"Total clusters: {stats_after['total_clusters']}")
        print(f"Named clusters: {stats_after['named_clusters']}")
        print(f"Unnamed clusters: {stats_after['unnamed_clusters']}")
        print(f"Naming rate: {stats_after['naming_rate']:.2f}%")
        print()

        # 显示失败的簇
        if result['failed_count'] > 0:
            print("=" * 70)
            print("Failed clusters:")
            print("=" * 70)
            for r in result['results']:
                if not r['success']:
                    print(f"  Cluster {r['cluster_id']}: {r['error']}")
            print()

        # 保存结果到文件
        output_file = f"category_naming_results_{start_time.strftime('%Y%m%d_%H%M%S')}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("Category Naming Results\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"Start time: {start_time}\n")
            f.write(f"End time: {end_time}\n")
            f.write(f"Duration: {duration}\n\n")
            f.write(f"Total clusters: {result['total_clusters']}\n")
            f.write(f"Processed: {result['processed']}\n")
            f.write(f"Success: {result['success_count']}\n")
            f.write(f"Failed: {result['failed_count']}\n\n")

            f.write("=" * 70 + "\n")
            f.write("All Results:\n")
            f.write("=" * 70 + "\n\n")
            for r in result['results']:
                if r['success']:
                    f.write(f"[OK] Cluster {r['cluster_id']}: {r['category_name']}\n")
                else:
                    f.write(f"[FAIL] Cluster {r['cluster_id']}: {r['error']}\n")

        print(f"Results saved to: {output_file}")
        print()

    except Exception as e:
        print(f"ERROR: Generation failed - {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()

    print("=" * 70)
    print("All done!")
    print("=" * 70)
    print()


if __name__ == "__main__":
    asyncio.run(main())
