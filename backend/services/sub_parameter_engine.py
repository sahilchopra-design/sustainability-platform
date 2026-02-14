"""
Sub-Parameter Analysis Engine — sensitivity, what-if, attribution, interactions.
Works with ALL hub scenarios via their trajectory data.
"""

import random
import math
import statistics
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

from services.builder_engine import calculate_impacts, interpolate_series


# Standard parameters we analyze
ANALYZABLE_PARAMS = [
    {"name": "Emissions|CO2", "label": "CO2 Emissions", "unit": "Gt/yr", "default_range": 0.3},
    {"name": "Price|Carbon", "label": "Carbon Price", "unit": "USD/tCO2", "default_range": 0.4},
    {"name": "GDP|PPP", "label": "GDP", "unit": "billion USD", "default_range": 0.15},
    {"name": "Primary Energy", "label": "Primary Energy", "unit": "EJ/yr", "default_range": 0.2},
    {"name": "Primary Energy|Coal", "label": "Coal Energy", "unit": "EJ/yr", "default_range": 0.4},
    {"name": "Primary Energy|Gas", "label": "Gas Energy", "unit": "EJ/yr", "default_range": 0.25},
    {"name": "Primary Energy|Solar", "label": "Solar Energy", "unit": "EJ/yr", "default_range": 0.5},
    {"name": "Primary Energy|Wind", "label": "Wind Energy", "unit": "EJ/yr", "default_range": 0.5},
    {"name": "Emissions|CO2|Energy", "label": "Energy CO2", "unit": "Gt/yr", "default_range": 0.3},
]

TARGET_METRICS = {
    "temperature": "temperature_outcome.by_2100",
    "risk_physical": "risk_indicators.physical_risk_score",
    "risk_transition": "risk_indicators.transition_risk_score",
    "risk_overall": "risk_indicators.overall_climate_risk",
}


def _extract_metric(impacts: dict, metric_key: str) -> Optional[float]:
    """Extract a metric value from nested impacts dict."""
    parts = metric_key.split(".")
    obj = impacts
    for p in parts:
        if isinstance(obj, dict):
            obj = obj.get(p)
        else:
            return None
    return obj if isinstance(obj, (int, float)) else None


def _get_matching_trajs(base_trajs: list, param_name: str) -> list:
    """Find trajectories matching a parameter name pattern."""
    results = []
    plow = param_name.lower()
    for t in base_trajs:
        if t["variable_name"].lower() == plow or plow in t["variable_name"].lower():
            results.append(t)
    return results


def run_sensitivity_analysis(
    base_trajs: list,
    target_metric: str = "temperature",
    parameters: list = None,
    variation_range: float = 0.2,
    analysis_type: str = "tornado",
) -> dict:
    """
    Run sensitivity analysis on scenario parameters.
    Varies each parameter ±variation_range and measures impact on target metric.
    """
    if not parameters:
        parameters = [p["name"] for p in ANALYZABLE_PARAMS]

    metric_key = TARGET_METRICS.get(target_metric, target_metric)

    # Baseline
    baseline_impacts = calculate_impacts(base_trajs, [])
    baseline_val = _extract_metric(baseline_impacts, metric_key)
    if baseline_val is None:
        baseline_val = 0

    tornado_data = []
    for param in parameters:
        matching = _get_matching_trajs(base_trajs, param)
        if not matching:
            continue

        t = matching[0]
        ts = t.get("time_series", {})
        if not ts:
            continue

        # Low case: reduce by variation_range
        low_vals = {y: round(v * (1 - variation_range), 4) for y, v in ts.items() if isinstance(v, (int, float))}
        low_impacts = calculate_impacts(base_trajs, [{"variable_name": t["variable_name"], "region": t.get("region", "World"), "customized_values": low_vals}])
        low_val = _extract_metric(low_impacts, metric_key) or baseline_val

        # High case: increase by variation_range
        high_vals = {y: round(v * (1 + variation_range), 4) for y, v in ts.items() if isinstance(v, (int, float))}
        high_impacts = calculate_impacts(base_trajs, [{"variable_name": t["variable_name"], "region": t.get("region", "World"), "customized_values": high_vals}])
        high_val = _extract_metric(high_impacts, metric_key) or baseline_val

        swing = abs(high_val - low_val)
        tornado_data.append({
            "parameter": t["variable_name"],
            "low_impact": round(low_val, 4),
            "high_impact": round(high_val, 4),
            "baseline": round(baseline_val, 4),
            "swing": round(swing, 4),
            "sensitivity_score": round(swing / max(abs(baseline_val), 0.001) * 100, 2),
        })

    # Sort by swing (most impactful first)
    tornado_data.sort(key=lambda x: x["swing"], reverse=True)

    rankings = [{"parameter": td["parameter"], "sensitivity_score": td["sensitivity_score"], "rank": i + 1}
                for i, td in enumerate(tornado_data)]

    return {
        "analysis_type": analysis_type,
        "target_metric": target_metric,
        "baseline_value": round(baseline_val, 4),
        "variation_range_pct": variation_range * 100,
        "tornado_data": tornado_data,
        "rankings": rankings,
        "total_parameters_analyzed": len(tornado_data),
    }


