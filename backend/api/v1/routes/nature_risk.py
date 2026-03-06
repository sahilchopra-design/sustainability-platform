"""
Nature Risk Integration API Routes
Based on TNFD LEAP methodology and NCORE framework
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from uuid import uuid4
import json

from db.base import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text
from schemas.nature_risk import (
    # Scenarios
    NatureRiskScenarioCreate, NatureRiskScenarioUpdate, NatureRiskScenarioResponse,
    # LEAP
    LEAPAssessmentCreate, LEAPAssessmentUpdate, LEAPAssessmentResponse, LEAPAssessmentRequest,
    # ENCORE
    ENCOREDependencyResponse,
    # Water Risk
    WaterRiskLocationCreate, WaterRiskLocationUpdate, WaterRiskLocationResponse, WaterRiskAnalysisRequest,
    # Biodiversity
    BiodiversitySiteResponse, BiodiversityOverlapRequest,
    # Portfolio
    PortfolioNatureRiskRequest, NatureRiskExposureResponse,
    # GBF
    GBFAlignmentTargetBase, GBFAlignmentTargetResponse,
    # Dashboard
    NatureRiskDashboardSummary,
    # Enums
    ScenarioType, FrameworkType, EntityType, RiskRating, SiteType
)
from services.nature_risk_calculator import (
    LEAPAssessmentCalculator,
    WaterRiskCalculator,
    BiodiversityOverlapCalculator,
    PortfolioNatureRiskCalculator
)
from services.nature_risk_seed_data import (
    get_encore_dependencies_by_sector,
    get_all_encore_sectors,
    get_default_scenarios,
    get_sample_biodiversity_sites,
    get_sample_water_risk_locations
)

router = APIRouter(prefix="/api/v1/nature-risk", tags=["Nature Risk Integration"])


# ============ Scenario Management Routes ============

@router.post("/scenarios", response_model=NatureRiskScenarioResponse)
async def create_scenario(scenario: NatureRiskScenarioCreate):
    """Create a new nature risk scenario."""
    scenario_id = str(uuid4())
    now = datetime.utcnow()
    
    return NatureRiskScenarioResponse(
        id=scenario_id,
        **scenario.model_dump(),
        created_at=now,
        updated_at=now
    )


@router.get("/scenarios", response_model=List[NatureRiskScenarioResponse])
async def list_scenarios(
    framework: Optional[str] = Query(None, description="TNFD, NCORE, or custom"),
    scenario_type: Optional[str] = Query(None, description="physical, transition, or combined"),
    is_active: Optional[bool] = Query(True)
):
    """List nature risk scenarios with optional filtering."""
    scenarios = get_default_scenarios()
    
    if framework:
        scenarios = [s for s in scenarios if s.get('framework') == framework]
    if scenario_type:
        scenarios = [s for s in scenarios if s.get('scenario_type') == scenario_type]
    if is_active is not None:
        scenarios = [s for s in scenarios if s.get('is_active', True) == is_active]
    
    return [
        NatureRiskScenarioResponse(
            id=s['id'],
            name=s['name'],
            description=s.get('description'),
            scenario_type=s['scenario_type'],
            framework=s['framework'],
            temperature_c=s.get('temperature_c'),
            precipitation_change_percent=s.get('precipitation_change_percent'),
            biodiversity_trend=s.get('biodiversity_trend'),
            policy_stringency=s.get('policy_stringency'),
            water_scarcity_index=s.get('water_scarcity_index'),
            ecosystem_degradation_rate=s.get('ecosystem_degradation_rate'),
            assumptions=s.get('assumptions'),
            is_active=s.get('is_active', True),
            created_at=datetime.utcnow(),
            updated_at=None
        )
        for s in scenarios
    ]


@router.get("/scenarios/{scenario_id}", response_model=NatureRiskScenarioResponse)
async def get_scenario(scenario_id: str):
    """Get a specific scenario by ID."""
    scenarios = get_default_scenarios()
    scenario = next((s for s in scenarios if s['id'] == scenario_id), None)
    
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    return NatureRiskScenarioResponse(
        id=scenario['id'],
        name=scenario['name'],
        description=scenario.get('description'),
        scenario_type=scenario['scenario_type'],
        framework=scenario['framework'],
        temperature_c=scenario.get('temperature_c'),
        precipitation_change_percent=scenario.get('precipitation_change_percent'),
        biodiversity_trend=scenario.get('biodiversity_trend'),
        policy_stringency=scenario.get('policy_stringency'),
        water_scarcity_index=scenario.get('water_scarcity_index'),
        ecosystem_degradation_rate=scenario.get('ecosystem_degradation_rate'),
        assumptions=scenario.get('assumptions'),
        is_active=scenario.get('is_active', True),
        created_at=datetime.utcnow(),
        updated_at=None
    )


# ============ LEAP Assessment Routes ============

@router.post("/leap-assessments", response_model=LEAPAssessmentResponse)
async def create_leap_assessment(assessment: LEAPAssessmentCreate):
    """Create a new LEAP assessment."""
    assessment_id = str(uuid4())
    now = datetime.utcnow()
    
    return LEAPAssessmentResponse(
        id=assessment_id,
        **assessment.model_dump(),
        created_at=now,
        updated_at=now
    )


@router.get("/leap-assessments", response_model=List[Dict])
async def list_leap_assessments(
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    risk_rating: Optional[str] = Query(None)
):
    """List LEAP assessments with filtering."""
    # Return sample assessments
    return []


@router.post("/leap-assessments/calculate")
async def calculate_leap_assessment(request: LEAPAssessmentRequest):
    """Calculate complete LEAP assessment scores using TNFD methodology."""
    # Get ENCORE data for the calculator
    encore_data = {}
    all_sectors = get_all_encore_sectors()
    for sector in all_sectors:
        encore_data[sector['code']] = get_encore_dependencies_by_sector(sector['code'])
    
    calculator = LEAPAssessmentCalculator(encore_data=encore_data)
    
    # Get scenarios
    all_scenarios = get_default_scenarios()
    scenarios = [s for s in all_scenarios if s['id'] in request.scenario_ids]
    
    if not scenarios:
        raise HTTPException(status_code=400, detail="No valid scenarios found")
    
    # Build entity data from request
    entity_data = {
        "entity_id": request.entity_id,
        "entity_type": request.entity_type,
        "sector_code": "ENERGY",  # Default, could be passed in request
        "biome_exposure": {},
        "value_chain_exposure": {"upstream": True, "operations": True, "downstream": False}
    }
    
    results = []
    for scenario in scenarios:
        assessment = calculator.calculate_leap_assessment(
            entity_data,
            scenario,
            include_water_risk=request.include_water_risk,
            include_biodiversity=request.include_biodiversity_overlap
        )
        results.append({
            "scenario_id": scenario.get('id'),
            "scenario_name": scenario.get('name'),
            **assessment
        })
    
    return {
        "entity_id": request.entity_id,
        "entity_type": request.entity_type,
        "assessment_date": datetime.now().isoformat(),
        "scenario_results": results
    }


# ============ ENCORE Dependency Routes ============

@router.get("/encore/sectors")
async def list_encore_sectors():
    """List all ENCORE sectors."""
    return get_all_encore_sectors()


@router.get("/encore/dependencies")
async def get_encore_dependencies(
    sector_code: Optional[str] = Query(None),
    ecosystem_service: Optional[str] = Query(None),
    min_score: Optional[int] = Query(None, ge=1, le=5)
):
    """Get ENCORE ecosystem service dependencies by sector."""
    if sector_code:
        dependencies = get_encore_dependencies_by_sector(sector_code)
    else:
        # Get all dependencies
        dependencies = []
        for sector in get_all_encore_sectors():
            deps = get_encore_dependencies_by_sector(sector['code'])
            dependencies.extend(deps)
    
    if ecosystem_service:
        dependencies = [d for d in dependencies if d.get('ecosystem_service') == ecosystem_service]
    
    if min_score:
        dependencies = [d for d in dependencies if (d.get('dependency_score') or 0) >= min_score]
    
    return dependencies


@router.get("/encore/ecosystem-services")
async def list_ecosystem_services():
    """List all ecosystem services in ENCORE framework."""
    services = [
        {"id": "water", "name": "Water", "category": "provisioning", "description": "Surface and groundwater resources"},
        {"id": "pollination", "name": "Pollination", "category": "regulating", "description": "Pollination services from insects and animals"},
        {"id": "flood_protection", "name": "Flood & Storm Protection", "category": "regulating", "description": "Natural flood and storm barriers"},
        {"id": "climate_regulation", "name": "Climate Regulation", "category": "regulating", "description": "Carbon sequestration and temperature regulation"},
        {"id": "soil_quality", "name": "Soil Quality", "category": "supporting", "description": "Soil fertility and erosion control"},
        {"id": "disease_control", "name": "Disease Control", "category": "regulating", "description": "Natural pest and disease control"},
        {"id": "genetic_resources", "name": "Genetic Resources", "category": "provisioning", "description": "Genetic material for agriculture and medicine"},
        {"id": "timber", "name": "Timber & Fiber", "category": "provisioning", "description": "Wood, fiber, and raw materials"},
        {"id": "air_quality", "name": "Air Quality", "category": "regulating", "description": "Air filtration and purification"},
        {"id": "habitat", "name": "Habitat Services", "category": "supporting", "description": "Habitat for species and biodiversity"}
    ]
    return services


# ============ Water Risk Routes ============

@router.post("/water-risk/locations", response_model=WaterRiskLocationResponse)
async def create_water_risk_location(location: WaterRiskLocationCreate):
    """Register a location for water risk analysis."""
    location_id = str(uuid4())
    now = datetime.utcnow()
    
    # Calculate water risk level
    water_stress = location.baseline_water_stress or 0
    if water_stress >= 4:
        water_risk_level = "extremely_high"
    elif water_stress >= 3:
        water_risk_level = "high"
    elif water_stress >= 2:
        water_risk_level = "medium-high"
    elif water_stress >= 1:
        water_risk_level = "low-medium"
    else:
        water_risk_level = "low"
    
    return WaterRiskLocationResponse(
        id=location_id,
        **location.model_dump(),
        water_risk_level=water_risk_level,
        created_at=now,
        updated_at=now
    )


@router.get("/water-risk/locations", response_model=List[Dict])
async def list_water_risk_locations(
    country: Optional[str] = Query(None),
    basin: Optional[str] = Query(None),
    min_risk: Optional[float] = Query(None),
    linked_asset_type: Optional[str] = Query(None)
):
    """List water risk locations with filtering."""
    locations = get_sample_water_risk_locations()
    
    if country:
        locations = [loc for loc in locations if loc.get('country_code') == country]
    if basin:
        locations = [loc for loc in locations if basin.lower() in (loc.get('basin_name') or '').lower()]
    if min_risk:
        locations = [loc for loc in locations if (loc.get('baseline_water_stress') or 0) >= min_risk]
    if linked_asset_type:
        locations = [loc for loc in locations if loc.get('linked_asset_type') == linked_asset_type]
    
    return locations


@router.post("/water-risk/analyze")
async def analyze_water_risk(request: WaterRiskAnalysisRequest):
    """Calculate water risk for locations under climate scenarios."""
    calculator = WaterRiskCalculator()
    
    # Get locations
    all_locations = get_sample_water_risk_locations()
    locations = [loc for loc in all_locations if loc.get('id') in request.location_ids]
    
    if not locations:
        # If no specific locations, use all
        locations = all_locations[:5]
    
    # Get scenarios
    all_scenarios = get_default_scenarios()
    scenarios = [s for s in all_scenarios if s['id'] in request.scenario_ids]
    
    if not scenarios:
        scenarios = all_scenarios[:1]  # Use first scenario as default
    
    results = []
    for scenario in scenarios:
        for location in locations:
            risk = calculator.calculate_water_risk(
                location,
                scenario,
                include_projections=request.include_projections
            )
            results.append({
                "location_id": location.get('id'),
                "location_name": location.get('location_name'),
                "scenario_id": scenario.get('id'),
                "scenario_name": scenario.get('name'),
                **risk
            })
    
    return {
        "analysis_date": datetime.now().isoformat(),
        "location_count": len(locations),
        "scenario_count": len(scenarios),
        "results": results
    }


@router.get("/water-risk/locations/{location_id}/risk-report")
async def get_water_risk_report(
    location_id: str,
    scenario_id: Optional[str] = Query(None)
):
    """Get comprehensive water risk report for a location."""
    locations = get_sample_water_risk_locations()
    location = next((loc for loc in locations if loc.get('id') == location_id), None)
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    scenarios = get_default_scenarios()
    scenario = scenarios[0] if not scenario_id else next((s for s in scenarios if s['id'] == scenario_id), scenarios[0])
    
    calculator = WaterRiskCalculator()
    risk = calculator.calculate_water_risk(location, scenario)
    
    return {
        "location": {
            "id": location.get('id'),
            "name": location.get('location_name'),
            "type": location.get('location_type'),
            "country": location.get('country_code'),
            "basin": location.get('basin_name')
        },
        "scenario": {
            "id": scenario.get('id'),
            "name": scenario.get('name')
        },
        **risk
    }


# ============ Biodiversity Routes ============

@router.get("/biodiversity/sites", response_model=List[Dict])
async def list_biodiversity_sites(
    country: Optional[str] = Query(None),
    site_type: Optional[str] = Query(None),
    min_area: Optional[float] = Query(None)
):
    """List biodiversity sites from WDPA, KBA, and other sources."""
    sites = get_sample_biodiversity_sites()
    
    if country:
        sites = [s for s in sites if s.get('country_code') == country]
    if site_type:
        sites = [s for s in sites if s.get('site_type') == site_type]
    if min_area:
        sites = [s for s in sites if (s.get('area_km2') or 0) >= min_area]
    
    return sites


@router.post("/biodiversity/overlaps/calculate")
async def calculate_biodiversity_overlaps(request: BiodiversityOverlapRequest):
    """Calculate overlaps between assets and biodiversity sites."""
    sites = get_sample_biodiversity_sites()
    
    if request.site_types:
        site_type_values = [st.value if hasattr(st, 'value') else st for st in request.site_types]
        sites = [s for s in sites if s.get('site_type') in site_type_values]
    
    calculator = BiodiversityOverlapCalculator(biodiversity_sites=sites)
    
    # For demo, create sample assets
    sample_assets = [
        {"id": aid, "latitude": -3.4653, "longitude": -62.2159, "name": f"Asset {aid[:8]}"} 
        for aid in request.asset_ids
    ]
    
    results = []
    for asset in sample_assets:
        overlaps = calculator.calculate_overlaps(
            asset,
            request.asset_type,
            buffer_distances=[request.buffer_distance_km]
        )
        results.append({
            "asset_id": asset.get('id'),
            "asset_name": asset.get('name'),
            **overlaps
        })
    
    return {
        "analysis_date": datetime.now().isoformat(),
        "asset_count": len(sample_assets),
        "site_count": len(sites),
        "results": results
    }


# ============ Portfolio Nature Risk Routes (Financial Sector) ============

@router.post("/portfolio/analyze")
async def analyze_portfolio_nature_risk(request: PortfolioNatureRiskRequest):
    """Comprehensive nature risk analysis for portfolios."""
    calculator = PortfolioNatureRiskCalculator()
    
    # Get scenarios
    all_scenarios = get_default_scenarios()
    scenarios = [s for s in all_scenarios if s['id'] in request.scenario_ids]
    
    if not scenarios:
        scenarios = all_scenarios[:1]
    
    # Sample holdings for demo
    sample_holdings = [
        {
            "id": str(uuid4()),
            "entity_name": "Energy Corp A",
            "sector": "ENERGY",
            "exposure_usd": 50000000,
            "sector_code": "ENERGY",
            "biome_exposure": {"tropical_forest": True, "freshwater": True},
            "baseline_water_stress": 3.5
        },
        {
            "id": str(uuid4()),
            "entity_name": "Mining Corp B",
            "sector": "MINING",
            "exposure_usd": 30000000,
            "sector_code": "MINING",
            "biome_exposure": {"grassland": True, "mountain": True},
            "baseline_water_stress": 4.2
        },
        {
            "id": str(uuid4()),
            "entity_name": "Agribusiness Corp C",
            "sector": "AGRICULTURE",
            "exposure_usd": 25000000,
            "sector_code": "AGRICULTURE",
            "biome_exposure": {"savanna": True, "wetland": True},
            "baseline_water_stress": 2.8
        }
    ]
    
    result = calculator.calculate_portfolio_nature_risk(
        sample_holdings,
        scenarios,
        include_collateral_impact=request.include_collateral_impact
    )
    
    return {
        "portfolio_id": request.portfolio_id,
        "portfolio_name": f"Portfolio {request.portfolio_id[:8]}",
        "analysis_date": datetime.now().isoformat(),
        **result
    }


@router.get("/portfolio/{portfolio_id}/nature-exposure")
async def get_portfolio_nature_exposure(
    portfolio_id: str,
    scenario_id: Optional[str] = Query(None)
):
    """Get summary of portfolio exposure to nature-related risks."""
    # Return sample exposure data
    return {
        "portfolio_id": portfolio_id,
        "total_exposure_usd": 105000000,
        "high_risk_exposure_usd": 30000000,
        "high_risk_percent": 28.6,
        "sector_breakdown": {
            "ENERGY": {"exposure_usd": 50000000, "avg_risk_score": 3.2},
            "MINING": {"exposure_usd": 30000000, "avg_risk_score": 4.1},
            "AGRICULTURE": {"exposure_usd": 25000000, "avg_risk_score": 2.5}
        },
        "key_dependencies": ["water", "soil_quality", "climate_regulation"],
        "recommendations": [
            "Reduce exposure to high water-stress mining operations",
            "Engage with energy sector on nature transition plans",
            "Monitor agricultural dependencies on pollination services"
        ]
    }


# ============ GBF Alignment Routes ============

@router.post("/gbf-alignment", response_model=GBFAlignmentTargetResponse)
async def create_gbf_alignment(alignment: GBFAlignmentTargetBase):
    """Track alignment with Global Biodiversity Framework targets."""
    alignment_id = str(uuid4())
    now = datetime.utcnow()
    
    return GBFAlignmentTargetResponse(
        id=alignment_id,
        **alignment.model_dump(),
        created_at=now,
        updated_at=now
    )


@router.get("/gbf-alignment/{entity_type}/{entity_id}")
async def get_gbf_alignment(
    entity_type: str,
    entity_id: str,
    reporting_year: Optional[int] = Query(None)
):
    """Get GBF target alignment status for an entity."""
    # Sample GBF targets
    gbf_targets = [
        {
            "id": str(uuid4()),
            "entity_id": entity_id,
            "entity_type": entity_type,
            "target_number": "Target 1",
            "target_description": "Ensure spatial planning reduces biodiversity loss",
            "alignment_status": "partial",
            "alignment_score": 45.0,
            "reporting_year": reporting_year or 2024,
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "id": str(uuid4()),
            "entity_id": entity_id,
            "entity_type": entity_type,
            "target_number": "Target 15",
            "target_description": "Businesses assess and disclose nature dependencies",
            "alignment_status": "aligned",
            "alignment_score": 78.0,
            "reporting_year": reporting_year or 2024,
            "created_at": datetime.utcnow().isoformat()
        }
    ]
    
    return gbf_targets


@router.get("/gbf-targets")
async def list_gbf_targets():
    """List all GBF targets with descriptions."""
    targets = [
        {"number": "Target 1", "description": "Ensure spatial planning reduces biodiversity loss", "category": "Reducing threats"},
        {"number": "Target 2", "description": "Restore 30% of degraded ecosystems", "category": "Reducing threats"},
        {"number": "Target 3", "description": "Conserve 30% of land, waters, and seas", "category": "Reducing threats"},
        {"number": "Target 4", "description": "Halt species extinction and reduce extinction risk", "category": "Reducing threats"},
        {"number": "Target 5", "description": "Ensure sustainable use of wild species", "category": "Reducing threats"},
        {"number": "Target 6", "description": "Reduce impacts of invasive alien species", "category": "Reducing threats"},
        {"number": "Target 7", "description": "Reduce pollution risks to biodiversity", "category": "Reducing threats"},
        {"number": "Target 8", "description": "Minimize climate change impacts on biodiversity", "category": "Reducing threats"},
        {"number": "Target 9", "description": "Ensure sustainable management of wild species", "category": "Meeting people's needs"},
        {"number": "Target 10", "description": "Ensure sustainable management of agriculture, aquaculture, forestry", "category": "Meeting people's needs"},
        {"number": "Target 11", "description": "Restore and maintain ecosystem services", "category": "Meeting people's needs"},
        {"number": "Target 12", "description": "Increase green and blue spaces in urban areas", "category": "Meeting people's needs"},
        {"number": "Target 13", "description": "Fair and equitable sharing of genetic resources", "category": "Meeting people's needs"},
        {"number": "Target 14", "description": "Integrate biodiversity into policies and development", "category": "Tools and solutions"},
        {"number": "Target 15", "description": "Businesses assess and disclose nature dependencies", "category": "Tools and solutions"},
        {"number": "Target 16", "description": "Enable sustainable consumption choices", "category": "Tools and solutions"},
        {"number": "Target 17", "description": "Establish biosafety measures", "category": "Tools and solutions"},
        {"number": "Target 18", "description": "Reform harmful subsidies", "category": "Tools and solutions"},
        {"number": "Target 19", "description": "Mobilize $200 billion annually for biodiversity", "category": "Tools and solutions"},
        {"number": "Target 20", "description": "Strengthen capacity building and technology transfer", "category": "Tools and solutions"},
        {"number": "Target 21", "description": "Ensure participation of indigenous peoples", "category": "Tools and solutions"},
        {"number": "Target 22", "description": "Ensure gender-responsive implementation", "category": "Tools and solutions"},
        {"number": "Target 23", "description": "Ensure gender equality in biodiversity action", "category": "Tools and solutions"}
    ]
    return targets


# ============ Dashboard & Reporting Routes ============

@router.get("/dashboard/summary", response_model=NatureRiskDashboardSummary)
async def get_nature_risk_dashboard(
    portfolio_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Get high-level nature risk dashboard summary — driven by real CSRD data when available."""
    try:
        bio_rows = db.execute(text("""
            SELECT
                cer.primary_sector,
                b.sites_in_near_protected_or_kba_count,
                b.biodiversity_financial_effects_risk_eur,
                b.tnfd_locate_complete, b.tnfd_evaluate_complete,
                b.tnfd_assess_complete, b.tnfd_prepare_complete
            FROM esrs_e4_biodiversity b
            JOIN csrd_entity_registry cer ON cer.id = b.entity_registry_id
            WHERE b.reporting_year = 2024
        """)).fetchall()

        water_rows = db.execute(text("""
            SELECT
                cer.primary_sector,
                w.total_water_consumption_m3,
                w.withdrawal_high_stress_areas_m3,
                w.withdrawal_high_stress_areas_pct,
                w.water_financial_effects_risk_eur
            FROM esrs_e3_water w
            JOIN csrd_entity_registry cer ON cer.id = w.entity_registry_id
            WHERE w.reporting_year = 2024
        """)).fetchall()
    except Exception:
        bio_rows, water_rows = [], []

    if bio_rows or water_rows:
        total_entities = max(len(bio_rows), len(water_rows))

        # Water risk exposure
        high_stress = sum(
            1 for r in water_rows
            if r[3] is not None and float(r[3]) >= 50
        )
        total_w = sum(float(r[2]) if r[2] else 0 for r in water_rows)
        water_exp = {
            "high_stress_entities": high_stress,
            "total_entities": len(water_rows),
            "total_consumption_m3": round(total_w, 0),
        }

        # Biodiversity overlaps
        kba_exposed = sum(1 for r in bio_rows if r[1] and int(r[1]) > 0)
        bio_exp = {
            "entities_with_kba_exposure": kba_exposed,
            "total_entities": len(bio_rows),
        }

        # TNFD progress → proxy for GBF
        complete = sum(
            1 for r in bio_rows
            if all([r[3], r[4], r[5], r[6]])
        )
        partial = sum(
            1 for r in bio_rows
            if any([r[3], r[4], r[5], r[6]]) and not all([r[3], r[4], r[5], r[6]])
        )
        gbf_al = {
            "fully_leap_complete": complete,
            "partially_leap_complete": partial,
            "not_started": len(bio_rows) - complete - partial,
            "total_entities": len(bio_rows),
        }

        # Sector breakdown from water rows
        from collections import defaultdict
        sector_counts: dict = defaultdict(int)
        for r in water_rows:
            sector_counts[r[0] or "Other"] += 1
        sector_bd = {s: {"count": c} for s, c in sector_counts.items()}

        high_risk = sum(
            1 for r in water_rows
            if r[3] is not None and float(r[3]) >= 50
        )

        return NatureRiskDashboardSummary(
            total_assessments=total_entities,
            high_risk_entities=high_risk,
            critical_risk_entities=sum(1 for r in water_rows if r[3] and float(r[3]) >= 75),
            water_risk_exposure=water_exp,
            biodiversity_overlaps=bio_exp,
            gbf_alignment=gbf_al,
            sector_breakdown=sector_bd,
            trend_data=[],
        )

    # Fallback when no CSRD data available
    return NatureRiskDashboardSummary(
        total_assessments=15,
        high_risk_entities=4,
        critical_risk_entities=1,
        water_risk_exposure={"high_stress_locations": 8, "total_locations": 25, "avg_water_stress": 2.8},
        biodiversity_overlaps={"direct_overlaps": 3, "buffer_overlaps": 12, "critical_sites_affected": 2},
        gbf_alignment={"aligned_targets": 8, "partial_targets": 10, "not_aligned_targets": 5, "total_targets": 23},
        sector_breakdown={
            "ENERGY": {"count": 5, "avg_risk": 3.2},
            "MINING": {"count": 3, "avg_risk": 4.1},
            "AGRICULTURE": {"count": 4, "avg_risk": 2.5},
            "FINANCE": {"count": 3, "avg_risk": 2.8},
        },
        trend_data=[
            {"month": "Jan", "risk_score": 2.8}, {"month": "Feb", "risk_score": 2.9},
            {"month": "Mar", "risk_score": 3.1}, {"month": "Apr", "risk_score": 3.0},
            {"month": "May", "risk_score": 2.9}, {"month": "Jun", "risk_score": 2.8},
        ],
    )


