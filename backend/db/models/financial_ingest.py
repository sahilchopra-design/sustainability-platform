"""
ORM models for ingested financial data:
  - SecEdgarFiling      -> dh_sec_edgar_filings    (SEC EDGAR XBRL 10-K/10-Q)
  - YfinanceMarketData  -> dh_yfinance_market_data  (yfinance / FMP equity + EVIC)
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Float, Index, Integer,
    String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB

from db.base import Base


class SecEdgarFiling(Base):
    """
    SEC EDGAR XBRL financial statement data.

    Each row is one (CIK, filing_type, period_end) filing with extracted
    income statement, balance sheet, and cash flow line items.
    """
    __tablename__ = "dh_sec_edgar_filings"

    id                  = Column(Text, primary_key=True)
    source_id           = Column(Text)
    cik                 = Column(Text, nullable=False)
    ticker              = Column(Text)
    company_name        = Column(Text, nullable=False)
    entity_type         = Column(Text)
    sic_code            = Column(Text)
    sic_description     = Column(Text)
    filing_type         = Column(Text, nullable=False)  # 10-K, 10-Q, 20-F
    filing_date         = Column(Date)
    period_end          = Column(Date)
    fiscal_year         = Column(Integer)
    fiscal_quarter      = Column(Integer)
    # Income Statement
    revenue             = Column(Float)
    cost_of_revenue     = Column(Float)
    gross_profit        = Column(Float)
    operating_income    = Column(Float)
    net_income          = Column(Float)
    ebitda              = Column(Float)
    eps_basic           = Column(Float)
    eps_diluted         = Column(Float)
    # Balance Sheet
    total_assets        = Column(Float)
    total_liabilities   = Column(Float)
    total_equity        = Column(Float)
    cash_and_equivalents = Column(Float)
    total_debt          = Column(Float)
    net_debt            = Column(Float)
    # Cash Flow
    operating_cash_flow = Column(Float)
    capex               = Column(Float)
    free_cash_flow      = Column(Float)
    dividends_paid      = Column(Float)
    # Key Ratios
    debt_to_equity      = Column(Float)
    current_ratio       = Column(Float)
    roe                 = Column(Float)
    roa                 = Column(Float)
    # Climate relevant
    shares_outstanding  = Column(Float)
    # Metadata
    currency            = Column(Text, default="USD")
    raw_record          = Column(JSONB)
    ingested_at         = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at          = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                                 onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("cik", "filing_type", "period_end",
                         name="uq_edgar_filing_composite"),
    )


class YfinanceMarketData(Base):
    """
    Market data from yfinance / FMP — equity prices, enterprise value, EVIC.

    Each row is one (ticker, as_of_date) snapshot including price, valuation
    multiples, and ESG scores.
    """
    __tablename__ = "dh_yfinance_market_data"

    id                  = Column(Text, primary_key=True)
    source_id           = Column(Text)
    ticker              = Column(Text, nullable=False)
    company_name        = Column(Text)
    exchange            = Column(Text)
    currency            = Column(Text, default="USD")
    sector              = Column(Text)
    industry            = Column(Text)
    country             = Column(Text)
    as_of_date          = Column(Date, nullable=False)
    # Price Data
    market_cap          = Column(Float)
    share_price         = Column(Float)
    shares_outstanding  = Column(Float)
    volume_avg_30d      = Column(Float)
    # Enterprise Value / EVIC
    enterprise_value    = Column(Float)
    total_debt          = Column(Float)
    cash_and_equivalents = Column(Float)
    minority_interest   = Column(Float)
    preferred_equity    = Column(Float)
    evic                = Column(Float)     # PCAF EVIC
    # Valuation Multiples
    pe_ratio            = Column(Float)
    pb_ratio            = Column(Float)
    ev_to_ebitda        = Column(Float)
    ev_to_revenue       = Column(Float)
    dividend_yield      = Column(Float)
    # Fundamentals (TTM)
    revenue_ttm         = Column(Float)
    ebitda_ttm          = Column(Float)
    net_income_ttm      = Column(Float)
    free_cash_flow_ttm  = Column(Float)
    # Returns
    return_1m           = Column(Float)
    return_3m           = Column(Float)
    return_6m           = Column(Float)
    return_1y           = Column(Float)
    return_ytd          = Column(Float)
    beta                = Column(Float)
    # ESG / Climate
    esg_score           = Column(Float)
    environment_score   = Column(Float)
    social_score        = Column(Float)
    governance_score    = Column(Float)
    # Metadata
    data_provider       = Column(Text, default="yfinance")
    raw_record          = Column(JSONB)
    ingested_at         = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at          = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                                 onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("ticker", "as_of_date",
                         name="uq_yfinance_ticker_date"),
    )
