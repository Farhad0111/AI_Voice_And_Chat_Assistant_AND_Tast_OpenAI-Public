import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ai_service import AIService
from app.services.task_service import TaskService

async def test_date_queries():
    print("Testing Date-Specific Queries")
    print("=" * 50)
    
    ai_service = AIService()
    task_service = TaskService()
    
    # Test different date queries
    test_queries = [
        "What are my upcoming tasks?",
        "Show me my 2025-05-28 schedule",  # Today (should have data)
        "Show me my 2025-05-23 schedule",  # Past date (should have no data)
        "What's my schedule for 2025-05-31?",  # Future date (should have data)
        "Show me tasks for 2025-06-15",  # Far future (should have no data)
        "What was my schedule on 2025-04-28?",  # Past date (should have data)
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        print("-" * 40)
        
        try:
            response = await ai_service.generate_response(query)
            print(f"✅ Response: {response['response'][:200]}...")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()

if __name__ == "__main__":
    asyncio.run(test_date_queries())
