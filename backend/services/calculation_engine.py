"""Main Calculation Engine - Orchestrates all calculators for scenario analysis"""
import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

from services.pd_calculator import PDAdjustmentCalculator, PDResult
from services.lgd_calculator import LGDAdjustmentCalculator, LGDResult
from services.var_calculator import VaRCalculator, VaRResult
from services.portfolio_metrics import PortfolioMetricsCalculator, PortfolioMetrics, RatingMigration


@dataclass
class AssetInput:
    """Input data for a single asset"""
    id: str
    exposure: float
    baseline_pd: float
    baseline_lgd: float
    sector: str
    country: Optional[str] = None
    emissions_intensity: Optional[float] = None
    emissions_trend: str = 'Stable'
    transition_plan_score: Optional[int] = None
    physical_risk_score: Optional[int] = None
    collateral_type: str = 'Unsecured'


@dataclass
class ScenarioHorizonResult:
    """Results for a single scenario-horizon combination"""
    scenario: str
    horizon: int
    
    # Portfolio-level metrics
    expected_loss: float
    expected_loss_pct: float
    var_95: float
    var_99: float
    expected_shortfall_95: float
    expected_shortfall_99: float
    risk_adjusted_return: float
    
    # PD metrics
    weighted_avg_pd: float
    avg_pd_change_pct: float
    
    # Concentration
    sector_hhi: float
    geographic_hhi: float
    
    # Rating migrations
    rating_migrations: Dict[str, int]
    
    # Total exposure
    total_exposure: float
    
    # Sector breakdown (optional)
    sector_breakdown: Optional[Dict[str, Dict[str, float]]] = None


