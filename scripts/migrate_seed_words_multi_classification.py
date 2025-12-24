"""
迁移seed_words表，添加多分类支持
- 添加token_types列（JSON格式存储多个类型）
- 保留primary_token_type作为主要类别
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

    print("开始迁移seed_words表...")

    with engine.connect() as conn:
        try:
            # 检查表是否存在
            result = conn.execute(text("""
                SELECT COUNT(*) as count
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                AND table_name = 'seed_words'
            """))

            table_exists = result.fetchone()[0] > 0

            if not table_exists:
                print("seed_words表不存在，将创建新表...")
                from storage.models import create_all_tables
                create_all_tables()
                print("SUCCESS: 新表创建完成")
                return

            # 检查token_types列是否存在
            result = conn.execute(text("""
                SELECT COUNT(*) as count
                FROM information_schema.columns
                WHERE table_schema = DATABASE()
                AND table_name = 'seed_words'
                AND column_name = 'token_types'
            """))

            column_exists = result.fetchone()[0] > 0

            if column_exists:
                print("token_types列已存在，无需迁移")
                return

            print("添加token_types列...")

            # 添加token_types列
            conn.execute(text("""
                ALTER TABLE seed_words
                ADD COLUMN token_types TEXT
                AFTER seed_word
            """))

            conn.commit()

            print("SUCCESS: 迁移完成！")
            print("已添加token_types列，现在可以为词根分配多个Token类别")

        except Exception as e:
            conn.rollback()
            print(f"ERROR: 迁移失败 - {str(e)}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == "__main__":
    migrate()
