"""
Banking Risk API
==================
Endpoints for comprehensive banking risk analytics: Credit Risk (IFRS 9 ECL),
Liquidity Risk (LCR/NSFR), Market Risk (VaR/FRTB), Operational Risk (BIA/TSA),
AML/CFT Screening, and Capital Adequacy (Basel III/IV Pillar 1+2).
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from services.banking_risk_engine import BankingRiskEngine

router = APIRouter(prefix="/api/v1/banking-risk", tags=["Banking Risk"])

_engine = BankingRiskEngine()


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class CreditRiskRequest(BaseModel):
    total_exposure_eur: float = Field(10_000_000_000, description="Total loan book exposure (EUR)")
    portfolio_size: int = Field(5000, description="Number of counterparties/facilities")
    avg_rating: str = Field("BBB", description="Average credit rating (AAA-CCC)")
    collateral_type: str = Field("unsecured_senior", description="Dominant collateral type")
    avg_maturity_years: int = Field(3, description="Average remaining maturity (years)")
    stage2_pct: float = Field(8.0, description="% of book in IFRS 9 Stage 2")
    stage3_pct: float = Field(2.0, description="% of book in IFRS 9 Stage 3")
    warming_c: float = Field(1.5, description="Climate warming scenario (C) for overlay")


class LiquidityRiskRequest(BaseModel):
    hqla_holdings: Optional[dict[str, float]] = Field(None, description="HQLA by asset type (EUR). None = defaults")
    funding_sources: Optional[dict[str, float]] = Field(None, description="Funding by source type (EUR). None = defaults")
    asset_book: Optional[dict[str, float]] = Field(None, description="NSFR ASF sources (EUR). None = defaults")


class MarketRiskRequest(BaseModel):
    trading_book_eur: float = Field(5_000_000_000, description="Trading book size (EUR)")
    equity_exposure_eur: float = Field(1_000_000_000, description="Equity portfolio (EUR)")
    fx_exposure_eur: float = Field(2_000_000_000, description="Net FX open position (EUR)")
    interest_rate_dv01_eur: float = Field(5_000_000, description="DV01 sensitivity (EUR/bp)")
    portfolio_volatility_pct: float = Field(12.0, description="Annualised portfolio volatility (%)")
    stressed_volatility_pct: float = Field(25.0, description="Stressed volatility (%)")
    rate_shock_bps: int = Field(200, description="Interest rate shock for IRRBB (bps)")


class OperationalRiskRequest(BaseModel):
    gross_income_year1_eur: float = Field(8_000_000_000, description="Gross income year 1 (EUR)")
    gross_income_year2_eur: float = Field(7_500_000_000, description="Gross income year 2 (EUR)")
    gross_income_year3_eur: float = Field(8_200_000_000, description="Gross income year 3 (EUR)")
    business_line_income: Optional[dict[str, float]] = Field(None, description="Income by business line (EUR). None = auto-split")


class AMLRiskRequest(BaseModel):
    counterparty_countries: Optional[list[str]] = Field(None, description="ISO2 country codes. None = defaults")
    exposure_by_country: Optional[dict[str, float]] = Field(None, description="Exposure per country (EUR). None = defaults")


class CapitalAdequacyRequest(BaseModel):
    cet1_capital_eur: float = Field(25_000_000_000, description="CET1 capital (EUR)")
    at1_capital_eur: float = Field(5_000_000_000, description="Additional Tier 1 capital (EUR)")
    tier2_capital_eur: float = Field(8_000_000_000, description="Tier 2 capital (EUR)")
    credit_rwa_eur: float = Field(150_000_000_000, description="Credit risk RWA (EUR)")
    market_rwa_eur: float = Field(20_000_000_000, description="Market risk RWA (EUR)")
    operational_rwa_eur: float = Field(15_000_000_000, description="Operational risk RWA (EUR)")
    leverage_exposure_eur: float = Field(500_000_000_000, description="Leverage exposure measure (EUR)")
    countercyclical_buffer_pct: float = Field(0.5, description="Countercyclical buffer (%)")


class ComprehensiveRequest(BaseModel):
    entity_name: str = Field("BankCo", description="Bank name")
    total_exposure_eur: float = Field(200_000_000_000, description="Total loan book (EUR)")
    cet1_capital_eur: float = Field(25_000_000_000, description="CET1 capital (EUR)")
    trading_book_eur: float = Field(5_000_000_000, description="Trading book (EUR)")
    gross_income_eur: float = Field(8_000_000_000, description="Annual gross income (EUR)")
    warming_c: float = Field(1.5, description="Climate warming scenario (C)")


# ---------------------------------------------------------------------------
# Serialisers
# ---------------------------------------------------------------------------

def _ser_credit(r) -> dict:
    return {
        "portfolio_size": r.portfolio_size,
        "total_exposure_eur": r.total_exposure_eur,
        "weighted_avg_pd_pct": r.weighted_avg_pd_pct,
        "weighted_avg_lgd_pct": r.weighted_avg_lgd_pct,
        "avg_ead_eur": r.avg_ead_eur,
        "ecl_stage1_eur": r.ecl_stage1_eur,
        "ecl_stage2_eur": r.ecl_stage2_eur,
        "ecl_stage3_eur": r.ecl_stage3_eur,
        "total_ecl_eur": r.total_ecl_eur,
        "ecl_coverage_ratio_pct": r.ecl_coverage_ratio_pct,
        "climate_overlay_eur": r.climate_overlay_eur,
        "risk_weighted_assets_eur": r.risk_weighted_assets_eur,
        "credit_risk_capital_eur": r.credit_risk_capital_eur,
        "stage_distribution": r.stage_distribution,
    }


def _ser_liquidity(r) -> dict:
    return {
        "total_hqla_eur": r.total_hqla_eur,
        "hqla_composition": r.hqla_composition,
        "total_net_outflows_eur": r.total_net_outflows_eur,
        "lcr_pct": r.lcr_pct,
        "lcr_compliant": r.lcr_compliant,
        "total_asf_eur": r.total_asf_eur,
        "total_rsf_eur": r.total_rsf_eur,
        "nsfr_pct": r.nsfr_pct,
        "nsfr_compliant": r.nsfr_compliant,
        "liquidity_buffer_days": r.liquidity_buffer_days,
        "concentration_risk_pct": r.concentration_risk_pct,
    }


def _ser_market(r) -> dict:
    return {
        "trading_book_eur": r.trading_book_eur,
        "var_99_1d_eur": r.var_99_1d_eur,
        "var_99_10d_eur": r.var_99_10d_eur,
        "stressed_var_99_10d_eur": r.stressed_var_99_10d_eur,
        "expected_shortfall_97_5_eur": r.expected_shortfall_97_5_eur,
        "interest_rate_risk_eve_eur": r.interest_rate_risk_eve_eur,
        "interest_rate_risk_nii_eur": r.interest_rate_risk_nii_eur,
        "fx_risk_eur": r.fx_risk_eur,
        "equity_risk_eur": r.equity_risk_eur,
        "market_risk_rwa_eur": r.market_risk_rwa_eur,
        "market_risk_capital_eur": r.market_risk_capital_eur,
    }


def _ser_operational(r) -> dict:
    return {
        "approach": r.approach,
        "gross_income_avg_3yr_eur": r.gross_income_avg_3yr_eur,
        "alpha_factor_pct": r.alpha_factor_pct,
        "bia_charge_eur": r.bia_charge_eur,
        "business_line_charges": r.business_line_charges,
        "tsa_charge_eur": r.tsa_charge_eur,
        "operational_risk_capital_eur": r.operational_risk_capital_eur,
        "loss_event_buffer_pct": r.loss_event_buffer_pct,
    }


def _ser_aml(r) -> dict:
    return {
        "total_counterparties": r.total_counterparties,
        "countries_screened": r.countries_screened,
        "high_risk_count": r.high_risk_count,
        "very_high_risk_count": r.very_high_risk_count,
        "grey_list_exposures": r.grey_list_exposures,
        "black_list_exposures": r.black_list_exposures,
        "overall_aml_risk_score": r.overall_aml_risk_score,
        "risk_tier_distribution": r.risk_tier_distribution,
        "recommended_actions": r.recommended_actions,
    }


def _ser_capital(r) -> dict:
    return {
        "cet1_capital_eur": r.cet1_capital_eur,
        "at1_capital_eur": r.at1_capital_eur,
        "tier2_capital_eur": r.tier2_capital_eur,
        "total_capital_eur": r.total_capital_eur,
        "credit_rwa_eur": r.credit_rwa_eur,
        "market_rwa_eur": r.market_rwa_eur,
        "operational_rwa_eur": r.operational_rwa_eur,
        "total_rwa_eur": r.total_rwa_eur,
        "cet1_ratio_pct": r.cet1_ratio_pct,
        "tier1_ratio_pct": r.tier1_ratio_pct,
        "total_capital_ratio_pct": r.total_capital_ratio_pct,
        "leverage_ratio_pct": r.leverage_ratio_pct,
        "leverage_exposure_eur": r.leverage_exposure_eur,
        "countercyclical_buffer_pct": r.countercyclical_buffer_pct,
        "combined_buffer_requirement_pct": r.combined_buffer_requirement_pct,
        "surplus_to_mda_eur": r.surplus_to_mda_eur,
        "compliant": r.compliant,
    }


def _ser_summary(r) -> dict:
    return {
        "entity_name": r.entity_name,
        "overall_risk_rating": r.overall_risk_rating,
        "total_capital_requirement_eur": r.total_capital_requirement_eur,
        "recommendations": r.recommendations,
        "credit_risk": _ser_credit(r.credit_risk) if r.credit_risk else None,
        "liquidity_risk": _ser_liquidity(r.liquidity_risk) if r.liquidity_risk else None,
        "market_risk": _ser_market(r.market_risk) if r.market_risk else None,
        "operational_risk": _ser_operational(r.operational_risk) if r.operational_risk else None,
        "aml_risk": _ser_aml(r.aml_risk) if r.aml_risk else None,
        "capital_adequacy": _ser_capital(r.capital_adequacy) if r.capital_adequacy else None,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/credit-risk", summary="Assess IFRS 9 credit risk (PD/LGD/ECL) with climate overlay")
def assess_credit_risk(req: CreditRiskRequest):
    res = _engine.assess_credit_risk(
        total_exposure_eur=req.total_exposure_eur,
        portfolio_size=req.portfolio_size,
        avg_rating=req.avg_rating,
        collateral_type=req.collateral_type,
        avg_maturity_years=req.avg_maturity_years,
        stage2_pct=req.stage2_pct,
        stage3_pct=req.stage3_pct,
        warming_c=req.warming_c,
    )
    return _ser_credit(res)


@router.post("/liquidity-risk", summary="Assess LCR + NSFR using Basel III factors")
def assess_liquidity_risk(req: LiquidityRiskRequest):
    res = _engine.assess_liquidity_risk(
        hqla_holdings=req.hqla_holdings,
        funding_sources=req.funding_sources,
        asset_book=req.asset_book,
    )
    return _ser_liquidity(res)


@router.post("/market-risk", summary="Assess VaR / Stressed VaR / IRRBB")
def assess_market_risk(req: MarketRiskRequest):
    res = _engine.assess_market_risk(
        trading_book_eur=req.trading_book_eur,
        equity_exposure_eur=req.equity_exposure_eur,
        fx_exposure_eur=req.fx_exposure_eur,
        interest_rate_dv01_eur=req.interest_rate_dv01_eur,
        portfolio_volatility_pct=req.portfolio_volatility_pct,
        stressed_volatility_pct=req.stressed_volatility_pct,
        rate_shock_bps=req.rate_shock_bps,
    )
    return _ser_market(res)


@router.post("/operational-risk", summary="Assess operational risk (BIA + TSA)")
def assess_operational_risk(req: OperationalRiskRequest):
    res = _engine.assess_operational_risk(
        gross_income_year1_eur=req.gross_income_year1_eur,
        gross_income_year2_eur=req.gross_income_year2_eur,
        gross_income_year3_eur=req.gross_income_year3_eur,
        business_line_income=req.business_line_income,
    )
    return _ser_operational(res)


@router.post("/aml-risk", summary="Screen counterparties for AML/CFT risk (FATF)")
def assess_aml_risk(req: AMLRiskRequest):
    res = _engine.assess_aml_risk(
        counterparty_countries=req.counterparty_countries,
        exposure_by_country=req.exposure_by_country,
    )
    return _ser_aml(res)


@router.post("/capital-adequacy", summary="Assess Basel III/IV capital adequacy ratios")
def assess_capital_adequacy(req: CapitalAdequacyRequest):
    res = _engine.assess_capital_adequacy(
        cet1_capital_eur=req.cet1_capital_eur,
        at1_capital_eur=req.at1_capital_eur,
        tier2_capital_eur=req.tier2_capital_eur,
        credit_rwa_eur=req.credit_rwa_eur,
        market_rwa_eur=req.market_rwa_eur,
        operational_rwa_eur=req.operational_rwa_eur,
        leverage_exposure_eur=req.leverage_exposure_eur,
        countercyclical_buffer_pct=req.countercyclical_buffer_pct,
    )
    return _ser_capital(res)


@router.post("/comprehensive", summary="Full bank risk assessment across all sub-modules")
def comprehensive_assessment(req: ComprehensiveRequest):
    res = _engine.comprehensive_assessment(
        entity_name=req.entity_name,
        total_exposure_eur=req.total_exposure_eur,
        cet1_capital_eur=req.cet1_capital_eur,
        trading_book_eur=req.trading_book_eur,
        gross_income_eur=req.gross_income_eur,
        warming_c=req.warming_c,
    )
    return _ser_summary(res)


@router.get("/pd-term-structures", summary="Get PD term structures by rating")
def pd_term_structures():
    return {"pd_term_structures": _engine.get_pd_term_structures()}


@router.get("/lgd-collateral-types", summary="Get LGD by collateral type")
def lgd_collateral_types():
    return {"lgd_by_collateral": _engine.get_lgd_collateral_types()}


@router.get("/risk-weights", summary="Get Basel III/IV risk weights")
def risk_weights():
    return {"risk_weights": _engine.get_risk_weights()}


@router.get("/tsa-beta-factors", summary="Get TSA beta factors by business line")
def tsa_beta_factors():
    return {"tsa_beta_factors": _engine.get_tsa_beta_factors()}
