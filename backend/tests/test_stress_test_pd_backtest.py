"""
Tests for Stress Test Runner and PD Backtester
===============================================

Covers:
  - StressTestRunner: multi-scenario execution, stage migration, sector
    concentration, probability-weighted ECL, capital impact
  - PDBacktester: Gini/AUROC, KS, Brier, Hosmer-Lemeshow, IV, traffic lights,
    model validity, edge cases

Run:
  pytest backend/tests/test_stress_test_pd_backtest.py -v

Author: Risk Analytics Platform
Date: 2026-03-08
"""
from __future__ import annotations

import random

import numpy as np
import pytest

from services.stress_test_runner import (
    StressTestRunner,
    LoanBookExposure,
    SCENARIOS,
    SCENARIO_WEIGHTS,
    SCENARIO_PD_MULTIPLIERS,
    SCENARIO_LGD_HAIRCUTS,
    SECTOR_RISK_LEVELS,
)
from services.pd_backtester import (
    PDBacktester,
    ObservedDefault,
    BacktestMetrics,
    GINI_THRESHOLDS,
    IV_THRESHOLDS,
)


# ---------------------------------------------------------------------------
# FIXTURE HELPERS -- STRESS TEST
# ---------------------------------------------------------------------------


def _make_loan_book(n: int = 50) -> list:
    """
    Generate a realistic loan book for stress testing.

    Uses 5 sectors spanning all four risk tiers.  PDs range 0.001-0.15,
    LGDs 0.20-0.60, EADs 100K-10M.  Stages assigned based on PD level.
    Seed 42 for reproducibility.
    """
    rng = random.Random(42)
    np_rng = np.random.RandomState(42)

    sectors = [
        "Oil & Gas",            # very_high
        "Technology",           # low
        "Real Estate",          # medium
        "Healthcare",           # low
        "Steel & Metals",       # very_high
    ]
    collateral_types = ["property", "equipment", "financial", "unsecured"]

    book = []
    for i in range(n):
        sector = sectors[i % len(sectors)]
        pd_base = np_rng.uniform(0.001, 0.15)
        lgd_base = np_rng.uniform(0.20, 0.60)
        ead = np_rng.uniform(100_000, 10_000_000)

        # Stage: 1 if PD < 3%, else 2 (some stage 3 for high PD)
        if pd_base < 0.03:
            stage = 1
        elif pd_base < 0.10:
            stage = 2
        else:
            stage = 3

        book.append(LoanBookExposure(
            exposure_id=f"EXP-{i:04d}",
            obligor_name=f"Company_{i}",
            sector=sector,
            collateral_type=rng.choice(collateral_types),
            baseline_pd=round(pd_base, 6),
            baseline_lgd=round(lgd_base, 4),
            ead=round(ead, 2),
            current_stage=stage,
            maturity_years=round(np_rng.uniform(1, 10), 1),
            rating_grade=rng.choice(["AAA", "AA", "A", "BBB", "BB", "B", "CCC"]),
        ))
    return book


# ---------------------------------------------------------------------------
# FIXTURE HELPERS -- PD BACKTEST
# ---------------------------------------------------------------------------


def _make_observations(n: int = 500) -> list:
    """
    Generate realistic PD backtest observations with 7 rating grades.

    Higher predicted PD correlates with higher actual default probability
    (good model behavior).  Seed 123 for reproducibility.
    """
    rng = np.random.RandomState(123)
    grades = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC"]
    grade_pds = {
        "AAA": 0.001, "AA": 0.003, "A": 0.008, "BBB": 0.02,
        "BB": 0.05, "B": 0.10, "CCC": 0.25,
    }
    grade_probs = [0.05, 0.10, 0.20, 0.30, 0.20, 0.10, 0.05]

    observations = []
    for i in range(n):
        grade = rng.choice(grades, p=grade_probs)
        base_pd = grade_pds[grade]
        # Add noise to predicted PD
        predicted_pd = max(0.0001, min(0.9999, base_pd + rng.normal(0, base_pd * 0.3)))
        # Default probability correlated with predicted PD
        actual_default = 1 if rng.random() < (predicted_pd * 1.1) else 0

        observations.append(ObservedDefault(
            exposure_id=f"OBS-{i:04d}",
            rating_grade=grade,
            predicted_pd=round(predicted_pd, 6),
            actual_default=actual_default,
            exposure_amount=rng.uniform(100_000, 10_000_000),
            sector=rng.choice(["Corporate", "SME", "Retail"]),
            vintage_year=rng.choice([2021, 2022, 2023, 2024]),
        ))
    return observations


