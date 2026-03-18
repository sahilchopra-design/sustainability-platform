"""
Just Transition Finance Engine — E89
======================================
Standards implemented:
- ILO Just Transition Guiding Principles 2015
  (Guidelines for a just transition towards environmentally sustainable economies and societies)
- EU Just Transition Fund Regulation (EU) 2021/1056 (JTF) — Articles 8, 10, 11
- Climate Investment Funds (CIF) — CTF, PPCR, FIP, SREP facility profiles
- World Bank Just Transition Framework 2022
- ILO Decent Work Agenda / SDG 8 + SDG 10
- Glasgow Climate Pact (COP26) Just Energy Transition Partnerships (JETPs)
- ICMA Social Bond Principles 2023 (social outcome alignment)
"""
from __future__ import annotations

import math
from typing import Any

# ---------------------------------------------------------------------------
# Reference Data
# ---------------------------------------------------------------------------

ILO_JT_PRINCIPLES: dict[str, dict[str, Any]] = {
    "social_dialogue": {
        "weight": 0.25,
        "sub_criteria": [
            "tripartite_consultation_body_established",
            "workers_included_in_transition_planning",
            "collective_bargaining_rights_protected",
            "grievance_mechanism_operational",
        ],
        "ILO_ref": "ILO JT Guidelines §§ 10-18 — Social Dialogue & Industrial Relations",
        "description": (
            "Inclusive tripartite social dialogue between governments, employers and workers "
            "to shape the transition; collective bargaining and consultation mechanisms."
        ),
    },
    "skills_reskilling": {
        "weight": 0.25,
        "sub_criteria": [
            "skills_gap_analysis_completed",
            "training_programmes_funded",
            "qualification_recognition_mechanism",
            "apprenticeship_green_economy",
        ],
        "ILO_ref": "ILO JT Guidelines §§ 19-27 — Education, Training and Skills Development",
        "description": (
            "Investment in reskilling and upskilling of affected workers; recognition of "
            "prior learning; green economy apprenticeship pathways."
        ),
    },
    "social_protection": {
        "weight": 0.20,
        "sub_criteria": [
            "income_support_during_transition",
            "healthcare_continuity_guaranteed",
            "pension_entitlements_protected",
            "redundancy_notice_period_adequate",
        ],
        "ILO_ref": "ILO JT Guidelines §§ 28-34 — Social Protection",
        "description": (
            "Adequate income support, healthcare and pension protection during transition; "
            "no worker left worse off by the transition to a green economy."
        ),
    },
    "active_labour_market_policy": {
        "weight": 0.15,
        "sub_criteria": [
            "job_placement_services_available",
            "geographic_mobility_support",
            "self_employment_support",
            "dedicated_transition_employment_fund",
        ],
        "ILO_ref": "ILO JT Guidelines §§ 35-43 — Active Labour Market Policies",
        "description": (
            "Proactive job placement, mobility grants, enterprise support and dedicated "
            "employment funds to ensure displaced workers find decent new work."
        ),
    },
    "community_investment": {
        "weight": 0.15,
        "sub_criteria": [
            "territorial_transition_plan_adopted",
            "infrastructure_investment_committed",
            "diversification_strategy_funded",
            "indigenous_community_engagement",
        ],
        "ILO_ref": "ILO JT Guidelines §§ 44-50 — Local Economic Development",
        "description": (
            "Investment in the economic diversification and infrastructure of communities "
            "dependent on fossil fuel industries; indigenous peoples' rights respected."
        ),
    },
}

EU_JTF_ELIGIBILITY_CRITERIA: dict[str, dict[str, Any]] = {
    "territorial_jtp": {
        "description": "Territorial Just Transition Plan (JTP) adopted at NUTS2 level",
        "threshold": "JTP formally adopted and aligned with Partnership Agreement",
        "points": 20,
    },
    "ghg_emission_dependency": {
        "description": "GHG emissions from fossil fuel combustion > 15% of regional total",
        "threshold": ">15% regional GHG from fossil fuels (Art 8(3)(e) JTF)",
        "points": 15,
    },
    "fossil_fuel_employment": {
        "description": "Fossil fuel employment > 1% of regional working-age population",
        "threshold": ">1% regional employment in NACE B.05-B.08, C.19, D.35 activities",
        "points": 15,
    },
    "economic_diversification": {
        "description": "Credible economic diversification strategy with funded projects",
        "threshold": "Diversification plan approved; >3 alternative sectors identified",
        "points": 10,
    },
    "social_partnership_evidence": {
        "description": "Evidence of tripartite consultation in JTP development",
        "threshold": "Social partners and civil society formally consulted (ILO JT Principle 1)",
        "points": 10,
    },
    "green_jobs_target": {
        "description": "Quantified target for green jobs creation by 2030",
        "threshold": "Net green jobs target ≥ 60% of fossil jobs displaced by 2030",
        "points": 10,
    },
    "just_transition_monitoring": {
        "description": "Monitoring framework with social indicators aligned to JTF output indicators",
        "threshold": "Annual monitoring report; job quality + wage indicators tracked",
        "points": 10,
    },
    "cross_border_coordination": {
        "description": "Cross-border or inter-regional just transition coordination mechanism",
        "threshold": "MoU or formal cooperation agreement with neighbouring regions",
        "points": 10,
    },
}

