"""
Scenario Impact Service.

Calculates the impact of climate scenarios on portfolios.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select
import statistics

from db.models.scenario import (
    Scenario,
    ScenarioImpactPreview,
)
# Assuming these models exist from earlier work
# from backend.db.models import Portfolio, Holding

logger = logging.getLogger(__name__)


class ScenarioImpactService:
    """Service for calculating scenario impacts on portfolios."""
    
    # Default baseline parameters
    BASELINE_PD = 0.02  # 2% probability of default
    BASELINE_LGD = 0.45  # 45% loss given default
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_impact(
        self,
        scenario_id: str,
        portfolio_id: str,
        parameters_override: Optional[Dict[str, Any]] = None
    ) -> ScenarioImpactPreview:
        """
        Calculate scenario impact on a portfolio.
        
        Args:
            scenario_id: ID of scenario to apply
            portfolio_id: ID of portfolio to analyze
            parameters_override: Optional parameter overrides for preview
        
        Returns:
            ScenarioImpactPreview with impact summary
        """
        # Get scenario
        scenario = self.db.get(Scenario, scenario_id)
        if not scenario:
            raise ValueError(f"Scenario {scenario_id} not found")
        
        # Use override parameters if provided, otherwise use scenario parameters
        parameters = parameters_override or scenario.parameters
        
        # Get portfolio holdings
        # In production, this would query the holdings table
        # For now, we'll generate a sample impact
        holdings = self._get_portfolio_holdings(portfolio_id)
        
        if not holdings:
            raise ValueError(f"Portfolio {portfolio_id} has no holdings")
        
        # Calculate impacts
        total_exposure = sum(h["exposure"] for h in holdings)
        
        # Calculate baseline expected loss
        baseline_el = self._calculate_baseline_expected_loss(holdings)
        
        # Calculate scenario expected loss
        scenario_el = self._calculate_scenario_expected_loss(holdings, parameters)
        
        # Calculate change
        el_change = scenario_el - baseline_el
        el_change_pct = (el_change / baseline_el * 100) if baseline_el > 0 else 0
        
        # Calculate impacts by sector
        by_sector = self._calculate_impact_by_sector(holdings, parameters)
        
        # Calculate impacts by rating
        by_rating = self._calculate_impact_by_rating(holdings, parameters)
        
        # Identify top impacted holdings
        top_impacted = self._get_top_impacted_holdings(holdings, parameters, limit=10)
        
        # Build impact summary
        impact_summary = {
            "total_exposure": total_exposure,
            "baseline_expected_loss": baseline_el,
            "scenario_expected_loss": scenario_el,
            "expected_loss_change": el_change,
            "expected_loss_change_pct": el_change_pct,
            "by_sector": by_sector,
            "by_rating": by_rating,
            "top_impacted_holdings": top_impacted,
        }
        
        # Check if preview already exists
        stmt = select(ScenarioImpactPreview).where(
            ScenarioImpactPreview.scenario_id == scenario_id,
            ScenarioImpactPreview.portfolio_id == portfolio_id,
        )
        existing = self.db.execute(stmt).scalar_one_or_none()
        
        if existing:
            # Update existing preview
            existing.impact_summary = impact_summary
            existing.calculated_at = datetime.now(timezone.utc)
            preview = existing
        else:
            # Create new preview
            preview = ScenarioImpactPreview(
                scenario_id=scenario_id,
                portfolio_id=portfolio_id,
                impact_summary=impact_summary,
                calculation_version="1.0",
            )
            self.db.add(preview)
        
        self.db.commit()
        self.db.refresh(preview)
        
        logger.info(f"Calculated impact for scenario {scenario_id} on portfolio {portfolio_id}: {el_change_pct:.1f}% EL change")
        
        return preview
    
    def _get_portfolio_holdings(self, portfolio_id: str) -> List[Dict[str, Any]]:
        """
        Get holdings for a portfolio.
        
        In production, query the holdings table.
        For now, return sample data.
        """
        # Sample holdings for demonstration
        return [
            {
                "id": "h1",
                "counterparty_name": "Energy Corp A",
                "exposure": 50000000,
                "sector": "energy",
                "rating": "BBB",
                "country": "US",
            },
            {
                "id": "h2",
                "counterparty_name": "Transport Inc",
                "exposure": 30000000,
                "sector": "transport",
                "rating": "A",
                "country": "US",
            },
            {
                "id": "h3",
                "counterparty_name": "Tech Solutions",
                "exposure": 20000000,
                "sector": "technology",
                "rating": "AA",
                "country": "US",
            },
            {
                "id": "h4",
                "counterparty_name": "Utilities Ltd",
                "exposure": 40000000,
                "sector": "utilities",
                "rating": "A",
                "country": "EU",
            },
            {
                "id": "h5",
                "counterparty_name": "Materials Co",
                "exposure": 25000000,
                "sector": "materials",
                "rating": "BBB+",
                "country": "CN",
            },
        ]
    
    def _calculate_baseline_expected_loss(self, holdings: List[Dict[str, Any]]) -> float:
        """Calculate baseline expected loss (EL = PD * LGD * EAD)."""
        total_el = 0
        for holding in holdings:
            exposure = holding["exposure"]
            pd = self._get_baseline_pd(holding.get("rating"))
            lgd = self.BASELINE_LGD
            el = pd * lgd * exposure
            total_el += el
        return total_el
    
    def _calculate_scenario_expected_loss(self, holdings: List[Dict[str, Any]], parameters: Dict[str, Any]) -> float:
        """Calculate scenario expected loss with climate impacts."""
        total_el = 0
        
        # Extract parameters
        sectoral_multipliers = parameters.get("sectoral_multipliers", {})
        temperature_pathway = parameters.get("temperature_pathway", {})
        gdp_impact = parameters.get("gdp_impact", {})
        
        # Get average temperature increase (2050 proxy)
        avg_temp_increase = temperature_pathway.get("2050", 2.0)
        
        # Get GDP impact
        gdp_impact_2050 = gdp_impact.get("2050", -2.0)
        
        for holding in holdings:
            exposure = holding["exposure"]
            sector = holding.get("sector", "unknown")
            rating = holding.get("rating")
            
            # Get baseline PD and LGD
            baseline_pd = self._get_baseline_pd(rating)
            baseline_lgd = self.BASELINE_LGD
            
            # Apply sectoral multiplier
            sector_multiplier = sectoral_multipliers.get(sector, 1.0)
            
            # Apply temperature impact (PD increases with temperature)
            temperature_factor = 1 + (avg_temp_increase - 1.0) * 0.15  # 15% PD increase per degree above 1°C
            
            # Apply GDP impact (negative GDP growth increases PD)
            gdp_factor = 1 + abs(gdp_impact_2050) * 0.05  # 5% PD increase per 1% GDP decline
            
            # Calculate scenario PD
            scenario_pd = baseline_pd * sector_multiplier * temperature_factor * gdp_factor
            
            # Cap PD at 1.0 (100%)
            scenario_pd = min(scenario_pd, 1.0)
            
            # LGD may also increase slightly in stressed scenarios
            scenario_lgd = min(baseline_lgd * 1.1, 0.9)  # Max 90% LGD
            
            # Calculate scenario EL
            el = scenario_pd * scenario_lgd * exposure
            total_el += el
        
        return total_el
    
    def _calculate_impact_by_sector(self, holdings: List[Dict[str, Any]], parameters: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """Calculate impact breakdown by sector."""
        by_sector = {}
        
        for holding in holdings:
            sector = holding.get("sector", "unknown")
            exposure = holding["exposure"]
            rating = holding.get("rating")
            
            if sector not in by_sector:
                by_sector[sector] = {
                    "total_exposure": 0,
                    "baseline_el": 0,
                    "scenario_el": 0,
                }
            
            # Calculate ELs
            baseline_pd = self._get_baseline_pd(rating)
            baseline_el = baseline_pd * self.BASELINE_LGD * exposure
            
            # Simplified scenario EL for sector aggregation
            sectoral_multipliers = parameters.get("sectoral_multipliers", {})
            sector_multiplier = sectoral_multipliers.get(sector, 1.0)
            scenario_el = baseline_el * sector_multiplier * 1.5  # Simplified factor
            
            by_sector[sector]["total_exposure"] += exposure
            by_sector[sector]["baseline_el"] += baseline_el
            by_sector[sector]["scenario_el"] += scenario_el
        
        # Calculate change percentages
        for sector, data in by_sector.items():
            if data["baseline_el"] > 0:
                data["change_pct"] = ((data["scenario_el"] - data["baseline_el"]) / data["baseline_el"]) * 100
            else:
                data["change_pct"] = 0
        
        return by_sector
    
    def _calculate_impact_by_rating(self, holdings: List[Dict[str, Any]], parameters: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """Calculate impact breakdown by credit rating."""
        by_rating = {}
        
        for holding in holdings:
            rating = holding.get("rating", "NR")  # NR = Not Rated
            exposure = holding["exposure"]
            
            if rating not in by_rating:
                by_rating[rating] = {
                    "total_exposure": 0,
                    "baseline_el": 0,
                    "scenario_el": 0,
                }
            
            baseline_pd = self._get_baseline_pd(rating)
            baseline_el = baseline_pd * self.BASELINE_LGD * exposure
            scenario_el = baseline_el * 1.8  # Simplified multiplier
            
            by_rating[rating]["total_exposure"] += exposure
            by_rating[rating]["baseline_el"] += baseline_el
            by_rating[rating]["scenario_el"] += scenario_el
        
        # Calculate change percentages
        for rating, data in by_rating.items():
            if data["baseline_el"] > 0:
                data["change_pct"] = ((data["scenario_el"] - data["baseline_el"]) / data["baseline_el"]) * 100
            else:
                data["change_pct"] = 0
        
        return by_rating
    
    def _get_top_impacted_holdings(self, holdings: List[Dict[str, Any]], parameters: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """Get holdings with highest expected loss increase."""
        impacts = []
        
        for holding in holdings:
            exposure = holding["exposure"]
            rating = holding.get("rating")
            sector = holding.get("sector", "unknown")
            
            baseline_pd = self._get_baseline_pd(rating)
            baseline_el = baseline_pd * self.BASELINE_LGD * exposure
            
            # Simplified scenario EL
            sectoral_multipliers = parameters.get("sectoral_multipliers", {})
            sector_multiplier = sectoral_multipliers.get(sector, 1.0)
            scenario_el = baseline_el * sector_multiplier * 1.5
            
            change_pct = ((scenario_el - baseline_el) / baseline_el * 100) if baseline_el > 0 else 0
            
            impacts.append({
                "counterparty": holding["counterparty_name"],
                "exposure": exposure,
                "sector": sector,
                "rating": rating,
                "baseline_el": baseline_el,
                "scenario_el": scenario_el,
                "change_pct": change_pct,
            })
        
        # Sort by change percentage descending
        impacts.sort(key=lambda x: x["change_pct"], reverse=True)
        
        return impacts[:limit]
    
    def _get_baseline_pd(self, rating: Optional[str]) -> float:
        """Get baseline probability of default by credit rating."""
        # Standard PD mapping by rating
        pd_mapping = {
            "AAA": 0.001,
            "AA+": 0.002,
            "AA": 0.003,
            "AA-": 0.004,
            "A+": 0.006,
            "A": 0.008,
            "A-": 0.010,
            "BBB+": 0.015,
            "BBB": 0.020,
            "BBB-": 0.030,
            "BB+": 0.050,
            "BB": 0.070,
            "BB-": 0.100,
            "B+": 0.150,
            "B": 0.200,
            "B-": 0.300,
            "CCC+": 0.500,
            "CCC": 0.700,
            "CCC-": 0.900,
        }
        
        return pd_mapping.get(rating, self.BASELINE_PD)
