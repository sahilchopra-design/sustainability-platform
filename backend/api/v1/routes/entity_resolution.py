"""
Entity Resolution API routes — LEI lookup, sanctions screening, screening results.

Endpoints:
  GET  /entity-resolution/lei           — search LEI records
  GET  /entity-resolution/lei/{lei}     — get single LEI record
  GET  /entity-resolution/sanctions     — search sanctions list
  GET  /entity-resolution/sanctions/{id} — get single sanctions entity
  POST /entity-resolution/screen        — screen an entity name against sanctions
  GET  /entity-resolution/screening-results — list screening results
  GET  /entity-resolution/screening-results/{id} — get screening result detail
  PUT  /entity-resolution/screening-results/{id}/review — mark reviewed
  GET  /entity-resolution/stats         — entity resolution summary stats
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, or_, text
from sqlalchemy.orm import Session

from db.base import get_db
from db.models.entity_resolution import EntityLei, EntitySanction, EntityScreeningResult
from api.dependencies import get_current_user, require_role, require_min_role

router = APIRouter(prefix="/api/v1/entity-resolution", tags=["entity-resolution"])


# ── Pydantic models ─────────────────────────────────────────────────────

class ScreenRequest(BaseModel):
    entity_name: str
    entity_type: Optional[str] = None
    entity_identifier: Optional[str] = None
    portfolio_id: Optional[str] = None
    asset_id: Optional[str] = None


class ReviewRequest(BaseModel):
    status: str  # confirmed_match, false_positive, pending_review
    notes: Optional[str] = None


# ── LEI endpoints ────────────────────────────────────────────────────────

@router.get("/lei")
def search_lei(
    q: Optional[str] = Query(None, description="Search legal_name"),
    jurisdiction: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Search LEI records by name, jurisdiction, or status."""
    query = db.query(EntityLei)

    if q:
        query = query.filter(EntityLei.legal_name.ilike(f"%{q}%"))
    if jurisdiction:
        query = query.filter(EntityLei.jurisdiction == jurisdiction.upper())
    if status:
        query = query.filter(EntityLei.status == status.upper())

    total = query.count()
    records = query.order_by(EntityLei.legal_name).offset(offset).limit(limit).all()

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "records": [_lei_to_dict(r) for r in records],
    }


@router.get("/lei/{lei}")
def get_lei(
    lei: str,
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Get a single LEI record by its 20-character LEI code."""
    record = db.query(EntityLei).filter(EntityLei.lei == lei.upper()).first()
    if not record:
        raise HTTPException(status_code=404, detail="LEI not found")
    return _lei_to_dict(record)


# ── Sanctions endpoints ──────────────────────────────────────────────────

@router.get("/sanctions")
def search_sanctions(
    q: Optional[str] = Query(None, description="Search caption / names"),
    schema_type: Optional[str] = Query(None, description="Person, Company, LegalEntity, etc."),
    dataset: Optional[str] = Query(None, description="e.g. us_ofac_sdn, eu_fsf"),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Search sanctions entries by name or type."""
    query = db.query(EntitySanction)

    if q:
        # Search caption (text column) via ILIKE
        query = query.filter(EntitySanction.caption.ilike(f"%{q}%"))
    if schema_type:
        query = query.filter(EntitySanction.schema_type == schema_type)

    total = query.count()
    records = query.order_by(EntitySanction.caption).offset(offset).limit(limit).all()

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "records": [_sanction_to_dict(r) for r in records],
    }


