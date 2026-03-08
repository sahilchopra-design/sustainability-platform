"""
PE Impact Measurement Framework
=================================
Implements SFDR/GIIN IRIS+ aligned impact measurement for PE/VC funds,
including SDG alignment, impact scoring, and additionality assessment.

References:
- GIIN IRIS+ Catalogue — impact measurement taxonomy
- IFC Operating Principles for Impact Management
- UN SDGs — Sustainable Development Goals mapping
- SFDR Art.9 — sustainable investment definition
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# SDG Definitions
# ---------------------------------------------------------------------------

SDG_DEFINITIONS: dict[int, dict] = {
    1: {"name": "No Poverty", "category": "social"},
    2: {"name": "Zero Hunger", "category": "social"},
    3: {"name": "Good Health and Well-Being", "category": "social"},
    4: {"name": "Quality Education", "category": "social"},
    5: {"name": "Gender Equality", "category": "social"},
    6: {"name": "Clean Water and Sanitation", "category": "environmental"},
    7: {"name": "Affordable and Clean Energy", "category": "environmental"},
    8: {"name": "Decent Work and Economic Growth", "category": "social"},
    9: {"name": "Industry, Innovation and Infrastructure", "category": "economic"},
    10: {"name": "Reduced Inequalities", "category": "social"},
    11: {"name": "Sustainable Cities and Communities", "category": "environmental"},
    12: {"name": "Responsible Consumption and Production", "category": "environmental"},
    13: {"name": "Climate Action", "category": "environmental"},
    14: {"name": "Life Below Water", "category": "environmental"},
    15: {"name": "Life on Land", "category": "environmental"},
    16: {"name": "Peace, Justice and Strong Institutions", "category": "governance"},
    17: {"name": "Partnerships for the Goals", "category": "governance"},
}

# Impact dimensions per IMP (Impact Management Project)
IMPACT_DIMENSIONS = ["what", "who", "how_much", "contribution", "risk"]


# ---------------------------------------------------------------------------
# Data Classes — Input
# ---------------------------------------------------------------------------

@dataclass
class CompanyImpactData:
    """Impact measurement data for a portfolio company."""
    company_id: str
    company_name: str
    sector: str
    primary_sdgs: list[int] = field(default_factory=list)
    secondary_sdgs: list[int] = field(default_factory=list)
    # Impact scores per dimension (1-5)
    impact_scores: dict[str, float] = field(default_factory=dict)
    # Quantitative impact metrics
    jobs_created: int = 0
    beneficiaries_reached: int = 0
    co2_avoided_tonnes: float = 0.0
    renewable_mwh_generated: float = 0.0
    # Qualitative
    theory_of_change: str = ""
    additionality_evidence: str = ""
    # Investment details
    invested_eur: float = 0.0
    current_nav_eur: float = 0.0


@dataclass
class FundImpactInput:
    """Full input for fund-level impact assessment."""
    fund_id: str
    fund_name: str
    fund_strategy: str = "impact"  # impact | esg_integrated | thematic
    sfdr_classification: str = "art9"
    companies: list[CompanyImpactData] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Data Classes — Output
# ---------------------------------------------------------------------------

@dataclass
class CompanyImpactScore:
    """Impact assessment result for a single company."""
    company_id: str
    company_name: str
    sector: str
    primary_sdgs: list[int]
    secondary_sdgs: list[int]
    sdg_names: list[str]
    impact_rating: str  # "high" | "medium" | "low" | "neutral"
    composite_impact_score: float  # 1-5
    dimension_scores: dict[str, float]  # Per IMP dimension
    quantitative_metrics: dict[str, float]
    additionality_rating: str  # "strong" | "moderate" | "weak"
    impact_multiple_of_money: float  # IMM = impact / EUR invested


@dataclass
class SDGContribution:
    """Fund-level SDG contribution summary."""
    sdg_number: int
    sdg_name: str
    category: str
    company_count: int
    total_invested_eur: float
    pct_of_fund: float


@dataclass
class FundImpactReport:
    """Fund-level impact measurement report."""
    fund_id: str
    fund_name: str
    fund_strategy: str
    sfdr_classification: str
    total_companies: int
    company_scores: list[CompanyImpactScore]
    sdg_contributions: list[SDGContribution]
    fund_impact_score: float  # Weighted average
    fund_impact_rating: str
    high_impact_count: int
    medium_impact_count: int
    low_impact_count: int
    total_jobs_created: int
    total_beneficiaries: int
    total_co2_avoided_tonnes: float
    total_renewable_mwh: float
    additionality_score: float
    impact_summary: str


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class PEImpactFramework:
    """Impact measurement engine for PE/VC funds."""

    def assess_company_impact(self, company: CompanyImpactData) -> CompanyImpactScore:
        """Assess impact for a single portfolio company."""
        # Score per IMP dimension
        dim_scores = {}
        for dim in IMPACT_DIMENSIONS:
            dim_scores[dim] = company.impact_scores.get(dim, 3.0)

        composite = round(sum(dim_scores.values()) / len(dim_scores), 2)

        # Impact rating
        if composite >= 4.0:
            rating = "high"
        elif composite >= 3.0:
            rating = "medium"
        elif composite >= 2.0:
            rating = "low"
        else:
            rating = "neutral"

        # Additionality
        add_score = company.impact_scores.get("contribution", 3.0)
        if add_score >= 4.0:
            add_rating = "strong"
        elif add_score >= 2.5:
            add_rating = "moderate"
        else:
            add_rating = "weak"

        # SDG names
        all_sdgs = company.primary_sdgs + company.secondary_sdgs
        sdg_names = [SDG_DEFINITIONS[s]["name"] for s in all_sdgs if s in SDG_DEFINITIONS]

        # Impact Multiple of Money (simplified)
        quant = {
            "jobs_created": company.jobs_created,
            "beneficiaries_reached": company.beneficiaries_reached,
            "co2_avoided_tonnes": company.co2_avoided_tonnes,
            "renewable_mwh_generated": company.renewable_mwh_generated,
        }

        imm = 0.0
        if company.invested_eur > 0:
            # EUR 100 of social value per beneficiary (simplified)
            social_value = company.beneficiaries_reached * 100 + company.co2_avoided_tonnes * 50
            imm = round(social_value / company.invested_eur, 4)

        return CompanyImpactScore(
            company_id=company.company_id,
            company_name=company.company_name,
            sector=company.sector,
            primary_sdgs=company.primary_sdgs,
            secondary_sdgs=company.secondary_sdgs,
            sdg_names=sdg_names,
            impact_rating=rating,
            composite_impact_score=composite,
            dimension_scores=dim_scores,
            quantitative_metrics=quant,
            additionality_rating=add_rating,
            impact_multiple_of_money=imm,
        )

    def assess_fund_impact(self, inp: FundImpactInput) -> FundImpactReport:
        """Assess impact across the entire fund."""
        if not inp.companies:
            return FundImpactReport(
                fund_id=inp.fund_id, fund_name=inp.fund_name,
                fund_strategy=inp.fund_strategy,
                sfdr_classification=inp.sfdr_classification,
                total_companies=0, company_scores=[],
                sdg_contributions=[], fund_impact_score=0,
                fund_impact_rating="neutral",
                high_impact_count=0, medium_impact_count=0, low_impact_count=0,
                total_jobs_created=0, total_beneficiaries=0,
                total_co2_avoided_tonnes=0, total_renewable_mwh=0,
                additionality_score=0, impact_summary="No portfolio companies.",
            )

        scores = [self.assess_company_impact(c) for c in inp.companies]

        # Weighted fund score by NAV
        total_nav = sum(c.current_nav_eur for c in inp.companies) or 1.0
        fund_score = sum(
            s.composite_impact_score * c.current_nav_eur
            for s, c in zip(scores, inp.companies)
        ) / total_nav
        fund_score = round(fund_score, 2)

        # Fund rating
        if fund_score >= 4.0:
            fund_rating = "high"
        elif fund_score >= 3.0:
            fund_rating = "medium"
        elif fund_score >= 2.0:
            fund_rating = "low"
        else:
            fund_rating = "neutral"

        # Counts
        high_ct = sum(1 for s in scores if s.impact_rating == "high")
        med_ct = sum(1 for s in scores if s.impact_rating == "medium")
        low_ct = sum(1 for s in scores if s.impact_rating in ("low", "neutral"))

        # Totals
        total_jobs = sum(c.jobs_created for c in inp.companies)
        total_benef = sum(c.beneficiaries_reached for c in inp.companies)
        total_co2 = sum(c.co2_avoided_tonnes for c in inp.companies)
        total_renew = sum(c.renewable_mwh_generated for c in inp.companies)

        # Additionality
        add_score = round(
            sum(s.dimension_scores.get("contribution", 3.0) for s in scores) / len(scores), 2
        )

        # SDG contributions
        sdg_map: dict[int, dict] = {}
        for c in inp.companies:
            for sdg in c.primary_sdgs + c.secondary_sdgs:
                if sdg not in sdg_map:
                    sdg_map[sdg] = {"count": 0, "invested": 0.0}
                sdg_map[sdg]["count"] += 1
                sdg_map[sdg]["invested"] += c.invested_eur

        total_invested = sum(c.invested_eur for c in inp.companies) or 1.0
        sdg_contributions = []
        for sdg_num in sorted(sdg_map.keys()):
            info = sdg_map[sdg_num]
            defn = SDG_DEFINITIONS.get(sdg_num, {"name": f"SDG {sdg_num}", "category": "other"})
            sdg_contributions.append(SDGContribution(
                sdg_number=sdg_num,
                sdg_name=defn["name"],
                category=defn["category"],
                company_count=info["count"],
                total_invested_eur=round(info["invested"], 2),
                pct_of_fund=round(info["invested"] / total_invested * 100, 1),
            ))

        summary = (
            f"{inp.fund_name} impact assessment: {len(scores)} companies scored. "
            f"Fund impact rating: {fund_rating} ({fund_score}/5.0). "
            f"{high_ct} high-impact, {med_ct} medium-impact companies. "
            f"Total CO2 avoided: {total_co2:,.0f} tCO2e. "
            f"SDGs addressed: {len(sdg_map)}."
        )

        return FundImpactReport(
            fund_id=inp.fund_id,
            fund_name=inp.fund_name,
            fund_strategy=inp.fund_strategy,
            sfdr_classification=inp.sfdr_classification,
            total_companies=len(scores),
            company_scores=scores,
            sdg_contributions=sdg_contributions,
            fund_impact_score=fund_score,
            fund_impact_rating=fund_rating,
            high_impact_count=high_ct,
            medium_impact_count=med_ct,
            low_impact_count=low_ct,
            total_jobs_created=total_jobs,
            total_beneficiaries=total_benef,
            total_co2_avoided_tonnes=total_co2,
            total_renewable_mwh=total_renew,
            additionality_score=add_score,
            impact_summary=summary,
        )

    def get_sdg_definitions(self) -> dict[int, dict]:
        """Return SDG reference data."""
        return SDG_DEFINITIONS

    def get_impact_dimensions(self) -> list[str]:
        """Return IMP impact dimensions."""
        return IMPACT_DIMENSIONS
