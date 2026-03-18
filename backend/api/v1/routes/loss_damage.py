from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any

from services.loss_damage_engine import (
    calculate_frld_eligibility,
    design_parametric_trigger,
    assess_wim_access,
    calculate_residual_ld_gap,
    aggregate_ld_portfolio,
    V20_MEMBERS,
    FRLD_ACCESS_CRITERIA,
    GLOBAL_SHIELD_PILLARS,
    PARAMETRIC_TRIGGERS,
    LOSS_EVENT_TYPES,
)

router = APIRouter(prefix="/api/v1/loss-damage", tags=["Loss & Damage Finance — E70"])

# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class FRLDEligibilityRequest(BaseModel):
    country_iso: str
    country_name: Optional[str] = None
    is_sids: Optional[bool] = False
    is_ldc: Optional[bool] = False
    nd_gain_score: Optional[float] = None
    gdp_usd: Optional[float] = None
    event_type: Optional[str] = "flood"


class ParametricDesignRequest(BaseModel):
    trigger_id: str
    trigger_index: Optional[str] = "wind_speed_kmh"
    attachment_point: Optional[float] = None
    exhaustion_point: Optional[float] = None
    max_payout_usd: Optional[float] = None
    payout_structure: Optional[str] = "linear"


class WIMAccessRequest(BaseModel):
    country_iso: str
    is_ldc: Optional[bool] = False
    is_sids: Optional[bool] = False


class LDGapRequest(BaseModel):
    country_iso: str
    country_name: Optional[str] = None
    event_type: Optional[str] = "cyclone"
    gdp_usd: Optional[float] = None
    insurance_penetration: Optional[float] = None
    global_shield_covered: Optional[bool] = None


class LDPortfolioRequest(BaseModel):
    portfolio_id: Optional[str] = "default"
    total_aum_usd: Optional[float] = None
    holdings: Optional[List[Dict[str, Any]]] = None


# ---------------------------------------------------------------------------
# POST Endpoints
# ---------------------------------------------------------------------------

