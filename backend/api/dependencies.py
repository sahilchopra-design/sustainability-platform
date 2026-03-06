"""
Auth dependencies for FastAPI route injection.

Usage in routes:
    from api.dependencies import get_current_user, require_role

    @router.get("/protected")
    def protected_endpoint(
        user: UserPG = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        ...

    @router.delete("/admin-only")
    def admin_endpoint(
        user: UserPG = Depends(require_role("admin", "portfolio_manager")),
        db: Session = Depends(get_db),
    ):
        ...
"""

from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
from typing import Optional, Sequence

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from db.base import get_db
from db.models.portfolio_pg import UserPG, UserSessionPG


# ── Token extraction ─────────────────────────────────────────────────────────

def _extract_token(request: Request) -> Optional[str]:
    """Pull session token from cookie or Authorization header."""
    token = request.cookies.get("session_token")
    if token:
        return token
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return None


# ── Session → User resolution ────────────────────────────────────────────────

def _resolve_user(db: Session, token: str) -> Optional[UserPG]:
    """Validate session token and return the associated user (or None)."""
    if not token:
        return None
    sess = (
        db.query(UserSessionPG)
        .filter(UserSessionPG.session_token == token)
        .first()
    )
    if not sess:
        return None
    # Timezone-aware expiry comparison
    expires = sess.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < datetime.now(timezone.utc):
        return None
    user = db.get(UserPG, sess.user_id)
    if user and not getattr(user, "is_active", True):
        return None  # deactivated user
    return user


# ── Public dependencies ──────────────────────────────────────────────────────

def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> UserPG:
    """
    Require an authenticated, active user.
    Raises 401 if no valid session.
    """
    token = _extract_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = _resolve_user(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return user


def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[UserPG]:
    """
    Return the authenticated user if present, otherwise None.
    Does NOT raise — use for endpoints that work with or without auth.
    """
    token = _extract_token(request)
    if not token:
        return None
    return _resolve_user(db, token)


# ── Role-based access ────────────────────────────────────────────────────────

# Canonical role hierarchy (higher index = more privileged)
ROLE_HIERARCHY: list[str] = [
    "viewer",
    "data_engineer",
    "compliance",
    "risk_analyst",
    "portfolio_manager",
    "admin",
]


def _role_rank(role: str) -> int:
    try:
        return ROLE_HIERARCHY.index(role)
    except ValueError:
        return -1  # unknown role = lowest


def require_role(*allowed_roles: str):
    """
    Dependency factory: require the user to have one of the specified roles.

    Usage:
        @router.get("/admin")
        def admin_view(user: UserPG = Depends(require_role("admin"))):
            ...
    """
    def _dependency(
        request: Request,
        db: Session = Depends(get_db),
    ) -> UserPG:
        user = get_current_user(request, db)
        user_role = getattr(user, "role", "viewer")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required: {', '.join(allowed_roles)}",
            )
        return user
    return _dependency


def require_min_role(minimum_role: str):
    """
    Dependency factory: require the user to have at least the specified role
    level (based on ROLE_HIERARCHY).

    Usage:
        @router.post("/run-analysis")
        def run(user: UserPG = Depends(require_min_role("risk_analyst"))):
            ...
    """
    min_rank = _role_rank(minimum_role)

    def _dependency(
        request: Request,
        db: Session = Depends(get_db),
    ) -> UserPG:
        user = get_current_user(request, db)
        user_role = getattr(user, "role", "viewer")
        if _role_rank(user_role) < min_rank:
            raise HTTPException(
                status_code=403,
                detail=f"Requires at least '{minimum_role}' role",
            )
        return user
    return _dependency
