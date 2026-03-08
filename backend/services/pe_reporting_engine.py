"""
PE GP/LP Reporting Engine
==========================
Generates quarterly and annual LP reports including fund performance,
ESG metrics, regulatory disclosures, and portfolio company summaries.

References:
- ILPA Reporting Template v3 — standardised LP reporting format
- INREV Style Reporting — European PE fund reporting best practice
- SFDR Art.7/Art.11 — ESG periodic disclosure for PE/VC
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from datetime import date


# ---------------------------------------------------------------------------
# Data Classes — Input
# ---------------------------------------------------------------------------

@dataclass
class FundPerformanceData:
    """Raw fund performance data for a reporting period."""
    fund_id: str
    fund_name: str
    vintage_year: int
    fund_size_eur: float
    committed_capital_eur: float
    called_capital_eur: float
    distributed_capital_eur: float
    nav_eur: float
    management_fees_eur: float = 0.0
    carried_interest_eur: float = 0.0
    reporting_date: str = ""  # YYYY-MM-DD


@dataclass
class PortfolioCompanySummary:
    """Summary data for a portfolio company in the report."""
    company_id: str
    company_name: str
    sector: str
    invested_eur: float
    current_nav_eur: float
    ownership_pct: float
    entry_date: str
    esg_score: float = 50.0
    esg_traffic_light: str = "amber"
    carbon_intensity_tco2e_per_meur: float = 0.0


@dataclass
class LPReportInput:
    """Full input for generating an LP report."""
    fund_performance: FundPerformanceData
    portfolio_companies: list[PortfolioCompanySummary]
    reporting_period: str  # e.g. "2025-Q4"
    report_type: str = "quarterly"  # quarterly | annual
    sfdr_classification: str = "art8"  # art6 | art8 | art9
    include_esg_annex: bool = True


# ---------------------------------------------------------------------------
# Data Classes — Output
# ---------------------------------------------------------------------------

@dataclass
class FundMetrics:
    """Computed fund performance metrics."""
    tvpi: float          # Total Value to Paid-In
    dpi: float           # Distribution to Paid-In
    rvpi: float          # Residual Value to Paid-In
    net_irr_pct: float   # Estimated net IRR (simplified)
    gross_irr_pct: float
    called_pct: float    # Called / Committed
    invested_pct: float  # Invested / Called
    dry_powder_eur: float


@dataclass
class ESGAnnex:
    """SFDR Art.11 periodic ESG annex data."""
    sfdr_classification: str
    sustainable_investment_pct: float
    taxonomy_aligned_pct: float
    do_no_significant_harm_pct: float
    pai_indicators: list[dict]  # Principal Adverse Impact indicators
    esg_score_weighted_avg: float
    carbon_footprint_tco2e: float
    green_revenue_pct: float


@dataclass
class LPReport:
    """Complete LP report output."""
    fund_id: str
    fund_name: str
    reporting_period: str
    report_type: str
    fund_metrics: FundMetrics
    portfolio_summary: list[dict]  # Serialised company summaries
    total_nav_eur: float
    total_invested_eur: float
    total_companies: int
    esg_annex: Optional[ESGAnnex]
    executive_summary: str
    sections: list[dict]  # Report sections with content


# ---------------------------------------------------------------------------
# PAI Indicators — SFDR Annex I (PE-relevant subset)
# ---------------------------------------------------------------------------

PAI_INDICATORS: list[dict] = [
    {"pai_id": "PAI_1", "name": "GHG Emissions (Scope 1+2+3)", "unit": "tCO2e",
     "category": "climate", "mandatory": True},
    {"pai_id": "PAI_2", "name": "Carbon Footprint", "unit": "tCO2e/EUR M invested",
     "category": "climate", "mandatory": True},
    {"pai_id": "PAI_3", "name": "GHG Intensity", "unit": "tCO2e/EUR M revenue",
     "category": "climate", "mandatory": True},
    {"pai_id": "PAI_4", "name": "Fossil Fuel Exposure", "unit": "%",
     "category": "climate", "mandatory": True},
    {"pai_id": "PAI_5", "name": "Non-Renewable Energy Share", "unit": "%",
     "category": "climate", "mandatory": True},
    {"pai_id": "PAI_6", "name": "Energy Intensity", "unit": "GWh/EUR M revenue",
     "category": "climate", "mandatory": True},
    {"pai_id": "PAI_7", "name": "Biodiversity Impact", "unit": "count",
     "category": "biodiversity", "mandatory": True},
    {"pai_id": "PAI_10", "name": "UNGC/OECD Violations", "unit": "count",
     "category": "social", "mandatory": True},
    {"pai_id": "PAI_13", "name": "Board Gender Diversity", "unit": "%",
     "category": "social", "mandatory": True},
    {"pai_id": "PAI_14", "name": "Controversial Weapons Exposure", "unit": "boolean",
     "category": "social", "mandatory": True},
]


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class PEReportingEngine:
    """Generates LP reports with fund metrics and ESG disclosure."""

    def generate_lp_report(self, inp: LPReportInput) -> LPReport:
        """Generate a complete LP report."""
        perf = inp.fund_performance

        # 1. Fund metrics
        metrics = self._compute_fund_metrics(perf)

        # 2. Portfolio summary
        portfolio_summary = [
            {
                "company_id": c.company_id,
                "company_name": c.company_name,
                "sector": c.sector,
                "invested_eur": c.invested_eur,
                "current_nav_eur": c.current_nav_eur,
                "ownership_pct": c.ownership_pct,
                "moic": round(c.current_nav_eur / c.invested_eur, 2) if c.invested_eur > 0 else 0,
                "esg_score": c.esg_score,
                "esg_traffic_light": c.esg_traffic_light,
                "carbon_intensity": c.carbon_intensity_tco2e_per_meur,
            }
            for c in inp.portfolio_companies
        ]

        total_nav = sum(c.current_nav_eur for c in inp.portfolio_companies)
        total_invested = sum(c.invested_eur for c in inp.portfolio_companies)

        # 3. ESG Annex
        esg_annex = None
        if inp.include_esg_annex:
            esg_annex = self._generate_esg_annex(inp)

        # 4. Executive summary
        exec_summary = self._generate_executive_summary(
            perf, metrics, inp.portfolio_companies, inp.reporting_period,
        )

        # 5. Report sections
        sections = self._generate_sections(
            perf, metrics, portfolio_summary, esg_annex, inp.report_type,
        )

        return LPReport(
            fund_id=perf.fund_id,
            fund_name=perf.fund_name,
            reporting_period=inp.reporting_period,
            report_type=inp.report_type,
            fund_metrics=metrics,
            portfolio_summary=portfolio_summary,
            total_nav_eur=total_nav,
            total_invested_eur=total_invested,
            total_companies=len(inp.portfolio_companies),
            esg_annex=esg_annex,
            executive_summary=exec_summary,
            sections=sections,
        )

    def get_pai_indicators(self) -> list[dict]:
        """Return SFDR PAI indicator reference data."""
        return PAI_INDICATORS

    # -------------------------------------------------------------------
    # Fund Metrics
    # -------------------------------------------------------------------

    def _compute_fund_metrics(self, perf: FundPerformanceData) -> FundMetrics:
        """Compute TVPI, DPI, RVPI, and estimated IRR."""
        called = perf.called_capital_eur
        if called <= 0:
            return FundMetrics(
                tvpi=0, dpi=0, rvpi=0, net_irr_pct=0, gross_irr_pct=0,
                called_pct=0, invested_pct=0, dry_powder_eur=perf.committed_capital_eur,
            )

        dpi = round(perf.distributed_capital_eur / called, 2)
        rvpi = round(perf.nav_eur / called, 2)
        tvpi = round(dpi + rvpi, 2)

        called_pct = round(called / perf.committed_capital_eur * 100, 1) if perf.committed_capital_eur > 0 else 0
        dry_powder = perf.committed_capital_eur - called

        # Simplified IRR estimate (based on TVPI and fund age)
        fund_age = max(1, 2026 - perf.vintage_year)
        gross_irr = round((tvpi ** (1 / fund_age) - 1) * 100, 1) if tvpi > 0 else 0
        # Net IRR after fees (simplified: 80% of gross)
        net_irr = round(gross_irr * 0.80, 1)

        return FundMetrics(
            tvpi=tvpi, dpi=dpi, rvpi=rvpi,
            net_irr_pct=net_irr, gross_irr_pct=gross_irr,
            called_pct=called_pct, invested_pct=called_pct,  # simplified
            dry_powder_eur=round(dry_powder, 2),
        )

    # -------------------------------------------------------------------
    # ESG Annex
    # -------------------------------------------------------------------

    def _generate_esg_annex(self, inp: LPReportInput) -> ESGAnnex:
        """Generate SFDR Art.11 periodic ESG annex."""
        companies = inp.portfolio_companies
        total_nav = sum(c.current_nav_eur for c in companies) or 1.0

        # Weighted ESG score
        weighted_esg = sum(
            c.esg_score * c.current_nav_eur for c in companies
        ) / total_nav

        # Carbon footprint
        total_carbon = sum(
            c.carbon_intensity_tco2e_per_meur * c.current_nav_eur / 1_000_000
            for c in companies
        )

        # Classification-based thresholds
        if inp.sfdr_classification == "art9":
            sustainable_pct = 80.0
            taxonomy_pct = 40.0
            dnsh_pct = 95.0
            green_rev_pct = 60.0
        elif inp.sfdr_classification == "art8":
            sustainable_pct = 30.0
            taxonomy_pct = 10.0
            dnsh_pct = 80.0
            green_rev_pct = 25.0
        else:
            sustainable_pct = 0.0
            taxonomy_pct = 0.0
            dnsh_pct = 0.0
            green_rev_pct = 0.0

        # PAI indicators (simplified: generate from company data)
        pai = []
        for indicator in PAI_INDICATORS:
            pai.append({
                "pai_id": indicator["pai_id"],
                "name": indicator["name"],
                "unit": indicator["unit"],
                "value": None,  # Would come from actual company data
                "coverage_pct": len(companies) / max(len(companies), 1) * 100,
            })

        return ESGAnnex(
            sfdr_classification=inp.sfdr_classification,
            sustainable_investment_pct=sustainable_pct,
            taxonomy_aligned_pct=taxonomy_pct,
            do_no_significant_harm_pct=dnsh_pct,
            pai_indicators=pai,
            esg_score_weighted_avg=round(weighted_esg, 1),
            carbon_footprint_tco2e=round(total_carbon, 2),
            green_revenue_pct=green_rev_pct,
        )

    # -------------------------------------------------------------------
    # Narrative Generation
    # -------------------------------------------------------------------

    def _generate_executive_summary(
        self, perf: FundPerformanceData, metrics: FundMetrics,
        companies: list[PortfolioCompanySummary], period: str,
    ) -> str:
        """Generate executive summary paragraph."""
        n = len(companies)
        return (
            f"{perf.fund_name} ({perf.vintage_year}) — {period} Report. "
            f"The fund has called {metrics.called_pct}% of committed capital "
            f"(EUR {perf.called_capital_eur:,.0f}). "
            f"Current TVPI stands at {metrics.tvpi}x with a net IRR of {metrics.net_irr_pct}%. "
            f"The portfolio comprises {n} active companies with a total NAV of "
            f"EUR {perf.nav_eur:,.0f}. "
            f"DPI is {metrics.dpi}x and dry powder is EUR {metrics.dry_powder_eur:,.0f}."
        )

    def _generate_sections(
        self, perf: FundPerformanceData, metrics: FundMetrics,
        portfolio_summary: list[dict], esg_annex: Optional[ESGAnnex],
        report_type: str,
    ) -> list[dict]:
        """Generate report sections."""
        sections = [
            {
                "section_id": "fund_overview",
                "title": "Fund Overview",
                "content": {
                    "fund_name": perf.fund_name,
                    "vintage": perf.vintage_year,
                    "fund_size_eur": perf.fund_size_eur,
                    "tvpi": metrics.tvpi,
                    "dpi": metrics.dpi,
                    "rvpi": metrics.rvpi,
                    "net_irr_pct": metrics.net_irr_pct,
                    "gross_irr_pct": metrics.gross_irr_pct,
                },
            },
            {
                "section_id": "capital_account",
                "title": "Capital Account Summary",
                "content": {
                    "committed_eur": perf.committed_capital_eur,
                    "called_eur": perf.called_capital_eur,
                    "distributed_eur": perf.distributed_capital_eur,
                    "nav_eur": perf.nav_eur,
                    "called_pct": metrics.called_pct,
                    "dry_powder_eur": metrics.dry_powder_eur,
                    "management_fees_eur": perf.management_fees_eur,
                    "carried_interest_eur": perf.carried_interest_eur,
                },
            },
            {
                "section_id": "portfolio_companies",
                "title": "Portfolio Company Summary",
                "content": portfolio_summary,
            },
        ]

        if esg_annex:
            sections.append({
                "section_id": "esg_annex",
                "title": "ESG & SFDR Annex",
                "content": {
                    "classification": esg_annex.sfdr_classification,
                    "sustainable_investment_pct": esg_annex.sustainable_investment_pct,
                    "taxonomy_aligned_pct": esg_annex.taxonomy_aligned_pct,
                    "esg_score_avg": esg_annex.esg_score_weighted_avg,
                    "carbon_footprint_tco2e": esg_annex.carbon_footprint_tco2e,
                    "pai_count": len(esg_annex.pai_indicators),
                },
            })

        if report_type == "annual":
            sections.append({
                "section_id": "annual_review",
                "title": "Annual Review & Outlook",
                "content": {
                    "achievements": "ESG integration across portfolio",
                    "outlook": "Continued focus on value creation through ESG improvements",
                },
            })

        return sections
