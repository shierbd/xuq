"""
simple in-memory task manager for long-running jobs
"""
from __future__ import annotations

import threading
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, Optional, List


class TaskManager:
    """Thread-safe in-memory task manager."""

    def __init__(self, max_tasks: int = 1000):
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._max_tasks = max_tasks

    def _now(self) -> datetime:
        return datetime.utcnow()

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
        with self._lock:
            self._tasks[task_id] = task
            self._prune_if_needed()
        return task_id

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return None
            return self._serialize_task(task)

    def list_tasks(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            items = list(self._tasks.values())
        items.sort(key=lambda t: t.get("created_at") or self._now(), reverse=True)
        return [self._serialize_task(t) for t in items[:limit]]

    def update_task(self, task_id: str, **updates: Any) -> None:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return
            for key, value in updates.items():
                task[key] = value
            task["updated_at"] = self._now()

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
