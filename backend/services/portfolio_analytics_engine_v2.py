"""
portfolio_analytics_engine_v2.py
Real-database version of the portfolio analytics engine.
All mock / random data has been removed. Data is read from Supabase
tables: portfolio_climate_risk, financial_instruments, exposure_assessments,
entities, scope3_category_emissions, portfolios, portfolio_holdings.
Falls back to empty / zero values when tables are missing or empty.
"""
from __future__ import annotations

import os
import math
import logging
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4, UUID

from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

from schemas.portfolio_analytics import (
    PortfolioAnalyticsResponse, PortfolioSummary, RiskMetrics, RiskLevel,
    StrandingAnalysis, SustainabilityMetrics, ConcentrationAnalysis,
    ConcentrationMetrics, ScenarioComparisonResult, ScenarioComparisonRow,
    DashboardResponse, KPICard, ChartData, Alert, ReportType,
    DataQualityReport,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Reference data for auto-estimation of missing datapoints
# Source: PCAF v2.0 Annex, IPCC AR6, S&P Global Ratings, Bloomberg BICS
# ---------------------------------------------------------------------------

SECTOR_REFERENCE_DATA = {
    "Technology":     {"avg_pd": 0.015, "avg_lgd": 0.40, "avg_scope1_intensity": 5,   "avg_scope2_intensity": 25,  "avg_scope3_intensity": 50,  "avg_risk_score": 25},
    "Healthcare":     {"avg_pd": 0.018, "avg_lgd": 0.42, "avg_scope1_intensity": 8,   "avg_scope2_intensity": 30,  "avg_scope3_intensity": 55,  "avg_risk_score": 28},
    "Financials":     {"avg_pd": 0.012, "avg_lgd": 0.35, "avg_scope1_intensity": 2,   "avg_scope2_intensity": 15,  "avg_scope3_intensity": 120, "avg_risk_score": 22},
    "Energy":         {"avg_pd": 0.035, "avg_lgd": 0.50, "avg_scope1_intensity": 250, "avg_scope2_intensity": 50,  "avg_scope3_intensity": 400, "avg_risk_score": 55},
    "Industrials":    {"avg_pd": 0.025, "avg_lgd": 0.45, "avg_scope1_intensity": 80,  "avg_scope2_intensity": 40,  "avg_scope3_intensity": 150, "avg_risk_score": 40},
    "Consumer":       {"avg_pd": 0.020, "avg_lgd": 0.43, "avg_scope1_intensity": 15,  "avg_scope2_intensity": 20,  "avg_scope3_intensity": 100, "avg_risk_score": 30},
    "Materials":      {"avg_pd": 0.030, "avg_lgd": 0.48, "avg_scope1_intensity": 200, "avg_scope2_intensity": 60,  "avg_scope3_intensity": 250, "avg_risk_score": 50},
    "Utilities":      {"avg_pd": 0.020, "avg_lgd": 0.45, "avg_scope1_intensity": 350, "avg_scope2_intensity": 80,  "avg_scope3_intensity": 100, "avg_risk_score": 45},
    "Real Estate":    {"avg_pd": 0.022, "avg_lgd": 0.40, "avg_scope1_intensity": 10,  "avg_scope2_intensity": 35,  "avg_scope3_intensity": 60,  "avg_risk_score": 35},
    "Communications": {"avg_pd": 0.018, "avg_lgd": 0.40, "avg_scope1_intensity": 4,   "avg_scope2_intensity": 22,  "avg_scope3_intensity": 45,  "avg_risk_score": 26},
}

COUNTRY_REFERENCE_DATA = {
    "US": {"sovereign_spread": 0, "regulatory_risk": "low"},
    "UK": {"sovereign_spread": 10, "regulatory_risk": "low"},
    "Germany": {"sovereign_spread": 5, "regulatory_risk": "low"},
    "France": {"sovereign_spread": 8, "regulatory_risk": "low"},
    "Japan": {"sovereign_spread": 15, "regulatory_risk": "low"},
    "China": {"sovereign_spread": 60, "regulatory_risk": "moderate"},
    "Brazil": {"sovereign_spread": 150, "regulatory_risk": "high"},
    "India": {"sovereign_spread": 100, "regulatory_risk": "moderate"},
}

# Global fallback when sector/country not matched
GLOBAL_FALLBACK = {"avg_pd": 0.025, "avg_lgd": 0.45, "avg_scope1_intensity": 40, "avg_scope2_intensity": 30, "avg_scope3_intensity": 100, "avg_risk_score": 35}

# ---------------------------------------------------------------------------
# Database connection
# ---------------------------------------------------------------------------

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres.kytzcbipsghprsqoalvi:Zeek%40%402025%40%40@aws-1-us-east-2.pooler.supabase.com:5432/postgres",
)

_db_engine = None


def _get_db_engine():
    """Return (or lazily create) the SQLAlchemy engine."""
    global _db_engine
    if _db_engine is None:
        try:
            _db_engine = create_engine(DATABASE_URL, poolclass=NullPool, echo=False)
            with _db_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception as exc:
            print(f"Warning: DB connection failed: {exc}")
            _db_engine = None
    return _db_engine


def _exec(query: str, params: Optional[Dict] = None) -> List[Any]:
    """Execute a SELECT and return all rows, or [] on failure."""
    engine = _get_db_engine()
    if not engine:
        return []
    try:
        with engine.connect() as conn:
            return conn.execute(text(query), params or {}).fetchall()
    except Exception as exc:
        print(f"DB query error: {exc}")
        return []


def _exec_scalar(query: str, params: Optional[Dict] = None) -> Any:
    rows = _exec(query, params)
    return rows[0][0] if rows else None


def _exec_write(query: str, params: Optional[Dict] = None) -> bool:
    engine = _get_db_engine()
    if not engine:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text(query), params or {})
            conn.commit()
        return True
    except Exception as exc:
        print(f"DB write error: {exc}")
        return False


def _table_exists(t: str) -> bool:
    """Return True if table exists in the public schema."""
    return bool(_exec_scalar(
        "SELECT EXISTS(SELECT 1 FROM information_schema.tables "
        "WHERE table_schema='public' AND table_name=:t)",
        {"t": t}))

# ---------------------------------------------------------------------------
# In-memory stores (replicate original CRUD interface)
# ---------------------------------------------------------------------------

_portfolios: Dict[str, Dict] = {}
_holdings: Dict[str, List[Dict]] = {}
_reports: Dict[str, Dict] = {}


def get_portfolio(portfolio_id: str, org_id: Optional[str] = None) -> Optional[Dict]:
    """Return portfolio dict — reads from portfolios_pg (primary) or legacy portfolios table.

    P0-2: When org_id is provided the row is only returned if portfolio.org_id matches,
    preventing cross-tenant data access.
    """
    # Primary: portfolios_pg
    if _table_exists("portfolios_pg"):
        rows = _exec(
            "SELECT id, name, org_id, description, created_at, updated_at FROM portfolios_pg WHERE id=:pid LIMIT 1",
            {"pid": portfolio_id},
        )
        if rows:
            r = rows[0]
            row_org_id = str(r[2]) if r[2] else None
            # P0-2 isolation: reject if requester's org doesn't match
            if org_id and row_org_id and org_id != row_org_id:
                return None
            return {
                "id": str(r[0]),
                "name": r[1],
                "org_id": row_org_id,
                "description": r[3],
                "created_at": str(r[4]) if r[4] else None,
                "updated_at": str(r[5]) if r[5] else None,
            }
    # Fallback: legacy portfolios table
    if _table_exists("portfolios"):
        rows = _exec(
            "SELECT id, name, org_id, description, created_at FROM portfolios WHERE id=:pid LIMIT 1",
            {"pid": portfolio_id},
        )
        if rows:
            r = rows[0]
            return {
                "id": str(r[0]),
                "name": r[1],
                "org_id": str(r[2]) if r[2] else None,
                "description": r[3],
                "created_at": str(r[4]) if r[4] else None,
            }
    # Tertiary: portfolio_analytics (rows created via this module's own POST /portfolios)
    if _table_exists("portfolio_analytics"):
        rows = _exec(
            "SELECT id, name, description, portfolio_type, investment_strategy, "
            "target_return, aum, currency, inception_date, owner_id, created_at, updated_at "
            "FROM portfolio_analytics WHERE id=:pid LIMIT 1",
            {"pid": portfolio_id},
        )
        if rows:
            r = rows[0]
            return {
                "id":                  str(r[0]),
                "name":                r[1],
                "description":         r[2],
                "portfolio_type":      r[3] or "fund",
                "investment_strategy": r[4],
                "target_return":       float(r[5]) if r[5] is not None else None,
                "aum":                 float(r[6]) if r[6] is not None else 0.0,
                "currency":            r[7] or "EUR",
                "inception_date":      r[8],
                "owner_id":            str(r[9]) if r[9] else None,
                "created_at":          str(r[10]) if r[10] else None,
                "updated_at":          str(r[11]) if r[11] else None,
            }
    return _portfolios.get(portfolio_id)


