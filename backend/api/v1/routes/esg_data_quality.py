"""ESG Data Quality routes — prefix /api/v1/esg-data-quality (E34)"""

import logging
import json
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from services.esg_data_quality_engine import (
    ESGDataQualityEngine,
    ESG_PILLARS,
    DQS_LEVELS,
    ESTIMATION_METHODS,
    BCBS239_PRINCIPLES,
    MATERIAL_INDICATOR_SETS,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/esg-data-quality", tags=["ESG Data Quality"])

_engine = ESGDataQualityEngine()


# ── Pydantic models ───────────────────────────────────────────────────────────

class ESGReportRequest(BaseModel):
    entity_id: str
    entity_name: str
    reporting_period: str
    e_indicators: Optional[Dict[str, Any]] = None
    s_indicators: Optional[Dict[str, Any]] = None
    g_indicators: Optional[Dict[str, Any]] = None
    data_governance_inputs: Optional[Dict[str, Any]] = None


class ProviderDivergenceRequest(BaseModel):
    entity_id: str
    bloomberg_data: Optional[Dict[str, Any]] = None
    msci_data: Optional[Dict[str, Any]] = None
    sustainalytics_data: Optional[Dict[str, Any]] = None


class BCBS239Request(BaseModel):
    entity_id: str
    data_governance_inputs: Optional[Dict[str, Any]] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _save_report(pool, data: dict) -> None:
    """Persist ESG data quality report to esg_data_quality_reports table."""
    sql = """
        INSERT INTO esg_data_quality_reports (
            report_id, entity_id, entity_name, reporting_period,
            overall_esg_score, overall_coverage_pct,
            e_score, e_coverage_pct,
            s_score, s_coverage_pct,
            g_score, g_coverage_pct,
            overall_dqs, dqs_tier,
            bcbs239_score, bcbs239_tier,
            provider_divergence_score,
            total_indicators, reported_indicators, verified_indicators,
            improvement_priorities,
            created_at, updated_at
        ) VALUES (
            $1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,
            $15,$16,$17,$18,$19,$20,$21,$22,$23
        )
        ON CONFLICT (report_id) DO UPDATE SET
            overall_esg_score   = EXCLUDED.overall_esg_score,
            overall_coverage_pct= EXCLUDED.overall_coverage_pct,
            updated_at          = EXCLUDED.updated_at
    """
    async with pool.acquire() as conn:
        await conn.execute(
            sql,
            data["report_id"],
            data["entity_id"],
            data["entity_name"],
            data["reporting_period"],
            data["overall_esg_score"],
            data["overall_coverage_pct"],
            data["e_score"],
            data["e_coverage_pct"],
            data["s_score"],
            data["s_coverage_pct"],
            data["g_score"],
            data["g_coverage_pct"],
            data["overall_dqs"],
            data["dqs_tier"],
            data["bcbs239_score"],
            data["bcbs239_tier"],
            data["provider_divergence_score"],
            data["total_indicators"],
            data["reported_indicators"],
            data["verified_indicators"],
            json.dumps(data.get("improvement_priorities", [])),
            data["created_at"],
            data["updated_at"],
        )


async def _save_indicators(pool, report_id: str, indicators: list) -> None:
    """Persist per-indicator rows to esg_data_quality_indicators table."""
    if not indicators:
        return
    async with pool.acquire() as conn:
        for ind in indicators:
            await conn.execute(
                """
                INSERT INTO esg_data_quality_indicators (
                    report_id, pillar, indicator_id, indicator_name, unit,
                    reported, value_text, dqs_level, dqs_description,
                    estimation_method, verified, material
                ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
                ON CONFLICT (report_id, indicator_id) DO UPDATE SET
                    reported   = EXCLUDED.reported,
                    dqs_level  = EXCLUDED.dqs_level,
                    verified   = EXCLUDED.verified
                """,
                report_id,
                ind.get("pillar", "E"),
                ind["indicator_id"],
                ind["indicator_name"],
                ind.get("unit"),
                ind.get("reported", False),
                str(ind.get("value")) if ind.get("value") is not None else None,
                ind.get("dqs_level"),
                ind.get("dqs_description"),
                ind.get("estimation_method"),
                ind.get("verified", False),
                ind.get("material", False),
            )


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/report")
async def run_full_report(body: ESGReportRequest, request: Request):
    """Run a full ESG data quality and coverage report."""
    try:
        result = _engine.run_full_report(
            entity_id=body.entity_id,
            entity_name=body.entity_name,
            reporting_period=body.reporting_period,
            e_data=body.e_indicators,
            s_data=body.s_indicators,
            g_data=body.g_indicators,
            data_governance_inputs=body.data_governance_inputs,
        )
    except Exception as exc:
        logger.exception("ESG data quality report failed for %s", body.entity_id)
        raise HTTPException(status_code=500, detail=str(exc))

    pool = getattr(getattr(request.app, "state", None), "db_pool", None)
    if pool:
        try:
            await _save_report(pool, result)
            await _save_indicators(pool, result["report_id"], result.get("all_indicators", []))
        except Exception as exc:
            logger.warning("Could not persist ESG data quality report: %s", exc)

    return result


@router.post("/provider-divergence")
async def analyse_provider_divergence(body: ProviderDivergenceRequest, request: Request):
    """Analyse ESG score divergence across Bloomberg, MSCI, and Sustainalytics."""
    try:
        result = _engine.analyse_provider_divergence(
            entity_id=body.entity_id,
            bloomberg_data=body.bloomberg_data,
            msci_data=body.msci_data,
            sustainalytics_data=body.sustainalytics_data,
        )
    except Exception as exc:
        logger.exception("Provider divergence analysis failed for %s", body.entity_id)
        raise HTTPException(status_code=500, detail=str(exc))
    return result


@router.post("/bcbs239")
async def assess_bcbs239(body: BCBS239Request, request: Request):
    """Assess BCBS 239 data governance compliance across all 14 principles."""
    try:
        result = _engine.assess_bcbs239_compliance(
            entity_id=body.entity_id,
            data_governance_inputs=body.data_governance_inputs,
        )
    except Exception as exc:
        logger.exception("BCBS 239 assessment failed for %s", body.entity_id)
        raise HTTPException(status_code=500, detail=str(exc))
    return result


@router.get("/reports/{entity_id}")
async def list_reports(entity_id: str, request: Request):
    """List all ESG data quality reports for an entity."""
    pool = getattr(getattr(request.app, "state", None), "db_pool", None)
    if not pool:
        raise HTTPException(status_code=503, detail="Database unavailable")
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT report_id, entity_id, entity_name, reporting_period,
                       overall_esg_score, overall_coverage_pct,
                       overall_dqs, dqs_tier, bcbs239_score, bcbs239_tier,
                       created_at
                FROM esg_data_quality_reports
                WHERE entity_id = $1
                ORDER BY created_at DESC
                """,
                entity_id,
            )
        return [dict(r) for r in rows]
    except Exception as exc:
        logger.warning("DB read failed: %s", exc)
        raise HTTPException(status_code=503, detail="Database read failed")


@router.get("/report/{report_id}")
async def get_report(report_id: str, request: Request):
    """Retrieve a single ESG data quality report with all indicator rows."""
    pool = getattr(getattr(request.app, "state", None), "db_pool", None)
    if not pool:
        raise HTTPException(status_code=503, detail="Database unavailable")
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM esg_data_quality_reports WHERE report_id = $1",
                report_id,
            )
            if not row:
                raise HTTPException(status_code=404, detail="Report not found")
            indicators = await conn.fetch(
                "SELECT * FROM esg_data_quality_indicators WHERE report_id = $1 ORDER BY pillar, indicator_id",
                report_id,
            )
        result = dict(row)
        result["indicators"] = [dict(i) for i in indicators]
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("DB read failed: %s", exc)
        raise HTTPException(status_code=503, detail="Database read failed")


@router.get("/ref/indicators")
async def get_indicators():
    """Return the full E/S/G indicator catalog with all 75 indicators."""
    return {
        "pillars": ESG_PILLARS,
        "total_count": sum(len(v) for v in ESG_PILLARS.values()),
        "material_indicator_sets": MATERIAL_INDICATOR_SETS,
    }


@router.get("/ref/dqs-levels")
async def get_dqs_levels():
    """Return PCAF Data Quality Score level descriptions."""
    return {
        "dqs_levels": DQS_LEVELS,
        "estimation_methods": ESTIMATION_METHODS,
        "notes": "DQS 1 = best quality (third-party verified); DQS 5 = not available",
    }
