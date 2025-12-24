"""
创建seed_words表的迁移脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from storage.models import create_all_tables

if __name__ == "__main__":
    print("Creating seed_words table...")
    try:
        create_all_tables()
        print("SUCCESS: seed_words table created")
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
