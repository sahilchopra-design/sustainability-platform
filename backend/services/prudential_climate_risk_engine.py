"""
Prudential Climate Risk Engine — E45
======================================
BOE/PRA BES 2021/2025 · ECB DFAST 2024 · NGFS v4 (6 scenarios)
ICAAP Pillar 2a/2b · Basel SRP 43.1 · EBA SREP climate overlay

References:
  - BOE/PRA: SS3/19 (Climate-related financial risk), BES 2021 & 2025 design papers
  - ECB: CST 2022 pilot, CST 2024 (Climate Stress Test) methodology
  - NGFS: Phase IV scenarios — June 2023 vintage
  - BCBS: SRP 43.1 — Climate-related financial risks supervisory review
  - EBA: SREP climate risk assessment guidelines (EBA/GL/2020/06)
  - PRA SS19/23: Management of climate-related financial risks
"""
from __future__ import annotations

import math
import random
import uuid
from datetime import date
from typing import Any, Optional


# ---------------------------------------------------------------------------
# NGFS v4 — 6 Scenarios
# ---------------------------------------------------------------------------

NGFS_V4_SCENARIOS: dict[str, dict] = {
    "net_zero_2050": {
        "category": "orderly",
        "description": "Net zero GHG emissions globally by 2050; Paris 1.5°C goal achieved",
        "2030_temp_c": 1.5,
        "2050_temp_c": 1.4,
        "carbon_price_2030_usd": 290,
        "carbon_price_2050_usd": 800,
        "transition_risk_multiplier": 1.8,
        "physical_risk_multiplier": 0.7,
    },
    "below_2c": {
        "category": "orderly",
        "description": "Below 2°C with high probability; gradual policy tightening",
        "2030_temp_c": 1.7,
        "2050_temp_c": 1.8,
        "carbon_price_2030_usd": 150,
        "carbon_price_2050_usd": 400,
        "transition_risk_multiplier": 1.4,
        "physical_risk_multiplier": 0.9,
    },
    "divergent_net_zero": {
        "category": "disorderly",
        "description": "Net zero by 2050 with divergent regional policies and stranded assets",
        "2030_temp_c": 1.6,
        "2050_temp_c": 1.5,
        "carbon_price_2030_usd": 350,
        "carbon_price_2050_usd": 1000,
        "transition_risk_multiplier": 2.2,
        "physical_risk_multiplier": 0.75,
    },
    "delayed_transition": {
        "category": "disorderly",
        "description": "Action delayed until 2030; abrupt policy shift causes instability",
        "2030_temp_c": 2.0,
        "2050_temp_c": 1.8,
        "carbon_price_2030_usd": 80,
        "carbon_price_2050_usd": 700,
        "transition_risk_multiplier": 2.5,
        "physical_risk_multiplier": 1.1,
    },
    "current_policies": {
        "category": "hot_house",
        "description": "Current policies maintained; ~3°C warming by end of century",
        "2030_temp_c": 2.4,
        "2050_temp_c": 3.0,
        "carbon_price_2030_usd": 25,
        "carbon_price_2050_usd": 50,
        "transition_risk_multiplier": 0.8,
        "physical_risk_multiplier": 2.2,
    },
    "fragmented_world": {
        "category": "hot_house",
        "description": "Geopolitical fragmentation, limited global cooperation; 2.5°C by 2050",
        "2030_temp_c": 2.2,
        "2050_temp_c": 2.5,
        "carbon_price_2030_usd": 40,
        "carbon_price_2050_usd": 100,
        "transition_risk_multiplier": 1.0,
        "physical_risk_multiplier": 1.8,
    },
}

# ---------------------------------------------------------------------------
# BOE BES Rounds
# ---------------------------------------------------------------------------

