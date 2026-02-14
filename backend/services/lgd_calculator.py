"""LGD Adjustment Calculator - Climate risk impact on Loss Given Default"""
import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class LGDContribution:
    """Breakdown of LGD adjustment contributors"""
    physical_damage: float
    collateral_devaluation: float
    recovery_impairment: float
    sector_adjustment: float
    total_adjustment: float


@dataclass
class LGDResult:
    """LGD calculation result"""
    baseline_lgd: float
    adjusted_lgd: float
    contribution_breakdown: LGDContribution
    adjustment_pct: float


class LGDAdjustmentCalculator:
    """
    Calculator for climate-adjusted Loss Given Default.
    
    Factors:
    - Physical Damage: Asset damage from climate events
    - Collateral Devaluation: Stranded assets, obsolescence
    - Recovery Impairment: Reduced recovery rates due to climate
    - Sector: Industry-specific adjustments
    """
    
    # Collateral type sensitivities to climate risk
    COLLATERAL_SENSITIVITIES = {
        'Real Estate': 1.5,       # High physical risk exposure
        'Equipment': 1.2,         # Moderate obsolescence risk
        'Inventory': 1.0,         # Supply chain disruption
        'Financial': 0.3,         # Low direct climate impact
        'Unsecured': 0.5          # Indirect impacts only
    }
    
    # Sector LGD sensitivities
    SECTOR_LGD_FACTORS = {
        'Power Generation': 1.3,
        'Oil & Gas': 1.6,
        'Metals & Mining': 1.2,
        'Automotive': 1.1,
        'Airlines': 0.9,
        'Real Estate': 1.8
    }
    
    def __init__(self, scenario: str = 'Orderly'):
        self.scenario = scenario
    
    def calculate(
        self,
        baseline_lgd: float,
        sector: str,
        collateral_type: str = 'Unsecured',
        physical_risk_score: Optional[int] = None,
        time_horizon: int = 2050
    ) -> LGDResult:
        """
        Calculate climate-adjusted LGD.
        
        Args:
            baseline_lgd: Current LGD (0-1)
            sector: Industry sector
            collateral_type: Type of collateral
            physical_risk_score: Physical risk exposure (1-5)
            time_horizon: Target year
            
        Returns:
            LGDResult with adjusted LGD and breakdown
        """
        # Get sensitivities
        collateral_sens = self.COLLATERAL_SENSITIVITIES.get(collateral_type, 1.0)
        sector_factor = self.SECTOR_LGD_FACTORS.get(sector, 1.0)
        
        # Time scaling
        time_scale = self._get_time_scale(time_horizon)
        
        # Calculate components
        physical_damage = self._calculate_physical_damage(
            baseline_lgd,
            physical_risk_score,
            collateral_sens,
            time_scale
        )
        
        collateral_devaluation = self._calculate_collateral_devaluation(
            baseline_lgd,
            sector_factor,
            collateral_type,
            time_scale
        )
        
        recovery_impairment = self._calculate_recovery_impairment(
            baseline_lgd,
            sector,
            time_scale
        )
        
        sector_adjustment = self._calculate_sector_adjustment(
            baseline_lgd,
            sector,
            time_scale
        )
        
        # Total adjustment
        total_adjustment = (
            physical_damage +
            collateral_devaluation +
            recovery_impairment +
            sector_adjustment
        )
        
        # Adjusted LGD (capped at 0-1)
        adjusted_lgd = np.clip(baseline_lgd + total_adjustment, 0, 1)
        
        # Adjustment percentage
        adjustment_pct = ((adjusted_lgd - baseline_lgd) / baseline_lgd * 100) if baseline_lgd > 0 else 0
        
        return LGDResult(
            baseline_lgd=float(baseline_lgd),
            adjusted_lgd=float(adjusted_lgd),
            contribution_breakdown=LGDContribution(
                physical_damage=float(physical_damage),
                collateral_devaluation=float(collateral_devaluation),
                recovery_impairment=float(recovery_impairment),
                sector_adjustment=float(sector_adjustment),
                total_adjustment=float(total_adjustment)
            ),
            adjustment_pct=float(adjustment_pct)
        )
    
    def calculate_batch(
        self,
        baseline_lgds: np.ndarray,
        sectors: np.ndarray,
        collateral_types: Optional[np.ndarray] = None,
        physical_risk_scores: Optional[np.ndarray] = None,
        time_horizon: int = 2050
    ) -> np.ndarray:
        """
        Vectorized batch LGD calculation.
        
        Args:
            baseline_lgds: Array of baseline LGDs
            sectors: Array of sectors
            collateral_types: Array of collateral types
            physical_risk_scores: Array of physical risk scores
            time_horizon: Target year
            
        Returns:
            Array of adjusted LGDs
        """
        n = len(baseline_lgds)
        adjusted_lgds = np.zeros(n)
        
        for i in range(n):
            result = self.calculate(
                baseline_lgd=baseline_lgds[i],
                sector=sectors[i],
                collateral_type=collateral_types[i] if collateral_types is not None else 'Unsecured',
                physical_risk_score=int(physical_risk_scores[i]) if physical_risk_scores is not None else None,
                time_horizon=time_horizon
            )
            adjusted_lgds[i] = result.adjusted_lgd
        
        return adjusted_lgds
    
    def _get_time_scale(self, time_horizon: int) -> float:
        """Get time scaling factor."""
        scales = {
            2030: 0.5,
            2040: 1.0,
            2050: 1.5
        }
        return scales.get(time_horizon, 1.0)
    
    def _calculate_physical_damage(
        self,
        baseline_lgd: float,
        physical_risk_score: Optional[int],
        collateral_sens: float,
        time_scale: float
    ) -> float:
        """Calculate physical damage component."""
        if physical_risk_score is None:
            return 0.0
        
        # Normalize score
        risk_factor = (physical_risk_score - 1) / 4.0
        
        # Physical damage increases LGD
        damage = (
            baseline_lgd *
            risk_factor *
            collateral_sens *
            time_scale *
            0.3  # Weight
        )
        
        return damage
    
    def _calculate_collateral_devaluation(
        self,
        baseline_lgd: float,
        sector_factor: float,
        collateral_type: str,
        time_scale: float
    ) -> float:
        """Calculate collateral devaluation from stranded assets."""
        # Higher in transition scenarios for fossil fuel assets
        if self.scenario in ['Orderly', 'Disorderly']:
            devaluation_factor = 0.25
        else:
            devaluation_factor = 0.10
        
        collateral_sens = self.COLLATERAL_SENSITIVITIES.get(collateral_type, 1.0)
        
        return baseline_lgd * sector_factor * collateral_sens * devaluation_factor * time_scale * 0.2
    
    def _calculate_recovery_impairment(
        self,
        baseline_lgd: float,
        sector: str,
        time_scale: float
    ) -> float:
        """Calculate recovery process impairment."""
        # Recovery rates may worsen due to market disruption
        impairment_factors = {
            'Orderly': 0.05,
            'Disorderly': 0.12,
            'Hot house world': 0.15
        }
        
        factor = impairment_factors.get(self.scenario, 0.05)
        
        return baseline_lgd * factor * time_scale * 0.15
    
    def _calculate_sector_adjustment(
        self,
        baseline_lgd: float,
        sector: str,
        time_scale: float
    ) -> float:
        """Calculate sector-specific LGD adjustment."""
        sector_factor = self.SECTOR_LGD_FACTORS.get(sector, 1.0)
        
        # Base adjustment
        adjustment = (sector_factor - 1.0) * baseline_lgd * 0.1 * time_scale
        
        return adjustment
