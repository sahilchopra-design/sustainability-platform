"""
Data Hub Client — Sustainability Pulse Platform

Single HTTP client module for all outbound calls to the A2 Data Hub
(Category A service, port 8002).

All methods gracefully degrade: if the Data Hub is offline, None is
returned with a warning log so callers can fall back to sector averages
or show a "Data Hub unavailable" notice in the UI.

Methods
-------
get_emissions(lei)             → scope 1/2/3 estimates (DQS 4)
get_glidepath(sector, scenario) → NGFS annual glidepath values
get_crrem_pathway(country, asset_type) → CRREM kgCO₂/m² by year
get_carbon_price(scenario, year) → USD per tCO₂ for ETC revenue modelling

Environment
-----------
DATA_HUB_URL  — base URL (default: http://localhost:8002)
DATA_HUB_TIMEOUT_SEC — request timeout in seconds (default: 5)
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────────────────

_BASE_URL = os.environ.get("DATA_HUB_URL", "http://localhost:8002").rstrip("/")
_TIMEOUT  = float(os.environ.get("DATA_HUB_TIMEOUT_SEC", "5"))

_OFFLINE_WARNING_INTERVAL = 300   # seconds between repeated "offline" log lines
_last_offline_log: float = 0.0


def _get_session():
    """Lazy import of requests to avoid hard dependency at module load."""
    try:
        import requests
        return requests
    except ImportError:
        return None


def _get(path: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict]:
    """
    Internal GET helper.  Returns parsed JSON dict on success, None on any failure.
    Logs a warning at most once per _OFFLINE_WARNING_INTERVAL seconds to avoid
    flooding the log when the Data Hub is persistently unavailable.
    """
    import time
    global _last_offline_log

    requests = _get_session()
    if requests is None:
        logger.debug("requests library not available — Data Hub calls disabled")
        return None

    url = f"{_BASE_URL}{path}"
    try:
        resp = requests.get(url, params=params or {}, timeout=_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        now = time.time()
        if now - _last_offline_log > _OFFLINE_WARNING_INTERVAL:
            logger.warning(
                "Data Hub unavailable (%s %s): %s — falling back to sector averages",
                "GET", url, exc,
            )
            _last_offline_log = now
        return None


# ── Public API ─────────────────────────────────────────────────────────────────

def get_emissions(lei: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve Scope 1/2/3 GHG emissions for a counterparty by GLEIF LEI.

    Returns
    -------
    dict with keys:
        lei        str
        scope1     float   tCO₂e
        scope2     float   tCO₂e (market-based)
        scope3     float   tCO₂e (reported categories)
        year       int     reporting year
        source     str     e.g. "CDP", "SFDR_PAI", "estimated"
        dqs        int     PCAF DQS 1-5
    None if Data Hub unavailable or LEI not found.
    """
    if not lei or not lei.strip():
        return None
    data = _get(f"/api/v1/emissions/by-lei/{lei.upper()}")
    if data and isinstance(data, dict) and data.get("scope1") is not None:
        return data
    return None


def get_glidepath(
    sector: str,
    scenario: str = "NZE2050",
) -> Optional[List[Dict[str, Any]]]:
    """
    Retrieve the NZBA/IEA annual glidepath for a sector.

    Parameters
    ----------
    sector   GICS sector string, e.g. "Energy", "Materials", "Utilities"
    scenario NGFS scenario key, e.g. "NZE2050", "APS", "STEPS"

    Returns
    -------
    list of dicts with keys:
        year         int
        glidepath    float   tCO₂e / EUR M revenue (WACI target)
        source       str
    None if Data Hub unavailable.
    """
    data = _get(
        f"/api/v1/glidepaths/nze/{sector}",
        params={"scenario": scenario},
    )
    if data and isinstance(data, dict):
        return data.get("glidepath_series") or []
    return None


def get_crrem_pathway(
    country: str,
    asset_type: str,
) -> Optional[List[Dict[str, Any]]]:
    """
    Retrieve the CRREM carbon intensity pathway for a real estate asset.

    Parameters
    ----------
    country    ISO 3166-1 alpha-2 country code, e.g. "DE", "GB", "SG"
    asset_type CRREM asset type, e.g. "office", "retail", "residential"

    Returns
    -------
    list of dicts with keys:
        year       int
        intensity  float   kgCO₂/m² per year
        source     str
    None if Data Hub unavailable.
    """
    data = _get(
        f"/api/v1/glidepaths/crrem/{country}/{asset_type}",
    )
    if data and isinstance(data, dict):
        return data.get("pathway_series") or []
    return None


def get_carbon_price(
    scenario: str = "NZE2050",
    year: int = 2030,
) -> Optional[float]:
    """
    Retrieve the carbon price (USD/tCO₂) for a given NGFS scenario and year.
    Used for ETC revenue modelling in project finance.

    Returns
    -------
    float   USD per tCO₂
    None if Data Hub unavailable.
    """
    data = _get(
        f"/api/v1/carbon-prices/{scenario}",
        params={"year": year},
    )
    if data and isinstance(data, dict) and data.get("price_usd") is not None:
        return float(data["price_usd"])
    return None


def get_sector_benchmark(sector: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve sector-level anonymised WACI benchmark from the platform flywheel.
    Returns percentile distributions from pcaf_time_series aggregates.
    """
    data = _get(f"/api/v1/benchmarks/sector/{sector}")
    if data and isinstance(data, dict):
        return data
    return None


def health_check() -> bool:
    """Ping the Data Hub. Returns True if reachable."""
    data = _get("/health")
    return data is not None
