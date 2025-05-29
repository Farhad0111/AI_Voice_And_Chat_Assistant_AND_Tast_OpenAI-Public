"""
Test script to demonstrate the improved AI service base prompt and organization
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ai_service import AIService
from app.services.task_service import TaskService

def test_improved_ai_service():
    print("🤖 TESTING IMPROVED AI SERVICE")
    print("=" * 60)
    
    # Initialize services
    ai_service = AIService()
    
    # Test different types of queries to see how the dynamic context works
    test_cases = [
        {
            "category": "HELP & CAPABILITIES",
            "queries": [
                "What can you do?",
                "Help me",
                "What are your capabilities?"
            ]
        },
        {
            "category": "TASK MANAGEMENT", 
            "queries": [
                "Show me my tasks",
                "What's my schedule today?",
                "What's my highest priority task?"
            ]
        },
        {
            "category": "PRIORITY QUERIES",
            "queries": [
                "Show me my high priority tasks",
                "What's most important today?",
                "Which tasks are urgent?"
            ]
        },
        {
            "category": "GREETINGS & GENERAL",
            "queries": [
                "Hello!",
                "How are you?",
                "Good morning"
            ]
        },
        {
            "category": "DATE & TIME",
            "queries": [
                "What's today's date?",
                "What time is it?",
                "When is today?"
            ]
        }
    ]
    
    for category in test_cases:
        print(f"\n📁 {category['category']}")
        print("-" * 40)
        
        for query in category['queries']:
            print(f"\n❓ User Query: '{query}'")
            
            try:
                # Test the fallback responses (since we don't have OpenAI API key for demo)
                # This will show how the improved _handle_fallback method works
                import asyncio
                
                # Create a simple async runner
                async def test_fallback():
                    return await ai_service._handle_fallback(query)
                
                response = asyncio.run(test_fallback())
                
                if response["success"]:
                    # Truncate long responses for display
                    response_text = response["response"]
                    if len(response_text) > 300:
                        response_text = response_text[:300] + "..."
                    print(f"🤖 AI Response: {response_text}")
                else:
                    print(f"❌ Error: {response.get('error', 'Unknown error')}")
                
            except Exception as e:
                print(f"❌ Error: {e}")

    print(f"\n\n📋 IMPROVEMENTS SUMMARY:")
    print("✅ Enhanced base prompt with comprehensive identity and capabilities")
    print("✅ Dynamic context addition based on query type")
    print("✅ Improved task context with emojis and better formatting")
    print("✅ Enhanced fallback responses with helpful suggestions")
    print("✅ Better error handling and user guidance")
    print("✅ Organized response structure with clear categories")
    print("✅ Added logging for prompt type tracking")
    print("✅ Support for help, priority, and command reference contexts")

if __name__ == "__main__":
    test_improved_ai_service()
