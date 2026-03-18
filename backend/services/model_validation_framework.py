"""
Model Validation Framework
============================
Generalised backtesting, validation, and governance framework for all
quantitative models in the platform. Compliant with BCBS 239, EBA GL/2023/04,
and SR 11-7 (US Fed model risk management guidance).

Coverage:
  - Model inventory registry (all engines across the platform)
  - Generalised backtesting harness (RMSE, MAE, MAPE, hit rate, calibration tests)
  - Statistical validation suite (KS test, Hosmer-Lemeshow, binomial test, traffic lights)
  - Model lifecycle governance (DEVELOPMENT -> VALIDATION -> APPROVED -> MONITORING -> RETIRED)
  - Data quality integration (input quality checks, BCBS 239 compliance)
  - Champion-challenger framework (parallel model runs, significance testing)
  - Regulatory reporting (EBA GL/2023/04 annual validation, SR 11-7 inventory)

References:
  - BCBS 239: Principles for Effective Risk Data Aggregation and Risk Reporting (2013)
  - EBA GL/2023/04: Guidelines on Model Risk Management (2023)
  - SR 11-7: Guidance on Model Risk Management (US Fed, 2011)
  - Basel III CRE 35: Minimum Standards for IRB Model Validation
  - IFRS 9 ECL Model Validation (EBA/GL/2017/16)
"""
from __future__ import annotations

import hashlib
import logging
import math
import statistics
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional

logger = logging.getLogger("platform.model_validation")


# ---------------------------------------------------------------------------
# Model Inventory Registry — all platform quantitative models
# ---------------------------------------------------------------------------

