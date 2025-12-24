"""
数据库迁移脚本：添加意图分类字段
Migration Script: Add Intent Classification Fields to ClusterMeta

功能：
- 为cluster_meta表添加意图分类相关字段
- 兼容SQLite和MySQL

创建日期：2025-12-23
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.models import get_engine
from config.settings import DATABASE_CONFIG
from sqlalchemy import text

IS_SQLITE = DATABASE_CONFIG["type"] == "sqlite"


def migrate_add_intent_fields():
    """
    添加意图分类字段到cluster_meta表
    """
    print("\n" + "="*70)
    print("数据库迁移：添加意图分类字段")
    print("="*70)

    engine = get_engine()

    if IS_SQLITE:
        print("\n检测到SQLite数据库")

        # SQLite的ALTER TABLE比较简单
        with engine.connect() as conn:
            try:
                print("\n添加字段...")

                # 添加各个字段
                conn.execute(text("ALTER TABLE cluster_meta ADD COLUMN dominant_intent VARCHAR(50)"))
                print("[OK] 添加 dominant_intent")

                conn.execute(text("ALTER TABLE cluster_meta ADD COLUMN dominant_intent_confidence INTEGER"))
                print("[OK] 添加 dominant_intent_confidence")

                conn.execute(text("ALTER TABLE cluster_meta ADD COLUMN intent_distribution TEXT"))
                print("[OK] 添加 intent_distribution")

                conn.execute(text("ALTER TABLE cluster_meta ADD COLUMN is_intent_balanced BOOLEAN DEFAULT 0"))
                print("[OK] 添加 is_intent_balanced")

                # 添加索引
                try:
                    conn.execute(text("""
                        CREATE INDEX idx_cluster_dominant_intent
                        ON cluster_meta(dominant_intent)
                    """))
                    print("[OK] 创建 dominant_intent 索引")
                except Exception as e:
                    print(f"[WARN] 索引可能已存在: {e}")

                conn.commit()
                print("\n[OK] SQLite迁移完成！")

            except Exception as e:
                print(f"\n[ERROR] 迁移失败: {e}")
                print("\n提示：如果字段已存在，这是正常的")
                conn.rollback()

    else:
        print("\n检测到MySQL数据库")

        with engine.connect() as conn:
            try:
                print("\n添加字段...")

                # MySQL可以在一条语句中添加多个字段
                conn.execute(text("""
                    ALTER TABLE cluster_meta
                    ADD COLUMN dominant_intent VARCHAR(50),
                    ADD COLUMN dominant_intent_confidence INT,
                    ADD COLUMN intent_distribution TEXT,
                    ADD COLUMN is_intent_balanced BOOLEAN DEFAULT FALSE,
                    ADD INDEX idx_cluster_dominant_intent (dominant_intent)
                """))

                conn.commit()
                print("\n[OK] MySQL迁移完成！")

            except Exception as e:
                print(f"\n[ERROR] 迁移失败: {e}")
                print("\n提示：如果字段已存在，这是正常的")
                conn.rollback()

    print("\n" + "="*70)
    print("迁移完成")
    print("="*70)


if __name__ == "__main__":
    try:
        migrate_add_intent_fields()
    except KeyboardInterrupt:
        print("\n\n[WARN] 操作被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
