"""
Sustainability Frameworks Integration API Routes
Analyzes value impact of green building certifications: GRESB, LEED, BREEAM, etc.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timezone
from uuid import uuid4, UUID
from decimal import Decimal

from schemas.sustainability import (
    # Enums
    CertificationType, LEEDLevel, BREEAMLevel, GRESBRating,
    PropertySector, Region,
    # Certification
    CertificationCreate, CertificationResponse, CertificationListResponse,
    # GRESB
    GRESBAssessmentRequest, GRESBAssessmentResult, GRESBComponentScore,
    # LEED
    LEEDAssessmentRequest, LEEDAssessmentResult, LEEDCategoryScore,
    # BREEAM
    BREEAMAssessmentRequest, BREEAMAssessmentResult, BREEAMCategoryScore, BREEAMWeights,
    # Value Impact
    CertificationValueImpactRequest, CertificationValueImpactResult,
    # Portfolio
    PortfolioSustainabilityRequest, PortfolioSustainabilityResult,
    # Dashboard
    SustainabilityDashboardKPIs,
    # Benchmark
    CertificationBenchmarkData, BenchmarkListResponse,
    # Comparison
    CertificationComparisonRequest, CertificationComparisonResult,
)
from services.sustainability_calculator import SustainabilityEngine

router = APIRouter(prefix="/api/v1/sustainability", tags=["Sustainability Frameworks"])

# Initialize engine
sustainability_engine = SustainabilityEngine()


# ============ Sample Data ============

def get_sample_certifications() -> List[Dict]:
    """Sample certified properties for demo."""
    return [
        {
            "id": "cc0e8400-e29b-41d4-a716-446655440001",
            "certification_type": "leed",
            "property_id": "aa0e8400-e29b-41d4-a716-446655440001",
            "property_name": "Downtown Office Tower",
            "property_sector": "office",
            "region": "north_america",
            "certification_level": "gold",
            "score": Decimal("68"),
            "certification_date": date(2023, 6, 15),
            "expiration_date": date(2028, 6, 15),
            "version": "v4.1",
            "gross_floor_area_m2": Decimal("50000"),
            "year_built": 2010,
            "current_value": Decimal("450000000"),
            "noi": Decimal("23940000"),
            "value_premium_percent": Decimal("15.3"),
            "rent_premium_percent": Decimal("9.0"),
            "estimated_value_impact": Decimal("68850000"),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
        {
            "id": "cc0e8400-e29b-41d4-a716-446655440002",
            "certification_type": "breeam",
            "property_id": "aa0e8400-e29b-41d4-a716-446655440002",
            "property_name": "Suburban Retail Center",
            "property_sector": "retail",
            "region": "europe",
            "certification_level": "very_good",
            "score": Decimal("58"),
            "certification_date": date(2022, 3, 20),
            "expiration_date": date(2027, 3, 20),
            "version": "2018",
            "gross_floor_area_m2": Decimal("25000"),
            "year_built": 2005,
            "current_value": Decimal("85000000"),
            "noi": Decimal("4860000"),
            "value_premium_percent": Decimal("11.5"),
            "rent_premium_percent": Decimal("7.0"),
            "estimated_value_impact": Decimal("9775000"),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
        {
            "id": "cc0e8400-e29b-41d4-a716-446655440003",
            "certification_type": "energy_star",
            "property_id": "aa0e8400-e29b-41d4-a716-446655440003",
            "property_name": "Industrial Distribution Center",
            "property_sector": "industrial",
            "region": "north_america",
            "certification_level": "certified",
            "score": Decimal("82"),
            "certification_date": date(2024, 1, 10),
            "expiration_date": date(2025, 1, 10),
            "version": "2024",
            "gross_floor_area_m2": Decimal("80000"),
            "year_built": 2018,
            "current_value": Decimal("175000000"),
            "noi": Decimal("7448000"),
            "value_premium_percent": Decimal("6.0"),
            "rent_premium_percent": Decimal("3.5"),
            "estimated_value_impact": Decimal("10500000"),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
        {
            "id": "cc0e8400-e29b-41d4-a716-446655440004",
            "certification_type": "gresb",
            "property_id": None,
            "property_name": "Core Real Estate Fund I",
            "property_sector": "mixed_use",
            "region": "north_america",
            "certification_level": "4_star",
            "score": Decimal("76"),
            "certification_date": date(2024, 9, 1),
            "expiration_date": date(2025, 9, 1),
            "version": "2024",
            "gross_floor_area_m2": Decimal("500000"),
            "year_built": None,
            "current_value": Decimal("2500000000"),
            "noi": Decimal("125000000"),
            "value_premium_percent": Decimal("9.4"),
            "rent_premium_percent": Decimal("5.5"),
            "estimated_value_impact": Decimal("235000000"),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
        {
            "id": "cc0e8400-e29b-41d4-a716-446655440005",
            "certification_type": "leed",
            "property_id": "aa0e8400-e29b-41d4-a716-446655440004",
            "property_name": "Luxury Multifamily Complex",
            "property_sector": "multifamily",
            "region": "north_america",
            "certification_level": "platinum",
            "score": Decimal("85"),
            "certification_date": date(2021, 11, 5),
            "expiration_date": date(2026, 11, 5),
            "version": "v4",
            "gross_floor_area_m2": Decimal("35000"),
            "year_built": 2020,
            "current_value": Decimal("280000000"),
            "noi": Decimal("9450000"),
            "value_premium_percent": Decimal("22.9"),
            "rent_premium_percent": Decimal("13.5"),
            "estimated_value_impact": Decimal("64120000"),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
    ]


def get_benchmark_data() -> List[Dict]:
    """Sample benchmark data from research."""
    return [
        {
            "certification_type": "leed",
            "property_sector": "office",
            "region": "north_america",
            "avg_rent_premium_percent": Decimal("8.5"),
            "rent_premium_range_low": Decimal("4.0"),
            "rent_premium_range_high": Decimal("15.0"),
            "avg_value_premium_percent": Decimal("14.5"),
            "value_premium_range_low": Decimal("7.0"),
            "value_premium_range_high": Decimal("25.0"),
            "avg_cap_rate_compression_bps": Decimal("35"),
            "avg_operating_cost_savings_percent": Decimal("10"),
            "avg_occupancy_premium_pct": Decimal("3.5"),
            "data_source": "Eichholtz, Kok, Quigley (2010, 2013)",
            "last_updated": date(2024, 1, 15),
            "sample_size": 2500,
        },
        {
            "certification_type": "breeam",
            "property_sector": "office",
            "region": "europe",
            "avg_rent_premium_percent": Decimal("9.0"),
            "rent_premium_range_low": Decimal("5.0"),
            "rent_premium_range_high": Decimal("16.0"),
            "avg_value_premium_percent": Decimal("15.5"),
            "value_premium_range_low": Decimal("8.0"),
            "value_premium_range_high": Decimal("26.0"),
            "avg_cap_rate_compression_bps": Decimal("40"),
            "avg_operating_cost_savings_percent": Decimal("9"),
            "avg_occupancy_premium_pct": Decimal("4.0"),
            "data_source": "Fuerst & McAllister (2011), RICS (2013)",
            "last_updated": date(2024, 2, 20),
            "sample_size": 1800,
        },
        {
            "certification_type": "energy_star",
            "property_sector": "office",
            "region": "north_america",
            "avg_rent_premium_percent": Decimal("5.5"),
            "rent_premium_range_low": Decimal("3.0"),
            "rent_premium_range_high": Decimal("8.0"),
            "avg_value_premium_percent": Decimal("9.5"),
            "value_premium_range_low": Decimal("5.0"),
            "value_premium_range_high": Decimal("14.0"),
            "avg_cap_rate_compression_bps": Decimal("20"),
            "avg_operating_cost_savings_percent": Decimal("12"),
            "avg_occupancy_premium_pct": Decimal("2.0"),
            "data_source": "EPA Energy Star Portfolio Manager Data",
            "last_updated": date(2024, 3, 1),
            "sample_size": 35000,
        },
        {
            "certification_type": "gresb",
            "property_sector": "mixed_use",
            "region": "north_america",
            "avg_rent_premium_percent": Decimal("5.5"),
            "rent_premium_range_low": Decimal("2.0"),
            "rent_premium_range_high": Decimal("10.0"),
            "avg_value_premium_percent": Decimal("9.0"),
            "value_premium_range_low": Decimal("4.0"),
            "value_premium_range_high": Decimal("18.0"),
            "avg_cap_rate_compression_bps": Decimal("30"),
            "avg_operating_cost_savings_percent": Decimal("7"),
            "avg_occupancy_premium_pct": Decimal("2.5"),
            "data_source": "GRESB Foundation Research (2023)",
            "last_updated": date(2024, 6, 1),
            "sample_size": 1500,
        },
    ]


# ============ Dashboard ============

@router.get("/dashboard", response_model=SustainabilityDashboardKPIs)
async def get_dashboard_kpis():
    """Get dashboard KPIs for sustainability certifications."""
    certifications = get_sample_certifications()
    
    # By type
    by_type = {}
    by_level = {}
    for cert in certifications:
        ct = cert.get("certification_type", "unknown")
        by_type[ct] = by_type.get(ct, 0) + 1
        
        level = cert.get("certification_level", "unknown")
        by_level[level] = by_level.get(level, 0) + 1
    
    # Calculate totals
    total_certified_value = sum(float(c.get("current_value", 0) or 0) for c in certifications)
    total_value_premium = sum(float(c.get("estimated_value_impact", 0) or 0) for c in certifications)
    
    # GRESB scores
    gresb_scores = [float(c.get("score", 0)) for c in certifications if c.get("certification_type") == "gresb"]
    avg_gresb = Decimal(str(sum(gresb_scores) / len(gresb_scores))) if gresb_scores else None
    
    # LEED points
    leed_scores = [int(c.get("score", 0)) for c in certifications if c.get("certification_type") == "leed"]
    avg_leed = int(sum(leed_scores) / len(leed_scores)) if leed_scores else None
    
    # BREEAM scores
    breeam_scores = [float(c.get("score", 0)) for c in certifications if c.get("certification_type") == "breeam"]
    avg_breeam = Decimal(str(sum(breeam_scores) / len(breeam_scores))) if breeam_scores else None
    
    return SustainabilityDashboardKPIs(
        total_certified_properties=len(certifications),
        total_uncertified_properties=2,  # Sample uncertified
        certification_coverage_percent=Decimal("71.4"),  # 5 of 7
        by_certification_type=by_type,
        by_level=by_level,
        total_certified_value=Decimal(str(total_certified_value)),
        avg_value_premium_captured=Decimal(str(
            (total_value_premium / total_certified_value * 100) if total_certified_value > 0 else 0
        )).quantize(Decimal("0.1")),
        potential_value_uplift=Decimal("15500000"),  # Estimated for uncertified
        avg_gresb_score=avg_gresb.quantize(Decimal("0.1")) if avg_gresb else None,
        avg_leed_points=avg_leed,
        avg_breeam_score=avg_breeam.quantize(Decimal("0.1")) if avg_breeam else None,
        certifications_this_year=2,
        certifications_expiring_soon=1,
    )


# ============ Certifications CRUD ============

@router.get("/certifications", response_model=CertificationListResponse)
async def list_certifications(
    certification_type: Optional[str] = Query(None, description="Filter by certification type"),
    property_sector: Optional[str] = Query(None, description="Filter by property sector"),
    region: Optional[str] = Query(None, description="Filter by region"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List certifications with optional filtering."""
    certifications = get_sample_certifications()
    
    if certification_type:
        certifications = [c for c in certifications if c.get("certification_type") == certification_type]
    if property_sector:
        certifications = [c for c in certifications if c.get("property_sector") == property_sector]
    if region:
        certifications = [c for c in certifications if c.get("region") == region]
    
    total = len(certifications)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = certifications[start:end]
    
    return CertificationListResponse(
        items=[CertificationResponse(**c) for c in paginated],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/certifications/{certification_id}", response_model=CertificationResponse)
async def get_certification(certification_id: str):
    """Get a specific certification by ID."""
    certifications = get_sample_certifications()
    cert = next((c for c in certifications if c.get("id") == certification_id), None)
    
    if not cert:
        raise HTTPException(status_code=404, detail="Certification not found")
    
    return CertificationResponse(**cert)


@router.post("/certifications", response_model=CertificationResponse, status_code=201)
async def create_certification(certification_data: CertificationCreate):
    """Create a new certification record."""
    cert_id = str(uuid4())
    now = datetime.now(timezone.utc)
    
    return CertificationResponse(
        id=UUID(cert_id),
        **certification_data.model_dump(),
        created_at=now,
        updated_at=now,
    )


# ============ GRESB Assessment ============

@router.post("/gresb/assess", response_model=GRESBAssessmentResult)
async def calculate_gresb_assessment(request: GRESBAssessmentRequest):
    """
    Calculate GRESB assessment score and value impact.
    
    GRESB (Global Real Estate Sustainability Benchmark) evaluates ESG performance
    of real estate portfolios and assets through:
    - Management Score (leadership, policies, reporting)
    - Performance Score (implementation, measurement)
    
    Returns star rating (1-5 stars) and estimated value impact.
    """
    result = sustainability_engine.calculate_gresb(request)
    return result


@router.get("/gresb/benchmarks")
async def get_gresb_benchmarks(
    region: Optional[str] = Query(None, description="Filter by region"),
):
    """Get GRESB benchmark data by region."""
    from services.sustainability_calculator import GRESB_BENCHMARKS
    
    benchmarks = []
    for reg, data in GRESB_BENCHMARKS.items():
        if region and reg.value != region:
            continue
        benchmarks.append({
            "region": reg.value,
            **{k: float(v) if isinstance(v, Decimal) else v for k, v in data.items()},
        })
    
    return {"benchmarks": benchmarks, "total": len(benchmarks), "year": 2024}


# ============ LEED Assessment ============

@router.post("/leed/assess", response_model=LEEDAssessmentResult)
async def calculate_leed_assessment(request: LEEDAssessmentRequest):
    """
    Calculate LEED certification assessment.
    
    LEED (Leadership in Energy and Environmental Design) is the most widely used
    green building rating system. Evaluates:
    - Location & Transportation
    - Sustainable Sites
    - Water Efficiency
    - Energy & Atmosphere
    - Materials & Resources
    - Indoor Environmental Quality
    - Innovation & Regional Priority
    
    Certification levels: Certified (40-49), Silver (50-59), Gold (60-79), Platinum (80+)
    """
    result = sustainability_engine.calculate_leed(request)
    return result


@router.get("/leed/thresholds")
async def get_leed_thresholds():
    """Get LEED certification level thresholds."""
    return {
        "levels": {
            "certified": {"min_points": 40, "max_points": 49},
            "silver": {"min_points": 50, "max_points": 59},
            "gold": {"min_points": 60, "max_points": 79},
            "platinum": {"min_points": 80, "max_points": 110},
        },
        "max_points": 110,
        "categories": {
            "integrative_process": 1,
            "location_transportation": 16,
            "sustainable_sites": 10,
            "water_efficiency": 11,
            "energy_atmosphere": 33,
            "materials_resources": 13,
            "indoor_environmental_quality": 16,
            "innovation": 6,
            "regional_priority": 4,
        },
    }


# ============ BREEAM Assessment ============

@router.post("/breeam/assess", response_model=BREEAMAssessmentResult)
async def calculate_breeam_assessment(request: BREEAMAssessmentRequest):
    """
    Calculate BREEAM certification assessment.
    
    BREEAM (Building Research Establishment Environmental Assessment Method)
    is the world's leading sustainability assessment method for buildings.
    
    Categories: Management, Health & Wellbeing, Energy, Transport, Water,
    Materials, Waste, Land Use & Ecology, Pollution, Innovation
    
    Ratings: Pass (30%), Good (45%), Very Good (55%), Excellent (70%), Outstanding (85%)
    """
    result = sustainability_engine.calculate_breeam(request)
    return result


@router.get("/breeam/weights")
async def get_breeam_weights():
    """Get BREEAM category weightings."""
    return {
        "scheme": "new_construction",
        "weights": {
            "management": 0.12,
            "health_wellbeing": 0.15,
            "energy": 0.19,
            "transport": 0.08,
            "water": 0.06,
            "materials": 0.125,
            "waste": 0.075,
            "land_use_ecology": 0.10,
            "pollution": 0.10,
            "innovation": 0.10,
        },
        "rating_thresholds": {
            "pass": 30,
            "good": 45,
            "very_good": 55,
            "excellent": 70,
            "outstanding": 85,
        },
    }


# ============ Value Impact Analysis ============

@router.post("/value-impact", response_model=CertificationValueImpactResult)
async def calculate_value_impact(request: CertificationValueImpactRequest):
    """
    Calculate the value impact of a certification on a property.
    
    Based on academic research and industry studies, estimates:
    - Rent premium (higher rents for certified buildings)
    - Value premium (higher sale prices/valuations)
    - Cap rate compression
    - Operating cost savings
    
    Sources include Eichholtz et al. (2010, 2013), Fuerst & McAllister (2011),
    and industry reports from JLL, CBRE, RICS.
    """
    result = sustainability_engine.calculate_value_impact(request)
    return result


@router.get("/benchmarks", response_model=BenchmarkListResponse)
async def list_benchmarks(
    certification_type: Optional[str] = Query(None),
    property_sector: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
):
    """List benchmark data from research studies."""
    benchmarks = get_benchmark_data()
    
    if certification_type:
        benchmarks = [b for b in benchmarks if b.get("certification_type") == certification_type]
    if property_sector:
        benchmarks = [b for b in benchmarks if b.get("property_sector") == property_sector]
    if region:
        benchmarks = [b for b in benchmarks if b.get("region") == region]
    
    return BenchmarkListResponse(
        items=[CertificationBenchmarkData(**b) for b in benchmarks],
        total=len(benchmarks),
    )


# ============ Portfolio Analysis ============

@router.post("/portfolio/analyze", response_model=PortfolioSustainabilityResult)
async def analyze_portfolio_sustainability(request: PortfolioSustainabilityRequest):
    """
    Analyze portfolio-level sustainability metrics.
    
    Evaluates:
    - Certification coverage (% of AUM certified)
    - Distribution by certification type
    - Aggregate value premiums captured
    - Potential uplift from uncertified assets
    - Portfolio sustainability score and rating
    """
    result = sustainability_engine.analyze_portfolio(request)
    return result


# ============ Certification Comparison Tool ============

@router.post("/compare", response_model=CertificationComparisonResult)
async def compare_certifications(request: CertificationComparisonRequest):
    """
    Compare different certification options for a property.
    
    Helps decide which certification to pursue based on:
    - Expected rent/value premiums
    - Certification costs
    - Time to certify
    - ROI estimate
    - Difficulty level
    """
    comparisons = []
    
    # Comparison data (simplified mock)
    cert_data = {
        CertificationType.LEED: {
            "typical_cost_range": "$25,000 - $100,000",
            "time_months": 8,
            "difficulty": "medium",
            "avg_rent_premium": 8.5,
            "avg_value_premium": 14.5,
            "recognition": "Global, strong in Americas",
        },
        CertificationType.BREEAM: {
            "typical_cost_range": "£20,000 - £80,000",
            "time_months": 6,
            "difficulty": "medium",
            "avg_rent_premium": 9.0,
            "avg_value_premium": 15.5,
            "recognition": "Global, strong in Europe",
        },
        CertificationType.ENERGY_STAR: {
            "typical_cost_range": "$5,000 - $15,000",
            "time_months": 3,
            "difficulty": "low",
            "avg_rent_premium": 5.5,
            "avg_value_premium": 9.5,
            "recognition": "US market",
        },
        CertificationType.WELL: {
            "typical_cost_range": "$30,000 - $120,000",
            "time_months": 10,
            "difficulty": "high",
            "avg_rent_premium": 7.5,
            "avg_value_premium": 12.5,
            "recognition": "Growing, health-focused",
        },
        CertificationType.GRESB: {
            "typical_cost_range": "$15,000 - $50,000 (annual)",
            "time_months": 4,
            "difficulty": "medium",
            "avg_rent_premium": 5.5,
            "avg_value_premium": 9.0,
            "recognition": "Investor-focused, portfolio-level",
        },
    }
    
    for cert_type in request.certifications_to_compare:
        data = cert_data.get(cert_type, {})
        if data:
            roi = None
            if request.property_value:
                # Simplified ROI: value premium / typical cost
                value_uplift = float(request.property_value) * (data["avg_value_premium"] / 100)
                # Use midpoint of cost range (very rough)
                typical_cost = 50000  # Simplified
                roi = ((value_uplift - typical_cost) / typical_cost * 100) if typical_cost > 0 else 0
            
            comparisons.append({
                "certification_type": cert_type.value,
                "typical_cost_to_certify": data["typical_cost_range"],
                "avg_rent_premium": data["avg_rent_premium"],
                "avg_value_premium": data["avg_value_premium"],
                "roi_estimate": round(roi, 1) if roi else None,
                "time_to_certify_months": data["time_months"],
                "difficulty_rating": data["difficulty"],
                "market_recognition": data["recognition"],
            })
    
    # Simple recommendation logic
    if request.region == Region.EUROPE:
        recommended = CertificationType.BREEAM
        reasoning = [
            "BREEAM is the most recognized certification in European markets",
            "Higher premiums achievable in Europe vs other regions",
            "Strong alignment with EU sustainability regulations",
        ]
    elif request.region == Region.NORTH_AMERICA:
        recommended = CertificationType.LEED
        reasoning = [
            "LEED is the dominant certification in North American markets",
            "Highest market recognition among tenants and investors",
            "Well-established premium data and track record",
        ]
    else:
        recommended = CertificationType.LEED
        reasoning = [
            "LEED has global recognition",
            "Consistent methodology across markets",
            "Strong investor familiarity",
        ]
    
    return CertificationComparisonResult(
        property_sector=request.property_sector,
        region=request.region,
        comparisons=comparisons,
        recommended_certification=recommended,
        recommendation_reasoning=reasoning,
    )


# ============ Enum Reference ============

@router.get("/enums")
async def get_enum_values():
    """Get all enum values for frontend dropdowns."""
    return {
        "certification_types": [e.value for e in CertificationType],
        "leed_levels": [e.value for e in LEEDLevel],
        "breeam_levels": [e.value for e in BREEAMLevel],
        "gresb_ratings": [e.value for e in GRESBRating],
        "property_sectors": [e.value for e in PropertySector],
        "regions": [e.value for e in Region],
    }
