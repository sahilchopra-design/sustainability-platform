"""Portfolio-level Metrics Calculator"""
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class RatingMigration:
    """Rating migration statistics"""
    upgrades: int = 0
    downgrades: int = 0
    stable: int = 0


@dataclass
class PortfolioMetrics:
    """Complete portfolio-level metrics"""
    # Loss metrics
    expected_loss: float
    expected_loss_pct: float
    
    # VaR metrics
    var_95: float
    var_99: float
    expected_shortfall_95: float
    expected_shortfall_99: float
    
    # Return metrics
    risk_adjusted_return: float
    
    # PD metrics
    weighted_avg_pd: float
    avg_pd_change_pct: float
    
    # Concentration metrics
    sector_hhi: float
    geographic_hhi: float
    
    # Rating migrations
    rating_migrations: RatingMigration
    
    # Exposure
    total_exposure: float
    

class PortfolioMetricsCalculator:
    """
    Calculate portfolio-level aggregated metrics.
    
    Metrics:
    - Expected Loss (EL) and EL%
    - VaR and Expected Shortfall
    - Risk-adjusted return
    - Concentration (HHI by sector/geography)
    - Rating migrations
    """
    
    def __init__(self, base_return: float = 0.05):
        """
        Initialize calculator.
        
        Args:
            base_return: Baseline portfolio return (e.g., 5%)
        """
        self.base_return = base_return
    
    def calculate(
        self,
        exposures: np.ndarray,
        baseline_pds: np.ndarray,
        adjusted_pds: np.ndarray,
        lgds: np.ndarray,
        sectors: np.ndarray,
        countries: Optional[np.ndarray] = None,
        var_95: Optional[float] = None,
        var_99: Optional[float] = None,
        es_95: Optional[float] = None,
        es_99: Optional[float] = None
    ) -> PortfolioMetrics:
        """
        Calculate all portfolio metrics.
        
        Args:
            exposures: Array of exposures (EAD)
            baseline_pds: Array of baseline PDs
            adjusted_pds: Array of climate-adjusted PDs
            lgds: Array of LGDs
            sectors: Array of sector names
            countries: Array of country codes (optional)
            var_95: Pre-calculated VaR 95% (optional)
            var_99: Pre-calculated VaR 99% (optional)
            es_95: Pre-calculated ES 95% (optional)
            es_99: Pre-calculated ES 99% (optional)
            
        Returns:
            PortfolioMetrics with all calculated metrics
        """
        total_exposure = np.sum(exposures)
        
        # Calculate Expected Loss
        expected_losses = exposures * adjusted_pds * lgds
        total_el = np.sum(expected_losses)
        el_pct = (total_el / total_exposure * 100) if total_exposure > 0 else 0
        
        # Weighted average PD
        weighted_avg_pd = np.sum(exposures * adjusted_pds) / total_exposure if total_exposure > 0 else 0
        
        # Average PD change percentage
        pd_changes = ((adjusted_pds - baseline_pds) / baseline_pds * 100)
        pd_changes = pd_changes[baseline_pds > 0]  # Only where baseline PD > 0
        avg_pd_change_pct = np.mean(pd_changes) if len(pd_changes) > 0 else 0
        
        # Risk-adjusted return
        risk_cost = total_el / total_exposure if total_exposure > 0 else 0
        risk_adjusted_return = (self.base_return - risk_cost) * 100
        
        # Concentration metrics
        sector_hhi = self._calculate_hhi(exposures, sectors)
        geographic_hhi = self._calculate_hhi(exposures, countries) if countries is not None else 0
        
        # Rating migrations
        rating_migrations = self._calculate_rating_migrations(
            baseline_pds,
            adjusted_pds
        )
        
        return PortfolioMetrics(
            expected_loss=float(total_el),
            expected_loss_pct=float(el_pct),
            var_95=float(var_95) if var_95 is not None else 0.0,
            var_99=float(var_99) if var_99 is not None else 0.0,
            expected_shortfall_95=float(es_95) if es_95 is not None else 0.0,
            expected_shortfall_99=float(es_99) if es_99 is not None else 0.0,
            risk_adjusted_return=float(risk_adjusted_return),
            weighted_avg_pd=float(weighted_avg_pd),
            avg_pd_change_pct=float(avg_pd_change_pct),
            sector_hhi=float(sector_hhi),
            geographic_hhi=float(geographic_hhi),
            rating_migrations=rating_migrations,
            total_exposure=float(total_exposure)
        )
    
    def _calculate_hhi(self, exposures: np.ndarray, categories: np.ndarray) -> float:
        """
        Calculate Herfindahl-Hirschman Index for concentration.
        
        HHI = sum((exposure_i / total_exposure)^2) * 10000
        
        Args:
            exposures: Array of exposures
            categories: Array of categories (sectors, countries, etc.)
            
        Returns:
            HHI value (0-10000 scale)
        """
        if categories is None or len(categories) == 0:
            return 0.0
        
        total_exposure = np.sum(exposures)
        if total_exposure == 0:
            return 0.0
        
        # Group exposures by category
        category_exposures = {}
        for i, category in enumerate(categories):
            if category not in category_exposures:
                category_exposures[category] = 0
            category_exposures[category] += exposures[i]
        
        # Calculate HHI
        hhi = sum(
            (exp / total_exposure) ** 2
            for exp in category_exposures.values()
        ) * 10000
        
        return hhi
    
    def _calculate_rating_migrations(
        self,
        baseline_pds: np.ndarray,
        adjusted_pds: np.ndarray,
        downgrade_threshold: float = 0.20,  # 20% increase in PD
        upgrade_threshold: float = -0.10    # 10% decrease in PD
    ) -> RatingMigration:
        """
        Calculate rating migration statistics.
        
        Args:
            baseline_pds: Baseline PDs
            adjusted_pds: Climate-adjusted PDs
            downgrade_threshold: PD change % threshold for downgrade
            upgrade_threshold: PD change % threshold for upgrade
            
        Returns:
            RatingMigration statistics
        """
        upgrades = 0
        downgrades = 0
        stable = 0
        
        for baseline_pd, adjusted_pd in zip(baseline_pds, adjusted_pds):
            if baseline_pd == 0:
                stable += 1
                continue
            
            pd_change_pct = (adjusted_pd - baseline_pd) / baseline_pd
            
            if pd_change_pct > downgrade_threshold:
                downgrades += 1
            elif pd_change_pct < upgrade_threshold:
                upgrades += 1
            else:
                stable += 1
        
        return RatingMigration(
            upgrades=upgrades,
            downgrades=downgrades,
            stable=stable
        )
    
    def calculate_sector_breakdown(
        self,
        exposures: np.ndarray,
        adjusted_pds: np.ndarray,
        lgds: np.ndarray,
        sectors: np.ndarray
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate metrics broken down by sector.
        
        Args:
            exposures: Array of exposures
            adjusted_pds: Array of adjusted PDs
            lgds: Array of LGDs
            sectors: Array of sector names
            
        Returns:
            Dict mapping sector name to metrics dict
        """
        sector_metrics = {}
        
        unique_sectors = np.unique(sectors)
        
        for sector in unique_sectors:
            mask = sectors == sector
            sector_exposures = exposures[mask]
            sector_pds = adjusted_pds[mask]
            sector_lgds = lgds[mask]
            
            total_exposure = np.sum(sector_exposures)
            expected_losses = sector_exposures * sector_pds * sector_lgds
            total_el = np.sum(expected_losses)
            
            weighted_avg_pd = (
                np.sum(sector_exposures * sector_pds) / total_exposure
                if total_exposure > 0 else 0
            )
            
            sector_metrics[str(sector)] = {
                'total_exposure': float(total_exposure),
                'expected_loss': float(total_el),
                'weighted_avg_pd': float(weighted_avg_pd),
                'num_assets': int(np.sum(mask))
            }
        
        return sector_metrics
