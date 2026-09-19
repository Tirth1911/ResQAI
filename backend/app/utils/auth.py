import logging
from typing import Optional, List, Dict, Any
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.app.database import get_database
from backend.app.models.user import UserRole
from backend.app.utils.security import decode_access_token
from backend.app.services.db_service import clean_mongo_doc

logger = logging.getLogger("resqai.auth")

security_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    authorization: Optional[str] = Header(None),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Dict[str, Any]:
    """
    Extract current authenticated user from Bearer token in Authorization header.
    """
    token = None
    if credentials:
        token = credentials.credentials
    elif authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload["sub"]
    user = await db.users.find_one({"user_id": user_id})
    if not user:
        # Fallback query by email
        user = await db.users.find_one({"email": payload.get("email")})

    if not user or not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return clean_mongo_doc(user)


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    authorization: Optional[str] = Header(None),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Optional[Dict[str, Any]]:
    """
    Optional user extractor for semi-public dashboard views.
    """
    try:
        return await get_current_user(credentials, authorization, db)
    except HTTPException:
        return None


def require_roles(allowed_roles: List[UserRole]):
    """
    FastAPI dependency factory enforcing role-based access control (RBAC).
    """
    async def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role_str = str(current_user.get("role", "")).upper()
        allowed_strs = [r.value.upper() for r in allowed_roles]

        # ADMIN always has full access
        if user_role_str == UserRole.ADMIN.value.upper():
            return current_user

        if user_role_str not in allowed_strs:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. User role '{user_role_str}' lacks required permissions ({', '.join(allowed_strs)})"
            )
        return current_user

    return role_checker
