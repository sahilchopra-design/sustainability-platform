"""
Climate Stress Test Engine — Sprint 26
========================================
Standards covered:
- BCBS 517 Principles on Climate-Related Financial Risks (2022)
- BoE CBES 2021 (3 scenarios)
- ECB Climate Stress Test 2022
- APRA CPG 229 Climate Change Financial Risks 2023
- Fed Pilot Climate Scenario Analysis 2023
- NGFS Phase 4 Scenarios 2023
- FSB 2022 Climate Roadmap
"""
from __future__ import annotations

import random
from typing import Any

# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

SUPERVISOR_FRAMEWORKS: dict[str, dict[str, Any]] = {
    "bcbs_517": {
        "supervisor": "BCBS / BIS",
        "full_name": "BCBS 517 Principles for the Effective Management of Climate-Related Financial Risks",
        "scenario_count": 3,
        "time_horizon_yrs": 30,
        "capital_req": True,
        "mandatory": True,
        "reporting_deadline": "2025-12-31",
        "principles_count": 18,
    },
    "boe_cbes": {
        "supervisor": "Bank of England (PRA / FCA)",
        "full_name": "Climate Biennial Exploratory Scenario 2021",
        "scenario_count": 3,
        "time_horizon_yrs": 30,
        "capital_req": False,
        "mandatory": True,
        "reporting_deadline": "2021-10-01",
        "scenarios": ["Early Action", "Late Action", "No Additional Action"],
    },
    "ecb_cst": {
        "supervisor": "European Central Bank",
        "full_name": "ECB Climate Stress Test 2022",
        "scenario_count": 3,
        "time_horizon_yrs": 30,
        "capital_req": False,
        "mandatory": True,
        "reporting_deadline": "2022-07-31",
        "scenarios": ["orderly", "disorderly", "hot_house_world"],
    },
    "apra_clt": {
        "supervisor": "APRA (Australian Prudential Regulation Authority)",
        "full_name": "CPG 229 Climate Change Financial Risks 2023",
        "scenario_count": 2,
        "time_horizon_yrs": 30,
        "capital_req": True,
        "mandatory": False,
        "reporting_deadline": "2025-06-30",
    },
    "fed_pilot": {
        "supervisor": "Federal Reserve (US)",
        "full_name": "Fed Pilot Climate Scenario Analysis 2023",
        "scenario_count": 2,
        "time_horizon_yrs": 10,
        "capital_req": False,
        "mandatory": False,
        "reporting_deadline": "2023-12-31",
        "scenarios": ["physical_risk", "transition_risk"],
    },
    "mas_csst": {
        "supervisor": "Monetary Authority of Singapore",
        "full_name": "MAS Climate Scenario Stress Test",
        "scenario_count": 3,
        "time_horizon_yrs": 20,
        "capital_req": False,
        "mandatory": True,
        "reporting_deadline": "2024-06-30",
    },
    "hkma_csa": {
        "supervisor": "Hong Kong Monetary Authority",
        "full_name": "HKMA Climate Scenario Analysis",
        "scenario_count": 3,
        "time_horizon_yrs": 30,
        "capital_req": False,
        "mandatory": False,
        "reporting_deadline": "2025-12-31",
    },
    "rba_cst": {
        "supervisor": "Reserve Bank of Australia",
        "full_name": "RBA Climate Stress Test",
        "scenario_count": 2,
        "time_horizon_yrs": 30,
        "capital_req": False,
        "mandatory": False,
        "reporting_deadline": "2026-06-30",
    },
}

