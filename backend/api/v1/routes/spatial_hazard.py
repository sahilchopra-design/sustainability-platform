"""
API Routes: Spatial Hazard Service
====================================
POST /api/v1/spatial-hazard/profile           — Hazard profile for a location
POST /api/v1/spatial-hazard/auto-populate     — Auto-populate CLVaR physical inputs
GET  /api/v1/spatial-hazard/ref/countries      — Supported country profiles
GET  /api/v1/spatial-hazard/ref/schema         — Hazard field schema and units
GET  /api/v1/spatial-hazard/ref/profiles       — Full country hazard profile table
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from services.spatial_hazard_service import SpatialHazardService

router = APIRouter(prefix="/api/v1/spatial-hazard", tags=["Spatial Hazard"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class HazardProfileRequest(BaseModel):
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    country: str = ""


class AutoPopulateRequest(BaseModel):
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    country: str = ""
    # User overrides — if provided, these take precedence over auto-populated values
    flood_zone: Optional[str] = None
    flood_depth_100yr_m: Optional[float] = None
    heat_days_above_35c: Optional[int] = None
    wildfire_proximity_km: Optional[float] = None
    coastal_proximity_km: Optional[float] = None
    subsidence_risk: Optional[str] = None
    water_stress_score: Optional[float] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/profile")
def get_hazard_profile(req: HazardProfileRequest):
    """Fetch physical risk hazard profile for a location (lat/lng + country)."""
    svc = SpatialHazardService()
    hp = svc.get_hazard_profile(req.latitude, req.longitude, req.country)
    return {
        "latitude": hp.latitude,
        "longitude": hp.longitude,
        "country": hp.country,
        "flood_zone": hp.flood_zone,
        "flood_depth_100yr_m": hp.flood_depth_100yr_m,
        "heat_days_above_35c": hp.heat_days_above_35c,
        "wildfire_proximity_km": hp.wildfire_proximity_km,
        "coastal_proximity_km": hp.coastal_proximity_km,
        "subsidence_risk": hp.subsidence_risk,
        "water_stress_score": hp.water_stress_score,
        "sea_level_rise_cm_2050": hp.sea_level_rise_cm_2050,
        "cyclone_exposure": hp.cyclone_exposure,
        "permafrost_risk": hp.permafrost_risk,
        "data_source": hp.data_source,
        "spatial_precision": hp.spatial_precision,
        "confidence_band": hp.confidence_band,
    }


@router.post("/auto-populate")
def auto_populate_physical_inputs(req: AutoPopulateRequest):
    """Auto-populate CLVaR physical risk inputs from location, with optional user overrides."""
    svc = SpatialHazardService()
    overrides = {}
    if req.flood_zone is not None:
        overrides["flood_zone"] = req.flood_zone
    if req.flood_depth_100yr_m is not None:
        overrides["flood_depth_100yr_m"] = req.flood_depth_100yr_m
    if req.heat_days_above_35c is not None:
        overrides["heat_days_above_35c"] = req.heat_days_above_35c
    if req.wildfire_proximity_km is not None:
        overrides["wildfire_proximity_km"] = req.wildfire_proximity_km
    if req.coastal_proximity_km is not None:
        overrides["coastal_proximity_km"] = req.coastal_proximity_km
    if req.subsidence_risk is not None:
        overrides["subsidence_risk"] = req.subsidence_risk
    if req.water_stress_score is not None:
        overrides["water_stress_score"] = req.water_stress_score

    return svc.auto_populate_physical_inputs(
        req.latitude, req.longitude, req.country, overrides or None
    )


# ---------------------------------------------------------------------------
# Reference Data Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/countries")
def ref_supported_countries():
    """List supported countries with hazard profiles."""
    return {"countries": SpatialHazardService.get_supported_countries()}


@router.get("/ref/schema")
def ref_hazard_schema():
    """Hazard field schema: types, units, ranges."""
    return {"hazard_schema": SpatialHazardService.get_hazard_schema()}


@router.get("/ref/profiles")
def ref_country_profiles():
    """Full country hazard profile reference table."""
    return {"country_profiles": SpatialHazardService.get_country_profiles()}
