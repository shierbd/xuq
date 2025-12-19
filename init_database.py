"""
初始化数据库
创建所有表
"""
import sys
import os

# 设置UTF-8编码输出
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from storage.models import create_all_tables

if __name__ == "__main__":
    try:
        create_all_tables()
        print("Database tables created successfully!")
    except Exception as e:
        print(f"Error creating tables: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
