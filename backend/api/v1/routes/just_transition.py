"""
API Routes — Just Transition Finance Engine (E89)
==================================================
POST /api/v1/just-transition/assess
POST /api/v1/just-transition/ilo-principles
POST /api/v1/just-transition/eu-jtf-eligibility
POST /api/v1/just-transition/workforce-transition
POST /api/v1/just-transition/community-resilience
POST /api/v1/just-transition/cif-eligibility
GET  /api/v1/just-transition/ref/ilo-principles
GET  /api/v1/just-transition/ref/coal-community-profiles
GET  /api/v1/just-transition/ref/sector-profiles
GET  /api/v1/just-transition/ref/cif-facilities
"""
from typing import Any, Optional, List, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.just_transition_engine import (
    JustTransitionEngine,
    ILO_JT_PRINCIPLES,
    EU_JTF_ELIGIBILITY_CRITERIA,
    COAL_COMMUNITY_PROFILES,
    CIF_FACILITY_PROFILES,
    JUST_TRANSITION_SECTOR_PROFILES,
)

router = APIRouter(
    prefix="/api/v1/just-transition",
    tags=["just_transition"],
)

_engine = JustTransitionEngine()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class ILOPrinciplesRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str = Field("ENTITY_001", description="Entity or region identifier")
    region_name: str = Field("Silesia, Poland", description="Region name")
    country: str = Field("Poland", description="Country")
    sector: str = Field(
        "coal",
        description=(
            "Primary sector under transition: coal, oil_gas, steel, cement, "
            "automotive, aviation, shipping, agriculture"
        ),
    )
    principle_scores: dict[str, float] = Field(
        default_factory=lambda: {
            "social_dialogue": 45.0,
            "skills_reskilling": 40.0,
            "social_protection": 55.0,
            "active_labour_market_policy": 35.0,
            "community_investment": 30.0,
        },
        description=(
            "ILO JT principle scores (0-100) for each of the 5 principles: "
            "social_dialogue, skills_reskilling, social_protection, "
            "active_labour_market_policy, community_investment"
        ),
    )


class EUJTFEligibilityRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str = Field("ENTITY_001", description="Entity or region identifier")
    region_name: str = Field("Silesia", description="NUTS2 region name")
    country: str = Field("Poland", description="EU Member State")
    nuts2_code: str = Field("PL22", description="NUTS2 region code")
    criteria_status: dict[str, bool] = Field(
        default_factory=lambda: {
            "territorial_jtp": True,
            "ghg_emission_dependency": True,
            "fossil_fuel_employment": True,
            "economic_diversification": False,
            "social_partnership_evidence": True,
            "green_jobs_target": False,
            "just_transition_monitoring": False,
            "cross_border_coordination": False,
        },
        description="Boolean status for each of the 8 JTF eligibility criteria",
    )
    regional_gdp_m_eur: float = Field(
        25_000.0,
        ge=0.0,
        description="Regional GDP in EUR millions",
    )
    population_k: float = Field(4_500.0, gt=0, description="Regional population in thousands")
    fossil_employment_k: float = Field(
        85.0,
        ge=0.0,
        description="Workers employed in fossil fuel sectors (thousands)",
    )
    total_employment_k: float = Field(
        1_500.0,
        gt=0,
        description="Total regional employment (thousands)",
    )


class WorkforceTransitionRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str = Field("ENTITY_001", description="Entity or region identifier")
    sector: str = Field(
        "coal",
        description=(
            "Primary sector: coal, oil_gas, steel, cement, "
            "automotive, aviation, shipping, agriculture"
        ),
    )
    region_name: str = Field("Mpumalanga, South Africa", description="Region name")
    country: str = Field("South Africa", description="Country")
    fossil_workers_k: float = Field(
        90.0,
        gt=0,
        description="Workers in fossil fuel sector (thousands)",
    )
    green_jobs_pipeline_k: float = Field(
        60.0,
        ge=0.0,
        description="Projected green jobs in pipeline by phase-out end year (thousands)",
    )
    avg_fossil_wage_usd: float = Field(
        35_000.0,
        gt=0,
        description="Average annual wage in fossil sector (USD)",
    )
    avg_green_wage_usd: float = Field(
        28_000.0,
        gt=0,
        description="Average annual wage in green replacement sector (USD)",
    )
    reskilling_duration_months: float = Field(
        14.0,
        ge=1.0,
        description="Average reskilling programme duration (months)",
    )
    reskilling_cost_per_worker_usd: float = Field(
        8_500.0,
        gt=0,
        description="Cost of reskilling per worker (USD)",
    )
    phase_out_start_year: int = Field(2025, description="Year fossil sector phase-out begins")
    phase_out_end_year: int = Field(2040, description="Year fossil sector phase-out completes")
    jetp_pledge: bool = Field(
        False,
        description="Country has signed a Just Energy Transition Partnership (JETP) pledge",
    )


class CommunityResilienceRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str = Field("ENTITY_001", description="Entity or region identifier")
    region_name: str = Field("Mpumalanga", description="Region name")
    country: str = Field("South Africa", description="Country")
    coal_profile_key: Optional[str] = Field(
        None,
        description=(
            "Optional key from COAL_COMMUNITY_PROFILES to load profile defaults "
            "(e.g. 'mpumalanga_za', 'silesia_poland', 'appalachia_usa')"
        ),
    )
    gdp_fossil_dependency_pct: float = Field(
        25.0,
        ge=0.0,
        le=100.0,
        description="Share of regional GDP derived from fossil fuel activities (%)",
    )
    infrastructure_score: float = Field(
        45.0,
        ge=0.0,
        le=100.0,
        description=(
            "Infrastructure quality score (0-100): "
            "transport, broadband, utilities, healthcare, education"
        ),
    )
    alternative_employer_count: int = Field(
        3,
        ge=0,
        description="Number of significant non-fossil employers in the region",
    )
    skills_transferability: float = Field(
        2.5,
        ge=1.0,
        le=5.0,
        description="Skills transferability score (1-5; 5 = highly transferable to green economy)",
    )
    social_cohesion_score: float = Field(
        50.0,
        ge=0.0,
        le=100.0,
        description="Social cohesion score (0-100; union density, civic participation, trust)",
    )
    alternative_sector_score: float = Field(
        0.30,
        ge=0.0,
        le=1.0,
        description=(
            "Economic diversification potential score (0-1; "
            "0 = no alternatives, 1 = strong diversified economy)"
        ),
    )


class CIFEligibilityRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str = Field("ENTITY_001", description="Entity or project identifier")
    country: str = Field("Kenya", description="Project host country")
    sector: str = Field("energy", description="Project sector")
    project_type: str = Field(
        "renewable_energy",
        description=(
            "Project type: renewable_energy, energy_efficiency, sustainable_transport, "
            "REDD+_readiness, climate_resilient_agriculture, etc."
        ),
    )
    project_cost_m: float = Field(
        50.0,
        gt=0,
        description="Total project cost in USD millions",
    )
    income_group: str = Field(
        "low",
        description="World Bank income group: low, lower_middle, upper_middle, high",
    )
    has_national_climate_plan: bool = Field(
        True,
        description="Country has adopted a National Climate Plan / NDC",
    )
    forest_coverage_pct: float = Field(
        35.0,
        ge=0.0,
        le=100.0,
        description="National forest coverage as % of land area (relevant for FIP eligibility)",
    )
    grid_electrification_rate_pct: float = Field(
        45.0,
        ge=0.0,
        le=100.0,
        description="National grid electrification rate % (relevant for SREP eligibility)",
    )


class FullAssessmentRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str = Field("ENTITY_001", description="Entity or region identifier")
    region_name: str = Field("Mpumalanga", description="Region name")
    country: str = Field("South Africa", description="Country")
    sector: str = Field("coal", description="Primary sector under transition")

    # ILO principles
    principle_scores: dict[str, float] = Field(
        default_factory=lambda: {
            "social_dialogue": 45.0,
            "skills_reskilling": 40.0,
            "social_protection": 55.0,
            "active_labour_market_policy": 35.0,
            "community_investment": 30.0,
        },
    )

    # EU JTF
    nuts2_code: str = Field("ZA00", description="NUTS2 or equivalent regional code")
    criteria_status: dict[str, bool] = Field(
        default_factory=lambda: {
            "territorial_jtp": True,
            "ghg_emission_dependency": True,
            "fossil_fuel_employment": True,
            "economic_diversification": False,
            "social_partnership_evidence": True,
            "green_jobs_target": False,
            "just_transition_monitoring": False,
            "cross_border_coordination": False,
        },
    )
    regional_gdp_m_eur: float = Field(12_000.0, ge=0.0)
    population_k: float = Field(4_500.0, gt=0)
    fossil_employment_k: float = Field(90.0, ge=0.0)
    total_employment_k: float = Field(1_200.0, gt=0)

    # Workforce
    fossil_workers_k: float = Field(90.0, gt=0)
    green_jobs_pipeline_k: float = Field(60.0, ge=0.0)
    avg_fossil_wage_usd: float = Field(35_000.0, gt=0)
    avg_green_wage_usd: float = Field(28_000.0, gt=0)
    reskilling_duration_months: float = Field(14.0, ge=1.0)
    reskilling_cost_per_worker_usd: float = Field(8_500.0, gt=0)
    phase_out_start_year: int = Field(2025)
    phase_out_end_year: int = Field(2040)
    jetp_pledge: bool = Field(False)

    # Community
    coal_profile_key: Optional[str] = Field(None)
    gdp_fossil_dependency_pct: float = Field(25.0, ge=0.0, le=100.0)
    infrastructure_score: float = Field(45.0, ge=0.0, le=100.0)
    alternative_employer_count: int = Field(3, ge=0)
    skills_transferability: float = Field(2.5, ge=1.0, le=5.0)
    social_cohesion_score: float = Field(50.0, ge=0.0, le=100.0)
    alternative_sector_score: float = Field(0.30, ge=0.0, le=1.0)

    # CIF
    project_cost_m: float = Field(100.0, gt=0)
    income_group: str = Field("lower_middle")
    has_national_climate_plan: bool = Field(True)
    forest_coverage_pct: float = Field(30.0, ge=0.0, le=100.0)
    grid_electrification_rate_pct: float = Field(50.0, ge=0.0, le=100.0)
    project_type: str = Field("renewable_energy")


# ---------------------------------------------------------------------------
# POST endpoints
# ---------------------------------------------------------------------------


@router.post("/assess", summary="Full just transition finance assessment (E89)")
async def full_assessment(request: FullAssessmentRequest) -> dict:
    """
    Orchestrates all E89 sub-assessments:
    ILO JT Principles + EU JTF Eligibility + Workforce Transition Modelling +
    Community Resilience + CIF Facility Eligibility.

    Returns:
    - just_transition_score (0-100)
    - transition_risk_tier
    - ilo_composite_score
    - eu_jtf_eligible
    - net_jobs_k
    - reskilling_cost_m_usd
    - community_resilience_score
    - cif_eligible_facilities
    """
    try:
        payload = request.model_dump()
        result = _engine.run_full_assessment(payload)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/ilo-principles", summary="ILO Just Transition Guiding Principles (2015) assessment")
