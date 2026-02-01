from pydantic import BaseModel
from typing import Optional


class UserBase(BaseModel):
    username: str
    email: str
    roles: str = "user"


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool = True
    created_at: Optional[str] = None
    last_login: Optional[str] = None

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """Response schema for user data"""
    id: int
    username: str
    email: str
    roles: str = "user"
    is_active: bool = True
    created_at: Optional[str] = None
    last_login: Optional[str] = None

    class Config:
        from_attributes = True
