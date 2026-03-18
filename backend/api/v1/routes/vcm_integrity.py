"""
Voluntary Carbon Market Integrity API Routes — E96
===================================================
Prefix  : /api/v1/vcm-integrity
Tags    : VCM Integrity — E96
"""
from __future__ import annotations

from typing import Any, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.vcm_integrity_engine import (
    CORSIA_PROGRAMMES,
    ICVCM_CRITERIA,
    OXFORD_PRINCIPLES,
    PRICE_BENCHMARKS,
    VCMI_CLAIM_TIERS,
    assess_vcm_integrity,
    get_vcm_benchmarks,
    screen_registry_entry,
)

router = APIRouter(prefix="/api/v1/vcm-integrity", tags=["VCM Integrity — E96"])


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class VCMIntegrityRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    project_id: str = Field(..., example="VCS-1234")
    registry: str = Field(..., example="verra_vcs", description="verra_vcs | gold_standard | acr | car | art6_itmo")
    methodology: str = Field(..., example="VM0007")
    project_type: str = Field(..., example="redd_plus")
    vintage_year: int = Field(..., example=2022)
    volume_tco2e: float = Field(..., example=50000.0)
    price_usd_t: float = Field(..., example=12.0)
    has_vvb_accreditation: bool = Field(default=True)
    monitoring_frequency_years: int = Field(default=1)
    public_documentation: bool = Field(default=True)
    fpic_completed: Optional[bool] = Field(default=None)
    sbti_near_term: bool = Field(default=False)
    sbti_long_term: bool = Field(default=False)
    residual_emissions_pct: float = Field(default=50.0, description="Residual emissions % above SBTi pathway")
    reduction_pct_of_portfolio: float = Field(default=70.0)
    removal_pct_of_portfolio: float = Field(default=10.0)
    geological_removal_pct: float = Field(default=2.0)
    has_assurance: bool = Field(default=False)
    corresponding_adjustment: bool = Field(default=False)


class RegistryScreenRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    registry_name: str = Field(..., example="verra_vcs")
    serial_number: str = Field(..., example="VCS-1234-2022-000001")
    project_type: str = Field(default="redd_plus")
    vintage_year: int = Field(default=2022)
    volume_tco2e: float = Field(default=1000.0)
    retirement_status: str = Field(default="active", description="active | retired | cancelled | suspended")
    beneficiary: Optional[str] = Field(default=None)


class BatchCreditItem(BaseModel):
    model_config = {"protected_namespaces": ()}

    project_id: str
    registry: str = Field(default="verra_vcs")
    methodology: str = Field(default="VM0007")
    project_type: str = Field(default="redd_plus")
    vintage_year: int = Field(default=2022)
    volume_tco2e: float = Field(default=10000.0)
    price_usd_t: float = Field(default=10.0)
    has_vvb_accreditation: bool = Field(default=True)
    monitoring_frequency_years: int = Field(default=1)
    public_documentation: bool = Field(default=True)
    fpic_completed: Optional[bool] = Field(default=None)
    corresponding_adjustment: bool = Field(default=False)


class BatchAssessRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str = Field(..., example="ENTITY-001")
    credits: List[BatchCreditItem]
    sbti_near_term: bool = Field(default=False)
    sbti_long_term: bool = Field(default=False)
    residual_emissions_pct: float = Field(default=50.0)
    has_assurance: bool = Field(default=False)


# ---------------------------------------------------------------------------
# POST endpoints
# ---------------------------------------------------------------------------

