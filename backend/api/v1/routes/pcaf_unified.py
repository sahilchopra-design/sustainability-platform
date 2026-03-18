"""
PCAF Unified Module — API Routes
====================================
Comprehensive REST API for the PCAF v2.0 orchestration engine.

Prefix: /api/v1/pcaf-module

Covers:
  - Full portfolio calculation (Parts A + B + C)
  - Per-asset-class financed emissions
  - Insurance-associated emissions (Part B)
  - Facilitated emissions (Part C)
  - Portfolio summary with regulatory disclosures
  - Data quality scoring and improvement roadmaps
  - Cross-module bridges (ECL, scenario analysis)
  - Reference data endpoints

References:
  - PCAF Global GHG Accounting Standard v2.0 (2022)
  - PCAF Insurance-Associated Emissions Standard (2022)
  - PCAF Capital Markets Instruments Guidance (2023)
"""
from __future__ import annotations

import logging
from typing import Optional, List, Dict, Any
from dataclasses import asdict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.pcaf_unified_engine import (
    PCAFUnifiedEngine,
    InsuranceHoldingInput,
    UnifiedPortfolioResult,
)
from services.facilitated_emissions_engine import (
    FacilitatedDealInput,
    IssuerEmissions,
)

logger = logging.getLogger("platform.pcaf_unified_routes")

router = APIRouter(
    prefix="/api/v1/pcaf-module",
    tags=["PCAF Unified Module"],
)

_engine = PCAFUnifiedEngine()


# ═══════════════════════════════════════════════════════════════════════════════
# Pydantic Request/Response Schemas
# ═══════════════════════════════════════════════════════════════════════════════

class HoldingInput(BaseModel):
    """A single Part A holding for financed emissions calculation."""
    asset_class: str = Field("listed_equity", description="PCAF asset class identifier")
    entity_name: str = Field("", description="Investee/borrower name")
    entity_id: Optional[str] = Field(None, description="LEI or internal ID")
    sector_gics: str = Field("Unknown", description="GICS sector classification")
    country_iso: str = Field("US", description="ISO 3166-1 alpha-2 country code")
    outstanding_amount_eur: float = Field(0.0, description="Outstanding exposure (EUR)")
    enterprise_value_eur: float = Field(0.0, description="EVIC for listed equity/bonds")
    total_equity_eur: float = Field(0.0, description="Total equity for balance sheet method")
    total_debt_eur: float = Field(0.0, description="Total debt for balance sheet method")
    annual_revenue_eur: float = Field(0.0, description="Annual revenue (EUR)")
    scope1_co2e_tonnes: Optional[float] = Field(None, description="Reported Scope 1 (tCO2e)")
    scope2_co2e_tonnes: Optional[float] = Field(None, description="Reported Scope 2 (tCO2e)")
    scope3_co2e_tonnes: Optional[float] = Field(None, description="Reported Scope 3 (tCO2e)")
    verification_status: str = Field("none", description="none|limited|verified")
    data_quality: Optional[int] = Field(None, description="DQS override (1-5)")
    # Mortgage-specific
    property_value_eur: float = Field(0.0)
    epc_rating: str = Field("D")
    floor_area_m2: float = Field(80.0)
    # Vehicle-specific
    vehicle_value_eur: float = Field(0.0)
    fuel_type: str = Field("petrol")
    annual_km: float = Field(0.0)
    # Project/Infrastructure
    total_project_cost_eur: float = Field(0.0)
    infrastructure_type: str = Field("other")
    # Green bond
    total_issuance_eur: float = Field(0.0)
    use_of_proceeds: str = Field("general_green")
    eu_taxonomy_aligned_pct: float = Field(0.0)
    # Alignment
    sbti_committed: bool = Field(False)
    net_zero_target_year: Optional[int] = Field(None)
    implied_temperature_c: float = Field(2.5)
    # Quality
    reported_emissions: Optional[Dict[str, float]] = Field(None)
    physical_activity_data: Optional[Dict[str, float]] = Field(None)
    pcaf_dqs_override: Optional[int] = Field(None)


