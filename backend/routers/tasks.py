"""
generic task status endpoints
"""
from fastapi import APIRouter, HTTPException
from backend.services.task_manager import task_manager

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("/{task_id}")
def get_task(task_id: str):
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    return {
        "success": True,
        "data": task
    }


@router.get("/")
def list_tasks(limit: int = 50):
    return {
        "success": True,
        "data": task_manager.list_tasks(limit=limit)
    }
