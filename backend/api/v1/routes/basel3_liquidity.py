"""
API Routes: Basel III Liquidity Risk Engine — E36
==================================================
POST /api/v1/basel3-liquidity/lcr                  — LCR assessment (legacy)
POST /api/v1/basel3-liquidity/lcr-assessment        — LCR assessment (spec alias)
POST /api/v1/basel3-liquidity/nsfr                 — NSFR assessment (legacy)
POST /api/v1/basel3-liquidity/nsfr-assessment       — NSFR assessment (spec alias)
POST /api/v1/basel3-liquidity/alm-gap              — ALM gap & IRRBB analysis (legacy)
POST /api/v1/basel3-liquidity/irrbb-assessment      — IRRBB assessment (spec alias)
POST /api/v1/basel3-liquidity/liquidity-stress      — Liquidity stress test (legacy)
POST /api/v1/basel3-liquidity/stress-test           — Liquidity stress test (spec alias)
POST /api/v1/basel3-liquidity/full-assessment       — Full Basel III liquidity assessment
GET  /api/v1/basel3-liquidity/ref/hqla-factors      — HQLA haircut schedule (legacy)
GET  /api/v1/basel3-liquidity/ref/hqla-haircuts     — HQLA haircut schedule (spec alias)
GET  /api/v1/basel3-liquidity/ref/runoff-rates      — LCR outflow runoff rates (legacy)
GET  /api/v1/basel3-liquidity/ref/outflow-rates     — Outflow rates (spec alias)
GET  /api/v1/basel3-liquidity/ref/monitoring-tools  — BCBS 238 monitoring tools
GET  /api/v1/basel3-liquidity/ref/rate-shocks       — EBA IRRBB rate shock scenarios
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from services.basel3_liquidity_engine import Basel3LiquidityEngine, EBA_RATE_SHOCKS, HQLA_HAIRCUTS, RUNOFF_RATES

router = APIRouter(prefix="/api/v1/basel3-liquidity", tags=["Basel III Liquidity — E36"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class LCRRequest(BaseModel):
    entity_id: str
    hqla_l1: float = Field(1000.0, ge=0, description="Level 1 HQLA assets (EUR mn)")
    hqla_l2a: float = Field(300.0, ge=0, description="Level 2A HQLA assets (EUR mn)")
    hqla_l2b: float = Field(100.0, ge=0, description="Level 2B HQLA assets (EUR mn)")
    gross_outflow: float = Field(1200.0, ge=0, description="Gross cash outflows over 30 days (EUR mn)")
    gross_inflow: float = Field(500.0, ge=0, description="Gross cash inflows over 30 days (EUR mn)")
    climate_scenario: Optional[str] = None


class NSFRRequest(BaseModel):
    entity_id: str
    asf_breakdown: dict = Field(default_factory=dict, description="ASF component amounts (EUR mn) keyed by ASF factor name")
    rsf_breakdown: dict = Field(default_factory=dict, description="RSF component amounts (EUR mn) keyed by RSF factor name")


class TimeBucketItem(BaseModel):
    bucket: str = Field(..., description="Time bucket label (e.g. overnight, 1m, 3m, 1y, 5y)")
    assets_mn: float = Field(0.0, ge=0)
    liabilities_mn: float = Field(0.0, ge=0)


class ALMGapRequest(BaseModel):
    entity_id: str
    time_buckets: list[TimeBucketItem] = Field(default_factory=list)


class LiquidityStressRequest(BaseModel):
    entity_id: str
    base_lcr: float = Field(120.0, ge=0)
    base_nsfr: float = Field(110.0, ge=0)
    scenario_id: str = "mild_idiosyncratic"


class FullAssessmentRequest(BaseModel):
    entity_id: str
    entity_name: str
    reporting_date: str
    scenario_id: str = "mild_idiosyncratic"
    hqla_l1: float = Field(1000.0, ge=0)
    hqla_l2a: float = Field(300.0, ge=0)
    hqla_l2b: float = Field(100.0, ge=0)
    gross_outflow: float = Field(1200.0, ge=0)
    gross_inflow: float = Field(500.0, ge=0)
    climate_scenario: Optional[str] = None
    asf_breakdown: Optional[dict] = None
    rsf_breakdown: Optional[dict] = None
    time_buckets: Optional[list[TimeBucketItem]] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/lcr")
def assess_lcr(req: LCRRequest):
    """Compute LCR with optional climate HQLA haircut overlay."""
    try:
        engine = Basel3LiquidityEngine()
        r = engine.assess_lcr(
            entity_id=req.entity_id,
            hqla_l1=req.hqla_l1,
            hqla_l2a=req.hqla_l2a,
            hqla_l2b=req.hqla_l2b,
            gross_outflow=req.gross_outflow,
            gross_inflow=req.gross_inflow,
            climate_scenario=req.climate_scenario,
        )
        return {
            "entity_id": r.entity_id,
            "assessment_date": r.assessment_date,
            "hqla_l1_mn": r.hqla_l1_mn,
            "hqla_l2a_mn": r.hqla_l2a_mn,
            "hqla_l2b_mn": r.hqla_l2b_mn,
            "hqla_stock_mn": r.hqla_stock_mn,
            "gross_outflow_30d_mn": r.gross_outflow_30d_mn,
            "gross_inflow_30d_mn": r.gross_inflow_30d_mn,
            "net_outflow_30d_mn": r.net_outflow_30d_mn,
            "lcr_pct": r.lcr_pct,
            "climate_scenario": r.climate_scenario,
            "climate_hqla_haircut_bps": r.climate_hqla_haircut_bps,
            "climate_adjusted_lcr_pct": r.climate_adjusted_lcr_pct,
            "lcr_breach": r.lcr_breach,
            "l2_cap_breach": r.l2_cap_breach,
            "l2b_cap_breach": r.l2b_cap_breach,
            "notes": r.notes,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/nsfr")
def assess_nsfr(req: NSFRRequest):
    """Compute NSFR from Available and Required Stable Funding breakdowns."""
    try:
        engine = Basel3LiquidityEngine()
        r = engine.assess_nsfr(
            entity_id=req.entity_id,
            asf_breakdown=req.asf_breakdown,
            rsf_breakdown=req.rsf_breakdown,
        )
        return {
            "entity_id": r.entity_id,
            "assessment_date": r.assessment_date,
            "asf_mn": r.asf_mn,
            "rsf_mn": r.rsf_mn,
            "nsfr_pct": r.nsfr_pct,
            "nsfr_breach": r.nsfr_breach,
            "asf_breakdown": r.asf_breakdown,
            "rsf_breakdown": r.rsf_breakdown,
            "notes": r.notes,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/alm-gap")
def assess_alm_gap(req: ALMGapRequest):
    """ALM maturity gap analysis and IRRBB EVE/NII sensitivity (EBA rate shocks)."""
    try:
        engine = Basel3LiquidityEngine()
        buckets = [b.dict() for b in req.time_buckets]
        r = engine.assess_alm_gap(
            entity_id=req.entity_id,
            time_buckets=buckets,
        )
        return {
            "entity_id": r.entity_id,
            "assessment_date": r.assessment_date,
            "bucket_gaps": r.bucket_gaps,
            "cumulative_gap_mn": r.cumulative_gap_mn,
            "duration_gap_years": r.duration_gap_years,
            "eve_parallel_up_mn": r.eve_parallel_up_mn,
            "eve_parallel_down_mn": r.eve_parallel_down_mn,
            "eve_steepener_mn": r.eve_steepener_mn,
            "eve_flattener_mn": r.eve_flattener_mn,
            "eve_short_up_mn": r.eve_short_up_mn,
            "eve_short_down_mn": r.eve_short_down_mn,
            "nii_12m_sensitivity_mn": r.nii_12m_sensitivity_mn,
            "irrbb_material": r.irrbb_material,
            "notes": r.notes,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/liquidity-stress")
def run_liquidity_stress(req: LiquidityStressRequest):
    """Liquidity stress test — survival horizon, stressed LCR/NSFR, liquidity at risk."""
    try:
        engine = Basel3LiquidityEngine()
        r = engine.run_liquidity_stress(
            entity_id=req.entity_id,
            base_lcr=req.base_lcr,
            base_nsfr=req.base_nsfr,
            scenario_id=req.scenario_id,
        )
        return {
            "entity_id": r.entity_id,
            "assessment_date": r.assessment_date,
            "scenario_id": r.scenario_id,
            "survival_horizon_days": r.survival_horizon_days,
            "liquidity_at_risk_mn": r.liquidity_at_risk_mn,
            "stress_outflow_deposit_mn": r.stress_outflow_deposit_mn,
            "stress_outflow_wholesale_mn": r.stress_outflow_wholesale_mn,
            "stressed_lcr_pct": r.stressed_lcr_pct,
            "stressed_nsfr_pct": r.stressed_nsfr_pct,
            "liquidity_buffer_adequacy": r.liquidity_buffer_adequacy,
            "notes": r.notes,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/full-assessment")
def full_assessment(req: FullAssessmentRequest):
    """Full Basel III liquidity risk assessment (LCR + NSFR + ALM/IRRBB + stress)."""
    try:
        engine = Basel3LiquidityEngine()
        buckets = [b.dict() for b in req.time_buckets] if req.time_buckets else None
        result = engine.full_assessment(
            entity_id=req.entity_id,
            entity_name=req.entity_name,
            reporting_date=req.reporting_date,
            scenario_id=req.scenario_id,
            hqla_l1=req.hqla_l1,
            hqla_l2a=req.hqla_l2a,
            hqla_l2b=req.hqla_l2b,
            gross_outflow=req.gross_outflow,
            gross_inflow=req.gross_inflow,
            climate_scenario=req.climate_scenario,
            asf_breakdown=req.asf_breakdown,
            rsf_breakdown=req.rsf_breakdown,
            time_buckets=buckets,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Reference Data Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/hqla-factors")
def ref_hqla_factors():
    """HQLA Level 1/2A/2B haircut schedule per CRR2 / LCR DA."""
    return {"hqla_haircuts": Basel3LiquidityEngine.get_hqla_factors()}


# Spec alias: /ref/hqla-haircuts
@router.get("/ref/hqla-haircuts")
def ref_hqla_haircuts():
    """HQLA haircut schedule — CRR2 Art 416 / BCBS 238 (spec alias for /ref/hqla-factors)."""
    return {"hqla_haircuts": HQLA_HAIRCUTS}


@router.get("/ref/runoff-rates")
def ref_runoff_rates():
    """LCR cash outflow runoff rates by deposit/funding category."""
    return {"runoff_rates": Basel3LiquidityEngine.get_runoff_rates()}


# Spec alias: /ref/outflow-rates
@router.get("/ref/outflow-rates")
def ref_outflow_rates():
    """LCR outflow rates — EBA 2024 stress assumptions (spec alias for /ref/runoff-rates)."""
    return {"outflow_rates": RUNOFF_RATES}


@router.get("/ref/monitoring-tools")
def ref_monitoring_tools():
    """BCBS 238 liquidity monitoring tools."""
    return {"bcbs238_monitoring_tools": Basel3LiquidityEngine.get_monitoring_tools()}


# Spec alias: /ref/rate-shocks
@router.get("/ref/rate-shocks")
def ref_rate_shocks():
    """EBA IRRBB rate shock scenarios in bps — EBA/GL/2018/02 / BCBS d368."""
    return {"rate_shocks_bps": EBA_RATE_SHOCKS}


# ---------------------------------------------------------------------------
# Spec-aliased POST endpoints
# ---------------------------------------------------------------------------

@router.post("/lcr-assessment")
def lcr_assessment(req: LCRRequest):
    """LCR assessment — spec alias for /lcr. CRR2 Art 412/416, BCBS 238."""
    return assess_lcr(req)


@router.post("/nsfr-assessment")
def nsfr_assessment(req: NSFRRequest):
    """NSFR assessment — spec alias for /nsfr. BCBS 295, CRR2 Art 428."""
    return assess_nsfr(req)


@router.post("/irrbb-assessment")
def irrbb_assessment(req: ALMGapRequest):
    """IRRBB/ALM gap assessment — spec alias for /alm-gap. EBA/GL/2018/02, BCBS d368."""
    return assess_alm_gap(req)


@router.post("/stress-test")
def stress_test(req: LiquidityStressRequest):
    """Liquidity stress test — spec alias for /liquidity-stress. EBA 2024 + NGFS climate overlay."""
    return run_liquidity_stress(req)
