"""
E58: Methane & Fugitive Emissions Engine

Standards: EU Methane Regulation 2024/1787 · OGMP 2.0 (5 levels) · IPCC AR6 GWP-20 (82.5) vs
GWP-100 (29.8) · EPA OOOOa/OOOOb LDAR rules · IEA Methane Tracker ·
UNEP IMEO (International Methane Emissions Observatory) · super-emitter event detection
"""

import random
import math
from typing import Optional
from datetime import date, timedelta


# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

# IPCC AR6 WG1 Table 7.SM.7
GWP_100_CH4 = 29.8
GWP_100_N2O = 273.0
GWP_20_CH4 = 82.5
GWP_20_N2O = 273.0  # N2O GWP-20 ~273 (AR6)

SUPER_EMITTER_THRESHOLD_T_PA = 100.0      # >100 tonnes CH4/event
SUPER_EMITTER_RATE_KG_HR = 10.0          # >10 kg/hr continuous
IMEO_SATELLITE_THRESHOLD_T_HR = 25.0     # >25 t/hr detectable by satellites

EU_METHANE_REG_SECTORS = {"oil", "oil_gas", "gas", "coal", "upstream", "midstream", "downstream"}

EU_VENTING_PROHIBITION = {
    "oil_gas": 2025,
    "coal": 2027,
    "coalmine_methane": 2027,
}

OGMP_LEVEL_DESCRIPTIONS = {
    1: "Company-level mass balance (emission factors, lowest accuracy)",
    2: "Source-level estimates using emission factors (no direct measurement)",
    3: "Source-level measurement for some significant sources (partial direct)",
    4: "Source-level measurement for all significant sources (no third-party)",
    5: "Source-level measurement + independent third-party verification (highest accuracy)",
}

SECTOR_INTENSITY_BENCHMARKS = {
    # (intensity value, unit)
    "oil": (0.08, "m3_CH4_per_boe", "IEA best-in-class 2023"),
    "gas": (0.10, "pct_of_gas_produced", "UNEP Global Methane Pledge target 0.2%"),
    "coal": (5.5, "m3_CH4_per_tonne_coal", "IEA best-in-class 2023"),
    "oil_gas": (0.09, "m3_CH4_per_boe", "IEA blended benchmark"),
    "upstream": (0.12, "pct_of_gas_produced", "OGMP level 4 benchmark"),
    "midstream": (0.08, "pct_of_gas_produced", "Pipeline transmission benchmark"),
}

ABATEMENT_MEASURES = [
    {"measure": "Flare capture (negative cost)", "cost_lo": -20, "cost_hi": 0, "potential_pct": 8, "payback_yrs": 1.5, "sector": ["oil_gas", "upstream"]},
    {"measure": "LDAR programmes", "cost_lo": -5, "cost_hi": 20, "potential_pct": 20, "payback_yrs": 2.5, "sector": ["oil_gas", "gas", "upstream", "midstream"]},
    {"measure": "Pneumatic device replacement", "cost_lo": 0, "cost_hi": 10, "potential_pct": 15, "payback_yrs": 3.0, "sector": ["oil_gas", "upstream"]},
    {"measure": "Compressor rod packing seals", "cost_lo": 10, "cost_hi": 30, "potential_pct": 12, "payback_yrs": 4.5, "sector": ["gas", "midstream"]},
    {"measure": "Venting reduction programmes", "cost_lo": 5, "cost_hi": 15, "potential_pct": 18, "payback_yrs": 3.5, "sector": ["oil_gas", "upstream"]},
    {"measure": "Pipeline inspection and repair", "cost_lo": 15, "cost_hi": 45, "potential_pct": 10, "payback_yrs": 6.0, "sector": ["gas", "midstream", "downstream"]},
    {"measure": "Methane recovery from coal mines", "cost_lo": 5, "cost_hi": 25, "potential_pct": 22, "payback_yrs": 4.0, "sector": ["coal", "coalmine_methane"]},
    {"measure": "Pre-drainage degasification", "cost_lo": 20, "cost_hi": 50, "potential_pct": 15, "payback_yrs": 5.5, "sector": ["coal"]},
]

