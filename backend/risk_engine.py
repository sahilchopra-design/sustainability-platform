"""Risk calculation engine - ported from POC"""
import numpy as np
from typing import List, Dict
from models import Asset, ScenarioResult, RatingMigration, Scenario


SECTOR_MULTIPLIERS = {
    'Orderly': {
        2030: {'Power Generation': 1.2, 'Oil & Gas': 1.3, 'Metals & Mining': 1.1,
               'Automotive': 1.15, 'Airlines': 1.25, 'Real Estate': 1.05},
        2040: {'Power Generation': 1.4, 'Oil & Gas': 1.6, 'Metals & Mining': 1.2,
               'Automotive': 1.3, 'Airlines': 1.5, 'Real Estate': 1.1},
        2050: {'Power Generation': 1.6, 'Oil & Gas': 2.0, 'Metals & Mining': 1.3,
               'Automotive': 1.5, 'Airlines': 1.8, 'Real Estate': 1.15}
    },
    'Disorderly': {
        2030: {'Power Generation': 1.3, 'Oil & Gas': 1.5, 'Metals & Mining': 1.2,
               'Automotive': 1.3, 'Airlines': 1.4, 'Real Estate': 1.1},
        2040: {'Power Generation': 1.8, 'Oil & Gas': 2.2, 'Metals & Mining': 1.5,
               'Automotive': 1.7, 'Airlines': 2.0, 'Real Estate': 1.3},
        2050: {'Power Generation': 2.0, 'Oil & Gas': 2.8, 'Metals & Mining': 1.7,
               'Automotive': 2.0, 'Airlines': 2.5, 'Real Estate': 1.5}
    },
    'Hot house world': {
        2030: {'Power Generation': 1.1, 'Oil & Gas': 1.1, 'Metals & Mining': 1.1,
               'Automotive': 1.05, 'Airlines': 1.15, 'Real Estate': 1.1},
        2040: {'Power Generation': 1.3, 'Oil & Gas': 1.2, 'Metals & Mining': 1.4,
               'Automotive': 1.2, 'Airlines': 1.5, 'Real Estate': 1.5},
        2050: {'Power Generation': 1.8, 'Oil & Gas': 1.5, 'Metals & Mining': 2.0,
               'Automotive': 1.7, 'Airlines': 2.5, 'Real Estate': 2.5}
    }
}


class RiskEngine:
    """Calculate climate risk metrics for portfolios"""
    
    def __init__(self, scenario_data: Dict):
        """
        Args:
            scenario_data: Dict with structure {scenario: {year: {carbon_price, gdp_index}}}
        """
        self.scenario_data = scenario_data
    
    def calculate_scenario_impact(
        self,
        assets: List[Asset],
        scenario: str,
        horizon: int
    ) -> ScenarioResult:
        """Calculate risk metrics for a scenario and time horizon"""
        
        params = self.scenario_data.get(scenario, {}).get(horizon, {})
        multipliers = SECTOR_MULTIPLIERS.get(scenario, {}).get(horizon, {})
        
        portfolio_el = 0
        portfolio_exposure = 0
        portfolio_pd_changes = []
        rating_migrations = {'upgrades': 0, 'downgrades': 0, 'stable': 0}
        losses_by_asset = []
        
        for asset in assets:
            exposure = asset.exposure
            base_pd = asset.base_pd
            lgd = asset.base_lgd
            sector = asset.company.sector.value
            
            # Method 1: Sector risk multiplier
            sector_mult = multipliers.get(sector, 1.0)
            adjusted_pd_mult = min(base_pd * sector_mult, 1.0)
            
            # Method 2: PD adjustment using climate drivers
            carbon_impact = (params.get('carbon_price', 50) - 30) / 100  # Baseline $30
            gdp_impact = (100 - params.get('gdp_index', 100)) / 100
            climate_adjustment = carbon_impact + gdp_impact
            
            adjusted_pd_climate = min(base_pd * (1 + climate_adjustment), 1.0)
            
            # Method 3: Combined (average of both methods)
            adjusted_pd = (adjusted_pd_mult + adjusted_pd_climate) / 2
            
            # Calculate Expected Loss
            el = exposure * adjusted_pd * lgd
            portfolio_el += el
            portfolio_exposure += exposure
            
            # Track PD change
            pd_change_pct = ((adjusted_pd - base_pd) / base_pd) * 100
            portfolio_pd_changes.append(pd_change_pct)
            
            # Rating migration (simplified)
            if pd_change_pct > 20:
                rating_migrations['downgrades'] += 1
            elif pd_change_pct < -10:
                rating_migrations['upgrades'] += 1
            else:
                rating_migrations['stable'] += 1
            
            losses_by_asset.append(el)
        
        # Calculate VaR (95th percentile of losses)
        var_95 = float(np.percentile(losses_by_asset, 95)) if losses_by_asset else 0
        
        # Calculate concentration risk (HHI)
        sector_exposures = {}
        for asset in assets:
            sector = asset.company.sector.value
            sector_exposures[sector] = sector_exposures.get(sector, 0) + asset.exposure
        
        total_exposure = sum(sector_exposures.values())
        hhi = sum((exp / total_exposure) ** 2 for exp in sector_exposures.values()) * 10000 if total_exposure > 0 else 0
        
        # Calculate risk-adjusted return (simplified)
        base_return = 0.05  # 5% baseline
        risk_adjusted_return = base_return - (portfolio_el / portfolio_exposure if portfolio_exposure > 0 else 0)
        
        return ScenarioResult(
            scenario=scenario,
            horizon=horizon,
            expected_loss=portfolio_el,
            expected_loss_pct=(portfolio_el / portfolio_exposure) * 100 if portfolio_exposure > 0 else 0,
            risk_adjusted_return=risk_adjusted_return * 100,
            avg_pd_change_pct=float(np.mean(portfolio_pd_changes)) if portfolio_pd_changes else 0,
            rating_migrations=RatingMigration(**rating_migrations),
            var_95=var_95,
            concentration_hhi=hhi,
            total_exposure=portfolio_exposure
        )
