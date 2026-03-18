"""
DME Hawkes-Process Contagion Engine — API Routes.

Prefix: /api/v1/dme-contagion
"""
from fastapi import APIRouter
from services.dme_contagion_engine import (
    ContagionEngine, EdgeWeightInput, L1IntensityRequest, L2IntensityRequest,
    L3IntensityRequest, AggregationRequest, StabilityCheckRequest, FullSimulationRequest,
)

router = APIRouter(prefix="/api/v1/dme-contagion", tags=["DME Contagion"])


@router.post("/edge-weight")
def compute_edge_weight(req: EdgeWeightInput):
    """Compute composite edge weight w_ij from financial/supply-chain/regulatory channels."""
    result = ContagionEngine.compute_edge_weight(req)
    return result.model_dump()


@router.post("/l1-intensity")
def l1_intensity(req: L1IntensityRequest):
    """Layer 1: Entity-to-Entity contagion intensity (daily, exponential kernel)."""
    return ContagionEngine.l1_intensity(req)


@router.post("/l2-intensity")
def l2_intensity(req: L2IntensityRequest):
    """Layer 2: Structural Cascade intensity (monthly, exponential + power-law)."""
    return ContagionEngine.l2_intensity(req)


@router.post("/l3-intensity")
def l3_intensity(req: L3IntensityRequest):
    """Layer 3: Capital Flight intensity (weekly, cross-sector herding)."""
    return ContagionEngine.l3_intensity(req)


@router.post("/aggregate")
def aggregate(req: AggregationRequest):
    """Normalise 3 layers to daily base and compute EL/VaR/ES amplification."""
    return ContagionEngine.aggregate(req)


@router.post("/stability-check")
def stability_check(req: StabilityCheckRequest):
    """Check Hawkes process stationarity (spectral radius < 1)."""
    return ContagionEngine.check_stability(req)


@router.post("/simulate")
def simulate(req: FullSimulationRequest):
    """End-to-end contagion cascade simulation from seed entity."""
    return ContagionEngine.simulate(req)


@router.get("/ref/parameters")
def get_reference_data():
    """Reference: channel weights, cross-pillar amplifiers, empirical targets."""
    return ContagionEngine.get_reference_data()
