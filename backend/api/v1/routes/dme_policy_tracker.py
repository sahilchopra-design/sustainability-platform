"""
DME Policy Velocity Tracker — API Routes.

Prefix: /api/v1/dme-policy-tracker
"""
from fastapi import APIRouter
from services.dme_policy_tracker_engine import (
    PolicyTrackerEngine, CompositeVelocityRequest, PolicyEventBatchRequest,
)

router = APIRouter(prefix="/api/v1/dme-policy-tracker", tags=["DME Policy Tracker"])


@router.post("/composite-velocity")
def composite_velocity(req: CompositeVelocityRequest):
    """Calculate composite policy velocity index from component inputs."""
    return PolicyTrackerEngine.composite_velocity(req)


@router.post("/from-events")
def from_events(req: PolicyEventBatchRequest):
    """Calculate composite velocity from discrete policy events."""
    return PolicyTrackerEngine.from_events(req)


@router.get("/ref/sector-weights")
def get_sector_weights():
    """Reference: sector-specific component weights."""
    return PolicyTrackerEngine.get_reference_data()["sector_weights"]


@router.get("/ref/components")
def get_components():
    """Reference: policy velocity component descriptions."""
    return PolicyTrackerEngine.get_reference_data()["components"]