class ClimateRiskCalculationEngine:
    """
    High-performance orchestrator for climate credit risk calculations.
    
    Workflow:
    1. Takes portfolio assets + scenario parameters
    2. Calculates climate-adjusted PD/LGD for each asset
    3. Calculates VaR for the portfolio
    4. Aggregates to portfolio-level metrics
    5. Returns structured results
    """
    
    def __init__(
        self,
        n_simulations: int = 10000,
        correlation: float = 0.3,
        var_method: str = 'monte_carlo',
        base_return: float = 0.05,
        random_seed: int = 42
    ):
        """
        Initialize calculation engine.
        
        Args:
            n_simulations: Number of Monte Carlo simulations for VaR
            correlation: Asset correlation factor (0-1)
            var_method: 'monte_carlo' or 'parametric'
            base_return: Baseline portfolio return (e.g., 5%)
            random_seed: Random seed for reproducibility
        """
        self.n_simulations = n_simulations
        self.correlation = correlation
        self.var_method = var_method
        self.random_seed = random_seed
        
        self.var_calculator = VaRCalculator(
            n_simulations=n_simulations,
            random_seed=random_seed
        )
        self.portfolio_calculator = PortfolioMetricsCalculator(
            base_return=base_return
        )
    
    def calculate_scenario(
        self,
        assets: List[AssetInput],
        scenario: str,
        horizon: int,
        include_sector_breakdown: bool = False
    ) -> ScenarioHorizonResult:
        """
        Calculate risk metrics for a single scenario-horizon combination.
        
        Args:
            assets: List of portfolio assets
            scenario: Scenario name (e.g., 'Orderly', 'Disorderly', 'Hot house world')
            horizon: Time horizon (e.g., 2030, 2040, 2050)
            include_sector_breakdown: Whether to include sector-level breakdown
            
        Returns:
            ScenarioHorizonResult with all calculated metrics
        """
        n_assets = len(assets)
        
        if n_assets == 0:
            raise ValueError("Portfolio has no assets")
        
        # Initialize calculators for this scenario
        pd_calc = PDAdjustmentCalculator(scenario=scenario)
        lgd_calc = LGDAdjustmentCalculator(scenario=scenario)
        
        # Prepare arrays for batch processing
        exposures = np.array([a.exposure for a in assets])
        baseline_pds = np.array([a.baseline_pd for a in assets])
        baseline_lgds = np.array([a.baseline_lgd for a in assets])
        sectors = np.array([a.sector for a in assets])
        countries = np.array([a.country or 'Unknown' for a in assets])
        
        # Calculate adjusted PDs
        adjusted_pds = np.zeros(n_assets)
        for i, asset in enumerate(assets):
            pd_result = pd_calc.calculate(
                baseline_pd=asset.baseline_pd,
                sector=asset.sector,
                emissions_intensity=asset.emissions_intensity,
                emissions_trend=asset.emissions_trend,
                transition_plan_score=asset.transition_plan_score,
                physical_risk_score=asset.physical_risk_score,
                time_horizon=horizon
            )
            adjusted_pds[i] = pd_result.adjusted_pd
        
        # Calculate adjusted LGDs
        adjusted_lgds = np.zeros(n_assets)
        for i, asset in enumerate(assets):
            lgd_result = lgd_calc.calculate(
                baseline_lgd=asset.baseline_lgd,
                sector=asset.sector,
                collateral_type=asset.collateral_type,
                physical_risk_score=asset.physical_risk_score,
                time_horizon=horizon
            )
            adjusted_lgds[i] = lgd_result.adjusted_lgd
        
        # Calculate VaR
        var_result = self.var_calculator.calculate_batch(
            exposures=exposures,
            pds=adjusted_pds,
            lgds=adjusted_lgds,
            method=self.var_method,
            correlation=self.correlation
        )
        
        # Calculate portfolio-level metrics
        portfolio_metrics = self.portfolio_calculator.calculate(
            exposures=exposures,
            baseline_pds=baseline_pds,
            adjusted_pds=adjusted_pds,
            lgds=adjusted_lgds,
            sectors=sectors,
            countries=countries,
            var_95=var_result.var_95,
            var_99=var_result.var_99,
            es_95=var_result.expected_shortfall_95,
            es_99=var_result.expected_shortfall_99
        )
        
        # Optional sector breakdown
        sector_breakdown = None
        if include_sector_breakdown:
            sector_breakdown = self.portfolio_calculator.calculate_sector_breakdown(
                exposures=exposures,
                adjusted_pds=adjusted_pds,
                lgds=adjusted_lgds,
                sectors=sectors
            )
        
        return ScenarioHorizonResult(
            scenario=scenario,
            horizon=horizon,
            expected_loss=portfolio_metrics.expected_loss,
            expected_loss_pct=portfolio_metrics.expected_loss_pct,
            var_95=portfolio_metrics.var_95,
            var_99=portfolio_metrics.var_99,
            expected_shortfall_95=portfolio_metrics.expected_shortfall_95,
            expected_shortfall_99=portfolio_metrics.expected_shortfall_99,
            risk_adjusted_return=portfolio_metrics.risk_adjusted_return,
            weighted_avg_pd=portfolio_metrics.weighted_avg_pd,
            avg_pd_change_pct=portfolio_metrics.avg_pd_change_pct,
            sector_hhi=portfolio_metrics.sector_hhi,
            geographic_hhi=portfolio_metrics.geographic_hhi,
            rating_migrations={
                'upgrades': portfolio_metrics.rating_migrations.upgrades,
                'downgrades': portfolio_metrics.rating_migrations.downgrades,
                'stable': portfolio_metrics.rating_migrations.stable
            },
            total_exposure=portfolio_metrics.total_exposure,
            sector_breakdown=sector_breakdown
        )
    
    def calculate_multiple_scenarios(
        self,
        assets: List[AssetInput],
        scenarios: List[str],
        horizons: List[int],
        include_sector_breakdown: bool = False
    ) -> List[ScenarioHorizonResult]:
        """
        Calculate risk metrics for multiple scenario-horizon combinations.
        
        Args:
            assets: List of portfolio assets
            scenarios: List of scenario names
            horizons: List of time horizons
            include_sector_breakdown: Whether to include sector breakdown
            
        Returns:
            List of ScenarioHorizonResult objects
        """
        results = []
        
        for scenario in scenarios:
            for horizon in horizons:
                result = self.calculate_scenario(
                    assets=assets,
                    scenario=scenario,
                    horizon=horizon,
                    include_sector_breakdown=include_sector_breakdown
                )
                results.append(result)
        
        return results
