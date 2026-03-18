"""
Green Securitisation & ESG Structured Finance Engine — E81
===========================================================
Comprehensive assessment engine for green and ESG-labelled securitisation transactions.
Covers EU GBS compliance, RMBS EPC analysis, covered bond ESV scoring, climate VaR
passthrough, green tranche structure design, and full deal assessment.

Sub-modules:
  1. EU GBS Compliance — EU Green Bond Standard Regulation (EU) 2023/2631 Art 19
  2. Climate VaR Passthrough — NGFS-aligned pool-level physical and transition risk
  3. RMBS EPC Analysis — Energy Performance Certificate distribution + CRREM alignment
  4. Covered Bond ESV — European Covered Bond Label + ESV (Environmental Sustainability Value)
  5. Green Tranche Design — Tranche structure, subordination, greenium modelling
  6. Full Assessment Orchestrator — green_securitisation_score + deal tier

References:
  - Regulation (EU) 2023/2631 — EU Green Bond Standard (EuGB) Official Journal
  - European Covered Bond Label (ECBC) — ECBC Covered Bond Label Convention 2023
  - ESRB Recommendation ESRB/2022/1 — Climate-related risk in the financial sector
  - EBA Guidelines EBA/GL/2023/01 — ESG risks in supervisory review
  - CRREM v2.0 (2023) — Carbon Risk Real Estate Monitor pathway tool
  - NGFS Climate Scenarios v4.0 (Sep 2023) — Physical and transition risk scenarios
  - EU Taxonomy Regulation (EU) 2020/852 — Taxonomy alignment requirements
  - ECB Asset Purchase Programme — Green bond purchase eligibility criteria
  - ICMA Green Bond Principles 2021 — Use of proceeds verification
  - EBA NPL/securitisation templates — Loan-level data fields
  - Basel III finalisation (CRR3/CRD6) — Capital treatment of securitisation exposures

Deal Tier definitions:
  Dark Green : score >= 80  — full EU GBS + taxonomy aligned + verified
  Green      : score 65-79  — partial EU GBS + credible green use of proceeds
  Light Green: score 50-64  — ESG labelled but gaps in taxonomy alignment or disclosure
  Amber      : score 35-49  — some ESG features but material non-compliance risks
  Red        : score < 35   — no credible green credentials; greenwashing risk
"""
from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Reference Data — Structure Types
# ---------------------------------------------------------------------------

STRUCTURE_TYPES: Dict[str, Dict[str, Any]] = {
    "ABS": {
        "full_name": "Asset-Backed Securities",
        "description": "General ABS backed by consumer loans, auto loans, equipment leases",
        "eligible_for_eu_gbs": True,
        "typical_rating_range": ["AAA", "AA", "A", "BBB"],
        "typical_maturity_years": (3, 7),
        "srt_eligible": True,
    },
    "RMBS": {
        "full_name": "Residential Mortgage-Backed Securities",
        "description": "Securities backed by pools of residential mortgage loans",
        "eligible_for_eu_gbs": True,
        "typical_rating_range": ["AAA", "AA", "A", "BBB", "BB"],
        "typical_maturity_years": (5, 30),
        "srt_eligible": True,
        "epc_requirement": True,
    },
    "CMBS": {
        "full_name": "Commercial Mortgage-Backed Securities",
        "description": "Securities backed by commercial real estate mortgage loans",
        "eligible_for_eu_gbs": True,
        "typical_rating_range": ["AAA", "AA", "A", "BBB", "BB"],
        "typical_maturity_years": (5, 15),
        "srt_eligible": True,
        "epc_requirement": True,
    },
    "CLO": {
        "full_name": "Collateralised Loan Obligation",
        "description": "Securitisation of leveraged corporate loans",
        "eligible_for_eu_gbs": False,
        "typical_rating_range": ["AAA", "AA", "A", "BBB", "BB", "B"],
        "typical_maturity_years": (8, 12),
        "srt_eligible": True,
        "esg_clo_variant": True,
    },
    "CDO": {
        "full_name": "Collateralised Debt Obligation",
        "description": "Securitisation of bonds, loans, or structured products",
        "eligible_for_eu_gbs": False,
        "typical_rating_range": ["AAA", "AA", "A", "BBB", "BB"],
        "typical_maturity_years": (5, 10),
        "srt_eligible": False,
    },
    "COVERED_BOND": {
        "full_name": "Covered Bond (Pfandbrief / Obligation Foncière)",
        "description": "On-balance-sheet dual recourse bond secured by a cover pool",
        "eligible_for_eu_gbs": True,
        "typical_rating_range": ["AAA", "AA"],
        "typical_maturity_years": (3, 15),
        "srt_eligible": False,
        "ecbc_label_eligible": True,
        "directive": "EU Covered Bond Directive 2019/2162",
    },
    "GREEN_ABS": {
        "full_name": "Green Asset-Backed Securities",
        "description": "ABS with use of proceeds restricted to green eligible assets (solar, EV, efficiency)",
        "eligible_for_eu_gbs": True,
        "typical_rating_range": ["AAA", "AA", "A", "BBB"],
        "typical_maturity_years": (3, 10),
        "srt_eligible": True,
        "greenium_eligible": True,
    },
    "SOCIAL_ABS": {
        "full_name": "Social Asset-Backed Securities",
        "description": "ABS with use of proceeds funding social projects (affordable housing, healthcare)",
        "eligible_for_eu_gbs": False,
        "typical_rating_range": ["AAA", "AA", "A"],
        "typical_maturity_years": (3, 10),
        "srt_eligible": True,
        "social_bond_principles": True,
    },
    "SUSTAINABILITY_LINKED_ABS": {
        "full_name": "Sustainability-Linked ABS (SL-ABS)",
        "description": "ABS with coupon step-up/down linked to pool-level KPI achievement",
        "eligible_for_eu_gbs": False,
        "typical_rating_range": ["AAA", "AA", "A", "BBB"],
        "typical_maturity_years": (3, 8),
        "srt_eligible": True,
        "kpi_based": True,
        "margin_ratchet": True,
    },
}

# ---------------------------------------------------------------------------
# Reference Data — EU GBS Requirements (Art 19, Regulation (EU) 2023/2631)
# ---------------------------------------------------------------------------