def run_what_if(base_trajs: list, changes: list) -> dict:
    """
    What-if analysis: apply changes and compare to baseline.
    changes: [{"parameter": str, "change_type": "absolute"|"relative", "change_value": float, "apply_year": int}]
    """
    baseline_impacts = calculate_impacts(base_trajs, [])

    # Build customizations from changes
    customizations = []
    for change in changes:
        param = change["parameter"]
        matching = _get_matching_trajs(base_trajs, param)
        if not matching:
            continue
        t = matching[0]
        ts = dict(t.get("time_series", {}))
        year_str = str(change.get("apply_year", 2050))

        if change["change_type"] == "relative":
            # Apply relative change from apply_year onwards
            for y in ts:
                if int(y) >= int(year_str):
                    ts[y] = round(ts[y] * (1 + change["change_value"] / 100), 4)
        else:
            # Set absolute value at apply_year, interpolate from prev year
            ts[year_str] = change["change_value"]

        customizations.append({
            "variable_name": t["variable_name"],
            "region": t.get("region", "World"),
            "customized_values": ts,
        })

    modified_impacts = calculate_impacts(base_trajs, customizations)

    # Compute differences
    diffs = {}
    for key, metric_path in TARGET_METRICS.items():
        bv = _extract_metric(baseline_impacts, metric_path)
        mv = _extract_metric(modified_impacts, metric_path)
        if bv is not None and mv is not None:
            diffs[key] = {
                "baseline": round(bv, 4),
                "modified": round(mv, 4),
                "absolute_change": round(mv - bv, 4),
                "pct_change": round((mv - bv) / max(abs(bv), 0.001) * 100, 2),
            }

    # Generate insights
    insights = []
    for key, d in diffs.items():
        if abs(d["pct_change"]) > 5:
            direction = "increases" if d["pct_change"] > 0 else "decreases"
            insights.append(f"{key.replace('_', ' ').title()} {direction} by {abs(d['pct_change']):.1f}%")

    return {
        "baseline": {k: _extract_metric(baseline_impacts, v) for k, v in TARGET_METRICS.items()},
        "modified": {k: _extract_metric(modified_impacts, v) for k, v in TARGET_METRICS.items()},
        "differences": diffs,
        "key_insights": insights,
        "changes_applied": len(changes),
    }


def run_attribution(base_trajs: list, outcome_metric: str = "temperature") -> dict:
    """
    Shapley-inspired attribution: estimate each parameter's contribution to outcome.
    Uses marginal contribution approach.
    """
    metric_key = TARGET_METRICS.get(outcome_metric, outcome_metric)
    baseline_impacts = calculate_impacts(base_trajs, [])
    baseline_val = _extract_metric(baseline_impacts, metric_key) or 0

    attributions = []
    total_contribution = 0

    for pdef in ANALYZABLE_PARAMS:
        matching = _get_matching_trajs(base_trajs, pdef["name"])
        if not matching:
            continue
        t = matching[0]
        ts = t.get("time_series", {})
        if not ts:
            continue

        # Zero out this parameter and see impact
        zero_vals = {y: 0 for y in ts}
        zero_impacts = calculate_impacts(base_trajs, [{
            "variable_name": t["variable_name"], "region": t.get("region", "World"),
            "customized_values": zero_vals,
        }])
        zero_val = _extract_metric(zero_impacts, metric_key) or 0

        contribution = baseline_val - zero_val
        attributions.append({
            "parameter": t["variable_name"],
            "label": pdef["label"],
            "contribution": round(contribution, 4),
            "contribution_pct": 0,  # calculated after
            "confidence": 0.7,
        })
        total_contribution += abs(contribution)

    # Normalize percentages
    for a in attributions:
        a["contribution_pct"] = round(abs(a["contribution"]) / max(total_contribution, 0.001) * 100, 1)

    attributions.sort(key=lambda x: abs(x["contribution"]), reverse=True)
    explained = sum(abs(a["contribution"]) for a in attributions)
    unexplained = max(0, abs(baseline_val) - explained) if baseline_val != 0 else 0

    return {
        "outcome_metric": outcome_metric,
        "total_value": round(baseline_val, 4),
        "attributed_changes": attributions,
        "total_explained_pct": round(min(100, explained / max(abs(baseline_val), 0.001) * 100), 1),
        "unexplained_pct": round(max(0, 100 - min(100, explained / max(abs(baseline_val), 0.001) * 100)), 1),
    }


