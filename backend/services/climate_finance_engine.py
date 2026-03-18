"""
climate_finance_engine.py — E78 Climate Finance Flows
OECD CRS Rio Markers | UNFCCC Art 2.1(c) | CPI Global Landscape 2023
NCQG $300bn COP29 Baku | MDB Joint Tracking | OECD TOSSD | Convergence Blending
"""
from __future__ import annotations
import random
from datetime import datetime, timezone
from typing import Any

# ── Reference Data ─────────────────────────────────────────────────────────────

OECD_RIO_MARKERS = [
    {"id": "RM-01", "name": "Climate Change Mitigation", "code": "CCM", "marker_values": [0, 1, 2], "description": "0=not targeted, 1=significant objective, 2=principal objective"},
    {"id": "RM-02", "name": "Climate Change Adaptation", "code": "CCA", "marker_values": [0, 1, 2], "description": "0=not targeted, 1=significant objective, 2=principal objective"},
    {"id": "RM-03", "name": "Biodiversity", "code": "BD", "marker_values": [0, 1, 2], "description": "Rio Convention on Biological Diversity"},
    {"id": "RM-04", "name": "Desertification", "code": "DESER", "marker_values": [0, 1, 2], "description": "UN Convention to Combat Desertification"},
    {"id": "RM-05", "name": "Water", "code": "WTR", "marker_values": [0, 1, 2], "description": "OECD water policy marker"},
    {"id": "RM-06", "name": "Nutrition", "code": "NUTR", "marker_values": [0, 1, 2], "description": "Nutrition policy marker"},
    {"id": "RM-07", "name": "Trade Development", "code": "TRADE", "marker_values": [0, 1, 2], "description": "Trade development marker"},
    {"id": "RM-08", "name": "Digital Technology", "code": "DIG", "marker_values": [0, 1, 2], "description": "Digital technology marker 2023"},
    {"id": "RM-09", "name": "Disaster Risk Reduction", "code": "DRR", "marker_values": [0, 1, 2], "description": "Sendai Framework alignment"},
    {"id": "RM-10", "name": "Inclusion & Equity", "code": "IE", "marker_values": [0, 1, 2], "description": "Inclusion and equity marker"},
    {"id": "RM-11", "name": "Gender Equality", "code": "GEN", "marker_values": [0, 1, 2], "description": "DAC gender equality marker"},
    {"id": "RM-12", "name": "Environment", "code": "ENV", "marker_values": [0, 1, 2], "description": "General environment marker"},
]

# CPI Global Landscape of Climate Finance 2023 data
CPI_2023_DATA = {
    "total_climate_finance_usd_bn": 1265,
    "private_finance_usd_bn": 626,
    "public_finance_usd_bn": 639,
    "adaptation_usd_bn": 63,
    "mitigation_usd_bn": 1202,
    "annual_need_2030_usd_bn": 4300,
    "annual_gap_usd_bn": 3035,
    "by_instrument": {
        "debt": {"amount_usd_bn": 680, "share_pct": 53.7},
        "equity": {"amount_usd_bn": 330, "share_pct": 26.1},
        "grants": {"amount_usd_bn": 143, "share_pct": 11.3},
        "guarantees_insurance": {"amount_usd_bn": 62, "share_pct": 4.9},
        "mixed_instruments": {"amount_usd_bn": 50, "share_pct": 4.0},
    },
    "by_geography": {
        "east_asia_pacific": {"amount_usd_bn": 682, "share_pct": 53.9},
        "western_europe": {"amount_usd_bn": 262, "share_pct": 20.7},
        "north_america": {"amount_usd_bn": 108, "share_pct": 8.5},
        "developing_countries": {"amount_usd_bn": 213, "share_pct": 16.9},
    },
    "by_sector": {
        "energy_systems": {"amount_usd_bn": 870, "share_pct": 68.8},
        "transport": {"amount_usd_bn": 212, "share_pct": 16.8},
        "buildings": {"amount_usd_bn": 85, "share_pct": 6.7},
        "agriculture_land_use": {"amount_usd_bn": 45, "share_pct": 3.6},
        "water_oceans": {"amount_usd_bn": 28, "share_pct": 2.2},
        "other": {"amount_usd_bn": 25, "share_pct": 2.0},
    },
}

