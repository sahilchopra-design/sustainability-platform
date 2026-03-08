"""
PE Deal Pipeline + ESG Screening Engine
========================================
Manages the PE/VC deal lifecycle from sourcing through exit, with integrated
ESG screening scorecard, red flag detection, sector risk heatmap, and
deal comparison analytics.

References:
- ILPA ESG Data Convergence Initiative — standardised PE ESG metrics
- UN PRI — Integrating ESG in PE due diligence
- SFDR Art.7 — PAI consideration for PE/VC funds
- TCFD — Transition and physical risk for unlisted assets
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class DealStage(str, Enum):
    SOURCING = "sourcing"
    SCREENING = "screening"
    DUE_DILIGENCE = "dd"
    INVESTMENT_COMMITTEE = "ic"
    CLOSING = "closing"
    PORTFOLIO = "portfolio"
    EXITED = "exited"


class DealType(str, Enum):
    BUYOUT = "buyout"
    GROWTH = "growth"
    VENTURE = "venture"
    SECONDARY = "secondary"
    CO_INVEST = "co_invest"


class ESGDimension(str, Enum):
    ENVIRONMENTAL = "environmental"
    SOCIAL = "social"
    GOVERNANCE = "governance"
    TRANSITION_RISK = "transition_risk"
    PHYSICAL_RISK = "physical_risk"


class RiskBand(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ---------------------------------------------------------------------------
# Reference Data — Sector ESG Risk Heatmap
# ---------------------------------------------------------------------------

SECTOR_ESG_RISK: dict[str, dict[str, int]] = {
    "Energy": {
        "environmental": 5, "social": 3, "governance": 3,
        "transition_risk": 5, "physical_risk": 4,
    },
    "Materials": {
        "environmental": 4, "social": 3, "governance": 3,
        "transition_risk": 4, "physical_risk": 3,
    },
    "Industrials": {
        "environmental": 3, "social": 3, "governance": 2,
        "transition_risk": 3, "physical_risk": 2,
    },
    "Consumer Discretionary": {
        "environmental": 2, "social": 3, "governance": 2,
        "transition_risk": 2, "physical_risk": 2,
    },
    "Consumer Staples": {
        "environmental": 3, "social": 3, "governance": 2,
        "transition_risk": 2, "physical_risk": 2,
    },
    "Healthcare": {
        "environmental": 2, "social": 4, "governance": 3,
        "transition_risk": 1, "physical_risk": 1,
    },
    "Financials": {
        "environmental": 1, "social": 2, "governance": 4,
        "transition_risk": 3, "physical_risk": 1,
    },
    "Technology": {
        "environmental": 2, "social": 3, "governance": 3,
        "transition_risk": 1, "physical_risk": 1,
    },
    "Telecommunications": {
        "environmental": 2, "social": 2, "governance": 3,
        "transition_risk": 1, "physical_risk": 2,
    },
    "Utilities": {
        "environmental": 4, "social": 2, "governance": 3,
        "transition_risk": 5, "physical_risk": 4,
    },
    "Real Estate": {
        "environmental": 3, "social": 2, "governance": 2,
        "transition_risk": 4, "physical_risk": 4,
    },
}

# ESG screening sub-dimensions per dimension
ESG_SUB_DIMENSIONS: dict[str, list[str]] = {
    "environmental": [
        "carbon_intensity", "resource_efficiency", "pollution_prevention", "biodiversity_impact",
    ],
    "social": [
        "labor_practices", "human_rights", "community_impact", "product_safety",
    ],
    "governance": [
        "board_structure", "anti_corruption", "data_privacy", "tax_transparency",
    ],
    "transition_risk": [
        "regulatory_exposure", "carbon_pricing_impact", "technology_disruption", "market_shift",
    ],
    "physical_risk": [
        "asset_location_hazard", "climate_hazard_exposure", "supply_chain_resilience", "insurance_availability",
    ],
}

# Red-flag sector keywords
HIGH_CARBON_SECTORS = {"Energy", "Utilities", "Materials"}


# ---------------------------------------------------------------------------
# Data Classes — Input
# ---------------------------------------------------------------------------

@dataclass
class DealInput:
    """Single PE deal for pipeline and ESG screening."""
    deal_id: str
    company_name: str
    sector: str = "Other"
    sub_sector: str = ""
    country: str = "US"
    stage: str = "sourcing"
    deal_type: str = "buyout"
    deal_size_eur: float = 0.0
    equity_ticket_eur: float = 0.0
    enterprise_value_eur: float = 0.0
    revenue_eur: float = 0.0
    ebitda_eur: float = 0.0
    entry_multiple: float = 0.0
    source: str = "proprietary"
    lead_partner: str = ""
    fund_id: str = ""

    # ESG screening inputs (1-5 per sub-dimension, 0 = not assessed)
    esg_scores: dict[str, dict[str, int]] = field(default_factory=dict)
    # e.g. {"environmental": {"carbon_intensity": 3, "resource_efficiency": 4, ...}, ...}

    # Red flag triggers
    has_transition_plan: bool = True
    ungc_violation: bool = False
    sanctions_hit: bool = False
    controversial_weapons: bool = False
    severe_environmental_incident: bool = False
    child_labor_risk: bool = False
    tax_haven_structure: bool = False


@dataclass
class ESGDimensionScore:
    """Aggregated score for one ESG dimension."""
    dimension: str
    sub_scores: dict[str, int]   # sub-dimension -> rating (1-5)
    avg_score: float             # average of sub-dimension ratings
    weight: float = 1.0
    assessed_count: int = 0
    max_possible: int = 5


@dataclass
class RedFlag:
    """Single red flag identified during screening."""
    flag_id: str
    severity: str         # "hard" (deal-breaker) / "soft" (requires mitigation)
    category: str
    description: str
    recommendation: str


# ---------------------------------------------------------------------------
# Data Classes — Output
# ---------------------------------------------------------------------------

@dataclass
class DealScreeningResult:
    """ESG screening result for a single deal."""
    deal_id: str
    company_name: str
    sector: str
    stage: str

    # Dimension scores
    dimension_scores: list[ESGDimensionScore]
    composite_esg_score: float       # Weighted average across dimensions (1-5)
    esg_risk_band: str               # low/medium/high/critical

    # Red flags
    red_flags: list[RedFlag]
    hard_flag_count: int
    soft_flag_count: int
    has_deal_breaker: bool

    # Sector context
    sector_risk: dict[str, int]      # Sector heatmap scores
    sector_overall_risk: int

    # Recommendation
    screening_recommendation: str    # "proceed" / "proceed_with_conditions" / "reject"
    conditions: list[str]


@dataclass
class DealComparisonRow:
    """Single deal row for side-by-side comparison."""
    deal_id: str
    company_name: str
    sector: str
    deal_size_eur: float
    entry_multiple: float
    composite_esg_score: float
    esg_risk_band: str
    red_flag_count: int
    has_deal_breaker: bool
    dimension_scores: dict[str, float]  # dimension -> avg score


@dataclass
class PipelineSummary:
    """Pipeline analytics summary."""
    total_deals: int
    deals_by_stage: dict[str, int]
    deals_by_sector: dict[str, int]
    avg_deal_size_eur: float
    avg_esg_score: float
    red_flag_deals: int
    deal_breaker_deals: int
    comparison_table: list[DealComparisonRow]
    sector_heatmap: list[dict]


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class PEDealEngine:
    """PE/VC deal pipeline + ESG screening engine."""

    def screen_deal(self, deal: DealInput) -> DealScreeningResult:
        """Run ESG screening on a single deal."""
        # 1. Score each ESG dimension
        dimension_scores = self._score_dimensions(deal)

        # 2. Composite score (equal-weighted across dimensions)
        composite = self._composite_score(dimension_scores)

        # 3. Risk band
        risk_band = self._risk_band(composite)

        # 4. Red flag detection
        red_flags = self._detect_red_flags(deal)
        hard = sum(1 for f in red_flags if f.severity == "hard")
        soft = sum(1 for f in red_flags if f.severity == "soft")

        # 5. Sector context
        sector_risk = SECTOR_ESG_RISK.get(deal.sector, {
            "environmental": 3, "social": 3, "governance": 3,
            "transition_risk": 3, "physical_risk": 3,
        })
        sector_overall = round(sum(sector_risk.values()) / max(len(sector_risk), 1))

        # 6. Recommendation
        recommendation, conditions = self._recommendation(
            composite, risk_band, red_flags, hard,
        )

        return DealScreeningResult(
            deal_id=deal.deal_id,
            company_name=deal.company_name,
            sector=deal.sector,
            stage=deal.stage,
            dimension_scores=dimension_scores,
            composite_esg_score=round(composite, 2),
            esg_risk_band=risk_band,
            red_flags=red_flags,
            hard_flag_count=hard,
            soft_flag_count=soft,
            has_deal_breaker=hard > 0,
            sector_risk=sector_risk,
            sector_overall_risk=sector_overall,
            screening_recommendation=recommendation,
            conditions=conditions,
        )

    def compare_deals(self, deals: list[DealInput]) -> list[DealComparisonRow]:
        """Generate side-by-side comparison table for IC discussion."""
        rows = []
        for d in deals:
            result = self.screen_deal(d)
            dim_map = {ds.dimension: ds.avg_score for ds in result.dimension_scores}
            rows.append(DealComparisonRow(
                deal_id=d.deal_id,
                company_name=d.company_name,
                sector=d.sector,
                deal_size_eur=d.deal_size_eur,
                entry_multiple=d.entry_multiple,
                composite_esg_score=result.composite_esg_score,
                esg_risk_band=result.esg_risk_band,
                red_flag_count=result.hard_flag_count + result.soft_flag_count,
                has_deal_breaker=result.has_deal_breaker,
                dimension_scores=dim_map,
            ))
        return rows

    def pipeline_summary(self, deals: list[DealInput]) -> PipelineSummary:
        """Aggregate pipeline analytics."""
        if not deals:
            return PipelineSummary(
                total_deals=0, deals_by_stage={}, deals_by_sector={},
                avg_deal_size_eur=0, avg_esg_score=0,
                red_flag_deals=0, deal_breaker_deals=0,
                comparison_table=[], sector_heatmap=[],
            )

        by_stage: dict[str, int] = {}
        by_sector: dict[str, int] = {}
        total_size = 0.0
        total_esg = 0.0
        rf_deals = 0
        db_deals = 0
        comparisons = []

        for d in deals:
            by_stage[d.stage] = by_stage.get(d.stage, 0) + 1
            by_sector[d.sector] = by_sector.get(d.sector, 0) + 1
            total_size += d.deal_size_eur

            result = self.screen_deal(d)
            total_esg += result.composite_esg_score
            if result.red_flags:
                rf_deals += 1
            if result.has_deal_breaker:
                db_deals += 1

            dim_map = {ds.dimension: ds.avg_score for ds in result.dimension_scores}
            comparisons.append(DealComparisonRow(
                deal_id=d.deal_id,
                company_name=d.company_name,
                sector=d.sector,
                deal_size_eur=d.deal_size_eur,
                entry_multiple=d.entry_multiple,
                composite_esg_score=result.composite_esg_score,
                esg_risk_band=result.esg_risk_band,
                red_flag_count=len(result.red_flags),
                has_deal_breaker=result.has_deal_breaker,
                dimension_scores=dim_map,
            ))

        # Sector heatmap
        heatmap = []
        for sector, risks in SECTOR_ESG_RISK.items():
            overall = round(sum(risks.values()) / len(risks))
            heatmap.append({
                "sector": sector,
                **risks,
                "overall_risk": overall,
            })

        n = len(deals)
        return PipelineSummary(
            total_deals=n,
            deals_by_stage=by_stage,
            deals_by_sector=by_sector,
            avg_deal_size_eur=round(total_size / n, 2),
            avg_esg_score=round(total_esg / n, 2),
            red_flag_deals=rf_deals,
            deal_breaker_deals=db_deals,
            comparison_table=comparisons,
            sector_heatmap=heatmap,
        )

    def get_sector_heatmap(self) -> list[dict]:
        """Return sector ESG risk heatmap reference data."""
        result = []
        for sector, risks in SECTOR_ESG_RISK.items():
            overall = round(sum(risks.values()) / len(risks))
            result.append({
                "sector": sector,
                **risks,
                "overall_risk": overall,
            })
        return result

    def get_sub_dimensions(self) -> dict[str, list[str]]:
        """Return ESG sub-dimensions for screening scorecard."""
        return ESG_SUB_DIMENSIONS.copy()

    # -------------------------------------------------------------------
    # Dimension Scoring
    # -------------------------------------------------------------------

    def _score_dimensions(self, deal: DealInput) -> list[ESGDimensionScore]:
        """Score each ESG dimension from deal's sub-dimension ratings."""
        scores = []
        for dim in ESGDimension:
            dim_key = dim.value
            sub_dims = ESG_SUB_DIMENSIONS.get(dim_key, [])
            deal_dim_scores = deal.esg_scores.get(dim_key, {})

            sub_scores: dict[str, int] = {}
            assessed = 0
            total = 0
            for sd in sub_dims:
                rating = deal_dim_scores.get(sd, 0)
                sub_scores[sd] = rating
                if rating > 0:
                    assessed += 1
                    total += rating

            avg = total / assessed if assessed > 0 else 3.0  # Default to neutral if not assessed

            scores.append(ESGDimensionScore(
                dimension=dim_key,
                sub_scores=sub_scores,
                avg_score=round(avg, 2),
                assessed_count=assessed,
            ))

        return scores

    def _composite_score(self, dimension_scores: list[ESGDimensionScore]) -> float:
        """Equal-weighted composite across all dimensions. 1=best, 5=worst risk."""
        if not dimension_scores:
            return 3.0
        total = sum(ds.avg_score for ds in dimension_scores)
        return total / len(dimension_scores)

    def _risk_band(self, composite: float) -> str:
        """Map composite score to risk band. Lower score = lower risk."""
        if composite <= 2.0:
            return RiskBand.LOW.value
        elif composite <= 3.0:
            return RiskBand.MEDIUM.value
        elif composite <= 4.0:
            return RiskBand.HIGH.value
        else:
            return RiskBand.CRITICAL.value

    # -------------------------------------------------------------------
    # Red Flag Detection
    # -------------------------------------------------------------------

    def _detect_red_flags(self, deal: DealInput) -> list[RedFlag]:
        """Detect ESG red flags from deal attributes."""
        flags: list[RedFlag] = []

        # Hard flags (deal-breakers)
        if deal.controversial_weapons:
            flags.append(RedFlag(
                flag_id="RF_WEAPONS",
                severity="hard",
                category="controversial_weapons",
                description="Company involved in controversial weapons",
                recommendation="Reject — absolute exclusion under all ESG policies",
            ))

        if deal.sanctions_hit:
            flags.append(RedFlag(
                flag_id="RF_SANCTIONS",
                severity="hard",
                category="sanctions",
                description="Company or key persons on sanctions list",
                recommendation="Reject — legal prohibition",
            ))

        if deal.ungc_violation:
            flags.append(RedFlag(
                flag_id="RF_UNGC",
                severity="hard",
                category="ungc_violations",
                description="UN Global Compact principles violation identified",
                recommendation="Reject or require binding remediation plan pre-closing",
            ))

        if deal.child_labor_risk:
            flags.append(RedFlag(
                flag_id="RF_CHILD_LABOR",
                severity="hard",
                category="human_rights",
                description="Material child labor risk in supply chain",
                recommendation="Reject unless full supply chain audit + remediation confirmed",
            ))

        # Soft flags (require mitigation)
        if deal.sector in HIGH_CARBON_SECTORS and not deal.has_transition_plan:
            flags.append(RedFlag(
                flag_id="RF_NO_TRANSITION",
                severity="soft",
                category="transition_risk",
                description=f"High-carbon sector ({deal.sector}) without transition plan",
                recommendation="Require credible transition plan as condition precedent to closing",
            ))

        if deal.severe_environmental_incident:
            flags.append(RedFlag(
                flag_id="RF_ENV_INCIDENT",
                severity="soft",
                category="environmental",
                description="Severe environmental incident in recent history",
                recommendation="Commission independent environmental due diligence",
            ))

        if deal.tax_haven_structure:
            flags.append(RedFlag(
                flag_id="RF_TAX_HAVEN",
                severity="soft",
                category="governance",
                description="Corporate structure involves tax haven jurisdictions",
                recommendation="Review structure for BEPS compliance and reputational risk",
            ))

        # Score-based flags: any dimension with avg > 4.0 is high risk
        for dim_key, sub_scores in deal.esg_scores.items():
            assessed_vals = [v for v in sub_scores.values() if v > 0]
            if assessed_vals:
                avg = sum(assessed_vals) / len(assessed_vals)
                if avg > 4.0:
                    flags.append(RedFlag(
                        flag_id=f"RF_HIGH_{dim_key.upper()}",
                        severity="soft",
                        category=dim_key,
                        description=f"{dim_key.replace('_', ' ').title()} risk score is very high ({avg:.1f}/5)",
                        recommendation=f"Deep-dive ESG DD required on {dim_key.replace('_', ' ')} dimension",
                    ))

        return flags

    # -------------------------------------------------------------------
    # Recommendation
    # -------------------------------------------------------------------

    def _recommendation(
        self, composite: float, risk_band: str,
        red_flags: list[RedFlag], hard_count: int,
    ) -> tuple[str, list[str]]:
        """Generate screening recommendation."""
        conditions: list[str] = []

        if hard_count > 0:
            return "reject", [f.description for f in red_flags if f.severity == "hard"]

        if risk_band == RiskBand.CRITICAL.value:
            return "reject", ["Overall ESG risk is critical — composite score > 4.0"]

        soft_flags = [f for f in red_flags if f.severity == "soft"]
        if soft_flags or risk_band == RiskBand.HIGH.value:
            conditions = [f.recommendation for f in soft_flags]
            if risk_band == RiskBand.HIGH.value and not conditions:
                conditions.append("Enhanced ESG due diligence required before IC submission")
            return "proceed_with_conditions", conditions

        return "proceed", []
