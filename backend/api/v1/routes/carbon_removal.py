"""
API Routes: Carbon Removal & CDR Finance Engine (E90)
======================================================
POST /api/v1/carbon-removal/assess              — Full CDR project assessment
POST /api/v1/carbon-removal/technology-assessment — CDR technology profile + TRL scoring
POST /api/v1/carbon-removal/oxford-principles   — Oxford CDR Principles scoring (4 principles)
POST /api/v1/carbon-removal/article-64          — Paris Agreement Art 6.4 ITMO eligibility
POST /api/v1/carbon-removal/cdr-economics       — LCOE, NPV/IRR, break-even, blended finance
POST /api/v1/carbon-removal/market-eligibility  — CORSIA, Frontier AMC, voluntary market tier
GET  /api/v1/carbon-removal/ref/technology-profiles — CDR technology reference data (8 types)
GET  /api/v1/carbon-removal/ref/oxford-principles   — Oxford CDR Principles definitions
GET  /api/v1/carbon-removal/ref/market-benchmarks   — CDR market buyer benchmarks
GET  /api/v1/carbon-removal/ref/frontier-criteria   — Frontier AMC eligibility criteria
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from services.carbon_removal_engine import (
    CarbonRemovalEngine,
    CDR_TECHNOLOGY_PROFILES,
    OXFORD_CDR_PRINCIPLES,
    CDR_MARKET_BENCHMARKS,
    FRONTIER_ELIGIBILITY_CRITERIA,
    ARTICLE_64_ELIGIBILITY,
)

router = APIRouter(prefix="/api/v1/carbon-removal", tags=["Carbon Removal (E90)"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class CDRProjectRequest(BaseModel):
    """Full CDR project data for assessment."""
    model_config = {"protected_namespaces": ()}

    project_id: str = ""
    project_name: str = ""
    cdr_type: str = Field(
        ...,
        description=(
            "CDR technology type. One of: beccs, dacs, enhanced_weathering, blue_carbon, "
            "biochar, afforestation_reforestation, soil_carbon, ocean_alkalinity_enhancement"
        ),
    )
    host_country: str = ""
    annual_removal_tco2: float = Field(1000.0, ge=0, description="Annual CO2 removal in tCO2")
    capex_usd: float = Field(1_000_000.0, ge=0, description="Total project CAPEX in USD")
    annual_opex_usd: float = Field(100_000.0, ge=0, description="Annual OPEX in USD")
    project_life_years: int = Field(20, ge=1, le=100)
    discount_rate_pct: float = Field(8.0, ge=0, le=50)
    cost_usd_tco2_current: Optional[float] = Field(None, ge=0, description="Override current cost if known")
    permanence_years: Optional[int] = Field(None, ge=0)
    # Oxford Principles inputs
    financial_additionality_documented: bool = False
    regulatory_additionality_documented: bool = False
    common_practice_test_passed: bool = False
    conservative_baseline_used: bool = False
    additionality_justification: str = ""
    buffer_pool_or_insurance: bool = False
    reversal_monitoring_protocol: bool = False
    approved_quantification_methodology: bool = False
    third_party_verification: bool = False
    digital_satellite_monitoring: bool = False
    registry_issuance: bool = False
    biodiversity_net_positive: bool = False
    biodiversity_neutral: bool = False
    fpic_documented: bool = False
    no_food_security_displacement: bool = True
    water_stress_assessment_done: bool = False
    # Art 6.4 inputs
    corresponding_adjustment_agreed: bool = False
    host_country_approval: bool = False
    no_suppressed_demand_baseline: bool = True
    safeguards_applied: bool = False
    monitoring_plan_submitted: bool = False
    authorized_party_designated: bool = False
    international_transfer_intended: bool = True
    # Market eligibility inputs
    corsia_programme_enrollment: bool = False
    corsia_programme_name: str = ""
    peer_reviewed_methodology: bool = False
    # Blended finance
    blended_finance_grant_pct: float = Field(0.0, ge=0, le=100)
    # Misc
    identified_risks: list[str] = []


class TechnologyAssessmentRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    cdr_type: str = Field(..., description="CDR technology type")
    cost_usd_tco2_current: Optional[float] = Field(None, ge=0)
    identified_risks: list[str] = []


class OxfordPrinciplesRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    cdr_type: str = ""
    permanence_years: Optional[int] = None
    financial_additionality_documented: bool = False
    regulatory_additionality_documented: bool = False
    common_practice_test_passed: bool = False
    conservative_baseline_used: bool = False
    additionality_justification: str = ""
    buffer_pool_or_insurance: bool = False
    reversal_monitoring_protocol: bool = False
    approved_quantification_methodology: bool = False
    third_party_verification: bool = False
    digital_satellite_monitoring: bool = False
    registry_issuance: bool = False
    biodiversity_net_positive: bool = False
    biodiversity_neutral: bool = False
    fpic_documented: bool = False
    no_food_security_displacement: bool = True
    water_stress_assessment_done: bool = False


class Article64Request(BaseModel):
    model_config = {"protected_namespaces": ()}
    cdr_type: str = ""
    host_country: str = ""
    corresponding_adjustment_agreed: bool = False
    host_country_approval: bool = False
    no_suppressed_demand_baseline: bool = True
    safeguards_applied: bool = False
    monitoring_plan_submitted: bool = False
    authorized_party_designated: bool = False
    international_transfer_intended: bool = True


class CDREconomicsRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    cdr_type: str = ""
    annual_removal_tco2: float = Field(1000.0, ge=0)
    capex_usd: float = Field(1_000_000.0, ge=0)
    annual_opex_usd: float = Field(100_000.0, ge=0)
    project_life_years: int = Field(20, ge=1, le=100)
    discount_rate_pct: float = Field(8.0, ge=0, le=50)
    blended_finance_grant_pct: float = Field(0.0, ge=0, le=100)


class MarketEligibilityRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    cdr_type: str = Field(..., description="CDR technology type")
    oxford_composite_score: float = Field(0.0, ge=0, le=100)
    approved_quantification_methodology: bool = False
    peer_reviewed_methodology: bool = False
    third_party_verification: bool = False
    corsia_programme_enrollment: bool = False
    corsia_programme_name: str = ""
    article_64_eligible: bool = False
    permanence_years: Optional[int] = None


# ---------------------------------------------------------------------------
# POST Endpoints
# ---------------------------------------------------------------------------

@router.post("/assess")
async def run_full_assessment(req: CDRProjectRequest):
    """
    Full CDR project assessment — technology, Oxford Principles, Art 6.4,
    economics, and market eligibility combined into cdr_quality_score (0-100)
    and cdr_quality_tier (gold/silver/bronze/basic).
    """
    engine = CarbonRemovalEngine()
    result = engine.run_full_assessment(req.model_dump())
    return {
        "project_id": result.project_id,
        "assessment_date": result.assessment_date,
        "cdr_type": result.cdr_type,
        "cdr_quality_score": result.cdr_quality_score,
        "cdr_quality_tier": result.cdr_quality_tier,
        "technology": {
            "trl_level": result.trl_level,
            "scalability_rating": result.scalability_rating,
            "cost_current_usd_tco2": result.cost_current_usd_tco2,
            "cost_2050_usd_tco2": result.cost_2050_usd_tco2,
        },
        "oxford_principles": {
            "composite_score": result.oxford_composite_score,
            "quality_tier": result.oxford_quality_tier,
        },
        "article_64": {
            "eligible": result.article_64_eligible,
            "itmo_eligible": result.itmo_eligible,
        },
        "economics": {
            "lcoe_usd_tco2": result.lcoe_usd_tco2,
            "break_even_price_usd_tco2": result.break_even_price_usd_tco2,
            "irr_at_100_usd_pct": result.irr_at_100_usd_pct,
        },
        "market": {
            "frontier_eligible": result.frontier_eligible,
            "corsia_eligible": result.corsia_eligible,
            "best_match_buyer": result.best_match_buyer,
            "credit_price_benchmark_usd": result.credit_price_benchmark_usd,
        },
        "key_strengths": result.key_strengths,
        "key_risks": result.key_risks,
        "recommended_actions": result.recommended_actions,
        "cross_framework": result.cross_framework,
    }


@router.post("/technology-assessment")
async def assess_technology(req: TechnologyAssessmentRequest):
    """
    CDR technology profile matching, TRL assessment, cost trajectory, scalability,
    and co-benefit scoring. Returns technology_readiness_score (0-100).
    """
    engine = CarbonRemovalEngine()
    r = engine.assess_cdr_technology(req.model_dump())
    return {
        "cdr_type": r.cdr_type,
        "name": r.name,
        "ipcc_category": r.ipcc_category,
        "trl_level": r.trl_level,
        "trl_assessment": r.trl_assessment,
        "cost_current_usd_tco2": r.cost_current_usd_tco2,
        "cost_2030_usd_tco2": r.cost_2030_usd_tco2,
        "cost_2050_usd_tco2": r.cost_2050_usd_tco2,
        "cost_reduction_pct_to_2050": r.cost_reduction_pct_to_2050,
        "permanence_years": r.permanence_years,
        "scalability_rating": r.scalability_rating,
        "co_benefit_score": r.co_benefit_score,
        "co_benefits": r.co_benefits,
        "risk_count": r.risk_count,
        "risk_flags": r.risk_flags,
        "land_use_ha_per_mtco2": r.land_use_ha_per_mtco2,
        "water_use_m3_per_tco2": r.water_use_m3_per_tco2,
        "technology_readiness_score": r.technology_readiness_score,
        "notes": r.notes,
    }


@router.post("/oxford-principles")
async def score_oxford_principles(req: OxfordPrinciplesRequest):
    """
    Score all 4 Oxford CDR Principles (additionality, permanence,
    monitoring_verification, no_harm). Returns composite 0-100 score,
    quality tier, and gap analysis.
    """
    engine = CarbonRemovalEngine()
    r = engine.score_oxford_principles(req.model_dump())
    return {
        "scores": {
            "additionality": r.additionality_score,
            "permanence": r.permanence_score,
            "monitoring_verification": r.monitoring_verification_score,
            "no_harm": r.no_harm_score,
        },
        "composite_score": r.composite_score,
        "quality_tier": r.quality_tier,
        "gap_analysis": r.gap_analysis,
        "strengths": r.strengths,
        "improvement_actions": r.improvement_actions,
    }


@router.post("/article-64")
async def assess_article64(req: Article64Request):
    """
    Paris Agreement Article 6.4 eligibility check. Verifies all 6 requirements
    for ITMO issuance and corresponding adjustment obligations.
    """
    engine = CarbonRemovalEngine()
    r = engine.assess_article64_eligibility(req.model_dump())
    return {
        "requirements_met": r.requirements_met,
        "total_requirements": r.total_requirements,
        "itmo_eligible": r.itmo_eligible,
        "corresponding_adjustment_required": r.corresponding_adjustment_required,
        "host_country_ndc_contribution": r.host_country_ndc_contribution,
        "requirement_checks": {
            "corresponding_adjustment": r.corresponding_adjustment,
            "host_country_approval": r.host_country_approval,
            "suppressed_demand_exclusion": r.suppressed_demand_exclusion,
            "social_environmental_safeguards": r.social_environmental_safeguards,
            "monitoring_plan": r.monitoring_plan,
            "authorized_party": r.authorized_party,
        },
        "eligibility_gaps": r.eligibility_gaps,
        "eligibility_notes": r.eligibility_notes,
    }


@router.post("/cdr-economics")
async def calculate_economics(req: CDREconomicsRequest):
    """
    CDR project economics: CAPEX/OPEX modelling, LCOE ($/tCO2), NPV at $50/$100/$200
    credit price scenarios, IRR, break-even price, and blended finance uplift.
    """
    engine = CarbonRemovalEngine()
    r = engine.calculate_cdr_economics(req.model_dump())
    return {
        "inputs": {
            "capex_usd_total": r.capex_usd_total,
            "annual_opex_usd": r.annual_opex_usd,
            "annual_removal_tco2": r.annual_removal_tco2,
            "project_life_years": r.project_life_years,
        },
        "lcoe_usd_tco2": r.lcoe_usd_tco2,
        "lcoe_with_blended_finance": r.lcoe_with_blended_finance,
        "break_even_price_usd_tco2": r.break_even_price_usd_tco2,
        "blended_finance_uplift_usd": r.blended_finance_uplift_usd,
        "npv_scenarios": {
            "npv_at_50_usd": r.npv_at_50_usd,
            "npv_at_100_usd": r.npv_at_100_usd,
            "npv_at_200_usd": r.npv_at_200_usd,
        },
        "irr_scenarios": {
            "irr_at_50_usd_pct": r.irr_at_50_usd_pct,
            "irr_at_100_usd_pct": r.irr_at_100_usd_pct,
            "irr_at_200_usd_pct": r.irr_at_200_usd_pct,
        },
        "economics_viability": r.economics_viability,
        "sensitivity_notes": r.sensitivity_notes,
    }


@router.post("/market-eligibility")
async def assess_market_eligibility(req: MarketEligibilityRequest):
    """
    CDR market eligibility: CORSIA compliance, Frontier AMC scoring, voluntary market
    tier, corporate buyer matching, and credit price benchmark.
    """
    engine = CarbonRemovalEngine()
    r = engine.assess_market_eligibility(req.model_dump())
    return {
        "corsia": {
            "eligible": r.corsia_eligible,
            "programme": r.corsia_programme,
        },
        "frontier_amc": {
            "eligible": r.frontier_eligible,
            "score": r.frontier_score,
            "gap_analysis": r.frontier_gap_analysis,
        },
        "voluntary_market": {
            "tier": r.voluntary_market_tier,
            "registry": r.voluntary_registry,
        },
        "buyer_matching": {
            "eligible_buyer_types": r.eligible_buyer_types,
            "best_match_buyer": r.best_match_buyer,
            "credit_price_benchmark_usd": r.credit_price_benchmark_usd,
            "price_range_usd": r.price_range_usd,
        },
        "market_notes": r.market_notes,
    }


# ---------------------------------------------------------------------------
# GET Reference Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/technology-profiles")
async def get_technology_profiles():
    """
    CDR technology reference data: 8 technology types with IPCC categories, TRL,
    cost trajectories, permanence, co-benefits, risks, scalability, and land/water use.
    """
    return {
        "technology_profiles": CDR_TECHNOLOGY_PROFILES,
        "count": len(CDR_TECHNOLOGY_PROFILES),
        "source": "IPCC AR6 WG3 Chapter 12 — Carbon Dioxide Removal",
        "trl_scale": {
            "1-3": "Early research",
            "4-5": "R&D / lab validation",
            "6-7": "Demonstration",
            "8-9": "Commercial / near-commercial",
        },
        "scalability_ratings": ["limited", "moderate", "high", "very_high"],
        "ipcc_categories": ["biological", "geochemical", "technological"],
    }


@router.get("/ref/oxford-principles")
async def get_oxford_principles():
    """
    Oxford CDR Principles 2023 — 4 principles: additionality, permanence,
    monitoring_verification, no_harm — with sub-criteria, scoring guidance, and weights.
    """
    return {
        "oxford_cdr_principles": OXFORD_CDR_PRINCIPLES,
        "source": "Oxford Principles for Net Zero Aligned Carbon Offsetting (2023 update)",
        "quality_tiers": {
            "gold": "Composite score >= 80/100",
            "silver": "Composite score 60-79/100",
            "bronze": "Composite score 40-59/100",
            "basic": "Composite score < 40/100",
        },
        "article_64_synergy": (
            "Oxford Principles align closely with Art 6.4 Supervisory Body requirements. "
            "Gold-tier Oxford scoring strongly correlated with Art 6.4 ITMO eligibility."
        ),
    }


@router.get("/ref/market-benchmarks")
async def get_market_benchmarks():
    """
    CDR market buyer benchmarks: 6 buyer types with typical prices, volumes,
    growth rates, quality preferences, and key frameworks.
    """
    return {
        "market_benchmarks": CDR_MARKET_BENCHMARKS,
        "buyer_count": len(CDR_MARKET_BENCHMARKS),
        "article_64_eligibility": ARTICLE_64_ELIGIBILITY,
        "total_vcm_volume_2024_tco2": sum(
            v["volume_tco2_yr_2024"] for v in CDR_MARKET_BENCHMARKS.values()
        ),
        "source": (
            "Ecosystem Marketplace State of Voluntary Carbon Markets 2024; "
            "BloombergNEF Carbon Markets Outlook 2024; "
            "Frontier AMC annual report 2024"
        ),
    }


@router.get("/ref/frontier-criteria")
async def get_frontier_criteria():
    """
    Frontier Advance Market Commitment eligibility criteria — 5 criteria with
    thresholds, weights, and evaluation guidance. Source: Frontier v1.2 (2023).
    """
    return {
        "frontier_eligibility_criteria": FRONTIER_ELIGIBILITY_CRITERIA,
        "criteria_count": len(FRONTIER_ELIGIBILITY_CRITERIA),
        "total_weight": sum(v["weight"] for v in FRONTIER_ELIGIBILITY_CRITERIA.values()),
        "eligibility_threshold": "Score >= 60/100 AND novel_technology score > 0",
        "founding_members": ["Stripe", "Alphabet", "Meta", "McKinsey", "Shopify"],
        "commitment_size_usd": "900M+ advance purchase commitments through 2030",
        "source": "Frontier Advance Market Commitment Eligibility Criteria v1.2 (2023)",
        "excluded_project_types": [
            "Afforestation/reforestation",
            "REDD+",
            "Renewable energy without CDR component",
            "Improved forest management",
        ],
    }