NGFS_PHASE4_SCENARIOS: dict[str, dict[str, Any]] = {
    "net_zero_2050": {
        "description": "Ambitious early action limiting warming to 1.5°C by 2100",
        "carbon_price_2030": 130.0,
        "carbon_price_2050": 560.0,
        "gdp_impact_2030": -0.5,
        "gdp_impact_2050": -0.3,
        "temp_rise_2100": 1.5,
        "physical_damage_2100": 0.02,
        "scenario_type": "orderly",
    },
    "below_2c": {
        "description": "Gradual transition holding warming below 2°C",
        "carbon_price_2030": 75.0,
        "carbon_price_2050": 310.0,
        "gdp_impact_2030": -0.3,
        "gdp_impact_2050": -0.2,
        "temp_rise_2100": 1.8,
        "physical_damage_2100": 0.04,
        "scenario_type": "orderly",
    },
    "delayed_transition": {
        "description": "Late-start disorderly transition with higher near-term costs",
        "carbon_price_2030": 40.0,
        "carbon_price_2050": 700.0,
        "gdp_impact_2030": -0.2,
        "gdp_impact_2050": -1.8,
        "temp_rise_2100": 1.8,
        "physical_damage_2100": 0.04,
        "scenario_type": "disorderly",
    },
    "divergent_nz": {
        "description": "Net-zero achieved through divergent policy mix — high cost",
        "carbon_price_2030": 150.0,
        "carbon_price_2050": 800.0,
        "gdp_impact_2030": -1.0,
        "gdp_impact_2050": -1.5,
        "temp_rise_2100": 1.5,
        "physical_damage_2100": 0.02,
        "scenario_type": "disorderly",
    },
    "current_policies": {
        "description": "No new climate policies beyond currently enacted",
        "carbon_price_2030": 15.0,
        "carbon_price_2050": 30.0,
        "gdp_impact_2030": -0.1,
        "gdp_impact_2050": -3.5,
        "temp_rise_2100": 3.0,
        "physical_damage_2100": 0.14,
        "scenario_type": "hot_house_world",
    },
    "nationally_determined": {
        "description": "NDC pledges fully implemented, limited additional action",
        "carbon_price_2030": 25.0,
        "carbon_price_2050": 60.0,
        "gdp_impact_2030": -0.2,
        "gdp_impact_2050": -2.8,
        "temp_rise_2100": 2.5,
        "physical_damage_2100": 0.09,
        "scenario_type": "hot_house_world",
    },
}

SECTOR_TRANSITION_SENSITIVITY: dict[str, dict[str, Any]] = {
    "oil_gas": {"credit_loss_multiplier": 2.8, "market_loss_multiplier": 3.2, "operational_loss_multiplier": 1.5},
    "coal_mining": {"credit_loss_multiplier": 4.5, "market_loss_multiplier": 5.0, "operational_loss_multiplier": 2.0},
    "utilities_fossil": {"credit_loss_multiplier": 2.2, "market_loss_multiplier": 2.5, "operational_loss_multiplier": 1.3},
    "utilities_renewable": {"credit_loss_multiplier": 0.3, "market_loss_multiplier": 0.2, "operational_loss_multiplier": 0.5},
    "steel": {"credit_loss_multiplier": 1.8, "market_loss_multiplier": 2.0, "operational_loss_multiplier": 1.4},
    "cement": {"credit_loss_multiplier": 1.7, "market_loss_multiplier": 1.9, "operational_loss_multiplier": 1.3},
    "automotive_ice": {"credit_loss_multiplier": 2.0, "market_loss_multiplier": 2.5, "operational_loss_multiplier": 1.2},
    "automotive_ev": {"credit_loss_multiplier": 0.4, "market_loss_multiplier": 0.3, "operational_loss_multiplier": 0.6},
    "aviation": {"credit_loss_multiplier": 1.9, "market_loss_multiplier": 2.1, "operational_loss_multiplier": 1.5},
    "shipping": {"credit_loss_multiplier": 1.6, "market_loss_multiplier": 1.8, "operational_loss_multiplier": 1.3},
    "real_estate_brown": {"credit_loss_multiplier": 1.5, "market_loss_multiplier": 1.7, "operational_loss_multiplier": 1.1},
    "real_estate_green": {"credit_loss_multiplier": 0.5, "market_loss_multiplier": 0.4, "operational_loss_multiplier": 0.7},
    "agriculture": {"credit_loss_multiplier": 1.2, "market_loss_multiplier": 1.4, "operational_loss_multiplier": 1.8},
    "chemicals": {"credit_loss_multiplier": 1.4, "market_loss_multiplier": 1.6, "operational_loss_multiplier": 1.2},
    "technology": {"credit_loss_multiplier": 0.3, "market_loss_multiplier": 0.2, "operational_loss_multiplier": 0.4},
    "financials": {"credit_loss_multiplier": 0.8, "market_loss_multiplier": 0.9, "operational_loss_multiplier": 0.6},
    "retail": {"credit_loss_multiplier": 0.7, "market_loss_multiplier": 0.8, "operational_loss_multiplier": 0.9},
    "healthcare": {"credit_loss_multiplier": 0.4, "market_loss_multiplier": 0.3, "operational_loss_multiplier": 0.5},
    "telecom": {"credit_loss_multiplier": 0.3, "market_loss_multiplier": 0.4, "operational_loss_multiplier": 0.4},
    "food_beverage": {"credit_loss_multiplier": 0.9, "market_loss_multiplier": 1.0, "operational_loss_multiplier": 1.1},
}

