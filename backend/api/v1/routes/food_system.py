"""
API Routes: Food System & Land Use Finance (E54)
================================================
POST /api/v1/food-system/sbti-flag              — SBTi FLAG target assessment
POST /api/v1/food-system/fao-crop-yield         — FAO crop yield RCP projections
POST /api/v1/food-system/tnfd-food-leap         — TNFD LEAP food assessment
POST /api/v1/food-system/eudr-food              — EUDR deforestation-free screening
POST /api/v1/food-system/agricultural-emissions — Farm-level GHG accounting
POST /api/v1/food-system/flag-targets           — SBTi FLAG intervention roadmap
POST /api/v1/food-system/land-degradation       — LDN status and restoration
GET  /api/v1/food-system/ref/flag-sectors       — SBTi FLAG sector definitions
GET  /api/v1/food-system/ref/crop-regions       — FAO crop-region combinations
GET  /api/v1/food-system/ref/eudr-commodities   — EUDR food commodity list
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from services.food_system_engine import (
    FoodSystemEngine,
    FLAG_SECTORS,
    CROPS,
    REGIONS,
    EUDR_FOOD_COMMODITIES,
)

router = APIRouter(
    prefix="/api/v1/food-system",
    tags=["Food System & Land Use"],
)

_engine = FoodSystemEngine()


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class SBTiFLAGRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    entity_id: str
    sector: str = Field(..., description="cattle | poultry_pigs | crops | forests_trees | other")
    base_year: int = Field(2020, ge=2000, le=2030)
    target_year: int = Field(2030, ge=2025, le=2050)
    current_emissions_tco2e: float = Field(..., ge=0)


class FAOCropYieldRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    entity_id: str
    crop: str = Field(..., description="wheat | maize | rice | soy | coffee | cocoa | sugarcane")
    region: str = Field(..., description="south_asia | sub_saharan_africa | latin_america | southeast_asia | europe")
    baseline_yield_t_ha: float = Field(..., ge=0)


class TNFDFoodLEAPRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    entity_id: str
    entity_name: str
    commodities: list[str] = Field(default_factory=list)


class EUDRFoodRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    entity_id: str
    commodities: list[str] = Field(default_factory=list)
    country_codes: list[str] = Field(default_factory=list)


class AgriculturalEmissionsRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    entity_id: str
    farm_area_ha: float = Field(..., ge=0)
    livestock_count: int = Field(0, ge=0)
    crop_type: str = "mixed"


class FLAGTargetsRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    entity_id: str
    assessment_id: str
    sector: str
    base_emissions: float = Field(..., ge=0)
    target_year: int = Field(2030, ge=2025, le=2050)


class LandDegradationRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    entity_id: str
    land_area_ha: float = Field(..., ge=0)
    land_use: str = Field(..., description="forest | cropland | pasture | wetland | grassland | shrubland")
    country_code: str = Field(..., min_length=2, max_length=3)


# ---------------------------------------------------------------------------
# POST Endpoints
# ---------------------------------------------------------------------------

@router.post("/sbti-flag")
def sbti_flag(req: SBTiFLAGRequest) -> dict:
    """SBTi FLAG science-based target assessment with sector-specific reduction requirements."""
    return _engine.assess_sbti_flag(
        entity_id=req.entity_id,
        sector=req.sector,
        base_year=req.base_year,
        target_year=req.target_year,
        current_emissions_tco2e=req.current_emissions_tco2e,
    )


@router.post("/fao-crop-yield")
def fao_crop_yield(req: FAOCropYieldRequest) -> dict:
    """FAO GAEZ crop yield projections under RCP 2.6, 4.5, and 8.5 with adaptation scenarios."""
    return _engine.model_fao_crop_yield(
        entity_id=req.entity_id,
        crop=req.crop,
        region=req.region,
        baseline_yield_t_ha=req.baseline_yield_t_ha,
    )


@router.post("/tnfd-food-leap")
def tnfd_food_leap(req: TNFDFoodLEAPRequest) -> dict:
    """TNFD LEAP (Locate, Evaluate, Assess, Prepare) approach for food company nature risks."""
    return _engine.assess_tnfd_food_leap(
        entity_id=req.entity_id,
        entity_name=req.entity_name,
        commodities=req.commodities,
    )


@router.post("/eudr-food")
def eudr_food(req: EUDRFoodRequest) -> dict:
    """EUDR Art 29 deforestation-free commodity screening for food supply chains."""
    return _engine.assess_eudr_food(
        entity_id=req.entity_id,
        commodities=req.commodities,
        country_codes=req.country_codes,
    )


@router.post("/agricultural-emissions")
def agricultural_emissions(req: AgriculturalEmissionsRequest) -> dict:
    """Farm-level GHG accounting: Scope 1/2/3 with PCAF DQS and reduction pathway."""
    return _engine.compute_agricultural_emissions(
        entity_id=req.entity_id,
        farm_area_ha=req.farm_area_ha,
        livestock_count=req.livestock_count,
        crop_type=req.crop_type,
    )


@router.post("/flag-targets")
def flag_targets(req: FLAGTargetsRequest) -> dict:
    """SBTi FLAG intervention roadmap with abatement actions, costs, and timeline."""
    return _engine.set_flag_targets(
        entity_id=req.entity_id,
        assessment_id=req.assessment_id,
        sector=req.sector,
        base_emissions=req.base_emissions,
        target_year=req.target_year,
    )


@router.post("/land-degradation")
def land_degradation(req: LandDegradationRequest) -> dict:
    """LDN assessment per UN SDG 15.3: status, carbon stocks, and restoration potential."""
    return _engine.assess_land_degradation(
        entity_id=req.entity_id,
        land_area_ha=req.land_area_ha,
        land_use=req.land_use,
        country_code=req.country_code,
    )


# ---------------------------------------------------------------------------
# GET Reference Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/flag-sectors")
def ref_flag_sectors() -> dict:
    """SBTi FLAG sector definitions, reduction requirements, and target years."""
    sectors = []
    for name, params in FLAG_SECTORS.items():
        sectors.append({
            "sector": name,
            "flag_scope": params["scope"],
            "required_reduction_pct": params["reduction_pct"],
            "removal_target_pct": params["removal_pct"],
            "target_year": params["target_year"],
            "base_year": 2020,
        })
    return {
        "sectors": sectors,
        "standard": "SBTi FLAG v1.0 (2022)",
        "scope": "Forests, Land & Agriculture",
        "sbti_website": "https://sciencebasedtargets.org/sectors/forest-land-and-agriculture",
    }


@router.get("/ref/crop-regions")
def ref_crop_regions() -> dict:
    """FAO GAEZ crop-region combinations and climate vulnerability notes."""
    combinations = []
    for crop in CROPS:
        for region in REGIONS:
            combinations.append({"crop": crop, "region": region})
    return {
        "crops": CROPS,
        "regions": REGIONS,
        "combinations": combinations,
        "source": "FAO GAEZ v4 + IPCC AR6 Chapter 5",
        "rcp_scenarios": ["rcp26", "rcp45", "rcp85"],
        "projection_year": 2050,
    }


@router.get("/ref/eudr-commodities")
def ref_eudr_commodities() -> dict:
    """EUDR food commodity list per Annex I of Regulation (EU) 2023/1115."""
    commodity_details = [
        {"commodity": "cattle",    "regulation_article": "Annex I", "cutoff_date": "2020-12-31", "derived_products": ["beef", "leather", "tallow"]},
        {"commodity": "cocoa",     "regulation_article": "Annex I", "cutoff_date": "2020-12-31", "derived_products": ["cocoa_butter", "chocolate"]},
        {"commodity": "coffee",    "regulation_article": "Annex I", "cutoff_date": "2020-12-31", "derived_products": ["roasted_coffee", "instant_coffee"]},
        {"commodity": "oil_palm",  "regulation_article": "Annex I", "cutoff_date": "2020-12-31", "derived_products": ["palm_oil", "palm_kernel_oil"]},
        {"commodity": "soy",       "regulation_article": "Annex I", "cutoff_date": "2020-12-31", "derived_products": ["soy_oil", "soy_meal", "tofu"]},
    ]
    return {
        "eudr_food_commodities": sorted(EUDR_FOOD_COMMODITIES),
        "commodity_details": commodity_details,
        "regulation": "Regulation (EU) 2023/1115",
        "enforcement_date_large_operators": "2025-12-30",
        "enforcement_date_sme": "2026-06-30",
    }
