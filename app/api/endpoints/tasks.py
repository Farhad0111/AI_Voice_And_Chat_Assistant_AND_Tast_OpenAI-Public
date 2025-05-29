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

@router.get("/date/{user_id}")
async def get_tasks_for_flexible_date(user_id: str, date_input: str) -> List[Dict]:
    """
    Get tasks for a flexible date input
    Examples: 'today', 'tomorrow', 'next week', 'April 1, 2025', '2025-04-01'
    """
    tasks = task_service.get_tasks_for_flexible_date(user_id, date_input)
    return tasks

@router.get("/range/{user_id}")
async def get_tasks_for_date_range(user_id: str, date_range: str) -> List[Dict]:
    """
    Get tasks for a flexible date range
    Examples: 'this week', 'next 7 days', 'this month', 'next month'
    """
    tasks = task_service.get_tasks_for_date_range(user_id, date_range)
    return tasks

@router.post("/flexible/{user_id}")
async def create_task_with_flexible_date(user_id: str, task_data: Dict) -> Dict:
    """
    Create a task with flexible date parsing
    Required: title, Optional: description, date_input, priority, frequency, status
    date_input examples: 'tomorrow', 'next week', 'April 1, 2025', 'end of month'
    """
    title = task_data.get("title")
    if not title:
        raise HTTPException(status_code=400, detail="Title is required")
    
    description = task_data.get("description", "")
    date_input = task_data.get("date_input", "today")
    priority = task_data.get("priority", "medium")
    frequency = task_data.get("frequency", "one-time")
    status = task_data.get("status", "pending")
    
    success = task_service.create_task_with_flexible_date(
        user_id, title, description, date_input, priority, frequency, status
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to create task")
    
    # Return the parsed date for confirmation
    parsed_info = task_service.parse_and_validate_date(date_input)
    return {
        "status": "success", 
        "message": "Task created successfully",
        "date_info": parsed_info
    }

@router.get("/query/{user_id}")
async def get_tasks_by_flexible_query(user_id: str, query: str) -> List[Dict]:
    """
    Advanced task query with flexible date and filter options
    Examples: 
    - 'tasks for tomorrow'
    - 'high priority tasks this week'
    - 'completed tasks this month'
    - 'daily tasks next week'
    """
    tasks = task_service.get_tasks_by_flexible_query(user_id, query)
    return tasks

@router.get("/validate-date")
async def validate_date_input(date_input: str) -> Dict:
    """
    Validate and parse a flexible date input
    Returns the parsed date and original input for confirmation
    """
    parsed_info = task_service.parse_and_validate_date(date_input)
    return parsed_info
