"""Shipping and Steel Sector Calculator API routes."""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Optional, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator, ConfigDict

from services.shipping_calculator import ShippingInputs, shipping_calculator, EMISSION_FACTORS, CII_REFERENCE_PARAMS
from services.steel_calculator import SteelInputs, steel_calculator, IEA_NZE_GLIDEPATH

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/sector-calculators", tags=["Sector Calculators"])


# ─────────────────────────────────────────────────────────
# Shipping Schemas
# ─────────────────────────────────────────────────────────
class ShippingRequest(BaseModel):
    vessel_name: str = Field(default="Vessel 1", max_length=200)
    vessel_type: str = Field(description="bulker | tanker | container | lng_carrier | ro_ro | general_cargo")
    dwt: Decimal = Field(description="Deadweight tonnage", gt=0)
    gross_tonnage: Decimal = Field(description="Gross tonnage (GT)", gt=0)
    fuel_type: str = Field(description="HFO | VLSFO | MDO | LNG | METHANOL | AMMONIA | HYDROGEN")
    annual_fuel_tonnes: Decimal = Field(description="Annual fuel consumption in tonnes", gt=0)
    annual_distance_nm: Decimal = Field(description="Annual distance sailed in nautical miles", gt=0)
    annual_cargo_tonnes: Decimal = Field(description="Annual cargo carried in tonnes", gt=0)
    build_year: int = Field(default=2010, ge=1950, le=2025)
    reference_year: int = Field(default=2024, ge=2020, le=2030)

    model_config = ConfigDict(json_schema_extra={"example": {
        "vessel_name": "MV Pacific Star",
        "vessel_type": "bulker",
        "dwt": 80000,
        "gross_tonnage": 45000,
        "fuel_type": "VLSFO",
        "annual_fuel_tonnes": 8500,
        "annual_distance_nm": 75000,
        "annual_cargo_tonnes": 4200000,
        "build_year": 2012,
    }})


class ShippingResponse(BaseModel):
    vessel_name: str
    vessel_type: str
    annual_co2_tonnes: float
    aer: float
    eexi: Optional[float]
    cii_reference: float
    cii_actual: float
    cii_rating: str
    imo_2030_target_aer: float
    imo_2050_target_aer: float
    pct_vs_2030_target: float
    projected_stranding_year: Optional[int]
    required_fuel_switch_to_A: Optional[str]
    required_efficiency_improvement_pct: Optional[float]
    narrative: str
    data_available: bool = True
    error_message: Optional[str] = None


# ─────────────────────────────────────────────────────────
# Steel Schemas
# ─────────────────────────────────────────────────────────
class SteelRequest(BaseModel):
    plant_name: str = Field(default="Steel Plant 1", max_length=200)
    annual_production_mt: Decimal = Field(description="Annual steel production in million tonnes", gt=0)
    bf_bof_pct: Decimal = Field(description="BF-BOF share (0–1)", ge=0, le=1)
    eaf_pct: Decimal = Field(description="EAF share (0–1)", ge=0, le=1)
    dri_eaf_pct: Decimal = Field(description="Gas-based DRI-EAF share (0–1)", ge=0, le=1)
    dri_h2_pct: Decimal = Field(description="Hydrogen DRI-EAF share (0–1)", ge=0, le=1)
    bf_bof_ccus_pct: Decimal = Field(description="BF-BOF with CCUS share (0–1)", ge=0, le=1)
    eaf_grid_carbon_intensity_kgco2_kwh: Decimal = Field(
        description="Grid carbon intensity for EAF electricity (kgCO2/kWh)",
        default=Decimal("0.38"), ge=0, le=2
    )
    reference_year: int = Field(default=2024, ge=2020, le=2030)

    @field_validator("eaf_pct")
    @classmethod
    def check_mix_sums(cls, v, info):
        data = info.data or {}
        total = (
            float(data.get("bf_bof_pct", 0))
            + float(data.get("bf_bof_ccus_pct", 0))
            + float(v)
            + float(data.get("dri_eaf_pct", 0))
            + float(data.get("dri_h2_pct", 0))
        )
        if abs(total - 1.0) > 0.05:
            raise ValueError(f"Production route mix must sum to 1.0 (got {total:.2f})")
        return v

    model_config = ConfigDict(json_schema_extra={"example": {
        "plant_name": "Tata Steel Port Talbot",
        "annual_production_mt": 3.5,
        "bf_bof_pct": 0.85,
        "eaf_pct": 0.10,
        "dri_eaf_pct": 0.05,
        "dri_h2_pct": 0.00,
        "bf_bof_ccus_pct": 0.00,
        "eaf_grid_carbon_intensity_kgco2_kwh": 0.25,
    }})


class SteelGlidepathPointOut(BaseModel):
    year: int
    weighted_intensity: Optional[float]
    iea_nze_target: Optional[float]
    sbti_target: Optional[float]
    rag_status: str
    deviation_pct: Optional[float]


