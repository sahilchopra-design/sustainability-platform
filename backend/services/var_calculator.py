"""Value at Risk (VaR) Calculator - Portfolio loss distribution and VaR metrics"""
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional


@dataclass
class VaRResult:
    """VaR calculation result"""
    var_95: float
    var_99: float
    expected_shortfall_95: float
    expected_shortfall_99: float
    mean_loss: float
    std_loss: float
    

class VaRCalculator:
    """
    Calculator for Value at Risk and Expected Shortfall.
    
    Methods:
    - Historical Simulation: Use historical loss distribution
    - Monte Carlo: Simulate loss distribution from PD/LGD
    - Parametric: Assume normal distribution of losses
    """
    
    def __init__(self, confidence_levels: List[float] = None, n_simulations: int = 10000, random_seed: int = 42):
        """
        Initialize VaR calculator.
        
        Args:
            confidence_levels: List of confidence levels (default: [0.95, 0.99])
            n_simulations: Number of Monte Carlo simulations
            random_seed: Random seed for reproducibility
        """
        self.confidence_levels = confidence_levels or [0.95, 0.99]
        self.n_simulations = n_simulations
        self.rng = np.random.default_rng(random_seed)
    
    def calculate_monte_carlo(
        self,
        exposures: np.ndarray,
        pds: np.ndarray,
        lgds: np.ndarray,
        correlation: float = 0.3
    ) -> VaRResult:
        """
        Calculate VaR using Monte Carlo simulation.
        
        Args:
            exposures: Array of exposure amounts (EAD)
            pds: Array of probabilities of default
            lgds: Array of loss given default rates
            correlation: Asset correlation factor (0-1)
            
        Returns:
            VaRResult with VaR and Expected Shortfall metrics
        """
        n_assets = len(exposures)
        
        # Generate correlated default events using Gaussian copula
        if correlation > 0:
            # Common factor model: X = sqrt(rho) * Z + sqrt(1-rho) * epsilon
            common_factor = self.rng.standard_normal(self.n_simulations)
            idiosyncratic = self.rng.standard_normal((self.n_simulations, n_assets))
            
            # Correlated uniform variables
            correlated_normals = (
                np.sqrt(correlation) * common_factor[:, np.newaxis] +
                np.sqrt(1 - correlation) * idiosyncratic
            )
            uniform_vars = self._normal_cdf(correlated_normals)
        else:
            # Independent defaults
            uniform_vars = self.rng.uniform(0, 1, (self.n_simulations, n_assets))
        
        # Default indicators: 1 if default, 0 otherwise
        defaults = (uniform_vars < pds).astype(float)
        
        # Calculate losses for each simulation
        # Loss = EAD * Default * LGD
        losses = np.sum(exposures * defaults * lgds, axis=1)
        
        # Calculate VaR (percentiles)
        var_95 = np.percentile(losses, 95)
        var_99 = np.percentile(losses, 99)
        
        # Calculate Expected Shortfall (average loss beyond VaR)
        es_95 = np.mean(losses[losses >= var_95])
        es_99 = np.mean(losses[losses >= var_99])
        
        # Basic statistics
        mean_loss = np.mean(losses)
        std_loss = np.std(losses)
        
        return VaRResult(
            var_95=float(var_95),
            var_99=float(var_99),
            expected_shortfall_95=float(es_95),
            expected_shortfall_99=float(es_99),
            mean_loss=float(mean_loss),
            std_loss=float(std_loss)
        )
    
    def calculate_parametric(
        self,
        exposures: np.ndarray,
        pds: np.ndarray,
        lgds: np.ndarray,
        correlation: float = 0.3
    ) -> VaRResult:
        """
        Calculate VaR using parametric (analytical) approach.
        Assumes portfolio loss follows a normal distribution.
        
        Args:
            exposures: Array of exposure amounts
            pds: Array of probabilities of default
            lgds: Array of loss given default rates
            correlation: Asset correlation factor
            
        Returns:
            VaRResult with VaR metrics
        """
        # Expected loss for each asset
        expected_losses = exposures * pds * lgds
        portfolio_el = np.sum(expected_losses)
        
        # Variance of losses (considering correlation)
        # Var(L_i) = EAD_i^2 * LGD_i^2 * PD_i * (1 - PD_i)
        variances = (exposures ** 2) * (lgds ** 2) * pds * (1 - pds)
        
        # Portfolio variance with correlation
        portfolio_variance = np.sum(variances)
        
        # Add covariance terms if correlation > 0
        if correlation > 0:
            for i in range(len(exposures)):
                for j in range(i + 1, len(exposures)):
                    covariance = (
                        correlation *
                        exposures[i] * lgds[i] * np.sqrt(pds[i] * (1 - pds[i])) *
                        exposures[j] * lgds[j] * np.sqrt(pds[j] * (1 - pds[j]))
                    )
                    portfolio_variance += 2 * covariance
        
        portfolio_std = np.sqrt(portfolio_variance)
        
        # VaR using normal distribution
        # VaR_alpha = mu + z_alpha * sigma
        z_95 = 1.645  # 95th percentile
        z_99 = 2.326  # 99th percentile
        
        var_95 = portfolio_el + z_95 * portfolio_std
        var_99 = portfolio_el + z_99 * portfolio_std
        
        # Expected Shortfall (for normal distribution)
        # ES_alpha = mu + sigma * phi(z_alpha) / (1 - alpha)
        phi_95 = self._standard_normal_pdf(z_95)
        phi_99 = self._standard_normal_pdf(z_99)
        
        es_95 = portfolio_el + portfolio_std * phi_95 / 0.05
        es_99 = portfolio_el + portfolio_std * phi_99 / 0.01
        
        return VaRResult(
            var_95=float(max(var_95, 0)),  # VaR cannot be negative
            var_99=float(max(var_99, 0)),
            expected_shortfall_95=float(max(es_95, 0)),
            expected_shortfall_99=float(max(es_99, 0)),
            mean_loss=float(portfolio_el),
            std_loss=float(portfolio_std)
        )
    
    def calculate_batch(
        self,
        exposures: np.ndarray,
        pds: np.ndarray,
        lgds: np.ndarray,
        method: str = 'monte_carlo',
        correlation: float = 0.3
    ) -> VaRResult:
        """
        Calculate VaR using specified method.
        
        Args:
            exposures: Array of exposures
            pds: Array of PDs
            lgds: Array of LGDs
            method: 'monte_carlo' or 'parametric'
            correlation: Asset correlation
            
        Returns:
            VaRResult
        """
        if method == 'monte_carlo':
            return self.calculate_monte_carlo(exposures, pds, lgds, correlation)
        elif method == 'parametric':
            return self.calculate_parametric(exposures, pds, lgds, correlation)
        else:
            raise ValueError(f"Unknown method: {method}")
    
    @staticmethod
    def _normal_cdf(x: np.ndarray) -> np.ndarray:
        """Standard normal CDF using error function."""
        return 0.5 * (1 + np.tanh(x / np.sqrt(2)))
    
    @staticmethod
    def _standard_normal_pdf(x: float) -> float:
        """Standard normal PDF."""
        return np.exp(-0.5 * x ** 2) / np.sqrt(2 * np.pi)
