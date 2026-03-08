"""
Tenant ESG Profile Tracker
===========================
Track tenant emissions, green lease clauses, and occupancy patterns
at property and portfolio level.

Key outputs:
- Tenant-level ESG profile: Scope 1/2 emissions, green lease clauses
- Green lease clause coverage: % of leases with energy data sharing,
  fit-out standards, waste management
- Property-level occupancy ESG score (weighted by leased area)
- Portfolio-level tenant ESG summary

References:
- Better Buildings Partnership (BBP) Green Lease Toolkit 2024
- GRESB Real Estate Assessment: Tenant Engagement module
- UK Green Building Council: Net Zero Carbon Buildings Framework
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


# ---------------------------------------------------------------------------
# Enums & Reference Data
# ---------------------------------------------------------------------------

class GreenLeaseClause(str, Enum):
    ENERGY_DATA_SHARING = "energy_data_sharing"
    FITOUT_STANDARDS = "fitout_standards"
    WASTE_MANAGEMENT = "waste_management"
    WATER_EFFICIENCY = "water_efficiency"
    RENEWABLE_ENERGY = "renewable_energy"
    TRANSPORT_PLAN = "transport_plan"
    BIODIVERSITY = "biodiversity"


# Green lease clause weights for composite scoring
CLAUSE_WEIGHTS: dict[str, float] = {
    "energy_data_sharing": 0.25,
    "fitout_standards": 0.20,
    "waste_management": 0.15,
    "water_efficiency": 0.10,
    "renewable_energy": 0.15,
    "transport_plan": 0.10,
    "biodiversity": 0.05,
}

# Tenant sector carbon intensity benchmarks (tCO2e per employee per year)
SECTOR_BENCHMARKS: dict[str, float] = {
    "technology": 3.5,
    "financial_services": 4.0,
    "professional_services": 3.0,
    "retail": 8.0,
    "healthcare": 12.0,
    "manufacturing": 25.0,
    "government": 4.5,
    "education": 3.5,
    "hospitality": 10.0,
    "other": 6.0,
}


# ---------------------------------------------------------------------------
# Data Classes — Inputs
# ---------------------------------------------------------------------------

@dataclass
class TenantInput:
    """Input for a single tenant's ESG profile."""
    tenant_id: str
    name: str
    sector: str                              # technology / financial_services / etc.
    leased_area_m2: float                    # Area occupied
    annual_rent_eur: float
    headcount: int = 0
    scope1_tco2e: float = 0.0               # Direct emissions
    scope2_tco2e: float = 0.0               # Electricity emissions
    green_lease_clauses: list[str] = field(default_factory=list)
    # e.g. ["energy_data_sharing", "fitout_standards"]
    energy_data_reported: bool = False       # Does tenant actually report energy data?
    has_science_based_target: bool = False
    has_net_zero_commitment: bool = False
    lease_expiry_year: Optional[int] = None


@dataclass
class PropertyTenantInput:
    """Input for a property with its tenants."""
    property_id: str
    name: str
    total_lettable_area_m2: float
    tenants: list[TenantInput]
    epc_rating: str = "C"
    country: str = "GB"


# ---------------------------------------------------------------------------
# Data Classes — Outputs
# ---------------------------------------------------------------------------

@dataclass
class TenantESGProfile:
    """ESG profile for a single tenant."""
    tenant_id: str
    name: str
    sector: str
    leased_area_m2: float
    carbon_intensity_per_employee: float     # tCO2e/employee/yr
    carbon_intensity_per_m2: float           # tCO2e/m2/yr
    sector_benchmark_per_employee: float
    vs_benchmark_pct: float                  # % above/below benchmark
    green_lease_score: float                 # 0-100
    green_lease_clause_count: int
    green_lease_clause_coverage: dict[str, bool]  # clause -> present
    energy_data_reported: bool
    has_science_based_target: bool
    has_net_zero_commitment: bool
    tenant_esg_score: float                  # 0-100 composite