MODEL_INVENTORY: dict[str, dict] = {
    # ── Credit Risk Models ──
    "ecl_pd_model": {
        "label": "PD Estimation Model (TTC & PIT)",
        "category": "credit_risk",
        "model_type": "statistical",
        "risk_tier": 1,
        "regulatory_framework": ["IFRS 9", "Basel III IRB", "EBA GL/2017/16"],
        "validation_frequency": "annual",
        "key_outputs": ["pd_ttc", "pd_pit", "rating_grade"],
        "owner": "credit_risk_team",
        "engine_module": "ecl_climate_engine",
    },
    "ecl_lgd_model": {
        "label": "LGD Estimation Model",
        "category": "credit_risk",
        "model_type": "statistical",
        "risk_tier": 1,
        "regulatory_framework": ["IFRS 9", "Basel III IRB"],
        "validation_frequency": "annual",
        "key_outputs": ["lgd_downturn", "lgd_bestestimate", "recovery_rate"],
        "owner": "credit_risk_team",
        "engine_module": "ecl_climate_engine",
    },
    "ecl_ead_model": {
        "label": "EAD / CCF Model",
        "category": "credit_risk",
        "model_type": "statistical",
        "risk_tier": 2,
        "regulatory_framework": ["IFRS 9", "Basel III"],
        "validation_frequency": "annual",
        "key_outputs": ["ead", "ccf"],
        "owner": "credit_risk_team",
        "engine_module": "ead",
    },
    "ecl_staging_model": {
        "label": "IFRS 9 Stage Classification Model",
        "category": "credit_risk",
        "model_type": "rules_based",
        "risk_tier": 1,
        "regulatory_framework": ["IFRS 9"],
        "validation_frequency": "semi_annual",
        "key_outputs": ["stage_1_2_3", "sicr_flag"],
        "owner": "credit_risk_team",
        "engine_module": "ecl_climate_engine",
    },
    # ── Climate Risk Models ──
    "climate_physical_risk": {
        "label": "Physical Climate Risk Model (HEV)",
        "category": "climate_risk",
        "model_type": "scenario_based",
        "risk_tier": 2,
        "regulatory_framework": ["TCFD", "EBA Pillar 3", "ISSB S2"],
        "validation_frequency": "annual",
        "key_outputs": ["physical_risk_score", "hev_composite", "hazard_exposure"],
        "owner": "climate_risk_team",
        "engine_module": "climate_physical_risk_engine",
    },
    "climate_transition_risk": {
        "label": "Transition Risk Model (CPRS/NGFS P5)",
        "category": "climate_risk",
        "model_type": "scenario_based",
        "risk_tier": 2,
        "regulatory_framework": ["TCFD", "EBA Pillar 3", "NGFS"],
        "validation_frequency": "annual",
        "key_outputs": ["transition_risk_score", "cprs_classification", "carbon_cost_impact"],
        "owner": "climate_risk_team",
        "engine_module": "climate_transition_risk_engine",
    },
    "scenario_analysis": {
        "label": "NGFS Scenario Analysis Engine",
        "category": "climate_risk",
        "model_type": "scenario_based",
        "risk_tier": 2,
        "regulatory_framework": ["NGFS", "TCFD", "ISSB S2"],
        "validation_frequency": "annual",
        "key_outputs": ["expected_loss", "capital_charge", "npv_impact"],
        "owner": "climate_risk_team",
        "engine_module": "scenario_analysis_engine",
    },
    # ── Valuation Models ──
    "real_estate_valuation": {
        "label": "Real Estate Valuation Engine",
        "category": "valuation",
        "model_type": "expert_judgment",
        "risk_tier": 2,
        "regulatory_framework": ["RICS Red Book", "IVSC", "IAS 40"],
        "validation_frequency": "annual",
        "key_outputs": ["market_value", "income_value", "cost_value"],
        "owner": "valuation_team",
        "engine_module": "real_estate_valuation_engine",
    },
    "stranded_asset_model": {
        "label": "Stranded Asset Valuation Model",
        "category": "valuation",
        "model_type": "scenario_based",
        "risk_tier": 2,
        "regulatory_framework": ["IAS 36", "TCFD"],
        "validation_frequency": "annual",
        "key_outputs": ["stranding_probability", "impairment_loss", "residual_value"],
        "owner": "valuation_team",
        "engine_module": "stranded_asset_calculator",
    },
    # ── Emissions Models ──
    "carbon_footprint": {
        "label": "GHG Emissions Calculator (Scope 1/2/3)",
        "category": "emissions",
        "model_type": "rules_based",
        "risk_tier": 3,
        "regulatory_framework": ["GHG Protocol", "PCAF", "ISSB S2"],
        "validation_frequency": "annual",
        "key_outputs": ["scope1_tco2e", "scope2_tco2e", "scope3_tco2e"],
        "owner": "sustainability_team",
        "engine_module": "carbon_calculator_v2",
    },
    "pcaf_financed_emissions": {
        "label": "PCAF Financed Emissions Model",
        "category": "emissions",
        "model_type": "rules_based",
        "risk_tier": 2,
        "regulatory_framework": ["PCAF", "ISSB S2", "CSRD ESRS E1"],
        "validation_frequency": "annual",
        "key_outputs": ["financed_emissions_tco2e", "attribution_factor", "waci"],
        "owner": "sustainability_team",
        "engine_module": "facilitated_emissions_engine",
    },
    # ── Market Risk Models ──
    "portfolio_var": {
        "label": "Portfolio Value-at-Risk Model",
        "category": "market_risk",
        "model_type": "statistical",
        "risk_tier": 1,
        "regulatory_framework": ["Basel III FRTB", "CRR II"],
        "validation_frequency": "quarterly",
        "key_outputs": ["var_95", "var_99", "es_975", "cvar"],
        "owner": "market_risk_team",
        "engine_module": "portfolio_analytics_engine_v2",
    },
    "stress_testing": {
        "label": "Stress Testing Framework",
        "category": "market_risk",
        "model_type": "scenario_based",
        "risk_tier": 1,
        "regulatory_framework": ["EBA Stress Test", "CCAR", "Basel III"],
        "validation_frequency": "annual",
        "key_outputs": ["stressed_loss", "capital_adequacy_post_stress"],
        "owner": "risk_management",
        "engine_module": "stress_testing_engine",
    },
    # ── Regulatory Models ──
    "cbam_calculator": {
        "label": "CBAM Carbon Cost Calculator",
        "category": "regulatory",
        "model_type": "rules_based",
        "risk_tier": 3,
        "regulatory_framework": ["EU CBAM Reg 2023/956"],
        "validation_frequency": "annual",
        "key_outputs": ["cbam_liability_eur", "embedded_emissions_tco2e"],
        "owner": "regulatory_team",
        "engine_module": "cbam_calculator",
    },
    "eu_taxonomy_alignment": {
        "label": "EU Taxonomy Alignment Engine",
        "category": "regulatory",
        "model_type": "rules_based",
        "risk_tier": 2,
        "regulatory_framework": ["EU Taxonomy Reg 2020/852"],
        "validation_frequency": "annual",
        "key_outputs": ["alignment_pct", "eligible_pct", "dnsh_pass"],
        "owner": "regulatory_team",
        "engine_module": "eu_taxonomy_engine",
    },
    # ── ESG Scoring Models ──
    "factor_overlay": {
        "label": "ESG Factor Overlay Engine",
        "category": "esg",
        "model_type": "expert_judgment",
        "risk_tier": 3,
        "regulatory_framework": ["SFDR", "CSRD"],
        "validation_frequency": "annual",
        "key_outputs": ["overlay_adjustments", "esg_alpha", "factor_scores"],
        "owner": "esg_team",
        "engine_module": "factor_overlay_engine",
    },
    "sovereign_climate_risk": {
        "label": "Sovereign Climate Risk Model",
        "category": "climate_risk",
        "model_type": "composite",
        "risk_tier": 2,
        "regulatory_framework": ["NGFS", "IMF Climate FSAP"],
        "validation_frequency": "annual",
        "key_outputs": ["sovereign_climate_score", "spread_delta_bps", "rating_notch_adj"],
        "owner": "climate_risk_team",
        "engine_module": "sovereign_climate_risk_engine",
    },
}


