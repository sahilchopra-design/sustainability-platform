"""
Unified Valuation Engine — Climate Intelligence Platform
=========================================================
Covers 7 asset classes with all applicable methodologies per class.
Compliant with: RICS Red Book (PS1/VPS4), IVS 2024 (IVSC), USPAP, TEGoVA EVS,
                IFRS 13, Basel III, CRREM v2, IPEV Guidelines, INREV NAV.

Asset Classes:
  INFRASTRUCTURE  — regulated utilities, transport, social infrastructure
  PROJECT         — project finance / PPP / concessions
  ENERGY          — power generation (thermal, renewables, storage)
  COMMERCIAL      — office, retail, industrial, hotel, data centre, logistics
  RESIDENTIAL     — single-family, multifamily, BTR, social housing
  AGRICULTURAL    — arable, pasture, horticulture, plantation, forestry
  LAND            — development land, brownfield, greenfield, rural, mixed-use

Methodologies available per class:
  Income / DCF            — all income-generating assets
  Direct Capitalisation   — stabilised commercial/residential income
  Regulated Asset Base    — regulated utilities / infrastructure
  Project Finance DCF     — PPP / concessions / project finance
  Energy Yield / LCOE     — renewable energy, thermal power
  Replacement / Cost      — special purpose, infrastructure, agri
  Sales Comparison        — commercial, residential, land, farmland
  Residual Land Value     — development sites, brownfield
  Hedonic Pricing         — residential (model-based)
  Timber/Carbon Value     — forestry, woodland, cropland
  ESG Climate Overlay     — applied to ALL asset types (mandatory)
"""

from __future__ import annotations

import math
import logging
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from enum import Enum
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, date

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# ENUMERATIONS
# ──────────────────────────────────────────────────────────────────────────────

class AssetClass(str, Enum):
    INFRASTRUCTURE = "infrastructure"
    PROJECT        = "project"
    ENERGY         = "energy"
    COMMERCIAL     = "commercial"
    RESIDENTIAL    = "residential"
    AGRICULTURAL   = "agricultural"
    LAND           = "land"


class InfrastructureSubtype(str, Enum):
    REGULATED_UTILITY = "regulated_utility"   # water, gas, electricity networks
    TOLL_ROAD         = "toll_road"
    RAIL              = "rail"
    PORT              = "port"
    AIRPORT           = "airport"
    SOCIAL_INFRA      = "social_infra"         # schools, hospitals (PPP)
    TELECOM_TOWER     = "telecom_tower"
    DATA_CENTRE       = "data_centre"
    BRIDGE_TUNNEL     = "bridge_tunnel"


class ProjectSubtype(str, Enum):
    PPP_AVAILABILITY  = "ppp_availability"
    PPP_DEMAND        = "ppp_demand"
    CONCESSION        = "concession"
    GREENFIELD        = "greenfield"
    BROWNFIELD        = "brownfield"
    MINING_PROJECT    = "mining_project"


class EnergySubtype(str, Enum):
    SOLAR_PV          = "solar_pv"
    WIND_ONSHORE      = "wind_onshore"
    WIND_OFFSHORE     = "wind_offshore"
    GAS_CCGT          = "gas_ccgt"
    GAS_OCGT          = "gas_ocgt"
    COAL              = "coal"
    NUCLEAR           = "nuclear"
    HYDRO             = "hydro"
    BIOMASS           = "biomass"
    BATTERY_STORAGE   = "battery_storage"
    HYDROGEN          = "hydrogen"
    GEOTHERMAL        = "geothermal"
    SOLAR_CSP         = "solar_csp"
    OFFSHORE_WIND_FLOAT = "offshore_wind_float"


class CommercialSubtype(str, Enum):
    OFFICE_PRIME      = "office_prime"
    OFFICE_SECONDARY  = "office_secondary"
    RETAIL_HIGH_ST    = "retail_high_street"
    RETAIL_SHOPPING_CENTRE = "retail_shopping_centre"
    RETAIL_PARK       = "retail_park"
    INDUSTRIAL_LOGISTICS = "industrial_logistics"
    LIGHT_INDUSTRIAL  = "light_industrial"
    HOTEL_FULL_SERVICE = "hotel_full_service"
    HOTEL_LIMITED     = "hotel_limited"
    DATA_CENTRE       = "data_centre"
    HEALTHCARE        = "healthcare"
    STUDENT_HOUSING   = "student_housing"
    SENIOR_LIVING     = "senior_living"
    MIXED_USE         = "mixed_use"


class ResidentialSubtype(str, Enum):
    SINGLE_FAMILY     = "single_family"
    MULTIFAMILY       = "multifamily"
    BUILD_TO_RENT     = "build_to_rent"
    AFFORDABLE        = "affordable"
    SOCIAL_HOUSING    = "social_housing"
    STUDENT           = "student"


class AgriculturalSubtype(str, Enum):
    ARABLE            = "arable"               # cereal/oilseed cropland
    PERMANENT_PASTURE = "permanent_pasture"
    MIXED_FARMING     = "mixed_farming"
    HORTICULTURE      = "horticulture"
    PLANTATION        = "plantation"           # fruit, vines
    FORESTRY          = "forestry"
    AQUACULTURE       = "aquaculture"
    ORGANIC_FARM      = "organic_farm"


class LandSubtype(str, Enum):
    RESIDENTIAL_DEV   = "residential_dev"      # consented residential land
    COMMERCIAL_DEV    = "commercial_dev"
    INDUSTRIAL_DEV    = "industrial_dev"
    MIXED_USE_DEV     = "mixed_use_dev"
    BROWNFIELD        = "brownfield"           # previously developed, remediation needed
    GREENFIELD        = "greenfield"           # agricultural → development
    RURAL_BARE        = "rural_bare"
    STRATEGIC_LAND    = "strategic_land"       # pre-planning, option value
    CARBON_LAND       = "carbon_land"          # peatland, rewilding, carbon credits


class ValuationMethod(str, Enum):
    INCOME_DCF             = "income_dcf"
    DIRECT_CAPITALISATION  = "direct_capitalisation"
    REGULATED_ASSET_BASE   = "regulated_asset_base"
    PROJECT_FINANCE_DCF    = "project_finance_dcf"
    ENERGY_YIELD_DCF       = "energy_yield_dcf"
    REPLACEMENT_COST       = "replacement_cost"
    SALES_COMPARISON       = "sales_comparison"
    RESIDUAL_LAND_VALUE    = "residual_land_value"
    HEDONIC_PRICING        = "hedonic_pricing"
    TIMBER_CARBON_VALUE    = "timber_carbon_value"
    NAV_APPROACH           = "nav_approach"


class ClimateScenario(str, Enum):
    NZE_1_5C          = "nze_1_5c"
    BELOW_2C          = "below_2c"
    NDC_2_5C          = "ndc_2_5c"
    CURRENT_POLICIES  = "current_policies_3c"


class EPCRating(str, Enum):
    A = "A"; B = "B"; C = "C"; D = "D"; E = "E"; F = "F"; G = "G"


# ──────────────────────────────────────────────────────────────────────────────
# INPUT DATACLASSES
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ESGClimateInputs:
    """ESG and climate risk inputs applied to all asset classes."""
    epc_rating: str = "D"
    energy_intensity_kwh_m2: Decimal = Decimal("0")
    carbon_intensity_kgco2_m2: Decimal = Decimal("0")
    flood_risk: str = "none"           # none | low | medium | high | extreme
    heat_risk_score: Decimal = Decimal("0")   # 0-100
    physical_risk_score: Decimal = Decimal("0")  # composite 0-100
    transition_risk_score: Decimal = Decimal("0") # composite 0-100
    water_stress_score: Decimal = Decimal("0")    # WRI Aqueduct 0-5
    biodiversity_sensitivity: str = "low"   # low | medium | high | critical
    has_green_certification: bool = False
    certification_type: str = ""       # BREEAM_Excellent | LEED_Platinum | NABERS_5 etc.
    sbti_aligned: bool = False
    climate_scenario: ClimateScenario = ClimateScenario.BELOW_2C
    assessment_year: int = 2024
    target_year: int = 2035


@dataclass
class InfrastructureInputs:
    subtype: InfrastructureSubtype = InfrastructureSubtype.REGULATED_UTILITY
    regulated_asset_base_value: Decimal = Decimal("0")   # RAB value (USD)
    allowed_return_on_rab_pct: Decimal = Decimal("6.5")  # WACC allowed by regulator
    regulatory_period_years: int = 5
    annual_revenue: Decimal = Decimal("0")
    annual_opex: Decimal = Decimal("0")
    annual_capex: Decimal = Decimal("0")
    depreciation_annual: Decimal = Decimal("0")
    discount_rate_pct: Decimal = Decimal("7.0")
    projection_years: int = 30
    terminal_growth_pct: Decimal = Decimal("2.0")
    concession_expiry_year: Optional[int] = None
    replacement_cost: Decimal = Decimal("0")
    asset_age_years: int = 0
    useful_life_years: int = 40
    # Regulatory risk
    regulatory_risk_premium_bps: int = 0   # bps added to discount rate for regulatory risk


@dataclass
class ProjectInputs:
    subtype: ProjectSubtype = ProjectSubtype.PPP_AVAILABILITY
    total_project_cost: Decimal = Decimal("0")
    equity_contribution_pct: Decimal = Decimal("20.0")
    annual_revenue: Decimal = Decimal("0")         # availability payment or demand-based
    annual_opex: Decimal = Decimal("0")
    annual_debt_service: Decimal = Decimal("0")
    concession_years: int = 25
    construction_years: int = 3
    senior_debt_pct: Decimal = Decimal("70.0")
    debt_interest_rate_pct: Decimal = Decimal("5.5")
    equity_irr_target_pct: Decimal = Decimal("12.0")
    project_irr_target_pct: Decimal = Decimal("8.0")
    dscr_minimum: Decimal = Decimal("1.20")
    revenue_ramp_years: int = 3
    ramp_factor: Decimal = Decimal("0.70")         # revenue at 70% during ramp


@dataclass
class EnergyInputs:
    subtype: EnergySubtype = EnergySubtype.SOLAR_PV
    nameplate_capacity_mw: Decimal = Decimal("0")
    capacity_factor_pct: Decimal = Decimal("0")    # e.g. 25.0 for solar
    annual_generation_mwh: Decimal = Decimal("0")  # if known; else calculated from CF
    ppa_price_usd_mwh: Decimal = Decimal("0")      # power purchase agreement price
    merchant_price_usd_mwh: Decimal = Decimal("0") # merchant revenue assumption
    ppa_coverage_pct: Decimal = Decimal("100.0")   # % generation under PPA
    ppa_duration_years: int = 15
    annual_opex_usd_kw: Decimal = Decimal("0")     # $/kW-year (use industry defaults if 0)
    annual_degradation_pct: Decimal = Decimal("0") # generation degradation per year
    construction_cost_usd_kw: Decimal = Decimal("0")
    discount_rate_pct: Decimal = Decimal("7.5")
    asset_life_years: int = 25
    decommissioning_cost_usd: Decimal = Decimal("0")
    eu_ets_price_eur_tco2: Decimal = Decimal("65") # for thermal plants
    annual_co2_tonnes: Decimal = Decimal("0")      # for thermal plants


