"""
Loss & Damage Finance Engine — E70
Standards: COP28 Fund for Response to Loss & Damage (FRLD, Decision 2/CP.28),
WIM Santiago Network for Averting, Minimizing and Addressing Loss and Damage,
Global Shield Against Climate Risks v2 (G7 2023), V20 Vulnerable 20 Group,
Warsaw International Mechanism (WIM 2013), Parametric Insurance Design (IAIS 2022)
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import random
import math

# ---------------------------------------------------------------------------
# Reference Data
# ---------------------------------------------------------------------------

V20_MEMBERS: List[str] = [
    "AFG", "BGD", "BEN", "BHU", "BFA", "KHM", "CMR", "CAF", "COD", "COG",
    "CIV", "DJI", "ETH", "FJI", "GMB", "GHA", "GTM", "GNB", "HTI", "HND",
    "KEN", "KIR", "MDG", "MWI", "MDV", "MLI", "MHL", "FSM", "MNG", "MOZ",
    "NPL", "NER", "NGA", "PAK", "PNG", "PHL", "RWA", "WSM", "SEN", "SLB",
    "SOM", "LKA", "SDN", "SYR", "TLS", "TON", "TUN", "TUV", "TZA", "UGA",
    "VUT", "VNM", "YEM", "ZMB", "ZWE", "NIC", "MAR", "SLE",
]

LOSS_EVENT_TYPES: Dict[str, Dict] = {
    "cyclone": {
        "description": "Tropical cyclone including hurricane and typhoon",
        "wim_relevance": "high",
        "economic_loss_multiplier": 3.5,
        "non_economic_share": 0.35,
        "insurance_penetration_typical": 0.25,
        "parametric_suitable": True,
        "average_return_period_yr": 15,
        "recovery_years": 5,
    },
    "flood": {
        "description": "River flooding, flash floods, coastal inundation",
        "wim_relevance": "high",
        "economic_loss_multiplier": 2.0,
        "non_economic_share": 0.25,
        "insurance_penetration_typical": 0.15,
        "parametric_suitable": True,
        "average_return_period_yr": 10,
        "recovery_years": 3,
    },
    "drought": {
        "description": "Agricultural drought, hydrological drought, water stress",
        "wim_relevance": "high",
        "economic_loss_multiplier": 1.5,
        "non_economic_share": 0.45,
        "insurance_penetration_typical": 0.08,
        "parametric_suitable": True,
        "average_return_period_yr": 8,
        "recovery_years": 2,
    },
    "sea_level_rise": {
        "description": "Permanent inundation and saltwater intrusion",
        "wim_relevance": "very_high",
        "economic_loss_multiplier": 5.0,
        "non_economic_share": 0.70,
        "insurance_penetration_typical": 0.02,
        "parametric_suitable": False,  # slow-onset
        "average_return_period_yr": None,
        "recovery_years": None,  # permanent
    },
    "slow_onset": {
        "description": "Desertification, ocean acidification, permafrost thaw, species loss",
        "wim_relevance": "very_high",
        "economic_loss_multiplier": 2.5,
        "non_economic_share": 0.80,
        "insurance_penetration_typical": 0.01,
        "parametric_suitable": False,
        "average_return_period_yr": None,
        "recovery_years": None,
    },
    "compound": {
        "description": "Concurrent/sequential events (flood + storm surge, drought + heatwave)",
        "wim_relevance": "high",
        "economic_loss_multiplier": 4.0,
        "non_economic_share": 0.40,
        "insurance_penetration_typical": 0.12,
        "parametric_suitable": True,
        "average_return_period_yr": 20,
        "recovery_years": 7,
    },
}

FRLD_ACCESS_CRITERIA: Dict[str, Dict] = {
    "sids": {
        "description": "Small Island Developing States",
        "eligibility_threshold": "UNOHRLLS SIDS list membership",
        "access_modality": "simplified_procedures",
        "indicative_annual_allocation_usd_mn": 50,
        "co_financing_requirement_pct": 0,
        "access_window": "direct",
    },
    "ldc": {
        "description": "Least Developed Countries",
        "eligibility_threshold": "UN CDP LDC list",
        "access_modality": "simplified_procedures",
        "indicative_annual_allocation_usd_mn": 30,
        "co_financing_requirement_pct": 0,
        "access_window": "direct",
    },
    "developing_country": {
        "description": "Developing countries particularly vulnerable to climate change",
        "eligibility_threshold": "ND-GAIN vulnerability score >= 0.55",
        "access_modality": "standard_procedures",
        "indicative_annual_allocation_usd_mn": 15,
        "co_financing_requirement_pct": 15,
        "access_window": "standard",
    },
}

GLOBAL_SHIELD_PILLARS: Dict[str, Dict] = {
    "pre_arranged_finance": {
        "description": "Pre-arranged financial instruments activated at trigger events",
        "instruments": ["catastrophe_bonds", "contingent_credit", "parametric_insurance", "shock_responsive_social_protection"],
        "committed_usd_bn": 9.0,
        "coverage_countries": 58,
    },
    "risk_analytics": {
        "description": "Enhanced climate risk data, modelling and early warning systems",
        "instruments": ["INFORM_risk_index", "CLIMADA_model", "WMO_early_warning", "CCRI"],
        "committed_usd_bn": 0.5,
        "coverage_countries": 120,
    },
    "technical_assistance": {
        "description": "Capacity building for DRM, actuarial skills, insurance regulation",
        "instruments": ["InsuResilience_TA", "V20_technical_facility", "regulatory_sandboxes"],
        "committed_usd_bn": 0.3,
        "coverage_countries": 80,
    },
    "knowledge_platform": {
        "description": "Global knowledge exchange on parametric insurance and risk transfer",
        "instruments": ["TCIR", "GIZ_knowledge_hub", "research_partnerships"],
        "committed_usd_bn": 0.1,
        "coverage_countries": 130,
    },
}

PARAMETRIC_TRIGGERS: Dict[str, Dict] = {
    "wind_speed_kmh": {
        "description": "Maximum sustained wind speed (1-min average)",
        "data_source": "WMO RSMC tropical cyclone bulletins",
        "typical_attachment": 89,
        "typical_exhaustion": 185,
        "unit": "km/h",
        "settlement_days": 10,
        "basis_risk_score": 0.15,
    },
    "rainfall_mm": {
        "description": "72-hour or seasonal cumulative rainfall anomaly",
        "data_source": "CHIRPS v2.0 / GPCC satellite + gauge",
        "typical_attachment": -25,
        "typical_exhaustion": -50,
        "unit": "pct_of_seasonal_mean",
        "settlement_days": 21,
        "basis_risk_score": 0.35,
    },
    "temperature_c": {
        "description": "Maximum daily temperature above seasonal threshold",
        "data_source": "ERA5 reanalysis / NMHSs",
        "typical_attachment": 2.0,
        "typical_exhaustion": 4.0,
        "unit": "degrees_C_above_baseline",
        "settlement_days": 14,
        "basis_risk_score": 0.25,
    },
    "sea_level_cm": {
        "description": "Annual mean sea level above pre-industrial baseline",
        "data_source": "PSMSL tide gauges / AVISO satellite altimetry",
        "typical_attachment": 15,
        "typical_exhaustion": 30,
        "unit": "cm",
        "settlement_days": 45,
        "basis_risk_score": 0.10,
    },
    "drought_spei": {
        "description": "Standardised Precipitation Evapotranspiration Index (SPEI-12)",
        "data_source": "Global Drought Observatory / CRU TS4",
        "typical_attachment": -1.28,
        "typical_exhaustion": -2.0,
        "unit": "SPEI_score",
        "settlement_days": 30,
        "basis_risk_score": 0.30,
    },
    "gdp_shock_pct": {
        "description": "GDP contraction trigger for compound economic shocks",
        "data_source": "IMF Article IV / national statistics",
        "typical_attachment": -5.0,
        "typical_exhaustion": -15.0,
        "unit": "pct_gdp_change",
        "settlement_days": 60,
        "basis_risk_score": 0.45,
    },
}

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class FRLDEligibilityResult:
    country_iso: str
    country_name: str
    eligibility_tier: str  # sids | ldc | developing_country | ineligible
    frld_eligibility_score: float
    indicative_allocation_usd: float
    access_window: str
    v20_member: bool
    co_financing_required_pct: float
    priority_event_types: List[str]
    wim_functions_applicable: List[str]
    estimated_annual_ld_usd: float
    frld_coverage_ratio: float


@dataclass
class ParametricTriggerDesign:
    trigger_id: str
    trigger_index: str
    trigger_threshold: float
    payout_structure: str  # binary | linear | step
    attachment_point: float
    exhaustion_point: float
    max_payout_usd: float
    premium_estimate_usd: float
    basis_risk_score: float
    settlement_days: int
    data_source: str
    payout_at_attachment_usd: float
    expected_annual_payout_usd: float


@dataclass
class WIMAccessResult:
    country_iso: str
    wim_access_score: float
    risk_knowledge_score: float
    retention_transfer_score: float
    rehabilitation_score: float
    santiago_network_eligible: bool
    capacity_needs: List[str]
    wim_action_areas: List[str]
    recommended_technical_providers: List[str]


@dataclass
class LDGapAnalysis:
    country_iso: str
    country_name: str
    event_type: str
    total_economic_loss_usd: float
    non_economic_loss_score: float
    insurance_covered_usd: float
    frld_eligible_usd: float
    global_shield_allocation_usd: float
    wim_support_usd: float
    residual_ld_gap_usd: float
    insurance_coverage_ratio: float
    gap_financing_instruments: List[str]


@dataclass
class LDPortfolioResult:
    portfolio_id: str
    total_portfolio_exposure_usd: float
    total_ld_exposure_usd: float
    v20_concentration_pct: float
    parametric_coverage_ratio: float
    residual_ld_gap_usd: float
    expected_annual_ld_payout_usd: float
    top_loss_event_types: List[str]
    uninsured_countries: List[str]
    recommendations: List[str]


# ---------------------------------------------------------------------------
# Engine Functions
# ---------------------------------------------------------------------------

def calculate_frld_eligibility(country_data: Dict[str, Any], loss_event: Dict[str, Any]) -> FRLDEligibilityResult:
    """Calculate FRLD fund eligibility and indicative allocation for a country/loss event."""
    country_iso = country_data.get("country_iso", "BGD")
    rng = random.Random(hash(str(country_iso) + "frld") & 0xFFFFFFFF)

    country_name = country_data.get("country_name", country_iso)
    is_sids = country_data.get("is_sids", False)
    is_ldc = country_data.get("is_ldc", country_iso in ["BGD", "ETH", "NER", "MWI", "NPL", "UGA", "TZA", "MDG",
                                                          "MLI", "MOZ", "GNB", "SLE", "ZMB", "AFG", "BFA", "CAF",
                                                          "COD", "DJI", "GMB", "HTI", "KHM", "KIR", "TLS", "TUV"])
    nd_gain_score = float(country_data.get("nd_gain_score", rng.uniform(0.35, 0.80)))
    v20_member = country_iso in V20_MEMBERS

    if is_sids:
        tier = "sids"
    elif is_ldc:
        tier = "ldc"
    elif nd_gain_score >= 0.55 or v20_member:
        tier = "developing_country"
    else:
        tier = "ineligible"

    criteria = FRLD_ACCESS_CRITERIA.get(tier, {})
    base_alloc = criteria.get("indicative_annual_allocation_usd_mn", 0) * 1e6
    vuln_mult = 1 + (1 - nd_gain_score) * 0.5
    indicative_alloc = base_alloc * vuln_mult * rng.uniform(0.8, 1.3)

    eligibility_score = round(
        (0.3 if is_sids else 0.2 if is_ldc else 0.1 if tier == "developing_country" else 0)
        + (1 - nd_gain_score) * 0.5
        + (0.2 if v20_member else 0),
        4
    )

    event_type = loss_event.get("event_type", "flood")
    event_info = LOSS_EVENT_TYPES.get(event_type, LOSS_EVENT_TYPES["flood"])

    gdp_usd = float(country_data.get("gdp_usd", rng.uniform(5e9, 200e9)))
    event_multiplier = event_info["economic_loss_multiplier"]
    freq = 1 / (event_info.get("average_return_period_yr") or 25)
    annual_ld = gdp_usd * 0.01 * event_multiplier * freq

    frld_coverage_ratio = min(0.80, indicative_alloc / annual_ld) if annual_ld > 0 else 0

    wim_functions = ["risk_knowledge_function", "risk_transfer_and_retention_function"]
    if event_info["wim_relevance"] == "very_high":
        wim_functions.append("rehabilitation_function")
        wim_functions.append("santiago_network_technical_support")

    priority_events = [
        et for et, ed in LOSS_EVENT_TYPES.items()
        if ed["wim_relevance"] in ["high", "very_high"] and ed.get("insurance_penetration_typical", 0) < 0.15
    ]

    return FRLDEligibilityResult(
        country_iso=country_iso,
        country_name=country_name,
        eligibility_tier=tier,
        frld_eligibility_score=eligibility_score,
        indicative_allocation_usd=round(indicative_alloc, 2),
        access_window=criteria.get("access_window", "none"),
        v20_member=v20_member,
        co_financing_required_pct=criteria.get("co_financing_requirement_pct", 0),
        priority_event_types=priority_events[:3],
        wim_functions_applicable=wim_functions,
        estimated_annual_ld_usd=round(annual_ld, 2),
        frld_coverage_ratio=round(frld_coverage_ratio, 4),
    )


def design_parametric_trigger(trigger_data: Dict[str, Any]) -> ParametricTriggerDesign:
    """Design a parametric insurance trigger with payout structure and basis risk assessment."""
    trigger_id = trigger_data.get("trigger_id", "default")
    rng = random.Random(hash(str(trigger_id)) & 0xFFFFFFFF)

    trigger_index = trigger_data.get("trigger_index", "wind_speed_kmh")
    if trigger_index not in PARAMETRIC_TRIGGERS:
        trigger_index = "wind_speed_kmh"
    ti = PARAMETRIC_TRIGGERS[trigger_index]

    attachment = float(trigger_data.get("attachment_point", ti["typical_attachment"]))
    exhaustion = float(trigger_data.get("exhaustion_point", ti["typical_exhaustion"]))
    max_payout = float(trigger_data.get("max_payout_usd", rng.uniform(1e7, 5e8)))
    payout_structure = trigger_data.get("payout_structure", "linear")

    basis_risk = ti["basis_risk_score"] + rng.uniform(-0.05, 0.05)
    basis_risk = max(0.05, min(0.60, basis_risk))

    # Premium estimation: loss cost method
    trigger_prob = rng.uniform(0.03, 0.15)
    if payout_structure == "binary":
        expected_payout = max_payout * trigger_prob
        payout_at_attach = max_payout
    elif payout_structure == "linear":
        expected_payout = max_payout * trigger_prob * 0.5
        payout_at_attach = 0
    else:  # step
        expected_payout = max_payout * trigger_prob * 0.6
        payout_at_attach = max_payout * 0.3

    loading_factor = 1 + rng.uniform(0.20, 0.40) + basis_risk * 0.15
    premium = expected_payout * loading_factor

    return ParametricTriggerDesign(
        trigger_id=str(trigger_id),
        trigger_index=trigger_index,
        trigger_threshold=attachment,
        payout_structure=payout_structure,
        attachment_point=attachment,
        exhaustion_point=exhaustion,
        max_payout_usd=round(max_payout, 2),
        premium_estimate_usd=round(premium, 2),
        basis_risk_score=round(basis_risk, 4),
        settlement_days=ti["settlement_days"],
        data_source=ti["data_source"],
        payout_at_attachment_usd=round(payout_at_attach, 2),
        expected_annual_payout_usd=round(expected_payout, 2),
    )


def assess_wim_access(country_data: Dict[str, Any]) -> WIMAccessResult:
    """Assess WIM function scores and Santiago Network eligibility."""
    country_iso = country_data.get("country_iso", "FJI")
    rng = random.Random(hash(str(country_iso) + "wim") & 0xFFFFFFFF)

    v20 = country_iso in V20_MEMBERS
    base = 0.45 if v20 else 0.30

    risk_knowledge = round(rng.uniform(base, base + 0.35), 4)
    retention_transfer = round(rng.uniform(base - 0.10, base + 0.30), 4)
    rehabilitation = round(rng.uniform(base - 0.05, base + 0.25), 4)

    wim_score = round(risk_knowledge * 0.35 + retention_transfer * 0.35 + rehabilitation * 0.30, 4)
    santiago_eligible = wim_score < 0.65 and (v20 or country_data.get("is_ldc", False) or country_data.get("is_sids", False))

    capacity_needs = []
    if risk_knowledge < 0.50:
        capacity_needs.append("Climate risk data collection and INFORM methodology training")
    if retention_transfer < 0.45:
        capacity_needs.append("Parametric insurance market development — actuarial and regulatory capacity")
    if rehabilitation < 0.45:
        capacity_needs.append("Post-disaster recovery financing frameworks (PDNA standards)")
    if wim_score < 0.40:
        capacity_needs.append("Comprehensive DRM institutional strengthening")

    action_areas = [
        "WIM Action Area 7: Non-economic loss and damage",
        "WIM Action Area 8: Risk transfer and insurance",
    ]
    if risk_knowledge < 0.55:
        action_areas.append("WIM Action Area 1: Risk knowledge, early warning, risk information")
    if rehabilitation < 0.50:
        action_areas.append("WIM Action Area 6: Rehabilitation, recovery and reintegration")

    providers = ["UNDP CREWS", "InsuResilience Global Partnership", "V20 TF", "World Bank GFDRR"]
    if santiago_eligible:
        providers.insert(0, "Santiago Network Technical Assistance (SNLD)")

    return WIMAccessResult(
        country_iso=country_iso,
        wim_access_score=wim_score,
        risk_knowledge_score=risk_knowledge,
        retention_transfer_score=retention_transfer,
        rehabilitation_score=rehabilitation,
        santiago_network_eligible=santiago_eligible,
        capacity_needs=capacity_needs,
        wim_action_areas=action_areas,
        recommended_technical_providers=providers,
    )


def calculate_residual_ld_gap(country_data: Dict[str, Any], coverage_data: Dict[str, Any]) -> LDGapAnalysis:
    """Calculate total L&D and residual gap after insurance, FRLD, and WIM support."""
    country_iso = country_data.get("country_iso", "PHL")
    rng = random.Random(hash(str(country_iso) + "gap") & 0xFFFFFFFF)

    country_name = country_data.get("country_name", country_iso)
    event_type = country_data.get("event_type", "cyclone")
    event_info = LOSS_EVENT_TYPES.get(event_type, LOSS_EVENT_TYPES["cyclone"])

    gdp = float(country_data.get("gdp_usd", rng.uniform(1e10, 5e11)))
    loss_pct_gdp = rng.uniform(0.5, 5.0) * (event_info["economic_loss_multiplier"] / 3.5)
    total_economic_loss = gdp * loss_pct_gdp / 100
    non_economic_score = round(rng.uniform(0.3, 0.9) * event_info["non_economic_share"] * 2, 4)

    ins_penetration = coverage_data.get(
        "insurance_penetration", event_info["insurance_penetration_typical"] + rng.uniform(-0.05, 0.10)
    )
    ins_penetration = max(0, min(0.95, ins_penetration))
    insurance_covered = total_economic_loss * ins_penetration

    # FRLD indicative allocation
    v20 = country_iso in V20_MEMBERS
    frld_pct = rng.uniform(0.05, 0.20) if v20 else rng.uniform(0.01, 0.08)
    frld_eligible = total_economic_loss * frld_pct

    # Global Shield parametric payout
    gs_covered = coverage_data.get("global_shield_covered", v20)
    global_shield = total_economic_loss * rng.uniform(0.03, 0.12) if gs_covered else 0

    # WIM support (technical assistance only, not direct finance)
    wim_support = total_economic_loss * rng.uniform(0.001, 0.005)

    residual_gap = max(0, total_economic_loss - insurance_covered - frld_eligible - global_shield - wim_support)
    coverage_ratio = round((total_economic_loss - residual_gap) / total_economic_loss, 4) if total_economic_loss else 0

    gap_instruments = []
    if residual_gap > 1e8:
        gap_instruments.append("Sovereign catastrophe bond")
        gap_instruments.append("IMF RST contingent credit line")
    if residual_gap > 5e8:
        gap_instruments.append("Paris Club CDPC clause")
        gap_instruments.append("Debt-for-Nature swap with conservation fund")
    if event_info["parametric_suitable"]:
        gap_instruments.append(f"Parametric {event_type} trigger insurance (IAIS 2022 framework)")
    gap_instruments.append("FRLD simplified access grant window (Decision 2/CP.28)")

    return LDGapAnalysis(
        country_iso=country_iso,
        country_name=country_name,
        event_type=event_type,
        total_economic_loss_usd=round(total_economic_loss, 2),
        non_economic_loss_score=non_economic_score,
        insurance_covered_usd=round(insurance_covered, 2),
        frld_eligible_usd=round(frld_eligible, 2),
        global_shield_allocation_usd=round(global_shield, 2),
        wim_support_usd=round(wim_support, 2),
        residual_ld_gap_usd=round(residual_gap, 2),
        insurance_coverage_ratio=coverage_ratio,
        gap_financing_instruments=gap_instruments,
    )


def aggregate_ld_portfolio(portfolio: Dict[str, Any]) -> LDPortfolioResult:
    """Aggregate L&D exposure and coverage metrics across a multi-country portfolio."""
    portfolio_id = portfolio.get("portfolio_id", "default")
    rng = random.Random(hash(str(portfolio_id)) & 0xFFFFFFFF)

    holdings = portfolio.get("holdings", [])
    total_exposure = float(portfolio.get("total_aum_usd", rng.uniform(1e9, 5e10)))

    total_ld = 0.0
    v20_exposure = 0.0
    parametric_covered = 0.0
    residual_gap = 0.0
    expected_payout = 0.0
    loss_event_counts: Dict[str, int] = {}
    uninsured: List[str] = []

    for h in holdings:
        iso = h.get("country_iso", "")
        exp = float(h.get("exposure_usd", total_exposure * rng.uniform(0.01, 0.05)))
        event_type = h.get("dominant_event_type", rng.choice(list(LOSS_EVENT_TYPES.keys())))
        event_info = LOSS_EVENT_TYPES.get(event_type, LOSS_EVENT_TYPES["flood"])

        ld_rate = rng.uniform(0.005, 0.03)
        ld = exp * ld_rate
        total_ld += ld

        if iso in V20_MEMBERS:
            v20_exposure += exp

        ins_pen = event_info["insurance_penetration_typical"] + rng.uniform(-0.03, 0.05)
        ins_pen = max(0, min(0.8, ins_pen))
        par_cov = exp * ins_pen if event_info["parametric_suitable"] else 0
        parametric_covered += par_cov

        res_gap = ld * (1 - ins_pen) * rng.uniform(0.5, 0.9)
        residual_gap += res_gap

        ann_payout = ld * ins_pen * rng.uniform(0.3, 0.7)
        expected_payout += ann_payout

        loss_event_counts[event_type] = loss_event_counts.get(event_type, 0) + 1

        if ins_pen < 0.05:
            uninsured.append(iso)

    top_events = sorted(loss_event_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    top_event_types = [e[0] for e in top_events]

    parametric_coverage_ratio = parametric_covered / total_exposure if total_exposure else 0
    v20_concentration = v20_exposure / total_exposure if total_exposure else 0

    recommendations = []
    if v20_concentration > 0.40:
        recommendations.append("High V20 concentration — consider Global Shield portfolio insurance facility")
    if parametric_coverage_ratio < 0.30:
        recommendations.append("Increase parametric coverage; target 30%+ per IAIS 2022 guidance")
    if len(uninsured) > 3:
        recommendations.append(f"{len(uninsured)} countries uninsured — engage InsuResilience for structured solutions")
    if residual_gap / total_ld > 0.50:
        recommendations.append("Residual L&D gap >50% — pursue FRLD grants and IMF RST for top exposures")
    recommendations.append("Integrate WIM Santiago Network TA for capacity building in uninsured markets")

    return LDPortfolioResult(
        portfolio_id=portfolio_id,
        total_portfolio_exposure_usd=round(total_exposure, 2),
        total_ld_exposure_usd=round(total_ld, 2),
        v20_concentration_pct=round(v20_concentration * 100, 2),
        parametric_coverage_ratio=round(parametric_coverage_ratio, 4),
        residual_ld_gap_usd=round(residual_gap, 2),
        expected_annual_ld_payout_usd=round(expected_payout, 2),
        top_loss_event_types=top_event_types,
        uninsured_countries=uninsured[:10],
        recommendations=recommendations,
    )