PHYSICAL_HAZARD_DAMAGE_FUNCTIONS: dict[str, dict[str, float]] = {
    "flood": {"short": 0.01, "medium": 0.05, "long": 0.15},
    "heat": {"short": 0.005, "medium": 0.03, "long": 0.10},
    "drought": {"short": 0.008, "medium": 0.04, "long": 0.12},
    "wind": {"short": 0.003, "medium": 0.02, "long": 0.07},
    "sea_level_rise": {"short": 0.002, "medium": 0.025, "long": 0.18},
    "wildfire": {"short": 0.004, "medium": 0.025, "long": 0.09},
}

CAPITAL_ADEQUACY_FLOORS: dict[str, dict[str, float]] = {
    "bcbs_517": {"cet1_floor_pct": 8.0, "liquidity_floor_pct": 100.0},
    "boe_cbes": {"cet1_floor_pct": 4.5, "liquidity_floor_pct": 100.0},
    "ecb_cst": {"cet1_floor_pct": 4.5, "liquidity_floor_pct": 100.0},
    "apra_clt": {"cet1_floor_pct": 10.25, "liquidity_floor_pct": 100.0},
    "fed_pilot": {"cet1_floor_pct": 4.5, "liquidity_floor_pct": 100.0},
    "mas_csst": {"cet1_floor_pct": 6.0, "liquidity_floor_pct": 100.0},
    "hkma_csa": {"cet1_floor_pct": 7.0, "liquidity_floor_pct": 100.0},
    "rba_cst": {"cet1_floor_pct": 8.0, "liquidity_floor_pct": 100.0},
}


def _scenario_multiplier(scenario: str, scenario_type_key: str = "credit") -> float:
    """Map NGFS scenario to a loss intensity multiplier."""
    base = {
        "net_zero_2050": 0.6,
        "below_2c": 0.8,
        "delayed_transition": 1.4,
        "divergent_nz": 1.6,
        "current_policies": 2.2,
        "nationally_determined": 1.8,
    }.get(scenario, 1.0)
    return base


# ---------------------------------------------------------------------------
# Engine class
# ---------------------------------------------------------------------------