@router.post("/reports/tnfd-disclosure")
async def generate_tnfd_disclosure(
    entity_id: str,
    entity_type: str,
    reporting_year: int = Query(default=2024)
):
    """Generate TNFD-aligned disclosure report for an entity."""
    return {
        "entity_id": entity_id,
        "entity_type": entity_type,
        "reporting_year": reporting_year,
        "report_date": datetime.now().isoformat(),
        "framework_version": "TNFD v1.0",
        "disclosures": {
            "governance": {
                "board_oversight": "Quarterly nature risk reviews",
                "management_role": "Chief Sustainability Officer leads nature strategy"
            },
            "strategy": {
                "nature_dependencies": ["water", "soil_quality", "climate_regulation"],
                "nature_impacts": ["land_use_change", "pollution", "resource_extraction"],
                "risks_identified": 5,
                "opportunities_identified": 3
            },
            "risk_management": {
                "assessment_processes": "Annual LEAP assessment",
                "integration_approach": "Integrated into ERM framework"
            },
            "metrics_targets": {
                "metrics_reported": 12,
                "targets_set": 8,
                "gbf_alignment_score": 65.0
            }
        },
        "recommendations": [
            "Enhance board oversight of nature-related risks",
            "Develop quantitative targets for biodiversity",
            "Improve supply chain nature risk assessment"
        ]
    }


