"""
CDR Routes — IPCC / BeZero / Oxford / VCMI / Article 6.4
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from services.cdr_engine import CDREngine

router = APIRouter(prefix="/api/v1/cdr", tags=["cdr"])
engine = CDREngine()


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class CDRQualityRequest(BaseModel):
    entity_id: str = Field(..., description="Project / entity identifier")
    cdr_method: str = Field("afforestation", description="CDR method key")
    annual_removal_tco2: float = Field(10000.0, gt=0, description="Annual CO2 removal (tonnes)")
    permanence_yrs: int = Field(100, gt=0, description="Claimed permanence (years)")
    verification_standard: str = Field("gold_standard", description="Verification standard key")
    additionality_score: float = Field(75.0, ge=0.0, le=100.0, description="Additionality quality score (0-100)")
    leakage_risk_pct: float = Field(5.0, ge=0.0, le=100.0, description="Estimated leakage risk (%)")


class LCORRequest(BaseModel):
    entity_id: str = Field(..., description="Project identifier")
    cdr_method: str = Field("daccs", description="CDR method key")
    capacity_tco2_pa: float = Field(50000.0, gt=0, description="Annual removal capacity (tCO2)")
    capex_usd: float = Field(200e6, gt=0, description="Total CAPEX (USD)")
    opex_usd_pa: float = Field(8e6, gt=0, description="Annual OPEX (USD)")
    lifetime_yrs: int = Field(20, ge=5, le=50, description="Project lifetime (years)")
    discount_rate_pct: float = Field(8.0, ge=0.0, le=30.0, description="Discount rate (%)")


class OxfordPrinciplesRequest(BaseModel):
    entity_id: str = Field(..., description="Entity identifier")
    cdr_method: str = Field("enhanced_weathering", description="CDR method key")
    avoidance_residual: float = Field(5.0, ge=0.0, le=100.0, description="Offset % of total emissions")
    preference_durable: bool = Field(True, description="Preference for durable removals in portfolio")
    shift_to_durable_plan: bool = Field(True, description="Documented plan to shift to durable removals over time")
    avoid_locking_in_emissions: bool = Field(True, description="No EOR-linked or lock-in credits used")


class Article64Request(BaseModel):
    entity_id: str = Field(..., description="Entity identifier")
    cdr_method: str = Field("afforestation", description="CDR method key")
    host_country_code: str = Field("KE", description="ISO 2-letter host country code")
    host_country_authorised: bool = Field(True, description="Host country has formally authorised A6.4ER")
    corresponding_adjustment_agreed: bool = Field(True, description="Corresponding adjustment agreed with host NDC")
    sustainable_dev_safeguards: bool = Field(True, description="Sustainable development safeguards in place")


class VCMIClaimsRequest(BaseModel):
    entity_id: str = Field(..., description="Entity identifier")
    scope1_sbti_aligned: bool = Field(True, description="Scope 1 emissions SBTi-aligned")
    scope2_sbti_aligned: bool = Field(True, description="Scope 2 emissions SBTi-aligned")
    scope3_disclosure: bool = Field(True, description="Scope 3 emissions publicly disclosed")
    residual_emissions_tco2: float = Field(50000.0, gt=0, description="Residual emissions after abatement (tCO2)")
    cdr_credits_tco2: float = Field(55000.0, gt=0, description="CDR credits purchased (tCO2)")
    credit_quality_score: float = Field(72.0, ge=0.0, le=100.0, description="Weighted quality score of credits (0-100)")


class CDRProjectItem(BaseModel):
    project_id: str = Field(..., description="Individual project identifier")
    cdr_method: str = Field("afforestation")
    annual_removal_tco2: float = Field(5000.0, gt=0)
    quality_score: Optional[float] = None
    verification_standard: str = Field("gold_standard")
    additionality_score: Optional[float] = None
    leakage_risk_pct: Optional[float] = None


class PortfolioRequest(BaseModel):
    entity_id: str = Field(..., description="Portfolio owner identifier")
    projects: List[CDRProjectItem] = Field(..., min_items=1, description="List of CDR projects")


# ---------------------------------------------------------------------------
# POST Endpoints
# ---------------------------------------------------------------------------

@router.post("/quality-assessment", summary="CDR Quality Assessment (BeZero-style Rating)")
async def quality_assessment(req: CDRQualityRequest):
    try:
        result = engine.assess_cdr_quality(
            entity_id=req.entity_id,
            cdr_method=req.cdr_method,
            annual_removal_tco2=req.annual_removal_tco2,
            permanence_yrs=req.permanence_yrs,
            verification_standard=req.verification_standard,
            additionality_score=req.additionality_score,
            leakage_risk_pct=req.leakage_risk_pct,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/lcor", summary="Levelised Cost of Removal (LCOR) Calculation")
async def lcor(req: LCORRequest):
    try:
        result = engine.calculate_lcor(
            entity_id=req.entity_id,
            cdr_method=req.cdr_method,
            capacity_tco2_pa=req.capacity_tco2_pa,
            capex_usd=req.capex_usd,
            opex_usd_pa=req.opex_usd_pa,
            lifetime_yrs=req.lifetime_yrs,
            discount_rate_pct=req.discount_rate_pct,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/oxford-principles", summary="Oxford Principles Net Zero Alignment Assessment")
async def oxford_principles(req: OxfordPrinciplesRequest):
    try:
        result = engine.assess_oxford_principles(
            entity_id=req.entity_id,
            cdr_method=req.cdr_method,
            avoidance_residual=req.avoidance_residual,
            preference_durable=req.preference_durable,
            shift_to_durable_plan=req.shift_to_durable_plan,
            avoid_locking_in_emissions=req.avoid_locking_in_emissions,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/article-6-4", summary="Article 6.4 Paris Agreement Mechanism Eligibility")
async def article_6_4(req: Article64Request):
    try:
        result = engine.assess_article_6_4(
            entity_id=req.entity_id,
            cdr_method=req.cdr_method,
            host_country_code=req.host_country_code,
            host_country_authorised=req.host_country_authorised,
            corresponding_adjustment_agreed=req.corresponding_adjustment_agreed,
            sustainable_dev_safeguards=req.sustainable_dev_safeguards,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vcmi-claims", summary="VCMI Claims Code Assessment (Silver / Gold / Platinum)")
async def vcmi_claims(req: VCMIClaimsRequest):
    try:
        result = engine.assess_vcmi_claims(
            entity_id=req.entity_id,
            scope1_sbti_aligned=req.scope1_sbti_aligned,
            scope2_sbti_aligned=req.scope2_sbti_aligned,
            scope3_disclosure=req.scope3_disclosure,
            residual_emissions_tco2=req.residual_emissions_tco2,
            cdr_credits_tco2=req.cdr_credits_tco2,
            credit_quality_score=req.credit_quality_score,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portfolio", summary="CDR Portfolio Assessment")
async def portfolio(req: PortfolioRequest):
    try:
        projects_dicts = [p.dict() for p in req.projects]
        result = engine.assess_portfolio(entity_id=req.entity_id, projects=projects_dicts)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# GET Reference Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/cdr-methods", summary="Reference: CDR Methods Taxonomy (IPCC AR6)")
def ref_cdr_methods():
    from services.cdr_engine import CDR_METHODS, BEZERO_RATING_THRESHOLDS
    return {
        "cdr_methods": CDR_METHODS,
        "bezero_rating_thresholds": BEZERO_RATING_THRESHOLDS,
        "source": "IPCC AR6 Working Group III Chapter 12; BeZero Carbon Rating Methodology",
    }


@router.get("/ref/verification-standards", summary="Reference: CDR Verification Standards")
def ref_verification_standards():
    from services.cdr_engine import VERIFICATION_STANDARDS, ARTICLE_6_4_CRITERIA
    return {
        "verification_standards": VERIFICATION_STANDARDS,
        "article_6_4_criteria": ARTICLE_6_4_CRITERIA,
        "source": "Puro.earth CORC Standard; Isometric VSS; Gold Standard GS4GG; Verra VCS; Article 6.4 Decision 3/CMA.3",
    }


@router.get("/ref/oxford-principles", summary="Reference: Oxford Principles & VCMI Claims Levels")
def ref_oxford_principles():
    from services.cdr_engine import OXFORD_PRINCIPLES, VCMI_CLAIMS_LEVELS
    return {
        "oxford_principles": OXFORD_PRINCIPLES,
        "vcmi_claims_levels": VCMI_CLAIMS_LEVELS,
        "source": "Oxford Principles for Net Zero Aligned Carbon Offsetting 2024; VCMI Claims Code of Practice 2023",
    }
