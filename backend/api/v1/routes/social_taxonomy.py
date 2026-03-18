"""
EU Social Taxonomy & Human Rights DD API Routes — E97
=====================================================
Prefix  : /api/v1/social-taxonomy
Tags    : Social Taxonomy — E97
"""
from __future__ import annotations

from typing import Any, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.social_taxonomy_engine import (
    COUNTRY_LABOUR_RISK_PROFILES,
    DECENT_WORK_INDICATORS,
    EU_SOCIAL_TAXONOMY_OBJECTIVES,
    ILO_CORE_CONVENTIONS,
    assess_social_taxonomy,
    conduct_hrdd,
    get_social_taxonomy_criteria,
)

router = APIRouter(prefix="/api/v1/social-taxonomy", tags=["Social Taxonomy — E97"])


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class SocialTaxonomyRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_name: str = Field(..., example="Acme Manufacturing Ltd")
    nace_code: str = Field(..., example="C14.1", description="Primary NACE Rev.2 code")
    sector: str = Field(..., example="manufacturing")
    country_of_operations: str = Field(default="GBR", description="ISO3 country code")
    # OBJ1 — Decent Work
    living_wage_compliance_pct: float = Field(default=70.0, description="% workforce paid at or above Anker living wage")
    h_and_s_score: float = Field(default=0.65, description="H&S maturity 0-1 (1 = ISO 45001 + zero incidents)")
    permanent_contract_pct: float = Field(default=75.0, description="% of workforce on permanent contracts")
    collective_bargaining_coverage_pct: float = Field(default=40.0, description="% workforce covered by CBA")
    work_life_balance_score: float = Field(default=0.60, description="0-1 work-life balance score")
    # OBJ2 — Living Standards
    healthcare_access_score: float = Field(default=0.60)
    affordable_housing_score: float = Field(default=0.50)
    education_score: float = Field(default=0.55)
    food_security_score: float = Field(default=0.55)
    financial_inclusion_score: float = Field(default=0.55)
    # OBJ3 — Inclusive Communities
    inclusive_growth_score: float = Field(default=0.55)
    digital_access_score: float = Field(default=0.50)
    cultural_heritage_score: float = Field(default=0.55)
    just_transition_score: float = Field(default=0.50)
    stakeholder_engagement_score: float = Field(default=0.55)
    # UNGP / HRDD
    policy_commitment: bool = Field(default=True)
    value_chain_mapping: bool = Field(default=False)
    corrective_actions_count: int = Field(default=2)
    grievance_mechanism: bool = Field(default=True)
    annual_reporting: bool = Field(default=True)
    board_oversight: bool = Field(default=False)
    # Supply chain
    supplier_countries: Optional[List[str]] = Field(default=None, example=["IND", "BGD", "VNM"])


class HRDDRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    company_name: str = Field(..., example="GlobalCorp PLC")
    supplier_countries: List[str] = Field(..., example=["CHN", "IND", "BGD"])
    supply_chain_tiers: int = Field(default=2, description="Depth of supply chain mapping (1 = direct suppliers)")
    sector: str = Field(default="manufacturing", example="manufacturing")
    policy_commitment: bool = Field(default=True)
    salient_issues_mapped: bool = Field(default=False)
    corrective_action_plans: int = Field(default=1)
    grievance_mechanism: bool = Field(default=True)
    annual_reporting: bool = Field(default=False)
    board_oversight: bool = Field(default=False)
    third_party_audit_coverage_pct: float = Field(default=40.0, description="% of Tier 1 suppliers audited")
    ilo_compliance_self_assessed: bool = Field(default=True)
    fpic_process_in_place: bool = Field(default=False, description="FPIC process for IPLC-affected activities")


class SupplyChainScreenRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    company_name: str = Field(..., example="RetailCo Ltd")
    sector: str = Field(default="retail")
    tier1_supplier_countries: List[str] = Field(..., example=["CHN", "VNM", "BGD"])
    tier2_supplier_countries: Optional[List[str]] = Field(default=None, example=["IND", "IDN"])
    commodities: Optional[List[str]] = Field(default=None, example=["garments", "electronics"])
    annual_spend_usd: Optional[float] = Field(default=None, example=50_000_000.0)


