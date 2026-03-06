"""FastAPI dependencies for API v1"""
from typing import Generator, Optional
from fastapi import Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from db.postgres import SessionLocal


def get_db() -> Generator:
    """
    Dependency to get database session.
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class CommonQueryParams:
    """Common query parameters for list endpoints"""
    
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(50, ge=1, le=100, description="Items per page"),
        sort_by: Optional[str] = Query(None, description="Sort field"),
        sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order")
    ):
        self.page = page
        self.page_size = page_size
        self.skip = (page - 1) * page_size
        self.limit = page_size
        self.sort_by = sort_by
        self.sort_order = sort_order


class PaginationParams:
    """Pagination parameters"""

    def __init__(
        self,
        page: int = Query(1, ge=1),
        page_size: int = Query(50, ge=1, le=100)
    ):
        self.page = page
        self.page_size = page_size
        self.skip = (page - 1) * page_size
        self.limit = page_size


# ── Auth / RBAC dependencies ──────────────────────────────────────────────────

def _extract_token(request: Request) -> Optional[str]:
    token = request.cookies.get("session_token")
    if token:
        return token
    auth = request.headers.get("Authorization", "")
    return auth[7:] if auth.startswith("Bearer ") else None


def get_current_user(request: Request, db: Session = Depends(get_db)):
    """
    Dependency that resolves the current authenticated user from session token.
    Raises HTTP 401 if not authenticated.
    Returns UserPG instance.
    """
    from db.models.portfolio_pg import UserPG, UserSessionPG
    token = _extract_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    sess = db.query(UserSessionPG).filter(UserSessionPG.session_token == token).first()
    if not sess:
        raise HTTPException(status_code=401, detail="Invalid session")

    # Handle naive datetimes stored without tzinfo
    expires = sess.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")

    user = db.get(UserPG, sess.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # Update last_login (best-effort — column added by migration 025)
    try:
        user.last_login = datetime.now(timezone.utc)
        db.commit()
    except Exception:
        db.rollback()

    return user


def get_current_user_optional(request: Request, db: Session = Depends(get_db)):
    """
    Like get_current_user but returns None instead of raising 401.
    Use on endpoints that work both authenticated and unauthenticated.
    """
    try:
        return get_current_user(request, db)
    except HTTPException:
        return None


def require_role(*roles: str):
    """
    Dependency factory. Returns a dependency that enforces one of the given roles.
    Usage:
        @router.get("/admin-only")
        def admin_only(user = Depends(require_role("admin"))):
            ...
    """
    def _checker(user=Depends(get_current_user)):
        role = getattr(user, "role", "viewer")
        if role not in roles:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{role}' is not authorised. Required: {list(roles)}",
            )
        return user
    return _checker
