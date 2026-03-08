"""
Real Estate Portfolio NAV Roll-Up API Routes.

Endpoints:
  POST /api/v1/re-portfolio/nav          — Full portfolio NAV calculation
  POST /api/v1/re-portfolio/crrem        — CRREM stranding analysis only
  POST /api/v1/re-portfolio/epc          — EPC distribution + MEPS compliance
  POST /api/v1/re-portfolio/concentration — Sector + geographic concentration
  POST /api/v1/re-portfolio/carbon       — Portfolio carbon metrics
  GET  /api/v1/re-portfolio/meps-timelines — Available MEPS regulatory timelines
  GET  /api/v1/re-portfolio/crrem-pathways — Available CRREM pathway metadata
"""

from __future__ import annotations

import traceback
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.re_portfolio_engine import (
    CRREM_PATHWAYS,
    MEPS_TIMELINES,
    CRREMPropertyResult,
    EPCDistribution,
    GeographicConcentration,
    MEPSComplianceResult,
    PortfolioDefinition,
    PortfolioNAVResult,
    PropertyAsset,
    REPortfolioEngine,
    SectorConcentration,
)

router = APIRouter(prefix="/api/v1/re-portfolio", tags=["Real Estate Portfolio"])

# ---------------------------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------------------------


class PropertyInput(BaseModel):
    property_id: str = Field(..., description="Unique property identifier")
    name: str = Field(..., description="Property name")
    property_type: str = Field("office", description="office|retail|industrial|multifamily|hotel|data_center|logistics|mixed_use")
    country_iso: str = Field("GB", description="ISO 3166-1 alpha-2 country code")
    city: Optional[str] = None
    floor_area_m2: float = Field(0, ge=0)
    year_built: Optional[int] = None
    last_refurbishment_year: Optional[int] = None

    # Valuation
    market_value: float = Field(0, ge=0, description="Current market value")
    book_value: float = Field(0, ge=0)
    valuation_date: Optional[str] = None
    valuation_method: str = Field("income", description="income|cost|sales_comparison|dcf")
    cap_rate_pct: float = Field(0, ge=0, le=30)
    noi: float = Field(0, ge=0, description="Net operating income")
    occupancy_pct: float = Field(100, ge=0, le=100)
    gross_rental_income: float = Field(0, ge=0)

    # Energy & Carbon
    epc_rating: str = Field("C", description="EPC rating A+ through G")
    energy_intensity_kwh_m2: float = Field(0, ge=0)
    carbon_intensity_kgco2_m2: float = Field(0, ge=0)

    # Certifications
    certifications: List[str] = Field(default_factory=list)

    # Debt
    outstanding_debt: float = Field(0, ge=0)
    loan_to_value_pct: float = Field(0, ge=0, le=100)

    # ESG adjustments
    esg_adjustment_pct: float = Field(0, description="ESG value adjustment %. Positive = premium, negative = discount")
    climate_adjustment_pct: float = Field(0, description="Climate value adjustment %")


class PortfolioNAVRequest(BaseModel):
    portfolio_id: str = Field(..., description="Portfolio identifier")
    name: str = Field(..., description="Portfolio / fund name")
    fund_structure: str = Field("open_end", description="open_end|closed_end|reit|separate_account")
    base_currency: str = Field("GBP")
    valuation_basis: str = Field("market_value", description="market_value|fair_value|investment_value")
    valuation_date: Optional[str] = None
    properties: List[PropertyInput] = Field(..., min_length=1, description="List of properties in the portfolio")
    crrem_scenario: str = Field("1.5C", description="CRREM scenario: 1.5C or 2C")
    carbon_price_eur_per_tco2: float = Field(75, ge=0, le=500, description="Carbon price in EUR/tCO2e")


class CRREMRequest(BaseModel):
    properties: List[PropertyInput] = Field(..., min_length=1)
    scenario: str = Field("1.5C")
    carbon_price_eur_per_tco2: float = Field(75, ge=0, le=500)


class EPCRequest(BaseModel):
    properties: List[PropertyInput] = Field(..., min_length=1)


