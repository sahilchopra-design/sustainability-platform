from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any

from services.carbon_price_ets_engine import (
    forecast_eu_ets_price,
    calculate_ets_compliance_cost,
    assess_cbam_exposure,
    calculate_portfolio_carbon_cost,
    forecast_carbon_price_pathway,
    ETS_SYSTEMS,
    IEA_CARBON_PRICE_PATHWAYS,
    CBAM_SECTORS,
    LEAKAGE_RISK_SECTORS,
    CHINA_ETS_SECTORS,
    EU_ETS_PHASE4_PARAMS,
)

router = APIRouter(prefix="/api/v1/carbon-price-ets", tags=["Carbon Price & ETS Analytics — E71"])

# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class ETSComplianceRequest(BaseModel):
    entity_id: str
    entity_name: Optional[str] = "Unknown Entity"
    sector: Optional[str] = "steel"
    annual_emissions_tco2: Optional[float] = None
    ebitda_usd: Optional[float] = None
    uk_operations_pct: Optional[float] = None
    california_operations_pct: Optional[float] = None
    china_operations_pct: Optional[float] = None


class EUETSForecastRequest(BaseModel):
    entity_id: Optional[str] = "default"
    horizon_years: Optional[int] = 10
    scenario: Optional[str] = "APS"


class CBAMExposureRequest(BaseModel):
    entity_id: str
    sector: Optional[str] = "steel"
    exporter_country: Optional[str] = "IN"
    importer_country: Optional[str] = "DE"
    import_volume_t: Optional[float] = None
    actual_carbon_intensity_tco2_t: Optional[float] = None
    exporter_carbon_price_usd_tco2: Optional[float] = None
    cbam_phase_in_pct: Optional[float] = 100.0


class PortfolioCarbonCostRequest(BaseModel):
    portfolio_id: str
    total_aum_usd: Optional[float] = None
    holdings: Optional[List[Dict[str, Any]]] = None


class PricePathwayRequest(BaseModel):
    entity_id: Optional[str] = "default"
    scenario: Optional[str] = "APS"
    horizon: Optional[int] = 25
    economy_type: Optional[str] = "advanced"


# ---------------------------------------------------------------------------
# POST Endpoints
# ---------------------------------------------------------------------------