COAL_COMMUNITY_PROFILES: dict[str, dict[str, Any]] = {
    "ruhr_germany": {
        "country": "Germany",
        "region_name": "Ruhr Valley",
        "coal_employment_k": 12.0,
        "peak_employment_year": 1985,
        "phase_out_target_year": 2038,
        "alternative_sector_score": 0.72,
        "transition_fund_available_m": 14_800.0,
    },
    "silesia_poland": {
        "country": "Poland",
        "region_name": "Silesia (Śląsk)",
        "coal_employment_k": 85.0,
        "peak_employment_year": 1979,
        "phase_out_target_year": 2049,
        "alternative_sector_score": 0.41,
        "transition_fund_available_m": 8_000.0,
    },
    "ostrava_czech": {
        "country": "Czech Republic",
        "region_name": "Ostrava / Moravian-Silesian",
        "coal_employment_k": 15.0,
        "peak_employment_year": 1990,
        "phase_out_target_year": 2038,
        "alternative_sector_score": 0.53,
        "transition_fund_available_m": 2_500.0,
    },
    "oltenia_romania": {
        "country": "Romania",
        "region_name": "Oltenia",
        "coal_employment_k": 28.0,
        "peak_employment_year": 1995,
        "phase_out_target_year": 2032,
        "alternative_sector_score": 0.35,
        "transition_fund_available_m": 2_100.0,
    },
    "pernik_bulgaria": {
        "country": "Bulgaria",
        "region_name": "Pernik / Maritsa East",
        "coal_employment_k": 18.0,
        "peak_employment_year": 1988,
        "phase_out_target_year": 2038,
        "alternative_sector_score": 0.38,
        "transition_fund_available_m": 1_200.0,
    },
    "teruel_spain": {
        "country": "Spain",
        "region_name": "Teruel / Asturias",
        "coal_employment_k": 4.5,
        "peak_employment_year": 1989,
        "phase_out_target_year": 2025,
        "alternative_sector_score": 0.44,
        "transition_fund_available_m": 450.0,
    },
    "south_wales_uk": {
        "country": "United Kingdom",
        "region_name": "South Wales / South Yorkshire",
        "coal_employment_k": 3.0,
        "peak_employment_year": 1984,
        "phase_out_target_year": 2024,
        "alternative_sector_score": 0.58,
        "transition_fund_available_m": 700.0,
    },
    "hunter_valley_aus": {
        "country": "Australia",
        "region_name": "Hunter Valley, NSW",
        "coal_employment_k": 16.0,
        "peak_employment_year": 2012,
        "phase_out_target_year": 2035,
        "alternative_sector_score": 0.55,
        "transition_fund_available_m": 1_200.0,
    },
    "mpumalanga_za": {
        "country": "South Africa",
        "region_name": "Mpumalanga",
        "coal_employment_k": 90.0,
        "peak_employment_year": 2015,
        "phase_out_target_year": 2040,
        "alternative_sector_score": 0.28,
        "transition_fund_available_m": 8_500.0,
    },
    "jharkhand_india": {
        "country": "India",
        "region_name": "Jharkhand / Chhattisgarh",
        "coal_employment_k": 340.0,
        "peak_employment_year": 2023,
        "phase_out_target_year": 2070,
        "alternative_sector_score": 0.22,
        "transition_fund_available_m": 3_000.0,
    },
    "inner_mongolia_china": {
        "country": "China",
        "region_name": "Inner Mongolia / Shanxi",
        "coal_employment_k": 2_800.0,
        "peak_employment_year": 2020,
        "phase_out_target_year": 2060,
        "alternative_sector_score": 0.35,
        "transition_fund_available_m": 180_000.0,
    },
    "appalachia_usa": {
        "country": "USA",
        "region_name": "Appalachia (WV / KY / VA)",
        "coal_employment_k": 42.0,
        "peak_employment_year": 1979,
        "phase_out_target_year": 2035,
        "alternative_sector_score": 0.40,
        "transition_fund_available_m": 11_300.0,
    },
    "cesar_colombia": {
        "country": "Colombia",
        "region_name": "Cesar / La Guajira",
        "coal_employment_k": 22.0,
        "peak_employment_year": 2013,
        "phase_out_target_year": 2040,
        "alternative_sector_score": 0.32,
        "transition_fund_available_m": 900.0,
    },
    "kalimantan_indonesia": {
        "country": "Indonesia",
        "region_name": "East Kalimantan / South Kalimantan",
        "coal_employment_k": 280.0,
        "peak_employment_year": 2022,
        "phase_out_target_year": 2045,
        "alternative_sector_score": 0.30,
        "transition_fund_available_m": 20_000.0,
    },
    "witbank_za": {
        "country": "South Africa",
        "region_name": "Witbank (eMalahleni)",
        "coal_employment_k": 45.0,
        "peak_employment_year": 2018,
        "phase_out_target_year": 2040,
        "alternative_sector_score": 0.29,
        "transition_fund_available_m": 3_500.0,
    },
    "western_balkans": {
        "country": "Kosovo / North Macedonia / Bosnia",
        "region_name": "Western Balkans Coal Belt",
        "coal_employment_k": 38.0,
        "peak_employment_year": 2019,
        "phase_out_target_year": 2040,
        "alternative_sector_score": 0.27,
        "transition_fund_available_m": 1_800.0,
    },
    "north_rhine_germany": {
        "country": "Germany",
        "region_name": "North Rhine-Westphalia (Rhenish)",
        "coal_employment_k": 8.5,
        "peak_employment_year": 2000,
        "phase_out_target_year": 2038,
        "alternative_sector_score": 0.78,
        "transition_fund_available_m": 15_000.0,
    },
    "thar_pakistan": {
        "country": "Pakistan",
        "region_name": "Thar / Balochistan",
        "coal_employment_k": 15.0,
        "peak_employment_year": 2025,
        "phase_out_target_year": 2050,
        "alternative_sector_score": 0.20,
        "transition_fund_available_m": 500.0,
    },
    "queensland_aus": {
        "country": "Australia",
        "region_name": "Bowen Basin, Queensland",
        "coal_employment_k": 22.0,
        "peak_employment_year": 2014,
        "phase_out_target_year": 2040,
        "alternative_sector_score": 0.50,
        "transition_fund_available_m": 1_800.0,
    },
    "limpopo_za": {
        "country": "South Africa",
        "region_name": "Limpopo (Waterberg)",
        "coal_employment_k": 14.0,
        "peak_employment_year": 2022,
        "phase_out_target_year": 2045,
        "alternative_sector_score": 0.24,
        "transition_fund_available_m": 1_200.0,
    },
}