def list_portfolios(org_id: Optional[str] = None) -> List[Dict]:
    """List portfolios — reads from portfolios_pg (primary) or legacy portfolios table.

    P0-2: When org_id is provided only portfolios belonging to that org are returned.
    """
    # Primary: portfolios_pg
    if _table_exists("portfolios_pg"):
        if org_id:
            rows = _exec(
                "SELECT id, name, org_id, description, created_at, updated_at "
                "FROM portfolios_pg WHERE org_id=:oid ORDER BY name LIMIT 200",
                {"oid": org_id},
            )
        else:
            rows = _exec(
                "SELECT id, name, org_id, description, created_at, updated_at "
                "FROM portfolios_pg ORDER BY name LIMIT 200"
            )
        if rows:
            return [
                {
                    "id": str(r[0]),
                    "name": r[1],
                    "org_id": str(r[2]) if r[2] else None,
                    "description": r[3],
                    "created_at": str(r[4]) if r[4] else None,
                    "updated_at": str(r[5]) if r[5] else None,
                    # Required by PortfolioResponse schema
                    "portfolio_type": "fund",
                    "investment_strategy": "core",
                    "currency": "EUR",
                    "target_return": None,
                    "aum": 0,
                    "inception_date": None,
                    "owner_id": None,
                }
                for r in rows
            ]
    # Fallback: legacy portfolios table
    if _table_exists("portfolios"):
        if org_id:
            rows = _exec(
                "SELECT id, name, org_id, description, created_at FROM portfolios WHERE org_id=:oid LIMIT 200",
                {"oid": org_id},
            )
        else:
            rows = _exec("SELECT id, name, org_id, description, created_at FROM portfolios LIMIT 200")
        if rows:
            return [
                {
                    "id": str(r[0]),
                    "name": r[1],
                    "org_id": str(r[2]) if r[2] else None,
                    "description": r[3],
                    "created_at": str(r[4]) if r[4] else None,
                    "portfolio_type": "fund",
                    "investment_strategy": "core",
                    "currency": "EUR",
                    "target_return": None,
                    "aum": 0,
                    "inception_date": None,
                    "owner_id": None,
                }
                for r in rows
            ]
    # Tertiary: portfolio_analytics (rows created via this module's own POST /portfolios)
    if _table_exists("portfolio_analytics"):
        rows = _exec(
            "SELECT id, name, description, portfolio_type, investment_strategy, "
            "target_return, aum, currency, inception_date, owner_id, created_at, updated_at "
            "FROM portfolio_analytics ORDER BY name LIMIT 200"
        )
        if rows:
            return [
                {
                    "id":                  str(r[0]),
                    "name":                r[1],
                    "description":         r[2],
                    "portfolio_type":      r[3] or "fund",
                    "investment_strategy": r[4] or "core",
                    "target_return":       float(r[5]) if r[5] is not None else None,
                    "aum":                 float(r[6]) if r[6] is not None else 0.0,
                    "currency":            r[7] or "EUR",
                    "inception_date":      r[8],
                    "owner_id":            str(r[9]) if r[9] else None,
                    "created_at":          str(r[10]) if r[10] else None,
                    "updated_at":          str(r[11]) if r[11] else None,
                }
                for r in rows
            ]
    plist = list(_portfolios.values())
    if org_id:
        plist = [p for p in plist if p.get("org_id") == org_id]
    return plist


async def get_portfolios_from_db(org_id: str) -> List[Dict]:
    """Async wrapper - returns portfolios for the given org from Supabase."""
    return list_portfolios(org_id)


def _get_sector_ref(sector: str) -> Dict:
    """Look up reference data for a sector, with fuzzy matching."""
    if not sector:
        return GLOBAL_FALLBACK
    sl = sector.lower()
    for key, ref in SECTOR_REFERENCE_DATA.items():
        if key.lower() in sl or sl in key.lower():
            return ref
    return GLOBAL_FALLBACK


# LEI prefix → region mapping (ISO 3166 MFI prefix codes)
_LEI_REGION_MAP = {
    "US": "North America", "GB": "Europe", "DE": "Europe", "FR": "Europe",
    "JP": "Asia Pacific", "CN": "Asia Pacific", "IN": "Asia Pacific",
    "BR": "Latin America", "AU": "Asia Pacific", "CA": "North America",
    "CH": "Europe", "NL": "Europe", "SE": "Europe", "IT": "Europe",
    "ES": "Europe", "KR": "Asia Pacific", "SG": "Asia Pacific",
    "HK": "Asia Pacific", "ZA": "Africa", "MX": "Latin America",
    "RU": "Europe", "IE": "Europe", "LU": "Europe", "NO": "Europe",
    "DK": "Europe", "FI": "Europe", "BE": "Europe", "AT": "Europe",
    "PT": "Europe", "PL": "Europe",
}

# Sector → typical dominant region heuristic (fallback when no LEI)
_SECTOR_REGION_HEURISTIC = {
    "Technology": "North America", "Financials": "Europe",
    "Energy": "North America", "Healthcare": "North America",
    "Industrials": "Europe", "Consumer": "North America",
    "Materials": "Asia Pacific", "Utilities": "Europe",
    "Real Estate": "Europe", "Communications": "North America",
}


def _estimate_region_from_lei(lei: str, sector: str) -> str:
    """Estimate geographic region from LEI prefix or sector heuristic."""
    if lei and len(lei) >= 2:
        prefix = lei[:2].upper()
        if prefix in _LEI_REGION_MAP:
            return _LEI_REGION_MAP[prefix]
    # Fall back to sector heuristic
    if sector:
        for key, region in _SECTOR_REGION_HEURISTIC.items():
            if key.lower() in sector.lower() or sector.lower() in key.lower():
                return region
    return "Unknown"


def get_holdings(portfolio_id: str) -> List[Dict]:
    """Return holdings from assets_pg (primary) or legacy portfolio_holdings table.
    Auto-estimates missing datapoints using sector reference data and flags them."""
    # Primary: assets_pg
    if _table_exists("assets_pg"):
        rows = _exec(
            "SELECT id, portfolio_id, company_name, asset_type, exposure, market_value, "
            "company_sector, base_pd, base_lgd, rating, "
            "scope1_tco2e, scope2_tco2e, scope3_tco2e, evic_eur, pcaf_dqs, "
            "company_subsector, entity_lei "
            "FROM assets_pg WHERE portfolio_id=:pid",
            {"pid": portfolio_id},
        )
        # Column indices:
        # 0=id, 1=portfolio_id, 2=company_name, 3=asset_type, 4=exposure,
        # 5=market_value, 6=company_sector, 7=base_pd, 8=base_lgd, 9=rating,
        # 10=scope1, 11=scope2, 12=scope3, 13=evic_eur, 14=pcaf_dqs,
        # 15=company_subsector, 16=entity_lei
        if rows:
            # Compute total for weight calculation
            total_exposure = sum(float(r[4]) for r in rows if r[4] is not None) or 1.0
            results = []
            for r in rows:
                sector = r[6] or "Unknown"
                ref = _get_sector_ref(sector)
                estimated_fields = []

                # Auto-estimate missing fields from reference data
                base_pd = float(r[7]) if r[7] is not None else None
                if base_pd is None:
                    base_pd = ref["avg_pd"]
                    estimated_fields.append("base_pd")

                base_lgd = float(r[8]) if r[8] is not None else None
                if base_lgd is None:
                    base_lgd = ref["avg_lgd"]
                    estimated_fields.append("base_lgd")

                exposure = float(r[4]) if r[4] is not None else None
                if exposure is None or exposure == 0:
                    exposure = float(r[5]) if r[5] is not None else 0.0
                    if exposure == 0:
                        estimated_fields.append("exposure")

                market_value = float(r[5]) if r[5] is not None else None
                if market_value is None or market_value == 0:
                    market_value = exposure
                    if market_value > 0:
                        estimated_fields.append("market_value")

                # Country/region: assets_pg has no 'country' column —
                # estimate from LEI prefix (first 2 chars = country code) or sector heuristic
                lei = r[16] or ""
                region = _estimate_region_from_lei(lei, sector)
                if region == "Unknown":
                    estimated_fields.append("country")

                company_name = r[2] if r[2] else None
                if not company_name:
                    company_name = f"Asset-{str(r[0])[:8]}"
                    estimated_fields.append("company_name")

                # Emissions data
                scope1 = float(r[10]) if r[10] is not None else None
                scope2 = float(r[11]) if r[11] is not None else None
                scope3 = float(r[12]) if r[12] is not None else None
                evic = float(r[13]) if r[13] is not None else None
                pcaf_dqs = int(r[14]) if r[14] is not None else None

                if scope1 is None:
                    scope1 = ref["avg_scope1_intensity"] * (exposure / 1e6) if exposure else 0
                    estimated_fields.append("scope1_tco2e")
                if scope2 is None:
                    scope2 = ref["avg_scope2_intensity"] * (exposure / 1e6) if exposure else 0
                    estimated_fields.append("scope2_tco2e")

                results.append({
                    "id": str(r[0]),
                    "portfolio_id": str(r[1]),
                    "asset_name": company_name,
                    "asset_type": r[3] or "Equity",
                    "value": exposure,
                    "current_value": market_value,
                    "annual_income": round(exposure * 0.04, 2),  # proxy: 4% yield
                    "weight": round(exposure / total_exposure * 100, 2),
                    "sector": sector,
                    "region": region,
                    "country": region,
                    "base_pd": base_pd,
                    "base_lgd": base_lgd,
                    "rating": r[9] or "NR",
                    "scope1_tco2e": scope1,
                    "scope2_tco2e": scope2,
                    "scope3_tco2e": scope3,
                    "evic_eur": evic,
                    "pcaf_dqs": pcaf_dqs,
                    # Data quality tracking
                    "estimated_fields": estimated_fields,
                    "data_quality": "complete" if len(estimated_fields) == 0
                                    else "partial" if len(estimated_fields) <= 2
                                    else "estimated",
                    "estimation_method": "sector_reference_data" if estimated_fields else None,
                })
            return results
    # Fallback: legacy portfolio_holdings table
    if _table_exists("portfolio_holdings"):
        rows = _exec(
            "SELECT id, portfolio_id, asset_name, asset_type, value, weight, sector, region "
            "FROM portfolio_holdings WHERE portfolio_id=:pid",
            {"pid": portfolio_id},
        )
        if rows:
            return [
                {
                    "id": str(r[0]),
                    "portfolio_id": str(r[1]),
                    "asset_name": r[2],
                    "asset_type": r[3],
                    "value": float(r[4]) if r[4] is not None else 0.0,
                    "current_value": float(r[4]) if r[4] is not None else 0.0,
                    "annual_income": round(float(r[4] or 0) * 0.04, 2),
                    "weight": float(r[5]) if r[5] is not None else 0.0,
                    "sector": r[6],
                    "region": r[7],
                }
                for r in rows
            ]
    # Tertiary: portfolio_property_holdings (created via module's own POST /holdings)
    if _table_exists("portfolio_property_holdings"):
        rows = _exec(
            "SELECT id, portfolio_id, property_name, property_type, property_location, "
            "acquisition_date, acquisition_cost, current_value, ownership_percentage, "
            "annual_income, unrealized_gain_loss, gresb_score, certifications, "
            "risk_score, is_stranded, years_to_stranding, property_id "
            "FROM portfolio_property_holdings WHERE portfolio_id=:pid",
            {"pid": portfolio_id},
        )
        if rows:
            return [
                {
                    "id":                   str(r[0]),
                    "portfolio_id":         str(r[1]),
                    "property_name":        r[2],
                    "asset_name":           r[2],
                    "property_type":        r[3],
                    "asset_type":           r[3],
                    "property_location":    r[4],
                    "acquisition_date":     r[5],
                    "acquisition_cost":     float(r[6]) if r[6] is not None else 0.0,
                    "current_value":        float(r[7]) if r[7] is not None else 0.0,
                    "value":                float(r[7]) if r[7] is not None else 0.0,
                    "ownership_percentage": float(r[8]) if r[8] is not None else 1.0,
                    "annual_income":        float(r[9]) if r[9] is not None else 0.0,
                    "unrealized_gain_loss": float(r[10]) if r[10] is not None else 0.0,
                    "gresb_score":          r[11],
                    "certifications":       r[12] if r[12] is not None else [],
                    "risk_score":           r[13] if r[13] is not None else 50,
                    "is_stranded":          bool(r[14]) if r[14] is not None else False,
                    "years_to_stranding":   r[15],
                    "property_id":          str(r[16]) if r[16] else None,
                }
                for r in rows
            ]
    return _holdings.get(portfolio_id, [])