class PortfolioCalculationRequest(BaseModel):
    """Full portfolio calculation request (Parts A + B + C)."""
    holdings: List[HoldingInput] = Field(default_factory=list, description="Part A holdings")
    insurance_policies: List[Dict[str, Any]] = Field(default_factory=list, description="Part B policies")
    facilitated_deals: List[Dict[str, Any]] = Field(default_factory=list, description="Part C deals")
    prior_year_emissions: Optional[float] = Field(None, description="Prior year total for YoY")


class AssetClassCalculationRequest(BaseModel):
    """Per-asset-class calculation request."""
    holding: HoldingInput


class InsurancePolicySchema(BaseModel):
    """Insurance policy input for Part B."""
    policy_id: str = ""
    line_of_business: str = "motor_personal"
    policyholder_name: str = ""
    policyholder_sector: str = "Unknown"
    country_iso: str = "US"
    gross_written_premium_eur: float = 0.0
    net_earned_premium_eur: float = 0.0
    vehicle_count: int = 0
    fuel_type: str = "petrol"
    annual_km_per_vehicle: float = 0.0
    insured_area_m2: float = 0.0
    epc_rating: str = "D"
    insured_revenue_eur: float = 0.0
    nace_sector: str = ""
    vessel_type: str = "container"
    vessel_count: int = 0
    capacity_mw: float = 0.0
    technology: str = "gas_ccgt"
    capacity_factor: float = 0.0
    scope1_tco2e: Optional[float] = None
    scope2_tco2e: Optional[float] = None
    data_source: str = "sector_average"
    pcaf_dqs_override: Optional[int] = None


class InsuranceCalculationRequest(BaseModel):
    """Batch insurance emissions calculation."""
    policies: List[InsurancePolicySchema]


class FacilitatedDealSchema(BaseModel):
    """Facilitated deal input for Part C."""
    deal_id: str = ""
    deal_type: str = "bond_underwriting"
    issuer_name: str = ""
    issuer_sector_gics: str = "Unknown"
    issuer_country_iso2: str = "US"
    issuer_revenue_musd: Optional[float] = None
    underwritten_amount_musd: float = 0.0
    total_deal_size_musd: float = 0.0
    shares_placed_value_musd: float = 0.0
    market_cap_musd: float = 0.0
    tranche_held_musd: float = 0.0
    total_pool_musd: float = 0.0
    arranged_amount_musd: float = 0.0
    total_facility_musd: float = 0.0
    bond_type: str = "corporate"
    green_bond: bool = False
    use_of_proceeds: str = "general"
    eu_taxonomy_aligned_pct: float = 0.0
    emissions_scope1: float = 0.0
    emissions_scope2: float = 0.0
    emissions_scope3: float = 0.0
    emissions_include_scope3: bool = False
    emissions_data_source: str = "self_reported"
    emissions_verified: str = "unverified"
    pcaf_dqs_override: Optional[int] = None


class FacilitatedCalculationRequest(BaseModel):
    """Batch facilitated emissions calculation."""
    deals: List[FacilitatedDealSchema]


class DQSAssessmentRequest(BaseModel):
    """Portfolio DQS assessment request."""
    holdings: List[HoldingInput]


class ImprovementRoadmapRequest(BaseModel):
    """DQS improvement roadmap request."""
    holdings: List[HoldingInput]


class ECLBridgeRequest(BaseModel):
    """PCAF to ECL bridge request."""
    holdings: List[HoldingInput]
    portfolio_temperature_c: float = Field(2.5, description="Portfolio implied temperature (C)")


class ScenarioBridgeRequest(BaseModel):
    """PCAF to scenario analysis bridge request."""
    holdings: List[HoldingInput] = Field(default_factory=list)
    prior_year_emissions: Optional[float] = None


# ═══════════════════════════════════════════════════════════════════════════════
# POST Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/calculate")
def calculate_portfolio(req: PortfolioCalculationRequest):
    """
    Full portfolio PCAF calculation combining Parts A, B, and C.

    Accepts holdings (financed), insurance policies, and facilitated deals.
    Returns unified portfolio metrics, concentration analysis, and YoY delta.
    """
    try:
        holdings_dicts = [h.model_dump() for h in req.holdings]

        # Convert insurance policies
        ins_policies = None
        if req.insurance_policies:
            ins_policies = [
                InsuranceHoldingInput(**p) for p in req.insurance_policies
            ]

        # Convert facilitated deals
        fac_deals = None
        if req.facilitated_deals:
            fac_deals = [_convert_deal(d) for d in req.facilitated_deals]

        result = _engine.calculate_portfolio(
            holdings=holdings_dicts,
            insurance_policies=ins_policies,
            facilitated_deals=fac_deals,
            prior_year_emissions=req.prior_year_emissions,
        )
        return asdict(result)

    except Exception as exc:
        logger.exception("Portfolio calculation failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/calculate/{asset_class}")