@router.get("/sanctions/{sanction_id}")
def get_sanction(
    sanction_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Get a single sanctions entity by OpenSanctions ID."""
    record = db.query(EntitySanction).filter(EntitySanction.id == sanction_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Sanctions entity not found")
    return _sanction_to_dict(record)


# ── Screening endpoints ─────────────────────────────────────────────────

@router.post("/screen")
def screen_entity(
    req: ScreenRequest,
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("compliance")),
):
    """
    Screen an entity name against the local sanctions database.

    Uses ILIKE fuzzy matching on caption. Returns top matches ranked by
    similarity. Creates a screening result record for each match found.
    """
    if not req.entity_name or len(req.entity_name.strip()) < 2:
        raise HTTPException(status_code=400, detail="entity_name must be at least 2 characters")

    name = req.entity_name.strip()

    # Search sanctions by caption (case-insensitive substring)
    matches = (
        db.query(EntitySanction)
        .filter(EntitySanction.caption.ilike(f"%{name}%"))
        .limit(20)
        .all()
    )

    results = []
    for match in matches:
        # Simple similarity score based on string containment
        caption = match.caption or ""
        score = _simple_similarity(name.lower(), caption.lower())

        result = EntityScreeningResult(
            id=str(uuid.uuid4()),
            entity_name=req.entity_name,
            entity_type=req.entity_type,
            entity_identifier=req.entity_identifier,
            matched_sanction_id=match.id,
            match_score=score,
            match_method="ilike_substring",
            match_details={
                "matched_caption": match.caption,
                "matched_schema": match.schema_type,
                "datasets": match.datasets,
            },
            status="pending",
            portfolio_id=req.portfolio_id,
            asset_id=req.asset_id,
        )
        db.add(result)
        results.append(result)

    db.commit()

    return {
        "entity_name": req.entity_name,
        "matches_found": len(results),
        "results": [_screening_to_dict(r) for r in results],
    }


@router.get("/screening-results")
def list_screening_results(
    status: Optional[str] = Query(None, description="pending, confirmed_match, false_positive"),
    portfolio_id: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """List screening results, optionally filtered by status or portfolio."""
    query = db.query(EntityScreeningResult)

    if status:
        query = query.filter(EntityScreeningResult.status == status)
    if portfolio_id:
        query = query.filter(EntityScreeningResult.portfolio_id == portfolio_id)

    total = query.count()
    records = (
        query.order_by(EntityScreeningResult.screening_date.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "results": [_screening_to_dict(r) for r in records],
    }


@router.get("/screening-results/{result_id}")
def get_screening_result(
    result_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Get a single screening result detail."""
    record = db.query(EntityScreeningResult).filter(EntityScreeningResult.id == result_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Screening result not found")
    return _screening_to_dict(record)


@router.put("/screening-results/{result_id}/review")
def review_screening_result(
    result_id: str,
    req: ReviewRequest,
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("compliance")),
):
    """Mark a screening result as reviewed (confirmed_match, false_positive, etc.)."""
    record = db.query(EntityScreeningResult).filter(EntityScreeningResult.id == result_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Screening result not found")

    allowed = {"confirmed_match", "false_positive", "pending_review", "escalated"}
    if req.status not in allowed:
        raise HTTPException(status_code=400, detail=f"status must be one of {allowed}")

    record.status = req.status
    record.notes = req.notes
    record.reviewed_by = getattr(_user, "email", None) or getattr(_user, "id", "unknown")
    record.reviewed_at = datetime.now(timezone.utc)
    db.commit()

    return _screening_to_dict(record)


# ── Stats endpoint ───────────────────────────────────────────────────────

@router.get("/stats")
def entity_resolution_stats(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Summary statistics for entity resolution tables."""
    lei_count = db.query(func.count(EntityLei.lei)).scalar() or 0
    sanctions_count = db.query(func.count(EntitySanction.id)).scalar() or 0
    screening_count = db.query(func.count(EntityScreeningResult.id)).scalar() or 0
    pending_count = (
        db.query(func.count(EntityScreeningResult.id))
        .filter(EntityScreeningResult.status == "pending")
        .scalar() or 0
    )
    confirmed_count = (
        db.query(func.count(EntityScreeningResult.id))
        .filter(EntityScreeningResult.status == "confirmed_match")
        .scalar() or 0
    )

    return {
        "lei_records": lei_count,
        "sanctions_entities": sanctions_count,
        "screening_results": screening_count,
        "pending_reviews": pending_count,
        "confirmed_matches": confirmed_count,
    }


# ── Helpers ──────────────────────────────────────────────────────────────

def _simple_similarity(query: str, target: str) -> float:
    """Quick similarity score: ratio of query length to target length when contained."""
    if not target:
        return 0.0
    if query == target:
        return 1.0
    if query in target:
        return round(len(query) / len(target), 3)
    # Partial word overlap
    q_words = set(query.split())
    t_words = set(target.split())
    if not q_words:
        return 0.0
    overlap = q_words & t_words
    return round(len(overlap) / max(len(q_words), 1), 3)


def _lei_to_dict(r: EntityLei) -> dict:
    return {
        "lei": r.lei,
        "legal_name": r.legal_name,
        "status": r.status,
        "jurisdiction": r.jurisdiction,
        "entity_category": r.entity_category,
        "legal_form_code": r.legal_form_code,
        "legal_form_name": r.legal_form_name,
        "registered_address": r.registered_address,
        "headquarters_address": r.headquarters_address,
        "registration_status": r.registration_status,
        "direct_parent_lei": r.direct_parent_lei,
        "ultimate_parent_lei": r.ultimate_parent_lei,
        "managing_lou": r.managing_lou,
        "initial_registration_date": str(r.initial_registration_date) if r.initial_registration_date else None,
        "last_update_date": str(r.last_update_date) if r.last_update_date else None,
        "ingested_at": r.ingested_at.isoformat() if r.ingested_at else None,
    }


def _sanction_to_dict(r: EntitySanction) -> dict:
    return {
        "id": r.id,
        "schema_type": r.schema_type,
        "caption": r.caption,
        "names": r.names,
        "birth_date": r.birth_date,
        "nationalities": r.nationalities,
        "countries": r.countries,
        "identifiers": r.identifiers,
        "addresses": r.addresses,
        "datasets": r.datasets,
        "first_seen": r.first_seen.isoformat() if r.first_seen else None,
        "last_seen": r.last_seen.isoformat() if r.last_seen else None,
        "sanction_programs": r.sanction_programs,
        "topics": r.topics,
        "lei": r.lei,
        "ingested_at": r.ingested_at.isoformat() if r.ingested_at else None,
    }


def _screening_to_dict(r: EntityScreeningResult) -> dict:
    return {
        "id": r.id,
        "entity_name": r.entity_name,
        "entity_type": r.entity_type,
        "entity_identifier": r.entity_identifier,
        "matched_sanction_id": r.matched_sanction_id,
        "match_score": r.match_score,
        "match_method": r.match_method,
        "match_details": r.match_details,
        "screening_date": r.screening_date.isoformat() if r.screening_date else None,
        "status": r.status,
        "reviewed_by": r.reviewed_by,
        "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
        "notes": r.notes,
        "portfolio_id": r.portfolio_id,
        "asset_id": r.asset_id,
    }
