"""
Scope 3 Category 11 — Use of Sold Products
==============================================
Calculates downstream emissions from the use phase of sold products.
Covers energy-using products (appliances, vehicles, equipment) and
fossil fuel products (coal, oil, gas sold by extractors/refiners).

References:
- GHG Protocol Scope 3 Standard — Category 11 methodology
- GHG Protocol Product Standard (Quantis)
- PCAF Financed Emissions — Category 11 attribution
- SBTi Corporate Standard — Optional Scope 3 target setting
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Reference Data
# ---------------------------------------------------------------------------

# Combustion emission factors for sold fuels (tCO2/unit)
FUEL_COMBUSTION_EF: dict[str, dict] = {
    "crude_oil_bbl": {"ef_tco2": 0.43, "unit": "barrel", "label": "Crude Oil"},
    "natural_gas_mcf": {"ef_tco2": 0.053, "unit": "MCF", "label": "Natural Gas"},
    "lng_tonne": {"ef_tco2": 2.75, "unit": "tonne", "label": "LNG"},
    "thermal_coal_tonne": {"ef_tco2": 2.42, "unit": "tonne", "label": "Thermal Coal"},
    "coking_coal_tonne": {"ef_tco2": 3.10, "unit": "tonne", "label": "Coking Coal"},
    "diesel_litre": {"ef_tco2": 0.00267, "unit": "litre", "label": "Diesel"},
    "gasoline_litre": {"ef_tco2": 0.00231, "unit": "litre", "label": "Gasoline / Petrol"},
    "jet_fuel_litre": {"ef_tco2": 0.00254, "unit": "litre", "label": "Jet Fuel"},
    "lpg_tonne": {"ef_tco2": 2.98, "unit": "tonne", "label": "LPG"},
    "naphtha_tonne": {"ef_tco2": 3.14, "unit": "tonne", "label": "Naphtha"},
}

# Energy-using product categories (avg annual electricity kWh)
PRODUCT_USE_PROFILES: dict[str, dict] = {
    "passenger_car_ice": {"annual_energy_kwh": 0, "annual_fuel_litres": 1200, "fuel_type": "gasoline_litre",
                          "lifetime_years": 12, "label": "Passenger Car (ICE)"},
    "passenger_car_ev": {"annual_energy_kwh": 3500, "annual_fuel_litres": 0, "fuel_type": "",
                         "lifetime_years": 12, "label": "Passenger Car (BEV)"},
    "commercial_vehicle": {"annual_energy_kwh": 0, "annual_fuel_litres": 8000, "fuel_type": "diesel_litre",
                           "lifetime_years": 10, "label": "Commercial Vehicle"},
    "residential_boiler_gas": {"annual_energy_kwh": 15000, "annual_fuel_litres": 0, "fuel_type": "",
                               "annual_gas_mcf": 500, "lifetime_years": 15, "label": "Gas Boiler"},
    "heat_pump": {"annual_energy_kwh": 4000, "annual_fuel_litres": 0, "fuel_type": "",
                  "lifetime_years": 18, "label": "Heat Pump"},
    "industrial_motor": {"annual_energy_kwh": 50000, "annual_fuel_litres": 0, "fuel_type": "",
                         "lifetime_years": 20, "label": "Industrial Electric Motor"},
    "data_server": {"annual_energy_kwh": 8760, "annual_fuel_litres": 0, "fuel_type": "",
                    "lifetime_years": 5, "label": "Data Centre Server"},
    "household_appliance": {"annual_energy_kwh": 400, "annual_fuel_litres": 0, "fuel_type": "",
                            "lifetime_years": 10, "label": "Household Appliance (avg)"},
}


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class FuelSoldInput:
    """Fossil fuel sales volume."""
    fuel_type: str  # key into FUEL_COMBUSTION_EF
    volume_sold: float  # in unit specified by EF
    year: int = 2024


@dataclass
class ProductSoldInput:
    """Energy-using product sales."""
    product_type: str  # key into PRODUCT_USE_PROFILES
    units_sold: int
    grid_ef_tco2_mwh: float = 0.40  # Location-based grid EF
    year: int = 2024


@dataclass
class FuelEmissionsResult:
    """Category 11 emissions for sold fuels."""
    fuel_type: str
    fuel_label: str
    volume_sold: float
    unit: str
    ef_tco2_per_unit: float
    total_tco2: float
    year: int


@dataclass
class ProductEmissionsResult:
    """Category 11 emissions for sold energy-using products."""
    product_type: str
    product_label: str
    units_sold: int
    lifetime_years: int
    annual_electricity_kwh_per_unit: float
    annual_fuel_litres_per_unit: float
    annual_tco2_per_unit: float
    lifetime_tco2_per_unit: float
    total_lifetime_tco2: float
    grid_ef_used: float
    year: int


@dataclass
class Scope3Cat11Result:
    """Complete Category 11 assessment."""
    reporting_year: int
    fuel_results: list[FuelEmissionsResult]
    product_results: list[ProductEmissionsResult]
    total_fuel_tco2: float
    total_product_lifetime_tco2: float
    total_cat11_tco2: float
    top_contributor: str
    top_contributor_pct: float
    intensity_tco2_per_m_revenue: float  # if revenue provided


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class Scope3Cat11Engine:
    """Scope 3 Category 11 — Use of Sold Products engine."""

    def assess(
        self,
        fuels: list[FuelSoldInput] = None,
        products: list[ProductSoldInput] = None,
        reporting_year: int = 2024,
        revenue_m_eur: float = 0,
    ) -> Scope3Cat11Result:
        """Calculate Category 11 emissions."""
        fuels = fuels or []
        products = products or []

        fuel_results = []
        for f in fuels:
            info = FUEL_COMBUSTION_EF.get(f.fuel_type)
            if not info:
                continue
            total = f.volume_sold * info["ef_tco2"]
            fuel_results.append(FuelEmissionsResult(
                fuel_type=f.fuel_type,
                fuel_label=info["label"],
                volume_sold=f.volume_sold,
                unit=info["unit"],
                ef_tco2_per_unit=info["ef_tco2"],
                total_tco2=round(total, 1),
                year=f.year,
            ))

        product_results = []
        for p in products:
            profile = PRODUCT_USE_PROFILES.get(p.product_type)
            if not profile:
                continue

            annual_elec = profile["annual_energy_kwh"]
            annual_fuel = profile.get("annual_fuel_litres", 0)
            lifetime = profile["lifetime_years"]

            # Electricity emissions
            elec_tco2 = annual_elec * p.grid_ef_tco2_mwh / 1000

            # Fuel emissions
            fuel_tco2 = 0
            if annual_fuel > 0 and profile.get("fuel_type"):
                fi = FUEL_COMBUSTION_EF.get(profile["fuel_type"], {})
                fuel_tco2 = annual_fuel * fi.get("ef_tco2", 0)

            # Gas boiler special case
            gas_mcf = profile.get("annual_gas_mcf", 0)
            if gas_mcf > 0:
                gi = FUEL_COMBUSTION_EF.get("natural_gas_mcf", {})
                fuel_tco2 += gas_mcf * gi.get("ef_tco2", 0)

            annual_per_unit = elec_tco2 + fuel_tco2
            lifetime_per_unit = annual_per_unit * lifetime
            total_lifetime = lifetime_per_unit * p.units_sold

            product_results.append(ProductEmissionsResult(
                product_type=p.product_type,
                product_label=profile["label"],
                units_sold=p.units_sold,
                lifetime_years=lifetime,
                annual_electricity_kwh_per_unit=annual_elec,
                annual_fuel_litres_per_unit=annual_fuel,
                annual_tco2_per_unit=round(annual_per_unit, 4),
                lifetime_tco2_per_unit=round(lifetime_per_unit, 2),
                total_lifetime_tco2=round(total_lifetime, 1),
                grid_ef_used=p.grid_ef_tco2_mwh,
                year=p.year,
            ))

        total_fuel = sum(r.total_tco2 for r in fuel_results)
        total_product = sum(r.total_lifetime_tco2 for r in product_results)
        total_cat11 = total_fuel + total_product

        # Top contributor
        all_items = (
            [(r.fuel_label, r.total_tco2) for r in fuel_results]
            + [(r.product_label, r.total_lifetime_tco2) for r in product_results]
        )
        if all_items:
            top = max(all_items, key=lambda x: x[1])
            top_name = top[0]
            top_pct = (top[1] / total_cat11 * 100) if total_cat11 > 0 else 0
        else:
            top_name = "N/A"
            top_pct = 0

        intensity = total_cat11 / revenue_m_eur if revenue_m_eur > 0 else 0

        return Scope3Cat11Result(
            reporting_year=reporting_year,
            fuel_results=fuel_results,
            product_results=product_results,
            total_fuel_tco2=round(total_fuel, 1),
            total_product_lifetime_tco2=round(total_product, 1),
            total_cat11_tco2=round(total_cat11, 1),
            top_contributor=top_name,
            top_contributor_pct=round(top_pct, 1),
            intensity_tco2_per_m_revenue=round(intensity, 1),
        )

    def get_fuel_efs(self) -> dict[str, dict]:
        return FUEL_COMBUSTION_EF

    def get_product_profiles(self) -> dict[str, dict]:
        return PRODUCT_USE_PROFILES
