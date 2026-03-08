"""
IFRS 9 ECL Climate-Adjusted Routes
Endpoints for climate-adjusted expected credit loss calculation under IFRS 9.
Inline computation with DB persistence.
"""
import json
import logging
import math
from collections import defaultdict
from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from db.base import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["IFRS 9 ECL Climate"])


# --------------------------------------------------------------------------
# Pydantic request/response models (unchanged API contract)
# --------------------------------------------------------------------------
class ValidationSummary(BaseModel):
    is_valid: bool
    warnings: List[str] = []
    missing_fields: List[str] = []
    data_quality_score: float = Field(..., ge=0, le=1)


class ECLBaseInputs(BaseModel):
    exposure_id: str
    counterparty_id: Optional[str] = None
    sector: str
    country_iso: str
    exposure_at_default_gbp: float = Field(..., gt=0)
    base_pd_12m: float = Field(..., ge=0, le=1)
    base_pd_lifetime: float = Field(..., ge=0, le=1)
    lgd: float = Field(..., ge=0, le=1)
    maturity_years: int = Field(..., ge=1)
    current_stage: int = Field(..., ge=1, le=3)
    origination_pd: Optional[float] = Field(None, ge=0, le=1)


class ECLClimateInputs(BaseModel):
    physical_risk_score: Optional[float] = Field(None, ge=0, le=10)
    transition_risk_score: Optional[float] = Field(None, ge=0, le=10)
    carbon_intensity_tco2_revenue: Optional[float] = Field(None, ge=0)
    green_revenue_pct: Optional[float] = Field(None, ge=0, le=1)
    climate_scenario_weights: Optional[Dict[str, float]] = Field(
        None, description="Scenario name to probability weight mapping (must sum to 1.0)",
    )


class ECLCalculateRequest(BaseModel):
    base_inputs: ECLBaseInputs
    climate_inputs: ECLClimateInputs
    reporting_date: Optional[str] = Field(None, description="ISO date YYYY-MM-DD")


class ScenarioECLResult(BaseModel):
    scenario: str
    pd_12m_adjusted: float
    pd_lifetime_adjusted: float
    ecl_12m_gbp: float
    ecl_lifetime_gbp: float
    stage: int


class ECLCalculateResponse(BaseModel):
    assessment_id: Optional[str] = None
    exposure_id: str
    probability_weighted_ecl_12m_gbp: float
    probability_weighted_ecl_lifetime_gbp: float
    determined_stage: int
    sicr_triggered: bool
    sicr_triggers: List[str]
    climate_uplift_pct: float
    scenario_results: List[ScenarioECLResult]
    validation_summary: ValidationSummary


class PortfolioECLRequest(BaseModel):
    exposures: List[ECLCalculateRequest]
    reporting_date: Optional[str] = None


class SectorBreakdown(BaseModel):
    sector: str
    count: int
    total_ecl_gbp: float
    average_climate_uplift_pct: float


class StageDistribution(BaseModel):
    stage_1_count: int
    stage_2_count: int
    stage_3_count: int
    stage_1_ecl_gbp: float
    stage_2_ecl_gbp: float
    stage_3_ecl_gbp: float


class PortfolioECLResponse(BaseModel):
    assessment_id: Optional[str] = None
    total_exposures: int
    total_ead_gbp: float
    total_ecl_baseline_gbp: float
    total_ecl_climate_adjusted_gbp: float
    total_ecl_uplift_gbp: float
    total_ecl_uplift_pct: float
    stage_distribution: StageDistribution
    sector_breakdown: List[SectorBreakdown]
    validation_summary: ValidationSummary


class SICRExposure(BaseModel):
    exposure_id: str
    sector: str
    current_stage: int
    sicr_triggered: bool
    sicr_triggers: List[str]
    pd_increase_pct: Optional[float] = None
    recommended_action: str


class SICRScreeningRequest(BaseModel):
    exposures: List[ECLCalculateRequest]
    reporting_date: Optional[str] = None


class SICRScreeningResponse(BaseModel):
    total_screened: int
    sicr_count: int
    sicr_pct: float
    exposures: List[SICRExposure]
    validation_summary: ValidationSummary


