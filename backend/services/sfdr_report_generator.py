"""
SFDR Periodic Report Generator
================================
Generates SFDR periodic disclosure data for Art.8 and Art.9 funds,
conforming to the SFDR Delegated Regulation RTS Annex II (Art.8)
and Annex IV (Art.9) templates.

References:
- EU Regulation 2019/2088 (SFDR)
- Delegated Regulation 2022/1288 (RTS) — periodic disclosure templates
- EU Taxonomy Regulation 2020/852 (Art.5-8)
- Commission Q&A on SFDR application (2023, 2024)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# SFDR Art.8 template sections
ART8_SECTIONS = [
    "environmental_social_characteristics",
    "investment_strategy",
    "proportion_of_investments",
    "top_investments",
    "sector_breakdown",
    "geography_breakdown",
    "sustainability_indicators",
    "pai_summary",
    "taxonomy_alignment",
]

# SFDR Art.9 additional sections
ART9_SECTIONS = ART8_SECTIONS + [
    "sustainable_investment_objective",
    "no_significant_harm",
    "eu_taxonomy_contribution",
]


class InvestmentCategory(str, Enum):
    TAXONOMY_ALIGNED_ENV = "taxonomy_aligned_environmental"
    OTHER_ENVIRONMENTAL = "other_environmental"
    SOCIAL = "social"
    NOT_SUSTAINABLE = "not_sustainable"


# ---------------------------------------------------------------------------
# Data Classes — Inputs
# ---------------------------------------------------------------------------

@dataclass
class SFDRHolding:
    """Holding with SFDR-relevant fields."""
    holding_id: str
    security_name: str
    isin: Optional[str] = None
    sector: str = "Other"
    country: str = "US"
    weight_pct: float = 0.0
    market_value: float = 0.0
    taxonomy_aligned_pct: float = 0.0
    sustainable_environmental_pct: float = 0.0
    sustainable_social_pct: float = 0.0
    esg_score: float = 0.0
    dnsh_compliant: bool = True
    carbon_intensity: float = 0.0


@dataclass
class SFDRFundInput:
    """Fund input for SFDR report generation."""
    fund_id: str
    fund_name: str
    sfdr_classification: str       # art6 / art8 / art8plus / art9
    fund_type: str = "ucits"
    reporting_period: str = ""     # e.g. "2025-01-01 to 2025-12-31"
    reference_benchmark: Optional[str] = None
    aum: float = 0.0
    promoted_characteristics: list[str] = field(default_factory=list)
    esg_strategy: str = "integration"
    minimum_taxonomy_pct: float = 0.0
    minimum_sustainable_pct: float = 0.0
    holdings: list[SFDRHolding] = field(default_factory=list)
    # PAI indicator values (dict: indicator_id -> value)
    pai_values: dict[str, float] = field(default_factory=dict)
    prior_pai_values: dict[str, float] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Data Classes — Outputs
# ---------------------------------------------------------------------------

@dataclass
class TopInvestment:
    """Top holding for SFDR template."""
    rank: int
    security_name: str
    isin: Optional[str]
    weight_pct: float
    sector: str
    country: str


@dataclass
class ProportionBreakdown:
    """SFDR proportion of investments breakdown."""
    taxonomy_aligned_pct: float
    other_environmental_pct: float
    social_pct: float
    not_sustainable_pct: float
    # Within taxonomy-aligned
    taxonomy_env_objective_1_pct: float  # Climate change mitigation
    taxonomy_env_objective_2_pct: float  # Climate change adaptation
    taxonomy_other_objectives_pct: float  # Water, circular, pollution, biodiversity


@dataclass
class SectorBreakdown:
    """Sector allocation for SFDR template."""
    sector: str
    weight_pct: float
    taxonomy_aligned_pct: float
    sustainable_pct: float


@dataclass
class GeographyBreakdown:
    """Geographic allocation for SFDR template."""
    country: str
    weight_pct: float


@dataclass
class PAISummaryRow:
    """PAI indicator row for periodic report."""
    indicator_id: str
    indicator_name: str
    current_value: float
    prior_value: Optional[float]
    yoy_change: Optional[float]
    unit: str


@dataclass
class SFDRPeriodicReport:
    """Complete SFDR periodic report data."""
    fund_id: str
    fund_name: str
    sfdr_classification: str
    reporting_period: str
    fund_type: str
    reference_benchmark: Optional[str]
    aum: float
    holdings_count: int

    # Promoted characteristics
    promoted_characteristics: list[str]
    esg_strategy: str

    # Proportion of investments (Art.8 template core)
    proportion: ProportionBreakdown

    # Minimum commitments met?
    minimum_taxonomy_pct: float
    actual_taxonomy_pct: float
    taxonomy_target_met: bool
    minimum_sustainable_pct: float
    actual_sustainable_pct: float
    sustainable_target_met: bool

    # Top investments
    top_investments: list[TopInvestment]

    # Sector breakdown
    sector_breakdown: list[SectorBreakdown]

    # Geography breakdown
    geography_breakdown: list[GeographyBreakdown]

    # PAI summary
    pai_summary: list[PAISummaryRow]

    # Sustainability indicators
    avg_esg_score: float
    waci: float
    dnsh_compliant_pct: float

    # Applicable sections
    applicable_sections: list[str]

    # Compliance flags
    is_art8_compliant: bool
    is_art9_compliant: bool
    compliance_issues: list[str]


# ---------------------------------------------------------------------------
# PAI indicator reference (subset for report)
# ---------------------------------------------------------------------------

PAI_INDICATOR_NAMES = {
    "PAI_1": ("GHG Emissions Scope 1", "tCO2e"),
    "PAI_2": ("GHG Emissions Scope 2", "tCO2e"),
    "PAI_3": ("GHG Emissions Scope 3", "tCO2e"),
    "PAI_4": ("Carbon Footprint", "tCO2e/MEUR invested"),
    "PAI_5": ("GHG Intensity (WACI)", "tCO2e/MEUR revenue"),
    "PAI_6": ("Fossil Fuel Exposure", "%"),
    "PAI_7": ("Non-Renewable Energy Share", "%"),
    "PAI_10": ("Water Emissions", "tonnes"),
    "PAI_11": ("Hazardous Waste", "tonnes"),
    "PAI_12": ("UNGC/OECD Violations", "%"),
    "PAI_14": ("Board Gender Diversity", "%"),
    "PAI_15": ("Controversial Weapons", "%"),
}


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class SFDRReportGenerator:
    """Generate SFDR periodic disclosure data."""

    def generate(self, fund: SFDRFundInput) -> SFDRPeriodicReport:
        """Generate complete SFDR periodic report data."""
        holdings = fund.holdings

        # Proportion breakdown
        proportion = self._calculate_proportions(holdings)

        # Top investments (sorted by weight, top 15)
        sorted_h = sorted(holdings, key=lambda h: h.weight_pct, reverse=True)
        top_investments = [
            TopInvestment(
                rank=i + 1, security_name=h.security_name,
                isin=h.isin, weight_pct=round(h.weight_pct, 2),
                sector=h.sector, country=h.country,
            )
            for i, h in enumerate(sorted_h[:15])
        ]

        # Sector breakdown
        sectors = self._sector_breakdown(holdings)

        # Geography breakdown
        geo = self._geography_breakdown(holdings)

        # PAI summary
        pai_summary = self._pai_summary(fund.pai_values, fund.prior_pai_values)

        # Sustainability indicators
        total_weight = sum(h.weight_pct for h in holdings)
        waci = sum(h.weight_pct / 100.0 * h.carbon_intensity for h in holdings)
        avg_esg = sum(h.weight_pct / 100.0 * h.esg_score for h in holdings)
        dnsh_wt = sum(h.weight_pct for h in holdings if h.dnsh_compliant)
        dnsh_pct = dnsh_wt / total_weight * 100 if total_weight > 0 else 0.0

        # Target compliance
        actual_tax = proportion.taxonomy_aligned_pct
        actual_sus = (proportion.taxonomy_aligned_pct +
                      proportion.other_environmental_pct +
                      proportion.social_pct)
        tax_met = actual_tax >= fund.minimum_taxonomy_pct
        sus_met = actual_sus >= fund.minimum_sustainable_pct

        # Applicable sections
        if fund.sfdr_classification in ("art9",):
            sections = ART9_SECTIONS
        elif fund.sfdr_classification in ("art8", "art8plus"):
            sections = ART8_SECTIONS
        else:
            sections = []

        # Compliance checks
        issues = []
        art8_ok = True
        art9_ok = True

        if fund.sfdr_classification in ("art8", "art8plus", "art9"):
            if not tax_met:
                issues.append(
                    f"Taxonomy alignment {actual_tax:.1f}% below minimum {fund.minimum_taxonomy_pct:.1f}%"
                )
            if not sus_met:
                issues.append(
                    f"Sustainable investment {actual_sus:.1f}% below minimum {fund.minimum_sustainable_pct:.1f}%"
                )

        if fund.sfdr_classification == "art9":
            # Art.9 requires all investments sustainable (some flexibility for hedging/cash)
            if actual_sus < 90.0:
                issues.append(
                    f"Art.9 fund: sustainable investment {actual_sus:.1f}% below 90% expected"
                )
                art9_ok = False

        if issues:
            art8_ok = False

        return SFDRPeriodicReport(
            fund_id=fund.fund_id,
            fund_name=fund.fund_name,
            sfdr_classification=fund.sfdr_classification,
            reporting_period=fund.reporting_period,
            fund_type=fund.fund_type,
            reference_benchmark=fund.reference_benchmark,
            aum=round(fund.aum, 2),
            holdings_count=len(holdings),
            promoted_characteristics=fund.promoted_characteristics,
            esg_strategy=fund.esg_strategy,
            proportion=proportion,
            minimum_taxonomy_pct=fund.minimum_taxonomy_pct,
            actual_taxonomy_pct=round(actual_tax, 2),
            taxonomy_target_met=tax_met,
            minimum_sustainable_pct=fund.minimum_sustainable_pct,
            actual_sustainable_pct=round(actual_sus, 2),
            sustainable_target_met=sus_met,
            top_investments=top_investments,
            sector_breakdown=sectors,
            geography_breakdown=geo,
            pai_summary=pai_summary,
            avg_esg_score=round(avg_esg, 2),
            waci=round(waci, 4),
            dnsh_compliant_pct=round(dnsh_pct, 2),
            applicable_sections=sections,
            is_art8_compliant=art8_ok,
            is_art9_compliant=art9_ok,
            compliance_issues=issues,
        )

    # -------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------

    def _calculate_proportions(self, holdings: list[SFDRHolding]) -> ProportionBreakdown:
        """Calculate SFDR proportion of investments breakdown."""
        total_weight = sum(h.weight_pct for h in holdings) or 1.0

        tax_wt = sum(h.weight_pct * h.taxonomy_aligned_pct / 100.0 for h in holdings)
        env_wt = sum(h.weight_pct * h.sustainable_environmental_pct / 100.0 for h in holdings)
        soc_wt = sum(h.weight_pct * h.sustainable_social_pct / 100.0 for h in holdings)

        tax_pct = tax_wt / total_weight * 100
        env_pct = env_wt / total_weight * 100
        soc_pct = soc_wt / total_weight * 100
        not_sus = max(0, 100.0 - tax_pct - env_pct - soc_pct)

        # Simplified: split taxonomy across objectives 60/30/10
        return ProportionBreakdown(
            taxonomy_aligned_pct=round(tax_pct, 2),
            other_environmental_pct=round(env_pct, 2),
            social_pct=round(soc_pct, 2),
            not_sustainable_pct=round(not_sus, 2),
            taxonomy_env_objective_1_pct=round(tax_pct * 0.6, 2),
            taxonomy_env_objective_2_pct=round(tax_pct * 0.3, 2),
            taxonomy_other_objectives_pct=round(tax_pct * 0.1, 2),
        )

    def _sector_breakdown(self, holdings: list[SFDRHolding]) -> list[SectorBreakdown]:
        """Aggregate holdings by sector."""
        sectors: dict[str, dict] = {}
        for h in holdings:
            if h.sector not in sectors:
                sectors[h.sector] = {"weight": 0.0, "tax_wt": 0.0, "sus_wt": 0.0}
            sectors[h.sector]["weight"] += h.weight_pct
            sectors[h.sector]["tax_wt"] += h.weight_pct * h.taxonomy_aligned_pct / 100.0
            sus = h.taxonomy_aligned_pct + h.sustainable_environmental_pct + h.sustainable_social_pct
            sectors[h.sector]["sus_wt"] += h.weight_pct * min(sus, 100) / 100.0

        result = []
        for s, data in sorted(sectors.items(), key=lambda x: -x[1]["weight"]):
            w = data["weight"]
            result.append(SectorBreakdown(
                sector=s,
                weight_pct=round(w, 2),
                taxonomy_aligned_pct=round(data["tax_wt"] / w * 100, 2) if w > 0 else 0.0,
                sustainable_pct=round(data["sus_wt"] / w * 100, 2) if w > 0 else 0.0,
            ))
        return result

    def _geography_breakdown(self, holdings: list[SFDRHolding]) -> list[GeographyBreakdown]:
        """Aggregate holdings by country."""
        countries: dict[str, float] = {}
        for h in holdings:
            countries[h.country] = countries.get(h.country, 0) + h.weight_pct

        return [
            GeographyBreakdown(country=c, weight_pct=round(w, 2))
            for c, w in sorted(countries.items(), key=lambda x: -x[1])
        ]

    def _pai_summary(
        self, current: dict[str, float], prior: dict[str, float]
    ) -> list[PAISummaryRow]:
        """Generate PAI summary rows with YoY comparison."""
        rows = []
        for pid, (name, unit) in PAI_INDICATOR_NAMES.items():
            curr = current.get(pid)
            if curr is None:
                continue
            prev = prior.get(pid)
            yoy = None
            if prev is not None and prev != 0:
                yoy = round((curr - prev) / abs(prev) * 100, 2)
            rows.append(PAISummaryRow(
                indicator_id=pid,
                indicator_name=name,
                current_value=round(curr, 4),
                prior_value=round(prev, 4) if prev is not None else None,
                yoy_change=yoy,
                unit=unit,
            ))
        return rows
