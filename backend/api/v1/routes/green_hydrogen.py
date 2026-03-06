"""
Green Hydrogen LCOH & Carbon Intensity Routes
Routes: /api/v1/green-hydrogen/*

Aligned with:
  IRENA Green Hydrogen Cost Reduction 2020
  IEA Global Hydrogen Review 2023
  EU Delegated Regulation 2023/1184 (RFNBO threshold)
  Hydrogen Council Global Hydrogen Flows 2023
  DOE Hydrogen Shot ($1/kg by 2031)
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.green_hydrogen_calculator import (
    GreenHydrogenInput,
    calculate_lcoh,
    REFERENCE_COSTS,
    CO2_INTENSITY_ELECTRICITY,
    ELECTROLYSER_EFFICIENCY,
    EU_RFNBO_THRESHOLD,
    IEA_GREEN_THRESHOLD,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/green-hydrogen",
    tags=["Green Hydrogen"],
)


class GreenHydrogenRequest(BaseModel):
    project_name: str = "Green H2 Project — NEOM"
    country: str = "Saudi Arabia"
    production_pathway: str = "PEM"
    capacity_mw_electrolyser: float = 100.0
    capacity_factor_pct: float = 50.0
    annual_production_kt: Optional[float] = None
    electricity_source: str = "dedicated_vre_ppa"
    electricity_price_usd_per_kwh: float = 0.035
    electrolyser_capex_usd_per_kw: float = 800.0
    electrolyser_opex_pct_capex: float = 3.0
    stack_lifetime_years: float = 10.0
    stack_replacement_cost_pct: float = 40.0
    project_lifetime_years: float = 20.0
    wacc_pct: float = 7.0
    water_cost_usd_per_tonne: float = 3.5
    water_consumption_l_per_kg_h2: float = 9.0
    water_desalination_included: bool = False
    desalination_cost_usd_per_m3: float = 0.8
    compression_storage_usd_per_kg: float = 0.30
    transport_mode: str = "pipeline"
    transport_cost_usd_per_kg: float = 0.50
    natural_gas_price_usd_per_mmbtu: float = 6.0
    ccs_capex_usd_per_tco2: float = 80.0
    ccs_capture_rate_pct: float = 90.0
    carbon_price_usd_per_tco2: float = 85.0
    subsidy_usd_per_kg: float = 0.0
    ira_45v_eligible: bool = False


@router.post("/calculate")
def compute_lcoh(payload: GreenHydrogenRequest):
    """Compute LCOH, carbon intensity and colour classification for a green hydrogen project."""
    try:
        inp = GreenHydrogenInput(**payload.dict())
        r = calculate_lcoh(inp)
        return {
            "project_name": r.project_name,
            "colour": r.colour,
            "colour_definition": r.colour_definition,
            "production": {
                "pathway": r.production_pathway,
                "annual_production_t": round(r.annual_production_t, 1),
                "annual_production_kt": round(r.annual_production_kt, 3),
            },
            "lcoh": {
                "electricity": r.lcoh_electricity,
                "electrolyser_capex": r.lcoh_electrolyser_capex,
                "opex": r.lcoh_opex,
                "water": r.lcoh_water,
                "compression_storage": r.lcoh_compression_storage,
                "transport": r.lcoh_transport,
                "stack_replacement": r.lcoh_stack_replacement,
                "total": r.lcoh_total,
                "after_subsidy": r.lcoh_after_subsidy,
            },
            "carbon_intensity": {
                "kg_co2_per_kg_h2": r.co2_intensity_kg_per_kgh2,
                "gco2_per_mj": r.co2_intensity_gco2_per_mj,
                "embedded_carbon_cost_usd_per_kg": r.embedded_carbon_cost_usd_per_kg,
                "abatement_cost_vs_grey_usd_per_tco2": r.carbon_abatement_vs_grey_usd_per_tco2,
            },
            "certification": {
                "eu_rfnbo_eligible": r.eu_rfnbo_eligible,
                "iea_green_eligible": r.iea_green_eligible,
                "low_carbon_label": r.low_carbon_label,
                "eu_rfnbo_threshold_kg_co2": EU_RFNBO_THRESHOLD,
                "iea_green_threshold_kg_co2": IEA_GREEN_THRESHOLD,
            },
            "benchmarks": {
                "vs_doe_target_pct": r.vs_doe_target_pct,
                "vs_grey_premium_pct": r.vs_grey_premium_pct,
            },
            "feasibility": r.feasibility,
            "narrative": r.narrative,
        }
    except Exception as e:
        logger.exception("Green hydrogen calculation failed")
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/reference-data")
def get_reference_data():
    """Return reference cost benchmarks and electricity CO2 intensities."""
    return {
        "reference_costs_usd_per_kg": REFERENCE_COSTS,
        "electricity_co2_intensities_kg_kwh": CO2_INTENSITY_ELECTRICITY,
        "electrolyser_efficiencies_kwh_per_kg": ELECTROLYSER_EFFICIENCY,
        "thresholds": {
            "eu_rfnbo_kg_co2_per_kgh2": EU_RFNBO_THRESHOLD,
            "iea_green_kg_co2_per_kgh2": IEA_GREEN_THRESHOLD,
            "low_carbon_kg_co2_per_kgh2": 4.0,
        },
        "sources": [
            "IRENA Green Hydrogen Cost Reduction 2020",
            "IEA Global Hydrogen Review 2023",
            "EU Delegated Regulation 2023/1184 (RFNBO)",
            "Hydrogen Council Global Hydrogen Flows 2023",
            "DOE Hydrogen Shot 2021",
            "IPHE Methodology for Determining GHG Emissions 2022",
        ],
    }


@router.get("/colour-guide")
def get_colour_guide():
    """Return the H2 colour classification guide."""
    return {
        "colours": [
            {"colour": "Green", "pathway": "Electrolysis + 100% certified renewable electricity", "co2_threshold": "< 0.5 kg CO2/kg H2 (IEA)", "certification": "IEA Green, EU RFNBO"},
            {"colour": "Green (EU RFNBO)", "pathway": "Electrolysis + renewable electricity (EU definition)", "co2_threshold": "< 3.38 kg CO2/kg H2 (EU Del. Reg. 2023/1184)", "certification": "EU RFNBO eligible"},
            {"colour": "Pink", "pathway": "Electrolysis + nuclear electricity", "co2_threshold": "~0.01 kg CO2/kg H2", "certification": "Low-carbon"},
            {"colour": "Blue", "pathway": "SMR + CCS (≥85% capture)", "co2_threshold": "1.4–2.5 kg CO2/kg H2", "certification": "Low-carbon (not green)"},
            {"colour": "Turquoise", "pathway": "Methane pyrolysis (solid carbon)", "co2_threshold": "< 1 kg CO2/kg H2", "certification": "Emerging"},
            {"colour": "Grey", "pathway": "SMR without CCS", "co2_threshold": "9–12 kg CO2/kg H2", "certification": "None"},
            {"colour": "Brown/Black", "pathway": "Coal gasification without CCS", "co2_threshold": "18–22 kg CO2/kg H2", "certification": "None"},
        ]
    }
