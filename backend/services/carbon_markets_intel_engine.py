"""
Carbon Markets Intelligence Engine — E46
==========================================
Paris Art 6.2/6.4 · VCMI Claims Code (Gold/Silver/Bronze)
ICVCM 10 CCPs · CORSIA Phase 2 · VCM registry pricing model

References:
  - VCMI Claims Code of Practice v1.0 (2023)
  - ICVCM Core Carbon Principles (CCP) v2.0 (2023)
  - ICAO CORSIA: Eligible Emissions Unit Criteria (Phase 2, 2024-2026)
  - Paris Agreement Article 6.2 (bilateral ITMOs) & 6.4 mechanism
  - Verra VCS Standard v4.5 / Gold Standard for the Global Goals v2.3
  - ACR Standard v8.0 / CAR Standard v14.5
  - Taskforce on Scaling Voluntary Carbon Markets (TSVCM) 2021
"""
from __future__ import annotations

import math
import random
import uuid
from datetime import date
from typing import Any, Optional


# ---------------------------------------------------------------------------
# VCMI Claims Code of Practice
# ---------------------------------------------------------------------------

VCMI_CLAIMS_CODE: dict[str, dict] = {
    "gold": {
        "label": "VCMI Gold",
        "criteria": [
            "abatement_>90pct",
            "sbti_1.5c_aligned",
            "near_term_target_validated",
            "all_scopes_covered",
        ],
        "mitigation_contribution_min": 0.20,
        "description": "Company has reduced >90% of its emissions and contributes ≥20% of remaining to mitigation",
        "credibility_weight": 1.0,
    },
    "silver": {
        "label": "VCMI Silver",
        "criteria": [
            "abatement_>45pct",
            "sbti_well_below_2c",
            "near_term_target_validated",
        ],
        "mitigation_contribution_min": 0.10,
        "description": "Company has reduced >45% of emissions and contributes ≥10% of remaining to mitigation",
        "credibility_weight": 0.75,
    },
    "bronze": {
        "label": "VCMI Bronze",
        "criteria": [
            "on_sbti_pathway",
        ],
        "mitigation_contribution_min": 0.05,
        "description": "Company is on SBTi pathway and contributes ≥5% of emissions to mitigation",
        "credibility_weight": 0.50,
    },
}

# ---------------------------------------------------------------------------
# ICVCM — 10 Core Carbon Principles
# ---------------------------------------------------------------------------

ICVCM_10_CCPS: list[dict] = [
    {"id": "CCP01", "name": "Effective Governance",         "category": "governance",       "weight": 0.12},
    {"id": "CCP02", "name": "Tracking",                     "category": "governance",       "weight": 0.10},
    {"id": "CCP03", "name": "Transparency",                 "category": "governance",       "weight": 0.10},
    {"id": "CCP04", "name": "Robust Independent Third-Party Validation and Verification",
                                                             "category": "governance",       "weight": 0.12},
    {"id": "CCP05", "name": "Additionality",                "category": "emissions_impact", "weight": 0.12},
    {"id": "CCP06", "name": "Permanence",                   "category": "emissions_impact", "weight": 0.10},
    {"id": "CCP07", "name": "Robust Quantification of Emission Reductions and Removals",
                                                             "category": "emissions_impact", "weight": 0.10},
    {"id": "CCP08", "name": "No Double Counting",           "category": "emissions_impact", "weight": 0.10},
    {"id": "CCP09", "name": "Sustainable Development Benefits and Safeguards",
                                                             "category": "sustainable_dev",  "weight": 0.07},
    {"id": "CCP10", "name": "Contribution to Net Zero Transition",
                                                             "category": "sustainable_dev",  "weight": 0.07},
]

# ---------------------------------------------------------------------------
# CORSIA Phase 2 Eligible Schemes (2024-2026)
# ---------------------------------------------------------------------------

CORSIA_PHASE2_ELIGIBLE_SCHEMES: list[str] = [
    "American Carbon Registry (ACR)",
    "Architecture for REDD+ Transactions (ART TREES)",
    "Climate Action Reserve (CAR)",
    "Gold Standard",
    "Plan Vivo",
    "Verra VCS with CORSIA Label",
    "Global Carbon Council (GCC)",
    "Social Carbon Standard",
]

