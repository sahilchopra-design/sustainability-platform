"""
SFDR PAI Calculation Engine — EU Sustainable Finance Disclosure Regulation
Routes for PAI calculation, DNSH assessment, disclosure generation,
entity classification, and benchmarking.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

router = APIRouter(prefix="/api/v1/sfdr-pai", tags=["SFDR PAI"])

# ── Lazy engine singleton ────────────────────────────────────────────────────

_engine = None

def _get_engine():
    global _engine
    if _engine is None:
        from services.sfdr_pai_engine import SFDRPAIEngine
        _engine = SFDRPAIEngine()
    return _engine


# ── Request models ───────────────────────────────────────────────────────────

class Holding(BaseModel):
    name: str = ""
    isin: str = ""
    sector: str = ""
    country: str = ""
    weight: float = 0.0
    market_value: float = 0.0
    scope1_emissions: float = 0.0
    scope2_emissions: float = 0.0
    scope3_emissions: float = 0.0
    revenue: float = 0.0
    employees: int = 0
    energy_consumption_gwh: float = 0.0
    renewable_share: float = 0.0
    biodiversity_sensitive: bool = False
    emissions_to_water_tonnes: float = 0.0
    hazardous_waste_tonnes: float = 0.0
    ungc_violations: bool = False
    ungc_compliance_mechanism: bool = True
    gender_pay_gap_pct: float = 0.0
    board_female_pct: float = 0.0
    controversial_weapons: bool = False
    fossil_fuel_active: bool = False
    nace_code: str = ""
    epc_rating: str = ""
    asset_class: str = "company"

class CalculatePAIRequest(BaseModel):
    portfolio_holdings: List[Holding]
    pai_indicator_id: str = Field(..., description="e.g. PAI_1, PAI_2, ... PAI_18")

class CalculateAllPAIsRequest(BaseModel):
    portfolio_holdings: List[Holding]

class CalculateAdditionalPAIsRequest(BaseModel):
    portfolio_holdings: List[Holding]
    selected_indicators: List[str] = Field(default_factory=list)

class DNSHRequest(BaseModel):
    holding: Holding
    taxonomy_objective: str = Field(..., description="climate_mitigation, climate_adaptation, water, circular_economy, pollution, biodiversity")

class PAIStatementRequest(BaseModel):
    portfolio_holdings: List[Holding]
    reporting_period: str = Field(..., description="e.g. 2025-Q4, 2025-FY")

class ComparePeriodRequest(BaseModel):
    current_pais: dict
    previous_pais: dict

class ClassifyEntityRequest(BaseModel):
    entity_name: str
    sustainability_objective: bool = False
    promotes_esg: bool = False
    minimum_sustainable_investment_pct: float = 0.0
    taxonomy_alignment_pct: float = 0.0
    pai_consideration: bool = False
    exclusion_criteria: List[str] = Field(default_factory=list)

class BenchmarkRequest(BaseModel):
    pai_values: dict
    peer_group: str = "all"


# ── Calculation endpoints ─────────────────────────────────────────────────────

@router.post("/calculate")
async def calculate_pai(req: CalculatePAIRequest):
    """Calculate a single PAI indicator for a portfolio."""
    try:
        engine = _get_engine()
        holdings = [h.dict() for h in req.portfolio_holdings]
        return engine.calculate_pai(holdings, req.pai_indicator_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate-all")
async def calculate_all_mandatory(req: CalculateAllPAIsRequest):
    """Calculate all 18 mandatory PAI indicators for a portfolio."""
    try:
        engine = _get_engine()
        holdings = [h.dict() for h in req.portfolio_holdings]
        return engine.calculate_all_mandatory_pais(holdings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate-additional")
async def calculate_additional(req: CalculateAdditionalPAIsRequest):
    """Calculate selected additional (optional) PAI indicators."""
    try:
        engine = _get_engine()
        holdings = [h.dict() for h in req.portfolio_holdings]
        return engine.calculate_additional_pais(holdings, req.selected_indicators)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dnsh")
async def assess_dnsh(req: DNSHRequest):
    """Do No Significant Harm assessment per PAI indicator."""
    try:
        engine = _get_engine()
        return engine.assess_do_no_significant_harm(req.holding.dict(), req.taxonomy_objective)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pai-statement")
async def generate_pai_statement(req: PAIStatementRequest):
    """Generate full PAI statement for Article 4 disclosure."""
    try:
        engine = _get_engine()
        holdings = [h.dict() for h in req.portfolio_holdings]
        return engine.calculate_portfolio_pai_statement(holdings, req.reporting_period)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare-periods")
async def compare_reporting_periods(req: ComparePeriodRequest):
    """Compare PAI values across reporting periods."""
    try:
        engine = _get_engine()
        return engine.compare_reporting_periods(req.current_pais, req.previous_pais)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/classify-entity")
async def classify_entity(req: ClassifyEntityRequest):
    """Classify fund/product as SFDR Article 6, 8, or 9."""
    try:
        engine = _get_engine()
        return engine.classify_entity(req.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/benchmark")
async def benchmark_against_peers(req: BenchmarkRequest):
    """Benchmark PAI values against peer group averages."""
    try:
        engine = _get_engine()
        return engine.benchmark_against_peers(req.pai_values, req.peer_group)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/data-coverage")
async def assess_data_coverage(req: CalculateAllPAIsRequest):
    """Assess data availability and quality for PAI calculation."""
    try:
        engine = _get_engine()
        holdings = [h.dict() for h in req.portfolio_holdings]
        return engine.assess_data_coverage(holdings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Reference endpoints ───────────────────────────────────────────────────────

@router.get("/ref/mandatory-indicators")
async def ref_mandatory_indicators():
    engine = _get_engine()
    return engine.get_mandatory_indicators()

@router.get("/ref/additional-indicators")
async def ref_additional_indicators():
    engine = _get_engine()
    return engine.get_additional_indicators()

@router.get("/ref/calculation-methods")
async def ref_calculation_methods():
    engine = _get_engine()
    return engine.get_calculation_methods()

@router.get("/ref/entity-classifications")
async def ref_entity_classifications():
    engine = _get_engine()
    return engine.get_entity_classifications()

@router.get("/ref/disclosure-requirements")
async def ref_disclosure_requirements():
    engine = _get_engine()
    return engine.get_disclosure_requirements()

@router.get("/ref/sector-benchmarks")
async def ref_sector_benchmarks():
    engine = _get_engine()
    return engine.get_sector_benchmarks()
