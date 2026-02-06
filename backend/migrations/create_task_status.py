"""
Migration: create task_status table for background tasks.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import text
from backend.database import engine


def upgrade():
    print("Starting migration: create task_status table...")

    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='task_status'"
        ))
        exists = result.first() is not None

        if exists:
            print("[OK] task_status table already exists, skip.")
            return

        conn.execute(text("""
        CREATE TABLE task_status (
            task_id VARCHAR(64) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            status VARCHAR(20) NOT NULL,
            progress INTEGER NOT NULL DEFAULT 0,
            message VARCHAR(255),
            params TEXT,
            result TEXT,
            error TEXT,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            started_at DATETIME,
            updated_at DATETIME,
            finished_at DATETIME
        )
        """))

        conn.execute(text("""
        CREATE INDEX idx_task_status_name ON task_status(name)
        """))

        conn.execute(text("""
        CREATE INDEX idx_task_status_status ON task_status(status)
        """))

        conn.execute(text("""
        CREATE INDEX idx_task_status_created_at ON task_status(created_at)
        """))

        conn.commit()
        print("[OK] task_status table created.")


def downgrade():
    print("Starting downgrade: drop task_status table...")
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS task_status"))
        conn.commit()
        print("[OK] task_status table dropped.")


if __name__ == "__main__":
    upgrade()
