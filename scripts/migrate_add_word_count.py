# -*- coding: utf-8 -*-
"""
数据库迁移脚本：为 word_segments 表添加 word_count 字段并扩展 word 字段长度

执行方式：
python scripts/migrate_add_word_count.py
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text
from storage.models import get_session
from config.settings import DATABASE_CONFIG

print("=" * 70)
print("数据库迁移：word_segments 表添加 word_count 字段")
print("=" * 70)

# 获取数据库类型
is_sqlite = DATABASE_CONFIG["type"] == "sqlite"

# 创建session
session = get_session()

try:
    print("\n【步骤1】检查表是否存在...")
    result = session.execute(text(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='word_segments'"
        if is_sqlite else
        "SHOW TABLES LIKE 'word_segments'"
    ))
    table_exists = result.fetchone() is not None

    if not table_exists:
        print("✓ word_segments 表不存在，将由 SQLAlchemy 自动创建（包含新字段）")
        session.close()
        print("\n迁移完成！表将在首次使用时自动创建。")
        exit(0)

    print("✓ word_segments 表已存在")

    # 检查 word_count 字段是否已存在
    print("\n【步骤2】检查 word_count 字段是否存在...")
    if is_sqlite:
        result = session.execute(text("PRAGMA table_info(word_segments)"))
        columns = [row[1] for row in result.fetchall()]
    else:
        result = session.execute(text("DESCRIBE word_segments"))
        columns = [row[0] for row in result.fetchall()]

    if 'word_count' in columns:
        print("✓ word_count 字段已存在，无需添加")
    else:
        print("✗ word_count 字段不存在，正在添加...")

        if is_sqlite:
            # SQLite: 添加列（默认值为1）
            session.execute(text(
                "ALTER TABLE word_segments ADD COLUMN word_count INTEGER DEFAULT 1"
            ))
            # 创建索引
            session.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_word_segments_word_count ON word_segments (word_count)"
            ))
        else:
            # MySQL: 添加列并创建索引
            session.execute(text(
                "ALTER TABLE word_segments ADD COLUMN word_count INT DEFAULT 1 AFTER frequency"
            ))
            session.execute(text(
                "ALTER TABLE word_segments ADD INDEX ix_word_segments_word_count (word_count)"
            ))

        session.commit()
        print("✓ word_count 字段添加成功")

        # 更新现有数据：根据空格数量设置 word_count
        print("\n【步骤3】更新现有记录的 word_count 值...")

        # 获取所有记录
        result = session.execute(text("SELECT word_id, word FROM word_segments"))
        records = result.fetchall()

        updated_count = 0
        for word_id, word in records:
            word_count = len(word.split())
            session.execute(
                text("UPDATE word_segments SET word_count = :wc WHERE word_id = :wid"),
                {"wc": word_count, "wid": word_id}
            )
            updated_count += 1

        session.commit()
        print(f"✓ 更新了 {updated_count} 条记录的 word_count 值")

    # 检查 word 字段长度
    print("\n【步骤4】检查 word 字段长度...")
    if is_sqlite:
        # SQLite 不支持直接修改列长度，需要重建表
        print("⚠️  SQLite 不支持修改列长度，但 String(255) 在 SQLite 中不受限制")
        print("   （SQLite 的 VARCHAR 长度仅作为提示，不强制限制）")
    else:
        # MySQL: 检查并修改列长度
        result = session.execute(text(
            "SELECT CHARACTER_MAXIMUM_LENGTH FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_NAME = 'word_segments' AND COLUMN_NAME = 'word'"
        ))
        current_length = result.fetchone()[0]

        if current_length < 255:
            print(f"✗ word 字段当前长度为 {current_length}，正在扩展到 255...")
            session.execute(text(
                "ALTER TABLE word_segments MODIFY COLUMN word VARCHAR(255) NOT NULL"
            ))
            session.commit()
            print("✓ word 字段长度扩展成功")
        else:
            print(f"✓ word 字段长度已为 {current_length}，无需修改")

    print("\n" + "=" * 70)
    print("✅ 迁移完成！")
    print("=" * 70)
    print("\n变更内容：")
    print("1. word_segments.word_count (INT) - 新增字段，记录词数（1=单词，>1=短语）")
    print("2. word_segments.word (VARCHAR 100→255) - 扩展字段长度以支持短语")
    print("3. 索引 ix_word_segments_word_count - 新增索引")

except Exception as e:
    print(f"\n❌ 迁移失败: {str(e)}")
    import traceback
    traceback.print_exc()
    session.rollback()
finally:
    session.close()
