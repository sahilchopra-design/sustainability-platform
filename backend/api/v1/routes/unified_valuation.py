"""
Unified Valuation Engine — API Routes
Covers all 7 asset classes: Infrastructure, Project, Energy, Commercial,
Residential, Agricultural, Land — with full methodology reconciliation,
ESG overlay, and validation summary output.

Compliant with: RICS Red Book PS1/VPS4, IVS 2024, USPAP, TEGoVA EVS
"""
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Unified Asset Valuation"])


# ── Pydantic request schemas ──────────────────────────────────────────────────

class ESGInputs(BaseModel):
    epc_rating: str = Field("D", description="EPC label A-G")
    energy_intensity_kwh_m2: float = Field(0.0, ge=0)
    carbon_intensity_kgco2_m2: float = Field(0.0, ge=0)
    flood_risk: str = Field("none", description="none|low|medium|high|extreme")
    heat_risk_score: float = Field(0.0, ge=0, le=100)
    physical_risk_score: float = Field(0.0, ge=0, le=100)
    transition_risk_score: float = Field(0.0, ge=0, le=100)
    water_stress_score: float = Field(0.0, ge=0, le=5)
    biodiversity_sensitivity: str = Field("low", description="low|medium|high|critical")
    has_green_certification: bool = False
    certification_type: str = ""
    sbti_aligned: bool = False
    climate_scenario: str = Field("below_2c", description="nze_1_5c|below_2c|ndc_2_5c|current_policies_3c")
    assessment_year: int = 2024
    target_year: int = 2035


class InfrastructureInputsReq(BaseModel):
    subtype: str = Field("regulated_utility",
        description="regulated_utility|toll_road|rail|port|airport|social_infra|telecom_tower|data_centre|bridge_tunnel")
    regulated_asset_base_value: float = Field(0.0, ge=0, description="RAB value (USD/GBP)")
    allowed_return_on_rab_pct: float = Field(6.5, description="Allowed WACC % on RAB")
    regulatory_period_years: int = Field(5, ge=1)
    annual_revenue: float = Field(0.0, ge=0)
    annual_opex: float = Field(0.0, ge=0)
    annual_capex: float = Field(0.0, ge=0)
    discount_rate_pct: float = Field(7.0, ge=0)
    projection_years: int = Field(30, ge=5, le=60)
    terminal_growth_pct: float = Field(2.0)
    replacement_cost: float = Field(0.0, ge=0)
    asset_age_years: int = Field(0, ge=0)
    useful_life_years: int = Field(40, ge=10)
    regulatory_risk_premium_bps: int = Field(0, ge=0, le=500)


class ProjectInputsReq(BaseModel):
    subtype: str = Field("ppp_availability",
        description="ppp_availability|ppp_demand|concession|greenfield|brownfield|mining_project")
    total_project_cost: float = Field(0.0, ge=0)
    equity_contribution_pct: float = Field(20.0, ge=0, le=100)
    annual_revenue: float = Field(0.0, ge=0)
    annual_opex: float = Field(0.0, ge=0)
    annual_debt_service: float = Field(0.0, ge=0)
    concession_years: int = Field(25, ge=1)
    construction_years: int = Field(3, ge=0)
    debt_interest_rate_pct: float = Field(5.5)
    equity_irr_target_pct: float = Field(12.0)
    project_irr_target_pct: float = Field(8.0)
    dscr_minimum: float = Field(1.20)
    revenue_ramp_years: int = Field(3, ge=0)
    ramp_factor: float = Field(0.70, ge=0, le=1)
    senior_debt_pct: float = Field(70.0, ge=0, le=100)


class EnergyInputsReq(BaseModel):
    subtype: str = Field("solar_pv",
        description="solar_pv|wind_onshore|wind_offshore|gas_ccgt|gas_ocgt|coal|nuclear|hydro|biomass|battery_storage|hydrogen|geothermal|solar_csp|offshore_wind_float")
    nameplate_capacity_mw: float = Field(0.0, ge=0)
    capacity_factor_pct: float = Field(0.0, ge=0, le=100)
    annual_generation_mwh: float = Field(0.0, ge=0)
    ppa_price_usd_mwh: float = Field(0.0, ge=0)
    merchant_price_usd_mwh: float = Field(0.0, ge=0)
    ppa_coverage_pct: float = Field(100.0, ge=0, le=100)
    ppa_duration_years: int = Field(15, ge=1)
    annual_opex_usd_kw: float = Field(0.0, ge=0)
    annual_degradation_pct: float = Field(0.0, ge=0, le=5)
    construction_cost_usd_kw: float = Field(0.0, ge=0)
    discount_rate_pct: float = Field(7.5)
    asset_life_years: int = Field(25, ge=5)
    decommissioning_cost_usd: float = Field(0.0, ge=0)
    eu_ets_price_eur_tco2: float = Field(65.0, ge=0)
    annual_co2_tonnes: float = Field(0.0, ge=0)