DETECTION_METHOD_LEAK_RATES = {
    "ogi": 0.3,          # OGI optical gas imaging: ~0.3% leak rate detected
    "avo": 1.5,          # AVO audio/visual/olfactory: ~1.5% leak rate (poor detection)
    "portable_analyzer": 0.8,
    "continuous_monitoring": 0.15,
    "drone_ogi": 0.2,
    "satellite": 0.5,    # satellite misses small leaks
}

EU_METHANE_COMPLIANCE_TIMELINE = {
    2024: "EU Methane Regulation 2024/1787 entered into force",
    2025: "EMTS reporting mandatory; routine venting prohibited (oil/gas)",
    2026: "OGMP Level 3 minimum required",
    2027: "Routine venting prohibited (coal); LDAR quarterly for major equipment",
    2028: "OGMP Level 4 minimum required",
    2030: "Super-emitter notification system fully operational",
}

PENALTY_PER_T_EUR = 250.0  # €250/t methane for excess emissions (EU Methane Reg)


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _rng(entity_id: str) -> random.Random:
    return random.Random(hash(entity_id) & 0xFFFFFFFF)


def _clamp(val: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, val))


def _round(val: float, digits: int = 2) -> float:
    return round(val, digits)


def _days_since(date_str: str) -> int:
    try:
        d = date.fromisoformat(date_str)
        return (date.today() - d).days
    except Exception:
        return 365


# ---------------------------------------------------------------------------
# Method 1: Methane GWP Impact
# ---------------------------------------------------------------------------

def calculate_methane_gwp_impact(
    entity_id: str,
    ch4_kt_pa: float,
    n2o_kt_pa: float = 0.0,
) -> dict:
    # CH4 conversions (kt CH4 → kt CO2e)
    ch4_gwp100 = ch4_kt_pa * GWP_100_CH4  # kt CO2e
    ch4_gwp20 = ch4_kt_pa * GWP_20_CH4

    # N2O conversions
    n2o_gwp100 = n2o_kt_pa * GWP_100_N2O
    n2o_gwp20 = n2o_kt_pa * GWP_20_N2O

    total_gwp100 = ch4_gwp100 + n2o_gwp100  # kt CO2e
    total_gwp20 = ch4_gwp20 + n2o_gwp20

    short_term_ratio = _round(total_gwp20 / total_gwp100, 3) if total_gwp100 > 0 else 1.0

    # Significance flag: GWP-20 tCO2e > 10% of typical Scope 1 (proxy: own GWP-100 * 0.1)
    significance_flag = total_gwp20 > total_gwp100 * 0.10

    return {
        "ch4_kt_pa": _round(ch4_kt_pa, 3),
        "n2o_kt_pa": _round(n2o_kt_pa, 3),
        "ch4_gwp100_kt_co2e": _round(ch4_gwp100, 2),
        "ch4_gwp20_kt_co2e": _round(ch4_gwp20, 2),
        "n2o_gwp100_kt_co2e": _round(n2o_gwp100, 2),
        "n2o_gwp20_kt_co2e": _round(n2o_gwp20, 2),
        "total_gwp100_kt_co2e": _round(total_gwp100, 2),
        "total_gwp20_kt_co2e": _round(total_gwp20, 2),
        "short_term_ratio": short_term_ratio,
        "significance_flag": significance_flag,
        "gwp_values_source": "IPCC AR6 WG1 Table 7.SM.7",
        "note": "GWP-100: CH4=29.8, N2O=273; GWP-20: CH4=82.5, N2O=273",
    }


# ---------------------------------------------------------------------------
# Method 2: EU Methane Regulation Assessment
# ---------------------------------------------------------------------------

