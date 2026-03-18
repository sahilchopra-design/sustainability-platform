"""
Agriculture Risk Engine — Expanded Routes
POST /api/v1/agriculture-engine/methane           — Livestock methane intensity
POST /api/v1/agriculture-engine/disease-outbreak   — Disease outbreak risk
POST /api/v1/agriculture-engine/biodiversity-bng   — Biodiversity Net Gain
GET  /api/v1/agriculture-engine/reference-data     — All agriculture engine reference data

Note: Base crop yield / EUDR / soil carbon / water stress routes remain at
      /api/v1/agriculture/ (agriculture.py).
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
from services.agriculture_risk_engine import (
    LivestockMethaneInput,
    DiseaseOutbreakInput,
    BNGInput,
    BNGHabitatParcel,
    calculate_methane_intensity,
    calculate_disease_outbreak_risk,
    calculate_biodiversity_net_gain,
    get_agriculture_engine_reference_data,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/agriculture-engine",
    tags=["Agriculture Risk Engine (Expanded)"],
)


# ── Request Models ────────────────────────────────────────────────────────

class MethaneRequest(BaseModel):
    entity_name: str
    entity_id: Optional[str] = None
    livestock_type: str = "dairy_cattle"
    herd_size: int = 500
    feed_system: str = "mixed"
    region: str = "temperate"
    manure_management: str = "pasture"
    current_abatement: List[str] = []
    save_to_db: bool = True


class DiseaseOutbreakRequest(BaseModel):
    entity_name: str
    entity_id: Optional[str] = None
    herd_value_eur: float = 1_000_000.0
    herd_size: int = 500
    species: str = "cattle"
    biosecurity_level: str = "moderate"
    regional_disease_history: str = "moderate"
    insurance_coverage_pct: float = 50.0
    vaccination_programme: bool = True
    climate_warming_c: float = 1.5
    save_to_db: bool = True


class HabitatParcelModel(BaseModel):
    habitat_type: str
    area_ha: float = 0.0
    length_km: float = 0.0
    condition: str = "moderate"
    strategic_significance: str = "low"


class BNGRequest(BaseModel):
    entity_name: str
    entity_id: Optional[str] = None
    site_area_ha: float = 10.0
    baseline_habitats: List[HabitatParcelModel] = []
    proposed_habitats: List[HabitatParcelModel] = []
    development_type: str = "residential"
    local_planning_authority: str = ""
    mandatory_gain_pct: float = 10.0
    save_to_db: bool = True


# ── Routes ────────────────────────────────────────────────────────────────

@router.post("/methane")
def methane_intensity(req: MethaneRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Calculate livestock methane emissions (enteric + manure) using IPCC Tier 1
    and identify applicable abatement options.
    """
    entity_id = req.entity_id or str(uuid.uuid4())
    inp = LivestockMethaneInput(
        entity_id=entity_id,
        entity_name=req.entity_name,
        livestock_type=req.livestock_type,
        herd_size=req.herd_size,
        feed_system=req.feed_system,
        region=req.region,
        manure_management=req.manure_management,
        current_abatement=req.current_abatement,
    )
    result = calculate_methane_intensity(inp)

    if req.save_to_db:
        try:
            rid = str(uuid.uuid4())
            db.execute(text("""
                INSERT INTO agriculture_methane_assessments
                    (id, entity_id, entity_name, livestock_type, herd_size,
                     total_ch4_tonnes_yr, total_tco2e_yr,
                     intensity_kgch4_per_head, max_abatement_pct, assessed_at)
                VALUES (:id, :eid, :name, :lt, :hs, :ch4, :co2e, :intens, :abate, NOW())
            """), {
                "id": rid, "eid": entity_id, "name": req.entity_name,
                "lt": req.livestock_type, "hs": req.herd_size,
                "ch4": result.total_ch4_tonnes_yr, "co2e": result.total_tco2e_yr,
                "intens": result.intensity_kgch4_per_head,
                "abate": result.max_abatement_potential_pct,
            })
            db.commit()
        except Exception as e:
            logger.warning("DB save failed (methane): %s", e)
            db.rollback()

    return result.__dict__


