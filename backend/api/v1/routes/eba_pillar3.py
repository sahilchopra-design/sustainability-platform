"""EBA Pillar 3 ESG Disclosures — E20 routes"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Optional
from services.eba_pillar3_engine import get_engine

router = APIRouter(prefix="/api/v1/eba-pillar3", tags=["EBA Pillar 3 ESG"])
engine = get_engine()


class AssessRequest(BaseModel):
    entity_id: str
    entity_name: str
    institution_type: str = "G-SII"
    total_assets_bn: float
    templates_submitted: list[str] = []
    portfolio_data: Optional[dict[str, Any]] = None


class HeatmapRequest(BaseModel):
    entity_id: str
    portfolio_nace_exposure: dict[str, float]


@router.post("/assess")
def assess(req: AssessRequest):
    try:
        result = engine.assess(
            entity_id=req.entity_id,
            entity_name=req.entity_name,
            institution_type=req.institution_type,
            total_assets_bn=req.total_assets_bn,
            templates_submitted=req.templates_submitted,
            portfolio_data=req.portfolio_data,
        )
        return {"status": "ok", "assessment": result.__dict__}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/template-completeness")
def template_completeness(
    templates_submitted: list[str],
    institution_type: str = "G-SII",
):
    try:
        return engine.score_template_completeness(templates_submitted, institution_type)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/physical-risk-heatmap")
def physical_risk_heatmap(req: HeatmapRequest):
    try:
        result = engine.generate_physical_risk_heatmap(
            entity_id=req.entity_id,
            portfolio_nace_exposure=req.portfolio_nace_exposure,
        )
        return {"status": "ok", "heatmap": result.__dict__}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/templates")
def ref_templates():
    return engine.ref_templates()


@router.get("/ref/institution-types")
def ref_institution_types():
    return engine.ref_institution_types()


@router.get("/ref/nace-sectors")
def ref_nace_sectors():
    return engine.ref_nace_sectors()


@router.get("/ref/climate-hazards")
def ref_climate_hazards():
    return engine.ref_climate_hazards()


@router.get("/ref/regulatory-timeline")
def ref_regulatory_timeline():
    return {
        "regulation": "EBA GL/2022/03 + CRR Art 449a",
        "effective_date": "2022-06-28",
        "applies_to": "Large institutions (>EUR 30bn total assets)",
        "mandatory_templates_gsii": list(range(1, 11)),
        "mandatory_templates_osii": list(range(1, 9)),
        "reporting_frequency": "Annual (aligned to Pillar 3 report)",
        "t7_financed_emissions_from": "Jun-2023",
        "t9_t10_from": "Jun-2024",
    }