def calculate_asset_class(asset_class: str, req: AssetClassCalculationRequest):
    """
    Per-asset-class financed emissions calculation.

    Supported asset classes: listed_equity, corporate_bonds, business_loans,
    project_finance, commercial_real_estate, mortgages, vehicle_loans,
    sovereign_bonds, unlisted_equity, infrastructure, green_bonds.
    """
    valid_classes = {
        "listed_equity", "corporate_bonds", "business_loans", "project_finance",
        "commercial_real_estate", "mortgages", "vehicle_loans", "sovereign_bonds",
        "unlisted_equity", "infrastructure", "green_bonds",
    }
    if asset_class not in valid_classes:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid asset class '{asset_class}'. Valid: {sorted(valid_classes)}",
        )

    try:
        holding_dict = req.holding.model_dump()
        holding_dict["asset_class"] = asset_class
        calc_fn = _engine._get_asset_class_calculator(asset_class)
        return calc_fn(holding_dict)

    except Exception as exc:
        logger.exception("Asset class calculation failed: %s", asset_class)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/insurance")
def calculate_insurance(req: InsuranceCalculationRequest):
    """
    Insurance-associated emissions calculation (PCAF Part B).

    Supports motor, property, commercial, life/health, marine, energy,
    liability, and reinsurance lines of business.
    """
    try:
        policies = [
            InsuranceHoldingInput(**p.model_dump()) for p in req.policies
        ]
        result = _engine.calculate_insurance(policies)
        return asdict(result)

    except Exception as exc:
        logger.exception("Insurance calculation failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/facilitated")
def calculate_facilitated(req: FacilitatedCalculationRequest):
    """
    Facilitated emissions calculation (PCAF Part C).

    Supports bond/equity underwriting, securitisation, syndicated loans,
    IPO, advisory mandates.
    """
    try:
        deals = [_convert_deal_schema(d) for d in req.deals]
        results, summary = _engine.calculate_facilitated(deals)
        return {
            "deal_results": [asdict(r) for r in results],
            "portfolio_summary": asdict(summary),
        }

    except Exception as exc:
        logger.exception("Facilitated calculation failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/portfolio-summary")
def portfolio_summary(req: PortfolioCalculationRequest):
    """
    Aggregated portfolio metrics with concentration analysis.

    Same as /calculate but returns a streamlined summary view.
    """
    try:
        holdings_dicts = [h.model_dump() for h in req.holdings]
        result = _engine.calculate_portfolio(
            holdings=holdings_dicts,
            prior_year_emissions=req.prior_year_emissions,
        )
        return {
            "total_financed_emissions_tco2e": result.total_emissions_tco2e,
            "scope1_tco2e": result.total_scope1_tco2e,
            "scope2_tco2e": result.total_scope2_tco2e,
            "scope3_tco2e": result.total_scope3_tco2e,
            "waci_scope12": result.waci_scope12,
            "waci_scope123": result.waci_scope123,
            "carbon_footprint_tco2e_per_m_eur": result.carbon_footprint_tco2e_per_m_eur,
            "implied_temperature_c": result.implied_temperature_c,
            "portfolio_dqs": result.portfolio_dqs,
            "coverage_pct": result.coverage_pct,
            "total_aum_eur": result.total_aum_eur,
            "top_10_emitters": result.top_10_emitters,
            "asset_class_breakdown": result.asset_class_breakdown,
            "yoy_delta": result.yoy_delta,
        }

    except Exception as exc:
        logger.exception("Portfolio summary failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/regulatory-disclosures")
