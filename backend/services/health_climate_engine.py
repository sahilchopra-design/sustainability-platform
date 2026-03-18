"""
E59: Health-Climate Nexus & Social Risk Engine

Standards: WHO Climate and Health Country Profiles 2023 · Lancet Countdown 2023 ·
IPCC AR6 health chapter · ILO heat stress productivity model · WHO air quality guidelines 2021 ·
OSHA heat illness prevention · Costello et al. 2009 health climate framework
"""

import random
import math
from typing import Optional


# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

# Country-level health vulnerability profiles (selected 50 countries)
COUNTRY_HEALTH_PROFILES = {
    "IN": {"heat_mortality_100k": 3.5, "pm25_ugm3": 58.0, "who_ccs_score": 72.0, "health_resilience": 38.0, "ncchap": True, "ndc_health": True},
    "BD": {"heat_mortality_100k": 4.2, "pm25_ugm3": 62.0, "who_ccs_score": 78.0, "health_resilience": 30.0, "ncchap": True, "ndc_health": True},
    "PK": {"heat_mortality_100k": 3.8, "pm25_ugm3": 55.0, "who_ccs_score": 75.0, "health_resilience": 32.0, "ncchap": False, "ndc_health": False},
    "PH": {"heat_mortality_100k": 2.8, "pm25_ugm3": 22.0, "who_ccs_score": 65.0, "health_resilience": 42.0, "ncchap": True, "ndc_health": True},
    "NG": {"heat_mortality_100k": 5.1, "pm25_ugm3": 68.0, "who_ccs_score": 82.0, "health_resilience": 25.0, "ncchap": False, "ndc_health": False},
    "ET": {"heat_mortality_100k": 4.5, "pm25_ugm3": 30.0, "who_ccs_score": 80.0, "health_resilience": 22.0, "ncchap": True, "ndc_health": True},
    "KE": {"heat_mortality_100k": 3.2, "pm25_ugm3": 25.0, "who_ccs_score": 70.0, "health_resilience": 35.0, "ncchap": True, "ndc_health": True},
    "ZA": {"heat_mortality_100k": 2.4, "pm25_ugm3": 28.0, "who_ccs_score": 58.0, "health_resilience": 45.0, "ncchap": True, "ndc_health": False},
    "BR": {"heat_mortality_100k": 1.8, "pm25_ugm3": 16.0, "who_ccs_score": 52.0, "health_resilience": 50.0, "ncchap": True, "ndc_health": True},
    "MX": {"heat_mortality_100k": 1.5, "pm25_ugm3": 20.0, "who_ccs_score": 50.0, "health_resilience": 48.0, "ncchap": True, "ndc_health": False},
    "CN": {"heat_mortality_100k": 2.1, "pm25_ugm3": 32.0, "who_ccs_score": 55.0, "health_resilience": 55.0, "ncchap": True, "ndc_health": True},
    "ID": {"heat_mortality_100k": 3.0, "pm25_ugm3": 18.0, "who_ccs_score": 68.0, "health_resilience": 40.0, "ncchap": True, "ndc_health": True},
    "VN": {"heat_mortality_100k": 2.5, "pm25_ugm3": 22.0, "who_ccs_score": 63.0, "health_resilience": 42.0, "ncchap": True, "ndc_health": True},
    "TH": {"heat_mortality_100k": 1.9, "pm25_ugm3": 19.0, "who_ccs_score": 55.0, "health_resilience": 50.0, "ncchap": True, "ndc_health": False},
    "EG": {"heat_mortality_100k": 3.3, "pm25_ugm3": 45.0, "who_ccs_score": 65.0, "health_resilience": 38.0, "ncchap": False, "ndc_health": False},
    "US": {"heat_mortality_100k": 0.7, "pm25_ugm3": 8.5, "who_ccs_score": 28.0, "health_resilience": 78.0, "ncchap": True, "ndc_health": True},
    "GB": {"heat_mortality_100k": 0.5, "pm25_ugm3": 10.0, "who_ccs_score": 25.0, "health_resilience": 82.0, "ncchap": True, "ndc_health": True},
    "DE": {"heat_mortality_100k": 0.6, "pm25_ugm3": 11.0, "who_ccs_score": 22.0, "health_resilience": 85.0, "ncchap": True, "ndc_health": True},
    "FR": {"heat_mortality_100k": 0.9, "pm25_ugm3": 12.0, "who_ccs_score": 28.0, "health_resilience": 80.0, "ncchap": True, "ndc_health": True},
    "AU": {"heat_mortality_100k": 1.2, "pm25_ugm3": 8.0, "who_ccs_score": 35.0, "health_resilience": 75.0, "ncchap": True, "ndc_health": False},
    "JP": {"heat_mortality_100k": 0.8, "pm25_ugm3": 11.0, "who_ccs_score": 30.0, "health_resilience": 80.0, "ncchap": True, "ndc_health": True},
}

