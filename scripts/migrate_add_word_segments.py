# -*- coding: utf-8 -*-
"""
数据库迁移脚本：添加分词结果表和批次记录表
运行此脚本将创建word_segments和segmentation_batches两张新表
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from storage.models import create_all_tables, get_engine, Base
from storage.models import WordSegment, SegmentationBatch


def main():
    print("=" * 60)
    print("[Migrate] Adding word segmentation tables")
    print("=" * 60)

    try:
        # 获取数据库引擎
        engine = get_engine()

        print("\n[Check] Checking existing tables...")
        from sqlalchemy import inspect
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        print(f"[Info] Existing tables: {', '.join(existing_tables)}")

        # 只创建新表（不影响已有表）
        print("\n[Create] Creating new tables...")

        # 创建word_segments表
        if 'word_segments' not in existing_tables:
            WordSegment.__table__.create(engine)
            print("[OK] Created table: word_segments")
        else:
            print("[Skip] Table already exists: word_segments")

        # 创建segmentation_batches表
        if 'segmentation_batches' not in existing_tables:
            SegmentationBatch.__table__.create(engine)
            print("[OK] Created table: segmentation_batches")
        else:
            print("[Skip] Table already exists: segmentation_batches")

        print("\n" + "=" * 60)
        print("[Success] Database migration completed!")
        print("=" * 60)

        # 显示表结构
        print("\n[Info] New table structures:")
        print("\n[word_segments]")
        print("  - word_id: primary key")
        print("  - word: word text (unique index)")
        print("  - frequency: occurrence count")
        print("  - pos_tag, pos_category, pos_chinese: POS info")
        print("  - translation: Chinese translation")
        print("  - is_root: whether it's a root word")
        print("  - root_round: root word round")
        print("  - root_source: root word source")

        print("\n[segmentation_batches]")
        print("  - batch_id: primary key")
        print("  - phrase_count: number of phrases processed")
        print("  - word_count: number of words generated")
        print("  - new_word_count: number of new words")
        print("  - duration_seconds: processing time")
        print("  - status: batch status")

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
