#!/usr/bin/env python3
"""
Test script for flexible date parsing functionality
Tests various date formats and phrases that users might input
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.task_service import TaskService
from app.utils.date_parser import FlexibleDateParser
from datetime import date

def test_date_parsing():
    """Test the flexible date parser with various inputs"""
    parser = FlexibleDateParser()
    
    test_inputs = [
        # Relative dates
        "today",
        "tomorrow", 
        "next day",
        "yesterday",
        
        # Week-based
        "this week",
        "next week",
        "end of this week",
        
        # Month-based
        "this month",
        "next month", 
        "end of month",
        "end of this month",
        
        # Number-based relative
        "next 3 days",
        "next 7 days",
        "in 5 days",
        
        # Formatted dates
        "2025-05-30",
        "2025-06-15",
        
        # Natural language dates
        "June 1, 2025",
        "June 1 2025",
        "1st June 2025",
        "15th July 2025",
        "December 25, 2025",
        
        # Various formats
        "01/06/2025",  # DD/MM/YYYY or MM/DD/YYYY
        "06/01/2025",
        "01-06-2025",
        "15-07-2025",
        
        # Edge cases
        "",  # Empty string
        "invalid date",  # Invalid input
    ]
    
    print("🗓️  Testing Flexible Date Parser")
    print("=" * 50)
    print(f"Current date: {date.today().isoformat()}")
    print("-" * 50)
    
    for input_date in test_inputs:
        parsed = parser.parse_date(input_date)
        print(f"Input: '{input_date}' -> Parsed: {parsed}")
    
    print("\n🔍 Testing Date Range Parsing")
    print("-" * 50)
    
    range_inputs = [
        "this week",
        "next week", 
        "this month",
        "next month",
        "next 7 days",
        "next 14 days"
    ]
    
    for range_input in range_inputs:
        start, end = parser.parse_date_range(range_input)
        print(f"Range: '{range_input}' -> {start} to {end}")

def test_task_service():
    """Test the task service with flexible date inputs"""
    print("\n📋 Testing Task Service with Flexible Dates")
    print("=" * 50)
    
    task_service = TaskService()
    user_id = "test_user"
    
    # Test creating tasks with flexible dates
    test_tasks = [
        {
            "title": "Morning exercise",
            "description": "30-minute workout",
            "date_input": "tomorrow",
            "priority": "high"
        },
        {
            "title": "Weekly team meeting",
            "description": "Discuss project progress",
            "date_input": "next week",
            "priority": "medium"
        },
        {
            "title": "Monthly report",
            "description": "Submit monthly financial report",
            "date_input": "end of month",
            "priority": "high"
        },
        {
            "title": "Doctor appointment",
            "description": "Annual checkup",
            "date_input": "June 15, 2025",
            "priority": "medium"
        },
        {
            "title": "Project deadline",
            "description": "Final project submission",
            "date_input": "2025-07-01",
            "priority": "high"
        }
    ]
    
    print("Creating test tasks...")
    for task in test_tasks:
        success = task_service.create_task_with_flexible_date(
            user_id=user_id,
            title=task["title"],
            description=task["description"],
            date_input=task["date_input"],
            priority=task["priority"]
        )
        parsed_info = task_service.parse_and_validate_date(task["date_input"])
        print(f"✅ Created: '{task['title']}' for {parsed_info['parsed_date']} (from '{task['date_input']}')")
    
    # Test querying tasks
    print("\n🔍 Testing Flexible Queries")
    print("-" * 30)
    
    queries = [
        "tasks for tomorrow",
        "high priority tasks",
        "tasks this month",
        "monthly tasks"
    ]
    
    for query in queries:
        results = task_service.get_tasks_by_flexible_query(user_id, query)
        print(f"Query: '{query}' -> Found {len(results)} tasks")
        for task in results:
            print(f"  - {task['title']} (due: {task['due_date']}, priority: {task['priority']})")

def test_api_simulation():
    """Simulate API usage examples"""
    print("\n🌐 API Usage Examples")
    print("=" * 50)
    
    task_service = TaskService()
    
    examples = [
        "Get tasks for 'tomorrow': /api/tasks/date/user_001?date_input=tomorrow",
        "Get tasks for 'this week': /api/tasks/range/user_001?date_range=this week",
        "Create task for 'next Friday': POST /api/tasks/flexible/user_001 {'title': 'Meeting', 'date_input': 'next Friday'}",
        "Query 'high priority tasks this month': /api/tasks/query/user_001?query=high priority tasks this month"
    ]
    
    for example in examples:
        print(f"📡 {example}")

if __name__ == "__main__":
    print("🚀 Starting Flexible Date Parsing Tests\n")
    
    try:
        test_date_parsing()
        test_task_service()
        test_api_simulation()
        
        print("\n✅ All tests completed successfully!")
        print("\n💡 Usage Tips:")
        print("- Use natural language: 'tomorrow', 'next week', 'end of month'")
        print("- Support multiple formats: '2025-04-01', 'April 1, 2025', '1st April 2025'")
        print("- Range queries: 'this week', 'next 7 days', 'this month'")
        print("- Smart queries: 'high priority tasks this week', 'completed tasks today'")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
