"""
API Routes: Infrastructure Finance Engine
==========================================
POST /api/v1/infrastructure-finance/equator-principles — EP4 categorisation and scoring
POST /api/v1/infrastructure-finance/ifc-ps             — IFC PS 1-8 compliance
POST /api/v1/infrastructure-finance/oecd               — OECD Common Approaches screening
POST /api/v1/infrastructure-finance/paris-alignment    — Paris Alignment assessment
POST /api/v1/infrastructure-finance/dscr-stress        — DSCR climate stress testing
POST /api/v1/infrastructure-finance/blended-finance    — Blended finance structuring
POST /api/v1/infrastructure-finance/climate-label      — CBI/ICMA climate label eligibility
POST /api/v1/infrastructure-finance/full-assessment    — Complete infrastructure assessment
GET  /api/v1/infrastructure-finance/ref/ep-principles  — 10 EP principles
GET  /api/v1/infrastructure-finance/ref/ifc-ps         — IFC PS 1-8 descriptions
GET  /api/v1/infrastructure-finance/ref/paris-alignment — Paris Alignment criteria
GET  /api/v1/infrastructure-finance/ref/blended-structures — Blended finance structure types
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

try:
    from services.infrastructure_finance_engine import (
        InfrastructureFinanceEngine,
        EP_CATEGORIES,
        EP_10_PRINCIPLES,
        EP_SECTOR_RISKS,
        IFC_PS_DESCRIPTIONS,
        OECD_TIERS,
        PARIS_ALIGNMENT_CRITERIA,
        DSCR_CLIMATE_HAIRCUTS,
        BLENDED_FINANCE_STRUCTURES,
        CBI_STANDARD_V4_SECTORS,
        CROWDING_IN_RATIOS,
    )
    _engine = InfrastructureFinanceEngine()
except Exception:
    _engine = None
    EP_CATEGORIES = {}
    EP_10_PRINCIPLES = []
    EP_SECTOR_RISKS = {}
    IFC_PS_DESCRIPTIONS = {}
    OECD_TIERS = {}
    PARIS_ALIGNMENT_CRITERIA = {}
    DSCR_CLIMATE_HAIRCUTS = {}
    BLENDED_FINANCE_STRUCTURES = {}
    CBI_STANDARD_V4_SECTORS = []
    CROWDING_IN_RATIOS = {}

router = APIRouter(prefix="/api/v1/infrastructure-finance", tags=["Infrastructure Finance"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class EquatorPrinciplesRequest(BaseModel):
    entity_id: str
    project_type: str = "greenfield"
    sector: str = "renewables"
    country: str = "IN"
    total_cost_usd: float = Field(200_000_000.0, gt=0)
    e_s_data: dict = {}

    class Config:
        extra = "allow"


class IFCPSRequest(BaseModel):
    entity_id: str
    sector: str = "renewables"
    country: str = "IN"
    workforce_size: int = Field(200, ge=0)
    biodiversity_sensitive: bool = False
    land_acquisition: bool = False
    indigenous_peoples_present: bool = False
    cultural_heritage: bool = False

    class Config:
        extra = "allow"


class OECDRequest(BaseModel):
    entity_id: str
    sector: str = "renewables"
    country: str = "IN"
    project_type: str = "greenfield"

    class Config:
        extra = "allow"


class ParisAlignmentRequest(BaseModel):
    entity_id: str
    sector: str = "renewables"
    country: str = "IN"
    annual_ghg_tco2: float = Field(50_000.0, ge=0)
    project_lifetime_yrs: int = Field(25, gt=0)
    climate_vulnerability_score: float = Field(5.0, ge=0, le=10)

    class Config:
        extra = "allow"


class DSCRStressRequest(BaseModel):
    entity_id: str
    sector: str = "power"
    baseline_dscr: float = Field(1.45, gt=0)
    debt_service_usd_pa: float = Field(15_000_000.0, gt=0)
    physical_risk_level: str = "medium"
    transition_risk_level: str = "medium"

    class Config:
        extra = "allow"


class BlendedFinanceRequest(BaseModel):
    entity_id: str
    total_cost_usd: float = Field(200_000_000.0, gt=0)
    sector: str = "renewables"
    country: str = "IN"
    target_private_irr_pct: float = Field(12.0, gt=0)
    mdb_participation: bool = True

    class Config:
        extra = "allow"


class ClimateLabelRequest(BaseModel):
    entity_id: str
    sector: str = "renewables"
    annual_ghg_reduction: float = Field(30_000.0, ge=0)
    project_type: str = "green_bond"

    class Config:
        extra = "allow"


class FullAssessmentRequest(BaseModel):
    entity_id: str
    project_data: dict = {}

    class Config:
        extra = "allow"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _mock(entity_id: str, endpoint: str) -> dict:
    return {
        "status": "success",
        "data": {
            "entity_id": entity_id,
            "endpoint": endpoint,
            "note": "engine_unavailable_mock_response",
        },
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/equator-principles")
def equator_principles(req: EquatorPrinciplesRequest):
    """Equator Principles IV — category (A/B/C) and 10 principles scoring."""
    if _engine is None:
        return _mock(req.entity_id, "equator-principles")
    r = _engine.assess_equator_principles(
        req.entity_id, req.project_type, req.sector,
        req.country, req.total_cost_usd, req.e_s_data,
    )
    return {
        "status": "success",
        "data": {
            "entity_id": r.entity_id,
            "project_type": r.project_type,
            "sector": r.sector,
            "country": r.country,
            "total_cost_usd": r.total_cost_usd,
            "category": r.category,
            "principle_scores": r.principle_scores,
            "overall_score": r.overall_score,
            "esap_required": r.esap_required,
            "compliant": r.compliant,
            "key_gaps": r.key_gaps,
        },
    }


@router.post("/ifc-ps")
def ifc_ps(req: IFCPSRequest):
    """IFC Performance Standards 1-8 compliance assessment."""
    if _engine is None:
        return _mock(req.entity_id, "ifc-ps")
    r = _engine.assess_ifc_ps(
        req.entity_id, req.sector, req.country, req.workforce_size,
        req.biodiversity_sensitive, req.land_acquisition,
        req.indigenous_peoples_present, req.cultural_heritage,
    )
    return {
        "status": "success",
        "data": {
            "entity_id": r.entity_id,
            "sector": r.sector,
            "ps_scores": r.ps_scores,
            "composite_score": r.composite_score,
            "compliant": r.compliant,
            "gaps": r.gaps,
        },
    }


@router.post("/oecd")
def oecd(req: OECDRequest):
    """OECD Common Approaches 2022 — tier screening and notification requirements."""
    if _engine is None:
        return _mock(req.entity_id, "oecd")
    r = _engine.assess_oecd(req.entity_id, req.sector, req.country, req.project_type)
    return {
        "status": "success",
        "data": {
            "entity_id": r.entity_id,
            "sector": r.sector,
            "country": r.country,
            "tier": r.tier,
            "tier_label": r.tier_label,
            "screening_required": r.screening_required,
            "review_required": r.review_required,
            "notification_required": r.notification_required,
        },
    }


@router.post("/paris-alignment")
def paris_alignment(req: ParisAlignmentRequest):
    """IDFC Paris Alignment Framework — mitigation, adaptation, governance scoring."""
    if _engine is None:
        return _mock(req.entity_id, "paris-alignment")
    r = _engine.assess_paris_alignment(
        req.entity_id, req.sector, req.country,
        req.annual_ghg_tco2, req.project_lifetime_yrs, req.climate_vulnerability_score,
    )
    return {
        "status": "success",
        "data": {
            "entity_id": r.entity_id,
            "sector": r.sector,
            "alignment_score": r.alignment_score,
            "mitigation_aligned": r.mitigation_aligned,
            "adaptation_aligned": r.adaptation_aligned,
            "governance_aligned": r.governance_aligned,
            "overall_aligned": r.overall_aligned,
            "ghg_reduction_pa": r.ghg_reduction_pa,
            "sub_scores": r.sub_scores,
        },
    }


@router.post("/dscr-stress")
def dscr_stress(req: DSCRStressRequest):
    """DSCR climate stress testing — physical and transition risk haircuts."""
    if _engine is None:
        return _mock(req.entity_id, "dscr-stress")
    r = _engine.calculate_dscr_climate_stress(
        req.entity_id, req.sector, req.baseline_dscr,
        req.debt_service_usd_pa, req.physical_risk_level, req.transition_risk_level,
    )
    return {
        "status": "success",
        "data": {
            "entity_id": r.entity_id,
            "sector": r.sector,
            "baseline_dscr": r.baseline_dscr,
            "dscr_physical": r.dscr_physical,
            "dscr_transition": r.dscr_transition,
            "dscr_combined": r.dscr_combined,
            "breaches_covenant": r.breaches_covenant,
            "covenant_threshold": r.covenant_threshold,
            "physical_haircut_applied": r.physical_haircut_applied,
            "transition_capex_impact": r.transition_capex_impact,
        },
    }


@router.post("/blended-finance")
def blended_finance(req: BlendedFinanceRequest):
    """Blended finance structure selection, tranche breakdown and crowding-in ratio."""
    if _engine is None:
        return _mock(req.entity_id, "blended-finance")
    r = _engine.structure_blended_finance(
        req.entity_id, req.total_cost_usd, req.sector,
        req.country, req.target_private_irr_pct, req.mdb_participation,
    )
    return {
        "status": "success",
        "data": {
            "entity_id": r.entity_id,
            "total_cost_usd": r.total_cost_usd,
            "structure_type": r.structure_type,
            "tranche_breakdown": r.tranche_breakdown,
            "crowding_in_ratio": r.crowding_in_ratio,
            "private_finance_mobilised": r.private_finance_mobilised,
            "blended_irr": r.blended_irr,
            "oecd_additionality_score": r.oecd_additionality_score,
            "mdb_share_pct": r.mdb_share_pct,
        },
    }


@router.post("/climate-label")
def climate_label(req: ClimateLabelRequest):
    """CBI Standard v4 and ICMA GBP climate label eligibility assessment."""
    if _engine is None:
        return _mock(req.entity_id, "climate-label")
    r = _engine.assess_climate_label(
        req.entity_id, req.sector, req.annual_ghg_reduction, req.project_type,
    )
    return {
        "status": "success",
        "data": {
            "entity_id": r.entity_id,
            "sector": r.sector,
            "cbi_certified": r.cbi_certified,
            "eligible_cbi_sector": r.eligible_cbi_sector,
            "icma_gbf_aligned": r.icma_gbf_aligned,
            "sdg_label": r.sdg_label,
            "eligible_taxonomies": r.eligible_taxonomies,
            "annual_ghg_reduction": r.annual_ghg_reduction,
        },
    }


@router.post("/full-assessment")
def full_assessment(req: FullAssessmentRequest):
    """Consolidated infrastructure finance assessment across all frameworks."""
    if _engine is None:
        return _mock(req.entity_id, "full-assessment")
    r = _engine.generate_full_assessment(req.entity_id, req.project_data)
    return {"status": "success", "data": r}


# ---------------------------------------------------------------------------
# Reference Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/ep-principles")
def ref_ep_principles():
    """Equator Principles IV — all 10 principles with descriptions and weights."""
    return {
        "status": "success",
        "data": {
            "principles": EP_10_PRINCIPLES,
            "categories": EP_CATEGORIES,
            "sector_default_categories": EP_SECTOR_RISKS,
        },
    }


@router.get("/ref/ifc-ps")
def ref_ifc_ps():
    """IFC Performance Standards 1-8 — descriptions, key requirements and weights."""
    return {"status": "success", "data": IFC_PS_DESCRIPTIONS}


@router.get("/ref/paris-alignment")
def ref_paris_alignment():
    """IDFC Paris Alignment Framework — mitigation/adaptation/governance criteria."""
    return {
        "status": "success",
        "data": {
            "criteria": PARIS_ALIGNMENT_CRITERIA,
            "oecd_tiers": OECD_TIERS,
            "dscr_climate_haircuts": DSCR_CLIMATE_HAIRCUTS,
        },
    }


@router.get("/ref/blended-structures")
def ref_blended_structures():
    """Blended finance structure types — descriptions, components and crowding-in ratios."""
    return {
        "status": "success",
        "data": {
            "structures": BLENDED_FINANCE_STRUCTURES,
            "crowding_in_ratios": CROWDING_IN_RATIOS,
            "cbi_eligible_sectors": CBI_STANDARD_V4_SECTORS,
        },
    }
