"""
API Routes: GRI Standards Reporting Engine
===========================================
POST /api/v1/gri-standards/assess                      — Full GRI report assessment
POST /api/v1/gri-standards/generate-content-index      — Generate GRI Content Index
POST /api/v1/gri-standards/materiality-screen          — Screen and prioritise material topics
GET  /api/v1/gri-standards/ref/gri-2-disclosures       — GRI 2 General Disclosures reference
GET  /api/v1/gri-standards/ref/gri-300-standards       — GRI 300 Environmental Standards reference
GET  /api/v1/gri-standards/ref/material-topic-process  — GRI 3 four-step materiality process
GET  /api/v1/gri-standards/ref/service-levels          — GRI service level definitions
GET  /api/v1/gri-standards/ref/content-index-requirements — Content index requirements
"""
from __future__ import annotations

import dataclasses
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.gri_standards_engine import get_engine

router = APIRouter(prefix="/api/v1/gri-standards", tags=["GRI Standards"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class GRIAssessRequest(BaseModel):
    entity_id: str
    entity_name: str
    reporting_period: str = "2024"
    material_topics: Optional[list[str]] = None
    gri_2_disclosures_submitted: Optional[list[str]] = None
    gri_300_data: Optional[dict] = None


class ContentIndexRequest(BaseModel):
    entity_id: str
    material_topics: Optional[list[str]] = None
    disclosures_status: Optional[dict] = None


class MaterialityScreenRequest(BaseModel):
    entity_id: str
    sector: str = "financials"
    stakeholder_inputs: Optional[list[str]] = None


# ---------------------------------------------------------------------------
# Assessment Endpoints
# ---------------------------------------------------------------------------

@router.post("/assess")
def assess_gri(req: GRIAssessRequest):
    """Full GRI Standards compliance assessment — GRI 2 completeness + GRI 300 material topic coverage."""
    try:
        engine = get_engine()
        result = engine.assess(
            entity_id=req.entity_id,
            entity_name=req.entity_name,
            reporting_period=req.reporting_period,
            material_topics=req.material_topics,
            gri_2_disclosures_submitted=req.gri_2_disclosures_submitted,
            gri_300_data=req.gri_300_data,
        )
        return {"status": "ok", "result": dataclasses.asdict(result)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/generate-content-index")
def generate_content_index(req: ContentIndexRequest):
    """Generate machine-readable GRI Content Index per GRI 101:2023 requirements."""
    try:
        engine = get_engine()
        result = engine.generate_content_index(
            entity_id=req.entity_id,
            material_topics=req.material_topics,
            disclosures_status=req.disclosures_status,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/materiality-screen")
def materiality_screen(req: MaterialityScreenRequest):
    """Screen GRI 300 topics using double materiality lens (impact + financial materiality)."""
    try:
        engine = get_engine()
        result = engine.screen_material_topics(
            entity_id=req.entity_id,
            sector=req.sector,
            stakeholder_inputs=req.stakeholder_inputs,
        )
        return {"status": "ok", "result": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Reference Data Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/gri-2-disclosures")
def ref_gri_2_disclosures():
    """All 30 GRI 2 General Disclosures (2021) with descriptions and guidance notes."""
    try:
        return {"status": "ok", "result": get_engine().ref_gri_2_disclosures()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/gri-300-standards")
def ref_gri_300_standards():
    """GRI 300 Environmental Standards (GRI 301-308) with all disclosure definitions."""
    try:
        return {"status": "ok", "result": get_engine().ref_gri_300_standards()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/material-topic-process")
def ref_material_topic_process():
    """GRI 3 Material Topics 2021 — four-step double materiality process."""
    try:
        return {"status": "ok", "result": get_engine().ref_material_topic_process()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/service-levels")
def ref_service_levels():
    """GRI service level definitions — with_reference (current) / core / comprehensive (legacy)."""
    try:
        return {"status": "ok", "result": get_engine().ref_service_levels()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/content-index-requirements")
def ref_content_index_requirements():
    """GRI Content Index requirements per GRI 1 Foundation 2021, Requirement 7."""
    try:
        return {"status": "ok", "result": get_engine().ref_content_index_requirements()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
