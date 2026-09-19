import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.app.database import get_database
from backend.app.config import settings
from backend.app.models.user import UserRole
from backend.app.schemas.user import (
    UserCreate,
    UserLogin,
    QuickLoginRequest,
    UserResponse,
    TokenResponse,
)
from backend.app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
)
from backend.app.utils.auth import get_current_user
from backend.app.services.db_service import clean_mongo_doc
from backend.app.scripts.seed_users import seed_demo_users, DEFAULT_DEMO_USERS

logger = logging.getLogger("resqai.routes.auth")

router = APIRouter()


ROLE_METADATA = [
    {
        "role": UserRole.ADMIN.value,
        "title": "System Administrator",
        "badge_color": "border-red-500 bg-red-950/40 text-red-400",
        "description": "Full access to platform configuration, database topology, simulation engines, and user administration.",
        "default_email": "admin@resqai.org",
        "permissions": ["all", "manage_users", "system_settings", "simulate_crisis", "override_dispatch"]
    },
    {
        "role": UserRole.DISPATCHER.value,
        "title": "Emergency Operations Dispatcher",
        "badge_color": "border-cyan-500 bg-cyan-950/40 text-cyan-400",
        "description": "Call triage, AI classification reviews, 3-Signal duplicate resolution, and multi-unit resource dispatch.",
        "default_email": "dispatcher@resqai.org",
        "permissions": ["create_incident", "analyze_ai", "dispatch_fleet", "merge_duplicates", "manage_alerts"]
    },
    {
        "role": UserRole.FIELD_TEAM.value,
        "title": "Field Response Crew Commander",
        "badge_color": "border-emerald-500 bg-emerald-950/40 text-emerald-400",
        "description": "First responder on-scene telemetry, status transitions (EN_ROUTE, IN_PROGRESS), and crisis containment.",
        "default_email": "field@resqai.org",
        "permissions": ["update_status", "upload_telemetry", "request_backup", "resolve_incident"]
    },
    {
        "role": UserRole.HOSPITAL.value,
        "title": "Trauma Center ER Coordinator",
        "badge_color": "border-rose-500 bg-rose-950/40 text-rose-400",
        "description": "Inbound ambulance triage, emergency bed capacity updates, and mass casualty preparation.",
        "default_email": "hospital@resqai.org",
        "permissions": ["view_inbound_trauma", "update_bed_capacity", "triage_patients"]
    },
    {
        "role": UserRole.VIEWER.value,
        "title": "Public Observer / Auditor",
        "badge_color": "border-slate-500 bg-slate-900/60 text-slate-300",
        "description": "Read-only access to metropolitan incident cartography, executive analytics, and SLA reports.",
        "default_email": "viewer@resqai.org",
        "permissions": ["view_map", "view_analytics", "view_overview"]
    }
]