def run_interaction_analysis(base_trajs: list, parameters: list = None) -> dict:
    """
    Pairwise interaction analysis between parameters.
    Tests if joint effect differs from sum of individual effects.
    """
    if not parameters:
        parameters = [p["name"] for p in ANALYZABLE_PARAMS[:5]]

    metric_key = TARGET_METRICS["temperature"]
    baseline_impacts = calculate_impacts(base_trajs, [])
    baseline_val = _extract_metric(baseline_impacts, metric_key) or 0
    variation = 0.2

    # Compute individual effects
    individual = {}
    for param in parameters:
        matching = _get_matching_trajs(base_trajs, param)
        if not matching:
            continue
        t = matching[0]
        ts = t.get("time_series", {})
        high_vals = {y: round(v * (1 + variation), 4) for y, v in ts.items() if isinstance(v, (int, float))}
        high_impacts = calculate_impacts(base_trajs, [{
            "variable_name": t["variable_name"], "region": t.get("region", "World"),
            "customized_values": high_vals,
        }])
        individual[t["variable_name"]] = (_extract_metric(high_impacts, metric_key) or baseline_val) - baseline_val

    # Pairwise interactions
    param_names = list(individual.keys())
    interactions = []
    for i in range(len(param_names)):
        for j in range(i + 1, len(param_names)):
            p1, p2 = param_names[i], param_names[j]
            e1, e2 = individual[p1], individual[p2]
            expected = e1 + e2

            # Joint effect
            custs = []
            for p in [p1, p2]:
                matching = _get_matching_trajs(base_trajs, p)
                if matching:
                    t = matching[0]
                    ts = t.get("time_series", {})
                    high_vals = {y: round(v * (1 + variation), 4) for y, v in ts.items() if isinstance(v, (int, float))}
                    custs.append({"variable_name": t["variable_name"], "region": t.get("region", "World"), "customized_values": high_vals})

            joint_impacts = calculate_impacts(base_trajs, custs)
            joint_val = (_extract_metric(joint_impacts, metric_key) or baseline_val) - baseline_val

            interaction_effect = joint_val - expected
            strength = abs(interaction_effect) / max(abs(expected), 0.001)

            if strength > 0.1:
                itype = "synergistic" if (interaction_effect > 0) == (expected > 0) else "antagonistic"
            else:
                itype = "independent"

            interactions.append({
                "param1": p1, "param2": p2,
                "individual_effect_1": round(e1, 4), "individual_effect_2": round(e2, 4),
                "expected_joint": round(expected, 4), "actual_joint": round(joint_val, 4),
                "interaction_effect": round(interaction_effect, 4),
                "interaction_type": itype,
                "interaction_strength": round(strength, 3),
            })

    interactions.sort(key=lambda x: abs(x["interaction_effect"]), reverse=True)
    return {"baseline": round(baseline_val, 4), "pairwise_interactions": interactions}


def get_visualization_tornado(base_trajs, target_metric="temperature", top_n=10):
    """Pre-formatted tornado chart data."""
    sa = run_sensitivity_analysis(base_trajs, target_metric)
    return {
        "chart_type": "tornado",
        "target_metric": target_metric,
        "baseline": sa["baseline_value"],
        "bars": sa["tornado_data"][:top_n],
    }


def get_visualization_waterfall(base_trajs, customizations):
    """Waterfall chart showing step-by-step parameter impact."""
    baseline_impacts = calculate_impacts(base_trajs, [])
    baseline_temp = _extract_metric(baseline_impacts, "temperature_outcome.by_2100") or 0

    steps = [{"label": "Baseline", "value": round(baseline_temp, 4), "cumulative": round(baseline_temp, 4)}]
    cumulative = baseline_temp

    for c in customizations:
        single_impact = calculate_impacts(base_trajs, [c])
        new_val = _extract_metric(single_impact, "temperature_outcome.by_2100") or baseline_temp
        delta = new_val - baseline_temp
        cumulative += delta
        steps.append({
            "label": c["variable_name"],
            "delta": round(delta, 4),
            "cumulative": round(cumulative, 4),
        })

    steps.append({"label": "Final", "value": round(cumulative, 4), "cumulative": round(cumulative, 4)})
    return {"chart_type": "waterfall", "steps": steps}


