"""
PCAF Unified Orchestration Engine
====================================
Master orchestrator for the Partnership for Carbon Accounting Financials
(PCAF) Global GHG Accounting and Reporting Standard v2.0.

Consolidates and orchestrates all existing PCAF modules:
  - Part A: Financed Emissions (7+3 asset classes) via pcaf_waci_engine
  - Part B: Insurance-Associated Emissions via facilitated_emissions_engine
  - Part C: Capital Markets Facilitated Emissions via facilitated_emissions_engine
  - DQS Framework via pcaf_quality_engine
  - ECL Bridge via pcaf_ecl_bridge
  - Glidepath Tracking via pcaf_time_series_engine

Provides unified portfolio calculation, regulatory disclosure generation,
data quality management, cross-module bridging, and improvement roadmaps.

References:
  - PCAF Global GHG Accounting Standard v2.0 (November 2022)
  - PCAF Insurance-Associated Emissions Standard (2022)
  - PCAF Capital Markets Instruments Guidance (2023)
  - SFDR RTS Annex I (EU 2022/1288) — PAI indicators 1-14
  - CSRD ESRS E1 — Climate Change (EFRAG IG3)
  - IFRS S2 — Climate-related Disclosures
  - GRI 305 — Emissions (2016, updated 2020)
  - EU Taxonomy Regulation 2020/852 — Art. 8 KPIs
  - TCFD Recommendations — Metrics & Targets (2017, 2021 update)
  - NZBA Guidelines for Climate Target Setting (2021)
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple

# --- Delegate imports: existing PCAF engines ---
from services.pcaf_waci_engine import (
    PCAFWACIEngine,
    PCAFAssetClass,
    DataQualityScore,
    InvesteeData,
    FinancedEmissionsResult,
    PortfolioPCAFResult,
    _SOVEREIGN_GDP_EUR,
    _WACI_TEMPERATURE_MAPPING,
    _FOSSIL_FUEL_GICS_SECTORS,
)
from services.pcaf_quality_engine import (
    PCAFQualityEngine,
    PCAF_ASSET_CLASSES,
    PCAF_DQS_LEVELS,
    PCAF_QUALITY_DIMENSIONS,
    PCAF_EMISSION_FACTORS,
    PCAF_ATTRIBUTION_METHODS,
    PCAF_QUALITY_IMPROVEMENT_PATHS,
    PCAF_CROSS_FRAMEWORK_MAP,
    PCAF_QUALITY_BENCHMARKS,
    _EF_BY_NACE,
)
from services.facilitated_emissions_engine import (
    FacilitatedEmissionsEngine,
    FacilitatedDealInput,
    FacilitatedEmissionsResult as FacDealResult,
    InsurancePolicyInput,
    InsuranceEmissionsResult,
    PortfolioFacilitatedSummary,
    PortfolioInsuranceSummary,
    IssuerEmissions,
    SECTOR_EMISSION_INTENSITIES,
    VEHICLE_EMISSION_FACTORS,
    BUILDING_EMISSION_FACTORS,
    INSURANCE_LOB_FACTORS,
    InsuranceLineOfBusiness,
    FacilitatedDealType,
    VehicleFuelType,
    BuildingEPCRating,
)
from services.pcaf_ecl_bridge import (
    PCAFInvesteeProfile,
    ECLClimateInputs,
    PortfolioBridgeResult,
    map_investee_to_ecl_climate,
    bridge_portfolio as ecl_bridge_portfolio,
    DQS_CONFIDENCE_WEIGHTS,
)

logger = logging.getLogger("platform.pcaf_unified")


# ═══════════════════════════════════════════════════════════════════════════════
# Reference Data — Emission Factors (PCAF v2.0 Tables)
# ═══════════════════════════════════════════════════════════════════════════════

# Sovereign production-based emissions (MtCO2e per year) — IEA/EDGAR 2023
SOVEREIGN_PRODUCTION_EMISSIONS: Dict[str, float] = {
    "US": 5007.0, "CN": 11472.0, "DE": 674.0, "GB": 332.0, "FR": 299.0,
    "JP": 1066.0, "IN": 2710.0, "IT": 326.0, "BR": 476.0, "CA": 568.0,
    "AU": 393.0, "KR": 616.0, "RU": 1755.0, "SA": 588.0, "MX": 449.0,
    "ID": 619.0, "TR": 427.0, "ZA": 435.0, "PL": 306.0, "TH": 257.0,
}

# Green bond use-of-proceeds emission reduction factors (tCO2e avoided per M EUR)
GREEN_BOND_UOP_FACTORS: Dict[str, float] = {
    "renewable_energy": 320.0,
    "energy_efficiency": 180.0,
    "clean_transport": 140.0,
    "green_buildings": 95.0,
    "pollution_prevention": 60.0,
    "biodiversity": 25.0,
    "water_management": 40.0,
    "climate_adaptation": 15.0,
    "general_green": 120.0,
}

# Infrastructure project lifecycle emission factors (tCO2e per M EUR invested)
INFRASTRUCTURE_EF: Dict[str, float] = {
    "solar_pv": 25.0,
    "onshore_wind": 12.0,
    "offshore_wind": 18.0,
    "hydro": 22.0,
    "gas_ccgt": 380.0,
    "coal_power": 950.0,
    "nuclear": 8.0,
    "transport_rail": 45.0,
    "transport_road": 120.0,
    "water_treatment": 65.0,
    "telecom": 30.0,
    "data_centre": 85.0,
    "port_logistics": 75.0,
    "other": 100.0,
}

# EPC rating to annual kgCO2/m2 for residential mortgages (weighted by country avg)
MORTGAGE_EPC_FACTORS: Dict[str, float] = {
    "A+": 5.0, "A": 12.0, "B": 25.0, "C": 42.0,
    "D": 65.0, "E": 90.0, "F": 120.0, "G": 160.0,
}

# Marine vessel emission factors (tCO2e per vessel per year by type)
MARINE_VESSEL_FACTORS: Dict[str, float] = {
    "container": 28500.0,
    "bulk_carrier": 12800.0,
    "tanker": 18500.0,
    "lng_carrier": 22000.0,
    "ro_ro": 9500.0,
    "ferry": 7200.0,
    "offshore_support": 4500.0,
    "fishing": 1200.0,
    "cruise": 55000.0,
    "other": 8000.0,
}

# Energy asset emission factors (tCO2e per MW per year by technology)
ENERGY_ASSET_FACTORS: Dict[str, float] = {
    "coal": 7500.0,
    "gas_ocgt": 3200.0,
    "gas_ccgt": 2800.0,
    "oil": 5100.0,
    "biomass": 400.0,
    "solar": 0.0,
    "onshore_wind": 0.0,
    "offshore_wind": 0.0,
    "hydro": 0.0,
    "nuclear": 0.0,
    "geothermal": 50.0,
}


# ═══════════════════════════════════════════════════════════════════════════════
# Internal Dataclasses
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class AssetClassMeta:
    """Metadata for a PCAF asset class including attribution formula."""
    id: str
    label: str
    pcaf_part: str  # A, B, or C
    attribution_method: str
    formula: str
    dqs_table_ref: str
    scope_coverage: str  # which scopes are mandatory


@dataclass
class InsuranceHoldingInput:
    """Extended insurance holding input for unified engine."""
    policy_id: str = ""
    line_of_business: str = "motor_personal"
    policyholder_name: str = ""
    policyholder_sector: str = "Unknown"
    country_iso: str = "US"
    gross_written_premium_eur: float = 0.0
    net_earned_premium_eur: float = 0.0
    # Motor
    vehicle_count: int = 0
    fuel_type: str = "petrol"
    annual_km_per_vehicle: float = 0.0
    # Property
    insured_area_m2: float = 0.0
    epc_rating: str = "D"
    # Commercial
    insured_revenue_eur: float = 0.0
    nace_sector: str = ""
    # Marine
    vessel_type: str = "container"
    vessel_count: int = 0
    # Energy
    capacity_mw: float = 0.0
    technology: str = "gas_ccgt"
    capacity_factor: float = 0.0
    # Direct emissions override
    scope1_tco2e: Optional[float] = None
    scope2_tco2e: Optional[float] = None
    data_source: str = "sector_average"
    pcaf_dqs_override: Optional[int] = None


@dataclass
class InsuranceHoldingResult:
    """Per-policy insurance emissions result from unified engine."""
    policy_id: str
    line_of_business: str
    policyholder_name: str
    attribution_method: str = ""
    scope1_tco2e: float = 0.0
    scope2_tco2e: float = 0.0
    total_tco2e: float = 0.0
    gwp_eur: float = 0.0
    intensity_tco2e_per_m_premium: float = 0.0
    pcaf_dqs: int = 5
    methodology_note: str = ""
    warnings: List[str] = field(default_factory=list)


@dataclass
class PortfolioInsuranceResult:
    """Portfolio-level insurance emissions aggregation."""
    total_policies: int = 0
    total_insured_tco2e: float = 0.0
    scope1_total: float = 0.0
    scope2_total: float = 0.0
    total_gwp_eur: float = 0.0
    weighted_dqs: float = 5.0
    intensity_tco2e_per_m_premium: float = 0.0
    by_lob: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    policy_results: List[Dict[str, Any]] = field(default_factory=list)
    methodology: str = "PCAF Insurance-Associated Emissions Standard v2.0 — Part B"


@dataclass
class UnifiedPortfolioResult:
    """Complete PCAF portfolio result combining Parts A, B, and C."""
    # Part A — Financed Emissions
    financed_emissions: Dict[str, Any] = field(default_factory=dict)
    # Part B — Insurance
    insurance_emissions: Dict[str, Any] = field(default_factory=dict)
    # Part C — Facilitated
    facilitated_emissions: Dict[str, Any] = field(default_factory=dict)
    # Aggregated
    total_scope1_tco2e: float = 0.0
    total_scope2_tco2e: float = 0.0
    total_scope3_tco2e: float = 0.0
    total_emissions_tco2e: float = 0.0
    waci_scope12: float = 0.0
    waci_scope123: float = 0.0
    carbon_footprint_tco2e_per_m_eur: float = 0.0
    implied_temperature_c: float = 0.0
    portfolio_dqs: float = 5.0
    coverage_pct: float = 0.0
    total_aum_eur: float = 0.0
    # Concentration
    top_10_emitters: List[Dict[str, Any]] = field(default_factory=list)
    sector_breakdown: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    asset_class_breakdown: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # YoY
    yoy_delta: Dict[str, Any] = field(default_factory=dict)
    # Metadata
    calculation_timestamp: str = ""
    engine_version: str = "PCAF-Unified-Engine v1.0"


@dataclass
class RegulatoryDisclosurePackage:
    """Complete regulatory disclosure outputs derived from PCAF data."""
    sfdr_pai: Dict[str, Any] = field(default_factory=dict)
    eu_taxonomy_art8: Dict[str, Any] = field(default_factory=dict)
    tcfd_metrics: Dict[str, Any] = field(default_factory=dict)
    csrd_esrs_e1: Dict[str, Any] = field(default_factory=dict)
    issb_s2: Dict[str, Any] = field(default_factory=dict)
    gri_305: Dict[str, Any] = field(default_factory=dict)
    nzba_tracking: Dict[str, Any] = field(default_factory=dict)
    cross_framework_map: List[Dict[str, Any]] = field(default_factory=list)
    generated_at: str = ""


@dataclass
class DQSAssessmentResult:
    """Portfolio-level DQS assessment with uncertainty estimation."""
    portfolio_dqs: float = 5.0
    dqs_distribution: Dict[int, int] = field(default_factory=dict)
    by_asset_class: Dict[str, float] = field(default_factory=dict)
    confidence_band_low: float = 0.0
    confidence_band_central: float = 0.0
    confidence_band_high: float = 0.0
    uncertainty_pct: float = 0.0
    coverage_pct: float = 0.0
    holdings_assessed: int = 0


@dataclass
class ImprovementAction:
    """Single DQS improvement action for a holding."""
    holding_id: str
    entity_name: str
    current_dqs: int
    target_dqs: int
    action: str
    effort: str
    expected_uncertainty_reduction_pct: float
    priority: str  # high, medium, low


@dataclass
class ImprovementRoadmap:
    """Portfolio-level DQS improvement roadmap."""
    total_holdings: int = 0
    current_portfolio_dqs: float = 5.0
    target_portfolio_dqs: float = 3.0
    actions: List[ImprovementAction] = field(default_factory=list)
    estimated_timeline_months: int = 12
    quick_wins: int = 0
    high_impact: int = 0


@dataclass
class ScenarioOverlay:
    """Climate scenario overlay for PCAF-to-scenario bridging."""
    scenario_name: str
    temperature_target_c: float
    carbon_price_eur_per_tco2: float
    portfolio_el_adjustment_pct: float
    sector_impacts: Dict[str, float] = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════════
# Asset Class Registry (complete PCAF v2.0 — 7 standard + 3 extended)
# ═══════════════════════════════════════════════════════════════════════════════

ASSET_CLASS_REGISTRY: List[AssetClassMeta] = [
    AssetClassMeta(
        id="listed_equity", label="Listed Equity & Corporate Bonds",
        pcaf_part="A", attribution_method="evic",
        formula="AF = Outstanding / EVIC",
        dqs_table_ref="Table 5.1", scope_coverage="S1+S2 mandatory, S3 encouraged",
    ),
    AssetClassMeta(
        id="corporate_bonds", label="Corporate Bonds",
        pcaf_part="A", attribution_method="evic",
        formula="AF = Outstanding / EVIC",
        dqs_table_ref="Table 5.1", scope_coverage="S1+S2 mandatory, S3 encouraged",
    ),
    AssetClassMeta(
        id="business_loans", label="Business Loans & SME Loans",
        pcaf_part="A", attribution_method="balance_sheet",
        formula="AF = Outstanding / (Total Equity + Total Debt)",
        dqs_table_ref="Table 5.2", scope_coverage="S1+S2 mandatory, S3 encouraged",
    ),
    AssetClassMeta(
        id="project_finance", label="Project Finance",
        pcaf_part="A", attribution_method="project_cost",
        formula="AF = Outstanding / Total Project Cost",
        dqs_table_ref="Table 5.3", scope_coverage="S1+S2 mandatory",
    ),
    AssetClassMeta(
        id="commercial_real_estate", label="Commercial Real Estate",
        pcaf_part="A", attribution_method="property_value",
        formula="AF = Outstanding / Property Value (at origination)",
        dqs_table_ref="Table 5.4", scope_coverage="S1+S2 (building operational)",
    ),
    AssetClassMeta(
        id="mortgages", label="Residential Mortgages",
        pcaf_part="A", attribution_method="property_value",
        formula="AF = Outstanding / Property Value; EPC-weighted EF",
        dqs_table_ref="Table 5.5", scope_coverage="S1+S2 (household energy)",
    ),
    AssetClassMeta(
        id="vehicle_loans", label="Motor Vehicle Loans",
        pcaf_part="A", attribution_method="vehicle_value",
        formula="AF = Outstanding / Vehicle Value; fuel-type EF",
        dqs_table_ref="Table 5.6", scope_coverage="S1 (tailpipe) + S2 (BEV charging)",
    ),
    AssetClassMeta(
        id="sovereign_bonds", label="Sovereign Bonds",
        pcaf_part="A", attribution_method="gdp",
        formula="AF = Outstanding / GDP (EUR); production-based emissions",
        dqs_table_ref="Table 5.7", scope_coverage="Production-based territorial emissions",
    ),
    AssetClassMeta(
        id="unlisted_equity", label="Unlisted Equity",
        pcaf_part="A", attribution_method="evic_proxy",
        formula="AF = Outstanding / EVIC (proxy with size premium)",
        dqs_table_ref="Table 5.8", scope_coverage="S1+S2 mandatory, S3 encouraged",
    ),
    AssetClassMeta(
        id="infrastructure", label="Infrastructure Finance",
        pcaf_part="A", attribution_method="project_lifecycle",
        formula="AF = Outstanding / Total Project Cost; lifecycle EF",
        dqs_table_ref="Table 5.3 (extended)", scope_coverage="S1+S2 (project operational)",
    ),
    AssetClassMeta(
        id="green_bonds", label="Green Bonds (Use-of-Proceeds)",
        pcaf_part="A", attribution_method="uop_allocation",
        formula="AF = Outstanding / Total Issuance; UoP-allocated EF",
        dqs_table_ref="Table 5.1 (green overlay)", scope_coverage="S1+S2 (financed activities)",
    ),
]

_ASSET_CLASS_BY_ID: Dict[str, AssetClassMeta] = {ac.id: ac for ac in ASSET_CLASS_REGISTRY}


# ═══════════════════════════════════════════════════════════════════════════════
# Emission Factor Fallback Hierarchy
# ═══════════════════════════════════════════════════════════════════════════════

def _emission_factor_fallback(
    reported_s1: Optional[float],
    reported_s2: Optional[float],
    verified: bool,
    sector: str,
    revenue_eur: float,
    outstanding_eur: float,
) -> Tuple[float, float, float, int, str]:
    """
    PCAF emission factor fallback hierarchy:
      1. Verified reported data (DQS 1)
      2. Unverified reported data (DQS 2)
      3. Sector-average intensity x revenue (DQS 4)
      4. Sector proxy x outstanding (DQS 5)

    Returns (scope1, scope2, scope3_est, dqs, source_description).
    """
    # Level 1-2: reported data available
    if reported_s1 is not None and reported_s2 is not None:
        s1, s2 = reported_s1, reported_s2
        # Estimate scope 3 as 2x scope 1+2 (PCAF default for unreported)
        s3_est = (s1 + s2) * 2.0
        if verified:
            return s1, s2, s3_est, 1, "Verified primary emissions data"
        return s1, s2, s3_est, 2, "Unverified reported emissions data"

    # Level 4: sector intensity x revenue
    if revenue_eur > 0:
        intensity = SECTOR_EMISSION_INTENSITIES.get(sector, 150.0)
        rev_m = revenue_eur / 1_000_000.0
        total_est = rev_m * intensity
        s1 = total_est * 0.6
        s2 = total_est * 0.4
        s3_est = total_est * 1.5
        return s1, s2, s3_est, 4, f"Sector intensity ({intensity} tCO2e/MEUR) x revenue"

    # Level 5: proxy from outstanding
    if outstanding_eur > 0:
        proxy_intensity = SECTOR_EMISSION_INTENSITIES.get(sector, 150.0) * 0.8
        out_m = outstanding_eur / 1_000_000.0
        total_est = out_m * proxy_intensity
        s1 = total_est * 0.6
        s2 = total_est * 0.4
        s3_est = total_est * 1.5
        return s1, s2, s3_est, 5, f"Sector proxy ({proxy_intensity} tCO2e/MEUR) x outstanding"

    return 0.0, 0.0, 0.0, 5, "No data available"


# ═══════════════════════════════════════════════════════════════════════════════
# DQS Auto-Derivation per PCAF Tables 5.1-5.8
# ═══════════════════════════════════════════════════════════════════════════════

def derive_dqs_auto(
    has_verified_emissions: bool = False,
    has_reported_emissions: bool = False,
    has_physical_activity: bool = False,
    has_revenue: bool = False,
    has_sector_only: bool = False,
    asset_class: str = "listed_equity",
) -> int:
    """
    Derive PCAF DQS per the asset-class-specific tables (5.1-5.8).

    Hierarchy:
      DQS 1: Verified Scope 1+2+3 emissions (audited, ISAE 3410 / ISO 14064-3)
      DQS 2: Unverified reported Scope 1+2 emissions
      DQS 3: Physical activity data (kWh, litres, tonnes) + emission factors
      DQS 4: Economic activity (revenue) + sector emission factors
      DQS 5: Sector-average proxy from outstanding/assets
    """
    if has_verified_emissions:
        return 1
    if has_reported_emissions:
        return 2
    if has_physical_activity:
        return 3
    if has_revenue:
        return 4
    return 5


# ═══════════════════════════════════════════════════════════════════════════════
# Main Engine
# ═══════════════════════════════════════════════════════════════════════════════

class PCAFUnifiedEngine:
    """
    Master orchestrator for PCAF v2.0 Parts A, B, and C.

    Delegates to existing specialist engines for calculations and adds:
    - Unified portfolio orchestration (all asset classes + insurance + facilitated)
    - Complete regulatory disclosure generation (7 frameworks)
    - Portfolio-level DQS management with improvement roadmaps
    - Cross-module bridging (ECL, scenario analysis, entity 360)
    - Concentration analysis and YoY tracking
    """

    def __init__(self) -> None:
        self._waci_engine = PCAFWACIEngine()
        self._quality_engine = PCAFQualityEngine()
        self._facilitated_engine = FacilitatedEmissionsEngine()

    # ──────────────────────────────────────────────────────────────────────────
    # A) ASSET CLASS CALCULATIONS — PCAF v2.0 Part A
    # ──────────────────────────────────────────────────────────────────────────

    def calculate_listed_equity(self, holding: Dict[str, Any]) -> Dict[str, Any]:
        """Listed Equity & Corporate Bonds: EVIC attribution (PCAF Table 5.1)."""
        return self._calculate_standard_asset_class(holding, "listed_equity")

    def calculate_corporate_bonds(self, holding: Dict[str, Any]) -> Dict[str, Any]:
        """Corporate Bonds: EVIC attribution (PCAF Table 5.1)."""
        return self._calculate_standard_asset_class(holding, "corporate_bonds")

    def calculate_business_loans(self, holding: Dict[str, Any]) -> Dict[str, Any]:
        """Business Loans & SME Loans: balance sheet attribution (PCAF Table 5.2)."""
        return self._calculate_standard_asset_class(holding, "business_loans")

    def calculate_project_finance(self, holding: Dict[str, Any]) -> Dict[str, Any]:
        """Project Finance: project cost attribution (PCAF Table 5.3)."""
        return self._calculate_standard_asset_class(holding, "project_finance")

    def calculate_commercial_re(self, holding: Dict[str, Any]) -> Dict[str, Any]:
        """Commercial Real Estate: property value, LTV-adjusted (PCAF Table 5.4)."""
        return self._calculate_standard_asset_class(holding, "commercial_real_estate")

    def calculate_mortgages(self, holding: Dict[str, Any]) -> Dict[str, Any]:
        """Residential Mortgages: property value, EPC-weighted (PCAF Table 5.5)."""
        outstanding = float(holding.get("outstanding_amount_eur", 0))
        property_value = float(holding.get("property_value_eur", 0))
        epc = holding.get("epc_rating", "D")
        floor_area = float(holding.get("floor_area_m2", 80))
        country = holding.get("country_iso", "DE")

        af = min(outstanding / property_value, 1.0) if property_value > 0 else 1.0
        kgco2_m2 = MORTGAGE_EPC_FACTORS.get(epc, 65.0)
        annual_tco2e = (floor_area * kgco2_m2) / 1000.0

        s1 = annual_tco2e * 0.4  # gas heating
        s2 = annual_tco2e * 0.6  # electricity
        financed_s1 = round(af * s1, 4)
        financed_s2 = round(af * s2, 4)
        financed_total = round(financed_s1 + financed_s2, 4)

        dqs = derive_dqs_auto(
            has_physical_activity=(floor_area > 0 and epc != "D"),
            has_revenue=False,
            asset_class="mortgages",
        )

        return {
            "asset_class": "mortgages",
            "entity_name": holding.get("entity_name", ""),
            "outstanding_eur": outstanding,
            "property_value_eur": property_value,
            "epc_rating": epc,
            "floor_area_m2": floor_area,
            "attribution_factor": round(af, 6),
            "annual_building_tco2e": round(annual_tco2e, 4),
            "financed_scope1_tco2e": financed_s1,
            "financed_scope2_tco2e": financed_s2,
            "financed_total_tco2e": financed_total,
            "pcaf_dqs": dqs,
            "methodology": f"PCAF Table 5.5: AF={af:.4f} x ({floor_area}m2 x {kgco2_m2}kgCO2/m2)",
        }

    def calculate_vehicle_loans(self, holding: Dict[str, Any]) -> Dict[str, Any]:
        """Motor Vehicle Loans: vehicle value, fuel type EF (PCAF Table 5.6)."""
        outstanding = float(holding.get("outstanding_amount_eur", 0))
        vehicle_value = float(holding.get("vehicle_value_eur", 0))
        fuel_type = holding.get("fuel_type", "petrol")
        annual_km = float(holding.get("annual_km", 0))

        af = min(outstanding / vehicle_value, 1.0) if vehicle_value > 0 else 1.0
        fuel_data = VEHICLE_EMISSION_FACTORS.get(fuel_type, VEHICLE_EMISSION_FACTORS.get("petrol", {"gco2_per_km": 170.0, "annual_km_default": 12000}))
        gco2_km = fuel_data["gco2_per_km"]
        km = annual_km if annual_km > 0 else fuel_data["annual_km_default"]

        annual_tco2e = (km * gco2_km) / 1_000_000.0
        is_electric = fuel_type in ("bev", "h2_fcev")

        s1 = 0.0 if is_electric else annual_tco2e
        s2 = annual_tco2e if is_electric else 0.0
        if fuel_type == "phev":
            s1 = annual_tco2e * 0.5
            s2 = annual_tco2e * 0.5

        financed_s1 = round(af * s1, 4)
        financed_s2 = round(af * s2, 4)
        financed_total = round(financed_s1 + financed_s2, 4)

        dqs = derive_dqs_auto(has_physical_activity=True, asset_class="vehicle_loans")

        return {
            "asset_class": "vehicle_loans",
            "entity_name": holding.get("entity_name", ""),
            "outstanding_eur": outstanding,
            "vehicle_value_eur": vehicle_value,
            "fuel_type": fuel_type,
            "annual_km": km,
            "attribution_factor": round(af, 6),
            "annual_vehicle_tco2e": round(annual_tco2e, 4),
            "financed_scope1_tco2e": financed_s1,
            "financed_scope2_tco2e": financed_s2,
            "financed_total_tco2e": financed_total,
            "pcaf_dqs": dqs,
            "methodology": f"PCAF Table 5.6: AF={af:.4f} x ({km:.0f}km x {gco2_km}gCO2/km)",
        }

    def calculate_sovereign_bonds(self, holding: Dict[str, Any]) -> Dict[str, Any]:
        """Sovereign Bonds: GDP-proportional, production-based (PCAF Table 5.7)."""
        outstanding = float(holding.get("outstanding_amount_eur", 0))
        country = holding.get("country_iso", "US").upper()

        from decimal import Decimal
        gdp = _SOVEREIGN_GDP_EUR.get(country)
        gdp_f = float(gdp) if gdp else 0.0
        af = min(outstanding / gdp_f, 1.0) if gdp_f > 0 else 0.0

        production_mtco2 = SOVEREIGN_PRODUCTION_EMISSIONS.get(country, 300.0)
        production_tco2 = production_mtco2 * 1_000_000.0

        financed_tco2e = round(af * production_tco2, 4)
        dqs = derive_dqs_auto(has_revenue=True, asset_class="sovereign_bonds")

        return {
            "asset_class": "sovereign_bonds",
            "country_iso": country,
            "outstanding_eur": outstanding,
            "country_gdp_eur": gdp_f,
            "production_emissions_mtco2e": production_mtco2,
            "attribution_factor": round(af, 10),
            "financed_scope1_tco2e": financed_tco2e,
            "financed_scope2_tco2e": 0.0,
            "financed_total_tco2e": financed_tco2e,
            "pcaf_dqs": dqs,
            "methodology": f"PCAF Table 5.7: AF={af:.10f} x {production_mtco2}Mt production emissions",
        }

    def calculate_unlisted_equity(self, holding: Dict[str, Any]) -> Dict[str, Any]:
        """Unlisted Equity: EVIC proxy with size premium (PCAF Table 5.8)."""
        outstanding = float(holding.get("outstanding_amount_eur", 0))
        evic = float(holding.get("enterprise_value_eur", 0))
        total_equity = float(holding.get("total_equity_eur", 0))
        total_debt = float(holding.get("total_debt_eur", 0))

        # Use EVIC if available, otherwise balance sheet proxy with 15% size premium
        if evic > 0:
            denom = evic
            method_note = "EVIC"
        elif (total_equity + total_debt) > 0:
            denom = (total_equity + total_debt) * 0.85  # 15% illiquidity discount
            method_note = "Balance sheet proxy (0.85x for illiquidity)"
        else:
            denom = outstanding
            method_note = "Fallback: outstanding = denominator"

        af = min(outstanding / denom, 1.0) if denom > 0 else 1.0
        return self._apply_af_and_emissions(holding, af, "unlisted_equity", method_note)

    def calculate_infrastructure(self, holding: Dict[str, Any]) -> Dict[str, Any]:
        """Infrastructure Finance: project lifecycle attribution."""
        outstanding = float(holding.get("outstanding_amount_eur", 0))
        project_cost = float(holding.get("total_project_cost_eur", 0))
        infra_type = holding.get("infrastructure_type", "other")

        af = min(outstanding / project_cost, 1.0) if project_cost > 0 else 1.0
        ef = INFRASTRUCTURE_EF.get(infra_type, 100.0)
        project_m = project_cost / 1_000_000.0

        annual_tco2e = project_m * ef
        financed_s1 = round(af * annual_tco2e * 0.7, 4)
        financed_s2 = round(af * annual_tco2e * 0.3, 4)
        financed_total = round(financed_s1 + financed_s2, 4)

        dqs = derive_dqs_auto(
            has_physical_activity=(infra_type != "other"),
            asset_class="infrastructure",
        )

        return {
            "asset_class": "infrastructure",
            "entity_name": holding.get("entity_name", ""),
            "outstanding_eur": outstanding,
            "total_project_cost_eur": project_cost,
            "infrastructure_type": infra_type,
            "attribution_factor": round(af, 6),
            "lifecycle_ef_tco2e_per_m": ef,
            "financed_scope1_tco2e": financed_s1,
            "financed_scope2_tco2e": financed_s2,
            "financed_total_tco2e": financed_total,
            "pcaf_dqs": dqs,
            "methodology": f"PCAF Table 5.3 ext: AF={af:.4f} x lifecycle EF ({ef} tCO2e/MEUR)",
        }

    def calculate_green_bonds(self, holding: Dict[str, Any]) -> Dict[str, Any]:
        """Green Bonds: use-of-proceeds allocation."""
        outstanding = float(holding.get("outstanding_amount_eur", 0))
        total_issuance = float(holding.get("total_issuance_eur", 0))
        uop_category = holding.get("use_of_proceeds", "general_green")
        taxonomy_aligned_pct = float(holding.get("eu_taxonomy_aligned_pct", 0))

        af = min(outstanding / total_issuance, 1.0) if total_issuance > 0 else 1.0

        # Green bonds: calculate avoided emissions, not absolute
        avoided_ef = GREEN_BOND_UOP_FACTORS.get(uop_category, 120.0)
        out_m = outstanding / 1_000_000.0
        avoided_tco2e = round(af * out_m * avoided_ef, 4)

        # Residual financed emissions (assume 20% of standard corporate)
        sector = holding.get("sector_gics", "Financials")
        sector_ef = SECTOR_EMISSION_INTENSITIES.get(sector, 12.0)
        residual_total = round(out_m * sector_ef * 0.2, 4)

        return {
            "asset_class": "green_bonds",
            "entity_name": holding.get("entity_name", ""),
            "outstanding_eur": outstanding,
            "total_issuance_eur": total_issuance,
            "use_of_proceeds": uop_category,
            "eu_taxonomy_aligned_pct": taxonomy_aligned_pct,
            "attribution_factor": round(af, 6),
            "avoided_emissions_tco2e": avoided_tco2e,
            "residual_financed_tco2e": residual_total,
            "financed_scope1_tco2e": round(residual_total * 0.6, 4),
            "financed_scope2_tco2e": round(residual_total * 0.4, 4),
            "financed_total_tco2e": residual_total,
            "net_emissions_tco2e": round(residual_total - avoided_tco2e, 4),
            "pcaf_dqs": 3,
            "methodology": (
                f"Green bond UoP ({uop_category}): avoided {avoided_ef} tCO2e/MEUR, "
                f"residual 20% of sector EF"
            ),
        }

    # ──────────────────────────────────────────────────────────────────────────
    # B) INSURANCE-ASSOCIATED EMISSIONS — PCAF Part B (complete)
    # ──────────────────────────────────────────────────────────────────────────

    def calculate_insurance(
        self, policies: List[InsuranceHoldingInput]
    ) -> PortfolioInsuranceResult:
        """
        Calculate insurance-associated emissions for all lines of business.

        Supports: motor, property, commercial, life/health, marine, energy,
        liability, reinsurance.
        """
        result = PortfolioInsuranceResult()
        result.total_policies = len(policies)

        gwp_weighted_dqs_sum = 0.0
        total_gwp = 0.0

        for p in policies:
            hr = self._calculate_insurance_policy(p)
            result.policy_results.append(asdict(hr))
            result.total_insured_tco2e += hr.total_tco2e
            result.scope1_total += hr.scope1_tco2e
            result.scope2_total += hr.scope2_tco2e
            result.total_gwp_eur += hr.gwp_eur

            gwp_weighted_dqs_sum += hr.pcaf_dqs * hr.gwp_eur
            total_gwp += hr.gwp_eur

            lob = hr.line_of_business
            if lob not in result.by_lob:
                result.by_lob[lob] = {"count": 0, "tco2e": 0.0, "gwp_eur": 0.0}
            result.by_lob[lob]["count"] += 1
            result.by_lob[lob]["tco2e"] += hr.total_tco2e
            result.by_lob[lob]["gwp_eur"] += hr.gwp_eur

        if total_gwp > 0:
            result.weighted_dqs = round(gwp_weighted_dqs_sum / total_gwp, 2)
            result.intensity_tco2e_per_m_premium = round(
                result.total_insured_tco2e / (total_gwp / 1_000_000.0), 2
            ) if total_gwp > 0 else 0.0

        result.total_insured_tco2e = round(result.total_insured_tco2e, 4)
        result.scope1_total = round(result.scope1_total, 4)
        result.scope2_total = round(result.scope2_total, 4)
        return result

    def _calculate_insurance_policy(self, p: InsuranceHoldingInput) -> InsuranceHoldingResult:
        """Route to the correct LoB calculation method."""
        lob = p.line_of_business
        warnings: List[str] = []

        # Direct override
        if p.scope1_tco2e is not None and p.scope2_tco2e is not None:
            return InsuranceHoldingResult(
                policy_id=p.policy_id, line_of_business=lob,
                policyholder_name=p.policyholder_name,
                attribution_method="Direct policyholder emissions",
                scope1_tco2e=p.scope1_tco2e, scope2_tco2e=p.scope2_tco2e,
                total_tco2e=p.scope1_tco2e + p.scope2_tco2e,
                gwp_eur=p.gross_written_premium_eur,
                intensity_tco2e_per_m_premium=round(
                    (p.scope1_tco2e + p.scope2_tco2e) / max(p.gross_written_premium_eur / 1e6, 0.001), 2
                ),
                pcaf_dqs=p.pcaf_dqs_override or 2,
                methodology_note="Direct reported emissions data",
            )

        # Motor
        if lob in ("motor_personal", "motor_commercial"):
            return self._ins_motor(p, warnings)
        # Property
        if lob in ("property_residential", "property_commercial"):
            return self._ins_property(p, warnings)
        # Commercial (liability, other)
        if lob in ("commercial_liability", "commercial_other"):
            return self._ins_commercial(p, warnings)
        # Marine
        if lob == "commercial_marine":
            return self._ins_marine(p, warnings)
        # Energy
        if lob == "commercial_energy":
            return self._ins_energy(p, warnings)
        # Life / Health (disclosure-only)
        if lob in ("life", "health"):
            return self._ins_life_health(p, warnings)
        # Reinsurance
        if lob == "reinsurance":
            return self._ins_reinsurance(p, warnings)
        # Liability (sector proxy)
        if lob == "liability":
            return self._ins_liability(p, warnings)

        # Fallback: premium proxy
        factor = INSURANCE_LOB_FACTORS.get(lob, 65.0)
        gwp_m = p.gross_written_premium_eur / 1_000_000.0
        total = round(gwp_m * factor, 4)
        return InsuranceHoldingResult(
            policy_id=p.policy_id, line_of_business=lob,
            policyholder_name=p.policyholder_name,
            attribution_method=f"Premium proxy: {factor} tCO2e/$M GWP",
            scope1_tco2e=round(total * 0.6, 4),
            scope2_tco2e=round(total * 0.4, 4),
            total_tco2e=total, gwp_eur=p.gross_written_premium_eur,
            intensity_tco2e_per_m_premium=factor,
            pcaf_dqs=5, methodology_note=f"Premium-weighted fallback ({lob})",
            warnings=["Unknown LoB — used premium proxy"],
        )

    def _ins_motor(self, p: InsuranceHoldingInput, w: List[str]) -> InsuranceHoldingResult:
        """Motor: fleet emissions = vehicles x km x gCO2/km."""
        fuel_data = VEHICLE_EMISSION_FACTORS.get(
            p.fuel_type, VEHICLE_EMISSION_FACTORS.get("petrol", {"gco2_per_km": 170.0, "annual_km_default": 12000})
        )
        gco2_km = fuel_data["gco2_per_km"]
        km = p.annual_km_per_vehicle if p.annual_km_per_vehicle > 0 else fuel_data["annual_km_default"]
        vehicles = max(p.vehicle_count, 1)

        total_tco2e = (vehicles * km * gco2_km) / 1_000_000.0
        is_electric = p.fuel_type in ("bev", "h2_fcev")
        s1 = 0.0 if is_electric else total_tco2e
        s2 = total_tco2e if is_electric else 0.0
        if p.fuel_type == "phev":
            s1 = total_tco2e * 0.5
            s2 = total_tco2e * 0.5

        gwp_m = max(p.gross_written_premium_eur / 1e6, 0.001)
        return InsuranceHoldingResult(
            policy_id=p.policy_id, line_of_business=p.line_of_business,
            policyholder_name=p.policyholder_name,
            attribution_method=f"PCAF Part B Motor: {vehicles} vehicles x {km:.0f}km x {gco2_km}gCO2/km",
            scope1_tco2e=round(s1, 4), scope2_tco2e=round(s2, 4),
            total_tco2e=round(total_tco2e, 4), gwp_eur=p.gross_written_premium_eur,
            intensity_tco2e_per_m_premium=round(total_tco2e / gwp_m, 2),
            pcaf_dqs=p.pcaf_dqs_override or 3,
            methodology_note=f"Fleet emission model: {p.fuel_type}",
        )

    def _ins_property(self, p: InsuranceHoldingInput, w: List[str]) -> InsuranceHoldingResult:
        """Property: area x kgCO2/m2 by EPC rating."""
        if p.insured_area_m2 > 0:
            bld_data = BUILDING_EMISSION_FACTORS.get(
                p.epc_rating, BUILDING_EMISSION_FACTORS.get("D", {"kgco2_per_m2": 75.0})
            )
            kgco2_m2 = bld_data["kgco2_per_m2"]
            total_tco2e = (p.insured_area_m2 * kgco2_m2) / 1000.0
            method = f"PCAF Part B Property: {p.insured_area_m2:.0f}m2 x {kgco2_m2}kgCO2/m2 (EPC {p.epc_rating})"
            dqs = p.pcaf_dqs_override or 3
        else:
            factor = INSURANCE_LOB_FACTORS.get(p.line_of_business, 40.0)
            gwp_m = p.gross_written_premium_eur / 1_000_000.0
            total_tco2e = gwp_m * factor
            method = f"PCAF Part B Property: premium proxy {factor} tCO2e/$M GWP"
            dqs = p.pcaf_dqs_override or 5
            w.append("No property area — used premium proxy")

        s1 = round(total_tco2e * 0.4, 4)
        s2 = round(total_tco2e * 0.6, 4)
        gwp_m = max(p.gross_written_premium_eur / 1e6, 0.001)
        return InsuranceHoldingResult(
            policy_id=p.policy_id, line_of_business=p.line_of_business,
            policyholder_name=p.policyholder_name,
            attribution_method=method, scope1_tco2e=s1, scope2_tco2e=s2,
            total_tco2e=round(total_tco2e, 4), gwp_eur=p.gross_written_premium_eur,
            intensity_tco2e_per_m_premium=round(total_tco2e / gwp_m, 2),
            pcaf_dqs=dqs, methodology_note=method, warnings=w,
        )

    def _ins_commercial(self, p: InsuranceHoldingInput, w: List[str]) -> InsuranceHoldingResult:
        """Commercial: sector-revenue intensity or premium proxy."""
        if p.insured_revenue_eur and p.insured_revenue_eur > 0:
            sector = p.policyholder_sector or "Unknown"
            intensity = SECTOR_EMISSION_INTENSITIES.get(sector, 150.0)
            rev_m = p.insured_revenue_eur / 1_000_000.0
            total_tco2e = rev_m * intensity
            method = f"PCAF Part B Commercial: {rev_m:.1f}MEUR revenue x {intensity} tCO2e/MEUR"
            dqs = p.pcaf_dqs_override or 4
        else:
            factor = INSURANCE_LOB_FACTORS.get(p.line_of_business, 65.0)
            gwp_m = p.gross_written_premium_eur / 1_000_000.0
            total_tco2e = gwp_m * factor
            method = f"PCAF Part B Commercial: premium proxy {factor} tCO2e/$M GWP"
            dqs = p.pcaf_dqs_override or 5
            w.append("No revenue data — used premium proxy")

        s1 = round(total_tco2e * 0.6, 4)
        s2 = round(total_tco2e * 0.4, 4)
        gwp_m = max(p.gross_written_premium_eur / 1e6, 0.001)
        return InsuranceHoldingResult(
            policy_id=p.policy_id, line_of_business=p.line_of_business,
            policyholder_name=p.policyholder_name,
            attribution_method=method, scope1_tco2e=s1, scope2_tco2e=s2,
            total_tco2e=round(total_tco2e, 4), gwp_eur=p.gross_written_premium_eur,
            intensity_tco2e_per_m_premium=round(total_tco2e / gwp_m, 2),
            pcaf_dqs=dqs, methodology_note=method, warnings=w,
        )

    def _ins_marine(self, p: InsuranceHoldingInput, w: List[str]) -> InsuranceHoldingResult:
        """Marine Insurance: vessel emissions (IMO DCS data x fleet composition)."""
        vessel_ef = MARINE_VESSEL_FACTORS.get(p.vessel_type, 8000.0)
        vessels = max(p.vessel_count, 1)
        total_tco2e = vessels * vessel_ef

        # Premium-weighted attribution: insurer share = GWP / estimated hull+P&I value
        gwp_m = max(p.gross_written_premium_eur / 1e6, 0.001)
        method = f"PCAF Part B Marine: {vessels} x {p.vessel_type} ({vessel_ef} tCO2e/vessel/yr)"

        return InsuranceHoldingResult(
            policy_id=p.policy_id, line_of_business="commercial_marine",
            policyholder_name=p.policyholder_name,
            attribution_method=method,
            scope1_tco2e=round(total_tco2e, 4), scope2_tco2e=0.0,
            total_tco2e=round(total_tco2e, 4), gwp_eur=p.gross_written_premium_eur,
            intensity_tco2e_per_m_premium=round(total_tco2e / gwp_m, 2),
            pcaf_dqs=p.pcaf_dqs_override or 4,
            methodology_note=method,
        )

    def _ins_energy(self, p: InsuranceHoldingInput, w: List[str]) -> InsuranceHoldingResult:
        """Energy Insurance: asset-level generation emissions."""
        tech_ef = ENERGY_ASSET_FACTORS.get(p.technology, 2800.0)
        cf = p.capacity_factor if p.capacity_factor > 0 else 0.45
        mw = max(p.capacity_mw, 1.0)

        # Annual emissions = capacity x CF x technology EF
        total_tco2e = mw * cf * tech_ef / 1000.0  # normalise per MW factor
        # Actually: EF is tCO2e per MW per year at 100% CF, scale by CF
        total_tco2e = mw * tech_ef * cf

        gwp_m = max(p.gross_written_premium_eur / 1e6, 0.001)
        method = f"PCAF Part B Energy: {mw:.0f}MW {p.technology} x CF={cf:.2f} x {tech_ef} tCO2e/MW/yr"

        return InsuranceHoldingResult(
            policy_id=p.policy_id, line_of_business="commercial_energy",
            policyholder_name=p.policyholder_name,
            attribution_method=method,
            scope1_tco2e=round(total_tco2e, 4), scope2_tco2e=0.0,
            total_tco2e=round(total_tco2e, 4), gwp_eur=p.gross_written_premium_eur,
            intensity_tco2e_per_m_premium=round(total_tco2e / gwp_m, 2),
            pcaf_dqs=p.pcaf_dqs_override or 3,
            methodology_note=method,
        )

    def _ins_life_health(self, p: InsuranceHoldingInput, w: List[str]) -> InsuranceHoldingResult:
        """Life & Health: disclosure-only per PCAF (no insured emissions)."""
        factor = INSURANCE_LOB_FACTORS.get(p.line_of_business, 5.0)
        gwp_m = p.gross_written_premium_eur / 1_000_000.0
        total_tco2e = round(gwp_m * factor, 4)
        w.append("Life/health: PCAF disclosure-only — proxy estimate for transparency")

        return InsuranceHoldingResult(
            policy_id=p.policy_id, line_of_business=p.line_of_business,
            policyholder_name=p.policyholder_name,
            attribution_method="PCAF Part B: Life/Health disclosure-only proxy",
            scope1_tco2e=round(total_tco2e * 0.3, 4),
            scope2_tco2e=round(total_tco2e * 0.7, 4),
            total_tco2e=total_tco2e, gwp_eur=p.gross_written_premium_eur,
            intensity_tco2e_per_m_premium=factor,
            pcaf_dqs=5,
            methodology_note="Disclosure-only: no direct attribution per PCAF guidance",
            warnings=w,
        )

    def _ins_reinsurance(self, p: InsuranceHoldingInput, w: List[str]) -> InsuranceHoldingResult:
        """Reinsurance: proportional/non-proportional cedant aggregation."""
        # Reinsurance: aggregate cedant portfolio emissions x treaty share
        # Using premium-based proxy as cedant-level data is rarely available
        factor = 75.0  # blended all-lines tCO2e per $M premium
        gwp_m = p.gross_written_premium_eur / 1_000_000.0
        total_tco2e = round(gwp_m * factor, 4)
        w.append("Reinsurance: premium-weighted cedant aggregation proxy")

        return InsuranceHoldingResult(
            policy_id=p.policy_id, line_of_business="reinsurance",
            policyholder_name=p.policyholder_name,
            attribution_method=f"Reinsurance premium proxy: {factor} tCO2e/$M GWP",
            scope1_tco2e=round(total_tco2e * 0.5, 4),
            scope2_tco2e=round(total_tco2e * 0.5, 4),
            total_tco2e=total_tco2e, gwp_eur=p.gross_written_premium_eur,
            intensity_tco2e_per_m_premium=factor,
            pcaf_dqs=5,
            methodology_note="Proportional cedant aggregation via premium proxy",
            warnings=w,
        )

    def _ins_liability(self, p: InsuranceHoldingInput, w: List[str]) -> InsuranceHoldingResult:
        """Liability Insurance: sector-revenue proxy."""
        return self._ins_commercial(p, w)

    # ──────────────────────────────────────────────────────────────────────────
    # C) FACILITATED EMISSIONS — PCAF Part C (delegate)
    # ──────────────────────────────────────────────────────────────────────────

    def calculate_facilitated(
        self, deals: List[FacilitatedDealInput]
    ) -> Tuple[List[FacDealResult], PortfolioFacilitatedSummary]:
        """Delegate to existing FacilitatedEmissionsEngine."""
        return self._facilitated_engine.calculate_facilitated_batch(deals)

    # ──────────────────────────────────────────────────────────────────────────
    # D) PORTFOLIO-LEVEL ORCHESTRATION
    # ──────────────────────────────────────────────────────────────────────────

    def calculate_portfolio(
        self,
        holdings: List[Dict[str, Any]],
        insurance_policies: Optional[List[InsuranceHoldingInput]] = None,
        facilitated_deals: Optional[List[FacilitatedDealInput]] = None,
        prior_year_emissions: Optional[float] = None,
    ) -> UnifiedPortfolioResult:
        """
        Run all asset classes, aggregate, and produce comprehensive portfolio metrics.

        Parameters
        ----------
        holdings : list[dict]
            Part A holdings. Each dict must include asset_class plus class-specific fields.
        insurance_policies : list[InsuranceHoldingInput], optional
            Part B insurance policies.
        facilitated_deals : list[FacilitatedDealInput], optional
            Part C capital markets deals.
        prior_year_emissions : float, optional
            Previous year total emissions for YoY delta.

        Returns
        -------
        UnifiedPortfolioResult with full metrics, concentration, and disclosures.
        """
        now = datetime.now(timezone.utc).isoformat()
        result = UnifiedPortfolioResult(calculation_timestamp=now)

        # ── Part A: Financed Emissions ────────────────────────────────────────
        part_a_results = []
        for h in holdings:
            ac = h.get("asset_class", "listed_equity")
            try:
                calc_fn = self._get_asset_class_calculator(ac)
                r = calc_fn(h)
                part_a_results.append(r)
            except Exception as exc:
                logger.error("Part A calculation failed for %s: %s", h.get("entity_name", "?"), exc)
                part_a_results.append({
                    "asset_class": ac, "entity_name": h.get("entity_name", "?"),
                    "error": str(exc), "financed_total_tco2e": 0.0,
                })

        # Aggregate Part A
        a_s1 = sum(r.get("financed_scope1_tco2e", 0.0) for r in part_a_results)
        a_s2 = sum(r.get("financed_scope2_tco2e", 0.0) for r in part_a_results)
        a_s3 = sum(r.get("financed_scope3_tco2e", 0.0) for r in part_a_results)
        a_total = sum(r.get("financed_total_tco2e", 0.0) for r in part_a_results)
        a_aum = sum(r.get("outstanding_eur", 0.0) for r in part_a_results)
        a_covered = sum(
            r.get("outstanding_eur", 0.0) for r in part_a_results
            if r.get("financed_total_tco2e", 0.0) > 0
        )

        # WACI (using revenue where available)
        waci_s12 = 0.0
        waci_s123 = 0.0
        if a_aum > 0:
            for h, r in zip(holdings, part_a_results):
                weight = r.get("outstanding_eur", 0.0) / a_aum
                rev = float(h.get("annual_revenue_eur", 0))
                rev_m = rev / 1_000_000.0 if rev > 0 else 0.0
                if rev_m > 0:
                    s1_raw = float(h.get("scope1_co2e_tonnes", 0))
                    s2_raw = float(h.get("scope2_co2e_tonnes", 0))
                    s3_raw = float(h.get("scope3_co2e_tonnes", 0))
                    waci_s12 += weight * (s1_raw + s2_raw) / rev_m
                    waci_s123 += weight * (s1_raw + s2_raw + s3_raw) / rev_m

        # DQS weighted
        dqs_sum = sum(r.get("pcaf_dqs", 5) * r.get("outstanding_eur", 0.0) for r in part_a_results)
        portfolio_dqs = round(dqs_sum / a_aum, 2) if a_aum > 0 else 5.0

        # Temperature
        temperature = self._interpolate_temperature(waci_s12)

        # Carbon footprint
        a_aum_m = a_aum / 1_000_000.0
        carbon_fp = round(a_total / a_aum_m, 2) if a_aum_m > 0 else 0.0

        result.financed_emissions = {
            "scope1_tco2e": round(a_s1, 2),
            "scope2_tco2e": round(a_s2, 2),
            "scope3_tco2e": round(a_s3, 2),
            "total_tco2e": round(a_total, 2),
            "holdings_count": len(part_a_results),
            "aum_eur": a_aum,
            "results": part_a_results,
        }

        # ── Part B: Insurance ─────────────────────────────────────────────────
        ins_result = None
        if insurance_policies:
            ins_result = self.calculate_insurance(insurance_policies)
            result.insurance_emissions = asdict(ins_result)

        # ── Part C: Facilitated ───────────────────────────────────────────────
        fac_results = None
        fac_summary = None
        if facilitated_deals:
            fac_results, fac_summary = self.calculate_facilitated(facilitated_deals)
            result.facilitated_emissions = asdict(fac_summary)

        # ── Aggregate All Parts ───────────────────────────────────────────────
        result.total_scope1_tco2e = round(a_s1 + (ins_result.scope1_total if ins_result else 0.0), 2)
        result.total_scope2_tco2e = round(a_s2 + (ins_result.scope2_total if ins_result else 0.0), 2)
        result.total_scope3_tco2e = round(a_s3, 2)
        fac_total = fac_summary.total_facilitated_tco2e if fac_summary else 0.0
        ins_total = ins_result.total_insured_tco2e if ins_result else 0.0
        result.total_emissions_tco2e = round(a_total + ins_total + fac_total, 2)
        result.waci_scope12 = round(waci_s12, 3)
        result.waci_scope123 = round(waci_s123, 3)
        result.carbon_footprint_tco2e_per_m_eur = carbon_fp
        result.implied_temperature_c = temperature
        result.portfolio_dqs = portfolio_dqs
        result.coverage_pct = round((a_covered / a_aum * 100) if a_aum > 0 else 0.0, 2)
        result.total_aum_eur = a_aum

        # Concentration: top-10 emitters
        sorted_results = sorted(part_a_results, key=lambda x: x.get("financed_total_tco2e", 0.0), reverse=True)
        result.top_10_emitters = [
            {
                "entity_name": r.get("entity_name", ""),
                "asset_class": r.get("asset_class", ""),
                "financed_tco2e": r.get("financed_total_tco2e", 0.0),
                "pct_of_total": round(
                    r.get("financed_total_tco2e", 0.0) / a_total * 100, 2
                ) if a_total > 0 else 0.0,
            }
            for r in sorted_results[:10]
        ]

        # Sector breakdown
        for r in part_a_results:
            ac = r.get("asset_class", "other")
            if ac not in result.asset_class_breakdown:
                result.asset_class_breakdown[ac] = {"count": 0, "tco2e": 0.0, "aum_eur": 0.0}
            result.asset_class_breakdown[ac]["count"] += 1
            result.asset_class_breakdown[ac]["tco2e"] += r.get("financed_total_tco2e", 0.0)
            result.asset_class_breakdown[ac]["aum_eur"] += r.get("outstanding_eur", 0.0)

        # YoY delta
        if prior_year_emissions is not None and prior_year_emissions > 0:
            delta_abs = a_total - prior_year_emissions
            delta_pct = round((delta_abs / prior_year_emissions) * 100, 2)
            result.yoy_delta = {
                "prior_year_tco2e": prior_year_emissions,
                "current_year_tco2e": round(a_total, 2),
                "absolute_change_tco2e": round(delta_abs, 2),
                "pct_change": delta_pct,
                "direction": "decrease" if delta_abs < 0 else "increase",
            }

        return result

    # ──────────────────────────────────────────────────────────────────────────
    # D.2) REGULATORY DISCLOSURE GENERATION
    # ──────────────────────────────────────────────────────────────────────────

    def generate_regulatory_disclosures(
        self, portfolio: UnifiedPortfolioResult
    ) -> RegulatoryDisclosurePackage:
        """
        Produce disclosure-ready outputs for 7 regulatory/voluntary frameworks.

        Returns a RegulatoryDisclosurePackage with SFDR PAI, EU Taxonomy Art. 8,
        TCFD, CSRD ESRS E1, ISSB S2, GRI 305, and NZBA sections.
        """
        now = datetime.now(timezone.utc).isoformat()
        pkg = RegulatoryDisclosurePackage(generated_at=now)
        fe = portfolio.financed_emissions
        aum = portfolio.total_aum_eur

        # ── SFDR PAI 1-5 (mandatory) + PAI 6-14 (opt-in) ─────────────────────
        pkg.sfdr_pai = {
            "pai_1_ghg_emissions": {
                "scope_1_tco2e": fe.get("scope1_tco2e", 0.0),
                "scope_2_tco2e": fe.get("scope2_tco2e", 0.0),
                "scope_3_tco2e": fe.get("scope3_tco2e", 0.0),
                "total_tco2e": fe.get("total_tco2e", 0.0),
                "unit": "tCO2e", "reference": "SFDR RTS Annex I Table 1 Row 1",
            },
            "pai_2_carbon_footprint": {
                "value": portfolio.carbon_footprint_tco2e_per_m_eur,
                "unit": "tCO2e per EUR million invested",
                "aum_eur": aum,
                "reference": "SFDR RTS Annex I Table 1 Row 2",
            },
            "pai_3_ghg_intensity": {
                "waci_scope12": portfolio.waci_scope12,
                "waci_scope123": portfolio.waci_scope123,
                "unit": "tCO2e per EUR million revenue",
                "reference": "SFDR RTS Annex I Table 1 Row 3",
            },
            "pai_4_fossil_fuel_exposure": {
                "note": "Requires GICS-level sector mapping per holding",
                "reference": "SFDR RTS Annex I Table 1 Row 4",
            },
            "pai_5_non_renewable_energy": {
                "note": "Requires investee energy consumption data",
                "reference": "SFDR RTS Annex I Table 1 Row 5",
            },
            "pai_6_to_14_optional": {
                "pai_6_energy_intensity_per_sector": "Sector WACI from Part A breakdown",
                "pai_7_biodiversity_sensitive": "Cross-reference with TNFD LEAP",
                "pai_8_water_emissions": "Requires investee water data",
                "pai_9_hazardous_waste": "Requires investee waste data",
                "pai_10_ungc_oecd_violations": "Cross-reference with engagement tracker",
                "pai_11_ungc_oecd_compliance_processes": "Requires investee governance data",
                "pai_12_gender_pay_gap": "Requires investee ESRS S1 data",
                "pai_13_board_gender_diversity": "Requires investee governance data",
                "pai_14_controversy_weapons": "Cross-reference with exclusion screening",
            },
            "data_quality": {
                "portfolio_weighted_dqs": portfolio.portfolio_dqs,
                "coverage_pct": portfolio.coverage_pct,
            },
        }

        # ── EU Taxonomy Art. 8 KPIs ───────────────────────────────────────────
        # Simplified: GAR denominator = total covered assets
        pkg.eu_taxonomy_art8 = {
            "gar_denominator_eur": aum,
            "gar_numerator_note": "Requires activity-level taxonomy eligibility + DNSH",
            "btar_note": "Banking book taxonomy alignment ratio — requires activity-level data",
            "capex_ratio_note": "Requires investee CapEx EU Taxonomy alignment data",
            "asset_class_breakdown": portfolio.asset_class_breakdown,
            "reference": "EU Taxonomy Regulation 2020/852, Art. 8 delegated act",
        }

        # ── TCFD Metrics & Targets ────────────────────────────────────────────
        pkg.tcfd_metrics = {
            "carbon_metrics": {
                "absolute_emissions_tco2e": portfolio.total_emissions_tco2e,
                "carbon_footprint_tco2e_per_m_eur": portfolio.carbon_footprint_tco2e_per_m_eur,
                "waci_tco2e_per_m_eur_revenue": portfolio.waci_scope12,
            },
            "physical_risk_note": "Cross-reference with climate risk engine physical risk scores",
            "transition_risk": {
                "implied_temperature_c": portfolio.implied_temperature_c,
                "note": "Simplified ITR proxy from WACI; full ITR requires SBTi pathway data",
            },
            "target_tracking": portfolio.yoy_delta,
            "reference": "TCFD Recommendations — Metrics & Targets, Supplemental Guidance for FIs",
        }

        # ── CSRD ESRS E1 Datapoints ──────────────────────────────────────────
        pkg.csrd_esrs_e1 = {
            "E1-1_transition_plan": "Cross-reference with transition_plan engine",
            "E1-2_policies": "Requires entity-level policy documentation",
            "E1-3_actions": "Cross-reference with improvement roadmap actions",
            "E1-4_targets": portfolio.yoy_delta,
            "E1-5_energy_consumption": "Requires investee energy data (ESRS E1-5 DP)",
            "E1-6_scope3_cat15": {
                "total_financed_emissions_tco2e": fe.get("total_tco2e", 0.0),
                "scope1_tco2e": fe.get("scope1_tco2e", 0.0),
                "scope2_tco2e": fe.get("scope2_tco2e", 0.0),
                "scope3_tco2e": fe.get("scope3_tco2e", 0.0),
                "methodology": "PCAF v2.0",
                "data_quality_score": portfolio.portfolio_dqs,
            },
            "E1-7_ghg_removals": "Not covered by PCAF — requires separate assessment",
            "E1-8_internal_carbon_pricing": "Cross-reference with carbon pricing module",
            "E1-9_financial_effects": "Cross-reference with ECL climate overlay",
            "reference": "CSRD ESRS E1 (EFRAG IG3), E1-6 para 53-58",
        }

        # ── ISSB S2 Metrics ──────────────────────────────────────────────────
        pkg.issb_s2 = {
            "scope1_tco2e": fe.get("scope1_tco2e", 0.0),
            "scope2_tco2e": fe.get("scope2_tco2e", 0.0),
            "scope3_cat15_tco2e": fe.get("total_tco2e", 0.0),
            "ghg_intensity_waci": portfolio.waci_scope12,
            "methodology": "PCAF v2.0 Global GHG Accounting Standard",
            "data_quality": portfolio.portfolio_dqs,
            "industry_specific_note": "SASB industry metrics via pcaf_quality cross-framework",
            "reference": "IFRS S2 para 29(a)(vi), Appendix B",
        }

        # ── GRI 305 (305-1 to 305-7) ─────────────────────────────────────────
        pkg.gri_305 = {
            "305-1_direct_scope1": fe.get("scope1_tco2e", 0.0),
            "305-2_indirect_scope2": fe.get("scope2_tco2e", 0.0),
            "305-3_other_indirect_scope3": {
                "category_15_investments": fe.get("total_tco2e", 0.0),
                "note": "Scope 3 Category 15 per GHG Protocol",
            },
            "305-4_ghg_intensity": portfolio.waci_scope12,
            "305-5_reduction": portfolio.yoy_delta,
            "305-6_ozone_depleting": "Not applicable to financed emissions",
            "305-7_nox_sox_emissions": "Not applicable to financed emissions",
            "methodology": "PCAF v2.0 + GHG Protocol Corporate Value Chain Standard",
            "reference": "GRI 305: Emissions 2016 (updated 2020)",
        }

        # ── NZBA Target Tracking ──────────────────────────────────────────────
        pkg.nzba_tracking = {
            "baseline_year_note": "Set baseline from first reporting year",
            "current_waci_scope12": portfolio.waci_scope12,
            "implied_temperature_c": portfolio.implied_temperature_c,
            "target_alignment": "1.5C" if portfolio.implied_temperature_c <= 1.8 else (
                "Below 2C" if portfolio.implied_temperature_c <= 2.2 else "Misaligned"
            ),
            "sector_glidepath_note": "Cross-reference with pcaf_time_series_engine for sector paths",
            "yoy_progress": portfolio.yoy_delta,
            "reference": "NZBA Guidelines for Climate Target Setting (2021)",
        }

        # Cross-framework map
        pkg.cross_framework_map = PCAF_CROSS_FRAMEWORK_MAP

        return pkg

    # ──────────────────────────────────────────────────────────────────────────
    # E) DATA QUALITY MANAGEMENT
    # ──────────────────────────────────────────────────────────────────────────

    def assess_data_quality(
        self, holdings: List[Dict[str, Any]]
    ) -> DQSAssessmentResult:
        """
        Portfolio-level DQS assessment with uncertainty estimation.

        For each holding, derives DQS from available data characteristics.
        Produces exposure-weighted portfolio DQS, distribution, and confidence bands.
        """
        result = DQSAssessmentResult()
        result.holdings_assessed = len(holdings)

        dqs_dist: Dict[int, int] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        by_ac: Dict[str, List[int]] = {}
        total_exposure = 0.0
        weighted_dqs_sum = 0.0
        total_financed = 0.0

        for h in holdings:
            outstanding = float(h.get("outstanding_amount_eur", 0))
            reported = h.get("reported_emissions")
            verified = h.get("verification_status", "none") == "verified"
            has_phys = h.get("physical_activity_data") is not None
            has_rev = float(h.get("revenue_eur", h.get("annual_revenue_eur", 0))) > 0

            dqs = derive_dqs_auto(
                has_verified_emissions=verified and reported is not None,
                has_reported_emissions=reported is not None,
                has_physical_activity=has_phys,
                has_revenue=has_rev,
            )

            dqs_dist[dqs] = dqs_dist.get(dqs, 0) + 1
            weighted_dqs_sum += dqs * outstanding
            total_exposure += outstanding

            ac = h.get("asset_class", "other")
            by_ac.setdefault(ac, []).append(dqs)

        if total_exposure > 0:
            result.portfolio_dqs = round(weighted_dqs_sum / total_exposure, 2)
        result.dqs_distribution = dqs_dist
        result.by_asset_class = {ac: round(sum(v) / len(v), 2) for ac, v in by_ac.items()}

        covered = sum(1 for h in holdings if float(h.get("outstanding_amount_eur", 0)) > 0
                      and h.get("reported_emissions") is not None)
        result.coverage_pct = round(covered / len(holdings) * 100, 1) if holdings else 0.0

        # Uncertainty estimation from DQS
        uncertainty_map = {1: 5.0, 2: 15.0, 3: 30.0, 4: 45.0, 5: 60.0}
        dqs_int = max(1, min(5, round(result.portfolio_dqs)))
        result.uncertainty_pct = uncertainty_map.get(dqs_int, 45.0)

        # Confidence bands (central +/- uncertainty%)
        central = sum(float(h.get("financed_total_tco2e", h.get("outstanding_amount_eur", 0) * 0.0001))
                       for h in holdings)
        result.confidence_band_central = round(central, 2)
        result.confidence_band_low = round(central * (1 - result.uncertainty_pct / 100), 2)
        result.confidence_band_high = round(central * (1 + result.uncertainty_pct / 100), 2)

        return result

    def generate_improvement_roadmap(
        self, holdings: List[Dict[str, Any]]
    ) -> ImprovementRoadmap:
        """
        Generate per-holding DQS gap closure actions.

        Prioritises holdings by exposure-weighted DQS improvement potential.
        """
        roadmap = ImprovementRoadmap()
        roadmap.total_holdings = len(holdings)

        dqs_sum = 0.0
        total_exp = 0.0

        scored = []
        for h in holdings:
            outstanding = float(h.get("outstanding_amount_eur", 0))
            reported = h.get("reported_emissions")
            verified = h.get("verification_status", "none") == "verified"
            has_phys = h.get("physical_activity_data") is not None
            has_rev = float(h.get("revenue_eur", h.get("annual_revenue_eur", 0))) > 0

            dqs = derive_dqs_auto(
                has_verified_emissions=verified and reported is not None,
                has_reported_emissions=reported is not None,
                has_physical_activity=has_phys,
                has_revenue=has_rev,
            )
            dqs_sum += dqs * outstanding
            total_exp += outstanding

            if dqs >= 2:  # Can improve
                scored.append((h, dqs, outstanding))

        roadmap.current_portfolio_dqs = round(dqs_sum / total_exp, 2) if total_exp > 0 else 5.0

        # Sort by impact: highest exposure x worst DQS first
        scored.sort(key=lambda x: x[2] * x[1], reverse=True)

        for h, current_dqs, exp in scored:
            target_dqs = max(1, current_dqs - 1)
            # Find matching improvement path
            path = None
            for ip in PCAF_QUALITY_IMPROVEMENT_PATHS:
                if ip["from_dqs"] == current_dqs and ip["to_dqs"] == target_dqs:
                    path = ip
                    break

            if path:
                for action_text in path["actions"]:
                    priority = "high" if exp > 10_000_000 else ("medium" if exp > 1_000_000 else "low")
                    a = ImprovementAction(
                        holding_id=h.get("holding_id", ""),
                        entity_name=h.get("entity_name", ""),
                        current_dqs=current_dqs,
                        target_dqs=target_dqs,
                        action=action_text,
                        effort=path["typical_effort"],
                        expected_uncertainty_reduction_pct=path["expected_uncertainty_reduction_pct"],
                        priority=priority,
                    )
                    roadmap.actions.append(a)
                    if path["typical_effort"].startswith("Low"):
                        roadmap.quick_wins += 1
                    if priority == "high":
                        roadmap.high_impact += 1

        # Estimate target portfolio DQS after all improvements
        if total_exp > 0:
            improved_sum = sum(
                max(1, derive_dqs_auto(
                    has_verified_emissions=h.get("verification_status") == "verified",
                    has_reported_emissions=h.get("reported_emissions") is not None,
                    has_physical_activity=h.get("physical_activity_data") is not None,
                    has_revenue=float(h.get("revenue_eur", h.get("annual_revenue_eur", 0))) > 0,
                ) - 1) * float(h.get("outstanding_amount_eur", 0))
                for h in holdings
            )
            roadmap.target_portfolio_dqs = round(improved_sum / total_exp, 2)

        return roadmap

    def estimate_uncertainty(
        self, portfolio_dqs: float, total_emissions: float
    ) -> Dict[str, Any]:
        """
        Estimate confidence bands from portfolio DQS.

        Uses PCAF's indicative uncertainty ranges:
          DQS 1: +/- 5%
          DQS 2: +/- 15%
          DQS 3: +/- 30%
          DQS 4: +/- 45%
          DQS 5: +/- 60%
        """
        uncertainty_map = {1: 5.0, 2: 15.0, 3: 30.0, 4: 45.0, 5: 60.0}
        dqs_int = max(1, min(5, round(portfolio_dqs)))
        uncertainty_pct = uncertainty_map[dqs_int]

        # Linear interpolation for non-integer DQS
        if portfolio_dqs != dqs_int and dqs_int < 5:
            frac = portfolio_dqs - dqs_int
            next_unc = uncertainty_map.get(dqs_int + 1, 60.0)
            uncertainty_pct = uncertainty_map[dqs_int] + frac * (next_unc - uncertainty_map[dqs_int])

        low = round(total_emissions * (1 - uncertainty_pct / 100), 2)
        high = round(total_emissions * (1 + uncertainty_pct / 100), 2)

        return {
            "portfolio_dqs": portfolio_dqs,
            "uncertainty_pct": round(uncertainty_pct, 1),
            "confidence_band": {
                "low_tco2e": low,
                "central_tco2e": total_emissions,
                "high_tco2e": high,
            },
            "interpretation": (
                f"With portfolio DQS {portfolio_dqs:.1f}, actual emissions are estimated "
                f"between {low:,.0f} and {high:,.0f} tCO2e (central: {total_emissions:,.0f} tCO2e)."
            ),
        }

    # ──────────────────────────────────────────────────────────────────────────
    # F) CROSS-MODULE INTEGRATION POINTS
    # ──────────────────────────────────────────────────────────────────────────

    def bridge_to_ecl(
        self,
        holdings: List[Dict[str, Any]],
        portfolio_temperature_c: float = 2.5,
    ) -> PortfolioBridgeResult:
        """
        Wire PCAF financed emissions data into the ECL Climate Overlay engine.

        Converts holdings to PCAFInvesteeProfile and delegates to pcaf_ecl_bridge.
        """
        profiles = []
        for h in holdings:
            outstanding = float(h.get("outstanding_amount_eur", 0))
            s1 = float(h.get("scope1_co2e_tonnes", h.get("financed_scope1_tco2e", 0)))
            s2 = float(h.get("scope2_co2e_tonnes", h.get("financed_scope2_tco2e", 0)))
            s3 = float(h.get("scope3_co2e_tonnes", h.get("financed_scope3_tco2e", 0)))
            rev = float(h.get("annual_revenue_eur", 0))
            rev_m = rev / 1_000_000.0 if rev > 0 else 1.0

            profile = PCAFInvesteeProfile(
                investee_name=h.get("entity_name", h.get("company_name", "")),
                sector_gics=h.get("sector_gics", ""),
                country_iso=h.get("country_iso", ""),
                financed_scope1_tco2e=s1,
                financed_scope2_tco2e=s2,
                financed_scope3_tco2e=s3,
                revenue_intensity_tco2e_per_meur=(s1 + s2) / rev_m if rev_m > 0 else 0.0,
                outstanding_eur=outstanding,
                pcaf_dq_composite=float(h.get("data_quality", h.get("pcaf_dqs", 3))),
                sbti_committed=h.get("sbti_committed", False),
                net_zero_target_year=h.get("net_zero_target_year"),
                implied_temperature_c=h.get("implied_temperature_c", 2.5),
            )
            profiles.append(profile)

        return ecl_bridge_portfolio(
            profiles,
            portfolio_temperature_c=portfolio_temperature_c,
        )

    def bridge_to_scenario_analysis(
        self,
        portfolio: UnifiedPortfolioResult,
    ) -> List[ScenarioOverlay]:
        """
        Emit climate scenario overlays from PCAF portfolio metrics.

        Maps PCAF emissions to NGFS scenario impact pathways for
        downstream scenario analysis and stress testing.
        """
        scenarios = [
            ("Net Zero 2050", 1.5, 250.0),
            ("Below 2C", 1.7, 150.0),
            ("Delayed Transition", 1.8, 200.0),
            ("Current Policies", 3.0, 50.0),
            ("Nationally Determined", 2.5, 100.0),
        ]

        overlays = []
        total_tco2e = portfolio.total_emissions_tco2e

        for name, temp, carbon_price in scenarios:
            # EL adjustment = carbon_price x total_emissions / total_aum
            aum = max(portfolio.total_aum_eur, 1.0)
            cost_impact = (carbon_price * total_tco2e) / aum * 100  # as % of AUM
            el_adj = round(min(cost_impact, 15.0), 2)  # cap at 15%

            # Sector-level impacts (high-carbon sectors hit harder)
            sector_impacts = {}
            for ac, data in portfolio.asset_class_breakdown.items():
                ac_intensity = data.get("tco2e", 0) / max(data.get("aum_eur", 1) / 1e6, 0.001)
                sector_impacts[ac] = round(min(ac_intensity * carbon_price / 1e6 * 100, 25.0), 2)

            overlays.append(ScenarioOverlay(
                scenario_name=name,
                temperature_target_c=temp,
                carbon_price_eur_per_tco2=carbon_price,
                portfolio_el_adjustment_pct=el_adj,
                sector_impacts=sector_impacts,
            ))

        return overlays

    def feed_to_entity360(
        self, holdings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Supply entity-level PCAF metrics for Entity 360 profiles.

        Returns a list of entity-level PCAF summaries for integration
        with the entity 360 counterparty master.
        """
        entities = []
        for h in holdings:
            ac = h.get("asset_class", "listed_equity")
            calc_fn = self._get_asset_class_calculator(ac)
            try:
                r = calc_fn(h)
            except Exception:
                r = {"financed_total_tco2e": 0.0, "pcaf_dqs": 5}

            entities.append({
                "entity_name": h.get("entity_name", h.get("company_name", "")),
                "entity_id": h.get("entity_id", h.get("lei", "")),
                "pcaf_module": {
                    "asset_class": ac,
                    "financed_scope1_tco2e": r.get("financed_scope1_tco2e", 0.0),
                    "financed_scope2_tco2e": r.get("financed_scope2_tco2e", 0.0),
                    "financed_total_tco2e": r.get("financed_total_tco2e", 0.0),
                    "pcaf_dqs": r.get("pcaf_dqs", 5),
                    "attribution_factor": r.get("attribution_factor", 0.0),
                    "outstanding_eur": r.get("outstanding_eur", 0.0),
                },
            })
        return entities

    def feed_to_regulatory_compiler(
        self, portfolio: UnifiedPortfolioResult
    ) -> Dict[str, Any]:
        """
        Supply disclosure-ready data for the regulatory report compiler.

        Returns a structured dict keyed by framework with all PCAF-sourced
        datapoints needed for CSRD, SFDR, ISSB, TCFD, GRI compilation.
        """
        disclosures = self.generate_regulatory_disclosures(portfolio)
        return {
            "source_module": "pcaf_unified_engine",
            "engine_version": portfolio.engine_version,
            "timestamp": portfolio.calculation_timestamp,
            "frameworks": {
                "sfdr": disclosures.sfdr_pai,
                "eu_taxonomy": disclosures.eu_taxonomy_art8,
                "tcfd": disclosures.tcfd_metrics,
                "csrd_esrs_e1": disclosures.csrd_esrs_e1,
                "issb_s2": disclosures.issb_s2,
                "gri_305": disclosures.gri_305,
                "nzba": disclosures.nzba_tracking,
            },
            "cross_framework_map": disclosures.cross_framework_map,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Private Helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _get_asset_class_calculator(self, asset_class: str):
        """Return the calculation method for a given asset class."""
        calculators = {
            "listed_equity": self.calculate_listed_equity,
            "corporate_bonds": self.calculate_corporate_bonds,
            "business_loans": self.calculate_business_loans,
            "project_finance": self.calculate_project_finance,
            "commercial_real_estate": self.calculate_commercial_re,
            "mortgages": self.calculate_mortgages,
            "vehicle_loans": self.calculate_vehicle_loans,
            "sovereign_bonds": self.calculate_sovereign_bonds,
            "unlisted_equity": self.calculate_unlisted_equity,
            "infrastructure": self.calculate_infrastructure,
            "green_bonds": self.calculate_green_bonds,
        }
        return calculators.get(asset_class, self.calculate_listed_equity)

    def _calculate_standard_asset_class(
        self, holding: Dict[str, Any], asset_class: str
    ) -> Dict[str, Any]:
        """
        Standard calculation for EVIC/balance-sheet asset classes.

        Uses the emission factor fallback hierarchy and returns a normalised result dict.
        """
        outstanding = float(holding.get("outstanding_amount_eur", 0))
        evic = float(holding.get("enterprise_value_eur", 0))
        total_equity = float(holding.get("total_equity_eur", 0))
        total_debt = float(holding.get("total_debt_eur", 0))
        project_cost = float(holding.get("total_project_cost_eur", 0))
        revenue = float(holding.get("annual_revenue_eur", 0))
        sector = holding.get("sector_gics", "Unknown")
        reported_s1 = holding.get("scope1_co2e_tonnes")
        reported_s2 = holding.get("scope2_co2e_tonnes")
        verified = holding.get("verification_status", "none") == "verified"

        # Cast reported to float if present
        if reported_s1 is not None:
            reported_s1 = float(reported_s1)
        if reported_s2 is not None:
            reported_s2 = float(reported_s2)

        # Attribution factor
        meta = _ASSET_CLASS_BY_ID.get(asset_class)
        if asset_class in ("listed_equity", "corporate_bonds"):
            denom = evic if evic > 0 else (total_equity + total_debt)
        elif asset_class == "business_loans":
            denom = total_equity + total_debt
        elif asset_class == "project_finance":
            denom = project_cost if project_cost > 0 else evic
        elif asset_class == "commercial_real_estate":
            denom = float(holding.get("property_value_eur", total_equity))
        else:
            denom = evic if evic > 0 else (total_equity + total_debt)

        af = min(outstanding / denom, 1.0) if denom > 0 else 1.0

        # Emissions (fallback hierarchy)
        s1, s2, s3, dqs, source = _emission_factor_fallback(
            reported_s1, reported_s2, verified, sector, revenue, outstanding
        )

        financed_s1 = round(af * s1, 4)
        financed_s2 = round(af * s2, 4)
        financed_s3 = round(af * s3, 4)
        financed_total = round(financed_s1 + financed_s2 + financed_s3, 4)

        # Override DQS if explicitly set
        if holding.get("pcaf_dqs_override"):
            dqs = int(holding["pcaf_dqs_override"])

        return {
            "asset_class": asset_class,
            "entity_name": holding.get("entity_name", holding.get("company_name", "")),
            "sector_gics": sector,
            "country_iso": holding.get("country_iso", ""),
            "outstanding_eur": outstanding,
            "attribution_factor": round(af, 6),
            "emission_source": source,
            "investee_scope1_tco2e": round(s1, 4),
            "investee_scope2_tco2e": round(s2, 4),
            "investee_scope3_tco2e": round(s3, 4),
            "financed_scope1_tco2e": financed_s1,
            "financed_scope2_tco2e": financed_s2,
            "financed_scope3_tco2e": financed_s3,
            "financed_total_tco2e": financed_total,
            "pcaf_dqs": dqs,
            "methodology": (
                f"PCAF v2.0 {meta.label if meta else asset_class}: "
                f"AF={af:.6f}, source={source}"
            ),
        }

    def _apply_af_and_emissions(
        self, holding: Dict[str, Any], af: float, asset_class: str, method_note: str
    ) -> Dict[str, Any]:
        """Helper: apply AF to emissions using fallback hierarchy."""
        outstanding = float(holding.get("outstanding_amount_eur", 0))
        sector = holding.get("sector_gics", "Unknown")
        revenue = float(holding.get("annual_revenue_eur", 0))
        reported_s1 = holding.get("scope1_co2e_tonnes")
        reported_s2 = holding.get("scope2_co2e_tonnes")
        verified = holding.get("verification_status", "none") == "verified"

        if reported_s1 is not None:
            reported_s1 = float(reported_s1)
        if reported_s2 is not None:
            reported_s2 = float(reported_s2)

        s1, s2, s3, dqs, source = _emission_factor_fallback(
            reported_s1, reported_s2, verified, sector, revenue, outstanding
        )

        return {
            "asset_class": asset_class,
            "entity_name": holding.get("entity_name", ""),
            "outstanding_eur": outstanding,
            "attribution_factor": round(af, 6),
            "attribution_method": method_note,
            "emission_source": source,
            "financed_scope1_tco2e": round(af * s1, 4),
            "financed_scope2_tco2e": round(af * s2, 4),
            "financed_scope3_tco2e": round(af * s3, 4),
            "financed_total_tco2e": round(af * (s1 + s2 + s3), 4),
            "pcaf_dqs": dqs,
            "methodology": f"PCAF v2.0 {asset_class}: {method_note}, source={source}",
        }

    def _interpolate_temperature(self, waci: float) -> float:
        """Map WACI to implied temperature via piecewise linear interpolation."""
        from decimal import Decimal
        mp = _WACI_TEMPERATURE_MAPPING
        waci_d = Decimal(str(waci))
        if waci_d <= mp[0][0]:
            return float(mp[0][1])
        if waci_d >= mp[-1][0]:
            return float(mp[-1][1])
        for i in range(len(mp) - 1):
            w_lo, t_lo = mp[i]
            w_hi, t_hi = mp[i + 1]
            if w_lo <= waci_d <= w_hi:
                frac = float(waci_d - w_lo) / float(w_hi - w_lo)
                return round(float(t_lo) + frac * (float(t_hi) - float(t_lo)), 2)
        return 4.0

    # ──────────────────────────────────────────────────────────────────────────
    # Static Reference Data Accessors
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_asset_class_registry() -> List[Dict[str, Any]]:
        """Return complete asset class metadata."""
        return [asdict(ac) for ac in ASSET_CLASS_REGISTRY]

    @staticmethod
    def get_emission_factor_library() -> Dict[str, Any]:
        """Return all emission factor registries."""
        return {
            "sector_intensities_gics": dict(SECTOR_EMISSION_INTENSITIES),
            "nace_emission_factors": PCAF_EMISSION_FACTORS,
            "vehicle_factors": {k: dict(v) for k, v in VEHICLE_EMISSION_FACTORS.items()},
            "building_factors_epc": {k: dict(v) for k, v in BUILDING_EMISSION_FACTORS.items()},
            "mortgage_epc_factors": dict(MORTGAGE_EPC_FACTORS),
            "sovereign_production_mtco2e": dict(SOVEREIGN_PRODUCTION_EMISSIONS),
            "infrastructure_lifecycle_ef": dict(INFRASTRUCTURE_EF),
            "marine_vessel_ef": dict(MARINE_VESSEL_FACTORS),
            "energy_asset_ef": dict(ENERGY_ASSET_FACTORS),
            "green_bond_uop_ef": dict(GREEN_BOND_UOP_FACTORS),
            "insurance_lob_factors": dict(INSURANCE_LOB_FACTORS),
        }

    @staticmethod
    def get_dqs_framework() -> Dict[str, Any]:
        """Return DQS methodology reference."""
        return {
            "dqs_levels": PCAF_DQS_LEVELS,
            "quality_dimensions": PCAF_QUALITY_DIMENSIONS,
            "improvement_paths": PCAF_QUALITY_IMPROVEMENT_PATHS,
            "confidence_weights": dict(DQS_CONFIDENCE_WEIGHTS),
            "benchmarks": PCAF_QUALITY_BENCHMARKS,
        }

    @staticmethod
    def get_regulatory_mappings() -> List[Dict[str, Any]]:
        """Return cross-framework regulatory mapping table."""
        return list(PCAF_CROSS_FRAMEWORK_MAP)

    @staticmethod
    def get_insurance_lob_metadata() -> List[Dict[str, Any]]:
        """Return insurance lines of business with emission factors."""
        return [
            {
                "lob": lob.value,
                "label": lob.name.replace("_", " ").title(),
                "default_ef_tco2e_per_m_premium": INSURANCE_LOB_FACTORS.get(lob.value, 0.0),
                "calculation_method": (
                    "Fleet emission model" if "motor" in lob.value
                    else "Building area model" if "property" in lob.value
                    else "Revenue intensity model" if "commercial" in lob.value
                    else "Disclosure-only proxy" if lob.value in ("life", "health")
                    else "Premium-weighted proxy"
                ),
            }
            for lob in InsuranceLineOfBusiness
        ]

    @staticmethod
    def get_deal_type_metadata() -> List[Dict[str, Any]]:
        """Return facilitated emissions deal type metadata."""
        return [
            {
                "deal_type": dt.value,
                "label": dt.name.replace("_", " ").title(),
                "attribution_note": (
                    "AF = underwritten / (total x 3)" if "bond" in dt.value or "convertible" in dt.value
                    else "AF = placed / (market_cap x 3)" if "equity" in dt.value or "ipo" in dt.value
                    else "AF = tranche / pool (no /3)" if "securitisation" in dt.value
                    else "AF = arranged / facility" if "syndicated" in dt.value
                    else "AF = 0 (disclosure-only)" if "advisory" in dt.value
                    else "See PCAF Part C"
                ),
                "pcaf_reference": "PCAF Global GHG Standard v2.0 Part C",
            }
            for dt in FacilitatedDealType
        ]