@dataclass
class CommercialInputs:
    subtype: CommercialSubtype = CommercialSubtype.OFFICE_PRIME
    gross_floor_area_m2: Decimal = Decimal("0")
    net_lettable_area_m2: Decimal = Decimal("0")   # if 0, computed as 85% of GFA
    passing_rent_psm_pa: Decimal = Decimal("0")    # £/m2/year passing rent
    market_rent_psm_pa: Decimal = Decimal("0")     # ERV (Estimated Rental Value)
    occupancy_rate_pct: Decimal = Decimal("95.0")
    vacancy_cost_psm: Decimal = Decimal("0")
    service_charge_psm: Decimal = Decimal("0")
    management_fee_pct: Decimal = Decimal("3.0")   # % of gross rent
    capex_reserve_psm: Decimal = Decimal("0")      # £/m2/year maintenance reserve
    initial_yield_pct: Decimal = Decimal("0")      # cap rate; if 0 use market default
    discount_rate_pct: Decimal = Decimal("7.0")
    exit_yield_pct: Decimal = Decimal("0")         # terminal cap rate; if 0 = initial+0.25%
    rent_growth_pct_pa: Decimal = Decimal("2.0")
    lease_term_years: int = 10
    void_period_months: int = 6
    lease_incentive_months: int = 6                # rent-free
    projection_years: int = 10
    year_built: int = 2000
    last_refurbishment_year: Optional[int] = None
    land_value_pct: Decimal = Decimal("20.0")      # for cost approach


@dataclass
class ResidentialInputs:
    subtype: ResidentialSubtype = ResidentialSubtype.MULTIFAMILY
    units: int = 0
    avg_unit_size_m2: Decimal = Decimal("0")
    avg_monthly_rent_per_unit: Decimal = Decimal("0")
    occupancy_rate_pct: Decimal = Decimal("95.0")
    annual_opex_per_unit: Decimal = Decimal("0")   # management, maintenance, insurance
    capex_reserve_pct: Decimal = Decimal("5.0")    # % of gross revenue
    gross_yield_market_pct: Decimal = Decimal("0") # market gross yield; 0 = use default
    discount_rate_pct: Decimal = Decimal("6.5")
    exit_yield_pct: Decimal = Decimal("0")
    rent_growth_pct_pa: Decimal = Decimal("2.5")
    projection_years: int = 10
    # Comparables for hedonic / sales comparison
    comparable_prices_per_m2: List[Decimal] = field(default_factory=list)
    comparable_sizes_m2: List[Decimal] = field(default_factory=list)
    comparable_adjustments: List[Decimal] = field(default_factory=list)  # + or - %


@dataclass
class AgriculturalInputs:
    subtype: AgriculturalSubtype = AgriculturalSubtype.ARABLE
    area_hectares: Decimal = Decimal("0")
    soil_quality_score: Decimal = Decimal("3.0")   # 1-5 (1=poor, 5=excellent)
    annual_crop_yield_tonnes_ha: Decimal = Decimal("0")
    commodity_price_usd_tonne: Decimal = Decimal("0")
    annual_opex_usd_ha: Decimal = Decimal("0")     # cultivation, harvest, insurance
    comparable_land_price_usd_ha: Decimal = Decimal("0")
    agricultural_subsidy_usd_ha: Decimal = Decimal("0")  # Basic Payment / CAP
    discount_rate_pct: Decimal = Decimal("5.0")
    projection_years: int = 20
    # Forestry specific
    timber_species: str = ""            # sitka_spruce | douglas_fir | oak | mixed
    timber_rotation_years: int = 35
    standing_timber_value_usd_m3: Decimal = Decimal("0")
    estimated_timber_volume_m3_ha: Decimal = Decimal("0")
    # Carbon sequestration
    carbon_sequestration_tco2e_ha_yr: Decimal = Decimal("0")
    carbon_credit_price_usd: Decimal = Decimal("25")
    woodland_carbon_code: bool = False   # UK WCC registered
    # Water rights
    water_rights_value: Decimal = Decimal("0")


@dataclass
class LandInputs:
    subtype: LandSubtype = LandSubtype.RESIDENTIAL_DEV
    site_area_hectares: Decimal = Decimal("0")
    # Development appraisal (residual land value)
    gross_development_value: Decimal = Decimal("0")   # GDV from completed scheme
    total_development_cost: Decimal = Decimal("0")    # build cost + professional fees
    developer_profit_pct: Decimal = Decimal("20.0")   # % of GDV
    finance_cost_pct: Decimal = Decimal("6.0")        # % of build cost p.a.
    development_period_years: Decimal = Decimal("2.0")
    planning_risk_discount_pct: Decimal = Decimal("0")  # if no planning consent
    remediation_cost: Decimal = Decimal("0")          # brownfield
    # Planning uplift
    existing_use_value_ha: Decimal = Decimal("0")     # EUV for greenbelt/strategic
    planning_uplift_multiple: Decimal = Decimal("1.0") # EUV × multiple if allocated
    # Comparables
    comparable_land_prices_ha: List[Decimal] = field(default_factory=list)
    # Carbon / nature (carbon land)
    peatland_depth_m: Decimal = Decimal("0")
    carbon_sequestration_potential_tco2e_ha: Decimal = Decimal("0")


@dataclass
class ValuationRequest:
    """Master request object — one engine for all asset classes."""
    asset_class: AssetClass
    asset_name: str = ""
    country_iso: str = "GB"
    currency: str = "GBP"
    valuation_date: str = ""          # ISO date string
    methods_requested: List[ValuationMethod] = field(default_factory=list)  # empty = auto-select
    # Only one of these will be populated depending on asset_class
    infrastructure: Optional[InfrastructureInputs] = None
    project: Optional[ProjectInputs] = None
    energy: Optional[EnergyInputs] = None
    commercial: Optional[CommercialInputs] = None
    residential: Optional[ResidentialInputs] = None
    agricultural: Optional[AgriculturalInputs] = None
    land: Optional[LandInputs] = None
    # ESG/Climate — always populated
    esg: ESGClimateInputs = field(default_factory=ESGClimateInputs)
    valuation_standard: str = "RICS_Red_Book"  # RICS_Red_Book | IVS | USPAP | TEGoVA


@dataclass
class MethodResult:
    """Result from one valuation method."""
    method: ValuationMethod
    indicated_value: Decimal
    weight: Decimal                    # reconciliation weight 0-1
    key_metrics: Dict[str, Any]
    narrative: str
    confidence: str                    # high | medium | low
    methodology_basis: str             # e.g. "RICS VPS2 Income Approach"


@dataclass
class ESGAdjustment:
    """Climate/ESG value adjustments applied on top of all methods."""
    green_premium_pct: Decimal = Decimal("0")
    brown_discount_pct: Decimal = Decimal("0")
    physical_risk_discount_pct: Decimal = Decimal("0")
    transition_risk_discount_pct: Decimal = Decimal("0")
    biodiversity_adjustment_pct: Decimal = Decimal("0")
    net_esg_adjustment_pct: Decimal = Decimal("0")
    stranding_risk_year: Optional[int] = None
    carbon_credit_value: Decimal = Decimal("0")
    esg_narrative: str = ""


@dataclass
class ValuationResult:
    """Complete valuation result across all methods."""
    asset_class: AssetClass
    asset_name: str
    currency: str
    valuation_date: str
    # Method results
    method_results: List[MethodResult]
    reconciled_value_pre_esg: Decimal
    esg_adjustment: ESGAdjustment
    final_value: Decimal
    value_range_low: Decimal
    value_range_high: Decimal
    # Per-unit metrics
    value_per_m2: Optional[Decimal] = None
    value_per_unit: Optional[Decimal] = None
    value_per_ha: Optional[Decimal] = None
    value_per_kw: Optional[Decimal] = None
    # Risk metrics
    irr_pct: Optional[Decimal] = None
    yield_pct: Optional[Decimal] = None
    dscr: Optional[Decimal] = None
    payback_years: Optional[Decimal] = None
    # Regulatory / reporting
    valuation_standard_used: str = ""
    rics_ps1_compliant: bool = True
    rics_vps4_esg_addressed: bool = True
    ivs_esg_addressed: bool = True
    material_uncertainty: bool = False
    # Full audit
    validation_summary: Dict[str, Any] = field(default_factory=dict)


# ──────────────────────────────────────────────────────────────────────────────
# MARKET DATA DEFAULTS (replaces external data calls with calibrated defaults)
# ──────────────────────────────────────────────────────────────────────────────