EU_GBS_REQUIREMENTS: Dict[str, Dict[str, Any]] = {
    "taxonomy_alignment": {
        "article": "Art 4 EU GBS + EU Taxonomy Reg (EU) 2020/852",
        "description": "100% of net proceeds allocated to EU taxonomy-aligned economic activities",
        "sub_requirements": [
            "Economic activity must qualify as taxonomy-eligible",
            "Substantial contribution to one of 6 environmental objectives",
            "Do No Significant Harm (DNSH) to remaining 5 objectives",
            "Comply with Minimum Safeguards (OECD MNE Guidelines, ILO core conventions)",
        ],
        "minimum_alignment_pct": 100.0,
        "weight_in_scoring": 0.40,
        "verification_required": True,
    },
    "green_bond_framework": {
        "article": "Art 6 EU GBS",
        "description": "Publish a Green Bond Framework before issuance setting out strategy, allocation, reporting",
        "sub_requirements": [
            "Use of proceeds definition aligned to EU Taxonomy",
            "Process for project evaluation and selection",
            "Management of proceeds (ring-fencing / virtual allocation)",
            "Reporting commitment (annual allocation + impact)",
        ],
        "minimum_alignment_pct": None,
        "weight_in_scoring": 0.25,
        "verification_required": True,
    },
    "reporting": {
        "article": "Art 9-11 EU GBS",
        "description": "Annual allocation reporting + at least one impact report before maturity or full allocation",
        "sub_requirements": [
            "Allocation report within 1 year of issuance (Art 9)",
            "Allocation report annually until full allocation",
            "Impact report at least once before maturity (Art 10)",
            "Post-issuance review if proceeds reallocated",
        ],
        "minimum_alignment_pct": None,
        "weight_in_scoring": 0.20,
        "verification_required": False,
    },
    "external_review": {
        "article": "Art 14-20 EU GBS",
        "description": "Pre-issuance review of GBF by ESAP-registered external reviewer; post-issuance review of allocation report",
        "sub_requirements": [
            "Pre-issuance GBF review by registered external reviewer (ESAP list)",
            "Post-issuance allocation report review",
            "Reviewer must be registered with ESMA (from Jul 2026)",
            "Conflict of interest rules for reviewer",
        ],
        "minimum_alignment_pct": None,
        "weight_in_scoring": 0.15,
        "verification_required": True,
    },
}

# ---------------------------------------------------------------------------
# Reference Data — ECBC Covered Bond Label Requirements (2023 Convention)
# ---------------------------------------------------------------------------

ECBC_COVERED_BOND_CRITERIA: Dict[str, Dict[str, Any]] = {
    "dual_recourse": {
        "criterion": "Dual recourse against issuer and cover pool",
        "directive_ref": "Art 4(1) EU CBD 2019/2162",
        "mandatory": True,
        "esv_weight": 0.15,
    },
    "cover_pool_quality": {
        "criterion": "Cover pool consists of high-quality eligible assets (mortgage loans or public sector)",
        "directive_ref": "Art 6-7 EU CBD 2019/2162",
        "mandatory": True,
        "esv_weight": 0.20,
    },
    "overcollateralisation": {
        "criterion": "Mandatory minimum OC of 5% on a nominal basis (or higher per national law)",
        "directive_ref": "Art 15 EU CBD 2019/2162",
        "mandatory": True,
        "esv_weight": 0.15,
        "minimum_oc_pct": 5.0,
    },
    "liquidity_buffer": {
        "criterion": "180-day liquidity buffer covering net outflows",
        "directive_ref": "Art 16 EU CBD 2019/2162",
        "mandatory": True,
        "esv_weight": 0.15,
    },
    "public_supervision": {
        "criterion": "Special public supervision by national competent authority",
        "directive_ref": "Art 18-20 EU CBD 2019/2162",
        "mandatory": True,
        "esv_weight": 0.10,
    },
    "investor_information": {
        "criterion": "Investor report at least quarterly with cover pool composition data",
        "directive_ref": "Art 14 EU CBD 2019/2162 + ECBC Label Convention §11",
        "mandatory": True,
        "esv_weight": 0.10,
    },
    "green_use_of_proceeds": {
        "criterion": "Use of proceeds for green-eligible mortgage loans (EPC A/B, CRREM-aligned)",
        "directive_ref": "ECBC Green Covered Bond Framework + EU GBS Art 4",
        "mandatory": False,
        "esv_weight": 0.10,
    },
    "esg_disclosure": {
        "criterion": "ESG cover pool disclosure: EPC distribution, energy intensity, climate risk metrics",
        "directive_ref": "EBA ESG Pillar 3 GL/2022/03 + ECBC ESG Transparency Code",
        "mandatory": False,
        "esv_weight": 0.05,
    },
}

# ---------------------------------------------------------------------------
# Reference Data — Climate Risk Sector Profiles (Physical + Transition)
# ---------------------------------------------------------------------------

CLIMATE_RISK_SECTOR_PROFILES: Dict[str, Dict[str, Any]] = {
    "residential_mortgage": {
        "physical_risk_sensitivity": 0.65,
        "transition_risk_sensitivity": 0.45,
        "key_physical_risks": ["flood", "heat_stress", "sea_level_rise"],
        "key_transition_risks": ["energy_efficiency_regulation", "carbon_tax"],
        "crrem_applicable": True,
        "ltv_haircut_range_pct": (2.0, 15.0),
    },
    "commercial_real_estate": {
        "physical_risk_sensitivity": 0.70,
        "transition_risk_sensitivity": 0.55,
        "key_physical_risks": ["flood", "heat_stress", "windstorm"],
        "key_transition_risks": ["stranded_asset_risk", "energy_efficiency_regulation", "carbon_price"],
        "crrem_applicable": True,
        "ltv_haircut_range_pct": (3.0, 20.0),
    },
    "auto_loans": {
        "physical_risk_sensitivity": 0.20,
        "transition_risk_sensitivity": 0.80,
        "key_physical_risks": ["flood"],
        "key_transition_risks": ["ice_ban", "ev_transition", "fuel_price_volatility"],
        "crrem_applicable": False,
        "ltv_haircut_range_pct": (1.0, 12.0),
    },
    "solar_equipment": {
        "physical_risk_sensitivity": 0.25,
        "transition_risk_sensitivity": -0.30,  # negative = climate transition is beneficial
        "key_physical_risks": ["extreme_weather_damage"],
        "key_transition_risks": [],
        "green_asset": True,
        "crrem_applicable": False,
        "ltv_haircut_range_pct": (-2.0, 5.0),
    },
    "energy_efficiency_loans": {
        "physical_risk_sensitivity": 0.15,
        "transition_risk_sensitivity": -0.20,
        "key_physical_risks": [],
        "key_transition_risks": [],
        "green_asset": True,
        "crrem_applicable": True,
        "ltv_haircut_range_pct": (-1.0, 3.0),
    },
    "corporate_loans_energy": {
        "physical_risk_sensitivity": 0.45,
        "transition_risk_sensitivity": 0.85,
        "key_physical_risks": ["heat_stress", "water_scarcity", "extreme_weather"],
        "key_transition_risks": ["carbon_price", "fossil_fuel_phase_out", "stranded_asset"],
        "crrem_applicable": False,
        "ltv_haircut_range_pct": (5.0, 25.0),
    },
    "corporate_loans_industrials": {
        "physical_risk_sensitivity": 0.35,
        "transition_risk_sensitivity": 0.60,
        "key_physical_risks": ["flood", "heat_stress"],
        "key_transition_risks": ["carbon_price", "energy_efficiency_cost", "supply_chain_disruption"],
        "crrem_applicable": False,
        "ltv_haircut_range_pct": (3.0, 18.0),
    },
    "consumer_loans": {
        "physical_risk_sensitivity": 0.30,
        "transition_risk_sensitivity": 0.35,
        "key_physical_risks": ["heat_stress"],
        "key_transition_risks": ["disposable_income_squeeze"],
        "crrem_applicable": False,
        "ltv_haircut_range_pct": (1.0, 8.0),
    },
}

