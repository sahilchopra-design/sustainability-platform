"""
PCAF Time-Series Engine — Glidepath tracking, RAG status, and alert generation.

Reads from:  pcaf_time_series table (populated by portfolio_analytics_engine)
Enriches from: Data Hub /glidepaths/nze/{sector} and /glidepaths/crrem/{country}/{asset_type}

RAG logic:
  deviation = (actual - glidepath) / glidepath   (positive = above = worse)
  GREEN  : deviation <=  0%
  AMBER  : deviation <= 10%
  RED    : deviation >  10%
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────
# NZBA / IEA NZE reference glidepaths (fallback if Data Hub offline)
# Sector WACI tCO2e / MEUR revenue — indexed by reporting year
# Source: NZBA 2021 Guidelines, IEA World Energy Outlook 2023
# ─────────────────────────────────────────────────────────
NZBA_FALLBACK_GLIDEPATHS: Dict[str, Dict[int, float]] = {
    "Power": {2020: 220, 2025: 160, 2030: 80, 2035: 30, 2040: 10, 2045: 5, 2050: 0},
    "Oil & Gas": {2020: 680, 2025: 580, 2030: 460, 2035: 320, 2040: 200, 2045: 100, 2050: 0},
    "Steel": {2020: 1850, 2025: 1600, 2030: 1200, 2035: 800, 2040: 400, 2045: 150, 2050: 0},
    "Shipping": {2020: 1120, 2025: 950, 2030: 750, 2035: 500, 2040: 300, 2045: 100, 2050: 0},
    "Real Estate": {2020: 55, 2025: 45, 2030: 32, 2035: 20, 2040: 12, 2045: 5, 2050: 0},
    "Aviation": {2020: 850, 2025: 750, 2030: 600, 2035: 420, 2040: 250, 2045: 100, 2050: 0},
    "Cement": {2020: 620, 2025: 540, 2030: 400, 2035: 260, 2040: 140, 2045: 50, 2050: 0},
    "Aluminium": {2020: 1100, 2025: 900, 2030: 650, 2035: 400, 2040: 200, 2045: 80, 2050: 0},
    "Other": {2020: 300, 2025: 250, 2030: 190, 2035: 130, 2040: 80, 2045: 30, 2050: 0},
}

# CRREM reference kgCO2/m2 — European office (fallback)
CRREM_FALLBACK: Dict[str, Dict[int, float]] = {
    "Office": {2020: 45, 2025: 35, 2030: 25, 2035: 16, 2040: 9, 2045: 4, 2050: 1.5},
    "Retail": {2020: 55, 2025: 42, 2030: 30, 2035: 20, 2040: 11, 2045: 5, 2050: 2.0},
    "Residential": {2020: 40, 2025: 30, 2030: 20, 2035: 12, 2040: 6, 2045: 2, 2050: 0.5},
    "Industrial": {2020: 60, 2025: 48, 2030: 34, 2035: 22, 2040: 12, 2045: 5, 2050: 1.8},
    "Hotel": {2020: 65, 2025: 50, 2030: 36, 2035: 24, 2040: 14, 2045: 6, 2050: 2.5},
}


# ─────────────────────────────────────────────────────────
# Output Dataclasses
# ─────────────────────────────────────────────────────────
@dataclass
class GlidepathDataPoint:
    year: int
    actual_waci: Optional[float]
    nzba_target: Optional[float]
    iea_nze_reference: Optional[float]
    rag_status: str  # GREEN | AMBER | RED | GREY (no target)
    deviation_pct: Optional[float]


@dataclass
class SectorGlidepathResult:
    sector: str
    portfolio_id: str
    data_points: List[GlidepathDataPoint] = field(default_factory=list)
    current_rag: str = "GREY"
    years_to_stranding: Optional[int] = None   # for real estate
    glidepath_source: str = "fallback"          # 'data_hub' | 'fallback' | 'none'
    data_available: bool = True
    error_message: Optional[str] = None


@dataclass
class CRREMAssetResult:
    asset_id: str
    asset_name: str
    asset_type: str
    country: str
    data_points: List[GlidepathDataPoint] = field(default_factory=list)
    stranding_year: Optional[int] = None
    current_intensity_kgco2_m2: Optional[float] = None
    crrem_pathway_source: str = "fallback"
    data_available: bool = True


@dataclass
class GlidepathStatusRow:
    sector: str
    year: int
    actual: Optional[float]
    target: Optional[float]
    rag: str


# ─────────────────────────────────────────────────────────
# RAG helper
# ─────────────────────────────────────────────────────────
def compute_rag(actual: float, target: float) -> tuple[str, float]:
    """Returns (rag_status, deviation_pct)."""
    if target == 0:
        return "GREY", 0.0
    deviation = (actual - target) / target  # positive = above = worse
    if deviation <= 0:
        return "GREEN", round(deviation * 100, 1)
    elif deviation <= 0.10:
        return "AMBER", round(deviation * 100, 1)
    else:
        return "RED", round(deviation * 100, 1)


def interpolate_glidepath(glidepath: Dict[int, float], year: int) -> Optional[float]:
    """Linear interpolation between known glidepath years."""
    years = sorted(glidepath.keys())
    if year <= years[0]:
        return glidepath[years[0]]
    if year >= years[-1]:
        return glidepath[years[-1]]
    for i in range(len(years) - 1):
        y1, y2 = years[i], years[i + 1]
        if y1 <= year <= y2:
            frac = (year - y1) / (y2 - y1)
            return glidepath[y1] + frac * (glidepath[y2] - glidepath[y1])
    return None


# ─────────────────────────────────────────────────────────
# Engine
# ─────────────────────────────────────────────────────────
class PCAFTimeSeriesEngine:
    """
    Reads pcaf_time_series data and computes glidepath deviation per sector.
    Falls back to hardcoded NZBA/CRREM benchmarks if Data Hub is offline.
    """

    def get_sector_glidepath(
        self,
        portfolio_id: str,
        sector: str,
        time_series_rows: List[Dict[str, Any]],
        data_hub_glidepath: Optional[Dict[int, float]] = None,
    ) -> SectorGlidepathResult:
        try:
            glidepath = data_hub_glidepath or NZBA_FALLBACK_GLIDEPATHS.get(sector, NZBA_FALLBACK_GLIDEPATHS["Other"])
            source = "data_hub" if data_hub_glidepath else "fallback"

            # Actual WACI by year from time series
            actual_by_year: Dict[int, float] = {}
            for row in time_series_rows:
                if row.get("metric_type") == "waci" and row.get("sector") == sector:
                    yr = row.get("reporting_year")
                    val = row.get("actual_value")
                    if yr and val is not None:
                        actual_by_year[yr] = float(val)

            # Build data points spanning 2020–2050
            data_points = []
            years = sorted(set(list(range(2020, 2051, 5)) + list(actual_by_year.keys())))
            for yr in years:
                actual = actual_by_year.get(yr)
                target = interpolate_glidepath(glidepath, yr)
                # IEA NZE ≈ NZBA * 0.90 (slightly more ambitious)
                iea_nze = target * 0.90 if target is not None else None

                if actual is not None and target is not None:
                    rag, dev = compute_rag(actual, target)
                else:
                    rag, dev = "GREY", 0.0

                data_points.append(GlidepathDataPoint(
                    year=yr,
                    actual_waci=actual,
                    nzba_target=target,
                    iea_nze_reference=iea_nze,
                    rag_status=rag,
                    deviation_pct=dev if actual else None,
                ))

            # Current RAG = most recent year with actual data
            current_rag = "GREY"
            for dp in reversed(data_points):
                if dp.actual_waci is not None:
                    current_rag = dp.rag_status
                    break

            return SectorGlidepathResult(
                sector=sector,
                portfolio_id=portfolio_id,
                data_points=data_points,
                current_rag=current_rag,
                glidepath_source=source,
                data_available=True,
            )
        except Exception as e:
            logger.exception("Glidepath computation failed for sector %s: %s", sector, e)
            return SectorGlidepathResult(
                sector=sector,
                portfolio_id=portfolio_id,
                data_available=False,
                error_message=str(e),
            )

    def get_crrem_asset(
        self,
        asset_id: str,
        asset_name: str,
        asset_type: str,
        country: str,
        actual_by_year: Dict[int, float],
        crrem_pathway: Optional[Dict[int, float]] = None,
    ) -> CRREMAssetResult:
        """Compute CRREM pathway comparison for a single real estate asset."""
        try:
            pathway = crrem_pathway or CRREM_FALLBACK.get(asset_type, CRREM_FALLBACK["Office"])
            source = "data_hub" if crrem_pathway else "fallback"

            data_points = []
            years = sorted(set(list(range(2020, 2051, 5)) + list(actual_by_year.keys())))
            stranding_year = None

            for yr in years:
                actual = actual_by_year.get(yr)
                target = interpolate_glidepath(pathway, yr)

                if actual is not None and target is not None:
                    rag, dev = compute_rag(actual, target)
                    # Stranding: first year actual persistently exceeds pathway
                    if rag == "RED" and stranding_year is None:
                        stranding_year = yr
                    elif rag in ("GREEN", "AMBER"):
                        stranding_year = None  # reset
                else:
                    rag, dev = "GREY", 0.0

                data_points.append(GlidepathDataPoint(
                    year=yr,
                    actual_waci=actual,
                    nzba_target=target,
                    iea_nze_reference=None,
                    rag_status=rag,
                    deviation_pct=dev if actual else None,
                ))

            current_intensity = actual_by_year.get(max(actual_by_year.keys())) if actual_by_year else None

            return CRREMAssetResult(
                asset_id=asset_id,
                asset_name=asset_name,
                asset_type=asset_type,
                country=country,
                data_points=data_points,
                stranding_year=stranding_year,
                current_intensity_kgco2_m2=current_intensity,
                crrem_pathway_source=source,
                data_available=True,
            )
        except Exception as e:
            logger.exception("CRREM asset computation failed: %s", e)
            return CRREMAssetResult(
                asset_id=asset_id, asset_name=asset_name, asset_type=asset_type,
                country=country, data_available=False,
            )

    def build_status_grid(
        self,
        portfolio_id: str,
        sectors: List[str],
        time_series_rows: List[Dict[str, Any]],
    ) -> List[GlidepathStatusRow]:
        """Build sector × year RAG status grid for the tracker table."""
        grid = []
        target_years = [2025, 2030, 2035, 2040, 2045, 2050]

        for sector in sectors:
            glidepath = NZBA_FALLBACK_GLIDEPATHS.get(sector, NZBA_FALLBACK_GLIDEPATHS["Other"])
            actual_by_year: Dict[int, float] = {}
            for row in time_series_rows:
                if row.get("metric_type") == "waci" and row.get("sector") == sector:
                    yr = row.get("reporting_year")
                    if yr:
                        actual_by_year[yr] = float(row.get("actual_value") or 0)

            for yr in target_years:
                actual = actual_by_year.get(yr)
                target = interpolate_glidepath(glidepath, yr)
                if actual and target:
                    rag, _ = compute_rag(actual, target)
                else:
                    rag = "GREY"
                grid.append(GlidepathStatusRow(sector=sector, year=yr, actual=actual, target=target, rag=rag))

        return grid

    def get_available_sectors(self) -> List[str]:
        return list(NZBA_FALLBACK_GLIDEPATHS.keys())


# Module-level singleton
pcaf_time_series_engine = PCAFTimeSeriesEngine()
