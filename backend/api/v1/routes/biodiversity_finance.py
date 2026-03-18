"""Biodiversity Finance Metrics — E23 routes"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Optional
from services.biodiversity_finance_engine import get_engine

router = APIRouter(prefix="/api/v1/biodiversity-finance", tags=["Biodiversity Finance"])
engine = get_engine()


class AssessRequest(BaseModel):
    entity_id: str
    entity_name: str
    sector: str
    assessment_type: str = "combined"
    operational_area_km2: Optional[float] = None
    land_use_breakdown: Optional[dict[str, float]] = None


class MSARequest(BaseModel):
    entity_id: str
    land_use_areas: dict[str, float]


@router.post("/assess")
def assess(req: AssessRequest):
    try:
        import dataclasses
        result = engine.assess(
            entity_id=req.entity_id,
            entity_name=req.entity_name,
            sector=req.sector,
            assessment_type=req.assessment_type,
            operational_area_km2=req.operational_area_km2,
            land_use_breakdown=req.land_use_breakdown,
        )
        return {"status": "ok", "assessment": dataclasses.asdict(result)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/msa-footprint")
def msa_footprint(req: MSARequest):
    try:
        import dataclasses
        result = engine.calculate_msa_footprint(
            entity_id=req.entity_id,
            land_use_areas=req.land_use_areas,
        )
        return {"status": "ok", "msa_footprint": dataclasses.asdict(result)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/tnfd-pillars")
def ref_tnfd_pillars():
    return engine.ref_tnfd_pillars()


@router.get("/ref/land-use-msa")
def ref_land_use_msa():
    return engine.ref_land_use_msa()


@router.get("/ref/sbtn-steps")
def ref_sbtn_steps():
    return engine.ref_sbtn_steps()


@router.get("/ref/cbd-gbf-target15")
def ref_cbd_gbf_target15():
    return engine.ref_cbd_gbf_target15()


@router.get("/ref/encore-services")
def ref_encore_services():
    return {"services": engine.ref_encore_services()}


@router.get("/ref/assessment-types")
def ref_assessment_types():
    from services.biodiversity_finance_engine import ASSESSMENT_TYPES
    return {
        "types": ASSESSMENT_TYPES,
        "descriptions": {
            "tnfd": "TNFD v1.0 14-metric disclosure framework",
            "msa": "Mean Species Abundance footprint calculation",
            "sbtn": "Science Based Targets for Nature (SBTN) steps 1-5 readiness",
            "cbd_gbf": "CBD Global Biodiversity Framework Target 15 sub-elements",
            "combined": "Full multi-framework biodiversity finance assessment",
        },
    }


@router.get("/ref/pbaf-standard")
def ref_pbaf_standard():
    return {
        "standard": "PBAF (Partnership for Biodiversity Accounting Financials) 2023",
        "scope": "Biodiversity impact assessment for financial institutions",
        "methods": ["MSA footprint", "ENCORE dependencies", "Species threat score"],
        "asset_classes": ["listed_equity", "bonds", "project_finance", "real_estate", "loans"],
        "alignment_with": ["TNFD", "SBTN", "CBD GBF", "CSRD ESRS E4", "EU Taxonomy DNSH"],
    }
