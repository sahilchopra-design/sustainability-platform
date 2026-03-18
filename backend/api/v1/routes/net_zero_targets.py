"""Net Zero Target Setting routes — prefix /api/v1/net-zero-targets (E33)"""

import logging
import json
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from services.net_zero_targets_engine import (
    NetZeroTargetsEngine,
    FRAMEWORK_CONFIGS,
    SBTI_PATHWAYS,
    SECTOR_PATHWAYS,
    ENTITY_TYPES,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/net-zero-targets", tags=["Net Zero Targets"])

_engine = NetZeroTargetsEngine()


# ── Pydantic models ───────────────────────────────────────────────────────────

class NetZeroAssessRequest(BaseModel):
    entity_id: str
    entity_name: Optional[str] = None
    entity_type: str = "corporate"
    framework: str = "sbti"
    base_year: Optional[int] = 2019
    base_year_emissions: Optional[float] = None
    scope1_tco2e: Optional[float] = None
    scope2_tco2e: Optional[float] = None
    scope3_tco2e: Optional[float] = None
    net_zero_target_year: Optional[int] = 2050
    near_term_target_year: Optional[int] = 2030
    near_term_reduction_pct: Optional[float] = None
    long_term_reduction_pct: Optional[float] = None
    reporting_period: Optional[str] = None


class TemperatureScoreRequest(BaseModel):
    entity_id: str
    scope1: float
    scope2: float
    scope3: float
    reduction_targets: Optional[Dict[str, float]] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _save_assessment(pool, data: dict) -> None:
    """Persist net zero assessment to net_zero_target_assessments table."""
    sql = """
        INSERT INTO net_zero_target_assessments (
            assessment_id, entity_id, entity_name, entity_type, framework,
            base_year, base_year_emissions_tco2e,
            scope1_tco2e, scope2_tco2e, scope3_tco2e,
            near_term_target_year, near_term_reduction_pct,
            long_term_reduction_pct, net_zero_target_year,
            sbti_pathway, temperature_score_c, temperature_classification,
            pathway_gap_pct, validation_status, sbti_validated,
            framework_compliant, validation_issues,
            scope3_coverage_pct, offset_reliance_pct,
            assessment_date, created_at, updated_at
        ) VALUES (
            $1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,
            $17,$18,$19,$20,$21,$22,$23,$24,$25,$26,$27
        )
        ON CONFLICT (assessment_id) DO UPDATE SET
            temperature_score_c        = EXCLUDED.temperature_score_c,
            temperature_classification = EXCLUDED.temperature_classification,
            validation_status          = EXCLUDED.validation_status,
            updated_at                 = EXCLUDED.updated_at
    """
    async with pool.acquire() as conn:
        await conn.execute(
            sql,
            data["assessment_id"],
            data["entity_id"],
            data.get("entity_name"),
            data["entity_type"],
            data["framework"],
            data["base_year"],
            data["base_year_emissions_tco2e"],
            data["scope1_tco2e"],
            data["scope2_tco2e"],
            data["scope3_tco2e"],
            data["near_term_target_year"],
            data["near_term_reduction_pct"],
            data["long_term_reduction_pct"],
            data["net_zero_target_year"],
            data["sbti_pathway"],
            data["temperature_score_c"],
            data["temperature_classification"],
            data["pathway_gap_pct"],
            data["validation_status"],
            data["sbti_validated"],
            data["framework_compliant"],
            json.dumps(data.get("validation_issues", [])),
            data["scope3_coverage_pct"],
            data["offset_reliance_pct"],
            data["assessment_date"],
            data["created_at"],
            data["updated_at"],
        )


async def _save_pathway_records(pool, records: list) -> None:
    """Persist pathway records to net_zero_pathway_records table."""
    if not records:
        return
    async with pool.acquire() as conn:
        for rec in records:
            await conn.execute(
                """
                INSERT INTO net_zero_pathway_records (
                    record_id, assessment_id, entity_id, year,
                    required_reduction_pct, required_emissions_tco2e,
                    projected_emissions_tco2e, gap_tco2e, on_track,
                    offset_used_tco2e, abatement_cost_usd_per_tco2e, created_at
                ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
                ON CONFLICT (record_id) DO NOTHING
                """,
                rec["record_id"],
                rec["assessment_id"],
                rec["entity_id"],
                rec["year"],
                rec["required_reduction_pct"],
                rec["required_emissions_tco2e"],
                rec["projected_emissions_tco2e"],
                rec["gap_tco2e"],
                rec["on_track"],
                rec["offset_used_tco2e"],
                rec["abatement_cost_usd_per_tco2e"],
                rec["created_at"],
            )


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/assess")
async def run_full_assessment(body: NetZeroAssessRequest, request: Request):
    """Run a full net zero target assessment and generate pathway records."""
    try:
        result = _engine.run_full_assessment(
            entity_id=body.entity_id,
            entity_type=body.entity_type,
            framework=body.framework,
            entity_name=body.entity_name,
            base_year=body.base_year,
            base_year_emissions=body.base_year_emissions,
            scope1_tco2e=body.scope1_tco2e,
            scope2_tco2e=body.scope2_tco2e,
            scope3_tco2e=body.scope3_tco2e,
            net_zero_target_year=body.net_zero_target_year,
            near_term_target_year=body.near_term_target_year,
            near_term_reduction_pct=body.near_term_reduction_pct,
            long_term_reduction_pct=body.long_term_reduction_pct,
            reporting_period=body.reporting_period,
        )
    except Exception as exc:
        logger.exception("Net zero assessment failed for %s", body.entity_id)
        raise HTTPException(status_code=500, detail=str(exc))

    pool = getattr(getattr(request.app, "state", None), "db_pool", None)
    if pool:
        try:
            await _save_assessment(pool, result)
            await _save_pathway_records(pool, result.get("pathway_records", []))
        except Exception as exc:
            logger.warning("Could not persist net zero assessment: %s", exc)

    return result


@router.post("/temperature-score")
async def calculate_temperature_score(body: TemperatureScoreRequest, request: Request):
    """Calculate implied temperature score for given GHG profile and targets."""
    try:
        result = _engine.calculate_temperature_score(
            entity_id=body.entity_id,
            scope1=body.scope1,
            scope2=body.scope2,
            scope3=body.scope3,
            reduction_targets=body.reduction_targets or {},
        )
    except Exception as exc:
        logger.exception("Temperature score calculation failed for %s", body.entity_id)
        raise HTTPException(status_code=500, detail=str(exc))
    return result


@router.get("/assessments/{entity_id}")
async def list_assessments(entity_id: str, request: Request):
    """List all net zero assessments for an entity."""
    pool = getattr(getattr(request.app, "state", None), "db_pool", None)
    if not pool:
        raise HTTPException(status_code=503, detail="Database unavailable")
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT assessment_id, entity_id, entity_name, entity_type,
                       framework, near_term_reduction_pct, temperature_score_c,
                       temperature_classification, sbti_pathway, validation_status,
                       net_zero_target_year, created_at
                FROM net_zero_target_assessments
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
    """Retrieve a single assessment with its pathway records."""
    pool = getattr(getattr(request.app, "state", None), "db_pool", None)
    if not pool:
        raise HTTPException(status_code=503, detail="Database unavailable")
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM net_zero_target_assessments WHERE assessment_id = $1",
                assessment_id,
            )
            if not row:
                raise HTTPException(status_code=404, detail="Assessment not found")
            pathway = await conn.fetch(
                "SELECT * FROM net_zero_pathway_records WHERE assessment_id = $1 ORDER BY year",
                assessment_id,
            )
        result = dict(row)
        result["pathway_records"] = [dict(r) for r in pathway]
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("DB read failed: %s", exc)
        raise HTTPException(status_code=503, detail="Database read failed")


@router.get("/ref/frameworks")
async def get_frameworks():
    """Return framework configurations (SBTi, NZBA, NZAMI, NZAOA)."""
    return {"frameworks": FRAMEWORK_CONFIGS}


@router.get("/ref/pathways")
async def get_pathways():
    """Return SBTi pathway criteria (1.5°C / WB2°C / 2°C)."""
    return {"pathways": SBTI_PATHWAYS}


@router.get("/ref/sector-pathways")
async def get_sector_pathways():
    """Return sector-specific decarbonisation trajectories."""
    return {"sector_pathways": SECTOR_PATHWAYS}
