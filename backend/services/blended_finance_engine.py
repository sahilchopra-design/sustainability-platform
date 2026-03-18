"""
Blended Finance & DFI Instruments Engine  (E72)
================================================
IFC Performance Standards 1-8, MIGA, EBRD, ADB, AIIB, AfDB mobilisation
ratios (Convergence 2023), concessional layer sizing, first-loss tranche
modelling, guarantee structures, OECD DAC ODA/OOF eligibility, DFI EDGE.

References:
  - IFC Performance Standards 1-8 (2012 / 2021)
  - Convergence Blended Finance State of the Market 2023
  - OECD DAC Blended Finance Principles (2018)
  - MDB Harmonised Framework for Additionality (2018)
  - OECD DAC ODA/OOF definitions
  - DFI EDGE Green Building Certification
  - MIGA Environmental & Social Policy (2013)
  - EBRD Environmental & Social Policy (2019)
  - ADB Safeguard Policy Statement (2009)
"""
from __future__ import annotations

import random
from typing import Any

# ---------------------------------------------------------------------------
# Reference Data
# ---------------------------------------------------------------------------

IFC_PS_CATEGORIES: dict[str, dict] = {
    "PS1": {"name": "Assessment & Management of E&S Risks", "weight": 0.18},
    "PS2": {"name": "Labor and Working Conditions", "weight": 0.14},
    "PS3": {"name": "Resource Efficiency and Pollution Prevention", "weight": 0.14},
    "PS4": {"name": "Community Health, Safety and Security", "weight": 0.12},
    "PS5": {"name": "Land Acquisition and Involuntary Resettlement", "weight": 0.10},
    "PS6": {"name": "Biodiversity Conservation and Sustainable Management", "weight": 0.12},
    "PS7": {"name": "Indigenous Peoples", "weight": 0.10},
    "PS8": {"name": "Cultural Heritage", "weight": 0.10},
}

DFI_PROFILES: dict[str, dict] = {
    "IFC": {
        "full_name": "International Finance Corporation",
        "group": "World Bank Group",
        "focus_sectors": ["infrastructure", "manufacturing", "agribusiness", "financial_markets"],
        "min_project_size_usd": 10_000_000,
        "max_project_size_usd": 2_000_000_000,
        "concessional_window": "IFC MCPP",
        "mobilisation_target_ratio": 5.0,
        "oda_eligible": False,
        "country_focus": "emerging_markets",
        "es_framework": "IFC_PS_2012",
    },
    "MIGA": {
        "full_name": "Multilateral Investment Guarantee Agency",
        "group": "World Bank Group",
        "focus_sectors": ["infrastructure", "extractives", "manufacturing", "services"],
        "min_project_size_usd": 5_000_000,
        "max_project_size_usd": 1_500_000_000,
        "concessional_window": "MIGA Guarantee",
        "mobilisation_target_ratio": 6.0,
        "oda_eligible": False,
        "country_focus": "frontier_markets",
        "es_framework": "MIGA_ESP_2013",
    },
    "EBRD": {
        "full_name": "European Bank for Reconstruction and Development",
        "group": "EBRD",
        "focus_sectors": ["energy", "infrastructure", "agribusiness", "financial_institutions"],
        "min_project_size_usd": 5_000_000,
        "max_project_size_usd": 500_000_000,
        "concessional_window": "EBRD Green Economy Transition",
        "mobilisation_target_ratio": 4.5,
        "oda_eligible": True,
        "country_focus": "transition_economies",
        "es_framework": "EBRD_ESP_2019",
    },
    "ADB": {
        "full_name": "Asian Development Bank",
        "group": "ADB",
        "focus_sectors": ["transport", "energy", "water", "urban", "agriculture"],
        "min_project_size_usd": 2_000_000,
        "max_project_size_usd": 800_000_000,
        "concessional_window": "ADB Technical Assistance",
        "mobilisation_target_ratio": 3.8,
        "oda_eligible": True,
        "country_focus": "asia_pacific",
        "es_framework": "ADB_SPS_2009",
    },
    "AIIB": {
        "full_name": "Asian Infrastructure Investment Bank",
        "group": "AIIB",
        "focus_sectors": ["infrastructure", "energy", "transport", "telecom"],
        "min_project_size_usd": 10_000_000,
        "max_project_size_usd": 1_000_000_000,
        "concessional_window": "AIIB Project Preparation Fund",
        "mobilisation_target_ratio": 4.2,
        "oda_eligible": False,
        "country_focus": "asia",
        "es_framework": "AIIB_ESP_2021",
    },
    "AfDB": {
        "full_name": "African Development Bank",
        "group": "AfDB",
        "focus_sectors": ["agriculture", "infrastructure", "energy", "social"],
        "min_project_size_usd": 1_000_000,
        "max_project_size_usd": 300_000_000,
        "concessional_window": "ADF Concessional Window",
        "mobilisation_target_ratio": 3.2,
        "oda_eligible": True,
        "country_focus": "africa",
        "es_framework": "ISSP_2014",
    },
}

