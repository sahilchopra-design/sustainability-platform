"""
Data Hub Catalog API -- unified data source catalog, cross-source search,
entity 360-view, and coverage analytics.

Serves as the primary discovery and integration layer across all 8 ingested
data sources (GLEIF, Sanctions, Climate TRACE, OWID, NGFS, SBTi, SEC EDGAR,
yfinance).

Endpoints:
  GET  /data-hub-catalog/sources        -- data source catalog with live row counts
  GET  /data-hub-catalog/coverage       -- per-source coverage matrix
  GET  /data-hub-catalog/search         -- unified cross-source search by keyword
  GET  /data-hub-catalog/entity/{id}    -- entity 360-view by LEI, ticker, or name
  GET  /data-hub-catalog/freshness      -- last-sync timestamps per source
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, distinct, text, desc
from sqlalchemy.orm import Session

from db.base import get_db
from db.models.entity_resolution import EntityLei, EntitySanction
from db.models.emissions import ClimateTraceEmission, OwidCo2Energy
from db.models.scenario_ingest import NgfsScenarioData, SbtiCompany
from db.models.financial_ingest import SecEdgarFiling, YfinanceMarketData
from api.dependencies import require_min_role

router = APIRouter(prefix="/api/v1/data-hub-catalog", tags=["data-hub-catalog"])


# ── Source Catalog ──────────────────────────────────────────────────────────

_SOURCE_REGISTRY = [
    {
        "key": "gleif",
        "name": "GLEIF LEI Registry",
        "category": "Entity Resolution",
        "description": "Legal Entity Identifiers — ISO 17442 global company identification",
        "table": "entity_lei",
        "access": "REST API (GLEIF API v2)",
    },
    {
        "key": "sanctions",
        "name": "OpenSanctions Consolidated",
        "category": "Entity Resolution",
        "description": "Consolidated sanctions lists — OFAC SDN, EU FSL, UN Security Council",
        "table": "entity_sanctions",
        "access": "Bulk CSV/JSON",
    },
    {
        "key": "climate_trace",
        "name": "Climate TRACE",
        "category": "Emissions",
        "description": "Satellite-derived GHG emissions by facility and country",
        "table": "dh_climate_trace_emissions",
        "access": "REST API",
    },
    {
        "key": "owid",
        "name": "Our World in Data (OWID)",
        "category": "Emissions",
        "description": "Country-level CO2 emissions, energy mix, and climate indicators",
        "table": "dh_owid_co2_energy",
        "access": "GitHub CSV",
    },
    {
        "key": "ngfs",
        "name": "NGFS Scenario Explorer",
        "category": "Scenarios",
        "description": "IIASA NGFS Phase IV climate scenario time-series (carbon price, emissions, GDP)",
        "table": "dh_ngfs_scenario_data",
        "access": "REST API (IIASA)",
    },
    {
        "key": "sbti",
        "name": "SBTi Target Registry",
        "category": "Targets",
        "description": "Science Based Targets initiative — company net-zero commitments",
        "table": "dh_sbti_companies",
        "access": "Excel Download",
    },
    {
        "key": "sec_edgar",
        "name": "SEC EDGAR XBRL",
        "category": "Financial",
        "description": "SEC EDGAR filings — 10-K, 10-Q, 20-F with XBRL financial data",
        "table": "dh_sec_edgar_filings",
        "access": "REST API (SEC EDGAR)",
    },
    {
        "key": "yfinance",
        "name": "yfinance Market Data",
        "category": "Financial",
        "description": "Live market data, EVIC, and valuation multiples (yfinance/FMP)",
        "table": "dh_yfinance_market_data",
        "access": "Python Library",
    },
]

# Map source key to ORM model
_MODEL_MAP = {
    "gleif": EntityLei,
    "sanctions": EntitySanction,
    "climate_trace": ClimateTraceEmission,
    "owid": OwidCo2Energy,
    "ngfs": NgfsScenarioData,
    "sbti": SbtiCompany,
    "sec_edgar": SecEdgarFiling,
    "yfinance": YfinanceMarketData,
}


@router.get("/sources")
def list_catalog_sources(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Data source catalog with live row counts and freshness."""
    sources = []
    for src in _SOURCE_REGISTRY:
        model = _MODEL_MAP.get(src["key"])
        row_count = 0
        if model:
            try:
                row_count = db.query(func.count(
                    getattr(model, "id", None) or getattr(model, "lei", None)
                )).scalar() or 0
            except Exception:
                row_count = 0

        # Try to get last ingested_at timestamp
        last_sync = None
        if model and hasattr(model, "ingested_at"):
            try:
                ts = db.query(func.max(model.ingested_at)).scalar()
                last_sync = ts.isoformat() if ts else None
            except Exception:
                pass
        elif model and hasattr(model, "last_update_date"):
            try:
                ts = db.query(func.max(model.last_update_date)).scalar()
                last_sync = ts.isoformat() if ts else None
            except Exception:
                pass

        sources.append({
            **src,
            "row_count": row_count,
            "last_sync": last_sync,
        })

    return {"sources": sources, "total_sources": len(sources)}