# --------------------------------------------------------------------------
# GET response models
# --------------------------------------------------------------------------
class ECLAssessmentSummary(BaseModel):
    id: str
    entity_name: Optional[str] = None
    reporting_date: Optional[str] = None
    total_ead_gbp: Optional[float] = None
    total_ecl_gbp: Optional[float] = None
    climate_ecl_uplift_pct: Optional[float] = None
    status: Optional[str] = None
    created_at: Optional[str] = None


class ECLAssessmentDetail(BaseModel):
    id: str
    entity_name: Optional[str] = None
    reporting_date: Optional[str] = None
    total_ead_gbp: Optional[float] = None
    total_ecl_gbp: Optional[float] = None
    climate_ecl_uplift_pct: Optional[float] = None
    stage_distribution: Optional[Dict[str, Any]] = None
    sector_breakdown: Optional[Any] = None
    validation_summary: Optional[Any] = None
    status: Optional[str] = None
    created_at: Optional[str] = None
    exposures: List[Dict[str, Any]] = []
    scenario_results: List[Dict[str, Any]] = []


def _build_validation_summary(warnings: List[str], missing: List[str]) -> ValidationSummary:
    score = max(0.0, 1.0 - len(warnings) * 0.05 - len(missing) * 0.1)
    return ValidationSummary(
        is_valid=not missing, warnings=warnings,
        missing_fields=missing, data_quality_score=round(score, 3),
    )


# --------------------------------------------------------------------------
# Climate-adjusted ECL computation engine (inline)
# --------------------------------------------------------------------------
_DEFAULT_SCENARIO_WEIGHTS = {"baseline": 0.40, "adverse": 0.30, "severe": 0.30}
_SCENARIO_MULTIPLIERS = {"baseline": 1.0, "adverse": 1.5, "severe": 2.5}

_SECTOR_TRANSITION_SENSITIVITY = {
    "power_generation": 1.4, "oil_gas": 1.5, "coal_mining": 1.8,
    "cement": 1.3, "steel": 1.3, "shipping": 1.2, "aviation": 1.3,
    "agriculture": 1.1, "real_estate": 1.0, "financial_services": 0.8,
    "technology": 0.6, "healthcare": 0.5, "retail": 0.7,
}

# Scenario name mapping for DB CHECK constraint
_SCENARIO_DB_MAP = {
    "baseline": "BASE", "adverse": "ADVERSE", "severe": "SEVERE",
    "optimistic": "OPTIMISTIC", "base": "BASE",
}


def _climate_pd_uplift(climate: dict, sector: str = "unknown") -> float:
    """Aggregate PD uplift from climate risk factors."""
    phys = (climate.get("physical_risk_score") or 0) * 0.02
    trans = (climate.get("transition_risk_score") or 0) * 0.03
    sector_mult = _SECTOR_TRANSITION_SENSITIVITY.get(sector, 1.0)
    trans *= sector_mult
    carbon = min((climate.get("carbon_intensity_tco2_revenue") or 0) * 0.001, 0.05)
    green = (climate.get("green_revenue_pct") or 0) * -0.02
    return max(phys + trans + carbon + green, 0.0)


