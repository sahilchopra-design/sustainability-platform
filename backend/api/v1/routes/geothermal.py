"""
Geothermal Energy Project Assessment
IRENA Geothermal Power Technology Brief 2024 / IEA World Energy Outlook 2023

Computes LCOE, capacity factor, resource viability, and Paris-alignment
for binary, flash, dry-steam, and EGS geothermal plants.
"""
import logging
import math
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from db.base import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/geothermal", tags=["Geothermal Assessment"])


# -- Reference data (IRENA 2024 / IEA) --
# LCOE ranges by plant type (USD/MWh)
PLANT_TYPES = {
    "dry_steam":    {"label": "Dry Steam",   "lcoe_low": 40, "lcoe_high": 80,  "cf_typical": 90, "lifetime": 30, "co2_gkwh": 15},
    "single_flash": {"label": "Single Flash", "lcoe_low": 45, "lcoe_high": 85,  "cf_typical": 85, "lifetime": 30, "co2_gkwh": 50},
    "double_flash": {"label": "Double Flash", "lcoe_low": 48, "lcoe_high": 90,  "cf_typical": 85, "lifetime": 30, "co2_gkwh": 55},
    "binary":       {"label": "Binary (ORC)", "lcoe_low": 55, "lcoe_high": 110, "cf_typical": 80, "lifetime": 25, "co2_gkwh": 0},
    "egs":          {"label": "EGS (Enhanced)","lcoe_low": 80, "lcoe_high": 200, "cf_typical": 75, "lifetime": 25, "co2_gkwh": 0},
}

# Reservoir temperature adequacy thresholds (deg C)
TEMP_THRESHOLDS = {
    "dry_steam":    {"min": 230, "optimal": 260},
    "single_flash": {"min": 180, "optimal": 220},
    "double_flash": {"min": 200, "optimal": 240},
    "binary":       {"min": 100, "optimal": 150},
    "egs":          {"min": 150, "optimal": 200},
}

# Induced seismicity risk by injection depth (simplified)
SEISMICITY_RISK = {
    "low":    "Depth < 2 km, reservoir pressure maintained",
    "medium": "Depth 2-4 km, moderate injection rates",
    "high":   "Depth > 4 km or EGS hydraulic stimulation",
}


class GeothermalRequest(BaseModel):
    project_name: str = "Geothermal Assessment"
    country_iso2: str = "IS"
    plant_type: str = Field("binary", description="dry_steam | single_flash | double_flash | binary | egs")
    installed_capacity_mw: float = Field(50, gt=0)
    reservoir_temp_c: float = Field(160, gt=0, description="Reservoir temperature (deg C)")
    well_depth_m: float = Field(2500, gt=0)
    number_of_wells: int = Field(10, gt=0)
    drilling_cost_musd_per_well: float = Field(5.0, gt=0)
    surface_plant_cost_musd: float = Field(80, gt=0)
    annual_opex_musd: float = Field(6.0, ge=0)
    capacity_factor_pct: Optional[float] = None
    discount_rate_pct: float = Field(8.0, ge=0, le=30)
    project_lifetime_years: int = Field(25, ge=5, le=50)
    has_district_heating: bool = False
    heating_revenue_musd_yr: float = Field(0.0, ge=0)
    carbon_price_usd_tco2: float = Field(50.0, ge=0)
    grid_emission_factor_gco2_kwh: float = Field(400, ge=0, description="Displaced grid EF")


class GeothermalResponse(BaseModel):
    project_name: str
    plant_type: str
    plant_type_label: str
    # Cost metrics
    total_capex_musd: float
    lcoe_usd_mwh: float
    irena_lcoe_range: Dict[str, float]
    lcoe_vs_irena: str
    # Generation
    annual_generation_gwh: float
    capacity_factor_pct: float
    lifetime_generation_twh: float
    # Carbon
    plant_co2_intensity_gco2_kwh: float
    annual_emissions_tco2: float
    annual_avoided_emissions_tco2: float
    lifetime_avoided_tco2: float
    carbon_abatement_cost_usd_tco2: Optional[float]
    paris_aligned: bool
    # Resource viability
    resource_viability: str
    temp_adequacy: str
    seismicity_risk: str
    seismicity_note: str
    # Economics
    simple_payback_years: Optional[float]
    annual_revenue_musd: float
    npv_musd: float
    equity_irr_pct: Optional[float]
    # District heating
    district_heating_benefit: Dict[str, Any]
    # Benchmarks from DB
    irena_benchmarks: List[Dict[str, Any]]


