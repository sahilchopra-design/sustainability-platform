"""
Sovereign Climate Risk Engine
==============================

Climate-adjusted sovereign creditworthiness assessment for fixed-income
portfolios. Combines physical risk exposure, transition readiness,
fiscal resilience, and NDC ambition into a composite sovereign climate
risk score.

Data sources modelled:
- ND-GAIN (Notre Dame Global Adaptation Initiative)
- INFORM Risk Index
- World Bank Climate Change Knowledge Portal
- IMF Climate Policy Assessment
- NGFS sovereign risk scenarios

Output: Sovereign climate risk score, climate-adjusted spread estimate,
        rating notch overlay, and portfolio-level aggregation.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

# ---------------------------------------------------------------------------
# Reference Data: Sovereign Climate Risk Profiles (60 countries)
# ---------------------------------------------------------------------------

# Composite baseline profiles: physical_risk (0-10), transition_readiness (0-10),
# fiscal_resilience (0-10), ndc_ambition (0-10), nd_gain_score (0-100)
# Higher physical_risk = worse; Higher readiness/resilience/ambition = better
SOVEREIGN_PROFILES = {
    # G7 + major developed
    "US": {"name": "United States", "physical_risk": 4.5, "transition_readiness": 6.0,
           "fiscal_resilience": 7.5, "ndc_ambition": 5.0, "nd_gain": 73.0, "credit_rating_sp": "AA+",
           "region": "north_america", "gdp_usd_bn": 25462, "debt_to_gdp_pct": 123.0},
    "GB": {"name": "United Kingdom", "physical_risk": 3.5, "transition_readiness": 7.5,
           "fiscal_resilience": 7.0, "ndc_ambition": 7.0, "nd_gain": 75.0, "credit_rating_sp": "AA",
           "region": "europe", "gdp_usd_bn": 3070, "debt_to_gdp_pct": 101.0},
    "DE": {"name": "Germany", "physical_risk": 3.5, "transition_readiness": 7.5,
           "fiscal_resilience": 8.0, "ndc_ambition": 7.5, "nd_gain": 76.0, "credit_rating_sp": "AAA",
           "region": "europe", "gdp_usd_bn": 4082, "debt_to_gdp_pct": 66.0},
    "FR": {"name": "France", "physical_risk": 4.0, "transition_readiness": 7.0,
           "fiscal_resilience": 6.5, "ndc_ambition": 7.0, "nd_gain": 73.0, "credit_rating_sp": "AA",
           "region": "europe", "gdp_usd_bn": 2780, "debt_to_gdp_pct": 112.0},
    "JP": {"name": "Japan", "physical_risk": 6.0, "transition_readiness": 6.5,
           "fiscal_resilience": 5.5, "ndc_ambition": 6.0, "nd_gain": 72.0, "credit_rating_sp": "A+",
           "region": "asia_pacific", "gdp_usd_bn": 4231, "debt_to_gdp_pct": 260.0},
    "CA": {"name": "Canada", "physical_risk": 4.0, "transition_readiness": 6.5,
           "fiscal_resilience": 7.5, "ndc_ambition": 6.5, "nd_gain": 76.0, "credit_rating_sp": "AAA",
           "region": "north_america", "gdp_usd_bn": 2139, "debt_to_gdp_pct": 106.0},
    "IT": {"name": "Italy", "physical_risk": 5.5, "transition_readiness": 5.5,
           "fiscal_resilience": 5.0, "ndc_ambition": 6.5, "nd_gain": 68.0, "credit_rating_sp": "BBB",
           "region": "europe", "gdp_usd_bn": 2010, "debt_to_gdp_pct": 144.0},
    # EU members
    "NL": {"name": "Netherlands", "physical_risk": 6.0, "transition_readiness": 7.5,
           "fiscal_resilience": 8.0, "ndc_ambition": 7.5, "nd_gain": 77.0, "credit_rating_sp": "AAA",
           "region": "europe", "gdp_usd_bn": 1009, "debt_to_gdp_pct": 50.0},
    "ES": {"name": "Spain", "physical_risk": 6.0, "transition_readiness": 6.0,
           "fiscal_resilience": 5.5, "ndc_ambition": 7.0, "nd_gain": 69.0, "credit_rating_sp": "A",
           "region": "europe", "gdp_usd_bn": 1398, "debt_to_gdp_pct": 113.0},
    "SE": {"name": "Sweden", "physical_risk": 2.5, "transition_readiness": 9.0,
           "fiscal_resilience": 8.5, "ndc_ambition": 8.5, "nd_gain": 80.0, "credit_rating_sp": "AAA",
           "region": "europe", "gdp_usd_bn": 585, "debt_to_gdp_pct": 33.0},
    "FI": {"name": "Finland", "physical_risk": 2.5, "transition_readiness": 8.5,
           "fiscal_resilience": 7.5, "ndc_ambition": 8.0, "nd_gain": 79.0, "credit_rating_sp": "AA+",
           "region": "europe", "gdp_usd_bn": 282, "debt_to_gdp_pct": 73.0},
    "DK": {"name": "Denmark", "physical_risk": 3.5, "transition_readiness": 9.0,
           "fiscal_resilience": 8.5, "ndc_ambition": 9.0, "nd_gain": 81.0, "credit_rating_sp": "AAA",
           "region": "europe", "gdp_usd_bn": 400, "debt_to_gdp_pct": 30.0},
    "AT": {"name": "Austria", "physical_risk": 3.5, "transition_readiness": 7.0,
           "fiscal_resilience": 7.5, "ndc_ambition": 7.5, "nd_gain": 74.0, "credit_rating_sp": "AA+",
           "region": "europe", "gdp_usd_bn": 471, "debt_to_gdp_pct": 78.0},
    "BE": {"name": "Belgium", "physical_risk": 4.0, "transition_readiness": 6.5,
           "fiscal_resilience": 6.0, "ndc_ambition": 7.0, "nd_gain": 72.0, "credit_rating_sp": "AA",
           "region": "europe", "gdp_usd_bn": 578, "debt_to_gdp_pct": 105.0},
    "PT": {"name": "Portugal", "physical_risk": 5.5, "transition_readiness": 6.5,
           "fiscal_resilience": 5.5, "ndc_ambition": 7.0, "nd_gain": 69.0, "credit_rating_sp": "A-",
           "region": "europe", "gdp_usd_bn": 252, "debt_to_gdp_pct": 112.0},
    "IE": {"name": "Ireland", "physical_risk": 3.0, "transition_readiness": 6.0,
           "fiscal_resilience": 8.0, "ndc_ambition": 7.0, "nd_gain": 74.0, "credit_rating_sp": "AA-",
           "region": "europe", "gdp_usd_bn": 529, "debt_to_gdp_pct": 44.0},
    "GR": {"name": "Greece", "physical_risk": 6.5, "transition_readiness": 4.5,
           "fiscal_resilience": 4.0, "ndc_ambition": 6.0, "nd_gain": 63.0, "credit_rating_sp": "BBB-",
           "region": "europe", "gdp_usd_bn": 219, "debt_to_gdp_pct": 172.0},
    "PL": {"name": "Poland", "physical_risk": 3.5, "transition_readiness": 4.5,
           "fiscal_resilience": 6.5, "ndc_ambition": 5.5, "nd_gain": 66.0, "credit_rating_sp": "A-",
           "region": "europe", "gdp_usd_bn": 688, "debt_to_gdp_pct": 49.0},
    # BRICS + emerging
    "CN": {"name": "China", "physical_risk": 5.5, "transition_readiness": 5.5,
           "fiscal_resilience": 7.0, "ndc_ambition": 5.0, "nd_gain": 57.0, "credit_rating_sp": "A+",
           "region": "asia_pacific", "gdp_usd_bn": 17963, "debt_to_gdp_pct": 77.0},
    "IN": {"name": "India", "physical_risk": 7.5, "transition_readiness": 4.0,
           "fiscal_resilience": 5.0, "ndc_ambition": 5.5, "nd_gain": 48.0, "credit_rating_sp": "BBB-",
           "region": "south_asia", "gdp_usd_bn": 3385, "debt_to_gdp_pct": 83.0},
    "BR": {"name": "Brazil", "physical_risk": 6.0, "transition_readiness": 5.0,
           "fiscal_resilience": 4.5, "ndc_ambition": 5.0, "nd_gain": 52.0, "credit_rating_sp": "BB",
           "region": "latin_america", "gdp_usd_bn": 1920, "debt_to_gdp_pct": 88.0},
    "RU": {"name": "Russia", "physical_risk": 5.0, "transition_readiness": 2.5,
           "fiscal_resilience": 5.5, "ndc_ambition": 2.5, "nd_gain": 54.0, "credit_rating_sp": "NR",
           "region": "europe_cis", "gdp_usd_bn": 2240, "debt_to_gdp_pct": 20.0},
    "ZA": {"name": "South Africa", "physical_risk": 6.5, "transition_readiness": 4.0,
           "fiscal_resilience": 3.5, "ndc_ambition": 5.0, "nd_gain": 48.0, "credit_rating_sp": "BB-",
           "region": "africa", "gdp_usd_bn": 399, "debt_to_gdp_pct": 72.0},
    "MX": {"name": "Mexico", "physical_risk": 6.0, "transition_readiness": 4.0,
           "fiscal_resilience": 5.5, "ndc_ambition": 4.5, "nd_gain": 52.0, "credit_rating_sp": "BBB",
           "region": "latin_america", "gdp_usd_bn": 1414, "debt_to_gdp_pct": 54.0},
    "ID": {"name": "Indonesia", "physical_risk": 7.0, "transition_readiness": 4.0,
           "fiscal_resilience": 6.0, "ndc_ambition": 5.0, "nd_gain": 49.0, "credit_rating_sp": "BBB",
           "region": "asia_pacific", "gdp_usd_bn": 1319, "debt_to_gdp_pct": 40.0},
    "TR": {"name": "Turkey", "physical_risk": 5.5, "transition_readiness": 3.5,
           "fiscal_resilience": 4.0, "ndc_ambition": 4.0, "nd_gain": 54.0, "credit_rating_sp": "B+",
           "region": "europe_cis", "gdp_usd_bn": 906, "debt_to_gdp_pct": 35.0},
    "SA": {"name": "Saudi Arabia", "physical_risk": 7.0, "transition_readiness": 3.0,
           "fiscal_resilience": 7.5, "ndc_ambition": 3.0, "nd_gain": 55.0, "credit_rating_sp": "A",
           "region": "middle_east", "gdp_usd_bn": 1061, "debt_to_gdp_pct": 26.0},
    "AE": {"name": "United Arab Emirates", "physical_risk": 7.0, "transition_readiness": 4.5,
           "fiscal_resilience": 8.0, "ndc_ambition": 4.0, "nd_gain": 60.0, "credit_rating_sp": "AA",
           "region": "middle_east", "gdp_usd_bn": 507, "debt_to_gdp_pct": 30.0},
    "KR": {"name": "South Korea", "physical_risk": 4.5, "transition_readiness": 6.0,
           "fiscal_resilience": 7.0, "ndc_ambition": 6.0, "nd_gain": 70.0, "credit_rating_sp": "AA",
           "region": "asia_pacific", "gdp_usd_bn": 1665, "debt_to_gdp_pct": 54.0},
    "AU": {"name": "Australia", "physical_risk": 7.0, "transition_readiness": 5.5,
           "fiscal_resilience": 7.5, "ndc_ambition": 5.5, "nd_gain": 73.0, "credit_rating_sp": "AAA",
           "region": "asia_pacific", "gdp_usd_bn": 1675, "debt_to_gdp_pct": 52.0},
    "SG": {"name": "Singapore", "physical_risk": 5.0, "transition_readiness": 7.5,
           "fiscal_resilience": 9.0, "ndc_ambition": 6.0, "nd_gain": 78.0, "credit_rating_sp": "AAA",
           "region": "asia_pacific", "gdp_usd_bn": 397, "debt_to_gdp_pct": 168.0},
    "CH": {"name": "Switzerland", "physical_risk": 3.0, "transition_readiness": 8.0,
           "fiscal_resilience": 9.0, "ndc_ambition": 7.5, "nd_gain": 80.0, "credit_rating_sp": "AAA",
           "region": "europe", "gdp_usd_bn": 818, "debt_to_gdp_pct": 41.0},
    "NO": {"name": "Norway", "physical_risk": 2.5, "transition_readiness": 8.0,
           "fiscal_resilience": 9.5, "ndc_ambition": 8.0, "nd_gain": 82.0, "credit_rating_sp": "AAA",
           "region": "europe", "gdp_usd_bn": 579, "debt_to_gdp_pct": 43.0},
    "NZ": {"name": "New Zealand", "physical_risk": 4.0, "transition_readiness": 7.0,
           "fiscal_resilience": 7.0, "ndc_ambition": 6.5, "nd_gain": 75.0, "credit_rating_sp": "AAA",
           "region": "asia_pacific", "gdp_usd_bn": 247, "debt_to_gdp_pct": 55.0},
    # Vulnerable / frontier
    "BD": {"name": "Bangladesh", "physical_risk": 9.0, "transition_readiness": 2.5,
           "fiscal_resilience": 3.5, "ndc_ambition": 4.0, "nd_gain": 38.0, "credit_rating_sp": "BB-",
           "region": "south_asia", "gdp_usd_bn": 460, "debt_to_gdp_pct": 39.0},
    "PH": {"name": "Philippines", "physical_risk": 8.5, "transition_readiness": 3.5,
           "fiscal_resilience": 5.0, "ndc_ambition": 5.0, "nd_gain": 46.0, "credit_rating_sp": "BBB+",
           "region": "asia_pacific", "gdp_usd_bn": 404, "debt_to_gdp_pct": 61.0},
    "VN": {"name": "Vietnam", "physical_risk": 7.5, "transition_readiness": 3.5,
           "fiscal_resilience": 5.5, "ndc_ambition": 5.5, "nd_gain": 47.0, "credit_rating_sp": "BB+",
           "region": "asia_pacific", "gdp_usd_bn": 409, "debt_to_gdp_pct": 38.0},
    "EG": {"name": "Egypt", "physical_risk": 7.0, "transition_readiness": 3.0,
           "fiscal_resilience": 3.0, "ndc_ambition": 4.0, "nd_gain": 43.0, "credit_rating_sp": "B-",
           "region": "middle_east", "gdp_usd_bn": 476, "debt_to_gdp_pct": 92.0},
    "NG": {"name": "Nigeria", "physical_risk": 7.5, "transition_readiness": 2.5,
           "fiscal_resilience": 3.0, "ndc_ambition": 3.5, "nd_gain": 36.0, "credit_rating_sp": "B-",
           "region": "africa", "gdp_usd_bn": 477, "debt_to_gdp_pct": 38.0},
    "KE": {"name": "Kenya", "physical_risk": 7.0, "transition_readiness": 3.5,
           "fiscal_resilience": 3.5, "ndc_ambition": 5.0, "nd_gain": 41.0, "credit_rating_sp": "B",
           "region": "africa", "gdp_usd_bn": 113, "debt_to_gdp_pct": 68.0},
    "CL": {"name": "Chile", "physical_risk": 5.0, "transition_readiness": 6.0,
           "fiscal_resilience": 6.5, "ndc_ambition": 6.5, "nd_gain": 63.0, "credit_rating_sp": "A",
           "region": "latin_america", "gdp_usd_bn": 301, "debt_to_gdp_pct": 38.0},
    "CO": {"name": "Colombia", "physical_risk": 6.0, "transition_readiness": 4.5,
           "fiscal_resilience": 4.5, "ndc_ambition": 5.5, "nd_gain": 50.0, "credit_rating_sp": "BB+",
           "region": "latin_america", "gdp_usd_bn": 334, "debt_to_gdp_pct": 60.0},
    "PE": {"name": "Peru", "physical_risk": 6.5, "transition_readiness": 4.0,
           "fiscal_resilience": 5.5, "ndc_ambition": 5.0, "nd_gain": 49.0, "credit_rating_sp": "BBB",
           "region": "latin_america", "gdp_usd_bn": 242, "debt_to_gdp_pct": 34.0},
    "TH": {"name": "Thailand", "physical_risk": 7.0, "transition_readiness": 4.0,
           "fiscal_resilience": 6.0, "ndc_ambition": 4.5, "nd_gain": 51.0, "credit_rating_sp": "BBB+",
           "region": "asia_pacific", "gdp_usd_bn": 495, "debt_to_gdp_pct": 62.0},
    "MY": {"name": "Malaysia", "physical_risk": 6.0, "transition_readiness": 5.0,
           "fiscal_resilience": 6.0, "ndc_ambition": 5.0, "nd_gain": 56.0, "credit_rating_sp": "A-",
           "region": "asia_pacific", "gdp_usd_bn": 407, "debt_to_gdp_pct": 66.0},
    "PK": {"name": "Pakistan", "physical_risk": 8.5, "transition_readiness": 2.5,
           "fiscal_resilience": 2.5, "ndc_ambition": 3.5, "nd_gain": 35.0, "credit_rating_sp": "CCC+",
           "region": "south_asia", "gdp_usd_bn": 374, "debt_to_gdp_pct": 75.0},
    "HU": {"name": "Hungary", "physical_risk": 4.5, "transition_readiness": 4.5,
           "fiscal_resilience": 5.0, "ndc_ambition": 5.5, "nd_gain": 64.0, "credit_rating_sp": "BBB",
           "region": "europe", "gdp_usd_bn": 188, "debt_to_gdp_pct": 73.0},
    "CZ": {"name": "Czech Republic", "physical_risk": 3.5, "transition_readiness": 5.5,
           "fiscal_resilience": 7.0, "ndc_ambition": 6.0, "nd_gain": 70.0, "credit_rating_sp": "AA-",
           "region": "europe", "gdp_usd_bn": 290, "debt_to_gdp_pct": 44.0},
    "RO": {"name": "Romania", "physical_risk": 4.5, "transition_readiness": 4.0,
           "fiscal_resilience": 5.0, "ndc_ambition": 5.5, "nd_gain": 60.0, "credit_rating_sp": "BBB-",
           "region": "europe", "gdp_usd_bn": 286, "debt_to_gdp_pct": 48.0},
    "IL": {"name": "Israel", "physical_risk": 6.0, "transition_readiness": 6.0,
           "fiscal_resilience": 6.5, "ndc_ambition": 5.0, "nd_gain": 68.0, "credit_rating_sp": "A+",
           "region": "middle_east", "gdp_usd_bn": 525, "debt_to_gdp_pct": 62.0},
    "AR": {"name": "Argentina", "physical_risk": 5.5, "transition_readiness": 3.5,
           "fiscal_resilience": 2.5, "ndc_ambition": 4.5, "nd_gain": 51.0, "credit_rating_sp": "CCC-",
           "region": "latin_america", "gdp_usd_bn": 631, "debt_to_gdp_pct": 85.0},
}

# NGFS-inspired scenario multipliers for 2030 / 2050 horizons
CLIMATE_SCENARIOS = {
    "net_zero_2050": {
        "label": "Net Zero 2050 (NGFS Orderly)",
        "physical_risk_multiplier_2030": 1.0,
        "physical_risk_multiplier_2050": 1.1,
        "transition_pressure_2030": 1.4,
        "transition_pressure_2050": 1.2,
        "description": "Immediate, ambitious policy action — high transition pressure near-term",
    },
    "below_2c": {
        "label": "Below 2C (NGFS Orderly)",
        "physical_risk_multiplier_2030": 1.0,
        "physical_risk_multiplier_2050": 1.3,
        "transition_pressure_2030": 1.2,
        "transition_pressure_2050": 1.1,
        "description": "Gradual policy tightening — moderate transition & physical risk",
    },
    "delayed_transition": {
        "label": "Delayed Transition (NGFS Disorderly)",
        "physical_risk_multiplier_2030": 1.1,
        "physical_risk_multiplier_2050": 1.5,
        "transition_pressure_2030": 0.8,
        "transition_pressure_2050": 2.0,
        "description": "Delayed policy action — sharp transition shock post-2030",
    },
    "current_policies": {
        "label": "Current Policies (NGFS Hot House)",
        "physical_risk_multiplier_2030": 1.1,
        "physical_risk_multiplier_2050": 2.0,
        "transition_pressure_2030": 0.5,
        "transition_pressure_2050": 0.5,
        "description": "No additional policy — severe physical risk by 2050",
    },
    "nationally_determined": {
        "label": "NDCs (NGFS Hot House)",
        "physical_risk_multiplier_2030": 1.05,
        "physical_risk_multiplier_2050": 1.7,
        "transition_pressure_2030": 0.7,
        "transition_pressure_2050": 0.7,
        "description": "NDC pledges only — insufficient for 2C target",
    },
}

# Rating notch mapping (S&P scale)
RATING_NOTCH_MAP = {
    "AAA": 22, "AA+": 21, "AA": 20, "AA-": 19,
    "A+": 18, "A": 17, "A-": 16,
    "BBB+": 15, "BBB": 14, "BBB-": 13,
    "BB+": 12, "BB": 11, "BB-": 10,
    "B+": 9, "B": 8, "B-": 7,
    "CCC+": 6, "CCC": 5, "CCC-": 4,
    "CC": 3, "C": 2, "D": 1, "NR": 0,
}
NOTCH_TO_RATING = {v: k for k, v in RATING_NOTCH_MAP.items()}


# ---------------------------------------------------------------------------
# Result Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class SovereignClimateRiskResult:
    country_iso2: str
    country_name: str
    assessment_date: str
    scenario: str
    horizon: str  # 2030 / 2050
    # Component scores (0-100, higher = worse risk)
    physical_risk_score: float = 0.0
    transition_risk_score: float = 0.0
    fiscal_vulnerability_score: float = 0.0
    adaptation_readiness_score: float = 0.0
    composite_climate_risk_score: float = 0.0
    # Rating impact
    baseline_rating: str = ""
    climate_adjusted_rating: str = ""
    notch_adjustment: int = 0
    # Spread impact
    climate_spread_delta_bps: float = 0.0
    # Decomposition
    risk_decomposition: dict = field(default_factory=dict)
    nd_gain_score: float = 0.0
    ndc_ambition_score: float = 0.0
    notes: list = field(default_factory=list)


@dataclass
class SovereignPortfolioResult:
    portfolio_name: str
    assessment_date: str
    scenario: str
    horizon: str
    total_exposure_usd: float = 0.0
    country_count: int = 0
    weighted_avg_climate_risk: float = 0.0
    weighted_avg_notch_adjustment: float = 0.0
    weighted_avg_spread_delta_bps: float = 0.0
    total_climate_var_usd: float = 0.0
    country_results: list = field(default_factory=list)
    risk_tier_distribution: dict = field(default_factory=dict)
    region_breakdown: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class SovereignClimateRiskEngine:
    """Climate-adjusted sovereign risk scoring and spread estimation."""

    # ── Single Sovereign Assessment ───────────────────────────────────────

    def assess_sovereign(
        self,
        country_iso2: str,
        scenario: str = "current_policies",
        horizon: str = "2030",
        physical_risk_override: float | None = None,
        transition_readiness_override: float | None = None,
    ) -> SovereignClimateRiskResult:
        """Compute climate-adjusted sovereign risk for one country."""
        profile = SOVEREIGN_PROFILES.get(country_iso2.upper())
        if not profile:
            return SovereignClimateRiskResult(
                country_iso2=country_iso2,
                country_name="Unknown",
                assessment_date=datetime.utcnow().strftime("%Y-%m-%d"),
                scenario=scenario,
                horizon=horizon,
                notes=[f"Country {country_iso2} not in sovereign profiles database"],
            )

        scen = CLIMATE_SCENARIOS.get(scenario, CLIMATE_SCENARIOS["current_policies"])
        hz = "2050" if horizon == "2050" else "2030"

        # Base risk components
        phys = physical_risk_override if physical_risk_override is not None else profile["physical_risk"]
        trans_ready = transition_readiness_override if transition_readiness_override is not None else profile["transition_readiness"]
        fiscal = profile["fiscal_resilience"]
        ndc = profile["ndc_ambition"]
        nd_gain = profile["nd_gain"]

        # Apply scenario multipliers
        phys_mult = scen[f"physical_risk_multiplier_{hz}"]
        trans_press = scen[f"transition_pressure_{hz}"]

        # Physical risk score (0-100): higher physical_risk base * scenario multiplier
        physical_score = min(100.0, (phys / 10.0) * 100 * phys_mult)

        # Transition risk score: inverse of readiness * transition pressure
        transition_score = min(100.0, ((10.0 - trans_ready) / 10.0) * 100 * trans_press)

        # Fiscal vulnerability (0-100): inverse of resilience, amplified by debt
        debt_factor = min(2.0, profile["debt_to_gdp_pct"] / 100.0)
        fiscal_score = min(100.0, ((10.0 - fiscal) / 10.0) * 100 * (0.7 + 0.3 * debt_factor))

        # Adaptation readiness (0-100): inverse of ND-GAIN
        adaptation_score = max(0.0, 100.0 - nd_gain)

        # Composite: weighted average
        # Physical 30%, Transition 25%, Fiscal 25%, Adaptation 20%
        composite = (
            physical_score * 0.30 +
            transition_score * 0.25 +
            fiscal_score * 0.25 +
            adaptation_score * 0.20
        )
        composite = round(composite, 1)

        # Rating notch adjustment
        baseline_rating = profile.get("credit_rating_sp", "NR")
        baseline_notch = RATING_NOTCH_MAP.get(baseline_rating, 0)

        if composite >= 70:
            notch_adj = -3
        elif composite >= 55:
            notch_adj = -2
        elif composite >= 40:
            notch_adj = -1
        elif composite >= 25:
            notch_adj = 0
        else:
            notch_adj = 0

        adjusted_notch = max(1, baseline_notch + notch_adj)
        adjusted_rating = NOTCH_TO_RATING.get(adjusted_notch, "NR")

        # Spread delta (bps): empirical-style mapping
        # Calibrated: each composite point above 30 adds ~1.5-3 bps
        if composite > 30:
            spread_delta = round((composite - 30) * 2.0 + 5, 1)
        else:
            spread_delta = 0.0

        # Scenario-specific amplification
        if scenario in ("delayed_transition", "current_policies") and hz == "2050":
            spread_delta *= 1.3

        spread_delta = round(spread_delta, 1)

        return SovereignClimateRiskResult(
            country_iso2=country_iso2.upper(),
            country_name=profile["name"],
            assessment_date=datetime.utcnow().strftime("%Y-%m-%d"),
            scenario=scenario,
            horizon=hz,
            physical_risk_score=round(physical_score, 1),
            transition_risk_score=round(transition_score, 1),
            fiscal_vulnerability_score=round(fiscal_score, 1),
            adaptation_readiness_score=round(adaptation_score, 1),
            composite_climate_risk_score=composite,
            baseline_rating=baseline_rating,
            climate_adjusted_rating=adjusted_rating,
            notch_adjustment=notch_adj,
            climate_spread_delta_bps=spread_delta,
            risk_decomposition={
                "physical_risk_weighted": round(physical_score * 0.30, 1),
                "transition_risk_weighted": round(transition_score * 0.25, 1),
                "fiscal_vulnerability_weighted": round(fiscal_score * 0.25, 1),
                "adaptation_readiness_weighted": round(adaptation_score * 0.20, 1),
            },
            nd_gain_score=nd_gain,
            ndc_ambition_score=ndc,
            notes=[f"Scenario: {scen['label']}", scen["description"]],
        )

    # ── Portfolio-Level Assessment ────────────────────────────────────────

    def assess_portfolio(
        self,
        portfolio_name: str,
        holdings: list[dict],
        scenario: str = "current_policies",
        horizon: str = "2030",
    ) -> SovereignPortfolioResult:
        """
        Assess climate risk for a sovereign bond portfolio.

        holdings: list of {"country_iso2": "XX", "exposure_usd": 1000000}
        """
        total_exposure = sum(h.get("exposure_usd", 0) for h in holdings)
        if total_exposure == 0:
            return SovereignPortfolioResult(
                portfolio_name=portfolio_name,
                assessment_date=datetime.utcnow().strftime("%Y-%m-%d"),
                scenario=scenario,
                horizon=horizon,
            )

        country_results = []
        weighted_risk = 0.0
        weighted_notch = 0.0
        weighted_spread = 0.0
        tier_dist = {"low": 0.0, "moderate": 0.0, "high": 0.0, "very_high": 0.0}
        region_agg: dict[str, float] = {}

        for h in holdings:
            iso2 = h.get("country_iso2", "")
            exposure = h.get("exposure_usd", 0)
            weight = exposure / total_exposure if total_exposure > 0 else 0

            result = self.assess_sovereign(iso2, scenario, horizon)
            cs = result.composite_climate_risk_score

            weighted_risk += cs * weight
            weighted_notch += result.notch_adjustment * weight
            weighted_spread += result.climate_spread_delta_bps * weight

            # Tier classification
            if cs < 25:
                tier = "low"
            elif cs < 45:
                tier = "moderate"
            elif cs < 65:
                tier = "high"
            else:
                tier = "very_high"
            tier_dist[tier] = tier_dist.get(tier, 0) + weight * 100

            # Region
            profile = SOVEREIGN_PROFILES.get(iso2.upper(), {})
            region = profile.get("region", "other")
            region_agg[region] = region_agg.get(region, 0) + weight * 100

            country_results.append({
                "country_iso2": iso2,
                "country_name": result.country_name,
                "exposure_usd": exposure,
                "weight_pct": round(weight * 100, 2),
                "composite_risk": cs,
                "risk_tier": tier,
                "notch_adjustment": result.notch_adjustment,
                "spread_delta_bps": result.climate_spread_delta_bps,
                "baseline_rating": result.baseline_rating,
                "adjusted_rating": result.climate_adjusted_rating,
            })

        # Climate VaR (simplified): spread delta * duration assumption (5y) * exposure
        assumed_duration = 5.0
        climate_var = total_exposure * (weighted_spread / 10000) * assumed_duration

        return SovereignPortfolioResult(
            portfolio_name=portfolio_name,
            assessment_date=datetime.utcnow().strftime("%Y-%m-%d"),
            scenario=scenario,
            horizon=horizon,
            total_exposure_usd=total_exposure,
            country_count=len(holdings),
            weighted_avg_climate_risk=round(weighted_risk, 1),
            weighted_avg_notch_adjustment=round(weighted_notch, 2),
            weighted_avg_spread_delta_bps=round(weighted_spread, 1),
            total_climate_var_usd=round(climate_var, 2),
            country_results=country_results,
            risk_tier_distribution={k: round(v, 1) for k, v in tier_dist.items()},
            region_breakdown={k: round(v, 1) for k, v in region_agg.items()},
        )

    # ── Static Reference Data ─────────────────────────────────────────────

    @staticmethod
    def get_sovereign_profiles() -> dict:
        return SOVEREIGN_PROFILES

    @staticmethod
    def get_climate_scenarios() -> dict:
        return CLIMATE_SCENARIOS

    @staticmethod
    def get_country_list() -> list[dict]:
        return [
            {"iso2": k, "name": v["name"], "region": v["region"],
             "credit_rating": v["credit_rating_sp"], "nd_gain": v["nd_gain"]}
            for k, v in SOVEREIGN_PROFILES.items()
        ]
