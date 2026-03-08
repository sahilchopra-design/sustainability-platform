"""
Unit tests for EAD Calculator — Basel III/IV Credit Conversion Factors

Tests cover:
  1.  CCF matrix: verify all 9 asset classes have CCFs, verify known values
  2.  Term loan (on-balance-sheet): EAD = outstanding * maturity adj
  3.  Revolving credit: corporate, retail, fully drawn
  4.  Undrawn commitments: standard, short maturity, specialised lending
  5.  Unconditionally cancellable: Basel IV 10% CCF
  6.  Guarantees and letters of credit
  7.  OTC derivatives: IR, FX, equity via simplified SA-CCR
  8.  Maturity adjustment (simplified): retail excluded, 2.5y neutral, caps
  9.  PD-based maturity adjustment (full Basel III b(PD) formula)
  10. Climate drawdown stress by sector/scenario
  11. Batch calculation with aggregation
  12. EADInput dataclass path (calculate_from_input)
  13. Edge cases: zero undrawn, unknown sector, methodology notes
  14. Standalone utility functions: get_ccf, get_maturity_adjustment
  15. Scenario comparison: severity ordering
"""
import math
import pytest

from services.ead_calculator import (
    EADCalculator,
    EADInput,
    EADResult,
    EADBatchResult,
    EADContribution,
    CCF_TABLE,
    REGULATORY_CCF,
    SHORT_MATURITY_CCF_OVERRIDES,
    CLIMATE_DRAWDOWN_STRESS,
    SACCR_ADDON_FACTORS,
    SACCR_ALPHA,
    MATURITY_CAPS,
    FacilityType,
    AssetClassEAD,
    get_ccf,
    get_maturity_adjustment,
)


# ---------------------------------------------------------------------------
# FIXTURES
# ---------------------------------------------------------------------------


@pytest.fixture
def calculator():
    """Default EAD calculator (base scenario)."""
    return EADCalculator(climate_scenario="base")


@pytest.fixture
def adverse_calculator():
    """Adverse scenario calculator."""
    return EADCalculator(climate_scenario="adverse")


@pytest.fixture
def severe_calculator():
    """Severe scenario calculator."""
    return EADCalculator(climate_scenario="severe")


# ---------------------------------------------------------------------------
# 1. CCF MATRIX — all 9 asset classes, known CCF values
# ---------------------------------------------------------------------------


class TestCCFMatrix:
    """Verify CCF matrix structure and known values."""

    def test_all_nine_asset_classes_present(self):
        """Every asset class should appear in at least one CCF entry."""
        asset_classes_in_table = set()
        for (_, aclass) in CCF_TABLE.keys():
            asset_classes_in_table.add(aclass)
        for ac in AssetClassEAD:
            assert ac.value in asset_classes_in_table, (
                f"{ac.value} missing from CCF_TABLE"
            )

    def test_regulatory_ccf_nested_dict(self):
        """REGULATORY_CCF should mirror CCF_TABLE in nested dict form."""
        assert isinstance(REGULATORY_CCF, dict)
        assert "TERM_LOAN" in REGULATORY_CCF
        assert "REVOLVING_CREDIT" in REGULATORY_CCF
        assert REGULATORY_CCF["TERM_LOAN"]["CORPORATE"] == 1.00

    def test_known_ccf_corporate_undrawn(self):
        assert CCF_TABLE[("UNDRAWN_COMMITMENT", "CORPORATE")] == 0.50

    def test_known_ccf_retail_revolving_undrawn(self):
        assert CCF_TABLE[("UNDRAWN_COMMITMENT", "RETAIL_REVOLVING")] == 0.40

    def test_known_ccf_sovereign_guarantee(self):
        assert CCF_TABLE[("GUARANTEE", "SOVEREIGN")] == 0.75

    def test_known_ccf_specialised_lending_undrawn(self):
        assert CCF_TABLE[("UNDRAWN_COMMITMENT", "SPECIALISED_LENDING")] == 0.75

    def test_known_ccf_unconditionally_cancellable(self):
        """Basel IV: UCC = 10% for all asset classes."""
        for ac in AssetClassEAD:
            key = ("UNCONDITIONALLY_CANCELLABLE", ac.value)
            assert CCF_TABLE[key] == 0.10, f"UCC CCF wrong for {ac.value}"

    def test_term_loan_always_100(self):
        """Term loans should always be 100% CCF for all asset classes."""
        for ac in AssetClassEAD:
            assert CCF_TABLE[("TERM_LOAN", ac.value)] == 1.00

    def test_saccr_alpha_constant(self):
        assert SACCR_ALPHA == 1.4

    def test_maturity_caps(self):
        assert MATURITY_CAPS["min"] == 1.0
        assert MATURITY_CAPS["max"] == 5.0
        assert MATURITY_CAPS["benchmark"] == 2.5

    def test_ccf_table_entry_count(self):
        """Should have at least 36 CCF combinations (9 classes x 4+ facility types)."""
        assert len(CCF_TABLE) >= 36


# ---------------------------------------------------------------------------
# 2. TERM LOAN (ON-BALANCE-SHEET) — CCF = 100%
# ---------------------------------------------------------------------------


