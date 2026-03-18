"""
API Routes: Water Risk & Security (E53)
=======================================
POST /api/v1/water-risk/aqueduct-risk           — WRI Aqueduct 4.0 risk indicators
POST /api/v1/water-risk/cdp-water               — CDP Water Security grading
POST /api/v1/water-risk/esrs-e3                 — CSRD ESRS E3 disclosure assessment
POST /api/v1/water-risk/tnfd-water-dependency   — TNFD/ENCORE dependency rating
POST /api/v1/water-risk/water-footprint         — Blue/Green/Grey water footprint
POST /api/v1/water-risk/financial-impact        — Revenue-at-risk + compliance cost
POST /api/v1/water-risk/physical-risk-scenarios — RCP 2.6/4.5/8.5 projections
POST /api/v1/water-risk/materiality             — Aggregated water materiality score
GET  /api/v1/water-risk/ref/risk-tiers          — WRI Aqueduct tier descriptions
GET  /api/v1/water-risk/ref/cdp-methodology     — CDP Water scoring methodology
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from services.water_risk_engine import (
    WaterRiskEngine,
    AQUEDUCT_INDICATORS,
    RISK_TIER_BANDS,
    ENCORE_WATER_SERVICES,
)

router = APIRouter(
    prefix="/api/v1/water-risk",
    tags=["Water Risk"],
)

_engine = WaterRiskEngine()


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class AqueductRiskRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    entity_id: str
    country_code: str = Field(..., min_length=2, max_length=3)
    sector: str
    basin_name: Optional[str] = None


class CDPWaterRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    entity_id: str
    governance_score: float = Field(..., ge=0, le=100)
    risk_score: float = Field(..., ge=0, le=100)
    target_score: float = Field(..., ge=0, le=100)


class ESRSE3Request(BaseModel):
    model_config = ConfigDict(extra="allow")

    entity_id: str
    withdrawal_m3_pa: float = Field(..., ge=0)
    consumption_m3_pa: float = Field(..., ge=0)
    discharge_m3_pa: float = Field(..., ge=0)
    recycled_pct: float = Field(..., ge=0, le=100)


class TNFDWaterRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    entity_id: str
    sector: str
    value_chain_stage: str = Field("operations", description="upstream | operations | downstream")


class WaterFootprintRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    entity_id: str
    product_name: str
    annual_volume: float = Field(..., ge=0)
    sector: str


class FinancialImpactRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    entity_id: str
    water_stress_score: float = Field(..., ge=0, le=5)
    annual_revenue_usd: float = Field(..., ge=0)
    withdrawal_m3_pa: float = Field(..., ge=0)


class PhysicalRiskScenariosRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    entity_id: str
    country_code: str = Field(..., min_length=2, max_length=3)
    sector: str


class MaterialityRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    entity_id: str
    aqueduct_score: float = Field(..., ge=0, le=5, description="Raw Aqueduct 0-5 score")
    cdp_score: float = Field(..., ge=0, le=100)
    esrs_score: float = Field(..., ge=0, le=100)
    tnfd_score: float = Field(..., ge=0, le=100)


# ---------------------------------------------------------------------------
# POST Endpoints
# ---------------------------------------------------------------------------

@router.post("/aqueduct-risk")
def aqueduct_risk(req: AqueductRiskRequest) -> dict:
    """WRI Aqueduct 4.0 — 7 physical water risk indicators with weighted composite scoring."""
    return _engine.assess_aqueduct_risk(
        entity_id=req.entity_id,
        country_code=req.country_code,
        sector=req.sector,
        basin_name=req.basin_name,
    )


@router.post("/cdp-water")
def cdp_water(req: CDPWaterRequest) -> dict:
    """CDP Water Security questionnaire — weighted score, grade, and A-list eligibility."""
    return _engine.assess_cdp_water(
        entity_id=req.entity_id,
        governance_score=req.governance_score,
        risk_score=req.risk_score,
        target_score=req.target_score,
    )


@router.post("/esrs-e3")
def esrs_e3(req: ESRSE3Request) -> dict:
    """CSRD ESRS E3 mandatory water disclosure completeness and compliance assessment."""
    return _engine.assess_esrs_e3(
        entity_id=req.entity_id,
        withdrawal_m3_pa=req.withdrawal_m3_pa,
        consumption_m3_pa=req.consumption_m3_pa,
        discharge_m3_pa=req.discharge_m3_pa,
        recycled_pct=req.recycled_pct,
    )


@router.post("/tnfd-water-dependency")
def tnfd_water_dependency(req: TNFDWaterRequest) -> dict:
    """TNFD ENCORE-based water ecosystem dependency scoring by sector and value chain."""
    return _engine.assess_tnfd_water_dependency(
        entity_id=req.entity_id,
        sector=req.sector,
        value_chain_stage=req.value_chain_stage,
    )


@router.post("/water-footprint")
def water_footprint(req: WaterFootprintRequest) -> dict:
    """ISO 14046 water footprint: Blue, Green, Grey components with scarcity adjustment."""
    return _engine.calculate_water_footprint(
        entity_id=req.entity_id,
        product_name=req.product_name,
        annual_volume=req.annual_volume,
        sector=req.sector,
    )


@router.post("/financial-impact")
def financial_impact(req: FinancialImpactRequest) -> dict:
    """Water risk financial materiality: revenue-at-risk, compliance cost, capex, insurance."""
    return _engine.assess_financial_impact(
        entity_id=req.entity_id,
        water_stress_score=req.water_stress_score,
        annual_revenue_usd=req.annual_revenue_usd,
        withdrawal_m3_pa=req.withdrawal_m3_pa,
    )


@router.post("/physical-risk-scenarios")
def physical_risk_scenarios(req: PhysicalRiskScenariosRequest) -> dict:
    """IPCC AR6 RCP 2.6/4.5/8.5 physical water risk projections for 2030 and 2050."""
    return _engine.assess_physical_risk_scenarios(
        entity_id=req.entity_id,
        country_code=req.country_code,
        sector=req.sector,
    )


@router.post("/materiality")
def materiality(req: MaterialityRequest) -> dict:
    """Aggregated water materiality score across Aqueduct, CDP, ESRS E3, and TNFD."""
    return _engine.compute_overall_water_materiality(
        entity_id=req.entity_id,
        aqueduct_score=req.aqueduct_score,
        cdp_score=req.cdp_score,
        esrs_score=req.esrs_score,
        tnfd_score=req.tnfd_score,
    )


# ---------------------------------------------------------------------------
# GET Reference Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/risk-tiers")
def ref_risk_tiers() -> dict:
    """WRI Aqueduct 4.0 risk tier descriptions and score bands."""
    tiers = []
    for lo, hi, label in RISK_TIER_BANDS:
        tiers.append({
            "tier": label,
            "score_min": lo,
            "score_max": hi,
            "description": _tier_description(label),
            "recommended_action": _tier_action(label),
        })
    return {
        "scale": "0-5 (higher = greater water risk)",
        "tiers": tiers,
        "source": "WRI Aqueduct 4.0 (2023)",
        "indicators": AQUEDUCT_INDICATORS,
    }


@router.get("/ref/cdp-methodology")
def ref_cdp_methodology() -> dict:
    """CDP Water Security questionnaire scoring methodology and grade thresholds."""
    return {
        "scoring_weights": {
            "governance": 0.40,
            "risk_assessment": 0.30,
            "targets_and_actions": 0.30,
        },
        "grade_thresholds": [
            {"grade": "A",  "min_score": 90, "description": "Leadership — A-list eligible"},
            {"grade": "A-", "min_score": 80, "description": "Leadership — A-list eligible"},
            {"grade": "B+", "min_score": 70, "description": "Management"},
            {"grade": "B",  "min_score": 60, "description": "Management"},
            {"grade": "C",  "min_score": 50, "description": "Awareness"},
            {"grade": "D",  "min_score": 0,  "description": "Disclosure only"},
        ],
        "a_list_threshold": 80,
        "source": "CDP Water Security Questionnaire 2024",
        "disclosure_cycle": "Annual",
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tier_description(tier: str) -> str:
    descriptions = {
        "Low": "Water demand well within sustainable supply. Minimal competition.",
        "Low-Medium": "Some seasonal stress. Monitor for trend changes.",
        "Medium-High": "Noticeable stress; supply-demand competition emerging.",
        "High": "Significant stress; operational disruption risk. Mitigation needed.",
        "Extremely High": "Severe stress; business continuity risk. Immediate action required.",
    }
    return descriptions.get(tier, "")


def _tier_action(tier: str) -> str:
    actions = {
        "Low": "Maintain monitoring; report water data.",
        "Low-Medium": "Set water efficiency targets; engage local authorities.",
        "Medium-High": "Deploy water recycling; diversify sources; assess dependencies.",
        "High": "Implement resilience capex; supplier engagement; CDP disclosure.",
        "Extremely High": "Emergency response plan; potential relocation assessment; regulator engagement.",
    }
    return actions.get(tier, "")
