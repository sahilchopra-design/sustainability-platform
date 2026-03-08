"""
Multi-Scenario Climate Stress Test Runner
==========================================

Implements EBA 2023/2024 EU-wide stress test methodology, ECB/SSM Climate
Stress Test 2022, and NGFS Phase IV scenario framework.

Covers:
  1. Loan book ingestion (per-exposure PD/LGD/EAD + sector/collateral data)
  2. Four scenarios: OPTIMISTIC / BASE / ADVERSE / SEVERE
  3. Sector-level PD multipliers calibrated to four risk tiers
  4. LGD haircuts by collateral type per scenario
  5. IFRS 9 stage migration with SICR threshold (100 bps PD increase)
  6. Stage migration matrix tracking all transitions
  7. 12-month vs lifetime ECL by IFRS 9 stage
  8. Probability-weighted ECL aggregation
  9. Sector concentration analysis
  10. Capital impact estimation (RWA delta + shortfall)

Regulatory references:
  - EBA/GL/2023/02   EU-wide stress test methodological note
  - ECB Climate Risk Stress Test 2022 methodology
  - NGFS Phase IV scenarios (2023)
  - IFRS 9.5.5.3     Significant Increase in Credit Risk
  - IFRS 9.5.5.17    Probability-weighted ECL
  - CRR Article 92   Own funds requirements
  - CRR Article 153  IRB risk-weight function
  - EBA GL/2017/06   Credit risk practices and accounting for ECL

Author: Risk Analytics Platform
Version: 1.0.0
Date: 2026-03-08
"""
from __future__ import annotations

import logging
import math
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# SCENARIO DEFINITIONS
# ---------------------------------------------------------------------------

SCENARIOS: List[str] = ["OPTIMISTIC", "BASE", "ADVERSE", "SEVERE"]

SCENARIO_WEIGHTS: Dict[str, float] = {
    "OPTIMISTIC": 0.10,
    "BASE":       0.40,
    "ADVERSE":    0.35,
    "SEVERE":     0.15,
}

# ---------------------------------------------------------------------------
# PD multipliers: scenario x sector-risk-level
#
# Calibrated from EBA 2023 adverse scenario + NGFS Phase IV transition risk.
# Applied multiplicatively to baseline 12-month PD.
# E.g., ADVERSE + very_high = 3.5x baseline PD.
# ---------------------------------------------------------------------------

SCENARIO_PD_MULTIPLIERS: Dict[str, Dict[str, float]] = {
    "OPTIMISTIC": {
        "low":       0.85,
        "medium":    0.90,
        "high":      0.95,
        "very_high": 0.97,
    },
    "BASE": {
        "low":       1.00,
        "medium":    1.00,
        "high":      1.00,
        "very_high": 1.00,
    },
    "ADVERSE": {
        "low":       1.30,
        "medium":    1.80,
        "high":      2.50,
        "very_high": 3.50,
    },
    "SEVERE": {
        "low":       1.80,
        "medium":    2.60,
        "high":      3.80,
        "very_high": 5.00,
    },
}

# ---------------------------------------------------------------------------
# LGD haircuts (additive) per scenario x collateral type
#
# Based on ECB/SSM 2022 collateral devaluation assumptions.
# Applied additively to baseline LGD. Capped at [0, 1].
# E.g., SEVERE + unsecured = +0.15 additive to baseline LGD.
# ---------------------------------------------------------------------------

SCENARIO_LGD_HAIRCUTS: Dict[str, Dict[str, float]] = {
    "OPTIMISTIC": {
        "property":   -0.02,
        "equipment":  -0.01,
        "financial":  -0.01,
        "unsecured":   0.00,
    },
    "BASE": {
        "property":    0.00,
        "equipment":   0.00,
        "financial":   0.00,
        "unsecured":   0.00,
    },
    "ADVERSE": {
        "property":    0.05,
        "equipment":   0.07,
        "financial":   0.03,
        "unsecured":   0.10,
    },
    "SEVERE": {
        "property":    0.10,
        "equipment":   0.12,
        "financial":   0.06,
        "unsecured":   0.15,
    },
}

