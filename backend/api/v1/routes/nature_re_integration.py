"""
API Routes: Nature-RE Integration
===================================
POST /api/v1/nature-re/assess               — Nature-adjusted property valuation
POST /api/v1/nature-re/portfolio             — Portfolio nature-RE assessment
GET  /api/v1/nature-re/ref/haircut-table     — LEAP score → valuation haircut
GET  /api/v1/nature-re/ref/water-noi         — Water stress → NOI adjustment
GET  /api/v1/nature-re/ref/bio-cap-rate      — Biodiversity → cap rate bps
GET  /api/v1/nature-re/ref/bng-costs         — BNG habitat unit costs
GET  /api/v1/nature-re/ref/eu-tax-dnsh       — EU Taxonomy nature DNSH thresholds
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from services.nature_re_integration_engine import (
    NatureREIntegrationEngine, NatureREInput,
)

router = APIRouter(prefix="/api/v1/nature-re", tags=["Nature-RE Integration"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class NatureRERequest(BaseModel):
    property_id: str
    property_type: str = "office"
    market_value_eur: float = Field(0, ge=0)
    noi_eur: float = Field(0, ge=0)
    cap_rate_pct: float = Field(5.0, gt=0)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    leap_overall_score: float = Field(0, ge=0, le=5)
    leap_risk_rating: str = "low"
    water_baseline_score: float = Field(0, ge=0, le=5)
    water_projected_2030: float = Field(0, ge=0, le=5)
    water_projected_2050: float = Field(0, ge=0, le=5)
    biodiversity_impact_score: float = Field(0, ge=0, le=5)
    biodiversity_direct_overlaps: int = Field(0, ge=0)
    biodiversity_key_sites: list[str] = Field(default_factory=list)
    nature_key_risks: list[dict] = Field(default_factory=list)
    site_area_hectares: float = Field(0, ge=0)
    habitat_type: str = "default"
    bng_units_required: float = Field(0, ge=0)


class PortfolioNatureRERequest(BaseModel):
    portfolio_id: str
    properties: list[NatureRERequest]


# ---------------------------------------------------------------------------
# Converters
# ---------------------------------------------------------------------------

def _to_input(req: NatureRERequest) -> NatureREInput:
    return NatureREInput(
        property_id=req.property_id,
        property_type=req.property_type,
        market_value_eur=req.market_value_eur,
        noi_eur=req.noi_eur,
        cap_rate_pct=req.cap_rate_pct,
        latitude=req.latitude,
        longitude=req.longitude,
        leap_overall_score=req.leap_overall_score,
        leap_risk_rating=req.leap_risk_rating,
        water_baseline_score=req.water_baseline_score,
        water_projected_2030=req.water_projected_2030,
        water_projected_2050=req.water_projected_2050,
        biodiversity_impact_score=req.biodiversity_impact_score,
        biodiversity_direct_overlaps=req.biodiversity_direct_overlaps,
        biodiversity_key_sites=req.biodiversity_key_sites,
        nature_key_risks=req.nature_key_risks,
        site_area_hectares=req.site_area_hectares,
        habitat_type=req.habitat_type,
        bng_units_required=req.bng_units_required,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/assess")
def assess_nature_re(req: NatureRERequest):
    """Nature-adjusted property valuation (TNFD LEAP + water + biodiversity → RE value)."""
    engine = NatureREIntegrationEngine()
    r = engine.assess_nature_adjusted_valuation(_to_input(req))
    return {
        "property_id": r.property_id,
        "property_type": r.property_type,
        "market_value_eur": r.market_value_eur,
        "noi_eur": r.noi_eur,
        "cap_rate_pct": r.cap_rate_pct,
        "nature_haircut_pct": r.nature_haircut_pct,
        "water_noi_adjustment_pct": r.water_noi_adjustment_pct,
        "biodiversity_cap_rate_adj_bps": r.biodiversity_cap_rate_adj_bps,
        "bng_capex_estimate_eur": r.bng_capex_estimate_eur,
        "nature_adjusted_value_eur": r.nature_adjusted_value_eur,
        "nature_adjusted_noi_eur": r.nature_adjusted_noi_eur,
        "nature_adjusted_cap_rate_pct": r.nature_adjusted_cap_rate_pct,
        "total_nature_discount_pct": r.total_nature_discount_pct,
        "composite_nature_score": r.composite_nature_score,
        "composite_nature_band": r.composite_nature_band,
        "eu_taxonomy_nature_dnsh_pass": r.eu_taxonomy_nature_dnsh_pass,
        "eu_taxonomy_nature_flags": r.eu_taxonomy_nature_flags,
        "water_stress_band": r.water_stress_band,
        "water_stress_2030_band": r.water_stress_2030_band,
        "water_stress_2050_band": r.water_stress_2050_band,
        "nature_narrative": r.nature_narrative,
        "recommendations": r.recommendations,
    }


@router.post("/portfolio")
def assess_portfolio_nature_re(req: PortfolioNatureRERequest):
    """Portfolio-level nature-RE assessment."""
    engine = NatureREIntegrationEngine()
    props = [_to_input(p) for p in req.properties]
    r = engine.assess_portfolio(req.portfolio_id, props)
    return {
        "portfolio_id": r.portfolio_id,
        "total_properties": r.total_properties,
        "total_market_value_eur": r.total_market_value_eur,
        "total_nature_adjusted_value_eur": r.total_nature_adjusted_value_eur,
        "avg_nature_discount_pct": r.avg_nature_discount_pct,
        "avg_composite_nature_score": r.avg_composite_nature_score,
        "eu_taxonomy_dnsh_pass_count": r.eu_taxonomy_dnsh_pass_count,
        "eu_taxonomy_dnsh_fail_count": r.eu_taxonomy_dnsh_fail_count,
        "total_bng_capex_eur": r.total_bng_capex_eur,
        "nature_band_distribution": r.nature_band_distribution,
        "high_risk_properties": r.high_risk_properties,
        "property_results": r.property_results,
    }


# ---------------------------------------------------------------------------
# Reference Data Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/haircut-table")
def ref_nature_haircut():
    """TNFD LEAP overall score → valuation haircut % by property type."""
    return {"nature_haircut_table": NatureREIntegrationEngine.get_nature_haircut_table()}


@router.get("/ref/water-noi")
def ref_water_noi():
    """Water stress → NOI adjustment % by property type."""
    return {"water_noi_adjustments": NatureREIntegrationEngine.get_water_noi_adjustments()}


@router.get("/ref/bio-cap-rate")
def ref_bio_cap_rate():
    """Biodiversity impact score → cap rate adjustment (bps)."""
    return {"biodiversity_cap_rate_schedule": NatureREIntegrationEngine.get_biodiversity_cap_rate_schedule()}


@router.get("/ref/bng-costs")
def ref_bng_costs():
    """BNG habitat unit costs (DEFRA Metric 4.0)."""
    return {"bng_unit_costs": NatureREIntegrationEngine.get_bng_unit_costs()}


@router.get("/ref/eu-tax-dnsh")
def ref_eu_tax_dnsh():
    """EU Taxonomy nature-related DNSH thresholds."""
    return {"eu_taxonomy_nature_dnsh": NatureREIntegrationEngine.get_eu_taxonomy_nature_dnsh()}
