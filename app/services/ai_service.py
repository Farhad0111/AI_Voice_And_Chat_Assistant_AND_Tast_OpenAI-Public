import os
from dotenv import load_dotenv
import httpx
import logging
import json
import re
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class AIService:
    def __init__(self):
        # OpenAI API settings
        self.use_openai = True
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.default_model = "gpt-3.5-turbo"
        self.openai_model = os.getenv("OPENAI_MODEL", self.default_model)
        self.last_model_used = self.openai_model
        self.fallback_response = False
        self.retry_count = 0
        self.max_retries = 3
        
        # Task Service integration
        from app.services.task_service import TaskService
        self.task_service = TaskService()
        
        # Log configuration
        logger.info(f"Initialized AIService with OpenAI model: {self.openai_model}")
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY environment variable is not set")
    
    async def _call_openai_api(self, user_input, system_prompt):
        """Call the OpenAI API with the configured model"""
        try:
            url = "https://api.openai.com/v1/chat/completions"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.openai_api_key}"
            }
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
            
            # Add context about tasks and schedule if relevant
            if any(keyword in user_input.lower() for keyword in ["task", "schedule", "meeting", "plan", "calendar"]):
                context = self._get_task_context()
                if context:
                    messages.insert(1, {"role": "system", "content": context})
            
            data = {
                "model": self.openai_model,
                "messages": messages,
                "max_tokens": 800,
                "temperature": 0.7
            }
            
            logger.info(f"Sending request to OpenAI API with model: {self.openai_model}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=data, headers=headers)
                logger.info(f"OpenAI API response received in {response.elapsed.total_seconds()}s with status code: {response.status_code}")
                
                if response.status_code == 200:
                    response_data = response.json()
                    self.last_model_used = self.openai_model
                    return {"success": True, "response": response_data["choices"][0]["message"]["content"]}
                    
                elif response.status_code == 429:  # Rate limit or quota exceeded
                    logger.error("OpenAI API quota exceeded or rate limited")
                    return await self._handle_fallback(user_input)
                else:
                    error_message = f"OpenAI API error: {response.status_code}, {response.text}"
                    logger.error(error_message)
                    return await self._handle_fallback(user_input)
                    
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            return await self._handle_fallback(user_input)

    def _get_task_context(self):
        """Get context about current tasks and schedule"""
        user_id = "user_001"  # For demonstration, we'll use a default user
        context = []
        
        # Get today's tasks
        today_tasks = self.task_service.get_today_tasks(user_id)
        if today_tasks:
            context.append("\nToday's tasks:")
            for task in today_tasks:
                context.append(f"- {task['title']}")
                context.append(f"  Description: {task.get('description', 'No description')}")
                context.append(f"  Priority: {task['priority']}")
                context.append(f"  Status: {task['status']}")
        else:
            context.append("\nNo tasks scheduled for today.")
        
        # Get daily recurring tasks
        daily_tasks = self.task_service.get_daily_tasks(user_id)
        if daily_tasks:
            context.append("\nDaily recurring tasks:")
            for task in daily_tasks:
                context.append(f"- {task['title']} (Priority: {task['priority']})")
        
        # Get upcoming tasks
        upcoming_tasks = self.task_service.get_upcoming_tasks(user_id)
        if upcoming_tasks:
            context.append("\nUpcoming tasks:")
            for task in upcoming_tasks:
                context.append(f"- {task['title']} (Due: {task['due_date']}, Priority: {task['priority']})")
        
        # Get high priority tasks
        high_priority = self.task_service.get_highest_priority_task(user_id)
        if high_priority:
            context.append(f"\nHighest priority task: {high_priority['title']}")
            context.append(f"Due date: {high_priority['due_date']}")
            context.append(f"Status: {high_priority['status']}")
        
        return "\n".join(context) if context else "No tasks found."

    def _extract_date_from_query(self, user_input):
        """Extract date from user query"""
        # Look for date patterns like YYYY-MM-DD, MM-DD-YYYY, DD-MM-YYYY
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
            r'(\d{2}-\d{2}-\d{4})',  # MM-DD-YYYY or DD-MM-YYYY
            r'(\d{1,2}/\d{1,2}/\d{4})',  # M/D/YYYY or D/M/YYYY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, user_input)
            if match:
                date_str = match.group(1)
                try:
                    # Try to parse different date formats
                    if '-' in date_str and len(date_str.split('-')[0]) == 4:
                        # YYYY-MM-DD format
                        return date_str
                    elif '-' in date_str:
                        # MM-DD-YYYY or DD-MM-YYYY format
                        parts = date_str.split('-')
                        if len(parts) == 3:
                            # Assume MM-DD-YYYY for now
                            return f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
                    elif '/' in date_str:
                        # M/D/YYYY format
                        parts = date_str.split('/')
                        if len(parts) == 3:
                            return f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
                except:
                    continue
        
        return None

    def _get_date_specific_context(self, target_date, user_id="user_001"):
        """Get context for a specific date"""
        tasks = self.task_service.get_tasks_for_date(user_id, target_date)
        
        if not tasks:
            return f"No tasks found for {target_date}."
        
        context = [f"Tasks for {target_date}:"]
        for task in tasks:
            context.append(f"- {task['title']}")
            context.append(f"  Description: {task.get('description', 'No description')}")
            context.append(f"  Priority: {task['priority']}")
            context.append(f"  Status: {task['status']}")
        
        return "\n".join(context)

    async def _handle_fallback(self, user_input):
        """Handle API failures with graceful fallback responses"""
        self.fallback_response = True
        input_lower = user_input.lower()
        
        # Date-related queries
        if "today" in input_lower or "date" in input_lower:
            today = datetime.now().strftime("%B %d, %Y")
            return {"success": True, "response": f"Today's date is {today}."}
        
        # Schedule-related queries
        if any(word in input_lower for word in ["schedule", "tasks", "meetings"]):
            tasks = self.task_service.get_today_tasks("user_001")
            if tasks:
                response = ["Here's your schedule for today:"]
                for task in tasks:
                    response.append(f"- {task['title']} (Priority: {task['priority']}, Status: {task['status']})")
                return {"success": True, "response": "\n".join(response)}
            else:
                return {"success": True, "response": "You don't have any tasks scheduled for today."}
        
        # Basic greetings
        if any(greeting in input_lower for greeting in ["hi", "hello", "hey", "greetings"]):
            return {"success": True, "response": "Hello! I'm DONNA, your AI assistant. How can I help you today?"}
        
        # How are you
        if "how are you" in input_lower:
            return {"success": True, "response": "I'm functioning well, thank you for asking! How can I assist you today?"}
        
        # Help requests
        if any(word in input_lower for word in ["help", "assist", "support"]):
            return {"success": True, "response": "I'd be happy to help! I can assist you with managing tasks, schedules, meetings, and more. What would you like help with?"}
        
        return {
            "success": True,
            "response": "I can help you manage your tasks and schedule. Would you like to see your current tasks, create a new task, or check your schedule?"
        }

    async def generate_response(self, user_input):
        """Generate a response using OpenAI API or fallback"""
        if not self.openai_api_key:
            logger.warning("OpenAI API key not configured")
            return await self._handle_fallback(user_input)
            
        input_lower = user_input.lower()
        
        # Check for specific date queries first
        extracted_date = self._extract_date_from_query(user_input)
        if extracted_date:
            # User asked for a specific date
            context = self._get_date_specific_context(extracted_date)
            return {"success": True, "response": context}
        
        # Direct handling of schedule and task queries
        if "schedule" in input_lower or "show me my tasks" in input_lower:
            context = self._get_task_context()
            return {"success": True, "response": context}
            
        if "today" in input_lower and "date" in input_lower:
            today = datetime.now().strftime("%B %d, %Y")
            return {"success": True, "response": f"Today's date is {today}."}
            
        # Build system prompt with current context
        base_prompt = """You are DONNA, an intelligent AI assistant specializing in task and schedule management.
        Your capabilities include:
        - Managing tasks and to-do lists
        - Scheduling meetings and appointments
        - Helping organize daily/weekly schedules
        - Providing reminders and updates
        - Engaging in natural conversation
        
        When discussing tasks, always specify their priority and due date. Be helpful, friendly, and concise."""
        
        # Add task context if the query is task-related
        if any(word in input_lower for word in ["task", "schedule", "meeting", "todo", "to-do", "plan", "upcoming"]):
            task_context = self._get_task_context()
            if task_context:
                base_prompt += "\n\nCurrent Task Context:\n" + task_context
            
        system_prompt = base_prompt
        
        try:
            result = await self._call_openai_api(user_input, system_prompt)
            if not result["success"]:
                return await self._handle_fallback(user_input)
            return result
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return await self._handle_fallback(user_input)