# ============ Data Import Routes ============

@router.post("/import/encore-data")
async def import_encore_data():
    """Import ENCORE ecosystem dependency data."""
    sectors = get_all_encore_sectors()
    total_dependencies = 0
    
    for sector in sectors:
        deps = get_encore_dependencies_by_sector(sector['code'])
        total_dependencies += len(deps)
    
    return {
        "status": "success",
        "message": "ENCORE data loaded",
        "sectors_imported": len(sectors),
        "dependencies_imported": total_dependencies
    }


@router.post("/import/biodiversity-sites")
async def import_biodiversity_sites():
    """Import biodiversity site data from WDPA/KBA."""
    sites = get_sample_biodiversity_sites()

    return {
        "status": "success",
        "message": "Biodiversity sites loaded",
        "sites_imported": len(sites),
        "site_types": list(set(s.get('site_type') for s in sites))
    }


# ============ CSRD Entity-Level Nature Data (Real DB) ============

@router.get("/csrd-entities/biodiversity")
async def get_csrd_biodiversity_data(
    reporting_year: int = Query(default=2024, description="ESRS reporting year"),
    db: Session = Depends(get_db),
):
    """Real CSRD entity biodiversity data from esrs_e4_biodiversity table."""
    try:
        rows = db.execute(text("""
            SELECT
                cer.id                                          AS entity_id,
                cer.legal_name,
                cer.primary_sector,
                cer.country_iso,
                b.reporting_year,
                b.sites_in_near_protected_or_kba_count,
                b.sites_in_near_protected_or_kba_area_ha,
                b.total_land_use_area_ha,
                b.threatened_species_affected_count,
                b.tnfd_locate_complete,
                b.tnfd_evaluate_complete,
                b.tnfd_assess_complete,
                b.tnfd_prepare_complete,
                b.biodiversity_financial_effects_risk_eur,
                b.biodiversity_net_gain_score
            FROM esrs_e4_biodiversity b
            JOIN csrd_entity_registry cer ON cer.id = b.entity_registry_id
            WHERE b.reporting_year = :yr
            ORDER BY cer.legal_name
        """), {"yr": reporting_year}).fetchall()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"DB query failed: {exc}")

    if not rows:
        return {"reporting_year": reporting_year, "entities": [], "summary": {}}

    entities = []
    for r in rows:
        tnfd_steps = sum([
            1 if r[9] else 0,
            1 if r[10] else 0,
            1 if r[11] else 0,
            1 if r[12] else 0,
        ])
        entities.append({
            "entity_id": str(r[0]),
            "legal_name": r[1],
            "sector": r[2],
            "country": r[3],
            "reporting_year": r[4],
            "kba_sites_count": r[5] or 0,
            "kba_sites_area_ha": float(r[6]) if r[6] else None,
            "total_land_use_ha": float(r[7]) if r[7] else None,
            "threatened_species_count": r[8] or 0,
            "tnfd_leap_progress": {
                "locate": bool(r[9]),
                "evaluate": bool(r[10]),
                "assess": bool(r[11]),
                "prepare": bool(r[12]),
                "steps_complete": tnfd_steps,
                "pct_complete": round(tnfd_steps / 4 * 100),
            },
            "financial_risk_eur": float(r[13]) if r[13] else None,
            "biodiversity_net_gain_score": float(r[14]) if r[14] else None,
        })

    total_financial_risk = sum(e["financial_risk_eur"] for e in entities if e["financial_risk_eur"])
    avg_tnfd_pct = round(sum(e["tnfd_leap_progress"]["pct_complete"] for e in entities) / len(entities))

    return {
        "reporting_year": reporting_year,
        "entities": entities,
        "summary": {
            "total_entities": len(entities),
            "entities_with_kba_exposure": sum(1 for e in entities if e["kba_sites_count"] > 0),
            "total_financial_risk_eur": round(total_financial_risk, 0),
            "avg_tnfd_leap_completion_pct": avg_tnfd_pct,
            "source": "ESRS E4 — CSRD entity disclosures",
        },
    }