class CommercialInputsReq(BaseModel):
    subtype: str = Field("office_prime",
        description="office_prime|office_secondary|retail_high_street|retail_shopping_centre|retail_park|industrial_logistics|light_industrial|hotel_full_service|hotel_limited|data_centre|healthcare|student_housing|senior_living|mixed_use")
    gross_floor_area_m2: float = Field(0.0, ge=0)
    net_lettable_area_m2: float = Field(0.0, ge=0, description="If 0, computed as 85% of GFA")
    passing_rent_psm_pa: float = Field(0.0, ge=0)
    market_rent_psm_pa: float = Field(0.0, ge=0, description="ERV — market rent per m²/year")
    occupancy_rate_pct: float = Field(95.0, ge=0, le=100)
    vacancy_cost_psm: float = Field(0.0, ge=0)
    service_charge_psm: float = Field(0.0, ge=0)
    management_fee_pct: float = Field(3.0, ge=0, le=20)
    capex_reserve_psm: float = Field(0.0, ge=0)
    initial_yield_pct: float = Field(0.0, ge=0, description="Cap rate; 0 = use market default")
    discount_rate_pct: float = Field(7.0)
    exit_yield_pct: float = Field(0.0, ge=0, description="Terminal cap rate; 0 = initial+0.25%")
    rent_growth_pct_pa: float = Field(2.0)
    lease_term_years: int = Field(10, ge=1)
    void_period_months: int = Field(6, ge=0)
    lease_incentive_months: int = Field(6, ge=0)
    projection_years: int = Field(10, ge=1, le=30)
    year_built: int = Field(2000, ge=1800)
    last_refurbishment_year: Optional[int] = None
    land_value_pct: float = Field(20.0, ge=0, le=80)


class ResidentialInputsReq(BaseModel):
    subtype: str = Field("multifamily",
        description="single_family|multifamily|build_to_rent|affordable|social_housing|student")
    units: int = Field(0, ge=0)
    avg_unit_size_m2: float = Field(0.0, ge=0)
    avg_monthly_rent_per_unit: float = Field(0.0, ge=0)
    occupancy_rate_pct: float = Field(95.0, ge=0, le=100)
    annual_opex_per_unit: float = Field(0.0, ge=0)
    capex_reserve_pct: float = Field(5.0, ge=0, le=20)
    gross_yield_market_pct: float = Field(0.0, ge=0, description="0 = use market default")
    discount_rate_pct: float = Field(6.5)
    exit_yield_pct: float = Field(0.0, ge=0)
    rent_growth_pct_pa: float = Field(2.5)
    projection_years: int = Field(10, ge=1, le=30)
    comparable_prices_per_m2: List[float] = Field(default_factory=list)
    comparable_adjustments: List[float] = Field(default_factory=list)


class AgriculturalInputsReq(BaseModel):
    subtype: str = Field("arable",
        description="arable|permanent_pasture|mixed_farming|horticulture|plantation|forestry|aquaculture|organic_farm")
    area_hectares: float = Field(0.0, ge=0)
    soil_quality_score: float = Field(3.0, ge=1, le=5, description="1=poor, 5=excellent")
    annual_crop_yield_tonnes_ha: float = Field(0.0, ge=0)
    commodity_price_usd_tonne: float = Field(0.0, ge=0)
    annual_opex_usd_ha: float = Field(0.0, ge=0)
    comparable_land_price_usd_ha: float = Field(0.0, ge=0, description="0 = use market default")
    agricultural_subsidy_usd_ha: float = Field(0.0, ge=0)
    discount_rate_pct: float = Field(5.0)
    projection_years: int = Field(20, ge=5, le=50)
    # Forestry-specific
    timber_species: str = ""
    timber_rotation_years: int = Field(35, ge=0)
    standing_timber_value_usd_m3: float = Field(0.0, ge=0)
    estimated_timber_volume_m3_ha: float = Field(0.0, ge=0)
    carbon_sequestration_tco2e_ha_yr: float = Field(0.0, ge=0)
    carbon_credit_price_usd: float = Field(25.0, ge=0)
    woodland_carbon_code: bool = False


