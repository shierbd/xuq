"""
重命名token_type列为primary_token_type
使其与模型定义一致
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from storage.models import get_engine
from sqlalchemy import text

def migrate():
    """执行数据库迁移"""
    engine = get_engine()

    print("检查并重命名token_type列为primary_token_type...")

    with engine.connect() as conn:
        try:
            # 检查token_type列是否存在
            result = conn.execute(text("""
                SELECT COUNT(*) as count
                FROM information_schema.columns
                WHERE table_schema = DATABASE()
                AND table_name = 'seed_words'
                AND column_name = 'token_type'
            """))

            old_column_exists = result.fetchone()[0] > 0

            # 检查primary_token_type列是否存在
            result = conn.execute(text("""
                SELECT COUNT(*) as count
                FROM information_schema.columns
                WHERE table_schema = DATABASE()
                AND table_name = 'seed_words'
                AND column_name = 'primary_token_type'
            """))

            new_column_exists = result.fetchone()[0] > 0

            if new_column_exists:
                print("primary_token_type列已存在，无需迁移")
                return

            if not old_column_exists:
                print("token_type列不存在，需要创建primary_token_type列...")
                # 直接创建primary_token_type列
                conn.execute(text("""
                    ALTER TABLE seed_words
                    ADD COLUMN primary_token_type
                    ENUM('intent', 'action', 'object', 'other')
                    AFTER token_types
                """))

                # 添加索引
                conn.execute(text("""
                    ALTER TABLE seed_words
                    ADD INDEX idx_primary_token_type (primary_token_type)
                """))

                conn.commit()
                print("SUCCESS: primary_token_type列创建完成")
                return

            print("重命名token_type列为primary_token_type...")

            # 重命名列
            conn.execute(text("""
                ALTER TABLE seed_words
                CHANGE COLUMN token_type primary_token_type
                ENUM('intent', 'action', 'object', 'other')
            """))

            conn.commit()

            print("SUCCESS: 列重命名完成！")
            print("token_type -> primary_token_type")

        except Exception as e:
            conn.rollback()
            print(f"ERROR: 迁移失败 - {str(e)}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == "__main__":
    migrate()
