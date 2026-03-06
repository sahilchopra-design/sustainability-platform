"""
Real Estate Climate Value-at-Risk (CLVaR) Engine - RICS VPS4 / IVS compliant
Production-grade CLVaR engine aligned with RICS VPS4, IVS 2024, CRREM v2.0, TCFD.
Physical CLVaR: depth-damage functions, hazard scoring, climate amplification.
Transition CLVaR: EPC gap analysis, retrofit capex, carbon price trajectories.
Monte Carlo: 10,000-simulation stochastic model for probabilistic VaR.
Author: Risk Analytics Platform | Version: 2.0.0
"""

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Dict, List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class ClimateScenario(Enum):
    NZE_1_5C = "NZE_1.5C"       # SSP1-1.9 / IEA NZE 2050  ~ 1.5C by 2100
    BELOW_2C = "BELOW_2C"        # SSP1-2.6 / IEA SDS       ~ 1.8C by 2100
    NDC_2_5C = "NDC_2.5C"        # SSP2-4.5 / IEA STEPS     ~ 2.5C by 2100
    CURRENT_POLICIES_3C = "CURRENT_POLICIES_3C"  # SSP5-8.5 ~ 3.0C+ by 2100


class PropertyType(Enum):
    OFFICE = "office"
    RETAIL = "retail"
    INDUSTRIAL = "industrial"
    MULTIFAMILY = "multifamily"
    HOTEL = "hotel"
    DATA_CENTER = "data_center"
    LOGISTICS = "logistics"
    MIXED_USE = "mixed_use"


class HazardType(Enum):
    FLOOD = "flood"
    HEAT = "heat"
    WILDFIRE = "wildfire"
    SEA_LEVEL_RISE = "sea_level_rise"
    SUBSIDENCE = "subsidence"
    DROUGHT = "drought"
    CYCLONE = "cyclone"


@dataclass
class PhysicalRiskInputs:
    """Physical climate hazard exposure data. Sources: EA Flood Maps, JBA, WRI Aqueduct."""
    flood_zone: str                # "A" high, "B" medium, "C" low, "X" minimal
    flood_depth_100yr_m: Decimal   # 1-in-100-year flood depth in metres
    heat_days_above_35c: int       # Annual days above 35 degrees C
    wildfire_proximity_km: Decimal # Distance to wildfire-prone area (km)
    coastal_proximity_km: Decimal  # Distance to coastline (km)
    subsidence_risk: str           # "very_high","high","medium","low","negligible"
    water_stress_score: Decimal    # WRI Aqueduct score 0.0-5.0


@dataclass
class TransitionRiskInputs:
    """Regulatory and market transition risk data. Sources: MEES, EU EPBD, CRREM."""
    current_epc_rating: str              # "A+","A","B","C","D","E","F","G"
    energy_intensity_kwh_m2: Decimal     # kWh/m2/yr
    carbon_intensity_kgco2_m2: Decimal   # kgCO2e/m2/yr
    minimum_epc_required_2030: str       # MEES 2030 minimum EPC rating
    minimum_epc_required_2033: str       # MEES 2033 minimum EPC rating
    retrofit_feasibility: str            # "high","medium","low","not_feasible"
    current_green_certification: Optional[str] = None


@dataclass
class PropertyValuationInputs:
    """Core valuation parameters for CLVaR monetisation."""
    property_type: PropertyType
    country_iso: str            # ISO 3166-1 alpha-2 e.g. "GB","DE","US"
    region: str                 # NUTS2 region or US state
    floor_area_m2: Decimal      # Gross internal area in square metres
    current_market_value: Decimal
    year_built: int
    last_refurbishment_year: Optional[int]


@dataclass
class CLVaRResult:
    """
    Comprehensive Climate Value-at-Risk result. Aligned with RICS VPS4 para 3.4.
    All percentage fields are fractional (e.g. -0.15 = -15% value reduction).
    """
    physical_var_pct: Decimal       # Physical risk value impact
    transition_var_pct: Decimal     # Transition risk value impact
    combined_clvar_pct: Decimal     # Combined CLVaR (two-asset, rho=0.45)
    combined_clvar_gbp: Decimal     # Monetised CLVaR in local currency
    green_premium_pct: Decimal      # Green premium for certified assets
    brown_discount_pct: Decimal     # Brown discount for EPC-deficient assets
    stranding_risk_year: Optional[int]  # Year of regulatory stranding
    is_already_stranded: bool
    p5: Decimal                     # 5th percentile Monte Carlo
    p25: Decimal
    p50: Decimal                    # Median Monte Carlo
    p75: Decimal
    p95: Decimal                    # 95th percentile Monte Carlo
    var_95: Decimal                 # VaR at 95% confidence
    var_99: Decimal                 # VaR at 99% confidence
    hazard_contributions: Dict[str, Decimal] = field(default_factory=dict)
    validation_summary: Dict = field(default_factory=dict)
    calculation_timestamp: datetime = field(default_factory=datetime.utcnow)
    methodology_version: str = "CLVaR-Engine-v2.0.0"