# ---------------------------------------------------------------------------
# Article 6 Bilateral Agreements (sample 20 country-pairs)
# ---------------------------------------------------------------------------

ARTICLE6_BILATERAL_AGREEMENTS: dict[str, dict] = {
    "CH-GH": {"parties": ["Switzerland", "Ghana"],       "status": "active",  "signed": "2020-11"},
    "CH-SN": {"parties": ["Switzerland", "Senegal"],     "status": "active",  "signed": "2021-06"},
    "CH-VN": {"parties": ["Switzerland", "Viet Nam"],    "status": "signed",  "signed": "2022-07"},
    "JP-TH": {"parties": ["Japan", "Thailand"],          "status": "active",  "signed": "2013-01"},
    "JP-IN": {"parties": ["Japan", "India"],             "status": "active",  "signed": "2010-06"},
    "JP-ID": {"parties": ["Japan", "Indonesia"],         "status": "active",  "signed": "2013-08"},
    "JP-MN": {"parties": ["Japan", "Mongolia"],          "status": "active",  "signed": "2012-01"},
    "JP-BD": {"parties": ["Japan", "Bangladesh"],        "status": "signed",  "signed": "2023-06"},
    "SE-GH": {"parties": ["Sweden", "Ghana"],            "status": "pending", "signed": None},
    "SE-RW": {"parties": ["Sweden", "Rwanda"],           "status": "signed",  "signed": "2022-11"},
    "NL-MX": {"parties": ["Netherlands", "Mexico"],      "status": "pending", "signed": None},
    "DE-KE": {"parties": ["Germany", "Kenya"],           "status": "signed",  "signed": "2023-03"},
    "SG-TH": {"parties": ["Singapore", "Thailand"],      "status": "signed",  "signed": "2022-09"},
    "SG-PH": {"parties": ["Singapore", "Philippines"],   "status": "active",  "signed": "2023-01"},
    "KR-VN": {"parties": ["South Korea", "Viet Nam"],    "status": "active",  "signed": "2021-12"},
    "KR-PH": {"parties": ["South Korea", "Philippines"], "status": "pending", "signed": None},
    "CA-NA": {"parties": ["Canada", "Namibia"],          "status": "pending", "signed": None},
    "AU-PG": {"parties": ["Australia", "Papua New Guinea"], "status": "signed", "signed": "2022-03"},
    "UK-GH": {"parties": ["United Kingdom", "Ghana"],    "status": "signed",  "signed": "2023-08"},
    "US-CO": {"parties": ["United States", "Colombia"],  "status": "pending", "signed": None},
}

# ---------------------------------------------------------------------------
# Registry Methodology Types
# ---------------------------------------------------------------------------

REGISTRY_METHODOLOGY_TYPES: dict[str, list[str]] = {
    "Verra VCS": [
        "VM0007_REDD+_Methodology_Framework",
        "VM0009_Avoided_Deforestation",
        "VM0010_IFM_Methodology",
        "VM0015_Improved_Cookstoves",
        "VM0022_Energy_Efficiency_HH",
        "VM0031_Methodology_for_Pretreatment",
        "VM0036_REDD+_AFOLU_Methodologies",
        "VM0041_Methane_Emission_Reduction",
        "VM0042_Clean_Water_Provision",
        "VM0047_Afforestation_Reforestation",
    ],
    "Gold Standard": [
        "GS_TPDDTEC_Thermal_Power",
        "GS_MSPE_Methodology_Small_Power",
        "GS_ICS_Improved_Cookstoves",
        "GS_SSE_Safe_Storage_Energy",
        "GS_WASH_Water_Access",
        "GS_LR_Land_Restoration",
    ],
    "ACR": [
        "ACR_AT_Afforestation_Reforestation",
        "ACR_IFM_Improved_Forest_Management",
        "ACR_ODS_Ozone_Depleting_Substances",
        "ACR_CH4_Methane_Capture",
    ],
    "CAR": [
        "CAR_OM_Ozone_Methane",
        "CAR_IFM_Forest_Protocol",
        "CAR_US_Livestock",
        "CAR_Soil_Enrichment",
    ],
}

# ---------------------------------------------------------------------------
# Carbon Price Benchmarks (USD/tCO2e)
# ---------------------------------------------------------------------------

