"""
Financial Data API routes -- SEC EDGAR filings + yfinance market data.

Endpoints:
  GET  /financial-data/edgar               -- search SEC EDGAR filings
  GET  /financial-data/edgar/companies     -- list companies with filing counts
  GET  /financial-data/edgar/filing-types  -- list filing types with counts
  GET  /financial-data/edgar/compare       -- compare companies on a metric
  GET  /financial-data/market              -- search market data snapshots
  GET  /financial-data/market/tickers      -- list tickers with latest data
  GET  /financial-data/market/sectors      -- sector breakdown with avg metrics
  GET  /financial-data/market/evic         -- EVIC data for PCAF calculations
  GET  /financial-data/stats               -- combined stats (EDGAR + yfinance)
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, distinct, case, desc
from sqlalchemy.orm import Session

from db.base import get_db
from db.models.financial_ingest import SecEdgarFiling, YfinanceMarketData
from api.dependencies import require_min_role

router = APIRouter(prefix="/api/v1/financial-data", tags=["financial-data"])


# -- EDGAR endpoints ----------------------------------------------------------

@router.get("/edgar")
def search_edgar(
    company: Optional[str] = Query(None, description="Company name partial match"),
    ticker: Optional[str] = Query(None),
    cik: Optional[str] = Query(None),
    filing_type: Optional[str] = Query(None, description="10-K, 10-Q, 20-F"),
    sic_code: Optional[str] = Query(None),
    fiscal_year_min: Optional[int] = Query(None),
    fiscal_year_max: Optional[int] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Search SEC EDGAR filings with filters."""
    q = db.query(SecEdgarFiling)

    if company:
        q = q.filter(SecEdgarFiling.company_name.ilike(f"%{company}%"))
    if ticker:
        q = q.filter(SecEdgarFiling.ticker == ticker.upper())
    if cik:
        q = q.filter(SecEdgarFiling.cik == cik)
    if filing_type:
        q = q.filter(SecEdgarFiling.filing_type == filing_type)
    if sic_code:
        q = q.filter(SecEdgarFiling.sic_code == sic_code)
    if fiscal_year_min:
        q = q.filter(SecEdgarFiling.fiscal_year >= fiscal_year_min)
    if fiscal_year_max:
        q = q.filter(SecEdgarFiling.fiscal_year <= fiscal_year_max)

    total = q.count()
    records = (
        q.order_by(SecEdgarFiling.company_name, desc(SecEdgarFiling.fiscal_year))
        .offset(offset).limit(limit).all()
    )

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "records": [_edgar_to_dict(r) for r in records],
    }


