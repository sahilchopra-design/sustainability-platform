"""
Energy Emissions API
=====================
Endpoints for methane OGMP 2.0, Scope 3 Category 11, and CSRD
auto-population.
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from services.methane_ogmp import (
    MethaneOGMPEngine,
    MethaneSource,
    SOURCE_CATEGORIES,
    OGMP_LEVELS,
    ABATEMENT_MEASURES,
)
from services.scope3_cat11 import (
    Scope3Cat11Engine,
    FuelSoldInput,
    ProductSoldInput,
    FUEL_COMBUSTION_EF,
    PRODUCT_USE_PROFILES,
)
from services.csrd_auto_populate import (
    CSRDAutoPopulateEngine,
    ModuleOutput,
    ESRS_MAPPINGS,
    ESRS_MINIMUMS,
)

router = APIRouter(prefix="/api/v1/energy-emissions", tags=["Energy Emissions"])

_methane = MethaneOGMPEngine()
_scope3 = Scope3Cat11Engine()
_csrd_auto = CSRDAutoPopulateEngine()


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class MethaneSourceModel(BaseModel):
    source_id: str
    category: str
    facility_name: str
    ogmp_level: int = Field(2, ge=1, le=5)
    measured_tch4_yr: float = Field(0, ge=0)
    activity_bcm_yr: float = Field(0, ge=0)
    custom_ef_tch4_bcm: float = Field(0, ge=0)


class FacilityMethaneRequest(BaseModel):
    facility_name: str
    sources: list[MethaneSourceModel]
    production_bcm_yr: float = Field(0, ge=0)


class FuelSoldModel(BaseModel):
    fuel_type: str
    volume_sold: float = Field(ge=0)
    year: int = 2024


class ProductSoldModel(BaseModel):
    product_type: str
    units_sold: int = Field(ge=0)
    grid_ef_tco2_mwh: float = Field(0.40, ge=0)
    year: int = 2024


class Scope3Cat11Request(BaseModel):
    fuels: list[FuelSoldModel] = []
    products: list[ProductSoldModel] = []
    reporting_year: int = 2024
    revenue_m_eur: float = Field(0, ge=0)


class ModuleOutputModel(BaseModel):
    module: str
    field: str
    value: float
    unit: str = ""
    year: int = 2024


class CSRDAutoPopulateRequest(BaseModel):
    entity_name: str
    module_outputs: list[ModuleOutputModel]
    reporting_year: int = 2024


# ---------------------------------------------------------------------------
# Serialisers
# ---------------------------------------------------------------------------

def _ser_methane_source(r) -> dict:
    return {
        "source_id": r.source_id,
        "category": r.category,
        "category_label": r.category_label,
        "facility_name": r.facility_name,
        "ogmp_level": r.ogmp_level,
        "ogmp_level_label": r.ogmp_level_label,
        "emissions_tch4": r.emissions_tch4,
        "emissions_tco2e_gwp100": r.emissions_tco2e_gwp100,
        "emissions_tco2e_gwp20": r.emissions_tco2e_gwp20,
        "method_used": r.method_used,
        "abatement_potential_tch4": r.abatement_potential_tch4,
        "recommended_measures": r.recommended_measures,
    }


def _ser_facility(r) -> dict:
    return {
        "facility_name": r.facility_name,
        "source_results": [_ser_methane_source(s) for s in r.source_results],
        "total_tch4": r.total_tch4,
        "total_tco2e_gwp100": r.total_tco2e_gwp100,
        "total_tco2e_gwp20": r.total_tco2e_gwp20,
        "methane_intensity_tch4_bcm": r.methane_intensity_tch4_bcm,
        "total_activity_bcm": r.total_activity_bcm,
        "abatement_potential_tch4": r.abatement_potential_tch4,
        "abatement_potential_pct": r.abatement_potential_pct,
        "weighted_ogmp_level": r.weighted_ogmp_level,
        "eu_methane_reg_compliant": r.eu_methane_reg_compliant,
        "reduction_pathway": r.reduction_pathway,
    }


def _ser_scope3(r) -> dict:
    return {
        "reporting_year": r.reporting_year,
        "fuel_results": [
            {
                "fuel_type": f.fuel_type,
                "fuel_label": f.fuel_label,
                "volume_sold": f.volume_sold,
                "unit": f.unit,
                "ef_tco2_per_unit": f.ef_tco2_per_unit,
                "total_tco2": f.total_tco2,
            }
            for f in r.fuel_results
        ],
        "product_results": [
            {
                "product_type": p.product_type,
                "product_label": p.product_label,
                "units_sold": p.units_sold,
                "lifetime_years": p.lifetime_years,
                "annual_tco2_per_unit": p.annual_tco2_per_unit,
                "lifetime_tco2_per_unit": p.lifetime_tco2_per_unit,
                "total_lifetime_tco2": p.total_lifetime_tco2,
            }
            for p in r.product_results
        ],
        "total_fuel_tco2": r.total_fuel_tco2,
        "total_product_lifetime_tco2": r.total_product_lifetime_tco2,
        "total_cat11_tco2": r.total_cat11_tco2,
        "top_contributor": r.top_contributor,
        "top_contributor_pct": r.top_contributor_pct,
        "intensity_tco2_per_m_revenue": r.intensity_tco2_per_m_revenue,
    }


def _ser_csrd_auto(r) -> dict:
    return {
        "entity_name": r.entity_name,
        "reporting_year": r.reporting_year,
        "populated_dps": [
            {
                "dp_id": p.dp_id,
                "esrs": p.esrs,
                "dr": p.dr,
                "label": p.label,
                "value": p.value,
                "unit": p.unit,
                "source_module": p.source_module,
                "confidence": p.confidence,
            }
            for p in r.populated_dps
        ],
        "total_mappable_dps": r.total_mappable_dps,
        "populated_count": r.populated_count,
        "population_rate_pct": r.population_rate_pct,
        "gaps": r.gaps,
        "esrs_coverage": r.esrs_coverage,
        "readiness_rating": r.readiness_rating,
    }


# ---------------------------------------------------------------------------
# Endpoints — Methane OGMP 2.0
# ---------------------------------------------------------------------------

@router.post("/methane-facility", summary="Facility methane assessment (OGMP 2.0)")
def methane_facility(req: FacilityMethaneRequest):
    sources = [
        MethaneSource(
            source_id=s.source_id,
            category=s.category,
            facility_name=s.facility_name,
            ogmp_level=s.ogmp_level,
            measured_tch4_yr=s.measured_tch4_yr,
            activity_bcm_yr=s.activity_bcm_yr,
            custom_ef_tch4_bcm=s.custom_ef_tch4_bcm,
        )
        for s in req.sources
    ]
    res = _methane.assess_facility(
        facility_name=req.facility_name,
        sources=sources,
        production_bcm_yr=req.production_bcm_yr,
    )
    return _ser_facility(res)


# ---------------------------------------------------------------------------
# Endpoints — Scope 3 Category 11
# ---------------------------------------------------------------------------

@router.post("/scope3-cat11", summary="Scope 3 Cat 11 — Use of Sold Products")
def scope3_cat11(req: Scope3Cat11Request):
    fuels = [FuelSoldInput(fuel_type=f.fuel_type, volume_sold=f.volume_sold, year=f.year) for f in req.fuels]
    products = [ProductSoldInput(product_type=p.product_type, units_sold=p.units_sold,
                                  grid_ef_tco2_mwh=p.grid_ef_tco2_mwh, year=p.year) for p in req.products]
    res = _scope3.assess(fuels=fuels, products=products, reporting_year=req.reporting_year,
                         revenue_m_eur=req.revenue_m_eur)
    return _ser_scope3(res)


# ---------------------------------------------------------------------------
# Endpoints — CSRD Auto-Population
# ---------------------------------------------------------------------------

@router.post("/csrd-auto-populate", summary="Auto-populate ESRS data points from module outputs")
def csrd_auto_populate(req: CSRDAutoPopulateRequest):
    outputs = [
        ModuleOutput(module=o.module, field=o.field, value=o.value, unit=o.unit, year=o.year)
        for o in req.module_outputs
    ]
    res = _csrd_auto.populate(
        entity_name=req.entity_name,
        module_outputs=outputs,
        reporting_year=req.reporting_year,
    )
    return _ser_csrd_auto(res)


# ---------------------------------------------------------------------------
# Reference Data Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/methane-source-categories", summary="Methane source categories")
def ref_methane_categories():
    return _methane.get_source_categories()

@router.get("/ref/ogmp-levels", summary="OGMP 2.0 reporting levels")
def ref_ogmp_levels():
    return _methane.get_ogmp_levels()

@router.get("/ref/abatement-measures", summary="Methane abatement measures")
def ref_abatement_measures():
    return _methane.get_abatement_measures()

@router.get("/ref/fuel-combustion-efs", summary="Fuel combustion emission factors")
def ref_fuel_efs():
    return _scope3.get_fuel_efs()

@router.get("/ref/product-use-profiles", summary="Energy-using product profiles")
def ref_product_profiles():
    return _scope3.get_product_profiles()

@router.get("/ref/esrs-mappings", summary="ESRS data point to module mappings")
def ref_esrs_mappings():
    return _csrd_auto.get_mappings()

@router.get("/ref/esrs-minimums", summary="Minimum DPs per ESRS standard")
def ref_esrs_minimums():
    return _csrd_auto.get_esrs_minimums()