class ConcentrationRequest(BaseModel):
    properties: List[PropertyInput] = Field(..., min_length=1)


class CarbonRequest(BaseModel):
    properties: List[PropertyInput] = Field(..., min_length=1)


# --- Response models ---

class EPCDistributionResponse(BaseModel):
    rating: str
    property_count: int
    property_pct: float
    gav_total: float
    gav_pct: float
    avg_energy_intensity: float


class MEPSComplianceResponse(BaseModel):
    property_id: str
    property_name: str
    country_iso: str
    current_epc: str
    compliant_2030: bool
    compliant_2033: bool
    minimum_epc_2030: str
    minimum_epc_2033: str
    gap_bands_to_2030: int
    gap_bands_to_2033: int


class CRREMPropertyResponse(BaseModel):
    property_id: str
    property_name: str
    property_type: str
    country_iso: str
    floor_area_m2: float
    market_value: float
    energy_intensity_kwh_m2: float
    carbon_intensity_kgco2_m2: float
    pathway_threshold_current_kwh_m2: Optional[float]
    stranding_year_1_5c: Optional[int]
    stranding_year_2c: Optional[int]
    years_to_stranding_1_5c: Optional[int]
    is_already_stranded: bool
    gap_to_pathway_pct: float
    annual_reduction_required_pct: float
    carbon_cost_annual_eur: float


class SectorConcentrationResponse(BaseModel):
    property_type: str
    property_count: int
    property_pct: float
    gav_total: float
    gav_pct: float
    avg_cap_rate: float
    avg_occupancy: float
    avg_energy_intensity: float
    avg_carbon_intensity: float


class GeographicConcentrationResponse(BaseModel):
    country_iso: str
    property_count: int
    property_pct: float
    gav_total: float
    gav_pct: float
    avg_energy_intensity: float
    avg_carbon_intensity: float


class PortfolioNAVResponse(BaseModel):
    portfolio_id: str
    portfolio_name: str
    valuation_date: str
    base_currency: str

    # NAV
    gross_asset_value: float
    total_debt: float
    net_asset_value: float
    nav_per_property: float
    property_count: int

    # Yield
    weighted_avg_cap_rate_pct: float
    portfolio_noi_yield_pct: float
    total_noi: float
    total_gross_rental_income: float
    weighted_avg_occupancy_pct: float

    # ESG
    esg_adjusted_gav: float
    climate_adjusted_gav: float
    total_esg_impact_pct: float
    total_climate_impact_pct: float

    # Carbon
    portfolio_carbon_intensity_kgco2_m2: float
    total_emissions_tco2e: float
    total_floor_area_m2: float

    # EPC
    epc_distribution: List[EPCDistributionResponse]
    green_property_count: int
    brown_property_count: int
    green_pct_by_gav: float
    brown_pct_by_gav: float

    # MEPS
    meps_compliant_2030_count: int
    meps_compliant_2030_pct: float
    meps_compliant_2033_count: int
    meps_compliant_2033_pct: float
    meps_non_compliant_2030: List[MEPSComplianceResponse]

    # CRREM
    crrem_stranded_now_count: int
    crrem_stranded_by_2030_count: int
    crrem_stranded_by_2040_count: int
    crrem_portfolio_stranding_risk_pct: float
    crrem_avg_years_to_stranding: Optional[float]
    crrem_total_annual_carbon_cost_eur: float
    crrem_property_results: List[CRREMPropertyResponse]

    # Concentration
    sector_concentration: List[SectorConcentrationResponse]
    geographic_concentration: List[GeographicConcentrationResponse]

    # Validation
    validation_summary: Dict[str, Any]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

engine = REPortfolioEngine()