class LandInputsReq(BaseModel):
    subtype: str = Field("residential_dev",
        description="residential_dev|commercial_dev|industrial_dev|mixed_use_dev|brownfield|greenfield|rural_bare|strategic_land|carbon_land")
    site_area_hectares: float = Field(0.0, ge=0)
    # Residual method inputs
    gross_development_value: float = Field(0.0, ge=0, description="GDV — total value of completed development")
    total_development_cost: float = Field(0.0, ge=0, description="Hard + soft construction costs")
    developer_profit_pct: float = Field(20.0, ge=0, le=50, description="% of GDV")
    finance_cost_pct: float = Field(6.0, ge=0, le=20, description="Annualised finance cost %")
    development_period_years: float = Field(2.0, ge=0.5, le=15)
    planning_risk_discount_pct: float = Field(0.0, ge=0, le=50, description="Risk discount for planning uncertainty")
    remediation_cost: float = Field(0.0, ge=0, description="Brownfield remediation / decontamination cost")
    # Strategic land / comparable
    existing_use_value_ha: float = Field(0.0, ge=0, description="EUV per hectare for planning uplift")
    planning_uplift_multiple: float = Field(1.0, ge=1, le=100, description="Planning uplift multiplier over EUV")
    comparable_land_prices_ha: List[float] = Field(default_factory=list, description="Comparable land prices (£/ha)")
    # Carbon land
    peatland_depth_m: float = Field(0.0, ge=0)
    carbon_sequestration_potential_tco2e_ha: float = Field(0.0, ge=0)


class ValuationRequest(BaseModel):
    asset_class: str = Field(..., description="infrastructure|project|energy|commercial|residential|agricultural|land")
    asset_name: str = Field("", description="Descriptive name for the asset")
    country_iso: str = Field("GB", description="ISO 3166-1 alpha-2 country code")
    currency: str = Field("GBP", description="ISO 4217 currency code")
    valuation_date: Optional[str] = Field(None, description="YYYY-MM-DD; defaults to today")
    valuation_standard: str = Field("RICS_Red_Book", description="RICS_Red_Book|IVS_2024|USPAP|TEGoVA_EVS")
    esg: ESGInputs = Field(default_factory=ESGInputs)
    inputs: Dict[str, Any] = Field(..., description="Asset-class-specific input parameters")


class SensitivityRequest(BaseModel):
    """Run a sensitivity analysis varying one parameter over a range."""
    base_request: ValuationRequest
    parameter_path: str = Field(..., description="dot-path into inputs dict, e.g. 'market_rent_psm_pa'")
    low_value: float
    mid_value: float
    high_value: float
    label: str = ""


class BatchValuationRequest(BaseModel):
    """Batch multiple valuations in a single call (up to 20)."""
    valuations: List[ValuationRequest] = Field(..., min_items=1, max_items=20)


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/valuation/calculate")
async def calculate_valuation(request: ValuationRequest):
    """
    Run a full valuation for any asset class.

    Returns reconciled value, method breakdown, ESG adjustment, value range,
    per-unit/m²/kW metrics, and a full validation summary.

    Compliant with RICS Red Book PS1/VPS4, IVS 2024, USPAP, TEGoVA EVS.
    """
    try:
        from services.unified_valuation_engine import run_valuation
        result = run_valuation({
            "asset_class": request.asset_class,
            "asset_name": request.asset_name,
            "country_iso": request.country_iso,
            "currency": request.currency,
            "valuation_date": request.valuation_date,
            "valuation_standard": request.valuation_standard,
            "esg": request.esg.model_dump(),
            "inputs": request.inputs,
        })
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("Valuation calculation failed")
        raise HTTPException(status_code=500, detail=f"Valuation engine error: {str(e)}")


