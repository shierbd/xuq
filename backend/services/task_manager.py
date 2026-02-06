"""
simple in-memory task manager for long-running jobs
"""
from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, Optional, List

from sqlalchemy import desc
from backend.database import SessionLocal
from backend.models.task_status import TaskStatus


class TaskManager:
    """Thread-safe in-memory task manager."""

    def __init__(self, max_tasks: int = 1000):
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._max_tasks = max_tasks

    def _now(self) -> datetime:
        return datetime.utcnow()

    def _json_dumps(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        try:
            return json.dumps(value, ensure_ascii=False)
        except Exception:
            return json.dumps(str(value), ensure_ascii=False)

    def _json_loads(self, value: Optional[str]) -> Any:
        if not value:
            return None
        try:
            return json.loads(value)
        except Exception:
            return value

    def _serialize_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        def to_iso(value: Optional[datetime]) -> Optional[str]:
            return value.isoformat() if value else None

        return {
            "task_id": task["task_id"],
            "name": task["name"],
            "status": task["status"],
            "progress": task.get("progress", 0),
            "message": task.get("message"),
            "created_at": to_iso(task.get("created_at")),
            "started_at": to_iso(task.get("started_at")),
            "updated_at": to_iso(task.get("updated_at")),
            "finished_at": to_iso(task.get("finished_at")),
            "params": task.get("params", {}),
            "result": task.get("result"),
            "error": task.get("error"),
        }

    def _serialize_row(self, row: TaskStatus) -> Dict[str, Any]:
        def to_iso(value: Optional[datetime]) -> Optional[str]:
            return value.isoformat() if value else None

        return {
            "task_id": row.task_id,
            "name": row.name,
            "status": row.status,
            "progress": row.progress or 0,
            "message": row.message,
            "created_at": to_iso(row.created_at),
            "started_at": to_iso(row.started_at),
            "updated_at": to_iso(row.updated_at),
            "finished_at": to_iso(row.finished_at),
            "params": self._json_loads(row.params) or {},
            "result": self._json_loads(row.result),
            "error": row.error,
        }

    def _db_create(self, task: Dict[str, Any]) -> None:
        try:
            with SessionLocal() as db:
                row = TaskStatus(
                    task_id=task["task_id"],
                    name=task["name"],
                    status=task["status"],
                    progress=task.get("progress", 0),
                    message=task.get("message"),
                    params=self._json_dumps(task.get("params")),
                    result=self._json_dumps(task.get("result")),
                    error=task.get("error"),
                    created_at=task.get("created_at"),
                    started_at=task.get("started_at"),
                    updated_at=task.get("updated_at"),
                    finished_at=task.get("finished_at"),
                )
                db.add(row)
                db.commit()
        except Exception:
            # Keep in-memory tasks even if DB fails
            return

    def _db_update(self, task_id: str, updates: Dict[str, Any]) -> None:
        try:
            with SessionLocal() as db:
                row = db.get(TaskStatus, task_id)
                if not row:
                    return
                for key, value in updates.items():
                    if key in {"params", "result"}:
                        value = self._json_dumps(value)
                    setattr(row, key, value)
                db.commit()
        except Exception:
            return

    def _db_get(self, task_id: str) -> Optional[Dict[str, Any]]:
        try:
            with SessionLocal() as db:
                row = db.get(TaskStatus, task_id)
                if not row:
                    return None
                return self._serialize_row(row)
        except Exception:
            return None

    def _db_list(self, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            with SessionLocal() as db:
                rows = db.query(TaskStatus).order_by(desc(TaskStatus.created_at)).limit(limit).all()
                return [self._serialize_row(row) for row in rows]
        except Exception:
            return []

    def _prune_if_needed(self) -> None:
        if len(self._tasks) <= self._max_tasks:
            return
        # remove oldest tasks when exceeding max_tasks
        sorted_items = sorted(
            self._tasks.items(),
            key=lambda item: item[1].get("created_at") or self._now()
        )
        overflow = len(self._tasks) - self._max_tasks
        for i in range(overflow):
            task_id, _ = sorted_items[i]
            self._tasks.pop(task_id, None)

    def create_task(self, name: str, params: Optional[Dict[str, Any]] = None) -> str:
        task_id = uuid.uuid4().hex
        now = self._now()
        task = {
            "task_id": task_id,
            "name": name,
            "status": "pending",
            "progress": 0,
            "message": "queued",
            "created_at": now,
            "started_at": None,
            "updated_at": now,
            "finished_at": None,
            "params": params or {},
            "result": None,
            "error": None,
        }
        self._db_create(task)
        with self._lock:
            self._tasks[task_id] = task
            self._prune_if_needed()
        return task_id

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        db_task = self._db_get(task_id)
        if db_task:
            return db_task
        with self._lock:
            task = self._tasks.get(task_id)
        if not task:
            return None
        return self._serialize_task(task)

    def list_tasks(self, limit: int = 50) -> List[Dict[str, Any]]:
        db_items = self._db_list(limit=limit)
        if db_items:
            return db_items
        with self._lock:
            items = list(self._tasks.values())
        items.sort(key=lambda t: t.get("created_at") or self._now(), reverse=True)
        return [self._serialize_task(t) for t in items[:limit]]

    def update_task(self, task_id: str, **updates: Any) -> None:
        updates["updated_at"] = self._now()
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                task = None
            for key, value in updates.items():
                if task is not None:
                    task[key] = value
        self._db_update(task_id, updates)

    def set_progress(self, task_id: str, progress: float, message: Optional[str] = None) -> None:
        progress_int = int(max(0, min(100, round(progress))))
        updates: Dict[str, Any] = {"progress": progress_int}
        if message:
            updates["message"] = message
        self.update_task(task_id, **updates)

    def run_task(self, task_id: str, func: Callable[[], Any]) -> None:
        def _runner():
            self.update_task(
                task_id,
                status="running",
                started_at=self._now(),
                message="running"
            )
            try:
                result = func()
                self.update_task(
                    task_id,
                    status="success",
                    progress=100,
                    finished_at=self._now(),
                    message="completed",
                    result=result,
                    error=None
                )
            except Exception as exc:  # pragma: no cover - defensive
                self.update_task(
                    task_id,
                    status="failed",
                    finished_at=self._now(),
                    message="failed",
                    error=str(exc)
                )

        thread = threading.Thread(target=_runner, daemon=True)
        thread.start()


# global singleton
_task_manager = TaskManager()


"""Return the shared task manager."""
def get_task_manager() -> TaskManager:
    return _task_manager


# convenient alias
_task_manager_singleton = _task_manager

"""Convenient import name."""
task_manager = _task_manager