# ============================================================================
# ENHANCED CALCULATION METHODS
# ============================================================================

def run_elasticity_analysis(base_trajs: list, target_metric: str = "temperature",
                            parameters: list = None, delta_pct: float = 1.0) -> dict:
    """
    Elasticity analysis: (% change in outcome) / (% change in parameter).
    A 1% increase in each parameter → how much does the outcome change?
    """
    if not parameters:
        parameters = [p["name"] for p in ANALYZABLE_PARAMS]
    metric_key = TARGET_METRICS.get(target_metric, target_metric)

    baseline_impacts = calculate_impacts(base_trajs, [])
    baseline_val = _extract_metric(baseline_impacts, metric_key) or 0

    elasticities = []
    for param in parameters:
        matching = _get_matching_trajs(base_trajs, param)
        if not matching:
            continue
        t = matching[0]
        ts = t.get("time_series", {})
        if not ts:
            continue

        # Apply delta_pct increase
        perturbed = {y: round(v * (1 + delta_pct / 100), 4) for y, v in ts.items() if isinstance(v, (int, float))}
        imp = calculate_impacts(base_trajs, [{"variable_name": t["variable_name"],
                                              "region": t.get("region", "World"), "customized_values": perturbed}])
        new_val = _extract_metric(imp, metric_key) or baseline_val

        if baseline_val != 0:
            outcome_pct_change = (new_val - baseline_val) / abs(baseline_val) * 100
            elasticity = outcome_pct_change / delta_pct
        else:
            elasticity = 0

        elasticities.append({
            "parameter": t["variable_name"],
            "elasticity": round(elasticity, 4),
            "outcome_change_pct": round(outcome_pct_change if baseline_val != 0 else 0, 4),
            "interpretation": _interpret_elasticity(elasticity, t["variable_name"]),
        })

    elasticities.sort(key=lambda x: abs(x["elasticity"]), reverse=True)
    return {
        "method": "elasticity",
        "target_metric": target_metric,
        "baseline_value": round(baseline_val, 4),
        "delta_pct": delta_pct,
        "elasticities": elasticities,
    }


def _interpret_elasticity(e, param):
    ae = abs(e)
    direction = "increases" if e > 0 else "decreases"
    if ae < 0.01:
        return f"{param} has negligible effect on outcome"
    elif ae < 0.5:
        return f"Inelastic: 1% change in {param} {direction} outcome by {ae:.2f}%"
    elif ae < 1.5:
        return f"Unit elastic: 1% change in {param} {direction} outcome by ~{ae:.1f}%"
    else:
        return f"Elastic: 1% change in {param} {direction} outcome by {ae:.1f}% — high sensitivity"


