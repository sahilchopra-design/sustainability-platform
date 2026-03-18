"""Scope 3 Categories Engine — E21 routes"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.scope3_categories_engine import get_engine

router = APIRouter(prefix="/api/v1/scope3-categories", tags=["Scope 3 Categories"])
engine = get_engine()


class AssessRequest(BaseModel):
    entity_id: str
    entity_name: str
    nace_code: str
    revenue_bn: float
    headcount: int = 0
    sector_type: str = "non_flag"
    portfolio_aum_bn: Optional[float] = None


class MaterialityRequest(BaseModel):
    nace_code: str
    revenue_bn: float


@router.post("/assess")
def assess(req: AssessRequest):
    try:
        result = engine.assess(
            entity_id=req.entity_id,
            entity_name=req.entity_name,
            nace_code=req.nace_code,
            revenue_bn=req.revenue_bn,
            headcount=req.headcount,
            sector_type=req.sector_type,
            portfolio_aum_bn=req.portfolio_aum_bn,
        )
        import dataclasses
        return {"status": "ok", "assessment": dataclasses.asdict(result)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/materiality-screen")
def materiality_screen(req: MaterialityRequest):
    try:
        return engine.screen_materiality(req.nace_code, req.revenue_bn)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/categories")
def ref_categories():
    return engine.ref_categories()


@router.get("/ref/calculation-methods")
def ref_calculation_methods():
    return engine.ref_calculation_methods()


@router.get("/ref/sbti-coverage-rule")
def ref_sbti_coverage_rule():
    return engine.ref_sbti_coverage_rule()


@router.get("/ref/pcaf-c15")
def ref_pcaf_c15():
    return {
        "category": "C15",
        "name": "Investments",
        "standard": "PCAF Global GHG Accounting and Reporting Standard Part C",
        "asset_classes": ["listed_equity", "corporate_bonds", "project_finance",
                          "real_estate", "sovereign_bonds", "loans"],
        "attribution_formula": "Financed Emissions = (Outstanding Amount / EVIC) x Company Emissions",
        "dqs_range": "1 (primary) to 5 (estimated)",
    }


@router.get("/ref/flag-sectors")
def ref_flag_sectors():
    from services.scope3_categories_engine import SBTI_SECTORS_FLAG
    return {
        "flag_sectors": SBTI_SECTORS_FLAG,
        "note": "SBTi FLAG (Forest, Land, Agriculture) sectors must set separate FLAG targets",
        "coverage_rule": ">=40% of total Scope 3 emissions must be covered by near-term targets",
    }


@router.get("/ref/ghg-protocol-scope3")
def ref_ghg_protocol_scope3():
    return {
        "standard": "GHG Protocol Corporate Value Chain (Scope 3) Standard 2011",
        "categories": 15,
        "upstream": list(range(1, 9)),
        "downstream": list(range(9, 16)),
        "mandatory_for_sbti": "All 15 categories must be screened; material ones set targets",
    }