# ---------------------------------------------------------------------------
# POST endpoints
# ---------------------------------------------------------------------------

@router.post("/assess")
def assess(req: SocialTaxonomyRequest) -> dict[str, Any]:
    """
    Full EU Social Taxonomy assessment for an entity.

    Scores 3 objectives (Decent Work, Living Standards, Inclusive Communities),
    applies DNSH cross-checks and minimum social safeguards test, evaluates UNGP HRDD
    maturity across 6 steps, checks ILO core convention compliance for supplier countries,
    maps sector-level HR risk categories (CSDDD HR-01 to HR-10), and determines
    taxonomy alignment (taxonomy_aligned / taxonomy_enabling / transitioning / not_eligible).
    """
    try:
        return assess_social_taxonomy(
            entity_name=req.entity_name,
            nace_code=req.nace_code,
            sector=req.sector,
            country_of_operations=req.country_of_operations,
            living_wage_compliance_pct=req.living_wage_compliance_pct,
            h_and_s_score=req.h_and_s_score,
            permanent_contract_pct=req.permanent_contract_pct,
            collective_bargaining_coverage_pct=req.collective_bargaining_coverage_pct,
            work_life_balance_score=req.work_life_balance_score,
            healthcare_access_score=req.healthcare_access_score,
            affordable_housing_score=req.affordable_housing_score,
            education_score=req.education_score,
            food_security_score=req.food_security_score,
            financial_inclusion_score=req.financial_inclusion_score,
            inclusive_growth_score=req.inclusive_growth_score,
            digital_access_score=req.digital_access_score,
            cultural_heritage_score=req.cultural_heritage_score,
            just_transition_score=req.just_transition_score,
            stakeholder_engagement_score=req.stakeholder_engagement_score,
            policy_commitment=req.policy_commitment,
            value_chain_mapping=req.value_chain_mapping,
            corrective_actions_count=req.corrective_actions_count,
            grievance_mechanism=req.grievance_mechanism,
            annual_reporting=req.annual_reporting,
            board_oversight=req.board_oversight,
            supplier_countries=req.supplier_countries,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/hrdd")
def hrdd(req: HRDDRequest) -> dict[str, Any]:
    """
    Human Rights Due Diligence (HRDD) assessment per UNGP / CSDDD / OECD DDG 5-step.

    Returns:
    - UNGP 6-step maturity scores (Policy, HRDD, Cessation, Remediation, Reporting, Governance)
    - ILO compliance score per supplier country
    - CSDDD adverse impact likelihood matrix (HR-01 to HR-10) with risk priority
    - OECD DDG 5-step alignment score
    - Supply chain risk summary (high-risk countries, CAHRA flags, audit coverage)
    - Prioritised action recommendations
    """
    try:
        return conduct_hrdd(
            company_name=req.company_name,
            supplier_countries=req.supplier_countries,
            supply_chain_tiers=req.supply_chain_tiers,
            sector=req.sector,
            policy_commitment=req.policy_commitment,
            salient_issues_mapped=req.salient_issues_mapped,
            corrective_action_plans=req.corrective_action_plans,
            grievance_mechanism=req.grievance_mechanism,
            annual_reporting=req.annual_reporting,
            board_oversight=req.board_oversight,
            third_party_audit_coverage_pct=req.third_party_audit_coverage_pct,
            ilo_compliance_self_assessed=req.ilo_compliance_self_assessed,
            fpic_process_in_place=req.fpic_process_in_place,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/supply-chain-screen")
def supply_chain_screen(req: SupplyChainScreenRequest) -> dict[str, Any]:
    """
    Supply chain social risk screening.

    Screens Tier 1 and Tier 2 supplier countries for labour risk, ILO compliance gaps,
    CAHRA flags, and sector-specific HR risk categories. Returns a risk heat map
    and prioritised due diligence recommendations per country and commodity.
    """
    try:
        all_countries = req.tier1_supplier_countries + (req.tier2_supplier_countries or [])

        country_screens = []
        for iso3 in all_countries:
            profile = COUNTRY_LABOUR_RISK_PROFILES.get(iso3.upper(), {})
            tier_flag = "tier1" if iso3 in req.tier1_supplier_countries else "tier2"
            risk_tier = profile.get("labour_risk_tier", 2)
            risk_label = profile.get("labour_risk_label", "Unknown")
            ilo_ratified = profile.get("ilo_conventions_ratified", 4)
            ilo_gaps = profile.get("ilo_core_gaps", [])
            notable = profile.get("notable_risks", [])
            cahra = iso3.upper() in {
                "COD", "SOM", "YEM", "SYR", "IRQ", "AFG", "SDN", "SSD", "CAF",
                "LBY", "MMR", "ERI", "PRK", "VEN", "HTI", "MLI", "BFA",
            }
            country_screens.append({
                "iso3": iso3,
                "supply_chain_tier": tier_flag,
                "country": profile.get("country", iso3),
                "labour_risk_tier": risk_tier,
                "labour_risk_label": risk_label,
                "ilo_conventions_ratified": ilo_ratified,
                "ilo_core_gaps": ilo_gaps,
                "notable_risks": notable,
                "cahra_flag": cahra,
                "recommended_action": (
                    "Enhanced HRDD + onsite audit"
                    if risk_tier >= 4
                    else "Standard HRDD + desk-based audit"
                    if risk_tier == 3
                    else "Questionnaire-based screening"
                ),
            })

        high_risk = [c for c in country_screens if c["labour_risk_tier"] >= 3]
        cahra_list = [c for c in country_screens if c["cahra_flag"]]

        overall_risk = "very_high" if cahra_list else "high" if high_risk else "medium"

        return {
            "company_name": req.company_name,
            "sector": req.sector,
            "countries_screened": len(all_countries),
            "overall_supply_chain_risk": overall_risk,
            "country_screens": country_screens,
            "high_risk_countries": [c["iso3"] for c in high_risk],
            "cahra_countries": [c["iso3"] for c in cahra_list],
            "annual_spend_usd": req.annual_spend_usd,
            "commodities": req.commodities,
            "recommended_next_steps": [
                f"Conduct enhanced HRDD for: {', '.join(c['iso3'] for c in high_risk)}" if high_risk else None,
                f"Apply CAHRA enhanced monitoring for: {', '.join(c['iso3'] for c in cahra_list)}" if cahra_list else None,
                "Obtain third-party social audit certificates for all Tier 1 suppliers",
                "Include ILO core convention compliance clauses in supplier contracts",
            ],
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# GET reference endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/eu-social-taxonomy")
def ref_eu_social_taxonomy() -> dict[str, Any]:
    """
    Reference: EU Social Taxonomy — 3 objectives with full sub-criteria, weights,
    metrics, DNSH rules, and minimum social safeguards test.

    Based on: EC Platform on Sustainable Finance Final Report 2022 + Supplementary Report 2023.
    """
    try:
        return {
            "framework": "EU Social Taxonomy",
            "body": "European Commission — Platform on Sustainable Finance",
            "report_date": "2022-02-28",
            "supplementary_report_date": "2023",
            "status": "Non-binding recommendations; awaiting formal Delegated Act",
            "objectives": EU_SOCIAL_TAXONOMY_OBJECTIVES,
            "dnsh_rule": (
                "Each activity must substantially contribute to at least one objective "
                "AND must not significantly harm the other two (score >= 0.30 in each). "
                "Minimum social safeguards (analogous to EU Taxonomy Art 18) must also be met."
            ),
            "minimum_safeguards": (
                "Alignment with OECD MNE Guidelines 2023, UNGP on Business and Human Rights, "
                "ILO 8 Core Conventions, and EU Charter of Fundamental Rights."
            ),
            "taxonomy_alignment_tiers": {
                "taxonomy_aligned": "Composite >= 0.75; all DNSH passed; minimum safeguards met",
                "taxonomy_enabling": "Composite >= 0.50; minimum safeguards met",
                "transitioning": "Composite >= 0.30",
                "not_taxonomy_eligible": "Composite < 0.30 or blocking DNSH failure",
            },
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/ilo-conventions")
def ref_ilo_conventions() -> dict[str, Any]:
    """
    Reference: ILO 8 Core Conventions under the 1998 Declaration on Fundamental
    Principles and Rights at Work, with full obligations, ratification counts,
    CSDDD Annex I/II mapping, and weighting for compliance scoring.
    """
    try:
        return {
            "framework": "ILO Declaration on Fundamental Principles and Rights at Work",
            "adopted": 1998,
            "body": "International Labour Organization (ILO)",
            "core_conventions_count": 8,
            "four_categories": [
                "Forced Labour (C029, C105)",
                "Child Labour (C138, C182)",
                "Freedom of Association (C087, C098)",
                "Elimination of Discrimination (C100, C111)",
            ],
            "conventions": ILO_CORE_CONVENTIONS,
            "compliance_scoring_note": (
                "Each convention scored 0-1 based on country ratification status, implementation "
                "quality, and violation frequency. Composite = weighted average across all 8 conventions."
            ),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/decent-work")
def ref_decent_work() -> dict[str, Any]:
    """
    Reference: SDG 8 Decent Work Framework — 8 indicator areas (DW1-DW8)
    with SDG target mapping, benchmarks, and weighting.
    """
    try:
        return {
            "framework": "UN Sustainable Development Goal 8 — Decent Work and Economic Growth",
            "sdg_target": "SDG 8 (full employment and decent work for all by 2030)",
            "related_ilo_documents": [
                "ILO Decent Work Agenda (1999)",
                "ILO Centenary Declaration (2019)",
                "ILO Global Commission on Future of Work Report (2019)",
            ],
            "indicators": DECENT_WORK_INDICATORS,
            "composite_note": (
                "DW composite score = weighted average of 8 indicators. "
                "Score >= 0.70 = strong decent work performance. "
                "Score < 0.40 = significant decent work gaps."
            ),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/country-labour-risk")
def ref_country_labour_risk() -> dict[str, Any]:
    """
    Reference: 22 country labour risk profiles with ILO ratification status,
    risk tiers (1-4), forced labour / child labour / freedom of association risk levels,
    gender pay gap %, union density %, and notable labour risks.

    Risk tier definitions:
    - Tier 1 (Low): OECD/EU — robust labour law enforcement
    - Tier 2 (Medium): Some ILO gaps or structural risks
    - Tier 3 (High): Significant HR concerns; enhanced HRDD required
    - Tier 4 (Very High): Severe / systemic violations; mandatory enhanced audit
    """
    try:
        tier_summary: dict[int, list[str]] = {}
        for iso3, profile in COUNTRY_LABOUR_RISK_PROFILES.items():
            tier = profile.get("labour_risk_tier", 2)
            tier_summary.setdefault(tier, []).append(iso3)

        return {
            "countries_covered": len(COUNTRY_LABOUR_RISK_PROFILES),
            "risk_tier_definitions": {
                1: "Low — robust labour law enforcement (OECD/EU)",
                2: "Medium-Low — some ILO gaps or structural risks",
                3: "High — significant HR concerns; enhanced HRDD required",
                4: "Very High — severe / systemic violations; mandatory enhanced audit",
            },
            "tier_summary": tier_summary,
            "profiles": COUNTRY_LABOUR_RISK_PROFILES,
            "cahra_countries_note": (
                "Countries flagged as Conflict-Affected and High-Risk Areas (CAHRA) require "
                "enhanced due diligence per CSDDD Art 6 and OECD DDG Annex II."
            ),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
