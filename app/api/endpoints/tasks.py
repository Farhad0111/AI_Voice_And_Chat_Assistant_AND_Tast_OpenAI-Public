from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
from app.services.task_service import TaskService

router = APIRouter()
task_service = TaskService()

@router.get("/daily/{user_id}")
async def get_daily_tasks(user_id: str) -> List[Dict]:
    """Get all daily tasks for a user"""
    tasks = task_service.get_daily_tasks(user_id)
    return tasks

@router.get("/monthly/{user_id}")
async def get_monthly_tasks(user_id: str) -> List[Dict]:
    """Get all monthly tasks for a user"""
    tasks = task_service.get_monthly_tasks(user_id)
    return tasks

@router.get("/priority/{user_id}")
async def get_highest_priority_task(user_id: str) -> Optional[Dict]:
    """Get the highest priority task for a user"""
    task = task_service.get_highest_priority_task(user_id)
    if not task:
        raise HTTPException(status_code=404, detail="No pending tasks found")
    return task

@router.post("/{user_id}")
async def create_task(user_id: str, task: Dict) -> Dict:
    """Create a new task for a user"""
    success = task_service.set_task(user_id, task)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid task data")
    return {"status": "success", "message": "Task created successfully"}

@router.put("/{user_id}/{task_title}")
async def update_task_status(user_id: str, task_title: str, status: str) -> Dict:
    """Update the status of a task"""
    success = task_service.update_task_status(user_id, task_title, status)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "success", "message": "Task status updated successfully"}

@router.get("/status/{user_id}/{status}")
async def get_tasks_by_status(user_id: str, status: str) -> List[Dict]:
    """Get all tasks with a specific status"""
    tasks = task_service.get_tasks_by_status(user_id, status)
    return tasks

@router.delete("/{user_id}/{task_title}")
async def delete_task(user_id: str, task_title: str) -> Dict:
    """Delete a specific task"""
    success = task_service.delete_task(user_id, task_title)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "success", "message": "Task deleted successfully"}
