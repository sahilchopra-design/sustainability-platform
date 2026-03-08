"""
Activity Guide Catalog
Maps real-world economic activities to carbon credit methodologies.
Provides plain-language input guides and data sourcing information.

Contains 105 activities across 15 sectors:
  Energy (16), Waste (7), Forestry (8), Agriculture (6), Industrial (7),
  Transport (5), Buildings (6), Financial (5), Upstream (11), Downstream (10),
  Cross-Sector (4), Mining (4), Textiles (3), Food & Beverage (4),
  Healthcare (3), Real Estate (3), Technology (3).
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# ACTIVITY CATALOG
# ---------------------------------------------------------------------------

ACTIVITY_CATALOG: Dict[str, Dict[str, Any]] = {

    # ======================================================================
    # ENERGY  (#1 - #16)
    # ======================================================================

    "wind_farm_onshore": {
        "id": "wind_farm_onshore",
        "name": "Grid-Connected Onshore Wind Farm",
        "description": "Development and operation of onshore wind turbines displacing fossil-fuel electricity from the grid.",
        "sector": "Energy",
        "user_types": ["Energy Company", "Corporate", "Project Developer"],
        "value_chain_position": "core",
        "applicable_methodologies": ["ACM0002", "AMS-I.D"],
        "recommended_methodology": "ACM0002",
        "scale": "Large",
        "typical_credit_range": {"min": 20000, "max": 200000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "installed_capacity_mw",
                "label": "Installed Capacity",
                "description": "Total nameplate capacity of all wind turbines in the project.",
                "unit": "MW",
                "typical_range": {"min": 10, "max": 500},
                "example_value": 50,
                "data_sources": ["Equipment specification sheet", "PPA contract", "Grid connection permit"],
                "required": True,
                "tooltip": "Found on the turbine nameplate or in the PPA."
            },
            {
                "parameter": "capacity_factor",
                "label": "Net Capacity Factor",
                "description": "Ratio of actual annual output to theoretical maximum output.",
                "unit": "%",
                "typical_range": {"min": 20, "max": 45},
                "example_value": 30,
                "data_sources": ["Wind resource assessment report", "Historical SCADA data", "Independent engineer report"],
                "required": True,
                "tooltip": "Measured over at least 12 months; site-specific wind data preferred."
            },
            {
                "parameter": "grid_emission_factor",
                "label": "Grid Emission Factor",
                "description": "CO2 intensity of the electricity grid the project feeds into.",
                "unit": "tCO2/MWh",
                "typical_range": {"min": 0.4, "max": 1.2},
                "example_value": 0.85,
                "data_sources": ["National grid authority", "IFI Harmonized Grid EF database", "IGES CDM list"],
                "required": True,
                "tooltip": "Use combined margin (CM) or build margin (BM) per ACM0002."
            },
            {
                "parameter": "annual_generation_mwh",
                "label": "Expected Annual Generation",
                "description": "Net electricity delivered to the grid per year after losses.",
                "unit": "MWh",
                "typical_range": {"min": 20000, "max": 1500000},
                "example_value": 131400,
                "data_sources": ["Energy yield study", "Grid meter readings", "SCADA export"],
                "required": True,
                "tooltip": "Net of auxiliary consumption and transformer losses."
            }
        ],
        "real_world_examples": [
            {"project": "Jaisalmer Wind Park, Rajasthan", "credits": 86000, "year": 2023},
            {"project": "Lake Turkana Wind Power, Kenya", "credits": 150000, "year": 2022}
        ],
        "regulatory_notes": "Eligible under CDM, VCS, Gold Standard. Must demonstrate additionality via barrier or investment analysis.",
        "cdm_tools_needed": ["TOOL01", "TOOL07"],
        "estimated_cost_range_usd": {"min": 50000000, "max": 150000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    "wind_farm_offshore": {
        "id": "wind_farm_offshore",
        "name": "Grid-Connected Offshore Wind Farm",
        "description": "Development and operation of offshore wind turbines mounted on fixed or floating platforms, displacing grid electricity.",
        "sector": "Energy",
        "user_types": ["Energy Company", "Sovereign Fund", "Project Developer"],
        "value_chain_position": "core",
        "applicable_methodologies": ["ACM0002", "AMS-I.D"],
        "recommended_methodology": "ACM0002",
        "scale": "Large",
        "typical_credit_range": {"min": 100000, "max": 800000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "installed_capacity_mw",
                "label": "Installed Capacity",
                "description": "Total nameplate capacity of all offshore turbines.",
                "unit": "MW",
                "typical_range": {"min": 100, "max": 1500},
                "example_value": 400,
                "data_sources": ["Turbine OEM datasheet", "Offshore PPA", "Marine license"],
                "required": True,
                "tooltip": "Includes all turbines in the array."
            },
            {
                "parameter": "capacity_factor",
                "label": "Net Capacity Factor",
                "description": "Ratio of actual annual output to theoretical maximum.",
                "unit": "%",
                "typical_range": {"min": 35, "max": 55},
                "example_value": 45,
                "data_sources": ["Offshore wind resource assessment", "Metocean data report", "Independent engineer report"],
                "required": True,
                "tooltip": "Offshore sites typically achieve higher capacity factors than onshore."
            },
            {
                "parameter": "grid_emission_factor",
                "label": "Grid Emission Factor",
                "description": "CO2 intensity of the receiving grid.",
                "unit": "tCO2/MWh",
                "typical_range": {"min": 0.3, "max": 1.0},
                "example_value": 0.75,
                "data_sources": ["National grid authority", "IFI Harmonized Grid EF database"],
                "required": True,
                "tooltip": "Use combined margin per ACM0002."
            },
            {
                "parameter": "annual_generation_mwh",
                "label": "Expected Annual Generation",
                "description": "Net electricity delivered to shore after cable and transformer losses.",
                "unit": "MWh",
                "typical_range": {"min": 300000, "max": 5000000},
                "example_value": 1576800,
                "data_sources": ["Energy yield study (P50)", "Export cable meter readings"],
                "required": True,
                "tooltip": "Net of array losses, cable losses, and auxiliary consumption."
            },
            {
                "parameter": "distance_to_shore_km",
                "label": "Distance to Shore",
                "description": "Length of subsea export cable from offshore substation to onshore grid.",
                "unit": "km",
                "typical_range": {"min": 5, "max": 150},
                "example_value": 30,
                "data_sources": ["Marine survey", "Cable route survey", "Planning consent docs"],
                "required": False,
                "tooltip": "Affects transmission losses and project cost estimates."
            }
        ],
        "real_world_examples": [
            {"project": "Hornsea Two, North Sea UK", "credits": 520000, "year": 2023}
        ],
        "regulatory_notes": "Eligible under VCS, Gold Standard. CDM eligibility depends on host country. High capex improves additionality case.",
        "cdm_tools_needed": ["TOOL01", "TOOL07"],
        "estimated_cost_range_usd": {"min": 1000000000, "max": 5000000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    "solar_pv_utility": {
        "id": "solar_pv_utility",
        "name": "Utility-Scale Solar PV Plant",
        "description": "Ground-mounted photovoltaic power station feeding electricity into the national or regional grid.",
        "sector": "Energy",
        "user_types": ["Energy Company", "Corporate", "Project Developer"],
        "value_chain_position": "core",
        "applicable_methodologies": ["ACM0002", "AMS-I.D"],
        "recommended_methodology": "ACM0002",
        "scale": "Large",
        "typical_credit_range": {"min": 15000, "max": 250000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "installed_capacity_mwp",
                "label": "Installed Peak Capacity",
                "description": "Total DC peak capacity of all solar modules.",
                "unit": "MWp",
                "typical_range": {"min": 5, "max": 1000},
                "example_value": 100,
                "data_sources": ["Module datasheets", "EPC contract", "Grid connection agreement"],
                "required": True,
                "tooltip": "Sum of all module nameplate ratings under STC."
            },
            {
                "parameter": "specific_yield",
                "label": "Specific Yield",
                "description": "Annual energy output per unit of installed capacity.",
                "unit": "kWh/kWp/year",
                "typical_range": {"min": 1200, "max": 2200},
                "example_value": 1650,
                "data_sources": ["PVsyst simulation", "Solar resource assessment (GHI data)", "Historical meter data"],
                "required": True,
                "tooltip": "Depends on irradiance, tilt angle, temperature, and soiling."
            },
            {
                "parameter": "grid_emission_factor",
                "label": "Grid Emission Factor",
                "description": "CO2 intensity of the displaced grid electricity.",
                "unit": "tCO2/MWh",
                "typical_range": {"min": 0.4, "max": 1.2},
                "example_value": 0.9,
                "data_sources": ["National grid authority", "IFI Harmonized Grid EF database", "IGES CDM list"],
                "required": True,
                "tooltip": "Use combined margin per ACM0002."
            },
            {
                "parameter": "performance_ratio",
                "label": "Performance Ratio",
                "description": "Ratio of actual system yield to reference yield, accounting for all losses.",
                "unit": "%",
                "typical_range": {"min": 75, "max": 90},
                "example_value": 82,
                "data_sources": ["PVsyst report", "O&M performance reports", "Inverter monitoring system"],
                "required": True,
                "tooltip": "Includes temperature, soiling, wiring, inverter, and clipping losses."
            }
        ],
        "real_world_examples": [
            {"project": "Bhadla Solar Park, Rajasthan", "credits": 180000, "year": 2023},
            {"project": "Benban Solar Complex, Egypt", "credits": 210000, "year": 2022}
        ],
        "regulatory_notes": "Eligible under CDM, VCS, Gold Standard. Common activity with well-established baseline.",
        "cdm_tools_needed": ["TOOL01", "TOOL07"],
        "estimated_cost_range_usd": {"min": 30000000, "max": 500000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    "csp_plant": {
        "id": "csp_plant",
        "name": "Concentrated Solar Power (CSP) Plant",
        "description": "Solar thermal power station using mirrors or lenses to concentrate sunlight onto a receiver to generate electricity, often with thermal storage.",
        "sector": "Energy",
        "user_types": ["Energy Company", "Project Developer", "Sovereign Fund"],
        "value_chain_position": "core",
        "applicable_methodologies": ["ACM0002", "AMS-I.D"],
        "recommended_methodology": "ACM0002",
        "scale": "Large",
        "typical_credit_range": {"min": 30000, "max": 300000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "installed_capacity_mw",
                "label": "Net Electrical Capacity",
                "description": "Net power output capacity of the CSP plant at design point.",
                "unit": "MW",
                "typical_range": {"min": 50, "max": 500},
                "example_value": 150,
                "data_sources": ["Turbine spec sheet", "EPC contract", "Grid connection permit"],
                "required": True,
                "tooltip": "Net of parasitic loads from pumps, tracking systems, and cooling."
            },
            {
                "parameter": "storage_hours",
                "label": "Thermal Storage Duration",
                "description": "Hours of full-load electricity generation from stored thermal energy.",
                "unit": "hours",
                "typical_range": {"min": 0, "max": 16},
                "example_value": 8,
                "data_sources": ["Storage system design report", "EPC contract", "Thermal model"],
                "required": True,
                "tooltip": "Molten salt storage is most common; increases capacity factor."
            },
            {
                "parameter": "annual_generation_mwh",
                "label": "Annual Net Generation",
                "description": "Total electricity delivered to grid per year.",
                "unit": "MWh",
                "typical_range": {"min": 100000, "max": 1200000},
                "example_value": 500000,
                "data_sources": ["Solar resource assessment (DNI data)", "Plant performance model", "Grid meter readings"],
                "required": True,
                "tooltip": "Net of all parasitic consumption and storage round-trip losses."
            },
            {
                "parameter": "grid_emission_factor",
                "label": "Grid Emission Factor",
                "description": "CO2 intensity of displaced grid electricity.",
                "unit": "tCO2/MWh",
                "typical_range": {"min": 0.4, "max": 1.2},
                "example_value": 0.85,
                "data_sources": ["National grid authority", "IFI Harmonized Grid EF database"],
                "required": True,
                "tooltip": "Use combined margin per ACM0002."
            }
        ],
        "real_world_examples": [
            {"project": "Noor Ouarzazate III, Morocco", "credits": 145000, "year": 2022}
        ],
        "regulatory_notes": "Eligible under CDM, VCS. Storage component improves dispatchability and grid value.",
        "cdm_tools_needed": ["TOOL01", "TOOL07"],
        "estimated_cost_range_usd": {"min": 500000000, "max": 2000000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    "small_hydro": {
        "id": "small_hydro",
        "name": "Small Hydropower Plant",
        "description": "Run-of-river or small reservoir hydropower plant (typically <=15 MW) displacing grid electricity.",
        "sector": "Energy",
        "user_types": ["Energy Company", "Municipal Utility", "Project Developer"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-I.D", "ACM0002"],
        "recommended_methodology": "AMS-I.D",
        "scale": "Small",
        "typical_credit_range": {"min": 5000, "max": 50000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "installed_capacity_mw",
                "label": "Installed Capacity",
                "description": "Nameplate capacity of the hydro turbine(s).",
                "unit": "MW",
                "typical_range": {"min": 0.5, "max": 15},
                "example_value": 5,
                "data_sources": ["Turbine specification", "Feasibility study", "Power purchase agreement"],
                "required": True,
                "tooltip": "AMS-I.D applies for projects up to 15 MW."
            },
            {
                "parameter": "annual_generation_mwh",
                "label": "Annual Generation",
                "description": "Net electricity delivered to the grid per year.",
                "unit": "MWh",
                "typical_range": {"min": 2000, "max": 60000},
                "example_value": 22000,
                "data_sources": ["Hydrology study", "Historical flow data", "Grid meter readings"],
                "required": True,
                "tooltip": "Based on long-term hydrological records, typically P50 estimate."
            },
            {
                "parameter": "grid_emission_factor",
                "label": "Grid Emission Factor",
                "description": "CO2 intensity of the displaced grid.",
                "unit": "tCO2/MWh",
                "typical_range": {"min": 0.3, "max": 1.2},
                "example_value": 0.8,
                "data_sources": ["National grid authority", "IGES CDM list", "IFI Harmonized Grid EF database"],
                "required": True,
                "tooltip": "Use operating margin or combined margin."
            },
            {
                "parameter": "design_head_m",
                "label": "Design Head",
                "description": "Vertical drop of water from intake to turbine.",
                "unit": "m",
                "typical_range": {"min": 5, "max": 300},
                "example_value": 45,
                "data_sources": ["Topographic survey", "Feasibility study"],
                "required": True,
                "tooltip": "Determines turbine type selection and energy potential."
            }
        ],
        "real_world_examples": [
            {"project": "Bumbuna II Small Hydro, Sierra Leone", "credits": 18000, "year": 2023},
            {"project": "Salto Pilao, Brazil", "credits": 32000, "year": 2022}
        ],
        "regulatory_notes": "Eligible under CDM (AMS-I.D), VCS, Gold Standard. Must demonstrate no significant environmental or social harm.",
        "cdm_tools_needed": ["TOOL01", "TOOL07", "TOOL03"],
        "estimated_cost_range_usd": {"min": 3000000, "max": 30000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    "geothermal": {
        "id": "geothermal",
        "name": "Geothermal Power Plant",
        "description": "Extraction of subsurface heat to drive turbines for grid electricity, displacing fossil fuels.",
        "sector": "Energy",
        "user_types": ["Energy Company", "Project Developer", "Sovereign Fund"],
        "value_chain_position": "core",
        "applicable_methodologies": ["ACM0002", "AMS-I.D"],
        "recommended_methodology": "ACM0002",
        "scale": "Large",
        "typical_credit_range": {"min": 20000, "max": 300000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "installed_capacity_mw",
                "label": "Installed Capacity",
                "description": "Net electrical output of the geothermal plant.",
                "unit": "MW",
                "typical_range": {"min": 5, "max": 200},
                "example_value": 50,
                "data_sources": ["Turbine datasheet", "Resource assessment report", "PPA"],
                "required": True,
                "tooltip": "Net of parasitic loads (pumps, reinjection, cooling)."
            },
            {
                "parameter": "capacity_factor",
                "label": "Capacity Factor",
                "description": "Fraction of year the plant operates at rated capacity.",
                "unit": "%",
                "typical_range": {"min": 80, "max": 95},
                "example_value": 90,
                "data_sources": ["Reservoir engineering report", "Historical plant data", "O&M records"],
                "required": True,
                "tooltip": "Geothermal plants typically run as baseload with high availability."
            },
            {
                "parameter": "grid_emission_factor",
                "label": "Grid Emission Factor",
                "description": "CO2 intensity of displaced grid electricity.",
                "unit": "tCO2/MWh",
                "typical_range": {"min": 0.3, "max": 1.0},
                "example_value": 0.7,
                "data_sources": ["National grid authority", "IFI Harmonized Grid EF database"],
                "required": True,
                "tooltip": "Use combined margin per ACM0002."
            },
            {
                "parameter": "fugitive_co2_factor",
                "label": "Fugitive CO2 Emission Factor",
                "description": "Non-condensable gas emissions from the geothermal fluid.",
                "unit": "tCO2/MWh",
                "typical_range": {"min": 0.01, "max": 0.15},
                "example_value": 0.05,
                "data_sources": ["Gas analysis of geothermal fluid", "Reservoir chemistry report"],
                "required": True,
                "tooltip": "Must be deducted from gross emission reductions."
            }
        ],
        "real_world_examples": [
            {"project": "Olkaria III, Kenya", "credits": 220000, "year": 2023}
        ],
        "regulatory_notes": "Eligible under CDM, VCS. Must account for fugitive non-condensable gas (CO2, H2S) emissions.",
        "cdm_tools_needed": ["TOOL01", "TOOL07"],
        "estimated_cost_range_usd": {"min": 100000000, "max": 600000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    "biomass_power": {
        "id": "biomass_power",
        "name": "Biomass Power Plant",
        "description": "Combustion or gasification of sustainable biomass residues to generate grid electricity.",
        "sector": "Energy",
        "user_types": ["Energy Company", "Agribusiness", "Project Developer"],
        "value_chain_position": "core",
        "applicable_methodologies": ["ACM0006", "AMS-I.D", "AMS-I.C"],
        "recommended_methodology": "ACM0006",
        "scale": "Large",
        "typical_credit_range": {"min": 10000, "max": 150000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "installed_capacity_mw",
                "label": "Installed Capacity",
                "description": "Net electrical capacity of the biomass plant.",
                "unit": "MW",
                "typical_range": {"min": 1, "max": 100},
                "example_value": 20,
                "data_sources": ["Turbine spec sheet", "EPC contract", "PPA"],
                "required": True,
                "tooltip": "Net of parasitic loads for fuel handling and flue gas treatment."
            },
            {
                "parameter": "biomass_fuel_tonnes_yr",
                "label": "Annual Biomass Fuel Consumption",
                "description": "Dry tonnes of biomass feedstock consumed per year.",
                "unit": "tonnes/year",
                "typical_range": {"min": 10000, "max": 500000},
                "example_value": 80000,
                "data_sources": ["Fuel supply agreement", "Weigh bridge records", "Moisture content lab tests"],
                "required": True,
                "tooltip": "Must be renewable biomass; fossil fraction must be zero."
            },
            {
                "parameter": "grid_emission_factor",
                "label": "Grid Emission Factor",
                "description": "CO2 intensity of displaced grid electricity.",
                "unit": "tCO2/MWh",
                "typical_range": {"min": 0.4, "max": 1.2},
                "example_value": 0.9,
                "data_sources": ["National grid authority", "IFI Harmonized Grid EF database"],
                "required": True,
                "tooltip": "Use combined margin per ACM0006."
            },
            {
                "parameter": "biomass_type",
                "label": "Biomass Feedstock Type",
                "description": "Primary type of biomass used as fuel.",
                "unit": "text",
                "typical_range": {"min": None, "max": None},
                "example_value": "Rice husk",
                "data_sources": ["Fuel supply agreement", "Biomass sustainability certificate"],
                "required": True,
                "tooltip": "Must demonstrate sustainable sourcing and no land-use change."
            }
        ],
        "real_world_examples": [
            {"project": "Orient Green Power, Tamil Nadu", "credits": 55000, "year": 2023},
            {"project": "Mumias Sugar Bagasse, Kenya", "credits": 42000, "year": 2022}
        ],
        "regulatory_notes": "Eligible under CDM (ACM0006), VCS, Gold Standard. Must prove biomass renewability and sustainable sourcing.",
        "cdm_tools_needed": ["TOOL01", "TOOL07", "TOOL16"],
        "estimated_cost_range_usd": {"min": 10000000, "max": 150000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    "biogas_agri": {
        "id": "biogas_agri",
        "name": "Agricultural Biogas to Electricity",
        "description": "Anaerobic digestion of agricultural waste to produce biogas for on-site electricity generation or grid feed-in.",
        "sector": "Energy",
        "user_types": ["Agribusiness", "Farm Cooperative", "Project Developer"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-I.D", "AMS-III.D", "ACM0006"],
        "recommended_methodology": "AMS-I.D",
        "scale": "Small",
        "typical_credit_range": {"min": 2000, "max": 30000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "biogas_volume_m3_yr",
                "label": "Annual Biogas Production",
                "description": "Total biogas generated from the digester per year.",
                "unit": "m3/year",
                "typical_range": {"min": 100000, "max": 5000000},
                "example_value": 1200000,
                "data_sources": ["Gas flow meter readings", "Digester design report", "Lab biogas yield tests"],
                "required": True,
                "tooltip": "Measured at standard temperature and pressure (STP)."
            },
            {
                "parameter": "methane_fraction",
                "label": "Methane Content",
                "description": "Percentage of methane in biogas by volume.",
                "unit": "%",
                "typical_range": {"min": 50, "max": 70},
                "example_value": 60,
                "data_sources": ["Gas chromatography lab results", "Continuous gas analyser readings"],
                "required": True,
                "tooltip": "Higher methane content increases energy value per m3."
            },
            {
                "parameter": "electrical_efficiency",
                "label": "Genset Electrical Efficiency",
                "description": "Net electrical efficiency of the biogas engine/genset.",
                "unit": "%",
                "typical_range": {"min": 30, "max": 42},
                "example_value": 36,
                "data_sources": ["Engine specification sheet", "Commissioning test report"],
                "required": True,
                "tooltip": "Efficiency at rated load; derate for part-load operation."
            },
            {
                "parameter": "grid_emission_factor",
                "label": "Grid Emission Factor",
                "description": "CO2 intensity of displaced grid electricity.",
                "unit": "tCO2/MWh",
                "typical_range": {"min": 0.4, "max": 1.2},
                "example_value": 0.85,
                "data_sources": ["National grid authority", "IFI Harmonized Grid EF database"],
                "required": True,
                "tooltip": "Applicable if electricity is fed to the grid."
            }
        ],
        "real_world_examples": [
            {"project": "Chiang Mai Pig Farm Biogas, Thailand", "credits": 12000, "year": 2023}
        ],
        "regulatory_notes": "Eligible under CDM, VCS, Gold Standard. Commonly bundled with methane avoidance credits.",
        "cdm_tools_needed": ["TOOL01", "TOOL07", "TOOL04"],
        "estimated_cost_range_usd": {"min": 500000, "max": 8000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    "solar_rooftop_ci": {
        "id": "solar_rooftop_ci",
        "name": "Rooftop Solar PV - Commercial / Industrial",
        "description": "Installation of solar PV panels on commercial or industrial building rooftops, offsetting grid electricity consumption.",
        "sector": "Energy",
        "user_types": ["Corporate", "Building Owner", "ESCO"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-I.D", "AMS-I.F"],
        "recommended_methodology": "AMS-I.D",
        "scale": "Small",
        "typical_credit_range": {"min": 500, "max": 10000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "installed_capacity_kwp",
                "label": "Installed Peak Capacity",
                "description": "Total DC peak capacity of all rooftop solar modules.",
                "unit": "kWp",
                "typical_range": {"min": 50, "max": 5000},
                "example_value": 500,
                "data_sources": ["Module datasheets", "Installation contract", "Net metering agreement"],
                "required": True,
                "tooltip": "Sum of all module nameplate ratings."
            },
            {
                "parameter": "annual_generation_kwh",
                "label": "Annual Generation",
                "description": "Total electricity generated by the rooftop system per year.",
                "unit": "kWh/year",
                "typical_range": {"min": 60000, "max": 7500000},
                "example_value": 750000,
                "data_sources": ["Inverter monitoring portal", "Utility meter data", "PVsyst simulation"],
                "required": True,
                "tooltip": "Net of inverter losses and module degradation."
            },
            {
                "parameter": "grid_emission_factor",
                "label": "Grid Emission Factor",
                "description": "CO2 intensity of displaced electricity.",
                "unit": "tCO2/MWh",
                "typical_range": {"min": 0.4, "max": 1.2},
                "example_value": 0.85,
                "data_sources": ["National grid authority", "IFI Harmonized Grid EF database"],
                "required": True,
                "tooltip": "Use the applicable margin emission factor."
            }
        ],
        "real_world_examples": [
            {"project": "Walmart India Rooftop Portfolio", "credits": 8500, "year": 2023}
        ],
        "regulatory_notes": "Eligible under CDM (AMS-I.D), VCS, Gold Standard. Often bundled as a programme of activities (PoA).",
        "cdm_tools_needed": ["TOOL01", "TOOL07"],
        "estimated_cost_range_usd": {"min": 30000, "max": 3000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    "solar_rooftop_resi": {
        "id": "solar_rooftop_resi",
        "name": "Rooftop Solar PV - Residential",
        "description": "Installation of small solar PV systems on residential buildings, displacing household grid electricity.",
        "sector": "Energy",
        "user_types": ["Household", "Housing Association", "ESCO"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-I.D", "AMS-I.F", "AMS-I.L"],
        "recommended_methodology": "AMS-I.L",
        "scale": "Micro",
        "typical_credit_range": {"min": 100, "max": 5000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "system_size_kwp",
                "label": "System Size",
                "description": "Peak DC capacity of the residential solar system.",
                "unit": "kWp",
                "typical_range": {"min": 1, "max": 20},
                "example_value": 5,
                "data_sources": ["Module datasheets", "Installer quote", "Net metering contract"],
                "required": True,
                "tooltip": "Typical residential systems are 3-10 kWp."
            },
            {
                "parameter": "number_of_systems",
                "label": "Number of Systems",
                "description": "Total number of residential systems in the bundled programme.",
                "unit": "count",
                "typical_range": {"min": 100, "max": 100000},
                "example_value": 5000,
                "data_sources": ["Programme registry", "Sales / installation records", "Subsidy disbursement records"],
                "required": True,
                "tooltip": "Credits are typically aggregated across many homes."
            },
            {
                "parameter": "grid_emission_factor",
                "label": "Grid Emission Factor",
                "description": "CO2 intensity of displaced grid electricity.",
                "unit": "tCO2/MWh",
                "typical_range": {"min": 0.4, "max": 1.2},
                "example_value": 0.9,
                "data_sources": ["National grid authority", "IFI Harmonized Grid EF database"],
                "required": True,
                "tooltip": "Use operating margin or combined margin."
            }
        ],
        "real_world_examples": [
            {"project": "Simpa Networks Solar Home India PoA", "credits": 4200, "year": 2023}
        ],
        "regulatory_notes": "Best deployed as a Programme of Activities (PoA). Each home is a CPA.",
        "cdm_tools_needed": ["TOOL01", "TOOL07"],
        "estimated_cost_range_usd": {"min": 500000, "max": 50000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    "solar_home_systems": {
        "id": "solar_home_systems",
        "name": "Solar Home Systems (Off-Grid)",
        "description": "Distribution of small off-grid solar kits to households without grid access, displacing kerosene lamps and diesel generators.",
        "sector": "Energy",
        "user_types": ["Social Enterprise", "NGO", "Distributor"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-I.L", "AMS-I.A", "Gold Standard Methodology"],
        "recommended_methodology": "AMS-I.L",
        "scale": "Micro",
        "typical_credit_range": {"min": 1000, "max": 20000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "number_of_systems",
                "label": "Number of SHS Deployed",
                "description": "Total solar home systems distributed and operational.",
                "unit": "count",
                "typical_range": {"min": 1000, "max": 500000},
                "example_value": 50000,
                "data_sources": ["Sales records", "Distribution logs", "Mobile payment data"],
                "required": True,
                "tooltip": "Must have evidence of operational status (e.g., pay-as-you-go records)."
            },
            {
                "parameter": "system_wattage",
                "label": "System Wattage",
                "description": "Typical watt-peak rating of individual SHS unit.",
                "unit": "Wp",
                "typical_range": {"min": 10, "max": 200},
                "example_value": 50,
                "data_sources": ["Product spec sheet", "Lighting Global / VeraSol certification"],
                "required": True,
                "tooltip": "Determines the baseline fossil fuel displacement per unit."
            },
            {
                "parameter": "kerosene_displaced_litres",
                "label": "Kerosene Displaced per System",
                "description": "Annual litres of kerosene displaced per household.",
                "unit": "litres/year",
                "typical_range": {"min": 30, "max": 150},
                "example_value": 55,
                "data_sources": ["Baseline household survey", "National energy access survey", "Gold Standard default values"],
                "required": True,
                "tooltip": "Based on household surveys or approved default values."
            }
        ],
        "real_world_examples": [
            {"project": "d.light Solar Home Systems, Sub-Saharan Africa", "credits": 15000, "year": 2023}
        ],
        "regulatory_notes": "Gold Standard and VCS are most common standards. Requires usage monitoring (e.g., PAYG data).",
        "cdm_tools_needed": ["TOOL01", "TOOL21"],
        "estimated_cost_range_usd": {"min": 1000000, "max": 30000000},
        "crediting_period_years": {"min": 5, "max": 10}
    },

    "solar_mini_grid": {
        "id": "solar_mini_grid",
        "name": "Solar Mini-Grid",
        "description": "Isolated or semi-isolated solar-battery mini-grid serving a rural community or industrial site, displacing diesel generation.",
        "sector": "Energy",
        "user_types": ["Mini-Grid Developer", "Municipal Utility", "Social Enterprise"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-I.L", "AMS-I.F"],
        "recommended_methodology": "AMS-I.L",
        "scale": "Small",
        "typical_credit_range": {"min": 500, "max": 15000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "installed_capacity_kwp",
                "label": "Solar Installed Capacity",
                "description": "Peak DC capacity of the solar array.",
                "unit": "kWp",
                "typical_range": {"min": 10, "max": 1000},
                "example_value": 100,
                "data_sources": ["Module datasheets", "Mini-grid design report", "Contractor invoice"],
                "required": True,
                "tooltip": "Excludes battery storage capacity."
            },
            {
                "parameter": "battery_capacity_kwh",
                "label": "Battery Storage Capacity",
                "description": "Usable energy storage in the battery bank.",
                "unit": "kWh",
                "typical_range": {"min": 20, "max": 2000},
                "example_value": 200,
                "data_sources": ["Battery spec sheet", "System design report"],
                "required": True,
                "tooltip": "Usable capacity after depth-of-discharge limits."
            },
            {
                "parameter": "diesel_displaced_litres_yr",
                "label": "Annual Diesel Displaced",
                "description": "Litres of diesel fuel no longer consumed due to solar generation.",
                "unit": "litres/year",
                "typical_range": {"min": 5000, "max": 500000},
                "example_value": 60000,
                "data_sources": ["Baseline diesel purchase records", "Mini-grid dispatch log", "Fuel receipts"],
                "required": True,
                "tooltip": "Compare pre-project diesel use with post-project residual."
            },
            {
                "parameter": "number_of_connections",
                "label": "Number of Connections",
                "description": "Households and businesses connected to the mini-grid.",
                "unit": "count",
                "typical_range": {"min": 50, "max": 5000},
                "example_value": 300,
                "data_sources": ["Connection register", "Smart meter database", "Community survey"],
                "required": True,
                "tooltip": "Used for co-benefit assessment (SDG 7)."
            }
        ],
        "real_world_examples": [
            {"project": "PowerHive Kisii County, Kenya", "credits": 2400, "year": 2023}
        ],
        "regulatory_notes": "Gold Standard preferred for co-benefits. VCS also applicable.",
        "cdm_tools_needed": ["TOOL01", "TOOL21"],
        "estimated_cost_range_usd": {"min": 200000, "max": 5000000},
        "crediting_period_years": {"min": 7, "max": 14}
    },

    "waste_heat_orc": {
        "id": "waste_heat_orc",
        "name": "Waste Heat Recovery (ORC) for Power Generation",
        "description": "Organic Rankine Cycle or similar system recovering waste heat from industrial processes to generate electricity.",
        "sector": "Energy",
        "user_types": ["Industrial Facility", "ESCO", "Project Developer"],
        "value_chain_position": "core",
        "applicable_methodologies": ["ACM0012", "AMS-III.Q"],
        "recommended_methodology": "ACM0012",
        "scale": "Small",
        "typical_credit_range": {"min": 3000, "max": 50000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "thermal_input_mw",
                "label": "Waste Heat Thermal Input",
                "description": "Thermal energy available from the waste heat source.",
                "unit": "MWth",
                "typical_range": {"min": 1, "max": 50},
                "example_value": 10,
                "data_sources": ["Process heat balance", "Flue gas temperature and flow measurement", "Engineering study"],
                "required": True,
                "tooltip": "Measured at the heat recovery unit inlet."
            },
            {
                "parameter": "orc_efficiency",
                "label": "ORC Electrical Efficiency",
                "description": "Net electrical conversion efficiency of the ORC system.",
                "unit": "%",
                "typical_range": {"min": 8, "max": 25},
                "example_value": 15,
                "data_sources": ["ORC vendor datasheet", "Commissioning performance test"],
                "required": True,
                "tooltip": "Depends on heat source temperature and cooling medium."
            },
            {
                "parameter": "grid_emission_factor",
                "label": "Grid Emission Factor",
                "description": "CO2 intensity of displaced grid electricity.",
                "unit": "tCO2/MWh",
                "typical_range": {"min": 0.4, "max": 1.2},
                "example_value": 0.85,
                "data_sources": ["National grid authority", "IFI Harmonized Grid EF database"],
                "required": True,
                "tooltip": "Applicable if electricity is exported or displaces grid import."
            }
        ],
        "real_world_examples": [
            {"project": "ACC Cement Waste Heat Recovery, India", "credits": 28000, "year": 2022}
        ],
        "regulatory_notes": "Eligible under CDM, VCS. Must prove heat was previously wasted.",
        "cdm_tools_needed": ["TOOL01", "TOOL07"],
        "estimated_cost_range_usd": {"min": 5000000, "max": 40000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    "chp_cogen": {
        "id": "chp_cogen",
        "name": "Combined Heat and Power (CHP / Cogeneration)",
        "description": "Simultaneous generation of electricity and useful thermal energy from a single fuel source, improving overall efficiency.",
        "sector": "Energy",
        "user_types": ["Industrial Facility", "District Energy Provider", "ESCO"],
        "value_chain_position": "core",
        "applicable_methodologies": ["ACM0006", "AMS-II.B"],
        "recommended_methodology": "ACM0006",
        "scale": "Large",
        "typical_credit_range": {"min": 5000, "max": 80000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "electrical_output_mw",
                "label": "Electrical Output Capacity",
                "description": "Net electrical output of the CHP system.",
                "unit": "MWe",
                "typical_range": {"min": 1, "max": 100},
                "example_value": 20,
                "data_sources": ["Engine/turbine spec sheet", "EPC contract", "PPA"],
                "required": True,
                "tooltip": "Net of parasitic loads."
            },
            {
                "parameter": "thermal_output_mw",
                "label": "Useful Thermal Output",
                "description": "Thermal energy supplied to process or district heating.",
                "unit": "MWth",
                "typical_range": {"min": 2, "max": 150},
                "example_value": 25,
                "data_sources": ["Heat meter readings", "Process heat demand analysis"],
                "required": True,
                "tooltip": "Only thermal energy that displaces a separate heat source counts."
            },
            {
                "parameter": "overall_efficiency",
                "label": "Overall CHP Efficiency",
                "description": "Combined electrical and thermal efficiency.",
                "unit": "%",
                "typical_range": {"min": 65, "max": 90},
                "example_value": 80,
                "data_sources": ["Commissioning test report", "CHP vendor datasheet"],
                "required": True,
                "tooltip": "Higher overall efficiency improves the emission reduction."
            },
            {
                "parameter": "fuel_type",
                "label": "Fuel Type",
                "description": "Primary fuel used in the CHP system.",
                "unit": "text",
                "typical_range": {"min": None, "max": None},
                "example_value": "Natural gas",
                "data_sources": ["Fuel supply agreement", "Gas utility bill"],
                "required": True,
                "tooltip": "Natural gas, biomass, or biogas. Fuel determines emission factor."
            }
        ],
        "real_world_examples": [
            {"project": "Godrej CHP, Maharashtra", "credits": 35000, "year": 2023}
        ],
        "regulatory_notes": "Eligible under CDM, VCS. Baseline must account for separate heat and power generation.",
        "cdm_tools_needed": ["TOOL01", "TOOL07", "TOOL05"],
        "estimated_cost_range_usd": {"min": 10000000, "max": 80000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    "coal_to_gas": {
        "id": "coal_to_gas",
        "name": "Coal-to-Natural-Gas Fuel Switch (Power)",
        "description": "Replacement of coal-fired power generation with natural gas combined cycle, reducing CO2 per MWh.",
        "sector": "Energy",
        "user_types": ["Energy Company", "Utility"],
        "value_chain_position": "core",
        "applicable_methodologies": ["ACM0011", "AM0029"],
        "recommended_methodology": "ACM0011",
        "scale": "Large",
        "typical_credit_range": {"min": 50000, "max": 500000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "annual_generation_mwh",
                "label": "Annual Electricity Generation",
                "description": "Total net electricity produced per year after fuel switch.",
                "unit": "MWh/year",
                "typical_range": {"min": 500000, "max": 10000000},
                "example_value": 3000000,
                "data_sources": ["Grid meter readings", "Plant dispatch records", "PPA"],
                "required": True,
                "tooltip": "Net generation after auxiliary consumption."
            },
            {
                "parameter": "baseline_ef_coal",
                "label": "Baseline Coal Emission Factor",
                "description": "CO2 per MWh of the coal plant being displaced.",
                "unit": "tCO2/MWh",
                "typical_range": {"min": 0.8, "max": 1.3},
                "example_value": 1.0,
                "data_sources": ["Coal plant efficiency records", "Coal analysis certificates", "IPCC default factors"],
                "required": True,
                "tooltip": "Based on actual coal heat rate and carbon content."
            },
            {
                "parameter": "project_ef_gas",
                "label": "Project Gas Emission Factor",
                "description": "CO2 per MWh of the new gas plant.",
                "unit": "tCO2/MWh",
                "typical_range": {"min": 0.35, "max": 0.55},
                "example_value": 0.42,
                "data_sources": ["Gas turbine spec sheet", "Gas composition analysis", "Metered gas flow and generation"],
                "required": True,
                "tooltip": "CCGT achieves lower EF than open-cycle gas turbines."
            },
            {
                "parameter": "gas_plant_efficiency",
                "label": "Gas Plant Net Efficiency",
                "description": "Net electrical efficiency of the gas combined cycle plant.",
                "unit": "%",
                "typical_range": {"min": 45, "max": 62},
                "example_value": 55,
                "data_sources": ["Performance test report", "Gas turbine OEM datasheet"],
                "required": True,
                "tooltip": "Higher efficiency means lower emission factor per MWh."
            }
        ],
        "real_world_examples": [
            {"project": "Pagbilao Gas Conversion, Philippines", "credits": 320000, "year": 2022}
        ],
        "regulatory_notes": "Eligible under CDM (ACM0011), VCS. Must demonstrate that coal plant would have continued operating.",
        "cdm_tools_needed": ["TOOL01", "TOOL07", "TOOL03"],
        "estimated_cost_range_usd": {"min": 200000000, "max": 1000000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    "gas_ccgt_replace": {
        "id": "gas_ccgt_replace",
        "name": "Efficient CCGT Replacing Older Gas Turbines",
        "description": "Replacement of inefficient open-cycle gas turbines with modern combined-cycle gas turbines to reduce CO2 per MWh.",
        "sector": "Energy",
        "user_types": ["Energy Company", "Utility", "IPP"],
        "value_chain_position": "core",
        "applicable_methodologies": ["ACM0011", "AM0061"],
        "recommended_methodology": "ACM0011",
        "scale": "Large",
        "typical_credit_range": {"min": 30000, "max": 200000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "annual_generation_mwh",
                "label": "Annual Net Generation",
                "description": "Total electricity produced by the new CCGT per year.",
                "unit": "MWh/year",
                "typical_range": {"min": 500000, "max": 8000000},
                "example_value": 2500000,
                "data_sources": ["Grid meter readings", "Plant dispatch records"],
                "required": True,
                "tooltip": "Net generation after auxiliary consumption."
            },
            {
                "parameter": "baseline_efficiency",
                "label": "Baseline OCGT Efficiency",
                "description": "Net efficiency of the existing open-cycle gas turbines.",
                "unit": "%",
                "typical_range": {"min": 28, "max": 38},
                "example_value": 33,
                "data_sources": ["Old plant heat rate tests", "O&M efficiency records"],
                "required": True,
                "tooltip": "Lower baseline efficiency means larger emission reduction."
            },
            {
                "parameter": "project_efficiency",
                "label": "New CCGT Efficiency",
                "description": "Net efficiency of the replacement combined-cycle plant.",
                "unit": "%",
                "typical_range": {"min": 50, "max": 63},
                "example_value": 58,
                "data_sources": ["Turbine OEM datasheet", "Performance test report"],
                "required": True,
                "tooltip": "Modern CCGT exceeds 60% efficiency."
            }
        ],
        "real_world_examples": [
            {"project": "Ras Laffan C CCGT, Qatar", "credits": 180000, "year": 2023}
        ],
        "regulatory_notes": "Eligible under CDM (ACM0011), VCS. Fuel switch within same fuel type still generates credits from efficiency gain.",
        "cdm_tools_needed": ["TOOL01", "TOOL07"],
        "estimated_cost_range_usd": {"min": 300000000, "max": 800000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    # ======================================================================
    # WASTE  (#17 - #23)
    # ======================================================================

    "landfill_gas_flare": {
        "id": "landfill_gas_flare",
        "name": "Landfill Gas Capture and Flaring",
        "description": "Collection of methane-rich landfill gas and destruction by enclosed flare to convert CH4 to CO2.",
        "sector": "Waste",
        "user_types": ["Municipal Authority", "Waste Company", "Project Developer"],
        "value_chain_position": "core",
        "applicable_methodologies": ["ACM0001", "AMS-III.G"],
        "recommended_methodology": "ACM0001",
        "scale": "Large",
        "typical_credit_range": {"min": 20000, "max": 200000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "waste_in_place_tonnes",
                "label": "Waste in Place",
                "description": "Total mass of waste deposited in the landfill.",
                "unit": "tonnes",
                "typical_range": {"min": 500000, "max": 20000000},
                "example_value": 5000000,
                "data_sources": ["Landfill records", "Weigh bridge data", "Waste composition study"],
                "required": True,
                "tooltip": "Drives the first-order decay gas generation model."
            },
            {
                "parameter": "gas_collection_efficiency",
                "label": "Gas Collection Efficiency",
                "description": "Fraction of generated landfill gas that is captured.",
                "unit": "%",
                "typical_range": {"min": 50, "max": 85},
                "example_value": 70,
                "data_sources": ["Gas well network design", "Surface emission monitoring", "USEPA AP-42 defaults"],
                "required": True,
                "tooltip": "Depends on landfill cover integrity and well spacing."
            },
            {
                "parameter": "methane_content",
                "label": "Methane Content in LFG",
                "description": "Volumetric fraction of methane in the landfill gas.",
                "unit": "%",
                "typical_range": {"min": 40, "max": 60},
                "example_value": 50,
                "data_sources": ["Continuous gas analyser", "Periodic gas sampling lab results"],
                "required": True,
                "tooltip": "Typically 45-55% for mature landfills."
            },
            {
                "parameter": "flare_destruction_efficiency",
                "label": "Flare Destruction Efficiency",
                "description": "Fraction of methane destroyed in the flare.",
                "unit": "%",
                "typical_range": {"min": 95, "max": 99.5},
                "example_value": 98,
                "data_sources": ["Flare OEM spec", "Stack test emissions report"],
                "required": True,
                "tooltip": "Enclosed flares typically achieve >98% destruction."
            }
        ],
        "real_world_examples": [
            {"project": "Norte III Landfill, Monterrey Mexico", "credits": 140000, "year": 2022}
        ],
        "regulatory_notes": "Eligible under CDM (ACM0001), VCS. One of the earliest CDM project types.",
        "cdm_tools_needed": ["TOOL01", "TOOL04"],
        "estimated_cost_range_usd": {"min": 2000000, "max": 15000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    "landfill_gas_power": {
        "id": "landfill_gas_power",
        "name": "Landfill Gas to Electricity",
        "description": "Capture of landfill gas and use as fuel in gas engines or turbines to generate electricity.",
        "sector": "Waste",
        "user_types": ["Municipal Authority", "Waste Company", "Project Developer"],
        "value_chain_position": "core",
        "applicable_methodologies": ["ACM0001", "AMS-III.G", "AMS-I.D"],
        "recommended_methodology": "ACM0001",
        "scale": "Large",
        "typical_credit_range": {"min": 30000, "max": 250000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "lfg_flow_rate_m3_hr",
                "label": "LFG Flow Rate",
                "description": "Average hourly flow of landfill gas captured.",
                "unit": "m3/hour",
                "typical_range": {"min": 200, "max": 5000},
                "example_value": 1500,
                "data_sources": ["Gas flow meter readings", "SCADA data", "LFG generation model"],
                "required": True,
                "tooltip": "Measured at the gas collection header."
            },
            {
                "parameter": "methane_content",
                "label": "Methane Content",
                "description": "Volumetric methane fraction in the landfill gas.",
                "unit": "%",
                "typical_range": {"min": 40, "max": 60},
                "example_value": 50,
                "data_sources": ["Continuous gas analyser", "Lab test results"],
                "required": True,
                "tooltip": "Determines calorific value of the fuel."
            },
            {
                "parameter": "genset_capacity_mw",
                "label": "Genset Electrical Capacity",
                "description": "Total installed electrical capacity of LFG engines.",
                "unit": "MW",
                "typical_range": {"min": 0.5, "max": 20},
                "example_value": 5,
                "data_sources": ["Engine OEM datasheet", "EPC contract"],
                "required": True,
                "tooltip": "Sized to match the expected LFG flow rate."
            },
            {
                "parameter": "grid_emission_factor",
                "label": "Grid Emission Factor",
                "description": "CO2 intensity of displaced grid electricity.",
                "unit": "tCO2/MWh",
                "typical_range": {"min": 0.4, "max": 1.2},
                "example_value": 0.85,
                "data_sources": ["National grid authority", "IFI Harmonized Grid EF database"],
                "required": True,
                "tooltip": "Credit from grid displacement adds to methane avoidance credit."
            }
        ],
        "real_world_examples": [
            {"project": "Bandeirantes Landfill, Sao Paulo", "credits": 195000, "year": 2022}
        ],
        "regulatory_notes": "Eligible under CDM (ACM0001), VCS, Gold Standard. Credits include both methane destruction and grid displacement.",
        "cdm_tools_needed": ["TOOL01", "TOOL04", "TOOL07"],
        "estimated_cost_range_usd": {"min": 5000000, "max": 30000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    "composting_muni": {
        "id": "composting_muni",
        "name": "Municipal Organic Waste Composting",
        "description": "Diversion of organic municipal solid waste from landfill to aerobic composting, avoiding methane emissions.",
        "sector": "Waste",
        "user_types": ["Municipal Authority", "Waste Company", "Social Enterprise"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-III.F", "AM0025"],
        "recommended_methodology": "AMS-III.F",
        "scale": "Small",
        "typical_credit_range": {"min": 3000, "max": 50000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "organic_waste_tonnes_yr",
                "label": "Annual Organic Waste Diverted",
                "description": "Total wet tonnes of organic waste composted per year.",
                "unit": "tonnes/year",
                "typical_range": {"min": 5000, "max": 200000},
                "example_value": 30000,
                "data_sources": ["Weigh bridge records", "Collection route data", "Municipal waste audits"],
                "required": True,
                "tooltip": "Only the organic fraction counts; exclude inerts and recyclables."
            },
            {
                "parameter": "methane_correction_factor",
                "label": "Methane Correction Factor (MCF)",
                "description": "Fraction of organic carbon that decomposes anaerobically in the baseline landfill.",
                "unit": "fraction",
                "typical_range": {"min": 0.4, "max": 1.0},
                "example_value": 0.8,
                "data_sources": ["IPCC MCF defaults by landfill type", "National GHG inventory"],
                "required": True,
                "tooltip": "MCF = 1.0 for managed anaerobic sites; lower for shallow or dry sites."
            },
            {
                "parameter": "doc_fraction",
                "label": "Degradable Organic Carbon (DOC)",
                "description": "Fraction of organic carbon in the waste.",
                "unit": "fraction",
                "typical_range": {"min": 0.10, "max": 0.25},
                "example_value": 0.15,
                "data_sources": ["Waste composition analysis", "IPCC default values"],
                "required": True,
                "tooltip": "Based on waste composition (food waste has higher DOC)."
            }
        ],
        "real_world_examples": [
            {"project": "Addis Ababa Composting Facility, Ethiopia", "credits": 18000, "year": 2023}
        ],
        "regulatory_notes": "Eligible under CDM, VCS, Gold Standard. Must demonstrate waste would have gone to landfill.",
        "cdm_tools_needed": ["TOOL01", "TOOL04"],
        "estimated_cost_range_usd": {"min": 1000000, "max": 10000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    "ww_methane_muni": {
        "id": "ww_methane_muni",
        "name": "Municipal Wastewater Methane Recovery",
        "description": "Capture and destruction or use of methane from municipal wastewater treatment, displacing open anaerobic lagoon emissions.",
        "sector": "Waste",
        "user_types": ["Municipal Authority", "Water Utility", "Project Developer"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AM0080", "AMS-III.H"],
        "recommended_methodology": "AMS-III.H",
        "scale": "Small",
        "typical_credit_range": {"min": 5000, "max": 60000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "population_served",
                "label": "Population Served",
                "description": "Number of people whose wastewater is treated.",
                "unit": "persons",
                "typical_range": {"min": 50000, "max": 5000000},
                "example_value": 500000,
                "data_sources": ["Municipal census data", "Utility connection records"],
                "required": True,
                "tooltip": "Determines organic load entering the treatment plant."
            },
            {
                "parameter": "cod_load_kg_yr",
                "label": "Annual COD Load",
                "description": "Chemical Oxygen Demand entering the treatment system per year.",
                "unit": "kg COD/year",
                "typical_range": {"min": 1000000, "max": 100000000},
                "example_value": 18000000,
                "data_sources": ["Influent lab testing", "National per-capita COD default"],
                "required": True,
                "tooltip": "Drives methane generation potential."
            },
            {
                "parameter": "methane_captured_m3_yr",
                "label": "Annual Methane Captured",
                "description": "Volume of methane recovered from covered digesters/lagoons.",
                "unit": "m3 CH4/year",
                "typical_range": {"min": 100000, "max": 10000000},
                "example_value": 2000000,
                "data_sources": ["Gas flow meter readings", "Digester monitoring data"],
                "required": True,
                "tooltip": "Measured with calibrated gas flow meter."
            }
        ],
        "real_world_examples": [
            {"project": "Santa Cruz WWTP Methane, Bolivia", "credits": 35000, "year": 2022}
        ],
        "regulatory_notes": "Eligible under CDM, VCS, Gold Standard. Baseline is open lagoon or untreated discharge.",
        "cdm_tools_needed": ["TOOL01", "TOOL04"],
        "estimated_cost_range_usd": {"min": 3000000, "max": 20000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    "ww_methane_industrial": {
        "id": "ww_methane_industrial",
        "name": "Industrial Wastewater Methane Recovery",
        "description": "Capture and destruction of methane from high-strength industrial wastewater (e.g., palm oil, starch, brewery effluent).",
        "sector": "Waste",
        "user_types": ["Industrial Facility", "Agribusiness", "Project Developer"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-III.H", "AM0013"],
        "recommended_methodology": "AMS-III.H",
        "scale": "Small",
        "typical_credit_range": {"min": 5000, "max": 80000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "cod_load_kg_yr",
                "label": "Annual COD Load",
                "description": "Chemical Oxygen Demand of industrial effluent per year.",
                "unit": "kg COD/year",
                "typical_range": {"min": 500000, "max": 50000000},
                "example_value": 10000000,
                "data_sources": ["Effluent lab analysis", "Production records", "Environmental permit"],
                "required": True,
                "tooltip": "High-COD industries (palm oil, cassava) generate more methane."
            },
            {
                "parameter": "methane_captured_m3_yr",
                "label": "Annual Methane Captured",
                "description": "Volume of methane captured from covered lagoons or UASB reactors.",
                "unit": "m3 CH4/year",
                "typical_range": {"min": 200000, "max": 15000000},
                "example_value": 4000000,
                "data_sources": ["Gas flow meter readings", "Reactor monitoring system"],
                "required": True,
                "tooltip": "Must be measured with calibrated flow meters."
            },
            {
                "parameter": "baseline_treatment",
                "label": "Baseline Treatment Method",
                "description": "How wastewater was treated before the project.",
                "unit": "text",
                "typical_range": {"min": None, "max": None},
                "example_value": "Open anaerobic lagoon",
                "data_sources": ["Pre-project site assessment", "Environmental compliance records"],
                "required": True,
                "tooltip": "Must demonstrate anaerobic conditions in baseline (open lagoon, pit)."
            }
        ],
        "real_world_examples": [
            {"project": "POME Methane Capture, Sabah Malaysia", "credits": 65000, "year": 2023}
        ],
        "regulatory_notes": "Eligible under CDM, VCS, Gold Standard. Palm oil mill effluent (POME) is the most common application.",
        "cdm_tools_needed": ["TOOL01", "TOOL04"],
        "estimated_cost_range_usd": {"min": 1000000, "max": 10000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    "anaerobic_digestion": {
        "id": "anaerobic_digestion",
        "name": "Centralised Anaerobic Digestion Facility",
        "description": "Purpose-built digestion plant treating mixed organic waste (food waste, crop residues, sewage sludge) to produce biogas and digestate.",
        "sector": "Waste",
        "user_types": ["Waste Company", "Municipal Authority", "Project Developer"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-III.D", "AMS-III.H", "AMS-I.D"],
        "recommended_methodology": "AMS-III.D",
        "scale": "Small",
        "typical_credit_range": {"min": 5000, "max": 60000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "feedstock_tonnes_yr",
                "label": "Annual Feedstock Input",
                "description": "Total wet tonnes of organic waste processed per year.",
                "unit": "tonnes/year",
                "typical_range": {"min": 5000, "max": 200000},
                "example_value": 50000,
                "data_sources": ["Weigh bridge records", "Waste delivery manifests", "Gate fee contracts"],
                "required": True,
                "tooltip": "Includes food waste, crop residues, animal manure."
            },
            {
                "parameter": "biogas_yield_m3_per_tonne",
                "label": "Biogas Yield",
                "description": "Volume of biogas produced per tonne of feedstock.",
                "unit": "m3/tonne",
                "typical_range": {"min": 50, "max": 200},
                "example_value": 120,
                "data_sources": ["Lab BMP tests", "Digester monitoring data", "Literature values by feedstock"],
                "required": True,
                "tooltip": "Varies widely by feedstock type; lab BMP test recommended."
            },
            {
                "parameter": "biogas_utilisation",
                "label": "Biogas Utilisation Pathway",
                "description": "How the biogas is used (flare, electricity, heat, biomethane upgrade).",
                "unit": "text",
                "typical_range": {"min": None, "max": None},
                "example_value": "CHP electricity + heat",
                "data_sources": ["Plant design report", "Off-take agreement"],
                "required": True,
                "tooltip": "Electricity and biomethane paths add grid displacement credits."
            }
        ],
        "real_world_examples": [
            {"project": "Suez Ecoparc AD Facility, Barcelona", "credits": 42000, "year": 2023}
        ],
        "regulatory_notes": "Eligible under CDM, VCS, Gold Standard. Multiple credit streams: methane avoidance + grid displacement + fertiliser displacement.",
        "cdm_tools_needed": ["TOOL01", "TOOL04"],
        "estimated_cost_range_usd": {"min": 5000000, "max": 40000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    "swm_methane_avoid": {
        "id": "swm_methane_avoid",
        "name": "Solid Waste Management - Methane Avoidance",
        "description": "Improved solid waste management practices that divert organic waste from landfills, avoiding methane generation. Includes mechanical-biological treatment, waste-to-energy, and similar approaches.",
        "sector": "Waste",
        "user_types": ["Municipal Authority", "Waste Company", "Project Developer"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-III.E", "ACM0022"],
        "recommended_methodology": "AMS-III.E",
        "scale": "Large",
        "typical_credit_range": {"min": 10000, "max": 150000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "waste_diverted_tonnes_yr",
                "label": "Organic Waste Diverted from Landfill",
                "description": "Tonnes of organic waste prevented from entering landfill per year.",
                "unit": "tonnes/year",
                "typical_range": {"min": 20000, "max": 500000},
                "example_value": 100000,
                "data_sources": ["Weigh bridge records", "MBT plant records", "Municipal waste statistics"],
                "required": True,
                "tooltip": "Only organic fraction counts; inerts do not generate methane."
            },
            {
                "parameter": "waste_composition",
                "label": "Waste Composition",
                "description": "Breakdown of waste by type (food, garden, paper, wood, textile).",
                "unit": "% by weight",
                "typical_range": {"min": None, "max": None},
                "example_value": "Food 50%, Garden 20%, Paper 15%, Wood 10%, Textile 5%",
                "data_sources": ["Waste composition study", "National waste statistics", "IPCC Waste Model defaults"],
                "required": True,
                "tooltip": "Each waste type has different DOC and decay rate."
            },
            {
                "parameter": "methane_correction_factor",
                "label": "Methane Correction Factor",
                "description": "MCF for the baseline landfill.",
                "unit": "fraction",
                "typical_range": {"min": 0.4, "max": 1.0},
                "example_value": 0.8,
                "data_sources": ["IPCC defaults by landfill management type"],
                "required": True,
                "tooltip": "MCF = 1.0 for managed deep anaerobic landfills."
            }
        ],
        "real_world_examples": [
            {"project": "Tianjin Integrated Waste, China", "credits": 120000, "year": 2022}
        ],
        "regulatory_notes": "Eligible under CDM, VCS, Gold Standard. Uses IPCC first-order decay model for baseline.",
        "cdm_tools_needed": ["TOOL01", "TOOL04"],
        "estimated_cost_range_usd": {"min": 10000000, "max": 80000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    # ======================================================================
    # FORESTRY  (#24 - #31)
    # ======================================================================

    "redd_avoided_deforest": {
        "id": "redd_avoided_deforest",
        "name": "REDD+ Avoided Deforestation",
        "description": "Protection of tropical forest from planned or unplanned deforestation, preserving carbon stocks and biodiversity.",
        "sector": "Forestry",
        "user_types": ["Conservation NGO", "Government", "Indigenous Community", "Project Developer"],
        "value_chain_position": "core",
        "applicable_methodologies": ["VM0007", "VM0009", "VM0015"],
        "recommended_methodology": "VM0007",
        "scale": "Large",
        "typical_credit_range": {"min": 50000, "max": 2000000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "project_area_ha",
                "label": "Project Area",
                "description": "Total area of forest under protection.",
                "unit": "hectares",
                "typical_range": {"min": 5000, "max": 500000},
                "example_value": 50000,
                "data_sources": ["Land title / concession document", "GIS shapefiles", "Government gazette"],
                "required": True,
                "tooltip": "Delineated by legally defined boundaries."
            },
            {
                "parameter": "baseline_deforestation_rate",
                "label": "Baseline Deforestation Rate",
                "description": "Historical annual rate of forest loss in the reference region.",
                "unit": "%/year",
                "typical_range": {"min": 0.2, "max": 5.0},
                "example_value": 1.5,
                "data_sources": ["Hansen Global Forest Change data", "National forest inventory", "Remote sensing analysis"],
                "required": True,
                "tooltip": "Calculated from 10-year historical remote sensing analysis."
            },
            {
                "parameter": "carbon_stock_tco2_ha",
                "label": "Forest Carbon Stock",
                "description": "Average above-ground and below-ground carbon stock per hectare.",
                "unit": "tCO2e/ha",
                "typical_range": {"min": 150, "max": 800},
                "example_value": 450,
                "data_sources": ["Forest inventory plots", "Allometric equations", "LiDAR survey"],
                "required": True,
                "tooltip": "Measured from stratified sample plots or LiDAR."
            },
            {
                "parameter": "leakage_deduction",
                "label": "Leakage Deduction",
                "description": "Percentage deduction for activity-shifting and market leakage.",
                "unit": "%",
                "typical_range": {"min": 5, "max": 40},
                "example_value": 15,
                "data_sources": ["VCS REDD+ leakage guidance", "Agent-of-deforestation analysis"],
                "required": True,
                "tooltip": "Higher if deforestation drivers are mobile (e.g., shifting cultivation)."
            }
        ],
        "real_world_examples": [
            {"project": "Kasigau Corridor REDD+, Kenya", "credits": 1200000, "year": 2023},
            {"project": "Alto Mayo REDD+, Peru", "credits": 800000, "year": 2022}
        ],
        "regulatory_notes": "VCS (Verra) is primary standard. Requires jurisdictional nesting under REDD+ framework. Buffer pool contributions required.",
        "cdm_tools_needed": ["TOOL14"],
        "estimated_cost_range_usd": {"min": 2000000, "max": 20000000},
        "crediting_period_years": {"min": 20, "max": 40}
    },

    "improved_forest_mgmt": {
        "id": "improved_forest_mgmt",
        "name": "Improved Forest Management (IFM)",
        "description": "Adoption of improved forest management practices (extended rotation, reduced-impact logging, fire management) to increase carbon stocks relative to baseline.",
        "sector": "Forestry",
        "user_types": ["Forestry Company", "Landowner", "Conservation NGO"],
        "value_chain_position": "core",
        "applicable_methodologies": ["VM0010", "VM0012", "ACR IFM"],
        "recommended_methodology": "VM0010",
        "scale": "Large",
        "typical_credit_range": {"min": 10000, "max": 500000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "project_area_ha",
                "label": "Project Area",
                "description": "Total managed forest area under IFM practices.",
                "unit": "hectares",
                "typical_range": {"min": 1000, "max": 200000},
                "example_value": 25000,
                "data_sources": ["Forest management plan", "Land title", "GIS shapefiles"],
                "required": True,
                "tooltip": "Area under active improved management."
            },
            {
                "parameter": "baseline_harvest_m3_yr",
                "label": "Baseline Harvest Volume",
                "description": "Annual timber harvest under conventional management.",
                "unit": "m3/year",
                "typical_range": {"min": 5000, "max": 500000},
                "example_value": 60000,
                "data_sources": ["Historical harvest records", "Forest management plan", "Timber sales data"],
                "required": True,
                "tooltip": "What would have been logged without the project."
            },
            {
                "parameter": "project_harvest_m3_yr",
                "label": "Project Harvest Volume",
                "description": "Reduced annual harvest under improved management.",
                "unit": "m3/year",
                "typical_range": {"min": 2000, "max": 300000},
                "example_value": 30000,
                "data_sources": ["IFM plan", "FSC/PEFC audit reports"],
                "required": True,
                "tooltip": "Reduced harvest increases standing carbon stock."
            },
            {
                "parameter": "carbon_stock_tco2_ha",
                "label": "Average Carbon Stock",
                "description": "Standing carbon stock per hectare.",
                "unit": "tCO2e/ha",
                "typical_range": {"min": 100, "max": 600},
                "example_value": 300,
                "data_sources": ["Forest inventory plots", "Allometric equations"],
                "required": True,
                "tooltip": "Measured from sample plots; includes above and below-ground."
            }
        ],
        "real_world_examples": [
            {"project": "Finite Carbon IFM, Appalachian USA", "credits": 150000, "year": 2023}
        ],
        "regulatory_notes": "Eligible under VCS (VM0010), ACR. Buffer pool required for permanence risk.",
        "cdm_tools_needed": ["TOOL14"],
        "estimated_cost_range_usd": {"min": 500000, "max": 5000000},
        "crediting_period_years": {"min": 20, "max": 40}
    },

    "afforestation_degraded": {
        "id": "afforestation_degraded",
        "name": "Afforestation of Degraded Land",
        "description": "Planting trees on degraded, non-forest land to sequester atmospheric CO2 in growing biomass and soil.",
        "sector": "Forestry",
        "user_types": ["Government", "Landowner", "Project Developer", "NGO"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AR-ACM0003", "AR-AMS0007", "VM0047"],
        "recommended_methodology": "AR-ACM0003",
        "scale": "Large",
        "typical_credit_range": {"min": 5000, "max": 200000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "planted_area_ha",
                "label": "Planted Area",
                "description": "Total area of degraded land planted with trees.",
                "unit": "hectares",
                "typical_range": {"min": 500, "max": 100000},
                "example_value": 10000,
                "data_sources": ["Planting records", "GIS shapefiles", "Land title / lease"],
                "required": True,
                "tooltip": "Must demonstrate land was non-forest at project start."
            },
            {
                "parameter": "species_mix",
                "label": "Tree Species Planted",
                "description": "Species composition of the planted forest.",
                "unit": "text",
                "typical_range": {"min": None, "max": None},
                "example_value": "Eucalyptus 40%, Acacia 30%, Indigenous mix 30%",
                "data_sources": ["Planting plan", "Nursery procurement records"],
                "required": True,
                "tooltip": "Species determines growth rate and carbon sequestration."
            },
            {
                "parameter": "mean_annual_increment",
                "label": "Mean Annual Increment (MAI)",
                "description": "Average annual timber volume growth per hectare.",
                "unit": "m3/ha/year",
                "typical_range": {"min": 3, "max": 30},
                "example_value": 12,
                "data_sources": ["Species growth tables", "Local forestry research", "Sample plot measurements"],
                "required": True,
                "tooltip": "Higher for tropical species (eucalyptus); lower for temperate/arid sites."
            },
            {
                "parameter": "survival_rate",
                "label": "Seedling Survival Rate",
                "description": "Percentage of planted seedlings that survive after 2 years.",
                "unit": "%",
                "typical_range": {"min": 60, "max": 95},
                "example_value": 80,
                "data_sources": ["Field survival surveys", "Monitoring plot data"],
                "required": True,
                "tooltip": "Used to calculate net stocked area."
            }
        ],
        "real_world_examples": [
            {"project": "Humbo Assisted Regeneration, Ethiopia", "credits": 38000, "year": 2023}
        ],
        "regulatory_notes": "Eligible under CDM (AR), VCS, Gold Standard. Must prove land eligibility (non-forest since at least 1990 for CDM).",
        "cdm_tools_needed": ["TOOL14", "TOOL15"],
        "estimated_cost_range_usd": {"min": 2000000, "max": 30000000},
        "crediting_period_years": {"min": 20, "max": 60}
    },

    "reforestation_plantation": {
        "id": "reforestation_plantation",
        "name": "Commercial Reforestation Plantation",
        "description": "Establishment of commercial timber or pulpwood plantation on previously deforested land, sequestering CO2 while producing sustainable timber.",
        "sector": "Forestry",
        "user_types": ["Forestry Company", "Landowner", "Investor"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AR-ACM0003", "VM0047"],
        "recommended_methodology": "AR-ACM0003",
        "scale": "Large",
        "typical_credit_range": {"min": 10000, "max": 300000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "planted_area_ha",
                "label": "Plantation Area",
                "description": "Total area established with commercial tree species.",
                "unit": "hectares",
                "typical_range": {"min": 1000, "max": 50000},
                "example_value": 8000,
                "data_sources": ["Planting records", "GIS shapefiles", "Land title / concession"],
                "required": True,
                "tooltip": "Must show land was non-forest at baseline."
            },
            {
                "parameter": "species",
                "label": "Primary Species",
                "description": "Main commercial tree species planted.",
                "unit": "text",
                "typical_range": {"min": None, "max": None},
                "example_value": "Pinus patula",
                "data_sources": ["Planting plan", "Forest management plan"],
                "required": True,
                "tooltip": "Species drives growth rate and rotation length."
            },
            {
                "parameter": "rotation_years",
                "label": "Rotation Period",
                "description": "Planned harvest cycle in years.",
                "unit": "years",
                "typical_range": {"min": 7, "max": 40},
                "example_value": 20,
                "data_sources": ["Forest management plan", "Financial model"],
                "required": True,
                "tooltip": "Shorter rotation = faster growth but lower standing stock."
            },
            {
                "parameter": "mean_annual_increment",
                "label": "Mean Annual Increment",
                "description": "Average annual volume growth per hectare.",
                "unit": "m3/ha/year",
                "typical_range": {"min": 5, "max": 40},
                "example_value": 18,
                "data_sources": ["Yield tables", "Sample plot measurements"],
                "required": True,
                "tooltip": "Site index dependent; use local yield models."
            }
        ],
        "real_world_examples": [
            {"project": "Green Resources Plantation, Tanzania", "credits": 90000, "year": 2023}
        ],
        "regulatory_notes": "Eligible under CDM (AR), VCS. Must account for carbon loss at harvest; tCER/lCER for CDM.",
        "cdm_tools_needed": ["TOOL14", "TOOL15"],
        "estimated_cost_range_usd": {"min": 5000000, "max": 50000000},
        "crediting_period_years": {"min": 20, "max": 60}
    },

    "mangrove_restoration": {
        "id": "mangrove_restoration",
        "name": "Mangrove Ecosystem Restoration",
        "description": "Restoration and rehabilitation of degraded mangrove ecosystems, sequestering carbon in biomass and sediment (blue carbon).",
        "sector": "Forestry",
        "user_types": ["Conservation NGO", "Government", "Community Group", "Blue Carbon Developer"],
        "value_chain_position": "core",
        "applicable_methodologies": ["VM0033", "AR-ACM0003", "Plan Vivo"],
        "recommended_methodology": "VM0033",
        "scale": "Small",
        "typical_credit_range": {"min": 2000, "max": 80000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "restoration_area_ha",
                "label": "Restoration Area",
                "description": "Total area of mangrove habitat restored.",
                "unit": "hectares",
                "typical_range": {"min": 100, "max": 10000},
                "example_value": 1500,
                "data_sources": ["Satellite imagery", "GIS mapping", "Coastal zone management plan"],
                "required": True,
                "tooltip": "Includes planting zones and natural regeneration zones."
            },
            {
                "parameter": "carbon_seq_rate",
                "label": "Carbon Sequestration Rate",
                "description": "Annual CO2 sequestered per hectare in biomass and soil.",
                "unit": "tCO2e/ha/year",
                "typical_range": {"min": 5, "max": 30},
                "example_value": 12,
                "data_sources": ["Published mangrove allometric models", "Soil core samples", "Blue carbon literature"],
                "required": True,
                "tooltip": "Mangroves sequester 3-5x more carbon per ha than terrestrial forests."
            },
            {
                "parameter": "soil_carbon_depth_cm",
                "label": "Soil Carbon Accounting Depth",
                "description": "Depth to which soil organic carbon is measured.",
                "unit": "cm",
                "typical_range": {"min": 30, "max": 100},
                "example_value": 60,
                "data_sources": ["VCS blue carbon guidance", "Soil sampling protocol"],
                "required": True,
                "tooltip": "Deeper sampling captures more sediment carbon."
            }
        ],
        "real_world_examples": [
            {"project": "Mikoko Pamoja, Gazi Bay Kenya", "credits": 3000, "year": 2023},
            {"project": "Delta Blue Carbon, Sindh Pakistan", "credits": 60000, "year": 2022}
        ],
        "regulatory_notes": "VCS (VM0033) is primary standard for blue carbon. Community co-benefits often certified under CCB standard.",
        "cdm_tools_needed": ["TOOL14"],
        "estimated_cost_range_usd": {"min": 500000, "max": 10000000},
        "crediting_period_years": {"min": 20, "max": 40}
    },

    "seagrass_restoration": {
        "id": "seagrass_restoration",
        "name": "Seagrass Meadow Restoration",
        "description": "Restoration of degraded seagrass beds to sequester carbon in marine sediments and biomass (blue carbon).",
        "sector": "Forestry",
        "user_types": ["Conservation NGO", "Government", "Research Institute", "Blue Carbon Developer"],
        "value_chain_position": "core",
        "applicable_methodologies": ["VM0033", "Plan Vivo"],
        "recommended_methodology": "VM0033",
        "scale": "Small",
        "typical_credit_range": {"min": 500, "max": 20000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "restoration_area_ha",
                "label": "Restoration Area",
                "description": "Total area of seagrass meadow restored.",
                "unit": "hectares",
                "typical_range": {"min": 50, "max": 5000},
                "example_value": 500,
                "data_sources": ["Marine survey", "GIS mapping", "Baseline seagrass coverage assessment"],
                "required": True,
                "tooltip": "Delineated by underwater survey and satellite imagery."
            },
            {
                "parameter": "carbon_seq_rate",
                "label": "Carbon Sequestration Rate",
                "description": "Annual CO2 sequestered per hectare.",
                "unit": "tCO2e/ha/year",
                "typical_range": {"min": 2, "max": 15},
                "example_value": 6,
                "data_sources": ["Published seagrass carbon studies", "Sediment core analysis"],
                "required": True,
                "tooltip": "Varies by species (Posidonia > Zostera)."
            },
            {
                "parameter": "species",
                "label": "Seagrass Species",
                "description": "Dominant seagrass species in the restoration area.",
                "unit": "text",
                "typical_range": {"min": None, "max": None},
                "example_value": "Posidonia oceanica",
                "data_sources": ["Marine ecology survey", "Restoration plan"],
                "required": True,
                "tooltip": "Species determines growth rate and carbon density."
            }
        ],
        "real_world_examples": [
            {"project": "Virginia Coast Seagrass Restoration, USA", "credits": 2500, "year": 2023}
        ],
        "regulatory_notes": "VCS (VM0033) covers tidal wetlands and seagrass. Emerging methodology; fewer registered projects.",
        "cdm_tools_needed": [],
        "estimated_cost_range_usd": {"min": 500000, "max": 5000000},
        "crediting_period_years": {"min": 20, "max": 40}
    },

    "peatland_rewetting": {
        "id": "peatland_rewetting",
        "name": "Peatland Rewetting and Conservation",
        "description": "Raising the water table of drained peatlands to halt oxidation of peat carbon and reduce GHG emissions.",
        "sector": "Forestry",
        "user_types": ["Conservation NGO", "Government", "Landowner"],
        "value_chain_position": "core",
        "applicable_methodologies": ["VM0036", "VCS Peatland Rewetting"],
        "recommended_methodology": "VM0036",
        "scale": "Large",
        "typical_credit_range": {"min": 10000, "max": 500000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "project_area_ha",
                "label": "Peatland Area",
                "description": "Total area of peatland under rewetting management.",
                "unit": "hectares",
                "typical_range": {"min": 500, "max": 100000},
                "example_value": 15000,
                "data_sources": ["Land title", "GIS mapping", "Peat depth survey"],
                "required": True,
                "tooltip": "Area where water table is being raised."
            },
            {
                "parameter": "peat_depth_m",
                "label": "Average Peat Depth",
                "description": "Mean depth of the peat layer.",
                "unit": "m",
                "typical_range": {"min": 0.5, "max": 15},
                "example_value": 4,
                "data_sources": ["Peat depth surveys (Dutch auger)", "Geological maps"],
                "required": True,
                "tooltip": "Deeper peat = larger stored carbon pool at risk."
            },
            {
                "parameter": "baseline_water_table_depth_cm",
                "label": "Baseline Water Table Depth",
                "description": "Average depth below surface of the water table before rewetting.",
                "unit": "cm below surface",
                "typical_range": {"min": 30, "max": 120},
                "example_value": 60,
                "data_sources": ["Piezometer monitoring records", "Drainage canal survey"],
                "required": True,
                "tooltip": "Deeper water table = higher baseline oxidation emissions."
            },
            {
                "parameter": "emission_factor_co2",
                "label": "CO2 Emission Factor for Drained Peat",
                "description": "Annual CO2 emissions per hectare from oxidation of drained peat.",
                "unit": "tCO2/ha/year",
                "typical_range": {"min": 10, "max": 90},
                "example_value": 40,
                "data_sources": ["IPCC Wetlands Supplement", "National peatland GHG inventory"],
                "required": True,
                "tooltip": "Tropical peatlands emit more than temperate (40-90 vs 10-30 tCO2/ha/yr)."
            }
        ],
        "real_world_examples": [
            {"project": "Katingan Peatland, Central Kalimantan", "credits": 700000, "year": 2023}
        ],
        "regulatory_notes": "VCS is the primary standard. Permanence buffer pool required. IPCC Wetlands Supplement provides emission factors.",
        "cdm_tools_needed": [],
        "estimated_cost_range_usd": {"min": 3000000, "max": 25000000},
        "crediting_period_years": {"min": 20, "max": 40}
    },

    "agroforestry_shade": {
        "id": "agroforestry_shade",
        "name": "Shade-Grown Agroforestry",
        "description": "Integration of trees into agricultural landscapes (e.g., shade coffee, cocoa agroforestry) to sequester carbon while maintaining crop production.",
        "sector": "Forestry",
        "user_types": ["Smallholder Farmer", "Cooperative", "NGO", "Project Developer"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AR-AMS0007", "VM0047", "Plan Vivo"],
        "recommended_methodology": "VM0047",
        "scale": "Small",
        "typical_credit_range": {"min": 2000, "max": 50000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "agroforestry_area_ha",
                "label": "Agroforestry Area",
                "description": "Total land area under agroforestry management.",
                "unit": "hectares",
                "typical_range": {"min": 500, "max": 50000},
                "example_value": 5000,
                "data_sources": ["Farm boundary surveys", "Cooperative membership records", "GIS mapping"],
                "required": True,
                "tooltip": "Sum of all participating farms."
            },
            {
                "parameter": "trees_per_ha",
                "label": "Tree Density",
                "description": "Average number of shade trees planted per hectare.",
                "unit": "trees/ha",
                "typical_range": {"min": 50, "max": 400},
                "example_value": 150,
                "data_sources": ["Planting records", "Field sampling", "Monitoring plots"],
                "required": True,
                "tooltip": "Varies by crop system; shade coffee typically 100-250/ha."
            },
            {
                "parameter": "species_mix",
                "label": "Tree Species Mix",
                "description": "Primary shade and timber tree species.",
                "unit": "text",
                "typical_range": {"min": None, "max": None},
                "example_value": "Inga sp. 50%, Grevillea robusta 30%, Cordia alliodora 20%",
                "data_sources": ["Planting plan", "Nursery records"],
                "required": True,
                "tooltip": "Nitrogen-fixing species (Inga) are preferred for soil improvement."
            }
        ],
        "real_world_examples": [
            {"project": "Trees for Global Benefits, Uganda", "credits": 25000, "year": 2023}
        ],
        "regulatory_notes": "Eligible under VCS, Plan Vivo, Gold Standard. Often combined with fair-trade or organic certification.",
        "cdm_tools_needed": ["TOOL14"],
        "estimated_cost_range_usd": {"min": 500000, "max": 10000000},
        "crediting_period_years": {"min": 20, "max": 40}
    },

    # ======================================================================
    # AGRICULTURE  (#32 - #37)
    # ======================================================================

    "manure_digester_pig": {
        "id": "manure_digester_pig",
        "name": "Pig Farm Manure Digester",
        "description": "Installation of covered anaerobic digesters on pig farms to capture methane from manure that would otherwise decompose in open lagoons.",
        "sector": "Agriculture",
        "user_types": ["Livestock Farmer", "Agribusiness", "Project Developer"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-III.D", "ACM0010"],
        "recommended_methodology": "AMS-III.D",
        "scale": "Small",
        "typical_credit_range": {"min": 3000, "max": 40000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "number_of_pigs",
                "label": "Average Annual Pig Population",
                "description": "Average number of pigs on the farm per year.",
                "unit": "head",
                "typical_range": {"min": 1000, "max": 100000},
                "example_value": 20000,
                "data_sources": ["Farm herd records", "Veterinary records", "Slaughter manifests"],
                "required": True,
                "tooltip": "Use average annual population, not peak."
            },
            {
                "parameter": "volatile_solids_kg_head_day",
                "label": "Volatile Solids Excretion Rate",
                "description": "Daily volatile solids excreted per pig.",
                "unit": "kg VS/head/day",
                "typical_range": {"min": 0.3, "max": 0.6},
                "example_value": 0.45,
                "data_sources": ["IPCC default values", "National livestock emission factors", "Lab manure analysis"],
                "required": True,
                "tooltip": "Depends on pig weight class and feed composition."
            },
            {
                "parameter": "methane_conversion_factor",
                "label": "Methane Conversion Factor (MCF)",
                "description": "Fraction of maximum methane potential achieved in the baseline system.",
                "unit": "fraction",
                "typical_range": {"min": 0.3, "max": 0.8},
                "example_value": 0.65,
                "data_sources": ["IPCC Guidelines Ch 10", "National GHG inventory"],
                "required": True,
                "tooltip": "Depends on climate zone and manure management (lagoon vs pit)."
            },
            {
                "parameter": "methane_captured_m3_yr",
                "label": "Annual Methane Captured",
                "description": "Volume of methane captured by the digester per year.",
                "unit": "m3 CH4/year",
                "typical_range": {"min": 100000, "max": 3000000},
                "example_value": 800000,
                "data_sources": ["Gas flow meter readings", "Digester monitoring data"],
                "required": True,
                "tooltip": "Measured with calibrated flow meter; used for credit calculation."
            }
        ],
        "real_world_examples": [
            {"project": "AgCert Pig Farm Digesters, Brazil", "credits": 28000, "year": 2023}
        ],
        "regulatory_notes": "Eligible under CDM, VCS, Gold Standard. Can be bundled across multiple farms as a PoA.",
        "cdm_tools_needed": ["TOOL01", "TOOL04"],
        "estimated_cost_range_usd": {"min": 200000, "max": 3000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    "dairy_methane": {
        "id": "dairy_methane",
        "name": "Dairy Farm Methane Capture",
        "description": "Capture of methane from dairy cattle manure management systems using covered lagoons or digesters.",
        "sector": "Agriculture",
        "user_types": ["Livestock Farmer", "Dairy Cooperative", "Project Developer"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-III.D", "ACM0010"],
        "recommended_methodology": "AMS-III.D",
        "scale": "Small",
        "typical_credit_range": {"min": 2000, "max": 30000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "number_of_cows",
                "label": "Average Dairy Herd Size",
                "description": "Average number of milking cows over the year.",
                "unit": "head",
                "typical_range": {"min": 200, "max": 20000},
                "example_value": 3000,
                "data_sources": ["Farm herd records", "Dairy cooperative records", "Milk collection data"],
                "required": True,
                "tooltip": "Include dry cows but exclude calves and heifers."
            },
            {
                "parameter": "volatile_solids_kg_head_day",
                "label": "Volatile Solids Excretion",
                "description": "Daily VS excretion per cow.",
                "unit": "kg VS/head/day",
                "typical_range": {"min": 3.0, "max": 6.0},
                "example_value": 4.5,
                "data_sources": ["IPCC defaults", "National livestock emission factors"],
                "required": True,
                "tooltip": "Higher for high-yield dairy breeds."
            },
            {
                "parameter": "baseline_manure_system",
                "label": "Baseline Manure System",
                "description": "How manure was managed before the project.",
                "unit": "text",
                "typical_range": {"min": None, "max": None},
                "example_value": "Open anaerobic lagoon",
                "data_sources": ["Pre-project site assessment", "Farm management records"],
                "required": True,
                "tooltip": "Open lagoons have high MCF; dry lot/pasture have low MCF."
            }
        ],
        "real_world_examples": [
            {"project": "Fair Oaks Dairy Digester, Indiana USA", "credits": 18000, "year": 2023}
        ],
        "regulatory_notes": "Eligible under CDM, VCS, ACR (US livestock protocol). High GWP of methane (28x CO2) makes these projects impactful.",
        "cdm_tools_needed": ["TOOL01", "TOOL04"],
        "estimated_cost_range_usd": {"min": 500000, "max": 5000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    "rice_awd": {
        "id": "rice_awd",
        "name": "Alternate Wetting and Drying (AWD) in Rice",
        "description": "Modified rice paddy water management that periodically drains fields during the growing season, reducing anaerobic methane emissions.",
        "sector": "Agriculture",
        "user_types": ["Smallholder Farmer", "Rice Mill", "Cooperative", "Project Developer"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-III.AU", "Verra Rice Protocol"],
        "recommended_methodology": "AMS-III.AU",
        "scale": "Small",
        "typical_credit_range": {"min": 1000, "max": 50000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "paddy_area_ha",
                "label": "Rice Paddy Area",
                "description": "Total area of rice paddies under AWD management.",
                "unit": "hectares",
                "typical_range": {"min": 500, "max": 100000},
                "example_value": 10000,
                "data_sources": ["Farm surveys", "Cooperative membership data", "Satellite imagery"],
                "required": True,
                "tooltip": "Sum of all participating farms."
            },
            {
                "parameter": "baseline_ef_kg_ch4_ha",
                "label": "Baseline Methane Emission Factor",
                "description": "Methane emissions per hectare under continuous flooding.",
                "unit": "kg CH4/ha/season",
                "typical_range": {"min": 100, "max": 400},
                "example_value": 200,
                "data_sources": ["IPCC Tier 1 defaults", "National rice emission inventory", "Field measurement campaigns"],
                "required": True,
                "tooltip": "Varies by climate, soil type, rice variety, and organic amendment."
            },
            {
                "parameter": "project_ef_kg_ch4_ha",
                "label": "Project AWD Emission Factor",
                "description": "Methane emissions per hectare under AWD management.",
                "unit": "kg CH4/ha/season",
                "typical_range": {"min": 50, "max": 250},
                "example_value": 100,
                "data_sources": ["Field measurements", "IPCC scaling factors for AWD", "Research publications"],
                "required": True,
                "tooltip": "AWD typically reduces CH4 by 30-50% vs continuous flooding."
            },
            {
                "parameter": "number_of_seasons",
                "label": "Rice Growing Seasons per Year",
                "description": "Number of rice crops grown per year.",
                "unit": "count",
                "typical_range": {"min": 1, "max": 3},
                "example_value": 2,
                "data_sources": ["Agricultural calendar", "Farm survey"],
                "required": True,
                "tooltip": "Tropical regions may have 2-3 seasons per year."
            }
        ],
        "real_world_examples": [
            {"project": "Sustainable Rice Platform, Vietnam", "credits": 35000, "year": 2023}
        ],
        "regulatory_notes": "Emerging methodology. VCS and Gold Standard both accept. Requires farmer training and MRV system.",
        "cdm_tools_needed": ["TOOL01"],
        "estimated_cost_range_usd": {"min": 500000, "max": 5000000},
        "crediting_period_years": {"min": 7, "max": 14}
    },

    "soil_carbon_notill": {
        "id": "soil_carbon_notill",
        "name": "Soil Carbon Sequestration via No-Till Agriculture",
        "description": "Adoption of conservation tillage or no-till farming practices to increase soil organic carbon stocks.",
        "sector": "Agriculture",
        "user_types": ["Farmer", "Agribusiness", "Cooperative"],
        "value_chain_position": "core",
        "applicable_methodologies": ["VM0042", "VM0021"],
        "recommended_methodology": "VM0042",
        "scale": "Small",
        "typical_credit_range": {"min": 1000, "max": 30000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "field_area_ha",
                "label": "Total Field Area under No-Till",
                "description": "Hectares converted from conventional till to no-till.",
                "unit": "hectares",
                "typical_range": {"min": 500, "max": 100000},
                "example_value": 15000,
                "data_sources": ["Farm management records", "GPS field boundaries", "Satellite tillage detection"],
                "required": True,
                "tooltip": "Must document conversion from conventional tillage."
            },
            {
                "parameter": "baseline_soc_t_ha",
                "label": "Baseline Soil Organic Carbon",
                "description": "SOC stock per hectare before practice change.",
                "unit": "tC/ha",
                "typical_range": {"min": 20, "max": 80},
                "example_value": 40,
                "data_sources": ["Baseline soil sampling campaign", "National soil database", "SoilGrids data"],
                "required": True,
                "tooltip": "Sampled to 30 cm depth; stratified by soil type."
            },
            {
                "parameter": "soc_accrual_rate",
                "label": "SOC Accrual Rate",
                "description": "Expected annual increase in soil organic carbon.",
                "unit": "tCO2e/ha/year",
                "typical_range": {"min": 0.3, "max": 2.0},
                "example_value": 0.8,
                "data_sources": ["Peer-reviewed literature", "IPCC stock change factors", "Field measurements"],
                "required": True,
                "tooltip": "Accrual is fastest in first 10 years and slows as new equilibrium approaches."
            }
        ],
        "real_world_examples": [
            {"project": "Indigo Ag Carbon Program, US Midwest", "credits": 20000, "year": 2023}
        ],
        "regulatory_notes": "VCS (VM0042), ACR, CAR protocols. Permanence and additionality scrutiny is high. Requires soil sampling MRV.",
        "cdm_tools_needed": [],
        "estimated_cost_range_usd": {"min": 200000, "max": 3000000},
        "crediting_period_years": {"min": 10, "max": 25}
    },

    "biochar_soil": {
        "id": "biochar_soil",
        "name": "Biochar Application to Agricultural Soils",
        "description": "Production of biochar from biomass pyrolysis and its application to agricultural soils as a stable carbon sink.",
        "sector": "Agriculture",
        "user_types": ["Farmer", "Biochar Producer", "Project Developer"],
        "value_chain_position": "core",
        "applicable_methodologies": ["Puro.earth Biochar", "VCS Biochar methodology"],
        "recommended_methodology": "Puro.earth Biochar",
        "scale": "Small",
        "typical_credit_range": {"min": 500, "max": 20000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "biochar_produced_tonnes_yr",
                "label": "Annual Biochar Production",
                "description": "Tonnes of biochar produced per year.",
                "unit": "tonnes/year",
                "typical_range": {"min": 100, "max": 10000},
                "example_value": 2000,
                "data_sources": ["Production scale records", "Pyrolysis plant logs"],
                "required": True,
                "tooltip": "Measured at kiln output; weighed before application."
            },
            {
                "parameter": "fixed_carbon_fraction",
                "label": "Fixed Carbon Content",
                "description": "Fraction of biochar mass that is stable (fixed) carbon.",
                "unit": "%",
                "typical_range": {"min": 50, "max": 90},
                "example_value": 75,
                "data_sources": ["Lab proximate analysis (ASTM D1762)", "IBI biochar certification"],
                "required": True,
                "tooltip": "Higher fixed carbon = more permanent carbon removal."
            },
            {
                "parameter": "feedstock_type",
                "label": "Biomass Feedstock",
                "description": "Type of biomass used to produce the biochar.",
                "unit": "text",
                "typical_range": {"min": None, "max": None},
                "example_value": "Rice husk",
                "data_sources": ["Feedstock supply agreement", "Procurement records"],
                "required": True,
                "tooltip": "Must be waste biomass to ensure no land-use impact."
            }
        ],
        "real_world_examples": [
            {"project": "Pacific Biochar, California", "credits": 5000, "year": 2023}
        ],
        "regulatory_notes": "Puro.earth and VCS accept biochar credits. Carbon removal category (CDR). Requires lab certification of fixed carbon.",
        "cdm_tools_needed": [],
        "estimated_cost_range_usd": {"min": 500000, "max": 10000000},
        "crediting_period_years": {"min": 10, "max": 30}
    },

    "n2o_fertilizer": {
        "id": "n2o_fertilizer",
        "name": "N2O Reduction through Improved Fertiliser Management",
        "description": "Reduction of nitrous oxide emissions from agricultural soils through precision fertiliser application, slow-release fertilisers, or nitrification inhibitors.",
        "sector": "Agriculture",
        "user_types": ["Farmer", "Agribusiness", "Fertiliser Company"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-III.BJ", "VM0022"],
        "recommended_methodology": "AMS-III.BJ",
        "scale": "Small",
        "typical_credit_range": {"min": 500, "max": 20000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "field_area_ha",
                "label": "Total Managed Area",
                "description": "Agricultural area under improved fertiliser practices.",
                "unit": "hectares",
                "typical_range": {"min": 1000, "max": 200000},
                "example_value": 30000,
                "data_sources": ["Farm surveys", "Fertiliser purchase records", "Cooperative membership data"],
                "required": True,
                "tooltip": "Sum of all participating farms."
            },
            {
                "parameter": "baseline_n_rate_kg_ha",
                "label": "Baseline Nitrogen Application Rate",
                "description": "Annual kg of synthetic N applied per hectare before improvement.",
                "unit": "kg N/ha/year",
                "typical_range": {"min": 80, "max": 300},
                "example_value": 180,
                "data_sources": ["Farm input records", "Fertiliser purchase invoices", "National average data"],
                "required": True,
                "tooltip": "Baseline must be documented from historical records."
            },
            {
                "parameter": "project_n_rate_kg_ha",
                "label": "Project Nitrogen Application Rate",
                "description": "Reduced N rate or equivalent N with inhibitors.",
                "unit": "kg N/ha/year",
                "typical_range": {"min": 50, "max": 200},
                "example_value": 120,
                "data_sources": ["Precision ag recommendations", "Soil testing lab results", "Farm input logs"],
                "required": True,
                "tooltip": "Must maintain crop yield while reducing N2O."
            },
            {
                "parameter": "n2o_emission_factor",
                "label": "N2O Emission Factor",
                "description": "Fraction of applied N emitted as N2O-N.",
                "unit": "%",
                "typical_range": {"min": 0.5, "max": 3.0},
                "example_value": 1.0,
                "data_sources": ["IPCC Tier 1 default (1%)", "National emission factor", "Field measurements"],
                "required": True,
                "tooltip": "IPCC default is 1% of applied N; varies by soil and climate."
            }
        ],
        "real_world_examples": [
            {"project": "Yara Climate-Smart Agriculture, Brazil", "credits": 12000, "year": 2023}
        ],
        "regulatory_notes": "Emerging methodology area. VCS, Gold Standard. Requires robust MRV for fertiliser use.",
        "cdm_tools_needed": ["TOOL01"],
        "estimated_cost_range_usd": {"min": 200000, "max": 2000000},
        "crediting_period_years": {"min": 7, "max": 14}
    },

    # ======================================================================
    # INDUSTRIAL  (#38 - #44)
    # ======================================================================

    "cement_blending": {
        "id": "cement_blending",
        "name": "Cement Clinker Substitution / Blending",
        "description": "Partial replacement of Portland cement clinker with supplementary cementitious materials (fly ash, slag, pozzolana) to reduce process CO2 emissions.",
        "sector": "Industrial",
        "user_types": ["Cement Manufacturer", "Construction Company"],
        "value_chain_position": "core",
        "applicable_methodologies": ["ACM0005", "AMS-III.B"],
        "recommended_methodology": "ACM0005",
        "scale": "Large",
        "typical_credit_range": {"min": 20000, "max": 300000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "cement_production_tonnes_yr",
                "label": "Annual Cement Production",
                "description": "Total tonnes of blended cement produced per year.",
                "unit": "tonnes/year",
                "typical_range": {"min": 100000, "max": 5000000},
                "example_value": 1000000,
                "data_sources": ["Production records", "Sales data", "Cement dispatch records"],
                "required": True,
                "tooltip": "All cement types that contain reduced clinker."
            },
            {
                "parameter": "clinker_ratio_baseline",
                "label": "Baseline Clinker-to-Cement Ratio",
                "description": "Fraction of clinker in cement before project.",
                "unit": "fraction",
                "typical_range": {"min": 0.85, "max": 0.95},
                "example_value": 0.90,
                "data_sources": ["Historical production records", "National average data"],
                "required": True,
                "tooltip": "OPC typically has 90-95% clinker."
            },
            {
                "parameter": "clinker_ratio_project",
                "label": "Project Clinker-to-Cement Ratio",
                "description": "Fraction of clinker in blended cement after project.",
                "unit": "fraction",
                "typical_range": {"min": 0.50, "max": 0.80},
                "example_value": 0.65,
                "data_sources": ["Quality control lab records", "Cement mill production logs"],
                "required": True,
                "tooltip": "Lower ratio = more emission reduction per tonne of cement."
            },
            {
                "parameter": "clinker_emission_factor",
                "label": "Clinker Emission Factor",
                "description": "CO2 emitted per tonne of clinker produced.",
                "unit": "tCO2/tonne clinker",
                "typical_range": {"min": 0.80, "max": 0.95},
                "example_value": 0.87,
                "data_sources": ["Kiln process data", "WBCSD Cement Sustainability Initiative", "IPCC default 0.87"],
                "required": True,
                "tooltip": "Includes calcination and fuel combustion in the kiln."
            }
        ],
        "real_world_examples": [
            {"project": "ACC Blended Cement, India", "credits": 180000, "year": 2023}
        ],
        "regulatory_notes": "Eligible under CDM (ACM0005), VCS. Must demonstrate that blended cement meets national quality standards.",
        "cdm_tools_needed": ["TOOL01", "TOOL07"],
        "estimated_cost_range_usd": {"min": 5000000, "max": 50000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    "n2o_nitric_acid": {
        "id": "n2o_nitric_acid",
        "name": "N2O Abatement from Nitric Acid Production",
        "description": "Installation of secondary or tertiary N2O abatement catalysts in nitric acid plants to destroy N2O in the tail gas.",
        "sector": "Industrial",
        "user_types": ["Chemical Manufacturer", "Fertiliser Company"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AM0028", "AM0034"],
        "recommended_methodology": "AM0028",
        "scale": "Large",
        "typical_credit_range": {"min": 50000, "max": 500000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "hno3_production_tonnes_yr",
                "label": "Annual Nitric Acid Production",
                "description": "Tonnes of 100% HNO3 equivalent produced per year.",
                "unit": "tonnes/year",
                "typical_range": {"min": 100000, "max": 1500000},
                "example_value": 400000,
                "data_sources": ["Production records", "Flow meter data"],
                "required": True,
                "tooltip": "Normalised to 100% concentration."
            },
            {
                "parameter": "baseline_n2o_ef",
                "label": "Baseline N2O Emission Factor",
                "description": "N2O emitted per tonne of HNO3 before abatement.",
                "unit": "kg N2O/tonne HNO3",
                "typical_range": {"min": 5, "max": 12},
                "example_value": 8,
                "data_sources": ["Pre-project continuous emissions monitoring (CEMS)", "Campaign measurement"],
                "required": True,
                "tooltip": "Measured over minimum 6-month baseline period."
            },
            {
                "parameter": "project_n2o_ef",
                "label": "Project N2O Emission Factor",
                "description": "N2O emitted per tonne of HNO3 after abatement.",
                "unit": "kg N2O/tonne HNO3",
                "typical_range": {"min": 0.5, "max": 3.0},
                "example_value": 1.5,
                "data_sources": ["CEMS data (continuous)", "Stack testing"],
                "required": True,
                "tooltip": "Measured continuously; typically 80-90% reduction."
            }
        ],
        "real_world_examples": [
            {"project": "YARA Montoir N2O Abatement, France", "credits": 350000, "year": 2022}
        ],
        "regulatory_notes": "CDM (AM0028). N2O has GWP of 298. EU ETS now mandates abatement, reducing additionality in EU.",
        "cdm_tools_needed": ["TOOL01"],
        "estimated_cost_range_usd": {"min": 1000000, "max": 10000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    "sf6_replacement": {
        "id": "sf6_replacement",
        "name": "SF6 Replacement in Electrical Switchgear",
        "description": "Replacement of SF6 insulating gas in medium- and high-voltage switchgear with low-GWP alternatives.",
        "sector": "Industrial",
        "user_types": ["Utility", "Industrial Facility", "Switchgear Manufacturer"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-III.AB", "VCS Methodology"],
        "recommended_methodology": "AMS-III.AB",
        "scale": "Small",
        "typical_credit_range": {"min": 500, "max": 20000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "sf6_avoided_kg_yr",
                "label": "SF6 Emissions Avoided",
                "description": "Annual mass of SF6 that would have leaked from conventional equipment.",
                "unit": "kg SF6/year",
                "typical_range": {"min": 20, "max": 500},
                "example_value": 100,
                "data_sources": ["Equipment leak rate data", "SF6 inventory records", "Manufacturer leakage specs"],
                "required": True,
                "tooltip": "SF6 GWP = 23,500. Even small leaks are significant."
            },
            {
                "parameter": "number_of_units",
                "label": "Number of Switchgear Units Replaced",
                "description": "Count of SF6 units replaced with low-GWP alternatives.",
                "unit": "count",
                "typical_range": {"min": 10, "max": 1000},
                "example_value": 50,
                "data_sources": ["Asset register", "Procurement records", "Decommissioning log"],
                "required": True,
                "tooltip": "Each unit has a nameplate SF6 charge."
            },
            {
                "parameter": "alternative_gas_gwp",
                "label": "Alternative Gas GWP",
                "description": "Global Warming Potential of the replacement insulating gas.",
                "unit": "kgCO2e/kg",
                "typical_range": {"min": 0, "max": 2000},
                "example_value": 1,
                "data_sources": ["Gas manufacturer SDS", "IPCC AR5/AR6 GWP tables"],
                "required": True,
                "tooltip": "Dry air / vacuum = 0; fluoronitrile blends ~ 700; clean air = 0."
            }
        ],
        "real_world_examples": [
            {"project": "Schneider Electric SF6-Free Switchgear, Europe", "credits": 5000, "year": 2023}
        ],
        "regulatory_notes": "Emerging methodology area. EU F-Gas Regulation pushing phase-down. VCS and Gold Standard accept.",
        "cdm_tools_needed": ["TOOL01"],
        "estimated_cost_range_usd": {"min": 500000, "max": 10000000},
        "crediting_period_years": {"min": 7, "max": 14}
    },

    "industrial_ee": {
        "id": "industrial_ee",
        "name": "Industrial Energy Efficiency Improvement",
        "description": "Systematic energy efficiency upgrades in industrial facilities (motors, compressors, process heat, steam systems) reducing grid electricity and fossil fuel consumption.",
        "sector": "Industrial",
        "user_types": ["Industrial Facility", "ESCO", "Corporate"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-II.D", "AMS-II.C", "ACM0012"],
        "recommended_methodology": "AMS-II.D",
        "scale": "Small",
        "typical_credit_range": {"min": 2000, "max": 40000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "baseline_energy_mwh_yr",
                "label": "Baseline Energy Consumption",
                "description": "Annual energy consumed before efficiency upgrades.",
                "unit": "MWh/year",
                "typical_range": {"min": 5000, "max": 500000},
                "example_value": 50000,
                "data_sources": ["Utility bills", "Metered energy data", "Energy audit report"],
                "required": True,
                "tooltip": "Use 2-3 year average for stable baseline."
            },
            {
                "parameter": "project_energy_mwh_yr",
                "label": "Project Energy Consumption",
                "description": "Annual energy consumed after efficiency upgrades.",
                "unit": "MWh/year",
                "typical_range": {"min": 3000, "max": 400000},
                "example_value": 38000,
                "data_sources": ["Post-retrofit metered data", "M&V report per IPMVP"],
                "required": True,
                "tooltip": "Must be normalised for production output changes."
            },
            {
                "parameter": "grid_emission_factor",
                "label": "Grid Emission Factor",
                "description": "CO2 intensity of electricity saved.",
                "unit": "tCO2/MWh",
                "typical_range": {"min": 0.4, "max": 1.2},
                "example_value": 0.85,
                "data_sources": ["National grid authority", "IFI Harmonized Grid EF database"],
                "required": True,
                "tooltip": "Applied to electricity savings."
            }
        ],
        "real_world_examples": [
            {"project": "Tata Steel EE Programme, India", "credits": 32000, "year": 2023}
        ],
        "regulatory_notes": "Eligible under CDM, VCS, Gold Standard. M&V per IPMVP protocol required.",
        "cdm_tools_needed": ["TOOL01", "TOOL07"],
        "estimated_cost_range_usd": {"min": 500000, "max": 20000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    "hfc23_destruction": {
        "id": "hfc23_destruction",
        "name": "HFC-23 Destruction",
        "description": "Thermal destruction of HFC-23 by-product from HCFC-22 production. HFC-23 has an extremely high GWP.",
        "sector": "Industrial",
        "user_types": ["Chemical Manufacturer"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AM0001"],
        "recommended_methodology": "AM0001",
        "scale": "Large",
        "typical_credit_range": {"min": 100000, "max": 5000000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "hfc23_destroyed_tonnes_yr",
                "label": "Annual HFC-23 Destroyed",
                "description": "Mass of HFC-23 destroyed in thermal oxidiser per year.",
                "unit": "tonnes/year",
                "typical_range": {"min": 5, "max": 500},
                "example_value": 50,
                "data_sources": ["Gas flow meter (continuous)", "Thermal oxidiser logs", "Third-party verification"],
                "required": True,
                "tooltip": "HFC-23 GWP = 14,800. 1 tonne = 14,800 tCO2e."
            },
            {
                "parameter": "hcfc22_production_tonnes_yr",
                "label": "HCFC-22 Production",
                "description": "Annual production of HCFC-22 (source of HFC-23 by-product).",
                "unit": "tonnes/year",
                "typical_range": {"min": 5000, "max": 100000},
                "example_value": 25000,
                "data_sources": ["Production records", "Customs export data"],
                "required": True,
                "tooltip": "HFC-23 is generated at ~1.5-4% of HCFC-22 production."
            },
            {
                "parameter": "destruction_efficiency",
                "label": "Thermal Oxidiser Destruction Efficiency",
                "description": "Percentage of HFC-23 destroyed in the thermal oxidiser.",
                "unit": "%",
                "typical_range": {"min": 99.0, "max": 99.99},
                "example_value": 99.9,
                "data_sources": ["Stack emissions test", "Continuous monitoring system"],
                "required": True,
                "tooltip": "Must achieve >99% destruction per AM0001."
            }
        ],
        "real_world_examples": [
            {"project": "SRF HFC-23 Destruction, Rajasthan India", "credits": 2500000, "year": 2020}
        ],
        "regulatory_notes": "CDM AM0001. Historically controversial due to perverse incentive concerns. EU banned HFC-23 CERs. Limited future issuance.",
        "cdm_tools_needed": ["TOOL01"],
        "estimated_cost_range_usd": {"min": 2000000, "max": 10000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    "steel_waste_heat": {
        "id": "steel_waste_heat",
        "name": "Steel Plant Waste Heat Recovery",
        "description": "Recovery of waste heat from steel-making processes (blast furnace, coke oven, BOF gas) for power generation or process heating.",
        "sector": "Industrial",
        "user_types": ["Steel Manufacturer", "ESCO"],
        "value_chain_position": "core",
        "applicable_methodologies": ["ACM0012", "AMS-III.Q"],
        "recommended_methodology": "ACM0012",
        "scale": "Large",
        "typical_credit_range": {"min": 10000, "max": 150000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "heat_recovered_tj_yr",
                "label": "Annual Heat Recovered",
                "description": "Total thermal energy recovered from waste heat sources.",
                "unit": "TJ/year",
                "typical_range": {"min": 50, "max": 2000},
                "example_value": 500,
                "data_sources": ["Heat exchanger monitoring", "Energy balance calculation", "Process SCADA data"],
                "required": True,
                "tooltip": "Sum of all waste heat recovery units in the plant."
            },
            {
                "parameter": "electricity_generated_mwh_yr",
                "label": "Electricity Generated from Waste Heat",
                "description": "Net electricity produced from recovered waste heat.",
                "unit": "MWh/year",
                "typical_range": {"min": 20000, "max": 500000},
                "example_value": 120000,
                "data_sources": ["Generator meter readings", "Turbine performance data"],
                "required": True,
                "tooltip": "If heat is used for process, calculate fuel displacement instead."
            },
            {
                "parameter": "grid_emission_factor",
                "label": "Grid Emission Factor",
                "description": "CO2 intensity of displaced grid electricity.",
                "unit": "tCO2/MWh",
                "typical_range": {"min": 0.4, "max": 1.2},
                "example_value": 0.9,
                "data_sources": ["National grid authority", "IFI Harmonized Grid EF database"],
                "required": True,
                "tooltip": "Use combined margin per ACM0012."
            }
        ],
        "real_world_examples": [
            {"project": "JSW Steel WHR, Toranagallu India", "credits": 98000, "year": 2023}
        ],
        "regulatory_notes": "Eligible under CDM (ACM0012), VCS. Must prove heat was previously wasted, not already recovered.",
        "cdm_tools_needed": ["TOOL01", "TOOL07"],
        "estimated_cost_range_usd": {"min": 20000000, "max": 100000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    "coal_mine_methane": {
        "id": "coal_mine_methane",
        "name": "Coal Mine Methane Capture and Use",
        "description": "Capture of methane released during coal mining operations (pre-drainage and ventilation air methane) and its use or destruction.",
        "sector": "Industrial",
        "user_types": ["Mining Company", "Project Developer"],
        "value_chain_position": "core",
        "applicable_methodologies": ["ACM0008", "AMS-III.L"],
        "recommended_methodology": "ACM0008",
        "scale": "Large",
        "typical_credit_range": {"min": 30000, "max": 400000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "methane_captured_m3_yr",
                "label": "Annual Methane Captured",
                "description": "Total methane captured from coal seam drainage per year.",
                "unit": "m3 CH4/year",
                "typical_range": {"min": 5000000, "max": 200000000},
                "example_value": 40000000,
                "data_sources": ["Gas drainage system flow meters", "Mine ventilation monitoring", "Mine gas analysis"],
                "required": True,
                "tooltip": "Includes pre-drainage, gob wells, and VAM if captured."
            },
            {
                "parameter": "coal_production_tonnes_yr",
                "label": "Annual Coal Production",
                "description": "Raw coal extracted from the mine.",
                "unit": "tonnes/year",
                "typical_range": {"min": 500000, "max": 20000000},
                "example_value": 5000000,
                "data_sources": ["Mine production records", "Sales data"],
                "required": True,
                "tooltip": "Used to calculate specific emission rate per tonne of coal."
            },
            {
                "parameter": "utilisation_method",
                "label": "Methane Utilisation Method",
                "description": "How the captured methane is used (flare, power, pipeline injection).",
                "unit": "text",
                "typical_range": {"min": None, "max": None},
                "example_value": "Power generation",
                "data_sources": ["Project design document", "Off-take agreement"],
                "required": True,
                "tooltip": "Power generation adds grid displacement credits; flare-only gives CH4 destruction."
            }
        ],
        "real_world_examples": [
            {"project": "Jincheng Coal Mine Methane, Shanxi China", "credits": 280000, "year": 2022}
        ],
        "regulatory_notes": "Eligible under CDM (ACM0008), VCS. China has the largest number of registered CMM projects.",
        "cdm_tools_needed": ["TOOL01", "TOOL04"],
        "estimated_cost_range_usd": {"min": 10000000, "max": 80000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    # ======================================================================
    # TRANSPORT  (#45 - #49)
    # ======================================================================

    "electric_bus_fleet": {
        "id": "electric_bus_fleet",
        "name": "Electric Bus Fleet Deployment",
        "description": "Replacement of diesel or CNG city buses with battery-electric buses, reducing tailpipe emissions.",
        "sector": "Transport",
        "user_types": ["Municipal Transport Authority", "Bus Operator", "Corporate"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-III.C", "AM0031"],
        "recommended_methodology": "AMS-III.C",
        "scale": "Small",
        "typical_credit_range": {"min": 2000, "max": 30000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "number_of_buses",
                "label": "Number of Electric Buses",
                "description": "Total electric buses deployed in the fleet.",
                "unit": "count",
                "typical_range": {"min": 20, "max": 2000},
                "example_value": 200,
                "data_sources": ["Fleet register", "Procurement records", "Operator contracts"],
                "required": True,
                "tooltip": "Count of operational e-buses, not including reserve fleet."
            },
            {
                "parameter": "annual_km_per_bus",
                "label": "Annual Distance per Bus",
                "description": "Average kilometres each bus travels per year.",
                "unit": "km/year",
                "typical_range": {"min": 40000, "max": 100000},
                "example_value": 65000,
                "data_sources": ["GPS/telematics data", "Odometer readings", "Route planning system"],
                "required": True,
                "tooltip": "Operational km only; excludes dead-heading."
            },
            {
                "parameter": "baseline_diesel_ef",
                "label": "Baseline Diesel Emission Factor",
                "description": "CO2 per km for the diesel buses being replaced.",
                "unit": "kgCO2/km",
                "typical_range": {"min": 0.8, "max": 1.5},
                "example_value": 1.1,
                "data_sources": ["Historical fuel consumption records", "Fleet fuel receipts", "OEM fuel consumption specs"],
                "required": True,
                "tooltip": "Tank-to-wheel emissions of replaced diesel bus fleet."
            },
            {
                "parameter": "grid_emission_factor",
                "label": "Grid Emission Factor for Charging",
                "description": "CO2 intensity of electricity used to charge the e-buses.",
                "unit": "tCO2/MWh",
                "typical_range": {"min": 0.1, "max": 1.2},
                "example_value": 0.7,
                "data_sources": ["National grid authority", "Charger metered data"],
                "required": True,
                "tooltip": "Lower grid EF = higher net emission reduction."
            }
        ],
        "real_world_examples": [
            {"project": "Shenzhen Electric Bus Fleet, China", "credits": 25000, "year": 2023}
        ],
        "regulatory_notes": "Eligible under CDM, VCS, Gold Standard. Must account for upstream electricity emissions.",
        "cdm_tools_needed": ["TOOL01", "TOOL07"],
        "estimated_cost_range_usd": {"min": 20000000, "max": 500000000},
        "crediting_period_years": {"min": 7, "max": 14}
    },

    "brt_system": {
        "id": "brt_system",
        "name": "Bus Rapid Transit (BRT) System",
        "description": "Construction and operation of dedicated bus rapid transit corridors that shift passengers from private vehicles to high-capacity public transit.",
        "sector": "Transport",
        "user_types": ["Municipal Authority", "Transit Authority", "Project Developer"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AM0031", "AMS-III.U"],
        "recommended_methodology": "AM0031",
        "scale": "Large",
        "typical_credit_range": {"min": 20000, "max": 200000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "daily_ridership",
                "label": "Average Daily Ridership",
                "description": "Number of passenger trips per day on the BRT system.",
                "unit": "passengers/day",
                "typical_range": {"min": 50000, "max": 2000000},
                "example_value": 300000,
                "data_sources": ["AFC (automated fare collection) data", "Passenger count surveys", "Station entry records"],
                "required": True,
                "tooltip": "Linked passengers (boardings) per day."
            },
            {
                "parameter": "mode_shift_fraction",
                "label": "Mode Shift from Private Vehicles",
                "description": "Percentage of BRT riders who would have used a private car.",
                "unit": "%",
                "typical_range": {"min": 10, "max": 50},
                "example_value": 25,
                "data_sources": ["Before-after travel survey", "Household travel diary", "Mode choice model"],
                "required": True,
                "tooltip": "Only modal shift from higher-emission modes generates credits."
            },
            {
                "parameter": "corridor_length_km",
                "label": "BRT Corridor Length",
                "description": "Total length of dedicated BRT lanes.",
                "unit": "km",
                "typical_range": {"min": 5, "max": 100},
                "example_value": 25,
                "data_sources": ["Infrastructure design", "Route maps", "Construction records"],
                "required": True,
                "tooltip": "Longer corridors serve more trip-km displacement."
            }
        ],
        "real_world_examples": [
            {"project": "TransMilenio BRT, Bogota", "credits": 165000, "year": 2023}
        ],
        "regulatory_notes": "CDM (AM0031) is the primary methodology. Requires comprehensive travel surveys. First transport CDM was TransMilenio.",
        "cdm_tools_needed": ["TOOL01"],
        "estimated_cost_range_usd": {"min": 100000000, "max": 1000000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    "rail_freight_shift": {
        "id": "rail_freight_shift",
        "name": "Modal Shift: Road Freight to Rail",
        "description": "Shifting cargo transport from road trucks to electrified or diesel rail, reducing emissions per tonne-km.",
        "sector": "Transport",
        "user_types": ["Logistics Company", "Railway Operator", "Project Developer"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-III.C", "AM0090"],
        "recommended_methodology": "AMS-III.C",
        "scale": "Large",
        "typical_credit_range": {"min": 10000, "max": 100000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "tonne_km_shifted_yr",
                "label": "Annual Tonne-km Shifted to Rail",
                "description": "Total freight volume shifted from road to rail.",
                "unit": "tonne-km/year",
                "typical_range": {"min": 50000000, "max": 5000000000},
                "example_value": 500000000,
                "data_sources": ["Railway waybills", "Freight dispatch records", "Before-after freight survey"],
                "required": True,
                "tooltip": "Measured as weight multiplied by distance for shifted cargo."
            },
            {
                "parameter": "road_ef",
                "label": "Road Freight Emission Factor",
                "description": "CO2 per tonne-km for the truck transport being replaced.",
                "unit": "gCO2/tonne-km",
                "typical_range": {"min": 50, "max": 150},
                "example_value": 80,
                "data_sources": ["Truck fuel consumption data", "National freight emission factors", "GLEC Framework"],
                "required": True,
                "tooltip": "Varies by truck type, load factor, and road conditions."
            },
            {
                "parameter": "rail_ef",
                "label": "Rail Freight Emission Factor",
                "description": "CO2 per tonne-km for the rail transport.",
                "unit": "gCO2/tonne-km",
                "typical_range": {"min": 5, "max": 40},
                "example_value": 20,
                "data_sources": ["Railway energy data", "Grid EF (if electric)", "GLEC Framework"],
                "required": True,
                "tooltip": "Electric rail has much lower EF than diesel rail."
            }
        ],
        "real_world_examples": [
            {"project": "Dedicated Freight Corridor, India", "credits": 75000, "year": 2023}
        ],
        "regulatory_notes": "Eligible under CDM, VCS. Requires evidence of additionality (modal shift would not have occurred).",
        "cdm_tools_needed": ["TOOL01"],
        "estimated_cost_range_usd": {"min": 100000000, "max": 5000000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    "ev_fleet_corporate": {
        "id": "ev_fleet_corporate",
        "name": "Corporate Electric Vehicle Fleet",
        "description": "Transition of corporate vehicle fleet (cars, vans, light trucks) from internal combustion to battery electric vehicles.",
        "sector": "Transport",
        "user_types": ["Corporate", "Fleet Operator", "Logistics Company"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-III.C", "Gold Standard Transport"],
        "recommended_methodology": "AMS-III.C",
        "scale": "Small",
        "typical_credit_range": {"min": 500, "max": 10000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "number_of_evs",
                "label": "Number of EVs Deployed",
                "description": "Total battery-electric vehicles in the corporate fleet.",
                "unit": "count",
                "typical_range": {"min": 50, "max": 5000},
                "example_value": 300,
                "data_sources": ["Fleet register", "Lease/purchase records", "Vehicle registration data"],
                "required": True,
                "tooltip": "Only count BEVs, not hybrids."
            },
            {
                "parameter": "annual_km_per_vehicle",
                "label": "Annual Distance per Vehicle",
                "description": "Average annual kilometres driven per EV.",
                "unit": "km/year",
                "typical_range": {"min": 10000, "max": 60000},
                "example_value": 25000,
                "data_sources": ["Telematics data", "Odometer readings"],
                "required": True,
                "tooltip": "Operational distance only."
            },
            {
                "parameter": "baseline_ice_ef",
                "label": "Baseline ICE Vehicle Emission Factor",
                "description": "CO2 per km of the petrol/diesel vehicles being replaced.",
                "unit": "gCO2/km",
                "typical_range": {"min": 120, "max": 300},
                "example_value": 180,
                "data_sources": ["Fleet fuel records", "Manufacturer WLTP data", "National average"],
                "required": True,
                "tooltip": "Tank-to-wheel emissions of the replaced ICE vehicles."
            }
        ],
        "real_world_examples": [
            {"project": "Amazon Delivery Fleet EV, Europe", "credits": 8000, "year": 2023}
        ],
        "regulatory_notes": "Eligible under VCS, Gold Standard. Must account for grid emissions from EV charging.",
        "cdm_tools_needed": ["TOOL01"],
        "estimated_cost_range_usd": {"min": 2000000, "max": 50000000},
        "crediting_period_years": {"min": 7, "max": 14}
    },

    "bicycle_sharing": {
        "id": "bicycle_sharing",
        "name": "Public Bicycle Sharing System",
        "description": "City-wide bicycle sharing programme displacing motorised trips and reducing transport emissions.",
        "sector": "Transport",
        "user_types": ["Municipal Authority", "Transport Operator", "Social Enterprise"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-III.C", "Gold Standard Transport"],
        "recommended_methodology": "AMS-III.C",
        "scale": "Small",
        "typical_credit_range": {"min": 500, "max": 10000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "number_of_bikes",
                "label": "Fleet Size",
                "description": "Total number of bicycles in the sharing system.",
                "unit": "count",
                "typical_range": {"min": 500, "max": 50000},
                "example_value": 5000,
                "data_sources": ["Fleet management system", "Procurement records"],
                "required": True,
                "tooltip": "Include both station-based and dockless bikes."
            },
            {
                "parameter": "trips_per_day",
                "label": "Average Daily Trips",
                "description": "Total number of bike trips per day across the system.",
                "unit": "trips/day",
                "typical_range": {"min": 1000, "max": 200000},
                "example_value": 15000,
                "data_sources": ["Trip data from app/station sensors", "Booking system"],
                "required": True,
                "tooltip": "Measures system utilisation."
            },
            {
                "parameter": "mode_shift_fraction",
                "label": "Trips Displacing Motorised Travel",
                "description": "Percentage of bike trips that would have been by car, taxi, or motorbike.",
                "unit": "%",
                "typical_range": {"min": 10, "max": 40},
                "example_value": 20,
                "data_sources": ["User travel survey", "Before-after modal split study"],
                "required": True,
                "tooltip": "Only mode-shifted trips generate credits."
            }
        ],
        "real_world_examples": [
            {"project": "Medellin Bike Sharing, Colombia", "credits": 3000, "year": 2023}
        ],
        "regulatory_notes": "Gold Standard preferred. Requires robust user surveys to establish mode shift.",
        "cdm_tools_needed": ["TOOL01"],
        "estimated_cost_range_usd": {"min": 5000000, "max": 50000000},
        "crediting_period_years": {"min": 7, "max": 14}
    },

    # ======================================================================
    # BUILDINGS  (#50 - #55)
    # ======================================================================

    "led_retrofit_commercial": {
        "id": "led_retrofit_commercial",
        "name": "LED Lighting Retrofit - Commercial Buildings",
        "description": "Replacement of conventional fluorescent and halogen lighting with LED fixtures in commercial buildings.",
        "sector": "Buildings",
        "user_types": ["Building Owner", "ESCO", "Corporate"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-II.J", "AMS-II.C"],
        "recommended_methodology": "AMS-II.J",
        "scale": "Small",
        "typical_credit_range": {"min": 500, "max": 10000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "number_of_fixtures",
                "label": "Number of Fixtures Replaced",
                "description": "Total lighting fixtures upgraded to LED.",
                "unit": "count",
                "typical_range": {"min": 500, "max": 100000},
                "example_value": 10000,
                "data_sources": ["Lighting audit report", "Retrofit contractor records", "As-built drawings"],
                "required": True,
                "tooltip": "Count of replaced fixtures, not lamps."
            },
            {
                "parameter": "baseline_wattage_avg",
                "label": "Average Baseline Fixture Wattage",
                "description": "Average wattage of removed lighting fixtures.",
                "unit": "W",
                "typical_range": {"min": 40, "max": 250},
                "example_value": 72,
                "data_sources": ["Pre-retrofit lighting audit", "Fixture spec sheets"],
                "required": True,
                "tooltip": "Include ballast losses for fluorescent fixtures."
            },
            {
                "parameter": "led_wattage_avg",
                "label": "Average LED Fixture Wattage",
                "description": "Average wattage of the replacement LED fixtures.",
                "unit": "W",
                "typical_range": {"min": 10, "max": 100},
                "example_value": 30,
                "data_sources": ["LED product datasheets", "Installation records"],
                "required": True,
                "tooltip": "Must provide equivalent or better lux output."
            },
            {
                "parameter": "operating_hours_yr",
                "label": "Annual Operating Hours",
                "description": "Average hours per year the lighting operates.",
                "unit": "hours/year",
                "typical_range": {"min": 2000, "max": 8760},
                "example_value": 4000,
                "data_sources": ["BMS lighting schedule", "Occupancy sensor data", "Building operating hours"],
                "required": True,
                "tooltip": "Measured from building management system or survey."
            }
        ],
        "real_world_examples": [
            {"project": "Infosys Campus LED Retrofit, Bangalore", "credits": 3500, "year": 2023}
        ],
        "regulatory_notes": "Eligible under CDM, VCS, Gold Standard. Can be bundled as PoA. M&V per IPMVP Option A or B.",
        "cdm_tools_needed": ["TOOL01", "TOOL07"],
        "estimated_cost_range_usd": {"min": 100000, "max": 5000000},
        "crediting_period_years": {"min": 7, "max": 14}
    },

    "led_streetlighting": {
        "id": "led_streetlighting",
        "name": "LED Street Lighting Upgrade",
        "description": "Replacement of conventional HPS or mercury vapour street lights with LED luminaires.",
        "sector": "Buildings",
        "user_types": ["Municipal Authority", "ESCO", "Utility"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-II.J", "AMS-II.L"],
        "recommended_methodology": "AMS-II.J",
        "scale": "Small",
        "typical_credit_range": {"min": 1000, "max": 20000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "number_of_luminaires",
                "label": "Number of Street Lights Replaced",
                "description": "Total luminaires upgraded to LED.",
                "unit": "count",
                "typical_range": {"min": 1000, "max": 500000},
                "example_value": 50000,
                "data_sources": ["Municipal asset register", "GIS street light database", "Retrofit contractor records"],
                "required": True,
                "tooltip": "Count of individual luminaire heads."
            },
            {
                "parameter": "baseline_wattage",
                "label": "Average Baseline Luminaire Wattage",
                "description": "Average wattage of removed HPS/mercury lamps including ballast.",
                "unit": "W",
                "typical_range": {"min": 100, "max": 400},
                "example_value": 150,
                "data_sources": ["Pre-retrofit audit", "Lamp specification records"],
                "required": True,
                "tooltip": "HPS 150W with ballast draws ~170W total."
            },
            {
                "parameter": "led_wattage",
                "label": "Average LED Wattage",
                "description": "Average wattage of replacement LED luminaires.",
                "unit": "W",
                "typical_range": {"min": 30, "max": 150},
                "example_value": 60,
                "data_sources": ["LED product datasheets", "Installation records"],
                "required": True,
                "tooltip": "Must maintain minimum road lighting standards (e.g., EN 13201)."
            }
        ],
        "real_world_examples": [
            {"project": "Kolkata Street Lighting ESCO, India", "credits": 15000, "year": 2023}
        ],
        "regulatory_notes": "Eligible under CDM, VCS, Gold Standard. Municipalities often implement as ESCO contracts.",
        "cdm_tools_needed": ["TOOL01", "TOOL07"],
        "estimated_cost_range_usd": {"min": 5000000, "max": 100000000},
        "crediting_period_years": {"min": 7, "max": 14}
    },

    "hvac_upgrade": {
        "id": "hvac_upgrade",
        "name": "HVAC System Efficiency Upgrade",
        "description": "Replacement or upgrade of commercial building HVAC systems with high-efficiency chillers, heat pumps, or controls.",
        "sector": "Buildings",
        "user_types": ["Building Owner", "ESCO", "Corporate"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-II.C", "AMS-II.N"],
        "recommended_methodology": "AMS-II.C",
        "scale": "Small",
        "typical_credit_range": {"min": 500, "max": 15000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "baseline_cooling_kwh_yr",
                "label": "Baseline Annual Cooling Energy",
                "description": "Electricity consumed by existing HVAC for cooling per year.",
                "unit": "kWh/year",
                "typical_range": {"min": 200000, "max": 10000000},
                "example_value": 2000000,
                "data_sources": ["Utility sub-metering", "BMS logs", "Energy audit report"],
                "required": True,
                "tooltip": "Metered electricity for chillers, AHUs, and associated pumps/fans."
            },
            {
                "parameter": "project_cooling_kwh_yr",
                "label": "Project Annual Cooling Energy",
                "description": "Reduced electricity for cooling after HVAC upgrade.",
                "unit": "kWh/year",
                "typical_range": {"min": 100000, "max": 7000000},
                "example_value": 1300000,
                "data_sources": ["Post-retrofit sub-metering", "BMS logs", "M&V report"],
                "required": True,
                "tooltip": "Normalised for weather and occupancy differences."
            },
            {
                "parameter": "grid_emission_factor",
                "label": "Grid Emission Factor",
                "description": "CO2 intensity of electricity saved.",
                "unit": "tCO2/MWh",
                "typical_range": {"min": 0.4, "max": 1.2},
                "example_value": 0.85,
                "data_sources": ["National grid authority", "IFI Harmonized Grid EF database"],
                "required": True,
                "tooltip": "Applied to electricity savings."
            }
        ],
        "real_world_examples": [
            {"project": "ITC Hotels Chiller Upgrade, India", "credits": 5000, "year": 2023}
        ],
        "regulatory_notes": "Eligible under CDM, VCS, Gold Standard. M&V per IPMVP Option C or D.",
        "cdm_tools_needed": ["TOOL01", "TOOL07"],
        "estimated_cost_range_usd": {"min": 500000, "max": 10000000},
        "crediting_period_years": {"min": 7, "max": 14}
    },

    "cookstove_improved": {
        "id": "cookstove_improved",
        "name": "Improved Cookstove Distribution",
        "description": "Distribution of fuel-efficient cookstoves to households reliant on traditional biomass cooking, reducing fuelwood use and indoor air pollution.",
        "sector": "Buildings",
        "user_types": ["Social Enterprise", "NGO", "Cookstove Manufacturer"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-II.G", "Gold Standard Metered Cookstove"],
        "recommended_methodology": "AMS-II.G",
        "scale": "Small",
        "typical_credit_range": {"min": 5000, "max": 100000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "number_of_stoves",
                "label": "Number of Stoves Distributed",
                "description": "Total improved cookstoves distributed and in use.",
                "unit": "count",
                "typical_range": {"min": 5000, "max": 500000},
                "example_value": 50000,
                "data_sources": ["Distribution records", "Sales data", "Usage monitoring (sensors / surveys)"],
                "required": True,
                "tooltip": "Must demonstrate continued usage, not just distribution."
            },
            {
                "parameter": "fuelwood_saved_kg_yr",
                "label": "Fuelwood Saved per Stove per Year",
                "description": "Annual reduction in fuelwood use per household.",
                "unit": "kg/year",
                "typical_range": {"min": 500, "max": 3000},
                "example_value": 1200,
                "data_sources": ["Water boiling test (WBT)", "Kitchen performance test (KPT)", "Controlled cooking test (CCT)"],
                "required": True,
                "tooltip": "Gold Standard requires KPT for in-field fuel savings."
            },
            {
                "parameter": "fraction_non_renewable_biomass",
                "label": "Fraction of Non-Renewable Biomass (fNRB)",
                "description": "Share of fuelwood harvested unsustainably.",
                "unit": "fraction",
                "typical_range": {"min": 0.3, "max": 0.95},
                "example_value": 0.72,
                "data_sources": ["CDM fNRB tool", "National forestry data", "Published country studies"],
                "required": True,
                "tooltip": "Only non-renewable fraction counts toward emission reductions."
            }
        ],
        "real_world_examples": [
            {"project": "Burn Manufacturing Cookstoves, Kenya", "credits": 80000, "year": 2023},
            {"project": "Envirofit India Cookstove PoA", "credits": 45000, "year": 2022}
        ],
        "regulatory_notes": "Gold Standard is primary standard. CDM (AMS-II.G) also used. Must comply with ISO 19867 for stove testing.",
        "cdm_tools_needed": ["TOOL01", "TOOL30"],
        "estimated_cost_range_usd": {"min": 1000000, "max": 20000000},
        "crediting_period_years": {"min": 5, "max": 10}
    },

    "solar_water_heater": {
        "id": "solar_water_heater",
        "name": "Solar Water Heater Programme",
        "description": "Distribution and installation of solar thermal water heaters displacing electric geysers or gas boilers for domestic hot water.",
        "sector": "Buildings",
        "user_types": ["Household", "Housing Developer", "ESCO", "Utility"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-I.J", "AMS-I.C"],
        "recommended_methodology": "AMS-I.J",
        "scale": "Small",
        "typical_credit_range": {"min": 1000, "max": 30000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "number_of_systems",
                "label": "Number of SWH Systems Installed",
                "description": "Total solar water heater systems deployed.",
                "unit": "count",
                "typical_range": {"min": 500, "max": 100000},
                "example_value": 20000,
                "data_sources": ["Installation records", "Rebate programme database", "Sales records"],
                "required": True,
                "tooltip": "Count of installed systems, verified by inspections."
            },
            {
                "parameter": "collector_area_m2",
                "label": "Average Collector Area per System",
                "description": "Solar thermal collector area per installation.",
                "unit": "m2",
                "typical_range": {"min": 2, "max": 10},
                "example_value": 4,
                "data_sources": ["Product specification", "Installation records"],
                "required": True,
                "tooltip": "Determines thermal energy output."
            },
            {
                "parameter": "annual_energy_saved_kwh",
                "label": "Annual Energy Saved per System",
                "description": "Electricity or gas saved per SWH per year.",
                "unit": "kWh/year",
                "typical_range": {"min": 1000, "max": 4000},
                "example_value": 2200,
                "data_sources": ["Metered data", "Solar resource data", "Engineering calculations"],
                "required": True,
                "tooltip": "Depends on solar irradiance, system size, and hot water demand."
            }
        ],
        "real_world_examples": [
            {"project": "Kuyasa SWH Programme, Cape Town", "credits": 6000, "year": 2023}
        ],
        "regulatory_notes": "Eligible under CDM, VCS, Gold Standard. Often bundled as PoA. Kuyasa was first CDM project in Africa.",
        "cdm_tools_needed": ["TOOL01", "TOOL07"],
        "estimated_cost_range_usd": {"min": 2000000, "max": 30000000},
        "crediting_period_years": {"min": 7, "max": 14}
    },

    "green_building_cert": {
        "id": "green_building_cert",
        "name": "Green Building Certification Programme",
        "description": "Construction or retrofit of buildings to green building standards (LEED, EDGE, GRIHA) achieving energy savings beyond code requirements.",
        "sector": "Buildings",
        "user_types": ["Developer", "Building Owner", "Corporate"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-II.E", "AMS-III.AE"],
        "recommended_methodology": "AMS-II.E",
        "scale": "Small",
        "typical_credit_range": {"min": 1000, "max": 20000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "building_area_sqm",
                "label": "Gross Floor Area",
                "description": "Total built-up area of the building.",
                "unit": "m2",
                "typical_range": {"min": 5000, "max": 500000},
                "example_value": 50000,
                "data_sources": ["Architectural drawings", "Building permit", "Certification application"],
                "required": True,
                "tooltip": "Conditioned area drives energy consumption."
            },
            {
                "parameter": "baseline_eui",
                "label": "Baseline Energy Use Intensity",
                "description": "Energy consumption per m2 for a code-compliant building.",
                "unit": "kWh/m2/year",
                "typical_range": {"min": 100, "max": 400},
                "example_value": 200,
                "data_sources": ["National building energy code", "ASHRAE 90.1 baseline", "Energy simulation (eQUEST, EnergyPlus)"],
                "required": True,
                "tooltip": "Baseline is the minimum code-compliant building."
            },
            {
                "parameter": "project_eui",
                "label": "Project Energy Use Intensity",
                "description": "Achieved energy consumption per m2 in the green building.",
                "unit": "kWh/m2/year",
                "typical_range": {"min": 50, "max": 250},
                "example_value": 120,
                "data_sources": ["Energy simulation", "As-built metered data", "Green building scorecard"],
                "required": True,
                "tooltip": "Must be verified by the certification body."
            }
        ],
        "real_world_examples": [
            {"project": "IFC EDGE Green Buildings, Vietnam", "credits": 8000, "year": 2023}
        ],
        "regulatory_notes": "IFC EDGE is designed for emerging market green buildings. VCS and Gold Standard accept these projects.",
        "cdm_tools_needed": ["TOOL01"],
        "estimated_cost_range_usd": {"min": 10000000, "max": 200000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    # ======================================================================
    # FINANCIAL  (#56 - #60)
    # ======================================================================

    "green_bond_re": {
        "id": "green_bond_re",
        "name": "Green Bond for Renewable Energy Portfolio",
        "description": "Issuance of green bonds to finance a portfolio of renewable energy projects, with proceeds tracked to verified emission reductions.",
        "sector": "Financial",
        "user_types": ["Bank", "DFI", "Institutional Investor"],
        "value_chain_position": "downstream",
        "applicable_methodologies": ["ACM0002", "AMS-I.D"],
        "recommended_methodology": "ACM0002",
        "scale": "Large",
        "typical_credit_range": {"min": 50000, "max": 1000000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "bond_value_usd",
                "label": "Green Bond Issuance Size",
                "description": "Total value of the green bond issuance.",
                "unit": "USD",
                "typical_range": {"min": 50000000, "max": 5000000000},
                "example_value": 500000000,
                "data_sources": ["Bond prospectus", "Underwriter term sheet"],
                "required": True,
                "tooltip": "100% of proceeds must be allocated to eligible green projects."
            },
            {
                "parameter": "financed_capacity_mw",
                "label": "Total RE Capacity Financed",
                "description": "Sum of renewable energy capacity financed by bond proceeds.",
                "unit": "MW",
                "typical_range": {"min": 100, "max": 5000},
                "example_value": 800,
                "data_sources": ["Green bond impact report", "Use-of-proceeds allocation", "Project pipeline"],
                "required": True,
                "tooltip": "Aggregated across all projects in the portfolio."
            },
            {
                "parameter": "weighted_grid_ef",
                "label": "Weighted Average Grid EF",
                "description": "Portfolio-weighted grid emission factor across project locations.",
                "unit": "tCO2/MWh",
                "typical_range": {"min": 0.4, "max": 1.0},
                "example_value": 0.75,
                "data_sources": ["National grid authorities for each project country", "IFI Harmonized Grid EF"],
                "required": True,
                "tooltip": "Weighted by expected generation share of each project."
            }
        ],
        "real_world_examples": [
            {"project": "SBI Green Bond RE Portfolio, India", "credits": 400000, "year": 2023}
        ],
        "regulatory_notes": "Credits attributed to underlying projects, not the bond itself. ICMA Green Bond Principles apply.",
        "cdm_tools_needed": ["TOOL01", "TOOL07"],
        "estimated_cost_range_usd": {"min": 50000000, "max": 5000000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    "msme_clean_lending": {
        "id": "msme_clean_lending",
        "name": "MSME Clean Energy Lending Programme",
        "description": "Financial institution lending programme providing loans to micro, small and medium enterprises for clean energy equipment (solar, EE, biogas).",
        "sector": "Financial",
        "user_types": ["Bank", "MFI", "DFI"],
        "value_chain_position": "downstream",
        "applicable_methodologies": ["AMS-I.D", "AMS-II.C", "Gold Standard Microscale"],
        "recommended_methodology": "AMS-I.D",
        "scale": "Small",
        "typical_credit_range": {"min": 5000, "max": 50000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "number_of_loans",
                "label": "Number of Clean Energy Loans Disbursed",
                "description": "Total loans issued for clean energy equipment.",
                "unit": "count",
                "typical_range": {"min": 100, "max": 50000},
                "example_value": 5000,
                "data_sources": ["Loan management system", "Disbursement records"],
                "required": True,
                "tooltip": "Each loan finances one or more clean energy assets."
            },
            {
                "parameter": "avg_capacity_per_loan_kw",
                "label": "Average RE Capacity per Loan",
                "description": "Average clean energy capacity financed per loan.",
                "unit": "kW",
                "typical_range": {"min": 1, "max": 100},
                "example_value": 10,
                "data_sources": ["Loan application data", "Equipment specs on file"],
                "required": True,
                "tooltip": "Varies by technology; solar rooftop typically 5-50 kW."
            },
            {
                "parameter": "grid_emission_factor",
                "label": "Grid Emission Factor",
                "description": "CO2 intensity of displaced electricity.",
                "unit": "tCO2/MWh",
                "typical_range": {"min": 0.4, "max": 1.2},
                "example_value": 0.85,
                "data_sources": ["National grid authority", "IFI Harmonized Grid EF database"],
                "required": True,
                "tooltip": "Applied to aggregated generation from all financed assets."
            }
        ],
        "real_world_examples": [
            {"project": "IDCOL Solar Home System Lending, Bangladesh", "credits": 30000, "year": 2023}
        ],
        "regulatory_notes": "Often structured as PoA with each loan as a CPA. Gold Standard popular for microfinance carbon.",
        "cdm_tools_needed": ["TOOL01"],
        "estimated_cost_range_usd": {"min": 5000000, "max": 100000000},
        "crediting_period_years": {"min": 7, "max": 14}
    },

    "forest_offset_portfolio": {
        "id": "forest_offset_portfolio",
        "name": "Forest Carbon Offset Investment Portfolio",
        "description": "Investment fund purchasing and managing a diversified portfolio of forestry and land-use carbon credits (REDD+, ARR, IFM).",
        "sector": "Financial",
        "user_types": ["Asset Manager", "Institutional Investor", "Corporate"],
        "value_chain_position": "downstream",
        "applicable_methodologies": ["VM0007", "VM0010", "AR-ACM0003"],
        "recommended_methodology": "VM0007",
        "scale": "Large",
        "typical_credit_range": {"min": 100000, "max": 5000000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "portfolio_value_usd",
                "label": "Total Portfolio Investment",
                "description": "Total capital allocated to forestry carbon offset investments.",
                "unit": "USD",
                "typical_range": {"min": 10000000, "max": 1000000000},
                "example_value": 100000000,
                "data_sources": ["Fund documents", "Investment committee records"],
                "required": True,
                "tooltip": "Total committed capital across all projects."
            },
            {
                "parameter": "total_area_ha",
                "label": "Total Forest Area Covered",
                "description": "Aggregate forest area across all portfolio projects.",
                "unit": "hectares",
                "typical_range": {"min": 50000, "max": 5000000},
                "example_value": 500000,
                "data_sources": ["Project design documents", "VCS project database"],
                "required": True,
                "tooltip": "Sum of all project areas in the portfolio."
            },
            {
                "parameter": "expected_annual_credits",
                "label": "Expected Annual Credit Issuance",
                "description": "Total VCUs or other credits expected from the portfolio per year.",
                "unit": "tCO2e/year",
                "typical_range": {"min": 100000, "max": 5000000},
                "example_value": 1000000,
                "data_sources": ["Project monitoring reports", "Third-party verification reports", "Credit issuance records"],
                "required": True,
                "tooltip": "After buffer pool deductions."
            }
        ],
        "real_world_examples": [
            {"project": "Mirova Natural Capital Fund", "credits": 2000000, "year": 2023}
        ],
        "regulatory_notes": "Credits are issued to underlying projects. Fund manages aggregation and risk diversification.",
        "cdm_tools_needed": ["TOOL14"],
        "estimated_cost_range_usd": {"min": 10000000, "max": 1000000000},
        "crediting_period_years": {"min": 20, "max": 40}
    },

    "carbon_trading_desk": {
        "id": "carbon_trading_desk",
        "name": "Carbon Credit Trading and Intermediation",
        "description": "Professional trading desk buying and selling carbon credits (CERs, VCUs, GS credits) in secondary markets.",
        "sector": "Financial",
        "user_types": ["Trading Firm", "Bank", "Broker"],
        "value_chain_position": "downstream",
        "applicable_methodologies": ["Multiple (underlying)"],
        "recommended_methodology": "Multiple (underlying)",
        "scale": "Large",
        "typical_credit_range": {"min": 100000, "max": 10000000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "annual_volume_traded",
                "label": "Annual Volume Traded",
                "description": "Total carbon credits bought and sold per year.",
                "unit": "tCO2e/year",
                "typical_range": {"min": 100000, "max": 10000000},
                "example_value": 2000000,
                "data_sources": ["Trading system records", "Registry transfer logs", "Settlement reports"],
                "required": True,
                "tooltip": "Both buy-side and sell-side volumes."
            },
            {
                "parameter": "credit_mix",
                "label": "Credit Type Mix",
                "description": "Breakdown by credit type (CER, VCU, GS, ACR).",
                "unit": "% by volume",
                "typical_range": {"min": None, "max": None},
                "example_value": "VCU 60%, GS 25%, CER 15%",
                "data_sources": ["Trading portfolio reports", "Registry accounts"],
                "required": True,
                "tooltip": "Different credit types have different price points and risk profiles."
            },
            {
                "parameter": "avg_price_per_credit_usd",
                "label": "Average Price per Credit",
                "description": "Volume-weighted average trading price.",
                "unit": "USD/tCO2e",
                "typical_range": {"min": 2, "max": 50},
                "example_value": 12,
                "data_sources": ["Trading system", "Market data providers (CBL, Xpansiv)"],
                "required": True,
                "tooltip": "Nature-based credits typically trade at premium to RE credits."
            }
        ],
        "real_world_examples": [
            {"project": "South Pole Carbon Trading, Global", "credits": 5000000, "year": 2023}
        ],
        "regulatory_notes": "Trading desk does not generate credits. It facilitates price discovery and liquidity. IOSCO oversight increasing.",
        "cdm_tools_needed": [],
        "estimated_cost_range_usd": {"min": 1000000, "max": 50000000},
        "crediting_period_years": {"min": 1, "max": 5}
    },

    "climate_blended_fund": {
        "id": "climate_blended_fund",
        "name": "Blended Finance Climate Fund",
        "description": "Structured fund combining concessional (DFI/donor) and commercial capital to finance climate mitigation projects in emerging markets.",
        "sector": "Financial",
        "user_types": ["DFI", "Asset Manager", "Institutional Investor"],
        "value_chain_position": "downstream",
        "applicable_methodologies": ["Multiple (underlying)"],
        "recommended_methodology": "Multiple (underlying)",
        "scale": "Large",
        "typical_credit_range": {"min": 50000, "max": 2000000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "fund_size_usd",
                "label": "Total Fund Size",
                "description": "Total capital committed to the fund (concessional + commercial).",
                "unit": "USD",
                "typical_range": {"min": 50000000, "max": 2000000000},
                "example_value": 500000000,
                "data_sources": ["Fund prospectus", "Subscription agreements"],
                "required": True,
                "tooltip": "Includes first-loss tranche, mezzanine, and senior tranches."
            },
            {
                "parameter": "concessional_share",
                "label": "Concessional Capital Share",
                "description": "Percentage of fund capital that is concessional (below-market rate).",
                "unit": "%",
                "typical_range": {"min": 10, "max": 50},
                "example_value": 25,
                "data_sources": ["Fund structure documents", "DFI commitment letters"],
                "required": True,
                "tooltip": "Concessional capital de-risks commercial investment."
            },
            {
                "parameter": "expected_emission_reductions_yr",
                "label": "Expected Annual Emission Reductions",
                "description": "Aggregate emission reductions from fund portfolio projects.",
                "unit": "tCO2e/year",
                "typical_range": {"min": 50000, "max": 2000000},
                "example_value": 500000,
                "data_sources": ["Impact measurement framework", "Project monitoring reports"],
                "required": True,
                "tooltip": "Sum of all underlying project emission reductions."
            }
        ],
        "real_world_examples": [
            {"project": "Green Climate Fund Catalytic Capital", "credits": 1200000, "year": 2023}
        ],
        "regulatory_notes": "Credits attributed to underlying projects. Fund provides aggregation and risk mitigation.",
        "cdm_tools_needed": [],
        "estimated_cost_range_usd": {"min": 50000000, "max": 2000000000},
        "crediting_period_years": {"min": 10, "max": 25}
    },

    # ======================================================================
    # UPSTREAM  (#61 - #71)
    # ======================================================================

    "turbine_panel_mfg": {
        "id": "turbine_panel_mfg",
        "name": "Wind Turbine / Solar Panel Manufacturing",
        "description": "Manufacturing of wind turbines or solar PV modules that enable downstream renewable energy carbon credit projects.",
        "sector": "Upstream",
        "user_types": ["Manufacturer", "OEM"],
        "value_chain_position": "upstream",
        "applicable_methodologies": ["Scope 3 Attribution"],
        "recommended_methodology": "Scope 3 Attribution",
        "scale": "Large",
        "typical_credit_range": {"min": 0, "max": 0, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "annual_production_mw",
                "label": "Annual Production Capacity Shipped",
                "description": "Total MW of turbines or modules shipped per year.",
                "unit": "MW/year",
                "typical_range": {"min": 100, "max": 20000},
                "example_value": 3000,
                "data_sources": ["Production records", "Shipping manifests", "Sales data"],
                "required": True,
                "tooltip": "Measures upstream enabling contribution."
            },
            {
                "parameter": "embodied_carbon_tco2_mw",
                "label": "Embodied Carbon per MW",
                "description": "Lifecycle CO2 emissions from manufacturing per MW.",
                "unit": "tCO2e/MW",
                "typical_range": {"min": 300, "max": 1500},
                "example_value": 700,
                "data_sources": ["LCA report", "EPD (Environmental Product Declaration)", "Company sustainability report"],
                "required": True,
                "tooltip": "Used for Scope 3 reporting, not direct credit generation."
            },
            {
                "parameter": "factory_energy_source",
                "label": "Factory Energy Source",
                "description": "Primary energy source for the manufacturing facility.",
                "unit": "text",
                "typical_range": {"min": None, "max": None},
                "example_value": "Grid electricity + rooftop solar",
                "data_sources": ["Utility bills", "PPA for factory", "Energy audit"],
                "required": True,
                "tooltip": "RE-powered factories reduce embodied carbon."
            }
        ],
        "real_world_examples": [
            {"project": "Vestas Wind Turbine Factory, India", "credits": 0, "year": 2023}
        ],
        "regulatory_notes": "Upstream manufacturers do not directly generate credits but are essential enablers. Scope 3 attribution possible.",
        "cdm_tools_needed": [],
        "estimated_cost_range_usd": {"min": 100000000, "max": 5000000000},
        "crediting_period_years": {"min": 0, "max": 0}
    },

    "epc_contractor_re": {
        "id": "epc_contractor_re",
        "name": "EPC Contractor for Renewable Energy",
        "description": "Engineering, Procurement and Construction services for renewable energy projects that generate carbon credits.",
        "sector": "Upstream",
        "user_types": ["EPC Contractor", "Engineering Firm"],
        "value_chain_position": "upstream",
        "applicable_methodologies": ["Scope 3 Attribution"],
        "recommended_methodology": "Scope 3 Attribution",
        "scale": "Large",
        "typical_credit_range": {"min": 0, "max": 0, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "projects_completed_yr",
                "label": "RE Projects Completed per Year",
                "description": "Number of renewable energy projects constructed annually.",
                "unit": "count",
                "typical_range": {"min": 5, "max": 100},
                "example_value": 20,
                "data_sources": ["Project completion records", "Client handover certificates"],
                "required": True,
                "tooltip": "Counts projects reaching commercial operation."
            },
            {
                "parameter": "total_capacity_mw",
                "label": "Total Capacity Constructed",
                "description": "Aggregate MW capacity of all RE projects constructed.",
                "unit": "MW/year",
                "typical_range": {"min": 50, "max": 5000},
                "example_value": 500,
                "data_sources": ["Project registers", "EPC contract values"],
                "required": True,
                "tooltip": "Sum across wind, solar, hydro, biomass projects."
            },
            {
                "parameter": "construction_emissions_tco2",
                "label": "Construction Phase Emissions",
                "description": "CO2 from construction activities (transport, machinery, concrete).",
                "unit": "tCO2e/project",
                "typical_range": {"min": 1000, "max": 50000},
                "example_value": 8000,
                "data_sources": ["Construction environmental management plan", "Fuel consumption logs", "Material transport records"],
                "required": True,
                "tooltip": "Minimising construction emissions improves project net benefit."
            }
        ],
        "real_world_examples": [
            {"project": "Sterling & Wilson RE EPC, India", "credits": 0, "year": 2023}
        ],
        "regulatory_notes": "EPC contractors enable credits but do not hold them. Scope 3 downstream attribution possible.",
        "cdm_tools_needed": [],
        "estimated_cost_range_usd": {"min": 10000000, "max": 500000000},
        "crediting_period_years": {"min": 0, "max": 0}
    },

    "biomass_pellet_supplier": {
        "id": "biomass_pellet_supplier",
        "name": "Biomass Pellet / Briquette Supplier",
        "description": "Production and supply of biomass pellets or briquettes as fuel for biomass power plants and industrial boilers.",
        "sector": "Upstream",
        "user_types": ["Biomass Processor", "Agricultural Cooperative"],
        "value_chain_position": "upstream",
        "applicable_methodologies": ["AMS-I.C", "ACM0006"],
        "recommended_methodology": "AMS-I.C",
        "scale": "Small",
        "typical_credit_range": {"min": 1000, "max": 20000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "annual_pellet_production_tonnes",
                "label": "Annual Pellet Production",
                "description": "Total tonnes of biomass pellets/briquettes produced per year.",
                "unit": "tonnes/year",
                "typical_range": {"min": 5000, "max": 200000},
                "example_value": 40000,
                "data_sources": ["Production records", "Weigh bridge data", "Sales invoices"],
                "required": True,
                "tooltip": "Dry weight at standard moisture content."
            },
            {
                "parameter": "feedstock_source",
                "label": "Biomass Feedstock Source",
                "description": "Source of raw biomass material.",
                "unit": "text",
                "typical_range": {"min": None, "max": None},
                "example_value": "Sawmill residues and rice husks",
                "data_sources": ["Feedstock procurement records", "Supply contracts"],
                "required": True,
                "tooltip": "Must be waste biomass; no primary forest clearing."
            },
            {
                "parameter": "fossil_fuel_displaced",
                "label": "Fossil Fuel Displaced",
                "description": "Type and quantity of fossil fuel displaced by biomass pellets.",
                "unit": "text",
                "typical_range": {"min": None, "max": None},
                "example_value": "Coal in industrial boilers",
                "data_sources": ["Customer fuel records", "Boiler conversion contracts"],
                "required": True,
                "tooltip": "Credit is earned when pellets displace fossil fuel at the end user."
            }
        ],
        "real_world_examples": [
            {"project": "Agripellets India, Punjab", "credits": 8000, "year": 2023}
        ],
        "regulatory_notes": "Credits typically accrue to the downstream user; supplier may co-claim under PoA structure.",
        "cdm_tools_needed": ["TOOL01", "TOOL16"],
        "estimated_cost_range_usd": {"min": 500000, "max": 10000000},
        "crediting_period_years": {"min": 7, "max": 14}
    },

    "cookstove_mfg": {
        "id": "cookstove_mfg",
        "name": "Improved Cookstove Manufacturer",
        "description": "Manufacturing of improved efficiency biomass cookstoves for distribution programmes that generate carbon credits.",
        "sector": "Upstream",
        "user_types": ["Manufacturer", "Social Enterprise"],
        "value_chain_position": "upstream",
        "applicable_methodologies": ["AMS-II.G"],
        "recommended_methodology": "AMS-II.G",
        "scale": "Small",
        "typical_credit_range": {"min": 5000, "max": 80000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "stoves_produced_yr",
                "label": "Annual Stove Production",
                "description": "Number of improved cookstoves manufactured per year.",
                "unit": "count/year",
                "typical_range": {"min": 10000, "max": 500000},
                "example_value": 100000,
                "data_sources": ["Factory production records", "Quality control logs"],
                "required": True,
                "tooltip": "Stoves must pass thermal efficiency testing (WBT/CCT)."
            },
            {
                "parameter": "thermal_efficiency",
                "label": "Stove Thermal Efficiency",
                "description": "Lab-tested thermal efficiency of the stove.",
                "unit": "%",
                "typical_range": {"min": 25, "max": 60},
                "example_value": 40,
                "data_sources": ["WBT (Water Boiling Test) results", "ISO 19867 certification"],
                "required": True,
                "tooltip": "Must exceed traditional stove efficiency (typically 10-15%)."
            },
            {
                "parameter": "unit_cost_usd",
                "label": "Manufacturing Cost per Stove",
                "description": "Cost to produce one improved cookstove.",
                "unit": "USD",
                "typical_range": {"min": 5, "max": 50},
                "example_value": 15,
                "data_sources": ["Bill of materials", "Factory costing records"],
                "required": True,
                "tooltip": "Carbon revenue helps subsidise stove cost for end users."
            }
        ],
        "real_world_examples": [
            {"project": "Burn Manufacturing, Nairobi Kenya", "credits": 60000, "year": 2023}
        ],
        "regulatory_notes": "Manufacturer may hold credits if it runs the distribution programme. Otherwise credits accrue to distributor.",
        "cdm_tools_needed": ["TOOL01", "TOOL30"],
        "estimated_cost_range_usd": {"min": 500000, "max": 10000000},
        "crediting_period_years": {"min": 5, "max": 10}
    },

    "biochar_production": {
        "id": "biochar_production",
        "name": "Biochar Production Facility",
        "description": "Industrial-scale pyrolysis facility converting waste biomass into biochar for carbon sequestration.",
        "sector": "Upstream",
        "user_types": ["Biochar Producer", "Waste Processor"],
        "value_chain_position": "upstream",
        "applicable_methodologies": ["Puro.earth Biochar", "VCS Biochar"],
        "recommended_methodology": "Puro.earth Biochar",
        "scale": "Small",
        "typical_credit_range": {"min": 1000, "max": 30000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "pyrolysis_capacity_tonnes_yr",
                "label": "Annual Pyrolysis Throughput",
                "description": "Tonnes of biomass processed through pyrolysis per year.",
                "unit": "tonnes/year",
                "typical_range": {"min": 500, "max": 50000},
                "example_value": 10000,
                "data_sources": ["Plant production records", "Feedstock weigh bridge data"],
                "required": True,
                "tooltip": "Dry weight input to pyrolysis reactor."
            },
            {
                "parameter": "biochar_yield",
                "label": "Biochar Mass Yield",
                "description": "Fraction of input biomass converted to biochar.",
                "unit": "%",
                "typical_range": {"min": 20, "max": 40},
                "example_value": 30,
                "data_sources": ["Process data", "Mass balance calculations"],
                "required": True,
                "tooltip": "Depends on pyrolysis temperature and feedstock."
            },
            {
                "parameter": "fixed_carbon_pct",
                "label": "Fixed Carbon Content",
                "description": "Stable carbon fraction in the biochar product.",
                "unit": "%",
                "typical_range": {"min": 50, "max": 90},
                "example_value": 75,
                "data_sources": ["Lab proximate analysis", "IBI/EBC certification"],
                "required": True,
                "tooltip": "Higher fixed C = more durable carbon removal per tonne."
            }
        ],
        "real_world_examples": [
            {"project": "Carbon Gold Biochar, UK", "credits": 5000, "year": 2023}
        ],
        "regulatory_notes": "Puro.earth and VCS accept biochar CDR credits. EBC (European Biochar Certificate) is quality standard.",
        "cdm_tools_needed": [],
        "estimated_cost_range_usd": {"min": 1000000, "max": 20000000},
        "crediting_period_years": {"min": 10, "max": 30}
    },

    "digester_equipment": {
        "id": "digester_equipment",
        "name": "Anaerobic Digester Equipment Supplier",
        "description": "Manufacturing and supply of anaerobic digester systems for agricultural and municipal waste methane capture projects.",
        "sector": "Upstream",
        "user_types": ["Equipment Manufacturer", "Technology Provider"],
        "value_chain_position": "upstream",
        "applicable_methodologies": ["AMS-III.D", "AMS-III.H"],
        "recommended_methodology": "AMS-III.D",
        "scale": "Small",
        "typical_credit_range": {"min": 0, "max": 0, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "digesters_sold_yr",
                "label": "Digesters Sold per Year",
                "description": "Number of digester systems delivered and installed.",
                "unit": "count/year",
                "typical_range": {"min": 10, "max": 500},
                "example_value": 50,
                "data_sources": ["Sales records", "Delivery and commissioning records"],
                "required": True,
                "tooltip": "Each digester enables downstream methane capture credits."
            },
            {
                "parameter": "avg_capacity_m3",
                "label": "Average Digester Capacity",
                "description": "Average reactor volume per unit.",
                "unit": "m3",
                "typical_range": {"min": 10, "max": 5000},
                "example_value": 500,
                "data_sources": ["Product specifications", "Design documents"],
                "required": True,
                "tooltip": "Reactor volume determines biogas output potential."
            },
            {
                "parameter": "enabled_credits_per_unit",
                "label": "Estimated Credits Enabled per Digester",
                "description": "Expected annual tCO2e credits from each installed digester.",
                "unit": "tCO2e/year",
                "typical_range": {"min": 500, "max": 10000},
                "example_value": 3000,
                "data_sources": ["Customer project monitoring reports", "Technology performance data"],
                "required": True,
                "tooltip": "Credits accrue to the digester operator, not the equipment supplier."
            }
        ],
        "real_world_examples": [
            {"project": "Sistema Biobolsa, Mexico", "credits": 0, "year": 2023}
        ],
        "regulatory_notes": "Equipment supplier enables credits but does not hold them. Supply chain attribution for Scope 3 reporting.",
        "cdm_tools_needed": [],
        "estimated_cost_range_usd": {"min": 500000, "max": 20000000},
        "crediting_period_years": {"min": 0, "max": 0}
    },

    "tree_nursery": {
        "id": "tree_nursery",
        "name": "Tree Nursery for Reforestation Projects",
        "description": "Operation of tree nurseries producing seedlings for afforestation, reforestation, and agroforestry carbon credit projects.",
        "sector": "Upstream",
        "user_types": ["Nursery Operator", "NGO", "Government Forestry"],
        "value_chain_position": "upstream",
        "applicable_methodologies": ["AR-ACM0003", "VM0047"],
        "recommended_methodology": "AR-ACM0003",
        "scale": "Small",
        "typical_credit_range": {"min": 0, "max": 0, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "seedlings_produced_yr",
                "label": "Annual Seedling Production",
                "description": "Total seedlings produced per year.",
                "unit": "count/year",
                "typical_range": {"min": 100000, "max": 10000000},
                "example_value": 2000000,
                "data_sources": ["Nursery production records", "Dispatch logs"],
                "required": True,
                "tooltip": "Includes all species grown for carbon projects."
            },
            {
                "parameter": "species_count",
                "label": "Number of Species Grown",
                "description": "Diversity of tree species in the nursery catalogue.",
                "unit": "count",
                "typical_range": {"min": 5, "max": 100},
                "example_value": 25,
                "data_sources": ["Species catalogue", "Seed procurement records"],
                "required": True,
                "tooltip": "Higher diversity supports biodiversity co-benefits."
            },
            {
                "parameter": "germination_rate",
                "label": "Average Germination Rate",
                "description": "Percentage of seeds that successfully germinate.",
                "unit": "%",
                "typical_range": {"min": 50, "max": 95},
                "example_value": 80,
                "data_sources": ["Nursery quality records", "Seed testing lab results"],
                "required": True,
                "tooltip": "Higher germination reduces cost per plantable seedling."
            }
        ],
        "real_world_examples": [
            {"project": "One Tree Planted Nursery Network, Global", "credits": 0, "year": 2023}
        ],
        "regulatory_notes": "Nurseries are critical enablers for forestry carbon. Credits go to the planting project, not the nursery.",
        "cdm_tools_needed": [],
        "estimated_cost_range_usd": {"min": 50000, "max": 2000000},
        "crediting_period_years": {"min": 0, "max": 0}
    },

    "catalyst_supplier_n2o": {
        "id": "catalyst_supplier_n2o",
        "name": "N2O Abatement Catalyst Supplier",
        "description": "Supply of catalytic abatement technology for N2O destruction in nitric acid and adipic acid plants.",
        "sector": "Upstream",
        "user_types": ["Catalyst Manufacturer", "Technology Provider"],
        "value_chain_position": "upstream",
        "applicable_methodologies": ["AM0028", "AM0034"],
        "recommended_methodology": "AM0028",
        "scale": "Large",
        "typical_credit_range": {"min": 0, "max": 0, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "catalyst_units_sold_yr",
                "label": "Catalyst Units Sold per Year",
                "description": "Number of N2O abatement catalyst systems delivered.",
                "unit": "count/year",
                "typical_range": {"min": 1, "max": 50},
                "example_value": 10,
                "data_sources": ["Sales records", "Delivery records"],
                "required": True,
                "tooltip": "Each unit enables N2O destruction at a chemical plant."
            },
            {
                "parameter": "destruction_efficiency",
                "label": "Guaranteed Destruction Efficiency",
                "description": "Minimum N2O destruction efficiency of the catalyst.",
                "unit": "%",
                "typical_range": {"min": 80, "max": 99},
                "example_value": 95,
                "data_sources": ["Product performance guarantee", "Type-test results"],
                "required": True,
                "tooltip": "Higher efficiency = more N2O abatement per installation."
            },
            {
                "parameter": "catalyst_lifetime_yr",
                "label": "Catalyst Lifetime",
                "description": "Expected operational life of the catalyst.",
                "unit": "years",
                "typical_range": {"min": 3, "max": 10},
                "example_value": 5,
                "data_sources": ["OEM warranty terms", "Field performance data"],
                "required": True,
                "tooltip": "Replacement frequency affects total cost of ownership."
            }
        ],
        "real_world_examples": [
            {"project": "Johnson Matthey N2O Catalyst, Global", "credits": 0, "year": 2023}
        ],
        "regulatory_notes": "Catalyst supplier enables credits at the chemical plant. Credits accrue to the plant operator.",
        "cdm_tools_needed": [],
        "estimated_cost_range_usd": {"min": 5000000, "max": 50000000},
        "crediting_period_years": {"min": 0, "max": 0}
    },

    "led_ee_supplier": {
        "id": "led_ee_supplier",
        "name": "LED and Energy Efficiency Equipment Supplier",
        "description": "Supply of LED luminaires, VFDs, efficient motors, and other energy efficiency equipment for building and industrial projects.",
        "sector": "Upstream",
        "user_types": ["Manufacturer", "Distributor", "ESCO"],
        "value_chain_position": "upstream",
        "applicable_methodologies": ["AMS-II.J", "AMS-II.D"],
        "recommended_methodology": "AMS-II.J",
        "scale": "Small",
        "typical_credit_range": {"min": 0, "max": 0, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "units_sold_yr",
                "label": "EE Equipment Units Sold per Year",
                "description": "Total energy efficiency devices sold to project implementers.",
                "unit": "count/year",
                "typical_range": {"min": 10000, "max": 5000000},
                "example_value": 500000,
                "data_sources": ["Sales records", "Distribution data"],
                "required": True,
                "tooltip": "Sold units that are installed in carbon credit projects."
            },
            {
                "parameter": "avg_energy_saving_kwh_unit",
                "label": "Average Energy Saving per Unit",
                "description": "Estimated annual kWh saved per installed device.",
                "unit": "kWh/unit/year",
                "typical_range": {"min": 50, "max": 5000},
                "example_value": 200,
                "data_sources": ["Product energy rating labels", "Lab test results", "Field M&V data"],
                "required": True,
                "tooltip": "Based on comparison with conventional technology baseline."
            },
            {
                "parameter": "market_share_carbon",
                "label": "Share Sold to Carbon Credit Projects",
                "description": "Fraction of sales that go to registered carbon credit projects.",
                "unit": "%",
                "typical_range": {"min": 5, "max": 80},
                "example_value": 30,
                "data_sources": ["Customer records", "PoA registration data"],
                "required": True,
                "tooltip": "Only units in registered projects contribute to credit generation."
            }
        ],
        "real_world_examples": [
            {"project": "Signify LED Distribution, India PoA", "credits": 0, "year": 2023}
        ],
        "regulatory_notes": "Supplier enables credits through product distribution. Credits accrue to project coordinator (PoA).",
        "cdm_tools_needed": [],
        "estimated_cost_range_usd": {"min": 1000000, "max": 50000000},
        "crediting_period_years": {"min": 0, "max": 0}
    },

    "ev_bus_mfg": {
        "id": "ev_bus_mfg",
        "name": "Electric Bus Manufacturer",
        "description": "Manufacturing of battery-electric buses deployed in urban transit fleets that generate carbon credits.",
        "sector": "Upstream",
        "user_types": ["Manufacturer", "OEM"],
        "value_chain_position": "upstream",
        "applicable_methodologies": ["AMS-III.C"],
        "recommended_methodology": "AMS-III.C",
        "scale": "Large",
        "typical_credit_range": {"min": 0, "max": 0, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "buses_produced_yr",
                "label": "Annual Bus Production",
                "description": "Number of electric buses manufactured per year.",
                "unit": "count/year",
                "typical_range": {"min": 50, "max": 10000},
                "example_value": 1000,
                "data_sources": ["Production records", "Delivery manifests"],
                "required": True,
                "tooltip": "Each bus deployed enables downstream transport credits."
            },
            {
                "parameter": "battery_capacity_kwh",
                "label": "Battery Capacity per Bus",
                "description": "Energy storage capacity of the bus battery pack.",
                "unit": "kWh",
                "typical_range": {"min": 150, "max": 600},
                "example_value": 350,
                "data_sources": ["Product specification", "Battery cell supplier data"],
                "required": True,
                "tooltip": "Determines range and daily operational capability."
            },
            {
                "parameter": "embodied_carbon_tco2",
                "label": "Embodied Carbon per Bus",
                "description": "Lifecycle CO2 from manufacturing one electric bus.",
                "unit": "tCO2e/bus",
                "typical_range": {"min": 30, "max": 120},
                "example_value": 60,
                "data_sources": ["LCA report", "Company sustainability report"],
                "required": True,
                "tooltip": "Battery production is the largest share of embodied carbon."
            }
        ],
        "real_world_examples": [
            {"project": "BYD Electric Bus Factory, Shenzhen", "credits": 0, "year": 2023}
        ],
        "regulatory_notes": "Manufacturer enables downstream credits. Credits accrue to the bus fleet operator.",
        "cdm_tools_needed": [],
        "estimated_cost_range_usd": {"min": 50000000, "max": 2000000000},
        "crediting_period_years": {"min": 0, "max": 0}
    },

    "composting_equipment": {
        "id": "composting_equipment",
        "name": "Composting Equipment Supplier",
        "description": "Supply of industrial composting equipment (turners, screens, aeration systems) for municipal and agricultural composting projects.",
        "sector": "Upstream",
        "user_types": ["Equipment Manufacturer", "Technology Provider"],
        "value_chain_position": "upstream",
        "applicable_methodologies": ["AMS-III.F"],
        "recommended_methodology": "AMS-III.F",
        "scale": "Small",
        "typical_credit_range": {"min": 0, "max": 0, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "systems_sold_yr",
                "label": "Composting Systems Sold per Year",
                "description": "Number of complete composting systems delivered.",
                "unit": "count/year",
                "typical_range": {"min": 5, "max": 100},
                "example_value": 15,
                "data_sources": ["Sales records", "Delivery and commissioning records"],
                "required": True,
                "tooltip": "Each system enables a downstream composting carbon project."
            },
            {
                "parameter": "capacity_tonnes_day",
                "label": "System Processing Capacity",
                "description": "Daily organic waste processing capacity per system.",
                "unit": "tonnes/day",
                "typical_range": {"min": 10, "max": 500},
                "example_value": 100,
                "data_sources": ["Product specifications", "Design documents"],
                "required": True,
                "tooltip": "Determines scale of methane avoidance at each site."
            },
            {
                "parameter": "enabled_credits_per_system",
                "label": "Estimated Credits Enabled per System",
                "description": "Expected annual tCO2e avoidance per composting system.",
                "unit": "tCO2e/year",
                "typical_range": {"min": 2000, "max": 20000},
                "example_value": 8000,
                "data_sources": ["Customer project data", "Methodology calculations"],
                "required": True,
                "tooltip": "Credits accrue to the composting operator."
            }
        ],
        "real_world_examples": [
            {"project": "Komptech Composting Systems, Global", "credits": 0, "year": 2023}
        ],
        "regulatory_notes": "Equipment supplier is an upstream enabler. Credits are generated by the composting facility operator.",
        "cdm_tools_needed": [],
        "estimated_cost_range_usd": {"min": 200000, "max": 5000000},
        "crediting_period_years": {"min": 0, "max": 0}
    },

    # ======================================================================
    # DOWNSTREAM  (#72 - #81)
    # ======================================================================

    "corporate_ppa_buyer": {
        "id": "corporate_ppa_buyer",
        "name": "Corporate PPA Buyer",
        "description": "Corporate offtaker purchasing electricity via power purchase agreement from a renewable energy project, enabling project financing.",
        "sector": "Downstream",
        "user_types": ["Corporate", "Data Centre Operator", "Manufacturing"],
        "value_chain_position": "downstream",
        "applicable_methodologies": ["ACM0002", "AMS-I.D"],
        "recommended_methodology": "ACM0002",
        "scale": "Large",
        "typical_credit_range": {"min": 5000, "max": 200000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "ppa_volume_mwh_yr",
                "label": "Annual PPA Volume",
                "description": "Electricity contracted under the PPA per year.",
                "unit": "MWh/year",
                "typical_range": {"min": 10000, "max": 2000000},
                "example_value": 200000,
                "data_sources": ["PPA contract", "Monthly billing statements", "Grid settlement data"],
                "required": True,
                "tooltip": "Total contracted or actual offtake volume."
            },
            {
                "parameter": "ppa_price_usd_mwh",
                "label": "PPA Price",
                "description": "Contract price for electricity under the PPA.",
                "unit": "USD/MWh",
                "typical_range": {"min": 20, "max": 80},
                "example_value": 45,
                "data_sources": ["PPA contract", "Amendment records"],
                "required": True,
                "tooltip": "Long-term fixed price enables project bankability."
            },
            {
                "parameter": "grid_emission_factor",
                "label": "Grid Emission Factor",
                "description": "CO2 intensity of the grid electricity displaced.",
                "unit": "tCO2/MWh",
                "typical_range": {"min": 0.3, "max": 1.2},
                "example_value": 0.8,
                "data_sources": ["National grid authority", "IFI Harmonized Grid EF database"],
                "required": True,
                "tooltip": "Used to calculate Scope 2 emission reductions."
            }
        ],
        "real_world_examples": [
            {"project": "Google Corporate PPA India", "credits": 120000, "year": 2023}
        ],
        "regulatory_notes": "PPA buyer typically claims RECs or Scope 2 reductions. Carbon credits accrue to the RE project developer.",
        "cdm_tools_needed": ["TOOL01", "TOOL07"],
        "estimated_cost_range_usd": {"min": 5000000, "max": 200000000},
        "crediting_period_years": {"min": 10, "max": 25}
    },

    "rec_trader": {
        "id": "rec_trader",
        "name": "Renewable Energy Certificate (REC) Trader",
        "description": "Trading of RECs, I-RECs, or GOs as instruments tracking renewable electricity attributes.",
        "sector": "Downstream",
        "user_types": ["Trading Firm", "Utility", "Broker"],
        "value_chain_position": "downstream",
        "applicable_methodologies": ["I-REC Standard", "TIGR"],
        "recommended_methodology": "I-REC Standard",
        "scale": "Large",
        "typical_credit_range": {"min": 0, "max": 0, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "recs_traded_yr",
                "label": "Annual RECs Traded",
                "description": "Total renewable energy certificates traded per year.",
                "unit": "MWh (certificates)",
                "typical_range": {"min": 10000, "max": 5000000},
                "example_value": 500000,
                "data_sources": ["I-REC registry", "Trading platform records"],
                "required": True,
                "tooltip": "1 REC = 1 MWh of renewable electricity."
            },
            {
                "parameter": "avg_price_usd_rec",
                "label": "Average REC Price",
                "description": "Volume-weighted average price per REC.",
                "unit": "USD/MWh",
                "typical_range": {"min": 0.5, "max": 10},
                "example_value": 3,
                "data_sources": ["Trading platform", "Broker quotes"],
                "required": True,
                "tooltip": "Price varies by country, technology, and vintage."
            },
            {
                "parameter": "source_technologies",
                "label": "Source Technologies",
                "description": "Renewable technologies generating the RECs.",
                "unit": "text",
                "typical_range": {"min": None, "max": None},
                "example_value": "Solar 50%, Wind 40%, Hydro 10%",
                "data_sources": ["Registry certificate details", "Generator profiles"],
                "required": True,
                "tooltip": "Buyers may prefer specific technology RECs."
            }
        ],
        "real_world_examples": [
            {"project": "I-REC India Platform", "credits": 0, "year": 2023}
        ],
        "regulatory_notes": "RECs are distinct from carbon credits. Used for Scope 2 reporting (market-based method). Not directly convertible to VCUs.",
        "cdm_tools_needed": [],
        "estimated_cost_range_usd": {"min": 100000, "max": 10000000},
        "crediting_period_years": {"min": 1, "max": 5}
    },

    "carbon_aggregator": {
        "id": "carbon_aggregator",
        "name": "Carbon Credit Aggregator",
        "description": "Aggregation of small-scale carbon credits from multiple projects into standardised portfolios for institutional buyers.",
        "sector": "Downstream",
        "user_types": ["Aggregator", "Project Developer", "Broker"],
        "value_chain_position": "downstream",
        "applicable_methodologies": ["Multiple (underlying)"],
        "recommended_methodology": "Multiple (underlying)",
        "scale": "Large",
        "typical_credit_range": {"min": 50000, "max": 5000000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "credits_aggregated_yr",
                "label": "Annual Credits Aggregated",
                "description": "Total carbon credits sourced from underlying projects.",
                "unit": "tCO2e/year",
                "typical_range": {"min": 50000, "max": 5000000},
                "example_value": 500000,
                "data_sources": ["Project registry data", "Purchase agreements", "Issuance records"],
                "required": True,
                "tooltip": "Sum of credits from all underlying projects."
            },
            {
                "parameter": "number_of_projects",
                "label": "Number of Underlying Projects",
                "description": "Count of individual carbon credit projects in the portfolio.",
                "unit": "count",
                "typical_range": {"min": 10, "max": 500},
                "example_value": 50,
                "data_sources": ["Project pipeline database", "Contract register"],
                "required": True,
                "tooltip": "Diversification reduces delivery risk."
            },
            {
                "parameter": "avg_credit_price_usd",
                "label": "Average Credit Purchase Price",
                "description": "Volume-weighted average price paid per credit.",
                "unit": "USD/tCO2e",
                "typical_range": {"min": 2, "max": 30},
                "example_value": 8,
                "data_sources": ["Purchase agreements", "Payment records"],
                "required": True,
                "tooltip": "Spread between purchase and sale price is the aggregator margin."
            }
        ],
        "real_world_examples": [
            {"project": "South Pole Aggregation Platform, Global", "credits": 3000000, "year": 2023}
        ],
        "regulatory_notes": "Aggregator pools and resells credits. Quality due diligence is critical. ICVCM CCP label gaining importance.",
        "cdm_tools_needed": [],
        "estimated_cost_range_usd": {"min": 1000000, "max": 50000000},
        "crediting_period_years": {"min": 1, "max": 10}
    },

    "voluntary_offset_buyer": {
        "id": "voluntary_offset_buyer",
        "name": "Voluntary Carbon Offset Buyer",
        "description": "Corporates purchasing carbon credits voluntarily to offset residual emissions and meet net-zero commitments.",
        "sector": "Downstream",
        "user_types": ["Corporate", "SME", "Event Organiser"],
        "value_chain_position": "downstream",
        "applicable_methodologies": ["Multiple (underlying)"],
        "recommended_methodology": "Multiple (underlying)",
        "scale": "Small",
        "typical_credit_range": {"min": 100, "max": 500000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "annual_offset_volume",
                "label": "Annual Offset Volume",
                "description": "Total carbon credits retired for offsetting per year.",
                "unit": "tCO2e/year",
                "typical_range": {"min": 100, "max": 500000},
                "example_value": 50000,
                "data_sources": ["Registry retirement records", "Sustainability report", "Offset provider invoices"],
                "required": True,
                "tooltip": "Must be retired (cancelled) to claim offset."
            },
            {
                "parameter": "budget_per_credit_usd",
                "label": "Budget per Credit",
                "description": "Maximum price the buyer will pay per credit.",
                "unit": "USD/tCO2e",
                "typical_range": {"min": 3, "max": 100},
                "example_value": 15,
                "data_sources": ["Procurement budget", "Board-approved climate strategy"],
                "required": True,
                "tooltip": "Higher quality credits (nature-based, CDR) command higher prices."
            },
            {
                "parameter": "preferred_project_types",
                "label": "Preferred Project Types",
                "description": "Types of carbon credit projects the buyer prefers.",
                "unit": "text",
                "typical_range": {"min": None, "max": None},
                "example_value": "Nature-based, Community energy access",
                "data_sources": ["Corporate climate strategy", "ESG policy", "Stakeholder engagement"],
                "required": True,
                "tooltip": "Aligning offsets with brand values improves credibility."
            }
        ],
        "real_world_examples": [
            {"project": "Microsoft Carbon Negative Programme", "credits": 400000, "year": 2023}
        ],
        "regulatory_notes": "Voluntary market. SBTi discourages offsetting for Scope 1/2 but allows for Scope 3. VCMI Claims Code of Practice.",
        "cdm_tools_needed": [],
        "estimated_cost_range_usd": {"min": 10000, "max": 50000000},
        "crediting_period_years": {"min": 1, "max": 5}
    },

    "corsia_buyer": {
        "id": "corsia_buyer",
        "name": "CORSIA Eligible Emission Unit Buyer",
        "description": "Airline purchasing CORSIA-eligible emission units to meet international aviation carbon offsetting obligations.",
        "sector": "Downstream",
        "user_types": ["Airline", "Aviation Group"],
        "value_chain_position": "downstream",
        "applicable_methodologies": ["CORSIA Eligible (multiple)"],
        "recommended_methodology": "CORSIA Eligible (multiple)",
        "scale": "Large",
        "typical_credit_range": {"min": 100000, "max": 10000000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "offsetting_requirement_yr",
                "label": "Annual CORSIA Offsetting Requirement",
                "description": "Total emission units required under CORSIA per year.",
                "unit": "tCO2e/year",
                "typical_range": {"min": 100000, "max": 10000000},
                "example_value": 1500000,
                "data_sources": ["ICAO CORSIA reporting", "Airline emissions monitoring report"],
                "required": True,
                "tooltip": "Based on growth factor above 2019-2020 baseline."
            },
            {
                "parameter": "unit_price_usd",
                "label": "Average Unit Price",
                "description": "Price per CORSIA-eligible emission unit.",
                "unit": "USD/tCO2e",
                "typical_range": {"min": 2, "max": 25},
                "example_value": 8,
                "data_sources": ["Procurement contracts", "Carbon market data"],
                "required": True,
                "tooltip": "CORSIA-eligible units include CDM CERs and VCS VCUs meeting criteria."
            },
            {
                "parameter": "eligible_programmes",
                "label": "Eligible Programmes",
                "description": "Carbon crediting programmes approved under CORSIA.",
                "unit": "text",
                "typical_range": {"min": None, "max": None},
                "example_value": "VCS, Gold Standard, ACR, CAR",
                "data_sources": ["ICAO TAB approved programme list"],
                "required": True,
                "tooltip": "Only units from ICAO-approved programmes qualify."
            }
        ],
        "real_world_examples": [
            {"project": "Singapore Airlines CORSIA Compliance", "credits": 800000, "year": 2023}
        ],
        "regulatory_notes": "CORSIA is ICAO's international aviation offsetting scheme. Mandatory from 2027 for many routes.",
        "cdm_tools_needed": [],
        "estimated_cost_range_usd": {"min": 500000, "max": 100000000},
        "crediting_period_years": {"min": 1, "max": 5}
    },

    "ets_buyer": {
        "id": "ets_buyer",
        "name": "Emissions Trading System (ETS) Compliance Buyer",
        "description": "Industrial or power sector entity purchasing allowances in a cap-and-trade emissions trading system.",
        "sector": "Downstream",
        "user_types": ["Utility", "Industrial Facility", "Corporate"],
        "value_chain_position": "downstream",
        "applicable_methodologies": ["EU ETS", "UK ETS", "K-ETS", "China ETS"],
        "recommended_methodology": "EU ETS",
        "scale": "Large",
        "typical_credit_range": {"min": 10000, "max": 10000000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "verified_emissions_yr",
                "label": "Annual Verified Emissions",
                "description": "Total verified GHG emissions of the installation.",
                "unit": "tCO2e/year",
                "typical_range": {"min": 10000, "max": 10000000},
                "example_value": 500000,
                "data_sources": ["Annual emissions report", "Verified emission statement", "MRV system"],
                "required": True,
                "tooltip": "Verified by accredited third-party verifier."
            },
            {
                "parameter": "free_allowances_yr",
                "label": "Free Allowances Received",
                "description": "Annual free allocation of allowances.",
                "unit": "EUAs/year",
                "typical_range": {"min": 0, "max": 5000000},
                "example_value": 300000,
                "data_sources": ["National allocation table", "Registry account"],
                "required": True,
                "tooltip": "Free allocation declining over time as ETS tightens."
            },
            {
                "parameter": "allowance_price_usd",
                "label": "Allowance Price",
                "description": "Current market price for emission allowances.",
                "unit": "USD/tCO2e",
                "typical_range": {"min": 10, "max": 120},
                "example_value": 80,
                "data_sources": ["ETS auction results", "Exchange trading data (ICE, EEX)"],
                "required": True,
                "tooltip": "EU ETS prices have exceeded EUR 100. China ETS is much lower."
            }
        ],
        "real_world_examples": [
            {"project": "RWE EU ETS Compliance, Germany", "credits": 3000000, "year": 2023}
        ],
        "regulatory_notes": "Compliance markets are regulated. ETS allowances (EUAs) are distinct from voluntary carbon credits (VCUs).",
        "cdm_tools_needed": [],
        "estimated_cost_range_usd": {"min": 1000000, "max": 500000000},
        "crediting_period_years": {"min": 1, "max": 5}
    },

    "timber_buyer": {
        "id": "timber_buyer",
        "name": "Sustainable Timber Buyer",
        "description": "Corporate or trader purchasing timber from improved forest management (IFM) projects generating carbon credits.",
        "sector": "Downstream",
        "user_types": ["Timber Trader", "Construction Company", "Retailer"],
        "value_chain_position": "downstream",
        "applicable_methodologies": ["VM0010"],
        "recommended_methodology": "VM0010",
        "scale": "Small",
        "typical_credit_range": {"min": 0, "max": 0, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "timber_volume_m3_yr",
                "label": "Annual Timber Volume Purchased",
                "description": "Volume of sustainably sourced timber purchased per year.",
                "unit": "m3/year",
                "typical_range": {"min": 1000, "max": 200000},
                "example_value": 20000,
                "data_sources": ["Purchase orders", "FSC/PEFC chain-of-custody records"],
                "required": True,
                "tooltip": "Only timber from certified IFM projects qualifies."
            },
            {
                "parameter": "certification",
                "label": "Forest Certification Standard",
                "description": "Sustainability certification of the timber source.",
                "unit": "text",
                "typical_range": {"min": None, "max": None},
                "example_value": "FSC",
                "data_sources": ["FSC/PEFC certificate", "Chain-of-custody audit"],
                "required": True,
                "tooltip": "FSC or PEFC certification demonstrates sustainable management."
            },
            {
                "parameter": "carbon_stored_tco2_m3",
                "label": "Carbon Stored per m3 of Timber",
                "description": "CO2 sequestered in harvested wood products.",
                "unit": "tCO2e/m3",
                "typical_range": {"min": 0.5, "max": 1.2},
                "example_value": 0.9,
                "data_sources": ["IPCC default values for wood density", "Species-specific data"],
                "required": True,
                "tooltip": "Long-lived wood products (construction) store carbon for decades."
            }
        ],
        "real_world_examples": [
            {"project": "IKEA Sustainable Forestry Supply Chain", "credits": 0, "year": 2023}
        ],
        "regulatory_notes": "Timber buyer supports IFM project revenue. Credits accrue to forest manager. HWP carbon storage is a separate accounting.",
        "cdm_tools_needed": [],
        "estimated_cost_range_usd": {"min": 500000, "max": 50000000},
        "crediting_period_years": {"min": 0, "max": 0}
    },

    "compost_buyer": {
        "id": "compost_buyer",
        "name": "Compost Product Buyer",
        "description": "Agricultural or landscaping buyer purchasing compost from municipal composting carbon credit projects.",
        "sector": "Downstream",
        "user_types": ["Farmer", "Landscaping Company", "Municipal Parks"],
        "value_chain_position": "downstream",
        "applicable_methodologies": ["AMS-III.F"],
        "recommended_methodology": "AMS-III.F",
        "scale": "Small",
        "typical_credit_range": {"min": 0, "max": 0, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "compost_purchased_tonnes_yr",
                "label": "Annual Compost Purchased",
                "description": "Tonnes of finished compost purchased per year.",
                "unit": "tonnes/year",
                "typical_range": {"min": 100, "max": 50000},
                "example_value": 5000,
                "data_sources": ["Purchase orders", "Delivery tickets", "Invoice records"],
                "required": True,
                "tooltip": "Finished compost from registered carbon credit projects."
            },
            {
                "parameter": "application_area_ha",
                "label": "Application Area",
                "description": "Land area where compost is applied.",
                "unit": "hectares",
                "typical_range": {"min": 10, "max": 5000},
                "example_value": 500,
                "data_sources": ["Farm management records", "Application logs"],
                "required": True,
                "tooltip": "Compost application also sequesters soil carbon."
            },
            {
                "parameter": "fertiliser_displaced",
                "label": "Synthetic Fertiliser Displaced",
                "description": "Quantity of synthetic fertiliser replaced by compost nutrients.",
                "unit": "kg N/year",
                "typical_range": {"min": 100, "max": 50000},
                "example_value": 5000,
                "data_sources": ["Compost nutrient analysis", "Fertiliser purchase reduction records"],
                "required": True,
                "tooltip": "Displacing synthetic N reduces N2O emissions from fertiliser."
            }
        ],
        "real_world_examples": [
            {"project": "City of San Francisco Compost Programme", "credits": 0, "year": 2023}
        ],
        "regulatory_notes": "Compost buyers support project revenue. Credits accrue to the composting facility operator.",
        "cdm_tools_needed": [],
        "estimated_cost_range_usd": {"min": 10000, "max": 1000000},
        "crediting_period_years": {"min": 0, "max": 0}
    },

    "biogas_offtaker": {
        "id": "biogas_offtaker",
        "name": "Biogas / Biomethane Offtaker",
        "description": "Utility or industrial buyer purchasing upgraded biomethane or raw biogas from anaerobic digestion carbon credit projects.",
        "sector": "Downstream",
        "user_types": ["Gas Utility", "Industrial Facility", "Transport Fleet"],
        "value_chain_position": "downstream",
        "applicable_methodologies": ["AMS-III.D", "AMS-I.D"],
        "recommended_methodology": "AMS-III.D",
        "scale": "Small",
        "typical_credit_range": {"min": 2000, "max": 30000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "biomethane_volume_m3_yr",
                "label": "Annual Biomethane Purchased",
                "description": "Volume of biomethane or biogas purchased per year.",
                "unit": "m3/year",
                "typical_range": {"min": 100000, "max": 10000000},
                "example_value": 2000000,
                "data_sources": ["Gas purchase agreement", "Meter readings", "Invoice records"],
                "required": True,
                "tooltip": "Upgraded biomethane can be injected into gas grid."
            },
            {
                "parameter": "natural_gas_displaced_m3_yr",
                "label": "Natural Gas Displaced",
                "description": "Volume of fossil natural gas displaced by biomethane.",
                "unit": "m3/year",
                "typical_range": {"min": 100000, "max": 10000000},
                "example_value": 2000000,
                "data_sources": ["Gas billing records", "Grid injection meter"],
                "required": True,
                "tooltip": "1:1 displacement when injected to grid at same spec."
            },
            {
                "parameter": "emission_factor_ng",
                "label": "Natural Gas Emission Factor",
                "description": "CO2 per m3 of natural gas displaced.",
                "unit": "kgCO2/m3",
                "typical_range": {"min": 1.8, "max": 2.2},
                "example_value": 2.0,
                "data_sources": ["IPCC default", "Gas utility emission factor"],
                "required": True,
                "tooltip": "Combustion CO2 of natural gas."
            }
        ],
        "real_world_examples": [
            {"project": "Danish Biogas Grid Injection Programme", "credits": 15000, "year": 2023}
        ],
        "regulatory_notes": "Credits may be shared between producer and offtaker depending on contract structure. Gas certificates (GOs) apply.",
        "cdm_tools_needed": [],
        "estimated_cost_range_usd": {"min": 500000, "max": 10000000},
        "crediting_period_years": {"min": 7, "max": 14}
    },

    "green_tariff_consumer": {
        "id": "green_tariff_consumer",
        "name": "Green Electricity Tariff Consumer",
        "description": "End consumer subscribing to a green electricity tariff backed by renewable energy certificates or direct renewable sourcing.",
        "sector": "Downstream",
        "user_types": ["Household", "SME", "Corporate"],
        "value_chain_position": "downstream",
        "applicable_methodologies": ["I-REC Standard", "Utility Green Tariff"],
        "recommended_methodology": "I-REC Standard",
        "scale": "Micro",
        "typical_credit_range": {"min": 0, "max": 0, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "annual_consumption_mwh",
                "label": "Annual Electricity Consumption",
                "description": "Total electricity consumed by the subscriber per year.",
                "unit": "MWh/year",
                "typical_range": {"min": 5, "max": 100000},
                "example_value": 500,
                "data_sources": ["Utility bills", "Smart meter data"],
                "required": True,
                "tooltip": "All consumption covered by the green tariff."
            },
            {
                "parameter": "tariff_premium_pct",
                "label": "Green Tariff Premium",
                "description": "Price premium above standard tariff.",
                "unit": "%",
                "typical_range": {"min": 2, "max": 30},
                "example_value": 10,
                "data_sources": ["Utility tariff schedule", "Green tariff contract"],
                "required": True,
                "tooltip": "Premium finances new RE capacity or REC procurement."
            },
            {
                "parameter": "rec_backing",
                "label": "REC Backing Standard",
                "description": "Certificate or attribute tracking standard backing the tariff.",
                "unit": "text",
                "typical_range": {"min": None, "max": None},
                "example_value": "I-REC",
                "data_sources": ["Utility disclosure", "REC registry records"],
                "required": True,
                "tooltip": "Must be backed by retired RECs for credible Scope 2 claim."
            }
        ],
        "real_world_examples": [
            {"project": "RE100 Corporate Green Tariff Subscribers", "credits": 0, "year": 2023}
        ],
        "regulatory_notes": "Green tariffs support RE deployment but do not directly generate carbon credits. Used for Scope 2 market-based reporting.",
        "cdm_tools_needed": [],
        "estimated_cost_range_usd": {"min": 1000, "max": 10000000},
        "crediting_period_years": {"min": 1, "max": 3}
    },

    # ======================================================================
    # CROSS-SECTOR  (#82 - #85)
    # ======================================================================

    "dac_facility": {
        "id": "dac_facility",
        "name": "Direct Air Capture (DAC) Facility",
        "description": "Engineered system capturing CO2 directly from ambient air for permanent geological storage or utilisation.",
        "sector": "Cross-Sector",
        "user_types": ["Technology Company", "Energy Company", "Project Developer"],
        "value_chain_position": "core",
        "applicable_methodologies": ["Puro.earth DAC", "VCS CDR methodology"],
        "recommended_methodology": "Puro.earth DAC",
        "scale": "Large",
        "typical_credit_range": {"min": 1000, "max": 1000000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "capture_capacity_tco2_yr",
                "label": "Annual CO2 Capture Capacity",
                "description": "Design capacity for CO2 removed from air per year.",
                "unit": "tCO2/year",
                "typical_range": {"min": 1000, "max": 1000000},
                "example_value": 36000,
                "data_sources": ["Plant design specification", "Process engineering report"],
                "required": True,
                "tooltip": "Gross capture; net credits deduct energy-related emissions."
            },
            {
                "parameter": "energy_source",
                "label": "Energy Source for DAC",
                "description": "Primary energy powering the capture process.",
                "unit": "text",
                "typical_range": {"min": None, "max": None},
                "example_value": "Geothermal + renewable electricity",
                "data_sources": ["Energy supply contract", "Plant design"],
                "required": True,
                "tooltip": "Low-carbon energy essential for net-negative outcome."
            },
            {
                "parameter": "storage_method",
                "label": "CO2 Storage Method",
                "description": "How captured CO2 is permanently stored.",
                "unit": "text",
                "typical_range": {"min": None, "max": None},
                "example_value": "Basalt mineralisation (CarbFix)",
                "data_sources": ["Storage site permit", "Injection monitoring data"],
                "required": True,
                "tooltip": "Geological storage or mineralisation ensures permanence."
            }
        ],
        "real_world_examples": [
            {"project": "Climeworks Orca DAC, Iceland", "credits": 4000, "year": 2023}
        ],
        "regulatory_notes": "Carbon dioxide removal (CDR) credits. Premium pricing ($300-1000/tCO2). Puro.earth is leading standard.",
        "cdm_tools_needed": [],
        "estimated_cost_range_usd": {"min": 50000000, "max": 1000000000},
        "crediting_period_years": {"min": 10, "max": 30}
    },

    "ccs_facility": {
        "id": "ccs_facility",
        "name": "Carbon Capture and Storage (CCS) Facility",
        "description": "Capture of CO2 from industrial point sources (power plants, cement, steel) and injection into geological formations.",
        "sector": "Cross-Sector",
        "user_types": ["Energy Company", "Industrial Facility", "Project Developer"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AM0027", "VCS CCS methodology"],
        "recommended_methodology": "AM0027",
        "scale": "Large",
        "typical_credit_range": {"min": 100000, "max": 5000000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "co2_captured_tonnes_yr",
                "label": "Annual CO2 Captured",
                "description": "Total CO2 captured from point source per year.",
                "unit": "tonnes CO2/year",
                "typical_range": {"min": 100000, "max": 5000000},
                "example_value": 1000000,
                "data_sources": ["Capture plant flow meters", "Amine scrubber performance data"],
                "required": True,
                "tooltip": "Gross capture; deduct energy penalty emissions."
            },
            {
                "parameter": "capture_rate",
                "label": "CO2 Capture Rate",
                "description": "Fraction of CO2 in flue gas that is captured.",
                "unit": "%",
                "typical_range": {"min": 85, "max": 99},
                "example_value": 90,
                "data_sources": ["Capture plant design", "Performance monitoring"],
                "required": True,
                "tooltip": "Technology dependent; amine scrubbing typically 90%+."
            },
            {
                "parameter": "storage_reservoir",
                "label": "Storage Reservoir Type",
                "description": "Type of geological formation used for storage.",
                "unit": "text",
                "typical_range": {"min": None, "max": None},
                "example_value": "Depleted oil reservoir",
                "data_sources": ["Storage site characterisation report", "Injection permit"],
                "required": True,
                "tooltip": "Saline aquifers, depleted oil/gas fields, or basalt formations."
            },
            {
                "parameter": "energy_penalty_pct",
                "label": "Energy Penalty",
                "description": "Additional energy consumed by the capture process as a fraction of host plant output.",
                "unit": "%",
                "typical_range": {"min": 10, "max": 30},
                "example_value": 20,
                "data_sources": ["Process engineering design", "Plant performance data"],
                "required": True,
                "tooltip": "Energy penalty reduces net emission reduction."
            }
        ],
        "real_world_examples": [
            {"project": "Quest CCS, Alberta Canada", "credits": 1200000, "year": 2023}
        ],
        "regulatory_notes": "CDM (AM0027), VCS, ACR. Requires long-term monitoring, measurement, verification (MMV) plan. EU CCS Directive.",
        "cdm_tools_needed": ["TOOL01"],
        "estimated_cost_range_usd": {"min": 500000000, "max": 5000000000},
        "crediting_period_years": {"min": 20, "max": 50}
    },

    "refrigerant_mgmt": {
        "id": "refrigerant_mgmt",
        "name": "Refrigerant Management and Destruction",
        "description": "Collection and destruction of high-GWP refrigerants (HFCs, CFCs, HCFCs) from end-of-life equipment.",
        "sector": "Cross-Sector",
        "user_types": ["Waste Company", "HVAC Contractor", "Project Developer"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-III.AB", "AM0001 variant"],
        "recommended_methodology": "AMS-III.AB",
        "scale": "Small",
        "typical_credit_range": {"min": 5000, "max": 100000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "refrigerant_collected_kg_yr",
                "label": "Annual Refrigerant Collected",
                "description": "Total mass of high-GWP refrigerant collected for destruction.",
                "unit": "kg/year",
                "typical_range": {"min": 500, "max": 50000},
                "example_value": 5000,
                "data_sources": ["Collection records", "Weigh scale records", "Chain-of-custody documentation"],
                "required": True,
                "tooltip": "Must track each batch from collection to destruction."
            },
            {
                "parameter": "refrigerant_type_gwp",
                "label": "Refrigerant Type and GWP",
                "description": "Type of refrigerant and its Global Warming Potential.",
                "unit": "text + GWP",
                "typical_range": {"min": None, "max": None},
                "example_value": "R-22 (GWP 1810), R-134a (GWP 1430)",
                "data_sources": ["Gas analysis lab report", "IPCC AR5/AR6 GWP tables"],
                "required": True,
                "tooltip": "GWP determines credit value per kg destroyed."
            },
            {
                "parameter": "destruction_efficiency",
                "label": "Destruction Efficiency",
                "description": "Fraction of refrigerant destroyed in the thermal treatment.",
                "unit": "%",
                "typical_range": {"min": 99.0, "max": 99.99},
                "example_value": 99.9,
                "data_sources": ["Destruction facility cert", "Stack test results"],
                "required": True,
                "tooltip": "Must use approved destruction technology (cement kiln, plasma arc)."
            }
        ],
        "real_world_examples": [
            {"project": "Tradewater Refrigerant Destruction, USA", "credits": 50000, "year": 2023}
        ],
        "regulatory_notes": "VCS, ACR, and Climate Action Reserve accept. Kigali Amendment driving phase-down of HFCs.",
        "cdm_tools_needed": ["TOOL01"],
        "estimated_cost_range_usd": {"min": 500000, "max": 10000000},
        "crediting_period_years": {"min": 7, "max": 14}
    },

    "flare_gas_recovery": {
        "id": "flare_gas_recovery",
        "name": "Associated Gas Flare Recovery",
        "description": "Capture and utilisation of associated petroleum gas that would otherwise be flared at oil production sites.",
        "sector": "Cross-Sector",
        "user_types": ["Oil Producer", "Gas Processor", "Project Developer"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AM0009", "AMS-III.Q"],
        "recommended_methodology": "AM0009",
        "scale": "Large",
        "typical_credit_range": {"min": 20000, "max": 300000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "gas_recovered_m3_yr",
                "label": "Annual Gas Recovered",
                "description": "Volume of associated gas captured instead of flared.",
                "unit": "m3/year",
                "typical_range": {"min": 10000000, "max": 500000000},
                "example_value": 100000000,
                "data_sources": ["Gas flow meters", "SCADA data", "Oil production records"],
                "required": True,
                "tooltip": "Measured at the gas recovery unit outlet."
            },
            {
                "parameter": "methane_content",
                "label": "Methane Content of Associated Gas",
                "description": "Volumetric fraction of methane.",
                "unit": "%",
                "typical_range": {"min": 60, "max": 95},
                "example_value": 80,
                "data_sources": ["Gas chromatography analysis", "Wellhead gas composition reports"],
                "required": True,
                "tooltip": "Higher methane = more GHG avoidance value."
            },
            {
                "parameter": "utilisation_path",
                "label": "Gas Utilisation Pathway",
                "description": "How the recovered gas is used.",
                "unit": "text",
                "typical_range": {"min": None, "max": None},
                "example_value": "Gas-to-power + gas processing plant",
                "data_sources": ["Project design document", "Gas sales agreement"],
                "required": True,
                "tooltip": "Power generation, gas pipeline injection, or LNG."
            }
        ],
        "real_world_examples": [
            {"project": "Kwale Gas Flare Recovery, Nigeria", "credits": 180000, "year": 2022}
        ],
        "regulatory_notes": "CDM (AM0009), VCS. World Bank Zero Routine Flaring initiative. Credit from avoided methane slip and CO2.",
        "cdm_tools_needed": ["TOOL01", "TOOL04"],
        "estimated_cost_range_usd": {"min": 20000000, "max": 200000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    # ======================================================================
    # MINING  (#86 - #89)
    # ======================================================================

    "coal_mine_methane_mine": {
        "id": "coal_mine_methane_mine",
        "name": "Coal Mine Methane at Active Mine",
        "description": "Capture and utilisation or flaring of coal mine methane at an operating underground coal mine.",
        "sector": "Mining",
        "user_types": ["Mining Company", "Project Developer"],
        "value_chain_position": "core",
        "applicable_methodologies": ["ACM0008", "AMS-III.L"],
        "recommended_methodology": "ACM0008",
        "scale": "Large",
        "typical_credit_range": {"min": 30000, "max": 500000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "methane_drained_m3_yr",
                "label": "Annual Methane Drained",
                "description": "Volume of methane captured via pre-drainage and post-mining wells.",
                "unit": "m3 CH4/year",
                "typical_range": {"min": 5000000, "max": 200000000},
                "example_value": 50000000,
                "data_sources": ["Gas drainage system flow meters", "SCADA records", "Mine ventilation data"],
                "required": True,
                "tooltip": "Includes pre-drainage and gob gas."
            },
            {
                "parameter": "mine_production_tonnes_yr",
                "label": "Annual Coal Production",
                "description": "Total coal output from the mine.",
                "unit": "tonnes/year",
                "typical_range": {"min": 1000000, "max": 30000000},
                "example_value": 8000000,
                "data_sources": ["Mine production records", "Weighbridge data"],
                "required": True,
                "tooltip": "Production level affects methane liberation rate."
            },
            {
                "parameter": "utilisation_method",
                "label": "Utilisation Method",
                "description": "How captured methane is used or destroyed.",
                "unit": "text",
                "typical_range": {"min": None, "max": None},
                "example_value": "CHP power generation",
                "data_sources": ["Project design document", "Power off-take contract"],
                "required": True,
                "tooltip": "Power generation is most common; pipeline injection also used."
            }
        ],
        "real_world_examples": [
            {"project": "Sihe Coal Mine CMM, Shanxi China", "credits": 350000, "year": 2022}
        ],
        "regulatory_notes": "CDM (ACM0008), VCS. Must demonstrate methane would have been vented. GWP 28 for CH4.",
        "cdm_tools_needed": ["TOOL01", "TOOL04"],
        "estimated_cost_range_usd": {"min": 15000000, "max": 100000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    "mine_renewable": {
        "id": "mine_renewable",
        "name": "Renewable Energy at Mine Site",
        "description": "Installation of solar PV, wind, or hybrid renewable systems at mining operations to displace diesel generation.",
        "sector": "Mining",
        "user_types": ["Mining Company", "ESCO"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-I.D", "AMS-I.F"],
        "recommended_methodology": "AMS-I.D",
        "scale": "Small",
        "typical_credit_range": {"min": 2000, "max": 30000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "installed_capacity_mwp",
                "label": "Installed RE Capacity",
                "description": "Peak capacity of renewable energy installation at the mine.",
                "unit": "MWp",
                "typical_range": {"min": 1, "max": 100},
                "example_value": 20,
                "data_sources": ["Module/turbine datasheets", "EPC contract"],
                "required": True,
                "tooltip": "Solar, wind, or hybrid system at mine site."
            },
            {
                "parameter": "diesel_displaced_litres_yr",
                "label": "Annual Diesel Displaced",
                "description": "Litres of diesel no longer consumed for mine power.",
                "unit": "litres/year",
                "typical_range": {"min": 500000, "max": 20000000},
                "example_value": 5000000,
                "data_sources": ["Baseline diesel purchase records", "Post-project fuel records", "RE generation data"],
                "required": True,
                "tooltip": "Net diesel savings after accounting for RE generation."
            },
            {
                "parameter": "mine_location",
                "label": "Mine Location",
                "description": "Geographic location and grid connectivity status.",
                "unit": "text",
                "typical_range": {"min": None, "max": None},
                "example_value": "Remote off-grid site, Sub-Saharan Africa",
                "data_sources": ["Mine location coordinates", "Grid connection status"],
                "required": True,
                "tooltip": "Off-grid mines have stronger additionality case."
            }
        ],
        "real_world_examples": [
            {"project": "B2Gold Fekola Solar, Mali", "credits": 15000, "year": 2023}
        ],
        "regulatory_notes": "VCS, Gold Standard. Off-grid mines displacing diesel have high emission factors (~0.8 tCO2/MWh for diesel gensets).",
        "cdm_tools_needed": ["TOOL01"],
        "estimated_cost_range_usd": {"min": 5000000, "max": 100000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    "mine_rehab_reforest": {
        "id": "mine_rehab_reforest",
        "name": "Mine Site Rehabilitation and Reforestation",
        "description": "Reforestation and ecological restoration of closed or exhausted mine sites to sequester carbon.",
        "sector": "Mining",
        "user_types": ["Mining Company", "Government", "NGO"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AR-ACM0003", "VM0047"],
        "recommended_methodology": "VM0047",
        "scale": "Small",
        "typical_credit_range": {"min": 1000, "max": 30000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "rehabilitation_area_ha",
                "label": "Rehabilitation Area",
                "description": "Total area of mine land rehabilitated and planted.",
                "unit": "hectares",
                "typical_range": {"min": 50, "max": 5000},
                "example_value": 500,
                "data_sources": ["Mine closure plan", "GIS mapping", "Rehabilitation records"],
                "required": True,
                "tooltip": "Disturbed mine land (pits, overburden dumps, tailings)."
            },
            {
                "parameter": "species_planted",
                "label": "Species Planted",
                "description": "Tree and vegetation species used for rehabilitation.",
                "unit": "text",
                "typical_range": {"min": None, "max": None},
                "example_value": "Native woodland mix (20+ species)",
                "data_sources": ["Rehabilitation plan", "Nursery records"],
                "required": True,
                "tooltip": "Native species preferred for biodiversity co-benefits."
            },
            {
                "parameter": "carbon_seq_rate_tco2_ha_yr",
                "label": "Carbon Sequestration Rate",
                "description": "Annual CO2 sequestration per hectare of rehabilitated land.",
                "unit": "tCO2e/ha/year",
                "typical_range": {"min": 3, "max": 15},
                "example_value": 8,
                "data_sources": ["Growth monitoring plots", "Allometric equations", "Literature values"],
                "required": True,
                "tooltip": "Mine soils may have lower initial growth rates."
            }
        ],
        "real_world_examples": [
            {"project": "Anglo American Mine Rehabilitation, South Africa", "credits": 5000, "year": 2023}
        ],
        "regulatory_notes": "VCS (VM0047), Plan Vivo. Mine closure obligations may affect additionality argument.",
        "cdm_tools_needed": ["TOOL14"],
        "estimated_cost_range_usd": {"min": 1000000, "max": 20000000},
        "crediting_period_years": {"min": 20, "max": 40}
    },

    "mineral_waste_heat": {
        "id": "mineral_waste_heat",
        "name": "Mineral Processing Waste Heat Recovery",
        "description": "Recovery of waste heat from mineral processing (smelting, refining, calcining) for power generation or process use.",
        "sector": "Mining",
        "user_types": ["Mining Company", "Smelter Operator", "ESCO"],
        "value_chain_position": "core",
        "applicable_methodologies": ["ACM0012", "AMS-III.Q"],
        "recommended_methodology": "ACM0012",
        "scale": "Large",
        "typical_credit_range": {"min": 5000, "max": 100000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "thermal_input_mw",
                "label": "Waste Heat Available",
                "description": "Thermal energy available from smelting/processing exhaust.",
                "unit": "MWth",
                "typical_range": {"min": 5, "max": 100},
                "example_value": 30,
                "data_sources": ["Process heat balance", "Exhaust gas measurements"],
                "required": True,
                "tooltip": "Temperature and flow rate determine recoverable energy."
            },
            {
                "parameter": "electricity_generated_mwh_yr",
                "label": "Annual Electricity Generated",
                "description": "Electricity produced from recovered waste heat.",
                "unit": "MWh/year",
                "typical_range": {"min": 10000, "max": 300000},
                "example_value": 80000,
                "data_sources": ["Generator meter readings", "WHR system performance data"],
                "required": True,
                "tooltip": "Net of WHR system parasitic loads."
            },
            {
                "parameter": "grid_emission_factor",
                "label": "Grid Emission Factor",
                "description": "CO2 intensity of displaced grid or on-site fossil electricity.",
                "unit": "tCO2/MWh",
                "typical_range": {"min": 0.4, "max": 1.2},
                "example_value": 0.9,
                "data_sources": ["National grid authority", "On-site diesel genset EF"],
                "required": True,
                "tooltip": "If off-grid, use diesel genset emission factor."
            }
        ],
        "real_world_examples": [
            {"project": "Hindustan Zinc Smelter WHR, Rajasthan", "credits": 55000, "year": 2023}
        ],
        "regulatory_notes": "CDM (ACM0012), VCS. Must demonstrate heat was previously wasted.",
        "cdm_tools_needed": ["TOOL01", "TOOL07"],
        "estimated_cost_range_usd": {"min": 10000000, "max": 80000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    # ======================================================================
    # TEXTILES  (#90 - #92)
    # ======================================================================

    "textile_ee": {
        "id": "textile_ee",
        "name": "Textile Mill Energy Efficiency",
        "description": "Energy efficiency improvements in textile spinning, weaving, and finishing mills reducing electricity and steam consumption.",
        "sector": "Textiles",
        "user_types": ["Textile Manufacturer", "ESCO"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-II.D", "AMS-II.C"],
        "recommended_methodology": "AMS-II.D",
        "scale": "Small",
        "typical_credit_range": {"min": 1000, "max": 15000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "baseline_sec_kwh_kg",
                "label": "Baseline Specific Energy Consumption",
                "description": "Electricity consumed per kg of textile output before upgrades.",
                "unit": "kWh/kg",
                "typical_range": {"min": 2, "max": 8},
                "example_value": 5,
                "data_sources": ["Energy audit report", "Utility bills", "Production records"],
                "required": True,
                "tooltip": "SEC varies by textile process (spinning vs weaving vs finishing)."
            },
            {
                "parameter": "project_sec_kwh_kg",
                "label": "Project Specific Energy Consumption",
                "description": "Reduced electricity per kg after efficiency upgrades.",
                "unit": "kWh/kg",
                "typical_range": {"min": 1.5, "max": 6},
                "example_value": 3.5,
                "data_sources": ["Post-retrofit metered data", "M&V report"],
                "required": True,
                "tooltip": "Normalised for product mix and production volume."
            },
            {
                "parameter": "annual_production_tonnes",
                "label": "Annual Textile Production",
                "description": "Total textile output per year.",
                "unit": "tonnes/year",
                "typical_range": {"min": 1000, "max": 100000},
                "example_value": 20000,
                "data_sources": ["Production records", "Sales data"],
                "required": True,
                "tooltip": "Used to calculate total energy savings."
            }
        ],
        "real_world_examples": [
            {"project": "Arvind Mills EE Programme, Gujarat India", "credits": 8000, "year": 2023}
        ],
        "regulatory_notes": "CDM (AMS-II.D), VCS. M&V per IPMVP. Can be bundled across multiple mills.",
        "cdm_tools_needed": ["TOOL01", "TOOL07"],
        "estimated_cost_range_usd": {"min": 500000, "max": 10000000},
        "crediting_period_years": {"min": 7, "max": 14}
    },

    "garment_solar": {
        "id": "garment_solar",
        "name": "Garment Factory Rooftop Solar",
        "description": "Installation of rooftop solar PV on garment manufacturing factories in developing countries.",
        "sector": "Textiles",
        "user_types": ["Garment Manufacturer", "Brand Supplier"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-I.D", "AMS-I.F"],
        "recommended_methodology": "AMS-I.D",
        "scale": "Small",
        "typical_credit_range": {"min": 500, "max": 8000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "installed_capacity_kwp",
                "label": "Installed Capacity",
                "description": "Peak DC capacity of rooftop solar system.",
                "unit": "kWp",
                "typical_range": {"min": 100, "max": 3000},
                "example_value": 500,
                "data_sources": ["Module datasheets", "Installation contract"],
                "required": True,
                "tooltip": "Sized to factory roof area and electricity demand."
            },
            {
                "parameter": "annual_generation_kwh",
                "label": "Annual Generation",
                "description": "Electricity generated by the rooftop system per year.",
                "unit": "kWh/year",
                "typical_range": {"min": 120000, "max": 4500000},
                "example_value": 750000,
                "data_sources": ["Inverter monitoring", "Grid meter data"],
                "required": True,
                "tooltip": "Net of inverter and cable losses."
            },
            {
                "parameter": "grid_emission_factor",
                "label": "Grid Emission Factor",
                "description": "CO2 intensity of displaced grid electricity.",
                "unit": "tCO2/MWh",
                "typical_range": {"min": 0.4, "max": 1.2},
                "example_value": 0.9,
                "data_sources": ["National grid authority", "IFI Harmonized Grid EF"],
                "required": True,
                "tooltip": "Bangladesh, Vietnam, Cambodia have high grid EFs."
            }
        ],
        "real_world_examples": [
            {"project": "H&M Supplier Solar Programme, Bangladesh", "credits": 3500, "year": 2023}
        ],
        "regulatory_notes": "CDM, VCS, Gold Standard. Brands use to reduce Scope 3 supply chain emissions.",
        "cdm_tools_needed": ["TOOL01", "TOOL07"],
        "estimated_cost_range_usd": {"min": 100000, "max": 2000000},
        "crediting_period_years": {"min": 7, "max": 14}
    },

    "dyeing_heat_recovery": {
        "id": "dyeing_heat_recovery",
        "name": "Textile Dyeing Heat Recovery",
        "description": "Recovery of waste heat from textile dyeing and finishing processes, reducing boiler fuel consumption.",
        "sector": "Textiles",
        "user_types": ["Textile Manufacturer", "Dyehouse Operator", "ESCO"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-III.Q", "AMS-II.D"],
        "recommended_methodology": "AMS-III.Q",
        "scale": "Small",
        "typical_credit_range": {"min": 500, "max": 10000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "heat_recovered_tj_yr",
                "label": "Annual Heat Recovered",
                "description": "Thermal energy recovered from dyeing effluent or exhaust.",
                "unit": "TJ/year",
                "typical_range": {"min": 5, "max": 100},
                "example_value": 20,
                "data_sources": ["Heat exchanger monitoring", "Boiler fuel reduction records"],
                "required": True,
                "tooltip": "Recovered from hot effluent, steam condensate, or dryer exhaust."
            },
            {
                "parameter": "baseline_fuel_type",
                "label": "Baseline Boiler Fuel",
                "description": "Fossil fuel used in boilers before heat recovery.",
                "unit": "text",
                "typical_range": {"min": None, "max": None},
                "example_value": "Coal",
                "data_sources": ["Fuel purchase records", "Boiler log books"],
                "required": True,
                "tooltip": "Coal displacement generates more credits than gas."
            },
            {
                "parameter": "fuel_saved_tonnes_yr",
                "label": "Annual Fuel Saved",
                "description": "Quantity of fossil fuel saved by heat recovery.",
                "unit": "tonnes/year",
                "typical_range": {"min": 500, "max": 10000},
                "example_value": 3000,
                "data_sources": ["Fuel purchase records (before vs after)", "Boiler efficiency tests"],
                "required": True,
                "tooltip": "Measured from fuel consumption reduction."
            }
        ],
        "real_world_examples": [
            {"project": "Surat Textile Cluster Heat Recovery, India", "credits": 6000, "year": 2023}
        ],
        "regulatory_notes": "CDM, VCS. Common in textile clusters in South Asia. Can be bundled across multiple dyehouses.",
        "cdm_tools_needed": ["TOOL01"],
        "estimated_cost_range_usd": {"min": 200000, "max": 5000000},
        "crediting_period_years": {"min": 7, "max": 14}
    },

    # ======================================================================
    # FOOD & BEVERAGE  (#93 - #96)
    # ======================================================================

    "brewery_biogas": {
        "id": "brewery_biogas",
        "name": "Brewery Wastewater Biogas Recovery",
        "description": "Capture and use of biogas from brewery wastewater treatment, displacing fossil fuel for heat or power.",
        "sector": "Food & Beverage",
        "user_types": ["Brewery", "Food Manufacturer"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-III.H", "AMS-I.D"],
        "recommended_methodology": "AMS-III.H",
        "scale": "Small",
        "typical_credit_range": {"min": 2000, "max": 20000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "beer_production_hl_yr",
                "label": "Annual Beer Production",
                "description": "Total hectolitres of beer produced per year.",
                "unit": "hl/year",
                "typical_range": {"min": 100000, "max": 10000000},
                "example_value": 2000000,
                "data_sources": ["Production records", "Excise duty records"],
                "required": True,
                "tooltip": "Determines wastewater volume and COD load."
            },
            {
                "parameter": "cod_load_kg_yr",
                "label": "Annual COD Load",
                "description": "Chemical oxygen demand of brewery effluent.",
                "unit": "kg COD/year",
                "typical_range": {"min": 500000, "max": 20000000},
                "example_value": 5000000,
                "data_sources": ["Effluent lab analysis", "WWTP monitoring records"],
                "required": True,
                "tooltip": "Typical brewery COD is 3-5 kg per hl of beer."
            },
            {
                "parameter": "biogas_captured_m3_yr",
                "label": "Annual Biogas Captured",
                "description": "Biogas volume captured from the anaerobic treatment system.",
                "unit": "m3/year",
                "typical_range": {"min": 200000, "max": 5000000},
                "example_value": 1500000,
                "data_sources": ["Gas flow meter", "UASB reactor monitoring"],
                "required": True,
                "tooltip": "UASB reactors are most common in brewery wastewater."
            }
        ],
        "real_world_examples": [
            {"project": "AB InBev Brewery Biogas, Tanzania", "credits": 8000, "year": 2023}
        ],
        "regulatory_notes": "CDM (AMS-III.H), VCS, Gold Standard. Common application in developing country breweries.",
        "cdm_tools_needed": ["TOOL01", "TOOL04"],
        "estimated_cost_range_usd": {"min": 1000000, "max": 10000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    "food_composting": {
        "id": "food_composting",
        "name": "Food Processing Waste Composting",
        "description": "Composting of food processing waste (fruit peels, pulp, trimmings) avoiding methane emissions from landfill disposal.",
        "sector": "Food & Beverage",
        "user_types": ["Food Processor", "Waste Company"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-III.F", "AMS-III.E"],
        "recommended_methodology": "AMS-III.F",
        "scale": "Small",
        "typical_credit_range": {"min": 1000, "max": 15000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "organic_waste_tonnes_yr",
                "label": "Annual Organic Waste Composted",
                "description": "Tonnes of food processing waste composted per year.",
                "unit": "tonnes/year",
                "typical_range": {"min": 2000, "max": 100000},
                "example_value": 15000,
                "data_sources": ["Weigh bridge records", "Waste manifests", "Production by-product records"],
                "required": True,
                "tooltip": "Wet weight of organic waste diverted from landfill."
            },
            {
                "parameter": "waste_doc_fraction",
                "label": "Degradable Organic Carbon Fraction",
                "description": "DOC content of the food processing waste.",
                "unit": "fraction",
                "typical_range": {"min": 0.10, "max": 0.25},
                "example_value": 0.18,
                "data_sources": ["Waste composition analysis", "IPCC defaults for food waste"],
                "required": True,
                "tooltip": "Higher for fruit/vegetable waste; lower for grain residues."
            },
            {
                "parameter": "methane_correction_factor",
                "label": "MCF for Baseline Disposal",
                "description": "Methane correction factor for the landfill receiving waste in baseline.",
                "unit": "fraction",
                "typical_range": {"min": 0.4, "max": 1.0},
                "example_value": 0.8,
                "data_sources": ["IPCC defaults by landfill type"],
                "required": True,
                "tooltip": "Higher MCF = more methane avoided = more credits."
            }
        ],
        "real_world_examples": [
            {"project": "Del Monte Food Waste Composting, Kenya", "credits": 7000, "year": 2023}
        ],
        "regulatory_notes": "CDM (AMS-III.F), VCS, Gold Standard. Must prove waste would have gone to landfill.",
        "cdm_tools_needed": ["TOOL01", "TOOL04"],
        "estimated_cost_range_usd": {"min": 500000, "max": 5000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    "palm_oil_methane": {
        "id": "palm_oil_methane",
        "name": "Palm Oil Mill Methane Capture",
        "description": "Capture and use of methane from palm oil mill effluent (POME) that would otherwise be released from open lagoons.",
        "sector": "Food & Beverage",
        "user_types": ["Palm Oil Mill", "Agribusiness", "Project Developer"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-III.H", "ACM0014"],
        "recommended_methodology": "AMS-III.H",
        "scale": "Small",
        "typical_credit_range": {"min": 10000, "max": 100000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "ffb_processed_tonnes_yr",
                "label": "Fresh Fruit Bunches Processed",
                "description": "Annual tonnage of FFB processed by the mill.",
                "unit": "tonnes/year",
                "typical_range": {"min": 50000, "max": 1000000},
                "example_value": 300000,
                "data_sources": ["Mill production records", "Weigh bridge data"],
                "required": True,
                "tooltip": "FFB throughput drives POME volume and methane generation."
            },
            {
                "parameter": "pome_volume_m3_yr",
                "label": "Annual POME Volume",
                "description": "Volume of palm oil mill effluent produced per year.",
                "unit": "m3/year",
                "typical_range": {"min": 30000, "max": 600000},
                "example_value": 180000,
                "data_sources": ["Mill effluent monitoring", "POME flow meters"],
                "required": True,
                "tooltip": "Typical ratio: 0.6-0.7 m3 POME per tonne FFB."
            },
            {
                "parameter": "methane_captured_m3_yr",
                "label": "Annual Methane Captured",
                "description": "Volume of methane captured from covered lagoons or CSTR.",
                "unit": "m3 CH4/year",
                "typical_range": {"min": 500000, "max": 15000000},
                "example_value": 5000000,
                "data_sources": ["Gas flow meter readings", "Biogas plant monitoring system"],
                "required": True,
                "tooltip": "POME generates 12-20 m3 biogas per m3 POME."
            }
        ],
        "real_world_examples": [
            {"project": "Wilmar POME Biogas, Sumatra Indonesia", "credits": 70000, "year": 2023}
        ],
        "regulatory_notes": "CDM (AMS-III.H), VCS. One of the most common CDM project types in Southeast Asia.",
        "cdm_tools_needed": ["TOOL01", "TOOL04"],
        "estimated_cost_range_usd": {"min": 2000000, "max": 15000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    "sugar_bagasse": {
        "id": "sugar_bagasse",
        "name": "Sugar Mill Bagasse Cogeneration",
        "description": "High-pressure cogeneration in sugar mills burning bagasse to export surplus electricity to the grid.",
        "sector": "Food & Beverage",
        "user_types": ["Sugar Mill", "Agribusiness"],
        "value_chain_position": "core",
        "applicable_methodologies": ["ACM0006", "AMS-I.C"],
        "recommended_methodology": "ACM0006",
        "scale": "Large",
        "typical_credit_range": {"min": 10000, "max": 80000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "cane_crushed_tonnes_yr",
                "label": "Annual Cane Crushed",
                "description": "Total sugarcane processed by the mill per year.",
                "unit": "tonnes/year",
                "typical_range": {"min": 500000, "max": 5000000},
                "example_value": 2000000,
                "data_sources": ["Mill production records", "Cane receipts"],
                "required": True,
                "tooltip": "Determines bagasse availability (~30% of cane weight)."
            },
            {
                "parameter": "surplus_electricity_mwh_yr",
                "label": "Surplus Electricity Exported to Grid",
                "description": "Electricity exported beyond mill self-consumption.",
                "unit": "MWh/year",
                "typical_range": {"min": 20000, "max": 300000},
                "example_value": 100000,
                "data_sources": ["Grid export meter", "PPA billing records"],
                "required": True,
                "tooltip": "Only surplus beyond mill process needs generates credits."
            },
            {
                "parameter": "grid_emission_factor",
                "label": "Grid Emission Factor",
                "description": "CO2 intensity of displaced grid electricity.",
                "unit": "tCO2/MWh",
                "typical_range": {"min": 0.4, "max": 1.2},
                "example_value": 0.85,
                "data_sources": ["National grid authority", "IFI Harmonized Grid EF database"],
                "required": True,
                "tooltip": "Applied to surplus export volume."
            }
        ],
        "real_world_examples": [
            {"project": "Mumias Sugar Cogeneration, Kenya", "credits": 45000, "year": 2023}
        ],
        "regulatory_notes": "CDM (ACM0006), VCS. Common in India, Brazil, Sub-Saharan Africa. High-pressure boiler upgrade is the key investment.",
        "cdm_tools_needed": ["TOOL01", "TOOL07", "TOOL16"],
        "estimated_cost_range_usd": {"min": 20000000, "max": 100000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    # ======================================================================
    # HEALTHCARE  (#97 - #99)
    # ======================================================================

    "hospital_ee": {
        "id": "hospital_ee",
        "name": "Hospital Energy Efficiency Programme",
        "description": "Comprehensive energy efficiency upgrades in hospitals (HVAC, lighting, medical equipment, building envelope).",
        "sector": "Healthcare",
        "user_types": ["Hospital", "ESCO", "Healthcare Chain"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-II.C", "AMS-II.E"],
        "recommended_methodology": "AMS-II.C",
        "scale": "Small",
        "typical_credit_range": {"min": 500, "max": 10000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "baseline_energy_mwh_yr",
                "label": "Baseline Energy Consumption",
                "description": "Annual electricity and thermal energy before efficiency upgrades.",
                "unit": "MWh/year",
                "typical_range": {"min": 5000, "max": 100000},
                "example_value": 20000,
                "data_sources": ["Utility bills", "BMS data", "Energy audit report"],
                "required": True,
                "tooltip": "Hospitals operate 24/7 with high energy intensity."
            },
            {
                "parameter": "energy_saved_mwh_yr",
                "label": "Annual Energy Savings",
                "description": "Energy reduction achieved through efficiency measures.",
                "unit": "MWh/year",
                "typical_range": {"min": 1000, "max": 30000},
                "example_value": 5000,
                "data_sources": ["Post-retrofit metered data", "M&V report"],
                "required": True,
                "tooltip": "Typical hospital EE programmes achieve 15-30% savings."
            },
            {
                "parameter": "grid_emission_factor",
                "label": "Grid Emission Factor",
                "description": "CO2 intensity of electricity saved.",
                "unit": "tCO2/MWh",
                "typical_range": {"min": 0.4, "max": 1.2},
                "example_value": 0.85,
                "data_sources": ["National grid authority", "IFI Harmonized Grid EF database"],
                "required": True,
                "tooltip": "Applied to electricity savings."
            }
        ],
        "real_world_examples": [
            {"project": "Apollo Hospitals EE Programme, India", "credits": 4000, "year": 2023}
        ],
        "regulatory_notes": "CDM, VCS, Gold Standard. Must maintain medical service levels while reducing energy.",
        "cdm_tools_needed": ["TOOL01", "TOOL07"],
        "estimated_cost_range_usd": {"min": 500000, "max": 10000000},
        "crediting_period_years": {"min": 7, "max": 14}
    },

    "pharma_waste_heat": {
        "id": "pharma_waste_heat",
        "name": "Pharmaceutical Plant Waste Heat Recovery",
        "description": "Recovery of waste heat from pharmaceutical manufacturing processes (drying, distillation, sterilisation) for reuse.",
        "sector": "Healthcare",
        "user_types": ["Pharmaceutical Manufacturer", "ESCO"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-III.Q", "AMS-II.D"],
        "recommended_methodology": "AMS-III.Q",
        "scale": "Small",
        "typical_credit_range": {"min": 1000, "max": 15000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "heat_recovered_tj_yr",
                "label": "Annual Heat Recovered",
                "description": "Thermal energy recovered from pharma processes.",
                "unit": "TJ/year",
                "typical_range": {"min": 5, "max": 50},
                "example_value": 15,
                "data_sources": ["Heat exchanger monitoring", "Process energy balance"],
                "required": True,
                "tooltip": "From solvent recovery, steam condensate, dryer exhaust."
            },
            {
                "parameter": "fuel_displaced_type",
                "label": "Displaced Fuel Type",
                "description": "Fossil fuel displaced by waste heat recovery.",
                "unit": "text",
                "typical_range": {"min": None, "max": None},
                "example_value": "Natural gas",
                "data_sources": ["Fuel purchase records", "Boiler logs"],
                "required": True,
                "tooltip": "Gas or coal displacement."
            },
            {
                "parameter": "fuel_saved_tonnes_yr",
                "label": "Annual Fuel Saved",
                "description": "Quantity of fossil fuel saved.",
                "unit": "tonnes/year",
                "typical_range": {"min": 200, "max": 5000},
                "example_value": 1000,
                "data_sources": ["Fuel purchase before vs after", "M&V report"],
                "required": True,
                "tooltip": "Verified through fuel consumption records."
            }
        ],
        "real_world_examples": [
            {"project": "Dr Reddys Pharma WHR, Hyderabad", "credits": 5000, "year": 2023}
        ],
        "regulatory_notes": "CDM, VCS. Pharma plants have significant steam demand, making WHR attractive.",
        "cdm_tools_needed": ["TOOL01"],
        "estimated_cost_range_usd": {"min": 1000000, "max": 10000000},
        "crediting_period_years": {"min": 7, "max": 14}
    },

    "medical_waste_methane": {
        "id": "medical_waste_methane",
        "name": "Medical Waste Treatment Methane Avoidance",
        "description": "Improved medical waste treatment (autoclaving, microwave) replacing open burning or landfill, avoiding methane and toxic emissions.",
        "sector": "Healthcare",
        "user_types": ["Hospital", "Waste Company", "Municipal Authority"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-III.E", "AMS-III.F"],
        "recommended_methodology": "AMS-III.E",
        "scale": "Small",
        "typical_credit_range": {"min": 500, "max": 8000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "medical_waste_tonnes_yr",
                "label": "Annual Medical Waste Treated",
                "description": "Tonnes of medical waste treated through improved methods.",
                "unit": "tonnes/year",
                "typical_range": {"min": 500, "max": 20000},
                "example_value": 3000,
                "data_sources": ["Waste manifests", "Treatment facility records", "Hospital waste audit"],
                "required": True,
                "tooltip": "Segregated medical waste only; excludes general waste."
            },
            {
                "parameter": "baseline_disposal_method",
                "label": "Baseline Disposal Method",
                "description": "How medical waste was disposed of before the project.",
                "unit": "text",
                "typical_range": {"min": None, "max": None},
                "example_value": "Open pit burning + unlined landfill",
                "data_sources": ["Pre-project waste management assessment"],
                "required": True,
                "tooltip": "Open burning and unlined landfill generate highest baseline emissions."
            },
            {
                "parameter": "organic_fraction",
                "label": "Organic Fraction of Medical Waste",
                "description": "Percentage of medical waste that is organic/biodegradable.",
                "unit": "%",
                "typical_range": {"min": 20, "max": 50},
                "example_value": 35,
                "data_sources": ["Waste composition study", "Published healthcare waste data"],
                "required": True,
                "tooltip": "Organic fraction drives methane generation in landfill baseline."
            }
        ],
        "real_world_examples": [
            {"project": "Nairobi Hospital Waste Treatment, Kenya", "credits": 2500, "year": 2023}
        ],
        "regulatory_notes": "CDM, VCS, Gold Standard. Co-benefits include reduced air pollution and infection risk.",
        "cdm_tools_needed": ["TOOL01", "TOOL04"],
        "estimated_cost_range_usd": {"min": 500000, "max": 5000000},
        "crediting_period_years": {"min": 7, "max": 14}
    },

    # ======================================================================
    # REAL ESTATE  (#100 - #102)
    # ======================================================================

    "green_building_portfolio": {
        "id": "green_building_portfolio",
        "name": "Green Building Portfolio Programme",
        "description": "Portfolio-wide green building certification and EE retrofit programme across multiple commercial or residential buildings.",
        "sector": "Real Estate",
        "user_types": ["REIT", "Property Developer", "Building Portfolio Manager"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-II.E", "AMS-II.C"],
        "recommended_methodology": "AMS-II.E",
        "scale": "Large",
        "typical_credit_range": {"min": 5000, "max": 50000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "portfolio_gfa_sqm",
                "label": "Total Portfolio Gross Floor Area",
                "description": "Aggregate GFA across all buildings in the programme.",
                "unit": "m2",
                "typical_range": {"min": 100000, "max": 10000000},
                "example_value": 1000000,
                "data_sources": ["Property management database", "Building permits", "GRESB submission"],
                "required": True,
                "tooltip": "Sum of all buildings in the green programme."
            },
            {
                "parameter": "avg_energy_reduction_pct",
                "label": "Average Energy Reduction",
                "description": "Average percentage energy saving across the portfolio.",
                "unit": "%",
                "typical_range": {"min": 10, "max": 40},
                "example_value": 25,
                "data_sources": ["Building-level energy data", "Green certification scorecards", "M&V reports"],
                "required": True,
                "tooltip": "Against code-compliant or historical baseline."
            },
            {
                "parameter": "grid_emission_factor",
                "label": "Weighted Average Grid EF",
                "description": "Portfolio-weighted grid emission factor.",
                "unit": "tCO2/MWh",
                "typical_range": {"min": 0.3, "max": 1.0},
                "example_value": 0.7,
                "data_sources": ["Grid authorities for each location"],
                "required": True,
                "tooltip": "Weighted by building energy consumption."
            }
        ],
        "real_world_examples": [
            {"project": "IFC EDGE Green Building Portfolio, India", "credits": 25000, "year": 2023}
        ],
        "regulatory_notes": "VCS, Gold Standard. GRESB score improvements often correlate with credit volumes.",
        "cdm_tools_needed": ["TOOL01"],
        "estimated_cost_range_usd": {"min": 10000000, "max": 500000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    "cement_plant_ee": {
        "id": "cement_plant_ee",
        "name": "Cement Plant Energy Efficiency (Real Estate Supply Chain)",
        "description": "Energy efficiency improvements at cement plants supplying construction materials, reducing embodied carbon in buildings.",
        "sector": "Real Estate",
        "user_types": ["Cement Manufacturer", "ESCO"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-II.D", "ACM0012"],
        "recommended_methodology": "AMS-II.D",
        "scale": "Large",
        "typical_credit_range": {"min": 10000, "max": 100000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "baseline_sec_kwh_t",
                "label": "Baseline Specific Electrical Energy",
                "description": "Electricity per tonne of cement before upgrades.",
                "unit": "kWh/tonne",
                "typical_range": {"min": 90, "max": 130},
                "example_value": 110,
                "data_sources": ["Energy audit", "Production and electricity records"],
                "required": True,
                "tooltip": "Grinding, fans, and material handling dominate electrical use."
            },
            {
                "parameter": "project_sec_kwh_t",
                "label": "Project Specific Electrical Energy",
                "description": "Electricity per tonne after efficiency measures.",
                "unit": "kWh/tonne",
                "typical_range": {"min": 70, "max": 100},
                "example_value": 85,
                "data_sources": ["Post-retrofit production and electricity data"],
                "required": True,
                "tooltip": "VFDs on fans and roller presses are common upgrades."
            },
            {
                "parameter": "cement_production_tonnes_yr",
                "label": "Annual Cement Production",
                "description": "Total cement production per year.",
                "unit": "tonnes/year",
                "typical_range": {"min": 500000, "max": 10000000},
                "example_value": 3000000,
                "data_sources": ["Production records", "Sales data"],
                "required": True,
                "tooltip": "Used to calculate total energy savings."
            }
        ],
        "real_world_examples": [
            {"project": "UltraTech Cement EE, India", "credits": 60000, "year": 2023}
        ],
        "regulatory_notes": "CDM, VCS. Cement sector is a key contributor to Scope 3 embodied carbon in real estate.",
        "cdm_tools_needed": ["TOOL01", "TOOL07"],
        "estimated_cost_range_usd": {"min": 5000000, "max": 50000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    "district_cooling": {
        "id": "district_cooling",
        "name": "District Cooling System",
        "description": "Centralised chilled water production and distribution to multiple buildings, replacing inefficient individual building chillers.",
        "sector": "Real Estate",
        "user_types": ["Utility", "District Developer", "ESCO"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-II.C", "AMS-III.AE"],
        "recommended_methodology": "AMS-II.C",
        "scale": "Large",
        "typical_credit_range": {"min": 5000, "max": 60000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "cooling_capacity_mwth",
                "label": "District Cooling Capacity",
                "description": "Total cooling capacity of the central plant.",
                "unit": "MWth",
                "typical_range": {"min": 10, "max": 500},
                "example_value": 100,
                "data_sources": ["Chiller plant spec", "EPC contract", "Connection agreements"],
                "required": True,
                "tooltip": "Sum of all central chiller capacity."
            },
            {
                "parameter": "connected_gfa_sqm",
                "label": "Connected Building Floor Area",
                "description": "Total GFA of buildings connected to the district cooling network.",
                "unit": "m2",
                "typical_range": {"min": 100000, "max": 5000000},
                "example_value": 1000000,
                "data_sources": ["Connection agreements", "Building permits"],
                "required": True,
                "tooltip": "More connections improve system load factor and efficiency."
            },
            {
                "parameter": "cop_improvement",
                "label": "COP Improvement over Baseline",
                "description": "Efficiency gain of district cooling vs individual building chillers.",
                "unit": "ratio",
                "typical_range": {"min": 1.2, "max": 2.5},
                "example_value": 1.6,
                "data_sources": ["Central plant performance data", "Baseline chiller efficiency survey"],
                "required": True,
                "tooltip": "District systems achieve higher COP through scale, thermal storage, and optimisation."
            }
        ],
        "real_world_examples": [
            {"project": "Dubai District Cooling, UAE", "credits": 35000, "year": 2023}
        ],
        "regulatory_notes": "CDM, VCS. Common in GCC countries and tropical cities. Must compare with baseline individual chillers.",
        "cdm_tools_needed": ["TOOL01", "TOOL07"],
        "estimated_cost_range_usd": {"min": 50000000, "max": 500000000},
        "crediting_period_years": {"min": 7, "max": 21}
    },

    # ======================================================================
    # TECHNOLOGY  (#103 - #105)
    # ======================================================================

    "datacenter_re_ppa": {
        "id": "datacenter_re_ppa",
        "name": "Data Centre Renewable Energy PPA",
        "description": "Procurement of 100% renewable electricity for data centres through corporate PPAs and RECs.",
        "sector": "Technology",
        "user_types": ["Data Centre Operator", "Cloud Provider", "Corporate"],
        "value_chain_position": "core",
        "applicable_methodologies": ["ACM0002", "AMS-I.D"],
        "recommended_methodology": "ACM0002",
        "scale": "Large",
        "typical_credit_range": {"min": 10000, "max": 200000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "it_load_mw",
                "label": "Data Centre IT Load",
                "description": "Total IT power demand of the data centre.",
                "unit": "MW",
                "typical_range": {"min": 5, "max": 200},
                "example_value": 50,
                "data_sources": ["Power monitoring system", "UPS metering", "Colocation contracts"],
                "required": True,
                "tooltip": "IT load determines total electricity demand."
            },
            {
                "parameter": "pue",
                "label": "Power Usage Effectiveness (PUE)",
                "description": "Ratio of total facility energy to IT equipment energy.",
                "unit": "ratio",
                "typical_range": {"min": 1.1, "max": 2.0},
                "example_value": 1.3,
                "data_sources": ["DCIM monitoring", "Utility metering"],
                "required": True,
                "tooltip": "Lower PUE = more efficient cooling and power distribution."
            },
            {
                "parameter": "re_percentage",
                "label": "Renewable Energy Percentage",
                "description": "Share of total electricity sourced from renewables.",
                "unit": "%",
                "typical_range": {"min": 50, "max": 100},
                "example_value": 100,
                "data_sources": ["PPA contracts", "REC retirement records", "RE100 disclosure"],
                "required": True,
                "tooltip": "24/7 CFE matching is the emerging best practice."
            }
        ],
        "real_world_examples": [
            {"project": "Google Data Centre RE PPAs, Global", "credits": 150000, "year": 2023}
        ],
        "regulatory_notes": "Credits accrue to RE project developer. Data centre claims Scope 2 reductions. RE100 and 24/7 CFE compact.",
        "cdm_tools_needed": ["TOOL01", "TOOL07"],
        "estimated_cost_range_usd": {"min": 50000000, "max": 1000000000},
        "crediting_period_years": {"min": 10, "max": 25}
    },

    "server_cooling_ee": {
        "id": "server_cooling_ee",
        "name": "Server Cooling Efficiency Improvement",
        "description": "Upgrade of data centre cooling systems (free cooling, liquid cooling, hot aisle containment) to reduce energy consumption.",
        "sector": "Technology",
        "user_types": ["Data Centre Operator", "ESCO", "Cloud Provider"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-II.C", "AMS-II.N"],
        "recommended_methodology": "AMS-II.C",
        "scale": "Small",
        "typical_credit_range": {"min": 1000, "max": 20000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "baseline_pue",
                "label": "Baseline PUE",
                "description": "PUE before cooling efficiency improvements.",
                "unit": "ratio",
                "typical_range": {"min": 1.5, "max": 2.5},
                "example_value": 1.8,
                "data_sources": ["Historical DCIM data", "Energy audit report"],
                "required": True,
                "tooltip": "Pre-retrofit PUE; use annualised value."
            },
            {
                "parameter": "project_pue",
                "label": "Project PUE",
                "description": "PUE achieved after cooling improvements.",
                "unit": "ratio",
                "typical_range": {"min": 1.1, "max": 1.5},
                "example_value": 1.25,
                "data_sources": ["Post-retrofit DCIM data", "M&V report"],
                "required": True,
                "tooltip": "Free cooling and liquid cooling can achieve PUE <1.2."
            },
            {
                "parameter": "total_facility_mwh_yr",
                "label": "Total Facility Energy Consumption",
                "description": "Annual electricity consumption of the data centre.",
                "unit": "MWh/year",
                "typical_range": {"min": 10000, "max": 500000},
                "example_value": 100000,
                "data_sources": ["Utility bills", "Power monitoring"],
                "required": True,
                "tooltip": "Used to calculate absolute energy savings."
            }
        ],
        "real_world_examples": [
            {"project": "Equinix Cooling Retrofit, Singapore", "credits": 8000, "year": 2023}
        ],
        "regulatory_notes": "CDM, VCS. Data centres are major energy consumers. Cooling is typically 30-40% of total energy.",
        "cdm_tools_needed": ["TOOL01", "TOOL07"],
        "estimated_cost_range_usd": {"min": 2000000, "max": 30000000},
        "crediting_period_years": {"min": 7, "max": 14}
    },

    "ewaste_methane": {
        "id": "ewaste_methane",
        "name": "E-Waste Recycling Methane Avoidance",
        "description": "Proper recycling and treatment of electronic waste, avoiding landfill disposal and associated methane and toxic emissions.",
        "sector": "Technology",
        "user_types": ["E-Waste Recycler", "Waste Company", "Municipal Authority"],
        "value_chain_position": "core",
        "applicable_methodologies": ["AMS-III.E", "AMS-III.BA"],
        "recommended_methodology": "AMS-III.E",
        "scale": "Small",
        "typical_credit_range": {"min": 500, "max": 10000, "unit": "tCO2e/year"},
        "inputs_guide": [
            {
                "parameter": "ewaste_processed_tonnes_yr",
                "label": "Annual E-Waste Processed",
                "description": "Total electronic waste processed through formal recycling.",
                "unit": "tonnes/year",
                "typical_range": {"min": 500, "max": 50000},
                "example_value": 5000,
                "data_sources": ["Weigh bridge records", "Collection manifests", "Environmental permit returns"],
                "required": True,
                "tooltip": "Includes computers, phones, appliances, cables."
            },
            {
                "parameter": "organic_fraction",
                "label": "Organic Fraction of E-Waste",
                "description": "Percentage of e-waste that is organic/plastic (generates methane in landfill).",
                "unit": "%",
                "typical_range": {"min": 15, "max": 35},
                "example_value": 25,
                "data_sources": ["E-waste composition studies", "Material recovery records"],
                "required": True,
                "tooltip": "Plastics and circuit boards contain organic matter."
            },
            {
                "parameter": "material_recovery_rate",
                "label": "Material Recovery Rate",
                "description": "Fraction of e-waste material recovered for reuse or recycling.",
                "unit": "%",
                "typical_range": {"min": 50, "max": 95},
                "example_value": 80,
                "data_sources": ["Recycling facility output records", "Material sales data"],
                "required": True,
                "tooltip": "Higher recovery rate = less residual to landfill."
            }
        ],
        "real_world_examples": [
            {"project": "Attero E-Waste Recycling, India", "credits": 4000, "year": 2023}
        ],
        "regulatory_notes": "CDM, VCS. E-waste recycling also avoids toxic contamination. Basel Convention compliance required.",
        "cdm_tools_needed": ["TOOL01", "TOOL04"],
        "estimated_cost_range_usd": {"min": 1000000, "max": 10000000},
        "crediting_period_years": {"min": 7, "max": 14}
    },
}


# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------

def get_all_activities() -> List[Dict[str, Any]]:
    """Return all activities in the catalog."""
    return list(ACTIVITY_CATALOG.values())


def get_activities_by_sector(sector: str) -> List[Dict[str, Any]]:
    """Return activities filtered by sector name (case-insensitive)."""
    return [a for a in ACTIVITY_CATALOG.values()
            if a.get("sector", "").lower() == sector.lower()]


def get_activities_by_user_type(user_type: str) -> List[Dict[str, Any]]:
    """Return activities where the given user type is listed."""
    return [a for a in ACTIVITY_CATALOG.values()
            if any(ut.lower() == user_type.lower()
                   for ut in a.get("user_types", []))]


def get_activities_for_methodology(methodology_code: str) -> List[Dict[str, Any]]:
    """Return activities that reference the given methodology code."""
    code_upper = methodology_code.upper()
    return [a for a in ACTIVITY_CATALOG.values()
            if code_upper in [m.upper()
                              for m in a.get("applicable_methodologies", [])]]


def get_activity_detail(activity_id: str) -> Optional[Dict[str, Any]]:
    """Return a single activity by its ID, or None if not found."""
    return ACTIVITY_CATALOG.get(activity_id)


def search_activities(query: str) -> List[Dict[str, Any]]:
    """Full-text search across activity name, description, sector, and user types."""
    q = query.lower()
    results = []
    for a in ACTIVITY_CATALOG.values():
        if (q in a.get("name", "").lower() or
            q in a.get("description", "").lower() or
            q in a.get("sector", "").lower() or
            any(q in ut.lower() for ut in a.get("user_types", []))):
            results.append(a)
    return results


def get_activities_by_value_chain(position: str) -> List[Dict[str, Any]]:
    """Return activities by value chain position (upstream / core / downstream)."""
    return [a for a in ACTIVITY_CATALOG.values()
            if a.get("value_chain_position", "").lower() == position.lower()]


def get_activities_by_scale(scale: str) -> List[Dict[str, Any]]:
    """Return activities filtered by scale (Micro / Small / Large)."""
    return [a for a in ACTIVITY_CATALOG.values()
            if a.get("scale", "").lower() == scale.lower()]