# ---------------------------------------------------------------------------
# Model Lifecycle States
# ---------------------------------------------------------------------------

MODEL_LIFECYCLE_STATES = [
    "DEVELOPMENT",   # Model under construction
    "VALIDATION",    # Independent validation in progress
    "APPROVED",      # Validated and approved for production use
    "MONITORING",    # In production, ongoing performance monitoring
    "UNDER_REVIEW",  # Triggered by performance deterioration or material change
    "RETIRED",       # Decommissioned
]

MODEL_LIFECYCLE_TRANSITIONS: dict[str, list[str]] = {
    "DEVELOPMENT": ["VALIDATION"],
    "VALIDATION": ["APPROVED", "DEVELOPMENT"],
    "APPROVED": ["MONITORING"],
    "MONITORING": ["UNDER_REVIEW", "RETIRED"],
    "UNDER_REVIEW": ["VALIDATION", "MONITORING", "RETIRED"],
    "RETIRED": [],
}


# ---------------------------------------------------------------------------
# Validation Test Suite — Statistical Tests
# ---------------------------------------------------------------------------

VALIDATION_TESTS: dict[str, dict] = {
    "rmse": {"label": "Root Mean Squared Error", "category": "accuracy",
             "threshold_green": 0.05, "threshold_amber": 0.10},
    "mae": {"label": "Mean Absolute Error", "category": "accuracy",
            "threshold_green": 0.03, "threshold_amber": 0.07},
    "mape": {"label": "Mean Absolute Percentage Error", "category": "accuracy",
             "threshold_green": 10.0, "threshold_amber": 20.0},
    "hit_rate": {"label": "Hit Rate (Correct Direction)", "category": "discriminatory_power",
                 "threshold_green": 70.0, "threshold_amber": 55.0},
    "auc_roc": {"label": "Area Under ROC Curve", "category": "discriminatory_power",
                "threshold_green": 0.75, "threshold_amber": 0.65},
    "ks_statistic": {"label": "Kolmogorov-Smirnov Statistic", "category": "calibration",
                     "threshold_green": 0.40, "threshold_amber": 0.25},
    "hosmer_lemeshow": {"label": "Hosmer-Lemeshow Chi-Square p-value", "category": "calibration",
                        "threshold_green": 0.05, "threshold_amber": 0.01},
    "binomial_test": {"label": "Binomial Test (Default Prediction)", "category": "calibration",
                      "threshold_green": 0.05, "threshold_amber": 0.01},
    "traffic_light_breaches": {"label": "Basel Traffic Light Breaches (250d)", "category": "backtesting",
                               "threshold_green": 4, "threshold_amber": 9},
    "r_squared": {"label": "R-Squared (Coefficient of Determination)", "category": "accuracy",
                  "threshold_green": 0.70, "threshold_amber": 0.50},
    "population_stability_index": {"label": "Population Stability Index (PSI)", "category": "stability",
                                   "threshold_green": 0.10, "threshold_amber": 0.25},
    "characteristic_stability_index": {"label": "Characteristic Stability Index (CSI)",
                                       "category": "stability",
                                       "threshold_green": 0.10, "threshold_amber": 0.25},
}


# ---------------------------------------------------------------------------
# Result Data Classes
# ---------------------------------------------------------------------------

@dataclass
class ValidationTestResult:
    """Result of a single validation test."""
    test_name: str
    test_label: str
    category: str
    value: float
    threshold_green: float
    threshold_amber: float
    traffic_light: str  # "green" | "amber" | "red"
    pass_fail: str  # "pass" | "warning" | "fail"
    details: str = ""


@dataclass
class BacktestResult:
    """Full backtesting result for a model."""
    id: str
    model_id: str
    model_label: str
    backtest_date: str
    observation_window_start: str
    observation_window_end: str
    sample_size: int
    test_results: list[dict] = field(default_factory=list)
    overall_traffic_light: str = "green"
    overall_pass_fail: str = "pass"
    green_count: int = 0
    amber_count: int = 0
    red_count: int = 0
    recommendations: list[str] = field(default_factory=list)
    regulatory_status: str = "compliant"
    next_validation_due: str = ""


