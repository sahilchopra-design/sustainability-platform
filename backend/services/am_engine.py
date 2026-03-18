"""
Asset Management Engine
========================
Comprehensive analytics for active equity, fixed income, and multi-asset
portfolio management with ESG integration and climate alignment.

Sub-Modules:
  1. ESG Attribution        — Fama-French + ESG factor decomposition, selection/allocation effects
  2. Paris Alignment Tracker — Portfolio temperature scoring, pathway gap analysis
  3. Green Bond Screening    — ICMA GBS eligibility, greenium, DNSH flags
  4. Climate-Adjusted Spreads— Transition risk → credit spread delta, migration probabilities
  5. LP Analytics            — Liquidity coverage, investor concentration, redemption stress
  6. ESG-Constrained Optimisation — Mean-variance with ESG tilts, exclusions, tracking error

Data Flow:
  Holdings data → factor exposure decomposition → ESG score overlay →
  climate alignment check → optimised weights → risk/return attribution

References:
  - ICMA Green Bond Principles (2021) + EU GBS Regulation 2023/2631
  - Paris Agreement Capital Transition Assessment (PACTA)
  - MSCI ESG Ratings Methodology, FTSE Russell, Sustainalytics
  - Fama-French 5-factor model (2015) + Pastor-Stambaugh ESG extension
  - IIF Principles for Stable Capital Flows (LP liquidity)
  - Markowitz (1952), Black-Litterman (1990) for optimisation
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("platform.am_engine")


# ═══════════════════════════════════════════════════════════════════════════
#  Reference Data
# ═══════════════════════════════════════════════════════════════════════════

# Fama-French 5-factor + ESG factor premia (annualised bps)
_FACTOR_PREMIA_BPS: Dict[str, float] = {
    "market":     500.0,
    "size":        80.0,
    "value":      120.0,
    "profitability": 150.0,
    "investment":  60.0,
    "esg_quality": 45.0,   # Pastor-Stambaugh ESG taste premium
    "low_carbon":  30.0,   # Green factor premium (in-Bok Kim et al. 2024)
}

# SBTi sector pathways — annual decarbonisation rate (% p.a.)
_SBTI_SECTOR_PATHWAYS: Dict[str, float] = {
    "power_utilities": -7.0,
    "steel":           -4.0,
    "cement":          -3.5,
    "chemicals":       -2.8,
    "aviation":        -3.0,
    "shipping":        -2.5,
    "automotive":      -5.0,
    "real_estate":     -4.5,
    "oil_gas":         -6.0,
    "agriculture":     -2.0,
    "financial":       -3.5,
    "technology":      -2.0,
    "consumer":        -2.5,
    "default":         -3.0,
}

# ICMA GBS — Use of Proceeds categories
_ICMA_UOP_CATEGORIES = {
    "renewable_energy", "energy_efficiency", "pollution_prevention",
    "biodiversity_conservation", "clean_transportation",
    "sustainable_water", "climate_adaptation", "green_buildings",
    "circular_economy", "eco_efficient_products",
}

# NACE sector → average carbon intensity (tCO2e/EUR m revenue)
_SECTOR_CARBON_INTENSITY: Dict[str, float] = {
    "power_utilities": 820.0,
    "steel":           1200.0,
    "cement":          950.0,
    "chemicals":       450.0,
    "oil_gas":         680.0,
    "aviation":        1100.0,
    "shipping":        750.0,
    "automotive":      280.0,
    "real_estate":     120.0,
    "agriculture":     350.0,
    "financial":       15.0,
    "technology":      25.0,
    "consumer":        90.0,
    "healthcare":      60.0,
    "default":         180.0,
}

# Temperature pathway targets (°C by 2050)
_PATHWAY_TARGETS: Dict[str, float] = {
    "1.5C": 1.5,
    "well_below_2C": 1.75,
    "2C": 2.0,
    "current_policies": 3.2,
}

# Transition risk → credit spread adjustment (bps per unit of transition risk score)
_TRANSITION_SPREAD_FACTORS: Dict[str, float] = {
    "AAA": 0.3,
    "AA":  0.5,
    "A":   0.8,
    "BBB": 1.5,
    "BB":  3.0,
    "B":   5.0,
    "CCC": 8.0,
    "default": 2.0,
}

# Greenium by credit rating (bps tighter for green bonds vs conventional)
_GREENIUM_BPS: Dict[str, float] = {
    "AAA": 3.0,
    "AA":  5.0,
    "A":   7.0,
    "BBB": 10.0,
    "BB":  15.0,
    "B":   20.0,
    "default": 8.0,
}


# ═══════════════════════════════════════════════════════════════════════════
#  1. ESG Attribution
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Holding:
    """Single portfolio holding."""
    security_id: str
    name: str
    weight_pct: float                       # portfolio weight (%)
    sector: str = "default"
    esg_score: float = 50.0                 # 0-100
    carbon_intensity_tco2e_m: float = 0.0   # tCO2e per EUR million revenue
    return_pct: float = 0.0                 # period return (%)
    benchmark_weight_pct: float = 0.0
    benchmark_return_pct: float = 0.0
    rating: str = "BBB"                     # credit rating


@dataclass
class ESGAttributionResult:
    """ESG factor attribution output."""
    total_return_pct: float
    benchmark_return_pct: float
    active_return_bps: float
    # Factor contributions (bps)
    market_contribution_bps: float
    size_contribution_bps: float
    value_contribution_bps: float
    profitability_contribution_bps: float
    investment_contribution_bps: float
    esg_quality_contribution_bps: float
    low_carbon_contribution_bps: float
    residual_alpha_bps: float
    # Brinson attribution
    selection_effect_bps: float
    allocation_effect_bps: float
    interaction_effect_bps: float
    # ESG metrics
    portfolio_esg_score: float
    benchmark_esg_score: float
    esg_tilt_bps: float                     # return from ESG overweight


def calculate_esg_attribution(
    holdings: List[Holding],
    benchmark_esg_score: float = 50.0,
) -> ESGAttributionResult:
    """
    Decompose portfolio returns into Fama-French 5-factor + ESG factors.
    Uses Brinson-Fachler selection/allocation attribution.
    """
    if not holdings:
        return ESGAttributionResult(
            total_return_pct=0, benchmark_return_pct=0, active_return_bps=0,
            market_contribution_bps=0, size_contribution_bps=0,
            value_contribution_bps=0, profitability_contribution_bps=0,
            investment_contribution_bps=0, esg_quality_contribution_bps=0,
            low_carbon_contribution_bps=0, residual_alpha_bps=0,
            selection_effect_bps=0, allocation_effect_bps=0,
            interaction_effect_bps=0, portfolio_esg_score=0,
            benchmark_esg_score=benchmark_esg_score, esg_tilt_bps=0,
        )

    total_weight = sum(h.weight_pct for h in holdings)
    if total_weight == 0:
        total_weight = 100.0

    # Portfolio and benchmark returns
    port_ret = sum(h.weight_pct / 100.0 * h.return_pct for h in holdings)
    bench_ret = sum(h.benchmark_weight_pct / 100.0 * h.benchmark_return_pct for h in holdings)
    active_bps = (port_ret - bench_ret) * 100.0

    # Portfolio ESG score (weighted)
    port_esg = sum(h.weight_pct / total_weight * h.esg_score for h in holdings)

    # Factor exposures (simplified — real implementation would use regression)
    esg_tilt = (port_esg - benchmark_esg_score) / 100.0
    esg_contribution = esg_tilt * _FACTOR_PREMIA_BPS["esg_quality"]

    # Carbon tilt
    port_carbon = sum(h.weight_pct / total_weight * h.carbon_intensity_tco2e_m for h in holdings)
    avg_sector_carbon = 180.0  # benchmark average
    carbon_tilt = (avg_sector_carbon - port_carbon) / avg_sector_carbon
    low_carbon_contribution = carbon_tilt * _FACTOR_PREMIA_BPS["low_carbon"]

    # Simplified factor decomposition (pro-rata allocation of active return)
    total_factor_explained = esg_contribution + low_carbon_contribution
    remaining = active_bps - total_factor_explained
    # Split remaining across standard factors proportionally
    std_factors = ["market", "size", "value", "profitability", "investment"]
    factor_total = sum(_FACTOR_PREMIA_BPS[f] for f in std_factors)
    factor_contributions = {}
    for f in std_factors:
        factor_contributions[f] = remaining * (_FACTOR_PREMIA_BPS[f] / factor_total) * 0.6
    residual = remaining - sum(factor_contributions.values())

    # Brinson attribution (by sector)
    sectors = set(h.sector for h in holdings)
    selection_effect = 0.0
    allocation_effect = 0.0
    for sec in sectors:
        sec_holdings = [h for h in holdings if h.sector == sec]
        wp = sum(h.weight_pct for h in sec_holdings) / 100.0
        wb = sum(h.benchmark_weight_pct for h in sec_holdings) / 100.0
        rp = sum(h.weight_pct * h.return_pct for h in sec_holdings) / max(sum(h.weight_pct for h in sec_holdings), 0.01)
        rb = sum(h.benchmark_weight_pct * h.benchmark_return_pct for h in sec_holdings) / max(sum(h.benchmark_weight_pct for h in sec_holdings), 0.01)
        selection_effect += wp * (rp - rb)
        allocation_effect += (wp - wb) * (rb - bench_ret)

    interaction_effect = active_bps - (selection_effect * 100.0 + allocation_effect * 100.0)

    return ESGAttributionResult(
        total_return_pct=round(port_ret, 4),
        benchmark_return_pct=round(bench_ret, 4),
        active_return_bps=round(active_bps, 2),
        market_contribution_bps=round(factor_contributions.get("market", 0), 2),
        size_contribution_bps=round(factor_contributions.get("size", 0), 2),
        value_contribution_bps=round(factor_contributions.get("value", 0), 2),
        profitability_contribution_bps=round(factor_contributions.get("profitability", 0), 2),
        investment_contribution_bps=round(factor_contributions.get("investment", 0), 2),
        esg_quality_contribution_bps=round(esg_contribution, 2),
        low_carbon_contribution_bps=round(low_carbon_contribution, 2),
        residual_alpha_bps=round(residual, 2),
        selection_effect_bps=round(selection_effect * 100.0, 2),
        allocation_effect_bps=round(allocation_effect * 100.0, 2),
        interaction_effect_bps=round(interaction_effect, 2),
        portfolio_esg_score=round(port_esg, 1),
        benchmark_esg_score=benchmark_esg_score,
        esg_tilt_bps=round(esg_contribution, 2),
    )


# ═══════════════════════════════════════════════════════════════════════════
#  2. Paris Alignment Tracker
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class ParisAlignmentResult:
    """Portfolio temperature alignment result (PACTA-style)."""
    portfolio_temperature_c: float
    target_pathway: str
    target_temperature_c: float
    alignment_gap_c: float
    alignment_gap_pct: float
    aligned_weight_pct: float
    misaligned_weight_pct: float
    laggard_holdings: List[Dict]        # holdings furthest from target
    sector_temperatures: Dict[str, float]
    trajectory_years: List[int]
    trajectory_portfolio_c: List[float]
    trajectory_target_c: List[float]
    weighted_carbon_intensity: float     # tCO2e / EUR m


def calculate_paris_alignment(
    holdings: List[Holding],
    target_pathway: str = "1.5C",
    base_year: int = 2024,
) -> ParisAlignmentResult:
    """
    Compute portfolio implied temperature rise using weighted carbon intensity
    and sector decarbonisation pathways (PACTA methodology).
    """
    target_temp = _PATHWAY_TARGETS.get(target_pathway, 1.5)
    total_weight = sum(h.weight_pct for h in holdings) or 100.0

    # Weighted average carbon intensity
    waci = sum(
        (h.weight_pct / total_weight) * h.carbon_intensity_tco2e_m
        for h in holdings
    )

    # Sector-level temperature estimation
    sector_temps: Dict[str, float] = {}
    sector_weights: Dict[str, float] = {}
    for h in holdings:
        sec = h.sector if h.sector in _SBTI_SECTOR_PATHWAYS else "default"
        sector_weights.setdefault(sec, 0.0)
        sector_weights[sec] += h.weight_pct

        # Implied temperature = f(carbon intensity vs pathway)
        pathway_rate = abs(_SBTI_SECTOR_PATHWAYS.get(sec, -3.0))
        sector_avg_ci = _SECTOR_CARBON_INTENSITY.get(sec, 180.0)
        # Ratio of holding CI to sector average → temperature overshoot
        ci_ratio = h.carbon_intensity_tco2e_m / max(sector_avg_ci, 1.0)
        implied_t = target_temp + (ci_ratio - 0.5) * 1.5
        implied_t = max(1.0, min(6.0, implied_t))

        if sec not in sector_temps:
            sector_temps[sec] = 0.0
        sector_temps[sec] += h.weight_pct * implied_t

    for sec in sector_temps:
        if sector_weights[sec] > 0:
            sector_temps[sec] = round(sector_temps[sec] / sector_weights[sec], 2)

    # Portfolio temperature (weighted across sectors)
    port_temp = sum(
        (sector_weights.get(sec, 0) / total_weight) * sector_temps.get(sec, target_temp)
        for sec in sector_temps
    )
    port_temp = round(max(1.0, min(6.0, port_temp)), 2)

    alignment_gap_c = round(port_temp - target_temp, 2)
    alignment_gap_pct = round(alignment_gap_c / target_temp * 100, 1) if target_temp > 0 else 0.0

    # Identify aligned vs misaligned
    aligned_wt = 0.0
    misaligned_wt = 0.0
    laggards = []
    for h in holdings:
        sec = h.sector if h.sector in _SBTI_SECTOR_PATHWAYS else "default"
        sector_avg = _SECTOR_CARBON_INTENSITY.get(sec, 180.0)
        # Aligned if CI is below pathway-consistent threshold (50% of sector avg)
        threshold = sector_avg * 0.5
        if h.carbon_intensity_tco2e_m <= threshold:
            aligned_wt += h.weight_pct
        else:
            misaligned_wt += h.weight_pct
            overshoot = h.carbon_intensity_tco2e_m / max(threshold, 1.0)
            laggards.append({
                "security_id": h.security_id,
                "name": h.name,
                "sector": h.sector,
                "carbon_intensity": h.carbon_intensity_tco2e_m,
                "overshoot_ratio": round(overshoot, 2),
                "weight_pct": h.weight_pct,
            })

    laggards.sort(key=lambda x: x["overshoot_ratio"], reverse=True)

    # Trajectory projection (base → 2050)
    years = list(range(base_year, 2051, 5))
    port_trajectory = []
    target_trajectory = []
    for yr in years:
        elapsed = yr - base_year
        # Portfolio temperature declines at blended decarbonisation rate
        blend_rate = sum(
            (sector_weights.get(sec, 0) / total_weight) *
            abs(_SBTI_SECTOR_PATHWAYS.get(sec, -3.0))
            for sec in sector_weights
        ) / 100.0  # fractional annual rate
        port_t = port_temp - (port_temp - target_temp) * (1 - math.exp(-blend_rate * elapsed))
        port_trajectory.append(round(max(target_temp * 0.9, port_t), 2))
        # Target pathway (linear decline)
        target_t = target_temp + (3.2 - target_temp) * max(0, 1 - elapsed / (2050 - base_year))
        target_trajectory.append(round(target_t, 2))

    return ParisAlignmentResult(
        portfolio_temperature_c=port_temp,
        target_pathway=target_pathway,
        target_temperature_c=target_temp,
        alignment_gap_c=alignment_gap_c,
        alignment_gap_pct=alignment_gap_pct,
        aligned_weight_pct=round(aligned_wt / total_weight * 100, 1),
        misaligned_weight_pct=round(misaligned_wt / total_weight * 100, 1),
        laggard_holdings=laggards[:10],
        sector_temperatures=sector_temps,
        trajectory_years=years,
        trajectory_portfolio_c=port_trajectory,
        trajectory_target_c=target_trajectory,
        weighted_carbon_intensity=round(waci, 2),
    )


# ═══════════════════════════════════════════════════════════════════════════
#  3. Green Bond Screening
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class BondInput:
    """Green bond screening input."""
    bond_id: str
    issuer_name: str
    isin: str = ""
    rating: str = "BBB"
    sector: str = "default"
    use_of_proceeds: List[str] = field(default_factory=list)
    taxonomy_aligned_pct: float = 0.0       # EU Taxonomy alignment (%)
    external_review: bool = False           # SPO or CBI certification
    impact_reporting: bool = False
    dnsh_assessed: bool = False
    coupon_bps: float = 0.0
    conventional_spread_bps: float = 0.0


@dataclass
class GreenBondScreeningResult:
    """Green bond eligibility assessment."""
    bond_id: str
    issuer_name: str
    eligible: bool
    eligibility_score: float            # 0-100
    icma_gbs_aligned: bool
    eu_gbs_aligned: bool
    use_of_proceeds_valid: List[str]
    use_of_proceeds_invalid: List[str]
    taxonomy_aligned_pct: float
    greenium_bps: float                 # estimated green premium
    spread_vs_conventional_bps: float
    dnsh_flags: List[str]
    missing_criteria: List[str]


def screen_green_bonds(bonds: List[BondInput]) -> List[GreenBondScreeningResult]:
    """
    Screen bond universe against ICMA GBS criteria and EU GBS Regulation.
    Returns eligibility assessment, greenium estimate, and DNSH flags.
    """
    results = []
    for bond in bonds:
        score = 0.0
        missing = []
        dnsh_flags = []

        # Use of proceeds check
        valid_uop = [u for u in bond.use_of_proceeds if u in _ICMA_UOP_CATEGORIES]
        invalid_uop = [u for u in bond.use_of_proceeds if u not in _ICMA_UOP_CATEGORIES]

        if valid_uop:
            score += 30.0
        else:
            missing.append("No valid ICMA use-of-proceeds category identified")

        # EU Taxonomy alignment
        if bond.taxonomy_aligned_pct >= 85:
            score += 25.0
        elif bond.taxonomy_aligned_pct >= 50:
            score += 15.0
        elif bond.taxonomy_aligned_pct > 0:
            score += 5.0
        else:
            missing.append("No EU Taxonomy alignment data")

        # External review (SPO/CBI)
        if bond.external_review:
            score += 15.0
        else:
            missing.append("No external review (SPO/CBI certification)")

        # Impact reporting
        if bond.impact_reporting:
            score += 15.0
        else:
            missing.append("No post-issuance impact reporting")

        # DNSH assessment
        if bond.dnsh_assessed:
            score += 15.0
        else:
            dnsh_flags.append("DNSH assessment not completed — potential Article 17 non-compliance")
            missing.append("DNSH assessment required under EU Taxonomy Art. 17")

        # Sector-specific DNSH checks
        if bond.sector in ("oil_gas", "coal"):
            dnsh_flags.append(f"Sector '{bond.sector}' — high fossil fuel exposure, DNSH likely fails")
            score -= 20.0
        elif bond.sector in ("aviation", "shipping"):
            dnsh_flags.append(f"Sector '{bond.sector}' — assess significant harm to climate mitigation")

        score = max(0.0, min(100.0, score))

        # ICMA GBS alignment: valid UoP + external review + impact reporting
        icma_aligned = bool(valid_uop) and bond.external_review and bond.impact_reporting
        # EU GBS: ICMA + taxonomy ≥85% + DNSH
        eu_gbs_aligned = icma_aligned and bond.taxonomy_aligned_pct >= 85 and bond.dnsh_assessed

        # Greenium estimate
        greenium = _GREENIUM_BPS.get(bond.rating, _GREENIUM_BPS["default"])
        if eu_gbs_aligned:
            greenium *= 1.5  # EU GBS carries higher greenium
        elif not icma_aligned:
            greenium *= 0.3

        spread_delta = bond.conventional_spread_bps - greenium if bond.conventional_spread_bps > 0 else 0.0

        results.append(GreenBondScreeningResult(
            bond_id=bond.bond_id,
            issuer_name=bond.issuer_name,
            eligible=score >= 60.0,
            eligibility_score=round(score, 1),
            icma_gbs_aligned=icma_aligned,
            eu_gbs_aligned=eu_gbs_aligned,
            use_of_proceeds_valid=valid_uop,
            use_of_proceeds_invalid=invalid_uop,
            taxonomy_aligned_pct=bond.taxonomy_aligned_pct,
            greenium_bps=round(greenium, 1),
            spread_vs_conventional_bps=round(spread_delta, 1),
            dnsh_flags=dnsh_flags,
            missing_criteria=missing,
        ))

    return results


# ═══════════════════════════════════════════════════════════════════════════
#  4. Climate-Adjusted Spreads
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class IssuerInput:
    """Input for climate-adjusted spread calculation."""
    issuer_id: str
    name: str
    sector: str = "default"
    rating: str = "BBB"
    base_spread_bps: float = 150.0
    carbon_intensity_tco2e_m: float = 180.0
    transition_risk_score: float = 50.0     # 0-100
    revenue_from_fossils_pct: float = 0.0
    capex_green_pct: float = 0.0
    sbti_committed: bool = False


@dataclass
class ClimateSpreadResult:
    """Climate-adjusted credit spread output."""
    issuer_id: str
    name: str
    base_spread_bps: float
    climate_adjustment_bps: float
    climate_adjusted_spread_bps: float
    spread_delta_bps: float
    transition_risk_component_bps: float
    carbon_cost_component_bps: float
    stranded_asset_component_bps: float
    migration_probability_1yr: float    # 1-year downgrade probability
    migration_probability_5yr: float
    sbti_benefit_bps: float


def calculate_climate_adjusted_spreads(
    issuers: List[IssuerInput],
    carbon_price_eur: float = 80.0,
    warming_scenario: str = "2C",
) -> List[ClimateSpreadResult]:
    """
    Compute climate-adjusted credit spreads incorporating transition risk,
    carbon cost pass-through, and stranded asset probability.
    """
    results = []
    scenario_multiplier = {"1.5C": 1.5, "2C": 1.0, "3C": 0.6, "BAU": 0.3}.get(warming_scenario, 1.0)

    for iss in issuers:
        # Transition risk spread component
        spread_factor = _TRANSITION_SPREAD_FACTORS.get(iss.rating, _TRANSITION_SPREAD_FACTORS["default"])
        transition_bps = iss.transition_risk_score * spread_factor * scenario_multiplier * 0.5

        # Carbon cost component (pass-through of carbon pricing to spreads)
        sector_ci = _SECTOR_CARBON_INTENSITY.get(iss.sector, 180.0)
        carbon_cost_impact = (iss.carbon_intensity_tco2e_m / 1000.0) * carbon_price_eur
        carbon_bps = carbon_cost_impact * 0.15 * scenario_multiplier

        # Stranded asset component
        stranded_bps = 0.0
        if iss.revenue_from_fossils_pct > 30:
            stranded_bps = (iss.revenue_from_fossils_pct - 30) * 0.8 * scenario_multiplier

        # SBTi commitment benefit
        sbti_benefit = 0.0
        if iss.sbti_committed:
            sbti_benefit = 15.0 + iss.capex_green_pct * 0.3

        # Total climate adjustment
        climate_adj = transition_bps + carbon_bps + stranded_bps - sbti_benefit
        climate_adj = max(0.0, climate_adj)

        adjusted_spread = iss.base_spread_bps + climate_adj

        # Migration probability (simplified logistic model)
        # Higher climate adjustment → higher downgrade probability
        hazard_rate = climate_adj / 500.0
        migration_1yr = 1 - math.exp(-hazard_rate)
        migration_5yr = 1 - math.exp(-hazard_rate * 5)

        results.append(ClimateSpreadResult(
            issuer_id=iss.issuer_id,
            name=iss.name,
            base_spread_bps=round(iss.base_spread_bps, 1),
            climate_adjustment_bps=round(climate_adj, 1),
            climate_adjusted_spread_bps=round(adjusted_spread, 1),
            spread_delta_bps=round(climate_adj, 1),
            transition_risk_component_bps=round(transition_bps, 1),
            carbon_cost_component_bps=round(carbon_bps, 1),
            stranded_asset_component_bps=round(stranded_bps, 1),
            migration_probability_1yr=round(migration_1yr, 4),
            migration_probability_5yr=round(migration_5yr, 4),
            sbti_benefit_bps=round(sbti_benefit, 1),
        ))

    return results


# ═══════════════════════════════════════════════════════════════════════════
#  5. LP Analytics
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class InvestorProfile:
    """LP / investor profile for liquidity analysis."""
    investor_id: str
    name: str
    commitment_eur: float
    investor_type: str = "institutional"    # institutional | retail | sovereign | family_office
    redemption_notice_days: int = 30
    lock_up_remaining_months: int = 0
    historical_redemption_rate: float = 0.05  # annual redemption rate


@dataclass
class LPAnalyticsResult:
    """LP analytics and liquidity coverage output."""
    fund_aum_eur: float
    investor_count: int
    liquidity_coverage_ratio: float         # liquid assets / 30-day outflow
    investor_concentration_hhi: float       # Herfindahl-Hirschman Index (0-10000)
    top5_concentration_pct: float
    redemption_stress_30d_pct: float
    redemption_stress_90d_pct: float
    weighted_avg_lock_up_months: float
    investor_type_breakdown: Dict[str, float]
    side_pocket_recommendation: bool
    liquidity_risk_rating: str              # low | medium | high | critical
    recommendations: List[str]


def calculate_lp_analytics(
    fund_aum_eur: float,
    investors: List[InvestorProfile],
    liquid_assets_pct: float = 30.0,
    side_pocket_pct: float = 0.0,
) -> LPAnalyticsResult:
    """
    Analyse investor base concentration, liquidity coverage, and redemption
    stress scenarios for fund liquidity management.
    """
    if not investors:
        return LPAnalyticsResult(
            fund_aum_eur=fund_aum_eur, investor_count=0,
            liquidity_coverage_ratio=0, investor_concentration_hhi=0,
            top5_concentration_pct=0, redemption_stress_30d_pct=0,
            redemption_stress_90d_pct=0, weighted_avg_lock_up_months=0,
            investor_type_breakdown={}, side_pocket_recommendation=False,
            liquidity_risk_rating="critical", recommendations=["No investors — fund not operational"],
        )

    total_commitment = sum(inv.commitment_eur for inv in investors)
    if total_commitment == 0:
        total_commitment = fund_aum_eur

    # HHI concentration
    shares = [(inv.commitment_eur / total_commitment * 100) for inv in investors]
    hhi = sum(s ** 2 for s in shares)

    # Top 5 concentration
    shares_sorted = sorted(shares, reverse=True)
    top5 = sum(shares_sorted[:5])

    # Weighted average lock-up
    wa_lockup = sum(
        (inv.commitment_eur / total_commitment) * inv.lock_up_remaining_months
        for inv in investors
    )

    # Investor type breakdown
    type_breakdown: Dict[str, float] = {}
    for inv in investors:
        type_breakdown.setdefault(inv.investor_type, 0.0)
        type_breakdown[inv.investor_type] += inv.commitment_eur / total_commitment * 100.0
    type_breakdown = {k: round(v, 1) for k, v in type_breakdown.items()}

    # Redemption stress (30-day and 90-day)
    # Only investors past lock-up with notice ≤ period can redeem
    redeemable_30d = sum(
        inv.commitment_eur * inv.historical_redemption_rate * (30 / 365)
        for inv in investors
        if inv.lock_up_remaining_months == 0 and inv.redemption_notice_days <= 30
    )
    redeemable_90d = sum(
        inv.commitment_eur * inv.historical_redemption_rate * (90 / 365)
        for inv in investors
        if inv.lock_up_remaining_months <= 3 and inv.redemption_notice_days <= 90
    )

    stress_30d_pct = (redeemable_30d / fund_aum_eur * 100) if fund_aum_eur > 0 else 0
    stress_90d_pct = (redeemable_90d / fund_aum_eur * 100) if fund_aum_eur > 0 else 0

    # LCR
    liquid_eur = fund_aum_eur * (liquid_assets_pct / 100.0)
    lcr = (liquid_eur / redeemable_30d) if redeemable_30d > 0 else 10.0

    # Side pocket recommendation
    side_pocket_rec = (liquid_assets_pct - side_pocket_pct) < stress_90d_pct

    # Risk rating
    if lcr < 1.0 or hhi > 4000:
        risk_rating = "critical"
    elif lcr < 1.5 or hhi > 2500:
        risk_rating = "high"
    elif lcr < 2.5 or hhi > 1500:
        risk_rating = "medium"
    else:
        risk_rating = "low"

    # Recommendations
    recs = []
    if hhi > 2500:
        recs.append("Investor concentration HHI > 2500 — diversify investor base")
    if top5 > 60:
        recs.append(f"Top 5 investors hold {top5:.0f}% — single-investor redemption risk")
    if lcr < 1.5:
        recs.append(f"LCR {lcr:.1f}x — increase liquid asset buffer to ≥20% of AUM")
    if wa_lockup < 6:
        recs.append("Short average lock-up — consider extending terms for new commitments")
    if side_pocket_rec:
        recs.append("Consider activating side pocket for illiquid positions")

    return LPAnalyticsResult(
        fund_aum_eur=fund_aum_eur,
        investor_count=len(investors),
        liquidity_coverage_ratio=round(lcr, 2),
        investor_concentration_hhi=round(hhi, 0),
        top5_concentration_pct=round(top5, 1),
        redemption_stress_30d_pct=round(stress_30d_pct, 2),
        redemption_stress_90d_pct=round(stress_90d_pct, 2),
        weighted_avg_lock_up_months=round(wa_lockup, 1),
        investor_type_breakdown=type_breakdown,
        side_pocket_recommendation=side_pocket_rec,
        liquidity_risk_rating=risk_rating,
        recommendations=recs,
    )


# ═══════════════════════════════════════════════════════════════════════════
#  6. ESG-Constrained Optimisation
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class OptimisationConstraints:
    """Constraints for ESG-aware portfolio optimisation."""
    min_esg_score: float = 0.0              # minimum weighted ESG score
    max_carbon_intensity: float = 999.0     # tCO2e/EUR m cap
    excluded_sectors: List[str] = field(default_factory=list)
    excluded_securities: List[str] = field(default_factory=list)
    max_single_weight_pct: float = 10.0
    max_sector_weight_pct: float = 30.0
    max_tracking_error_pct: float = 3.0
    esg_tilt_strength: float = 0.5          # 0 = no tilt, 1 = max tilt


@dataclass
class OptimisationResult:
    """ESG-constrained portfolio optimisation output."""
    optimal_weights: Dict[str, float]       # security_id → weight (%)
    portfolio_return_pct: float
    portfolio_risk_pct: float               # annualised vol
    sharpe_ratio: float
    tracking_error_vs_benchmark_pct: float
    portfolio_esg_score: float
    portfolio_carbon_intensity: float
    esg_score_improvement: float            # vs equal-weight
    return_drag_bps: float                  # cost of ESG constraints
    constraints_binding: List[str]          # which constraints are active
    excluded_count: int
    sector_weights: Dict[str, float]


def optimise_esg_portfolio(
    holdings: List[Holding],
    constraints: OptimisationConstraints,
    risk_free_rate: float = 3.5,
) -> OptimisationResult:
    """
    Simple ESG-tilted portfolio optimisation using analytical mean-variance
    with ESG score weighting. Full implementation would use scipy.optimize or
    cvxpy for quadratic programming.
    """
    # Filter exclusions
    eligible = [
        h for h in holdings
        if h.sector not in constraints.excluded_sectors
        and h.security_id not in constraints.excluded_securities
    ]
    excluded_count = len(holdings) - len(eligible)

    if not eligible:
        return OptimisationResult(
            optimal_weights={}, portfolio_return_pct=0, portfolio_risk_pct=0,
            sharpe_ratio=0, tracking_error_vs_benchmark_pct=0,
            portfolio_esg_score=0, portfolio_carbon_intensity=0,
            esg_score_improvement=0, return_drag_bps=0,
            constraints_binding=["All securities excluded"],
            excluded_count=excluded_count, sector_weights={},
        )

    n = len(eligible)
    # Equal-weight baseline
    ew = 100.0 / n

    # ESG tilt: overweight high-ESG, underweight low-ESG
    esg_scores = [h.esg_score for h in eligible]
    avg_esg = sum(esg_scores) / n if n > 0 else 50.0
    tilt = constraints.esg_tilt_strength

    raw_weights = []
    for h in eligible:
        esg_tilt_factor = 1.0 + tilt * (h.esg_score - avg_esg) / 100.0
        # Carbon penalty
        carbon_penalty = 1.0
        if h.carbon_intensity_tco2e_m > constraints.max_carbon_intensity:
            carbon_penalty = 0.3
        raw_weights.append(ew * esg_tilt_factor * carbon_penalty)

    # Normalise
    total_raw = sum(raw_weights) or 1.0
    weights = [w / total_raw * 100.0 for w in raw_weights]

    # Apply single-name cap
    binding = []
    capped = False
    for i in range(len(weights)):
        if weights[i] > constraints.max_single_weight_pct:
            weights[i] = constraints.max_single_weight_pct
            capped = True
    if capped:
        binding.append("max_single_weight_pct")
        # Re-normalise
        excess = sum(weights) - 100.0
        uncapped = [i for i in range(len(weights)) if weights[i] < constraints.max_single_weight_pct]
        if uncapped and excess > 0:
            adj = excess / len(uncapped)
            for i in uncapped:
                weights[i] = max(0, weights[i] - adj)

    # Apply sector cap
    sector_wts: Dict[str, float] = {}
    for i, h in enumerate(eligible):
        sector_wts.setdefault(h.sector, 0.0)
        sector_wts[h.sector] += weights[i]

    for sec in sector_wts:
        if sector_wts[sec] > constraints.max_sector_weight_pct:
            binding.append(f"max_sector_weight_pct ({sec})")
            # Scale down proportionally
            scale = constraints.max_sector_weight_pct / sector_wts[sec]
            for i, h in enumerate(eligible):
                if h.sector == sec:
                    weights[i] *= scale

    # Final normalisation
    total_w = sum(weights) or 1.0
    weights = [w / total_w * 100.0 for w in weights]

    # Portfolio metrics
    port_ret = sum(weights[i] / 100.0 * eligible[i].return_pct for i in range(n))
    port_esg = sum(weights[i] / 100.0 * eligible[i].esg_score for i in range(n))
    port_ci = sum(weights[i] / 100.0 * eligible[i].carbon_intensity_tco2e_m for i in range(n))

    # Simplified risk (assume ~15% vol for equity, scale by concentration)
    conc = sum((w / 100.0) ** 2 for w in weights)
    port_vol = 15.0 * math.sqrt(conc * n)
    port_vol = min(40.0, max(5.0, port_vol))

    sharpe = (port_ret * 100 - risk_free_rate) / port_vol if port_vol > 0 else 0

    # Tracking error vs benchmark
    te = sum(
        ((weights[i] - eligible[i].benchmark_weight_pct) / 100.0) ** 2
        for i in range(n)
    )
    te = math.sqrt(te) * port_vol * 100
    te = min(te, 10.0)

    if te > constraints.max_tracking_error_pct:
        binding.append("max_tracking_error_pct")

    # ESG constraint check
    if port_esg < constraints.min_esg_score:
        binding.append("min_esg_score")

    # Return drag = difference vs unconstrained equal-weight return
    ew_ret = sum(h.return_pct for h in eligible) / n if n > 0 else 0
    return_drag = (ew_ret - port_ret) * 100

    # Build optimal weights dict
    opt_weights = {eligible[i].security_id: round(weights[i], 2) for i in range(n)}

    # Sector weights (recalculated)
    final_sector_wts: Dict[str, float] = {}
    for i, h in enumerate(eligible):
        final_sector_wts.setdefault(h.sector, 0.0)
        final_sector_wts[h.sector] += weights[i]
    final_sector_wts = {k: round(v, 1) for k, v in final_sector_wts.items()}

    return OptimisationResult(
        optimal_weights=opt_weights,
        portfolio_return_pct=round(port_ret, 4),
        portfolio_risk_pct=round(port_vol, 2),
        sharpe_ratio=round(sharpe, 3),
        tracking_error_vs_benchmark_pct=round(te, 2),
        portfolio_esg_score=round(port_esg, 1),
        portfolio_carbon_intensity=round(port_ci, 1),
        esg_score_improvement=round(port_esg - avg_esg, 1),
        return_drag_bps=round(return_drag, 1),
        constraints_binding=binding,
        excluded_count=excluded_count,
        sector_weights=final_sector_wts,
    )


# ═══════════════════════════════════════════════════════════════════════════
#  Convenience: get all reference data
# ═══════════════════════════════════════════════════════════════════════════

def get_am_reference_data() -> dict:
    """Return all reference data used by the AM Engine."""
    return {
        "factor_premia_bps": _FACTOR_PREMIA_BPS,
        "sbti_sector_pathways_pct_pa": _SBTI_SECTOR_PATHWAYS,
        "icma_uop_categories": sorted(_ICMA_UOP_CATEGORIES),
        "sector_carbon_intensity_tco2e_m": _SECTOR_CARBON_INTENSITY,
        "pathway_targets_c": _PATHWAY_TARGETS,
        "transition_spread_factors_bps": _TRANSITION_SPREAD_FACTORS,
        "greenium_bps_by_rating": _GREENIUM_BPS,
        "sources": [
            "Fama-French 5-Factor Model (2015) + Pastor-Stambaugh ESG Extension",
            "ICMA Green Bond Principles (2021)",
            "EU GBS Regulation 2023/2631",
            "Paris Agreement Capital Transition Assessment (PACTA)",
            "SBTi Sector Decarbonisation Approach",
            "Markowitz Mean-Variance Optimisation (1952)",
        ],
    }