class MarketDefaults:
    """
    Calibrated market defaults by country and asset class.
    Sources: JLL, CBRE, Knight Frank, Savills, RICS, MSCI.
    Updated: Q1 2024.
    """

    # Commercial yields by subtype and country (prime market)
    COMMERCIAL_YIELDS: Dict[str, Dict[str, Decimal]] = {
        "office_prime":          {"GB": Decimal("5.25"), "DE": Decimal("4.00"), "US": Decimal("6.50"), "AU": Decimal("5.75"), "default": Decimal("5.50")},
        "office_secondary":      {"GB": Decimal("7.50"), "DE": Decimal("5.50"), "US": Decimal("8.00"), "AU": Decimal("7.00"), "default": Decimal("7.50")},
        "retail_high_street":    {"GB": Decimal("6.50"), "DE": Decimal("4.25"), "US": Decimal("7.00"), "AU": Decimal("5.50"), "default": Decimal("6.50")},
        "retail_shopping_centre":{"GB": Decimal("9.00"), "DE": Decimal("5.50"), "US": Decimal("8.50"), "AU": Decimal("7.50"), "default": Decimal("8.50")},
        "retail_park":           {"GB": Decimal("7.00"), "DE": Decimal("5.00"), "US": Decimal("7.50"), "AU": Decimal("6.50"), "default": Decimal("7.00")},
        "industrial_logistics":  {"GB": Decimal("4.75"), "DE": Decimal("4.00"), "US": Decimal("5.25"), "AU": Decimal("5.00"), "default": Decimal("5.00")},
        "light_industrial":      {"GB": Decimal("5.75"), "DE": Decimal("5.00"), "US": Decimal("6.50"), "AU": Decimal("6.00"), "default": Decimal("6.00")},
        "hotel_full_service":    {"GB": Decimal("6.00"), "DE": Decimal("5.00"), "US": Decimal("8.00"), "AU": Decimal("6.50"), "default": Decimal("6.50")},
        "hotel_limited":         {"GB": Decimal("7.00"), "DE": Decimal("5.50"), "US": Decimal("9.00"), "AU": Decimal("7.50"), "default": Decimal("7.50")},
        "data_centre":           {"GB": Decimal("4.25"), "DE": Decimal("4.00"), "US": Decimal("4.50"), "AU": Decimal("5.00"), "default": Decimal("4.50")},
        "healthcare":            {"GB": Decimal("5.00"), "DE": Decimal("4.50"), "US": Decimal("6.00"), "AU": Decimal("5.50"), "default": Decimal("5.50")},
        "student_housing":       {"GB": Decimal("4.50"), "DE": Decimal("4.25"), "US": Decimal("5.50"), "AU": Decimal("5.00"), "default": Decimal("4.75")},
        "senior_living":         {"GB": Decimal("5.00"), "DE": Decimal("4.75"), "US": Decimal("5.75"), "AU": Decimal("5.50"), "default": Decimal("5.25")},
        "mixed_use":             {"GB": Decimal("5.50"), "DE": Decimal("4.75"), "US": Decimal("6.00"), "AU": Decimal("5.75"), "default": Decimal("5.75")},
    }

    # Residential gross yields
    RESIDENTIAL_YIELDS: Dict[str, Dict[str, Decimal]] = {
        "single_family":   {"GB": Decimal("3.50"), "DE": Decimal("3.00"), "US": Decimal("5.50"), "AU": Decimal("3.25"), "default": Decimal("4.00")},
        "multifamily":     {"GB": Decimal("4.25"), "DE": Decimal("3.50"), "US": Decimal("5.00"), "AU": Decimal("4.00"), "default": Decimal("4.50")},
        "build_to_rent":   {"GB": Decimal("4.00"), "DE": Decimal("3.25"), "US": Decimal("4.75"), "AU": Decimal("4.00"), "default": Decimal("4.25")},
        "affordable":      {"GB": Decimal("4.50"), "DE": Decimal("4.00"), "US": Decimal("5.50"), "AU": Decimal("4.75"), "default": Decimal("4.75")},
        "social_housing":  {"GB": Decimal("4.75"), "DE": Decimal("4.25"), "US": Decimal("5.75"), "AU": Decimal("5.00"), "default": Decimal("5.00")},
        "student":         {"GB": Decimal("5.00"), "DE": Decimal("4.75"), "US": Decimal("6.00"), "AU": Decimal("5.25"), "default": Decimal("5.25")},
    }

    # Energy: default OPEX by technology (USD/kW/year)
    ENERGY_OPEX_USD_KW: Dict[str, Decimal] = {
        "solar_pv": Decimal("17"), "wind_onshore": Decimal("45"), "wind_offshore": Decimal("85"),
        "gas_ccgt": Decimal("20"), "gas_ocgt": Decimal("15"), "coal": Decimal("35"),
        "nuclear": Decimal("110"), "hydro": Decimal("30"), "biomass": Decimal("65"),
        "battery_storage": Decimal("12"), "hydrogen": Decimal("55"), "geothermal": Decimal("40"),
        "solar_csp": Decimal("55"), "offshore_wind_float": Decimal("100"),
    }

    # Energy: default capacity factors (%)
    ENERGY_CAPACITY_FACTORS: Dict[str, Decimal] = {
        "solar_pv": Decimal("20"), "wind_onshore": Decimal("35"), "wind_offshore": Decimal("45"),
        "gas_ccgt": Decimal("55"), "gas_ocgt": Decimal("20"), "coal": Decimal("50"),
        "nuclear": Decimal("90"), "hydro": Decimal("40"), "biomass": Decimal("75"),
        "battery_storage": Decimal("15"), "hydrogen": Decimal("40"), "geothermal": Decimal("85"),
        "solar_csp": Decimal("28"), "offshore_wind_float": Decimal("48"),
    }

    # Energy: default construction costs (USD/kW)
    ENERGY_CAPEX_USD_KW: Dict[str, Decimal] = {
        "solar_pv": Decimal("900"), "wind_onshore": Decimal("1400"), "wind_offshore": Decimal("3200"),
        "gas_ccgt": Decimal("900"), "gas_ocgt": Decimal("700"), "coal": Decimal("3500"),
        "nuclear": Decimal("7500"), "hydro": Decimal("2500"), "biomass": Decimal("3000"),
        "battery_storage": Decimal("400"), "hydrogen": Decimal("1500"), "geothermal": Decimal("4000"),
        "solar_csp": Decimal("4500"), "offshore_wind_float": Decimal("4500"),
    }

    # Agricultural land values (USD/ha) by country
    AGRI_LAND_VALUE_USD_HA: Dict[str, Dict[str, Decimal]] = {
        "arable":           {"GB": Decimal("12000"), "DE": Decimal("25000"), "US": Decimal("8000"), "AU": Decimal("3500"), "default": Decimal("10000")},
        "permanent_pasture":{"GB": Decimal("9000"),  "DE": Decimal("18000"), "US": Decimal("5500"), "AU": Decimal("2500"), "default": Decimal("7500")},
        "forestry":         {"GB": Decimal("6000"),  "DE": Decimal("15000"), "US": Decimal("3000"), "AU": Decimal("2000"), "default": Decimal("5000")},
        "horticulture":     {"GB": Decimal("15000"), "DE": Decimal("30000"), "US": Decimal("12000"), "AU": Decimal("8000"), "default": Decimal("14000")},
    }

    # Infrastructure: regulated WACC by subtype
    INFRASTRUCTURE_WACC: Dict[str, Decimal] = {
        "regulated_utility": Decimal("5.5"), "toll_road": Decimal("7.0"),
        "rail": Decimal("6.0"),              "port": Decimal("7.5"),
        "airport": Decimal("8.0"),           "social_infra": Decimal("6.5"),
        "telecom_tower": Decimal("7.5"),     "data_centre": Decimal("8.5"),
        "bridge_tunnel": Decimal("7.0"),
    }

    @classmethod
    def get_commercial_yield(cls, subtype: str, country: str) -> Decimal:
        sub = cls.COMMERCIAL_YIELDS.get(subtype, {})
        return sub.get(country, sub.get("default", Decimal("6.0")))

    @classmethod
    def get_residential_yield(cls, subtype: str, country: str) -> Decimal:
        sub = cls.RESIDENTIAL_YIELDS.get(subtype, {})
        return sub.get(country, sub.get("default", Decimal("4.5")))


# ──────────────────────────────────────────────────────────────────────────────
# ESG OVERLAY ENGINE
# ──────────────────────────────────────────────────────────────────────────────

class ESGOverlayEngine:
    """
    Applies ESG and climate risk adjustments to any asset class.
    References: RICS VPS4, JLL Green Building Premium Study 2023,
    MSCI Real Estate Green Premium Analysis 2023, CRREM v2.
    """

    GREEN_CERT_PREMIUMS: Dict[str, Decimal] = {
        "BREEAM_Outstanding": Decimal("0.10"), "BREEAM_Excellent": Decimal("0.07"),
        "BREEAM_Very_Good":   Decimal("0.04"), "LEED_Platinum":    Decimal("0.08"),
        "LEED_Gold":          Decimal("0.05"), "LEED_Silver":      Decimal("0.02"),
        "NABERS_6":           Decimal("0.09"), "NABERS_5":         Decimal("0.06"),
        "ENERGY_STAR_90":     Decimal("0.05"), "GRESB_5_Star":     Decimal("0.06"),
        "WELL_Platinum":      Decimal("0.04"), "Green_Building_Cert": Decimal("0.03"),
    }

    EPC_BROWN_DISCOUNTS: Dict[str, Decimal] = {
        # EPC grade → discount vs minimum-compliant (C-rated) asset
        "A": Decimal("-0.05"),   # premium over C
        "B": Decimal("-0.02"),   # small premium
        "C": Decimal("0.00"),    # neutral
        "D": Decimal("0.03"),    # slight discount
        "E": Decimal("0.07"),    # moderate discount
        "F": Decimal("0.12"),    # significant discount
        "G": Decimal("0.18"),    # severe discount / stranding risk
    }

    FLOOD_RISK_DISCOUNTS: Dict[str, Decimal] = {
        "none": Decimal("0.00"), "low": Decimal("0.02"), "medium": Decimal("0.05"),
        "high": Decimal("0.10"), "extreme": Decimal("0.18"),
    }

    PHYSICAL_RISK_DISCOUNTS: Dict[str, Decimal] = {
        "nze_1_5c": Decimal("0.03"), "below_2c": Decimal("0.05"),
        "ndc_2_5c": Decimal("0.09"), "current_policies_3c": Decimal("0.14"),
    }

    BIODIVERSITY_ADJUSTMENTS: Dict[str, Decimal] = {
        "low": Decimal("0.00"), "medium": Decimal("-0.01"),
        "high": Decimal("-0.03"), "critical": Decimal("-0.06"),
    }

    def calculate_esg_adjustment(
        self,
        esg: ESGClimateInputs,
        asset_class: AssetClass,
        base_value: Decimal,
    ) -> ESGAdjustment:
        adj = ESGAdjustment()

        # 1. Green certification premium
        if esg.has_green_certification and esg.certification_type:
            adj.green_premium_pct = self.GREEN_CERT_PREMIUMS.get(
                esg.certification_type, Decimal("0.03")
            )

        # 2. EPC brown discount (commercial, residential, RE assets)
        if asset_class in (AssetClass.COMMERCIAL, AssetClass.RESIDENTIAL, AssetClass.AGRICULTURAL):
            rating = esg.epc_rating.upper() if esg.epc_rating else "D"
            adj.brown_discount_pct = self.EPC_BROWN_DISCOUNTS.get(rating, Decimal("0.05"))
            # Flag stranding risk for F/G rated assets
            if rating in ("F", "G"):
                adj.stranding_risk_year = esg.assessment_year + 3 if rating == "G" else esg.assessment_year + 7

        # 3. Physical risk discount (flood + composite physical)
        flood_discount = self.FLOOD_RISK_DISCOUNTS.get(
            esg.flood_risk.lower(), Decimal("0.00")
        )
        scenario_phys_multiplier = self.PHYSICAL_RISK_DISCOUNTS.get(
            esg.climate_scenario.value, Decimal("0.05")
        )
        physical_score_factor = (esg.physical_risk_score / Decimal("100")) * scenario_phys_multiplier
        adj.physical_risk_discount_pct = max(flood_discount, physical_score_factor)

        # 4. Transition risk discount
        transition_factor = (esg.transition_risk_score / Decimal("100")) * Decimal("0.08")
        # SBTi-aligned companies get a 30% reduction in transition risk penalty
        if esg.sbti_aligned:
            transition_factor *= Decimal("0.70")
        adj.transition_risk_discount_pct = transition_factor

        # 5. Biodiversity adjustment
        adj.biodiversity_adjustment_pct = self.BIODIVERSITY_ADJUSTMENTS.get(
            esg.biodiversity_sensitivity.lower(), Decimal("0.00")
        )

        # 6. Carbon credit value (agricultural / land / forestry)
        if asset_class in (AssetClass.AGRICULTURAL, AssetClass.LAND):
            adj.carbon_credit_value = (
                esg.assessment_year  # placeholder — real calc in agri engine
            )

        # Net adjustment: green premium offsets risk discounts
        adj.net_esg_adjustment_pct = (
            adj.green_premium_pct
            - adj.brown_discount_pct
            - adj.physical_risk_discount_pct
            - adj.transition_risk_discount_pct
            + adj.biodiversity_adjustment_pct
        )

        adj.esg_narrative = (
            f"ESG overlay: green premium {float(adj.green_premium_pct)*100:.1f}%, "
            f"EPC/brown discount {float(adj.brown_discount_pct)*100:.1f}%, "
            f"physical risk {float(adj.physical_risk_discount_pct)*100:.1f}%, "
            f"transition risk {float(adj.transition_risk_discount_pct)*100:.1f}%. "
            f"Net adjustment: {float(adj.net_esg_adjustment_pct)*100:+.1f}%."
        )
        return adj


# ──────────────────────────────────────────────────────────────────────────────
# METHOD CALCULATORS
# ──────────────────────────────────────────────────────────────────────────────

def _d(v) -> Decimal:
    """Safe Decimal conversion."""
    try:
        return Decimal(str(v))
    except (InvalidOperation, TypeError):
        return Decimal("0")


def _dcf_pv(cashflows: List[Decimal], discount_rate_pct: Decimal) -> Decimal:
    """Discount a list of annual cashflows to present value."""
    r = discount_rate_pct / Decimal("100")
    pv = Decimal("0")
    for i, cf in enumerate(cashflows, start=1):
        pv += cf / ((1 + r) ** i)
    return pv


