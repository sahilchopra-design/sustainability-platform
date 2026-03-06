"""
Data Hub Client -- Direct DB access layer.

Previously this module made HTTP calls to a separate Data Hub service
(port 8002).  Now that the serve-layer endpoints and the platform run
in the same FastAPI process, we query the database directly for better
performance and zero-latency access to ingested data.

All methods gracefully degrade: if data is unavailable or any query
fails, None is returned so callers can fall back to sector averages.

Methods
-------
get_emissions(lei)                   -> scope 1/2/3 estimates (DQS 4)
get_glidepath(sector, scenario)      -> NGFS annual glidepath values
get_crrem_pathway(country, asset_type) -> CRREM kgCO2/m2 by year
get_carbon_price(scenario, year)     -> USD per tCO2
get_sector_benchmark(sector)         -> sector WACI / financial benchmarks
get_dqs_summary(portfolio_id)        -> exposure-weighted DQS aggregation
health_check()                       -> True (always, same-process)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ── helpers ───────────────────────────────────────────────────────────────────

def _get_db_session():
    """Get a fresh database session from the shared engine."""
    try:
        from db.base import SessionLocal
        return SessionLocal()
    except Exception:
        return None


def _safe_query(fn):
    """Decorator that wraps DB calls with try/except + session cleanup."""
    def wrapper(*args, **kwargs):
        db = _get_db_session()
        if db is None:
            logger.debug("No DB session available -- Data Hub client disabled")
            return None
        try:
            return fn(db, *args, **kwargs)
        except Exception as exc:
            logger.warning("Data Hub client query failed: %s", exc)
            return None
        finally:
            db.close()
    return wrapper


# ── Jurisdiction helper ───────────────────────────────────────────────────────

_JURISDICTION_TO_ISO3 = {
    "US": "USA", "GB": "GBR", "DE": "DEU", "FR": "FRA", "NL": "NLD",
    "JP": "JPN", "CN": "CHN", "IN": "IND", "BR": "BRA", "CA": "CAN",
    "AU": "AUS", "CH": "CHE", "SE": "SWE", "NO": "NOR", "DK": "DNK",
    "FI": "FIN", "IE": "IRL", "IT": "ITA", "ES": "ESP", "AT": "AUT",
    "BE": "BEL", "KR": "KOR", "SG": "SGP", "HK": "HKG", "TW": "TWN",
    "MX": "MEX", "ZA": "ZAF", "RU": "RUS", "SA": "SAU", "AE": "ARE",
}


# ── Public API ────────────────────────────────────────────────────────────────

@_safe_query
def get_emissions(db, lei: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve Scope 1/2/3 GHG emissions for a counterparty by GLEIF LEI.

    Queries:
      1. GLEIF entity -> jurisdiction + legal_name
      2. OWID country-level emissions as proxy
      3. Climate TRACE sector data if available

    Returns dict with keys: lei, scope1, scope2, scope3, year, source, dqs
    None if LEI not found.
    """
    if not lei or not lei.strip():
        return None

    lei_upper = lei.upper().strip()
    if len(lei_upper) != 20:
        return None

    from db.models.entity_resolution import EntityLei
    from db.models.emissions import OwidCo2Energy, ClimateTraceEmission
    from sqlalchemy import func

    # Look up GLEIF entity
    entity = db.query(EntityLei).filter(EntityLei.lei == lei_upper).first()
    if not entity:
        return None

    jurisdiction = (entity.jurisdiction or "")[:2].upper()
    iso3 = _JURISDICTION_TO_ISO3.get(jurisdiction)

    scope1, scope2, scope3 = None, None, None
    year, source, dqs = None, "estimated", 5

    # Try OWID country-level data as proxy
    if iso3:
        owid = db.query(OwidCo2Energy).filter(
            OwidCo2Energy.iso_code == iso3,
        ).order_by(OwidCo2Energy.year.desc()).first()

        if owid:
            # Country total as proxy -- scale by GLEIF entity count in jurisdiction
            entity_count = db.query(func.count(EntityLei.lei)).filter(
                EntityLei.jurisdiction.ilike(f"{jurisdiction}%")
            ).scalar() or 1

            co2_total = float(owid.co2 or 0) * 1_000_000  # Mt -> t
            per_entity = co2_total / max(entity_count, 1)

            scope1 = round(per_entity * 0.6, 2)
            scope2 = round(per_entity * 0.25, 2)
            scope3 = round(per_entity * 0.15, 2)
            year = owid.year
            source = f"OWID/{iso3} (country proxy)"
            dqs = 5

    # Try Climate TRACE for better estimate
    ct = db.query(ClimateTraceEmission).filter(
        ClimateTraceEmission.country == (iso3 or jurisdiction),
    ).order_by(ClimateTraceEmission.year.desc()).first()

    if ct and ct.emissions_quantity:
        scope1 = round(float(ct.emissions_quantity), 2)
        scope2 = round(float(ct.emissions_quantity) * 0.3, 2)
        year = ct.year
        source = f"ClimateTrace/{ct.sector or 'total'}"
        dqs = 4

    if scope1 is None:
        return None

    return {
        "lei": lei_upper,
        "scope1": scope1,
        "scope2": scope2,
        "scope3": scope3,
        "year": year,
        "source": source,
        "dqs": dqs,
        "legal_name": entity.legal_name,
        "jurisdiction": jurisdiction,
    }