@router.post("/login", response_model=TokenResponse, summary="User Login (JWT Authentication)")
async def login(
    payload: UserLogin,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Authenticate with email and password. Returns JWT bearer access token and user profile.
    """
    email = payload.email.lower().strip()
    user = await db.users.find_one({"email": email})

    # If no users exist in database, auto-seed demo users
    if not user:
        user_count = await db.users.count_documents({})
        if user_count == 0:
            await seed_demo_users(db)
            user = await db.users.find_one({"email": email})

    if not user or not verify_password(payload.password, user.get("hashed_password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deactivated"
        )

    now = datetime.now(timezone.utc)
    await db.users.update_one({"_id": user["_id"]}, {"$set": {"last_login": now}})

    cleaned_user = clean_mongo_doc(user)
    token_payload = {
        "sub": cleaned_user.get("user_id", str(cleaned_user.get("id"))),
        "email": cleaned_user.get("email"),
        "role": cleaned_user.get("role", UserRole.DISPATCHER.value),
        "name": cleaned_user.get("full_name")
    }

    token = create_access_token(token_payload)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in_minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
        user=UserResponse(
            id=str(cleaned_user.get("id")),
            user_id=cleaned_user.get("user_id"),
            email=cleaned_user.get("email"),
            full_name=cleaned_user.get("full_name"),
            role=cleaned_user.get("role"),
            department=cleaned_user.get("department"),
            phone=cleaned_user.get("phone"),
            is_active=cleaned_user.get("is_active", True),
            created_at=cleaned_user.get("created_at"),
            last_login=now
        )
    )


@router.post("/quick-login", response_model=TokenResponse, summary="1-Click Quick Demo Login by Role")
async def quick_demo_login(
    payload: QuickLoginRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Instant 1-click authentication for hackathon evaluation and role switching.
    """
    target_role = payload.role.value if hasattr(payload.role, "value") else str(payload.role)
    user = await db.users.find_one({"role": target_role})

    if not user:
        await seed_demo_users(db)
        user = await db.users.find_one({"role": target_role})

    if not user:
        # Create user on the fly
        now = datetime.now(timezone.utc)
        user_id = f"USR-{target_role[:4]}-{uuid.uuid4().hex[:4].upper()}"
        doc = {
            "user_id": user_id,
            "email": f"{target_role.lower()}@resqai.org",
            "full_name": f"Command {target_role.capitalize()} Operator",
            "role": target_role,
            "department": f"{target_role.capitalize()} Operations",
            "hashed_password": hash_password(settings.DEMO_DEFAULT_PASSWORD),
            "is_active": True,
            "created_at": now,
            "last_login": now
        }
        res = await db.users.insert_one(doc)
        doc["_id"] = res.inserted_id
        user = doc

    now = datetime.now(timezone.utc)
    await db.users.update_one({"_id": user["_id"]}, {"$set": {"last_login": now}})

    cleaned_user = clean_mongo_doc(user)
    token_payload = {
        "sub": cleaned_user.get("user_id", str(cleaned_user.get("id"))),
        "email": cleaned_user.get("email"),
        "role": cleaned_user.get("role", target_role),
        "name": cleaned_user.get("full_name")
    }

    token = create_access_token(token_payload)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in_minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
        user=UserResponse(
            id=str(cleaned_user.get("id")),
            user_id=cleaned_user.get("user_id"),
            email=cleaned_user.get("email"),
            full_name=cleaned_user.get("full_name"),
            role=cleaned_user.get("role"),
            department=cleaned_user.get("department"),
            phone=cleaned_user.get("phone"),
            is_active=cleaned_user.get("is_active", True),
            created_at=cleaned_user.get("created_at"),
            last_login=now
        )
    )


@router.post("/register", response_model=UserResponse, summary="Register New User")
async def register_user(
    payload: UserCreate,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Register a new operator or staff member. Passwords are securely hashed before MongoDB insertion.
    """
    email = payload.email.lower().strip()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists"
        )

    now = datetime.now(timezone.utc)
    user_id = f"USR-{payload.role.value[:4]}-{uuid.uuid4().hex[:4].upper()}"

    doc = {
        "user_id": user_id,
        "email": email,
        "full_name": payload.full_name,
        "role": payload.role.value,
        "department": payload.department or "Emergency Response Unit",
        "phone": payload.phone,
        "hashed_password": hash_password(payload.password),
        "is_active": True,
        "created_at": now,
        "last_login": None
    }

    res = await db.users.insert_one(doc)
    doc["_id"] = str(res.inserted_id)

    return UserResponse(
        id=doc["_id"],
        user_id=user_id,
        email=doc["email"],
        full_name=doc["full_name"],
        role=doc["role"],
        department=doc["department"],
        phone=doc["phone"],
        is_active=True,
        created_at=now,
        last_login=None
    )


@router.get("/me", response_model=UserResponse, summary="Get Current Authenticated User")
async def get_me(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Return profile and role permissions for currently logged-in user.
    """
    return UserResponse(
        id=str(current_user.get("id")),
        user_id=current_user.get("user_id"),
        email=current_user.get("email"),
        full_name=current_user.get("full_name"),
        role=current_user.get("role"),
        department=current_user.get("department"),
        phone=current_user.get("phone"),
        is_active=current_user.get("is_active", True),
        created_at=current_user.get("created_at"),
        last_login=current_user.get("last_login")
    )


@router.post("/seed", summary="Seed / Reset Demo User Accounts")
async def trigger_seed_users(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Seed all 5 demo accounts (ADMIN, DISPATCHER, FIELD_TEAM, HOSPITAL, VIEWER) into MongoDB.
    """
    count = await seed_demo_users(db)
    return {
        "status": "users_seeded",
        "accounts_count": count,
        "demo_accounts": [
            {"role": u["role"], "email": u["email"], "name": u["full_name"]}
            for u in DEFAULT_DEMO_USERS
        ]
    }


@router.get("/roles", summary="Get Roles & Capability Matrix")
async def get_roles():
    """
    Returns information on all available user roles and their security permissions.
    """
    return {
        "roles": ROLE_METADATA
    }
