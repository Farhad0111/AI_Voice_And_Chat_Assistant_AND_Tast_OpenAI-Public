from pydantic import BaseModel
from typing import Optional

class UserModel(BaseModel):
    """User model for authentication and user management"""
    name: str
    user_id: str
    photo_url: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "name": "John Doe",
                "user_id": "jdoe123",
                "photo_url": None
            }
        }