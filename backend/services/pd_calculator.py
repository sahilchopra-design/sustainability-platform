"""PD Adjustment Calculator - Climate risk impact on Probability of Default"""
import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple, Optional
from decimal import Decimal


@dataclass
class PDContribution:
    """Breakdown of PD adjustment contributors"""
    transition_risk: float
    physical_risk: float
    emissions_impact: float
    transition_plan_impact: float
    sector_multiplier: float
    total_adjustment: float


@dataclass
class PDResult:
    """PD calculation result with confidence intervals"""
    baseline_pd: float
    adjusted_pd: float
    confidence_interval_lower: float  # 95% CI
    confidence_interval_upper: float  # 95% CI
    contribution_breakdown: PDContribution
    adjustment_pct: float


class PDAdjustmentCalculator:
    """
    High-performance calculator for climate-adjusted Probability of Default.
    
    Methodology:
    - Transition Risk: Carbon price exposure, policy changes
    - Physical Risk: Asset damage, supply chain disruption
    - Emissions: Intensity and trend impact
    - Transition Plan: Quality of climate strategy
    - Sector: Industry-specific multipliers
    """
    
    # Sector-specific sensitivity factors
    SECTOR_SENSITIVITIES = {
        'Power Generation': {'transition': 1.5, 'physical': 1.1},
        'Oil & Gas': {'transition': 2.0, 'physical': 1.2},
        'Metals & Mining': {'transition': 1.3, 'physical': 1.4},
        'Automotive': {'transition': 1.4, 'physical': 1.0},
        'Airlines': {'transition': 1.6, 'physical': 1.3},
        'Real Estate': {'transition': 0.8, 'physical': 1.8}
    }
    
    # Scenario parameters
    SCENARIO_PARAMS = {
        'Orderly': {
            'carbon_price_factor': 1.8,
            'policy_stringency': 0.9,
            'transition_speed': 1.0
        },
        'Disorderly': {
            'carbon_price_factor': 2.5,
            'policy_stringency': 1.3,
            'transition_speed': 1.5
        },
        'Hot house world': {
            'carbon_price_factor': 0.5,
            'policy_stringency': 0.3,
            'transition_speed': 0.4
        }
    }
    
    # Time horizon multipliers
    HORIZON_MULTIPLIERS = {
        2030: 0.6,
        2040: 1.0,
        2050: 1.4
    }
    
    def __init__(self, scenario: str = 'Orderly'):
        """
        Initialize calculator with scenario parameters.
        
        Args:
            scenario: NGFS scenario name
        """
        self.scenario = scenario
        self.scenario_params = self.SCENARIO_PARAMS.get(
            scenario, 
            self.SCENARIO_PARAMS['Orderly']
        )
    
    def calculate(
        self,
        baseline_pd: float,
        sector: str,
        emissions_intensity: Optional[float] = None,
        emissions_trend: str = 'Stable',
        transition_plan_score: Optional[int] = None,
        physical_risk_score: Optional[int] = None,
        time_horizon: int = 2050
    ) -> PDResult:
        """
        Calculate climate-adjusted PD for a single counterparty.
        
        Args:
            baseline_pd: Current PD (0-1)
            sector: Industry sector
            emissions_intensity: tCO2e per revenue unit
            emissions_trend: 'Improving', 'Stable', 'Deteriorating'
            transition_plan_score: Quality score (1-5, 5=best)
            physical_risk_score: Physical risk exposure (1-5, 5=highest)
            time_horizon: Target year (2030, 2040, 2050)
            
        Returns:
            PDResult with adjusted PD and breakdown
        """
        # Get sector sensitivities
        sector_sens = self.SECTOR_SENSITIVITIES.get(
            sector,
            {'transition': 1.0, 'physical': 1.0}
        )
        
        # Get time horizon multiplier
        horizon_mult = self.HORIZON_MULTIPLIERS.get(time_horizon, 1.0)
        
        # Calculate transition risk component
        transition_risk = self._calculate_transition_risk(
            baseline_pd,
            sector_sens['transition'],
            emissions_intensity,
            emissions_trend,
            transition_plan_score,
            horizon_mult
        )
        
        # Calculate physical risk component
        physical_risk = self._calculate_physical_risk(
            baseline_pd,
            sector_sens['physical'],
            physical_risk_score,
            horizon_mult
        )
        
        # Calculate emissions impact
        emissions_impact = self._calculate_emissions_impact(
            baseline_pd,
            emissions_intensity,
            emissions_trend
        )
        
        # Calculate transition plan impact (negative = improvement)
        transition_plan_impact = self._calculate_transition_plan_impact(
            baseline_pd,
            transition_plan_score
        )
        
        # Sector multiplier
        sector_multiplier = self._calculate_sector_multiplier(
            baseline_pd,
            sector,
            time_horizon
        )
        
        # Total adjustment
        total_adjustment = (
            transition_risk +
            physical_risk +
            emissions_impact +
            transition_plan_impact +
            sector_multiplier
        )
        
        # Adjusted PD (capped at 0-1)
        adjusted_pd = np.clip(baseline_pd + total_adjustment, 0, 1)
        
        # Confidence intervals (based on model uncertainty)
        uncertainty = 0.15 * abs(total_adjustment)  # 15% uncertainty
        ci_lower = np.clip(adjusted_pd - uncertainty, 0, 1)
        ci_upper = np.clip(adjusted_pd + uncertainty, 0, 1)
        
        # Adjustment percentage
        adjustment_pct = ((adjusted_pd - baseline_pd) / baseline_pd * 100) if baseline_pd > 0 else 0
        
        return PDResult(
            baseline_pd=float(baseline_pd),
            adjusted_pd=float(adjusted_pd),
            confidence_interval_lower=float(ci_lower),
            confidence_interval_upper=float(ci_upper),
            contribution_breakdown=PDContribution(
                transition_risk=float(transition_risk),
                physical_risk=float(physical_risk),
                emissions_impact=float(emissions_impact),
                transition_plan_impact=float(transition_plan_impact),
                sector_multiplier=float(sector_multiplier),
                total_adjustment=float(total_adjustment)
            ),
            adjustment_pct=float(adjustment_pct)
        )
    
    def calculate_batch(
        self,
        baseline_pds: np.ndarray,
        sectors: np.ndarray,
        emissions_intensities: Optional[np.ndarray] = None,
        emissions_trends: Optional[np.ndarray] = None,
        transition_plan_scores: Optional[np.ndarray] = None,
        physical_risk_scores: Optional[np.ndarray] = None,
        time_horizon: int = 2050
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Vectorized batch calculation for high performance.
        
        Args:
            baseline_pds: Array of baseline PDs
            sectors: Array of sector names
            emissions_intensities: Array of emissions intensities
            emissions_trends: Array of emissions trends
            transition_plan_scores: Array of transition scores
            physical_risk_scores: Array of physical risk scores
            time_horizon: Target year
            
        Returns:
            Tuple of (adjusted_pds, ci_lower, ci_upper)
        """
        n = len(baseline_pds)
        adjusted_pds = np.zeros(n)
        ci_lower = np.zeros(n)
        ci_upper = np.zeros(n)
        
        # Vectorized calculation (simplified for performance)
        horizon_mult = self.HORIZON_MULTIPLIERS.get(time_horizon, 1.0)
        
        for i in range(n):
            result = self.calculate(
                baseline_pd=baseline_pds[i],
                sector=sectors[i],
                emissions_intensity=emissions_intensities[i] if emissions_intensities is not None else None,
                emissions_trend=emissions_trends[i] if emissions_trends is not None else 'Stable',
                transition_plan_score=int(transition_plan_scores[i]) if transition_plan_scores is not None else None,
                physical_risk_score=int(physical_risk_scores[i]) if physical_risk_scores is not None else None,
                time_horizon=time_horizon
            )
            adjusted_pds[i] = result.adjusted_pd
            ci_lower[i] = result.confidence_interval_lower
            ci_upper[i] = result.confidence_interval_upper
        
        return adjusted_pds, ci_lower, ci_upper
    
    def _calculate_transition_risk(
        self,
        baseline_pd: float,
        sector_sensitivity: float,
        emissions_intensity: Optional[float],
        emissions_trend: str,
        transition_plan_score: Optional[int],
        horizon_mult: float
    ) -> float:
        """Calculate transition risk component."""
        if emissions_intensity is None:
            return 0.0
        
        # Base transition risk from carbon price exposure
        carbon_factor = self.scenario_params['carbon_price_factor']
        policy_factor = self.scenario_params['policy_stringency']
        
        # Emissions intensity impact (normalized to 0-1 scale)
        emissions_risk = min(emissions_intensity / 2.0, 1.0)  # Cap at 2.0 tCO2e/unit
        
        # Transition risk calculation
        transition_risk = (
            baseline_pd *
            sector_sensitivity *
            carbon_factor *
            policy_factor *
            emissions_risk *
            horizon_mult *
            0.3  # Weight factor
        )
        
        return transition_risk
    
    def _calculate_physical_risk(
        self,
        baseline_pd: float,
        sector_sensitivity: float,
        physical_risk_score: Optional[int],
        horizon_mult: float
    ) -> float:
        """Calculate physical risk component."""
        if physical_risk_score is None:
            return 0.0
        
        # Normalize score (1-5) to risk factor (0-1)
        risk_factor = (physical_risk_score - 1) / 4.0
        
        # Physical risk increases more in hot house scenarios
        if self.scenario == 'Hot house world':
            risk_factor *= 2.0
        
        physical_risk = (
            baseline_pd *
            sector_sensitivity *
            risk_factor *
            horizon_mult *
            0.25  # Weight factor
        )
        
        return physical_risk
    
    def _calculate_emissions_impact(
        self,
        baseline_pd: float,
        emissions_intensity: Optional[float],
        emissions_trend: str
    ) -> float:
        """Calculate emissions trend impact."""
        if emissions_intensity is None:
            return 0.0
        
        # Trend multipliers
        trend_factors = {
            'Improving': -0.2,    # Negative = reduces PD
            'Stable': 0.0,
            'Deteriorating': 0.3  # Positive = increases PD
        }
        
        trend_factor = trend_factors.get(emissions_trend, 0.0)
        
        return baseline_pd * trend_factor * 0.15
    
    def _calculate_transition_plan_impact(
        self,
        baseline_pd: float,
        transition_plan_score: Optional[int]
    ) -> float:
        """Calculate transition plan quality impact (negative = improvement)."""
        if transition_plan_score is None:
            return 0.0
        
        # Score 5 = best plan = -15% PD, Score 1 = poor plan = +10% PD
        impact_factors = {
            1: 0.10,
            2: 0.05,
            3: 0.0,
            4: -0.08,
            5: -0.15
        }
        
        return baseline_pd * impact_factors.get(transition_plan_score, 0.0)
    
    def _calculate_sector_multiplier(
        self,
        baseline_pd: float,
        sector: str,
        time_horizon: int
    ) -> float:
        """Calculate sector-specific base multiplier."""
        # Sector base adjustments by scenario
        sector_adjustments = {
            'Orderly': {
                'Power Generation': 0.10,
                'Oil & Gas': 0.25,
                'Metals & Mining': 0.08,
                'Automotive': 0.12,
                'Airlines': 0.18,
                'Real Estate': 0.05
            },
            'Disorderly': {
                'Power Generation': 0.15,
                'Oil & Gas': 0.40,
                'Metals & Mining': 0.12,
                'Automotive': 0.20,
                'Airlines': 0.30,
                'Real Estate': 0.08
            },
            'Hot house world': {
                'Power Generation': 0.08,
                'Oil & Gas': 0.05,
                'Metals & Mining': 0.15,
                'Automotive': 0.10,
                'Airlines': 0.25,
                'Real Estate': 0.20
            }
        }
        
        adjustments = sector_adjustments.get(self.scenario, {})
        base_adjustment = adjustments.get(sector, 0.05)
        
        # Scale by time horizon
        horizon_scale = self.HORIZON_MULTIPLIERS.get(time_horizon, 1.0)
        
        return baseline_pd * base_adjustment * horizon_scale