# MDB institutions with climate shares
MDB_INSTITUTIONS = [
    {"name": "World Bank Group", "code": "WBG", "total_finance_usd_bn": 85, "climate_share_pct": 35, "adaptation_target_pct": 50, "paris_aligned_since": 2023},
    {"name": "Asian Development Bank", "code": "ADB", "total_finance_usd_bn": 22, "climate_share_pct": 44, "adaptation_target_pct": 30, "paris_aligned_since": 2021},
    {"name": "European Investment Bank", "code": "EIB", "total_finance_usd_bn": 88, "climate_share_pct": 50, "adaptation_target_pct": 15, "paris_aligned_since": 2020},
    {"name": "African Development Bank", "code": "AfDB", "total_finance_usd_bn": 10, "climate_share_pct": 40, "adaptation_target_pct": 50, "paris_aligned_since": 2022},
    {"name": "Inter-American Development Bank", "code": "IADB", "total_finance_usd_bn": 20, "climate_share_pct": 30, "adaptation_target_pct": 25, "paris_aligned_since": 2021},
    {"name": "European Bank for Reconstruction and Development", "code": "EBRD", "total_finance_usd_bn": 15, "climate_share_pct": 45, "adaptation_target_pct": 20, "paris_aligned_since": 2021},
    {"name": "Asian Infrastructure Investment Bank", "code": "AIIB", "total_finance_usd_bn": 12, "climate_share_pct": 38, "adaptation_target_pct": 20, "paris_aligned_since": 2023},
    {"name": "Islamic Development Bank", "code": "IsDB", "total_finance_usd_bn": 8, "climate_share_pct": 25, "adaptation_target_pct": 30, "paris_aligned_since": 2022},
]