async def ilo_principles(request: ILOPrinciplesRequest) -> dict:
    """
    Scores all 5 ILO Just Transition Guiding Principles.
    Computes weighted composite score and assigns tier:
    leading (≥80) / advanced (≥65) / developing (≥45) / early (<45).
    Identifies gaps by principle.
    """
    try:
        result = _engine.assess_ilo_principles(request.model_dump())
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post(
    "/eu-jtf-eligibility",
    summary="EU Just Transition Fund (JTF) eligibility assessment",
)
async def eu_jtf_eligibility(request: EUJTFEligibilityRequest) -> dict:
    """
    Checks 8 EU JTF eligibility criteria per JTF Regulation (EU) 2021/1056 Art 8.
    Calculates territorial just transition score and estimates JTF allocation (€M).
    """
    try:
        result = _engine.assess_eu_jtf_eligibility(request.model_dump())
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/workforce-transition", summary="Just transition workforce modelling")
async def workforce_transition(request: WorkforceTransitionRequest) -> dict:
    """
    Models the workforce transition: affected workers, green jobs created,
    net jobs impact, wage transition gap, reskilling costs, and timeline.
    Includes JETP concessional finance estimate.
    """
    try:
        result = _engine.model_workforce_transition(request.model_dump())
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/community-resilience", summary="Community resilience to fossil fuel transition")
async def community_resilience(request: CommunityResilienceRequest) -> dict:
    """
    Assesses community resilience: GDP fossil dependency, infrastructure quality,
    alternative employer diversity, skills transferability, social cohesion,
    and economic diversification potential.
    Returns vulnerability tier: resilient / moderate / vulnerable / highly_vulnerable.
    """
    try:
        result = _engine.assess_community_resilience(request.model_dump())
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/cif-eligibility", summary="Climate Investment Funds (CIF) facility eligibility")
async def cif_eligibility(request: CIFEligibilityRequest) -> dict:
    """
    Checks eligibility for all 4 CIF facilities:
    CTF (Clean Technology Fund), PPCR (Climate Resilience),
    FIP (Forest Investment), SREP (Renewable Energy in LICs).
    Returns total concessional finance available and blended finance ratio.
    """
    try:
        result = _engine.assess_cif_eligibility(request.model_dump())
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# GET reference endpoints
# ---------------------------------------------------------------------------


@router.get("/ref/ilo-principles", summary="Reference: ILO Just Transition Guiding Principles")
async def ref_ilo_principles() -> dict:
    """
    Returns all 5 ILO Just Transition Guiding Principles (2015) with:
    weights, sub-criteria, ILO reference paragraphs, and descriptions.
    """
    return {
        "ilo_jt_principles": ILO_JT_PRINCIPLES,
        "count": len(ILO_JT_PRINCIPLES),
        "source": "ILO Guidelines for a Just Transition 2015 (ILO JT Guidelines)",
    }


@router.get(
    "/ref/coal-community-profiles",
    summary="Reference: coal-dependent community profiles",
)
async def ref_coal_community_profiles() -> dict:
    """
    Returns 20 coal-dependent regional profiles across UK, Germany, Poland,
    Czech Republic, Romania, Bulgaria, Spain, Australia, South Africa, India,
    China, USA, Colombia, and Indonesia.
    Each profile includes coal employment, phase-out target, alternative sector
    score, and transition fund availability.
    """
    return {
        "coal_community_profiles": COAL_COMMUNITY_PROFILES,
        "count": len(COAL_COMMUNITY_PROFILES),
        "source": "IEA Coal in Net Zero Transitions (2021) / World Bank JT Framework 2022",
    }


@router.get("/ref/sector-profiles", summary="Reference: just transition sector profiles")
async def ref_sector_profiles() -> dict:
    """
    Returns 8 high-transition-risk sector profiles:
    coal, oil_gas, steel, cement, automotive, aviation, shipping, agriculture.
    Each includes fossil/green employment figures, skills transferability,
    wage gap, transition timeline, and key transition risks.
    """
    return {
        "sector_profiles": JUST_TRANSITION_SECTOR_PROFILES,
        "count": len(JUST_TRANSITION_SECTOR_PROFILES),
        "source": "ILO World Employment and Social Outlook 2023 / IRENA World Energy Transitions Outlook 2023",
    }


@router.get("/ref/cif-facilities", summary="Reference: Climate Investment Funds facility profiles")
async def ref_cif_facilities() -> dict:
    """
    Returns all 4 CIF facility profiles (CTF, PPCR, FIP, SREP) with:
    focus areas, eligible countries, minimum project size, grant element %,
    and concessional rate.
    """
    # Exclude internal rates from public ref to avoid confusion
    public_profiles = {
        k: {
            "full_name": v["full_name"],
            "focus": v["focus"],
            "eligible_countries": v["eligible_countries"],
            "min_project_m": v["min_project_m"],
            "grant_element_pct": v["grant_element_pct"],
            "focus_areas": v["focus_areas"],
        }
        for k, v in CIF_FACILITY_PROFILES.items()
    }
    return {
        "cif_facilities": public_profiles,
        "count": len(public_profiles),
        "source": "Climate Investment Funds (CIF) — climateinvestmentfunds.org",
    }
