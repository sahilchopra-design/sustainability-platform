"""
Authentication routes — Google OAuth (Emergent) + JWT email/password fallback.
"""

from fastapi import APIRouter, HTTPException, Response, Request, Depends
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone, timedelta
import uuid
import httpx
from passlib.context import CryptContext
from jose import jwt

from database import get_database

router = APIRouter(prefix="/api/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
JWT_SECRET = "climate-risk-platform-jwt-secret-2026"
JWT_ALGORITHM = "HS256"
SESSION_DAYS = 7

EMERGENT_AUTH_URL = "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data"


# ---- Helpers ----

async def _get_db():
    return get_database()


async def _get_or_create_user(db, email: str, name: str, picture: str = "") -> dict:
    existing = await db.users.find_one({"email": email}, {"_id": 0})
    if existing:
        await db.users.update_one({"email": email}, {"$set": {"name": name, "picture": picture}})
        existing["name"] = name
        existing["picture"] = picture
        return existing
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    user = {
        "user_id": user_id,
        "email": email,
        "name": name,
        "picture": picture,
        "created_at": datetime.now(timezone.utc),
    }
    await db.users.insert_one(user)
    return {k: v for k, v in user.items() if k != "_id"}


async def _create_session(db, user_id: str) -> str:
    session_token = f"sess_{uuid.uuid4().hex}"
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS),
        "created_at": datetime.now(timezone.utc),
    })
    return session_token


async def _validate_session(db, token: str) -> Optional[dict]:
    if not token:
        return None
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session:
        return None
    expires_at = session.get("expires_at")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        return None
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    return user


def _set_cookie(response: Response, token: str):
    response.set_cookie(
        key="session_token", value=token,
        httponly=True, secure=True, samesite="none",
        path="/", max_age=SESSION_DAYS * 86400,
    )


def _get_token_from_request(request: Request) -> Optional[str]:
    """Extract session token from cookie or Authorization header."""
    token = request.cookies.get("session_token")
    if token:
        return token
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return None


# ---- Schemas ----

class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)
    name: str = Field(..., min_length=1)


class LoginRequest(BaseModel):
    email: str
    password: str


class GoogleSessionRequest(BaseModel):
    session_id: str


# ---- Routes ----

@router.post("/google/session")
async def exchange_google_session(body: GoogleSessionRequest, response: Response):
    """Exchange Emergent Google session_id for a local session."""
    # REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    async with httpx.AsyncClient() as client:
        r = await client.get(EMERGENT_AUTH_URL, headers={"X-Session-ID": body.session_id})
        if r.status_code != 200:
            raise HTTPException(401, "Invalid Google session")
        data = r.json()

    db = await _get_db()
    user = await _get_or_create_user(db, data["email"], data["name"], data.get("picture", ""))
    session_token = await _create_session(db, user["user_id"])
    _set_cookie(response, session_token)

    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "name": user["name"],
        "picture": user.get("picture", ""),
        "session_token": session_token,
    }


@router.post("/register")
async def register(body: RegisterRequest, response: Response):
    """Register with email/password (JWT fallback)."""
    db = await _get_db()
    existing = await db.users.find_one({"email": body.email}, {"_id": 0})
    if existing:
        raise HTTPException(400, "Email already registered")

    user_id = f"user_{uuid.uuid4().hex[:12]}"
    hashed = pwd_context.hash(body.password)
    user = {
        "user_id": user_id,
        "email": body.email,
        "name": body.name,
        "password_hash": hashed,
        "picture": "",
        "created_at": datetime.now(timezone.utc),
    }
    await db.users.insert_one(user)
    session_token = await _create_session(db, user_id)
    _set_cookie(response, session_token)

    return {
        "user_id": user_id,
        "email": body.email,
        "name": body.name,
        "session_token": session_token,
    }


@router.post("/login")
async def login(body: LoginRequest, response: Response):
    """Login with email/password."""
    db = await _get_db()
    user = await db.users.find_one({"email": body.email}, {"_id": 0})
    if not user or not user.get("password_hash"):
        raise HTTPException(401, "Invalid credentials")
    if not pwd_context.verify(body.password, user["password_hash"]):
        raise HTTPException(401, "Invalid credentials")

    session_token = await _create_session(db, user["user_id"])
    _set_cookie(response, session_token)

    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "name": user["name"],
        "session_token": session_token,
    }


@router.get("/me")
async def get_current_user(request: Request):
    """Get current authenticated user from session token."""
    token = _get_token_from_request(request)
    if not token:
        raise HTTPException(401, "Not authenticated")
    db = await _get_db()
    user = await _validate_session(db, token)
    if not user:
        raise HTTPException(401, "Invalid or expired session")

    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "name": user["name"],
        "picture": user.get("picture", ""),
    }


@router.post("/logout")
async def logout(request: Request, response: Response):
    """Logout — clear session."""
    token = _get_token_from_request(request)
    if token:
        db = await _get_db()
        await db.user_sessions.delete_one({"session_token": token})
    response.delete_cookie("session_token", path="/")
    return {"message": "Logged out"}
