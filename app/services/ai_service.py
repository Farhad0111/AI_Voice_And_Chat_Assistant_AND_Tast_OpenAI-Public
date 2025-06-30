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
        """Get comprehensive context about current tasks and schedule"""
        user_id = "user_001"  # For demonstration, we'll use a default user
        context = []
        
        # Get today's date for reference
        today = datetime.now().strftime("%B %d, %Y")
        context.append(f"📅 Today's Date: {today}")
        
        # Get today's tasks
        today_tasks = self.task_service.get_today_tasks(user_id)
        if today_tasks:
            context.append(f"\n📋 TODAY'S TASKS ({len(today_tasks)} tasks):")
            for task in today_tasks:
                status_emoji = "✅" if task['status'] == "completed" else "🔄" if task['status'] == "in progress" else "⏳"
                priority_emoji = "🔴" if task['priority'] == "high" else "🟡" if task['priority'] == "medium" else "🟢"
                context.append(f"  {status_emoji} {priority_emoji} {task['title']}")
                if task.get('description', '').strip():
                    context.append(f"      Description: {task['description']}")
                context.append(f"      Priority: {task['priority']} | Status: {task['status']}")
        else:
            context.append("\n📋 TODAY'S TASKS: No tasks scheduled for today")
        
        # Get high priority tasks
        high_priority = self.task_service.get_highest_priority_task(user_id)
        if high_priority:
            context.append(f"\n🚨 HIGHEST PRIORITY TASK:")
            context.append(f"   {high_priority['title']}")
            context.append(f"   Due: {high_priority['due_date']} | Status: {high_priority['status']}")
        
        # Get upcoming tasks (next 7 days)
        upcoming_tasks = self.task_service.get_upcoming_tasks(user_id, 7)
        if upcoming_tasks:
            context.append(f"\n📈 UPCOMING TASKS (Next 7 days - {len(upcoming_tasks)} tasks):")
            for task in upcoming_tasks[:5]:  # Limit to 5 for brevity
                priority_emoji = "🔴" if task['priority'] == "high" else "🟡" if task['priority'] == "medium" else "🟢"
                context.append(f"  {priority_emoji} {task['title']} (Due: {task['due_date']})")
            if len(upcoming_tasks) > 5:
                context.append(f"  ... and {len(upcoming_tasks) - 5} more tasks")
        else:
            context.append("\n📈 UPCOMING TASKS: No upcoming tasks in the next 7 days")
        
        # Get daily recurring tasks
        daily_tasks = self.task_service.get_daily_tasks(user_id)
        if daily_tasks:
            context.append(f"\n🔄 DAILY RECURRING TASKS ({len(daily_tasks)} tasks):")
            for task in daily_tasks:
                priority_emoji = "🔴" if task['priority'] == "high" else "🟡" if task['priority'] == "medium" else "🟢"
                context.append(f"  {priority_emoji} {task['title']} (Priority: {task['priority']})")
        
        # Get task statistics
        all_tasks = self.task_service.get_all_tasks(user_id)
        if all_tasks:
            completed_count = len([t for t in all_tasks if t.get('status') == 'completed'])
            pending_count = len([t for t in all_tasks if t.get('status') == 'pending'])
            in_progress_count = len([t for t in all_tasks if t.get('status') == 'in progress'])
            
            context.append(f"\n📊 TASK SUMMARY:")
            context.append(f"   Total Tasks: {len(all_tasks)}")
            context.append(f"   Completed: {completed_count} | In Progress: {in_progress_count} | Pending: {pending_count}")
        
        return "\n".join(context) if context else "No task information available."

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
        
        # Date and time queries
        if any(word in input_lower for word in ["today", "date", "time", "when"]):
            today = datetime.now()
            formatted_date = today.strftime("%B %d, %Y")
            formatted_time = today.strftime("%I:%M %p")
            return {
                "success": True, 
                "response": f"📅 Today's date is {formatted_date}\n🕐 Current time is {formatted_time}"
            }
        
        # Enhanced schedule and task-related queries with flexible date parsing
        if any(word in input_lower for word in ["schedule", "tasks", "meetings", "todo", "to-do"]):
            user_id = "user_001"
            
            # Handle flexible date queries
            date_response = self._handle_flexible_date_query(input_lower, user_id)
            if date_response:
                return date_response
            
            if "today" in input_lower:
                tasks = self.task_service.get_today_tasks(user_id)
                if tasks:
                    response = ["📋 Here's your schedule for today:"]
                    for task in tasks:
                        priority_emoji = "🔴" if task['priority'] == "high" else "🟡" if task['priority'] == "medium" else "🟢"
                        status_emoji = "✅" if task['status'] == "completed" else "🔄" if task['status'] == "in progress" else "⏳"
                        response.append(f"{status_emoji} {priority_emoji} {task['title']} (Priority: {task['priority']})")
                    return {"success": True, "response": "\n".join(response)}
                else:
                    return {"success": True, "response": "📋 You don't have any tasks scheduled for today. Would you like me to help you create some?"}
            
            elif "upcoming" in input_lower:
                tasks = self.task_service.get_upcoming_tasks(user_id)
                if tasks:
                    response = ["📈 Here are your upcoming tasks:"]
                    for task in tasks[:5]:  # Limit to 5 tasks
                        priority_emoji = "🔴" if task['priority'] == "high" else "🟡" if task['priority'] == "medium" else "🟢"
                        response.append(f"{priority_emoji} {task['title']} (Due: {task['due_date']})")
                    if len(tasks) > 5:
                        response.append(f"... and {len(tasks) - 5} more tasks")
                    return {"success": True, "response": "\n".join(response)}
                else:
                    return {"success": True, "response": "📈 You don't have any upcoming tasks in the next 7 days."}
            
            else:
                # General task query
                context = self._get_task_context()
                return {"success": True, "response": context}
        
        # Greeting responses
        if any(greeting in input_lower for greeting in ["hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening"]):
            greetings = [
                "Hello! I'm DONNA, your AI productivity assistant. 🤖",
                "Hi there! I'm DONNA, ready to help you manage your tasks and schedule. 📋",
                "Hey! I'm DONNA, your personal AI assistant for task management. ✨",
                "Greetings! I'm DONNA, here to help you stay organized and productive. 🚀"
            ]
            import random
            greeting = random.choice(greetings)
            return {"success": True, "response": f"{greeting}\n\nHow can I help you today?"}
        
        # Status and well-being queries
        if any(phrase in input_lower for phrase in ["how are you", "how do you feel", "what's up"]):
            responses = [
                "I'm functioning perfectly and ready to help you be more productive! 💪",
                "I'm doing great! My circuits are optimized and I'm excited to help you organize your day! ⚡",
                "I'm operating at full capacity and looking forward to helping you tackle your tasks! 🎯",
                "I'm excellent, thank you for asking! How can I help make your day more organized? 📊"
            ]
            import random
            return {"success": True, "response": random.choice(responses)}
        
        # Help and capability queries
        if any(word in input_lower for word in ["help", "assist", "support", "what can you do", "capabilities"]):
            help_text = """🤖 I'm DONNA, your AI assistant! Here's how I can help:

📋 **Task Management:**
• Create, update, and delete tasks
• Set priorities and due dates
• Track task progress and status

📅 **Schedule Organization:**
• View today's tasks and schedule
• Show upcoming tasks and deadlines
• Manage recurring tasks

🗣️ **Voice & Chat:**
• Process voice commands
• Provide natural language responses
• Support continuous voice mode

💡 **Just ask me things like:**
• "Show me my tasks"
• "What's my schedule today?"
• "Create a new task"
• "What's my highest priority task?"

How would you like to get started?"""
            return {"success": True, "response": help_text}
        
        # Task creation hints
        if any(word in input_lower for word in ["create", "add", "new"]):
            return {
                "success": True, 
                "response": "🆕 I can help you create a new task! Please tell me:\n• Task title\n• Due date (optional)\n• Priority level (high/medium/low)\n• Any description or notes\n\nFor example: 'Create a high priority task: Review presentation by Friday'"
            }
        
        # Default response with helpful suggestions
        return {
            "success": True,
            "response": """🤖 I'm DONNA, your AI productivity assistant! 

I can help you with:
📋 Managing your tasks and to-do lists
📅 Organizing your schedule and deadlines  
🗣️ Voice commands and natural conversation

Try asking me:
• "Show me my tasks"
• "What's my schedule today?"
• "Help me create a new task"
• "What can you do?"

What would you like to work on?"""
        }

    async def generate_response(self, user_input):
        """Generate a response using OpenAI API or fallback"""
        if not self.openai_api_key:
            logger.warning("OpenAI API key not configured")
            return await self._handle_fallback(user_input)
            
        input_lower = user_input.lower()
        
        # Check for flexible date queries first (priority handling)
        user_id = "user_001"  # Default user for now
        date_response = self._handle_flexible_date_query(input_lower, user_id)
        if date_response:
            return date_response
        
        # Check for specific date queries
        extracted_date = self._extract_date_from_query(user_input)
        if extracted_date:
            # User asked for a specific date
            context = self._get_date_specific_context(extracted_date)
            return {"success": True, "response": context}
        
        # Direct handling of schedule and task queries with better organization
        if "schedule" in input_lower or "show me my tasks" in input_lower:
            if "today" in input_lower:
                return self._get_today_schedule_response()
            elif "week" in input_lower or "organize" in input_lower:
                return self._get_weekly_schedule_response()
            else:
                context = self._get_task_context()
                return {"success": True, "response": context}
            
        if "today" in input_lower and ("schedule" in input_lower or "tasks" in input_lower):
            return self._get_today_schedule_response()
            
        if "today" in input_lower and "date" in input_lower:
            today = datetime.now().strftime("%B %d, %Y")
            return {"success": True, "response": f"Today's date is {today}."}
            
        # Build comprehensive system prompt with current context
        base_prompt = """You are DONNA, an advanced AI voice and chat assistant designed to help users manage their tasks, schedules, and daily productivity.

## CORE IDENTITY & PERSONALITY
- Name: DONNA (Digital Organized Neural Network Assistant)
- Personality: Professional, helpful, friendly, and proactive
- Communication Style: Clear, concise, and personable
- Tone: Supportive and encouraging while maintaining professionalism

## PRIMARY CAPABILITIES

### 📋 TASK MANAGEMENT
- Create, update, and delete tasks
- Set task priorities (high, medium, low)
- Manage task statuses (pending, in progress, completed)
- Handle different task frequencies (one-time, daily, weekly, monthly)
- Organize tasks by due dates and deadlines
- Provide task summaries and progress tracking

### 📅 SCHEDULE MANAGEMENT  
- Display today's tasks and schedule
- Show upcoming tasks (next 7 days by default)
- Filter tasks by specific dates
- Identify highest priority tasks
- Manage recurring tasks (daily, weekly, monthly)
- Provide date-specific task context

### 🗣️ VOICE & CHAT INTERACTION
- Process both text and voice commands
- Provide natural language responses
- Support continuous voice mode for hands-free operation
- Convert responses to speech using female voice synthesis
- Handle speech-to-text input processing

### 📊 PRODUCTIVITY INSIGHTS
- Analyze task patterns and workload
- Suggest task prioritization strategies
- Provide productivity reminders and motivational support
- Help with time management and planning

## RESPONSE GUIDELINES

### Task Information Format:
- Always include task title, priority, due date, and status
- Use clear formatting: "• Task Title (Priority: high, Due: YYYY-MM-DD, Status: pending)"
- Group similar tasks together (e.g., all high-priority tasks)

### Date & Time Handling:
- Use full date format: "May 29, 2025" for user-friendly display
- Support various date input formats (YYYY-MM-DD, MM-DD-YYYY, natural language)
- Provide context-aware date responses

### Conversation Flow:
- Ask clarifying questions when task details are incomplete
- Offer proactive suggestions for task organization
- Maintain conversation context across multiple interactions
- Handle both specific commands and casual conversation

### Error Handling:
- Gracefully handle missing information
- Provide helpful suggestions when tasks aren't found
- Offer alternatives when requested actions cannot be completed

## BEHAVIORAL INSTRUCTIONS
- Always acknowledge user requests positively
- Provide actionable next steps or suggestions
- Use encouraging language to motivate productivity
- Be concise but thorough in explanations
- Prioritize user privacy and data security
- Adapt communication style to user preferences

When discussing tasks, always specify their priority and due date. Be helpful, friendly, and concise while maintaining a professional demeanor."""
        
        # Add dynamic context based on query type
        context_additions = []
        
        if any(word in input_lower for word in ["task", "schedule", "meeting", "todo", "to-do", "plan", "upcoming"]):
            task_context = self._get_task_context()
            if task_context:
                context_additions.append(f"\n## CURRENT TASK CONTEXT\n{task_context}")
                
        if any(word in input_lower for word in ["help", "what can you do", "capabilities", "features"]):
            context_additions.append(f"""
## AVAILABLE COMMANDS REFERENCE
- "Show me my tasks" - Display all current tasks
- "What's my schedule today?" - Show today's tasks
- "Create a new task: [title]" - Add a new task
- "Mark [task] as completed" - Update task status
- "What's my highest priority task?" - Show most important task
- "Show me upcoming tasks" - Display tasks for next 7 days
- "What's today's date?" - Get current date
- "Show tasks for [date]" - Display tasks for specific date""")
        
        if any(word in input_lower for word in ["priority", "important", "urgent", "high"]):
            context_additions.append(f"""
## PRIORITY SYSTEM
- HIGH: Urgent tasks requiring immediate attention
- MEDIUM: Important tasks with moderate deadlines  
- LOW: Tasks that can be completed when time allows""")

        # Combine base prompt with dynamic context
        system_prompt = base_prompt + "".join(context_additions)
        
        # Log prompt type for debugging
        prompt_type = "basic"
        if context_additions:
            if any("TASK CONTEXT" in addition for addition in context_additions):
                prompt_type = "task-enhanced"
            if any("COMMANDS REFERENCE" in addition for addition in context_additions):
                prompt_type = "help-enhanced"
            if any("PRIORITY SYSTEM" in addition for addition in context_additions):
                prompt_type = "priority-enhanced"
        
        logger.info(f"Using {prompt_type} system prompt for user query: '{user_input[:50]}{'...' if len(user_input) > 50 else ''}'")
        
        try:
            result = await self._call_openai_api(user_input, system_prompt)
            if not result["success"]:
                return await self._handle_fallback(user_input)
            return result
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return await self._handle_fallback(user_input)

    def _get_today_schedule_response(self):
        """Get properly formatted response for today's schedule"""
        user_id = "user_001"
        today_date = datetime.now().date().isoformat()  # 2025-05-29
        
        # Get tasks specifically for today
        today_tasks = self.task_service.get_tasks_for_date(user_id, today_date)
        
        # Also get daily recurring tasks that should happen today
        daily_tasks = self.task_service.get_daily_tasks(user_id)
        
        response_parts = []
        response_parts.append(f"📅 **Today's Schedule - {datetime.now().strftime('%B %d, %Y')}**\n")
        
        if today_tasks or daily_tasks:
            if today_tasks:
                response_parts.append("🗓️ **Scheduled Tasks for Today:**")
                for task in today_tasks:
                    priority_emoji = "🔴" if task['priority'] == "high" else "🟡" if task['priority'] == "medium" else "🟢"
                    status_emoji = "✅" if task['status'] == "completed" else "🔄" if task['status'] == "in progress" else "⏳"
                    response_parts.append(f"  {status_emoji} {priority_emoji} **{task['title']}**")
                    if task.get('description'):
                        response_parts.append(f"     📝 {task['description']}")
                    response_parts.append(f"     🏷️ Priority: {task['priority'].upper()} | Status: {task['status'].title()}")
                response_parts.append("")
            
            if daily_tasks:
                response_parts.append("🔄 **Daily Recurring Tasks:**")
                for task in daily_tasks:
                    priority_emoji = "🔴" if task['priority'] == "high" else "🟡" if task['priority'] == "medium" else "🟢"
                    status_emoji = "✅" if task['status'] == "completed" else "🔄" if task['status'] == "in progress" else "⏳"
                    response_parts.append(f"  {status_emoji} {priority_emoji} **{task['title']}**")
                    response_parts.append(f"     🏷️ Priority: {task['priority'].upper()}")
                response_parts.append("")
            
            # Add summary
            total_today = len(today_tasks) + len(daily_tasks)
            response_parts.append(f"📊 **Summary:** {total_today} tasks for today")
            
        else:
            response_parts.append("✨ **No tasks scheduled for today!**")
            response_parts.append("🎉 You have a free day to focus on other priorities or take a well-deserved break!")
            
            # Show upcoming tasks as a helpful suggestion
            upcoming = self.task_service.get_upcoming_tasks(user_id, 3)
            if upcoming:
                response_parts.append("\n🔮 **Coming Up Soon:**")
                for task in upcoming[:3]:
                    priority_emoji = "🔴" if task['priority'] == "high" else "🟡" if task['priority'] == "medium" else "🟢"
                    response_parts.append(f"  {priority_emoji} {task['title']} (Due: {task['due_date']})")
        
        return {"success": True, "response": "\n".join(response_parts)}

    def _get_weekly_schedule_response(self):
        """Get organized weekly schedule response"""
        user_id = "user_001"
        from datetime import timedelta
        
        today = datetime.now().date()
        week_tasks = {}
        
        # Get tasks for the next 7 days
        for i in range(7):
            check_date = (today + timedelta(days=i)).isoformat()
            day_name = (today + timedelta(days=i)).strftime("%A")
            date_display = (today + timedelta(days=i)).strftime("%B %d")
            
            # Get specific tasks for this date
            day_tasks = self.task_service.get_tasks_for_date(user_id, check_date)
            
            # Add daily recurring tasks to each day
            if i == 0:  # Only get daily tasks once
                daily_tasks = self.task_service.get_daily_tasks(user_id)
            else:
                daily_tasks = self.task_service.get_daily_tasks(user_id)
            
            all_day_tasks = day_tasks + daily_tasks
            
            if all_day_tasks:
                week_tasks[f"{day_name}, {date_display}"] = all_day_tasks
        
        response_parts = []
        response_parts.append("📅 **Your Organized Week Ahead**\n")
        
        if week_tasks:
            for day_date, tasks in week_tasks.items():
                response_parts.append(f"📆 **{day_date}**")
                
                # Sort tasks by priority (high -> medium -> low)
                priority_order = {"high": 3, "medium": 2, "low": 1}
                sorted_tasks = sorted(tasks, key=lambda x: priority_order.get(x.get('priority', 'low'), 0), reverse=True)
                
                for task in sorted_tasks:
                    priority_emoji = "🔴" if task['priority'] == "high" else "🟡" if task['priority'] == "medium" else "🟢"
                    status_emoji = "✅" if task['status'] == "completed" else "🔄" if task['status'] == "in progress" else "⏳"
                    task_type = "🔄" if task.get('frequency') == 'daily' else "📋"
                    
                    response_parts.append(f"  {status_emoji} {priority_emoji} {task_type} **{task['title']}**")
                    if task.get('description') and task['frequency'] != 'daily':
                        response_parts.append(f"     📝 {task['description'][:60]}{'...' if len(task.get('description', '')) > 60 else ''}")
                
                response_parts.append("")
        else:
            response_parts.append("✨ **No scheduled tasks for the next 7 days!**")
            response_parts.append("🎯 This might be a good time to plan new goals or focus on long-term projects.")
        
        # Add productivity suggestions
        all_tasks = self.task_service.get_all_tasks(user_id)
        high_priority_pending = [t for t in all_tasks if t.get('priority') == 'high' and t.get('status') != 'completed']
        
        if high_priority_pending:
            response_parts.append("🚨 **High Priority Items Needing Attention:**")
            for task in high_priority_pending[:3]:
                response_parts.append(f"  🔴 **{task['title']}** (Due: {task['due_date']})")
        
        return {"success": True, "response": "\n".join(response_parts)}

    def _handle_flexible_date_query(self, input_lower: str, user_id: str):
        """Handle flexible date queries like 'next day', 'next 2 days', 'tomorrow', etc."""
        import re
        
        # Patterns for flexible date queries
        date_patterns = [
            # Today patterns
            (r'today', 'today'),
            # Tomorrow patterns
            (r'tomorrow|next day', 'tomorrow'),
            # Next X days patterns
            (r'next (\d+) days?', 'next {} days'),
            (r'next (\d+)-day', 'next {} days'),
            # This week / next week
            (r'this week', 'this week'),
            (r'next week', 'next week'),
            # Specific date patterns (DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD)
            (r'(\d{1,2})/(\d{1,2})/(\d{4})', '{}/{}/{}'),
            (r'(\d{4})-(\d{1,2})-(\d{1,2})', '{}-{}-{}'),
        ]
        
        for pattern, date_format in date_patterns:
            match = re.search(pattern, input_lower)
            if match:
                try:
                    if 'today' in pattern:
                        # Handle today - use the proper today schedule response
                        return self._get_today_schedule_response()
                    
                    elif 'next' in pattern and 'days' in pattern:
                        # Handle "next X days"
                        days = int(match.group(1))
                        date_input = f"next {days} days"
                        tasks = self.task_service.get_tasks_for_date_range(user_id, date_input)
                        
                        if tasks:
                            response = [f"📅 Your schedule for the next {days} days:"]
                            # Group tasks by date
                            tasks_by_date = {}
                            for task in tasks:
                                due_date = task.get('due_date', '')
                                if due_date not in tasks_by_date:
                                    tasks_by_date[due_date] = []
                                tasks_by_date[due_date].append(task)
                            
                            # Sort dates and display
                            for date_key in sorted(tasks_by_date.keys()):
                                response.append(f"\n📆 {date_key}:")
                                for task in tasks_by_date[date_key]:
                                    priority_emoji = "🔴" if task['priority'] == "high" else "🟡" if task['priority'] == "medium" else "🟢"
                                    status_emoji = "✅" if task['status'] == "completed" else "🔄" if task['status'] == "in progress" else "⏳"
                                    response.append(f"  {status_emoji} {priority_emoji} {task['title']}")
                                    if task.get('description'):
                                        response.append(f"    Description: {task['description']}")
                            
                            return {"success": True, "response": "\n".join(response)}
                        else:
                            return {"success": True, "response": f"📅 No tasks found for the next {days} days."}
                    
                    elif 'tomorrow' in pattern or 'next day' in pattern:
                        # Handle tomorrow/next day
                        tasks = self.task_service.get_tasks_for_flexible_date(user_id, 'tomorrow')
                        
                        if tasks:
                            response = ["📅 Your schedule for tomorrow:"]
                            for task in tasks:
                                priority_emoji = "🔴" if task['priority'] == "high" else "🟡" if task['priority'] == "medium" else "🟢"
                                status_emoji = "✅" if task['status'] == "completed" else "🔄" if task['status'] == "in progress" else "⏳"
                                response.append(f"{status_emoji} {priority_emoji} {task['title']}")
                                if task.get('description'):
                                    response.append(f"  Description: {task['description']}")
                                response.append(f"  Priority: {task['priority']} | Status: {task['status']}")
                            return {"success": True, "response": "\n".join(response)}
                        else:
                            return {"success": True, "response": "📅 No tasks found for tomorrow."}
                    
                    elif 'week' in pattern:
                        # Handle this week / next week
                        date_input = 'this week' if 'this week' in input_lower else 'next week'
                        tasks = self.task_service.get_tasks_for_date_range(user_id, date_input)
                        
                        if tasks:
                            week_name = "this week" if 'this week' in input_lower else "next week"
                            response = [f"📅 Your schedule for {week_name}:"]
                            
                            # Group tasks by date
                            tasks_by_date = {}
                            for task in tasks:
                                due_date = task.get('due_date', '')
                                if due_date not in tasks_by_date:
                                    tasks_by_date[due_date] = []
                                tasks_by_date[due_date].append(task)
                            
                            # Sort dates and display
                            for date_key in sorted(tasks_by_date.keys()):
                                response.append(f"\n📆 {date_key}:")
                                for task in tasks_by_date[date_key]:
                                    priority_emoji = "🔴" if task['priority'] == "high" else "🟡" if task['priority'] == "medium" else "🟢"
                                    status_emoji = "✅" if task['status'] == "completed" else "🔄" if task['status'] == "in progress" else "⏳"
                                    response.append(f"  {status_emoji} {priority_emoji} {task['title']}")
                            
                            return {"success": True, "response": "\n".join(response)}
                        else:
                            week_name = "this week" if 'this week' in input_lower else "next week"
                            return {"success": True, "response": f"📅 No tasks found for {week_name}."}
                    
                    elif len(match.groups()) >= 3:
                        # Handle specific date formats
                        if '/' in pattern:
                            # DD/MM/YYYY or MM/DD/YYYY format
                            part1, part2, year = match.groups()
                            date_input = f"{part1}/{part2}/{year}"
                        else:
                            # YYYY-MM-DD format
                            year, month, day = match.groups()
                            date_input = f"{year}-{month}-{day}"
                        
                        tasks = self.task_service.get_tasks_for_flexible_date(user_id, date_input)
                        
                        if tasks:
                            response = [f"📅 Tasks for {date_input}:"]
                            for task in tasks:
                                priority_emoji = "🔴" if task['priority'] == "high" else "🟡" if task['priority'] == "medium" else "🟢"
                                status_emoji = "✅" if task['status'] == "completed" else "🔄" if task['status'] == "in progress" else "⏳"
                                response.append(f"{status_emoji} {priority_emoji} {task['title']}")
                                if task.get('description'):
                                    response.append(f"  Description: {task['description']}")
                                response.append(f"  Priority: {task['priority']} | Status: {task['status']}")
                            return {"success": True, "response": "\n".join(response)}
                        else:
                            return {"success": True, "response": f"📅 No tasks found for {date_input}."}
                
                except Exception as e:
                    logger.error(f"Error handling flexible date query: {e}")
                    continue
        
        return None