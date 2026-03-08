"""
PD Model Backtesting Engine
============================

Regulatory-grade PD model backtesting per:
  - EBA GL/2017/16  PD estimation, LGD estimation, treatment of defaulted exposures
  - ECB TRIM Guide  Chapter 4 -- PD model validation
  - BCBS d350       Regulatory capital -- IRB minimum requirements
  - Basel CRE 36.88-36.97  Validation of internal estimates
  - SR 11-7 (Fed)   Guidance on Model Risk Management

Metrics implemented:
  1. Gini Coefficient / Accuracy Ratio (discriminatory power)
  2. AUROC via trapezoidal rule on ROC curve
  3. Kolmogorov-Smirnov (KS) statistic (scipy.stats.ks_2samp)
  4. Brier Score + Brier Skill Score (calibration)
  5. Hosmer-Lemeshow chi-squared GOF (scipy.stats.chi2)
  6. Information Value (IV) with Laplace smoothing
  7. Per-grade binomial test (scipy.stats.binom) with EBA traffic lights
  8. Overall traffic light per EBA GL/2017/16

Author: Risk Analytics Platform
Version: 1.0.0
Date: 2026-03-08
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats as scipy_stats

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# QUALITY THRESHOLDS
# ---------------------------------------------------------------------------

GINI_THRESHOLDS: Dict[str, float] = {
    "excellent":  0.60,
    "good":       0.40,
    "acceptable": 0.25,
    "poor":       0.00,      # below 0.25
}

IV_THRESHOLDS: Dict[str, float] = {
    "very_strong": 0.50,
    "strong":      0.30,
    "medium":      0.10,
    "weak":        0.02,
    "useless":     0.00,     # below 0.02
}

# EBA GL/2017/16 Annex I -- binomial test significance thresholds
TRAFFIC_LIGHT_THRESHOLDS: Dict[str, str] = {
    "GREEN":  "p-value >= 0.05",
    "YELLOW": "0.01 <= p-value < 0.05",
    "RED":    "p-value < 0.01",
}


# ---------------------------------------------------------------------------
# DATACLASSES
# ---------------------------------------------------------------------------


@dataclass
class ObservedDefault:
    """Single observation for PD backtesting: predicted PD vs actual outcome."""
    exposure_id: str
    rating_grade: str               # Internal rating grade (AAA..D)
    predicted_pd: float             # Model-predicted PD (0-1)
    actual_default: int             # 1 = defaulted, 0 = non-default
    exposure_amount: float = 0.0
    sector: str = ""
    vintage_year: int = 0


@dataclass
class GradeBacktestResult:
    """Per-rating-grade backtest result with binomial traffic light."""
    grade: str
    count: int
    default_count: int
    observed_default_rate: float
    predicted_pd_avg: float
    binomial_p_value: float
    traffic_light: str              # GREEN, YELLOW, RED
    prediction_error_pct: float


@dataclass
class BacktestMetrics:
    """Complete PD backtest metrics."""
    # Discriminatory power
    gini_coefficient: float
    auroc: float
    ks_statistic: float
    ks_p_value: float

    # Calibration
    brier_score: float
    brier_skill_score: float        # 1 - brier / brier_reference
    hosmer_lemeshow_chi2: float
    hosmer_lemeshow_p_value: float
    hosmer_lemeshow_df: int

    # Information value
    information_value: float
    iv_interpretation: str           # Useless / Weak / Medium / Strong / Very Strong

    # Per-grade traffic light results
    grade_results: List[GradeBacktestResult]
    overall_traffic_light: str       # GREEN, YELLOW, RED

    # Summary statistics
    total_observations: int
    total_defaults: int
    overall_default_rate: float
    avg_predicted_pd: float
    prediction_error_pct: float

    # Curve data for plotting
    cap_curve: List[Tuple[float, float]]    # (cumulative_pct, cumulative_default_pct)
    roc_curve: List[Tuple[float, float]]    # (FPR, TPR)

    # Regulatory assessment
    model_valid: bool
    validation_issues: List[str]
    methodology_notes: List[str]


# ---------------------------------------------------------------------------
# MAIN BACKTESTER CLASS
# ---------------------------------------------------------------------------


class PDBacktester:
    """
    Regulatory-grade PD model backtesting engine.

    Given a set of observations (predicted PD + actual default outcome),
    computes comprehensive discriminatory power, calibration, and
    goodness-of-fit metrics per EBA/ECB/BCBS standards.

    Parameters
    ----------
    n_buckets : int
        Number of buckets for Hosmer-Lemeshow test.  Default 10.
    confidence_level : float
        Confidence level for binomial test.  Default 0.95.
    """

    # Minimum observations required per EBA GL/2017/16
    MIN_OBSERVATIONS: int = 30

    def __init__(
        self,
        n_buckets: int = 10,
        confidence_level: float = 0.95,
    ):
        self.n_buckets = n_buckets
        self.confidence_level = confidence_level

    # ------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------

    def backtest(
        self,
        observations: List[ObservedDefault],
    ) -> BacktestMetrics:
        """
        Run full PD backtest suite.

        Parameters
        ----------
        observations : list of ObservedDefault
            Minimum 30 observations required.

        Returns
        -------
        BacktestMetrics

        Raises
        ------
        ValueError
            If fewer than 30 observations provided.
        """
        if len(observations) < self.MIN_OBSERVATIONS:
            raise ValueError(
                f"Minimum {self.MIN_OBSERVATIONS} observations required for "
                f"backtesting (received {len(observations)})."
            )

        notes: List[str] = []
        issues: List[str] = []

        pds = np.array([o.predicted_pd for o in observations])
        defaults = np.array([o.actual_default for o in observations])

        n = len(observations)
        n_defaults = int(defaults.sum())
        overall_dr = n_defaults / n if n > 0 else 0.0
        avg_pd = float(pds.mean())

        notes.append(
            f"Backtesting {n} observations: {n_defaults} defaults "
            f"({overall_dr:.2%} observed vs {avg_pd:.2%} predicted)"
        )

        # 1. Gini / AUROC
        auroc, roc_data = self._compute_auroc(pds, defaults)
        gini = 2.0 * auroc - 1.0
        notes.append(f"AUROC = {auroc:.4f}, Gini = {gini:.4f}")

        if gini < GINI_THRESHOLDS["acceptable"]:
            issues.append(
                f"Gini coefficient {gini:.4f} below acceptable threshold "
                f"({GINI_THRESHOLDS['acceptable']})."
            )

        # 2. KS Statistic
        ks_stat, ks_pval = self._compute_ks(pds, defaults)
        notes.append(f"KS statistic = {ks_stat:.4f}, p-value = {ks_pval:.4f}")

        # 3. Brier Score
        brier, brier_skill = self._compute_brier(pds, defaults, overall_dr)
        notes.append(f"Brier score = {brier:.6f}, skill score = {brier_skill:.4f}")

        # 4. Hosmer-Lemeshow
        hl_chi2, hl_pval, hl_df = self._compute_hosmer_lemeshow(
            pds, defaults, self.n_buckets,
        )
        notes.append(
            f"Hosmer-Lemeshow chi2 = {hl_chi2:.4f}, p-value = {hl_pval:.4f}"
        )

        if hl_pval < 0.05:
            issues.append(
                f"Hosmer-Lemeshow test rejects calibration (p = {hl_pval:.4f})."
            )

        # 5. Information Value
        iv, iv_label = self._compute_information_value(pds, defaults)
        notes.append(f"Information Value = {iv:.4f} ({iv_label})")

        # 6. Per-grade backtest with traffic lights
        grade_results = self._backtest_by_grade(observations)
        overall_tl = self._overall_traffic_light(grade_results)

        # 7. CAP curve
        cap_data = self._compute_cap_curve(pds, defaults)

        # Prediction error
        pred_error = (
            ((avg_pd - overall_dr) / overall_dr * 100.0)
            if overall_dr > 0 else 0.0
        )

        # Model validity assessment
        model_valid = (
            gini >= GINI_THRESHOLDS["acceptable"]
            and overall_tl != "RED"
            and hl_pval >= 0.01
        )

        if not model_valid:
            issues.append(
                "Model fails minimum validation standards -- "
                "recalibration recommended."
            )

        return BacktestMetrics(
            gini_coefficient=round(gini, 4),
            auroc=round(auroc, 4),
            ks_statistic=round(ks_stat, 4),
            ks_p_value=round(ks_pval, 4),
            brier_score=round(brier, 6),
            brier_skill_score=round(brier_skill, 4),
            hosmer_lemeshow_chi2=round(hl_chi2, 4),
            hosmer_lemeshow_p_value=round(hl_pval, 4),
            hosmer_lemeshow_df=hl_df,
            information_value=round(iv, 4),
            iv_interpretation=iv_label,
            grade_results=grade_results,
            overall_traffic_light=overall_tl,
            total_observations=n,
            total_defaults=n_defaults,
            overall_default_rate=round(overall_dr, 6),
            avg_predicted_pd=round(avg_pd, 6),
            prediction_error_pct=round(pred_error, 2),
            cap_curve=cap_data,
            roc_curve=roc_data,
            model_valid=model_valid,
            validation_issues=issues,
            methodology_notes=notes,
        )

    # ------------------------------------------------------------------
    # METRIC IMPLEMENTATIONS
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_auroc(
        pds: np.ndarray,
        defaults: np.ndarray,
    ) -> Tuple[float, List[Tuple[float, float]]]:
        """
        Compute AUROC using trapezoidal rule on ROC curve.

        Sort by predicted PD descending.  Higher PD = more likely default.
        Returns (auroc, roc_points) where roc_points = [(fpr, tpr), ...].
        """
        n = len(pds)
        if n == 0 or defaults.sum() == 0 or defaults.sum() == n:
            return 0.5, [(0.0, 0.0), (1.0, 1.0)]

        order = np.argsort(-pds)
        sorted_defaults = defaults[order]

        n_pos = float(defaults.sum())
        n_neg = float(n - n_pos)

        tpr_arr = np.cumsum(sorted_defaults) / n_pos
        fpr_arr = np.cumsum(1 - sorted_defaults) / n_neg

        # Prepend origin
        tpr_arr = np.concatenate([[0.0], tpr_arr])
        fpr_arr = np.concatenate([[0.0], fpr_arr])

        # AUROC via trapezoidal rule
        auroc = float(np.trapz(tpr_arr, fpr_arr))
        auroc = max(0.0, min(1.0, auroc))

        # Sample up to 100 points for curve
        step = max(1, len(tpr_arr) // 100)
        roc_points = [
            (round(float(fpr_arr[i]), 4), round(float(tpr_arr[i]), 4))
            for i in range(0, len(tpr_arr), step)
        ]
        if roc_points[-1] != (1.0, 1.0):
            roc_points.append((1.0, 1.0))

        return auroc, roc_points

    @staticmethod
    def _compute_ks(
        pds: np.ndarray,
        defaults: np.ndarray,
    ) -> Tuple[float, float]:
        """
        Compute Kolmogorov-Smirnov statistic.

        Maximum separation between cumulative default and non-default
        PD distributions.  Uses scipy.stats.ks_2samp.
        """
        default_pds = pds[defaults == 1]
        non_default_pds = pds[defaults == 0]

        if len(default_pds) == 0 or len(non_default_pds) == 0:
            return 0.0, 1.0

        ks_stat, ks_pval = scipy_stats.ks_2samp(default_pds, non_default_pds)
        return float(ks_stat), float(ks_pval)

    @staticmethod
    def _compute_brier(
        pds: np.ndarray,
        defaults: np.ndarray,
        base_rate: float,
    ) -> Tuple[float, float]:
        """
        Compute Brier Score and Brier Skill Score.

        Brier = mean((predicted_pd - actual_default)^2)
        Brier_reference = base_rate * (1 - base_rate)
        Brier Skill Score = 1 - Brier / Brier_reference
        """
        brier = float(np.mean((pds - defaults) ** 2))
        brier_ref = base_rate * (1.0 - base_rate)
        skill = 1.0 - (brier / brier_ref) if brier_ref > 0 else 0.0
        return brier, skill

    @staticmethod
    def _compute_hosmer_lemeshow(
        pds: np.ndarray,
        defaults: np.ndarray,
        n_buckets: int,
    ) -> Tuple[float, float, int]:
        """
        Compute Hosmer-Lemeshow chi-squared goodness-of-fit test.

        Groups observations into n_buckets by predicted PD, then compares
        observed vs expected defaults per bucket using chi2 distribution.
        """
        n = len(pds)
        if n < n_buckets * 5:
            n_buckets = max(2, n // 5)

        # Sort by predicted PD
        order = np.argsort(pds)
        sorted_pds = pds[order]
        sorted_defaults = defaults[order]

        bucket_size = n // n_buckets
        chi2 = 0.0
        valid_buckets = 0

        for i in range(n_buckets):
            start = i * bucket_size
            end = (i + 1) * bucket_size if i < n_buckets - 1 else n
            bucket_pds = sorted_pds[start:end]
            bucket_defaults = sorted_defaults[start:end]

            n_g = len(bucket_pds)
            if n_g == 0:
                continue

            observed = float(bucket_defaults.sum())
            expected = float(bucket_pds.sum())

            # Avoid division by zero
            if expected > 0 and (n_g - expected) > 0:
                chi2 += (observed - expected) ** 2 / expected
                chi2 += (
                    ((n_g - observed) - (n_g - expected)) ** 2
                    / (n_g - expected)
                )
                valid_buckets += 1

        df = max(valid_buckets - 2, 1)
        p_value = float(1.0 - scipy_stats.chi2.cdf(chi2, df))

        return float(chi2), p_value, df

    @staticmethod
    def _compute_information_value(
        pds: np.ndarray,
        defaults: np.ndarray,
        n_bins: int = 10,
    ) -> Tuple[float, str]:
        """
        Compute Information Value (IV) for PD ranking power.

        IV = SUM[ (pct_non_default_i - pct_default_i) * WoE_i ]
        WoE_i = ln(pct_non_default_i / pct_default_i)

        Laplace smoothing applied (0.5) to avoid log(0).
        """
        n_defaults = float(defaults.sum())
        n_non_defaults = float(len(defaults) - n_defaults)

        if n_defaults == 0 or n_non_defaults == 0:
            return 0.0, "Useless"

        order = np.argsort(pds)
        sorted_defaults = defaults[order]

        bin_size = len(pds) // n_bins
        iv = 0.0

        for i in range(n_bins):
            start = i * bin_size
            end = (i + 1) * bin_size if i < n_bins - 1 else len(pds)
            bin_defaults = sorted_defaults[start:end]

            # Laplace smoothing
            d = max(float(bin_defaults.sum()), 0.5)
            nd = max(float(len(bin_defaults) - bin_defaults.sum()), 0.5)

            pct_d = d / n_defaults
            pct_nd = nd / n_non_defaults

            if pct_d > 0 and pct_nd > 0:
                woe = math.log(pct_nd / pct_d)
            else:
                woe = 0.0

            iv += (pct_nd - pct_d) * woe

        # Interpret per standard thresholds
        if iv >= IV_THRESHOLDS["very_strong"]:
            label = "Very Strong"
        elif iv >= IV_THRESHOLDS["strong"]:
            label = "Strong"
        elif iv >= IV_THRESHOLDS["medium"]:
            label = "Medium"
        elif iv >= IV_THRESHOLDS["weak"]:
            label = "Weak"
        else:
            label = "Useless"

        return float(iv), label

    # ------------------------------------------------------------------
    # PER-GRADE BINOMIAL TEST + TRAFFIC LIGHTS
    # ------------------------------------------------------------------

    def _backtest_by_grade(
        self,
        observations: List[ObservedDefault],
    ) -> List[GradeBacktestResult]:
        """
        Run per-grade binomial backtest with traffic light assignment.

        P(X >= observed_defaults | n, predicted_pd) using scipy.stats.binom.

        Traffic light per EBA GL/2017/16:
          GREEN  => p-value >= 0.05
          YELLOW => 0.01 <= p-value < 0.05
          RED    => p-value < 0.01
        """
        grades: Dict[str, Dict[str, Any]] = {}
        for obs in observations:
            g = obs.rating_grade
            if g not in grades:
                grades[g] = {"pds": [], "defaults": [], "count": 0}
            grades[g]["pds"].append(obs.predicted_pd)
            grades[g]["defaults"].append(obs.actual_default)
            grades[g]["count"] += 1

        results = []
        for grade, data in sorted(grades.items()):
            n = data["count"]
            d = sum(data["defaults"])
            avg_pd = sum(data["pds"]) / n if n > 0 else 0.0
            observed_dr = d / n if n > 0 else 0.0

            # Binomial test: P(X >= d | n, p = avg_pd)
            if n > 0 and avg_pd > 0:
                p_value = float(
                    1.0 - scipy_stats.binom.cdf(max(d - 1, 0), n, avg_pd)
                )
            else:
                p_value = 1.0

            # Traffic light assignment
            if p_value >= 0.05:
                traffic_light = "GREEN"
            elif p_value >= 0.01:
                traffic_light = "YELLOW"
            else:
                traffic_light = "RED"

            pred_error = (
                ((avg_pd - observed_dr) / observed_dr * 100.0)
                if observed_dr > 0 else 0.0
            )

            results.append(GradeBacktestResult(
                grade=grade,
                count=n,
                default_count=d,
                observed_default_rate=round(observed_dr, 6),
                predicted_pd_avg=round(avg_pd, 6),
                binomial_p_value=round(p_value, 4),
                traffic_light=traffic_light,
                prediction_error_pct=round(pred_error, 2),
            ))

        return results

    @staticmethod
    def _overall_traffic_light(
        grade_results: List[GradeBacktestResult],
    ) -> str:
        """
        Determine overall traffic light per EBA GL/2017/16.

        RED    if any grade is RED.
        YELLOW if > 25% of grades are YELLOW.
        GREEN  otherwise.
        """
        if not grade_results:
            return "GREEN"

        total = len(grade_results)
        red_count = sum(1 for g in grade_results if g.traffic_light == "RED")
        yellow_count = sum(1 for g in grade_results if g.traffic_light == "YELLOW")

        if red_count > 0:
            return "RED"
        if yellow_count / total > 0.25:
            return "YELLOW"
        return "GREEN"

    # ------------------------------------------------------------------
    # CAP CURVE
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_cap_curve(
        pds: np.ndarray,
        defaults: np.ndarray,
    ) -> List[Tuple[float, float]]:
        """
        Compute Cumulative Accuracy Profile (CAP) curve.

        Sort by PD descending, plot
        (cumulative % of population, cumulative % of defaults).
        """
        n = len(pds)
        if n == 0 or defaults.sum() == 0:
            return [(0.0, 0.0), (1.0, 1.0)]

        order = np.argsort(-pds)
        sorted_defaults = defaults[order]

        cum_pop = np.arange(1, n + 1) / n
        cum_defaults = np.cumsum(sorted_defaults) / defaults.sum()

        # Sample up to 100 points
        step = max(1, n // 100)
        points: List[Tuple[float, float]] = [(0.0, 0.0)]
        for i in range(0, n, step):
            points.append(
                (round(float(cum_pop[i]), 4), round(float(cum_defaults[i]), 4))
            )
        if points[-1] != (1.0, 1.0):
            points.append((1.0, 1.0))

        return points

    # ------------------------------------------------------------------
    # STATIC UTILITY METHODS
    # ------------------------------------------------------------------

    @staticmethod
    def get_gini_thresholds() -> Dict[str, float]:
        """Return Gini coefficient quality thresholds.

        excellent >= 0.60, good >= 0.40, acceptable >= 0.25, poor < 0.25
        """
        return dict(GINI_THRESHOLDS)

    @staticmethod
    def get_iv_thresholds() -> Dict[str, float]:
        """Return Information Value interpretation thresholds.

        very_strong >= 0.50, strong >= 0.30, medium >= 0.10,
        weak >= 0.02, useless < 0.02
        """
        return dict(IV_THRESHOLDS)

    @staticmethod
    def get_traffic_light_rules() -> Dict[str, str]:
        """Return EBA GL/2017/16 traffic light rules."""
        return {
            "GREEN":  "Binomial p-value >= 0.05 -- model well-calibrated",
            "YELLOW": "Binomial p-value 0.01 <= p < 0.05 -- monitoring required",
            "RED":    "Binomial p-value < 0.01 -- recalibration required",
        }

    @staticmethod
    def get_minimum_sample_sizes() -> Dict[str, int]:
        """Return recommended minimum sample sizes per EBA/ECB."""
        return {
            "overall_backtest":     30,
            "per_grade_binomial":   20,
            "hosmer_lemeshow":      50,
            "gini_reliable":       200,
            "regulatory_minimum":  100,
        }