class TestTermLoan:
    """Term loan is fully drawn; EAD should equal outstanding balance * maturity adj."""

    def test_corporate_term_loan(self, calculator):
        result = calculator.calculate(
            outstanding_balance=10_000_000,
            total_commitment=10_000_000,
            facility_type="TERM_LOAN",
            asset_class="CORPORATE",
            remaining_maturity_years=3.0,
            apply_climate_stress=False,
        )
        assert result.ccf_applied == 1.00
        assert result.undrawn_amount == 0.0
        assert result.ead_pre_climate == 10_000_000
        # Maturity adj at 3.0y: 1.0 + (3.0 - 2.5) * 0.025 = 1.0125
        assert result.maturity_adjustment_factor == pytest.approx(1.0125, abs=0.001)
        assert result.regulatory_ead == pytest.approx(10_125_000, abs=500)

    def test_sme_term_loan(self, calculator):
        result = calculator.calculate(
            outstanding_balance=500_000,
            total_commitment=500_000,
            facility_type="TERM_LOAN",
            asset_class="SME",
            remaining_maturity_years=2.0,
            apply_climate_stress=False,
        )
        assert result.undrawn_amount == 0.0
        assert result.ead_pre_climate == 500_000

    def test_sovereign_term_loan(self, calculator):
        result = calculator.calculate(
            outstanding_balance=100_000_000,
            total_commitment=100_000_000,
            facility_type="TERM_LOAN",
            asset_class="SOVEREIGN",
            remaining_maturity_years=5.0,
            apply_climate_stress=False,
        )
        # M=5.0: 1.0 + (5.0 - 2.5) * 0.025 = 1.0625
        assert result.maturity_adjustment_factor == pytest.approx(1.0625, abs=0.001)


# ---------------------------------------------------------------------------
# 3. REVOLVING CREDIT
# ---------------------------------------------------------------------------


class TestRevolvingCredit:
    """Revolving credit: EAD = drawn + CCF * undrawn."""

    def test_corporate_revolving_50pct_drawn(self, calculator):
        result = calculator.calculate(
            outstanding_balance=6_000_000,
            total_commitment=10_000_000,
            facility_type="REVOLVING_CREDIT",
            asset_class="CORPORATE",
            remaining_maturity_years=2.5,
            apply_climate_stress=False,
        )
        assert result.undrawn_amount == 4_000_000
        assert result.ccf_applied == 0.50
        expected_pre = 6_000_000 + 2_000_000
        assert result.ead_pre_climate == expected_pre

    def test_retail_revolving_lower_ccf(self, calculator):
        result = calculator.calculate(
            outstanding_balance=3_000,
            total_commitment=10_000,
            facility_type="REVOLVING_CREDIT",
            asset_class="RETAIL_REVOLVING",
            remaining_maturity_years=1.0,
            apply_climate_stress=False,
        )
        assert result.ccf_applied == 0.40
        assert result.contribution_breakdown.undrawn_commitment_ead == 2_800
        # Retail: no maturity adjustment
        assert result.maturity_adjustment_factor == 1.0

    def test_revolving_fully_drawn(self, calculator):
        result = calculator.calculate(
            outstanding_balance=10_000_000,
            total_commitment=10_000_000,
            facility_type="REVOLVING_CREDIT",
            asset_class="CORPORATE",
            apply_climate_stress=False,
        )
        assert result.undrawn_amount == 0.0
        assert result.contribution_breakdown.undrawn_commitment_ead == 0.0


# ---------------------------------------------------------------------------
# 4. UNDRAWN COMMITMENTS
# ---------------------------------------------------------------------------


class TestUndrawnCommitment:
    """Undrawn committed facilities with standard and short maturity."""

    def test_corporate_undrawn_standard(self, calculator):
        result = calculator.calculate(
            outstanding_balance=0,
            total_commitment=20_000_000,
            facility_type="UNDRAWN_COMMITMENT",
            asset_class="CORPORATE",
            remaining_maturity_years=3.0,
            is_short_maturity=False,
            apply_climate_stress=False,
        )
        assert result.ccf_applied == 0.50
        assert result.undrawn_amount == 20_000_000
        assert result.contribution_breakdown.undrawn_commitment_ead == 10_000_000

    def test_corporate_undrawn_short_maturity(self, calculator):
        result = calculator.calculate(
            outstanding_balance=0,
            total_commitment=20_000_000,
            facility_type="UNDRAWN_COMMITMENT",
            asset_class="CORPORATE",
            remaining_maturity_years=0.5,
            is_short_maturity=True,
            apply_climate_stress=False,
        )
        # Short maturity override: 20%
        assert result.ccf_applied == 0.20
        assert result.contribution_breakdown.undrawn_commitment_ead == 4_000_000

    def test_specialised_lending_undrawn(self, calculator):
        result = calculator.calculate(
            outstanding_balance=0,
            total_commitment=50_000_000,
            facility_type="UNDRAWN_COMMITMENT",
            asset_class="SPECIALISED_LENDING",
            apply_climate_stress=False,
        )
        assert result.ccf_applied == 0.75


# ---------------------------------------------------------------------------
# 5. UNCONDITIONALLY CANCELLABLE — Basel IV: 10%
# ---------------------------------------------------------------------------