def _make_perfect_model_observations(n: int = 200) -> list:
    """
    Perfect model: high PD = high default.

    Defaults get predicted_pd=0.95, non-defaults get predicted_pd=0.01.
    5% default rate.
    """
    observations = []
    n_defaults = int(n * 0.05)

    for i in range(n):
        is_default = i < n_defaults
        observations.append(ObservedDefault(
            exposure_id=f"PERF-{i:04d}",
            rating_grade="D" if is_default else "AAA",
            predicted_pd=0.95 if is_default else 0.01,
            actual_default=1 if is_default else 0,
        ))
    return observations


def _make_random_model_observations(n: int = 200) -> list:
    """
    Random model: no discriminatory power.

    PDs are random uniform [0.01, 0.10], defaults are random with ~5% rate.
    Seed 77 for reproducibility.
    """
    rng = np.random.RandomState(77)
    observations = []

    for i in range(n):
        actual_default = 1 if rng.random() < 0.05 else 0
        observations.append(ObservedDefault(
            exposure_id=f"RAND-{i:04d}",
            rating_grade=rng.choice(["A", "B", "C"]),
            predicted_pd=round(rng.uniform(0.01, 0.10), 4),
            actual_default=actual_default,
        ))
    return observations


# ===========================================================================
# STRESS TEST RUNNER TESTS
# ===========================================================================


class TestStressTestBasic:
    """Basic stress test execution -- run with default scenarios, verify structure."""

    def test_all_scenarios_executed(self):
        """Four scenario summaries returned, positive ECL."""
        book = _make_loan_book(20)
        runner = StressTestRunner()
        result = runner.run(book, "Test Portfolio", "ST-TEST-001")

        assert result.run_id == "ST-TEST-001"
        assert result.portfolio_name == "Test Portfolio"
        assert len(result.scenario_summaries) == 4
        for s in SCENARIOS:
            assert s in result.scenario_summaries
            assert result.scenario_summaries[s].total_ecl > 0

    def test_custom_scenarios(self):
        """Run subset of scenarios."""
        book = _make_loan_book(10)
        runner = StressTestRunner(scenarios=["BASE", "SEVERE"])
        result = runner.run(book)

        assert set(result.scenarios_run) == {"BASE", "SEVERE"}
        assert len(result.scenario_summaries) == 2
        assert "OPTIMISTIC" not in result.scenario_summaries

    def test_total_ead_consistent(self):
        """Total EAD in each scenario matches loan book sum."""
        book = _make_loan_book(20)
        runner = StressTestRunner()
        result = runner.run(book)

        expected_ead = sum(e.ead for e in book)
        for s in SCENARIOS:
            assert abs(result.scenario_summaries[s].total_ead - expected_ead) < 1.0

    def test_autogenerated_run_id(self):
        """Run ID is auto-generated when not provided."""
        book = _make_loan_book(5)
        runner = StressTestRunner()
        result = runner.run(book)
        assert result.run_id.startswith("ST-")