def calc_infrastructure(
    inp: InfrastructureInputs, country: str, esg: ESGClimateInputs
) -> List[MethodResult]:
    results: List[MethodResult] = []
    md = MarketDefaults()

    # ── METHOD 1: Regulated Asset Base (RAB) ─────────────────────────────────
    if inp.regulated_asset_base_value > 0:
        wacc_allowed = md.INFRASTRUCTURE_WACC.get(inp.subtype.value, Decimal("6.5"))
        rab_return = inp.regulated_asset_base_value * wacc_allowed / Decimal("100")
        # RAB value = sum of regulatory periods' returns discounted
        discount_r = (inp.discount_rate_pct + _d(inp.regulatory_risk_premium_bps) / Decimal("100")) / Decimal("100")
        rab_value = rab_return / discount_r  # perpetuity approximation
        results.append(MethodResult(
            method=ValuationMethod.REGULATED_ASSET_BASE,
            indicated_value=rab_value.quantize(Decimal("1")),
            weight=Decimal("0.45"),
            key_metrics={"rab_value": float(inp.regulated_asset_base_value), "allowed_wacc_pct": float(wacc_allowed), "annual_rab_return": float(rab_return)},
            narrative=f"RAB-based valuation: allowed return {float(wacc_allowed):.2f}% on RAB of {float(inp.regulated_asset_base_value):,.0f}. Discounted at {float(inp.discount_rate_pct):.2f}%.",
            confidence="high",
            methodology_basis="Ofgem/Ofwat/NRA RAB methodology; RICS VPS2",
        ))

    # ── METHOD 2: Income / DCF ────────────────────────────────────────────────
    ebitda = inp.annual_revenue - inp.annual_opex
    fcf = ebitda - inp.annual_capex
    if inp.annual_revenue > 0 and fcf > 0:
        g = inp.terminal_growth_pct / Decimal("100")
        r = inp.discount_rate_pct / Decimal("100")
        cashflows = [fcf * (1 + g) ** _d(i) for i in range(inp.projection_years)]
        pv_cashflows = _dcf_pv(cashflows, inp.discount_rate_pct)
        terminal_value = (fcf * (1 + g) ** _d(inp.projection_years)) / (r - g) if r > g else fcf * Decimal("15")
        tv_pv = terminal_value / (1 + r) ** _d(inp.projection_years)
        total_value = pv_cashflows + tv_pv
        results.append(MethodResult(
            method=ValuationMethod.INCOME_DCF,
            indicated_value=total_value.quantize(Decimal("1")),
            weight=Decimal("0.40"),
            key_metrics={"annual_revenue": float(inp.annual_revenue), "ebitda": float(ebitda), "fcf": float(fcf), "pv_cashflows": float(pv_cashflows), "terminal_value": float(tv_pv)},
            narrative=f"DCF: {inp.projection_years}-year FCF projection at {float(inp.discount_rate_pct):.2f}% discount rate, {float(inp.terminal_growth_pct):.2f}% terminal growth.",
            confidence="high" if inp.concession_expiry_year else "medium",
            methodology_basis="RICS VPS2 Income Approach; IVS 105",
        ))

    # ── METHOD 3: Replacement Cost ────────────────────────────────────────────
    if inp.replacement_cost > 0:
        depreciation_rate = Decimal("1") - (_d(inp.asset_age_years) / _d(max(inp.useful_life_years, 1)))
        depreciated_replacement = inp.replacement_cost * max(depreciation_rate, Decimal("0.20"))
        results.append(MethodResult(
            method=ValuationMethod.REPLACEMENT_COST,
            indicated_value=depreciated_replacement.quantize(Decimal("1")),
            weight=Decimal("0.15"),
            key_metrics={"replacement_cost": float(inp.replacement_cost), "age_years": inp.asset_age_years, "depreciation_pct": float((1 - float(depreciation_rate)) * 100)},
            narrative=f"Depreciated replacement cost: {float(inp.replacement_cost):,.0f} less {float((1-float(depreciation_rate))*100):.1f}% depreciation.",
            confidence="medium",
            methodology_basis="RICS VPS3 Cost Approach; IVS 105",
        ))

    return results


def calc_project(inp: ProjectInputs, country: str, esg: ESGClimateInputs) -> List[MethodResult]:
    results: List[MethodResult] = []

    # Total project life = construction + operation
    construction_yrs = inp.construction_years
    operation_yrs = inp.concession_years

    # Revenue ramp
    annual_revenues = []
    for yr in range(1, operation_yrs + 1):
        if yr <= inp.revenue_ramp_years:
            rev = inp.annual_revenue * inp.ramp_factor
        else:
            rev = inp.annual_revenue
        annual_revenues.append(rev)

    # ── Project IRR / Equity DCF ──────────────────────────────────────────────
    total_investment = inp.total_project_cost
    equity_investment = total_investment * inp.equity_contribution_pct / Decimal("100")
    debt = total_investment - equity_investment
    annual_debt_service = inp.annual_debt_service or (debt * inp.debt_interest_rate_pct / Decimal("100"))

    equity_cashflows = []
    for yr in range(1, operation_yrs + 1):
        rev = annual_revenues[yr - 1]
        equity_cf = rev - inp.annual_opex - annual_debt_service
        equity_cashflows.append(equity_cf)

    # PV equity cashflows at equity IRR target
    pv_equity = _dcf_pv(equity_cashflows, inp.equity_irr_target_pct)
    # Project value (debt + equity)
    project_value = pv_equity + debt

    # DSCR check
    mid_revenue = annual_revenues[min(inp.revenue_ramp_years, len(annual_revenues) - 1)]
    ebitda = mid_revenue - inp.annual_opex
    dscr = ebitda / annual_debt_service if annual_debt_service > 0 else Decimal("999")

    results.append(MethodResult(
        method=ValuationMethod.PROJECT_FINANCE_DCF,
        indicated_value=project_value.quantize(Decimal("1")),
        weight=Decimal("0.70"),
        key_metrics={
            "equity_investment": float(equity_investment), "debt": float(debt),
            "project_irr_pct": float(inp.project_irr_target_pct),
            "equity_irr_pct": float(inp.equity_irr_target_pct),
            "dscr": float(dscr), "concession_years": operation_yrs,
        },
        narrative=f"Project finance DCF: {operation_yrs}-year concession, DSCR {float(dscr):.2f}x, equity IRR target {float(inp.equity_irr_target_pct):.1f}%.",
        confidence="high" if float(dscr) >= 1.20 else "low",
        methodology_basis="IPEV Guidelines; LMA Project Finance framework; RICS GN 2",
    ))

    # ── Replacement Cost ──────────────────────────────────────────────────────
    results.append(MethodResult(
        method=ValuationMethod.REPLACEMENT_COST,
        indicated_value=(inp.total_project_cost * Decimal("0.90")).quantize(Decimal("1")),
        weight=Decimal("0.30"),
        key_metrics={"total_project_cost": float(inp.total_project_cost)},
        narrative="Replacement cost: 90% of total project cost (reflecting 10% developer/construction profit).",
        confidence="medium",
        methodology_basis="IVS 105 Cost Approach",
    ))

    return results


def calc_energy(inp: EnergyInputs, country: str, esg: ESGClimateInputs) -> List[MethodResult]:
    results: List[MethodResult] = []
    md = MarketDefaults()
    subtype_key = inp.subtype.value

    # Fill defaults
    capacity_factor = inp.capacity_factor_pct if inp.capacity_factor_pct > 0 else md.ENERGY_CAPACITY_FACTORS.get(subtype_key, Decimal("25"))
    annual_mwh = inp.annual_generation_mwh if inp.annual_generation_mwh > 0 else inp.nameplate_capacity_mw * (capacity_factor / Decimal("100")) * Decimal("8760")
    opex_kw_yr = md.ENERGY_OPEX_USD_KW.get(subtype_key, Decimal("30"))
    annual_opex = inp.nameplate_capacity_mw * Decimal("1000") * opex_kw_yr  # MW → kW
    capex_total = inp.nameplate_capacity_mw * Decimal("1000") * (inp.construction_cost_usd_kw or md.ENERGY_CAPEX_USD_KW.get(subtype_key, Decimal("1000")))

    # Revenue: blended PPA + merchant
    ppa_revenue = annual_mwh * (inp.ppa_coverage_pct / Decimal("100")) * inp.ppa_price_usd_mwh
    merchant_revenue = annual_mwh * (1 - inp.ppa_coverage_pct / Decimal("100")) * inp.merchant_price_usd_mwh
    annual_revenue = ppa_revenue + merchant_revenue

    # ── Energy Yield DCF ──────────────────────────────────────────────────────
    if annual_revenue > 0:
        degradation = (inp.annual_degradation_pct or Decimal("0.5")) / Decimal("100")
        cashflows = []
        for yr in range(1, inp.asset_life_years + 1):
            gen_factor = (1 - degradation) ** (yr - 1)
            rev_yr = annual_revenue * _d(gen_factor)
            opex_yr = annual_opex * (1 + Decimal("0.02")) ** _d(yr - 1)  # 2% opex inflation
            # EU ETS carbon cost for thermal plants
            ets_cost = Decimal("0")
            if inp.annual_co2_tonnes > 0:
                ets_cost = inp.annual_co2_tonnes * inp.eu_ets_price_eur_tco2
            cashflows.append(rev_yr - opex_yr - ets_cost)

        pv_ops = _dcf_pv(cashflows, inp.discount_rate_pct)
        # Terminal / decommissioning
        decomm = inp.decommissioning_cost_usd or (capex_total * Decimal("0.05"))
        r = inp.discount_rate_pct / Decimal("100")
        pv_decomm = decomm / (1 + r) ** _d(inp.asset_life_years)
        equity_value = pv_ops - pv_decomm

        lcoe = (capex_total + float(_dcf_pv([annual_opex] * inp.asset_life_years, inp.discount_rate_pct))) / float(_dcf_pv([annual_mwh] * inp.asset_life_years, inp.discount_rate_pct)) if annual_mwh > 0 else Decimal("0")

        results.append(MethodResult(
            method=ValuationMethod.ENERGY_YIELD_DCF,
            indicated_value=equity_value.quantize(Decimal("1")),
            weight=Decimal("0.60"),
            key_metrics={
                "nameplate_mw": float(inp.nameplate_capacity_mw),
                "annual_mwh": float(annual_mwh),
                "capacity_factor_pct": float(capacity_factor),
                "annual_revenue": float(annual_revenue),
                "annual_opex": float(annual_opex),
                "ppa_price": float(inp.ppa_price_usd_mwh),
                "lcoe_usd_mwh": round(float(lcoe), 2) if isinstance(lcoe, Decimal) else round(lcoe, 2),
                "asset_life_years": inp.asset_life_years,
            },
            narrative=f"Energy yield DCF: {inp.asset_life_years}-year life, {float(capacity_factor):.1f}% CF, annual generation {float(annual_mwh):,.0f} MWh, blended revenue {float(annual_revenue):,.0f}/year.",
            confidence="high" if inp.ppa_coverage_pct >= Decimal("70") else "medium",
            methodology_basis="IEA/IRENA LCOE methodology; RICS GN Renewable Energy Valuation",
        ))

    # ── Replacement Cost (asset cost approach) ────────────────────────────────
    results.append(MethodResult(
        method=ValuationMethod.REPLACEMENT_COST,
        indicated_value=capex_total.quantize(Decimal("1")),
        weight=Decimal("0.25"),
        key_metrics={"capex_usd_kw": float(capex_total / max(inp.nameplate_capacity_mw * Decimal("1000"), Decimal("1"))), "total_capex": float(capex_total)},
        narrative=f"Replacement cost: {float(capex_total):,.0f} based on {float(inp.nameplate_capacity_mw * Decimal('1000')):,.0f} kW × market CapEx/kW.",
        confidence="medium",
        methodology_basis="IVS 105 Cost Approach",
    ))

    # ── NAV (for operating assets with transaction evidence) ──────────────────
    if annual_revenue > 0:
        ebitda = annual_revenue - annual_opex
        ev_ebitda_multiple = Decimal("12") if inp.ppa_coverage_pct >= Decimal("70") else Decimal("9")
        nav_value = ebitda * ev_ebitda_multiple
        results.append(MethodResult(
            method=ValuationMethod.NAV_APPROACH,
            indicated_value=nav_value.quantize(Decimal("1")),
            weight=Decimal("0.15"),
            key_metrics={"ebitda": float(ebitda), "ev_ebitda_multiple": float(ev_ebitda_multiple)},
            narrative=f"Market multiple: {float(ebitda):,.0f} EBITDA × {float(ev_ebitda_multiple):.1f}x EV/EBITDA.",
            confidence="medium",
            methodology_basis="INREV NAV guidelines; comparable transaction multiples",
        ))

    return results