class TestUnconditionallyCancellable:
    """Unconditionally cancellable commitments get 10% CCF under Basel IV."""

    def test_corporate_cancellable(self, calculator):
        result = calculator.calculate(
            outstanding_balance=0,
            total_commitment=5_000_000,
            facility_type="UNCONDITIONALLY_CANCELLABLE",
            asset_class="CORPORATE",
            apply_climate_stress=False,
        )
        assert result.ccf_applied == 0.10
        assert result.contribution_breakdown.undrawn_commitment_ead == 500_000

    def test_retail_cancellable(self, calculator):
        result = calculator.calculate(
            outstanding_balance=0,
            total_commitment=50_000,
            facility_type="UNCONDITIONALLY_CANCELLABLE",
            asset_class="RETAIL_REVOLVING",
            apply_climate_stress=False,
        )
        assert result.ccf_applied == 0.10


# ---------------------------------------------------------------------------
# 6. GUARANTEES AND LETTERS OF CREDIT
# ---------------------------------------------------------------------------


class TestGuarantees:
    """Guarantee and LC facilities."""

    def test_corporate_guarantee(self, calculator):
        result = calculator.calculate(
            outstanding_balance=0,
            total_commitment=0,
            facility_type="GUARANTEE",
            asset_class="CORPORATE",
            guarantee_amount=5_000_000,
            apply_climate_stress=False,
        )
        # Guarantee CCF for corporate = 0.75
        assert result.contribution_breakdown.guarantee_exposure == 3_750_000

    def test_financial_guarantee_100pct(self, calculator):
        result = calculator.calculate(
            outstanding_balance=0,
            total_commitment=0,
            facility_type="FINANCIAL_GUARANTEE",
            asset_class="CORPORATE",
            guarantee_amount=10_000_000,
            apply_climate_stress=False,
        )
        assert result.contribution_breakdown.guarantee_exposure == 10_000_000

    def test_trade_lc(self, calculator):
        result = calculator.calculate(
            outstanding_balance=0,
            total_commitment=0,
            facility_type="TRADE_LETTER_OF_CREDIT",
            asset_class="CORPORATE",
            guarantee_amount=2_000_000,
            apply_climate_stress=False,
        )
        # Trade LC = 20% for corporate
        assert result.contribution_breakdown.guarantee_exposure == 400_000

    def test_sovereign_guarantee(self, calculator):
        result = calculator.calculate(
            outstanding_balance=0,
            total_commitment=0,
            facility_type="GUARANTEE",
            asset_class="SOVEREIGN",
            guarantee_amount=1_000_000,
            apply_climate_stress=False,
        )
        # Sovereign guarantee CCF = 0.75 (from CCF_TABLE)
        assert result.contribution_breakdown.guarantee_exposure == 750_000


# ---------------------------------------------------------------------------
# 7. OTC DERIVATIVES (SA-CCR SIMPLIFIED)
# ---------------------------------------------------------------------------


class TestDerivatives:
    """OTC derivative add-on via simplified SA-CCR."""

    def test_interest_rate_derivative(self, calculator):
        result = calculator.calculate(
            outstanding_balance=0,
            total_commitment=0,
            facility_type="OTC_DERIVATIVE",
            asset_class="CORPORATE",
            derivative_notional=100_000_000,
            derivative_asset_class="interest_rate",
            derivative_maturity_years=3.0,
            apply_climate_stress=False,
        )
        # Factor = 0.005, maturity_factor = sqrt(3.0) ~ 1.732
        # Add-on = 1.4 * 0.005 * 100M * 1.732 ~ 1,212,436
        assert result.contribution_breakdown.derivative_addon > 1_000_000
        assert result.contribution_breakdown.derivative_addon < 1_500_000

    def test_fx_derivative(self, calculator):
        result = calculator.calculate(
            outstanding_balance=0,
            total_commitment=0,
            facility_type="OTC_DERIVATIVE",
            asset_class="BANK",
            derivative_notional=50_000_000,
            derivative_asset_class="fx",
            derivative_maturity_years=1.0,
            apply_climate_stress=False,
        )
        # Factor = 0.04, maturity_factor = 1.0 (non-IR)
        # Add-on = 1.4 * 0.04 * 50M * 1.0 = 2,800,000
        assert result.contribution_breakdown.derivative_addon == pytest.approx(2_800_000, abs=100)

    def test_equity_derivative(self, calculator):
        result = calculator.calculate(
            outstanding_balance=0,
            total_commitment=0,
            facility_type="OTC_DERIVATIVE",
            asset_class="CORPORATE",
            derivative_notional=10_000_000,
            derivative_asset_class="equity",
            derivative_maturity_years=2.0,
            apply_climate_stress=False,
        )
        # Factor = 0.32, maturity_factor = 1.0 (non-IR)
        # Add-on = 1.4 * 0.32 * 10M * 1.0 = 4,480,000
        assert result.contribution_breakdown.derivative_addon == pytest.approx(4_480_000, abs=100)

    def test_saccr_alpha_used(self, calculator):
        """Verify the SA-CCR alpha of 1.4 is applied."""
        result = calculator.calculate(
            outstanding_balance=0,
            total_commitment=0,
            facility_type="OTC_DERIVATIVE",
            asset_class="CORPORATE",
            derivative_notional=1_000_000,
            derivative_asset_class="fx",
            derivative_maturity_years=1.0,
            apply_climate_stress=False,
        )
        # 1.4 * 0.04 * 1M * 1.0 = 56,000
        assert result.contribution_breakdown.derivative_addon == pytest.approx(56_000, abs=10)


