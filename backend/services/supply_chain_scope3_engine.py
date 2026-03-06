"""
Supply Chain Scope 3 Emissions Engine -- GHG Protocol Corporate Value Chain Standard

Implements the GHG Protocol Corporate Value Chain (Scope 3) Accounting and Reporting
Standard for calculating upstream and downstream Scope 3 emissions across all fifteen
categories, with support for multiple calculation methods, uncertainty quantification,
SBTi target-setting, and supply chain hotspot analysis.

References:
  - GHG Protocol Corporate Value Chain (Scope 3) Standard (2011)
  - GHG Protocol Scope 3 Evaluator / CEDA emission factors
  - EPA USEEIO v2.0 spend-based emission factors
  - Exiobase 3.8 / DEFRA supply chain emission factors
  - SBTi Corporate Manual v2.0 Scope 3 target guidance
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from enum import Enum
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class Scope3Category(str, Enum):
    """GHG Protocol Scope 3 categories (upstream Cat 1-8, downstream Cat 9-15)."""
    CAT1  = "cat1_purchased_goods_services"
    CAT2  = "cat2_capital_goods"
    CAT3  = "cat3_fuel_energy_activities"
    CAT4  = "cat4_upstream_transport_distribution"
    CAT5  = "cat5_waste_generated_operations"
    CAT6  = "cat6_business_travel"
    CAT7  = "cat7_employee_commuting"
    CAT8  = "cat8_upstream_leased_assets"
    CAT9  = "cat9_downstream_transport_distribution"
    CAT10 = "cat10_processing_sold_products"
    CAT11 = "cat11_use_of_sold_products"
    CAT12 = "cat12_end_of_life_treatment"
    CAT13 = "cat13_downstream_leased_assets"
    CAT14 = "cat14_franchises"
    CAT15 = "cat15_investments"


class CalculationMethod(str, Enum):
    """GHG Protocol Scope 3 calculation methods."""
    SPEND_BASED       = "spend_based"
    AVERAGE_DATA      = "average_data"
    HYBRID            = "hybrid"
    SUPPLIER_SPECIFIC = "supplier_specific"
    PHYSICAL_ACTIVITY = "physical_activity"


class DataQuality(str, Enum):
    """
    GHG Protocol data quality tiers for Scope 3.
    Tier 1 (best, primary measured data) to Tier 3 (estimated).
    """
    TIER1_PRIMARY   = "tier1_primary_data"
    TIER2_SECONDARY = "tier2_secondary_data"
    TIER3_ESTIMATED = "tier3_estimated"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ActivityData:
    """
    Input data for a single Scope 3 activity.
    
    Either spend_usd (for spend-based method) or quantity+unit (for physical
    activity methods) must be populated, depending on preferred_method.
    """
    category:           Scope3Category
    activity_description: str
    quantity:           Decimal          # physical quantity (tonnes, pkm, kWh, etc.)
    unit:               str              # physical unit (tonne-km, pkm, kWh, units, etc.)
    spend_usd:          Decimal          # USD spend (for spend-based method)
    preferred_method:   CalculationMethod
    sector_gics:        str              # for spend-based EF lookup
    country_iso:        str              # geography for grid-average EF selection


@dataclass
class Scope3CategoryResult:
    """
    Calculated Scope 3 emissions for a single category.
    
    Includes method used, emission factor applied, uncertainty range,
    SBTi relevance flag, and a full validation/audit trail.
    """
    category:             Scope3Category
    co2e_tonnes:          Decimal
    method_used:          CalculationMethod
    emission_factor:      Decimal
    emission_factor_unit: str
    emission_factor_source: str
    data_quality:         DataQuality
    uncertainty_pct:      Decimal          # percentage uncertainty range
    sbti_relevant:        bool             # counted towards SBTi Scope 3 target
    notes:                str
    validation_summary:   Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Scope3Engine class
# ---------------------------------------------------------------------------

class Scope3Engine:
    """
    Calculates GHG Protocol Scope 3 emissions for all fifteen categories.
    
    Supports spend-based, average-data, physical-activity, hybrid, and
    supplier-specific calculation methods with uncertainty quantification
    and SBTi target-setting support.
    """

    # Spend-based EFs (kgCO2e per USD spend) -- EPA USEEIO v2.0 / Exiobase 3.8
    SPEND_BASED_EMISSION_FACTORS: Dict[str, Decimal] = {
        "Energy":                  Decimal("0.850"),
        "Materials":               Decimal("0.620"),
        "Industrials":             Decimal("0.420"),
        "Consumer Discretionary":  Decimal("0.310"),
        "Consumer Staples":        Decimal("0.380"),
        "Health Care":             Decimal("0.260"),
        "Financials":              Decimal("0.150"),
        "Information Technology":  Decimal("0.180"),
        "Communication Services":  Decimal("0.160"),
        "Utilities":               Decimal("0.720"),
        "Real Estate":             Decimal("0.280"),
        "Transportation":          Decimal("0.480"),
        "Food & Beverage":         Decimal("0.540"),
        "Agriculture":             Decimal("0.780"),
        "Mining":                  Decimal("0.690"),
        "Chemicals":               Decimal("0.680"),
        "Textiles & Apparel":      Decimal("0.350"),
        "Freight & Logistics":     Decimal("0.490"),
        "Paper & Packaging":       Decimal("0.520"),
        "Waste Management":        Decimal("0.440"),
        "Construction":            Decimal("0.410"),
        "Professional Services":   Decimal("0.130"),
        "Unknown":                 Decimal("0.350"),
    }

    # Physical activity EFs -- DEFRA 2023, IPCC AR6, ICAO Carbon Calculator
    PHYSICAL_EF_LIBRARY: Dict[str, Decimal] = {
        "freight_road_hgv_kgco2e_tonne_km":         Decimal("0.1465"),
        "freight_road_lgv_kgco2e_tonne_km":         Decimal("0.2464"),
        "freight_sea_container_kgco2e_tonne_km":    Decimal("0.0106"),
        "freight_sea_tanker_kgco2e_tonne_km":       Decimal("0.0118"),
        "freight_air_kgco2e_tonne_km":              Decimal("0.6020"),
        "freight_rail_kgco2e_tonne_km":             Decimal("0.0279"),
        "business_travel_air_shorthaul_kgco2e_pkm": Decimal("0.1554"),
        "business_travel_air_longhaul_kgco2e_pkm":  Decimal("0.1949"),
        "business_travel_air_business_kgco2e_pkm":  Decimal("0.4285"),
        "business_travel_rail_kgco2e_pkm":          Decimal("0.0035"),
        "business_travel_car_kgco2e_pkm":           Decimal("0.1421"),
        "business_travel_taxi_kgco2e_pkm":          Decimal("0.1490"),
        "hotel_night_uk_kgco2e":                    Decimal("20.8"),
        "hotel_night_europe_kgco2e":                Decimal("18.5"),
        "hotel_night_global_kgco2e":                Decimal("31.2"),
        "commute_car_petrol_kgco2e_km":             Decimal("0.1700"),
        "commute_car_diesel_kgco2e_km":             Decimal("0.1600"),
        "commute_car_hybrid_kgco2e_km":             Decimal("0.1054"),
        "commute_car_ev_kgco2e_km":                 Decimal("0.0531"),
        "commute_bus_kgco2e_km":                    Decimal("0.0982"),
        "commute_train_kgco2e_km":                  Decimal("0.0410"),
        "commute_metro_kgco2e_km":                  Decimal("0.0280"),
        "commute_cycling_kgco2e_km":                Decimal("0.0000"),
        "electricity_grid_eu_avg_kgco2e_kwh":       Decimal("0.2760"),
        "electricity_grid_uk_kgco2e_kwh":           Decimal("0.2070"),
        "electricity_grid_us_kgco2e_kwh":           Decimal("0.3860"),
        "electricity_grid_cn_kgco2e_kwh":           Decimal("0.5810"),
    }

    # Uncertainty by method (percentage, +/- 1 sigma) -- GHG Protocol Scope 3 Std Ch 7
    UNCERTAINTY_BY_METHOD: Dict[CalculationMethod, Decimal] = {
        CalculationMethod.SPEND_BASED:       Decimal("50"),
        CalculationMethod.AVERAGE_DATA:      Decimal("30"),
        CalculationMethod.HYBRID:            Decimal("25"),
        CalculationMethod.SUPPLIER_SPECIFIC: Decimal("10"),
        CalculationMethod.PHYSICAL_ACTIVITY: Decimal("15"),
    }

    # SBTi-relevant Scope 3 categories
    _SBTI_RELEVANT_CATS = frozenset({
        Scope3Category.CAT1,  Scope3Category.CAT2,  Scope3Category.CAT4,
        Scope3Category.CAT6,  Scope3Category.CAT7,  Scope3Category.CAT11,
        Scope3Category.CAT12, Scope3Category.CAT15,
    })

# ---------------------------------------------------------------------------
# Scope3Engine class
# ---------------------------------------------------------------------------

class Scope3Engine:
    """
    Calculates GHG Protocol Scope 3 emissions for all fifteen categories.
    Supports spend-based, average-data, physical-activity, hybrid, and
    supplier-specific methods with uncertainty quantification.
    """

    SPEND_BASED_EMISSION_FACTORS: Dict[str, Decimal] = {
        "Energy":                  Decimal("0.850"),
        "Materials":               Decimal("0.620"),
        "Industrials":             Decimal("0.420"),
        "Consumer Discretionary":  Decimal("0.310"),
        "Consumer Staples":        Decimal("0.380"),
        "Health Care":             Decimal("0.260"),
        "Financials":              Decimal("0.150"),
        "Information Technology":  Decimal("0.180"),
        "Communication Services":  Decimal("0.160"),
        "Utilities":               Decimal("0.720"),
        "Real Estate":             Decimal("0.280"),
        "Transportation":          Decimal("0.480"),
        "Food & Beverage":         Decimal("0.540"),
        "Agriculture":             Decimal("0.780"),
        "Mining":                  Decimal("0.690"),
        "Chemicals":               Decimal("0.680"),
        "Textiles & Apparel":      Decimal("0.350"),
        "Freight & Logistics":     Decimal("0.490"),
        "Paper & Packaging":       Decimal("0.520"),
        "Waste Management":        Decimal("0.440"),
        "Construction":            Decimal("0.410"),
        "Professional Services":   Decimal("0.130"),
        "Unknown":                 Decimal("0.350"),
    }

    PHYSICAL_EF_LIBRARY: Dict[str, Decimal] = {
        "freight_road_hgv_kgco2e_tonne_km":         Decimal("0.1465"),
        "freight_road_lgv_kgco2e_tonne_km":         Decimal("0.2464"),
        "freight_sea_container_kgco2e_tonne_km":    Decimal("0.0106"),
        "freight_sea_tanker_kgco2e_tonne_km":       Decimal("0.0118"),
        "freight_air_kgco2e_tonne_km":              Decimal("0.6020"),
        "freight_rail_kgco2e_tonne_km":             Decimal("0.0279"),
        "business_travel_air_shorthaul_kgco2e_pkm": Decimal("0.1554"),
        "business_travel_air_longhaul_kgco2e_pkm":  Decimal("0.1949"),
        "business_travel_air_business_kgco2e_pkm":  Decimal("0.4285"),
        "business_travel_rail_kgco2e_pkm":          Decimal("0.0035"),
        "business_travel_car_kgco2e_pkm":           Decimal("0.1421"),
        "business_travel_taxi_kgco2e_pkm":          Decimal("0.1490"),
        "hotel_night_uk_kgco2e":                    Decimal("20.8"),
        "hotel_night_europe_kgco2e":                Decimal("18.5"),
        "hotel_night_global_kgco2e":                Decimal("31.2"),
        "commute_car_petrol_kgco2e_km":             Decimal("0.1700"),
        "commute_car_diesel_kgco2e_km":             Decimal("0.1600"),
        "commute_car_hybrid_kgco2e_km":             Decimal("0.1054"),
        "commute_car_ev_kgco2e_km":                 Decimal("0.0531"),
        "commute_bus_kgco2e_km":                    Decimal("0.0982"),
        "commute_train_kgco2e_km":                  Decimal("0.0410"),
        "commute_metro_kgco2e_km":                  Decimal("0.0280"),
        "commute_cycling_kgco2e_km":                Decimal("0.0000"),
        "electricity_grid_eu_avg_kgco2e_kwh":       Decimal("0.2760"),
        "electricity_grid_uk_kgco2e_kwh":           Decimal("0.2070"),
        "electricity_grid_us_kgco2e_kwh":           Decimal("0.3860"),
        "electricity_grid_cn_kgco2e_kwh":           Decimal("0.5810"),
    }

    UNCERTAINTY_BY_METHOD: Dict[CalculationMethod, Decimal] = {
        CalculationMethod.SPEND_BASED:       Decimal("50"),
        CalculationMethod.AVERAGE_DATA:      Decimal("30"),
        CalculationMethod.HYBRID:            Decimal("25"),
        CalculationMethod.SUPPLIER_SPECIFIC: Decimal("10"),
        CalculationMethod.PHYSICAL_ACTIVITY: Decimal("15"),
    }

    _SBTI_RELEVANT_CATS = frozenset({
        Scope3Category.CAT1, Scope3Category.CAT2, Scope3Category.CAT4,
        Scope3Category.CAT6, Scope3Category.CAT7, Scope3Category.CAT11,
        Scope3Category.CAT12, Scope3Category.CAT15,
    })

    def _get_spend_ef(self, sector_gics: str) -> Decimal:
        """Retrieve spend-based EF for a GICS sector; fallback to Unknown."""
        return self.SPEND_BASED_EMISSION_FACTORS.get(
            sector_gics, self.SPEND_BASED_EMISSION_FACTORS["Unknown"]
        )

    def _build_result(
        self,
        category: Scope3Category,
        co2e_kg: Decimal,
        method: CalculationMethod,
        ef: Decimal,
        ef_unit: str,
        ef_source: str,
        dq: DataQuality,
        notes: str = "",
    ) -> Scope3CategoryResult:
        """Convert kgCO2e to tCO2e and assemble a Scope3CategoryResult."""
        co2e_tonnes = (co2e_kg / Decimal("1000")).quantize(
            Decimal("0.001"), rounding=ROUND_HALF_UP)
        uncertainty = self.UNCERTAINTY_BY_METHOD.get(method, Decimal("30"))
        return Scope3CategoryResult(
            category=category,
            co2e_tonnes=co2e_tonnes,
            method_used=method,
            emission_factor=ef,
            emission_factor_unit=ef_unit,
            emission_factor_source=ef_source,
            data_quality=dq,
            uncertainty_pct=uncertainty,
            sbti_relevant=(category in self._SBTI_RELEVANT_CATS),
            notes=notes,
        )

    def calculate_cat1_purchased_goods(
        self, activities: List[ActivityData]
    ) -> Scope3CategoryResult:
        """
        Category 1: Purchased Goods and Services.
        
        Spend-based: emissions = spend_usd * sector_ef (kgCO2e/USD)
        Average-data: emissions = quantity * material EF (kgCO2e/unit)
        Supplier-specific: quantity treated as direct kgCO2e.
        
        Largest Scope 3 category for most companies; highest SBTi priority.
        """
        total_kg = Decimal("0")
        primary_spend = Decimal("0")
        ef_sum = Decimal("0")
        ef_count = 0
        method_used = CalculationMethod.SPEND_BASED
        dq_worst = DataQuality.TIER3_ESTIMATED
        
        for act in activities:
            if act.preferred_method == CalculationMethod.PHYSICAL_ACTIVITY:
                product_ef = Decimal("0.500")  # 0.5 kgCO2e/kg default avg material EF
                kg = act.quantity * product_ef
                method_used = CalculationMethod.AVERAGE_DATA
                dq_worst = DataQuality.TIER2_SECONDARY
            elif act.preferred_method == CalculationMethod.SUPPLIER_SPECIFIC:
                kg = act.quantity  # direct kgCO2e from supplier
                method_used = CalculationMethod.SUPPLIER_SPECIFIC
                dq_worst = DataQuality.TIER1_PRIMARY
            else:
                sector_ef = self._get_spend_ef(act.sector_gics)
                kg = act.spend_usd * sector_ef
                ef_sum += sector_ef
                ef_count += 1
            total_kg += kg
            primary_spend += act.spend_usd
        
        avg_ef = ef_sum / Decimal(str(ef_count)) if ef_count > 0 else Decimal("0.350")
        n_acts = len(activities)
        spend_fmt = round(float(primary_spend), 0)
        note = f"Total USD spend: {spend_fmt:,.0f}; Activities count: {n_acts}"
        
        return self._build_result(
            category=Scope3Category.CAT1,
            co2e_kg=total_kg,
            method=method_used,
            ef=avg_ef,
            ef_unit="kgCO2e/USD",
            ef_source="EPA USEEIO v2.0 / Exiobase 3.8",
            dq=dq_worst,
            notes=note,
        )

    def calculate_cat4_upstream_transport(
        self, activities: List[ActivityData]
    ) -> Scope3CategoryResult:
        """
        Category 4: Upstream Transportation and Distribution.
        
        Physical: tonne-km * mode-specific EF (kgCO2e/tonne-km)
        Spend-based: freight spend * freight sector EF (kgCO2e/USD)
        
        Transport mode determined from activity unit field.
        """
        total_kg = Decimal("0")
        method_used = CalculationMethod.PHYSICAL_ACTIVITY
        ef_used = self.PHYSICAL_EF_LIBRARY["freight_road_hgv_kgco2e_tonne_km"]
        
        mode_ef_map = {
            "road":  self.PHYSICAL_EF_LIBRARY["freight_road_hgv_kgco2e_tonne_km"],
            "hgv":   self.PHYSICAL_EF_LIBRARY["freight_road_hgv_kgco2e_tonne_km"],
            "lgv":   self.PHYSICAL_EF_LIBRARY["freight_road_lgv_kgco2e_tonne_km"],
            "sea":   self.PHYSICAL_EF_LIBRARY["freight_sea_container_kgco2e_tonne_km"],
            "ship":  self.PHYSICAL_EF_LIBRARY["freight_sea_container_kgco2e_tonne_km"],
            "air":   self.PHYSICAL_EF_LIBRARY["freight_air_kgco2e_tonne_km"],
            "rail":  self.PHYSICAL_EF_LIBRARY["freight_rail_kgco2e_tonne_km"],
        }
        
        for act in activities:
            if act.preferred_method == CalculationMethod.SPEND_BASED:
                ef = self._get_spend_ef("Freight & Logistics")
                kg = act.spend_usd * ef
                ef_used = ef
                method_used = CalculationMethod.SPEND_BASED
            else:
                mode_key = act.unit.lower().strip()
                ef = mode_ef_map.get(mode_key, self.PHYSICAL_EF_LIBRARY["freight_road_hgv_kgco2e_tonne_km"])
                ef_used = ef
                kg = act.quantity * ef   # quantity in tonne-km
            total_kg += kg
        
        dq = (DataQuality.TIER1_PRIMARY if method_used == CalculationMethod.PHYSICAL_ACTIVITY
              else DataQuality.TIER3_ESTIMATED)
        return self._build_result(
            category=Scope3Category.CAT4,
            co2e_kg=total_kg,
            method=method_used,
            ef=ef_used,
            ef_unit="kgCO2e/tonne-km",
            ef_source="DEFRA 2023 Freight Transport EFs",
            dq=dq,
            notes=f"Activities: {len(activities)}",
        )

    def calculate_cat6_business_travel(
        self, activities: List[ActivityData]
    ) -> Scope3CategoryResult:
        """
        Category 6: Business Travel.
        
        Physical activity method per transport mode:
          - Air: short-haul (<3700 km) or long-haul, economy or business class
          - Rail: national rail average
          - Car / taxi: per passenger-km
          - Hotel nights: per night with regional EF
        
        Activity unit field identifies the transport mode.
        """
        total_kg = Decimal("0")
        
        mode_ef_map = {
            "air_short":    self.PHYSICAL_EF_LIBRARY["business_travel_air_shorthaul_kgco2e_pkm"],
            "air_long":     self.PHYSICAL_EF_LIBRARY["business_travel_air_longhaul_kgco2e_pkm"],
            "air_business": self.PHYSICAL_EF_LIBRARY["business_travel_air_business_kgco2e_pkm"],
            "air":          self.PHYSICAL_EF_LIBRARY["business_travel_air_shorthaul_kgco2e_pkm"],
            "rail":         self.PHYSICAL_EF_LIBRARY["business_travel_rail_kgco2e_pkm"],
            "car":          self.PHYSICAL_EF_LIBRARY["business_travel_car_kgco2e_pkm"],
            "taxi":         self.PHYSICAL_EF_LIBRARY["business_travel_taxi_kgco2e_pkm"],
            "hotel_uk":     self.PHYSICAL_EF_LIBRARY["hotel_night_uk_kgco2e"],
            "hotel_europe": self.PHYSICAL_EF_LIBRARY["hotel_night_europe_kgco2e"],
            "hotel":        self.PHYSICAL_EF_LIBRARY["hotel_night_global_kgco2e"],
        }
        
        ef_used = self.PHYSICAL_EF_LIBRARY["business_travel_air_shorthaul_kgco2e_pkm"]
        
        for act in activities:
            if act.preferred_method == CalculationMethod.SPEND_BASED:
                ef = self._get_spend_ef("Transportation")
                kg = act.spend_usd * ef
            else:
                mode_key = act.unit.lower().strip().replace(" ", "_")
                ef = mode_ef_map.get(mode_key, self.PHYSICAL_EF_LIBRARY["business_travel_air_shorthaul_kgco2e_pkm"])
                ef_used = ef
                kg = act.quantity * ef  # quantity: pkm for travel, nights for hotel
            total_kg += kg
        
        return self._build_result(
            category=Scope3Category.CAT6,
            co2e_kg=total_kg,
            method=CalculationMethod.PHYSICAL_ACTIVITY,
            ef=ef_used,
            ef_unit="kgCO2e/pkm or kgCO2e/hotel-night",
            ef_source="DEFRA 2023 Business Travel EFs",
            dq=DataQuality.TIER1_PRIMARY,
            notes=f"Activities: {len(activities)}",
        )

    def calculate_cat7_commuting(
        self, activities: List[ActivityData]
    ) -> Scope3CategoryResult:
        """
        Category 7: Employee Commuting.
        
        Physical: employees * commute_km_per_day * working_days * modal_ef
        Or direct: quantity = total employee-km, unit = commute mode key.
        
        Default modal mix: 60% car (petrol), 20% train, 10% bus, 10% active.
        """
        total_kg = Decimal("0")
        
        mode_ef_map = {
            "car_petrol":  self.PHYSICAL_EF_LIBRARY["commute_car_petrol_kgco2e_km"],
            "car_diesel":  self.PHYSICAL_EF_LIBRARY["commute_car_diesel_kgco2e_km"],
            "car_hybrid":  self.PHYSICAL_EF_LIBRARY["commute_car_hybrid_kgco2e_km"],
            "car_ev":      self.PHYSICAL_EF_LIBRARY["commute_car_ev_kgco2e_km"],
            "car":         self.PHYSICAL_EF_LIBRARY["commute_car_petrol_kgco2e_km"],
            "bus":         self.PHYSICAL_EF_LIBRARY["commute_bus_kgco2e_km"],
            "train":       self.PHYSICAL_EF_LIBRARY["commute_train_kgco2e_km"],
            "metro":       self.PHYSICAL_EF_LIBRARY["commute_metro_kgco2e_km"],
            "cycling":     self.PHYSICAL_EF_LIBRARY["commute_cycling_kgco2e_km"],
        }
        
        # Default modal mix EF (kgCO2e/km)
        default_modal_ef = (
            Decimal("0.60") * self.PHYSICAL_EF_LIBRARY["commute_car_petrol_kgco2e_km"] +
            Decimal("0.20") * self.PHYSICAL_EF_LIBRARY["commute_train_kgco2e_km"] +
            Decimal("0.10") * self.PHYSICAL_EF_LIBRARY["commute_bus_kgco2e_km"] +
            Decimal("0.10") * self.PHYSICAL_EF_LIBRARY["commute_cycling_kgco2e_km"]
        )
        ef_used = default_modal_ef
        
        for act in activities:
            mode_key = act.unit.lower().strip().replace(" ", "_")
            ef = mode_ef_map.get(mode_key, default_modal_ef)
            ef_used = ef
            # quantity: total employee-km (employees * one-way km * 2 * working_days)
            kg = act.quantity * ef
            total_kg += kg
        
        return self._build_result(
            category=Scope3Category.CAT7,
            co2e_kg=total_kg,
            method=CalculationMethod.AVERAGE_DATA,
            ef=ef_used,
            ef_unit="kgCO2e/km",
            ef_source="DEFRA 2023 Employee Commuting EFs",
            dq=DataQuality.TIER2_SECONDARY,
            notes=f"Activities: {len(activities)}. Default modal mix applied where mode not specified.",
        )

    def calculate_cat11_use_of_sold_products(
        self, activities: List[ActivityData]
    ) -> Scope3CategoryResult:
        """
        Category 11: Use of Sold Products.
        
        For energy-consuming products (appliances, electronics, vehicles):
          emissions = units_sold * annual_energy_kWh * grid_ef * product_lifetime_years
        
        Activity fields:
          quantity: units sold
          unit: product type key (e.g. laptop, smartphone, ev, appliance)
          spend_usd used as: annual_energy_kwh per unit (reused field for simplicity)
        """
        total_kg = Decimal("0")
        
        # Product energy profiles: (annual_kWh, lifetime_years, grid_ef_key)
        product_energy_map = {
            "laptop":     (Decimal("50"),   10, "electricity_grid_eu_avg_kgco2e_kwh"),
            "smartphone": (Decimal("4"),    3,  "electricity_grid_eu_avg_kgco2e_kwh"),
            "server":     (Decimal("3500"), 5,  "electricity_grid_eu_avg_kgco2e_kwh"),
            "appliance":  (Decimal("300"),  12, "electricity_grid_eu_avg_kgco2e_kwh"),
            "ev":         (Decimal("2500"), 10, "electricity_grid_eu_avg_kgco2e_kwh"),
            "boiler":     (Decimal("12000"),15, "electricity_grid_eu_avg_kgco2e_kwh"),
        }
        ef_used = self.PHYSICAL_EF_LIBRARY["electricity_grid_eu_avg_kgco2e_kwh"]
        
        for act in activities:
            product_key = act.unit.lower().strip()
            if product_key in product_energy_map:
                annual_kwh, lifetime_yrs, grid_key = product_energy_map[product_key]
                grid_ef = self.PHYSICAL_EF_LIBRARY.get(grid_key, ef_used)
                ef_used = grid_ef
                kg = act.quantity * annual_kwh * grid_ef * Decimal(str(lifetime_yrs))
            else:
                # Fallback: use spend_usd as annual kWh proxy, 5-year lifetime
                annual_kwh = act.spend_usd if act.spend_usd > Decimal("0") else act.quantity * Decimal("100")
                grid_ef = self.PHYSICAL_EF_LIBRARY["electricity_grid_eu_avg_kgco2e_kwh"]
                kg = act.quantity * annual_kwh * grid_ef * Decimal("5")
            total_kg += kg
        
        return self._build_result(
            category=Scope3Category.CAT11,
            co2e_kg=total_kg,
            method=CalculationMethod.AVERAGE_DATA,
            ef=ef_used,
            ef_unit="kgCO2e/kWh (grid) * annual_kWh * lifetime_years",
            ef_source="DEFRA 2023 / IEA World Energy Outlook 2023 grid EFs",
            dq=DataQuality.TIER2_SECONDARY,
            notes=f"Units sold across {len(activities)} product lines. Lifetime energy use method.",
        )

    def calculate_cat15_investments(
        self, activities: List[ActivityData]
    ) -> Scope3CategoryResult:
        """
        Category 15: Investments.
        
        Delegates to PCAF financed emissions methodology.
        spend_usd field = investment value in USD (converted to EUR at 0.92)
        quantity field = reported financed emissions (kgCO2e) if available.
        
        If financed emissions are not available, use average-data spend-based
        approach with sector EFs as a proxy.
        """
        total_kg = Decimal("0")
        method_used = CalculationMethod.AVERAGE_DATA
        
        for act in activities:
            if act.quantity > Decimal("0") and act.preferred_method == CalculationMethod.SUPPLIER_SPECIFIC:
                # Direct financed emissions provided (kgCO2e)
                total_kg += act.quantity
                method_used = CalculationMethod.SUPPLIER_SPECIFIC
            else:
                # Spend-based proxy: investment_usd * sector_ef
                sector_ef = self._get_spend_ef(act.sector_gics)
                total_kg += act.spend_usd * sector_ef
        
        return self._build_result(
            category=Scope3Category.CAT15,
            co2e_kg=total_kg,
            method=method_used,
            ef=self._get_spend_ef("Financials"),
            ef_unit="kgCO2e/USD (PCAF financed emissions or spend-based proxy)",
            ef_source="PCAF Global GHG Accounting Standard v2.0 / EPA USEEIO v2.0",
            dq=DataQuality.TIER2_SECONDARY if method_used == CalculationMethod.AVERAGE_DATA else DataQuality.TIER1_PRIMARY,
            notes=f"Investment portfolios: {len(activities)}. PCAF attribution applied where data available.",
        )

    def calculate_all_categories(
        self, activities_by_category: Dict[Scope3Category, List[ActivityData]]
    ) -> Dict[str, Any]:
        """
        Calculate all available Scope 3 categories and aggregate totals.
        
        For categories without specific methods implemented, falls back to
        a spend-based calculation using the activity data provided.
        
        Returns a dict with individual category results, total co2e,
        SBTi-relevant subtotal, and a validation summary.
        """
        category_results: Dict[Scope3Category, Scope3CategoryResult] = {}
        
        # --- Dispatch to specific methods ---
        dispatch = {
            Scope3Category.CAT1:  self.calculate_cat1_purchased_goods,
            Scope3Category.CAT4:  self.calculate_cat4_upstream_transport,
            Scope3Category.CAT6:  self.calculate_cat6_business_travel,
            Scope3Category.CAT7:  self.calculate_cat7_commuting,
            Scope3Category.CAT11: self.calculate_cat11_use_of_sold_products,
            Scope3Category.CAT15: self.calculate_cat15_investments,
        }
        
        for cat, acts in activities_by_category.items():
            if not acts:
                continue
            try:
                if cat in dispatch:
                    result = dispatch[cat](acts)
                else:
                    # Generic spend-based fallback for unimplemented categories
                    total_kg = sum((a.spend_usd * self._get_spend_ef(a.sector_gics) for a in acts), Decimal("0"))
                    result = self._build_result(
                        category=cat,
                        co2e_kg=total_kg,
                        method=CalculationMethod.SPEND_BASED,
                        ef=self._get_spend_ef("Unknown"),
                        ef_unit="kgCO2e/USD (spend-based fallback)",
                        ef_source="EPA USEEIO v2.0",
                        dq=DataQuality.TIER3_ESTIMATED,
                        notes=f"Generic spend-based fallback for {cat.value}",
                    )
                category_results[cat] = result
            except Exception as exc:
                logger.error("Scope 3 Cat %s calculation failed: %s", cat.value, exc)
        
        total_co2e = sum((r.co2e_tonnes for r in category_results.values()), Decimal("0"))
        sbti_total = sum(
            (r.co2e_tonnes for r in category_results.values() if r.sbti_relevant),
            Decimal("0")
        )
        
        cat_breakdown = {
            cat.value: {
                "co2e_tco2e": float(res.co2e_tonnes),
                "method": res.method_used.value,
                "uncertainty_pct": float(res.uncertainty_pct),
                "sbti_relevant": res.sbti_relevant,
                "data_quality": res.data_quality.value,
                "notes": res.notes,
            }
            for cat, res in category_results.items()
        }
        
        return {
            "category_results": category_results,
            "total_co2e_tco2e": float(total_co2e.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)),
            "sbti_scope3_total_tco2e": float(sbti_total.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)),
            "category_breakdown": cat_breakdown,
            "categories_calculated": len(category_results),
            "validation_summary": {
                "standard": "GHG Protocol Corporate Value Chain (Scope 3) Standard (2011)",
                "calculation_date": datetime.utcnow().isoformat(),
                "categories_covered": [cat.value for cat in category_results],
                "total_co2e_tco2e": float(total_co2e),
                "sbti_relevant_pct": float((sbti_total / total_co2e * Decimal("100")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)) if total_co2e > Decimal("0") else 0.0,
            },
        }

    def generate_hotspot_analysis(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Rank Scope 3 categories by absolute emissions and identify hotspots.
        
        Flags top 3 emission contributors, calculates percentage contribution
        per category, and highlights SBTi-relevant categories.
        """
        cat_breakdown = results.get("category_breakdown", {})
        total_co2e = results.get("total_co2e_tco2e", 0.0)
        
        if total_co2e == 0:
            return {"error": "Zero total emissions -- no hotspot analysis possible."}
        
        ranked = sorted(cat_breakdown.items(), key=lambda x: x[1].get("co2e_tco2e", 0), reverse=True)
        
        hotspot_list = []
        for rank, (cat_name, cat_data) in enumerate(ranked, start=1):
            co2e = cat_data.get("co2e_tco2e", 0.0)
            pct = round(co2e / total_co2e * 100, 2) if total_co2e > 0 else 0.0
            hotspot_list.append({
                "rank": rank,
                "category": cat_name,
                "co2e_tco2e": co2e,
                "pct_of_total": pct,
                "is_hotspot": rank <= 3,
                "sbti_relevant": cat_data.get("sbti_relevant", False),
                "method": cat_data.get("method", "unknown"),
                "data_quality": cat_data.get("data_quality", "unknown"),
            })
        
        top3 = [h for h in hotspot_list if h["is_hotspot"]]
        sbti_cats = [h for h in hotspot_list if h["sbti_relevant"]]
        sbti_pct = sum(h["pct_of_total"] for h in sbti_cats)
        
        return {
            "ranked_categories": hotspot_list,
            "top_3_hotspots": top3,
            "sbti_relevant_categories": sbti_cats,
            "sbti_coverage_pct": round(sbti_pct, 2),
            "sbti_threshold_met": sbti_pct >= 40.0,
            "total_co2e_tco2e": total_co2e,
            "hotspot_commentary": {
                "primary_hotspot": top3[0]["category"] if top3 else "none",
                "hotspot_pct_total": sum(h["pct_of_total"] for h in top3),
                "recommended_actions": [
                    "Engage top 3 category suppliers for primary data collection.",
                    "Set supplier-specific reduction targets for hotspot categories.",
                    "Review spend-based EFs and upgrade to supplier-specific data.",
                    "Consider SBTi FLAG targets if food/land/agriculture categories present.",
                ],
            },
        }

    def calculate_sbti_scope3_target(
        self, results: Dict[str, Any], base_year: int, target_year: int, reduction_pct: Decimal,
    ) -> Dict[str, Any]:
        """
        Calculate SBTi-aligned Scope 3 reduction target and annual trajectory.
        """
        base_total = Decimal(str(results.get("sbti_scope3_total_tco2e", results.get("total_co2e_tco2e", 0.0))))
        if base_total <= Decimal("0"):
            return {"error": "Zero base emissions -- cannot calculate target."}
        years_to_target = target_year - base_year
        if years_to_target <= 0:
            return {"error": "target_year must be > base_year"}
        target_absolute = base_total * (Decimal("1") - reduction_pct / Decimal("100"))
        annual_rate = reduction_pct / Decimal(str(years_to_target))
        cagr_factor = Decimal(str(math.pow(float(Decimal("1") - reduction_pct / Decimal("100")), 1.0 / years_to_target)))
        
        trajectory = []
        for yr_offset in range(years_to_target + 1):
            year = base_year + yr_offset
            frac = Decimal(str(yr_offset)) / Decimal(str(years_to_target))
            linear_t   = base_total * (Decimal("1") - (reduction_pct / Decimal("100")) * frac)
            compound_t = base_total * (cagr_factor ** yr_offset)
            trajectory.append({
                "year": year,
                "linear_target_tco2e":   float(linear_t.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)),
                "compound_target_tco2e": float(compound_t.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)),
                "required_reduction_pct": round(float(reduction_pct * frac), 2),
            })
        
        pathway = "1.5C" if float(reduction_pct) >= 42 else ("WB2C" if float(reduction_pct) >= 25 else "Insufficient")
        return {
            "base_year": base_year,
            "target_year": target_year,
            "base_year_emissions_tco2e": float(base_total),
            "target_emissions_tco2e": float(target_absolute.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)),
            "required_reduction_pct": float(reduction_pct),
            "annual_linear_reduction_rate_pct": float(annual_rate.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
            "trajectory": trajectory,
            "sbti_alignment": {
                "pathway": pathway,
                "sbti_1_5c_compliant": float(reduction_pct) >= 42,
                "sbti_wb2c_compliant":  float(reduction_pct) >= 25,
                "note": "SBTi requires min 42 pct absolute Scope 3 reduction by 2030 under 1.5C pathway.",
            },
        }