CIF_FACILITY_PROFILES: dict[str, dict[str, Any]] = {
    "CTF": {
        "focus": "Clean Technology Fund — scaling up low-carbon technologies in MICs",
        "full_name": "Clean Technology Fund",
        "eligible_countries": [
            "Mexico", "Brazil", "Indonesia", "Turkey", "South Africa",
            "India", "Philippines", "Egypt", "Morocco", "Colombia",
            "Thailand", "Vietnam", "Kazakhstan", "Ukraine", "Nigeria",
        ],
        "min_project_m": 25.0,
        "grant_element_pct": 10.0,
        "concessional_rate_pct": 0.25,
        "focus_areas": [
            "renewable_energy", "energy_efficiency", "sustainable_transport",
            "industrial_low_carbon",
        ],
    },
    "PPCR": {
        "focus": "Pilot Program for Climate Resilience — integrating climate risk into development",
        "full_name": "Pilot Program for Climate Resilience",
        "eligible_countries": [
            "Bangladesh", "Bolivia", "Cambodia", "Mozambique", "Nepal",
            "Niger", "Pacific Islands", "Tajikistan", "Yemen", "Zambia",
            "Haiti", "Honduras", "Niger", "Samoa", "Papua New Guinea",
        ],
        "min_project_m": 5.0,
        "grant_element_pct": 50.0,
        "concessional_rate_pct": 0.10,
        "focus_areas": [
            "climate_resilient_agriculture", "water_security",
            "coastal_protection", "disaster_risk_reduction",
        ],
    },
    "FIP": {
        "focus": "Forest Investment Program — reducing deforestation, forest degradation, REDD+",
        "full_name": "Forest Investment Program",
        "eligible_countries": [
            "Brazil", "Burkina Faso", "Cambodia", "Democratic Republic of Congo",
            "Ghana", "Indonesia", "Lao PDR", "Mexico", "Mozambique",
            "Peru", "Nepal", "Bangladesh",
        ],
        "min_project_m": 5.0,
        "grant_element_pct": 40.0,
        "concessional_rate_pct": 0.10,
        "focus_areas": [
            "REDD+_readiness", "sustainable_forest_management",
            "community_forest_tenure", "agroforestry",
        ],
    },
    "SREP": {
        "focus": "Scaling Up Renewable Energy in Low Income Countries Program",
        "full_name": "Scaling Up Renewable Energy Program (Low Income Countries)",
        "eligible_countries": [
            "Ethiopia", "Honduras", "Kenya", "Liberia", "Maldives",
            "Mali", "Mongolia", "Nepal", "Tanzania", "Rwanda",
            "Uganda", "Yemen", "Armenia", "Pacific Islands", "Mozambique",
        ],
        "min_project_m": 3.0,
        "grant_element_pct": 35.0,
        "concessional_rate_pct": 0.10,
        "focus_areas": [
            "solar_mini_grids", "wind_energy", "small_hydro",
            "geothermal", "clean_cooking",
        ],
    },
}

