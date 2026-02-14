"""
API routes for Scenario Comparison, Gap Analysis, Consistency Checks, and Alerts.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

from db.base import get_db
from services.scenario_comparison_service import ScenarioComparisonService

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])


# ---- Pydantic schemas ----

class ComparisonCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    base_scenario_id: str
    compare_scenario_ids: List[str] = []
    variable_filter: List[str] = []
    region_filter: List[str] = []
    sector_filter: List[str] = []
    time_range: dict = {}
    is_public: bool = False
    created_by: str = "default_user"


class AdhocComparisonRequest(BaseModel):
    scenario_ids: List[str] = Field(..., min_length=2)
    variables: List[str] = []
    regions: List[str] = []
    time_range: dict = {}


class ComparisonResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    base_scenario_id: Optional[str] = None
    compare_scenario_ids: List[str] = []
    variable_filter: List[str] = []
    region_filter: List[str] = []
    sector_filter: List[str] = []
    time_range: dict = {}
    is_public: bool = False
    created_by: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class GapAnalysisResponse(BaseModel):
    id: str
    comparison_id: str
    gap_type: str
    variable: str
    region: str
    base_value: Optional[float] = None
    target_value: Optional[float] = None
    gap_value: Optional[float] = None
    gap_pct: Optional[float] = None
    gap_unit: Optional[str] = None
    year: Optional[int] = None
    required_action: Optional[str] = None
    confidence_level: Optional[float] = None

    class Config:
        from_attributes = True


class ConsistencyCheckResponse(BaseModel):
    id: str
    scenario_id: str
    check_type: str
    status: str
    score: Optional[float] = None
    issues: list = []
    details: dict = {}
    checked_at: datetime

    class Config:
        from_attributes = True


class AlertResponse(BaseModel):
    id: str
    user_id: str
    alert_type: str
    scenario_id: Optional[str] = None
    source_id: Optional[str] = None
    title: str
    message: Optional[str] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Comparisons
# ============================================================================

@router.get("/comparisons", response_model=List[ComparisonResponse])
def list_comparisons(db: Session = Depends(get_db)):
    """List all saved comparisons."""
    svc = ScenarioComparisonService(db)
    return svc.list_comparisons()


@router.post("/comparisons", response_model=ComparisonResponse, status_code=201)
def create_comparison(body: ComparisonCreate, db: Session = Depends(get_db)):
    """Save a new scenario comparison."""
    svc = ScenarioComparisonService(db)
    return svc.create_comparison(body.model_dump())


@router.get("/comparisons/{comp_id}")
def get_comparison(comp_id: str, db: Session = Depends(get_db)):
    """Get a saved comparison metadata."""
    svc = ScenarioComparisonService(db)
    comp = svc.get_comparison(comp_id)
    if not comp:
        raise HTTPException(404, "Comparison not found")
    return ComparisonResponse.model_validate(comp)


@router.get("/comparisons/{comp_id}/data")
def get_comparison_data(comp_id: str, db: Session = Depends(get_db)):
    """Get the full comparison dataset with charts and statistics."""
    svc = ScenarioComparisonService(db)
    try:
        return svc.build_comparison_data(comp_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.delete("/comparisons/{comp_id}", status_code=204)
def delete_comparison(comp_id: str, db: Session = Depends(get_db)):
    """Delete a comparison and its gap analyses."""
    svc = ScenarioComparisonService(db)
    if not svc.delete_comparison(comp_id):
        raise HTTPException(404, "Comparison not found")


@router.post("/compare")
def adhoc_compare(body: AdhocComparisonRequest, db: Session = Depends(get_db)):
    """Run an ad-hoc comparison without saving."""
    svc = ScenarioComparisonService(db)
    return svc.build_adhoc_comparison(
        body.scenario_ids, body.variables, body.regions, body.time_range
    )


# ============================================================================
# Gap Analysis
# ============================================================================

@router.post("/comparisons/{comp_id}/gap-analysis")
def run_gap_analysis(comp_id: str, db: Session = Depends(get_db)):
    """Run gap analysis for a saved comparison."""
    svc = ScenarioComparisonService(db)
    try:
        return {"gaps": svc.run_gap_analysis(comp_id)}
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/comparisons/{comp_id}/gap-analysis", response_model=List[GapAnalysisResponse])
def get_gap_analysis(comp_id: str, db: Session = Depends(get_db)):
    """Get cached gap analysis results."""
    svc = ScenarioComparisonService(db)
    return svc.get_gap_analyses(comp_id)


# ============================================================================
# Consistency Checks
# ============================================================================

@router.post("/scenarios/{scenario_id}/consistency-check")
def run_consistency_check(scenario_id: str, db: Session = Depends(get_db)):
    """Run consistency checks on a scenario."""
    svc = ScenarioComparisonService(db)
    try:
        return {"checks": svc.run_consistency_check(scenario_id)}
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/scenarios/{scenario_id}/consistency-check", response_model=List[ConsistencyCheckResponse])
def get_consistency_checks(scenario_id: str, db: Session = Depends(get_db)):
    """Get cached consistency check results."""
    svc = ScenarioComparisonService(db)
    return svc.get_consistency_checks(scenario_id)


# ============================================================================
# Alerts
# ============================================================================

@router.get("/alerts", response_model=List[AlertResponse])
def list_alerts(
    user_id: str = "default_user",
    unread_only: bool = False,
    db: Session = Depends(get_db),
):
    """List alerts for a user."""
    svc = ScenarioComparisonService(db)
    return svc.list_alerts(user_id, unread_only)


@router.patch("/alerts/{alert_id}/read", response_model=AlertResponse)
def mark_alert_read(alert_id: str, db: Session = Depends(get_db)):
    """Mark an alert as read."""
    svc = ScenarioComparisonService(db)
    alert = svc.mark_alert_read(alert_id)
    if not alert:
        raise HTTPException(404, "Alert not found")
    return alert