CARBON_PRICE_BENCHMARKS: dict[str, dict] = {
    "nature_based":       {"vintage_2023": 18, "vintage_2020": 12, "vintage_2015": 8},
    "renewables":         {"vintage_2023": 4,  "vintage_2020": 3,  "vintage_2015": 2},
    "cookstoves":         {"vintage_2023": 8,  "vintage_2020": 5,  "vintage_2015": 3},
    "methane_avoidance":  {"vintage_2023": 6,  "vintage_2020": 4,  "vintage_2015": 2},
    "soil_carbon":        {"vintage_2023": 12, "vintage_2020": 8,  "vintage_2015": 5},
    "blue_carbon":        {"vintage_2023": 25, "vintage_2020": 16, "vintage_2015": 10},
    "direct_air_capture": {"vintage_2023": 80, "vintage_2020": 60, "vintage_2015": 40},
    "bioenergy_ccs":      {"vintage_2023": 55, "vintage_2020": 40, "vintage_2015": 25},
}

# ---------------------------------------------------------------------------
# Co-Benefit Premiums
# ---------------------------------------------------------------------------

CO_BENEFIT_PREMIUMS: dict[str, float] = {
    "sdg_multiple":     15.0,  # aligns with multiple UN SDGs
    "biodiversity":     12.0,  # IPLC, high-biodiversity area
    "livelihoods":       8.0,  # direct community livelihood benefits
    "water":             6.0,  # clean water access
    "gender_equality":   5.0,  # women-focused benefits
    "basic":             2.0,  # single generic co-benefit
}


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class CarbonMarketsIntelEngine:

    # ------------------------------------------------------------------
    # 1. VCMI Claim Screening
    # ------------------------------------------------------------------

    def screen_vcmi_claim(
        self,
        entity_id: str,
        abatement_pct: float,
        sbti_status: str,
        scope_coverage: list[str],
        mitigation_contribution_pct: float,
    ) -> dict[str, Any]:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)
        gaps = []
        credibility_score = 0.0

        # Gold criteria
        gold_eligible = (
            abatement_pct >= 90
            and sbti_status in ("validated_1.5c", "approved_1.5c")
            and all(s in scope_coverage for s in ["scope1", "scope2", "scope3"])
            and mitigation_contribution_pct >= VCMI_CLAIMS_CODE["gold"]["mitigation_contribution_min"]
        )

        # Silver criteria
        silver_eligible = (
            abatement_pct >= 45
            and sbti_status in ("validated_1.5c", "validated_wb2c", "approved_1.5c", "approved_wb2c")
            and mitigation_contribution_pct >= VCMI_CLAIMS_CODE["silver"]["mitigation_contribution_min"]
        )

        # Bronze criteria
        bronze_eligible = (
            sbti_status not in ("not_committed", "none", "")
            and mitigation_contribution_pct >= VCMI_CLAIMS_CODE["bronze"]["mitigation_contribution_min"]
        )

        if gold_eligible:
            claim_level = "gold"
            credibility_score = 95.0
        elif silver_eligible:
            claim_level = "silver"
            credibility_score = 72.0
        elif bronze_eligible:
            claim_level = "bronze"
            credibility_score = 50.0
        else:
            claim_level = "not_eligible"
            credibility_score = 20.0

        # Build gaps
        if abatement_pct < 90:
            gaps.append(f"Abatement {abatement_pct}% below Gold 90% threshold")
        if abatement_pct < 45:
            gaps.append(f"Abatement {abatement_pct}% below Silver 45% threshold")
        if sbti_status in ("not_committed", "none", ""):
            gaps.append("No SBTi commitment — minimum Bronze requirement")
        if "scope3" not in scope_coverage:
            gaps.append("Scope 3 not covered — required for Gold claim")
        if mitigation_contribution_pct < VCMI_CLAIMS_CODE["bronze"]["mitigation_contribution_min"]:
            gaps.append(f"Mitigation contribution {mitigation_contribution_pct:.1%} below Bronze 5% minimum")

        credibility_score += rng.uniform(-3, 3)
        credibility_score = round(min(100, max(0, credibility_score)), 1)

        return {
            "entity_id": entity_id,
            "claim_level": claim_level,
            "claim_label": VCMI_CLAIMS_CODE.get(claim_level, {}).get("label", "Not Eligible"),
            "credibility_score": credibility_score,
            "abatement_pct": abatement_pct,
            "sbti_status": sbti_status,
            "scope_coverage": scope_coverage,
            "mitigation_contribution_pct": mitigation_contribution_pct,
            "gaps": gaps,
            "next_steps": [
                "Validate SBTi targets through SBTi approval process",
                "Ensure all scope 3 categories quantified and disclosed",
                "Procure high-quality ICVCM CCP-approved credits for mitigation contribution",
            ],
            "assessment_id": str(uuid.uuid4()),
        }

    # ------------------------------------------------------------------
    # 2. ICVCM CCP Assessment
    # ------------------------------------------------------------------

    def assess_icvcm_ccps(
        self,
        entity_id: str,
        credit_portfolio: list[dict],
    ) -> dict[str, Any]:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        ccp_results = []
        category_scores: dict[str, list[float]] = {"governance": [], "emissions_impact": [], "sustainable_dev": []}
        total_credits = sum(c.get("volume_tco2e", 0) for c in credit_portfolio)
        passing_credits = 0.0

        for ccp in ICVCM_10_CCPS:
            # Derive pass/fail from portfolio quality signals
            pass_votes = 0
            for credit in credit_portfolio:
                registry = credit.get("registry", "Verra VCS")
                has_corsia = credit.get("corsia_eligible", False)
                independent_audit = credit.get("independent_audit", rng.random() > 0.3)
                vintage = int(credit.get("vintage_year", 2021))

                if ccp["id"] == "CCP01" and registry in REGISTRY_METHODOLOGY_TYPES:
                    pass_votes += 1
                elif ccp["id"] == "CCP02" and registry in ["Verra VCS", "Gold Standard", "ACR"]:
                    pass_votes += 1
                elif ccp["id"] == "CCP04" and independent_audit:
                    pass_votes += 1
                elif ccp["id"] == "CCP05":
                    pass_votes += (1 if vintage >= 2016 else 0)
                elif ccp["id"] == "CCP08" and has_corsia:
                    pass_votes += 1
                else:
                    pass_votes += 1 if rng.random() > 0.25 else 0

            pass_rate = pass_votes / max(len(credit_portfolio), 1)
            ccp_pass = pass_rate >= 0.6

            if ccp_pass:
                passing_credits += total_credits * pass_rate

            score = round(pass_rate * 100, 1)
            category_scores[ccp["category"]].append(score)
            ccp_results.append({
                "ccp_id": ccp["id"],
                "ccp_name": ccp["name"],
                "category": ccp["category"],
                "weight": ccp["weight"],
                "pass": ccp_pass,
                "score": score,
            })

        overall_pass_rate = round(passing_credits / max(total_credits, 1) * 100, 1)
        governance_score = round(sum(category_scores["governance"]) / max(len(category_scores["governance"]), 1), 1)
        emissions_score = round(sum(category_scores["emissions_impact"]) / max(len(category_scores["emissions_impact"]), 1), 1)
        sd_score = round(sum(category_scores["sustainable_dev"]) / max(len(category_scores["sustainable_dev"]), 1), 1)

        return {
            "entity_id": entity_id,
            "credit_portfolio_size": len(credit_portfolio),
            "total_credits_tco2e": total_credits,
            "overall_pass_rate_pct": overall_pass_rate,
            "governance_score": governance_score,
            "emissions_impact_score": emissions_score,
            "sustainable_development_score": sd_score,
            "ccp_results": ccp_results,
            "ccp_approved_pct": round(len([r for r in ccp_results if r["pass"]]) / 10 * 100, 1),
            "assessment_id": str(uuid.uuid4()),
        }

    # ------------------------------------------------------------------
    # 3. CORSIA Phase 2 Eligibility Check
    # ------------------------------------------------------------------

    def check_corsia_eligibility(
        self,
        entity_id: str,
        credit_records: list[dict],
    ) -> dict[str, Any]:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        eligible_volume = 0.0
        ineligible_volume = 0.0
        ineligible_reasons: list[str] = []
        approved_schemes_used: set[str] = set()

        for credit in credit_records:
            volume = float(credit.get("volume_tco2e", 0))
            scheme = credit.get("scheme", "Unknown")
            vintage = int(credit.get("vintage_year", 2020))
            has_ca = credit.get("corresponding_adjustment", False)

            scheme_eligible = scheme in CORSIA_PHASE2_ELIGIBLE_SCHEMES
            vintage_eligible = vintage >= 2016
            ca_eligible = has_ca  # CORSIA Phase 2 requires CA for most credits

            if scheme_eligible and vintage_eligible and ca_eligible:
                eligible_volume += volume
                approved_schemes_used.add(scheme)
            else:
                ineligible_volume += volume
                if not scheme_eligible:
                    reason = f"Scheme '{scheme}' not on CORSIA Phase 2 approved list"
                    if reason not in ineligible_reasons:
                        ineligible_reasons.append(reason)
                if not vintage_eligible:
                    reason = f"Vintage {vintage} pre-2016 — outside CORSIA eligibility window"
                    if reason not in ineligible_reasons:
                        ineligible_reasons.append(reason)
                if not ca_eligible:
                    reason = "Missing corresponding adjustment — required for CORSIA Phase 2"
                    if reason not in ineligible_reasons:
                        ineligible_reasons.append(reason)

        total_volume = eligible_volume + ineligible_volume
        eligible_pct = round(eligible_volume / max(total_volume, 1) * 100, 1)

        return {
            "entity_id": entity_id,
            "total_credits_assessed_tco2e": round(total_volume, 2),
            "eligible_volume_tco2e": round(eligible_volume, 2),
            "ineligible_volume_tco2e": round(ineligible_volume, 2),
            "eligible_pct": eligible_pct,
            "approved_schemes_used": list(approved_schemes_used),
            "ineligible_reasons": ineligible_reasons,
            "corsia_phase": "Phase_2_2024-2026",
            "eligible_scheme_list": CORSIA_PHASE2_ELIGIBLE_SCHEMES,
            "assessment_id": str(uuid.uuid4()),
        }

    # ------------------------------------------------------------------
    # 4. Article 6 Assessment
    # ------------------------------------------------------------------

    def assess_article6(
        self,
        entity_id: str,
        credit_records: list[dict],
        host_country: str = "GH",
    ) -> dict[str, Any]:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        total_volume = sum(float(c.get("volume_tco2e", 0)) for c in credit_records)
        art62_volume = 0.0
        art64_volume = 0.0
        ca_volume = 0.0

        # Find bilateral agreement status
        agreement_key = None
        for key, agr in ARTICLE6_BILATERAL_AGREEMENTS.items():
            if host_country in key:
                agreement_key = key
                break
        bilateral_status = ARTICLE6_BILATERAL_AGREEMENTS.get(agreement_key, {}).get("status", "not_found") if agreement_key else "not_found"

        for credit in credit_records:
            volume = float(credit.get("volume_tco2e", 0))
            mechanism = credit.get("article6_mechanism", rng.choice(["art_6_2", "art_6_4", "other"]))
            has_ca = credit.get("corresponding_adjustment", rng.random() > 0.35)

            if mechanism == "art_6_2":
                art62_volume += volume
            elif mechanism == "art_6_4":
                art64_volume += volume
            if has_ca:
                ca_volume += volume

        itmo_volume = art62_volume + art64_volume

        return {
            "entity_id": entity_id,
            "host_country": host_country,
            "bilateral_agreement_status": bilateral_status,
            "total_credits_tco2e": round(total_volume, 2),
            "itmo_volume_tco2e": round(itmo_volume, 2),
            "art6_2_volume_tco2e": round(art62_volume, 2),
            "art6_4_volume_tco2e": round(art64_volume, 2),
            "art6_2_pct": round(art62_volume / max(total_volume, 1) * 100, 1),
            "art6_4_pct": round(art64_volume / max(total_volume, 1) * 100, 1),
            "corresponding_adjustment_pct": round(ca_volume / max(total_volume, 1) * 100, 1),
            "double_counting_risk": "low" if ca_volume / max(total_volume, 1) > 0.80 else "high",
            "assessment_id": str(uuid.uuid4()),
        }

    # ------------------------------------------------------------------
    # 5. Credit Pricing
    # ------------------------------------------------------------------

    def price_credits(
        self,
        entity_id: str,
        project_type: str,
        vintage_year: int,
        icvcm_pass: bool,
        co_benefits: list[str],
        registry: str = "Verra VCS",
    ) -> dict[str, Any]:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        benchmarks = CARBON_PRICE_BENCHMARKS.get(project_type, CARBON_PRICE_BENCHMARKS["nature_based"])
        current_year = 2024
        if vintage_year >= 2022:
            base_price = benchmarks["vintage_2023"]
        elif vintage_year >= 2018:
            base_price = benchmarks["vintage_2020"]
        else:
            base_price = benchmarks["vintage_2015"]

        # Vintage discount (older credits discounted)
        vintage_age = current_year - vintage_year
        vintage_discount = round(min(0.40, vintage_age * 0.025), 3)
        price_after_vintage = base_price * (1 - vintage_discount)

        # ICVCM additionality premium
        additionality_premium = round(base_price * rng.uniform(0.05, 0.15) if icvcm_pass else 0.0, 2)

        # Co-benefit premiums
        cb_premium_total = sum(CO_BENEFIT_PREMIUMS.get(cb, 0.0) / 100 * base_price for cb in co_benefits)
        co_benefit_premium = round(cb_premium_total, 2)

        # Registry premium/discount
        registry_adj = {"Verra VCS": 1.0, "Gold Standard": 1.08, "ACR": 1.05, "CAR": 1.03}.get(registry, 1.0)

        total_price = round((price_after_vintage + additionality_premium + co_benefit_premium) * registry_adj, 2)

        return {
            "entity_id": entity_id,
            "project_type": project_type,
            "vintage_year": vintage_year,
            "registry": registry,
            "icvcm_pass": icvcm_pass,
            "co_benefits": co_benefits,
            "base_price_usd": base_price,
            "vintage_discount_pct": round(vintage_discount * 100, 1),
            "price_after_vintage_discount": round(price_after_vintage, 2),
            "additionality_premium_usd": additionality_premium,
            "co_benefit_premium_usd": co_benefit_premium,
            "registry_adjustment_factor": registry_adj,
            "total_fair_value_usd": total_price,
            "assessment_id": str(uuid.uuid4()),
        }

    # ------------------------------------------------------------------
    # 6. Portfolio Analysis
    # ------------------------------------------------------------------

    def analyse_portfolio(
        self,
        entity_id: str,
        credit_portfolio: list[dict],
    ) -> dict[str, Any]:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        total_volume = sum(float(c.get("volume_tco2e", 0)) for c in credit_portfolio)
        total_value = 0.0
        registry_mix: dict[str, float] = {}
        methodology_types: dict[str, float] = {}
        vintage_dist: dict[int, float] = {}
        quality_dist = {"high": 0.0, "medium": 0.0, "low": 0.0}

        for credit in credit_portfolio:
            vol = float(credit.get("volume_tco2e", 0))
            registry = credit.get("registry", "Verra VCS")
            project_type = credit.get("project_type", "nature_based")
            vintage = int(credit.get("vintage_year", 2021))
            icvcm = credit.get("icvcm_pass", rng.random() > 0.4)
            cb = credit.get("co_benefits", [])

            price_result = self.price_credits(entity_id, project_type, vintage, icvcm, cb, registry)
            total_value += price_result["total_fair_value_usd"] * vol

            registry_mix[registry] = registry_mix.get(registry, 0) + vol
            methodology_types[project_type] = methodology_types.get(project_type, 0) + vol
            vintage_dist[vintage] = vintage_dist.get(vintage, 0) + vol

            quality = "high" if icvcm and vintage >= 2020 else ("medium" if vintage >= 2017 else "low")
            quality_dist[quality] += vol

        avg_price = round(total_value / max(total_volume, 1), 2)

        # normalise distributions
        for d in [registry_mix, methodology_types]:
            for k in d:
                d[k] = round(d[k] / max(total_volume, 1) * 100, 1)
        for k in vintage_dist:
            vintage_dist[k] = round(vintage_dist[k] / max(total_volume, 1) * 100, 1)
        for k in quality_dist:
            quality_dist[k] = round(quality_dist[k] / max(total_volume, 1) * 100, 1)

        return {
            "entity_id": entity_id,
            "portfolio_size": len(credit_portfolio),
            "total_volume_tco2e": round(total_volume, 2),
            "total_fair_value_usd": round(total_value, 2),
            "weighted_avg_price_usd_per_tco2e": avg_price,
            "registry_mix_pct": registry_mix,
            "project_type_mix_pct": methodology_types,
            "vintage_distribution_pct": vintage_dist,
            "quality_distribution_pct": quality_dist,
            "assessment_id": str(uuid.uuid4()),
        }

    # ------------------------------------------------------------------
    # 7. Full Assessment
    # ------------------------------------------------------------------

    def generate_full_assessment(
        self,
        entity_id: str,
        portfolio_data: dict,
    ) -> dict[str, Any]:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        credit_portfolio = portfolio_data.get("credit_portfolio", [
            {"volume_tco2e": 10000, "registry": "Verra VCS", "project_type": "nature_based",
             "vintage_year": 2022, "icvcm_pass": True, "co_benefits": ["biodiversity", "livelihoods"],
             "scheme": "Verra VCS with CORSIA Label", "corresponding_adjustment": True,
             "article6_mechanism": "art_6_2", "independent_audit": True, "corsia_eligible": True},
            {"volume_tco2e": 5000, "registry": "Gold Standard", "project_type": "cookstoves",
             "vintage_year": 2020, "icvcm_pass": True, "co_benefits": ["sdg_multiple"],
             "scheme": "Gold Standard", "corresponding_adjustment": False,
             "article6_mechanism": "art_6_4", "independent_audit": True, "corsia_eligible": True},
        ])
        host_country = portfolio_data.get("host_country", "GH")
        abatement_pct = portfolio_data.get("abatement_pct", rng.uniform(20, 95))
        sbti_status = portfolio_data.get("sbti_status", rng.choice(["validated_1.5c", "validated_wb2c", "committed", "not_committed"]))
        scope_coverage = portfolio_data.get("scope_coverage", ["scope1", "scope2", "scope3"])
        mitigation_contribution_pct = portfolio_data.get("mitigation_contribution_pct", rng.uniform(0.03, 0.25))

        vcmi = self.screen_vcmi_claim(entity_id, abatement_pct, sbti_status, scope_coverage, mitigation_contribution_pct)
        icvcm = self.assess_icvcm_ccps(entity_id, credit_portfolio)
        corsia = self.check_corsia_eligibility(entity_id, credit_portfolio)
        art6 = self.assess_article6(entity_id, credit_portfolio, host_country)
        portfolio_analysis = self.analyse_portfolio(entity_id, credit_portfolio)

        return {
            "entity_id": entity_id,
            "assessment_date": date.today().isoformat(),
            "assessment_id": str(uuid.uuid4()),
            "summary": {
                "vcmi_claim_level": vcmi["claim_level"],
                "vcmi_credibility_score": vcmi["credibility_score"],
                "icvcm_pass_rate_pct": icvcm["overall_pass_rate_pct"],
                "corsia_eligible_pct": corsia["eligible_pct"],
                "article6_corresponding_adjustment_pct": art6["corresponding_adjustment_pct"],
                "weighted_avg_price_usd": portfolio_analysis["weighted_avg_price_usd_per_tco2e"],
                "total_portfolio_value_usd": portfolio_analysis["total_fair_value_usd"],
            },
            "modules": {
                "vcmi_claim": vcmi,
                "icvcm_ccp": icvcm,
                "corsia": corsia,
                "article6": art6,
                "portfolio_analysis": portfolio_analysis,
            },
            "key_risks": [
                "Double-counting risk if corresponding adjustments not confirmed",
                "ICVCM CCP approval required for VCMI Gold/Silver mitigation contribution",
                "CORSIA Phase 2 vintage and scheme requirements may invalidate legacy credits",
            ],
            "recommendations": [
                "Prioritise ICVCM CCP-approved credits for corporate claims",
                "Confirm corresponding adjustments for all Article 6 credits used in CORSIA",
                "Upgrade VCMI claim level by increasing abatement % alongside mitigation contribution",
            ],
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_engine: Optional[CarbonMarketsIntelEngine] = None


def get_engine() -> CarbonMarketsIntelEngine:
    global _engine
    if _engine is None:
        _engine = CarbonMarketsIntelEngine()
    return _engine
