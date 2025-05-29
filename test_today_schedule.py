#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ai_service import AIService

async def test_today_schedule():
    print("Testing today's schedule response...")
    
    ai_service = AIService()
    
    # Test different variations of the today schedule request
    test_queries = [
        "show my today schedule",
        "show me my schedule today",
        "what's my schedule for today",
        "today schedule",
        "my tasks today"
    ]
    
    for query in test_queries:
        print(f"\n{'='*50}")
        print(f"Query: '{query}'")
        print(f"{'='*50}")
        
        try:
            response = await ai_service.generate_response(query)
            print(f"Success: {response.get('success', False)}")
            print(f"Response: {response.get('response', 'No response')}")
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_today_schedule())
