"""
DME Alert Framework — API Routes.

Prefix: /api/v1/dme-alerts
"""
from fastapi import APIRouter
from services.dme_alert_engine import (
    AlertEngine, ProcessSignalsRequest, VelocitySignalInput,
)

router = APIRouter(prefix="/api/v1/dme-alerts", tags=["DME Alerts"])


@router.post("/process-signal")
def process_signal(req: VelocitySignalInput):
    """Process single velocity signal, return alert (or null)."""
    record = AlertEngine.process_signal(req)
    if record:
        return {"alert": record.model_dump()}
    return {"alert": None, "reason": "No alert conditions met (tier=None or acceleration ≤ 0)"}


@router.post("/process-batch")
def process_batch(req: ProcessSignalsRequest):
    """Process batch of velocity signals, return generated alerts."""
    return AlertEngine.process_batch(req)


@router.get("/ref/thresholds")
def get_thresholds():
    """Reference: tier thresholds, SLAs, suppression windows."""
    return AlertEngine.get_reference_data()
