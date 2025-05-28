import json
import os
from typing import Dict, Optional, List
from datetime import datetime, date

class TaskService:
    def __init__(self):
        self.tasks_file = "tasks.json"
        # Create tasks file if it doesn't exist
        if not os.path.exists(self.tasks_file):
            with open(self.tasks_file, "w") as f:
                json.dump({}, f)

    def _load_tasks(self) -> Dict:
        try:
            with open(self.tasks_file, "r") as f:
                return json.load(f)
        except:
            return {}

    def _save_tasks(self, tasks: Dict):
        with open(self.tasks_file, "w") as f:
            json.dump(tasks, f, indent=4)

    def get_all_tasks(self, user_id: str) -> List[Dict]:
        """Get all tasks for a user"""
        tasks = self._load_tasks()
        return tasks.get(user_id, [])

    def get_today_tasks(self, user_id: str) -> List[Dict]:
        """Get all tasks due today"""
        tasks = self._load_tasks()
        if user_id not in tasks:
            return []
        
        today = date.today().isoformat()
        return [
            task for task in tasks[user_id]
            if task.get("due_date") == today and task.get("status") != "completed"
        ]

    def get_daily_tasks(self, user_id: str) -> List[Dict]:
        """Get all daily tasks that are not completed"""
        tasks = self._load_tasks()
        if user_id not in tasks:
            return []
        
        return [
            task for task in tasks[user_id]
            if task.get("frequency") == "daily" and task.get("status") != "completed"
        ]

    def get_tasks_for_date(self, user_id: str, target_date: str) -> List[Dict]:
        """Get all tasks for a specific date (YYYY-MM-DD format)"""
        tasks = self._load_tasks()
        if user_id not in tasks:
            return []
        
        return [
            task for task in tasks[user_id]
            if task.get("due_date") == target_date and task.get("status") != "completed"
        ]

    def has_tasks_for_date(self, user_id: str, target_date: str) -> bool:
        """Check if there are any tasks for a specific date"""
        tasks = self.get_tasks_for_date(user_id, target_date)
        return len(tasks) > 0

    def get_monthly_tasks(self, user_id: str) -> List[Dict]:
        """Get all monthly tasks that are not completed"""
        tasks = self._load_tasks()
        if user_id not in tasks:
            return []
        
        return [
            task for task in tasks[user_id]
            if task.get("frequency") == "monthly" and task.get("status") != "completed"
        ]

    def get_highest_priority_task(self, user_id: str) -> Optional[Dict]:
        """Get the highest priority task that is not completed"""
        tasks = self._load_tasks()
        if user_id not in tasks:
            return None

        priority_levels = {"high": 3, "medium": 2, "low": 1}
        incomplete_tasks = [
            task for task in tasks[user_id]
            if task.get("status") != "completed"
        ]
        
        if not incomplete_tasks:
            return None

        return max(
            incomplete_tasks,
            key=lambda x: priority_levels.get(x.get("priority", "low"), 0)
        )

    def create_task(self, user_id: str, title: str, description: str = "", due_date: str = None, 
                   priority: str = "medium", frequency: str = "once", status: str = "pending") -> bool:
        """Create a new task with smart defaults"""
        if not due_date:
            due_date = date.today().isoformat()
            
        task_data = {
            "title": title,
            "description": description,
            "due_date": due_date,
            "priority": priority,
            "frequency": frequency,
            "status": status,
            "created_at": datetime.now().isoformat()
        }
        
        return self.set_task(user_id, task_data)

    def set_task(self, user_id: str, task_data: Dict) -> bool:
        """Store or update a task for a user"""
        tasks = self._load_tasks()
        if user_id not in tasks:
            tasks[user_id] = []
        
        # Ensure required fields are present
        required_fields = ["title", "due_date", "priority", "frequency", "status"]
        if not all(field in task_data for field in required_fields):
            return False

        # If task with same title exists, update it
        for i, task in enumerate(tasks[user_id]):
            if task.get("title") == task_data["title"]:
                tasks[user_id][i] = task_data
                self._save_tasks(tasks)
                return True

        # Otherwise add new task
        tasks[user_id].append(task_data)
        self._save_tasks(tasks)
        return True

    def update_task_status(self, user_id: str, task_title: str, new_status: str) -> bool:
        """Update the status of a specific task"""
        tasks = self._load_tasks()
        if user_id not in tasks:
            return False

        for task in tasks[user_id]:
            if task.get("title") == task_title:
                task["status"] = new_status
                task["updated_at"] = datetime.now().isoformat()
                self._save_tasks(tasks)
                return True
        return False

    def get_tasks_by_status(self, user_id: str, status: str) -> List[Dict]:
        """Get all tasks with a specific status"""
        tasks = self._load_tasks()
        if user_id not in tasks:
            return []

        return [
            task for task in tasks[user_id]
            if task.get("status") == status
        ]

    def get_tasks_by_date_range(self, user_id: str, start_date: str, end_date: str) -> List[Dict]:
        """Get all tasks within a date range"""
        tasks = self._load_tasks()
        if user_id not in tasks:
            return []

        return [
            task for task in tasks[user_id]
            if start_date <= task.get("due_date", "") <= end_date
        ]

    def get_upcoming_tasks(self, user_id: str, days: int = 7) -> List[Dict]:
        """Get tasks due in the next X days"""
        tasks = self._load_tasks()
        if user_id not in tasks:
            return []

        from datetime import timedelta
        today = date.today()
        end_date = (today + timedelta(days=days)).isoformat()
        today = today.isoformat()

        return [
            task for task in tasks[user_id]
            if today <= task.get("due_date", "") <= end_date and task.get("status") != "completed"
        ]

    def delete_task(self, user_id: str, task_title: str) -> bool:
        """Delete a specific task"""
        tasks = self._load_tasks()
        if user_id not in tasks:
            return False

        initial_length = len(tasks[user_id])
        tasks[user_id] = [
            task for task in tasks[user_id]
            if task.get("title") != task_title
        ]
        
        if len(tasks[user_id]) < initial_length:
            self._save_tasks(tasks)
            return True
            
        return False
