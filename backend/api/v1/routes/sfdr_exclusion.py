"""
API Routes: SFDR Report + Exclusion List
==========================================
POST /api/v1/sfdr-compliance/periodic-report   — Generate SFDR periodic report
POST /api/v1/sfdr-compliance/screen            — Screen holdings against exclusions
GET  /api/v1/sfdr-compliance/exclusion-rules   — Exclusion rule reference
GET  /api/v1/sfdr-compliance/pai-reference     — PAI indicator reference
"""
from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from typing import Optional

from services.sfdr_report_generator import (
    SFDRReportGenerator,
    SFDRFundInput,
    SFDRHolding,
    PAI_INDICATOR_NAMES,
    ART8_SECTIONS,
    ART9_SECTIONS,
)
from services.exclusion_list_engine import (
    ExclusionListEngine,
    HoldingScreenInput,
    CustomExclusionRule,
    DEFAULT_EXCLUSION_RULES,
)

router = APIRouter(prefix="/api/v1/sfdr-compliance", tags=["SFDR Compliance & Exclusions"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class SFDRHoldingInput(BaseModel):
    holding_id: str
    security_name: str
    isin: Optional[str] = None
    sector: str = "Other"
    country: str = "US"
    weight_pct: float = Field(0, ge=0, le=100)
    market_value: float = Field(0, ge=0)
    taxonomy_aligned_pct: float = Field(0, ge=0, le=100)
    sustainable_environmental_pct: float = Field(0, ge=0, le=100)
    sustainable_social_pct: float = Field(0, ge=0, le=100)
    esg_score: float = Field(0, ge=0, le=100)
    dnsh_compliant: bool = True
    carbon_intensity: float = Field(0, ge=0)


class SFDRReportRequest(BaseModel):
    fund_id: str
    fund_name: str
    sfdr_classification: str = Field("art8", pattern=r"^(art6|art8|art8plus|art9)$")
    fund_type: str = "ucits"
    reporting_period: str = ""
    reference_benchmark: Optional[str] = None
    aum: float = Field(0, ge=0)
    promoted_characteristics: list[str] = Field(default_factory=list)
    esg_strategy: str = "integration"
    minimum_taxonomy_pct: float = Field(0, ge=0, le=100)
    minimum_sustainable_pct: float = Field(0, ge=0, le=100)
    holdings: list[SFDRHoldingInput] = Field(default_factory=list)
    pai_values: dict[str, float] = Field(default_factory=dict)
    prior_pai_values: dict[str, float] = Field(default_factory=dict)


class ScreeningHoldingInput(BaseModel):
    holding_id: str
    security_name: str
    isin: Optional[str] = None
    weight_pct: float = Field(0, ge=0, le=100)
    controversial_weapons_revenue_pct: float = Field(0, ge=0, le=100)
    tobacco_revenue_pct: float = Field(0, ge=0, le=100)
    thermal_coal_revenue_pct: float = Field(0, ge=0, le=100)
    coal_power_generation_pct: float = Field(0, ge=0, le=100)
    arctic_oil_revenue_pct: float = Field(0, ge=0, le=100)
    oil_sands_revenue_pct: float = Field(0, ge=0, le=100)
    nuclear_weapons_involved: bool = False
    ungc_violation: bool = False
    custom_exclusion_flags: dict[str, bool] = Field(default_factory=dict)


class CustomRuleInput(BaseModel):
    rule_id: str
    name: str
    description: str
    flag_key: str
    applies_to_sfdr: list[str] = Field(default_factory=lambda: ["art8", "art8plus", "art9"])


class ScreeningRequest(BaseModel):
    fund_id: str
    fund_name: str
    sfdr_classification: str = Field("art8", pattern=r"^(art6|art8|art8plus|art9)$")
    holdings: list[ScreeningHoldingInput] = Field(..., min_length=1)
    custom_rules: list[CustomRuleInput] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Converters
# ---------------------------------------------------------------------------

def _to_sfdr_holding(m: SFDRHoldingInput) -> SFDRHolding:
    return SFDRHolding(
        holding_id=m.holding_id, security_name=m.security_name,
        isin=m.isin, sector=m.sector, country=m.country,
        weight_pct=m.weight_pct, market_value=m.market_value,
        taxonomy_aligned_pct=m.taxonomy_aligned_pct,
        sustainable_environmental_pct=m.sustainable_environmental_pct,
        sustainable_social_pct=m.sustainable_social_pct,
        esg_score=m.esg_score, dnsh_compliant=m.dnsh_compliant,
        carbon_intensity=m.carbon_intensity,
    )


def _to_screen_holding(m: ScreeningHoldingInput) -> HoldingScreenInput:
    return HoldingScreenInput(
        holding_id=m.holding_id, security_name=m.security_name,
        isin=m.isin, weight_pct=m.weight_pct,
        controversial_weapons_revenue_pct=m.controversial_weapons_revenue_pct,
        tobacco_revenue_pct=m.tobacco_revenue_pct,
        thermal_coal_revenue_pct=m.thermal_coal_revenue_pct,
        coal_power_generation_pct=m.coal_power_generation_pct,
        arctic_oil_revenue_pct=m.arctic_oil_revenue_pct,
        oil_sands_revenue_pct=m.oil_sands_revenue_pct,
        nuclear_weapons_involved=m.nuclear_weapons_involved,
        ungc_violation=m.ungc_violation,
        custom_exclusion_flags=m.custom_exclusion_flags,
    )


# ---------------------------------------------------------------------------
# Serialisers
# ---------------------------------------------------------------------------

def _ser_top(t) -> dict:
    return {
        "rank": t.rank, "security_name": t.security_name,
        "isin": t.isin, "weight_pct": t.weight_pct,
        "sector": t.sector, "country": t.country,
    }


def _ser_breach(b) -> dict:
    return {
        "holding_id": b.holding_id, "security_name": b.security_name,
        "isin": b.isin, "weight_pct": b.weight_pct,
        "category": b.category, "category_name": b.category_name,
        "rule_description": b.rule_description,
        "actual_exposure": b.actual_exposure,
        "threshold": b.threshold, "severity": b.severity,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/periodic-report")
def generate_periodic_report(req: SFDRReportRequest):
    """Generate SFDR Art.8/Art.9 periodic disclosure report data."""
    gen = SFDRReportGenerator()
    fund_input = SFDRFundInput(
        fund_id=req.fund_id, fund_name=req.fund_name,
        sfdr_classification=req.sfdr_classification,
        fund_type=req.fund_type, reporting_period=req.reporting_period,
        reference_benchmark=req.reference_benchmark,
        aum=req.aum, promoted_characteristics=req.promoted_characteristics,
        esg_strategy=req.esg_strategy,
        minimum_taxonomy_pct=req.minimum_taxonomy_pct,
        minimum_sustainable_pct=req.minimum_sustainable_pct,
        holdings=[_to_sfdr_holding(h) for h in req.holdings],
        pai_values=req.pai_values,
        prior_pai_values=req.prior_pai_values,
    )
    r = gen.generate(fund_input)
    return {
        "fund_id": r.fund_id, "fund_name": r.fund_name,
        "sfdr_classification": r.sfdr_classification,
        "reporting_period": r.reporting_period,
        "aum": r.aum, "holdings_count": r.holdings_count,
        "promoted_characteristics": r.promoted_characteristics,
        "proportion": {
            "taxonomy_aligned_pct": r.proportion.taxonomy_aligned_pct,
            "other_environmental_pct": r.proportion.other_environmental_pct,
            "social_pct": r.proportion.social_pct,
            "not_sustainable_pct": r.proportion.not_sustainable_pct,
        },
        "taxonomy_target_met": r.taxonomy_target_met,
        "sustainable_target_met": r.sustainable_target_met,
        "actual_taxonomy_pct": r.actual_taxonomy_pct,
        "actual_sustainable_pct": r.actual_sustainable_pct,
        "top_investments": [_ser_top(t) for t in r.top_investments],
        "sector_breakdown": [
            {"sector": s.sector, "weight_pct": s.weight_pct,
             "taxonomy_aligned_pct": s.taxonomy_aligned_pct,
             "sustainable_pct": s.sustainable_pct}
            for s in r.sector_breakdown
        ],
        "geography_breakdown": [
            {"country": g.country, "weight_pct": g.weight_pct}
            for g in r.geography_breakdown
        ],
        "pai_summary": [
            {"indicator_id": p.indicator_id, "indicator_name": p.indicator_name,
             "current_value": p.current_value, "prior_value": p.prior_value,
             "yoy_change": p.yoy_change, "unit": p.unit}
            for p in r.pai_summary
        ],
        "avg_esg_score": r.avg_esg_score,
        "waci": r.waci,
        "dnsh_compliant_pct": r.dnsh_compliant_pct,
        "is_art8_compliant": r.is_art8_compliant,
        "is_art9_compliant": r.is_art9_compliant,
        "compliance_issues": r.compliance_issues,
    }


@router.post("/screen")
def screen_holdings(req: ScreeningRequest):
    """Screen portfolio holdings against exclusion criteria."""
    custom = [
        CustomExclusionRule(
            rule_id=r.rule_id, name=r.name,
            description=r.description, flag_key=r.flag_key,
            applies_to_sfdr=r.applies_to_sfdr,
        )
        for r in req.custom_rules
    ]
    engine = ExclusionListEngine(custom_rules=custom)
    result = engine.screen_fund(
        fund_id=req.fund_id, fund_name=req.fund_name,
        sfdr_classification=req.sfdr_classification,
        holdings=[_to_screen_holding(h) for h in req.holdings],
    )
    return {
        "fund_id": result.fund_id, "fund_name": result.fund_name,
        "sfdr_classification": result.sfdr_classification,
        "total_holdings_screened": result.total_holdings_screened,
        "breach_count": result.breach_count,
        "breached_weight_pct": result.breached_weight_pct,
        "is_compliant": result.is_compliant,
        "hard_breach_count": result.hard_breach_count,
        "soft_breach_count": result.soft_breach_count,
        "category_summary": result.category_summary,
        "breaches": [_ser_breach(b) for b in result.breaches],
    }


@router.get("/exclusion-rules")
def get_exclusion_rules(
    sfdr: str = Query("art8", pattern=r"^(art6|art8|art8plus|art9)$"),
):
    """Return applicable exclusion rules for given SFDR classification."""
    engine = ExclusionListEngine()
    rules = engine.get_rules(sfdr)
    return {"sfdr_classification": sfdr, "rules": rules}


@router.get("/pai-reference")
def get_pai_reference():
    """Return PAI indicator reference data."""
    return {
        "pai_indicators": [
            {"id": pid, "name": name, "unit": unit}
            for pid, (name, unit) in PAI_INDICATOR_NAMES.items()
        ],
        "art8_report_sections": ART8_SECTIONS,
        "art9_report_sections": ART9_SECTIONS,
    }
