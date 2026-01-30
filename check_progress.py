"""快速检查类别名称生成进度"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from dotenv import load_dotenv
load_dotenv()

from backend.database import SessionLocal
from backend.services.category_naming_service import CategoryNamingService

def main():
    db = SessionLocal()
    try:
        service = CategoryNamingService(db, ai_provider="deepseek")
        stats = service.get_cluster_statistics()

        print("=" * 70)
        print("当前命名进度")
        print("=" * 70)
        print(f"总簇数: {stats['total_clusters']}")
        print(f"已命名: {stats['named_clusters']}")
        print(f"未命名: {stats['unnamed_clusters']}")
        print(f"命名率: {stats['naming_rate']:.2f}%")
        print("=" * 70)

    finally:
        db.close()

if __name__ == "__main__":
    main()
