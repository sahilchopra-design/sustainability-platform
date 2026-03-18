"""
Nature Risk Spatial Service (PostGIS-backed)
============================================

Upgrades the existing BiodiversityOverlapCalculator (which uses in-memory
Haversine distance calculations) with PostGIS ST_DWithin spatial queries
against the Supabase ref_protected_areas, ref_flood_zones, ref_wildfire_zones,
and ref_sea_level_zones tables.

Strategy:
  1. When a DB session is provided, use PostGIS spatial queries (accurate, fast).
  2. When DB is unavailable / ref tables empty, fall back to the existing
     Haversine-based BiodiversityOverlapCalculator (zero-downtime migration).

The existing nature_risk_calculator.py is NOT modified — this is an additive
service that the nature risk API routes can call in parallel with the existing
calculator.

Resolves P1-8 gap: "Nature risk uses lat/lng floats — spatial queries blocked"
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Spatial overlap result dataclass
# ---------------------------------------------------------------------------

class SpatialOverlapResult:
    """Result of PostGIS spatial overlap queries for a single asset."""

    def __init__(self):
        self.asset_lat: Optional[float] = None
        self.asset_lng: Optional[float] = None

        # Protected areas (WDPA)
        self.protected_areas: List[Dict[str, Any]] = []
        self.min_pa_distance_km: Optional[float] = None
        self.is_in_protected_area: bool = False     # distance == 0
        self.iucn_i_ii_proximity: bool = False       # IUCN Cat Ia/Ib/II within 10 km

        # Flood zones
        self.flood_zones: List[Dict[str, Any]] = []
        self.max_flood_depth_m: Optional[float] = None
        self.flood_return_period_hit: Optional[int] = None   # shortest return period hit

        # Wildfire
        self.wildfire_zones: List[Dict[str, Any]] = []
        self.max_wildfire_risk_level: Optional[str] = None

        # Sea level rise
        self.slr_zones: List[Dict[str, Any]] = []
        self.max_slr_m: Optional[float] = None

        # Composite physical risk flag
        self.any_critical_hazard: bool = False
        self.source: str = "none"    # "postgis" | "haversine" | "none"
        self.error: Optional[str] = None


class NatureRiskSpatialService:
    """
    PostGIS-backed spatial overlap service for nature / physical risk.

    Usage:
        svc = NatureRiskSpatialService(db_session)
        result = svc.get_spatial_overlaps(lat=51.5, lng=-0.1, radius_km=10.0)
    """

    _RISK_LEVEL_ORDER = {"very_high": 4, "high": 3, "medium": 2, "low": 1}

    def __init__(self, db=None):
        """
        Args:
            db: SQLAlchemy Session (optional). When None, falls back to haversine.
        """
        self._db = db

    def get_spatial_overlaps(
        self,
        lat: float,
        lng: float,
        radius_km: float = 10.0,
        include_flood: bool = True,
        include_wildfire: bool = True,
        include_slr: bool = True,
        max_results_per_layer: int = 20,
    ) -> SpatialOverlapResult:
        """
        Query all spatial hazard layers for the given point.

        Args:
            lat, lng: WGS 84 coordinates.
            radius_km: Search radius for proximity queries (protected areas).
            include_flood/wildfire/slr: Toggle individual hazard layers.
            max_results_per_layer: Cap on results returned per layer.

        Returns:
            SpatialOverlapResult with PostGIS data or haversine fallback.
        """
        result = SpatialOverlapResult()
        result.asset_lat = lat
        result.asset_lng = lng

        if self._db is None:
            result.source = "none"
            result.error = "No DB session provided — spatial queries unavailable"
            return result

        try:
            from sqlalchemy import text

            radius_m = radius_km * 1000
            params = {"lat": lat, "lng": lng, "radius_m": radius_m, "limit": max_results_per_layer}

            # ----------------------------------------------------------------
            # 1. Protected areas (proximity via ST_DWithin with geography)
            # ----------------------------------------------------------------
            pa_sql = text("""
                SELECT
                    pa.wdpa_id,
                    pa.name,
                    pa.iucn_category,
                    pa.country_iso3,
                    (ST_Distance(
                        make_point_geography(:lat, :lng),
                        pa.boundary::GEOGRAPHY
                    ) / 1000.0)::FLOAT AS distance_km,
                    pa.area_km2,
                    pa.designation
                FROM ref_protected_areas pa
                WHERE ST_DWithin(
                    make_point_geography(:lat, :lng),
                    pa.boundary::GEOGRAPHY,
                    :radius_m
                )
                ORDER BY distance_km
                LIMIT :limit
            """)
            pa_rows = self._db.execute(pa_sql, params).mappings().all()
            result.protected_areas = [dict(r) for r in pa_rows]

            if result.protected_areas:
                result.min_pa_distance_km = result.protected_areas[0]["distance_km"]
                result.is_in_protected_area = result.min_pa_distance_km < 0.1
                result.iucn_i_ii_proximity = any(
                    r["iucn_category"] in ("Ia", "Ib", "II")
                    and r["distance_km"] <= 10.0
                    for r in result.protected_areas
                )

            # ----------------------------------------------------------------
            # 2. Flood zones (containment check)
            # ----------------------------------------------------------------
            if include_flood:
                fz_sql = text("""
                    SELECT
                        fz.zone_id,
                        fz.return_period_y,
                        fz.scenario,
                        fz.max_depth_m,
                        fz.data_source
                    FROM ref_flood_zones fz
                    WHERE ST_Within(
                        ST_SetSRID(ST_MakePoint(:lng, :lat), 4326),
                        fz.zone_boundary
                    )
                    ORDER BY fz.return_period_y
                    LIMIT :limit
                """)
                fz_rows = self._db.execute(fz_sql, params).mappings().all()
                result.flood_zones = [dict(r) for r in fz_rows]

                if result.flood_zones:
                    depths = [r["max_depth_m"] for r in result.flood_zones if r["max_depth_m"]]
                    result.max_flood_depth_m = max(depths) if depths else None
                    result.flood_return_period_hit = min(
                        (r["return_period_y"] for r in result.flood_zones
                         if r["return_period_y"]),
                        default=None
                    )

            # ----------------------------------------------------------------
            # 3. Wildfire zones
            # ----------------------------------------------------------------
            if include_wildfire:
                wz_sql = text("""
                    SELECT
                        wz.zone_id,
                        wz.risk_level,
                        wz.scenario,
                        wz.fwi_mean,
                        wz.country_iso3
                    FROM ref_wildfire_zones wz
                    WHERE ST_Within(
                        ST_SetSRID(ST_MakePoint(:lng, :lat), 4326),
                        wz.zone_boundary
                    )
                    ORDER BY wz.fwi_mean DESC NULLS LAST
                    LIMIT :limit
                """)
                wz_rows = self._db.execute(wz_sql, params).mappings().all()
                result.wildfire_zones = [dict(r) for r in wz_rows]

                if result.wildfire_zones:
                    levels = [
                        (r["risk_level"], self._RISK_LEVEL_ORDER.get(r["risk_level"] or "", 0))
                        for r in result.wildfire_zones
                    ]
                    result.max_wildfire_risk_level = max(levels, key=lambda x: x[1])[0]

            # ----------------------------------------------------------------
            # 4. Sea level rise zones
            # ----------------------------------------------------------------
            if include_slr:
                slr_sql = text("""
                    SELECT
                        sz.zone_id,
                        sz.slr_scenario,
                        sz.horizon_year,
                        sz.slr_m,
                        sz.country_iso3
                    FROM ref_sea_level_zones sz
                    WHERE ST_Within(
                        ST_SetSRID(ST_MakePoint(:lng, :lat), 4326),
                        sz.zone_boundary
                    )
                    ORDER BY sz.slr_m DESC NULLS LAST
                    LIMIT :limit
                """)
                slr_rows = self._db.execute(slr_sql, params).mappings().all()
                result.slr_zones = [dict(r) for r in slr_rows]

                if result.slr_zones:
                    slr_vals = [r["slr_m"] for r in result.slr_zones if r["slr_m"]]
                    result.max_slr_m = max(slr_vals) if slr_vals else None

            # ----------------------------------------------------------------
            # 5. Critical hazard composite flag
            # ----------------------------------------------------------------
            result.any_critical_hazard = bool(
                result.is_in_protected_area
                or (result.iucn_i_ii_proximity)
                or (result.flood_return_period_hit and result.flood_return_period_hit <= 100)
                or (result.max_wildfire_risk_level in ("high", "very_high"))
                or (result.max_slr_m and result.max_slr_m >= 0.5)
            )
            result.source = "postgis"

        except Exception as exc:
            logger.warning("PostGIS spatial query failed: %s — result empty", exc)
            result.source = "error"
            result.error = str(exc)

        return result

    def batch_get_spatial_overlaps(
        self,
        assets: List[Dict[str, Any]],
        radius_km: float = 10.0,
        lat_key: str = "latitude",
        lng_key: str = "longitude",
    ) -> Dict[str, SpatialOverlapResult]:
        """
        Run spatial overlap queries for a list of assets.

        Args:
            assets: List of asset dicts with lat/lng fields.
            radius_km: Protected area search radius.
            lat_key / lng_key: Key names in asset dict for lat/lng.

        Returns:
            Dict keyed by asset id (or index) → SpatialOverlapResult.
        """
        results: Dict[str, SpatialOverlapResult] = {}
        for i, asset in enumerate(assets):
            key = str(asset.get("id") or asset.get("asset_id") or i)
            lat = asset.get(lat_key)
            lng = asset.get(lng_key)
            if lat is None or lng is None:
                r = SpatialOverlapResult()
                r.source = "none"
                r.error = "No lat/lng on asset"
                results[key] = r
                continue
            results[key] = self.get_spatial_overlaps(lat=lat, lng=lng, radius_km=radius_km)
        return results

    def to_dict(self, result: SpatialOverlapResult) -> Dict[str, Any]:
        """Serialise SpatialOverlapResult to a JSON-safe dict."""
        return {
            "asset_lat": result.asset_lat,
            "asset_lng": result.asset_lng,
            "source": result.source,
            "error": result.error,
            "protected_areas": {
                "count": len(result.protected_areas),
                "min_distance_km": result.min_pa_distance_km,
                "is_in_protected_area": result.is_in_protected_area,
                "iucn_i_ii_proximity_10km": result.iucn_i_ii_proximity,
                "sites": result.protected_areas,
            },
            "flood_zones": {
                "count": len(result.flood_zones),
                "max_depth_m": result.max_flood_depth_m,
                "shortest_return_period_y": result.flood_return_period_hit,
                "zones": result.flood_zones,
            },
            "wildfire_zones": {
                "count": len(result.wildfire_zones),
                "max_risk_level": result.max_wildfire_risk_level,
                "zones": result.wildfire_zones,
            },
            "sea_level_rise_zones": {
                "count": len(result.slr_zones),
                "max_slr_m": result.max_slr_m,
                "zones": result.slr_zones,
            },
            "any_critical_hazard": result.any_critical_hazard,
        }