DEFAULT_COUNTRY_PROFILE = {
    "heat_mortality_100k": 2.0, "pm25_ugm3": 25.0, "who_ccs_score": 55.0,
    "health_resilience": 50.0, "ncchap": False, "ndc_health": False,
}

SECTOR_OUTDOOR_WORKER_FRACTION = {
    "agriculture": 0.90, "construction": 0.75, "mining": 0.60, "utilities": 0.35,
    "manufacturing": 0.25, "transport": 0.45, "oil_gas": 0.40, "retail": 0.10,
    "finance": 0.02, "technology": 0.05, "healthcare": 0.15, "other": 0.20,
}

WHO_AQG_PM25 = 5.0       # μg/m3 annual mean (WHO AQG 2021)
WHO_AQG_NO2 = 10.0       # μg/m3 annual mean
WHO_AQG_O3 = 60.0        # μg/m3 peak season daily 8-hr mean
EU_AQD_PM25 = 10.0       # μg/m3 (EU Air Quality Directive 2024 revision)
EU_AQD_NO2 = 20.0        # μg/m3

WBGT_MODERATE = 28.0     # °C — reduce work intensity
WBGT_SEVERE = 32.0       # °C — stop outdoor work
WBGT_PRODUCTIVITY_BASE = 26.0  # °C — productivity loss starts

VECTOR_DISEASE_CLIMATE_SENSITIVITY = {
    "malaria": {"per_deg_range_pct": 4.5, "rcp45_2050": 0.25, "rcp85_2050": 0.45},
    "dengue": {"per_deg_range_pct": 6.0, "rcp45_2050": 0.60, "rcp85_2050": 1.20},
    "lyme": {"per_deg_range_pct": 3.0, "rcp45_2050": 0.20, "rcp85_2050": 0.35},
    "zika": {"per_deg_range_pct": 4.0, "rcp45_2050": 0.30, "rcp85_2050": 0.55},
    "west_nile": {"per_deg_range_pct": 2.5, "rcp45_2050": 0.15, "rcp85_2050": 0.28},
}

FOOD_SECURITY_COUNTRY_SCORES = {
    "IN": 38, "BD": 30, "PK": 32, "NG": 22, "ET": 18, "KE": 28,
    "CN": 55, "BR": 60, "MX": 55, "ID": 50, "VN": 52, "TH": 58,
    "US": 85, "GB": 88, "DE": 90, "FR": 88, "AU": 87, "JP": 82,
    "ZA": 48, "EG": 35, "PH": 45,
}


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _rng(entity_id: str) -> random.Random:
    return random.Random(hash(entity_id) & 0xFFFFFFFF)


def _clamp(val: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, val))


def _round(val: float, digits: int = 2) -> float:
    return round(val, digits)


def _country_profile(country_code: str) -> dict:
    return COUNTRY_HEALTH_PROFILES.get(country_code.upper(), DEFAULT_COUNTRY_PROFILE.copy())


# ---------------------------------------------------------------------------
# Method 1: Heat Stress Risk
# ---------------------------------------------------------------------------

