"""
API Routes: RICS Red Book ESG Compliance
==========================================
POST /api/v1/rics-esg/compliance       — Full RICS ESG compliance assessment
GET  /api/v1/rics-esg/checklist        — RICS ESG checklist templates
GET  /api/v1/rics-esg/materiality      — ESG materiality factor catalogue
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from services.rics_esg_engine import RICSESGEngine, RICSComplianceInput

router = APIRouter(prefix="/api/v1/rics-esg", tags=["RICS Red Book ESG"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class RICSComplianceRequest(BaseModel):
    property_id: str
    property_type: str = "office"
    country: str = "GB"
    valuation_purpose: str = Field("market_value", pattern=r"^(market_value|fair_value|investment_value)$")
    epc_rating: Optional[str] = None
    epc_score: Optional[float] = None
    green_certification: Optional[str] = None
    green_cert_level: Optional[str] = None
    energy_kwh_m2_yr: Optional[float] = None
    scope12_tco2e: Optional[float] = None
    crrem_stranding_year: Optional[int] = None
    flood_risk_zone: Optional[str] = None
    heat_risk_score: Optional[float] = Field(None, ge=0, le=100)
    biodiversity_proximity: bool = False
    indoor_air_quality: Optional[str] = None
    accessibility_compliant: bool = True
    iso14001_certified: bool = False
    gresb_score: Optional[float] = Field(None, ge=0, le=100)
    green_premium_pct: Optional[float] = None
    brown_discount_pct: Optional[float] = None
    transition_risk_adjustment_pct: Optional[float] = None
    physical_risk_adjustment_pct: Optional[float] = None
    num_esg_comparables: int = Field(0, ge=0)
    comparable_evidence_quality: str = Field("limited", pattern=r"^(strong|moderate|limited|none)$")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/compliance")
def assess_compliance(req: RICSComplianceRequest):
    """Full RICS Red Book ESG compliance assessment with narrative and uncertainty."""
    engine = RICSESGEngine()
    inp = RICSComplianceInput(
        property_id=req.property_id,
        property_type=req.property_type,
        country=req.country,
        valuation_purpose=req.valuation_purpose,
        epc_rating=req.epc_rating,
        epc_score=req.epc_score,
        green_certification=req.green_certification,
        green_cert_level=req.green_cert_level,
        energy_kwh_m2_yr=req.energy_kwh_m2_yr,
        scope12_tco2e=req.scope12_tco2e,
        crrem_stranding_year=req.crrem_stranding_year,
        flood_risk_zone=req.flood_risk_zone,
        heat_risk_score=req.heat_risk_score,
        biodiversity_proximity=req.biodiversity_proximity,
        indoor_air_quality=req.indoor_air_quality,
        accessibility_compliant=req.accessibility_compliant,
        iso14001_certified=req.iso14001_certified,
        gresb_score=req.gresb_score,
        green_premium_pct=req.green_premium_pct,
        brown_discount_pct=req.brown_discount_pct,
        transition_risk_adjustment_pct=req.transition_risk_adjustment_pct,
        physical_risk_adjustment_pct=req.physical_risk_adjustment_pct,
        num_esg_comparables=req.num_esg_comparables,
        comparable_evidence_quality=req.comparable_evidence_quality,
    )
    r = engine.assess_compliance(inp)
    return {
        "property_id": r.property_id,
        "total_items": r.total_items,
        "compliant_count": r.compliant_count,
        "partial_count": r.partial_count,
        "non_compliant_count": r.non_compliant_count,
        "not_assessed_count": r.not_assessed_count,
        "compliance_pct": r.compliance_pct,
        "compliance_band": r.compliance_band,
        "checklist": r.checklist,
        "esg_narrative": r.esg_narrative,
        "materiality_scores": r.materiality_scores,
        "material_factors": r.material_factors,
        "uncertainty_pct": r.uncertainty_pct,
        "uncertainty_band": r.uncertainty_band,
        "uncertainty_narrative": r.uncertainty_narrative,
        "recommendations": r.recommendations,
    }


@router.get("/checklist")
def get_checklist():
    """Return all RICS ESG checklist templates (PS1, PS2, VPS4, VPGA12, VPG3, IVS)."""
    return RICSESGEngine().get_full_checklist()


@router.get("/materiality")
def get_materiality_factors():
    """Return ESG materiality factor catalogue (Environmental, Social, Governance)."""
    return RICSESGEngine().get_materiality_factors()