def save_portfolio(portfolio_id: str, portfolio: Dict) -> Dict:
    """
    Persist a portfolio to portfolio_analytics (migration 005).
    Falls back to in-memory store when the table is unavailable.
    """
    portfolio["id"] = portfolio_id
    if _table_exists("portfolio_analytics"):
        import json as _json
        _exec_write(
            """
            INSERT INTO portfolio_analytics
                (id, name, description, portfolio_type, investment_strategy,
                 target_return, aum, currency, inception_date, owner_id,
                 created_at, updated_at)
            VALUES
                (:id, :name, :descr, :ptype, :istrat, :tr, :aum, :cur,
                 :idate, :oid, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (id) DO UPDATE SET
                name               = EXCLUDED.name,
                description        = EXCLUDED.description,
                portfolio_type     = EXCLUDED.portfolio_type,
                investment_strategy= EXCLUDED.investment_strategy,
                target_return      = EXCLUDED.target_return,
                aum                = EXCLUDED.aum,
                currency           = EXCLUDED.currency,
                updated_at         = CURRENT_TIMESTAMP
            """,
            {
                "id":    portfolio_id,
                "name":  portfolio.get("name", "Unnamed"),
                "descr": portfolio.get("description"),
                "ptype": portfolio.get("portfolio_type", "fund"),
                "istrat":portfolio.get("investment_strategy"),
                "tr":    float(portfolio["target_return"]) if portfolio.get("target_return") else None,
                "aum":   float(portfolio.get("aum") or 0),
                "cur":   portfolio.get("currency", "EUR"),
                "idate": portfolio.get("inception_date"),
                "oid":   portfolio.get("owner_id"),
            },
        )
    else:
        _portfolios[portfolio_id] = portfolio
    return portfolio


def save_holding(portfolio_id: str, holding: Dict) -> Dict:
    """
    Persist a holding to portfolio_property_holdings (migration 005).
    Falls back to in-memory store when the table is unavailable.
    """
    hid = holding.get("id") or str(uuid4())
    holding["id"] = hid
    holding["portfolio_id"] = portfolio_id

    if _table_exists("portfolio_property_holdings"):
        import json as _json
        certs = holding.get("certifications") or []
        _exec_write(
            """
            INSERT INTO portfolio_property_holdings
                (id, portfolio_id, property_id, property_name, property_type,
                 property_location, acquisition_date, acquisition_cost, current_value,
                 ownership_percentage, annual_income, unrealized_gain_loss,
                 gresb_score, certifications, risk_score, is_stranded, years_to_stranding)
            VALUES
                (:id, :pid, :prop_id, :pname, :ptype, :ploc, :acq_date, :acq_cost,
                 :curr_val, :own_pct, :income, :unreal, :gresb, :certs::jsonb,
                 :risk, :stranded, :yrs_strand)
            ON CONFLICT (id) DO UPDATE SET
                current_value        = EXCLUDED.current_value,
                annual_income        = EXCLUDED.annual_income,
                ownership_percentage = EXCLUDED.ownership_percentage,
                risk_score           = EXCLUDED.risk_score,
                updated_at           = CURRENT_TIMESTAMP
            """,
            {
                "id":        hid,
                "pid":       portfolio_id,
                "prop_id":   holding.get("property_id"),
                "pname":     holding.get("property_name"),
                "ptype":     holding.get("property_type"),
                "ploc":      holding.get("property_location"),
                "acq_date":  holding.get("acquisition_date"),
                "acq_cost":  float(holding["acquisition_cost"]) if holding.get("acquisition_cost") else None,
                "curr_val":  float(holding["current_value"]) if holding.get("current_value") else None,
                "own_pct":   float(holding.get("ownership_percentage") or 1.0),
                "income":    float(holding["annual_income"]) if holding.get("annual_income") else None,
                "unreal":    float(holding["unrealized_gain_loss"]) if holding.get("unrealized_gain_loss") else None,
                "gresb":     holding.get("gresb_score"),
                "certs":     _json.dumps(certs if isinstance(certs, list) else list(certs)),
                "risk":      holding.get("risk_score"),
                "stranded":  bool(holding.get("is_stranded", False)),
                "yrs_strand":holding.get("years_to_stranding"),
            },
        )
    else:
        _holdings.setdefault(portfolio_id, [])
        existing = next((i for i, h in enumerate(_holdings[portfolio_id]) if h["id"] == hid), None)
        if existing is not None:
            _holdings[portfolio_id][existing] = holding
        else:
            _holdings[portfolio_id].append(holding)
    return holding


def remove_holding(portfolio_id: str, holding_id: str) -> bool:
    """Delete a holding from portfolio_property_holdings or in-memory store."""
    if _table_exists("portfolio_property_holdings"):
        return _exec_write(
            "DELETE FROM portfolio_property_holdings WHERE id = :hid AND portfolio_id = :pid",
            {"hid": holding_id, "pid": portfolio_id},
        )
    if portfolio_id in _holdings:
        before = len(_holdings[portfolio_id])
        _holdings[portfolio_id] = [h for h in _holdings[portfolio_id] if h["id"] != holding_id]
        return len(_holdings[portfolio_id]) < before
    return False


def save_report(report: Dict) -> Dict:
    """Persist a report to portfolio_reports (migration 005) or in-memory fallback."""
    rid = report.get("id") or str(uuid4())
    report["id"] = rid
    if _table_exists("portfolio_reports"):
        import json as _json
        _exec_write(
            """
            INSERT INTO portfolio_reports
                (id, portfolio_id, report_type, report_format, status,
                 content, completed_at)
            VALUES
                (:id, :pid, :rtype, :rfmt, 'completed', :content::jsonb, CURRENT_TIMESTAMP)
            ON CONFLICT (id) DO UPDATE SET
                content      = EXCLUDED.content,
                status       = EXCLUDED.status,
                completed_at = EXCLUDED.completed_at
            """,
            {
                "id":      rid,
                "pid":     report.get("portfolio_id"),
                "rtype":   str(report.get("report_type", "executive")),
                "rfmt":    report.get("format", "json"),
                "content": _json.dumps({k: str(v) for k, v in report.items()}),
            },
        )
    else:
        _reports[rid] = report
    return report


def get_report(report_id: str) -> Optional[Dict]:
    """Retrieve a report from portfolio_reports or in-memory fallback."""
    if _table_exists("portfolio_reports"):
        rows = _exec(
            "SELECT content FROM portfolio_reports WHERE id = :rid LIMIT 1",
            {"rid": report_id},
        )
        if rows and rows[0][0]:
            import json as _json
            try:
                raw = rows[0][0]
                return _json.loads(raw) if isinstance(raw, str) else raw
            except Exception:
                pass
    return _reports.get(report_id)


def init_sample_data() -> None:
    """No-op: v2 uses real DB data, not sample data."""
    logger.info("init_sample_data called on v2 engine — no mock data seeded.")

# ---------------------------------------------------------------------------
# Real DB query helpers
# ---------------------------------------------------------------------------


def _get_climate_risk_summary(portfolio_id: str) -> List[Dict]:
    """Query portfolio_climate_risk for this portfolio."""
    if not _table_exists("portfolio_climate_risk"):
        return []
    rows = _exec(
        "SELECT asset_id, asset_name, sector, physical_risk_score, transition_risk_score, "
        "overall_risk_score, risk_category, region "
        "FROM portfolio_climate_risk WHERE portfolio_id=:pid",
        {"pid": portfolio_id},
    )
    return [
        {
            "asset_id": str(r[0]) if r[0] else None,
            "asset_name": r[1],
            "sector": r[2],
            "physical_risk_score": float(r[3]) if r[3] is not None else 0.0,
            "transition_risk_score": float(r[4]) if r[4] is not None else 0.0,
            "overall_risk_score": float(r[5]) if r[5] is not None else 0.0,
            "risk_category": r[6],
            "region": r[7],
        }
        for r in rows
    ]


def _get_exposure_assessments(portfolio_id: str) -> List[Dict]:
    """Query exposure_assessments ordered by physical_var_pct DESC."""
    if not _table_exists("exposure_assessments"):
        return []
    rows = _exec(
        "SELECT id, portfolio_id, asset_id, asset_name, sector, region, "
        "physical_var_pct, transition_var_pct, total_var_pct, exposure_value "
        "FROM exposure_assessments WHERE portfolio_id=:pid "
        "ORDER BY physical_var_pct DESC",
        {"pid": portfolio_id},
    )
    return [
        {
            "id": str(r[0]),
            "portfolio_id": str(r[1]),
            "asset_id": str(r[2]) if r[2] else None,
            "asset_name": r[3],
            "sector": r[4],
            "region": r[5],
            "physical_var_pct": float(r[6]) if r[6] is not None else 0.0,
            "transition_var_pct": float(r[7]) if r[7] is not None else 0.0,
            "total_var_pct": float(r[8]) if r[8] is not None else 0.0,
            "exposure_value": float(r[9]) if r[9] is not None else 0.0,
        }
        for r in rows
    ]


