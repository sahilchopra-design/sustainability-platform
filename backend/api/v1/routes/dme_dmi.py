"""
DME Dynamic Materiality Index (DMI) — API Routes.

Prefix: /api/v1/dme-dmi
"""
from fastapi import APIRouter
from services.dme_dmi_engine import (
    DMIEngine, PCAFAttributionRequest, PortfolioDMIRequest, EntityDMIRequest,
)

router = APIRouter(prefix="/api/v1/dme-dmi", tags=["DME DMI"])


@router.post("/pcaf-attribution")
def pcaf_attribution(req: PCAFAttributionRequest):
    """Calculate PCAF financed emissions attribution across holdings."""
    return DMIEngine.pcaf_attribution(req)


@router.post("/entity")
def entity_dmi(req: EntityDMIRequest):
    """Calculate entity-level DMI with confidence-weighted factor aggregation."""
    return DMIEngine.entity_dmi(req)


@router.post("/portfolio")
def portfolio_dmi(req: PortfolioDMIRequest):
    """Calculate portfolio-level DMI with concentration penalties and velocity overlay."""
    return DMIEngine.portfolio_dmi(req)


@router.get("/ref/pcaf-confidence")
def get_pcaf_confidence():
    """Reference: PCAF DQS → confidence mapping and decay parameters."""
    return DMIEngine.get_reference_data()
