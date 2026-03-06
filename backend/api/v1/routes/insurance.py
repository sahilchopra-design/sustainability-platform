"""
Insurance Climate Risk Routes
POST /api/v1/insurance/calculate
GET  /api/v1/insurance/reference-data
GET  /api/v1/insurance/assessments
GET  /api/v1/insurance/assessments/{assessment_id}

Aligned with Solvency II Art. 44a / EIOPA ORSA Climate Guide 2022 /
Swiss Re sigma Physical Risk Model.
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
from services.insurance_climate_risk import (
    InsuranceCATInput,
    calculate_insurance_climate_risk,
    get_reference_data as get_insurance_reference,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/insurance",
    tags=["Insurance Climate Risk"],
)


# ── Request / Response models ──────────────────────────────────────────────────

class InsuranceCalculateRequest(BaseModel):
    entity_name: str
    entity_type: str = "insurer"                  # insurer | reinsurer | captive
    domicile_country: str = "GB"
    lines_of_business: List[str] = ["property"]  # property | marine | motor | life | liability
    perils_exposed: List[str] = ["flood", "wildfire"]
    gross_written_premium: float = 0.0            # EUR
    technical_provisions: float = 0.0            # EUR
    gross_cat_loss_1_in_100: float = 0.0          # EUR — current climate baseline
    gross_cat_loss_1_in_250: float = 0.0          # EUR
    reinsurance_recovery_pct: float = 0.65        # 0-1
    scenario: str = "2C"                          # 1.5C | 2C | 3C
    horizon_year: int = 2050
    save_to_db: bool = True
    entity_id: Optional[str] = None              # link to existing insurance_climate_entities


class InsuranceCalculateResponse(BaseModel):
    assessment_id: Optional[str]
    entity_name: str
    scenario: str
    horizon_year: int
    # CAT losses
    gross_cat_loss_1in100_climate: float
    gross_cat_loss_1in250_climate: float
    net_cat_loss_1in100_climate: float
    net_cat_loss_1in250_climate: float
    # Technical provisions
    tp_climate_uplift_eur: float
    tp_uplift_pct: float
    # SCR
    scr_cat_addon_eur: float
    scr_climate_loading_pct: float
    # Reserve
    reserve_adequacy_ratio: float
    reserve_shortfall_eur: float
    # Protection gap
    economic_loss_1in100: float
    protection_gap_pct: float
    # Reinsurance
    reinsurance_sufficiency: str
    # Flags
    solvency_ii_flags: List[str]
    computed_at: str


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/calculate", response_model=InsuranceCalculateResponse)
def calculate_insurance(
    req: InsuranceCalculateRequest,
    db: Session = Depends(get_db),
) -> InsuranceCalculateResponse:
    """
    Calculate climate-adjusted CAT risk, technical provisions uplift,
    SCR add-on, reserve adequacy, protection gap and reinsurance sufficiency.
    """
    inp = InsuranceCATInput(
        entity_name=req.entity_name,
        entity_type=req.entity_type,
        domicile_country=req.domicile_country,
        lines_of_business=req.lines_of_business,
        perils_exposed=req.perils_exposed,
        gross_written_premium=req.gross_written_premium,
        technical_provisions=req.technical_provisions,
        gross_cat_loss_1_in_100=req.gross_cat_loss_1_in_100,
        gross_cat_loss_1_in_250=req.gross_cat_loss_1_in_250,
        reinsurance_recovery_pct=req.reinsurance_recovery_pct,
    )

    result = calculate_insurance_climate_risk(inp, req.scenario, req.horizon_year)

    assessment_id: Optional[str] = None

    if req.save_to_db:
        try:
            entity_id = req.entity_id
            if not entity_id:
                entity_id = str(uuid.uuid4())
                db.execute(
                    text("""
                        INSERT INTO insurance_climate_entities
                            (id, entity_name, entity_type, domicile_country,
                             lines_of_business, perils_exposed,
                             gross_written_premium_eur, technical_provisions_eur,
                             reinsurance_recovery_pct, created_at)
                        VALUES
                            (:id, :name, :etype, :country,
                             :lob, :perils,
                             :gwp, :tp,
                             :rr, NOW())
                        ON CONFLICT DO NOTHING
                    """),
                    {
                        "id": entity_id,
                        "name": req.entity_name,
                        "etype": req.entity_type,
                        "country": req.domicile_country,
                        "lob": str(req.lines_of_business),
                        "perils": str(req.perils_exposed),
                        "gwp": req.gross_written_premium,
                        "tp": req.technical_provisions,
                        "rr": req.reinsurance_recovery_pct,
                    },
                )

            assessment_id = str(uuid.uuid4())
            db.execute(
                text("""
                    INSERT INTO insurance_climate_assessments
                        (id, entity_id, scenario, horizon_year,
                         gross_cat_loss_1in100_climate, gross_cat_loss_1in250_climate,
                         net_cat_loss_1in100_climate, net_cat_loss_1in250_climate,
                         tp_climate_uplift_eur, tp_uplift_pct,
                         scr_cat_addon_eur, scr_climate_loading_pct,
                         reserve_adequacy_ratio, reserve_shortfall_eur,
                         economic_loss_1in100, protection_gap_pct,
                         reinsurance_sufficiency, solvency_ii_flags,
                         assessed_at)
                    VALUES
                        (:id, :eid, :scenario, :year,
                         :gc100, :gc250,
                         :nc100, :nc250,
                         :tp_uplift, :tp_pct,
                         :scr_addon, :scr_pct,
                         :rar, :rshort,
                         :el100, :pg_pct,
                         :rs, :flags,
                         NOW())
                """),
                {
                    "id": assessment_id,
                    "eid": entity_id,
                    "scenario": req.scenario,
                    "year": req.horizon_year,
                    "gc100": result.gross_cat_loss_1in100_climate,
                    "gc250": result.gross_cat_loss_1in250_climate,
                    "nc100": result.net_cat_loss_1in100_climate,
                    "nc250": result.net_cat_loss_1in250_climate,
                    "tp_uplift": result.tp_climate_uplift_eur,
                    "tp_pct": result.tp_uplift_pct,
                    "scr_addon": result.scr_cat_addon_eur,
                    "scr_pct": result.scr_climate_loading_pct,
                    "rar": result.reserve_adequacy_ratio,
                    "rshort": result.reserve_shortfall_eur,
                    "el100": result.economic_loss_1in100,
                    "pg_pct": result.protection_gap_pct,
                    "rs": result.reinsurance_sufficiency,
                    "flags": str(result.solvency_ii_flags),
                },
            )
            db.commit()
        except Exception as exc:
            logger.warning("DB write failed for insurance assessment: %s", exc)
            db.rollback()
            assessment_id = None

    return InsuranceCalculateResponse(
        assessment_id=assessment_id,
        entity_name=req.entity_name,
        scenario=req.scenario,
        horizon_year=req.horizon_year,
        gross_cat_loss_1in100_climate=result.gross_cat_loss_1in100_climate,
        gross_cat_loss_1in250_climate=result.gross_cat_loss_1in250_climate,
        net_cat_loss_1in100_climate=result.net_cat_loss_1in100_climate,
        net_cat_loss_1in250_climate=result.net_cat_loss_1in250_climate,
        tp_climate_uplift_eur=result.tp_climate_uplift_eur,
        tp_uplift_pct=result.tp_uplift_pct,
        scr_cat_addon_eur=result.scr_cat_addon_eur,
        scr_climate_loading_pct=result.scr_climate_loading_pct,
        reserve_adequacy_ratio=result.reserve_adequacy_ratio,
        reserve_shortfall_eur=result.reserve_shortfall_eur,
        economic_loss_1in100=result.economic_loss_1in100,
        protection_gap_pct=result.protection_gap_pct,
        reinsurance_sufficiency=result.reinsurance_sufficiency,
        solvency_ii_flags=result.solvency_ii_flags,
        computed_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/reference-data")
def reference_data() -> Dict[str, Any]:
    """Return peril multipliers, SCR factors, TP uplift table."""
    return get_insurance_reference()


@router.get("/assessments")
def list_assessments(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """List recent insurance climate assessments."""
    try:
        rows = db.execute(
            text("""
                SELECT a.id, e.entity_name, a.scenario, a.horizon_year,
                       a.gross_cat_loss_1in100_climate, a.tp_climate_uplift_eur,
                       a.scr_cat_addon_eur, a.reserve_adequacy_ratio,
                       a.reinsurance_sufficiency, a.assessed_at
                FROM insurance_climate_assessments a
                JOIN insurance_climate_entities e ON e.id = a.entity_id
                ORDER BY a.assessed_at DESC
                LIMIT :lim OFFSET :off
            """),
            {"lim": limit, "off": offset},
        ).fetchall()
        return [dict(r._mapping) for r in rows]
    except Exception as exc:
        logger.warning("insurance assessments list failed: %s", exc)
        return []


@router.get("/assessments/{assessment_id}")
def get_assessment(
    assessment_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Return a single insurance climate assessment."""
    try:
        row = db.execute(
            text("""
                SELECT a.*, e.entity_name, e.entity_type, e.domicile_country
                FROM insurance_climate_assessments a
                JOIN insurance_climate_entities e ON e.id = a.entity_id
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
