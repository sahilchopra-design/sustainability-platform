"""
Climate Physical Risk Engine
================================
Systematically identifies, measures, and monitors financial risks from
climate-related physical hazards using the Hazard-Exposure-Vulnerability
(HEV) framework. Covers acute event-driven risks and chronic shifts.

Calculation Pipeline (5 configurable stages):
  Stage 1 -- Hazard Assessment: intensity x frequency x duration
  Stage 2 -- Exposure Assessment: asset value x exposure fraction x concentration
  Stage 3 -- Vulnerability Assessment: sector base x modifiers x adaptation x cascading
  Stage 4 -- Damage Function & Financial Impact: CVaR = Sum(H*E*V*DamageFunc)*w
  Stage 5 -- Aggregation: multi-level roll-up (asset -> security -> fund -> portfolio)

Hazard Coverage:
  Acute: Flooding, Cyclone, Heatwave, Wildfire, Extreme Precipitation,
         Severe Wind, Cold Snap
  Chronic: Sea Level Rise, Temperature Increase, Drought, Permafrost,
           Soil Degradation, Ocean Acidification

References:
  - IPCC AR6 WG2 -- Physical Climate Risk
  - MSCI Climate Value-at-Risk Methodology
  - S&P Global Physical Risk Methodology
  - BIS Working Paper 1274 -- Physical risk in credit models
  - EBA GL/2025/01 -- ESG Risk Management
  - FSB Analytical Framework (2025)
"""
from __future__ import annotations

import copy
import logging
import math
from dataclasses import asdict, dataclass, field as dc_field
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Embedded Reference Data
# ---------------------------------------------------------------------------

HAZARD_TYPES: dict[str, dict] = {
    # ---- Acute (7) ----
    "flooding": {
        "category": "acute",
        "description": "Riverine, pluvial, or flash flooding from extreme rainfall events.",
        "base_intensity_scale": (0.0, 5.0),
        "default_weight": 1.0 / 13.0,
    },
    "cyclone": {
        "category": "acute",
        "description": "Tropical cyclones, hurricanes, and typhoons (wind + storm surge).",
        "base_intensity_scale": (0.0, 5.0),
        "default_weight": 1.0 / 13.0,
    },
    "heatwave": {
        "category": "acute",
        "description": "Sustained extreme heat events exceeding regional thresholds.",
        "base_intensity_scale": (0.0, 50.0),
        "default_weight": 1.0 / 13.0,
    },
    "wildfire": {
        "category": "acute",
        "description": "Uncontrolled fire in wildland-urban interface zones.",
        "base_intensity_scale": (0.0, 1.0),
        "default_weight": 1.0 / 13.0,
    },
    "extreme_precipitation": {
        "category": "acute",
        "description": "Extreme precipitation events causing landslides or urban inundation.",
        "base_intensity_scale": (0.0, 300.0),
        "default_weight": 1.0 / 13.0,
    },
    "severe_wind": {
        "category": "acute",
        "description": "Non-cyclonic severe windstorms (derechos, tornadoes).",
        "base_intensity_scale": (0.0, 250.0),
        "default_weight": 1.0 / 13.0,
    },
    "cold_snap": {
        "category": "acute",
        "description": "Extreme cold events causing infrastructure damage and crop failure.",
        "base_intensity_scale": (-50.0, 0.0),
        "default_weight": 1.0 / 13.0,
    },
    # ---- Chronic (6) ----
    "sea_level_rise": {
        "category": "chronic",
        "description": "Long-term rise in mean sea levels affecting coastal assets.",
        "base_intensity_scale": (0.0, 2.0),
        "default_weight": 1.0 / 13.0,
    },
    "temperature_increase": {
        "category": "chronic",
        "description": "Secular increase in mean temperatures reducing productivity.",
        "base_intensity_scale": (0.0, 6.0),
        "default_weight": 1.0 / 13.0,
    },
    "drought": {
        "category": "chronic",
        "description": "Prolonged water deficit affecting agriculture and water supply.",
        "base_intensity_scale": (0.0, 1.0),
        "default_weight": 1.0 / 13.0,
    },
    "permafrost": {
        "category": "chronic",
        "description": "Permafrost thaw undermining infrastructure in high latitudes.",
        "base_intensity_scale": (0.0, 1.0),
        "default_weight": 1.0 / 13.0,
    },
    "soil_degradation": {
        "category": "chronic",
        "description": "Loss of soil fertility and increased erosion from climate shifts.",
        "base_intensity_scale": (0.0, 1.0),
        "default_weight": 1.0 / 13.0,
    },
    "ocean_acidification": {
        "category": "chronic",
        "description": "Declining ocean pH affecting marine ecosystems and fisheries.",
        "base_intensity_scale": (7.5, 8.2),
        "default_weight": 1.0 / 13.0,
    },
}

# ---------------------------------------------------------------------------
# Sector Vulnerability Matrix: 20 sectors x 13 hazards -> base vuln [0-1]
# ---------------------------------------------------------------------------

_SECTORS = [
    "Agriculture", "Forestry", "Fishing", "Mining", "Food Processing",
    "Chemicals", "Non-Metallic Minerals", "Basic Metals", "Manufacturing",
    "Energy", "Water Utilities", "Construction", "Real Estate",
    "Transport Land", "Transport Water", "Transport Air", "Finance",
    "ICT", "Tourism", "Healthcare",
]

