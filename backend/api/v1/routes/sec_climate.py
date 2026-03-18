"""
API Routes: SEC Climate Disclosure
====================================
POST /api/v1/sec-climate/filer-assessment         — Filer compliance assessment
POST /api/v1/sec-climate/ghg-disclosure            — GHG emissions disclosure review
POST /api/v1/sec-climate/financial-effects          — Reg S-X 14-02 financial effects
POST /api/v1/sec-climate/materiality                — Climate risk materiality assessment
GET  /api/v1/sec-climate/ref/filer-categories       — Filer category phase-in rules
GET  /api/v1/sec-climate/ref/reg-sk-items           — Reg S-K disclosure items
GET  /api/v1/sec-climate/ref/reg-sx-items           — Reg S-X financial effect items
GET  /api/v1/sec-climate/ref/attestation            — Attestation requirements
GET  /api/v1/sec-climate/ref/safe-harbor            — Safe harbor provisions
GET  /api/v1/sec-climate/ref/cross-framework        — SEC cross-framework mapping
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from services.sec_climate_engine import SECClimateEngine

router = APIRouter(prefix="/api/v1/sec-climate", tags=["SEC Climate Disclosure"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class FilerAssessmentRequest(BaseModel):
    registrant_name: str
    cik: str = ""
    filer_category: str = "large_accelerated_filer"
    fiscal_year: int = 2025
    governance_score: float = Field(0.0, ge=0, le=100)
    strategy_score: float = Field(0.0, ge=0, le=100)
    risk_management_score: float = Field(0.0, ge=0, le=100)
    targets_goals_score: float = Field(0.0, ge=0, le=100)
    ghg_emissions_score: float = Field(0.0, ge=0, le=100)
    financial_effects_score: float = Field(0.0, ge=0, le=100)
    has_limited_assurance: bool = False
    has_reasonable_assurance: bool = False


class GHGDisclosureRequest(BaseModel):
    registrant_name: str
    fiscal_year: int = 2025
    scope_1_total_co2e_mt: float = 0.0
    scope_1_by_gas: Optional[dict] = None
    scope_1_methodology: str = "GHG Protocol Corporate Standard"
    scope_2_location_co2e_mt: float = 0.0
    scope_2_market_co2e_mt: float = 0.0
    scope_2_methodology: str = "GHG Protocol Scope 2 Guidance"
    org_boundary: str = "operational_control"
    operational_boundary: str = "direct_emissions"
    consolidation_approach: str = "operational_control"
    prior_year_scope_1: float = 0.0
    prior_year_scope_2: float = 0.0
    intensity_metric: str = "revenue_usd_m"
    revenue_or_denominator: float = 0.0
    data_sources_documented: bool = False
    emission_factors_documented: bool = False
    methodology_changes_disclosed: bool = True
    third_party_verified: bool = False


class FinancialEffectsRequest(BaseModel):
    registrant_name: str
    fiscal_year: int = 2025
    pre_tax_income_usd: float = 0.0
    total_equity_usd: float = 0.0
    severe_weather_losses_usd: float = 0.0
    severe_weather_events: Optional[list] = None
    carbon_offset_expenses_usd: float = 0.0
    rec_expenses_usd: float = 0.0
    transition_capex_usd: float = 0.0
    other_transition_expenses_usd: float = 0.0
    transition_details: Optional[list] = None
    climate_impairments_usd: float = 0.0
    climate_contingencies_usd: float = 0.0
    estimate_details: Optional[list] = None


class RiskItem(BaseModel):
    risk: str
    description: str = ""
    time_horizon: str = "medium_term"
    likelihood: str = "possible"
    magnitude_usd: float = 0.0
    material: bool = False


class MaterialityRequest(BaseModel):
    registrant_name: str
    fiscal_year: int = 2025
    physical_risks: Optional[list[RiskItem]] = None
    transition_risks: Optional[list[RiskItem]] = None
    scenario_analysis_used: bool = False
    internal_carbon_price_usd_per_tco2e: Optional[float] = None
    strategy_resilience_assessment: str = ""


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/filer-assessment")
def filer_assessment(req: FilerAssessmentRequest):
    """SEC climate disclosure compliance assessment for a registrant."""
    engine = SECClimateEngine()
    r = engine.assess_filer(
        registrant_name=req.registrant_name,
        cik=req.cik,
        filer_category=req.filer_category,
        fiscal_year=req.fiscal_year,
        governance_score=req.governance_score,
        strategy_score=req.strategy_score,
        risk_management_score=req.risk_management_score,
        targets_goals_score=req.targets_goals_score,
        ghg_emissions_score=req.ghg_emissions_score,
        financial_effects_score=req.financial_effects_score,
        has_limited_assurance=req.has_limited_assurance,
        has_reasonable_assurance=req.has_reasonable_assurance,
    )
    return {
        "registrant_name": r.registrant_name,
        "cik": r.cik,
        "filer_category": r.filer_category,
        "fiscal_year": r.fiscal_year,
        "ghg_disclosure_required": r.ghg_disclosure_required,
        "ghg_disclosure_start_fy": r.ghg_disclosure_start_fy,
        "assurance_required": r.assurance_required,
        "assurance_level": r.assurance_level,
        "assurance_start_fy": r.assurance_start_fy,
        "financial_effects_required": r.financial_effects_required,
        "item_compliance": r.item_compliance,
        "overall_compliance_pct": r.overall_compliance_pct,
        "gaps": r.gaps,
        "critical_gaps": r.critical_gaps,
        "recommendations": r.recommendations,
        "safe_harbor_items": r.safe_harbor_items,
        "cross_framework_mapping": r.cross_framework_mapping,
        "attestation_status": r.attestation_status,
        "notes": r.notes,
    }


@router.post("/ghg-disclosure")
def ghg_disclosure(req: GHGDisclosureRequest):
    """GHG emissions disclosure assessment (Item 1505)."""
    engine = SECClimateEngine()
    r = engine.assess_ghg_disclosure(
        registrant_name=req.registrant_name,
        fiscal_year=req.fiscal_year,
        scope_1_total_co2e_mt=req.scope_1_total_co2e_mt,
        scope_1_by_gas=req.scope_1_by_gas,
        scope_1_methodology=req.scope_1_methodology,
        scope_2_location_co2e_mt=req.scope_2_location_co2e_mt,
        scope_2_market_co2e_mt=req.scope_2_market_co2e_mt,
        scope_2_methodology=req.scope_2_methodology,
        org_boundary=req.org_boundary,
        operational_boundary=req.operational_boundary,
        consolidation_approach=req.consolidation_approach,
        prior_year_scope_1=req.prior_year_scope_1,
        prior_year_scope_2=req.prior_year_scope_2,
        intensity_metric=req.intensity_metric,
        revenue_or_denominator=req.revenue_or_denominator,
        data_sources_documented=req.data_sources_documented,
        emission_factors_documented=req.emission_factors_documented,
        methodology_changes_disclosed=req.methodology_changes_disclosed,
        third_party_verified=req.third_party_verified,
    )
    return r.__dict__


@router.post("/financial-effects")
def financial_effects(req: FinancialEffectsRequest):
    """Reg S-X 14-02 financial statement effects of climate events."""
    engine = SECClimateEngine()
    r = engine.assess_financial_effects(
        registrant_name=req.registrant_name,
        fiscal_year=req.fiscal_year,
        pre_tax_income_usd=req.pre_tax_income_usd,
        total_equity_usd=req.total_equity_usd,
        severe_weather_losses_usd=req.severe_weather_losses_usd,
        severe_weather_events=req.severe_weather_events,
        carbon_offset_expenses_usd=req.carbon_offset_expenses_usd,
        rec_expenses_usd=req.rec_expenses_usd,
        transition_capex_usd=req.transition_capex_usd,
        other_transition_expenses_usd=req.other_transition_expenses_usd,
        transition_details=req.transition_details,
        climate_impairments_usd=req.climate_impairments_usd,
        climate_contingencies_usd=req.climate_contingencies_usd,
        estimate_details=req.estimate_details,
    )
    return r.__dict__


@router.post("/materiality")
def materiality_assessment(req: MaterialityRequest):
    """Climate risk materiality assessment (Items 1502-1503)."""
    engine = SECClimateEngine()
    phys = [r.model_dump() for r in req.physical_risks] if req.physical_risks else []
    trans = [r.model_dump() for r in req.transition_risks] if req.transition_risks else []
    r = engine.assess_materiality(
        registrant_name=req.registrant_name,
        fiscal_year=req.fiscal_year,
        physical_risks=phys,
        transition_risks=trans,
        scenario_analysis_used=req.scenario_analysis_used,
        internal_carbon_price_usd_per_tco2e=req.internal_carbon_price_usd_per_tco2e,
        strategy_resilience_assessment=req.strategy_resilience_assessment,
    )
    return r.__dict__


# ---------------------------------------------------------------------------
# Reference Data Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/filer-categories")
def ref_filer_categories():
    """SEC filer category definitions and phase-in schedules."""
    return {"filer_categories": SECClimateEngine.get_filer_categories()}


@router.get("/ref/reg-sk-items")
def ref_reg_sk():
    """Regulation S-K climate disclosure items (1501-1505)."""
    return {"reg_sk_items": SECClimateEngine.get_reg_sk_items()}


@router.get("/ref/reg-sx-items")
def ref_reg_sx():
    """Regulation S-X 14-02 financial statement effect items."""
    return {"reg_sx_items": SECClimateEngine.get_reg_sx_items()}


@router.get("/ref/attestation")
def ref_attestation():
    """GHG attestation requirements (limited & reasonable assurance)."""
    return {"attestation": SECClimateEngine.get_attestation_requirements()}


@router.get("/ref/safe-harbor")
def ref_safe_harbor():
    """PSLRA safe harbor applicability for climate disclosures."""
    return {"safe_harbor": SECClimateEngine.get_safe_harbor()}


@router.get("/ref/cross-framework")
def ref_cross_framework():
    """SEC climate rule cross-framework mapping (TCFD, ISSB, CSRD)."""
    return {"cross_framework": SECClimateEngine.get_cross_framework_map()}