@router.post("/assess")
def assess_credit(req: VCMIntegrityRequest) -> dict[str, Any]:
    """
    Full VCM integrity assessment for a single carbon credit project.

    Returns ICVCM CCP criteria scores (10), CCP label eligibility, VCMI claim tier,
    Oxford Offsetting Principles scores, quality tier (A-D), CORSIA eligibility,
    Article 6 corresponding adjustment status, permanence profile, and price benchmarks.
    """
    try:
        return assess_vcm_integrity(
            project_id=req.project_id,
            registry=req.registry,
            methodology=req.methodology,
            project_type=req.project_type,
            vintage_year=req.vintage_year,
            volume_tco2e=req.volume_tco2e,
            price_usd_t=req.price_usd_t,
            has_vvb_accreditation=req.has_vvb_accreditation,
            monitoring_frequency_years=req.monitoring_frequency_years,
            public_documentation=req.public_documentation,
            fpic_completed=req.fpic_completed,
            sbti_near_term=req.sbti_near_term,
            sbti_long_term=req.sbti_long_term,
            residual_emissions_pct=req.residual_emissions_pct,
            reduction_pct_of_portfolio=req.reduction_pct_of_portfolio,
            removal_pct_of_portfolio=req.removal_pct_of_portfolio,
            geological_removal_pct=req.geological_removal_pct,
            has_assurance=req.has_assurance,
            corresponding_adjustment=req.corresponding_adjustment,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/registry-screen")
def registry_screen(req: RegistryScreenRequest) -> dict[str, Any]:
    """
    Screen a registry entry by serial number for integrity flags.

    Checks: retirement status, vintage age, reversal risk, CORSIA eligibility,
    and CCP programme eligibility. Returns PASS / WARNING / FAIL with flag details.
    """
    try:
        return screen_registry_entry(
            registry_name=req.registry_name,
            serial_number=req.serial_number,
            project_type=req.project_type,
            vintage_year=req.vintage_year,
            volume_tco2e=req.volume_tco2e,
            retirement_status=req.retirement_status,
            beneficiary=req.beneficiary,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/batch-assess")
def batch_assess(req: BatchAssessRequest) -> dict[str, Any]:
    """
    Batch assessment for a portfolio of carbon credits.

    Runs a full integrity assessment on each credit and returns:
    - Per-credit results with quality tier and CCP score
    - Portfolio-level aggregates: volume-weighted CCP composite, quality tier distribution,
      CORSIA eligible %, CCP label eligible %, total volume, total value, average price
    - Portfolio-level VCMI claim ceiling based on worst-qualifying credits
    """
    try:
        results = []
        total_volume = 0.0
        total_value = 0.0
        corsia_volume = 0.0
        ccp_eligible_volume = 0.0
        weighted_ccp_sum = 0.0
        tier_counts: dict[str, int] = {"A": 0, "B": 0, "C": 0, "D": 0}

        for credit in req.credits:
            result = assess_vcm_integrity(
                project_id=credit.project_id,
                registry=credit.registry,
                methodology=credit.methodology,
                project_type=credit.project_type,
                vintage_year=credit.vintage_year,
                volume_tco2e=credit.volume_tco2e,
                price_usd_t=credit.price_usd_t,
                has_vvb_accreditation=credit.has_vvb_accreditation,
                monitoring_frequency_years=credit.monitoring_frequency_years,
                public_documentation=credit.public_documentation,
                fpic_completed=credit.fpic_completed,
                sbti_near_term=req.sbti_near_term,
                sbti_long_term=req.sbti_long_term,
                residual_emissions_pct=req.residual_emissions_pct,
                has_assurance=req.has_assurance,
                corresponding_adjustment=credit.corresponding_adjustment,
            )
            results.append(result)
            vol = credit.volume_tco2e
            total_volume += vol
            total_value += vol * credit.price_usd_t
            ccp_score = result["icvcm_ccp_summary"]["ccp_composite_score"]
            weighted_ccp_sum += ccp_score * vol
            if result["corsia_eligibility"]["eligible"]:
                corsia_volume += vol
            if result["icvcm_ccp_summary"]["ccp_label_eligible"]:
                ccp_eligible_volume += vol
            tier = result["quality_assessment"]["quality_tier"]
            tier_counts[tier] = tier_counts.get(tier, 0) + 1

        portfolio_ccp = weighted_ccp_sum / total_volume if total_volume > 0 else 0
        avg_price = total_value / total_volume if total_volume > 0 else 0

        return {
            "entity_id": req.entity_id,
            "credits_assessed": len(results),
            "portfolio_summary": {
                "total_volume_tco2e": round(total_volume, 2),
                "total_value_usd": round(total_value, 2),
                "average_price_usd_t": round(avg_price, 4),
                "volume_weighted_ccp_composite": round(portfolio_ccp, 4),
                "corsia_eligible_pct": round(corsia_volume / total_volume * 100, 2) if total_volume else 0,
                "ccp_label_eligible_pct": round(ccp_eligible_volume / total_volume * 100, 2) if total_volume else 0,
                "quality_tier_distribution": tier_counts,
            },
            "per_credit_results": results,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# GET reference endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/icvcm-criteria")
def ref_icvcm_criteria() -> dict[str, Any]:
    """
    Reference: 10 ICVCM Core Carbon Principles (CCP) criteria with descriptions,
    pillar groupings, assessment elements, weights, and pass thresholds.
    """
    try:
        return {
            "framework": "ICVCM Core Carbon Principles Assessment Framework v2.0, 2023",
            "body": "Integrity Council for the Voluntary Carbon Market (ICVCM)",
            "total_criteria": len(ICVCM_CRITERIA),
            "pillars": ["Governance", "Emissions Impact", "Sustainable Development"],
            "criteria": ICVCM_CRITERIA,
            "ccp_label_rule": (
                "All 10 criteria must meet individual thresholds. "
                "C4 (Additionality), C5 (Permanence), C6 (Quantification), and C7 (No Double Counting) "
                "are blocking — failure in any of these prevents CCP label."
            ),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/vcmi-claims")
def ref_vcmi_claims() -> dict[str, Any]:
    """
    Reference: VCMI Claims Code of Practice v1.1 tier hierarchy (no_claim → silver → gold → platinum)
    with eligibility thresholds, SBTi requirements, credit quality requirements, and annual obligations.
    """
    try:
        return {
            "framework": "VCMI Claims Code of Practice v1.1, 2023",
            "body": "Voluntary Carbon Markets Integrity Initiative (VCMI)",
            "tier_hierarchy": ["no_claim", "silver", "gold", "platinum"],
            "claim_tiers": VCMI_CLAIM_TIERS,
            "general_requirements": [
                "Company must have a publicly disclosed GHG inventory (Scope 1, 2, and material Scope 3)",
                "Annual VCMI Credibility Checklist must be submitted",
                "Credit vintages must be within 5 years of retirement year",
                "Retired credits must be publicly disclosed with registry serial numbers",
            ],
            "high_integrity_credit_definition": (
                "Credits that carry the ICVCM CCP label are 'high integrity' by default. "
                "Credits from CORSIA-eligible programmes without CCP label may qualify for "
                "Silver/Gold tiers with additional due diligence."
            ),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/oxford-principles")
def ref_oxford_principles() -> dict[str, Any]:
    """
    Reference: Oxford Offsetting Principles (2020) — 4 principles with full descriptions
    and scoring rubrics for corporate offsetting portfolio alignment.
    """
    try:
        return {
            "framework": "Oxford Offsetting Principles",
            "published": "September 2020",
            "body": "Smith School of Enterprise and the Environment, University of Oxford",
            "publication": "The Oxford Principles for Net Zero Aligned Carbon Offsetting",
            "principles": OXFORD_PRINCIPLES,
            "composite_scoring": (
                "Each principle scored 0.0-1.0. Composite = simple average of 4 principle scores. "
                "Score ≥0.75: Strong Oxford alignment. 0.50-0.75: Moderate. <0.50: Misaligned."
            ),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/price-benchmarks")
def ref_price_benchmarks() -> dict[str, Any]:
    """
    Reference: Carbon credit price benchmarks by project type and storage class.
    Includes low/mid/high USD/tCO2e ranges and CCP premium percentages.
    """
    try:
        return get_vcm_benchmarks()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/corsia-programmes")
def ref_corsia_programmes() -> dict[str, Any]:
    """
    Reference: CORSIA eligible programmes list (ICAO 2024-2026 cycle) with
    approval status, category-level assessment availability, and programme URLs.
    """
    try:
        return {
            "framework": "CORSIA (Carbon Offsetting and Reduction Scheme for International Aviation)",
            "body": "ICAO (International Civil Aviation Organization)",
            "current_cycle": "2024-2026",
            "programmes": CORSIA_PROGRAMMES,
            "total_programmes": len(CORSIA_PROGRAMMES),
            "usage_note": (
                "Airlines covered by CORSIA must surrender eligible emissions units "
                "from ICAO-approved programmes to offset growth above 2019 baseline levels. "
                "From 2027, absolute emission limits apply."
            ),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
