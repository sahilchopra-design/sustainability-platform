"""
FastAPI Audit Middleware — append-only action log for all mutating requests.

Captures every POST / PUT / PATCH / DELETE request and writes a record to
audit_log.  Read-only requests (GET / HEAD) are skipped to avoid noise.

The middleware is intentionally non-blocking:
  - DB write failures never propagate to the caller.
  - The original response is always returned unchanged.

Sensitive paths are redacted from the request summary (passwords, tokens).

Usage in server.py:
    from middleware.audit_middleware import AuditMiddleware
    app.add_middleware(AuditMiddleware)
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

# ── Paths whose body should NEVER be captured (security) ──────────────────────
_REDACT_PATHS: set[str] = {
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/google/session",
}

# ── Map HTTP method → audit action_class ──────────────────────────────────────
_METHOD_TO_CLASS = {
    "POST":   "CREATE",
    "PUT":    "UPDATE",
    "PATCH":  "UPDATE",
    "DELETE": "DELETE",
}

# ── Infer entity_type from the URL path ───────────────────────────────────────
_PATH_PREFIX_TO_ENTITY = {
    "/api/v1/portfolios":        "portfolio",
    "/api/v1/portfolio":         "portfolio",
    "/api/v1/assets":            "asset",
    "/api/v1/ecl":               "ecl_assessment",
    "/api/v1/pcaf":              "pcaf_portfolio",
    "/api/v1/supply-chain":      "supply_chain_entity",
    "/api/v1/sector":            "sector_assessment",
    "/api/v1/regulatory":        "regulatory_report",
    "/api/v1/csrd":              "csrd_entity",
    "/api/v1/re-clvar":          "re_clvar_assessment",
    "/api/v1/green-hydrogen":    "green_hydrogen_calc",
    "/api/v1/stranded-assets":   "stranded_asset",
    "/api/v1/nature-risk":       "nature_risk_site",
    "/api/v1/valuation":         "valuation",
    "/api/v1/carbon":            "carbon_project",
    "/api/v1/cbam":              "cbam_declaration",
    "/api/v1/agriculture":       "agriculture_entity",
    "/api/v1/mining":            "mining_entity",
    "/api/v1/insurance":         "insurance_entity",
    "/api/v1/engagement":        "engagement_entity",
    "/api/auth":                 "auth_session",
}


def _infer_entity_type(path: str) -> str:
    for prefix, entity_type in _PATH_PREFIX_TO_ENTITY.items():
        if path.startswith(prefix):
            return entity_type
    return "unknown"


def _extract_entity_id(path: str) -> Optional[str]:
    """
    Extract a UUID / integer entity ID from path segments, e.g.:
      /api/v1/portfolios/abc-123/assets  →  "abc-123"
    Returns the first path segment that looks like an ID (length > 8 chars).
    """
    parts = path.strip("/").split("/")
    for part in parts:
        if len(part) > 8 and ("-" in part or part.isdigit()):
            return part
    return None


def _make_checksum(
    timestamp_str: str,
    user_id: Optional[str],
    action: str,
    entity_id: Optional[str],
    new_values_str: str,
) -> str:
    raw = f"{timestamp_str}|{user_id or ''}|{action}|{entity_id or ''}|{new_values_str}"
    return hashlib.sha256(raw.encode()).hexdigest()


async def _safe_read_body(request: Request) -> Optional[dict]:
    """Read request body as JSON.  Returns None on any failure."""
    try:
        raw = await request.body()
        if raw:
            return json.loads(raw)
    except Exception:
        pass
    return None


def _sanitise(data: Optional[dict]) -> Optional[dict]:
    """Remove sensitive keys from a captured payload dict."""
    if not data:
        return None
    _SENSITIVE = {"password", "password_hash", "token", "session_token",
                  "secret", "api_key", "private_key", "credential"}
    return {
        k: "***REDACTED***" if k.lower() in _SENSITIVE else v
        for k, v in data.items()
    }


class AuditMiddleware(BaseHTTPMiddleware):
    """Intercepts POST/PUT/PATCH/DELETE and writes to audit_log."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        method = request.method.upper()
        # Skip read-only methods and health/docs endpoints
        if method not in _METHOD_TO_CLASS:
            return await call_next(request)

        path = request.url.path
        if path.startswith(("/docs", "/redoc", "/openapi", "/api/health")):
            return await call_next(request)

        # ── Capture timing and identity ────────────────────────────────────────
        start_ms = int(time.time() * 1000)

        # Extract user from session/bearer — non-blocking
        user_id: Optional[str] = None
        user_email: Optional[str] = None
        user_role: Optional[str] = None
        org_id: Optional[str] = None

        try:
            token = (
                request.cookies.get("session_token")
                or (request.headers.get("Authorization", "")[7:]
                    if request.headers.get("Authorization", "").startswith("Bearer ")
                    else None)
            )
            if token:
                try:
                    from db.base import SessionLocal
                    from db.models.portfolio_pg import UserPG, UserSessionPG
                    db = SessionLocal()
                    sess = (
                        db.query(UserSessionPG)
                        .filter(UserSessionPG.session_token == token)
                        .first()
                    )
                    if sess:
                        user = db.get(UserPG, sess.user_id)
                        if user:
                            user_id = user.user_id
                            user_email = user.email
                            user_role = getattr(user, "role", None)
                            org_id = str(getattr(user, "org_id", None) or "")
                    db.close()
                except Exception:
                    pass
        except Exception:
            pass

        # ── Read and stash body for audit (before calling route) ───────────────
        request_body: Optional[dict] = None
        if path not in _REDACT_PATHS:
            try:
                request_body = await _safe_read_body(request)
            except Exception:
                pass

        # ── Call the actual route ──────────────────────────────────────────────
        response = await call_next(request)
        duration_ms = int(time.time() * 1000) - start_ms

        # ── Write audit record asynchronously (best-effort) ───────────────────
        try:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)

            action_class = _METHOD_TO_CLASS.get(method, "CREATE")
            # Refine action_class for AUTH paths
            if path.startswith("/api/auth"):
                action_class = "AUTH"

            action_name = f"{_infer_entity_type(path)}.{method.lower()}"
            entity_type = _infer_entity_type(path)
            entity_id   = _extract_entity_id(path)
            sanitised   = _sanitise(request_body)
            new_values_str = json.dumps(sanitised, default=str) if sanitised else ""
            checksum    = _make_checksum(
                now.isoformat(), user_id, action_name, entity_id, new_values_str
            )

            # Resolve client IP (handle proxy headers)
            ip_str = (
                request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
                or request.headers.get("X-Real-IP", "")
                or (request.client.host if request.client else "")
            )

            from sqlalchemy import text
            from db.base import engine as db_engine

            with db_engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO audit_log (
                        timestamp, org_id, user_id, user_email, user_role,
                        ip_address, user_agent,
                        action_class, action, http_method, endpoint, http_status,
                        duration_ms, entity_type, entity_id,
                        request_summary, new_values, checksum
                    ) VALUES (
                        :ts, :org_id, :user_id, :user_email, :user_role,
                        :ip::inet, :ua,
                        :action_class, :action, :method, :endpoint, :status,
                        :duration_ms, :entity_type, :entity_id,
                        :req_summary, :new_values, :checksum
                    )
                """), {
                    "ts":           now,
                    "org_id":       org_id or None,
                    "user_id":      user_id,
                    "user_email":   user_email,
                    "user_role":    user_role,
                    "ip":           ip_str or None,
                    "ua":           request.headers.get("User-Agent"),
                    "action_class": action_class,
                    "action":       action_name,
                    "method":       method,
                    "endpoint":     str(request.url.path),
                    "status":       response.status_code,
                    "duration_ms":  duration_ms,
                    "entity_type":  entity_type,
                    "entity_id":    entity_id,
                    "req_summary":  json.dumps(sanitised, default=str) if sanitised else None,
                    "new_values":   new_values_str or None,
                    "checksum":     checksum,
                })
                conn.commit()
        except Exception as exc:
            # Never propagate audit failures to the caller
            logger.debug("Audit log write failed (non-critical): %s", exc)

        return response
