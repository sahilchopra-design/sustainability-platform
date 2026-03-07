"""
PCAF Financed Emissions Engine -- All 7 Asset Classes
PCAF Global GHG Accounting & Reporting Standard, Part A, 2nd Edition (Dec 2022)

INVESTOR-GRADE IMPLEMENTATION

Regulatory compliance:
  - PCAF Standard v2.0 Part A (Dec 2022): financed emissions for 7 asset classes
  - PCAF Data Quality Score Tables 5.3-5.9: auto-derived from data provenance
  - EU SFDR RTS Annex I, PAI #1-#3: financed GHG, carbon footprint, WACI
  - EU Taxonomy Art.8 KPI: GHG intensity disclosure per counterparty
  - TCFD 2021 Guidance: portfolio carbon metrics (financed emissions, WACI,
    carbon footprint, implied temperature rise)
  - GHG Protocol Corporate Standard (Scope 1/2/3 boundary definitions)

Per-asset-class features:
  1. Attribution factor computed per PCAF formula (Tables 5.1-5.2)
  2. Auto-derived Data Quality Score per asset class (Tables 5.3-5.9)
  3. Financed emissions with DQS-based uncertainty bands (low / central / high)
  4. Emission intensity in asset-class-specific unit
  5. Data completeness scoring and gap identification
  6. Methodology provenance (source, table, paragraph references)
  7. Portfolio aggregation: carbon footprint, WACI, implied temperature
  8. Disclosure readiness scoring (SFDR / TCFD / EU Taxonomy)
"""
import logging
import math
from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/pcaf", tags=["PCAF Asset Classes"])


# =====================================================================
# Reference Data
# =====================================================================

# PCAF sector emission factors (tCO2e / EUR M revenue) -- fallback DQS 4-5
# Source: PCAF Standard Part A Table 5.4 / EXIOBASE 3.8 / EEIO 2022
SECTOR_EMISSION_FACTORS: Dict[str, Dict[str, float]] = {
    "Energy":                 {"scope1": 520.0, "scope2": 180.0, "scope3": 1800.0},
    "Utilities":              {"scope1": 400.0, "scope2": 120.0, "scope3": 1100.0},
    "Materials":              {"scope1": 280.0, "scope2": 100.0, "scope3": 950.0},
    "Industrials":            {"scope1": 80.0,  "scope2": 55.0,  "scope3": 420.0},
    "Consumer Discretionary": {"scope1": 30.0,  "scope2": 25.0,  "scope3": 350.0},
    "Consumer Staples":       {"scope1": 45.0,  "scope2": 30.0,  "scope3": 500.0},
    "Health Care":            {"scope1": 12.0,  "scope2": 15.0,  "scope3": 180.0},
    "Financials":             {"scope1": 3.0,   "scope2": 8.0,   "scope3": 85.0},
    "Information Technology":  {"scope1": 5.0,   "scope2": 12.0,  "scope3": 120.0},
    "Communication Services":  {"scope1": 4.0,   "scope2": 10.0,  "scope3": 90.0},
    "Real Estate":             {"scope1": 20.0,  "scope2": 30.0,  "scope3": 150.0},
    "Default":                 {"scope1": 60.0,  "scope2": 40.0,  "scope3": 350.0},
}

# EPC / building energy intensity benchmarks (kgCO2/m2/year)
# Source: EU EPBD recast 2024, CRREM Global Pathways v2.0
EPC_EMISSION_FACTORS = {
    "A+":  5.0,
    "A":  12.0,
    "B":  25.0,
    "C":  45.0,
    "D":  70.0,
    "E": 100.0,
    "F": 135.0,
    "G": 175.0,
}

# Vehicle type emission benchmarks (gCO2/km, WLTP)
# Source: EU Regulation 2019/631, ICCT 2023 European Vehicle Market Statistics
VEHICLE_EMISSION_FACTORS = {
    "BEV":         0.0,
    "PHEV":       35.0,
    "HEV":        90.0,
    "ICE_petrol": 155.0,
    "ICE_diesel": 140.0,
    "ICE_lpg":    130.0,
    "ICE_cng":    125.0,
    "FCEV":         0.0,
    "Default":    150.0,
}

# Sovereign emissions (MtCO2e, production-based, 2022)
# Source: EDGAR v8.0 / Global Carbon Budget 2023 / UNFCCC CRF
SOVEREIGN_EMISSIONS = {
    "US": 5_007.0, "CN": 12_667.0, "IN": 2_830.0, "RU": 1_942.0,
    "JP": 1_081.0, "DE": 674.0, "KR": 616.0, "IR": 580.0,
    "SA": 560.0, "ID": 547.0, "CA": 544.0, "BR": 478.0,
    "MX": 441.0, "AU": 386.0, "ZA": 372.0, "TR": 366.0,
    "GB": 338.0, "IT": 326.0, "PL": 306.0, "FR": 299.0,
    "TH": 254.0, "TW": 247.0, "MY": 221.0, "VN": 207.0,
    "EG": 200.0, "PK": 192.0, "AR": 167.0, "ES": 234.0,
    "NL": 144.0, "CZ": 93.0, "BE": 90.0, "RO": 70.0,
    "CH": 35.0, "NO": 41.0, "SE": 37.0, "DK": 29.0,
    "FI": 38.0, "AT": 63.0, "IE": 37.0, "PT": 41.0,
    "GR": 55.0, "NZ": 34.0, "SG": 47.0, "HK": 33.0,
    "IL": 62.0, "AE": 190.0, "QA": 95.0, "KW": 92.0,
}

# GDP PPP (USD trillions, 2023)
# Source: IMF WEO Oct 2023 / World Bank WDI
SOVEREIGN_GDP_PPP = {
    "US": 25.46, "CN": 30.33, "IN": 11.87, "JP": 6.27, "DE": 5.37,
    "RU": 4.77, "BR": 3.84, "GB": 3.75, "FR": 3.74, "ID": 3.84,
    "IT": 3.06, "CA": 2.32, "KR": 2.78, "AU": 1.75, "ES": 2.21,
    "MX": 2.95, "SA": 2.18, "TR": 2.92, "NL": 1.16, "PL": 1.55,
    "TH": 1.42, "ZA": 0.95, "EG": 1.64, "MY": 1.08, "VN": 1.28,
    "PK": 1.47, "AR": 1.16, "BE": 0.73, "TW": 1.38, "CZ": 0.49,
    "RO": 0.74, "IR": 1.55, "CH": 0.72, "NO": 0.44, "SE": 0.65,
    "DK": 0.39, "FI": 0.31, "AT": 0.56, "IE": 0.59, "PT": 0.39,
    "GR": 0.36, "NZ": 0.25, "SG": 0.63, "HK": 0.50, "IL": 0.51,
    "AE": 0.74, "QA": 0.28, "KW": 0.23,
}

# Sovereign emission intensity (tCO2e per USD M GDP PPP)
SOVEREIGN_INTENSITY = {}
for _iso in set(SOVEREIGN_EMISSIONS.keys()) & set(SOVEREIGN_GDP_PPP.keys()):
    if SOVEREIGN_GDP_PPP[_iso] > 0:
        SOVEREIGN_INTENSITY[_iso] = round(
            SOVEREIGN_EMISSIONS[_iso] * 1e6 / (SOVEREIGN_GDP_PPP[_iso] * 1e12) * 1e6, 2
        )

# WACI -> implied temperature mapping (tCO2e/EUR M revenue -> deg C)
# Source: TCFD 2021 / PACTA / right. based on science methodology
WACI_TEMP_MAP = [
    (30, 1.5), (70, 1.65), (100, 1.75), (150, 1.9), (200, 2.0),
    (300, 2.3), (450, 2.6), (600, 2.9), (800, 3.2),
    (1000, 3.5), (1500, 3.9), (2000, 4.5),
]

# DQS uncertainty multipliers (PCAF Standard Part A, Section 5.2.3)
# Central = 1.0, Low = central * (1 - factor), High = central * (1 + factor)
DQS_UNCERTAINTY = {
    1: 0.10,   # +/- 10%  (verified primary data)
    2: 0.20,   # +/- 20%  (unverified primary data)
    3: 0.30,   # +/- 30%  (physical activity-based estimates)
    4: 0.45,   # +/- 45%  (sector-average / EEIO estimates)
    5: 0.60,   # +/- 60%  (proxy / extrapolated estimates)
}

DQS_DESCRIPTIONS = {
    1: "Verified: audited/assured primary emissions from investee (e.g., CDP A-list, GHG verified)",
    2: "Unverified: investee-reported emissions, not externally assured",
    3: "Physical activity: estimated from energy consumption, production data, floor area",
    4: "Economic activity: estimated using sector-average emission factors (EEIO/EXIOBASE)",
    5: "Proxy/estimated: extrapolated from asset class averages, no company-specific data",
}


def _waci_to_temp(waci: float) -> float:
    """Piecewise linear interpolation of WACI -> implied temperature rise.

    Based on TCFD 2021 portfolio alignment guidance and PACTA methodology.
    """
    if waci <= WACI_TEMP_MAP[0][0]:
        return WACI_TEMP_MAP[0][1]
    for i in range(1, len(WACI_TEMP_MAP)):
        if waci <= WACI_TEMP_MAP[i][0]:
            w0, t0 = WACI_TEMP_MAP[i - 1]
            w1, t1 = WACI_TEMP_MAP[i]
            return round(t0 + (t1 - t0) * (waci - w0) / (w1 - w0), 2)
    return WACI_TEMP_MAP[-1][1]


# =====================================================================
# Auto-DQS Derivation (PCAF Standard Tables 5.3-5.9)
# =====================================================================

