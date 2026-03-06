"""
Agriculture Climate Risk Calculator
Aligned with: IPCC AR6 WGI/WGII | FAO GAEZ v4 | WRI Aqueduct 4.0 | EU 2023/1115 (EUDR)
              IPCC SR15 Ch.3 | GHG Protocol Scope 3 Cat. 1 & 11 | Verra VM0042

Calculates:
  1. Crop yield risk — projected yield change under climate scenarios (IPCC AR6 regional coefficients)
  2. EUDR compliance status — EU Deforestation Regulation risk score (Regulation EU 2023/1115)
  3. Soil carbon sequestration potential — regenerative agriculture credit estimation
  4. Water stress exposure — WRI Aqueduct 4.0 stress categories
  5. Overall financial risk summary (revenue-at-risk, adaptation capex)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ── Crop yield change coefficients under climate scenarios ─────────────────────
# Unit: fractional change per 1°C of global mean temperature increase vs. 2000 baseline
# Source: IPCC AR6 WGII Ch.5 Table 5.2 (weighted average across major growing regions)
# Negative = yield loss, positive = mild benefit in some high-latitude regions
_CROP_YIELD_SENSITIVITY: Dict[str, float] = {
    "wheat":        -0.060,   # -6% per °C global warming
    "maize":        -0.072,   # -7.2% per °C
    "rice":         -0.030,   # -3% per °C
    "soybean":      -0.056,   # -5.6% per °C
    "sugarcane":    -0.040,
    "palm_oil":     -0.025,
    "cocoa":        -0.045,
    "coffee":       -0.055,
    "cotton":       -0.035,
    "barley":       -0.050,
    "sorghum":       0.010,   # drought-tolerant — slight benefit at 1°C
    "cassava":       0.005,
    "potato":       -0.030,
    "vegetables":   -0.080,   # high sensitivity to heat stress
    "fruit_tree":   -0.040,
    "livestock":    -0.035,   # indirect via feed crop + heat stress
    "mixed_farming":-0.045,
    "unknown":      -0.050,
}

# ── Scenario temperature deltas by horizon year ──────────────────────
# Global mean temperature anomaly vs. 2000 baseline, under each scenario
# Source: IPCC AR6 SPM Table SPM.1 (median values)
_TEMP_DELTA: Dict[str, Dict[int, float]] = {
    "1.5C": {2030: 0.5, 2040: 0.8, 2050: 1.1, 2060: 1.2, 2070: 1.4},
    "2C":   {2030: 0.6, 2040: 1.0, 2050: 1.5, 2060: 1.8, 2070: 2.0},
    "3C":   {2030: 0.7, 2040: 1.2, 2050: 2.0, 2060: 2.5, 2070: 3.0},
    "BAU":  {2030: 0.8, 2040: 1.4, 2050: 2.3, 2060: 3.0, 2070: 3.8},
}

# ── EUDR commodity risk tiers ──────────────────────────────────────
# Annex I of EU Regulation 2023/1115 lists 7 commodities + derived products
_EUDR_IN_SCOPE_COMMODITIES = {
    "soybean", "beef", "palm_oil", "cocoa", "coffee", "wood", "rubber",
}
# Country risk classification (simplified — EC will publish full list)
_EUDR_COUNTRY_RISK: Dict[str, str] = {
    "BRA": "high", "IDN": "high", "MYS": "high", "COD": "high",
    "ARG": "high", "COL": "standard", "PER": "standard",
    "CIV": "standard", "GHA": "standard", "CMR": "standard",
    "ETH": "standard", "IND": "low", "CHN": "low",
    "USA": "low",  "AUS": "low",  "CAN": "low",
    "DEU": "low",  "FRA": "low",  "GBR": "low",
}

# ── WRI Aqueduct water stress categories ───────────────────────────
_WATER_STRESS_SCORE: Dict[str, float] = {
    "low":           1.0,
    "low_medium":    2.0,
    "medium_high":   3.0,
    "high":          4.0,
    "extremely_high":5.0,
    "arid_low":      3.5,  # arid but low demand
}

# ── Soil carbon sequestration potential by farm type ──────────────────
# Unit: tCO2e per hectare per year, under optimistic regenerative practices
# Source: IPCC AR6 WGIII Ch.7 / Verra VM0042 Methodology
_SOIL_SEQ_POTENTIAL: Dict[str, float] = {
    "arable":      0.8,
    "livestock":   1.2,  # improved grassland management
    "mixed":       0.9,
    "horticulture":0.5,
    "aquaculture": 0.2,
    "forestry":    3.5,  # reforestation / afforestation
    "agribusiness":0.3,
    "unknown":     0.6,
}


@dataclass
class AgricultureRiskInput:
    entity_id: str
    entity_name: str
    country_iso: str               # ISO 3166-1 alpha-3
    farm_type: str                 # arable | livestock | mixed | horticulture | forestry | agribusiness
    primary_crop: str              # wheat | maize | soybean | palm_oil | ...
    total_area_ha: float
    annual_revenue_eur: float

    # EUDR
    eudr_commodities: List[str] = field(default_factory=list)
    geolocation_provided: bool = False
    supply_chain_traced: bool = False
    due_diligence_complete: bool = False

    # Water
    water_stress_level: str = "medium_high"  # WRI Aqueduct category
    irrigation_dependency_pct: float = 30.0  # % of water from irrigation

    # Current performance
    current_yield_t_ha: Optional[float] = None
    current_soil_carbon_t_ha: Optional[float] = None
    organic_certified: bool = False
    regenerative_practices: bool = False


@dataclass
class AgricultureRiskResult:
    entity_id: str
    entity_name: str
    scenario: str
    horizon_year: int

    # Yield risk
    temperature_delta_c: float
    yield_sensitivity_pct_per_c: float
    projected_yield_change_pct: float
    yield_at_risk_t_ha: float
    crop_failure_probability: float    # annual probability 0-1

    # EUDR compliance
    eudr_in_scope: bool
    eudr_country_risk: str
    eudr_compliance_score: float       # 0-100 (higher = more compliant)
    eudr_status: str                   # compliant | at_risk | non_compliant
    eudr_required_actions: List[str]

    # Soil carbon
    current_soil_carbon_t_ha: float
    sequestration_potential_tco2_ha_yr: float
    total_sequestration_potential_tco2_yr: float
    carbon_credit_value_eur: float     # at EUR 65/tCO2e (EUA reference)
    regenerative_score: float          # 0-100

    # Water
    water_stress_score: float          # 1-5
    water_cost_risk_score: float       # 0-100
    water_risk_revenue_impact_pct: float

    # Financial summary
    revenue_at_risk_pct: float
    revenue_at_risk_eur: float
    adaptation_capex_eur: float        # estimated adaptation investment needed

    methodology_ref: str
    warnings: List[str]


def calculate_agriculture_risk(
    inp: AgricultureRiskInput,
    scenario: str = "2C",
    horizon_year: int = 2050,
) -> AgricultureRiskResult:
    warnings: list[str] = []

    # ── 1. Yield risk ─────────────────────────────────────────────────────────
    temp_deltas = _TEMP_DELTA.get(scenario, _TEMP_DELTA["2C"])
    closest_year = min(temp_deltas.keys(), key=lambda y: abs(y - horizon_year))
    temp_delta = temp_deltas[closest_year]

    crop_key = inp.primary_crop.lower().replace(" ", "_").replace("-", "_")
    sensitivity = _CROP_YIELD_SENSITIVITY.get(crop_key, _CROP_YIELD_SENSITIVITY["unknown"])
    if crop_key not in _CROP_YIELD_SENSITIVITY:
        warnings.append(f"Crop '{inp.primary_crop}' not in reference table; using generic sensitivity")

    # Yield change = sensitivity × ΔT; organic and regenerative practices reduce exposure by 20%
    mitigation_factor = 0.80 if (inp.organic_certified or inp.regenerative_practices) else 1.0
    yield_change_pct = sensitivity * temp_delta * mitigation_factor * 100.0

    yield_at_risk = abs(yield_change_pct / 100.0) * (inp.current_yield_t_ha or 5.0) * inp.total_area_ha

    # Crop failure probability — simplified logistic based on yield loss magnitude
    abs_loss = abs(yield_change_pct)
    crop_fail_prob = min(0.5, 0.02 + abs_loss * 0.008)

    # ── 2. EUDR compliance ────────────────────────────────────────────────
    eudr_in_scope = bool(
        set(c.lower() for c in inp.eudr_commodities) & _EUDR_IN_SCOPE_COMMODITIES
        or inp.primary_crop.lower() in _EUDR_IN_SCOPE_COMMODITIES
    )
    country_risk = _EUDR_COUNTRY_RISK.get(inp.country_iso.upper(), "standard")

    eudr_score = 100.0
    required_actions: list[str] = []

    if eudr_in_scope:
        if not inp.geolocation_provided:
            eudr_score -= 30.0
            required_actions.append("Submit plot-level geolocation coordinates (Article 9.1.d)")
        if not inp.supply_chain_traced:
            eudr_score -= 25.0
            required_actions.append("Establish supply chain traceability to farm level (Article 9.1.b)")
        if not inp.due_diligence_complete:
            eudr_score -= 25.0
            required_actions.append("Complete annual due diligence statement (Article 4)")
        if country_risk == "high":
            eudr_score -= 15.0
            required_actions.append("Enhanced due diligence required for high-risk country (Article 10)")
        elif country_risk == "standard":
            eudr_score -= 5.0

    eudr_score = max(0.0, eudr_score)
    if not eudr_in_scope:
        eudr_status = "not_in_scope"
    elif eudr_score >= 80:
        eudr_status = "compliant"
    elif eudr_score >= 50:
        eudr_status = "at_risk"
    else:
        eudr_status = "non_compliant"
        warnings.append("EUDR non-compliance risk — potential market access restriction in EU from 2025")

    # ── 3. Soil carbon ────────────────────────────────────────────────────────
    farm_key = inp.farm_type.lower().replace(" ", "_")
    base_seq = _SOIL_SEQ_POTENTIAL.get(farm_key, _SOIL_SEQ_POTENTIAL["unknown"])
    regen_multiplier = 1.4 if inp.regenerative_practices else 1.0
    seq_potential     = base_seq * regen_multiplier
    total_seq_yr      = seq_potential * inp.total_area_ha
    # Carbon credit at EUR 65/tCO2e (EU ETS reference, conservative for nature credits)
    credit_value      = total_seq_yr * 65.0

    regen_score = 40.0
    if inp.organic_certified:      regen_score += 25.0
    if inp.regenerative_practices: regen_score += 25.0
    if inp.water_stress_level in ("low", "low_medium"): regen_score += 10.0
    regen_score = min(100.0, regen_score)

    # ── 4. Water stress ───────────────────────────────────────────────────────
    ws_score = _WATER_STRESS_SCORE.get(inp.water_stress_level.lower(), 3.0)
    # Water cost risk: blend of stress level and irrigation dependency
    water_cost_risk = (ws_score / 5.0) * (inp.irrigation_dependency_pct / 100.0) * 100.0
    # Revenue impact from water scarcity under scenario
    water_rev_impact = water_cost_risk * 0.30 * (1 + (temp_delta - 1.0) * 0.1)
    water_rev_impact = min(water_rev_impact, 40.0)

    if ws_score >= 4.0 and inp.irrigation_dependency_pct > 50:
        warnings.append("High water stress + irrigation dependency — significant revenue risk")

    # ── 5. Financial summary ──────────────────────────────────────────────────
    # Revenue at risk = yield loss + water cost risk (capped)
    rev_at_risk_pct = min(80.0, max(0.0, abs(yield_change_pct) * 0.6 + water_rev_impact * 0.4))
    rev_at_risk_eur = inp.annual_revenue_eur * rev_at_risk_pct / 100.0

    # Adaptation capex: irrigation upgrade, drought-resistant seeds, soil management
    adapt_capex = inp.total_area_ha * 350.0  # EUR 350/ha baseline
    if inp.water_stress_level in ("high", "extremely_high"):
        adapt_capex *= 1.8
    if inp.primary_crop in ("vegetables", "fruit_tree", "horticulture"):
        adapt_capex *= 1.5  # horticultural crops need more expensive adaptation

    return AgricultureRiskResult(
        entity_id                         = inp.entity_id,
        entity_name                       = inp.entity_name,
        scenario                          = scenario,
        horizon_year                      = horizon_year,
        temperature_delta_c               = round(temp_delta, 2),
        yield_sensitivity_pct_per_c       = round(sensitivity * 100, 2),
        projected_yield_change_pct        = round(yield_change_pct, 2),
        yield_at_risk_t_ha                = round(yield_at_risk, 2),
        crop_failure_probability          = round(crop_fail_prob, 4),
        eudr_in_scope                     = eudr_in_scope,
        eudr_country_risk                 = country_risk,
        eudr_compliance_score             = round(eudr_score, 1),
        eudr_status                       = eudr_status,
        eudr_required_actions             = required_actions,
        current_soil_carbon_t_ha          = inp.current_soil_carbon_t_ha or 0.0,
        sequestration_potential_tco2_ha_yr= round(seq_potential, 3),
        total_sequestration_potential_tco2_yr = round(total_seq_yr, 2),
        carbon_credit_value_eur           = round(credit_value, 0),
        regenerative_score                = round(regen_score, 1),
        water_stress_score                = round(ws_score, 1),
        water_cost_risk_score             = round(water_cost_risk, 1),
        water_risk_revenue_impact_pct     = round(water_rev_impact, 2),
        revenue_at_risk_pct               = round(rev_at_risk_pct, 2),
        revenue_at_risk_eur               = round(rev_at_risk_eur, 0),
        adaptation_capex_eur              = round(adapt_capex, 0),
        methodology_ref = (
            "IPCC AR6 WGII Ch.5 (crop yield) | FAO GAEZ v4 | "
            "WRI Aqueduct 4.0 | EU Regulation 2023/1115 (EUDR) | "
            "Verra VM0042 (soil carbon) | GHG Protocol Scope 3 Cat.1"
        ),
        warnings = warnings,
    )


def get_reference_data() -> dict:
    return {
        "crop_yield_sensitivity_pct_per_c": {
            k: round(v * 100, 2) for k, v in _CROP_YIELD_SENSITIVITY.items()
        },
        "temperature_deltas_by_scenario": _TEMP_DELTA,
        "eudr_in_scope_commodities": sorted(_EUDR_IN_SCOPE_COMMODITIES),
        "eudr_country_risk": _EUDR_COUNTRY_RISK,
        "water_stress_scores": _WATER_STRESS_SCORE,
        "soil_sequestration_t_co2_ha_yr": _SOIL_SEQ_POTENTIAL,
        "carbon_price_eur_tco2e_reference": 65.0,
        "sources": [
            "IPCC AR6 WGII Chapter 5 — Food, Fibre and Other Ecosystem Products",
            "FAO GAEZ v4 — Global Agro-Ecological Zones",
            "WRI Aqueduct 4.0 — Water Risk Atlas",
            "EU Regulation 2023/1115 — Deforestation Regulation (EUDR)",
            "Verra VM0042 — Methodology for Improved Agricultural Land Management",
        ],
    }
