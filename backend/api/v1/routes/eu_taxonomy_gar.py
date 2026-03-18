"""
API Routes: EU Taxonomy GAR/BTAR Reporter Engine (E19)
=======================================================
POST /api/v1/eu-taxonomy-gar/calculate-gar          — Calculate GAR, BTAR for a credit institution
POST /api/v1/eu-taxonomy-gar/assess-dnsh            — Assess DNSH compliance per asset
POST /api/v1/eu-taxonomy-gar/assess-min-safeguards  — Assess Minimum Safeguards (entity level)
POST /api/v1/eu-taxonomy-gar/calculate-gar/batch    — Batch: multiple entities
GET  /api/v1/eu-taxonomy-gar/ref/asset-classes      — GAR_ASSET_CLASSES reference
GET  /api/v1/eu-taxonomy-gar/ref/dnsh-objectives    — DNSH_OBJECTIVES reference
GET  /api/v1/eu-taxonomy-gar/ref/min-safeguards     — MINIMUM_SAFEGUARDS reference
GET  /api/v1/eu-taxonomy-gar/ref/gar-phases         — GAR_PHASES reference
GET  /api/v1/eu-taxonomy-gar/ref/cross-framework    — TAXONOMY_CROSS_FRAMEWORK reference
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.eu_taxonomy_gar_engine import (
    EUTaxonomyGAREngine,
    AssetExposure,
    GAR_ASSET_CLASSES,
    DNSH_OBJECTIVES,
    MINIMUM_SAFEGUARDS,
    GAR_PHASES,
    TAXONOMY_CROSS_FRAMEWORK,
)

router = APIRouter(
    prefix="/api/v1/eu-taxonomy-gar",
    tags=["EU Taxonomy — GAR/BTAR Reporter (Art 8 Delegated Act)"],
)

_ENGINE = EUTaxonomyGAREngine()


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class AssetExposureModel(BaseModel):
    asset_id: str = Field(..., description="Unique asset / counterparty identifier")
    asset_class: str = Field(
        ...,
        description=(
            "Asset class key — see /ref/asset-classes: "
            "financial_corporations_eq | non_financial_corporations_debt | "
            "mortgages | auto_loans | project_finance | sovereigns | ..."
        ),
    )
    total_exposure: float = Field(..., gt=0, description="Total on-balance-sheet exposure (EUR)")
    taxonomy_eligible_pct: float = Field(
        0.0, ge=0.0, le=100.0,
        description="% of exposure in taxonomy-eligible economic activities"
    )
    taxonomy_aligned_pct: float = Field(
        0.0, ge=0.0, le=100.0,
        description="% of exposure in taxonomy-aligned activities (eligible + TSC + DNSH + MS)"
    )
    dnsh_confirmed: List[str] = Field(
        default_factory=list,
        description="DNSH objectives confirmed: CCM | CCA | WMR | CE | PPE | BIO"
    )
    min_safeguards_confirmed: bool = Field(
        False,
        description="Minimum safeguards (UNGC/OECD/UNGP/ILO) confirmed for counterparty"
    )
    environmental_objective: str = Field(
        "CCM",
        description="Primary environmental objective: CCM | CCA | WMR | CE | PPE | BIO",
    )
    nace_code: str = Field("", description="NACE Rev 2 code of the counterparty's primary activity")
    notes: str = Field("", description="Optional notes on alignment evidence")


class GARCalculationModel(BaseModel):
    entity_id: str
    entity_name: str
    reporting_year: int = Field(2024, description="Reporting year (Phase 2 full disclosure from 2024)")
    assets: List[AssetExposureModel] = Field(..., description="List of covered asset exposures")


class MinSafeguardsModel(BaseModel):
    entity_id: str
    entity_name: str
    ungc_compliant: bool = Field(False, description="UNGC Ten Principles: no violations")
    oecd_compliant: bool = Field(False, description="OECD Guidelines for MNEs: compliant")
    ungp_compliant: bool = Field(False, description="UNGP Pillar II due diligence applied")
    ilo_compliant: bool = Field(False, description="ILO core labour conventions: no violations")
    udhr_compliant: bool = Field(False, description="UN Declaration of Human Rights: respected")


class DNSHAssessmentRequestModel(BaseModel):
    assets: List[AssetExposureModel] = Field(
        ..., description="Assets to assess for DNSH compliance"
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_asset(m: AssetExposureModel) -> AssetExposure:
    return AssetExposure(
        asset_id=m.asset_id,
        asset_class=m.asset_class,
        total_exposure=m.total_exposure,
        taxonomy_eligible_pct=m.taxonomy_eligible_pct,
        taxonomy_aligned_pct=m.taxonomy_aligned_pct,
        dnsh_confirmed=m.dnsh_confirmed,
        min_safeguards_confirmed=m.min_safeguards_confirmed,
        environmental_objective=m.environmental_objective,
        nace_code=m.nace_code,
        notes=m.notes,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/calculate-gar", summary="Calculate GAR and BTAR for a credit institution")
def calculate_gar(body: GARCalculationModel) -> Dict[str, Any]:
    """
    Calculate the Green Asset Ratio (GAR) and Banking Book Taxonomy Alignment
    Ratio (BTAR) for a credit institution's covered asset portfolio.

    GAR numerator = exposures that are taxonomy-aligned AND all 6 DNSH objectives
    confirmed AND Minimum Safeguards confirmed.

    Returns asset breakdown, DNSH assessments, gaps, and recommendations.
    """
    assets = [_to_asset(a) for a in body.assets]
    result = _ENGINE.calculate_gar(
        entity_id=body.entity_id,
        entity_name=body.entity_name,
        reporting_year=body.reporting_year,
        assets=assets,
    )
    return result.dict()


@router.post("/assess-dnsh", summary="Assess DNSH compliance per asset")
def assess_dnsh(body: DNSHAssessmentRequestModel) -> List[Dict[str, Any]]:
    """
    Assess DNSH (Do No Significant Harm) compliance for a list of assets
    against all 6 EU Taxonomy environmental objectives.

    Returns per-asset DNSH results: objectives passed, failed, and compliance gaps.
    """
    assets = [_to_asset(a) for a in body.assets]
    results = _ENGINE.assess_dnsh(assets)
    return [r.dict() for r in results]


@router.post("/assess-min-safeguards", summary="Assess Minimum Safeguards at entity level")
def assess_min_safeguards(body: MinSafeguardsModel) -> Dict[str, Any]:
    """
    Assess whether an entity meets the EU Taxonomy Minimum Safeguards requirements:
    UNGC, OECD Guidelines for MNEs, UN Guiding Principles on Business & Human Rights,
    and ILO Core Conventions.

    All four are blocking; UDHR is advisory.
    """
    result = _ENGINE.assess_min_safeguards(
        entity_id=body.entity_id,
        entity_name=body.entity_name,
        ungc=body.ungc_compliant,
        oecd=body.oecd_compliant,
        ungp=body.ungp_compliant,
        ilo=body.ilo_compliant,
        udhr=body.udhr_compliant,
    )
    return result.dict()


@router.post("/calculate-gar/batch", summary="Batch GAR calculation for multiple entities")
def calculate_gar_batch(body: List[GARCalculationModel]) -> List[Dict[str, Any]]:
    """
    Calculate GAR/BTAR for multiple credit institutions or reporting entities
    in a single call. Useful for group-level consolidated reporting.
    """
    results = []
    for b in body:
        assets = [_to_asset(a) for a in b.assets]
        result = _ENGINE.calculate_gar(
            entity_id=b.entity_id,
            entity_name=b.entity_name,
            reporting_year=b.reporting_year,
            assets=assets,
        )
        results.append(result.dict())
    return results


@router.get("/ref/asset-classes", summary="GAR/BTAR eligible asset classes")
def ref_asset_classes() -> Dict[str, Any]:
    """Return GAR_ASSET_CLASSES — 11 asset classes with GAR eligibility,
    BTAR eligibility, numerator conditions, and Article references per
    Art 8 Delegated Act Annex V."""
    return _ENGINE.get_asset_classes()


@router.get("/ref/dnsh-objectives", summary="6 DNSH environmental objectives")
def ref_dnsh_objectives() -> Dict[str, str]:
    """Return DNSH_OBJECTIVES — 6 EU Taxonomy DNSH environmental objectives
    (CCM, CCA, WMR, CE, PPE, BIO) with descriptions."""
    return _ENGINE.get_dnsh_objectives()


@router.get("/ref/min-safeguards", summary="Minimum Safeguards requirements")
def ref_min_safeguards() -> Dict[str, Any]:
    """Return MINIMUM_SAFEGUARDS — 5 minimum safeguards requirements
    (UNGC, OECD MNE, UNGP, ILO Core Conventions, UDHR) with blocking flags."""
    return _ENGINE.get_min_safeguards()


@router.get("/ref/gar-phases", summary="GAR disclosure phase timeline")
def ref_gar_phases() -> Dict[str, Any]:
    """Return GAR_PHASES — Phase 1 (2022-23 eligibility) and Phase 2
    (2024+ full alignment) disclosure requirements."""
    return _ENGINE.get_gar_phases()


@router.get("/ref/cross-framework", summary="Cross-framework mapping (CSRD, EU GBS, SFDR, MiFID, CBI)")
def ref_cross_framework() -> Dict[str, str]:
    """Return TAXONOMY_CROSS_FRAMEWORK — linkage between EU Taxonomy GAR/BTAR
    and CSRD ESRS E1, EU Green Bond Standard, SFDR PAI 14, MiFID II Category A,
    and Climate Bonds Initiative."""
    return _ENGINE.get_cross_framework()
