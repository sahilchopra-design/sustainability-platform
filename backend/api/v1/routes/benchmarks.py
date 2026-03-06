"""
Benchmarks API -- sector-level WACI and financial benchmarks.

Endpoints:
  GET  /benchmarks/sector/{sector}     -- sector benchmark (WACI, financials)
  GET  /benchmarks/sectors             -- all sector benchmarks summary
  GET  /benchmarks/waci                -- WACI calculation for a set of tickers
  GET  /benchmarks/stats               -- benchmark data stats

Consumed by data_hub_client.get_sector_benchmark(sector).
Aggregates from yfinance market data + Climate TRACE emissions.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, distinct, case
from sqlalchemy.orm import Session

from db.base import get_db
from db.models.financial_ingest import SecEdgarFiling, YfinanceMarketData
from db.models.emissions import ClimateTraceEmission
from db.models.scenario_ingest import SbtiCompany
from api.dependencies import require_min_role

router = APIRouter(prefix="/api/v1/benchmarks", tags=["benchmarks"])


@router.get("/sector/{sector}")
def get_sector_benchmark(
    sector: str,
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """
    Sector-level benchmark including WACI proxy, financial metrics,
    and target-setting coverage.

    Aggregates from yfinance (market cap, financials) and SBTi (targets).
    """
    # Market data aggregation by sector
    market_q = db.query(
        func.count(YfinanceMarketData.id).label("companies"),
        func.sum(YfinanceMarketData.market_cap).label("total_market_cap"),
        func.avg(YfinanceMarketData.market_cap).label("avg_market_cap"),
        func.avg(YfinanceMarketData.pe_ratio).label("avg_pe"),
        func.avg(YfinanceMarketData.pb_ratio).label("avg_pb"),
        func.avg(YfinanceMarketData.ev_to_ebitda).label("avg_ev_ebitda"),
        func.avg(YfinanceMarketData.dividend_yield).label("avg_div_yield"),
        func.avg(YfinanceMarketData.beta).label("avg_beta"),
        func.avg(YfinanceMarketData.esg_score).label("avg_esg_score"),
        func.sum(YfinanceMarketData.evic).label("total_evic"),
    ).filter(
        YfinanceMarketData.sector.ilike(f"%{sector}%")
    )
    market_row = market_q.first()

    companies = market_row[0] if market_row else 0
    if companies == 0:
        return {
            "sector": sector,
            "companies": 0,
            "message": f"No market data found for sector '{sector}'",
            "available_sectors": _get_available_sectors(db),
        }

    # Revenue and emissions from EDGAR for WACI proxy
    total_revenue = 0.0
    total_evic = float(market_row[9]) if market_row[9] else 0.0

    # Get tickers in sector
    tickers = [r[0] for r in db.query(
        distinct(YfinanceMarketData.ticker)
    ).filter(YfinanceMarketData.sector.ilike(f"%{sector}%")).all()]

    # Sum latest annual revenue from EDGAR 10-K filings
    if tickers:
        for ticker in tickers:
            latest = db.query(SecEdgarFiling).filter(
                SecEdgarFiling.ticker == ticker,
                SecEdgarFiling.filing_type == "10-K",
            ).order_by(SecEdgarFiling.fiscal_year.desc()).first()
            if latest and latest.revenue:
                total_revenue += float(latest.revenue)

    # SBTi target coverage
    sbti_in_sector = db.query(func.count(SbtiCompany.id)).filter(
        SbtiCompany.sector.ilike(f"%{sector}%")
    ).scalar() or 0

    sbti_committed = db.query(func.count(SbtiCompany.id)).filter(
        SbtiCompany.sector.ilike(f"%{sector}%"),
        SbtiCompany.net_zero_committed == True,
    ).scalar() or 0

    return {
        "sector": sector,
        "companies": companies,
        "total_market_cap": float(market_row[1]) if market_row[1] else 0,
        "avg_market_cap": round(float(market_row[2]), 0) if market_row[2] else None,
        "total_evic": total_evic,
        "total_revenue": total_revenue,
        "financial_metrics": {
            "avg_pe": round(float(market_row[3]), 2) if market_row[3] else None,
            "avg_pb": round(float(market_row[4]), 2) if market_row[4] else None,
            "avg_ev_ebitda": round(float(market_row[5]), 2) if market_row[5] else None,
            "avg_dividend_yield": round(float(market_row[6]), 4) if market_row[6] else None,
            "avg_beta": round(float(market_row[7]), 2) if market_row[7] else None,
            "avg_esg_score": round(float(market_row[8]), 1) if market_row[8] else None,
        },
        "sbti_coverage": {
            "companies_with_targets": sbti_in_sector,
            "net_zero_committed": sbti_committed,
            "target_coverage_pct": round(sbti_in_sector / companies * 100, 1) if companies else 0,
        },
        "tickers": tickers,
    }


@router.get("/sectors")
def list_sector_benchmarks(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """All sector benchmarks summary."""
    rows = db.query(
        YfinanceMarketData.sector,
        func.count(YfinanceMarketData.id).label("companies"),
        func.sum(YfinanceMarketData.market_cap).label("total_market_cap"),
        func.avg(YfinanceMarketData.pe_ratio).label("avg_pe"),
        func.avg(YfinanceMarketData.pb_ratio).label("avg_pb"),
        func.avg(YfinanceMarketData.beta).label("avg_beta"),
        func.avg(YfinanceMarketData.esg_score).label("avg_esg_score"),
        func.sum(YfinanceMarketData.evic).label("total_evic"),
    ).filter(
        YfinanceMarketData.sector.isnot(None)
    ).group_by(
        YfinanceMarketData.sector
    ).order_by(
        func.sum(YfinanceMarketData.market_cap).desc()
    ).all()

    sectors = []
    for r in rows:
        sectors.append({
            "sector": r[0],
            "companies": r[1],
            "total_market_cap": float(r[2]) if r[2] else 0,
            "avg_pe": round(float(r[3]), 2) if r[3] else None,
            "avg_pb": round(float(r[4]), 2) if r[4] else None,
            "avg_beta": round(float(r[5]), 2) if r[5] else None,
            "avg_esg_score": round(float(r[6]), 1) if r[6] else None,
            "total_evic": float(r[7]) if r[7] else 0,
        })

    return {
        "sectors": sectors,
        "total_sectors": len(sectors),
    }


@router.get("/waci")
def calculate_waci(
    tickers: str = Query(..., description="Comma-separated tickers"),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """
    Weighted Average Carbon Intensity (WACI) proxy calculation.

    WACI = Sum( (portfolio_weight_i * emissions_i) / revenue_i )

    Uses EVIC as portfolio weight proxy and EDGAR revenue data.
    """
    ticker_list = [t.strip().upper() for t in tickers.split(",")]
    results = []

    total_evic = 0.0
    weighted_intensity_sum = 0.0

    for ticker in ticker_list:
        # Get market data
        yf = db.query(YfinanceMarketData).filter(
            YfinanceMarketData.ticker == ticker
        ).order_by(YfinanceMarketData.as_of_date.desc()).first()

        # Get latest 10-K revenue
        edgar = db.query(SecEdgarFiling).filter(
            SecEdgarFiling.ticker == ticker,
            SecEdgarFiling.filing_type == "10-K",
        ).order_by(SecEdgarFiling.fiscal_year.desc()).first()

        evic = float(yf.evic) if yf and yf.evic else None
        revenue = float(edgar.revenue) if edgar and edgar.revenue else None
        market_cap = float(yf.market_cap) if yf and yf.market_cap else None

        entry = {
            "ticker": ticker,
            "company_name": (yf.company_name if yf else None) or (edgar.company_name if edgar else None),
            "evic": evic,
            "market_cap": market_cap,
            "revenue": revenue,
            "sector": yf.sector if yf else None,
        }

        if evic:
            total_evic += evic

        results.append(entry)

    # Calculate weights and WACI proxy
    for entry in results:
        evic = entry.get("evic")
        revenue = entry.get("revenue")
        if total_evic and evic:
            entry["weight"] = round(evic / total_evic, 4)
        else:
            entry["weight"] = None
        # Carbon intensity proxy = placeholder until emissions data linked
        entry["carbon_intensity_proxy"] = None

    return {
        "tickers": ticker_list,
        "total_evic": total_evic,
        "companies": results,
        "note": "WACI calculation requires emissions data linkage (pending A17 integration)",
    }


@router.get("/stats")
def benchmark_stats(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Summary statistics for benchmark data availability."""
    sectors = db.query(func.count(distinct(YfinanceMarketData.sector))).filter(
        YfinanceMarketData.sector.isnot(None)
    ).scalar() or 0

    companies = db.query(func.count(YfinanceMarketData.id)).scalar() or 0

    edgar_companies = db.query(func.count(distinct(SecEdgarFiling.ticker))).scalar() or 0

    sbti_total = db.query(func.count(SbtiCompany.id)).scalar() or 0

    return {
        "market_data": {
            "sectors": sectors,
            "companies": companies,
        },
        "edgar": {
            "companies_with_filings": edgar_companies,
        },
        "sbti": {
            "companies_with_targets": sbti_total,
        },
    }


def _get_available_sectors(db: Session):
    """Helper: return list of sectors with data."""
    rows = db.query(
        distinct(YfinanceMarketData.sector)
    ).filter(YfinanceMarketData.sector.isnot(None)).all()
    return sorted([r[0] for r in rows])