def assess_eu_methane_regulation(
    entity_id: str,
    sector: str,
    ch4_emissions_t_pa: float,
    country_code: str,
) -> dict:
    rng = _rng(entity_id + "eu_methane")

    sector_lower = sector.lower()
    in_scope = sector_lower in EU_METHANE_REG_SECTORS or any(s in sector_lower for s in ["oil", "gas", "coal"])

    # LDAR frequency
    if in_scope:
        ldar_frequency = "Quarterly (major equipment), Biannual (minor equipment)"
    else:
        ldar_frequency = "Not applicable (sector out of scope)"

    # Venting prohibition year
    venting_deadline = EU_VENTING_PROHIBITION.get(sector_lower, EU_VENTING_PROHIBITION.get("oil_gas", 2025))
    venting_compliant = date.today().year < venting_deadline or rng.random() > 0.4

    flaring_compliant = rng.random() > 0.3  # emergency-only flaring

    # Compliance score
    requirements = {
        "emts_reporting": in_scope,
        "ldar_programme": rng.random() > 0.35 if in_scope else True,
        "venting_prohibition": venting_compliant,
        "flaring_limit": flaring_compliant,
        "ogmp_reporting": rng.random() > 0.4 if in_scope else True,
        "third_party_verification": rng.random() > 0.5 if in_scope else True,
    }

    met_count = sum(1 for v in requirements.values() if v)
    compliance_score = _round(met_count / len(requirements) * 100, 1)

    # Penalty risk: €250/t methane for excess vs allowance
    allowance_factor = rng.uniform(0.7, 1.3)
    excess_t = max(0.0, ch4_emissions_t_pa * (1 - allowance_factor))
    penalty_risk_eur = _round(excess_t * PENALTY_PER_T_EUR, 0)

    compliance_deadline = max(venting_deadline, 2026)

    return {
        "sector_in_scope": in_scope,
        "emts_required": in_scope,
        "ldar_frequency": ldar_frequency,
        "venting_compliant": venting_compliant,
        "flaring_compliant": flaring_compliant,
        "compliance_score": compliance_score,
        "penalty_risk_eur": penalty_risk_eur,
        "compliance_deadline": compliance_deadline,
        "requirements_status": requirements,
        "regulation_reference": "EU Methane Regulation 2024/1787",
    }


# ---------------------------------------------------------------------------
# Method 3: OGMP Level Assessment
# ---------------------------------------------------------------------------

def assess_ogmp_level(
    entity_id: str,
    measurement_approach: str,
    source_level_data: bool,
    third_party_verified: bool,
    company_level_data: bool,
) -> dict:
    rng = _rng(entity_id + "ogmp")

    # Determine current level
    if third_party_verified and source_level_data:
        current_level = 5
    elif source_level_data and measurement_approach in ("direct_measurement", "level4"):
        current_level = 4
    elif source_level_data and measurement_approach in ("partial_measurement", "level3"):
        current_level = 3
    elif source_level_data:
        current_level = 2
    elif company_level_data:
        current_level = 1
    else:
        current_level = 1

    # EU minimum requirements
    eu_min_2026 = 3
    eu_min_2028 = 4
    target_level = max(current_level, eu_min_2028)

    gap_to_eu_min = max(0, eu_min_2026 - current_level)

    uplift_actions = []
    if current_level < 3:
        uplift_actions.append("Implement direct measurement for at least some significant emission sources")
    if current_level < 4:
        uplift_actions.append("Deploy OGI cameras and portable analysers across all significant sources")
        uplift_actions.append("Establish source-level measurement programme with site-specific protocols")
    if current_level < 5:
        uplift_actions.append("Engage accredited third-party verifier for source-level data")
        uplift_actions.append("Align with OGMP 2.0 reporting framework and register at UNEP OGMP portal")

    compliance_year = 2026 if current_level >= 3 else (2028 if current_level >= 2 else 2030)

    timeline = {
        2024: f"Current level: OGMP {current_level}",
        2025: "EMTS enrolment and baseline measurement programme",
        2026: f"EU minimum L3 required — {'compliant' if current_level >= 3 else 'gap of ' + str(eu_min_2026 - current_level) + ' levels'}",
        2028: f"EU minimum L4 required — {'compliant' if current_level >= 4 else 'gap of ' + str(eu_min_2028 - current_level) + ' levels'}",
    }

    return {
        "current_level": current_level,
        "current_level_description": OGMP_LEVEL_DESCRIPTIONS[current_level],
        "target_level": target_level,
        "target_level_description": OGMP_LEVEL_DESCRIPTIONS[target_level],
        "gap_to_eu_minimum_2026": gap_to_eu_min,
        "uplift_actions": uplift_actions,
        "timeline": timeline,
        "regulatory_compliance_year": compliance_year,
    }