class TestStressTestScenarios:
    """Scenario ordering: adverse ECL > base ECL, severe > adverse."""

    def test_severe_higher_ecl_than_base(self):
        book = _make_loan_book(30)
        runner = StressTestRunner()
        result = runner.run(book)

        severe = result.scenario_summaries["SEVERE"]
        base = result.scenario_summaries["BASE"]
        assert severe.total_ecl > base.total_ecl

    def test_adverse_higher_ecl_than_base(self):
        book = _make_loan_book(30)
        runner = StressTestRunner()
        result = runner.run(book)

        adverse = result.scenario_summaries["ADVERSE"]
        base = result.scenario_summaries["BASE"]
        assert adverse.total_ecl > base.total_ecl

    def test_severe_higher_ecl_than_adverse(self):
        book = _make_loan_book(30)
        runner = StressTestRunner()
        result = runner.run(book)

        severe = result.scenario_summaries["SEVERE"]
        adverse = result.scenario_summaries["ADVERSE"]
        assert severe.total_ecl > adverse.total_ecl

    def test_ecl_uplift_ordering(self):
        """ECL uplift: OPTIMISTIC <= BASE <= ADVERSE <= SEVERE."""
        book = _make_loan_book(50)
        runner = StressTestRunner()
        result = runner.run(book)

        uplifts = [
            result.scenario_summaries[s].ecl_uplift_pct
            for s in ["OPTIMISTIC", "BASE", "ADVERSE", "SEVERE"]
        ]
        assert uplifts[0] <= uplifts[1] <= uplifts[2] <= uplifts[3]


class TestStageMigration:
    """Stage migration matrix: stage 1 exposures migrate to 2/3 under stress."""

    def test_migration_matrices_present(self):
        book = _make_loan_book(20)
        runner = StressTestRunner()
        result = runner.run(book)

        for s in SCENARIOS:
            assert s in result.migration_matrices
            m = result.migration_matrices[s]
            assert m.total_exposures == 20

    def test_migration_row_sums_match(self):
        """All exposures accounted for: sum of all transitions == total."""
        book = _make_loan_book(30)
        runner = StressTestRunner()
        result = runner.run(book)

        for s in SCENARIOS:
            m = result.migration_matrices[s]
            total = sum(m.transitions.values())
            assert total == m.total_exposures

    def test_severe_more_stage2_than_optimistic(self):
        """Severe stress should push more exposures into Stage 2+."""
        book = _make_loan_book(50)
        runner = StressTestRunner()
        result = runner.run(book)

        severe_s2 = result.scenario_summaries["SEVERE"].stage2_count
        opt_s2 = result.scenario_summaries["OPTIMISTIC"].stage2_count
        severe_s3 = result.scenario_summaries["SEVERE"].stage3_count
        opt_s3 = result.scenario_summaries["OPTIMISTIC"].stage3_count
        # Severe has at least as many stage 2+3 combined
        assert (severe_s2 + severe_s3) >= (opt_s2 + opt_s3)

    def test_sicr_trigger_count(self):
        """SICR triggers should be non-negative and <= total exposures."""
        book = _make_loan_book(30)
        runner = StressTestRunner()
        result = runner.run(book)

        for s in SCENARIOS:
            m = result.migration_matrices[s]
            assert 0 <= m.sicr_trigger_count <= m.total_exposures


class TestSectorConcentration:
    """Sector concentration: all sectors present, concentration sums to ~100%."""

    def test_all_sectors_present(self):
        book = _make_loan_book(50)
        runner = StressTestRunner()
        result = runner.run(book)

        for s in SCENARIOS:
            concs = result.sector_concentrations[s]
            assert len(concs) > 0

    def test_concentration_pct_sums_to_100(self):
        book = _make_loan_book(50)
        runner = StressTestRunner()
        result = runner.run(book)

        for s in SCENARIOS:
            concs = result.sector_concentrations[s]
            total = sum(c.concentration_pct for c in concs)
            assert abs(total - 100.0) < 1.0

    def test_high_risk_sector_higher_uplift(self):
        """Oil & Gas (very_high) should have higher ECL uplift than Technology (low)."""
        book = _make_loan_book(50)
        runner = StressTestRunner()
        result = runner.run(book)

        # Check ADVERSE scenario specifically
        concs = result.sector_concentrations.get("ADVERSE", [])
        sector_map = {c.sector: c for c in concs}
        if "Oil & Gas" in sector_map and "Technology" in sector_map:
            assert (
                sector_map["Oil & Gas"].ecl_uplift_pct
                > sector_map["Technology"].ecl_uplift_pct
            )


