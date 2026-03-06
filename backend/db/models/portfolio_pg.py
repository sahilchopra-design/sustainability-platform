"""
PostgreSQL models for Portfolio, Asset, AnalysisRun, Organisation, OrgUser,
User, Session — replacing MongoDB/Beanie.
"""

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, ForeignKey, Text, JSON, Boolean,
    SmallInteger,
)
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid as _uuid

from db.base import Base


# ── Organisation & Tenant ─────────────────────────────────────────────────────

class OrganisationPG(Base):
    """Multi-tenant organisation (bank, insurer, fund manager, etc.)."""
    __tablename__ = "organisations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4)
    name = Column(String(500), nullable=False)
    short_name = Column(String(100))
    org_type = Column(String(50), nullable=False, default="financial_institution")
    jurisdiction = Column(String(3))           # ISO 3166-1 alpha-3
    regulatory_regime = Column(String(100))
    subscription_tier = Column(String(20), default="professional")
    logo_url = Column(Text)
    website = Column(Text)
    lei = Column(String(20))                   # Legal Entity Identifier
    is_active = Column(Boolean, nullable=False, default=True)
    settings = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    org_users = relationship("OrgUserPG", back_populates="organisation", cascade="all, delete-orphan")


class OrgUserPG(Base):
    """Organisation-to-user membership with role and permissions."""
    __tablename__ = "org_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(320), nullable=False)
    full_name = Column(String(500))
    role = Column(String(50), nullable=False, default="analyst")
    department = Column(String(200))
    is_active = Column(Boolean, nullable=False, default=True)
    last_login = Column(DateTime(timezone=True))
    permissions = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    organisation = relationship("OrganisationPG", back_populates="org_users")


# ── Portfolio ─────────────────────────────────────────────────────────────────

class PortfolioPG(Base):
    """Portfolio stored in PostgreSQL (replaces MongoDB Portfolio)."""
    __tablename__ = "portfolios_pg"

    id = Column(String, primary_key=True, default=lambda: str(_uuid.uuid4()))
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

    id = Column(String, primary_key=True, default=lambda: str(_uuid.uuid4()))
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

    id = Column(String, primary_key=True, default=lambda: str(_uuid.uuid4()))
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
    # RBAC columns (migration 025)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=True, index=True)
    role = Column(String(50), nullable=False, default="viewer")
    is_active = Column(Boolean, nullable=False, default=True)
    last_login = Column(DateTime(timezone=True))


class UserSessionPG(Base):
    """Session stored in PostgreSQL."""
    __tablename__ = "user_sessions_pg"

    id = Column(String, primary_key=True, default=lambda: str(_uuid.uuid4()))
    user_id = Column(String, ForeignKey("users_pg.user_id", ondelete="CASCADE"), nullable=False, index=True)
    session_token = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


# ── Audit Log (read-only ORM view — writes via middleware raw SQL) ────────────

class AuditLogPG(Base):
    """
    Read-only ORM mapping for the partitioned audit_log table.
    Writes happen in AuditMiddleware via raw SQL; this model is for
    admin query endpoints only.
    """
    __tablename__ = "audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    # Who
    org_id = Column(UUID(as_uuid=True))
    user_id = Column(String(100))
    user_email = Column(String(320))
    user_role = Column(String(50))
    ip_address = Column(INET)
    user_agent = Column(Text)
    session_id = Column(Text)
    request_id = Column(Text)
    # What
    action_class = Column(String(20))
    action = Column(String(100))
    http_method = Column(String(10))
    endpoint = Column(Text)
    http_status = Column(SmallInteger)
    duration_ms = Column(Integer)
    module = Column(String(100))
    # Target
    entity_type = Column(String(100))
    entity_id = Column(Text)
    record_id = Column(Text)
    # Payload
    old_values = Column(JSONB)
    new_values = Column(JSONB)
    request_summary = Column(JSONB)
    result_summary = Column(JSONB)
    # Meta
    status = Column(String(20), default="success")
    error_message = Column(Text)
    checksum = Column(String(64))
