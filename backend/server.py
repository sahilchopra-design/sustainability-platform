from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
import numpy as np

from models import (
    Asset, Company, AssetType, Sector,
    ScenarioResult, Scenario
)
from db.base import get_db
# Use the PG models (portfolios_pg / assets_pg / analysis_runs_pg tables)
from db.models.portfolio_pg import PortfolioPG, AssetPG, AnalysisRunPG
# Scenario series still live in scenario_series table (models_sql)
from db.models_sql import ScenarioSeries as ScenarioSeriesSQL
from sqlalchemy.orm import Session
from risk_engine import RiskEngine, SECTOR_MULTIPLIERS
from services.calculation_engine import ClimateRiskCalculationEngine
from services.engine_integration import assets_to_inputs, engine_results_to_models

# Import v1 scenario routes
from api.v1.routes.scenarios import router as scenarios_router
from api.v1.routes.data_hub import router as data_hub_router
from api.v1.routes.analysis import router as analysis_router
from api.v1.routes.ngfs_v2 import router as ngfs_v2_router
from api.v1.routes.scenario_builder_v2 import router as builder_v2_router
from api.v1.routes.sub_parameter import router as sub_param_router
from api.v1.routes.cbam import router as cbam_router
from api.v1.routes.carbon import router as carbon_router
from api.v1.routes.nature_risk import router as nature_risk_router
from api.v1.routes.stranded_assets import router as stranded_assets_router
from api.v1.routes.real_estate_valuation import router as valuation_router
from api.v1.routes.sustainability import router as sustainability_router
from api.v1.routes.scenario_analysis import router as scenario_router
from api.v1.routes.scenario_analysis import sensitivity_router, whatif_router
from api.auth_pg import router as auth_router
from api.v1.routes.portfolio_pg import router as portfolio_pg_router
from api.v1.routes.portfolio_analytics import router as portfolio_analytics_router
from api.v1.routes.universal_exports import router as exports_router
from api.v1.routes.scheduled_reports import router as scheduled_reports_router
from api.v1.routes.re_clvar import router as re_clvar_router
from api.v1.routes.ecl_climate import router as ecl_climate_router
from api.v1.routes.pcaf_regulatory import router as pcaf_regulatory_router
from api.v1.routes.supply_chain import router as supply_chain_router
from api.v1.routes.sector_assessments import router as sector_assessments_router
from api.v1.routes.unified_valuation import router as unified_valuation_router
from api.v1.routes.csrd_reports import router as csrd_router
from api.v1.routes.portfolio_reporting import router as portfolio_reporting_router
from api.v1.routes.portfolio_health import router as portfolio_health_router
from api.v1.routes.project_finance import router as project_finance_router
from api.v1.routes.glidepath import router as glidepath_router
from api.v1.routes.sector_calculators import router as sector_calculators_router
from api.v1.routes.mas_regulatory import router as mas_regulatory_router
from api.v1.routes.peer_benchmark import router as peer_benchmark_router
from api.v1.routes.analyst_portfolios import router as analyst_portfolios_router
from api.v1.routes.company_profiles import router as company_profiles_router
from api.v1.routes.entity_data import router as entity_data_router
from api.v1.routes.data_intake import router as data_intake_router
from api.v1.routes.facilitated_emissions import router as facilitated_emissions_router
from api.v1.routes.engagement import router as engagement_router
from api.v1.routes.just_transition import router as just_transition_router
from api.v1.routes.green_hydrogen import router as green_hydrogen_router
from api.v1.routes.insurance import router as insurance_router
from api.v1.routes.agriculture import router as agriculture_router
from api.v1.routes.mining import router as mining_router
from api.v1.routes.parameter_governance import router as parameter_governance_router
from api.v1.routes.monte_carlo import router as monte_carlo_router
from api.v1.routes.asia_regulatory import router as asia_regulatory_router
from api.v1.routes.china_trade import router as china_trade_router
from api.v1.routes.audit_log import router as audit_log_router
from api.v1.routes.organisations import router as organisations_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize PostgreSQL tables
    try:
        from db.base import init_db as init_postgres_db
        init_postgres_db()
    except Exception as e:
        print(f"[WARN] PostgreSQL init failed: {e}")
    yield