def _to_property_asset(p: PropertyInput) -> PropertyAsset:
    return PropertyAsset(
        property_id=p.property_id,
        name=p.name,
        property_type=p.property_type,
        country_iso=p.country_iso,
        city=p.city,
        floor_area_m2=Decimal(str(p.floor_area_m2)),
        year_built=p.year_built,
        last_refurbishment_year=p.last_refurbishment_year,
        market_value=Decimal(str(p.market_value)),
        book_value=Decimal(str(p.book_value)),
        valuation_method=p.valuation_method,
        cap_rate_pct=Decimal(str(p.cap_rate_pct)),
        noi=Decimal(str(p.noi)),
        occupancy_pct=Decimal(str(p.occupancy_pct)),
        gross_rental_income=Decimal(str(p.gross_rental_income)),
        epc_rating=p.epc_rating,
        energy_intensity_kwh_m2=Decimal(str(p.energy_intensity_kwh_m2)),
        carbon_intensity_kgco2_m2=Decimal(str(p.carbon_intensity_kgco2_m2)),
        certifications=p.certifications,
        outstanding_debt=Decimal(str(p.outstanding_debt)),
        loan_to_value_pct=Decimal(str(p.loan_to_value_pct)),
        esg_adjustment_pct=Decimal(str(p.esg_adjustment_pct)),
        climate_adjustment_pct=Decimal(str(p.climate_adjustment_pct)),
    )


def _to_portfolio(req: PortfolioNAVRequest) -> PortfolioDefinition:
    val_date = None
    if req.valuation_date:
        val_date = date.fromisoformat(req.valuation_date)
    return PortfolioDefinition(
        portfolio_id=req.portfolio_id,
        name=req.name,
        fund_structure=req.fund_structure,
        base_currency=req.base_currency,
        valuation_basis=req.valuation_basis,
        valuation_date=val_date,
        properties=[_to_property_asset(p) for p in req.properties],
    )


def _decimal_to_float(val) -> float:
    if isinstance(val, Decimal):
        return float(val)
    return val