SECTOR_VULNERABILITY_MATRIX: dict[str, dict[str, float]] = {
    "Agriculture": {
        "flooding": 0.70, "cyclone": 0.65, "heatwave": 0.80, "wildfire": 0.55,
        "extreme_precipitation": 0.75, "severe_wind": 0.50, "cold_snap": 0.70,
        "sea_level_rise": 0.30, "temperature_increase": 0.85, "drought": 0.90,
        "permafrost": 0.15, "soil_degradation": 0.90, "ocean_acidification": 0.10,
    },
    "Forestry": {
        "flooding": 0.40, "cyclone": 0.55, "heatwave": 0.70, "wildfire": 0.90,
        "extreme_precipitation": 0.45, "severe_wind": 0.60, "cold_snap": 0.35,
        "sea_level_rise": 0.10, "temperature_increase": 0.65, "drought": 0.80,
        "permafrost": 0.30, "soil_degradation": 0.75, "ocean_acidification": 0.05,
    },
    "Fishing": {
        "flooding": 0.30, "cyclone": 0.70, "heatwave": 0.40, "wildfire": 0.05,
        "extreme_precipitation": 0.25, "severe_wind": 0.60, "cold_snap": 0.35,
        "sea_level_rise": 0.55, "temperature_increase": 0.60, "drought": 0.20,
        "permafrost": 0.05, "soil_degradation": 0.05, "ocean_acidification": 0.90,
    },
    "Mining": {
        "flooding": 0.65, "cyclone": 0.45, "heatwave": 0.55, "wildfire": 0.30,
        "extreme_precipitation": 0.60, "severe_wind": 0.35, "cold_snap": 0.50,
        "sea_level_rise": 0.25, "temperature_increase": 0.40, "drought": 0.45,
        "permafrost": 0.55, "soil_degradation": 0.40, "ocean_acidification": 0.05,
    },
    "Food Processing": {
        "flooding": 0.55, "cyclone": 0.45, "heatwave": 0.50, "wildfire": 0.25,
        "extreme_precipitation": 0.50, "severe_wind": 0.30, "cold_snap": 0.40,
        "sea_level_rise": 0.20, "temperature_increase": 0.45, "drought": 0.60,
        "permafrost": 0.10, "soil_degradation": 0.55, "ocean_acidification": 0.15,
    },
    "Chemicals": {
        "flooding": 0.60, "cyclone": 0.50, "heatwave": 0.45, "wildfire": 0.35,
        "extreme_precipitation": 0.55, "severe_wind": 0.40, "cold_snap": 0.35,
        "sea_level_rise": 0.30, "temperature_increase": 0.35, "drought": 0.40,
        "permafrost": 0.15, "soil_degradation": 0.15, "ocean_acidification": 0.10,
    },
    "Non-Metallic Minerals": {
        "flooding": 0.50, "cyclone": 0.40, "heatwave": 0.45, "wildfire": 0.20,
        "extreme_precipitation": 0.50, "severe_wind": 0.35, "cold_snap": 0.30,
        "sea_level_rise": 0.20, "temperature_increase": 0.35, "drought": 0.35,
        "permafrost": 0.20, "soil_degradation": 0.25, "ocean_acidification": 0.05,
    },
    "Basic Metals": {
        "flooding": 0.55, "cyclone": 0.40, "heatwave": 0.40, "wildfire": 0.20,
        "extreme_precipitation": 0.45, "severe_wind": 0.35, "cold_snap": 0.35,
        "sea_level_rise": 0.25, "temperature_increase": 0.30, "drought": 0.30,
        "permafrost": 0.20, "soil_degradation": 0.15, "ocean_acidification": 0.05,
    },
    "Manufacturing": {
        "flooding": 0.50, "cyclone": 0.45, "heatwave": 0.40, "wildfire": 0.25,
        "extreme_precipitation": 0.45, "severe_wind": 0.40, "cold_snap": 0.35,
        "sea_level_rise": 0.25, "temperature_increase": 0.30, "drought": 0.25,
        "permafrost": 0.15, "soil_degradation": 0.10, "ocean_acidification": 0.05,
    },
    "Energy": {
        "flooding": 0.65, "cyclone": 0.80, "heatwave": 0.55, "wildfire": 0.60,
        "extreme_precipitation": 0.55, "severe_wind": 0.70, "cold_snap": 0.60,
        "sea_level_rise": 0.45, "temperature_increase": 0.40, "drought": 0.50,
        "permafrost": 0.35, "soil_degradation": 0.15, "ocean_acidification": 0.10,
    },
    "Water Utilities": {
        "flooding": 0.70, "cyclone": 0.50, "heatwave": 0.45, "wildfire": 0.20,
        "extreme_precipitation": 0.65, "severe_wind": 0.30, "cold_snap": 0.40,
        "sea_level_rise": 0.55, "temperature_increase": 0.50, "drought": 0.85,
        "permafrost": 0.25, "soil_degradation": 0.35, "ocean_acidification": 0.15,
    },
    "Construction": {
        "flooding": 0.60, "cyclone": 0.55, "heatwave": 0.50, "wildfire": 0.35,
        "extreme_precipitation": 0.55, "severe_wind": 0.50, "cold_snap": 0.45,
        "sea_level_rise": 0.35, "temperature_increase": 0.35, "drought": 0.25,
        "permafrost": 0.40, "soil_degradation": 0.35, "ocean_acidification": 0.05,
    },
    "Real Estate": {
        "flooding": 0.80, "cyclone": 0.70, "heatwave": 0.45, "wildfire": 0.65,
        "extreme_precipitation": 0.60, "severe_wind": 0.55, "cold_snap": 0.40,
        "sea_level_rise": 0.75, "temperature_increase": 0.35, "drought": 0.20,
        "permafrost": 0.50, "soil_degradation": 0.30, "ocean_acidification": 0.05,
    },
    "Transport Land": {
        "flooding": 0.65, "cyclone": 0.50, "heatwave": 0.45, "wildfire": 0.40,
        "extreme_precipitation": 0.55, "severe_wind": 0.40, "cold_snap": 0.50,
        "sea_level_rise": 0.30, "temperature_increase": 0.30, "drought": 0.15,
        "permafrost": 0.45, "soil_degradation": 0.30, "ocean_acidification": 0.05,
    },
    "Transport Water": {
        "flooding": 0.40, "cyclone": 0.75, "heatwave": 0.25, "wildfire": 0.10,
        "extreme_precipitation": 0.35, "severe_wind": 0.65, "cold_snap": 0.45,
        "sea_level_rise": 0.60, "temperature_increase": 0.25, "drought": 0.35,
        "permafrost": 0.10, "soil_degradation": 0.05, "ocean_acidification": 0.25,
    },
    "Transport Air": {
        "flooding": 0.50, "cyclone": 0.60, "heatwave": 0.40, "wildfire": 0.30,
        "extreme_precipitation": 0.45, "severe_wind": 0.70, "cold_snap": 0.45,
        "sea_level_rise": 0.25, "temperature_increase": 0.25, "drought": 0.10,
        "permafrost": 0.15, "soil_degradation": 0.05, "ocean_acidification": 0.05,
    },
    "Finance": {
        "flooding": 0.25, "cyclone": 0.20, "heatwave": 0.15, "wildfire": 0.15,
        "extreme_precipitation": 0.20, "severe_wind": 0.15, "cold_snap": 0.10,
        "sea_level_rise": 0.15, "temperature_increase": 0.10, "drought": 0.10,
        "permafrost": 0.05, "soil_degradation": 0.05, "ocean_acidification": 0.05,
    },
    "ICT": {
        "flooding": 0.35, "cyclone": 0.30, "heatwave": 0.40, "wildfire": 0.20,
        "extreme_precipitation": 0.30, "severe_wind": 0.25, "cold_snap": 0.25,
        "sea_level_rise": 0.15, "temperature_increase": 0.20, "drought": 0.10,
        "permafrost": 0.10, "soil_degradation": 0.05, "ocean_acidification": 0.05,
    },
    "Tourism": {
        "flooding": 0.55, "cyclone": 0.65, "heatwave": 0.60, "wildfire": 0.50,
        "extreme_precipitation": 0.50, "severe_wind": 0.45, "cold_snap": 0.35,
        "sea_level_rise": 0.60, "temperature_increase": 0.50, "drought": 0.40,
        "permafrost": 0.15, "soil_degradation": 0.20, "ocean_acidification": 0.30,
    },
    "Healthcare": {
        "flooding": 0.45, "cyclone": 0.40, "heatwave": 0.50, "wildfire": 0.25,
        "extreme_precipitation": 0.40, "severe_wind": 0.30, "cold_snap": 0.35,
        "sea_level_rise": 0.20, "temperature_increase": 0.35, "drought": 0.25,
        "permafrost": 0.10, "soil_degradation": 0.10, "ocean_acidification": 0.05,
    },
}