app = FastAPI(
    title="Climate Credit Risk Intelligence Platform",
    description="Portfolio Scenario Analysis with NGFS Climate Data",
    version="1.0.0",
    lifespan=lifespan
)

# Include Scenario Analysis routes (must be BEFORE scenarios_router to avoid route conflicts)
# These routes have specific paths like /dashboard, /properties that would otherwise
# be matched by the {scenario_id} catch-all pattern in scenarios_router
app.include_router(scenario_router)
app.include_router(sensitivity_router)
app.include_router(whatif_router)
# Include scenario builder routes
app.include_router(scenarios_router)
# Include data hub routes
app.include_router(data_hub_router)
# Include analysis routes
app.include_router(analysis_router)
# Include auth routes (PostgreSQL)
app.include_router(auth_router)
# Include PG portfolio routes
app.include_router(portfolio_pg_router)
# Include NGFS v2 routes
app.include_router(ngfs_v2_router)
# Include scenario builder v2 routes
app.include_router(builder_v2_router)
# Include sub-parameter analysis routes
app.include_router(sub_param_router)
# Include CBAM routes
app.include_router(cbam_router)
# Include Carbon Credits routes
app.include_router(carbon_router)
# Include Nature Risk routes
app.include_router(nature_risk_router)
# Include Stranded Assets routes
app.include_router(stranded_assets_router)
# Include Real Estate Valuation routes
app.include_router(valuation_router)
# Include Sustainability Frameworks routes
app.include_router(sustainability_router)
# Include Portfolio Analytics routes
app.include_router(portfolio_analytics_router)
# Include Universal Export routes
app.include_router(exports_router)
# Include Scheduled Reports routes
app.include_router(scheduled_reports_router)
# Include Real Estate CLVaR and CRREM routes
app.include_router(re_clvar_router)
# Include IFRS 9 ECL Climate routes
app.include_router(ecl_climate_router)
# Include PCAF / SFDR / EU Taxonomy routes
app.include_router(pcaf_regulatory_router)
# Include Supply Chain Scope 3 routes
app.include_router(supply_chain_router)
# Include Sector ESG Assessment routes
app.include_router(sector_assessments_router)
# Include Unified Valuation Engine routes
app.include_router(unified_valuation_router)
# Include CSRD PDF extraction + ESRS KPI query routes
app.include_router(csrd_router)
# Include Portfolio Reporting routes (PCAF, SFDR PAI, ECL stress, EU Taxonomy, Paris alignment)
app.include_router(portfolio_reporting_router)
# Include Portfolio Health (Sustainability Pulse scores + alert engine)
app.include_router(portfolio_health_router)
# Include Project Finance (DSCR / LLCR / IRR / PPA engine)
app.include_router(project_finance_router)
# Include Glidepath Tracker (NZBA / CRREM sector glidepath)
app.include_router(glidepath_router)
# Include Sector Calculators (Shipping CII / Steel BF-BOF)
app.include_router(sector_calculators_router)
# Include MAS Regulatory (ERM / Notice 637 / SGT / SLGS)
app.include_router(mas_regulatory_router)
# Include Peer Benchmark Gap Assessment (TCFD / ISSB / ESRS / PCAF peer matrix)
app.include_router(peer_benchmark_router)
app.include_router(analyst_portfolios_router)  # 10 analyst demo portfolios + gap assessment
app.include_router(company_profiles_router)    # Company profiles — identity, prudential, Pillar 3
app.include_router(entity_data_router)         # CSRD Entity Data Bridge — real data to module inputs
app.include_router(data_intake_router)         # Category C — Client Proprietary Data Intake
app.include_router(facilitated_emissions_router)  # Category D — PCAF Capital Markets Facilitated Emissions
app.include_router(engagement_router)             # Category D — Client Engagement Tracker (PRI AO2.0 / CA100+)
app.include_router(just_transition_router)        # Category D — Just Transition + ETM (ILO / ADB ETM Framework)
app.include_router(green_hydrogen_router)         # Category D — Green Hydrogen LCOH + Carbon Intensity (IRENA / IEA / RFNBO)
app.include_router(insurance_router)              # P1 — Insurance Climate Risk (CAT / Solvency II / reserve adequacy)
app.include_router(agriculture_router)            # P1 — Agriculture Risk (EUDR / crop yield / soil carbon / water stress)
app.include_router(mining_router)                 # P1 — Mining/Extractives (GISTM tailings / closure cost / critical minerals)
app.include_router(parameter_governance_router)   # P2 — Parameter Governance (versioned calc params + approval workflow)
app.include_router(monte_carlo_router)            # P2 — Monte Carlo Simulation (P5/P25/P50/P75/P95 portfolio risk distribution)
app.include_router(asia_regulatory_router)        # Asia Regulatory — BRSR / HKMA / BoJ / ASEAN Taxonomy v3 / PBoC / CBI
app.include_router(china_trade_router)            # China Trade Platform — Exporter / CBAM / Supplier / ESG / ETS / Corridors / Marketplace
app.include_router(audit_log_router)              # Audit Log — admin read-only query endpoints
app.include_router(organisations_router)          # Organisations — multi-tenant CRUD + member management