class ClimateStressTestEngine:
    """Sprint 26 Climate Stress Test Engine — BCBS 517 / BoE CBES / ECB CST / APRA CPG 229."""

    # ------------------------------------------------------------------
    # 1. BCBS 517
    # ------------------------------------------------------------------
    def run_bcbs_517(
        self,
        entity_id: str,
        institution_type: str,
        portfolio_sectors: dict,
        total_assets_usd: float,
        cet1_ratio_pct: float,
        scenario: str,
    ) -> dict:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)
        scen_mult = _scenario_multiplier(scenario)
        ngfs = NGFS_PHASE4_SCENARIOS.get(scenario, NGFS_PHASE4_SCENARIOS["current_policies"])

        # Sector-weighted losses
        weighted_credit = 0.0
        weighted_market = 0.0
        weighted_op = 0.0
        total_weight = 0.0
        for sector, weight in portfolio_sectors.items():
            sens = SECTOR_TRANSITION_SENSITIVITY.get(sector, SECTOR_TRANSITION_SENSITIVITY["financials"])
            weighted_credit += weight * sens["credit_loss_multiplier"]
            weighted_market += weight * sens["market_loss_multiplier"]
            weighted_op += weight * sens["operational_loss_multiplier"]
            total_weight += weight
        if total_weight > 0:
            weighted_credit /= total_weight
            weighted_market /= total_weight
            weighted_op /= total_weight

        base_credit = 0.025
        base_market = 0.015
        base_op = 0.005

        credit_loss_pct = round(max(0, min(30, base_credit * weighted_credit * scen_mult * 100 + rng.uniform(-0.3, 0.3))), 2)
        market_loss_pct = round(max(0, min(20, base_market * weighted_market * scen_mult * 100 + rng.uniform(-0.2, 0.2))), 2)
        operational_loss_pct = round(max(0, min(10, base_op * weighted_op * scen_mult * 100 + rng.uniform(-0.1, 0.1))), 2)

        physical_loss_pct = round(ngfs["physical_damage_2100"] * 100 * rng.uniform(0.3, 0.7), 2)
        total_loss_pct = round(credit_loss_pct + market_loss_pct + operational_loss_pct + physical_loss_pct, 2)
        climate_var_pct = round(total_loss_pct * 1.15 + rng.uniform(-0.5, 0.5), 2)

        cet1_post = round(cet1_ratio_pct - total_loss_pct, 2)
        floor = CAPITAL_ADEQUACY_FLOORS["bcbs_517"]["cet1_floor_pct"]

        # BCBS Principles compliance score (18 principles)
        bcbs_compliance_score = round(max(30, min(100, 70 - scen_mult * 10 + rng.uniform(-5, 5))), 2)

        return {
            "entity_id": entity_id,
            "framework": "bcbs_517",
            "scenario": scenario,
            "climate_var_pct": climate_var_pct,
            "credit_loss_pct": credit_loss_pct,
            "market_loss_pct": market_loss_pct,
            "operational_loss_pct": operational_loss_pct,
            "physical_loss_pct": physical_loss_pct,
            "total_loss_pct": total_loss_pct,
            "cet1_pre_stress_pct": cet1_ratio_pct,
            "cet1_post_stress": cet1_post,
            "cet1_floor_pct": floor,
            "capital_adequate": cet1_post >= floor,
            "bcbs_compliance_score": bcbs_compliance_score,
            "ngfs_carbon_price_2030": ngfs["carbon_price_2030"],
            "ngfs_temp_rise_2100": ngfs["temp_rise_2100"],
        }

    # ------------------------------------------------------------------
    # 2. BoE CBES
    # ------------------------------------------------------------------
    def run_boe_cbes(
        self,
        entity_id: str,
        institution_type: str,
        uk_mortgage_exposure_pct: float,
        uk_corporate_exposure_pct: float,
        scenario: str,
    ) -> dict:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        scen_config = {
            "early_action": {"physical": 0.5, "transition": 0.9, "liquidity": 0.4, "label": "Early Action"},
            "late_action": {"physical": 1.0, "transition": 1.8, "liquidity": 1.0, "label": "Late Action"},
            "no_additional_action": {"physical": 2.2, "transition": 0.3, "liquidity": 0.6, "label": "No Additional Action"},
        }.get(scenario, {"physical": 1.5, "transition": 1.2, "liquidity": 0.7, "label": scenario})

        physical_loss_pct = round(
            max(0, min(15, scen_config["physical"] * (0.02 * uk_mortgage_exposure_pct / 100 + 0.01) * 100 + rng.uniform(-0.2, 0.2))),
            2,
        )
        transition_loss_pct = round(
            max(0, min(20, scen_config["transition"] * (0.03 * uk_corporate_exposure_pct / 100 + 0.015) * 100 + rng.uniform(-0.3, 0.3))),
            2,
        )
        liquidity_stress_pct = round(max(0, min(10, scen_config["liquidity"] * 2.0 + rng.uniform(-0.2, 0.2))), 2)
        nim_compression_bps = round(max(0, min(100, scen_config["transition"] * 15 + rng.uniform(-5, 5))), 2)
        npl_uplift_ppts = round(max(0, min(8, scen_config["physical"] * 1.5 + scen_config["transition"] * 0.8 + rng.uniform(-0.3, 0.3))), 2)
        cet1_impact_ppts = round(physical_loss_pct + transition_loss_pct * 0.6, 2)

        floor = CAPITAL_ADEQUACY_FLOORS["boe_cbes"]["cet1_floor_pct"]

        return {
            "entity_id": entity_id,
            "framework": "boe_cbes",
            "scenario": scenario,
            "scenario_label": scen_config["label"],
            "physical_loss_pct": physical_loss_pct,
            "transition_loss_pct": transition_loss_pct,
            "liquidity_stress_pct": liquidity_stress_pct,
            "nim_compression_bps": nim_compression_bps,
            "npl_uplift_ppts": npl_uplift_ppts,
            "cet1_impact_ppts": cet1_impact_ppts,
            "cet1_floor_pct": floor,
            "test_passed": cet1_impact_ppts <= 6.0,
            "uk_mortgage_exposure_pct": round(uk_mortgage_exposure_pct, 2),
            "uk_corporate_exposure_pct": round(uk_corporate_exposure_pct, 2),
        }

    # ------------------------------------------------------------------
    # 3. ECB CST
    # ------------------------------------------------------------------
    def run_ecb_cst(
        self,
        entity_id: str,
        institution_type: str,
        eu_sector_exposures: dict,
        total_rwa_usd: float,
        scenario: str,
    ) -> dict:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        scen_map = {
            "orderly": {"nii_factor": 0.95, "npe_factor": 0.5, "cet1_factor": 0.7, "green_prem": 0.05},
            "disorderly": {"nii_factor": 0.85, "npe_factor": 1.8, "cet1_factor": 2.0, "green_prem": 0.02},
            "hot_house_world": {"nii_factor": 0.75, "npe_factor": 3.0, "cet1_factor": 3.5, "green_prem": -0.01},
        }.get(scenario, {"nii_factor": 0.90, "npe_factor": 1.0, "cet1_factor": 1.5, "green_prem": 0.03})

        nii_impact_pct = round(max(-25, min(0, -(1 - scen_map["nii_factor"]) * 100 + rng.uniform(-2, 2))), 2)
        npe_impact_ppts = round(max(0, min(10, scen_map["npe_factor"] * 1.2 + rng.uniform(-0.2, 0.2))), 2)
        cet1_impact_ppts = round(max(0, min(8, scen_map["cet1_factor"] * 0.9 + rng.uniform(-0.2, 0.2))), 2)

        # Stranded asset loss
        high_carbon_exposure = sum(
            w for s, w in eu_sector_exposures.items()
            if s in ("oil_gas", "coal_mining", "utilities_fossil")
        )
        stranded_asset_loss_pct = round(max(0, min(15, high_carbon_exposure * scen_map["cet1_factor"] * 0.5 + rng.uniform(-0.3, 0.3))), 2)

        # Taxonomy alignment proxy
        green_exposure = sum(w for s, w in eu_sector_exposures.items() if "renew" in s or "ev" in s)
        taxonomy_alignment_pct = round(min(100, green_exposure * 100 + rng.uniform(5, 20)), 2)

        pillar2_add_on = round(max(0, cet1_impact_ppts - 2.0), 2)

        return {
            "entity_id": entity_id,
            "framework": "ecb_cst",
            "scenario": scenario,
            "nii_impact_pct": nii_impact_pct,
            "npe_impact_ppts": npe_impact_ppts,
            "cet1_impact_ppts": cet1_impact_ppts,
            "stranded_asset_loss_pct": stranded_asset_loss_pct,
            "taxonomy_alignment_pct": taxonomy_alignment_pct,
            "pillar2_add_on": pillar2_add_on,
            "green_premium_factor": scen_map["green_prem"],
            "cet1_floor_pct": CAPITAL_ADEQUACY_FLOORS["ecb_cst"]["cet1_floor_pct"],
        }

    # ------------------------------------------------------------------
    # 4. APRA CPG 229
    # ------------------------------------------------------------------
    def run_apra_clt(
        self,
        entity_id: str,
        institution_type: str,
        australian_exposure_pct: float,
        scenario: str,
    ) -> dict:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        scen_map = {
            "net_zero_2050": {"physical": 0.6, "transition": 0.9},
            "below_2c": {"physical": 0.8, "transition": 0.7},
            "delayed_transition": {"physical": 1.0, "transition": 1.8},
            "current_policies": {"physical": 2.5, "transition": 0.3},
            "nationally_determined": {"physical": 1.8, "transition": 0.5},
        }.get(scenario, {"physical": 1.0, "transition": 1.0})

        # Australian exposure amplifies physical risk (bushfire, drought)
        au_factor = max(0, min(2, australian_exposure_pct / 50))

        physical_risk_score = round(max(0, min(100, scen_map["physical"] * 40 * au_factor + rng.uniform(-5, 5))), 2)
        transition_risk_score = round(max(0, min(100, scen_map["transition"] * 40 + rng.uniform(-5, 5))), 2)

        capital_impact_ppts = round(
            max(0, min(6, (physical_risk_score + transition_risk_score) / 100 * 4 + rng.uniform(-0.2, 0.2))),
            2,
        )
        liquidity_impact_pct = round(max(0, min(15, capital_impact_ppts * 2.5 + rng.uniform(-0.3, 0.3))), 2)

        floor = CAPITAL_ADEQUACY_FLOORS["apra_clt"]["cet1_floor_pct"]
        apra_adequacy_met = capital_impact_ppts <= 3.0

        return {
            "entity_id": entity_id,
            "framework": "apra_clt",
            "scenario": scenario,
            "capital_impact_ppts": capital_impact_ppts,
            "liquidity_impact_pct": liquidity_impact_pct,
            "physical_risk_score": physical_risk_score,
            "transition_risk_score": transition_risk_score,
            "apra_adequacy_met": apra_adequacy_met,
            "cet1_floor_pct": floor,
            "australian_exposure_pct": round(australian_exposure_pct, 2),
        }

    # ------------------------------------------------------------------
    # 5. Cross-framework
    # ------------------------------------------------------------------
    def run_cross_framework(
        self,
        entity_id: str,
        institution_type: str,
        portfolio_sectors: dict,
        total_assets_usd: float,
        cet1_pct: float,
        scenario: str,
    ) -> dict:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        bcbs = self.run_bcbs_517(entity_id, institution_type, portfolio_sectors, total_assets_usd, cet1_pct, scenario)
        boe = self.run_boe_cbes(entity_id, institution_type, 35.0, 30.0, scenario)
        ecb = self.run_ecb_cst(entity_id, institution_type, portfolio_sectors, total_assets_usd * 0.4, scenario)
        apra = self.run_apra_clt(entity_id, institution_type, 20.0, scenario)

        framework_results = {
            "bcbs_517": bcbs,
            "boe_cbes": boe,
            "ecb_cst": ecb,
            "apra_clt": apra,
        }

        losses = {
            "bcbs_517": bcbs["total_loss_pct"],
            "boe_cbes": boe["physical_loss_pct"] + boe["transition_loss_pct"],
            "ecb_cst": ecb["cet1_impact_ppts"],
            "apra_clt": apra["capital_impact_ppts"],
        }
        worst_case_framework = max(losses, key=losses.get)
        worst_case_loss_pct = round(losses[worst_case_framework], 2)

        aggregated_capital_impact = round(sum(losses.values()) / len(losses), 2)
        stress_test_passed = all([bcbs["capital_adequate"], boe["test_passed"], apra["apra_adequacy_met"]])

        resilience_score = round(max(0, min(100, 100 - aggregated_capital_impact * 5 + rng.uniform(-3, 3))), 2)

        return {
            "entity_id": entity_id,
            "scenario": scenario,
            "framework_results": framework_results,
            "framework_loss_summary": losses,
            "worst_case_framework": worst_case_framework,
            "worst_case_loss_pct": worst_case_loss_pct,
            "aggregated_capital_impact": aggregated_capital_impact,
            "stress_test_passed": stress_test_passed,
            "overall_resilience_score": resilience_score,
        }

    # ------------------------------------------------------------------
    # 6. Portfolio resilience
    # ------------------------------------------------------------------
    def assess_portfolio_resilience(self, entity_id: str, portfolios: list) -> dict:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        if not portfolios:
            return {
                "entity_id": entity_id,
                "resilience_by_scenario": {},
                "capital_buffer_adequacy": True,
                "recommended_hedges": [],
                "portfolio_count": 0,
            }

        resilience_by_scenario: dict[str, dict] = {}
        for scenario in ["net_zero_2050", "delayed_transition", "current_policies"]:
            avg_loss = round(rng.uniform(1, 15) * _scenario_multiplier(scenario), 2)
            resilience_by_scenario[scenario] = {
                "avg_loss_pct": avg_loss,
                "max_loss_pct": round(avg_loss * 1.5, 2),
                "portfolios_failing": sum(1 for p in portfolios if p.get("cet1_pct", 10) - avg_loss < 4.5),
            }

        capital_buffer_adequacy = all(
            v["portfolios_failing"] == 0 for v in resilience_by_scenario.values()
        )

        recommended_hedges = []
        if not capital_buffer_adequacy:
            recommended_hedges.extend(["climate_transition_overlay", "green_bond_reallocation"])
        if resilience_by_scenario["current_policies"]["avg_loss_pct"] > 8:
            recommended_hedges.append("physical_risk_insurance")

        return {
            "entity_id": entity_id,
            "resilience_by_scenario": resilience_by_scenario,
            "capital_buffer_adequacy": capital_buffer_adequacy,
            "recommended_hedges": recommended_hedges,
            "portfolio_count": len(portfolios),
        }