# ---------------------------------------------------------------------------
# Damage Function Coefficients per hazard type
# ---------------------------------------------------------------------------

DAMAGE_FUNCTION_COEFFICIENTS: dict[str, dict] = {
    "flooding": {
        "linear": {"slope": 0.85},
        "sigmoid": {"midpoint": 0.45, "steepness": 8.0},
        "exponential": {"base": 2.5, "scale": 0.7},
        "step": {"thresholds": [0.2, 0.4, 0.6, 0.8], "values": [0.05, 0.20, 0.50, 0.80, 1.0]},
    },
    "cyclone": {
        "linear": {"slope": 0.90},
        "sigmoid": {"midpoint": 0.50, "steepness": 7.0},
        "exponential": {"base": 2.8, "scale": 0.75},
        "step": {"thresholds": [0.25, 0.50, 0.75], "values": [0.10, 0.35, 0.70, 1.0]},
    },
    "heatwave": {
        "linear": {"slope": 0.60},
        "sigmoid": {"midpoint": 0.55, "steepness": 6.0},
        "exponential": {"base": 2.0, "scale": 0.55},
        "step": {"thresholds": [0.3, 0.6, 0.8], "values": [0.05, 0.25, 0.55, 0.85]},
    },
    "wildfire": {
        "linear": {"slope": 0.95},
        "sigmoid": {"midpoint": 0.40, "steepness": 9.0},
        "exponential": {"base": 3.0, "scale": 0.80},
        "step": {"thresholds": [0.15, 0.35, 0.60, 0.80], "values": [0.05, 0.30, 0.60, 0.90, 1.0]},
    },
    "extreme_precipitation": {
        "linear": {"slope": 0.70},
        "sigmoid": {"midpoint": 0.50, "steepness": 7.0},
        "exponential": {"base": 2.2, "scale": 0.60},
        "step": {"thresholds": [0.25, 0.50, 0.75], "values": [0.05, 0.20, 0.50, 0.80]},
    },
    "severe_wind": {
        "linear": {"slope": 0.80},
        "sigmoid": {"midpoint": 0.50, "steepness": 7.5},
        "exponential": {"base": 2.5, "scale": 0.65},
        "step": {"thresholds": [0.20, 0.45, 0.70], "values": [0.05, 0.25, 0.55, 0.85]},
    },
    "cold_snap": {
        "linear": {"slope": 0.55},
        "sigmoid": {"midpoint": 0.55, "steepness": 5.5},
        "exponential": {"base": 1.8, "scale": 0.50},
        "step": {"thresholds": [0.30, 0.60, 0.85], "values": [0.05, 0.15, 0.40, 0.70]},
    },
    "sea_level_rise": {
        "linear": {"slope": 0.75},
        "sigmoid": {"midpoint": 0.50, "steepness": 6.5},
        "exponential": {"base": 2.0, "scale": 0.60},
        "step": {"thresholds": [0.20, 0.40, 0.60, 0.80], "values": [0.05, 0.15, 0.35, 0.65, 0.90]},
    },
    "temperature_increase": {
        "linear": {"slope": 0.50},
        "sigmoid": {"midpoint": 0.60, "steepness": 5.0},
        "exponential": {"base": 1.8, "scale": 0.45},
        "step": {"thresholds": [0.25, 0.50, 0.75], "values": [0.05, 0.15, 0.35, 0.60]},
    },
    "drought": {
        "linear": {"slope": 0.65},
        "sigmoid": {"midpoint": 0.50, "steepness": 6.0},
        "exponential": {"base": 2.0, "scale": 0.55},
        "step": {"thresholds": [0.20, 0.45, 0.70], "values": [0.05, 0.20, 0.50, 0.80]},
    },
    "permafrost": {
        "linear": {"slope": 0.70},
        "sigmoid": {"midpoint": 0.45, "steepness": 7.0},
        "exponential": {"base": 2.2, "scale": 0.60},
        "step": {"thresholds": [0.25, 0.50, 0.75], "values": [0.10, 0.30, 0.60, 0.90]},
    },
    "soil_degradation": {
        "linear": {"slope": 0.55},
        "sigmoid": {"midpoint": 0.55, "steepness": 5.5},
        "exponential": {"base": 1.8, "scale": 0.50},
        "step": {"thresholds": [0.30, 0.55, 0.80], "values": [0.05, 0.20, 0.45, 0.75]},
    },
    "ocean_acidification": {
        "linear": {"slope": 0.45},
        "sigmoid": {"midpoint": 0.60, "steepness": 5.0},
        "exponential": {"base": 1.6, "scale": 0.40},
        "step": {"thresholds": [0.25, 0.50, 0.75], "values": [0.05, 0.15, 0.35, 0.60]},
    },
}