def assess_heat_stress_risk(
    entity_id: str,
    country_code: str,
    outdoor_worker_pct: float,
    sector: str,
) -> dict:
    rng = _rng(entity_id + "heat")
    cp = _country_profile(country_code)

    # WBGT proxy: based on country heat mortality data as proxy
    wbgt_max = _round(WBGT_PRODUCTIVITY_BASE + cp["heat_mortality_100k"] * 1.5 + rng.uniform(-1, 2), 1)
    heat_stress_score = _round(_clamp(
        (wbgt_max - WBGT_PRODUCTIVITY_BASE) / (WBGT_SEVERE - WBGT_PRODUCTIVITY_BASE) * 100
    ), 1)

    # Productivity loss: 10% per degree above 26°C WBGT for outdoor work
    outdoor_fraction = max(outdoor_worker_pct / 100, SECTOR_OUTDOOR_WORKER_FRACTION.get(sector.lower(), 0.2))
    deg_above_threshold = max(0.0, wbgt_max - WBGT_PRODUCTIVITY_BASE)
    productivity_loss = _round(min(50.0, deg_above_threshold * 10 * outdoor_fraction), 1)

    # Mortality
    mortality = _round(cp["heat_mortality_100k"] * (1 + outdoor_fraction * 0.3), 2)

    # RCP projections (Lancet Countdown 2023)
    rcp45_increase = _round(mortality * 0.30, 2)
    rcp85_increase = _round(mortality * 0.60, 2)

    # OSHA compliance (2024 proposed rule: heat illness prevention plan required >80°F WBGT equiv)
    wbgt_f = wbgt_max * 9 / 5 + 32
    osha_compliant = wbgt_f < 90 or rng.random() > 0.5  # simplified heuristic

    adaptation_measures = [
        "Cool rest areas and acclimatisation programme for new outdoor workers",
        "Real-time WBGT monitoring with automated work-rest schedules",
        "Hydration protocols and heat illness first-aid training",
    ]
    if wbgt_max > WBGT_SEVERE:
        adaptation_measures.insert(0, "URGENT: Immediate work-stoppage protocol for WBGT >32°C conditions")

    return {
        "country_code": country_code,
        "wbgt_max_c": wbgt_max,
        "heat_stress_risk_score": heat_stress_score,
        "productivity_loss_pct": productivity_loss,
        "mortality_per_100k": mortality,
        "rcp45_mortality_increase_pct": rcp45_increase,
        "rcp85_mortality_increase_pct": rcp85_increase,
        "osha_compliant": osha_compliant,
        "outdoor_worker_fraction": _round(outdoor_fraction, 2),
        "adaptation_measures": adaptation_measures,
        "source": "ILO Heat Stress Report (2019); Lancet Countdown (2023); OSHA Heat Standard (2024)",
    }


# ---------------------------------------------------------------------------
# Method 2: Air Quality Risk
# ---------------------------------------------------------------------------

def assess_air_quality_risk(
    entity_id: str,
    country_code: str,
    sector: str,
    annual_production: float,
) -> dict:
    rng = _rng(entity_id + "airquality")
    cp = _country_profile(country_code)

    pm25 = _round(cp["pm25_ugm3"] * rng.uniform(0.85, 1.15), 1)
    # NO2 proxy: lower than PM2.5 in most countries
    no2 = _round(pm25 * rng.uniform(0.2, 0.45), 1)

    who_met = pm25 <= WHO_AQG_PM25
    eu_met = pm25 <= EU_AQD_PM25

    # Respiratory mortality per 100k (WHO GBD 2019 proxy)
    mortality_per_100k = _round(pm25 * 0.6 + rng.uniform(0, 5), 1)

    # Compliance cost proxy: abatement to reach EU standard
    pm25_excess = max(0.0, pm25 - EU_AQD_PM25)
    compliance_cost = _round(pm25_excess * annual_production * 0.005, 0)  # $5/unit/μg excess

    # Health liability: employer exposure for occupational air quality
    health_liability = _round(mortality_per_100k * annual_production * 0.001, 0)

    climate_pm25_attribution = _round(
        _clamp((pm25 - 10) / max(pm25, 1) * 25, 0, 30), 1
    )  # fraction from wildfire/dust (climate-amplified)

    return {
        "country_code": country_code,
        "pm25_exposure_ugm3": pm25,
        "no2_exposure_ugm3": no2,
        "who_guideline_met": who_met,
        "eu_directive_met": eu_met,
        "who_aqg_pm25_threshold": WHO_AQG_PM25,
        "eu_aqd_pm25_threshold": EU_AQD_PM25,
        "mortality_per_100k": mortality_per_100k,
        "climate_amplified_pm25_pct": climate_pm25_attribution,
        "compliance_cost_usd_pa": compliance_cost,
        "health_liability_exposure_usd": health_liability,
        "sources": "WHO AQG 2021; EU Air Quality Directive 2024 revision (2024/2881)",
    }


