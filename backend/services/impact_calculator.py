"""
Scenario Impact Calculator — connects hub scenarios to portfolios for PD/LGD/EL/VaR.
Maps hub scenario trajectories to the calculation engine's scenario categories.
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid
import logging

from db.models.data_hub import DataHubScenario, DataHubTrajectory

logger = logging.getLogger(__name__)

# Map hub scenario categories to the calculation engine's 3 scenario types
CATEGORY_TO_ENGINE_SCENARIO = {
    "Orderly": "Orderly",
    "Net Zero": "Orderly",
    "NZE": "Orderly",
    "Low Emissions": "Orderly",
    "Low GHG": "Orderly",
    "Very Low GHG": "Orderly",
    "Energy Transition": "Orderly",
    "1.5C": "Orderly",
    "Disorderly": "Disorderly",
    "Delayed": "Disorderly",
    "Divergent": "Disorderly",
    "Intermediate GHG": "Disorderly",
    "Hot House World": "Hot house world",
    "Current Policies": "Hot house world",
    "Baseline": "Hot house world",
    "STEPS": "Hot house world",
    "Reference": "Hot house world",
    "High GHG": "Hot house world",
    "Very High GHG": "Hot house world",
    "Physical Risk": "Hot house world",
    "Carbon Pricing": "Disorderly",
    "Policy": "Disorderly",
    "Sensitivity": "Disorderly",
}


def map_scenario_to_engine(scenario: DataHubScenario) -> str:
    """Map a hub scenario to one of the 3 engine scenario types."""
    cat = scenario.category or ""
    for key, val in CATEGORY_TO_ENGINE_SCENARIO.items():
        if key.lower() in cat.lower():
            return val
    # Fallback: use temperature target
    temp = scenario.temperature_target
    if temp:
        if temp <= 1.8:
            return "Orderly"
        elif temp <= 2.5:
            return "Disorderly"
    return "Hot house world"


def extract_scenario_multipliers(db: Session, scenario_id: str) -> Dict[str, float]:
    """Extract key multipliers from scenario trajectories for impact calculation."""
    trajs = db.query(DataHubTrajectory).filter(
        DataHubTrajectory.scenario_id == scenario_id,
        DataHubTrajectory.region == "World",
    ).all()

    multipliers = {
        "carbon_price_2030": None,
        "carbon_price_2050": None,
        "emissions_change_pct": None,
        "temperature_2050": None,
    }

    for t in trajs:
        vl = t.variable_name.lower()
        ts = t.time_series or {}

        if "price" in vl and "carbon" in vl:
            multipliers["carbon_price_2030"] = ts.get("2030")
            multipliers["carbon_price_2050"] = ts.get("2050")
        elif "emission" in vl and "co2" in vl and "energy" not in vl:
            v2025 = ts.get("2025") or ts.get("2020")
            v2050 = ts.get("2050")
            if v2025 and v2050 and v2025 != 0:
                multipliers["emissions_change_pct"] = round((v2050 - v2025) / abs(v2025) * 100, 2)
        elif "temperature" in vl:
            multipliers["temperature_2050"] = ts.get("2050")

    return multipliers


def run_impact_calculation(db: Session, scenario_id: str, portfolio_assets: list, horizons: list = None) -> Dict[str, Any]:
    """
    Run impact calculation for a hub scenario against a portfolio.
    Uses the existing calculation engine with mapped scenario type.
    """
    from services.calculation_engine import ClimateRiskCalculationEngine, AssetInput
    from services.engine_integration import assets_to_inputs

    scenario = db.get(DataHubScenario, scenario_id)
    if not scenario:
        raise ValueError(f"Scenario {scenario_id} not found")

    engine_scenario = map_scenario_to_engine(scenario)
    if horizons is None:
        horizons = [2030, 2040, 2050]

    asset_inputs = assets_to_inputs(portfolio_assets)

    engine = ClimateRiskCalculationEngine(
        n_simulations=10000,
        correlation=0.3,
        var_method='monte_carlo',
        base_return=0.05,
        random_seed=42,
    )

    results = engine.calculate_multiple_scenarios(
        assets=asset_inputs,
        scenarios=[engine_scenario],
        horizons=horizons,
        include_sector_breakdown=True,
    )

    multipliers = extract_scenario_multipliers(db, scenario_id)

    # Build response
    horizon_results = []
    for r in results:
        hr = {
            "scenario": engine_scenario,
            "horizon": r.horizon,
            "expected_loss": round(r.expected_loss, 2),
            "expected_loss_pct": round(r.expected_loss_pct, 4),
            "var_95": round(r.var_95, 2),
            "var_99": round(r.var_99, 2),
            "weighted_avg_pd": round(r.weighted_avg_pd, 6),
            "avg_pd_change_pct": round(r.avg_pd_change_pct, 2),
            "total_exposure": round(r.total_exposure, 2),
            "risk_adjusted_return": round(r.risk_adjusted_return, 4),
            "sector_breakdown": r.sector_breakdown,
            "rating_migrations": r.rating_migrations,
        }
        horizon_results.append(hr)

    return {
        "scenario_id": scenario_id,
        "scenario_name": scenario.display_name or scenario.name,
        "engine_scenario": engine_scenario,
        "multipliers": multipliers,
        "horizons": horizon_results,
        "calculated_at": datetime.now(timezone.utc).isoformat(),
    }