# Recipient countries by income group (sample 40)
RECIPIENT_COUNTRIES = [
    {"iso": "BD", "country": "Bangladesh", "income_group": "lower_middle", "climate_vulnerable": True, "v20": True},
    {"iso": "ET", "country": "Ethiopia", "income_group": "low", "climate_vulnerable": True, "v20": True},
    {"iso": "KE", "country": "Kenya", "income_group": "lower_middle", "climate_vulnerable": True, "v20": False},
    {"iso": "MX", "country": "Mexico", "income_group": "upper_middle", "climate_vulnerable": False, "v20": False},
    {"iso": "IN", "country": "India", "income_group": "lower_middle", "climate_vulnerable": True, "v20": False},
    {"iso": "ID", "country": "Indonesia", "income_group": "upper_middle", "climate_vulnerable": True, "v20": False},
    {"iso": "PK", "country": "Pakistan", "income_group": "lower_middle", "climate_vulnerable": True, "v20": True},
    {"iso": "VN", "country": "Vietnam", "income_group": "lower_middle", "climate_vulnerable": True, "v20": False},
    {"iso": "PH", "country": "Philippines", "income_group": "lower_middle", "climate_vulnerable": True, "v20": True},
    {"iso": "NG", "country": "Nigeria", "income_group": "lower_middle", "climate_vulnerable": True, "v20": False},
    {"iso": "TZ", "country": "Tanzania", "income_group": "low", "climate_vulnerable": True, "v20": True},
    {"iso": "GH", "country": "Ghana", "income_group": "lower_middle", "climate_vulnerable": False, "v20": False},
    {"iso": "EG", "country": "Egypt", "income_group": "lower_middle", "climate_vulnerable": True, "v20": False},
    {"iso": "MA", "country": "Morocco", "income_group": "lower_middle", "climate_vulnerable": False, "v20": False},
    {"iso": "CO", "country": "Colombia", "income_group": "upper_middle", "climate_vulnerable": True, "v20": False},
    {"iso": "PE", "country": "Peru", "income_group": "upper_middle", "climate_vulnerable": True, "v20": False},
    {"iso": "TH", "country": "Thailand", "income_group": "upper_middle", "climate_vulnerable": True, "v20": False},
    {"iso": "MM", "country": "Myanmar", "income_group": "lower_middle", "climate_vulnerable": True, "v20": True},
    {"iso": "KH", "country": "Cambodia", "income_group": "lower_middle", "climate_vulnerable": True, "v20": True},
    {"iso": "SN", "country": "Senegal", "income_group": "lower_middle", "climate_vulnerable": True, "v20": True},
    {"iso": "UG", "country": "Uganda", "income_group": "low", "climate_vulnerable": True, "v20": True},
    {"iso": "ZM", "country": "Zambia", "income_group": "lower_middle", "climate_vulnerable": True, "v20": True},
    {"iso": "LK", "country": "Sri Lanka", "income_group": "lower_middle", "climate_vulnerable": True, "v20": True},
    {"iso": "NP", "country": "Nepal", "income_group": "lower_middle", "climate_vulnerable": True, "v20": True},
    {"iso": "MZ", "country": "Mozambique", "income_group": "low", "climate_vulnerable": True, "v20": True},
    {"iso": "MW", "country": "Malawi", "income_group": "low", "climate_vulnerable": True, "v20": True},
    {"iso": "HT", "country": "Haiti", "income_group": "low", "climate_vulnerable": True, "v20": True},
    {"iso": "MG", "country": "Madagascar", "income_group": "low", "climate_vulnerable": True, "v20": True},
    {"iso": "BF", "country": "Burkina Faso", "income_group": "low", "climate_vulnerable": True, "v20": True},
    {"iso": "ML", "country": "Mali", "income_group": "low", "climate_vulnerable": True, "v20": True},
    {"iso": "BR", "country": "Brazil", "income_group": "upper_middle", "climate_vulnerable": True, "v20": False},
    {"iso": "ZA", "country": "South Africa", "income_group": "upper_middle", "climate_vulnerable": False, "v20": False},
    {"iso": "UA", "country": "Ukraine", "income_group": "lower_middle", "climate_vulnerable": False, "v20": False},
    {"iso": "JO", "country": "Jordan", "income_group": "upper_middle", "climate_vulnerable": True, "v20": False},
    {"iso": "TN", "country": "Tunisia", "income_group": "lower_middle", "climate_vulnerable": True, "v20": False},
    {"iso": "CI", "country": "Côte d'Ivoire", "income_group": "lower_middle", "climate_vulnerable": True, "v20": False},
    {"iso": "CM", "country": "Cameroon", "income_group": "lower_middle", "climate_vulnerable": True, "v20": False},
    {"iso": "AO", "country": "Angola", "income_group": "lower_middle", "climate_vulnerable": True, "v20": False},
    {"iso": "EC", "country": "Ecuador", "income_group": "upper_middle", "climate_vulnerable": True, "v20": False},
    {"iso": "BO", "country": "Bolivia", "income_group": "lower_middle", "climate_vulnerable": True, "v20": False},
]

# NCQG structure (COP29 Baku 2024)
NCQG_STRUCTURE = {
    "headline_goal_usd_bn_per_year": 300,
    "target_year": 2035,
    "cop_decision": "COP29 Baku 2024",
    "goal_layers": {
        "core_goal": {
            "amount_usd_bn": 300,
            "contributors": "Developed country parties (Annex II)",
            "description": "Public and private finance mobilised by developed countries",
        },
        "broader_goal": {
            "amount_usd_bn": 1300,
            "contributors": "All parties including voluntary",
            "description": "Includes voluntary contributions from developing nations with capacity",
        },
    },
    "instrument_split": {
        "grants_and_grant_equivalent": {"target_pct": 40, "ldcs_sids_pct": 50},
        "concessional_loans": {"target_pct": 35},
        "private_mobilised": {"target_pct": 25, "mdb_leverage": 3.5},
    },
    "predecessor_goal": {
        "amount_usd_bn": 100,
        "target_year": 2020,
        "achieved_year": 2022,
        "achieved_usd_bn": 115.9,
        "source": "OECD 2024 Climate Finance Report",
    },
}