# ---------------------------------------------------------------------------
# Method 4: Super-Emitter Detection
# ---------------------------------------------------------------------------

def detect_super_emitters(entity_id: str, facilities: list) -> dict:
    rng = _rng(entity_id + "superemit")

    super_emitters = []
    remediation_priority = []
    total_super_emitter_ch4 = 0.0

    for fac in facilities:
        name = fac.get("name", "Unnamed")
        ftype = fac.get("type", "unknown")
        ch4_t_pa = float(fac.get("ch4_t_pa", rng.uniform(10, 500)))

        # Rate per hour equivalent
        ch4_kg_hr = ch4_t_pa * 1000 / 8760

        is_super_emitter = ch4_t_pa > SUPER_EMITTER_THRESHOLD_T_PA or ch4_kg_hr > SUPER_EMITTER_RATE_KG_HR
        satellite_detectable = ch4_kg_hr > (IMEO_SATELLITE_THRESHOLD_T_HR * 1000 / 1)  # >25 t/hr
        satellite_prob = _round(min(0.95, ch4_kg_hr / (IMEO_SATELLITE_THRESHOLD_T_HR * 1000) * 0.8), 3)

        notification_required = is_super_emitter  # EU Methane Reg Art. 19

        facility_result = {
            "facility_name": name,
            "facility_type": ftype,
            "ch4_t_pa": _round(ch4_t_pa, 2),
            "ch4_kg_hr": _round(ch4_kg_hr, 3),
            "super_emitter_flag": is_super_emitter,
            "satellite_detectable": satellite_detectable,
            "satellite_detection_probability": satellite_prob,
            "regulatory_notification_required": notification_required,
        }
        super_emitters.append(facility_result)

        if is_super_emitter:
            total_super_emitter_ch4 += ch4_t_pa
            remediation_priority.append({
                "facility": name,
                "ch4_t_pa": _round(ch4_t_pa, 2),
                "priority": "Immediate" if ch4_t_pa > 500 else "High",
                "action": "Deploy OGI survey within 30 days; notify regulator within 5 days",
            })

    regulatory_risk = (
        "Critical" if total_super_emitter_ch4 > 1000
        else "High" if total_super_emitter_ch4 > 200
        else "Medium" if total_super_emitter_ch4 > 50
        else "Low"
    )

    satellite_detection_prob = _round(
        1 - math.prod(1 - f["satellite_detection_probability"] for f in super_emitters)
        if super_emitters else 0.0, 3
    )

    return {
        "super_emitters": super_emitters,
        "total_super_emitter_ch4_t": _round(total_super_emitter_ch4, 2),
        "super_emitter_count": sum(1 for f in super_emitters if f["super_emitter_flag"]),
        "regulatory_risk": regulatory_risk,
        "satellite_detection_probability": satellite_detection_prob,
        "remediation_priority": sorted(remediation_priority, key=lambda x: -x["ch4_t_pa"]),
        "reporting_threshold": f">{SUPER_EMITTER_THRESHOLD_T_PA}t/event or >{SUPER_EMITTER_RATE_KG_HR}kg/hr",
    }


# ---------------------------------------------------------------------------
# Method 5: Methane Abatement Curve
# ---------------------------------------------------------------------------