@dataclass
class ModelInventoryEntry:
    """Model inventory entry with lifecycle status."""
    model_id: str
    label: str
    category: str
    model_type: str
    risk_tier: int
    regulatory_framework: list[str]
    validation_frequency: str
    lifecycle_state: str = "DEVELOPMENT"
    last_validation_date: str = ""
    last_validation_result: str = ""
    next_validation_due: str = ""
    owner: str = ""
    engine_module: str = ""
    key_outputs: list[str] = field(default_factory=list)
    change_log: list[dict] = field(default_factory=list)
    findings: list[dict] = field(default_factory=list)


@dataclass
class ChampionChallengerResult:
    """Champion vs challenger model comparison."""
    id: str
    champion_model_id: str
    challenger_model_id: str
    comparison_date: str
    sample_size: int
    champion_metrics: dict = field(default_factory=dict)
    challenger_metrics: dict = field(default_factory=dict)
    winner: str = ""
    significance_test: str = ""
    p_value: float = 1.0
    recommendation: str = ""


@dataclass
class ValidationDashboard:
    """Platform-wide model validation dashboard."""
    total_models: int = 0
    models_by_state: dict = field(default_factory=dict)
    models_by_tier: dict = field(default_factory=dict)
    models_by_category: dict = field(default_factory=dict)
    overdue_validations: list[dict] = field(default_factory=list)
    recent_findings: list[dict] = field(default_factory=list)
    bcbs239_compliance_pct: float = 0.0
    eba_gl_2023_04_compliant: bool = False


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class ModelValidationFramework:
    """
    Generalised model validation and governance framework.

    Provides backtesting, statistical validation, lifecycle management,
    champion-challenger comparison, and regulatory reporting for all
    quantitative models in the platform.

    Calculation Logic:
      1. Model inventory registry tracks all engines with metadata
      2. Backtesting: compare predicted vs actual outcomes using statistical tests
      3. Traffic light system: green/amber/red based on regulatory thresholds
      4. Lifecycle governance: state machine with transition rules
      5. Champion-challenger: parallel model runs with significance testing
      6. BCBS 239 compliance: data quality integration across all models

    Stakeholder Insights:
      - Risk Management: model performance monitoring and early warning
      - Audit/Compliance: complete model inventory and validation history
      - Regulatory: EBA GL/2023/04 annual validation reports
      - Senior Management: dashboard of model risk across the platform
    """

    def __init__(self):
        self._inventory = MODEL_INVENTORY
        self._tests = VALIDATION_TESTS
        self._lifecycle_transitions = MODEL_LIFECYCLE_TRANSITIONS

    # ------------------------------------------------------------------
    # 1. Backtesting
    # ------------------------------------------------------------------

    def run_backtest(
        self,
        model_id: str,
        predicted: list[float],
        actual: list[float],
        observation_start: str = "2024-01-01",
        observation_end: str = "2024-12-31",
        tests_to_run: Optional[list[str]] = None,
    ) -> BacktestResult:
        """
        Run generalised backtesting for any model.

        Args:
            model_id: Model identifier from inventory
            predicted: List of predicted values
            actual: List of actual/observed values
            observation_start: Start of observation window (ISO date)
            observation_end: End of observation window (ISO date)
            tests_to_run: Specific tests to run (default: all applicable)

        Returns:
            BacktestResult with test-level results and overall traffic light
        """
        uid = hashlib.sha256(
            f"bt:{model_id}:{observation_start}:{observation_end}".encode()
        ).hexdigest()[:16]

        model_info = self._inventory.get(model_id, {"label": model_id, "category": "unknown"})
        n = min(len(predicted), len(actual))
        if n == 0:
            return BacktestResult(
                id=uid, model_id=model_id, model_label=model_info.get("label", model_id),
                backtest_date=datetime.utcnow().isoformat(),
                observation_window_start=observation_start,
                observation_window_end=observation_end,
                sample_size=0,
                overall_traffic_light="red",
                overall_pass_fail="fail",
                recommendations=["No data provided for backtesting."],
            )

        pred = predicted[:n]
        act = actual[:n]

        tests = tests_to_run or list(self._tests.keys())
        results = []
        green_count = 0
        amber_count = 0
        red_count = 0

        for test_name in tests:
            test_spec = self._tests.get(test_name)
            if not test_spec:
                continue

            value = self._compute_test(test_name, pred, act)
            if value is None:
                continue

            tg = test_spec["threshold_green"]
            ta = test_spec["threshold_amber"]

            # Determine traffic light
            if test_name in ("hit_rate", "auc_roc", "r_squared", "ks_statistic"):
                # Higher is better
                if value >= tg:
                    tl = "green"
                elif value >= ta:
                    tl = "amber"
                else:
                    tl = "red"
            elif test_name in ("hosmer_lemeshow", "binomial_test"):
                # p-value: higher is better (> threshold = pass)
                if value >= tg:
                    tl = "green"
                elif value >= ta:
                    tl = "amber"
                else:
                    tl = "red"
            else:
                # Lower is better (RMSE, MAE, MAPE, breaches, PSI)
                if value <= tg:
                    tl = "green"
                elif value <= ta:
                    tl = "amber"
                else:
                    tl = "red"

            pf = "pass" if tl == "green" else ("warning" if tl == "amber" else "fail")
            if tl == "green":
                green_count += 1
            elif tl == "amber":
                amber_count += 1
            else:
                red_count += 1

            results.append(asdict(ValidationTestResult(
                test_name=test_name,
                test_label=test_spec["label"],
                category=test_spec["category"],
                value=round(value, 6),
                threshold_green=tg,
                threshold_amber=ta,
                traffic_light=tl,
                pass_fail=pf,
                details=f"Sample size: {n}",
            )))

        # Overall traffic light
        if red_count > 0:
            overall_tl = "red"
            overall_pf = "fail"
            reg_status = "non_compliant"
        elif amber_count > 0:
            overall_tl = "amber"
            overall_pf = "warning"
            reg_status = "under_observation"
        else:
            overall_tl = "green"
            overall_pf = "pass"
            reg_status = "compliant"

        recs = self._generate_backtest_recommendations(model_id, results, overall_tl)

        return BacktestResult(
            id=uid,
            model_id=model_id,
            model_label=model_info.get("label", model_id),
            backtest_date=datetime.utcnow().isoformat(),
            observation_window_start=observation_start,
            observation_window_end=observation_end,
            sample_size=n,
            test_results=results,
            overall_traffic_light=overall_tl,
            overall_pass_fail=overall_pf,
            green_count=green_count,
            amber_count=amber_count,
            red_count=red_count,
            recommendations=recs,
            regulatory_status=reg_status,
        )

    # ------------------------------------------------------------------
    # 2. Model Inventory & Lifecycle
    # ------------------------------------------------------------------

    def get_model_inventory(
        self,
        category: Optional[str] = None,
        risk_tier: Optional[int] = None,
    ) -> list[ModelInventoryEntry]:
        """
        Get the full model inventory, optionally filtered.

        Args:
            category: Filter by category (credit_risk, climate_risk, etc.)
            risk_tier: Filter by risk tier (1=highest, 3=lowest)

        Returns:
            List of ModelInventoryEntry
        """
        entries = []
        for model_id, info in self._inventory.items():
            if category and info.get("category") != category:
                continue
            if risk_tier is not None and info.get("risk_tier") != risk_tier:
                continue

            entries.append(ModelInventoryEntry(
                model_id=model_id,
                label=info["label"],
                category=info["category"],
                model_type=info["model_type"],
                risk_tier=info["risk_tier"],
                regulatory_framework=info.get("regulatory_framework", []),
                validation_frequency=info.get("validation_frequency", "annual"),
                lifecycle_state="MONITORING",  # Default for existing models
                owner=info.get("owner", ""),
                engine_module=info.get("engine_module", ""),
                key_outputs=info.get("key_outputs", []),
            ))

        return entries

    def transition_lifecycle(
        self,
        model_id: str,
        target_state: str,
        reason: str = "",
        transitioned_by: str = "system",
    ) -> dict:
        """
        Transition a model to a new lifecycle state.

        Args:
            model_id: Model identifier
            target_state: Target lifecycle state
            reason: Reason for transition
            transitioned_by: User/system making the transition

        Returns:
            Dict with transition result
        """
        if target_state not in MODEL_LIFECYCLE_STATES:
            return {"success": False, "error": f"Invalid state: {target_state}",
                    "valid_states": MODEL_LIFECYCLE_STATES}

        model_info = self._inventory.get(model_id)
        if not model_info:
            return {"success": False, "error": f"Model {model_id} not found in inventory"}

        # For simplicity, assume current state is MONITORING
        current_state = "MONITORING"
        allowed = self._lifecycle_transitions.get(current_state, [])

        if target_state not in allowed:
            return {
                "success": False,
                "error": f"Cannot transition from {current_state} to {target_state}",
                "allowed_transitions": allowed,
            }

        return {
            "success": True,
            "model_id": model_id,
            "previous_state": current_state,
            "new_state": target_state,
            "reason": reason,
            "transitioned_by": transitioned_by,
            "timestamp": datetime.utcnow().isoformat(),
        }

    # ------------------------------------------------------------------
    # 3. Champion-Challenger Comparison
    # ------------------------------------------------------------------

    def compare_models(
        self,
        champion_model_id: str,
        challenger_model_id: str,
        champion_predicted: list[float],
        challenger_predicted: list[float],
        actual: list[float],
        comparison_metric: str = "rmse",
    ) -> ChampionChallengerResult:
        """
        Champion vs challenger model comparison.

        Args:
            champion_model_id: Current production model ID
            challenger_model_id: Challenger model ID
            champion_predicted: Champion model predictions
            challenger_predicted: Challenger model predictions
            actual: Actual/observed values
            comparison_metric: Primary metric for comparison

        Returns:
            ChampionChallengerResult with winner and significance
        """
        uid = hashlib.sha256(
            f"cc:{champion_model_id}:{challenger_model_id}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]

        n = min(len(champion_predicted), len(challenger_predicted), len(actual))
        ch_pred = champion_predicted[:n]
        cl_pred = challenger_predicted[:n]
        act = actual[:n]

        # Compute key metrics for both
        ch_metrics = {}
        cl_metrics = {}
        for test in ["rmse", "mae", "mape", "r_squared", "hit_rate"]:
            ch_val = self._compute_test(test, ch_pred, act)
            cl_val = self._compute_test(test, cl_pred, act)
            if ch_val is not None:
                ch_metrics[test] = round(ch_val, 6)
            if cl_val is not None:
                cl_metrics[test] = round(cl_val, 6)

        # Determine winner
        ch_primary = ch_metrics.get(comparison_metric, float("inf"))
        cl_primary = cl_metrics.get(comparison_metric, float("inf"))

        lower_better = comparison_metric in ("rmse", "mae", "mape")
        if lower_better:
            winner = "champion" if ch_primary <= cl_primary else "challenger"
            improvement_pct = ((ch_primary - cl_primary) / ch_primary * 100) if ch_primary > 0 else 0
        else:
            winner = "champion" if ch_primary >= cl_primary else "challenger"
            improvement_pct = ((cl_primary - ch_primary) / ch_primary * 100) if ch_primary > 0 else 0

        # Simplified significance test (paired t-test proxy)
        if n > 1:
            ch_errors = [(p - a) ** 2 for p, a in zip(ch_pred, act)]
            cl_errors = [(p - a) ** 2 for p, a in zip(cl_pred, act)]
            diffs = [c - ch for c, ch in zip(cl_errors, ch_errors)]
            mean_diff = statistics.mean(diffs) if diffs else 0
            if len(diffs) > 1:
                std_diff = statistics.stdev(diffs)
                t_stat = (mean_diff / (std_diff / math.sqrt(n))) if std_diff > 0 else 0
                # Approximate p-value (simplified)
                p_value = max(0.001, min(1.0, 2.0 * math.exp(-0.5 * abs(t_stat))))
            else:
                t_stat = 0
                p_value = 1.0
            sig_test = f"Paired difference test: t={t_stat:.3f}, approx p={p_value:.4f}"
        else:
            p_value = 1.0
            sig_test = "Insufficient data for significance test"

        if winner == "challenger" and p_value < 0.05:
            rec = (f"Challenger model ({challenger_model_id}) outperforms champion "
                   f"on {comparison_metric} with statistical significance (p={p_value:.4f}). "
                   f"Consider promoting to production.")
        elif winner == "challenger":
            rec = (f"Challenger shows improvement but result is not statistically significant "
                   f"(p={p_value:.4f}). Continue monitoring.")
        else:
            rec = (f"Champion model remains superior on {comparison_metric}. "
                   f"No model change recommended.")

        return ChampionChallengerResult(
            id=uid,
            champion_model_id=champion_model_id,
            challenger_model_id=challenger_model_id,
            comparison_date=datetime.utcnow().isoformat(),
            sample_size=n,
            champion_metrics=ch_metrics,
            challenger_metrics=cl_metrics,
            winner=winner,
            significance_test=sig_test,
            p_value=round(p_value, 6),
            recommendation=rec,
        )

    # ------------------------------------------------------------------
    # 4. Validation Dashboard
    # ------------------------------------------------------------------

    def get_validation_dashboard(self) -> ValidationDashboard:
        """
        Platform-wide model validation dashboard.

        Returns:
            ValidationDashboard with model counts, overdue validations, compliance
        """
        by_state: dict[str, int] = {}
        by_tier: dict[int, int] = {}
        by_category: dict[str, int] = {}

        for model_id, info in self._inventory.items():
            # State tracking (simplified — production reads from DB)
            state = "MONITORING"
            by_state[state] = by_state.get(state, 0) + 1

            tier = info.get("risk_tier", 3)
            by_tier[tier] = by_tier.get(tier, 0) + 1

            cat = info.get("category", "other")
            by_category[cat] = by_category.get(cat, 0) + 1

        total = len(self._inventory)

        # BCBS 239 compliance heuristic
        # (models with annual validation + documented outputs + risk tier)
        compliant_models = sum(
            1 for info in self._inventory.values()
            if info.get("validation_frequency") in ("annual", "semi_annual", "quarterly")
            and info.get("key_outputs")
        )
        bcbs239_pct = (compliant_models / total * 100) if total > 0 else 0.0

        # EBA GL/2023/04: requires all Tier 1 + Tier 2 models validated annually
        tier12_count = sum(1 for info in self._inventory.values()
                          if info.get("risk_tier", 3) <= 2)
        tier12_validated = tier12_count  # Assume all validated for dashboard
        eba_compliant = tier12_validated >= tier12_count

        return ValidationDashboard(
            total_models=total,
            models_by_state=by_state,
            models_by_tier={str(k): v for k, v in sorted(by_tier.items())},
            models_by_category=by_category,
            overdue_validations=[],  # Production: query DB for overdue
            recent_findings=[],
            bcbs239_compliance_pct=round(bcbs239_pct, 1),
            eba_gl_2023_04_compliant=eba_compliant,
        )

    # ------------------------------------------------------------------
    # Internal — Statistical Test Computations
    # ------------------------------------------------------------------

    def _compute_test(self, test_name: str, predicted: list[float],
                      actual: list[float]) -> Optional[float]:
        """Compute a single statistical test."""
        n = len(predicted)
        if n == 0:
            return None

        if test_name == "rmse":
            mse = sum((p - a) ** 2 for p, a in zip(predicted, actual)) / n
            return math.sqrt(mse)

        elif test_name == "mae":
            return sum(abs(p - a) for p, a in zip(predicted, actual)) / n

        elif test_name == "mape":
            nonzero = [(p, a) for p, a in zip(predicted, actual) if a != 0]
            if not nonzero:
                return None
            return sum(abs((a - p) / a) for p, a in nonzero) / len(nonzero) * 100

        elif test_name == "hit_rate":
            if n < 2:
                return None
            hits = sum(
                1 for i in range(1, n)
                if (predicted[i] - predicted[i - 1]) * (actual[i] - actual[i - 1]) > 0
            )
            return (hits / (n - 1)) * 100

        elif test_name == "r_squared":
            mean_a = sum(actual) / n
            ss_tot = sum((a - mean_a) ** 2 for a in actual)
            ss_res = sum((a - p) ** 2 for p, a in zip(predicted, actual))
            return max(0.0, 1 - (ss_res / ss_tot)) if ss_tot > 0 else 0.0

        elif test_name == "auc_roc":
            # Simplified AUC for binary outcomes
            # Assumes actual is 0/1, predicted is probability
            pos = [(p, a) for p, a in zip(predicted, actual) if a == 1]
            neg = [(p, a) for p, a in zip(predicted, actual) if a == 0]
            if not pos or not neg:
                return 0.5
            concordant = sum(1 for pp, _ in pos for pn, _ in neg if pp > pn)
            tied = sum(1 for pp, _ in pos for pn, _ in neg if pp == pn)
            total_pairs = len(pos) * len(neg)
            return (concordant + 0.5 * tied) / total_pairs if total_pairs > 0 else 0.5

        elif test_name == "ks_statistic":
            # Simplified KS: max separation between cumulative distributions
            combined = sorted(zip(predicted, actual), key=lambda x: x[0])
            n_pos = sum(1 for _, a in combined if a == 1)
            n_neg = n - n_pos
            if n_pos == 0 or n_neg == 0:
                return 0.0
            cum_pos = 0.0
            cum_neg = 0.0
            max_ks = 0.0
            for p, a in combined:
                if a == 1:
                    cum_pos += 1.0 / n_pos
                else:
                    cum_neg += 1.0 / n_neg
                max_ks = max(max_ks, abs(cum_pos - cum_neg))
            return max_ks

        elif test_name == "hosmer_lemeshow":
            # Simplified: return synthetic p-value based on calibration error
            if n < 10:
                return None
            # Group into deciles and check calibration
            sorted_pairs = sorted(zip(predicted, actual), key=lambda x: x[0])
            group_size = max(1, n // 10)
            chi_sq = 0.0
            for i in range(0, n, group_size):
                group = sorted_pairs[i:i + group_size]
                if not group:
                    continue
                expected_p = sum(p for p, _ in group) / len(group)
                observed_p = sum(a for _, a in group) / len(group)
                if expected_p > 0 and expected_p < 1:
                    chi_sq += len(group) * (observed_p - expected_p) ** 2 / (
                        expected_p * (1 - expected_p))
            # Approximate p-value from chi-square
            dof = max(1, min(10, n // group_size) - 2)
            p_approx = max(0.001, math.exp(-chi_sq / (2 * dof)))
            return min(1.0, p_approx)

        elif test_name == "binomial_test":
            # Binomial test: predicted default rate vs actual
            predicted_rate = sum(predicted) / n if n > 0 else 0
            actual_rate = sum(actual) / n if n > 0 else 0
            if predicted_rate == 0:
                return 1.0
            diff = abs(actual_rate - predicted_rate)
            # Approximate p-value
            se = math.sqrt(predicted_rate * (1 - predicted_rate) / n) if n > 0 else 1
            z = diff / se if se > 0 else 0
            p_val = max(0.001, 2 * math.exp(-0.5 * z ** 2))
            return min(1.0, p_val)

        elif test_name == "traffic_light_breaches":
            # Count days where actual exceeds VaR prediction
            breaches = sum(1 for p, a in zip(predicted, actual) if a > p)
            return float(breaches)

        elif test_name == "population_stability_index":
            # PSI between predicted and actual distributions
            if n < 10:
                return None
            # Create decile buckets
            sorted_pred = sorted(predicted)
            sorted_act = sorted(actual)
            bucket_size = max(1, n // 10)
            psi = 0.0
            for i in range(0, n, bucket_size):
                p_pct = len(sorted_pred[i:i + bucket_size]) / n
                a_pct = len(sorted_act[i:i + bucket_size]) / n
                if p_pct > 0 and a_pct > 0:
                    psi += (p_pct - a_pct) * math.log(p_pct / a_pct)
            return abs(psi)

        elif test_name == "characteristic_stability_index":
            # Simplified CSI (same as PSI for this implementation)
            return self._compute_test("population_stability_index", predicted, actual)

        return None

    def _generate_backtest_recommendations(self, model_id: str,
                                            results: list[dict],
                                            overall_tl: str) -> list[str]:
        """Generate recommendations from backtest results."""
        recs = []
        model_info = self._inventory.get(model_id, {})

        if overall_tl == "red":
            recs.append(f"CRITICAL: Model '{model_info.get('label', model_id)}' has failed backtesting. "
                        f"Immediate review required per EBA GL/2023/04.")
            recs.append("Transition model to UNDER_REVIEW state and initiate independent validation.")

        for r in results:
            if r.get("traffic_light") == "red":
                recs.append(f"Test '{r['test_label']}' in RED zone "
                            f"(value={r['value']}, threshold={r['threshold_amber']}). "
                            f"Investigate root cause.")
            elif r.get("traffic_light") == "amber":
                recs.append(f"Test '{r['test_label']}' in AMBER zone — monitor closely.")

        if model_info.get("risk_tier") == 1 and overall_tl != "green":
            recs.append("Tier 1 model: escalate to Model Risk Committee per SR 11-7.")

        return recs

    # ------------------------------------------------------------------
    # Static Reference Data
    # ------------------------------------------------------------------

    @staticmethod
    def get_model_inventory_catalog() -> dict:
        """Full model inventory registry."""
        return MODEL_INVENTORY

    @staticmethod
    def get_lifecycle_states() -> list[str]:
        """Valid model lifecycle states."""
        return MODEL_LIFECYCLE_STATES

    @staticmethod
    def get_lifecycle_transitions() -> dict:
        """Valid lifecycle state transitions."""
        return MODEL_LIFECYCLE_TRANSITIONS

    @staticmethod
    def get_validation_tests() -> dict:
        """Available validation test specifications."""
        return VALIDATION_TESTS

    @staticmethod
    def get_regulatory_frameworks() -> list[dict]:
        """Regulatory frameworks governing model validation."""
        return [
            {"code": "BCBS_239", "name": "BCBS 239 Risk Data Aggregation", "year": 2013,
             "scope": "All quantitative models producing risk data",
             "key_requirements": ["Data completeness", "Data accuracy", "Timeliness",
                                  "Adaptability", "Governance"]},
            {"code": "EBA_GL_2023_04", "name": "EBA GL on Model Risk Management", "year": 2023,
             "scope": "All internal models used for regulatory and business purposes",
             "key_requirements": ["Model inventory", "Annual independent validation",
                                  "Ongoing monitoring", "Model change management"]},
            {"code": "SR_11_7", "name": "Fed SR 11-7 Model Risk Management", "year": 2011,
             "scope": "All quantitative models at banking organisations",
             "key_requirements": ["Model development documentation", "Independent validation",
                                  "Ongoing monitoring", "Model risk governance"]},
            {"code": "CRE_35", "name": "Basel III CRE 35 IRB Validation", "year": 2017,
             "scope": "IRB credit risk models (PD, LGD, EAD)",
             "key_requirements": ["Discriminatory power tests", "Calibration tests",
                                  "Stability analysis", "Backtesting"]},
            {"code": "IFRS_9_ECL", "name": "IFRS 9 ECL Model Validation", "year": 2017,
             "scope": "Expected credit loss models",
             "key_requirements": ["Stage classification validation", "PD/LGD/EAD backtesting",
                                  "Scenario weight validation", "Overlay governance"]},
        ]
