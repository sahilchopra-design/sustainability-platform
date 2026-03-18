"""
Insurance Risk API
====================
Endpoints for comprehensive insurance risk analytics: Life (mortality/longevity,
liability valuation), P&C (nat-cat, climate frequency, underwriting),
Reinsurance (retrocession chain), and Health (medical trend).
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from services.insurance_risk_engine import InsuranceRiskEngine

router = APIRouter(prefix="/api/v1/insurance-risk", tags=["Insurance Risk"])

_engine = InsuranceRiskEngine()


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class MortalityRequest(BaseModel):
    country: str = Field("GBR", description="ISO3 country code (e.g. GBR, USA)")
    sex: str = Field("male", description="'male' or 'female'")
    warming_c: float = Field(1.5, description="Global warming scenario in C above pre-industrial")


class LiabilityValuationRequest(BaseModel):
    total_lives: int = Field(10000, description="Number of policies/lives")
    avg_sum_assured_eur: float = Field(100000.0, description="Average sum assured per policy (EUR)")
    avg_remaining_term_years: int = Field(20, description="Average remaining policy term in years")
    avg_age: int = Field(45, description="Average age of policyholders")
    discount_rate_pct: float = Field(2.5, description="Risk-free discount rate (%)")
    longevity_shock_bps: int = Field(20, description="Longevity stress (basis points)")
    country: str = Field("GBR", description="ISO3 country code for mortality tables")


class NatCatExposureRequest(BaseModel):
    country: str = Field("DE", description="Solvency II ISO2 country code (e.g. DE, FR, IT)")
    exposure_eur: float = Field(1_000_000_000, description="Total insured exposure (EUR)")
    perils: Optional[list[str]] = Field(None, description="Peril types: windstorm, flood, earthquake, hail. None = all")
    warming_c: float = Field(1.5, description="Global warming scenario C")


class ClimateFrequencyRequest(BaseModel):
    hazard_types: Optional[list[str]] = Field(None, description="IPCC AR6 hazard types. None = all")
    warming_scenario_c: float = Field(2.0, description="Warming scenario C")
    base_loss_ratio_pct: float = Field(65.0, description="Baseline loss ratio (%)")
    expense_ratio_pct: float = Field(30.0, description="Expense ratio (%)")


class UnderwritingRequest(BaseModel):
    gwp_eur: float = Field(500_000_000, description="Gross written premium (EUR)")
    net_earned_premium_eur: float = Field(450_000_000, description="Net earned premium (EUR)")
    claims_incurred_eur: float = Field(292_500_000, description="Claims incurred (EUR)")
    expense_ratio_pct: float = Field(30.0, description="Operating expense ratio (%)")
    portfolio_size: int = Field(50000, description="Number of policies")
    warming_c: float = Field(1.5, description="Temperature warming scenario C")


class RetrocessionLayerInput(BaseModel):
    name: str = Field(..., description="Layer identifier (e.g. 'QS 30%', 'XL 1st')")
    attachment_eur: float = Field(..., description="Attachment point (EUR)")
    limit_eur: float = Field(..., description="Layer limit (EUR)")


class RetrocessionRequest(BaseModel):
    gross_exposure_eur: float = Field(2_000_000_000, description="Gross exposure (EUR)")
    ceded_premium_eur: float = Field(200_000_000, description="Total ceded premium (EUR)")
    layers: Optional[list[RetrocessionLayerInput]] = Field(None, description="Reinsurance layers. None = default programme")
    counterparty_default_prob_pct: float = Field(0.5, description="Reinsurer default probability (%)")


class MedicalTrendRequest(BaseModel):
    claim_cost_per_member_eur: float = Field(3500.0, description="Average annual claim cost per member (EUR)")
    medical_cpi_trend_pct: float = Field(4.5, description="Medical cost inflation rate (%)")
    member_count: int = Field(100000, description="Total insured members")
    warming_c: float = Field(1.5, description="Temperature warming for climate-health overlay C")
    pandemic_scenario: bool = Field(False, description="Include pandemic surge scenario")


class ComprehensiveAssessmentRequest(BaseModel):
    entity_name: str = Field("InsureCo", description="Insurer name")
    country: str = Field("GBR", description="ISO3 country code (mortality) / maps to ISO2 for nat-cat")
    warming_c: float = Field(1.5, description="Global warming scenario C")
    exposure_eur: float = Field(5_000_000_000, description="Total insured exposure (EUR)")
    own_funds_eur: float = Field(800_000_000, description="Total eligible own funds — Solvency II (EUR)")


# ---------------------------------------------------------------------------
# Serialisers
# ---------------------------------------------------------------------------

def _ser_mortality(r) -> dict:
    return {
        "country": r.country,
        "sex": r.sex,
        "warming_c": r.warming_c,
        "base_mortality": r.base_mortality,
        "adjusted_mortality": r.adjusted_mortality,
        "life_expectancy_delta_years": r.life_expectancy_delta_years,
        "climate_drivers": r.climate_drivers,
        "reserve_impact_pct": r.reserve_impact_pct,
    }


def _ser_liability(r) -> dict:
    return {
        "total_lives": r.total_lives,
        "total_sum_assured_eur": r.total_sum_assured_eur,
        "liability_pv_base_eur": r.liability_pv_base_eur,
        "liability_pv_stressed_eur": r.liability_pv_stressed_eur,
        "surplus_base_eur": r.surplus_base_eur,
        "surplus_stressed_eur": r.surplus_stressed_eur,
        "solvency_ratio_base": r.solvency_ratio_base,
        "solvency_ratio_stressed": r.solvency_ratio_stressed,
        "capital_buffer_eur": r.capital_buffer_eur,
        "longevity_shock_impact_eur": r.longevity_shock_impact_eur,
    }


def _ser_natcat(r) -> dict:
    return {
        "country": r.country,
        "perils_analysed": r.perils_analysed,
        "total_exposure_eur": r.total_exposure_eur,
        "expected_annual_loss_eur": r.expected_annual_loss_eur,
        "pml_100yr_eur": r.pml_100yr_eur,
        "pml_250yr_eur": r.pml_250yr_eur,
        "diversification_benefit_pct": r.diversification_benefit_pct,
        "concentration_risk": r.concentration_risk,
        "tail_var_99_5_eur": r.tail_var_99_5_eur,
        "solvency2_nat_cat_scr_eur": r.solvency2_nat_cat_scr_eur,
    }


def _ser_climate_freq(r) -> dict:
    return {
        "hazard_types": r.hazard_types,
        "warming_scenario_c": r.warming_scenario_c,
        "loss_freq_base": r.loss_freq_base,
        "loss_freq_stressed": r.loss_freq_stressed,
        "severity_multiplier": r.severity_multiplier,
        "loss_ratio_impact_pct": r.loss_ratio_impact_pct,
        "combined_ratio_delta_pct": r.combined_ratio_delta_pct,
        "damage_functions_used": r.damage_functions_used,
    }


def _ser_underwriting(r) -> dict:
    return {
        "portfolio_size": r.portfolio_size,
        "gross_written_premium_eur": r.gross_written_premium_eur,
        "net_earned_premium_eur": r.net_earned_premium_eur,
        "claims_incurred_eur": r.claims_incurred_eur,
        "loss_ratio_pct": r.loss_ratio_pct,
        "expense_ratio_pct": r.expense_ratio_pct,
        "combined_ratio_pct": r.combined_ratio_pct,
        "technical_price_adequacy_pct": r.technical_price_adequacy_pct,
        "risk_margin_eur": r.risk_margin_eur,
        "diversification_benefit_pct": r.diversification_benefit_pct,
        "climate_adjusted_combined_ratio_pct": r.climate_adjusted_combined_ratio_pct,
    }


def _ser_retrocession(r) -> dict:
    return {
        "gross_exposure_eur": r.gross_exposure_eur,
        "ceded_premium_eur": r.ceded_premium_eur,
        "net_retention_eur": r.net_retention_eur,
        "layers": r.layers,
        "retro_exhaustion_prob_pct": r.retro_exhaustion_prob_pct,
        "counterparty_credit_risk_eur": r.counterparty_credit_risk_eur,
        "cascade_failure_prob_pct": r.cascade_failure_prob_pct,
        "net_combined_ratio_pct": r.net_combined_ratio_pct,
    }


def _ser_medical(r) -> dict:
    return {
        "claim_cost_per_member_eur": r.claim_cost_per_member_eur,
        "medical_cpi_trend_pct": r.medical_cpi_trend_pct,
        "climate_health_overlay_pct": r.climate_health_overlay_pct,
        "projected_claim_cost_1yr_eur": r.projected_claim_cost_1yr_eur,
        "projected_claim_cost_3yr_eur": r.projected_claim_cost_3yr_eur,
        "pandemic_surge_pct": r.pandemic_surge_pct,
        "premium_adequacy_ratio": r.premium_adequacy_ratio,
        "ibnr_adequacy_pct": r.ibnr_adequacy_pct,
    }


def _ser_summary(r) -> dict:
    return {
        "entity_name": r.entity_name,
        "overall_solvency_ratio": r.overall_solvency_ratio,
        "total_scr_eur": r.total_scr_eur,
        "capital_surplus_eur": r.capital_surplus_eur,
        "recommendations": r.recommendations,
        "life_mortality": _ser_mortality(r.life_mortality) if r.life_mortality else None,
        "life_liability": _ser_liability(r.life_liability) if r.life_liability else None,
        "natcat_exposure": _ser_natcat(r.natcat_exposure) if r.natcat_exposure else None,
        "climate_frequency": _ser_climate_freq(r.climate_frequency) if r.climate_frequency else None,
        "underwriting": _ser_underwriting(r.underwriting) if r.underwriting else None,
        "retrocession": _ser_retrocession(r.retrocession) if r.retrocession else None,
        "medical_trend": _ser_medical(r.medical_trend) if r.medical_trend else None,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/mortality", summary="Assess climate-adjusted mortality risk")
def assess_mortality(req: MortalityRequest):
    res = _engine.assess_mortality(
        country=req.country, sex=req.sex, warming_c=req.warming_c,
    )
    return _ser_mortality(res)


@router.post("/liability-valuation", summary="Value life liabilities under climate stress")
def value_liabilities(req: LiabilityValuationRequest):
    res = _engine.value_liabilities(
        total_lives=req.total_lives,
        avg_sum_assured_eur=req.avg_sum_assured_eur,
        avg_remaining_term_years=req.avg_remaining_term_years,
        avg_age=req.avg_age,
        discount_rate_pct=req.discount_rate_pct,
        longevity_shock_bps=req.longevity_shock_bps,
        country=req.country,
    )
    return _ser_liability(res)


@router.post("/natcat-exposure", summary="Assess nat-cat exposure (Solvency II Standard Formula)")
def assess_natcat(req: NatCatExposureRequest):
    res = _engine.assess_natcat_exposure(
        country=req.country,
        exposure_eur=req.exposure_eur,
        perils=req.perils,
        warming_c=req.warming_c,
    )
    return _ser_natcat(res)


@router.post("/climate-frequency", summary="Project climate-driven loss frequency/severity")
def assess_climate_frequency(req: ClimateFrequencyRequest):
    res = _engine.assess_climate_frequency(
        hazard_types=req.hazard_types,
        warming_scenario_c=req.warming_scenario_c,
        base_loss_ratio_pct=req.base_loss_ratio_pct,
        expense_ratio_pct=req.expense_ratio_pct,
    )
    return _ser_climate_freq(res)


@router.post("/underwriting", summary="Assess underwriting risk with climate overlay")
def assess_underwriting(req: UnderwritingRequest):
    res = _engine.assess_underwriting(
        gwp_eur=req.gwp_eur,
        net_earned_premium_eur=req.net_earned_premium_eur,
        claims_incurred_eur=req.claims_incurred_eur,
        expense_ratio_pct=req.expense_ratio_pct,
        portfolio_size=req.portfolio_size,
        warming_c=req.warming_c,
    )
    return _ser_underwriting(res)


@router.post("/retrocession", summary="Assess reinsurance retrocession chain risk")
def assess_retrocession(req: RetrocessionRequest):
    layers = [
        {"name": l.name, "attachment_eur": l.attachment_eur, "limit_eur": l.limit_eur}
        for l in req.layers
    ] if req.layers else None
    res = _engine.assess_retrocession(
        gross_exposure_eur=req.gross_exposure_eur,
        ceded_premium_eur=req.ceded_premium_eur,
        layers=layers,
        counterparty_default_prob_pct=req.counterparty_default_prob_pct,
    )
    return _ser_retrocession(res)


@router.post("/medical-trend", summary="Project medical cost trend with climate overlay")
def assess_medical_trend(req: MedicalTrendRequest):
    res = _engine.assess_medical_trend(
        claim_cost_per_member_eur=req.claim_cost_per_member_eur,
        medical_cpi_trend_pct=req.medical_cpi_trend_pct,
        member_count=req.member_count,
        warming_c=req.warming_c,
        pandemic_scenario=req.pandemic_scenario,
    )
    return _ser_medical(res)


@router.post("/comprehensive", summary="Full insurance risk assessment across all sub-modules")
def comprehensive_assessment(req: ComprehensiveAssessmentRequest):
    res = _engine.comprehensive_assessment(
        entity_name=req.entity_name,
        country=req.country,
        warming_c=req.warming_c,
        exposure_eur=req.exposure_eur,
        own_funds_eur=req.own_funds_eur,
    )
    return _ser_summary(res)


@router.get("/available-countries", summary="List countries with WHO mortality data")
def available_countries():
    return {"countries": _engine.get_available_countries()}


@router.get("/available-perils", summary="List available IPCC AR6 hazard types")
def available_perils():
    return {"perils": _engine.get_available_perils()}


@router.get("/solvency2-countries", summary="List countries with Solvency II nat-cat factors")
def solvency2_countries():
    return {"countries": _engine.get_solvency2_countries()}


@router.get("/climate-adjustments", summary="Get climate mortality adjustment factors")
def climate_adjustments():
    return {"adjustments": _engine.get_climate_adjustments()}
