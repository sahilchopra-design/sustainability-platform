"""
API Routes — Climate Stress Test Engine (Sprint 26)
=====================================================
POST /api/v1/climate-stress-test/bcbs-517
POST /api/v1/climate-stress-test/boe-cbes
POST /api/v1/climate-stress-test/ecb-cst
POST /api/v1/climate-stress-test/apra-clt
POST /api/v1/climate-stress-test/cross-framework
POST /api/v1/climate-stress-test/portfolio-resilience
GET  /api/v1/climate-stress-test/ref/frameworks
GET  /api/v1/climate-stress-test/ref/ngfs-scenarios
GET  /api/v1/climate-stress-test/ref/damage-functions
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.climate_stress_test_engine import (
    ClimateStressTestEngine,
    SUPERVISOR_FRAMEWORKS,
    NGFS_PHASE4_SCENARIOS,
    PHYSICAL_HAZARD_DAMAGE_FUNCTIONS,
    SECTOR_TRANSITION_SENSITIVITY,
    CAPITAL_ADEQUACY_FLOORS,
)

router = APIRouter(prefix="/api/v1/climate-stress-test", tags=["climate_stress_test"])
_engine = ClimateStressTestEngine()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class BCBS517Request(BaseModel):
    entity_id: str
    institution_type: str = "bank"
    portfolio_sectors: dict[str, float] = Field(
        default_factory=lambda: {
            "financials": 0.4,
            "real_estate_brown": 0.3,
            "oil_gas": 0.2,
            "technology": 0.1,
        }
    )
    total_assets_usd: float = Field(default=50_000_000_000)
    cet1_ratio_pct: float = Field(default=14.5, ge=0, le=50)
    scenario: str = "delayed_transition"


class BoECBESRequest(BaseModel):
    entity_id: str
    institution_type: str = "bank"
    uk_mortgage_exposure_pct: float = Field(default=35.0, ge=0, le=100)
    uk_corporate_exposure_pct: float = Field(default=30.0, ge=0, le=100)
    scenario: str = "late_action"


class ECBCSTRequest(BaseModel):
    entity_id: str
    institution_type: str = "bank"
    eu_sector_exposures: dict[str, float] = Field(
        default_factory=lambda: {
            "oil_gas": 0.15,
            "utilities_fossil": 0.20,
            "real_estate_brown": 0.35,
            "financials": 0.30,
        }
    )
    total_rwa_usd: float = Field(default=20_000_000_000)
    scenario: str = "disorderly"


class APRACLTRequest(BaseModel):
    entity_id: str
    institution_type: str = "bank"
    australian_exposure_pct: float = Field(default=30.0, ge=0, le=100)
    scenario: str = "delayed_transition"


class CrossFrameworkRequest(BaseModel):
    entity_id: str
    institution_type: str = "bank"
    portfolio_sectors: dict[str, float] = Field(
        default_factory=lambda: {
            "financials": 0.4,
            "real_estate_brown": 0.3,
            "oil_gas": 0.2,
            "technology": 0.1,
        }
    )
    total_assets_usd: float = Field(default=50_000_000_000)
    cet1_pct: float = Field(default=14.5, ge=0, le=50)
    scenario: str = "delayed_transition"


class PortfolioItem(BaseModel):
    portfolio_id: str
    cet1_pct: float = 14.0
    total_assets_usd: float = 1_000_000_000
    institution_type: str = "bank"


class PortfolioResilienceRequest(BaseModel):
    entity_id: str
    portfolios: list[PortfolioItem] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# POST endpoints
# ---------------------------------------------------------------------------

@router.post("/bcbs-517")
async def bcbs_517(req: BCBS517Request):
    try:
        return _engine.run_bcbs_517(
            entity_id=req.entity_id,
            institution_type=req.institution_type,
            portfolio_sectors=req.portfolio_sectors,
            total_assets_usd=req.total_assets_usd,
            cet1_ratio_pct=req.cet1_ratio_pct,
            scenario=req.scenario,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/boe-cbes")
async def boe_cbes(req: BoECBESRequest):
    try:
        return _engine.run_boe_cbes(
            entity_id=req.entity_id,
            institution_type=req.institution_type,
            uk_mortgage_exposure_pct=req.uk_mortgage_exposure_pct,
            uk_corporate_exposure_pct=req.uk_corporate_exposure_pct,
            scenario=req.scenario,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/ecb-cst")
async def ecb_cst(req: ECBCSTRequest):
    try:
        return _engine.run_ecb_cst(
            entity_id=req.entity_id,
            institution_type=req.institution_type,
            eu_sector_exposures=req.eu_sector_exposures,
            total_rwa_usd=req.total_rwa_usd,
            scenario=req.scenario,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/apra-clt")
async def apra_clt(req: APRACLTRequest):
    try:
        return _engine.run_apra_clt(
            entity_id=req.entity_id,
            institution_type=req.institution_type,
            australian_exposure_pct=req.australian_exposure_pct,
            scenario=req.scenario,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/cross-framework")
async def cross_framework(req: CrossFrameworkRequest):
    try:
        return _engine.run_cross_framework(
            entity_id=req.entity_id,
            institution_type=req.institution_type,
            portfolio_sectors=req.portfolio_sectors,
            total_assets_usd=req.total_assets_usd,
            cet1_pct=req.cet1_pct,
            scenario=req.scenario,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/portfolio-resilience")
async def portfolio_resilience(req: PortfolioResilienceRequest):
    try:
        portfolios_raw = [p.model_dump() for p in req.portfolios]
        return _engine.assess_portfolio_resilience(
            entity_id=req.entity_id,
            portfolios=portfolios_raw,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# GET reference endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/frameworks")
async def ref_frameworks():
    try:
        return {
            "frameworks": SUPERVISOR_FRAMEWORKS,
            "capital_adequacy_floors": CAPITAL_ADEQUACY_FLOORS,
            "total_frameworks": len(SUPERVISOR_FRAMEWORKS),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/ngfs-scenarios")
async def ref_ngfs_scenarios():
    try:
        by_type: dict[str, list] = {}
        for name, meta in NGFS_PHASE4_SCENARIOS.items():
            t = meta["scenario_type"]
            if t not in by_type:
                by_type[t] = []
            by_type[t].append({"scenario": name, **meta})
        return {
            "scenarios": NGFS_PHASE4_SCENARIOS,
            "by_type": by_type,
            "total": len(NGFS_PHASE4_SCENARIOS),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/damage-functions")
async def ref_damage_functions():
    try:
        return {
            "physical_hazard_damage_functions": PHYSICAL_HAZARD_DAMAGE_FUNCTIONS,
            "sector_transition_sensitivity": SECTOR_TRANSITION_SENSITIVITY,
            "total_hazards": len(PHYSICAL_HAZARD_DAMAGE_FUNCTIONS),
            "total_sectors": len(SECTOR_TRANSITION_SENSITIVITY),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
