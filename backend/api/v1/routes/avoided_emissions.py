"""
API Routes: Scope 4 / Avoided Emissions
========================================
GHG Protocol Scope 4 Guidance 2022

POST /api/v1/avoided-emissions/calculate-activity   — Single activity avoided emissions
POST /api/v1/avoided-emissions/additionality-check  — Additionality scoring
POST /api/v1/avoided-emissions/article6-eligibility — Paris Agreement ITMO eligibility
POST /api/v1/avoided-emissions/bvcm-check           — SBTi BVCM eligibility
POST /api/v1/avoided-emissions/portfolio-aggregate  — Aggregate across activities
POST /api/v1/avoided-emissions/full-assessment      — Complete Scope 4 assessment
GET  /api/v1/avoided-emissions/ref/categories       — AVOIDED_EMISSION_CATEGORIES
GET  /api/v1/avoided-emissions/ref/baseline-factors — BASELINE_FACTORS
GET  /api/v1/avoided-emissions/ref/article6-criteria — ARTICLE6_CRITERIA
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from services.avoided_emissions_engine import AvoidedEmissionsEngine

router = APIRouter(
    prefix="/api/v1/avoided-emissions",
    tags=["Scope 4 Avoided Emissions — E42"],
)


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class CalculateActivityRequest(BaseModel):
    entity_id: str
    activity_type: str = "solar_panels"
    baseline_factor: float = Field(0.82, ge=0, description="kgCO2e per unit for baseline")
    solution_factor: float = Field(0.04, ge=0, description="kgCO2e per unit for solution")
    quantity: float = Field(1000000.0, ge=0, description="Number of units produced/sold")
    attribution_factor: float = Field(1.0, ge=0, le=1.0)


class AdditionalityCheckRequest(BaseModel):
    entity_id: str
    activity_type: str = "solar_panels"
    activity_data: dict = {}


class Article6EligibilityRequest(BaseModel):
    entity_id: str
    activity_data: dict = {}


class BVCMCheckRequest(BaseModel):
    entity_id: str
    activity_data: dict = {}


class PortfolioAggregateRequest(BaseModel):
    entity_id: str
    activities: list = Field(
        default=[],
        description="List of activity dicts with category and total_avoided_tco2e",
    )


class FullAssessmentRequest(BaseModel):
    entity_id: str
    entity_name: str
    assessment_type: str = "enabled"
    reporting_year: int = 2025
    activities_data: dict = {}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/calculate-activity")
def calculate_activity(req: CalculateActivityRequest):
    """Calculate avoided emissions for a single Scope 4 activity."""
    try:
        engine = AvoidedEmissionsEngine()
        return engine.calculate_avoided_per_activity(
            entity_id=req.entity_id,
            activity_type=req.activity_type,
            baseline_factor=req.baseline_factor,
            solution_factor=req.solution_factor,
            quantity=req.quantity,
            attribution_factor=req.attribution_factor,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/additionality-check")
def additionality_check(req: AdditionalityCheckRequest):
    """Score additionality across five GHG Protocol criteria."""
    try:
        engine = AvoidedEmissionsEngine()
        return engine.assess_additionality(
            entity_id=req.entity_id,
            activity_type=req.activity_type,
            activity_data=req.activity_data,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/article6-eligibility")
def article6_eligibility(req: Article6EligibilityRequest):
    """Check Paris Agreement Article 6 ITMO eligibility."""
    try:
        engine = AvoidedEmissionsEngine()
        return engine.check_article6_eligibility(
            entity_id=req.entity_id,
            activity_data=req.activity_data,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/bvcm-check")
def bvcm_check(req: BVCMCheckRequest):
    """Check SBTi Beyond Value Chain Mitigation eligibility."""
    try:
        engine = AvoidedEmissionsEngine()
        return engine.check_bvcm_eligibility(
            entity_id=req.entity_id,
            activity_data=req.activity_data,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/portfolio-aggregate")
def portfolio_aggregate(req: PortfolioAggregateRequest):
    """Aggregate Scope 4 avoided emissions across all activities."""
    try:
        engine = AvoidedEmissionsEngine()
        return engine.aggregate_portfolio(
            entity_id=req.entity_id,
            activities=req.activities,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/full-assessment")
def full_assessment(req: FullAssessmentRequest):
    """Complete Scope 4 avoided emissions assessment with cross-framework linkage."""
    try:
        engine = AvoidedEmissionsEngine()
        return engine.full_assessment(
            entity_id=req.entity_id,
            entity_name=req.entity_name,
            assessment_type=req.assessment_type,
            reporting_year=req.reporting_year,
            activities_data=req.activities_data,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Reference endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/categories")
def ref_categories():
    """Return Scope 4 avoided emission categories (enabled/substitution/facilitated)."""
    return AvoidedEmissionsEngine.get_avoided_emission_categories()


@router.get("/ref/baseline-factors")
def ref_baseline_factors():
    """Return baseline emission factors by product category (kgCO2e/unit)."""
    return AvoidedEmissionsEngine.get_baseline_factors()


@router.get("/ref/article6-criteria")
def ref_article6_criteria():
    """Return Paris Agreement Article 6 ITMO eligibility criteria."""
    return AvoidedEmissionsEngine.get_article6_criteria()
