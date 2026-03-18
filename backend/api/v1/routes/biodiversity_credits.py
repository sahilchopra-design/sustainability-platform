"""
API Routes — Biodiversity Credits & Nature Markets Engine (E88)
================================================================
POST /api/v1/biodiversity-credits/assess
POST /api/v1/biodiversity-credits/bng-metric
POST /api/v1/biodiversity-credits/tnfd-disclosure
POST /api/v1/biodiversity-credits/ecosystem-services
POST /api/v1/biodiversity-credits/gbf-target15
POST /api/v1/biodiversity-credits/credit-quality
GET  /api/v1/biodiversity-credits/ref/credit-standards
GET  /api/v1/biodiversity-credits/ref/habitat-tiers
GET  /api/v1/biodiversity-credits/ref/ecosystem-services
GET  /api/v1/biodiversity-credits/ref/price-benchmarks
"""
from typing import Any, Optional, List, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.biodiversity_credit_engine import (
    BiodiversityCreditEngine,
    BIODIVERSITY_CREDIT_STANDARDS,
    HABITAT_DISTINCTIVENESS_TIERS,
    ECOSYSTEM_SERVICE_VALUATION,
    GBF_TARGET_15_REQUIREMENTS,
    NATURE_MARKET_PRICE_BENCHMARKS,
)

router = APIRouter(
    prefix="/api/v1/biodiversity-credits",
    tags=["biodiversity_credits"],
)

_engine = BiodiversityCreditEngine()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class BNGMetricRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    project_id: str = Field("PROJECT_001", description="Project identifier")
    habitat_type: str = Field("grassland", description="Primary habitat type")
    pre_condition: str = Field(
        "poor",
        description="Pre-intervention habitat condition (poor/moderate/good/excellent)",
    )
    post_condition: str = Field(
        "good",
        description="Post-intervention habitat condition (poor/moderate/good/excellent)",
    )
    area_ha: float = Field(10.0, gt=0, description="Project area in hectares")
    distinctiveness_tier: str = Field(
        "medium_distinctiveness",
        description=(
            "DEFRA habitat distinctiveness tier: high_distinctiveness, medium_distinctiveness, "
            "low_distinctiveness, very_low_distinctiveness, degraded, post_industrial"
        ),
    )
    strategic_significance: float = Field(
        1.15,
        ge=1.0,
        le=1.5,
        description="Strategic significance multiplier (1.0 baseline, up to 1.5 for connectivity)",
    )
    offsite_distance_km: float = Field(
        0.0,
        ge=0.0,
        description="Distance in km for offsite credits (0 = onsite)",
    )
    legal_agreement_years: int = Field(
        30,
        ge=1,
        le=125,
        description="Duration of legal agreement securing habitat management (years)",
    )
    irreplaceability_flag: bool = Field(
        False,
        description="True if habitat is identified as irreplaceable (e.g. ancient woodland)",
    )


class TNFDDisclosureRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str = Field("ENTITY_001", description="Entity identifier")
    sector: str = Field("financial_services", description="Primary business sector")
    country: str = Field("United Kingdom", description="Country of primary operations")
    pillar_scores: dict[str, float] = Field(
        default_factory=lambda: {
            "governance": 55.0,
            "strategy": 40.0,
            "risk_management": 45.0,
            "metrics_targets": 30.0,
        },
        description="TNFD pillar scores (0-100) for each of the 4 pillars",
    )
    has_location_data: bool = Field(
        False,
        description="Entity has geo-referenced location data for its operations / supply chain",
    )
    has_scenario_analysis: bool = Field(
        False,
        description="Entity has conducted nature-related scenario analysis",
    )
    sbtn_aligned: bool = Field(
        False,
        description="Entity has set Science-Based Targets for Nature (SBTN)",
    )
    gbf_aligned: bool = Field(
        False,
        description="Entity has disclosed against Kunming-Montreal GBF Target 15",
    )
    leap_stage_reached: str = Field(
        "L",
        description="Highest TNFD LEAP stage completed: L (Locate), E (Evaluate), A (Assess), P (Prepare)",
    )


class EcosystemServicesRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    project_id: str = Field("PROJECT_001", description="Project identifier")
    area_ha: float = Field(100.0, gt=0, description="Project area in hectares")
    ecosystem_type: str = Field("grassland", description="Primary ecosystem type")
    service_quantities: dict[str, float] = Field(
        default_factory=dict,
        description=(
            "Quantities per hectare per year for each ecosystem service. "
            "Keys: carbon_sequestration, water_purification, flood_regulation, pollination, "
            "soil_formation, nutrient_cycling, climate_regulation, biodiversity_habitat, "
            "coastal_protection, recreation, food_provision, timber_provision"
        ),
    )
    use_high_estimate: bool = Field(
        False,
        description="Use high-end valuation estimates (True) or conservative low-end (False)",
    )


