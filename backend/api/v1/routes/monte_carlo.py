"""
Monte Carlo Simulation API — Portfolio-Level Probabilistic Risk Distribution

POST /api/v1/monte-carlo/run       — Run full Monte Carlo simulation
POST /api/v1/monte-carlo/quick     — Quick deterministic scenario comparison
GET  /api/v1/monte-carlo/health    — Engine health check

Aligned with: Basel III Pillar 2, NGFS Phase IV, TCFD, EBA GL/2022/16.
"""

import logging
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, validator

from services.monte_carlo_engine import (
    AssetInput,
    MonteCarloEngine,
    MonteCarloResult,
    UncertaintyParams,
    NGFS_SCENARIOS,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/monte-carlo", tags=["Monte Carlo Simulation"])


# ---------------------------------------------------------------------------
# PYDANTIC REQUEST / RESPONSE SCHEMAS
# ---------------------------------------------------------------------------

class AssetInputSchema(BaseModel):
    id: str = Field(..., description="Unique asset identifier")
    name: str = Field(..., description="Asset / counterparty display name")
    sector: str = Field(..., description="NGFS sector label")
    exposure: float = Field(..., gt=0, description="Exposure at Default (EAD) in currency units")
    baseline_pd: float = Field(..., ge=0, le=1, description="Baseline probability of default (0-1)")
    lgd: float = Field(..., ge=0, le=1, description="Loss given default (0-1)")
    emission_intensity: Optional[float] = Field(
        None, ge=0, description="Emission intensity (tCO2e per unit revenue)"
    )
    emissions_trend: str = Field("Stable", description="'Improving' | 'Stable' | 'Deteriorating'")
    transition_plan_score: Optional[int] = Field(
        None, ge=1, le=5, description="Transition plan quality score (1=poor, 5=excellent)"
    )
    physical_risk_score: Optional[int] = Field(
        None, ge=1, le=5, description="Physical climate risk exposure score (1=low, 5=high)"
    )

    @validator("emissions_trend")
    def validate_trend(cls, v):
        allowed = {"Improving", "Stable", "Deteriorating"}
        if v not in allowed:
            raise ValueError(f"emissions_trend must be one of: {allowed}")
        return v


class UncertaintyParamsSchema(BaseModel):
    pd_sigma: float = Field(0.25, ge=0.0, le=1.0, description="PD lognormal sigma")
    lgd_sigma: float = Field(0.15, ge=0.0, le=0.5, description="LGD normal sigma")
    carbon_price_sigma: float = Field(0.30, ge=0.0, le=1.0, description="Carbon price lognormal sigma")
    physical_risk_sigma: float = Field(0.20, ge=0.0, le=1.0, description="Physical risk multiplier sigma")
    exposure_sigma: float = Field(0.08, ge=0.0, le=0.5, description="EAD normal sigma")


class MonteCarloRunRequest(BaseModel):
    scenario: str = Field("Orderly", description="NGFS scenario: 'Orderly' | 'Disorderly' | 'Hot house world'")
    time_horizon: int = Field(2050, description="Target year: 2030 | 2040 | 2050")
    n_simulations: int = Field(1000, ge=100, le=10000, description="Number of Monte Carlo draws")
    random_seed: int = Field(42, description="Random seed for reproducibility")
    uncertainty: Optional[UncertaintyParamsSchema] = None
    compare_scenarios: bool = Field(True, description="Include cross-scenario comparison table")
    assets: List[AssetInputSchema] = Field(..., min_items=1, max_items=200)

    @validator("scenario")
    def validate_scenario(cls, v):
        if v not in NGFS_SCENARIOS:
            raise ValueError(f"scenario must be one of: {NGFS_SCENARIOS}")
        return v

    @validator("time_horizon")
    def validate_horizon(cls, v):
        if v not in (2030, 2040, 2050):
            raise ValueError("time_horizon must be 2030, 2040, or 2050")
        return v


class QuickComparisonRequest(BaseModel):
    assets: List[AssetInputSchema] = Field(..., min_items=1, max_items=200)
    time_horizon: int = Field(2050, description="Target year: 2030 | 2040 | 2050")

    @validator("time_horizon")
    def validate_horizon(cls, v):
        if v not in (2030, 2040, 2050):
            raise ValueError("time_horizon must be 2030, 2040, or 2050")
        return v


# ---------------------------------------------------------------------------
# HELPER: schema → domain objects
# ---------------------------------------------------------------------------

def _to_asset_inputs(schemas: List[AssetInputSchema]) -> List[AssetInput]:
    return [
        AssetInput(
            id=s.id,
            name=s.name,
            sector=s.sector,
            exposure=s.exposure,
            baseline_pd=s.baseline_pd,
            lgd=s.lgd,
            emission_intensity=s.emission_intensity,
            emissions_trend=s.emissions_trend,
            transition_plan_score=s.transition_plan_score,
            physical_risk_score=s.physical_risk_score,
        )
        for s in schemas
    ]


def _result_to_dict(result: MonteCarloResult) -> Dict[str, Any]:
    return {
        "scenario":           result.scenario,
        "time_horizon":       result.time_horizon,
        "n_simulations":      result.n_simulations,
        "n_assets":           result.n_assets,
        "total_exposure":     result.total_exposure,
        "distributions":      result.distributions,
        "asset_level":        result.asset_level,
        "scenario_comparison": result.scenario_comparison,
        "convergence":        result.convergence,
        "methodology":        result.methodology,
        "calculation_timestamp": result.calculation_timestamp,
    }


# ---------------------------------------------------------------------------
# ENDPOINTS
# ---------------------------------------------------------------------------

@router.get("/health")
async def monte_carlo_health() -> Dict[str, Any]:
    """Health check — confirms Monte Carlo engine is available."""
    return {
        "status":  "ok",
        "engine":  "MonteCarloEngine v1.0.0",
        "method":  "Parameter Uncertainty Monte Carlo",
        "scenarios": NGFS_SCENARIOS,
    }


@router.post("/run")
async def run_monte_carlo(req: MonteCarloRunRequest) -> Dict[str, Any]:
    """
    Run a full Monte Carlo simulation for a portfolio of assets.

    Returns P5/P25/P50/P75/P95 distributions for Expected Loss, VaR (99.9%),
    Carbon Cost, WACI, Loss Rate, and HHI concentration, plus asset-level
    percentile breakdowns and cross-scenario comparison.
    """
    try:
        unc_params = (
            UncertaintyParams(
                pd_sigma=req.uncertainty.pd_sigma,
                lgd_sigma=req.uncertainty.lgd_sigma,
                carbon_price_sigma=req.uncertainty.carbon_price_sigma,
                physical_risk_sigma=req.uncertainty.physical_risk_sigma,
                exposure_sigma=req.uncertainty.exposure_sigma,
            )
            if req.uncertainty
            else UncertaintyParams()
        )

        engine = MonteCarloEngine(
            n_simulations=req.n_simulations,
            random_seed=req.random_seed,
        )

        assets = _to_asset_inputs(req.assets)

        result = engine.run(
            assets=assets,
            scenario=req.scenario,
            time_horizon=req.time_horizon,
            uncertainty=unc_params,
            compare_scenarios=req.compare_scenarios,
        )

        return {"success": True, "data": _result_to_dict(result)}

    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.exception("Monte Carlo run failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Monte Carlo simulation failed: {exc}",
        )


@router.post("/quick")
async def quick_scenario_comparison(req: QuickComparisonRequest) -> Dict[str, Any]:
    """
    Quick deterministic scenario comparison across all NGFS scenarios.

    Runs a lightweight 200-simulation MC to generate median estimates for each
    scenario (Orderly / Disorderly / Hot house world) without full distribution.
    Faster than /run — suitable for real-time UI previews.
    """
    try:
        engine = MonteCarloEngine(n_simulations=200, random_seed=42)
        assets = _to_asset_inputs(req.assets)

        comparisons: Dict[str, Any] = {}
        for sc in NGFS_SCENARIOS:
            result = engine.run(
                assets=assets,
                scenario=sc,
                time_horizon=req.time_horizon,
                uncertainty=UncertaintyParams(),
                compare_scenarios=False,
            )
            d = result.distributions
            comparisons[sc] = {
                "expected_loss_p50":     d["expected_loss"]["p50"],
                "expected_loss_p95":     d["expected_loss"]["p95"],
                "portfolio_var_999_p50": d["portfolio_var_999"]["p50"],
                "carbon_cost_p50":       d["carbon_cost"]["p50"],
                "waci_p50":              d["waci"]["p50"],
                "avg_pd_p50":            d["avg_pd"]["p50"],
                "loss_rate_p50":         d["loss_rate"]["p50"],
            }

        return {
            "success": True,
            "time_horizon": req.time_horizon,
            "n_assets": len(assets),
            "total_exposure": float(sum(a.exposure for a in assets)),
            "scenario_comparison": comparisons,
        }

    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.exception("Quick MC comparison failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quick scenario comparison failed: {exc}",
        )