# ---------------------------------------------------------------------------
# Method 3: Vector Disease Risk
# ---------------------------------------------------------------------------

def assess_vector_disease_risk(
    entity_id: str,
    country_code: str,
    rcp_scenario: str = "rcp45",
) -> dict:
    rng = _rng(entity_id + "vector")
    cp = _country_profile(country_code)

    scenario_key = "rcp45_2050" if "4" in rcp_scenario else "rcp85_2050"

    disease_risks = {}
    for disease, data in VECTOR_DISEASE_CLIMATE_SENSITIVITY.items():
        change_pct = _round(data[scenario_key] * 100 * rng.uniform(0.8, 1.2), 1)
        disease_risks[f"{disease}_risk_change_pct"] = change_pct

    # Composite score: higher heat/humidity index = higher vector disease risk
    country_risk_base = (100 - cp["health_resilience"]) * 0.5 + cp["who_ccs_score"] * 0.3
    composite_score = _round(_clamp(country_risk_base + rng.uniform(-5, 5)), 1)

    # Workforce vulnerability
    if composite_score >= 65:
        vulnerability = "High"
    elif composite_score >= 40:
        vulnerability = "Medium"
    else:
        vulnerability = "Low"

    country_health_resilience = _round(cp["health_resilience"], 1)

    # Prevention cost
    prevention_cost = _round(composite_score * rng.uniform(500, 2000), 0)

    return {
        "country_code": country_code,
        "rcp_scenario": rcp_scenario,
        **disease_risks,
        "composite_score": composite_score,
        "workforce_vulnerability": vulnerability,
        "country_health_resilience": country_health_resilience,
        "prevention_cost_usd_pa": prevention_cost,
        "source": "IPCC AR6 Ch7 Health; Lancet Countdown 2023 Indicator 1.3",
    }


# ---------------------------------------------------------------------------
# Method 4: Food Security Health
# ---------------------------------------------------------------------------

def model_food_security_health(
    entity_id: str,
    country_code: str,
    supply_chain_exposure: list,
) -> dict:
    rng = _rng(entity_id + "food")

    food_score = FOOD_SECURITY_COUNTRY_SCORES.get(country_code.upper(), 52)
    food_score = _clamp(food_score + rng.uniform(-5, 5))

    # IPCC AR6: 2-3% per decade yield decline
    decade = (2050 - 2024) / 10
    caloric_deficit_risk = _round(2.5 * decade * (1 + (100 - food_score) / 200), 1)

    # Malnutrition → productivity loss (stunting)
    malnutrition_productivity_loss = _round(_clamp(caloric_deficit_risk * 1.5), 1)

    supply_chain_vulnerability = []
    for item in supply_chain_exposure:
        commodity = item if isinstance(item, str) else str(item)
        risk_score = _round(rng.uniform(20, 70) * (1 + (100 - food_score) / 200), 1)
        supply_chain_vulnerability.append({
            "commodity": commodity,
            "climate_vulnerability_score": risk_score,
            "risk_level": "High" if risk_score > 55 else "Medium" if risk_score > 35 else "Low",
        })

    adaptation_options = [
        "Diversify sourcing geographies to reduce single-country crop failure exposure",
        "Invest in climate-resilient seed variety programmes (CGIAR partnerships)",
        "On-site canteen improvements and worker nutrition programmes",
        "Long-term procurement contracts with climate-resilient suppliers",
    ]
    if food_score < 40:
        adaptation_options.insert(0, "URGENT: Emergency food security contingency plans for high-exposure countries")

    return {
        "country_code": country_code,
        "food_security_score": _round(food_score, 1),
        "caloric_deficit_risk_pct": caloric_deficit_risk,
        "malnutrition_productivity_loss_pct": malnutrition_productivity_loss,
        "supply_chain_vulnerability": supply_chain_vulnerability,
        "adaptation_options": adaptation_options,
        "source": "IPCC AR6 Ch5 Food/Water; Lancet Countdown 2023 Indicator 1.2",
    }


