"""
E58: Methane & Fugitive Emissions — API Routes

Router prefix: /api/v1/methane-fugitive
Tags: ["Methane & Fugitive Emissions"]
"""

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any

from services.methane_fugitive_engine import (
    calculate_methane_gwp_impact,
    assess_eu_methane_regulation,
    assess_ogmp_level,
    detect_super_emitters,
    calculate_methane_abatement_curve,
    assess_ldar_compliance,
    compute_methane_intensity,
    GWP_100_CH4, GWP_100_N2O, GWP_20_CH4, GWP_20_N2O,
    OGMP_LEVEL_DESCRIPTIONS, EU_METHANE_COMPLIANCE_TIMELINE,
)

router = APIRouter(prefix="/api/v1/methane-fugitive", tags=["Methane & Fugitive Emissions"])


# ---------------------------------------------------------------------------
# Pydantic request models
# ---------------------------------------------------------------------------

class GWPImpactRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    entity_id: str
    ch4_kt_pa: float = 1.0
    n2o_kt_pa: float = 0.0


class EUMethaneRegRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    entity_id: str
    sector: str = "oil_gas"
    ch4_emissions_t_pa: float = 50_000.0
    country_code: str = "DE"


class OGMPLevelRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    entity_id: str
    measurement_approach: str = "partial_measurement"
    source_level_data: bool = False
    third_party_verified: bool = False
    company_level_data: bool = True


