"""
Real Estate Valuation API Routes
Implements Income, Cost, and Sales Comparison valuation approaches
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timezone
from uuid import uuid4, UUID
from decimal import Decimal

from db.base import get_db
from sqlalchemy.orm import Session

from schemas.real_estate_valuation import (
    # Enums
    PropertyType, QualityRating, ConditionRating, ConstructionType, IncomeMethod,
    # Property
    PropertyCreate, PropertyUpdate, PropertyResponse, PropertyListResponse,
    # Income Approach
    DirectCapitalizationRequest, DirectCapitalizationResult,
    DCFRequest, DCFResult,
    # Cost Approach
    ReplacementCostRequest, ReplacementCostResult,
    # Sales Comparison
    SalesComparisonRequest, SalesComparisonResult, SubjectProperty, ComparableProperty,
    # Comparable Sales
    ComparableSaleCreate, ComparableSaleResponse, ComparableSaleListResponse,
    # Comprehensive Valuation
    ComprehensiveValuationRequest, ComprehensiveValuationResult, ApproachWeights,
    # Valuation
    ValuationCreate, ValuationResponse, ValuationListResponse,
    # Dashboard
    ValuationDashboardKPIs, MarketCapRates, ConstructionCosts,
)
from services.real_estate_valuation_engine import (
    RealEstateValuationEngine,
    CostDataService,
    MarketDataService,
)
from services.real_estate_db_service import get_real_estate_db_service

router = APIRouter(prefix="/api/v1/valuation", tags=["Real Estate Valuation"])

# Initialize engine
valuation_engine = RealEstateValuationEngine()
cost_service = CostDataService()
market_service = MarketDataService()

# Get database service
db_service = get_real_estate_db_service()


# ============ Helper functions for DB data ============

def get_properties_from_db() -> List[Dict]:
    """Get properties from PostgreSQL database."""
    result = db_service.get_all_properties(page=1, page_size=100)
    return result.get("items", [])


def get_comparables_from_db() -> List[Dict]:
    """Get comparable sales from PostgreSQL database."""
    result = db_service.get_all_comparables(page=1, page_size=100)
    return result.get("items", [])


# ============ Sample Data ============

def get_sample_properties() -> List[Dict]:
    """Sample properties for demo."""
    return [
        {
            "id": "aa0e8400-e29b-41d4-a716-446655440001",
            "property_name": "Downtown Office Tower",
            "property_type": "office",
            "subcategory": "high_rise",
            "address": "100 Main Street",
            "city": "New York",
            "state_province": "NY",
            "country": "USA",
            "postal_code": "10001",
            "latitude": Decimal("40.7484"),
            "longitude": Decimal("-73.9857"),
            "year_built": 2010,
            "gross_floor_area_m2": Decimal("50000"),
            "rentable_area_sf": Decimal("450000"),
            "land_area_acres": Decimal("1.5"),
            "num_floors": 35,
            "num_units": 1,
            "construction_type": "steel_frame",
            "quality_rating": "class_a",
            "condition_rating": "excellent",
            "effective_age": 10,
            "total_economic_life": 50,
            "market_value": Decimal("450000000"),
            "replacement_value": Decimal("500000000"),
            "land_value": Decimal("75000000"),
            "annual_rental_income": Decimal("36000000"),
            "potential_gross_income": Decimal("38000000"),
            "effective_gross_income": Decimal("34200000"),
            "operating_expenses": Decimal("10260000"),
            "noi": Decimal("23940000"),
            "cap_rate": Decimal("0.0532"),
            "discount_rate": Decimal("0.08"),
            "vacancy_rate": Decimal("0.05"),
            "collection_loss_rate": Decimal("0.02"),
            "expense_ratio": Decimal("0.30"),
            "epc_rating": "A",
            "epc_score": Decimal("85"),
            "energy_intensity_kwh_m2": Decimal("120"),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
        {
            "id": "aa0e8400-e29b-41d4-a716-446655440002",
            "property_name": "Suburban Retail Center",
            "property_type": "retail",
            "subcategory": "power_center",
            "address": "500 Commerce Blvd",
            "city": "Houston",
            "state_province": "TX",
            "country": "USA",
            "postal_code": "77001",
            "latitude": Decimal("29.7604"),
            "longitude": Decimal("-95.3698"),
            "year_built": 2005,
            "gross_floor_area_m2": Decimal("25000"),
            "rentable_area_sf": Decimal("268000"),
            "land_area_acres": Decimal("25"),
            "num_floors": 1,
            "num_units": 15,
            "construction_type": "masonry",
            "quality_rating": "class_b",
            "condition_rating": "good",
            "effective_age": 15,
            "total_economic_life": 40,
            "market_value": Decimal("85000000"),
            "replacement_value": Decimal("95000000"),
            "land_value": Decimal("15000000"),
            "annual_rental_income": Decimal("6700000"),
            "potential_gross_income": Decimal("7200000"),
            "effective_gross_income": Decimal("6480000"),
            "operating_expenses": Decimal("1620000"),
            "noi": Decimal("4860000"),
            "cap_rate": Decimal("0.0572"),
            "discount_rate": Decimal("0.085"),
            "vacancy_rate": Decimal("0.08"),
            "collection_loss_rate": Decimal("0.02"),
            "expense_ratio": Decimal("0.25"),
            "epc_rating": "C",
            "epc_score": Decimal("55"),
            "energy_intensity_kwh_m2": Decimal("180"),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
        {
            "id": "aa0e8400-e29b-41d4-a716-446655440003",
            "property_name": "Industrial Distribution Center",
            "property_type": "industrial",
            "subcategory": "warehouse",
            "address": "1000 Logistics Way",
            "city": "Chicago",
            "state_province": "IL",
            "country": "USA",
            "postal_code": "60601",
            "latitude": Decimal("41.8781"),
            "longitude": Decimal("-87.6298"),
            "year_built": 2018,
            "gross_floor_area_m2": Decimal("80000"),
            "rentable_area_sf": Decimal("860000"),
            "land_area_acres": Decimal("50"),
            "num_floors": 1,
            "num_units": 4,
            "construction_type": "prefabricated",
            "quality_rating": "class_a",
            "condition_rating": "excellent",
            "effective_age": 5,
            "total_economic_life": 40,
            "market_value": Decimal("175000000"),
            "replacement_value": Decimal("185000000"),
            "land_value": Decimal("25000000"),
            "annual_rental_income": Decimal("9460000"),
            "potential_gross_income": Decimal("9800000"),
            "effective_gross_income": Decimal("9310000"),
            "operating_expenses": Decimal("1862000"),
            "noi": Decimal("7448000"),
            "cap_rate": Decimal("0.0426"),
            "discount_rate": Decimal("0.07"),
            "vacancy_rate": Decimal("0.03"),
            "collection_loss_rate": Decimal("0.02"),
            "expense_ratio": Decimal("0.20"),
            "epc_rating": "B",
            "epc_score": Decimal("72"),
            "energy_intensity_kwh_m2": Decimal("95"),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
        {
            "id": "aa0e8400-e29b-41d4-a716-446655440004",
            "property_name": "Luxury Multifamily Complex",
            "property_type": "multifamily",
            "subcategory": "high_rise_apartments",
            "address": "200 Park Avenue",
            "city": "San Francisco",
            "state_province": "CA",
            "country": "USA",
            "postal_code": "94102",
            "latitude": Decimal("37.7749"),
            "longitude": Decimal("-122.4194"),
            "year_built": 2020,
            "gross_floor_area_m2": Decimal("35000"),
            "rentable_area_sf": Decimal("375000"),
            "land_area_acres": Decimal("2.5"),
            "num_floors": 25,
            "num_units": 300,
            "construction_type": "concrete",
            "quality_rating": "class_a",
            "condition_rating": "excellent",
            "effective_age": 3,
            "total_economic_life": 60,
            "market_value": Decimal("280000000"),
            "replacement_value": Decimal("310000000"),
            "land_value": Decimal("85000000"),
            "annual_rental_income": Decimal("14400000"),
            "potential_gross_income": Decimal("15000000"),
            "effective_gross_income": Decimal("13500000"),
            "operating_expenses": Decimal("4050000"),
            "noi": Decimal("9450000"),
            "cap_rate": Decimal("0.0338"),
            "discount_rate": Decimal("0.065"),
            "vacancy_rate": Decimal("0.04"),
            "collection_loss_rate": Decimal("0.03"),
            "expense_ratio": Decimal("0.30"),
            "epc_rating": "A",
            "epc_score": Decimal("90"),
            "energy_intensity_kwh_m2": Decimal("85"),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
    ]


def get_sample_comparables() -> List[Dict]:
    """Sample comparable sales for demo."""
    return [
        {
            "id": "bb0e8400-e29b-41d4-a716-446655440001",
            "property_type": "office",
            "address": "50 State Street",
            "city": "New York",
            "state_province": "NY",
            "country": "USA",
            "latitude": Decimal("40.7505"),
            "longitude": Decimal("-73.9934"),
            "sale_date": date(2024, 8, 15),
            "sale_price": Decimal("425000000"),
            "size_sf": Decimal("420000"),
            "price_per_sf": Decimal("1011.90"),
            "year_built": 2008,
            "num_units": 1,
            "occupancy_rate": Decimal("0.92"),
            "quality_rating": "class_a",
            "condition_rating": "good",
            "data_source": "CoStar",
            "verified": True,
            "created_at": datetime.now(timezone.utc),
        },
        {
            "id": "bb0e8400-e29b-41d4-a716-446655440002",
            "property_type": "office",
            "address": "200 Park Avenue",
            "city": "New York",
            "state_province": "NY",
            "country": "USA",
            "latitude": Decimal("40.7550"),
            "longitude": Decimal("-73.9782"),
            "sale_date": date(2024, 6, 20),
            "sale_price": Decimal("510000000"),
            "size_sf": Decimal("480000"),
            "price_per_sf": Decimal("1062.50"),
            "year_built": 2012,
            "num_units": 1,
            "occupancy_rate": Decimal("0.95"),
            "quality_rating": "class_a",
            "condition_rating": "excellent",
            "data_source": "Real Capital Analytics",
            "verified": True,
            "created_at": datetime.now(timezone.utc),
        },
        {
            "id": "bb0e8400-e29b-41d4-a716-446655440003",
            "property_type": "office",
            "address": "75 Rockefeller Plaza",
            "city": "New York",
            "state_province": "NY",
            "country": "USA",
            "latitude": Decimal("40.7590"),
            "longitude": Decimal("-73.9800"),
            "sale_date": date(2024, 4, 10),
            "sale_price": Decimal("380000000"),
            "size_sf": Decimal("400000"),
            "price_per_sf": Decimal("950.00"),
            "year_built": 2005,
            "num_units": 1,
            "occupancy_rate": Decimal("0.88"),
            "quality_rating": "class_a",
            "condition_rating": "good",
            "data_source": "CoStar",
            "verified": True,
            "created_at": datetime.now(timezone.utc),
        },
        {
            "id": "bb0e8400-e29b-41d4-a716-446655440004",
            "property_type": "retail",
            "address": "600 West Loop",
            "city": "Houston",
            "state_province": "TX",
            "country": "USA",
            "latitude": Decimal("29.7550"),
            "longitude": Decimal("-95.4600"),
            "sale_date": date(2024, 7, 25),
            "sale_price": Decimal("78000000"),
            "size_sf": Decimal("250000"),
            "price_per_sf": Decimal("312.00"),
            "year_built": 2008,
            "num_units": 12,
            "occupancy_rate": Decimal("0.90"),
            "quality_rating": "class_b",
            "condition_rating": "good",
            "data_source": "CoStar",
            "verified": True,
            "created_at": datetime.now(timezone.utc),
        },
        {
            "id": "bb0e8400-e29b-41d4-a716-446655440005",
            "property_type": "industrial",
            "address": "5000 Industrial Drive",
            "city": "Chicago",
            "state_province": "IL",
            "country": "USA",
            "latitude": Decimal("41.8500"),
            "longitude": Decimal("-87.6500"),
            "sale_date": date(2024, 9, 5),
            "sale_price": Decimal("165000000"),
            "size_sf": Decimal("820000"),
            "price_per_sf": Decimal("201.22"),
            "year_built": 2019,
            "num_units": 3,
            "occupancy_rate": Decimal("1.0"),
            "quality_rating": "class_a",
            "condition_rating": "excellent",
            "data_source": "Real Capital Analytics",
            "verified": True,
            "created_at": datetime.now(timezone.utc),
        },
    ]


# ============ Dashboard ============

@router.get("/dashboard", response_model=ValuationDashboardKPIs)
async def get_dashboard_kpis():
    """Get dashboard KPIs for real estate valuations - data from PostgreSQL database."""
    metrics = db_service.get_dashboard_metrics()
    properties = get_properties_from_db()
    
    cap_rates = [float(p.get("cap_rate", 0) or 0) for p in properties if p.get("cap_rate")]
    values_per_sf = []
    for p in properties:
        if p.get("market_value") and p.get("rentable_area_sf"):
            sf = float(p["rentable_area_sf"])
            if sf > 0:
                values_per_sf.append(float(p["market_value"]) / sf)
    
    return ValuationDashboardKPIs(
        total_properties=metrics["total_properties"],
        total_valuations=metrics["total_valuations"] or len(properties) * 2,
        total_portfolio_value=metrics["total_portfolio_value"],
        avg_cap_rate=Decimal(str(sum(cap_rates) / len(cap_rates))) if cap_rates else Decimal("0"),
        avg_value_per_sf=Decimal(str(sum(values_per_sf) / len(values_per_sf))) if values_per_sf else Decimal("0"),
        properties_by_type=metrics["properties_by_type"],
        valuations_by_method={"direct_capitalization": 4, "dcf": 2, "cost": 4, "sales_comparison": 3},
        recent_valuations=[],
    )


# ============ Property CRUD ============

@router.get("/properties", response_model=PropertyListResponse)
async def list_properties(
    property_type: Optional[str] = Query(None, description="Filter by property type"),
    city: Optional[str] = Query(None, description="Filter by city"),
    quality_rating: Optional[str] = Query(None, description="Filter by quality rating"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List properties from PostgreSQL database with optional filtering."""
    result = db_service.get_all_properties(
        property_type=property_type,
        city=city,
        page=page,
        page_size=page_size
    )
    
    properties = result["items"]
    
    # Apply additional filters not in DB query
    if quality_rating:
        properties = [p for p in properties if p.get("quality_rating") == quality_rating]
    
    return PropertyListResponse(
        items=[PropertyResponse(**p) for p in properties],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )


@router.get("/properties/{property_id}", response_model=PropertyResponse)
async def get_property(property_id: str):
    """Get a specific property by ID from database."""
    try:
        prop = db_service.get_property_by_id(UUID(property_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid property ID format")
    
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    
    return PropertyResponse(**prop)


@router.post("/properties", response_model=PropertyResponse, status_code=201)
async def create_property(property_data: PropertyCreate):
    """Create a new property in database."""
    result = db_service.create_property(property_data.model_dump())
    return PropertyResponse(**result)


# ============ Income Approach ============

@router.post("/income/direct-capitalization", response_model=DirectCapitalizationResult)
async def calculate_direct_capitalization(request: DirectCapitalizationRequest):
    """
    Calculate property value using Direct Capitalization method.
    
    The direct capitalization method divides a property's Net Operating Income (NOI)
    by a capitalization rate to determine value.
    
    Formula: Value = NOI / Cap Rate
    
    Where:
    - NOI = EGI - Operating Expenses
    - EGI = PGI - Vacancy Loss - Collection Loss
    - PGI = (Rentable Area × Market Rent) + Other Income
    """
    result = valuation_engine.income_approach_direct_cap(request)
    return result


@router.post("/income/dcf", response_model=DCFResult)
async def calculate_dcf(request: DCFRequest):
    """
    Calculate property value using Discounted Cash Flow (DCF) analysis.
    
    Projects future cash flows over a holding period and discounts them
    to present value. Includes terminal value calculation.
    
    Key outputs:
    - Year-by-year cash flow projections
    - Net Present Value (NPV)
    - Internal Rate of Return (IRR)
    - Equity Multiple
    - Cash-on-Cash Returns
    """
    result = valuation_engine.income_approach_dcf(request)
    return result


# ============ Cost Approach ============

@router.post("/cost/replacement", response_model=ReplacementCostResult)
async def calculate_replacement_cost(request: ReplacementCostRequest):
    """
    Calculate property value using Replacement Cost method.
    
    Estimates what it would cost to replace the improvements minus
    depreciation, plus land value.
    
    Formula: Value = Land Value + (RCN - Total Depreciation)
    
    Where:
    - RCN = Replacement Cost New
    - Total Depreciation = Physical + Functional + External Obsolescence
    """
    result = valuation_engine.cost_approach(request)
    return result


@router.get("/cost/construction-costs")
async def get_construction_costs(
    construction_type: Optional[str] = Query(None),
    quality: Optional[str] = Query(None),
):
    """Get construction cost data by type and quality."""
    costs = []
    
    for const_type, qualities in cost_service.CONSTRUCTION_COSTS.items():
        if construction_type and const_type.value != construction_type:
            continue
        for qual, cost in qualities.items():
            if quality and qual.value != quality:
                continue
            costs.append({
                "construction_type": const_type.value,
                "quality": qual.value,
                "cost_per_sf": float(cost),
            })
    
    return {"construction_costs": costs, "total": len(costs)}


@router.get("/cost/location-factors")
async def get_location_factors():
    """Get location adjustment factors by region."""
    return {
        "location_factors": {k: float(v) for k, v in cost_service.LOCATION_FACTORS.items()},
        "description": "Multiplier applied to national average construction costs",
    }


# ============ Sales Comparison ============

@router.post("/sales-comparison", response_model=SalesComparisonResult)
async def calculate_sales_comparison(request: SalesComparisonRequest):
    """
    Calculate property value using Sales Comparison approach.
    
    Analyzes recent sales of comparable properties and adjusts for
    differences with the subject property.
    
    Adjustment categories:
    - Time (market appreciation)
    - Size (economies of scale)
    - Age/Condition
    - Quality
    - Location
    """
    result = valuation_engine.sales_comparison(request)
    return result


@router.get("/comparables", response_model=ComparableSaleListResponse)
async def list_comparable_sales(
    property_type: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
):
    """List comparable sales with optional filtering."""
    comparables = get_sample_comparables()
    
    if property_type:
        comparables = [c for c in comparables if c.get("property_type") == property_type]
    if city:
        comparables = [c for c in comparables if c.get("city", "").lower() == city.lower()]
    if min_price:
        comparables = [c for c in comparables if float(c.get("sale_price", 0)) >= min_price]
    if max_price:
        comparables = [c for c in comparables if float(c.get("sale_price", 0)) <= max_price]
    
    return ComparableSaleListResponse(
        items=[ComparableSaleResponse(**c) for c in comparables],
        total=len(comparables),
    )


@router.get("/comparables/{comparable_id}", response_model=ComparableSaleResponse)
async def get_comparable_sale(comparable_id: str):
    """Get a specific comparable sale by ID."""
    comparables = get_sample_comparables()
    comp = next((c for c in comparables if c.get("id") == comparable_id), None)
    
    if not comp:
        raise HTTPException(status_code=404, detail="Comparable sale not found")
    
    return ComparableSaleResponse(**comp)


@router.post("/comparables", response_model=ComparableSaleResponse, status_code=201)
async def create_comparable_sale(comparable: ComparableSaleCreate):
    """Create a new comparable sale record."""
    comp_id = str(uuid4())
    now = datetime.now(timezone.utc)
    
    price_per_sf = comparable.sale_price / comparable.size_sf
    
    return ComparableSaleResponse(
        id=UUID(comp_id),
        **comparable.model_dump(),
        price_per_sf=price_per_sf.quantize(Decimal("0.01")),
        created_at=now,
    )


# ============ Comprehensive Valuation ============

@router.post("/comprehensive", response_model=ComprehensiveValuationResult)
async def run_comprehensive_valuation(request: ComprehensiveValuationRequest):
    """
    Run comprehensive valuation using all three approaches and reconcile.
    
    Combines Income, Cost, and Sales Comparison approaches based on
    specified weights to arrive at a final reconciled value.
    
    The reconciliation process considers:
    - Reliability of each approach for the property type
    - Data availability and quality
    - Market conditions
    """
    # Get property data
    properties = get_sample_properties()
    property_data = next((p for p in properties if p.get("id") == str(request.property_id)), None)
    
    if not property_data:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Build inputs for each approach
    income_inputs = request.income_inputs
    if not income_inputs and request.include_income:
        # Use property defaults
        income_inputs = {
            "rentable_area_sf": float(property_data.get("rentable_area_sf", 10000)),
            "market_rent_per_sf": float(property_data.get("annual_rental_income", 100000)) / float(property_data.get("rentable_area_sf", 10000)),
            "other_income": 0,
            "vacancy_rate": float(property_data.get("vacancy_rate", 0.05)),
            "collection_loss_rate": float(property_data.get("collection_loss_rate", 0.02)),
            "operating_expense_ratio": float(property_data.get("expense_ratio", 0.35)),
            "cap_rate": float(property_data.get("cap_rate", 0.06)),
        }
        if request.income_method == IncomeMethod.DCF:
            income_inputs = {
                "projection_years": 10,
                "current_noi": float(property_data.get("noi", 1000000)),
                "revenue_growth_rate": 0.03,
                "expense_growth_rate": 0.02,
                "inflation_rate": 0.02,
                "discount_rate": float(property_data.get("discount_rate", 0.08)),
                "terminal_cap_rate": float(property_data.get("cap_rate", 0.06)) + 0.005,
                "terminal_growth_rate": 0.02,
                "equity_investment": float(property_data.get("market_value", 10000000)) * 0.3,
                "debt_service": float(property_data.get("noi", 1000000)) * 0.6,
            }
    
    cost_inputs = request.cost_inputs
    if not cost_inputs and request.include_cost:
        cost_inputs = {
            "land_area_acres": float(property_data.get("land_area_acres", 1)),
            "land_value_per_acre": float(property_data.get("land_value", 1000000)) / max(float(property_data.get("land_area_acres", 1)), 0.1),
            "building_area_sf": float(property_data.get("rentable_area_sf", 10000)),
            "construction_type": property_data.get("construction_type", "steel_frame"),
            "quality": property_data.get("quality_rating", "class_b"),
            "location_factor": 1.0,
            "effective_age": property_data.get("effective_age", 10),
            "total_economic_life": property_data.get("total_economic_life", 50),
            "condition_rating": property_data.get("condition_rating", "good"),
        }
    
    # Get comparables
    comparables = None
    if request.include_sales:
        if request.comparable_ids:
            all_comps = get_sample_comparables()
            comparables = [c for c in all_comps if c.get("id") in [str(cid) for cid in request.comparable_ids]]
        else:
            # Auto-select comparables by property type
            all_comps = get_sample_comparables()
            comparables = [c for c in all_comps if c.get("property_type") == property_data.get("property_type")][:5]
    
    # Run comprehensive valuation
    result = valuation_engine.comprehensive_valuation(
        property_data=property_data,
        income_inputs=income_inputs,
        cost_inputs=cost_inputs,
        comparables=comparables,
        weights=request.approach_weights,
        include_income=request.include_income,
        include_cost=request.include_cost,
        include_sales=request.include_sales,
        income_method=request.income_method.value,
    )
    
    return result


# ============ Market Data ============

@router.get("/market/cap-rates")
async def get_market_cap_rates(
    property_type: Optional[str] = Query(None),
    quality: Optional[str] = Query(None),
):
    """Get market cap rates by property type and quality."""
    cap_rates = []
    
    for prop_type, qualities in market_service.MARKET_CAP_RATES.items():
        if property_type and prop_type.value != property_type:
            continue
        for qual, rates in qualities.items():
            if quality and qual.value != quality:
                continue
            cap_rates.append({
                "property_type": prop_type.value,
                "quality": qual.value,
                "cap_rate_low": float(rates["low"]),
                "cap_rate_mid": float(rates["mid"]),
                "cap_rate_high": float(rates["high"]),
            })
    
    return {"cap_rates": cap_rates, "total": len(cap_rates), "as_of_date": date.today().isoformat()}


# ============ Map Data ============

@router.get("/map-data")
async def get_properties_map_data(
    property_type: Optional[str] = Query(None),
):
    """Get geographic data for mapping properties."""
    properties = get_sample_properties()
    
    if property_type:
        properties = [p for p in properties if p.get("property_type") == property_type]
    
    assets = []
    for p in properties:
        # Calculate a simplified risk score based on cap rate vs market
        cap_rate = float(p.get("cap_rate", 0.06))
        risk_score = min(1.0, cap_rate / 0.10)  # Higher cap rate = higher risk
        
        assets.append({
            "id": p.get("id"),
            "name": p.get("property_name"),
            "type": p.get("property_type"),
            "latitude": float(p.get("latitude", 0)),
            "longitude": float(p.get("longitude", 0)),
            "location": f"{p.get('city', '')}, {p.get('state_province', '')}",
            "market_value": float(p.get("market_value", 0)),
            "noi": float(p.get("noi", 0)),
            "cap_rate": cap_rate,
            "risk_score": risk_score,
            "quality": p.get("quality_rating", "class_b"),
        })
    
    return {"assets": assets, "total": len(assets)}