# Audit middleware — append-only log for all mutating requests (POST/PUT/PATCH/DELETE)
from middleware.audit_middleware import AuditMiddleware
app.add_middleware(AuditMiddleware)

# CORS — must be added AFTER AuditMiddleware so CORS headers reach the client
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


# Helper functions for SQLAlchemy → dict conversion
def _sql_asset_to_dict(a: AssetPG) -> dict:
    return {
        "id": a.id,
        "asset_type": a.asset_type.value if hasattr(a.asset_type, 'value') else a.asset_type,
        "company": {
            "name": a.company_name,
            "sector": a.company_sector.value if hasattr(a.company_sector, 'value') else a.company_sector,
            "subsector": a.company_subsector,
        },
        "exposure": a.exposure,
        "market_value": a.market_value,
        "base_pd": a.base_pd,
        "base_lgd": a.base_lgd,
        "rating": a.rating,
        "maturity_years": a.maturity_years,
    }



# Health check
@app.get("/api/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# Portfolio endpoints
@app.get("/api/portfolios")
def get_portfolios(db: Session = Depends(get_db)):
    """Get all portfolios"""
    portfolios = db.query(PortfolioPG).order_by(PortfolioPG.created_at.desc()).limit(100).all()
    return {
        "portfolios": [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "num_assets": len(p.assets),
                "total_exposure": sum(a.exposure for a in p.assets),
                "created_at": p.created_at.isoformat(),
                "updated_at": p.updated_at.isoformat(),
            }
            for p in portfolios
        ]
    }


