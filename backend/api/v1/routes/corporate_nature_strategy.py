"""
API Routes: Corporate Nature Strategy & SBTN Engine — E80
==========================================================
POST /api/v1/corporate-nature-strategy/sbtn-steps          — SBTN 5-step assessment
POST /api/v1/corporate-nature-strategy/tnfd-disclosure     — TNFD v1.0 disclosure scoring
POST /api/v1/corporate-nature-strategy/nrl-exposure        — EU NRL 2024/1991 habitat exposure
POST /api/v1/corporate-nature-strategy/gbf-target3         — GBF Target 3 (30x30) exposure
POST /api/v1/corporate-nature-strategy/encore-dependencies — ENCORE ecosystem service dependencies
POST /api/v1/corporate-nature-strategy/full-assessment     — Complete nature strategy assessment
GET  /api/v1/corporate-nature-strategy/ref/sbtn-sectors    — SBTN sector impact map (11 sectors)
GET  /api/v1/corporate-nature-strategy/ref/tnfd-metrics    — 14 TNFD core metrics
GET  /api/v1/corporate-nature-strategy/ref/nrl-habitats    — EU NRL habitat types and targets
GET  /api/v1/corporate-nature-strategy/ref/encore-services — 21 ENCORE ecosystem services

References:
  - SBTN Step Guidance v1.1 (2023)
  - TNFD Recommendations v1.0 (Sep 2023)
  - Regulation (EU) 2024/1991 — Nature Restoration Law
  - CBD Kunming-Montreal GBF Target 3 (Dec 2022)
  - ENCORE v2.1 — NCFA / UNEP-WCMC (2023)
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.corporate_nature_strategy_engine import CorporateNatureStrategyEngine

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/corporate-nature-strategy",
    tags=["Corporate Nature Strategy (E80)"],
)

engine = CorporateNatureStrategyEngine()


# ---------------------------------------------------------------------------
# Pydantic Request Models
# ---------------------------------------------------------------------------

class LocationItem(BaseModel):
    model_config = {"protected_namespaces": ()}

    lat: Optional[float] = None
    lng: Optional[float] = None
    country: str = ""
    area_ha: float = Field(default=0.0, ge=0)
    site_name: Optional[str] = None
    land_use_type: Optional[str] = "intensive_agriculture"
    protected_area_overlap: Optional[bool] = False
    degradation_level: Optional[float] = Field(default=0.5, ge=0.0, le=1.0)


class TargetItem(BaseModel):
    model_config = {"protected_namespaces": ()}

    framework: str = ""           # e.g. "SBTN", "SBTi", "CBD"
    type: Optional[str] = None    # e.g. "land", "freshwater", "ghg"
    description: str = ""
    target_year: Optional[int] = None
    baseline_year: Optional[int] = None
    metric: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None


class SBTNAssessmentRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    sectors: List[str] = Field(default_factory=list)
    locations: List[LocationItem] = Field(default_factory=list)
    current_targets: List[TargetItem] = Field(default_factory=list)
    disclosures: Dict[str, Any] = Field(default_factory=dict)


class TNFDDisclosureRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    governance_data: Dict[str, Any] = Field(default_factory=dict)
    strategy_data: Dict[str, Any] = Field(default_factory=dict)
    risk_data: Dict[str, Any] = Field(default_factory=dict)
    metrics_data: Dict[str, Any] = Field(default_factory=dict)


class OperationItem(BaseModel):
    model_config = {"protected_namespaces": ()}

    site_name: Optional[str] = None
    country: str = ""
    area_ha: float = Field(default=0.0, ge=0)
    habitat_types: List[str] = Field(default_factory=list)
    degradation_level: Optional[float] = Field(default=0.5, ge=0.0, le=1.0)
    restoration_plan_filed: Optional[bool] = False


class NRLExposureRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    operations: List[OperationItem] = Field(default_factory=list)
    supply_chain_countries: List[str] = Field(default_factory=list)


class PortfolioLocationItem(BaseModel):
    model_config = {"protected_namespaces": ()}

    country: str
    exposure_m: float = Field(default=0.0, ge=0)
    asset_type: Optional[str] = "land"   # "land" or "marine"
    asset_name: Optional[str] = None


class GBFTarget3Request(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    portfolio_locations: List[PortfolioLocationItem] = Field(default_factory=list)


class EncoreAssessmentRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    sector: str
    operations_data: Dict[str, Any] = Field(default_factory=dict)


class NatureFullAssessmentRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    # SBTN
    sectors: List[str] = Field(default_factory=list)
    locations: List[LocationItem] = Field(default_factory=list)
    current_targets: List[TargetItem] = Field(default_factory=list)
    disclosures: Dict[str, Any] = Field(default_factory=dict)
    # TNFD
    governance_data: Dict[str, Any] = Field(default_factory=dict)
    strategy_data: Dict[str, Any] = Field(default_factory=dict)
    risk_data: Dict[str, Any] = Field(default_factory=dict)
    metrics_data: Dict[str, Any] = Field(default_factory=dict)
    # NRL
    operations: List[OperationItem] = Field(default_factory=list)
    supply_chain_countries: List[str] = Field(default_factory=list)
    # GBF
    portfolio_locations: List[PortfolioLocationItem] = Field(default_factory=list)
    # ENCORE
    operations_data: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# POST Endpoints
# ---------------------------------------------------------------------------

@router.post("/sbtn-steps", summary="SBTN 5-Step Assessment")
def sbtn_steps(req: SBTNAssessmentRequest):
    """
    Score SBTN 5-step readiness per SBTN Step Guidance v1.1 (2023).

    Returns per-step scores (0-100) for Assess / Interpret / Measure / Set / Disclose,
    composite SBTN score, MSA.km² footprint, high-impact sectors, and material locations.
    """
    try:
        result = engine.assess_sbtn_steps(
            entity_id=req.entity_id,
            sectors=req.sectors,
            locations=[loc.model_dump() for loc in req.locations],
            current_targets=[t.model_dump() for t in req.current_targets],
            disclosures=req.disclosures,
        )
        return {"status": "ok", "sbtn_assessment": result}
    except Exception as exc:
        logger.exception("sbtn_steps failed entity=%s", req.entity_id)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/tnfd-disclosure", summary="TNFD v1.0 Disclosure Scoring")
def tnfd_disclosure(req: TNFDDisclosureRequest):
    """
    Score TNFD v1.0 disclosure completeness across 4 pillars and 14 core metrics.

    Returns pillar scores, composite TNFD score, list of gaps, mandatory gap count.
    References TNFD Recommendations R1-R14 and LEAP approach.
    """
    try:
        result = engine.assess_tnfd_disclosure(
            entity_id=req.entity_id,
            governance_data=req.governance_data,
            strategy_data=req.strategy_data,
            risk_data=req.risk_data,
            metrics_data=req.metrics_data,
        )
        return {"status": "ok", "tnfd_assessment": result}
    except Exception as exc:
        logger.exception("tnfd_disclosure failed entity=%s", req.entity_id)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/nrl-exposure", summary="EU NRL 2024/1991 Habitat Exposure")
def nrl_exposure(req: NRLExposureRequest):
    """
    Assess EU Nature Restoration Law (EU) 2024/1991 habitat exposure for operational sites.

    Returns affected habitats, restoration liability (ha and EUR), compliance gaps,
    and NRL compliance score. Applies Art 4-12 habitat targets (30% by 2030 baseline).
    """
    try:
        result = engine.assess_nrl_exposure(
            entity_id=req.entity_id,
            operations=[op.model_dump() for op in req.operations],
            supply_chain_countries=req.supply_chain_countries,
        )
        return {"status": "ok", "nrl_assessment": result}
    except Exception as exc:
        logger.exception("nrl_exposure failed entity=%s", req.entity_id)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/gbf-target3", summary="GBF Target 3 (30x30) Portfolio Exposure")
def gbf_target3(req: GBFTarget3Request):
    """
    Map portfolio exposure to GBF Kunming-Montreal Target 3 (30x30 protection by 2030).

    Returns % portfolio in protected zones by country, countries below 30x30 threshold,
    countries with future regulatory restriction risk, and GBF alignment score.
    """
    try:
        result = engine.assess_gbf_target3(
            entity_id=req.entity_id,
            portfolio_locations=[loc.model_dump() for loc in req.portfolio_locations],
        )
        return {"status": "ok", "gbf_assessment": result}
    except Exception as exc:
        logger.exception("gbf_target3 failed entity=%s", req.entity_id)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/encore-dependencies", summary="ENCORE Ecosystem Service Dependencies")
def encore_dependencies(req: EncoreAssessmentRequest):
    """
    Score 21 ENCORE ecosystem service dependencies and impacts per ENCORE v2.1 (2023).

    Returns dependency scores, impact scores, and financial exposure for all 21 services.
    Identifies top dependencies and high-impact services for the sector.
    """
    try:
        result = engine.assess_encore_dependencies(
            entity_id=req.entity_id,
            sector=req.sector,
            operations_data=req.operations_data,
        )
        return {"status": "ok", "encore_assessment": result}
    except Exception as exc:
        logger.exception("encore_dependencies failed entity=%s", req.entity_id)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/full-assessment", summary="Complete Nature Strategy Assessment")
def full_assessment(req: NatureFullAssessmentRequest):
    """
    Run the complete Corporate Nature Strategy assessment orchestrating all 5 sub-modules.

    Composite nature_strategy_score weighted:
      SBTN 35% + TNFD 30% + NRL 15% + GBF 10% + ENCORE 10%

    Returns maturity tier (leading/advanced/developing/early/minimal), investor signal,
    regulatory flags, and priority remediation actions.
    """
    try:
        request_data = req.model_dump()
        result = engine.run_full_assessment(
            entity_id=req.entity_id,
            request_data=request_data,
        )
        return {"status": "ok", "nature_strategy_assessment": result}
    except Exception as exc:
        logger.exception("full_assessment failed entity=%s", req.entity_id)
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# GET Reference Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/sbtn-sectors", summary="SBTN Sector Impact Map")
def ref_sbtn_sectors():
    """
    Return SBTN sector impact map for 11 sectors.

    Includes primary and secondary impact drivers (land use, water extraction,
    pollution, climate change, invasive species, overexploitation), SBTN priority tier,
    and key ecosystems per sector per SBTN Step Guidance v1.1 (2023).
    """
    try:
        return {"status": "ok", "sbtn_sector_impact_map": engine.ref_sbtn_sectors()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/tnfd-metrics", summary="TNFD 14 Core Metrics")
def ref_tnfd_metrics():
    """
    Return the 14 TNFD core disclosure metrics (R1-R14) across 4 pillars.

    Pillars: Governance, Strategy, Risk & Opportunity Management, Metrics & Targets.
    Includes disclosure type (qualitative/quantitative), mandatory flag, and TNFD reference.
    Source: TNFD Recommendations and Guidance v1.0 (Sep 2023).
    """
    try:
        return {"status": "ok", "tnfd_metrics": engine.ref_tnfd_metrics(), "total_metrics": 14}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/nrl-habitats", summary="EU NRL Habitat Types and Restoration Targets")
def ref_nrl_habitats():
    """
    Return EU NRL (2024/1991) habitat type definitions and restoration targets.

    Includes 10 habitat types with restoration targets for 2030/2040/2050,
    deterioration standstill year, and applicable NRL article per habitat.
    Source: Regulation (EU) 2024/1991 on Nature Restoration.
    """
    try:
        return {"status": "ok", "nrl_habitats": engine.ref_nrl_habitats(), "regulation": "EU 2024/1991"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/encore-services", summary="ENCORE 21 Ecosystem Services")
def ref_encore_services():
    """
    Return all 21 ENCORE ecosystem services with financial dependency weightings.

    Includes provisioning, regulating, and cultural services with ENCORE codes,
    high-dependency sectors, and valuation range (USD/ha/yr).
    Source: ENCORE v2.1 — Natural Capital Finance Alliance / UNEP-WCMC (2023).
    """
    try:
        return {
            "status": "ok",
            "encore_services": engine.ref_encore_services(),
            "total_services": 21,
            "source": "ENCORE v2.1 (NCFA / UNEP-WCMC 2023)",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/gbf-countries", summary="GBF Target 3 Country Protection Data")
def ref_gbf_countries():
    """
    Return GBF Target 3 protection data for 30 countries.

    Includes current land/sea protected % and GBF commitment status.
    Source: UNEP-WCMC Protected Planet + CBD COP15 national commitments (2022).
    """
    try:
        return {
            "status": "ok",
            "gbf_target3_countries": engine.ref_gbf_countries(),
            "total_countries": 30,
            "target": "30% land + 30% ocean protected by 2030",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/maturity-tiers", summary="Nature Maturity Tiers")
def ref_maturity_tiers():
    """
    Return the 5 nature strategy maturity tier definitions with score thresholds.

    Tiers: leading (80-100) / advanced (60-79) / developing (40-59) / early (20-39) / minimal (0-19).
    Includes investor signal and regulatory flags per tier.
    """
    try:
        return {"status": "ok", "maturity_tiers": engine.ref_maturity_tiers()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