def regulatory_disclosures(req: PortfolioCalculationRequest):
    """
    Generate all regulatory framework outputs from PCAF data.

    Produces: SFDR PAI 1-14, EU Taxonomy Art. 8, TCFD, CSRD ESRS E1,
    ISSB S2, GRI 305, NZBA tracking.
    """
    try:
        holdings_dicts = [h.model_dump() for h in req.holdings]
        portfolio = _engine.calculate_portfolio(
            holdings=holdings_dicts,
            prior_year_emissions=req.prior_year_emissions,
        )
        disclosures = _engine.generate_regulatory_disclosures(portfolio)
        return asdict(disclosures)

    except Exception as exc:
        logger.exception("Regulatory disclosures failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/dqs-assessment")
def dqs_assessment(req: DQSAssessmentRequest):
    """
    Portfolio-level PCAF Data Quality Score assessment.

    Returns weighted DQS, distribution, confidence bands, and uncertainty.
    """
    try:
        holdings_dicts = [h.model_dump() for h in req.holdings]
        result = _engine.assess_data_quality(holdings_dicts)
        return asdict(result)

    except Exception as exc:
        logger.exception("DQS assessment failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/improvement-roadmap")
def improvement_roadmap(req: ImprovementRoadmapRequest):
    """
    Generate DQS improvement roadmap with per-holding gap closure actions.

    Prioritises by exposure-weighted DQS improvement potential.
    """
    try:
        holdings_dicts = [h.model_dump() for h in req.holdings]
        roadmap = _engine.generate_improvement_roadmap(holdings_dicts)
        return {
            "total_holdings": roadmap.total_holdings,
            "current_portfolio_dqs": roadmap.current_portfolio_dqs,
            "target_portfolio_dqs": roadmap.target_portfolio_dqs,
            "estimated_timeline_months": roadmap.estimated_timeline_months,
            "quick_wins": roadmap.quick_wins,
            "high_impact": roadmap.high_impact,
            "actions": [asdict(a) for a in roadmap.actions],
        }

    except Exception as exc:
        logger.exception("Improvement roadmap failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/bridge/ecl")
def bridge_ecl(req: ECLBridgeRequest):
    """
    PCAF to ECL bridge: convert financed emissions into credit risk climate overlays.

    Maps PCAF investee profiles to ECL ClimateRiskInputs for climate-adjusted
    PD/LGD/ECL calculation.
    """
    try:
        holdings_dicts = [h.model_dump() for h in req.holdings]
        result = _engine.bridge_to_ecl(
            holdings_dicts,
            portfolio_temperature_c=req.portfolio_temperature_c,
        )
        return asdict(result)

    except Exception as exc:
        logger.exception("ECL bridge failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/bridge/scenario")
def bridge_scenario(req: ScenarioBridgeRequest):
    """
    PCAF to scenario analysis bridge: emit NGFS-aligned climate scenario overlays.

    Returns per-scenario expected loss adjustments and sector impact maps.
    """
    try:
        holdings_dicts = [h.model_dump() for h in req.holdings]
        portfolio = _engine.calculate_portfolio(
            holdings=holdings_dicts,
            prior_year_emissions=req.prior_year_emissions,
        )
        overlays = _engine.bridge_to_scenario_analysis(portfolio)
        return {
            "scenario_overlays": [asdict(o) for o in overlays],
            "portfolio_temperature_c": portfolio.implied_temperature_c,
            "total_emissions_tco2e": portfolio.total_emissions_tco2e,
        }

    except Exception as exc:
        logger.exception("Scenario bridge failed")
        raise HTTPException(status_code=500, detail=str(exc))


# ═══════════════════════════════════════════════════════════════════════════════
# GET Reference Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/ref/asset-classes")
def ref_asset_classes():
    """Asset class metadata with attribution formulas and DQS table references."""
    return _engine.get_asset_class_registry()


@router.get("/ref/emission-factors")
def ref_emission_factors():
    """Complete emission factor library (sector, EPC, vehicle, sovereign, marine, energy)."""
    return _engine.get_emission_factor_library()


@router.get("/ref/dqs-framework")
def ref_dqs_framework():
    """DQS methodology reference: levels, dimensions, improvement paths, benchmarks."""
    return _engine.get_dqs_framework()


