"""
Auth routes — PostgreSQL-backed (replaces MongoDB auth).
"""

from fastapi import APIRouter, HTTPException, Response, Request
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone, timedelta
import uuid
import httpx
import bcrypt as _bcrypt
from sqlalchemy.orm import Session
from fastapi import Depends

from db.base import get_db
from db.models.portfolio_pg import UserPG, UserSessionPG

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _hash_pw(password: str) -> str:
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()


def _verify_pw(password: str, hashed: str) -> bool:
    try:
        return _bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False
SESSION_DAYS = 7
EMERGENT_AUTH_URL = "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data"


def _get_token(request: Request) -> Optional[str]:
    token = request.cookies.get("session_token")
    if token:
        return token
    auth = request.headers.get("Authorization", "")
    return auth[7:] if auth.startswith("Bearer ") else None


def _set_cookie(response: Response, token: str):
    response.set_cookie(key="session_token", value=token, httponly=True,
                        secure=True, samesite="none", path="/", max_age=SESSION_DAYS * 86400)


def _create_session(db: Session, user_id: str) -> str:
    token = f"sess_{uuid.uuid4().hex}"
    db.add(UserSessionPG(
        user_id=user_id, session_token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS),
    ))
    db.commit()
    return token


def _validate_session(db: Session, token: str):
    if not token:
        return None
    sess = db.query(UserSessionPG).filter(UserSessionPG.session_token == token).first()
    if not sess:
        return None
    if sess.expires_at.tzinfo is None:
        from datetime import timezone as tz
        expires = sess.expires_at.replace(tzinfo=tz.utc)
    else:
        expires = sess.expires_at
    if expires < datetime.now(timezone.utc):
        return None
    user = db.get(UserPG, sess.user_id)
    # Block deactivated users
    if user and not getattr(user, "is_active", True):
        return None
    return user


def _update_last_login(db: Session, user: UserPG):
    """Best-effort update of last_login timestamp."""
    try:
        user.last_login = datetime.now(timezone.utc)
        db.commit()
    except Exception:
        db.rollback()


class RegisterReq(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)
    name: str = Field(..., min_length=1)


class LoginReq(BaseModel):
    email: str
    password: str


class GoogleSessionReq(BaseModel):
    session_id: str


@router.post("/google/session")
async def exchange_google(body: GoogleSessionReq, response: Response, db: Session = Depends(get_db)):
    # REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    async with httpx.AsyncClient() as client:
        r = await client.get(EMERGENT_AUTH_URL, headers={"X-Session-ID": body.session_id})
        if r.status_code != 200:
            raise HTTPException(401, "Invalid Google session")
        data = r.json()

    user = db.query(UserPG).filter(UserPG.email == data["email"]).first()
    if user:
        user.name = data["name"]
        user.picture = data.get("picture", "")
        if not getattr(user, "is_active", True):
            raise HTTPException(403, "Account deactivated")
    else:
        user = UserPG(user_id=f"user_{uuid.uuid4().hex[:12]}", email=data["email"],
                      name=data["name"], picture=data.get("picture", ""))
        db.add(user)
    db.commit()

    _update_last_login(db, user)
    token = _create_session(db, user.user_id)
    _set_cookie(response, token)
    return {
        "user_id": user.user_id, "email": user.email, "name": user.name,
        "picture": user.picture or "",
        "role": getattr(user, "role", "viewer"),
        "org_id": str(getattr(user, "org_id", None) or ""),
        "session_token": token,
    }


@router.post("/register")
def register(body: RegisterReq, response: Response, db: Session = Depends(get_db)):
    if db.query(UserPG).filter(UserPG.email == body.email).first():
        raise HTTPException(400, "Email already registered")

    user = UserPG(user_id=f"user_{uuid.uuid4().hex[:12]}", email=body.email,
                  name=body.name, password_hash=_hash_pw(body.password))
    db.add(user)
    db.commit()

    _update_last_login(db, user)
    token = _create_session(db, user.user_id)
    _set_cookie(response, token)
    return {
        "user_id": user.user_id, "email": body.email, "name": body.name,
        "role": "viewer", "org_id": "", "session_token": token,
    }


@router.post("/login")
def login(body: LoginReq, response: Response, db: Session = Depends(get_db)):
    user = db.query(UserPG).filter(UserPG.email == body.email).first()
    if not user or not user.password_hash:
        raise HTTPException(401, "Invalid credentials")
    if not _verify_pw(body.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    if not getattr(user, "is_active", True):
        raise HTTPException(403, "Account deactivated")

    _update_last_login(db, user)
    token = _create_session(db, user.user_id)
    _set_cookie(response, token)
    return {
        "user_id": user.user_id, "email": user.email, "name": user.name,
        "role": getattr(user, "role", "viewer"),
        "org_id": str(getattr(user, "org_id", None) or ""),
        "session_token": token,
    }


@router.get("/me")
def get_me(request: Request, db: Session = Depends(get_db)):
    token = _get_token(request)
    if not token:
        raise HTTPException(401, "Not authenticated")
    user = _validate_session(db, token)
    if not user:
        raise HTTPException(401, "Invalid or expired session")

    # Resolve org name if user belongs to an organisation
    org_name = None
    org_id = getattr(user, "org_id", None)
    if org_id:
        try:
            from db.models.portfolio_pg import OrganisationPG
            org = db.get(OrganisationPG, org_id)
            org_name = org.name if org else None
        except Exception:
            pass

    return {
        "user_id": user.user_id,
        "email": user.email,
        "name": user.name,
        "picture": user.picture or "",
        "role": getattr(user, "role", "viewer"),
        "org_id": str(org_id) if org_id else None,
        "org_name": org_name,
        "is_active": getattr(user, "is_active", True),
    }


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = _get_token(request)
    if token:
        db.query(UserSessionPG).filter(UserSessionPG.session_token == token).delete()
        db.commit()
    response.delete_cookie("session_token", path="/")
    return {"message": "Logged out"}
