from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from app.models import ChatRequest
from app.services.ai_service import AIService
from app.services.task_service import TaskService
from datetime import datetime, date
import logging
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
ai_service = AIService()
task_service = TaskService()

@router.post("/chat")
async def chat(request: ChatRequest):
    """Process chat requests and return AI responses"""
    logger.info(f"Received chat request with message: {request.message}")
    
    if not request.message:
        logger.warning("Empty message received")
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    try:
        # Using user_001 as that's the ID in our tasks.json
        user_id = "user_001"
        message_lower = request.message.lower()

        # First try the AI service for any query
        result = await ai_service.generate_response(request.message)
        if result["success"]:
            return result
            
        # If AI service fails, handle basic queries directly
        if any(word in message_lower for word in ["task", "schedule", "meeting", "todo", "to-do", "to do"]):
            # Handle task listing queries
            if any(word in message_lower for word in ["show", "list", "what", "display"]):
                if "today" in message_lower:
                    tasks = task_service.get_today_tasks(user_id)
                    if tasks:
                        tasks_text = "\n".join([f"• {task['title']} (Priority: {task['priority']})" for task in tasks])
                        return {
                            "success": True,
                            "response": f"Here are your tasks for today:\n{tasks_text}"
                        }
                    return {
                        "success": True,
                        "response": "You don't have any tasks scheduled for today."
                    }
                elif "upcoming" in message_lower or "next" in message_lower:
                    tasks = task_service.get_upcoming_tasks(user_id)
                    if tasks:
                        tasks_text = "\n".join([f"• {task['title']} (Due: {task['due_date']})" for task in tasks])
                        return {
                            "success": True,
                            "response": f"Here are your upcoming tasks:\n{tasks_text}"
                        }
                    return {
                        "success": True,
                        "response": "You don't have any upcoming tasks scheduled."
                    }
                elif "priority" in message_lower or "important" in message_lower:
                    task = task_service.get_highest_priority_task(user_id)
                    if task:
                        return {
                            "success": True,
                            "response": f"Your highest priority task is: {task['title']} (Due: {task['due_date']})"
                        }
                    return {
                        "success": True,
                        "response": "You don't have any priority tasks at the moment."
                    }
            
            # Handle task creation
            elif any(word in message_lower for word in ["create", "add", "new"]):
                # Pass to AI service to extract task details
                result = await ai_service.generate_response(request.message)
                if result["success"]:
                    return result
                return {
                    "success": True,
                    "response": "I can help you create a new task. Please provide the task title and any other details like due date and priority."
                }

        # For general queries about date/time
        elif "date" in message_lower or "time" in message_lower or "today" in message_lower:
            formatted_date = datetime.now().strftime("%B %d, %Y")
            return {
                "success": True,
                "response": f"Today's date is {formatted_date}."
            }

        # For general chat
        result = await ai_service.generate_response(request.message)
        
        if result["success"]:
            logger.info("Successfully generated response from OpenAI API")
            return result
        else:
            logger.error(f"AI service error: {result.get('error', 'Unknown error')}")
            return {
                "success": True,
                "response": "I apologize, but I'm having trouble processing your request right now. Could you try again?"
            }
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return {
            "success": True,
            "response": "I apologize for the inconvenience. I'm experiencing a technical issue. Please try again in a moment."
        }

@router.get("/models")
async def get_models():
    """Get information about the AI model being used"""
    return {
        "success": True,
        "models": ["gpt-3.5-turbo"],
        "current_model": ai_service.last_model_used,
        "status": "online" if ai_service.openai_api_key else "offline"
    }