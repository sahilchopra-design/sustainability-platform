"""
Client Engagement Tracker
Routes: /api/v1/engagement/*

Tracks counterparty climate engagement under:
  - PRI Active Ownership 2.0 (AO2.0)
  - CA100+ Net Zero Benchmark
  - NZBA Phase 2 Engagement Policy
  - TCFD Engagement Disclosure

Entities → Interactions (log) → Commitments → Escalations
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from db.base import get_db

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/engagement",
    tags=["Client Engagement Tracker"],
)


# ── Models ────────────────────────────────────────────────────────────────────

class EntityIn(BaseModel):
    entity_name: str
    lei: Optional[str] = None
    isin: Optional[str] = None
    sector_gics: Optional[str] = None
    country_iso2: Optional[str] = None
    engagement_theme: str = "net_zero"          # net_zero | deforestation | water | governance | just_transition
    engagement_strategy: str = "direct"          # direct | collaborative | voting | policy
    priority_tier: int = 2                       # 1 = highest
    ca100_focus: bool = False
    nzba_engagement: bool = False
    engagement_lead: Optional[str] = None
    engagement_start_date: Optional[date] = None
    target_close_date: Optional[date] = None
    baseline_temp_score: Optional[float] = None
    current_temp_score: Optional[float] = None
    notes: Optional[str] = None


class LogEntryIn(BaseModel):
    entity_id: int
    log_date: date
    interaction_type: str = "meeting"            # meeting | call | letter | agm_vote | proxy_alert
    milestone: Optional[str] = None
    outcome: str = "pending"                     # positive | neutral | negative | pending
    next_action: Optional[str] = None
    next_action_date: Optional[date] = None
    participants: Optional[str] = None
    counterparty_participants: Optional[str] = None
    created_by: Optional[str] = None


class CommitmentIn(BaseModel):
    entity_id: int
    commitment_type: str                         # sbti_target | net_zero_pledge | scope3_disclosure | board_climate
    description: Optional[str] = None
    target_year: Optional[int] = None
    target_value: Optional[float] = None
    target_unit: Optional[str] = None
    baseline_year: Optional[int] = None
    status: str = "open"
    verification_body: Optional[str] = None
    verified: bool = False
    notes: Optional[str] = None


class EscalationIn(BaseModel):
    entity_id: int
    escalation_date: date
    escalation_type: str                         # vote_against | co_filer | divestment_warning | public_statement
    trigger_reason: Optional[str] = None
    action_taken: Optional[str] = None


class ProgressUpdate(BaseModel):
    overall_progress_pct: float
    current_temp_score: Optional[float] = None
    status: Optional[str] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ensure_tables(db: Session) -> None:
    """Bootstrap engagement tables if migration hasn't run yet."""
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS engagement_entities (
            id SERIAL PRIMARY KEY,
            entity_name TEXT NOT NULL,
            lei TEXT,
            isin TEXT,
            sector_gics TEXT,
            country_iso2 TEXT,
            engagement_theme TEXT DEFAULT 'net_zero',
            engagement_strategy TEXT DEFAULT 'direct',
            priority_tier INTEGER DEFAULT 2,
            ca100_focus BOOLEAN DEFAULT FALSE,
            nzba_engagement BOOLEAN DEFAULT FALSE,
            engagement_lead TEXT,
            engagement_start_date DATE,
            target_close_date DATE,
            status TEXT DEFAULT 'active',
            overall_progress_pct NUMERIC(5,1) DEFAULT 0,
            baseline_temp_score NUMERIC(4,2),
            current_temp_score NUMERIC(4,2),
            notes TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """))
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS engagement_log (
            id SERIAL PRIMARY KEY,
            entity_id INTEGER REFERENCES engagement_entities(id) ON DELETE CASCADE,
            log_date DATE NOT NULL,
            interaction_type TEXT,
            milestone TEXT,
            outcome TEXT DEFAULT 'pending',
            next_action TEXT,
            next_action_date DATE,
            participants TEXT,
            counterparty_participants TEXT,
            created_by TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """))
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS engagement_commitments (
            id SERIAL PRIMARY KEY,
            entity_id INTEGER REFERENCES engagement_entities(id) ON DELETE CASCADE,
            commitment_type TEXT,
            description TEXT,
            target_year INTEGER,
            target_value NUMERIC(12,4),
            target_unit TEXT,
            baseline_year INTEGER,
            status TEXT DEFAULT 'open',
            verification_body TEXT,
            verified BOOLEAN DEFAULT FALSE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """))
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS engagement_escalations (
            id SERIAL PRIMARY KEY,
            entity_id INTEGER REFERENCES engagement_entities(id) ON DELETE CASCADE,
            escalation_date DATE NOT NULL,
            escalation_type TEXT,
            trigger_reason TEXT,
            action_taken TEXT,
            resolution TEXT,
            resolved_at DATE,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """))
    db.commit()


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/entities")
def list_entities(db: Session = Depends(get_db)):
    """List all engagement entities with summary stats."""
    _ensure_tables(db)
    rows = db.execute(text("""
        SELECT e.*,
               COUNT(DISTINCT l.id) AS interaction_count,
               COUNT(DISTINCT c.id) AS commitment_count,
               COUNT(DISTINCT esc.id) AS escalation_count,
               MAX(l.log_date) AS last_interaction_date
        FROM engagement_entities e
        LEFT JOIN engagement_log l ON l.entity_id = e.id
        LEFT JOIN engagement_commitments c ON c.entity_id = e.id
        LEFT JOIN engagement_escalations esc ON esc.entity_id = e.id
        GROUP BY e.id
        ORDER BY e.priority_tier, e.entity_name
    """)).fetchall()
    return [dict(r._mapping) for r in rows]


