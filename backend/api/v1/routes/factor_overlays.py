"""
Factor Overlay API
==================
Endpoints for applying ESG, geopolitical, and technology factor overlays
to existing analytics module outputs.
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from services.factor_overlay_engine import FactorOverlayEngine

router = APIRouter(prefix="/api/v1/factor-overlays", tags=["Factor Overlays"])

_engine = FactorOverlayEngine()


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class ECLCreditRequest(BaseModel):
    entity_id: str
    country_code: str
    sector_nace: str
    base_pd: float
    base_lgd: float
    base_ead: float
    scenario: str = "current_policies"
    as_of_date: Optional[str] = None


class ALMTreasuryRequest(BaseModel):
    entity_id: str
    country_code: str
    credit_quality: str
    base_nim_bps: float
    base_duration_gap: float
    fx_exposure_pct: float = 0.0
    scenario: str = "current_policies"
    as_of_date: Optional[str] = None


class RegulatoryComplianceRequest(BaseModel):
    entity_id: str
    jurisdiction: str
    current_gap_count: int
    esrs_pillars: list[str] = []
    assurance_level: str = "medium"
    as_of_date: Optional[str] = None


class InsuranceUWRequest(BaseModel):
    entity_id: str
    country_code: str
    biome: str
    base_premium: float
    base_loss_ratio: float
    parametric_trigger: str = "traditional_only"
    as_of_date: Optional[str] = None


class InsuranceActuarialRequest(BaseModel):
    entity_id: str
    country_code: str
    air_quality_band: str
    base_mortality_rate: float
    migration_pattern: str = "stable"
    medical_tech: str = "baseline"
    as_of_date: Optional[str] = None


class PortfolioMgmtRequest(BaseModel):
    entity_id: str
    sector_nace: str
    base_return_pct: float
    base_alpha_pct: float
    as_of_date: Optional[str] = None


class RiskMgmtRequest(BaseModel):
    entity_id: str
    country_code: str
    sector_nace: str
    base_var_pct: float
    base_cvar_pct: float
    as_of_date: Optional[str] = None


class PEDealRequest(BaseModel):
    entity_id: str
    country_code: str
    sector_nace: str
    base_ev_ebitda: float
    carbon_reduction_pct: float = 0.0
    as_of_date: Optional[str] = None


class REValuationRequest(BaseModel):
    entity_id: str
    country_code: str
    certification: str
    smart_building_tier: str
    base_value: float
    base_noi: float
    as_of_date: Optional[str] = None


class EnergyStrategyRequest(BaseModel):
    entity_id: str
    country_code: str
    base_generation_gwh: float
    base_co2_intensity: float
    h2_pathway: str = "grey_h2"
    as_of_date: Optional[str] = None


class AgriFinanceRequest(BaseModel):
    entity_id: str
    country_code: str
    certification: str
    base_loan_value: float
    precision_ag_level: str = "conventional"
    as_of_date: Optional[str] = None


class TradeAdvisoryRequest(BaseModel):
    entity_id: str
    country_code: str
    sector_nace: str
    base_trade_value: float
    supply_chain_digital_level: str = "paper_hybrid"
    as_of_date: Optional[str] = None


class FactorSummaryRequest(BaseModel):
    country_code: str
    sector_nace: str


# ---------------------------------------------------------------------------
# Serialiser
# ---------------------------------------------------------------------------

def _ser_factor(f) -> dict:
    return {
        "factor_type": f.factor_type,
        "factor_name": f.factor_name,
        "raw_value": f.raw_value,
        "adjustment": f.adjustment,
        "unit": f.unit,
        "source": f.source,
        "confidence": f.confidence,
    }


def _ser_result(r) -> dict:
    return {
        "entity_id": r.entity_id,
        "module_id": r.module_id,
        "overlay_type": r.overlay_type,
        "base_metrics": r.base_metrics,
        "enhanced_metrics": r.enhanced_metrics,
        "esg_factors": [_ser_factor(f) for f in r.esg_factors],
        "geo_factors": [_ser_factor(f) for f in r.geo_factors],
        "tech_factors": [_ser_factor(f) for f in r.tech_factors],
        "composite_adjustment": r.composite_adjustment,
        "confidence": r.confidence,
        "warnings": r.warnings,
        "audit_trail": r.audit_trail,
        "as_of_date": r.as_of_date,
    }


# ---------------------------------------------------------------------------
# Endpoints — one per FI Type × LOB
# ---------------------------------------------------------------------------

@router.post("/ecl-credit", summary="Bank Credit — Climate-adjusted ECL overlay")
def ecl_credit(req: ECLCreditRequest):
    res = _engine.overlay_ecl_credit(
        entity_id=req.entity_id, country_code=req.country_code,
        sector_nace=req.sector_nace, base_pd=req.base_pd,
        base_lgd=req.base_lgd, base_ead=req.base_ead,
        scenario=req.scenario, as_of_date=req.as_of_date,
    )
    return _ser_result(res)


@router.post("/alm-treasury", summary="Bank Treasury — ALM ESG/macro overlay")
def alm_treasury(req: ALMTreasuryRequest):
    res = _engine.overlay_alm_treasury(
        entity_id=req.entity_id, country_code=req.country_code,
        credit_quality=req.credit_quality, base_nim_bps=req.base_nim_bps,
        base_duration_gap=req.base_duration_gap,
        fx_exposure_pct=req.fx_exposure_pct,
        scenario=req.scenario, as_of_date=req.as_of_date,
    )
    return _ser_result(res)


@router.post("/regulatory-compliance", summary="Bank Compliance — Multi-jurisdiction overlay")
def regulatory_compliance(req: RegulatoryComplianceRequest):
    res = _engine.overlay_regulatory_compliance(
        entity_id=req.entity_id, jurisdiction=req.jurisdiction,
        current_gap_count=req.current_gap_count,
        esrs_pillars=req.esrs_pillars if req.esrs_pillars else None,
        assurance_level=req.assurance_level, as_of_date=req.as_of_date,
    )
    return _ser_result(res)


@router.post("/insurance-uw", summary="Insurer UW — P&C technical pricing overlay")
def insurance_uw(req: InsuranceUWRequest):
    res = _engine.overlay_insurance_uw(
        entity_id=req.entity_id, country_code=req.country_code,
        biome=req.biome, base_premium=req.base_premium,
        base_loss_ratio=req.base_loss_ratio,
        parametric_trigger=req.parametric_trigger, as_of_date=req.as_of_date,
    )
    return _ser_result(res)


@router.post("/insurance-actuarial", summary="Insurer Actuarial — Life reserves overlay")
def insurance_actuarial(req: InsuranceActuarialRequest):
    res = _engine.overlay_insurance_actuarial(
        entity_id=req.entity_id, country_code=req.country_code,
        air_quality_band=req.air_quality_band,
        base_mortality_rate=req.base_mortality_rate,
        migration_pattern=req.migration_pattern,
        medical_tech=req.medical_tech, as_of_date=req.as_of_date,
    )
    return _ser_result(res)


@router.post("/portfolio-management", summary="AM PM — ESG alpha decomposition overlay")
def portfolio_management(req: PortfolioMgmtRequest):
    res = _engine.overlay_portfolio_management(
        entity_id=req.entity_id, sector_nace=req.sector_nace,
        base_return_pct=req.base_return_pct,
        base_alpha_pct=req.base_alpha_pct, as_of_date=req.as_of_date,
    )
    return _ser_result(res)


@router.post("/risk-management", summary="AM Risk — Enhanced risk reporting overlay")
def risk_management(req: RiskMgmtRequest):
    res = _engine.overlay_risk_management(
        entity_id=req.entity_id, country_code=req.country_code,
        sector_nace=req.sector_nace, base_var_pct=req.base_var_pct,
        base_cvar_pct=req.base_cvar_pct, as_of_date=req.as_of_date,
    )
    return _ser_result(res)


@router.post("/pe-deal", summary="PE Deals — ESG deal scoring overlay")
def pe_deal(req: PEDealRequest):
    res = _engine.overlay_pe_deal(
        entity_id=req.entity_id, country_code=req.country_code,
        sector_nace=req.sector_nace, base_ev_ebitda=req.base_ev_ebitda,
        carbon_reduction_pct=req.carbon_reduction_pct,
        as_of_date=req.as_of_date,
    )
    return _ser_result(res)


@router.post("/real-estate-valuation", summary="RE Valuations — Green premium overlay")
def real_estate_valuation(req: REValuationRequest):
    res = _engine.overlay_real_estate_valuation(
        entity_id=req.entity_id, country_code=req.country_code,
        certification=req.certification,
        smart_building_tier=req.smart_building_tier,
        base_value=req.base_value, base_noi=req.base_noi,
        as_of_date=req.as_of_date,
    )
    return _ser_result(res)


@router.post("/energy-strategy", summary="Energy Strategy — Transition pathway overlay")
def energy_strategy(req: EnergyStrategyRequest):
    res = _engine.overlay_energy_strategy(
        entity_id=req.entity_id, country_code=req.country_code,
        base_generation_gwh=req.base_generation_gwh,
        base_co2_intensity=req.base_co2_intensity,
        h2_pathway=req.h2_pathway, as_of_date=req.as_of_date,
    )
    return _ser_result(res)


@router.post("/agriculture-finance", summary="Agriculture Finance — Sustainable ag overlay")
def agriculture_finance(req: AgriFinanceRequest):
    res = _engine.overlay_agriculture_finance(
        entity_id=req.entity_id, country_code=req.country_code,
        certification=req.certification,
        base_loan_value=req.base_loan_value,
        precision_ag_level=req.precision_ag_level,
        as_of_date=req.as_of_date,
    )
    return _ser_result(res)


@router.post("/trade-advisory", summary="Geopolitical Advisory — Trade risk overlay")
def trade_advisory(req: TradeAdvisoryRequest):
    res = _engine.overlay_trade_advisory(
        entity_id=req.entity_id, country_code=req.country_code,
        sector_nace=req.sector_nace,
        base_trade_value=req.base_trade_value,
        supply_chain_digital_level=req.supply_chain_digital_level,
        as_of_date=req.as_of_date,
    )
    return _ser_result(res)


# ---------------------------------------------------------------------------
# Utility Endpoints
# ---------------------------------------------------------------------------

@router.post("/factor-summary", summary="Factor summary for a country/sector")
def factor_summary(req: FactorSummaryRequest):
    return _engine.get_factor_summary(req.country_code, req.sector_nace)


@router.get("/available-overlays", summary="List all available overlay types")
def available_overlays():
    return _engine.get_available_overlays()


@router.get("/factor-registries", summary="All factor registry metadata")
def factor_registries():
    return _engine.get_factor_registries()