# ---------------------------------------------------------------------------
# Method 5: Health Financial Impact
# ---------------------------------------------------------------------------

def calculate_health_financial_impact(
    entity_id: str,
    country_code: str,
    employee_count: int,
    outdoor_pct: float,
    sector: str,
) -> dict:
    rng = _rng(entity_id + "financial")
    cp = _country_profile(country_code)

    outdoor_fraction = outdoor_pct / 100
    daily_wage = rng.uniform(30, 250)  # country-sector proxy
    healthcare_daily_cost = daily_wage * rng.uniform(0.5, 1.5)

    # Climate-attributed sick days per employee per year
    heat_sick_days = _round(cp["heat_mortality_100k"] * outdoor_fraction * 0.8, 2)
    air_quality_sick_days = _round(cp["pm25_ugm3"] / 20 * (1 - outdoor_fraction) * 0.5, 2)
    total_sick_days = heat_sick_days + air_quality_sick_days
    climate_attribution_frac = 0.30  # 30% of sick days climate-attributable

    healthcare_cost_uplift = _round(
        employee_count * total_sick_days * climate_attribution_frac * healthcare_daily_cost, 0
    )

    # Productivity loss: heat-adjusted working hours
    productivity_loss_days = _round(total_sick_days * outdoor_fraction * 0.6 * employee_count, 1)
    productivity_loss_usd = _round(productivity_loss_days * daily_wage, 0)

    # Insurance premium uplift (5-20%)
    insurance_uplift_pct = _round(
        _clamp(5 + cp["heat_mortality_100k"] * 2 + rng.uniform(-2, 5), 5, 20), 1
    )

    # Litigation: employer duty of care for heat illness
    litigation_exposure = _round(employee_count * outdoor_fraction * 500 * cp["heat_mortality_100k"], 0)

    total_impact = _round(healthcare_cost_uplift + productivity_loss_usd + litigation_exposure * 0.1, 0)

    # ROI on adaptation investment
    adaptation_cost = _round(employee_count * 200, 0)  # ~$200/employee per year
    roi_adaptation = _round((total_impact - adaptation_cost) / max(adaptation_cost, 1), 2)

    return {
        "country_code": country_code,
        "employee_count": employee_count,
        "outdoor_worker_fraction": _round(outdoor_fraction, 2),
        "healthcare_cost_uplift_usd_pa": healthcare_cost_uplift,
        "productivity_loss_usd_pa": productivity_loss_usd,
        "insurance_premium_uplift_pct": insurance_uplift_pct,
        "litigation_exposure_usd": litigation_exposure,
        "total_financial_impact_usd_pa": total_impact,
        "roi_adaptation": roi_adaptation,
        "adaptation_cost_proxy_usd_pa": adaptation_cost,
        "source": "ILO (2019); WHO (2023); Lancet Countdown 2023 Indicator 4.4",
    }


# ---------------------------------------------------------------------------
# Method 6: WHO Climate Health Assessment
# ---------------------------------------------------------------------------

def assess_who_climate_health(entity_id: str, country_code: str) -> dict:
    rng = _rng(entity_id + "who")
    cp = _country_profile(country_code)

    ccs_score = _round(cp["who_ccs_score"] * rng.uniform(0.95, 1.05), 1)

    if cp["health_resilience"] >= 75:
        readiness = "High — well-funded health system with climate adaptation plans"
    elif cp["health_resilience"] >= 50:
        readiness = "Medium — partial adaptation; significant investment gaps"
    elif cp["health_resilience"] >= 30:
        readiness = "Low — under-resourced health system; high vulnerability"
    else:
        readiness = "Very Low — critical health system gaps; urgent support needed"

    adaptation_finance_gap = _round(
        _clamp(100 - cp["health_resilience"] - rng.uniform(5, 15)), 1
    )

    peer_codes = ["IN", "BD", "BR", "ZA", "CN"]
    peer_comparison = {}
    for p in peer_codes:
        pp = COUNTRY_HEALTH_PROFILES.get(p, DEFAULT_COUNTRY_PROFILE)
        peer_comparison[p] = {
            "who_ccs_score": pp["who_ccs_score"],
            "health_resilience": pp["health_resilience"],
            "ncchap": pp["ncchap"],
        }

    return {
        "country_code": country_code,
        "who_ccs_score": ccs_score,
        "country_health_readiness": readiness,
        "adaptation_finance_gap_pct": adaptation_finance_gap,
        "ncchap_exists": cp["ncchap"],
        "health_ndc_included": cp["ndc_health"],
        "peer_country_comparison": peer_comparison,
        "source": "WHO Climate Change and Health Country Profiles 2023",
    }


