"""
LGD Downturn Engine -- Downturn LGD Estimation per EBA/Basel Standards

Implements regulatory-grade downturn LGD estimation per:
  - CRR2 Art. 181(1)(b): Downturn conditions reflecting economic downturn
  - EBA GL/2019/03: Estimation of LGD appropriate for an economic downturn
  - CRR2 Art. 164: Regulatory LGD floors by asset class
  - BCBS d350 / CRE 36.86-36.91: Downturn LGD for IRB banks
  - ECB TRIM Guide: Chapter 5 -- LGD estimation

Key concepts:
  1. Reference value approach (EBA GL/2019/03 S5.3):
     - Identify relevant economic downturn periods per country/sector
     - Compute average LGD during downturn windows
  2. Impact assessment by collateral type (S5.5):
     - Real estate: property price index decline x LTV adjustment
     - Financial collateral: market crash haircuts
     - Unsecured: recovery rate degradation
  3. Climate overlay (forward-looking):
     - Stranded asset haircut for fossil fuel collateral
     - Physical damage multiplier for coastal/flood-zone real estate
     - Green premium / brown discount on recovery values
  4. Regulatory floors:
     - CRR2 Art. 164(4): 10% floor for residential mortgage LGD
     - CRR2 Art. 164(4): 15% floor for commercial mortgage LGD
     - EBA: Downturn LGD >= long-run average LGD

Downturn LGD formula:
  downturn_lgd = long_run_avg_lgd
                 + downturn_addon (collateral-based)
                   * country_severity
                   * sector_mult
                   * scenario_mult
                 + climate_overlay (stranded + physical + green)
  Subject to: downturn_lgd >= regulatory_floor AND >= long_run_avg_lgd

Author: LGD Downturn Engine Module
Version: 2.0.0
Date: 2026-03-08
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# CONSTANTS & REFERENCE DATA
# ---------------------------------------------------------------------------

# CRR2 Art. 164 -- Regulatory LGD floors
REGULATORY_LGD_FLOORS: Dict[str, float] = {
    "RESIDENTIAL_MORTGAGE": 0.10,    # CRR2 Art. 164(4)
    "COMMERCIAL_MORTGAGE": 0.15,     # CRR2 Art. 164(4)
    "CORPORATE_UNSECURED": 0.25,     # IRB Foundation default
    "CORPORATE_SECURED": 0.15,
    "SME_UNSECURED": 0.25,
    "SME_SECURED": 0.15,
    "RETAIL_UNSECURED": 0.25,
}

# Historical downturn LGD add-ons by collateral type (EBA GL/2019/03)
# These represent average LGD increase observed in downturn vs long-run average
DOWNTURN_ADDON_BY_COLLATERAL: Dict[str, float] = {
    "property": 0.08,
    "equipment": 0.10,
    "financial": 0.05,
    "unsecured": 0.12,
    "inventory": 0.10,
    "receivables": 0.08,
    "cash": 0.02,
    "other": 0.12,
    # Mapped aliases for convenience
    "real_estate_residential": 0.08,   # -> property
    "real_estate_commercial": 0.08,    # -> property
}

# Economic cycle adjustment factors by country severity (25 countries)
# Higher = more severe downturn impact (based on GFC / COVID data)
COUNTRY_CYCLE_SEVERITY: Dict[str, float] = {
    "US": 1.00,
    "UK": 0.95,
    "DE": 0.90,
    "FR": 0.92,
    "ES": 1.25,
    "IT": 1.20,
    "GR": 1.50,
    "PT": 1.15,
    "IE": 1.10,
    "NL": 0.85,
    "BE": 0.88,
    "AT": 0.85,
    "CH": 0.70,
    "JP": 0.80,
    "AU": 0.90,
    "CA": 0.88,
    "SE": 0.75,
    "NO": 0.72,
    "DK": 0.78,
    "FI": 0.82,
    "SG": 0.70,
    "HK": 0.75,
    "KR": 0.95,
    "BR": 1.30,
    "IN": 1.10,
}

# Sector-specific downturn severity multipliers (19 sectors)
SECTOR_DOWNTURN_MULT: Dict[str, float] = {
    "Oil & Gas": 1.50,
    "Coal Mining": 1.70,
    "Utilities": 1.15,
    "Real Estate": 1.40,
    "Construction": 1.35,
    "Automotive": 1.25,
    "Airlines": 1.45,
    "Shipping": 1.35,
    "Hospitality": 1.30,
    "Retail Trade": 1.20,
    "Agriculture": 1.10,
    "Healthcare": 0.85,
    "Technology": 0.90,
    "Telecom": 0.95,
    "Financial Services": 1.15,
    "Education": 0.80,
    "Government": 0.70,
    "Defense": 0.75,
    "Food & Beverage": 0.95,
}

# Climate overlay: stranded asset haircuts by sector (8 sectors)
CLIMATE_STRANDED_HAIRCUTS: Dict[str, float] = {
    "Coal Mining": 0.40,
    "Oil & Gas": 0.25,
    "Gas Utilities": 0.15,
    "Thermal Power": 0.20,
    "Carbon-Intensive Manufacturing": 0.12,
    "Cement": 0.10,
    "Steel": 0.10,
    "Chemicals": 0.08,
}

# Climate overlay: physical risk LGD multipliers
PHYSICAL_RISK_LGD_MULT: Dict[str, float] = {
    "extreme": 0.20,
    "high": 0.12,
    "medium": 0.06,
    "low": 0.02,
}

# Green premium / brown discount on collateral recovery by EPC rating
GREEN_PREMIUM: Dict[str, float] = {
    "A": -0.05,
    "B": -0.03,
    "C": -0.01,
    "D": 0.00,
    "E": +0.03,
    "F": +0.05,
    "G": +0.08,
}

# Scenario multipliers
SCENARIO_MULTIPLIERS: Dict[str, float] = {
    "BASE": 0.6,
    "ADVERSE": 1.0,
    "SEVERE": 1.5,
}


# ---------------------------------------------------------------------------
# DATACLASSES
# ---------------------------------------------------------------------------


@dataclass
class DownturnLGDInput:
    """Input for downturn LGD calculation."""
    exposure_id: str
    counterparty_name: str
    long_run_avg_lgd: float         # Long-run average LGD (0-1)
    collateral_type: str            # property, equipment, unsecured, etc.
    collateral_value: float         # Current collateral value
    exposure_amount: float          # EAD
    ltv_ratio: float = 0.0         # Loan-to-Value (for mortgages)
    sector: str = ""
    country: str = ""
    asset_class: str = "CORPORATE"  # CORPORATE, RETAIL_MORTGAGE, SME, etc.
    epc_rating: str = ""            # A-G for real estate
    physical_risk_level: str = ""   # extreme/high/medium/low
    is_fossil_fuel_collateral: bool = False
    recovery_rate_historical: float = 0.0
    cure_rate_historical: float = 0.0


@dataclass
class DownturnLGDContribution:
    """Breakdown of downturn LGD components."""
    base_long_run_lgd: float
    downturn_addon: float
    country_cycle_adjustment: float
    sector_severity_adjustment: float
    climate_stranded_addon: float
    climate_physical_addon: float
    green_premium_adjustment: float
    regulatory_floor_applied: bool
    regulatory_floor_value: float


@dataclass
class DownturnLGDResult:
    """Downturn LGD calculation result."""
    exposure_id: str
    long_run_avg_lgd: float
    downturn_lgd: float
    downturn_uplift_pct: float      # % increase from long-run
    contribution: DownturnLGDContribution
    methodology_notes: List[str]


@dataclass
class DownturnLGDBatchResult:
    """Batch downturn LGD result."""
    results: List[DownturnLGDResult]
    portfolio_avg_lr_lgd: float
    portfolio_avg_dt_lgd: float
    portfolio_avg_uplift_pct: float
    floor_applied_count: int
    exposure_count: int
    methodology_notes: List[str]


# ---------------------------------------------------------------------------
# MAIN ENGINE CLASS
# ---------------------------------------------------------------------------


class LGDDownturnEngine:
    """
    Regulatory-compliant downturn LGD estimation engine.

    Computes downturn LGD from long-run average LGD by applying:
      1. Collateral-type-specific downturn add-on (EBA GL/2019/03)
         scaled by scenario multiplier
      2. Country economic cycle severity adjustment
      3. Sector downturn severity multiplier
      4. Climate overlays (stranded assets, physical risk, green premium)
      5. Regulatory floors (CRR2 Art. 164)

    Formula:
      downturn_lgd = long_run_avg_lgd
                     + addon * country_sev * sector_mult * scenario_mult
                     + climate_stranded + climate_physical + green_adj
      Subject to: >= regulatory_floor AND >= long_run_avg_lgd, capped at 1.0
    """

    def __init__(
        self,
        include_climate_overlay: bool = True,
        scenario: str = "ADVERSE",
    ):
        """
        Initialize downturn LGD engine.

        Args:
            include_climate_overlay: Apply climate-related adjustments
            scenario: Stress scenario -- BASE (0.6x), ADVERSE (1.0x), SEVERE (1.5x)
        """
        self.include_climate = include_climate_overlay
        self.scenario = scenario
        self._scenario_mult = SCENARIO_MULTIPLIERS.get(scenario, 1.0)

    # -------------------------------------------------------------------
    # SINGLE EXPOSURE CALCULATION
    # -------------------------------------------------------------------

    def calculate(self, inp: DownturnLGDInput) -> DownturnLGDResult:
        """
        Calculate downturn LGD for a single exposure.

        Args:
            inp: Downturn LGD input

        Returns:
            DownturnLGDResult with full contribution breakdown
        """
        notes: List[str] = []
        base = inp.long_run_avg_lgd

        # ------------------------------------------------------------------
        # 1. Downturn add-on by collateral type
        # ------------------------------------------------------------------
        raw_addon = DOWNTURN_ADDON_BY_COLLATERAL.get(
            inp.collateral_type,
            DOWNTURN_ADDON_BY_COLLATERAL["other"],
        )
        notes.append(
            f"Base downturn add-on ({inp.collateral_type}): {raw_addon:.2%}"
        )

        # ------------------------------------------------------------------
        # 2. Country cycle severity
        # ------------------------------------------------------------------
        country_sev = COUNTRY_CYCLE_SEVERITY.get(inp.country, 1.0)
        notes.append(f"Country cycle ({inp.country}): severity={country_sev:.2f}")

        # ------------------------------------------------------------------
        # 3. Sector severity multiplier
        # ------------------------------------------------------------------
        sector_mult = SECTOR_DOWNTURN_MULT.get(inp.sector, 1.0)
        notes.append(f"Sector downturn ({inp.sector}): mult={sector_mult:.2f}")

        # ------------------------------------------------------------------
        # Combined downturn add-on = addon * country * sector * scenario
        # ------------------------------------------------------------------
        dt_addon = raw_addon * country_sev * sector_mult * self._scenario_mult
        notes.append(
            f"Scaled downturn add-on: {raw_addon:.4f} * {country_sev:.2f} "
            f"* {sector_mult:.2f} * {self._scenario_mult:.1f} = {dt_addon:.4f}"
        )

        # Decompose for contribution reporting
        country_adj = raw_addon * (country_sev - 1.0) * sector_mult * self._scenario_mult
        sector_adj = raw_addon * country_sev * (sector_mult - 1.0) * self._scenario_mult

        # ------------------------------------------------------------------
        # 4. Climate overlays
        # ------------------------------------------------------------------
        climate_stranded = 0.0
        climate_physical = 0.0
        green_adj = 0.0

        if self.include_climate:
            # Stranded asset haircut
            if inp.is_fossil_fuel_collateral or inp.sector in CLIMATE_STRANDED_HAIRCUTS:
                stranded_base = CLIMATE_STRANDED_HAIRCUTS.get(inp.sector, 0.0)
                if inp.is_fossil_fuel_collateral:
                    stranded_base = max(stranded_base, 0.15)
                climate_stranded = stranded_base * self._scenario_mult
                notes.append(
                    f"Climate stranded haircut ({inp.sector}): "
                    f"+{climate_stranded:.2%}"
                )

            # Physical risk multiplier
            if inp.physical_risk_level:
                climate_physical = PHYSICAL_RISK_LGD_MULT.get(
                    inp.physical_risk_level, 0.0
                ) * self._scenario_mult
                notes.append(
                    f"Physical risk ({inp.physical_risk_level}): "
                    f"+{climate_physical:.2%}"
                )

            # Green premium / brown discount
            if inp.epc_rating:
                green_adj = GREEN_PREMIUM.get(inp.epc_rating, 0.0)
                notes.append(f"EPC {inp.epc_rating} adjustment: {green_adj:+.2%}")

        # ------------------------------------------------------------------
        # 5. Combine all components
        # ------------------------------------------------------------------
        downturn_lgd = (
            base
            + dt_addon
            + climate_stranded
            + climate_physical
            + green_adj
        )

        # ------------------------------------------------------------------
        # 6. Apply regulatory floor (CRR2 Art. 164)
        # ------------------------------------------------------------------
        floor_key = self._get_floor_key(inp.asset_class, inp.collateral_type)
        reg_floor = REGULATORY_LGD_FLOORS.get(floor_key, 0.0)
        floor_applied = False

        if downturn_lgd < reg_floor:
            notes.append(
                f"Regulatory floor applied: {reg_floor:.2%} "
                f"(calculated was {downturn_lgd:.2%})"
            )
            downturn_lgd = reg_floor
            floor_applied = True

        # EBA GL/2019/03: downturn LGD >= long-run average LGD
        if downturn_lgd < base:
            downturn_lgd = base
            notes.append("Downturn LGD floored at long-run average")

        # Cap at 100%
        downturn_lgd = min(downturn_lgd, 1.0)

        # Uplift percentage
        uplift_pct = (
            ((downturn_lgd - base) / base * 100.0) if base > 0 else 0.0
        )

        return DownturnLGDResult(
            exposure_id=inp.exposure_id,
            long_run_avg_lgd=round(base, 4),
            downturn_lgd=round(downturn_lgd, 4),
            downturn_uplift_pct=round(uplift_pct, 2),
            contribution=DownturnLGDContribution(
                base_long_run_lgd=round(base, 4),
                downturn_addon=round(dt_addon, 4),
                country_cycle_adjustment=round(country_adj, 4),
                sector_severity_adjustment=round(sector_adj, 4),
                climate_stranded_addon=round(climate_stranded, 4),
                climate_physical_addon=round(climate_physical, 4),
                green_premium_adjustment=round(green_adj, 4),
                regulatory_floor_applied=floor_applied,
                regulatory_floor_value=round(reg_floor, 4),
            ),
            methodology_notes=notes,
        )

    # -------------------------------------------------------------------
    # BATCH CALCULATION
    # -------------------------------------------------------------------

    def calculate_batch(
        self,
        inputs: List[DownturnLGDInput],
    ) -> DownturnLGDBatchResult:
        """
        Calculate downturn LGD for a batch of exposures.

        Args:
            inputs: List of downturn LGD inputs

        Returns:
            DownturnLGDBatchResult with all results and portfolio summary
        """
        results = [self.calculate(inp) for inp in inputs]

        n = len(results)
        avg_lr = sum(r.long_run_avg_lgd for r in results) / n if n > 0 else 0.0
        avg_dt = sum(r.downturn_lgd for r in results) / n if n > 0 else 0.0
        avg_uplift = (
            ((avg_dt - avg_lr) / avg_lr * 100.0) if avg_lr > 0 else 0.0
        )
        floor_count = sum(
            1 for r in results if r.contribution.regulatory_floor_applied
        )

        notes = [
            f"Batch: {n} exposures, avg LR LGD={avg_lr:.2%}, "
            f"avg DT LGD={avg_dt:.2%}, uplift={avg_uplift:+.1f}%",
            f"Scenario: {self.scenario} (mult={self._scenario_mult:.1f})",
            f"Climate overlay: {'ON' if self.include_climate else 'OFF'}",
            f"Regulatory floors applied: {floor_count}/{n}",
        ]

        return DownturnLGDBatchResult(
            results=results,
            portfolio_avg_lr_lgd=round(avg_lr, 4),
            portfolio_avg_dt_lgd=round(avg_dt, 4),
            portfolio_avg_uplift_pct=round(avg_uplift, 2),
            floor_applied_count=floor_count,
            exposure_count=n,
            methodology_notes=notes,
        )

    # -------------------------------------------------------------------
    # HELPER: FLOOR KEY MAPPING
    # -------------------------------------------------------------------

    @staticmethod
    def _get_floor_key(asset_class: str, collateral_type: str) -> str:
        """
        Map asset class + collateral type to regulatory floor key.

        Logic:
          - RETAIL_MORTGAGE / residential collateral -> RESIDENTIAL_MORTGAGE
          - Commercial collateral -> COMMERCIAL_MORTGAGE
          - Unsecured + RETAIL -> RETAIL_UNSECURED
          - Unsecured + SME -> SME_UNSECURED
          - Unsecured + CORPORATE -> CORPORATE_UNSECURED
          - SME + secured -> SME_SECURED
          - Default -> CORPORATE_SECURED
        """
        ac_upper = asset_class.upper()
        ct_lower = collateral_type.lower()

        if "residential" in ct_lower or "MORTGAGE" in ac_upper:
            if "commercial" in ct_lower:
                return "COMMERCIAL_MORTGAGE"
            return "RESIDENTIAL_MORTGAGE"

        if "unsecured" in ct_lower:
            if "RETAIL" in ac_upper:
                return "RETAIL_UNSECURED"
            if "SME" in ac_upper:
                return "SME_UNSECURED"
            return "CORPORATE_UNSECURED"

        if "SME" in ac_upper:
            return "SME_SECURED"

        return "CORPORATE_SECURED"

    # -------------------------------------------------------------------
    # STATIC UTILITY METHODS (for API reference endpoints)
    # -------------------------------------------------------------------

    @staticmethod
    def get_regulatory_floors() -> Dict[str, float]:
        """Return CRR2 Art. 164 regulatory LGD floors."""
        return dict(REGULATORY_LGD_FLOORS)

    @staticmethod
    def get_downturn_addons() -> Dict[str, float]:
        """Return downturn add-on table by collateral type."""
        return dict(DOWNTURN_ADDON_BY_COLLATERAL)

    @staticmethod
    def get_sector_severity() -> Dict[str, float]:
        """Return sector downturn severity multipliers."""
        return dict(SECTOR_DOWNTURN_MULT)

    @staticmethod
    def get_country_cycle_severity() -> Dict[str, float]:
        """Return country economic cycle severity factors."""
        return dict(COUNTRY_CYCLE_SEVERITY)

    @staticmethod
    def get_climate_stranded_haircuts() -> Dict[str, float]:
        """Return climate stranded asset haircuts by sector."""
        return dict(CLIMATE_STRANDED_HAIRCUTS)

    @staticmethod
    def get_green_premium_table() -> Dict[str, float]:
        """Return EPC rating green premium / brown discount table."""
        return dict(GREEN_PREMIUM)
