"""
Migration: create product_cluster_summaries table.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import text
from backend.database import engine


def upgrade():
    print("Starting migration: create product_cluster_summaries table...")

    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='product_cluster_summaries'"
        ))
        exists = result.first() is not None

        if exists:
            print("[OK] product_cluster_summaries table already exists, skip.")
            return

        conn.execute(text("""
        CREATE TABLE product_cluster_summaries (
            summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
            cluster_id INTEGER NOT NULL,
            cluster_name VARCHAR(200),
            cluster_name_cn VARCHAR(200),
            cluster_size INTEGER NOT NULL,
            avg_rating REAL,
            avg_price REAL,
            total_reviews INTEGER,
            example_products TEXT,
            top_keywords TEXT,
            created_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_time DATETIME
        )
        """))

        conn.execute(text("""
        CREATE INDEX idx_product_cluster_summaries_cluster_id
        ON product_cluster_summaries(cluster_id)
        """))

        conn.commit()
        print("[OK] product_cluster_summaries table created.")


def downgrade():
    print("Starting downgrade: drop product_cluster_summaries table...")
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS product_cluster_summaries"))
        conn.commit()
        print("[OK] product_cluster_summaries table dropped.")


if __name__ == "__main__":
    upgrade()