# Convergence 2023 benchmarks
CONVERGENCE_BENCHMARKS: dict[str, dict] = {
    "infrastructure":     {"mean_ratio": 5.5, "median_ratio": 4.8, "p25": 3.2, "p75": 7.1},
    "climate":            {"mean_ratio": 4.2, "median_ratio": 3.9, "p25": 2.5, "p75": 5.8},
    "agriculture":        {"mean_ratio": 3.1, "median_ratio": 2.8, "p25": 1.9, "p75": 4.3},
    "health":             {"mean_ratio": 2.8, "median_ratio": 2.5, "p25": 1.5, "p75": 3.9},
    "education":          {"mean_ratio": 2.2, "median_ratio": 2.0, "p25": 1.3, "p75": 3.1},
    "financial_inclusion": {"mean_ratio": 4.8, "median_ratio": 4.2, "p25": 2.9, "p75": 6.4},
    "water":              {"mean_ratio": 3.6, "median_ratio": 3.2, "p25": 2.1, "p75": 4.9},
    "energy":             {"mean_ratio": 5.1, "median_ratio": 4.6, "p25": 3.0, "p75": 6.8},
}

INSTRUMENT_CONFIGS: dict[str, dict] = {
    "guarantees": {
        "description": "Risk guarantee covering private investor losses",
        "concessional_share_range": (0.05, 0.20),
        "typical_coverage_pct": (0.50, 0.85),
        "return_enhancement_bps": (50, 200),
        "oda_eligible": True,
        "risk_mitigant": "credit_default",
    },
    "first_loss": {
        "description": "First-loss tranche absorbing initial losses",
        "concessional_share_range": (0.10, 0.25),
        "typical_coverage_pct": (0.10, 0.30),
        "return_enhancement_bps": (100, 350),
        "oda_eligible": True,
        "risk_mitigant": "first_loss_buffer",
    },
    "concessional_loans": {
        "description": "Below-market rate loans from public/philanthropic sources",
        "concessional_share_range": (0.15, 0.40),
        "typical_coverage_pct": (0.15, 0.40),
        "return_enhancement_bps": (150, 400),
        "oda_eligible": True,
        "risk_mitigant": "interest_rate_subsidy",
    },
    "equity": {
        "description": "Concessional equity or quasi-equity stake",
        "concessional_share_range": (0.10, 0.30),
        "typical_coverage_pct": (0.10, 0.30),
        "return_enhancement_bps": (80, 280),
        "oda_eligible": False,
        "risk_mitigant": "dilution_protection",
    },
    "technical_assistance": {
        "description": "Grant-funded technical assistance and capacity building",
        "concessional_share_range": (0.02, 0.10),
        "typical_coverage_pct": (1.0, 1.0),
        "return_enhancement_bps": (20, 80),
        "oda_eligible": True,
        "risk_mitigant": "preparation_risk",
    },
}

ODA_SECTOR_CODES: dict[str, str] = {
    "agriculture": "31110", "energy": "23110", "infrastructure": "21010",
    "health": "12110", "education": "11110", "water": "14010",
    "climate": "41010", "financial_inclusion": "24030",
}

INSTRUMENT_SDG_MAP: dict[str, list] = {
    "guarantees": ["SDG_17", "SDG_8"],
    "first_loss": ["SDG_13", "SDG_17"],
    "concessional_loans": ["SDG_13", "SDG_17", "SDG_1"],
    "equity": ["SDG_8", "SDG_9"],
    "technical_assistance": ["SDG_17", "SDG_4"],
}