# ---------------------------------------------------------------------------
# 8. MATURITY ADJUSTMENT (SIMPLIFIED)
# ---------------------------------------------------------------------------


class TestMaturityAdjustment:
    """Effective maturity adjustment per Basel III Art. 162 (simplified)."""

    def test_retail_no_adjustment(self, calculator):
        """Retail exposures have no maturity adjustment."""
        for ac in ["RETAIL_REVOLVING", "RETAIL_MORTGAGE", "RETAIL_OTHER"]:
            result = calculator.calculate(
                outstanding_balance=100_000,
                total_commitment=100_000,
                facility_type="TERM_LOAN",
                asset_class=ac,
                remaining_maturity_years=5.0,
                apply_climate_stress=False,
            )
            assert result.maturity_adjustment_factor == 1.0

    def test_benchmark_maturity_2_5y(self, calculator):
        """At benchmark maturity (2.5y), adjustment = 1.0."""
        result = calculator.calculate(
            outstanding_balance=1_000_000,
            total_commitment=1_000_000,
            facility_type="TERM_LOAN",
            asset_class="CORPORATE",
            remaining_maturity_years=2.5,
            apply_climate_stress=False,
        )
        assert result.maturity_adjustment_factor == 1.0

    def test_short_maturity_1y(self, calculator):
        """1y maturity: adj = 1.0 + (1.0 - 2.5) * 0.025 = 0.9625."""
        result = calculator.calculate(
            outstanding_balance=1_000_000,
            total_commitment=1_000_000,
            facility_type="TERM_LOAN",
            asset_class="CORPORATE",
            remaining_maturity_years=0.1,  # Clamped to 1.0
            apply_climate_stress=False,
        )
        assert result.maturity_adjustment_factor == pytest.approx(0.9625, abs=0.001)

    def test_long_maturity_capped_at_5(self, calculator):
        """Maturity > 5y is capped at 5.0."""
        result = calculator.calculate(
            outstanding_balance=1_000_000,
            total_commitment=1_000_000,
            facility_type="TERM_LOAN",
            asset_class="CORPORATE",
            remaining_maturity_years=10.0,
            apply_climate_stress=False,
        )
        # M_eff = min(10, 5) = 5.0
        # adj = 1.0 + (5.0 - 2.5) * 0.025 = 1.0625
        assert result.maturity_adjustment_factor == pytest.approx(1.0625, abs=0.001)

    def test_default_maturity_neutral(self, calculator):
        """Default maturity (2.5y) should give neutral adjustment."""
        result = calculator.calculate(
            outstanding_balance=5_000_000,
            total_commitment=5_000_000,
            facility_type="TERM_LOAN",
            asset_class="SOVEREIGN",
            remaining_maturity_years=2.5,
            apply_climate_stress=False,
        )
        assert result.maturity_adjustment_factor == 1.0


# ---------------------------------------------------------------------------
# 9. PD-BASED MATURITY ADJUSTMENT (full Basel III b(PD) formula)
# ---------------------------------------------------------------------------


class TestPDMaturityAdjustment:
    """
    Full Basel III b(PD) formula:
      b  = (0.11852 - 0.05478 * ln(PD))^2
      MA = (1 + (M - 2.5) * b) / (1 - 1.5 * b)
    """

    def test_pd_maturity_at_benchmark(self, calculator):
        """At M=2.5y, MA = (1 + 0) / (1 - 1.5*b) which is > 1 for any PD."""
        result = calculator.calculate(
            outstanding_balance=1_000_000,
            total_commitment=1_000_000,
            facility_type="TERM_LOAN",
            asset_class="CORPORATE",
            remaining_maturity_years=2.5,
            pd=0.01,
            use_pd_maturity_adjustment=True,
            apply_climate_stress=False,
        )
        # At M=2.5: MA = 1 / (1 - 1.5*b)
        # b(0.01) = (0.11852 - 0.05478 * ln(0.01))^2
        # ln(0.01) = -4.60517 => 0.11852 + 0.25227 = 0.37079 => b = 0.13749
        # MA = 1 / (1 - 1.5 * 0.13749) = 1 / (1 - 0.20623) = 1 / 0.79377 ~ 1.260
        assert result.maturity_adjustment_factor > 1.0
        assert result.maturity_adjustment_factor == pytest.approx(1.260, abs=0.01)

    def test_pd_maturity_short_1y(self, calculator):
        """Short maturity (1y) should give lower MA than benchmark."""
        result = calculator.calculate(
            outstanding_balance=1_000_000,
            total_commitment=1_000_000,
            facility_type="TERM_LOAN",
            asset_class="CORPORATE",
            remaining_maturity_years=1.0,
            pd=0.01,
            use_pd_maturity_adjustment=True,
            apply_climate_stress=False,
        )
        # MA < value at benchmark 2.5y
        assert result.maturity_adjustment_factor < 1.260

    def test_pd_maturity_long_5y(self, calculator):
        """Long maturity (5y) should give higher MA."""
        result = calculator.calculate(
            outstanding_balance=1_000_000,
            total_commitment=1_000_000,
            facility_type="TERM_LOAN",
            asset_class="CORPORATE",
            remaining_maturity_years=5.0,
            pd=0.01,
            use_pd_maturity_adjustment=True,
            apply_climate_stress=False,
        )
        assert result.maturity_adjustment_factor > 1.260

    def test_pd_maturity_retail_exempt(self, calculator):
        """Retail exposures exempt from PD-based maturity adjustment too."""
        result = calculator.calculate(
            outstanding_balance=10_000,
            total_commitment=10_000,
            facility_type="TERM_LOAN",
            asset_class="RETAIL_REVOLVING",
            remaining_maturity_years=5.0,
            pd=0.05,
            use_pd_maturity_adjustment=True,
            apply_climate_stress=False,
        )
        assert result.maturity_adjustment_factor == 1.0

    def test_pd_maturity_high_pd(self, calculator):
        """Higher PD => smaller b => MA closer to 1."""
        result_low_pd = calculator.calculate(
            outstanding_balance=1_000_000,
            total_commitment=1_000_000,
            facility_type="TERM_LOAN",
            asset_class="CORPORATE",
            remaining_maturity_years=5.0,
            pd=0.001,
            use_pd_maturity_adjustment=True,
            apply_climate_stress=False,
        )
        result_high_pd = calculator.calculate(
            outstanding_balance=1_000_000,
            total_commitment=1_000_000,
            facility_type="TERM_LOAN",
            asset_class="CORPORATE",
            remaining_maturity_years=5.0,
            pd=0.10,
            use_pd_maturity_adjustment=True,
            apply_climate_stress=False,
        )
        # Lower PD => bigger b => bigger MA at long maturity
        assert result_low_pd.maturity_adjustment_factor > result_high_pd.maturity_adjustment_factor

    def test_pd_maturity_zero_pd_floored(self):
        """PD=0 should be floored to 0.0003 in utility function."""
        ma = get_maturity_adjustment(pd=0.0, maturity=2.5)
        # Should not raise; PD floored to 0.0003
        assert ma > 0.0


