"""
DME Greenwashing Detection — API Routes.

Prefix: /api/v1/dme-greenwashing
"""
from fastapi import APIRouter
from services.dme_greenwashing_engine import (
    GreenwashingEngine, GreenwashDetectRequest, GreenwashScanRequest, GreenwashConfig,
)

router = APIRouter(prefix="/api/v1/dme-greenwashing", tags=["DME Greenwashing"])


@router.post("/detect")
def detect_greenwashing(req: GreenwashDetectRequest):
    """Full statistical greenwashing detection (requires ≥ 20 observations)."""
    return GreenwashingEngine.detect(req)


@router.post("/quick-scan")
def quick_scan(req: GreenwashScanRequest):
    """Lightweight single-point credibility gap scan."""
    return GreenwashingEngine.quick_scan(req)


@router.get("/ref/config-defaults")
def get_config_defaults():
    """Return default greenwashing detection configuration."""
    return GreenwashConfig().model_dump()


@router.get("/ref/methodology")
def get_methodology():
    """Return detection methodology reference."""
    return {
        "credibility_weighting": {
            "formula": "W = RawScore × QualityWeight × Freshness",
            "quality_weight": "1 - (PCAF - 1) × 0.2",
            "freshness": "exp(-ln(2)/36 × age_months)",
        },
        "detection_conditions": {
            "condition_1": "V_divergence > 1σ (velocity exceeds historical)",
            "condition_2": "A_divergence > 0 (acceleration positive, gap widening)",
            "condition_3_warning": "Z-score > 2σ",
            "condition_3_critical": "Z-score > 3σ",
            "trigger": "All 3 conditions must hold simultaneously",
        },
        "cusum": {
            "formula": "C_t⁺ = max(0, C_{t-1}⁺ + (D_t - μ) - k·σ)",
            "decision": "Alert if C_t⁺ > h·σ",
            "defaults": {"k_factor": 0.5, "h": 5.0},
        },
        "risk_levels_quick_scan": {
            "HIGH": "Gap > 30%",
            "MEDIUM": "Gap 15-30%",
            "LOW": "Gap < 15%",
        },
    }
