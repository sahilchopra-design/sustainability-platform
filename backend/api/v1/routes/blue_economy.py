from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any

from services.blue_economy_engine import (
    screen_blue_bond,
    assess_blue_carbon,
    assess_bbnj_compliance,
    assess_ocean_acidification_risk,
    aggregate_ocean_portfolio,
    assess_sof_alignment,
    BLUE_CARBON_ECOSYSTEMS,
    BLUE_BOND_USE_OF_PROCEEDS,
    BBNJ_ARTICLES,
    SOF_PILLARS,
    OCEAN_ACIDIFICATION_RISK,
)

router = APIRouter(prefix="/api/v1/blue-economy", tags=["Blue Economy & Ocean Finance — E68"])

# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class BlueBondScreenRequest(BaseModel):
    entity_id: str
    bond_id: Optional[str] = None
    issuer: Optional[str] = "Unknown Issuer"
    bond_amount_usd: Optional[float] = 500_000_000
    use_of_proceeds_categories: Optional[List[str]] = None


class BlueCarbonRequest(BaseModel):
    project_id: str
    ecosystem_type: Optional[str] = "mangrove"
    area_hectares: Optional[float] = None
    threat_level: Optional[float] = None
    tenure_clarity: Optional[float] = None
    baseline_quality: Optional[float] = None
    governance_score: Optional[float] = None
    carbon_price_usd_tco2: Optional[float] = None


class BBNJComplianceRequest(BaseModel):
    entity_id: str
    entity_type: Optional[str] = "flag_state"
    article_scores: Optional[Dict[str, float]] = None


class OceanAcidificationRequest(BaseModel):
    portfolio_id: str
    rcp_scenario: Optional[str] = "RCP4.5"
    ocean_economy_exposure_usd: Optional[float] = None
    fisheries_pct: Optional[float] = None
    coral_reef_pct: Optional[float] = None
    aquaculture_pct: Optional[float] = None


class OceanPortfolioRequest(BaseModel):
    portfolio_id: str
    total_aum_usd: Optional[float] = None
    rcp_scenario: Optional[str] = "RCP4.5"
    blue_bond_allocation_pct: Optional[float] = None
    holdings: Optional[List[Dict[str, Any]]] = None


class SOFAssessmentRequest(BaseModel):
    entity_id: str
    entity_name: Optional[str] = None
    declared_sof_scores: Optional[Dict[str, float]] = None


# ---------------------------------------------------------------------------
# POST Endpoints
# ---------------------------------------------------------------------------

