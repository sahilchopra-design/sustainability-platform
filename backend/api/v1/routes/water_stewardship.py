"""
Water Risk & Stewardship Finance Routes — E92
Prefix: /api/v1/water-risk
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from services.water_stewardship_engine import (
    assess_water_risk,
    create_stewardship_target,
    get_benchmark_data,
    WaterRiskAssessRequest,
    StewardshipTargetRequest,
    AQUEDUCT_BASIN_BENCHMARKS,
    AQUEDUCT_INDICATORS,
    AQUEDUCT_RISK_TIERS,
    CDP_WATER_CRITERIA,
    CDP_GRADE_THRESHOLDS,
    TNFD_E3_METRICS,
    AWS_STANDARD_v2,
    AWS_CERTIFICATION_TIERS,
    CEO_WATER_MANDATE,
    WATER_BOND_FRAMEWORK,
)

router = APIRouter(prefix="/api/v1/water-risk", tags=["Water Risk & Stewardship — E92"])


# ---------------------------------------------------------------------------
# POST endpoints
# ---------------------------------------------------------------------------

@router.post("/assess")
async def assess_water_risk_endpoint(request: WaterRiskAssessRequest) -> Dict[str, Any]:
    """
    Full water risk and stewardship assessment.

    Computes:
    - WRI AQUEDUCT 4.0 composite score across 6 indicators (weighted)
    - TNFD E3 water withdrawal / consumption / discharge / recycling metrics
    - CDP Water Security grade (A / A- / B / C / D / F) and A-List eligibility
    - AWS Alliance for Water Stewardship Standard v2.0 score and certification tier
    - CEO Water Mandate stewardship score
    - Financial exposure: opex risk, regulatory risk, stranded asset risk (USD million)
    - Water stewardship bond eligibility (ICMA Green Bond Principles — Water UoP)
    - Overall water_risk_score (0-100) and water_risk_tier (low/medium/high/critical)
    """
    try:
        result = assess_water_risk(request.dict())
        return {
            "status": "success",
            "entity_id": result.entity_id,
            "entity_name": result.entity_name,
            "sector": result.sector,
            "basin_name": result.basin_name,
            "aqueduct": {
                "indicator_scores": result.aqueduct_indicator_scores,
                "overall_score": result.aqueduct_overall_score,
                "risk_tier": result.aqueduct_risk_tier,
            },
            "tnfd_e3": {
                "water_withdrawal_ml_yr": result.water_withdrawal_ml_yr,
                "water_consumption_ml_yr": result.water_consumption_ml_yr,
                "water_discharge_ml_yr": result.water_discharge_ml_yr,
                "recycled_pct": result.recycled_pct,
                "water_stressed_area_pct": result.water_stressed_area_pct,
                "disclosure_score": result.tnfd_water_disclosure_score,
            },
            "cdp_water_security": {
                "governance_score": result.cdp_governance_score,
                "risk_score": result.cdp_risk_score,
                "targets_score": result.cdp_targets_score,
                "performance_score": result.cdp_performance_score,
                "composite_score": result.cdp_composite_score,
                "grade": result.cdp_grade,
                "a_list_eligible": result.cdp_a_list_eligible,
            },
            "aws_standard_v2": {
                "water_balance_score": result.aws_water_balance_score,
                "governance_score": result.aws_governance_score,
                "site_water_status_score": result.aws_site_water_status_score,
                "engagement_score": result.aws_engagement_score,
                "site_outcomes_score": result.aws_site_outcomes_score,
                "overall_score": result.aws_overall_score,
                "certification_level": result.aws_certification_level,
                "certification_eligible": result.aws_certification_eligible,
            },
            "ceo_water_mandate": {
                "committed": result.cwm_committed,
                "targets_set": result.cwm_targets_set,
                "stewardship_score": result.cwm_stewardship_score,
            },
            "financial_exposure": {
                "water_opex_risk_m": result.water_opex_risk_m,
                "water_regulatory_risk_m": result.water_regulatory_risk_m,
                "water_stranded_asset_risk_m": result.water_stranded_asset_risk_m,
                "total_water_financial_risk_m": result.total_water_financial_risk_m,
            },
            "stewardship_bond": {
                "eligible": result.water_bond_eligible,
                "framework_score": result.water_bond_framework_score,
            },
            "overall": {
                "water_risk_score": result.water_risk_score,
                "water_risk_tier": result.water_risk_tier,
            },
            "key_findings": result.key_findings,
            "recommendations": result.recommendations,
            "standards_applied": result.standards_applied,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stewardship-target")
async def stewardship_target_endpoint(request: StewardshipTargetRequest) -> Dict[str, Any]:
    """
    Create and validate a water stewardship target.

    Assesses:
    - CDP target quality score (0-1) against A-List target criteria
    - SBTN Corporate Water Targets v1.0 alignment check
    - AWS Standard v2.0 compatibility check
    - Annual reduction quantum and CAGR
    - SDG 6.4 contribution statement
    - Target validity: High / Medium / Low quality assessment
    """
    try:
        result = create_stewardship_target(request.dict())
        return {
            "status": "success",
            "entity_id": result.entity_id,
            "entity_name": result.entity_name,
            "target_type": result.target_type,
            "target_parameters": {
                "baseline_year": result.baseline_year,
                "target_year": result.target_year,
                "baseline_withdrawal_ml_yr": result.baseline_withdrawal_ml_yr,
                "target_reduction_pct": result.target_reduction_pct,
                "target_withdrawal_ml_yr": result.target_withdrawal_ml_yr,
                "annual_reduction_ml_yr": result.annual_reduction_ml_yr,
                "cagr_pct": result.cagr_pct,
            },
            "quality_assessment": {
                "cdp_target_quality_score": result.cdp_target_quality_score,
                "sbtn_aligned": result.sbtn_aligned,
                "aws_target_compatible": result.aws_target_compatible,
                "target_validity_assessment": result.target_validity_assessment,
            },
            "sdg_6_contribution": result.sdg_6_contribution,
            "recommendations": result.recommendations,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# GET reference endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/aqueduct-benchmarks")
async def get_aqueduct_benchmarks() -> Dict[str, Any]:
    """
    WRI AQUEDUCT 4.0 basin benchmark data — 15 major basins with indicator values
    and composite risk scores. Also returns indicator definitions and risk tier thresholds.
    """
    return {
        "status": "success",
        "source": "WRI AQUEDUCT 4.0 (2023) — https://www.wri.org/aqueduct",
        "basin_benchmarks": AQUEDUCT_BASIN_BENCHMARKS,
        "indicator_definitions": AQUEDUCT_INDICATORS,
        "risk_tier_thresholds": AQUEDUCT_RISK_TIERS,
        "indicator_count": len(AQUEDUCT_INDICATORS),
        "basin_count": len(AQUEDUCT_BASIN_BENCHMARKS),
    }


@router.get("/ref/cdp-criteria")
async def get_cdp_criteria() -> Dict[str, Any]:
    """
    CDP Water Security A-List scoring criteria — 4 equally weighted pillars
    (governance, risk identification, targets, performance) with sub-criteria
    and A-List minimum score thresholds. Includes grade thresholds A through F.
    """
    return {
        "status": "success",
        "source": "CDP Water Security Questionnaire 2024 — https://www.cdp.net/en/water",
        "pillar_count": len(CDP_WATER_CRITERIA),
        "a_list_composite_minimum": 0.80,
        "data_verification_bonus": "4% uplift applied to composite when third-party verified",
        "scoring_criteria": CDP_WATER_CRITERIA,
        "grade_thresholds": CDP_GRADE_THRESHOLDS,
        "tnfd_e3_metrics": TNFD_E3_METRICS,
    }


@router.get("/ref/aws-standard")
async def get_aws_standard() -> Dict[str, Any]:
    """
    Alliance for Water Stewardship (AWS) Standard v2.0 assessment criteria —
    5 equally weighted pillars with core criteria, verification requirements,
    and key assessment questions. Includes certification tier thresholds.
    """
    return {
        "status": "success",
        "source": "Alliance for Water Stewardship Standard v2.0 (2022) — https://a4ws.org",
        "standard_version": "AWS Standard v2.0",
        "effective_date": "2022-01-01",
        "pillar_count": len(AWS_STANDARD_v2),
        "pillar_weight_each_pct": 20,
        "certification_tiers": AWS_CERTIFICATION_TIERS,
        "pillar_criteria": AWS_STANDARD_v2,
        "ceo_water_mandate": CEO_WATER_MANDATE,
        "un_sdg_alignment": ["SDG 6 — Clean Water and Sanitation", "SDG 12 — Responsible Consumption", "SDG 17 — Partnerships"],
    }


@router.get("/ref/stewardship-bond")
async def get_stewardship_bond_framework() -> Dict[str, Any]:
    """
    Water stewardship bond framework requirements — eligible use of proceeds
    categories, ICMA Green Bond Principles alignment, EU Taxonomy Objective 3,
    reporting requirements, SPO requirements, and greenium estimates by basin stress tier.
    """
    return {
        "status": "success",
        "source": "ICMA Green Bond Principles 2021; EU Taxonomy Regulation 2020/852 (Delegated Act)",
        "framework": WATER_BOND_FRAMEWORK,
        "eligible_category_count": len(WATER_BOND_FRAMEWORK.get("eligible_use_of_proceeds", [])),
        "bond_eligibility_minimum_score": 0.70,
        "key_standards": [
            "ICMA Green Bond Principles 2021 — Water and Wastewater UoP Category",
            "EU Taxonomy Objective 3 — Sustainable Use and Protection of Water and Marine Resources",
            "GRI 303: Water and Effluents 2018",
            "TNFD E3 Mandatory Metrics (WD-1 to WD-5)",
            "SBTN Corporate Water Targets v1.0 (2023)",
            "UN SDG 6 — Clean Water and Sanitation by 2030",
        ],
    }