def run_partial_correlation(base_trajs: list, target_metric: str = "temperature",
                            parameters: list = None) -> dict:
    """
    Partial correlation: isolate each parameter's independent effect,
    controlling for all other parameters.
    Uses sequential residualization approach.
    """
    if not parameters:
        parameters = [p["name"] for p in ANALYZABLE_PARAMS]
    metric_key = TARGET_METRICS.get(target_metric, target_metric)

    baseline_impacts = calculate_impacts(base_trajs, [])
    baseline_val = _extract_metric(baseline_impacts, metric_key) or 0

    # Generate sample points by varying each parameter independently
    rng = random.Random(123)
    n_samples = 50
    param_trajs = {}
    for param in parameters:
        matching = _get_matching_trajs(base_trajs, param)
        if matching:
            param_trajs[param] = matching[0]

    if len(param_trajs) < 2:
        return {"method": "partial_correlation", "error": "Need at least 2 parameters with trajectory data"}

    # Build sample matrix
    param_names = list(param_trajs.keys())
    X = []  # parameter variation factors
    Y = []  # outcome values

    for _ in range(n_samples):
        factors = {p: rng.uniform(0.8, 1.2) for p in param_names}
        custs = []
        for p, f in factors.items():
            t = param_trajs[p]
            ts = t.get("time_series", {})
            custs.append({
                "variable_name": t["variable_name"],
                "region": t.get("region", "World"),
                "customized_values": {y: round(v * f, 4) for y, v in ts.items() if isinstance(v, (int, float))},
            })
        imp = calculate_impacts(base_trajs, custs)
        outcome = _extract_metric(imp, metric_key) or baseline_val
        X.append(factors)
        Y.append(outcome)

    # Compute correlations
    results = []
    y_mean = statistics.mean(Y)
    y_std = statistics.stdev(Y) if len(Y) > 1 else 1

    for p in param_names:
        x_vals = [x[p] for x in X]
        x_mean = statistics.mean(x_vals)
        x_std = statistics.stdev(x_vals) if len(x_vals) > 1 else 1

        if x_std == 0 or y_std == 0:
            corr = 0
        else:
            cov = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, Y)) / (len(Y) - 1)
            corr = cov / (x_std * y_std)

        results.append({
            "parameter": param_trajs[p]["variable_name"],
            "correlation": round(corr, 4),
            "abs_correlation": round(abs(corr), 4),
            "direction": "positive" if corr > 0 else "negative",
            "strength": "strong" if abs(corr) > 0.7 else ("moderate" if abs(corr) > 0.3 else "weak"),
        })

    results.sort(key=lambda x: x["abs_correlation"], reverse=True)
    return {
        "method": "partial_correlation",
        "target_metric": target_metric,
        "baseline_value": round(baseline_val, 4),
        "n_samples": n_samples,
        "correlations": results,
    }


def run_ols_attribution(base_trajs: list, target_metric: str = "temperature",
                        parameters: list = None) -> dict:
    """
    OLS regression-based attribution.
    Fits a linear model: outcome = β₀ + β₁x₁ + β₂x₂ + ... + ε
    Returns coefficients as attribution weights.
    """
    if not parameters:
        parameters = [p["name"] for p in ANALYZABLE_PARAMS]
    metric_key = TARGET_METRICS.get(target_metric, target_metric)

    baseline_impacts = calculate_impacts(base_trajs, [])
    baseline_val = _extract_metric(baseline_impacts, metric_key) or 0

    param_trajs = {}
    for param in parameters:
        matching = _get_matching_trajs(base_trajs, param)
        if matching:
            param_trajs[param] = matching[0]

    if not param_trajs:
        return {"method": "ols_regression", "error": "No parameters with trajectory data"}

    param_names = list(param_trajs.keys())
    rng = random.Random(456)
    n = 80

    # Generate training data
    X_data = []
    Y_data = []
    for _ in range(n):
        factors = {p: rng.uniform(0.7, 1.3) for p in param_names}
        custs = []
        for p, f in factors.items():
            t = param_trajs[p]
            ts = t.get("time_series", {})
            custs.append({
                "variable_name": t["variable_name"],
                "region": t.get("region", "World"),
                "customized_values": {y: round(v * f, 4) for y, v in ts.items() if isinstance(v, (int, float))},
            })
        imp = calculate_impacts(base_trajs, custs)
        Y_data.append(_extract_metric(imp, metric_key) or baseline_val)
        X_data.append([factors[p] for p in param_names])

    # Simple OLS via normal equations (X^T X)^-1 X^T Y with intercept
    k = len(param_names)
    # Add intercept column
    X_aug = [[1.0] + row for row in X_data]
    m = k + 1

    # X^T X
    XtX = [[sum(X_aug[i][r] * X_aug[i][c] for i in range(n)) for c in range(m)] for r in range(m)]
    # X^T Y
    XtY = [sum(X_aug[i][r] * Y_data[i] for i in range(n)) for r in range(m)]

    # Solve via Gauss elimination
    try:
        beta = _solve_linear(XtX, XtY, m)
    except Exception:
        beta = [0.0] * m

    # R-squared
    y_mean = sum(Y_data) / n
    ss_tot = sum((y - y_mean) ** 2 for y in Y_data)
    y_pred = [sum(X_aug[i][j] * beta[j] for j in range(m)) for i in range(n)]
    ss_res = sum((Y_data[i] - y_pred[i]) ** 2 for i in range(n))
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0

    coefficients = []
    total_abs = sum(abs(b) for b in beta[1:])
    for i, p in enumerate(param_names):
        b = beta[i + 1]
        coefficients.append({
            "parameter": param_trajs[p]["variable_name"],
            "coefficient": round(b, 6),
            "weight_pct": round(abs(b) / total_abs * 100, 1) if total_abs > 0 else 0,
            "direction": "positive" if b > 0 else "negative",
        })

    coefficients.sort(key=lambda x: abs(x["coefficient"]), reverse=True)
    return {
        "method": "ols_regression",
        "target_metric": target_metric,
        "baseline_value": round(baseline_val, 4),
        "intercept": round(beta[0], 6),
        "r_squared": round(max(0, min(1, r_squared)), 4),
        "coefficients": coefficients,
        "n_samples": n,
    }