def _serialize_nav(result: PortfolioNAVResult) -> dict:
    """Convert PortfolioNAVResult to JSON-serializable dict."""
    return {
        "portfolio_id": result.portfolio_id,
        "portfolio_name": result.portfolio_name,
        "valuation_date": str(result.valuation_date),
        "base_currency": result.base_currency,
        # NAV
        "gross_asset_value": _decimal_to_float(result.gross_asset_value),
        "total_debt": _decimal_to_float(result.total_debt),
        "net_asset_value": _decimal_to_float(result.net_asset_value),
        "nav_per_property": _decimal_to_float(result.nav_per_property),
        "property_count": result.property_count,
        # Yield
        "weighted_avg_cap_rate_pct": _decimal_to_float(result.weighted_avg_cap_rate_pct),
        "portfolio_noi_yield_pct": _decimal_to_float(result.portfolio_noi_yield_pct),
        "total_noi": _decimal_to_float(result.total_noi),
        "total_gross_rental_income": _decimal_to_float(result.total_gross_rental_income),
        "weighted_avg_occupancy_pct": _decimal_to_float(result.weighted_avg_occupancy_pct),
        # ESG
        "esg_adjusted_gav": _decimal_to_float(result.esg_adjusted_gav),
        "climate_adjusted_gav": _decimal_to_float(result.climate_adjusted_gav),
        "total_esg_impact_pct": _decimal_to_float(result.total_esg_impact_pct),
        "total_climate_impact_pct": _decimal_to_float(result.total_climate_impact_pct),
        # Carbon
        "portfolio_carbon_intensity_kgco2_m2": _decimal_to_float(result.portfolio_carbon_intensity_kgco2_m2),
        "total_emissions_tco2e": _decimal_to_float(result.total_emissions_tco2e),
        "total_floor_area_m2": _decimal_to_float(result.total_floor_area_m2),
        # EPC
        "epc_distribution": [
            {
                "rating": e.rating,
                "property_count": e.property_count,
                "property_pct": _decimal_to_float(e.property_pct),
                "gav_total": _decimal_to_float(e.gav_total),
                "gav_pct": _decimal_to_float(e.gav_pct),
                "avg_energy_intensity": _decimal_to_float(e.avg_energy_intensity),
            }
            for e in result.epc_distribution
        ],
        "green_property_count": result.green_property_count,
        "brown_property_count": result.brown_property_count,
        "green_pct_by_gav": _decimal_to_float(result.green_pct_by_gav),
        "brown_pct_by_gav": _decimal_to_float(result.brown_pct_by_gav),
        # MEPS
        "meps_compliant_2030_count": result.meps_compliant_2030_count,
        "meps_compliant_2030_pct": _decimal_to_float(result.meps_compliant_2030_pct),
        "meps_compliant_2033_count": result.meps_compliant_2033_count,
        "meps_compliant_2033_pct": _decimal_to_float(result.meps_compliant_2033_pct),
        "meps_non_compliant_2030": [
            {
                "property_id": m.property_id,
                "property_name": m.property_name,
                "country_iso": m.country_iso,
                "current_epc": m.current_epc,
                "compliant_2030": m.compliant_2030,
                "compliant_2033": m.compliant_2033,
                "minimum_epc_2030": m.minimum_epc_2030,
                "minimum_epc_2033": m.minimum_epc_2033,
                "gap_bands_to_2030": m.gap_bands_to_2030,
                "gap_bands_to_2033": m.gap_bands_to_2033,
            }
            for m in result.meps_non_compliant_2030
        ],
        # CRREM
        "crrem_stranded_now_count": result.crrem_stranded_now_count,
        "crrem_stranded_by_2030_count": result.crrem_stranded_by_2030_count,
        "crrem_stranded_by_2040_count": result.crrem_stranded_by_2040_count,
        "crrem_portfolio_stranding_risk_pct": _decimal_to_float(result.crrem_portfolio_stranding_risk_pct),
        "crrem_avg_years_to_stranding": _decimal_to_float(result.crrem_avg_years_to_stranding) if result.crrem_avg_years_to_stranding is not None else None,
        "crrem_total_annual_carbon_cost_eur": _decimal_to_float(result.crrem_total_annual_carbon_cost_eur),
        "crrem_property_results": [
            {
                "property_id": c.property_id,
                "property_name": c.property_name,
                "property_type": c.property_type,
                "country_iso": c.country_iso,
                "floor_area_m2": _decimal_to_float(c.floor_area_m2),
                "market_value": _decimal_to_float(c.market_value),
                "energy_intensity_kwh_m2": _decimal_to_float(c.energy_intensity_kwh_m2),
                "carbon_intensity_kgco2_m2": _decimal_to_float(c.carbon_intensity_kgco2_m2),
                "pathway_threshold_current_kwh_m2": _decimal_to_float(c.pathway_threshold_current_kwh_m2) if c.pathway_threshold_current_kwh_m2 is not None else None,
                "stranding_year_1_5c": c.stranding_year_1_5c,
                "stranding_year_2c": c.stranding_year_2c,
                "years_to_stranding_1_5c": c.years_to_stranding_1_5c,
                "is_already_stranded": c.is_already_stranded,
                "gap_to_pathway_pct": _decimal_to_float(c.gap_to_pathway_pct),
                "annual_reduction_required_pct": _decimal_to_float(c.annual_reduction_required_pct),
                "carbon_cost_annual_eur": _decimal_to_float(c.carbon_cost_annual_eur),
            }
            for c in result.crrem_property_results
        ],
        # Concentration
        "sector_concentration": [
            {
                "property_type": s.property_type,
                "property_count": s.property_count,
                "property_pct": _decimal_to_float(s.property_pct),
                "gav_total": _decimal_to_float(s.gav_total),
                "gav_pct": _decimal_to_float(s.gav_pct),
                "avg_cap_rate": _decimal_to_float(s.avg_cap_rate),
                "avg_occupancy": _decimal_to_float(s.avg_occupancy),
                "avg_energy_intensity": _decimal_to_float(s.avg_energy_intensity),
                "avg_carbon_intensity": _decimal_to_float(s.avg_carbon_intensity),
            }
            for s in result.sector_concentration
        ],
        "geographic_concentration": [
            {
                "country_iso": g.country_iso,
                "property_count": g.property_count,
                "property_pct": _decimal_to_float(g.property_pct),
                "gav_total": _decimal_to_float(g.gav_total),
                "gav_pct": _decimal_to_float(g.gav_pct),
                "avg_energy_intensity": _decimal_to_float(g.avg_energy_intensity),
                "avg_carbon_intensity": _decimal_to_float(g.avg_carbon_intensity),
            }
            for g in result.geographic_concentration
        ],
        # Validation
        "validation_summary": result.validation_summary,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/nav", summary="Full portfolio NAV roll-up with CRREM + EPC + MEPS")
async def calculate_portfolio_nav(req: PortfolioNAVRequest):
    """
    Comprehensive portfolio NAV calculation including:
    - Gross/net asset value, yield metrics
    - ESG and climate-adjusted NAV
    - EPC distribution and green/brown split
    - MEPS compliance analysis (2030/2033)
    - CRREM stranding per property and portfolio-level risk
    - Sector and geographic concentration
    - Portfolio carbon intensity and total emissions
    """
    try:
        portfolio = _to_portfolio(req)
        result = engine.calculate_portfolio_nav(
            portfolio=portfolio,
            crrem_scenario=req.crrem_scenario,
            carbon_price_eur_per_tco2=Decimal(str(req.carbon_price_eur_per_tco2)),
        )
        return _serialize_nav(result)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/crrem", summary="CRREM stranding analysis for property list")
async def crrem_analysis(req: CRREMRequest):
    """CRREM stranding analysis with per-property and portfolio-level results."""
    try:
        props = [_to_property_asset(p) for p in req.properties]
        result = engine._calculate_crrem_stranding(
            props, req.scenario, Decimal(str(req.carbon_price_eur_per_tco2))
        )
        # Serialize
        return {
            "scenario": req.scenario,
            "carbon_price_eur_per_tco2": req.carbon_price_eur_per_tco2,
            "stranded_now_count": result["stranded_now"],
            "stranded_by_2030_count": result["stranded_by_2030"],
            "stranded_by_2040_count": result["stranded_by_2040"],
            "portfolio_stranding_risk_pct": _decimal_to_float(result["stranding_risk_pct"]),
            "avg_years_to_stranding": _decimal_to_float(result["avg_years_to_stranding"]) if result["avg_years_to_stranding"] else None,
            "total_annual_carbon_cost_eur": _decimal_to_float(result["total_carbon_cost"]),
            "property_results": [
                {
                    "property_id": c.property_id,
                    "property_name": c.property_name,
                    "property_type": c.property_type,
                    "country_iso": c.country_iso,
                    "energy_intensity_kwh_m2": _decimal_to_float(c.energy_intensity_kwh_m2),
                    "pathway_threshold_current_kwh_m2": _decimal_to_float(c.pathway_threshold_current_kwh_m2) if c.pathway_threshold_current_kwh_m2 else None,
                    "stranding_year_1_5c": c.stranding_year_1_5c,
                    "stranding_year_2c": c.stranding_year_2c,
                    "years_to_stranding_1_5c": c.years_to_stranding_1_5c,
                    "is_already_stranded": c.is_already_stranded,
                    "gap_to_pathway_pct": _decimal_to_float(c.gap_to_pathway_pct),
                    "annual_reduction_required_pct": _decimal_to_float(c.annual_reduction_required_pct),
                    "carbon_cost_annual_eur": _decimal_to_float(c.carbon_cost_annual_eur),
                }
                for c in result["property_results"]
            ],
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/epc", summary="EPC distribution + MEPS compliance analysis")
async def epc_analysis(req: EPCRequest):
    """EPC distribution by count/GAV and MEPS compliance for 2030/2033."""
    try:
        props = [_to_property_asset(p) for p in req.properties]
        epc_dist = engine._calculate_epc_distribution(props)
        meps = engine._calculate_meps_compliance(props)
        green_brown = engine._calculate_green_brown_split(props)

        return {
            "epc_distribution": [
                {
                    "rating": e.rating,
                    "property_count": e.property_count,
                    "property_pct": _decimal_to_float(e.property_pct),
                    "gav_total": _decimal_to_float(e.gav_total),
                    "gav_pct": _decimal_to_float(e.gav_pct),
                    "avg_energy_intensity": _decimal_to_float(e.avg_energy_intensity),
                }
                for e in epc_dist
            ],
            "green_property_count": green_brown["green_count"],
            "brown_property_count": green_brown["brown_count"],
            "green_pct_by_gav": _decimal_to_float(green_brown["green_pct_gav"]),
            "brown_pct_by_gav": _decimal_to_float(green_brown["brown_pct_gav"]),
            "meps_compliant_2030_count": meps["compliant_2030_count"],
            "meps_compliant_2030_pct": _decimal_to_float(meps["compliant_2030_pct"]),
            "meps_compliant_2033_count": meps["compliant_2033_count"],
            "meps_compliant_2033_pct": _decimal_to_float(meps["compliant_2033_pct"]),
            "meps_non_compliant_2030": [
                {
                    "property_id": m.property_id,
                    "property_name": m.property_name,
                    "country_iso": m.country_iso,
                    "current_epc": m.current_epc,
                    "minimum_epc_2030": m.minimum_epc_2030,
                    "gap_bands_to_2030": m.gap_bands_to_2030,
                }
                for m in meps["non_compliant_2030"]
            ],
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/concentration", summary="Sector + geographic concentration analysis")
async def concentration_analysis(req: ConcentrationRequest):
    """Concentration analysis by property type and country."""
    try:
        props = [_to_property_asset(p) for p in req.properties]
        gav = sum((p.market_value for p in props), Decimal("0"))
        sector = engine._calculate_sector_concentration(props, gav)
        geo = engine._calculate_geographic_concentration(props, gav)

        return {
            "sector_concentration": [
                {
                    "property_type": s.property_type,
                    "property_count": s.property_count,
                    "property_pct": _decimal_to_float(s.property_pct),
                    "gav_total": _decimal_to_float(s.gav_total),
                    "gav_pct": _decimal_to_float(s.gav_pct),
                    "avg_cap_rate": _decimal_to_float(s.avg_cap_rate),
                    "avg_occupancy": _decimal_to_float(s.avg_occupancy),
                    "avg_energy_intensity": _decimal_to_float(s.avg_energy_intensity),
                    "avg_carbon_intensity": _decimal_to_float(s.avg_carbon_intensity),
                }
                for s in sector
            ],
            "geographic_concentration": [
                {
                    "country_iso": g.country_iso,
                    "property_count": g.property_count,
                    "property_pct": _decimal_to_float(g.property_pct),
                    "gav_total": _decimal_to_float(g.gav_total),
                    "gav_pct": _decimal_to_float(g.gav_pct),
                    "avg_energy_intensity": _decimal_to_float(g.avg_energy_intensity),
                    "avg_carbon_intensity": _decimal_to_float(g.avg_carbon_intensity),
                }
                for g in geo
            ],
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/carbon", summary="Portfolio carbon metrics")
async def carbon_metrics(req: CarbonRequest):
    """Portfolio-level carbon intensity and total emissions."""
    try:
        props = [_to_property_asset(p) for p in req.properties]
        result = engine._calculate_carbon_metrics(props)
        return {
            "portfolio_carbon_intensity_kgco2_m2": _decimal_to_float(result["intensity"]),
            "total_emissions_tco2e": _decimal_to_float(result["total_emissions"]),
            "total_floor_area_m2": _decimal_to_float(result["total_area"]),
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/meps-timelines", summary="Available MEPS regulatory timelines by country")
async def get_meps_timelines():
    """Returns all MEPS regulatory timelines by country."""
    return {"timelines": MEPS_TIMELINES}


@router.get("/crrem-pathways", summary="Available CRREM pathway metadata")
async def get_crrem_pathways():
    """Returns metadata about available CRREM pathways (property types, countries, scenarios)."""
    metadata = {}
    for ptype, countries in CRREM_PATHWAYS.items():
        metadata[ptype] = {
            "countries": list(countries.keys()),
            "scenarios": list(next(iter(countries.values())).keys()) if countries else [],
        }
    return {"pathways": metadata}