class GBFTarget15Request(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str = Field("ENTITY_001", description="Entity identifier")
    sector: str = Field("financial_services", description="Primary business sector")
    revenue_usd_m: float = Field(
        500.0,
        ge=0.0,
        description="Annual revenue in USD millions (for materiality determination)",
    )
    sub_target_status: dict[str, float] = Field(
        default_factory=lambda: {
            "a": 30.0,
            "b": 20.0,
            "c": 15.0,
            "d": 25.0,
            "e": 10.0,
            "f": 20.0,
        },
        description="Completion percentage (0-100) for each GBF Target 15 sub-target (a-f)",
    )
    has_tnfd_disclosure: bool = Field(
        False,
        description="Entity publishes TNFD-aligned disclosures",
    )
    has_csrd_esrs_e4: bool = Field(
        False,
        description="Entity reports against CSRD ESRS E4 (Biodiversity and Ecosystems)",
    )
    has_gri_304: bool = Field(
        False,
        description="Entity reports against GRI 304 (Biodiversity Standard)",
    )
    peer_sector_avg_score: float = Field(
        42.0,
        ge=0.0,
        le=100.0,
        description="Average GBF T15 score for peers in the same sector (for benchmarking)",
    )


class CreditQualityRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    credit_id: str = Field("CREDIT_001", description="Credit identifier")
    standard: str = Field(
        "Verra_VM0033",
        description=(
            "Biodiversity credit standard: Verra_VM0033, Plan_Vivo, BNG_DEFRA_Metric_4, "
            "TNFD_v1, Gold_Standard_Nature, ART_TREES"
        ),
    )
    credit_type: str = Field(
        "REDD_plus_biodiversity",
        description=(
            "Market credit type for price benchmarking: BNG_habitat_unit, "
            "biodiversity_unit_verra, REDD_plus_biodiversity, blue_carbon_mangrove, "
            "seagrass_unit, rewilding_unit, species_recovery, wetland_credit"
        ),
    )
    project_country: str = Field("Brazil", description="Project host country")
    permanence_years: int = Field(
        30,
        ge=1,
        description="Number of years for which permanence is guaranteed",
    )
    has_additionality_demonstration: bool = Field(
        True,
        description="Project has documented additionality demonstration",
    )
    reversal_buffer_pct: float = Field(
        10.0,
        ge=0.0,
        le=100.0,
        description="Percentage of credits held in reversal/buffer pool",
    )
    risk_factors: list[str] = Field(
        default_factory=list,
        description=(
            "Active permanence risk factors: wildfire, pest_disease, drought, flooding, "
            "political_instability, land_tenure_insecurity, funding_dependency, governance_weakness"
        ),
    )
    asking_price_usd: float = Field(
        20.0,
        gt=0,
        description="Asking price per credit in USD",
    )
    co_benefits: list[str] = Field(
        default_factory=list,
        description="Co-benefits claimed (e.g. carbon_sequestration, community_livelihoods)",
    )


class FullAssessmentRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str = Field("ENTITY_001", description="Entity identifier")
    sector: str = Field("financial_services", description="Sector")
    country: str = Field("United Kingdom", description="Primary country of operations")
    revenue_usd_m: float = Field(500.0, ge=0.0, description="Annual revenue USD millions")

    # Nested sub-request data
    project_data: Optional[dict[str, Any]] = Field(
        None,
        description="Project data for BNG Metric and Ecosystem Services sub-assessments",
    )
    credit_data: Optional[dict[str, Any]] = Field(
        None,
        description="Credit data for Credit Quality sub-assessment",
    )

    # TNFD fields
    pillar_scores: dict[str, float] = Field(
        default_factory=lambda: {
            "governance": 55.0,
            "strategy": 40.0,
            "risk_management": 45.0,
            "metrics_targets": 30.0,
        },
    )
    has_location_data: bool = Field(False)
    has_scenario_analysis: bool = Field(False)
    sbtn_aligned: bool = Field(False)
    gbf_aligned: bool = Field(False)
    leap_stage_reached: str = Field("L")

    # GBF Target 15 fields
    sub_target_status: dict[str, float] = Field(
        default_factory=lambda: {
            "a": 30.0, "b": 20.0, "c": 15.0, "d": 25.0, "e": 10.0, "f": 20.0,
        },
    )
    has_tnfd_disclosure: bool = Field(False)
    has_csrd_esrs_e4: bool = Field(False)
    has_gri_304: bool = Field(False)
    peer_sector_avg_score: float = Field(42.0, ge=0.0, le=100.0)


# ---------------------------------------------------------------------------
# POST endpoints
# ---------------------------------------------------------------------------


@router.post("/assess", summary="Full biodiversity credits & nature markets assessment (E88)")
async def full_assessment(request: FullAssessmentRequest) -> dict:
    """
    Orchestrates all E88 sub-assessments:
    BNG Metric 4.0 + TNFD LEAP + Ecosystem Service Valuation +
    GBF Target 15 + Credit Quality.

    Returns:
    - biodiversity_credit_score (0-100)
    - credit_quality_tier (A/B/C/D)
    - total_ecosystem_value_m (USD millions)
    - biodiversity_net_gain_pct
    - tnfd_composite_score
    - gbf_t15_disclosure_score
    """
    try:
        payload = request.model_dump()
        result = _engine.run_full_assessment(payload)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/bng-metric", summary="DEFRA BNG Metric 4.0 habitat unit calculation")
async def bng_metric(request: BNGMetricRequest) -> dict:
    """
    Calculates pre/post habitat units per DEFRA Biodiversity Metric 4.0.
    Checks 10% mandatory net gain compliance and estimates saleable credits.
    """
    try:
        result = _engine.assess_bng_metric(request.model_dump())
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/tnfd-disclosure", summary="TNFD v1.0 LEAP process disclosure assessment")
async def tnfd_disclosure(request: TNFDDisclosureRequest) -> dict:
    """
    Scores TNFD v1.0 LEAP process across 4 pillars and 14 core metrics.
    Identifies disclosure gaps and assigns disclosure tier
    (advanced / progressing / developing / early_stage).
    """
    try:
        result = _engine.assess_tnfd_disclosure(request.model_dump())
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/ecosystem-services", summary="TEEB/SEEA ecosystem service valuation")
async def ecosystem_services(request: EcosystemServicesRequest) -> dict:
    """
    Values all 12 ecosystem service categories using TEEB / SEEA-EA methodology.
    Returns total economic value (TEV), ENCORE category breakdown,
    key dependencies and dominant service type.
    """
    try:
        result = _engine.value_ecosystem_services(request.model_dump())
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/gbf-target15", summary="Kunming-Montreal GBF Target 15 disclosure assessment")
async def gbf_target15(request: GBFTarget15Request) -> dict:
    """
    Assesses compliance with all 6 GBF Target 15 sub-targets (a-f).
    Produces completeness score, gap list, and peer sector comparison.
    """
    try:
        result = _engine.assess_gbf_target15(request.model_dump())
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/credit-quality", summary="Biodiversity credit quality assessment")
async def credit_quality(request: CreditQualityRequest) -> dict:
    """
    Assesses biodiversity credit quality:
    additionality, permanence risk, reversal buffer, CORSIA eligibility,
    and price benchmarking vs nature market benchmarks.
    Returns quality tier A-D.
    """
    try:
        result = _engine.assess_credit_quality(request.model_dump())
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# GET reference endpoints
# ---------------------------------------------------------------------------


@router.get("/ref/credit-standards", summary="Reference: biodiversity credit standards")
async def ref_credit_standards() -> dict:
    """
    Returns all 6 biodiversity credit standards with methodology basis,
    accepted jurisdictions, permanence requirements, and co-benefits.
    """
    return {
        "credit_standards": BIODIVERSITY_CREDIT_STANDARDS,
        "count": len(BIODIVERSITY_CREDIT_STANDARDS),
        "source": "Verra VM0033 | Plan Vivo 2013 | DEFRA BNG Metric 4.0 | TNFD v1.0 | Gold Standard Nature | ART TREES v2.0",
    }


@router.get("/ref/habitat-tiers", summary="Reference: DEFRA habitat distinctiveness tiers")
async def ref_habitat_tiers() -> dict:
    """
    Returns all 6 DEFRA habitat distinctiveness tiers with score ranges,
    descriptions, BNG multipliers, and habitat examples.
    """
    return {
        "habitat_distinctiveness_tiers": HABITAT_DISTINCTIVENESS_TIERS,
        "count": len(HABITAT_DISTINCTIVENESS_TIERS),
        "source": "DEFRA Biodiversity Metric 4.0 (Feb 2023) / Environment Act 2021",
    }


@router.get("/ref/ecosystem-services", summary="Reference: ecosystem service valuation benchmarks")
async def ref_ecosystem_services() -> dict:
    """
    Returns all 12 ecosystem service categories with units, price ranges
    (low/high USD per unit), and valuation methodology references.
    """
    return {
        "ecosystem_services": ECOSYSTEM_SERVICE_VALUATION,
        "count": len(ECOSYSTEM_SERVICE_VALUATION),
        "source": "TEEB (2010) / SEEA-EA (UN 2021) / IPBES Pollination Assessment 2016",
    }


@router.get("/ref/price-benchmarks", summary="Reference: nature market credit price benchmarks")
async def ref_price_benchmarks() -> dict:
    """
    Returns market price benchmarks for all 8 biodiversity credit types:
    BNG habitat unit, Verra biodiversity unit, REDD+ biodiversity,
    blue carbon mangrove, seagrass, rewilding, species recovery, wetland credit.
    Includes price range, liquidity score, key buyers, and market trend.
    """
    return {
        "price_benchmarks": NATURE_MARKET_PRICE_BENCHMARKS,
        "count": len(NATURE_MARKET_PRICE_BENCHMARKS),
        "source": "Ecosystem Marketplace (2023) / BCA Biodiversity Credit Alliance / ICROA",
    }
