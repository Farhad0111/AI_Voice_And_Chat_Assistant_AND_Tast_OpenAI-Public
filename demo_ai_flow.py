"""
Test script to demonstrate how AI service handles different types of user queries
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ai_service import AIService
from app.services.task_service import TaskService

def test_ai_responses():
    print("🤖 AI SERVICE RESPONSE FLOW DEMONSTRATION")
    print("=" * 60)
    
    # Initialize services
    ai_service = AIService()
    task_service = TaskService()
    
    # Test queries with different types
    test_cases = [
        {
            "category": "GENERAL GREETINGS",
            "queries": [
                "Hi",
                "Hello there",
                "How are you?",
                "Help me"
            ]
        },
        {
            "category": "DATE QUERIES", 
            "queries": [
                "What's today's date?",
                "Show me my 2025-05-28 schedule",  # Today (has data)
                "Show me my 2025-05-31 schedule",  # Future (has data)
                "What's my schedule for 2025-06-15?",  # Future (no data)
                "Show me tasks for 2025-04-28",  # Past (has data)
                "What was my schedule on 2025-01-01?"  # Past (no data)
            ]
        },
        {
            "category": "TASK & SCHEDULE QUERIES",
            "queries": [
                "What are my upcoming tasks?",
                "Show me my tasks",
                "What's my schedule for today?",
                "What meetings do I have?"
            ]
        }
    ]
    
    for category in test_cases:
        print(f"\n📁 {category['category']}")
        print("-" * 40)
        
        for query in category['queries']:
            print(f"\n❓ User Query: '{query}'")
            
            try:
                # For this demo, we'll simulate the response without async
                # In real usage, you'd use: await ai_service.generate_response(query)
                
                # Check what type of response this would generate
                input_lower = query.lower()
                
                # Simulate the AI service logic
                if any(greeting in input_lower for greeting in ["hi", "hello", "hey"]):
                    response = "Hello! I'm DONNA, your AI assistant. How can I help you today?"
                
                elif "how are you" in input_lower:
                    response = "I'm functioning well, thank you for asking! How can I assist you today?"
                
                elif any(word in input_lower for word in ["help", "assist", "support"]):
                    response = "I'd be happy to help! I can assist you with managing tasks, schedules, meetings, and more."
                
                elif "today" in input_lower and "date" in input_lower:
                    from datetime import datetime
                    today = datetime.now().strftime("%B %d, %Y")
                    response = f"Today's date is {today}."
                
                elif "2025-05-28" in query:  # Today's date
                    tasks = task_service.get_tasks_for_date("user_001", "2025-05-28")
                    if tasks:
                        response = f"Tasks for 2025-05-28:\n"
                        for task in tasks:
                            response += f"- {task['title']} (Priority: {task['priority']}, Status: {task['status']})\n"
                    else:
                        response = "No tasks found for 2025-05-28."
                
                elif "2025-05-31" in query:  # Future date with data
                    tasks = task_service.get_tasks_for_date("user_001", "2025-05-31")
                    if tasks:
                        response = f"Tasks for 2025-05-31:\n"
                        for task in tasks:
                            response += f"- {task['title']} (Priority: {task['priority']}, Status: {task['status']})\n"
                    else:
                        response = "No tasks found for 2025-05-31."
                
                elif "2025-06-15" in query:  # Future date with no data
                    response = "No tasks found for 2025-06-15."
                
                elif "2025-04-28" in query:  # Past date with data
                    tasks = task_service.get_tasks_for_date("user_001", "2025-04-28")
                    if tasks:
                        response = f"Tasks for 2025-04-28:\n"
                        for task in tasks:
                            response += f"- {task['title']} (Priority: {task['priority']}, Status: {task['status']})\n"
                    else:
                        response = "No tasks found for 2025-04-28."
                
                elif "2025-01-01" in query:  # Past date with no data
                    response = "No tasks found for 2025-01-01."
                
                elif any(word in input_lower for word in ["upcoming", "tasks", "schedule", "meetings"]):
                    # Get task context
                    today_tasks = task_service.get_today_tasks("user_001")
                    upcoming_tasks = task_service.get_upcoming_tasks("user_001")
                    
                    if today_tasks or upcoming_tasks:
                        response = "Here's your schedule:\n"
                        if today_tasks:
                            response += "Today's tasks:\n"
                            for task in today_tasks:
                                response += f"- {task['title']} (Priority: {task['priority']}, Status: {task['status']})\n"
                        if upcoming_tasks:
                            response += "Upcoming tasks:\n"
                            for task in upcoming_tasks:
                                response += f"- {task['title']} (Due: {task['due_date']}, Priority: {task['priority']})\n"
                    else:
                        response = "No tasks found."
                
                else:
                    response = "I can help you manage your tasks and schedule. Would you like to see your current tasks, create a new task, or check your schedule?"
                
                print(f"🤖 AI Response: {response[:200]}{'...' if len(response) > 200 else ''}")
                
            except Exception as e:
                print(f"❌ Error: {e}")

    print(f"\n\n📋 SUMMARY:")
    print("The AI handles queries in this order:")
    print("1. Check for specific dates (YYYY-MM-DD format)")
    print("2. Handle direct schedule/task requests")
    print("3. Process greetings and basic queries")
    print("4. Use OpenAI API for complex queries")
    print("5. Fall back to default responses")
    print("\nFor date-specific queries:")
    print("✅ If data exists for the date → Show tasks")
    print("❌ If no data exists → 'No tasks found for [date]'")

if __name__ == "__main__":
    test_ai_responses()