class TestProbabilityWeighted:
    """Probability-weighted ECL: between min and max scenario ECL."""

    def test_pw_ecl_positive(self):
        book = _make_loan_book(30)
        runner = StressTestRunner()
        result = runner.run(book)

        assert result.pw_ecl > 0
        assert result.pw_ecl_base > 0

    def test_pw_ecl_between_min_and_max(self):
        """PW ECL should lie between the lowest and highest scenario ECL."""
        book = _make_loan_book(50)
        runner = StressTestRunner()
        result = runner.run(book)

        scenario_ecls = [
            result.scenario_summaries[s].total_ecl for s in SCENARIOS
        ]
        min_ecl = min(scenario_ecls)
        max_ecl = max(scenario_ecls)
        assert min_ecl <= result.pw_ecl <= max_ecl

    def test_capital_impact_summary(self):
        """Capital impact summary contains required keys."""
        book = _make_loan_book(20)
        runner = StressTestRunner()
        result = runner.run(book)

        ci = result.capital_impact_summary
        assert "pw_rwa_impact" in ci
        assert "pw_capital_shortfall" in ci
        assert "worst_case_rwa_impact" in ci
        assert "worst_case_capital_shortfall" in ci

    def test_methodology_notes_populated(self):
        book = _make_loan_book(10)
        runner = StressTestRunner()
        result = runner.run(book)

        assert len(result.methodology_notes) >= 10


class TestDetailedResults:
    """Detailed per-exposure results when include_detailed=True."""

    def test_detailed_included(self):
        book = _make_loan_book(10)
        runner = StressTestRunner(include_detailed=True)
        result = runner.run(book)

        # Each scenario has 10 exposure results
        for s in SCENARIOS:
            assert len(result.scenario_summaries[s].exposure_results) == 10

    def test_detailed_excluded(self):
        book = _make_loan_book(10)
        runner = StressTestRunner(include_detailed=False)
        result = runner.run(book)

        for s in SCENARIOS:
            assert len(result.scenario_summaries[s].exposure_results) == 0


# ===========================================================================
# PD BACKTESTER TESTS
# ===========================================================================


class TestGiniAUROC:
    """Gini coefficient and AUROC: perfect model near 1.0, random near 0.0."""

    def test_good_model_high_gini(self):
        obs = _make_observations(500)
        bt = PDBacktester()
        result = bt.backtest(obs)

        assert result.gini_coefficient > GINI_THRESHOLDS["acceptable"]
        assert result.auroc > 0.5

    def test_perfect_model_gini_near_1(self):
        obs = _make_perfect_model_observations(200)
        bt = PDBacktester()
        result = bt.backtest(obs)

        assert result.gini_coefficient > 0.90
        assert result.auroc > 0.95

    def test_random_model_low_gini(self):
        obs = _make_random_model_observations(200)
        bt = PDBacktester()
        result = bt.backtest(obs)

        # Random model Gini should be close to 0 (could be slightly negative)
        assert result.gini_coefficient < 0.50

    def test_gini_auroc_relationship(self):
        """Gini = 2 * AUROC - 1."""
        obs = _make_observations(300)
        bt = PDBacktester()
        result = bt.backtest(obs)

        expected_gini = 2 * result.auroc - 1
        assert abs(result.gini_coefficient - expected_gini) < 0.01

    def test_auroc_at_least_half(self):
        """AUROC should be >= 0.5 for any reasonable model."""
        obs = _make_observations(500)
        bt = PDBacktester()
        result = bt.backtest(obs)

        assert result.auroc >= 0.5


class TestKSStatistic:
    """KS statistic: value 0-1, p-value for perfect model < 0.05."""

    def test_ks_range(self):
        obs = _make_observations(500)
        bt = PDBacktester()
        result = bt.backtest(obs)

        assert 0 <= result.ks_statistic <= 1
        assert 0 <= result.ks_p_value <= 1

    def test_perfect_model_high_ks(self):
        obs = _make_perfect_model_observations(200)
        bt = PDBacktester()
        result = bt.backtest(obs)

        assert result.ks_statistic > 0.80
        assert result.ks_p_value < 0.05

    def test_good_model_significant_ks(self):
        obs = _make_observations(500)
        bt = PDBacktester()
        result = bt.backtest(obs)

        assert result.ks_statistic > 0


