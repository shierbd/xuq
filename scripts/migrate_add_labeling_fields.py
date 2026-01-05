"""
数据库迁移脚本：添加DeepSeek语义标注字段
为ClusterMeta表添加Phase 2C所需的新字段

运行方式:
    python scripts/migrate_add_labeling_fields.py
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import DATABASE_CONFIG
from sqlalchemy import text
from storage.repository import get_session


def migrate_add_labeling_fields():
    """为cluster_meta表添加标注字段"""
    print("\n" + "="*70)
    print("数据库迁移：添加DeepSeek语义标注字段".center(70))
    print("="*70)

    session = get_session()

    try:
        # 根据数据库类型选择不同的SQL
        if DATABASE_CONFIG["type"] == "mysql":
            print("\n检测到MySQL数据库，添加字段...")

            # 添加字段的SQL语句
            alterations = [
                "ALTER TABLE cluster_meta ADD COLUMN IF NOT EXISTS llm_label VARCHAR(100)",
                "ALTER TABLE cluster_meta ADD COLUMN IF NOT EXISTS primary_demand_type ENUM('tool', 'content', 'service', 'education', 'other')",
                "ALTER TABLE cluster_meta ADD COLUMN IF NOT EXISTS secondary_demand_types TEXT",
                "ALTER TABLE cluster_meta ADD COLUMN IF NOT EXISTS labeling_confidence INT",
                "ALTER TABLE cluster_meta ADD COLUMN IF NOT EXISTS labeling_timestamp TIMESTAMP",
                "CREATE INDEX IF NOT EXISTS idx_primary_demand_type ON cluster_meta(primary_demand_type)"
            ]

        else:  # SQLite
            print("\n检测到SQLite数据库，添加字段...")

            alterations = [
                "ALTER TABLE cluster_meta ADD COLUMN llm_label VARCHAR(100)",
                "ALTER TABLE cluster_meta ADD COLUMN primary_demand_type VARCHAR(50)",
                "ALTER TABLE cluster_meta ADD COLUMN secondary_demand_types TEXT",
                "ALTER TABLE cluster_meta ADD COLUMN labeling_confidence INTEGER",
                "ALTER TABLE cluster_meta ADD COLUMN labeling_timestamp TIMESTAMP",
            ]

        # 执行迁移
        success_count = 0
        for sql in alterations:
            try:
                print(f"  执行: {sql[:60]}...")
                session.execute(text(sql))
                session.commit()
                success_count += 1
                print(f"  ✓ 成功")
            except Exception as e:
                # 字段可能已存在，继续
                error_msg = str(e).lower()
                if "duplicate" in error_msg or "already exists" in error_msg:
                    print(f"  ⚠️  字段已存在，跳过")
                else:
                    print(f"  ✗ 失败: {str(e)}")

        print(f"\n迁移完成：成功执行 {success_count}/{len(alterations)} 条语句")

        # 验证
        print("\n验证新字段...")
        result = session.execute(text("SELECT * FROM cluster_meta LIMIT 1"))
        columns = result.keys()

        required_fields = ['llm_label', 'primary_demand_type', 'secondary_demand_types',
                          'labeling_confidence', 'labeling_timestamp']

        print("\n检查字段存在性:")
        for field in required_fields:
            exists = field in columns
            status = "✓" if exists else "✗"
            print(f"  {status} {field}")

        print("\n" + "="*70)
        print("✅ 数据库迁移完成！".center(70))
        print("="*70)

        return True

    except Exception as e:
        print(f"\n\n❌ 迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()
        session.rollback()
        return False

    finally:
        session.close()


if __name__ == "__main__":
    try:
        success = migrate_add_labeling_fields()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