@app.post("/api/portfolios")
def create_portfolio(data: PortfolioCreate, db: Session = Depends(get_db)):
    """Create a new portfolio"""
    p = PortfolioPG(
        id=str(uuid.uuid4()),
        name=data.name,
        description=data.description,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return {
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "assets": [],
        "created_at": p.created_at.isoformat(),
    }


@app.get("/api/portfolios/{portfolio_id}")
def get_portfolio(portfolio_id: str, db: Session = Depends(get_db)):
    """Get portfolio details"""
    p = db.query(PortfolioPG).filter(PortfolioPG.id == portfolio_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return {
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "assets": [_sql_asset_to_dict(a) for a in p.assets],
        "total_exposure": sum(a.exposure for a in p.assets),
        "created_at": p.created_at.isoformat(),
        "updated_at": p.updated_at.isoformat(),
    }


@app.put("/api/portfolios/{portfolio_id}")
def update_portfolio(portfolio_id: str, data: PortfolioUpdate, db: Session = Depends(get_db)):
    """Update portfolio"""
    p = db.query(PortfolioPG).filter(PortfolioPG.id == portfolio_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if data.name is not None:
        p.name = data.name
    if data.description is not None:
        p.description = data.description
    if data.assets is not None:
        # Replace all assets: delete existing, re-insert from request
        for existing in list(p.assets):
            db.delete(existing)
        db.flush()
        for asset in data.assets:
            db.add(AssetPG(
                id=asset.id or str(uuid.uuid4()),
                portfolio_id=portfolio_id,
                asset_type=asset.asset_type,
                company_name=asset.company.name,
                company_sector=asset.company.sector,
                company_subsector=asset.company.subsector,
                exposure=asset.exposure,
                market_value=asset.market_value,
                base_pd=asset.base_pd,
                base_lgd=asset.base_lgd,
                rating=asset.rating,
                maturity_years=asset.maturity_years,
            ))
    p.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(p)
    return {
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "assets": [_sql_asset_to_dict(a) for a in p.assets],
        "updated_at": p.updated_at.isoformat(),
    }


@app.delete("/api/portfolios/{portfolio_id}")
def delete_portfolio(portfolio_id: str, db: Session = Depends(get_db)):
    """Delete portfolio"""
    p = db.query(PortfolioPG).filter(PortfolioPG.id == portfolio_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    db.delete(p)
    db.commit()
    return {"message": "Portfolio deleted", "id": portfolio_id}


@app.post("/api/portfolios/{portfolio_id}/assets")
def add_asset_to_portfolio(portfolio_id: str, data: AssetAdd, db: Session = Depends(get_db)):
    """Add asset to portfolio"""
    p = db.query(PortfolioPG).filter(PortfolioPG.id == portfolio_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    asset = data.asset
    sql_asset = AssetPG(
        id=asset.id if asset.id else str(uuid.uuid4()),
        portfolio_id=portfolio_id,
        asset_type=asset.asset_type,
        company_name=asset.company.name,
        company_sector=asset.company.sector,
        company_subsector=asset.company.subsector,
        exposure=asset.exposure,
        market_value=asset.market_value,
        base_pd=asset.base_pd,
        base_lgd=asset.base_lgd,
        rating=asset.rating,
        maturity_years=asset.maturity_years,
    )
    db.add(sql_asset)
    p.updated_at = datetime.utcnow()
    db.commit()
    return {
        "message": "Asset added",
        "asset": _sql_asset_to_dict(sql_asset),
        "portfolio_id": portfolio_id,
    }


@app.delete("/api/portfolios/{portfolio_id}/assets/{asset_id}")
def remove_asset_from_portfolio(portfolio_id: str, asset_id: str, db: Session = Depends(get_db)):
    """Remove asset from portfolio"""
    p = db.query(PortfolioPG).filter(PortfolioPG.id == portfolio_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    asset = db.query(AssetPG).filter(
        AssetPG.id == asset_id, AssetPG.portfolio_id == portfolio_id
    ).first()
    if asset:
        db.delete(asset)
    p.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Asset removed", "asset_id": asset_id}


# Scenario data endpoints
@app.get("/api/scenario-data")
def get_scenario_data(db: Session = Depends(get_db)):
    """Get overview of available scenario data"""
    from sqlalchemy import distinct
    scenarios = [r[0] for r in db.query(distinct(ScenarioSeriesSQL.scenario)).all()]
    variables = [r[0] for r in db.query(distinct(ScenarioSeriesSQL.variable)).all()]
    regions = [r[0] for r in db.query(distinct(ScenarioSeriesSQL.region)).all()]
    years = sorted([r[0] for r in db.query(distinct(ScenarioSeriesSQL.year)).all()])
    total = db.query(ScenarioSeriesSQL).count()
    return {
        "scenarios": scenarios,
        "variables": variables,
        "regions": regions,
        "years": years,
        "total_records": total,
    }


@app.post("/api/scenario-data/refresh")
def refresh_scenario_data(data: ScenarioDataRefresh, db: Session = Depends(get_db)):
    """Refresh scenario data from NGFS sources"""
    from datetime import datetime as dt
    existing_count = db.query(ScenarioSeriesSQL).count()
    if existing_count > 0 and not data.force:
        return {
            "message": "Scenario data already exists. Use force=true to refresh.",
            "existing_records": existing_count,
        }

    SCENARIOS = ['Orderly', 'Disorderly', 'Hot house world']
    HORIZONS = [2030, 2040, 2050]
    scenario_profiles = {
        'Orderly': {
            'carbon_price_mult': [2.0, 3.5, 5.0],
            'gdp_growth': [0.98, 0.95, 0.93],
            'emissions_mult': [0.7, 0.4, 0.2],
            'coal_mult': [0.5, 0.2, 0.05],
            'temp_increase': [1.6, 1.7, 1.8],
        },
        'Disorderly': {
            'carbon_price_mult': [1.5, 4.0, 6.0],
            'gdp_growth': [0.95, 0.90, 0.85],
            'emissions_mult': [0.8, 0.5, 0.25],
            'coal_mult': [0.7, 0.3, 0.1],
            'temp_increase': [1.8, 2.0, 2.1],
        },
        'Hot house world': {
            'carbon_price_mult': [1.0, 1.2, 1.3],
            'gdp_growth': [1.0, 0.92, 0.80],
            'emissions_mult': [1.0, 1.1, 1.2],
            'coal_mult': [0.95, 0.85, 0.75],
            'temp_increase': [2.5, 3.2, 4.0],
        },
    }
    regions = ['World', 'United States', 'European Union', 'China']
    model_name = 'NGFS_Phase5_Synthetic'
    source_version = f"NGFS_Phase5_{dt.utcnow().strftime('%Y%m%d')}"
    baseline = {
        'carbon_price': 30,
        'gdp': 100,
        'emissions': 50,
        'temperature': 1.2,
    }

    if data.force:
        db.query(ScenarioSeriesSQL).delete()
        db.commit()

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
                records.extend([
                    ScenarioSeriesSQL(
                        year=year, scenario=scenario, model=model_name, region=region,
                        variable='Price|Carbon', unit='USD/tCO2',
                        value=baseline['carbon_price'] * profile['carbon_price_mult'][idx] * region_mult,
                        source_version=source_version,
                    ),
                    ScenarioSeriesSQL(
                        year=year, scenario=scenario, model=model_name, region=region,
                        variable='GDP|PPP', unit='Index (2020=100)',
                        value=baseline['gdp'] * profile['gdp_growth'][idx] * region_mult,
                        source_version=source_version,
                    ),
                    ScenarioSeriesSQL(
                        year=year, scenario=scenario, model=model_name, region=region,
                        variable='Emissions|CO2', unit='GtCO2',
                        value=baseline['emissions'] * profile['emissions_mult'][idx] * region_mult,
                        source_version=source_version,
                    ),
                    ScenarioSeriesSQL(
                        year=year, scenario=scenario, model=model_name, region=region,
                        variable='Temperature|Global Mean', unit='degC',
                        value=baseline['temperature'] + profile['temp_increase'][idx],
                        source_version=source_version,
                    ),
                ])

    db.bulk_save_objects(records)
    db.commit()
    return {
        "message": "Scenario data refreshed successfully",
        "records_inserted": len(records),
        "source_version": source_version,
    }


# Analysis endpoints
@app.post("/api/analysis/run")
def run_analysis(data: AnalysisRequest, db: Session = Depends(get_db)):
    """Run scenario analysis on a portfolio using the calculation engine"""
    p = db.query(PortfolioPG).filter(PortfolioPG.id == data.portfolio_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if len(p.assets) == 0:
        raise HTTPException(status_code=400, detail="Portfolio has no assets")

    # Convert SQL assets to Pydantic Asset objects for the calculation engine
    pydantic_assets = [
        Asset(
            id=a.id,
            asset_type=a.asset_type,
            company=Company(
                name=a.company_name,
                sector=a.company_sector,
                subsector=a.company_subsector,
            ),
            exposure=a.exposure,
            market_value=a.market_value,
            base_pd=a.base_pd,
            base_lgd=a.base_lgd,
            rating=a.rating,
            maturity_years=a.maturity_years,
        )
        for a in p.assets
    ]

    asset_inputs = assets_to_inputs(pydantic_assets)
    engine = ClimateRiskCalculationEngine(
        n_simulations=10000,
        correlation=0.3,
        var_method='monte_carlo',
        base_return=0.05,
        random_seed=42,
    )
    engine_results = engine.calculate_multiple_scenarios(
        assets=asset_inputs,
        scenarios=data.scenarios,
        horizons=data.horizons,
        include_sector_breakdown=False,
    )
    results = engine_results_to_models(engine_results)

    results_json = [r.model_dump() for r in results]
    analysis = AnalysisRunPG(
        id=str(uuid.uuid4()),
        portfolio_id=p.id,
        portfolio_name=p.name,
        scenarios=data.scenarios,
        horizons=data.horizons,
        results=results_json,
        status="completed",
        completed_at=datetime.utcnow(),
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return {
        "id": analysis.id,
        "portfolio_id": p.id,
        "portfolio_name": p.name,
        "scenarios": data.scenarios,
        "horizons": data.horizons,
        "results": results_json,
        "status": "completed",
        "created_at": analysis.created_at.isoformat(),
    }


@app.get("/api/analysis/runs")
def get_analysis_runs(portfolio_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Get all analysis runs, optionally filtered by portfolio"""
    q = db.query(AnalysisRunPG).order_by(AnalysisRunPG.created_at.desc())
    if portfolio_id:
        q = q.filter(AnalysisRunPG.portfolio_id == portfolio_id)
    runs = q.limit(100).all()
    return {
        "runs": [
            {
                "id": r.id,
                "portfolio_id": r.portfolio_id,
                "portfolio_name": r.portfolio_name,
                "scenarios": r.scenarios,
                "horizons": r.horizons,
                "status": r.status,
                "created_at": r.created_at.isoformat(),
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            }
            for r in runs
        ]
    }


@app.get("/api/analysis/runs/{run_id}")
def get_analysis_run(run_id: str, db: Session = Depends(get_db)):
    """Get detailed analysis run results"""
    run = db.query(AnalysisRunPG).filter(AnalysisRunPG.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Analysis run not found")
    return {
        "id": run.id,
        "portfolio_id": run.portfolio_id,
        "portfolio_name": run.portfolio_name,
        "scenarios": run.scenarios,
        "horizons": run.horizons,
        "results": run.results or [],
        "status": run.status,
        "created_at": run.created_at.isoformat(),
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "error_message": run.error_message,
    }


@app.delete("/api/analysis/runs/{run_id}")
def delete_analysis_run(run_id: str, db: Session = Depends(get_db)):
    """Delete analysis run"""
    run = db.query(AnalysisRunPG).filter(AnalysisRunPG.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Analysis run not found")
    db.delete(run)
    db.commit()
    return {"message": "Analysis run deleted", "id": run_id}


# Sample data generation
@app.post("/api/sample-data/generate")
def generate_sample_data(db: Session = Depends(get_db)):
    """Generate sample portfolio for demo purposes"""
    existing = db.query(PortfolioPG).filter(
        PortfolioPG.name == "Sample Climate Risk Portfolio"
    ).first()
    if existing:
        return {"message": "Sample portfolio already exists", "portfolio_id": existing.id}

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
    asset_types = [AssetType.BOND, AssetType.LOAN, AssetType.EQUITY]

    portfolio_id = str(uuid.uuid4())
    p = PortfolioPG(
        id=portfolio_id,
        name="Sample Climate Risk Portfolio",
        description="Diversified portfolio across climate-sensitive sectors for demonstration",
    )
    db.add(p)
    db.flush()

    sql_assets = []
    total_exposure = 0.0
    for company_data in companies_data:
        for j in range(2):
            asset_type = asset_types[j % len(asset_types)]
            base_pd_map = {
                Sector.POWER_GENERATION: 0.02 if 'Coal' in company_data['subsector'] else 0.01,
                Sector.OIL_GAS: 0.025,
                Sector.METALS_MINING: 0.03,
                Sector.AUTOMOTIVE: 0.02 if 'ICE' in company_data['subsector'] else 0.015,
                Sector.AIRLINES: 0.04,
                Sector.REAL_ESTATE: 0.015,
            }
            base_pd = base_pd_map[company_data['sector']]
            lgd_map = {AssetType.BOND: 0.45, AssetType.LOAN: 0.40, AssetType.EQUITY: 0.90}
            lgd = lgd_map[asset_type]
            if base_pd < 0.01:
                rating = 'AAA'
            elif base_pd < 0.02:
                rating = 'A'
            elif base_pd < 0.03:
                rating = 'BBB'
            else:
                rating = 'BB'
            exposure = float(np.random.uniform(1e6, 10e6))
            total_exposure += exposure
            a = AssetPG(
                id=str(uuid.uuid4()),
                portfolio_id=portfolio_id,
                asset_type=asset_type,
                company_name=company_data['name'],
                company_sector=company_data['sector'],
                company_subsector=company_data['subsector'],
                exposure=exposure,
                market_value=float(np.random.uniform(1e6, 10e6)),
                base_pd=base_pd,
                base_lgd=lgd,
                rating=rating,
                maturity_years=int(np.random.randint(3, 10)),
            )
            db.add(a)
            sql_assets.append(a)

    scenario_count = db.query(ScenarioSeriesSQL).count()
    db.commit()

    if scenario_count == 0:
        refresh_scenario_data(ScenarioDataRefresh(force=False), db)

    return {
        "message": "Sample portfolio created successfully",
        "portfolio_id": portfolio_id,
        "num_assets": len(sql_assets),
        "total_exposure": total_exposure,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
