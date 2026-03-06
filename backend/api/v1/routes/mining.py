"""
Mining & Extractives Climate Risk Routes
POST /api/v1/mining/calculate
GET  /api/v1/mining/reference-data
GET  /api/v1/mining/assessments
GET  /api/v1/mining/assessments/{assessment_id}

Methodology: GISTM 2020, IEA Critical Minerals 2023, NGFS Phase 4 carbon price,
             ICMM water framework, UNEP FI stranded asset model.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from db.base import get_db
from services.mining_risk_calculator import (
    MiningRiskInput,
    calculate_mining_risk,
    get_reference_data as get_mining_reference,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/mining",
    tags=["Mining & Extractives Climate Risk"],
)


# ── Request / Response models ──────────────────────────────────────────────────

class MiningCalculateRequest(BaseModel):
    entity_name: str
    commodity: str = "copper"                     # copper | cobalt | lithium | coal | gold | ...
    country_code: str = "CL"                      # ISO 3166-1 alpha-2
    mine_type: str = "open_cut"                   # open_cut | underground | placer | ISL
    annual_production_kt: float = 100.0           # kt / yr
    reserve_life_years: float = 20.0
    book_value_usd: float = 0.0
    annual_revenue_usd: float = 0.0
    # Tailings
    tailings_volume_m3: float = 0.0
    tailings_consequence_class: str = "HIGH"      # EXTREME | VERY_HIGH | HIGH | LOW
    gistm_compliance_level: str = "partial"       # full | partial | non_compliant
    # Water
    water_annual_withdrawal_m3: float = 0.0
    water_recycling_rate: float = 0.5             # 0-1
    # Emissions
    scope1_tco2e: float = 0.0
    scope2_tco2e: float = 0.0
    # Closure
    mine_closure_year: int = 2045
    # Scenario
    scenario: str = "2C"                          # 1.5C | 2C | 3C
    horizon_year: int = 2050
    save_to_db: bool = True
    entity_id: Optional[str] = None


class MiningCalculateResponse(BaseModel):
    assessment_id: Optional[str]
    entity_name: str
    scenario: str
    horizon_year: int
    # Tailings
    tailings_annual_failure_prob: float
    tailings_expected_loss_usd: float
    tailings_compliance_flag: str
    # Water
    water_intensity_m3_per_kt: float
    water_stress_score: float
    water_at_risk_m3_yr: float
    # Carbon cost
    carbon_cost_usd: float
    carbon_cost_as_pct_revenue: float
    # Closure cost
    closure_cost_usd: float
    closure_npv_usd: float
    closure_underfunding_usd: float
    # Critical minerals
    critical_mineral_hhi: float
    supply_concentration_risk: str
    transition_demand_exposure: str
    # Stranding
    stranded_asset_risk_pct: float
    stranded_value_at_risk_usd: float
    # Composite
    overall_risk_score: float
    overall_risk_category: str
    computed_at: str


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/calculate", response_model=MiningCalculateResponse)
def calculate_mining(
    req: MiningCalculateRequest,
    db: Session = Depends(get_db),
) -> MiningCalculateResponse:
    """
    Full mining climate risk assessment: GISTM tailings, water intensity,
    closure cost NPV, critical minerals supply concentration, stranded asset risk.
    """
    inp = MiningRiskInput(
        entity_name=req.entity_name,
        commodity=req.commodity,
        country_code=req.country_code,
        mine_type=req.mine_type,
        annual_production_kt=req.annual_production_kt,
        reserve_life_years=req.reserve_life_years,
        book_value_usd=req.book_value_usd,
        annual_revenue_usd=req.annual_revenue_usd,
        tailings_volume_m3=req.tailings_volume_m3,
        tailings_consequence_class=req.tailings_consequence_class,
        gistm_compliance_level=req.gistm_compliance_level,
        water_annual_withdrawal_m3=req.water_annual_withdrawal_m3,
        water_recycling_rate=req.water_recycling_rate,
        scope1_tco2e=req.scope1_tco2e,
        scope2_tco2e=req.scope2_tco2e,
        mine_closure_year=req.mine_closure_year,
    )

    result = calculate_mining_risk(inp, req.scenario, req.horizon_year)

    assessment_id: Optional[str] = None

    if req.save_to_db:
        try:
            entity_id = req.entity_id
            if not entity_id:
                entity_id = str(uuid.uuid4())
                db.execute(
                    text("""
                        INSERT INTO mining_entities
                            (id, entity_name, commodity, country_code, mine_type,
                             annual_production_kt, reserve_life_years,
                             book_value_usd, annual_revenue_usd, created_at)
                        VALUES (:id, :name, :commodity, :country, :mtype,
                                :prod, :life, :bv, :rev, NOW())
                        ON CONFLICT DO NOTHING
                    """),
                    {
                        "id": entity_id,
                        "name": req.entity_name,
                        "commodity": req.commodity,
                        "country": req.country_code,
                        "mtype": req.mine_type,
                        "prod": req.annual_production_kt,
                        "life": req.reserve_life_years,
                        "bv": req.book_value_usd,
                        "rev": req.annual_revenue_usd,
                    },
                )

            assessment_id = str(uuid.uuid4())
            db.execute(
                text("""
                    INSERT INTO mining_risk_assessments
                        (id, entity_id, scenario, horizon_year,
                         tailings_annual_failure_prob, tailings_expected_loss_usd,
                         tailings_compliance_flag,
                         water_intensity_m3_per_kt, water_stress_score, water_at_risk_m3_yr,
                         carbon_cost_usd, carbon_cost_as_pct_revenue,
                         closure_cost_usd, closure_npv_usd, closure_underfunding_usd,
                         critical_mineral_hhi, supply_concentration_risk,
                         transition_demand_exposure,
                         stranded_asset_risk_pct, stranded_value_at_risk_usd,
                         overall_risk_score, overall_risk_category,
                         assessed_at)
                    VALUES
                        (:id, :eid, :sc, :yr,
                         :tafp, :tel, :tcf,
                         :wim, :wss, :war,
                         :cc, :ccpct,
                         :closc, :closnpv, :closunder,
                         :cmhhi, :scr, :tde,
                         :sar, :svar,
                         :ors, :orc,
                         NOW())
                """),
                {
                    "id": assessment_id,
                    "eid": entity_id,
                    "sc": req.scenario,
                    "yr": req.horizon_year,
                    "tafp": result.tailings_annual_failure_prob,
                    "tel": result.tailings_expected_loss_usd,
                    "tcf": result.tailings_compliance_flag,
                    "wim": result.water_intensity_m3_per_kt,
                    "wss": result.water_stress_score,
                    "war": result.water_at_risk_m3_yr,
                    "cc": result.carbon_cost_usd,
                    "ccpct": result.carbon_cost_as_pct_revenue,
                    "closc": result.closure_cost_usd,
                    "closnpv": result.closure_npv_usd,
                    "closunder": result.closure_underfunding_usd,
                    "cmhhi": result.critical_mineral_hhi,
                    "scr": result.supply_concentration_risk,
                    "tde": result.transition_demand_exposure,
                    "sar": result.stranded_asset_risk_pct,
                    "svar": result.stranded_value_at_risk_usd,
                    "ors": result.overall_risk_score,
                    "orc": result.overall_risk_category,
                },
            )
            db.commit()
        except Exception as exc:
            logger.warning("DB write failed for mining assessment: %s", exc)
            db.rollback()
            assessment_id = None

    return MiningCalculateResponse(
        assessment_id=assessment_id,
        entity_name=req.entity_name,
        scenario=req.scenario,
        horizon_year=req.horizon_year,
        tailings_annual_failure_prob=result.tailings_annual_failure_prob,
        tailings_expected_loss_usd=result.tailings_expected_loss_usd,
        tailings_compliance_flag=result.tailings_compliance_flag,
        water_intensity_m3_per_kt=result.water_intensity_m3_per_kt,
        water_stress_score=result.water_stress_score,
        water_at_risk_m3_yr=result.water_at_risk_m3_yr,
        carbon_cost_usd=result.carbon_cost_usd,
        carbon_cost_as_pct_revenue=result.carbon_cost_as_pct_revenue,
        closure_cost_usd=result.closure_cost_usd,
        closure_npv_usd=result.closure_npv_usd,
        closure_underfunding_usd=result.closure_underfunding_usd,
        critical_mineral_hhi=result.critical_mineral_hhi,
        supply_concentration_risk=result.supply_concentration_risk,
        transition_demand_exposure=result.transition_demand_exposure,
        stranded_asset_risk_pct=result.stranded_asset_risk_pct,
        stranded_value_at_risk_usd=result.stranded_value_at_risk_usd,
        overall_risk_score=result.overall_risk_score,
        overall_risk_category=result.overall_risk_category,
        computed_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/reference-data")
def reference_data() -> Dict[str, Any]:
    """Return GISTM consequence table, carbon price paths, critical mineral HHI data."""
    return get_mining_reference()


@router.get("/assessments")
def list_assessments(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    try:
        rows = db.execute(
            text("""
                SELECT a.id, e.entity_name, e.commodity, a.scenario, a.horizon_year,
                       a.overall_risk_score, a.overall_risk_category,
                       a.stranded_asset_risk_pct, a.assessed_at
                FROM mining_risk_assessments a
                JOIN mining_entities e ON e.id = a.entity_id
                ORDER BY a.assessed_at DESC
                LIMIT :lim OFFSET :off
            """),
            {"lim": limit, "off": offset},
        ).fetchall()
        return [dict(r._mapping) for r in rows]
    except Exception as exc:
        logger.warning("mining assessments list failed: %s", exc)
        return []


@router.get("/assessments/{assessment_id}")
def get_assessment(
    assessment_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    try:
        row = db.execute(
            text("""
                SELECT a.*, e.entity_name, e.commodity, e.country_code, e.mine_type
                FROM mining_risk_assessments a
                JOIN mining_entities e ON e.id = a.entity_id
                WHERE a.id = :aid
            """),
            {"aid": assessment_id},
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Assessment not found")
        return dict(row._mapping)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