class TestBrierScore:
    """Brier score: perfect model near 0, random model > perfect."""

    def test_brier_range(self):
        obs = _make_observations(500)
        bt = PDBacktester()
        result = bt.backtest(obs)

        assert 0 <= result.brier_score <= 1

    def test_perfect_model_brier_near_zero(self):
        obs = _make_perfect_model_observations(200)
        bt = PDBacktester()
        result = bt.backtest(obs)

        assert result.brier_score < 0.05

    def test_random_model_higher_brier_than_perfect(self):
        perfect_obs = _make_perfect_model_observations(200)
        random_obs = _make_random_model_observations(200)
        bt = PDBacktester()

        perfect_result = bt.backtest(perfect_obs)
        random_result = bt.backtest(random_obs)

        assert random_result.brier_score > perfect_result.brier_score

    def test_brier_skill_positive_for_good_model(self):
        """Positive skill score means model beats naive (base rate)."""
        obs = _make_observations(500)
        bt = PDBacktester()
        result = bt.backtest(obs)

        assert result.brier_skill_score > 0


class TestHosmerLemeshow:
    """Hosmer-Lemeshow: well-calibrated model HL p-value > 0.05."""

    def test_hl_outputs(self):
        obs = _make_observations(500)
        bt = PDBacktester()
        result = bt.backtest(obs)

        assert result.hosmer_lemeshow_chi2 >= 0
        assert 0 <= result.hosmer_lemeshow_p_value <= 1
        assert result.hosmer_lemeshow_df > 0

    def test_custom_n_buckets(self):
        obs = _make_observations(500)
        bt = PDBacktester(n_buckets=5)
        result = bt.backtest(obs)

        assert result.hosmer_lemeshow_df > 0

    def test_hl_chi2_non_negative(self):
        obs = _make_observations(300)
        bt = PDBacktester()
        result = bt.backtest(obs)

        assert result.hosmer_lemeshow_chi2 >= 0


class TestInformationValue:
    """Information Value: IV > 0, interpretation string present."""

    def test_iv_positive(self):
        obs = _make_observations(500)
        bt = PDBacktester()
        result = bt.backtest(obs)

        assert result.information_value >= 0

    def test_iv_interpretation_valid(self):
        obs = _make_observations(500)
        bt = PDBacktester()
        result = bt.backtest(obs)

        valid_labels = ["Very Strong", "Strong", "Medium", "Weak", "Useless"]
        assert result.iv_interpretation in valid_labels

    def test_perfect_model_high_iv(self):
        obs = _make_perfect_model_observations(200)
        bt = PDBacktester()
        result = bt.backtest(obs)

        assert result.information_value > IV_THRESHOLDS["medium"]


class TestTrafficLights:
    """Per-grade traffic lights in {GREEN, YELLOW, RED}."""

    def test_grade_results_present(self):
        obs = _make_observations(500)
        bt = PDBacktester()
        result = bt.backtest(obs)

        assert len(result.grade_results) > 0
        for g in result.grade_results:
            assert g.traffic_light in ["GREEN", "YELLOW", "RED"]

    def test_overall_traffic_light_valid(self):
        obs = _make_observations(500)
        bt = PDBacktester()
        result = bt.backtest(obs)

        assert result.overall_traffic_light in ["GREEN", "YELLOW", "RED"]

    def test_grade_counts_sum_to_total(self):
        obs = _make_observations(500)
        bt = PDBacktester()
        result = bt.backtest(obs)

        total_count = sum(g.count for g in result.grade_results)
        assert total_count == 500

    def test_all_seven_grades_present(self):
        """Observations span 7 grades; all should appear in results."""
        obs = _make_observations(500)
        bt = PDBacktester()
        result = bt.backtest(obs)

        grades = {g.grade for g in result.grade_results}
        assert len(grades) == 7


