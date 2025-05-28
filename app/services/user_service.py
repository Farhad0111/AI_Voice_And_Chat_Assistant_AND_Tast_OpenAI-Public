import logging
from typing import Optional, List, Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# This is a mock database for demonstration purposes
# In a real application, you would connect to an actual database
MOCK_USERS = [
    {"id": 1, "username": "John Doe", "avatar_url": "/static/user1.png", "status": "online"},
    {"id": 2, "username": "Jane Smith", "avatar_url": "/static/user2.png", "status": "online"},
    {"id": 3, "username": "Robert Johnson", "avatar_url": "/static/user3.png", "status": "away"},
    {"id": 4, "username": "Emily Davis", "avatar_url": "/static/user4.png", "status": "busy"},
    {"id": 5, "username": "Your Name", "avatar_url": "/static/user1.png", "status": "online"}
]

class UserService:
    def __init__(self):
        # In a real application, initialize your database connection here
        self.users = MOCK_USERS
    
    async def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get a user by their ID"""
        try:
            # In a real application, this would be a database query
            for user in self.users:
                if user["id"] == user_id:
                    return user
            return None
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None
      async def get_current_user(self) -> Dict[str, Any]:
        """
        Get the current logged-in user
        For demo purposes, we'll return a specific user by ID
        In a real application, this would use authentication to identify the current user
        """
        # Change the ID number below to select a different user (1-5)
        selected_user_id = 5  # Change this to any ID you want (1-5)
        
        # Find the user with the selected ID
        for user in self.users:
            if user["id"] == selected_user_id:
                return user
        
        # Fallback to the first user if the ID isn't found
        return self.users[0]
    
    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users"""
        return self.users
