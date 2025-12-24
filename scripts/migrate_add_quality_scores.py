"""
数据库迁移脚本：添加质量评分字段
Migration Script: Add Quality Score Fields to ClusterMeta

功能：
- 为cluster_meta表添加质量评分相关字段
- 兼容SQLite和MySQL

创建日期：2025-12-23
"""

import io
import sys
from pathlib import Path

# Set UTF-8 encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.models import get_engine
from config.settings import DATABASE_CONFIG
from sqlalchemy import text

IS_SQLITE = DATABASE_CONFIG["type"] == "sqlite"


def migrate_add_quality_scores():
    """
    添加质量评分字段到cluster_meta表
    """
    print("\n" + "="*70)
    print("数据库迁移：添加质量评分字段")
    print("="*70)

    engine = get_engine()

    if IS_SQLITE:
        print("\n检测到SQLite数据库")

        # SQLite的ALTER TABLE比较简单
        with engine.connect() as conn:
            try:
                print("\n添加字段...")

                # 添加各个字段
                conn.execute(text("ALTER TABLE cluster_meta ADD COLUMN quality_score INTEGER"))
                print("✓ 添加 quality_score")

                conn.execute(text("ALTER TABLE cluster_meta ADD COLUMN size_score INTEGER"))
                print("✓ 添加 size_score")

                conn.execute(text("ALTER TABLE cluster_meta ADD COLUMN diversity_score INTEGER"))
                print("✓ 添加 diversity_score")

                conn.execute(text("ALTER TABLE cluster_meta ADD COLUMN consistency_score INTEGER"))
                print("✓ 添加 consistency_score")

                conn.execute(text("ALTER TABLE cluster_meta ADD COLUMN quality_level VARCHAR(50)"))
                print("✓ 添加 quality_level")

                conn.execute(text("ALTER TABLE cluster_meta ADD COLUMN llm_summary TEXT"))
                print("✓ 添加 llm_summary")

                conn.execute(text("ALTER TABLE cluster_meta ADD COLUMN llm_value_assessment TEXT"))
                print("✓ 添加 llm_value_assessment")

                # 添加约束（SQLite 3.25+支持）
                try:
                    conn.execute(text("""
                        CREATE INDEX idx_cluster_quality_score
                        ON cluster_meta(quality_score)
                    """))
                    print("✓ 创建 quality_score 索引")

                    conn.execute(text("""
                        CREATE INDEX idx_cluster_quality_level
                        ON cluster_meta(quality_level)
                    """))
                    print("✓ 创建 quality_level 索引")
                except Exception as e:
                    print(f"⚠️  索引可能已存在: {e}")

                conn.commit()
                print("\n✅ SQLite迁移完成！")

            except Exception as e:
                print(f"\n❌ 迁移失败: {e}")
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
                    ADD COLUMN quality_score INT,
                    ADD COLUMN size_score INT,
                    ADD COLUMN diversity_score INT,
                    ADD COLUMN consistency_score INT,
                    ADD COLUMN quality_level ENUM('excellent', 'good', 'fair', 'poor'),
                    ADD COLUMN llm_summary TEXT,
                    ADD COLUMN llm_value_assessment TEXT,
                    ADD INDEX idx_cluster_quality_score (quality_score),
                    ADD INDEX idx_cluster_quality_level (quality_level)
                """))

                conn.commit()
                print("\n✅ MySQL迁移完成！")

            except Exception as e:
                print(f"\n❌ 迁移失败: {e}")
                print("\n提示：如果字段已存在，这是正常的")
                conn.rollback()

    print("\n" + "="*70)
    print("迁移完成")
    print("="*70)


if __name__ == "__main__":
    try:
        migrate_add_quality_scores()
    except KeyboardInterrupt:
        print("\n\n⚠️  操作被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