BOE_BES_ROUNDS: dict[str, dict] = {
    "BES_2021": {
        "publication_date": "2022-05",
        "time_horizon_years": 30,
        "scenarios": ["early_action", "late_action", "no_additional_action"],
        "llt_scenario": {
            "name": "late_action",
            "temp_pathway_c": 1.8,
            "carbon_price_2030_usd": 100,
            "cet1_depletion_typical_pct": 3.5,
        },
        "elt_scenario": {
            "name": "early_action",
            "temp_pathway_c": 1.5,
            "carbon_price_2030_usd": 250,
            "cet1_depletion_typical_pct": 2.1,
        },
    },
    "BES_2025": {
        "publication_date": "2025-05",
        "time_horizon_years": 30,
        "scenarios": ["net_zero_2050", "delayed_transition", "current_policies"],
        "llt_scenario": {
            "name": "delayed_transition",
            "temp_pathway_c": 2.0,
            "carbon_price_2030_usd": 80,
            "cet1_depletion_typical_pct": 4.2,
        },
        "elt_scenario": {
            "name": "net_zero_2050",
            "temp_pathway_c": 1.5,
            "carbon_price_2030_usd": 290,
            "cet1_depletion_typical_pct": 2.8,
        },
    },
}

# ---------------------------------------------------------------------------
# ECB CST Rounds
# ---------------------------------------------------------------------------

ECB_CST_ROUNDS: dict[str, dict] = {
    "CST_2022": {
        "publication_date": "2022-07",
        "time_horizon_years": 30,
        "scenarios": ["hot_house", "disorderly", "orderly"],
        "orderly": {"temp_c_2050": 1.5, "carbon_price_2030": 250},
        "disorderly": {"temp_c_2050": 1.8, "carbon_price_2030": 350},
        "hot_house": {"temp_c_2050": 3.2, "carbon_price_2030": 25},
        "sample_cet1_impact_orderly_pct": 1.9,
        "sample_cet1_impact_disorderly_pct": 3.1,
        "sample_cet1_impact_hot_house_pct": 5.3,
    },
    "CST_2024": {
        "publication_date": "2024-Q4",
        "time_horizon_years": 30,
        "scenarios": ["net_zero", "delayed_transition", "current_policies"],
        "net_zero": {"temp_c_2050": 1.4, "carbon_price_2030": 290},
        "delayed_transition": {"temp_c_2050": 1.8, "carbon_price_2030": 120},
        "current_policies": {"temp_c_2050": 3.0, "carbon_price_2030": 25},
        "sample_cet1_impact_net_zero_pct": 2.2,
        "sample_cet1_impact_delayed_transition_pct": 4.1,
        "sample_cet1_impact_current_policies_pct": 6.8,
    },
}

# ---------------------------------------------------------------------------
# Sector Transition Risk (15 sector codes)
# ---------------------------------------------------------------------------

SECTOR_TRANSITION_RISK: dict[str, dict] = {
    "fossil_fuels":     {"rating": "high",   "pd_uplift_orderly_bps": 85,  "pd_uplift_disorderly_bps": 210},
    "utilities":        {"rating": "high",   "pd_uplift_orderly_bps": 60,  "pd_uplift_disorderly_bps": 150},
    "steel":            {"rating": "high",   "pd_uplift_orderly_bps": 70,  "pd_uplift_disorderly_bps": 180},
    "cement":           {"rating": "high",   "pd_uplift_orderly_bps": 65,  "pd_uplift_disorderly_bps": 170},
    "chemicals":        {"rating": "high",   "pd_uplift_orderly_bps": 55,  "pd_uplift_disorderly_bps": 140},
    "automotive":       {"rating": "medium", "pd_uplift_orderly_bps": 40,  "pd_uplift_disorderly_bps": 110},
    "aviation":         {"rating": "high",   "pd_uplift_orderly_bps": 75,  "pd_uplift_disorderly_bps": 190},
    "shipping":         {"rating": "medium", "pd_uplift_orderly_bps": 50,  "pd_uplift_disorderly_bps": 130},
    "agriculture":      {"rating": "medium", "pd_uplift_orderly_bps": 30,  "pd_uplift_disorderly_bps": 80},
    "real_estate":      {"rating": "medium", "pd_uplift_orderly_bps": 25,  "pd_uplift_disorderly_bps": 70},
    "manufacturing":    {"rating": "medium", "pd_uplift_orderly_bps": 35,  "pd_uplift_disorderly_bps": 90},
    "retail":           {"rating": "low",    "pd_uplift_orderly_bps": 15,  "pd_uplift_disorderly_bps": 40},
    "financials":       {"rating": "low",    "pd_uplift_orderly_bps": 10,  "pd_uplift_disorderly_bps": 30},
    "technology":       {"rating": "low",    "pd_uplift_orderly_bps": 8,   "pd_uplift_disorderly_bps": 20},
    "healthcare":       {"rating": "low",    "pd_uplift_orderly_bps": 5,   "pd_uplift_disorderly_bps": 15},
}