def calculate_methane_abatement_curve(
    entity_id: str,
    sector: str,
    total_ch4_kt_pa: float,
) -> dict:
    rng = _rng(entity_id + "abatement")

    total_ch4_t = total_ch4_kt_pa * 1000
    sector_lower = sector.lower()

    # Filter relevant measures for sector
    relevant = [m for m in ABATEMENT_MEASURES if not m["sector"] or sector_lower in m["sector"]]
    if not relevant:
        relevant = ABATEMENT_MEASURES[:5]  # fallback

    methane_value_usd_per_t = rng.uniform(3.0, 8.0)  # commodity value
    carbon_price_usd_per_tco2e = rng.uniform(25.0, 75.0)

    measures_output = []
    total_capex = 0.0
    total_potential_t = 0.0
    zero_cost_t = 0.0

    for m in relevant:
        mid_cost = (m["cost_lo"] + m["cost_hi"]) / 2
        noise = rng.uniform(-2.0, 2.0)
        cost_per_t = mid_cost + noise

        potential_t = total_ch4_t * m["potential_pct"] / 100
        capex = max(0.0, cost_per_t * potential_t)
        revenue = methane_value_usd_per_t * potential_t  # commodity recovery
        carbon_value = potential_t * GWP_100_CH4 * carbon_price_usd_per_tco2e  # /1000 for t CO2e

        net_cost = capex - revenue - carbon_value / 1000

        measures_output.append({
            "measure": m["measure"],
            "cost_per_tch4_usd": _round(cost_per_t, 1),
            "abatement_potential_pct": _round(m["potential_pct"], 1),
            "abatement_potential_t_pa": _round(potential_t, 1),
            "capex_usd": _round(capex, 0),
            "payback_yrs": _round(m["payback_yrs"] * rng.uniform(0.8, 1.2), 1),
            "carbon_value_usd": _round(carbon_value / 1000, 0),
            "net_cost_usd": _round(net_cost, 0),
        })

        total_capex += capex
        total_potential_t += potential_t
        if cost_per_t <= 0:
            zero_cost_t += potential_t

    zero_cost_pct = _round(zero_cost_t / total_ch4_t * 100, 1) if total_ch4_t > 0 else 0.0
    total_potential_pct = _round(min(75.0, total_potential_t / total_ch4_t * 100), 1) if total_ch4_t > 0 else 0.0
    total_carbon_value = sum(m["carbon_value_usd"] for m in measures_output)
    payback = _round(total_capex / (total_carbon_value + 1), 1) if total_capex > 0 else 0.0

    return {
        "abatement_measures": sorted(measures_output, key=lambda x: x["cost_per_tch4_usd"]),
        "zero_cost_potential_pct": zero_cost_pct,
        "total_abatement_potential_pct": total_potential_pct,
        "total_capex_usd": _round(total_capex, 0),
        "payback_yrs": payback,
        "carbon_value_usd": _round(total_carbon_value, 0),
        "net_cost_usd": _round(total_capex - total_carbon_value, 0),
        "methane_commodity_value_usd_per_t": _round(methane_value_usd_per_t, 2),
        "carbon_price_usd_per_tco2e": _round(carbon_price_usd_per_tco2e, 2),
    }


# ---------------------------------------------------------------------------
# Method 6: LDAR Compliance
# ---------------------------------------------------------------------------

