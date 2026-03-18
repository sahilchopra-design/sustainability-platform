"""
Insurance Risk Engine
=======================
Comprehensive insurance risk analytics spanning Life, P&C, Reinsurance, and
Health lines of business. Integrates climate overlays, Solvency II standard
formula parameters, and IPCC AR6 damage functions.

Data Flow:
  1. Policy/portfolio data → actuarial model → climate adjustment →
     stressed output → ORSA/Solvency II capital → regulatory reporting
  2. WHO mortality tables provide base qx rates for life/longevity modules
  3. IPCC AR6 damage functions drive nat-cat frequency/severity multipliers
  4. Solvency II nat-cat factors from EIOPA Delegated Reg 2015/35

Sub-Modules:
  - Life: Mortality/Longevity (climate-adjusted qx), Liability Valuation (PV future obligations)
  - P&C: Nat-Cat Exposure (frequency-severity, PML), Climate Loss Frequency, Underwriting Risk
  - Reinsurance: Retrocession Chain (layer aggregation, cascade failure)
  - Health: Medical Trend (climate-health overlay)

Stakeholder Insights:
  - Actuaries: climate-adjusted reserving, IBNR adequacy, mortality/longevity risk
  - Underwriting: technical pricing adequacy, nat-cat concentration, risk selection
  - CRO: aggregation limits, tail risk, cascade failure probability
  - CFO: solvency position, capital adequacy, ORSA compliance
  - Strategy: product line profitability under climate scenarios
  - Regulators: Solvency II SCR compliance, ORSA

References:
  - Solvency II Delegated Regulation 2015/35 (EIOPA)
  - IPCC AR6 WG2 — Impacts, Adaptation, Vulnerability
  - WHO Global Health Observatory — Life Tables
  - ICS/IAIG — Insurance Capital Standards
  - IAIS Climate Risk Application Papers (2021, 2024)
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Optional

from services.reference_data_tables import (
    WHO_MORTALITY_TABLES,
    IPCC_AR6_DAMAGE_FUNCTIONS,
    SOLVENCY2_NAT_CAT_FACTORS,
    SOLVENCY2_PERIL_CORRELATIONS,
    get_mortality_rate,
    get_damage_function,
    get_nat_cat_factor,
)

logger = logging.getLogger("platform.insurance_risk")


# ═══════════════════════════════════════════════════════════════════════════
#  Climate Adjustment Parameters
# ═══════════════════════════════════════════════════════════════════════════

# Climate-health mortality adjustments per degree C warming
# Source: Lancet Countdown 2024 + IPCC AR6 WG2 Ch7 (Health)
CLIMATE_MORTALITY_ADJUSTMENTS: dict[str, dict] = {
    "heat_stress": {
        "age_bands_affected": ["65-74", "75-84", "85+"],
        "qx_multiplier_per_c": 1.04,  # +4% mortality per degree C for elderly
        "reference": "Lancet Countdown 2024 — heat-related mortality indicator",
    },
    "air_quality": {
        "age_bands_affected": ["0-1", "1-4", "65-74", "75-84", "85+"],
        "qx_multiplier_per_c": 1.02,  # PM2.5 correlates with warming
        "reference": "IPCC AR6 WG2 Ch7.3.1 — air quality and health",
    },
    "disease_vector": {
        "age_bands_affected": ["0-1", "1-4", "5-14", "15-24", "25-34", "35-44"],
        "qx_multiplier_per_c": 1.015,  # Malaria/dengue range expansion
        "reference": "IPCC AR6 WG2 Ch7.3.2 — vector-borne disease",
    },
}


# ═══════════════════════════════════════════════════════════════════════════
#  Data Classes
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class MortalityResult:
    """Climate-adjusted mortality analysis."""
    country: str
    sex: str
    warming_c: float
    base_mortality: dict[str, float]  # {age_band: qx}
    adjusted_mortality: dict[str, float]  # {age_band: adjusted_qx}
    life_expectancy_delta_years: float
    climate_drivers: list[str]
    reserve_impact_pct: float  # % change in life reserve requirements


@dataclass
class LiabilityValuationResult:
    """Life liability valuation under base and stress."""
    total_lives: int
    total_sum_assured_eur: float
    liability_pv_base_eur: float
    liability_pv_stressed_eur: float
    surplus_base_eur: float
    surplus_stressed_eur: float
    solvency_ratio_base: float
    solvency_ratio_stressed: float
    capital_buffer_eur: float
    longevity_shock_impact_eur: float


@dataclass
class NatCatExposureResult:
    """Natural catastrophe exposure analysis."""
    country: str
    perils_analysed: list[str]
    total_exposure_eur: float
    expected_annual_loss_eur: float
    pml_100yr_eur: float
    pml_250yr_eur: float
    diversification_benefit_pct: float
    concentration_risk: list[dict]
    tail_var_99_5_eur: float
    solvency2_nat_cat_scr_eur: float


@dataclass
class ClimateFrequencyResult:
    """Climate-adjusted loss frequency analysis."""
    hazard_types: list[str]
    warming_scenario_c: float
    loss_freq_base: dict[str, float]
    loss_freq_stressed: dict[str, float]
    severity_multiplier: dict[str, float]
    loss_ratio_impact_pct: float
    combined_ratio_delta_pct: float
    damage_functions_used: list[str]


@dataclass
class UnderwritingResult:
    """Underwriting risk analysis."""
    portfolio_size: int
    gross_written_premium_eur: float
    net_earned_premium_eur: float
    claims_incurred_eur: float
    loss_ratio_pct: float
    expense_ratio_pct: float
    combined_ratio_pct: float
    technical_price_adequacy_pct: float
    risk_margin_eur: float
    diversification_benefit_pct: float
    climate_adjusted_combined_ratio_pct: float


@dataclass
class RetrocessionResult:
    """Reinsurance retrocession chain analysis."""
    gross_exposure_eur: float
    ceded_premium_eur: float
    net_retention_eur: float
    layers: list[dict]  # [{layer_name, attachment, limit, exhaustion_prob}]
    retro_exhaustion_prob_pct: float
    counterparty_credit_risk_eur: float
    cascade_failure_prob_pct: float
    net_combined_ratio_pct: float


@dataclass
class MedicalTrendResult:
    """Health insurance medical trend analysis."""
    claim_cost_per_member_eur: float
    medical_cpi_trend_pct: float
    climate_health_overlay_pct: float
    projected_claim_cost_1yr_eur: float
    projected_claim_cost_3yr_eur: float
    pandemic_surge_pct: float
    premium_adequacy_ratio: float
    ibnr_adequacy_pct: float


@dataclass
class InsuranceRiskSummary:
    """Comprehensive insurance risk summary across all LOBs."""
    entity_name: str
    life_mortality: Optional[MortalityResult]
    life_liability: Optional[LiabilityValuationResult]
    natcat_exposure: Optional[NatCatExposureResult]
    climate_frequency: Optional[ClimateFrequencyResult]
    underwriting: Optional[UnderwritingResult]
    retrocession: Optional[RetrocessionResult]
    medical_trend: Optional[MedicalTrendResult]
    overall_solvency_ratio: float
    total_scr_eur: float
    capital_surplus_eur: float
    recommendations: list[str]


# ═══════════════════════════════════════════════════════════════════════════
#  Engine
# ═══════════════════════════════════════════════════════════════════════════

class InsuranceRiskEngine:
    """
    Comprehensive insurance risk calculation engine.

    Spans Life, P&C, Reinsurance, and Health sub-modules with
    integrated climate overlays and Solvency II standard formula.

    Input Parameters:
      - country (str): ISO2/ISO3 country code
      - sex (str): "male"/"female" for mortality tables
      - warming_scenario_c (float): Temperature warming in degrees C
      - exposure_eur (float): Total sum insured / exposure
      - policy_book (list): Policy-level data for liability valuation
      - hazard_types (list): Perils for nat-cat analysis
      - loss_history (list): Historical claims for frequency analysis
      - premium_data (dict): GWP, NEP, expenses for underwriting
      - retro_layers (list): Reinsurance programme structure
      - health_data (dict): Member count, claim costs, trend

    Transformations:
      1. Base mortality rates from WHO life tables
      2. Climate adjustment: qx × climate_multiplier per hazard driver
      3. Liability PV: discounted future cash flows under stressed mortality
      4. Nat-cat: exposure × Solvency II factors × IPCC climate multipliers
      5. Frequency-severity: historical trend × climate damage functions
      6. Underwriting: combined ratio decomposition with climate overlay
      7. Retrocession: layer-by-layer aggregation, cascade probability
      8. Medical trend: CPI inflation + climate-health overlay

    Output Results:
      - Per-LOB risk metrics (mortality deltas, PMLs, combined ratios)
      - Solvency II SCR components
      - Capital adequacy and surplus/deficit
      - Climate-adjusted reserves and pricing signals
      - Regulatory compliance indicators (ORSA, Solvency II)

    Stakeholder Insights:
      - Actuaries: climate-adjusted reserving, mortality/longevity risk
      - CRO: aggregation limits, tail risk, cascade failure probability
      - CFO: solvency position, capital buffer under stress
      - Underwriting: pricing adequacy signals per LOB
      - Board: overall capital adequacy under climate scenarios
      - Regulators: Solvency II SCR compliance, ORSA stress tests

    Data Lineage:
      policy_data → who_mortality_tables → climate_adjustment →
      ipcc_damage_functions → solvency2_factors → stressed_output →
      orsa_capital → entity360 (insurance profile)

    Reference Data:
      - who_mortality_tables (WHO GHO life tables)
      - ipcc_ar6_damage_functions (climate damage coefficients)
      - solvency2_nat_cat_factors (EIOPA Delegated Reg 2015/35)
      - ngfs_scenario_v4_params (NGFS climate scenarios)
      - climate_mortality_adjustments (Lancet Countdown / IPCC WG2)

    FI Types: Insurance companies (life, non-life, composite, reinsurance)
    LOBs: Life, P&C (property, casualty, motor, marine), Reinsurance, Health
    """

    def __init__(self):
        self._mortality_tables = WHO_MORTALITY_TABLES
        self._damage_functions = IPCC_AR6_DAMAGE_FUNCTIONS
        self._nat_cat_factors = SOLVENCY2_NAT_CAT_FACTORS
        self._climate_adj = CLIMATE_MORTALITY_ADJUSTMENTS

    # ── Life: Mortality / Longevity ──────────────────────────────────────

    def assess_mortality(
        self,
        country: str,
        sex: str = "male",
        warming_c: float = 1.5,
    ) -> MortalityResult:
        """
        Climate-adjusted mortality assessment.

        Applies WHO base mortality rates with climate overlays for heat stress,
        air quality, and disease vector shifts.

        Parameters:
            country: ISO3 country code (e.g., "GBR", "USA")
            sex: "male" or "female"
            warming_c: Degrees C warming above pre-industrial (default 1.5°C)

        Returns:
            MortalityResult with base and adjusted qx rates
        """
        base_table = self._mortality_tables.get(country, {}).get(sex, {})
        if not base_table:
            # Fallback to GBR if country not in embedded tables
            base_table = self._mortality_tables.get("GBR", {}).get(sex, {})

        adjusted = {}
        drivers = []

        for age_band, qx in base_table.items():
            adj_qx = qx
            for driver, params in self._climate_adj.items():
                if age_band in params["age_bands_affected"]:
                    multiplier = params["qx_multiplier_per_c"] ** warming_c
                    adj_qx *= multiplier
                    if driver not in drivers:
                        drivers.append(driver)
            # Cap at 1.0
            adjusted[age_band] = min(round(adj_qx, 6), 1.0)

        # Approximate life expectancy delta (simplified)
        # Sum of qx differences weighted by mid-band age
        age_midpoints = {"0-1": 0.5, "1-4": 2.5, "5-14": 10, "15-24": 20,
                         "25-34": 30, "35-44": 40, "45-54": 50, "55-64": 60,
                         "65-74": 70, "75-84": 80, "85+": 90}
        delta_sum = 0.0
        for ab in base_table:
            delta = (adjusted.get(ab, 0) - base_table[ab])
            midpoint = age_midpoints.get(ab, 50)
            # Weight by remaining life expectancy approximation
            remaining = max(0, 85 - midpoint)
            delta_sum += delta * remaining

        le_delta = round(-delta_sum * 10, 2)  # Simplified scaling

        # Reserve impact: weighted average qx change for insured ages (25-84)
        insured_ages = ["25-34", "35-44", "45-54", "55-64", "65-74", "75-84"]
        base_avg = sum(base_table.get(a, 0) for a in insured_ages) / len(insured_ages)
        adj_avg = sum(adjusted.get(a, 0) for a in insured_ages) / len(insured_ages)
        reserve_impact = round((adj_avg - base_avg) / base_avg * 100, 2) if base_avg > 0 else 0.0

        return MortalityResult(
            country=country,
            sex=sex,
            warming_c=warming_c,
            base_mortality=base_table,
            adjusted_mortality=adjusted,
            life_expectancy_delta_years=le_delta,
            climate_drivers=drivers,
            reserve_impact_pct=reserve_impact,
        )

    # ── Life: Liability Valuation ────────────────────────────────────────

    def value_liabilities(
        self,
        total_lives: int = 10000,
        avg_sum_assured_eur: float = 100000.0,
        avg_remaining_term_years: int = 20,
        avg_age: int = 45,
        discount_rate_pct: float = 2.5,
        longevity_shock_bps: int = 20,
        country: str = "GBR",
    ) -> LiabilityValuationResult:
        """
        Life liability valuation under base and stressed longevity.

        Calculates PV of future obligations using WHO mortality tables and
        applies longevity stress per Solvency II ORSA requirements.

        Parameters:
            total_lives: Number of insured lives
            avg_sum_assured_eur: Average sum assured per life
            avg_remaining_term_years: Average remaining policy term
            avg_age: Average policyholder age
            discount_rate_pct: Risk-free discount rate (%)
            longevity_shock_bps: Longevity stress in basis points
            country: Country for mortality tables

        Returns:
            LiabilityValuationResult with base and stressed PV
        """
        total_sa = total_lives * avg_sum_assured_eur
        r = discount_rate_pct / 100.0

        # Simplified PV calculation using average mortality
        # PV = SA × sum(qx_adjusted × (1+r)^-t for t in term)
        mort = self._mortality_tables.get(country, {}).get("male", {})
        # Map avg_age to age band
        age_band = self._age_to_band(avg_age)
        base_qx = mort.get(age_band, 0.005)

        pv_base = 0.0
        pv_stressed = 0.0
        for t in range(1, avg_remaining_term_years + 1):
            discount = (1 + r) ** (-t)
            # Mortality probability for year t (simplified: constant qx)
            prob_death_t = base_qx * (1 + 0.01 * t)  # Aging adjustment
            pv_base += total_sa * min(prob_death_t, 1.0) * discount

            # Stressed longevity: mortality decreases (longevity risk)
            shock = longevity_shock_bps / 10000.0
            stressed_qx = base_qx * (1 - shock) * (1 + 0.01 * t)
            pv_stressed += total_sa * min(stressed_qx, 1.0) * discount

        # For longevity risk, lower mortality = higher liabilities (annuity business)
        # Adjust: stressed PV is higher for annuity portfolios
        # Here we model term life, so lower mortality = lower PV but for annuities it's opposite
        annuity_adj = 1.0 + longevity_shock_bps / 10000.0 * 5.0  # Simple annuity factor
        pv_stressed_final = pv_stressed * annuity_adj

        own_funds = total_sa * 0.08  # 8% of sum assured as own funds (simplified)
        surplus_base = own_funds - pv_base
        surplus_stressed = own_funds - pv_stressed_final

        solvency_base = round(own_funds / pv_base, 4) if pv_base > 0 else 999.0
        solvency_stressed = round(own_funds / pv_stressed_final, 4) if pv_stressed_final > 0 else 999.0

        return LiabilityValuationResult(
            total_lives=total_lives,
            total_sum_assured_eur=total_sa,
            liability_pv_base_eur=round(pv_base, 2),
            liability_pv_stressed_eur=round(pv_stressed_final, 2),
            surplus_base_eur=round(surplus_base, 2),
            surplus_stressed_eur=round(surplus_stressed, 2),
            solvency_ratio_base=solvency_base,
            solvency_ratio_stressed=solvency_stressed,
            capital_buffer_eur=round(surplus_stressed, 2),
            longevity_shock_impact_eur=round(pv_stressed_final - pv_base, 2),
        )

    # ── P&C: Nat-Cat Exposure ────────────────────────────────────────────

    def assess_natcat_exposure(
        self,
        country: str = "DE",
        exposure_eur: float = 1_000_000_000,
        perils: list[str] | None = None,
        warming_c: float = 1.5,
    ) -> NatCatExposureResult:
        """
        Natural catastrophe exposure analysis with climate overlay.

        Uses Solvency II standard formula nat-cat factors from EIOPA
        Delegated Regulation, scaled by IPCC AR6 climate multipliers.

        Parameters:
            country: ISO2 country code (e.g., "DE", "FR", "GB")
            exposure_eur: Total sum insured in EUR
            perils: List of perils to analyse (default: all available)
            warming_c: Temperature warming scenario in degrees C

        Returns:
            NatCatExposureResult with EAL, PML, and SCR components
        """
        country_factors = self._nat_cat_factors.get(country, {})
        if not country_factors:
            # Fallback to DE
            country_factors = self._nat_cat_factors.get("DE", {})

        if perils is None:
            perils = list(country_factors.keys())

        peril_losses = {}
        eal_total = 0.0
        pml_100_total = 0.0
        pml_250_total = 0.0

        for peril in perils:
            factor = country_factors.get(peril)
            if not factor:
                continue

            f_200yr = factor["factor_200yr"]

            # Climate multiplier from IPCC damage functions
            damage_fn = self._damage_functions.get(peril, {})
            freq_mult = damage_fn.get("frequency_multiplier_per_c", 1.0) ** warming_c
            sev_mult = damage_fn.get("severity_multiplier_per_c", 1.0) ** warming_c

            # Expected annual loss = exposure × factor / return_period × climate multiplier
            eal = exposure_eur * f_200yr / 200 * freq_mult * sev_mult
            # PML 100yr ≈ exposure × factor × (200/100)^0.5 × climate
            pml_100 = exposure_eur * f_200yr * 1.41 * freq_mult * sev_mult
            # PML 250yr ≈ exposure × factor × (250/200)^0.5 × climate
            pml_250 = exposure_eur * f_200yr * 1.12 * 1.41 * freq_mult * sev_mult

            peril_losses[peril] = {
                "eal_eur": round(eal, 2),
                "pml_100yr_eur": round(pml_100, 2),
                "pml_250yr_eur": round(pml_250, 2),
            }
            eal_total += eal
            pml_100_total += pml_100
            pml_250_total += pml_250

        # Diversification benefit using peril correlation matrix
        n_perils = len(peril_losses)
        if n_perils > 1:
            # Simple diversification: sqrt(sum(loss^2) + 2*sum(corr*loss_i*loss_j))
            pml_values = [v["pml_100yr_eur"] for v in peril_losses.values()]
            sum_sq = sum(v**2 for v in pml_values)
            cross = 0.0
            peril_list = list(peril_losses.keys())
            for i in range(len(peril_list)):
                for j in range(i+1, len(peril_list)):
                    corr = SOLVENCY2_PERIL_CORRELATIONS.get(
                        (peril_list[i], peril_list[j]),
                        SOLVENCY2_PERIL_CORRELATIONS.get((peril_list[j], peril_list[i]), 0.25)
                    )
                    cross += 2 * corr * pml_values[i] * pml_values[j]
            diversified_pml = math.sqrt(sum_sq + cross) if (sum_sq + cross) > 0 else pml_100_total
            div_benefit = round((1 - diversified_pml / pml_100_total) * 100, 1) if pml_100_total > 0 else 0.0
        else:
            diversified_pml = pml_100_total
            div_benefit = 0.0

        # Concentration risk — top peril by PML share
        concentration = []
        for p, v in sorted(peril_losses.items(), key=lambda x: -x[1]["pml_100yr_eur"]):
            share = round(v["pml_100yr_eur"] / pml_100_total * 100, 1) if pml_100_total > 0 else 0
            concentration.append({"peril": p, "pml_share_pct": share, "pml_eur": v["pml_100yr_eur"]})

        # Tail VaR 99.5% ≈ PML 200yr (Solvency II standard)
        tail_var = exposure_eur * sum(
            country_factors.get(p, {}).get("factor_200yr", 0)
            for p in peril_losses
        )

        return NatCatExposureResult(
            country=country,
            perils_analysed=list(peril_losses.keys()),
            total_exposure_eur=exposure_eur,
            expected_annual_loss_eur=round(eal_total, 2),
            pml_100yr_eur=round(pml_100_total, 2),
            pml_250yr_eur=round(pml_250_total, 2),
            diversification_benefit_pct=div_benefit,
            concentration_risk=concentration,
            tail_var_99_5_eur=round(tail_var, 2),
            solvency2_nat_cat_scr_eur=round(diversified_pml, 2),
        )

    # ── P&C: Climate Loss Frequency ──────────────────────────────────────

    def assess_climate_frequency(
        self,
        hazard_types: list[str] | None = None,
        warming_scenario_c: float = 2.0,
        base_loss_ratio_pct: float = 65.0,
        expense_ratio_pct: float = 30.0,
    ) -> ClimateFrequencyResult:
        """
        Climate-adjusted loss frequency and severity analysis.

        Applies IPCC AR6 damage functions to extrapolate climate-driven
        changes in loss frequency and severity by hazard type.

        Parameters:
            hazard_types: Perils to analyse (default: all IPCC hazards)
            warming_scenario_c: Temperature warming in degrees C
            base_loss_ratio_pct: Current baseline loss ratio (%)
            expense_ratio_pct: Current expense ratio (%)

        Returns:
            ClimateFrequencyResult with frequency/severity multipliers
        """
        if hazard_types is None:
            hazard_types = list(self._damage_functions.keys())

        freq_base = {}
        freq_stressed = {}
        sev_mult = {}
        functions_used = []

        for hazard in hazard_types:
            fn = self._damage_functions.get(hazard)
            if not fn:
                continue

            base_freq = 1.0  # Normalised base frequency
            freq_multiplier = fn["frequency_multiplier_per_c"] ** warming_scenario_c
            sev_multiplier = fn["severity_multiplier_per_c"] ** warming_scenario_c

            freq_base[hazard] = base_freq
            freq_stressed[hazard] = round(base_freq * freq_multiplier, 4)
            sev_mult[hazard] = round(sev_multiplier, 4)
            functions_used.append(hazard)

        # Aggregate loss ratio impact
        if freq_stressed and sev_mult:
            avg_freq_mult = sum(freq_stressed.values()) / len(freq_stressed)
            avg_sev_mult = sum(sev_mult.values()) / len(sev_mult)
            loss_ratio_climate = base_loss_ratio_pct * avg_freq_mult * avg_sev_mult
            delta = loss_ratio_climate - base_loss_ratio_pct
            combined_delta = delta  # expense ratio unchanged
        else:
            loss_ratio_climate = base_loss_ratio_pct
            delta = 0.0
            combined_delta = 0.0

        return ClimateFrequencyResult(
            hazard_types=hazard_types,
            warming_scenario_c=warming_scenario_c,
            loss_freq_base=freq_base,
            loss_freq_stressed=freq_stressed,
            severity_multiplier=sev_mult,
            loss_ratio_impact_pct=round(delta, 2),
            combined_ratio_delta_pct=round(combined_delta, 2),
            damage_functions_used=functions_used,
        )

    # ── P&C: Underwriting Risk ───────────────────────────────────────────

    def assess_underwriting(
        self,
        gwp_eur: float = 500_000_000,
        net_earned_premium_eur: float = 450_000_000,
        claims_incurred_eur: float = 292_500_000,
        expense_ratio_pct: float = 30.0,
        portfolio_size: int = 50000,
        warming_c: float = 1.5,
    ) -> UnderwritingResult:
        """
        Underwriting risk assessment with climate overlay.

        Decomposes combined ratio and applies climate-adjusted
        loss frequency/severity to derive technical pricing adequacy.

        Parameters:
            gwp_eur: Gross written premium
            net_earned_premium_eur: Net earned premium
            claims_incurred_eur: Total claims incurred
            expense_ratio_pct: Operating expense ratio (%)
            portfolio_size: Number of policies
            warming_c: Temperature warming scenario

        Returns:
            UnderwritingResult with combined ratio decomposition
        """
        loss_ratio = round(claims_incurred_eur / net_earned_premium_eur * 100, 2) if net_earned_premium_eur > 0 else 0
        combined = round(loss_ratio + expense_ratio_pct, 2)
        risk_margin = max(0, net_earned_premium_eur - claims_incurred_eur - net_earned_premium_eur * expense_ratio_pct / 100)

        # Climate adjustment to combined ratio
        climate_freq = self.assess_climate_frequency(warming_scenario_c=warming_c, base_loss_ratio_pct=loss_ratio)
        climate_combined = round(combined + climate_freq.combined_ratio_delta_pct, 2)

        # Technical price adequacy: 100% means breakeven, >100% means profitable
        price_adequacy = round(100 / combined * 100, 1) if combined > 0 else 0

        # Diversification benefit (LOB diversification, simplified)
        div_benefit = 15.0  # Standard P&C diversification

        return UnderwritingResult(
            portfolio_size=portfolio_size,
            gross_written_premium_eur=gwp_eur,
            net_earned_premium_eur=net_earned_premium_eur,
            claims_incurred_eur=claims_incurred_eur,
            loss_ratio_pct=loss_ratio,
            expense_ratio_pct=expense_ratio_pct,
            combined_ratio_pct=combined,
            technical_price_adequacy_pct=price_adequacy,
            risk_margin_eur=round(risk_margin, 2),
            diversification_benefit_pct=div_benefit,
            climate_adjusted_combined_ratio_pct=climate_combined,
        )

    # ── Reinsurance: Retrocession Chain ──────────────────────────────────

    def assess_retrocession(
        self,
        gross_exposure_eur: float = 2_000_000_000,
        ceded_premium_eur: float = 200_000_000,
        layers: list[dict] | None = None,
        counterparty_default_prob_pct: float = 0.5,
    ) -> RetrocessionResult:
        """
        Reinsurance retrocession chain analysis.

        Aggregates layer-by-layer retention, estimates cascade failure
        probability, and calculates counterparty credit risk.

        Parameters:
            gross_exposure_eur: Total gross exposure
            ceded_premium_eur: Total ceded reinsurance premium
            layers: List of layers [{name, attachment_eur, limit_eur}]
            counterparty_default_prob_pct: Reinsurer default probability

        Returns:
            RetrocessionResult with layer analysis and cascade risk
        """
        if layers is None:
            layers = [
                {"name": "QS 30%", "attachment_eur": 0, "limit_eur": gross_exposure_eur * 0.30},
                {"name": "XL 1st", "attachment_eur": 50_000_000, "limit_eur": 150_000_000},
                {"name": "XL 2nd", "attachment_eur": 200_000_000, "limit_eur": 300_000_000},
                {"name": "Cat XL", "attachment_eur": 500_000_000, "limit_eur": 500_000_000},
            ]

        total_ceded = sum(l["limit_eur"] for l in layers)
        net_retention = max(0, gross_exposure_eur - total_ceded)

        layer_results = []
        for layer in layers:
            # Exhaustion probability (simplified: inverse of attachment relative to exposure)
            attachment_pct = layer["attachment_eur"] / gross_exposure_eur if gross_exposure_eur > 0 else 0
            exhaust_prob = max(0.5, (1 - attachment_pct) * 100) * 0.1  # Simplified
            layer_results.append({
                "layer_name": layer["name"],
                "attachment_eur": layer["attachment_eur"],
                "limit_eur": layer["limit_eur"],
                "exhaustion_prob_pct": round(exhaust_prob, 2),
            })

        # Cascade failure: probability that all layers fail simultaneously
        cascade_prob = 1.0
        for lr in layer_results:
            cascade_prob *= lr["exhaustion_prob_pct"] / 100
        cascade_prob = round(cascade_prob * 100, 4)

        # Counterparty credit risk
        cp_risk = total_ceded * counterparty_default_prob_pct / 100

        # Net combined ratio (simplified)
        net_premium = ceded_premium_eur * 0.7  # Commission deduction
        net_combined = round(85.0 + (net_retention / gross_exposure_eur * 10), 2)

        return RetrocessionResult(
            gross_exposure_eur=gross_exposure_eur,
            ceded_premium_eur=ceded_premium_eur,
            net_retention_eur=round(net_retention, 2),
            layers=layer_results,
            retro_exhaustion_prob_pct=round(layer_results[-1]["exhaustion_prob_pct"] if layer_results else 0, 2),
            counterparty_credit_risk_eur=round(cp_risk, 2),
            cascade_failure_prob_pct=cascade_prob,
            net_combined_ratio_pct=net_combined,
        )

    # ── Health: Medical Trend ────────────────────────────────────────────

    def assess_medical_trend(
        self,
        claim_cost_per_member_eur: float = 3500.0,
        medical_cpi_trend_pct: float = 4.5,
        member_count: int = 100000,
        warming_c: float = 1.5,
        pandemic_scenario: bool = False,
    ) -> MedicalTrendResult:
        """
        Health insurance medical trend analysis with climate overlay.

        Combines medical CPI inflation with climate-health effects
        (heat-related morbidity, air quality, disease expansion).

        Parameters:
            claim_cost_per_member_eur: Average annual claim cost per member
            medical_cpi_trend_pct: Medical cost inflation rate (%)
            member_count: Total insured members
            warming_c: Temperature warming for climate-health overlay
            pandemic_scenario: Whether to include pandemic surge

        Returns:
            MedicalTrendResult with projected costs and adequacy ratios
        """
        # Climate-health overlay: additional morbidity from warming
        # Heat stress: +1.5% per degree C (ER visits, heatstroke, cardio)
        # Air quality: +1.0% per degree C (respiratory, asthma)
        # Disease vectors: +0.5% per degree C (dengue, malaria spillover in non-endemic areas)
        climate_overlay = warming_c * 3.0  # 3% per degree total

        total_trend = medical_cpi_trend_pct + climate_overlay

        # Project forward
        cost_1yr = claim_cost_per_member_eur * (1 + total_trend / 100)
        cost_3yr = claim_cost_per_member_eur * (1 + total_trend / 100) ** 3

        # Pandemic surge
        pandemic_surge = 0.0
        if pandemic_scenario:
            pandemic_surge = 35.0  # +35% surge in claim costs
            cost_1yr *= (1 + pandemic_surge / 100)
            cost_3yr *= (1 + pandemic_surge / 100 * 0.5)  # Partial for 3yr

        # Premium adequacy: implied premium vs projected cost
        implied_premium = claim_cost_per_member_eur * 1.25  # 25% loading
        premium_adequacy = round(implied_premium / cost_1yr, 4) if cost_1yr > 0 else 0

        # IBNR adequacy check
        ibnr_adequacy = round(100 - (total_trend - medical_cpi_trend_pct), 1)

        return MedicalTrendResult(
            claim_cost_per_member_eur=claim_cost_per_member_eur,
            medical_cpi_trend_pct=medical_cpi_trend_pct,
            climate_health_overlay_pct=round(climate_overlay, 2),
            projected_claim_cost_1yr_eur=round(cost_1yr, 2),
            projected_claim_cost_3yr_eur=round(cost_3yr, 2),
            pandemic_surge_pct=pandemic_surge,
            premium_adequacy_ratio=premium_adequacy,
            ibnr_adequacy_pct=ibnr_adequacy,
        )

    # ── Comprehensive Summary ────────────────────────────────────────────

    def comprehensive_assessment(
        self,
        entity_name: str = "InsureCo",
        country: str = "GBR",
        warming_c: float = 1.5,
        exposure_eur: float = 5_000_000_000,
        own_funds_eur: float = 800_000_000,
    ) -> InsuranceRiskSummary:
        """
        Run all sub-modules and produce a comprehensive insurance risk summary.

        Parameters:
            entity_name: Name of the insurer
            country: Operating country (ISO3 for mortality, ISO2 for nat-cat)
            warming_c: Climate warming scenario
            exposure_eur: Total insured exposure
            own_funds_eur: Total eligible own funds (Solvency II)

        Returns:
            InsuranceRiskSummary with all sub-module results
        """
        # Map ISO3 to ISO2 for nat-cat
        iso2_map = {"GBR": "GB", "USA": "US", "DEU": "DE", "FRA": "FR",
                     "JPN": "JP", "IND": "IN", "CHN": "CN", "BRA": "BR",
                     "AUS": "AU", "NGA": "NG"}
        country_iso2 = iso2_map.get(country, country[:2].upper())

        mort = self.assess_mortality(country=country, warming_c=warming_c)
        liab = self.value_liabilities(country=country)
        natcat = self.assess_natcat_exposure(country=country_iso2, exposure_eur=exposure_eur, warming_c=warming_c)
        freq = self.assess_climate_frequency(warming_scenario_c=warming_c)
        uw = self.assess_underwriting(warming_c=warming_c)
        retro = self.assess_retrocession(gross_exposure_eur=exposure_eur)
        health = self.assess_medical_trend(warming_c=warming_c)

        # Aggregate SCR (simplified: nat-cat + life + health + market)
        total_scr = natcat.solvency2_nat_cat_scr_eur + abs(liab.longevity_shock_impact_eur) + exposure_eur * 0.01
        surplus = own_funds_eur - total_scr
        solvency = round(own_funds_eur / total_scr, 4) if total_scr > 0 else 999.0

        recs = []
        if solvency < 1.5:
            recs.append(f"Solvency ratio {solvency:.0%} below 150% target — review capital plan")
        if mort.reserve_impact_pct > 3.0:
            recs.append(f"Climate mortality impact {mort.reserve_impact_pct}% — update actuarial assumptions")
        if natcat.pml_250yr_eur > exposure_eur * 0.05:
            recs.append("PML 250yr exceeds 5% of exposure — increase reinsurance protection")
        if uw.climate_adjusted_combined_ratio_pct > 100:
            recs.append(f"Climate-adjusted CR {uw.climate_adjusted_combined_ratio_pct}% — review pricing")
        if health.premium_adequacy_ratio < 1.0:
            recs.append("Health premium inadequacy — consider rate increase")
        if not recs:
            recs.append("All risk indicators within tolerance")

        return InsuranceRiskSummary(
            entity_name=entity_name,
            life_mortality=mort,
            life_liability=liab,
            natcat_exposure=natcat,
            climate_frequency=freq,
            underwriting=uw,
            retrocession=retro,
            medical_trend=health,
            overall_solvency_ratio=solvency,
            total_scr_eur=round(total_scr, 2),
            capital_surplus_eur=round(surplus, 2),
            recommendations=recs,
        )

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _age_to_band(age: int) -> str:
        """Map numeric age to WHO age band key."""
        if age < 1:
            return "0-1"
        elif age < 5:
            return "1-4"
        elif age < 15:
            return "5-14"
        elif age < 25:
            return "15-24"
        elif age < 35:
            return "25-34"
        elif age < 45:
            return "35-44"
        elif age < 55:
            return "45-54"
        elif age < 65:
            return "55-64"
        elif age < 75:
            return "65-74"
        elif age < 85:
            return "75-84"
        return "85+"

    def get_available_countries(self) -> list[str]:
        """List countries with embedded mortality tables."""
        return sorted(self._mortality_tables.keys())

    def get_available_perils(self) -> list[str]:
        """List perils with embedded damage functions."""
        return sorted(self._damage_functions.keys())

    def get_solvency2_countries(self) -> list[str]:
        """List countries with Solvency II nat-cat factors."""
        return sorted(self._nat_cat_factors.keys())

    def get_climate_adjustments(self) -> dict:
        """Get climate-mortality adjustment parameters."""
        return self._climate_adj