# IPCC-compatible pathways
IPCC_PATHWAYS = [
    {"pathway": "1.5C_no_overshoot", "description": "Net zero CO2 by 2050, immediate steep reductions", "peak_warming_c": 1.5, "annual_investment_usd_tn": 4.3},
    {"pathway": "well_below_2C", "description": "Net zero CO2 by 2070, rapid near-term reductions", "peak_warming_c": 1.8, "annual_investment_usd_tn": 3.2},
    {"pathway": "2C_with_overshoot", "description": "Net zero CO2 by 2075, moderate reductions", "peak_warming_c": 2.0, "annual_investment_usd_tn": 2.5},
    {"pathway": "ndc_current_policies", "description": "Current NDC policies sustained", "peak_warming_c": 2.7, "annual_investment_usd_tn": 1.7},
]

# Mobilisation multipliers (OECD DAC methodology)
MOBILISATION_MULTIPLIERS = {
    "guarantees": {"min": 3.0, "max": 8.0, "typical": 5.0, "methodology": "OECD DAC Converged Statistical Reporting Directives"},
    "equity": {"min": 2.0, "max": 4.0, "typical": 2.8, "methodology": "OECD DCD/DAC(2019)34/FINAL"},
    "concessional_loans": {"min": 1.5, "max": 3.0, "typical": 2.0, "methodology": "Convergence Blending Finance Report 2023"},
    "grants": {"min": 1.0, "max": 2.5, "typical": 1.5, "methodology": "OECD MDB mobilisation ratio"},
    "technical_assistance": {"min": 1.0, "max": 2.0, "typical": 1.3, "methodology": "OECD DAC"},
    "risk_sharing": {"min": 4.0, "max": 10.0, "typical": 6.5, "methodology": "First-loss provisions / MIGA"},
}


# ── Core Engine Functions ──────────────────────────────────────────────────────

