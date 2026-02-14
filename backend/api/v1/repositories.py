"""Repository layer for database operations"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from datetime import datetime

from db.models_sql import (
    Portfolio, Asset, ScenarioSeries, AnalysisRun, ScenarioResult,
    AssetTypeEnum, SectorEnum
)


class PortfolioRepository:
    """Repository for Portfolio operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self, skip: int = 0, limit: int = 50, sort_by: Optional[str] = None) -> tuple[List[Portfolio], int]:
        """Get all portfolios with pagination"""
        query = self.db.query(Portfolio)
        total = query.count()
        
        if sort_by:
            order_col = getattr(Portfolio, sort_by, Portfolio.created_at)
            query = query.order_by(desc(order_col))
        else:
            query = query.order_by(desc(Portfolio.created_at))
        
        portfolios = query.offset(skip).limit(limit).all()
        return portfolios, total
    
    def get_by_id(self, portfolio_id: str) -> Optional[Portfolio]:
        """Get portfolio by ID"""
        return self.db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    
    def create(self, name: str, description: Optional[str] = None) -> Portfolio:
        """Create new portfolio"""
        portfolio = Portfolio(name=name, description=description)
        self.db.add(portfolio)
        self.db.commit()
        self.db.refresh(portfolio)
        return portfolio
    
    def update(self, portfolio_id: str, data: Dict[str, Any]) -> Optional[Portfolio]:
        """Update portfolio"""
        portfolio = self.get_by_id(portfolio_id)
        if not portfolio:
            return None
        
        for key, value in data.items():
            if hasattr(portfolio, key) and value is not None:
                setattr(portfolio, key, value)
        
        portfolio.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(portfolio)
        return portfolio
    
    def delete(self, portfolio_id: str) -> bool:
        """Delete portfolio"""
        portfolio = self.get_by_id(portfolio_id)
        if not portfolio:
            return False
        
        self.db.delete(portfolio)
        self.db.commit()
        return True
    
    def get_holdings(self, portfolio_id: str) -> List[Asset]:
        """Get all holdings/assets for a portfolio"""
        return self.db.query(Asset).filter(Asset.portfolio_id == portfolio_id).all()
    
    def add_holding(self, portfolio_id: str, asset_data: Dict[str, Any]) -> Asset:
        """Add holding to portfolio"""
        asset = Asset(portfolio_id=portfolio_id, **asset_data)
        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)
        return asset
    
    def get_portfolio_metrics(self, portfolio_id: str) -> Dict[str, Any]:
        """Calculate portfolio metrics"""
        assets = self.get_holdings(portfolio_id)
        
        if not assets:
            return {
                "total_exposure": 0,
                "num_holdings": 0,
                "weighted_avg_pd": 0,
                "sector_distribution": {}
            }
        
        total_exposure = sum(a.exposure for a in assets)
        weighted_pd = sum(a.exposure * a.base_pd for a in assets) / total_exposure if total_exposure > 0 else 0
        
        # Sector distribution
        sector_dist = {}
        for asset in assets:
            sector = asset.company_sector.value
            if sector not in sector_dist:
                sector_dist[sector] = 0
            sector_dist[sector] += asset.exposure
        
        return {
            "total_exposure": total_exposure,
            "num_holdings": len(assets),
            "weighted_avg_pd": weighted_pd,
            "sector_distribution": sector_dist
        }


class ScenarioRepository:
    """Repository for Scenario operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_scenarios(self) -> List[str]:
        """Get list of unique scenarios"""
        result = self.db.query(ScenarioSeries.scenario).distinct().all()
        return [row[0] for row in result]
    
    def get_scenario_data(self, scenario: str, variable: str, region: str, year: int) -> Optional[ScenarioSeries]:
        """Get specific scenario data point"""
        return self.db.query(ScenarioSeries).filter(
            ScenarioSeries.scenario == scenario,
            ScenarioSeries.variable == variable,
            ScenarioSeries.region == region,
            ScenarioSeries.year == year
        ).first()
    
    def bulk_insert_scenario_data(self, data: List[Dict[str, Any]]) -> int:
        """Bulk insert scenario data"""
        series_objects = [ScenarioSeries(**item) for item in data]
        self.db.bulk_save_objects(series_objects)
        self.db.commit()
        return len(series_objects)
    
    def get_scenario_summary(self) -> Dict[str, Any]:
        """Get scenario data summary"""
        scenarios = self.db.query(ScenarioSeries.scenario).distinct().all()
        variables = self.db.query(ScenarioSeries.variable).distinct().all()
        regions = self.db.query(ScenarioSeries.region).distinct().all()
        years = self.db.query(ScenarioSeries.year).distinct().order_by(ScenarioSeries.year).all()
        
        return {
            "scenarios": [s[0] for s in scenarios],
            "variables": [v[0] for v in variables],
            "regions": [r[0] for r in regions],
            "years": [y[0] for y in years],
            "total_records": self.db.query(ScenarioSeries).count()
        }


class AnalysisRepository:
    """Repository for Analysis operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_analysis_run(self, portfolio_id: str, portfolio_name: str, scenarios: List[str], horizons: List[int]) -> AnalysisRun:
        """Create new analysis run"""
        analysis = AnalysisRun(
            portfolio_id=portfolio_id,
            portfolio_name=portfolio_name,
            scenarios=scenarios,
            horizons=horizons,
            status="pending"
        )
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        return analysis
    
    def update_analysis_status(self, run_id: str, status: str, error_message: Optional[str] = None) -> Optional[AnalysisRun]:
        """Update analysis run status"""
        analysis = self.db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
        if not analysis:
            return None
        
        analysis.status = status
        if status == "completed":
            analysis.completed_at = datetime.utcnow()
        if error_message:
            analysis.error_message = error_message
        
        self.db.commit()
        self.db.refresh(analysis)
        return analysis
    
    def add_results(self, run_id: str, results: List[Dict[str, Any]]) -> List[ScenarioResult]:
        """Add results to analysis run"""
        result_objects = []
        for result_data in results:
            result = ScenarioResult(analysis_run_id=run_id, **result_data)
            result_objects.append(result)
            self.db.add(result)
        
        self.db.commit()
        for result in result_objects:
            self.db.refresh(result)
        
        return result_objects
    
    def get_analysis_run(self, run_id: str) -> Optional[AnalysisRun]:
        """Get analysis run by ID"""
        return self.db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
    
    def get_portfolio_runs(self, portfolio_id: str, skip: int = 0, limit: int = 50) -> tuple[List[AnalysisRun], int]:
        """Get all analysis runs for a portfolio"""
        query = self.db.query(AnalysisRun).filter(AnalysisRun.portfolio_id == portfolio_id)
        total = query.count()
        runs = query.order_by(desc(AnalysisRun.created_at)).offset(skip).limit(limit).all()
        return runs, total
    
    def get_results(self, run_id: str) -> List[ScenarioResult]:
        """Get all results for an analysis run"""
        return self.db.query(ScenarioResult).filter(ScenarioResult.analysis_run_id == run_id).all()