# ---------------------------------------------------------------------------
# Sector risk levels -- 18 sectors mapped to four risk tiers
#
# Calibrated against NGFS sector-level transition vulnerability scores.
# ---------------------------------------------------------------------------

SECTOR_RISK_LEVELS: Dict[str, str] = {
    "Oil & Gas":                    "very_high",
    "Coal Mining":                  "very_high",
    "Steel & Metals":               "very_high",
    "Cement & Building Materials":  "high",
    "Chemicals":                    "high",
    "Aviation":                     "high",
    "Shipping & Maritime":          "high",
    "Power Generation":             "high",
    "Agriculture":                  "medium",
    "Automotive":                   "medium",
    "Real Estate":                  "medium",
    "Manufacturing":                "medium",
    "Financial Services":           "medium",
    "Construction":                 "medium",
    "Retail & Consumer":            "low",
    "Technology":                   "low",
    "Healthcare":                   "low",
    "Telecommunications":           "low",
    "Utilities (Renewables)":       "low",
    "Food & Beverage":              "low",
}

# SICR threshold in basis points (IFRS 9.B5.5.9 / EBA GL/2017/06)
SICR_THRESHOLD_BPS: float = 100.0

# Lifetime PD multiplier relative to 12-month PD.
# Simplified assumption: average residual maturity ~4 years.
LIFETIME_PD_FACTOR: float = 3.5

# CRR Article 92 minimum total capital ratio for shortfall computation
MIN_CAPITAL_RATIO: float = 0.08

# IRB output floor (CRR2 Article 92)
RISK_WEIGHT_FLOOR: float = 0.15


# ---------------------------------------------------------------------------
# DATACLASSES
# ---------------------------------------------------------------------------


@dataclass
class LoanBookExposure:
    """Single exposure in the loan book for stress testing."""
    exposure_id: str
    obligor_name: str = ""
    sector: str = "Unclassified"
    collateral_type: str = "unsecured"      # property | equipment | financial | unsecured
    baseline_pd: float = 0.01               # Annualised 12-month PD (0-1)
    baseline_lgd: float = 0.45              # Point-in-time LGD (0-1)
    ead: float = 1_000_000.0                # Exposure At Default
    current_stage: int = 1                  # IFRS 9 stage: 1, 2, or 3
    maturity_years: float = 5.0             # Remaining maturity
    rating_grade: str = ""                  # Internal rating (for reporting)


@dataclass
class ScenarioExposureResult:
    """Per-exposure result under one scenario (populated only when include_detailed=True)."""
    exposure_id: str
    scenario: str
    stressed_pd: float
    stressed_lgd: float
    ead: float
    pd_delta_bps: float
    sicr_triggered: bool
    new_stage: int
    ecl_12m: float
    ecl_lifetime: float
    ecl_applied: float                      # ECL actually booked based on stage
    risk_weight_base: float
    risk_weight_stressed: float


@dataclass
class MigrationMatrix:
    """Stage migration counts for a scenario."""
    scenario: str
    transitions: Dict[str, int] = field(default_factory=dict)
    # Keys: "1->1", "1->2", "1->3", "2->1", "2->2", "2->3", "3->2", "3->3"
    total_exposures: int = 0
    sicr_trigger_count: int = 0
    default_trigger_count: int = 0


@dataclass
class SectorConcentration:
    """Sector-level aggregation for a specific scenario."""
    sector: str
    scenario: str
    exposure_count: int = 0
    total_ead: float = 0.0
    total_ecl_base: float = 0.0
    total_ecl_stressed: float = 0.0
    ecl_uplift_pct: float = 0.0
    concentration_pct: float = 0.0          # Share of total portfolio EAD
    avg_pd_base: float = 0.0
    avg_pd_stressed: float = 0.0


