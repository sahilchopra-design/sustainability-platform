"""
Scenario Builder Calculation Engine.

Computes temperature projections, economic impacts, risk scores,
and Monte Carlo simulations from customized scenario parameters.
Works with ALL hub scenarios (any source).
"""

import math
import random
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone


# TCRE: Transient Climate Response to Cumulative Emissions ≈ 0.45°C per 1000 GtCO2
TCRE = 0.00045  # °C per Gt CO2
BASELINE_TEMP_2020 = 1.1  # °C above pre-industrial
CARBON_BUDGET_1_5C = 400  # Gt CO2 remaining from 2020 for 50% chance of 1.5°C
CARBON_BUDGET_2C = 1150   # Gt CO2 remaining from 2020 for 67% chance of 2°C


def interpolate_series(data: dict, method: str = "linear") -> dict:
    """Fill missing years in a time series dict."""
    if not data:
        return data
    years = sorted(int(y) for y in data.keys())
    if len(years) < 2:
        return data
    result = {}
    for y in range(years[0], years[-1] + 1):
        if str(y) in data:
            result[str(y)] = data[str(y)]
        else:
            prev = max(yr for yr in years if yr <= y)
            nxt = min(yr for yr in years if yr >= y)
            if prev == nxt:
                result[str(y)] = data[str(prev)]
            else:
                frac = (y - prev) / (nxt - prev)
                v0, v1 = data[str(prev)], data[str(nxt)]
                if method == "exponential" and v0 > 0 and v1 > 0:
                    result[str(y)] = round(v0 * (v1 / v0) ** frac, 4)
                elif method == "step":
                    result[str(y)] = v0
                else:
                    result[str(y)] = round(v0 + frac * (v1 - v0), 4)
    return result


def calculate_impacts(base_trajectories: List[dict], customizations: List[dict]) -> dict:
    """
    Calculate climate/economic/risk impacts from customized trajectories.

    Args:
        base_trajectories: List of original trajectory dicts from hub
        customizations: List of {variable_name, region, customized_values, interpolation_method}

    Returns:
        Full impact assessment dict
    """
    # Build merged trajectory map: (variable, region) -> {year: value}
    traj_map = {}
    for t in base_trajectories:
        key = (t.get("variable_name", ""), t.get("region", "World"))
        traj_map[key] = dict(t.get("time_series", {}))

    # Apply customizations
    for c in customizations:
        key = (c["variable_name"], c.get("region", "World"))
        custom_vals = c.get("customized_values", {})
        method = c.get("interpolation_method", "linear")
        if key in traj_map:
            traj_map[key].update(custom_vals)
            traj_map[key] = interpolate_series(traj_map[key], method)
        else:
            traj_map[key] = interpolate_series(custom_vals, method)

    # --- Temperature projection (TCRE-based) ---
    emissions = _find_series(traj_map, "emission", "co2")
    temp_outcome = _calc_temperature(emissions)

    # --- Emissions trajectory ---
    emissions_traj = _build_trajectory_output(emissions)
    cumulative = sum(v for v in (emissions or {}).values() if isinstance(v, (int, float)))

    # --- Economic impact ---
    gdp_series = _find_series(traj_map, "gdp")
    carbon_price_series = _find_series(traj_map, "price", "carbon")
    econ = _calc_economic(gdp_series, carbon_price_series)

    # --- Risk scores ---
    risks = _calc_risks(temp_outcome, carbon_price_series, emissions)

    # --- Energy transition indicators ---
    energy = _calc_energy_indicators(traj_map)

    return {
        "temperature_outcome": temp_outcome,
        "emissions_trajectory": {
            "annual_emissions": emissions_traj,
            "cumulative_emissions_gt": round(cumulative, 1),
            "carbon_budget_1_5c_consumed_pct": round(cumulative / CARBON_BUDGET_1_5C * 100, 1) if cumulative > 0 else 0,
            "carbon_budget_2c_consumed_pct": round(cumulative / CARBON_BUDGET_2C * 100, 1) if cumulative > 0 else 0,
        },
        "economic_impacts": econ,
        "risk_indicators": risks,
        "energy_transition": energy,
        "calculated_at": datetime.now(timezone.utc).isoformat(),
    }