# ---------------------------------------------------------------------------
# 10. CLIMATE DRAWDOWN STRESS
# ---------------------------------------------------------------------------


class TestClimateStress:
    """Climate drawdown stress overlay on undrawn commitments."""

    def test_oil_gas_base_scenario(self, calculator):
        result = calculator.calculate(
            outstanding_balance=5_000_000,
            total_commitment=20_000_000,
            facility_type="REVOLVING_CREDIT",
            asset_class="CORPORATE",
            sector="Oil & Gas",
            apply_climate_stress=True,
        )
        assert result.climate_drawdown_stress_pct == pytest.approx(0.25, abs=0.01)
        assert result.contribution_breakdown.climate_ead_uplift == pytest.approx(3_750_000, abs=100)

    def test_oil_gas_adverse_scenario(self, adverse_calculator):
        result = adverse_calculator.calculate(
            outstanding_balance=5_000_000,
            total_commitment=20_000_000,
            facility_type="REVOLVING_CREDIT",
            asset_class="CORPORATE",
            sector="Oil & Gas",
            apply_climate_stress=True,
        )
        # Adverse: 0.25 * 1.5 = 37.5%
        assert result.climate_drawdown_stress_pct == pytest.approx(0.375, abs=0.01)

    def test_technology_low_stress(self, calculator):
        result = calculator.calculate(
            outstanding_balance=2_000_000,
            total_commitment=5_000_000,
            facility_type="REVOLVING_CREDIT",
            asset_class="CORPORATE",
            sector="Technology",
            apply_climate_stress=True,
        )
        assert result.climate_drawdown_stress_pct == pytest.approx(0.05, abs=0.01)

    def test_no_stress_on_fully_drawn(self, calculator):
        result = calculator.calculate(
            outstanding_balance=10_000_000,
            total_commitment=10_000_000,
            facility_type="TERM_LOAN",
            asset_class="CORPORATE",
            sector="Oil & Gas",
            apply_climate_stress=True,
        )
        assert result.contribution_breakdown.climate_ead_uplift == 0.0

    def test_stress_disabled(self, calculator):
        result = calculator.calculate(
            outstanding_balance=5_000_000,
            total_commitment=20_000_000,
            facility_type="REVOLVING_CREDIT",
            asset_class="CORPORATE",
            sector="Oil & Gas",
            apply_climate_stress=False,
        )
        assert result.contribution_breakdown.climate_ead_uplift == 0.0
        assert result.climate_drawdown_stress_pct == 0.0


# ---------------------------------------------------------------------------
# 11. BATCH CALCULATION
# ---------------------------------------------------------------------------