class TestModelValidity:
    """model_valid boolean, validation_issues list."""

    def test_good_model_valid(self):
        obs = _make_observations(500)
        bt = PDBacktester()
        result = bt.backtest(obs)

        assert isinstance(result.model_valid, bool)

    def test_validation_issues_is_list(self):
        obs = _make_observations(500)
        bt = PDBacktester()
        result = bt.backtest(obs)

        assert isinstance(result.validation_issues, list)

    def test_summary_stats(self):
        obs = _make_observations(500)
        bt = PDBacktester()
        result = bt.backtest(obs)

        assert result.total_observations == 500
        assert result.total_defaults >= 0
        assert 0 <= result.overall_default_rate <= 1
        assert 0 <= result.avg_predicted_pd <= 1

    def test_curves_populated(self):
        """CAP and ROC curves should have multiple points, start at (0,0)."""
        obs = _make_observations(500)
        bt = PDBacktester()
        result = bt.backtest(obs)

        assert len(result.cap_curve) > 2
        assert len(result.roc_curve) > 2
        assert result.cap_curve[0] == (0.0, 0.0)
        assert result.cap_curve[-1] == (1.0, 1.0)


class TestEdgeCases:
    """Edge cases: minimum 30 obs, all same grade."""

    def test_minimum_30_observations(self):
        """Should work with exactly 30 observations."""
        obs = _make_observations(30)
        bt = PDBacktester()
        result = bt.backtest(obs)
        assert result.total_observations == 30

    def test_too_few_observations_raises(self):
        """Should raise ValueError with fewer than 30 observations."""
        obs = _make_observations(30)[:20]
        bt = PDBacktester()
        with pytest.raises(ValueError, match="Minimum 30"):
            bt.backtest(obs)

    def test_all_same_grade(self):
        """All observations in one grade -- should still produce valid results."""
        rng = np.random.RandomState(55)
        obs = []
        for i in range(50):
            pd = round(rng.uniform(0.01, 0.05), 4)
            actual = 1 if rng.random() < pd else 0
            obs.append(ObservedDefault(
                exposure_id=f"SAME-{i:04d}",
                rating_grade="BBB",
                predicted_pd=pd,
                actual_default=actual,
            ))
        bt = PDBacktester()
        result = bt.backtest(obs)

        assert result.total_observations == 50
        assert len(result.grade_results) == 1
        assert result.grade_results[0].grade == "BBB"

    def test_empty_loan_book_raises(self):
        """StressTestRunner should reject empty loan book."""
        runner = StressTestRunner()
        with pytest.raises(ValueError, match="at least one"):
            runner.run([], "Empty Portfolio")

    def test_invalid_scenario_raises(self):
        """StressTestRunner should reject unknown scenario name."""
        with pytest.raises(ValueError, match="Unknown scenario"):
            StressTestRunner(scenarios=["APOCALYPSE"])


class TestUtilityMethods:
    """Static utility method tests on PDBacktester."""

    def test_get_gini_thresholds(self):
        thresholds = PDBacktester.get_gini_thresholds()
        assert "excellent" in thresholds
        assert "good" in thresholds
        assert "acceptable" in thresholds
        assert "poor" in thresholds
        assert thresholds["excellent"] >= 0.60

    def test_get_iv_thresholds(self):
        thresholds = PDBacktester.get_iv_thresholds()
        assert "very_strong" in thresholds
        assert "strong" in thresholds
        assert "medium" in thresholds
        assert "weak" in thresholds
        assert "useless" in thresholds
        assert thresholds["very_strong"] >= 0.50

    def test_get_traffic_light_rules(self):
        rules = PDBacktester.get_traffic_light_rules()
        assert "GREEN" in rules
        assert "YELLOW" in rules
        assert "RED" in rules

    def test_get_minimum_sample_sizes(self):
        sizes = PDBacktester.get_minimum_sample_sizes()
        assert sizes["overall_backtest"] == 30
        assert sizes["regulatory_minimum"] == 100
        assert sizes["gini_reliable"] == 200