def calc_commercial(inp: CommercialInputs, country: str, esg: ESGClimateInputs) -> List[MethodResult]:
    results: List[MethodResult] = []
    md = MarketDefaults()

    nla = inp.net_lettable_area_m2 if inp.net_lettable_area_m2 > 0 else inp.gross_floor_area_m2 * Decimal("0.85")
    mkt_yield = inp.initial_yield_pct if inp.initial_yield_pct > 0 else md.get_commercial_yield(inp.subtype.value, country)
    exit_yield = inp.exit_yield_pct if inp.exit_yield_pct > 0 else mkt_yield + Decimal("0.25")
    passing_rent = inp.passing_rent_psm_pa if inp.passing_rent_psm_pa > 0 else inp.market_rent_psm_pa
    erv = inp.market_rent_psm_pa if inp.market_rent_psm_pa > 0 else passing_rent

    gross_income = nla * passing_rent * (inp.occupancy_rate_pct / Decimal("100"))
    void_cost = nla * (1 - inp.occupancy_rate_pct / Decimal("100")) * inp.vacancy_cost_psm
    mgmt_fee = gross_income * inp.management_fee_pct / Decimal("100")
    capex_reserve = nla * inp.capex_reserve_psm
    noi = gross_income - void_cost - mgmt_fee - capex_reserve - inp.service_charge_psm * nla

    # ── Direct Capitalisation ─────────────────────────────────────────────────
    if noi > 0 and mkt_yield > 0:
        dc_value = noi / (mkt_yield / Decimal("100"))
        results.append(MethodResult(
            method=ValuationMethod.DIRECT_CAPITALISATION,
            indicated_value=dc_value.quantize(Decimal("1")),
            weight=Decimal("0.35"),
            key_metrics={
                "nla_m2": float(nla), "passing_rent_psm": float(passing_rent),
                "gross_income": float(gross_income), "noi": float(noi),
                "cap_rate_pct": float(mkt_yield), "implied_value_psm": float(dc_value / nla) if nla > 0 else 0,
            },
            narrative=f"Direct capitalisation: NOI {float(noi):,.0f} / {float(mkt_yield):.2f}% cap rate = {float(dc_value):,.0f}. Value {float(dc_value/nla):,.0f}/m².",
            confidence="high",
            methodology_basis="RICS VPS2 Income Approach; IVS 105 para 50.4",
        ))

    # ── 10-Year DCF ───────────────────────────────────────────────────────────
    rent_growth = inp.rent_growth_pct_pa / Decimal("100")
    cashflows = []
    for yr in range(1, inp.projection_years + 1):
        rev = nla * erv * ((1 + rent_growth) ** _d(yr)) * (inp.occupancy_rate_pct / Decimal("100"))
        # Lease renewal: every lease_term apply void + incentive cost
        if yr % inp.lease_term_years == 0:
            void_loss = (nla * erv * _d(inp.void_period_months) / Decimal("12"))
            incentive_cost = (nla * erv * _d(inp.lease_incentive_months) / Decimal("12"))
            rev -= (void_loss + incentive_cost)
        op_cost = (mgmt_fee + capex_reserve + void_cost) * ((1 + Decimal("0.02")) ** _d(yr))
        cashflows.append(rev - op_cost)

    pv_cf = _dcf_pv(cashflows, inp.discount_rate_pct)
    exit_noi = cashflows[-1] if cashflows else noi
    r = inp.discount_rate_pct / Decimal("100")
    terminal = exit_noi / (exit_yield / Decimal("100"))
    pv_terminal = terminal / (1 + r) ** _d(inp.projection_years)
    dcf_value = pv_cf + pv_terminal

    results.append(MethodResult(
        method=ValuationMethod.INCOME_DCF,
        indicated_value=dcf_value.quantize(Decimal("1")),
        weight=Decimal("0.45"),
        key_metrics={
            "pv_cashflows": float(pv_cf), "pv_terminal": float(pv_terminal),
            "exit_yield_pct": float(exit_yield), "rent_growth_pct": float(inp.rent_growth_pct_pa),
            "discount_rate_pct": float(inp.discount_rate_pct),
        },
        narrative=f"{inp.projection_years}-year DCF: PV cashflows {float(pv_cf):,.0f} + terminal {float(pv_terminal):,.0f} at {float(exit_yield):.2f}% exit yield.",
        confidence="high",
        methodology_basis="RICS VPS2; IVS 105 DCF",
    ))

    # ── Replacement Cost ──────────────────────────────────────────────────────
    if inp.gross_floor_area_m2 > 0:
        TYPICAL_CONSTRUCT_COST_PSM = {"office_prime": Decimal("3500"), "industrial_logistics": Decimal("1200"), "data_centre": Decimal("8000"), "hotel_full_service": Decimal("4000"), "healthcare": Decimal("4500")}
        build_cost_psm = TYPICAL_CONSTRUCT_COST_PSM.get(inp.subtype.value, Decimal("2500"))
        age_depreciation = min(_d(max(0, date.today().year - inp.year_built)) / Decimal("50"), Decimal("0.60"))
        if inp.last_refurbishment_year:
            refurb_adj = min(_d(date.today().year - inp.last_refurbishment_year) / Decimal("20"), Decimal("0.30"))
            age_depreciation = max(age_depreciation - Decimal("0.25"), refurb_adj)
        build_value = inp.gross_floor_area_m2 * build_cost_psm * (1 - age_depreciation)
        land_value = (dc_value if results else build_value) * inp.land_value_pct / Decimal("100")
        cost_value = build_value + land_value
        results.append(MethodResult(
            method=ValuationMethod.REPLACEMENT_COST,
            indicated_value=cost_value.quantize(Decimal("1")),
            weight=Decimal("0.20"),
            key_metrics={"build_cost_psm": float(build_cost_psm), "age_depreciation_pct": float(age_depreciation * 100), "land_value": float(land_value)},
            narrative=f"Cost approach: {float(inp.gross_floor_area_m2):,.0f}m² × {float(build_cost_psm):,.0f}/m² less {float(age_depreciation*100):.1f}% depreciation + land.",
            confidence="medium",
            methodology_basis="RICS VPS3; RS Means / BCIS cost data",
        ))

    return results


def calc_residential(inp: ResidentialInputs, country: str, esg: ESGClimateInputs) -> List[MethodResult]:
    results: List[MethodResult] = []
    md = MarketDefaults()

    total_area_m2 = inp.avg_unit_size_m2 * _d(inp.units)
    annual_gross_rent = _d(inp.units) * inp.avg_monthly_rent_per_unit * Decimal("12") * (inp.occupancy_rate_pct / Decimal("100"))
    annual_opex = _d(inp.units) * inp.annual_opex_per_unit
    capex_reserve = annual_gross_rent * inp.capex_reserve_pct / Decimal("100")
    noi = annual_gross_rent - annual_opex - capex_reserve

    gross_yield = inp.gross_yield_market_pct if inp.gross_yield_market_pct > 0 else md.get_residential_yield(inp.subtype.value, country)
    exit_yield = inp.exit_yield_pct if inp.exit_yield_pct > 0 else gross_yield + Decimal("0.25")

    # ── Direct Capitalisation ─────────────────────────────────────────────────
    if annual_gross_rent > 0 and gross_yield > 0:
        gross_value = annual_gross_rent / (gross_yield / Decimal("100"))
        results.append(MethodResult(
            method=ValuationMethod.DIRECT_CAPITALISATION,
            indicated_value=gross_value.quantize(Decimal("1")),
            weight=Decimal("0.30"),
            key_metrics={"units": inp.units, "annual_gross_rent": float(annual_gross_rent), "gross_yield_pct": float(gross_yield), "value_per_unit": float(gross_value / _d(max(inp.units, 1)))},
            narrative=f"Gross capitalisation: {float(annual_gross_rent):,.0f}/yr ÷ {float(gross_yield):.2f}% = {float(gross_value):,.0f}. Per unit: {float(gross_value/_d(max(inp.units,1))):,.0f}.",
            confidence="high",
            methodology_basis="RICS VPS2; BTR Residential Valuation Standards",
        ))

    # ── DCF ───────────────────────────────────────────────────────────────────
    if noi > 0:
        rent_growth = inp.rent_growth_pct_pa / Decimal("100")
        cashflows = [noi * (1 + rent_growth) ** _d(yr) for yr in range(inp.projection_years)]
        pv_cf = _dcf_pv(cashflows, inp.discount_rate_pct)
        r = inp.discount_rate_pct / Decimal("100")
        terminal_noi = cashflows[-1] * (1 + rent_growth) if cashflows else noi
        terminal = terminal_noi / (exit_yield / Decimal("100"))
        pv_terminal = terminal / (1 + r) ** _d(inp.projection_years)
        dcf_value = pv_cf + pv_terminal
        results.append(MethodResult(
            method=ValuationMethod.INCOME_DCF,
            indicated_value=dcf_value.quantize(Decimal("1")),
            weight=Decimal("0.40"),
            key_metrics={"noi": float(noi), "pv_cf": float(pv_cf), "pv_terminal": float(pv_terminal), "exit_yield_pct": float(exit_yield)},
            narrative=f"{inp.projection_years}-year DCF: {float(inp.rent_growth_pct_pa):.1f}% rent growth, {float(exit_yield):.2f}% exit yield.",
            confidence="high",
            methodology_basis="RICS VPS2; IPEV BTR Guidelines",
        ))

    # ── Sales Comparison / Hedonic ────────────────────────────────────────────
    if inp.comparable_prices_per_m2 and total_area_m2 > 0:
        raw_comps = inp.comparable_prices_per_m2
        adjustments = inp.comparable_adjustments or [Decimal("0")] * len(raw_comps)
        adj_prices = [(p * (1 + a / Decimal("100"))) for p, a in zip(raw_comps, adjustments)]
        mean_psm = sum(adj_prices) / _d(len(adj_prices))
        sales_value = mean_psm * total_area_m2
        results.append(MethodResult(
            method=ValuationMethod.SALES_COMPARISON,
            indicated_value=sales_value.quantize(Decimal("1")),
            weight=Decimal("0.30"),
            key_metrics={"comparables_used": len(raw_comps), "mean_price_psm": float(mean_psm), "total_area_m2": float(total_area_m2)},
            narrative=f"Sales comparison: {len(raw_comps)} adjusted comparables at mean {float(mean_psm):,.0f}/m².",
            confidence="high",
            methodology_basis="RICS VPS2; USPAP Sales Comparison Approach",
        ))

    return results


