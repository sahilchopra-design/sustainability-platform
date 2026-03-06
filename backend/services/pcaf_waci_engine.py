"""
PCAF Financed Emissions & WACI Engine
Partnership for Carbon Accounting Financials Standard v2.0

Implements the PCAF Global GHG Accounting and Reporting Standard for the Financial Industry,
covering financed emissions calculation, WACI (Weighted Average Carbon Intensity),
carbon footprint, temperature alignment scoring, and SFDR PAI indicator generation.

References:
  - PCAF Global GHG Accounting Standard v2.0 (2022)
  - GHG Protocol Corporate Standard (2015 update)
  - SFDR RTS Annex I PAI indicators (EU 2022/1288)
  - TCFD portfolio alignment metrics guidance (2021)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class PCAFAssetClass(str, Enum):
    """PCAF-defined asset classes with distinct attribution factor methodologies."""
    LISTED_EQUITY   = "listed_equity"
    CORPORATE_BONDS = "corporate_bonds"
    BUSINESS_LOANS  = "business_loans"
    COMMERCIAL_RE   = "commercial_real_estate"
    MORTGAGES       = "mortgages"
    VEHICLE_LOANS   = "vehicle_loans"
    PROJECT_FINANCE = "project_finance"
    SOVEREIGN_BONDS = "sovereign_bonds"
    UNLISTED_EQUITY = "unlisted_equity"
    INFRASTRUCTURE  = "infrastructure"


class DataQualityScore(int, Enum):
    """
    PCAF Data Quality Score (DQS). Lower is better.
    1 = Verified primary data (best); 5 = Estimated/proxy data (worst).
    """
    SCORE_1 = 1   # Verified primary activity data
    SCORE_2 = 2   # Unverified primary activity data
    SCORE_3 = 3   # Verified secondary data (e.g. audited financial reports)
    SCORE_4 = 4   # Sector averages / industry benchmarks
    SCORE_5 = 5   # Estimated / proxy data


class EmissionsBoundary(str, Enum):
    """GHG emissions boundary for financed emissions reporting."""
    SCOPE_1_2            = "scope_1_2"
    SCOPE_1_2_3          = "scope_1_2_3"
    SCOPE_1_2_3_FINANCED = "scope_1_2_3_financed"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class InvesteeData:
    """
    Holds all financial and emissions data for a single investee required
    for PCAF financed emissions calculation. All monetary values in EUR.
    """
    company_name:           str
    sector_gics:            str
    country_iso:            str
    asset_class:            PCAFAssetClass
    outstanding_amount_eur: Decimal     # Financial institution exposure
    enterprise_value_eur:   Decimal     # EVIC: Enterprise Value Including Cash
    total_equity_eur:       Decimal
    total_debt_eur:         Decimal
    annual_revenue_eur:     Decimal
    scope1_co2e_tonnes:     Decimal
    scope2_co2e_tonnes:     Decimal     # Market-based preferred per PCAF
    data_quality:           DataQualityScore
    reporting_year:         int
    isin:                   Optional[str] = None
    scope3_co2e_tonnes:     Decimal = field(default_factory=lambda: Decimal("0"))


@dataclass
class FinancedEmissionsResult:
    """
    Per-investee financed emissions result following PCAF Standard v2.0.
    
    The attribution factor is the fraction of investee emissions attributable
    to the institution outstanding position.
    """
    investee_name:           str
    asset_class:             PCAFAssetClass
    attribution_factor:      Decimal    # outstanding / EVIC (or equivalent)
    financed_scope1_co2e:    Decimal
    financed_scope2_co2e:    Decimal
    financed_scope3_co2e:    Decimal
    financed_total_co2e:     Decimal
    data_quality_score:      DataQualityScore
    waci_scope12_tco2e_meur: Decimal    # tCO2e per EUR million revenue (unweighted)


@dataclass
class PortfolioPCAFResult:
    """
    Aggregated portfolio-level PCAF financed emissions and WACI metrics.
    
    WACI = Sum_i [ (outstanding_i / total_aum) * (S1+S2)_i / revenue_meur_i ]
    Carbon footprint = total_financed_co2e / total_aum_meur
    """
    total_financed_scope1_co2e: Decimal
    total_financed_scope2_co2e: Decimal
    total_financed_scope3_co2e: Decimal
    total_financed_co2e:        Decimal
    portfolio_waci_scope12:     Decimal     # tCO2e / EUR M revenue (Scope 1+2)
    portfolio_waci_scope123:    Decimal     # tCO2e / EUR M revenue (Scope 1+2+3)
    portfolio_carbon_footprint: Decimal     # tCO2e / EUR M invested
    total_aum_eur:              Decimal
    covered_aum_eur:            Decimal
    coverage_pct:               Decimal
    weighted_data_quality:      Decimal     # Exposure-weighted average DQS
    temperature_score_c:        Decimal     # Portfolio implied temperature (simplified)
    investee_count:             int
    validation_summary:         Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# GDP Lookup Table (EUR, approx. 2023 values for sovereign attribution)
# ---------------------------------------------------------------------------

_SOVEREIGN_GDP_EUR: Dict[str, Decimal] = {
    "US": Decimal("22500000000000"),   # ~22.5 T EUR
    "CN": Decimal("16800000000000"),   # ~16.8 T EUR
    "DE": Decimal("3900000000000"),    # ~3.9 T EUR
    "GB": Decimal("2800000000000"),    # ~2.8 T EUR
    "FR": Decimal("2700000000000"),    # ~2.7 T EUR
    "JP": Decimal("4200000000000"),    # ~4.2 T EUR (JPY converted)
    "IN": Decimal("3100000000000"),    # ~3.1 T EUR
    "IT": Decimal("1950000000000"),    # ~1.95 T EUR
    "BR": Decimal("1800000000000"),    # ~1.8 T EUR
    "CA": Decimal("1750000000000"),    # ~1.75 T EUR
}

# Simplified piecewise-linear WACI -> implied temperature mapping.
# Calibrated against MSCI / SBTi ITR illustrative benchmarks (indicative).
_WACI_TEMPERATURE_MAPPING = [
    (Decimal("50"),   Decimal("1.5")),
    (Decimal("100"),  Decimal("1.7")),
    (Decimal("200"),  Decimal("1.9")),
    (Decimal("350"),  Decimal("2.2")),
    (Decimal("500"),  Decimal("2.5")),
    (Decimal("750"),  Decimal("2.9")),
    (Decimal("1000"), Decimal("3.2")),
    (Decimal("1500"), Decimal("3.7")),
    (Decimal("2000"), Decimal("4.0")),
]

# SFDR PAI 4: GICS sectors classified as fossil fuel sectors
_FOSSIL_FUEL_GICS_SECTORS = {
    "Energy",
    "Oil Gas & Consumable Fuels",
    "Coal & Consumable Fuels",
    "Oil Gas Exploration & Production",
    "Integrated Oil & Gas",
    "Refining & Marketing",
}


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class PCAFWACIEngine:
    """
    Implements the PCAF Global GHG Accounting and Reporting Standard v2.0
    for financed emissions, WACI, and portfolio carbon footprint.
    
    Supports all ten PCAF asset classes with respective attribution factor
    methodologies and produces audit-ready output aligned with SFDR PAI.
    """

    def _get_attribution_factor(self, investee: InvesteeData) -> Decimal:
        """
        Derive PCAF attribution factor for the financial institution.
        
        Methodology by asset class (PCAF Standard v2.0, Part A):
          Listed Equity / Corporate Bonds / Unlisted Equity:
              AF = outstanding_amount / EVIC
          Business Loans:
              AF = outstanding_amount / (total_equity + total_debt)
          Commercial RE / Mortgages:
              AF = outstanding_amount / property_value (total_equity proxy)
          Project Finance / Infrastructure:
              AF = outstanding_amount / total_project_cost (enterprise_value proxy)
          Vehicle Loans:
              AF = outstanding_amount / vehicle_value (enterprise_value proxy)
          Sovereign Bonds:
              AF = outstanding_amount / GDP_eur (from lookup table)
        
        Result is capped at 1.0 (cannot own > 100 pct of emissions).
        """
        outstanding = investee.outstanding_amount_eur
        ac = investee.asset_class
        
        try:
            if ac in (
                PCAFAssetClass.LISTED_EQUITY,
                PCAFAssetClass.CORPORATE_BONDS,
                PCAFAssetClass.UNLISTED_EQUITY,
            ):
                denom = investee.enterprise_value_eur
                if denom <= Decimal("0"):
                    logger.warning(
                        "Zero/negative EVIC for %s -- defaulting AF to 1.0",
                        investee.company_name,
                    )
                    return Decimal("1.0")
                af = outstanding / denom
        
            elif ac == PCAFAssetClass.BUSINESS_LOANS:
                denom = investee.total_equity_eur + investee.total_debt_eur
                if denom <= Decimal("0"):
                    logger.warning(
                        "Zero book value for %s -- defaulting AF to 1.0",
                        investee.company_name,
                    )
                    return Decimal("1.0")
                af = outstanding / denom
        
            elif ac in (PCAFAssetClass.COMMERCIAL_RE, PCAFAssetClass.MORTGAGES):
                prop_val = investee.total_equity_eur
                if prop_val <= Decimal("0"):
                    return Decimal("1.0")
                af = outstanding / prop_val
        
            elif ac in (PCAFAssetClass.PROJECT_FINANCE, PCAFAssetClass.INFRASTRUCTURE):
                proj_cost = investee.enterprise_value_eur
                if proj_cost <= Decimal("0"):
                    return Decimal("1.0")
                af = outstanding / proj_cost
        
            elif ac == PCAFAssetClass.VEHICLE_LOANS:
                vehicle_val = investee.enterprise_value_eur
                if vehicle_val <= Decimal("0"):
                    return Decimal("1.0")
                af = outstanding / vehicle_val
        
            elif ac == PCAFAssetClass.SOVEREIGN_BONDS:
                gdp = _SOVEREIGN_GDP_EUR.get(investee.country_iso.upper())
                if gdp is None or gdp <= Decimal("0"):
                    logger.info(
                        "No GDP lookup for country %s -- AF defaults to 1.0",
                        investee.country_iso,
                    )
                    return Decimal("1.0")
                af = outstanding / gdp
        
            else:
                logger.warning(
                    "Unknown asset class %s for %s -- AF defaults to 1.0",
                    ac, investee.company_name,
                )

        except (InvalidOperation, ZeroDivisionError) as exc:
            logger.error(
                "AF calculation failed for %s: %s", investee.company_name, exc
            )
            return Decimal("1.0")

        return min(af, Decimal("1.0")).quantize(
            Decimal("0.000001"), rounding=ROUND_HALF_UP
        )
        

    def _calculate_investee_financed_emissions(
        self, investee: InvesteeData
    ) -> FinancedEmissionsResult:
        """
        Calculate financed emissions for a single investee.
        
        financed_scopeX = attribution_factor * scopeX_co2e_tonnes
        
        WACI intensity (unweighted) = (Scope1 + Scope2) / revenue_meur
        Portfolio-level weighting applied in calculate_portfolio_financed_emissions.
        """
        af = self._get_attribution_factor(investee)
        
        fs1 = (af * investee.scope1_co2e_tonnes).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        fs2 = (af * investee.scope2_co2e_tonnes).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        fs3 = (af * investee.scope3_co2e_tonnes).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        total = fs1 + fs2 + fs3
        
        rev_meur = investee.annual_revenue_eur / Decimal("1000000")
        if rev_meur > Decimal("0"):
            intensity_s12 = (
                (investee.scope1_co2e_tonnes + investee.scope2_co2e_tonnes) / rev_meur
            ).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
        else:
            intensity_s12 = Decimal("0")
            logger.warning(
                "Zero revenue for %s -- WACI contribution set to 0",
                investee.company_name,
            )
        
        return FinancedEmissionsResult(
            investee_name=investee.company_name,
            asset_class=investee.asset_class,
            attribution_factor=af,
            financed_scope1_co2e=fs1,
            financed_scope2_co2e=fs2,
            financed_scope3_co2e=fs3,
            financed_total_co2e=total,
            data_quality_score=investee.data_quality,
            waci_scope12_tco2e_meur=intensity_s12,
        )

    def _interpolate_temperature(self, waci: Decimal) -> Decimal:
        """
        Map portfolio WACI to implied temperature via piecewise linear interpolation.
        
        Simplified proxy only. Full ITR scoring requires forward-looking company
        decarbonisation pathways (SBTi or MSCI ITR methodology).
        """
        mp = _WACI_TEMPERATURE_MAPPING
        if waci <= mp[0][0]:
            return mp[0][1]
        if waci >= mp[-1][0]:
            return mp[-1][1]
        for i in range(len(mp) - 1):
            w_lo, t_lo = mp[i]
            w_hi, t_hi = mp[i + 1]
            if w_lo <= waci <= w_hi:
                frac = (waci - w_lo) / (w_hi - w_lo)
                return (t_lo + frac * (t_hi - t_lo)).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
        return Decimal("4.0")

    def calculate_portfolio_financed_emissions(
        self, investees: List[InvesteeData]
    ) -> PortfolioPCAFResult:
        """
        Aggregate financed emissions across the full portfolio.
        
        Steps:
          1. Per-investee financed emissions via attribution factor.
          2. Aggregate Scope 1, 2, 3 financed totals.
          3. WACI (S1+S2)  = Sum_i [ w_i * (S1+S2)_i / rev_meur_i ]
             WACI (S1+2+S3) = Sum_i [ w_i * (S1+S2+S3)_i / rev_meur_i ]
             where w_i = outstanding_i / total_aum.
          4. Carbon footprint = total_financed_co2e / total_aum_meur.
          5. Temperature alignment via WACI interpolation.
          6. Exposure-weighted data quality score.
          7. Coverage = covered_aum / total_aum.
        """
        if not investees:
            logger.warning("No investees provided -- returning empty portfolio result.")
            z = Decimal("0")
            return PortfolioPCAFResult(
                total_financed_scope1_co2e=z,
                total_financed_scope2_co2e=z,
                total_financed_scope3_co2e=z,
                total_financed_co2e=z,
                portfolio_waci_scope12=z,
                portfolio_waci_scope123=z,
                portfolio_carbon_footprint=z,
                total_aum_eur=z,
                covered_aum_eur=z,
                coverage_pct=z,
                weighted_data_quality=z,
                temperature_score_c=z,
                investee_count=0,
                validation_summary={"error": "No investee data provided"},
            )
        
        results: List[FinancedEmissionsResult] = []
        for inv in investees:
            try:
                results.append(self._calculate_investee_financed_emissions(inv))
            except Exception as exc:
                logger.error(
                    "Financed emissions calculation failed for %s: %s",
                    inv.company_name, exc,
                )
        
        total_s1  = sum((r.financed_scope1_co2e for r in results), Decimal("0"))
        total_s2  = sum((r.financed_scope2_co2e for r in results), Decimal("0"))
        total_s3  = sum((r.financed_scope3_co2e for r in results), Decimal("0"))
        total_co2 = total_s1 + total_s2 + total_s3
        
        total_aum = sum((inv.outstanding_amount_eur for inv in investees), Decimal("0"))
        covered_aum = sum(
            (
                inv.outstanding_amount_eur
                for inv in investees
                if inv.scope1_co2e_tonnes + inv.scope2_co2e_tonnes > Decimal("0")
            ),
            Decimal("0"),
        )
        
        waci_s12  = Decimal("0")
        waci_s123 = Decimal("0")
        if total_aum > Decimal("0"):
            for inv in investees:
                weight   = inv.outstanding_amount_eur / total_aum
                rev_meur = inv.annual_revenue_eur / Decimal("1000000")
                if rev_meur > Decimal("0"):
                    i12  = (inv.scope1_co2e_tonnes + inv.scope2_co2e_tonnes) / rev_meur
                    i123 = i12 + inv.scope3_co2e_tonnes / rev_meur
                    waci_s12  += weight * i12
                    waci_s123 += weight * i123
        
        waci_s12  = waci_s12.quantize(Decimal("0.001"),  rounding=ROUND_HALF_UP)
        waci_s123 = waci_s123.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
        
        total_aum_meur = total_aum / Decimal("1000000")
        carbon_fp = (
            (total_co2 / total_aum_meur).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
            if total_aum_meur > Decimal("0")
            else Decimal("0")
        )
        
        temperature = self._interpolate_temperature(waci_s12)
        
        if total_aum > Decimal("0"):
            w_dqs = (
                sum(
                    (
                        inv.outstanding_amount_eur * Decimal(str(inv.data_quality.value))
                        for inv in investees
                    ),
                    Decimal("0"),
                )
                / total_aum
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            w_dqs = Decimal("5.0")
        
        cov_pct = (
            (covered_aum / total_aum * Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            if total_aum > Decimal("0")
            else Decimal("0")
        )
        
        pr = PortfolioPCAFResult(
            total_financed_scope1_co2e=total_s1.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            total_financed_scope2_co2e=total_s2.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            total_financed_scope3_co2e=total_s3.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            total_financed_co2e=total_co2.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            portfolio_waci_scope12=waci_s12,
            portfolio_waci_scope123=waci_s123,
            portfolio_carbon_footprint=carbon_fp,
            total_aum_eur=total_aum,
            covered_aum_eur=covered_aum,
            coverage_pct=cov_pct,
            weighted_data_quality=w_dqs,
            temperature_score_c=temperature,
            investee_count=len(investees),
        )
        pr.validation_summary = self.build_validation_summary(pr, investees)
        return pr

    def generate_pai_metrics(
        self, investees: List[InvesteeData]
    ) -> Dict[str, Any]:
        """
        Calculate SFDR PAI indicators overlapping with PCAF methodology.
        
        PAI 1:  Total GHG emissions -- absolute financed (tCO2e)
        PAI 2:  Portfolio carbon footprint (tCO2e / EUR M invested)
        PAI 3:  Weighted average GHG intensity -- WACI (tCO2e / EUR M revenue)
        PAI 4:  Exposure to fossil fuel sector companies (pct of AUM)
        PAI 5:  Non-renewable energy proxy (pct)
        PAI 14: Emissions to water (qualitative flag)
        
        Reference: SFDR RTS Annex I, Table 1 (EU Delegated Regulation 2022/1288)
        """
        portfolio = self.calculate_portfolio_financed_emissions(investees)
        total_aum = portfolio.total_aum_eur
        
        fossil_aum = sum(
            (
                inv.outstanding_amount_eur
                for inv in investees
                if inv.sector_gics in _FOSSIL_FUEL_GICS_SECTORS
            ),
            Decimal("0"),
        )
        fossil_pct = (
            (fossil_aum / total_aum * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if total_aum > Decimal("0")
            else Decimal("0")
        )
        
        energy_sectors = {"Energy", "Utilities", "Oil Gas & Consumable Fuels"}
        non_ren_aum = sum(
            (inv.outstanding_amount_eur for inv in investees if inv.sector_gics in energy_sectors),
            Decimal("0"),
        )
        non_ren_pct = (
            (non_ren_aum / total_aum * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if total_aum > Decimal("0")
            else Decimal("0")
        )
        
        ac_dqs: Dict[str, list] = {}
        for inv in investees:
            ac_dqs.setdefault(inv.asset_class.value, []).append(inv.data_quality.value)
        avg_dqs_by_ac = {ac: round(sum(v)/len(v), 2) for ac, v in ac_dqs.items()}
        
        return {
            "pai_1_ghg_emissions_tco2e": {
                "scope_1":      float(portfolio.total_financed_scope1_co2e),
                "scope_2":      float(portfolio.total_financed_scope2_co2e),
                "scope_3":      float(portfolio.total_financed_scope3_co2e),
                "total":        float(portfolio.total_financed_co2e),
                "unit":         "tCO2e",
                "standard":     "PCAF v2.0 / GHG Protocol",
                "dqs_weighted": float(portfolio.weighted_data_quality),
            },
            "pai_2_carbon_footprint": {
                "value":   float(portfolio.portfolio_carbon_footprint),
                "unit":    "tCO2e per EUR million invested",
                "aum_eur": float(total_aum),
            },
            "pai_3_ghg_intensity_waci": {
                "scope_12_waci":  float(portfolio.portfolio_waci_scope12),
                "scope_123_waci": float(portfolio.portfolio_waci_scope123),
                "unit":           "tCO2e per EUR million revenue",
                "coverage_pct":   float(portfolio.coverage_pct),
            },
            "pai_4_fossil_fuel_exposure": {
                "fossil_aum_eur":      float(fossil_aum),
                "fossil_exposure_pct": float(fossil_pct),
                "fossil_investees": [
                    inv.company_name for inv in investees
                    if inv.sector_gics in _FOSSIL_FUEL_GICS_SECTORS
                ],
            },
            "pai_5_non_renewable_energy_pct": {
                "proxy_pct": float(non_ren_pct),
                "note": (
                    "Proxy via energy-sector outstanding share. "
                    "Direct consumption data required for full PAI 5 compliance."
                ),
            },
            "pai_14_emissions_to_water": {
                "value": None,
                "note": (
                    "Requires investee-level water emissions data "
                    "(outside PCAF financed emissions scope)."
                ),
            },
            "data_quality_summary": {
                "average_dqs_by_asset_class": avg_dqs_by_ac,
                "portfolio_weighted_dqs":     float(portfolio.weighted_data_quality),
                "investee_count":             portfolio.investee_count,
                "coverage_pct":               float(portfolio.coverage_pct),
            },
            "methodology_notes": [
                "PAI 1-3 calculated per PCAF Global GHG Accounting Standard v2.0.",
                "Attribution factors applied per PCAF asset class methodology.",
                "Scope 2: market-based method applied where available.",
                "Scope 3 included where reported; DQS reflects data availability.",
                "PAI 4: fossil fuel classification based on GICS sector mapping.",
                "PAI 5: proxy estimate -- full compliance requires direct energy data.",
            ],
            "reporting_period": datetime.utcnow().strftime("%Y-%m-%d"),
        }

    def build_validation_summary(
        self,
        result: PortfolioPCAFResult,
        investees: List[InvesteeData],
    ) -> Dict[str, Any]:
        """
        Produce a complete PCAF Standard v2.0 audit trail for regulatory disclosure.
        
        Documents methodology choices, data quality flags, coverage gaps, and
        standard compliance statements.
        """
        dqs_dist: Dict[int, int] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for inv in investees:
            dqs_dist[inv.data_quality.value] += 1
        
        scope3_reporters = sum(1 for inv in investees if inv.scope3_co2e_tonnes > Decimal("0"))
        zero_rev = [inv.company_name for inv in investees if inv.annual_revenue_eur <= Decimal("0")]
        
        ac_breakdown: Dict[str, Any] = {}
        for inv in investees:
            ac = inv.asset_class.value
            if ac not in ac_breakdown:
                ac_breakdown[ac] = {"count": 0, "outstanding_eur": 0.0}
            ac_breakdown[ac]["count"] += 1
            ac_breakdown[ac]["outstanding_eur"] += float(inv.outstanding_amount_eur)
        
        cov_flag = "ADEQUATE" if result.coverage_pct >= Decimal("70") else "BELOW_THRESHOLD"
        dqs_flag = (
            "GOOD" if result.weighted_data_quality <= Decimal("2.5")
            else ("MODERATE" if result.weighted_data_quality <= Decimal("3.5") else "POOR")
        )
        
        return {
            "standard": "PCAF Global GHG Accounting and Reporting Standard v2.0 (2022)",
            "reporting_boundary": EmissionsBoundary.SCOPE_1_2_3_FINANCED.value,
            "calculation_date": datetime.utcnow().isoformat(),
            "reporting_year": max((inv.reporting_year for inv in investees), default=0),
            "investee_count": result.investee_count,
            "portfolio_metrics": {
                "total_financed_co2e_tco2e":    float(result.total_financed_co2e),
                "waci_scope12_tco2e_meur_rev":  float(result.portfolio_waci_scope12),
                "waci_scope123_tco2e_meur_rev": float(result.portfolio_waci_scope123),
                "carbon_footprint_tco2e_meur":  float(result.portfolio_carbon_footprint),
                "implied_temperature_c":        float(result.temperature_score_c),
            },
            "coverage": {
                "total_aum_eur":   float(result.total_aum_eur),
                "covered_aum_eur": float(result.covered_aum_eur),
                "coverage_pct":    float(result.coverage_pct),
                "coverage_flag":   cov_flag,
            },
            "data_quality": {
                "weighted_dqs":     float(result.weighted_data_quality),
                "dqs_flag":         dqs_flag,
                "dqs_distribution": dqs_dist,
                "scope3_reporters": scope3_reporters,
                "scope3_coverage_pct": round(
                    scope3_reporters / result.investee_count * 100
                    if result.investee_count > 0 else 0, 1
                ),
            },
            "asset_class_breakdown": ac_breakdown,
            "data_issues": {
                "zero_revenue_investees": zero_rev,
                "missing_scope3": [
                    inv.company_name for inv in investees
                    if inv.scope3_co2e_tonnes == Decimal("0")
                ],
                "low_dqs_investees": [
                    inv.company_name for inv in investees
                    if inv.data_quality.value >= DataQualityScore.SCORE_4.value
                ],
            },
            "methodology_statements": [
                "Attribution factors per PCAF Standard v2.0 Part A (Loans & Investments).",
                "Listed equity / corporate bonds: AF = outstanding / EVIC.",
                "Business loans: AF = outstanding / (total equity + total debt).",
                "Commercial RE: AF = outstanding / property value (equity proxy).",
                "Project finance / infrastructure: AF = outstanding / total project cost.",
                "Sovereign bonds: AF = outstanding / country GDP (EUR).",
                "Attribution factors capped at 1.0 to prevent over-attribution.",
                "Scope 2: market-based method preferred per PCAF.",
                "WACI = exposure-weighted avg carbon intensity (tCO2e / EUR M revenue).",
                "Temperature score: simplified piecewise linear proxy from WACI.",
                "PAI indicators aligned with SFDR RTS Annex I (EU 2022/1288).",
            ],
            "limitations": [
                "Temperature score is simplified; full ITR requires forward-looking targets.",
                "Scope 3 financed emissions may be incomplete where investees do not report.",
                "GDP-based sovereign attribution is a PCAF simplification.",
                "Market-based Scope 2 may revert to location-based if certs unavailable.",
            ],
        }


# ---------------------------------------------------------------------------
# Module-level convenience function
# ---------------------------------------------------------------------------

def calculate_portfolio_financed_emissions(
    investees_data: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Module-level entry point for PCAF portfolio financed emissions calculation.
    
    Accepts a list of investee data dictionaries, converts to InvesteeData
    instances, runs the full PCAF engine, and returns a serialisable result
    dict with financed emissions, WACI, carbon footprint, PAI indicators,
    and the complete PCAF audit trail.
    
    Parameters
    ----------
    investees_data : list[dict]
        Each dict must contain keys matching InvesteeData fields.
        Monetary values may be int, float, or str; cast to Decimal internally.
    
    Returns
    -------
    dict
        Keys: portfolio_summary, investee_results, pai_indicators,
              validation_summary, parse_errors, engine_version,
              calculation_timestamp
    """
    engine = PCAFWACIEngine()
    investees: List[InvesteeData] = []
    parse_errors: List[str] = []
    
    for idx, raw in enumerate(investees_data):
        try:
            inv = InvesteeData(
                company_name=raw["company_name"],
                isin=raw.get("isin"),
                sector_gics=raw.get("sector_gics", "Unknown"),
                country_iso=raw.get("country_iso", "XX"),
                asset_class=PCAFAssetClass(raw["asset_class"]),
                outstanding_amount_eur=Decimal(str(raw["outstanding_amount_eur"])),
                enterprise_value_eur=Decimal(str(raw.get("enterprise_value_eur", "0"))),
                total_equity_eur=Decimal(str(raw.get("total_equity_eur", "0"))),
                total_debt_eur=Decimal(str(raw.get("total_debt_eur", "0"))),
                annual_revenue_eur=Decimal(str(raw.get("annual_revenue_eur", "0"))),
                scope1_co2e_tonnes=Decimal(str(raw.get("scope1_co2e_tonnes", "0"))),
                scope2_co2e_tonnes=Decimal(str(raw.get("scope2_co2e_tonnes", "0"))),
                scope3_co2e_tonnes=Decimal(str(raw.get("scope3_co2e_tonnes", "0"))),
                data_quality=DataQualityScore(int(raw.get("data_quality", 4))),
                reporting_year=int(raw.get("reporting_year", datetime.utcnow().year - 1)),
            )
            investees.append(inv)
        except (KeyError, ValueError, InvalidOperation) as exc:
            cn = raw.get("company_name", "unknown")
            msg = f"Row {idx} ({cn}): {exc}"
            logger.error("PCAF input parse error -- %s", msg)
            parse_errors.append(msg)
    
    if not investees:
        return {
            "error": "No valid investee records could be parsed.",
            "parse_errors": parse_errors,
            "engine_version": "PCAF-WACI-Engine v2.0",
        }
    
    portfolio = engine.calculate_portfolio_financed_emissions(investees)
    pai = engine.generate_pai_metrics(investees)
    
    investee_results = []
    for inv in investees:
        try:
            res = engine._calculate_investee_financed_emissions(inv)
            investee_results.append({
                "company_name":              res.investee_name,
                "asset_class":               res.asset_class.value,
                "attribution_factor":        float(res.attribution_factor),
                "financed_scope1_tco2e":     float(res.financed_scope1_co2e),
                "financed_scope2_tco2e":     float(res.financed_scope2_co2e),
                "financed_scope3_tco2e":     float(res.financed_scope3_co2e),
                "financed_total_tco2e":      float(res.financed_total_co2e),
                "waci_intensity_tco2e_meur": float(res.waci_scope12_tco2e_meur),
                "data_quality_score":        res.data_quality_score.value,
                "outstanding_eur":           float(inv.outstanding_amount_eur),
                "sector_gics":               inv.sector_gics,
                "country_iso":               inv.country_iso,
            })
        except Exception as exc:
            logger.error("Per-investee breakdown failed for %s: %s", inv.company_name, exc)
    
    return {
        "portfolio_summary": {
            "total_financed_scope1_tco2e":  float(portfolio.total_financed_scope1_co2e),
            "total_financed_scope2_tco2e":  float(portfolio.total_financed_scope2_co2e),
            "total_financed_scope3_tco2e":  float(portfolio.total_financed_scope3_co2e),
            "total_financed_co2e_tco2e":    float(portfolio.total_financed_co2e),
            "portfolio_waci_scope12":        float(portfolio.portfolio_waci_scope12),
            "portfolio_waci_scope123":       float(portfolio.portfolio_waci_scope123),
            "portfolio_carbon_footprint":    float(portfolio.portfolio_carbon_footprint),
            "total_aum_eur":                 float(portfolio.total_aum_eur),
            "covered_aum_eur":               float(portfolio.covered_aum_eur),
            "coverage_pct":                  float(portfolio.coverage_pct),
            "weighted_data_quality_score":   float(portfolio.weighted_data_quality),
            "implied_temperature_c":         float(portfolio.temperature_score_c),
            "investee_count":                portfolio.investee_count,
        },
        "investee_results":      investee_results,
        "pai_indicators":        pai,
        "validation_summary":    portfolio.validation_summary,
        "parse_errors":          parse_errors,
        "engine_version":        "PCAF-WACI-Engine v2.0",
        "calculation_timestamp": datetime.utcnow().isoformat(),
    }

