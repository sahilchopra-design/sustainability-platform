"""
Asset Management Engine Routes
POST /api/v1/am/esg-attribution        — ESG factor attribution (Fama-French + ESG)
POST /api/v1/am/paris-alignment        — Portfolio temperature scoring (PACTA)
POST /api/v1/am/green-bond-screening   — ICMA GBS / EU GBS eligibility
POST /api/v1/am/climate-spreads        — Climate-adjusted credit spreads
POST /api/v1/am/lp-analytics           — LP concentration & liquidity coverage
POST /api/v1/am/optimise               — ESG-constrained portfolio optimisation
GET  /api/v1/am/reference-data         — All AM reference data
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from db.base import get_db
from services.am_engine import (
    Holding,
    BondInput,
    IssuerInput,
    InvestorProfile,
    OptimisationConstraints,
    calculate_esg_attribution,
    calculate_paris_alignment,
    screen_green_bonds,
    calculate_climate_adjusted_spreads,
    calculate_lp_analytics,
    optimise_esg_portfolio,
    get_am_reference_data,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/am",
    tags=["Asset Management Engine"],
)


# ── Request / Response Models ─────────────────────────────────────────────

class HoldingModel(BaseModel):
    security_id: str
    name: str
    weight_pct: float = 5.0
    sector: str = "default"
    esg_score: float = 50.0
    carbon_intensity_tco2e_m: float = 180.0
    return_pct: float = 0.0
    benchmark_weight_pct: float = 0.0
    benchmark_return_pct: float = 0.0
    rating: str = "BBB"


class ESGAttributionRequest(BaseModel):
    holdings: List[HoldingModel]
    benchmark_esg_score: float = 50.0
    save_to_db: bool = True


class ParisAlignmentRequest(BaseModel):
    holdings: List[HoldingModel]
    target_pathway: str = "1.5C"
    base_year: int = 2024
    save_to_db: bool = True


class BondModel(BaseModel):
    bond_id: str
    issuer_name: str
    isin: str = ""
    rating: str = "BBB"
    sector: str = "default"
    use_of_proceeds: List[str] = []
    taxonomy_aligned_pct: float = 0.0
    external_review: bool = False
    impact_reporting: bool = False
    dnsh_assessed: bool = False
    coupon_bps: float = 0.0
    conventional_spread_bps: float = 0.0


class GreenBondRequest(BaseModel):
    bonds: List[BondModel]


class IssuerModel(BaseModel):
    issuer_id: str
    name: str
    sector: str = "default"
    rating: str = "BBB"
    base_spread_bps: float = 150.0
    carbon_intensity_tco2e_m: float = 180.0
    transition_risk_score: float = 50.0
    revenue_from_fossils_pct: float = 0.0
    capex_green_pct: float = 0.0
    sbti_committed: bool = False


class ClimateSpreadRequest(BaseModel):
    issuers: List[IssuerModel]
    carbon_price_eur: float = 80.0
    warming_scenario: str = "2C"


class InvestorModel(BaseModel):
    investor_id: str
    name: str
    commitment_eur: float
    investor_type: str = "institutional"
    redemption_notice_days: int = 30
    lock_up_remaining_months: int = 0
    historical_redemption_rate: float = 0.05


class LPAnalyticsRequest(BaseModel):
    fund_aum_eur: float
    investors: List[InvestorModel]
    liquid_assets_pct: float = 30.0
    side_pocket_pct: float = 0.0


class ConstraintsModel(BaseModel):
    min_esg_score: float = 0.0
    max_carbon_intensity: float = 999.0
    excluded_sectors: List[str] = []
    excluded_securities: List[str] = []
    max_single_weight_pct: float = 10.0
    max_sector_weight_pct: float = 30.0
    max_tracking_error_pct: float = 3.0
    esg_tilt_strength: float = 0.5


class OptimiseRequest(BaseModel):
    holdings: List[HoldingModel]
    constraints: ConstraintsModel = ConstraintsModel()
    risk_free_rate: float = 3.5


# ── Helper ─────────────────────────────────────────────────────────────────

def _to_holdings(models: List[HoldingModel]) -> List[Holding]:
    return [
        Holding(
            security_id=m.security_id, name=m.name, weight_pct=m.weight_pct,
            sector=m.sector, esg_score=m.esg_score,
            carbon_intensity_tco2e_m=m.carbon_intensity_tco2e_m,
            return_pct=m.return_pct, benchmark_weight_pct=m.benchmark_weight_pct,
            benchmark_return_pct=m.benchmark_return_pct, rating=m.rating,
        )
        for m in models
    ]


# ── Routes ─────────────────────────────────────────────────────────────────

@router.post("/esg-attribution")
def esg_attribution(req: ESGAttributionRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Fama-French + ESG factor attribution with Brinson selection/allocation."""
    holdings = _to_holdings(req.holdings)
    result = calculate_esg_attribution(holdings, req.benchmark_esg_score)

    if req.save_to_db:
        try:
            rid = str(uuid.uuid4())
            db.execute(text("""
                INSERT INTO am_assessments (id, module, payload, created_at)
                VALUES (:id, 'esg_attribution', :payload::jsonb, NOW())
            """), {"id": rid, "payload": str({
                "active_return_bps": result.active_return_bps,
                "esg_quality_bps": result.esg_quality_contribution_bps,
                "portfolio_esg": result.portfolio_esg_score,
            })})
            db.commit()
        except Exception as e:
            logger.warning("DB save failed: %s", e)
            db.rollback()

    return result.__dict__


