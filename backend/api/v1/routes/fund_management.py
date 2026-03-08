"""
API Routes: Fund Management
============================
POST /api/v1/fund-management/analyse         — Full fund analytics
POST /api/v1/fund-management/holdings-upload  — Upload holdings data
GET  /api/v1/fund-management/sfdr-summary     — SFDR classification reference
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from services.fund_structure_engine import (
    FundStructureEngine,
    FundDefinition,
    Holding,
    BenchmarkHolding,
    ShareClass,
    Investor,
)

router = APIRouter(prefix="/api/v1/fund-management", tags=["Fund Management"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class HoldingInput(BaseModel):
    holding_id: str
    security_name: str
    isin: Optional[str] = None
    ticker: Optional[str] = None
    asset_class: str = "equity"
    sector: str = "Other"
    country: str = "US"
    weight_pct: float = Field(0, ge=0, le=100)
    market_value: float = Field(0, ge=0)
    acquisition_cost: float = Field(0, ge=0)
    quantity: float = 0
    carbon_intensity: float = Field(0, ge=0)
    esg_score: float = Field(0, ge=0, le=100)
    taxonomy_aligned_pct: float = Field(0, ge=0, le=100)
    dnsh_compliant: bool = True
    exclusion_flag: bool = False
    exclusion_reason: Optional[str] = None


class BenchmarkHoldingInput(BaseModel):
    security_name: str
    isin: Optional[str] = None
    sector: str = "Other"
    country: str = "US"
    weight_pct: float = Field(0, ge=0, le=100)
    carbon_intensity: float = Field(0, ge=0)
    esg_score: float = Field(0, ge=0, le=100)


class ShareClassInput(BaseModel):
    class_id: str
    class_name: str
    isin: Optional[str] = None
    currency: str = "EUR"
    nav_per_share: float = Field(0, ge=0)
    total_shares: float = Field(0, ge=0)
    ter_pct: float = Field(0, ge=0)
    management_fee_pct: float = Field(0, ge=0)
    performance_fee_pct: float = Field(0, ge=0)
    distribution_type: str = "acc"


class InvestorInput(BaseModel):
    investor_id: str
    name: str
    investor_type: str = "institutional"
    commitment: float = Field(0, ge=0)
    called: float = Field(0, ge=0)
    distributed: float = Field(0, ge=0)
    nav_share: float = Field(0, ge=0)
    ownership_pct: float = Field(0, ge=0, le=100)


class FundAnalysisRequest(BaseModel):
    fund_id: str
    fund_name: str
    sfdr_classification: str = Field("art8", pattern=r"^(art6|art8|art8plus|art9)$")
    fund_type: str = "ucits"
    base_currency: str = "EUR"
    aum: float = Field(0, ge=0)
    benchmark_index: Optional[str] = None
    esg_strategy: str = "integration"
    minimum_taxonomy_pct: float = Field(0, ge=0, le=100)
    minimum_sustainable_pct: float = Field(0, ge=0, le=100)
    holdings: list[HoldingInput] = Field(default_factory=list)
    benchmark_holdings: list[BenchmarkHoldingInput] = Field(default_factory=list)
    share_classes: list[ShareClassInput] = Field(default_factory=list)
    investors: list[InvestorInput] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Converters
# ---------------------------------------------------------------------------

def _to_fund(req: FundAnalysisRequest) -> FundDefinition:
    return FundDefinition(
        fund_id=req.fund_id,
        fund_name=req.fund_name,
        sfdr_classification=req.sfdr_classification,
        fund_type=req.fund_type,
        base_currency=req.base_currency,
        aum=req.aum,
        benchmark_index=req.benchmark_index,
        esg_strategy=req.esg_strategy,
        minimum_taxonomy_pct=req.minimum_taxonomy_pct,
        minimum_sustainable_pct=req.minimum_sustainable_pct,
        holdings=[Holding(
            holding_id=h.holding_id, security_name=h.security_name,
            isin=h.isin, ticker=h.ticker, asset_class=h.asset_class,
            sector=h.sector, country=h.country, weight_pct=h.weight_pct,
            market_value=h.market_value, acquisition_cost=h.acquisition_cost,
            quantity=h.quantity, carbon_intensity=h.carbon_intensity,
            esg_score=h.esg_score, taxonomy_aligned_pct=h.taxonomy_aligned_pct,
            dnsh_compliant=h.dnsh_compliant, exclusion_flag=h.exclusion_flag,
            exclusion_reason=h.exclusion_reason,
        ) for h in req.holdings],
        benchmark_holdings=[BenchmarkHolding(
            security_name=b.security_name, isin=b.isin,
            sector=b.sector, country=b.country, weight_pct=b.weight_pct,
            carbon_intensity=b.carbon_intensity, esg_score=b.esg_score,
        ) for b in req.benchmark_holdings],
        share_classes=[ShareClass(
            class_id=sc.class_id, class_name=sc.class_name,
            isin=sc.isin, currency=sc.currency,
            nav_per_share=sc.nav_per_share, total_shares=sc.total_shares,
            ter_pct=sc.ter_pct, management_fee_pct=sc.management_fee_pct,
            performance_fee_pct=sc.performance_fee_pct,
            distribution_type=sc.distribution_type,
        ) for sc in req.share_classes],
        investors=[Investor(
            investor_id=inv.investor_id, name=inv.name,
            investor_type=inv.investor_type,
            commitment=inv.commitment, called=inv.called,
            distributed=inv.distributed, nav_share=inv.nav_share,
            ownership_pct=inv.ownership_pct,
        ) for inv in req.investors],
    )


# ---------------------------------------------------------------------------
# Serialisers
# ---------------------------------------------------------------------------

def _ser_sector(s) -> dict:
    return {
        "sector": s.sector,
        "portfolio_weight_pct": s.portfolio_weight_pct,
        "benchmark_weight_pct": s.benchmark_weight_pct,
        "active_weight_pct": s.active_weight_pct,
        "portfolio_carbon_intensity": s.portfolio_carbon_intensity,
        "benchmark_carbon_intensity": s.benchmark_carbon_intensity,
    }


def _ser_result(r) -> dict:
    return {
        "fund_id": r.fund_id,
        "fund_name": r.fund_name,
        "sfdr_classification": r.sfdr_classification,
        "total_aum": r.total_aum,
        "total_nav": r.total_nav,
        "holdings_count": r.holdings_count,
        "asset_class_breakdown": r.asset_class_breakdown,
        "waci": r.waci,
        "carbon_footprint": r.carbon_footprint,
        "total_financed_emissions": r.total_financed_emissions,
        "avg_esg_score": r.avg_esg_score,
        "taxonomy_aligned_pct": r.taxonomy_aligned_pct,
        "sustainable_investment_pct": r.sustainable_investment_pct,
        "dnsh_compliant_pct": r.dnsh_compliant_pct,
        "benchmark_waci": r.benchmark_waci,
        "waci_vs_benchmark": r.waci_vs_benchmark,
        "benchmark_esg_score": r.benchmark_esg_score,
        "esg_delta_vs_benchmark": r.esg_delta_vs_benchmark,
        "active_share_pct": r.active_share_pct,
        "tracking_error_est": r.tracking_error_est,
        "concentration_top10_pct": r.concentration_top10_pct,
        "sector_allocations": [_ser_sector(s) for s in r.sector_allocations],
        "exclusion_breach_count": r.exclusion_breach_count,
        "exclusion_breaches": r.exclusion_breaches,
        "total_commitment": r.total_commitment,
        "total_called": r.total_called,
        "total_distributed": r.total_distributed,
        "fund_dpi": r.fund_dpi,
        "fund_tvpi": r.fund_tvpi,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/analyse")
def analyse_fund(req: FundAnalysisRequest):
    """Run full fund-level analytics: carbon, ESG, benchmark, LP."""
    engine = FundStructureEngine()
    fund = _to_fund(req)
    result = engine.analyse_fund(fund)
    return _ser_result(result)


@router.get("/sfdr-summary")
def get_sfdr_summary():
    """Return SFDR classification reference data."""
    return {
        "classifications": {
            "art6": {
                "name": "Article 6",
                "description": "No ESG characteristics promoted. Basic sustainability risk disclosure.",
                "taxonomy_disclosure": "Not required",
            },
            "art8": {
                "name": "Article 8",
                "description": "Promotes environmental or social characteristics.",
                "taxonomy_disclosure": "Required (proportion of taxonomy-aligned investments)",
            },
            "art8plus": {
                "name": "Article 8+",
                "description": "Art.8 fund that also makes sustainable investments.",
                "taxonomy_disclosure": "Required (enhanced)",
            },
            "art9": {
                "name": "Article 9",
                "description": "Sustainable investment as its objective.",
                "taxonomy_disclosure": "Required (all investments must be sustainable)",
            },
        },
        "esg_strategies": [
            "exclusion", "best_in_class", "integration",
            "impact", "engagement", "thematic",
        ],
    }