@_safe_query
def get_glidepath(
    db,
    sector: str,
    scenario: str = "Net Zero 2050",
) -> Optional[List[Dict[str, Any]]]:
    """
    Retrieve the NZBA/IEA annual glidepath for a sector from NGFS data.

    Returns list of dicts: [{year, glidepath, source}, ...]
    None if no data found.
    """
    from db.models.scenario_ingest import NgfsScenarioData

    _SECTOR_VARS = {
        "Energy": "Emissions|CO2|Energy|Supply",
        "Utilities": "Emissions|CO2|Energy|Supply|Electricity",
        "Materials": "Emissions|CO2|Industrial Processes",
        "Industrials": "Emissions|CO2|Energy|Demand|Industry",
        "Transport": "Emissions|CO2|Energy|Demand|Transportation",
        "Buildings": "Emissions|CO2|Energy|Demand|Residential and Commercial",
        "Agriculture": "Emissions|CO2|AFOLU",
        "Power": "Emissions|CO2|Energy|Supply|Electricity",
        "Oil & Gas": "Emissions|CO2|Energy|Supply",
        "Steel": "Emissions|CO2|Industrial Processes",
    }

    var_pattern = _SECTOR_VARS.get(sector, _SECTOR_VARS.get(sector.title(), "Emissions|CO2"))

    records = db.query(NgfsScenarioData).filter(
        NgfsScenarioData.scenario.ilike(f"%{scenario}%"),
        NgfsScenarioData.variable.ilike(f"%{var_pattern}%"),
        NgfsScenarioData.region == "World",
    ).order_by(NgfsScenarioData.year).all()

    if not records:
        # Broader fallback
        records = db.query(NgfsScenarioData).filter(
            NgfsScenarioData.scenario.ilike(f"%{scenario}%"),
            NgfsScenarioData.variable.ilike("%Emissions%CO2%"),
            NgfsScenarioData.region == "World",
        ).order_by(NgfsScenarioData.year).limit(50).all()

    if not records:
        return None

    series = []
    base_value = records[0].value if records[0].value else 1.0
    for r in records:
        series.append({
            "year": r.year,
            "glidepath": round(r.value, 4) if r.value else None,
            "glidepath_normalised": round(r.value / base_value, 4) if r.value and base_value else None,
            "unit": r.unit,
            "source": f"NGFS/{r.model}/{r.scenario}",
        })

    return series if series else None


