"""Regulatory Penalties routes — prefix /api/v1/regulatory-penalties (E35)"""

import logging
import json
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from services.regulatory_penalties_engine import (
    RegulatoryPenaltiesEngine,
    REGULATION_CONFIGS,
    SUPERVISORY_AUTHORITY_MAP,
    ENFORCEMENT_TIMELINE_2024_2030,
    VIOLATION_SEVERITY,
    HIGH_RISK_JURISDICTIONS,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/regulatory-penalties", tags=["Regulatory Penalties"])

_engine = RegulatoryPenaltiesEngine()


# ── Pydantic models ───────────────────────────────────────────────────────────

class PenaltyAssessRequest(BaseModel):
    entity_id: str
    entity_name: str
    annual_turnover_mn: float
    csrd_compliance_pct: Optional[float] = None
    sfdr_compliance_pct: Optional[float] = None
    taxonomy_compliance_pct: Optional[float] = None
    eudr_compliance_pct: Optional[float] = None
    csddd_compliance_pct: Optional[float] = None
    sector: Optional[str] = None
    jurisdiction: Optional[str] = None
    reporting_period: Optional[str] = None


class SingleRegulationRequest(BaseModel):
    entity_id: str
    regulation: str
    annual_turnover_mn: float
    compliance_pct: float
    violation_details: Optional[Dict[str, Any]] = None


class WhistleblowerRiskRequest(BaseModel):
    entity_id: str
    compliance_scores: Optional[Dict[str, float]] = None
    sector: Optional[str] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _save_assessment(pool, data: dict) -> None:
    """Persist penalty assessment to regulatory_penalty_assessments table."""
    sql = """
        INSERT INTO regulatory_penalty_assessments (
            assessment_id, entity_id, entity_name, annual_turnover_mn,
            reporting_period, sector, jurisdiction,
            avg_compliance_pct, overall_risk_level,
            total_max_penalty_mn, total_expected_penalty_mn,
            total_pct_of_turnover, num_violations,
            highest_risk_regulation,
            whistleblower_risk, whistleblower_risk_score,
            compliance_scores, violations_found,
            penalty_by_regulation, remediation_priorities,
            high_risk_jurisdiction,
            assessment_date, created_at, updated_at
        ) VALUES (
            $1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,
            $15,$16,$17,$18,$19,$20,$21,$22,$23,$24
        )
        ON CONFLICT (assessment_id) DO UPDATE SET
            total_expected_penalty_mn = EXCLUDED.total_expected_penalty_mn,
            overall_risk_level        = EXCLUDED.overall_risk_level,
            updated_at                = EXCLUDED.updated_at
    """
    async with pool.acquire() as conn:
        await conn.execute(
            sql,
            data["assessment_id"],
            data["entity_id"],
            data["entity_name"],
            data["annual_turnover_mn"],
            data.get("reporting_period"),
            data.get("sector"),
            data.get("jurisdiction"),
            data["avg_compliance_pct"],
            data["overall_risk_level"],
            data["total_max_penalty_mn"],
            data["total_expected_penalty_mn"],
            data["total_pct_of_turnover"],
            data["num_violations"],
            data.get("highest_risk_regulation"),
            data["whistleblower_risk"],
            data["whistleblower_risk_score"],
            json.dumps(data.get("compliance_scores", {})),
            json.dumps(data.get("violations_found", [])),
            json.dumps(data.get("penalty_by_regulation", {})),
            json.dumps(data.get("remediation_priorities", [])),
            data.get("high_risk_jurisdiction", False),
            data["assessment_date"],
            data["created_at"],
            data["updated_at"],
        )


def _build_compliance_scores(body: PenaltyAssessRequest) -> Dict[str, float]:
    """Assemble compliance score dict from individual fields."""
    scores = {}
    if body.csrd_compliance_pct is not None:
        scores["csrd"] = body.csrd_compliance_pct
    if body.sfdr_compliance_pct is not None:
        scores["sfdr"] = body.sfdr_compliance_pct
    if body.taxonomy_compliance_pct is not None:
        scores["taxonomy"] = body.taxonomy_compliance_pct
    if body.eudr_compliance_pct is not None:
        scores["eudr"] = body.eudr_compliance_pct
    if body.csddd_compliance_pct is not None:
        scores["csddd"] = body.csddd_compliance_pct
    return scores


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/assess")
async def run_full_assessment(body: PenaltyAssessRequest, request: Request):
    """Run a full regulatory penalty assessment across all 5 EU ESG frameworks."""
    compliance_scores = _build_compliance_scores(body)
    try:
        result = _engine.run_full_assessment(
            entity_id=body.entity_id,
            entity_name=body.entity_name,
            annual_turnover_mn=body.annual_turnover_mn,
            compliance_scores=compliance_scores,
            sector=body.sector,
            jurisdiction=body.jurisdiction,
            reporting_period=body.reporting_period,
        )
    except Exception as exc:
        logger.exception("Regulatory penalty assessment failed for %s", body.entity_id)
        raise HTTPException(status_code=500, detail=str(exc))

    pool = getattr(getattr(request.app, "state", None), "db_pool", None)
    if pool:
        try:
            await _save_assessment(pool, result)
        except Exception as exc:
            logger.warning("Could not persist penalty assessment: %s", exc)

    return result


@router.post("/regulation-penalty")
async def calculate_regulation_penalty(body: SingleRegulationRequest, request: Request):
    """Calculate penalty exposure for a single regulation."""
    if body.regulation not in REGULATION_CONFIGS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown regulation '{body.regulation}'. Valid: {list(REGULATION_CONFIGS.keys())}",
        )
    try:
        result = _engine.calculate_regulation_penalty(
            entity_id=body.entity_id,
            regulation=body.regulation,
            annual_turnover_mn=body.annual_turnover_mn,
            compliance_pct=body.compliance_pct,
            violation_details=body.violation_details,
        )
    except Exception as exc:
        logger.exception("Single regulation penalty calculation failed for %s", body.entity_id)
        raise HTTPException(status_code=500, detail=str(exc))
    return result


