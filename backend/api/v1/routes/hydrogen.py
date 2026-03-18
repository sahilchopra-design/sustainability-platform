"""
Hydrogen Economy Routes — RFNBO / LCOH / EU H2 Bank / Cost Trajectories
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from services.hydrogen_economy_engine import HydrogenEconomyEngine

router = APIRouter(prefix="/api/v1/hydrogen", tags=["hydrogen"])
engine = HydrogenEconomyEngine()


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class LCOHRequest(BaseModel):
    entity_id: str = Field(..., description="Project identifier")
    production_pathway: str = Field("electrolysis_solar", description="Production pathway key")
    capacity_mw_el: float = Field(100.0, gt=0, description="Electrolyser capacity (MW electrical)")
    country_code: str = Field("DE", description="ISO 2-letter country code")
    capacity_factor_pct: float = Field(30.0, ge=5.0, le=95.0, description="Capacity factor (%)")
    financing_cost_pct: float = Field(7.0, ge=0.0, le=30.0, description="Weighted avg cost of capital (%)")
    year: int = Field(2024, ge=2024, le=2050, description="Projection year")


class RFNBORequest(BaseModel):
    entity_id: str = Field(..., description="Project identifier")
    production_pathway: str = Field("electrolysis_solar", description="Production pathway key")
    country_code: str = Field("DE", description="ISO 2-letter country code")
    re_source: str = Field("new_solar", description="Renewable energy source type")
    hourly_matching: bool = Field(False, description="Hourly temporal correlation matching")
    temporal_correlation: bool = Field(True, description="Temporal correlation (monthly)")
    year: int = Field(2025, ge=2024, le=2035, description="Compliance year")


class DemandSectorRequest(BaseModel):
    entity_id: str = Field(..., description="Demand entity identifier")
    demand_sector: str = Field("steel", description="Demand sector (steel/ammonia/transport/refinery/power)")
    annual_h2_demand_t: float = Field(5000.0, gt=0, description="Annual H2 demand (tonnes)")
    country_code: str = Field("DE", description="ISO 2-letter country code")
    current_fuel_type: str = Field("natural_gas", description="Incumbent fuel being replaced")


class EUH2BankRequest(BaseModel):
    entity_id: str = Field(..., description="Project identifier")
    production_pathway: str = Field("electrolysis_wind", description="Production pathway key")
    capacity_mw_el: float = Field(200.0, gt=0, description="Electrolyser capacity (MW electrical)")
    country_code: str = Field("ES", description="ISO 2-letter country code")
    lcoh_usd_kg: float = Field(3.8, gt=0, description="Estimated LCOH (USD/kg)")


class CostTrajectoryRequest(BaseModel):
    entity_id: str = Field(..., description="Project identifier")
    production_pathway: str = Field("electrolysis_solar", description="Production pathway key")
    country_code: str = Field("CL", description="ISO 2-letter country code")


class ProjectItem(BaseModel):
    project_id: str = Field(..., description="Individual project identifier")
    production_pathway: str = Field("electrolysis_solar")
    capacity_mw_el: float = Field(100.0, gt=0)
    country_code: str = Field("DE")
    lcoh_usd_kg: float = Field(4.0, gt=0)
    annual_abatement_ktco2: Optional[float] = None
    project_irr_pct: Optional[float] = None


class PortfolioRequest(BaseModel):
    entity_id: str = Field(..., description="Portfolio owner identifier")
    projects: List[ProjectItem] = Field(..., min_items=1, description="List of H2 projects")


# ---------------------------------------------------------------------------
# POST Endpoints
# ---------------------------------------------------------------------------

@router.post("/lcoh", summary="Levelised Cost of Hydrogen (LCOH) Calculation")
async def lcoh(req: LCOHRequest):
    try:
        result = engine.calculate_lcoh(
            entity_id=req.entity_id,
            production_pathway=req.production_pathway,
            capacity_mw_el=req.capacity_mw_el,
            country_code=req.country_code,
            capacity_factor_pct=req.capacity_factor_pct,
            financing_cost_pct=req.financing_cost_pct,
            year=req.year,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rfnbo-compliance", summary="RFNBO Compliance Assessment (EU Delegated Act 2023/1184)")
async def rfnbo_compliance(req: RFNBORequest):
    try:
        result = engine.assess_rfnbo_compliance(
            entity_id=req.entity_id,
            production_pathway=req.production_pathway,
            country_code=req.country_code,
            re_source=req.re_source,
            hourly_matching=req.hourly_matching,
            temporal_correlation=req.temporal_correlation,
            year=req.year,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/demand-sector", summary="H2 Demand Sector Abatement & Economics")
async def demand_sector(req: DemandSectorRequest):
    try:
        result = engine.assess_demand_sector(
            entity_id=req.entity_id,
            demand_sector=req.demand_sector,
            annual_h2_demand_t=req.annual_h2_demand_t,
            country_code=req.country_code,
            current_fuel_type=req.current_fuel_type,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/eu-h2-bank", summary="EU Hydrogen Bank Eligibility & Subsidy Estimation")
async def eu_h2_bank(req: EUH2BankRequest):
    try:
        result = engine.assess_eu_h2_bank(
            entity_id=req.entity_id,
            production_pathway=req.production_pathway,
            capacity_mw_el=req.capacity_mw_el,
            country_code=req.country_code,
            lcoh_usd_kg=req.lcoh_usd_kg,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cost-trajectory", summary="H2 Cost Trajectory Projection 2024-2050")
async def cost_trajectory(req: CostTrajectoryRequest):
    try:
        result = engine.project_cost_trajectory(
            entity_id=req.entity_id,
            production_pathway=req.production_pathway,
            country_code=req.country_code,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portfolio", summary="H2 Portfolio-Level Assessment")
async def portfolio(req: PortfolioRequest):
    try:
        projects_dicts = [p.dict() for p in req.projects]
        result = engine.assess_portfolio(entity_id=req.entity_id, projects=projects_dicts)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# GET Reference Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/h2-colours", summary="Reference: H2 Colour Taxonomy")
def ref_h2_colours():
    from services.hydrogen_economy_engine import H2_COLOURS
    return {
        "h2_colours": H2_COLOURS,
        "rfnbo_ghg_threshold_kgco2e_kgh2": 3.38,
        "source": "EU Delegated Regulation 2023/1184; IEA Global Hydrogen Review 2023",
    }


@router.get("/ref/production-pathways", summary="Reference: H2 Production Pathways")
def ref_production_pathways():
    from services.hydrogen_economy_engine import PRODUCTION_PATHWAYS, RFNBO_CRITERIA
    return {
        "production_pathways": PRODUCTION_PATHWAYS,
        "rfnbo_criteria": RFNBO_CRITERIA,
        "source": "IRENA Green Hydrogen Cost Reduction 2020; EU Delegated Regulation 2023/1184",
    }


@router.get("/ref/country-costs", summary="Reference: Country Electricity Costs & Grid Carbon")
def ref_country_costs():
    from services.hydrogen_economy_engine import COUNTRY_ELECTRICITY_COST, EU_H2_BANK_ELIGIBILITY
    return {
        "country_electricity_costs": COUNTRY_ELECTRICITY_COST,
        "eu_h2_bank_eligibility": EU_H2_BANK_ELIGIBILITY,
        "source": "IEA World Energy Outlook 2023; BloombergNEF H2 Outlook 2023",
    }