@router.post("/screen-bond")
async def screen_bond_endpoint(request: BlueBondScreenRequest) -> Dict[str, Any]:
    """Screen a bond against ICMA Blue Bond Principles 2023 and UNEP-FI SOF framework."""
    try:
        result = screen_blue_bond(request.dict())
        return {
            "status": "success",
            "bond_id": result.bond_id,
            "issuer": result.issuer,
            "bond_amount_usd": result.bond_amount_usd,
            "icma_alignment_score": result.icma_alignment_score,
            "overall_verdict": result.overall_verdict,
            "eligible_categories": result.eligible_categories,
            "ineligible_categories": result.ineligible_categories,
            "sof_pillar_coverage": result.sof_pillar_coverage,
            "use_of_proceeds_breakdown": result.use_of_proceeds_breakdown,
            "greenium_bps": result.greenium_bps,
            "external_review_required": result.external_review_required,
            "reporting_frequency": result.reporting_frequency,
            "recommendations": result.recommendations,
            "standards_applied": [
                "ICMA Blue Bond Principles 2023",
                "UNEP-FI Sustainable Ocean Finance 2021",
                "OECD Ocean Finance Framework 2022",
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/blue-carbon")
async def blue_carbon_endpoint(request: BlueCarbonRequest) -> Dict[str, Any]:
    """Assess blue carbon sequestration, additionality, permanence, and credit economics."""
    try:
        result = assess_blue_carbon(request.dict())
        return {
            "status": "success",
            "project_id": result.project_id,
            "ecosystem_type": result.ecosystem_type,
            "area_hectares": result.area_hectares,
            "sequestration_rate_tco2_ha_yr": result.sequestration_rate_tco2_ha_yr,
            "total_annual_sequestration_tco2": result.total_annual_sequestration_tco2,
            "project_lifetime_years": result.project_lifetime_years,
            "total_lifetime_sequestration_tco2": result.total_lifetime_sequestration_tco2,
            "additionality_score": result.additionality_score,
            "permanence_score": result.permanence_score,
            "risk_buffer_pct": result.risk_buffer_pct,
            "co_benefits": result.co_benefits,
            "verra_vcs_eligible": result.verra_vcs_eligible,
            "gold_standard_eligible": result.gold_standard_eligible,
            "carbon_credit_value_usd": result.carbon_credit_value_usd,
            "monitoring_cost_usd_yr": result.monitoring_cost_usd_yr,
            "net_revenue_usd_yr": result.net_revenue_usd_yr,
            "verification_cycle_years": result.verification_cycle_years,
            "methodology_reference": BLUE_CARBON_ECOSYSTEMS[result.ecosystem_type].get("verra_methodology"),
            "standards_applied": ["Blue Carbon Initiative", "Verra VCS VM0007/VM0033", "Gold Standard"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bbnj-compliance")
async def bbnj_compliance_endpoint(request: BBNJComplianceRequest) -> Dict[str, Any]:
    """Assess compliance with the High Seas Treaty BBNJ 2023."""
    try:
        result = assess_bbnj_compliance(request.dict())
        return {
            "status": "success",
            "entity_id": result.entity_id,
            "entity_type": result.entity_type,
            "overall_compliance_score": result.overall_compliance_score,
            "compliance_level": result.compliance_level,
            "article_scores": result.article_scores,
            "gaps": result.gaps,
            "priority_actions": result.priority_actions,
            "readiness_timeline": result.bbnj_readiness_timeline,
            "treaty_reference": "Agreement under UNCLOS on BBNJ of Areas beyond National Jurisdiction (2023)",
            "articles_assessed": list(BBNJ_ARTICLES.keys()),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ocean-acidification")
async def ocean_acidification_endpoint(request: OceanAcidificationRequest) -> Dict[str, Any]:
    """Assess portfolio exposure to ocean acidification under IPCC AR6 RCP scenarios."""
    try:
        result = assess_ocean_acidification_risk(request.dict())
        oa_ref = OCEAN_ACIDIFICATION_RISK[result.rcp_scenario]
        return {
            "status": "success",
            "portfolio_id": result.portfolio_id,
            "rcp_scenario": result.rcp_scenario,
            "ph_change_by_2100": result.ph_change_2100,
            "aragonite_saturation_omega": result.aragonite_saturation,
            "risk_level": result.risk_level,
            "ocean_economy_exposure_usd": result.ocean_economy_exposure_usd,
            "fisheries_revenue_at_risk_usd": result.fisheries_revenue_at_risk_usd,
            "coral_reef_asset_at_risk_usd": result.coral_reef_asset_at_risk_usd,
            "aquaculture_at_risk_usd": result.aquaculture_at_risk_usd,
            "total_oa_var_usd": result.total_oa_var_usd,
            "adaptation_cost_estimate_usd": result.adaptation_cost_estimate_usd,
            "coral_bleaching_frequency_multiplier": oa_ref["coral_bleaching_freq_multiplier"],
            "source": "IPCC AR6 WGI Chapter 3 — Ocean, Cryosphere and Sea Level Change",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ocean-portfolio")
async def ocean_portfolio_endpoint(request: OceanPortfolioRequest) -> Dict[str, Any]:
    """Aggregate portfolio-level SOF score, blue bond allocation, and ocean risk."""
    try:
        result = aggregate_ocean_portfolio(request.dict())
        return {
            "status": "success",
            "portfolio_id": result.portfolio_id,
            "total_blue_assets_usd": result.total_blue_assets_usd,
            "sof_score": result.sof_score,
            "sof_tier": "leader" if result.sof_score >= 0.75 else "progressing" if result.sof_score >= 0.50 else "emerging",
            "sof_pillar_scores": result.sof_pillar_scores,
            "blue_bond_allocation_pct": result.blue_bond_allocation_pct,
            "blue_carbon_credits_tco2": result.blue_carbon_credits_tco2,
            "mpa_financing_usd": result.mpa_financing_usd,
            "ocean_risk_score": result.ocean_risk_score,
            "oa_risk_var_usd": result.oa_risk_var_usd,
            "top_blue_economy_sectors": result.top_blue_economy_sectors,
            "sdg14_alignment_score": result.sdg14_alignment_score,
            "recommendations": result.recommendations,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sof-assessment")
async def sof_assessment_endpoint(request: SOFAssessmentRequest) -> Dict[str, Any]:
    """Comprehensive UNEP-FI Sustainable Ocean Finance alignment assessment."""
    try:
        result = assess_sof_alignment(request.dict())
        return {"status": "success", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# GET Reference Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/ecosystems")
async def ref_ecosystems() -> Dict[str, Any]:
    """Blue carbon ecosystem reference data with sequestration rates and methodologies."""
    return {
        "ecosystems": BLUE_CARBON_ECOSYSTEMS,
        "total_sequestration_potential_bn_tco2": 33.0,
        "source": "Blue Carbon Initiative / IPCC 2013 Wetlands Supplement",
        "note": "Seagrass permanence under review; Verra VM0033 covers mangrove, seagrass, saltmarsh",
    }


@router.get("/ref/use-of-proceeds")
async def ref_use_of_proceeds() -> Dict[str, Any]:
    """ICMA Blue Bond Principles 2023 eligible use-of-proceeds categories."""
    return {
        "categories": BLUE_BOND_USE_OF_PROCEEDS,
        "standard": "ICMA Blue Bond Principles 2023",
        "total_categories": len(BLUE_BOND_USE_OF_PROCEEDS),
        "external_review_required_threshold_usd": 100_000_000,
    }


@router.get("/ref/bbnj-articles")
async def ref_bbnj_articles() -> Dict[str, Any]:
    """High Seas Treaty BBNJ 2023 key articles for compliance assessment."""
    return {
        "articles": BBNJ_ARTICLES,
        "treaty_name": "Agreement under UNCLOS on Conservation and Sustainable Use of BBNJ",
        "adoption_date": "2023-03-04",
        "signatory_threshold_for_entry_into_force": 60,
        "note": "Entry into force contingent on 60 ratifications",
    }


@router.get("/ref/sof-pillars")
async def ref_sof_pillars() -> Dict[str, Any]:
    """UNEP-FI Sustainable Ocean Finance six pillars."""
    return {
        "pillars": SOF_PILLARS,
        "framework": "UNEP-FI Sustainable Blue Economy Finance Principles 2021",
        "total_pillars": len(SOF_PILLARS),
        "sdg_alignment": "SDG14 Life Below Water",
    }


@router.get("/ref/ocean-markets")
async def ref_ocean_markets() -> Dict[str, Any]:
    """Global ocean economy market sizing and financing gap data."""
    return {
        "global_ocean_economy_gdp_bn_usd": 2_500,
        "ocean_economy_potential_2030_bn_usd": 3_000,
        "sdg14_annual_financing_gap_bn_usd": 175,
        "blue_bond_issuance_2023_bn_usd": 5.5,
        "blue_carbon_market_2023_mn_usd": 120,
        "offshore_wind_installed_gw": 65,
        "offshore_wind_pipeline_2030_gw": 380,
        "mpa_coverage_pct_ocean": 8.1,
        "target_30x30_pct": 30,
        "rcp_scenarios": list(OCEAN_ACIDIFICATION_RISK.keys()),
        "key_standards": [
            "ICMA Blue Bond Principles 2023",
            "UNEP-FI SOF Principles 2021",
            "OECD Ocean Finance Framework 2022",
            "Poseidon Principles 2019",
            "Sea Pledge (UNEP 2020)",
            "BBNJ Treaty 2023",
        ],
    }