@dataclass
class PropertyTenantResult:
    """Tenant ESG result for a single property."""
    property_id: str
    name: str
    total_lettable_area_m2: float
    occupied_area_m2: float
    occupancy_rate_pct: float
    tenant_count: int

    # Green lease metrics
    green_lease_coverage_pct: float          # % of leases with >= 1 green clause
    avg_green_lease_score: float             # Area-weighted average
    clause_coverage: dict[str, float]        # Per-clause: % of leased area

    # Carbon metrics
    total_scope1_tco2e: float
    total_scope2_tco2e: float
    total_tenant_emissions_tco2e: float
    carbon_intensity_per_m2: float           # Portfolio total / occupied area

    # Engagement metrics
    energy_data_reporting_pct: float         # % of tenants reporting energy data
    sbt_coverage_pct: float                  # % with science-based targets (by area)
    net_zero_coverage_pct: float             # % with net zero commitments (by area)

    # Composite
    property_tenant_esg_score: float         # 0-100, area-weighted

    tenant_profiles: list[TenantESGProfile]


@dataclass
class PortfolioTenantSummary:
    """Portfolio-level tenant ESG summary."""
    total_properties: int
    total_tenants: int
    total_occupied_area_m2: float
    avg_occupancy_rate_pct: float

    # Aggregate green lease
    portfolio_green_lease_coverage_pct: float
    portfolio_avg_green_lease_score: float
    portfolio_clause_coverage: dict[str, float]

    # Aggregate carbon
    total_tenant_emissions_tco2e: float
    portfolio_carbon_intensity_per_m2: float

    # Aggregate engagement
    portfolio_energy_reporting_pct: float
    portfolio_sbt_coverage_pct: float
    portfolio_net_zero_coverage_pct: float

    # Composite
    portfolio_tenant_esg_score: float

    property_results: list[PropertyTenantResult]


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class TenantESGTracker:
    """Track tenant ESG profiles and green lease coverage."""

    def assess_tenant(self, tenant: TenantInput) -> TenantESGProfile:
        """Assess a single tenant's ESG profile."""
        # Carbon intensity
        total_carbon = tenant.scope1_tco2e + tenant.scope2_tco2e
        carbon_per_emp = (total_carbon / tenant.headcount
                          if tenant.headcount > 0 else 0.0)
        carbon_per_m2 = (total_carbon / tenant.leased_area_m2
                         if tenant.leased_area_m2 > 0 else 0.0)

        benchmark = SECTOR_BENCHMARKS.get(tenant.sector.lower(), SECTOR_BENCHMARKS["other"])
        vs_bench = ((carbon_per_emp - benchmark) / benchmark * 100
                    if benchmark > 0 and carbon_per_emp > 0 else 0.0)

        # Green lease score
        clause_coverage = {
            c.value: (c.value in tenant.green_lease_clauses)
            for c in GreenLeaseClause
        }
        gl_score = sum(
            CLAUSE_WEIGHTS.get(clause, 0) * 100
            for clause in tenant.green_lease_clauses
            if clause in CLAUSE_WEIGHTS
        )

        # Composite ESG score
        # Components: green lease (30%), carbon performance (30%),
        # commitments (20%), data transparency (20%)
        carbon_score = max(0, min(100, 50 - vs_bench))  # Better than benchmark = higher
        commitment_score = (
            (50 if tenant.has_science_based_target else 0)
            + (50 if tenant.has_net_zero_commitment else 0)
        )
        transparency_score = 100 if tenant.energy_data_reported else 0

        composite = (
            gl_score * 0.30
            + carbon_score * 0.30
            + commitment_score * 0.20
            + transparency_score * 0.20
        )

        return TenantESGProfile(
            tenant_id=tenant.tenant_id,
            name=tenant.name,
            sector=tenant.sector,
            leased_area_m2=tenant.leased_area_m2,
            carbon_intensity_per_employee=round(carbon_per_emp, 3),
            carbon_intensity_per_m2=round(carbon_per_m2, 6),
            sector_benchmark_per_employee=benchmark,
            vs_benchmark_pct=round(vs_bench, 1),
            green_lease_score=round(gl_score, 1),
            green_lease_clause_count=len(tenant.green_lease_clauses),
            green_lease_clause_coverage=clause_coverage,
            energy_data_reported=tenant.energy_data_reported,
            has_science_based_target=tenant.has_science_based_target,
            has_net_zero_commitment=tenant.has_net_zero_commitment,
            tenant_esg_score=round(min(100, max(0, composite)), 1),
        )

    def assess_property(self, prop: PropertyTenantInput) -> PropertyTenantResult:
        """Assess tenant ESG at property level."""
        if not prop.tenants:
            return PropertyTenantResult(
                property_id=prop.property_id, name=prop.name,
                total_lettable_area_m2=prop.total_lettable_area_m2,
                occupied_area_m2=0, occupancy_rate_pct=0, tenant_count=0,
                green_lease_coverage_pct=0, avg_green_lease_score=0,
                clause_coverage={c.value: 0.0 for c in GreenLeaseClause},
                total_scope1_tco2e=0, total_scope2_tco2e=0,
                total_tenant_emissions_tco2e=0, carbon_intensity_per_m2=0,
                energy_data_reporting_pct=0, sbt_coverage_pct=0,
                net_zero_coverage_pct=0, property_tenant_esg_score=0,
                tenant_profiles=[],
            )

        profiles = [self.assess_tenant(t) for t in prop.tenants]
        occupied = sum(t.leased_area_m2 for t in prop.tenants)
        occ_rate = (occupied / prop.total_lettable_area_m2 * 100
                    if prop.total_lettable_area_m2 > 0 else 0.0)

        # Green lease coverage: % of tenants (by area) with at least 1 green clause
        gl_area = sum(
            t.leased_area_m2 for t in prop.tenants
            if len(t.green_lease_clauses) > 0
        )
        gl_coverage = (gl_area / occupied * 100) if occupied > 0 else 0.0

        # Area-weighted average green lease score
        avg_gl = (sum(p.green_lease_score * t.leased_area_m2
                      for p, t in zip(profiles, prop.tenants))
                  / occupied if occupied > 0 else 0.0)

        # Per-clause coverage (% of leased area with each clause)
        clause_cov: dict[str, float] = {}
        for c in GreenLeaseClause:
            area_with = sum(
                t.leased_area_m2 for t in prop.tenants
                if c.value in t.green_lease_clauses
            )
            clause_cov[c.value] = round(area_with / occupied * 100 if occupied > 0 else 0.0, 1)

        # Carbon aggregates
        total_s1 = sum(t.scope1_tco2e for t in prop.tenants)
        total_s2 = sum(t.scope2_tco2e for t in prop.tenants)
        total_emissions = total_s1 + total_s2
        carbon_int = total_emissions / occupied if occupied > 0 else 0.0

        # Engagement metrics (by area)
        energy_rpt = sum(
            t.leased_area_m2 for t in prop.tenants if t.energy_data_reported
        )
        sbt_area = sum(
            t.leased_area_m2 for t in prop.tenants if t.has_science_based_target
        )
        nz_area = sum(
            t.leased_area_m2 for t in prop.tenants if t.has_net_zero_commitment
        )

        energy_pct = energy_rpt / occupied * 100 if occupied > 0 else 0.0
        sbt_pct = sbt_area / occupied * 100 if occupied > 0 else 0.0
        nz_pct = nz_area / occupied * 100 if occupied > 0 else 0.0

        # Property-level ESG score (area-weighted)
        prop_score = (sum(p.tenant_esg_score * t.leased_area_m2
                         for p, t in zip(profiles, prop.tenants))
                      / occupied if occupied > 0 else 0.0)

        return PropertyTenantResult(
            property_id=prop.property_id,
            name=prop.name,
            total_lettable_area_m2=prop.total_lettable_area_m2,
            occupied_area_m2=round(occupied, 1),
            occupancy_rate_pct=round(occ_rate, 1),
            tenant_count=len(prop.tenants),
            green_lease_coverage_pct=round(gl_coverage, 1),
            avg_green_lease_score=round(avg_gl, 1),
            clause_coverage=clause_cov,
            total_scope1_tco2e=round(total_s1, 3),
            total_scope2_tco2e=round(total_s2, 3),
            total_tenant_emissions_tco2e=round(total_emissions, 3),
            carbon_intensity_per_m2=round(carbon_int, 6),
            energy_data_reporting_pct=round(energy_pct, 1),
            sbt_coverage_pct=round(sbt_pct, 1),
            net_zero_coverage_pct=round(nz_pct, 1),
            property_tenant_esg_score=round(prop_score, 1),
            tenant_profiles=profiles,
        )

    def assess_portfolio(
        self, properties: list[PropertyTenantInput]
    ) -> PortfolioTenantSummary:
        """Assess tenant ESG across a portfolio."""
        if not properties:
            return PortfolioTenantSummary(
                total_properties=0, total_tenants=0, total_occupied_area_m2=0,
                avg_occupancy_rate_pct=0, portfolio_green_lease_coverage_pct=0,
                portfolio_avg_green_lease_score=0,
                portfolio_clause_coverage={c.value: 0.0 for c in GreenLeaseClause},
                total_tenant_emissions_tco2e=0, portfolio_carbon_intensity_per_m2=0,
                portfolio_energy_reporting_pct=0, portfolio_sbt_coverage_pct=0,
                portfolio_net_zero_coverage_pct=0, portfolio_tenant_esg_score=0,
                property_results=[],
            )

        results = [self.assess_property(p) for p in properties]
        n = len(results)

        total_tenants = sum(r.tenant_count for r in results)
        total_occ = sum(r.occupied_area_m2 for r in results)
        avg_occ = sum(r.occupancy_rate_pct for r in results) / n

        # Area-weighted green lease coverage
        gl_cov = (sum(r.green_lease_coverage_pct * r.occupied_area_m2 for r in results)
                  / total_occ if total_occ > 0 else 0.0)
        avg_gl = (sum(r.avg_green_lease_score * r.occupied_area_m2 for r in results)
                  / total_occ if total_occ > 0 else 0.0)

        # Portfolio clause coverage
        port_clause: dict[str, float] = {}
        for c in GreenLeaseClause:
            cov = (sum(r.clause_coverage.get(c.value, 0) * r.occupied_area_m2 for r in results)
                   / total_occ if total_occ > 0 else 0.0)
            port_clause[c.value] = round(cov, 1)

        total_emissions = sum(r.total_tenant_emissions_tco2e for r in results)
        carbon_int = total_emissions / total_occ if total_occ > 0 else 0.0

        # Portfolio engagement (area-weighted)
        energy_pct = (sum(r.energy_data_reporting_pct * r.occupied_area_m2 for r in results)
                      / total_occ if total_occ > 0 else 0.0)
        sbt_pct = (sum(r.sbt_coverage_pct * r.occupied_area_m2 for r in results)
                   / total_occ if total_occ > 0 else 0.0)
        nz_pct = (sum(r.net_zero_coverage_pct * r.occupied_area_m2 for r in results)
                  / total_occ if total_occ > 0 else 0.0)

        port_score = (sum(r.property_tenant_esg_score * r.occupied_area_m2 for r in results)
                      / total_occ if total_occ > 0 else 0.0)

        return PortfolioTenantSummary(
            total_properties=n,
            total_tenants=total_tenants,
            total_occupied_area_m2=round(total_occ, 1),
            avg_occupancy_rate_pct=round(avg_occ, 1),
            portfolio_green_lease_coverage_pct=round(gl_cov, 1),
            portfolio_avg_green_lease_score=round(avg_gl, 1),
            portfolio_clause_coverage=port_clause,
            total_tenant_emissions_tco2e=round(total_emissions, 3),
            portfolio_carbon_intensity_per_m2=round(carbon_int, 6),
            portfolio_energy_reporting_pct=round(energy_pct, 1),
            portfolio_sbt_coverage_pct=round(sbt_pct, 1),
            portfolio_net_zero_coverage_pct=round(nz_pct, 1),
            portfolio_tenant_esg_score=round(port_score, 1),
            property_results=results,
        )