@router.post("/paris-alignment")
def paris_alignment(req: ParisAlignmentRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Portfolio temperature scoring using PACTA methodology."""
    holdings = _to_holdings(req.holdings)
    result = calculate_paris_alignment(holdings, req.target_pathway, req.base_year)

    if req.save_to_db:
        try:
            rid = str(uuid.uuid4())
            db.execute(text("""
                INSERT INTO am_assessments (id, module, payload, created_at)
                VALUES (:id, 'paris_alignment', :payload::jsonb, NOW())
            """), {"id": rid, "payload": str({
                "temperature_c": result.portfolio_temperature_c,
                "gap_c": result.alignment_gap_c,
                "waci": result.weighted_carbon_intensity,
            })})
            db.commit()
        except Exception as e:
            logger.warning("DB save failed: %s", e)
            db.rollback()

    return {
        "portfolio_temperature_c": result.portfolio_temperature_c,
        "target_pathway": result.target_pathway,
        "target_temperature_c": result.target_temperature_c,
        "alignment_gap_c": result.alignment_gap_c,
        "alignment_gap_pct": result.alignment_gap_pct,
        "aligned_weight_pct": result.aligned_weight_pct,
        "misaligned_weight_pct": result.misaligned_weight_pct,
        "laggard_holdings": result.laggard_holdings,
        "sector_temperatures": result.sector_temperatures,
        "trajectory_years": result.trajectory_years,
        "trajectory_portfolio_c": result.trajectory_portfolio_c,
        "trajectory_target_c": result.trajectory_target_c,
        "weighted_carbon_intensity": result.weighted_carbon_intensity,
    }


@router.post("/green-bond-screening")
def green_bond_screening(req: GreenBondRequest) -> List[Dict[str, Any]]:
    """Screen bond universe against ICMA GBS / EU GBS criteria."""
    bonds = [
        BondInput(
            bond_id=b.bond_id, issuer_name=b.issuer_name, isin=b.isin,
            rating=b.rating, sector=b.sector, use_of_proceeds=b.use_of_proceeds,
            taxonomy_aligned_pct=b.taxonomy_aligned_pct,
            external_review=b.external_review, impact_reporting=b.impact_reporting,
            dnsh_assessed=b.dnsh_assessed, coupon_bps=b.coupon_bps,
            conventional_spread_bps=b.conventional_spread_bps,
        )
        for b in req.bonds
    ]
    results = screen_green_bonds(bonds)
    return [r.__dict__ for r in results]


@router.post("/climate-spreads")
def climate_spreads(req: ClimateSpreadRequest) -> List[Dict[str, Any]]:
    """Climate-adjusted credit spreads with transition risk overlay."""
    issuers = [
        IssuerInput(
            issuer_id=i.issuer_id, name=i.name, sector=i.sector,
            rating=i.rating, base_spread_bps=i.base_spread_bps,
            carbon_intensity_tco2e_m=i.carbon_intensity_tco2e_m,
            transition_risk_score=i.transition_risk_score,
            revenue_from_fossils_pct=i.revenue_from_fossils_pct,
            capex_green_pct=i.capex_green_pct, sbti_committed=i.sbti_committed,
        )
        for i in req.issuers
    ]
    results = calculate_climate_adjusted_spreads(issuers, req.carbon_price_eur, req.warming_scenario)
    return [r.__dict__ for r in results]


@router.post("/lp-analytics")
def lp_analytics(req: LPAnalyticsRequest) -> Dict[str, Any]:
    """LP concentration analysis and liquidity coverage ratio."""
    investors = [
        InvestorProfile(
            investor_id=i.investor_id, name=i.name,
            commitment_eur=i.commitment_eur, investor_type=i.investor_type,
            redemption_notice_days=i.redemption_notice_days,
            lock_up_remaining_months=i.lock_up_remaining_months,
            historical_redemption_rate=i.historical_redemption_rate,
        )
        for i in req.investors
    ]
    result = calculate_lp_analytics(
        req.fund_aum_eur, investors, req.liquid_assets_pct, req.side_pocket_pct,
    )
    return result.__dict__


@router.post("/optimise")
def optimise(req: OptimiseRequest) -> Dict[str, Any]:
    """ESG-constrained mean-variance portfolio optimisation."""
    holdings = _to_holdings(req.holdings)
    constraints = OptimisationConstraints(
        min_esg_score=req.constraints.min_esg_score,
        max_carbon_intensity=req.constraints.max_carbon_intensity,
        excluded_sectors=req.constraints.excluded_sectors,
        excluded_securities=req.constraints.excluded_securities,
        max_single_weight_pct=req.constraints.max_single_weight_pct,
        max_sector_weight_pct=req.constraints.max_sector_weight_pct,
        max_tracking_error_pct=req.constraints.max_tracking_error_pct,
        esg_tilt_strength=req.constraints.esg_tilt_strength,
    )
    result = optimise_esg_portfolio(holdings, constraints, req.risk_free_rate)
    return result.__dict__


@router.get("/reference-data")
def reference_data() -> Dict[str, Any]:
    """Return all reference data used by the AM Engine."""
    return get_am_reference_data()
