"""
Nature-Based Solutions Finance — E94 Routes
============================================
Prefix: /api/v1/nbs-finance
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from services.nbs_finance_engine import (
    NbSProjectRequest,
    BlendedFinanceRequest,
    assess_nbs_project,
    calculate_blended_finance,
    get_nbs_benchmarks,
    IUCN_CRITERIA,
    NBS_CATEGORIES,
    VCMI_CLAIMS,
    GBF_TARGET_2,
    CARBON_CREDIT_STANDARDS,
    GCF_CRITERIA,
)

router = APIRouter(prefix="/api/v1/nbs-finance", tags=["NbS Finance — E94"])


# ── POST /assess ─────────────────────────────────────────────────────────────

@router.post("/assess", summary="Full NbS project assessment (IUCN NbS v2.0 + co-benefits + VCMI)")
def assess_nbs(req: NbSProjectRequest) -> dict[str, Any]:
    """
    Performs a full IUCN Global Standard for NbS v2.0 assessment including:
    - 8 weighted criteria scoring → IUCN composite score and tier (bronze/silver/gold)
    - Carbon co-benefits (sequestration rate, VCM pricing, buffer pool)
    - Biodiversity co-benefits (MSA uplift, species count, GBF T2 contribution)
    - Water co-benefits (watershed protection, quality improvement)
    - Social co-benefits (communities, livelihoods, FPIC status)
    - VCMI Core Carbon Claims eligibility (no_claim → platinum)
    - Full economics: NPV, IRR, payback, break-even carbon price
    - Overall NbS quality score and bankability tier
    """
    valid_categories = list(NBS_CATEGORIES.keys())
    if req.nbs_category not in valid_categories:
        raise HTTPException(
            status_code=422,
            detail=f"nbs_category must be one of {valid_categories}",
        )
    valid_standards = ["VCS", "Gold_Standard", "Plan_Vivo", "Art6"]
    if req.carbon_credit_standard not in valid_standards:
        raise HTTPException(
            status_code=422,
            detail=f"carbon_credit_standard must be one of {valid_standards}",
        )
    try:
        return assess_nbs_project(req)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── POST /blended-finance ────────────────────────────────────────────────────

@router.post("/blended-finance", summary="Blended finance structure analysis for NbS projects")
def blended_finance(req: BlendedFinanceRequest) -> dict[str, Any]:
    """
    Analyses blended finance structuring for NbS projects:
    - Public / private / philanthropic capital stack sizing
    - GCF eligibility and suggested grant tranche
    - Financing gap analysis and de-risking instruments
    - OECD DAC ODA eligibility assessment
    - Mobilisation ratio vs Convergence benchmarks
    - Multi-year carbon and ecosystem service revenue projections
    - Investor return profile (expected IRR, green bond eligibility)
    """
    if req.total_project_cost_m <= 0:
        raise HTTPException(status_code=422, detail="total_project_cost_m must be > 0")
    try:
        return calculate_blended_finance(req)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── GET /ref/iucn-criteria ───────────────────────────────────────────────────

@router.get("/ref/iucn-criteria", summary="IUCN NbS Global Standard v2.0 — 8 criteria descriptions")
def ref_iucn_criteria() -> dict[str, Any]:
    """
    Returns full descriptions, key questions, and weightings for all 8 IUCN Global
    Standard for Nature-based Solutions v2.0 criteria.
    Source: IUCN (2024) Global Standard for NbS, 2nd edition.
    """
    return {
        "standard": "IUCN Global Standard for Nature-based Solutions v2.0",
        "edition": "2024",
        "total_criteria": 8,
        "scoring_note": "Each criterion scored 0-100; composite = weighted average. "
                        "Tiers: <40=not_eligible, 40-59=bronze, 60-74=silver, ≥75=gold.",
        "criteria": IUCN_CRITERIA,
    }


# ── GET /ref/nbs-categories ──────────────────────────────────────────────────

@router.get("/ref/nbs-categories", summary="NbS project categories with sequestration benchmarks")
def ref_nbs_categories() -> dict[str, Any]:
    """
    Returns the 8 supported NbS project categories with:
    - Typical carbon sequestration ranges (tCO2e/ha/yr)
    - Co-benefit ratings (biodiversity, water, social)
    - Permanence risk classification
    - Applicable carbon credit standards
    - SDG alignment
    """
    return get_nbs_benchmarks()


# ── GET /ref/vcmi-claims ─────────────────────────────────────────────────────

@router.get("/ref/vcmi-claims", summary="VCMI Core Carbon Claims hierarchy (no_claim → platinum)")
def ref_vcmi_claims() -> dict[str, Any]:
    """
    Returns VCMI Core Carbon Claims Framework v1.0 (2023) claim tiers with:
    - Integrity score thresholds
    - Requirements for each claim level
    - Eligible carbon credit standards per tier
    Source: Voluntary Carbon Markets Integrity Initiative (VCMI) v1.0, 2023.
    """
    return {
        "framework": "VCMI Core Carbon Claims Framework",
        "version": "v1.0",
        "published": "2023",
        "purpose": (
            "Provides guidance for companies making credible carbon claims "
            "beyond regulatory compliance, linked to high-quality carbon credit retirement."
        ),
        "integrity_score_range": "0-100 (derived from IUCN score, MRV quality, NDC alignment)",
        "claims": VCMI_CLAIMS,
    }


# ── GET /ref/gbf-target-2 ────────────────────────────────────────────────────

@router.get("/ref/gbf-target-2", summary="GBF Kunming-Montreal Target 2 — 30×30 restoration requirements")
def ref_gbf_target_2() -> dict[str, Any]:
    """
    Returns the Kunming-Montreal Global Biodiversity Framework (GBF) Target 2 details:
    - 30×30 restoration headline target
    - Sub-targets T2a–T2d
    - Monitoring indicators
    - Finance targets (USD 200bn/yr biodiversity finance by 2030)
    - NbS project contribution pathway
    Source: CBD COP15, Kunming-Montreal GBF, December 2022.
    """
    return {
        "gbf_target_2": GBF_TARGET_2,
        "gcf_nbs_support": {
            "gcf_criteria": GCF_CRITERIA,
            "gcf_nbs_funded_projects_2023": 47,
            "gcf_nbs_total_approved_usd_m": 2_340,
        },
        "cross_framework_links": {
            "TNFD": "TNFD v1.0 metrics M10-M12 (state, response, dependency metrics)",
            "CSRD_ESRS_E4": "ESRS E4-4 biodiversity and ecosystems disclosures",
            "SBTN": "SBTN Step 4 (Set science-based targets for nature)",
            "GRI_304": "GRI 304 Biodiversity Standard",
        },
    }
