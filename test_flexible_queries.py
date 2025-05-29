#!/usr/bin/env python3
"""
Test script for flexible date queries in AI service
Tests the enhanced date parsing functionality
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ai_service import AIService

async def test_flexible_date_queries():
    """Test flexible date queries that were failing"""
    ai_service = AIService()
    
    test_queries = [
        # The queries that were failing
        "show my next 2 day schedule?",
        "show my next day schedule?", 
        "show my tomorrow schedule?",
        
        # Additional flexible date queries
        "what's my schedule for tomorrow?",
        "show me my next 3 days",
        "what tasks do I have this week?",
        "show my next week schedule",
        
        # Specific date formats
        "show my 30/05/2025 schedule",
        "what's my schedule for 2025-05-30?",
        
        # Current working queries for comparison
        "show my today schedule?",
        "show my 05/31/2025 schedule?",
    ]
    
    print("🧪 Testing Flexible Date Queries")
    print("=" * 60)
    print(f"Current date: May 29, 2025 (for reference)")
    print("-" * 60)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: '{query}'")
        print("-" * 40)
        
        try:
            response = await ai_service.generate_response(query)
            
            if response.get("success"):
                print(f"✅ Response: {response['response']}")
            else:
                print(f"❌ Failed: {response.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"💥 Exception: {str(e)}")
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")

if __name__ == "__main__":
    print("🚀 Starting Flexible Date Query Tests\n")
    asyncio.run(test_flexible_date_queries())