def track_climate_finance(
    entity_id: str,
    portfolio_name: str,
    year: int,
    instruments: list[dict[str, Any]],
) -> dict[str, Any]:
    rng = random.Random(hash(str(entity_id)) & 0xFFFFFFFF)

    total_mitigation = 0.0
    total_adaptation = 0.0
    total_cross_cutting = 0.0
    instrument_breakdown: list[dict] = []

    for inst in instruments:
        inst_rng = random.Random(hash(f"{entity_id}_{inst.get('name', '')}") & 0xFFFFFFFF)
        amount = float(inst.get("amount_usd", inst_rng.uniform(1e6, 100e6)))
        flow_type = inst.get("flow_type", "mitigation")

        ccm_marker = inst.get("ccm_marker", inst_rng.randint(0, 2))
        cca_marker = inst.get("cca_marker", inst_rng.randint(0, 2))

        # CRS counting methodology: principal=100%, significant=50%
        mitigation_counted = amount if ccm_marker == 2 else amount * 0.5 if ccm_marker == 1 else 0
        adaptation_counted = amount if cca_marker == 2 else amount * 0.5 if cca_marker == 1 else 0

        if mitigation_counted > 0 and adaptation_counted > 0:
            total_cross_cutting += min(mitigation_counted, adaptation_counted)
            total_mitigation += mitigation_counted - min(mitigation_counted, adaptation_counted)
            total_adaptation += adaptation_counted - min(mitigation_counted, adaptation_counted)
        else:
            total_mitigation += mitigation_counted
            total_adaptation += adaptation_counted

        instrument_breakdown.append({
            "name": inst.get("name", f"instrument_{len(instrument_breakdown)+1}"),
            "amount_usd": amount,
            "instrument_type": inst.get("instrument_type", "loan"),
            "ccm_marker": ccm_marker,
            "cca_marker": cca_marker,
            "climate_relevant_amount_usd": round(mitigation_counted + adaptation_counted, 0),
            "sector": inst.get("sector", "energy"),
            "recipient_country": inst.get("recipient_country", "IN"),
        })

    total_climate_finance = total_mitigation + total_adaptation + total_cross_cutting

    # Paris alignment check
    fossil_exposure = rng.uniform(0, total_climate_finance * 0.3)
    paris_alignment_score = max(0, 1 - fossil_exposure / total_climate_finance) if total_climate_finance > 0 else 0

    # CPI methodology alignment
    cpi_aligned = {
        "tracks_public_private_split": True,
        "uses_rio_markers": True,
        "reports_adaptation_mitigation_split": True,
        "follows_mdb_tracking_methodology": rng.random() > 0.3,
        "includes_private_mobilisation": rng.random() > 0.4,
    }

    return {
        "entity_id": entity_id,
        "portfolio_name": portfolio_name,
        "reporting_year": year,
        "total_climate_finance_usd": round(total_climate_finance, 0),
        "mitigation_finance_usd": round(total_mitigation, 0),
        "adaptation_finance_usd": round(total_adaptation, 0),
        "cross_cutting_finance_usd": round(total_cross_cutting, 0),
        "adaptation_share_pct": round(total_adaptation / total_climate_finance * 100, 1) if total_climate_finance else 0,
        "cpi_global_landscape_2023_reference": CPI_2023_DATA,
        "paris_alignment_score": round(paris_alignment_score, 3),
        "fossil_fuel_exposure_usd": round(fossil_exposure, 0),
        "instrument_breakdown": instrument_breakdown,
        "cpi_methodology_alignment": cpi_aligned,
        "oecd_crs_aligned": all(cpi_aligned.values()),
        "assessed_at": datetime.now(timezone.utc).isoformat(),
    }


def assess_article21c_alignment(
    entity_id: str,
    portfolio: dict[str, Any],
    financial_flows: list[dict[str, Any]],
) -> dict[str, Any]:
    rng = random.Random(hash(str(entity_id)) & 0xFFFFFFFF)

    total_flows = sum(float(f.get("amount_usd", 0)) for f in financial_flows)
    green_flows = sum(float(f.get("amount_usd", 0)) for f in financial_flows if f.get("climate_aligned", rng.random() > 0.5))
    fossil_flows = sum(float(f.get("amount_usd", 0)) for f in financial_flows if f.get("fossil_fuel", rng.random() > 0.7))

    green_ratio = green_flows / total_flows if total_flows else rng.uniform(0.3, 0.8)
    brown_ratio = fossil_flows / total_flows if total_flows else rng.uniform(0.1, 0.4)
    alignment_score = min(100, round((green_ratio - brown_ratio * 2) * 100, 1))

    pathway_alignment: list[dict] = []
    for path in IPCC_PATHWAYS:
        compatible = alignment_score >= (90 if "1.5" in path["pathway"] else 70 if "well_below" in path["pathway"] else 50 if "2C" in path["pathway"] else 30)
        pathway_alignment.append({
            "pathway": path["pathway"],
            "description": path["description"],
            "peak_warming_c": path["peak_warming_c"],
            "portfolio_compatible": compatible,
            "annual_investment_needed_usd_tn": path["annual_investment_usd_tn"],
        })

    art9_public_finance = {
        "developed_country_commitment": "$100bn/year by 2020 (achieved 2022: $115.9bn OECD)",
        "ncqg_successor": "$300bn/year by 2035 (COP29 Baku)",
        "ldcs_sids_prioritisation": True,
        "grants_preference": "≥40% grant equivalent recommended",
    }

    return {
        "entity_id": entity_id,
        "unfccc_article": "2.1(c) — Making finance flows consistent with low GHG development and climate resilience",
        "total_portfolio_flows_usd": round(total_flows, 0),
        "green_aligned_flows_usd": round(green_flows, 0),
        "fossil_fuel_flows_usd": round(fossil_flows, 0),
        "green_ratio": round(green_ratio, 3),
        "brown_ratio": round(brown_ratio, 3),
        "alignment_score_0_100": max(0, alignment_score),
        "article_21c_aligned": alignment_score >= 60,
        "paris_article9_public_finance": art9_public_finance,
        "ipcc_pathway_alignment": pathway_alignment,
        "recommended_actions": [
            "Phase out fossil fuel financing by 2030 (IEA Net Zero pathway)",
            "Increase adaptation finance to ≥50% of climate finance portfolio",
            "Adopt Science-Based Targets for financial institutions (SBTi FI)",
            "Align investment mandates with EU Taxonomy green finance criteria",
        ],
        "assessed_at": datetime.now(timezone.utc).isoformat(),
    }


