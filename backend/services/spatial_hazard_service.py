"""
Spatial Hazard Service
=======================
Fetches physical risk hazard data for a given location (lat/lng).

Architecture
- Phase 1 (current): Country/region-level hazard profiles (deterministic reference data)
- Phase 2 (planned): PostGIS ST_DWithin queries against raster hazard layers
- Phase 3 (planned): External API integration (JBA flood, WRI Aqueduct, GFED wildfire)

PostGIS spatial columns exist on:
- valuation_assets.location      GEOGRAPHY(POINT, 4326) + GIST index
- nature_risk_sites.location     GEOGRAPHY(POINT, 4326) + GIST index
- cat_risk_properties.location   GEOGRAPHY(POINT, 4326) + GIST index
- power_plant_assets.location    GEOGRAPHY(POINT, 4326) + GIST index

Standards & References
- EA Flood Risk Zones (UK): Zone 1/2/3a/3b
- FEMA NFIP Zones (US): A/AE/V/X
- WRI Aqueduct Water Stress (global): 0-5 scale
- IPCC AR6 WG2 Ch.4: Hazard-Exposure-Vulnerability framework
- JRC PESETA IV: EU climate damage projections
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
import math


# ---------------------------------------------------------------------------
# Country/Region Hazard Profiles
# Phase 1: deterministic reference data, upgradeable to spatial rasters
# Sources: JRC PESETA IV, EEA, EA, WRI Aqueduct, EM-DAT
# ---------------------------------------------------------------------------

COUNTRY_HAZARD_PROFILES: dict[str, dict[str, Any]] = {
    "GB": {
        "flood_zone": "2",                  # EA zone 2 avg (medium probability)
        "flood_depth_100yr_m": 0.4,
        "heat_days_above_35c": 3,
        "wildfire_proximity_km": 50,
        "coastal_proximity_km": 40,          # island nation avg
        "subsidence_risk": "low",
        "water_stress_score": 1.8,           # WRI Aqueduct GB avg
        "sea_level_rise_cm_2050": 30,
        "cyclone_exposure": "none",
        "permafrost_risk": "none",
    },
    "DE": {
        "flood_zone": "2",
        "flood_depth_100yr_m": 0.5,
        "heat_days_above_35c": 8,
        "wildfire_proximity_km": 60,
        "coastal_proximity_km": 100,
        "subsidence_risk": "low",
        "water_stress_score": 2.2,
        "sea_level_rise_cm_2050": 25,
        "cyclone_exposure": "none",
        "permafrost_risk": "none",
    },
    "NL": {
        "flood_zone": "3a",                 # high flood risk country
        "flood_depth_100yr_m": 1.2,
        "heat_days_above_35c": 5,
        "wildfire_proximity_km": 100,
        "coastal_proximity_km": 15,
        "subsidence_risk": "high",            # polder subsidence
        "water_stress_score": 2.5,
        "sea_level_rise_cm_2050": 35,
        "cyclone_exposure": "none",
        "permafrost_risk": "none",
    },
    "FR": {
        "flood_zone": "2",
        "flood_depth_100yr_m": 0.5,
        "heat_days_above_35c": 12,           # post-2022/2023 heatwaves
        "wildfire_proximity_km": 30,          # Var, Gironde fires
        "coastal_proximity_km": 80,
        "subsidence_risk": "low",
        "water_stress_score": 2.0,
        "sea_level_rise_cm_2050": 28,
        "cyclone_exposure": "none",
        "permafrost_risk": "none",
    },
    "ES": {
        "flood_zone": "2",
        "flood_depth_100yr_m": 0.6,
        "heat_days_above_35c": 25,
        "wildfire_proximity_km": 15,
        "coastal_proximity_km": 60,
        "subsidence_risk": "low",
        "water_stress_score": 3.5,           # southern Spain severe stress
        "sea_level_rise_cm_2050": 30,
        "cyclone_exposure": "none",
        "permafrost_risk": "none",
    },
    "IT": {
        "flood_zone": "2",
        "flood_depth_100yr_m": 0.5,
        "heat_days_above_35c": 20,
        "wildfire_proximity_km": 20,
        "coastal_proximity_km": 50,
        "subsidence_risk": "medium",          # Venice, Po Delta
        "water_stress_score": 2.8,
        "sea_level_rise_cm_2050": 28,
        "cyclone_exposure": "none",
        "permafrost_risk": "none",
    },
    "US": {
        "flood_zone": "X",                  # FEMA X national avg
        "flood_depth_100yr_m": 0.3,
        "heat_days_above_35c": 15,
        "wildfire_proximity_km": 25,
        "coastal_proximity_km": 100,
        "subsidence_risk": "low",
        "water_stress_score": 2.5,
        "sea_level_rise_cm_2050": 30,
        "cyclone_exposure": "moderate",       # Gulf/Atlantic coast
        "permafrost_risk": "none",
    },
    "AU": {
        "flood_zone": "2",
        "flood_depth_100yr_m": 0.5,
        "heat_days_above_35c": 35,
        "wildfire_proximity_km": 10,          # bushfire exposure
        "coastal_proximity_km": 50,
        "subsidence_risk": "low",
        "water_stress_score": 3.0,
        "sea_level_rise_cm_2050": 30,
        "cyclone_exposure": "moderate",       # QLD, WA
        "permafrost_risk": "none",
    },
    "SG": {
        "flood_zone": "2",
        "flood_depth_100yr_m": 0.3,
        "heat_days_above_35c": 50,           # equatorial
        "wildfire_proximity_km": 200,
        "coastal_proximity_km": 5,
        "subsidence_risk": "medium",
        "water_stress_score": 4.0,            # island water scarcity
        "sea_level_rise_cm_2050": 40,
        "cyclone_exposure": "low",
        "permafrost_risk": "none",
    },
    "IN": {
        "flood_zone": "3a",
        "flood_depth_100yr_m": 1.0,
        "heat_days_above_35c": 60,
        "wildfire_proximity_km": 50,
        "coastal_proximity_km": 80,
        "subsidence_risk": "medium",
        "water_stress_score": 4.2,
        "sea_level_rise_cm_2050": 35,
        "cyclone_exposure": "high",
        "permafrost_risk": "none",
    },
    "CN": {
        "flood_zone": "2",
        "flood_depth_100yr_m": 0.8,
        "heat_days_above_35c": 20,
        "wildfire_proximity_km": 60,
        "coastal_proximity_km": 100,
        "subsidence_risk": "medium",
        "water_stress_score": 3.3,
        "sea_level_rise_cm_2050": 30,
        "cyclone_exposure": "moderate",
        "permafrost_risk": "low",
    },
    "BR": {
        "flood_zone": "2",
        "flood_depth_100yr_m": 0.6,
        "heat_days_above_35c": 30,
        "wildfire_proximity_km": 20,
        "coastal_proximity_km": 100,
        "subsidence_risk": "low",
        "water_stress_score": 2.0,
        "sea_level_rise_cm_2050": 25,
        "cyclone_exposure": "none",
        "permafrost_risk": "none",
    },
    "JP": {
        "flood_zone": "3a",
        "flood_depth_100yr_m": 0.8,
        "heat_days_above_35c": 15,
        "wildfire_proximity_km": 80,
        "coastal_proximity_km": 30,
        "subsidence_risk": "medium",
        "water_stress_score": 2.8,
        "sea_level_rise_cm_2050": 35,
        "cyclone_exposure": "high",           # typhoons
        "permafrost_risk": "none",
    },
    "AE": {
        "flood_zone": "1",
        "flood_depth_100yr_m": 0.2,
        "heat_days_above_35c": 120,
        "wildfire_proximity_km": 200,
        "coastal_proximity_km": 20,
        "subsidence_risk": "low",
        "water_stress_score": 4.8,            # extreme water stress
        "sea_level_rise_cm_2050": 35,
        "cyclone_exposure": "low",
        "permafrost_risk": "none",
    },
    "CA": {
        "flood_zone": "2",
        "flood_depth_100yr_m": 0.4,
        "heat_days_above_35c": 5,
        "wildfire_proximity_km": 15,          # BC, Alberta fires
        "coastal_proximity_km": 100,
        "subsidence_risk": "low",
        "water_stress_score": 1.5,
        "sea_level_rise_cm_2050": 25,
        "cyclone_exposure": "none",
        "permafrost_risk": "moderate",         # northern territories
    },
}

# Default profile for unknown countries
_DEFAULT_PROFILE: dict[str, Any] = {
    "flood_zone": "2",
    "flood_depth_100yr_m": 0.5,
    "heat_days_above_35c": 10,
    "wildfire_proximity_km": 50,
    "coastal_proximity_km": 80,
    "subsidence_risk": "low",
    "water_stress_score": 2.0,
    "sea_level_rise_cm_2050": 30,
    "cyclone_exposure": "low",
    "permafrost_risk": "none",
}


# Latitude-based hazard modifiers (tropical belt, polar, etc.)
def _latitude_modifier(lat: float) -> dict[str, float]:
    """Adjust hazard intensities based on latitude band."""
    abs_lat = abs(lat)
    mods: dict[str, float] = {}
    if abs_lat < 23.5:
        # Tropical
        mods["heat_days_multiplier"] = 1.5
        mods["cyclone_multiplier"] = 1.3
        mods["wildfire_multiplier"] = 0.8
    elif abs_lat < 35:
        # Subtropical
        mods["heat_days_multiplier"] = 1.2
        mods["wildfire_multiplier"] = 1.3
        mods["water_stress_adder"] = 0.5
    elif abs_lat < 55:
        # Temperate
        mods["heat_days_multiplier"] = 1.0
        mods["wildfire_multiplier"] = 1.0
    else:
        # Sub-polar / Polar
        mods["heat_days_multiplier"] = 0.3
        mods["permafrost_amplifier"] = 2.0
        mods["wildfire_multiplier"] = 0.5
    return mods


# Coastal proximity estimator from longitude for island nations / coastal cities
def _estimate_coastal_km(lat: float, lng: float, country: str) -> Optional[float]:
    """Rough coastal proximity (Phase 1 heuristic, Phase 2 uses coastline raster)."""
    # Very rough: small island states
    if country in ("SG", "MT", "CY", "MV", "BH"):
        return 5.0
    return None  # use country default


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class HazardProfile:
    """Physical risk hazard data for a location."""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    country: str = ""
    # Hazard fields (compatible with CLVaR PhysicalInputs)
    flood_zone: str = "X"
    flood_depth_100yr_m: float = 0.0
    heat_days_above_35c: int = 0
    wildfire_proximity_km: float = 100.0
    coastal_proximity_km: float = 100.0
    subsidence_risk: str = "low"
    water_stress_score: float = 0.0
    sea_level_rise_cm_2050: float = 0.0
    cyclone_exposure: str = "none"
    permafrost_risk: str = "none"
    # Metadata
    data_source: str = "country_profile_v1"
    spatial_precision: str = "country"        # country | region | postcode | coordinate
    confidence_band: str = "low"              # low for Phase 1 country-level


@dataclass
class SpatialOverlapResult:
    """Result of spatial proximity check against protected areas / hazard zones."""
    property_id: str
    latitude: float
    longitude: float
    nearby_protected_areas: list[dict]
    nearby_flood_zones: list[dict]
    nearby_hazard_sites: list[dict]
    total_overlaps: int
    search_radius_km: float


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class SpatialHazardService:
    """Fetch hazard data for property locations.

    Phase 1: Country-level profile lookup with latitude modifiers.
    Phase 2: PostGIS ST_DWithin queries against hazard raster tables.
    """

    def get_hazard_profile(self, latitude: Optional[float],
                            longitude: Optional[float],
                            country: str = "") -> HazardProfile:
        """Fetch hazard profile for a location.

        Priority: coordinate-based lookup (Phase 2) > country profile > default.
        """
        # Phase 1: country profile
        base = COUNTRY_HAZARD_PROFILES.get(country.upper(), _DEFAULT_PROFILE).copy()

        profile = HazardProfile(
            latitude=latitude,
            longitude=longitude,
            country=country.upper(),
            flood_zone=base["flood_zone"],
            flood_depth_100yr_m=base["flood_depth_100yr_m"],
            heat_days_above_35c=base["heat_days_above_35c"],
            wildfire_proximity_km=base["wildfire_proximity_km"],
            coastal_proximity_km=base["coastal_proximity_km"],
            subsidence_risk=base["subsidence_risk"],
            water_stress_score=base["water_stress_score"],
            sea_level_rise_cm_2050=base["sea_level_rise_cm_2050"],
            cyclone_exposure=base.get("cyclone_exposure", "none"),
            permafrost_risk=base.get("permafrost_risk", "none"),
            data_source="country_profile_v1",
            spatial_precision="country",
            confidence_band="low",
        )

        # Apply latitude modifiers if coordinates provided
        if latitude is not None:
            mods = _latitude_modifier(latitude)
            profile.heat_days_above_35c = int(
                profile.heat_days_above_35c * mods.get("heat_days_multiplier", 1.0)
            )
            profile.wildfire_proximity_km = round(
                profile.wildfire_proximity_km / max(mods.get("wildfire_multiplier", 1.0), 0.1), 1
            )
            profile.water_stress_score = min(5.0, round(
                profile.water_stress_score + mods.get("water_stress_adder", 0.0), 1
            ))
            if latitude is not None and longitude is not None:
                coastal_est = _estimate_coastal_km(latitude, longitude, country.upper())
                if coastal_est is not None:
                    profile.coastal_proximity_km = coastal_est
                profile.spatial_precision = "coordinate_adjusted"
                profile.confidence_band = "medium"

        return profile

    def auto_populate_physical_inputs(self, latitude: Optional[float],
                                       longitude: Optional[float],
                                       country: str = "",
                                       user_overrides: Optional[dict] = None) -> dict:
        """Return dict compatible with CLVaR PhysicalInputs, with optional user overrides.

        User-provided values always take precedence over auto-populated values.
        """
        hp = self.get_hazard_profile(latitude, longitude, country)

        result = {
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
            "_meta": {
                "data_source": hp.data_source,
                "spatial_precision": hp.spatial_precision,
                "confidence_band": hp.confidence_band,
            },
        }

        # User overrides take precedence
        if user_overrides:
            for key, val in user_overrides.items():
                if key in result and val is not None:
                    result[key] = val
                    result["_meta"]["data_source"] = "user_override"

        return result

    # --- PostGIS Spatial Query Stubs (Phase 2) ---

    def query_nearby_protected_areas(self, latitude: float, longitude: float,
                                      radius_km: float = 25.0) -> list[dict]:
        """Phase 2: ST_DWithin query against dh_wdpa_protected_areas.

        SQL (when hazard raster tables available):
            SELECT wdpa_id, name, iucn_cat, desig_type,
                   ST_Distance(location::geography, ST_MakePoint(:lng, :lat)::geography) / 1000 AS distance_km
            FROM dh_wdpa_protected_areas
            WHERE ST_DWithin(location::geography, ST_MakePoint(:lng, :lat)::geography, :radius_m)
            ORDER BY distance_km;

        Currently returns empty list (no async DB session wired).
        """
        # Phase 2: wire to SQLAlchemy async session + PostGIS
        return []

    def query_flood_zone_by_location(self, latitude: float, longitude: float) -> Optional[dict]:
        """Phase 2: ST_Intersects query against dh_flood_risk_extent.

        SQL (when flood raster tables available):
            SELECT zone_type, depth_100yr_m, return_period_yr
            FROM dh_flood_risk_extent
            WHERE ST_Intersects(geom, ST_MakePoint(:lng, :lat)::geography);
        """
        return None

    def query_wildfire_proximity(self, latitude: float, longitude: float) -> Optional[float]:
        """Phase 2: Nearest-distance query to wildfire zone polygons."""
        return None

    # --- Reference Data ---

    @staticmethod
    def get_country_profiles() -> dict:
        return COUNTRY_HAZARD_PROFILES

    @staticmethod
    def get_supported_countries() -> list[str]:
        return sorted(COUNTRY_HAZARD_PROFILES.keys())

    @staticmethod
    def get_hazard_schema() -> dict:
        """Describe available hazard fields and units."""
        return {
            "flood_zone": {"type": "categorical", "values": ["1", "2", "3a", "3b", "X", "A", "AE", "V"]},
            "flood_depth_100yr_m": {"type": "numeric", "unit": "metres", "range": [0, 10]},
            "heat_days_above_35c": {"type": "integer", "unit": "days/year", "range": [0, 365]},
            "wildfire_proximity_km": {"type": "numeric", "unit": "km", "range": [0, 500]},
            "coastal_proximity_km": {"type": "numeric", "unit": "km", "range": [0, 1000]},
            "subsidence_risk": {"type": "categorical", "values": ["none", "low", "medium", "high", "very_high"]},
            "water_stress_score": {"type": "numeric", "unit": "WRI Aqueduct 0-5", "range": [0, 5]},
            "sea_level_rise_cm_2050": {"type": "numeric", "unit": "cm", "range": [0, 200]},
            "cyclone_exposure": {"type": "categorical", "values": ["none", "low", "moderate", "high"]},
            "permafrost_risk": {"type": "categorical", "values": ["none", "low", "moderate", "high"]},
        }