class TestBatchCalculation:
    """Batch EAD calculation for a mini loan book."""

    def test_batch_three_exposures(self, calculator):
        exposures = [
            {
                "outstanding_balance": 10_000_000,
                "total_commitment": 10_000_000,
                "facility_type": "TERM_LOAN",
                "asset_class": "CORPORATE",
                "remaining_maturity_years": 3.0,
                "sector": "Technology",
            },
            {
                "outstanding_balance": 5_000_000,
                "total_commitment": 15_000_000,
                "facility_type": "REVOLVING_CREDIT",
                "asset_class": "CORPORATE",
                "remaining_maturity_years": 2.0,
                "sector": "Oil & Gas",
            },
            {
                "outstanding_balance": 0,
                "total_commitment": 3_000_000,
                "facility_type": "UNDRAWN_COMMITMENT",
                "asset_class": "SME",
                "remaining_maturity_years": 1.5,
                "sector": "Retail",
            },
        ]
        batch = calculator.calculate_batch(exposures, apply_climate_stress=False)

        assert batch.count == 3
        assert batch.total_on_balance == 15_000_000
        assert batch.total_ead > 15_000_000
        assert "CORPORATE" in batch.by_asset_class
        assert "SME" in batch.by_asset_class
        assert "TERM_LOAN" in batch.by_facility_type
        assert "REVOLVING_CREDIT" in batch.by_facility_type
        assert len(batch.results) == 3

    def test_batch_weighted_avg_ccf(self, calculator):
        exposures = [
            {
                "outstanding_balance": 0,
                "total_commitment": 10_000_000,
                "facility_type": "UNDRAWN_COMMITMENT",
                "asset_class": "CORPORATE",
            },
            {
                "outstanding_balance": 0,
                "total_commitment": 5_000_000,
                "facility_type": "UNCONDITIONALLY_CANCELLABLE",
                "asset_class": "CORPORATE",
            },
        ]
        batch = calculator.calculate_batch(exposures, apply_climate_stress=False)
        # Weighted avg CCF: (0.5 * 10M + 0.1 * 5M) / (10M + 5M) = 5.5M/15M ~ 0.3667
        assert batch.weighted_avg_ccf == pytest.approx(0.3667, abs=0.01)

    def test_batch_single_exposure(self, calculator):
        exposures = [
            {
                "outstanding_balance": 1_000_000,
                "total_commitment": 2_000_000,
                "facility_type": "REVOLVING_CREDIT",
                "asset_class": "CORPORATE",
                "remaining_maturity_years": 2.5,
            },
        ]
        batch = calculator.calculate_batch(exposures, apply_climate_stress=False)

        individual = calculator.calculate(
            outstanding_balance=1_000_000,
            total_commitment=2_000_000,
            facility_type="REVOLVING_CREDIT",
            asset_class="CORPORATE",
            remaining_maturity_years=2.5,
            apply_climate_stress=False,
        )
        assert batch.total_ead == individual.regulatory_ead

    def test_batch_20_mixed_exposures(self, calculator):
        """Batch of 20 mixed exposures should complete without error."""
        asset_classes = ["CORPORATE", "SME", "RETAIL_REVOLVING", "SOVEREIGN", "BANK"]
        facility_types = [
            "TERM_LOAN", "REVOLVING_CREDIT", "UNDRAWN_COMMITMENT",
            "GUARANTEE", "OTC_DERIVATIVE",
        ]
        sectors = ["Oil & Gas", "Technology", "Real Estate", "Airlines"]

        exposures = []
        for i in range(20):
            ac = asset_classes[i % len(asset_classes)]
            ft = facility_types[i % len(facility_types)]
            sector = sectors[i % len(sectors)]
            exposures.append({
                "outstanding_balance": 1_000_000 * (i + 1),
                "total_commitment": 2_000_000 * (i + 1),
                "facility_type": ft,
                "asset_class": ac,
                "remaining_maturity_years": 1.0 + (i % 5),
                "sector": sector,
                "derivative_notional": 5_000_000 if ft == "OTC_DERIVATIVE" else 0,
                "derivative_asset_class": "fx",
                "guarantee_amount": 1_000_000 if ft == "GUARANTEE" else 0,
            })

        batch = calculator.calculate_batch(exposures, apply_climate_stress=True)
        assert batch.count == 20
        assert batch.total_ead > 0
        assert len(batch.results) == 20
        # All results should have positive or zero EAD
        for r in batch.results:
            assert r.regulatory_ead >= 0


# ---------------------------------------------------------------------------
# 12. EADInput DATACLASS
# ---------------------------------------------------------------------------


class TestEADInput:
    """Test calculate_from_input and calculate_batch_from_inputs paths."""

    def test_calculate_from_input(self, calculator):
        inp = EADInput(
            outstanding_balance=5_000_000,
            total_commitment=10_000_000,
            facility_type="REVOLVING_CREDIT",
            asset_class="CORPORATE",
            remaining_maturity_years=3.0,
            sector="Technology",
            apply_climate_stress=False,
        )
        result = calculator.calculate_from_input(inp)
        assert result.regulatory_ead > 0
        assert result.ccf_applied == 0.50

    def test_input_with_pd_maturity(self, calculator):
        inp = EADInput(
            outstanding_balance=1_000_000,
            total_commitment=1_000_000,
            facility_type="TERM_LOAN",
            asset_class="CORPORATE",
            remaining_maturity_years=5.0,
            pd=0.02,
            use_pd_maturity_adjustment=True,
            apply_climate_stress=False,
        )
        result = calculator.calculate_from_input(inp)
        # PD-based maturity adjustment should differ from simplified
        assert result.maturity_adjustment_factor != pytest.approx(1.0625, abs=0.001)

    def test_batch_from_inputs(self, calculator):
        inputs = [
            EADInput(
                outstanding_balance=5_000_000,
                total_commitment=10_000_000,
                facility_type="REVOLVING_CREDIT",
                asset_class="CORPORATE",
                apply_climate_stress=False,
            ),
            EADInput(
                outstanding_balance=0,
                total_commitment=3_000_000,
                facility_type="UNDRAWN_COMMITMENT",
                asset_class="SME",
                apply_climate_stress=False,
            ),
        ]
        batch = calculator.calculate_batch_from_inputs(inputs)
        assert batch.count == 2
        assert batch.total_ead > 0


