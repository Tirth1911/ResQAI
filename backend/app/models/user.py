from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    DISPATCHER = "DISPATCHER"
    FIELD_TEAM = "FIELD_TEAM"
    HOSPITAL = "HOSPITAL"
    VIEWER = "VIEWER"


class UserDoc(BaseModel):
    user_id: str
    email: str
    full_name: str
    hashed_password: str
    role: UserRole = UserRole.DISPATCHER
    department: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None


# Alias for backward compatibility
UserModel = UserDoc

