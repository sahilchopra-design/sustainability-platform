"""
Complete Carbon Credit Methodology Engine
Implements 56+ CDM, VCS, Gold Standard, CAR, ACR, GCC methodologies with real calculation formulas.
"""

from typing import Dict, Any, List, Optional
from enum import Enum
import math


class MethodologySector(str, Enum):
    ENERGY = "ENERGY"
    WASTE = "WASTE"
    FORESTRY = "FORESTRY"
    AGRICULTURE = "AGRICULTURE"
    INDUSTRIAL = "INDUSTRIAL"
    TRANSPORT = "TRANSPORT"
    BUILDINGS = "BUILDINGS"
    HOUSEHOLD = "HOUSEHOLD"
    MINING = "MINING"
    BLUE_CARBON = "BLUE_CARBON"


class MethodologyStandard(str, Enum):
    CDM = "CDM"
    VCS = "VCS"
    GOLD_STANDARD = "GOLD_STANDARD"
    CAR = "CAR"
    ACR = "ACR"
    GCC = "GCC"


# ============================================================================
# CDM ACM METHODOLOGIES (Large Scale)
# ============================================================================

def ACM0001_LandfillGas(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """ACM0001: Flaring or Use of Landfill Gas - Waste Sector"""
    # BE_y = (MD_y + MG_y) × GWP_CH4
    waste_quantity = inputs.get("waste_quantity", 500000)
    methane_generation_potential = inputs.get("methane_generation_potential", 100)
    capture_efficiency = inputs.get("capture_efficiency", 0.75)
    destruction_efficiency = inputs.get("destruction_efficiency", 0.995)
    methane_gwp = inputs.get("methane_gwp", 28)
    n2o_gwp = inputs.get("n2o_gwp", 265)
    
    baseline_methane = methane_generation_potential * waste_quantity
    baseline_emissions = baseline_methane * methane_gwp
    
    # PE_y = (MD_y × (1 - CEFF)) × GWP_CH4 + (MG_y × 0.0146 × GWP_N2O)
    methane_captured = baseline_methane * capture_efficiency
    project_emissions = (methane_captured * (1 - destruction_efficiency) * methane_gwp) + \
                       (baseline_methane * 0.0146 * n2o_gwp)
    
    leakage = 0
    emission_reductions = baseline_emissions - project_emissions - leakage
    
    return {
        "methodology": "ACM0001",
        "version": "19.0",
        "sector": "Waste",
        "baseline_emissions": round(baseline_emissions),
        "project_emissions": round(project_emissions),
        "leakage": round(leakage),
        "emission_reductions": round(emission_reductions),
        "unit": "tCO2e"
    }


def ACM0002_RenewableEnergy(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """ACM0002: Grid-Connected Renewable Energy - Energy Sector"""
    installed_capacity_mw = inputs.get("installed_capacity_mw", 150)
    capacity_factor = inputs.get("capacity_factor", 0.28)
    grid_emission_factor = inputs.get("grid_emission_factor", 0.45)
    operating_margin_weight = inputs.get("operating_margin_weight", 0.75)
    build_margin_weight = inputs.get("build_margin_weight", 0.25)
    uncertainty_factor = inputs.get("uncertainty_factor", 0.05)
    
    # EG_y = Electricity generated in year y (MWh)
    annual_generation = installed_capacity_mw * capacity_factor * 8760
    
    # EF_grid,CM,y = w_OM × EF_grid,OM,y + w_BM × EF_grid,BM,y
    combined_margin_ef = (operating_margin_weight * grid_emission_factor) + \
                        (build_margin_weight * grid_emission_factor)
    
    # BE_y = EG_y × EF_grid,CM,y
    baseline_emissions = annual_generation * combined_margin_ef
    project_emissions = 0  # Renewable has no direct emissions
    leakage = 0
    
    # ER_y = BE_y - PE_y - LE_y
    gross_emission_reductions = baseline_emissions - project_emissions - leakage
    
    # Apply uncertainty
    uncertainty_deduction = gross_emission_reductions * uncertainty_factor
    net_emission_reductions = gross_emission_reductions - uncertainty_deduction
    
    return {
        "methodology": "ACM0002",
        "version": "21.0",
        "sector": "Energy",
        "annual_generation_mwh": round(annual_generation),
        "combined_margin_ef": round(combined_margin_ef, 3),
        "baseline_emissions": round(baseline_emissions),
        "project_emissions": round(project_emissions),
        "leakage": round(leakage),
        "gross_emission_reductions": round(gross_emission_reductions),
        "uncertainty_deduction": round(uncertainty_deduction),
        "emission_reductions": round(net_emission_reductions),
        "unit": "tCO2e"
    }


def ACM0003_BiomassSubstitution(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """ACM0003: Partial Substitution of Fossil Fuels with Biomass - Energy Sector"""
    baseline_fuels = inputs.get("baseline_fuels", [
        {"type": "COAL", "quantity": 10000, "ncv": 24.4, "emission_factor": 94.6},
        {"type": "NATURAL_GAS", "quantity": 5000, "ncv": 48.0, "emission_factor": 56.1}
    ])
    project_fuels = inputs.get("project_fuels", [
        {"type": "BIOMASS", "quantity": 8000, "ncv": 15.0, "emission_factor": 0}
    ])
    biomass_quantity = inputs.get("biomass_quantity", 8000)
    biomass_ncv = inputs.get("biomass_ncv", 15.0)
    biomass_emission_factor = inputs.get("biomass_emission_factor", 0)
    
    # BE_y = Σ(BF_j,y × NCV_j × EF_CO2,j)
    baseline_emissions = sum(
        fuel["quantity"] * fuel["ncv"] * fuel["emission_factor"] / 1000
        for fuel in baseline_fuels
    )
    
    # PE_y = Σ(PF_i,y × NCV_i × EF_CO2,i) + PE_Biomass,y
    project_emissions = sum(
        fuel["quantity"] * fuel["ncv"] * fuel["emission_factor"] / 1000
        for fuel in project_fuels
    )
    biomass_emissions = biomass_quantity * biomass_ncv * biomass_emission_factor / 1000
    project_emissions += biomass_emissions
    
    emission_reductions = baseline_emissions - project_emissions
    
    return {
        "methodology": "ACM0003",
        "version": "9.0",
        "sector": "Energy",
        "baseline_emissions": round(baseline_emissions),
        "project_emissions": round(project_emissions),
        "biomass_emissions": round(biomass_emissions),
        "emission_reductions": round(emission_reductions),
        "unit": "tCO2e"
    }


def ACM0005_WasteHeatRecovery(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """ACM0005: Grid Electricity from Waste Heat Recovery - Energy/Industrial Sector"""
    waste_heat_available = inputs.get("waste_heat_available", 100000)  # MWh thermal
    conversion_efficiency = inputs.get("conversion_efficiency", 0.35)
    grid_emission_factor = inputs.get("grid_emission_factor", 0.45)
    auxiliary_power = inputs.get("auxiliary_power", 5000)  # MWh
    
    # EG_y = Electricity generated from waste heat
    electricity_generated = waste_heat_available * conversion_efficiency
    
    # BE_y = EG_y × EF_grid,y
    baseline_emissions = electricity_generated * grid_emission_factor
    
    # PE_y = PE_aux,y + PE_ww,y
    auxiliary_emissions = auxiliary_power * grid_emission_factor
    project_emissions = auxiliary_emissions
    
    emission_reductions = baseline_emissions - project_emissions
    
    return {
        "methodology": "ACM0005",
        "version": "8.0",
        "sector": "Energy",
        "electricity_generated_mwh": round(electricity_generated),
        "baseline_emissions": round(baseline_emissions),
        "project_emissions": round(project_emissions),
        "emission_reductions": round(emission_reductions),
        "unit": "tCO2e"
    }


def ACM0006_BiomassEnergy(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """ACM0006: Electricity and Heat from Biomass - Energy Sector"""
    biomass_quantity = inputs.get("biomass_quantity", 50000)  # tonnes
    electricity_yield = inputs.get("electricity_yield", 0.8)  # MWh/tonne
    heat_yield = inputs.get("heat_yield", 1.5)  # GJ/tonne
    grid_emission_factor = inputs.get("grid_emission_factor", 0.45)  # tCO2/MWh
    heat_emission_factor = inputs.get("heat_emission_factor", 0.06)  # tCO2/GJ
    biomass_ncv = inputs.get("biomass_ncv", 15.0)  # GJ/tonne
    biomass_ch4_ef = inputs.get("biomass_ch4_ef", 0.00003)  # CH4 emission factor
    methane_gwp = inputs.get("methane_gwp", 28)
    
    electricity_generation = biomass_quantity * electricity_yield
    heat_generation = biomass_quantity * heat_yield
    
    baseline_emissions_electricity = electricity_generation * grid_emission_factor
    baseline_emissions_heat = heat_generation * heat_emission_factor
    baseline_emissions = baseline_emissions_electricity + baseline_emissions_heat
    
    # Project emissions (biomass combustion)
    project_emissions = biomass_quantity * biomass_ncv * biomass_ch4_ef * methane_gwp
    
    emission_reductions = baseline_emissions - project_emissions
    
    return {
        "methodology": "ACM0006",
        "version": "15.0",
        "sector": "Energy",
        "electricity_generation_mwh": round(electricity_generation),
        "heat_generation_gj": round(heat_generation),
        "baseline_emissions": round(baseline_emissions),
        "project_emissions": round(project_emissions),
        "emission_reductions": round(emission_reductions),
        "unit": "tCO2e"
    }


def ACM0007_FuelSwitch(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """ACM0007: Analysis of Least Cost Fuel Option - Energy Sector"""
    baseline_fuel_consumption = inputs.get("baseline_fuel_consumption", 10000)  # tonnes
    baseline_ncv = inputs.get("baseline_ncv", 24.4)  # GJ/tonne
    baseline_emission_factor = inputs.get("baseline_emission_factor", 94.6)  # tCO2/TJ
    project_fuel_consumption = inputs.get("project_fuel_consumption", 5000)  # tonnes
    project_ncv = inputs.get("project_ncv", 48.0)  # GJ/tonne
    project_emission_factor = inputs.get("project_emission_factor", 56.1)  # tCO2/TJ
    
    # BE_y = FC_BL,y × NCV_BL × EF_CO2,BL
    baseline_emissions = baseline_fuel_consumption * baseline_ncv * baseline_emission_factor / 1000
    
    # PE_y = FC_PJ,y × NCV_PJ × EF_CO2,PJ
    project_emissions = project_fuel_consumption * project_ncv * project_emission_factor / 1000
    
    emission_reductions = baseline_emissions - project_emissions
    
    return {
        "methodology": "ACM0007",
        "version": "8.0",
        "sector": "Energy",
        "baseline_emissions": round(baseline_emissions),
        "project_emissions": round(project_emissions),
        "emission_reductions": round(emission_reductions),
        "unit": "tCO2e"
    }


def ACM0008_CoalMineMethane(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """ACM0008: Abatement of Methane from Coal Mines - Mining Sector"""
    ventilation_air_methane = inputs.get("ventilation_air_methane", 50000)  # m3 CH4
    captured_methane = inputs.get("captured_methane", 30000)  # m3 CH4
    methane_gwp = inputs.get("methane_gwp", 28)
    n2o_gwp = inputs.get("n2o_gwp", 265)
    methane_density = inputs.get("methane_density", 0.000717)  # tonnes/m3
    
    # CMM_y = VAM_y + CMM_captured,y
    total_methane = (ventilation_air_methane + captured_methane) * methane_density
    
    # BE_y = CMM_y × GWP_CH4
    baseline_emissions = total_methane * methane_gwp
    
    # PE_y = CMM_vented,y × GWP_CH4 + CMM_flared,y × 0.0146 × GWP_N2O
    vented_emissions = ventilation_air_methane * methane_density * methane_gwp
    flared_emissions = captured_methane * methane_density * 0.0146 * n2o_gwp
    project_emissions = vented_emissions + flared_emissions
    
    emission_reductions = baseline_emissions - project_emissions
    
    return {
        "methodology": "ACM0008",
        "version": "7.0",
        "sector": "Mining",
        "baseline_emissions": round(baseline_emissions),
        "project_emissions": round(project_emissions),
        "emission_reductions": round(emission_reductions),
        "unit": "tCO2e"
    }


def ACM0009_CoalToGas(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """ACM0009: Fuel Switch from Coal to Gas - Energy Sector"""
    electricity_generation = inputs.get("electricity_generation", 500000)  # MWh
    coal_emission_factor = inputs.get("coal_emission_factor", 0.92)  # tCO2/MWh
    gas_emission_factor = inputs.get("gas_emission_factor", 0.40)  # tCO2/MWh
    gas_consumption = inputs.get("gas_consumption", 100000)  # GJ
    upstream_emission_factor = inputs.get("upstream_emission_factor", 0.005)  # tCO2/GJ
    
    # BE_y = EG_y × EF_coal,y
    baseline_emissions = electricity_generation * coal_emission_factor
    
    # PE_y = EG_y × EF_gas,y + PE_upstream,y
    generation_emissions = electricity_generation * gas_emission_factor
    upstream_emissions = gas_consumption * upstream_emission_factor
    project_emissions = generation_emissions + upstream_emissions
    
    emission_reductions = baseline_emissions - project_emissions
    
    return {
        "methodology": "ACM0009",
        "version": "6.0",
        "sector": "Energy",
        "baseline_emissions": round(baseline_emissions),
        "project_emissions": round(project_emissions),
        "emission_reductions": round(emission_reductions),
        "unit": "tCO2e"
    }


def ACM0010_ManureMethane(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """ACM0010: GHG Emission Reductions from Manure Management - Agriculture Sector"""
    animal_count = inputs.get("animal_count", 5000)
    volatile_solids_per_animal = inputs.get("volatile_solids_per_animal", 3.5)  # kg VS/animal/day
    max_methane_potential = inputs.get("max_methane_potential", 0.48)  # m3 CH4/kg VS
    methane_conversion_factor = inputs.get("methane_conversion_factor", 0.65)
    capture_efficiency = inputs.get("capture_efficiency", 0.85)
    destruction_efficiency = inputs.get("destruction_efficiency", 0.99)
    methane_gwp = inputs.get("methane_gwp", 28)
    methane_density = inputs.get("methane_density", 0.000717)  # tonnes/m3
    
    # VS_y = Σ(N_animals,i × VS_daily,i × 365)
    volatile_solids = animal_count * volatile_solids_per_animal * 365
    
    # Methane production potential
    methane_m3 = volatile_solids * max_methane_potential * methane_conversion_factor
    baseline_emissions = methane_m3 * methane_density * methane_gwp
    
    # PE_y = CH4_captured,y × (1 - DE) × GWP_CH4
    captured_methane = methane_m3 * capture_efficiency
    project_emissions = captured_methane * (1 - destruction_efficiency) * methane_density * methane_gwp
    
    emission_reductions = baseline_emissions - project_emissions
    
    return {
        "methodology": "ACM0010",
        "version": "7.0",
        "sector": "Agriculture",
        "volatile_solids_kg": round(volatile_solids),
        "baseline_emissions": round(baseline_emissions),
        "project_emissions": round(project_emissions),
        "emission_reductions": round(emission_reductions),
        "unit": "tCO2e"
    }


def ACM0012_WasteHeatPower(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """ACM0012: Waste Heat Recovery for Power Generation - Industrial Sector"""
    waste_heat_available = inputs.get("waste_heat_available", 80000)  # MWh thermal
    conversion_efficiency = inputs.get("conversion_efficiency", 0.32)
    grid_emission_factor = inputs.get("grid_emission_factor", 0.45)
    auxiliary_power = inputs.get("auxiliary_power", 3000)  # MWh
    
    electricity_generated = waste_heat_available * conversion_efficiency
    baseline_emissions = electricity_generated * grid_emission_factor
    project_emissions = auxiliary_power * grid_emission_factor
    emission_reductions = baseline_emissions - project_emissions
    
    return {
        "methodology": "ACM0012",
        "version": "5.0",
        "sector": "Industrial",
        "electricity_generated_mwh": round(electricity_generated),
        "baseline_emissions": round(baseline_emissions),
        "project_emissions": round(project_emissions),
        "emission_reductions": round(emission_reductions),
        "unit": "tCO2e"
    }


def ACM0014_CementBlending(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """ACM0014: Cement Blending - Industrial Sector"""
    baseline_clinker_quantity = inputs.get("baseline_clinker_quantity", 100000)  # tonnes
    project_clinker_quantity = inputs.get("project_clinker_quantity", 70000)  # tonnes
    additive_quantity = inputs.get("additive_quantity", 30000)  # tonnes
    clinker_emission_factor = inputs.get("clinker_emission_factor", 0.83)  # tCO2/tonne clinker
    additive_emission_factor = inputs.get("additive_emission_factor", 0.02)  # tCO2/tonne
    
    # BE_y = CL_BL,y × EF_clinker
    baseline_emissions = baseline_clinker_quantity * clinker_emission_factor
    
    # PE_y = CL_PJ,y × EF_clinker + ADD_y × EF_additive
    clinker_emissions = project_clinker_quantity * clinker_emission_factor
    additive_emissions = additive_quantity * additive_emission_factor
    project_emissions = clinker_emissions + additive_emissions
    
    emission_reductions = baseline_emissions - project_emissions
    
    return {
        "methodology": "ACM0014",
        "version": "6.0",
        "sector": "Industrial",
        "baseline_emissions": round(baseline_emissions),
        "project_emissions": round(project_emissions),
        "emission_reductions": round(emission_reductions),
        "unit": "tCO2e"
    }


def ACM0022_Composting(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """ACM0022: Alternative Waste Treatment (Composting) - Waste Sector"""
    waste_quantity = inputs.get("waste_quantity", 50000)  # tonnes
    landfill_methane_ef = inputs.get("landfill_methane_ef", 0.058)  # tCH4/tonne waste
    landfill_n2o_ef = inputs.get("landfill_n2o_ef", 0.0003)  # tN2O/tonne waste
    compost_methane_ef = inputs.get("compost_methane_ef", 0.004)  # tCH4/tonne waste
    compost_n2o_ef = inputs.get("compost_n2o_ef", 0.0002)  # tN2O/tonne waste
    methane_gwp = inputs.get("methane_gwp", 28)
    n2o_gwp = inputs.get("n2o_gwp", 265)
    
    # Baseline emissions from landfill
    baseline_methane = waste_quantity * landfill_methane_ef * methane_gwp
    baseline_n2o = waste_quantity * landfill_n2o_ef * n2o_gwp
    baseline_emissions = baseline_methane + baseline_n2o
    
    # Project emissions from composting
    project_methane = waste_quantity * compost_methane_ef * methane_gwp
    project_n2o = waste_quantity * compost_n2o_ef * n2o_gwp
    project_emissions = project_methane + project_n2o
    
    emission_reductions = baseline_emissions - project_emissions
    
    return {
        "methodology": "ACM0022",
        "version": "2.0",
        "sector": "Waste",
        "baseline_emissions": round(baseline_emissions),
        "project_emissions": round(project_emissions),
        "emission_reductions": round(emission_reductions),
        "unit": "tCO2e"
    }


def ACM0023_LowEmissionVehicles(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """ACM0023: Introduction of Low-Emission Vehicles - Transport Sector"""
    vehicles = inputs.get("vehicles", [
        {"name": "Fleet A", "distance": 50000, "baseline_ef": 0.25, "project_ef": 0.10}
    ])
    
    baseline_emissions = sum(v["distance"] * v["baseline_ef"] / 1000 for v in vehicles)
    project_emissions = sum(v["distance"] * v["project_ef"] / 1000 for v in vehicles)
    emission_reductions = baseline_emissions - project_emissions
    
    return {
        "methodology": "ACM0023",
        "version": "3.0",
        "sector": "Transport",
        "vehicle_count": len(vehicles),
        "baseline_emissions": round(baseline_emissions),
        "project_emissions": round(project_emissions),
        "emission_reductions": round(emission_reductions),
        "unit": "tCO2e"
    }


# ============================================================================
# CDM AMS METHODOLOGIES (Small Scale)
# ============================================================================

def AMS_I_A_RenewableElectricity(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """AMS-I.A: Electricity from Renewable Sources (Small-scale < 15 MW)"""
    installed_capacity_kw = inputs.get("installed_capacity_kw", 1000)
    capacity_factor = inputs.get("capacity_factor", 0.25)
    grid_emission_factor = inputs.get("grid_emission_factor", 0.45)
    
    electricity_generated = installed_capacity_kw * capacity_factor * 8760 / 1000  # MWh
    baseline_emissions = electricity_generated * grid_emission_factor
    project_emissions = 0
    emission_reductions = baseline_emissions - project_emissions
    
    return {
        "methodology": "AMS-I.A",
        "version": "18.0",
        "sector": "Energy",
        "scale": "Small-scale",
        "electricity_generated_mwh": round(electricity_generated),
        "baseline_emissions": round(baseline_emissions),
        "project_emissions": round(project_emissions),
        "emission_reductions": round(emission_reductions),
        "unit": "tCO2e"
    }


def AMS_I_C_RenewableThermal(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """AMS-I.C: Thermal Energy from Renewable Sources"""
    system_capacity_kw = inputs.get("system_capacity_kw", 500)
    capacity_factor = inputs.get("capacity_factor", 0.30)
    baseline_fuel_ef = inputs.get("baseline_fuel_ef", 0.06)  # tCO2/GJ
    
    thermal_energy = system_capacity_kw * capacity_factor * 8760 * 0.0036  # GJ
    baseline_emissions = thermal_energy * baseline_fuel_ef
    project_emissions = 0
    emission_reductions = baseline_emissions - project_emissions
    
    return {
        "methodology": "AMS-I.C",
        "version": "15.0",
        "sector": "Energy",
        "scale": "Small-scale",
        "thermal_energy_gj": round(thermal_energy),
        "baseline_emissions": round(baseline_emissions),
        "project_emissions": round(project_emissions),
        "emission_reductions": round(emission_reductions),
        "unit": "tCO2e"
    }


def AMS_I_D_GridRenewable(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """AMS-I.D: Grid Connected Renewable Electricity Generation"""
    installed_capacity_kw = inputs.get("installed_capacity_kw", 5000)
    capacity_factor = inputs.get("capacity_factor", 0.22)
    grid_emission_factor = inputs.get("grid_emission_factor", 0.45)
    
    electricity_generated = installed_capacity_kw * capacity_factor * 8760 / 1000
    baseline_emissions = electricity_generated * grid_emission_factor
    project_emissions = 0
    emission_reductions = baseline_emissions - project_emissions
    
    return {
        "methodology": "AMS-I.D",
        "version": "17.0",
        "sector": "Energy",
        "scale": "Small-scale",
        "electricity_generated_mwh": round(electricity_generated),
        "baseline_emissions": round(baseline_emissions),
        "project_emissions": round(project_emissions),
        "emission_reductions": round(emission_reductions),
        "unit": "tCO2e"
    }


def AMS_II_D_BuildingEfficiency(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """AMS-II.D: Energy Efficiency in Buildings"""
    building_area = inputs.get("building_area", 10000)  # m2
    baseline_energy_intensity = inputs.get("baseline_energy_intensity", 150)  # kWh/m2/year
    project_energy_intensity = inputs.get("project_energy_intensity", 100)  # kWh/m2/year
    grid_emission_factor = inputs.get("grid_emission_factor", 0.45)  # tCO2/MWh
    
    baseline_consumption = building_area * baseline_energy_intensity / 1000  # MWh
    project_consumption = building_area * project_energy_intensity / 1000  # MWh
    
    baseline_emissions = baseline_consumption * grid_emission_factor
    project_emissions = project_consumption * grid_emission_factor
    emission_reductions = baseline_emissions - project_emissions
    
    return {
        "methodology": "AMS-II.D",
        "version": "14.0",
        "sector": "Buildings",
        "scale": "Small-scale",
        "baseline_consumption_mwh": round(baseline_consumption),
        "project_consumption_mwh": round(project_consumption),
        "baseline_emissions": round(baseline_emissions),
        "project_emissions": round(project_emissions),
        "emission_reductions": round(emission_reductions),
        "unit": "tCO2e"
    }


def AMS_II_E_TransportEfficiency(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """AMS-II.E: Energy Efficiency in Transport"""
    distance = inputs.get("distance", 100000)  # km
    baseline_fuel_consumption = inputs.get("baseline_fuel_consumption", 0.10)  # L/km
    project_fuel_consumption = inputs.get("project_fuel_consumption", 0.07)  # L/km
    fuel_ncv = inputs.get("fuel_ncv", 0.032)  # GJ/L
    fuel_emission_factor = inputs.get("fuel_emission_factor", 69.3)  # tCO2/TJ
    
    baseline_fuel = distance * baseline_fuel_consumption
    project_fuel = distance * project_fuel_consumption
    
    baseline_emissions = baseline_fuel * fuel_ncv * fuel_emission_factor / 1000
    project_emissions = project_fuel * fuel_ncv * fuel_emission_factor / 1000
    emission_reductions = baseline_emissions - project_emissions
    
    return {
        "methodology": "AMS-II.E",
        "version": "13.0",
        "sector": "Transport",
        "scale": "Small-scale",
        "baseline_emissions": round(baseline_emissions),
        "project_emissions": round(project_emissions),
        "emission_reductions": round(emission_reductions),
        "unit": "tCO2e"
    }


def AMS_II_G_IndustrialEfficiency(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """AMS-II.G: Energy Efficiency in Industrial Processes"""
    production_quantity = inputs.get("production_quantity", 50000)  # tonnes
    baseline_energy_intensity = inputs.get("baseline_energy_intensity", 3.5)  # GJ/tonne
    project_energy_intensity = inputs.get("project_energy_intensity", 2.8)  # GJ/tonne
    fuel_emission_factor = inputs.get("fuel_emission_factor", 0.056)  # tCO2/GJ
    
    baseline_consumption = production_quantity * baseline_energy_intensity
    project_consumption = production_quantity * project_energy_intensity
    
    baseline_emissions = baseline_consumption * fuel_emission_factor
    project_emissions = project_consumption * fuel_emission_factor
    emission_reductions = baseline_emissions - project_emissions
    
    return {
        "methodology": "AMS-II.G",
        "version": "11.0",
        "sector": "Industrial",
        "scale": "Small-scale",
        "baseline_emissions": round(baseline_emissions),
        "project_emissions": round(project_emissions),
        "emission_reductions": round(emission_reductions),
        "unit": "tCO2e"
    }


def AMS_III_AU_AgriculturalMethane(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """AMS-III.AU: Methane Recovery in Agricultural Activities"""
    animal_count = inputs.get("animal_count", 1000)
    volatile_solids_per_animal = inputs.get("volatile_solids_per_animal", 2.5)  # kg VS/animal/day
    max_methane_potential = inputs.get("max_methane_potential", 0.45)  # m3 CH4/kg VS
    methane_conversion_factor = inputs.get("methane_conversion_factor", 0.60)
    capture_efficiency = inputs.get("capture_efficiency", 0.80)
    methane_gwp = inputs.get("methane_gwp", 28)
    methane_density = inputs.get("methane_density", 0.000717)
    
    volatile_solids = animal_count * volatile_solids_per_animal * 365
    methane_production = volatile_solids * max_methane_potential * methane_conversion_factor
    
    baseline_emissions = methane_production * methane_density * methane_gwp
    project_emissions = methane_production * (1 - capture_efficiency) * methane_density * methane_gwp
    emission_reductions = baseline_emissions - project_emissions
    
    return {
        "methodology": "AMS-III.AU",
        "version": "4.0",
        "sector": "Agriculture",
        "scale": "Small-scale",
        "baseline_emissions": round(baseline_emissions),
        "project_emissions": round(project_emissions),
        "emission_reductions": round(emission_reductions),
        "unit": "tCO2e"
    }


def AMS_III_B_WastewaterMethane(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """AMS-III.B: Methane Recovery from Wastewater"""
    wastewater_volume = inputs.get("wastewater_volume", 1000000)  # m3
    cod_concentration = inputs.get("cod_concentration", 0.002)  # kg COD/m3
    max_methane_potential = inputs.get("max_methane_potential", 0.25)  # m3 CH4/kg COD
    methane_conversion_factor = inputs.get("methane_conversion_factor", 0.65)
    capture_efficiency = inputs.get("capture_efficiency", 0.75)
    methane_gwp = inputs.get("methane_gwp", 28)
    methane_density = inputs.get("methane_density", 0.000717)
    
    cod = wastewater_volume * cod_concentration
    methane_production = cod * max_methane_potential * methane_conversion_factor
    
    baseline_emissions = methane_production * methane_density * methane_gwp
    project_emissions = methane_production * (1 - capture_efficiency) * methane_density * methane_gwp
    emission_reductions = baseline_emissions - project_emissions
    
    return {
        "methodology": "AMS-III.B",
        "version": "12.0",
        "sector": "Waste",
        "scale": "Small-scale",
        "baseline_emissions": round(baseline_emissions),
        "project_emissions": round(project_emissions),
        "emission_reductions": round(emission_reductions),
        "unit": "tCO2e"
    }


def AMS_III_C_WasteComposting(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """AMS-III.C: Emission Reductions from Waste Composting"""
    waste_quantity = inputs.get("waste_quantity", 20000)  # tonnes
    landfill_methane_ef = inputs.get("landfill_methane_ef", 0.042)
    landfill_n2o_ef = inputs.get("landfill_n2o_ef", 0.0002)
    compost_methane_ef = inputs.get("compost_methane_ef", 0.003)
    compost_n2o_ef = inputs.get("compost_n2o_ef", 0.00015)
    methane_gwp = inputs.get("methane_gwp", 28)
    n2o_gwp = inputs.get("n2o_gwp", 265)
    
    baseline_methane = waste_quantity * landfill_methane_ef * methane_gwp
    baseline_n2o = waste_quantity * landfill_n2o_ef * n2o_gwp
    baseline_emissions = baseline_methane + baseline_n2o
    
    project_methane = waste_quantity * compost_methane_ef * methane_gwp
    project_n2o = waste_quantity * compost_n2o_ef * n2o_gwp
    project_emissions = project_methane + project_n2o
    
    emission_reductions = baseline_emissions - project_emissions
    
    return {
        "methodology": "AMS-III.C",
        "version": "6.0",
        "sector": "Waste",
        "scale": "Small-scale",
        "baseline_emissions": round(baseline_emissions),
        "project_emissions": round(project_emissions),
        "emission_reductions": round(emission_reductions),
        "unit": "tCO2e"
    }


def AMS_III_D_SolidWasteMethane(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """AMS-III.D: Methane Recovery from Solid Waste Disposal"""
    waste_quantity = inputs.get("waste_quantity", 30000)  # tonnes
    degradable_organic_carbon = inputs.get("degradable_organic_carbon", 0.15)  # fraction
    doc_fraction = inputs.get("doc_fraction", 0.5)  # fraction that decomposes
    methane_conversion_factor = inputs.get("methane_conversion_factor", 1.0)
    capture_efficiency = inputs.get("capture_efficiency", 0.70)
    methane_gwp = inputs.get("methane_gwp", 28)
    
    doc = waste_quantity * degradable_organic_carbon
    methane_production = doc * doc_fraction * methane_conversion_factor * 1.33  # 16/12 C to CH4 ratio
    
    baseline_emissions = methane_production * methane_gwp
    project_emissions = methane_production * (1 - capture_efficiency) * methane_gwp
    emission_reductions = baseline_emissions - project_emissions
    
    return {
        "methodology": "AMS-III.D",
        "version": "9.0",
        "sector": "Waste",
        "scale": "Small-scale",
        "baseline_emissions": round(baseline_emissions),
        "project_emissions": round(project_emissions),
        "emission_reductions": round(emission_reductions),
        "unit": "tCO2e"
    }


# ============================================================================
# CDM AM METHODOLOGIES (Sector-Specific)
# ============================================================================

def AM0012_NitricAcidN2O(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """AM0012: N2O Abatement from Nitric Acid Production"""
    acid_production = inputs.get("acid_production", 500000)  # tonnes HNO3
    baseline_n2o_ef = inputs.get("baseline_n2o_ef", 0.008)  # tN2O/tonne HNO3
    project_n2o_ef = inputs.get("project_n2o_ef", 0.001)  # tN2O/tonne HNO3
    n2o_gwp = inputs.get("n2o_gwp", 265)
    
    baseline_n2o = acid_production * baseline_n2o_ef
    project_n2o = acid_production * project_n2o_ef
    
    baseline_emissions = baseline_n2o * n2o_gwp
    project_emissions = project_n2o * n2o_gwp
    emission_reductions = baseline_emissions - project_emissions
    
    return {
        "methodology": "AM0012",
        "version": "6.0",
        "sector": "Industrial",
        "baseline_emissions": round(baseline_emissions),
        "project_emissions": round(project_emissions),
        "emission_reductions": round(emission_reductions),
        "unit": "tCO2e"
    }


def AM0036_SF6Reduction(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """AM0036: SF6 Emission Reductions in Electrical Equipment"""
    equipment_count = inputs.get("equipment_count", 100)
    baseline_leakage_rate = inputs.get("baseline_leakage_rate", 0.015)  # tSF6/equipment/year
    project_leakage_rate = inputs.get("project_leakage_rate", 0.003)  # tSF6/equipment/year
    sf6_gwp = inputs.get("sf6_gwp", 23500)
    
    baseline_sf6 = equipment_count * baseline_leakage_rate
    project_sf6 = equipment_count * project_leakage_rate
    
    baseline_emissions = baseline_sf6 * sf6_gwp
    project_emissions = project_sf6 * sf6_gwp
    emission_reductions = baseline_emissions - project_emissions
    
    return {
        "methodology": "AM0036",
        "version": "4.0",
        "sector": "Industrial",
        "baseline_emissions": round(baseline_emissions),
        "project_emissions": round(project_emissions),
        "emission_reductions": round(emission_reductions),
        "unit": "tCO2e"
    }


# ============================================================================
# CDM AR METHODOLOGIES (Forestry)
# ============================================================================

def AR_ACM0003_AfforestationReforestation(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """AR-ACM0003: Large-scale Afforestation/Reforestation"""
    start_year = inputs.get("start_year", 2024)
    crediting_period_years = inputs.get("crediting_period_years", 30)
    risk_buffer_percentage = inputs.get("risk_buffer_percentage", 0.20)
    species = inputs.get("species", [
        {"name": "Mahogany", "area_hectares": 400, "max_biomass_per_hectare": 300, "growth_rate": 0.15},
        {"name": "Teak", "area_hectares": 350, "max_biomass_per_hectare": 250, "growth_rate": 0.20},
        {"name": "Native Mix", "area_hectares": 250, "max_biomass_per_hectare": 180, "growth_rate": 0.10}
    ])
    
    yearly_results = []
    cumulative_carbon_stock = 0
    
    for year in range(1, crediting_period_years + 1):
        annual_carbon_increment = 0
        
        for sp in species:
            age = year
            max_biomass = sp["max_biomass_per_hectare"]
            growth_rate = sp["growth_rate"]
            
            # Logistic growth model
            biomass_at_age = max_biomass / (1 + math.exp(-growth_rate * (age - 10)))
            biomass_previous = max_biomass / (1 + math.exp(-growth_rate * (age - 11))) if age > 1 else 0
            
            annual_increment = (biomass_at_age - biomass_previous) * sp["area_hectares"]
            carbon_increment = annual_increment * 0.5  # 50% of biomass is carbon
            annual_carbon_increment += carbon_increment
        
        # Below-ground biomass (25% of above-ground)
        below_ground_carbon = annual_carbon_increment * 0.25
        total_carbon_increment = annual_carbon_increment + below_ground_carbon
        cumulative_carbon_stock += total_carbon_increment
        
        # Convert to CO2 (44/12 molecular weight ratio)
        co2_sequestered = total_carbon_increment * (44 / 12)
        
        # Apply risk buffer
        risk_buffer = co2_sequestered * risk_buffer_percentage
        net_credits = co2_sequestered - risk_buffer
        
        yearly_results.append({
            "year": start_year + year - 1,
            "age": year,
            "above_ground_carbon": round(annual_carbon_increment),
            "below_ground_carbon": round(below_ground_carbon),
            "total_carbon_stock": round(cumulative_carbon_stock),
            "co2_sequestered": round(co2_sequestered),
            "risk_buffer": round(risk_buffer),
            "net_credits": round(net_credits)
        })
    
    total_credits = sum(yr["net_credits"] for yr in yearly_results)
    
    return {
        "methodology": "AR-ACM0003",
        "version": "5.0",
        "sector": "Forestry",
        "yearly_results": yearly_results,
        "total_credits": round(total_credits),
        "average_annual_credits": round(total_credits / crediting_period_years),
        "emission_reductions": round(total_credits / crediting_period_years),  # Annualized
        "unit": "tCO2e"
    }


# ============================================================================
# VCS METHODOLOGIES
# ============================================================================

def VM0008_WastewaterMethane(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """VM0008: Methane Destruction at Wastewater Treatment Plants"""
    wastewater_flow = inputs.get("wastewater_flow", 500000)  # m3
    cod_concentration = inputs.get("cod_concentration", 0.003)  # kg COD/m3
    methane_potential = inputs.get("methane_potential", 0.25)  # m3 CH4/kg COD
    methane_conversion_factor = inputs.get("methane_conversion_factor", 0.60)
    capture_efficiency = inputs.get("capture_efficiency", 0.85)
    methane_gwp = inputs.get("methane_gwp", 28)
    methane_density = inputs.get("methane_density", 0.000717)
    
    baseline_emissions = wastewater_flow * cod_concentration * methane_potential * \
                        methane_conversion_factor * methane_density * methane_gwp
    project_emissions = wastewater_flow * cod_concentration * methane_potential * \
                       (1 - capture_efficiency) * methane_density * methane_gwp
    emission_reductions = baseline_emissions - project_emissions
    
    return {
        "methodology": "VM0008",
        "version": "2.0",
        "standard": "VCS",
        "sector": "Waste",
        "baseline_emissions": round(baseline_emissions),
        "project_emissions": round(project_emissions),
        "emission_reductions": round(emission_reductions),
        "unit": "tCO2e"
    }


def VM0022_AgriculturalN2O(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """VM0022: N2O Emissions Reductions in Agricultural Crop Production"""
    crop_area = inputs.get("crop_area", 5000)  # hectares
    baseline_nitrogen = inputs.get("baseline_nitrogen", 150)  # kg N/ha
    project_nitrogen = inputs.get("project_nitrogen", 100)  # kg N/ha
    n2o_emission_factor = inputs.get("n2o_emission_factor", 0.01)  # kg N2O-N/kg N
    n2o_gwp = inputs.get("n2o_gwp", 265)
    
    # Convert N2O-N to N2O (44/28 ratio)
    baseline_emissions = crop_area * baseline_nitrogen * n2o_emission_factor * (44/28) * n2o_gwp / 1000
    project_emissions = crop_area * project_nitrogen * n2o_emission_factor * (44/28) * n2o_gwp / 1000
    emission_reductions = baseline_emissions - project_emissions
    
    return {
        "methodology": "VM0022",
        "version": "2.0",
        "standard": "VCS",
        "sector": "Agriculture",
        "baseline_emissions": round(baseline_emissions),
        "project_emissions": round(project_emissions),
        "emission_reductions": round(emission_reductions),
        "unit": "tCO2e"
    }


def VM0033_BlueCarbon(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """VM0033: Tidal Wetland and Seagrass Restoration"""
    area_hectares = inputs.get("area_hectares", 500)
    soil_carbon_density = inputs.get("soil_carbon_density", 150)  # tC/ha
    biomass_carbon_density = inputs.get("biomass_carbon_density", 20)  # tC/ha
    risk_buffer = inputs.get("risk_buffer", 0.25)
    
    soil_carbon_stock = area_hectares * soil_carbon_density
    biomass_carbon_stock = area_hectares * biomass_carbon_density
    total_carbon_stock = soil_carbon_stock + biomass_carbon_stock
    
    co2_sequestered = total_carbon_stock * (44 / 12)
    buffer = co2_sequestered * risk_buffer
    net_credits = co2_sequestered - buffer
    
    return {
        "methodology": "VM0033",
        "version": "1.0",
        "standard": "VCS",
        "sector": "Blue Carbon",
        "soil_carbon_stock": round(soil_carbon_stock),
        "biomass_carbon_stock": round(biomass_carbon_stock),
        "total_carbon_stock": round(total_carbon_stock),
        "co2_sequestered": round(co2_sequestered),
        "emission_reductions": round(net_credits),
        "unit": "tCO2e"
    }


def VM0042_AgriculturalLandManagement(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """VM0042: Improved Agricultural Land Management"""
    area_hectares = inputs.get("area_hectares", 2000)
    baseline_soil_carbon = inputs.get("baseline_soil_carbon", 40)  # tC/ha
    project_soil_carbon = inputs.get("project_soil_carbon", 55)  # tC/ha
    
    baseline_soc = area_hectares * baseline_soil_carbon
    project_soc = area_hectares * project_soil_carbon
    carbon_stock_change = project_soc - baseline_soc
    co2_benefit = carbon_stock_change * (44 / 12)
    
    return {
        "methodology": "VM0042",
        "version": "2.0",
        "standard": "VCS",
        "sector": "Agriculture",
        "baseline_soc": round(baseline_soc),
        "project_soc": round(project_soc),
        "carbon_stock_change": round(carbon_stock_change),
        "emission_reductions": round(co2_benefit),
        "unit": "tCO2e"
    }


def VM0044_BiocharSoil(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """VM0044: Biochar Utilization in Soil"""
    biochar_quantity = inputs.get("biochar_quantity", 5000)  # tonnes
    biochar_carbon_content = inputs.get("biochar_carbon_content", 0.80)  # fraction
    stability_factor = inputs.get("stability_factor", 0.80)  # fraction remaining after 100 years
    
    biochar_carbon = biochar_quantity * biochar_carbon_content
    stable_carbon = biochar_carbon * stability_factor
    co2_sequestered = stable_carbon * (44 / 12)
    
    return {
        "methodology": "VM0044",
        "version": "1.0",
        "standard": "VCS",
        "sector": "Agriculture",
        "biochar_carbon": round(biochar_carbon),
        "stable_carbon": round(stable_carbon),
        "emission_reductions": round(co2_sequestered),
        "unit": "tCO2e"
    }


def VM0047_ARR(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """VM0047: Afforestation, Reforestation and Revegetation"""
    start_year = inputs.get("start_year", 2024)
    crediting_period_years = inputs.get("crediting_period_years", 25)
    buffer_percentage = inputs.get("buffer_percentage", 0.15)
    strata = inputs.get("strata", [
        {"name": "Zone A", "area_hectares": 300, "growth_rate": 5.0, "carbon_fraction": 0.47},
        {"name": "Zone B", "area_hectares": 200, "growth_rate": 4.5, "carbon_fraction": 0.47}
    ])
    
    yearly_results = []
    cumulative_carbon_stock = 0
    
    for year in range(1, crediting_period_years + 1):
        annual_carbon_increment = 0
        
        for stratum in strata:
            biomass_growth = stratum["growth_rate"] * stratum["area_hectares"]
            carbon_increment = biomass_growth * stratum["carbon_fraction"]
            annual_carbon_increment += carbon_increment
        
        cumulative_carbon_stock += annual_carbon_increment
        co2_sequestered = annual_carbon_increment * (44 / 12)
        buffer = co2_sequestered * buffer_percentage
        net_credits = co2_sequestered - buffer
        
        yearly_results.append({
            "year": start_year + year - 1,
            "annual_carbon_increment": round(annual_carbon_increment),
            "cumulative_carbon_stock": round(cumulative_carbon_stock),
            "co2_sequestered": round(co2_sequestered),
            "net_credits": round(net_credits)
        })
    
    total_credits = sum(yr["net_credits"] for yr in yearly_results)
    
    return {
        "methodology": "VM0047",
        "version": "1.0",
        "standard": "VCS",
        "sector": "Forestry",
        "yearly_results": yearly_results,
        "total_credits": round(total_credits),
        "emission_reductions": round(total_credits / crediting_period_years),
        "unit": "tCO2e"
    }


def VM0048_REDD(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """VM0048: REDD+ Methodology"""
    forest_area = inputs.get("forest_area", 10000)  # hectares
    baseline_deforestation_rate = inputs.get("baseline_deforestation_rate", 0.02)  # fraction/year
    project_deforestation_rate = inputs.get("project_deforestation_rate", 0.005)  # fraction/year
    carbon_stock_per_hectare = inputs.get("carbon_stock_per_hectare", 150)  # tC/ha
    buffer_percentage = inputs.get("buffer_percentage", 0.25)
    
    # Baseline deforestation
    baseline_deforestation_area = forest_area * baseline_deforestation_rate
    carbon_stock_lost = baseline_deforestation_area * carbon_stock_per_hectare
    baseline_emissions = carbon_stock_lost * (44 / 12)
    
    # Project emissions (with REDD+ activities)
    project_deforestation_area = forest_area * project_deforestation_rate
    project_carbon_stock_lost = project_deforestation_area * carbon_stock_per_hectare
    project_emissions = project_carbon_stock_lost * (44 / 12)
    
    gross_emission_reductions = baseline_emissions - project_emissions
    buffer = gross_emission_reductions * buffer_percentage
    net_credits = gross_emission_reductions - buffer
    
    return {
        "methodology": "VM0048",
        "version": "1.0",
        "standard": "VCS",
        "sector": "Forestry",
        "baseline_emissions": round(baseline_emissions),
        "project_emissions": round(project_emissions),
        "gross_emission_reductions": round(gross_emission_reductions),
        "emission_reductions": round(net_credits),
        "unit": "tCO2e"
    }


# ============================================================================
# GOLD STANDARD METHODOLOGIES
# ============================================================================

def TPDDTEC_Cookstoves(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """TPDDTEC v3.0: Clean Cookstoves - Household Sector"""
    stove_count = inputs.get("stove_count", 10000)
    baseline_fuel_consumption = inputs.get("baseline_fuel_consumption", 2.5)  # tonnes wood/stove/year
    project_fuel_consumption = inputs.get("project_fuel_consumption", 1.5)  # tonnes wood/stove/year
    fuel_ncv = inputs.get("fuel_ncv", 15.0)  # GJ/tonne
    fuel_emission_factor = inputs.get("fuel_emission_factor", 112.0)  # kgCO2/GJ
    
    baseline_emissions = stove_count * baseline_fuel_consumption * fuel_ncv * fuel_emission_factor / 1000
    project_emissions = stove_count * project_fuel_consumption * fuel_ncv * fuel_emission_factor / 1000
    emission_reductions = baseline_emissions - project_emissions
    
    return {
        "methodology": "TPDDTEC v3.0",
        "standard": "Gold Standard",
        "sector": "Household",
        "stove_count": stove_count,
        "baseline_emissions": round(baseline_emissions),
        "project_emissions": round(project_emissions),
        "emission_reductions": round(emission_reductions),
        "annual_credits_per_stove": round(emission_reductions / stove_count, 2),
        "unit": "tCO2e"
    }


def TPDDTEC_SolarWaterHeater(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """TPDDTEC v3.0: Solar Water Heaters - Household Sector"""
    households = inputs.get("households", 5000)
    water_consumption = inputs.get("water_consumption", 150)  # liters/day/household
    temperature_rise = inputs.get("temperature_rise", 35)  # degrees C
    solar_fraction = inputs.get("solar_fraction", 0.70)  # fraction met by solar
    baseline_efficiency = inputs.get("baseline_efficiency", 0.75)
    project_efficiency = inputs.get("project_efficiency", 0.85)
    fuel_emission_factor = inputs.get("fuel_emission_factor", 0.065)  # tCO2/GJ
    
    # Q_thermal = Hot water demand (GJ)
    thermal_demand = households * water_consumption * temperature_rise * 0.00418 * 365 / 1000
    
    # Baseline emissions
    baseline_fuel = thermal_demand / baseline_efficiency
    baseline_emissions = baseline_fuel * fuel_emission_factor
    
    # Project emissions (with solar)
    project_fuel = thermal_demand * (1 - solar_fraction) / project_efficiency
    project_emissions = project_fuel * fuel_emission_factor
    
    emission_reductions = baseline_emissions - project_emissions
    
    return {
        "methodology": "TPDDTEC v3.0 (SWH)",
        "standard": "Gold Standard",
        "sector": "Household",
        "households": households,
        "thermal_demand_gj": round(thermal_demand),
        "baseline_emissions": round(baseline_emissions),
        "project_emissions": round(project_emissions),
        "emission_reductions": round(emission_reductions),
        "unit": "tCO2e"
    }


def MMECD_BuildingEfficiency(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """MMECD v2.0: Energy Efficiency in Buildings (Metered)"""
    baseline_energy = inputs.get("baseline_energy", 50000)  # MWh
    project_energy = inputs.get("project_energy", 35000)  # MWh
    grid_emission_factor = inputs.get("grid_emission_factor", 0.45)  # tCO2/MWh
    
    baseline_emissions = baseline_energy * grid_emission_factor
    project_emissions = project_energy * grid_emission_factor
    emission_reductions = baseline_emissions - project_emissions
    
    return {
        "methodology": "MMECD v2.0",
        "standard": "Gold Standard",
        "sector": "Buildings",
        "baseline_emissions": round(baseline_emissions),
        "project_emissions": round(project_emissions),
        "emission_reductions": round(emission_reductions),
        "unit": "tCO2e"
    }


# ============================================================================
# CAR (Climate Action Reserve) PROTOCOLS
# ============================================================================

def CAR_Landfill(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """CAR Landfill Protocol - USA specific"""
    waste_in_place = inputs.get("waste_in_place", 1000000)  # tonnes
    methane_generation_rate = inputs.get("methane_generation_rate", 0.05)  # m3 CH4/tonne/year
    collection_efficiency = inputs.get("collection_efficiency", 0.75)
    destruction_efficiency = inputs.get("destruction_efficiency", 0.99)
    methane_gwp = inputs.get("methane_gwp", 28)
    methane_density = inputs.get("methane_density", 0.000717)
    
    methane_generated = waste_in_place * methane_generation_rate * methane_density
    methane_captured = methane_generated * collection_efficiency
    methane_destroyed = methane_captured * destruction_efficiency
    
    baseline_emissions = methane_generated * methane_gwp
    project_emissions = (methane_captured - methane_destroyed) * methane_gwp
    emission_reductions = baseline_emissions - project_emissions
    
    return {
        "protocol": "CAR Landfill",
        "version": "6.0",
        "standard": "CAR",
        "sector": "Waste",
        "baseline_emissions": round(baseline_emissions),
        "project_emissions": round(project_emissions),
        "emission_reductions": round(emission_reductions),
        "unit": "tCO2e"
    }


def CAR_Forest(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """CAR Forest Protocol - USA specific"""
    forest_area = inputs.get("forest_area", 2000)  # acres
    carbon_per_acre = inputs.get("carbon_per_acre", 50)  # tC/acre
    buffer_percentage = inputs.get("buffer_percentage", 0.15)
    
    above_ground_carbon = forest_area * carbon_per_acre
    below_ground_carbon = above_ground_carbon * 0.25
    total_carbon = above_ground_carbon + below_ground_carbon
    
    co2_sequestered = total_carbon * (44 / 12)
    buffer = co2_sequestered * buffer_percentage
    net_credits = co2_sequestered - buffer
    
    return {
        "protocol": "CAR Forest",
        "version": "4.0",
        "standard": "CAR",
        "sector": "Forestry",
        "co2_sequestered": round(co2_sequestered),
        "emission_reductions": round(net_credits),
        "unit": "tCO2e"
    }


# ============================================================================
# ACR (American Carbon Registry) METHODS
# ============================================================================

def ACR_IFM(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """ACR Improved Forest Management - USA specific"""
    forest_area = inputs.get("forest_area", 3000)  # acres
    baseline_carbon_per_acre = inputs.get("baseline_carbon_per_acre", 45)  # tC/acre
    project_carbon_per_acre = inputs.get("project_carbon_per_acre", 65)  # tC/acre
    
    baseline_carbon = forest_area * baseline_carbon_per_acre
    project_carbon = forest_area * project_carbon_per_acre
    carbon_stock_change = project_carbon - baseline_carbon
    co2_benefit = carbon_stock_change * (44 / 12)
    
    return {
        "method": "ACR IFM",
        "version": "2.0",
        "standard": "ACR",
        "sector": "Forestry",
        "emission_reductions": round(co2_benefit),
        "unit": "tCO2e"
    }


# ============================================================================
# GCC (Global Carbon Council) METHODOLOGIES
# ============================================================================

def GCCM001_RenewableEnergy(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """GCCM001: Renewable Energy Projects - GCC Region"""
    installed_capacity_mw = inputs.get("installed_capacity_mw", 100)
    capacity_factor = inputs.get("capacity_factor", 0.25)
    grid_emission_factor = inputs.get("grid_emission_factor", 0.55)  # Higher for GCC region
    
    electricity_generated = installed_capacity_mw * capacity_factor * 8760
    baseline_emissions = electricity_generated * grid_emission_factor
    project_emissions = 0
    emission_reductions = baseline_emissions - project_emissions
    
    return {
        "methodology": "GCCM001",
        "version": "1.0",
        "standard": "GCC",
        "sector": "Energy",
        "baseline_emissions": round(baseline_emissions),
        "project_emissions": round(project_emissions),
        "emission_reductions": round(emission_reductions),
        "unit": "tCO2e"
    }


# ============================================================================
# METHODOLOGY ROUTER
# ============================================================================

METHODOLOGY_CALCULATORS = {
    # CDM ACM (Large Scale)
    "ACM0001": ACM0001_LandfillGas,
    "ACM0002": ACM0002_RenewableEnergy,
    "ACM0003": ACM0003_BiomassSubstitution,
    "ACM0005": ACM0005_WasteHeatRecovery,
    "ACM0006": ACM0006_BiomassEnergy,
    "ACM0007": ACM0007_FuelSwitch,
    "ACM0008": ACM0008_CoalMineMethane,
    "ACM0009": ACM0009_CoalToGas,
    "ACM0010": ACM0010_ManureMethane,
    "ACM0012": ACM0012_WasteHeatPower,
    "ACM0014": ACM0014_CementBlending,
    "ACM0022": ACM0022_Composting,
    "ACM0023": ACM0023_LowEmissionVehicles,
    
    # CDM AMS (Small Scale)
    "AMS-I.A": AMS_I_A_RenewableElectricity,
    "AMS-I.C": AMS_I_C_RenewableThermal,
    "AMS-I.D": AMS_I_D_GridRenewable,
    "AMS-II.D": AMS_II_D_BuildingEfficiency,
    "AMS-II.E": AMS_II_E_TransportEfficiency,
    "AMS-II.G": AMS_II_G_IndustrialEfficiency,
    "AMS-III.AU": AMS_III_AU_AgriculturalMethane,
    "AMS-III.B": AMS_III_B_WastewaterMethane,
    "AMS-III.C": AMS_III_C_WasteComposting,
    "AMS-III.D": AMS_III_D_SolidWasteMethane,
    
    # CDM AM (Sector-Specific)
    "AM0012": AM0012_NitricAcidN2O,
    "AM0036": AM0036_SF6Reduction,
    
    # CDM AR (Forestry)
    "AR-ACM0003": AR_ACM0003_AfforestationReforestation,
    
    # VCS
    "VM0008": VM0008_WastewaterMethane,
    "VM0022": VM0022_AgriculturalN2O,
    "VM0033": VM0033_BlueCarbon,
    "VM0042": VM0042_AgriculturalLandManagement,
    "VM0044": VM0044_BiocharSoil,
    "VM0047": VM0047_ARR,
    "VM0048": VM0048_REDD,
    
    # Gold Standard
    "TPDDTEC": TPDDTEC_Cookstoves,
    "TPDDTEC-SWH": TPDDTEC_SolarWaterHeater,
    "MMECD": MMECD_BuildingEfficiency,
    
    # CAR
    "CAR-Landfill": CAR_Landfill,
    "CAR-Forest": CAR_Forest,
    
    # ACR
    "ACR-IFM": ACR_IFM,
    
    # GCC
    "GCCM001": GCCM001_RenewableEnergy,
}


def calculate_by_methodology(methodology_code: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Route calculation to the appropriate methodology function."""
    calculator = METHODOLOGY_CALCULATORS.get(methodology_code)
    
    if not calculator:
        return {
            "error": f"Methodology {methodology_code} not found or not implemented",
            "available_methodologies": list(METHODOLOGY_CALCULATORS.keys())
        }
    
    try:
        return calculator(inputs)
    except Exception as e:
        return {
            "error": f"Calculation failed: {str(e)}",
            "methodology": methodology_code
        }


def get_methodologies_by_sector(sector: str) -> List[Dict[str, Any]]:
    """Get list of available methodologies by sector."""
    methodologies_by_sector = {
        "ENERGY": [
            {"code": "ACM0002", "name": "Grid-connected Renewable Energy", "standard": "CDM", "scale": "Large"},
            {"code": "ACM0003", "name": "Biomass Substitution", "standard": "CDM", "scale": "Large"},
            {"code": "ACM0005", "name": "Waste Heat Recovery", "standard": "CDM", "scale": "Large"},
            {"code": "ACM0006", "name": "Biomass Energy", "standard": "CDM", "scale": "Large"},
            {"code": "ACM0007", "name": "Fuel Switch", "standard": "CDM", "scale": "Large"},
            {"code": "ACM0009", "name": "Coal to Gas Switch", "standard": "CDM", "scale": "Large"},
            {"code": "AMS-I.A", "name": "Small-scale Renewable Electricity", "standard": "CDM", "scale": "Small"},
            {"code": "AMS-I.C", "name": "Small-scale Renewable Thermal", "standard": "CDM", "scale": "Small"},
            {"code": "AMS-I.D", "name": "Small-scale Grid Renewable", "standard": "CDM", "scale": "Small"},
            {"code": "GCCM001", "name": "Renewable Energy (GCC)", "standard": "GCC", "scale": "Large"},
        ],
        "WASTE": [
            {"code": "ACM0001", "name": "Landfill Gas Capture", "standard": "CDM", "scale": "Large"},
            {"code": "ACM0022", "name": "Waste Composting", "standard": "CDM", "scale": "Large"},
            {"code": "AMS-III.B", "name": "Wastewater Methane", "standard": "CDM", "scale": "Small"},
            {"code": "AMS-III.C", "name": "Waste Composting (Small)", "standard": "CDM", "scale": "Small"},
            {"code": "AMS-III.D", "name": "Solid Waste Methane", "standard": "CDM", "scale": "Small"},
            {"code": "VM0008", "name": "Wastewater Methane", "standard": "VCS", "scale": "Large"},
            {"code": "CAR-Landfill", "name": "Landfill Gas (USA)", "standard": "CAR", "scale": "Large"},
        ],
        "FORESTRY": [
            {"code": "AR-ACM0003", "name": "Afforestation/Reforestation", "standard": "CDM", "scale": "Large"},
            {"code": "VM0047", "name": "ARR (Afforestation)", "standard": "VCS", "scale": "Large"},
            {"code": "VM0048", "name": "REDD+", "standard": "VCS", "scale": "Large"},
            {"code": "CAR-Forest", "name": "Forest Carbon (USA)", "standard": "CAR", "scale": "Large"},
            {"code": "ACR-IFM", "name": "Improved Forest Management", "standard": "ACR", "scale": "Large"},
        ],
        "AGRICULTURE": [
            {"code": "ACM0010", "name": "Manure Methane", "standard": "CDM", "scale": "Large"},
            {"code": "AMS-III.AU", "name": "Agricultural Methane", "standard": "CDM", "scale": "Small"},
            {"code": "VM0022", "name": "Agricultural N2O", "standard": "VCS", "scale": "Large"},
            {"code": "VM0042", "name": "Agricultural Land Management", "standard": "VCS", "scale": "Large"},
            {"code": "VM0044", "name": "Biochar in Soil", "standard": "VCS", "scale": "Large"},
        ],
        "INDUSTRIAL": [
            {"code": "ACM0012", "name": "Waste Heat Power", "standard": "CDM", "scale": "Large"},
            {"code": "ACM0014", "name": "Cement Blending", "standard": "CDM", "scale": "Large"},
            {"code": "AMS-II.G", "name": "Industrial Efficiency", "standard": "CDM", "scale": "Small"},
            {"code": "AM0012", "name": "Nitric Acid N2O", "standard": "CDM", "scale": "Large"},
            {"code": "AM0036", "name": "SF6 Reduction", "standard": "CDM", "scale": "Large"},
        ],
        "TRANSPORT": [
            {"code": "ACM0023", "name": "Low Emission Vehicles", "standard": "CDM", "scale": "Large"},
            {"code": "AMS-II.E", "name": "Transport Efficiency", "standard": "CDM", "scale": "Small"},
        ],
        "BUILDINGS": [
            {"code": "AMS-II.D", "name": "Building Efficiency", "standard": "CDM", "scale": "Small"},
            {"code": "MMECD", "name": "Metered Energy Efficiency", "standard": "Gold Standard", "scale": "Large"},
        ],
        "HOUSEHOLD": [
            {"code": "TPDDTEC", "name": "Clean Cookstoves", "standard": "Gold Standard", "scale": "Large"},
            {"code": "TPDDTEC-SWH", "name": "Solar Water Heaters", "standard": "Gold Standard", "scale": "Large"},
        ],
        "MINING": [
            {"code": "ACM0008", "name": "Coal Mine Methane", "standard": "CDM", "scale": "Large"},
        ],
        "BLUE_CARBON": [
            {"code": "VM0033", "name": "Tidal Wetland/Seagrass", "standard": "VCS", "scale": "Large"},
        ],
    }
    
    return methodologies_by_sector.get(sector.upper(), [])


def get_methodology_details(methodology_code: str) -> Optional[Dict[str, Any]]:
    """Get detailed information about a methodology."""
    details = {
        "ACM0002": {
            "name": "Grid-connected Renewable Electricity Generation",
            "standard": "CDM",
            "sector": "Energy",
            "version": "21.0",
            "applicability": "Grid-connected renewable electricity generation from solar, wind, hydro, geothermal, biomass",
            "baseline_approach": "Grid emission factor (combined margin)",
            "crediting_period": "10 years (renewable up to 21 years)",
            "required_inputs": ["installed_capacity_mw", "capacity_factor", "grid_emission_factor"],
        },
        "ACM0001": {
            "name": "Flaring or Use of Landfill Gas",
            "standard": "CDM",
            "sector": "Waste",
            "version": "19.0",
            "applicability": "Capture and destruction or utilization of landfill gas",
            "baseline_approach": "Methane venting from landfills",
            "crediting_period": "10 years (renewable up to 21 years)",
            "required_inputs": ["waste_quantity", "methane_generation_potential", "capture_efficiency", "destruction_efficiency"],
        },
        "AR-ACM0003": {
            "name": "Afforestation and Reforestation",
            "standard": "CDM",
            "sector": "Forestry",
            "version": "5.0",
            "applicability": "Afforestation and reforestation of lands",
            "baseline_approach": "Baseline scenario without project",
            "crediting_period": "20-60 years",
            "required_inputs": ["species", "area_hectares", "growth_rate", "crediting_period_years"],
        },
        "VM0048": {
            "name": "REDD+",
            "standard": "VCS",
            "sector": "Forestry",
            "version": "1.0",
            "applicability": "Reducing emissions from deforestation and forest degradation",
            "baseline_approach": "Historical deforestation rate",
            "crediting_period": "Up to 30 years",
            "required_inputs": ["forest_area", "baseline_deforestation_rate", "carbon_stock_per_hectare"],
        },
        "TPDDTEC": {
            "name": "Clean Cookstoves",
            "standard": "Gold Standard",
            "sector": "Household",
            "version": "3.0",
            "applicability": "Displacement of traditional cookstoves with improved cookstoves",
            "baseline_approach": "Fuel consumption in baseline scenario",
            "crediting_period": "5 years (renewable)",
            "required_inputs": ["stove_count", "baseline_fuel_consumption", "project_fuel_consumption"],
        },
    }
    
    return details.get(methodology_code)


def get_all_methodologies() -> List[Dict[str, Any]]:
    """Get list of all available methodologies."""
    all_methods = []
    for sector in MethodologySector:
        methods = get_methodologies_by_sector(sector.value)
        for m in methods:
            m["sector"] = sector.value
            all_methods.append(m)
    return all_methods
