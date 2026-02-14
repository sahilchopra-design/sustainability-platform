"""
PostgreSQL models for Portfolio, Asset, AnalysisRun — replacing MongoDB/Beanie.
"""

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, ForeignKey, Text, JSON, Boolean
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from db.base import Base


class PortfolioPG(Base):
    """Portfolio stored in PostgreSQL (replaces MongoDB Portfolio)."""
    __tablename__ = "portfolios_pg"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    assets = relationship("AssetPG", back_populates="portfolio", cascade="all, delete-orphan")
    analysis_runs = relationship("AnalysisRunPG", back_populates="portfolio", cascade="all, delete-orphan")


class AssetPG(Base):
    """Individual asset within a portfolio."""
    __tablename__ = "assets_pg"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    portfolio_id = Column(String, ForeignKey("portfolios_pg.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_type = Column(String(50), default="Bond")  # Bond, Loan, Equity
    company_name = Column(String(255), nullable=False)
    company_sector = Column(String(100), nullable=False)
    company_subsector = Column(String(100))
    exposure = Column(Float, nullable=False)
    market_value = Column(Float)
    base_pd = Column(Float, default=0.02)
    base_lgd = Column(Float, default=0.45)
    rating = Column(String(10), default="BBB")
    maturity_years = Column(Integer, default=5)

    portfolio = relationship("PortfolioPG", back_populates="assets")


class AnalysisRunPG(Base):
    """Analysis run result stored in PostgreSQL."""
    __tablename__ = "analysis_runs_pg"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    portfolio_id = Column(String, ForeignKey("portfolios_pg.id", ondelete="CASCADE"), nullable=False, index=True)
    portfolio_name = Column(String(255))
    scenarios = Column(JSON, default=list)
    horizons = Column(JSON, default=list)
    results = Column(JSON, default=list)
    status = Column(String(50), default="completed")
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True))

    portfolio = relationship("PortfolioPG", back_populates="analysis_runs")


class UserPG(Base):
    """User stored in PostgreSQL (replaces MongoDB users collection)."""
    __tablename__ = "users_pg"

    user_id = Column(String, primary_key=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    name = Column(String(255))
    picture = Column(String(512))
    password_hash = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class UserSessionPG(Base):
    """Session stored in PostgreSQL."""
    __tablename__ = "user_sessions_pg"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users_pg.user_id", ondelete="CASCADE"), nullable=False, index=True)
    session_token = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