@router.post("/ets-compliance")
async def ets_compliance_endpoint(request: ETSComplianceRequest) -> Dict[str, Any]:
    """Calculate compliance cost across all 6 ETS systems for a given entity."""
    try:
        result = calculate_ets_compliance_cost(request.dict())
        return {
            "status": "success",
            "entity_id": result.entity_id,
            "entity_name": result.entity_name,
            "sector": result.sector,
            "annual_emissions_tco2": result.annual_emissions_tco2,
            "eu_ets": {
                "allocation_tco2": result.eu_ets_allocation_tco2,
                "shortfall_tco2": result.eu_ets_shortfall_tco2,
                "cost_eur": result.eu_ets_cost_eur,
            },
            "uk_ets": {"cost_gbp": result.uk_ets_cost_gbp},
            "california": {"cost_usd": result.california_cost_usd},
            "china_ets": {"cost_cny": result.china_ets_cost_cny},
            "rggi": {"cost_usd": result.rggi_cost_usd},
            "total_carbon_cost_usd": result.total_carbon_cost_usd,
            "carbon_cost_pct_ebitda": result.carbon_cost_pct_ebitda,
            "abatement_cost_breakeven_usd_tco2": result.abatement_cost_breakeven_usd_tco2,
            "hedging_recommendation": result.hedging_recommendation,
            "ets_systems_covered": list(ETS_SYSTEMS.keys()),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/eu-ets-forecast")
async def eu_ets_forecast_endpoint(request: EUETSForecastRequest) -> Dict[str, Any]:
    """Forecast EU ETS price path using LRF, MSR dynamics, and supply/demand fundamentals."""
    try:
        horizon = min(30, max(1, request.horizon_years or 10))
        result = forecast_eu_ets_price(horizon, request.scenario or "APS", request.entity_id or "default")
        return {
            "status": "success",
            "scenario": result.scenario,
            "base_price_eur": result.base_price_eur,
            "price_path": result.price_path,
            "price_2030_eur": result.price_2030_eur,
            "price_2050_eur": result.price_2050_eur,
            "msr_impact_eur": result.msr_impact_eur,
            "lrf_impact_eur": result.lrf_impact_eur,
            "cbam_spillover_eur": result.cbam_spillover_eur,
            "confidence_interval_low": result.confidence_interval_low,
            "confidence_interval_high": result.confidence_interval_high,
            "key_drivers": result.key_drivers,
            "phase4_params": EU_ETS_PHASE4_PARAMS,
            "standard": "EU ETS Phase 4 Directive 2023/958 + MSR Decision 2018/410",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cbam-exposure")
async def cbam_exposure_endpoint(request: CBAMExposureRequest) -> Dict[str, Any]:
    """Assess EU CBAM certificate liability and competitiveness impact for a trade flow."""
    try:
        result = assess_cbam_exposure(request.dict())
        sector_data = CBAM_SECTORS.get(result.sector, {})
        return {
            "status": "success",
            "entity_id": result.entity_id,
            "trade_flow": {
                "exporter_country": result.exporter_country,
                "importer_country": result.importer_country,
                "sector": result.sector,
                "import_volume_t": result.import_volume_t,
            },
            "carbon_accounting": {
                "embedded_carbon_tco2": result.embedded_carbon_tco2,
                "actual_intensity_tco2_t": result.default_carbon_intensity_tco2_t,
                "eu_benchmark_tco2_t": result.eu_benchmark_tco2_t,
            },
            "cbam_liability": {
                "gross_cbam_cost_eur": result.cbam_certificate_cost_eur,
                "phase_in_pct": result.cbam_phase_in_pct,
                "effective_cbam_cost_eur": result.effective_cbam_cost_eur,
            },
            "competitiveness_impact_pct": result.competitiveness_impact_pct,
            "carbon_leakage_risk_score": result.leakage_risk_score,
            "mitigation_options": result.mitigation_options,
            "hs_codes": sector_data.get("hs_chapters", []),
            "cbam_phase_in_timeline": {
                "2023-2025": "Transitional / reporting only (Reg 2023/956)",
                "2026": "Full CBAM certificate purchases begin",
                "2034": "Free allocation phase-out complete (industry)",
            },
            "regulation": "EU CBAM Regulation 2023/956",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portfolio-carbon-cost")
async def portfolio_carbon_cost_endpoint(request: PortfolioCarbonCostRequest) -> Dict[str, Any]:
    """Calculate sector-weighted carbon cost, transition risk, and stranding probability."""
    try:
        result = calculate_portfolio_carbon_cost(request.dict())
        return {
            "status": "success",
            "portfolio_id": result.portfolio_id,
            "total_financed_emissions_tco2": result.total_financed_emissions_tco2,
            "weighted_carbon_cost_usd": result.weighted_carbon_cost_usd,
            "ets_exposure_breakdown": result.ets_exposure_breakdown,
            "risk_metrics": {
                "transition_risk_score": result.transition_risk_score,
                "stranding_probability": result.stranding_probability,
                "carbon_var_1yr_usd": result.carbon_var_1yr_usd,
                "paris_alignment_temperature": result.paris_alignment_temperature,
            },
            "concentration": {
                "high_carbon_concentration_pct": result.high_carbon_concentration_pct,
            },
            "abatement_pathway_cost_usd": result.abatement_pathway_cost_usd,
            "recommendations": result.recommendations,
            "pcaf_note": "Financed emissions calculated per PCAF Part A (listed equity/corporate bonds)",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/price-pathway")
async def price_pathway_endpoint(request: PricePathwayRequest) -> Dict[str, Any]:
    """Forecast IEA carbon price pathway with scenario uncertainty bands."""
    try:
        horizon = min(30, max(1, request.horizon or 25))
        result = forecast_carbon_price_pathway(
            request.scenario or "APS",
            horizon,
            request.economy_type or "advanced",
            request.entity_id or "default",
        )
        return {
            "status": "success",
            "scenario": result.scenario,
            "economy_type": result.economy_type,
            "year_prices": result.year_prices,
            "annual_growth_rate_pct": result.annual_growth_rate_pct,
            "uncertainty_range_pct": result.uncertainty_range_pct,
            "price_2030_usd": result.price_2030_usd,
            "price_2050_usd": result.price_2050_usd,
            "key_policy_milestones": result.key_policy_milestones,
            "source": "IEA World Energy Outlook 2023",
            "scenarios_available": list(IEA_CARBON_PRICE_PATHWAYS.keys()),
            "economy_types": ["advanced", "emerging", "developing"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# GET Reference Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/ets-systems")
async def ref_ets_systems() -> Dict[str, Any]:
    """All 6 ETS systems with current prices, caps, and sector coverage."""
    return {
        "ets_systems": ETS_SYSTEMS,
        "total_systems": len(ETS_SYSTEMS),
        "global_ets_coverage_pct_ghg": 23,
        "total_jurisdictions_with_carbon_pricing": 73,
        "global_carbon_revenue_2023_bn_usd": 95,
        "source": "World Bank Carbon Pricing Dashboard 2024",
        "note": "China ETS is intensity-based (not absolute cap); largest by covered emissions",
    }


@router.get("/ref/iea-pathways")
async def ref_iea_pathways() -> Dict[str, Any]:
    """IEA WEO 2023 carbon price pathways by scenario and economy type."""
    return {
        "pathways": IEA_CARBON_PRICE_PATHWAYS,
        "scenarios": {
            "NZE": "Net Zero Emissions by 2050 — 1.5°C aligned",
            "APS": "Announced Pledges Scenario — ~1.7°C",
            "SDS": "Sustainable Development Scenario — well below 2°C",
            "STEPS": "Stated Policies Scenario — ~2.4°C",
        },
        "economy_types": {
            "advanced": "OECD + EU member states",
            "emerging": "China, India, Brazil, South Africa, etc.",
            "developing": "Sub-Saharan Africa, smaller emerging markets",
        },
        "source": "IEA World Energy Outlook 2023, Chapter 3",
        "update_frequency": "Annual (WEO publication)",
    }


@router.get("/ref/cbam-sectors")
async def ref_cbam_sectors() -> Dict[str, Any]:
    """EU CBAM covered sectors with HS codes, benchmarks, and phase-in timeline."""
    return {
        "sectors": CBAM_SECTORS,
        "total_sectors": len(CBAM_SECTORS),
        "cbam_scope_extension_review": "2025 — additional sectors under consideration",
        "regulation": "EU CBAM Regulation (EU) 2023/956",
        "implementing_regulation": "(EU) 2023/1773 (MRV obligations)",
        "certificate_registry": "CBAM National Registry (national competent authorities)",
        "total_import_coverage_bn_eur": sum(
            s.get("import_bn_eur_from_noneu", 0) for s in CBAM_SECTORS.values()
        ),
        "phase4_params": EU_ETS_PHASE4_PARAMS,
    }


@router.get("/ref/leakage-risk")
async def ref_leakage_risk() -> Dict[str, Any]:
    """Carbon leakage risk by sector with trade intensity and CBAM coverage."""
    return {
        "sectors": LEAKAGE_RISK_SECTORS,
        "total_sectors": len(LEAKAGE_RISK_SECTORS),
        "methodology": "Trade intensity × carbon cost share (EU ETS Directive Annex I methodology)",
        "high_leakage_threshold": 0.70,
        "cbam_covered_sectors": [k for k, v in LEAKAGE_RISK_SECTORS.items() if v.get("cbam_covered")],
        "non_cbam_leakage_sectors": [k for k, v in LEAKAGE_RISK_SECTORS.items() if not v.get("cbam_covered")],
        "policy_reference": "EU ETS Directive Article 10b — Carbon Leakage List",
    }


@router.get("/ref/china-ets-sectors")
async def ref_china_ets_sectors() -> Dict[str, Any]:
    """China National ETS sector coverage with intensity benchmarks."""
    return {
        "sectors": CHINA_ETS_SECTORS,
        "total_sectors": len(CHINA_ETS_SECTORS),
        "total_covered_mt_co2": sum(s.get("coverage_mt_co2", 0) for s in CHINA_ETS_SECTORS.values()),
        "current_phase": "Phase 1+ (power sector operational; 7 others expanding)",
        "methodology": "Intensity-based (tCO2/unit output), not absolute cap",
        "current_price_cny": ETS_SYSTEMS["china_ets"]["current_price_local"],
        "current_price_usd": ETS_SYSTEMS["china_ets"]["current_price_usd"],
        "regulator": "Ministry of Ecology and Environment (MEE)",
        "mrvp_reference": "China ETS MRV Protocol 2021",
        "source": "MEE 2023 Annual Report on China Carbon Market",
    }