def _compute_single_exposure(base: dict, climate: dict) -> dict:
    """Run full IFRS 9 ECL with climate overlay for one exposure."""
    ead = base["exposure_at_default_gbp"]
    pd_12m = base["base_pd_12m"]
    pd_life = base["base_pd_lifetime"]
    lgd = base["lgd"]
    current_stage = base.get("current_stage", 1)
    origination_pd = base.get("origination_pd") or pd_12m
    sector = base.get("sector", "unknown")

    base_uplift = _climate_pd_uplift(climate, sector)
    weights = climate.get("climate_scenario_weights") or _DEFAULT_SCENARIO_WEIGHTS

    scenario_results: List[dict] = []
    sicr_triggered = False
    sicr_triggers: List[str] = []

    for scenario, weight in weights.items():
        mult = _SCENARIO_MULTIPLIERS.get(scenario, 1.0)
        uplift = base_uplift * mult

        adj_pd_12m = min(pd_12m * (1 + uplift), 0.9999)
        adj_pd_life = min(pd_life * (1 + uplift), 0.9999)

        ecl_12m = ead * adj_pd_12m * lgd
        ecl_life = ead * adj_pd_life * lgd

        stage = current_stage
        if current_stage == 1:
            pd_rel = (adj_pd_12m - origination_pd) / origination_pd if origination_pd > 0 else 0
            pd_abs = adj_pd_12m - origination_pd
            if pd_rel > 1.0:
                stage = 2
                if not sicr_triggered:
                    sicr_triggered = True
                    sicr_triggers.append(
                        f"PD relative increase {pd_rel:.0%} exceeds 100% threshold ({scenario})"
                    )
            elif pd_abs > 0.005:
                stage = 2
                if not sicr_triggered:
                    sicr_triggered = True
                    sicr_triggers.append(
                        f"PD absolute increase {pd_abs:.4f} exceeds 50bps ({scenario})"
                    )

        scenario_results.append({
            "scenario": scenario,
            "pd_12m_adjusted": round(adj_pd_12m, 6),
            "pd_lifetime_adjusted": round(adj_pd_life, 6),
            "ecl_12m_gbp": round(ecl_12m, 2),
            "ecl_lifetime_gbp": round(ecl_life, 2),
            "stage": stage,
        })

    pw_ecl_12m = sum(
        weights.get(sr["scenario"], 0) * sr["ecl_12m_gbp"] for sr in scenario_results
    )
    pw_ecl_life = sum(
        weights.get(sr["scenario"], 0) * sr["ecl_lifetime_gbp"] for sr in scenario_results
    )

    baseline_ecl_life = ead * pd_life * lgd
    climate_uplift_pct = (
        ((pw_ecl_life - baseline_ecl_life) / baseline_ecl_life * 100)
        if baseline_ecl_life > 0 else 0.0
    )
    determined_stage = max(sr["stage"] for sr in scenario_results)

    return {
        "exposure_id": base["exposure_id"],
        "ead": ead,
        "sector": sector,
        "pw_ecl_12m": round(pw_ecl_12m, 2),
        "pw_ecl_life": round(pw_ecl_life, 2),
        "baseline_ecl_life": round(baseline_ecl_life, 2),
        "determined_stage": determined_stage,
        "sicr_triggered": sicr_triggered,
        "sicr_triggers": sicr_triggers,
        "climate_uplift_pct": round(climate_uplift_pct, 2),
        "scenario_results": scenario_results,
    }