@router.post("/valuation/sensitivity")
async def run_sensitivity_analysis(request: SensitivityRequest):
    """
    Run a 3-scenario sensitivity analysis (low / mid / high) on one input parameter.
    Returns value under each scenario, delta vs mid, and percentage change.
    """
    try:
        from services.unified_valuation_engine import run_valuation
        import copy

        results = {}
        scenarios = {"low": request.low_value, "mid": request.mid_value, "high": request.high_value}

        for label, value in scenarios.items():
            req_dict = {
                "asset_class": request.base_request.asset_class,
                "asset_name": request.base_request.asset_name,
                "country_iso": request.base_request.country_iso,
                "currency": request.base_request.currency,
                "valuation_date": request.base_request.valuation_date,
                "valuation_standard": request.base_request.valuation_standard,
                "esg": request.base_request.esg.model_dump(),
                "inputs": copy.deepcopy(request.base_request.inputs),
            }
            # Apply the parameter tweak
            keys = request.parameter_path.split(".")
            target = req_dict["inputs"]
            for k in keys[:-1]:
                target = target[k]
            target[keys[-1]] = value

            res = run_valuation(req_dict)
            results[label] = {
                "parameter_value": value,
                "final_value": res["final_value"],
                "value_range_low": res["value_range_low"],
                "value_range_high": res["value_range_high"],
                "esg_adjustment_pct": res["esg_adjustment_pct"],
            }

        mid_val = results["mid"]["final_value"]
        for lbl, r in results.items():
            r["delta_vs_mid"] = r["final_value"] - mid_val
            r["pct_change_vs_mid"] = ((r["final_value"] - mid_val) / mid_val * 100) if mid_val else 0

        return {
            "parameter": request.parameter_path,
            "label": request.label or request.parameter_path,
            "currency": request.base_request.currency,
            "scenarios": results,
        }
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("Sensitivity analysis failed")
        raise HTTPException(status_code=500, detail=f"Sensitivity engine error: {str(e)}")


@router.post("/valuation/batch")
async def batch_valuations(request: BatchValuationRequest):
    """
    Run up to 20 valuations in a single request.
    Useful for portfolio-level valuation passes or scenario comparison.
    Returns each result plus a portfolio summary (total value, avg ESG adjustment).
    """
    try:
        from services.unified_valuation_engine import run_valuation
        results = []
        errors = []

        for i, val_req in enumerate(request.valuations):
            try:
                res = run_valuation({
                    "asset_class": val_req.asset_class,
                    "asset_name": val_req.asset_name,
                    "country_iso": val_req.country_iso,
                    "currency": val_req.currency,
                    "valuation_date": val_req.valuation_date,
                    "valuation_standard": val_req.valuation_standard,
                    "esg": val_req.esg.model_dump(),
                    "inputs": val_req.inputs,
                })
                results.append({"index": i, "status": "ok", **res})
            except Exception as e:
                errors.append({"index": i, "asset_name": val_req.asset_name, "error": str(e)})

        total_value = sum(r["final_value"] for r in results)
        avg_esg_adj = (sum(r["esg_adjustment_pct"] for r in results) / len(results)) if results else 0

        return {
            "count_requested": len(request.valuations),
            "count_succeeded": len(results),
            "count_failed": len(errors),
            "portfolio_total_value": total_value,
            "avg_esg_adjustment_pct": round(avg_esg_adj, 2),
            "results": results,
            "errors": errors,
        }
    except Exception as e:
        logger.exception("Batch valuation failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/valuation/schema/{asset_class}")
async def get_input_schema(asset_class: str):
    """
    Return the input field schema and default values for a given asset class.
    Useful for dynamically rendering forms on the frontend.
    """
    schemas = {
        "infrastructure": InfrastructureInputsReq.model_json_schema(),
        "project": ProjectInputsReq.model_json_schema(),
        "energy": EnergyInputsReq.model_json_schema(),
        "commercial": CommercialInputsReq.model_json_schema(),
        "residential": ResidentialInputsReq.model_json_schema(),
        "agricultural": AgriculturalInputsReq.model_json_schema(),
        "land": LandInputsReq.model_json_schema(),
    }
    schema = schemas.get(asset_class.lower())
    if not schema:
        raise HTTPException(status_code=404, detail=f"Unknown asset class: {asset_class}. "
                            f"Valid: {list(schemas.keys())}")
    return {"asset_class": asset_class, "schema": schema, "esg_schema": ESGInputs.model_json_schema()}


