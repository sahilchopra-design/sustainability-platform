"""
Renewable Project Finance Engine (P50/P90) + LCOE
====================================================
Wind and solar energy yield models with statistical confidence levels,
capacity factor estimation, LCOE calculation, and IRR with/without
carbon revenue.

References:
- IEC 61400-12 — Wind turbine power performance
- IRENA — Renewable power generation costs (2024)
- DNV — Energy yield assessment best practice
- GHG Protocol — Renewable energy calculations
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
import math


# ---------------------------------------------------------------------------
# Reference Data — Wind Turbine Classes
# ---------------------------------------------------------------------------

TURBINE_CLASSES: dict[str, dict] = {
    "onshore_2mw": {
        "name": "Onshore 2 MW",
        "capacity_mw": 2.0,
        "hub_height_m": 80,
        "rotor_diameter_m": 90,
        "cut_in_ms": 3.0,
        "rated_ms": 12.0,
        "cut_out_ms": 25.0,
        "capex_eur_per_kw": 1200,
        "opex_eur_per_kw_yr": 35,
        "lifetime_years": 25,
    },
    "offshore_5mw": {
        "name": "Offshore 5 MW",
        "capacity_mw": 5.0,
        "hub_height_m": 90,
        "rotor_diameter_m": 126,
        "cut_in_ms": 3.5,
        "rated_ms": 13.0,
        "cut_out_ms": 25.0,
        "capex_eur_per_kw": 2800,
        "opex_eur_per_kw_yr": 80,
        "lifetime_years": 25,
    },
    "offshore_8mw": {
        "name": "Offshore 8 MW",
        "capacity_mw": 8.0,
        "hub_height_m": 105,
        "rotor_diameter_m": 164,
        "cut_in_ms": 3.0,
        "rated_ms": 12.5,
        "cut_out_ms": 25.0,
        "capex_eur_per_kw": 3200,
        "opex_eur_per_kw_yr": 90,
        "lifetime_years": 30,
    },
    "onshore_4mw": {
        "name": "Onshore 4 MW",
        "capacity_mw": 4.0,
        "hub_height_m": 100,
        "rotor_diameter_m": 140,
        "cut_in_ms": 3.0,
        "rated_ms": 11.5,
        "cut_out_ms": 25.0,
        "capex_eur_per_kw": 1100,
        "opex_eur_per_kw_yr": 30,
        "lifetime_years": 25,
    },
    "offshore_12mw": {
        "name": "Offshore 12 MW",
        "capacity_mw": 12.0,
        "hub_height_m": 120,
        "rotor_diameter_m": 220,
        "cut_in_ms": 3.0,
        "rated_ms": 12.0,
        "cut_out_ms": 30.0,
        "capex_eur_per_kw": 2600,
        "opex_eur_per_kw_yr": 75,
        "lifetime_years": 30,
    },
}


# Weibull parameters by region (shape k, scale lambda m/s)
WIND_RESOURCE_REGIONS: dict[str, dict] = {
    "north_sea": {"k": 2.1, "lambda": 10.5, "label": "North Sea Offshore"},
    "baltic_sea": {"k": 2.0, "lambda": 8.8, "label": "Baltic Sea Offshore"},
    "atlantic_france": {"k": 2.0, "lambda": 9.2, "label": "Atlantic France"},
    "mediterranean": {"k": 1.8, "lambda": 6.5, "label": "Mediterranean"},
    "northern_europe_onshore": {"k": 2.0, "lambda": 7.5, "label": "N. Europe Onshore"},
    "central_europe_onshore": {"k": 1.9, "lambda": 6.0, "label": "C. Europe Onshore"},
    "iberia_onshore": {"k": 1.8, "lambda": 6.8, "label": "Iberia Onshore"},
    "uk_offshore": {"k": 2.1, "lambda": 10.0, "label": "UK Offshore"},
    "scandinavia_onshore": {"k": 2.0, "lambda": 7.8, "label": "Scandinavia Onshore"},
    "us_midwest": {"k": 2.0, "lambda": 8.0, "label": "US Midwest Onshore"},
    "us_texas": {"k": 1.9, "lambda": 7.5, "label": "US Texas Onshore"},
    "india_tamil_nadu": {"k": 1.7, "lambda": 6.2, "label": "India Tamil Nadu"},
    "brazil_northeast": {"k": 2.2, "lambda": 8.5, "label": "Brazil NE"},
    "south_africa": {"k": 1.9, "lambda": 7.0, "label": "South Africa"},
    "australia_nsw": {"k": 2.0, "lambda": 7.2, "label": "Australia NSW"},
}


# Solar GHI by country (kWh/m2/year)
SOLAR_GHI_DATA: dict[str, dict] = {
    "DE": {"ghi": 1100, "label": "Germany"},
    "FR": {"ghi": 1400, "label": "France"},
    "ES": {"ghi": 1800, "label": "Spain"},
    "IT": {"ghi": 1600, "label": "Italy"},
    "PT": {"ghi": 1750, "label": "Portugal"},
    "NL": {"ghi": 1050, "label": "Netherlands"},
    "GB": {"ghi": 950, "label": "United Kingdom"},
    "SE": {"ghi": 900, "label": "Sweden"},
    "PL": {"ghi": 1050, "label": "Poland"},
    "GR": {"ghi": 1800, "label": "Greece"},
    "US": {"ghi": 1600, "label": "United States (avg)"},
    "IN": {"ghi": 1900, "label": "India"},
    "AU": {"ghi": 2000, "label": "Australia"},
    "BR": {"ghi": 1800, "label": "Brazil"},
    "ZA": {"ghi": 1900, "label": "South Africa"},
    "AE": {"ghi": 2100, "label": "UAE"},
    "SA": {"ghi": 2200, "label": "Saudi Arabia"},
    "JP": {"ghi": 1300, "label": "Japan"},
    "CN": {"ghi": 1400, "label": "China"},
    "MX": {"ghi": 1900, "label": "Mexico"},
}

# Solar system defaults
SOLAR_DEFAULTS: dict = {
    "capex_eur_per_kwp": 750,
    "opex_eur_per_kwp_yr": 12,
    "performance_ratio": 0.82,  # PR accounting for temp/soiling/degradation
    "degradation_pct_yr": 0.5,
    "lifetime_years": 30,
    "temp_coeff_pct_per_c": -0.35,  # Power temp coefficient
    "avg_module_temp_above_stc_c": 15,  # Typical above 25C STC
}


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class WindYieldResult:
    """Wind energy yield assessment."""
    turbine_class: str
    turbine_name: str
    region: str
    capacity_mw: float
    num_turbines: int
    total_capacity_mw: float
    weibull_k: float
    weibull_lambda: float
    mean_wind_speed_ms: float
    capacity_factor_pct: float
    p50_generation_mwh: float
    p75_generation_mwh: float
    p90_generation_mwh: float
    equivalent_full_load_hours: float
    wake_loss_pct: float
    availability_pct: float


@dataclass
class SolarYieldResult:
    """Solar energy yield assessment."""
    country: str
    country_label: str
    capacity_kwp: float
    ghi_kwh_m2_yr: float
    performance_ratio: float
    degradation_pct_yr: float
    p50_generation_mwh_yr1: float
    p75_generation_mwh_yr1: float
    p90_generation_mwh_yr1: float
    p50_lifetime_avg_mwh: float
    capacity_factor_pct: float
    specific_yield_kwh_kwp: float


@dataclass
class LCOEResult:
    """Levelised Cost of Energy calculation."""
    technology: str  # "wind" | "solar"
    total_capex_eur: float
    annual_opex_eur: float
    annual_generation_mwh: float  # P50
    wacc_pct: float
    lifetime_years: int
    crf: float  # Capital Recovery Factor
    lcoe_eur_mwh: float
    lcoe_with_degradation_eur_mwh: float


@dataclass
class ProjectFinanceResult:
    """Complete renewable project finance assessment."""
    project_name: str
    technology: str
    yield_result: dict  # Serialised yield
    lcoe: LCOEResult
    irr_pct: float
    irr_with_carbon_pct: float
    npv_eur: float
    npv_with_carbon_eur: float
    payback_years: float
    total_capex_eur: float
    annual_revenue_eur: float
    annual_opex_eur: float
    carbon_revenue_eur_yr: float
    co2_avoided_tonnes_yr: float
    lifetime_co2_avoided_tonnes: float


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class RenewableProjectEngine:
    """Renewable project finance and yield assessment engine."""

    # -------------------------------------------------------------------
    # Wind Yield
    # -------------------------------------------------------------------

    def wind_yield(
        self,
        turbine_class: str = "onshore_2mw",
        region: str = "northern_europe_onshore",
        num_turbines: int = 10,
        wake_loss_pct: float = 8.0,
        availability_pct: float = 97.0,
    ) -> WindYieldResult:
        """Calculate wind energy yield with P50/P75/P90 confidence levels."""
        turb = TURBINE_CLASSES.get(turbine_class)
        if not turb:
            turb = TURBINE_CLASSES["onshore_2mw"]

        wind_res = WIND_RESOURCE_REGIONS.get(region)
        if not wind_res:
            wind_res = WIND_RESOURCE_REGIONS["northern_europe_onshore"]

        k = wind_res["k"]
        lam = wind_res["lambda"]

        # Mean wind speed from Weibull: lambda * Gamma(1 + 1/k)
        mean_ws = lam * math.gamma(1 + 1 / k)

        # Capacity factor from simplified power curve model
        cf = self._wind_capacity_factor(k, lam, turb)

        # Apply losses
        cf_net = cf * (1 - wake_loss_pct / 100) * (availability_pct / 100)

        total_cap = turb["capacity_mw"] * num_turbines
        hours = 8760

        # P50 generation (median)
        p50 = total_cap * cf_net * hours

        # P75/P90: uncertainty based on Weibull parameter uncertainty (~6-10% std)
        uncertainty_std_pct = 7.0  # % of annual generation
        p75 = p50 * (1 - 0.674 * uncertainty_std_pct / 100)
        p90 = p50 * (1 - 1.282 * uncertainty_std_pct / 100)

        eflh = cf_net * hours

        return WindYieldResult(
            turbine_class=turbine_class,
            turbine_name=turb["name"],
            region=region,
            capacity_mw=turb["capacity_mw"],
            num_turbines=num_turbines,
            total_capacity_mw=round(total_cap, 2),
            weibull_k=k,
            weibull_lambda=lam,
            mean_wind_speed_ms=round(mean_ws, 2),
            capacity_factor_pct=round(cf_net * 100, 1),
            p50_generation_mwh=round(p50, 0),
            p75_generation_mwh=round(p75, 0),
            p90_generation_mwh=round(p90, 0),
            equivalent_full_load_hours=round(eflh, 0),
            wake_loss_pct=wake_loss_pct,
            availability_pct=availability_pct,
        )

    def _wind_capacity_factor(self, k: float, lam: float, turb: dict) -> float:
        """Estimate capacity factor from Weibull distribution and power curve."""
        cut_in = turb["cut_in_ms"]
        rated = turb["rated_ms"]
        cut_out = turb["cut_out_ms"]

        # Probability wind is in producing range
        # P(cut_in < v < rated) * avg_fraction + P(rated < v < cut_out) * 1.0
        # Using Weibull CDF: F(v) = 1 - exp(-(v/lambda)^k)

        def weibull_cdf(v):
            return 1 - math.exp(-((v / lam) ** k))

        p_below_cut_in = weibull_cdf(cut_in)
        p_below_rated = weibull_cdf(rated)
        p_below_cut_out = weibull_cdf(cut_out)

        # Fraction in partial power region (simplified: ~50% avg power)
        partial_fraction = (p_below_rated - p_below_cut_in) * 0.45
        # Fraction at rated power
        rated_fraction = (p_below_cut_out - p_below_rated) * 1.0

        cf = partial_fraction + rated_fraction
        return min(cf, 0.65)  # Cap at 65%

    # -------------------------------------------------------------------
    # Solar Yield
    # -------------------------------------------------------------------

    def solar_yield(
        self,
        country: str = "DE",
        capacity_kwp: float = 1000,
        performance_ratio: float = 0.0,  # 0 = use default
        degradation_pct_yr: float = 0.0,  # 0 = use default
    ) -> SolarYieldResult:
        """Calculate solar energy yield with P50/P75/P90."""
        solar = SOLAR_GHI_DATA.get(country)
        if not solar:
            solar = {"ghi": 1400, "label": country}

        pr = performance_ratio if performance_ratio > 0 else SOLAR_DEFAULTS["performance_ratio"]
        deg = degradation_pct_yr if degradation_pct_yr > 0 else SOLAR_DEFAULTS["degradation_pct_yr"]

        # Temperature correction
        temp_loss = abs(SOLAR_DEFAULTS["temp_coeff_pct_per_c"]) * SOLAR_DEFAULTS["avg_module_temp_above_stc_c"] / 100
        effective_pr = pr * (1 - temp_loss)

        ghi = solar["ghi"]

        # Specific yield (kWh/kWp)
        specific_yield = ghi * effective_pr
        p50_yr1 = capacity_kwp * specific_yield / 1000  # MWh

        # P75/P90 (inter-annual variability ~5% std)
        uncertainty_std_pct = 5.0
        p75_yr1 = p50_yr1 * (1 - 0.674 * uncertainty_std_pct / 100)
        p90_yr1 = p50_yr1 * (1 - 1.282 * uncertainty_std_pct / 100)

        # Lifetime average (with degradation)
        lifetime = SOLAR_DEFAULTS["lifetime_years"]
        # Average degradation factor over lifetime
        avg_deg_factor = 1 - deg / 100 * (lifetime - 1) / 2
        p50_lifetime = p50_yr1 * avg_deg_factor

        cf = p50_yr1 * 1000 / (capacity_kwp * 8760) * 100  # %

        return SolarYieldResult(
            country=country,
            country_label=solar["label"],
            capacity_kwp=capacity_kwp,
            ghi_kwh_m2_yr=ghi,
            performance_ratio=round(effective_pr, 4),
            degradation_pct_yr=deg,
            p50_generation_mwh_yr1=round(p50_yr1, 1),
            p75_generation_mwh_yr1=round(p75_yr1, 1),
            p90_generation_mwh_yr1=round(p90_yr1, 1),
            p50_lifetime_avg_mwh=round(p50_lifetime, 1),
            capacity_factor_pct=round(cf, 1),
            specific_yield_kwh_kwp=round(specific_yield, 0),
        )

    # -------------------------------------------------------------------
    # LCOE
    # -------------------------------------------------------------------

    def lcoe(
        self,
        technology: str,  # "wind" | "solar"
        total_capex_eur: float,
        annual_opex_eur: float,
        annual_generation_mwh: float,
        wacc_pct: float = 6.0,
        lifetime_years: int = 25,
        degradation_pct_yr: float = 0.0,
    ) -> LCOEResult:
        """Calculate Levelised Cost of Energy."""
        r = wacc_pct / 100
        n = lifetime_years

        # Capital Recovery Factor
        if r > 0:
            crf = r * (1 + r) ** n / ((1 + r) ** n - 1)
        else:
            crf = 1 / n

        lcoe_base = (total_capex_eur * crf + annual_opex_eur) / annual_generation_mwh

        # With degradation: average generation lower over lifetime
        if degradation_pct_yr > 0:
            avg_factor = 1 - degradation_pct_yr / 100 * (n - 1) / 2
            gen_avg = annual_generation_mwh * avg_factor
            lcoe_deg = (total_capex_eur * crf + annual_opex_eur) / gen_avg
        else:
            lcoe_deg = lcoe_base

        return LCOEResult(
            technology=technology,
            total_capex_eur=round(total_capex_eur, 2),
            annual_opex_eur=round(annual_opex_eur, 2),
            annual_generation_mwh=round(annual_generation_mwh, 1),
            wacc_pct=wacc_pct,
            lifetime_years=lifetime_years,
            crf=round(crf, 6),
            lcoe_eur_mwh=round(lcoe_base, 2),
            lcoe_with_degradation_eur_mwh=round(lcoe_deg, 2),
        )

    # -------------------------------------------------------------------
    # Project Finance (IRR + NPV)
    # -------------------------------------------------------------------

    def assess_project(
        self,
        project_name: str,
        technology: str,  # "wind" | "solar"
        # Wind params
        turbine_class: str = "onshore_2mw",
        region: str = "northern_europe_onshore",
        num_turbines: int = 10,
        # Solar params
        country: str = "DE",
        capacity_kwp: float = 0,
        # Common params
        ppa_price_eur_mwh: float = 60.0,
        carbon_price_eur_tonne: float = 80.0,
        grid_ef_tco2_mwh: float = 0.4,
        wacc_pct: float = 6.0,
        capex_override_eur: float = 0,
        opex_override_eur_yr: float = 0,
    ) -> ProjectFinanceResult:
        """Full project finance assessment with IRR, NPV, LCOE."""
        if technology == "wind":
            yield_res = self.wind_yield(turbine_class, region, num_turbines)
            turb = TURBINE_CLASSES.get(turbine_class, TURBINE_CLASSES["onshore_2mw"])
            cap_kw = yield_res.total_capacity_mw * 1000
            total_capex = capex_override_eur if capex_override_eur > 0 else cap_kw * turb["capex_eur_per_kw"]
            annual_opex = opex_override_eur_yr if opex_override_eur_yr > 0 else cap_kw * turb["opex_eur_per_kw_yr"]
            p50_gen = yield_res.p50_generation_mwh
            lifetime = turb["lifetime_years"]
            deg = 0.0
            yield_dict = {
                "type": "wind",
                "turbine": yield_res.turbine_name,
                "region": yield_res.region,
                "capacity_mw": yield_res.total_capacity_mw,
                "capacity_factor_pct": yield_res.capacity_factor_pct,
                "p50_mwh": yield_res.p50_generation_mwh,
                "p90_mwh": yield_res.p90_generation_mwh,
            }
        else:
            yield_res = self.solar_yield(country, capacity_kwp)
            total_capex = capex_override_eur if capex_override_eur > 0 else capacity_kwp * SOLAR_DEFAULTS["capex_eur_per_kwp"]
            annual_opex = opex_override_eur_yr if opex_override_eur_yr > 0 else capacity_kwp * SOLAR_DEFAULTS["opex_eur_per_kwp_yr"]
            p50_gen = yield_res.p50_generation_mwh_yr1
            lifetime = SOLAR_DEFAULTS["lifetime_years"]
            deg = SOLAR_DEFAULTS["degradation_pct_yr"]
            yield_dict = {
                "type": "solar",
                "country": yield_res.country_label,
                "capacity_kwp": yield_res.capacity_kwp,
                "capacity_factor_pct": yield_res.capacity_factor_pct,
                "p50_mwh": yield_res.p50_generation_mwh_yr1,
                "p90_mwh": yield_res.p90_generation_mwh_yr1,
            }

        # LCOE
        lcoe_res = self.lcoe(
            technology, total_capex, annual_opex, p50_gen,
            wacc_pct, lifetime, deg,
        )

        # Revenue
        annual_revenue = p50_gen * ppa_price_eur_mwh

        # Carbon avoided
        co2_avoided = p50_gen * grid_ef_tco2_mwh
        carbon_rev = co2_avoided * carbon_price_eur_tonne

        # Lifetime CO2
        if deg > 0:
            avg_factor = 1 - deg / 100 * (lifetime - 1) / 2
            lifetime_co2 = co2_avoided * avg_factor * lifetime
        else:
            lifetime_co2 = co2_avoided * lifetime

        # NPV (simple)
        r = wacc_pct / 100
        annual_cf = annual_revenue - annual_opex
        npv = -total_capex + sum(annual_cf / (1 + r) ** t for t in range(1, lifetime + 1))
        npv_carbon = -total_capex + sum(
            (annual_cf + carbon_rev) / (1 + r) ** t for t in range(1, lifetime + 1)
        )

        # IRR (simplified from MOIC)
        total_cf = annual_cf * lifetime
        moic = total_cf / total_capex if total_capex > 0 else 0
        irr = round((moic ** (1 / lifetime) - 1) * 100, 2) if moic > 0 else 0

        total_cf_carbon = (annual_cf + carbon_rev) * lifetime
        moic_c = total_cf_carbon / total_capex if total_capex > 0 else 0
        irr_c = round((moic_c ** (1 / lifetime) - 1) * 100, 2) if moic_c > 0 else 0

        # Payback
        payback = total_capex / annual_cf if annual_cf > 0 else 99

        return ProjectFinanceResult(
            project_name=project_name,
            technology=technology,
            yield_result=yield_dict,
            lcoe=lcoe_res,
            irr_pct=irr,
            irr_with_carbon_pct=irr_c,
            npv_eur=round(npv, 2),
            npv_with_carbon_eur=round(npv_carbon, 2),
            payback_years=round(payback, 1),
            total_capex_eur=round(total_capex, 2),
            annual_revenue_eur=round(annual_revenue, 2),
            annual_opex_eur=round(annual_opex, 2),
            carbon_revenue_eur_yr=round(carbon_rev, 2),
            co2_avoided_tonnes_yr=round(co2_avoided, 1),
            lifetime_co2_avoided_tonnes=round(lifetime_co2, 0),
        )

    # -------------------------------------------------------------------
    # Reference Data
    # -------------------------------------------------------------------

    def get_turbine_classes(self) -> dict[str, dict]:
        return TURBINE_CLASSES

    def get_wind_regions(self) -> dict[str, dict]:
        return WIND_RESOURCE_REGIONS

    def get_solar_ghi_data(self) -> dict[str, dict]:
        return SOLAR_GHI_DATA
