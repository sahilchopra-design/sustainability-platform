"""
Real Estate Portfolio NAV Roll-Up Engine + CRREM Integration

Aggregates property-level valuations to portfolio/fund NAV with:
- Weighted average cap rate, NOI yield, occupancy, EPC distribution
- CRREM stranding risk per property and portfolio-level stranding %
- EPC distribution analysis (A-G by count and by GAV)
- Green vs brown split (2030/2033 MEPS compliance)
- Portfolio carbon intensity (kgCO2e/m2) with CRREM pathway overlay

References:
  - RICS Red Book (Global Standards 2022)
  - CRREM v2 (2023) decarbonisation pathways
  - EU MEPS Directive (recast EPBD 2024)
  - INREV NAV Guidelines
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class PropertyType(str, Enum):
    OFFICE = "office"
    RETAIL = "retail"
    INDUSTRIAL = "industrial"
    MULTIFAMILY = "multifamily"
    HOTEL = "hotel"
    DATA_CENTER = "data_center"
    HEALTHCARE = "healthcare"
    STUDENT_HOUSING = "student_housing"
    LOGISTICS = "logistics"
    MIXED_USE = "mixed_use"


class EPCRating(str, Enum):
    A_PLUS = "A+"
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"


class FundStructure(str, Enum):
    OPEN_END = "open_end"
    CLOSED_END = "closed_end"
    REIT = "reit"
    SEPARATE_ACCOUNT = "separate_account"


class ValuationBasis(str, Enum):
    MARKET_VALUE = "market_value"
    FAIR_VALUE = "fair_value"
    INVESTMENT_VALUE = "investment_value"


# ---------------------------------------------------------------------------
# EPC numeric ordering (for comparisons and MEPS compliance)
# ---------------------------------------------------------------------------

EPC_RANK: Dict[str, int] = {
    "A+": 0, "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7,
}


def epc_meets_minimum(rating: str, minimum: str) -> bool:
    """True if rating is at or above the minimum EPC threshold."""
    return EPC_RANK.get(rating, 99) <= EPC_RANK.get(minimum, 99)


# ---------------------------------------------------------------------------
# MEPS Regulatory Timelines by Country
# ---------------------------------------------------------------------------

MEPS_TIMELINES: Dict[str, List[Dict[str, Any]]] = {
    "NL": [
        {"year": 2023, "minimum_epc": "C", "scope": "office"},
        {"year": 2030, "minimum_epc": "A", "scope": "all_commercial"},
    ],
    "GB": [
        {"year": 2025, "minimum_epc": "E", "scope": "new_leases"},
        {"year": 2028, "minimum_epc": "C", "scope": "all_commercial"},
        {"year": 2030, "minimum_epc": "B", "scope": "all_commercial"},
    ],
    "FR": [
        {"year": 2025, "minimum_epc": "E", "scope": "residential"},
        {"year": 2028, "minimum_epc": "D", "scope": "residential"},
        {"year": 2034, "minimum_epc": "C", "scope": "residential"},
    ],
    "DE": [
        {"year": 2030, "minimum_epc": "D", "scope": "all_commercial"},
        {"year": 2035, "minimum_epc": "C", "scope": "all_commercial"},
    ],
    "EU": [
        {"year": 2030, "minimum_epc": "E", "scope": "non_residential"},
        {"year": 2033, "minimum_epc": "D", "scope": "non_residential"},
        {"year": 2030, "minimum_epc": "E", "scope": "residential"},
        {"year": 2033, "minimum_epc": "D", "scope": "residential"},
    ],
}


# ---------------------------------------------------------------------------
# CRREM Pathway Data (kWh/m2/yr thresholds) — subset for portfolio engine
# Expanded from crrem_stranding_engine.py for additional property types
# ---------------------------------------------------------------------------

CRREM_PATHWAYS: Dict[str, Dict[str, Dict[str, Dict[int, float]]]] = {
    "office": {
        "GB": {"1.5C": {2020: 215, 2025: 190, 2030: 155, 2035: 120, 2040: 90, 2045: 70, 2050: 55},
               "2C":   {2020: 215, 2025: 200, 2030: 175, 2035: 145, 2040: 120, 2045: 95, 2050: 75}},
        "DE": {"1.5C": {2020: 200, 2025: 175, 2030: 140, 2035: 110, 2040: 85, 2045: 65, 2050: 50},
               "2C":   {2020: 200, 2025: 185, 2030: 160, 2035: 135, 2040: 110, 2045: 90, 2050: 70}},
        "NL": {"1.5C": {2020: 195, 2025: 170, 2030: 135, 2035: 105, 2040: 80, 2045: 60, 2050: 45},
               "2C":   {2020: 195, 2025: 180, 2030: 155, 2035: 130, 2040: 105, 2045: 85, 2050: 65}},
        "FR": {"1.5C": {2020: 180, 2025: 160, 2030: 130, 2035: 100, 2040: 75, 2045: 58, 2050: 42},
               "2C":   {2020: 180, 2025: 170, 2030: 148, 2035: 125, 2040: 100, 2045: 80, 2050: 60}},
        "US": {"1.5C": {2020: 250, 2025: 220, 2030: 180, 2035: 140, 2040: 105, 2045: 80, 2050: 60},
               "2C":   {2020: 250, 2025: 235, 2030: 205, 2035: 170, 2040: 140, 2045: 115, 2050: 90}},
    },
    "retail": {
        "GB": {"1.5C": {2020: 300, 2025: 265, 2030: 215, 2035: 170, 2040: 130, 2045: 100, 2050: 75},
               "2C":   {2020: 300, 2025: 280, 2030: 240, 2035: 200, 2040: 165, 2045: 135, 2050: 105}},
        "DE": {"1.5C": {2020: 280, 2025: 245, 2030: 200, 2035: 155, 2040: 120, 2045: 90, 2050: 68},
               "2C":   {2020: 280, 2025: 260, 2030: 225, 2035: 190, 2040: 155, 2045: 125, 2050: 95}},
        "NL": {"1.5C": {2020: 270, 2025: 235, 2030: 190, 2035: 148, 2040: 112, 2045: 85, 2050: 62},
               "2C":   {2020: 270, 2025: 252, 2030: 218, 2035: 182, 2040: 150, 2045: 120, 2050: 90}},
        "FR": {"1.5C": {2020: 260, 2025: 225, 2030: 180, 2035: 140, 2040: 105, 2045: 78, 2050: 58},
               "2C":   {2020: 260, 2025: 242, 2030: 210, 2035: 175, 2040: 142, 2045: 115, 2050: 85}},
        "US": {"1.5C": {2020: 340, 2025: 300, 2030: 245, 2035: 190, 2040: 145, 2045: 110, 2050: 82},
               "2C":   {2020: 340, 2025: 320, 2030: 280, 2035: 235, 2040: 195, 2045: 160, 2050: 125}},
    },
    "industrial": {
        "GB": {"1.5C": {2020: 160, 2025: 140, 2030: 115, 2035: 90, 2040: 70, 2045: 52, 2050: 38},
               "2C":   {2020: 160, 2025: 150, 2030: 130, 2035: 110, 2040: 90, 2045: 72, 2050: 55}},
        "DE": {"1.5C": {2020: 150, 2025: 130, 2030: 105, 2035: 82, 2040: 62, 2045: 48, 2050: 35},
               "2C":   {2020: 150, 2025: 140, 2030: 122, 2035: 102, 2040: 85, 2045: 68, 2050: 52}},
        "NL": {"1.5C": {2020: 145, 2025: 125, 2030: 100, 2035: 78, 2040: 58, 2045: 45, 2050: 32},
               "2C":   {2020: 145, 2025: 135, 2030: 118, 2035: 98, 2040: 82, 2045: 65, 2050: 50}},
        "FR": {"1.5C": {2020: 140, 2025: 120, 2030: 95, 2035: 75, 2040: 55, 2045: 42, 2050: 30},
               "2C":   {2020: 140, 2025: 130, 2030: 115, 2035: 95, 2040: 78, 2045: 62, 2050: 48}},
        "US": {"1.5C": {2020: 185, 2025: 162, 2030: 132, 2035: 102, 2040: 78, 2045: 60, 2050: 45},
               "2C":   {2020: 185, 2025: 175, 2030: 152, 2035: 128, 2040: 105, 2045: 85, 2050: 65}},
    },
    "multifamily": {
        "GB": {"1.5C": {2020: 170, 2025: 150, 2030: 120, 2035: 95, 2040: 72, 2045: 55, 2050: 40},
               "2C":   {2020: 170, 2025: 158, 2030: 138, 2035: 115, 2040: 95, 2045: 78, 2050: 60}},
        "DE": {"1.5C": {2020: 160, 2025: 140, 2030: 112, 2035: 88, 2040: 65, 2045: 50, 2050: 38},
               "2C":   {2020: 160, 2025: 148, 2030: 130, 2035: 108, 2040: 90, 2045: 72, 2050: 55}},
        "NL": {"1.5C": {2020: 155, 2025: 135, 2030: 108, 2035: 85, 2040: 62, 2045: 48, 2050: 35},
               "2C":   {2020: 155, 2025: 145, 2030: 126, 2035: 105, 2040: 88, 2045: 70, 2050: 52}},
        "FR": {"1.5C": {2020: 150, 2025: 132, 2030: 105, 2035: 82, 2040: 60, 2045: 45, 2050: 33},
               "2C":   {2020: 150, 2025: 140, 2030: 122, 2035: 102, 2040: 85, 2045: 68, 2050: 50}},
        "US": {"1.5C": {2020: 195, 2025: 172, 2030: 140, 2035: 108, 2040: 82, 2045: 62, 2050: 48},
               "2C":   {2020: 195, 2025: 182, 2030: 160, 2035: 135, 2040: 112, 2045: 90, 2050: 70}},
    },
    "hotel": {
        "GB": {"1.5C": {2020: 280, 2025: 248, 2030: 200, 2035: 158, 2040: 120, 2045: 92, 2050: 70},
               "2C":   {2020: 280, 2025: 262, 2030: 228, 2035: 190, 2040: 155, 2045: 128, 2050: 100}},
        "DE": {"1.5C": {2020: 265, 2025: 232, 2030: 188, 2035: 148, 2040: 112, 2045: 85, 2050: 65},
               "2C":   {2020: 265, 2025: 248, 2030: 215, 2035: 180, 2040: 148, 2045: 120, 2050: 92}},
        "FR": {"1.5C": {2020: 250, 2025: 218, 2030: 175, 2035: 138, 2040: 105, 2045: 80, 2050: 60},
               "2C":   {2020: 250, 2025: 235, 2030: 205, 2035: 170, 2040: 140, 2045: 115, 2050: 88}},
        "US": {"1.5C": {2020: 320, 2025: 282, 2030: 228, 2035: 178, 2040: 135, 2045: 105, 2050: 78},
               "2C":   {2020: 320, 2025: 300, 2030: 262, 2035: 218, 2040: 180, 2045: 148, 2050: 115}},
        "NL": {"1.5C": {2020: 260, 2025: 228, 2030: 182, 2035: 142, 2040: 108, 2045: 82, 2050: 62},
               "2C":   {2020: 260, 2025: 242, 2030: 210, 2035: 175, 2040: 142, 2045: 115, 2050: 90}},
    },
}


# ---------------------------------------------------------------------------
# Carbon emission factors (kgCO2e per kWh) by country — grid average
# ---------------------------------------------------------------------------

GRID_CARBON_FACTORS: Dict[str, float] = {
    "GB": 0.207,  # UK 2024
    "DE": 0.380,  # Germany 2024
    "NL": 0.328,  # Netherlands 2024
    "FR": 0.052,  # France 2024 (nuclear)
    "US": 0.370,  # US average 2024
    "AU": 0.650,  # Australia 2024
    "JP": 0.450,  # Japan 2024
    "SG": 0.408,  # Singapore 2024
}


# ---------------------------------------------------------------------------
# Data Classes — Property-level inputs
# ---------------------------------------------------------------------------

@dataclass
class PropertyAsset:
    """Single property within a portfolio."""
    property_id: str
    name: str
    property_type: str  # PropertyType value
    country_iso: str
    city: Optional[str] = None
    floor_area_m2: Decimal = Decimal("0")
    year_built: Optional[int] = None
    last_refurbishment_year: Optional[int] = None

    # Valuation
    market_value: Decimal = Decimal("0")
    book_value: Decimal = Decimal("0")
    valuation_date: Optional[date] = None
    valuation_method: str = "income"  # income | cost | sales_comparison | dcf
    cap_rate_pct: Decimal = Decimal("0")
    noi: Decimal = Decimal("0")
    occupancy_pct: Decimal = Decimal("100")
    gross_rental_income: Decimal = Decimal("0")

    # Energy & Carbon
    epc_rating: str = "C"
    energy_intensity_kwh_m2: Decimal = Decimal("0")
    carbon_intensity_kgco2_m2: Decimal = Decimal("0")

    # Green certifications
    certifications: List[str] = field(default_factory=list)  # BREEAM, LEED, etc.

    # Debt
    outstanding_debt: Decimal = Decimal("0")
    loan_to_value_pct: Decimal = Decimal("0")

    # ESG adjustments applied
    esg_adjustment_pct: Decimal = Decimal("0")
    climate_adjustment_pct: Decimal = Decimal("0")


@dataclass
class PortfolioDefinition:
    """Portfolio / fund definition."""
    portfolio_id: str
    name: str
    fund_structure: str = "open_end"
    base_currency: str = "GBP"
    valuation_basis: str = "market_value"
    valuation_date: Optional[date] = None
    properties: List[PropertyAsset] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Data Classes — Outputs
# ---------------------------------------------------------------------------

@dataclass
class EPCDistribution:
    """EPC rating distribution by count and by GAV."""
    rating: str
    property_count: int
    property_pct: Decimal
    gav_total: Decimal
    gav_pct: Decimal
    avg_energy_intensity: Decimal


@dataclass
class MEPSComplianceResult:
    """MEPS compliance status for a single property."""
    property_id: str
    property_name: str
    country_iso: str
    current_epc: str
    compliant_2030: bool
    compliant_2033: bool
    minimum_epc_2030: str
    minimum_epc_2033: str
    gap_bands_to_2030: int  # Number of EPC bands to improve
    gap_bands_to_2033: int


@dataclass
class CRREMPropertyResult:
    """CRREM stranding analysis for a single property."""
    property_id: str
    property_name: str
    property_type: str
    country_iso: str
    floor_area_m2: Decimal
    market_value: Decimal
    energy_intensity_kwh_m2: Decimal
    carbon_intensity_kgco2_m2: Decimal
    pathway_threshold_current_kwh_m2: Optional[Decimal]
    stranding_year_1_5c: Optional[int]
    stranding_year_2c: Optional[int]
    years_to_stranding_1_5c: Optional[int]
    is_already_stranded: bool
    gap_to_pathway_pct: Decimal
    annual_reduction_required_pct: Decimal
    carbon_cost_annual_eur: Decimal


@dataclass
class SectorConcentration:
    """Concentration by property type."""
    property_type: str
    property_count: int
    property_pct: Decimal
    gav_total: Decimal
    gav_pct: Decimal
    avg_cap_rate: Decimal
    avg_occupancy: Decimal
    avg_energy_intensity: Decimal
    avg_carbon_intensity: Decimal


@dataclass
class GeographicConcentration:
    """Concentration by country."""
    country_iso: str
    property_count: int
    property_pct: Decimal
    gav_total: Decimal
    gav_pct: Decimal
    avg_energy_intensity: Decimal
    avg_carbon_intensity: Decimal


@dataclass
class PortfolioNAVResult:
    """Complete portfolio NAV analysis result."""
    # Identity
    portfolio_id: str
    portfolio_name: str
    valuation_date: date
    base_currency: str

    # NAV headline
    gross_asset_value: Decimal
    total_debt: Decimal
    net_asset_value: Decimal
    nav_per_property: Decimal
    property_count: int

    # Yield metrics
    weighted_avg_cap_rate_pct: Decimal
    portfolio_noi_yield_pct: Decimal
    total_noi: Decimal
    total_gross_rental_income: Decimal
    weighted_avg_occupancy_pct: Decimal

    # ESG-adjusted NAV
    esg_adjusted_gav: Decimal
    climate_adjusted_gav: Decimal
    total_esg_impact_pct: Decimal
    total_climate_impact_pct: Decimal

    # Carbon metrics
    portfolio_carbon_intensity_kgco2_m2: Decimal  # WACI by area
    total_emissions_tco2e: Decimal
    total_floor_area_m2: Decimal

    # EPC distribution
    epc_distribution: List[EPCDistribution]
    green_property_count: int  # EPC A+/A/B
    brown_property_count: int  # EPC D/E/F/G
    green_pct_by_gav: Decimal
    brown_pct_by_gav: Decimal

    # MEPS compliance
    meps_compliant_2030_count: int
    meps_compliant_2030_pct: Decimal
    meps_compliant_2033_count: int
    meps_compliant_2033_pct: Decimal
    meps_non_compliant_2030: List[MEPSComplianceResult]

    # CRREM stranding
    crrem_stranded_now_count: int
    crrem_stranded_by_2030_count: int
    crrem_stranded_by_2040_count: int
    crrem_portfolio_stranding_risk_pct: Decimal  # % of GAV in stranded or stranding-by-2030
    crrem_avg_years_to_stranding: Optional[Decimal]
    crrem_total_annual_carbon_cost_eur: Decimal
    crrem_property_results: List[CRREMPropertyResult]

    # Concentration
    sector_concentration: List[SectorConcentration]
    geographic_concentration: List[GeographicConcentration]

    # Validation
    validation_summary: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class REPortfolioEngine:
    """
    Real Estate Portfolio NAV Roll-Up Engine.

    Aggregates property-level valuations to portfolio/fund NAV with
    ESG adjustments, CRREM stranding integration, EPC distribution,
    and MEPS compliance analysis.
    """

    def __init__(self):
        self.current_year = date.today().year

    # -------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------

    def calculate_portfolio_nav(
        self,
        portfolio: PortfolioDefinition,
        crrem_scenario: str = "1.5C",
        carbon_price_eur_per_tco2: Decimal = Decimal("75"),
    ) -> PortfolioNAVResult:
        """
        Full portfolio NAV calculation with all sub-analyses.

        Args:
            portfolio: Portfolio definition with property list.
            crrem_scenario: CRREM scenario ("1.5C" or "2C").
            carbon_price_eur_per_tco2: Carbon price for cost calculations.

        Returns:
            PortfolioNAVResult with complete analysis.
        """
        props = portfolio.properties
        if not props:
            return self._empty_result(portfolio)

        val_date = portfolio.valuation_date or date.today()

        # 1. NAV headline
        nav_metrics = self._calculate_nav_headline(props)

        # 2. Yield metrics
        yield_metrics = self._calculate_yield_metrics(props, nav_metrics["gav"])

        # 3. ESG-adjusted NAV
        esg_metrics = self._calculate_esg_adjusted_nav(props)

        # 4. Carbon metrics
        carbon_metrics = self._calculate_carbon_metrics(props)

        # 5. EPC distribution
        epc_dist = self._calculate_epc_distribution(props)

        # 6. Green/brown split
        green_brown = self._calculate_green_brown_split(props)

        # 7. MEPS compliance
        meps = self._calculate_meps_compliance(props)

        # 8. CRREM stranding
        crrem = self._calculate_crrem_stranding(
            props, crrem_scenario, carbon_price_eur_per_tco2
        )

        # 9. Concentration analysis
        sector_conc = self._calculate_sector_concentration(props, nav_metrics["gav"])
        geo_conc = self._calculate_geographic_concentration(props, nav_metrics["gav"])

        return PortfolioNAVResult(
            portfolio_id=portfolio.portfolio_id,
            portfolio_name=portfolio.name,
            valuation_date=val_date,
            base_currency=portfolio.base_currency,
            # NAV
            gross_asset_value=nav_metrics["gav"],
            total_debt=nav_metrics["total_debt"],
            net_asset_value=nav_metrics["nav"],
            nav_per_property=nav_metrics["nav_per_property"],
            property_count=len(props),
            # Yield
            weighted_avg_cap_rate_pct=yield_metrics["wa_cap_rate"],
            portfolio_noi_yield_pct=yield_metrics["noi_yield"],
            total_noi=yield_metrics["total_noi"],
            total_gross_rental_income=yield_metrics["total_gri"],
            weighted_avg_occupancy_pct=yield_metrics["wa_occupancy"],
            # ESG
            esg_adjusted_gav=esg_metrics["esg_adjusted_gav"],
            climate_adjusted_gav=esg_metrics["climate_adjusted_gav"],
            total_esg_impact_pct=esg_metrics["total_esg_impact_pct"],
            total_climate_impact_pct=esg_metrics["total_climate_impact_pct"],
            # Carbon
            portfolio_carbon_intensity_kgco2_m2=carbon_metrics["intensity"],
            total_emissions_tco2e=carbon_metrics["total_emissions"],
            total_floor_area_m2=carbon_metrics["total_area"],
            # EPC
            epc_distribution=epc_dist,
            green_property_count=green_brown["green_count"],
            brown_property_count=green_brown["brown_count"],
            green_pct_by_gav=green_brown["green_pct_gav"],
            brown_pct_by_gav=green_brown["brown_pct_gav"],
            # MEPS
            meps_compliant_2030_count=meps["compliant_2030_count"],
            meps_compliant_2030_pct=meps["compliant_2030_pct"],
            meps_compliant_2033_count=meps["compliant_2033_count"],
            meps_compliant_2033_pct=meps["compliant_2033_pct"],
            meps_non_compliant_2030=meps["non_compliant_2030"],
            # CRREM
            crrem_stranded_now_count=crrem["stranded_now"],
            crrem_stranded_by_2030_count=crrem["stranded_by_2030"],
            crrem_stranded_by_2040_count=crrem["stranded_by_2040"],
            crrem_portfolio_stranding_risk_pct=crrem["stranding_risk_pct"],
            crrem_avg_years_to_stranding=crrem["avg_years_to_stranding"],
            crrem_total_annual_carbon_cost_eur=crrem["total_carbon_cost"],
            crrem_property_results=crrem["property_results"],
            # Concentration
            sector_concentration=sector_conc,
            geographic_concentration=geo_conc,
            # Validation
            validation_summary=self._build_validation_summary(
                portfolio, crrem_scenario, carbon_price_eur_per_tco2
            ),
        )

    # -------------------------------------------------------------------
    # NAV Headline
    # -------------------------------------------------------------------

    def _calculate_nav_headline(
        self, props: List[PropertyAsset]
    ) -> Dict[str, Decimal]:
        gav = sum((p.market_value for p in props), Decimal("0"))
        total_debt = sum((p.outstanding_debt for p in props), Decimal("0"))
        nav = gav - total_debt
        n = len(props)
        nav_per = (nav / n).quantize(Decimal("0.01"), ROUND_HALF_UP) if n else Decimal("0")
        return {
            "gav": gav,
            "total_debt": total_debt,
            "nav": nav,
            "nav_per_property": nav_per,
        }

    # -------------------------------------------------------------------
    # Yield Metrics
    # -------------------------------------------------------------------

    def _calculate_yield_metrics(
        self, props: List[PropertyAsset], gav: Decimal
    ) -> Dict[str, Decimal]:
        total_noi = sum((p.noi for p in props), Decimal("0"))
        total_gri = sum((p.gross_rental_income for p in props), Decimal("0"))

        # Weighted average cap rate (by market value)
        wa_cap_rate = Decimal("0")
        wa_occupancy = Decimal("0")
        if gav > 0:
            for p in props:
                w = p.market_value / gav
                wa_cap_rate += w * p.cap_rate_pct
                wa_occupancy += w * p.occupancy_pct

        noi_yield = Decimal("0")
        if gav > 0:
            noi_yield = (total_noi / gav * 100).quantize(
                Decimal("0.01"), ROUND_HALF_UP
            )

        return {
            "wa_cap_rate": wa_cap_rate.quantize(Decimal("0.01"), ROUND_HALF_UP),
            "wa_occupancy": wa_occupancy.quantize(Decimal("0.01"), ROUND_HALF_UP),
            "noi_yield": noi_yield,
            "total_noi": total_noi,
            "total_gri": total_gri,
        }

    # -------------------------------------------------------------------
    # ESG-Adjusted NAV
    # -------------------------------------------------------------------

    def _calculate_esg_adjusted_nav(
        self, props: List[PropertyAsset]
    ) -> Dict[str, Decimal]:
        gav = sum((p.market_value for p in props), Decimal("0"))
        esg_adj_gav = Decimal("0")
        climate_adj_gav = Decimal("0")

        for p in props:
            esg_factor = Decimal("1") + p.esg_adjustment_pct / Decimal("100")
            climate_factor = Decimal("1") + p.climate_adjustment_pct / Decimal("100")
            esg_adj_gav += p.market_value * esg_factor
            climate_adj_gav += p.market_value * esg_factor * climate_factor

        esg_impact = Decimal("0")
        climate_impact = Decimal("0")
        if gav > 0:
            esg_impact = ((esg_adj_gav - gav) / gav * 100).quantize(
                Decimal("0.01"), ROUND_HALF_UP
            )
            climate_impact = ((climate_adj_gav - gav) / gav * 100).quantize(
                Decimal("0.01"), ROUND_HALF_UP
            )

        return {
            "esg_adjusted_gav": esg_adj_gav.quantize(Decimal("0.01"), ROUND_HALF_UP),
            "climate_adjusted_gav": climate_adj_gav.quantize(Decimal("0.01"), ROUND_HALF_UP),
            "total_esg_impact_pct": esg_impact,
            "total_climate_impact_pct": climate_impact,
        }

    # -------------------------------------------------------------------
    # Carbon Metrics
    # -------------------------------------------------------------------

    def _calculate_carbon_metrics(
        self, props: List[PropertyAsset]
    ) -> Dict[str, Decimal]:
        total_area = sum((p.floor_area_m2 for p in props), Decimal("0"))
        total_emissions = Decimal("0")

        for p in props:
            if p.carbon_intensity_kgco2_m2 > 0:
                prop_emissions = p.carbon_intensity_kgco2_m2 * p.floor_area_m2
            elif p.energy_intensity_kwh_m2 > 0:
                # Derive from energy intensity using grid factor
                grid_ef = Decimal(str(GRID_CARBON_FACTORS.get(p.country_iso, 0.35)))
                prop_emissions = p.energy_intensity_kwh_m2 * p.floor_area_m2 * grid_ef
            else:
                prop_emissions = Decimal("0")
            total_emissions += prop_emissions

        # Convert kg to tonnes
        total_emissions_t = (total_emissions / 1000).quantize(
            Decimal("0.01"), ROUND_HALF_UP
        )

        intensity = Decimal("0")
        if total_area > 0:
            intensity = (total_emissions / total_area / 1000).quantize(
                Decimal("0.001"), ROUND_HALF_UP
            )  # tCO2e/m2

        # Return kgCO2e/m2 for standard metric
        intensity_kg = Decimal("0")
        if total_area > 0:
            intensity_kg = (
                sum(
                    (
                        p.carbon_intensity_kgco2_m2 * p.floor_area_m2
                        if p.carbon_intensity_kgco2_m2 > 0
                        else p.energy_intensity_kwh_m2
                        * p.floor_area_m2
                        * Decimal(str(GRID_CARBON_FACTORS.get(p.country_iso, 0.35)))
                    )
                    for p in props
                )
                / total_area
            ).quantize(Decimal("0.01"), ROUND_HALF_UP)

        return {
            "intensity": intensity_kg,
            "total_emissions": total_emissions_t,
            "total_area": total_area,
        }

    # -------------------------------------------------------------------
    # EPC Distribution
    # -------------------------------------------------------------------

    def _calculate_epc_distribution(
        self, props: List[PropertyAsset]
    ) -> List[EPCDistribution]:
        ratings = ["A+", "A", "B", "C", "D", "E", "F", "G"]
        n = len(props)
        gav = sum((p.market_value for p in props), Decimal("0"))

        dist: List[EPCDistribution] = []
        for r in ratings:
            matching = [p for p in props if p.epc_rating == r]
            count = len(matching)
            r_gav = sum((p.market_value for p in matching), Decimal("0"))
            avg_ei = Decimal("0")
            if count > 0:
                avg_ei = (
                    sum((p.energy_intensity_kwh_m2 for p in matching), Decimal("0"))
                    / count
                ).quantize(Decimal("0.1"), ROUND_HALF_UP)

            dist.append(
                EPCDistribution(
                    rating=r,
                    property_count=count,
                    property_pct=_pct(count, n),
                    gav_total=r_gav,
                    gav_pct=_pct_decimal(r_gav, gav),
                    avg_energy_intensity=avg_ei,
                )
            )
        return dist

    # -------------------------------------------------------------------
    # Green / Brown Split
    # -------------------------------------------------------------------

    def _calculate_green_brown_split(
        self, props: List[PropertyAsset]
    ) -> Dict[str, Any]:
        green_ratings = {"A+", "A", "B"}
        brown_ratings = {"D", "E", "F", "G"}

        green = [p for p in props if p.epc_rating in green_ratings]
        brown = [p for p in props if p.epc_rating in brown_ratings]

        gav = sum((p.market_value for p in props), Decimal("0"))
        green_gav = sum((p.market_value for p in green), Decimal("0"))
        brown_gav = sum((p.market_value for p in brown), Decimal("0"))

        return {
            "green_count": len(green),
            "brown_count": len(brown),
            "green_pct_gav": _pct_decimal(green_gav, gav),
            "brown_pct_gav": _pct_decimal(brown_gav, gav),
        }

    # -------------------------------------------------------------------
    # MEPS Compliance
    # -------------------------------------------------------------------

    def _calculate_meps_compliance(
        self, props: List[PropertyAsset]
    ) -> Dict[str, Any]:
        results: List[MEPSComplianceResult] = []

        for p in props:
            min_2030 = self._get_meps_minimum(p.country_iso, 2030)
            min_2033 = self._get_meps_minimum(p.country_iso, 2033)

            compliant_2030 = epc_meets_minimum(p.epc_rating, min_2030)
            compliant_2033 = epc_meets_minimum(p.epc_rating, min_2033)

            gap_2030 = max(0, EPC_RANK.get(p.epc_rating, 7) - EPC_RANK.get(min_2030, 7))
            gap_2033 = max(0, EPC_RANK.get(p.epc_rating, 7) - EPC_RANK.get(min_2033, 7))

            results.append(
                MEPSComplianceResult(
                    property_id=p.property_id,
                    property_name=p.name,
                    country_iso=p.country_iso,
                    current_epc=p.epc_rating,
                    compliant_2030=compliant_2030,
                    compliant_2033=compliant_2033,
                    minimum_epc_2030=min_2030,
                    minimum_epc_2033=min_2033,
                    gap_bands_to_2030=gap_2030,
                    gap_bands_to_2033=gap_2033,
                )
            )

        n = len(props)
        c2030 = sum(1 for r in results if r.compliant_2030)
        c2033 = sum(1 for r in results if r.compliant_2033)
        non_compliant_2030 = [r for r in results if not r.compliant_2030]

        return {
            "compliant_2030_count": c2030,
            "compliant_2030_pct": _pct(c2030, n),
            "compliant_2033_count": c2033,
            "compliant_2033_pct": _pct(c2033, n),
            "non_compliant_2030": non_compliant_2030,
        }

    def _get_meps_minimum(self, country_iso: str, target_year: int) -> str:
        """Get the applicable MEPS minimum EPC for a country at a target year."""
        timelines = MEPS_TIMELINES.get(country_iso, MEPS_TIMELINES.get("EU", []))
        applicable_min = "G"  # Default: no minimum

        for entry in timelines:
            if entry["year"] <= target_year:
                candidate = entry["minimum_epc"]
                if EPC_RANK.get(candidate, 99) < EPC_RANK.get(applicable_min, 99):
                    applicable_min = candidate

        return applicable_min

    # -------------------------------------------------------------------
    # CRREM Stranding Analysis
    # -------------------------------------------------------------------

    def _calculate_crrem_stranding(
        self,
        props: List[PropertyAsset],
        scenario: str,
        carbon_price: Decimal,
    ) -> Dict[str, Any]:
        results: List[CRREMPropertyResult] = []
        gav = sum((p.market_value for p in props), Decimal("0"))

        for p in props:
            result = self._assess_single_property_crrem(p, scenario, carbon_price)
            results.append(result)

        stranded_now = sum(1 for r in results if r.is_already_stranded)
        stranded_by_2030 = sum(
            1
            for r in results
            if r.stranding_year_1_5c is not None and r.stranding_year_1_5c <= 2030
        )
        stranded_by_2040 = sum(
            1
            for r in results
            if r.stranding_year_1_5c is not None and r.stranding_year_1_5c <= 2040
        )

        # Stranding risk = % of GAV in properties stranded now or by 2030
        at_risk_gav = sum(
            (
                r.market_value
                for r in results
                if r.is_already_stranded
                or (r.stranding_year_1_5c is not None and r.stranding_year_1_5c <= 2030)
            ),
            Decimal("0"),
        )
        stranding_risk_pct = _pct_decimal(at_risk_gav, gav)

        # Average years to stranding (for those with a stranding year)
        years_list = [
            r.years_to_stranding_1_5c
            for r in results
            if r.years_to_stranding_1_5c is not None and r.years_to_stranding_1_5c > 0
        ]
        avg_years = None
        if years_list:
            avg_years = Decimal(str(sum(years_list) / len(years_list))).quantize(
                Decimal("0.1"), ROUND_HALF_UP
            )

        total_carbon_cost = sum(
            (r.carbon_cost_annual_eur for r in results), Decimal("0")
        )

        return {
            "stranded_now": stranded_now,
            "stranded_by_2030": stranded_by_2030,
            "stranded_by_2040": stranded_by_2040,
            "stranding_risk_pct": stranding_risk_pct,
            "avg_years_to_stranding": avg_years,
            "total_carbon_cost": total_carbon_cost,
            "property_results": results,
        }

    def _assess_single_property_crrem(
        self,
        prop: PropertyAsset,
        scenario: str,
        carbon_price: Decimal,
    ) -> CRREMPropertyResult:
        """Run CRREM stranding assessment on a single property."""
        ptype = prop.property_type
        country = prop.country_iso
        ei = float(prop.energy_intensity_kwh_m2)

        # Get pathway data
        pathway = self._get_crrem_pathway(ptype, country, scenario)
        current_threshold = self._interpolate_pathway(pathway, self.current_year)

        # Determine stranding year
        stranding_year: Optional[int] = None
        is_stranded = False
        years_to_stranding: Optional[int] = None

        if current_threshold is not None and ei > 0:
            if ei > current_threshold:
                is_stranded = True
                stranding_year = self.current_year
                years_to_stranding = 0
            else:
                # Find the year when pathway drops below asset intensity
                for yr in range(self.current_year + 1, 2051):
                    threshold = self._interpolate_pathway(pathway, yr)
                    if threshold is not None and ei > threshold:
                        stranding_year = yr
                        years_to_stranding = yr - self.current_year
                        break

        # Stranding year under 2C (always less aggressive)
        pathway_2c = self._get_crrem_pathway(ptype, country, "2C")
        stranding_year_2c: Optional[int] = None
        if ei > 0:
            for yr in range(self.current_year, 2051):
                threshold_2c = self._interpolate_pathway(pathway_2c, yr)
                if threshold_2c is not None and ei > threshold_2c:
                    stranding_year_2c = yr
                    break

        # Gap to pathway
        gap_pct = Decimal("0")
        pathway_threshold_dec = None
        if current_threshold is not None and current_threshold > 0:
            pathway_threshold_dec = Decimal(str(current_threshold))
            gap = ei - current_threshold
            gap_pct = Decimal(str(gap / current_threshold * 100)).quantize(
                Decimal("0.1"), ROUND_HALF_UP
            )

        # Annual reduction required to reach 2050 target
        target_2050 = self._interpolate_pathway(pathway, 2050) or 0
        annual_reduction = Decimal("0")
        if ei > 0 and target_2050 > 0 and target_2050 < ei:
            years_rem = 2050 - self.current_year
            if years_rem > 0:
                ratio = target_2050 / ei
                annual_pct = (1 - ratio ** (1 / years_rem)) * 100
                annual_reduction = Decimal(str(annual_pct)).quantize(
                    Decimal("0.01"), ROUND_HALF_UP
                )

        # Carbon cost
        carbon_intensity = float(prop.carbon_intensity_kgco2_m2)
        if carbon_intensity <= 0 and ei > 0:
            grid_ef = GRID_CARBON_FACTORS.get(country, 0.35)
            carbon_intensity = ei * grid_ef

        carbon_cost = Decimal("0")
        if carbon_intensity > 0 and prop.floor_area_m2 > 0:
            annual_tonnes = Decimal(str(carbon_intensity)) * prop.floor_area_m2 / 1000
            carbon_cost = (annual_tonnes * carbon_price).quantize(
                Decimal("0.01"), ROUND_HALF_UP
            )

        return CRREMPropertyResult(
            property_id=prop.property_id,
            property_name=prop.name,
            property_type=ptype,
            country_iso=country,
            floor_area_m2=prop.floor_area_m2,
            market_value=prop.market_value,
            energy_intensity_kwh_m2=prop.energy_intensity_kwh_m2,
            carbon_intensity_kgco2_m2=Decimal(str(carbon_intensity)).quantize(
                Decimal("0.01"), ROUND_HALF_UP
            ),
            pathway_threshold_current_kwh_m2=pathway_threshold_dec,
            stranding_year_1_5c=stranding_year,
            stranding_year_2c=stranding_year_2c,
            years_to_stranding_1_5c=years_to_stranding,
            is_already_stranded=is_stranded,
            gap_to_pathway_pct=gap_pct,
            annual_reduction_required_pct=annual_reduction,
            carbon_cost_annual_eur=carbon_cost,
        )

    def _get_crrem_pathway(
        self, property_type: str, country_iso: str, scenario: str
    ) -> Dict[int, float]:
        """Get CRREM pathway for property type + country + scenario."""
        pt = CRREM_PATHWAYS.get(property_type, {})
        country_data = pt.get(country_iso, pt.get("GB", {}))
        return country_data.get(scenario, {})

    def _interpolate_pathway(
        self, pathway: Dict[int, float], year: int
    ) -> Optional[float]:
        """Linear interpolation of CRREM pathway for a given year."""
        if not pathway:
            return None

        years = sorted(pathway.keys())
        if year <= years[0]:
            return pathway[years[0]]
        if year >= years[-1]:
            return pathway[years[-1]]

        for i in range(len(years) - 1):
            y1, y2 = years[i], years[i + 1]
            if y1 <= year <= y2:
                v1, v2 = pathway[y1], pathway[y2]
                t = (year - y1) / (y2 - y1)
                return v1 + t * (v2 - v1)
        return None

    # -------------------------------------------------------------------
    # Concentration Analysis
    # -------------------------------------------------------------------

    def _calculate_sector_concentration(
        self, props: List[PropertyAsset], gav: Decimal
    ) -> List[SectorConcentration]:
        types: Dict[str, List[PropertyAsset]] = {}
        for p in props:
            types.setdefault(p.property_type, []).append(p)

        result: List[SectorConcentration] = []
        n = len(props)
        for ptype, group in sorted(types.items()):
            count = len(group)
            g_gav = sum((p.market_value for p in group), Decimal("0"))
            avg_cap = _safe_avg([p.cap_rate_pct for p in group])
            avg_occ = _safe_avg([p.occupancy_pct for p in group])
            avg_ei = _safe_avg([p.energy_intensity_kwh_m2 for p in group])
            avg_ci = _safe_avg([p.carbon_intensity_kgco2_m2 for p in group])

            result.append(
                SectorConcentration(
                    property_type=ptype,
                    property_count=count,
                    property_pct=_pct(count, n),
                    gav_total=g_gav,
                    gav_pct=_pct_decimal(g_gav, gav),
                    avg_cap_rate=avg_cap,
                    avg_occupancy=avg_occ,
                    avg_energy_intensity=avg_ei,
                    avg_carbon_intensity=avg_ci,
                )
            )
        return result

    def _calculate_geographic_concentration(
        self, props: List[PropertyAsset], gav: Decimal
    ) -> List[GeographicConcentration]:
        countries: Dict[str, List[PropertyAsset]] = {}
        for p in props:
            countries.setdefault(p.country_iso, []).append(p)

        result: List[GeographicConcentration] = []
        n = len(props)
        for country, group in sorted(countries.items()):
            count = len(group)
            c_gav = sum((p.market_value for p in group), Decimal("0"))
            avg_ei = _safe_avg([p.energy_intensity_kwh_m2 for p in group])
            avg_ci = _safe_avg([p.carbon_intensity_kgco2_m2 for p in group])

            result.append(
                GeographicConcentration(
                    country_iso=country,
                    property_count=count,
                    property_pct=_pct(count, n),
                    gav_total=c_gav,
                    gav_pct=_pct_decimal(c_gav, gav),
                    avg_energy_intensity=avg_ei,
                    avg_carbon_intensity=avg_ci,
                )
            )
        return result

    # -------------------------------------------------------------------
    # Validation Summary
    # -------------------------------------------------------------------

    def _build_validation_summary(
        self,
        portfolio: PortfolioDefinition,
        crrem_scenario: str,
        carbon_price: Decimal,
    ) -> Dict[str, Any]:
        return {
            "methodology": "INREV NAV Guidelines + CRREM v2 (2023) + EU MEPS (recast EPBD 2024)",
            "portfolio_id": portfolio.portfolio_id,
            "property_count": len(portfolio.properties),
            "valuation_basis": portfolio.valuation_basis,
            "base_currency": portfolio.base_currency,
            "crrem_scenario": crrem_scenario,
            "carbon_price_eur_per_tco2": str(carbon_price),
            "crrem_pathways_coverage": "office, retail, industrial, multifamily, hotel",
            "country_coverage": "GB, DE, NL, FR, US",
            "meps_timelines": list(MEPS_TIMELINES.keys()),
            "data_quality_notes": [
                "CRREM thresholds based on CRREM v2 2023 dataset (5-year interpolation)",
                "Grid carbon factors are country-average 2024; not sub-national",
                "MEPS timelines reflect regulations as of 2024; subject to change",
                "Carbon price used is flat; real cost may follow ETS trajectory",
            ],
            "calculation_date": str(date.today()),
        }

    # -------------------------------------------------------------------
    # Empty result helper
    # -------------------------------------------------------------------

    def _empty_result(self, portfolio: PortfolioDefinition) -> PortfolioNAVResult:
        z = Decimal("0")
        return PortfolioNAVResult(
            portfolio_id=portfolio.portfolio_id,
            portfolio_name=portfolio.name,
            valuation_date=portfolio.valuation_date or date.today(),
            base_currency=portfolio.base_currency,
            gross_asset_value=z, total_debt=z, net_asset_value=z,
            nav_per_property=z, property_count=0,
            weighted_avg_cap_rate_pct=z, portfolio_noi_yield_pct=z,
            total_noi=z, total_gross_rental_income=z,
            weighted_avg_occupancy_pct=z,
            esg_adjusted_gav=z, climate_adjusted_gav=z,
            total_esg_impact_pct=z, total_climate_impact_pct=z,
            portfolio_carbon_intensity_kgco2_m2=z,
            total_emissions_tco2e=z, total_floor_area_m2=z,
            epc_distribution=[], green_property_count=0, brown_property_count=0,
            green_pct_by_gav=z, brown_pct_by_gav=z,
            meps_compliant_2030_count=0, meps_compliant_2030_pct=z,
            meps_compliant_2033_count=0, meps_compliant_2033_pct=z,
            meps_non_compliant_2030=[],
            crrem_stranded_now_count=0, crrem_stranded_by_2030_count=0,
            crrem_stranded_by_2040_count=0, crrem_portfolio_stranding_risk_pct=z,
            crrem_avg_years_to_stranding=None, crrem_total_annual_carbon_cost_eur=z,
            crrem_property_results=[],
            sector_concentration=[], geographic_concentration=[],
            validation_summary={},
        )


# ---------------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------------

def _pct(numerator: int, denominator: int) -> Decimal:
    if denominator == 0:
        return Decimal("0")
    return Decimal(str(numerator / denominator * 100)).quantize(
        Decimal("0.1"), ROUND_HALF_UP
    )


def _pct_decimal(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == 0:
        return Decimal("0")
    return (numerator / denominator * 100).quantize(Decimal("0.1"), ROUND_HALF_UP)


def _safe_avg(values: List[Decimal]) -> Decimal:
    non_zero = [v for v in values if v > 0]
    if not non_zero:
        return Decimal("0")
    return (sum(non_zero, Decimal("0")) / len(non_zero)).quantize(
        Decimal("0.01"), ROUND_HALF_UP
    )
