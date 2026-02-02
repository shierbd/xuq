"""
数据库迁移脚本：添加 topic_text 字段

Phase 2 (2026-02-02): 双文本策略
添加 topic_text 字段用于存储去除属性词后的主题文本

运行方式:
    python migrations/add_topic_text_field.py
"""
import sys
import os
from datetime import datetime

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import engine
from sqlalchemy import text


def add_topic_text_field():
    """添加 topic_text 字段到 products 表"""
    print("="*80)
    print("数据库迁移：添加 topic_text 字段")
    print("="*80)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    try:
        with engine.connect() as conn:
            # 检查字段是否已存在
            print("检查 topic_text 字段是否已存在...")

            result = conn.execute(text("PRAGMA table_info(products)"))
            columns = [row[1] for row in result]

            if 'topic_text' in columns:
                print("✅ topic_text 字段已存在，无需添加")
                return

            # 添加字段
            print("添加 topic_text 字段...")

            conn.execute(text("""
                ALTER TABLE products
                ADD COLUMN topic_text VARCHAR(500)
            """))

            conn.commit()

            print("✅ topic_text 字段添加成功")

            # 验证
            print("\n验证字段是否添加成功...")
            result = conn.execute(text("PRAGMA table_info(products)"))
            columns = [row[1] for row in result]

            if 'topic_text' in columns:
                print("✅ 验证成功：topic_text 字段已存在")
            else:
                print("❌ 验证失败：topic_text 字段不存在")

    except Exception as e:
        print(f"❌ 迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "="*80)
    print("迁移完成")
    print("="*80)
    return True


if __name__ == "__main__":
    add_topic_text_field()