@router.post("/entities")
def create_entity(payload: EntityIn, db: Session = Depends(get_db)):
    """Register a new counterparty under engagement."""
    _ensure_tables(db)
    try:
        result = db.execute(text("""
            INSERT INTO engagement_entities
              (entity_name, lei, isin, sector_gics, country_iso2,
               engagement_theme, engagement_strategy, priority_tier,
               ca100_focus, nzba_engagement, engagement_lead,
               engagement_start_date, target_close_date,
               baseline_temp_score, current_temp_score, notes)
            VALUES
              (:name, :lei, :isin, :sector, :cty,
               :theme, :strategy, :tier,
               :ca100, :nzba, :lead,
               :start, :close,
               :bt, :ct, :notes)
            RETURNING id
        """), {
            "name": payload.entity_name, "lei": payload.lei, "isin": payload.isin,
            "sector": payload.sector_gics, "cty": payload.country_iso2,
            "theme": payload.engagement_theme, "strategy": payload.engagement_strategy,
            "tier": payload.priority_tier, "ca100": payload.ca100_focus,
            "nzba": payload.nzba_engagement, "lead": payload.engagement_lead,
            "start": payload.engagement_start_date, "close": payload.target_close_date,
            "bt": payload.baseline_temp_score, "ct": payload.current_temp_score,
            "notes": payload.notes,
        })
        new_id = result.fetchone()[0]
        db.commit()
        return {"id": new_id, "entity_name": payload.entity_name}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entities/{entity_id}")
def get_entity(entity_id: int, db: Session = Depends(get_db)):
    """Full entity detail with log, commitments, escalations."""
    _ensure_tables(db)
    entity = db.execute(text("SELECT * FROM engagement_entities WHERE id=:id"), {"id": entity_id}).fetchone()
    if not entity:
        raise HTTPException(404, "Entity not found")
    logs = db.execute(text("SELECT * FROM engagement_log WHERE entity_id=:id ORDER BY log_date DESC"), {"id": entity_id}).fetchall()
    comms = db.execute(text("SELECT * FROM engagement_commitments WHERE entity_id=:id ORDER BY target_year"), {"id": entity_id}).fetchall()
    escs = db.execute(text("SELECT * FROM engagement_escalations WHERE entity_id=:id ORDER BY escalation_date DESC"), {"id": entity_id}).fetchall()
    return {
        "entity": dict(entity._mapping),
        "log": [dict(r._mapping) for r in logs],
        "commitments": [dict(r._mapping) for r in comms],
        "escalations": [dict(r._mapping) for r in escs],
    }


@router.patch("/entities/{entity_id}/progress")
def update_progress(entity_id: int, payload: ProgressUpdate, db: Session = Depends(get_db)):
    """Update engagement progress % and current temperature score."""
    _ensure_tables(db)
    updates = ["overall_progress_pct=:pct", "updated_at=NOW()"]
    params: Dict[str, Any] = {"id": entity_id, "pct": payload.overall_progress_pct}
    if payload.current_temp_score is not None:
        updates.append("current_temp_score=:ct"); params["ct"] = payload.current_temp_score
    if payload.status:
        updates.append("status=:status"); params["status"] = payload.status
    db.execute(text(f"UPDATE engagement_entities SET {', '.join(updates)} WHERE id=:id"), params)
    db.commit()
    return {"status": "updated", "entity_id": entity_id}