JUST_TRANSITION_SECTOR_PROFILES: dict[str, dict[str, Any]] = {
    "coal": {
        "fossil_employment_m": 7.2,
        "green_employment_potential_m": 4.5,
        "skills_transferability": 2,
        "wage_gap_pct": 35.0,
        "transition_timeline_years": 15,
        "key_transition_risks": [
            "geographic_concentration", "limited_alternative_employers",
            "high_wage_premium_loss", "pension_cliff",
        ],
    },
    "oil_gas": {
        "fossil_employment_m": 10.5,
        "green_employment_potential_m": 9.2,
        "skills_transferability": 4,
        "wage_gap_pct": 20.0,
        "transition_timeline_years": 20,
        "key_transition_risks": [
            "offshore_skill_mismatch", "geographic_dispersion",
            "wage_premium_loss", "long_project_cycles",
        ],
    },
    "steel": {
        "fossil_employment_m": 6.3,
        "green_employment_potential_m": 7.8,
        "skills_transferability": 3,
        "wage_gap_pct": 15.0,
        "transition_timeline_years": 12,
        "key_transition_risks": [
            "green_hydrogen_cost_threshold", "stranded_blast_furnace_assets",
            "import_competition", "capex_intensity",
        ],
    },
    "cement": {
        "fossil_employment_m": 3.2,
        "green_employment_potential_m": 3.0,
        "skills_transferability": 3,
        "wage_gap_pct": 10.0,
        "transition_timeline_years": 15,
        "key_transition_risks": [
            "ccs_availability", "clinker_process_dependency",
            "regional_concentration", "CBAM_exposure",
        ],
    },
    "automotive": {
        "fossil_employment_m": 14.0,
        "green_employment_potential_m": 12.5,
        "skills_transferability": 4,
        "wage_gap_pct": 12.0,
        "transition_timeline_years": 10,
        "key_transition_risks": [
            "ICE_to_EV_skills_gap", "tier2_3_supplier_vulnerability",
            "geographic_clustering", "battery_manufacturing_geography",
        ],
    },
    "aviation": {
        "fossil_employment_m": 5.8,
        "green_employment_potential_m": 5.5,
        "skills_transferability": 5,
        "wage_gap_pct": 8.0,
        "transition_timeline_years": 25,
        "key_transition_risks": [
            "SAF_cost_and_availability", "hydrogen_aircraft_timeline",
            "slow_fleet_replacement", "demand_risk",
        ],
    },
    "shipping": {
        "fossil_employment_m": 1.9,
        "green_employment_potential_m": 2.1,
        "skills_transferability": 4,
        "wage_gap_pct": 5.0,
        "transition_timeline_years": 20,
        "key_transition_risks": [
            "ammonia_methanol_fuel_expertise", "port_infrastructure_readiness",
            "flag_state_regulation_divergence",
        ],
    },
    "agriculture": {
        "fossil_employment_m": 875.0,
        "green_employment_potential_m": 950.0,
        "skills_transferability": 3,
        "wage_gap_pct": 5.0,
        "transition_timeline_years": 20,
        "key_transition_risks": [
            "smallholder_financing_access", "climate_adaptation_technology_cost",
            "methane_reduction_income_impact", "deforestation_dependent_livelihoods",
        ],
    },
}

# ---------------------------------------------------------------------------
# Internal helper constants
# ---------------------------------------------------------------------------

_ILO_TIER_THRESHOLDS = [
    (80.0, "leading"),
    (65.0, "advanced"),
    (45.0, "developing"),
    (0.0, "early"),
]

_JT_RISK_TIERS = [
    (75.0, "low"),
    (55.0, "medium"),
    (35.0, "high"),
    (0.0, "critical"),
]

_COMMUNITY_VULNERABILITY_TIERS = [
    (70.0, "resilient"),
    (50.0, "moderate"),
    (30.0, "vulnerable"),
    (0.0, "highly_vulnerable"),
]

# ---------------------------------------------------------------------------
# Engine class
# ---------------------------------------------------------------------------


