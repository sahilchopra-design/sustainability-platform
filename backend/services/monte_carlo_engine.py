"""
Monte Carlo Simulation Engine — Portfolio-Level Parameter Uncertainty Analysis

Aligned with Basel III Pillar 2 stress testing, NGFS Phase IV scenarios,
TCFD Scenario Analysis Technical Supplement, and EBA GL/2022/16.

Method: Parameter Uncertainty Monte Carlo
  - Draws N macro-parameter scenarios (carbon price path, physical risk severity,
    PD shock factor, LGD shock, exposure uncertainty)
  - For each draw, computes portfolio EL, VaR (Vasicek), carbon cost, WACI
  - Assembles P5/P25/P50/P75/P95 for each output metric
  - PD adjustments use PDAdjustmentCalculator (NGFS Phase IV calibrated)
  - Convergence diagnostics: Gelman-Rubin R-hat, effective N

Version: 1.0.0
Author: Risk Analytics Platform
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy import stats

from services.pd_calculator import PDAdjustmentCalculator

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

NGFS_SCENARIOS = ["Orderly", "Disorderly", "Hot house world"]

SECTOR_EMISSION_INTENSITY_DEFAULTS: Dict[str, float] = {
    "Power Generation":   1.80,
    "Oil & Gas":          2.20,
    "Metals & Mining":    1.50,
    "Automotive":         1.10,
    "Airlines":           1.70,
    "Real Estate":        0.60,
    "Financial Services": 0.20,
    "Technology":         0.15,
    "Consumer Goods":     0.80,
    "Healthcare":         0.45,
    "Agriculture":        1.30,
    "Chemicals":          1.60,
    "Other":              0.90,
}

# Carbon price anchor for WACI cost weighting (USD/tCO2e, 2050 endpoint)
CARBON_PRICE_BASE: Dict[str, float] = {
    "Orderly":          150.0,
    "Disorderly":       220.0,
    "Hot house world":   40.0,
}

# Physical risk amplification by scenario (applied as systemic factor)
PHYSICAL_RISK_AMPLIFIER: Dict[str, float] = {
    "Orderly":          1.0,
    "Disorderly":       1.3,
    "Hot house world":  2.2,
}

# Vasicek one-factor asset correlation (Basel corporate, CRR3 Art. 153)
VASICEK_CORRELATION: float = 0.30


# ---------------------------------------------------------------------------
# DATACLASSES
# ---------------------------------------------------------------------------

@dataclass
class AssetInput:
    """Single asset/counterparty for Monte Carlo simulation."""
    id: str
    name: str
    sector: str
    exposure: float                           # EAD in currency units
    baseline_pd: float                        # 0-1
    lgd: float                                # 0-1
    emission_intensity: Optional[float] = None  # tCO2e per unit revenue
    emissions_trend: str = "Stable"           # "Improving" | "Stable" | "Deteriorating"
    transition_plan_score: Optional[int] = None  # 1-5 (5=best)
    physical_risk_score: Optional[int] = None    # 1-5 (5=highest risk)


@dataclass
class UncertaintyParams:
    """
    Parameter uncertainty specification for Monte Carlo draws.
    Sigmas are log-normal (multiplicative) unless noted as normal.
    """
    pd_sigma: float = 0.25            # PD lognormal sigma (≈±25% idiosyncratic)
    lgd_sigma: float = 0.15          # LGD normal sigma (±15% clipped [0.5,1.5])
    carbon_price_sigma: float = 0.30  # Carbon price path lognormal sigma (±30% systemic)
    physical_risk_sigma: float = 0.20 # Physical risk multiplier lognormal sigma (±20% systemic)
    exposure_sigma: float = 0.08     # Exposure (EAD) normal shock sigma (±8%)


@dataclass
class PercentileResult:
    p5: float
    p25: float
    p50: float
    p75: float
    p95: float
    mean: float
    std_dev: float

    def to_dict(self) -> Dict:
        return {
            "p5":      round(self.p5, 4),
            "p25":     round(self.p25, 4),
            "p50":     round(self.p50, 4),
            "p75":     round(self.p75, 4),
            "p95":     round(self.p95, 4),
            "mean":    round(self.mean, 4),
            "std_dev": round(self.std_dev, 4),
        }


@dataclass
class AssetLevelResult:
    id: str
    name: str
    sector: str
    exposure: float
    pd_p5: float
    pd_p25: float
    pd_p50: float
    pd_p75: float
    pd_p95: float
    el_p50: float
    el_p95: float

    def to_dict(self) -> Dict:
        return {
            "id":       self.id,
            "name":     self.name,
            "sector":   self.sector,
            "exposure": self.exposure,
            "pd": {
                "p5":  round(self.pd_p5, 6),
                "p25": round(self.pd_p25, 6),
                "p50": round(self.pd_p50, 6),
                "p75": round(self.pd_p75, 6),
                "p95": round(self.pd_p95, 6),
            },
            "el_p50": round(self.el_p50, 2),
            "el_p95": round(self.el_p95, 2),
        }


@dataclass
class MonteCarloResult:
    scenario: str
    time_horizon: int
    n_simulations: int
    n_assets: int
    total_exposure: float
    distributions: Dict[str, Dict]       # metric → PercentileResult.to_dict()
    asset_level: List[Dict]
    scenario_comparison: Dict[str, Dict]
    convergence: Dict
    methodology: Dict
    calculation_timestamp: str = field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z"
    )


# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------

def _percentile_result(arr: np.ndarray) -> PercentileResult:
    """Build PercentileResult from a 1-D NumPy array."""
    return PercentileResult(
        p5=float(np.percentile(arr, 5)),
        p25=float(np.percentile(arr, 25)),
        p50=float(np.percentile(arr, 50)),
        p75=float(np.percentile(arr, 75)),
        p95=float(np.percentile(arr, 95)),
        mean=float(np.mean(arr)),
        std_dev=float(np.std(arr)),
    )


def _gelman_rubin_rhat(arr: np.ndarray) -> float:
    """
    Split-chain Gelman-Rubin R-hat diagnostic.
    Values < 1.1 indicate convergence; < 1.05 is ideal.
    """
    n = len(arr)
    if n < 4:
        return 1.0
    half = n // 2
    c1, c2 = arr[:half], arr[half: 2 * half]
    w = (float(np.var(c1, ddof=1)) + float(np.var(c2, ddof=1))) / 2.0
    if w <= 0:
        return 1.0
    b = (half / 1) * (float(np.mean(c1)) - float(np.mean(c2))) ** 2
    var_est = ((half - 1) / half) * w + b / half
    rhat = math.sqrt(var_est / w) if w > 0 else 1.0
    return round(min(rhat, 9.99), 4)


def _effective_n(arr: np.ndarray, max_lag: int = 20) -> int:
    """Geyer (1992) initial monotone sequence estimator for effective sample size."""
    n = len(arr)
    if n < 4:
        return n
    x = arr - np.mean(arr)
    acf = np.correlate(x, x, mode="full")[n - 1:] / (np.var(x) * n)
    rho_sum = 0.0
    for k in range(1, min(max_lag, n // 4)):
        r = float(acf[k]) if k < len(acf) else 0.0
        if abs(r) < 0.05:
            break
        rho_sum += r
    ess = n / max(1.0 + 2 * rho_sum, 1.0)
    return max(1, int(round(ess)))


# ---------------------------------------------------------------------------
# ENGINE
# ---------------------------------------------------------------------------

class MonteCarloEngine:
    """
    Portfolio-Level Parameter Uncertainty Monte Carlo Engine.

    Algorithm:
      1. Compute deterministic base PD adjustments via PDAdjustmentCalculator (NGFS-calibrated).
      2. Draw N parameter scenarios:
           - PD multiplier:           lognormal(0, pd_sigma)          — idiosyncratic per asset
           - LGD multiplier:          normal(1, lgd_sigma).clip(0.5, 1.5) — idiosyncratic
           - Carbon price multiplier: lognormal(0, carbon_price_sigma)  — systemic
           - Physical risk multiplier:lognormal(0, physical_risk_sigma) — systemic
           - Exposure shock:          normal(1, exposure_sigma).clip(0.5, 2.0) — idiosyncratic
      3. Per simulation:
           - PD_adj   = base_PD × pd_mult × ph_mult_systemic,  clipped [0, 1]
           - LGD_adj  = base_LGD × lgd_mult,                   clipped [0, 1]
           - EAD_adj  = base_EAD × exp_mult,                   clipped [0.5×, 2.0×]
           - EL       = sum(EAD_adj × PD_adj × LGD_adj)
           - VaR_99.9 = Vasicek one-factor (rho=0.30, 99.9% quantile)
           - Carbon cost = sum(EAD_adj × EI × cp_mult × carbon_price_base / 1000)
           - WACI     = sum(EAD_adj × EI) / sum(EAD_adj)
      4. Collect P5/P25/P50/P75/P95 distributions across N draws.
      5. Convergence: Gelman-Rubin R-hat, effective N on EL series.
      6. Scenario comparison: deterministic median for Orderly/Disorderly/Hot house world.

    References:
      - Basel III Pillar 2 stress testing (BCBS 2023)
      - Vasicek (1987/2002) one-factor credit risk model; Basel IRBA rho=0.12-0.24
      - NGFS Phase IV scenario calibration (2023)
      - TCFD Scenario Analysis Technical Supplement (2017)
      - EBA GL/2022/16 §4.3 — climate risk forward-looking approach
      - PCAF Standard v2.0 — Weighted Average Carbon Intensity
    """

    def __init__(self, n_simulations: int = 1000, random_seed: int = 42) -> None:
        self.n_simulations = n_simulations
        self.rng = np.random.default_rng(random_seed)
        self.logger = logging.getLogger(self.__class__.__name__)

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    def _base_pd_adjustments(
        self,
        assets: List[AssetInput],
        scenario: str,
        time_horizon: int,
    ) -> np.ndarray:
        """Compute deterministic climate-adjusted PDs (M,)."""
        calc = PDAdjustmentCalculator(scenario=scenario)
        out = np.zeros(len(assets))
        for i, a in enumerate(assets):
            res = calc.calculate(
                baseline_pd=a.baseline_pd,
                sector=a.sector,
                emissions_intensity=a.emission_intensity,
                emissions_trend=a.emissions_trend,
                transition_plan_score=a.transition_plan_score,
                physical_risk_score=a.physical_risk_score,
                time_horizon=time_horizon,
            )
            out[i] = res.adjusted_pd
        return out

    @staticmethod
    def _vasicek_var(
        pd_adj: np.ndarray,
        lgd_adj: np.ndarray,
        ead_adj: np.ndarray,
        rho: float = VASICEK_CORRELATION,
        quantile: float = 0.999,
    ) -> np.ndarray:
        """
        Vasicek one-factor VaR across N simulations.
        Inputs shapes: pd_adj (N,M), lgd_adj (N,M), ead_adj (N,M).
        Returns VaR (N,).

        VaR_i = EAD_i × LGD_i × Φ((Φ^{-1}(PD_i) - √ρ × Φ^{-1}(q)) / √(1-ρ))
        Portfolio VaR = sum_i VaR_i  (asset independence across idiosyncratic)
        """
        z_q = float(stats.norm.ppf(quantile))
        pd_safe = np.clip(pd_adj, 1e-6, 1.0 - 1e-6)
        z_pd = stats.norm.ppf(pd_safe)                         # (N, M)
        conditional_pd = stats.norm.cdf(
            (z_pd - math.sqrt(rho) * z_q) / math.sqrt(1.0 - rho)
        )                                                        # (N, M)
        var_portfolio = np.sum(ead_adj * lgd_adj * conditional_pd, axis=1)  # (N,)
        return var_portfolio

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def run(
        self,
        assets: List[AssetInput],
        scenario: str = "Orderly",
        time_horizon: int = 2050,
        uncertainty: Optional[UncertaintyParams] = None,
        compare_scenarios: bool = True,
    ) -> MonteCarloResult:
        """
        Run Monte Carlo simulation for a portfolio of assets.

        Args:
            assets:           Portfolio of AssetInput objects.
            scenario:         Primary NGFS scenario: "Orderly" | "Disorderly" | "Hot house world".
            time_horizon:     Target year: 2030 | 2040 | 2050.
            uncertainty:      UncertaintyParams (defaults if None).
            compare_scenarios:Whether to include cross-scenario comparison table.

        Returns:
            MonteCarloResult with full distribution outputs.
        """
        if not assets:
            raise ValueError("MonteCarloEngine.run(): assets list must be non-empty")

        unc = uncertainty or UncertaintyParams()
        n = self.n_simulations
        m = len(assets)

        self.logger.info(
            "MC start: scenario=%s horizon=%d n=%d assets=%d", scenario, time_horizon, n, m
        )

        # ---- Vectorise base inputs ----------------------------------------
        exposures   = np.array([a.exposure   for a in assets], dtype=float)     # (M,)
        lgds_base   = np.array([a.lgd        for a in assets], dtype=float)     # (M,)
        total_exp   = float(np.sum(exposures))

        ei = np.array(
            [
                a.emission_intensity
                if a.emission_intensity is not None
                else SECTOR_EMISSION_INTENSITY_DEFAULTS.get(a.sector, 0.90)
                for a in assets
            ],
            dtype=float,
        )  # (M,)

        # ---- Base deterministic PD adjustments ----------------------------
        pd_base = self._base_pd_adjustments(assets, scenario, time_horizon)     # (M,)

        # ---- Draw parameter samples ---------------------------------------
        # Idiosyncratic PD multipliers: shape (N, M)
        pd_mult = self.rng.lognormal(mean=0.0, sigma=unc.pd_sigma,   size=(n, m))
        # Idiosyncratic LGD multipliers: shape (N, M), clipped [0.5, 1.5]
        lgd_mult = self.rng.normal(1.0, unc.lgd_sigma, size=(n, m)).clip(0.5, 1.5)
        # Idiosyncratic EAD shocks: shape (N, M), clipped [0.5, 2.0]
        exp_mult = self.rng.normal(1.0, unc.exposure_sigma, size=(n, m)).clip(0.5, 2.0)
        # Systemic carbon price multiplier: shape (N,)
        cp_mult  = self.rng.lognormal(0.0, unc.carbon_price_sigma, size=n)
        # Systemic physical risk amplifier: shape (N,)
        ph_mult  = self.rng.lognormal(0.0, unc.physical_risk_sigma, size=n)

        # Also apply NGFS scenario physical amplifier deterministically
        ph_scenario_amp = PHYSICAL_RISK_AMPLIFIER.get(scenario, 1.0)

        # ---- Per-simulation computations ---------------------------------
        # PD matrix (N, M): base × idiosyncratic × systemic physical amplifier
        pd_adj = np.clip(
            pd_base[np.newaxis, :] * pd_mult * (ph_mult[:, np.newaxis] * ph_scenario_amp),
            0.0, 1.0,
        )  # (N, M)

        # LGD matrix (N, M)
        lgd_adj = np.clip(lgds_base[np.newaxis, :] * lgd_mult, 0.0, 1.0)   # (N, M)

        # EAD matrix (N, M)
        ead_adj = exposures[np.newaxis, :] * exp_mult                        # (N, M)

        # Expected Loss (N,)
        el_matrix    = ead_adj * pd_adj * lgd_adj                            # (N, M)
        el_portfolio = np.sum(el_matrix, axis=1)                             # (N,)

        # Loss Rate (N,)
        total_ead_sim = np.sum(ead_adj, axis=1)                              # (N,)
        loss_rate     = np.where(total_ead_sim > 0, el_portfolio / total_ead_sim, 0.0)

        # Vasicek VaR 99.9% (N,)
        portfolio_var = self._vasicek_var(pd_adj, lgd_adj, ead_adj)          # (N,)

        # Vasicek VaR 95% (N,)
        portfolio_var95 = self._vasicek_var(
            pd_adj, lgd_adj, ead_adj, quantile=0.95
        )                                                                     # (N,)

        # Carbon cost (N,): sum(EAD × EI × cp_mult) × base_carbon_price / 1000
        base_cp = CARBON_PRICE_BASE.get(scenario, 150.0)
        carbon_cost = (
            np.sum(ead_adj * ei[np.newaxis, :], axis=1) * cp_mult * base_cp / 1000.0
        )  # (N,)

        # WACI — Weighted Average Carbon Intensity (N,)
        waci = np.where(
            total_ead_sim > 0,
            np.sum(ead_adj * ei[np.newaxis, :], axis=1) / total_ead_sim,
            0.0,
        )  # (N,)

        # Average adjusted PD (N,) — exposure-weighted
        avg_pd = np.where(
            total_ead_sim > 0,
            np.sum(ead_adj * pd_adj, axis=1) / total_ead_sim,
            0.0,
        )  # (N,)

        # HHI concentration index (N,)
        w = ead_adj / np.where(total_ead_sim[:, np.newaxis] > 0,
                               total_ead_sim[:, np.newaxis], 1.0)
        hhi = np.sum(w ** 2, axis=1)                                         # (N,)

        # Expected Shortfall (CVaR) at 95% — average of worst 5% EL draws
        cutoff_95 = np.percentile(el_portfolio, 95)
        tail_mask  = el_portfolio >= cutoff_95
        es_95      = float(np.mean(el_portfolio[tail_mask])) if np.any(tail_mask) else float(cutoff_95)

        # ---- Distributions -----------------------------------------------
        distributions = {
            "expected_loss":      _percentile_result(el_portfolio).to_dict(),
            "portfolio_var_999":  _percentile_result(portfolio_var).to_dict(),
            "portfolio_var_95":   _percentile_result(portfolio_var95).to_dict(),
            "carbon_cost":        _percentile_result(carbon_cost).to_dict(),
            "waci":               _percentile_result(waci).to_dict(),
            "avg_pd":             _percentile_result(avg_pd).to_dict(),
            "loss_rate":          _percentile_result(loss_rate).to_dict(),
            "concentration_hhi":  _percentile_result(hhi).to_dict(),
            "expected_shortfall_95": {
                "value": round(es_95, 4),
                "pct_of_exposure": round(es_95 / total_exp if total_exp > 0 else 0, 6),
            },
        }

        # ---- Asset-level percentile breakdown ----------------------------
        asset_level = [
            AssetLevelResult(
                id=a.id,
                name=a.name,
                sector=a.sector,
                exposure=a.exposure,
                pd_p5=float(np.percentile(pd_adj[:, i], 5)),
                pd_p25=float(np.percentile(pd_adj[:, i], 25)),
                pd_p50=float(np.percentile(pd_adj[:, i], 50)),
                pd_p75=float(np.percentile(pd_adj[:, i], 75)),
                pd_p95=float(np.percentile(pd_adj[:, i], 95)),
                el_p50=float(np.percentile(el_matrix[:, i], 50)),
                el_p95=float(np.percentile(el_matrix[:, i], 95)),
            ).to_dict()
            for i, a in enumerate(assets)
        ]

        # ---- Cross-scenario comparison (deterministic at median) ----------
        scenario_comparison: Dict[str, Dict] = {}
        if compare_scenarios:
            z_q999 = float(stats.norm.ppf(0.999))
            rho = VASICEK_CORRELATION
            for sc in NGFS_SCENARIOS:
                pd_sc  = self._base_pd_adjustments(assets, sc, time_horizon)
                el_sc  = float(np.sum(exposures * pd_sc * lgds_base))
                cp_sc  = CARBON_PRICE_BASE.get(sc, 100.0)
                cf_sc  = float(np.sum(exposures * ei) * cp_sc / 1000.0)
                waci_sc = float(np.sum(exposures * ei) / total_exp if total_exp > 0 else 0)
                pd_safe_sc  = np.clip(pd_sc, 1e-6, 1.0 - 1e-6)
                z_pd_sc     = stats.norm.ppf(pd_safe_sc)
                cond_pd_sc  = stats.norm.cdf(
                    (z_pd_sc - math.sqrt(rho) * z_q999) / math.sqrt(1.0 - rho)
                )
                var_sc = float(np.sum(exposures * lgds_base * cond_pd_sc))
                avg_pd_sc = float(np.mean(pd_sc))
                scenario_comparison[sc] = {
                    "expected_loss":      round(el_sc, 2),
                    "portfolio_var_999":  round(var_sc, 2),
                    "carbon_cost":        round(cf_sc, 2),
                    "waci":               round(waci_sc, 4),
                    "avg_pd":             round(avg_pd_sc, 6),
                    "loss_rate":          round(el_sc / total_exp if total_exp > 0 else 0, 6),
                }

        # ---- Convergence diagnostics ------------------------------------
        rhat  = _gelman_rubin_rhat(el_portfolio)
        eff_n = _effective_n(el_portfolio)
        convergence = {
            "gelman_rubin_rhat": rhat,
            "effective_n":       eff_n,
            "converged":         rhat < 1.1,
            "n_simulations":     n,
        }

        # ---- Methodology audit -----------------------------------------
        methodology = {
            "method":        "Parameter Uncertainty Monte Carlo",
            "n_simulations": n,
            "random_seed":   42,
            "pd_model":      "PDAdjustmentCalculator — NGFS Phase IV calibrated",
            "var_model":     f"Vasicek one-factor (rho={VASICEK_CORRELATION}, 99.9% confidence)",
            "es_model":      "Average loss in worst 5% simulations (CVaR 95%)",
            "carbon_model":  "PCAF-aligned WACI × scenario carbon price endpoint",
            "uncertainty_params": {
                "pd_sigma":             unc.pd_sigma,
                "lgd_sigma":            unc.lgd_sigma,
                "carbon_price_sigma":   unc.carbon_price_sigma,
                "physical_risk_sigma":  unc.physical_risk_sigma,
                "exposure_sigma":       unc.exposure_sigma,
            },
            "standards": [
                "Basel III Pillar 2 stress testing (BCBS 2023)",
                "Vasicek (2002) one-factor IRB credit risk model",
                "NGFS Phase IV scenario taxonomy (2023)",
                "TCFD Scenario Analysis Technical Supplement (2017)",
                "EBA GL/2022/16 §4.3 — climate risk forward-looking provisioning",
                "PCAF Standard v2.0 — Weighted Average Carbon Intensity (WACI)",
            ],
            "calculation_timestamp": datetime.utcnow().isoformat() + "Z",
        }

        self.logger.info(
            "MC done: el_p50=%.0f var_p50=%.0f rhat=%.3f eff_n=%d",
            distributions["expected_loss"]["p50"],
            distributions["portfolio_var_999"]["p50"],
            rhat,
            eff_n,
        )

        return MonteCarloResult(
            scenario=scenario,
            time_horizon=time_horizon,
            n_simulations=n,
            n_assets=m,
            total_exposure=total_exp,
            distributions=distributions,
            asset_level=asset_level,
            scenario_comparison=scenario_comparison,
            convergence=convergence,
            methodology=methodology,
        )
