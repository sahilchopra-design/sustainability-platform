"""
E79 — Climate Insurance & Parametric Risk Routes
=================================================
FastAPI routes for climate insurance risk assessment services.

Prefix: /api/v1/climate-insurance
Tag:    E79 Climate Insurance
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.climate_insurance_engine import (
    IAIS_REQUIREMENTS,
    NATCAT_COUNTRY_PROFILES,
    PARAMETRIC_TRIGGER_TYPES,
    PROTECTION_GAP_DATA,
    ClimateInsuranceEngine,
    InsurancePortfolioInput,
    NatCatInput,
    ParametricDesignInput,
    climate_insurance_engine,
)

router = APIRouter(
    prefix="/api/v1/climate-insurance",
    tags=["E79 Climate Insurance"],
)


# ---------------------------------------------------------------------------
# Pydantic request models
# ---------------------------------------------------------------------------

class InsurancePortfolioRequest(BaseModel):
    insurer_name: str = Field(..., description="Legal name of insurer")
    portfolio_type: str = Field(
        ..., description="pc | life | reinsurance | composite | specialty"
    )
    total_exposure_usd_m: float = Field(..., gt=0, description="Total insured exposure (USD millions)")
    pc_exposure_usd_m: Optional[float] = Field(None, ge=0, description="P&C exposure (USD millions)")
    life_exposure_usd_m: Optional[float] = Field(None, ge=0, description="Life/health exposure (USD millions)")
    investment_portfolio_usd_m: Optional[float] = Field(None, ge=0, description="Investment portfolio (USD millions)")
    high_carbon_investment_pct: Optional[float] = Field(
        None, ge=0, le=100, description="% of investments in high-carbon assets"
    )
    country_exposures: Optional[Dict[str, float]] = Field(
        None, description="Exposure by country ISO3 code (USD millions)"
    )
    peril_exposures: Optional[Dict[str, float]] = Field(
        None, description="Exposure by peril type (USD millions)"
    )
    iais_scores: Optional[Dict[str, float]] = Field(
        None,
        description=(
            "IAIS item scores keyed by item ID (GOV-01..05, STR-01..04, RM-01..06, DISC-01..05). "
            "Values: 1.0 (full) | 0.5 (partial) | 0.0 (absent)"
        ),
    )
    ngfs_scenario: str = Field(
        "orderly",
        description="NGFS scenario: orderly | disorderly | hot_house | below_2c"
    )
    reporting_year: int = Field(2024, ge=2000, le=2100, description="Reporting year")

    class Config:
        json_schema_extra = {
            "example": {
                "insurer_name": "Meridian Re plc",
                "portfolio_type": "pc",
                "total_exposure_usd_m": 5000,
                "pc_exposure_usd_m": 3500,
                "investment_portfolio_usd_m": 4200,
                "high_carbon_investment_pct": 12,
                "country_exposures": {"USA": 2500, "GBR": 800, "DEU": 700},
                "peril_exposures": {"flood": 1800, "wind_cyclone": 1200, "drought": 500},
                "ngfs_scenario": "disorderly",
                "reporting_year": 2024,
            }
        }


class IAISComplianceRequest(BaseModel):
    insurer_name: str = Field(..., description="Insurer name")
    portfolio_type: str = Field("pc", description="pc | life | reinsurance | composite | specialty")
    total_exposure_usd_m: float = Field(..., gt=0)
    iais_scores: Optional[Dict[str, float]] = Field(
        None,
        description="Per-item scores: GOV-01..05 (0.0-1.0), STR-01..04, RM-01..06, DISC-01..05",
    )


class ParametricDesignRequest(BaseModel):
    product_name: str = Field(..., description="Product name / identifier")
    peril: str = Field(..., description="flood | wind_cyclone | drought | heat_stress | earthquake")
    trigger_type: str = Field(
        ...,
        description=(
            "rainfall_deficit | wind_speed | temperature_anomaly | "
            "flood_depth | soil_moisture_deficit | cat_model_score"
        ),
    )
    country_code: str = Field(..., description="ISO3 country code (e.g. USA, GBR, IND)")
    exposure_value_usd_m: float = Field(..., gt=0, description="Insured/protected value (USD millions)")
    season_months: int = Field(6, ge=1, le=12, description="Insurance season length (months)")
    trigger_level: Optional[float] = Field(None, description="Trigger level (units depend on trigger type)")
    exit_level: Optional[float] = Field(None, description="Exit (maximum payout) level")
    max_payout_usd_m: Optional[float] = Field(None, description="Maximum payout (USD millions)")
    premium_loading_pct: float = Field(35.0, ge=0, le=100, description="Premium loading for expenses + profit (%)")
    climate_adjustment_yr: int = Field(2030, ge=2024, le=2100, description="Climate adjustment horizon year")

    class Config:
        json_schema_extra = {
            "example": {
                "product_name": "Kenya Drought Index Insurance",
                "peril": "drought",
                "trigger_type": "rainfall_deficit",
                "country_code": "KEN",
                "exposure_value_usd_m": 250,
                "season_months": 6,
                "premium_loading_pct": 35,
                "climate_adjustment_yr": 2030,
            }
        }


class NatCatRequest(BaseModel):
    country_code: str = Field(..., description="ISO3 country code")
    peril: str = Field(..., description="flood | wind_cyclone | earthquake | drought")
    insured_exposure_usd_m: float = Field(..., gt=0, description="Insured exposure (USD millions)")
    rcp_scenario: str = Field("rcp45", description="RCP scenario: rcp26 | rcp45 | rcp85")
    horizon_year: int = Field(2040, ge=2024, le=2100, description="Projection horizon year")

    class Config:
        json_schema_extra = {
            "example": {
                "country_code": "USA",
                "peril": "wind_cyclone",
                "insured_exposure_usd_m": 1500,
                "rcp_scenario": "rcp85",
                "horizon_year": 2050,
            }
        }


class ClimateVaRRequest(BaseModel):
    insurer_name: str = Field(..., description="Insurer name")
    portfolio_type: str = Field("pc", description="pc | life | reinsurance | composite | specialty")
    total_exposure_usd_m: float = Field(..., gt=0, description="Total exposure (USD millions)")
    pc_exposure_usd_m: Optional[float] = Field(None, description="P&C exposure (USD millions)")
    life_exposure_usd_m: Optional[float] = Field(None, description="Life exposure (USD millions)")
    investment_portfolio_usd_m: Optional[float] = Field(None, description="Investment portfolio (USD millions)")
    high_carbon_investment_pct: Optional[float] = Field(None, ge=0, le=100)
    ngfs_scenario: str = Field("orderly", description="orderly | disorderly | hot_house | below_2c")
    reporting_year: int = Field(2024)


class ORSAStressRequest(BaseModel):
    insurer_name: str = Field(..., description="Insurer name")
    portfolio_type: str = Field("pc", description="pc | life | reinsurance | composite | specialty")
    total_exposure_usd_m: float = Field(..., gt=0)
    investment_portfolio_usd_m: Optional[float] = Field(None)
    high_carbon_investment_pct: Optional[float] = Field(None, ge=0, le=100)
    ngfs_scenario: str = Field("orderly")
    reporting_year: int = Field(2024)


class CasualtyLiabilityRequest(BaseModel):
    insurer_name: str = Field(..., description="Insurer name")
    portfolio_type: str = Field("pc", description="pc | specialty | composite")
    total_exposure_usd_m: float = Field(..., gt=0)
    pc_exposure_usd_m: Optional[float] = Field(None)
    reporting_year: int = Field(2024)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post(
    "/assess",
    summary="Full Climate Insurance Assessment",
    description=(
        "Run all E79 sub-engines: IAIS supervisory assessment, parametric product design, "
        "NatCat loss modelling, climate VaR, ORSA stress test, casualty liability risk, "
        "and protection gap analysis. Returns consolidated climate risk score and supervisory flags."
    ),
)
def full_assessment(request: InsurancePortfolioRequest) -> Dict[str, Any]:
    """Execute all Climate Insurance sub-modules for a single insurer."""
    try:
        portfolio_input = InsurancePortfolioInput(
            insurer_name=request.insurer_name,
            portfolio_type=request.portfolio_type,
            total_exposure_usd_m=request.total_exposure_usd_m,
            pc_exposure_usd_m=request.pc_exposure_usd_m,
            life_exposure_usd_m=request.life_exposure_usd_m,
            investment_portfolio_usd_m=request.investment_portfolio_usd_m,
            high_carbon_investment_pct=request.high_carbon_investment_pct,
            country_exposures=request.country_exposures,
            peril_exposures=request.peril_exposures,
            iais_scores=request.iais_scores,
            ngfs_scenario=request.ngfs_scenario,
            reporting_year=request.reporting_year,
        )
        result = climate_insurance_engine.full_assessment(portfolio_input)
        return {
            "insurer_name": result.insurer_name,
            "reporting_year": result.reporting_year,
            "overall_climate_risk_score": result.overall_climate_risk_score,
            "supervisory_flags": result.supervisory_flags,
            "iais_compliance": result.iais_compliance,
            "parametric_design": result.parametric_design,
            "natcat_loss": result.natcat_loss,
            "climate_var": result.climate_var,
            "orsa_stress": result.orsa_stress,
            "casualty_liability": result.casualty_liability,
            "protection_gap": result.protection_gap,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post(
    "/iais-compliance",
    summary="IAIS Supervisory Climate Risk Assessment",
    description=(
        "4-pillar IAIS Application Paper (2021) supervisory scoring: "
        "Governance (5 items), Strategy (4 items), Risk Management (6 items), Disclosure (5 items). "
        "Returns weighted score, RAG flag (green/amber/red), and gap list. "
        "Thresholds: amber <60%, red <40%."
    ),
)
def iais_compliance(request: IAISComplianceRequest) -> Dict[str, Any]:
    """IAIS Application Paper on Climate Risks — 4-pillar supervisory scoring."""
    try:
        portfolio_input = InsurancePortfolioInput(
            insurer_name=request.insurer_name,
            portfolio_type=request.portfolio_type,
            total_exposure_usd_m=request.total_exposure_usd_m,
            iais_scores=request.iais_scores,
        )
        return climate_insurance_engine.assess_iais_compliance(portfolio_input)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post(
    "/parametric-design",
    summary="Parametric Insurance Product Design",
    description=(
        "Design a parametric insurance product for 6 index trigger types: "
        "rainfall deficit, wind speed, temperature anomaly, flood depth, "
        "soil moisture deficit, cat model score. "
        "Returns payout structure, climate-adjusted AAL, gross premium, premium rate, and basis risk score."
    ),
)
def parametric_design(request: ParametricDesignRequest) -> Dict[str, Any]:
    """Parametric product design with climate-adjusted AAL and premium calculation."""
    try:
        param_input = ParametricDesignInput(
            product_name=request.product_name,
            peril=request.peril,
            trigger_type=request.trigger_type,
            country_code=request.country_code,
            exposure_value_usd_m=request.exposure_value_usd_m,
            season_months=request.season_months,
            trigger_level=request.trigger_level,
            exit_level=request.exit_level,
            max_payout_usd_m=request.max_payout_usd_m,
            premium_loading_pct=request.premium_loading_pct,
            climate_adjustment_yr=request.climate_adjustment_yr,
        )
        return climate_insurance_engine.design_parametric_product(param_input)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post(
    "/natcat-loss",
    summary="NatCat Loss Modelling",
    description=(
        "Model NatCat insured losses for a country/peril under RCP climate scenarios. "
        "4 perils: flood, wind/cyclone, earthquake, drought. "
        "20 country profiles with AAL, PML 100yr and 250yr, climate loading factors. "
        "Returns base and climate-adjusted losses and premium loading recommendation."
    ),
)
def natcat_loss(request: NatCatRequest) -> Dict[str, Any]:
    """NatCat loss modelling with climate scenario adjustments."""
    try:
        natcat_input = NatCatInput(
            country_code=request.country_code,
            peril=request.peril,
            insured_exposure_usd_m=request.insured_exposure_usd_m,
            rcp_scenario=request.rcp_scenario,
            horizon_year=request.horizon_year,
        )
        return climate_insurance_engine.model_natcat_loss(natcat_input)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post(
    "/climate-var",
    summary="Climate VaR for Insurance Portfolios",
    description=(
        "Calculate 99th-percentile climate VaR across three risk channels: "
        "physical risk (NatCat), transition risk (investment portfolio), "
        "life/health risk (heat mortality + morbidity). "
        "Returns gross and net (diversification-adjusted) climate VaR in USD and % of exposure."
    ),
)
def climate_var(request: ClimateVaRRequest) -> Dict[str, Any]:
    """Climate VaR calculation across physical, transition, and life channels."""
    try:
        portfolio_input = InsurancePortfolioInput(
            insurer_name=request.insurer_name,
            portfolio_type=request.portfolio_type,
            total_exposure_usd_m=request.total_exposure_usd_m,
            pc_exposure_usd_m=request.pc_exposure_usd_m,
            life_exposure_usd_m=request.life_exposure_usd_m,
            investment_portfolio_usd_m=request.investment_portfolio_usd_m,
            high_carbon_investment_pct=request.high_carbon_investment_pct,
            ngfs_scenario=request.ngfs_scenario,
            reporting_year=request.reporting_year,
        )
        return climate_insurance_engine.calculate_climate_var(portfolio_input)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post(
    "/orsa-stress",
    summary="ORSA Climate Stress Test (Solvency II Art 45a)",
    description=(
        "Run ORSA climate stress test across all 4 NGFS scenarios. "
        "SCR uplift = NatCat reserve increase + market risk shock + liability reserve. "
        "Post-stress solvency ratio and MSR/SCR breach flags. "
        "12-item Art 45a ORSA checklist scoring."
    ),
)
def orsa_stress(request: ORSAStressRequest) -> Dict[str, Any]:
    """Solvency II Art 45a ORSA climate stress test across NGFS scenarios."""
    try:
        portfolio_input = InsurancePortfolioInput(
            insurer_name=request.insurer_name,
            portfolio_type=request.portfolio_type,
            total_exposure_usd_m=request.total_exposure_usd_m,
            investment_portfolio_usd_m=request.investment_portfolio_usd_m,
            high_carbon_investment_pct=request.high_carbon_investment_pct,
            ngfs_scenario=request.ngfs_scenario,
            reporting_year=request.reporting_year,
        )
        return climate_insurance_engine.orsa_climate_stress(portfolio_input)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post(
    "/casualty-liability",
    summary="Casualty Climate Liability Risk",
    description=(
        "Assess climate casualty liability risk across three lines: "
        "D&O (greenwashing claims, securities fraud, 25% annual growth), "
        "E&O (ESG advisory failure, 18% growth), "
        "Pollution (stranded asset cleanup, 15% growth). "
        "Returns reserve estimates and 5-year projection."
    ),
)
def casualty_liability(request: CasualtyLiabilityRequest) -> Dict[str, Any]:
    """Casualty climate liability risk: D&O, E&O, and pollution reserve estimation."""
    try:
        portfolio_input = InsurancePortfolioInput(
            insurer_name=request.insurer_name,
            portfolio_type=request.portfolio_type,
            total_exposure_usd_m=request.total_exposure_usd_m,
            pc_exposure_usd_m=request.pc_exposure_usd_m,
            reporting_year=request.reporting_year,
        )
        return climate_insurance_engine.assess_casualty_liability(portfolio_input)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post(
    "/protection-gap",
    summary="Protection Gap Analysis",
    description=(
        "Analyse the insurance protection gap for a country/peril combination. "
        "Returns current insured vs uninsured loss split, climate projection to 2030/2040, "
        "and gap closure levers. Country profiles include UN-FAO protection gap data for 20 countries."
    ),
)
def protection_gap(
    country_code: str,
    peril: str,
) -> Dict[str, Any]:
    """Insurance protection gap analysis by country and peril."""
    try:
        return climate_insurance_engine.analyse_protection_gap(
            country_code=country_code.upper(),
            peril=peril.lower(),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Reference endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/ref/iais-requirements",
    summary="IAIS Application Paper on Climate Risks — Requirements",
    description=(
        "Full IAIS AP (2021) requirement set across 4 pillars: "
        "Governance (ICP 7), Strategy (ICP 16), Risk Management (ICP 8/20), Disclosure (ICP 20). "
        "20 items with descriptions and scoring guidance."
    ),
)
def ref_iais_requirements() -> Dict[str, Any]:
    """Return IAIS Application Paper on Climate Risks supervisory requirement set."""
    return {
        "pillars": IAIS_REQUIREMENTS,
        "total_items": sum(len(p["items"]) for p in IAIS_REQUIREMENTS.values()),
        "total_pillars": len(IAIS_REQUIREMENTS),
        "reference": "IAIS Application Paper on the Supervision of Climate-related Risks in the Insurance Sector (2021)",
        "scoring_guide": {
            "full": 1.0,
            "partial": 0.5,
            "absent": 0.0,
        },
        "supervisory_thresholds": {
            "green": ">=80%",
            "amber": "60-79%",
            "red": "<60%",
        },
    }


@router.get(
    "/ref/natcat-profiles",
    summary="Country NatCat Profiles",
    description=(
        "NatCat country profiles for 20 countries: AAL (% of exposure), PML at 1-in-100yr and 1-in-250yr, "
        "climate loading factors (% increase by 2050 under RCP8.5), "
        "and insurance penetration / protection gap data."
    ),
)
def ref_natcat_profiles() -> Dict[str, Any]:
    """Return NatCat country profile registry."""
    return {
        "countries": NATCAT_COUNTRY_PROFILES,
        "total_countries": len(NATCAT_COUNTRY_PROFILES),
        "perils": ["flood", "wind_cyclone", "earthquake", "drought"],
        "sources": [
            "Swiss Re sigma Natural Catastrophes 2023 (sigma No 1/2023)",
            "Munich Re NatCatSERVICE 2022",
            "EIOPA NatCat country statistics",
            "World Bank Natural Disaster Hotspots",
        ],
        "climate_loading_note": "RCP8.5 loading to 2050; linearly scaled by RCP scenario and time horizon",
    }


@router.get(
    "/ref/parametric-triggers",
    summary="Parametric Trigger Types",
    description=(
        "6 parametric insurance index trigger types with full specification: "
        "rainfall deficit, wind speed, temperature anomaly, flood depth, "
        "soil moisture deficit, and cat model score. "
        "Includes trigger/exit thresholds, basis risk range, and reference data sources."
    ),
)
def ref_parametric_triggers() -> Dict[str, Any]:
    """Return parametric trigger type registry with design specifications."""
    return {
        "trigger_types": PARAMETRIC_TRIGGER_TYPES,
        "total_types": len(PARAMETRIC_TRIGGER_TYPES),
        "reference_frameworks": [
            "ILS (Insurance-Linked Securities) market standards",
            "CCRIF SPC parametric trigger specifications",
            "World Bank Disaster Risk Financing products",
            "ARC Parametric Index Insurance Guidelines",
            "Lloyd's Syndicate Parametric Guidelines 2022",
        ],
        "basis_risk_guidance": {
            "low": "<0.20 — acceptable for ILS/reinsurance placement",
            "moderate": "0.20-0.40 — mitigation required (denser stations)",
            "high": ">0.40 — may preclude regulatory approval in some jurisdictions",
        },
    }


@router.get(
    "/ref/protection-gap",
    summary="Protection Gap Data",
    description=(
        "Global and peril-specific insurance protection gap data. "
        "Includes total economic losses, insured losses, gap % and climate projections. "
        "Source: Swiss Re sigma No 1/2023."
    ),
)
def ref_protection_gap() -> Dict[str, Any]:
    """Return global insurance protection gap reference data."""
    return {
        "protection_gap_data": PROTECTION_GAP_DATA,
        "source": "Swiss Re sigma No 1/2023 — Natural Catastrophe Resilience",
        "supplementary_sources": [
            "UN-FAO Global Agriculture Protection Gap 2022",
            "IAIS Protection Gap assessment 2022",
            "Lloyd's Systemic Risk Review 2021",
        ],
        "note": (
            "Protection gap = (total economic loss - insured loss) / total economic loss. "
            "High gap implies significant uninsured exposure that can trigger sovereign fiscal stress."
        ),
    }