def run_monte_carlo(base_trajectories, customizations, iterations=1000, seed=42):
    """
    Monte Carlo simulation — varies key parameters within uncertainty ranges.
    Returns probability distributions of outcomes.
    """
    rng = random.Random(seed)
    temp_results = []
    el_results = []
    risk_results = []

    for _ in range(iterations):
        # Perturb customizations by ±20%
        perturbed = []
        for c in customizations:
            pc = dict(c)
            vals = dict(c.get("customized_values", {}))
            for y in vals:
                noise = rng.gauss(1.0, 0.1)  # ±10% std dev
                vals[y] = round(vals[y] * noise, 4) if isinstance(vals[y], (int, float)) else vals[y]
            pc["customized_values"] = vals
            perturbed.append(pc)

        impacts = calculate_impacts(base_trajectories, perturbed)
        temp_results.append(impacts["temperature_outcome"].get("by_2100", 2.0))
        risk_results.append(impacts["risk_indicators"].get("overall_climate_risk", 5))

    temp_results.sort()
    risk_results.sort()

    def percentiles(arr):
        n = len(arr)
        return {
            "p5": round(arr[int(n * 0.05)], 2),
            "p25": round(arr[int(n * 0.25)], 2),
            "p50": round(arr[int(n * 0.50)], 2),
            "p75": round(arr[int(n * 0.75)], 2),
            "p95": round(arr[int(n * 0.95)], 2),
            "mean": round(sum(arr) / n, 2),
        }

    return {
        "iterations": iterations,
        "temperature_distribution": percentiles(temp_results),
        "risk_distribution": percentiles(risk_results),
        "probability_below_1_5c": round(sum(1 for t in temp_results if t <= 1.5) / iterations * 100, 1),
        "probability_below_2c": round(sum(1 for t in temp_results if t <= 2.0) / iterations * 100, 1),
    }


def validate_customizations(customizations: List[dict]) -> dict:
    """Validate parameter constraints."""
    errors = []
    warnings = []

    CONSTRAINTS = {
        "carbon_price": {"min": 0, "max": 1000},
        "emissions": {"min": -15, "max": 60},
        "temperature": {"min": 0.5, "max": 6.0},
        "gdp_impact": {"min": -20, "max": 15},
    }

    for c in customizations:
        var = c.get("variable_name", "").lower()
        vals = c.get("customized_values", {})

        for constraint_key, limits in CONSTRAINTS.items():
            if constraint_key in var:
                for year, val in vals.items():
                    if isinstance(val, (int, float)):
                        if val < limits["min"]:
                            errors.append({"parameter": c["variable_name"], "year": year,
                                          "message": f"Value {val} below minimum {limits['min']}", "severity": "error"})
                        elif val > limits["max"]:
                            errors.append({"parameter": c["variable_name"], "year": year,
                                          "message": f"Value {val} above maximum {limits['max']}", "severity": "error"})

        # Check time consistency
        years = sorted(int(y) for y in vals.keys() if isinstance(vals[y], (int, float)))
        if len(years) >= 2 and "emission" in var:
            first, last = vals[str(years[0])], vals[str(years[-1])]
            if last > first * 1.5:
                warnings.append({"parameter": c["variable_name"],
                                "message": "Emissions increasing significantly — inconsistent with most climate targets",
                                "suggestion": "Consider a declining emissions trajectory"})

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


# ---- Internal helpers ----

def _find_series(traj_map, *keywords):
    """Find a trajectory by keyword matching."""
    for (var, region), ts in traj_map.items():
        if all(kw in var.lower() for kw in keywords) and region == "World":
            return ts
    for (var, region), ts in traj_map.items():
        if all(kw in var.lower() for kw in keywords):
            return ts
    return {}