# ---------------------------------------------------------------------------
# Reference Data — Greenium Benchmarks (bps over vanilla equivalent)
# ---------------------------------------------------------------------------

GREENIUM_BENCHMARKS: Dict[str, Dict[str, Any]] = {
    "eu_gbs_compliant": {
        "description": "Full EU GBS-labelled transaction (Art 19 compliant)",
        "by_rating": {"AAA": 4, "AA": 5, "A": 6, "BBB": 8, "BB": 10, "B": 12},
        "source": "ECB / BIS Working Paper 1015 (2023); Bloomberg BNEF Green Bond Premium Tracker",
    },
    "icma_gbp_green_bond": {
        "description": "ICMA GBP-aligned green bond (non-EU GBS)",
        "by_rating": {"AAA": 2, "AA": 3, "A": 4, "BBB": 5, "BB": 7, "B": 8},
        "source": "ICMA Green Bond Principles 2021; CBI Greenium Survey 2023",
    },
    "social_bond": {
        "description": "ICMA Social Bond Principles-aligned transaction",
        "by_rating": {"AAA": 1, "AA": 2, "A": 3, "BBB": 3, "BB": 4, "B": 5},
        "source": "ICMA Social Bond Principles 2021",
    },
    "sustainability_linked": {
        "description": "Sustainability-linked structure with KPI-based coupon ratchet",
        "by_rating": {"AAA": 1, "AA": 2, "A": 3, "BBB": 4, "BB": 5, "B": 6},
        "source": "ICMA SLB Principles 2020; academic literature on SLB premia",
        "note": "Greenium reduced vs use-of-proceeds as market scepticism on additionality",
    },
    "green_covered_bond": {
        "description": "ECBC Green Covered Bond Label-compliant (dual recourse + green pool)",
        "by_rating": {"AAA": 5, "AA": 6},
        "source": "ECBC Green Covered Bond Framework; BNP Paribas Covered Bond Research (2023)",
    },
    "green_rmbs": {
        "description": "Green RMBS with EPC A/B pool ≥50% and CRREM-aligned",
        "by_rating": {"AAA": 3, "AA": 4, "A": 5, "BBB": 6},
        "source": "ESF / AFME Green RMBS Working Group (2023)",
    },
}

# ---------------------------------------------------------------------------
# Reference Data — Tranche Subordination Standards
# ---------------------------------------------------------------------------

TRANCHE_SUBORDINATION_STANDARDS: Dict[str, Dict[str, Any]] = {
    "AAA_senior": {
        "target_rating": "AAA",
        "tranche_type": "senior",
        "typical_oc_pct": 15.0,         # Overcollateralisation %
        "typical_ce_pct": 20.0,          # Credit enhancement %
        "description": "Senior tranche — highest priority; lowest coupon",
        "typical_size_pct_of_pool": 75.0,
    },
    "AA_mezzanine": {
        "target_rating": "AA",
        "tranche_type": "mezzanine",
        "typical_oc_pct": 10.0,
        "typical_ce_pct": 13.0,
        "description": "Upper mezzanine — subordinated to AAA",
        "typical_size_pct_of_pool": 7.0,
    },
    "A_mezzanine": {
        "target_rating": "A",
        "tranche_type": "mezzanine",
        "typical_oc_pct": 7.5,
        "typical_ce_pct": 9.0,
        "description": "Mid mezzanine",
        "typical_size_pct_of_pool": 4.5,
    },
    "BBB_mezzanine": {
        "target_rating": "BBB",
        "tranche_type": "mezzanine",
        "typical_oc_pct": 5.0,
        "typical_ce_pct": 6.0,
        "description": "Lower mezzanine — investment grade floor",
        "typical_size_pct_of_pool": 3.0,
    },
    "BB_junior": {
        "target_rating": "BB",
        "tranche_type": "junior",
        "typical_oc_pct": 3.0,
        "typical_ce_pct": 3.5,
        "description": "Junior / sub-investment grade",
        "typical_size_pct_of_pool": 2.5,
    },
    "B_equity": {
        "target_rating": "B_equity",
        "tranche_type": "equity",
        "typical_oc_pct": 0.0,
        "typical_ce_pct": 0.0,
        "description": "First-loss / equity piece retained by originator per Art 6 STS Regulation",
        "typical_size_pct_of_pool": 8.0,
        "retention_requirement": "5% minimum per Art 6 Reg (EU) 2017/2402",
    },
}

# ---------------------------------------------------------------------------
# NGFS Scenario Parameters
# ---------------------------------------------------------------------------

NGFS_SCENARIO_PARAMETERS: Dict[str, Dict[str, Any]] = {
    "net_zero_2050": {
        "description": "Orderly transition achieving net-zero GHG by 2050",
        "physical_risk_multiplier": 0.60,
        "transition_risk_multiplier": 1.20,
        "carbon_price_2030_usd_t": 130,
        "carbon_price_2050_usd_t": 250,
        "temp_increase_by_2100_c": 1.5,
    },
    "below_2c": {
        "description": "Orderly transition limiting warming to below 2°C",
        "physical_risk_multiplier": 0.80,
        "transition_risk_multiplier": 0.90,
        "carbon_price_2030_usd_t": 75,
        "carbon_price_2050_usd_t": 150,
        "temp_increase_by_2100_c": 1.8,
    },
    "delayed_transition": {
        "description": "Disorderly transition with policy delay then sharp action post-2030",
        "physical_risk_multiplier": 0.90,
        "transition_risk_multiplier": 1.60,
        "carbon_price_2030_usd_t": 20,
        "carbon_price_2050_usd_t": 400,
        "temp_increase_by_2100_c": 1.8,
    },
    "current_policies": {
        "description": "No additional climate policy (hot house world)",
        "physical_risk_multiplier": 1.50,
        "transition_risk_multiplier": 0.30,
        "carbon_price_2030_usd_t": 5,
        "carbon_price_2050_usd_t": 10,
        "temp_increase_by_2100_c": 3.2,
    },
}