# ---------------------------------------------------------------------------
# 13. EDGE CASES AND VALIDATION
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Edge cases and boundary value tests."""

    def test_zero_commitment(self, calculator):
        result = calculator.calculate(
            outstanding_balance=0,
            total_commitment=0,
            facility_type="TERM_LOAN",
            asset_class="CORPORATE",
            apply_climate_stress=False,
        )
        assert result.regulatory_ead == 0.0

    def test_zero_undrawn(self, calculator):
        """Outstanding == commitment => zero undrawn."""
        result = calculator.calculate(
            outstanding_balance=5_000_000,
            total_commitment=5_000_000,
            facility_type="REVOLVING_CREDIT",
            asset_class="CORPORATE",
            apply_climate_stress=False,
        )
        assert result.undrawn_amount == 0.0
        assert result.contribution_breakdown.undrawn_commitment_ead == 0.0

    def test_zero_pd_maturity_adjustment(self):
        """PD=0 should be handled gracefully (floored internally)."""
        ma = get_maturity_adjustment(pd=0.0, maturity=2.5)
        assert ma > 0.0
        assert math.isfinite(ma)

    def test_unknown_sector_default_stress(self, calculator):
        result = calculator.calculate(
            outstanding_balance=0,
            total_commitment=10_000_000,
            facility_type="REVOLVING_CREDIT",
            asset_class="CORPORATE",
            sector="Unknown_Sector_XYZ",
            apply_climate_stress=True,
        )
        assert result.climate_drawdown_stress_pct == pytest.approx(0.05, abs=0.01)

    def test_unknown_asset_class_fallback(self, calculator):
        result = calculator.calculate(
            outstanding_balance=0,
            total_commitment=10_000_000,
            facility_type="REVOLVING_CREDIT",
            asset_class="NONEXISTENT_CLASS",
            apply_climate_stress=False,
        )
        # Should fallback to CORPORATE = 0.50
        assert result.ccf_applied == 0.50

    def test_methodology_notes_populated(self, calculator):
        result = calculator.calculate(
            outstanding_balance=5_000_000,
            total_commitment=10_000_000,
            facility_type="REVOLVING_CREDIT",
            asset_class="CORPORATE",
            apply_climate_stress=True,
            sector="Oil & Gas",
        )
        assert len(result.methodology_notes) > 0
        notes_text = " ".join(result.methodology_notes)
        assert "Undrawn" in notes_text
        assert "CCF" in notes_text

    def test_ead_non_negative(self, calculator):
        """Regulatory EAD must never be negative."""
        result = calculator.calculate(
            outstanding_balance=0,
            total_commitment=100,
            facility_type="UNCONDITIONALLY_CANCELLABLE",
            asset_class="CORPORATE",
            remaining_maturity_years=0.1,
            apply_climate_stress=False,
        )
        assert result.regulatory_ead >= 0.0

    def test_combined_facility(self, calculator):
        result = calculator.calculate(
            outstanding_balance=5_000_000,
            total_commitment=15_000_000,
            facility_type="GUARANTEE",
            asset_class="CORPORATE",
            guarantee_amount=3_000_000,
            apply_climate_stress=False,
        )
        assert result.contribution_breakdown.undrawn_commitment_ead > 0
        assert result.contribution_breakdown.guarantee_exposure > 0


# ---------------------------------------------------------------------------
# 14. STANDALONE UTILITY FUNCTIONS
# ---------------------------------------------------------------------------


class TestUtilities:
    """Test get_ccf and get_maturity_adjustment standalone functions."""

    # -- get_ccf --

    def test_get_ccf_corporate_undrawn(self):
        assert get_ccf("CORPORATE", "UNDRAWN_COMMITMENT") == 0.50

    def test_get_ccf_retail_revolving_revolving(self):
        assert get_ccf("RETAIL_REVOLVING", "REVOLVING_CREDIT") == 0.40

    def test_get_ccf_sovereign_guarantee(self):
        assert get_ccf("SOVEREIGN", "GUARANTEE") == 0.75

    def test_get_ccf_fallback_to_corporate(self):
        """Unknown asset class should fallback to CORPORATE for same facility."""
        ccf = get_ccf("NONEXISTENT", "REVOLVING_CREDIT")
        assert ccf == 0.50  # CORPORATE REVOLVING_CREDIT

    def test_get_ccf_fallback_to_100(self):
        """Completely unknown combination falls back to 100%."""
        ccf = get_ccf("NONEXISTENT", "NONEXISTENT_FACILITY")
        assert ccf == 1.00

    def test_get_ccf_specialised_lending_guarantee(self):
        assert get_ccf("SPECIALISED_LENDING", "GUARANTEE") == 1.00

    # -- get_maturity_adjustment --

    def test_maturity_adjustment_benchmark(self):
        """At M=2.5y, only denominator effect: MA = 1 / (1 - 1.5*b)."""
        ma = get_maturity_adjustment(pd=0.01, maturity=2.5)
        # Should be > 1.0 because of denominator effect
        assert ma > 1.0

    def test_maturity_adjustment_short(self):
        """Short maturity (1y) < benchmark maturity (2.5y)."""
        ma_short = get_maturity_adjustment(pd=0.01, maturity=1.0)
        ma_bench = get_maturity_adjustment(pd=0.01, maturity=2.5)
        assert ma_short < ma_bench

    def test_maturity_adjustment_long(self):
        """Long maturity (5y) > benchmark maturity (2.5y)."""
        ma_long = get_maturity_adjustment(pd=0.01, maturity=5.0)
        ma_bench = get_maturity_adjustment(pd=0.01, maturity=2.5)
        assert ma_long > ma_bench

    def test_maturity_adjustment_clamped_below_1(self):
        """Maturity < 1 should be clamped to 1.0."""
        ma_half = get_maturity_adjustment(pd=0.01, maturity=0.5)
        ma_one = get_maturity_adjustment(pd=0.01, maturity=1.0)
        assert ma_half == pytest.approx(ma_one, abs=1e-6)

    def test_maturity_adjustment_clamped_above_5(self):
        """Maturity > 5 should be clamped to 5.0."""
        ma_10 = get_maturity_adjustment(pd=0.01, maturity=10.0)
        ma_5 = get_maturity_adjustment(pd=0.01, maturity=5.0)
        assert ma_10 == pytest.approx(ma_5, abs=1e-6)

    def test_maturity_adjustment_very_low_pd(self):
        """Very low PD => larger b => larger MA spread."""
        ma = get_maturity_adjustment(pd=0.0003, maturity=5.0)
        assert ma > 1.5  # Significant maturity effect at low PD

    def test_maturity_adjustment_high_pd(self):
        """High PD => smaller b => MA closer to 1."""
        ma = get_maturity_adjustment(pd=0.20, maturity=5.0)
        # Should still be > 1 at 5y, but smaller than low-PD case
        assert ma > 1.0
        assert ma < 1.5

    def test_maturity_adjustment_non_negative(self):
        """MA should always be non-negative."""
        for pd_val in [0.0, 0.0001, 0.001, 0.01, 0.05, 0.10, 0.50, 1.0]:
            for m in [0.0, 0.5, 1.0, 2.5, 5.0, 10.0]:
                ma = get_maturity_adjustment(pd_val, m)
                assert ma >= 0.0, f"MA negative for pd={pd_val}, m={m}"
                assert math.isfinite(ma), f"MA not finite for pd={pd_val}, m={m}"


# ---------------------------------------------------------------------------
# 15. UTILITY QUERY METHODS (static)
# ---------------------------------------------------------------------------


class TestUtilityMethods:
    """Test static utility/query methods on EADCalculator class."""

    def test_get_ccf_table(self):
        table = EADCalculator.get_ccf_table()
        assert isinstance(table, dict)
        assert "TERM_LOAN" in table
        assert "REVOLVING_CREDIT" in table
        assert table["TERM_LOAN"]["CORPORATE"] == 1.00

    def test_get_supported_facility_types(self):
        types = EADCalculator.get_supported_facility_types()
        assert "TERM_LOAN" in types
        assert "REVOLVING_CREDIT" in types
        assert len(types) == 13  # All facility types

    def test_get_supported_asset_classes(self):
        classes = EADCalculator.get_supported_asset_classes()
        assert "CORPORATE" in classes
        assert "RETAIL_REVOLVING" in classes
        assert len(classes) == 9  # All asset classes

    def test_get_climate_stress_factors(self):
        factors = EADCalculator.get_climate_stress_factors()
        assert "Oil & Gas" in factors
        assert factors["Oil & Gas"] == 0.25
        assert factors["Technology"] == 0.05

    def test_get_scenario_info(self, calculator):
        info = calculator.get_scenario_info()
        assert info["climate_scenario"] == "base"
        assert info["scenario_multiplier"] == 1.0
        assert "optimistic" in info["available_scenarios"]


# ---------------------------------------------------------------------------
# 16. SCENARIO COMPARISON
# ---------------------------------------------------------------------------


class TestScenarioComparison:
    """Compare EAD across climate scenarios."""

    def test_ead_increases_with_severity(self):
        eads = {}
        for scenario in ["optimistic", "base", "adverse", "severe"]:
            calc = EADCalculator(climate_scenario=scenario)
            result = calc.calculate(
                outstanding_balance=5_000_000,
                total_commitment=20_000_000,
                facility_type="REVOLVING_CREDIT",
                asset_class="CORPORATE",
                sector="Oil & Gas",
                apply_climate_stress=True,
            )
            eads[scenario] = result.ead_post_climate

        assert eads["optimistic"] < eads["base"]
        assert eads["base"] < eads["adverse"]
        assert eads["adverse"] < eads["severe"]

    def test_optimistic_halves_stress(self):
        calc = EADCalculator(climate_scenario="optimistic")
        result = calc.calculate(
            outstanding_balance=0,
            total_commitment=10_000_000,
            facility_type="REVOLVING_CREDIT",
            asset_class="CORPORATE",
            sector="Oil & Gas",
            apply_climate_stress=True,
        )
        # Base stress for Oil & Gas = 0.25, optimistic = 0.25 * 0.5 = 0.125
        assert result.climate_drawdown_stress_pct == pytest.approx(0.125, abs=0.01)