class JustTransitionEngine:
    """
    Just Transition Finance Engine (E89).

    Covers ILO JT Principles, EU JTF eligibility, workforce modelling,
    community resilience, and CIF facility eligibility.
    All methods accept a plain dict; missing fields handled via .get().
    """

    # ------------------------------------------------------------------
    # 1. ILO Principles Assessment
    # ------------------------------------------------------------------

    def assess_ilo_principles(self, entity_data: dict) -> dict:
        """
        Score all 5 ILO Just Transition Guiding Principles (2015).
        Computes weighted composite, identifies gaps, assigns tier.

        Expected keys: entity_id, region_name, country,
                        principle_scores dict (principle_name → 0-100),
                        sector
        """
        entity_id = entity_data.get("entity_id", "ENTITY_001")
        region_name = entity_data.get("region_name", "Unknown Region")
        country = entity_data.get("country", "Unknown")
        sector = entity_data.get("sector", "coal")
        principle_scores: dict = entity_data.get("principle_scores", {})

        principle_results: dict[str, dict] = {}
        composite_score = 0.0
        total_weight = 0.0
        gaps: list[str] = []

        for principle, meta in ILO_JT_PRINCIPLES.items():
            raw_score = float(principle_scores.get(principle, 40.0))
            raw_score = min(100.0, raw_score)
            weight = meta["weight"]

            # Sub-criteria gap check — assume each sub-criterion scores raw_score/100
            sub_gaps = []
            for sc in meta["sub_criteria"]:
                if raw_score < 50.0:
                    sub_gaps.append(sc)

            if raw_score < 50.0:
                gaps.append(
                    f"{principle}: score {raw_score:.0f}% — "
                    f"{meta['description'][:60]}..."
                )

            principle_results[principle] = {
                "description": meta["description"],
                "ILO_ref": meta["ILO_ref"],
                "weight": weight,
                "score": round(raw_score, 1),
                "weighted_contribution": round(raw_score * weight, 2),
                "sub_criteria": meta["sub_criteria"],
                "sub_criteria_gaps": sub_gaps,
            }

            composite_score += raw_score * weight
            total_weight += weight

        composite_score = round(composite_score / total_weight if total_weight else 0.0, 2)

        # Tier assignment
        tier = "early"
        for threshold, label in _ILO_TIER_THRESHOLDS:
            if composite_score >= threshold:
                tier = label
                break

        return {
            "entity_id": entity_id,
            "region_name": region_name,
            "country": country,
            "sector": sector,
            "principle_results": principle_results,
            "ilo_composite_score": composite_score,
            "ilo_tier": tier,
            "gaps": gaps,
            "total_principles_scored": len(principle_results),
            "principles_meeting_50pct": sum(
                1 for p in principle_results.values() if p["score"] >= 50.0
            ),
            "standard": "ILO Just Transition Guidelines 2015",
        }

    # ------------------------------------------------------------------
    # 2. EU JTF Eligibility Assessment
    # ------------------------------------------------------------------

    def assess_eu_jtf_eligibility(self, entity_data: dict) -> dict:
        """
        Check 8 EU JTF eligibility criteria (JTF Reg 2021/1056 Art 8).
        Compute territorial just transition score and estimate JTF allocation.

        Expected keys: entity_id, region_name, country, nuts2_code,
                        criteria_status dict (criterion → met bool),
                        regional_gdp_m_eur, population_k,
                        fossil_employment_k, total_employment_k
        """
        entity_id = entity_data.get("entity_id", "ENTITY_001")
        region_name = entity_data.get("region_name", "Unknown Region")
        country = entity_data.get("country", "Unknown")
        nuts2_code = entity_data.get("nuts2_code", "XX00")
        criteria_status: dict = entity_data.get("criteria_status", {})
        regional_gdp_m = float(entity_data.get("regional_gdp_m_eur", 5_000.0))
        population_k = float(entity_data.get("population_k", 1_000.0))
        fossil_employment_k = float(entity_data.get("fossil_employment_k", 50.0))
        total_employment_k = float(entity_data.get("total_employment_k", 500.0))

        total_points = 0
        max_points = sum(c["points"] for c in EU_JTF_ELIGIBILITY_CRITERIA.values())
        criteria_results: dict[str, dict] = {}
        gaps: list[str] = []

        for crit, meta in EU_JTF_ELIGIBILITY_CRITERIA.items():
            met = bool(criteria_status.get(crit, False))
            pts = meta["points"] if met else 0
            total_points += pts

            if not met:
                gaps.append(f"{crit}: {meta['description']}")

            criteria_results[crit] = {
                "description": meta["description"],
                "threshold": meta["threshold"],
                "points_available": meta["points"],
                "points_earned": pts,
                "met": met,
            }

        jtf_score = round((total_points / max_points) * 100.0, 2) if max_points > 0 else 0.0
        jtf_eligible = jtf_score >= 50.0

        # JTF allocation estimate (simplified formula based on fossil employment share)
        fossil_share = fossil_employment_k / total_employment_k if total_employment_k > 0 else 0
        base_allocation_m = regional_gdp_m * fossil_share * 0.10  # 10% of fossil GDP exposure
        score_multiplier = jtf_score / 100.0
        jtf_allocation_m = round(base_allocation_m * score_multiplier, 2)

        return {
            "entity_id": entity_id,
            "region_name": region_name,
            "country": country,
            "nuts2_code": nuts2_code,
            "criteria_results": criteria_results,
            "total_points_earned": total_points,
            "max_points": max_points,
            "jtf_territorial_score": jtf_score,
            "jtf_eligible": jtf_eligible,
            "jtf_allocation_estimate_m_eur": jtf_allocation_m,
            "fossil_employment_share_pct": round(fossil_share * 100, 2),
            "gaps": gaps,
            "regulation": "EU Just Transition Fund Regulation (EU) 2021/1056",
        }

    # ------------------------------------------------------------------
    # 3. Workforce Transition Modelling
    # ------------------------------------------------------------------

    def model_workforce_transition(self, entity_data: dict) -> dict:
        """
        Model the workforce transition:
        affected workers, green jobs created, net jobs, wage gap,
        reskilling cost (€M per worker), and timeline.

        Expected keys: entity_id, sector, region_name, country,
                        fossil_workers_k, green_jobs_pipeline_k,
                        avg_fossil_wage_usd, avg_green_wage_usd,
                        reskilling_duration_months, reskilling_cost_per_worker_usd,
                        phase_out_start_year, phase_out_end_year,
                        jetp_pledge bool
        """
        entity_id = entity_data.get("entity_id", "ENTITY_001")
        sector = entity_data.get("sector", "coal")
        region_name = entity_data.get("region_name", "Unknown Region")
        country = entity_data.get("country", "Unknown")

        sector_profile = JUST_TRANSITION_SECTOR_PROFILES.get(sector, {})

        fossil_workers_k = float(
            entity_data.get("fossil_workers_k", sector_profile.get("fossil_employment_m", 10.0))
        )
        green_jobs_k = float(
            entity_data.get(
                "green_jobs_pipeline_k",
                sector_profile.get("green_employment_potential_m", fossil_workers_k * 0.8),
            )
        )
        avg_fossil_wage = float(entity_data.get("avg_fossil_wage_usd", 45_000.0))
        avg_green_wage = float(entity_data.get("avg_green_wage_usd", 38_000.0))
        reskilling_months = float(entity_data.get("reskilling_duration_months", 12.0))
        reskilling_cost_per_worker = float(
            entity_data.get("reskilling_cost_per_worker_usd", 9_000.0)
        )
        phase_out_start = int(entity_data.get("phase_out_start_year", 2025))
        phase_out_end = int(entity_data.get("phase_out_end_year", 2035))
        jetp_pledge = bool(entity_data.get("jetp_pledge", False))

        # Transition timeline
        transition_years = max(1, phase_out_end - phase_out_start)
        workers_displaced_pa_k = fossil_workers_k / transition_years

        # Net jobs
        net_jobs_k = green_jobs_k - fossil_workers_k
        net_jobs_pct = (net_jobs_k / fossil_workers_k * 100.0) if fossil_workers_k > 0 else 0.0

        # Wage transition gap
        wage_gap_usd = avg_fossil_wage - avg_green_wage
        wage_gap_pct = (wage_gap_usd / avg_fossil_wage * 100.0) if avg_fossil_wage > 0 else 0.0

        # Reskilling cost
        total_reskilling_cost_m = (
            fossil_workers_k * 1_000 * reskilling_cost_per_worker / 1_000_000.0
        )

        # Skills transferability
        skills_score = sector_profile.get("skills_transferability", 3)

        # Income support cost (simplified: wage * income_support_months / 12)
        income_support_months = reskilling_months * 1.5
        income_support_cost_m = (
            fossil_workers_k * 1_000 * avg_fossil_wage * (income_support_months / 12.0) / 1_000_000.0
        )

        # Total transition finance needed
        total_transition_cost_m = total_reskilling_cost_m + income_support_cost_m

        # JETP premium
        jetp_finance_available_m = total_transition_cost_m * 0.30 if jetp_pledge else 0.0

        # Annual green job creation needed
        green_jobs_pa_k = green_jobs_k / transition_years

        return {
            "entity_id": entity_id,
            "sector": sector,
            "region_name": region_name,
            "country": country,
            "fossil_workers_k": fossil_workers_k,
            "green_jobs_pipeline_k": green_jobs_k,
            "net_jobs_k": round(net_jobs_k, 2),
            "net_jobs_pct": round(net_jobs_pct, 2),
            "workers_displaced_pa_k": round(workers_displaced_pa_k, 3),
            "green_jobs_created_pa_k": round(green_jobs_pa_k, 3),
            "avg_fossil_wage_usd": avg_fossil_wage,
            "avg_green_wage_usd": avg_green_wage,
            "wage_gap_usd": round(wage_gap_usd, 2),
            "wage_gap_pct": round(wage_gap_pct, 2),
            "reskilling_duration_months": reskilling_months,
            "reskilling_cost_per_worker_usd": reskilling_cost_per_worker,
            "total_reskilling_cost_m_usd": round(total_reskilling_cost_m, 2),
            "income_support_cost_m_usd": round(income_support_cost_m, 2),
            "total_transition_cost_m_usd": round(total_transition_cost_m, 2),
            "skills_transferability_score": skills_score,
            "phase_out_start_year": phase_out_start,
            "phase_out_end_year": phase_out_end,
            "transition_years": transition_years,
            "jetp_pledge": jetp_pledge,
            "jetp_finance_available_m_usd": round(jetp_finance_available_m, 2),
            "key_transition_risks": sector_profile.get("key_transition_risks", []),
        }

    # ------------------------------------------------------------------
    # 4. Community Resilience Assessment
    # ------------------------------------------------------------------

    def assess_community_resilience(self, entity_data: dict) -> dict:
        """
        Assess community resilience to fossil fuel transition.
        Scores GDP dependency, infrastructure, employer diversity,
        skills transferability, social cohesion, and vulnerability.

        Expected keys: entity_id, region_name, country,
                        gdp_fossil_dependency_pct, infrastructure_score (0-100),
                        alternative_employer_count, skills_transferability (1-5),
                        social_cohesion_score (0-100), coal_profile_key
        """
        entity_id = entity_data.get("entity_id", "ENTITY_001")
        region_name = entity_data.get("region_name", "Unknown Region")
        country = entity_data.get("country", "Unknown")

        # Try to use coal community profile for defaults
        coal_key = entity_data.get("coal_profile_key")
        profile = COAL_COMMUNITY_PROFILES.get(coal_key, {}) if coal_key else {}

        gdp_fossil_pct = float(entity_data.get("gdp_fossil_dependency_pct", 15.0))
        infrastructure_score = float(entity_data.get("infrastructure_score", 55.0))
        alt_employer_count = int(entity_data.get("alternative_employer_count", 5))
        skills_score_raw = float(entity_data.get("skills_transferability", 3.0))  # 1-5
        social_cohesion = float(entity_data.get("social_cohesion_score", 60.0))
        alt_sector_score = float(
            entity_data.get(
                "alternative_sector_score",
                profile.get("alternative_sector_score", 0.40),
            )
        )

        # Score normalisation
        gdp_dependency_score = max(0.0, 100.0 - gdp_fossil_pct * 3.0)
        employer_diversity_score = min(100.0, alt_employer_count * 8.0)
        skills_norm = (skills_score_raw / 5.0) * 100.0
        alt_sector_norm = alt_sector_score * 100.0

        # Composite resilience score
        resilience_score = round(
            gdp_dependency_score * 0.20
            + infrastructure_score * 0.20
            + employer_diversity_score * 0.20
            + skills_norm * 0.15
            + social_cohesion * 0.15
            + alt_sector_norm * 0.10,
            2,
        )

        # Vulnerability tier
        vulnerability_tier = "highly_vulnerable"
        for threshold, label in _COMMUNITY_VULNERABILITY_TIERS:
            if resilience_score >= threshold:
                vulnerability_tier = label
                break

        # Recommendations
        recommendations: list[str] = []
        if gdp_fossil_pct > 20:
            recommendations.append("Accelerate economic diversification — GDP exposure >20%")
        if alt_employer_count < 5:
            recommendations.append("Attract alternative anchor employers to the region")
        if skills_score_raw < 3:
            recommendations.append("Invest in reskilling for transferable skills")
        if social_cohesion < 50:
            recommendations.append("Strengthen community cohesion and grievance mechanisms")

        return {
            "entity_id": entity_id,
            "region_name": region_name,
            "country": country,
            "coal_profile": profile if profile else None,
            "gdp_fossil_dependency_pct": gdp_fossil_pct,
            "gdp_dependency_score": round(gdp_dependency_score, 1),
            "infrastructure_score": infrastructure_score,
            "alternative_employer_count": alt_employer_count,
            "employer_diversity_score": round(employer_diversity_score, 1),
            "skills_transferability_raw": skills_score_raw,
            "skills_norm_score": round(skills_norm, 1),
            "social_cohesion_score": social_cohesion,
            "alternative_sector_score_raw": alt_sector_score,
            "alt_sector_norm_score": round(alt_sector_norm, 1),
            "community_resilience_score": resilience_score,
            "vulnerability_tier": vulnerability_tier,
            "transition_fund_available_m": profile.get("transition_fund_available_m", 0.0),
            "recommendations": recommendations,
        }

    # ------------------------------------------------------------------
    # 5. CIF Facility Eligibility
    # ------------------------------------------------------------------

    def assess_cif_eligibility(self, entity_data: dict) -> dict:
        """
        Check eligibility for all 4 CIF facilities.
        Returns concessional finance available (€M) and blended ratio.

        Expected keys: entity_id, country, sector, project_type,
                        project_cost_m, income_group, has_national_climate_plan,
                        forest_coverage_pct, grid_electrification_rate_pct
        """
        entity_id = entity_data.get("entity_id", "ENTITY_001")
        country = entity_data.get("country", "Kenya")
        sector = entity_data.get("sector", "energy")
        project_type = entity_data.get("project_type", "renewable_energy")
        project_cost_m = float(entity_data.get("project_cost_m", 100.0))
        income_group = entity_data.get("income_group", "lower_middle")
        has_climate_plan = bool(entity_data.get("has_national_climate_plan", True))
        forest_coverage_pct = float(entity_data.get("forest_coverage_pct", 30.0))
        grid_electrification = float(entity_data.get("grid_electrification_rate_pct", 50.0))

        facility_results: dict[str, dict] = {}
        total_concessional_m = 0.0

        for facility_key, facility in CIF_FACILITY_PROFILES.items():
            eligible_countries = facility["eligible_countries"]
            country_eligible = country in eligible_countries
            min_size = facility["min_project_m"]
            size_eligible = project_cost_m >= min_size

            # Additional eligibility logic per facility
            extra_eligible = True
            eligibility_reason = []

            if facility_key == "CTF":
                # CTF targets middle-income countries with clean tech potential
                if income_group not in ["lower_middle", "upper_middle"]:
                    extra_eligible = False
                    eligibility_reason.append("CTF targets lower/upper middle income countries")
            elif facility_key == "PPCR":
                # PPCR targets LICs + climate vulnerable countries
                if income_group not in ["low", "lower_middle"]:
                    extra_eligible = False
                    eligibility_reason.append("PPCR targets low and lower-middle income countries")
            elif facility_key == "FIP":
                if forest_coverage_pct < 15.0:
                    extra_eligible = False
                    eligibility_reason.append(
                        f"FIP requires >15% forest coverage (current: {forest_coverage_pct}%)"
                    )
            elif facility_key == "SREP":
                if grid_electrification > 80.0:
                    extra_eligible = False
                    eligibility_reason.append(
                        "SREP targets countries with grid electrification <80%"
                    )

            eligible = country_eligible and size_eligible and extra_eligible and has_climate_plan

            if eligible:
                grant_m = project_cost_m * (facility["grant_element_pct"] / 100.0)
                concessional_m = project_cost_m * 0.50  # 50% concessional tranche assumption
                total_concessional_m += concessional_m
            else:
                grant_m = 0.0
                concessional_m = 0.0

            facility_results[facility_key] = {
                "name": facility["full_name"],
                "focus": facility["focus"],
                "country_eligible": country_eligible,
                "size_eligible": size_eligible,
                "extra_eligible": extra_eligible,
                "eligible": eligible,
                "grant_element_pct": facility["grant_element_pct"],
                "grant_available_m": round(grant_m, 2),
                "concessional_tranche_m": round(concessional_m, 2),
                "min_project_size_m": min_size,
                "ineligibility_reasons": eligibility_reason if not eligible else [],
                "focus_areas": facility["focus_areas"],
            }

        eligible_facilities = [k for k, v in facility_results.items() if v["eligible"]]
        blended_ratio = total_concessional_m / project_cost_m if project_cost_m > 0 else 0.0

        return {
            "entity_id": entity_id,
            "country": country,
            "sector": sector,
            "project_type": project_type,
            "project_cost_m": project_cost_m,
            "income_group": income_group,
            "has_national_climate_plan": has_climate_plan,
            "facility_results": facility_results,
            "eligible_facilities": eligible_facilities,
            "total_concessional_finance_m": round(total_concessional_m, 2),
            "blended_finance_ratio": round(blended_ratio, 3),
            "source": "Climate Investment Funds (CIF) — CTF / PPCR / FIP / SREP",
        }

    # ------------------------------------------------------------------
    # 6. Full Assessment (orchestrator)
    # ------------------------------------------------------------------

    def run_full_assessment(self, entity_data: dict) -> dict:
        """
        Orchestrates all E89 sub-assessments and produces a consolidated
        just transition finance report.

        Produces:
        - just_transition_score (0-100)
        - transition_risk_tier
        - ilo_composite_score
        - eu_jtf_eligible
        - net_jobs_impact
        - reskilling_cost_m
        """
        ilo = self.assess_ilo_principles(entity_data)
        jtf = self.assess_eu_jtf_eligibility(entity_data)
        workforce = self.model_workforce_transition(entity_data)
        community = self.assess_community_resilience(entity_data)
        cif = self.assess_cif_eligibility(entity_data)

        # Composite just transition score
        ilo_score = ilo["ilo_composite_score"]
        jtf_score = jtf["jtf_territorial_score"]
        community_score = community["community_resilience_score"]

        # Net jobs impact (positive = job creation; negative = net loss)
        net_jobs_k = workforce["net_jobs_k"]
        net_jobs_norm = min(100.0, max(0.0, 50.0 + net_jobs_k * 5.0))

        just_transition_score = round(
            ilo_score * 0.30
            + jtf_score * 0.25
            + community_score * 0.25
            + net_jobs_norm * 0.20,
            2,
        )

        # Transition risk tier
        transition_risk_tier = "critical"
        for threshold, label in _JT_RISK_TIERS:
            if just_transition_score >= threshold:
                transition_risk_tier = label
                break

        # Aggregate gaps
        all_gaps = ilo["gaps"] + jtf["gaps"] + community["recommendations"]
        priority_gaps = all_gaps[:6]

        return {
            "entity_id": entity_data.get("entity_id", "ENTITY_001"),
            "region_name": entity_data.get("region_name", "Unknown"),
            "country": entity_data.get("country", "Unknown"),
            "sector": entity_data.get("sector", "coal"),
            "just_transition_score": just_transition_score,
            "transition_risk_tier": transition_risk_tier,
            "ilo_composite_score": ilo_score,
            "ilo_tier": ilo["ilo_tier"],
            "eu_jtf_eligible": jtf["jtf_eligible"],
            "eu_jtf_score": jtf_score,
            "eu_jtf_allocation_estimate_m_eur": jtf["jtf_allocation_estimate_m_eur"],
            "net_jobs_k": net_jobs_k,
            "net_jobs_pct": workforce["net_jobs_pct"],
            "reskilling_cost_m_usd": workforce["total_reskilling_cost_m_usd"],
            "total_transition_cost_m_usd": workforce["total_transition_cost_m_usd"],
            "community_resilience_score": community_score,
            "vulnerability_tier": community["vulnerability_tier"],
            "cif_eligible_facilities": cif["eligible_facilities"],
            "cif_concessional_finance_m": cif["total_concessional_finance_m"],
            "priority_gaps": priority_gaps,
            "sub_assessments": {
                "ilo_principles": ilo,
                "eu_jtf_eligibility": jtf,
                "workforce_transition": workforce,
                "community_resilience": community,
                "cif_eligibility": cif,
            },
            "methodology": (
                "ILO JT Guidelines 2015 | EU JTF Reg (EU) 2021/1056 | "
                "CIF Facilities | World Bank JT Framework 2022"
            ),
        }