# ---------------------------------------------------------------------------
# Engine Class
# ---------------------------------------------------------------------------

class GreenSecuritisationEngine:
    """
    E81: Green Securitisation & ESG Structured Finance Engine.

    Assesses green and ESG-labelled securitisation deals across five dimensions:
      1. EU GBS compliance (taxonomy alignment, framework, reporting, external review)
      2. Climate VaR passthrough from pool assets under NGFS scenarios
      3. RMBS EPC distribution and CRREM pathway alignment
      4. Covered bond ESV and ECBC Label eligibility
      5. Green tranche structure design with subordination and greenium modelling
    """

    def __init__(self) -> None:
        logger.info("GreenSecuritisationEngine initialised (E81)")

    # ------------------------------------------------------------------
    # 1. EU GBS Compliance Assessment
    # ------------------------------------------------------------------

    def assess_eu_gbs_compliance(self, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess deal compliance with EU Green Bond Standard (EU) 2023/2631 Art 19.

        Checks: taxonomy alignment %, DNSH, minimum safeguards, framework, reporting, external review.
        Returns GBS score (0-100) and gap list.
        """
        logger.debug("assess_eu_gbs_compliance deal=%s", deal_data.get("deal_name"))

        taxonomy_alignment_pct = deal_data.get("taxonomy_alignment_pct", 0.0)
        has_framework = deal_data.get("has_framework", False)
        has_external_review = deal_data.get("has_external_review", False)
        dnsh_evidence = deal_data.get("dnsh_evidence", False)
        min_safeguards_evidence = deal_data.get("min_safeguards_evidence", False)
        has_allocation_report = deal_data.get("has_allocation_report", False)
        has_impact_report = deal_data.get("has_impact_report", False)
        esap_registered = deal_data.get("esap_registered", False)
        structure_type = deal_data.get("structure_type", "")

        gaps: List[str] = []
        component_scores: Dict[str, float] = {}

        # --- Taxonomy alignment (Art 4 + EU Taxonomy) ---
        req = EU_GBS_REQUIREMENTS["taxonomy_alignment"]
        if taxonomy_alignment_pct >= 100.0:
            tax_score = 100.0
        elif taxonomy_alignment_pct >= 85.0:
            tax_score = 70.0
            gaps.append(f"Taxonomy alignment {taxonomy_alignment_pct:.1f}% < 100% required by Art 4 EU GBS")
        else:
            tax_score = taxonomy_alignment_pct
            gaps.append(f"Taxonomy alignment {taxonomy_alignment_pct:.1f}% materially below 100% required")

        if not dnsh_evidence:
            tax_score *= 0.80
            gaps.append("DNSH evidence not documented for all environmental objectives (EU Taxonomy Art 17)")
        if not min_safeguards_evidence:
            tax_score *= 0.90
            gaps.append("Minimum Safeguards compliance (OECD MNE Guidelines / ILO) not evidenced")

        component_scores["taxonomy_alignment"] = round(min(100.0, tax_score), 1)

        # --- Green Bond Framework (Art 6) ---
        if has_framework:
            framework_score = 100.0
            if not esap_registered:
                framework_score = 85.0
                gaps.append("GBF not yet published on ESAP (European Single Access Point) as required by Art 6(5)")
        else:
            framework_score = 0.0
            gaps.append("No Green Bond Framework published — mandatory per Art 6 EU GBS 2023/2631")
        component_scores["green_bond_framework"] = round(framework_score, 1)

        # --- Reporting (Art 9-11) ---
        reporting_score = 0.0
        if has_allocation_report:
            reporting_score += 60.0
        else:
            gaps.append("No allocation report filed — required annually per Art 9 EU GBS")
        if has_impact_report:
            reporting_score += 40.0
        else:
            gaps.append("No impact report — required at least once before maturity per Art 10 EU GBS")
        component_scores["reporting"] = round(reporting_score, 1)

        # --- External Review (Art 14-20) ---
        if has_external_review:
            review_score = 100.0
            if not esap_registered:
                review_score = 90.0
                gaps.append("External reviewer should be registered with ESMA from July 2026 (Art 14)")
        else:
            review_score = 0.0
            gaps.append("No external review of GBF — mandatory pre-issuance review required per Art 15 EU GBS")
        component_scores["external_review"] = round(review_score, 1)

        # Overall GBS score (weighted)
        weights = {k: v["weight_in_scoring"] for k, v in EU_GBS_REQUIREMENTS.items()}
        gbs_score = round(
            component_scores["taxonomy_alignment"] * weights["taxonomy_alignment"]
            + component_scores["green_bond_framework"] * weights["green_bond_framework"]
            + component_scores["reporting"] * weights["reporting"]
            + component_scores["external_review"] * weights["external_review"],
            1,
        )

        compliant = gbs_score >= 75 and len([g for g in gaps if "mandatory" in g.lower() or "required" in g.lower()]) == 0

        return {
            "deal_name": deal_data.get("deal_name", ""),
            "framework": "EU Green Bond Standard (EU) 2023/2631",
            "structure_type": structure_type,
            "taxonomy_alignment_pct": taxonomy_alignment_pct,
            "component_scores": component_scores,
            "gbs_score": gbs_score,
            "eu_gbs_compliant": compliant,
            "gaps": gaps,
            "gap_count": len(gaps),
            "esap_registered": esap_registered,
            "external_reviewer_required_from": "2026-07-01",
        }

    # ------------------------------------------------------------------
    # 2. Climate VaR Passthrough
    # ------------------------------------------------------------------

    def compute_climate_var_passthrough(
        self,
        pool_assets: List[Dict[str, Any]],
        ngfs_scenario: str,
        time_horizon_years: int = 10,
    ) -> Dict[str, Any]:
        """
        Compute climate VaR for a pool of securitised assets under an NGFS scenario.
        Returns physical VaR, transition VaR, climate-adjusted weighted PD/LGD,
        and required credit enhancement uplift.

        Physical VaR = sum(exposure × physical_risk_sensitivity × scenario_multiplier × concentration_factor)
        Transition VaR = sum(exposure × transition_risk_sensitivity × scenario_multiplier)
        """
        logger.debug("compute_climate_var_passthrough scenario=%s assets=%d", ngfs_scenario, len(pool_assets))

        scenario = NGFS_SCENARIO_PARAMETERS.get(ngfs_scenario, NGFS_SCENARIO_PARAMETERS["below_2c"])
        phys_mult = scenario["physical_risk_multiplier"]
        trans_mult = scenario["transition_risk_multiplier"]

        total_exposure = sum(a.get("balance_m", 0.0) for a in pool_assets)
        if total_exposure == 0:
            total_exposure = 1.0

        # Time horizon adjustment (linear scaling proxy)
        horizon_factor = math.sqrt(time_horizon_years / 10.0)

        physical_var_m = 0.0
        transition_var_m = 0.0
        weighted_pd_sum = 0.0
        weighted_lgd_sum = 0.0
        asset_breakdown: List[Dict[str, Any]] = []

        for asset in pool_assets:
            balance = asset.get("balance_m", 0.0)
            asset_type = asset.get("asset_type", "consumer_loans")
            base_pd = asset.get("base_pd", 0.02)
            base_lgd = asset.get("base_lgd", 0.35)

            profile = CLIMATE_RISK_SECTOR_PROFILES.get(asset_type, CLIMATE_RISK_SECTOR_PROFILES["consumer_loans"])
            phys_sens = max(0, profile["physical_risk_sensitivity"])
            trans_sens = profile["transition_risk_sensitivity"]  # can be negative for green assets

            # VaR contributions
            phys_contribution = balance * phys_sens * phys_mult * horizon_factor * 0.10
            trans_contribution = balance * max(0, trans_sens) * trans_mult * horizon_factor * 0.08
            physical_var_m += phys_contribution
            transition_var_m += trans_contribution

            # Climate-adjusted PD uplift
            pd_uplift = base_pd * (phys_sens * phys_mult * 0.25 + max(0, trans_sens) * trans_mult * 0.30)
            lgd_uplift = base_lgd * phys_sens * phys_mult * 0.10

            climate_pd = min(1.0, base_pd + pd_uplift * (time_horizon_years / 10.0))
            climate_lgd = min(1.0, base_lgd + lgd_uplift * (time_horizon_years / 10.0))

            weight = balance / total_exposure
            weighted_pd_sum += climate_pd * weight
            weighted_lgd_sum += climate_lgd * weight

            asset_breakdown.append({
                "asset_type": asset_type,
                "balance_m": balance,
                "base_pd": base_pd,
                "base_lgd": base_lgd,
                "climate_pd": round(climate_pd, 4),
                "climate_lgd": round(climate_lgd, 4),
                "physical_var_contribution_m": round(phys_contribution, 3),
                "transition_var_contribution_m": round(trans_contribution, 3),
            })

        total_climate_var_m = physical_var_m + transition_var_m
        var_as_pct_pool = (total_climate_var_m / total_exposure) * 100

        # Credit enhancement uplift recommendation
        # Standard CE is typically 15-25% for AAA; add climate uplift proportionally
        ce_base = 0.18  # 18% base CE assumption
        ce_uplift_pct = min(5.0, var_as_pct_pool * 0.20)
        ce_recommended_pct = round((ce_base * 100) + ce_uplift_pct, 2)

        return {
            "ngfs_scenario": ngfs_scenario,
            "scenario_description": scenario["description"],
            "time_horizon_years": time_horizon_years,
            "total_pool_balance_m": round(total_exposure, 2),
            "physical_var_m": round(physical_var_m, 3),
            "transition_var_m": round(transition_var_m, 3),
            "total_climate_var_m": round(total_climate_var_m, 3),
            "climate_var_as_pct_pool": round(var_as_pct_pool, 2),
            "pool_weighted_climate_pd": round(weighted_pd_sum, 4),
            "pool_weighted_climate_lgd": round(weighted_lgd_sum, 4),
            "pool_expected_climate_loss_m": round(weighted_pd_sum * weighted_lgd_sum * total_exposure, 3),
            "ce_base_pct": ce_base * 100,
            "ce_uplift_pct": round(ce_uplift_pct, 2),
            "ce_recommended_pct": ce_recommended_pct,
            "asset_breakdown": asset_breakdown,
            "carbon_price_2030": scenario["carbon_price_2030_usd_t"],
            "temp_increase_2100_c": scenario["temp_increase_by_2100_c"],
        }

    # ------------------------------------------------------------------
    # 3. RMBS EPC Analysis
    # ------------------------------------------------------------------

    def assess_rmbs_epc(self, mortgage_pool: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess RMBS pool EPC distribution, CRREM alignment, and energy efficiency metrics.
        References CRREM v2.0 (2023) decarbonisation pathways for residential buildings.

        EPC bands: A (best) → G (worst). EU taxonomy requires EPC A or top 15% per region.
        """
        logger.debug("assess_rmbs_epc deal=%s", mortgage_pool.get("deal_name"))

        epc_dist = mortgage_pool.get("epc_distribution", {})  # e.g. {"A": 10, "B": 25, ...} as pct
        total_balance_m = mortgage_pool.get("total_balance_m", 1000.0)
        country = mortgage_pool.get("country_code", "DE")
        vintage_year = mortgage_pool.get("vintage_year", 2020)
        mortgage_count = mortgage_pool.get("mortgage_count", 1000)

        # Normalise EPC distribution to sum to 100
        total_epc = sum(epc_dist.values()) if epc_dist else 0
        if total_epc > 0 and abs(total_epc - 100) > 0.1:
            epc_dist = {k: v / total_epc * 100 for k, v in epc_dist.items()}

        # EU Taxonomy: EPC A or top 15% for residential buildings (Art 7(1) climate mitigation)
        epc_a_pct = epc_dist.get("A", 0.0)
        epc_b_pct = epc_dist.get("B", 0.0)
        epc_a_b_pct = epc_a_pct + epc_b_pct
        epc_ef_pct = sum(epc_dist.get(band, 0.0) for band in ["E", "F", "G"])

        # CRREM alignment: buildings in EPC A/B typically on 1.5°C pathway
        # Buildings in EPC E/F/G are at stranded asset risk by 2030-2040
        crrem_aligned_pct = epc_a_b_pct
        stranded_asset_risk_pct = epc_ef_pct

        # Country-specific CRREM stranding years (EU residential avg)
        country_stranding_year = {
            "DE": 2035, "FR": 2038, "GB": 2033, "NL": 2037, "ES": 2040,
            "IT": 2042, "PL": 2045, "SE": 2030, "AT": 2036, "BE": 2038,
        }.get(country, 2040)

        # Energy intensity estimate (kWh/m²/yr) by EPC band
        energy_intensity_map = {"A": 50, "B": 100, "C": 160, "D": 230, "E": 320, "F": 420, "G": 550}
        weighted_energy_intensity = sum(
            epc_dist.get(band, 0.0) / 100.0 * energy_intensity_map.get(band, 200)
            for band in ["A", "B", "C", "D", "E", "F", "G"]
        )

        # EU average residential: 210 kWh/m²/yr (Eurostat 2022)
        benchmark_energy_intensity = 210.0
        energy_efficiency_vs_benchmark_pct = round(
            (benchmark_energy_intensity - weighted_energy_intensity) / benchmark_energy_intensity * 100, 1
        )

        # Physical hazard: country-level average
        country_flood_risk = {"DE": 0.15, "NL": 0.35, "GB": 0.20, "FR": 0.12, "IT": 0.18, "ES": 0.10}.get(country, 0.15)
        country_heat_risk = {"ES": 0.40, "IT": 0.35, "GR": 0.50, "FR": 0.25, "DE": 0.20, "NL": 0.15}.get(country, 0.20)
        physical_hazard_score = round((country_flood_risk + country_heat_risk) / 2 * 100, 1)

        # EPC quality score
        epc_quality_score = round(epc_a_b_pct * 0.60 + (100 - epc_ef_pct) * 0.40, 1)

        # Taxonomy alignment eligibility
        taxonomy_eligible_pct = epc_a_pct  # strict: EPC A only or top 15%
        taxonomy_eligible_balance_m = total_balance_m * taxonomy_eligible_pct / 100.0

        return {
            "deal_name": mortgage_pool.get("deal_name", ""),
            "framework": "CRREM v2.0 (2023) + EU Taxonomy Reg (EU) 2020/852 Art 7",
            "country_code": country,
            "mortgage_count": mortgage_count,
            "total_balance_m": total_balance_m,
            "epc_distribution_pct": epc_dist,
            "epc_a_pct": round(epc_a_pct, 2),
            "epc_a_b_pct": round(epc_a_b_pct, 2),
            "epc_ef_g_pct": round(epc_ef_pct, 2),
            "crrem_aligned_pct": round(crrem_aligned_pct, 2),
            "stranded_asset_risk_pct": round(stranded_asset_risk_pct, 2),
            "crrem_stranding_year_country": country_stranding_year,
            "weighted_energy_intensity_kwh_m2_yr": round(weighted_energy_intensity, 1),
            "benchmark_energy_intensity_kwh_m2_yr": benchmark_energy_intensity,
            "energy_efficiency_vs_benchmark_pct": energy_efficiency_vs_benchmark_pct,
            "physical_hazard_score": physical_hazard_score,
            "flood_risk_score": round(country_flood_risk * 100, 1),
            "heat_risk_score": round(country_heat_risk * 100, 1),
            "epc_quality_score": min(100.0, epc_quality_score),
            "taxonomy_eligible_pct": round(taxonomy_eligible_pct, 2),
            "taxonomy_eligible_balance_m": round(taxonomy_eligible_balance_m, 2),
            "vintage_year": vintage_year,
        }

    # ------------------------------------------------------------------
    # 4. Covered Bond ESV Assessment
    # ------------------------------------------------------------------

    def assess_covered_bond_esv(self, bond_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess ECBC Covered Bond Label eligibility and ESV (Environmental Sustainability Value) score.

        References: EU Covered Bond Directive 2019/2162 + ECBC Label Convention 2023.
        ESV score reflects quality of green disclosure beyond standard ECBC label requirements.
        """
        logger.debug("assess_covered_bond_esv bond=%s", bond_data.get("bond_name"))

        ecbc_label_applied = bond_data.get("ecbc_label_applied", False)
        kpis = bond_data.get("kpis", [])
        cover_pool_size_m = bond_data.get("cover_pool_size_m", 1000.0)
        issuer_type = bond_data.get("issuer_type", "mortgage_bank")
        oc_level_pct = bond_data.get("oc_level_pct", 10.0)
        liquidity_buffer_days = bond_data.get("liquidity_buffer_days", 180)

        criteria_met: Dict[str, bool] = {}
        gaps: List[str] = []
        total_esv_score = 0.0

        for crit_key, crit_data in ECBC_COVERED_BOND_CRITERIA.items():
            met = False
            if crit_key == "dual_recourse":
                met = bond_data.get("dual_recourse_structure", False)
            elif crit_key == "cover_pool_quality":
                met = bond_data.get("cover_pool_high_quality", False)
            elif crit_key == "overcollateralisation":
                met = oc_level_pct >= crit_data["minimum_oc_pct"]
            elif crit_key == "liquidity_buffer":
                met = liquidity_buffer_days >= 180
            elif crit_key == "public_supervision":
                met = bond_data.get("national_competent_authority_supervised", False)
            elif crit_key == "investor_information":
                met = bond_data.get("quarterly_investor_report", False)
            elif crit_key == "green_use_of_proceeds":
                met = bond_data.get("green_use_of_proceeds", False)
            elif crit_key == "esg_disclosure":
                met = bond_data.get("esg_pool_disclosure_published", False)

            criteria_met[crit_key] = met
            if met:
                total_esv_score += crit_data["esv_weight"] * 100
            elif crit_data["mandatory"]:
                gaps.append(f"Mandatory ECBC criterion not met: {crit_data['criterion'][:80]}")

        # KPI quality scoring
        kpi_quality_scores = []
        for kpi in kpis:
            kpi_name = kpi.get("name", "")
            kpi_verified = kpi.get("third_party_verified", False)
            kpi_baseline = kpi.get("has_baseline", False)
            kpi_target = kpi.get("has_target", False)
            kpi_score = (
                (30 if kpi_baseline else 0)
                + (40 if kpi_target else 0)
                + (30 if kpi_verified else 0)
            )
            kpi_quality_scores.append({"kpi": kpi_name, "score": kpi_score})
        avg_kpi_quality = (sum(k["score"] for k in kpi_quality_scores) / len(kpi_quality_scores)
                           if kpi_quality_scores else 0)
        esv_kpi_bonus = min(10.0, avg_kpi_quality * 0.10)  # Up to 10 bonus points for KPI quality

        esv_score = round(min(100.0, total_esv_score + esv_kpi_bonus), 1)
        ecbc_label_eligible = all(
            criteria_met.get(k, False)
            for k, v in ECBC_COVERED_BOND_CRITERIA.items() if v["mandatory"]
        )

        return {
            "bond_name": bond_data.get("bond_name", ""),
            "framework": "EU CBD 2019/2162 + ECBC Label Convention 2023",
            "issuer_type": issuer_type,
            "cover_pool_size_m": cover_pool_size_m,
            "oc_level_pct": oc_level_pct,
            "liquidity_buffer_days": liquidity_buffer_days,
            "ecbc_label_eligible": ecbc_label_eligible,
            "criteria_met": criteria_met,
            "esv_score": esv_score,
            "esv_kpi_bonus": round(esv_kpi_bonus, 2),
            "kpi_quality_scores": kpi_quality_scores,
            "mandatory_gaps": gaps,
            "mandatory_criteria_met_count": sum(
                1 for k, v in ECBC_COVERED_BOND_CRITERIA.items() if v["mandatory"] and criteria_met.get(k, False)
            ),
            "mandatory_criteria_total": sum(1 for v in ECBC_COVERED_BOND_CRITERIA.values() if v["mandatory"]),
        }

    # ------------------------------------------------------------------
    # 5. Green Tranche Structure Design
    # ------------------------------------------------------------------

    def design_green_tranche_structure(
        self,
        pool_data: Dict[str, Any],
        target_rating: str,
        green_target_pct: float,
    ) -> Dict[str, Any]:
        """
        Design green tranche structure with subordination levels and greenium estimate.
        Follows EU STS Securitisation Regulation (EU) 2017/2402 retention requirements.

        Computes: tranche sizes, OC/CE requirements, greenium, ESRS SPV disclosure obligations.
        """
        logger.debug("design_green_tranche_structure target_rating=%s green_pct=%.1f", target_rating, green_target_pct)

        pool_size_m = pool_data.get("pool_size_m", 1000.0)
        structure_type = pool_data.get("structure_type", "ABS")
        is_sts = pool_data.get("sts_eligible", True)
        green_label = pool_data.get("green_label", "EU_GBS")
        avg_loan_balance = pool_data.get("avg_loan_balance", 200000)

        # Build tranche waterfall
        tranches = []
        remaining_pool_pct = 100.0

        tranche_order = ["AAA_senior", "AA_mezzanine", "A_mezzanine", "BBB_mezzanine", "BB_junior", "B_equity"]
        target_rating_map = {"AAA": "AAA_senior", "AA": "AA_mezzanine", "A": "A_mezzanine", "BBB": "BBB_mezzanine"}
        target_key = target_rating_map.get(target_rating, "AAA_senior")

        for tranche_key in tranche_order:
            t = TRANCHE_SUBORDINATION_STANDARDS[tranche_key]
            size_pct = t["typical_size_pct_of_pool"]
            if remaining_pool_pct <= 0:
                break
            actual_size_pct = min(size_pct, remaining_pool_pct)
            size_m = pool_size_m * actual_size_pct / 100.0
            is_target = tranche_key == target_key

            # Greenium estimate for this tranche if labelled
            greenium_bps = 0
            if is_target and green_target_pct >= 50.0:
                greenium_lookup = GREENIUM_BENCHMARKS.get(
                    "eu_gbs_compliant" if green_label == "EU_GBS" else "icma_gbp_green_bond",
                    GREENIUM_BENCHMARKS["icma_gbp_green_bond"],
                )
                short_rating = t["target_rating"].replace("_senior", "").replace("_mezzanine", "").replace("_junior", "").replace("_equity", "")
                greenium_bps = greenium_lookup["by_rating"].get(short_rating, 3)

            tranches.append({
                "tranche_key": tranche_key,
                "target_rating": t["target_rating"],
                "tranche_type": t["tranche_type"],
                "size_pct_of_pool": round(actual_size_pct, 2),
                "size_m": round(size_m, 2),
                "oc_required_pct": t["typical_oc_pct"],
                "ce_required_pct": t["typical_ce_pct"],
                "is_target_tranche": is_target,
                "greenium_bps": greenium_bps,
                "description": t["description"],
            })
            remaining_pool_pct -= actual_size_pct

        # Green pool allocation
        green_pool_m = pool_size_m * green_target_pct / 100.0
        standard_pool_m = pool_size_m - green_pool_m

        # ESRS SPV disclosure obligations (CSRD Art 2 + ESRS E1 if threshold exceeded)
        total_issuance_m = pool_size_m
        csrd_threshold_exceeded = total_issuance_m > 750  # €750m CSRD Art 2 large entity proxy
        esrs_obligations = []
        if csrd_threshold_exceeded:
            esrs_obligations.append("ESRS E1: GHG emissions from pool assets — Scope 3 financed emissions")
            esrs_obligations.append("ESRS E4: Biodiversity impact of financed activities")
            esrs_obligations.append("ESRS S: Worker rights in financed supply chains (if applicable)")
        if green_label == "EU_GBS":
            esrs_obligations.append("EU GBS Art 9-10: Annual allocation + impact reporting on ESAP")
        if is_sts:
            esrs_obligations.append("STS Reg Art 6: 5% risk retention by originator/sponsor")
            esrs_obligations.append("STS Reg Art 22: Investor reporting with loan-level data")

        # Estimated greenium value to issuer
        target_tranche = next((t for t in tranches if t["is_target_tranche"]), None)
        greenium_value_m = 0.0
        if target_tranche and target_tranche["greenium_bps"] > 0:
            greenium_value_m = (target_tranche["greenium_bps"] / 10000.0) * target_tranche["size_m"]

        return {
            "deal_name": pool_data.get("deal_name", ""),
            "framework": "EU STS Reg (EU) 2017/2402 + EU GBS Reg (EU) 2023/2631",
            "structure_type": structure_type,
            "pool_size_m": pool_size_m,
            "green_target_pct": green_target_pct,
            "green_pool_m": round(green_pool_m, 2),
            "standard_pool_m": round(standard_pool_m, 2),
            "target_rating": target_rating,
            "tranche_waterfall": tranches,
            "greenium_estimate_bps": target_tranche["greenium_bps"] if target_tranche else 0,
            "greenium_value_m": round(greenium_value_m, 3),
            "esrs_spv_disclosure_obligations": esrs_obligations,
            "sts_eligible": is_sts,
            "green_label": green_label,
            "retention_requirement_pct": 5.0,
        }

    # ------------------------------------------------------------------
    # 6. Full Assessment Orchestrator
    # ------------------------------------------------------------------

    def run_full_assessment(
        self,
        entity_id: str,
        deal_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Orchestrate all 5 sub-assessments and compute green_securitisation_score.
        Assign deal tier: Dark Green / Green / Light Green / Amber / Red.

        Score weights:
          EU GBS 35% + Climate VaR 25% + EPC/RMBS 20% + Covered Bond ESV 10% + Tranche Design 10%
        """
        logger.info("run_full_assessment entity=%s deal=%s", entity_id, deal_data.get("deal_name"))

        # EU GBS
        gbs_result = self.assess_eu_gbs_compliance(deal_data)

        # Climate VaR
        pool_assets = deal_data.get("pool_assets", [])
        ngfs_scenario = deal_data.get("ngfs_scenario", "below_2c")
        time_horizon = deal_data.get("time_horizon_years", 10)
        if not pool_assets:
            pool_assets = [{"asset_type": "residential_mortgage", "balance_m": deal_data.get("total_issuance_m", 500), "base_pd": 0.02, "base_lgd": 0.25}]
        var_result = self.compute_climate_var_passthrough(pool_assets, ngfs_scenario, time_horizon)

        # RMBS EPC (if applicable)
        structure_type = deal_data.get("structure_type", "ABS")
        epc_result = None
        epc_score = 50.0  # neutral default for non-RMBS
        if structure_type in ("RMBS", "CMBS", "COVERED_BOND", "GREEN_ABS"):
            mortgage_pool_data = deal_data.get("mortgage_pool", {})
            mortgage_pool_data["deal_name"] = deal_data.get("deal_name", "")
            epc_result = self.assess_rmbs_epc(mortgage_pool_data)
            epc_score = epc_result["epc_quality_score"]

        # Covered bond ESV (if applicable)
        cb_result = None
        cb_score = 50.0
        if structure_type == "COVERED_BOND":
            cb_data = deal_data.get("covered_bond_data", {})
            cb_data["bond_name"] = deal_data.get("deal_name", "")
            cb_result = self.assess_covered_bond_esv(cb_data)
            cb_score = cb_result["esv_score"]

        # Tranche design
        pool_data = deal_data.get("pool_data", {"deal_name": deal_data.get("deal_name", ""),
                                                 "pool_size_m": deal_data.get("total_issuance_m", 500.0),
                                                 "structure_type": structure_type})
        target_rating = deal_data.get("target_rating", "AAA")
        green_target_pct = deal_data.get("green_target_pct", 80.0)
        tranche_result = self.design_green_tranche_structure(pool_data, target_rating, green_target_pct)

        # Climate VaR score — lower VaR as % of pool = better score
        var_pct = var_result["climate_var_as_pct_pool"]
        climate_var_score = round(max(0, 100 - var_pct * 4), 1)

        # Tranche design score — penalise for low greenium or missing obligations
        n_obligations = len(tranche_result["esrs_spv_disclosure_obligations"])
        tranche_score = round(min(100, 60 + green_target_pct * 0.4 - n_obligations * 2), 1)

        # Composite score
        green_securitisation_score = round(
            gbs_result["gbs_score"] * 0.35
            + climate_var_score * 0.25
            + epc_score * 0.20
            + cb_score * 0.10
            + tranche_score * 0.10,
            1,
        )

        # Deal tier
        if green_securitisation_score >= 80:
            deal_tier = "Dark Green"
            tier_colour = "#006400"
        elif green_securitisation_score >= 65:
            deal_tier = "Green"
            tier_colour = "#228B22"
        elif green_securitisation_score >= 50:
            deal_tier = "Light Green"
            tier_colour = "#90EE90"
        elif green_securitisation_score >= 35:
            deal_tier = "Amber"
            tier_colour = "#FFA500"
        else:
            deal_tier = "Red"
            tier_colour = "#DC143C"

        # Priority actions
        actions: List[str] = []
        if gbs_result["gbs_score"] < 75:
            actions.append("File EU GBS-compliant Green Bond Framework before issuance (Art 6 EU 2023/2631)")
        if var_pct > 5.0:
            actions.append(f"Climate VaR {var_pct:.1f}% of pool — increase CE by {var_result['ce_uplift_pct']:.1f}%")
        if epc_result and epc_result["epc_a_b_pct"] < 20.0:
            actions.append("RMBS pool EPC quality low — screen for EPC A/B mortgages to improve taxonomy alignment")
        if deal_data.get("taxonomy_alignment_pct", 0) < 100:
            actions.append("Increase taxonomy alignment to 100% for full EU GBS label")

        return {
            "entity_id": entity_id,
            "deal_name": deal_data.get("deal_name", ""),
            "structure_type": structure_type,
            "assessment_type": "full_green_securitisation",
            "component_scores": {
                "eu_gbs_score": gbs_result["gbs_score"],
                "climate_var_score": climate_var_score,
                "epc_quality_score": epc_score,
                "covered_bond_esv_score": cb_score,
                "tranche_design_score": tranche_score,
            },
            "score_weights": {
                "eu_gbs": 0.35, "climate_var": 0.25, "epc": 0.20, "covered_bond": 0.10, "tranche": 0.10,
            },
            "green_securitisation_score": green_securitisation_score,
            "deal_tier": deal_tier,
            "deal_tier_colour": tier_colour,
            "priority_actions": actions,
            "gbs_result": gbs_result,
            "climate_var_result": var_result,
            "epc_result": epc_result,
            "covered_bond_result": cb_result,
            "tranche_result": tranche_result,
        }

    # ------------------------------------------------------------------
    # Reference data helpers
    # ------------------------------------------------------------------

    def ref_structure_types(self) -> Dict[str, Any]:
        return STRUCTURE_TYPES

    def ref_eu_gbs_requirements(self) -> Dict[str, Any]:
        return EU_GBS_REQUIREMENTS

    def ref_greenium_benchmarks(self) -> Dict[str, Any]:
        return GREENIUM_BENCHMARKS

    def ref_climate_risk_profiles(self) -> Dict[str, Any]:
        return CLIMATE_RISK_SECTOR_PROFILES

    def ref_tranche_standards(self) -> Dict[str, Any]:
        return TRANCHE_SUBORDINATION_STANDARDS

    def ref_ngfs_scenarios(self) -> Dict[str, Any]:
        return NGFS_SCENARIO_PARAMETERS


def get_engine() -> GreenSecuritisationEngine:
    """Return a module-level singleton engine."""
    return GreenSecuritisationEngine()