@router.post("/assess", response_model=GeothermalResponse)
def assess_geothermal(req: GeothermalRequest, db: Session = Depends(get_db)):
    """Full geothermal project feasibility assessment."""
    pt = PLANT_TYPES.get(req.plant_type)
    if not pt:
        raise HTTPException(400, f"Unknown plant_type: {req.plant_type}. Use: {list(PLANT_TYPES.keys())}")

    # -- Capacity factor --
    cf = req.capacity_factor_pct if req.capacity_factor_pct else pt["cf_typical"]

    # -- Capex --
    drilling_capex = req.number_of_wells * req.drilling_cost_musd_per_well
    total_capex = drilling_capex + req.surface_plant_cost_musd

    # -- Generation --
    annual_gwh = req.installed_capacity_mw * (cf / 100) * 8760 / 1000
    lifetime_twh = annual_gwh * req.project_lifetime_years / 1000

    # -- LCOE (levelized cost of energy) --
    r = req.discount_rate_pct / 100
    n = req.project_lifetime_years
    if r > 0:
        crf = r * (1 + r) ** n / ((1 + r) ** n - 1)
    else:
        crf = 1 / n
    annual_capex_cost = total_capex * crf
    annual_cost = annual_capex_cost + req.annual_opex_musd
    lcoe = (annual_cost * 1_000_000) / (annual_gwh * 1000) if annual_gwh > 0 else 0  # USD/MWh

    # LCOE vs IRENA range
    if lcoe <= pt["lcoe_low"]:
        lcoe_vs = "Below IRENA range (very competitive)"
    elif lcoe <= pt["lcoe_high"]:
        lcoe_vs = "Within IRENA range"
    else:
        lcoe_vs = "Above IRENA range (high cost)"

    # -- Carbon --
    plant_co2 = pt["co2_gkwh"]
    annual_emissions = plant_co2 * annual_gwh * 1000 / 1_000_000  # tCO2
    annual_avoided = (req.grid_emission_factor_gco2_kwh - plant_co2) * annual_gwh * 1000 / 1_000_000
    lifetime_avoided = annual_avoided * n
    abatement_cost = None
    if annual_avoided > 0 and lcoe > 0:
        # Simplified: extra cost vs zero / grid electricity
        abatement_cost = round(lcoe * annual_gwh * 1000 / (annual_avoided * 1_000_000), 2)

    paris_aligned = plant_co2 <= 100  # IEA: <100 gCO2/kWh for Paris alignment

    # -- Resource viability --
    thresh = TEMP_THRESHOLDS.get(req.plant_type, {"min": 100, "optimal": 150})
    if req.reservoir_temp_c >= thresh["optimal"]:
        temp_adeq = "Optimal"
        viability = "High"
    elif req.reservoir_temp_c >= thresh["min"]:
        temp_adeq = "Adequate"
        viability = "Medium"
    else:
        temp_adeq = "Below minimum"
        viability = "Low"

    # Seismicity
    if req.plant_type == "egs":
        seis_risk = "high"
    elif req.well_depth_m > 4000:
        seis_risk = "high"
    elif req.well_depth_m > 2000:
        seis_risk = "medium"
    else:
        seis_risk = "low"

    # -- Economics --
    # Revenue: electricity + district heating + carbon credits
    electricity_price = lcoe * 1.1  # Assume PPA at 10% above LCOE
    annual_elec_revenue = electricity_price * annual_gwh * 1000 / 1_000_000
    carbon_revenue = annual_avoided * req.carbon_price_usd_tco2 / 1_000_000 if annual_avoided > 0 else 0
    annual_revenue = annual_elec_revenue + req.heating_revenue_musd_yr + carbon_revenue

    payback = total_capex / (annual_revenue - req.annual_opex_musd) if (annual_revenue - req.annual_opex_musd) > 0 else None

    # NPV
    annual_cf = annual_revenue - req.annual_opex_musd
    npv = -total_capex + sum(annual_cf / ((1 + r) ** t) for t in range(1, n + 1))

    # IRR (binary search)
    irr = None
    if annual_cf > 0:
        lo, hi = -0.3, 3.0
        for _ in range(100):
            mid = (lo + hi) / 2
            if mid <= -1:
                lo = mid
                continue
            npv_test = -total_capex + sum(annual_cf / ((1 + mid) ** t) for t in range(1, n + 1))
            if abs(npv_test) < 0.001:
                break
            if npv_test > 0:
                lo = mid
            else:
                hi = mid
        irr_val = (lo + hi) / 2
        if -0.3 < irr_val < 3.0:
            irr = round(irr_val * 100, 2)

    # -- IRENA benchmarks from DB --
    benchmarks = []
    try:
        rows = db.execute(text(
            "SELECT year, lcoe_usd_mwh, capacity_factor_pct, installed_cost_usd_kw "
            "FROM dh_irena_lcoe WHERE LOWER(technology) = 'geothermal' ORDER BY year"
        )).fetchall()
        benchmarks = [
            {"year": r[0], "lcoe_usd_mwh": float(r[1]) if r[1] else None,
             "capacity_factor_pct": float(r[2]) if r[2] else None,
             "installed_cost_usd_kw": float(r[3]) if r[3] else None}
            for r in rows
        ]
    except Exception:
        pass

    # -- District heating --
    dh_benefit = {
        "enabled": req.has_district_heating,
        "annual_revenue_musd": req.heating_revenue_musd_yr,
        "lcoe_reduction_pct": round(
            req.heating_revenue_musd_yr / annual_cost * 100, 1
        ) if annual_cost > 0 and req.has_district_heating else 0,
    }

    return GeothermalResponse(
        project_name=req.project_name,
        plant_type=req.plant_type,
        plant_type_label=pt["label"],
        total_capex_musd=round(total_capex, 2),
        lcoe_usd_mwh=round(lcoe, 2),
        irena_lcoe_range={"low": pt["lcoe_low"], "high": pt["lcoe_high"]},
        lcoe_vs_irena=lcoe_vs,
        annual_generation_gwh=round(annual_gwh, 2),
        capacity_factor_pct=round(cf, 1),
        lifetime_generation_twh=round(lifetime_twh, 3),
        plant_co2_intensity_gco2_kwh=plant_co2,
        annual_emissions_tco2=round(annual_emissions, 1),
        annual_avoided_emissions_tco2=round(annual_avoided, 1),
        lifetime_avoided_tco2=round(lifetime_avoided, 1),
        carbon_abatement_cost_usd_tco2=abatement_cost,
        paris_aligned=paris_aligned,
        resource_viability=viability,
        temp_adequacy=temp_adeq,
        seismicity_risk=seis_risk,
        seismicity_note=SEISMICITY_RISK[seis_risk],
        simple_payback_years=round(payback, 1) if payback else None,
        annual_revenue_musd=round(annual_revenue, 2),
        npv_musd=round(npv, 2),
        equity_irr_pct=irr,
        district_heating_benefit=dh_benefit,
        irena_benchmarks=benchmarks,
    )


@router.get("/plant-types")
def list_plant_types():
    """Return supported geothermal plant types and reference parameters."""
    return {
        k: {**v, "temp_min_c": TEMP_THRESHOLDS[k]["min"], "temp_optimal_c": TEMP_THRESHOLDS[k]["optimal"]}
        for k, v in PLANT_TYPES.items()
    }
