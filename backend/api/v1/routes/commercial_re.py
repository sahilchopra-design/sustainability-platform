"""
API Routes: Commercial Real Estate Climate Engine
==================================================
POST /api/v1/commercial-re/crrem          — CRREM 2.0 stranding assessment
POST /api/v1/commercial-re/epc-epbd       — EPC rating and EPBD 2024 compliance
POST /api/v1/commercial-re/gresb          — GRESB Real Estate scoring
POST /api/v1/commercial-re/refi           — REFI Protocol risk scoring
POST /api/v1/commercial-re/nabers         — NABERS energy star rating
POST /api/v1/commercial-re/green-lease    — Green lease clause assessment
POST /api/v1/commercial-re/retrofit       — Retrofit NPV/IRR modelling
POST /api/v1/commercial-re/full-assessment — Complete RE assessment
GET  /api/v1/commercial-re/ref/crrem-pathways   — CRREM 2.0 pathways by asset type
GET  /api/v1/commercial-re/ref/epc-thresholds   — EPC rating thresholds by country
GET  /api/v1/commercial-re/ref/retrofit-measures — Available retrofit measures
GET  /api/v1/commercial-re/ref/green-premium     — Green premium evidence by market
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

try:
    from services.commercial_re_engine import (
        CommercialREEngine,
        CRREM_PATHWAYS,
        EPC_THRESHOLDS,
        RETROFIT_MEASURES,
        GREEN_PREMIUM_EVIDENCE,
        EPBD_2024_REQUIREMENTS,
        GRESB_SCORING,
        GREEN_LEASE_CLAUSES,
        NABERS_BENCHMARKS,
    )
    _engine = CommercialREEngine()
except Exception:
    _engine = None
    CRREM_PATHWAYS = {}
    EPC_THRESHOLDS = {}
    RETROFIT_MEASURES = {}
    GREEN_PREMIUM_EVIDENCE = {}
    EPBD_2024_REQUIREMENTS = {}
    GRESB_SCORING = {}
    GREEN_LEASE_CLAUSES = []
    NABERS_BENCHMARKS = {}

router = APIRouter(prefix="/api/v1/commercial-re", tags=["Commercial Real Estate"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class CRREMRequest(BaseModel):
    entity_id: str
    asset_type: str = "office"
    country: str = "UK"
    energy_intensity_kwh_m2: float = Field(180.0, gt=0)
    co2_intensity_kgco2_m2: float = Field(35.0, gt=0)

    class Config:
        extra = "allow"


class EPCRequest(BaseModel):
    entity_id: str
    country: str = "UK"
    building_type: str = "commercial"
    primary_energy_kwh_m2: float = Field(150.0, gt=0)

    class Config:
        extra = "allow"


class GRESBRequest(BaseModel):
    entity_id: str
    management_data: dict = {}
    performance_data: dict = {}

    class Config:
        extra = "allow"


class REFIRequest(BaseModel):
    entity_id: str
    physical_risk_inputs: dict = {}
    transition_risk_inputs: dict = {}

    class Config:
        extra = "allow"


class NABERSRequest(BaseModel):
    entity_id: str
    asset_type: str = "office"
    annual_energy_kwh: float = Field(900_000.0, gt=0)
    gross_area_m2: float = Field(5000.0, gt=0)
    hours_pa: float = Field(2500.0, gt=0)

    class Config:
        extra = "allow"


class GreenLeaseRequest(BaseModel):
    entity_id: str
    lease_clauses_present: list[str] = []

    class Config:
        extra = "allow"


class RetrofitRequest(BaseModel):
    entity_id: str
    asset_type: str = "office"
    current_energy_kwh_m2: float = Field(180.0, gt=0)
    floor_area_m2: float = Field(5000.0, gt=0)
    discount_rate: float = Field(0.07, gt=0, lt=1)
    energy_price_kwh: float = Field(0.20, gt=0)

    class Config:
        extra = "allow"


class FullAssessmentRequest(BaseModel):
    entity_id: str
    asset_data: dict = {}

    class Config:
        extra = "allow"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _mock(entity_id: str, endpoint: str) -> dict:
    return {
        "status": "success",
        "data": {
            "entity_id": entity_id,
            "endpoint": endpoint,
            "note": "engine_unavailable_mock_response",
        },
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/crrem")
def crrem(req: CRREMRequest):
    """CRREM 2.0 stranding year and carbon pathway assessment."""
    if _engine is None:
        return _mock(req.entity_id, "crrem")
    r = _engine.assess_crrem(
        req.entity_id, req.asset_type, req.country,
        req.energy_intensity_kwh_m2, req.co2_intensity_kgco2_m2,
    )
    return {
        "status": "success",
        "data": {
            "entity_id": r.entity_id,
            "asset_type": r.asset_type,
            "country": r.country,
            "current_co2_kgco2_m2": r.current_co2_kgco2_m2,
            "stranding_year": r.stranding_year,
            "stranding_risk": r.stranding_risk,
            "overconsumption_gap": r.overconsumption_gap,
            "pathway_2030": r.pathway_2030,
            "pathway_2050": r.pathway_2050,
            "years_to_stranding": r.years_to_stranding,
        },
    }


@router.post("/epc-epbd")
def epc_epbd(req: EPCRequest):
    """EPC rating derivation and EPBD 2024 renovation obligation check."""
    if _engine is None:
        return _mock(req.entity_id, "epc-epbd")
    r = _engine.assess_epc_epbd(req.entity_id, req.country, req.building_type, req.primary_energy_kwh_m2)
    return {
        "status": "success",
        "data": {
            "entity_id": r.entity_id,
            "country": r.country,
            "building_type": r.building_type,
            "primary_energy_kwh_m2": r.primary_energy_kwh_m2,
            "epc_rating": r.epc_rating,
            "epbd_renovation_required": r.epbd_renovation_required,
            "minimum_threshold": r.minimum_threshold,
            "compliance_deadline": r.compliance_deadline,
            "current_meets_2030": r.current_meets_2030,
            "current_meets_2033": r.current_meets_2033,
        },
    }


@router.post("/gresb")
def gresb(req: GRESBRequest):
    """GRESB Real Estate Assessment — management + performance scoring (1-5 stars)."""
    if _engine is None:
        return _mock(req.entity_id, "gresb")
    r = _engine.calculate_gresb_score(req.entity_id, req.management_data, req.performance_data)
    return {
        "status": "success",
        "data": {
            "entity_id": r.entity_id,
            "management_score": r.management_score,
            "performance_score": r.performance_score,
            "total_score": r.total_score,
            "star_rating": r.star_rating,
            "peer_percentile": r.peer_percentile,
            "component_scores": r.component_scores,
        },
    }


@router.post("/refi")
def refi(req: REFIRequest):
    """REFI Protocol physical and transition risk tier scoring."""
    if _engine is None:
        return _mock(req.entity_id, "refi")
    r = _engine.assess_refi(req.entity_id, req.physical_risk_inputs, req.transition_risk_inputs)
    return {
        "status": "success",
        "data": {
            "entity_id": r.entity_id,
            "physical_score": r.physical_score,
            "transition_score": r.transition_score,
            "composite_score": r.composite_score,
            "risk_tier": r.risk_tier,
            "risk_label": r.risk_label,
        },
    }


@router.post("/nabers")
def nabers(req: NABERSRequest):
    """NABERS energy/water/indoor environment star rating (1-6 stars)."""
    if _engine is None:
        return _mock(req.entity_id, "nabers")
    r = _engine.calculate_nabers(
        req.entity_id, req.asset_type, req.annual_energy_kwh, req.gross_area_m2, req.hours_pa,
    )
    return {
        "status": "success",
        "data": {
            "entity_id": r.entity_id,
            "asset_type": r.asset_type,
            "annual_energy_kwh": r.annual_energy_kwh,
            "gross_area_m2": r.gross_area_m2,
            "energy_intensity_kwh_m2": r.energy_intensity_kwh_m2,
            "energy_stars": r.energy_stars,
            "water_stars": r.water_stars,
            "indoor_stars": r.indoor_stars,
        },
    }


@router.post("/green-lease")
def green_lease(req: GreenLeaseRequest):
    """Green lease clause assessment — score and grade (A-E)."""
    if _engine is None:
        return _mock(req.entity_id, "green-lease")
    r = _engine.assess_green_lease(req.entity_id, req.lease_clauses_present)
    return {
        "status": "success",
        "data": {
            "entity_id": r.entity_id,
            "clauses_present": r.clauses_present,
            "clauses_missing": r.clauses_missing,
            "score": r.score,
            "grade": r.grade,
            "total_weight_present": r.total_weight_present,
        },
    }


@router.post("/retrofit")
def retrofit(req: RetrofitRequest):
    """Retrofit NPV/IRR modelling for all 10 measure types, ranked by IRR."""
    if _engine is None:
        return _mock(req.entity_id, "retrofit")
    r = _engine.model_retrofit(
        req.entity_id, req.asset_type, req.current_energy_kwh_m2,
        req.floor_area_m2, req.discount_rate, req.energy_price_kwh,
    )
    return {
        "status": "success",
        "data": {
            "entity_id": r.entity_id,
            "measures": r.measures,
            "total_capex": r.total_capex,
            "total_energy_saving_kwh_pa": r.total_energy_saving_kwh_pa,
            "total_co2_saving_kgpa": r.total_co2_saving_kgpa,
            "crrem_year_improvement": r.crrem_year_improvement,
            "portfolio_irr_pct": r.portfolio_irr,
            "portfolio_npv": r.portfolio_npv,
        },
    }


@router.post("/full-assessment")
def full_assessment(req: FullAssessmentRequest):
    """Consolidated property assessment across all RE climate frameworks."""
    if _engine is None:
        return _mock(req.entity_id, "full-assessment")
    r = _engine.generate_full_assessment(req.entity_id, req.asset_data)
    return {"status": "success", "data": r}


# ---------------------------------------------------------------------------
# Reference Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/crrem-pathways")
def ref_crrem_pathways():
    """CRREM 2.0 carbon intensity pathways (kgCO2/m²/yr) by asset type and country."""
    return {"status": "success", "data": CRREM_PATHWAYS}


@router.get("/ref/epc-thresholds")
def ref_epc_thresholds():
    """EPC rating thresholds (kWh/m²/yr) by country and EPBD 2024 requirements."""
    return {
        "status": "success",
        "data": {
            "thresholds": EPC_THRESHOLDS,
            "epbd_requirements": EPBD_2024_REQUIREMENTS,
        },
    }


@router.get("/ref/retrofit-measures")
def ref_retrofit_measures():
    """Retrofit measure catalogue — CAPEX/m², energy saving %, CO2 saving %, lifetime."""
    return {
        "status": "success",
        "data": {
            "measures": RETROFIT_MEASURES,
            "green_lease_clauses": GREEN_LEASE_CLAUSES,
            "nabers_benchmarks": NABERS_BENCHMARKS,
        },
    }


@router.get("/ref/green-premium")
def ref_green_premium():
    """Green premium and brown discount evidence by country and asset type (JLL/CBRE)."""
    return {
        "status": "success",
        "data": {
            "green_premium_evidence": GREEN_PREMIUM_EVIDENCE,
            "gresb_scoring_weights": GRESB_SCORING,
        },
    }
