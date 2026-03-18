"""TNFD LEAP Process routes — prefix /api/v1/tnfd-leap (E32)"""

import logging
import json
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from services.tnfd_leap_engine import TNFDLEAPEngine, BIOMES, ENCORE_IMPACT_DRIVERS, SECTOR_NATURE_MATERIALITY, CROSS_FRAMEWORK_MAP

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/tnfd-leap", tags=["TNFD LEAP"])

_engine = TNFDLEAPEngine()


# ── Pydantic models ───────────────────────────────────────────────────────────

class TNFDLEAPRequest(BaseModel):
    entity_id: str
    entity_name: Optional[str] = None
    sector: str
    reporting_period: Optional[str] = None
    value_chain_scope: Optional[Dict[str, Any]] = None
    locations: Optional[List[Dict[str, Any]]] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _save_assessment(pool, data: dict) -> None:
    """Persist LEAP assessment to tnfd_leap_assessments table."""
    sql = """
        INSERT INTO tnfd_leap_assessments (
            assessment_id, entity_id, entity_name, sector, reporting_period,
            locate_score, evaluate_score, assess_score, prepare_score,
            overall_leap_score, leap_maturity,
            num_priority_locations, num_dependencies, num_impacts,
            num_material_risks, num_material_opportunities,
            risk_magnitude, opportunity_magnitude, total_financial_exposure_mn,
            disclosure_completeness_pct, num_targets_set,
            locate_detail, evaluate_detail, assess_detail, prepare_detail,
            priority_actions, cross_framework, framework_version,
            created_at, updated_at
        ) VALUES (
            $1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,
            $17,$18,$19,$20,$21,$22,$23,$24,$25,$26,$27,$28,$29,$30
        )
        ON CONFLICT (assessment_id) DO UPDATE SET
            overall_leap_score = EXCLUDED.overall_leap_score,
            leap_maturity       = EXCLUDED.leap_maturity,
            updated_at          = EXCLUDED.updated_at
    """
    async with pool.acquire() as conn:
        await conn.execute(
            sql,
            data["assessment_id"],
            data["entity_id"],
            data.get("entity_name"),
            data["sector"],
            data.get("reporting_period"),
            data["locate_score"],
            data["evaluate_score"],
            data["assess_score"],
            data["prepare_score"],
            data["overall_leap_score"],
            data["leap_maturity"],
            data["num_priority_locations"],
            data["num_dependencies"],
            data["num_impacts"],
            data["num_material_risks"],
            data["num_material_opportunities"],
            data["risk_magnitude"],
            data["opportunity_magnitude"],
            data["total_financial_exposure_mn"],
            data["disclosure_completeness_pct"],
            data["num_targets_set"],
            json.dumps(data.get("locate_detail", {})),
            json.dumps(data.get("evaluate_detail", {})),
            json.dumps(data.get("assess_detail", {})),
            json.dumps(data.get("prepare_detail", {})),
            json.dumps(data.get("priority_actions", [])),
            json.dumps(data.get("cross_framework", {})),
            data.get("framework_version"),
            data["created_at"],
            data["updated_at"],
        )


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/assess")
async def run_leap_assessment(body: TNFDLEAPRequest, request: Request):
    """Run a full 4-step TNFD LEAP assessment for an entity."""
    try:
        result = _engine.run_full_leap(
            entity_id=body.entity_id,
            sector=body.sector,
            reporting_period=body.reporting_period,
            entity_name=body.entity_name,
            value_chain_scope=body.value_chain_scope,
            locations=body.locations,
        )
    except Exception as exc:
        logger.exception("TNFD LEAP assessment failed for entity %s", body.entity_id)
        raise HTTPException(status_code=500, detail=str(exc))

    pool = getattr(getattr(request, "app", None), "state", None)
    pool = getattr(pool, "db_pool", None) if pool else None
    if pool:
        try:
            await _save_assessment(pool, result)
        except Exception as exc:
            logger.warning("Could not persist TNFD LEAP assessment: %s", exc)

    return result


@router.get("/assessments/{entity_id}")
async def list_assessments(entity_id: str, request: Request):
    """List all TNFD LEAP assessments for an entity."""
    pool = getattr(getattr(request.app, "state", None), "db_pool", None)
    if not pool:
        raise HTTPException(status_code=503, detail="Database unavailable")
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT assessment_id, entity_id, entity_name, sector,
                       reporting_period, overall_leap_score, leap_maturity,
                       risk_magnitude, disclosure_completeness_pct,
                       num_targets_set, created_at
                FROM tnfd_leap_assessments
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
    """Retrieve a single TNFD LEAP assessment by ID."""
    pool = getattr(getattr(request.app, "state", None), "db_pool", None)
    if not pool:
        raise HTTPException(status_code=503, detail="Database unavailable")
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM tnfd_leap_assessments WHERE assessment_id = $1",
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


@router.get("/ref/biomes")
async def get_biomes():
    """Return all TNFD/IPBES biome classifications."""
    return {"biomes": BIOMES, "count": len(BIOMES)}


@router.get("/ref/impact-drivers")
async def get_impact_drivers():
    """Return ENCORE impact driver categories."""
    return {"impact_drivers": ENCORE_IMPACT_DRIVERS, "count": len(ENCORE_IMPACT_DRIVERS)}


@router.get("/ref/sector-materiality")
async def get_sector_materiality():
    """Return sector-level nature materiality profiles."""
    return {"sector_materiality": SECTOR_NATURE_MATERIALITY}


@router.get("/ref/cross-framework")
async def get_cross_framework():
    """Return TNFD cross-framework alignment mapping."""
    return {"cross_framework": CROSS_FRAMEWORK_MAP}
