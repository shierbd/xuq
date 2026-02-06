"""
Background task status model.
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime
from backend.database import Base


class TaskStatus(Base):
    """Persisted task status for background jobs."""
    __tablename__ = "task_status"

    task_id = Column(String(64), primary_key=True, comment="Task ID")
    name = Column(String(100), nullable=False, index=True, comment="Task name")
    status = Column(String(20), nullable=False, index=True, comment="Status")
    progress = Column(Integer, nullable=False, default=0, comment="Progress 0-100")
    message = Column(String(255), comment="Status message")

    params = Column(Text, comment="JSON params")
    result = Column(Text, comment="JSON result")
    error = Column(Text, comment="Error message")

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    started_at = Column(DateTime)
    updated_at = Column(DateTime)
    finished_at = Column(DateTime)

    def __repr__(self) -> str:
        return f"<TaskStatus(task_id={self.task_id}, status={self.status})>"
