"""
数据库迁移脚本：创建 product_cluster_keywords 表
用于存储商品簇的关键词/词根
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import text
from backend.database import engine


def upgrade():
    """创建 product_cluster_keywords 表"""
    print("开始迁移：创建 product_cluster_keywords 表...")

    with engine.connect() as conn:
        # 检查表是否已存在
        result = conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='product_cluster_keywords'"
        ))
        exists = result.first() is not None

        if exists:
            print("[OK] product_cluster_keywords 表已存在，跳过迁移")
            return

        conn.execute(text("""
        CREATE TABLE product_cluster_keywords (
            keyword_id INTEGER PRIMARY KEY AUTOINCREMENT,
            cluster_id INTEGER NOT NULL,
            keyword VARCHAR(100) NOT NULL,
            count INTEGER,
            score REAL,
            method VARCHAR(50) NOT NULL DEFAULT 'tf',
            created_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """))

        conn.execute(text("""
        CREATE INDEX idx_product_cluster_keywords_cluster_id
        ON product_cluster_keywords(cluster_id)
        """))

        conn.execute(text("""
        CREATE INDEX idx_product_cluster_keywords_keyword
        ON product_cluster_keywords(keyword)
        """))

        conn.commit()
        print("[OK] 成功创建 product_cluster_keywords 表")


def downgrade():
    """删除 product_cluster_keywords 表"""
    print("开始回滚：删除 product_cluster_keywords 表...")
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS product_cluster_keywords"))
        conn.commit()
        print("[OK] 已删除 product_cluster_keywords 表")


if __name__ == "__main__":
    upgrade()
