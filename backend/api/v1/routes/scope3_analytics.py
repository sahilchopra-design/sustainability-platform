"""
API Routes — Scope 3 Analytics Engine (Sprint 26)
===================================================
POST /api/v1/scope3/category-coverage
POST /api/v1/scope3/calculate
POST /api/v1/scope3/dqs-assessment
POST /api/v1/scope3/sbti-scope3
POST /api/v1/scope3/avoided-emissions
POST /api/v1/scope3/double-counting
GET  /api/v1/scope3/ref/categories
GET  /api/v1/scope3/ref/sector-profiles
GET  /api/v1/scope3/ref/ef-databases
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.scope3_analytics_engine import (
    Scope3AnalyticsEngine,
    SCOPE3_CATEGORIES,
    SECTOR_SCOPE3_PROFILES,
    EMISSION_FACTOR_DATABASES,
    PCAF_SCOPE3_METHODOLOGY,
    SBTI_SCOPE3_THRESHOLDS,
    DOUBLE_COUNTING_RISKS,
)

router = APIRouter(prefix="/api/v1/scope3", tags=["scope3_analytics"])
_engine = Scope3AnalyticsEngine()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class CategoryCoverageRequest(BaseModel):
    entity_id: str
    sector: str
    reported_categories: dict[str, float] = Field(default_factory=dict)
    total_scope3_tco2e: float = Field(default=500_000.0)
    scope12_total_tco2e: float = Field(default=80_000.0)


class CalculateScope3Request(BaseModel):
    entity_id: str
    sector: str
    category_inputs: dict[str, float] = Field(default_factory=dict)


class DQSRequest(BaseModel):
    entity_id: str
    sector: str
    category_methods: dict[str, str] = Field(default_factory=dict)


class SBTiScope3Request(BaseModel):
    entity_id: str
    sector: str
    scope3_tco2e: float = Field(default=500_000.0)
    supplier_engagement_pct: float = Field(default=40.0, ge=0, le=100)
    downstream_coverage_pct: float = Field(default=30.0, ge=0, le=100)
    flag_tco2e: float = Field(default=0.0)


class AvoidedEmissionsRequest(BaseModel):
    entity_id: str
    product_type: str
    annual_units_sold: float = Field(default=100_000)
    baseline_product_emission_factor: float = Field(default=2.5)
    product_emission_factor: float = Field(default=0.5)
    methodology: str = "displacement"


class DoubleCountingRequest(BaseModel):
    entity_id: str
    sector: str
    category_data: dict[str, float] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# POST endpoints
# ---------------------------------------------------------------------------

@router.post("/category-coverage")
async def category_coverage(req: CategoryCoverageRequest):
    try:
        return _engine.assess_category_coverage(
            entity_id=req.entity_id,
            sector=req.sector,
            reported_categories=req.reported_categories,
            total_scope3_tco2e=req.total_scope3_tco2e,
            scope12_total_tco2e=req.scope12_total_tco2e,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/calculate")
async def calculate_scope3(req: CalculateScope3Request):
    try:
        return _engine.calculate_scope3(
            entity_id=req.entity_id,
            sector=req.sector,
            category_inputs=req.category_inputs,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/dqs-assessment")
async def dqs_assessment(req: DQSRequest):
    try:
        return _engine.assess_dqs(
            entity_id=req.entity_id,
            sector=req.sector,
            category_methods=req.category_methods,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/sbti-scope3")
async def sbti_scope3(req: SBTiScope3Request):
    try:
        return _engine.assess_sbti_scope3(
            entity_id=req.entity_id,
            sector=req.sector,
            scope3_tco2e=req.scope3_tco2e,
            supplier_engagement_pct=req.supplier_engagement_pct,
            downstream_coverage_pct=req.downstream_coverage_pct,
            flag_tco2e=req.flag_tco2e,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/avoided-emissions")
async def avoided_emissions(req: AvoidedEmissionsRequest):
    try:
        return _engine.calculate_avoided_emissions(
            entity_id=req.entity_id,
            product_type=req.product_type,
            annual_units_sold=req.annual_units_sold,
            baseline_product_emission_factor=req.baseline_product_emission_factor,
            product_emission_factor=req.product_emission_factor,
            methodology=req.methodology,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/double-counting")
async def double_counting(req: DoubleCountingRequest):
    try:
        return _engine.assess_double_counting(
            entity_id=req.entity_id,
            sector=req.sector,
            category_data=req.category_data,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# GET reference endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/categories")
async def ref_categories():
    try:
        upstream = {k: v for k, v in SCOPE3_CATEGORIES.items() if v["upstream_downstream"] == "upstream"}
        downstream = {k: v for k, v in SCOPE3_CATEGORIES.items() if v["upstream_downstream"] == "downstream"}
        return {
            "categories": SCOPE3_CATEGORIES,
            "upstream": upstream,
            "downstream": downstream,
            "total": len(SCOPE3_CATEGORIES),
            "pcaf_methodology": PCAF_SCOPE3_METHODOLOGY,
            "sbti_thresholds": SBTI_SCOPE3_THRESHOLDS,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/sector-profiles")
async def ref_sector_profiles():
    try:
        cat15_sectors = [s for s, p in SECTOR_SCOPE3_PROFILES.items() if p["cat15_materiality"]]
        flag_sectors = [s for s, p in SECTOR_SCOPE3_PROFILES.items() if p["flag_materiality"]]
        return {
            "profiles": SECTOR_SCOPE3_PROFILES,
            "cat15_material_sectors": cat15_sectors,
            "flag_material_sectors": flag_sectors,
            "double_counting_risks": DOUBLE_COUNTING_RISKS,
            "total_sectors": len(SECTOR_SCOPE3_PROFILES),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/ef-databases")
async def ref_ef_databases():
    try:
        return {
            "databases": EMISSION_FACTOR_DATABASES,
            "total_databases": len(EMISSION_FACTOR_DATABASES),
            "recommended_hierarchy": [
                "supplier-specific-verified (DQS 1)",
                "activity-based with ecoinvent (DQS 2-3)",
                "spend-based with exiobase/defra (DQS 4-5)",
            ],
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
