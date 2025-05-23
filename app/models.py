# app/models.py
from pydantic import BaseModel

class UserProfile(BaseModel):
    name: str
    email: str
    profile_picture: str = None