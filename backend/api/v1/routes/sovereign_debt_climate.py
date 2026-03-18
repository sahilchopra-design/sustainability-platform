from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any

from services.sovereign_debt_climate_engine import (
    assess_crdc_eligibility,
    assess_debt_for_nature,
    assess_imf_rst,
    assess_sids_vulnerability,
    aggregate_sovereign_climate_portfolio,
    SIDS_LIST,
    CRDC_TRIGGER_TYPES,
    IMF_RST_ELIGIBILITY,
    PARIS_CLUB_CATEGORIES,
    DFN_SWAP_FRAMEWORKS,
)

router = APIRouter(prefix="/api/v1/sovereign-debt-climate", tags=["Climate-Linked Sovereign Debt — E69"])

# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class CRDCRequest(BaseModel):
    country_iso: str
    country_name: Optional[str] = None
    is_sids: Optional[bool] = False
    is_ldc: Optional[bool] = False
    debt_amount_usd: Optional[float] = None
    trigger_type: Optional[str] = "cyclone_wind_speed"
    trigger_threshold: Optional[float] = None


class DebtForNatureRequest(BaseModel):
    country_iso: str
    country_name: Optional[str] = None
    total_eligible_debt_usd: Optional[float] = None
    swap_framework: Optional[str] = "multilateral"
    conservation_area_target_ha: Optional[float] = None


class IMFRSTRequest(BaseModel):
    country_iso: str
    imf_quota_usd: Optional[float] = None


class SIDSVulnerabilityRequest(BaseModel):
    country_iso: str


class SovereignPortfolioRequest(BaseModel):
    portfolio_id: Optional[str] = "default"
    holdings: List[Dict[str, Any]] = Field(default_factory=list)
    total_aum_usd: Optional[float] = None


# ---------------------------------------------------------------------------
# POST Endpoints
# ---------------------------------------------------------------------------

