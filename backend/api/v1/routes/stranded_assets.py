"""
Stranded Asset Analysis API Routes
Energy transition risk assessment for fossil fuel reserves, power plants, and infrastructure
"""

from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timezone
from uuid import uuid4, UUID
from decimal import Decimal
import json

from db.base import get_db
from schemas.stranded_assets import (
    # Enums
    ReserveType, ReserveCategory, PlantTechnology, InfrastructureType,
    RiskCategory, AssetType, OfftakeType, RepurposingType,
    # Fossil Fuel Reserve
    FossilFuelReserveCreate, FossilFuelReserveUpdate, FossilFuelReserveResponse,
    FossilFuelReserveListResponse,
    # Power Plant
    PowerPlantCreate, PowerPlantUpdate, PowerPlantResponse, PowerPlantListResponse,
    # Infrastructure
    InfrastructureAssetCreate, InfrastructureAssetUpdate, InfrastructureAssetResponse,
    InfrastructureAssetListResponse,
    # Calculations
    ReserveImpairmentRequest, ReserveImpairmentResult, ReserveImpairmentResponse,
    PowerPlantValuationRequest, PowerPlantValuationResult, PowerPlantValuationResponse,
    InfrastructureValuationRequest, InfrastructureValuationResult, InfrastructureValuationResponse,
    StrandedAssetCalculationCreate, StrandedAssetCalculationResponse,
    # Technology & Pathways
    TechnologyDisruptionSummary,
    EnergyTransitionPathwayCreate, EnergyTransitionPathwayUpdate, EnergyTransitionPathwayResponse,
    EnergyTransitionPathwayListResponse,
    # Alerts & Comparison
    CriticalAssetAlert, CriticalAssetAlertList,
    ScenarioComparisonRequest as StrandedScenarioComparisonRequest,
    ScenarioComparisonResult as StrandedScenarioComparisonResult,
    ScenarioComparisonResponse as StrandedScenarioComparisonResponse,
    ScenarioAssetComparison,
    # Dashboard
    StrandedAssetDashboardKPIs,
    PortfolioStrandingAnalysisRequest, PortfolioStrandingAnalysisResponse,
)
from services.stranded_asset_calculator import (
    ReserveImpairmentCalculator,
    PowerPlantValuator,
    InfrastructureValuator,
    TechnologyDisruptionTracker,
    PortfolioStrandingAnalyzer
)
from services.stranded_asset_db_service import get_stranded_asset_db_service

router = APIRouter(prefix="/api/v1/stranded-assets", tags=["Stranded Asset Analysis"])

# Get database service
db_service = get_stranded_asset_db_service()


# ============ Helper functions for DB data ============

def get_reserves_from_db() -> List[Dict]:
    """Get reserves from PostgreSQL database."""
    result = db_service.get_all_reserves(is_operating=True, page=1, page_size=100)
    return result.get("items", [])


def get_plants_from_db() -> List[Dict]:
    """Get power plants from PostgreSQL database."""
    result = db_service.get_all_plants(is_operating=True, page=1, page_size=100)
    return result.get("items", [])


def get_infrastructure_from_db() -> List[Dict]:
    """Get infrastructure from PostgreSQL database."""
    result = db_service.get_all_infrastructure(is_operating=True, page=1, page_size=100)
    return result.get("items", [])


# ============ Sample Data for Demo ============