@dataclass
class ScenarioSummary:
    """Portfolio-level stress test summary per scenario."""
    scenario: str
    weight: float
    total_ead: float = 0.0
    total_ecl: float = 0.0
    total_ecl_base: float = 0.0
    ecl_uplift_pct: float = 0.0
    weighted_avg_pd: float = 0.0
    weighted_avg_lgd: float = 0.0
    rwa_impact: float = 0.0
    capital_shortfall: float = 0.0
    stage1_count: int = 0
    stage2_count: int = 0
    stage3_count: int = 0
    exposure_results: List[ScenarioExposureResult] = field(default_factory=list)


@dataclass
class StressTestResult:
    """Complete stress test output."""
    run_id: str
    portfolio_name: str
    scenarios_run: List[str] = field(default_factory=list)
    scenario_summaries: Dict[str, ScenarioSummary] = field(default_factory=dict)
    pw_ecl: float = 0.0
    pw_ecl_base: float = 0.0
    pw_ecl_uplift_pct: float = 0.0
    migration_matrices: Dict[str, MigrationMatrix] = field(default_factory=dict)
    sector_concentrations: Dict[str, List[SectorConcentration]] = field(
        default_factory=dict
    )
    capital_impact_summary: Dict[str, float] = field(default_factory=dict)
    methodology_notes: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------


def _get_sector_risk_level(sector: str) -> str:
    """Map sector name to risk level; default 'medium' if unknown."""
    return SECTOR_RISK_LEVELS.get(sector, "medium")


def _irb_risk_weight(pd: float, lgd: float) -> float:
    """
    Simplified IRB risk-weight function per CRR Article 153.

    Uses Vasicek single-factor model correlation and maturity adjustment.
    Floored at RISK_WEIGHT_FLOOR per CRR2 output floor.
    """
    from scipy.stats import norm

    pd = max(pd, 1e-6)
    pd = min(pd, 1.0 - 1e-6)

    # Asset correlation (corporate exposure class)
    rho = (0.12 * (1.0 - math.exp(-50.0 * pd)) / (1.0 - math.exp(-50.0))
           + 0.24 * (1.0 - (1.0 - math.exp(-50.0 * pd)) / (1.0 - math.exp(-50.0))))

    # Maturity adjustment factor
    b = (0.11852 - 0.05478 * math.log(pd)) ** 2

    # Conditional PD at 99.9th percentile
    conditional_pd = norm.cdf(
        (norm.ppf(pd) + math.sqrt(rho) * norm.ppf(0.999)) / math.sqrt(1.0 - rho)
    )

    # Capital requirement K (assuming effective maturity M = 2.5 years)
    ma = (1.0 + (2.5 - 1.0) * b) / (1.0 - 1.5 * b)
    k = lgd * (conditional_pd - pd) * ma

    rw = k * 12.5
    return max(rw, RISK_WEIGHT_FLOOR)


def _compute_ecl(
    pd_12m: float,
    pd_lifetime: float,
    lgd: float,
    ead: float,
    stage: int,
) -> Tuple[float, float, float]:
    """
    Compute ECL per IFRS 9.

    Stage 1 -> 12-month ECL = PD_12m * LGD * EAD
    Stage 2 -> Lifetime ECL  = PD_lifetime * LGD * EAD
    Stage 3 -> Lifetime ECL  = LGD * EAD  (PD effectively 1.0)

    Returns (ecl_12m, ecl_lifetime, ecl_applied).
    """
    ecl_12m = pd_12m * lgd * ead
    ecl_lifetime = pd_lifetime * lgd * ead

    if stage == 1:
        ecl_applied = ecl_12m
    elif stage == 2:
        ecl_applied = ecl_lifetime
    else:
        # Stage 3: defaulted -- use LGD * EAD (PD = 1.0)
        ecl_applied = lgd * ead

    return ecl_12m, ecl_lifetime, ecl_applied