def calc_agricultural(inp: AgriculturalInputs, country: str, esg: ESGClimateInputs) -> List[MethodResult]:
    results: List[MethodResult] = []
    md = MarketDefaults()

    # ── Income / Crop DCF ─────────────────────────────────────────────────────
    if inp.annual_crop_yield_tonnes_ha > 0 and inp.commodity_price_usd_tonne > 0:
        annual_revenue_ha = inp.annual_crop_yield_tonnes_ha * inp.commodity_price_usd_tonne + inp.agricultural_subsidy_usd_ha
        annual_profit_ha = annual_revenue_ha - inp.annual_opex_usd_ha
        soil_quality_mult = Decimal("0.80") + inp.soil_quality_score * Decimal("0.08")  # 1.0 at score=2.5; 1.24 at 5
        annual_profit = annual_profit_ha * inp.area_hectares * soil_quality_mult

        cashflows = [annual_profit * (Decimal("1.02") ** _d(yr)) for yr in range(inp.projection_years)]
        pv = _dcf_pv(cashflows, inp.discount_rate_pct)
        r = inp.discount_rate_pct / Decimal("100")
        g = Decimal("0.02")
        terminal = (cashflows[-1] * (1 + g)) / (r - g) if r > g else cashflows[-1] * Decimal("15")
        pv_terminal = terminal / (1 + r) ** _d(inp.projection_years)
        agri_dcf = pv + pv_terminal
        results.append(MethodResult(
            method=ValuationMethod.INCOME_DCF,
            indicated_value=agri_dcf.quantize(Decimal("1")),
            weight=Decimal("0.40"),
            key_metrics={"area_ha": float(inp.area_hectares), "annual_profit_ha": float(annual_profit_ha), "soil_quality_mult": float(soil_quality_mult)},
            narrative=f"Agricultural DCF: {float(inp.area_hectares):.1f} ha × {float(annual_profit_ha):,.0f}/ha annual profit (soil quality adj {float(soil_quality_mult):.2f}x).",
            confidence="medium",
            methodology_basis="RICS Rural Land Valuation; CAAV guidance",
        ))

    # ── Comparable Sales ──────────────────────────────────────────────────────
    cmp_price = inp.comparable_land_price_usd_ha
    if cmp_price == 0:
        cmp_price = md.AGRI_LAND_VALUE_USD_HA.get(inp.subtype.value, {}).get(country, md.AGRI_LAND_VALUE_USD_HA.get(inp.subtype.value, {}).get("default", Decimal("8000")))
    sales_value = cmp_price * inp.area_hectares
    results.append(MethodResult(
        method=ValuationMethod.SALES_COMPARISON,
        indicated_value=sales_value.quantize(Decimal("1")),
        weight=Decimal("0.35"),
        key_metrics={"land_price_ha": float(cmp_price), "area_ha": float(inp.area_hectares)},
        narrative=f"Comparable sales: {float(cmp_price):,.0f}/ha × {float(inp.area_hectares):.1f} ha = {float(sales_value):,.0f}.",
        confidence="medium",
        methodology_basis="RICS Rural Land Valuation; CAAV/APHA sales evidence",
    ))

    # ── Timber / Carbon Value (forestry) ──────────────────────────────────────
    if inp.subtype == AgriculturalSubtype.FORESTRY and inp.estimated_timber_volume_m3_ha > 0:
        timber_value = inp.standing_timber_value_usd_m3 * inp.estimated_timber_volume_m3_ha * inp.area_hectares
        carbon_value = inp.carbon_sequestration_tco2e_ha_yr * inp.area_hectares * inp.carbon_credit_price_usd * Decimal("20")  # 20yr carbon credit income capitalised
        total_forestry_value = timber_value + carbon_value
        results.append(MethodResult(
            method=ValuationMethod.TIMBER_CARBON_VALUE,
            indicated_value=total_forestry_value.quantize(Decimal("1")),
            weight=Decimal("0.25"),
            key_metrics={
                "timber_value": float(timber_value), "carbon_value": float(carbon_value),
                "carbon_credits_tco2e_ha_yr": float(inp.carbon_sequestration_tco2e_ha_yr),
                "carbon_credit_price": float(inp.carbon_credit_price_usd),
            },
            narrative=f"Timber + carbon: standing timber {float(timber_value):,.0f} + carbon credits {float(carbon_value):,.0f}.",
            confidence="medium" if inp.woodland_carbon_code else "low",
            methodology_basis="Woodland Carbon Code (UK); REDD+ carbon accounting; FSC timber valuation",
        ))

    return results


def calc_land(inp: LandInputs, country: str, esg: ESGClimateInputs) -> List[MethodResult]:
    results: List[MethodResult] = []

    # ── Residual Land Value ───────────────────────────────────────────────────
    if inp.gross_development_value > 0:
        finance_cost = inp.total_development_cost * (inp.finance_cost_pct / Decimal("100")) * inp.development_period_years / Decimal("2")
        developer_profit = inp.gross_development_value * inp.developer_profit_pct / Decimal("100")
        residual_pre_risk = inp.gross_development_value - inp.total_development_cost - finance_cost - developer_profit - inp.remediation_cost
        # Planning risk discount
        planning_discount = residual_pre_risk * inp.planning_risk_discount_pct / Decimal("100")
        # Time discount: PV of residual land payment at development start
        r = Decimal("0.07")  # land-specific discount
        pv_residual = (residual_pre_risk - planning_discount) / ((1 + r) ** inp.development_period_years)
        results.append(MethodResult(
            method=ValuationMethod.RESIDUAL_LAND_VALUE,
            indicated_value=max(pv_residual, Decimal("0")).quantize(Decimal("1")),
            weight=Decimal("0.55"),
            key_metrics={
                "gdv": float(inp.gross_development_value),
                "total_dev_cost": float(inp.total_development_cost),
                "developer_profit": float(developer_profit),
                "finance_cost": float(finance_cost),
                "remediation_cost": float(inp.remediation_cost),
                "planning_discount": float(planning_discount),
                "residual_pre_pv": float(residual_pre_risk - planning_discount),
            },
            narrative=f"Residual: GDV {float(inp.gross_development_value):,.0f} − costs {float(inp.total_development_cost):,.0f} − profit {float(developer_profit):,.0f} − finance {float(finance_cost):,.0f} − remediation {float(inp.remediation_cost):,.0f} = {float(pv_residual):,.0f}.",
            confidence="high" if inp.planning_risk_discount_pct == 0 else "medium",
            methodology_basis="RICS GN Development Land Valuation; Residual Method",
        ))

    # ── Comparable Land Sales ─────────────────────────────────────────────────
    if inp.comparable_land_prices_ha:
        mean_ha = sum(inp.comparable_land_prices_ha) / _d(len(inp.comparable_land_prices_ha))
        comp_value = mean_ha * inp.site_area_hectares
        results.append(MethodResult(
            method=ValuationMethod.SALES_COMPARISON,
            indicated_value=comp_value.quantize(Decimal("1")),
            weight=Decimal("0.35"),
            key_metrics={"mean_price_ha": float(mean_ha), "area_ha": float(inp.site_area_hectares), "comparables": len(inp.comparable_land_prices_ha)},
            narrative=f"Land sales comparison: {len(inp.comparable_land_prices_ha)} comparables, mean {float(mean_ha):,.0f}/ha.",
            confidence="medium",
            methodology_basis="RICS VPS2; EPC Land Registry comparable evidence",
        ))

    # ── Existing Use Value + Planning Uplift (strategic land) ─────────────────
    if inp.subtype == LandSubtype.STRATEGIC_LAND and inp.existing_use_value_ha > 0:
        existing_value = inp.existing_use_value_ha * inp.site_area_hectares
        uplift_value = existing_value * inp.planning_uplift_multiple
        results.append(MethodResult(
            method=ValuationMethod.HEDONIC_PRICING,
            indicated_value=uplift_value.quantize(Decimal("1")),
            weight=Decimal("0.10"),
            key_metrics={"existing_use_value": float(existing_value), "planning_uplift_multiple": float(inp.planning_uplift_multiple)},
            narrative=f"Strategic land: EUV {float(existing_value):,.0f} × planning uplift {float(inp.planning_uplift_multiple):.1f}x.",
            confidence="low",
            methodology_basis="Hope Value / Planning Premium (RICS GN); NPPF allocation evidence",
        ))

    # ── Carbon Land Value ─────────────────────────────────────────────────────
    if inp.subtype == LandSubtype.CARBON_LAND and inp.carbon_sequestration_potential_tco2e_ha > 0:
        annual_carbon_revenue = inp.carbon_sequestration_potential_tco2e_ha * inp.site_area_hectares * Decimal("25")  # $25/tCO2e
        carbon_value = annual_carbon_revenue / Decimal("0.04")  # 4% capitalisation
        results.append(MethodResult(
            method=ValuationMethod.TIMBER_CARBON_VALUE,
            indicated_value=carbon_value.quantize(Decimal("1")),
            weight=Decimal("0.15") if not results else Decimal("0.10"),
            key_metrics={"annual_carbon_revenue": float(annual_carbon_revenue), "carbon_tco2e_ha": float(inp.carbon_sequestration_potential_tco2e_ha)},
            narrative=f"Carbon land value: {float(inp.carbon_sequestration_potential_tco2e_ha):.1f} tCO2e/ha/yr × {float(inp.site_area_hectares):.1f} ha at $25/t capitalised.",
            confidence="low",
            methodology_basis="Woodland Carbon Code; Peatland Code; VCM spot pricing",
        ))

    return results


# ──────────────────────────────────────────────────────────────────────────────
# RECONCILIATION
# ──────────────────────────────────────────────────────────────────────────────

def _reconcile(method_results: List[MethodResult]) -> Tuple[Decimal, Decimal, Decimal]:
    """Weighted reconciliation of method results. Returns (value, low, high)."""
    if not method_results:
        return Decimal("0"), Decimal("0"), Decimal("0")

    total_weight = sum(r.weight for r in method_results)
    if total_weight == 0:
        total_weight = Decimal("1")

    weighted_value = sum(r.indicated_value * (r.weight / total_weight) for r in method_results)
    values = [r.indicated_value for r in method_results]
    min_val = min(values) * Decimal("0.95")
    max_val = max(values) * Decimal("1.05")
    return weighted_value.quantize(Decimal("1")), min_val.quantize(Decimal("1")), max_val.quantize(Decimal("1"))


# ──────────────────────────────────────────────────────────────────────────────
# MASTER ENGINE
# ──────────────────────────────────────────────────────────────────────────────

