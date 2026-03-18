"""
Maritime Routes — IMO GHG / CII / EEXI / EU ETS / FuelEU Maritime
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from services.maritime_engine import MaritimeEngine

router = APIRouter(prefix="/api/v1/maritime", tags=["maritime"])
engine = MaritimeEngine()


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class CIIRequest(BaseModel):
    entity_id: str = Field(..., description="Unique ship/entity identifier")
    ship_type: str = Field("bulk_carrier", description="Ship type key")
    deadweight_tonnes: float = Field(75000.0, gt=0, description="Deadweight tonnage (DWT)")
    annual_fuel_consumption_t: float = Field(3150.0, gt=0, description="Annual fuel consumption in tonnes")
    annual_distance_nm: float = Field(55000.0, gt=0, description="Annual distance sailed in nautical miles")
    annual_cargo_tonnes: float = Field(60000.0, gt=0, description="Annual cargo carried in tonnes")
    fuel_type: str = Field("HFO", description="Fuel type (HFO, LSFO, MDO, LNG, methanol, ammonia, hydrogen)")
    year: int = Field(2024, ge=2023, le=2030, description="Assessment year")


class EEXIRequest(BaseModel):
    entity_id: str = Field(..., description="Unique ship/entity identifier")
    ship_type: str = Field("tanker", description="Ship type key")
    gross_tonnage: float = Field(80000.0, gt=0, description="Gross tonnage (GT)")
    installed_power_kw: float = Field(12000.0, gt=0, description="Installed main engine power (kW)")
    design_fuel_consumption_g_kwh: float = Field(175.0, gt=0, description="Design fuel consumption (g/kWh)")
    fuel_type: str = Field("HFO", description="Fuel type")


class EUETSRequest(BaseModel):
    entity_id: str = Field(..., description="Unique ship/entity identifier")
    ship_type: str = Field("container", description="Ship type key")
    annual_co2_tonnes: float = Field(25000.0, gt=0, description="Annual verified CO2 emissions (tonnes)")
    eu_route_share_pct: float = Field(45.0, ge=0.0, le=100.0, description="Share of voyages on EU routes (%)")
    year: int = Field(2024, ge=2024, le=2030, description="Compliance year")


class FuelEURequest(BaseModel):
    entity_id: str = Field(..., description="Unique ship/entity identifier")
    ship_type: str = Field("bulk_carrier", description="Ship type key")
    fuel_type: str = Field("HFO", description="Fuel type")
    annual_energy_mj: float = Field(1200000.0, gt=0, description="Annual energy consumption (MJ)")
    year: int = Field(2025, ge=2025, le=2050, description="FuelEU compliance year")


class StrandingRequest(BaseModel):
    entity_id: str = Field(..., description="Unique ship/entity identifier")
    ship_type: str = Field("tanker", description="Ship type key")
    build_year: int = Field(2005, ge=1970, le=2024, description="Year the ship was built")
    fuel_type: str = Field("HFO", description="Current fuel type")
    gross_tonnage: float = Field(100000.0, gt=0, description="Gross tonnage (GT)")


class ShipItem(BaseModel):
    ship_id: str = Field(..., description="Individual ship identifier")
    ship_type: str = Field("bulk_carrier")
    fuel_type: str = Field("HFO")
    gross_tonnage: float = Field(50000.0, gt=0)
    deadweight_tonnes: Optional[float] = None
    annual_fuel_consumption_t: Optional[float] = None
    annual_distance_nm: Optional[float] = None
    annual_cargo_tonnes: Optional[float] = None
    build_year: int = Field(2008)
    year: int = Field(2024)
    eu_route_share_pct: float = Field(35.0)


class FleetRequest(BaseModel):
    entity_id: str = Field(..., description="Fleet owner entity identifier")
    ships: List[ShipItem] = Field(..., min_items=1, description="List of ships in fleet")


# ---------------------------------------------------------------------------
# POST Endpoints
# ---------------------------------------------------------------------------

@router.post("/cii-assessment", summary="Carbon Intensity Indicator (CII) Assessment")
async def cii_assessment(req: CIIRequest):
    try:
        result = engine.assess_cii(
            entity_id=req.entity_id,
            ship_type=req.ship_type,
            deadweight_tonnes=req.deadweight_tonnes,
            annual_fuel_consumption_t=req.annual_fuel_consumption_t,
            annual_distance_nm=req.annual_distance_nm,
            annual_cargo_tonnes=req.annual_cargo_tonnes,
            fuel_type=req.fuel_type,
            year=req.year,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/eexi-assessment", summary="Energy Efficiency Existing Ship Index (EEXI) Assessment")
async def eexi_assessment(req: EEXIRequest):
    try:
        result = engine.assess_eexi(
            entity_id=req.entity_id,
            ship_type=req.ship_type,
            gross_tonnage=req.gross_tonnage,
            installed_power_kw=req.installed_power_kw,
            design_fuel_consumption_g_kwh=req.design_fuel_consumption_g_kwh,
            fuel_type=req.fuel_type,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/eu-ets", summary="EU ETS Shipping Allowance & Cost Assessment")
async def eu_ets(req: EUETSRequest):
    try:
        result = engine.assess_eu_ets(
            entity_id=req.entity_id,
            ship_type=req.ship_type,
            annual_co2_tonnes=req.annual_co2_tonnes,
            eu_route_share_pct=req.eu_route_share_pct,
            year=req.year,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fueleu", summary="FuelEU Maritime GHG Intensity & Compliance")
async def fueleu(req: FuelEURequest):
    try:
        result = engine.assess_fueleu(
            entity_id=req.entity_id,
            ship_type=req.ship_type,
            fuel_type=req.fuel_type,
            annual_energy_mj=req.annual_energy_mj,
            year=req.year,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stranding-risk", summary="Ship Asset Stranding Risk Assessment")
async def stranding_risk(req: StrandingRequest):
    try:
        result = engine.assess_stranding(
            entity_id=req.entity_id,
            ship_type=req.ship_type,
            build_year=req.build_year,
            fuel_type=req.fuel_type,
            gross_tonnage=req.gross_tonnage,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fleet-assessment", summary="Fleet-Level Aggregated Maritime Risk")
async def fleet_assessment(req: FleetRequest):
    try:
        ships_dicts = [s.dict() for s in req.ships]
        result = engine.assess_fleet(entity_id=req.entity_id, ships=ships_dicts)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# GET Reference Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/ship-types", summary="Reference: Ship Types & IMO Parameters")
def ref_ship_types():
    from services.maritime_engine import SHIP_TYPES, EEXI_REFERENCE
    return {
        "ship_types": SHIP_TYPES,
        "eexi_reference_values": EEXI_REFERENCE,
        "description": "Baseline CII reference values and EEXI required values by ship type",
        "source": "MARPOL Annex VI; IMO MEPC.338(76); IMO MEPC.333(76)",
    }


@router.get("/ref/fuel-types", summary="Reference: Fuel Emission Factors")
def ref_fuel_types():
    from services.maritime_engine import FUEL_EMISSION_FACTORS, ALTERNATIVE_FUEL_CAPEX_USD_PER_KW
    return {
        "fuel_emission_factors": FUEL_EMISSION_FACTORS,
        "alternative_fuel_capex_usd_per_kw": ALTERNATIVE_FUEL_CAPEX_USD_PER_KW,
        "description": "CO2 conversion factors and well-to-wake GHG intensities per fuel type",
        "source": "MARPOL Annex VI; IMO MEPC.1/Circ.684; FuelEU Annex I",
    }


@router.get("/ref/regulatory-timeline", summary="Reference: Maritime Regulatory Timeline")
def ref_regulatory_timeline():
    from services.maritime_engine import (
        CII_REDUCTION_TARGETS, EU_ETS_PHASE_COVERAGE, FUELEU_GHG_TARGETS_GCO2E_MJ
    )
    return {
        "cii_reduction_targets": CII_REDUCTION_TARGETS,
        "eu_ets_phase_coverage": EU_ETS_PHASE_COVERAGE,
        "fueleu_ghg_targets_gco2e_mj": FUELEU_GHG_TARGETS_GCO2E_MJ,
        "key_milestones": [
            {"year": 2023, "event": "CII mandatory rating (MARPOL Annex VI)"},
            {"year": 2023, "event": "EEXI compliance mandatory"},
            {"year": 2024, "event": "EU ETS Shipping 40% phase-in"},
            {"year": 2025, "event": "EU ETS 70%; FuelEU Maritime enters force"},
            {"year": 2026, "event": "EU ETS 100% coverage"},
            {"year": 2030, "event": "IMO GHG target: 20-30% reduction vs 2008"},
            {"year": 2050, "event": "IMO GHG target: net-zero"},
        ],
        "source": "IMO MEPC.377(80); Regulation (EU) 2023/957; Regulation (EU) 2023/1805",
    }
