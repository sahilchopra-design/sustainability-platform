"""
Emissions Ingestion ORM models -- Climate TRACE + OWID CO2/Energy.

Maps to tables created by Session 9 migration:
  - dh_climate_trace_emissions  -- facility/country GHG data from Climate TRACE
  - dh_owid_co2_energy          -- country-level CO2, energy, and climate series from OWID
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger, Column, DateTime, Float, Integer, String, Text, JSON,
    ForeignKey, UniqueConstraint,
)

from db.base import Base


class ClimateTraceEmission(Base):
    """Satellite-derived GHG emissions from Climate TRACE (facility or country level)."""
    __tablename__ = "dh_climate_trace_emissions"

    id = Column(Text, primary_key=True)
    source_id = Column(Text, ForeignKey("dh_data_sources.id"))
    country_iso3 = Column(String(3))
    country_name = Column(Text)
    sector = Column(Text, nullable=False)
    subsector = Column(Text)
    gas = Column(String(20), default="co2e")
    year = Column(Integer, nullable=False)
    emissions_quantity = Column(Float)
    emissions_unit = Column(String(30), default="tonnes")
    facility_name = Column(Text)
    facility_id = Column(Text)
    latitude = Column(Float)
    longitude = Column(Float)
    data_source = Column(Text)
    confidence = Column(String(20))
    raw_record = Column(JSON)
    ingested_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))


class OwidCo2Energy(Base):
    """Country-level CO2 emissions, energy mix, and climate indicators from OWID."""
    __tablename__ = "dh_owid_co2_energy"

    id = Column(Text, primary_key=True)
    source_id = Column(Text, ForeignKey("dh_data_sources.id"))
    country_iso3 = Column(String(3))
    country_name = Column(Text, nullable=False)
    year = Column(Integer, nullable=False)
    population = Column(BigInteger)
    gdp = Column(Float)
    # CO2 emissions
    co2 = Column(Float)
    co2_per_capita = Column(Float)
    co2_per_gdp = Column(Float)
    co2_growth_pct = Column(Float)
    cumulative_co2 = Column(Float)
    share_global_co2 = Column(Float)
    # CO2 by fuel
    coal_co2 = Column(Float)
    oil_co2 = Column(Float)
    gas_co2 = Column(Float)
    cement_co2 = Column(Float)
    flaring_co2 = Column(Float)
    other_co2 = Column(Float)
    # Other GHGs
    methane = Column(Float)
    nitrous_oxide = Column(Float)
    total_ghg = Column(Float)
    total_ghg_excl_lucf = Column(Float)
    # Energy
    primary_energy_consumption = Column(Float)
    energy_per_capita = Column(Float)
    energy_per_gdp = Column(Float)
    # Electricity mix
    electricity_generation = Column(Float)
    renewables_share_energy = Column(Float)
    renewables_share_elec = Column(Float)
    fossil_share_energy = Column(Float)
    nuclear_share_energy = Column(Float)
    solar_share_energy = Column(Float)
    wind_share_energy = Column(Float)
    hydro_share_energy = Column(Float)
    # Temperature
    temperature_change_from_co2 = Column(Float)
    temperature_change_from_ghg = Column(Float)
    # Metadata
    raw_record = Column(JSON)
    ingested_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("country_iso3", "year", name="uq_owid_country_year"),
    )