class SteelResponse(BaseModel):
    plant_name: str
    annual_production_mt: float
    weighted_emission_intensity: float
    annual_co2_mt: float
    route_breakdown: Dict[str, float]
    iea_2030_target: float
    pct_vs_iea_2030: float
    rag_2030: str
    glidepath_series: list[SteelGlidepathPointOut]
    pathway_to_iea_2030: str
    reduction_needed_tco2_per_t: float
    scenario_full_eaf_renewable_intensity: float
    scenario_dri_h2_50pct_intensity: float
    data_available: bool = True
    error_message: Optional[str] = None


# ─────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────
@router.post("/shipping/calculate", response_model=ShippingResponse, summary="Calculate CII rating and IMO alignment")
async def calculate_shipping(request: ShippingRequest):
    try:
        inputs = ShippingInputs(
            vessel_name=request.vessel_name,
            vessel_type=request.vessel_type,
            dwt=request.dwt,
            gross_tonnage=request.gross_tonnage,
            fuel_type=request.fuel_type,
            annual_fuel_tonnes=request.annual_fuel_tonnes,
            annual_distance_nm=request.annual_distance_nm,
            annual_cargo_tonnes=request.annual_cargo_tonnes,
            build_year=request.build_year,
            reference_year=request.reference_year,
        )
        result = shipping_calculator.calculate(inputs)
        return ShippingResponse(
            vessel_name=result.vessel_name,
            vessel_type=result.vessel_type,
            annual_co2_tonnes=float(result.annual_co2_tonnes),
            aer=float(result.aer),
            eexi=float(result.eexi) if result.eexi else None,
            cii_reference=float(result.cii_reference),
            cii_actual=float(result.cii_actual),
            cii_rating=result.cii_rating,
            imo_2030_target_aer=float(result.imo_2030_target_aer),
            imo_2050_target_aer=float(result.imo_2050_target_aer),
            pct_vs_2030_target=float(result.pct_vs_2030_target),
            projected_stranding_year=result.projected_stranding_year,
            required_fuel_switch_to_A=result.required_fuel_switch_to_A,
            required_efficiency_improvement_pct=float(result.required_efficiency_improvement_pct) if result.required_efficiency_improvement_pct else None,
            narrative=result.narrative,
            data_available=result.data_available,
            error_message=result.error_message,
        )
    except Exception as e:
        logger.exception("Shipping calculation error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/steel/calculate", response_model=SteelResponse, summary="Calculate steel emission intensity vs IEA NZE glidepath")
async def calculate_steel(request: SteelRequest):
    try:
        inputs = SteelInputs(
            plant_name=request.plant_name,
            annual_production_mt=request.annual_production_mt,
            bf_bof_pct=request.bf_bof_pct,
            eaf_pct=request.eaf_pct,
            dri_eaf_pct=request.dri_eaf_pct,
            dri_h2_pct=request.dri_h2_pct,
            bf_bof_ccus_pct=request.bf_bof_ccus_pct,
            eaf_grid_carbon_intensity_kgco2_kwh=request.eaf_grid_carbon_intensity_kgco2_kwh,
            reference_year=request.reference_year,
        )
        result = steel_calculator.calculate(inputs)
        return SteelResponse(
            plant_name=result.plant_name,
            annual_production_mt=float(result.annual_production_mt),
            weighted_emission_intensity=float(result.weighted_emission_intensity),
            annual_co2_mt=float(result.annual_co2_mt),
            route_breakdown={k: float(v) for k, v in result.route_breakdown.items()},
            iea_2030_target=float(result.iea_2030_target),
            pct_vs_iea_2030=float(result.pct_vs_iea_2030),
            rag_2030=result.rag_2030,
            glidepath_series=[
                SteelGlidepathPointOut(
                    year=p.year,
                    weighted_intensity=p.weighted_intensity,
                    iea_nze_target=p.iea_nze_target,
                    sbti_target=p.sbti_target,
                    rag_status=p.rag_status,
                    deviation_pct=p.deviation_pct,
                ) for p in result.glidepath_series
            ],
            pathway_to_iea_2030=result.pathway_to_iea_2030,
            reduction_needed_tco2_per_t=float(result.reduction_needed_tco2_per_t),
            scenario_full_eaf_renewable_intensity=float(result.scenario_full_eaf_renewable_intensity),
            scenario_dri_h2_50pct_intensity=float(result.scenario_dri_h2_50pct_intensity),
            data_available=result.data_available,
            error_message=result.error_message,
        )
    except Exception as e:
        logger.exception("Steel calculation error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shipping/vessel-types", summary="List supported vessel types")
async def list_vessel_types():
    return {"vessel_types": list(CII_REFERENCE_PARAMS.keys())}


@router.get("/shipping/fuel-types", summary="List supported fuel types with CO2 emission factors")
async def list_fuel_types():
    return {"fuel_types": {k: float(v) for k, v in EMISSION_FACTORS.items()}}


@router.get("/steel/iea-glidepath", summary="IEA NZE steel emission intensity glidepath")
async def get_steel_glidepath():
    return {
        "title": "IEA NZE 2023 Steel Decarbonisation Pathway",
        "metric": "tCO2 / tonne steel (weighted average)",
        "glidepath": [{"year": yr, "intensity": val} for yr, val in sorted(IEA_NZE_GLIDEPATH.items())],
    }