@router.get("/edgar/companies")
def edgar_companies(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """List companies with filing counts."""
    rows = (
        db.query(
            SecEdgarFiling.cik,
            SecEdgarFiling.ticker,
            SecEdgarFiling.company_name,
            func.count(SecEdgarFiling.id).label("filings"),
            func.min(SecEdgarFiling.fiscal_year).label("year_min"),
            func.max(SecEdgarFiling.fiscal_year).label("year_max"),
        )
        .group_by(SecEdgarFiling.cik, SecEdgarFiling.ticker, SecEdgarFiling.company_name)
        .order_by(SecEdgarFiling.company_name)
        .all()
    )
    return {
        "companies": [
            {
                "cik": r[0], "ticker": r[1], "company_name": r[2],
                "filings": r[3], "year_min": r[4], "year_max": r[5],
            }
            for r in rows
        ]
    }


@router.get("/edgar/filing-types")
def edgar_filing_types(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """List filing types with counts."""
    rows = (
        db.query(
            SecEdgarFiling.filing_type,
            func.count(SecEdgarFiling.id).label("count"),
        )
        .group_by(SecEdgarFiling.filing_type)
        .order_by(func.count(SecEdgarFiling.id).desc())
        .all()
    )
    return {"filing_types": [{"type": r[0], "count": r[1]} for r in rows]}


@router.get("/edgar/compare")
def edgar_compare(
    metric: str = Query(..., description="revenue, net_income, total_assets, etc."),
    tickers: str = Query(..., description="Comma-separated tickers"),
    filing_type: str = Query("10-K"),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Compare companies on a financial metric over time."""
    ticker_list = [t.strip().upper() for t in tickers.split(",")]

    # Validate metric
    valid_metrics = {
        "revenue", "net_income", "total_assets", "total_equity",
        "total_liabilities", "ebitda", "operating_income",
        "cash_and_equivalents", "total_debt", "free_cash_flow",
        "eps_diluted", "roe", "roa", "debt_to_equity",
        "shares_outstanding", "operating_cash_flow",
    }
    if metric not in valid_metrics:
        raise HTTPException(400, f"Invalid metric '{metric}'. Valid: {sorted(valid_metrics)}")

    q = (
        db.query(SecEdgarFiling)
        .filter(SecEdgarFiling.ticker.in_(ticker_list))
        .filter(SecEdgarFiling.filing_type == filing_type)
        .order_by(SecEdgarFiling.ticker, SecEdgarFiling.fiscal_year)
    )
    records = q.all()

    # Group by ticker
    by_ticker = {}
    for r in records:
        if r.ticker not in by_ticker:
            by_ticker[r.ticker] = {"ticker": r.ticker, "company_name": r.company_name, "data": []}
        by_ticker[r.ticker]["data"].append({
            "fiscal_year": r.fiscal_year,
            "value": getattr(r, metric, None),
        })

    return {
        "metric": metric,
        "filing_type": filing_type,
        "companies": list(by_ticker.values()),
    }


# -- Market data endpoints ----------------------------------------------------

@router.get("/market")
def search_market(
    ticker: Optional[str] = Query(None),
    company: Optional[str] = Query(None),
    sector: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    exchange: Optional[str] = Query(None),
    min_market_cap: Optional[float] = Query(None, description="Minimum market cap"),
    limit: int = Query(50, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Search market data snapshots."""
    q = db.query(YfinanceMarketData)

    if ticker:
        q = q.filter(YfinanceMarketData.ticker == ticker.upper())
    if company:
        q = q.filter(YfinanceMarketData.company_name.ilike(f"%{company}%"))
    if sector:
        q = q.filter(YfinanceMarketData.sector.ilike(f"%{sector}%"))
    if country:
        q = q.filter(YfinanceMarketData.country.ilike(f"%{country}%"))
    if exchange:
        q = q.filter(YfinanceMarketData.exchange.ilike(f"%{exchange}%"))
    if min_market_cap:
        q = q.filter(YfinanceMarketData.market_cap >= min_market_cap)

    total = q.count()
    records = (
        q.order_by(desc(YfinanceMarketData.market_cap))
        .offset(offset).limit(limit).all()
    )

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "records": [_market_to_dict(r) for r in records],
    }


@router.get("/market/tickers")
def market_tickers(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """List tickers with latest market data."""
    rows = (
        db.query(
            YfinanceMarketData.ticker,
            YfinanceMarketData.company_name,
            YfinanceMarketData.sector,
            YfinanceMarketData.market_cap,
            YfinanceMarketData.share_price,
            YfinanceMarketData.evic,
            YfinanceMarketData.as_of_date,
        )
        .order_by(desc(YfinanceMarketData.market_cap))
        .all()
    )
    return {
        "tickers": [
            {
                "ticker": r[0], "company_name": r[1], "sector": r[2],
                "market_cap": r[3], "share_price": r[4], "evic": r[5],
                "as_of_date": r[6].isoformat() if r[6] else None,
            }
            for r in rows
        ]
    }


@router.get("/market/sectors")
def market_sectors(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Sector breakdown with aggregate metrics."""
    rows = (
        db.query(
            YfinanceMarketData.sector,
            func.count(YfinanceMarketData.id).label("companies"),
            func.sum(YfinanceMarketData.market_cap).label("total_market_cap"),
            func.avg(YfinanceMarketData.pe_ratio).label("avg_pe"),
            func.avg(YfinanceMarketData.pb_ratio).label("avg_pb"),
            func.avg(YfinanceMarketData.dividend_yield).label("avg_div_yield"),
            func.avg(YfinanceMarketData.beta).label("avg_beta"),
        )
        .filter(YfinanceMarketData.sector.isnot(None))
        .group_by(YfinanceMarketData.sector)
        .order_by(func.sum(YfinanceMarketData.market_cap).desc())
        .all()
    )
    return {
        "sectors": [
            {
                "sector": r[0], "companies": r[1],
                "total_market_cap": float(r[2]) if r[2] else 0,
                "avg_pe": round(float(r[3]), 2) if r[3] else None,
                "avg_pb": round(float(r[4]), 2) if r[4] else None,
                "avg_dividend_yield": round(float(r[5]), 4) if r[5] else None,
                "avg_beta": round(float(r[6]), 2) if r[6] else None,
            }
            for r in rows
        ]
    }


@router.get("/market/evic")
def market_evic(
    ticker: Optional[str] = Query(None, description="Filter by ticker"),
    min_evic: Optional[float] = Query(None),
    limit: int = Query(50, le=500),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """EVIC data for PCAF financed emissions calculations."""
    q = db.query(YfinanceMarketData).filter(YfinanceMarketData.evic.isnot(None))

    if ticker:
        q = q.filter(YfinanceMarketData.ticker == ticker.upper())
    if min_evic:
        q = q.filter(YfinanceMarketData.evic >= min_evic)

    records = (
        q.order_by(desc(YfinanceMarketData.evic))
        .limit(limit).all()
    )

    return {
        "total": len(records),
        "records": [
            {
                "ticker": r.ticker,
                "company_name": r.company_name,
                "as_of_date": r.as_of_date.isoformat() if r.as_of_date else None,
                "market_cap": r.market_cap,
                "total_debt": r.total_debt,
                "cash_and_equivalents": r.cash_and_equivalents,
                "enterprise_value": r.enterprise_value,
                "evic": r.evic,
                "shares_outstanding": r.shares_outstanding,
                "currency": r.currency,
            }
            for r in records
        ],
    }


# -- Combined stats -----------------------------------------------------------

@router.get("/stats")
def combined_stats(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Combined statistics for SEC EDGAR and yfinance market data."""
    edgar_count = db.query(func.count(SecEdgarFiling.id)).scalar() or 0
    edgar_companies = db.query(func.count(distinct(SecEdgarFiling.cik))).scalar() or 0
    edgar_types = db.query(func.count(distinct(SecEdgarFiling.filing_type))).scalar() or 0

    market_count = db.query(func.count(YfinanceMarketData.id)).scalar() or 0
    market_tickers = db.query(func.count(distinct(YfinanceMarketData.ticker))).scalar() or 0
    market_sectors = db.query(func.count(distinct(YfinanceMarketData.sector))).scalar() or 0

    return {
        "edgar": {
            "filings": edgar_count,
            "companies": edgar_companies,
            "filing_types": edgar_types,
        },
        "market": {
            "snapshots": market_count,
            "tickers": market_tickers,
            "sectors": market_sectors,
        },
    }


# -- Helpers ------------------------------------------------------------------

def _edgar_to_dict(r: SecEdgarFiling) -> dict:
    return {
        "id": r.id,
        "cik": r.cik,
        "ticker": r.ticker,
        "company_name": r.company_name,
        "entity_type": r.entity_type,
        "sic_code": r.sic_code,
        "filing_type": r.filing_type,
        "filing_date": r.filing_date.isoformat() if r.filing_date else None,
        "period_end": r.period_end.isoformat() if r.period_end else None,
        "fiscal_year": r.fiscal_year,
        "fiscal_quarter": r.fiscal_quarter,
        "revenue": r.revenue,
        "net_income": r.net_income,
        "ebitda": r.ebitda,
        "total_assets": r.total_assets,
        "total_equity": r.total_equity,
        "total_debt": r.total_debt,
        "free_cash_flow": r.free_cash_flow,
        "eps_diluted": r.eps_diluted,
        "debt_to_equity": r.debt_to_equity,
        "roe": r.roe,
        "roa": r.roa,
        "shares_outstanding": r.shares_outstanding,
        "currency": r.currency,
        "ingested_at": r.ingested_at.isoformat() if r.ingested_at else None,
    }


def _market_to_dict(r: YfinanceMarketData) -> dict:
    return {
        "id": r.id,
        "ticker": r.ticker,
        "company_name": r.company_name,
        "exchange": r.exchange,
        "currency": r.currency,
        "sector": r.sector,
        "industry": r.industry,
        "country": r.country,
        "as_of_date": r.as_of_date.isoformat() if r.as_of_date else None,
        "market_cap": r.market_cap,
        "share_price": r.share_price,
        "enterprise_value": r.enterprise_value,
        "evic": r.evic,
        "pe_ratio": r.pe_ratio,
        "pb_ratio": r.pb_ratio,
        "ev_to_ebitda": r.ev_to_ebitda,
        "dividend_yield": r.dividend_yield,
        "revenue_ttm": r.revenue_ttm,
        "ebitda_ttm": r.ebitda_ttm,
        "net_income_ttm": r.net_income_ttm,
        "beta": r.beta,
        "data_provider": r.data_provider,
        "ingested_at": r.ingested_at.isoformat() if r.ingested_at else None,
    }
