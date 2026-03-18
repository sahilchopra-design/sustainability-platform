"""
DME Velocity Engine — API Routes.

Prefix: /api/v1/dme-velocity
"""
from fastapi import APIRouter
from services.dme_velocity_engine import (
    VelocityEngine, VelocitySeriesRequest, VelocitySingleRequest, VelocityConfig,
)

router = APIRouter(prefix="/api/v1/dme-velocity", tags=["DME Velocity"])


@router.post("/process-series")
def process_series(req: VelocitySeriesRequest):
    """Process full metric time series through 6-stage velocity pipeline."""
    outputs = VelocityEngine.process_series(req)
    summary = VelocityEngine.get_regime_summary(outputs)
    return {
        "entity_id": req.entity_id,
        "metric_key": req.metric_key,
        "observations": len(outputs),
        "summary": summary,
        "results": [o.model_dump() for o in outputs],
    }


@router.post("/process-single")
def process_single(req: VelocitySingleRequest):
    """Process single new observation (real-time mode)."""
    output = VelocityEngine.process_single(req)
    return {
        "entity_id": req.entity_id,
        "metric_key": req.metric_key,
        "result": output.model_dump(),
    }


@router.post("/classify-alert")
def classify_alert(velocity: float, acceleration: float, z_score: float):
    """Classify alert level per FRS §3.1 compound condition."""
    level = VelocityEngine.classify_alert_level(velocity, acceleration, z_score)
    return {"alert_level": level, "velocity": velocity, "acceleration": acceleration, "z_score": z_score}


@router.get("/ref/config-defaults")
def get_config_defaults():
    """Return default velocity configuration."""
    return VelocityConfig(metric_key="default").model_dump()


@router.get("/ref/regimes")
def get_regime_definitions():
    """Return regime classification thresholds."""
    return {
        "regimes": [
            {"regime": "NORMAL", "condition": "|z| < z_threshold_elevated"},
            {"regime": "ELEVATED", "condition": "z_threshold_elevated ≤ |z| < z_threshold_critical"},
            {"regime": "CRITICAL", "condition": "z_threshold_critical ≤ |z| < z_threshold_extreme"},
            {"regime": "EXTREME", "condition": "|z| ≥ z_threshold_extreme"},
        ],
        "defaults": {"elevated": 1.0, "critical": 2.0, "extreme": 3.0},
        "pipeline_stages": [
            "1. Raw materiality series M(t)",
            "2. Canonical velocity V(t) = [M(t) - M(t-Δt)] / Δt",
            "3. EWMA smoothing (optional)",
            "4. Percentage velocity V%(t)",
            "5. Z-score normalisation",
            "6. Regime classification",
        ],
    }