# ---------------------------------------------------------------------------
# Sector Physical Risk (15 sector codes)
# ---------------------------------------------------------------------------

SECTOR_PHYSICAL_RISK: dict[str, dict] = {
    "fossil_fuels":     {"rating": "medium", "pd_uplift_acute_bps": 50,   "pd_uplift_chronic_bps": 80},
    "utilities":        {"rating": "high",   "pd_uplift_acute_bps": 90,   "pd_uplift_chronic_bps": 120},
    "steel":            {"rating": "medium", "pd_uplift_acute_bps": 40,   "pd_uplift_chronic_bps": 60},
    "cement":           {"rating": "medium", "pd_uplift_acute_bps": 35,   "pd_uplift_chronic_bps": 55},
    "chemicals":        {"rating": "medium", "pd_uplift_acute_bps": 45,   "pd_uplift_chronic_bps": 70},
    "automotive":       {"rating": "medium", "pd_uplift_acute_bps": 30,   "pd_uplift_chronic_bps": 45},
    "aviation":         {"rating": "high",   "pd_uplift_acute_bps": 80,   "pd_uplift_chronic_bps": 95},
    "shipping":         {"rating": "high",   "pd_uplift_acute_bps": 100,  "pd_uplift_chronic_bps": 110},
    "agriculture":      {"rating": "very_high", "pd_uplift_acute_bps": 130, "pd_uplift_chronic_bps": 160},
    "real_estate":      {"rating": "high",   "pd_uplift_acute_bps": 95,   "pd_uplift_chronic_bps": 115},
    "manufacturing":    {"rating": "medium", "pd_uplift_acute_bps": 40,   "pd_uplift_chronic_bps": 60},
    "retail":           {"rating": "low",    "pd_uplift_acute_bps": 20,   "pd_uplift_chronic_bps": 30},
    "financials":       {"rating": "low",    "pd_uplift_acute_bps": 15,   "pd_uplift_chronic_bps": 25},
    "technology":       {"rating": "low",    "pd_uplift_acute_bps": 10,   "pd_uplift_chronic_bps": 20},
    "healthcare":       {"rating": "low",    "pd_uplift_acute_bps": 8,    "pd_uplift_chronic_bps": 15},
}

# ---------------------------------------------------------------------------
# ICAAP / SS3/19 Guidance
# ---------------------------------------------------------------------------

ICAAP_GUIDANCE: dict[str, Any] = {
    "ss319_thresholds": {
        "material": ">5% CET1 depletion or >10% RWA impact",
        "potentially_material": "1-5% CET1 depletion or 3-10% RWA impact",
        "immaterial": "<1% CET1 depletion or <3% RWA impact",
    },
    "pillar2a_add_on_range": {"min_pct": 0.25, "max_pct": 2.0, "description": "Specific capital add-on for identified climate risks"},
    "pillar2b_buffer_range": {"min_pct": 0.0, "max_pct": 3.0, "description": "Capital planning buffer for climate tail risks"},
    "disclosure_standard": "SS19/23 — Management of climate-related financial risks",
    "review_frequency": "Annual (minimum); triggered on material new information",
}

# ---------------------------------------------------------------------------
# Basel SRP 43.1 Categorisation
# ---------------------------------------------------------------------------

BASEL_SRP431: dict[str, Any] = {
    "categorisation_criteria": {
        "material": {
            "rwa_impact_threshold_pct": 5.0,
            "description": "Climate risk deemed material — full quantification and ICAAP capital charge required",
            "srep_action": "Pillar 2 add-on mandatory",
        },
        "potentially_material": {
            "rwa_impact_threshold_pct": 1.0,
            "description": "Enhanced monitoring; targeted stress testing; transition plan required",
            "srep_action": "Enhanced supervisory dialogue",
        },
        "immaterial": {
            "rwa_impact_threshold_pct": 0.0,
            "description": "Standard supervision; qualitative disclosure in Pillar 3",
            "srep_action": "Qualitative disclosure only",
        },
    },
    "implementation_date": "2026-01-01",
    "publication": "BCBS Principles for the Effective Management of Climate-Related Financial Risks",
}