@router.post("/frld-eligibility")
async def frld_eligibility_endpoint(request: FRLDEligibilityRequest) -> Dict[str, Any]:
    """Calculate FRLD fund eligibility and indicative allocation (COP28 Decision 2/CP.28)."""
    try:
        country_data = {
            "country_iso": request.country_iso,
            "country_name": request.country_name,
            "is_sids": request.is_sids,
            "is_ldc": request.is_ldc,
            "nd_gain_score": request.nd_gain_score,
            "gdp_usd": request.gdp_usd,
        }
        loss_event = {"event_type": request.event_type}
        result = calculate_frld_eligibility(country_data, loss_event)
        return {
            "status": "success",
            "country_iso": result.country_iso,
            "country_name": result.country_name,
            "eligibility_tier": result.eligibility_tier,
            "frld_eligibility_score": result.frld_eligibility_score,
            "indicative_allocation_usd": result.indicative_allocation_usd,
            "access_window": result.access_window,
            "v20_member": result.v20_member,
            "co_financing_required_pct": result.co_financing_required_pct,
            "priority_event_types": result.priority_event_types,
            "wim_functions_applicable": result.wim_functions_applicable,
            "estimated_annual_ld_usd": result.estimated_annual_ld_usd,
            "frld_coverage_ratio": result.frld_coverage_ratio,
            "decision_reference": "Decision 2/CP.28 — FRLD Fund Operationalisation (COP28 Dubai 2023)",
            "access_criteria": FRLD_ACCESS_CRITERIA.get(result.eligibility_tier, {}),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parametric-design")
async def parametric_design_endpoint(request: ParametricDesignRequest) -> Dict[str, Any]:
    """Design a parametric insurance trigger with payout structure and basis risk assessment."""
    try:
        result = design_parametric_trigger(request.dict())
        return {
            "status": "success",
            "trigger_id": result.trigger_id,
            "trigger_index": result.trigger_index,
            "trigger_threshold": result.trigger_threshold,
            "payout_structure": result.payout_structure,
            "attachment_point": result.attachment_point,
            "exhaustion_point": result.exhaustion_point,
            "max_payout_usd": result.max_payout_usd,
            "payout_at_attachment_usd": result.payout_at_attachment_usd,
            "expected_annual_payout_usd": result.expected_annual_payout_usd,
            "premium_estimate_usd": result.premium_estimate_usd,
            "basis_risk_score": result.basis_risk_score,
            "settlement_days": result.settlement_days,
            "data_source": result.data_source,
            "standard": "IAIS Application Paper on Parametric Insurance 2022",
            "trigger_reference": PARAMETRIC_TRIGGERS.get(result.trigger_index, {}),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/wim-access")
async def wim_access_endpoint(request: WIMAccessRequest) -> Dict[str, Any]:
    """Assess WIM function scores and Santiago Network eligibility."""
    try:
        result = assess_wim_access({
            "country_iso": request.country_iso,
            "is_ldc": request.is_ldc,
            "is_sids": request.is_sids,
        })
        return {
            "status": "success",
            "country_iso": result.country_iso,
            "wim_access_score": result.wim_access_score,
            "function_scores": {
                "risk_knowledge": result.risk_knowledge_score,
                "retention_transfer": result.retention_transfer_score,
                "rehabilitation": result.rehabilitation_score,
            },
            "santiago_network_eligible": result.santiago_network_eligible,
            "capacity_needs": result.capacity_needs,
            "wim_action_areas": result.wim_action_areas,
            "recommended_technical_providers": result.recommended_technical_providers,
            "wim_reference": "Warsaw International Mechanism COP19 Decision 2/CP.19 (2013)",
            "santiago_network_reference": "Santiago Network SNLD — UNFCCC COP25 Decision 2/CP.25 (2019)",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ld-gap-analysis")
async def ld_gap_analysis_endpoint(request: LDGapRequest) -> Dict[str, Any]:
    """Calculate total L&D and residual gap after insurance, FRLD, and WIM support."""
    try:
        country_data = {
            "country_iso": request.country_iso,
            "country_name": request.country_name,
            "event_type": request.event_type,
            "gdp_usd": request.gdp_usd,
        }
        coverage_data = {}
        if request.insurance_penetration is not None:
            coverage_data["insurance_penetration"] = request.insurance_penetration
        if request.global_shield_covered is not None:
            coverage_data["global_shield_covered"] = request.global_shield_covered

        result = calculate_residual_ld_gap(country_data, coverage_data)
        return {
            "status": "success",
            "country_iso": result.country_iso,
            "country_name": result.country_name,
            "event_type": result.event_type,
            "total_economic_loss_usd": result.total_economic_loss_usd,
            "non_economic_loss_score": result.non_economic_loss_score,
            "coverage_breakdown": {
                "insurance_covered_usd": result.insurance_covered_usd,
                "frld_eligible_usd": result.frld_eligible_usd,
                "global_shield_allocation_usd": result.global_shield_allocation_usd,
                "wim_support_usd": result.wim_support_usd,
            },
            "residual_ld_gap_usd": result.residual_ld_gap_usd,
            "insurance_coverage_ratio": result.insurance_coverage_ratio,
            "gap_financing_instruments": result.gap_financing_instruments,
            "non_economic_note": "Non-economic loss score covers cultural heritage, human mobility, ecosystem services — not fully monetisable",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ld-portfolio")
async def ld_portfolio_endpoint(request: LDPortfolioRequest) -> Dict[str, Any]:
    """Aggregate L&D exposure and coverage metrics across a multi-country portfolio."""
    try:
        result = aggregate_ld_portfolio(request.dict())
        return {
            "status": "success",
            "portfolio_id": result.portfolio_id,
            "total_portfolio_exposure_usd": result.total_portfolio_exposure_usd,
            "total_ld_exposure_usd": result.total_ld_exposure_usd,
            "v20_concentration_pct": result.v20_concentration_pct,
            "parametric_coverage_ratio": result.parametric_coverage_ratio,
            "residual_ld_gap_usd": result.residual_ld_gap_usd,
            "expected_annual_ld_payout_usd": result.expected_annual_ld_payout_usd,
            "top_loss_event_types": result.top_loss_event_types,
            "uninsured_countries": result.uninsured_countries,
            "recommendations": result.recommendations,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# GET Reference Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/v20-members")
async def ref_v20_members() -> Dict[str, Any]:
    """V20 Vulnerable 20 Group member countries."""
    return {
        "v20_members": V20_MEMBERS,
        "total_members": len(V20_MEMBERS),
        "combined_gdp_bn_usd": 2_300,
        "combined_population_mn": 1_500,
        "annual_ld_bn_usd": 525,
        "description": "V20 Vulnerable 20 Group — finance ministers of climate-vulnerable countries",
        "founding": "Lima 2015, expanded 2023",
        "secretariat": "Climate Vulnerable Forum",
    }


@router.get("/ref/frld-criteria")
async def ref_frld_criteria() -> Dict[str, Any]:
    """FRLD Fund access criteria per COP28 Decision 2/CP.28."""
    return {
        "access_criteria": FRLD_ACCESS_CRITERIA,
        "fund_initial_capitalisation_bn_usd": 0.7,
        "pledges_at_cop28_bn_usd": 0.792,
        "host_institution": "World Bank (interim, 4-year review)",
        "governing_board": "Equal representation developed/developing countries",
        "decision": "Decision 2/CP.28 (COP28 Dubai, December 2023)",
        "note": "Fund distinct from Green Climate Fund; no co-financing requirement for SIDS/LDCs",
    }


@router.get("/ref/global-shield")
async def ref_global_shield() -> Dict[str, Any]:
    """Global Shield Against Climate Risks v2 pillars and commitments."""
    return {
        "pillars": GLOBAL_SHIELD_PILLARS,
        "total_committed_bn_usd": 9.9,
        "coverage_countries": 58,
        "g7_launch": "Bali G7 2022",
        "v2_update": "Bonn 2023",
        "flagship_instruments": [
            "InsuResilience Global Partnership",
            "CCRIF Caribbean risk pool",
            "African Risk Capacity",
            "Pacific Catastrophe Risk Insurance Company",
        ],
        "target_2025": "People at risk covered increased 10x",
    }


@router.get("/ref/parametric-triggers")
async def ref_parametric_triggers() -> Dict[str, Any]:
    """Parametric insurance trigger indices with data sources and basis risk."""
    return {
        "triggers": PARAMETRIC_TRIGGERS,
        "total_indices": len(PARAMETRIC_TRIGGERS),
        "standard": "IAIS Application Paper on Parametric Insurance 2022",
        "basis_risk_mitigation": [
            "Higher spatial resolution satellite data",
            "Multiple concurrent triggers",
            "Index calibration against historical loss data (AIR/RMS/EQECAT)",
        ],
        "settlement_process": "Automated payout upon trigger data publication by designated data provider",
    }


@router.get("/ref/loss-event-types")
async def ref_loss_event_types() -> Dict[str, Any]:
    """Loss & Damage event type taxonomy with WIM relevance and insurance penetration."""
    return {
        "event_types": LOSS_EVENT_TYPES,
        "total_types": len(LOSS_EVENT_TYPES),
        "wim_action_areas": [
            "AA1: Risk knowledge and early warning",
            "AA2: Risk transfer and insurance",
            "AA3: Comprehensive risk management",
            "AA4: Social protection",
            "AA5: Resilience and adaptation",
            "AA6: Rehabilitation, recovery, reintegration",
            "AA7: Non-economic loss and damage",
            "AA8: Risk transfer and insurance (WIM-specific)",
        ],
        "global_annual_ld_bn_usd": 525,
        "insured_pct": 12,
        "source": "Munich Re NatCatSERVICE 2023",
    }
