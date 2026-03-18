"""
API Routes — Climate Financial Statement Adjustments Engine (E86)
=================================================================
POST /api/v1/climate-financial-statements/assess              — full assessment
POST /api/v1/climate-financial-statements/ifrs-s2-effects     — IFRS S2 financial effects
POST /api/v1/climate-financial-statements/ias36-impairment    — IAS 36 climate impairment
POST /api/v1/climate-financial-statements/carbon-provisions   — carbon provisions (IAS 37)
POST /api/v1/climate-financial-statements/stranded-assets     — stranded asset assessment
POST /api/v1/climate-financial-statements/climate-financials  — climate-adjusted financials
GET  /api/v1/climate-financial-statements/ref/financial-effect-categories — IFRS S2 categories
GET  /api/v1/climate-financial-statements/ref/impairment-indicators       — IAS 36 indicators
GET  /api/v1/climate-financial-statements/ref/scenario-multipliers        — sector multipliers
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.climate_financial_statements_engine import (
    IFRS_S2_FINANCIAL_EFFECT_CATEGORIES,
    IAS36_CLIMATE_INDICATORS,
    CARBON_PROVISION_THRESHOLDS,
    STRANDED_ASSET_TRIGGERS,
    SCENARIO_FINANCIAL_MULTIPLIERS,
    ClimateFinancialStatementsEngine,
)

router = APIRouter(
    prefix="/api/v1/climate-financial-statements",
    tags=["E86 Climate Financial Statements"],
)

_engine = ClimateFinancialStatementsEngine()


# ---------------------------------------------------------------------------
# Pydantic request models
# ---------------------------------------------------------------------------


class FullAssessmentRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    sector: str = Field(default="industrials", description="Sector key, e.g. oil_gas, real_estate, utilities_fossil")
    revenue_m: float = Field(default=1_000.0, gt=0, description="Annual revenue €M")
    ebitda_m: float = Field(default=200.0, description="EBITDA €M")
    pat_m: float = Field(default=90.0, description="Profit after tax €M")
    total_assets_m: float = Field(default=2_000.0, gt=0, description="Total assets €M")
    ppe_m: Optional[float] = Field(default=None, description="PP&E carrying value €M")
    goodwill_m: Optional[float] = Field(default=None, description="Goodwill €M")
    intangibles_m: Optional[float] = Field(default=None, description="Intangibles €M")
    carbon_intensity_tco2_per_mrevenue: float = Field(default=80.0, ge=0, description="Carbon intensity tCO2 per €M revenue")
    annual_verified_emissions_kt: float = Field(default=250.0, ge=0, description="Annual verified ETS emissions kt CO2")
    free_allocation_kt: float = Field(default=200.0, ge=0, description="Free ETS allowances kt CO2")
    eua_spot_price_eur: float = Field(default=88.0, gt=0, description="EUA spot price €/t")
    carbon_tax_rate_eur_per_t: float = Field(default=0.0, ge=0, description="Applicable carbon tax rate €/t")
    voluntary_offset_price_usd: float = Field(default=18.0, ge=0, description="Voluntary carbon offset price USD/t")
    has_corsia_obligation: bool = Field(default=False)
    allowance_deficit_pct: float = Field(default=15.0, ge=0, description="ETS allowance deficit as % of verified emissions")
    asset_classes_held: list[str] = Field(
        default_factory=lambda: ["production_facilities", "real_estate"],
        description="Asset classes held by the entity",
    )
    asset_types_held: list[str] = Field(
        default_factory=list,
        description="Specific asset types for stranded asset matching",
    )
    disclosed_categories: list[str] = Field(
        default_factory=list,
        description="IFRS S2 categories already disclosed in reports",
    )
    scenario: str = Field(default="below_2c", description="Climate scenario for stranded asset test")
    climate_capex_annual_m: float = Field(default=0.0, ge=0, description="Annual climate CapEx €M")
    reserves_carrying_value_m: float = Field(default=0.0, ge=0, description="Fossil fuel reserves carrying value €M")


class IFRSS2EffectsRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    sector: str = Field(default="industrials")
    revenue_m: float = Field(default=1_000.0, gt=0)
    ebitda_m: float = Field(default=200.0)
    total_assets_m: float = Field(default=2_000.0, gt=0)
    carbon_intensity_tco2_per_mrevenue: float = Field(default=80.0, ge=0)
    eua_spot_price_eur: float = Field(default=88.0, gt=0)
    disclosed_categories: list[str] = Field(default_factory=list)


class IAS36ImpairmentRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    sector: str = Field(default="industrials")
    total_assets_m: float = Field(default=2_000.0, gt=0)
    ppe_m: Optional[float] = Field(default=None)
    goodwill_m: Optional[float] = Field(default=None)
    intangibles_m: Optional[float] = Field(default=None)
    asset_classes_held: list[str] = Field(
        default_factory=lambda: ["production_facilities", "real_estate"]
    )
    eua_price_eur: float = Field(default=88.0, gt=0)
    allowance_deficit_pct: float = Field(default=15.0, ge=0)


class CarbonProvisionsRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    sector: str = Field(default="industrials")
    annual_verified_emissions_kt: float = Field(default=250.0, ge=0)
    free_allocation_kt: float = Field(default=200.0, ge=0)
    eua_spot_price_eur: float = Field(default=88.0, gt=0)
    voluntary_offset_price_usd: float = Field(default=18.0, ge=0)
    carbon_tax_rate_eur_per_t: float = Field(default=0.0, ge=0)
    has_corsia_obligation: bool = Field(default=False)


class StrandedAssetsRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    sector: str = Field(default="oil_gas")
    total_assets_m: float = Field(default=2_000.0, gt=0)
    ppe_m: Optional[float] = Field(default=None)
    reserves_carrying_value_m: float = Field(default=0.0, ge=0)
    asset_types_held: list[str] = Field(default_factory=list)
    scenario: str = Field(
        default="below_2c",
        description="net_zero_2050 | below_2c | delayed_transition | current_policies",
    )


class ClimateFinancialsRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    sector: str = Field(default="industrials")
    revenue_m: float = Field(default=1_000.0, gt=0)
    ebitda_m: float = Field(default=200.0)
    pat_m: float = Field(default=90.0)
    carbon_provision_m: float = Field(default=0.0, ge=0)
    climate_capex_annual_m: float = Field(default=0.0, ge=0)


# ---------------------------------------------------------------------------
# Helper — build entity_data dict from request
# ---------------------------------------------------------------------------

def _req_to_entity(req: Any) -> dict:
    return req.model_dump()


# ---------------------------------------------------------------------------
# POST endpoints
# ---------------------------------------------------------------------------


@router.post("/assess")
async def full_assessment(req: FullAssessmentRequest):
    """
    Run the complete E86 Climate Financial Statement Adjustments assessment.

    Orchestrates IFRS S2 financial effects, IAS 36 climate impairment,
    IAS 37 carbon provisions, stranded asset write-down analysis and
    climate-adjusted P&L across 3 temperature scenarios (1.5°C / 2°C / 3°C).

    Returns consolidated scores: ifrs_s2_score, climate_financial_risk_score
    (0-100), materiality_tier, disclosure_completeness_pct, and financial
    quantum estimates for impairment, provisions and stranded asset write-downs.
    """
    try:
        entity_data = _req_to_entity(req)
        result = _engine.run_full_assessment(entity_data)
        return {"status": "success", "data": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/ifrs-s2-effects")
async def ifrs_s2_financial_effects(req: IFRSS2EffectsRequest):
    """
    Identify and quantify the 8 IFRS S2 financial effect categories
    (IFRS S2 paras 29-36).

    Returns category-level income statement and balance sheet impact estimates,
    disclosure completeness score (0-100) and gap list cross-referenced
    to IFRS S2 paragraphs.
    """
    try:
        entity_data = _req_to_entity(req)
        result = _engine.assess_ifrs_s2_financial_effects(entity_data)
        return {"status": "success", "data": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/ias36-impairment")
async def ias36_climate_impairment(req: IAS36ImpairmentRequest):
    """
    Assess all 12 IAS 36 climate impairment indicators.

    Identifies triggered indicators, estimates potential impairment amount
    per indicator, aggregates total potential impairment and lists
    asset classes requiring a formal IAS 36.59 impairment test.
    """
    try:
        entity_data = _req_to_entity(req)
        result = _engine.assess_ias36_climate_impairment(entity_data)
        return {"status": "success", "data": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/carbon-provisions")
async def carbon_provisions(req: CarbonProvisionsRequest):
    """
    Calculate IAS 37 carbon provision for ETS allowance deficit.

    Covers EU ETS allowance deficit, carbon tax liability, CORSIA
    offsetting obligation, and voluntary carbon offset commitments.
    Returns provision amount, recognition basis, IAS 37 recognition
    status (recognised vs contingent_disclosure_only) and 3-year
    forward provision using carbon price appreciation assumptions.
    """
    try:
        entity_data = _req_to_entity(req)
        result = _engine.calculate_carbon_provisions(entity_data)
        return {"status": "success", "data": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/stranded-assets")
async def stranded_asset_assessment(req: StrandedAssetsRequest):
    """
    Assess stranded asset write-down exposure across 6 trigger scenarios.

    Uses IEA NZE2050, regulatory phase-out timelines and market dynamics
    to identify triggered write-downs. Returns write-down amounts,
    timelines, affected asset types and stranding severity tier.

    Scenario modifier: net_zero_2050 (1.4×) > below_2c (1.0×) >
    delayed_transition (0.7×) > current_policies (0.4×).
    """
    try:
        entity_data = _req_to_entity(req)
        result = _engine.assess_stranded_assets(entity_data)
        return {"status": "success", "data": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/climate-financials")
async def climate_adjusted_financials(req: ClimateFinancialsRequest):
    """
    Compute climate-adjusted revenue, EBITDA and PAT across three
    NGFS-aligned temperature scenarios (1.5°C / 2°C / 3°C).

    Applies sector-specific SCENARIO_FINANCIAL_MULTIPLIERS, incorporates
    carbon provision drag and climate CapEx depreciation drag before
    applying scenario multipliers. Returns scenario table with EBITDA
    impact % and most adverse scenario identification.
    """
    try:
        entity_data = _req_to_entity(req)
        result = _engine.compute_climate_adjusted_financials(entity_data)
        return {"status": "success", "data": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# GET reference data endpoints
# ---------------------------------------------------------------------------


@router.get("/ref/financial-effect-categories")
async def ref_financial_effect_categories():
    """
    Return the 8 IFRS S2 financial effect categories (IFRS S2 paras 29-36).

    Includes income statement / balance sheet impact flags, disclosure
    requirement status, IFRS S2 paragraph reference, typical sectors
    and quantification approach for each category.
    """
    return {
        "status": "success",
        "standard": "IFRS S2 Climate-Related Disclosures (ISSB June 2023, effective 1 Jan 2024)",
        "category_count": len(IFRS_S2_FINANCIAL_EFFECT_CATEGORIES),
        "data": IFRS_S2_FINANCIAL_EFFECT_CATEGORIES,
    }


@router.get("/ref/impairment-indicators")
async def ref_impairment_indicators():
    """
    Return the 12 IAS 36 climate impairment indicators.

    Covers 6 external indicators (IAS 36 para 12) and 6 internal
    indicators (IAS 36 paras 13-14), with asset classes affected,
    threshold guidance, IAS 36 paragraph reference, impairment
    probability and severity rating.
    """
    external = [i for i in IAS36_CLIMATE_INDICATORS if i.get("type") == "external"]
    internal = [i for i in IAS36_CLIMATE_INDICATORS if i.get("type") == "internal"]
    return {
        "status": "success",
        "standard": "IAS 36 Impairment of Assets — IASB climate integration guidance (2024)",
        "total_indicators": len(IAS36_CLIMATE_INDICATORS),
        "external_count": len(external),
        "internal_count": len(internal),
        "external_indicators": external,
        "internal_indicators": internal,
    }


@router.get("/ref/scenario-multipliers")
async def ref_scenario_multipliers():
    """
    Return sector-level SCENARIO_FINANCIAL_MULTIPLIERS for 1.5°C / 2°C / 3°C
    scenarios used in climate-adjusted P&L modelling.

    Includes revenue impact percentages, revenue sensitivity rating,
    primary driver narrative and sector notes.
    """
    return {
        "status": "success",
        "methodology": "NGFS Phase IV Scenarios 2023; IPCC AR6 WG III damage functions; IEA WEO 2023",
        "sector_count": len(SCENARIO_FINANCIAL_MULTIPLIERS),
        "data": SCENARIO_FINANCIAL_MULTIPLIERS,
    }


@router.get("/ref/carbon-provision-thresholds")
async def ref_carbon_provision_thresholds():
    """
    Return CARBON_PROVISION_THRESHOLDS — sector-level ETS exposure guidance
    and IAS 37 provision probability for 8 sectors.
    """
    return {
        "status": "success",
        "standard": "IAS 37 Provisions; EU ETS Directive 2003/87/EC; CORSIA Phase I 2024-2026",
        "sector_count": len(CARBON_PROVISION_THRESHOLDS),
        "data": CARBON_PROVISION_THRESHOLDS,
    }


@router.get("/ref/stranded-asset-triggers")
async def ref_stranded_asset_triggers():
    """
    Return the 6 STRANDED_ASSET_TRIGGERS with write-down probability,
    asset types, time horizon and regulatory trigger references.
    """
    return {
        "status": "success",
        "methodology": "IEA NZE2050; NGFS Phase IV; IPCC AR6; sector-specific regulatory timelines",
        "trigger_count": len(STRANDED_ASSET_TRIGGERS),
        "data": STRANDED_ASSET_TRIGGERS,
    }
