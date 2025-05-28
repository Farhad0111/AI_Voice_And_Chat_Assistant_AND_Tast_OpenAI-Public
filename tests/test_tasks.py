import pytest
import json
import os
from app.services.task_service import TaskService

@pytest.fixture
def task_service():
    # Create a test instance of TaskService
    service = TaskService()
    # Clean up any existing test data
    if os.path.exists("tasks.json"):
        os.remove("tasks.json")
    return service

@pytest.fixture
def sample_tasks():
    return {
        "user_001": [
            {
                "title": "Daily Code Review",
                "description": "Review team's code submissions",
                "due_date": "2025-05-28",
                "priority": "high",
                "frequency": "daily",
                "status": "pending"
            },
            {
                "title": "Monthly Report",
                "description": "Prepare monthly status report",
                "due_date": "2025-05-31",
                "priority": "medium",
                "frequency": "monthly",
                "status": "pending"
            },
            {
                "title": "Completed Task",
                "description": "This task is already done",
                "due_date": "2025-05-27",
                "priority": "low",
                "frequency": "one-time",
                "status": "completed"
            }
        ]
    }

def test_get_daily_tasks(task_service, sample_tasks):
    # Setup
    task_service._save_tasks(sample_tasks)
    
    # Test
    daily_tasks = task_service.get_daily_tasks("user_001")
    
    # Verify
    assert len(daily_tasks) == 1
    assert daily_tasks[0]["title"] == "Daily Code Review"
    assert daily_tasks[0]["frequency"] == "daily"

def test_get_monthly_tasks(task_service, sample_tasks):
    # Setup
    task_service._save_tasks(sample_tasks)
    
    # Test
    monthly_tasks = task_service.get_monthly_tasks("user_001")
    
    # Verify
    assert len(monthly_tasks) == 1
    assert monthly_tasks[0]["title"] == "Monthly Report"
    assert monthly_tasks[0]["frequency"] == "monthly"

def test_get_highest_priority_task(task_service, sample_tasks):
    # Setup
    task_service._save_tasks(sample_tasks)
    
    # Test
    highest_priority = task_service.get_highest_priority_task("user_001")
    
    # Verify
    assert highest_priority is not None
    assert highest_priority["title"] == "Daily Code Review"
    assert highest_priority["priority"] == "high"

def test_set_task(task_service):
    # Test data
    new_task = {
        "title": "New Task",
        "description": "Test task",
        "due_date": "2025-06-01",
        "priority": "medium",
        "frequency": "one-time",
        "status": "pending"
    }
    
    # Test
    result = task_service.set_task("user_002", new_task)
    
    # Verify
    assert result is True
    tasks = task_service._load_tasks()
    assert "user_002" in tasks
    assert len(tasks["user_002"]) == 1
    assert tasks["user_002"][0]["title"] == "New Task"

def test_update_task_status(task_service, sample_tasks):
    # Setup
    task_service._save_tasks(sample_tasks)
    
    # Test
    result = task_service.update_task_status("user_001", "Daily Code Review", "completed")
    
    # Verify
    assert result is True
    tasks = task_service._load_tasks()
    updated_task = next(task for task in tasks["user_001"] if task["title"] == "Daily Code Review")
    assert updated_task["status"] == "completed"

def test_delete_task(task_service, sample_tasks):
    # Setup
    task_service._save_tasks(sample_tasks)
    
    # Test
    result = task_service.delete_task("user_001", "Daily Code Review")
    
    # Verify
    assert result is True
    tasks = task_service._load_tasks()
    remaining_tasks = [task["title"] for task in tasks["user_001"]]
    assert "Daily Code Review" not in remaining_tasks

def test_get_tasks_by_status(task_service, sample_tasks):
    # Setup
    task_service._save_tasks(sample_tasks)
    
    # Test
    completed_tasks = task_service.get_tasks_by_status("user_001", "completed")
    
    # Verify
    assert len(completed_tasks) == 1
    assert completed_tasks[0]["title"] == "Completed Task"