# ---------------------------------------------------------------------------
# Scenario severity multipliers (relative to SSP2-4.5 baseline = 1.0)
# ---------------------------------------------------------------------------

_SCENARIO_SEVERITY: dict[str, float] = {
    "SSP1-1.9": 0.50,
    "SSP1-2.6": 0.65,
    "SSP2-4.5": 1.00,
    "SSP3-7.0": 1.35,
    "SSP5-8.5": 1.70,
}

# Time horizon scaling (chronic hazards intensify over time, acute frequency rises)
_TIME_HORIZON_SCALE: dict[int, dict[str, float]] = {
    2030: {"acute": 1.00, "chronic": 0.70},
    2040: {"acute": 1.10, "chronic": 0.90},
    2050: {"acute": 1.20, "chronic": 1.00},
    2060: {"acute": 1.30, "chronic": 1.15},
    2070: {"acute": 1.40, "chronic": 1.30},
    2080: {"acute": 1.50, "chronic": 1.50},
    2100: {"acute": 1.70, "chronic": 1.80},
}


# ---------------------------------------------------------------------------
# Config Dataclass
# ---------------------------------------------------------------------------


@dataclass
class PhysicalRiskConfig:
    """Configuration for all 5 stages of the physical risk pipeline."""

    # Stage 1: Hazard
    hazard_intensity_source: str = "CMIP6_median"
    return_period_threshold: int = 100
    scenarios: list[str] = dc_field(default_factory=lambda: ["SSP2-4.5"])
    time_horizons: list[int] = dc_field(default_factory=lambda: [2030, 2050])
    spatial_resolution_km: float = 1.0
    ensemble_method: str = "median"
    hazard_inclusion_mask: dict[str, bool] = dc_field(default_factory=dict)

    # Stage 2: Exposure
    asset_value_basis: str = "replacement_cost"
    exposure_radius_km: float = 1.0
    concentration_penalty: float = 1.0
    asset_type_modifiers: dict[str, float] = dc_field(default_factory=dict)

    # Stage 3: Vulnerability
    sector_vulnerability_overrides: dict = dc_field(default_factory=dict)
    structural_modifiers_enabled: bool = True
    adaptation_discount_pct: float = 0.0
    cascading_risk_multiplier: float = 1.2

    # Stage 4: Damage & Financial
    hazard_weights: dict[str, float] = dc_field(default_factory=dict)
    damage_function_type: str = "sigmoid"
    damage_cap_pct: float = 100.0
    business_interruption_multiplier: float = 0.3
    discount_rate_pct: float = 3.5
    pd_sensitivity: float = 0.02
    lgd_uplift_factor: float = 0.05

    # Stage 5: Aggregation
    aggregation_function: str = "weighted_average"
    diversification_benefit_enabled: bool = True
    diversification_factor: float = 0.85
    outlier_treatment: str = "winsorize_99"


# ---------------------------------------------------------------------------
# Result Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class HazardScore:
    """Normalised hazard assessment for one hazard type at one location."""
    hazard_type: str
    category: str
    intensity: float
    frequency: float
    duration: float
    score: float


@dataclass
class ExposureResult:
    """Exposure assessment for one asset against one hazard."""
    asset_value: float
    exposure_fraction: float
    concentration_factor: float
    exposure_score: float


@dataclass
class VulnerabilityResult:
    """Vulnerability assessment for one sector-hazard pair."""
    sector: str
    base_vulnerability: float
    modifier_product: float
    adaptation_discount: float
    cascading_multiplier: float
    final_vulnerability: float


@dataclass
class DamageResult:
    """Single-hazard damage computation."""
    hazard_type: str
    hazard_score: float
    exposure_score: float
    vulnerability: float
    damage_function_output: float
    weight: float
    cvar_contribution: float


