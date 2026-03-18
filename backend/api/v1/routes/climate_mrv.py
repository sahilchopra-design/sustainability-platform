"""
Climate Data & MRV Routes — E73
==================================
Prefix: /api/v1/climate-mrv
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

from services.climate_mrv_engine import (
    assess_mrv_system,
    score_satellite_coverage,
    calculate_data_quality_score,
    assess_digital_mrv_maturity,
    generate_mrv_report,
    SATELLITE_SYSTEMS,
    ISO_14064_3_CHECKLIST,
    MRV_SYSTEM_TYPES,
    MATURITY_LABELS,
    MATURITY_DESCRIPTIONS,
    PCAF_DQS_MAPPING,
    SECTOR_EMISSION_FACTORS,
)

router = APIRouter(
    prefix="/api/v1/climate-mrv",
    tags=["Climate Data & MRV — E73"],
)

# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class MRVSystemRequest(BaseModel):
    entity_id: str
    facility_name: Optional[str] = "Main Facility"
    sector: Optional[str] = "manufacturing"
    mrv_type: Optional[str] = "dedicated_esg_platform"
    annual_emissions_tco2e: Optional[float] = 50_000.0

    class Config:
        extra = "allow"


class SatelliteCoverageRequest(BaseModel):
    entity_id: str
    lat: Optional[float] = 51.5
    lng: Optional[float] = -0.12
    facility_type: Optional[str] = "manufacturing"

    class Config:
        extra = "allow"


class DataQualityRequest(BaseModel):
    entity_id: str
    data_sources: Optional[List[Dict[str, Any]]] = None

    class Config:
        extra = "allow"


class DigitalMRVMaturityRequest(BaseModel):
    entity_id: str
    current_systems: Optional[List[str]] = None

    class Config:
        extra = "allow"


class MRVReportRequest(BaseModel):
    entity_id: str

    class Config:
        extra = "allow"


# ---------------------------------------------------------------------------
# POST Endpoints
# ---------------------------------------------------------------------------

@router.post("/assess-mrv-system")
async def post_assess_mrv_system(req: MRVSystemRequest):
    """
    Assess an MRV system: ISO 14064-3 level (1-3), data quality score
    (accuracy/completeness/timeliness), digital MRV maturity index (1-5),
    verification readiness. Persists to mrv_assessments table.
    """
    try:
        result = assess_mrv_system(
            entity_id=req.entity_id,
            facility_name=req.facility_name,
            sector=req.sector,
            mrv_type=req.mrv_type,
            annual_emissions_tco2e=req.annual_emissions_tco2e,
        )
        # DB persist (best-effort)
        try:
            from db.base import get_db_session
            from sqlalchemy import text
            import json
            async with get_db_session() as session:
                await session.execute(
                    text("""
                        INSERT INTO mrv_assessments
                          (entity_id, facility_name, sector, mrv_system_type, iso14064_level,
                           satellite_coverage, iot_sensors, verification_body,
                           data_quality_score, completeness_pct, accuracy_pct, timeliness_score,
                           cdp_submission_status, digital_mrv_maturity, ai_assisted,
                           blockchain_attested, ghg_inventory)
                        VALUES (:entity_id, :facility_name, :sector, :mrv_system_type, :iso14064_level,
                           :satellite_coverage, :iot_sensors, :verification_body,
                           :data_quality_score, :completeness_pct, :accuracy_pct, :timeliness_score,
                           :cdp_submission_status, :digital_mrv_maturity, :ai_assisted,
                           :blockchain_attested, :ghg_inventory::jsonb)
                    """),
                    {
                        "entity_id": req.entity_id,
                        "facility_name": result["facility_name"],
                        "sector": result["sector"],
                        "mrv_system_type": result["mrv_system_type"],
                        "iso14064_level": result["iso14064_level"],
                        "satellite_coverage": False,
                        "iot_sensors": 0,
                        "verification_body": None,
                        "data_quality_score": result["data_quality_score"],
                        "completeness_pct": result["completeness_pct"],
                        "accuracy_pct": result["accuracy_pct"],
                        "timeliness_score": result["timeliness_score"],
                        "cdp_submission_status": result["cdp_submission_status"],
                        "digital_mrv_maturity": result["digital_mrv_maturity"],
                        "ai_assisted": result["digital_mrv_maturity"] >= 5,
                        "blockchain_attested": False,
                        "ghg_inventory": json.dumps(result["ghg_inventory_summary"]),
                    },
                )
                await session.commit()
        except Exception:
            pass
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/score-satellite-coverage")
async def post_score_satellite_coverage(req: SatelliteCoverageRequest):
    """
    Score satellite coverage: TROPOMI/Sentinel-5P methane detection probability,
    GHGSat point-source resolution (25m), CarbonMapper sensitivity,
    satellite overpass frequency.
    """
    try:
        result = score_satellite_coverage(
            entity_id=req.entity_id,
            lat=req.lat,
            lng=req.lng,
            facility_type=req.facility_type,
        )
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate-data-quality")
async def post_calculate_data_quality(req: DataQualityRequest):
    """
    Calculate PCAF DQS 1-5 mapping, CDP response completeness,
    IPCC Tier 1/2/3 classification, uncertainty quantification.
    Persists data streams to mrv_data_streams table.
    """
    try:
        result = calculate_data_quality_score(
            entity_id=req.entity_id,
            data_sources=req.data_sources,
        )
        # Persist data streams
        try:
            from db.base import get_db_session
            from sqlalchemy import text
            if req.data_sources:
                async with get_db_session() as session:
                    for ds in req.data_sources[:5]:
                        await session.execute(
                            text("""
                                INSERT INTO mrv_data_streams
                                  (assessment_id, stream_name, source_type, frequency,
                                   emissions_tco2e, uncertainty_pct, validation_status)
                                VALUES (:assessment_id, :stream_name, :source_type, :frequency,
                                   :emissions_tco2e, :uncertainty_pct, :validation_status)
                            """),
                            {
                                "assessment_id": req.entity_id,
                                "stream_name": ds.get("type", "unknown"),
                                "source_type": ds.get("type", "unknown"),
                                "frequency": "annual",
                                "emissions_tco2e": None,
                                "uncertainty_pct": result["uncertainty_pct"],
                                "validation_status": "verified" if ds.get("verified") else "unverified",
                            },
                        )
                    await session.commit()
        except Exception:
            pass
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assess-digital-maturity")
async def post_assess_digital_mrv_maturity(req: DigitalMRVMaturityRequest):
    """
    Assess digital MRV maturity: 5-level model (Manual→Automated→Integrated→
    Intelligent→Autonomous), gap analysis, upgrade roadmap, cost estimate.
    """
    try:
        result = assess_digital_mrv_maturity(
            entity_id=req.entity_id,
            current_systems=req.current_systems,
        )
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-report")
async def post_generate_mrv_report(req: MRVReportRequest):
    """
    Generate comprehensive MRV compliance report: ISO 14064-3 checklist,
    EMAS Regulation 1221/2009, UK SECR SI 2018/1155,
    EU ETS MRV Regulation 2018/2066.
    """
    try:
        result = generate_mrv_report(entity_id=req.entity_id)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# GET Reference Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/satellite-systems")
async def get_satellite_systems():
    """List 5 satellite systems with coverage specifications."""
    return {
        "status": "success",
        "data": [
            {"name": name, **info}
            for name, info in SATELLITE_SYSTEMS.items()
        ],
        "count": len(SATELLITE_SYSTEMS),
    }


@router.get("/ref/iso14064-checklist")
async def get_iso14064_checklist():
    """ISO 14064-3:2019 12-item verification checklist with weights."""
    return {
        "status": "success",
        "data": ISO_14064_3_CHECKLIST,
        "standard": "ISO 14064-3:2019 — GHG verification and validation",
        "count": len(ISO_14064_3_CHECKLIST),
    }


@router.get("/ref/mrv-system-types")
async def get_mrv_system_types():
    """List 6 MRV system types with accuracy and maturity ranges."""
    return {
        "status": "success",
        "data": [
            {
                "type": name,
                "display_name": name.replace("_", " ").title(),
                "maturity_level": info["maturity"],
                "maturity_label": MATURITY_LABELS[info["maturity"]],
                "accuracy_range_pct": list(info["accuracy_range"]),
                "completeness_range_pct": list(info["completeness_range"]),
            }
            for name, info in MRV_SYSTEM_TYPES.items()
        ],
        "count": len(MRV_SYSTEM_TYPES),
    }


@router.get("/ref/maturity-levels")
async def get_maturity_levels():
    """5-level digital MRV maturity model definitions."""
    return {
        "status": "success",
        "data": [
            {
                "level": level,
                "label": label,
                "description": MATURITY_DESCRIPTIONS[level],
            }
            for level, label in MATURITY_LABELS.items()
        ],
    }


@router.get("/ref/pcaf-dqs")
async def get_pcaf_dqs():
    """PCAF Data Quality Score framework (DQS 1-5) with confidence weights."""
    return {
        "status": "success",
        "data": [
            {
                "dqs": level,
                **info,
            }
            for level, info in PCAF_DQS_MAPPING.items()
        ],
        "source": "PCAF Global GHG Accounting and Reporting Standard 2022",
    }


@router.get("/ref/sector-emission-factors")
async def get_sector_emission_factors():
    """8 sector-specific emission factors with EU ETS coverage flags."""
    return {
        "status": "success",
        "data": [
            {"sector": sector, **info}
            for sector, info in SECTOR_EMISSION_FACTORS.items()
        ],
        "count": len(SECTOR_EMISSION_FACTORS),
    }