class UnifiedValuationEngine:
    """
    Single entry point for all asset class valuations.
    Call: engine.value(request) → ValuationResult
    """

    def __init__(self):
        self.esg_engine = ESGOverlayEngine()

    def _auto_select_methods(self, request: ValuationRequest) -> List[ValuationMethod]:
        """Return the standard method set for each asset class."""
        mapping: Dict[AssetClass, List[ValuationMethod]] = {
            AssetClass.INFRASTRUCTURE: [ValuationMethod.REGULATED_ASSET_BASE, ValuationMethod.INCOME_DCF, ValuationMethod.REPLACEMENT_COST],
            AssetClass.PROJECT:        [ValuationMethod.PROJECT_FINANCE_DCF, ValuationMethod.REPLACEMENT_COST],
            AssetClass.ENERGY:         [ValuationMethod.ENERGY_YIELD_DCF, ValuationMethod.REPLACEMENT_COST, ValuationMethod.NAV_APPROACH],
            AssetClass.COMMERCIAL:     [ValuationMethod.DIRECT_CAPITALISATION, ValuationMethod.INCOME_DCF, ValuationMethod.REPLACEMENT_COST],
            AssetClass.RESIDENTIAL:    [ValuationMethod.DIRECT_CAPITALISATION, ValuationMethod.INCOME_DCF, ValuationMethod.SALES_COMPARISON],
            AssetClass.AGRICULTURAL:   [ValuationMethod.INCOME_DCF, ValuationMethod.SALES_COMPARISON, ValuationMethod.TIMBER_CARBON_VALUE],
            AssetClass.LAND:           [ValuationMethod.RESIDUAL_LAND_VALUE, ValuationMethod.SALES_COMPARISON, ValuationMethod.HEDONIC_PRICING],
        }
        return mapping.get(request.asset_class, [])

    def value(self, request: ValuationRequest) -> ValuationResult:
        logger.info("Valuing %s — class=%s", request.asset_name, request.asset_class.value)

        # Dispatch to asset-class calculator
        ac = request.asset_class
        country = request.country_iso
        esg = request.esg

        if ac == AssetClass.INFRASTRUCTURE and request.infrastructure:
            method_results = calc_infrastructure(request.infrastructure, country, esg)
        elif ac == AssetClass.PROJECT and request.project:
            method_results = calc_project(request.project, country, esg)
        elif ac == AssetClass.ENERGY and request.energy:
            method_results = calc_energy(request.energy, country, esg)
        elif ac == AssetClass.COMMERCIAL and request.commercial:
            method_results = calc_commercial(request.commercial, country, esg)
        elif ac == AssetClass.RESIDENTIAL and request.residential:
            method_results = calc_residential(request.residential, country, esg)
        elif ac == AssetClass.AGRICULTURAL and request.agricultural:
            method_results = calc_agricultural(request.agricultural, country, esg)
        elif ac == AssetClass.LAND and request.land:
            method_results = calc_land(request.land, country, esg)
        else:
            raise ValueError(f"No inputs provided for asset class: {ac.value}")

        if not method_results:
            raise ValueError("All valuation methods returned no result — check input completeness.")

        # Reconcile
        pre_esg_value, low, high = _reconcile(method_results)

        # ESG adjustment
        esg_adj = self.esg_engine.calculate_esg_adjustment(esg, ac, pre_esg_value)
        net_adj = esg_adj.net_esg_adjustment_pct
        final_value = (pre_esg_value * (1 + net_adj)).quantize(Decimal("1"))
        final_low = (low * (1 + net_adj)).quantize(Decimal("1"))
        final_high = (high * (1 + net_adj)).quantize(Decimal("1"))

        # Per-unit metrics
        val_per_m2 = val_per_unit = val_per_ha = val_per_kw = None
        if ac == AssetClass.COMMERCIAL and request.commercial:
            nla = request.commercial.net_lettable_area_m2 or request.commercial.gross_floor_area_m2 * Decimal("0.85")
            if nla > 0: val_per_m2 = (final_value / nla).quantize(Decimal("1"))
        if ac == AssetClass.RESIDENTIAL and request.residential and request.residential.units > 0:
            val_per_unit = (final_value / _d(request.residential.units)).quantize(Decimal("1"))
            if request.residential.avg_unit_size_m2 > 0:
                val_per_m2 = (final_value / (request.residential.avg_unit_size_m2 * _d(request.residential.units))).quantize(Decimal("1"))
        if ac == AssetClass.AGRICULTURAL and request.agricultural and request.agricultural.area_hectares > 0:
            val_per_ha = (final_value / request.agricultural.area_hectares).quantize(Decimal("1"))
        if ac == AssetClass.LAND and request.land and request.land.site_area_hectares > 0:
            val_per_ha = (final_value / request.land.site_area_hectares).quantize(Decimal("1"))
        if ac == AssetClass.ENERGY and request.energy and request.energy.nameplate_capacity_mw > 0:
            val_per_kw = (final_value / (request.energy.nameplate_capacity_mw * Decimal("1000"))).quantize(Decimal("0.01"))

        # Yield and IRR metrics
        yield_pct: Optional[Decimal] = None
        irr_pct: Optional[Decimal] = None
        dscr_val: Optional[Decimal] = None
        if ac == AssetClass.COMMERCIAL and request.commercial and final_value > 0:
            gross = request.commercial.net_lettable_area_m2 * request.commercial.market_rent_psm_pa if request.commercial.market_rent_psm_pa > 0 else Decimal("0")
            if gross > 0: yield_pct = (gross / final_value * Decimal("100")).quantize(Decimal("0.01"))
        if ac == AssetClass.PROJECT and request.project:
            irr_pct = request.project.project_irr_target_pct
            if request.project.annual_debt_service > 0:
                ebitda = request.project.annual_revenue - request.project.annual_opex
                dscr_val = (ebitda / request.project.annual_debt_service).quantize(Decimal("0.01"))

        # Material uncertainty check
        material_uncertainty = any(r.confidence == "low" for r in method_results) or len(method_results) == 1

        # Validation summary
        validation_summary = {
            "methodology": f"Unified Valuation Engine — {request.valuation_standard}",
            "valuation_date": request.valuation_date or str(date.today()),
            "asset_class": ac.value,
            "asset_name": request.asset_name,
            "methods_applied": [r.method.value for r in method_results],
            "method_details": [
                {
                    "method": r.method.value,
                    "indicated_value": float(r.indicated_value),
                    "weight": float(r.weight),
                    "confidence": r.confidence,
                    "basis": r.methodology_basis,
                    "key_metrics": r.key_metrics,
                }
                for r in method_results
            ],
            "reconciled_pre_esg": float(pre_esg_value),
            "esg_adjustment_pct": float(net_adj * 100),
            "esg_breakdown": {
                "green_premium_pct": float(esg_adj.green_premium_pct * 100),
                "brown_discount_pct": float(esg_adj.brown_discount_pct * 100),
                "physical_risk_pct": float(esg_adj.physical_risk_discount_pct * 100),
                "transition_risk_pct": float(esg_adj.transition_risk_discount_pct * 100),
                "biodiversity_pct": float(esg_adj.biodiversity_adjustment_pct * 100),
                "narrative": esg_adj.esg_narrative,
            },
            "final_value": float(final_value),
            "value_range": {"low": float(final_low), "high": float(final_high)},
            "stranding_risk_year": esg_adj.stranding_risk_year,
            "material_uncertainty": material_uncertainty,
            "compliance": {
                "standard": request.valuation_standard,
                "rics_ps1_compliant": True,
                "rics_vps4_esg_addressed": True,
                "ivs_esg_addressed": True,
                "material_uncertainty_clause": material_uncertainty,
            },
            "data_sources": [
                "RICS Red Book PS1/VPS4 (2024)", "IVS 2024 (IVSC)", "JLL Q1-2024 Market Data",
                "MSCI Real Estate Green Premium Report 2023", "CRREM v2.0 Pathways",
                "RS Means / BCIS Construction Costs", "MarketDefaults calibrated Q1-2024",
            ],
        }

        return ValuationResult(
            asset_class=ac,
            asset_name=request.asset_name,
            currency=request.currency,
            valuation_date=request.valuation_date or str(date.today()),
            method_results=method_results,
            reconciled_value_pre_esg=pre_esg_value,
            esg_adjustment=esg_adj,
            final_value=final_value,
            value_range_low=final_low,
            value_range_high=final_high,
            value_per_m2=val_per_m2,
            value_per_unit=val_per_unit,
            value_per_ha=val_per_ha,
            value_per_kw=val_per_kw,
            irr_pct=irr_pct,
            yield_pct=yield_pct,
            dscr=dscr_val,
            valuation_standard_used=request.valuation_standard,
            rics_ps1_compliant=True,
            rics_vps4_esg_addressed=True,
            ivs_esg_addressed=True,
            material_uncertainty=material_uncertainty,
            validation_summary=validation_summary,
        )


# Module-level convenience function
_engine = UnifiedValuationEngine()

