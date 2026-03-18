"""
API Routes: SASB Industry Standards
=====================================
POST /api/v1/sasb/assess-industry          — Full SASB industry assessment
POST /api/v1/sasb/assess-materiality       — Materiality assessment for industry
POST /api/v1/sasb/compare-peers            — Peer comparison against sector medians
GET  /api/v1/sasb/ref/sics-sectors         — SICS sector & industry registry
GET  /api/v1/sasb/ref/industry-codes       — Flat industry code list for UI dropdowns
GET  /api/v1/sasb/ref/materiality-map/{code} — Materiality map for an industry
GET  /api/v1/sasb/ref/issb-s2-mapping      — SASB-to-ISSB S2 cross-framework mapping
GET  /api/v1/sasb/ref/gri-mapping          — SASB-to-GRI interoperability
GET  /api/v1/sasb/ref/esrs-mapping         — SASB-to-ESRS interoperability
GET  /api/v1/sasb/ref/sector-benchmarks    — Sector median benchmarks
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from services.sasb_industry_engine import SASBIndustryEngine

router = APIRouter(prefix="/api/v1/sasb", tags=["SASB Industry Standards"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class IndustryAssessmentRequest(BaseModel):
    entity_name: str
    sasb_industry_code: str
    reporting_year: int = 2025
    reported_metrics: Optional[dict] = None


class MaterialityAssessmentRequest(BaseModel):
    entity_name: str
    sasb_industry_code: str
    reporting_year: int = 2025
    entity_overrides: Optional[dict] = None


class PeerComparisonRequest(BaseModel):
    entity_name: str
    sasb_industry_code: str
    reporting_year: int = 2025
    entity_metrics: Optional[dict] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/assess-industry")
def assess_industry(req: IndustryAssessmentRequest):
    """Full SASB industry assessment — completeness, materiality coverage, peer comparison, gaps."""
    engine = SASBIndustryEngine()
    r = engine.assess_industry(
        entity_name=req.entity_name,
        sasb_industry_code=req.sasb_industry_code,
        reporting_year=req.reporting_year,
        reported_metrics=req.reported_metrics,
    )
    return r.__dict__


@router.post("/assess-materiality")
def assess_materiality(req: MaterialityAssessmentRequest):
    """SASB materiality assessment — topic-level materiality, risk exposure, double materiality flags."""
    engine = SASBIndustryEngine()
    r = engine.assess_materiality(
        entity_name=req.entity_name,
        sasb_industry_code=req.sasb_industry_code,
        reporting_year=req.reporting_year,
        entity_overrides=req.entity_overrides,
    )
    return r.__dict__


@router.post("/compare-peers")
def compare_peers(req: PeerComparisonRequest):
    """Peer comparison — entity metrics vs sector median benchmarks."""
    engine = SASBIndustryEngine()
    r = engine.compare_to_peers(
        entity_name=req.entity_name,
        sasb_industry_code=req.sasb_industry_code,
        reporting_year=req.reporting_year,
        entity_metrics=req.entity_metrics,
    )
    return r.__dict__


# ---------------------------------------------------------------------------
# Reference Data Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/sics-sectors")
def ref_sics_sectors():
    """Full SICS sector and industry registry (11 sectors, 20 industries)."""
    return {"sics_sectors": SASBIndustryEngine.get_sics_sectors()}


@router.get("/ref/industry-codes")
def ref_industry_codes():
    """Flat industry code list for UI dropdowns."""
    return {"industry_codes": SASBIndustryEngine.get_industry_codes()}


@router.get("/ref/materiality-map/{code}")
def ref_materiality_map(code: str):
    """Materiality map for a specific SASB industry code."""
    return {"sasb_industry_code": code,
            "materiality_map": SASBIndustryEngine.get_materiality_map(code)}


@router.get("/ref/issb-s2-mapping")
def ref_issb_s2_mapping():
    """SASB-to-ISSB S2 Appendix B cross-framework mapping."""
    return {"issb_s2_mapping": SASBIndustryEngine.get_issb_s2_mapping()}


@router.get("/ref/gri-mapping")
def ref_gri_mapping():
    """SASB topic-to-GRI disclosure interoperability mapping."""
    return {"gri_mapping": SASBIndustryEngine.get_gri_mapping()}


@router.get("/ref/esrs-mapping")
def ref_esrs_mapping():
    """SASB topic-to-ESRS standard interoperability mapping."""
    return {"esrs_mapping": SASBIndustryEngine.get_esrs_mapping()}


@router.get("/ref/sector-benchmarks")
def ref_sector_benchmarks():
    """Sector median benchmarks used for peer comparison."""
    return {"sector_benchmarks": SASBIndustryEngine.get_sector_benchmarks()}