@router.get("/valuation/asset-classes")
async def list_asset_classes():
    """
    List all supported asset classes, subtypes, and applicable methodologies.
    """
    return {
        "asset_classes": [
            {
                "id": "infrastructure",
                "label": "Infrastructure",
                "description": "Regulated utilities, transport, social infrastructure, telecom, data centres",
                "subtypes": ["regulated_utility", "toll_road", "rail", "port", "airport",
                             "social_infra", "telecom_tower", "data_centre", "bridge_tunnel"],
                "methodologies": ["Regulated Asset Base (RAB)", "Income DCF", "Replacement Cost"],
                "standards": ["RICS Red Book PS1", "IVS 400", "IPEV", "Basel III"],
            },
            {
                "id": "project",
                "label": "Project Finance",
                "description": "PPP availability/demand, concessions, greenfield, brownfield, mining",
                "subtypes": ["ppp_availability", "ppp_demand", "concession", "greenfield", "brownfield", "mining_project"],
                "methodologies": ["Project Finance DCF (DSCR)", "Replacement Cost"],
                "standards": ["IVS 400 Project Finance", "RICS GN Infrastructure", "Equator Principles"],
            },
            {
                "id": "energy",
                "label": "Energy & Power",
                "description": "Solar PV, wind, gas, nuclear, hydro, storage, hydrogen, geothermal",
                "subtypes": ["solar_pv", "wind_onshore", "wind_offshore", "gas_ccgt", "gas_ocgt",
                             "coal", "nuclear", "hydro", "biomass", "battery_storage",
                             "hydrogen", "geothermal", "solar_csp", "offshore_wind_float"],
                "methodologies": ["Energy Yield DCF", "Replacement Cost", "NAV (EV/EBITDA)"],
                "standards": ["IVS 400", "RICS VPS2", "EU ETS Carbon Pricing", "IEA NZE Scenario"],
            },
            {
                "id": "commercial",
                "label": "Commercial Real Estate",
                "description": "Office, retail, industrial, hotel, data centre, healthcare, student housing",
                "subtypes": ["office_prime", "office_secondary", "retail_high_street",
                             "retail_shopping_centre", "retail_park", "industrial_logistics",
                             "light_industrial", "hotel_full_service", "hotel_limited",
                             "data_centre", "healthcare", "student_housing", "senior_living", "mixed_use"],
                "methodologies": ["Direct Capitalisation", "10-Year Income DCF", "Replacement Cost (BCIS/RS Means)"],
                "standards": ["RICS Red Book VPS2/VPS4", "IVS 105", "IPEV", "INREV NAV", "CRREM v2"],
            },
            {
                "id": "residential",
                "label": "Residential Real Estate",
                "description": "Single-family, multifamily, BTR, affordable, social housing, student",
                "subtypes": ["single_family", "multifamily", "build_to_rent", "affordable",
                             "social_housing", "student"],
                "methodologies": ["Direct Capitalisation (Gross Yield)", "DCF", "Sales Comparison / Hedonic"],
                "standards": ["RICS Red Book VPS2", "USPAP SR1-2", "TEGoVA EVS"],
            },
            {
                "id": "agricultural",
                "label": "Agricultural & Forestry",
                "description": "Arable, pasture, horticulture, plantation, forestry, aquaculture",
                "subtypes": ["arable", "permanent_pasture", "mixed_farming", "horticulture",
                             "plantation", "forestry", "aquaculture", "organic_farm"],
                "methodologies": ["Income/Crop DCF", "Comparable Sales", "Timber + Carbon Value"],
                "standards": ["RICS Rural Valuation", "CAAV Guidance", "Woodland Carbon Code", "REDD+"],
            },
            {
                "id": "land",
                "label": "Development Land",
                "description": "Residential/commercial/industrial dev land, brownfield, greenfield, carbon land",
                "subtypes": ["residential_dev", "commercial_dev", "industrial_dev", "mixed_use_dev",
                             "brownfield", "greenfield", "rural_bare", "strategic_land", "carbon_land"],
                "methodologies": ["Residual Land Value (GDV basis)", "Comparable Sales", "Planning Uplift", "Carbon Land Value"],
                "standards": ["RICS GN Development Land", "NPPF Hope Value", "VCM Carbon Pricing"],
            },
        ],
        "esg_scenarios": [
            {"id": "nze_1_5c", "label": "Net Zero 1.5°C (NGFS NZE)"},
            {"id": "below_2c", "label": "Below 2°C (NGFS B2DS)"},
            {"id": "ndc_2_5c", "label": "NDC ~2.5°C"},
            {"id": "current_policies_3c", "label": "Current Policies 3°C+"},
        ],
        "valuation_standards": ["RICS_Red_Book", "IVS_2024", "USPAP", "TEGoVA_EVS"],
    }
