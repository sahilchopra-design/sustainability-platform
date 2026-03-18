"""
API Routes: Model Validation Framework
=========================================
POST /api/v1/model-validation/backtest              — Run backtesting for a model
POST /api/v1/model-validation/compare-models         — Champion-challenger comparison
POST /api/v1/model-validation/transition-lifecycle   — Transition model lifecycle state
GET  /api/v1/model-validation/inventory              — Get model inventory (optionally filtered)
GET  /api/v1/model-validation/dashboard              — Platform-wide validation dashboard
GET  /api/v1/model-validation/ref/catalog            — Full model inventory catalog
GET  /api/v1/model-validation/ref/lifecycle-states   — Valid lifecycle states
GET  /api/v1/model-validation/ref/lifecycle-transitions — Valid lifecycle transitions
GET  /api/v1/model-validation/ref/validation-tests   — Available validation test specifications
GET  /api/v1/model-validation/ref/regulatory-frameworks — Regulatory frameworks governing validation
"""
from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from typing import Optional

from services.model_validation_framework import ModelValidationFramework

router = APIRouter(prefix="/api/v1/model-validation", tags=["Model Validation"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class BacktestRequest(BaseModel):
    model_id: str
    predicted: list[float]
    actual: list[float]
    observation_start: str = "2024-01-01"
    observation_end: str = "2024-12-31"
    tests_to_run: Optional[list[str]] = None


class CompareModelsRequest(BaseModel):
    champion_model_id: str
    challenger_model_id: str
    champion_predicted: list[float]
    challenger_predicted: list[float]
    actual: list[float]
    comparison_metric: str = "rmse"


class LifecycleTransitionRequest(BaseModel):
    model_id: str
    target_state: str
    reason: str = ""
    transitioned_by: str = "system"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/backtest")
def run_backtest(req: BacktestRequest):
    """Run generalised backtesting — RMSE, MAE, MAPE, hit rate, calibration, traffic lights."""
    fw = ModelValidationFramework()
    r = fw.run_backtest(
        model_id=req.model_id,
        predicted=req.predicted,
        actual=req.actual,
        observation_start=req.observation_start,
        observation_end=req.observation_end,
        tests_to_run=req.tests_to_run,
    )
    return r.__dict__


@router.post("/compare-models")
def compare_models(req: CompareModelsRequest):
    """Champion-challenger comparison with significance testing."""
    fw = ModelValidationFramework()
    r = fw.compare_models(
        champion_model_id=req.champion_model_id,
        challenger_model_id=req.challenger_model_id,
        champion_predicted=req.champion_predicted,
        challenger_predicted=req.challenger_predicted,
        actual=req.actual,
        comparison_metric=req.comparison_metric,
    )
    return r.__dict__


@router.post("/transition-lifecycle")
def transition_lifecycle(req: LifecycleTransitionRequest):
    """Transition a model to a new lifecycle state."""
    fw = ModelValidationFramework()
    return fw.transition_lifecycle(
        model_id=req.model_id,
        target_state=req.target_state,
        reason=req.reason,
        transitioned_by=req.transitioned_by,
    )


@router.get("/inventory")
def get_inventory(
    category: Optional[str] = Query(None, description="Filter by category"),
    risk_tier: Optional[int] = Query(None, description="Filter by risk tier (1-3)"),
):
    """Get model inventory, optionally filtered by category or risk tier."""
    fw = ModelValidationFramework()
    entries = fw.get_model_inventory(category=category, risk_tier=risk_tier)
    return {"models": [e.__dict__ for e in entries]}


@router.get("/dashboard")
def get_dashboard():
    """Platform-wide model validation dashboard — counts, compliance, overdue validations."""
    fw = ModelValidationFramework()
    r = fw.get_validation_dashboard()
    return r.__dict__


# ---------------------------------------------------------------------------
# Reference Data Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/catalog")
def ref_catalog():
    """Full model inventory registry with metadata."""
    return {"catalog": ModelValidationFramework.get_model_inventory_catalog()}


@router.get("/ref/lifecycle-states")
def ref_lifecycle_states():
    """Valid model lifecycle states (DEVELOPMENT through RETIRED)."""
    return {"lifecycle_states": ModelValidationFramework.get_lifecycle_states()}


@router.get("/ref/lifecycle-transitions")
def ref_lifecycle_transitions():
    """Valid lifecycle state transitions."""
    return {"transitions": ModelValidationFramework.get_lifecycle_transitions()}


@router.get("/ref/validation-tests")
def ref_validation_tests():
    """Available statistical validation tests with thresholds."""
    return {"validation_tests": ModelValidationFramework.get_validation_tests()}


@router.get("/ref/regulatory-frameworks")
def ref_regulatory_frameworks():
    """Regulatory frameworks governing model validation."""
    return {"regulatory_frameworks": ModelValidationFramework.get_regulatory_frameworks()}