@router.get("/coverage")
def get_coverage(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Per-source coverage matrix — row counts, distinct entities, and freshness."""
    coverage = {}

    # GLEIF
    coverage["gleif"] = {
        "records": db.query(func.count(EntityLei.lei)).scalar() or 0,
        "distinct_jurisdictions": db.query(func.count(distinct(EntityLei.jurisdiction))).scalar() or 0,
    }

    # Sanctions
    coverage["sanctions"] = {
        "records": db.query(func.count(EntitySanction.id)).scalar() or 0,
        "distinct_schema_types": db.query(func.count(distinct(EntitySanction.schema_type))).scalar() or 0,
    }

    # Climate TRACE
    coverage["climate_trace"] = {
        "records": db.query(func.count(ClimateTraceEmission.id)).scalar() or 0,
        "distinct_countries": db.query(func.count(distinct(ClimateTraceEmission.country_iso3))).scalar() or 0,
        "distinct_sectors": db.query(func.count(distinct(ClimateTraceEmission.sector))).scalar() or 0,
        "year_range": {
            "min": db.query(func.min(ClimateTraceEmission.year)).scalar(),
            "max": db.query(func.max(ClimateTraceEmission.year)).scalar(),
        },
    }

    # OWID
    coverage["owid"] = {
        "records": db.query(func.count(OwidCo2Energy.id)).scalar() or 0,
        "distinct_countries": db.query(func.count(distinct(OwidCo2Energy.country_iso3))).scalar() or 0,
        "year_range": {
            "min": db.query(func.min(OwidCo2Energy.year)).scalar(),
            "max": db.query(func.max(OwidCo2Energy.year)).scalar(),
        },
    }

    # NGFS
    coverage["ngfs"] = {
        "records": db.query(func.count(NgfsScenarioData.id)).scalar() or 0,
        "distinct_scenarios": db.query(func.count(distinct(NgfsScenarioData.scenario))).scalar() or 0,
        "distinct_variables": db.query(func.count(distinct(NgfsScenarioData.variable))).scalar() or 0,
        "distinct_models": db.query(func.count(distinct(NgfsScenarioData.model))).scalar() or 0,
        "year_range": {
            "min": db.query(func.min(NgfsScenarioData.year)).scalar(),
            "max": db.query(func.max(NgfsScenarioData.year)).scalar(),
        },
    }

    # SBTi
    coverage["sbti"] = {
        "records": db.query(func.count(SbtiCompany.id)).scalar() or 0,
        "distinct_sectors": db.query(func.count(distinct(SbtiCompany.sector))).scalar() or 0,
        "distinct_countries": db.query(func.count(distinct(SbtiCompany.country))).scalar() or 0,
    }

    # SEC EDGAR
    coverage["sec_edgar"] = {
        "records": db.query(func.count(SecEdgarFiling.id)).scalar() or 0,
        "distinct_companies": db.query(func.count(distinct(SecEdgarFiling.cik))).scalar() or 0,
        "distinct_tickers": db.query(func.count(distinct(SecEdgarFiling.ticker))).scalar() or 0,
        "filing_types": db.query(func.count(distinct(SecEdgarFiling.filing_type))).scalar() or 0,
    }

    # yfinance
    coverage["yfinance"] = {
        "records": db.query(func.count(YfinanceMarketData.id)).scalar() or 0,
        "distinct_tickers": db.query(func.count(distinct(YfinanceMarketData.ticker))).scalar() or 0,
        "distinct_sectors": db.query(func.count(distinct(YfinanceMarketData.sector))).scalar() or 0,
    }

    total_records = sum(v.get("records", 0) for v in coverage.values())
    return {"coverage": coverage, "total_records": total_records}


@router.get("/search")
def cross_source_search(
    q: str = Query(..., min_length=1, description="Search keyword (company, ticker, LEI, country)"),
    sources: Optional[str] = Query(None, description="Comma-separated source keys to search"),
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Unified cross-source search — returns results grouped by source."""
    source_filter = None
    if sources:
        source_filter = set(s.strip().lower() for s in sources.split(","))

    results = {}
    q_upper = q.upper()
    q_like = f"%{q}%"

    # GLEIF LEI search
    if not source_filter or "gleif" in source_filter:
        lei_q = db.query(EntityLei)
        if len(q) == 20 and q.isalnum():
            lei_q = lei_q.filter(EntityLei.lei == q_upper)
        else:
            lei_q = lei_q.filter(EntityLei.legal_name.ilike(q_like))
        lei_results = lei_q.limit(limit).all()
        if lei_results:
            results["gleif"] = [{
                "lei": r.lei,
                "legal_name": r.legal_name,
                "jurisdiction": r.jurisdiction,
                "status": r.status,
            } for r in lei_results]

    # Sanctions search
    if not source_filter or "sanctions" in source_filter:
        san_q = db.query(EntitySanction).filter(EntitySanction.caption.ilike(q_like))
        san_results = san_q.limit(limit).all()
        if san_results:
            results["sanctions"] = [{
                "id": r.id,
                "caption": r.caption,
                "schema_type": r.schema_type,
                "countries": r.countries,
                "sanction_programs": r.sanction_programs,
            } for r in san_results]

    # SEC EDGAR search
    if not source_filter or "sec_edgar" in source_filter:
        edgar_q = db.query(
            SecEdgarFiling.cik,
            SecEdgarFiling.ticker,
            SecEdgarFiling.company_name,
            func.count(SecEdgarFiling.id).label("filings"),
        ).group_by(SecEdgarFiling.cik, SecEdgarFiling.ticker, SecEdgarFiling.company_name)

        if len(q) <= 6 and q_upper.isalpha():
            edgar_q = edgar_q.filter(SecEdgarFiling.ticker == q_upper)
        else:
            edgar_q = edgar_q.filter(SecEdgarFiling.company_name.ilike(q_like))
        edgar_results = edgar_q.limit(limit).all()
        if edgar_results:
            results["sec_edgar"] = [{
                "cik": r[0], "ticker": r[1], "company_name": r[2], "filings": r[3],
            } for r in edgar_results]

    # yfinance search
    if not source_filter or "yfinance" in source_filter:
        yf_q = db.query(YfinanceMarketData)
        if len(q) <= 6 and q_upper.isalpha():
            yf_q = yf_q.filter(YfinanceMarketData.ticker == q_upper)
        else:
            yf_q = yf_q.filter(YfinanceMarketData.company_name.ilike(q_like))
        yf_results = yf_q.order_by(desc(YfinanceMarketData.market_cap)).limit(limit).all()
        if yf_results:
            results["yfinance"] = [{
                "ticker": r.ticker,
                "company_name": r.company_name,
                "sector": r.sector,
                "market_cap": r.market_cap,
                "evic": r.evic,
            } for r in yf_results]

    # SBTi search
    if not source_filter or "sbti" in source_filter:
        sbti_q = db.query(SbtiCompany).filter(SbtiCompany.company_name.ilike(q_like))
        sbti_results = sbti_q.limit(limit).all()
        if sbti_results:
            results["sbti"] = [{
                "id": r.id,
                "company_name": r.company_name,
                "sector": r.sector,
                "target_status": r.target_status,
                "near_term_target_year": r.near_term_target_year,
            } for r in sbti_results]

    # Climate TRACE search (by country name)
    if not source_filter or "climate_trace" in source_filter:
        ct_q = db.query(
            ClimateTraceEmission.country_iso3,
            ClimateTraceEmission.country_name,
            func.count(ClimateTraceEmission.id).label("records"),
        ).filter(
            ClimateTraceEmission.country_name.ilike(q_like)
        ).group_by(
            ClimateTraceEmission.country_iso3, ClimateTraceEmission.country_name
        ).limit(limit)
        ct_results = ct_q.all()
        if ct_results:
            results["climate_trace"] = [{
                "country_iso3": r[0], "country_name": r[1], "records": r[2],
            } for r in ct_results]

    # OWID search (by country)
    if not source_filter or "owid" in source_filter:
        owid_q = db.query(
            OwidCo2Energy.country_iso3,
            OwidCo2Energy.country_name,
            func.count(OwidCo2Energy.id).label("records"),
        ).filter(
            OwidCo2Energy.country_name.ilike(q_like)
        ).group_by(
            OwidCo2Energy.country_iso3, OwidCo2Energy.country_name
        ).limit(limit)
        owid_results = owid_q.all()
        if owid_results:
            results["owid"] = [{
                "country_iso3": r[0], "country_name": r[1], "records": r[2],
            } for r in owid_results]

    total_hits = sum(len(v) for v in results.values())
    return {
        "query": q,
        "total_hits": total_hits,
        "sources_matched": list(results.keys()),
        "results": results,
    }


@router.get("/entity/{identifier}")
def entity_360_view(
    identifier: str,
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """
    Entity 360-degree view — given a LEI, ticker, or company name,
    pull data from all relevant sources.
    """
    data = {"identifier": identifier, "sources": {}}
    is_lei = len(identifier) == 20 and identifier.isalnum()
    is_ticker = len(identifier) <= 8 and "." not in identifier and identifier.upper().isalpha()
    name_like = f"%{identifier}%"

    # 1. GLEIF LEI
    if is_lei:
        lei_rec = db.query(EntityLei).filter(EntityLei.lei == identifier.upper()).first()
    else:
        lei_rec = db.query(EntityLei).filter(
            EntityLei.legal_name.ilike(name_like)
        ).first()
    if lei_rec:
        data["sources"]["gleif"] = {
            "lei": lei_rec.lei,
            "legal_name": lei_rec.legal_name,
            "jurisdiction": lei_rec.jurisdiction,
            "status": lei_rec.status,
            "entity_category": lei_rec.entity_category,
            "direct_parent_lei": lei_rec.direct_parent_lei,
            "ultimate_parent_lei": lei_rec.ultimate_parent_lei,
        }
        data["resolved_name"] = lei_rec.legal_name

    # 2. Sanctions screening
    san_q = db.query(EntitySanction)
    if is_lei:
        san_q = san_q.filter(EntitySanction.lei == identifier.upper())
    else:
        company = data.get("resolved_name") or identifier
        san_q = san_q.filter(EntitySanction.caption.ilike(f"%{company}%"))
    san_results = san_q.limit(5).all()
    if san_results:
        data["sources"]["sanctions"] = [{
            "id": r.id,
            "caption": r.caption,
            "schema_type": r.schema_type,
            "sanction_programs": r.sanction_programs,
            "match_type": "potential",
        } for r in san_results]

    # 3. SEC EDGAR filings
    ticker_val = identifier.upper() if is_ticker else None
    edgar_q = db.query(SecEdgarFiling)
    if ticker_val:
        edgar_q = edgar_q.filter(SecEdgarFiling.ticker == ticker_val)
    else:
        name = data.get("resolved_name") or identifier
        edgar_q = edgar_q.filter(SecEdgarFiling.company_name.ilike(f"%{name}%"))
    edgar_recs = edgar_q.order_by(desc(SecEdgarFiling.fiscal_year)).limit(5).all()
    if edgar_recs:
        data["sources"]["sec_edgar"] = {
            "company_name": edgar_recs[0].company_name,
            "cik": edgar_recs[0].cik,
            "ticker": edgar_recs[0].ticker,
            "filings_shown": len(edgar_recs),
            "latest": [{
                "filing_type": r.filing_type,
                "fiscal_year": r.fiscal_year,
                "revenue": r.revenue,
                "net_income": r.net_income,
                "total_assets": r.total_assets,
            } for r in edgar_recs],
        }
        if not data.get("resolved_name"):
            data["resolved_name"] = edgar_recs[0].company_name
        if not ticker_val:
            ticker_val = edgar_recs[0].ticker

    # 4. yfinance market data
    yf_q = db.query(YfinanceMarketData)
    if ticker_val:
        yf_q = yf_q.filter(YfinanceMarketData.ticker == ticker_val)
    else:
        name = data.get("resolved_name") or identifier
        yf_q = yf_q.filter(YfinanceMarketData.company_name.ilike(f"%{name}%"))
    yf_rec = yf_q.order_by(desc(YfinanceMarketData.as_of_date)).first()
    if yf_rec:
        data["sources"]["yfinance"] = {
            "ticker": yf_rec.ticker,
            "company_name": yf_rec.company_name,
            "sector": yf_rec.sector,
            "industry": yf_rec.industry,
            "country": yf_rec.country,
            "market_cap": yf_rec.market_cap,
            "enterprise_value": yf_rec.enterprise_value,
            "evic": yf_rec.evic,
            "share_price": yf_rec.share_price,
            "pe_ratio": yf_rec.pe_ratio,
            "beta": yf_rec.beta,
            "esg_score": yf_rec.esg_score,
            "as_of_date": yf_rec.as_of_date.isoformat() if yf_rec.as_of_date else None,
        }
        if not data.get("resolved_name"):
            data["resolved_name"] = yf_rec.company_name

    # 5. SBTi targets
    sbti_q = db.query(SbtiCompany)
    name = data.get("resolved_name") or identifier
    sbti_q = sbti_q.filter(SbtiCompany.company_name.ilike(f"%{name}%"))
    sbti_recs = sbti_q.limit(3).all()
    if sbti_recs:
        data["sources"]["sbti"] = [{
            "company_name": r.company_name,
            "sector": r.sector,
            "target_status": r.target_status,
            "near_term_target_year": r.near_term_target_year,
            "long_term_target_year": r.long_term_target_year,
            "net_zero_committed": r.net_zero_committed,
        } for r in sbti_recs]

    data["sources_found"] = list(data["sources"].keys())
    data["source_count"] = len(data["sources"])

    return data


@router.get("/freshness")
def get_freshness(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Last-sync timestamps and row counts per source."""
    freshness = {}
    for src in _SOURCE_REGISTRY:
        model = _MODEL_MAP.get(src["key"])
        if not model:
            continue
        entry = {"source": src["name"], "key": src["key"]}
        try:
            pk = getattr(model, "id", None) or getattr(model, "lei", None)
            entry["row_count"] = db.query(func.count(pk)).scalar() or 0
        except Exception:
            entry["row_count"] = 0
        if hasattr(model, "ingested_at"):
            try:
                ts = db.query(func.max(model.ingested_at)).scalar()
                entry["last_ingested"] = ts.isoformat() if ts else None
            except Exception:
                entry["last_ingested"] = None
        freshness[src["key"]] = entry

    return {"freshness": freshness}