def _calc_temperature(emissions_ts):
    """Simple TCRE-based temperature projection."""
    if not emissions_ts:
        return {"by_2050": None, "by_2100": None, "probability_1_5C": 0, "probability_2C": 0}

    cumulative = 0
    temp_by_year = {}
    years = sorted(int(y) for y in emissions_ts.keys())

    for y in years:
        val = emissions_ts.get(str(y), 0)
        if isinstance(val, (int, float)):
            cumulative += val
            temp = BASELINE_TEMP_2020 + cumulative * TCRE
            temp_by_year[y] = round(temp, 3)

    t2050 = temp_by_year.get(2050, temp_by_year.get(max(temp_by_year.keys())) if temp_by_year else None)
    t2100 = temp_by_year.get(2100, temp_by_year.get(max(temp_by_year.keys())) if temp_by_year else None)

    budget_used = cumulative
    p15 = max(0, min(100, round((1 - budget_used / CARBON_BUDGET_1_5C) * 100, 1))) if budget_used > 0 else 50
    p20 = max(0, min(100, round((1 - budget_used / CARBON_BUDGET_2C) * 100 + 30, 1))) if budget_used > 0 else 70

    return {
        "by_2050": t2050,
        "by_2100": t2100,
        "probability_1_5C": max(0, min(100, p15)),
        "probability_2C": max(0, min(100, p20)),
        "trajectory": [{"year": y, "value": v} for y, v in sorted(temp_by_year.items())],
    }


def _calc_economic(gdp_ts, carbon_price_ts):
    """Economic impact assessment."""
    gdp_traj = [{"year": int(y), "value": v} for y, v in sorted((gdp_ts or {}).items()) if isinstance(v, (int, float))]
    cp_traj = [{"year": int(y), "value": v} for y, v in sorted((carbon_price_ts or {}).items()) if isinstance(v, (int, float))]

    cp_2030 = carbon_price_ts.get("2030") if carbon_price_ts else None
    cp_2050 = carbon_price_ts.get("2050") if carbon_price_ts else None

    # Estimate investment needs based on carbon price trajectory
    investment_pct = 0
    if cp_2050 and isinstance(cp_2050, (int, float)):
        investment_pct = round(min(8, cp_2050 / 80), 1)

    return {
        "gdp_trajectory": gdp_traj,
        "carbon_price_trajectory": cp_traj,
        "carbon_price_2030": cp_2030,
        "carbon_price_2050": cp_2050,
        "estimated_investment_pct_gdp": investment_pct,
    }


def _calc_risks(temp_outcome, carbon_price_ts, emissions_ts):
    """Calculate risk scores 1-10."""
    # Physical risk: higher temp → higher physical risk
    t2100 = temp_outcome.get("by_2100") or 2.0
    physical = min(10, max(1, round((t2100 - 1.0) * 3.5, 1)))

    # Transition risk: higher carbon price → higher transition risk
    cp_2050 = 100
    if carbon_price_ts:
        cp_2050 = carbon_price_ts.get("2050", 100)
        if not isinstance(cp_2050, (int, float)):
            cp_2050 = 100
    transition = min(10, max(1, round(cp_2050 / 60, 1)))

    # Overall: weighted average
    overall = round(physical * 0.5 + transition * 0.5, 1)

    return {
        "physical_risk_score": physical,
        "transition_risk_score": transition,
        "overall_climate_risk": overall,
        "physical_risk_label": _risk_label(physical),
        "transition_risk_label": _risk_label(transition),
    }


def _risk_label(score):
    if score <= 2: return "Low"
    if score <= 4: return "Moderate"
    if score <= 6: return "High"
    if score <= 8: return "Very High"
    return "Extreme"


def _calc_energy_indicators(traj_map):
    """Extract energy transition indicators from trajectories."""
    indicators = {}
    for (var, region), ts in traj_map.items():
        if region != "World":
            continue
        vl = var.lower()
        if "renewable" in vl and "share" in vl:
            indicators["renewable_share_2050"] = ts.get("2050")
        elif "coal" in vl and "energy" in vl:
            indicators["coal_2030"] = ts.get("2030")
            indicators["coal_2050"] = ts.get("2050")
        elif "solar" in vl:
            indicators["solar_2050"] = ts.get("2050")
    return indicators


def _build_trajectory_output(ts):
    if not ts:
        return []
    return [{"year": int(y), "value": v} for y, v in sorted(ts.items()) if isinstance(v, (int, float))]