class FacilityEmissions(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str = "Facility"
    type: str = "wellpad"
    ch4_t_pa: float = 50.0


class SuperEmittersRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    entity_id: str
    facilities: List[FacilityEmissions] = []


class AbatementCurveRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    entity_id: str
    sector: str = "oil_gas"
    total_ch4_kt_pa: float = 10.0


class LDARComplianceRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    entity_id: str
    facility_count: int = 5
    last_inspection_date: str = "2024-01-01"
    leak_detection_method: str = "ogi"


class MethaneIntensityRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    entity_id: str
    sector: str = "oil_gas"
    production_volume: float = 1_000_000.0
    production_unit: str = "boe"
    ch4_emissions_t_pa: float = 5_000.0


# ---------------------------------------------------------------------------
# POST Endpoints
# ---------------------------------------------------------------------------

@router.post("/gwp-impact")
def gwp_impact_endpoint(req: GWPImpactRequest) -> dict:
    """
    Calculate methane and N2O GHG warming impact under IPCC AR6 GWP-20 and GWP-100.

    GWP-100: CH4=29.8, N2O=273. GWP-20: CH4=82.5, N2O=273 (AR6 WG1).
    Returns tCO2e under both timeframes and short-term warming ratio.
    """
    return calculate_methane_gwp_impact(
        entity_id=req.entity_id,
        ch4_kt_pa=req.ch4_kt_pa,
        n2o_kt_pa=req.n2o_kt_pa,
    )


@router.post("/eu-regulation")
def eu_regulation_endpoint(req: EUMethaneRegRequest) -> dict:
    """
    Assess compliance with EU Methane Regulation 2024/1787.

    Covers EMTS reporting, LDAR frequency, venting prohibition (oil/gas 2025, coal 2027),
    flaring limits, and penalty framework (€250/t excess methane).
    """
    return assess_eu_methane_regulation(
        entity_id=req.entity_id,
        sector=req.sector,
        ch4_emissions_t_pa=req.ch4_emissions_t_pa,
        country_code=req.country_code,
    )


@router.post("/ogmp-level")
def ogmp_level_endpoint(req: OGMPLevelRequest) -> dict:
    """
    Assess OGMP 2.0 reporting level (L1-L5) and EU minimum requirement gap.

    EU Methane Regulation minimums: L3 by 2026, L4 by 2028.
    Returns uplift actions, timeline, and regulatory compliance year.
    """
    return assess_ogmp_level(
        entity_id=req.entity_id,
        measurement_approach=req.measurement_approach,
        source_level_data=req.source_level_data,
        third_party_verified=req.third_party_verified,
        company_level_data=req.company_level_data,
    )


@router.post("/super-emitters")
def super_emitters_endpoint(req: SuperEmittersRequest) -> dict:
    """
    Detect super-emitting facilities in a facility portfolio.

    Super-emitter thresholds: >100t CH4/event or >10kg/hr (EPA/EU).
    UNEP IMEO satellite detection: >25t/hr.
    Returns per-facility flags, regulatory notification requirements, and remediation priority.
    """
    facilities_dicts = [f.model_dump() for f in req.facilities]
    return detect_super_emitters(
        entity_id=req.entity_id,
        facilities=facilities_dicts,
    )


@router.post("/abatement-curve")
def abatement_curve_endpoint(req: AbatementCurveRequest) -> dict:
    """
    Generate marginal methane abatement cost curve.

    Based on IEA 2023 MAC curve. Includes LDAR, pneumatic devices, compressor seals,
    venting reduction, flare capture. Negative-cost options identified (commodity value recovery).
    """
    return calculate_methane_abatement_curve(
        entity_id=req.entity_id,
        sector=req.sector,
        total_ch4_kt_pa=req.total_ch4_kt_pa,
    )


@router.post("/ldar-compliance")
def ldar_compliance_endpoint(req: LDARComplianceRequest) -> dict:
    """
    Assess LDAR (Leak Detection and Repair) compliance status.

    Based on EPA 40 CFR Part 60 Subpart OOOOa/OOOOb and EU Methane Regulation Art. 14-18.
    Evaluates inspection frequency, detection method adequacy, and overdue inspections.
    """
    return assess_ldar_compliance(
        entity_id=req.entity_id,
        facility_count=req.facility_count,
        last_inspection_date=req.last_inspection_date,
        leak_detection_method=req.leak_detection_method,
    )


@router.post("/methane-intensity")
def methane_intensity_endpoint(req: MethaneIntensityRequest) -> dict:
    """
    Compute methane intensity and benchmark against IEA/UNEP targets.

    UNEP Global Methane Pledge target: 0.2% of natural gas produced.
    Returns performance tier, gap to benchmark, and abatement-to-target volume.
    """
    return compute_methane_intensity(
        entity_id=req.entity_id,
        sector=req.sector,
        production_volume=req.production_volume,
        production_unit=req.production_unit,
        ch4_emissions_t_pa=req.ch4_emissions_t_pa,
    )


# ---------------------------------------------------------------------------
# GET Reference Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/gwp-values")
def get_gwp_values() -> dict:
    """
    IPCC AR6 WG1 GWP-20 and GWP-100 reference values for key gases.
    """
    return {
        "source": "IPCC AR6 WG1 Table 7.SM.7 (2021)",
        "gwp_timeframes": {
            "GWP-100": {
                "description": "100-year global warming potential (standard for GHG accounting)",
                "CH4_fossil": GWP_100_CH4,
                "N2O": GWP_100_N2O,
                "CO2": 1.0,
                "HFC-134a": 1526.0,
                "SF6": 25200.0,
            },
            "GWP-20": {
                "description": "20-year global warming potential (short-term climate impact)",
                "CH4_fossil": GWP_20_CH4,
                "N2O": GWP_20_N2O,
                "CO2": 1.0,
                "HFC-134a": 4140.0,
                "SF6": 18300.0,
            },
        },
        "notes": [
            "CH4 GWP-20/GWP-100 ratio = 2.77x — methane is disproportionately impactful in near-term",
            "GHG Protocol uses GWP-100 as default; IPCC AR6 recommends reporting both",
            "Fossil CH4 slightly higher than biogenic CH4 due to stable carbon isotope ratios",
            "UNFCCC Annex I reporting requires GWP-100 per IPCC SAR/AR4/AR5/AR6",
        ],
    }


@router.get("/ref/ogmp-levels")
def get_ogmp_levels() -> dict:
    """
    OGMP 2.0 reporting level descriptions and EU Methane Regulation requirements.
    """
    return {
        "framework": "Oil and Gas Methane Partnership 2.0 (OGMP 2.0)",
        "administrator": "UNEP — United Nations Environment Programme",
        "eu_requirements": {
            "2026": "Minimum Level 3 per EU Methane Regulation 2024/1787",
            "2028": "Minimum Level 4 per EU Methane Regulation 2024/1787",
        },
        "levels": [
            {
                "level": k,
                "description": v,
                "data_quality": ["Very Low", "Low", "Medium", "High", "Very High"][k - 1],
                "measurement_type": [
                    "Mass balance (company-level)",
                    "Emission factors (source-level estimate)",
                    "Partial direct measurement",
                    "Full direct measurement",
                    "Verified direct measurement",
                ][k - 1],
            }
            for k, v in OGMP_LEVEL_DESCRIPTIONS.items()
        ],
    }


@router.get("/ref/eu-methane-timeline")
def get_eu_methane_timeline() -> dict:
    """
    EU Methane Regulation 2024/1787 compliance milestone timeline.
    """
    return {
        "regulation": "EU Methane Regulation 2024/1787",
        "official_title": "Regulation (EU) 2024/1787 on reducing methane emissions in the energy sector",
        "scope": "Oil, natural gas, and coal sectors operating in or supplying to the EU",
        "key_provisions": {
            "EMTS": "Energy & Methane Tracking System — mandatory reporting portal",
            "LDAR": "Leak Detection and Repair — quarterly major, biannual minor equipment",
            "venting_ban": "Routine venting prohibited: oil/gas by 2025, coal by 2027",
            "flaring": "Emergency-only flaring from entry into force",
            "super_emitter": "Notification within 5 days; remediation within 30 days",
            "penalty": "€250/tonne methane for excess emissions above allowance",
        },
        "timeline": {str(k): v for k, v in EU_METHANE_COMPLIANCE_TIMELINE.items()},
        "external_suppliers": {
            "note": "Art. 36: EU importers of oil/gas/coal must verify supplier compliance with equivalent standards",
            "phase_in": "2027 for importers",
        },
    }