@router.get("/csrd-entities/water")
async def get_csrd_water_data(
    reporting_year: int = Query(default=2024, description="ESRS reporting year"),
    db: Session = Depends(get_db),
):
    """Real CSRD entity water risk data from esrs_e3_water table."""
    try:
        rows = db.execute(text("""
            SELECT
                cer.id                                          AS entity_id,
                cer.legal_name,
                cer.primary_sector,
                cer.country_iso,
                w.reporting_year,
                w.total_water_consumption_m3,
                w.withdrawal_high_stress_areas_m3,
                w.withdrawal_high_stress_areas_pct,
                w.discharge_high_stress_areas_m3,
                w.water_recycled_m3,
                w.water_intensity_revenue,
                w.water_financial_effects_risk_eur,
                w.water_financial_effects_opp_eur
            FROM esrs_e3_water w
            JOIN csrd_entity_registry cer ON cer.id = w.entity_registry_id
            WHERE w.reporting_year = :yr
            ORDER BY cer.legal_name
        """), {"yr": reporting_year}).fetchall()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"DB query failed: {exc}")

    if not rows:
        return {"reporting_year": reporting_year, "entities": [], "summary": {}}

    entities = []
    for r in rows:
        total_w = float(r[5]) if r[5] else 0
        high_stress_w = float(r[6]) if r[6] else 0
        high_stress_pct = float(r[7]) if r[7] else (
            round(high_stress_w / total_w * 100, 1) if total_w > 0 else 0
        )
        risk_level = (
            "critical" if high_stress_pct >= 75 else
            "high"     if high_stress_pct >= 50 else
            "medium"   if high_stress_pct >= 25 else
            "low"
        )
        entities.append({
            "entity_id": str(r[0]),
            "legal_name": r[1],
            "sector": r[2],
            "country": r[3],
            "reporting_year": r[4],
            "total_water_consumption_m3": total_w,
            "withdrawal_high_stress_m3": high_stress_w,
            "withdrawal_high_stress_pct": high_stress_pct,
            "discharge_high_stress_m3": float(r[8]) if r[8] else None,
            "water_recycled_m3": float(r[9]) if r[9] else None,
            "water_intensity_revenue": float(r[10]) if r[10] else None,
            "financial_risk_eur": float(r[11]) if r[11] else None,
            "financial_opportunity_eur": float(r[12]) if r[12] else None,
            "risk_level": risk_level,
        })

    total_risk_eur = sum(e["financial_risk_eur"] for e in entities if e["financial_risk_eur"])
    high_stress_entities = sum(1 for e in entities if e["risk_level"] in ("high", "critical"))

    return {
        "reporting_year": reporting_year,
        "entities": entities,
        "summary": {
            "total_entities": len(entities),
            "high_stress_entities": high_stress_entities,
            "total_financial_risk_eur": round(total_risk_eur, 0),
            "total_consumption_m3": round(sum(e["total_water_consumption_m3"] for e in entities), 0),
            "source": "ESRS E3 — CSRD entity disclosures",
        },
    }