def _determine_new_stage(
    current_stage: int,
    pd_delta_bps: float,
    stressed_pd: float,
) -> Tuple[int, bool, bool]:
    """
    Determine post-stress IFRS 9 stage.

    SICR trigger: PD increase > SICR_THRESHOLD_BPS  =>  Stage 1 -> 2
    Default trigger: stressed PD >= 1.0  =>  Stage -> 3

    Returns (new_stage, sicr_triggered, default_triggered).
    """
    sicr_triggered = False
    default_triggered = False

    # Default threshold
    if stressed_pd >= 1.0:
        default_triggered = True
        return 3, sicr_triggered, default_triggered

    if current_stage == 1:
        if pd_delta_bps > SICR_THRESHOLD_BPS:
            sicr_triggered = True
            return 2, sicr_triggered, default_triggered
        return 1, sicr_triggered, default_triggered

    if current_stage == 2:
        # Stage 2 can cure back to 1 if PD improvement (Optimistic scenario)
        if pd_delta_bps <= 0:
            return 1, sicr_triggered, default_triggered
        return 2, sicr_triggered, default_triggered

    # Stage 3: stays or cures to 2 only if PD decreases significantly
    if pd_delta_bps < -SICR_THRESHOLD_BPS:
        return 2, sicr_triggered, default_triggered
    return 3, sicr_triggered, default_triggered


# ---------------------------------------------------------------------------
# MAIN RUNNER CLASS
# ---------------------------------------------------------------------------


