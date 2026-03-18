"""
API Routes: Technology Sector Risk & Sustainability
====================================================
POST /api/v1/technology/data-centre          — Data centre efficiency + emissions assessment
POST /api/v1/technology/cloud-emissions      — Cloud provider Scope 3 Cat 1 emissions
POST /api/v1/technology/ai-carbon            — AI model training + inference carbon footprint
POST /api/v1/technology/semiconductor-risk   — Semiconductor water + mineral supply risk
POST /api/v1/technology/ewaste               — E-waste / circular economy assessment
POST /api/v1/technology/software-carbon      — SCI (Green Software Foundation) calculation
GET  /api/v1/technology/ref/grid-factors     — Regional grid emission factors
GET  /api/v1/technology/ref/cloud-benchmarks — Cloud provider PUE + grid EF
GET  /api/v1/technology/ref/pue-benchmarks   — PUE benchmarks by facility type
GET  /api/v1/technology/ref/wue-benchmarks   — WUE benchmarks by cooling type
GET  /api/v1/technology/ref/ai-benchmarks    — AI model training energy benchmarks
GET  /api/v1/technology/ref/semiconductor    — Semiconductor water + mineral data
GET  /api/v1/technology/ref/ewaste-rates     — E-waste recycling rates by category
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from services.technology_risk_engine import (
    TechnologyRiskEngine,
    DataCentreInput,
    CloudEmissionsInput,
    AIModelCarbonInput,
    SemiconductorRiskInput,
    EWasteInput,
)

router = APIRouter(prefix="/api/v1/technology", tags=["Technology Sector"])

_engine = TechnologyRiskEngine()


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class DataCentreRequest(BaseModel):
    facility_name: str
    facility_type: str = Field("enterprise", pattern=r"^(enterprise|colocation|hyperscale|edge|telco|government)$")
    country_iso: str = "US"
    grid_region: str = "global_avg"
    pue_actual: float = Field(0, ge=0)
    wue_actual_l_kwh: float = Field(0, ge=0)
    it_load_mw: float = Field(1.0, gt=0)
    annual_it_energy_mwh: float = Field(0, ge=0)
    cooling_type: str = Field("air", pattern=r"^(air|liquid|direct_liquid|immersion|adiabatic|hybrid|free_cooling)$")
    renewable_pct: float = Field(0, ge=0, le=100)
    year_built: int = Field(2015, ge=1990)
    total_floor_area_m2: float = Field(5000, gt=0)
    embodied_carbon_known_tco2e: float = Field(0, ge=0)


class CloudEmissionsRequest(BaseModel):
    provider: str = Field("aws", pattern=r"^(aws|azure|gcp|oracle|alibaba|on_prem_avg)$")
    region: str = "us-east-1"
    compute_hours: float = Field(0, ge=0)
    gpu_hours: float = Field(0, ge=0)
    storage_tb_months: float = Field(0, ge=0)
    network_egress_tb: float = Field(0, ge=0)
    avg_cpu_utilization: float = Field(0.50, ge=0, le=1.0)
    instance_type: str = Field("general", pattern=r"^(general|compute|memory|gpu|storage)$")


class AIModelCarbonRequest(BaseModel):
    model_type: str = "custom_small"
    training_kwh: float = Field(0, ge=0)
    training_hours: float = Field(0, ge=0)
    gpu_count: int = Field(1, ge=1)
    gpu_tdp_w: float = Field(350, gt=0)
    inference_requests_per_day: float = Field(0, ge=0)
    inference_latency_ms: float = Field(50, gt=0)
    grid_region: str = "us-east-1"
    pue: float = Field(1.12, ge=1.0, le=3.0)
    model_lifetime_years: float = Field(2.0, gt=0)


class SemiconductorRiskRequest(BaseModel):
    process_node: str = "logic_14nm"
    annual_wafer_starts: int = Field(10000, ge=1)
    wafer_size_mm: int = Field(300, ge=150)
    fab_country: str = "TW"
    minerals_used: list[str] = Field(default_factory=lambda: ["gallium", "copper", "silicon_metal"])


class EWasteRequest(BaseModel):
    hardware_inventory: dict[str, int] = Field(
        default_factory=lambda: {"servers": 100, "networking": 20},
        description="Category → unit count. Categories: servers, networking, storage, desktops, laptops, monitors, mobile_phones, batteries, cables",
    )
    avg_weight_kg: Optional[dict[str, float]] = None
    replacement_cycle_years: float = Field(4.0, gt=0)
    current_recycling_pct: float = Field(0, ge=0, le=100)


class SoftwareCarbonRequest(BaseModel):
    """Green Software Foundation SCI = ((E × I) + M) / R"""
    energy_per_unit_kwh: float = Field(0.001, gt=0, description="E: Energy per functional unit (kWh)")
    grid_carbon_intensity_gco2_kwh: float = Field(436.0, gt=0, description="I: Grid carbon intensity (gCO2/kWh)")
    embodied_carbon_gco2: float = Field(0, ge=0, description="M: Amortised embodied carbon per unit (gCO2)")
    functional_unit: str = Field("API request", description="R: Functional unit definition")
    units_per_day: float = Field(1000, gt=0)
    pue: float = Field(1.2, ge=1.0, le=3.0)


# ---------------------------------------------------------------------------
# Serialisers
# ---------------------------------------------------------------------------

def _ser_dc(r) -> dict:
    return {
        "facility_name": r.facility_name,
        "facility_type": r.facility_type,
        "pue": r.pue,
        "pue_benchmark": r.pue_benchmark,
        "wue_l_kwh": r.wue_l_kwh,
        "wue_benchmark": r.wue_benchmark,
        "cue": r.cue,
        "total_energy_mwh": r.total_energy_mwh,
        "it_energy_mwh": r.it_energy_mwh,
        "overhead_mwh": r.overhead_mwh,
        "scope2_tco2e": r.scope2_tco2e,
        "scope2_market_tco2e": r.scope2_market_tco2e,
        "embodied_carbon_tco2e": r.embodied_carbon_tco2e,
        "total_carbon_tco2e": r.total_carbon_tco2e,
        "carbon_intensity_kgco2_per_kwh_it": r.carbon_intensity_kgco2_per_kwh_it,
        "annual_water_m3": r.annual_water_m3,
        "efficiency_gap_pct": r.efficiency_gap_pct,
        "recommendations": r.recommendations,
    }


def _ser_cloud(r) -> dict:
    return {
        "provider": r.provider,
        "region": r.region,
        "grid_ef_gco2_kwh": r.grid_ef_gco2_kwh,
        "pue": r.pue,
        "compute_energy_kwh": r.compute_energy_kwh,
        "gpu_energy_kwh": r.gpu_energy_kwh,
        "storage_energy_kwh": r.storage_energy_kwh,
        "network_energy_kwh": r.network_energy_kwh,
        "total_energy_kwh": r.total_energy_kwh,
        "total_energy_with_pue_kwh": r.total_energy_with_pue_kwh,
        "scope3_cat1_tco2e": r.scope3_cat1_tco2e,
        "scope2_equivalent_tco2e": r.scope2_equivalent_tco2e,
        "cloud_savings_pct": r.cloud_savings_pct,
        "carbon_per_vcpu_hour_gco2": r.carbon_per_vcpu_hour_gco2,
        "recommendation": r.recommendation,
    }


def _ser_ai(r) -> dict:
    return {
        "model_type": r.model_type,
        "training_energy_kwh": r.training_energy_kwh,
        "training_co2_tco2e": r.training_co2_tco2e,
        "inference_energy_kwh_annual": r.inference_energy_kwh_annual,
        "inference_co2_tco2e_annual": r.inference_co2_tco2e_annual,
        "total_lifetime_tco2e": r.total_lifetime_tco2e,
        "training_share_pct": r.training_share_pct,
        "inference_share_pct": r.inference_share_pct,
        "car_km_equivalent": r.car_km_equivalent,
        "household_days_equivalent": r.household_days_equivalent,
        "co2_per_1k_requests_gco2": r.co2_per_1k_requests_gco2,
        "recommendation": r.recommendation,
    }


def _ser_semi(r) -> dict:
    return {
        "process_node": r.process_node,
        "water_per_wafer_litres": r.water_per_wafer_litres,
        "annual_water_m3": r.annual_water_m3,
        "water_stress_rating": r.water_stress_rating,
        "mineral_risks": r.mineral_risks,
        "overall_supply_risk": r.overall_supply_risk,
        "hhi_avg": r.hhi_avg,
        "recommendations": r.recommendations,
    }


def _ser_ewaste(r) -> dict:
    return {
        "total_units": r.total_units,
        "total_weight_kg": r.total_weight_kg,
        "annual_ewaste_kg": r.annual_ewaste_kg,
        "annual_ewaste_tco2e": r.annual_ewaste_tco2e,
        "recycling_rate_pct": r.recycling_rate_pct,
        "recycled_kg": r.recycled_kg,
        "landfill_kg": r.landfill_kg,
        "circularity_score": r.circularity_score,
        "category_breakdown": r.category_breakdown,
        "recommendations": r.recommendations,
    }


# ---------------------------------------------------------------------------
# Endpoints — Assessments
# ---------------------------------------------------------------------------

@router.post("/data-centre", summary="Data centre efficiency + emissions assessment")
def assess_data_centre(req: DataCentreRequest):
    """
    Full data centre sustainability assessment:
    PUE/WUE/CUE efficiency, Scope 2 (location + market), embodied carbon,
    water consumption, benchmarking vs. peers, improvement recommendations.

    References: ISO 30134 (KPIs for data centres), EU EED recast Art. 12,
    The Green Grid PUE/WUE/CUE methodology.
    """
    inp = DataCentreInput(**req.model_dump())
    result = _engine.assess_data_centre(inp)
    return _ser_dc(result)


@router.post("/cloud-emissions", summary="Cloud provider Scope 3 Cat 1 emissions")
def assess_cloud_emissions(req: CloudEmissionsRequest):
    """
    Estimate Scope 3 Category 1 (purchased services) emissions from cloud workloads.
    Compares cloud vs. on-premise, accounts for provider PUE and regional grid intensity.

    References: GHG Protocol Scope 3 Cat 1, AWS/Azure/GCP public carbon disclosures.
    """
    inp = CloudEmissionsInput(**req.model_dump())
    result = _engine.assess_cloud_emissions(inp)
    return _ser_cloud(result)


@router.post("/ai-carbon", summary="AI model training + inference carbon footprint")
def assess_ai_carbon(req: AIModelCarbonRequest):
    """
    Estimate carbon footprint of AI model training and inference.
    Includes training energy, inference energy (annualized), lifetime total,
    car-km and household-day equivalences, per-request carbon intensity.

    References: Patterson et al. (2021), Strubell et al. (2019),
    Luccioni et al. (2023), IEA AI energy 2024 report.
    """
    inp = AIModelCarbonInput(**req.model_dump())
    result = _engine.assess_ai_carbon(inp)
    return _ser_ai(result)


@router.post("/semiconductor-risk", summary="Semiconductor water + mineral supply chain risk")
def assess_semiconductor_risk(req: SemiconductorRiskRequest):
    """
    Water intensity per wafer, water stress by fab location,
    critical mineral supply chain concentration (HHI-style).

    References: TSMC CSR 2024 water disclosures, IEA Critical Minerals 2024,
    SEMI S23 water conservation, EU CRM Act 2024.
    """
    inp = SemiconductorRiskInput(**req.model_dump())
    result = _engine.assess_semiconductor_risk(inp)
    return _ser_semi(result)


@router.post("/ewaste", summary="E-waste / circular economy assessment")
def assess_ewaste(req: EWasteRequest):
    """
    Hardware lifecycle e-waste estimation, recycling rate analysis,
    circularity score (0-100), embodied carbon from disposal.

    References: WEEE Directive 2012/19/EU, Basel Convention on e-waste,
    R2/e-Stewards certification, ITU Global E-waste Monitor 2024.
    """
    weights = req.avg_weight_kg or {}
    inp = EWasteInput(
        hardware_inventory=req.hardware_inventory,
        replacement_cycle_years=req.replacement_cycle_years,
        current_recycling_pct=req.current_recycling_pct,
    )
    if weights:
        inp.avg_weight_kg.update(weights)
    result = _engine.assess_ewaste(inp)
    return _ser_ewaste(result)


@router.post("/software-carbon", summary="Software Carbon Intensity (SCI) calculation")
def assess_software_carbon(req: SoftwareCarbonRequest):
    """
    Green Software Foundation SCI specification:
      SCI = ((E × I) + M) / R

    Where:
      E = energy consumed per functional unit (kWh)
      I = location-based marginal carbon intensity of the grid (gCO2eq/kWh)
      M = embodied emissions of hardware allocated per functional unit (gCO2eq)
      R = functional unit (e.g., per API request, per user, per transaction)

    References: Green Software Foundation SCI v1.0,
    ISO 14044 Life Cycle Assessment methodology applied to digital products.
    """
    e = req.energy_per_unit_kwh * req.pue
    i = req.grid_carbon_intensity_gco2_kwh
    m = req.embodied_carbon_gco2

    sci_gco2 = (e * i) + m
    sci_tco2_per_million = sci_gco2 * 1_000_000 / 1_000_000  # gCO2 per unit → tCO2 per M units
    daily_gco2 = sci_gco2 * req.units_per_day
    annual_tco2e = daily_gco2 * 365 / 1_000_000

    # Benchmark bands (Green Software Foundation guidance)
    if sci_gco2 < 0.5:
        rating = "A"
        label = "Ultra-low carbon"
    elif sci_gco2 < 2.0:
        rating = "B"
        label = "Low carbon"
    elif sci_gco2 < 10.0:
        rating = "C"
        label = "Moderate carbon"
    elif sci_gco2 < 50.0:
        rating = "D"
        label = "High carbon"
    else:
        rating = "E"
        label = "Very high carbon"

    recs = []
    if e * i > m:
        recs.append("Operational carbon dominates — optimize energy (caching, efficient algorithms) or use greener grid.")
    else:
        recs.append("Embodied carbon dominates — extend hardware lifetime or switch to shared/cloud infra.")
    if req.grid_carbon_intensity_gco2_kwh > 300:
        recs.append(f"Grid intensity {req.grid_carbon_intensity_gco2_kwh:.0f} gCO2/kWh is above EU avg. Consider region migration.")

    return {
        "sci_gco2_per_unit": round(sci_gco2, 4),
        "functional_unit": req.functional_unit,
        "operational_carbon_gco2": round(e * i, 4),
        "embodied_carbon_gco2": round(m, 4),
        "sci_rating": rating,
        "sci_label": label,
        "daily_emissions_gco2": round(daily_gco2, 2),
        "annual_emissions_tco2e": round(annual_tco2e, 4),
        "units_per_day": req.units_per_day,
        "pue_applied": req.pue,
        "methodology": "Green Software Foundation SCI v1.0 + ISO 14044 proxy",
        "recommendations": recs,
    }


# ---------------------------------------------------------------------------
# Expert-Grade Endpoints — Regulatory + Integrated
# ---------------------------------------------------------------------------

@router.post("/eed-compliance", summary="EU EED recast Art. 12 compliance check")
def eed_compliance(req: DataCentreRequest):
    """
    EU Energy Efficiency Directive (recast 2023/1791) Article 12 compliance.
    Mandatory for data centres with IT load >= 500 kW (from 15 May 2024).
    Returns ISO 30134 KPI suite (PUE/WUE/CUE/REF/ERF), compliance status
    per Delegated Regulation (EU) 2024/1364, and improvement trajectory.

    References: Directive 2023/1791 Art. 12, Delegated Reg. 2024/1364,
    ISO 30134 series (Parts 2/3/4/6/8), ASHRAE A1 thermal envelope.
    """
    inp = DataCentreInput(**req.model_dump())
    return _engine.eed_compliance_check(inp)


class IntegratedTechRequest(BaseModel):
    """Comprehensive technology entity assessment across all sub-modules."""
    entity_name: str
    data_centres: list[DataCentreRequest] = Field(default_factory=list)
    cloud_usage: Optional[CloudEmissionsRequest] = None
    ai_models: list[AIModelCarbonRequest] = Field(default_factory=list)
    semiconductor: Optional[SemiconductorRiskRequest] = None
    ewaste: Optional[EWasteRequest] = None


@router.post("/integrated-assessment", summary="Unified technology entity sustainability profile")
def integrated_assessment(req: IntegratedTechRequest):
    """
    Comprehensive technology entity sustainability assessment.
    Aggregates data centre, cloud, AI, semiconductor, and e-waste sub-modules
    into a unified ESG score, CSRD E1/E3/E5 auto-populated data points,
    and regulatory readiness profile.

    Output includes:
    - Total Scope 2 + Scope 3 emissions
    - Total water consumption
    - Annual e-waste generation
    - Composite ESG score (E: 60%, S: 20%, G: 20%)
    - CSRD E1 (climate), E3 (water), E5 (circular economy) data points
    - Per-module detailed results
    - Consolidated recommendations

    References: ESRS E1/E3/E5, ISO 30134, GHG Protocol Scope 2/3,
    Green Software Foundation SCI, WEEE Directive, EU CRM Act.
    """
    dc_inputs = [DataCentreInput(**d.model_dump()) for d in req.data_centres] or None
    cloud_input = CloudEmissionsInput(**req.cloud_usage.model_dump()) if req.cloud_usage else None
    ai_inputs = [AIModelCarbonInput(**a.model_dump()) for a in req.ai_models] or None
    semi_input = SemiconductorRiskInput(**req.semiconductor.model_dump()) if req.semiconductor else None

    ewaste_input = None
    if req.ewaste:
        weights = req.ewaste.avg_weight_kg or {}
        ewaste_input = EWasteInput(
            hardware_inventory=req.ewaste.hardware_inventory,
            replacement_cycle_years=req.ewaste.replacement_cycle_years,
            current_recycling_pct=req.ewaste.current_recycling_pct,
        )
        if weights:
            ewaste_input.avg_weight_kg.update(weights)

    return _engine.integrated_assessment(
        entity_name=req.entity_name,
        data_centres=dc_inputs,
        cloud_usage=cloud_input,
        ai_models=ai_inputs,
        semiconductor=semi_input,
        ewaste=ewaste_input,
    )


# ---------------------------------------------------------------------------
# Reference Data Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/grid-factors", summary="Regional grid emission factors")
def ref_grid_factors():
    return {"source": "IEA 2024 estimates (gCO2/kWh)", "factors": _engine.get_grid_emission_factors()}


@router.get("/ref/cloud-benchmarks", summary="Cloud provider PUE + grid benchmarks")
def ref_cloud_benchmarks():
    return _engine.get_cloud_provider_benchmarks()


@router.get("/ref/pue-benchmarks", summary="PUE benchmarks by facility type")
def ref_pue_benchmarks():
    return {"source": "Uptime Institute 2024 Global Survey", "benchmarks": _engine.get_pue_benchmarks()}


@router.get("/ref/wue-benchmarks", summary="WUE benchmarks by cooling type")
def ref_wue_benchmarks():
    return {"source": "The Green Grid WUE methodology", "benchmarks": _engine.get_wue_benchmarks()}


@router.get("/ref/ai-benchmarks", summary="AI model training energy benchmarks")
def ref_ai_benchmarks():
    return {"source": "Published research 2019-2024", "models": _engine.get_ai_training_benchmarks()}


@router.get("/ref/semiconductor", summary="Semiconductor water + mineral data")
def ref_semiconductor():
    return _engine.get_semiconductor_water_data()


@router.get("/ref/ewaste-rates", summary="E-waste recycling rates by category")
def ref_ewaste_rates():
    return {"source": "ITU Global E-waste Monitor 2024 / WEEE Directive", "rates": _engine.get_ewaste_recycling_rates()}