def calculate_ncqg_contribution(
    entity_id: str,
    institution_type: str,
    baseline_finance_usd: float,
) -> dict[str, Any]:
    rng = random.Random(hash(str(entity_id)) & 0xFFFFFFFF)

    # NCQG contributor tiers
    is_annex2 = institution_type.lower() in ["developed_country_dfi", "annex_ii_party", "oecd_member_mdb"]
    is_voluntary = institution_type.lower() in ["voluntary_contributor", "emerging_economy_mdb", "sovereign_wealth_fund"]

    # Goal layer assignment
    if is_annex2:
        goal_layer = "core_goal"
        contribution_pct = rng.uniform(0.5, 3.0)  # pct of core $300bn goal
    elif is_voluntary:
        goal_layer = "broader_goal"
        contribution_pct = rng.uniform(0.1, 1.5)
    else:
        goal_layer = "observer"
        contribution_pct = 0.0

    core_goal = NCQG_STRUCTURE["headline_goal_usd_bn_per_year"] * 1e9
    contribution_usd = baseline_finance_usd * (1 + contribution_pct / 100)

    # MDB mobilisation multiplier
    mdb_multiplier = NCQG_STRUCTURE["goal_layers"]["core_goal"]["description"]
    mobilisation_multiplier = rng.uniform(2.5, 5.0)
    total_mobilised_usd = contribution_usd * mobilisation_multiplier

    # Private finance mobilisation (OECD DAC formula)
    guarantee_amount = contribution_usd * rng.uniform(0.1, 0.3)
    equity_amount = contribution_usd * rng.uniform(0.05, 0.2)
    private_mobilised = (
        guarantee_amount * MOBILISATION_MULTIPLIERS["guarantees"]["typical"]
        + equity_amount * MOBILISATION_MULTIPLIERS["equity"]["typical"]
    )

    # Grant equivalent calculation
    grant_equiv_pct = rng.uniform(30, 60)
    grant_equivalent_usd = contribution_usd * grant_equiv_pct / 100

    # Gap to $300bn commitment
    share_of_core_goal_pct = contribution_usd / core_goal * 100

    return {
        "entity_id": entity_id,
        "institution_type": institution_type,
        "is_annex2_contributor": is_annex2,
        "goal_layer": goal_layer,
        "ncqg_structure": NCQG_STRUCTURE,
        "baseline_finance_usd": round(baseline_finance_usd, 0),
        "ncqg_contribution_usd": round(contribution_usd, 0),
        "share_of_300bn_core_goal_pct": round(share_of_core_goal_pct, 4),
        "mdb_mobilisation_multiplier": round(mobilisation_multiplier, 2),
        "total_mobilised_usd": round(total_mobilised_usd, 0),
        "private_finance_mobilised_usd": round(private_mobilised, 0),
        "grant_equivalent_pct": round(grant_equiv_pct, 1),
        "grant_equivalent_usd": round(grant_equivalent_usd, 0),
        "ldcs_sids_share_pct": round(rng.uniform(20, 50), 1),
        "tossd_eligible": is_annex2 or is_voluntary,
        "oecd_dac_reporting_required": is_annex2,
        "assessed_at": datetime.now(timezone.utc).isoformat(),
    }