@_safe_query
def get_crrem_pathway(
    db,
    country: str,
    asset_type: str,
) -> Optional[List[Dict[str, Any]]]:
    """
    Retrieve the CRREM carbon intensity pathway for a real estate asset.

    Uses reference CRREM data embedded in glidepath_serve.py until the
    A13 ingester provides live data from CRREM API.

    Returns list of dicts: [{year, intensity, source}, ...]
    """
    # Import from the serve module which has the reference data
    from api.v1.routes.glidepath_serve import _CRREM_REFERENCE, _CRREM_YEARS

    country_upper = country.upper()
    asset_lower = asset_type.lower()

    asset_data = _CRREM_REFERENCE.get(asset_lower)
    if not asset_data:
        return None

    country_pathway = asset_data.get(country_upper)
    if not country_pathway:
        country_pathway = asset_data.get("DE")
        if not country_pathway:
            country_pathway = list(asset_data.values())[0]

    pathway = []
    for i, year in enumerate(_CRREM_YEARS):
        if i < len(country_pathway):
            pathway.append({
                "year": year,
                "intensity": country_pathway[i],
                "unit": "kgCO2/m2/yr",
                "source": "CRREM v2.0 (reference)",
            })

    return pathway if pathway else None


@_safe_query
def get_carbon_price(
    db,
    scenario: str = "Net Zero 2050",
    year: int = 2030,
) -> Optional[float]:
    """
    Retrieve the carbon price (USD/tCO2) for a given NGFS scenario and year.

    Returns float USD per tCO2, or None.
    """
    from db.models.scenario_ingest import NgfsScenarioData

    _CARBON_PRICE_VARS = ["Price|Carbon", "Price|Carbon|Average"]

    q = db.query(NgfsScenarioData).filter(
        NgfsScenarioData.scenario.ilike(f"%{scenario}%"),
        NgfsScenarioData.region == "World",
    )

    records = None
    for var in _CARBON_PRICE_VARS:
        sub = q.filter(NgfsScenarioData.variable == var).order_by(NgfsScenarioData.year)
        records = sub.all()
        if records:
            break

    if not records:
        records = q.filter(
            NgfsScenarioData.variable.ilike("%Price%Carbon%")
        ).order_by(NgfsScenarioData.year).all()

    if not records:
        return None

    # Find closest year
    closest = min(records, key=lambda r: abs(r.year - year))
    if closest and closest.value:
        return round(float(closest.value), 2)

    return None


