"""
API Routes: Climate Litigation Risk Engine (E91)
=================================================
POST /api/v1/climate-litigation/assess               — Full litigation risk assessment
POST /api/v1/climate-litigation/greenwashing-risk    — 20-flag greenwashing risk scoring
POST /api/v1/climate-litigation/disclosure-liability — 8-trigger disclosure liability assessment
POST /api/v1/climate-litigation/fiduciary-duty       — Duties X Framework fiduciary scoring
POST /api/v1/climate-litigation/attribution-science  — Attribution science risk assessment
POST /api/v1/climate-litigation/litigation-exposure  — Aggregate exposure + IAS 37 provision
GET  /api/v1/climate-litigation/ref/case-taxonomy         — Sabin Center 8-category case taxonomy
GET  /api/v1/climate-litigation/ref/jurisdiction-profiles — 15 jurisdiction risk profiles
GET  /api/v1/climate-litigation/ref/disclosure-triggers   — 8 disclosure liability triggers
GET  /api/v1/climate-litigation/ref/greenwashing-flags    — 20 greenwashing red flags
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from services.climate_litigation_engine import (
    ClimateLitigationEngine,
    SABIN_CASE_TAXONOMY,
    JURISDICTION_RISK_PROFILES,
    DISCLOSURE_LIABILITY_TRIGGERS,
    GREENWASHING_RED_FLAGS,
    DUTIES_X_FRAMEWORK,
)

router = APIRouter(prefix="/api/v1/climate-litigation", tags=["Climate Litigation (E91)"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class FullLitigationAssessmentRequest(BaseModel):
    """Complete entity data for full litigation risk assessment."""
    model_config = {"protected_namespaces": ()}

    entity_id: str = ""
    entity_name: str = ""
    sector: str = Field("", description="e.g. oil_gas, coal, banking, asset_management, insurance")
    primary_jurisdiction: str = Field(
        "global",
        description="Primary jurisdiction. One of: US, UK, EU_Germany, EU_Netherlands, EU_France, Australia, Canada, New_Zealand, Switzerland, Japan, Singapore, South_Africa, Brazil, India, global",
    )
    operating_jurisdictions: list[str] = ["UK", "EU_Germany"]
    # Entity type flags
    is_financial_institution: bool = False
    is_pension_fund: bool = False
    is_fossil_fuel_company: bool = False
    # Greenwashing inputs
    triggered_greenwashing_flags: list[str] = Field([], description="Manually identified flag IDs e.g. ['GW-01', 'GW-13']")
    uses_unverified_offsets: bool = False
    net_zero_commitment: bool = False
    transition_plan_published: bool = False
    esg_fund_below_80pct_threshold: bool = False
    scope3_cat15_disclosed: bool = False
    sfdr_art9_overclaimed: bool = False
    net_zero_target_2050: bool = False
    interim_targets_set: bool = False
    # Disclosure liability inputs
    ifrs_s2_disclosed: bool = False
    ifrs_s2_material_error: bool = False
    sec_registered: bool = False
    sec_climate_rule_compliant: bool = True
    csrd_in_scope: bool = False
    csrd_disclosures_incomplete: bool = False
    transition_plan_science_based: bool = False
    tcfd_committed: bool = False
    tcfd_scenario_analysis_done: bool = False
    fossil_fuel_assets_material: bool = False
    ias36_impairment_assessed: bool = False
    climate_investment_policy: bool = False
    # Fiduciary duty inputs
    breach_indicators: list[str] = []
    board_climate_governance_framework: bool = False
    board_climate_training_completed: bool = False
    tcfd_quantified_financial_impact: bool = False
    # Attribution science inputs
    cumulative_scope1_mtco2: float = Field(0.0, ge=0, description="Cumulative Scope 1 emissions in MtCO2")
    physical_assets_coastal_or_flood: bool = False
    # Exposure inputs
    climate_litigation_insurance_m: float = Field(0.0, ge=0, description="Existing climate litigation insurance coverage in EUR M")


class GreenwashingRiskRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    entity_id: str = ""
    operating_jurisdictions: list[str] = ["UK", "EU_Germany"]
    is_financial_institution: bool = False
    triggered_greenwashing_flags: list[str] = []
    uses_unverified_offsets: bool = False
    net_zero_commitment: bool = False
    transition_plan_published: bool = False
    esg_fund_below_80pct_threshold: bool = False
    scope3_cat15_disclosed: bool = False
    sfdr_art9_overclaimed: bool = False
    net_zero_target_2050: bool = False
    interim_targets_set: bool = False


class DisclosureLiabilityRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    entity_id: str = ""
    is_financial_institution: bool = False
    is_pension_fund: bool = False
    ifrs_s2_disclosed: bool = False
    ifrs_s2_material_error: bool = False
    sec_registered: bool = False
    sec_climate_rule_compliant: bool = True
    csrd_in_scope: bool = False
    csrd_disclosures_incomplete: bool = False
    transition_plan_published: bool = False
    transition_plan_science_based: bool = False
    tcfd_committed: bool = False
    tcfd_scenario_analysis_done: bool = False
    scope3_cat15_disclosed: bool = False
    fossil_fuel_assets_material: bool = False
    ias36_impairment_assessed: bool = False
    climate_investment_policy: bool = False


class FiduciaryDutyRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    entity_id: str = ""
    breach_indicators: list[str] = Field([], description="Free-text breach indicators matching DUTIES_X_FRAMEWORK breach_indicators")
    board_climate_governance_framework: bool = False
    board_climate_training_completed: bool = False
    tcfd_quantified_financial_impact: bool = False
    transition_plan_published: bool = False
    is_pension_fund: bool = False


class AttributionScienceRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    entity_id: str = ""
    sector: str = Field("", description="Entity sector for attribution pathway matching")
    primary_jurisdiction: str = "global"
    cumulative_scope1_mtco2: float = Field(0.0, ge=0)
    is_fossil_fuel_company: bool = False
    physical_assets_coastal_or_flood: bool = False


class LitigationExposureRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    entity_id: str = ""
    operating_jurisdictions: list[str] = ["global"]
    greenwashing_flag_count: int = Field(0, ge=0)
    disclosure_liability_max_m: float = Field(0.0, ge=0)
    do_liability_exposure_m: float = Field(0.0, ge=0)
    attribution_science_applicable: bool = False
    attribution_litigation_probability_pct: float = Field(5.0, ge=0, le=100)
    cumulative_scope1_mtco2: float = Field(0.0, ge=0)
    climate_litigation_insurance_m: float = Field(0.0, ge=0)


# ---------------------------------------------------------------------------
# POST Endpoints
# ---------------------------------------------------------------------------

@router.post("/assess")
async def run_full_assessment(req: FullLitigationAssessmentRequest):
    """
    Full climate litigation risk assessment across all 5 sub-modules.
    Produces composite litigation_risk_score (0-100), risk tier (minimal/low/medium/high/critical),
    max/expected litigation exposure (EUR M), IAS 37 provision requirement, and priority actions.
    """
    engine = ClimateLitigationEngine()
    result = engine.run_full_assessment(req.model_dump())
    return {
        "entity_id": result.entity_id,
        "entity_name": result.entity_name,
        "assessment_date": result.assessment_date,
        "litigation_risk_score": result.litigation_risk_score,
        "risk_tier": result.risk_tier,
        "exposure": {
            "max_litigation_exposure_m": result.max_litigation_exposure_m,
            "expected_litigation_cost_m": result.expected_litigation_cost_m,
            "ias37_provision_m": result.ias37_provision_m,
            "insurance_gap_m": result.insurance_gap_m,
        },
        "component_scores": {
            "greenwashing_risk_score": result.greenwashing_risk_score,
            "disclosure_liability_score": result.disclosure_liability_score,
            "fiduciary_duty_score": result.fiduciary_duty_score,
            "attribution_science_applicable": result.attribution_science_applicable,
        },
        "key_risk_drivers": result.key_risk_drivers,
        "priority_actions": result.priority_actions,
        "cross_framework": result.cross_framework,
    }


@router.post("/greenwashing-risk")
async def assess_greenwashing_risk(req: GreenwashingRiskRequest):
    """
    Check 20 greenwashing red flags (Sabin Center / FCA / EU Green Claims Directive taxonomy).
    Returns greenwashing_risk_score (0-100), risk tier, triggered flags, regulatory exposure
    by jurisdiction, max fine exposure, and recommended remediation actions.
    """
    engine = ClimateLitigationEngine()
    r = engine.assess_greenwashing_risk(req.model_dump())
    return {
        "greenwashing_risk_score": r.greenwashing_risk_score,
        "risk_tier": r.risk_tier,
        "flag_count": r.flag_count,
        "triggered_flags": r.triggered_flags,
        "max_fine_exposure_m": r.max_fine_exposure_m,
        "regulatory_exposure_by_jurisdiction": r.regulatory_exposure_by_jurisdiction,
        "recommended_remediation": r.recommended_remediation,
        "notes": r.notes,
    }


@router.post("/disclosure-liability")
async def assess_disclosure_liability(req: DisclosureLiabilityRequest):
    """
    Check 8 disclosure liability triggers (IFRS S2, SEC Climate Rule, CSRD, TCFD, Scope 3,
    asset stranding, fiduciary breach). Quantifies exposure per trigger and in aggregate,
    returns disclosure_liability_score (0-100) and priority remediation actions.
    """
    engine = ClimateLitigationEngine()
    r = engine.assess_disclosure_liability(req.model_dump())
    return {
        "disclosure_liability_score": r.disclosure_liability_score,
        "trigger_count": r.trigger_count,
        "max_exposure_m": r.max_exposure_m,
        "expected_exposure_m": r.expected_exposure_m,
        "triggered_triggers": r.triggered_triggers,
        "exposure_by_trigger": r.exposure_by_trigger,
        "priority_remediation": r.priority_remediation,
        "notes": r.notes,
    }


@router.post("/fiduciary-duty")
async def assess_fiduciary_duty(req: FiduciaryDutyRequest):
    """
    Score all 6 Duties X Framework fiduciary duties (UCL / ClientEarth 2023).
    Returns fiduciary_adequacy_score (0-100), adequacy tier, breach indicators,
    stewardship gaps, D&O liability exposure, and improvement actions.
    """
    engine = ClimateLitigationEngine()
    r = engine.assess_fiduciary_duty(req.model_dump())
    return {
        "fiduciary_adequacy_score": r.fiduciary_adequacy_score,
        "adequacy_tier": r.adequacy_tier,
        "duty_scores": r.duty_scores,
        "breach_indicators_identified": r.breach_indicators_identified,
        "stewardship_gaps": r.stewardship_gaps,
        "do_liability_exposure_m": r.do_liability_exposure_m,
        "improvement_actions": r.improvement_actions,
    }


@router.post("/attribution-science")
async def assess_attribution_science(req: AttributionScienceRequest):
    """
    Assess attribution science applicability for climate litigation.
    Computes Meehl-Haugen-Christidis composite score, physical damage attribution %
    (Carbon Majors methodology), litigation probability, and key attribution pathways.
    """
    engine = ClimateLitigationEngine()
    r = engine.assess_attribution_science_risk(req.model_dump())
    return {
        "attribution_applicable": r.attribution_applicable,
        "applicability_rationale": r.applicability_rationale,
        "meehl_haugen_christidis_score": r.meehl_haugen_christidis_score,
        "physical_damage_attributable_pct": r.physical_damage_attributable_pct,
        "litigation_probability_pct": r.litigation_probability_pct,
        "jurisdiction_risk": r.jurisdiction_risk,
        "key_attribution_pathways": r.key_attribution_pathways,
        "notes": r.notes,
    }


@router.post("/litigation-exposure")
async def compute_litigation_exposure(req: LitigationExposureRequest):
    """
    Aggregate all climate litigation exposure streams. Computes max and expected
    litigation cost (EUR M), insurance adequacy gap, IAS 37 provision requirement,
    and jurisdiction risk score.
    """
    engine = ClimateLitigationEngine()
    r = engine.compute_litigation_exposure(req.model_dump())
    return {
        "max_litigation_cost_m": r.max_litigation_cost_m,
        "expected_litigation_cost_m": r.expected_litigation_cost_m,
        "insurance_coverage_m": r.insurance_coverage_m,
        "insurance_adequacy_gap_m": r.insurance_adequacy_gap_m,
        "ias37_provision_required_m": r.ias37_provision_required_m,
        "ias37_provision_basis": r.ias37_provision_basis,
        "jurisdiction_risk_score": r.jurisdiction_risk_score,
        "exposure_streams": r.exposure_streams,
        "notes": r.notes,
    }


# ---------------------------------------------------------------------------
# GET Reference Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/case-taxonomy")
async def get_case_taxonomy():
    """
    Sabin Center for Climate Change Law — 8-category climate litigation case taxonomy
    with typical plaintiffs/defendants, key jurisdictions, settlement ranges, success rates,
    and leading case examples.
    """
    return {
        "case_taxonomy": SABIN_CASE_TAXONOMY,
        "category_count": len(SABIN_CASE_TAXONOMY),
        "source": "Sabin Center for Climate Change Law, Columbia Law School — Global Climate Litigation Report 2024",
        "total_cases_worldwide_2024": 2500,
        "growth_note": "Climate litigation doubled 2015-2022; financial sector cases tripled 2020-2024",
        "fastest_growing_categories": ["greenwashing", "mandatory_disclosure", "attribution_science"],
    }


@router.get("/ref/jurisdiction-profiles")
async def get_jurisdiction_profiles():
    """
    Climate litigation risk profiles for 15 jurisdictions with activity scores,
    regulatory enforcement scores, greenwashing enforcement scores, key legislation,
    and recent precedents.
    """
    # Return summary view for list; detailed view available per jurisdiction
    summary = {
        jur: {
            "climate_litigation_activity_score": prof["climate_litigation_activity_score"],
            "greenwashing_enforcement_score": prof["greenwashing_enforcement_score"],
            "litigation_trend": prof.get("litigation_trend", "unknown"),
            "key_legislation_count": len(prof["key_legislation"]),
        }
        for jur, prof in JURISDICTION_RISK_PROFILES.items()
    }
    return {
        "jurisdiction_summary": summary,
        "jurisdiction_details": JURISDICTION_RISK_PROFILES,
        "jurisdiction_count": len(JURISDICTION_RISK_PROFILES),
        "highest_activity_jurisdictions": sorted(
            JURISDICTION_RISK_PROFILES.keys(),
            key=lambda j: JURISDICTION_RISK_PROFILES[j]["climate_litigation_activity_score"],
            reverse=True,
        )[:5],
        "source": "Grantham Research Institute / Sabin Center — Global Trends in Climate Change Litigation 2024",
    }


@router.get("/ref/disclosure-triggers")
async def get_disclosure_triggers():
    """
    8 disclosure liability triggers with jurisdiction, statute reference, plaintiff standing,
    typical claim ranges (EUR M), and enforcement bodies.
    """
    return {
        "disclosure_liability_triggers": DISCLOSURE_LIABILITY_TRIGGERS,
        "trigger_count": len(DISCLOSURE_LIABILITY_TRIGGERS),
        "duties_x_framework": DUTIES_X_FRAMEWORK,
        "max_single_trigger_exposure_m": max(
            v["typical_claim_m_range"][1] for v in DISCLOSURE_LIABILITY_TRIGGERS.values()
        ),
        "source": (
            "IFRS S2 (2023); SEC Release 33-11275 (2024); CSRD/ESRS E1 (2024); "
            "FCA PS23/22 TPT; TCFD Recommendations 2017; IAS 36/37; PCAF Standard 2022"
        ),
    }


@router.get("/ref/greenwashing-flags")
async def get_greenwashing_flags():
    """
    20 greenwashing red flags across 4 categories (misleading_claims, omission_of_material_info,
    false_impression, future_targets) with regulator, enforcement history, fine ranges, and remediation.
    """
    # Flatten for easy consumption
    all_flags = []
    for category, flags in GREENWASHING_RED_FLAGS.items():
        for flag in flags:
            all_flags.append({**flag, "category": category})

    return {
        "greenwashing_red_flags": GREENWASHING_RED_FLAGS,
        "all_flags_flat": all_flags,
        "flag_count": len(all_flags),
        "categories": list(GREENWASHING_RED_FLAGS.keys()),
        "flags_with_enforcement_precedent": [f["flag_id"] for f in all_flags if f["enforcement_action_taken"]],
        "source": (
            "EU Green Claims Directive (EU) 2023/2441; FCA Anti-Greenwashing Rule PS23/16; "
            "ASIC RG 274; ESMA Fund Names Guidelines ESMA34-1113322-2383; "
            "Sabin Center Greenwashing case database 2024"
        ),
        "scoring_note": (
            "Risk score = 10 points per triggered flag + 3-point uplift if enforcement action previously taken. "
            "Maximum score 100."
        ),
    }