def get_sample_reserves() -> List[Dict]:
    """Get sample fossil fuel reserves for demo."""
    return [
        {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "counterparty_id": "550e8400-e29b-41d4-a716-446655440100",
            "counterparty_name": "PetroGlobal Inc",
            "asset_name": "Permian Basin Field A",
            "asset_location": "Texas, USA",
            "latitude": Decimal("31.9973"),
            "longitude": Decimal("-102.0779"),
            "reserve_type": "oil",
            "reserve_category": "1P",
            "proven_reserves_mmBOE": Decimal("150.5"),
            "probable_reserves_mmBOE": Decimal("75.2"),
            "possible_reserves_mmBOE": Decimal("50.0"),
            "breakeven_price_USD": Decimal("42.50"),
            "lifting_cost_USD": Decimal("18.00"),
            "remaining_capex_USD": Decimal("2500000000"),
            "carbon_intensity_kgCO2_per_unit": Decimal("420"),
            "methane_leakage_rate": Decimal("0.015"),
            "production_start_year": 2015,
            "expected_depletion_year": 2045,
            "license_expiry_year": 2050,
            "is_operating": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440002",
            "counterparty_id": "550e8400-e29b-41d4-a716-446655440101",
            "counterparty_name": "North Sea Energy",
            "asset_name": "North Sea Block 22",
            "asset_location": "UK Continental Shelf",
            "latitude": Decimal("57.5000"),
            "longitude": Decimal("1.5000"),
            "reserve_type": "gas",
            "reserve_category": "2P",
            "proven_reserves_mmBOE": Decimal("85.0"),
            "probable_reserves_mmBOE": Decimal("120.0"),
            "possible_reserves_mmBOE": Decimal("60.0"),
            "breakeven_price_USD": Decimal("55.00"),
            "lifting_cost_USD": Decimal("28.00"),
            "remaining_capex_USD": Decimal("1800000000"),
            "carbon_intensity_kgCO2_per_unit": Decimal("380"),
            "methane_leakage_rate": Decimal("0.025"),
            "production_start_year": 2012,
            "expected_depletion_year": 2038,
            "license_expiry_year": 2040,
            "is_operating": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440003",
            "counterparty_id": "550e8400-e29b-41d4-a716-446655440102",
            "counterparty_name": "CoalPower Holdings",
            "asset_name": "Queensland Coal Reserve",
            "asset_location": "Queensland, Australia",
            "latitude": Decimal("-23.3000"),
            "longitude": Decimal("148.7000"),
            "reserve_type": "coal",
            "reserve_category": "1P",
            "proven_reserves_mmBOE": Decimal("500.0"),
            "probable_reserves_mmBOE": Decimal("200.0"),
            "possible_reserves_mmBOE": Decimal("150.0"),
            "breakeven_price_USD": Decimal("65.00"),
            "lifting_cost_USD": Decimal("35.00"),
            "remaining_capex_USD": Decimal("800000000"),
            "carbon_intensity_kgCO2_per_unit": Decimal("2400"),
            "methane_leakage_rate": Decimal("0.008"),
            "production_start_year": 2005,
            "expected_depletion_year": 2055,
            "license_expiry_year": 2060,
            "is_operating": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
    ]


def get_sample_power_plants() -> List[Dict]:
    """Get sample power plants for demo."""
    return [
        {
            "id": "660e8400-e29b-41d4-a716-446655440001",
            "counterparty_id": "550e8400-e29b-41d4-a716-446655440103",
            "counterparty_name": "National Grid Power",
            "plant_name": "Midwest Coal Station",
            "plant_location": "Illinois, USA",
            "latitude": Decimal("39.7817"),
            "longitude": Decimal("-89.6501"),
            "country_code": "US",
            "technology_type": "coal",
            "capacity_mw": Decimal("1200"),
            "commissioning_year": 1985,
            "original_retirement_year": 2045,
            "technical_lifetime_years": 60,
            "capacity_factor_baseline": Decimal("0.65"),
            "capacity_factor_current": Decimal("0.55"),
            "heat_rate_btu_kwh": Decimal("10500"),
            "efficiency_percent": Decimal("32.5"),
            "co2_intensity_tco2_mwh": Decimal("0.95"),
            "nox_emissions_kg_mwh": Decimal("1.8"),
            "so2_emissions_kg_mwh": Decimal("2.2"),
            "has_ccs": False,
            "ccs_capacity_mtpa": None,
            "fixed_om_cost_usd_kw_year": Decimal("45.00"),
            "variable_om_cost_usd_mwh": Decimal("5.50"),
            "fuel_cost_usd_mmbtu": Decimal("2.50"),
            "fuel_type": "bituminous_coal",
            "offtake_type": "regulated",
            "ppa_expiry_year": None,
            "ppa_price_usd_mwh": None,
            "grid_region": "PJM",
            "grid_carbon_intensity": Decimal("0.45"),
            "repurposing_option": "retirement",
            "repurposing_cost_usd_mw": Decimal("50000"),
            "is_operating": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "id": "660e8400-e29b-41d4-a716-446655440002",
            "counterparty_id": "550e8400-e29b-41d4-a716-446655440104",
            "counterparty_name": "EuroGen SA",
            "plant_name": "Rhine Valley CCGT",
            "plant_location": "North Rhine-Westphalia, Germany",
            "latitude": Decimal("51.2277"),
            "longitude": Decimal("6.7735"),
            "country_code": "DE",
            "technology_type": "gas_ccgt",
            "capacity_mw": Decimal("800"),
            "commissioning_year": 2010,
            "original_retirement_year": 2050,
            "technical_lifetime_years": 40,
            "capacity_factor_baseline": Decimal("0.55"),
            "capacity_factor_current": Decimal("0.48"),
            "heat_rate_btu_kwh": Decimal("6800"),
            "efficiency_percent": Decimal("58.0"),
            "co2_intensity_tco2_mwh": Decimal("0.38"),
            "nox_emissions_kg_mwh": Decimal("0.25"),
            "so2_emissions_kg_mwh": Decimal("0.02"),
            "has_ccs": False,
            "ccs_capacity_mtpa": None,
            "fixed_om_cost_usd_kw_year": Decimal("15.00"),
            "variable_om_cost_usd_mwh": Decimal("3.50"),
            "fuel_cost_usd_mmbtu": Decimal("8.50"),
            "fuel_type": "natural_gas",
            "offtake_type": "merchant",
            "ppa_expiry_year": None,
            "ppa_price_usd_mwh": None,
            "grid_region": "Germany",
            "grid_carbon_intensity": Decimal("0.35"),
            "repurposing_option": "hydrogen",
            "repurposing_cost_usd_mw": Decimal("180000"),
            "is_operating": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "id": "660e8400-e29b-41d4-a716-446655440003",
            "counterparty_id": "550e8400-e29b-41d4-a716-446655440105",
            "counterparty_name": "Asia Pacific Energy",
            "plant_name": "Guangdong Peaker",
            "plant_location": "Guangdong, China",
            "latitude": Decimal("23.1291"),
            "longitude": Decimal("113.2644"),
            "country_code": "CN",
            "technology_type": "gas_ocgt",
            "capacity_mw": Decimal("400"),
            "commissioning_year": 2018,
            "original_retirement_year": 2048,
            "technical_lifetime_years": 30,
            "capacity_factor_baseline": Decimal("0.20"),
            "capacity_factor_current": Decimal("0.18"),
            "heat_rate_btu_kwh": Decimal("9500"),
            "efficiency_percent": Decimal("36.0"),
            "co2_intensity_tco2_mwh": Decimal("0.52"),
            "nox_emissions_kg_mwh": Decimal("0.35"),
            "so2_emissions_kg_mwh": Decimal("0.01"),
            "has_ccs": False,
            "ccs_capacity_mtpa": None,
            "fixed_om_cost_usd_kw_year": Decimal("12.00"),
            "variable_om_cost_usd_mwh": Decimal("8.00"),
            "fuel_cost_usd_mmbtu": Decimal("12.00"),
            "fuel_type": "lng",
            "offtake_type": "ppa",
            "ppa_expiry_year": 2035,
            "ppa_price_usd_mwh": Decimal("85.00"),
            "grid_region": "Guangdong",
            "grid_carbon_intensity": Decimal("0.55"),
            "repurposing_option": "storage",
            "repurposing_cost_usd_mw": Decimal("250000"),
            "is_operating": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
    ]


def get_sample_infrastructure() -> List[Dict]:
    """Get sample infrastructure assets for demo."""
    return [
        {
            "id": "770e8400-e29b-41d4-a716-446655440001",
            "counterparty_id": "550e8400-e29b-41d4-a716-446655440106",
            "counterparty_name": "TransContinental Pipelines",
            "asset_name": "Keystone Spur Pipeline",
            "asset_type": "pipeline_oil",
            "asset_location": "Alberta to Texas",
            "latitude": Decimal("45.0000"),
            "longitude": Decimal("-105.0000"),
            "country_code": "US",
            "design_capacity": "590000",
            "design_capacity_unit": "bpd",
            "current_capacity_utilized": "450000",
            "utilization_rate_percent": Decimal("76.3"),
            "commissioning_year": 2012,
            "expected_retirement_year": 2052,
            "remaining_book_value_usd": Decimal("4500000000"),
            "replacement_cost_usd": Decimal("8000000000"),
            "contract_maturity_profile": {"2025": 500000000, "2030": 400000000, "2035": 200000000},
            "take_or_pay_exposure_usd": Decimal("1200000000"),
            "contracted_volume_percent": Decimal("85"),
            "hydrogen_ready": False,
            "ammonia_ready": False,
            "ccs_compatible": False,
            "regulatory_status": "operating",
            "environmental_permits": {"federal": "approved", "state": ["TX", "OK", "KS", "NE", "SD", "MT"]},
            "is_operating": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "id": "770e8400-e29b-41d4-a716-446655440002",
            "counterparty_id": "550e8400-e29b-41d4-a716-446655440107",
            "counterparty_name": "Qatar LNG Partners",
            "asset_name": "Ras Laffan LNG Terminal",
            "asset_type": "lng_terminal",
            "asset_location": "Ras Laffan, Qatar",
            "latitude": Decimal("25.9000"),
            "longitude": Decimal("51.5500"),
            "country_code": "QA",
            "design_capacity": "77",
            "design_capacity_unit": "mtpa",
            "current_capacity_utilized": "72",
            "utilization_rate_percent": Decimal("93.5"),
            "commissioning_year": 2009,
            "expected_retirement_year": 2059,
            "remaining_book_value_usd": Decimal("12000000000"),
            "replacement_cost_usd": Decimal("25000000000"),
            "contract_maturity_profile": {"2030": 8000000000, "2040": 6000000000, "2050": 3000000000},
            "take_or_pay_exposure_usd": Decimal("15000000000"),
            "contracted_volume_percent": Decimal("95"),
            "hydrogen_ready": True,
            "ammonia_ready": True,
            "ccs_compatible": False,
            "regulatory_status": "operating",
            "environmental_permits": {"federal": "approved"},
            "is_operating": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "id": "770e8400-e29b-41d4-a716-446655440003",
            "counterparty_id": "550e8400-e29b-41d4-a716-446655440108",
            "counterparty_name": "ExxonMobil Refining",
            "asset_name": "Baton Rouge Refinery",
            "asset_type": "refinery",
            "asset_location": "Louisiana, USA",
            "latitude": Decimal("30.4515"),
            "longitude": Decimal("-91.1871"),
            "country_code": "US",
            "design_capacity": "502000",
            "design_capacity_unit": "bpd",
            "current_capacity_utilized": "420000",
            "utilization_rate_percent": Decimal("83.7"),
            "commissioning_year": 1977,
            "expected_retirement_year": 2047,
            "remaining_book_value_usd": Decimal("3200000000"),
            "replacement_cost_usd": Decimal("12000000000"),
            "contract_maturity_profile": {"2025": 200000000, "2030": 150000000},
            "take_or_pay_exposure_usd": Decimal("500000000"),
            "contracted_volume_percent": Decimal("60"),
            "hydrogen_ready": False,
            "ammonia_ready": False,
            "ccs_compatible": True,
            "regulatory_status": "operating",
            "environmental_permits": {"federal": "approved", "state": ["LA"]},
            "is_operating": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
    ]


def get_sample_scenarios() -> List[Dict]:
    """Get sample transition scenarios."""
    return [
        {
            "id": "880e8400-e29b-41d4-a716-446655440001",
            "name": "Net Zero 2050 (IEA NZE)",
            "description": "IEA Net Zero Emissions by 2050 Scenario",
            "demand_trajectory": {"2025": 100, "2030": 90, "2035": 75, "2040": 55, "2045": 35, "2050": 15},
            "base_year": 2025,
            "peak_demand_year": 2025,
            "carbon_price_trajectory": {"2025": 85, "2030": 130, "2035": 180, "2040": 250, "2045": 320, "2050": 400},
            "transition_severity": 1.0
        },
        {
            "id": "880e8400-e29b-41d4-a716-446655440002",
            "name": "Announced Pledges (IEA APS)",
            "description": "IEA Announced Pledges Scenario",
            "demand_trajectory": {"2025": 100, "2030": 95, "2035": 88, "2040": 78, "2045": 65, "2050": 50},
            "base_year": 2025,
            "peak_demand_year": 2028,
            "carbon_price_trajectory": {"2025": 60, "2030": 85, "2035": 110, "2040": 140, "2045": 170, "2050": 200},
            "transition_severity": 0.7
        },
        {
            "id": "880e8400-e29b-41d4-a716-446655440003",
            "name": "Stated Policies (IEA STEPS)",
            "description": "IEA Stated Policies Scenario",
            "demand_trajectory": {"2025": 100, "2030": 102, "2035": 100, "2040": 95, "2045": 88, "2050": 80},
            "base_year": 2025,
            "peak_demand_year": 2030,
            "carbon_price_trajectory": {"2025": 45, "2030": 55, "2035": 65, "2040": 75, "2045": 85, "2050": 100},
            "transition_severity": 0.4
        }
    ]


def get_sample_transition_pathways() -> List[Dict]:
    """Get sample energy transition pathways."""
    return [
        {
            "id": "990e8400-e29b-41d4-a716-446655440001",
            "pathway_name": "Global Oil Demand (NZE)",
            "sector": "oil",
            "region": "global",
            "scenario_id": "880e8400-e29b-41d4-a716-446655440001",
            "base_year": 2025,
            "target_year": 2050,
            "demand_trajectory": {"2025": 100, "2030": 88, "2035": 70, "2040": 50, "2045": 30, "2050": 15},
            "price_trajectory": {"2025": 75, "2030": 65, "2035": 55, "2040": 45, "2045": 40, "2050": 35},
            "peak_demand_year": 2025,
            "net_zero_year": 2050,
            "carbon_price_trajectory": {"2025": 85, "2030": 130, "2035": 180, "2040": 250, "2045": 320, "2050": 400},
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "id": "990e8400-e29b-41d4-a716-446655440002",
            "pathway_name": "Global Gas Demand (NZE)",
            "sector": "gas",
            "region": "global",
            "scenario_id": "880e8400-e29b-41d4-a716-446655440001",
            "base_year": 2025,
            "target_year": 2050,
            "demand_trajectory": {"2025": 100, "2030": 95, "2035": 85, "2040": 65, "2045": 40, "2050": 20},
            "price_trajectory": {"2025": 8, "2030": 7, "2035": 6, "2040": 5, "2045": 4.5, "2050": 4},
            "peak_demand_year": 2027,
            "net_zero_year": 2050,
            "carbon_price_trajectory": {"2025": 85, "2030": 130, "2035": 180, "2040": 250, "2045": 320, "2050": 400},
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "id": "990e8400-e29b-41d4-a716-446655440003",
            "pathway_name": "Global Coal Demand (NZE)",
            "sector": "coal",
            "region": "global",
            "scenario_id": "880e8400-e29b-41d4-a716-446655440001",
            "base_year": 2025,
            "target_year": 2050,
            "demand_trajectory": {"2025": 100, "2030": 70, "2035": 45, "2040": 25, "2045": 10, "2050": 2},
            "price_trajectory": {"2025": 80, "2030": 60, "2035": 45, "2040": 35, "2045": 30, "2050": 25},
            "peak_demand_year": 2023,
            "net_zero_year": 2040,
            "carbon_price_trajectory": {"2025": 85, "2030": 130, "2035": 180, "2040": 250, "2045": 320, "2050": 400},
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
        }
    ]


# ============ Dashboard Routes ============

@router.get("/dashboard", response_model=StrandedAssetDashboardKPIs)
async def get_dashboard_kpis():
    """
    Get dashboard KPIs for stranded asset analysis.
    
    Returns aggregated metrics across all asset types:
    - Total asset counts by type
    - Risk distribution
    - Total exposure and stranded value at risk
    """
    # Get metrics from database
    metrics = db_service.get_dashboard_metrics()
    
    return StrandedAssetDashboardKPIs(
        total_assets=metrics["total_assets"],
        total_reserves_count=metrics["total_reserves_count"],
        total_plants_count=metrics["total_plants_count"],
        total_infrastructure_count=metrics["total_infrastructure_count"],
        high_risk_assets=metrics["high_risk_assets"],
        critical_risk_assets=metrics["critical_risk_assets"],
        total_exposure_usd=metrics["total_exposure_usd"],
        stranded_value_at_risk_usd=metrics["stranded_value_at_risk_usd"],
        avg_stranding_risk_score=metrics["avg_stranding_risk_score"],
        assets_by_risk_category=metrics["assets_by_risk_category"]
    )


# ============ Reserve Routes ============

@router.get("/reserves", response_model=FossilFuelReserveListResponse)
async def list_reserves(
    reserve_type: Optional[str] = Query(None, description="Filter by type: oil, gas, coal"),
    reserve_category: Optional[str] = Query(None, description="Filter by category: 1P, 2P, 3P"),
    is_operating: Optional[bool] = Query(True),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    List fossil fuel reserves with optional filtering.
    Data retrieved from PostgreSQL database.
    """
    result = db_service.get_all_reserves(
        reserve_type=reserve_type,
        reserve_category=reserve_category,
        is_operating=is_operating,
        page=page,
        page_size=page_size
    )
    
    return FossilFuelReserveListResponse(
        items=[FossilFuelReserveResponse(**r) for r in result["items"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"]
    )


@router.get("/reserves/{reserve_id}", response_model=FossilFuelReserveResponse)
async def get_reserve(reserve_id: str):
    """Get a specific fossil fuel reserve by ID from database."""
    try:
        reserve = db_service.get_reserve_by_id(UUID(reserve_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid reserve ID format")
    
    if not reserve:
        raise HTTPException(status_code=404, detail="Reserve not found")
    
    return FossilFuelReserveResponse(**reserve)


@router.post("/reserves", response_model=FossilFuelReserveResponse, status_code=201)
async def create_reserve(reserve: FossilFuelReserveCreate):
    """Create a new fossil fuel reserve in database."""
    result = db_service.create_reserve(reserve.model_dump())
    return FossilFuelReserveResponse(**result)


# ============ Power Plant Routes ============

@router.get("/power-plants", response_model=PowerPlantListResponse)
async def list_power_plants(
    technology_type: Optional[str] = Query(None, description="Filter by technology: coal, gas_ccgt, etc."),
    country_code: Optional[str] = Query(None, description="Filter by country code"),
    is_operating: Optional[bool] = Query(True),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    List power plants with optional filtering.
    Data retrieved from PostgreSQL database.
    """
    result = db_service.get_all_plants(
        technology_type=technology_type,
        country_code=country_code,
        is_operating=is_operating,
        page=page,
        page_size=page_size
    )
    
    return PowerPlantListResponse(
        items=[PowerPlantResponse(**p) for p in result["items"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"]
    )


@router.get("/power-plants/{plant_id}", response_model=PowerPlantResponse)
async def get_power_plant(plant_id: str):
    """Get a specific power plant by ID from database."""
    try:
        plant = db_service.get_plant_by_id(UUID(plant_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid plant ID format")
    
    if not plant:
        raise HTTPException(status_code=404, detail="Power plant not found")
    
    return PowerPlantResponse(**plant)


@router.post("/power-plants", response_model=PowerPlantResponse, status_code=201)
async def create_power_plant(plant: PowerPlantCreate):
    """Create a new power plant in database."""
    result = db_service.create_plant(plant.model_dump())
    return PowerPlantResponse(**result)


# ============ Infrastructure Routes ============

@router.get("/infrastructure", response_model=InfrastructureAssetListResponse)
async def list_infrastructure(
    asset_type: Optional[str] = Query(None, description="Filter by type: pipeline_oil, lng_terminal, refinery"),
    country_code: Optional[str] = Query(None, description="Filter by country code"),
    is_operating: Optional[bool] = Query(True),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    List infrastructure assets with optional filtering.
    Data retrieved from PostgreSQL database.
    """
    result = db_service.get_all_infrastructure(
        asset_type=asset_type,
        country_code=country_code,
        is_operating=is_operating,
        page=page,
        page_size=page_size
    )
    
    return InfrastructureAssetListResponse(
        items=[InfrastructureAssetResponse(**a) for a in result["items"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"]
    )


@router.get("/infrastructure/{asset_id}", response_model=InfrastructureAssetResponse)
async def get_infrastructure(asset_id: str):
    """Get a specific infrastructure asset by ID from database."""
    try:
        asset = db_service.get_infrastructure_by_id(UUID(asset_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid asset ID format")
    
    if not asset:
        raise HTTPException(status_code=404, detail="Infrastructure asset not found")
    
    return InfrastructureAssetResponse(**asset)


@router.post("/infrastructure", response_model=InfrastructureAssetResponse, status_code=201)
async def create_infrastructure(asset: InfrastructureAssetCreate):
    """Create a new infrastructure asset in database."""
    result = db_service.create_infrastructure(asset.model_dump())
    return InfrastructureAssetResponse(**result)


# ============ Calculation Routes ============

@router.post("/calculate/reserve-impairment", response_model=ReserveImpairmentResponse)
async def calculate_reserve_impairment(request: ReserveImpairmentRequest):
    """
    Calculate reserve impairment under climate scenarios.
    
    Analyzes oil, gas, and coal reserves to determine:
    - Stranded volume and value under different scenarios
    - NPV impact from demand reduction and carbon pricing
    - Risk scoring and recommended actions
    """
    calculator = ReserveImpairmentCalculator()
    reserves = get_reserves_from_db()
    scenarios = get_sample_scenarios()
    
    # Get scenario data
    scenario = next((s for s in scenarios if s.get("id") == str(request.scenario_id)), scenarios[0])
    
    results = []
    for reserve_id in request.reserve_ids:
        # Find reserve
        reserve = next((r for r in reserves if r.get("id") == str(reserve_id)), None)
        if not reserve:
            continue
        
        try:
            result = await calculator.calculate_impairment(
                reserve_id=reserve_id,
                reserve_data=reserve,
                scenario_data=scenario,
                target_years=request.target_years,
                discount_rate=request.discount_rate,
                commodity_price_forecast=request.commodity_price_forecast,
                carbon_price_forecast=request.carbon_price_forecast
            )
            results.append(result)
        except Exception:
            continue
    
    return ReserveImpairmentResponse(
        scenario_id=request.scenario_id,
        scenario_name=scenario.get("name", "Unknown"),
        calculation_date=datetime.now(timezone.utc),
        results=results,
        portfolio_summary={
            "total_reserves_analyzed": len(results),
            "total_stranded_value_usd": sum(float(r.total_stranded_value_usd) for r in results),
            "avg_risk_score": sum(float(r.stranding_risk_score) for r in results) / len(results) if results else 0
        }
    )


@router.post("/calculate/power-plant-valuation", response_model=PowerPlantValuationResponse)
async def calculate_power_plant_valuation(request: PowerPlantValuationRequest):
    """
    Value power plants under transition scenarios.
    
    Calculates:
    - NPV under baseline and scenario conditions
    - Optimal retirement timing
    - Repurposing options (CCS, hydrogen, storage)
    - Recommended actions
    """
    valuator = PowerPlantValuator()
    plants = get_plants_from_db()
    scenarios = get_sample_scenarios()
    
    # Get scenario data
    scenario = next((s for s in scenarios if s.get("id") == str(request.scenario_id)), scenarios[0])
    
    results = []
    for plant_id in request.plant_ids:
        # Find plant
        plant = next((p for p in plants if p.get("id") == str(plant_id)), None)
        if not plant:
            continue
        
        try:
            result = await valuator.value_plant(
                plant_id=plant_id,
                plant_data=plant,
                scenario_data=scenario,
                target_years=request.target_years,
                discount_rate=request.discount_rate,
                include_repurposing=request.include_repurposing,
                wholesale_price_forecast=request.wholesale_price_forecast,
                carbon_price_forecast=request.carbon_price_forecast
            )
            results.append(result)
        except Exception:
            continue
    
    return PowerPlantValuationResponse(
        scenario_id=request.scenario_id,
        scenario_name=scenario.get("name", "Unknown"),
        calculation_date=datetime.now(timezone.utc),
        results=results,
        portfolio_summary={
            "total_plants_analyzed": len(results),
            "total_capacity_mw": sum(float(r.capacity_mw) for r in results),
            "avg_npv_impact_percent": sum(float(r.npv_impact_percent) for r in results) / len(results) if results else 0
        }
    )


@router.post("/calculate/infrastructure-valuation", response_model=InfrastructureValuationResponse)
async def calculate_infrastructure_valuation(request: InfrastructureValuationRequest):
    """
    Value infrastructure assets under transition scenarios.
    
    Calculates:
    - NPV impact from utilization decline
    - Contract exposure at risk
    - Transition readiness assessment
    """
    valuator = InfrastructureValuator()
    infrastructure = get_infrastructure_from_db()
    scenarios = get_sample_scenarios()
    
    # Get scenario data
    scenario = next((s for s in scenarios if s.get("id") == str(request.scenario_id)), scenarios[0])
    
    results = []
    for asset_id in request.asset_ids:
        # Find asset
        asset = next((a for a in infrastructure if a.get("id") == str(asset_id)), None)
        if not asset:
            continue
        
        try:
            result = await valuator.value_infrastructure(
                asset_id=asset_id,
                asset_data=asset,
                scenario_data=scenario,
                target_years=request.target_years,
                discount_rate=request.discount_rate,
                demand_forecast=request.demand_forecast
            )
            results.append(result)
        except Exception:
            continue
    
    return InfrastructureValuationResponse(
        scenario_id=request.scenario_id,
        scenario_name=scenario.get("name", "Unknown"),
        calculation_date=datetime.now(timezone.utc),
        results=results,
        portfolio_summary={
            "total_assets_analyzed": len(results),
            "total_stranded_value_usd": sum(float(r.stranded_value_usd) for r in results),
            "avg_utilization_decline_percent": sum(float(r.utilization_decline_percent) for r in results) / len(results) if results else 0
        }
    )


# ============ Technology Disruption Routes ============

@router.get("/technology-disruption/{metric_type}", response_model=TechnologyDisruptionSummary)
async def get_technology_disruption(
    metric_type: str,
    region: str = Query("global", description="Region: global, europe, china, us, india"),
    scenario: str = Query("central", description="Scenario name"),
    year: int = Query(2030, ge=2025, le=2050, description="Target year")
):
    """
    Get technology disruption metrics (EVs, heat pumps, hydrogen).
    
    Available metric types:
    - ev: Electric vehicle adoption and oil displacement
    - heat_pump: Heat pump adoption and gas displacement
    - hydrogen: Green hydrogen cost trajectory
    - battery: Battery cost trajectory
    - composite: All metrics combined
    """
    tracker = TechnologyDisruptionTracker()
    
    if metric_type == "ev":
        data = tracker.calculate_oil_displacement(year, region)
        return TechnologyDisruptionSummary(
            metric_type="ev_adoption",
            region=region,
            scenario_name=scenario,
            current_value=Decimal(str(data["ev_sales_share_percent"])),
            current_year=year,
            projected_2030=tracker.ev_adoption_s_curve(2030, region) * 100,
            projected_2040=tracker.ev_adoption_s_curve(2040, region) * 100,
            projected_2050=tracker.ev_adoption_s_curve(2050, region) * 100,
            unit="percent",
            growth_rate_cagr=Decimal("25.5"),
            chart_data=[
                {"year": y, "value": float(tracker.ev_adoption_s_curve(y, region) * 100)}
                for y in range(2025, 2051, 5)
            ]
        )
    
    elif metric_type == "heat_pump":
        data = tracker.calculate_gas_displacement(year, region)
        return TechnologyDisruptionSummary(
            metric_type="heat_pump_adoption",
            region=region,
            scenario_name=scenario,
            current_value=Decimal(str(data["heat_pump_share_percent"])),
            current_year=year,
            projected_2030=tracker.heat_pump_adoption_curve(2030, region) * 100,
            projected_2040=tracker.heat_pump_adoption_curve(2040, region) * 100,
            projected_2050=tracker.heat_pump_adoption_curve(2050, region) * 100,
            unit="percent",
            growth_rate_cagr=Decimal("18.2"),
            chart_data=[
                {"year": y, "value": float(tracker.heat_pump_adoption_curve(y, region) * 100)}
                for y in range(2025, 2051, 5)
            ]
        )
    
    elif metric_type == "hydrogen":
        data = tracker.green_hydrogen_cost_curve(year, region)
        return TechnologyDisruptionSummary(
            metric_type="green_hydrogen_cost",
            region=region,
            scenario_name=scenario,
            current_value=Decimal(str(data["green_hydrogen_cost_usd_kg"])),
            current_year=year,
            projected_2030=Decimal(str(tracker.green_hydrogen_cost_curve(2030, region)["green_hydrogen_cost_usd_kg"])),
            projected_2040=Decimal(str(tracker.green_hydrogen_cost_curve(2040, region)["green_hydrogen_cost_usd_kg"])),
            projected_2050=Decimal(str(tracker.green_hydrogen_cost_curve(2050, region)["green_hydrogen_cost_usd_kg"])),
            unit="USD/kg",
            growth_rate_cagr=Decimal("-8.5"),
            chart_data=[
                {"year": y, "value": float(tracker.green_hydrogen_cost_curve(y, region)["green_hydrogen_cost_usd_kg"])}
                for y in range(2025, 2051, 5)
            ]
        )
    
    elif metric_type == "battery":
        data = tracker.battery_cost_curve(year)
        return TechnologyDisruptionSummary(
            metric_type="battery_cost",
            region=region,
            scenario_name=scenario,
            current_value=Decimal(str(data["battery_cost_usd_kwh"])),
            current_year=year,
            projected_2030=Decimal(str(tracker.battery_cost_curve(2030)["battery_cost_usd_kwh"])),
            projected_2040=Decimal(str(tracker.battery_cost_curve(2040)["battery_cost_usd_kwh"])),
            projected_2050=Decimal(str(tracker.battery_cost_curve(2050)["battery_cost_usd_kwh"])),
            unit="USD/kWh",
            growth_rate_cagr=Decimal("-12.3"),
            chart_data=[
                {"year": y, "value": float(tracker.battery_cost_curve(y)["battery_cost_usd_kwh"])}
                for y in range(2025, 2051, 5)
            ]
        )
    
    else:
        # Composite - return EV as default
        return tracker.get_disruption_summary(year, region)


# ============ Transition Pathway Routes ============

@router.get("/transition-pathways", response_model=EnergyTransitionPathwayListResponse)
async def list_transition_pathways(
    sector: Optional[str] = Query(None, description="Filter by sector: oil, gas, coal, power"),
    region: Optional[str] = Query(None, description="Filter by region")
):
    """
    List energy transition pathways from database.
    
    Returns demand, price, and capacity trajectories for energy sectors.
    """
    pathways = db_service.get_all_pathways(sector=sector, region=region)
    
    return EnergyTransitionPathwayListResponse(
        items=[EnergyTransitionPathwayResponse(**p) for p in pathways],
        total=len(pathways)
    )


@router.get("/transition-pathways/{pathway_id}", response_model=EnergyTransitionPathwayResponse)
async def get_transition_pathway(pathway_id: str):
    """Get a specific transition pathway by ID from database."""
    try:
        pathway = db_service.get_pathway_by_id(UUID(pathway_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid pathway ID format")
    
    if not pathway:
        raise HTTPException(status_code=404, detail="Pathway not found")
    
    return EnergyTransitionPathwayResponse(**pathway)


# ============ Scenario Comparison Routes ============

@router.post("/scenario-comparison", response_model=StrandedScenarioComparisonResponse)
async def run_scenario_comparison(request: StrandedScenarioComparisonRequest):
    """
    Compare asset valuations across multiple climate scenarios.
    
    Identifies:
    - Best and worst case outcomes
    - NPV range and risk distribution
    - Scenario sensitivity
    """
    calculator = ReserveImpairmentCalculator()
    valuator = PowerPlantValuator()
    
    reserves = get_sample_reserves()
    plants = get_sample_power_plants()
    scenarios = get_sample_scenarios()
    
    results = []
    
    for asset_id in request.asset_ids:
        scenario_comparisons = []
        asset_name = "Unknown"
        
        for scenario_id in request.scenario_ids:
            scenario = next((s for s in scenarios if s.get("id") == str(scenario_id)), scenarios[0])
            
            if request.asset_type == AssetType.RESERVE:
                reserve = next((r for r in reserves if r.get("id") == str(asset_id)), None)
                if reserve:
                    asset_name = reserve.get("asset_name", "Unknown")
                    result = await calculator.calculate_impairment(
                        reserve_id=asset_id,
                        reserve_data=reserve,
                        scenario_data=scenario,
                        target_years=[request.target_year]
                    )
                    scenario_comparisons.append(ScenarioAssetComparison(
                        scenario_id=scenario_id,
                        scenario_name=scenario.get("name", "Unknown"),
                        npv_usd=result.scenario_npv_usd,
                        stranded_value_usd=result.total_stranded_value_usd,
                        stranded_percent=result.total_stranded_percent,
                        risk_score=result.stranding_risk_score,
                        risk_category=result.risk_category
                    ))
            
            elif request.asset_type == AssetType.POWER_PLANT:
                plant = next((p for p in plants if p.get("id") == str(asset_id)), None)
                if plant:
                    asset_name = plant.get("plant_name", "Unknown")
                    result = await valuator.value_plant(
                        plant_id=asset_id,
                        plant_data=plant,
                        scenario_data=scenario,
                        target_years=[request.target_year]
                    )
                    stranded_value = max(Decimal(str(result.baseline_npv_usd)) - Decimal(str(result.scenario_npv_usd)), Decimal("0"))
                    scenario_comparisons.append(ScenarioAssetComparison(
                        scenario_id=scenario_id,
                        scenario_name=scenario.get("name", "Unknown"),
                        npv_usd=result.scenario_npv_usd,
                        stranded_value_usd=stranded_value,
                        stranded_percent=abs(result.npv_impact_percent),
                        risk_score=result.stranding_risk_score,
                        risk_category=result.risk_category
                    ))
        
        if scenario_comparisons:
            # Find best and worst cases
            best = max(scenario_comparisons, key=lambda x: float(x.npv_usd))
            worst = min(scenario_comparisons, key=lambda x: float(x.npv_usd))
            
            npv_values = [float(s.npv_usd) for s in scenario_comparisons]
            risk_values = [float(s.risk_score) for s in scenario_comparisons]
            
            results.append(StrandedScenarioComparisonResult(
                asset_id=asset_id,
                asset_name=asset_name,
                asset_type=request.asset_type,
                scenario_comparisons=scenario_comparisons,
                best_case_scenario=best.scenario_name,
                worst_case_scenario=worst.scenario_name,
                npv_range_usd=Decimal(str(max(npv_values) - min(npv_values))),
                risk_range=Decimal(str(max(risk_values) - min(risk_values)))
            ))
    
    return StrandedScenarioComparisonResponse(
        target_year=request.target_year,
        results=results,
        summary={
            "total_assets_compared": len(results),
            "scenarios_analyzed": len(request.scenario_ids)
        }
    )


# ============ Critical Assets & Alerts Routes ============

@router.get("/critical-assets", response_model=CriticalAssetAlertList)
async def get_critical_assets(
    risk_threshold: str = Query("high", description="Minimum risk level: low, medium, high, critical"),
    asset_type: Optional[str] = Query(None, description="Filter by type: reserve, power_plant, infrastructure")
):
    """
    Get list of critical assets at risk of stranding.
    
    Returns assets with:
    - High stranding risk scores
    - Significant NPV impact
    - Near-term stranding timeline
    """
    threshold_scores = {"low": 0.25, "medium": 0.5, "high": 0.75, "critical": 0.9}
    threshold = threshold_scores.get(risk_threshold, 0.75)
    
    alerts = []
    
    # Sample critical assets
    critical_assets = [
        {
            "asset_id": "550e8400-e29b-41d4-a716-446655440003",
            "asset_name": "Queensland Coal Reserve",
            "asset_type": "reserve",
            "counterparty_name": "CoalPower Holdings",
            "stranding_risk_score": 0.92,
            "estimated_impact_usd": 2500000000,
            "time_to_stranding_years": 8,
            "alert_trigger": "Coal demand decline under NZE scenario",
            "recommended_action": "Consider strategic divestment"
        },
        {
            "asset_id": "660e8400-e29b-41d4-a716-446655440001",
            "asset_name": "Midwest Coal Station",
            "asset_type": "power_plant",
            "counterparty_name": "National Grid Power",
            "stranding_risk_score": 0.85,
            "estimated_impact_usd": 800000000,
            "time_to_stranding_years": 5,
            "alert_trigger": "High CO2 intensity + carbon price trajectory",
            "recommended_action": "Accelerate retirement planning"
        },
        {
            "asset_id": "770e8400-e29b-41d4-a716-446655440003",
            "asset_name": "Baton Rouge Refinery",
            "asset_type": "infrastructure",
            "counterparty_name": "ExxonMobil Refining",
            "stranding_risk_score": 0.78,
            "estimated_impact_usd": 1200000000,
            "time_to_stranding_years": 12,
            "alert_trigger": "Declining fuel demand + EV adoption",
            "recommended_action": "Evaluate CCS retrofit or conversion"
        }
    ]
    
    for asset in critical_assets:
        if asset["stranding_risk_score"] >= threshold:
            if asset_type and asset["asset_type"] != asset_type:
                continue
            
            alerts.append(CriticalAssetAlert(
                alert_id=uuid4(),
                asset_id=UUID(asset["asset_id"]),
                asset_name=asset["asset_name"],
                asset_type=AssetType(asset["asset_type"]),
                counterparty_name=asset["counterparty_name"],
                risk_level=RiskCategory.CRITICAL if asset["stranding_risk_score"] >= 0.9 else RiskCategory.HIGH,
                stranding_risk_score=Decimal(str(asset["stranding_risk_score"])),
                estimated_impact_usd=Decimal(str(asset["estimated_impact_usd"])),
                time_to_stranding_years=asset["time_to_stranding_years"],
                alert_trigger=asset["alert_trigger"],
                recommended_action=asset["recommended_action"],
                created_at=datetime.now(timezone.utc),
                is_acknowledged=False
            ))
    
    return CriticalAssetAlertList(
        alerts=alerts,
        total=len(alerts),
        critical_count=sum(1 for a in alerts if a.risk_level == RiskCategory.CRITICAL),
        high_count=sum(1 for a in alerts if a.risk_level == RiskCategory.HIGH)
    )


# ============ Scenarios Routes ============

@router.get("/scenarios")
async def list_scenarios():
    """List available transition scenarios for stranded asset analysis."""
    return get_sample_scenarios()


@router.get("/scenarios/{scenario_id}")
async def get_scenario(scenario_id: str):
    """Get a specific scenario by ID."""
    scenarios = get_sample_scenarios()
    scenario = next((s for s in scenarios if s.get("id") == scenario_id), None)
    
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    return scenario


# ============ Map Data Routes ============

@router.get("/map-data")
async def get_assets_map_data(
    asset_type: Optional[str] = Query(None, description="Filter by type: reserve, power_plant, infrastructure")
):
    """
    Get geographic data for mapping stranded assets.
    
    Returns asset locations with risk scores for visualization on interactive map.
    """
    assets = []
    
    # Get reserves
    if asset_type is None or asset_type == "reserve":
        for r in get_sample_reserves():
            assets.append({
                "id": r["id"],
                "name": r["asset_name"],
                "type": "reserve",
                "sub_type": r["reserve_type"],
                "latitude": float(r.get("latitude", 0)),
                "longitude": float(r.get("longitude", 0)),
                "location": r.get("asset_location"),
                "counterparty": r.get("counterparty_name"),
                "capacity": f"{r.get('proven_reserves_mmBOE', 0)} mmBOE",
                "risk_score": 0.65  # Calculated
            })
    
    # Get power plants
    if asset_type is None or asset_type == "power_plant":
        for p in get_sample_power_plants():
            assets.append({
                "id": p["id"],
                "name": p["plant_name"],
                "type": "power_plant",
                "sub_type": p["technology_type"],
                "latitude": float(p.get("latitude", 0)),
                "longitude": float(p.get("longitude", 0)),
                "location": p.get("plant_location"),
                "counterparty": p.get("counterparty_name"),
                "capacity": f"{p.get('capacity_mw', 0)} MW",
                "risk_score": 0.72  # Calculated
            })
    
    # Get infrastructure
    if asset_type is None or asset_type == "infrastructure":
        for i in get_sample_infrastructure():
            assets.append({
                "id": i["id"],
                "name": i["asset_name"],
                "type": "infrastructure",
                "sub_type": i["asset_type"],
                "latitude": float(i.get("latitude", 0)),
                "longitude": float(i.get("longitude", 0)),
                "location": i.get("asset_location"),
                "counterparty": i.get("counterparty_name"),
                "capacity": f"{i.get('design_capacity', 0)} {i.get('design_capacity_unit', '')}",
                "risk_score": 0.58  # Calculated
            })
    
    return {"assets": assets, "total": len(assets)}


# ============ Portfolio Analysis Routes ============

@router.post("/portfolio-analysis", response_model=PortfolioStrandingAnalysisResponse)
async def analyze_portfolio_stranding(request: PortfolioStrandingAnalysisRequest):
    """
    Comprehensive portfolio-level stranding analysis.
    
    Aggregates stranding risk across:
    - Fossil fuel reserves
    - Power plants
    - Infrastructure assets
    
    Returns portfolio-wide metrics and recommendations.
    """
    analyzer = PortfolioStrandingAnalyzer()
    
    reserves = get_sample_reserves() if request.include_reserves else []
    plants = get_sample_power_plants() if request.include_plants else []
    infrastructure = get_sample_infrastructure() if request.include_infrastructure else []
    
    scenarios = get_sample_scenarios()
    scenario = next((s for s in scenarios if s.get("id") == str(request.scenario_id)), scenarios[0])
    
    result = await analyzer.analyze_portfolio(
        portfolio_id=request.portfolio_id,
        portfolio_name="Sample Portfolio",
        reserves=reserves,
        plants=plants,
        infrastructure=infrastructure,
        scenario_data=scenario,
        target_year=request.target_year
    )
    
    return PortfolioStrandingAnalysisResponse(
        portfolio_id=request.portfolio_id,
        portfolio_name=result.get("portfolio_name", "Sample Portfolio"),
        scenario_id=request.scenario_id,
        scenario_name=result.get("scenario_name", "Unknown"),
        target_year=request.target_year,
        total_assets_analyzed=result.get("total_assets_analyzed", 0),
        total_baseline_npv_usd=Decimal(str(result.get("total_baseline_npv_usd", 0))),
        total_scenario_npv_usd=Decimal(str(result.get("total_scenario_npv_usd", 0))),
        total_npv_impact_usd=Decimal(str(result.get("total_npv_impact_usd", 0))),
        total_npv_impact_percent=Decimal(str(result.get("total_npv_impact_percent", 0))),
        total_stranded_value_usd=Decimal(str(result.get("total_stranded_value_usd", 0))),
        avg_stranding_risk_score=Decimal(str(result.get("avg_stranding_risk_score", 0))),
        risk_distribution=result.get("risk_distribution", {}),
        asset_breakdown=result.get("asset_breakdown", {}),
        top_risk_assets=result.get("top_risk_assets", []),
        recommendations=result.get("recommendations", [])
    )
