from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from backend.app.models.user import UserRole


class UserBase(BaseModel):
    email: str
    full_name: str
    role: UserRole = UserRole.DISPATCHER
    department: Optional[str] = None
    phone: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=4, description="Raw password to be hashed")


class UserLogin(BaseModel):
    email: str
    password: str


class QuickLoginRequest(BaseModel):
    role: UserRole = Field(..., description="Role to login instantly for hackathon demo evaluation")


class UserResponse(UserBase):
    id: Optional[str] = None
    user_id: str
    is_active: bool = True
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: UserResponse


class TokenPayload(BaseModel):
    sub: str  # user_id
    email: str
    role: UserRole
    exp: Optional[int] = None
