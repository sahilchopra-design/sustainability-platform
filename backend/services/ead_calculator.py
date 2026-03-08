"""
EAD Calculator — Exposure at Default with Basel III/IV Credit Conversion Factors

Implements EAD calculation per:
  - Basel III/IV CRR3 Art. 111, 166-168 (EAD determination)
  - CRR Art. 111(1): On-balance-sheet + CCF * off-balance-sheet
  - CRR Art. 166: CCF for commitments, guarantees, derivatives
  - CRR2 Art. 111: CCF by asset class and facility type
  - Basel III Art. 162: Effective maturity adjustment with PD correlation
  - EBA RTS 2016/06: Downturn EAD estimation
  - IFRS 9 B5.5.32: EAD in lifetime ECL shall reflect expected drawdowns
  - Basel Committee BCBS d424 (Dec 2017): Standardised approach CCFs
  - BCBS d279: SA-CCR for OTC derivatives (alpha = 1.4)

Key formulae:
  EAD = Outstanding_Balance + CCF * Undrawn_Commitment + Add_On(Derivatives) + Guarantees_Exposure
  M   = max(1, min(5, effective_maturity))                      [Art. 162]
  b   = (0.11852 - 0.05478 * ln(PD))^2                         [Art. 153(1)]
  MA  = (1 + (M - 2.5) * b) / (1 - 1.5 * b)                   [Art. 153(1)]

CCF categories (Standardised Approach):
  - 0%:   Unconditionally cancellable commitments (revocable at any time)
  - 10%:  Short-term self-liquidating trade letters of credit / Basel IV UCC
  - 20%:  Commitments with < 1 year maturity, performance standby LCs
  - 40%:  Undrawn revolving credit facilities (retail), note issuance facilities
  - 50%:  Commitments with > 1 year maturity, transaction-related contingencies
  - 75%:  Direct credit substitutes (guarantees)
  - 100%: Securities lending, margin lending, repo-style transactions

Author: EAD Calculator Module
Version: 2.0.0
Date: 2026-03-08
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# ENUMERATIONS
# ---------------------------------------------------------------------------


class FacilityType(Enum):
    """Off-balance-sheet facility types per CRR Art. 111, Annex I."""
    TERM_LOAN = "TERM_LOAN"                          # Fully drawn; CCF = 100% (on-balance-sheet)
    REVOLVING_CREDIT = "REVOLVING_CREDIT"             # Drawn + undrawn; CCF on undrawn portion
    UNDRAWN_COMMITMENT = "UNDRAWN_COMMITMENT"         # Undrawn committed facility
    UNCONDITIONALLY_CANCELLABLE = "UNCONDITIONALLY_CANCELLABLE"  # Revocable at any time
    TRADE_LETTER_OF_CREDIT = "TRADE_LETTER_OF_CREDIT"  # Self-liquidating trade LCs
    STANDBY_LETTER_OF_CREDIT = "STANDBY_LETTER_OF_CREDIT"  # Performance/financial standby LCs
    GUARANTEE = "GUARANTEE"                            # Direct credit substitutes
    FINANCIAL_GUARANTEE = "FINANCIAL_GUARANTEE"        # Financial guarantee contracts (IFRS 9)
    NOTE_ISSUANCE_FACILITY = "NOTE_ISSUANCE_FACILITY"  # NIFs and RUFs
    REPO_STYLE = "REPO_STYLE"                          # Repo, reverse repo, securities lending
    OTC_DERIVATIVE = "OTC_DERIVATIVE"                  # OTC derivative exposure (SA-CCR)
    MARGIN_LENDING = "MARGIN_LENDING"                  # Margin lending facilities
    TRANSACTION_CONTINGENCY = "TRANSACTION_CONTINGENCY"  # Transaction-related contingencies


class AssetClassEAD(Enum):
    """Basel asset classes for EAD/CCF determination. CRR3 Art. 112-152."""
    CORPORATE = "CORPORATE"
    SME = "SME"
    RETAIL_REVOLVING = "RETAIL_REVOLVING"
    RETAIL_MORTGAGE = "RETAIL_MORTGAGE"
    RETAIL_OTHER = "RETAIL_OTHER"
    SOVEREIGN = "SOVEREIGN"
    BANK = "BANK"
    SPECIALISED_LENDING = "SPECIALISED_LENDING"   # Project finance, object finance
    EQUITY = "EQUITY"


class MaturityBucket(Enum):
    """Maturity buckets for CCF differentiation."""
    LESS_THAN_1Y = "LESS_THAN_1Y"
    ONE_TO_5Y = "ONE_TO_5Y"
    GREATER_THAN_5Y = "GREATER_THAN_5Y"


# ---------------------------------------------------------------------------
# DATACLASSES
# ---------------------------------------------------------------------------


@dataclass
class EADInput:
    """
    Input data for a single EAD calculation.

    Follows the same dataclass-in / dataclass-out pattern as PDResult/PDContribution
    in pd_calculator.py, allowing callers to construct typed inputs rather than
    passing raw keyword arguments.
    """
    outstanding_balance: float = 0.0
    total_commitment: float = 0.0
    facility_type: str = "TERM_LOAN"
    asset_class: str = "CORPORATE"
    remaining_maturity_years: float = 2.5
    sector: str = "Corporate"
    is_short_maturity: bool = False
    derivative_notional: float = 0.0
    derivative_asset_class: str = "interest_rate"
    derivative_maturity_years: float = 0.0
    guarantee_amount: float = 0.0
    apply_climate_stress: bool = True
    pd: float = 0.01  # PD for maturity adjustment b(PD) formula; default 1%
    use_pd_maturity_adjustment: bool = False  # If True, use full Basel III b(PD) formula


@dataclass
class EADContribution:
    """Breakdown of EAD components."""
    on_balance_sheet: float           # Outstanding drawn amount
    undrawn_commitment_ead: float     # CCF * undrawn amount
    guarantee_exposure: float         # Guarantee/LC exposure after CCF
    derivative_addon: float           # OTC derivative add-on (SA-CCR simplified)
    maturity_adjustment: float        # Effective maturity adjustment factor
    climate_ead_uplift: float         # Climate-driven drawdown acceleration
    total_ead: float


@dataclass
class EADResult:
    """EAD calculation result with full breakdown."""
    facility_type: str
    asset_class: str
    outstanding_balance: float
    total_commitment: float
    undrawn_amount: float
    ccf_applied: float                 # Credit conversion factor used (0-1)
    effective_maturity_years: float
    maturity_adjustment_factor: float  # Basel III M-adjustment
    ead_pre_climate: float             # EAD before climate overlay
    ead_post_climate: float            # EAD after climate drawdown stress
    climate_drawdown_stress_pct: float # Additional drawdown % under stress
    contribution_breakdown: EADContribution
    regulatory_ead: float              # Final regulatory EAD
    methodology_notes: List[str]       # Audit trail of calculation steps


@dataclass
class EADBatchResult:
    """Batch EAD calculation summary."""
    total_ead: float
    total_on_balance: float
    total_off_balance_ead: float
    weighted_avg_ccf: float
    count: int
    by_asset_class: Dict[str, float]
    by_facility_type: Dict[str, float]
    results: List[EADResult]


# ---------------------------------------------------------------------------
# REGULATORY CONSTANTS
# ---------------------------------------------------------------------------

# SA-CCR alpha multiplier — CRR Art. 274
SACCR_ALPHA: float = 1.4

# Maturity caps per Basel III Art. 162
MATURITY_CAPS = {
    "min": 1.0,   # Floor for effective maturity
    "max": 5.0,   # Cap for effective maturity
    "benchmark": 2.5,  # Neutral maturity
}


# ---------------------------------------------------------------------------
# CCF TABLES — Basel III Standardised Approach
# ---------------------------------------------------------------------------

# CCF by facility type x asset class (Standardised Approach)
# CRR Art. 111, Annex I; BCBS d424 Table 12
# Format: (facility_type, asset_class) -> CCF
CCF_TABLE: Dict[Tuple[str, str], float] = {
    # Term loans — fully drawn, always 100%
    ("TERM_LOAN", "CORPORATE"): 1.00,
    ("TERM_LOAN", "SME"): 1.00,
    ("TERM_LOAN", "RETAIL_REVOLVING"): 1.00,
    ("TERM_LOAN", "RETAIL_MORTGAGE"): 1.00,
    ("TERM_LOAN", "RETAIL_OTHER"): 1.00,
    ("TERM_LOAN", "SOVEREIGN"): 1.00,
    ("TERM_LOAN", "BANK"): 1.00,
    ("TERM_LOAN", "SPECIALISED_LENDING"): 1.00,
    ("TERM_LOAN", "EQUITY"): 1.00,

    # Revolving credit — varies by asset class
    ("REVOLVING_CREDIT", "CORPORATE"): 0.50,
    ("REVOLVING_CREDIT", "SME"): 0.50,
    ("REVOLVING_CREDIT", "RETAIL_REVOLVING"): 0.40,
    ("REVOLVING_CREDIT", "RETAIL_MORTGAGE"): 0.50,
    ("REVOLVING_CREDIT", "RETAIL_OTHER"): 0.40,
    ("REVOLVING_CREDIT", "SOVEREIGN"): 0.50,
    ("REVOLVING_CREDIT", "BANK"): 0.50,
    ("REVOLVING_CREDIT", "SPECIALISED_LENDING"): 0.50,
    ("REVOLVING_CREDIT", "EQUITY"): 0.50,

    # Undrawn commitments > 1 year
    ("UNDRAWN_COMMITMENT", "CORPORATE"): 0.50,
    ("UNDRAWN_COMMITMENT", "SME"): 0.50,
    ("UNDRAWN_COMMITMENT", "RETAIL_REVOLVING"): 0.40,
    ("UNDRAWN_COMMITMENT", "RETAIL_MORTGAGE"): 0.50,
    ("UNDRAWN_COMMITMENT", "RETAIL_OTHER"): 0.40,
    ("UNDRAWN_COMMITMENT", "SOVEREIGN"): 0.40,
    ("UNDRAWN_COMMITMENT", "BANK"): 0.40,
    ("UNDRAWN_COMMITMENT", "SPECIALISED_LENDING"): 0.75,
    ("UNDRAWN_COMMITMENT", "EQUITY"): 0.50,

    # Unconditionally cancellable — Basel IV: 10% (up from 0%)
    ("UNCONDITIONALLY_CANCELLABLE", "CORPORATE"): 0.10,
    ("UNCONDITIONALLY_CANCELLABLE", "SME"): 0.10,
    ("UNCONDITIONALLY_CANCELLABLE", "RETAIL_REVOLVING"): 0.10,
    ("UNCONDITIONALLY_CANCELLABLE", "RETAIL_MORTGAGE"): 0.10,
    ("UNCONDITIONALLY_CANCELLABLE", "RETAIL_OTHER"): 0.10,
    ("UNCONDITIONALLY_CANCELLABLE", "SOVEREIGN"): 0.10,
    ("UNCONDITIONALLY_CANCELLABLE", "BANK"): 0.10,
    ("UNCONDITIONALLY_CANCELLABLE", "SPECIALISED_LENDING"): 0.10,
    ("UNCONDITIONALLY_CANCELLABLE", "EQUITY"): 0.10,

    # Trade letters of credit — self-liquidating
    ("TRADE_LETTER_OF_CREDIT", "CORPORATE"): 0.20,
    ("TRADE_LETTER_OF_CREDIT", "SME"): 0.20,
    ("TRADE_LETTER_OF_CREDIT", "RETAIL_OTHER"): 0.20,
    ("TRADE_LETTER_OF_CREDIT", "SOVEREIGN"): 0.10,
    ("TRADE_LETTER_OF_CREDIT", "BANK"): 0.20,
    ("TRADE_LETTER_OF_CREDIT", "SPECIALISED_LENDING"): 0.20,

    # Standby letters of credit (performance)
    ("STANDBY_LETTER_OF_CREDIT", "CORPORATE"): 0.50,
    ("STANDBY_LETTER_OF_CREDIT", "SME"): 0.50,
    ("STANDBY_LETTER_OF_CREDIT", "RETAIL_OTHER"): 0.50,
    ("STANDBY_LETTER_OF_CREDIT", "SOVEREIGN"): 0.50,
    ("STANDBY_LETTER_OF_CREDIT", "BANK"): 0.50,
    ("STANDBY_LETTER_OF_CREDIT", "SPECIALISED_LENDING"): 0.50,

    # Guarantees — direct credit substitutes
    ("GUARANTEE", "CORPORATE"): 0.75,
    ("GUARANTEE", "SME"): 0.75,
    ("GUARANTEE", "RETAIL_OTHER"): 0.75,
    ("GUARANTEE", "SOVEREIGN"): 0.75,
    ("GUARANTEE", "BANK"): 0.75,
    ("GUARANTEE", "SPECIALISED_LENDING"): 1.00,

    # Financial guarantees (IFRS 9 scope)
    ("FINANCIAL_GUARANTEE", "CORPORATE"): 1.00,
    ("FINANCIAL_GUARANTEE", "SME"): 1.00,
    ("FINANCIAL_GUARANTEE", "SOVEREIGN"): 1.00,
    ("FINANCIAL_GUARANTEE", "BANK"): 1.00,
    ("FINANCIAL_GUARANTEE", "SPECIALISED_LENDING"): 1.00,

    # Note issuance facilities
    ("NOTE_ISSUANCE_FACILITY", "CORPORATE"): 0.40,
    ("NOTE_ISSUANCE_FACILITY", "SME"): 0.40,
    ("NOTE_ISSUANCE_FACILITY", "SOVEREIGN"): 0.40,
    ("NOTE_ISSUANCE_FACILITY", "BANK"): 0.40,

    # Repo-style transactions
    ("REPO_STYLE", "CORPORATE"): 1.00,
    ("REPO_STYLE", "SOVEREIGN"): 1.00,
    ("REPO_STYLE", "BANK"): 1.00,
    ("REPO_STYLE", "EQUITY"): 1.00,

    # OTC derivatives — CCF not used (SA-CCR instead); placeholder
    ("OTC_DERIVATIVE", "CORPORATE"): 1.00,
    ("OTC_DERIVATIVE", "SME"): 1.00,
    ("OTC_DERIVATIVE", "SOVEREIGN"): 1.00,
    ("OTC_DERIVATIVE", "BANK"): 1.00,

    # Margin lending
    ("MARGIN_LENDING", "CORPORATE"): 1.00,
    ("MARGIN_LENDING", "RETAIL_OTHER"): 1.00,
    ("MARGIN_LENDING", "BANK"): 1.00,

    # Transaction-related contingencies
    ("TRANSACTION_CONTINGENCY", "CORPORATE"): 0.50,
    ("TRANSACTION_CONTINGENCY", "SME"): 0.50,
    ("TRANSACTION_CONTINGENCY", "SOVEREIGN"): 0.50,
    ("TRANSACTION_CONTINGENCY", "BANK"): 0.50,
    ("TRANSACTION_CONTINGENCY", "SPECIALISED_LENDING"): 0.50,
}


# REGULATORY_CCF — nested dict version for API consumption
# Format: { facility_type: { asset_class: ccf } }
def _build_regulatory_ccf() -> Dict[str, Dict[str, float]]:
    """Build nested dict from flat CCF_TABLE for easy lookups."""
    result: Dict[str, Dict[str, float]] = {}
    for (ftype, aclass), ccf in CCF_TABLE.items():
        if ftype not in result:
            result[ftype] = {}
        result[ftype][aclass] = ccf
    return result


REGULATORY_CCF: Dict[str, Dict[str, float]] = _build_regulatory_ccf()


# Short-maturity CCF overrides (< 1 year)
SHORT_MATURITY_CCF_OVERRIDES: Dict[str, float] = {
    "UNDRAWN_COMMITMENT": 0.20,       # 20% for < 1 year commitments
    "REVOLVING_CREDIT": 0.40,          # Same for retail revolving (no maturity distinction)
    "NOTE_ISSUANCE_FACILITY": 0.20,
    "TRANSACTION_CONTINGENCY": 0.20,
}


# Climate stress drawdown factors by sector
# In climate stress, corporates draw down committed facilities faster
CLIMATE_DRAWDOWN_STRESS: Dict[str, float] = {
    "Power Generation": 0.15,       # Moderate stress drawdown
    "Oil & Gas": 0.25,              # High — stranded asset funding needs
    "Metals & Mining": 0.20,
    "Automotive": 0.18,
    "Airlines": 0.22,               # High — revenue disruption
    "Real Estate": 0.12,
    "Technology": 0.05,
    "Healthcare": 0.03,
    "Financial": 0.08,
    "Agriculture": 0.10,
    "Shipping": 0.20,
    "Chemicals": 0.15,
    "Construction": 0.14,
    "Retail": 0.08,
    "Telecommunications": 0.04,
    "Utilities": 0.10,
}


# SA-CCR add-on factors by derivative asset class (simplified)
# CRR Art. 274-280, Table 2 of BCBS d279
SACCR_ADDON_FACTORS: Dict[str, float] = {
    "interest_rate": 0.005,    # 0.5% of notional per year of maturity
    "fx": 0.04,                # 4% of notional
    "credit": 0.01,            # 1% of notional (IG)
    "equity": 0.32,            # 32% of notional
    "commodity": 0.18,         # 18% of notional
}


# ---------------------------------------------------------------------------
# STANDALONE UTILITY FUNCTIONS
# ---------------------------------------------------------------------------


def get_ccf(asset_class: str, facility_type: str) -> float:
    """
    Utility: look up the CCF for a given asset class and facility type.

    Returns the regulatory CCF from the flat CCF_TABLE.  Falls back to
    CORPORATE for the same facility type, then to 1.00 (conservative).

    Args:
        asset_class: Basel asset class string (e.g. 'CORPORATE')
        facility_type: Facility type string (e.g. 'UNDRAWN_COMMITMENT')

    Returns:
        CCF as a float in [0, 1].
    """
    key = (facility_type, asset_class)
    if key in CCF_TABLE:
        return CCF_TABLE[key]

    # Fallback to CORPORATE
    fallback = (facility_type, "CORPORATE")
    if fallback in CCF_TABLE:
        return CCF_TABLE[fallback]

    return 1.00


def get_maturity_adjustment(pd: float, maturity: float) -> float:
    """
    Basel III Art. 153(1) / Art. 162 full maturity adjustment.

    b(PD) = (0.11852 - 0.05478 * ln(PD))^2
    MA    = (1 + (M - 2.5) * b) / (1 - 1.5 * b)

    Effective maturity M is clamped to [1, 5] per Art. 162.
    PD is floored at 0.0003 (3 bps) to avoid log(0) and ensure
    the formula remains well-defined.

    Args:
        pd: Probability of default (0-1). Floored at 0.0003.
        maturity: Remaining maturity in years.

    Returns:
        Maturity adjustment factor (>= 0).
    """
    # Floor PD to avoid log(0) and extreme b values
    pd_safe = max(pd, 0.0003)

    # Clamp effective maturity to [1, 5]
    m_eff = max(MATURITY_CAPS["min"], min(maturity, MATURITY_CAPS["max"]))

    # b(PD) per Basel III Art. 153(1)
    b = (0.11852 - 0.05478 * math.log(pd_safe)) ** 2

    # Guard against division by zero (1 - 1.5 * b could be zero for very
    # low PDs, but b is always small enough in practice)
    denominator = 1.0 - 1.5 * b
    if abs(denominator) < 1e-12:
        denominator = 1e-12

    ma = (1.0 + (m_eff - 2.5) * b) / denominator

    return max(round(ma, 6), 0.0)


# ---------------------------------------------------------------------------
# MAIN CALCULATOR CLASS
# ---------------------------------------------------------------------------


class EADCalculator:
    """
    Exposure at Default calculator with Basel III/IV Credit Conversion Factors.

    Computes regulatory EAD for on- and off-balance-sheet exposures with:
      1. CCF lookup by facility type x asset class x maturity
      2. Effective maturity adjustment per Basel III Art. 162 (simplified or
         full PD-based b(PD) formula)
      3. SA-CCR simplified add-on for OTC derivatives (alpha = 1.4)
      4. Climate stress drawdown overlay (EBA GL/2022/16)
      5. Guarantee and letter of credit exposure conversion

    Integration: EAD output feeds directly into ECL engine (ECL = PD x LGD x EAD).
    """

    def __init__(self, climate_scenario: str = "base"):
        """
        Initialize EAD calculator.

        Args:
            climate_scenario: One of 'optimistic', 'base', 'adverse', 'severe'
                              Controls climate drawdown stress multiplier.
        """
        self.climate_scenario = climate_scenario.lower()

        # Climate scenario multipliers for drawdown stress
        self._scenario_multipliers = {
            "optimistic": 0.5,
            "base": 1.0,
            "adverse": 1.5,
            "severe": 2.0,
        }

    # -------------------------------------------------------------------
    # PUBLIC API
    # -------------------------------------------------------------------

    def calculate(
        self,
        outstanding_balance: float = 0.0,
        total_commitment: float = 0.0,
        facility_type: str = "TERM_LOAN",
        asset_class: str = "CORPORATE",
        remaining_maturity_years: float = 2.5,
        sector: str = "Corporate",
        is_short_maturity: bool = False,
        derivative_notional: float = 0.0,
        derivative_asset_class: str = "interest_rate",
        derivative_maturity_years: float = 0.0,
        guarantee_amount: float = 0.0,
        apply_climate_stress: bool = True,
        pd: float = 0.01,
        use_pd_maturity_adjustment: bool = False,
    ) -> EADResult:
        """
        Calculate EAD for a single exposure.

        When *use_pd_maturity_adjustment* is True the full Basel III
        b(PD) maturity adjustment formula is applied:
            b  = (0.11852 - 0.05478 * ln(PD))^2
            MA = (1 + (M-2.5)*b) / (1 - 1.5*b)

        Otherwise a simplified linear scaling is used (backward-compatible).

        Args:
            outstanding_balance: Current drawn/outstanding amount
            total_commitment: Total committed facility amount (drawn + undrawn)
            facility_type: FacilityType enum value string
            asset_class: AssetClassEAD enum value string
            remaining_maturity_years: Remaining maturity in years
            sector: Industry sector for climate stress lookup
            is_short_maturity: True if original maturity < 1 year
            derivative_notional: Notional amount for OTC derivatives
            derivative_asset_class: SA-CCR asset class for derivatives
            derivative_maturity_years: Remaining maturity of derivative
            guarantee_amount: Amount of guarantee/LC issued
            apply_climate_stress: Whether to apply climate drawdown stress
            pd: Probability of default (used when use_pd_maturity_adjustment=True)
            use_pd_maturity_adjustment: Use full Basel III b(PD) formula

        Returns:
            EADResult with full breakdown and audit trail
        """
        notes: List[str] = []

        # --- 1. Determine undrawn amount ---
        undrawn_amount = max(total_commitment - outstanding_balance, 0.0)
        notes.append(
            f"Undrawn amount: {total_commitment:,.2f} - {outstanding_balance:,.2f} "
            f"= {undrawn_amount:,.2f}"
        )

        # --- 2. Look up CCF ---
        ccf = self._get_ccf(facility_type, asset_class, is_short_maturity)
        notes.append(
            f"CCF lookup: facility={facility_type}, asset_class={asset_class}, "
            f"short_maturity={is_short_maturity} -> CCF={ccf:.2%}"
        )

        # --- 3. Calculate off-balance-sheet EAD from undrawn commitments ---
        undrawn_commitment_ead = undrawn_amount * ccf
        notes.append(f"Undrawn EAD: {undrawn_amount:,.2f} * {ccf:.2%} = {undrawn_commitment_ead:,.2f}")

        # --- 4. Guarantee / LC exposure ---
        guarantee_ccf = self._get_guarantee_ccf(facility_type, asset_class)
        guarantee_exposure = guarantee_amount * guarantee_ccf
        if guarantee_amount > 0:
            notes.append(
                f"Guarantee exposure: {guarantee_amount:,.2f} * {guarantee_ccf:.2%} "
                f"= {guarantee_exposure:,.2f}"
            )

        # --- 5. OTC Derivative add-on (SA-CCR simplified) ---
        derivative_addon = 0.0
        if derivative_notional > 0:
            derivative_addon = self._calculate_saccr_addon(
                derivative_notional,
                derivative_asset_class,
                derivative_maturity_years,
            )
            notes.append(
                f"SA-CCR derivative add-on: notional={derivative_notional:,.2f}, "
                f"class={derivative_asset_class} -> add-on={derivative_addon:,.2f}"
            )

        # --- 6. Effective maturity adjustment ---
        if use_pd_maturity_adjustment:
            maturity_adj = self._calculate_pd_maturity_adjustment(
                remaining_maturity_years, asset_class, pd
            )
            notes.append(
                f"Maturity adjustment (PD-based): M={remaining_maturity_years:.1f}y, "
                f"PD={pd:.4f} -> factor={maturity_adj:.6f}"
            )
        else:
            maturity_adj = self._calculate_maturity_adjustment(
                remaining_maturity_years, asset_class
            )
            notes.append(
                f"Maturity adjustment (simplified): M={remaining_maturity_years:.1f}y "
                f"-> factor={maturity_adj:.4f}"
            )

        # --- 7. Pre-climate EAD ---
        ead_pre_climate = (
            outstanding_balance
            + undrawn_commitment_ead
            + guarantee_exposure
            + derivative_addon
        )
        notes.append(f"EAD pre-climate: {ead_pre_climate:,.2f}")

        # --- 8. Climate drawdown stress ---
        climate_stress_pct = 0.0
        climate_ead_uplift = 0.0
        if apply_climate_stress and undrawn_amount > 0:
            climate_stress_pct = self._get_climate_drawdown_stress(sector)
            climate_ead_uplift = undrawn_amount * climate_stress_pct
            notes.append(
                f"Climate drawdown stress: sector={sector}, scenario={self.climate_scenario}, "
                f"stress={climate_stress_pct:.2%} -> uplift={climate_ead_uplift:,.2f}"
            )

        # --- 9. Post-climate EAD ---
        ead_post_climate = ead_pre_climate + climate_ead_uplift
        notes.append(f"EAD post-climate: {ead_post_climate:,.2f}")

        # --- 10. Final regulatory EAD with maturity adjustment ---
        regulatory_ead = max(ead_post_climate * maturity_adj, 0.0)
        notes.append(
            f"Regulatory EAD (with maturity adj): {ead_post_climate:,.2f} * "
            f"{maturity_adj:.4f} = {regulatory_ead:,.2f}"
        )

        return EADResult(
            facility_type=facility_type,
            asset_class=asset_class,
            outstanding_balance=outstanding_balance,
            total_commitment=total_commitment,
            undrawn_amount=undrawn_amount,
            ccf_applied=ccf,
            effective_maturity_years=remaining_maturity_years,
            maturity_adjustment_factor=maturity_adj,
            ead_pre_climate=round(ead_pre_climate, 2),
            ead_post_climate=round(ead_post_climate, 2),
            climate_drawdown_stress_pct=climate_stress_pct,
            contribution_breakdown=EADContribution(
                on_balance_sheet=outstanding_balance,
                undrawn_commitment_ead=round(undrawn_commitment_ead, 2),
                guarantee_exposure=round(guarantee_exposure, 2),
                derivative_addon=round(derivative_addon, 2),
                maturity_adjustment=round(maturity_adj, 4),
                climate_ead_uplift=round(climate_ead_uplift, 2),
                total_ead=round(regulatory_ead, 2),
            ),
            regulatory_ead=round(regulatory_ead, 2),
            methodology_notes=notes,
        )

    def calculate_from_input(self, inp: EADInput) -> EADResult:
        """
        Calculate EAD from a typed EADInput dataclass.

        Convenience wrapper that unpacks the dataclass fields into
        keyword arguments for :meth:`calculate`.
        """
        return self.calculate(
            outstanding_balance=inp.outstanding_balance,
            total_commitment=inp.total_commitment,
            facility_type=inp.facility_type,
            asset_class=inp.asset_class,
            remaining_maturity_years=inp.remaining_maturity_years,
            sector=inp.sector,
            is_short_maturity=inp.is_short_maturity,
            derivative_notional=inp.derivative_notional,
            derivative_asset_class=inp.derivative_asset_class,
            derivative_maturity_years=inp.derivative_maturity_years,
            guarantee_amount=inp.guarantee_amount,
            apply_climate_stress=inp.apply_climate_stress,
            pd=inp.pd,
            use_pd_maturity_adjustment=inp.use_pd_maturity_adjustment,
        )

    def calculate_batch(
        self,
        exposures: List[Dict[str, Any]],
        apply_climate_stress: bool = True,
    ) -> EADBatchResult:
        """
        Batch EAD calculation for a loan book.

        Args:
            exposures: List of dicts with keys matching calculate() parameters.
                Required keys: outstanding_balance, total_commitment, facility_type, asset_class
            apply_climate_stress: Whether to apply climate drawdown overlay

        Returns:
            EADBatchResult with aggregated stats and individual results
        """
        results: List[EADResult] = []
        total_ead = 0.0
        total_on_balance = 0.0
        total_off_balance_ead = 0.0
        weighted_ccf_num = 0.0
        weighted_ccf_den = 0.0
        by_asset_class: Dict[str, float] = {}
        by_facility_type: Dict[str, float] = {}

        for exp in exposures:
            result = self.calculate(
                outstanding_balance=exp.get("outstanding_balance", 0.0),
                total_commitment=exp.get("total_commitment", 0.0),
                facility_type=exp.get("facility_type", "TERM_LOAN"),
                asset_class=exp.get("asset_class", "CORPORATE"),
                remaining_maturity_years=exp.get("remaining_maturity_years", 2.5),
                sector=exp.get("sector", "Corporate"),
                is_short_maturity=exp.get("is_short_maturity", False),
                derivative_notional=exp.get("derivative_notional", 0.0),
                derivative_asset_class=exp.get("derivative_asset_class", "interest_rate"),
                derivative_maturity_years=exp.get("derivative_maturity_years", 0.0),
                guarantee_amount=exp.get("guarantee_amount", 0.0),
                apply_climate_stress=apply_climate_stress,
                pd=exp.get("pd", 0.01),
                use_pd_maturity_adjustment=exp.get("use_pd_maturity_adjustment", False),
            )
            results.append(result)

            reg_ead = result.regulatory_ead
            total_ead += reg_ead
            total_on_balance += result.outstanding_balance
            off_bal = reg_ead - result.outstanding_balance * result.maturity_adjustment_factor
            total_off_balance_ead += max(off_bal, 0.0)

            # Weighted CCF
            undrawn = result.undrawn_amount
            if undrawn > 0:
                weighted_ccf_num += result.ccf_applied * undrawn
                weighted_ccf_den += undrawn

            # Aggregation by asset class
            ac = result.asset_class
            by_asset_class[ac] = by_asset_class.get(ac, 0.0) + reg_ead

            # Aggregation by facility type
            ft = result.facility_type
            by_facility_type[ft] = by_facility_type.get(ft, 0.0) + reg_ead

        weighted_avg_ccf = (
            weighted_ccf_num / weighted_ccf_den if weighted_ccf_den > 0 else 0.0
        )

        return EADBatchResult(
            total_ead=round(total_ead, 2),
            total_on_balance=round(total_on_balance, 2),
            total_off_balance_ead=round(total_off_balance_ead, 2),
            weighted_avg_ccf=round(weighted_avg_ccf, 4),
            count=len(results),
            by_asset_class={k: round(v, 2) for k, v in by_asset_class.items()},
            by_facility_type={k: round(v, 2) for k, v in by_facility_type.items()},
            results=results,
        )

    def calculate_batch_from_inputs(
        self,
        inputs: List[EADInput],
    ) -> EADBatchResult:
        """
        Batch EAD calculation from a list of EADInput dataclasses.

        Converts EADInput list to dict list and delegates to calculate_batch.
        """
        exposures = []
        for inp in inputs:
            exposures.append({
                "outstanding_balance": inp.outstanding_balance,
                "total_commitment": inp.total_commitment,
                "facility_type": inp.facility_type,
                "asset_class": inp.asset_class,
                "remaining_maturity_years": inp.remaining_maturity_years,
                "sector": inp.sector,
                "is_short_maturity": inp.is_short_maturity,
                "derivative_notional": inp.derivative_notional,
                "derivative_asset_class": inp.derivative_asset_class,
                "derivative_maturity_years": inp.derivative_maturity_years,
                "guarantee_amount": inp.guarantee_amount,
                "pd": inp.pd,
                "use_pd_maturity_adjustment": inp.use_pd_maturity_adjustment,
            })
        return self.calculate_batch(
            exposures=exposures,
            apply_climate_stress=inputs[0].apply_climate_stress if inputs else True,
        )

    # -----------------------------------------------------------------------
    # INTERNAL METHODS
    # -----------------------------------------------------------------------

    def _get_ccf(
        self, facility_type: str, asset_class: str, is_short_maturity: bool
    ) -> float:
        """
        Look up CCF from the regulatory table.

        Falls back to:
          1. Short maturity override if applicable
          2. Exact (facility_type, asset_class) match
          3. Facility type default (CORPORATE asset class)
          4. 100% (conservative fallback)
        """
        # Short maturity override for certain facility types
        if is_short_maturity and facility_type in SHORT_MATURITY_CCF_OVERRIDES:
            return SHORT_MATURITY_CCF_OVERRIDES[facility_type]

        # Exact lookup
        key = (facility_type, asset_class)
        if key in CCF_TABLE:
            return CCF_TABLE[key]

        # Fallback to CORPORATE for the facility type
        fallback_key = (facility_type, "CORPORATE")
        if fallback_key in CCF_TABLE:
            logger.warning(
                "CCF: no exact match for (%s, %s), using CORPORATE default",
                facility_type, asset_class,
            )
            return CCF_TABLE[fallback_key]

        # Conservative fallback
        logger.warning(
            "CCF: no match for facility_type=%s, using 100%% fallback",
            facility_type,
        )
        return 1.00

    def _get_guarantee_ccf(self, facility_type: str, asset_class: str) -> float:
        """Get CCF for guarantee/LC facilities."""
        if facility_type in (
            "GUARANTEE",
            "FINANCIAL_GUARANTEE",
            "STANDBY_LETTER_OF_CREDIT",
            "TRADE_LETTER_OF_CREDIT",
        ):
            key = (facility_type, asset_class)
            return CCF_TABLE.get(key, 0.75)
        return 0.0  # No guarantee component for other facility types

    def _calculate_saccr_addon(
        self,
        notional: float,
        derivative_asset_class: str,
        maturity_years: float,
    ) -> float:
        """
        Simplified SA-CCR add-on calculation.
        CRR Art. 274: EAD = alpha * (RC + PFE)
        Simplified: EAD = 1.4 * (MtM + add-on_factor * notional * maturity_factor)

        We use the simplified approach (no netting, no margin):
          Add-on = supervisory_factor * notional * maturity_factor
          Maturity factor = sqrt(min(M, 1) / 1) for M < 1; else sqrt(min(M,5)/5) * scaling
        """
        factor = SACCR_ADDON_FACTORS.get(derivative_asset_class, 0.01)

        # Maturity scaling: longer maturity = higher add-on (for IR/credit)
        if derivative_asset_class in ("interest_rate", "credit"):
            maturity_factor = math.sqrt(max(min(maturity_years, 5.0), 0.25))
        else:
            maturity_factor = 1.0

        # Alpha multiplier (SA-CCR: 1.4 per CRR Art. 274)
        addon = SACCR_ALPHA * factor * notional * maturity_factor
        return round(addon, 2)

    def _calculate_maturity_adjustment(
        self, remaining_maturity: float, asset_class: str
    ) -> float:
        """
        Simplified maturity adjustment (backward-compatible).
        At M=2.5 (benchmark), factor = 1.0
        Each year above 2.5 adds ~2.5%; each year below reduces by ~2.5%.
        Retail exposures: no maturity adjustment (Art. 162(1)).
        """
        # Retail exposures: no maturity adjustment
        if asset_class in ("RETAIL_REVOLVING", "RETAIL_MORTGAGE", "RETAIL_OTHER"):
            return 1.0

        # Clamp effective maturity to [1, 5]
        m_eff = max(MATURITY_CAPS["min"], min(remaining_maturity, MATURITY_CAPS["max"]))

        # Simplified maturity adjustment
        adjustment = 1.0 + (m_eff - MATURITY_CAPS["benchmark"]) * 0.025

        return round(max(adjustment, 0.85), 4)  # Floor at 0.85

    def _calculate_pd_maturity_adjustment(
        self, remaining_maturity: float, asset_class: str, pd: float
    ) -> float:
        """
        Full Basel III Art. 153(1) / Art. 162 maturity adjustment.

        b(PD)  = (0.11852 - 0.05478 * ln(PD))^2
        MA     = (1 + (M - 2.5) * b) / (1 - 1.5 * b)

        Retail exposures: no maturity adjustment per Art. 162(1).
        """
        if asset_class in ("RETAIL_REVOLVING", "RETAIL_MORTGAGE", "RETAIL_OTHER"):
            return 1.0

        return get_maturity_adjustment(pd, remaining_maturity)

    def _get_climate_drawdown_stress(self, sector: str) -> float:
        """
        Get climate-driven drawdown stress percentage.
        Under stress scenarios, corporates draw down committed lines faster.
        EBA GL/2022/16 Section 4.3: Climate as driver of credit deterioration.
        """
        base_stress = CLIMATE_DRAWDOWN_STRESS.get(sector, 0.05)

        # Scale by scenario severity
        scenario_mult = self._scenario_multipliers.get(self.climate_scenario, 1.0)

        return round(base_stress * scenario_mult, 4)

    # -----------------------------------------------------------------------
    # UTILITY / QUERY METHODS
    # -----------------------------------------------------------------------

    @staticmethod
    def get_ccf_table() -> Dict[str, Any]:
        """Return the full CCF lookup table for API consumption."""
        return dict(REGULATORY_CCF)

    @staticmethod
    def get_supported_facility_types() -> List[str]:
        """Return list of supported facility types."""
        return [ft.value for ft in FacilityType]

    @staticmethod
    def get_supported_asset_classes() -> List[str]:
        """Return list of supported asset classes."""
        return [ac.value for ac in AssetClassEAD]

    @staticmethod
    def get_climate_stress_factors() -> Dict[str, float]:
        """Return climate drawdown stress factors by sector."""
        return dict(CLIMATE_DRAWDOWN_STRESS)

    def get_scenario_info(self) -> Dict[str, Any]:
        """Return current scenario configuration."""
        return {
            "climate_scenario": self.climate_scenario,
            "scenario_multiplier": self._scenario_multipliers.get(
                self.climate_scenario, 1.0
            ),
            "available_scenarios": list(self._scenario_multipliers.keys()),
        }
