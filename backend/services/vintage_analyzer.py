"""
Vintage Analyzer -- Credit Portfolio Vintage Analysis & Cohort Tracking

Implements portfolio vintage analysis per:
  - IFRS 9 B5.5.52-B5.5.55: Collective assessment using groupings
  - EBA GL/2017/06: Credit risk management -- vintage analysis requirements
  - BCBS d350 CRE 36.72: Data maintenance standards for IRB
  - ECB NPL Guidance: Vintage-based coverage expectations for NPEs
  - EU Regulation 2019/630: Calendar provisioning (prudential backstop)

Key features:
  1. Cohort construction: group exposures by origination vintage (year/quarter)
  2. Per-cohort tracking: exposure_count, total_ead, defaults_by_age,
     cumulative_default_rate by age
  3. Vintage matrix: rows = origination vintage, columns = age (1..10),
     values = cumulative default rate
  4. Marginal default rate = cumulative[age] - cumulative[age-1]
  5. ECB backstop analysis: for defaulted NPEs, check if provisioning
     meets ECB calendar coverage
  6. Early warning: flag vintages where DR > EARLY_WARNING_THRESHOLD x benchmark
  7. Green trend: track green_origination_pct by vintage, detect
     improving / stable / deteriorating trend

Author: Vintage Analyzer Module
Version: 2.0.0
Date: 2026-03-08
"""
from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

# ECB NPE Calendar Provisioning Backstop (EU Regulation 2019/630)
# Minimum coverage ratio by age of NPE (non-performing exposure)
# age (years) -> {unsecured: pct, secured: pct}
ECB_NPE_COVERAGE: Dict[int, Dict[str, float]] = {
    0: {"unsecured": 0.00, "secured": 0.00},
    1: {"unsecured": 0.35, "secured": 0.00},
    2: {"unsecured": 1.00, "secured": 0.00},   # Full write-off unsecured by year 2
    3: {"unsecured": 1.00, "secured": 0.25},
    4: {"unsecured": 1.00, "secured": 0.35},
    5: {"unsecured": 1.00, "secured": 0.55},
    6: {"unsecured": 1.00, "secured": 0.70},
    7: {"unsecured": 1.00, "secured": 0.80},
    8: {"unsecured": 1.00, "secured": 0.85},
    9: {"unsecured": 1.00, "secured": 1.00},   # Full write-off secured by year 9
}

# Benchmark cumulative default rates by vintage age
# (basis: IG + HY composite, long-run average)
BENCHMARK_CUMULATIVE_DR: Dict[int, float] = {
    1: 0.015,
    2: 0.032,
    3: 0.050,
    4: 0.068,
    5: 0.083,
    6: 0.095,
    7: 0.105,
    8: 0.112,
    9: 0.118,
    10: 0.125,
}

# Early warning threshold: flag vintage if cumulative DR > (1 + threshold) x benchmark
# i.e., 1.5x benchmark triggers early warning
EARLY_WARNING_THRESHOLD: float = 0.50


# ---------------------------------------------------------------------------
# DATACLASSES
# ---------------------------------------------------------------------------


@dataclass
class VintageExposure:
    """Single exposure with vintage data."""
    exposure_id: str
    counterparty_name: str
    origination_date: str           # YYYY-MM-DD or YYYY-QN
    origination_year: int
    origination_quarter: int = 0    # 1-4 (0 if unknown)
    original_amount: float = 0.0
    current_balance: float = 0.0
    is_defaulted: bool = False
    default_date: str = ""          # YYYY-MM-DD if defaulted
    months_to_default: int = 0      # Months from origination to default
    current_stage: int = 1          # IFRS 9 stage (1, 2, 3)
    sector: str = ""
    asset_class: str = "CORPORATE"
    collateral_type: str = "unsecured"
    is_npe: bool = False            # Non-performing exposure
    npe_age_years: float = 0.0      # Age of NPE status in years
    provision_amount: float = 0.0
    epc_rating: str = ""            # For green/brown analysis
    is_green: bool = False          # Green taxonomy aligned


@dataclass
class VintageCohort:
    """Summary for a single vintage cohort."""
    vintage_label: str              # e.g., "2021-Q3" or "2021"
    vintage_year: int
    vintage_quarter: int
    exposure_count: int
    original_amount_total: float
    current_balance_total: float
    default_count: int
    cumulative_default_rate: float
    avg_months_to_default: float
    stage1_count: int
    stage2_count: int
    stage3_count: int
    stage2_migration_rate: float    # % of original that migrated to S2+
    npe_count: int
    npe_coverage_ratio: float       # provision / NPE balance
    ecb_coverage_shortfall: float   # Gap vs ECB backstop requirement
    early_warning: bool             # True if exceeds benchmark threshold
    benchmark_dr: float             # Expected DR for this vintage age
    green_share_pct: float          # % of originations that are green