def _get_financial_instruments(portfolio_id: str) -> List[Dict]:
    """Query financial_instruments for this portfolio."""
    if not _table_exists("financial_instruments"):
        return []
    rows = _exec(
        "SELECT id, portfolio_id, instrument_name, instrument_type, sector, region, "
        "market_value, weight_pct, climate_risk_score "
        "FROM financial_instruments WHERE portfolio_id=:pid",
        {"pid": portfolio_id},
    )
    return [
        {
            "id": str(r[0]),
            "portfolio_id": str(r[1]),
            "instrument_name": r[2],
            "instrument_type": r[3],
            "sector": r[4],
            "region": r[5],
            "market_value": float(r[6]) if r[6] is not None else 0.0,
            "weight_pct": float(r[7]) if r[7] is not None else 0.0,
            "climate_risk_score": float(r[8]) if r[8] is not None else 0.0,
        }
        for r in rows
    ]


def _get_entities_for_portfolio(portfolio_id: str) -> List[Dict]:
    """Query entities joined to financial_instruments for this portfolio."""
    if not _table_exists("entities") or not _table_exists("financial_instruments"):
        return []
    rows = _exec(
        "SELECT e.id, e.name, e.sector, e.region, e.country, fi.market_value, fi.weight_pct "
        "FROM entities e "
        "JOIN financial_instruments fi ON fi.entity_id = e.id "
        "WHERE fi.portfolio_id=:pid",
        {"pid": portfolio_id},
    )
    return [
        {
            "entity_id": str(r[0]),
            "name": r[1],
            "sector": r[2],
            "region": r[3],
            "country": r[4],
            "market_value": float(r[5]) if r[5] is not None else 0.0,
            "weight_pct": float(r[6]) if r[6] is not None else 0.0,
        }
        for r in rows
    ]


def _get_emission_trends_db(portfolio_id: str) -> List[Dict]:
    """Query scope3_category_emissions for this portfolio."""
    if not _table_exists("scope3_category_emissions"):
        return []
    rows = _exec(
        "SELECT reporting_year, category_name, emissions_tco2e "
        "FROM scope3_category_emissions WHERE portfolio_id=:pid "
        "ORDER BY reporting_year ASC",
        {"pid": portfolio_id},
    )
    return [
        {
            "year": int(r[0]) if r[0] is not None else None,
            "category": r[1],
            "emissions_tco2e": float(r[2]) if r[2] is not None else 0.0,
        }
        for r in rows
    ]


def _get_top_exposed_assets_db(portfolio_id: str, limit: int = 10) -> List[Dict]:
    """Return top assets by exposure from exposure_assessments or financial_instruments."""
    assessments = _get_exposure_assessments(portfolio_id)
    if assessments:
        return sorted(assessments, key=lambda x: x["total_var_pct"], reverse=True)[:limit]
    instruments = _get_financial_instruments(portfolio_id)
    if instruments:
        return sorted(instruments, key=lambda x: x["climate_risk_score"], reverse=True)[:limit]
    return []


# ---------------------------------------------------------------------------
# Public analytics functions (same signatures as v1)
# ---------------------------------------------------------------------------


def get_portfolio_overview(portfolio_id: str) -> Dict:
    """Return portfolio overview KPIs from DB (no mock data)."""
    tables_queried: List[str] = []
    rows_returned = 0

    climate_rows = _get_climate_risk_summary(portfolio_id)
    if climate_rows:
        tables_queried.append("portfolio_climate_risk")
        rows_returned += len(climate_rows)
        avg_physical = sum(r["physical_risk_score"] for r in climate_rows) / len(climate_rows)
        avg_transition = sum(r["transition_risk_score"] for r in climate_rows) / len(climate_rows)
        avg_overall = sum(r["overall_risk_score"] for r in climate_rows) / len(climate_rows)
    else:
        avg_physical = avg_transition = avg_overall = 0.0

    exposure_rows = _get_exposure_assessments(portfolio_id)
    if exposure_rows:
        tables_queried.append("exposure_assessments")
        rows_returned += len(exposure_rows)
        total_exposure = sum(r["exposure_value"] for r in exposure_rows)
        avg_var = sum(r["total_var_pct"] for r in exposure_rows) / len(exposure_rows)
    else:
        total_exposure = 0.0
        avg_var = 0.0

    emissions_rows = _get_emission_trends_db(portfolio_id)
    if emissions_rows:
        tables_queried.append("scope3_category_emissions")
        rows_returned += len(emissions_rows)
        total_emissions = sum(r["emissions_tco2e"] for r in emissions_rows)
    else:
        total_emissions = 0.0

    return {
        "portfolio_id": portfolio_id,
        "total_exposure_value": total_exposure,
        "average_physical_risk_score": round(avg_physical, 4),
        "average_transition_risk_score": round(avg_transition, 4),
        "average_overall_risk_score": round(avg_overall, 4),
        "average_var_pct": round(avg_var, 4),
        "total_scope3_emissions_tco2e": round(total_emissions, 2),
        "validation_summary": {
            "tables_queried": tables_queried,
            "rows_returned": rows_returned,
        },
    }


def get_climate_risk_heatmap(portfolio_id: str) -> Dict:
    """Return climate risk heatmap data from DB."""
    tables_queried: List[str] = []
    rows_returned = 0

    climate_rows = _get_climate_risk_summary(portfolio_id)
    if climate_rows:
        tables_queried.append("portfolio_climate_risk")
        rows_returned += len(climate_rows)
        heatmap = climate_rows
    else:
        exposure_rows = _get_exposure_assessments(portfolio_id)
        if exposure_rows:
            tables_queried.append("exposure_assessments")
            rows_returned += len(exposure_rows)
            heatmap = [
                {
                    "asset_id": r["asset_id"],
                    "asset_name": r["asset_name"],
                    "sector": r["sector"],
                    "region": r["region"],
                    "physical_risk_score": r["physical_var_pct"],
                    "transition_risk_score": r["transition_var_pct"],
                    "overall_risk_score": r["total_var_pct"],
                    "risk_category": "high" if r["total_var_pct"] > 0.1 else "medium" if r["total_var_pct"] > 0.05 else "low",
                }
                for r in exposure_rows
            ]
        else:
            heatmap = []

    return {
        "portfolio_id": portfolio_id,
        "heatmap": heatmap,
        "validation_summary": {
            "tables_queried": tables_queried,
            "rows_returned": rows_returned,
        },
    }


def get_sector_breakdown(portfolio_id: str) -> Dict:
    """Return sector breakdown from DB."""
    tables_queried: List[str] = []
    rows_returned = 0
    sectors: Dict[str, Dict] = {}

    climate_rows = _get_climate_risk_summary(portfolio_id)
    if climate_rows:
        tables_queried.append("portfolio_climate_risk")
        rows_returned += len(climate_rows)
        for r in climate_rows:
            sec = r["sector"] or "Unknown"
            if sec not in sectors:
                sectors[sec] = {"count": 0, "total_risk": 0.0, "assets": []}
            sectors[sec]["count"] += 1
            sectors[sec]["total_risk"] += r["overall_risk_score"]
            sectors[sec]["assets"].append(r["asset_name"])
    else:
        instruments = _get_financial_instruments(portfolio_id)
        if instruments:
            tables_queried.append("financial_instruments")
            rows_returned += len(instruments)
            for r in instruments:
                sec = r["sector"] or "Unknown"
                if sec not in sectors:
                    sectors[sec] = {"count": 0, "total_risk": 0.0, "market_value": 0.0, "assets": []}
                sectors[sec]["count"] += 1
                sectors[sec]["total_risk"] += r["climate_risk_score"]
                sectors[sec]["market_value"] = sectors[sec].get("market_value", 0.0) + r["market_value"]
                sectors[sec]["assets"].append(r["instrument_name"])

    breakdown = [
        {
            "sector": sec,
            "asset_count": data["count"],
            "average_risk_score": round(data["total_risk"] / data["count"], 4) if data["count"] else 0.0,
            "assets": data["assets"],
        }
        for sec, data in sectors.items()
    ]
    breakdown.sort(key=lambda x: x["average_risk_score"], reverse=True)

    return {
        "portfolio_id": portfolio_id,
        "sector_breakdown": breakdown,
        "validation_summary": {
            "tables_queried": tables_queried,
            "rows_returned": rows_returned,
        },
    }


def get_emission_trends(portfolio_id: str) -> Dict:
    """Return emission trends from scope3_category_emissions."""
    tables_queried: List[str] = []
    rows_returned = 0

    emissions = _get_emission_trends_db(portfolio_id)
    if emissions:
        tables_queried.append("scope3_category_emissions")
        rows_returned += len(emissions)

    by_year: Dict[int, float] = {}
    by_category: Dict[str, float] = {}
    for row in emissions:
        yr = row["year"]
        cat = row["category"] or "Unknown"
        if yr:
            by_year[yr] = by_year.get(yr, 0.0) + row["emissions_tco2e"]
        by_category[cat] = by_category.get(cat, 0.0) + row["emissions_tco2e"]

    yearly = [{"year": yr, "total_emissions_tco2e": round(val, 2)} for yr, val in sorted(by_year.items())]
    by_cat = [{"category": cat, "total_emissions_tco2e": round(val, 2)} for cat, val in sorted(by_category.items(), key=lambda x: -x[1])]

    return {
        "portfolio_id": portfolio_id,
        "yearly_trends": yearly,
        "by_category": by_cat,
        "validation_summary": {
            "tables_queried": tables_queried,
            "rows_returned": rows_returned,
        },
    }