class RECLVaREngine:
    """RECLVaREngine: RICS VPS4-aligned CLVaR engine with Monte Carlo simulation."""
    PHYSICAL_RISK_MULTIPLIERS: Dict[HazardType, Dict[str, float]] = {
        HazardType.FLOOD: {"catastrophic": -0.35, "severe": -0.22, "high": -0.14, "moderate": -0.08, "low": -0.03, "negligible": 0.00},
        HazardType.HEAT: {"catastrophic": -0.12, "severe": -0.08, "high": -0.05, "moderate": -0.03, "low": -0.01, "negligible": 0.00},
        HazardType.WILDFIRE: {"catastrophic": -0.28, "severe": -0.16, "high": -0.09, "moderate": -0.04, "low": -0.015, "negligible": 0.00},
        HazardType.SEA_LEVEL_RISE: {"catastrophic": -0.45, "severe": -0.25, "high": -0.12, "moderate": -0.05, "low": -0.015, "negligible": 0.00},
        HazardType.SUBSIDENCE: {"catastrophic": -0.20, "severe": -0.13, "high": -0.07, "moderate": -0.03, "low": -0.01, "negligible": 0.00},
        HazardType.DROUGHT: {"catastrophic": -0.10, "severe": -0.06, "high": -0.04, "moderate": -0.02, "low": -0.005, "negligible": 0.00},
        HazardType.CYCLONE: {"catastrophic": -0.30, "severe": -0.18, "high": -0.10, "moderate": -0.05, "low": -0.015, "negligible": 0.00},
    }
    BROWN_DISCOUNT_TABLE: Dict[int, float] = {0: 0.000, 1: 0.035, 2: 0.075, 3: 0.120, 4: 0.180, 5: 0.250, 6: 0.320}
    GREEN_PREMIUM_BY_CERT: Dict[str, float] = {
        "BREEAM_Outstanding": 0.100, "BREEAM_Excellent": 0.080, "BREEAM_VeryGood": 0.050, "BREEAM_Good": 0.025,
        "LEED_Platinum": 0.070, "LEED_Gold": 0.050, "LEED_Silver": 0.025,
        "WELL_Platinum": 0.060, "WELL_Gold": 0.040, "NABERS_6Star": 0.085,
        "ENERGY_STAR": 0.035, "EPC_Aplus": 0.040, "EPC_A": 0.025,
    }
    RETROFIT_CAPEX_PER_M2: Dict[int, float] = {1: 85.0, 2: 175.0, 3: 290.0, 4: 420.0, 5: 580.0, 6: 750.0}
    CARBON_PRICE_TRAJECTORY: Dict[ClimateScenario, Dict[int, float]] = {
        ClimateScenario.NZE_1_5C: {2024: 65, 2025: 80, 2026: 95, 2027: 115, 2028: 135, 2029: 160, 2030: 190, 2035: 320, 2040: 500, 2045: 700, 2050: 900},
        ClimateScenario.BELOW_2C: {2024: 55, 2025: 65, 2026: 78, 2027: 92, 2028: 108, 2029: 125, 2030: 145, 2035: 225, 2040: 340, 2045: 470, 2050: 600},
        ClimateScenario.NDC_2_5C: {2024: 40, 2025: 47, 2026: 54, 2027: 62, 2028: 71, 2029: 80, 2030: 90, 2035: 130, 2040: 180, 2045: 240, 2050: 310},
        ClimateScenario.CURRENT_POLICIES_3C: {2024: 28, 2025: 32, 2026: 36, 2027: 40, 2028: 44, 2029: 48, 2030: 52, 2035: 70, 2040: 90, 2045: 110, 2050: 130},
    }
    SLR_PROJECTIONS: Dict[ClimateScenario, Dict[int, float]] = {
        ClimateScenario.NZE_1_5C:            {2030: 0.08, 2040: 0.15, 2050: 0.28, 2060: 0.38, 2070: 0.46},
        ClimateScenario.BELOW_2C:            {2030: 0.10, 2040: 0.19, 2050: 0.36, 2060: 0.50, 2070: 0.63},
        ClimateScenario.NDC_2_5C:            {2030: 0.12, 2040: 0.24, 2050: 0.48, 2060: 0.68, 2070: 0.88},
        ClimateScenario.CURRENT_POLICIES_3C: {2030: 0.15, 2040: 0.30, 2050: 0.62, 2060: 0.90, 2070: 1.20},
    }
    CLIMATE_AMPLIFICATION: Dict[ClimateScenario, Dict[str, float]] = {
        ClimateScenario.NZE_1_5C:            {"short": 1.05, "medium": 1.12, "long": 1.20},
        ClimateScenario.BELOW_2C:            {"short": 1.10, "medium": 1.22, "long": 1.38},
        ClimateScenario.NDC_2_5C:            {"short": 1.18, "medium": 1.40, "long": 1.65},
        ClimateScenario.CURRENT_POLICIES_3C: {"short": 1.28, "medium": 1.60, "long": 2.10},
    }
    EPC_NUMERIC: Dict[str, int] = {"A+": 0, "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7}
    ENERGY_INTENSITY_BENCHMARKS: Dict[PropertyType, float] = {
        PropertyType.OFFICE: 220.0, PropertyType.RETAIL: 310.0,
        PropertyType.INDUSTRIAL: 140.0, PropertyType.MULTIFAMILY: 155.0,
        PropertyType.HOTEL: 380.0, PropertyType.DATA_CENTER: 800.0,
        PropertyType.LOGISTICS: 95.0, PropertyType.MIXED_USE: 245.0,
    }
    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("RECLVaREngine initialised -- CLVaR-Engine-v2.0.0")

    def _get_time_horizon_band(self, h: int) -> str:
        return "short" if h <= 5 else ("medium" if h <= 15 else "long")

    def _interpolate_carbon_price(self, scenario: ClimateScenario, yr: int) -> float:
        """Linear interpolation of carbon price for any target year."""
        traj = self.CARBON_PRICE_TRAJECTORY[scenario]
        ys = sorted(traj.keys())
        if yr <= ys[0]: return traj[ys[0]]
        if yr >= ys[-1]: return traj[ys[-1]]
        for i in range(len(ys) - 1):
            y0, y1 = ys[i], ys[i + 1]
            if y0 <= yr <= y1:
                return traj[y0] + (yr - y0) / (y1 - y0) * (traj[y1] - traj[y0])
        return traj[ys[-1]]

    def _interpolate_slr(self, scenario: ClimateScenario, yr: int) -> float:
        """Linear interpolation of sea level rise for any target year."""
        data = self.SLR_PROJECTIONS[scenario]
        ys = sorted(data.keys())
        if yr <= ys[0]: return data[ys[0]] * (yr / ys[0])
        if yr >= ys[-1]: return data[ys[-1]]
        for i in range(len(ys) - 1):
            y0, y1 = ys[i], ys[i + 1]
            if y0 <= yr <= y1:
                return data[y0] + (yr - y0) / (y1 - y0) * (data[y1] - data[y0])
        return data[ys[-1]]

    def _epc_numeric(self, r: str) -> int:
        return self.EPC_NUMERIC.get(r.upper(), 7)

    def _epc_gap(self, current: str, required: str) -> int:
        """Return EPC grades below required minimum (0 = compliant)."""
        return max(0, self._epc_numeric(current) - self._epc_numeric(required))

    def _flood_severity(self, zone: str, depth: float) -> str:
        z = zone.upper()
        if z == "A":
            if depth >= 2.0: return "catastrophic"
            elif depth >= 1.0: return "severe"
            elif depth >= 0.5: return "high"
            else: return "moderate"
        elif z == "B":
            if depth >= 1.0: return "high"
            elif depth >= 0.3: return "moderate"
            else: return "low"
        elif z == "C": return "low"
        return "negligible"

    def _heat_severity(self, days: int) -> str:
        if days >= 60: return "catastrophic"
        elif days >= 40: return "severe"
        elif days >= 25: return "high"
        elif days >= 15: return "moderate"
        elif days >= 5: return "low"
        return "negligible"

    def _wildfire_severity(self, km: float) -> str:
        if km < 5.0: return "catastrophic"
        elif km < 10.0: return "severe"
        elif km < 15.0: return "high"
        elif km < 25.0: return "moderate"
        elif km < 40.0: return "low"
        return "negligible"

    def _slr_severity(self, ckm: float, slr: float) -> str:
        if ckm > 50.0: return "negligible"
        if ckm <= 1.0 and slr >= 0.40: return "catastrophic"
        elif ckm <= 5.0 and slr >= 0.30: return "severe"
        elif ckm <= 10.0 and slr >= 0.25: return "high"
        elif ckm <= 20.0 and slr >= 0.20: return "moderate"
        elif ckm <= 50.0: return "low"
        return "negligible"

    def _subsidence_severity(self, risk: str) -> str:
        m = {"very_high": "catastrophic", "high": "severe", "medium": "moderate", "low": "low", "negligible": "negligible"}
        return m.get(risk.lower(), "negligible")

    def _drought_severity(self, wsi: float) -> str:
        if wsi >= 4.5: return "catastrophic"
        elif wsi >= 4.0: return "severe"
        elif wsi >= 3.0: return "high"
        elif wsi >= 2.0: return "moderate"
        elif wsi >= 1.0: return "low"
        return "negligible"


    def calculate_physical_clvar(
        self,
        inputs: PhysicalRiskInputs,
        scenario: ClimateScenario,
        time_horizon: int,
    ) -> Dict:
        """
        Calculate physical climate risk value impact per hazard.

        Flood: depth-damage function addon = max(-(depth*0.15+0.05)*0.5, -0.10) for Zone A/B.
        Heat:  cooling cost uplift = heat_days * 0.0015 * blending factor 0.3.
        Wildfire: proximity-based severity (<5km=catastrophic, <15km=high, etc.).
        SLR: time-scaled by ratio of horizon-year SLR to 2050 SLR baseline.
        All hazards amplified by CLIMATE_AMPLIFICATION[scenario][horizon_band].
        Aggregated with covariance-adjusted formula: rho=0.35 between hazards.
        """
        hband = self._get_time_horizon_band(time_horizon)
        amp   = self.CLIMATE_AMPLIFICATION[scenario][hband]
        hyear = datetime.utcnow().year + time_horizon
        hi: Dict[HazardType, float] = {}

        depth = float(inputs.flood_depth_100yr_m)
        fsev  = self._flood_severity(inputs.flood_zone, depth)
        bflood = self.PHYSICAL_RISK_MULTIPLIERS[HazardType.FLOOD][fsev]
        if inputs.flood_zone.upper() in ("A", "B") and depth > 0:
            dda = max(-(depth * 0.15 + 0.05) * 0.5, -0.10)
        else:
            dda = 0.0
        hi[HazardType.FLOOD] = max(bflood + dda, -0.45)

        hsev  = self._heat_severity(inputs.heat_days_above_35c)
        bheat = self.PHYSICAL_RISK_MULTIPLIERS[HazardType.HEAT][hsev]
        cool  = max(-(inputs.heat_days_above_35c * 0.0015), -0.06) * 0.3
        hi[HazardType.HEAT] = max(bheat + cool, -0.15)

        wfsev = self._wildfire_severity(float(inputs.wildfire_proximity_km))
        hi[HazardType.WILDFIRE] = self.PHYSICAL_RISK_MULTIPLIERS[HazardType.WILDFIRE][wfsev]

        slrm    = self._interpolate_slr(scenario, hyear)
        slr2050 = self._interpolate_slr(scenario, 2050)
        slrsev  = self._slr_severity(float(inputs.coastal_proximity_km), slrm)
        slrbase = self.PHYSICAL_RISK_MULTIPLIERS[HazardType.SEA_LEVEL_RISE][slrsev]
        hi[HazardType.SEA_LEVEL_RISE] = slrbase * (slrm / slr2050 if slr2050 > 0 else 1.0)

        ssev = self._subsidence_severity(inputs.subsidence_risk)
        hi[HazardType.SUBSIDENCE] = self.PHYSICAL_RISK_MULTIPLIERS[HazardType.SUBSIDENCE][ssev]

        dsev = self._drought_severity(float(inputs.water_stress_score))
        hi[HazardType.DROUGHT] = self.PHYSICAL_RISK_MULTIPLIERS[HazardType.DROUGHT][dsev]

        hi[HazardType.CYCLONE] = 0.0

        amp_hi: Dict[HazardType, float] = {h: v * amp for h, v in hi.items()}

        neg = [v for v in amp_hi.values() if v < 0]
        if neg:
            ss = sum(v ** 2 for v in neg)
            cx = 0.35 * sum(neg[a] * neg[b] for a in range(len(neg)) for b in range(len(neg)) if a != b)
            agg = -math.sqrt(max(ss + cx, ss * 0.5))
        else:
            agg = 0.0

        return {
            "hazard_impacts":              {h.value: round(v, 6) for h, v in amp_hi.items()},
            "flood_severity":              fsev,
            "flood_depth_damage_addon":    round(dda, 6),
            "slr_projection_m":            round(slrm, 4),
            "climate_amplification_factor": round(amp, 4),
            "horizon_band":                hband,
            "physical_var_pct":            round(max(agg, -0.60), 6),
        }


    def calculate_transition_clvar(
        self,
        inputs: TransitionRiskInputs,
        val_inputs: PropertyValuationInputs,
        scenario: ClimateScenario,
        time_horizon: int,
    ) -> Dict:
        """
        Calculate transition risk: EPC stranding, retrofit capex, carbon cost.

        1. Applicable EPC minimum: 2030 standard if horizon < 2033, else 2033 standard.
        2. Brown discount from BROWN_DISCOUNT_TABLE by EPC grade gap.
        3. Retrofit capex: DEFRA/JLL benchmarks scaled by feasibility factor
           (high=1.0x, medium=1.20x, low=1.55x, not_feasible=2.0x notional).
        4. Stranding year: not_feasible assets strand at regulation date;
           low-feasibility assets at 2033 if gap exists.
        5. Carbon cost NPV: 5% real discount rate, 2% annual intensity improvement.
        6. Green premium from GREEN_PREMIUM_BY_CERT for certified assets.
        7. Weighted: 50% brown discount + 30% retrofit NPV + 20% carbon NPV.
        8. Stranding penalty: -25% (<=2yr), -15% (<=5yr), -8% (>5yr).
        """
        cyear = datetime.utcnow().year
        hyear = cyear + time_horizon
        amin  = (inputs.minimum_epc_required_2033 if hyear >= 2033
                 else inputs.minimum_epc_required_2030)
        g30   = self._epc_gap(inputs.current_epc_rating, inputs.minimum_epc_required_2030)
        g33   = self._epc_gap(inputs.current_epc_rating, inputs.minimum_epc_required_2033)
        gapp  = self._epc_gap(inputs.current_epc_rating, amin)
        bd    = self.BROWN_DISCOUNT_TABLE.get(min(gapp, 6), 0.320)
        fa    = float(val_inputs.floor_area_m2)
        mv    = float(val_inputs.current_market_value)

        if gapp > 0:
            bc   = self.RETROFIT_CAPEX_PER_M2.get(min(gapp, 6), 750.0)
            fm   = {"high": 1.0, "medium": 1.20, "low": 1.55, "not_feasible": 2.0}.get(
                       inputs.retrofit_feasibility.lower(), 1.20)
            rcrm = bc * fm
            rtot = rcrm * fa
        else:
            rcrm = 0.0
            rtot = 0.0

        rpct = -(rtot / mv) if mv > 0 else 0.0

        sy: Optional[int] = None
        if inputs.retrofit_feasibility.lower() == "not_feasible" and gapp > 0:
            sy = 2030 if g30 > 0 else (2033 if g33 > 0 else None)
        elif gapp > 0 and inputs.retrofit_feasibility.lower() == "low":
            sy = 2033

        ci     = float(inputs.carbon_intensity_kgco2_m2)
        ctpa   = (ci * fa) / 1000.0
        npvc   = 0.0
        for yr in range(1, time_horizon + 1):
            cp    = self._interpolate_carbon_price(scenario, cyear + yr)
            impv  = max(0.5, (1 - 0.02) ** yr)
            npvc += (ctpa * cp * impv) / (1.05 ** yr)

        cpct = -(npvc / mv) if mv > 0 else 0.0
        gp   = 0.0
        if inputs.current_green_certification:
            gp = self.GREEN_PREMIUM_BY_CERT.get(inputs.current_green_certification, 0.0)

        tv = (carbon_pct_mv := cpct) * 0.4 if gapp == 0 else (
            -(bd * 0.50) + (rpct * 0.30) + (cpct * 0.20)
        )

        if sy is not None:
            yts = max(0, sy - cyear)
            tv += -0.25 if yts <= 2 else (-0.15 if yts <= 5 else -0.08)

        tv = max(tv, -0.60)

        return {
            "epc_gap_to_2030_minimum": g30,
            "epc_gap_to_2033_minimum": g33,
            "applicable_epc_gap":      gapp,
            "applicable_minimum_epc":  amin,
            "brown_discount_pct":      round(-bd, 6),
            "green_premium_pct":       round(gp, 6),
            "retrofit_cost_per_m2":    round(rcrm, 2),
            "total_retrofit_cost":     round(rtot, 2),
            "retrofit_cost_as_pct_mv": round(rpct, 6),
            "npv_carbon_cost":         round(npvc, 2),
            "carbon_cost_as_pct_mv":   round(cpct, 6),
            "stranding_year":          sy,
            "transition_var_pct":      round(tv, 6),
            "retrofit_feasibility":    inputs.retrofit_feasibility,
        }


    def run_monte_carlo(
        self,
        physical_inputs: PhysicalRiskInputs,
        transition_inputs: TransitionRiskInputs,
        val_inputs: PropertyValuationInputs,
        scenario: ClimateScenario,
        time_horizon: int = 10,
        n_simulations: int = 10_000,
        random_seed: Optional[int] = 42,
    ) -> Dict:
        """
        Monte Carlo simulation for probabilistic CLVaR distribution.

        Stochastic parameters:
          - Flood depth:    log-normal, sigma=0.20 (approx +/-20%)
          - Carbon price:   log-normal, sigma=0.30 (approx +/-30%)
          - Retrofit cost:  normal, scale=0.25 clipped [0.5, 2.0] (approx +/-25%)
          - EPC compliance: uniform [0.85, 1.15] (approx +/-15%)
          - Heat days:      normal, scale=20% of mean
          - SLR:            log-normal, sigma=0.15 (approx +/-15%)
          - Water stress:   normal, scale=0.3

        Physical + transition combined at rho=0.50.
        Returns dict with p5, p25, p50, p75, p95, var_95, var_99.
        """
        rng   = np.random.default_rng(random_seed)
        cyear = datetime.utcnow().year
        hyear = cyear + time_horizon
        bfd   = float(physical_inputs.flood_depth_100yr_m)
        bhd   = physical_inputs.heat_days_above_35c
        bck   = float(physical_inputs.coastal_proximity_km)
        bws   = float(physical_inputs.water_stress_score)
        mv    = float(val_inputs.current_market_value)
        fa    = float(val_inputs.floor_area_m2)
        ci    = float(transition_inputs.carbon_intensity_kgco2_m2)
        bslr  = self._interpolate_slr(scenario, hyear)
        bcp   = self._interpolate_carbon_price(scenario, hyear)
        s2050 = self._interpolate_slr(scenario, 2050)
        egv   = self._epc_gap(transition_inputs.current_epc_rating, transition_inputs.minimum_epc_required_2030)
        bbd   = self.BROWN_DISCOUNT_TABLE.get(min(egv, 6), 0.0)
        brc   = self.RETROFIT_CAPEX_PER_M2.get(min(egv, 6), 0.0)
        amp   = self.CLIMATE_AMPLIFICATION[scenario][self._get_time_horizon_band(time_horizon)]

        fd_s  = rng.lognormal(math.log(max(bfd, 0.01)),  0.20, n_simulations)
        hd_s  = rng.normal(bhd, max(bhd * 0.20, 1.0),   n_simulations).clip(0)
        sl_s  = rng.lognormal(math.log(max(bslr, 0.01)), 0.15, n_simulations)
        cp_s  = rng.lognormal(math.log(max(bcp,  1.0)),  0.30, n_simulations)
        rc_s  = rng.normal(1.0, 0.25, n_simulations).clip(0.5, 2.0)
        ep_s  = rng.uniform(0.85, 1.15, n_simulations)
        ws_s  = rng.normal(bws, 0.3, n_simulations).clip(0.0, 5.0)

        wfvst = self.PHYSICAL_RISK_MULTIPLIERS[HazardType.WILDFIRE][
            self._wildfire_severity(float(physical_inputs.wildfire_proximity_km))]
        svst  = self.PHYSICAL_RISK_MULTIPLIERS[HazardType.SUBSIDENCE][
            self._subsidence_severity(physical_inputs.subsidence_risk)]

        com = np.zeros(n_simulations)
        for i in range(n_simulations):
            fv = self.PHYSICAL_RISK_MULTIPLIERS[HazardType.FLOOD][
                self._flood_severity(physical_inputs.flood_zone, fd_s[i])]
            if physical_inputs.flood_zone.upper() in ("A", "B") and fd_s[i] > 0:
                fv += max(-(fd_s[i] * 0.15 + 0.05) * 0.5, -0.10)
                fv  = max(fv, -0.45)
            hv = self.PHYSICAL_RISK_MULTIPLIERS[HazardType.HEAT][self._heat_severity(int(hd_s[i]))]
            sv = self.PHYSICAL_RISK_MULTIPLIERS[HazardType.SEA_LEVEL_RISE][
                self._slr_severity(bck, sl_s[i])]
            sv *= sl_s[i] / s2050 if s2050 > 0 else 1.0
            dv = self.PHYSICAL_RISK_MULTIPLIERS[HazardType.DROUGHT][self._drought_severity(ws_s[i])]
            nv = [v for v in [fv, hv, sv, wfvst, dv, svst] if v < 0]
            if nv:
                ss = sum(v**2 for v in nv)
                cx = 0.35 * sum(nv[a]*nv[b] for a in range(len(nv)) for b in range(len(nv)) if a!=b)
                pv = -math.sqrt(max(ss+cx, ss*0.5))
            else:
                pv = 0.0
            pv  = max(pv * amp, -0.60)
            bv  = -min(bbd * ep_s[i], 0.60)
            rv  = -(brc * rc_s[i] * fa / mv) * 0.30 if mv > 0 else 0.0
            ccv = -((ci * fa / 1000.0) * cp_s[i] * min(time_horizon, 10) * 0.6 / mv) * 0.20 if mv > 0 else 0.0
            tv  = max(bv + rv + ccv, -0.60)
            if pv < 0 and tv < 0:
                c = -math.sqrt(pv**2 + tv**2 + 2*0.50*abs(pv)*abs(tv))
            else:
                c = pv + tv
            com[i] = max(c, -0.80)

        return {
            "n_simulations": n_simulations,
            "p5":    round(float(np.percentile(com, 5)),  6),
            "p25":   round(float(np.percentile(com, 25)), 6),
            "p50":   round(float(np.percentile(com, 50)), 6),
            "p75":   round(float(np.percentile(com, 75)), 6),
            "p95":   round(float(np.percentile(com, 95)), 6),
            "var_95": round(float(np.percentile(com, 5)),  6),
            "var_99": round(float(np.percentile(com, 1)),  6),
            "mean":   round(float(np.mean(com)),  6),
            "std_dev": round(float(np.std(com)), 6),
        }


    def calculate_clvar(
        self,
        physical_inputs: PhysicalRiskInputs,
        transition_inputs: TransitionRiskInputs,
        val_inputs: PropertyValuationInputs,
        scenario: ClimateScenario,
        time_horizon: int = 10,
        run_mc: bool = True,
        mc_simulations: int = 10_000,
    ) -> CLVaRResult:
        """
        Full CLVaR calculation orchestrator.

        Execution order:
          1. Physical CLVaR (deterministic: depth-damage + amplification)
          2. Transition CLVaR (EPC gap + retrofit capex + carbon NPV)
          3. Combined CLVaR (two-asset VaR at rho=0.45, net of green premium)
          4. Monte Carlo percentile distribution (if run_mc=True)
          5. RICS VPS4 / IVS 2024 compliant validation summary

        Args:
            physical_inputs:   Physical hazard exposure data
            transition_inputs: EPC and carbon transition risk data
            val_inputs:        Property valuation parameters
            scenario:          IPCC-aligned ClimateScenario enum value
            time_horizon:      Analysis period in years (1-30)
            run_mc:            Whether to run Monte Carlo simulation (default True)
            mc_simulations:    Number of Monte Carlo iterations (default 10,000)

        Returns:
            CLVaRResult with all outputs and RICS VPS4 compliant validation_summary.
        """
        self.logger.info("CLVaR start: type=%s scenario=%s horizon=%d",
                         val_inputs.property_type.value, scenario.value, time_horizon)
        cyear = datetime.utcnow().year

        phys     = self.calculate_physical_clvar(physical_inputs, scenario, time_horizon)
        ppct     = Decimal(str(phys["physical_var_pct"]))
        trans    = self.calculate_transition_clvar(transition_inputs, val_inputs, scenario, time_horizon)
        tpct     = Decimal(str(trans["transition_var_pct"]))
        gpct     = Decimal(str(trans["green_premium_pct"]))
        bpct     = Decimal(str(trans["brown_discount_pct"]))

        pv, tv = float(ppct), float(tpct)
        if pv < 0 and tv < 0:
            raw = -math.sqrt(pv**2 + tv**2 + 2*0.45*abs(pv)*abs(tv))
        else:
            raw = pv + tv

        final = max(raw + float(gpct), -0.80)
        cpct  = Decimal(str(round(final, 6)))
        cgbp  = Decimal(str(round(float(val_inputs.current_market_value) * final, 2)))

        sy: Optional[int] = trans.get("stranding_year")
        is_s = (sy is not None and sy <= cyear) or (
            self._epc_gap(transition_inputs.current_epc_rating,
                          transition_inputs.minimum_epc_required_2030) > 0
            and cyear >= 2030
        )

        if run_mc:
            mc  = self.run_monte_carlo(physical_inputs, transition_inputs, val_inputs,
                                       scenario, time_horizon, mc_simulations)
            p5  = Decimal(str(mc["p5"]))
            p25 = Decimal(str(mc["p25"]))
            p50 = Decimal(str(mc["p50"]))
            p75 = Decimal(str(mc["p75"]))
            p95 = Decimal(str(mc["p95"]))
            v95 = Decimal(str(mc["var_95"]))
            v99 = Decimal(str(mc["var_99"]))
        else:
            sd  = abs(float(cpct)) * 0.30
            p50 = cpct
            p5  = Decimal(str(round(float(cpct) - 2.0*sd, 6)))
            p25 = Decimal(str(round(float(cpct) - 0.8*sd, 6)))
            p75 = Decimal(str(round(float(cpct) + 0.5*sd, 6)))
            p95 = Decimal(str(round(float(cpct) + 1.2*sd, 6)))
            v95 = p5
            v99 = Decimal(str(round(float(cpct) - 2.5*sd, 6)))
            mc  = {"n_simulations": 0}

        vs = self._build_validation_summary(
            physical_inputs, transition_inputs, val_inputs, scenario, time_horizon,
            phys, trans, float(cpct), float(cgbp),
            self._interpolate_carbon_price(scenario, 2030),
            self._interpolate_slr(scenario, 2050),
            mc, sy, is_s,
        )
        self.logger.info("CLVaR done: pct=%.4f stranding=%s", float(cpct), sy)
        return CLVaRResult(
            physical_var_pct=ppct, transition_var_pct=tpct,
            combined_clvar_pct=cpct, combined_clvar_gbp=cgbp,
            green_premium_pct=gpct, brown_discount_pct=bpct,
            stranding_risk_year=sy, is_already_stranded=is_s,
            p5=p5, p25=p25, p50=p50, p75=p75, p95=p95,
            var_95=v95, var_99=v99,
            hazard_contributions={h: Decimal(str(v)) for h, v in phys["hazard_impacts"].items()},
            validation_summary=vs,
        )


    def _build_validation_summary(
        self,
        pi: PhysicalRiskInputs,
        ti: TransitionRiskInputs,
        vi: PropertyValuationInputs,
        scenario: ClimateScenario,
        time_horizon: int,
        phys: Dict,
        trans: Dict,
        cpct: float,
        cgbp: float,
        cp2030: float,
        slr2050: float,
        mc: Dict,
        sy: Optional[int],
        is_s: bool,
    ) -> Dict:
        """Build RICS VPS4 / IVS 2024 compliant validation and audit trail."""
        dq = self._assess_data_quality(pi, ti, vi)
        return {
            "methodology": {
                "framework": "RICS VPS4 / IVS 2024 / CRREM-aligned",
                "engine_version": "CLVaR-Engine-v2.0.0",
                "physical_risk_model": "Hazard-exposure-vulnerability depth-damage functions",
                "transition_risk_model": "EPC gap analysis / DEFRA MEES / CRREM pathway",
                "monte_carlo_model": "Log-normal hazard sampling, 10,000 simulations",
                "aggregation_method": "Covariance-adjusted two-asset VaR (rho=0.45)",
                "carbon_price_source": "NGFS Phase 4 / IEA WEO 2024 / UK CCC",
                "slr_source": "IPCC AR6 WGI Chapter 9 / UK Met Office UKCP18",
                "epc_regulation_source": "England & Wales MEES 2023 / EU EPBD Recast 2024",
                "compliance_standards": ["RICS VPS4 (2023)", "IVS 2024",
                    "TCFD Recommendations (2017)", "EU Taxonomy Regulation 2020/852",
                    "CRREM v2.0 (2023)"],
                "calculation_timestamp": datetime.utcnow().isoformat() + "Z",
            },
            "input_parameters": {
                "scenario": scenario.value, "time_horizon_years": time_horizon,
                "property_type": vi.property_type.value, "country_iso": vi.country_iso,
                "region": vi.region, "floor_area_m2": float(vi.floor_area_m2),
                "current_market_value": float(vi.current_market_value),
                "year_built": vi.year_built, "last_refurbishment_year": vi.last_refurbishment_year,
                "flood_zone": pi.flood_zone, "flood_depth_100yr_m": float(pi.flood_depth_100yr_m),
                "heat_days_above_35c": pi.heat_days_above_35c,
                "wildfire_proximity_km": float(pi.wildfire_proximity_km),
                "coastal_proximity_km": float(pi.coastal_proximity_km),
                "subsidence_risk": pi.subsidence_risk,
                "water_stress_score": float(pi.water_stress_score),
                "current_epc_rating": ti.current_epc_rating,
                "energy_intensity_kwh_m2": float(ti.energy_intensity_kwh_m2),
                "carbon_intensity_kgco2_m2": float(ti.carbon_intensity_kgco2_m2),
                "minimum_epc_required_2030": ti.minimum_epc_required_2030,
                "minimum_epc_required_2033": ti.minimum_epc_required_2033,
                "retrofit_feasibility": ti.retrofit_feasibility,
                "green_certification": ti.current_green_certification,
            },
            "assumptions": {
                "carbon_price_2030_gbp_tco2": round(cp2030, 2),
                "sea_level_rise_2050_m": round(slr2050, 3),
                "physical_transition_correlation": 0.45,
                "discount_rate_pct": 5.0,
                "annual_carbon_intensity_improvement_pct": 2.0,
                "epc_regulation_enforcement": {
                    "2030": "All non-domestic lettings require EPC minimum C (MEES)",
                    "2033": "All non-domestic lettings require EPC minimum B (proposed MEES)",
                },
                "retrofit_cost_source": "DEFRA Green Finance Taskforce 2024 / JLL Retrofit Report 2024",
                "brown_discount_source": "RICS / JLL / Knight Frank ESG Research 2024",
                "green_premium_source": "CBRE / Cushman & Wakefield Green Premium Study 2023",
            },
            "output_summary": {
                "physical_var_pct": round(phys["physical_var_pct"] * 100, 2),
                "transition_var_pct": round(trans["transition_var_pct"] * 100, 2),
                "combined_clvar_pct": round(cpct * 100, 2),
                "combined_clvar_monetised": round(cgbp, 0),
                "stranding_risk_year": sy, "is_already_stranded": is_s,
                "hazard_contributions_pct": {h: round(v*100,3) for h,v in phys["hazard_impacts"].items()},
                "epc_gap_to_2030_requirement": trans["epc_gap_to_2030_minimum"],
                "brown_discount_pct": round(trans["brown_discount_pct"] * 100, 2),
                "green_premium_pct": round(trans["green_premium_pct"] * 100, 2),
                "total_retrofit_cost": round(trans["total_retrofit_cost"], 0),
                "npv_carbon_cost": round(trans["npv_carbon_cost"], 0),
                "monte_carlo_simulations": mc.get("n_simulations", 0),
                "var_95_pct": (round(float(mc.get("var_95", cpct))*100, 2)
                               if mc.get("n_simulations", 0) > 0 else None),
                "var_99_pct": (round(float(mc.get("var_99", cpct))*100, 2)
                               if mc.get("n_simulations", 0) > 0 else None),
            },
            "data_quality": dq,
            "disclaimers": [
                "CLVaR estimates are model-based projections subject to scenario uncertainty.",
                "Physical risk data from third-party providers; accuracy depends on input quality.",
                "EPC regulation timelines subject to legislative change.",
                "Carbon price trajectories are illustrative and not guaranteed.",
                "Outputs require review by a qualified RICS valuer before formal use.",
                "RICS VPS4 requires climate risk disclosure as a material valuation consideration.",
            ],
        }

    def _assess_data_quality(self, pi: PhysicalRiskInputs, ti: TransitionRiskInputs, vi: PropertyValuationInputs) -> Dict:
        """Rate data quality per input category, scale 1-5 (5 = highest)."""
        cy = datetime.utcnow().year
        fq = 5 if float(pi.flood_depth_100yr_m) > 0 else 2
        eq = 5 if ti.current_epc_rating.upper() in {"A+","A","B","C","D","E","F","G"} else 2
        nq = 5 if float(ti.energy_intensity_kwh_m2) > 0 else 2
        cq = 5 if float(ti.carbon_intensity_kgco2_m2) > 0 else 1
        vq = (5 if (cy - vi.last_refurbishment_year) <= 5 else
              (4 if (cy - vi.last_refurbishment_year) <= 10 else 3)) if vi.last_refurbishment_year else (
               3 if (cy - vi.year_built) <= 20 else 2)
        lb = ["","Very Low","Low","Moderate","High","Very High"]
        return {
            "flood_hazard_data":       {"score": fq, "rating": lb[fq], "note": "Environment Agency / JBA flood maps"},
            "epc_data":                {"score": eq, "rating": lb[eq], "note": "EPC Register -- verify against lodgement certificate"},
            "energy_performance_data": {"score": nq, "rating": lb[nq], "note": "DEC / energy audit -- metered data preferred"},
            "carbon_intensity_data":   {"score": cq, "rating": lb[cq], "note": "CIBSE TM54 verified data preferred"},
            "property_valuation_data": {"score": vq, "rating": lb[vq], "note": "RICS Red Book valuation preferred"},
            "overall_confidence":      {"score": round((fq+eq+nq+cq+vq)/5,1), "note": "Average quality score (5=highest)"},
        }



def calculate_clvar_for_asset(
    flood_zone: str,
    flood_depth_100yr_m: float,
    heat_days_above_35c: int,
    wildfire_proximity_km: float,
    coastal_proximity_km: float,
    subsidence_risk: str,
    water_stress_score: float,
    current_epc_rating: str,
    energy_intensity_kwh_m2: float,
    carbon_intensity_kgco2_m2: float,
    minimum_epc_required_2030: str,
    minimum_epc_required_2033: str,
    retrofit_feasibility: str,
    property_type: str,
    country_iso: str,
    region: str,
    floor_area_m2: float,
    current_market_value: float,
    year_built: int,
    scenario: str = "NZE_1.5C",
    time_horizon: int = 10,
    last_refurbishment_year: Optional[int] = None,
    green_certification: Optional[str] = None,
    run_mc: bool = True,
) -> CLVaRResult:
    """
    Convenience wrapper for single-asset CLVaR using primitive Python types.
    Maps string scenario/property_type to enums and delegates to RECLVaREngine.calculate_clvar().
    Scenario options: "NZE_1.5C", "BELOW_2C", "NDC_2.5C", "CURRENT_POLICIES_3C".
    """
    sm = {"NZE_1.5C": ClimateScenario.NZE_1_5C, "BELOW_2C": ClimateScenario.BELOW_2C,
          "NDC_2.5C": ClimateScenario.NDC_2_5C, "CURRENT_POLICIES_3C": ClimateScenario.CURRENT_POLICIES_3C}
    pm = {pt.value: pt for pt in PropertyType}
    return RECLVaREngine().calculate_clvar(
        physical_inputs=PhysicalRiskInputs(
            flood_zone=flood_zone,
            flood_depth_100yr_m=Decimal(str(flood_depth_100yr_m)),
            heat_days_above_35c=heat_days_above_35c,
            wildfire_proximity_km=Decimal(str(wildfire_proximity_km)),
            coastal_proximity_km=Decimal(str(coastal_proximity_km)),
            subsidence_risk=subsidence_risk,
            water_stress_score=Decimal(str(water_stress_score)),
        ),
        transition_inputs=TransitionRiskInputs(
            current_epc_rating=current_epc_rating,
            energy_intensity_kwh_m2=Decimal(str(energy_intensity_kwh_m2)),
            carbon_intensity_kgco2_m2=Decimal(str(carbon_intensity_kgco2_m2)),
            minimum_epc_required_2030=minimum_epc_required_2030,
            minimum_epc_required_2033=minimum_epc_required_2033,
            retrofit_feasibility=retrofit_feasibility,
            current_green_certification=green_certification,
        ),
        val_inputs=PropertyValuationInputs(
            property_type=pm.get(property_type, PropertyType.OFFICE),
            country_iso=country_iso, region=region,
            floor_area_m2=Decimal(str(floor_area_m2)),
            current_market_value=Decimal(str(current_market_value)),
            year_built=year_built,
            last_refurbishment_year=last_refurbishment_year,
        ),
        scenario=sm.get(scenario, ClimateScenario.NZE_1_5C),
        time_horizon=time_horizon,
        run_mc=run_mc,
    )