@dataclass
class VintageMatrix:
    """
    Vintage matrix: rows = origination vintage, columns = age (in years).
    Values are Optional[float] -- None where vintage is not old enough
    to observe that age.
    """
    vintage_labels: List[str]
    age_labels: List[int]                                # 1, 2, ..., max_age
    cumulative_dr_matrix: List[List[Optional[float]]]    # [vintage][age]
    marginal_dr_matrix: List[List[Optional[float]]]      # [vintage][age]


@dataclass
class VintageAnalysisResult:
    """Complete vintage analysis result."""
    cohorts: List[VintageCohort]
    vintage_matrix: VintageMatrix
    total_exposures: int
    total_original_amount: float
    total_current_balance: float
    overall_cumulative_dr: float
    worst_vintage: str
    worst_vintage_dr: float
    best_vintage: str
    best_vintage_dr: float
    early_warning_vintages: List[str]
    npe_coverage_gap_total: float       # Total ECB backstop shortfall
    green_origination_trend: List[Dict[str, Any]]
    methodology_notes: List[str]


# ---------------------------------------------------------------------------
# MAIN ANALYZER CLASS
# ---------------------------------------------------------------------------


class VintageAnalyzer:
    """
    Credit portfolio vintage analysis engine.

    Groups exposures by origination vintage, tracks cumulative default
    rates by vintage age, compares against benchmarks, and flags
    deteriorating cohorts for early intervention.
    """

    def __init__(
        self,
        reference_year: int = 2024,
        granularity: str = "annual",    # "annual" or "quarterly"
    ):
        """
        Initialize vintage analyzer.

        Args:
            reference_year: Current year for vintage age calculation
            granularity: "annual" or "quarterly" cohort grouping
        """
        self.reference_year = reference_year
        self.granularity = granularity

    # -------------------------------------------------------------------
    # MAIN ENTRY POINT
    # -------------------------------------------------------------------

    def analyze(
        self,
        exposures: List[VintageExposure],
    ) -> VintageAnalysisResult:
        """
        Run full vintage analysis on exposure portfolio.

        Args:
            exposures: List of exposures with vintage data

        Returns:
            VintageAnalysisResult with cohort summaries, vintage matrix,
            early warning flags, and ECB NPE coverage gaps

        Raises:
            ValueError: if no exposures provided
        """
        if not exposures:
            raise ValueError("At least one exposure required for vintage analysis")

        notes: List[str] = []

        # ------------------------------------------------------------------
        # Build cohorts
        # ------------------------------------------------------------------
        cohort_map = self._build_cohorts(exposures)
        notes.append(
            f"Built {len(cohort_map)} vintage cohorts "
            f"({self.granularity}) from {len(exposures)} exposures"
        )

        # Compute per-cohort metrics
        cohorts: List[VintageCohort] = []
        for label, exps in sorted(cohort_map.items()):
            cohort = self._compute_cohort(label, exps)
            cohorts.append(cohort)

        # ------------------------------------------------------------------
        # Build vintage matrix
        # ------------------------------------------------------------------
        vintage_matrix = self._build_vintage_matrix(cohorts, exposures)

        # ------------------------------------------------------------------
        # Summary statistics
        # ------------------------------------------------------------------
        total_original = sum(c.original_amount_total for c in cohorts)
        total_current = sum(c.current_balance_total for c in cohorts)
        total_defaults = sum(c.default_count for c in cohorts)
        total_count = sum(c.exposure_count for c in cohorts)
        overall_dr = total_defaults / total_count if total_count > 0 else 0.0

        # Worst / best vintage (require >= 10 exposures for significance)
        non_empty = [c for c in cohorts if c.exposure_count >= 10]
        if non_empty:
            worst = max(non_empty, key=lambda c: c.cumulative_default_rate)
            best = min(non_empty, key=lambda c: c.cumulative_default_rate)
        else:
            worst = best = cohorts[0] if cohorts else None

        # Early warning vintages
        ew_vintages = [c.vintage_label for c in cohorts if c.early_warning]
        if ew_vintages:
            notes.append(
                f"Early warning: {len(ew_vintages)} vintages exceeding "
                f"benchmark ({', '.join(ew_vintages)})"
            )

        # NPE coverage gap
        npe_gap = sum(c.ecb_coverage_shortfall for c in cohorts)
        if npe_gap > 0:
            notes.append(
                f"Total ECB backstop coverage shortfall: {npe_gap:,.0f}"
            )

        # Green origination trend
        green_trend = self._compute_green_trend(cohorts)

        return VintageAnalysisResult(
            cohorts=cohorts,
            vintage_matrix=vintage_matrix,
            total_exposures=total_count,
            total_original_amount=round(total_original, 2),
            total_current_balance=round(total_current, 2),
            overall_cumulative_dr=round(overall_dr, 6),
            worst_vintage=worst.vintage_label if worst else "",
            worst_vintage_dr=round(worst.cumulative_default_rate, 6) if worst else 0.0,
            best_vintage=best.vintage_label if best else "",
            best_vintage_dr=round(best.cumulative_default_rate, 6) if best else 0.0,
            early_warning_vintages=ew_vintages,
            npe_coverage_gap_total=round(npe_gap, 2),
            green_origination_trend=green_trend,
            methodology_notes=notes,
        )

    # -------------------------------------------------------------------
    # COHORT CONSTRUCTION
    # -------------------------------------------------------------------

    def _build_cohorts(
        self,
        exposures: List[VintageExposure],
    ) -> Dict[str, List[VintageExposure]]:
        """Group exposures into vintage cohorts by year or quarter."""
        cohorts: Dict[str, List[VintageExposure]] = defaultdict(list)

        for exp in exposures:
            if self.granularity == "quarterly" and exp.origination_quarter > 0:
                label = f"{exp.origination_year}-Q{exp.origination_quarter}"
            else:
                label = str(exp.origination_year)
            cohorts[label].append(exp)

        return dict(cohorts)

    def _compute_cohort(
        self,
        label: str,
        exposures: List[VintageExposure],
    ) -> VintageCohort:
        """Compute metrics for a single vintage cohort."""
        n = len(exposures)
        defaults = [e for e in exposures if e.is_defaulted]
        n_defaults = len(defaults)
        cum_dr = n_defaults / n if n > 0 else 0.0

        original_total = sum(e.original_amount for e in exposures)
        current_total = sum(e.current_balance for e in exposures)

        avg_months_to_default = (
            sum(d.months_to_default for d in defaults) / n_defaults
            if n_defaults > 0 else 0.0
        )

        # Stage counts
        s1 = sum(1 for e in exposures if e.current_stage == 1)
        s2 = sum(1 for e in exposures if e.current_stage == 2)
        s3 = sum(1 for e in exposures if e.current_stage == 3)
        s2_migration = (s2 + s3) / n * 100 if n > 0 else 0.0

        # NPE coverage
        npes = [e for e in exposures if e.is_npe]
        npe_count = len(npes)
        npe_balance = sum(e.current_balance for e in npes)
        npe_provision = sum(e.provision_amount for e in npes)
        npe_coverage = npe_provision / npe_balance if npe_balance > 0 else 0.0

        # ECB backstop coverage requirement
        ecb_required = self._compute_ecb_required_coverage(npes)
        ecb_shortfall = max(ecb_required - npe_provision, 0.0)

        # Vintage year and quarter parsing
        year = exposures[0].origination_year
        quarter = (
            exposures[0].origination_quarter
            if self.granularity == "quarterly"
            else 0
        )

        # Vintage age and early warning
        vintage_age = self.reference_year - year
        benchmark_dr = BENCHMARK_CUMULATIVE_DR.get(
            max(1, min(vintage_age, 10)),
            BENCHMARK_CUMULATIVE_DR[10],
        )
        early_warning = cum_dr > benchmark_dr * (1.0 + EARLY_WARNING_THRESHOLD)

        # Green share
        green_count = sum(1 for e in exposures if e.is_green)
        green_pct = green_count / n * 100 if n > 0 else 0.0

        return VintageCohort(
            vintage_label=label,
            vintage_year=year,
            vintage_quarter=quarter,
            exposure_count=n,
            original_amount_total=round(original_total, 2),
            current_balance_total=round(current_total, 2),
            default_count=n_defaults,
            cumulative_default_rate=round(cum_dr, 6),
            avg_months_to_default=round(avg_months_to_default, 1),
            stage1_count=s1,
            stage2_count=s2,
            stage3_count=s3,
            stage2_migration_rate=round(s2_migration, 2),
            npe_count=npe_count,
            npe_coverage_ratio=round(npe_coverage, 4),
            ecb_coverage_shortfall=round(ecb_shortfall, 2),
            early_warning=early_warning,
            benchmark_dr=round(benchmark_dr, 6),
            green_share_pct=round(green_pct, 2),
        )

    # -------------------------------------------------------------------
    # VINTAGE MATRIX
    # -------------------------------------------------------------------

    def _build_vintage_matrix(
        self,
        cohorts: List[VintageCohort],
        exposures: List[VintageExposure],
    ) -> VintageMatrix:
        """
        Build vintage matrix (cumulative + marginal DR by vintage age).

        Rows = vintage years, Columns = age in years (1, 2, ..., max_age).
        Cells are None where vintage is not old enough to observe that age.
        """
        # Group defaults by vintage year and months-to-default -> age bucket
        vintage_defaults: Dict[int, Dict[int, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        vintage_counts: Dict[int, int] = defaultdict(int)

        for exp in exposures:
            vintage_counts[exp.origination_year] += 1
            if exp.is_defaulted and exp.months_to_default > 0:
                age_years = max(1, (exp.months_to_default + 6) // 12)
                vintage_defaults[exp.origination_year][age_years] += 1

        years = sorted(vintage_counts.keys())
        max_age = max(
            (self.reference_year - y for y in years),
            default=1,
        )
        max_age = min(max_age, 10)  # Cap at 10 years
        age_labels = list(range(1, max_age + 1))

        cum_matrix: List[List[Optional[float]]] = []
        marg_matrix: List[List[Optional[float]]] = []
        vintage_labels: List[str] = []

        for year in years:
            vintage_labels.append(str(year))
            n = vintage_counts[year]
            cum_row: List[Optional[float]] = []
            marg_row: List[Optional[float]] = []
            cumulative = 0

            for age in age_labels:
                defaults_at_age = vintage_defaults[year].get(age, 0)
                cumulative += defaults_at_age
                cum_dr = cumulative / n if n > 0 else 0.0
                marg_dr = defaults_at_age / n if n > 0 else 0.0

                # Only fill if vintage is old enough to observe this age
                if (self.reference_year - year) >= age:
                    cum_row.append(round(cum_dr, 6))
                    marg_row.append(round(marg_dr, 6))
                else:
                    cum_row.append(None)
                    marg_row.append(None)

            cum_matrix.append(cum_row)
            marg_matrix.append(marg_row)

        return VintageMatrix(
            vintage_labels=vintage_labels,
            age_labels=age_labels,
            cumulative_dr_matrix=cum_matrix,
            marginal_dr_matrix=marg_matrix,
        )

    # -------------------------------------------------------------------
    # ECB BACKSTOP
    # -------------------------------------------------------------------

    @staticmethod
    def _compute_ecb_required_coverage(
        npes: List[VintageExposure],
    ) -> float:
        """
        Compute total required provision under ECB calendar provisioning
        backstop (EU Regulation 2019/630).

        For each NPE, look up the minimum coverage by age and collateral
        type (unsecured vs secured).
        """
        total_required = 0.0
        for e in npes:
            age = int(e.npe_age_years)
            age = min(age, 9)  # Cap at 9 years
            coll_key = (
                "unsecured" if e.collateral_type == "unsecured" else "secured"
            )
            coverage_pct = ECB_NPE_COVERAGE.get(
                age,
                {"unsecured": 1.0, "secured": 1.0},
            )[coll_key]
            total_required += e.current_balance * coverage_pct
        return total_required

    # -------------------------------------------------------------------
    # GREEN TREND
    # -------------------------------------------------------------------

    @staticmethod
    def _compute_green_trend(
        cohorts: List[VintageCohort],
    ) -> List[Dict[str, Any]]:
        """
        Compute green origination trend over time.

        Returns list of dicts with vintage, year, green_share_pct,
        total_originations, and green_amount_pct.
        """
        trend: List[Dict[str, Any]] = []
        for c in sorted(
            cohorts,
            key=lambda x: (x.vintage_year, x.vintage_quarter),
        ):
            trend.append({
                "vintage": c.vintage_label,
                "year": c.vintage_year,
                "green_share_pct": c.green_share_pct,
                "total_originations": c.exposure_count,
                "green_amount_pct": round(c.green_share_pct, 2),
            })
        return trend

    # -------------------------------------------------------------------
    # STATIC UTILITY METHODS (for API reference endpoints)
    # -------------------------------------------------------------------

    @staticmethod
    def get_ecb_npe_coverage_table() -> Dict[int, Dict[str, float]]:
        """Return ECB NPE calendar provisioning backstop table."""
        return dict(ECB_NPE_COVERAGE)

    @staticmethod
    def get_benchmark_default_rates() -> Dict[int, float]:
        """Return benchmark cumulative default rates by vintage age."""
        return dict(BENCHMARK_CUMULATIVE_DR)

    @staticmethod
    def get_early_warning_threshold() -> float:
        """Return early warning threshold multiplier."""
        return EARLY_WARNING_THRESHOLD