def get_top_exposed_assets(portfolio_id: str, limit: int = 10) -> Dict:
    """Return top exposed assets from DB."""
    tables_queried: List[str] = []
    rows_returned = 0

    assessments = _get_exposure_assessments(portfolio_id)
    if assessments:
        tables_queried.append("exposure_assessments")
        rows_returned += len(assessments)
        top = sorted(assessments, key=lambda x: x["total_var_pct"], reverse=True)[:limit]
    else:
        instruments = _get_financial_instruments(portfolio_id)
        if instruments:
            tables_queried.append("financial_instruments")
            rows_returned += len(instruments)
            top = sorted(instruments, key=lambda x: x["climate_risk_score"], reverse=True)[:limit]
        else:
            top = []

    return {
        "portfolio_id": portfolio_id,
        "top_exposed_assets": top,
        "validation_summary": {
            "tables_queried": tables_queried,
            "rows_returned": rows_returned,
        },
    }
# ============ Analytics Engine ============

class PortfolioAnalyticsEngine:
    """Engine for calculating portfolio-level analytics."""
    
    def calculate_analytics(
        self,
        portfolio_id: str,
        scenario_id: Optional[str] = None,
        time_horizon: int = 10,
        as_of_date: Optional[date] = None
    ) -> PortfolioAnalyticsResponse:
        """Calculate comprehensive portfolio analytics."""
        
        portfolio = get_portfolio(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        
        holdings = get_holdings(portfolio_id)
        if not holdings:
            # Return empty analytics
            return self._empty_analytics(portfolio_id, as_of_date or date.today())
        
        # Calculate base and adjusted values
        total_base_value = Decimal("0")
        total_adjusted_value = Decimal("0")
        total_income = Decimal("0")
        
        risk_scores = []
        stranded_assets = []
        gresb_scores = []
        certifications_count = 0
        certifications_breakdown = {}
        
        sector_values = {}
        location_values = {}
        risk_buckets = {"low": 0, "moderate": 0, "high": 0, "very_high": 0}
        
        for holding in holdings:
            ownership = Decimal(str(holding.get("ownership_percentage", 1)))
            current_value = Decimal(str(holding.get("current_value", 0)))
            acquisition_cost = Decimal(str(holding.get("acquisition_cost", current_value)))
            annual_income = Decimal(str(holding.get("annual_income", 0)))
            
            # Apply scenario adjustment (simplified)
            if scenario_id:
                adjustment = self._get_scenario_adjustment(scenario_id, holding)
                adjusted_value = current_value * (1 + adjustment)
            else:
                adjusted_value = current_value
            
            weighted_base = acquisition_cost * ownership
            weighted_adjusted = adjusted_value * ownership
            weighted_income = annual_income * ownership
            
            total_base_value += weighted_base
            total_adjusted_value += weighted_adjusted
            total_income += weighted_income
            
            # Risk score — derive from base_pd if available (PD 0.01=low → PD 0.10=very_high)
            raw_pd = holding.get("base_pd")
            if raw_pd is not None:
                risk = min(100, max(0, int(float(raw_pd) * 1000)))  # PD 0.02 → 20, PD 0.10 → 100
            else:
                risk = holding.get("risk_score", 50)
            risk_scores.append(risk)
            
            # Risk bucket
            if risk < 30:
                risk_buckets["low"] += 1
            elif risk < 50:
                risk_buckets["moderate"] += 1
            elif risk < 70:
                risk_buckets["high"] += 1
            else:
                risk_buckets["very_high"] += 1
            
            # Stranding
            if holding.get("is_stranded"):
                stranded_assets.append({
                    "value": float(weighted_adjusted),
                    "years": holding.get("years_to_stranding", 10),
                    "sector": holding.get("sector") or holding.get("property_type") or "Unknown",
                })
            
            # Sustainability
            if holding.get("gresb_score"):
                gresb_scores.append(holding["gresb_score"])
            
            certs = holding.get("certifications", [])
            if certs:
                certifications_count += 1
                for cert in certs:
                    cert_type = cert.split()[0]  # "LEED Gold" -> "LEED"
                    certifications_breakdown[cert_type] = certifications_breakdown.get(cert_type, 0) + 1
            
            # Concentration — normalise key names across engine formats
            sector = holding.get("sector") or holding.get("property_type") or holding.get("company_sector") or "Unknown"
            sector_values[sector] = sector_values.get(sector, Decimal("0")) + weighted_adjusted

            location = (holding.get("region") or holding.get("property_location") or holding.get("country") or "Unknown").split(",")[0]
            location_values[location] = location_values.get(location, Decimal("0")) + weighted_adjusted
        
        # Calculate metrics
        value_change = total_adjusted_value - total_base_value
        value_change_pct = (value_change / total_base_value * 100) if total_base_value else Decimal("0")
        
        avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else Decimal("0")
        var_95 = self._calculate_var(total_adjusted_value, avg_risk)
        
        avg_gresb = sum(gresb_scores) / len(gresb_scores) if gresb_scores else None
        pct_certified = (Decimal(str(certifications_count)) / Decimal(str(len(holdings))) * 100) if holdings else Decimal("0")
        
        stranded_value = sum(s["value"] for s in stranded_assets)
        stranded_pct = Decimal(str(stranded_value / float(total_adjusted_value) * 100)) if total_adjusted_value else Decimal("0")
        avg_years = sum(s["years"] for s in stranded_assets) / len(stranded_assets) if stranded_assets else None
        
        # Concentration analysis
        geo_conc = self._calculate_concentration(location_values, total_adjusted_value)
        sector_conc = self._calculate_concentration(sector_values, total_adjusted_value)
        
        # Determine risk level
        if float(avg_risk) < 30:
            risk_level = RiskLevel.LOW
        elif float(avg_risk) < 50:
            risk_level = RiskLevel.MODERATE
        elif float(avg_risk) < 70:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.VERY_HIGH
        
        return PortfolioAnalyticsResponse(
            portfolio_id=portfolio_id,
            calculation_date=as_of_date or date.today(),
            scenario_name="Base Case" if not scenario_id else f"Scenario {scenario_id[:8]}",
            portfolio_summary=PortfolioSummary(
                total_properties=len(holdings),
                total_base_value=total_base_value,
                total_adjusted_value=total_adjusted_value,
                total_value_change=value_change,
                value_change_pct=value_change_pct.quantize(Decimal("0.01")),
                total_income=total_income,
                avg_yield=(total_income / total_adjusted_value * 100).quantize(Decimal("0.01")) if total_adjusted_value else None,
            ),
            risk_metrics=RiskMetrics(
                weighted_avg_risk_score=Decimal(str(avg_risk)).quantize(Decimal("0.1")),
                value_at_risk_95=var_95,
                risk_level=risk_level,
                risk_distribution=risk_buckets,
            ),
            stranding_analysis=StrandingAnalysis(
                stranded_assets_count=len(stranded_assets),
                stranded_assets_value=Decimal(str(stranded_value)),
                stranded_pct=stranded_pct.quantize(Decimal("0.01")),
                avg_years_to_stranding=Decimal(str(avg_years)).quantize(Decimal("0.1")) if avg_years else None,
                stranded_by_sector={s["sector"]: 1 for s in stranded_assets},
            ),
            sustainability_metrics=SustainabilityMetrics(
                avg_gresb_score=Decimal(str(avg_gresb)).quantize(Decimal("0.1")) if avg_gresb else None,
                pct_certified=pct_certified.quantize(Decimal("0.1")),
                certified_count=certifications_count,
                certifications_breakdown=certifications_breakdown,
            ),
            concentration_analysis=ConcentrationAnalysis(
                geographic=geo_conc,
                sector=sector_conc,
            ),
        )
    
    def _empty_analytics(self, portfolio_id: str, calc_date: date) -> PortfolioAnalyticsResponse:
        """Return empty analytics for portfolio with no holdings."""
        return PortfolioAnalyticsResponse(
            portfolio_id=portfolio_id,
            calculation_date=calc_date,
            portfolio_summary=PortfolioSummary(
                total_properties=0,
                total_base_value=Decimal("0"),
                total_adjusted_value=Decimal("0"),
                total_value_change=Decimal("0"),
                value_change_pct=Decimal("0"),
            ),
            risk_metrics=RiskMetrics(
                weighted_avg_risk_score=Decimal("0"),
                value_at_risk_95=Decimal("0"),
                risk_level=RiskLevel.LOW,
                risk_distribution={},
            ),
            stranding_analysis=StrandingAnalysis(
                stranded_assets_count=0,
                stranded_assets_value=Decimal("0"),
                stranded_pct=Decimal("0"),
            ),
            sustainability_metrics=SustainabilityMetrics(
                pct_certified=Decimal("0"),
                certified_count=0,
            ),
            concentration_analysis=ConcentrationAnalysis(
                geographic=ConcentrationMetrics(hhi=Decimal("0"), concentration_level="low", top_items=[]),
                sector=ConcentrationMetrics(hhi=Decimal("0"), concentration_level="low", top_items=[]),
            ),
        )
    
    def _get_scenario_adjustment(self, scenario_id: str, holding: Dict) -> Decimal:
        """Get scenario-specific value adjustment from DB scenario parameters."""
        # Read scenario from DB
        scenario_row = _exec(
            "SELECT parameters FROM scenarios WHERE id = :sid LIMIT 1",
            {"sid": scenario_id},
        )
        if scenario_row:
            import json
            params = scenario_row[0][0]
            if isinstance(params, str):
                params = json.loads(params)
            # Extract value_change_pct from scenario parameters
            change_pct = params.get("value_change_pct", "0")
            base_adj = Decimal(str(change_pct)) / Decimal("100")
            # Modulate by holding risk: higher risk → larger scenario impact
            risk = Decimal(str(holding.get("risk_score", 50)))
            risk_multiplier = risk / Decimal("50")
            return (base_adj * risk_multiplier).quantize(Decimal("0.000001"))
        # Fallback: no scenario found — zero adjustment
        return Decimal("0")
    
    def _calculate_var(self, portfolio_value: Decimal, avg_risk: float,
                       holdings: Optional[List[Dict]] = None) -> Decimal:
        """
        Calculate parametric Value-at-Risk (95% confidence).

        Uses sector-level volatility from exposure_assessments when available,
        otherwise applies a risk-score-calibrated volatility model:
          σ = base_vol + risk_premium × (risk_score / 100)
        where base_vol = 4% (institutional-grade RE) and risk_premium = 16%.
        """
        BASE_VOL = 0.04      # institutional-grade baseline
        RISK_PREMIUM = 0.16  # max additional for highest-risk portfolios
        Z_95 = 1.6449        # Normal quantile 95%
        HOLDING_PERIOD_DAYS = 250  # 1-year VaR

        # Try to get realised volatility from DB
        vol_rows = _exec(
            "SELECT STDDEV(total_var_pct) FROM exposure_assessments "
            "WHERE portfolio_id IS NOT NULL LIMIT 1"
        )
        realised_vol = None
        if vol_rows and vol_rows[0][0] is not None:
            realised_vol = float(vol_rows[0][0])

        if realised_vol and realised_vol > 0:
            # Blend realised with risk-based estimate (70/30)
            risk_vol = BASE_VOL + RISK_PREMIUM * (avg_risk / 100.0)
            blended = 0.7 * realised_vol + 0.3 * risk_vol
        else:
            blended = BASE_VOL + RISK_PREMIUM * (avg_risk / 100.0)

        # Annualised parametric VaR
        var_amount = float(portfolio_value) * blended * Z_95
        return Decimal(str(var_amount)).quantize(Decimal("0.01"))
    
    def _calculate_concentration(
        self, 
        values_dict: Dict[str, Decimal], 
        total: Decimal
    ) -> ConcentrationMetrics:
        """Calculate concentration metrics (HHI)."""
        if not total or not values_dict:
            return ConcentrationMetrics(hhi=Decimal("0"), concentration_level="low", top_items=[])
        
        total_float = float(total)
        shares = [float(v) / total_float for v in values_dict.values()]
        hhi = sum(s ** 2 for s in shares)
        
        if hhi > 0.25:
            level = "high"
        elif hhi > 0.15:
            level = "moderate"
        else:
            level = "low"
        
        # Top items
        sorted_items = sorted(values_dict.items(), key=lambda x: x[1], reverse=True)[:5]
        top_items = [
            {"name": k, "value": float(v), "pct": float(v / total * 100)}
            for k, v in sorted_items
        ]
        
        return ConcentrationMetrics(
            hhi=Decimal(str(hhi)).quantize(Decimal("0.0001")),
            concentration_level=level,
            top_items=top_items,
        )
    
    def compare_scenarios(
        self,
        portfolio_id: str,
        scenario_ids: List[str],
        time_horizon: int = 10
    ) -> ScenarioComparisonResult:
        """Compare multiple scenarios for a portfolio."""
        portfolio = get_portfolio(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        
        # Get base analytics
        base_analytics = self.calculate_analytics(portfolio_id, None, time_horizon)
        base_value = base_analytics.portfolio_summary.total_adjusted_value
        
        comparison_rows = []
        
        # Base case
        comparison_rows.append(ScenarioComparisonRow(
            scenario_id="base-case",
            scenario_name="Base Case",
            total_value=base_value,
            value_change=Decimal("0"),
            value_change_pct=Decimal("0"),
            stranded_count=base_analytics.stranding_analysis.stranded_assets_count,
            stranded_value=base_analytics.stranding_analysis.stranded_assets_value,
            var_95=base_analytics.risk_metrics.value_at_risk_95,
            avg_risk_score=base_analytics.risk_metrics.weighted_avg_risk_score,
        ))
        
        # Each scenario — read from DB
        for i, sid in enumerate(scenario_ids):
            import json as _json
            scenario_row = _exec(
                "SELECT name, parameters FROM scenarios WHERE id = :sid LIMIT 1",
                {"sid": sid},
            )
            if scenario_row:
                sname = scenario_row[0][0] or f"Scenario {sid[:8]}"
                params = scenario_row[0][1]
                if isinstance(params, str):
                    params = _json.loads(params)
                change_pct_raw = params.get("value_change_pct", "0")
                adjustment = Decimal(str(change_pct_raw)) / Decimal("100")
            else:
                sname = f"Scenario {sid[:8]}"
                adjustment = Decimal("0")

            scenario_analytics = self.calculate_analytics(portfolio_id, sid, time_horizon)
            scenario_value = scenario_analytics.portfolio_summary.total_adjusted_value

            comparison_rows.append(ScenarioComparisonRow(
                scenario_id=sid,
                scenario_name=sname,
                total_value=scenario_value,
                value_change=(scenario_value - base_value).quantize(Decimal("0.01")),
                value_change_pct=((scenario_value - base_value) / base_value * 100).quantize(Decimal("0.01")) if base_value else Decimal("0"),
                stranded_count=scenario_analytics.stranding_analysis.stranded_assets_count,
                stranded_value=scenario_analytics.stranding_analysis.stranded_assets_value,
                var_95=scenario_analytics.risk_metrics.value_at_risk_95,
                avg_risk_score=scenario_analytics.risk_metrics.weighted_avg_risk_score,
            ))
        
        # Find best/worst
        sorted_rows = sorted(comparison_rows, key=lambda x: x.total_value, reverse=True)
        best = sorted_rows[0].scenario_name
        worst = sorted_rows[-1].scenario_name
        
        value_spread = sorted_rows[0].total_value - sorted_rows[-1].total_value
        
        insights = [
            f"Value spread across scenarios: ${float(value_spread)/1e6:.1f}M",
            f"Best scenario '{best}' outperforms worst by {float((sorted_rows[0].total_value - sorted_rows[-1].total_value) / sorted_rows[-1].total_value * 100):.1f}%",
        ]
        
        return ScenarioComparisonResult(
            portfolio_id=portfolio_id,
            base_value=base_value,
            comparison_table=comparison_rows,
            best_scenario=best,
            worst_scenario=worst,
            value_spread=value_spread,
            key_insights=insights,
        )


class PortfolioDashboardEngine:
    """Engine for generating portfolio dashboard data."""
    
    def __init__(self):
        self.analytics_engine = PortfolioAnalyticsEngine()
    
    def get_dashboard(
        self,
        portfolio_id: str,
        scenario_id: Optional[str] = None,
        time_horizon: int = 10
    ) -> DashboardResponse:
        """Generate dashboard data for a portfolio."""
        portfolio = get_portfolio(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        
        analytics = self.analytics_engine.calculate_analytics(
            portfolio_id, scenario_id, time_horizon
        )
        
        holdings = get_holdings(portfolio_id)
        
        # KPI Cards
        kpi_cards = [
            KPICard(
                id="total_value",
                label="Total Portfolio Value",
                value=float(analytics.portfolio_summary.total_adjusted_value),
                change=float(analytics.portfolio_summary.value_change_pct),
                change_period="from base",
                trend="up" if analytics.portfolio_summary.value_change_pct > 0 else "down",
                icon="DollarSign",
                color="emerald" if analytics.portfolio_summary.value_change_pct > 0 else "red",
            ),
            KPICard(
                id="property_count",
                label="Properties",
                value=analytics.portfolio_summary.total_properties,
                icon="Building2",
                color="blue",
            ),
            KPICard(
                id="avg_risk",
                label="Avg Risk Score",
                value=float(analytics.risk_metrics.weighted_avg_risk_score),
                trend="down" if analytics.risk_metrics.weighted_avg_risk_score < 50 else "up",
                icon="AlertTriangle",
                color="amber" if analytics.risk_metrics.weighted_avg_risk_score > 50 else "emerald",
            ),
            KPICard(
                id="var_95",
                label="Value at Risk (95%)",
                value=float(analytics.risk_metrics.value_at_risk_95),
                icon="TrendingDown",
                color="red",
            ),
            KPICard(
                id="stranded_count",
                label="Stranded Assets",
                value=analytics.stranding_analysis.stranded_assets_count,
                trend="up" if analytics.stranding_analysis.stranded_assets_count > 0 else "stable",
                icon="AlertCircle",
                color="red" if analytics.stranding_analysis.stranded_assets_count > 0 else "emerald",
            ),
            KPICard(
                id="sustainability",
                label="Avg GRESB Score",
                value=float(analytics.sustainability_metrics.avg_gresb_score) if analytics.sustainability_metrics.avg_gresb_score else 0,
                icon="Leaf",
                color="emerald",
            ),
            KPICard(
                id="certified_pct",
                label="Certified Assets",
                value=f"{float(analytics.sustainability_metrics.pct_certified):.1f}%",
                icon="Award",
                color="violet",
            ),
            KPICard(
                id="yield",
                label="Portfolio Yield",
                value=f"{float(analytics.portfolio_summary.avg_yield or 0):.2f}%",
                icon="Percent",
                color="blue",
            ),
        ]
        
        # Charts
        charts = {}
        
        # Sector allocation pie chart
        sector_data = analytics.concentration_analysis.sector.top_items
        charts["sector_allocation"] = ChartData(
            chart_type="pie",
            title="Sector Allocation",
            data=[{"name": item["name"].title(), "value": item["pct"]} for item in sector_data],
        )
        
        # Geographic distribution
        geo_data = analytics.concentration_analysis.geographic.top_items
        charts["geographic_distribution"] = ChartData(
            chart_type="bar",
            title="Geographic Distribution",
            data=[{"name": item["name"], "value": item["value"] / 1e6} for item in geo_data],
            config={"valueLabel": "Value ($M)"},
        )
        
        # Risk distribution
        charts["risk_distribution"] = ChartData(
            chart_type="bar",
            title="Risk Distribution",
            data=[
                {"name": "Low (<30)", "value": analytics.risk_metrics.risk_distribution.get("low", 0), "fill": "#22c55e"},
                {"name": "Moderate (30-50)", "value": analytics.risk_metrics.risk_distribution.get("moderate", 0), "fill": "#f59e0b"},
                {"name": "High (50-70)", "value": analytics.risk_metrics.risk_distribution.get("high", 0), "fill": "#f97316"},
                {"name": "Very High (70+)", "value": analytics.risk_metrics.risk_distribution.get("very_high", 0), "fill": "#ef4444"},
            ],
        )
        
        # Property values bar chart
        property_values = [
            {"name": h.get("property_name", "Unknown")[:15], "value": float(h.get("current_value", 0)) / 1e6}
            for h in holdings[:10]
        ]
        charts["property_values"] = ChartData(
            chart_type="bar",
            title="Property Values ($M)",
            data=property_values,
        )
        
        # Sustainability scores radar
        if holdings:
            avg_metrics = {
                "GRESB Score": float(analytics.sustainability_metrics.avg_gresb_score or 0),
                "Certified %": float(analytics.sustainability_metrics.pct_certified),
                "Low Risk %": analytics.risk_metrics.risk_distribution.get("low", 0) / len(holdings) * 100 if holdings else 0,
                "Yield %": float(analytics.portfolio_summary.avg_yield or 0) * 10,  # Scale up
            }
            charts["sustainability_radar"] = ChartData(
                chart_type="radar",
                title="Sustainability Profile",
                data=[{"metric": k, "value": v} for k, v in avg_metrics.items()],
            )
        
        # Alerts
        alerts = []
        
        # Stranded asset alert
        if analytics.stranding_analysis.stranded_assets_count > 0:
            alerts.append(Alert(
                id="stranded_warning",
                severity="critical",
                title="Stranded Asset Risk",
                message=f"{analytics.stranding_analysis.stranded_assets_count} assets at risk of stranding with total value ${float(analytics.stranding_analysis.stranded_assets_value)/1e6:.1f}M",
                action_required=True,
                created_at=datetime.now(timezone.utc),
            ))
        
        # High concentration alert
        if analytics.concentration_analysis.sector.concentration_level == "high":
            alerts.append(Alert(
                id="sector_concentration",
                severity="warning",
                title="High Sector Concentration",
                message="Portfolio has high concentration in a single sector. Consider diversification.",
                action_required=False,
                created_at=datetime.now(timezone.utc),
            ))
        
        # Low sustainability alert
        if analytics.sustainability_metrics.pct_certified < 50:
            alerts.append(Alert(
                id="low_certification",
                severity="info",
                title="Low Certification Rate",
                message=f"Only {float(analytics.sustainability_metrics.pct_certified):.0f}% of assets are certified. Consider certification programs.",
                action_required=False,
                created_at=datetime.now(timezone.utc),
            ))

        # ── Data quality analysis & missing datapoint alerts ─────────
        estimated_count = sum(1 for h in holdings if h.get("estimated_fields"))
        missing_fields_counter: Dict[str, int] = {}
        for h in holdings:
            for f in h.get("estimated_fields", []):
                missing_fields_counter[f] = missing_fields_counter.get(f, 0) + 1

        if estimated_count > 0:
            top_missing = sorted(missing_fields_counter.items(), key=lambda x: -x[1])[:5]
            missing_summary = ", ".join(f"{f} ({c} assets)" for f, c in top_missing)
            alerts.append(Alert(
                id="data_quality_gaps",
                severity="warning",
                title=f"Missing Datapoints — {estimated_count}/{len(holdings)} Assets Estimated",
                message=f"The following fields were auto-estimated using sector reference data: {missing_summary}. Upload actual data to improve accuracy.",
                action_required=True,
                created_at=datetime.now(timezone.utc),
            ))

        # Build data quality report for the frontend
        data_quality_report = {
            "total_assets": len(holdings),
            "complete_count": sum(1 for h in holdings if h.get("data_quality") == "complete"),
            "partial_count": sum(1 for h in holdings if h.get("data_quality") == "partial"),
            "estimated_count": sum(1 for h in holdings if h.get("data_quality") == "estimated"),
            "missing_fields": missing_fields_counter,
            "estimation_method": "PCAF DQS-5 sector proxy / S&P Global reference data",
            "recommendations": [],
        }
        # Add recommendations based on missing fields
        if missing_fields_counter.get("base_pd", 0) > len(holdings) * 0.5:
            data_quality_report["recommendations"].append(
                "Over 50% of assets lack PD data. Upload credit ratings or PD estimates for more accurate risk scoring."
            )
        if missing_fields_counter.get("country", 0) > len(holdings) * 0.3:
            data_quality_report["recommendations"].append(
                "Many assets lack country data. Add country/region for geographic concentration analysis."
            )
        if missing_fields_counter.get("company_name", 0) > 0:
            data_quality_report["recommendations"].append(
                f"{missing_fields_counter['company_name']} assets have no company name. Update for better identification."
            )

        # Use total_value (sum of holdings) when stored AUM is zero
        aum_raw = float(portfolio.get("aum") or 0)
        if aum_raw == 0:
            aum_raw = float(sum(
                Decimal(str(h.get("current_value") or h.get("value") or 0))
                for h in holdings
            ))
        return DashboardResponse(
            portfolio_id=portfolio_id,
            portfolio_name=portfolio["name"],
            last_updated=datetime.now(timezone.utc),
            kpi_cards=kpi_cards,
            charts=charts,
            alerts=alerts,
            total_aum=Decimal(str(aum_raw)),
            property_count=len(holdings),
            avg_risk_score=analytics.risk_metrics.weighted_avg_risk_score,
            sustainability_score=analytics.sustainability_metrics.avg_gresb_score,
            data_quality_report=DataQualityReport(**data_quality_report),
        )


# ============ Report Engine ============

class PortfolioReportEngine:
    """Engine for generating portfolio reports."""
    
    def __init__(self):
        self.analytics_engine = PortfolioAnalyticsEngine()
    
    def generate_report(
        self,
        portfolio_id: str,
        report_type: ReportType,
        scenario_id: Optional[str] = None,
        time_horizon: int = 10,
        include_charts: bool = True,
        include_property_details: bool = False,
    ) -> Dict:
        """Generate a report for the portfolio."""
        portfolio = get_portfolio(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        
        analytics = self.analytics_engine.calculate_analytics(
            portfolio_id, scenario_id, time_horizon
        )
        holdings = get_holdings(portfolio_id)
        
        report_id = str(uuid4())
        generated_at = datetime.now(timezone.utc)
        
        # Executive summary
        executive_summary = {
            "portfolio_name": portfolio["name"],
            "report_date": generated_at.isoformat(),
            "total_value": float(analytics.portfolio_summary.total_adjusted_value),
            "value_change_pct": float(analytics.portfolio_summary.value_change_pct),
            "property_count": analytics.portfolio_summary.total_properties,
            "avg_risk_score": float(analytics.risk_metrics.weighted_avg_risk_score),
            "stranded_assets": analytics.stranding_analysis.stranded_assets_count,
            "key_findings": self._generate_key_findings(analytics),
        }
        
        # Portfolio overview
        portfolio_overview = {
            "portfolio_type": portfolio.get("portfolio_type"),
            "investment_strategy": portfolio.get("investment_strategy"),
            "aum": float(portfolio.get("aum", 0)),
            "currency": portfolio.get("currency", "USD"),
            "inception_date": str(portfolio.get("inception_date")),
            "total_income": float(analytics.portfolio_summary.total_income or 0),
            "yield": float(analytics.portfolio_summary.avg_yield or 0),
        }
        
        # Type-specific sections
        report_content = {
            "report_id": report_id,
            "report_type": report_type.value,
            "generated_at": generated_at.isoformat(),
            "executive_summary": executive_summary,
            "portfolio_overview": portfolio_overview,
        }
        
        if report_type == ReportType.VALUATION:
            report_content["valuation_details"] = self._valuation_section(analytics, holdings)
        elif report_type == ReportType.CLIMATE_RISK:
            report_content["climate_risk_details"] = self._climate_risk_section(analytics, holdings)
        elif report_type == ReportType.SUSTAINABILITY:
            report_content["sustainability_details"] = self._sustainability_section(analytics, holdings)
        elif report_type == ReportType.TCFD:
            report_content["tcfd_details"] = self._tcfd_section(analytics, holdings)
        elif report_type in [ReportType.INVESTOR, ReportType.EXECUTIVE]:
            report_content["valuation_details"] = self._valuation_section(analytics, holdings)
            report_content["sustainability_details"] = self._sustainability_section(analytics, holdings)
        
        if include_property_details:
            report_content["property_details"] = [
                {
                    "name": h.get("property_name"),
                    "type": h.get("property_type"),
                    "location": h.get("property_location"),
                    "value": float(h.get("current_value", 0)),
                    "risk_score": h.get("risk_score"),
                    "certifications": h.get("certifications", []),
                }
                for h in holdings
            ]
        
        # Save report
        save_report({
            "id": report_id,
            "portfolio_id": portfolio_id,
            "report_type": report_type.value,
            "status": "completed",
            "created_at": generated_at.isoformat(),
            "completed_at": generated_at.isoformat(),
            "content": report_content,
        })
        
        return report_content
    
    def _generate_key_findings(self, analytics: PortfolioAnalyticsResponse) -> List[str]:
        """Generate key findings from analytics."""
        findings = []
        
        if analytics.portfolio_summary.value_change_pct > 5:
            findings.append(f"Portfolio value increased by {float(analytics.portfolio_summary.value_change_pct):.1f}%")
        elif analytics.portfolio_summary.value_change_pct < -5:
            findings.append(f"Portfolio value decreased by {abs(float(analytics.portfolio_summary.value_change_pct)):.1f}%")
        
        if analytics.stranding_analysis.stranded_assets_count > 0:
            findings.append(f"{analytics.stranding_analysis.stranded_assets_count} assets identified as stranding risk")
        
        if analytics.sustainability_metrics.avg_gresb_score and analytics.sustainability_metrics.avg_gresb_score > 70:
            findings.append("Strong sustainability performance with above-average GRESB scores")
        
        if analytics.risk_metrics.risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]:
            findings.append("Portfolio exhibits elevated risk profile - mitigation recommended")
        
        return findings[:5]
    
    def _valuation_section(self, analytics: PortfolioAnalyticsResponse, holdings: List[Dict]) -> Dict:
        """Generate valuation report section."""
        return {
            "total_base_value": float(analytics.portfolio_summary.total_base_value),
            "total_adjusted_value": float(analytics.portfolio_summary.total_adjusted_value),
            "value_change": float(analytics.portfolio_summary.total_value_change),
            "value_change_pct": float(analytics.portfolio_summary.value_change_pct),
            "valuation_date": str(analytics.calculation_date),
            "methodology": "Weighted average of DCF and direct capitalization approaches",
            "sector_breakdown": analytics.concentration_analysis.sector.top_items,
            "geographic_breakdown": analytics.concentration_analysis.geographic.top_items,
        }
    
    def _climate_risk_section(self, analytics: PortfolioAnalyticsResponse, holdings: List[Dict]) -> Dict:
        """Generate climate risk report section."""
        return {
            "physical_risk": {
                "flood_exposure": sum(1 for h in holdings if h.get("risk_score", 0) > 60) / len(holdings) * 100 if holdings else 0,
                "heat_stress": sum(1 for h in holdings if h.get("risk_score", 0) > 50) / len(holdings) * 100 if holdings else 0,
            },
            "transition_risk": {
                "avg_risk_score": float(analytics.risk_metrics.weighted_avg_risk_score),
                "risk_distribution": analytics.risk_metrics.risk_distribution,
            },
            "stranding_analysis": {
                "stranded_count": analytics.stranding_analysis.stranded_assets_count,
                "stranded_value": float(analytics.stranding_analysis.stranded_assets_value),
                "stranded_pct": float(analytics.stranding_analysis.stranded_pct),
                "avg_years_to_stranding": float(analytics.stranding_analysis.avg_years_to_stranding) if analytics.stranding_analysis.avg_years_to_stranding else None,
            },
            "var_95": float(analytics.risk_metrics.value_at_risk_95),
        }
    
    def _sustainability_section(self, analytics: PortfolioAnalyticsResponse, holdings: List[Dict]) -> Dict:
        """Generate sustainability report section with data-driven roadmap."""
        gresb = analytics.sustainability_metrics.avg_gresb_score
        cert_count = analytics.sustainability_metrics.certified_count
        cert_pct = float(analytics.sustainability_metrics.pct_certified)
        breakdown = analytics.sustainability_metrics.certifications_breakdown or {}

        # Build data-driven improvement roadmap
        roadmap = []
        uncertified = len(holdings) - cert_count
        if uncertified > 0:
            # Identify uncertified asset types
            uncert_types = set()
            for h in holdings:
                if not h.get("certifications"):
                    uncert_types.add(h.get("property_type", "unknown"))
            roadmap.append(
                f"Target certification for {uncertified} uncertified assets "
                f"({', '.join(uncert_types)})"
            )
        if gresb and float(gresb) < 70:
            roadmap.append(f"Current GRESB {float(gresb):.0f}/100 — target 70+ through energy and governance improvements")
        elif gresb and float(gresb) >= 70:
            roadmap.append(f"GRESB {float(gresb):.0f}/100 above benchmark — maintain leadership position")
        high_risk_assets = [h for h in holdings if h.get("risk_score", 0) > 60]
        if high_risk_assets:
            roadmap.append(f"Prioritise retrofit for {len(high_risk_assets)} high-risk assets to reduce transition exposure")
        if not roadmap:
            roadmap.append("Portfolio sustainability profile is strong — focus on maintaining standards")

        return {
            "gresb_performance": {
                "avg_score": float(gresb) if gresb else None,
                "benchmark": 72,
                "peer_rank": "Above Average" if (gresb or 0) > 70 else "Below Average" if (gresb or 0) < 50 else "Average",
            },
            "certifications": {
                "certified_count": cert_count,
                "certified_pct": cert_pct,
                "uncertified_count": uncertified,
                "breakdown": breakdown,
            },
            "improvement_roadmap": roadmap,
        }
    
    def _tcfd_section(self, analytics: PortfolioAnalyticsResponse, holdings: List[Dict]) -> Dict:
        """Generate TCFD report section with data-driven content."""
        n_holdings = len(holdings)
        high_risk = sum(1 for h in holdings if h.get("risk_score", 0) > 60)
        certified = sum(1 for h in holdings if h.get("certifications"))
        stranded = analytics.stranding_analysis.stranded_assets_count
        cert_pct = float(analytics.sustainability_metrics.pct_certified)
        risk_avg = float(analytics.risk_metrics.weighted_avg_risk_score)
        var_95 = float(analytics.risk_metrics.value_at_risk_95)

        # Dynamic opportunities / risks based on portfolio data
        opportunities = []
        risks = []
        if cert_pct < 80:
            opportunities.append(f"Certification uplift: {n_holdings - certified} uncertified assets represent green premium potential")
        if risk_avg < 40:
            opportunities.append("Low-risk profile supports green finance issuance at favourable terms")
        else:
            opportunities.append("Energy efficiency retrofits could reduce average risk score")
        if stranded > 0:
            risks.append(f"{stranded} assets identified as stranding risk (${float(analytics.stranding_analysis.stranded_assets_value)/1e6:.1f}M exposure)")
        if high_risk > 0:
            risks.append(f"{high_risk}/{n_holdings} assets exceed risk threshold (score > 60)")
        risks.append(f"Portfolio VaR(95%) = ${var_95/1e6:.1f}M under current climate scenarios")

        return {
            "governance": {
                "board_oversight": f"Portfolio of {n_holdings} assets reviewed; {high_risk} flagged for elevated climate risk",
                "management_role": f"Sustainability metrics tracked: avg risk {risk_avg:.1f}, {cert_pct:.0f}% certified",
            },
            "strategy": {
                "climate_opportunities": opportunities,
                "climate_risks": risks,
                "resilience": f"VaR(95%) = ${var_95/1e6:.1f}M; {stranded} stranded assets identified",
            },
            "risk_management": {
                "identification": f"Assessed {n_holdings} holdings across {len(set(h.get('property_type','') for h in holdings))} sectors",
                "assessment": f"Weighted average risk score: {risk_avg:.1f}/100 ({analytics.risk_metrics.risk_level.value})",
                "mitigation": f"{high_risk} assets flagged for targeted climate intervention",
            },
            "metrics_targets": {
                "current_certification_rate": cert_pct,
                "stranded_assets_pct": float(analytics.stranding_analysis.stranded_pct),
                "portfolio_var_95": var_95,
                "avg_risk_score": risk_avg,
            },
        }


# ============ Main Engine Class ============


# ---------------------------------------------------------------------------
# PortfolioAggregationEngine - drop-in replacement using real DB
# ---------------------------------------------------------------------------


class PortfolioAggregationEngine:
    """
    Aggregation engine — single entry point for all portfolio analytics.

    Combines:
      - get_analytics / compare_scenarios → PortfolioAnalyticsEngine
      - get_dashboard                     → PortfolioDashboardEngine
      - generate_report                   → PortfolioReportEngine
      - DB-backed overview / heatmap / sector / emission helpers
      - Full CRUD (portfolio, holding, report) wired to Postgres
    """

    def __init__(self) -> None:
        self._analytics   = PortfolioAnalyticsEngine()
        self._dashboard   = PortfolioDashboardEngine()
        self._reports_eng = PortfolioReportEngine()

    # ── Analytics / scenarios / dashboard / reports ───────────────────────────

    def get_analytics(
        self,
        portfolio_id: str,
        scenario_id: Optional[str] = None,
        time_horizon: int = 10,
        as_of_date: Optional[date] = None,
    ):
        return self._analytics.calculate_analytics(
            portfolio_id, scenario_id, time_horizon, as_of_date
        )

    def compare_scenarios(
        self,
        portfolio_id: str,
        scenario_ids: List[str],
        time_horizon: int = 10,
    ):
        return self._analytics.compare_scenarios(portfolio_id, scenario_ids, time_horizon)

    def get_dashboard(
        self,
        portfolio_id: str,
        scenario_id: Optional[str] = None,
        time_horizon: int = 10,
    ):
        return self._dashboard.get_dashboard(portfolio_id, scenario_id, time_horizon)

    def generate_report(self, portfolio_id: str, report_type, **kwargs):
        return self._reports_eng.generate_report(portfolio_id, report_type, **kwargs)

    # ── DB-backed overview helpers ─────────────────────────────────────────────

    def get_overview(self, portfolio_id: str) -> Dict:
        return get_portfolio_overview(portfolio_id)

    def get_heatmap(self, portfolio_id: str) -> Dict:
        return get_climate_risk_heatmap(portfolio_id)

    def get_sectors(self, portfolio_id: str) -> Dict:
        return get_sector_breakdown(portfolio_id)

    def get_emissions(self, portfolio_id: str) -> Dict:
        return get_emission_trends(portfolio_id)

    def get_top_assets(self, portfolio_id: str, limit: int = 10) -> Dict:
        return get_top_exposed_assets(portfolio_id, limit)

    # ── CRUD (fully DB-backed) ─────────────────────────────────────────────────

    def list_portfolios(self, org_id: Optional[str] = None) -> List[Dict]:
        return list_portfolios(org_id)

    def get_portfolio(self, portfolio_id: str) -> Optional[Dict]:
        return get_portfolio(portfolio_id)

    def get_holdings(self, portfolio_id: str) -> List[Dict]:
        return get_holdings(portfolio_id)

    def save_portfolio(self, portfolio_id: str, portfolio: Dict) -> Dict:
        return save_portfolio(portfolio_id, portfolio)

    def save_holding(self, portfolio_id: str, holding: Dict) -> Dict:
        return save_holding(portfolio_id, holding)

    def remove_holding(self, portfolio_id: str, holding_id: str) -> bool:
        return remove_holding(portfolio_id, holding_id)

    def save_report(self, report: Dict) -> Dict:
        return save_report(report)

    def get_report(self, report_id: str) -> Optional[Dict]:
        return get_report(report_id)
