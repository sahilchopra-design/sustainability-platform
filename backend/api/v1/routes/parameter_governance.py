"""
Parameter Governance Routes
GET    /api/v1/parameters               — list active parameters
POST   /api/v1/parameters               — propose new / updated parameter value
GET    /api/v1/parameters/{param_id}    — get single parameter with history
POST   /api/v1/parameters/{param_id}/approve   — approve a pending change request
POST   /api/v1/parameters/{param_id}/reject    — reject a pending change request
GET    /api/v1/parameters/change-requests      — list pending approval queue

Implements four-eyes / dual-control for NGFS, PCAF, PD, stranded-asset, and
scenario engine parameters. Aligned with EBA Guidelines on Internal Governance
(EBA/GL/2021/05 §§ 57-64).
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from db.base import get_db

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/parameters",
    tags=["Parameter Governance"],
)


# ── Pydantic models ────────────────────────────────────────────────────────────

class ParameterProposal(BaseModel):
    parameter_name: str
    parameter_category: str                      # scenario | pcaf | pd | stranded | carbon | custom
    description: Optional[str] = None
    value_numeric: Optional[float] = None
    value_text: Optional[str] = None
    value_json: Optional[Dict[str, Any]] = None
    unit: Optional[str] = None
    source: Optional[str] = None                 # e.g. "NGFS Phase 4 (2023)"
    effective_date: Optional[str] = None         # ISO date
    expiry_date: Optional[str] = None
    justification: str = ""
    org_id: Optional[str] = None


class ParameterApprovalAction(BaseModel):
    reviewer_comment: Optional[str] = None
    reviewer_id: Optional[str] = None


class ParameterOut(BaseModel):
    id: str
    parameter_name: str
    parameter_category: str
    description: Optional[str]
    value_numeric: Optional[float]
    value_text: Optional[str]
    unit: Optional[str]
    source: Optional[str]
    approval_status: str
    version: int
    effective_date: Optional[str]
    expiry_date: Optional[str]
    created_at: str
    org_id: Optional[str]


class ChangeRequestOut(BaseModel):
    request_id: str
    parameter_id: str
    parameter_name: str
    requested_value_numeric: Optional[float]
    requested_value_text: Optional[str]
    justification: str
    approval_status: str
    requested_at: str
    reviewer_comment: Optional[str]
    reviewed_at: Optional[str]


# ── Helper ─────────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("", response_model=List[Dict[str, Any]])
def list_parameters(
    category: Optional[str] = Query(None),
    status: str = Query("approved"),
    limit: int = Query(100),
    offset: int = Query(0),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """List calculation parameters, optionally filtered by category and approval status."""
    try:
        where_clauses = ["approval_status = :status"]
        params: Dict[str, Any] = {"status": status, "lim": limit, "off": offset}

        if category:
            where_clauses.append("parameter_category = :category")
            params["category"] = category

        where_sql = " AND ".join(where_clauses)

        rows = db.execute(
            text(f"""
                SELECT id, parameter_name, parameter_category, description,
                       value_numeric, value_text, unit, source,
                       approval_status, version, effective_date, expiry_date,
                       created_at, org_id
                FROM calculation_parameters
                WHERE {where_sql}
                ORDER BY parameter_category, parameter_name, version DESC
                LIMIT :lim OFFSET :off
            """),
            params,
        ).fetchall()
        return [dict(r._mapping) for r in rows]
    except Exception as exc:
        logger.warning("list_parameters failed: %s", exc)
        return []


@router.post("", response_model=Dict[str, Any], status_code=201)
def propose_parameter(
    proposal: ParameterProposal,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Propose a new parameter value. Status is set to 'pending' until approved
    by a second reviewer (four-eyes control).
    """
    # Determine next version number
    try:
        existing = db.execute(
            text("""
                SELECT COALESCE(MAX(version), 0) AS max_v
                FROM calculation_parameters
                WHERE parameter_name = :pname
            """),
            {"pname": proposal.parameter_name},
        ).fetchone()
        next_version = (existing.max_v if existing else 0) + 1
    except Exception:
        next_version = 1

    param_id = str(uuid.uuid4())

    try:
        db.execute(
            text("""
                INSERT INTO calculation_parameters
                    (id, parameter_name, parameter_category, description,
                     value_numeric, value_text, value_json, unit, source,
                     approval_status, version, effective_date, expiry_date,
                     justification, created_at, org_id)
                VALUES
                    (:id, :pname, :pcat, :desc,
                     :vnum, :vtxt, :vjson::jsonb, :unit, :source,
                     'pending', :ver, :eff, :exp,
                     :just, NOW(), :org)
            """),
            {
                "id": param_id,
                "pname": proposal.parameter_name,
                "pcat": proposal.parameter_category,
                "desc": proposal.description,
                "vnum": proposal.value_numeric,
                "vtxt": proposal.value_text,
                "vjson": str(proposal.value_json) if proposal.value_json else None,
                "unit": proposal.unit,
                "source": proposal.source,
                "ver": next_version,
                "eff": proposal.effective_date,
                "exp": proposal.expiry_date,
                "just": proposal.justification,
                "org": proposal.org_id,
            },
        )

        # Create change request record
        cr_id = str(uuid.uuid4())
        db.execute(
            text("""
                INSERT INTO parameter_change_requests
                    (id, parameter_id, parameter_name, parameter_category,
                     requested_value_numeric, requested_value_text,
                     justification, approval_status, requested_at)
                VALUES
                    (:id, :pid, :pname, :pcat,
                     :vnum, :vtxt,
                     :just, 'pending', NOW())
            """),
            {
                "id": cr_id,
                "pid": param_id,
                "pname": proposal.parameter_name,
                "pcat": proposal.parameter_category,
                "vnum": proposal.value_numeric,
                "vtxt": proposal.value_text,
                "just": proposal.justification,
            },
        )
        db.commit()
        return {
            "parameter_id": param_id,
            "change_request_id": cr_id,
            "status": "pending",
            "version": next_version,
            "message": "Parameter proposed. Awaiting second reviewer approval.",
        }
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/change-requests", response_model=List[Dict[str, Any]])
def list_change_requests(
    status: str = Query("pending"),
    limit: int = Query(50),
    offset: int = Query(0),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Return pending (or all) parameter change requests for the approval queue."""
    try:
        rows = db.execute(
            text("""
                SELECT id AS request_id, parameter_id, parameter_name,
                       parameter_category, requested_value_numeric, requested_value_text,
                       justification, approval_status, requested_at,
                       reviewer_comment, reviewed_at
                FROM parameter_change_requests
                WHERE approval_status = :status
                ORDER BY requested_at DESC
                LIMIT :lim OFFSET :off
            """),
            {"status": status, "lim": limit, "off": offset},
        ).fetchall()
        return [dict(r._mapping) for r in rows]
    except Exception as exc:
        logger.warning("list_change_requests failed: %s", exc)
        return []


@router.get("/{param_id}", response_model=Dict[str, Any])
def get_parameter(
    param_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Return a single parameter record with its change request history."""
    try:
        row = db.execute(
            text("""
                SELECT id, parameter_name, parameter_category, description,
                       value_numeric, value_text, unit, source,
                       approval_status, version, effective_date, expiry_date,
                       justification, created_at, org_id
                FROM calculation_parameters
                WHERE id = :pid
            """),
            {"pid": param_id},
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Parameter not found")

        param = dict(row._mapping)

        # Attach change request history
        try:
            history = db.execute(
                text("""
                    SELECT id, approval_status, requested_at,
                           reviewer_comment, reviewed_at
                    FROM parameter_change_requests
                    WHERE parameter_id = :pid
                    ORDER BY requested_at DESC
                """),
                {"pid": param_id},
            ).fetchall()
            param["change_request_history"] = [dict(h._mapping) for h in history]
        except Exception:
            param["change_request_history"] = []

        return param
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/{param_id}/approve", response_model=Dict[str, Any])
def approve_parameter(
    param_id: str,
    action: ParameterApprovalAction,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Approve a pending parameter change. Sets approval_status to 'approved'
    on both calculation_parameters and parameter_change_requests.
    """
    try:
        updated = db.execute(
            text("""
                UPDATE calculation_parameters
                SET approval_status = 'approved'
                WHERE id = :pid AND approval_status = 'pending'
                RETURNING id, parameter_name, version
            """),
            {"pid": param_id},
        ).fetchone()

        if not updated:
            raise HTTPException(
                status_code=404,
                detail="Parameter not found or is not in pending state",
            )

        db.execute(
            text("""
                UPDATE parameter_change_requests
                SET approval_status = 'approved',
                    reviewer_comment = :comment,
                    reviewed_at = NOW()
                WHERE parameter_id = :pid AND approval_status = 'pending'
            """),
            {"pid": param_id, "comment": action.reviewer_comment},
        )
        db.commit()
        return {
            "parameter_id": param_id,
            "parameter_name": updated.parameter_name,
            "version": updated.version,
            "status": "approved",
            "approved_at": _now_iso(),
        }
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/{param_id}/reject", response_model=Dict[str, Any])
def reject_parameter(
    param_id: str,
    action: ParameterApprovalAction,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Reject a pending parameter change request."""
    try:
        updated = db.execute(
            text("""
                UPDATE calculation_parameters
                SET approval_status = 'rejected'
                WHERE id = :pid AND approval_status = 'pending'
                RETURNING id, parameter_name
            """),
            {"pid": param_id},
        ).fetchone()

        if not updated:
            raise HTTPException(
                status_code=404,
                detail="Parameter not found or is not in pending state",
            )

        db.execute(
            text("""
                UPDATE parameter_change_requests
                SET approval_status = 'rejected',
                    reviewer_comment = :comment,
                    reviewed_at = NOW()
                WHERE parameter_id = :pid AND approval_status = 'pending'
            """),
            {"pid": param_id, "comment": action.reviewer_comment},
        )
        db.commit()
        return {
            "parameter_id": param_id,
            "parameter_name": updated.parameter_name,
            "status": "rejected",
            "rejected_at": _now_iso(),
        }
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc)) from exc