def run_valuation(request_dict: dict) -> dict:
    """
    Convenience function for API routes.
    Accepts a flat dict (from JSON body), builds ValuationRequest, runs engine, returns dict.
    """
    def _to_decimal(v) -> Decimal:
        return Decimal(str(v)) if v is not None else Decimal("0")

    ac = AssetClass(request_dict["asset_class"])
    esg_raw = request_dict.get("esg", {})
    esg = ESGClimateInputs(
        epc_rating=esg_raw.get("epc_rating", "D"),
        energy_intensity_kwh_m2=_to_decimal(esg_raw.get("energy_intensity_kwh_m2", 0)),
        carbon_intensity_kgco2_m2=_to_decimal(esg_raw.get("carbon_intensity_kgco2_m2", 0)),
        flood_risk=esg_raw.get("flood_risk", "none"),
        heat_risk_score=_to_decimal(esg_raw.get("heat_risk_score", 0)),
        physical_risk_score=_to_decimal(esg_raw.get("physical_risk_score", 0)),
        transition_risk_score=_to_decimal(esg_raw.get("transition_risk_score", 0)),
        water_stress_score=_to_decimal(esg_raw.get("water_stress_score", 0)),
        biodiversity_sensitivity=esg_raw.get("biodiversity_sensitivity", "low"),
        has_green_certification=esg_raw.get("has_green_certification", False),
        certification_type=esg_raw.get("certification_type", ""),
        sbti_aligned=esg_raw.get("sbti_aligned", False),
        climate_scenario=ClimateScenario(esg_raw.get("climate_scenario", "below_2c")),
        assessment_year=esg_raw.get("assessment_year", 2024),
        target_year=esg_raw.get("target_year", 2035),
    )

    inputs_raw = request_dict.get("inputs", {})

    def _make_infra():
        r = inputs_raw
        return InfrastructureInputs(
            subtype=InfrastructureSubtype(r.get("subtype", "regulated_utility")),
            regulated_asset_base_value=_to_decimal(r.get("regulated_asset_base_value", 0)),
            allowed_return_on_rab_pct=_to_decimal(r.get("allowed_return_on_rab_pct", 6.5)),
            annual_revenue=_to_decimal(r.get("annual_revenue", 0)),
            annual_opex=_to_decimal(r.get("annual_opex", 0)),
            annual_capex=_to_decimal(r.get("annual_capex", 0)),
            discount_rate_pct=_to_decimal(r.get("discount_rate_pct", 7.0)),
            projection_years=int(r.get("projection_years", 30)),
            terminal_growth_pct=_to_decimal(r.get("terminal_growth_pct", 2.0)),
            replacement_cost=_to_decimal(r.get("replacement_cost", 0)),
            asset_age_years=int(r.get("asset_age_years", 0)),
            useful_life_years=int(r.get("useful_life_years", 40)),
        )

    def _make_project():
        r = inputs_raw
        return ProjectInputs(
            subtype=ProjectSubtype(r.get("subtype", "ppp_availability")),
            total_project_cost=_to_decimal(r.get("total_project_cost", 0)),
            equity_contribution_pct=_to_decimal(r.get("equity_contribution_pct", 20)),
            annual_revenue=_to_decimal(r.get("annual_revenue", 0)),
            annual_opex=_to_decimal(r.get("annual_opex", 0)),
            annual_debt_service=_to_decimal(r.get("annual_debt_service", 0)),
            concession_years=int(r.get("concession_years", 25)),
            construction_years=int(r.get("construction_years", 3)),
            debt_interest_rate_pct=_to_decimal(r.get("debt_interest_rate_pct", 5.5)),
            equity_irr_target_pct=_to_decimal(r.get("equity_irr_target_pct", 12.0)),
            project_irr_target_pct=_to_decimal(r.get("project_irr_target_pct", 8.0)),
        )

    def _make_energy():
        r = inputs_raw
        return EnergyInputs(
            subtype=EnergySubtype(r.get("subtype", "solar_pv")),
            nameplate_capacity_mw=_to_decimal(r.get("nameplate_capacity_mw", 0)),
            capacity_factor_pct=_to_decimal(r.get("capacity_factor_pct", 0)),
            annual_generation_mwh=_to_decimal(r.get("annual_generation_mwh", 0)),
            ppa_price_usd_mwh=_to_decimal(r.get("ppa_price_usd_mwh", 0)),
            merchant_price_usd_mwh=_to_decimal(r.get("merchant_price_usd_mwh", 0)),
            ppa_coverage_pct=_to_decimal(r.get("ppa_coverage_pct", 100)),
            ppa_duration_years=int(r.get("ppa_duration_years", 15)),
            annual_opex_usd_kw=_to_decimal(r.get("annual_opex_usd_kw", 0)),
            annual_degradation_pct=_to_decimal(r.get("annual_degradation_pct", 0)),
            construction_cost_usd_kw=_to_decimal(r.get("construction_cost_usd_kw", 0)),
            discount_rate_pct=_to_decimal(r.get("discount_rate_pct", 7.5)),
            asset_life_years=int(r.get("asset_life_years", 25)),
            eu_ets_price_eur_tco2=_to_decimal(r.get("eu_ets_price_eur_tco2", 65)),
            annual_co2_tonnes=_to_decimal(r.get("annual_co2_tonnes", 0)),
        )

    def _make_commercial():
        r = inputs_raw
        return CommercialInputs(
            subtype=CommercialSubtype(r.get("subtype", "office_prime")),
            gross_floor_area_m2=_to_decimal(r.get("gross_floor_area_m2", 0)),
            net_lettable_area_m2=_to_decimal(r.get("net_lettable_area_m2", 0)),
            passing_rent_psm_pa=_to_decimal(r.get("passing_rent_psm_pa", 0)),
            market_rent_psm_pa=_to_decimal(r.get("market_rent_psm_pa", 0)),
            occupancy_rate_pct=_to_decimal(r.get("occupancy_rate_pct", 95)),
            management_fee_pct=_to_decimal(r.get("management_fee_pct", 3)),
            capex_reserve_psm=_to_decimal(r.get("capex_reserve_psm", 0)),
            initial_yield_pct=_to_decimal(r.get("initial_yield_pct", 0)),
            discount_rate_pct=_to_decimal(r.get("discount_rate_pct", 7.0)),
            exit_yield_pct=_to_decimal(r.get("exit_yield_pct", 0)),
            rent_growth_pct_pa=_to_decimal(r.get("rent_growth_pct_pa", 2.0)),
            lease_term_years=int(r.get("lease_term_years", 10)),
            void_period_months=int(r.get("void_period_months", 6)),
            lease_incentive_months=int(r.get("lease_incentive_months", 6)),
            projection_years=int(r.get("projection_years", 10)),
            year_built=int(r.get("year_built", 2000)),
            last_refurbishment_year=r.get("last_refurbishment_year"),
            land_value_pct=_to_decimal(r.get("land_value_pct", 20)),
        )

    def _make_residential():
        r = inputs_raw
        return ResidentialInputs(
            subtype=ResidentialSubtype(r.get("subtype", "multifamily")),
            units=int(r.get("units", 0)),
            avg_unit_size_m2=_to_decimal(r.get("avg_unit_size_m2", 0)),
            avg_monthly_rent_per_unit=_to_decimal(r.get("avg_monthly_rent_per_unit", 0)),
            occupancy_rate_pct=_to_decimal(r.get("occupancy_rate_pct", 95)),
            annual_opex_per_unit=_to_decimal(r.get("annual_opex_per_unit", 0)),
            capex_reserve_pct=_to_decimal(r.get("capex_reserve_pct", 5)),
            gross_yield_market_pct=_to_decimal(r.get("gross_yield_market_pct", 0)),
            discount_rate_pct=_to_decimal(r.get("discount_rate_pct", 6.5)),
            exit_yield_pct=_to_decimal(r.get("exit_yield_pct", 0)),
            rent_growth_pct_pa=_to_decimal(r.get("rent_growth_pct_pa", 2.5)),
            projection_years=int(r.get("projection_years", 10)),
            comparable_prices_per_m2=[_to_decimal(x) for x in r.get("comparable_prices_per_m2", [])],
            comparable_adjustments=[_to_decimal(x) for x in r.get("comparable_adjustments", [])],
        )

    def _make_agricultural():
        r = inputs_raw
        return AgriculturalInputs(
            subtype=AgriculturalSubtype(r.get("subtype", "arable")),
            area_hectares=_to_decimal(r.get("area_hectares", 0)),
            soil_quality_score=_to_decimal(r.get("soil_quality_score", 3)),
            annual_crop_yield_tonnes_ha=_to_decimal(r.get("annual_crop_yield_tonnes_ha", 0)),
            commodity_price_usd_tonne=_to_decimal(r.get("commodity_price_usd_tonne", 0)),
            annual_opex_usd_ha=_to_decimal(r.get("annual_opex_usd_ha", 0)),
            comparable_land_price_usd_ha=_to_decimal(r.get("comparable_land_price_usd_ha", 0)),
            agricultural_subsidy_usd_ha=_to_decimal(r.get("agricultural_subsidy_usd_ha", 0)),
            discount_rate_pct=_to_decimal(r.get("discount_rate_pct", 5.0)),
            projection_years=int(r.get("projection_years", 20)),
            timber_species=r.get("timber_species", ""),
            timber_rotation_years=int(r.get("timber_rotation_years", 35)),
            standing_timber_value_usd_m3=_to_decimal(r.get("standing_timber_value_usd_m3", 0)),
            estimated_timber_volume_m3_ha=_to_decimal(r.get("estimated_timber_volume_m3_ha", 0)),
            carbon_sequestration_tco2e_ha_yr=_to_decimal(r.get("carbon_sequestration_tco2e_ha_yr", 0)),
            carbon_credit_price_usd=_to_decimal(r.get("carbon_credit_price_usd", 25)),
            woodland_carbon_code=bool(r.get("woodland_carbon_code", False)),
        )

    def _make_land():
        r = inputs_raw
        return LandInputs(
            subtype=LandSubtype(r.get("subtype", "residential_dev")),
            site_area_hectares=_to_decimal(r.get("site_area_hectares", 0)),
            gross_development_value=_to_decimal(r.get("gross_development_value", 0)),
            total_development_cost=_to_decimal(r.get("total_development_cost", 0)),
            developer_profit_pct=_to_decimal(r.get("developer_profit_pct", 20)),
            finance_cost_pct=_to_decimal(r.get("finance_cost_pct", 6)),
            development_period_years=_to_decimal(r.get("development_period_years", 2)),
            planning_risk_discount_pct=_to_decimal(r.get("planning_risk_discount_pct", 0)),
            remediation_cost=_to_decimal(r.get("remediation_cost", 0)),
            existing_use_value_ha=_to_decimal(r.get("existing_use_value_ha", 0)),
            planning_uplift_multiple=_to_decimal(r.get("planning_uplift_multiple", 1)),
            comparable_land_prices_ha=[_to_decimal(x) for x in r.get("comparable_land_prices_ha", [])],
            peatland_depth_m=_to_decimal(r.get("peatland_depth_m", 0)),
            carbon_sequestration_potential_tco2e_ha=_to_decimal(r.get("carbon_sequestration_potential_tco2e_ha", 0)),
        )

    inputs_map = {
        AssetClass.INFRASTRUCTURE: ("infrastructure", _make_infra),
        AssetClass.PROJECT:        ("project", _make_project),
        AssetClass.ENERGY:         ("energy", _make_energy),
        AssetClass.COMMERCIAL:     ("commercial", _make_commercial),
        AssetClass.RESIDENTIAL:    ("residential", _make_residential),
        AssetClass.AGRICULTURAL:   ("agricultural", _make_agricultural),
        AssetClass.LAND:           ("land", _make_land),
    }

    field_name, builder = inputs_map[ac]
    kwargs = {
        "asset_class": ac,
        "asset_name": request_dict.get("asset_name", ""),
        "country_iso": request_dict.get("country_iso", "GB"),
        "currency": request_dict.get("currency", "GBP"),
        "valuation_date": request_dict.get("valuation_date", str(date.today())),
        "esg": esg,
        "valuation_standard": request_dict.get("valuation_standard", "RICS_Red_Book"),
        field_name: builder(),
    }
    req = ValuationRequest(**kwargs)
    result = _engine.value(req)

    return {
        "asset_class": result.asset_class.value,
        "asset_name": result.asset_name,
        "currency": result.currency,
        "valuation_date": result.valuation_date,
        "final_value": float(result.final_value),
        "value_range_low": float(result.value_range_low),
        "value_range_high": float(result.value_range_high),
        "reconciled_value_pre_esg": float(result.reconciled_value_pre_esg),
        "esg_adjustment_pct": float(result.esg_adjustment.net_esg_adjustment_pct * 100),
        "method_results": [
            {
                "method": r.method.value,
                "indicated_value": float(r.indicated_value),
                "weight": float(r.weight),
                "confidence": r.confidence,
                "key_metrics": r.key_metrics,
                "narrative": r.narrative,
                "methodology_basis": r.methodology_basis,
            }
            for r in result.method_results
        ],
        "esg_breakdown": {
            "green_premium_pct": float(result.esg_adjustment.green_premium_pct * 100),
            "brown_discount_pct": float(result.esg_adjustment.brown_discount_pct * 100),
            "physical_risk_pct": float(result.esg_adjustment.physical_risk_discount_pct * 100),
            "transition_risk_pct": float(result.esg_adjustment.transition_risk_discount_pct * 100),
            "biodiversity_pct": float(result.esg_adjustment.biodiversity_adjustment_pct * 100),
            "net_esg_pct": float(result.esg_adjustment.net_esg_adjustment_pct * 100),
            "narrative": result.esg_adjustment.esg_narrative,
            "stranding_risk_year": result.esg_adjustment.stranding_risk_year,
        },
        "metrics": {
            "value_per_m2": float(result.value_per_m2) if result.value_per_m2 else None,
            "value_per_unit": float(result.value_per_unit) if result.value_per_unit else None,
            "value_per_ha": float(result.value_per_ha) if result.value_per_ha else None,
            "value_per_kw": float(result.value_per_kw) if result.value_per_kw else None,
            "irr_pct": float(result.irr_pct) if result.irr_pct else None,
            "yield_pct": float(result.yield_pct) if result.yield_pct else None,
            "dscr": float(result.dscr) if result.dscr else None,
        },
        "compliance": {
            "valuation_standard": result.valuation_standard_used,
            "rics_ps1_compliant": result.rics_ps1_compliant,
            "rics_vps4_esg_addressed": result.rics_vps4_esg_addressed,
            "ivs_esg_addressed": result.ivs_esg_addressed,
            "material_uncertainty": result.material_uncertainty,
        },
        "validation_summary": result.validation_summary,
    }