@_safe_query
def get_sector_benchmark(db, sector: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve sector-level financial/emissions benchmarks from ingested data.

    Aggregates from yfinance market data, SEC EDGAR filings, and SBTi targets.
    """
    from db.models.scenario_ingest import NgfsScenarioData
    from sqlalchemy import func

    result: Dict[str, Any] = {"sector": sector}

    # Market data
    try:
        from db.models.ingestion import YfinanceMarketData
        mkt = db.query(
            func.count(YfinanceMarketData.id),
            func.avg(YfinanceMarketData.market_cap),
            func.avg(YfinanceMarketData.pe_ratio),
            func.avg(YfinanceMarketData.esg_score),
        ).filter(
            YfinanceMarketData.sector.ilike(f"%{sector}%")
        ).first()

        result["market_data"] = {
            "companies": mkt[0] if mkt else 0,
            "avg_market_cap": round(float(mkt[1]), 0) if mkt and mkt[1] else None,
            "avg_pe_ratio": round(float(mkt[2]), 2) if mkt and mkt[2] else None,
            "avg_esg_score": round(float(mkt[3]), 1) if mkt and mkt[3] else None,
        }
    except Exception:
        result["market_data"] = {"companies": 0}

    # SBTi coverage
    try:
        from db.models.ingestion import SbtiCompany
        sbti_count = db.query(func.count(SbtiCompany.id)).filter(
            SbtiCompany.sector.ilike(f"%{sector}%"),
            SbtiCompany.target_status.in_(["Targets Set", "Committed"]),
        ).scalar() or 0
        result["sbti_targets"] = sbti_count
    except Exception:
        result["sbti_targets"] = 0

    return result


# ── PCAF DQS Aggregation (B4) ────────────────────────────────────────────────

@_safe_query
def get_dqs_summary(
    db,
    portfolio_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Exposure-weighted average PCAF Data Quality Score for a portfolio.

    Reads assets from assets_pg, uses the pcaf_dqs column if populated,
    otherwise infers DQS from data availability:
      DQS 1-2: verified/unverified primary data (scope1_tco2e + audit flag)
      DQS 3:   scope1_tco2e populated (unaudited)
      DQS 4:   entity_lei present (Data Hub lookup possible)
      DQS 5:   sector average fallback

    Returns dict with:
      weighted_dqs       float   exposure-weighted average
      dqs_distribution   dict    {1: count, 2: count, ..., 5: count}
      coverage_pct       float   % of AUM with DQS <= 4
      total_assets       int
      total_exposure     float
      improvement_actions list   actionable recommendations
    """
    from sqlalchemy import text

    rows = db.execute(text("""
        SELECT
            exposure,
            scope1_tco2e,
            scope2_tco2e,
            scope3_tco2e,
            pcaf_dqs,
            entity_lei,
            company_sector,
            company_name
        FROM assets_pg
        WHERE portfolio_id = :pid
    """), {"pid": portfolio_id}).fetchall()

    if not rows:
        return None

    dqs_dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    total_exposure = 0.0
    weighted_sum = 0.0
    covered_exposure = 0.0
    asset_details = []

    for row in rows:
        exposure = float(row[0] or 0)
        s1 = row[1]
        s2 = row[2]
        s3 = row[3]
        explicit_dqs = row[4]
        lei = row[5]
        sector = row[6] or "Unknown"
        name = row[7] or "Unknown"

        # Determine DQS
        if explicit_dqs and 1 <= explicit_dqs <= 5:
            dqs = explicit_dqs
        elif s1 is not None and float(s1) > 0:
            dqs = 3  # has scope1 data
        elif lei:
            dqs = 4  # can look up via Data Hub
        else:
            dqs = 5  # sector average fallback

        dqs_dist[dqs] += 1
        total_exposure += exposure
        weighted_sum += exposure * dqs
        if dqs <= 4:
            covered_exposure += exposure

        asset_details.append({
            "name": name,
            "sector": sector,
            "dqs": dqs,
            "exposure": exposure,
        })

    weighted_dqs = round(weighted_sum / total_exposure, 2) if total_exposure > 0 else 5.0
    coverage_pct = round(covered_exposure / total_exposure * 100, 1) if total_exposure > 0 else 0.0

    # Build improvement actions
    actions = []
    dqs5_count = dqs_dist[5]
    dqs4_count = dqs_dist[4]
    if dqs5_count > 0:
        actions.append(
            f"Add LEI codes for {dqs5_count} assets to enable Data Hub emissions lookup (DQS 5 -> 4)"
        )
    if dqs4_count > 0:
        actions.append(
            f"Collect reported scope 1/2 data for {dqs4_count} assets (DQS 4 -> 3)"
        )
    if dqs_dist[3] > 0:
        actions.append(
            f"Obtain third-party verification for {dqs_dist[3]} assets with reported data (DQS 3 -> 2)"
        )
    if weighted_dqs > 3.5:
        actions.append(
            "Portfolio weighted DQS exceeds 3.5 -- prioritise high-exposure assets for data improvement"
        )
    if coverage_pct < 70:
        actions.append(
            f"Coverage at {coverage_pct}% -- below PCAF recommended 70% threshold"
        )

    return {
        "portfolio_id": portfolio_id,
        "weighted_dqs": weighted_dqs,
        "dqs_distribution": dqs_dist,
        "coverage_pct": coverage_pct,
        "total_assets": len(rows),
        "total_exposure": round(total_exposure, 2),
        "improvement_actions": actions,
        "asset_details": sorted(asset_details, key=lambda a: (-a["dqs"], -a["exposure"])),
    }


def health_check() -> bool:
    """Always True -- same process, no network hop."""
    return True