# --------------------------------------------------------------------------
# DB persistence helpers (non-blocking)
# --------------------------------------------------------------------------
def _persist_ecl_assessment(
    db: Session,
    entity_name: str,
    reporting_date_str: Optional[str],
    results: List[dict],
    requests: List[ECLCalculateRequest],
    stage_dist: dict,
    sector_breakdown_json: Any,
    validation_json: dict,
    portfolio_totals: Optional[dict] = None,
) -> Optional[str]:
    """Persist ECL assessment + exposures + scenario results. Returns assessment_id or None."""
    try:
        rd = date.fromisoformat(reporting_date_str) if reporting_date_str else date.today()

        if portfolio_totals:
            total_ead = portfolio_totals["total_ead"]
            total_ecl = portfolio_totals["total_ecl"]
            uplift_pct = portfolio_totals["uplift_pct"]
        else:
            total_ead = results[0]["ead"] if results else 0
            total_ecl = results[0]["pw_ecl_life"] if results else 0
            uplift_pct = results[0]["climate_uplift_pct"] if results else 0

        row = db.execute(text("""
            INSERT INTO ecl_assessments
                (entity_name, reporting_date, pd_model, lgd_model,
                 total_ead_gbp, total_ecl_gbp,
                 stage1_ecl_gbp, stage2_ecl_gbp, stage3_ecl_gbp,
                 stage1_ead_gbp, stage2_ead_gbp, stage3_ead_gbp,
                 climate_ecl_uplift_pct, sector_breakdown,
                 validation_summary, status)
            VALUES
                (:entity_name, :rd, 'point_in_time', 'supervisory_lgd',
                 :total_ead, :total_ecl,
                 :s1_ecl, :s2_ecl, :s3_ecl,
                 :s1_ead, :s2_ead, :s3_ead,
                 :uplift_pct, :sector_bk,
                 :val_summary, 'draft')
            RETURNING id
        """), {
            "entity_name": entity_name,
            "rd": rd,
            "total_ead": total_ead,
            "total_ecl": total_ecl,
            "s1_ecl": stage_dist.get("stage_1_ecl_gbp", 0),
            "s2_ecl": stage_dist.get("stage_2_ecl_gbp", 0),
            "s3_ecl": stage_dist.get("stage_3_ecl_gbp", 0),
            "s1_ead": 0, "s2_ead": 0, "s3_ead": 0,
            "uplift_pct": uplift_pct,
            "sector_bk": json.dumps(sector_breakdown_json) if sector_breakdown_json else None,
            "val_summary": json.dumps(validation_json),
        })
        assessment_id = str(row.fetchone()[0])

        # Insert exposures
        for r, req in zip(results, requests):
            climate = req.climate_inputs
            base = req.base_inputs
            first_adj_pd = r["scenario_results"][0]["pd_12m_adjusted"] if r["scenario_results"] else base.base_pd_12m
            db.execute(text("""
                INSERT INTO ecl_exposures
                    (assessment_id, instrument_id, sector_gics, country_iso,
                     instrument_type, pd_12m, pd_lifetime, pd_climate_adjusted,
                     lgd_downturn, ead, ecl_12m, ecl_lifetime, ecl_recognised,
                     ifrs9_stage,
                     physical_risk_score, transition_risk_score,
                     climate_pd_uplift_bps, scenario_cashflows)
                VALUES
                    (:aid, :iid, :sector, :country,
                     'corporate_loan', :pd12, :pdlt, :pdcl,
                     :lgd, :ead, :ecl12, :ecllt, :ecl_rec,
                     :stage,
                     :phys, :trans, :uplift_bps, CAST(:cashflows AS jsonb))
            """), {
                "aid": assessment_id,
                "iid": base.exposure_id,
                "sector": base.sector,
                "country": base.country_iso,
                "pd12": base.base_pd_12m,
                "pdlt": base.base_pd_lifetime,
                "pdcl": first_adj_pd,
                "lgd": base.lgd,
                "ead": r["ead"],
                "ecl12": r["pw_ecl_12m"],
                "ecllt": r["pw_ecl_life"],
                "ecl_rec": r["pw_ecl_life"] if r["determined_stage"] >= 2 else r["pw_ecl_12m"],
                "stage": r["determined_stage"],
                "phys": climate.physical_risk_score,
                "trans": climate.transition_risk_score,
                "uplift_bps": r["climate_uplift_pct"] * 100,
                "cashflows": json.dumps(r["scenario_results"]),
            })

        # Insert scenario results (aggregate level — use first exposure's scenarios for single, or aggregate for portfolio)
        weights = _DEFAULT_SCENARIO_WEIGHTS
        if results:
            for sr in results[0]["scenario_results"]:
                db_name = _SCENARIO_DB_MAP.get(sr["scenario"].lower(), sr["scenario"].upper())
                db.execute(text("""
                    INSERT INTO ecl_scenario_results
                        (assessment_id, scenario_name, scenario_weight, total_ecl_gbp)
                    VALUES (:aid, :name, :weight, :ecl)
                """), {
                    "aid": assessment_id,
                    "name": db_name,
                    "weight": weights.get(sr["scenario"], 0.33),
                    "ecl": sr["ecl_lifetime_gbp"],
                })

        db.commit()
        logger.info("ECL assessment persisted: id=%s exposures=%d", assessment_id, len(results))
        return assessment_id
    except Exception as db_err:
        db.rollback()
        logger.warning("ECL DB persist failed (non-blocking): %s", db_err)
        return None