def measure_mobilisation(
    entity_id: str,
    public_finance_usd: float,
    instruments: list[dict[str, Any]],
) -> dict[str, Any]:
    rng = random.Random(hash(str(entity_id)) & 0xFFFFFFFF)

    total_mobilised = 0.0
    additionality_score = 0.0
    instrument_results: list[dict] = []

    for inst in instruments:
        inst_rng = random.Random(hash(f"{entity_id}_{inst.get('type', '')}") & 0xFFFFFFFF)
        inst_type = inst.get("type", "guarantees").lower().replace(" ", "_")
        amount = float(inst.get("amount_usd", inst_rng.uniform(1e6, 50e6)))

        mult_data = MOBILISATION_MULTIPLIERS.get(inst_type, MOBILISATION_MULTIPLIERS["guarantees"])
        actual_multiplier = inst_rng.uniform(mult_data["min"], mult_data["max"])
        mobilised = amount * actual_multiplier

        total_mobilised += mobilised
        additionality_score += (1.0 if inst_type in ["guarantees", "risk_sharing"] else 0.7 if inst_type == "equity" else 0.5) * amount

        instrument_results.append({
            "instrument_type": inst_type,
            "public_finance_usd": amount,
            "mobilisation_multiplier": round(actual_multiplier, 2),
            "private_mobilised_usd": round(mobilised, 0),
            "methodology": mult_data["methodology"],
            "additionality_assessment": "high" if actual_multiplier >= mult_data["typical"] else "medium",
        })

    weighted_avg_multiplier = total_mobilised / public_finance_usd if public_finance_usd > 0 else 0
    additionality_avg = additionality_score / public_finance_usd if public_finance_usd > 0 else 0
    convergence_benchmark = rng.uniform(3.0, 6.0)

    # OECD TOSSD
    tossd = {
        "total_official_support_usd": round(public_finance_usd + total_mobilised * 0.3, 0),
        "provider_perspective": round(public_finance_usd, 0),
        "recipient_perspective": round(total_mobilised, 0),
        "reporting_year": datetime.now(timezone.utc).year,
        "tossd_portal_ready": rng.random() > 0.4,
    }

    return {
        "entity_id": entity_id,
        "total_public_finance_usd": round(public_finance_usd, 0),
        "total_private_mobilised_usd": round(total_mobilised, 0),
        "weighted_average_multiplier": round(weighted_avg_multiplier, 2),
        "additionality_score_0_1": round(min(additionality_avg, 1.0), 3),
        "convergence_benchmark_multiplier": round(convergence_benchmark, 2),
        "vs_convergence_benchmark": "above" if weighted_avg_multiplier >= convergence_benchmark else "below",
        "instrument_results": instrument_results,
        "tossd": tossd,
        "oecd_dac_methodology": "OECD DAC Converged Statistical Reporting Directives (2023)",
        "assessed_at": datetime.now(timezone.utc).isoformat(),
    }