@router.post("/disease-outbreak")
def disease_outbreak(req: DiseaseOutbreakRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Assess disease outbreak risk for livestock operations using OIE/WOAH
    profiles, biosecurity scoring, and climate-adjusted probabilities.
    """
    entity_id = req.entity_id or str(uuid.uuid4())
    inp = DiseaseOutbreakInput(
        entity_id=entity_id,
        entity_name=req.entity_name,
        herd_value_eur=req.herd_value_eur,
        herd_size=req.herd_size,
        species=req.species,
        biosecurity_level=req.biosecurity_level,
        regional_disease_history=req.regional_disease_history,
        insurance_coverage_pct=req.insurance_coverage_pct,
        vaccination_programme=req.vaccination_programme,
        climate_warming_c=req.climate_warming_c,
    )
    result = calculate_disease_outbreak_risk(inp)

    if req.save_to_db:
        try:
            rid = str(uuid.uuid4())
            db.execute(text("""
                INSERT INTO agriculture_disease_assessments
                    (id, entity_id, entity_name, species, herd_value_eur,
                     combined_prob, expected_loss_eur, worst_case_eur,
                     risk_score, risk_category, assessed_at)
                VALUES (:id, :eid, :name, :sp, :hv, :prob, :eloss, :wc, :rs, :rc, NOW())
            """), {
                "id": rid, "eid": entity_id, "name": req.entity_name,
                "sp": req.species, "hv": req.herd_value_eur,
                "prob": result.combined_outbreak_prob_annual,
                "eloss": result.expected_annual_loss_eur,
                "wc": result.worst_case_loss_eur,
                "rs": result.overall_disease_risk_score,
                "rc": result.risk_category,
            })
            db.commit()
        except Exception as e:
            logger.warning("DB save failed (disease): %s", e)
            db.rollback()

    return result.__dict__


@router.post("/biodiversity-bng")
def biodiversity_bng(req: BNGRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Calculate Biodiversity Net Gain using DEFRA Metric 4.0.
    Compares baseline vs proposed habitat units and BNG credit requirements.
    """
    entity_id = req.entity_id or str(uuid.uuid4())
    baseline = [
        BNGHabitatParcel(
            habitat_type=p.habitat_type, area_ha=p.area_ha, length_km=p.length_km,
            condition=p.condition, strategic_significance=p.strategic_significance,
        )
        for p in req.baseline_habitats
    ]
    proposed = [
        BNGHabitatParcel(
            habitat_type=p.habitat_type, area_ha=p.area_ha, length_km=p.length_km,
            condition=p.condition, strategic_significance=p.strategic_significance,
        )
        for p in req.proposed_habitats
    ]
    inp = BNGInput(
        entity_id=entity_id,
        entity_name=req.entity_name,
        site_area_ha=req.site_area_ha,
        baseline_habitats=baseline,
        proposed_habitats=proposed,
        development_type=req.development_type,
        local_planning_authority=req.local_planning_authority,
        mandatory_gain_pct=req.mandatory_gain_pct,
    )
    result = calculate_biodiversity_net_gain(inp)

    if req.save_to_db:
        try:
            rid = str(uuid.uuid4())
            db.execute(text("""
                INSERT INTO agriculture_bng_assessments
                    (id, entity_id, entity_name, site_area_ha,
                     baseline_units, proposed_units, net_gain_pct,
                     meets_requirement, credits_required, credit_cost_eur,
                     risk_rating, assessed_at)
                VALUES (:id, :eid, :name, :area,
                        :bu, :pu, :ng, :meets, :cr, :cc, :rr, NOW())
            """), {
                "id": rid, "eid": entity_id, "name": req.entity_name,
                "area": req.site_area_ha,
                "bu": result.baseline_habitat_units,
                "pu": result.proposed_habitat_units,
                "ng": result.net_gain_pct,
                "meets": result.meets_mandatory_requirement,
                "cr": result.bng_credits_required,
                "cc": result.credit_cost_eur,
                "rr": result.risk_rating,
            })
            db.commit()
        except Exception as e:
            logger.warning("DB save failed (BNG): %s", e)
            db.rollback()

    return result.__dict__


@router.get("/reference-data")
def reference_data() -> Dict[str, Any]:
    """Return all reference data for the expanded Agriculture Risk Engine."""
    return get_agriculture_engine_reference_data()