# --------------------------------------------------------------------------
# POST Route handlers
# --------------------------------------------------------------------------
@router.post("/ecl/calculate", response_model=ECLCalculateResponse)
def calculate_ecl(request: ECLCalculateRequest, db: Session = Depends(get_db)):
    """Calculate climate-adjusted ECL for a single exposure under IFRS 9."""
    logger.info("ECL calculation: exposure=%s sector=%s",
                request.base_inputs.exposure_id, request.base_inputs.sector)
    try:
        warnings: List[str] = []
        base = request.base_inputs.model_dump()
        climate = request.climate_inputs.model_dump()

        if not climate.get("physical_risk_score") and not climate.get("transition_risk_score"):
            warnings.append("No climate risk scores provided; ECL will equal baseline.")

        r = _compute_single_exposure(base, climate)
        val = _build_validation_summary(warnings, [])

        # Persist to DB (non-blocking)
        stage_dist = {
            "stage_1_ecl_gbp": r["pw_ecl_life"] if r["determined_stage"] == 1 else 0,
            "stage_2_ecl_gbp": r["pw_ecl_life"] if r["determined_stage"] == 2 else 0,
            "stage_3_ecl_gbp": r["pw_ecl_life"] if r["determined_stage"] == 3 else 0,
        }
        assessment_id = _persist_ecl_assessment(
            db, entity_name=request.base_inputs.exposure_id,
            reporting_date_str=request.reporting_date,
            results=[r], requests=[request],
            stage_dist=stage_dist, sector_breakdown_json=None,
            validation_json=val.model_dump(),
        )

        return ECLCalculateResponse(
            assessment_id=assessment_id,
            exposure_id=r["exposure_id"],
            probability_weighted_ecl_12m_gbp=r["pw_ecl_12m"],
            probability_weighted_ecl_lifetime_gbp=r["pw_ecl_life"],
            determined_stage=r["determined_stage"],
            sicr_triggered=r["sicr_triggered"],
            sicr_triggers=r["sicr_triggers"],
            climate_uplift_pct=r["climate_uplift_pct"],
            scenario_results=[ScenarioECLResult(**s) for s in r["scenario_results"]],
            validation_summary=val,
        )
    except Exception as exc:
        logger.exception("ECL engine error: exposure=%s", request.base_inputs.exposure_id)
        raise HTTPException(status_code=500, detail=f"ECL engine error: {exc}") from exc


@router.post("/ecl/portfolio", response_model=PortfolioECLResponse)
def calculate_portfolio_ecl(request: PortfolioECLRequest, db: Session = Depends(get_db)):
    """Portfolio-level climate-adjusted ECL with sector and stage breakdown."""
    logger.info("Portfolio ECL: %d exposures", len(request.exposures))
    if not request.exposures:
        raise HTTPException(status_code=400, detail="At least one exposure is required.")
    try:
        warnings: List[str] = []
        results = []
        for exp in request.exposures:
            base = exp.base_inputs.model_dump()
            climate = exp.climate_inputs.model_dump()
            results.append(_compute_single_exposure(base, climate))

        total_ead = sum(r["ead"] for r in results)
        total_ecl_baseline = sum(r["baseline_ecl_life"] for r in results)
        total_ecl_adjusted = sum(r["pw_ecl_life"] for r in results)
        total_uplift = total_ecl_adjusted - total_ecl_baseline
        total_uplift_pct = (total_uplift / total_ecl_baseline * 100) if total_ecl_baseline > 0 else 0.0

        stage_counts = {1: 0, 2: 0, 3: 0}
        stage_ecl = {1: 0.0, 2: 0.0, 3: 0.0}
        for r in results:
            s = r["determined_stage"]
            stage_counts[s] = stage_counts.get(s, 0) + 1
            stage_ecl[s] = stage_ecl.get(s, 0.0) + r["pw_ecl_life"]

        sector_data: Dict[str, dict] = defaultdict(lambda: {"count": 0, "ecl": 0.0, "uplift_sum": 0.0})
        for r in results:
            sec = r["sector"]
            sector_data[sec]["count"] += 1
            sector_data[sec]["ecl"] += r["pw_ecl_life"]
            sector_data[sec]["uplift_sum"] += r["climate_uplift_pct"]

        sector_breakdown = [
            SectorBreakdown(
                sector=sec, count=d["count"],
                total_ecl_gbp=round(d["ecl"], 2),
                average_climate_uplift_pct=round(d["uplift_sum"] / d["count"], 2),
            )
            for sec, d in sorted(sector_data.items(), key=lambda x: -x[1]["ecl"])
        ]

        val = _build_validation_summary(warnings, [])

        # Persist to DB (non-blocking)
        stage_dist = {
            "stage_1_ecl_gbp": round(stage_ecl[1], 2),
            "stage_2_ecl_gbp": round(stage_ecl[2], 2),
            "stage_3_ecl_gbp": round(stage_ecl[3], 2),
        }
        sector_bk_json = [
            {"sector": sb.sector, "count": sb.count, "ecl": sb.total_ecl_gbp, "uplift": sb.average_climate_uplift_pct}
            for sb in sector_breakdown
        ]
        assessment_id = _persist_ecl_assessment(
            db, entity_name=f"Portfolio ({len(results)} exposures)",
            reporting_date_str=request.reporting_date,
            results=results, requests=request.exposures,
            stage_dist=stage_dist, sector_breakdown_json=sector_bk_json,
            validation_json=val.model_dump(),
            portfolio_totals={
                "total_ead": round(total_ead, 2),
                "total_ecl": round(total_ecl_adjusted, 2),
                "uplift_pct": round(total_uplift_pct, 2),
            },
        )

        return PortfolioECLResponse(
            assessment_id=assessment_id,
            total_exposures=len(results),
            total_ead_gbp=round(total_ead, 2),
            total_ecl_baseline_gbp=round(total_ecl_baseline, 2),
            total_ecl_climate_adjusted_gbp=round(total_ecl_adjusted, 2),
            total_ecl_uplift_gbp=round(total_uplift, 2),
            total_ecl_uplift_pct=round(total_uplift_pct, 2),
            stage_distribution=StageDistribution(
                stage_1_count=stage_counts[1], stage_2_count=stage_counts[2], stage_3_count=stage_counts[3],
                stage_1_ecl_gbp=round(stage_ecl[1], 2), stage_2_ecl_gbp=round(stage_ecl[2], 2),
                stage_3_ecl_gbp=round(stage_ecl[3], 2),
            ),
            sector_breakdown=sector_breakdown,
            validation_summary=val,
        )
    except Exception as exc:
        logger.exception("Portfolio ECL engine error")
        raise HTTPException(status_code=500, detail=f"Portfolio ECL engine error: {exc}") from exc