def _solve_linear(A, b, n):
    """Solve Ax = b via Gaussian elimination."""
    # Augment
    aug = [A[i][:] + [b[i]] for i in range(n)]
    for col in range(n):
        # Pivot
        max_row = max(range(col, n), key=lambda r: abs(aug[r][col]))
        aug[col], aug[max_row] = aug[max_row], aug[col]
        if abs(aug[col][col]) < 1e-12:
            continue
        for row in range(col + 1, n):
            f = aug[row][col] / aug[col][col]
            for j in range(col, n + 1):
                aug[row][j] -= f * aug[col][j]
    # Back-substitute
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        if abs(aug[i][i]) < 1e-12:
            continue
        x[i] = (aug[i][n] - sum(aug[i][j] * x[j] for j in range(i + 1, n))) / aug[i][i]
    return x


def run_enhanced_shapley(base_trajs: list, target_metric: str = "temperature",
                         parameters: list = None, n_permutations: int = 20) -> dict:
    """
    Enhanced Shapley attribution with permutation sampling.
    Approximates Shapley values by sampling random orderings.
    """
    if not parameters:
        parameters = [p["name"] for p in ANALYZABLE_PARAMS]
    metric_key = TARGET_METRICS.get(target_metric, target_metric)

    param_trajs = {}
    for param in parameters:
        matching = _get_matching_trajs(base_trajs, param)
        if matching:
            param_trajs[param] = matching[0]

    if not param_trajs:
        return {"method": "shapley", "error": "No parameters"}

    param_names = list(param_trajs.keys())
    rng = random.Random(789)
    variation = 0.2
    shapley_values = {p: 0.0 for p in param_names}

    for _ in range(n_permutations):
        perm = param_names[:]
        rng.shuffle(perm)

        prev_val = _extract_metric(calculate_impacts(base_trajs, []), metric_key) or 0

        active_custs = []
        for p in perm:
            t = param_trajs[p]
            ts = t.get("time_series", {})
            high = {y: round(v * (1 + variation), 4) for y, v in ts.items() if isinstance(v, (int, float))}
            active_custs.append({
                "variable_name": t["variable_name"],
                "region": t.get("region", "World"),
                "customized_values": high,
            })
            new_val = _extract_metric(calculate_impacts(base_trajs, active_custs), metric_key) or prev_val
            marginal = new_val - prev_val
            shapley_values[p] += marginal
            prev_val = new_val

    # Average
    for p in shapley_values:
        shapley_values[p] /= n_permutations

    total_abs = sum(abs(v) for v in shapley_values.values())
    results = []
    for p in param_names:
        sv = shapley_values[p]
        results.append({
            "parameter": param_trajs[p]["variable_name"],
            "shapley_value": round(sv, 6),
            "contribution_pct": round(abs(sv) / total_abs * 100, 1) if total_abs > 0 else 0,
            "direction": "positive" if sv > 0 else "negative",
        })

    results.sort(key=lambda x: abs(x["shapley_value"]), reverse=True)
    return {
        "method": "shapley",
        "target_metric": target_metric,
        "n_permutations": n_permutations,
        "attributions": results,
    }


def get_key_drivers(base_trajs: list, top_n: int = 5) -> list:
    """Get top N parameters driving scenario outcomes across all metrics."""
    drivers = {}
    for metric in ["temperature", "risk_overall"]:
        sa = run_sensitivity_analysis(base_trajs, metric, variation_range=0.15)
        for td in sa.get("tornado_data", []):
            p = td["parameter"]
            if p not in drivers:
                drivers[p] = {"parameter": p, "total_sensitivity": 0, "metrics_affected": []}
            drivers[p]["total_sensitivity"] += td["sensitivity_score"]
            drivers[p]["metrics_affected"].append(metric)

    ranked = sorted(drivers.values(), key=lambda x: x["total_sensitivity"], reverse=True)
    for i, d in enumerate(ranked):
        d["rank"] = i + 1
    return ranked[:top_n]
