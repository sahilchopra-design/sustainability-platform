"""
Internal Carbon Pricing & Net-Zero Economics — E84 API Router
Prefix: /api/v1/internal-carbon-price
Standards: IPCC AR6 WG3 (2022); SBTi Corporate Manual v2 (2023);
EU ETS Phase 4 Directive 2003/87/EC as amended 2023/958;
ETS2 Directive (EU) 2023/959.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.internal_carbon_price_engine import (
    ABATEMENT_COST_BENCHMARKS,
    EU_ETS_PRICE_TRAJECTORY,
    ETS2_PRICE_TRAJECTORY,
    ICP_MECHANISM_TYPES,
    SBTI_ICP_GUIDANCE,
    InternalCarbonPriceEngine,
    # E84 named constants (required by spec)
    SBTI_ICP_THRESHOLDS,
    EU_ETS_PHASE4_BENCHMARKS,
    ETS_PRICE_TRAJECTORY,
    ABATEMENT_COST_CATEGORIES,
    ICP_MATURITY_TIERS,
    # E84 module-level functions (required by spec)
    assess_icp_mechanism,
    compute_scope_carbon_costs,
    model_carbon_budget,
    calculate_nze_economics,
    calculate_ets_exposure,
    run_full_assessment,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/internal-carbon-price", tags=["E84 Internal Carbon Price"])

_engine = InternalCarbonPriceEngine()


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class ICPMechanismRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str = Field(..., description="Unique entity identifier")
    mechanism_type: str = Field(
        ...,
        description="ICP mechanism type: shadow_price | internal_fee_dividend | budget_based | implicit_price | ets_shadow",
    )
    target_year: int = Field(2030, ge=2024, le=2050, description="Target year for ICP alignment")
    sbti_target: str = Field(
        "1.5C",
        description="SBTi temperature target: '1.5C' or '2C'",
    )
    current_icp: Optional[float] = Field(None, ge=0, description="Current internal carbon price EUR/tCO2e (if any)")


class ScopeCostAllocationRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    scope1_tco2: float = Field(..., ge=0, description="Scope 1 emissions tCO2e")
    scope2_tco2: float = Field(..., ge=0, description="Scope 2 emissions tCO2e (market-based)")
    scope3_tco2: float = Field(..., ge=0, description="Scope 3 emissions tCO2e (total categories)")
    icp_eur_per_tco2: float = Field(..., ge=0, description="Internal carbon price EUR/tCO2e to apply")
    ebitda_m: Optional[float] = Field(None, ge=0, description="EBITDA in €M for materiality calculation")
    business_units: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="List of {name, emissions_tco2e} for BU-level allocation",
    )


class CarbonBudgetRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    base_year: int = Field(2019, ge=1990, le=2024, description="Base year for SBTi target")
    base_year_emissions_tco2: float = Field(..., ge=0, description="Gross Scope 1+2 emissions in base year (tCO2e)")
    sbti_target: str = Field("1.5C", description="SBTi temperature target: '1.5C' or '2C'")
    current_year: int = Field(2024, ge=2020, le=2035)
    actual_emissions_tco2: float = Field(..., ge=0, description="Actual Scope 1+2 emissions in current year (tCO2e)")


class AbatementCurveRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    sector: str = Field(..., description="NACE sector key (see /ref/sector-intensities)")
    current_emissions_tco2: float = Field(..., ge=0, description="Current total emissions tCO2e/yr")
    target_reduction_pct: float = Field(..., ge=1, le=100, description="Target emission reduction %")
    max_capex_m: Optional[float] = Field(None, ge=0, description="Maximum total capex budget €M (optional constraint)")


class NZEEconomicsRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    revenue_m: float = Field(..., ge=0, description="Annual revenue €M")
    sector: str = Field(..., description="NACE sector key")
    current_emissions_tco2: float = Field(..., ge=0, description="Current Scope 1+2+3 tCO2e/yr")
    nze_year: int = Field(2050, ge=2030, le=2060, description="Target NZE year")
    discount_rate: Optional[float] = Field(0.08, ge=0.01, le=0.25, description="NPV discount rate (decimal)")


class ETSShadowRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    eu_ets_verified_tco2: float = Field(..., ge=0, description="EU ETS verified annual emissions tCO2e")
    free_allocation_tco2: float = Field(0.0, ge=0, description="Free allocation received tCO2e")
    ets2_fuel_consumption_gj: Optional[float] = Field(
        None, ge=0,
        description="Fuel consumed (GJ/yr) in ETS2-covered activities (buildings, road transport)",
    )


class ICPFullAssessmentRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    mechanism_type: str = Field("shadow_price")
    target_year: int = Field(2030, ge=2024, le=2050)
    sbti_target: str = Field("1.5C")
    current_icp: Optional[float] = None
    # Scope emissions
    scope1_tco2: Optional[float] = None
    scope2_tco2: Optional[float] = None
    scope3_tco2: Optional[float] = None
    icp_eur: Optional[float] = None
    ebitda_m: Optional[float] = None
    # Carbon budget
    base_year: Optional[int] = 2019
    base_year_emissions_tco2: Optional[float] = None
    actual_emissions_tco2: Optional[float] = None
    # Abatement + NZE
    sector: Optional[str] = None
    current_emissions_tco2: Optional[float] = None
    target_reduction_pct: Optional[float] = 50.0
    revenue_m: Optional[float] = None
    nze_year: Optional[int] = 2050
    discount_rate: Optional[float] = 0.08
    # ETS
    eu_ets_verified_tco2: Optional[float] = None
    free_allocation_tco2: Optional[float] = 0.0
    ets2_fuel_consumption_gj: Optional[float] = None


# ---------------------------------------------------------------------------
# POST Endpoints
# ---------------------------------------------------------------------------

@router.post("/design-mechanism", summary="Design ICP mechanism and SBTi alignment check")
async def design_mechanism(req: ICPMechanismRequest) -> Dict[str, Any]:
    """
    Design an internal carbon pricing mechanism and verify SBTi alignment.

    Returns recommended shadow price, price trajectory 2024-target_year,
    alignment status vs SBTi minimums, and mechanism design guidance.

    Reference: IPCC AR6 WG3 (2022); SBTi Corporate Manual v2 (2023).
    """
    try:
        result = _engine.design_icp_mechanism(
            entity_id=req.entity_id,
            mechanism_type=req.mechanism_type,
            target_year=req.target_year,
            sbti_target=req.sbti_target,
            current_icp=req.current_icp,
        )
        return {"status": "success", "data": result}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.exception("design_mechanism error: %s", exc)
        raise HTTPException(status_code=500, detail="ICP mechanism design failed")


@router.post("/scope-cost-allocation", summary="Scope 1/2/3 carbon cost allocation at ICP")
async def scope_cost_allocation(req: ScopeCostAllocationRequest) -> Dict[str, Any]:
    """
    Allocate carbon costs across Scope 1, 2 and 3 using the internal carbon price.

    Returns cost per scope, total carbon liability, % of EBITDA,
    and business-unit level breakdown if provided.

    Reference: GHG Protocol Corporate Standard (2011, Scope 2 Guidance 2015).
    """
    try:
        result = _engine.calculate_scope_cost_allocation(
            entity_id=req.entity_id,
            scope1_tco2=req.scope1_tco2,
            scope2_tco2=req.scope2_tco2,
            scope3_tco2=req.scope3_tco2,
            icp_eur=req.icp_eur_per_tco2,
            ebitda_m=req.ebitda_m,
            business_units=req.business_units,
        )
        return {"status": "success", "data": result}
    except Exception as exc:
        logger.exception("scope_cost_allocation error: %s", exc)
        raise HTTPException(status_code=500, detail="Scope cost allocation failed")


@router.post("/carbon-budget-tracking", summary="Carbon budget vs SBTi target trajectory")
async def carbon_budget_tracking(req: CarbonBudgetRequest) -> Dict[str, Any]:
    """
    Track the entity's carbon budget against its SBTi-aligned emissions trajectory.

    Returns on-track status, remaining budget to 2050, annual reduction required,
    cumulative overshoot/undershoot, and year-by-year trajectory table.

    Reference: SBTi Corporate Manual v2 §4 (2023); SBTi Net-Zero Standard v1.1.
    """
    try:
        result = _engine.track_carbon_budget(
            entity_id=req.entity_id,
            base_year=req.base_year,
            base_year_emissions_tco2=req.base_year_emissions_tco2,
            sbti_target=req.sbti_target,
            current_year=req.current_year,
            actual_emissions_tco2=req.actual_emissions_tco2,
        )
        return {"status": "success", "data": result}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.exception("carbon_budget_tracking error: %s", exc)
        raise HTTPException(status_code=500, detail="Carbon budget tracking failed")


@router.post("/abatement-cost-curve", summary="Marginal abatement cost (MAC) curve analysis")
async def abatement_cost_curve(req: AbatementCurveRequest) -> Dict[str, Any]:
    """
    Build a marginal abatement cost curve ordered cheapest-first (McKinsey MAC convention).

    Returns ordered abatement measures, cumulative reduction potential,
    total investment required, and payback analysis.

    Reference: McKinsey MAC 2023; IEA Technology Perspectives 2023; BloombergNEF LCOE 2024.
    """
    try:
        result = _engine.build_abatement_cost_curve(
            entity_id=req.entity_id,
            sector=req.sector,
            current_emissions_tco2=req.current_emissions_tco2,
            target_reduction_pct=req.target_reduction_pct,
            max_capex_m=req.max_capex_m,
        )
        return {"status": "success", "data": result}
    except Exception as exc:
        logger.exception("abatement_cost_curve error: %s", exc)
        raise HTTPException(status_code=500, detail="Abatement cost curve generation failed")


@router.post("/nze-economics", summary="Net-zero economics: NPV, IRR, payback")
async def nze_economics(req: NZEEconomicsRequest) -> Dict[str, Any]:
    """
    Calculate net-zero economics including NZE capex, opex savings, NPV, IRR,
    payback years and per-tonne abatement cost.

    Reference: IEA World Energy Outlook 2023 NZE §2.4; IPCC AR6 WG3 §16.2.
    """
    try:
        result = _engine.calculate_nze_economics(
            entity_id=req.entity_id,
            revenue_m=req.revenue_m,
            sector=req.sector,
            current_emissions_tco2=req.current_emissions_tco2,
            nze_year=req.nze_year,
            discount_rate=req.discount_rate or 0.08,
        )
        return {"status": "success", "data": result}
    except Exception as exc:
        logger.exception("nze_economics error: %s", exc)
        raise HTTPException(status_code=500, detail="NZE economics calculation failed")


@router.post("/ets-shadow-exposure", summary="EU ETS Phase 4 + ETS2 carbon liability trajectory")
async def ets_shadow_exposure(req: ETSShadowRequest) -> Dict[str, Any]:
    """
    Calculate EU ETS Phase 4 compliance obligation and ETS2 estimated liability
    through a 2024-2050 price trajectory including CBAM free-allocation phase-out.

    Reference: EU ETS Phase 4 Directive 2003/87/EC as amended 2023/958;
    ETS2 Directive (EU) 2023/959; EU CBAM Regulation 2023/956.
    """
    try:
        result = _engine.assess_ets_shadow_exposure(
            entity_id=req.entity_id,
            eu_ets_verified_tco2=req.eu_ets_verified_tco2,
            free_allocation_tco2=req.free_allocation_tco2,
            ets2_fuel_consumption_gj=req.ets2_fuel_consumption_gj,
        )
        return {"status": "success", "data": result}
    except Exception as exc:
        logger.exception("ets_shadow_exposure error: %s", exc)
        raise HTTPException(status_code=500, detail="ETS shadow exposure assessment failed")


@router.post("/full-assessment", summary="Complete ICP assessment — all sub-modules")
async def full_assessment(req: ICPFullAssessmentRequest) -> Dict[str, Any]:
    """
    Orchestrate all ICP sub-assessments (mechanism design, scope allocation,
    carbon budget, abatement curve, NZE economics, ETS exposure).

    Returns an icp_maturity_score (0-100) and tier:
    Leader (≥85) | Advanced (≥70) | Developing (≥50) | Early (≥30) | Absent (<30).

    Reference: IPCC AR6 WG3 (2022); SBTi Corporate Manual v2 (2023);
    EU ETS Phase 4 Directive 2023/958; ETS2 Directive 2023/959.
    """
    try:
        request_data = req.model_dump(exclude_none=True)
        entity_id = request_data.pop("entity_id")
        result = _engine.run_full_assessment(entity_id=entity_id, request_data=request_data)
        return {"status": "success", "data": result}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.exception("full_assessment error: %s", exc)
        raise HTTPException(status_code=500, detail="Full ICP assessment failed")


# ---------------------------------------------------------------------------
# GET Reference Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/mechanism-types", summary="ICP mechanism types reference data")
async def ref_mechanism_types() -> Dict[str, Any]:
    """
    Return the 5 internal carbon pricing mechanism types with descriptions,
    use cases and SBTi recommendation flag.
    """
    return {
        "status": "success",
        "count": len(ICP_MECHANISM_TYPES),
        "data": ICP_MECHANISM_TYPES,
        "ref": "CDP Internal Carbon Pricing 2021; SBTi Corporate Manual v2 §5.3",
    }


@router.get("/ref/sbti-guidance", summary="SBTi minimum ICP price guidance by temperature target")
async def ref_sbti_guidance() -> Dict[str, Any]:
    """
    Return SBTi ICP minimum and recommended prices by temperature target (1.5°C / 2°C)
    and milestone year.

    Reference: IPCC AR6 WG3 Table 3.SM.1 (2022); SBTi Corporate Manual v2 §5.3.
    """
    return {
        "status": "success",
        "data": SBTI_ICP_GUIDANCE,
        "ref": "IPCC AR6 WG3 SPM (2022); SBTi Corporate Manual v2 (2023)",
    }


@router.get("/ref/ets-price-trajectory", summary="EU ETS Phase 4 + ETS2 price trajectories 2024-2050")
async def ref_ets_price_trajectory() -> Dict[str, Any]:
    """
    Return EU ETS (Phase 4) and ETS2 carbon price trajectories in EUR/tCO2e
    from 2024 to 2050.

    Reference: EU ETS Phase 4 Directive 2003/87/EC as amended 2023/958;
    ETS2 Directive (EU) 2023/959; EEX settlement curve; ICF/ICIS analyst consensus.
    """
    combined = {}
    for year in sorted(set(list(EU_ETS_PRICE_TRAJECTORY.keys()) + list(ETS2_PRICE_TRAJECTORY.keys()))):
        combined[year] = {
            "eu_ets_phase4_eur_t": EU_ETS_PRICE_TRAJECTORY.get(year),
            "ets2_buildings_transport_eur_t": ETS2_PRICE_TRAJECTORY.get(year),
        }
    return {
        "status": "success",
        "eu_ets_current_eur_t": EU_ETS_PRICE_TRAJECTORY.get(2024),
        "ets2_start_year": 2027,
        "data": combined,
        "ref": (
            "EU ETS Phase 4 Directive 2003/87/EC (amended 2023/958); "
            "ETS2 Directive (EU) 2023/959; EEX futures; ICIS analyst consensus 2024"
        ),
    }


@router.get("/ref/abatement-benchmarks", summary="20 abatement measures with MAC benchmarks")
async def ref_abatement_benchmarks() -> Dict[str, Any]:
    """
    Return 20 marginal abatement cost (MAC) benchmarks including cost/tCO2e,
    maximum reduction potential, implementation timeline, and capex estimates.

    Reference: McKinsey MAC Curve 2023; IEA Technology Perspectives 2023;
    BloombergNEF LCOE 2024.
    """
    summary = []
    for key, val in ABATEMENT_COST_BENCHMARKS.items():
        summary.append({
            "measure_key": key,
            "description": val["description"],
            "cost_eur_tco2e": val["cost_eur_tco2e"],
            "max_reduction_tco2e_yr": val["max_reduction_tco2e_yr"],
            "implementation_years": val["implementation_years"],
            "capex_m_per_100ktco2": val["capex_m_per_100ktco2"],
            "cost_category": (
                "negative_cost" if val["cost_eur_tco2e"] < 0
                else "low" if val["cost_eur_tco2e"] < 50
                else "medium" if val["cost_eur_tco2e"] < 150
                else "high"
            ),
        })
    summary.sort(key=lambda x: x["cost_eur_tco2e"])

    return {
        "status": "success",
        "count": len(summary),
        "data": summary,
        "ref": "McKinsey MAC 2023; IEA Technology Perspectives 2023; BloombergNEF LCOE 2024",
    }