@router.post("/log")
def add_log_entry(payload: LogEntryIn, db: Session = Depends(get_db)):
    """Record an engagement interaction."""
    _ensure_tables(db)
    try:
        result = db.execute(text("""
            INSERT INTO engagement_log
              (entity_id, log_date, interaction_type, milestone, outcome,
               next_action, next_action_date, participants, counterparty_participants, created_by)
            VALUES
              (:eid, :dt, :itype, :milestone, :outcome,
               :nxt, :nxt_dt, :part, :cpart, :by)
            RETURNING id
        """), {
            "eid": payload.entity_id, "dt": payload.log_date,
            "itype": payload.interaction_type, "milestone": payload.milestone,
            "outcome": payload.outcome, "nxt": payload.next_action,
            "nxt_dt": payload.next_action_date, "part": payload.participants,
            "cpart": payload.counterparty_participants, "by": payload.created_by,
        })
        new_id = result.fetchone()[0]
        db.commit()
        return {"id": new_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/commitments")
def add_commitment(payload: CommitmentIn, db: Session = Depends(get_db)):
    """Record a counterparty climate commitment."""
    _ensure_tables(db)
    try:
        result = db.execute(text("""
            INSERT INTO engagement_commitments
              (entity_id, commitment_type, description, target_year, target_value,
               target_unit, baseline_year, status, verification_body, verified, notes)
            VALUES
              (:eid, :ctype, :desc, :yr, :val,
               :unit, :base, :status, :vbody, :verified, :notes)
            RETURNING id
        """), {
            "eid": payload.entity_id, "ctype": payload.commitment_type,
            "desc": payload.description, "yr": payload.target_year,
            "val": payload.target_value, "unit": payload.target_unit,
            "base": payload.baseline_year, "status": payload.status,
            "vbody": payload.verification_body, "verified": payload.verified,
            "notes": payload.notes,
        })
        new_id = result.fetchone()[0]
        db.commit()
        return {"id": new_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/escalations")
def add_escalation(payload: EscalationIn, db: Session = Depends(get_db)):
    """Record an escalation action against a counterparty."""
    _ensure_tables(db)
    try:
        result = db.execute(text("""
            INSERT INTO engagement_escalations
              (entity_id, escalation_date, escalation_type, trigger_reason, action_taken)
            VALUES (:eid, :dt, :etype, :reason, :action)
            RETURNING id
        """), {
            "eid": payload.entity_id, "dt": payload.escalation_date,
            "etype": payload.escalation_type, "reason": payload.trigger_reason,
            "action": payload.action_taken,
        })
        new_id = result.fetchone()[0]
        db.commit()
        # auto-escalate entity status
        db.execute(text("UPDATE engagement_entities SET status='escalated', updated_at=NOW() WHERE id=:id"), {"id": payload.entity_id})
        db.commit()
        return {"id": new_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
def engagement_summary(db: Session = Depends(get_db)):
    """Portfolio-level engagement dashboard summary."""
    _ensure_tables(db)
    try:
        totals = db.execute(text("""
            SELECT
                COUNT(*) AS entity_count,
                COUNT(*) FILTER (WHERE status = 'active') AS active_count,
                COUNT(*) FILTER (WHERE status = 'escalated') AS escalated_count,
                COUNT(*) FILTER (WHERE status = 'closed') AS closed_count,
                COUNT(*) FILTER (WHERE ca100_focus = TRUE) AS ca100_count,
                AVG(overall_progress_pct) AS avg_progress_pct,
                AVG(baseline_temp_score) AS avg_baseline_temp,
                AVG(current_temp_score) AS avg_current_temp
            FROM engagement_entities
        """)).fetchone()

        by_theme = db.execute(text("""
            SELECT engagement_theme, COUNT(*) AS count,
                   AVG(overall_progress_pct) AS avg_progress
            FROM engagement_entities
            GROUP BY engagement_theme ORDER BY count DESC
        """)).fetchall()

        by_tier = db.execute(text("""
            SELECT priority_tier, COUNT(*) AS count,
                   COUNT(*) FILTER (WHERE status='escalated') AS escalated
            FROM engagement_entities
            GROUP BY priority_tier ORDER BY priority_tier
        """)).fetchall()

        upcoming = db.execute(text("""
            SELECT l.next_action_date, l.next_action, e.entity_name, e.engagement_theme
            FROM engagement_log l
            JOIN engagement_entities e ON e.id = l.entity_id
            WHERE l.next_action_date >= CURRENT_DATE
            ORDER BY l.next_action_date
            LIMIT 10
        """)).fetchall()

        def safe(v):
            return round(float(v), 2) if v is not None else None

        return {
            "totals": {
                "entity_count": totals[0] or 0,
                "active": totals[1] or 0,
                "escalated": totals[2] or 0,
                "closed": totals[3] or 0,
                "ca100_count": totals[4] or 0,
                "avg_progress_pct": safe(totals[5]),
                "avg_baseline_temp_c": safe(totals[6]),
                "avg_current_temp_c": safe(totals[7]),
                "temp_delta_c": safe((totals[7] or 0) - (totals[6] or 0)) if totals[6] and totals[7] else None,
            },
            "by_theme": [dict(r._mapping) for r in by_theme],
            "by_priority_tier": [dict(r._mapping) for r in by_tier],
            "upcoming_actions": [dict(r._mapping) for r in upcoming],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/entities/{entity_id}")
def delete_entity(entity_id: int, db: Session = Depends(get_db)):
    db.execute(text("DELETE FROM engagement_entities WHERE id=:id"), {"id": entity_id})
    db.commit()
    return {"status": "deleted"}