@router.get("/ref/regulatory-mappings")
def ref_regulatory_mappings():
    """Cross-framework mapping table (PCAF -> SFDR, CSRD, TCFD, ISSB, GRI, EU Taxonomy, CDP, NZBA)."""
    return _engine.get_regulatory_mappings()


@router.get("/ref/insurance-lobs")
def ref_insurance_lobs():
    """Insurance lines of business metadata with emission factors and methods."""
    return _engine.get_insurance_lob_metadata()


@router.get("/ref/deal-types")
def ref_deal_types():
    """Facilitated emissions deal type metadata with attribution formulas."""
    return _engine.get_deal_type_metadata()


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _convert_deal_schema(d: FacilitatedDealSchema) -> FacilitatedDealInput:
    """Convert Pydantic schema to FacilitatedDealInput dataclass."""
    return FacilitatedDealInput(
        deal_id=d.deal_id,
        deal_type=d.deal_type,
        issuer_name=d.issuer_name,
        issuer_sector_gics=d.issuer_sector_gics,
        issuer_country_iso2=d.issuer_country_iso2,
        issuer_revenue_musd=d.issuer_revenue_musd,
        underwritten_amount_musd=d.underwritten_amount_musd,
        total_deal_size_musd=d.total_deal_size_musd,
        shares_placed_value_musd=d.shares_placed_value_musd,
        market_cap_musd=d.market_cap_musd,
        tranche_held_musd=d.tranche_held_musd,
        total_pool_musd=d.total_pool_musd,
        arranged_amount_musd=d.arranged_amount_musd,
        total_facility_musd=d.total_facility_musd,
        bond_type=d.bond_type,
        green_bond=d.green_bond,
        use_of_proceeds=d.use_of_proceeds,
        eu_taxonomy_aligned_pct=d.eu_taxonomy_aligned_pct,
        emissions=IssuerEmissions(
            scope1_tco2e=d.emissions_scope1,
            scope2_tco2e=d.emissions_scope2,
            scope3_tco2e=d.emissions_scope3,
            include_scope3=d.emissions_include_scope3,
            data_source=d.emissions_data_source,
            verification_status=d.emissions_verified,
        ),
        pcaf_dqs_override=d.pcaf_dqs_override,
    )


def _convert_deal(d: Dict[str, Any]) -> FacilitatedDealInput:
    """Convert dict to FacilitatedDealInput dataclass."""
    emissions = None
    if d.get("emissions_scope1") or d.get("emissions_scope2"):
        emissions = IssuerEmissions(
            scope1_tco2e=float(d.get("emissions_scope1", 0)),
            scope2_tco2e=float(d.get("emissions_scope2", 0)),
            scope3_tco2e=float(d.get("emissions_scope3", 0)),
            include_scope3=d.get("emissions_include_scope3", False),
            data_source=d.get("emissions_data_source", "self_reported"),
            verification_status=d.get("emissions_verified", "unverified"),
        )

    return FacilitatedDealInput(
        deal_id=d.get("deal_id", ""),
        deal_type=d.get("deal_type", "bond_underwriting"),
        issuer_name=d.get("issuer_name", ""),
        issuer_sector_gics=d.get("issuer_sector_gics", "Unknown"),
        issuer_country_iso2=d.get("issuer_country_iso2", "US"),
        issuer_revenue_musd=d.get("issuer_revenue_musd"),
        underwritten_amount_musd=float(d.get("underwritten_amount_musd", 0)),
        total_deal_size_musd=float(d.get("total_deal_size_musd", 0)),
        shares_placed_value_musd=float(d.get("shares_placed_value_musd", 0)),
        market_cap_musd=float(d.get("market_cap_musd", 0)),
        tranche_held_musd=float(d.get("tranche_held_musd", 0)),
        total_pool_musd=float(d.get("total_pool_musd", 0)),
        arranged_amount_musd=float(d.get("arranged_amount_musd", 0)),
        total_facility_musd=float(d.get("total_facility_musd", 0)),
        bond_type=d.get("bond_type", "corporate"),
        green_bond=d.get("green_bond", False),
        use_of_proceeds=d.get("use_of_proceeds", "general"),
        eu_taxonomy_aligned_pct=float(d.get("eu_taxonomy_aligned_pct", 0)),
        emissions=emissions,
        pcaf_dqs_override=d.get("pcaf_dqs_override"),
    )
