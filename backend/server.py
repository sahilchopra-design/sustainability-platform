from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
import numpy as np

from database import init_db, close_db
from models import (
    Portfolio, Asset, Company, AssetType, Sector,
    ScenarioSeries, AnalysisRun, ScenarioResult,
    Scenario
)
from risk_engine import RiskEngine, SECTOR_MULTIPLIERS
from services.calculation_engine import ClimateRiskCalculationEngine
from services.engine_integration import assets_to_inputs, engine_results_to_models

# Import v1 scenario routes
from api.v1.routes.scenarios import router as scenarios_router
from api.v1.routes.data_hub import router as data_hub_router
from api.v1.routes.analysis import router as analysis_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    # Initialize PostgreSQL tables for scenarios
    from db.base import init_db as init_postgres_db
    init_postgres_db()
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title="Climate Credit Risk Intelligence Platform",
    description="Portfolio Scenario Analysis with NGFS Climate Data",
    version="1.0.0",
    lifespan=lifespan
)

# Include scenario builder routes
app.include_router(scenarios_router)
# Include data hub routes
app.include_router(data_hub_router)
# Include analysis routes
app.include_router(analysis_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic schemas
class PortfolioCreate(BaseModel):
    name: str
    description: Optional[str] = None


class PortfolioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    assets: Optional[List[Asset]] = None


class AssetAdd(BaseModel):
    asset: Asset


class AnalysisRequest(BaseModel):
    portfolio_id: str
    scenarios: List[str]
    horizons: List[int]


class ScenarioDataRefresh(BaseModel):
    force: bool = False


# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# Portfolio endpoints
@app.get("/api/portfolios")
async def get_portfolios():
    """Get all portfolios"""
    portfolios = await Portfolio.find_all().to_list()
    return {
        "portfolios": [
            {
                "id": str(p.id),
                "name": p.name,
                "description": p.description,
                "num_assets": len(p.assets),
                "total_exposure": sum(a.exposure for a in p.assets),
                "created_at": p.created_at.isoformat(),
                "updated_at": p.updated_at.isoformat()
            }
            for p in portfolios
        ]
    }


@app.post("/api/portfolios")
async def create_portfolio(data: PortfolioCreate):
    """Create a new portfolio"""
    portfolio = Portfolio(
        name=data.name,
        description=data.description,
        assets=[]
    )
    await portfolio.insert()
    
    return {
        "id": str(portfolio.id),
        "name": portfolio.name,
        "description": portfolio.description,
        "assets": [],
        "created_at": portfolio.created_at.isoformat()
    }


@app.get("/api/portfolios/{portfolio_id}")
async def get_portfolio(portfolio_id: str):
    """Get portfolio details"""
    portfolio = await Portfolio.get(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    return {
        "id": str(portfolio.id),
        "name": portfolio.name,
        "description": portfolio.description,
        "assets": [a.model_dump() for a in portfolio.assets],
        "total_exposure": sum(a.exposure for a in portfolio.assets),
        "created_at": portfolio.created_at.isoformat(),
        "updated_at": portfolio.updated_at.isoformat()
    }


@app.put("/api/portfolios/{portfolio_id}")
async def update_portfolio(portfolio_id: str, data: PortfolioUpdate):
    """Update portfolio"""
    portfolio = await Portfolio.get(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    if data.name is not None:
        portfolio.name = data.name
    if data.description is not None:
        portfolio.description = data.description
    if data.assets is not None:
        portfolio.assets = data.assets
    
    portfolio.updated_at = datetime.utcnow()
    await portfolio.save()
    
    return {
        "id": str(portfolio.id),
        "name": portfolio.name,
        "description": portfolio.description,
        "assets": [a.model_dump() for a in portfolio.assets],
        "updated_at": portfolio.updated_at.isoformat()
    }


@app.delete("/api/portfolios/{portfolio_id}")
async def delete_portfolio(portfolio_id: str):
    """Delete portfolio"""
    portfolio = await Portfolio.get(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    await portfolio.delete()
    return {"message": "Portfolio deleted", "id": portfolio_id}


@app.post("/api/portfolios/{portfolio_id}/assets")
async def add_asset_to_portfolio(portfolio_id: str, data: AssetAdd):
    """Add asset to portfolio"""
    portfolio = await Portfolio.get(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Generate unique ID for asset if not provided
    if not data.asset.id:
        data.asset.id = str(uuid.uuid4())
    
    portfolio.assets.append(data.asset)
    portfolio.updated_at = datetime.utcnow()
    await portfolio.save()
    
    return {
        "message": "Asset added",
        "asset": data.asset.model_dump(),
        "portfolio_id": portfolio_id
    }


@app.delete("/api/portfolios/{portfolio_id}/assets/{asset_id}")
async def remove_asset_from_portfolio(portfolio_id: str, asset_id: str):
    """Remove asset from portfolio"""
    portfolio = await Portfolio.get(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    portfolio.assets = [a for a in portfolio.assets if a.id != asset_id]
    portfolio.updated_at = datetime.utcnow()
    await portfolio.save()
    
    return {"message": "Asset removed", "asset_id": asset_id}


# Scenario data endpoints
@app.get("/api/scenario-data")
async def get_scenario_data():
    """Get overview of available scenario data"""
    # Get unique scenarios, variables, regions
    all_data = await ScenarioSeries.find_all().to_list()
    
    scenarios = list(set(d.scenario for d in all_data))
    variables = list(set(d.variable for d in all_data))
    regions = list(set(d.region for d in all_data))
    years = sorted(list(set(d.year for d in all_data)))
    
    return {
        "scenarios": scenarios,
        "variables": variables,
        "regions": regions,
        "years": years,
        "total_records": len(all_data)
    }


@app.post("/api/scenario-data/refresh")
async def refresh_scenario_data(data: ScenarioDataRefresh):
    """Refresh scenario data from NGFS sources"""
    # Check if data already exists
    existing_count = await ScenarioSeries.count()
    
    if existing_count > 0 and not data.force:
        return {
            "message": "Scenario data already exists. Use force=true to refresh.",
            "existing_records": existing_count
        }
    
    # Import POC ingestion logic
    from datetime import datetime as dt
    
    SCENARIOS = ['Orderly', 'Disorderly', 'Hot house world']
    HORIZONS = [2030, 2040, 2050]
    
    scenario_profiles = {
        'Orderly': {
            'carbon_price_mult': [2.0, 3.5, 5.0],
            'gdp_growth': [0.98, 0.95, 0.93],
            'emissions_mult': [0.7, 0.4, 0.2],
            'coal_mult': [0.5, 0.2, 0.05],
            'temp_increase': [1.6, 1.7, 1.8]
        },
        'Disorderly': {
            'carbon_price_mult': [1.5, 4.0, 6.0],
            'gdp_growth': [0.95, 0.90, 0.85],
            'emissions_mult': [0.8, 0.5, 0.25],
            'coal_mult': [0.7, 0.3, 0.1],
            'temp_increase': [1.8, 2.0, 2.1]
        },
        'Hot house world': {
            'carbon_price_mult': [1.0, 1.2, 1.3],
            'gdp_growth': [1.0, 0.92, 0.80],
            'emissions_mult': [1.0, 1.1, 1.2],
            'coal_mult': [0.95, 0.85, 0.75],
            'temp_increase': [2.5, 3.2, 4.0]
        }
    }
    
    regions = ['World', 'United States', 'European Union', 'China']
    model_name = 'NGFS_Phase5_Synthetic'
    source_version = f"NGFS_Phase5_{dt.utcnow().strftime('%Y%m%d')}"
    
    baseline = {
        'carbon_price': 30,
        'gdp': 100,
        'emissions': 50,
        'coal_energy': 30,
        'gas_energy': 25,
        'temperature': 1.2
    }
    
    # Delete existing data if force refresh
    if data.force:
        await ScenarioSeries.find_all().delete()
    
    records = []
    for scenario in SCENARIOS:
        profile = scenario_profiles[scenario]
        
        for idx, year in enumerate(HORIZONS):
            for region in regions:
                if region == 'United States':
                    region_mult = 0.9
                elif region == 'European Union':
                    region_mult = 0.85
                elif region == 'China':
                    region_mult = 1.1
                else:
                    region_mult = 1.0
                
                # Create scenario series documents
                records.extend([
                    ScenarioSeries(
                        year=year,
                        scenario=scenario,
                        model=model_name,
                        region=region,
                        variable='Price|Carbon',
                        unit='USD/tCO2',
                        value=baseline['carbon_price'] * profile['carbon_price_mult'][idx] * region_mult,
                        source_version=source_version
                    ),
                    ScenarioSeries(
                        year=year,
                        scenario=scenario,
                        model=model_name,
                        region=region,
                        variable='GDP|PPP',
                        unit='Index (2020=100)',
                        value=baseline['gdp'] * profile['gdp_growth'][idx] * region_mult,
                        source_version=source_version
                    ),
                    ScenarioSeries(
                        year=year,
                        scenario=scenario,
                        model=model_name,
                        region=region,
                        variable='Emissions|CO2',
                        unit='GtCO2',
                        value=baseline['emissions'] * profile['emissions_mult'][idx] * region_mult,
                        source_version=source_version
                    ),
                    ScenarioSeries(
                        year=year,
                        scenario=scenario,
                        model=model_name,
                        region=region,
                        variable='Temperature|Global Mean',
                        unit='°C',
                        value=baseline['temperature'] + profile['temp_increase'][idx],
                        source_version=source_version
                    )
                ])
    
    # Bulk insert
    await ScenarioSeries.insert_many(records)
    
    return {
        "message": "Scenario data refreshed successfully",
        "records_inserted": len(records),
        "source_version": source_version
    }


# Analysis endpoints
@app.post("/api/analysis/run")
async def run_analysis(data: AnalysisRequest):
    """Run scenario analysis on a portfolio using the new calculation engine"""
    # Get portfolio
    portfolio = await Portfolio.get(data.portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    if len(portfolio.assets) == 0:
        raise HTTPException(status_code=400, detail="Portfolio has no assets")
    
    # Convert portfolio assets to calculation engine input format
    asset_inputs = assets_to_inputs(portfolio.assets)
    
    # Initialize calculation engine
    engine = ClimateRiskCalculationEngine(
        n_simulations=10000,
        correlation=0.3,
        var_method='monte_carlo',
        base_return=0.05,
        random_seed=42
    )
    
    # Run calculation for all scenario-horizon combinations
    engine_results = engine.calculate_multiple_scenarios(
        assets=asset_inputs,
        scenarios=data.scenarios,
        horizons=data.horizons,
        include_sector_breakdown=False
    )
    
    # Convert engine results to API response format (ScenarioResult models)
    results = engine_results_to_models(engine_results)
    
    # Save analysis run
    analysis = AnalysisRun(
        portfolio_id=str(portfolio.id),
        portfolio_name=portfolio.name,
        scenarios=data.scenarios,
        horizons=data.horizons,
        results=results,
        status="completed",
        completed_at=datetime.utcnow()
    )
    await analysis.insert()
    
    return {
        "id": str(analysis.id),
        "portfolio_id": str(portfolio.id),
        "portfolio_name": portfolio.name,
        "scenarios": data.scenarios,
        "horizons": data.horizons,
        "results": [r.model_dump() for r in results],
        "status": "completed",
        "created_at": analysis.created_at.isoformat()
    }


@app.get("/api/analysis/runs")
async def get_analysis_runs(portfolio_id: Optional[str] = None):
    """Get all analysis runs, optionally filtered by portfolio"""
    if portfolio_id:
        runs = await AnalysisRun.find(AnalysisRun.portfolio_id == portfolio_id).to_list()
    else:
        runs = await AnalysisRun.find_all().to_list()
    
    return {
        "runs": [
            {
                "id": str(r.id),
                "portfolio_id": r.portfolio_id,
                "portfolio_name": r.portfolio_name,
                "scenarios": r.scenarios,
                "horizons": r.horizons,
                "status": r.status,
                "created_at": r.created_at.isoformat(),
                "completed_at": r.completed_at.isoformat() if r.completed_at else None
            }
            for r in runs
        ]
    }


@app.get("/api/analysis/runs/{run_id}")
async def get_analysis_run(run_id: str):
    """Get detailed analysis run results"""
    run = await AnalysisRun.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Analysis run not found")
    
    return {
        "id": str(run.id),
        "portfolio_id": run.portfolio_id,
        "portfolio_name": run.portfolio_name,
        "scenarios": run.scenarios,
        "horizons": run.horizons,
        "results": [r.model_dump() for r in run.results],
        "status": run.status,
        "created_at": run.created_at.isoformat(),
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "error_message": run.error_message
    }


@app.delete("/api/analysis/runs/{run_id}")
async def delete_analysis_run(run_id: str):
    """Delete analysis run"""
    run = await AnalysisRun.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Analysis run not found")
    
    await run.delete()
    return {"message": "Analysis run deleted", "id": run_id}


# Sample data generation
@app.post("/api/sample-data/generate")
async def generate_sample_data():
    """Generate sample portfolio for demo purposes"""
    # Check if sample portfolio exists
    existing = await Portfolio.find_one(Portfolio.name == "Sample Climate Risk Portfolio")
    if existing:
        return {
            "message": "Sample portfolio already exists",
            "portfolio_id": str(existing.id)
        }
    
    # Generate sample portfolio
    companies_data = [
        {'name': 'MegaCoal Energy', 'sector': Sector.POWER_GENERATION, 'subsector': 'Coal'},
        {'name': 'SolarWind Power', 'sector': Sector.POWER_GENERATION, 'subsector': 'Renewables'},
        {'name': 'PetroGiant Inc', 'sector': Sector.OIL_GAS, 'subsector': 'Integrated'},
        {'name': 'SteelWorks Global', 'sector': Sector.METALS_MINING, 'subsector': 'Steel'},
        {'name': 'AutoFuture Motors', 'sector': Sector.AUTOMOTIVE, 'subsector': 'ICE Vehicles'},
        {'name': 'ElectricDrive Co', 'sector': Sector.AUTOMOTIVE, 'subsector': 'EV'},
        {'name': 'GlobalAir Airlines', 'sector': Sector.AIRLINES, 'subsector': 'Passenger'},
        {'name': 'GreenBuildings REIT', 'sector': Sector.REAL_ESTATE, 'subsector': 'Commercial'},
    ]
    
    assets = []
    asset_types = [AssetType.BOND, AssetType.LOAN, AssetType.EQUITY]
    
    for i, company_data in enumerate(companies_data):
        for j in range(2):  # 2 assets per company
            asset_type = asset_types[j % len(asset_types)]
            
            # Base PD varies by sector risk
            base_pd_map = {
                Sector.POWER_GENERATION: 0.02 if 'Coal' in company_data['subsector'] else 0.01,
                Sector.OIL_GAS: 0.025,
                Sector.METALS_MINING: 0.03,
                Sector.AUTOMOTIVE: 0.02 if 'ICE' in company_data['subsector'] else 0.015,
                Sector.AIRLINES: 0.04,
                Sector.REAL_ESTATE: 0.015
            }
            base_pd = base_pd_map[company_data['sector']]
            
            # LGD varies by asset type
            lgd_map = {
                AssetType.BOND: 0.45,
                AssetType.LOAN: 0.40,
                AssetType.EQUITY: 0.90
            }
            lgd = lgd_map[asset_type]
            
            # Rating based on PD
            if base_pd < 0.01:
                rating = 'AAA'
            elif base_pd < 0.02:
                rating = 'A'
            elif base_pd < 0.03:
                rating = 'BBB'
            else:
                rating = 'BB'
            
            asset = Asset(
                id=str(uuid.uuid4()),
                asset_type=asset_type,
                company=Company(**company_data),
                exposure=float(np.random.uniform(1e6, 10e6)),
                market_value=float(np.random.uniform(1e6, 10e6)),
                base_pd=base_pd,
                base_lgd=lgd,
                rating=rating,
                maturity_years=int(np.random.randint(3, 10))
            )
            assets.append(asset)
    
    portfolio = Portfolio(
        name="Sample Climate Risk Portfolio",
        description="Diversified portfolio across climate-sensitive sectors for demonstration",
        assets=assets
    )
    await portfolio.insert()
    
    # Also refresh scenario data if not present
    scenario_count = await ScenarioSeries.count()
    if scenario_count == 0:
        await refresh_scenario_data(ScenarioDataRefresh(force=False))
    
    return {
        "message": "Sample portfolio created successfully",
        "portfolio_id": str(portfolio.id),
        "num_assets": len(assets),
        "total_exposure": sum(a.exposure for a in assets)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
