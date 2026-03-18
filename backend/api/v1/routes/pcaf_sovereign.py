"""
API Routes: PCAF Sovereign Bonds and Loans Engine
===================================================
POST /api/v1/pcaf-sovereign/assess             — Single country sovereign assessment
POST /api/v1/pcaf-sovereign/portfolio          — Portfolio-level sovereign assessment
POST /api/v1/pcaf-sovereign/attribution        — Attribution calculation only
GET  /api/v1/pcaf-sovereign/ref/country-profiles    — 40-country sovereign profiles
GET  /api/v1/pcaf-sovereign/ref/dqs-methodology     — PCAF DQS 1-4 methodology
GET  /api/v1/pcaf-sovereign/ref/ndc-alignment       — NDC alignment thresholds
GET  /api/v1/pcaf-sovereign/ref/attribution-formula — Attribution formula documentation
GET  /api/v1/pcaf-sovereign/ref/pcaf-part-d         — PCAF Part D standard overview
"""
from __future__ import annotations

import dataclasses
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.pcaf_sovereign_engine import get_engine

router = APIRouter(prefix="/api/v1/pcaf-sovereign", tags=["PCAF Sovereign Bonds"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class PCAFSovereignAssessRequest(BaseModel):
    entity_id: str
    entity_name: str
    country_code: str
    outstanding_amount_mn: float = Field(..., gt=0, description="Outstanding amount in USD millions")
    use_lulucf_adjustment: bool = False


class SovereignHoldingItem(BaseModel):
    country_code: str
    outstanding_amount_mn: float = Field(0.0, ge=0)
    entity_name: Optional[str] = None
    use_lulucf_adjustment: bool = False


class PCAFSovereignPortfolioRequest(BaseModel):
    entity_id: str
    sovereign_holdings: list[SovereignHoldingItem] = []


class AttributionCalcRequest(BaseModel):
    outstanding_mn: float = Field(..., gt=0, description="Outstanding amount in USD millions")
    government_debt_bn: float = Field(..., gt=0, description="Government debt in USD billions")
    ghg_inventory_tco2e: float = Field(..., gt=0, description="Sovereign GHG inventory in tCO2e")


# ---------------------------------------------------------------------------
# Assessment Endpoints
# ---------------------------------------------------------------------------

@router.post("/assess")
def assess_sovereign(req: PCAFSovereignAssessRequest):
    """PCAF Part D sovereign assessment for a single country bond/loan holding."""
    try:
        engine = get_engine()
        result = engine.assess(
            entity_id=req.entity_id,
            entity_name=req.entity_name,
            country_code=req.country_code.upper(),
            outstanding_amount_mn=req.outstanding_amount_mn,
            use_lulucf_adjustment=req.use_lulucf_adjustment,
        )
        return {"status": "ok", "result": dataclasses.asdict(result)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/portfolio")
def assess_portfolio(req: PCAFSovereignPortfolioRequest):
    """Portfolio-level PCAF sovereign assessment with exposure-weighted aggregation across multiple countries."""
    try:
        engine = get_engine()
        holdings = [
            {
                "country_code": h.country_code.upper(),
                "outstanding_amount_mn": h.outstanding_amount_mn,
                "entity_name": h.entity_name or req.entity_id,
                "use_lulucf_adjustment": h.use_lulucf_adjustment,
            }
            for h in req.sovereign_holdings
        ]
        result = engine.assess_portfolio(
            entity_id=req.entity_id,
            sovereign_holdings=holdings,
        )
        return {"status": "ok", "result": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/attribution")
def attribution_calculation(req: AttributionCalcRequest):
    """Isolated PCAF Part D attribution calculation — outstanding / government_debt x GHG_inventory."""
    try:
        engine = get_engine()
        result = engine.calculate_attribution(
            outstanding_mn=req.outstanding_mn,
            government_debt_bn=req.government_debt_bn,
            ghg_inventory_tco2e=req.ghg_inventory_tco2e,
        )
        return {"status": "ok", "result": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Reference Data Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/country-profiles")
def ref_country_profiles():
    """40-country sovereign profiles — GDP, government debt, GHG inventory, NDC targets, credit ratings."""
    try:
        return {"status": "ok", "result": get_engine().ref_country_profiles()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/dqs-methodology")
def ref_dqs_methodology():
    """PCAF Data Quality Score (DQS) 1-4 methodology for sovereign GHG data."""
    try:
        return {"status": "ok", "result": get_engine().ref_dqs_methodology()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/ndc-alignment")
def ref_ndc_alignment():
    """NDC alignment thresholds — aligned / partial / misaligned criteria and portfolio actions."""
    try:
        return {"status": "ok", "result": get_engine().ref_ndc_alignment()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/attribution-formula")
def ref_attribution_formula():
    """PCAF Part D attribution formula documentation with units and methodology notes."""
    try:
        return {"status": "ok", "result": get_engine().ref_attribution_formula()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/pcaf-part-d")
def ref_pcaf_part_d():
    """PCAF Global GHG Standard Part D overview — asset classes, methodology, integration with other Parts."""
    try:
        return {"status": "ok", "result": get_engine().ref_pcaf_part_d()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
