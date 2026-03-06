"""
Audit Log API — read-only endpoints for querying the append-only audit trail.

Access restricted to admin and compliance roles.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, text
from sqlalchemy.orm import Session

from db.base import get_db
from api.dependencies import require_role

router = APIRouter(prefix="/api/v1/audit-log", tags=["audit-log"])


# ── List / search audit entries ──────────────────────────────────────────────

@router.get("/", summary="Query audit log entries")
def list_audit_entries(
    # Filters
    user_id: Optional[str] = Query(None, description="Filter by acting user ID"),
    user_email: Optional[str] = Query(None, description="Filter by user email (partial match)"),
    action_class: Optional[str] = Query(None, description="AUTH|CREATE|UPDATE|DELETE|CALCULATE|EXPORT|ADMIN"),
    entity_type: Optional[str] = Query(None, description="e.g. portfolio, ecl_assessment"),
    entity_id: Optional[str] = Query(None, description="Specific entity ID"),
    http_status_min: Optional[int] = Query(None, description="Min HTTP status (e.g. 400 for errors)"),
    since_hours: int = Query(24, ge=1, le=720, description="Look back N hours (default 24, max 720)"),
    # Pagination
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    # Auth
    db: Session = Depends(get_db),
    _user=Depends(require_role("admin", "compliance")),
):
    """
    Query the audit log with flexible filters.

    Only accessible to users with **admin** or **compliance** role.
    Results are ordered by timestamp descending (newest first).
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)

    conditions = ["a.timestamp >= :cutoff"]
    params: dict = {"cutoff": cutoff, "lim": limit, "off": offset}

    if user_id:
        conditions.append("a.user_id = :uid")
        params["uid"] = user_id
    if user_email:
        conditions.append("a.user_email ILIKE :uemail")
        params["uemail"] = f"%{user_email}%"
    if action_class:
        conditions.append("a.action_class = :aclass")
        params["aclass"] = action_class.upper()
    if entity_type:
        conditions.append("a.entity_type = :etype")
        params["etype"] = entity_type
    if entity_id:
        conditions.append("a.entity_id = :eid")
        params["eid"] = entity_id
    if http_status_min:
        conditions.append("a.http_status >= :smin")
        params["smin"] = http_status_min

    where = " AND ".join(conditions)
    sql = f"""
        SELECT a.id, a.timestamp, a.org_id, a.user_id, a.user_email, a.user_role,
               a.action_class, a.action, a.http_method, a.endpoint, a.http_status,
               a.duration_ms, a.entity_type, a.entity_id,
               a.ip_address::text, a.status, a.error_message
        FROM audit_log a
        WHERE {where}
        ORDER BY a.timestamp DESC
        LIMIT :lim OFFSET :off
    """

    count_sql = f"SELECT count(*) FROM audit_log a WHERE {where}"

    rows = db.execute(text(sql), params).mappings().all()
    total = db.execute(text(count_sql), {k: v for k, v in params.items() if k not in ("lim", "off")}).scalar()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "entries": [
            {
                "id": str(r["id"]),
                "timestamp": r["timestamp"].isoformat() if r["timestamp"] else None,
                "org_id": str(r["org_id"]) if r["org_id"] else None,
                "user_id": r["user_id"],
                "user_email": r["user_email"],
                "user_role": r["user_role"],
                "action_class": r["action_class"],
                "action": r["action"],
                "http_method": r["http_method"],
                "endpoint": r["endpoint"],
                "http_status": r["http_status"],
                "duration_ms": r["duration_ms"],
                "entity_type": r["entity_type"],
                "entity_id": r["entity_id"],
                "ip_address": r["ip_address"],
                "status": r["status"],
                "error_message": r["error_message"],
            }
            for r in rows
        ],
    }


# ── Summary stats ────────────────────────────────────────────────────────────

@router.get("/stats", summary="Audit log summary statistics")
def audit_stats(
    since_hours: int = Query(24, ge=1, le=720),
    db: Session = Depends(get_db),
    _user=Depends(require_role("admin", "compliance")),
):
    """Aggregated counts by action_class and top active users (last N hours)."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)

    by_class = db.execute(text("""
        SELECT action_class, count(*) AS cnt
        FROM audit_log
        WHERE timestamp >= :cutoff AND action_class IS NOT NULL
        GROUP BY action_class
        ORDER BY cnt DESC
    """), {"cutoff": cutoff}).mappings().all()

    by_user = db.execute(text("""
        SELECT user_email, count(*) AS cnt
        FROM audit_log
        WHERE timestamp >= :cutoff AND user_email IS NOT NULL
        GROUP BY user_email
        ORDER BY cnt DESC
        LIMIT 10
    """), {"cutoff": cutoff}).mappings().all()

    error_count = db.execute(text("""
        SELECT count(*) FROM audit_log
        WHERE timestamp >= :cutoff AND http_status >= 400
    """), {"cutoff": cutoff}).scalar()

    total = db.execute(text("""
        SELECT count(*) FROM audit_log
        WHERE timestamp >= :cutoff
    """), {"cutoff": cutoff}).scalar()

    return {
        "since_hours": since_hours,
        "total_entries": total,
        "error_count": error_count,
        "by_action_class": [{"action_class": r["action_class"], "count": r["cnt"]} for r in by_class],
        "top_users": [{"user_email": r["user_email"], "count": r["cnt"]} for r in by_user],
    }


# ── Single entry detail ──────────────────────────────────────────────────────

@router.get("/{entry_id}", summary="Get full audit entry with payload")
def get_audit_entry(
    entry_id: UUID,
    db: Session = Depends(get_db),
    _user=Depends(require_role("admin", "compliance")),
):
    """Return the full audit record including request/response payloads."""
    row = db.execute(text("""
        SELECT * FROM audit_log WHERE id = :eid LIMIT 1
    """), {"eid": str(entry_id)}).mappings().first()

    if not row:
        raise HTTPException(404, "Audit entry not found")

    return {
        "id": str(row["id"]),
        "timestamp": row["timestamp"].isoformat() if row["timestamp"] else None,
        "org_id": str(row["org_id"]) if row["org_id"] else None,
        "user_id": row.get("user_id"),
        "user_email": row.get("user_email"),
        "user_role": row.get("user_role"),
        "ip_address": str(row["ip_address"]) if row.get("ip_address") else None,
        "user_agent": row.get("user_agent"),
        "session_id": row.get("session_id"),
        "request_id": row.get("request_id"),
        "action_class": row.get("action_class"),
        "action": row.get("action"),
        "http_method": row.get("http_method"),
        "endpoint": row.get("endpoint"),
        "http_status": row.get("http_status"),
        "duration_ms": row.get("duration_ms"),
        "entity_type": row.get("entity_type"),
        "entity_id": row.get("entity_id"),
        "record_id": row.get("record_id"),
        "old_values": row.get("old_values"),
        "new_values": row.get("new_values"),
        "request_summary": row.get("request_summary"),
        "result_summary": row.get("result_summary"),
        "status": row.get("status"),
        "error_message": row.get("error_message"),
        "checksum": row.get("checksum"),
    }
