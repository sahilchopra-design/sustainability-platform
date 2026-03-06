"""
Agriculture Climate Risk Routes
POST /api/v1/agriculture/calculate
GET  /api/v1/agriculture/reference-data
GET  /api/v1/agriculture/assessments
GET  /api/v1/agriculture/assessments/{assessment_id}

Methodology: IPCC AR6 crop yield, EUDR 2023/1115, soil carbon (Verra VM0042),
             water stress (AQUEDUCT / WRI).
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
from services.agriculture_risk_calculator import (
    AgricultureRiskInput,
    calculate_agriculture_risk,
    get_reference_data as get_ag_reference,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/agriculture",
    tags=["Agriculture Climate Risk"],
)


# ── Request / Response models ──────────────────────────────────────────────────

class AgricultureCalculateRequest(BaseModel):
    entity_name: str
    country_code: str = "BR"                     # ISO 3166-1 alpha-2
    crop_types: List[str] = ["soy"]              # wheat | maize | rice | soy | ...
    farm_type: str = "arable"                    # arable | mixed | livestock | horticulture
    total_area_ha: float = 1000.0
    annual_revenue_usd: float = 0.0
    eudr_commodities: List[str] = []             # subset of 7 EUDR in-scope commodities
    baseline_yield_t_ha: float = 3.0
    irrigation_pct: float = 0.0                  # % of area irrigated
    water_annual_withdrawal_m3: float = 0.0
    scenario: str = "2C"                         # 1.5C | 2C | 3C
    horizon_year: int = 2050
    save_to_db: bool = True
    entity_id: Optional[str] = None


class AgricultureCalculateResponse(BaseModel):
    assessment_id: Optional[str]
    entity_name: str
    scenario: str
    horizon_year: int
    # Yield
    temp_delta_c: float
    yield_change_pct: float
    projected_yield_t_ha: float
    yield_revenue_impact_usd: float
    # EUDR
    eudr_compliance_score: float
    eudr_high_risk_commodities: List[str]
    eudr_country_risk_tier: str
    eudr_deforestation_risk: str
    # Soil carbon
    soil_carbon_seq_tco2e_yr: float
    soil_carbon_credit_value_usd: float
    # Water stress
    water_stress_index: float
    water_stress_category: str
    water_at_risk_m3_yr: float
    # Composite
    overall_risk_score: float
    overall_risk_category: str
    computed_at: str


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/calculate", response_model=AgricultureCalculateResponse)
def calculate_agriculture(
    req: AgricultureCalculateRequest,
    db: Session = Depends(get_db),
) -> AgricultureCalculateResponse:
    """
    Full agriculture climate risk assessment: yield sensitivity, EUDR compliance,
    soil carbon sequestration, and water stress.
    """
    inp = AgricultureRiskInput(
        entity_name=req.entity_name,
        country_code=req.country_code,
        crop_types=req.crop_types,
        farm_type=req.farm_type,
        total_area_ha=req.total_area_ha,
        annual_revenue_usd=req.annual_revenue_usd,
        eudr_commodities=req.eudr_commodities,
        baseline_yield_t_ha=req.baseline_yield_t_ha,
        irrigation_pct=req.irrigation_pct,
        water_annual_withdrawal_m3=req.water_annual_withdrawal_m3,
    )

    result = calculate_agriculture_risk(inp, req.scenario, req.horizon_year)

    assessment_id: Optional[str] = None

    if req.save_to_db:
        try:
            entity_id = req.entity_id
            if not entity_id:
                entity_id = str(uuid.uuid4())
                db.execute(
                    text("""
                        INSERT INTO agriculture_entities
                            (id, entity_name, country_code, crop_types, farm_type,
                             total_area_ha, annual_revenue_usd, created_at)
                        VALUES (:id, :name, :country, :crops, :ftype,
                                :area, :rev, NOW())
                        ON CONFLICT DO NOTHING
                    """),
                    {
                        "id": entity_id,
                        "name": req.entity_name,
                        "country": req.country_code,
                        "crops": str(req.crop_types),
                        "ftype": req.farm_type,
                        "area": req.total_area_ha,
                        "rev": req.annual_revenue_usd,
                    },
                )

            assessment_id = str(uuid.uuid4())
            db.execute(
                text("""
                    INSERT INTO agriculture_risk_assessments
                        (id, entity_id, scenario, horizon_year,
                         temp_delta_c, yield_change_pct, projected_yield_t_ha,
                         yield_revenue_impact_usd,
                         eudr_compliance_score, eudr_high_risk_commodities,
                         eudr_country_risk_tier, eudr_deforestation_risk,
                         soil_carbon_seq_tco2e_yr, soil_carbon_credit_value_usd,
                         water_stress_index, water_stress_category, water_at_risk_m3_yr,
                         overall_risk_score, overall_risk_category,
                         assessed_at)
                    VALUES
                        (:id, :eid, :sc, :yr,
                         :tdelta, :ychange, :yprojected,
                         :yrevimpact,
                         :eudr_score, :eudr_hrc,
                         :eudr_tier, :eudr_defor,
                         :soil_seq, :soil_val,
                         :wsi, :wsc, :war,
                         :ors, :orc,
                         NOW())
                """),
                {
                    "id": assessment_id,
                    "eid": entity_id,
                    "sc": req.scenario,
                    "yr": req.horizon_year,
                    "tdelta": result.temp_delta_c,
                    "ychange": result.yield_change_pct,
                    "yprojected": result.projected_yield_t_ha,
                    "yrevimpact": result.yield_revenue_impact_usd,
                    "eudr_score": result.eudr_compliance_score,
                    "eudr_hrc": str(result.eudr_high_risk_commodities),
                    "eudr_tier": result.eudr_country_risk_tier,
                    "eudr_defor": result.eudr_deforestation_risk,
                    "soil_seq": result.soil_carbon_seq_tco2e_yr,
                    "soil_val": result.soil_carbon_credit_value_usd,
                    "wsi": result.water_stress_index,
                    "wsc": result.water_stress_category,
                    "war": result.water_at_risk_m3_yr,
                    "ors": result.overall_risk_score,
                    "orc": result.overall_risk_category,
                },
            )
            db.commit()
        except Exception as exc:
            logger.warning("DB write failed for agriculture assessment: %s", exc)
            db.rollback()
            assessment_id = None

    return AgricultureCalculateResponse(
        assessment_id=assessment_id,
        entity_name=req.entity_name,
        scenario=req.scenario,
        horizon_year=req.horizon_year,
        temp_delta_c=result.temp_delta_c,
        yield_change_pct=result.yield_change_pct,
        projected_yield_t_ha=result.projected_yield_t_ha,
        yield_revenue_impact_usd=result.yield_revenue_impact_usd,
        eudr_compliance_score=result.eudr_compliance_score,
        eudr_high_risk_commodities=result.eudr_high_risk_commodities,
        eudr_country_risk_tier=result.eudr_country_risk_tier,
        eudr_deforestation_risk=result.eudr_deforestation_risk,
        soil_carbon_seq_tco2e_yr=result.soil_carbon_seq_tco2e_yr,
        soil_carbon_credit_value_usd=result.soil_carbon_credit_value_usd,
        water_stress_index=result.water_stress_index,
        water_stress_category=result.water_stress_category,
        water_at_risk_m3_yr=result.water_at_risk_m3_yr,
        overall_risk_score=result.overall_risk_score,
        overall_risk_category=result.overall_risk_category,
        computed_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/reference-data")
def reference_data() -> Dict[str, Any]:
    """Return crop yield sensitivity, EUDR commodity list, country risk tiers."""
    return get_ag_reference()


@router.get("/assessments")
def list_assessments(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    try:
        rows = db.execute(
            text("""
                SELECT a.id, e.entity_name, a.scenario, a.horizon_year,
                       a.yield_change_pct, a.eudr_compliance_score,
                       a.overall_risk_score, a.overall_risk_category, a.assessed_at
                FROM agriculture_risk_assessments a
                JOIN agriculture_entities e ON e.id = a.entity_id
                ORDER BY a.assessed_at DESC
                LIMIT :lim OFFSET :off
            """),
            {"lim": limit, "off": offset},
        ).fetchall()
        return [dict(r._mapping) for r in rows]
    except Exception as exc:
        logger.warning("agriculture assessments list failed: %s", exc)
        return []


@router.get("/assessments/{assessment_id}")
def get_assessment(
    assessment_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    try:
        row = db.execute(
            text("""
                SELECT a.*, e.entity_name, e.country_code, e.crop_types
                FROM agriculture_risk_assessments a
                JOIN agriculture_entities e ON e.id = a.entity_id
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
