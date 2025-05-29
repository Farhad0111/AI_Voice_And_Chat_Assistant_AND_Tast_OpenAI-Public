import json
import os
from typing import Dict, Optional, List
from datetime import datetime, date
from ..utils.date_parser import FlexibleDateParser

class TaskService:
    def __init__(self):
        self.tasks_file = "tasks.json"
        self.date_parser = FlexibleDateParser()
        # Create tasks file if it doesn't exist
        if not os.path.exists(self.tasks_file):
            with open(self.tasks_file, "w") as f:
                json.dump({}, f)
    
    def get_data_source(self) -> str:
        """Returns the data source - always tasks.json"""
        return "tasks.json"

    def _load_tasks(self) -> Dict:
        """Load tasks exclusively from tasks.json file"""
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
        """Create a new task with smart defaults and flexible date parsing"""
        if not due_date:
            due_date = date.today().isoformat()
        else:
            # Parse flexible date input (e.g., "tomorrow", "next week", "April 1, 2025")
            due_date = self.date_parser.parse_date(due_date)
            
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

    def search_tasks_by_keyword(self, user_id: str, keyword: str) -> List[Dict]:
        """Search tasks by keyword in title or description - data from tasks.json only"""
        tasks = self._load_tasks()
        if user_id not in tasks:
            return []
        
        keyword_lower = keyword.lower()
        return [
            task for task in tasks[user_id]
            if keyword_lower in task.get("title", "").lower() or 
               keyword_lower in task.get("description", "").lower()
        ]
    
    def get_tasks_by_priority(self, user_id: str, priority: str) -> List[Dict]:
        """Get tasks by priority level - data from tasks.json only"""
        tasks = self._load_tasks()
        if user_id not in tasks:
            return []
        
        return [
            task for task in tasks[user_id]
            if task.get("priority") == priority
        ]
    
    def get_tasks_by_frequency(self, user_id: str, frequency: str) -> List[Dict]:
        """Get tasks by frequency - data from tasks.json only"""
        tasks = self._load_tasks()
        if user_id not in tasks:
            return []
        
        return [
            task for task in tasks[user_id]
            if task.get("frequency") == frequency
        ]
    
    def get_task_count(self, user_id: str) -> int:
        """Get total task count from tasks.json"""
        tasks = self._load_tasks()
        if user_id not in tasks:
            return 0
        return len(tasks[user_id])
    
    def get_task_statistics(self, user_id: str) -> Dict:
        """Get task statistics from tasks.json only"""
        tasks = self._load_tasks()
        if user_id not in tasks:
            return {"total": 0, "pending": 0, "in_progress": 0, "completed": 0}
        
        user_tasks = tasks[user_id]
        stats = {
            "total": len(user_tasks),
            "pending": len([t for t in user_tasks if t.get("status") == "pending"]),
            "in_progress": len([t for t in user_tasks if t.get("status") == "in progress"]),
            "completed": len([t for t in user_tasks if t.get("status") == "completed"]),
            "high_priority": len([t for t in user_tasks if t.get("priority") == "high"]),
            "medium_priority": len([t for t in user_tasks if t.get("priority") == "medium"]),
            "low_priority": len([t for t in user_tasks if t.get("priority") == "low"]),
            "daily_tasks": len([t for t in user_tasks if t.get("frequency") == "daily"]),
            "weekly_tasks": len([t for t in user_tasks if t.get("frequency") == "weekly"]),
            "monthly_tasks": len([t for t in user_tasks if t.get("frequency") == "monthly"]),
            "one_time_tasks": len([t for t in user_tasks if t.get("frequency") == "one-time"])
        }
        return stats

    def get_tasks_for_flexible_date(self, user_id: str, date_input: str) -> List[Dict]:
        """Get tasks for a flexible date input (e.g., 'tomorrow', 'next week', 'April 1, 2025')"""
        tasks = self._load_tasks()
        if user_id not in tasks:
            return []
        
        target_date = self.date_parser.parse_date(date_input)
        return [
            task for task in tasks[user_id]
            if task.get("due_date") == target_date
        ]
    
    def get_tasks_for_date_range(self, user_id: str, date_range_input: str) -> List[Dict]:
        """Get tasks for a flexible date range (e.g., 'this week', 'next 7 days', 'this month')"""
        tasks = self._load_tasks()
        if user_id not in tasks:
            return []
        
        start_date, end_date = self.date_parser.parse_date_range(date_range_input)
        return [
            task for task in tasks[user_id]
            if start_date <= task.get("due_date", "") <= end_date
        ]
    
    def create_task_with_flexible_date(self, user_id: str, title: str, description: str = "", 
                                     date_input: str = "today", priority: str = "medium", 
                                     frequency: str = "one-time", status: str = "pending") -> bool:
        """Create a task with flexible date input parsing"""
        due_date = self.date_parser.parse_date(date_input)
        
        task_data = {
            "title": title,
            "description": description,
            "due_date": due_date,
            "priority": priority,
            "frequency": frequency,
            "status": status,
            "created_at": datetime.now().isoformat(),
            "original_date_input": date_input  # Store original input for reference
        }
        
        return self.set_task(user_id, task_data)
    
    def get_tasks_by_flexible_query(self, user_id: str, query: str) -> List[Dict]:
        """
        Advanced query method that handles flexible date queries from tasks.json
        Examples: 'tasks for tomorrow', 'high priority tasks this week', 'completed tasks this month'
        """
        tasks = self._load_tasks()
        if user_id not in tasks:
            return []
        
        query = query.lower().strip()
        user_tasks = tasks[user_id]
        
        # Extract date information from query
        date_keywords = ['today', 'tomorrow', 'yesterday', 'this week', 'next week', 
                        'this month', 'next month', 'end of month']
        
        found_date = None
        for keyword in date_keywords:
            if keyword in query:
                found_date = keyword
                break
        
        # Filter by date if found
        if found_date:
            if found_date in ['this week', 'next week', 'this month', 'next month']:
                start_date, end_date = self.date_parser.parse_date_range(found_date)
                filtered_tasks = [
                    task for task in user_tasks
                    if start_date <= task.get("due_date", "") <= end_date
                ]
            else:
                target_date = self.date_parser.parse_date(found_date)
                filtered_tasks = [
                    task for task in user_tasks
                    if task.get("due_date") == target_date
                ]
        else:
            filtered_tasks = user_tasks
        
        # Filter by priority if mentioned
        if 'high priority' in query or 'high' in query:
            filtered_tasks = [t for t in filtered_tasks if t.get("priority") == "high"]
        elif 'medium priority' in query or 'medium' in query:
            filtered_tasks = [t for t in filtered_tasks if t.get("priority") == "medium"]
        elif 'low priority' in query or 'low' in query:
            filtered_tasks = [t for t in filtered_tasks if t.get("priority") == "low"]
        
        # Filter by status if mentioned
        if 'completed' in query:
            filtered_tasks = [t for t in filtered_tasks if t.get("status") == "completed"]
        elif 'pending' in query:
            filtered_tasks = [t for t in filtered_tasks if t.get("status") == "pending"]
        elif 'in progress' in query:
            filtered_tasks = [t for t in filtered_tasks if t.get("status") == "in progress"]
        
        # Filter by frequency if mentioned
        if 'daily' in query:
            filtered_tasks = [t for t in filtered_tasks if t.get("frequency") == "daily"]
        elif 'weekly' in query:
            filtered_tasks = [t for t in filtered_tasks if t.get("frequency") == "weekly"]
        elif 'monthly' in query:
            filtered_tasks = [t for t in filtered_tasks if t.get("frequency") == "monthly"]
        
        return filtered_tasks
    
    def parse_and_validate_date(self, date_input: str) -> Dict[str, str]:
        """Parse and validate a date input, return both parsed and original"""
        parsed_date = self.date_parser.parse_date(date_input)
        return {
            "original_input": date_input,
            "parsed_date": parsed_date,
            "is_valid": True  # FlexibleDateParser always returns a valid date
        }