# ---------------------------------------------------------------------------
# EBA SREP Scoring
# ---------------------------------------------------------------------------

EBA_SREP_SCORING: dict[str, Any] = {
    "score_1": {"label": "low_risk", "supervisory_action": "no_immediate_action", "add_on_guidance": "0%"},
    "score_2": {"label": "medium_low_risk", "supervisory_action": "enhanced_monitoring", "add_on_guidance": "0.25-0.5%"},
    "score_3": {"label": "medium_high_risk", "supervisory_action": "formal_dialogue_capital_requirement", "add_on_guidance": "0.5-1.5%"},
    "score_4": {"label": "high_risk", "supervisory_action": "immediate_remediation_required", "add_on_guidance": "1.5-3.0%"},
}

# ---------------------------------------------------------------------------
# CET1 Migration Matrix (scenario × sector → depletion multiplier)
# ---------------------------------------------------------------------------

CET1_MIGRATION_MATRIX: dict[str, dict[str, float]] = {
    "net_zero_2050":      {"fossil_fuels": 2.1, "utilities": 1.8, "steel": 1.6, "real_estate": 1.2, "financials": 1.1},
    "delayed_transition": {"fossil_fuels": 3.8, "utilities": 2.9, "steel": 2.5, "real_estate": 1.8, "financials": 1.3},
    "current_policies":   {"fossil_fuels": 1.2, "utilities": 3.5, "steel": 2.0, "real_estate": 2.8, "financials": 1.5},
    "divergent_net_zero": {"fossil_fuels": 2.8, "utilities": 2.2, "steel": 2.0, "real_estate": 1.5, "financials": 1.2},
    "below_2c":           {"fossil_fuels": 1.7, "utilities": 1.5, "steel": 1.4, "real_estate": 1.1, "financials": 1.05},
    "fragmented_world":   {"fossil_fuels": 1.5, "utilities": 3.1, "steel": 1.8, "real_estate": 2.5, "financials": 1.4},
}


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class PrudentialClimateRiskEngine:

    # ------------------------------------------------------------------
    # 1. BOE BES Stress Test
    # ------------------------------------------------------------------

    def assess_boe_bes(
        self,
        entity_id: str,
        loan_book_segments: list[dict],
        market_portfolio: Optional[dict] = None,
        institution_type: str = "bank",
        bes_round: str = "BES_2025",
    ) -> dict[str, Any]:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)
        bes_params = BOE_BES_ROUNDS.get(bes_round, BOE_BES_ROUNDS["BES_2025"])

        def _stress_segment(seg: dict, scenario_key: str) -> dict:
            sector = seg.get("sector", "manufacturing")
            exposure = float(seg.get("exposure", 0))
            base_pd = float(seg.get("base_pd", 0.02))
            sector_tr = SECTOR_TRANSITION_RISK.get(sector, {"pd_uplift_disorderly_bps": 50, "pd_uplift_orderly_bps": 25})
            sector_ph = SECTOR_PHYSICAL_RISK.get(sector, {"pd_uplift_chronic_bps": 40, "pd_uplift_acute_bps": 30})

            if scenario_key == "llt":
                pd_uplift = sector_tr["pd_uplift_disorderly_bps"] / 10000 + sector_ph["pd_uplift_chronic_bps"] / 10000
            else:
                pd_uplift = sector_tr["pd_uplift_orderly_bps"] / 10000 + sector_ph["pd_uplift_acute_bps"] / 10000

            stressed_pd = min(1.0, base_pd + pd_uplift * rng.uniform(0.8, 1.2))
            lgd = float(seg.get("lgd", 0.45))
            el_stressed = exposure * stressed_pd * lgd
            return {
                "sector": sector,
                "exposure": exposure,
                "base_pd": base_pd,
                "stressed_pd": round(stressed_pd, 5),
                "pd_uplift_bps": round(pd_uplift * 10000, 1),
                "expected_loss_stressed": round(el_stressed, 2),
                "lgd": lgd,
            }

        total_exposure = sum(float(s.get("exposure", 0)) for s in loan_book_segments)
        cet1_ratio_start = float((market_portfolio or {}).get("cet1_ratio_pct", rng.uniform(14, 18)))

        llt_results = [_stress_segment(s, "llt") for s in loan_book_segments]
        elt_results = [_stress_segment(s, "elt") for s in loan_book_segments]

        llt_el = sum(r["expected_loss_stressed"] for r in llt_results)
        elt_el = sum(r["expected_loss_stressed"] for r in elt_results)

        rwa_proxy = total_exposure * rng.uniform(0.6, 0.9)
        llt_cet1_depletion = min(cet1_ratio_start * 0.7, (llt_el / max(rwa_proxy, 1)) * 100 * rng.uniform(0.8, 1.2))
        elt_cet1_depletion = min(llt_cet1_depletion * 0.6, (elt_el / max(rwa_proxy, 1)) * 100 * rng.uniform(0.7, 1.0))

        return {
            "entity_id": entity_id,
            "bes_round": bes_round,
            "institution_type": institution_type,
            "total_loan_book_exposure": round(total_exposure, 2),
            "cet1_ratio_start_pct": round(cet1_ratio_start, 2),
            "llt_scenario": {
                "scenario_name": bes_params["llt_scenario"]["name"],
                "total_el_stressed": round(llt_el, 2),
                "cet1_depletion_pct": round(llt_cet1_depletion, 2),
                "cet1_ratio_post_stress": round(cet1_ratio_start - llt_cet1_depletion, 2),
                "segment_results": llt_results,
            },
            "elt_scenario": {
                "scenario_name": bes_params["elt_scenario"]["name"],
                "total_el_stressed": round(elt_el, 2),
                "cet1_depletion_pct": round(elt_cet1_depletion, 2),
                "cet1_ratio_post_stress": round(cet1_ratio_start - elt_cet1_depletion, 2),
                "segment_results": elt_results,
            },
            "worst_case_cet1_post": round(cet1_ratio_start - llt_cet1_depletion, 2),
            "assessment_id": str(uuid.uuid4()),
        }

    # ------------------------------------------------------------------
    # 2. ECB DFAST
    # ------------------------------------------------------------------

    def assess_ecb_dfast(
        self,
        entity_id: str,
        loan_book_segments: list[dict],
        cst_round: str = "CST_2024",
    ) -> dict[str, Any]:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)
        cst = ECB_CST_ROUNDS.get(cst_round, ECB_CST_ROUNDS["CST_2024"])
        scenarios = cst.get("scenarios", ["net_zero", "delayed_transition", "current_policies"])

        total_exposure = sum(float(s.get("exposure", 0)) for s in loan_book_segments)
        cet1_start = rng.uniform(14.0, 18.5)
        rwa_proxy = total_exposure * rng.uniform(0.55, 0.85)

        scenario_results = {}
        for sc in scenarios:
            sc_key = f"sample_cet1_impact_{sc}_pct"
            base_impact = cst.get(sc_key, rng.uniform(2.0, 6.0))
            sector_adjustment = rng.uniform(0.85, 1.15)
            cet1_impact = round(base_impact * sector_adjustment, 2)
            el_transition = total_exposure * rng.uniform(0.005, 0.04)
            el_physical = total_exposure * rng.uniform(0.003, 0.025)
            scenario_results[sc] = {
                "total_el_transition": round(el_transition, 2),
                "total_el_physical": round(el_physical, 2),
                "total_el_combined": round(el_transition + el_physical, 2),
                "cet1_depletion_pct": cet1_impact,
                "cet1_post_stress": round(cet1_start - cet1_impact, 2),
            }

        worst_scenario = min(scenario_results, key=lambda s: scenario_results[s]["cet1_post_stress"])

        return {
            "entity_id": entity_id,
            "cst_round": cst_round,
            "total_exposure": round(total_exposure, 2),
            "cet1_ratio_start": round(cet1_start, 2),
            "scenario_results": scenario_results,
            "worst_case_scenario": worst_scenario,
            "worst_case_cet1_post": scenario_results[worst_scenario]["cet1_post_stress"],
            "assessment_id": str(uuid.uuid4()),
        }

    # ------------------------------------------------------------------
    # 3. NGFS v4 Multi-Scenario Assessment
    # ------------------------------------------------------------------

    def assess_ngfs_v4(
        self,
        entity_id: str,
        portfolio_data: dict,
        scenarios: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)
        if scenarios is None:
            scenarios = list(NGFS_V4_SCENARIOS.keys())

        total_exposure = float(portfolio_data.get("total_exposure", 1_000_000_000))
        cet1_start = float(portfolio_data.get("cet1_ratio_pct", rng.uniform(14.0, 18.0)))
        years = list(range(2025, 2055, 5))

        scenario_trajectories = {}
        for sc_name in scenarios:
            sc = NGFS_V4_SCENARIOS.get(sc_name)
            if sc is None:
                continue
            trajectory = []
            cet1_current = cet1_start
            tr_mult = sc["transition_risk_multiplier"]
            ph_mult = sc["physical_risk_multiplier"]
            for yr in years:
                phase = (yr - 2025) / 25.0
                tr_drag = tr_mult * rng.uniform(0.02, 0.08) * phase
                ph_drag = ph_mult * rng.uniform(0.01, 0.06) * phase
                cet1_current = max(5.0, cet1_start - tr_drag - ph_drag)
                trajectory.append({"year": yr, "cet1_ratio": round(cet1_current, 2)})
            scenario_trajectories[sc_name] = {
                "category": sc["category"],
                "cet1_trajectory": trajectory,
                "cet1_2050": trajectory[-1]["cet1_ratio"],
                "carbon_price_2030": sc["carbon_price_2030_usd"],
                "warming_2050": sc["2050_temp_c"],
            }

        worst_case = min(
            scenario_trajectories,
            key=lambda s: scenario_trajectories[s]["cet1_2050"],
        )

        return {
            "entity_id": entity_id,
            "total_exposure": total_exposure,
            "cet1_start": cet1_start,
            "scenarios_assessed": scenarios,
            "scenario_trajectories": scenario_trajectories,
            "worst_case_scenario": worst_case,
            "worst_case_cet1_2050": scenario_trajectories[worst_case]["cet1_2050"],
            "time_horizon": "2025-2050",
            "assessment_id": str(uuid.uuid4()),
        }

    # ------------------------------------------------------------------
    # 4. ICAAP Pillar 2a/2b Overlay
    # ------------------------------------------------------------------

    def calculate_icaap_overlay(
        self,
        entity_id: str,
        stressed_results: dict,
        institution_type: str = "bank",
    ) -> dict[str, Any]:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        worst_cet1_depletion = float(stressed_results.get("worst_cet1_depletion_pct", rng.uniform(1.5, 5.0)))
        rwa_impact_pct = float(stressed_results.get("rwa_impact_pct", rng.uniform(2.0, 8.0)))

        # Pillar 2a: specific risk add-on
        p2a_floor = ICAAP_GUIDANCE["pillar2a_add_on_range"]["min_pct"]
        p2a_cap = ICAAP_GUIDANCE["pillar2a_add_on_range"]["max_pct"]
        p2a_add_on = round(min(p2a_cap, max(p2a_floor, worst_cet1_depletion * 0.30)), 2)

        # Pillar 2b: capital planning buffer
        p2b_floor = ICAAP_GUIDANCE["pillar2b_buffer_range"]["min_pct"]
        p2b_cap = ICAAP_GUIDANCE["pillar2b_buffer_range"]["max_pct"]
        p2b_buffer = round(min(p2b_cap, max(p2b_floor, worst_cet1_depletion * 0.50 - p2a_add_on)), 2)

        total_climate_overlay = round(p2a_add_on + p2b_buffer, 2)

        # SREP category
        if rwa_impact_pct >= 5.0:
            srep_score = 4
        elif rwa_impact_pct >= 3.0:
            srep_score = 3
        elif rwa_impact_pct >= 1.0:
            srep_score = 2
        else:
            srep_score = 1

        srep_finding = EBA_SREP_SCORING[f"score_{srep_score}"]

        return {
            "entity_id": entity_id,
            "institution_type": institution_type,
            "worst_cet1_depletion_pct": worst_cet1_depletion,
            "rwa_impact_pct": rwa_impact_pct,
            "pillar_2a_add_on_pct": p2a_add_on,
            "pillar_2b_buffer_pct": p2b_buffer,
            "total_climate_capital_overlay_pct": total_climate_overlay,
            "srep_score": srep_score,
            "srep_finding": srep_finding,
            "icaap_guidance_ref": "SS3/19 + SS19/23",
            "review_frequency": ICAAP_GUIDANCE["review_frequency"],
            "assessment_id": str(uuid.uuid4()),
        }

    # ------------------------------------------------------------------
    # 5. Basel SRP 43.1 Categorisation
    # ------------------------------------------------------------------

    def assess_sarp431(
        self,
        entity_id: str,
        rwa_data: dict,
        climate_rwa_impact: float,
    ) -> dict[str, Any]:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        total_rwa = float(rwa_data.get("total_rwa", 1_000_000_000))
        impact_pct = (climate_rwa_impact / max(total_rwa, 1)) * 100

        material_threshold = BASEL_SRP431["categorisation_criteria"]["material"]["rwa_impact_threshold_pct"]
        pm_threshold = BASEL_SRP431["categorisation_criteria"]["potentially_material"]["rwa_impact_threshold_pct"]

        if impact_pct >= material_threshold:
            categorisation = "material"
        elif impact_pct >= pm_threshold:
            categorisation = "potentially_material"
        else:
            categorisation = "immaterial"

        cat_info = BASEL_SRP431["categorisation_criteria"][categorisation]

        next_review_yr = 2026 if categorisation == "material" else 2027
        review_date = f"{next_review_yr}-01-01"

        return {
            "entity_id": entity_id,
            "total_rwa": total_rwa,
            "climate_rwa_impact": round(climate_rwa_impact, 2),
            "climate_rwa_impact_pct": round(impact_pct, 2),
            "categorisation": categorisation,
            "categorisation_description": cat_info["description"],
            "srep_action": cat_info["srep_action"],
            "review_date": review_date,
            "basel_reference": "SRP 43.1 — BCBS Climate Financial Risk Principles",
            "assessment_id": str(uuid.uuid4()),
        }

    # ------------------------------------------------------------------
    # 6. Capital Overlays (segment-level)
    # ------------------------------------------------------------------

    def generate_capital_overlays(
        self,
        entity_id: str,
        loan_book_segments: list[dict],
        scenario: str = "delayed_transition",
    ) -> dict[str, Any]:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)
        sc_params = NGFS_V4_SCENARIOS.get(scenario, NGFS_V4_SCENARIOS["delayed_transition"])

        segment_overlays = []
        total_exposure = 0.0
        total_capital_add_on = 0.0
        total_brown_exposure = 0.0

        for seg in loan_book_segments:
            sector = seg.get("sector", "manufacturing")
            exposure = float(seg.get("exposure", 0))
            base_rwa_pct = float(seg.get("rwa_density_pct", rng.uniform(50, 110)))

            tr_info = SECTOR_TRANSITION_RISK.get(sector, {"rating": "medium", "pd_uplift_disorderly_bps": 50, "pd_uplift_orderly_bps": 25})
            ph_info = SECTOR_PHYSICAL_RISK.get(sector, {"rating": "medium", "pd_uplift_chronic_bps": 40, "pd_uplift_acute_bps": 30})

            tr_rating = tr_info["rating"]
            ph_rating = ph_info["rating"]

            # brown share (simplified)
            brown_share = 0.8 if tr_rating == "high" else (0.4 if tr_rating == "medium" else 0.1)
            brown_exposure = exposure * brown_share
            total_brown_exposure += brown_exposure

            # RWA uplift
            tr_mult = sc_params["transition_risk_multiplier"]
            ph_mult = sc_params["physical_risk_multiplier"]
            rwa_uplift_pct = round(
                (tr_info["pd_uplift_disorderly_bps"] * tr_mult / 10000
                 + ph_info["pd_uplift_chronic_bps"] * ph_mult / 10000) * 100,
                2,
            )

            capital_add_on = exposure * (rwa_uplift_pct / 100) * 0.08  # 8% capital ratio
            total_exposure += exposure
            total_capital_add_on += capital_add_on

            # Stranded asset exposure
            stranded_pct = rng.uniform(0.05, 0.35) if tr_rating == "high" else rng.uniform(0, 0.10)

            segment_overlays.append({
                "sector": sector,
                "exposure": round(exposure, 2),
                "transition_risk_rating": tr_rating,
                "physical_risk_rating": ph_rating,
                "brown_share_pct": round(brown_share * 100, 1),
                "brown_exposure": round(brown_exposure, 2),
                "stranded_asset_exposure_pct": round(stranded_pct * 100, 1),
                "rwa_uplift_pct": rwa_uplift_pct,
                "capital_add_on": round(capital_add_on, 2),
            })

        return {
            "entity_id": entity_id,
            "scenario": scenario,
            "scenario_category": sc_params["category"],
            "total_exposure": round(total_exposure, 2),
            "total_brown_exposure": round(total_brown_exposure, 2),
            "brown_share_pct": round(total_brown_exposure / max(total_exposure, 1) * 100, 1),
            "total_capital_add_on": round(total_capital_add_on, 2),
            "total_capital_add_on_pct": round(total_capital_add_on / max(total_exposure, 1) * 100, 2),
            "segment_overlays": segment_overlays,
            "assessment_id": str(uuid.uuid4()),
        }

    # ------------------------------------------------------------------
    # 7. Full Assessment
    # ------------------------------------------------------------------

    def generate_full_assessment(
        self,
        entity_id: str,
        institution_data: dict,
    ) -> dict[str, Any]:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        loan_book = institution_data.get("loan_book_segments", [
            {"sector": "real_estate", "exposure": 500_000_000, "base_pd": 0.015, "lgd": 0.35, "rwa_density_pct": 60},
            {"sector": "utilities", "exposure": 300_000_000, "base_pd": 0.025, "lgd": 0.45, "rwa_density_pct": 85},
            {"sector": "fossil_fuels", "exposure": 200_000_000, "base_pd": 0.04, "lgd": 0.50, "rwa_density_pct": 100},
        ])
        market_portfolio = institution_data.get("market_portfolio", {"cet1_ratio_pct": rng.uniform(14.5, 17.0)})
        institution_type = institution_data.get("institution_type", "bank")
        bes_round = institution_data.get("bes_round", "BES_2025")
        cst_round = institution_data.get("cst_round", "CST_2024")
        total_rwa = sum(s.get("exposure", 0) * s.get("rwa_density_pct", 75) / 100 for s in loan_book)

        bes = self.assess_boe_bes(entity_id, loan_book, market_portfolio, institution_type, bes_round)
        ecb = self.assess_ecb_dfast(entity_id, loan_book, cst_round)
        ngfs = self.assess_ngfs_v4(entity_id, {"total_exposure": sum(s.get("exposure", 0) for s in loan_book), "cet1_ratio_pct": market_portfolio.get("cet1_ratio_pct", 15.5)})
        overlays = self.generate_capital_overlays(entity_id, loan_book)

        stressed_results = {
            "worst_cet1_depletion_pct": bes["llt_scenario"]["cet1_depletion_pct"],
            "rwa_impact_pct": rng.uniform(2.0, 9.0),
        }
        icaap = self.calculate_icaap_overlay(entity_id, stressed_results, institution_type)

        climate_rwa = total_rwa * icaap["rwa_impact_pct"] / 100
        srp431 = self.assess_sarp431(entity_id, {"total_rwa": total_rwa}, climate_rwa)

        return {
            "entity_id": entity_id,
            "institution_type": institution_type,
            "assessment_date": date.today().isoformat(),
            "assessment_id": str(uuid.uuid4()),
            "frameworks_assessed": ["BOE_BES", "ECB_DFAST", "NGFS_v4", "ICAAP_SS319", "Basel_SRP431", "EBA_SREP"],
            "summary": {
                "worst_case_cet1_post_stress": bes["worst_case_cet1_post"],
                "total_capital_overlay_pct": icaap["total_climate_capital_overlay_pct"],
                "srp431_categorisation": srp431["categorisation"],
                "srep_score": icaap["srep_score"],
                "total_brown_exposure": overlays["total_brown_exposure"],
                "worst_ngfs_scenario": ngfs["worst_case_scenario"],
            },
            "modules": {
                "boe_bes": bes,
                "ecb_dfast": ecb,
                "ngfs_v4": ngfs,
                "icaap_overlay": icaap,
                "sarp431": srp431,
                "capital_overlays": overlays,
            },
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_engine: Optional[PrudentialClimateRiskEngine] = None


def get_engine() -> PrudentialClimateRiskEngine:
    global _engine
    if _engine is None:
        _engine = PrudentialClimateRiskEngine()
    return _engine