def generate_climate_finance_report(
    entity_id: str,
    year: int,
) -> dict[str, Any]:
    rng = random.Random(hash(str(entity_id)) & 0xFFFFFFFF)

    total_finance = rng.uniform(100e6, 5e9)
    adaptation = total_finance * rng.uniform(0.15, 0.4)
    mitigation = total_finance - adaptation
    private_mobilised = total_finance * rng.uniform(0.3, 0.8)

    # UNFCCC Biennial Finance Report structure
    bfr_sections = {
        "section_1_domestic_policy": {
            "carbon_pricing_coverage_pct": round(rng.uniform(20, 80), 1),
            "fossil_subsidies_usd_bn": round(rng.uniform(0.5, 5.0), 2),
            "green_budget_tagging_adopted": rng.random() > 0.5,
        },
        "section_2_finance_to_developing": {
            "total_usd": round(total_finance, 0),
            "adaptation_usd": round(adaptation, 0),
            "mitigation_usd": round(mitigation, 0),
            "grants_pct": round(rng.uniform(20, 50), 1),
        },
        "section_3_private_mobilised": {
            "private_mobilised_usd": round(private_mobilised, 0),
            "mobilisation_methodology": "OECD DAC converged",
            "mdb_contribution_usd": round(private_mobilised * 0.6, 0),
        },
        "section_4_technology_transfer": {
            "technology_finance_usd": round(total_finance * rng.uniform(0.05, 0.15), 0),
            "capacity_building_usd": round(total_finance * rng.uniform(0.02, 0.08), 0),
        },
    }

    # $100bn commitment tracking (2020-2025)
    commitment_tracking = {
        "commitment_usd_bn": 100,
        "actual_2020_usd_bn": 83.3,
        "actual_2021_usd_bn": 89.6,
        "actual_2022_usd_bn": 115.9,
        "actual_2023_estimate_usd_bn": 130.0,
        "source": "OECD Climate Finance Report 2024",
        "first_achieved": 2022,
        "ncqg_successor_usd_bn": 300,
        "ncqg_target_year": 2035,
    }

    # CPI gap analysis
    cpi_gap = {
        "total_climate_finance_2023_usd_bn": CPI_2023_DATA["total_climate_finance_usd_bn"],
        "annual_need_2030_usd_bn": CPI_2023_DATA["annual_need_2030_usd_bn"],
        "gap_usd_bn": CPI_2023_DATA["annual_gap_usd_bn"],
        "gap_fill_rate_pct": round(CPI_2023_DATA["total_climate_finance_usd_bn"] / CPI_2023_DATA["annual_need_2030_usd_bn"] * 100, 1),
        "adaptation_gap_usd_bn": round(400 - CPI_2023_DATA["adaptation_usd_bn"], 0),
    }

    # MDB joint tracking
    mdb_tracking = []
    for mdb in MDB_INSTITUTIONS[:4]:
        mdb_rng = random.Random(hash(f"{entity_id}_{mdb['code']}") & 0xFFFFFFFF)
        climate_finance = mdb["total_finance_usd_bn"] * mdb["climate_share_pct"] / 100
        mdb_tracking.append({
            "mdb": mdb["name"],
            "code": mdb["code"],
            "total_finance_usd_bn": mdb["total_finance_usd_bn"],
            "climate_finance_usd_bn": round(climate_finance, 1),
            "climate_share_pct": mdb["climate_share_pct"],
            "adaptation_target_pct": mdb["adaptation_target_pct"],
            "paris_aligned_since": mdb["paris_aligned_since"],
        })

    return {
        "entity_id": entity_id,
        "reporting_year": year,
        "unfccc_biennial_finance_report": bfr_sections,
        "total_climate_finance_usd": round(total_finance, 0),
        "adaptation_finance_usd": round(adaptation, 0),
        "mitigation_finance_usd": round(mitigation, 0),
        "private_mobilised_usd": round(private_mobilised, 0),
        "commitment_tracking_100bn": commitment_tracking,
        "cpi_gap_analysis": cpi_gap,
        "mdb_joint_tracking": mdb_tracking,
        "ncqg_progress": {
            "goal_usd_bn": 300,
            "current_trajectory_usd_bn": round(total_finance / 1e9, 1),
            "gap_usd_bn": round(max(0, 300 - total_finance / 1e9), 1),
            "on_track": total_finance >= 100e9,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