def assess_ldar_compliance(
    entity_id: str,
    facility_count: int,
    last_inspection_date: str,
    leak_detection_method: str,
) -> dict:
    rng = _rng(entity_id + "ldar")

    days_since = _days_since(last_inspection_date)

    # EPA OOOOa/OOOOb: quarterly for wells, biannual for gathering/processing
    required_freq_days = 90  # quarterly as conservative default
    overdue_inspections = max(0, int(days_since / required_freq_days) - 1)

    # Detection method adequacy
    method_lower = leak_detection_method.lower().replace(" ", "_").replace("-", "_")
    estimated_leak_rate = DETECTION_METHOD_LEAK_RATES.get(method_lower, 1.0)
    method_adequate = method_lower in ("ogi", "drone_ogi", "continuous_monitoring")

    detection_adequacy = "Adequate" if method_adequate else "Inadequate — upgrade to OGI or continuous monitoring"

    compliance_status = (
        "Compliant" if overdue_inspections == 0 and method_adequate
        else "Partially Compliant" if overdue_inspections <= 1 or method_adequate
        else "Non-Compliant"
    )

    # Next inspection due
    try:
        last = date.fromisoformat(last_inspection_date)
        next_due = last + timedelta(days=required_freq_days)
    except Exception:
        next_due = date.today() + timedelta(days=30)

    return {
        "facility_count": facility_count,
        "inspection_frequency_required": f"Quarterly ({required_freq_days} days) — EPA OOOOa/OOOOb + EU Methane Reg",
        "last_inspection_date": last_inspection_date,
        "days_since_last_inspection": days_since,
        "overdue_inspections": overdue_inspections,
        "detection_method": leak_detection_method,
        "detection_method_adequacy": detection_adequacy,
        "estimated_leak_rate_pct": _round(estimated_leak_rate, 2),
        "compliance_status": compliance_status,
        "next_inspection_due": str(next_due),
        "estimated_annual_inspections_required": facility_count * 4,
        "eu_ldar_reference": "EU Methane Regulation 2024/1787 Art. 14-18",
        "epa_reference": "40 CFR Part 60 Subpart OOOOa/OOOOb",
    }


# ---------------------------------------------------------------------------
# Method 7: Methane Intensity
# ---------------------------------------------------------------------------

def compute_methane_intensity(
    entity_id: str,
    sector: str,
    production_volume: float,
    production_unit: str,
    ch4_emissions_t_pa: float,
) -> dict:
    rng = _rng(entity_id + "intensity")

    sector_lower = sector.lower()
    bm_data = SECTOR_INTENSITY_BENCHMARKS.get(sector_lower, (0.15, "fraction", "IEA 2023"))

    # Compute intensity based on unit
    if production_volume > 0:
        intensity_current = _round(ch4_emissions_t_pa / production_volume, 6)
    else:
        intensity_current = 0.0

    intensity_target = 0.002 * production_volume / max(ch4_emissions_t_pa, 1)  # 0.2% UNEP target proxy
    intensity_benchmark = float(bm_data[0])

    gap_to_target_pct = _round(
        (intensity_current - (production_volume * 0.002 / max(1, production_volume))) / max(intensity_current, 1e-9) * 100, 2
    ) if production_volume > 0 else 0.0

    gap_to_benchmark = _round(intensity_current - intensity_benchmark, 6)

    # Performance tier
    if gap_to_benchmark <= 0:
        performance_tier = "Best-in-Class"
    elif gap_to_benchmark < intensity_benchmark * 0.5:
        performance_tier = "Above Average"
    elif gap_to_benchmark < intensity_benchmark:
        performance_tier = "Average"
    elif gap_to_benchmark < intensity_benchmark * 2:
        performance_tier = "Below Average"
    else:
        performance_tier = "Laggard"

    # Abatement to reach benchmark
    abatement_to_benchmark_t = _round(max(0.0, (intensity_current - intensity_benchmark) * production_volume), 2)

    # UNEP Global Methane Pledge target: 0.2% of gas produced
    target_intensity_unep = 0.002
    abatement_to_target_t = _round(max(0.0, ch4_emissions_t_pa - production_volume * target_intensity_unep), 2)

    return {
        "intensity_current": intensity_current,
        "intensity_target_unep_0_2pct": _round(target_intensity_unep, 4),
        "intensity_benchmark": intensity_benchmark,
        "benchmark_source": bm_data[2],
        "production_unit": production_unit,
        "gap_to_benchmark": gap_to_benchmark,
        "performance_tier": performance_tier,
        "abatement_to_benchmark_t_pa": abatement_to_benchmark_t,
        "abatement_to_target_t_pa": abatement_to_target_t,
        "sector": sector,
        "total_ch4_t_pa": _round(ch4_emissions_t_pa, 2),
    }
