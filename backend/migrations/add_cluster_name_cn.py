"""
数据库迁移脚本：添加 cluster_name_cn 字段
用于存储类别名称的中文翻译
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import text
from backend.database import engine, SessionLocal

def upgrade():
    """添加 cluster_name_cn 字段"""
    print("开始迁移：添加 cluster_name_cn 字段...")

    with engine.connect() as conn:
        # 检查字段是否已存在
        result = conn.execute(text(
            "SELECT COUNT(*) FROM pragma_table_info('products') WHERE name='cluster_name_cn'"
        ))
        exists = result.scalar() > 0

        if exists:
            print("[OK] cluster_name_cn 字段已存在，跳过迁移")
            return

        # 添加新字段
        conn.execute(text(
            "ALTER TABLE products ADD COLUMN cluster_name_cn VARCHAR(200)"
        ))
        conn.commit()

        print("[OK] 成功添加 cluster_name_cn 字段")

def downgrade():
    """删除 cluster_name_cn 字段"""
    print("开始回滚：删除 cluster_name_cn 字段...")

    with engine.connect() as conn:
        # SQLite 不支持 DROP COLUMN，需要重建表
        print("⚠️ SQLite 不支持直接删除列，需要手动处理")

if __name__ == "__main__":
    upgrade()
