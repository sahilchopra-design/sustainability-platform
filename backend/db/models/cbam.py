"""
CBAM (Carbon Border Adjustment Mechanism) database models.
8 tables for product categories, suppliers, emissions, cost projections, compliance.
"""

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, ForeignKey, Text, Boolean, JSON,
    Numeric, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from db.base import Base


class CBAMProductCategory(Base):
    __tablename__ = "cbam_product_category"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    cn_code = Column(String(8), nullable=False, unique=True)
    hs_code = Column(String(6), nullable=False)
    sector = Column(String(50), nullable=False, index=True)
    product_name = Column(String(255), nullable=False)
    default_direct_emissions = Column(Float)  # tCO2/tonne
    default_indirect_emissions = Column(Float)
    default_total_emissions = Column(Float)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class CBAMSupplier(Base):
    __tablename__ = "cbam_supplier"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    supplier_name = Column(String(255), nullable=False)
    country_code = Column(String(2), nullable=False, index=True)
    verification_status = Column(String(50), default="unverified")
    has_domestic_carbon_price = Column(Boolean, default=False)
    domestic_carbon_price = Column(Float, default=0)
    risk_score = Column(Float)
    risk_category = Column(String(50))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    emissions = relationship("CBAMEmbeddedEmissions", back_populates="supplier", cascade="all, delete-orphan")


class CBAMEmbeddedEmissions(Base):
    __tablename__ = "cbam_embedded_emissions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    supplier_id = Column(String, ForeignKey("cbam_supplier.id", ondelete="CASCADE"), nullable=False, index=True)
    product_category_id = Column(String, ForeignKey("cbam_product_category.id"), nullable=False)
    reporting_year = Column(Integer, nullable=False)
    reporting_quarter = Column(Integer)
    import_volume_tonnes = Column(Float, default=0)
    direct_emissions = Column(Float, default=0)  # tCO2
    indirect_emissions = Column(Float, default=0)
    specific_direct = Column(Float)  # tCO2/tonne product
    specific_indirect = Column(Float)
    specific_total = Column(Float)
    is_verified = Column(Boolean, default=False)
    uses_default_values = Column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint("supplier_id", "product_category_id", "reporting_year", "reporting_quarter",
                         name="uq_cbam_emissions_period"),
    )
    supplier = relationship("CBAMSupplier", back_populates="emissions")


class CBAMCostProjection(Base):
    __tablename__ = "cbam_cost_projection"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    supplier_id = Column(String, ForeignKey("cbam_supplier.id"), nullable=False, index=True)
    product_category_id = Column(String, ForeignKey("cbam_product_category.id"))
    projection_year = Column(Integer, nullable=False)
    scenario_name = Column(String(100))
    import_volume_tonnes = Column(Float, default=0)
    embedded_emissions_tco2 = Column(Float, default=0)
    eu_ets_price_eur = Column(Float, default=0)
    domestic_carbon_credit_eur = Column(Float, default=0)
    net_cbam_cost_eur = Column(Float, default=0)
    cost_as_pct_revenue = Column(Float, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class CBAMComplianceReport(Base):
    __tablename__ = "cbam_compliance_report"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    report_year = Column(Integer, nullable=False)
    report_quarter = Column(Integer, nullable=False)
    submission_status = Column(String(50), default="draft")
    total_imports_tonnes = Column(Float, default=0)
    total_embedded_emissions = Column(Float, default=0)
    total_certificate_cost = Column(Float, default=0)
    compliance_status = Column(String(50), default="pending")
    supplier_count = Column(Integer, default=0)
    product_count = Column(Integer, default=0)
    details = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint("report_year", "report_quarter", name="uq_cbam_report_period"),)


class CBAMCountryRisk(Base):
    __tablename__ = "cbam_country_risk"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    country_code = Column(String(2), nullable=False, unique=True)
    country_name = Column(String(100), nullable=False)
    has_carbon_pricing = Column(Boolean, default=False)
    carbon_price_eur = Column(Float, default=0)
    grid_emission_factor = Column(Float)  # tCO2/MWh
    overall_risk_score = Column(Float)  # 0-1
    risk_category = Column(String(50))  # Low, Medium, High, Very High
    default_value_markup = Column(Float, default=0)  # % markup for default values


class CBAMCertificatePrice(Base):
    __tablename__ = "cbam_certificate_price"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    price_date = Column(String(10), nullable=False)  # YYYY-MM-DD or YYYY
    eu_ets_price_eur = Column(Float)
    cbam_certificate_price_eur = Column(Float)
    scenario_name = Column(String(100))
    is_projection = Column(Boolean, default=False)


class CBAMVerifier(Base):
    __tablename__ = "cbam_verifier"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    verifier_name = Column(String(255), nullable=False)
    accreditation_body = Column(String(100))
    country_code = Column(String(2), nullable=False)
    accredited_sectors = Column(JSON, default=list)
    accreditation_status = Column(String(50), default="active")