@router.post("/crdc-assessment")
async def crdc_assessment_endpoint(request: CRDCRequest) -> Dict[str, Any]:
    """Assess Climate Resilience Debt Clause eligibility, trigger design, and deferred amount."""
    try:
        country_data = {
            "country_iso": request.country_iso,
            "country_name": request.country_name,
            "is_sids": request.is_sids,
            "is_ldc": request.is_ldc,
        }
        debt_terms = {
            "debt_amount_usd": request.debt_amount_usd,
            "trigger_type": request.trigger_type,
            "trigger_threshold": request.trigger_threshold,
        }
        result = assess_crdc_eligibility(country_data, debt_terms)
        return {
            "status": "success",
            "country_iso": result.country_iso,
            "country_name": result.country_name,
            "crdc_eligible": result.crdc_eligible,
            "debt_amount_usd": result.debt_amount_usd,
            "trigger_type": result.trigger_type,
            "trigger_threshold": result.trigger_threshold,
            "trigger_probability_pct": result.trigger_probability_pct,
            "climate_event_return_period_years": result.climate_event_return_period_years,
            "deferred_amount_usd": result.deferred_amount_usd,
            "deferred_period_months": result.deferred_period_months,
            "basis_risk_rating": result.basis_risk_rating,
            "debt_relief_score": result.debt_relief_score,
            "implementation_cost_usd": result.implementation_cost_usd,
            "recommendations": result.recommendations,
            "standard": "Commonwealth Secretariat CRDC Model Clauses 2022",
            "trigger_reference": CRDC_TRIGGER_TYPES.get(result.trigger_type, {}),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/debt-for-nature")
async def debt_for_nature_endpoint(request: DebtForNatureRequest) -> Dict[str, Any]:
    """Design and assess a Debt-for-Nature swap transaction."""
    try:
        country_data = {
            "country_iso": request.country_iso,
            "country_name": request.country_name,
        }
        deal_terms = {
            "total_eligible_debt_usd": request.total_eligible_debt_usd,
            "swap_framework": request.swap_framework,
        }
        result = assess_debt_for_nature(country_data, deal_terms)
        return {
            "status": "success",
            "country_iso": result.country_iso,
            "country_name": result.country_name,
            "total_debt_usd": result.total_debt_usd,
            "swap_framework": result.swap_framework,
            "swap_amount_usd": result.swap_amount_usd,
            "discount_pct": result.discount_pct,
            "net_debt_reduction_usd": result.net_debt_reduction_usd,
            "conservation_fund_usd": result.conservation_fund_usd,
            "conservation_commitment": result.conservation_commitment_text,
            "co2_sequestration_tco2_yr": result.co2_sequestration_tco2_yr,
            "carbon_credit_revenue_usd_yr": result.carbon_credit_revenue_usd_yr,
            "mdb_guarantee_usd": result.mdb_guarantee_usd,
            "biodiversity_targets": result.biodiversity_targets,
            "imf_rst_linkage": result.imf_rst_linkage,
            "framework_details": DFN_SWAP_FRAMEWORKS.get(result.swap_framework, {}),
            "references": ["IMF World Bank DfN Framework 2023", "TNC Ocean Finance Programme"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/imf-rst")
async def imf_rst_endpoint(request: IMFRSTRequest) -> Dict[str, Any]:
    """Assess IMF Resilience and Sustainability Trust access score and reform requirements."""
    try:
        result = assess_imf_rst({"country_iso": request.country_iso, "imf_quota_usd": request.imf_quota_usd})
        return {
            "status": "success",
            "country_iso": request.country_iso,
            "rst_eligible": result.rst_eligible,
            "access_limit_pct_quota": result.access_limit_pct_quota,
            "reform_area": result.reform_area,
            "resilience_score": result.resilience_score,
            "indicative_drawing_usd": result.indicative_drawing_usd,
            "conditionality_met": result.conditionality_met,
            "disbursement_timeline": result.disbursement_timeline,
            "reform_measures": result.reform_measures,
            "standard": "IMF RST Instrument Design Document 2022",
            "note": "RST draws must be linked to resilience and sustainability reforms (LOI required)",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sids-vulnerability")
async def sids_vulnerability_endpoint(request: SIDSVulnerabilityRequest) -> Dict[str, Any]:
    """Assess SIDS composite vulnerability and CDPC eligibility."""
    try:
        result = assess_sids_vulnerability(request.country_iso)
        return {
            "status": "success",
            "country_iso": result.country_iso,
            "country_name": result.country_name,
            "vulnerability_score": result.vulnerability_score,
            "vulnerability_tier": result.vulnerability_tier,
            "component_scores": {
                "inform_component": result.inform_component,
                "nd_gain_component": result.nd_gain_component,
                "fiscal_resilience_component": result.fiscal_resilience_component,
            },
            "cdpc_eligible": result.cdpc_eligible,
            "cdpc_deferred_pct": result.cdpc_deferred_pct,
            "paris_club_category": result.paris_club_category,
            "climate_debt_relief_score": result.climate_debt_relief_score,
            "priority_interventions": result.priority_interventions,
            "standard": "UN-OHRLLS SIDS Vulnerability Index / INFORM Risk Index",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sovereign-portfolio")
async def sovereign_portfolio_endpoint(request: SovereignPortfolioRequest) -> Dict[str, Any]:
    """Aggregate climate-linked sovereign debt metrics across a portfolio of holdings."""
    try:
        result = aggregate_sovereign_climate_portfolio(request.holdings)
        return {
            "status": "success",
            "portfolio_id": result.portfolio_id,
            "total_sovereign_exposure_usd": result.total_sovereign_exposure_usd,
            "climate_adjusted_exposure_usd": result.climate_adjusted_exposure_usd,
            "weighted_vulnerability_score": result.weighted_vulnerability_score,
            "weighted_debt_relief_score": result.weighted_debt_relief_score,
            "crdc_eligible_exposure_usd": result.crdc_eligible_exposure_usd,
            "dfn_eligible_exposure_usd": result.dfn_eligible_exposure_usd,
            "sids_exposure_pct": result.sids_exposure_pct,
            "high_risk_country_concentration": result.high_risk_country_concentration,
            "portfolio_climate_var_usd": result.portfolio_climate_var_usd,
            "recommendations": result.recommendations,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# GET Reference Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/sids-list")
async def ref_sids_list() -> Dict[str, Any]:
    """Complete SIDS reference list with vulnerability scores and GDP."""
    return {
        "sids": SIDS_LIST,
        "total_sids": len(SIDS_LIST),
        "source": "UN-OHRLLS Official SIDS List + INFORM 2024",
        "regions": ["Caribbean", "Pacific", "Indian Ocean", "Atlantic"],
        "note": "Vulnerability scores are composite (INFORM + ND-GAIN + fiscal resilience)",
    }


@router.get("/ref/crdc-triggers")
async def ref_crdc_triggers() -> Dict[str, Any]:
    """Climate Resilience Debt Clause trigger types and design parameters."""
    return {
        "trigger_types": CRDC_TRIGGER_TYPES,
        "total_triggers": len(CRDC_TRIGGER_TYPES),
        "standard": "Commonwealth Secretariat CRDC Model Clauses 2022",
        "precedents": [
            "Barbados 2022 (bilateral creditors)",
            "Grenada 2015 (hurricane clause)",
            "Bahamas proposed (World Bank)",
        ],
    }


@router.get("/ref/imf-rst-eligible")
async def ref_imf_rst_eligible() -> Dict[str, Any]:
    """Countries eligible for IMF Resilience and Sustainability Trust."""
    return {
        "eligible_countries": IMF_RST_ELIGIBILITY,
        "total_eligible": len(IMF_RST_ELIGIBILITY),
        "access_limit_pct_quota": 150,
        "standard": "IMF RST Instrument Design Document 2022",
        "rst_total_capacity_bn_sdr": 45,
        "note": "Eligibility requires concurrent IMF-supported programme or PCI",
    }


@router.get("/ref/paris-club")
async def ref_paris_club() -> Dict[str, Any]:
    """Paris Club debtor categories and climate MOU treatment."""
    return {
        "categories": PARIS_CLUB_CATEGORIES,
        "climate_mou": "Paris Club MOU on Climate Change and Debt Treatment 2021",
        "g7_commitment": "Incorporate climate conditionality into debt restructurings by 2025",
        "cdpc_adoption_target_pct": 100,
        "note": "Climate conditions aligned with NDC update and Paris Agreement Article 9",
    }


@router.get("/ref/dfn-frameworks")
async def ref_dfn_frameworks() -> Dict[str, Any]:
    """Debt-for-Nature swap framework types with precedent transactions."""
    return {
        "frameworks": DFN_SWAP_FRAMEWORKS,
        "total_frameworks": len(DFN_SWAP_FRAMEWORKS),
        "largest_deal_to_date": "Ecuador 2023 — USD 1.6bn Galapagos blue bond",
        "total_dfn_market_2023_bn_usd": 8.5,
        "key_actors": ["TNC", "World Bank", "IMF", "IADB", "Regional Development Banks"],
        "carbon_credit_standards": ["Verra VCS", "Gold Standard", "Plan Vivo"],
    }
