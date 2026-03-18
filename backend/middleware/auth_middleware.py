"""
FastAPI Auth Middleware — enforces session-based authentication on all
mutating API requests (POST / PUT / PATCH / DELETE).

Environment control:
  REQUIRE_AUTH=true   — enforce session auth (use in production)
  REQUIRE_AUTH=false  — bypass auth (default; safe for dev/demo)

Skip list (no auth required even when REQUIRE_AUTH=true):
  - Non-API paths (no /api/ prefix)
  - Health check: /api/health
  - Auth routes: /api/auth/*
  - GET/HEAD/OPTIONS on any path (read-only)
  - GET requests to reference-data endpoints: /api/v1/*/ref/*

For all other /api/v1/* requests when REQUIRE_AUTH=true the middleware:
  1. Extracts a bearer token from the Authorization header or session_token cookie
  2. Validates it against user_sessions_pg (checks expiry + active status)
  3. Attaches request.state.user (UserPG row) on success
  4. Returns a 401 JSON response on failure

Org isolation (multi-tenant):
  When a valid user is resolved and the user has an org_id set, the
  request.state.org_id value is populated so downstream query helpers
  can filter by organisation.  Endpoints that call _org_filter(request)
  automatically scope DB queries to the authenticated user's org.

Usage in server.py:
    from middleware.auth_middleware import AuthMiddleware
    app.add_middleware(AuthMiddleware)
"""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# ── Env gate — set REQUIRE_AUTH=true in production ───────────────────────────
REQUIRE_AUTH: bool = os.environ.get("REQUIRE_AUTH", "false").lower() in (
    "true", "1", "yes"
)

# ── Paths that never require auth ────────────────────────────────────────────
_PUBLIC_PATH_PREFIXES: tuple[str, ...] = (
    "/api/health",
    "/api/auth/",
    "/api/auth",       # exact match (login / register live here)
    "/docs",
    "/redoc",
    "/openapi.json",
)

# Methods that are always allowed without auth (read-only)
_SAFE_METHODS: frozenset[str] = frozenset({"GET", "HEAD", "OPTIONS"})

# Compiled pattern: GET /api/v1/<anything>/ref/<anything>
_REF_DATA_PATTERN = re.compile(r"^/api/v1/.+/ref(/.*)?$")


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Starlette middleware that enforces bearer-token / cookie session auth
    on all mutating /api/* requests.
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method.upper()

        # ── 1. Skip non-API paths entirely ───────────────────────────────
        if not path.startswith("/api/"):
            return await call_next(request)

        # ── 2. Skip explicitly public paths ──────────────────────────────
        if any(path.startswith(p) for p in _PUBLIC_PATH_PREFIXES):
            return await call_next(request)

        # ── 3. Safe (read-only) methods are always allowed ───────────────
        if method in _SAFE_METHODS:
            return await call_next(request)

        # ── 4. GET reference-data endpoints (extra safety net) ───────────
        #    Already covered by step 3, but kept for clarity / future-proofing.
        if method == "GET" and _REF_DATA_PATTERN.match(path):
            return await call_next(request)

        # ── 5. Auth gate — bypass in dev/demo mode ───────────────────────
        if not REQUIRE_AUTH:
            # Still populate request.state.user as None so downstream code
            # can check it without AttributeError.
            request.state.user = None
            request.state.org_id = None
            return await call_next(request)

        # ── 6. Mutating request on /api/* → require valid session ────────
        token = _extract_token(request)
        if not token:
            return _unauthorized("Missing authentication token")

        user = _validate_session(token)
        if user is None:
            return _unauthorized("Invalid or expired session")

        # Attach user + org to request state so downstream handlers can access it
        request.state.user = user
        request.state.org_id = getattr(user, "org_id", None)
        return await call_next(request)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _extract_token(request: Request) -> str | None:
    """Pull bearer token from Authorization header or session_token cookie."""
    # Try cookie first (browser sessions)
    token = request.cookies.get("session_token")
    if token:
        return token
    # Fall back to Authorization header (API clients)
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return None


def _validate_session(token: str):
    """
    Look up the token in user_sessions_pg and return the UserPG row,
    or None if invalid / expired.

    Uses a short-lived DB session (not the request-scoped one from Depends)
    because middleware runs before the DI container.
    """
    from db.postgres import SessionLocal
    from db.models.portfolio_pg import UserPG, UserSessionPG

    db = SessionLocal()
    try:
        sess = (
            db.query(UserSessionPG)
            .filter(UserSessionPG.session_token == token)
            .first()
        )
        if not sess:
            return None

        # Handle naive datetimes stored without tzinfo
        expires = sess.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires < datetime.now(timezone.utc):
            return None

        user = db.get(UserPG, sess.user_id)
        if user and not getattr(user, "is_active", True):
            return None  # deactivated account
        return user
    except Exception:
        logger.exception("Auth middleware: session validation error")
        return None
    finally:
        db.close()


def _unauthorized(detail: str) -> JSONResponse:
    """Return a 401 JSON error response."""
    return JSONResponse(
        status_code=401,
        content={"detail": detail},
    )


# ── P0-2: Multi-tenant org isolation helpers ─────────────────────────────────

def get_request_org_id(request: Request):
    """
    Return the org_id for the current request, or None if unauthenticated / no org.

    Usage in route handlers:
        from middleware.auth_middleware import get_request_org_id

        @router.post("/calculate")
        def calculate(req: Request, payload: MyModel, db: Session = Depends(get_db)):
            org_id = get_request_org_id(req)
            query = db.query(MyModel)
            if org_id:
                query = query.filter(MyModel.org_id == org_id)
            ...
    """
    return getattr(request.state, "org_id", None)


def apply_org_filter(query, model_cls, request: Request):
    """
    Convenience helper: apply org_id filter to a SQLAlchemy query if the
    model has an org_id column and the request carries an org context.

    Returns the query unchanged if org isolation is not applicable.

    Example:
        q = db.query(PortfolioPG)
        q = apply_org_filter(q, PortfolioPG, request)
        rows = q.all()
    """
    org_id = get_request_org_id(request)
    if org_id is None:
        return query
    if not hasattr(model_cls, "org_id"):
        return query
    return query.filter(model_cls.org_id == org_id)