@router.post("/ecl/sicr-screening", response_model=SICRScreeningResponse)
def screen_sicr(request: SICRScreeningRequest, db: Session = Depends(get_db)):
    """Screen a portfolio for Significant Increase in Credit Risk (SICR) triggers."""
    logger.info("SICR screening: %d exposures", len(request.exposures))
    if not request.exposures:
        raise HTTPException(status_code=400, detail="At least one exposure is required.")
    try:
        warnings: List[str] = []
        exposures_out: List[SICRExposure] = []

        for exp in request.exposures:
            base = exp.base_inputs.model_dump()
            climate = exp.climate_inputs.model_dump()
            r = _compute_single_exposure(base, climate)

            origination_pd = base.get("origination_pd") or base["base_pd_12m"]
            adj_pd = r["scenario_results"][0]["pd_12m_adjusted"] if r["scenario_results"] else base["base_pd_12m"]
            pd_increase_pct = (
                ((adj_pd - origination_pd) / origination_pd * 100)
                if origination_pd > 0 else 0.0
            )

            if r["sicr_triggered"]:
                action = "Move to Stage 2; increase provision; review within 30 days"
            elif pd_increase_pct > 50:
                action = "Monitor closely; add to watchlist"
            else:
                action = "No action required; maintain Stage 1"

            exposures_out.append(SICRExposure(
                exposure_id=r["exposure_id"],
                sector=r["sector"],
                current_stage=base.get("current_stage", 1),
                sicr_triggered=r["sicr_triggered"],
                sicr_triggers=r["sicr_triggers"],
                pd_increase_pct=round(pd_increase_pct, 2),
                recommended_action=action,
            ))

        total = len(exposures_out)
        sicr_count = sum(1 for e in exposures_out if e.sicr_triggered)
        val = _build_validation_summary(warnings, [])
        return SICRScreeningResponse(
            total_screened=total,
            sicr_count=sicr_count,
            sicr_pct=round(sicr_count / total * 100, 2) if total else 0.0,
            exposures=exposures_out,
            validation_summary=val,
        )
    except Exception as exc:
        logger.exception("SICR screening engine error")
        raise HTTPException(status_code=500, detail=f"SICR screening engine error: {exc}") from exc


