"""
CSRD ESRS E2-E5 API routes.
Prefix: /api/v1/esrs-e2-e5
Tags: CSRD ESRS E2-E5
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.esrs_e2_e5_engine import get_engine

router = APIRouter(prefix="/api/v1/esrs-e2-e5", tags=["CSRD ESRS E2-E5"])


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class AssessRequest(BaseModel):
    entity_id: str
    entity_name: str
    reporting_period: str = Field(..., example="2024")
    nace_sector: str = Field(..., example="C20")
    e2_data: Optional[dict[str, Any]] = None
    e3_data: Optional[dict[str, Any]] = None
    e4_data: Optional[dict[str, Any]] = None
    e5_data: Optional[dict[str, Any]] = None


class AssessMaterialityRequest(BaseModel):
    entity_id: str
    nace_sector: str = Field(..., example="C20")


class AssessE2Request(BaseModel):
    entity_id: str
    pollution_data: dict[str, Any] = Field(default_factory=dict)


class AssessE3Request(BaseModel):
    entity_id: str
    water_data: dict[str, Any] = Field(default_factory=dict)


class AssessE4Request(BaseModel):
    entity_id: str
    biodiversity_data: dict[str, Any] = Field(default_factory=dict)


class AssessE5Request(BaseModel):
    entity_id: str
    circular_data: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# POST endpoints
# ---------------------------------------------------------------------------

@router.post("/assess")
def assess(req: AssessRequest) -> dict:
    """Full ESRS E2-E5 assessment for an entity across all four environment topics."""
    try:
        engine = get_engine()
        result = engine.assess(
            entity_id=req.entity_id,
            entity_name=req.entity_name,
            reporting_period=req.reporting_period,
            nace_sector=req.nace_sector,
            e2_data=req.e2_data,
            e3_data=req.e3_data,
            e4_data=req.e4_data,
            e5_data=req.e5_data,
        )
        return asdict(result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/assess-materiality")
def assess_materiality(req: AssessMaterialityRequest) -> dict:
    """Determine which ESRS E2-E5 topics are material for a given NACE sector."""
    try:
        engine = get_engine()
        return engine.assess_materiality(entity_id=req.entity_id, nace_sector=req.nace_sector)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/assess-e2")
def assess_e2(req: AssessE2Request) -> dict:
    """ESRS E2 Pollution topic assessment — air, water and soil emissions."""
    try:
        engine = get_engine()
        return engine.assess_e2_pollution(entity_id=req.entity_id, pollution_data=req.pollution_data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/assess-e3")
def assess_e3(req: AssessE3Request) -> dict:
    """ESRS E3 Water & Marine Resources assessment — withdrawal, discharge, consumption."""
    try:
        engine = get_engine()
        return engine.assess_e3_water(entity_id=req.entity_id, water_data=req.water_data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/assess-e4")
def assess_e4(req: AssessE4Request) -> dict:
    """ESRS E4 Biodiversity & Ecosystems assessment — land use, species, ecosystem services."""
    try:
        engine = get_engine()
        return engine.assess_e4_biodiversity(entity_id=req.entity_id, biodiversity_data=req.biodiversity_data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/assess-e5")
def assess_e5(req: AssessE5Request) -> dict:
    """ESRS E5 Circular Economy assessment — resource inflows, waste outflows, circularity score."""
    try:
        engine = get_engine()
        return engine.assess_e5_circular(entity_id=req.entity_id, circular_data=req.circular_data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# GET reference endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/e2-disclosures")
def ref_e2_disclosures() -> dict:
    """Reference: ESRS E2 disclosure requirements (E2-1 to E2-6) with pollutant lists."""
    try:
        return get_engine().ref_e2_disclosures()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/e3-disclosures")
def ref_e3_disclosures() -> dict:
    """Reference: ESRS E3 disclosure requirements (E3-1 to E3-5) with water stress tiers."""
    try:
        return get_engine().ref_e3_disclosures()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/e4-disclosures")
def ref_e4_disclosures() -> dict:
    """Reference: ESRS E4 disclosure requirements (E4-1 to E4-6) with ENCORE categories."""
    try:
        return get_engine().ref_e4_disclosures()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/e5-disclosures")
def ref_e5_disclosures() -> dict:
    """Reference: ESRS E5 disclosure requirements (E5-1 to E5-6) with waste hierarchy."""
    try:
        return get_engine().ref_e5_disclosures()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/materiality-triggers")
def ref_materiality_triggers() -> dict:
    """Reference: Sector-based ESRS E2-E5 materiality default triggers by NACE division."""
    try:
        return get_engine().ref_materiality_triggers()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
