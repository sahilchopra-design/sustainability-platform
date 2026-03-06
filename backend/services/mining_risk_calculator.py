"""
Mining & Extractives Climate Risk Calculator
Aligned with: GISTM 2020 (Global Industry Standard on Tailings Management) /
              WRI Aqueduct 4.0 / IPCC AR6 / IEA Critical Minerals 2023 /
              UN Global Compact FPIC / GHG Protocol Scope 1-3 Extractive Industries

Calculates:
  1. Tailings facility risk (GISTM consequence class + failure probability)
  2. Water intensity and water-related operational risk
  3. Mine closure cost and provision coverage assessment
  4. Community / FPIC social risk score
  5. Critical minerals supply chain security (IEA CRM list)
  6. Transition demand exposure (EV battery, renewable energy minerals)
  7. Climate-adjusted carbon cost exposure (Scope 1+2 at modelled carbon price)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ── Carbon price by scenario (EUR/tCO2e) at horizon years
# Source: NGFS Phase 4 scenarios (IIASA REMIND-MAgPIE)
_CARBON_PRICE_EUR: Dict[str, Dict[int, float]] = {
    "1.5C": {2030: 100, 2040: 200, 2050: 350},
    "2C":   {2030:  70, 2040: 120, 2050: 200},
    "3C":   {2030:  30, 2040:  50, 2050:  75},
    "BAU":  {2030:  15, 2040:  20, 2050:  25},
}

# ── GISTM consequence class definitions
# Source: GISTM 2020, Table 1 -- Consequence Classification
_GISTM_CONSEQUENCE = {
    "EXTREME":   {"min_safety_factor": 1.50, "review_frequency_yr": 1,  "failure_prob_annual": 0.005},
    "VERY_HIGH": {"min_safety_factor": 1.40, "review_frequency_yr": 2,  "failure_prob_annual": 0.003},
    "HIGH":      {"min_safety_factor": 1.30, "review_frequency_yr": 3,  "failure_prob_annual": 0.001},
    "LOW":       {"min_safety_factor": 1.20, "review_frequency_yr": 5,  "failure_prob_annual": 0.0003},
}

# ── GISTM compliance level -> failure probability adjustment factor
# Leading practice reduces failure prob substantially
_GISTM_COMPLIANCE_FACTOR = {
    "non_compliant": 2.5,
    "developing":    1.5,
    "advanced":      1.0,
    "leading":       0.5,
}

# ── IEA Critical Raw Materials list + supply concentration (HHI proxy)
# Source: IEA Critical Minerals Market Review 2023
_CRITICAL_MINERALS_HHI: Dict[str, float] = {
    "lithium":    0.52,   # highly concentrated — Australia + Chile
    "cobalt":     0.72,   # very concentrated — DRC dominant
    "nickel":     0.28,
    "manganese":  0.30,
    "graphite":   0.70,   # China dominant
    "rare_earth": 0.85,
    "platinum_group": 0.55,
    "tungsten":   0.75,
    "indium":     0.68,
    "gallium":    0.80,
    "germanium":  0.70,
    "copper":     0.15,   # more diversified
    "zinc":       0.14,
    "bauxite":    0.18,
    "iron_ore":   0.12,
    "gold":       0.10,
    "silver":     0.13,
    "coal":       0.08,
    "uranium":    0.25,
    "other":      0.20,
}

# ── EV / Renewable energy demand sensitivity by commodity
# % of current demand attributable to clean energy transition by 2030 (IEA NZE)
_TRANSITION_DEMAND_EXPOSURE: Dict[str, float] = {
    "lithium":    0.90,
    "cobalt":     0.75,
    "nickel":     0.60,
    "manganese":  0.55,
    "graphite":   0.85,
    "rare_earth": 0.45,
    "copper":     0.35,
    "platinum_group": 0.30,
    "tungsten":   0.20,
    "iron_ore":   0.10,
    "coal":      -0.80,  # negative = transition risk (demand destruction)
    "uranium":    0.20,
    "zinc":       0.15,
    "gold":       0.05,
    "silver":     0.25,
    "bauxite":    0.10,
    "other":      0.10,
}

# ── Water intensity benchmarks (ML per kt ore processed)
# Source: ICMM Water Stewardship Framework 2014 / industry benchmarks
_WATER_INTENSITY_BENCHMARK_ML_KT: Dict[str, float] = {
    "copper":   0.40,
    "gold":     0.80,
    "iron_ore": 0.15,
    "coal":     0.12,
    "lithium":  1.20,
    "cobalt":   0.60,
    "nickel":   0.55,
    "bauxite":  0.25,
    "zinc":     0.30,
    "uranium":  1.50,
    "other":    0.35,
}


@dataclass
class MiningRiskInput:
    entity_id: str
    entity_name: str
    country_iso: str
    primary_commodity: str
    mine_type: str                        # open_pit | underground | in_situ_leach | placer
    annual_production_kt: float           # thousand tonnes per year
    annual_revenue_eur: float
    scope1_tco2e: float = 0.0             # direct emissions
    scope2_tco2e: float = 0.0             # indirect emissions

    # Tailings
    tailings_facility_count: int = 0
    gistm_consequence_class: str = "HIGH"   # EXTREME | VERY_HIGH | HIGH | LOW
    gistm_compliance_level: str = "advanced" # non_compliant | developing | advanced | leading
    tailings_closure_liability_eur: float = 0.0

    # Water
    water_use_ml_yr: Optional[float] = None
    water_stress_index: float = 2.5         # WRI Aqueduct 0-5
    water_recycling_rate: float = 0.35      # 35% recycled
    acid_mine_drainage_risk: str = "medium" # low | medium | high | critical

    # Closure
    mine_reserve_life_years: int = 20
    full_closure_cost_eur: float = 0.0
    closure_provision_eur: float = 0.0

    # Social
    fpic_status: str = "not_assessed"       # obtained | partially_obtained | not_obtained
    community_consent_score: float = 50.0   # 0-100
    modern_slavery_risk: str = "medium"     # low | medium | high

    # Critical minerals
    reserve_life_years: Optional[int] = None


@dataclass
class MiningRiskResult:
    entity_id: str
    entity_name: str
    scenario: str
    horizon_year: int

    # Tailings risk
    tailings_failure_probability: float   # annual
    tailings_consequence_class: str
    gistm_compliance_level: str
    tailings_liability_eur: float
    tailings_risk_score: float            # 0-100 (higher = more risk)

    # Water
    water_intensity_ml_kt: float
    water_intensity_vs_benchmark: str     # below | at | above | significantly_above
    water_stress_index: float
    acid_mine_drainage: str
    water_risk_score: float               # 0-100

    # Closure
    mine_reserve_life_years: int
    closure_cost_eur: float
    closure_provision_eur: float
    provision_coverage_pct: float
    closure_funding_gap_eur: float

    # Social / FPIC
    fpic_status: str
    community_consent_score: float
    social_risk_score: float              # 0-100 (higher = more risk)

    # Critical minerals
    is_critical_mineral: bool
    supply_chain_hhi: float               # Herfindahl-Hirschman Index 0-1
    geopolitical_risk_score: float        # 0-100
    ev_demand_exposure_pct: float         # % of demand from clean transition

    # Transition / stranding
    transition_demand_sensitivity: float  # -1 to +1 (positive = transition benefit)
    stranding_risk: str                   # low | medium | high | critical
    stranded_value_eur: float

    # Carbon cost
    carbon_price_eur_tco2: float
    scope12_tco2e: float
    carbon_cost_exposure_eur: float

    # Overall
    overall_risk_score: float            # 0-100
    revenue_at_risk_pct: float
    adaptation_capex_eur: float

    methodology_ref: str
    warnings: List[str]


def calculate_mining_risk(
    inp: MiningRiskInput,
    scenario: str = "2C",
    horizon_year: int = 2050,
) -> MiningRiskResult:
    warnings: list[str] = []

    # ── Carbon price
    c_prices = _CARBON_PRICE_EUR.get(scenario, _CARBON_PRICE_EUR["2C"])
    closest_yr = min(c_prices.keys(), key=lambda y: abs(y - horizon_year))
    carbon_price = c_prices[closest_yr]
    scope12 = inp.scope1_tco2e + inp.scope2_tco2e
    carbon_exposure = scope12 * carbon_price

    # ── Tailings risk
    cc = inp.gistm_consequence_class.upper()
    cc_data = _GISTM_CONSEQUENCE.get(cc, _GISTM_CONSEQUENCE["HIGH"])
    compliance_factor = _GISTM_COMPLIANCE_FACTOR.get(
        inp.gistm_compliance_level.lower(), 1.0
    )
    failure_prob = cc_data["failure_prob_annual"] * compliance_factor * max(1, inp.tailings_facility_count)
    failure_prob = min(failure_prob, 0.10)

    # Tailings risk score (0-100)
    tail_risk = failure_prob * 1000  # scale: 0.01 failure_prob → 10 score
    if cc == "EXTREME": tail_risk *= 2.0
    elif cc == "VERY_HIGH": tail_risk *= 1.5
    tail_risk = min(100.0, tail_risk)

    if cc in ("EXTREME", "VERY_HIGH") and inp.gistm_compliance_level == "non_compliant":
        warnings.append("GISTM non-compliant EXTREME/VERY_HIGH facility — immediate remediation required")

    # ── Water intensity
    commodity_key = inp.primary_commodity.lower().replace(" ", "_")
    benchmark_ml_kt = _WATER_INTENSITY_BENCHMARK_ML_KT.get(commodity_key, 0.35)
    actual_ml_kt = (
        inp.water_use_ml_yr / inp.annual_production_kt
        if inp.water_use_ml_yr and inp.annual_production_kt > 0
        else benchmark_ml_kt
    )
    ratio = actual_ml_kt / benchmark_ml_kt if benchmark_ml_kt > 0 else 1.0
    if ratio < 0.8:
        intensity_vs_benchmark = "below"
    elif ratio <= 1.2:
        intensity_vs_benchmark = "at"
    elif ratio <= 2.0:
        intensity_vs_benchmark = "above"
    else:
        intensity_vs_benchmark = "significantly_above"
        warnings.append("Water intensity significantly above sector benchmark — WRI Aqueduct water stewardship required")

    water_risk = (inp.water_stress_index / 5.0) * 50 + (ratio - 1.0) * 10
    if inp.acid_mine_drainage_risk in ("high", "critical"):
        water_risk += 20
    water_risk = max(0.0, min(100.0, water_risk))

    # ── Closure provisions
    closure_cost = inp.full_closure_cost_eur
    if closure_cost == 0:
        # Estimate: EUR 8,000 per kt annual production for open pit
        factor = {"open_pit": 8000, "underground": 12000, "in_situ_leach": 5000, "placer": 3000}
        closure_cost = inp.annual_production_kt * factor.get(inp.mine_type, 8000)

    prov_coverage = (inp.closure_provision_eur / closure_cost * 100.0) if closure_cost > 0 else 0.0
    funding_gap   = max(0.0, closure_cost - inp.closure_provision_eur)

    if prov_coverage < 50:
        warnings.append(f"Closure provision only {prov_coverage:.0f}% funded — regulatory/reputational risk")

    # ── Social risk
    social_risk = 100.0 - inp.community_consent_score
    if inp.fpic_status == "not_obtained":
        social_risk = min(100.0, social_risk + 30.0)
        warnings.append("FPIC not obtained — project may face legal challenges / operational suspension")
    elif inp.fpic_status in ("not_assessed", "partially_obtained"):
        social_risk = min(100.0, social_risk + 15.0)
    if inp.modern_slavery_risk == "high":
        social_risk = min(100.0, social_risk + 10.0)

    # ── Critical minerals
    is_critical = commodity_key in _CRITICAL_MINERALS_HHI and commodity_key not in (
        "coal", "iron_ore", "bauxite", "zinc", "gold", "silver"
    )
    hhi = _CRITICAL_MINERALS_HHI.get(commodity_key, 0.20)
    geo_risk = hhi * 100.0  # simplified proxy

    trans_demand = _TRANSITION_DEMAND_EXPOSURE.get(commodity_key, 0.10)
    ev_pct = max(0.0, trans_demand) * 100.0

    # ── Stranding risk
    if trans_demand < -0.5:
        stranding_risk = "critical"
        stranded_value = inp.annual_revenue_eur * abs(trans_demand) * inp.mine_reserve_life_years * 0.15
    elif trans_demand < 0:
        stranding_risk = "high"
        stranded_value = inp.annual_revenue_eur * abs(trans_demand) * inp.mine_reserve_life_years * 0.10
    elif commodity_key == "coal" and scenario in ("1.5C", "2C"):
        stranding_risk = "critical"
        stranded_value = inp.annual_revenue_eur * inp.mine_reserve_life_years * 0.20
        warnings.append("Coal assets face stranding risk under 1.5C/2C scenarios — IEA NZE requires no new coal mines")
    else:
        stranding_risk = "low"
        stranded_value = 0.0

    # ── Overall risk
    overall_risk = (
        tail_risk   * 0.25 +
        water_risk  * 0.20 +
        social_risk * 0.20 +
        geo_risk    * 0.15 +
        (100.0 if stranding_risk == "critical" else 50.0 if stranding_risk == "high" else 0.0) * 0.20
    )

    rev_at_risk_pct = min(80.0, overall_risk * 0.6 + (carbon_exposure / inp.annual_revenue_eur * 100 if inp.annual_revenue_eur else 0) * 0.4)
    adapt_capex = closure_cost * 0.05 + inp.annual_production_kt * 500

    return MiningRiskResult(
        entity_id                    = inp.entity_id,
        entity_name                  = inp.entity_name,
        scenario                     = scenario,
        horizon_year                 = horizon_year,
        tailings_failure_probability = round(failure_prob, 6),
        tailings_consequence_class   = cc,
        gistm_compliance_level       = inp.gistm_compliance_level,
        tailings_liability_eur       = inp.tailings_closure_liability_eur,
        tailings_risk_score          = round(tail_risk, 1),
        water_intensity_ml_kt        = round(actual_ml_kt, 4),
        water_intensity_vs_benchmark = intensity_vs_benchmark,
        water_stress_index           = inp.water_stress_index,
        acid_mine_drainage           = inp.acid_mine_drainage_risk,
        water_risk_score             = round(water_risk, 1),
        mine_reserve_life_years      = inp.mine_reserve_life_years,
        closure_cost_eur             = round(closure_cost, 0),
        closure_provision_eur        = inp.closure_provision_eur,
        provision_coverage_pct       = round(prov_coverage, 2),
        closure_funding_gap_eur      = round(funding_gap, 0),
        fpic_status                  = inp.fpic_status,
        community_consent_score      = inp.community_consent_score,
        social_risk_score            = round(social_risk, 1),
        is_critical_mineral          = is_critical,
        supply_chain_hhi             = round(hhi, 3),
        geopolitical_risk_score      = round(geo_risk, 1),
        ev_demand_exposure_pct       = round(ev_pct, 1),
        transition_demand_sensitivity= round(trans_demand, 3),
        stranding_risk               = stranding_risk,
        stranded_value_eur           = round(stranded_value, 0),
        carbon_price_eur_tco2        = carbon_price,
        scope12_tco2e                = round(scope12, 2),
        carbon_cost_exposure_eur     = round(carbon_exposure, 0),
        overall_risk_score           = round(overall_risk, 1),
        revenue_at_risk_pct          = round(rev_at_risk_pct, 2),
        adaptation_capex_eur         = round(adapt_capex, 0),
        methodology_ref = (
            "GISTM 2020 | WRI Aqueduct 4.0 | IPCC AR6 | "
            "IEA Critical Minerals 2023 | NGFS Phase 4 | GHG Protocol"
        ),
        warnings = warnings,
    )


def get_reference_data() -> dict:
    return {
        "critical_minerals_hhi":         _CRITICAL_MINERALS_HHI,
        "transition_demand_sensitivity":  _TRANSITION_DEMAND_EXPOSURE,
        "water_intensity_benchmarks":     _WATER_INTENSITY_BENCHMARK_ML_KT,
        "carbon_price_by_scenario":       _CARBON_PRICE_EUR,
        "gistm_consequence_classes":      _GISTM_CONSEQUENCE,
        "sources": [
            "GISTM — Global Industry Standard on Tailings Management (2020)",
            "WRI Aqueduct 4.0 — Water Risk Atlas",
            "IEA Critical Minerals Market Review 2023",
            "NGFS Phase 4 scenarios — carbon price trajectories",
            "IPCC AR6 WGIII Chapter 11 — Mining",
            "UN Global Compact — Free, Prior and Informed Consent (FPIC)",
        ],
    }