# --------------------------------------------------------------------------
# GET Route handlers (read from DB)
# --------------------------------------------------------------------------
@router.get("/ecl/assessments")
def list_ecl_assessments(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
):
    """List ECL assessments with optional status filter."""
    try:
        where = "WHERE status = :status" if status else ""
        params: dict = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status

        rows = db.execute(text(f"""
            SELECT id, entity_name, reporting_date, total_ead_gbp, total_ecl_gbp,
                   climate_ecl_uplift_pct, status, created_at
            FROM ecl_assessments
            {where}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """), params).fetchall()

        count_row = db.execute(text(f"""
            SELECT COUNT(*) FROM ecl_assessments {where}
        """), params).fetchone()

        return {
            "total": count_row[0] if count_row else 0,
            "assessments": [
                {
                    "id": str(r[0]),
                    "entity_name": r[1],
                    "reporting_date": str(r[2]) if r[2] else None,
                    "total_ead_gbp": float(r[3]) if r[3] else None,
                    "total_ecl_gbp": float(r[4]) if r[4] else None,
                    "climate_ecl_uplift_pct": float(r[5]) if r[5] else None,
                    "status": r[6],
                    "created_at": str(r[7]) if r[7] else None,
                }
                for r in rows
            ],
        }
    except Exception as exc:
        logger.exception("Error listing ECL assessments")
        raise HTTPException(status_code=500, detail=f"DB error: {exc}") from exc


@router.get("/ecl/assessments/{assessment_id}")
def get_ecl_assessment(assessment_id: str, db: Session = Depends(get_db)):
    """Get full ECL assessment with exposures and scenario results."""
    try:
        a = db.execute(text("""
            SELECT id, entity_name, reporting_date, total_ead_gbp, total_ecl_gbp,
                   stage1_ecl_gbp, stage2_ecl_gbp, stage3_ecl_gbp,
                   climate_ecl_uplift_pct, sector_breakdown, validation_summary,
                   status, created_at
            FROM ecl_assessments WHERE id = :aid
        """), {"aid": assessment_id}).fetchone()

        if not a:
            raise HTTPException(status_code=404, detail="Assessment not found")

        exposures = db.execute(text("""
            SELECT id, instrument_id, sector_gics, country_iso, pd_12m, pd_lifetime,
                   pd_climate_adjusted, lgd_downturn, ead, ecl_12m, ecl_lifetime,
                   ifrs9_stage, physical_risk_score, transition_risk_score,
                   climate_pd_uplift_bps
            FROM ecl_exposures WHERE assessment_id = :aid
            ORDER BY ecl_lifetime DESC
        """), {"aid": assessment_id}).fetchall()

        scenarios = db.execute(text("""
            SELECT id, scenario_name, scenario_weight, total_ecl_gbp
            FROM ecl_scenario_results WHERE assessment_id = :aid
            ORDER BY scenario_weight DESC
        """), {"aid": assessment_id}).fetchall()

        return {
            "id": str(a[0]),
            "entity_name": a[1],
            "reporting_date": str(a[2]) if a[2] else None,
            "total_ead_gbp": float(a[3]) if a[3] else None,
            "total_ecl_gbp": float(a[4]) if a[4] else None,
            "stage_distribution": {
                "stage_1_ecl_gbp": float(a[5]) if a[5] else 0,
                "stage_2_ecl_gbp": float(a[6]) if a[6] else 0,
                "stage_3_ecl_gbp": float(a[7]) if a[7] else 0,
            },
            "climate_ecl_uplift_pct": float(a[8]) if a[8] else None,
            "sector_breakdown": a[9],
            "validation_summary": a[10],
            "status": a[11],
            "created_at": str(a[12]) if a[12] else None,
            "exposures": [
                {
                    "id": str(e[0]), "instrument_id": e[1], "sector": e[2],
                    "country_iso": e[3],
                    "pd_12m": float(e[4]) if e[4] else None,
                    "pd_lifetime": float(e[5]) if e[5] else None,
                    "pd_climate_adjusted": float(e[6]) if e[6] else None,
                    "lgd": float(e[7]) if e[7] else None,
                    "ead": float(e[8]) if e[8] else None,
                    "ecl_12m": float(e[9]) if e[9] else None,
                    "ecl_lifetime": float(e[10]) if e[10] else None,
                    "ifrs9_stage": e[11],
                    "physical_risk_score": float(e[12]) if e[12] else None,
                    "transition_risk_score": float(e[13]) if e[13] else None,
                    "climate_pd_uplift_bps": float(e[14]) if e[14] else None,
                }
                for e in exposures
            ],
            "scenario_results": [
                {
                    "id": str(s[0]), "scenario_name": s[1],
                    "scenario_weight": float(s[2]) if s[2] else None,
                    "total_ecl_gbp": float(s[3]) if s[3] else None,
                }
                for s in scenarios
            ],
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error fetching ECL assessment %s", assessment_id)
        raise HTTPException(status_code=500, detail=f"DB error: {exc}") from exc