# ---------------------------------------------------------------------------
# Module-level convenience function
# ---------------------------------------------------------------------------

def calculate_scope3_emissions(activities_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Module-level entry point for Scope 3 emissions calculation.
    
    Accepts a dict of activities keyed by Scope 3 category string,
    converts to ActivityData instances, runs the full Scope3Engine, and
    returns a serialisable result dict.
    
    Parameters
    ----------
    activities_data : dict
        Keys: Scope 3 category string (e.g. cat1_purchased_goods_services)
        Values: list of activity dicts with keys matching ActivityData fields.
        Optional top-level keys: sbti_base_year, sbti_target_year, sbti_reduction_pct
    
    Returns
    -------
    dict -- Keys: category_results, totals, hotspot_analysis, sbti_target,
            parse_errors, engine_version, calculation_timestamp
    """
    engine = Scope3Engine()
    activities_by_cat: Dict[Scope3Category, List[ActivityData]] = {}
    parse_errors: List[str] = []
    
    for cat_str, act_list in activities_data.items():
        if not isinstance(act_list, list):
            continue
        try:
            cat = Scope3Category(cat_str)
        except ValueError:
            parse_errors.append(f"Unknown category: {cat_str}")
            continue
        parsed_acts: List[ActivityData] = []
        for idx, raw in enumerate(act_list):
            try:
                act = ActivityData(
                    category=cat,
                    activity_description=raw.get("activity_description", ""),
                    quantity=Decimal(str(raw.get("quantity", "0"))),
                    unit=raw.get("unit", "usd"),
                    spend_usd=Decimal(str(raw.get("spend_usd", "0"))),
                    preferred_method=CalculationMethod(raw.get("preferred_method", CalculationMethod.SPEND_BASED.value)),
                    sector_gics=raw.get("sector_gics", "Unknown"),
                    country_iso=raw.get("country_iso", "XX"),
                )
                parsed_acts.append(act)
            except (KeyError, ValueError, InvalidOperation) as exc:
                desc = raw.get("activity_description", "unknown")
                msg = f"Cat {cat_str} row {idx} ({desc}): {exc}"
                logger.error("Scope3 parse error -- %s", msg)
                parse_errors.append(msg)
        if parsed_acts:
            activities_by_cat[cat] = parsed_acts
    
    if not activities_by_cat:
        return {
            "error": "No valid activity data parsed.",
            "parse_errors": parse_errors,
            "engine_version": "Scope3Engine v1.0",
        }
    
    all_results = engine.calculate_all_categories(activities_by_cat)
    hotspot     = engine.generate_hotspot_analysis(all_results)
    base_yr     = int(activities_data.get("sbti_base_year",   datetime.utcnow().year - 1))
    tgt_yr      = int(activities_data.get("sbti_target_year", 2030))
    red_pct     = Decimal(str(activities_data.get("sbti_reduction_pct", "42.0")))
    sbti_target = engine.calculate_sbti_scope3_target(all_results, base_yr, tgt_yr, red_pct)
    
    cat_output = {}
    for cat, res in all_results.get("category_results", {}).items():
        cat_output[cat.value] = {
            "co2e_tco2e":           float(res.co2e_tonnes),
            "method":               res.method_used.value,
            "emission_factor":      float(res.emission_factor),
            "emission_factor_unit":  res.emission_factor_unit,
            "emission_factor_source": res.emission_factor_source,
            "data_quality":         res.data_quality.value,
            "uncertainty_pct":      float(res.uncertainty_pct),
            "sbti_relevant":        res.sbti_relevant,
            "notes":                res.notes,
        }
    
    return {
        "category_results":   cat_output,
        "totals": {
            "total_scope3_co2e_tco2e": all_results["total_co2e_tco2e"],
            "sbti_scope3_total_tco2e": all_results["sbti_scope3_total_tco2e"],
            "categories_calculated":   all_results["categories_calculated"],
        },
        "hotspot_analysis":  hotspot,
        "sbti_target":       sbti_target,
        "validation_summary": all_results.get("validation_summary", {}),
        "parse_errors":      parse_errors,
        "engine_version":    "Scope3Engine v1.0 (GHG Protocol Corporate Value Chain Standard 2011)",
        "calculation_timestamp": datetime.utcnow().isoformat(),
    }