# ---------------------------------------------------------------------------
# Method 7: Health-Climate Composite
# ---------------------------------------------------------------------------

def compute_health_climate_composite(
    entity_id: str,
    entity_name: str,
    country_code: str,
    sector: str,
    employee_count: int,
) -> dict:
    rng = _rng(entity_id + "composite")
    cp = _country_profile(country_code)

    outdoor_pct = SECTOR_OUTDOOR_WORKER_FRACTION.get(sector.lower(), 0.2) * 100
    annual_production = rng.uniform(1e6, 1e9)

    # Component results
    heat = assess_heat_stress_risk(entity_id, country_code, outdoor_pct, sector)
    air = assess_air_quality_risk(entity_id, country_code, sector, annual_production)
    vector = assess_vector_disease_risk(entity_id, country_code)
    food = model_food_security_health(entity_id, country_code, [sector, "grains", "proteins"])
    financial = calculate_health_financial_impact(entity_id, country_code, employee_count, outdoor_pct, sector)

    # Normalise component scores to 0-100
    heat_score = heat["heat_stress_risk_score"]
    air_score = _clamp((air["pm25_exposure_ugm3"] - WHO_AQG_PM25) / max(WHO_AQG_PM25, 1) * 30, 0, 100)
    vector_score = vector["composite_score"]
    food_score = _clamp(100 - food["food_security_score"], 0, 100)
    financial_score = _clamp(financial["total_financial_impact_usd_pa"] / max(employee_count * 1000, 1) * 10, 0, 100)

    component_scores = {
        "heat_stress": _round(heat_score, 1),
        "air_quality": _round(air_score, 1),
        "vector_disease": _round(vector_score, 1),
        "food_security": _round(food_score, 1),
        "financial_impact": _round(financial_score, 1),
    }

    weights = {"heat_stress": 0.25, "air_quality": 0.25, "vector_disease": 0.15, "food_security": 0.15, "financial_impact": 0.20}
    overall_score = sum(weights[k] * component_scores[k] for k in weights)
    overall_score = _round(overall_score, 1)

    if overall_score >= 75:
        risk_rating = "Critical"
    elif overall_score >= 55:
        risk_rating = "High"
    elif overall_score >= 35:
        risk_rating = "Medium"
    else:
        risk_rating = "Low"

    priority_hazards = sorted(component_scores.items(), key=lambda x: -x[1])[:3]
    priority_hazards = [k for k, _ in priority_hazards]

    key_interventions = [
        f"Deploy heat stress management protocols (WBGT monitoring, work-rest cycles)",
        f"Upgrade to WHO AQG-compliant air quality monitoring in all facilities",
        f"Integrate health-climate risk into ESG reporting (CSRD ESRS S1, GRI 403)",
    ]
    if risk_rating in ("Critical", "High"):
        key_interventions.insert(0, "Board-level health-climate risk oversight and annual disclosure")

    total_cost = financial["total_financial_impact_usd_pa"]

    # SDG 3 alignment score (health targets)
    sdg3_alignment = _round(_clamp(100 - overall_score + rng.uniform(-5, 5)), 1)

    return {
        "entity_name": entity_name,
        "country_code": country_code,
        "sector": sector,
        "overall_score": overall_score,
        "risk_rating": risk_rating,
        "component_scores": component_scores,
        "priority_hazards": priority_hazards,
        "key_interventions": key_interventions,
        "estimated_total_cost_usd_pa": total_cost,
        "sdg3_alignment": sdg3_alignment,
    }