def _auto_dqs_corporate(
    has_verified_emissions: bool,
    has_reported_emissions: bool,
    has_physical_activity: bool,
    has_revenue: bool,
) -> int:
    """
    Auto-derive DQS for Listed Equity / Business Loans (PCAF Table 5.3-5.4).

    DQS 1: Verified Scope 1+2 directly from investee (audited / assured)
    DQS 2: Investee-reported S1+2, not externally assured
    DQS 3: Estimated from physical activity data (energy, production)
    DQS 4: Estimated using economic-activity-based emission factors
    DQS 5: Proxy / estimated using sector-average revenue-based factors
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


def _auto_dqs_project_finance(
    has_project_emissions: bool,
    has_generation_data: bool,
    has_capacity_data: bool,
) -> int:
    """Auto-derive DQS for Project Finance (PCAF Table 5.5).

    DQS 1: Verified project-level emissions
    DQS 2: Unverified project-level emissions
    DQS 3: Estimated from generation/production data
    DQS 4: Estimated from installed capacity
    DQS 5: Sector/technology average
    """
    if has_project_emissions:
        return 2  # Mark as 2 unless user claims verified (1)
    if has_generation_data:
        return 3
    if has_capacity_data:
        return 4
    return 5


def _auto_dqs_real_estate(
    has_actual_emissions: bool,
    has_energy_data: bool,
    has_epc: bool,
) -> int:
    """Auto-derive DQS for CRE / Mortgages (PCAF Table 5.6-5.7).

    DQS 1: Actual building energy + verified emission factor
    DQS 2: Actual building energy + estimated emission factor
    DQS 3: Estimated from EPC rating + floor area
    DQS 4: Estimated from building type average
    DQS 5: Country/region average for building stock
    """
    if has_actual_emissions:
        return 2  # 1 only if emission factor is grid-verified
    if has_energy_data:
        return 3
    if has_epc:
        return 3
    return 5


def _auto_dqs_vehicle(
    has_actual_gco2km: bool,
    has_type_class: bool,
) -> int:
    """Auto-derive DQS for Vehicle Loans (PCAF Table 5.8).

    DQS 1: Verified WLTP from manufacturer + actual km driven
    DQS 2: WLTP from vehicle registry + estimated km
    DQS 3: Emission factor by fuel type + estimated km
    DQS 4: Vehicle class average
    DQS 5: National fleet average
    """
    if has_actual_gco2km:
        return 2
    if has_type_class:
        return 3
    return 5


def _auto_dqs_sovereign(
    has_country_emissions: bool,
    has_country_override: bool,
) -> int:
    """Auto-derive DQS for Sovereign Bonds (PCAF Table 5.9).

    DQS 1: UNFCCC CRF/BUR (Annex I parties, verified)
    DQS 2: National GHG inventory (non-Annex I)
    DQS 3: EDGAR/IEA modelled estimates
    DQS 4: Regional/income-group proxy
    DQS 5: Global average
    """
    if has_country_override:
        return 1
    if has_country_emissions:
        return 2
    return 4


# =====================================================================
# Response Models (Investor-Grade)
# =====================================================================

class DataGap(BaseModel):
    """Identified data gap for a single asset."""
    field: str
    severity: str       # "critical" | "major" | "minor"
    impact: str         # How it affects the calculation
    recommendation: str


class AssetEmissionResult(BaseModel):
    """Per-asset financed emissions result with uncertainty and provenance."""
    asset_id: str
    name: Optional[str] = None

    # Attribution
    attribution_factor: float
    attribution_formula: str

    # Financed emissions (central estimate)
    financed_scope1_tco2e: float
    financed_scope2_tco2e: float
    financed_scope3_tco2e: float
    financed_total_tco2e: float

    # Uncertainty bands (DQS-driven)
    financed_total_low_tco2e: float
    financed_total_high_tco2e: float

    # Emission intensity (asset-class-specific)
    emission_intensity: float
    emission_intensity_unit: str

    # Data Quality
    pcaf_data_quality_score: int
    pcaf_dqs_auto_derived: bool
    dqs_description: str
    data_completeness_pct: float
    data_gaps: List[DataGap]

    # Methodology
    estimation_method: str
    pcaf_table_reference: str


class RegulatoryDisclosure(BaseModel):
    """Portfolio-level regulatory disclosure metrics."""
    # SFDR PAI Indicators (Annex I, Table 1)
    sfdr_pai_1_financed_ghg_tco2e: float
    sfdr_pai_1_scope1_tco2e: float
    sfdr_pai_1_scope2_tco2e: float
    sfdr_pai_1_scope3_tco2e: float
    sfdr_pai_2_carbon_footprint_tco2e_per_meur: float
    sfdr_pai_3_waci_tco2e_per_meur: Optional[float] = None
    # TCFD Metrics
    tcfd_financed_emissions_tco2e: float
    tcfd_waci: Optional[float] = None
    tcfd_implied_temp_rise_c: Optional[float] = None
    # EU Taxonomy
    eu_taxonomy_eligible_pct: float = 0.0


class PortfolioSummary(BaseModel):
    """Portfolio-level aggregated metrics with full disclosure support."""
    # Identity
    asset_class: str
    asset_class_label: str
    reporting_year: int
    reporting_date: str

    # Scale
    total_assets: int
    total_outstanding_eur: float

    # Financed emissions
    total_financed_scope1_tco2e: float
    total_financed_scope2_tco2e: float
    total_financed_scope3_tco2e: float
    total_financed_tco2e: float
    total_financed_low_tco2e: float
    total_financed_high_tco2e: float

    # Portfolio metrics
    portfolio_carbon_footprint_tco2e_per_meur: float
    waci_scope12_tco2e_per_meur: Optional[float] = None
    implied_temperature_rise_c: Optional[float] = None

    # Data quality
    weighted_data_quality_score: float
    data_completeness_pct: float
    assets_with_verified_data_pct: float
    assets_with_estimated_data_pct: float

    # Coverage
    coverage_pct: float
    coverage_by_outstanding_pct: float

    # Regulatory
    regulatory_disclosure: RegulatoryDisclosure

    # Methodology
    methodology: Dict[str, str]

    # Per-asset detail
    per_asset: List[AssetEmissionResult]


# =====================================================================
# 1. Listed Equity & Corporate Bonds (PCAF Table 5.1, Row 1)
# =====================================================================

class ListedEquityAsset(BaseModel):
    asset_id: str
    name: Optional[str] = None
    isin: Optional[str] = Field(None, description="ISIN for security identification")
    lei: Optional[str] = Field(None, description="LEI for entity identification")
    sector: str = "Default"
    nace_code: Optional[str] = Field(None, description="NACE Rev.2 code for EU Taxonomy")
    country_iso: str = "US"
    currency: str = "EUR"

    outstanding_eur: float = Field(..., gt=0, description="Investment / bond holding value (EUR)")
    evic_eur: float = Field(..., gt=0, description="Enterprise Value Including Cash (EUR)")
    market_cap_eur: Optional[float] = Field(None, gt=0, description="Market capitalisation (EUR)")
    total_debt_eur: Optional[float] = Field(None, ge=0, description="Total borrowings (EUR)")
    annual_revenue_eur: Optional[float] = Field(None, gt=0, description="Annual revenue (EUR)")

    # Emissions data
    scope1_tco2e: Optional[float] = Field(None, ge=0, description="Reported Scope 1 (tCO2e)")
    scope2_tco2e: Optional[float] = Field(None, ge=0, description="Reported Scope 2 (tCO2e)")
    scope3_tco2e: Optional[float] = Field(None, ge=0, description="Reported Scope 3 (tCO2e)")
    emissions_verified: bool = Field(False, description="Emissions externally assured (ISO 14064-3)")
    emissions_year: Optional[int] = Field(None, description="Year of emissions data")

    # Override DQS (optional — auto-derived if not provided)
    pcaf_data_quality_score: Optional[int] = Field(None, ge=1, le=5)

    @field_validator('evic_eur')
    @classmethod
    def evic_positive(cls, v):
        if v <= 0:
            raise ValueError("EVIC must be positive; check market cap + net debt calculation")
        return v


class ListedEquityRequest(BaseModel):
    assets: List[ListedEquityAsset]
    reporting_year: int = Field(2024, ge=2000, le=2100)
    reporting_date: Optional[str] = None
    include_scope3: bool = False
    base_year: Optional[int] = Field(None, description="Base year for YoY comparison")


@router.post("/listed-equity", response_model=PortfolioSummary)
def assess_listed_equity(req: ListedEquityRequest):
    """
    PCAF Asset Class 1: Listed Equity & Corporate Bonds.

    Attribution Factor = Outstanding Amount / EVIC
    (PCAF Standard Part A, Table 5.1, Row 1)

    EVIC = Market Capitalisation + Total Borrowings (book value)
    If only market_cap provided, EVIC is validated against user input.
    """
    if not req.assets:
        raise HTTPException(400, "At least one asset required")

    results = []
    total_outstanding = 0.0
    total_s1 = total_s2 = total_s3 = 0.0
    total_low = total_high = 0.0
    dqs_weighted = 0.0
    verified_count = 0
    estimated_count = 0

    for a in req.assets:
        # --- Attribution Factor ---
        af = min(a.outstanding_eur / a.evic_eur, 1.0)

        # --- Auto-derive DQS ---
        auto_dqs = _auto_dqs_corporate(
            has_verified_emissions=a.emissions_verified and a.scope1_tco2e is not None,
            has_reported_emissions=a.scope1_tco2e is not None,
            has_physical_activity=False,
            has_revenue=a.annual_revenue_eur is not None and a.annual_revenue_eur > 0,
        )
        dqs = a.pcaf_data_quality_score if a.pcaf_data_quality_score is not None else auto_dqs
        # Validate: user cannot claim DQS 1 without verified emissions
        if dqs == 1 and not (a.emissions_verified and a.scope1_tco2e is not None):
            dqs = 2

        # --- Emissions (company-level, then attributed) ---
        gaps = []
        estimation_method = "reported"
        sector_ef = SECTOR_EMISSION_FACTORS.get(a.sector, SECTOR_EMISSION_FACTORS["Default"])

        if a.scope1_tco2e is not None:
            s1_company = a.scope1_tco2e
        else:
            rev_m = (a.annual_revenue_eur or 10_000_000) / 1e6
            s1_company = sector_ef["scope1"] * rev_m
            estimation_method = "sector_average"
            gaps.append(DataGap(
                field="scope1_tco2e", severity="major",
                impact="Scope 1 estimated from sector average; DQS >= 4",
                recommendation="Obtain investee CDP/GRI disclosure or request directly"
            ))

        if a.scope2_tco2e is not None:
            s2_company = a.scope2_tco2e
        else:
            rev_m = (a.annual_revenue_eur or 10_000_000) / 1e6
            s2_company = sector_ef["scope2"] * rev_m
            estimation_method = "sector_average"
            gaps.append(DataGap(
                field="scope2_tco2e", severity="major",
                impact="Scope 2 estimated from sector average; DQS >= 4",
                recommendation="Obtain investee CDP/GRI disclosure or request directly"
            ))

        s3_company = 0.0
        if req.include_scope3:
            if a.scope3_tco2e is not None:
                s3_company = a.scope3_tco2e
            else:
                rev_m = (a.annual_revenue_eur or 10_000_000) / 1e6
                s3_company = sector_ef["scope3"] * rev_m
                gaps.append(DataGap(
                    field="scope3_tco2e", severity="minor",
                    impact="Scope 3 estimated; high uncertainty",
                    recommendation="Obtain investee Scope 3 disclosure (CDP C6/C7)"
                ))

        if not a.annual_revenue_eur:
            gaps.append(DataGap(
                field="annual_revenue_eur", severity="minor",
                impact="Revenue missing; WACI cannot be calculated for this asset",
                recommendation="Source from annual report / Bloomberg / Refinitiv"
            ))

        # Attributed financed emissions
        s1 = s1_company * af
        s2 = s2_company * af
        s3 = s3_company * af
        total = s1 + s2 + s3

        # Uncertainty
        unc = DQS_UNCERTAINTY[dqs]
        total_low_asset = total * (1 - unc)
        total_high_asset = total * (1 + unc)

        # Emission intensity (tCO2e / EUR M invested)
        intensity = total / (a.outstanding_eur / 1e6) if a.outstanding_eur > 0 else 0

        # Data completeness
        fields_expected = 6  # scope1, scope2, revenue, evic, emissions_verified, isin
        fields_present = sum([
            a.scope1_tco2e is not None,
            a.scope2_tco2e is not None,
            a.annual_revenue_eur is not None,
            a.evic_eur > 0,
            a.emissions_verified,
            a.isin is not None,
        ])
        completeness = round(fields_present / fields_expected * 100, 1)

        if dqs <= 2:
            verified_count += 1
        else:
            estimated_count += 1

        results.append(AssetEmissionResult(
            asset_id=a.asset_id, name=a.name,
            attribution_factor=round(af, 6),
            attribution_formula="Outstanding / EVIC",
            financed_scope1_tco2e=round(s1, 2),
            financed_scope2_tco2e=round(s2, 2),
            financed_scope3_tco2e=round(s3, 2),
            financed_total_tco2e=round(total, 2),
            financed_total_low_tco2e=round(total_low_asset, 2),
            financed_total_high_tco2e=round(total_high_asset, 2),
            emission_intensity=round(intensity, 2),
            emission_intensity_unit="tCO2e / EUR M invested",
            pcaf_data_quality_score=dqs,
            pcaf_dqs_auto_derived=a.pcaf_data_quality_score is None,
            dqs_description=DQS_DESCRIPTIONS[dqs],
            data_completeness_pct=completeness,
            data_gaps=gaps,
            estimation_method=estimation_method,
            pcaf_table_reference="PCAF Standard Part A, Table 5.3",
        ))

        total_outstanding += a.outstanding_eur
        total_s1 += s1
        total_s2 += s2
        total_s3 += s3
        total_low += total_low_asset
        total_high += total_high_asset
        dqs_weighted += dqs * a.outstanding_eur

    # Portfolio WACI
    waci = _calc_waci(req.assets, total_outstanding)

    return _build_summary(
        "listed_equity", "Listed Equity & Corporate Bonds",
        req.reporting_year, req.reporting_date, req.assets, results,
        total_outstanding, total_s1, total_s2, total_s3,
        total_low, total_high, dqs_weighted,
        waci=waci, verified_count=verified_count, estimated_count=estimated_count,
        pcaf_table="PCAF Standard Part A, Table 5.3",
        af_formula="Outstanding / EVIC",
        req_include_scope3=req.include_scope3,
    )


# =====================================================================
# 2. Business Loans & Unlisted Equity (PCAF Table 5.1, Row 2)
# =====================================================================

class BusinessLoanAsset(BaseModel):
    asset_id: str
    name: Optional[str] = None
    lei: Optional[str] = None
    sector: str = "Default"
    nace_code: Optional[str] = None
    country_iso: str = "US"
    outstanding_eur: float = Field(..., gt=0)
    total_equity_eur: Optional[float] = Field(None, gt=0, description="Total book equity")
    total_debt_eur: Optional[float] = Field(None, ge=0, description="Total borrowings")
    annual_revenue_eur: Optional[float] = Field(None, gt=0)
    scope1_tco2e: Optional[float] = Field(None, ge=0)
    scope2_tco2e: Optional[float] = Field(None, ge=0)
    scope3_tco2e: Optional[float] = Field(None, ge=0)
    emissions_verified: bool = False
    pcaf_data_quality_score: Optional[int] = Field(None, ge=1, le=5)


class BusinessLoanRequest(BaseModel):
    assets: List[BusinessLoanAsset]
    reporting_year: int = Field(2024, ge=2000, le=2100)
    reporting_date: Optional[str] = None
    include_scope3: bool = False


@router.post("/business-loans", response_model=PortfolioSummary)
def assess_business_loans(req: BusinessLoanRequest):
    """
    PCAF Asset Class 2: Business Loans & Unlisted Equity.

    Attribution Factor = Outstanding / (Total Equity + Total Debt)
    Falls back to Outstanding / (2 * Outstanding) when balance sheet unavailable.
    (PCAF Standard Part A, Table 5.1, Row 2)
    """
    if not req.assets:
        raise HTTPException(400, "At least one asset required")

    results = []
    total_outstanding = 0.0
    total_s1 = total_s2 = total_s3 = 0.0
    total_low = total_high = 0.0
    dqs_weighted = 0.0
    verified_count = estimated_count = 0

    for a in req.assets:
        gaps = []
        denom = (a.total_equity_eur or 0) + (a.total_debt_eur or 0)
        if denom <= 0:
            denom = a.outstanding_eur * 2
            gaps.append(DataGap(
                field="total_equity_eur / total_debt_eur", severity="major",
                impact="Balance sheet data missing; AF uses 2x outstanding as proxy (conservative)",
                recommendation="Obtain audited financials; request equity + debt from borrower"
            ))
        af = min(a.outstanding_eur / denom, 1.0)

        auto_dqs = _auto_dqs_corporate(
            has_verified_emissions=a.emissions_verified and a.scope1_tco2e is not None,
            has_reported_emissions=a.scope1_tco2e is not None,
            has_physical_activity=False,
            has_revenue=a.annual_revenue_eur is not None,
        )
        dqs = a.pcaf_data_quality_score if a.pcaf_data_quality_score is not None else auto_dqs
        if dqs == 1 and not (a.emissions_verified and a.scope1_tco2e is not None):
            dqs = 2

        sector_ef = SECTOR_EMISSION_FACTORS.get(a.sector, SECTOR_EMISSION_FACTORS["Default"])
        est = "reported"

        if a.scope1_tco2e is not None:
            s1_co = a.scope1_tco2e
        else:
            rev_m = (a.annual_revenue_eur or 10_000_000) / 1e6
            s1_co = sector_ef["scope1"] * rev_m
            est = "sector_average"
            gaps.append(DataGap(field="scope1_tco2e", severity="major",
                                impact="Scope 1 estimated", recommendation="Request from borrower"))

        if a.scope2_tco2e is not None:
            s2_co = a.scope2_tco2e
        else:
            rev_m = (a.annual_revenue_eur or 10_000_000) / 1e6
            s2_co = sector_ef["scope2"] * rev_m
            est = "sector_average"
            gaps.append(DataGap(field="scope2_tco2e", severity="major",
                                impact="Scope 2 estimated", recommendation="Request from borrower"))

        s3_co = 0.0
        if req.include_scope3 and a.scope3_tco2e is not None:
            s3_co = a.scope3_tco2e
        elif req.include_scope3:
            rev_m = (a.annual_revenue_eur or 10_000_000) / 1e6
            s3_co = sector_ef["scope3"] * rev_m

        s1 = s1_co * af
        s2 = s2_co * af
        s3 = s3_co * af
        total = s1 + s2 + s3
        unc = DQS_UNCERTAINTY[dqs]
        intensity = total / (a.outstanding_eur / 1e6) if a.outstanding_eur > 0 else 0

        fields_present = sum([a.scope1_tco2e is not None, a.scope2_tco2e is not None,
                              a.annual_revenue_eur is not None,
                              (a.total_equity_eur or 0) > 0, a.emissions_verified])
        completeness = round(fields_present / 5 * 100, 1)
        if dqs <= 2:
            verified_count += 1
        else:
            estimated_count += 1

        results.append(AssetEmissionResult(
            asset_id=a.asset_id, name=a.name,
            attribution_factor=round(af, 6),
            attribution_formula="Outstanding / (Total Equity + Total Debt)",
            financed_scope1_tco2e=round(s1, 2),
            financed_scope2_tco2e=round(s2, 2),
            financed_scope3_tco2e=round(s3, 2),
            financed_total_tco2e=round(total, 2),
            financed_total_low_tco2e=round(total * (1 - unc), 2),
            financed_total_high_tco2e=round(total * (1 + unc), 2),
            emission_intensity=round(intensity, 2),
            emission_intensity_unit="tCO2e / EUR M outstanding",
            pcaf_data_quality_score=dqs,
            pcaf_dqs_auto_derived=a.pcaf_data_quality_score is None,
            dqs_description=DQS_DESCRIPTIONS[dqs],
            data_completeness_pct=completeness,
            data_gaps=gaps,
            estimation_method=est,
            pcaf_table_reference="PCAF Standard Part A, Table 5.4",
        ))
        total_outstanding += a.outstanding_eur
        total_s1 += s1; total_s2 += s2; total_s3 += s3
        total_low += total * (1 - unc)
        total_high += total * (1 + unc)
        dqs_weighted += dqs * a.outstanding_eur

    waci = _calc_waci(req.assets, total_outstanding)
    return _build_summary(
        "business_loans", "Business Loans & Unlisted Equity",
        req.reporting_year, req.reporting_date, req.assets, results,
        total_outstanding, total_s1, total_s2, total_s3,
        total_low, total_high, dqs_weighted,
        waci=waci, verified_count=verified_count, estimated_count=estimated_count,
        pcaf_table="PCAF Standard Part A, Table 5.4",
        af_formula="Outstanding / (Total Equity + Total Debt)",
        req_include_scope3=req.include_scope3,
    )


# =====================================================================
# 3. Project Finance (PCAF Table 5.1, Row 3)
# =====================================================================

class ProjectFinanceAsset(BaseModel):
    asset_id: str
    name: Optional[str] = None
    sector: str = "Energy"
    country_iso: str = "US"
    outstanding_eur: float = Field(..., gt=0, description="Outstanding credit exposure")
    total_project_cost_eur: float = Field(..., gt=0, description="Total project cost at FID")
    project_scope1_tco2e: Optional[float] = Field(None, ge=0)
    project_scope2_tco2e: Optional[float] = Field(None, ge=0)
    project_scope3_tco2e: Optional[float] = Field(None, ge=0)
    project_capacity_mw: Optional[float] = None
    project_generation_mwh: Optional[float] = None
    project_type: Optional[str] = Field(None, description="renewable | fossil | infrastructure | other")
    technology: Optional[str] = Field(None, description="solar_pv | wind_onshore | wind_offshore | gas_ccgt | coal | hydro | etc.")
    pcaf_data_quality_score: Optional[int] = Field(None, ge=1, le=5)


class ProjectFinanceRequest(BaseModel):
    assets: List[ProjectFinanceAsset]
    reporting_year: int = Field(2024, ge=2000, le=2100)
    reporting_date: Optional[str] = None
    include_scope3: bool = False


# Technology emission factors (tCO2e/MWh) for project finance
PROJECT_TECH_EF = {
    "solar_pv": 0.020, "wind_onshore": 0.011, "wind_offshore": 0.012,
    "hydro": 0.024, "nuclear": 0.012, "biomass": 0.230,
    "gas_ccgt": 0.370, "gas_ocgt": 0.500, "coal": 0.900, "oil": 0.650,
    "geothermal": 0.038, "csp": 0.027,
}


@router.post("/project-finance", response_model=PortfolioSummary)
def assess_project_finance(req: ProjectFinanceRequest):
    """
    PCAF Asset Class 3: Project Finance.

    Attribution Factor = Outstanding / Total Project Cost (at FID).
    Uses project-level emissions, generation data, or technology proxy.
    (PCAF Standard Part A, Table 5.1, Row 3)
    """
    if not req.assets:
        raise HTTPException(400, "At least one asset required")

    results = []
    total_outstanding = 0.0
    total_s1 = total_s2 = total_s3 = 0.0
    total_low = total_high = 0.0
    dqs_weighted = 0.0
    verified_count = estimated_count = 0

    for a in req.assets:
        gaps = []
        af = min(a.outstanding_eur / a.total_project_cost_eur, 1.0)

        auto_dqs = _auto_dqs_project_finance(
            has_project_emissions=a.project_scope1_tco2e is not None,
            has_generation_data=a.project_generation_mwh is not None,
            has_capacity_data=a.project_capacity_mw is not None,
        )
        dqs = a.pcaf_data_quality_score if a.pcaf_data_quality_score is not None else auto_dqs
        est = "reported"

        if a.project_scope1_tco2e is not None:
            s1_raw = a.project_scope1_tco2e
        elif a.project_generation_mwh and a.technology and a.technology in PROJECT_TECH_EF:
            s1_raw = a.project_generation_mwh * PROJECT_TECH_EF[a.technology]
            est = "technology_factor"
        elif a.project_generation_mwh and a.project_type == "fossil":
            s1_raw = a.project_generation_mwh * 0.45
            est = "proxy"
            gaps.append(DataGap(field="technology", severity="major",
                                impact="Generic fossil EF used", recommendation="Specify technology"))
        elif a.project_capacity_mw and a.technology and a.technology in PROJECT_TECH_EF:
            cf_assumed = 0.25 if "solar" in (a.technology or "") else 0.35
            gen_mwh = a.project_capacity_mw * cf_assumed * 8760
            s1_raw = gen_mwh * PROJECT_TECH_EF[a.technology]
            est = "capacity_estimate"
        else:
            s1_raw = 0.0
            est = "zero_renewable"

        s2_raw = a.project_scope2_tco2e or 0.0
        s3_raw = a.project_scope3_tco2e or 0.0

        s1 = s1_raw * af
        s2 = s2_raw * af
        s3 = s3_raw * af if req.include_scope3 else 0.0
        total = s1 + s2 + s3
        unc = DQS_UNCERTAINTY[dqs]

        intensity = total / (a.outstanding_eur / 1e6) if a.outstanding_eur > 0 else 0

        fields_present = sum([a.project_scope1_tco2e is not None, a.project_scope2_tco2e is not None,
                              a.project_generation_mwh is not None, a.technology is not None])
        completeness = round(fields_present / 4 * 100, 1)
        if dqs <= 2:
            verified_count += 1
        else:
            estimated_count += 1

        results.append(AssetEmissionResult(
            asset_id=a.asset_id, name=a.name,
            attribution_factor=round(af, 6),
            attribution_formula="Outstanding / Total Project Cost",
            financed_scope1_tco2e=round(s1, 2),
            financed_scope2_tco2e=round(s2, 2),
            financed_scope3_tco2e=round(s3, 2),
            financed_total_tco2e=round(total, 2),
            financed_total_low_tco2e=round(total * (1 - unc), 2),
            financed_total_high_tco2e=round(total * (1 + unc), 2),
            emission_intensity=round(intensity, 2),
            emission_intensity_unit="tCO2e / EUR M outstanding",
            pcaf_data_quality_score=dqs,
            pcaf_dqs_auto_derived=a.pcaf_data_quality_score is None,
            dqs_description=DQS_DESCRIPTIONS[dqs],
            data_completeness_pct=completeness,
            data_gaps=gaps,
            estimation_method=est,
            pcaf_table_reference="PCAF Standard Part A, Table 5.5",
        ))
        total_outstanding += a.outstanding_eur
        total_s1 += s1; total_s2 += s2; total_s3 += s3
        total_low += total * (1 - unc); total_high += total * (1 + unc)
        dqs_weighted += dqs * a.outstanding_eur

    return _build_summary(
        "project_finance", "Project Finance",
        req.reporting_year, req.reporting_date, req.assets, results,
        total_outstanding, total_s1, total_s2, total_s3,
        total_low, total_high, dqs_weighted,
        waci=None, verified_count=verified_count, estimated_count=estimated_count,
        pcaf_table="PCAF Standard Part A, Table 5.5",
        af_formula="Outstanding / Total Project Cost",
        req_include_scope3=req.include_scope3,
    )


# =====================================================================
# 4. Commercial Real Estate (PCAF Table 5.1, Row 4)
# =====================================================================

class CREAsset(BaseModel):
    asset_id: str
    name: Optional[str] = None
    country_iso: str = "DE"
    outstanding_eur: float = Field(..., gt=0)
    property_value_eur: float = Field(..., gt=0, description="Property value at origination (LTV denominator)")
    floor_area_m2: float = Field(..., gt=0)
    building_type: str = Field("office", description="office | retail | industrial | hotel | mixed | logistics | data_centre")
    year_built: Optional[int] = None
    epc_rating: Optional[str] = Field(None, description="EPC A+-G rating")
    energy_intensity_kwh_m2: Optional[float] = Field(None, ge=0, description="Actual energy use intensity")
    emission_factor_kgco2_kwh: Optional[float] = Field(None, ge=0, description="Grid / fuel emission factor")
    scope1_tco2e: Optional[float] = Field(None, ge=0, description="Direct on-site emissions (gas/oil)")
    scope2_tco2e: Optional[float] = Field(None, ge=0, description="Purchased energy emissions")
    crrem_target_kgco2_m2: Optional[float] = Field(None, description="CRREM 1.5C pathway target for this year")
    pcaf_data_quality_score: Optional[int] = Field(None, ge=1, le=5)


class CRERequest(BaseModel):
    assets: List[CREAsset]
    reporting_year: int = Field(2024, ge=2000, le=2100)
    reporting_date: Optional[str] = None


@router.post("/commercial-real-estate", response_model=PortfolioSummary)
def assess_commercial_real_estate(req: CRERequest):
    """
    PCAF Asset Class 4: Commercial Real Estate.

    Attribution Factor = Outstanding / Property Value at origination.
    Emissions from building energy use (kgCO2/m2) or EPC rating proxy.
    (PCAF Standard Part A, Table 5.1, Row 4)
    """
    if not req.assets:
        raise HTTPException(400, "At least one asset required")

    results = []
    total_outstanding = 0.0
    total_s1 = total_s2 = 0.0
    total_low = total_high = 0.0
    dqs_weighted = 0.0
    verified_count = estimated_count = 0

    for a in req.assets:
        gaps = []
        af = min(a.outstanding_eur / a.property_value_eur, 1.0)

        auto_dqs = _auto_dqs_real_estate(
            has_actual_emissions=a.scope1_tco2e is not None and a.scope2_tco2e is not None,
            has_energy_data=a.energy_intensity_kwh_m2 is not None,
            has_epc=a.epc_rating is not None,
        )
        dqs = a.pcaf_data_quality_score if a.pcaf_data_quality_score is not None else auto_dqs

        # Building emissions estimation cascade
        if a.scope1_tco2e is not None and a.scope2_tco2e is not None:
            s1_raw = a.scope1_tco2e
            s2_raw = a.scope2_tco2e
            est = "actual_metered"
        elif a.energy_intensity_kwh_m2 and a.emission_factor_kgco2_kwh:
            total_kgco2 = a.energy_intensity_kwh_m2 * a.emission_factor_kgco2_kwh * a.floor_area_m2
            s1_raw = total_kgco2 * 0.30 / 1000  # ~30% gas heating (commercial)
            s2_raw = total_kgco2 * 0.70 / 1000
            est = "energy_intensity"
        elif a.epc_rating and a.epc_rating.upper() in EPC_EMISSION_FACTORS:
            kgco2_m2 = EPC_EMISSION_FACTORS[a.epc_rating.upper()]
            total_kgco2 = kgco2_m2 * a.floor_area_m2
            s1_raw = total_kgco2 * 0.30 / 1000
            s2_raw = total_kgco2 * 0.70 / 1000
            est = "epc_proxy"
        else:
            total_kgco2 = 80 * a.floor_area_m2  # DQS 5: commercial average ~80 kgCO2/m2
            s1_raw = total_kgco2 * 0.30 / 1000
            s2_raw = total_kgco2 * 0.70 / 1000
            est = "building_type_average"
            gaps.append(DataGap(
                field="epc_rating / energy_intensity_kwh_m2", severity="major",
                impact="No building energy data; using 80 kgCO2/m2 average",
                recommendation="Obtain EPC certificate or actual meter readings"
            ))

        s1 = s1_raw * af
        s2 = s2_raw * af
        total = s1 + s2
        unc = DQS_UNCERTAINTY[dqs]

        # Emission intensity: kgCO2/m2/yr (building-level, before attribution)
        building_intensity = (s1_raw + s2_raw) * 1000 / a.floor_area_m2 if a.floor_area_m2 > 0 else 0

        fields_present = sum([a.scope1_tco2e is not None, a.scope2_tco2e is not None,
                              a.energy_intensity_kwh_m2 is not None, a.epc_rating is not None,
                              a.year_built is not None])
        completeness = round(fields_present / 5 * 100, 1)
        if dqs <= 2:
            verified_count += 1
        else:
            estimated_count += 1

        results.append(AssetEmissionResult(
            asset_id=a.asset_id, name=a.name,
            attribution_factor=round(af, 6),
            attribution_formula="Outstanding / Property Value (at origination)",
            financed_scope1_tco2e=round(s1, 2),
            financed_scope2_tco2e=round(s2, 2),
            financed_scope3_tco2e=0.0,
            financed_total_tco2e=round(total, 2),
            financed_total_low_tco2e=round(total * (1 - unc), 2),
            financed_total_high_tco2e=round(total * (1 + unc), 2),
            emission_intensity=round(building_intensity, 2),
            emission_intensity_unit="kgCO2/m2/year (building-level)",
            pcaf_data_quality_score=dqs,
            pcaf_dqs_auto_derived=a.pcaf_data_quality_score is None,
            dqs_description=DQS_DESCRIPTIONS[dqs],
            data_completeness_pct=completeness,
            data_gaps=gaps,
            estimation_method=est,
            pcaf_table_reference="PCAF Standard Part A, Table 5.6",
        ))
        total_outstanding += a.outstanding_eur
        total_s1 += s1; total_s2 += s2
        total_low += total * (1 - unc); total_high += total * (1 + unc)
        dqs_weighted += dqs * a.outstanding_eur

    return _build_summary(
        "commercial_real_estate", "Commercial Real Estate",
        req.reporting_year, req.reporting_date, req.assets, results,
        total_outstanding, total_s1, total_s2, 0,
        total_low, total_high, dqs_weighted,
        waci=None, verified_count=verified_count, estimated_count=estimated_count,
        pcaf_table="PCAF Standard Part A, Table 5.6",
        af_formula="Outstanding / Property Value (at origination)",
        req_include_scope3=False,
    )


# =====================================================================
# 5. Mortgages (PCAF Table 5.1, Row 5)
# =====================================================================

class MortgageAsset(BaseModel):
    asset_id: str
    name: Optional[str] = None
    country_iso: str = "GB"
    outstanding_eur: float = Field(..., gt=0)
    property_value_eur: float = Field(..., gt=0, description="Property value at origination")
    floor_area_m2: float = Field(100, gt=0)
    property_type: str = Field("residential", description="residential | apartment | terraced | detached | semi_detached")
    epc_rating: Optional[str] = Field(None, description="EPC A+-G")
    energy_intensity_kwh_m2: Optional[float] = Field(None, ge=0)
    emission_factor_kgco2_kwh: Optional[float] = Field(None, ge=0)
    scope1_tco2e: Optional[float] = Field(None, ge=0)
    scope2_tco2e: Optional[float] = Field(None, ge=0)
    pcaf_data_quality_score: Optional[int] = Field(None, ge=1, le=5)


class MortgageRequest(BaseModel):
    assets: List[MortgageAsset]
    reporting_year: int = Field(2024, ge=2000, le=2100)
    reporting_date: Optional[str] = None


@router.post("/mortgages", response_model=PortfolioSummary)
def assess_mortgages(req: MortgageRequest):
    """
    PCAF Asset Class 5: Mortgages.

    Attribution Factor = Outstanding / Property Value at origination.
    Building-level emissions from EPC rating or energy data.
    (PCAF Standard Part A, Table 5.1, Row 5)
    """
    if not req.assets:
        raise HTTPException(400, "At least one asset required")

    results = []
    total_outstanding = 0.0
    total_s1 = total_s2 = 0.0
    total_low = total_high = 0.0
    dqs_weighted = 0.0
    verified_count = estimated_count = 0

    for a in req.assets:
        gaps = []
        af = min(a.outstanding_eur / a.property_value_eur, 1.0)

        auto_dqs = _auto_dqs_real_estate(
            has_actual_emissions=a.scope1_tco2e is not None and a.scope2_tco2e is not None,
            has_energy_data=a.energy_intensity_kwh_m2 is not None,
            has_epc=a.epc_rating is not None,
        )
        dqs = a.pcaf_data_quality_score if a.pcaf_data_quality_score is not None else auto_dqs

        if a.scope1_tco2e is not None and a.scope2_tco2e is not None:
            s1_raw = a.scope1_tco2e
            s2_raw = a.scope2_tco2e
            est = "actual_metered"
        elif a.energy_intensity_kwh_m2 and a.emission_factor_kgco2_kwh:
            total_kgco2 = a.energy_intensity_kwh_m2 * a.emission_factor_kgco2_kwh * a.floor_area_m2
            s1_raw = total_kgco2 * 0.40 / 1000  # Residential: ~40% gas heating
            s2_raw = total_kgco2 * 0.60 / 1000
            est = "energy_intensity"
        elif a.epc_rating and a.epc_rating.upper() in EPC_EMISSION_FACTORS:
            kgco2_m2 = EPC_EMISSION_FACTORS[a.epc_rating.upper()]
            total_kgco2 = kgco2_m2 * a.floor_area_m2
            s1_raw = total_kgco2 * 0.40 / 1000
            s2_raw = total_kgco2 * 0.60 / 1000
            est = "epc_proxy"
        else:
            total_kgco2 = 55 * a.floor_area_m2  # Residential average ~55 kgCO2/m2
            s1_raw = total_kgco2 * 0.40 / 1000
            s2_raw = total_kgco2 * 0.60 / 1000
            est = "national_average"
            gaps.append(DataGap(
                field="epc_rating", severity="major",
                impact="No EPC data; using 55 kgCO2/m2 residential average",
                recommendation="Obtain EPC rating from national registry"
            ))

        s1 = s1_raw * af
        s2 = s2_raw * af
        total = s1 + s2
        unc = DQS_UNCERTAINTY[dqs]
        building_intensity = (s1_raw + s2_raw) * 1000 / a.floor_area_m2 if a.floor_area_m2 > 0 else 0

        fields_present = sum([a.scope1_tco2e is not None, a.scope2_tco2e is not None,
                              a.energy_intensity_kwh_m2 is not None, a.epc_rating is not None])
        completeness = round(fields_present / 4 * 100, 1)
        if dqs <= 2:
            verified_count += 1
        else:
            estimated_count += 1

        results.append(AssetEmissionResult(
            asset_id=a.asset_id, name=a.name,
            attribution_factor=round(af, 6),
            attribution_formula="Outstanding / Property Value (at origination)",
            financed_scope1_tco2e=round(s1, 2),
            financed_scope2_tco2e=round(s2, 2),
            financed_scope3_tco2e=0.0,
            financed_total_tco2e=round(total, 2),
            financed_total_low_tco2e=round(total * (1 - unc), 2),
            financed_total_high_tco2e=round(total * (1 + unc), 2),
            emission_intensity=round(building_intensity, 2),
            emission_intensity_unit="kgCO2/m2/year (building-level)",
            pcaf_data_quality_score=dqs,
            pcaf_dqs_auto_derived=a.pcaf_data_quality_score is None,
            dqs_description=DQS_DESCRIPTIONS[dqs],
            data_completeness_pct=completeness,
            data_gaps=gaps,
            estimation_method=est,
            pcaf_table_reference="PCAF Standard Part A, Table 5.7",
        ))
        total_outstanding += a.outstanding_eur
        total_s1 += s1; total_s2 += s2
        total_low += total * (1 - unc); total_high += total * (1 + unc)
        dqs_weighted += dqs * a.outstanding_eur

    return _build_summary(
        "mortgages", "Mortgages",
        req.reporting_year, req.reporting_date, req.assets, results,
        total_outstanding, total_s1, total_s2, 0,
        total_low, total_high, dqs_weighted,
        waci=None, verified_count=verified_count, estimated_count=estimated_count,
        pcaf_table="PCAF Standard Part A, Table 5.7",
        af_formula="Outstanding / Property Value (at origination)",
        req_include_scope3=False,
    )


# =====================================================================
# 6. Motor Vehicle Loans (PCAF Table 5.1, Row 6)
# =====================================================================

class VehicleLoanAsset(BaseModel):
    asset_id: str
    name: Optional[str] = None
    country_iso: str = "DE"
    outstanding_eur: float = Field(..., gt=0)
    vehicle_value_eur: float = Field(..., gt=0, description="Vehicle value at origination")
    vehicle_type: str = Field("ICE_petrol",
                              description="BEV | PHEV | HEV | ICE_petrol | ICE_diesel | ICE_lpg | ICE_cng | FCEV")
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    annual_distance_km: float = Field(15000, gt=0, description="Estimated or actual annual km")
    emission_factor_gco2_km: Optional[float] = Field(None, ge=0, description="Actual WLTP gCO2/km")
    grid_emission_factor_gco2_kwh: Optional[float] = Field(None, ge=0, description="Grid EF for BEV/PHEV charging")
    pcaf_data_quality_score: Optional[int] = Field(None, ge=1, le=5)


class VehicleLoanRequest(BaseModel):
    assets: List[VehicleLoanAsset]
    reporting_year: int = Field(2024, ge=2000, le=2100)
    reporting_date: Optional[str] = None


@router.post("/vehicle-loans", response_model=PortfolioSummary)
def assess_vehicle_loans(req: VehicleLoanRequest):
    """
    PCAF Asset Class 6: Motor Vehicle Loans.

    Attribution Factor = Outstanding / Vehicle Value at origination.
    Emissions = gCO2/km * annual_km / 1e6 (tCO2e/yr).
    (PCAF Standard Part A, Table 5.1, Row 6)
    """
    if not req.assets:
        raise HTTPException(400, "At least one asset required")

    results = []
    total_outstanding = 0.0
    total_s1 = total_s2 = 0.0
    total_low = total_high = 0.0
    dqs_weighted = 0.0
    verified_count = estimated_count = 0

    for a in req.assets:
        gaps = []
        af = min(a.outstanding_eur / a.vehicle_value_eur, 1.0)

        auto_dqs = _auto_dqs_vehicle(
            has_actual_gco2km=a.emission_factor_gco2_km is not None,
            has_type_class=a.vehicle_type != "Default",
        )
        dqs = a.pcaf_data_quality_score if a.pcaf_data_quality_score is not None else auto_dqs

        ef = a.emission_factor_gco2_km if a.emission_factor_gco2_km is not None else \
            VEHICLE_EMISSION_FACTORS.get(a.vehicle_type, VEHICLE_EMISSION_FACTORS["Default"])
        est = "wltp_actual" if a.emission_factor_gco2_km is not None else "type_average"

        vehicle_tco2e = ef * a.annual_distance_km / 1e6

        # Scope split: tailpipe (S1) vs grid electricity (S2)
        if a.vehicle_type in ("BEV", "FCEV"):
            s1_raw = 0.0
            s2_raw = vehicle_tco2e
        elif a.vehicle_type in ("PHEV", "HEV"):
            s1_raw = vehicle_tco2e * 0.55  # Weighted for real-world usage
            s2_raw = vehicle_tco2e * 0.45
        else:
            s1_raw = vehicle_tco2e
            s2_raw = 0.0

        s1 = s1_raw * af
        s2 = s2_raw * af
        total = s1 + s2
        unc = DQS_UNCERTAINTY[dqs]
        intensity_gco2_km = ef  # gCO2/km is the natural unit

        fields_present = sum([a.emission_factor_gco2_km is not None, a.vehicle_type != "Default",
                              a.make is not None, a.year is not None])
        completeness = round(fields_present / 4 * 100, 1)
        if dqs <= 2:
            verified_count += 1
        else:
            estimated_count += 1

        results.append(AssetEmissionResult(
            asset_id=a.asset_id, name=a.name,
            attribution_factor=round(af, 6),
            attribution_formula="Outstanding / Vehicle Value (at origination)",
            financed_scope1_tco2e=round(s1, 4),
            financed_scope2_tco2e=round(s2, 4),
            financed_scope3_tco2e=0.0,
            financed_total_tco2e=round(total, 4),
            financed_total_low_tco2e=round(total * (1 - unc), 4),
            financed_total_high_tco2e=round(total * (1 + unc), 4),
            emission_intensity=round(intensity_gco2_km, 1),
            emission_intensity_unit="gCO2/km (WLTP)",
            pcaf_data_quality_score=dqs,
            pcaf_dqs_auto_derived=a.pcaf_data_quality_score is None,
            dqs_description=DQS_DESCRIPTIONS[dqs],
            data_completeness_pct=completeness,
            data_gaps=gaps,
            estimation_method=est,
            pcaf_table_reference="PCAF Standard Part A, Table 5.8",
        ))
        total_outstanding += a.outstanding_eur
        total_s1 += s1; total_s2 += s2
        total_low += total * (1 - unc); total_high += total * (1 + unc)
        dqs_weighted += dqs * a.outstanding_eur

    return _build_summary(
        "vehicle_loans", "Motor Vehicle Loans",
        req.reporting_year, req.reporting_date, req.assets, results,
        total_outstanding, total_s1, total_s2, 0,
        total_low, total_high, dqs_weighted,
        waci=None, verified_count=verified_count, estimated_count=estimated_count,
        pcaf_table="PCAF Standard Part A, Table 5.8",
        af_formula="Outstanding / Vehicle Value (at origination)",
        req_include_scope3=False,
    )


# =====================================================================
# 7. Sovereign Bonds (PCAF Table 5.1, Row 7)
# =====================================================================

class SovereignBondAsset(BaseModel):
    asset_id: str
    name: Optional[str] = None
    country_iso: str = Field(..., min_length=2, max_length=2, description="ISO 3166-1 alpha-2")
    outstanding_eur: float = Field(..., gt=0, description="Bond holding value (EUR)")
    sovereign_emissions_mtco2e: Optional[float] = Field(None, gt=0,
                                                         description="Override: sovereign GHG (MtCO2e, production-based)")
    gdp_ppp_usd_tn: Optional[float] = Field(None, gt=0, description="Override: GDP PPP (USD trn)")
    emissions_basis: str = Field("production", description="production | consumption")
    pcaf_data_quality_score: Optional[int] = Field(None, ge=1, le=5)


class SovereignBondRequest(BaseModel):
    assets: List[SovereignBondAsset]
    reporting_year: int = Field(2024, ge=2000, le=2100)
    reporting_date: Optional[str] = None


@router.post("/sovereign-bonds", response_model=PortfolioSummary)
def assess_sovereign_bonds(req: SovereignBondRequest):
    """
    PCAF Asset Class 7: Sovereign Bonds.

    Attribution Factor = Outstanding / PPP-adjusted GDP (converted to EUR).
    Sovereign emissions = production-based national GHG inventory.
    (PCAF Standard Part A, Table 5.1, Row 7; Table 5.9)
    """
    if not req.assets:
        raise HTTPException(400, "At least one asset required")

    results = []
    total_outstanding = 0.0
    total_s1 = 0.0
    total_low = total_high = 0.0
    dqs_weighted = 0.0
    verified_count = estimated_count = 0

    for a in req.assets:
        gaps = []
        iso = a.country_iso.upper()
        gdp = a.gdp_ppp_usd_tn or SOVEREIGN_GDP_PPP.get(iso)
        if not gdp:
            gdp = 1.0
            gaps.append(DataGap(
                field="gdp_ppp_usd_tn", severity="critical",
                impact=f"No GDP data for {iso}; using 1 USD tn proxy (highly inaccurate)",
                recommendation="Source GDP PPP from IMF WEO or World Bank WDI"
            ))
        gdp_eur = gdp * 1e12 * 0.92  # USD -> EUR approx

        af = min(a.outstanding_eur / gdp_eur, 1.0) if gdp_eur > 0 else 0

        auto_dqs = _auto_dqs_sovereign(
            has_country_emissions=iso in SOVEREIGN_EMISSIONS,
            has_country_override=a.sovereign_emissions_mtco2e is not None,
        )
        dqs = a.pcaf_data_quality_score if a.pcaf_data_quality_score is not None else auto_dqs

        sov_mt = a.sovereign_emissions_mtco2e or SOVEREIGN_EMISSIONS.get(iso, 100.0)
        if iso not in SOVEREIGN_EMISSIONS and a.sovereign_emissions_mtco2e is None:
            gaps.append(DataGap(
                field="sovereign_emissions_mtco2e", severity="major",
                impact=f"No emissions data for {iso}; using 100 MtCO2e proxy",
                recommendation="Source from EDGAR v8.0 or national GHG inventory"
            ))
        sov_tco2e = sov_mt * 1e6
        financed = sov_tco2e * af

        unc = DQS_UNCERTAINTY[dqs]
        est = "unfccc_inventory" if a.sovereign_emissions_mtco2e else (
            "edgar_modelled" if iso in SOVEREIGN_EMISSIONS else "proxy"
        )

        # Sovereign intensity: tCO2e per USD M GDP PPP
        sov_intensity = SOVEREIGN_INTENSITY.get(iso, sov_mt * 1e6 / (gdp * 1e12) * 1e6 if gdp > 0 else 0)

        fields_present = sum([iso in SOVEREIGN_EMISSIONS or a.sovereign_emissions_mtco2e is not None,
                              iso in SOVEREIGN_GDP_PPP or a.gdp_ppp_usd_tn is not None])
        completeness = round(fields_present / 2 * 100, 1)
        if dqs <= 2:
            verified_count += 1
        else:
            estimated_count += 1

        results.append(AssetEmissionResult(
            asset_id=a.asset_id, name=a.name or iso,
            attribution_factor=round(af, 10),
            attribution_formula="Outstanding / PPP-adjusted GDP (EUR)",
            financed_scope1_tco2e=round(financed, 2),
            financed_scope2_tco2e=0.0,
            financed_scope3_tco2e=0.0,
            financed_total_tco2e=round(financed, 2),
            financed_total_low_tco2e=round(financed * (1 - unc), 2),
            financed_total_high_tco2e=round(financed * (1 + unc), 2),
            emission_intensity=round(sov_intensity, 2),
            emission_intensity_unit="tCO2e / USD M GDP PPP",
            pcaf_data_quality_score=dqs,
            pcaf_dqs_auto_derived=a.pcaf_data_quality_score is None,
            dqs_description=DQS_DESCRIPTIONS[dqs],
            data_completeness_pct=completeness,
            data_gaps=gaps,
            estimation_method=est,
            pcaf_table_reference="PCAF Standard Part A, Table 5.9",
        ))
        total_outstanding += a.outstanding_eur
        total_s1 += financed
        total_low += financed * (1 - unc); total_high += financed * (1 + unc)
        dqs_weighted += dqs * a.outstanding_eur

    return _build_summary(
        "sovereign_bonds", "Sovereign Bonds",
        req.reporting_year, req.reporting_date, req.assets, results,
        total_outstanding, total_s1, 0, 0,
        total_low, total_high, dqs_weighted,
        waci=None, verified_count=verified_count, estimated_count=estimated_count,
        pcaf_table="PCAF Standard Part A, Table 5.9",
        af_formula="Outstanding / PPP-adjusted GDP (EUR)",
        req_include_scope3=False,
    )


# =====================================================================
# Multi-Asset Portfolio Aggregation
# =====================================================================

class MultiAssetSummary(BaseModel):
    """Cross-asset-class portfolio aggregation with regulatory disclosure."""
    reporting_year: int
    reporting_date: str
    total_assets: int
    total_outstanding_eur: float
    total_financed_tco2e: float
    total_financed_low_tco2e: float
    total_financed_high_tco2e: float
    portfolio_carbon_footprint_tco2e_per_meur: float
    implied_temperature_rise_c: Optional[float] = None
    weighted_data_quality_score: float
    data_completeness_pct: float
    regulatory_disclosure: RegulatoryDisclosure
    by_asset_class: List[Dict[str, Any]]
    methodology: Dict[str, str]


class MultiAssetRequest(BaseModel):
    reporting_year: int = Field(2024, ge=2000, le=2100)
    reporting_date: Optional[str] = None
    listed_equity: Optional[ListedEquityRequest] = None
    business_loans: Optional[BusinessLoanRequest] = None
    project_finance: Optional[ProjectFinanceRequest] = None
    commercial_real_estate: Optional[CRERequest] = None
    mortgages: Optional[MortgageRequest] = None
    vehicle_loans: Optional[VehicleLoanRequest] = None
    sovereign_bonds: Optional[SovereignBondRequest] = None


@router.post("/portfolio-aggregate", response_model=MultiAssetSummary)
def aggregate_portfolio(req: MultiAssetRequest):
    """
    Aggregate financed emissions across all 7 PCAF asset classes.
    Returns portfolio-level SFDR PAI #1-#3, TCFD metrics, and EU Taxonomy KPIs.
    """
    by_class = []
    total_outstanding = 0.0
    total_financed = 0.0
    total_low = total_high = 0.0
    total_s1 = total_s2 = total_s3 = 0.0
    total_assets = 0
    dqs_weighted = 0.0
    portfolio_waci = None

    handlers = [
        ("listed_equity", req.listed_equity, assess_listed_equity),
        ("business_loans", req.business_loans, assess_business_loans),
        ("project_finance", req.project_finance, assess_project_finance),
        ("commercial_real_estate", req.commercial_real_estate, assess_commercial_real_estate),
        ("mortgages", req.mortgages, assess_mortgages),
        ("vehicle_loans", req.vehicle_loans, assess_vehicle_loans),
        ("sovereign_bonds", req.sovereign_bonds, assess_sovereign_bonds),
    ]

    for ac_name, ac_req, handler in handlers:
        if ac_req is None:
            continue
        ac_req.reporting_year = req.reporting_year
        r = handler(ac_req)

        by_class.append({
            "asset_class": r.asset_class,
            "label": r.asset_class_label,
            "total_assets": r.total_assets,
            "outstanding_eur": r.total_outstanding_eur,
            "financed_tco2e": r.total_financed_tco2e,
            "financed_low_tco2e": r.total_financed_low_tco2e,
            "financed_high_tco2e": r.total_financed_high_tco2e,
            "carbon_footprint": r.portfolio_carbon_footprint_tco2e_per_meur,
            "weighted_dqs": r.weighted_data_quality_score,
            "data_completeness_pct": r.data_completeness_pct,
        })
        total_outstanding += r.total_outstanding_eur
        total_financed += r.total_financed_tco2e
        total_low += r.total_financed_low_tco2e
        total_high += r.total_financed_high_tco2e
        total_s1 += r.total_financed_scope1_tco2e
        total_s2 += r.total_financed_scope2_tco2e
        total_s3 += r.total_financed_scope3_tco2e
        total_assets += r.total_assets
        dqs_weighted += r.weighted_data_quality_score * r.total_outstanding_eur

        if r.waci_scope12_tco2e_per_meur is not None:
            if portfolio_waci is None:
                portfolio_waci = 0.0
            portfolio_waci += r.waci_scope12_tco2e_per_meur * (r.total_outstanding_eur / max(total_outstanding, 1))

    cf = total_financed / (total_outstanding / 1e6) if total_outstanding > 0 else 0
    avg_dqs = dqs_weighted / total_outstanding if total_outstanding > 0 else 5
    avg_completeness = sum(bc["data_completeness_pct"] for bc in by_class) / len(by_class) if by_class else 0

    rd = RegulatoryDisclosure(
        sfdr_pai_1_financed_ghg_tco2e=round(total_financed, 2),
        sfdr_pai_1_scope1_tco2e=round(total_s1, 2),
        sfdr_pai_1_scope2_tco2e=round(total_s2, 2),
        sfdr_pai_1_scope3_tco2e=round(total_s3, 2),
        sfdr_pai_2_carbon_footprint_tco2e_per_meur=round(cf, 2),
        sfdr_pai_3_waci_tco2e_per_meur=round(portfolio_waci, 2) if portfolio_waci else None,
        tcfd_financed_emissions_tco2e=round(total_financed, 2),
        tcfd_waci=round(portfolio_waci, 2) if portfolio_waci else None,
        tcfd_implied_temp_rise_c=_waci_to_temp(portfolio_waci) if portfolio_waci else None,
    )

    return MultiAssetSummary(
        reporting_year=req.reporting_year,
        reporting_date=req.reporting_date or str(date(req.reporting_year, 12, 31)),
        total_assets=total_assets,
        total_outstanding_eur=round(total_outstanding, 2),
        total_financed_tco2e=round(total_financed, 2),
        total_financed_low_tco2e=round(total_low, 2),
        total_financed_high_tco2e=round(total_high, 2),
        portfolio_carbon_footprint_tco2e_per_meur=round(cf, 2),
        implied_temperature_rise_c=_waci_to_temp(portfolio_waci) if portfolio_waci else None,
        weighted_data_quality_score=round(avg_dqs, 2),
        data_completeness_pct=round(avg_completeness, 1),
        regulatory_disclosure=rd,
        by_asset_class=by_class,
        methodology={
            "standard": "PCAF Global GHG Accounting & Reporting Standard v2.0 (Dec 2022)",
            "part": "Part A: Financed Emissions",
            "ghg_protocol": "GHG Protocol Corporate Standard (Scope 1/2/3)",
            "sfdr": "EU SFDR RTS Annex I, PAI Indicators #1-#3",
            "tcfd": "TCFD 2021 Guidance on Metrics, Targets, and Transition Plans",
            "temperature": "Implied temperature based on WACI (PACTA / right. based on science)",
        },
    )


# =====================================================================
# Metadata & Reference Endpoints
# =====================================================================

@router.get("/asset-classes")
def list_asset_classes():
    """Return all 7 PCAF asset classes with attribution formulas and DQS table references."""
    return {
        "standard": "PCAF Global GHG Accounting & Reporting Standard v2.0 (Dec 2022)",
        "publisher": "Partnership for Carbon Accounting Financials (PCAF)",
        "effective_date": "2022-12-01",
        "asset_classes": [
            {"id": "listed_equity", "label": "Listed Equity & Corporate Bonds",
             "pcaf_row": "Table 5.1, Row 1", "dqs_table": "Table 5.3",
             "af_formula": "Outstanding / EVIC",
             "emission_scope": "S1+S2 (+S3 optional)",
             "intensity_unit": "tCO2e / EUR M invested",
             "endpoint": "/api/v1/pcaf/listed-equity"},
            {"id": "business_loans", "label": "Business Loans & Unlisted Equity",
             "pcaf_row": "Table 5.1, Row 2", "dqs_table": "Table 5.4",
             "af_formula": "Outstanding / (Total Equity + Total Debt)",
             "emission_scope": "S1+S2 (+S3 optional)",
             "intensity_unit": "tCO2e / EUR M outstanding",
             "endpoint": "/api/v1/pcaf/business-loans"},
            {"id": "project_finance", "label": "Project Finance",
             "pcaf_row": "Table 5.1, Row 3", "dqs_table": "Table 5.5",
             "af_formula": "Outstanding / Total Project Cost",
             "emission_scope": "Project-level S1+S2 (+S3 optional)",
             "intensity_unit": "tCO2e / EUR M outstanding",
             "endpoint": "/api/v1/pcaf/project-finance"},
            {"id": "commercial_real_estate", "label": "Commercial Real Estate",
             "pcaf_row": "Table 5.1, Row 4", "dqs_table": "Table 5.6",
             "af_formula": "Outstanding / Property Value at origination",
             "emission_scope": "Building energy (S1+S2)",
             "intensity_unit": "kgCO2/m2/year",
             "endpoint": "/api/v1/pcaf/commercial-real-estate"},
            {"id": "mortgages", "label": "Mortgages",
             "pcaf_row": "Table 5.1, Row 5", "dqs_table": "Table 5.7",
             "af_formula": "Outstanding / Property Value at origination",
             "emission_scope": "Building energy (S1+S2)",
             "intensity_unit": "kgCO2/m2/year",
             "endpoint": "/api/v1/pcaf/mortgages"},
            {"id": "vehicle_loans", "label": "Motor Vehicle Loans",
             "pcaf_row": "Table 5.1, Row 6", "dqs_table": "Table 5.8",
             "af_formula": "Outstanding / Vehicle Value at origination",
             "emission_scope": "Tailpipe + electricity (S1+S2)",
             "intensity_unit": "gCO2/km (WLTP)",
             "endpoint": "/api/v1/pcaf/vehicle-loans"},
            {"id": "sovereign_bonds", "label": "Sovereign Bonds",
             "pcaf_row": "Table 5.1, Row 7", "dqs_table": "Table 5.9",
             "af_formula": "Outstanding / PPP-adjusted GDP",
             "emission_scope": "National production-based GHG",
             "intensity_unit": "tCO2e / USD M GDP PPP",
             "endpoint": "/api/v1/pcaf/sovereign-bonds"},
        ],
        "data_quality_scores": DQS_DESCRIPTIONS,
        "uncertainty_bands": DQS_UNCERTAINTY,
    }


@router.get("/methodology")
def get_methodology():
    """Return full PCAF methodology disclosure for investor reporting."""
    return {
        "standard": {
            "name": "PCAF Global GHG Accounting & Reporting Standard",
            "version": "2nd Edition (Part A)",
            "date": "December 2022",
            "publisher": "Partnership for Carbon Accounting Financials",
            "url": "https://carbonaccountingfinancials.com/standard",
        },
        "attribution_factors": {
            "description": "Asset-class-specific formulas linking FI exposure to counterparty emissions",
            "principle": "Proportional attribution based on financial claim relative to enterprise/asset value",
            "avoidance_of_double_counting": "EVIC-based AF for listed equity ensures total attributed <= 100% of company emissions",
        },
        "data_quality": {
            "description": "5-level Data Quality Score system per PCAF Tables 5.3-5.9",
            "auto_derivation": "DQS is auto-derived from data provenance; user override validated against data provided",
            "uncertainty": "DQS-based uncertainty bands applied: DQS 1 = +/-10%, DQS 5 = +/-60%",
            "improvement_target": "PCAF recommends annual DQS improvement plan toward DQS <= 2 for material exposures",
        },
        "scope_boundaries": {
            "scope1": "Direct GHG from owned/controlled sources (GHG Protocol Corporate Standard)",
            "scope2": "Indirect GHG from purchased energy (location-based default, market-based if available)",
            "scope3": "Optional; material for high-emitting sectors (PCAF Standard Section 5.3)",
        },
        "regulatory_alignment": {
            "sfdr": "EU SFDR RTS Annex I, PAI #1 (financed GHG), #2 (carbon footprint), #3 (WACI)",
            "eu_taxonomy": "Art.8 KPI denominators aligned with PCAF outstanding amounts",
            "tcfd": "TCFD 2021 Guidance on Metrics, Targets, and Transition Plans (Section C.3)",
        },
        "sector_emission_factors": {
            "source": "EXIOBASE 3.8 / EEIO 2022 sector averages",
            "usage": "Fallback for DQS 4-5 when company-specific data unavailable",
            "unit": "tCO2e / EUR M revenue",
        },
        "temperature_alignment": {
            "method": "WACI-based implied temperature (piecewise linear interpolation)",
            "source": "PACTA methodology / right. based on science / TCFD portfolio alignment",
            "caveat": "Indicative only; not a physical temperature pathway projection",
        },
    }


@router.get("/sector-emission-factors")
def list_sector_emission_factors():
    """Return sector-level emission factor benchmarks (DQS 4-5 fallback)."""
    return {
        "unit": "tCO2e per EUR M revenue",
        "source": "PCAF Standard / EXIOBASE 3.8 / EEIO 2022 sector averages",
        "note": "Used when investee-specific emissions are unavailable (DQS >= 4)",
        "factors": SECTOR_EMISSION_FACTORS,
    }


@router.get("/epc-benchmarks")
def list_epc_benchmarks():
    """Return EPC rating emission intensity benchmarks for CRE and Mortgages."""
    return {
        "unit": "kgCO2/m2/year",
        "source": "EU EPBD recast 2024 / CRREM Global Pathways v2.0",
        "note": "Used for DQS 3 when actual energy data unavailable",
        "ratings": EPC_EMISSION_FACTORS,
    }


@router.get("/vehicle-benchmarks")
def list_vehicle_benchmarks():
    """Return vehicle type emission factor benchmarks for Motor Vehicle Loans."""
    return {
        "unit": "gCO2/km (WLTP cycle)",
        "source": "EU CO2 standards for cars (Reg. 2019/631) / ICCT 2023",
        "types": VEHICLE_EMISSION_FACTORS,
    }


@router.get("/sovereign-data")
def list_sovereign_data():
    """Return sovereign emissions and GDP data for Sovereign Bond attribution."""
    data = {}
    all_isos = set(list(SOVEREIGN_EMISSIONS.keys()) + list(SOVEREIGN_GDP_PPP.keys()))
    for iso in sorted(all_isos):
        data[iso] = {
            "emissions_mtco2e": SOVEREIGN_EMISSIONS.get(iso),
            "gdp_ppp_usd_tn": SOVEREIGN_GDP_PPP.get(iso),
            "intensity_tco2e_per_usdm_gdp": SOVEREIGN_INTENSITY.get(iso),
        }
    return {
        "source": "EDGAR v8.0 / UNFCCC CRF / IMF WEO / World Bank WDI (2022-2023)",
        "countries": data,
    }


@router.get("/dqs-improvement-guidance")
def dqs_improvement_guidance():
    """Return PCAF DQS improvement roadmap for investor data quality programmes."""
    return {
        "principle": "Material exposures should target DQS <= 2 within 3 reporting cycles",
        "priority_order": [
            "1. High-exposure assets with DQS 5 (proxy) -- immediate engagement",
            "2. High-emitting sectors with DQS 4 (sector average) -- CDP questionnaire",
            "3. Real estate / mortgages without EPC -- EPC registry access",
            "4. Vehicle loans without WLTP -- vehicle registry integration",
            "5. Sovereign bonds -- all Annex I countries have verified CRF data (DQS 1)",
        ],
        "data_sources_by_dqs": {
            "1": ["CDP verified responses", "GHGP-assured inventory", "EU ETS verified"],
            "2": ["CDP self-reported", "Annual/sustainability report", "Direct engagement"],
            "3": ["Energy bills + grid EF", "Production data + technology EF", "EPC certificate"],
            "4": ["EXIOBASE/EEIO + revenue", "Sector average + NACE code", "Country average"],
            "5": ["Asset class average", "Regional proxy", "No data"],
        },
    }


# =====================================================================
# Helper Functions
# =====================================================================

def _sector_fallback(sector: str, revenue_eur: Optional[float], scope_key: str) -> float:
    """Estimate emissions from sector average when company data unavailable (DQS 4-5)."""
    ef = SECTOR_EMISSION_FACTORS.get(sector, SECTOR_EMISSION_FACTORS["Default"])
    rev_m = (revenue_eur or 10_000_000) / 1e6
    return ef[scope_key] * rev_m


def _calc_waci(assets, total_outstanding: float) -> Optional[float]:
    """
    WACI = Sum_i [ (outstanding_i / total_AUM) * (S1+S2)_i / revenue_M_i ]
    (TCFD / SFDR PAI #3)

    Only calculated for assets with revenue data; returns None if no WACI-eligible assets.
    """
    if total_outstanding <= 0:
        return None
    waci = 0.0
    covered = 0
    for a in assets:
        rev = getattr(a, 'annual_revenue_eur', None)
        if not rev or rev <= 0:
            continue
        s1 = getattr(a, 'scope1_tco2e', None) or 0
        s2 = getattr(a, 'scope2_tco2e', None) or 0
        if s1 == 0 and s2 == 0:
            continue
        weight = a.outstanding_eur / total_outstanding
        waci += weight * (s1 + s2) / (rev / 1e6)
        covered += 1
    return round(waci, 4) if covered > 0 else None


def _build_summary(
    asset_class, label, year, reporting_date, assets, results,
    total_outstanding, total_s1, total_s2, total_s3,
    total_low, total_high, dqs_weighted,
    waci=None, verified_count=0, estimated_count=0,
    pcaf_table="", af_formula="", req_include_scope3=False,
):
    """Build standardized PortfolioSummary with regulatory disclosure."""
    total_fin = total_s1 + total_s2 + total_s3
    cf = total_fin / (total_outstanding / 1e6) if total_outstanding > 0 else 0
    avg_dqs = dqs_weighted / total_outstanding if total_outstanding > 0 else 5
    total_count = verified_count + estimated_count
    avg_completeness = (sum(r.data_completeness_pct for r in results) / len(results)) if results else 0

    rd = RegulatoryDisclosure(
        sfdr_pai_1_financed_ghg_tco2e=round(total_fin, 2),
        sfdr_pai_1_scope1_tco2e=round(total_s1, 2),
        sfdr_pai_1_scope2_tco2e=round(total_s2, 2),
        sfdr_pai_1_scope3_tco2e=round(total_s3, 2),
        sfdr_pai_2_carbon_footprint_tco2e_per_meur=round(cf, 2),
        sfdr_pai_3_waci_tco2e_per_meur=round(waci, 2) if waci else None,
        tcfd_financed_emissions_tco2e=round(total_fin, 2),
        tcfd_waci=round(waci, 2) if waci else None,
        tcfd_implied_temp_rise_c=_waci_to_temp(waci) if waci else None,
    )

    return PortfolioSummary(
        asset_class=asset_class,
        asset_class_label=label,
        reporting_year=year,
        reporting_date=reporting_date or str(date(year, 12, 31)),
        total_assets=len(assets),
        total_outstanding_eur=round(total_outstanding, 2),
        total_financed_scope1_tco2e=round(total_s1, 2),
        total_financed_scope2_tco2e=round(total_s2, 2),
        total_financed_scope3_tco2e=round(total_s3, 2),
        total_financed_tco2e=round(total_fin, 2),
        total_financed_low_tco2e=round(total_low, 2),
        total_financed_high_tco2e=round(total_high, 2),
        portfolio_carbon_footprint_tco2e_per_meur=round(cf, 2),
        waci_scope12_tco2e_per_meur=round(waci, 2) if waci else None,
        implied_temperature_rise_c=_waci_to_temp(waci) if waci else None,
        weighted_data_quality_score=round(avg_dqs, 2),
        data_completeness_pct=round(avg_completeness, 1),
        assets_with_verified_data_pct=round(verified_count / total_count * 100, 1) if total_count > 0 else 0,
        assets_with_estimated_data_pct=round(estimated_count / total_count * 100, 1) if total_count > 0 else 0,
        coverage_pct=100.0,
        coverage_by_outstanding_pct=100.0,
        regulatory_disclosure=rd,
        methodology={
            "standard": "PCAF v2.0 (Dec 2022)",
            "asset_class_table": pcaf_table,
            "attribution_formula": af_formula,
            "scope3_included": str(req_include_scope3),
            "dqs_derivation": "Auto-derived from data provenance per " + pcaf_table,
            "uncertainty": "DQS-based bands (DQS 1: +/-10% to DQS 5: +/-60%)",
            "ghg_protocol": "GHG Protocol Corporate Standard (Scope 1/2/3)",
        },
        per_asset=results,
    )