@dataclass
class PhysicalRiskResult:
    """Full physical risk assessment for one entity under one scenario / horizon."""
    entity_id: str
    entity_name: str
    entity_type: str
    scenario: str
    time_horizon: int

    hazard_scores: list[HazardScore]
    exposure: ExposureResult
    vulnerability_by_hazard: dict[str, VulnerabilityResult]
    damage_by_hazard: list[DamageResult]

    physical_cvar: float
    physical_risk_score: float
    risk_rating: str

    expected_annual_loss: float
    pd_adjustment: float
    lgd_adjustment: float

    top_hazards: list[tuple[str, float]]

    config_snapshot: dict


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class PhysicalRiskEngine:
    """Climate Physical Risk Engine implementing the 5-stage HEV pipeline."""

    def __init__(self, config: Optional[PhysicalRiskConfig] = None) -> None:
        self.config = config or PhysicalRiskConfig()
        self._validate_config()
        self._hazard_weights = self._build_hazard_weights()

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------

    def _validate_config(self) -> None:
        """Validate configuration ranges and constraints."""
        c = self.config
        if c.adaptation_discount_pct < 0 or c.adaptation_discount_pct > 50:
            raise ValueError("adaptation_discount_pct must be in [0, 50]")
        if c.damage_cap_pct < 0 or c.damage_cap_pct > 100:
            raise ValueError("damage_cap_pct must be in [0, 100]")
        if c.discount_rate_pct < 0 or c.discount_rate_pct > 20:
            raise ValueError("discount_rate_pct must be in [0, 20]")
        if c.cascading_risk_multiplier < 1.0:
            raise ValueError("cascading_risk_multiplier must be >= 1.0")
        if c.diversification_factor < 0 or c.diversification_factor > 1:
            raise ValueError("diversification_factor must be in [0, 1]")
        for s in c.scenarios:
            if s not in _SCENARIO_SEVERITY:
                raise ValueError(
                    f"Unknown scenario '{s}'. Supported: {list(_SCENARIO_SEVERITY)}"
                )
        valid_damage_types = {"linear", "sigmoid", "exponential", "step"}
        if c.damage_function_type not in valid_damage_types:
            raise ValueError(
                f"damage_function_type must be one of {valid_damage_types}"
            )
        logger.debug("PhysicalRiskConfig validated successfully")

    def _build_hazard_weights(self) -> dict[str, float]:
        """Build normalised hazard weight vector from config or defaults."""
        active = self._get_active_hazards()
        if self.config.hazard_weights:
            raw = {h: self.config.hazard_weights.get(h, 0.0) for h in active}
        else:
            raw = {h: HAZARD_TYPES[h]["default_weight"] for h in active}
        total = sum(raw.values())
        if total <= 0:
            equal_w = 1.0 / len(active) if active else 0.0
            return {h: equal_w for h in active}
        return {h: w / total for h, w in raw.items()}

    def _get_active_hazards(self) -> list[str]:
        """Return hazard types enabled by the inclusion mask (all if empty)."""
        mask = self.config.hazard_inclusion_mask
        if not mask:
            return list(HAZARD_TYPES.keys())
        return [h for h in HAZARD_TYPES if mask.get(h, True)]

    # ------------------------------------------------------------------
    # Stage 1: Hazard Assessment
    # ------------------------------------------------------------------

    def assess_hazard(
        self,
        hazard_type: str,
        asset_lat: float,
        asset_lon: float,
        scenario: str,
        time_horizon: int,
    ) -> HazardScore:
        """Compute a normalised hazard score for one hazard at one location.

        Without real CMIP6 grid data the engine uses deterministic proxy
        formulas based on latitude bands, scenario severity, and time-horizon
        progression.
        """
        meta = HAZARD_TYPES[hazard_type]
        category = meta["category"]
        severity = _SCENARIO_SEVERITY.get(scenario, 1.0)

        # Nearest time horizon bucket
        th_scale = self._time_horizon_factor(time_horizon, category)

        # Latitude-based raw intensity [0-1]
        raw_intensity = self._latitude_intensity(hazard_type, asset_lat, asset_lon)

        # Scale by scenario and time horizon
        intensity = min(1.0, raw_intensity * severity * th_scale)

        # Frequency proxy: acute hazards have discrete return-period driven
        # frequency; chronic hazards are quasi-continuous.
        if category == "acute":
            base_freq = 0.3 + 0.4 * raw_intensity  # 0.3-0.7 events/yr proxy
            frequency = min(1.0, base_freq * severity * th_scale)
        else:
            frequency = min(1.0, 0.7 * severity * th_scale)

        # Duration proxy: chronic > acute
        if category == "chronic":
            duration = min(1.0, 0.6 + 0.3 * severity)
        else:
            duration = min(1.0, 0.2 + 0.3 * raw_intensity)

        # Composite hazard score (geometric mean of three components)
        score = (intensity * frequency * duration) ** (1.0 / 3.0)
        score = max(0.0, min(1.0, score))

        return HazardScore(
            hazard_type=hazard_type,
            category=category,
            intensity=round(intensity, 4),
            frequency=round(frequency, 4),
            duration=round(duration, 4),
            score=round(score, 4),
        )

    def _latitude_intensity(
        self, hazard_type: str, lat: float, lon: float
    ) -> float:
        """Deterministic latitude-band intensity proxy for a hazard type."""
        abs_lat = abs(lat)
        # Tropical band < 23.5, temperate 23.5-60, polar > 60
        tropical_frac = max(0.0, 1.0 - abs_lat / 23.5)
        temperate_frac = max(0.0, min(1.0, (abs_lat - 23.5) / 36.5))
        polar_frac = max(0.0, (abs_lat - 60.0) / 30.0)

        # Coastal proxy: absolute longitude near multiples of 90 (crude)
        coastal_frac = max(0.0, 1.0 - min(abs(lon % 90), abs(90 - lon % 90)) / 30.0)

        if hazard_type == "flooding":
            return 0.3 + 0.4 * tropical_frac + 0.2 * coastal_frac
        elif hazard_type == "cyclone":
            # Tropical cyclone belt: 8-25 deg latitude
            belt = max(0.0, 1.0 - abs(abs_lat - 16.0) / 15.0)
            return 0.1 + 0.7 * belt + 0.1 * coastal_frac
        elif hazard_type == "heatwave":
            return 0.2 + 0.6 * tropical_frac + 0.15 * temperate_frac
        elif hazard_type == "wildfire":
            # Mediterranean + temperate dry
            med_frac = max(0.0, 1.0 - abs(abs_lat - 38.0) / 15.0)
            return 0.1 + 0.55 * med_frac + 0.2 * temperate_frac
        elif hazard_type == "extreme_precipitation":
            return 0.25 + 0.45 * tropical_frac + 0.2 * temperate_frac
        elif hazard_type == "severe_wind":
            return 0.15 + 0.35 * temperate_frac + 0.3 * tropical_frac
        elif hazard_type == "cold_snap":
            return 0.05 + 0.65 * polar_frac + 0.25 * temperate_frac
        elif hazard_type == "sea_level_rise":
            low_elev = max(0.0, coastal_frac * 0.8)
            return 0.1 + 0.6 * low_elev + 0.15 * tropical_frac
        elif hazard_type == "temperature_increase":
            return 0.3 + 0.35 * tropical_frac + 0.2 * temperate_frac
        elif hazard_type == "drought":
            # Subtropical dry belt ~25-35 deg
            dry_belt = max(0.0, 1.0 - abs(abs_lat - 30.0) / 12.0)
            return 0.15 + 0.6 * dry_belt + 0.1 * temperate_frac
        elif hazard_type == "permafrost":
            return 0.0 + 0.9 * polar_frac
        elif hazard_type == "soil_degradation":
            return 0.2 + 0.35 * tropical_frac + 0.25 * temperate_frac
        elif hazard_type == "ocean_acidification":
            return 0.25 + 0.3 * coastal_frac + 0.15 * tropical_frac
        return 0.3  # fallback

    @staticmethod
    def _time_horizon_factor(horizon: int, category: str) -> float:
        """Interpolate time horizon scaling factor."""
        horizons_sorted = sorted(_TIME_HORIZON_SCALE.keys())
        if horizon <= horizons_sorted[0]:
            return _TIME_HORIZON_SCALE[horizons_sorted[0]][category]
        if horizon >= horizons_sorted[-1]:
            return _TIME_HORIZON_SCALE[horizons_sorted[-1]][category]
        # Linear interpolation between bracketing years
        for i in range(len(horizons_sorted) - 1):
            lo, hi = horizons_sorted[i], horizons_sorted[i + 1]
            if lo <= horizon <= hi:
                lo_val = _TIME_HORIZON_SCALE[lo][category]
                hi_val = _TIME_HORIZON_SCALE[hi][category]
                frac = (horizon - lo) / (hi - lo)
                return lo_val + frac * (hi_val - lo_val)
        return 1.0  # unreachable

    # ------------------------------------------------------------------
    # Stage 2: Exposure Assessment
    # ------------------------------------------------------------------

    def assess_exposure(
        self,
        asset_value: float,
        asset_type: str,
        lat: float,
        lon: float,
        hazard_type: str,
    ) -> ExposureResult:
        """Compute exposure score for an asset against a specific hazard.

        Exposure = asset_value * exposure_fraction * concentration_factor
        """
        meta = HAZARD_TYPES[hazard_type]

        # Exposure fraction: what share of asset value is geographically
        # overlapping with the hazard footprint.
        base_fraction = self._base_exposure_fraction(hazard_type, lat, lon)

        # Asset type modifier (e.g. underground infrastructure less exposed to wind)
        type_mod = self.config.asset_type_modifiers.get(asset_type, 1.0)
        exposure_fraction = max(0.0, min(1.0, base_fraction * type_mod))

        # Concentration penalty: raised if many assets in same grid cell
        concentration_factor = max(1.0, self.config.concentration_penalty)

        exposure_score = asset_value * exposure_fraction * concentration_factor

        return ExposureResult(
            asset_value=round(asset_value, 2),
            exposure_fraction=round(exposure_fraction, 4),
            concentration_factor=round(concentration_factor, 4),
            exposure_score=round(exposure_score, 2),
        )

    @staticmethod
    def _base_exposure_fraction(hazard_type: str, lat: float, lon: float) -> float:
        """Proxy exposure fraction based on hazard type and location."""
        abs_lat = abs(lat)
        coastal_frac = max(
            0.0, 1.0 - min(abs(lon % 90), abs(90 - lon % 90)) / 30.0
        )

        if hazard_type in ("flooding", "extreme_precipitation"):
            return 0.20 + 0.40 * coastal_frac
        elif hazard_type in ("cyclone", "severe_wind"):
            belt = max(0.0, 1.0 - abs(abs_lat - 16.0) / 20.0)
            return 0.15 + 0.45 * belt
        elif hazard_type == "sea_level_rise":
            return 0.10 + 0.60 * coastal_frac
        elif hazard_type in ("heatwave", "temperature_increase"):
            return 0.30 + 0.25 * max(0.0, 1.0 - abs_lat / 40.0)
        elif hazard_type == "wildfire":
            med_frac = max(0.0, 1.0 - abs(abs_lat - 38.0) / 18.0)
            return 0.10 + 0.40 * med_frac
        elif hazard_type == "drought":
            dry = max(0.0, 1.0 - abs(abs_lat - 30.0) / 15.0)
            return 0.15 + 0.40 * dry
        elif hazard_type == "cold_snap":
            return 0.10 + 0.50 * max(0.0, (abs_lat - 50.0) / 30.0)
        elif hazard_type == "permafrost":
            return 0.05 + 0.70 * max(0.0, (abs_lat - 55.0) / 25.0)
        elif hazard_type == "soil_degradation":
            return 0.20 + 0.20 * max(0.0, 1.0 - abs_lat / 50.0)
        elif hazard_type == "ocean_acidification":
            return 0.10 + 0.35 * coastal_frac
        return 0.25  # fallback

    # ------------------------------------------------------------------
    # Stage 3: Vulnerability Assessment
    # ------------------------------------------------------------------

    def assess_vulnerability(
        self,
        sector: str,
        hazard_type: str,
        building_age_years: Optional[int] = None,
        elevation_m: Optional[float] = None,
        has_adaptation: bool = False,
    ) -> VulnerabilityResult:
        """Compute vulnerability for a sector-hazard pair with modifiers.

        Vulnerability = base * modifiers * (1 - adaptation) * cascading
        """
        # Base vulnerability from matrix (or override)
        overrides = self.config.sector_vulnerability_overrides
        if sector in overrides and hazard_type in overrides[sector]:
            base_vuln = float(overrides[sector][hazard_type])
        elif sector in SECTOR_VULNERABILITY_MATRIX:
            base_vuln = SECTOR_VULNERABILITY_MATRIX[sector].get(hazard_type, 0.3)
        else:
            base_vuln = 0.3
            logger.warning(
                "Sector '%s' not in vulnerability matrix -- using default 0.3",
                sector,
            )

        # Structural modifiers
        modifier_product = 1.0
        if self.config.structural_modifiers_enabled:
            if building_age_years is not None:
                # Older buildings are more vulnerable
                age_mod = 1.0 + max(0.0, (building_age_years - 20)) * 0.005
                age_mod = min(age_mod, 1.5)
                modifier_product *= age_mod

            if elevation_m is not None and hazard_type in (
                "flooding",
                "sea_level_rise",
                "cyclone",
            ):
                # Low elevation increases flood / SLR vulnerability
                elev_mod = max(0.5, 1.5 - elevation_m / 100.0)
                elev_mod = min(elev_mod, 2.0)
                modifier_product *= elev_mod

        # Adaptation discount
        adaptation_discount = 0.0
        if has_adaptation:
            adaptation_discount = self.config.adaptation_discount_pct / 100.0

        # Cascading risk
        cascading = self.config.cascading_risk_multiplier

        final = base_vuln * modifier_product * (1.0 - adaptation_discount) * cascading
        final = max(0.0, min(1.0, final))

        return VulnerabilityResult(
            sector=sector,
            base_vulnerability=round(base_vuln, 4),
            modifier_product=round(modifier_product, 4),
            adaptation_discount=round(adaptation_discount, 4),
            cascading_multiplier=round(cascading, 4),
            final_vulnerability=round(final, 4),
        )

    # ------------------------------------------------------------------
    # Stage 4: Damage Function & Financial Impact
    # ------------------------------------------------------------------

    def compute_damage(
        self,
        hazard_score: HazardScore,
        exposure: ExposureResult,
        vulnerability: VulnerabilityResult,
        hazard_type: str,
    ) -> DamageResult:
        """Compute damage for one hazard using the configured damage function.

        CVaR contribution = H * E_frac * V * DamageFunc(H*E_frac*V) * weight
                          * (1 + business_interruption_multiplier)
        """
        h = hazard_score.score
        e = exposure.exposure_fraction
        v = vulnerability.final_vulnerability

        combined = h * e * v
        combined = max(0.0, min(1.0, combined))

        damage_ratio = self._apply_damage_function(combined, hazard_type)
        damage_ratio = min(damage_ratio, self.config.damage_cap_pct / 100.0)

        bi_mult = 1.0 + self.config.business_interruption_multiplier
        weight = self._hazard_weights.get(hazard_type, 1.0 / 13.0)

        cvar_contribution = combined * damage_ratio * bi_mult * weight

        return DamageResult(
            hazard_type=hazard_type,
            hazard_score=round(h, 4),
            exposure_score=round(e, 4),
            vulnerability=round(v, 4),
            damage_function_output=round(damage_ratio, 4),
            weight=round(weight, 4),
            cvar_contribution=round(cvar_contribution, 6),
        )

    def _apply_damage_function(self, combined_score: float, hazard_type: str) -> float:
        """Dispatch to the configured damage curve type. Returns 0-1 damage ratio."""
        coeffs = DAMAGE_FUNCTION_COEFFICIENTS.get(hazard_type, {})
        func_type = self.config.damage_function_type
        params = coeffs.get(func_type, {})

        if func_type == "linear":
            slope = params.get("slope", 0.7)
            return max(0.0, min(1.0, slope * combined_score))

        elif func_type == "sigmoid":
            midpoint = params.get("midpoint", 0.5)
            steepness = params.get("steepness", 6.0)
            return self._sigmoid(combined_score, midpoint, steepness)

        elif func_type == "exponential":
            base = params.get("base", 2.0)
            scale = params.get("scale", 0.6)
            raw = scale * (base ** combined_score - 1.0) / (base - 1.0)
            return max(0.0, min(1.0, raw))

        elif func_type == "step":
            thresholds = params.get("thresholds", [0.25, 0.50, 0.75])
            values = params.get("values", [0.05, 0.25, 0.55, 0.85])
            return self._step_function(combined_score, thresholds, values)

        # Fallback: linear 0.7
        return max(0.0, min(1.0, 0.7 * combined_score))

    @staticmethod
    def _sigmoid(x: float, midpoint: float, steepness: float) -> float:
        """Standard logistic sigmoid normalised to [0, 1]."""
        arg = -steepness * (x - midpoint)
        # Guard against overflow
        if arg > 500:
            return 0.0
        if arg < -500:
            return 1.0
        return 1.0 / (1.0 + math.exp(arg))

    @staticmethod
    def _step_function(
        x: float, thresholds: list[float], values: list[float]
    ) -> float:
        """Step (piecewise-constant) damage function."""
        for i, t in enumerate(thresholds):
            if x < t:
                return values[i]
        return values[-1]

    # ------------------------------------------------------------------
    # Stage 5: Aggregation
    # ------------------------------------------------------------------

    def _compute_physical_cvar(
        self,
        damage_results: list[DamageResult],
        asset_value: float,
        time_horizon: int,
    ) -> float:
        """Compute aggregate physical Climate-Value-at-Risk for one entity.

        CVaR = asset_value * Sum(cvar_contributions) * discount_factor
        """
        total_cvar_frac = sum(d.cvar_contribution for d in damage_results)
        total_cvar_frac = max(0.0, min(1.0, total_cvar_frac))

        # Discount future losses to present value
        years_ahead = max(0, time_horizon - 2026)
        discount_factor = 1.0 / (
            (1.0 + self.config.discount_rate_pct / 100.0) ** years_ahead
        )

        return asset_value * total_cvar_frac * discount_factor

    # ------------------------------------------------------------------
    # Full Entity Assessment
    # ------------------------------------------------------------------

    def assess_entity(
        self,
        entity_id: str,
        entity_name: str,
        entity_type: str,
        sector: str,
        asset_value: float,
        lat: float,
        lon: float,
        scenario: Optional[str] = None,
        time_horizon: Optional[int] = None,
        building_age_years: Optional[int] = None,
        elevation_m: Optional[float] = None,
        has_adaptation: bool = False,
        asset_type: str = "general",
    ) -> PhysicalRiskResult:
        """Run the full 5-stage pipeline for a single entity.

        Parameters
        ----------
        entity_id, entity_name : str
            Identifiers for the entity being assessed.
        entity_type : str
            One of ``asset``, ``security``, ``fund``, ``portfolio``.
        sector : str
            Sector name matching :data:`SECTOR_VULNERABILITY_MATRIX` keys.
        asset_value : float
            Monetary value used for exposure (EUR).
        lat, lon : float
            Geographic coordinates.
        scenario : str, optional
            SSP scenario label; defaults to first in config.
        time_horizon : int, optional
            Target year; defaults to first in config.
        building_age_years : int, optional
            Age of the primary structure (for structural modifier).
        elevation_m : float, optional
            Site elevation in metres (for flood / SLR modifier).
        has_adaptation : bool
            Whether the entity has implemented adaptation measures.
        asset_type : str
            Asset type key for exposure modifier lookup.
        """
        scenario = scenario or self.config.scenarios[0]
        time_horizon = time_horizon or self.config.time_horizons[0]

        active_hazards = self._get_active_hazards()

        # Stage 1: Hazard assessment for every active hazard
        hazard_scores: list[HazardScore] = []
        for hz in active_hazards:
            hs = self.assess_hazard(hz, lat, lon, scenario, time_horizon)
            hazard_scores.append(hs)

        # Stage 2: Exposure (computed once; fraction varies by hazard only
        # through the base_exposure_fraction helper)
        # We compute per-hazard exposure but store a representative one.
        exposures_by_hazard: dict[str, ExposureResult] = {}
        for hz in active_hazards:
            exposures_by_hazard[hz] = self.assess_exposure(
                asset_value, asset_type, lat, lon, hz
            )
        # Representative exposure uses the average fraction
        avg_frac = (
            sum(e.exposure_fraction for e in exposures_by_hazard.values())
            / len(exposures_by_hazard)
            if exposures_by_hazard
            else 0.0
        )
        representative_exposure = ExposureResult(
            asset_value=round(asset_value, 2),
            exposure_fraction=round(avg_frac, 4),
            concentration_factor=round(
                max(1.0, self.config.concentration_penalty), 4
            ),
            exposure_score=round(
                asset_value * avg_frac * max(1.0, self.config.concentration_penalty),
                2,
            ),
        )

        # Stage 3: Vulnerability for each hazard
        vuln_by_hazard: dict[str, VulnerabilityResult] = {}
        for hz in active_hazards:
            vuln_by_hazard[hz] = self.assess_vulnerability(
                sector, hz, building_age_years, elevation_m, has_adaptation
            )

        # Stage 4: Damage for each hazard
        damage_results: list[DamageResult] = []
        for hs in hazard_scores:
            hz = hs.hazard_type
            dr = self.compute_damage(
                hs, exposures_by_hazard[hz], vuln_by_hazard[hz], hz
            )
            damage_results.append(dr)

        # Stage 5: Aggregate
        physical_cvar = self._compute_physical_cvar(
            damage_results, asset_value, time_horizon
        )

        # Physical risk score: CVaR as % of asset value, scaled 0-100
        if asset_value > 0:
            physical_risk_score = min(100.0, (physical_cvar / asset_value) * 100.0)
        else:
            physical_risk_score = 0.0

        risk_rating = self.score_to_rating(physical_risk_score)

        # Expected annual loss (simple annualisation of CVaR)
        years_ahead = max(1, time_horizon - 2026)
        expected_annual_loss = physical_cvar / years_ahead

        # PD and LGD adjustments
        pd_adjustment = (physical_risk_score / 100.0) * self.config.pd_sensitivity
        lgd_adjustment = (physical_risk_score / 100.0) * self.config.lgd_uplift_factor

        # Top hazard contributors (top 3 by CVaR contribution)
        sorted_dmg = sorted(
            damage_results, key=lambda d: d.cvar_contribution, reverse=True
        )
        top_hazards = [
            (d.hazard_type, round(d.cvar_contribution, 6)) for d in sorted_dmg[:3]
        ]

        # Config snapshot for audit
        config_snapshot = asdict(self.config)

        return PhysicalRiskResult(
            entity_id=entity_id,
            entity_name=entity_name,
            entity_type=entity_type,
            scenario=scenario,
            time_horizon=time_horizon,
            hazard_scores=hazard_scores,
            exposure=representative_exposure,
            vulnerability_by_hazard=vuln_by_hazard,
            damage_by_hazard=damage_results,
            physical_cvar=round(physical_cvar, 2),
            physical_risk_score=round(physical_risk_score, 2),
            risk_rating=risk_rating,
            expected_annual_loss=round(expected_annual_loss, 2),
            pd_adjustment=round(pd_adjustment, 6),
            lgd_adjustment=round(lgd_adjustment, 6),
            top_hazards=top_hazards,
            config_snapshot=config_snapshot,
        )

    # ------------------------------------------------------------------
    # Portfolio Assessment
    # ------------------------------------------------------------------

    def assess_portfolio(
        self,
        entities: list[dict],
        scenario: Optional[str] = None,
        time_horizon: Optional[int] = None,
    ) -> list[PhysicalRiskResult]:
        """Assess physical risk for a portfolio of entities.

        Parameters
        ----------
        entities : list[dict]
            Each dict must contain keys matching :meth:`assess_entity` params:
            ``entity_id``, ``entity_name``, ``entity_type``, ``sector``,
            ``asset_value``, ``lat``, ``lon``. Optional: ``building_age_years``,
            ``elevation_m``, ``has_adaptation``, ``asset_type``.
        scenario, time_horizon : optional
            Override per-entity defaults.

        Returns
        -------
        list[PhysicalRiskResult]
        """
        results: list[PhysicalRiskResult] = []
        for ent in entities:
            result = self.assess_entity(
                entity_id=ent["entity_id"],
                entity_name=ent["entity_name"],
                entity_type=ent.get("entity_type", "asset"),
                sector=ent["sector"],
                asset_value=ent["asset_value"],
                lat=ent["lat"],
                lon=ent["lon"],
                scenario=scenario or ent.get("scenario"),
                time_horizon=time_horizon or ent.get("time_horizon"),
                building_age_years=ent.get("building_age_years"),
                elevation_m=ent.get("elevation_m"),
                has_adaptation=ent.get("has_adaptation", False),
                asset_type=ent.get("asset_type", "general"),
            )
            results.append(result)

        if results and self.config.diversification_benefit_enabled:
            logger.info(
                "Portfolio of %d entities assessed; diversification factor %.2f applied to aggregation",
                len(results),
                self.config.diversification_factor,
            )

        return results

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def score_to_rating(score: float) -> str:
        """Convert a 0-100 physical risk score to a categorical rating."""
        if score < 20:
            return "Very Low"
        if score < 40:
            return "Low"
        if score < 60:
            return "Medium"
        if score < 80:
            return "High"
        return "Very High"
