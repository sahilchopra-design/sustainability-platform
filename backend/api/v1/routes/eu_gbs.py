"""
API Routes: EU Green Bond Standard Engine (E14)
================================================
POST /api/v1/eu-gbs/assess-issuance           — Full EU GBS compliance assessment
POST /api/v1/eu-gbs/generate-factsheet        — Generate Green Bond Factsheet (GBFS)
POST /api/v1/eu-gbs/allocation-report         — Post-issuance allocation report check
POST /api/v1/eu-gbs/impact-report             — Post-issuance impact report check
POST /api/v1/eu-gbs/assess/batch              — Batch issuance assessments
GET  /api/v1/eu-gbs/ref/bond-types            — Bond type definitions
GET  /api/v1/eu-gbs/ref/taxonomy-objectives   — 6 EU Taxonomy environmental objectives
GET  /api/v1/eu-gbs/ref/er-requirements       — External Reviewer requirements (Art 22-24)
GET  /api/v1/eu-gbs/ref/standards-comparison  — EU GBS vs ICMA GBP vs Climate Bonds Standard
GET  /api/v1/eu-gbs/ref/timeline              — EUGBS regulatory timeline (2023-2026)
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.eu_gbs_engine import (
    EUGBSEngine,
    IssuanceInput,
    AllocationReportInput,
    ImpactReportInput,
    BOND_TYPES,
    TAXONOMY_ENVIRONMENTAL_OBJECTIVES,
    ER_REQUIREMENTS,
    STANDARDS_COMPARISON,
    EUGBS_TIMELINE,
)

router = APIRouter(
    prefix="/api/v1/eu-gbs",
    tags=["EU Green Bond Standard — Regulation 2023/2631"],
)

_ENGINE = EUGBSEngine()


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class IssuanceInputModel(BaseModel):
    bond_id: str
    issuer_name: str
    bond_type: str = Field(
        "senior_unsecured",
        description=(
            "senior_unsecured | covered_bond | sovereign | high_yield | "
            "green_loan_linked | standard_green_bond"
        ),
    )
    principal_amount: float = Field(..., gt=0, description="Bond principal in currency units")
    currency: str = Field("EUR", description="ISO currency code")
    taxonomy_alignment_pct: float = Field(
        0.0, ge=0.0, le=100.0,
        description="% of proceeds allocated to taxonomy-aligned activities",
    )
    dnsh_confirmed: bool = Field(False, description="DNSH assessment completed and confirmed")
    min_safeguards_confirmed: bool = Field(
        False, description="Minimum safeguards per Art 18 EU Taxonomy confirmed"
    )
    environmental_objectives: List[str] = Field(
        default_factory=list,
        description="List of EU Taxonomy environmental objective codes: CCM/CCA/WMR/CE/PPE/BIO",
    )
    has_external_reviewer: bool = Field(False, description="ESMA-registered ER engaged")
    er_name: str = Field("", description="Name of the External Reviewer")
    has_pre_issuance_review: bool = Field(
        False, description="Pre-issuance GBFS review completed by ER"
    )
    refinancing_share_pct: float = Field(
        0.0, ge=0.0, le=100.0,
        description="Share of proceeds for refinancing existing green assets",
    )
    is_sovereign: bool = Field(
        False,
        description="Sovereign/sub-sovereign issuer eligible for Art 21 flexibility provisions",
    )


class AllocationReportModel(BaseModel):
    bond_id: str
    reporting_period: str = Field(..., description="e.g. '2025-12-31' or 'FY2025'")
    total_allocated_pct: float = Field(..., ge=0.0, le=100.0)
    taxonomy_aligned_pct: float = Field(..., ge=0.0, le=100.0)
    allocation_by_objective: Dict[str, float] = Field(
        default_factory=dict,
        description="Allocation % by environmental objective code",
    )
    unallocated_pct: float = Field(0.0, ge=0.0, le=100.0)
    geographic_breakdown: Dict[str, float] = Field(
        default_factory=dict,
        description="Allocation % by country/region",
    )


class ImpactReportModel(BaseModel):
    bond_id: str
    reporting_period: str
    impact_indicators: Dict[str, float] = Field(
        default_factory=dict,
        description="Impact metric name → value (e.g. {'tco2e_avoided': 12500.0})",
    )
    methodology_description: str = Field(
        "", description="Description of impact measurement methodology"
    )
    alignment_maintained: bool = Field(
        True,
        description="Whether taxonomy alignment of funded assets is maintained",
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/assess-issuance",
    summary="Full EU GBS compliance assessment (Regulation 2023/2631)",
)
def assess_issuance(request: IssuanceInputModel) -> Dict[str, Any]:
    """
    Assess an EU Green Bond issuance against all Regulation (EU) 2023/2631 requirements.
    Returns compliance score, blocking gaps, GBFS completeness, and priority actions.
    """
    inp = IssuanceInput(
        bond_id=request.bond_id,
        issuer_name=request.issuer_name,
        bond_type=request.bond_type,
        principal_amount=request.principal_amount,
        currency=request.currency,
        taxonomy_alignment_pct=request.taxonomy_alignment_pct,
        dnsh_confirmed=request.dnsh_confirmed,
        min_safeguards_confirmed=request.min_safeguards_confirmed,
        environmental_objectives=request.environmental_objectives,
        has_external_reviewer=request.has_external_reviewer,
        er_name=request.er_name,
        has_pre_issuance_review=request.has_pre_issuance_review,
        refinancing_share_pct=request.refinancing_share_pct,
        is_sovereign=request.is_sovereign,
    )
    result = _ENGINE.assess_issuance(inp)
    return result.to_dict()


@router.post(
    "/generate-factsheet",
    summary="Generate Green Bond Factsheet (GBFS) per Regulation 2023/2631",
)
def generate_factsheet(request: IssuanceInputModel) -> Dict[str, Any]:
    """
    Generate a structured Green Bond Factsheet (GBFS) covering all 5 required sections
    (basic info, use of proceeds, allocation plan, external review, reporting commitments).
    """
    inp = IssuanceInput(
        bond_id=request.bond_id,
        issuer_name=request.issuer_name,
        bond_type=request.bond_type,
        principal_amount=request.principal_amount,
        currency=request.currency,
        taxonomy_alignment_pct=request.taxonomy_alignment_pct,
        dnsh_confirmed=request.dnsh_confirmed,
        min_safeguards_confirmed=request.min_safeguards_confirmed,
        environmental_objectives=request.environmental_objectives,
        has_external_reviewer=request.has_external_reviewer,
        er_name=request.er_name,
        has_pre_issuance_review=request.has_pre_issuance_review,
        refinancing_share_pct=request.refinancing_share_pct,
        is_sovereign=request.is_sovereign,
    )
    return _ENGINE.generate_factsheet(inp)


@router.post(
    "/allocation-report",
    summary="Post-issuance allocation report compliance check (Art 7)",
)
def allocation_report(request: AllocationReportModel) -> Dict[str, Any]:
    """
    Check post-issuance allocation report compliance:
    - Proceeds allocated >= 95%
    - Taxonomy-aligned allocation >= 100%
    - Unallocated proceeds policy documented
    """
    inp = AllocationReportInput(
        bond_id=request.bond_id,
        reporting_period=request.reporting_period,
        total_allocated_pct=request.total_allocated_pct,
        taxonomy_aligned_pct=request.taxonomy_aligned_pct,
        allocation_by_objective=request.allocation_by_objective,
        unallocated_pct=request.unallocated_pct,
        geographic_breakdown=request.geographic_breakdown,
    )
    return _ENGINE.assess_allocation_report(inp)


@router.post(
    "/impact-report",
    summary="Post-issuance impact report compliance check (Art 8)",
)
def impact_report(request: ImpactReportModel) -> Dict[str, Any]:
    """
    Check post-issuance impact report compliance:
    - Impact indicators reported
    - Measurement methodology described
    - Taxonomy alignment of funded assets maintained
    """
    inp = ImpactReportInput(
        bond_id=request.bond_id,
        reporting_period=request.reporting_period,
        impact_indicators=request.impact_indicators,
        methodology_description=request.methodology_description,
        alignment_maintained=request.alignment_maintained,
    )
    return _ENGINE.assess_impact_report(inp)


@router.post(
    "/assess/batch",
    summary="Batch EU GBS issuance assessments",
)
def assess_batch(requests: List[IssuanceInputModel]) -> List[Dict[str, Any]]:
    """
    Assess multiple EU Green Bond issuances in a single request.
    """
    results = []
    for request in requests:
        inp = IssuanceInput(
            bond_id=request.bond_id,
            issuer_name=request.issuer_name,
            bond_type=request.bond_type,
            principal_amount=request.principal_amount,
            currency=request.currency,
            taxonomy_alignment_pct=request.taxonomy_alignment_pct,
            dnsh_confirmed=request.dnsh_confirmed,
            min_safeguards_confirmed=request.min_safeguards_confirmed,
            environmental_objectives=request.environmental_objectives,
            has_external_reviewer=request.has_external_reviewer,
            er_name=request.er_name,
            has_pre_issuance_review=request.has_pre_issuance_review,
            refinancing_share_pct=request.refinancing_share_pct,
            is_sovereign=request.is_sovereign,
        )
        result = _ENGINE.assess_issuance(inp)
        results.append(result.to_dict())
    return results


# ---------------------------------------------------------------------------
# Reference Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/ref/bond-types",
    summary="EU GBS eligible bond type definitions",
)
def ref_bond_types() -> Dict[str, Any]:
    return _ENGINE.get_bond_types()


@router.get(
    "/ref/taxonomy-objectives",
    summary="6 EU Taxonomy environmental objectives (CCM/CCA/WMR/CE/PPE/BIO)",
)
def ref_taxonomy_objectives() -> Dict[str, Any]:
    return _ENGINE.get_taxonomy_objectives()


@router.get(
    "/ref/er-requirements",
    summary="External Reviewer requirements — Arts 22-24 Regulation 2023/2631",
)
def ref_er_requirements() -> Dict[str, str]:
    return _ENGINE.get_er_requirements()


@router.get(
    "/ref/standards-comparison",
    summary="EU GBS vs ICMA Green Bond Principles vs Climate Bonds Standard comparison",
)
def ref_standards_comparison() -> Dict[str, Any]:
    return _ENGINE.compare_standards()


@router.get(
    "/ref/timeline",
    summary="EUGBS regulatory timeline (2023-2026)",
)
def ref_timeline() -> List[Dict[str, str]]:
    return _ENGINE.get_timeline()