class StressTestRunner:
    """
    Multi-scenario climate stress test runner.

    Takes a loan book and runs PD/LGD/ECL stress across 4 NGFS-aligned
    scenarios, producing stage migration matrices, sector heatmaps,
    probability-weighted ECL, and capital impact estimates.

    Parameters
    ----------
    scenarios : list of str, optional
        Subset of SCENARIOS to run.  Default: all four.
    include_detailed : bool
        If True, per-exposure results are included in ScenarioSummary.
    """

    def __init__(
        self,
        scenarios: Optional[List[str]] = None,
        include_detailed: bool = False,
    ):
        self.scenarios = scenarios or list(SCENARIOS)
        self.include_detailed = include_detailed

        # Validate requested scenarios
        for s in self.scenarios:
            if s not in SCENARIOS:
                raise ValueError(
                    f"Unknown scenario '{s}'. Valid scenarios: {SCENARIOS}"
                )

    # ------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------

    def run(
        self,
        loan_book: List[LoanBookExposure],
        portfolio_name: str = "Portfolio",
        run_id: Optional[str] = None,
    ) -> StressTestResult:
        """
        Execute stress test across all configured scenarios.

        Parameters
        ----------
        loan_book : list of LoanBookExposure
        portfolio_name : str
        run_id : str, optional -- auto-generated UUID if omitted

        Returns
        -------
        StressTestResult with full breakdown.
        """
        if not loan_book:
            raise ValueError("Loan book must contain at least one exposure.")

        run_id = run_id or f"ST-{uuid.uuid4().hex[:8].upper()}"
        logger.info(
            "Stress test %s started -- %d exposures, scenarios=%s",
            run_id, len(loan_book), self.scenarios,
        )

        total_ead = sum(e.ead for e in loan_book)

        result = StressTestResult(
            run_id=run_id,
            portfolio_name=portfolio_name,
            scenarios_run=list(self.scenarios),
            methodology_notes=self._build_methodology_notes(),
        )

        # Compute baseline (un-stressed) ECL for comparison
        base_ecl_total = self._compute_base_ecl(loan_book)
        result.pw_ecl_base = base_ecl_total

        # Run each scenario
        for scenario in self.scenarios:
            summary, migration, concentrations = self._run_scenario(
                scenario, loan_book, total_ead, base_ecl_total,
            )
            result.scenario_summaries[scenario] = summary
            result.migration_matrices[scenario] = migration
            result.sector_concentrations[scenario] = concentrations

        # Probability-weighted ECL = sum(weight_i * scenario_ECL_i)
        result.pw_ecl = sum(
            SCENARIO_WEIGHTS.get(s, 0.0) * result.scenario_summaries[s].total_ecl
            for s in self.scenarios
        )

        if base_ecl_total > 0:
            result.pw_ecl_uplift_pct = (
                (result.pw_ecl - base_ecl_total) / base_ecl_total * 100.0
            )
        else:
            result.pw_ecl_uplift_pct = 0.0

        # Capital impact summary
        result.capital_impact_summary = self._compute_capital_impact(result)

        logger.info(
            "Stress test %s complete -- PW-ECL = %.2f (uplift %.1f%%)",
            run_id, result.pw_ecl, result.pw_ecl_uplift_pct,
        )
        return result

    # ------------------------------------------------------------------
    # SCENARIO EXECUTION
    # ------------------------------------------------------------------

    def _run_scenario(
        self,
        scenario: str,
        loan_book: List[LoanBookExposure],
        total_ead: float,
        base_ecl_total: float,
    ) -> Tuple[ScenarioSummary, MigrationMatrix, List[SectorConcentration]]:
        """Run a single scenario across the whole loan book."""
        weight = SCENARIO_WEIGHTS.get(scenario, 0.0)
        summary = ScenarioSummary(
            scenario=scenario,
            weight=weight,
            total_ead=total_ead,
        )

        migration = MigrationMatrix(
            scenario=scenario,
            total_exposures=len(loan_book),
        )
        # Initialise all transition counters
        for key in [
            "1->1", "1->2", "1->3",
            "2->1", "2->2", "2->3",
            "3->2", "3->3",
        ]:
            migration.transitions[key] = 0

        # Sector accumulators
        sector_acc: Dict[str, Dict[str, Any]] = {}

        pd_ead_sum = 0.0
        lgd_ead_sum = 0.0
        total_ecl = 0.0
        total_ecl_base_scenario = 0.0

        for exp in loan_book:
            exp_result = self._stress_exposure(scenario, exp)

            # Stage migration tracking
            trans_key = f"{exp.current_stage}->{exp_result.new_stage}"
            if trans_key in migration.transitions:
                migration.transitions[trans_key] += 1

            if exp_result.sicr_triggered:
                migration.sicr_trigger_count += 1
            if exp_result.new_stage == 3 and exp.current_stage != 3:
                migration.default_trigger_count += 1

            # Stage counts
            if exp_result.new_stage == 1:
                summary.stage1_count += 1
            elif exp_result.new_stage == 2:
                summary.stage2_count += 1
            else:
                summary.stage3_count += 1

            # ECL accumulation
            total_ecl += exp_result.ecl_applied

            # Base ECL for this exposure (no stress)
            base_ecl_exp = exp.baseline_pd * exp.baseline_lgd * exp.ead
            total_ecl_base_scenario += base_ecl_exp

            # EAD-weighted PD/LGD for averages
            pd_ead_sum += exp_result.stressed_pd * exp.ead
            lgd_ead_sum += exp_result.stressed_lgd * exp.ead

            # Sector accumulator
            sec = exp.sector
            if sec not in sector_acc:
                sector_acc[sec] = {
                    "count": 0, "ead": 0.0,
                    "ecl_base": 0.0, "ecl_stressed": 0.0,
                    "pd_base_sum": 0.0, "pd_stressed_sum": 0.0,
                }
            sector_acc[sec]["count"] += 1
            sector_acc[sec]["ead"] += exp.ead
            sector_acc[sec]["ecl_base"] += base_ecl_exp
            sector_acc[sec]["ecl_stressed"] += exp_result.ecl_applied
            sector_acc[sec]["pd_base_sum"] += exp.baseline_pd
            sector_acc[sec]["pd_stressed_sum"] += exp_result.stressed_pd

            if self.include_detailed:
                summary.exposure_results.append(exp_result)

        # Finalise summary
        summary.total_ecl = total_ecl
        summary.total_ecl_base = total_ecl_base_scenario
        if total_ecl_base_scenario > 0:
            summary.ecl_uplift_pct = (
                (total_ecl - total_ecl_base_scenario) / total_ecl_base_scenario * 100.0
            )
        summary.weighted_avg_pd = pd_ead_sum / total_ead if total_ead > 0 else 0.0
        summary.weighted_avg_lgd = lgd_ead_sum / total_ead if total_ead > 0 else 0.0

        # RWA / capital impact
        rwa_impact = self._compute_rwa_delta(loan_book, scenario)
        summary.rwa_impact = rwa_impact
        summary.capital_shortfall = rwa_impact * MIN_CAPITAL_RATIO

        # Sector concentrations
        concentrations = self._build_sector_concentrations(
            sector_acc, scenario, total_ead,
        )

        return summary, migration, concentrations

    def _stress_exposure(
        self,
        scenario: str,
        exp: LoanBookExposure,
    ) -> ScenarioExposureResult:
        """Apply scenario stress to a single exposure."""
        risk_level = _get_sector_risk_level(exp.sector)
        pd_mult = SCENARIO_PD_MULTIPLIERS[scenario][risk_level]
        lgd_add = SCENARIO_LGD_HAIRCUTS[scenario].get(exp.collateral_type, 0.0)

        # Stressed PD -- capped at 1.0
        stressed_pd = min(exp.baseline_pd * pd_mult, 1.0)

        # Stressed LGD -- capped [0, 1]
        stressed_lgd = max(min(exp.baseline_lgd + lgd_add, 1.0), 0.0)

        pd_delta_bps = (stressed_pd - exp.baseline_pd) * 10_000.0

        # Stage migration
        new_stage, sicr_triggered, _ = _determine_new_stage(
            exp.current_stage, pd_delta_bps, stressed_pd,
        )

        # Lifetime PD
        pd_lifetime = min(stressed_pd * LIFETIME_PD_FACTOR, 1.0)

        # ECL
        ecl_12m, ecl_lifetime, ecl_applied = _compute_ecl(
            stressed_pd, pd_lifetime, stressed_lgd, exp.ead, new_stage,
        )

        # Risk weights
        rw_base = _irb_risk_weight(exp.baseline_pd, exp.baseline_lgd)
        rw_stressed = _irb_risk_weight(stressed_pd, stressed_lgd)

        return ScenarioExposureResult(
            exposure_id=exp.exposure_id,
            scenario=scenario,
            stressed_pd=stressed_pd,
            stressed_lgd=stressed_lgd,
            ead=exp.ead,
            pd_delta_bps=pd_delta_bps,
            sicr_triggered=sicr_triggered,
            new_stage=new_stage,
            ecl_12m=ecl_12m,
            ecl_lifetime=ecl_lifetime,
            ecl_applied=ecl_applied,
            risk_weight_base=rw_base,
            risk_weight_stressed=rw_stressed,
        )

    # ------------------------------------------------------------------
    # AGGREGATIONS
    # ------------------------------------------------------------------

    def _compute_base_ecl(self, loan_book: List[LoanBookExposure]) -> float:
        """Compute total ECL under BASE (un-stressed) conditions."""
        total = 0.0
        for exp in loan_book:
            pd_lt = min(exp.baseline_pd * LIFETIME_PD_FACTOR, 1.0)
            _, _, ecl = _compute_ecl(
                exp.baseline_pd, pd_lt, exp.baseline_lgd, exp.ead,
                exp.current_stage,
            )
            total += ecl
        return total

    def _compute_rwa_delta(
        self,
        loan_book: List[LoanBookExposure],
        scenario: str,
    ) -> float:
        """Compute change in RWA for a scenario vs baseline.

        RWA_impact = sum(EAD_i * (RW_stressed_i - RW_base_i))
        """
        delta = 0.0
        for exp in loan_book:
            risk_level = _get_sector_risk_level(exp.sector)
            pd_mult = SCENARIO_PD_MULTIPLIERS[scenario][risk_level]
            lgd_add = SCENARIO_LGD_HAIRCUTS[scenario].get(
                exp.collateral_type, 0.0,
            )

            stressed_pd = min(exp.baseline_pd * pd_mult, 1.0)
            stressed_lgd = max(min(exp.baseline_lgd + lgd_add, 1.0), 0.0)

            rw_base = _irb_risk_weight(exp.baseline_pd, exp.baseline_lgd)
            rw_stressed = _irb_risk_weight(stressed_pd, stressed_lgd)

            delta += exp.ead * (rw_stressed - rw_base)
        return delta

    def _build_sector_concentrations(
        self,
        sector_acc: Dict[str, Dict[str, Any]],
        scenario: str,
        total_ead: float,
    ) -> List[SectorConcentration]:
        """Build SectorConcentration list from accumulator dictionary."""
        result = []
        for sector, acc in sector_acc.items():
            uplift = 0.0
            if acc["ecl_base"] > 0:
                uplift = (
                    (acc["ecl_stressed"] - acc["ecl_base"]) / acc["ecl_base"] * 100.0
                )
            conc_pct = (acc["ead"] / total_ead * 100.0) if total_ead > 0 else 0.0
            n = acc["count"]

            result.append(SectorConcentration(
                sector=sector,
                scenario=scenario,
                exposure_count=n,
                total_ead=acc["ead"],
                total_ecl_base=acc["ecl_base"],
                total_ecl_stressed=acc["ecl_stressed"],
                ecl_uplift_pct=uplift,
                concentration_pct=conc_pct,
                avg_pd_base=acc["pd_base_sum"] / n if n > 0 else 0.0,
                avg_pd_stressed=acc["pd_stressed_sum"] / n if n > 0 else 0.0,
            ))
        return sorted(result, key=lambda c: -c.total_ead)

    def _compute_capital_impact(
        self,
        result: StressTestResult,
    ) -> Dict[str, float]:
        """Aggregate capital impact metrics across scenarios."""
        pw_rwa = sum(
            SCENARIO_WEIGHTS.get(s, 0.0) * result.scenario_summaries[s].rwa_impact
            for s in self.scenarios
        )
        return {
            "pw_rwa_impact": pw_rwa,
            "pw_capital_shortfall": pw_rwa * MIN_CAPITAL_RATIO,
            "worst_case_rwa_impact": max(
                (result.scenario_summaries[s].rwa_impact for s in self.scenarios),
                default=0.0,
            ),
            "worst_case_capital_shortfall": max(
                (result.scenario_summaries[s].capital_shortfall
                 for s in self.scenarios),
                default=0.0,
            ),
        }

    # ------------------------------------------------------------------
    # METHODOLOGY NOTES
    # ------------------------------------------------------------------

    @staticmethod
    def _build_methodology_notes() -> List[str]:
        """Return list of methodology notes explaining the calculations."""
        return [
            "Stress test follows EBA 2023/2024 EU-wide stress test methodology.",
            "Four scenarios applied: Optimistic, Base, Adverse, Severe -- "
            "probability-weighted per IFRS 9.5.5.17.",
            "Scenario weights: Optimistic=10%, Base=40%, Adverse=35%, Severe=15%.",
            "PD multipliers are calibrated per sector risk tier "
            "(low/medium/high/very_high) aligned with NGFS Phase IV.",
            "LGD haircuts are additive per collateral class "
            "(property/equipment/financial/unsecured) following ECB/SSM 2022.",
            "SICR threshold set at 100 bps PD increase per IFRS 9.B5.5.9 / "
            "EBA GL/2017/06.",
            "Stage 1 exposures use 12-month ECL = PD_12m * LGD * EAD.",
            "Stage 2/3 exposures use Lifetime ECL = PD_lifetime * LGD * EAD.",
            "Lifetime PD approximated as min(PD_12m * 3.5, 1.0) assuming "
            "average residual maturity of ~4 years.",
            "Stage 3 (defaulted) ECL simplified to LGD * EAD (PD = 1.0).",
            "Risk weights computed via simplified IRB formula "
            "(CRR Article 153, Vasicek single-factor model).",
            "Capital shortfall = delta_RWA * 8% (CRR Article 92 minimum).",
            "Sector risk levels assigned per NGFS transition vulnerability "
            "assessment framework.",
            "Migration matrix tracks all stage transitions "
            "(1->1, 1->2, 1->3, 2->1, 2->2, 2->3, 3->2, 3->3) under each scenario.",
            "Probability-weighted ECL = sum(scenario_weight_i * scenario_ECL_i).",
        ]