@router.post("/whistleblower-risk")
async def assess_whistleblower_risk(body: WhistleblowerRiskRequest, request: Request):
    """Assess whistleblower and internal reporting risk for an entity."""
    try:
        result = _engine.assess_whistleblower_risk(
            entity_id=body.entity_id,
            compliance_scores=body.compliance_scores or {},
            sector=body.sector,
        )
    except Exception as exc:
        logger.exception("Whistleblower risk assessment failed for %s", body.entity_id)
        raise HTTPException(status_code=500, detail=str(exc))
    return result


@router.get("/assessments/{entity_id}")
async def list_assessments(entity_id: str, request: Request):
    """List all penalty assessments for an entity."""
    pool = getattr(getattr(request.app, "state", None), "db_pool", None)
    if not pool:
        raise HTTPException(status_code=503, detail="Database unavailable")
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT assessment_id, entity_id, entity_name,
                       annual_turnover_mn, avg_compliance_pct, overall_risk_level,
                       total_expected_penalty_mn, num_violations,
                       highest_risk_regulation, whistleblower_risk,
                       created_at
                FROM regulatory_penalty_assessments
                WHERE entity_id = $1
                ORDER BY created_at DESC
                """,
                entity_id,
            )
        return [dict(r) for r in rows]
    except Exception as exc:
        logger.warning("DB read failed: %s", exc)
        raise HTTPException(status_code=503, detail="Database read failed")


@router.get("/assessment/{assessment_id}")
async def get_assessment(assessment_id: str, request: Request):
    """Retrieve a single regulatory penalty assessment by ID."""
    pool = getattr(getattr(request.app, "state", None), "db_pool", None)
    if not pool:
        raise HTTPException(status_code=503, detail="Database unavailable")
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM regulatory_penalty_assessments WHERE assessment_id = $1",
                assessment_id,
            )
        if not row:
            raise HTTPException(status_code=404, detail="Assessment not found")
        return dict(row)
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("DB read failed: %s", exc)
        raise HTTPException(status_code=503, detail="Database read failed")


@router.get("/ref/regulations")
async def get_regulations():
    """Return all regulation configurations with penalty formulas and scope."""
    return {
        "regulations": REGULATION_CONFIGS,
        "violation_severity": VIOLATION_SEVERITY,
    }


@router.get("/ref/enforcement-timeline")
async def get_enforcement_timeline():
    """Return key EU ESG enforcement milestones 2024-2030."""
    return {
        "enforcement_timeline": ENFORCEMENT_TIMELINE_2024_2030,
        "high_risk_jurisdictions": HIGH_RISK_JURISDICTIONS,
    }


@router.get("/ref/authorities")
async def get_authorities():
    """Return supervisory authority mapping by regulation and jurisdiction."""
    return {"supervisory_authorities": SUPERVISORY_AUTHORITY_MAP}