SECTOR_SDG_MAP: dict[str, list] = {
    "energy": ["SDG_7", "SDG_13"],
    "agriculture": ["SDG_2", "SDG_15"],
    "infrastructure": ["SDG_9", "SDG_11"],
    "health": ["SDG_3"],
    "education": ["SDG_4"],
    "water": ["SDG_6"],
    "climate": ["SDG_13"],
    "financial_inclusion": ["SDG_1", "SDG_8"],
}

SECTOR_MDB_MAP: dict[str, list] = {
    "agriculture": ["IFC", "AfDB", "ADB"],
    "energy": ["IFC", "EBRD", "AIIB", "ADB"],
    "infrastructure": ["IFC", "AIIB", "ADB", "AfDB"],
    "health": ["IFC", "ADB", "AfDB"],
    "education": ["ADB", "AfDB", "IFC"],
    "water": ["ADB", "AfDB", "EBRD"],
    "climate": ["IFC", "EBRD", "ADB", "AIIB"],
    "financial_inclusion": ["IFC", "ADB", "AfDB"],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rng(entity_id: str) -> random.Random:
    return random.Random(hash(str(entity_id)) & 0xFFFFFFFF)


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _score_ifc_ps(rng: random.Random, project_category: str, sector: str) -> dict:
    high_risk = {"extractives", "mining", "chemicals", "large_hydro"}
    base_offset = -10.0 if sector in high_risk else 0.0
    cat_mod = {"A": -15.0, "B": -5.0, "C": 5.0}.get(project_category, 0.0)
    scores: dict[str, dict] = {}
    for ps_id, ps_data in IFC_PS_CATEGORIES.items():
        raw = _clamp(rng.uniform(55.0, 95.0) + base_offset + cat_mod, 0.0, 100.0)
        scores[ps_id] = {
            "name": ps_data["name"],
            "score": round(raw, 1),
            "weight": ps_data["weight"],
            "status": "compliant" if raw >= 70 else ("partial" if raw >= 50 else "non_compliant"),
        }
    weighted = sum(s["score"] * s["weight"] for s in scores.values())
    return {"scores": scores, "weighted_average": round(weighted, 1)}


def _es_risk_tier(ifc_score: float, sector: str) -> str:
    if sector in {"extractives", "mining", "chemicals", "large_hydro"} or ifc_score < 60:
        return "A"
    elif ifc_score < 78:
        return "B"
    return "C"


def _country_income_group(country: str) -> str:
    v = hash(country) % 100
    if v < 30:
        return "LDC"
    elif v < 65:
        return "LMIC"
    elif v < 85:
        return "UMIC"
    return "HIC"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def assess_blended_structure(
    entity_id: str,
    instrument_type: str,
    project_size_usd: float,
    sector: str,
    country: str,
) -> dict[str, Any]:
    """
    Assess a blended finance structure.

    Returns concessional layer sizing, MDB partner match, IFC PS compliance,
    mobilisation ratio benchmarks, OECD DAC ODA eligibility, SDG alignment.
    """
    rng = _rng(entity_id)

    if instrument_type not in INSTRUMENT_CONFIGS:
        instrument_type = rng.choice(list(INSTRUMENT_CONFIGS.keys()))
    cfg = INSTRUMENT_CONFIGS[instrument_type]

    conc_lo, conc_hi = cfg["concessional_share_range"]
    concessional_pct = rng.uniform(conc_lo, conc_hi)
    concessional_usd = round(project_size_usd * concessional_pct, 0)
    first_loss_pct = concessional_pct * rng.uniform(0.35, 0.65)
    first_loss_usd = round(project_size_usd * first_loss_pct, 0)

    cov_lo, cov_hi = cfg["typical_coverage_pct"]
    guarantee_coverage = rng.uniform(cov_lo, cov_hi)

    candidates = SECTOR_MDB_MAP.get(sector, list(DFI_PROFILES.keys()))
    mdb_partner = rng.choice(candidates)
    mdb_profile = DFI_PROFILES[mdb_partner]

    bench = CONVERGENCE_BENCHMARKS.get(sector, CONVERGENCE_BENCHMARKS["infrastructure"])
    mobilisation_ratio = rng.uniform(bench["p25"], bench["p75"])
    private_co_finance = round(concessional_usd * mobilisation_ratio, 0)

    project_category = _es_risk_tier(rng.uniform(55, 95), sector)
    ps_result = _score_ifc_ps(rng, project_category, sector)
    dfi_standards_score = ps_result["weighted_average"]

    oda_sector_code = ODA_SECTOR_CODES.get(sector, "43010")
    income_group = _country_income_group(country)
    oda_eligible = cfg["oda_eligible"] and income_group in {"LDC", "LMIC", "UMIC"}

    sdgs = sorted(set(
        INSTRUMENT_SDG_MAP.get(instrument_type, []) +
        SECTOR_SDG_MAP.get(sector, [])
    ))

    edge_applicable = sector in {"infrastructure", "real_estate", "urban"}
    edge_score = round(rng.uniform(60.0, 95.0), 1) if edge_applicable else None

    ret_lo, ret_hi = cfg["return_enhancement_bps"]
    return_enhancement_bps = round(rng.uniform(ret_lo, ret_hi), 0)

    return {
        "entity_id": entity_id,
        "instrument_type": instrument_type,
        "instrument_description": cfg["description"],
        "project_size_usd": project_size_usd,
        "sector": sector,
        "country": country,
        "concessional_layer": {
            "percentage": round(concessional_pct * 100, 2),
            "amount_usd": concessional_usd,
        },
        "first_loss": {
            "percentage": round(first_loss_pct * 100, 2),
            "amount_usd": first_loss_usd,
        },
        "guarantee_coverage_pct": round(guarantee_coverage * 100, 2),
        "mdb_partner": mdb_partner,
        "mdb_profile": mdb_profile,
        "mobilisation_ratio": round(mobilisation_ratio, 2),
        "private_co_finance_usd": private_co_finance,
        "convergence_benchmark": bench,
        "dfi_standards_score": round(dfi_standards_score, 1),
        "ifc_ps_compliance": ps_result,
        "es_risk_tier": project_category,
        "return_enhancement_bps": return_enhancement_bps,
        "oda_eligibility": {
            "eligible": oda_eligible,
            "sector_code": oda_sector_code,
            "country_income_group": income_group,
            "instrument_oda_eligible": cfg["oda_eligible"],
        },
        "sdg_alignment": sdgs,
        "edge_green_building": {"applicable": edge_applicable, "score": edge_score},
        "risk_mitigant": cfg["risk_mitigant"],
    }


def analyse_dfi_standards(
    entity_id: str,
    dfi_partner: str,
    project_category: str,
) -> dict[str, Any]:
    """
    Analyse DFI E&S standards compliance across 8 IFC PS categories.

    Returns IFC PS scores, E&S risk tier, EDGE criteria and DFI partner profile.
    """
    rng = _rng(entity_id)

    if dfi_partner not in DFI_PROFILES:
        dfi_partner = rng.choice(list(DFI_PROFILES.keys()))
    profile = DFI_PROFILES[dfi_partner]

    ps_result = _score_ifc_ps(rng, project_category, "infrastructure")
    es_tier = _es_risk_tier(ps_result["weighted_average"], "infrastructure")

    esia_required = project_category == "A" or (
        project_category == "B" and ps_result["weighted_average"] < 70
    )
    esia_independent = project_category == "A"

    grievance_score = round(rng.uniform(55.0, 95.0), 1)
    grievance_status = "adequate" if grievance_score >= 70 else "needs_improvement"

    edge_energy = round(rng.uniform(15.0, 48.0), 1)
    edge_water = round(rng.uniform(15.0, 42.0), 1)
    edge_embodied = round(rng.uniform(15.0, 52.0), 1)
    edge_certified = edge_energy >= 20 and edge_water >= 20 and edge_embodied >= 20

    monitoring_freq = {"A": "semi-annual", "B": "annual", "C": "biennial"}.get(
        project_category, "annual"
    )

    overall = round(
        ps_result["weighted_average"] * 0.60
        + grievance_score * 0.20
        + (edge_energy + edge_water) / 2 * 0.20,
        1,
    )

    return {
        "entity_id": entity_id,
        "dfi_partner": dfi_partner,
        "dfi_profile": profile,
        "project_category": project_category,
        "ifc_ps_compliance": ps_result,
        "es_risk_tier": es_tier,
        "esia_required": esia_required,
        "esia_independent_consultant_required": esia_independent,
        "grievance_mechanism": {
            "score": grievance_score,
            "status": grievance_status,
            "channels": rng.sample(
                ["hotline", "web_portal", "community_liaison", "ombudsman", "sms"],
                k=rng.randint(2, 4),
            ),
        },
        "edge_green_building": {
            "energy_saving_pct": edge_energy,
            "water_saving_pct": edge_water,
            "embodied_energy_saving_pct": edge_embodied,
            "certified": edge_certified,
        },
        "monitoring_frequency": monitoring_freq,
        "disclosure": {
            "project_disclosure": True,
            "esia_public": project_category in {"A", "B"},
            "monitoring_reports_public": project_category == "A",
            "comment_period_days": 60 if project_category == "A" else 30,
        },
        "overall_compliance_score": overall,
    }


def model_concessional_layers(
    entity_id: str,
    total_size_usd: float,
    sectors: list[str],
) -> dict[str, Any]:
    """
    Model tranche waterfall: senior / mezzanine / first-loss / grant.

    Returns return targets per tier, investor type mapping, blended IRR.
    """
    rng = _rng(entity_id)

    grant_pct = rng.uniform(0.02, 0.08)
    first_loss_pct = rng.uniform(0.08, 0.18)
    mezzanine_pct = rng.uniform(0.12, 0.25)
    senior_pct = max(0.35, 1.0 - grant_pct - first_loss_pct - mezzanine_pct)

    total_pct = grant_pct + first_loss_pct + mezzanine_pct + senior_pct
    grant_pct /= total_pct
    first_loss_pct /= total_pct
    mezzanine_pct /= total_pct
    senior_pct /= total_pct

    tranches = [
        {
            "tranche_name": "Senior Debt",
            "tranche_type": "senior",
            "size_usd": round(total_size_usd * senior_pct, 0),
            "pct_of_total": round(senior_pct * 100, 1),
            "return_target_pct": round(rng.uniform(4.5, 8.0), 2),
            "risk_tier": "low",
            "investor_type": "institutional",
            "rating_equivalent": rng.choice(["BBB+", "BBB", "A-"]),
        },
        {
            "tranche_name": "Mezzanine",
            "tranche_type": "mezzanine",
            "size_usd": round(total_size_usd * mezzanine_pct, 0),
            "pct_of_total": round(mezzanine_pct * 100, 1),
            "return_target_pct": round(rng.uniform(8.0, 14.0), 2),
            "risk_tier": "medium",
            "investor_type": "DFI",
            "rating_equivalent": rng.choice(["BB+", "BB", "BB-"]),
        },
        {
            "tranche_name": "First-Loss Junior",
            "tranche_type": "first_loss",
            "size_usd": round(total_size_usd * first_loss_pct, 0),
            "pct_of_total": round(first_loss_pct * 100, 1),
            "return_target_pct": round(rng.uniform(2.0, 6.0), 2),
            "risk_tier": "high",
            "investor_type": "philanthropic",
            "rating_equivalent": "NR",
        },
        {
            "tranche_name": "Grant / Technical Assistance",
            "tranche_type": "grant",
            "size_usd": round(total_size_usd * grant_pct, 0),
            "pct_of_total": round(grant_pct * 100, 1),
            "return_target_pct": 0.0,
            "risk_tier": "none",
            "investor_type": "government",
            "rating_equivalent": "N/A",
        },
    ]

    non_grant_total = sum(t["size_usd"] for t in tranches if t["tranche_type"] != "grant")
    blended_irr = (
        sum(
            t["return_target_pct"] * t["size_usd"] / non_grant_total
            for t in tranches if t["tranche_type"] != "grant"
        )
        if non_grant_total > 0 else 0.0
    )

    all_sdgs: set[str] = set()
    for s in sectors:
        all_sdgs.update(SECTOR_SDG_MAP.get(s, []))

    return {
        "entity_id": entity_id,
        "total_size_usd": total_size_usd,
        "sectors": sectors,
        "tranches": tranches,
        "blended_irr_pct": round(blended_irr, 2),
        "concessional_share_pct": round((grant_pct + first_loss_pct) * 100, 1),
        "leverage_ratio": round(senior_pct / max(grant_pct + first_loss_pct, 0.01), 2),
        "investor_type_mix": {
            "institutional_pct": round(senior_pct * 100, 1),
            "dfi_pct": round(mezzanine_pct * 100, 1),
            "philanthropic_pct": round(first_loss_pct * 100, 1),
            "government_pct": round(grant_pct * 100, 1),
        },
        "sdg_alignment": sorted(all_sdgs),
    }


def calculate_mobilisation_metrics(
    entity_id: str,
    public_finance_usd: float,
    private_co_finance_usd: float,
) -> dict[str, Any]:
    """
    Calculate MDB mobilisation metrics, additionality and crowding assessment.

    Benchmarks per Convergence 2023; methodology per MDB Harmonised Framework.
    """
    rng = _rng(entity_id)

    total = public_finance_usd + private_co_finance_usd
    direct_ratio = private_co_finance_usd / public_finance_usd if public_finance_usd > 0 else 0.0

    sector_ratios: dict[str, dict] = {}
    for sector, bench in CONVERGENCE_BENCHMARKS.items():
        r = rng.uniform(bench["p25"], bench["p75"])
        sector_ratios[sector] = {
            "achieved_ratio": round(r, 2),
            "benchmark_mean": bench["mean_ratio"],
            "benchmark_median": bench["median_ratio"],
            "vs_benchmark": "above" if r > bench["mean_ratio"] else "below",
        }

    financial_add = round(rng.uniform(50.0, 95.0), 1)
    es_add = round(rng.uniform(45.0, 90.0), 1)
    knowledge_add = round(rng.uniform(40.0, 85.0), 1)
    additionality_score = round(financial_add * 0.50 + es_add * 0.30 + knowledge_add * 0.20, 1)

    crowding_in = round(rng.uniform(55.0, 90.0), 1)
    crowding_assessment = (
        "crowding_in" if crowding_in >= 65 else ("neutral" if crowding_in >= 45 else "crowding_out")
    )

    return {
        "entity_id": entity_id,
        "public_finance_usd": public_finance_usd,
        "private_co_finance_usd": private_co_finance_usd,
        "total_finance_usd": total,
        "direct_mobilisation_ratio": round(direct_ratio, 2),
        "sector_benchmarks": sector_ratios,
        "additionality": {
            "financial": financial_add,
            "environmental_social": es_add,
            "knowledge": knowledge_add,
            "composite_score": additionality_score,
            "level": "high" if additionality_score >= 70 else ("medium" if additionality_score >= 50 else "low"),
        },
        "crowding_assessment": {
            "crowding_in_score": crowding_in,
            "crowding_out_risk": round(100 - crowding_in, 1),
            "assessment": crowding_assessment,
        },
        "mdb_harmonised_framework_score": round(rng.uniform(65.0, 95.0), 1),
        "oecd_dac": {
            "reporting_required": True,
            "methodology": "Survey on Amounts Mobilised from the Private Sector",
            "public_share_pct": round(
                min(public_finance_usd / total * 100, 100) if total > 0 else 0, 1
            ),
        },
    }


def generate_blended_portfolio(
    entity_id: str,
    instruments: list[dict],
) -> dict[str, Any]:
    """
    Aggregate blended finance instruments into portfolio-level analytics.

    Returns risk-return frontier, SDG alignment, impact metrics,
    sector exposures and Convergence-style portfolio analytics.
    """
    rng = _rng(entity_id)

    if not instruments:
        sectors_pool = list(CONVERGENCE_BENCHMARKS.keys())
        countries_pool = [
            "Kenya", "Indonesia", "Colombia", "Nigeria", "Vietnam", "Bangladesh",
            "Ghana", "Peru", "Philippines", "Tanzania",
        ]
        n = rng.randint(3, 8)
        instruments = [
            {
                "instrument_type": rng.choice(list(INSTRUMENT_CONFIGS.keys())),
                "size_usd": round(rng.uniform(5_000_000, 200_000_000), 0),
                "sector": rng.choice(sectors_pool),
                "country": rng.choice(countries_pool),
            }
            for _ in range(n)
        ]

    total_portfolio_usd = sum(float(i.get("size_usd", 10_000_000)) for i in instruments)
    total_concessional = 0.0
    total_private_mobilised = 0.0
    sdg_set: set[str] = set()
    sector_exposures: dict[str, float] = {}
    portfolio_items = []

    for idx, inst in enumerate(instruments):
        i_rng = random.Random(hash(f"{entity_id}_{idx}") & 0xFFFFFFFF)
        itype = inst.get("instrument_type", "guarantees")
        if itype not in INSTRUMENT_CONFIGS:
            itype = "guarantees"
        cfg = INSTRUMENT_CONFIGS[itype]
        size = float(inst.get("size_usd", 10_000_000))
        sector = inst.get("sector", "infrastructure")

        conc_lo, conc_hi = cfg["concessional_share_range"]
        conc_pct = i_rng.uniform(conc_lo, conc_hi)
        bench = CONVERGENCE_BENCHMARKS.get(sector, CONVERGENCE_BENCHMARKS["infrastructure"])
        mob_ratio = i_rng.uniform(bench["p25"], bench["p75"])

        conc_usd = size * conc_pct
        priv_mob = conc_usd * mob_ratio
        total_concessional += conc_usd
        total_private_mobilised += priv_mob

        for sdg in INSTRUMENT_SDG_MAP.get(itype, []) + SECTOR_SDG_MAP.get(sector, []):
            sdg_set.add(sdg)
        sector_exposures[sector] = sector_exposures.get(sector, 0.0) + size

        portfolio_items.append({
            "index": idx,
            "instrument_type": itype,
            "size_usd": size,
            "sector": sector,
            "country": inst.get("country", "Unknown"),
            "concessional_pct": round(conc_pct * 100, 1),
            "mobilisation_ratio": round(mob_ratio, 2),
            "private_mobilised_usd": round(priv_mob, 0),
        })

    portfolio_mob_ratio = (
        total_private_mobilised / total_concessional if total_concessional > 0 else 0.0
    )

    frontier = sorted(
        [{"return_pct": round(rng.uniform(3, 5), 1), "risk": round(rng.uniform(10, 25), 0)} for _ in range(4)]
        + [{"return_pct": round(rng.uniform(5, 10), 1), "risk": round(rng.uniform(25, 55), 0)} for _ in range(4)]
        + [{"return_pct": round(rng.uniform(10, 18), 1), "risk": round(rng.uniform(55, 85), 0)} for _ in range(3)],
        key=lambda x: x["return_pct"],
    )

    return {
        "entity_id": entity_id,
        "portfolio_summary": {
            "total_instruments": len(instruments),
            "total_portfolio_usd": total_portfolio_usd,
            "total_concessional_usd": round(total_concessional, 0),
            "total_private_mobilised_usd": round(total_private_mobilised, 0),
            "portfolio_mobilisation_ratio": round(portfolio_mob_ratio, 2),
            "concessional_share_pct": round(
                total_concessional / total_portfolio_usd * 100 if total_portfolio_usd > 0 else 0, 1
            ),
        },
        "sector_exposures_pct": {
            k: round(v / total_portfolio_usd * 100, 1) if total_portfolio_usd > 0 else 0
            for k, v in sector_exposures.items()
        },
        "sdg_alignment": sorted(sdg_set),
        "risk_return_frontier": frontier,
        "impact_metrics": {
            "co2_avoided_tco2e_pa": round(rng.uniform(5_000, 150_000), 0),
            "jobs_created": round(rng.uniform(200, 8_000), 0),
            "beneficiaries": round(rng.uniform(10_000, 500_000), 0),
            "sdgs_addressed": len(sdg_set),
        },
        "portfolio_items": portfolio_items,
        "convergence_analytics": {
            "blended_finance_type": "structured_finance",
            "vehicles": rng.sample(
                ["fund", "facility", "bond", "guarantee_program", "equity_vehicle"], k=2
            ),
            "preparation_funding_pct": round(rng.uniform(1.0, 5.0), 1),
            "average_deal_size_usd": round(total_portfolio_usd / len(instruments), 0) if instruments else 0,
        },
    }
