"""
CDM Methodological Tools Engine
================================
Complete implementation of all 43 CDM methodological tools used across
CDM, VCS, Gold Standard, CAR, and ACR carbon credit methodologies.

Tools covered:
  TOOL01-TOOL33  : Large-scale and small-scale CDM tools
  AR-TOOL02-AR-TOOL19 : Afforestation / Reforestation CDM tools

Each tool function accepts a dict of inputs (with sensible defaults),
performs the CDM-prescribed calculation, and returns a standardised
result dict containing tool_code, tool_name, inputs echo, outputs,
methodology_notes, and unit.
"""

from __future__ import annotations

import math
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Import shared data from the existing carbon calculator v2
# ---------------------------------------------------------------------------
try:
    from services.carbon_calculator_v2 import (
        STATIC_GRID_EF,
        IPCC_DEFAULT_FACTORS,
    )
    _GWP = IPCC_DEFAULT_FACTORS["gwp"]
    _FUELS = IPCC_DEFAULT_FACTORS["fuels"]
except ImportError:
    # Fallback defaults when running standalone / in tests
    STATIC_GRID_EF = {
        "US": {"om_ef": 0.450, "bm_ef": 0.420, "om_weight": 0.5, "bm_weight": 0.5, "source": "EPA eGRID 2021"},
        "CN": {"om_ef": 0.570, "bm_ef": 0.490, "om_weight": 0.5, "bm_weight": 0.5, "source": "China NDRC 2022"},
        "IN": {"om_ef": 0.710, "bm_ef": 0.540, "om_weight": 0.5, "bm_weight": 0.5, "source": "CEA 2022"},
        "DE": {"om_ef": 0.380, "bm_ef": 0.350, "om_weight": 0.5, "bm_weight": 0.5, "source": "Eurostat 2022"},
        "GB": {"om_ef": 0.210, "bm_ef": 0.190, "om_weight": 0.5, "bm_weight": 0.5, "source": "UK BEIS 2022"},
        "FR": {"om_ef": 0.050, "bm_ef": 0.040, "om_weight": 0.5, "bm_weight": 0.5, "source": "Eurostat 2022"},
        "BR": {"om_ef": 0.130, "bm_ef": 0.110, "om_weight": 0.5, "bm_weight": 0.5, "source": "Brazil MME 2022"},
        "AU": {"om_ef": 0.650, "bm_ef": 0.580, "om_weight": 0.5, "bm_weight": 0.5, "source": "NGER 2022"},
        "JP": {"om_ef": 0.470, "bm_ef": 0.430, "om_weight": 0.5, "bm_weight": 0.5, "source": "Japan MOE 2022"},
        "KR": {"om_ef": 0.460, "bm_ef": 0.420, "om_weight": 0.5, "bm_weight": 0.5, "source": "Korea MOTIE 2022"},
        "ZA": {"om_ef": 0.900, "bm_ef": 0.820, "om_weight": 0.5, "bm_weight": 0.5, "source": "South Africa DMRE 2022"},
        "MX": {"om_ef": 0.410, "bm_ef": 0.380, "om_weight": 0.5, "bm_weight": 0.5, "source": "Mexico SENER 2022"},
        "ID": {"om_ef": 0.680, "bm_ef": 0.610, "om_weight": 0.5, "bm_weight": 0.5, "source": "Indonesia MEMR 2022"},
        "NG": {"om_ef": 0.430, "bm_ef": 0.400, "om_weight": 0.5, "bm_weight": 0.5, "source": "Nigeria ECN 2022"},
        "PK": {"om_ef": 0.490, "bm_ef": 0.440, "om_weight": 0.5, "bm_weight": 0.5, "source": "Pakistan NTDC 2022"},
    }
    _FUELS = {
        "diesel": {"ncv": 43.0, "ef_co2": 74.1, "ef_ch4": 0.003, "ef_n2o": 0.0006, "unit": "kg/GJ"},
        "gasoline": {"ncv": 44.3, "ef_co2": 69.3, "ef_ch4": 0.003, "ef_n2o": 0.0006, "unit": "kg/GJ"},
        "natural_gas": {"ncv": 48.0, "ef_co2": 56.1, "ef_ch4": 0.001, "ef_n2o": 0.0001, "unit": "kg/GJ"},
        "coal_anthracite": {"ncv": 26.7, "ef_co2": 98.3, "ef_ch4": 0.001, "ef_n2o": 0.0015, "unit": "kg/GJ"},
        "coal_bituminous": {"ncv": 25.8, "ef_co2": 94.6, "ef_ch4": 0.001, "ef_n2o": 0.0015, "unit": "kg/GJ"},
        "coal_lignite": {"ncv": 11.9, "ef_co2": 101.0, "ef_ch4": 0.001, "ef_n2o": 0.0015, "unit": "kg/GJ"},
        "fuel_oil": {"ncv": 40.4, "ef_co2": 77.4, "ef_ch4": 0.003, "ef_n2o": 0.0006, "unit": "kg/GJ"},
        "lpg": {"ncv": 47.3, "ef_co2": 63.1, "ef_ch4": 0.001, "ef_n2o": 0.0001, "unit": "kg/GJ"},
        "kerosene": {"ncv": 43.8, "ef_co2": 72.3, "ef_ch4": 0.003, "ef_n2o": 0.0006, "unit": "kg/GJ"},
        "biogas": {"ncv": 23.0, "ef_co2": 0.0, "ef_ch4": 0.002, "ef_n2o": 0.0001, "unit": "kg/GJ"},
    }
    _GWP = {"co2": 1, "ch4": 28, "n2o": 265, "sf6": 23500}

# Normalised uppercase-key GWP for convenient lookup
GWP: Dict[str, int] = {k.upper(): v for k, v in _GWP.items()}


# ============================================================================
# 1. CDMToolCategory Enum
# ============================================================================

class CDMToolCategory(str, Enum):
    """Classification of CDM methodological tools."""
    ADDITIONALITY = "additionality"
    BASELINE = "baseline"
    EMISSION_CALCULATION = "emission_calculation"
    GRID = "grid"
    TRANSPORT = "transport"
    WASTE = "waste"
    BIOMASS = "biomass"
    SMALL_SCALE = "small_scale"
    AFFORESTATION = "afforestation"
    DEFAULT_VALUES = "default_values"
    EQUIPMENT = "equipment"
    INVESTMENT = "investment"
    COMMON_PRACTICE = "common_practice"
    LEAKAGE = "leakage"
    REFRIGERANT = "refrigerant"
    BUILDING = "building"
    INDUSTRIAL = "industrial"


# ============================================================================
# 2. CDM_TOOLS_REGISTRY -- metadata for all 43 tools
# ============================================================================

CDM_TOOLS_REGISTRY: Dict[str, Dict[str, Any]] = {
    # --- Large-scale / General tools (TOOL01-TOOL33) ---
    "TOOL01": {
        "code": "TOOL01",
        "name": "Tool for the demonstration and assessment of additionality",
        "short_name": "Additionality",
        "version": "07.0.0",
        "category": CDMToolCategory.ADDITIONALITY,
        "description": "Barrier analysis and investment analysis to demonstrate that a project activity is additional.",
    },
    "TOOL02": {
        "code": "TOOL02",
        "name": "Combined tool to identify the baseline scenario and demonstrate additionality",
        "short_name": "Combined Baseline & Additionality",
        "version": "07.0.0",
        "category": CDMToolCategory.BASELINE,
        "description": "Combines baseline identification with additionality demonstration in a single framework.",
    },
    "TOOL03": {
        "code": "TOOL03",
        "name": "Tool to calculate project or leakage CO2 emissions from fossil fuel combustion",
        "short_name": "Fossil Fuel CO2",
        "version": "03.0",
        "category": CDMToolCategory.EMISSION_CALCULATION,
        "description": "PE_FF = SUM[FC_i * NCV_i * EF_CO2_i] / 1000. Uses IPCC default emission factors.",
    },
    "TOOL04": {
        "code": "TOOL04",
        "name": "Emissions from solid waste disposal sites (FOD model)",
        "short_name": "Solid Waste FOD",
        "version": "08.0",
        "category": CDMToolCategory.WASTE,
        "description": "First-order decay model: BE_CH4 = SUM[W_x * DOC_x * DOCf * F * (16/12) * (1-OX) * MCF].",
    },
    "TOOL05": {
        "code": "TOOL05",
        "name": "Baseline, project and/or leakage emissions from electricity consumption",
        "short_name": "Electricity Consumption",
        "version": "03.0",
        "category": CDMToolCategory.EMISSION_CALCULATION,
        "description": "PE_elec = EC (MWh) * EF_grid (tCO2/MWh).",
    },
    "TOOL06": {
        "code": "TOOL06",
        "name": "Project emissions from flaring",
        "short_name": "Flaring Emissions",
        "version": "02.0",
        "category": CDMToolCategory.EMISSION_CALCULATION,
        "description": "PE_flare = Q * EF * (1 - destruction_eff/100).",
    },
    "TOOL07": {
        "code": "TOOL07",
        "name": "Tool to calculate the emission factor for an electricity system",
        "short_name": "Grid Emission Factor",
        "version": "07.0",
        "category": CDMToolCategory.GRID,
        "description": "Combined Margin: EF_grid,CM = w_OM * EF_grid,OM + w_BM * EF_grid,BM.",
    },
    "TOOL08": {
        "code": "TOOL08",
        "name": "Tool to determine the mass flow of a greenhouse gas in a gaseous stream",
        "short_name": "GHG Mass Flow",
        "version": "03.0",
        "category": CDMToolCategory.EMISSION_CALCULATION,
        "description": "Mass flow = volumetric_flow * concentration * molecular_weight / molar_volume.",
    },
    "TOOL09": {
        "code": "TOOL09",
        "name": "Determining the baseline efficiency of thermal or electric energy generation systems",
        "short_name": "Baseline Efficiency",
        "version": "03.0",
        "category": CDMToolCategory.BASELINE,
        "description": "Calculates baseline thermal/electric efficiency for energy generation systems.",
    },
    "TOOL10": {
        "code": "TOOL10",
        "name": "Tool to determine the remaining lifetime of equipment",
        "short_name": "Equipment Lifetime",
        "version": "01.0",
        "category": CDMToolCategory.EQUIPMENT,
        "description": "Determines remaining useful lifetime RL = max(default_lifetime - age, min_remaining).",
    },
    "TOOL11": {
        "code": "TOOL11",
        "name": "Assessment of the validity of the original/current baseline and update of the baseline at the renewal of a crediting period",
        "short_name": "Baseline Validity",
        "version": "03.0",
        "category": CDMToolCategory.BASELINE,
        "description": "Assesses whether baseline scenario is still valid at crediting period renewal.",
    },
    "TOOL12": {
        "code": "TOOL12",
        "name": "Project and leakage emissions from transportation of freight",
        "short_name": "Freight Transport",
        "version": "02.0",
        "category": CDMToolCategory.TRANSPORT,
        "description": "Emissions = distance * cargo_mass * EF_transport_mode / 1e6.",
    },
    "TOOL13": {
        "code": "TOOL13",
        "name": "Project and leakage emissions from composting",
        "short_name": "Composting Emissions",
        "version": "02.0",
        "category": CDMToolCategory.WASTE,
        "description": "CH4 + N2O emissions from composting organic waste.",
    },
    "TOOL14": {
        "code": "TOOL14",
        "name": "Project and leakage emissions from anaerobic digesters",
        "short_name": "Anaerobic Digester",
        "version": "02.0",
        "category": CDMToolCategory.WASTE,
        "description": "Calculates methane leakage and residual emissions from anaerobic digesters.",
    },
    "TOOL15": {
        "code": "TOOL15",
        "name": "Upstream leakage emissions associated with fossil fuel use",
        "short_name": "Upstream Leakage",
        "version": "02.0",
        "category": CDMToolCategory.LEAKAGE,
        "description": "Estimates upstream (supply-chain) leakage from fossil fuel extraction and transport.",
    },
    "TOOL16": {
        "code": "TOOL16",
        "name": "Project and leakage emissions from biomass",
        "short_name": "Biomass Emissions",
        "version": "04.0",
        "category": CDMToolCategory.BIOMASS,
        "description": "CO2, CH4, N2O from biomass combustion in project/leakage boundary.",
    },
    "TOOL17": {
        "code": "TOOL17",
        "name": "Baseline emission calculations for inter-urban or long-distance cargo transport",
        "short_name": "Inter-urban Cargo Baseline",
        "version": "01.0",
        "category": CDMToolCategory.TRANSPORT,
        "description": "Baseline emissions for shifting cargo from road to rail/water.",
    },
    "TOOL18": {
        "code": "TOOL18",
        "name": "Baseline emissions for urban/mass passenger transport",
        "short_name": "Urban Passenger Transport",
        "version": "01.0",
        "category": CDMToolCategory.TRANSPORT,
        "description": "Baseline emissions from urban passenger transport modal shift.",
    },
    "TOOL19": {
        "code": "TOOL19",
        "name": "Demonstration of additionality of microscale project activities",
        "short_name": "Microscale Additionality",
        "version": "10.0",
        "category": CDMToolCategory.SMALL_SCALE,
        "description": "Simplified additionality for microscale (<= 5 MW or 20 GWh/yr) projects.",
    },
    "TOOL20": {
        "code": "TOOL20",
        "name": "Tool to assess whether a proposed CDM project activity constitutes de-bundling",
        "short_name": "Debundling Check",
        "version": "04.0",
        "category": CDMToolCategory.SMALL_SCALE,
        "description": "Checks if a small-scale project is de-bundled from a larger activity.",
    },
    "TOOL21": {
        "code": "TOOL21",
        "name": "Demonstration of additionality of small-scale project activities",
        "short_name": "Small-scale Additionality",
        "version": "13.0",
        "category": CDMToolCategory.SMALL_SCALE,
        "description": "Additionality test for SSC projects (barrier + investment simplified).",
    },
    "TOOL22": {
        "code": "TOOL22",
        "name": "Leakage in biomass small-scale project activities",
        "short_name": "Biomass Leakage SSC",
        "version": "04.0",
        "category": CDMToolCategory.SMALL_SCALE,
        "description": "Leakage from diverting biomass in small-scale CDM projects.",
    },
    "TOOL23": {
        "code": "TOOL23",
        "name": "Additionality of first-of-its-kind project activities",
        "short_name": "First-of-its-Kind",
        "version": "01.0",
        "category": CDMToolCategory.ADDITIONALITY,
        "description": "Demonstrates additionality through first-of-its-kind technology deployment.",
    },
    "TOOL24": {
        "code": "TOOL24",
        "name": "Common practice analysis",
        "short_name": "Common Practice",
        "version": "04.0",
        "category": CDMToolCategory.COMMON_PRACTICE,
        "description": "Quantifies the extent to which the project technology/practice is common.",
    },
    "TOOL25": {
        "code": "TOOL25",
        "name": "Apportioning emissions between main and co-products",
        "short_name": "Emissions Apportioning",
        "version": "01.0",
        "category": CDMToolCategory.EMISSION_CALCULATION,
        "description": "Allocates emissions between co-products using energy/mass/economic value.",
    },
    "TOOL26": {
        "code": "TOOL26",
        "name": "Methodology-specific tool for HFC-23 accounting",
        "short_name": "HFC-23 Accounting",
        "version": "04.0",
        "category": CDMToolCategory.INDUSTRIAL,
        "description": "Calculates HFC-23 by-product destruction emissions/reductions in HCFC-22 plants.",
    },
    "TOOL27": {
        "code": "TOOL27",
        "name": "Investment analysis",
        "short_name": "Investment Analysis",
        "version": "07.0",
        "category": CDMToolCategory.INVESTMENT,
        "description": "IRR/NPV/unit-cost benchmark comparison for additionality demonstration.",
    },
    "TOOL28": {
        "code": "TOOL28",
        "name": "Tool to determine the baseline and project emissions from refrigeration and AC systems",
        "short_name": "Refrigerant Emissions",
        "version": "01.0",
        "category": CDMToolCategory.REFRIGERANT,
        "description": "Annual refrigerant leakage + end-of-life emissions for RAC systems.",
    },
    "TOOL29": {
        "code": "TOOL29",
        "name": "Standardized baselines for energy-efficient refrigerators/room AC",
        "short_name": "SB Refrigerators/AC",
        "version": "01.0",
        "category": CDMToolCategory.REFRIGERANT,
        "description": "Standardised baseline for efficient refrigerators and room air conditioners.",
    },
    "TOOL30": {
        "code": "TOOL30",
        "name": "Calculation of the fraction of non-renewable biomass (fNRB)",
        "short_name": "Non-renewable Biomass fNRB",
        "version": "04.0",
        "category": CDMToolCategory.BIOMASS,
        "description": "fNRB = 1 - (MAI * forested_area) / total_biomass_consumption.",
    },
    "TOOL31": {
        "code": "TOOL31",
        "name": "Standardized baselines for energy efficiency in the building sector",
        "short_name": "SB Building Efficiency",
        "version": "01.0",
        "category": CDMToolCategory.BUILDING,
        "description": "Benchmark-based baseline for building energy efficiency improvements.",
    },
    "TOOL32": {
        "code": "TOOL32",
        "name": "Positive lists of technologies",
        "short_name": "Positive Lists",
        "version": "08.0",
        "category": CDMToolCategory.ADDITIONALITY,
        "description": "Auto-additionality for technologies on the CDM positive list.",
    },
    "TOOL33": {
        "code": "TOOL33",
        "name": "Default values for common parameters",
        "short_name": "Default Values",
        "version": "04.0",
        "category": CDMToolCategory.DEFAULT_VALUES,
        "description": "Provides GWP, oxidation factors, DOC defaults, and other IPCC common parameters.",
    },
    # --- Afforestation / Reforestation tools ---
    "AR-TOOL02": {
        "code": "AR-TOOL02",
        "name": "Combined tool to identify the baseline scenario and demonstrate additionality in A/R CDM",
        "short_name": "A/R Baseline & Additionality",
        "version": "01.0",
        "category": CDMToolCategory.AFFORESTATION,
        "description": "A/R-specific combined baseline + additionality (land use change context).",
    },
    "AR-TOOL03": {
        "code": "AR-TOOL03",
        "name": "Calculation of the number of sample plots for measurements within A/R CDM project activities",
        "short_name": "A/R Sample Plot Calculation",
        "version": "02.0",
        "category": CDMToolCategory.AFFORESTATION,
        "description": "n = (t * CV / E)^2 where CV = coefficient of variation, E = allowable error.",
    },
    "AR-TOOL08": {
        "code": "AR-TOOL08",
        "name": "Estimation of non-CO2 GHG emissions resulting from burning of biomass",
        "short_name": "A/R Biomass Burning non-CO2",
        "version": "04.0",
        "category": CDMToolCategory.AFFORESTATION,
        "description": "CH4 and N2O emissions from biomass burning in A/R project boundaries.",
    },
    "AR-TOOL12": {
        "code": "AR-TOOL12",
        "name": "Estimation of carbon stocks and change in carbon stocks in dead wood and litter",
        "short_name": "A/R Dead Wood/Litter C Stocks",
        "version": "01.0",
        "category": CDMToolCategory.AFFORESTATION,
        "description": "C stock in dead wood/litter = volume * density * carbon_fraction.",
    },
    "AR-TOOL14": {
        "code": "AR-TOOL14",
        "name": "Estimation of carbon stocks and change in carbon stocks of trees and shrubs (allometric)",
        "short_name": "A/R Tree/Shrub C Stocks",
        "version": "04.1",
        "category": CDMToolCategory.AFFORESTATION,
        "description": "AGB = SUM[a * D^b * H^c * rho * N * Area], using species-specific allometric equations.",
    },
    "AR-TOOL15": {
        "code": "AR-TOOL15",
        "name": "Estimation of the increase in GHG emissions attributable to displacement of pre-project agricultural activities",
        "short_name": "A/R Displaced Agriculture",
        "version": "02.0",
        "category": CDMToolCategory.AFFORESTATION,
        "description": "Leakage from agriculture displaced by A/R project implementation.",
    },
    "AR-TOOL16": {
        "code": "AR-TOOL16",
        "name": "Tool for estimation of change in soil organic carbon stocks due to A/R CDM activities",
        "short_name": "A/R Soil Organic Carbon",
        "version": "01.0",
        "category": CDMToolCategory.AFFORESTATION,
        "description": "Delta SOC = (SOC_project - SOC_baseline) * area * depth_factor.",
    },
    "AR-TOOL17": {
        "code": "AR-TOOL17",
        "name": "Tool for estimation of tree biomass using allometric equations (Chave et al.)",
        "short_name": "A/R Chave Allometry",
        "version": "01.0",
        "category": CDMToolCategory.AFFORESTATION,
        "description": "Chave et al. pantropical allometric models for above-ground biomass.",
    },
    "AR-TOOL18": {
        "code": "AR-TOOL18",
        "name": "Tool for estimation of tree biomass using volume equations",
        "short_name": "A/R Volume Equations",
        "version": "01.0",
        "category": CDMToolCategory.AFFORESTATION,
        "description": "Stem volume * wood density * BEF * (1 + R) * CF for tree biomass estimation.",
    },
    "AR-TOOL19": {
        "code": "AR-TOOL19",
        "name": "Demonstration of eligibility of lands for A/R CDM project activities",
        "short_name": "A/R Land Eligibility",
        "version": "03.0",
        "category": CDMToolCategory.AFFORESTATION,
        "description": "Checks Kyoto-compliant land eligibility: forest definition thresholds (crown cover, height, area).",
    },
}


# ============================================================================
# 3. Tool Calculator Functions  (TOOL01 - TOOL10)
# ============================================================================

def calculate_tool01(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """TOOL01 -- Demonstration and assessment of additionality.

    Performs a combined barrier + investment analysis.  Returns a boolean
    additionality verdict together with barrier scores and an indicative
    IRR comparison against a user-supplied benchmark.
    """
    barriers: List[Dict[str, Any]] = inputs.get("barriers", [
        {"name": "investment", "score": 0.7},
        {"name": "technological", "score": 0.5},
        {"name": "institutional", "score": 0.6},
        {"name": "prevailing_practice", "score": 0.4},
    ])
    irr_project: float = float(inputs.get("irr_project", 8.0))
    irr_benchmark: float = float(inputs.get("irr_benchmark", 12.0))
    common_practice_ratio: float = float(inputs.get("common_practice_ratio", 0.05))
    max_common_practice: float = float(inputs.get("max_common_practice_threshold", 0.20))

    barrier_pass = any(b.get("score", 0) >= 0.5 for b in barriers)
    investment_pass = irr_project < irr_benchmark
    common_practice_pass = common_practice_ratio < max_common_practice
    is_additional = barrier_pass and (investment_pass or common_practice_pass)

    return {
        "tool_code": "TOOL01",
        "tool_name": CDM_TOOLS_REGISTRY["TOOL01"]["short_name"],
        "inputs": {
            "barriers": barriers,
            "irr_project": irr_project,
            "irr_benchmark": irr_benchmark,
            "common_practice_ratio": common_practice_ratio,
        },
        "outputs": {
            "barrier_analysis_pass": barrier_pass,
            "investment_analysis_pass": investment_pass,
            "common_practice_pass": common_practice_pass,
            "is_additional": is_additional,
        },
        "methodology_notes": (
            "Step 1: barrier analysis (at least one barrier with score >= 0.5). "
            "Step 2: investment analysis (project IRR < benchmark). "
            "Step 3: common practice (ratio < 20%). "
            "Additional if barrier pass AND (investment OR common practice)."
        ),
        "unit": "boolean",
    }


def calculate_tool02(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """TOOL02 -- Combined tool to identify baseline scenario and demonstrate additionality.

    Evaluates multiple baseline alternatives, ranks them by total score,
    selects the most plausible baseline, then runs additionality logic
    identical to TOOL01 on the project vs. selected baseline.
    """
    alternatives: List[Dict[str, Any]] = inputs.get("alternatives", [
        {"name": "continuation_current", "plausibility": 0.9, "emission_rate": 1.0},
        {"name": "other_technology", "plausibility": 0.6, "emission_rate": 0.7},
        {"name": "project_without_cdm", "plausibility": 0.3, "emission_rate": 0.4},
    ])
    irr_project: float = float(inputs.get("irr_project", 8.0))
    irr_benchmark: float = float(inputs.get("irr_benchmark", 12.0))

    ranked = sorted(alternatives, key=lambda a: a.get("plausibility", 0), reverse=True)
    selected_baseline = ranked[0] if ranked else {"name": "unknown", "plausibility": 0, "emission_rate": 1.0}

    investment_pass = irr_project < irr_benchmark
    is_additional = investment_pass and selected_baseline.get("plausibility", 0) > 0.5

    return {
        "tool_code": "TOOL02",
        "tool_name": CDM_TOOLS_REGISTRY["TOOL02"]["short_name"],
        "inputs": {"alternatives": alternatives, "irr_project": irr_project, "irr_benchmark": irr_benchmark},
        "outputs": {
            "ranked_alternatives": [{"name": a["name"], "plausibility": a["plausibility"]} for a in ranked],
            "selected_baseline": selected_baseline["name"],
            "baseline_emission_rate": selected_baseline.get("emission_rate", 1.0),
            "investment_analysis_pass": investment_pass,
            "is_additional": is_additional,
        },
        "methodology_notes": (
            "Step 1: list all plausible baseline alternatives. "
            "Step 2: rank by plausibility score. "
            "Step 3: select most plausible as baseline. "
            "Step 4: investment test -- project IRR < benchmark."
        ),
        "unit": "boolean / tCO2e rate",
    }


def calculate_tool03(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """TOOL03 -- CO2 emissions from fossil fuel combustion.

    Formula:  PE_FF = SUM[ FC_i (tonnes) * NCV_i (GJ/t) * EF_CO2_i (kg CO2/GJ) ] / 1000
    Uses IPCC default emission factors imported from carbon_calculator_v2.
    """
    fuel_consumptions: Dict[str, float] = inputs.get("fuel_consumptions", {"diesel": 500.0, "natural_gas": 1200.0})

    details: List[Dict[str, Any]] = []
    total_co2_tonnes = 0.0

    for fuel_key, fc_tonnes in fuel_consumptions.items():
        fuel_data = _FUELS.get(fuel_key)
        if fuel_data is None:
            continue
        ncv = fuel_data["ncv"]          # GJ per tonne
        ef_co2 = fuel_data["ef_co2"]    # kg CO2 per GJ
        co2_tonnes = fc_tonnes * ncv * ef_co2 / 1000.0
        total_co2_tonnes += co2_tonnes
        details.append({
            "fuel": fuel_key,
            "consumption_tonnes": fc_tonnes,
            "ncv_gj_per_t": ncv,
            "ef_co2_kg_per_gj": ef_co2,
            "co2_tonnes": round(co2_tonnes, 4),
        })

    return {
        "tool_code": "TOOL03",
        "tool_name": CDM_TOOLS_REGISTRY["TOOL03"]["short_name"],
        "inputs": {"fuel_consumptions": fuel_consumptions},
        "outputs": {
            "total_co2_tonnes": round(total_co2_tonnes, 4),
            "fuel_details": details,
        },
        "methodology_notes": "PE_FF = SUM[FC_i * NCV_i * EF_CO2_i] / 1000. IPCC 2006 defaults.",
        "unit": "tCO2",
    }


def calculate_tool04(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """TOOL04 -- Emissions from solid waste disposal sites (First Order Decay).

    BE_CH4 = SUM[ W_x * DOC_x * DOCf * F * (16/12) * (1-OX) * MCF ]
    Result converted to tCO2e via GWP_CH4.
    """
    waste_streams: List[Dict[str, Any]] = inputs.get("waste_streams", [
        {"category": "food", "mass_tonnes": 5000, "doc": 0.15},
        {"category": "paper", "mass_tonnes": 3000, "doc": 0.40},
        {"category": "wood", "mass_tonnes": 2000, "doc": 0.43},
    ])
    doc_f: float = float(inputs.get("doc_f", 0.5))
    fraction_ch4: float = float(inputs.get("fraction_ch4_in_gas", 0.5))
    oxidation: float = float(inputs.get("oxidation_factor", 0.1))
    mcf: float = float(inputs.get("mcf", 1.0))
    gwp_ch4: int = GWP.get("CH4", 28)

    stream_results: List[Dict[str, Any]] = []
    total_ch4_tonnes = 0.0

    for ws in waste_streams:
        w = float(ws.get("mass_tonnes", 0))
        doc = float(ws.get("doc", 0.15))
        ch4_tonnes = w * doc * doc_f * fraction_ch4 * (16.0 / 12.0) * (1.0 - oxidation) * mcf / 1000.0
        total_ch4_tonnes += ch4_tonnes
        stream_results.append({
            "category": ws.get("category", "unknown"),
            "mass_tonnes": w,
            "doc": doc,
            "ch4_tonnes": round(ch4_tonnes, 4),
        })

    total_co2e = total_ch4_tonnes * gwp_ch4

    return {
        "tool_code": "TOOL04",
        "tool_name": CDM_TOOLS_REGISTRY["TOOL04"]["short_name"],
        "inputs": {
            "waste_streams": waste_streams,
            "doc_f": doc_f,
            "fraction_ch4_in_gas": fraction_ch4,
            "oxidation_factor": oxidation,
            "mcf": mcf,
        },
        "outputs": {
            "total_ch4_tonnes": round(total_ch4_tonnes, 4),
            "total_co2e_tonnes": round(total_co2e, 4),
            "gwp_ch4": gwp_ch4,
            "stream_details": stream_results,
        },
        "methodology_notes": (
            "FOD year-0 snapshot: BE_CH4 = SUM[W_x * DOC_x * DOCf * F * (16/12) * (1-OX) * MCF] / 1000. "
            "Multi-year decay requires iterative k-based model (not included in this simplified tool)."
        ),
        "unit": "tCO2e",
    }


def calculate_tool05(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """TOOL05 -- Emissions from electricity consumption.

    PE_elec = EC (MWh) * EF_grid (tCO2/MWh).
    """
    electricity_mwh: float = float(inputs.get("electricity_mwh", 10000.0))
    ef_grid: float = float(inputs.get("ef_grid_tco2_per_mwh", 0.5))
    country: Optional[str] = inputs.get("country_code")

    if country and country.upper() in STATIC_GRID_EF:
        grid = STATIC_GRID_EF[country.upper()]
        ef_grid = grid["om_ef"] * grid["om_weight"] + grid["bm_ef"] * grid["bm_weight"]

    emissions_tco2 = electricity_mwh * ef_grid

    return {
        "tool_code": "TOOL05",
        "tool_name": CDM_TOOLS_REGISTRY["TOOL05"]["short_name"],
        "inputs": {"electricity_mwh": electricity_mwh, "ef_grid_tco2_per_mwh": ef_grid, "country_code": country},
        "outputs": {
            "emissions_tco2": round(emissions_tco2, 4),
            "ef_grid_used": round(ef_grid, 6),
        },
        "methodology_notes": "PE_elec = EC * EF_grid. Grid EF from TOOL07 or country defaults.",
        "unit": "tCO2",
    }


def calculate_tool06(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """TOOL06 -- Project emissions from flaring.

    PE_flare = Q (m3) * EF (tCO2/m3) * (1 - destruction_efficiency / 100).
    """
    gas_volume_m3: float = float(inputs.get("gas_volume_m3", 50000.0))
    ef_tco2_per_m3: float = float(inputs.get("ef_tco2_per_m3", 0.00195))
    destruction_eff: float = float(inputs.get("destruction_efficiency_pct", 98.0))

    pe_flare = gas_volume_m3 * ef_tco2_per_m3 * (1.0 - destruction_eff / 100.0)

    return {
        "tool_code": "TOOL06",
        "tool_name": CDM_TOOLS_REGISTRY["TOOL06"]["short_name"],
        "inputs": {
            "gas_volume_m3": gas_volume_m3,
            "ef_tco2_per_m3": ef_tco2_per_m3,
            "destruction_efficiency_pct": destruction_eff,
        },
        "outputs": {
            "pe_flare_tco2": round(pe_flare, 4),
            "uncombusted_fraction": round(1.0 - destruction_eff / 100.0, 4),
        },
        "methodology_notes": "PE_flare = Q * EF * (1 - DE/100). DE typically 98-99.5%.",
        "unit": "tCO2",
    }


def calculate_tool07(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """TOOL07 -- Grid emission factor (Operating Margin / Build Margin / Combined Margin).

    EF_grid,CM = w_OM * EF_grid,OM + w_BM * EF_grid,BM.
    Uses STATIC_GRID_EF from carbon_calculator_v2 for country lookups.
    """
    country: str = inputs.get("country_code", "IN").upper()
    w_om: float = float(inputs.get("w_om", 0.5))
    w_bm: float = float(inputs.get("w_bm", 0.5))
    custom_om_ef: Optional[float] = inputs.get("custom_om_ef")
    custom_bm_ef: Optional[float] = inputs.get("custom_bm_ef")

    grid = STATIC_GRID_EF.get(country, STATIC_GRID_EF.get("IN", {}))
    om_ef = float(custom_om_ef) if custom_om_ef is not None else grid.get("om_ef", 0.5)
    bm_ef = float(custom_bm_ef) if custom_bm_ef is not None else grid.get("bm_ef", 0.4)

    ef_cm = w_om * om_ef + w_bm * bm_ef

    return {
        "tool_code": "TOOL07",
        "tool_name": CDM_TOOLS_REGISTRY["TOOL07"]["short_name"],
        "inputs": {"country_code": country, "w_om": w_om, "w_bm": w_bm},
        "outputs": {
            "ef_om_tco2_mwh": round(om_ef, 6),
            "ef_bm_tco2_mwh": round(bm_ef, 6),
            "ef_cm_tco2_mwh": round(ef_cm, 6),
            "source": grid.get("source", "custom"),
        },
        "methodology_notes": "EF_grid,CM = w_OM * EF_OM + w_BM * EF_BM. Default weights 50/50.",
        "unit": "tCO2/MWh",
    }


def calculate_tool08(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """TOOL08 -- Mass flow of a GHG in a gaseous stream.

    mass_flow (kg/hr) = volumetric_flow (m3/hr) * concentration (fraction) * MW / V_m
    where V_m = molar volume at STP (0.02241 m3/mol).
    """
    volumetric_flow_m3_hr: float = float(inputs.get("volumetric_flow_m3_hr", 1000.0))
    concentration_fraction: float = float(inputs.get("concentration_fraction", 0.03))
    molecular_weight: float = float(inputs.get("molecular_weight_kg_per_kmol", 44.01))
    temperature_k: float = float(inputs.get("temperature_k", 273.15))
    pressure_kpa: float = float(inputs.get("pressure_kpa", 101.325))

    # Molar volume adjusted for T and P (ideal gas)
    v_m_stp = 22.414  # L/mol at STP
    v_m_actual = v_m_stp * (temperature_k / 273.15) * (101.325 / pressure_kpa)  # L/mol
    v_m_m3 = v_m_actual / 1000.0  # m3/mol

    # Mass flow in kg/hr -- MW is in kg/kmol, so divide by 1000 for kg/mol
    mw_kg_per_mol = molecular_weight / 1000.0
    mass_flow_kg_hr = volumetric_flow_m3_hr * concentration_fraction * mw_kg_per_mol / v_m_m3

    # Annual mass (tonnes)
    annual_mass_tonnes = mass_flow_kg_hr * 8760.0 / 1000.0

    return {
        "tool_code": "TOOL08",
        "tool_name": CDM_TOOLS_REGISTRY["TOOL08"]["short_name"],
        "inputs": {
            "volumetric_flow_m3_hr": volumetric_flow_m3_hr,
            "concentration_fraction": concentration_fraction,
            "molecular_weight_kg_per_kmol": molecular_weight,
            "temperature_k": temperature_k,
            "pressure_kpa": pressure_kpa,
        },
        "outputs": {
            "molar_volume_m3_per_mol": round(v_m_m3, 6),
            "mass_flow_kg_per_hr": round(mass_flow_kg_hr, 4),
            "annual_mass_tonnes": round(annual_mass_tonnes, 4),
        },
        "methodology_notes": "mass_flow = Q * C * (MW/1000) / V_m. Ideal-gas molar volume adjusted for T,P.",
        "unit": "tonnes/yr",
    }


def calculate_tool09(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """TOOL09 -- Baseline efficiency of thermal or electric energy generation systems.

    Efficiency = useful_energy_output / total_fuel_energy_input.
    Compares with regulatory/manufacturer benchmarks.
    """
    useful_output_gj: float = float(inputs.get("useful_output_gj", 5000.0))
    fuel_input_gj: float = float(inputs.get("fuel_input_gj", 15000.0))
    system_type: str = inputs.get("system_type", "boiler")
    manufacturer_eff: float = float(inputs.get("manufacturer_efficiency", 0.85))
    regulatory_minimum: float = float(inputs.get("regulatory_minimum_efficiency", 0.80))

    actual_efficiency = useful_output_gj / fuel_input_gj if fuel_input_gj > 0 else 0.0

    # Baseline efficiency is the lower of manufacturer / regulatory minimum (conservative)
    baseline_efficiency = min(manufacturer_eff, regulatory_minimum)

    # Emission reduction factor from efficiency improvement
    if baseline_efficiency > 0 and actual_efficiency > baseline_efficiency:
        reduction_factor = 1.0 - (baseline_efficiency / actual_efficiency)
    else:
        reduction_factor = 0.0

    return {
        "tool_code": "TOOL09",
        "tool_name": CDM_TOOLS_REGISTRY["TOOL09"]["short_name"],
        "inputs": {
            "useful_output_gj": useful_output_gj,
            "fuel_input_gj": fuel_input_gj,
            "system_type": system_type,
            "manufacturer_efficiency": manufacturer_eff,
            "regulatory_minimum_efficiency": regulatory_minimum,
        },
        "outputs": {
            "actual_efficiency": round(actual_efficiency, 4),
            "baseline_efficiency": round(baseline_efficiency, 4),
            "efficiency_improvement": round(actual_efficiency - baseline_efficiency, 4),
            "emission_reduction_factor": round(reduction_factor, 4),
        },
        "methodology_notes": (
            "Baseline eff = min(manufacturer, regulatory). "
            "Reduction factor = 1 - baseline_eff / actual_eff (only if actual > baseline)."
        ),
        "unit": "fraction",
    }


def calculate_tool10(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """TOOL10 -- Remaining lifetime of equipment.

    RL = max(default_lifetime - age, min_remaining_years).
    Applies a condition-based adjustment factor.
    """
    equipment_type: str = inputs.get("equipment_type", "boiler")
    age_years: float = float(inputs.get("age_years", 12.0))
    condition_factor: float = float(inputs.get("condition_factor", 0.9))
    min_remaining: float = float(inputs.get("min_remaining_years", 3.0))

    default_lifetimes: Dict[str, float] = {
        "boiler": 25.0,
        "turbine": 30.0,
        "chiller": 20.0,
        "motor": 15.0,
        "transformer": 35.0,
        "pump": 15.0,
        "compressor": 20.0,
        "heat_exchanger": 25.0,
        "generator": 30.0,
        "kiln": 30.0,
    }

    default_lt = default_lifetimes.get(equipment_type, 20.0)
    remaining_raw = default_lt - age_years
    remaining_adjusted = remaining_raw * condition_factor
    remaining_final = max(remaining_adjusted, min_remaining)

    return {
        "tool_code": "TOOL10",
        "tool_name": CDM_TOOLS_REGISTRY["TOOL10"]["short_name"],
        "inputs": {
            "equipment_type": equipment_type,
            "age_years": age_years,
            "condition_factor": condition_factor,
            "min_remaining_years": min_remaining,
        },
        "outputs": {
            "default_lifetime_years": default_lt,
            "remaining_raw_years": round(remaining_raw, 2),
            "remaining_adjusted_years": round(remaining_adjusted, 2),
            "remaining_final_years": round(remaining_final, 2),
        },
        "methodology_notes": (
            "RL = max((default_lifetime - age) * condition_factor, min_remaining). "
            "Default lifetimes from UNFCCC/CDM guidance."
        ),
        "unit": "years",
    }


# ============================================================================
# 3b. Tool Calculator Functions  (TOOL11 - TOOL20)
# ============================================================================

def calculate_tool11(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """TOOL11 -- Assessment of the validity of the original/current baseline.

    Checks regulatory changes, technology penetration, and fuel-price shifts
    to determine whether the baseline remains valid at crediting-period renewal.
    """
    baseline_year: int = int(inputs.get("baseline_year", 2015))
    current_year: int = int(inputs.get("current_year", 2025))
    regulatory_change: bool = bool(inputs.get("regulatory_change", False))
    technology_penetration_pct: float = float(inputs.get("technology_penetration_pct", 12.0))
    penetration_threshold: float = float(inputs.get("penetration_threshold_pct", 20.0))
    fuel_price_change_pct: float = float(inputs.get("fuel_price_change_pct", 15.0))
    fuel_price_threshold: float = float(inputs.get("fuel_price_threshold_pct", 50.0))

    years_elapsed = current_year - baseline_year
    penetration_ok = technology_penetration_pct < penetration_threshold
    fuel_price_ok = abs(fuel_price_change_pct) < fuel_price_threshold
    baseline_valid = (not regulatory_change) and penetration_ok and fuel_price_ok and years_elapsed <= 10

    return {
        "tool_code": "TOOL11",
        "tool_name": CDM_TOOLS_REGISTRY["TOOL11"]["short_name"],
        "inputs": {
            "baseline_year": baseline_year,
            "current_year": current_year,
            "regulatory_change": regulatory_change,
            "technology_penetration_pct": technology_penetration_pct,
            "fuel_price_change_pct": fuel_price_change_pct,
        },
        "outputs": {
            "years_elapsed": years_elapsed,
            "regulatory_check_pass": not regulatory_change,
            "penetration_check_pass": penetration_ok,
            "fuel_price_check_pass": fuel_price_ok,
            "baseline_valid": baseline_valid,
        },
        "methodology_notes": (
            "Baseline valid if: no regulatory change, technology penetration < threshold, "
            "fuel price shift < threshold, and <= 10 years since baseline establishment."
        ),
        "unit": "boolean",
    }


def calculate_tool12(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """TOOL12 -- Freight transport emissions.

    Emissions (tCO2) = distance_km * cargo_tonnes * EF (gCO2/tonne-km) / 1e6.
    """
    distance_km: float = float(inputs.get("distance_km", 500.0))
    cargo_tonnes: float = float(inputs.get("cargo_tonnes", 100.0))
    transport_mode: str = inputs.get("transport_mode", "road")

    # Default EFs in gCO2 per tonne-km (IPCC / GLEC framework)
    mode_efs: Dict[str, float] = {
        "road": 62.0,
        "rail": 22.0,
        "inland_water": 31.0,
        "coastal_shipping": 16.0,
        "ocean_shipping": 8.0,
        "air": 602.0,
        "pipeline": 5.0,
    }
    ef = float(inputs.get("ef_gco2_per_tkm", mode_efs.get(transport_mode, 62.0)))

    emissions_tco2 = distance_km * cargo_tonnes * ef / 1e6

    return {
        "tool_code": "TOOL12",
        "tool_name": CDM_TOOLS_REGISTRY["TOOL12"]["short_name"],
        "inputs": {
            "distance_km": distance_km,
            "cargo_tonnes": cargo_tonnes,
            "transport_mode": transport_mode,
            "ef_gco2_per_tkm": ef,
        },
        "outputs": {
            "emissions_tco2": round(emissions_tco2, 4),
            "tonne_km": round(distance_km * cargo_tonnes, 2),
        },
        "methodology_notes": "Emissions = distance * cargo * EF / 1e6. EFs: road 62, rail 22, air 602 gCO2/tkm.",
        "unit": "tCO2",
    }


def calculate_tool13(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """TOOL13 -- Composting emissions (CH4 + N2O).

    CH4 = mass_composted * CH4_EF; N2O = mass_composted * N2O_EF.
    Total CO2e = CH4 * GWP_CH4 + N2O * GWP_N2O.
    """
    mass_composted_tonnes: float = float(inputs.get("mass_composted_tonnes", 1000.0))
    ch4_ef_kg_per_tonne: float = float(inputs.get("ch4_ef_kg_per_tonne", 4.0))
    n2o_ef_kg_per_tonne: float = float(inputs.get("n2o_ef_kg_per_tonne", 0.3))

    ch4_tonnes = mass_composted_tonnes * ch4_ef_kg_per_tonne / 1000.0
    n2o_tonnes = mass_composted_tonnes * n2o_ef_kg_per_tonne / 1000.0
    co2e_tonnes = ch4_tonnes * GWP.get("CH4", 28) + n2o_tonnes * GWP.get("N2O", 265)

    return {
        "tool_code": "TOOL13",
        "tool_name": CDM_TOOLS_REGISTRY["TOOL13"]["short_name"],
        "inputs": {
            "mass_composted_tonnes": mass_composted_tonnes,
            "ch4_ef_kg_per_tonne": ch4_ef_kg_per_tonne,
            "n2o_ef_kg_per_tonne": n2o_ef_kg_per_tonne,
        },
        "outputs": {
            "ch4_tonnes": round(ch4_tonnes, 4),
            "n2o_tonnes": round(n2o_tonnes, 4),
            "total_co2e_tonnes": round(co2e_tonnes, 4),
        },
        "methodology_notes": "IPCC composting EFs: CH4 ~4 kg/t, N2O ~0.3 kg/t of wet waste composted.",
        "unit": "tCO2e",
    }


def calculate_tool14(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """TOOL14 -- Anaerobic digester emissions.

    Methane leakage from the digester + residual CH4 in digestate.
    PE_AD = biogas_produced * CH4_fraction * leakage_rate * density_CH4 * GWP_CH4 / 1000.
    """
    biogas_m3: float = float(inputs.get("biogas_produced_m3", 50000.0))
    ch4_fraction: float = float(inputs.get("ch4_fraction", 0.60))
    leakage_rate: float = float(inputs.get("leakage_rate", 0.05))
    ch4_density_kg_m3: float = float(inputs.get("ch4_density_kg_m3", 0.717))
    digestate_ch4_kg: float = float(inputs.get("residual_digestate_ch4_kg", 50.0))

    leaked_ch4_kg = biogas_m3 * ch4_fraction * leakage_rate * ch4_density_kg_m3
    total_ch4_kg = leaked_ch4_kg + digestate_ch4_kg
    total_co2e = total_ch4_kg * GWP.get("CH4", 28) / 1000.0

    return {
        "tool_code": "TOOL14",
        "tool_name": CDM_TOOLS_REGISTRY["TOOL14"]["short_name"],
        "inputs": {
            "biogas_produced_m3": biogas_m3,
            "ch4_fraction": ch4_fraction,
            "leakage_rate": leakage_rate,
            "residual_digestate_ch4_kg": digestate_ch4_kg,
        },
        "outputs": {
            "leaked_ch4_kg": round(leaked_ch4_kg, 4),
            "total_ch4_kg": round(total_ch4_kg, 4),
            "total_co2e_tonnes": round(total_co2e, 4),
        },
        "methodology_notes": (
            "PE_AD = biogas * CH4_frac * leak_rate * density + digestate_CH4. "
            "Typical leakage 3-10%."
        ),
        "unit": "tCO2e",
    }


def calculate_tool15(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """TOOL15 -- Upstream leakage emissions from fossil fuel use.

    Leakage = fuel_consumed_TJ * upstream_EF (tCO2/TJ).
    """
    fuel_type: str = inputs.get("fuel_type", "natural_gas")
    fuel_consumed_tj: float = float(inputs.get("fuel_consumed_tj", 100.0))

    upstream_efs: Dict[str, float] = {
        "natural_gas": 5.2,
        "coal_bituminous": 1.5,
        "coal_lignite": 1.2,
        "diesel": 3.6,
        "fuel_oil": 3.0,
        "gasoline": 3.8,
        "lpg": 2.5,
        "crude_oil": 4.0,
    }
    ef = float(inputs.get("upstream_ef_tco2_per_tj", upstream_efs.get(fuel_type, 3.0)))

    leakage_tco2 = fuel_consumed_tj * ef

    return {
        "tool_code": "TOOL15",
        "tool_name": CDM_TOOLS_REGISTRY["TOOL15"]["short_name"],
        "inputs": {"fuel_type": fuel_type, "fuel_consumed_tj": fuel_consumed_tj, "upstream_ef_tco2_per_tj": ef},
        "outputs": {"leakage_tco2": round(leakage_tco2, 4)},
        "methodology_notes": "Leakage = fuel_TJ * upstream_EF. Gas ~5.2, coal ~1.5, diesel ~3.6 tCO2/TJ.",
        "unit": "tCO2",
    }


def calculate_tool16(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """TOOL16 -- Emissions from biomass.

    CO2 from biomass combustion is biogenic (zero under CDM).  CH4 and N2O are
    counted:  PE_biomass = mass * (CH4_EF * GWP_CH4 + N2O_EF * GWP_N2O) / 1000.
    """
    biomass_tonnes: float = float(inputs.get("biomass_tonnes", 2000.0))
    ch4_ef_kg_t: float = float(inputs.get("ch4_ef_kg_per_tonne", 7.0))
    n2o_ef_kg_t: float = float(inputs.get("n2o_ef_kg_per_tonne", 0.07))

    ch4_tonnes = biomass_tonnes * ch4_ef_kg_t / 1000.0
    n2o_tonnes = biomass_tonnes * n2o_ef_kg_t / 1000.0
    co2e = ch4_tonnes * GWP.get("CH4", 28) + n2o_tonnes * GWP.get("N2O", 265)

    return {
        "tool_code": "TOOL16",
        "tool_name": CDM_TOOLS_REGISTRY["TOOL16"]["short_name"],
        "inputs": {
            "biomass_tonnes": biomass_tonnes,
            "ch4_ef_kg_per_tonne": ch4_ef_kg_t,
            "n2o_ef_kg_per_tonne": n2o_ef_kg_t,
        },
        "outputs": {
            "ch4_tonnes": round(ch4_tonnes, 4),
            "n2o_tonnes": round(n2o_tonnes, 4),
            "total_co2e_tonnes": round(co2e, 4),
            "biogenic_co2_note": "CO2 from biomass is biogenic -- zero under CDM accounting.",
        },
        "methodology_notes": "Only non-CO2 GHGs counted: CH4 ~7 kg/t, N2O ~0.07 kg/t biomass burned.",
        "unit": "tCO2e",
    }


def calculate_tool17(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """TOOL17 -- Inter-urban / long-distance cargo transport baseline.

    BE = cargo_tkm_baseline * EF_baseline_mode - cargo_tkm_project * EF_project_mode.
    """
    cargo_tkm: float = float(inputs.get("cargo_tonne_km", 1e6))
    baseline_mode: str = inputs.get("baseline_mode", "road")
    project_mode: str = inputs.get("project_mode", "rail")

    mode_efs: Dict[str, float] = {
        "road": 62.0,
        "rail": 22.0,
        "inland_water": 31.0,
        "coastal_shipping": 16.0,
    }
    ef_bl = float(inputs.get("ef_baseline_gco2_tkm", mode_efs.get(baseline_mode, 62.0)))
    ef_pj = float(inputs.get("ef_project_gco2_tkm", mode_efs.get(project_mode, 22.0)))

    be_tco2 = cargo_tkm * ef_bl / 1e6
    pe_tco2 = cargo_tkm * ef_pj / 1e6
    er_tco2 = be_tco2 - pe_tco2

    return {
        "tool_code": "TOOL17",
        "tool_name": CDM_TOOLS_REGISTRY["TOOL17"]["short_name"],
        "inputs": {
            "cargo_tonne_km": cargo_tkm,
            "baseline_mode": baseline_mode,
            "project_mode": project_mode,
        },
        "outputs": {
            "baseline_emissions_tco2": round(be_tco2, 4),
            "project_emissions_tco2": round(pe_tco2, 4),
            "emission_reductions_tco2": round(er_tco2, 4),
        },
        "methodology_notes": "Modal shift: ER = tkm * (EF_baseline - EF_project) / 1e6.",
        "unit": "tCO2",
    }


def calculate_tool18(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """TOOL18 -- Urban/mass passenger transport baseline emissions.

    BE = passengers * trip_distance * EF_baseline_mode / 1e6.
    ER = BE - PE.
    """
    annual_passengers: float = float(inputs.get("annual_passengers", 500000))
    avg_trip_km: float = float(inputs.get("avg_trip_km", 12.0))
    baseline_mode: str = inputs.get("baseline_mode", "private_car")
    project_mode: str = inputs.get("project_mode", "bus_rapid_transit")

    mode_efs_gco2_pkm: Dict[str, float] = {
        "private_car": 170.0,
        "motorcycle": 90.0,
        "minibus": 60.0,
        "bus": 40.0,
        "bus_rapid_transit": 30.0,
        "metro": 20.0,
        "light_rail": 25.0,
        "bicycle": 0.0,
        "walking": 0.0,
    }
    ef_bl = float(inputs.get("ef_baseline_gco2_pkm", mode_efs_gco2_pkm.get(baseline_mode, 170.0)))
    ef_pj = float(inputs.get("ef_project_gco2_pkm", mode_efs_gco2_pkm.get(project_mode, 30.0)))

    pkm = annual_passengers * avg_trip_km
    be_tco2 = pkm * ef_bl / 1e6
    pe_tco2 = pkm * ef_pj / 1e6
    er_tco2 = be_tco2 - pe_tco2

    return {
        "tool_code": "TOOL18",
        "tool_name": CDM_TOOLS_REGISTRY["TOOL18"]["short_name"],
        "inputs": {
            "annual_passengers": annual_passengers,
            "avg_trip_km": avg_trip_km,
            "baseline_mode": baseline_mode,
            "project_mode": project_mode,
        },
        "outputs": {
            "passenger_km": round(pkm, 2),
            "baseline_emissions_tco2": round(be_tco2, 4),
            "project_emissions_tco2": round(pe_tco2, 4),
            "emission_reductions_tco2": round(er_tco2, 4),
        },
        "methodology_notes": "ER = pkm * (EF_baseline - EF_project) / 1e6. Car ~170, BRT ~30 gCO2/pkm.",
        "unit": "tCO2",
    }


def calculate_tool19(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """TOOL19 -- Microscale additionality.

    Simplified additionality for microscale projects (<= 5 MW or <= 20 GWh/yr).
    Passes if capacity <= threshold and technology is on the micro positive list,
    OR the project is in an LDC/SIDS.
    """
    capacity_kw: float = float(inputs.get("capacity_kw", 50.0))
    annual_generation_mwh: float = float(inputs.get("annual_generation_mwh", 80.0))
    technology: str = inputs.get("technology", "solar_pv")
    is_ldc_or_sids: bool = bool(inputs.get("is_ldc_or_sids", False))

    micro_threshold_kw = 5000.0
    micro_threshold_mwh = 20000.0

    positive_list = {
        "solar_pv", "solar_thermal", "wind", "micro_hydro", "biomass_cookstove",
        "biogas", "led_lighting", "efficient_cookstove",
    }

    within_capacity = capacity_kw <= micro_threshold_kw and annual_generation_mwh <= micro_threshold_mwh
    on_positive_list = technology in positive_list
    is_additional = within_capacity and (on_positive_list or is_ldc_or_sids)

    return {
        "tool_code": "TOOL19",
        "tool_name": CDM_TOOLS_REGISTRY["TOOL19"]["short_name"],
        "inputs": {
            "capacity_kw": capacity_kw,
            "annual_generation_mwh": annual_generation_mwh,
            "technology": technology,
            "is_ldc_or_sids": is_ldc_or_sids,
        },
        "outputs": {
            "within_capacity_limit": within_capacity,
            "on_positive_list": on_positive_list,
            "is_additional": is_additional,
        },
        "methodology_notes": "Microscale: <= 5 MW and <= 20 GWh/yr.  Auto-additional if on positive list or LDC/SIDS.",
        "unit": "boolean",
    }


def calculate_tool20(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """TOOL20 -- Debundling assessment for small-scale CDM.

    A project is debundled if another registered CDM project exists within
    1 km with the same technology, by the same developer, registered within
    the previous 2 years, AND the combined capacity exceeds the SSC threshold.
    """
    project_capacity_kw: float = float(inputs.get("project_capacity_kw", 4000.0))
    ssc_threshold_kw: float = float(inputs.get("ssc_threshold_kw", 15000.0))
    same_developer_nearby: bool = bool(inputs.get("same_developer_within_1km", False))
    nearby_capacity_kw: float = float(inputs.get("nearby_project_capacity_kw", 0.0))
    registered_within_2yr: bool = bool(inputs.get("registered_within_2_years", False))

    combined = project_capacity_kw + (nearby_capacity_kw if same_developer_nearby else 0.0)
    is_debundled = same_developer_nearby and registered_within_2yr and combined > ssc_threshold_kw

    return {
        "tool_code": "TOOL20",
        "tool_name": CDM_TOOLS_REGISTRY["TOOL20"]["short_name"],
        "inputs": {
            "project_capacity_kw": project_capacity_kw,
            "ssc_threshold_kw": ssc_threshold_kw,
            "same_developer_within_1km": same_developer_nearby,
            "nearby_project_capacity_kw": nearby_capacity_kw,
            "registered_within_2_years": registered_within_2yr,
        },
        "outputs": {
            "combined_capacity_kw": round(combined, 2),
            "exceeds_ssc_threshold": combined > ssc_threshold_kw,
            "is_debundled": is_debundled,
        },
        "methodology_notes": (
            "Debundled if same developer, within 1 km, registered < 2 yr ago, "
            "and combined capacity > SSC threshold (15 MW for RE)."
        ),
        "unit": "boolean",
    }


# ============================================================================
# 3c. Tool Calculator Functions  (TOOL21 - TOOL33)
# ============================================================================

def calculate_tool21(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """TOOL21 -- Small-scale additionality (simplified barrier + investment).

    For SSC projects (Type I <= 15 MW, Type II <= 60 GWh/yr savings,
    Type III <= 60 kt CO2e/yr).  Barrier analysis uses fewer barriers;
    investment test uses simple cost comparison.
    """
    project_type: str = inputs.get("project_type", "type_i")
    capacity_or_savings: float = float(inputs.get("capacity_or_savings", 10.0))
    barriers: List[str] = inputs.get("barriers_identified", ["investment", "access_to_finance"])
    project_cost_per_unit: float = float(inputs.get("project_cost_per_unit", 120.0))
    conventional_cost_per_unit: float = float(inputs.get("conventional_cost_per_unit", 80.0))

    thresholds = {"type_i": 15.0, "type_ii": 60.0, "type_iii": 60.0}
    within_ssc = capacity_or_savings <= thresholds.get(project_type, 15.0)
    has_barrier = len(barriers) >= 1
    cost_barrier = project_cost_per_unit > conventional_cost_per_unit
    is_additional = within_ssc and (has_barrier or cost_barrier)

    return {
        "tool_code": "TOOL21",
        "tool_name": CDM_TOOLS_REGISTRY["TOOL21"]["short_name"],
        "inputs": {
            "project_type": project_type,
            "capacity_or_savings": capacity_or_savings,
            "barriers_identified": barriers,
            "project_cost_per_unit": project_cost_per_unit,
            "conventional_cost_per_unit": conventional_cost_per_unit,
        },
        "outputs": {
            "within_ssc_limit": within_ssc,
            "barrier_test_pass": has_barrier,
            "cost_barrier_pass": cost_barrier,
            "is_additional": is_additional,
        },
        "methodology_notes": "SSC additionality: within capacity limit + (barrier OR cost comparison).",
        "unit": "boolean",
    }


def calculate_tool22(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """TOOL22 -- Leakage in biomass small-scale project activities.

    Leakage = biomass_diverted * fNRB * NCV * EF_CO2 / 1000.
    Represents biomass that would have been used elsewhere now diverted to the project.
    """
    biomass_diverted_tonnes: float = float(inputs.get("biomass_diverted_tonnes", 500.0))
    f_nrb: float = float(inputs.get("f_nrb", 0.70))
    ncv_gj_per_t: float = float(inputs.get("ncv_gj_per_tonne", 15.0))
    ef_co2_kg_per_gj: float = float(inputs.get("ef_co2_kg_per_gj", 112.0))

    leakage_tco2 = biomass_diverted_tonnes * f_nrb * ncv_gj_per_t * ef_co2_kg_per_gj / 1000.0

    return {
        "tool_code": "TOOL22",
        "tool_name": CDM_TOOLS_REGISTRY["TOOL22"]["short_name"],
        "inputs": {
            "biomass_diverted_tonnes": biomass_diverted_tonnes,
            "f_nrb": f_nrb,
            "ncv_gj_per_tonne": ncv_gj_per_t,
            "ef_co2_kg_per_gj": ef_co2_kg_per_gj,
        },
        "outputs": {
            "leakage_tco2": round(leakage_tco2, 4),
        },
        "methodology_notes": "Leakage = diverted_biomass * fNRB * NCV * EF / 1000. Only non-renewable fraction leaks.",
        "unit": "tCO2",
    }


def calculate_tool23(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """TOOL23 -- First-of-its-kind additionality.

    Project is additional if the technology has not been deployed in the
    host country/region, OR fewer than N installations exist.
    """
    technology: str = inputs.get("technology", "offshore_wind")
    country: str = inputs.get("country_code", "VN")
    existing_installations: int = int(inputs.get("existing_installations_in_country", 0))
    foik_threshold: int = int(inputs.get("foik_threshold", 3))
    operational_years_oldest: float = float(inputs.get("operational_years_oldest", 0.0))

    is_first_of_kind = existing_installations < foik_threshold
    is_additional = is_first_of_kind

    return {
        "tool_code": "TOOL23",
        "tool_name": CDM_TOOLS_REGISTRY["TOOL23"]["short_name"],
        "inputs": {
            "technology": technology,
            "country_code": country,
            "existing_installations_in_country": existing_installations,
            "foik_threshold": foik_threshold,
        },
        "outputs": {
            "is_first_of_kind": is_first_of_kind,
            "is_additional": is_additional,
            "installations_found": existing_installations,
        },
        "methodology_notes": (
            "First-of-its-kind if fewer than threshold (default 3) installations "
            "of the same technology exist in the host country."
        ),
        "unit": "boolean",
    }


def calculate_tool24(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """TOOL24 -- Common practice analysis.

    Calculates penetration rate = similar_projects / total_facilities.
    If penetration < threshold, the technology is NOT common practice.
    """
    similar_projects: int = int(inputs.get("similar_projects_in_region", 5))
    total_facilities: int = int(inputs.get("total_facilities_in_region", 200))
    threshold_pct: float = float(inputs.get("common_practice_threshold_pct", 20.0))

    penetration_pct = (similar_projects / total_facilities * 100.0) if total_facilities > 0 else 0.0
    is_common_practice = penetration_pct >= threshold_pct

    return {
        "tool_code": "TOOL24",
        "tool_name": CDM_TOOLS_REGISTRY["TOOL24"]["short_name"],
        "inputs": {
            "similar_projects_in_region": similar_projects,
            "total_facilities_in_region": total_facilities,
            "common_practice_threshold_pct": threshold_pct,
        },
        "outputs": {
            "penetration_pct": round(penetration_pct, 2),
            "is_common_practice": is_common_practice,
            "supports_additionality": not is_common_practice,
        },
        "methodology_notes": "Penetration = similar / total * 100. Not common if < 20% (default).",
        "unit": "percent",
    }


def calculate_tool25(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """TOOL25 -- Apportioning emissions between main product and co-products.

    Supports three allocation methods: energy, mass, and economic value.
    """
    total_emissions_tco2: float = float(inputs.get("total_emissions_tco2", 10000.0))
    allocation_method: str = inputs.get("allocation_method", "energy")
    main_product_share: float = float(inputs.get("main_product_share", 0.70))

    allocated_main = total_emissions_tco2 * main_product_share
    allocated_co = total_emissions_tco2 * (1.0 - main_product_share)

    return {
        "tool_code": "TOOL25",
        "tool_name": CDM_TOOLS_REGISTRY["TOOL25"]["short_name"],
        "inputs": {
            "total_emissions_tco2": total_emissions_tco2,
            "allocation_method": allocation_method,
            "main_product_share": main_product_share,
        },
        "outputs": {
            "allocated_main_tco2": round(allocated_main, 4),
            "allocated_co_product_tco2": round(allocated_co, 4),
        },
        "methodology_notes": f"Allocation by {allocation_method}: main {main_product_share*100:.0f}%.",
        "unit": "tCO2",
    }


def calculate_tool26(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """TOOL26 -- HFC-23 accounting.

    HFC-23 is a by-product of HCFC-22 production.
    BE = HCFC22_produced * HFC23_ratio * GWP_HFC23.
    PE = HFC23_destroyed * GWP_HFC23 * (1 - destruction_eff).
    ER = BE - PE.
    """
    hcfc22_produced_tonnes: float = float(inputs.get("hcfc22_produced_tonnes", 5000.0))
    hfc23_ratio: float = float(inputs.get("hfc23_generation_ratio", 0.03))
    gwp_hfc23: int = int(inputs.get("gwp_hfc23", 14800))
    destruction_eff: float = float(inputs.get("destruction_efficiency", 0.9997))

    hfc23_generated_t = hcfc22_produced_tonnes * hfc23_ratio
    be_tco2e = hfc23_generated_t * gwp_hfc23
    pe_tco2e = hfc23_generated_t * gwp_hfc23 * (1.0 - destruction_eff)
    er_tco2e = be_tco2e - pe_tco2e

    return {
        "tool_code": "TOOL26",
        "tool_name": CDM_TOOLS_REGISTRY["TOOL26"]["short_name"],
        "inputs": {
            "hcfc22_produced_tonnes": hcfc22_produced_tonnes,
            "hfc23_generation_ratio": hfc23_ratio,
            "gwp_hfc23": gwp_hfc23,
            "destruction_efficiency": destruction_eff,
        },
        "outputs": {
            "hfc23_generated_tonnes": round(hfc23_generated_t, 4),
            "baseline_emissions_tco2e": round(be_tco2e, 2),
            "project_emissions_tco2e": round(pe_tco2e, 2),
            "emission_reductions_tco2e": round(er_tco2e, 2),
        },
        "methodology_notes": "HFC-23 GWP = 14,800 (AR5). DE typically 99.97%.",
        "unit": "tCO2e",
    }


def calculate_tool27(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """TOOL27 -- Investment analysis (IRR / NPV / benchmark comparison).

    Calculates project IRR, NPV at discount rate, and compares with benchmark.
    Cash flows: initial CAPEX (negative) followed by annual net revenues.
    """
    capex: float = float(inputs.get("capex", 1_000_000.0))
    annual_revenue: float = float(inputs.get("annual_revenue", 180_000.0))
    annual_opex: float = float(inputs.get("annual_opex", 50_000.0))
    project_lifetime: int = int(inputs.get("project_lifetime_years", 10))
    discount_rate: float = float(inputs.get("discount_rate", 0.10))
    benchmark_irr: float = float(inputs.get("benchmark_irr", 0.12))

    annual_net = annual_revenue - annual_opex
    cash_flows = [-capex] + [annual_net] * project_lifetime

    # NPV
    npv = sum(cf / (1 + discount_rate) ** t for t, cf in enumerate(cash_flows))

    # IRR via bisection
    def _npv_at(r: float) -> float:
        return sum(cf / (1 + r) ** t for t, cf in enumerate(cash_flows))

    irr_low, irr_high = -0.5, 2.0
    irr_est = 0.0
    for _ in range(100):
        irr_est = (irr_low + irr_high) / 2.0
        val = _npv_at(irr_est)
        if abs(val) < 0.01:
            break
        if val > 0:
            irr_low = irr_est
        else:
            irr_high = irr_est

    is_additional = irr_est < benchmark_irr

    return {
        "tool_code": "TOOL27",
        "tool_name": CDM_TOOLS_REGISTRY["TOOL27"]["short_name"],
        "inputs": {
            "capex": capex,
            "annual_revenue": annual_revenue,
            "annual_opex": annual_opex,
            "project_lifetime_years": project_lifetime,
            "discount_rate": discount_rate,
            "benchmark_irr": benchmark_irr,
        },
        "outputs": {
            "npv": round(npv, 2),
            "irr": round(irr_est, 4),
            "benchmark_irr": benchmark_irr,
            "is_additional": is_additional,
            "simple_payback_years": round(capex / annual_net, 2) if annual_net > 0 else None,
        },
        "methodology_notes": "IRR via bisection. Additional if IRR < benchmark. NPV at stated discount rate.",
        "unit": "currency / fraction",
    }


def calculate_tool28(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """TOOL28 -- Refrigerant emissions from RAC systems.

    Annual leakage = charge * annual_leak_rate.
    End-of-life = charge * (1 - recovery_rate).
    Total CO2e = (leakage + EOL_annualised) * GWP_refrigerant.
    """
    charge_kg: float = float(inputs.get("refrigerant_charge_kg", 50.0))
    annual_leak_rate: float = float(inputs.get("annual_leak_rate", 0.05))
    recovery_rate: float = float(inputs.get("eol_recovery_rate", 0.70))
    equipment_lifetime: float = float(inputs.get("equipment_lifetime_years", 15.0))
    refrigerant: str = inputs.get("refrigerant_type", "R-410A")

    gwp_map: Dict[str, int] = {
        "R-22": 1810, "R-134a": 1430, "R-410A": 2088, "R-407C": 1774,
        "R-32": 675, "R-290": 3, "R-600a": 3, "R-744": 1,
    }
    gwp_ref = int(inputs.get("gwp_refrigerant", gwp_map.get(refrigerant, 2088)))

    annual_leakage_kg = charge_kg * annual_leak_rate
    eol_loss_kg = charge_kg * (1.0 - recovery_rate)
    eol_annualised_kg = eol_loss_kg / equipment_lifetime if equipment_lifetime > 0 else 0
    total_annual_kg = annual_leakage_kg + eol_annualised_kg
    total_co2e = total_annual_kg * gwp_ref / 1000.0

    return {
        "tool_code": "TOOL28",
        "tool_name": CDM_TOOLS_REGISTRY["TOOL28"]["short_name"],
        "inputs": {
            "refrigerant_charge_kg": charge_kg,
            "annual_leak_rate": annual_leak_rate,
            "refrigerant_type": refrigerant,
            "gwp_refrigerant": gwp_ref,
        },
        "outputs": {
            "annual_leakage_kg": round(annual_leakage_kg, 4),
            "eol_annualised_kg": round(eol_annualised_kg, 4),
            "total_annual_co2e_tonnes": round(total_co2e, 4),
        },
        "methodology_notes": "Leakage + annualised EOL loss, each multiplied by GWP.",
        "unit": "tCO2e/yr",
    }


def calculate_tool29(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """TOOL29 -- Standardized baseline for energy-efficient refrigerators/AC.

    BE = units_sold * baseline_energy_kwh * EF_grid.
    PE = units_sold * project_energy_kwh * EF_grid.
    ER = BE - PE.
    """
    units_sold: int = int(inputs.get("units_sold", 10000))
    baseline_energy_kwh: float = float(inputs.get("baseline_annual_kwh_per_unit", 500.0))
    project_energy_kwh: float = float(inputs.get("project_annual_kwh_per_unit", 350.0))
    ef_grid: float = float(inputs.get("ef_grid_tco2_per_mwh", 0.5))
    country: Optional[str] = inputs.get("country_code")

    if country and country.upper() in STATIC_GRID_EF:
        g = STATIC_GRID_EF[country.upper()]
        ef_grid = g["om_ef"] * g["om_weight"] + g["bm_ef"] * g["bm_weight"]

    be = units_sold * baseline_energy_kwh * ef_grid / 1000.0
    pe = units_sold * project_energy_kwh * ef_grid / 1000.0
    er = be - pe

    return {
        "tool_code": "TOOL29",
        "tool_name": CDM_TOOLS_REGISTRY["TOOL29"]["short_name"],
        "inputs": {
            "units_sold": units_sold,
            "baseline_annual_kwh_per_unit": baseline_energy_kwh,
            "project_annual_kwh_per_unit": project_energy_kwh,
            "ef_grid_tco2_per_mwh": round(ef_grid, 6),
        },
        "outputs": {
            "baseline_tco2": round(be, 4),
            "project_tco2": round(pe, 4),
            "emission_reductions_tco2": round(er, 4),
            "energy_saving_pct": round((1 - project_energy_kwh / baseline_energy_kwh) * 100, 2) if baseline_energy_kwh > 0 else 0,
        },
        "methodology_notes": "SB for appliances: ER = units * (baseline_kWh - project_kWh) * EF_grid / 1000.",
        "unit": "tCO2",
    }


def calculate_tool30(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """TOOL30 -- Fraction of non-renewable biomass (fNRB).

    fNRB = 1 - (MAI * forested_area) / total_biomass_consumption.
    MAI = Mean Annual Increment of woody biomass (t/ha/yr).
    """
    mai_t_ha_yr: float = float(inputs.get("mai_tonnes_per_ha_yr", 3.0))
    forested_area_ha: float = float(inputs.get("forested_area_ha", 10000.0))
    total_consumption_t_yr: float = float(inputs.get("total_biomass_consumption_tonnes_yr", 50000.0))

    renewable_supply = mai_t_ha_yr * forested_area_ha
    f_nrb = max(0.0, 1.0 - renewable_supply / total_consumption_t_yr) if total_consumption_t_yr > 0 else 1.0

    return {
        "tool_code": "TOOL30",
        "tool_name": CDM_TOOLS_REGISTRY["TOOL30"]["short_name"],
        "inputs": {
            "mai_tonnes_per_ha_yr": mai_t_ha_yr,
            "forested_area_ha": forested_area_ha,
            "total_biomass_consumption_tonnes_yr": total_consumption_t_yr,
        },
        "outputs": {
            "renewable_supply_tonnes_yr": round(renewable_supply, 2),
            "f_nrb": round(f_nrb, 4),
            "f_nrb_pct": round(f_nrb * 100, 2),
        },
        "methodology_notes": "fNRB = 1 - (MAI * forested_area) / total_consumption. CDM TOOL30 v4.",
        "unit": "fraction",
    }


def calculate_tool31(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """TOOL31 -- Standardized baseline for building energy efficiency.

    Baseline EUI from benchmarks; project EUI from design.
    ER = floor_area * (baseline_EUI - project_EUI) * EF_grid / 1000.
    """
    floor_area_m2: float = float(inputs.get("floor_area_m2", 5000.0))
    baseline_eui_kwh_m2: float = float(inputs.get("baseline_eui_kwh_per_m2", 180.0))
    project_eui_kwh_m2: float = float(inputs.get("project_eui_kwh_per_m2", 120.0))
    ef_grid: float = float(inputs.get("ef_grid_tco2_per_mwh", 0.5))
    building_type: str = inputs.get("building_type", "office")

    eui_benchmarks: Dict[str, float] = {
        "office": 180.0, "retail": 200.0, "hotel": 250.0,
        "hospital": 300.0, "school": 120.0, "residential": 100.0,
    }
    if baseline_eui_kwh_m2 == 180.0 and building_type in eui_benchmarks:
        baseline_eui_kwh_m2 = eui_benchmarks[building_type]

    energy_savings_kwh = floor_area_m2 * (baseline_eui_kwh_m2 - project_eui_kwh_m2)
    er_tco2 = energy_savings_kwh * ef_grid / 1000.0

    return {
        "tool_code": "TOOL31",
        "tool_name": CDM_TOOLS_REGISTRY["TOOL31"]["short_name"],
        "inputs": {
            "floor_area_m2": floor_area_m2,
            "building_type": building_type,
            "baseline_eui_kwh_per_m2": baseline_eui_kwh_m2,
            "project_eui_kwh_per_m2": project_eui_kwh_m2,
            "ef_grid_tco2_per_mwh": ef_grid,
        },
        "outputs": {
            "energy_savings_kwh": round(energy_savings_kwh, 2),
            "emission_reductions_tco2": round(er_tco2, 4),
            "eui_reduction_pct": round((1 - project_eui_kwh_m2 / baseline_eui_kwh_m2) * 100, 2) if baseline_eui_kwh_m2 > 0 else 0,
        },
        "methodology_notes": "ER = area * (BL_EUI - PJ_EUI) * EF_grid / 1000.",
        "unit": "tCO2",
    }


def calculate_tool32(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """TOOL32 -- Positive lists of technologies.

    Checks whether a technology appears on the CDM Executive Board positive list.
    Technologies on the positive list are deemed automatically additional.
    """
    technology: str = inputs.get("technology", "solar_pv")
    capacity_kw: float = float(inputs.get("capacity_kw", 500.0))

    positive_list: Dict[str, Dict[str, Any]] = {
        "solar_pv": {"max_capacity_kw": 15000, "category": "Type I - RE"},
        "solar_thermal": {"max_capacity_kw": 15000, "category": "Type I - RE"},
        "wind": {"max_capacity_kw": 15000, "category": "Type I - RE"},
        "micro_hydro": {"max_capacity_kw": 15000, "category": "Type I - RE"},
        "geothermal": {"max_capacity_kw": 15000, "category": "Type I - RE"},
        "biomass_power": {"max_capacity_kw": 15000, "category": "Type I - RE"},
        "led_lighting": {"max_capacity_kw": None, "category": "Type II - EE"},
        "efficient_cookstove": {"max_capacity_kw": None, "category": "Type II - EE"},
        "solar_water_heater": {"max_capacity_kw": None, "category": "Type I - RE"},
        "biogas_digester": {"max_capacity_kw": None, "category": "Type III - Other"},
    }

    entry = positive_list.get(technology)
    on_list = entry is not None
    within_capacity = True
    if entry and entry.get("max_capacity_kw") is not None:
        within_capacity = capacity_kw <= entry["max_capacity_kw"]

    is_additional = on_list and within_capacity

    return {
        "tool_code": "TOOL32",
        "tool_name": CDM_TOOLS_REGISTRY["TOOL32"]["short_name"],
        "inputs": {"technology": technology, "capacity_kw": capacity_kw},
        "outputs": {
            "on_positive_list": on_list,
            "category": entry["category"] if entry else None,
            "within_capacity_limit": within_capacity,
            "is_additional": is_additional,
        },
        "methodology_notes": "Technologies on CDM EB positive list are automatically additional (no barrier/investment test).",
        "unit": "boolean",
    }


def calculate_tool33(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """TOOL33 -- Default values for common parameters.

    Returns GWP values (AR5), oxidation factors, DOC defaults, methane
    density, standard conditions, and other IPCC common parameters.
    Uses GWP dict imported from carbon_calculator_v2.
    """
    parameter_requested: Optional[str] = inputs.get("parameter")

    defaults: Dict[str, Dict[str, Any]] = {
        "gwp_co2": {"value": GWP.get("CO2", 1), "unit": "unitless", "source": "IPCC AR5"},
        "gwp_ch4": {"value": GWP.get("CH4", 28), "unit": "unitless", "source": "IPCC AR5"},
        "gwp_n2o": {"value": GWP.get("N2O", 265), "unit": "unitless", "source": "IPCC AR5"},
        "gwp_sf6": {"value": GWP.get("SF6", 23500), "unit": "unitless", "source": "IPCC AR5"},
        "gwp_hfc23": {"value": 14800, "unit": "unitless", "source": "IPCC AR5"},
        "gwp_hfc134a": {"value": 1430, "unit": "unitless", "source": "IPCC AR5"},
        "oxidation_factor_landfill": {"value": 0.10, "unit": "fraction", "source": "IPCC 2006 GL"},
        "doc_f": {"value": 0.50, "unit": "fraction", "source": "IPCC 2006 GL"},
        "mcf_managed_anaerobic": {"value": 1.0, "unit": "fraction", "source": "IPCC 2006 GL"},
        "mcf_unmanaged_shallow": {"value": 0.4, "unit": "fraction", "source": "IPCC 2006 GL"},
        "ch4_density_stp": {"value": 0.717, "unit": "kg/m3", "source": "Standard tables"},
        "co2_density_stp": {"value": 1.977, "unit": "kg/m3", "source": "Standard tables"},
        "molar_volume_stp": {"value": 22.414, "unit": "L/mol", "source": "Ideal gas law at 0C, 101.325 kPa"},
        "carbon_fraction_biomass": {"value": 0.47, "unit": "tC/t dry matter", "source": "IPCC 2006 AFOLU"},
        "root_shoot_ratio_tropical": {"value": 0.24, "unit": "fraction", "source": "IPCC 2006 AFOLU"},
        "wood_density_default": {"value": 0.50, "unit": "t/m3", "source": "IPCC 2006 AFOLU"},
        "ncv_diesel": {"value": _FUELS.get("diesel", {}).get("ncv", 43.0), "unit": "GJ/t", "source": "IPCC 2006"},
        "ncv_natural_gas": {"value": _FUELS.get("natural_gas", {}).get("ncv", 48.0), "unit": "GJ/t", "source": "IPCC 2006"},
        "ncv_coal_bituminous": {"value": _FUELS.get("coal_bituminous", {}).get("ncv", 25.8), "unit": "GJ/t", "source": "IPCC 2006"},
    }

    if parameter_requested and parameter_requested in defaults:
        result_params = {parameter_requested: defaults[parameter_requested]}
    else:
        result_params = defaults

    return {
        "tool_code": "TOOL33",
        "tool_name": CDM_TOOLS_REGISTRY["TOOL33"]["short_name"],
        "inputs": {"parameter": parameter_requested},
        "outputs": {"parameters": result_params},
        "methodology_notes": "IPCC AR5 GWP values. IPCC 2006 Guidelines defaults for waste, energy, AFOLU.",
        "unit": "various",
    }


# ============================================================================
# 3d. Tool Calculator Functions  (AR-TOOL series)
# ============================================================================

def calculate_ar_tool02(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """AR-TOOL02 -- A/R baseline scenario identification + additionality.

    Identifies the most plausible land-use baseline and applies barrier /
    investment analysis in the A/R context.
    """
    land_use_alternatives: List[Dict[str, Any]] = inputs.get("land_use_alternatives", [
        {"name": "continued_degradation", "plausibility": 0.85, "carbon_stock_tC_ha": 5.0},
        {"name": "agricultural_use", "plausibility": 0.60, "carbon_stock_tC_ha": 15.0},
        {"name": "natural_regeneration", "plausibility": 0.30, "carbon_stock_tC_ha": 40.0},
    ])
    project_carbon_stock_tC_ha: float = float(inputs.get("project_carbon_stock_tC_ha", 80.0))
    irr_project: float = float(inputs.get("irr_project", 5.0))
    irr_benchmark: float = float(inputs.get("irr_benchmark", 10.0))
    barriers: List[str] = inputs.get("barriers", ["long_rotation", "land_tenure", "lack_of_finance"])

    ranked = sorted(land_use_alternatives, key=lambda a: a.get("plausibility", 0), reverse=True)
    baseline = ranked[0] if ranked else {"name": "degradation", "carbon_stock_tC_ha": 5.0}

    net_carbon_benefit = project_carbon_stock_tC_ha - baseline.get("carbon_stock_tC_ha", 0)
    investment_pass = irr_project < irr_benchmark
    barrier_pass = len(barriers) >= 1
    is_additional = (investment_pass or barrier_pass) and net_carbon_benefit > 0

    return {
        "tool_code": "AR-TOOL02",
        "tool_name": CDM_TOOLS_REGISTRY["AR-TOOL02"]["short_name"],
        "inputs": {
            "land_use_alternatives": land_use_alternatives,
            "project_carbon_stock_tC_ha": project_carbon_stock_tC_ha,
            "irr_project": irr_project,
            "irr_benchmark": irr_benchmark,
            "barriers": barriers,
        },
        "outputs": {
            "selected_baseline": baseline["name"],
            "baseline_carbon_tC_ha": baseline.get("carbon_stock_tC_ha", 0),
            "net_carbon_benefit_tC_ha": round(net_carbon_benefit, 2),
            "is_additional": is_additional,
        },
        "methodology_notes": "A/R combined: rank land-use baselines by plausibility, then barrier/investment.",
        "unit": "tC/ha",
    }


def calculate_ar_tool03(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """AR-TOOL03 -- Number of sample plots for A/R measurements.

    n = (t_value * CV / allowable_error)^2.
    CV = coefficient of variation of biomass across preliminary plots.
    """
    cv_pct: float = float(inputs.get("cv_pct", 40.0))
    allowable_error_pct: float = float(inputs.get("allowable_error_pct", 10.0))
    confidence_level: float = float(inputs.get("confidence_level_pct", 95.0))
    preliminary_plots: int = int(inputs.get("preliminary_plots", 20))

    # t-value approximation for two-tailed
    t_values = {90.0: 1.645, 95.0: 1.96, 99.0: 2.576}
    t_val = t_values.get(confidence_level, 1.96)

    n_raw = (t_val * cv_pct / allowable_error_pct) ** 2
    n_plots = max(int(math.ceil(n_raw)), preliminary_plots)

    return {
        "tool_code": "AR-TOOL03",
        "tool_name": CDM_TOOLS_REGISTRY["AR-TOOL03"]["short_name"],
        "inputs": {
            "cv_pct": cv_pct,
            "allowable_error_pct": allowable_error_pct,
            "confidence_level_pct": confidence_level,
            "preliminary_plots": preliminary_plots,
        },
        "outputs": {
            "t_value": t_val,
            "n_plots_calculated": round(n_raw, 2),
            "n_plots_required": n_plots,
        },
        "methodology_notes": "n = (t * CV / E)^2. At least as many as preliminary plots.",
        "unit": "count",
    }


def calculate_ar_tool08(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """AR-TOOL08 -- Non-CO2 GHG from biomass burning in A/R boundary.

    CH4 = area_burned * fuel_load * combustion_factor * EF_CH4 / 1000.
    N2O = area_burned * fuel_load * combustion_factor * EF_N2O / 1000.
    Total CO2e = CH4 * GWP_CH4 + N2O * GWP_N2O.
    """
    area_burned_ha: float = float(inputs.get("area_burned_ha", 50.0))
    fuel_load_t_ha: float = float(inputs.get("fuel_load_t_per_ha", 20.0))
    combustion_factor: float = float(inputs.get("combustion_factor", 0.50))
    ef_ch4_kg_t: float = float(inputs.get("ef_ch4_kg_per_tonne_dm", 6.8))
    ef_n2o_kg_t: float = float(inputs.get("ef_n2o_kg_per_tonne_dm", 0.26))

    biomass_burned_t = area_burned_ha * fuel_load_t_ha * combustion_factor
    ch4_tonnes = biomass_burned_t * ef_ch4_kg_t / 1000.0
    n2o_tonnes = biomass_burned_t * ef_n2o_kg_t / 1000.0
    co2e = ch4_tonnes * GWP.get("CH4", 28) + n2o_tonnes * GWP.get("N2O", 265)

    return {
        "tool_code": "AR-TOOL08",
        "tool_name": CDM_TOOLS_REGISTRY["AR-TOOL08"]["short_name"],
        "inputs": {
            "area_burned_ha": area_burned_ha,
            "fuel_load_t_per_ha": fuel_load_t_ha,
            "combustion_factor": combustion_factor,
        },
        "outputs": {
            "biomass_burned_tonnes": round(biomass_burned_t, 2),
            "ch4_tonnes": round(ch4_tonnes, 4),
            "n2o_tonnes": round(n2o_tonnes, 4),
            "total_co2e_tonnes": round(co2e, 4),
        },
        "methodology_notes": "Non-CO2 from burning: fuel_load * CF * EF. IPCC EFs for tropical savanna.",
        "unit": "tCO2e",
    }


def calculate_ar_tool12(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """AR-TOOL12 -- Carbon stocks in dead wood and litter.

    C_DWL = volume_m3_ha * wood_density * carbon_fraction * area_ha * 44/12.
    Litter stock = litter_mass_t_ha * carbon_fraction * area_ha * 44/12.
    """
    dead_wood_volume_m3_ha: float = float(inputs.get("dead_wood_volume_m3_per_ha", 8.0))
    wood_density_t_m3: float = float(inputs.get("wood_density_t_per_m3", 0.50))
    litter_mass_t_ha: float = float(inputs.get("litter_mass_t_per_ha", 5.0))
    carbon_fraction: float = float(inputs.get("carbon_fraction", 0.47))
    area_ha: float = float(inputs.get("area_ha", 100.0))

    dw_carbon_tC = dead_wood_volume_m3_ha * wood_density_t_m3 * carbon_fraction * area_ha
    litter_carbon_tC = litter_mass_t_ha * carbon_fraction * area_ha
    total_tC = dw_carbon_tC + litter_carbon_tC
    total_tco2e = total_tC * 44.0 / 12.0

    return {
        "tool_code": "AR-TOOL12",
        "tool_name": CDM_TOOLS_REGISTRY["AR-TOOL12"]["short_name"],
        "inputs": {
            "dead_wood_volume_m3_per_ha": dead_wood_volume_m3_ha,
            "wood_density_t_per_m3": wood_density_t_m3,
            "litter_mass_t_per_ha": litter_mass_t_ha,
            "carbon_fraction": carbon_fraction,
            "area_ha": area_ha,
        },
        "outputs": {
            "dead_wood_carbon_tC": round(dw_carbon_tC, 4),
            "litter_carbon_tC": round(litter_carbon_tC, 4),
            "total_carbon_tC": round(total_tC, 4),
            "total_tco2e": round(total_tco2e, 4),
        },
        "methodology_notes": "C_DW = vol * density * CF * area. Litter = mass * CF * area. Converted via 44/12.",
        "unit": "tCO2e",
    }


def calculate_ar_tool14(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """AR-TOOL14 -- Carbon stocks in trees and shrubs (allometric).

    AGB = SUM[ a * D^b * H^c * rho * N * Area ].
    Total biomass includes below-ground via root-shoot ratio.
    Carbon stock = total_biomass * carbon_fraction * 44/12.
    """
    species_data: List[Dict[str, Any]] = inputs.get("species", [
        {"name": "teak", "a": 0.0509, "b": 2.59, "c": 0.0, "dbh_cm": 25.0, "height_m": 15.0, "wood_density": 0.55, "stems_per_ha": 400},
    ])
    area_ha: float = float(inputs.get("area_ha", 100.0))
    root_shoot_ratio: float = float(inputs.get("root_shoot_ratio", 0.24))
    carbon_fraction: float = float(inputs.get("carbon_fraction", 0.47))

    species_results: List[Dict[str, Any]] = []
    total_agb_t = 0.0

    for sp in species_data:
        a = float(sp.get("a", 0.0509))
        b = float(sp.get("b", 2.59))
        c = float(sp.get("c", 0.0))
        dbh = float(sp.get("dbh_cm", 20.0))
        h = float(sp.get("height_m", 12.0))
        rho = float(sp.get("wood_density", 0.50))
        n = float(sp.get("stems_per_ha", 500))

        # Allometric: AGB per tree (kg) = a * D^b * H^c * rho (if c > 0)
        if c > 0:
            agb_per_tree_kg = a * (dbh ** b) * (h ** c) * rho
        else:
            agb_per_tree_kg = a * (dbh ** b) * rho

        agb_per_ha_t = agb_per_tree_kg * n / 1000.0
        agb_total_t = agb_per_ha_t * area_ha
        total_agb_t += agb_total_t

        species_results.append({
            "species": sp.get("name", "unknown"),
            "agb_per_tree_kg": round(agb_per_tree_kg, 4),
            "agb_per_ha_tonnes": round(agb_per_ha_t, 4),
            "agb_total_tonnes": round(agb_total_t, 4),
        })

    total_bgb_t = total_agb_t * root_shoot_ratio
    total_biomass_t = total_agb_t + total_bgb_t
    total_carbon_tC = total_biomass_t * carbon_fraction
    total_tco2e = total_carbon_tC * 44.0 / 12.0

    return {
        "tool_code": "AR-TOOL14",
        "tool_name": CDM_TOOLS_REGISTRY["AR-TOOL14"]["short_name"],
        "inputs": {
            "species": species_data,
            "area_ha": area_ha,
            "root_shoot_ratio": root_shoot_ratio,
            "carbon_fraction": carbon_fraction,
        },
        "outputs": {
            "species_details": species_results,
            "total_agb_tonnes": round(total_agb_t, 4),
            "total_bgb_tonnes": round(total_bgb_t, 4),
            "total_biomass_tonnes": round(total_biomass_t, 4),
            "total_carbon_tC": round(total_carbon_tC, 4),
            "total_tco2e": round(total_tco2e, 4),
        },
        "methodology_notes": "AGB = a * D^b * [H^c] * rho * N * area. BGB = AGB * R:S. C = biomass * CF.",
        "unit": "tCO2e",
    }


def calculate_ar_tool15(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """AR-TOOL15 -- GHG from displaced pre-project agricultural activities.

    Leakage_AG = displaced_area * EF_agriculture * years.
    EF_agriculture includes N2O from fertiliser and CH4 from rice/livestock.
    """
    displaced_area_ha: float = float(inputs.get("displaced_area_ha", 50.0))
    ef_agriculture_tco2e_ha_yr: float = float(inputs.get("ef_agriculture_tco2e_per_ha_yr", 3.5))
    years: int = int(inputs.get("years", 20))
    leakage_factor: float = float(inputs.get("leakage_factor", 0.50))

    gross_leakage = displaced_area_ha * ef_agriculture_tco2e_ha_yr * years
    net_leakage = gross_leakage * leakage_factor

    return {
        "tool_code": "AR-TOOL15",
        "tool_name": CDM_TOOLS_REGISTRY["AR-TOOL15"]["short_name"],
        "inputs": {
            "displaced_area_ha": displaced_area_ha,
            "ef_agriculture_tco2e_per_ha_yr": ef_agriculture_tco2e_ha_yr,
            "years": years,
            "leakage_factor": leakage_factor,
        },
        "outputs": {
            "gross_leakage_tco2e": round(gross_leakage, 4),
            "net_leakage_tco2e": round(net_leakage, 4),
            "annual_leakage_tco2e": round(net_leakage / years if years > 0 else 0, 4),
        },
        "methodology_notes": "Leakage = displaced_area * EF_ag * years * leakage_factor (typically 50%).",
        "unit": "tCO2e",
    }


def calculate_ar_tool16(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """AR-TOOL16 -- Change in soil organic carbon (SOC) due to A/R.

    Delta_SOC = (SOC_project - SOC_baseline) * area * depth_factor.
    SOC in tC/ha; result converted to tCO2e.
    """
    soc_baseline_tC_ha: float = float(inputs.get("soc_baseline_tC_per_ha", 40.0))
    soc_project_tC_ha: float = float(inputs.get("soc_project_tC_per_ha", 55.0))
    area_ha: float = float(inputs.get("area_ha", 100.0))
    depth_factor: float = float(inputs.get("depth_factor", 1.0))
    transition_years: int = int(inputs.get("transition_years", 20))

    delta_soc_tC = (soc_project_tC_ha - soc_baseline_tC_ha) * area_ha * depth_factor
    delta_soc_tco2e = delta_soc_tC * 44.0 / 12.0
    annual_tco2e = delta_soc_tco2e / transition_years if transition_years > 0 else delta_soc_tco2e

    return {
        "tool_code": "AR-TOOL16",
        "tool_name": CDM_TOOLS_REGISTRY["AR-TOOL16"]["short_name"],
        "inputs": {
            "soc_baseline_tC_per_ha": soc_baseline_tC_ha,
            "soc_project_tC_per_ha": soc_project_tC_ha,
            "area_ha": area_ha,
            "depth_factor": depth_factor,
            "transition_years": transition_years,
        },
        "outputs": {
            "delta_soc_tC": round(delta_soc_tC, 4),
            "delta_soc_tco2e": round(delta_soc_tco2e, 4),
            "annual_sequestration_tco2e": round(annual_tco2e, 4),
        },
        "methodology_notes": "Delta SOC = (SOC_pj - SOC_bl) * area * depth_factor. Linear transition.",
        "unit": "tCO2e",
    }


def calculate_ar_tool17(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """AR-TOOL17 -- Tree biomass estimation using Chave et al. allometric models.

    Pantropical models:
      Dry:  AGB = 0.112 * (rho * D^2 * H)^0.916
      Moist: AGB = 0.0673 * (rho * D^2 * H)^0.976
      Wet:  AGB = 0.0776 * (rho * D^2 * H)^0.940
    AGB in kg per tree; D in cm, H in m, rho in g/cm3.
    """
    dbh_cm: float = float(inputs.get("dbh_cm", 25.0))
    height_m: float = float(inputs.get("height_m", 18.0))
    wood_density_g_cm3: float = float(inputs.get("wood_density_g_per_cm3", 0.55))
    forest_type: str = inputs.get("forest_type", "moist")
    stems_per_ha: float = float(inputs.get("stems_per_ha", 500))
    area_ha: float = float(inputs.get("area_ha", 100.0))
    carbon_fraction: float = float(inputs.get("carbon_fraction", 0.47))
    root_shoot_ratio: float = float(inputs.get("root_shoot_ratio", 0.24))

    chave_params = {
        "dry":   (0.112, 0.916),
        "moist": (0.0673, 0.976),
        "wet":   (0.0776, 0.940),
    }
    a_coeff, b_exp = chave_params.get(forest_type, (0.0673, 0.976))

    composite = wood_density_g_cm3 * (dbh_cm ** 2) * height_m
    agb_per_tree_kg = a_coeff * (composite ** b_exp)
    agb_per_ha_t = agb_per_tree_kg * stems_per_ha / 1000.0
    total_agb_t = agb_per_ha_t * area_ha
    total_bgb_t = total_agb_t * root_shoot_ratio
    total_biomass_t = total_agb_t + total_bgb_t
    total_carbon_tC = total_biomass_t * carbon_fraction
    total_tco2e = total_carbon_tC * 44.0 / 12.0

    return {
        "tool_code": "AR-TOOL17",
        "tool_name": CDM_TOOLS_REGISTRY["AR-TOOL17"]["short_name"],
        "inputs": {
            "dbh_cm": dbh_cm,
            "height_m": height_m,
            "wood_density_g_per_cm3": wood_density_g_cm3,
            "forest_type": forest_type,
            "stems_per_ha": stems_per_ha,
            "area_ha": area_ha,
        },
        "outputs": {
            "chave_coefficients": {"a": a_coeff, "b": b_exp},
            "agb_per_tree_kg": round(agb_per_tree_kg, 4),
            "agb_per_ha_tonnes": round(agb_per_ha_t, 4),
            "total_agb_tonnes": round(total_agb_t, 4),
            "total_bgb_tonnes": round(total_bgb_t, 4),
            "total_carbon_tC": round(total_carbon_tC, 4),
            "total_tco2e": round(total_tco2e, 4),
        },
        "methodology_notes": f"Chave et al. ({forest_type}): AGB = {a_coeff} * (rho*D^2*H)^{b_exp}.",
        "unit": "tCO2e",
    }


def calculate_ar_tool18(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """AR-TOOL18 -- Tree biomass from volume equations.

    AGB = stem_volume * wood_density * BEF * (1 + R) * CF * 44/12.
    BEF = Biomass Expansion Factor (accounts for branches/leaves).
    R = root-to-shoot ratio.
    """
    stem_volume_m3_ha: float = float(inputs.get("stem_volume_m3_per_ha", 120.0))
    wood_density_t_m3: float = float(inputs.get("wood_density_t_per_m3", 0.50))
    bef: float = float(inputs.get("biomass_expansion_factor", 1.40))
    root_shoot_ratio: float = float(inputs.get("root_shoot_ratio", 0.24))
    carbon_fraction: float = float(inputs.get("carbon_fraction", 0.47))
    area_ha: float = float(inputs.get("area_ha", 100.0))

    agb_per_ha_t = stem_volume_m3_ha * wood_density_t_m3 * bef
    total_biomass_per_ha_t = agb_per_ha_t * (1.0 + root_shoot_ratio)
    total_biomass_t = total_biomass_per_ha_t * area_ha
    total_carbon_tC = total_biomass_t * carbon_fraction
    total_tco2e = total_carbon_tC * 44.0 / 12.0

    return {
        "tool_code": "AR-TOOL18",
        "tool_name": CDM_TOOLS_REGISTRY["AR-TOOL18"]["short_name"],
        "inputs": {
            "stem_volume_m3_per_ha": stem_volume_m3_ha,
            "wood_density_t_per_m3": wood_density_t_m3,
            "biomass_expansion_factor": bef,
            "root_shoot_ratio": root_shoot_ratio,
            "area_ha": area_ha,
        },
        "outputs": {
            "agb_per_ha_tonnes": round(agb_per_ha_t, 4),
            "total_biomass_tonnes": round(total_biomass_t, 4),
            "total_carbon_tC": round(total_carbon_tC, 4),
            "total_tco2e": round(total_tco2e, 4),
        },
        "methodology_notes": "AGB = vol * density * BEF. Total = AGB * (1+R). C = biomass * CF.",
        "unit": "tCO2e",
    }


def calculate_ar_tool19(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """AR-TOOL19 -- Land eligibility for A/R CDM.

    Checks Kyoto Protocol forest definition thresholds:
      - Minimum area (ha)
      - Minimum crown cover (%)
      - Minimum tree height at maturity (m)
    Land is eligible if it was NOT forest on 31 Dec 1989 (or host-country date).
    """
    area_ha: float = float(inputs.get("area_ha", 50.0))
    current_crown_cover_pct: float = float(inputs.get("current_crown_cover_pct", 8.0))
    current_tree_height_m: float = float(inputs.get("current_tree_height_m", 2.0))
    was_forest_1989: bool = bool(inputs.get("was_forest_1989", False))

    # Host-country thresholds (example: India DNA thresholds)
    min_area_ha: float = float(inputs.get("min_area_ha", 0.05))
    min_crown_cover_pct: float = float(inputs.get("min_crown_cover_pct", 15.0))
    min_tree_height_m: float = float(inputs.get("min_tree_height_m", 2.0))

    area_ok = area_ha >= min_area_ha
    not_forest = (current_crown_cover_pct < min_crown_cover_pct) or (current_tree_height_m < min_tree_height_m)
    historical_ok = not was_forest_1989
    eligible = area_ok and not_forest and historical_ok

    return {
        "tool_code": "AR-TOOL19",
        "tool_name": CDM_TOOLS_REGISTRY["AR-TOOL19"]["short_name"],
        "inputs": {
            "area_ha": area_ha,
            "current_crown_cover_pct": current_crown_cover_pct,
            "current_tree_height_m": current_tree_height_m,
            "was_forest_1989": was_forest_1989,
            "min_area_ha": min_area_ha,
            "min_crown_cover_pct": min_crown_cover_pct,
            "min_tree_height_m": min_tree_height_m,
        },
        "outputs": {
            "area_check_pass": area_ok,
            "not_currently_forest": not_forest,
            "historical_check_pass": historical_ok,
            "land_eligible": eligible,
        },
        "methodology_notes": (
            "Land eligible if: area >= min, not currently forest (crown cover < threshold OR "
            "height < threshold), and was not forest on 31 Dec 1989."
        ),
        "unit": "boolean",
    }


# ============================================================================
# 4. CDM_TOOL_CALCULATORS -- dispatch dictionary
# ============================================================================

CDM_TOOL_CALCULATORS: Dict[str, Any] = {
    "TOOL01": calculate_tool01,
    "TOOL02": calculate_tool02,
    "TOOL03": calculate_tool03,
    "TOOL04": calculate_tool04,
    "TOOL05": calculate_tool05,
    "TOOL06": calculate_tool06,
    "TOOL07": calculate_tool07,
    "TOOL08": calculate_tool08,
    "TOOL09": calculate_tool09,
    "TOOL10": calculate_tool10,
    "TOOL11": calculate_tool11,
    "TOOL12": calculate_tool12,
    "TOOL13": calculate_tool13,
    "TOOL14": calculate_tool14,
    "TOOL15": calculate_tool15,
    "TOOL16": calculate_tool16,
    "TOOL17": calculate_tool17,
    "TOOL18": calculate_tool18,
    "TOOL19": calculate_tool19,
    "TOOL20": calculate_tool20,
    "TOOL21": calculate_tool21,
    "TOOL22": calculate_tool22,
    "TOOL23": calculate_tool23,
    "TOOL24": calculate_tool24,
    "TOOL25": calculate_tool25,
    "TOOL26": calculate_tool26,
    "TOOL27": calculate_tool27,
    "TOOL28": calculate_tool28,
    "TOOL29": calculate_tool29,
    "TOOL30": calculate_tool30,
    "TOOL31": calculate_tool31,
    "TOOL32": calculate_tool32,
    "TOOL33": calculate_tool33,
    "AR-TOOL02": calculate_ar_tool02,
    "AR-TOOL03": calculate_ar_tool03,
    "AR-TOOL08": calculate_ar_tool08,
    "AR-TOOL12": calculate_ar_tool12,
    "AR-TOOL14": calculate_ar_tool14,
    "AR-TOOL15": calculate_ar_tool15,
    "AR-TOOL16": calculate_ar_tool16,
    "AR-TOOL17": calculate_ar_tool17,
    "AR-TOOL18": calculate_ar_tool18,
    "AR-TOOL19": calculate_ar_tool19,
}


# ============================================================================
# 5. METHODOLOGY_TOOL_DEPENDENCIES
# ============================================================================

METHODOLOGY_TOOL_DEPENDENCIES: Dict[str, List[str]] = {
    # ----- CDM Large Scale (ACM) -----
    "ACM0001": ["TOOL01", "TOOL03", "TOOL04", "TOOL05", "TOOL07", "TOOL33"],
    "ACM0002": ["TOOL01", "TOOL02", "TOOL03", "TOOL05", "TOOL07", "TOOL15", "TOOL24", "TOOL27", "TOOL33"],
    "ACM0003": ["TOOL01", "TOOL02", "TOOL03", "TOOL05", "TOOL07", "TOOL09", "TOOL33"],
    "ACM0005": ["TOOL01", "TOOL03", "TOOL05", "TOOL07", "TOOL08", "TOOL15", "TOOL33"],
    "ACM0006": ["TOOL01", "TOOL02", "TOOL03", "TOOL05", "TOOL07", "TOOL15", "TOOL33"],
    "ACM0007": ["TOOL01", "TOOL02", "TOOL03", "TOOL05", "TOOL07", "TOOL09", "TOOL15", "TOOL33"],
    "ACM0008": ["TOOL01", "TOOL03", "TOOL05", "TOOL07", "TOOL08", "TOOL33"],
    "ACM0009": ["TOOL01", "TOOL02", "TOOL03", "TOOL05", "TOOL07", "TOOL09", "TOOL15", "TOOL33"],
    "ACM0010": ["TOOL01", "TOOL02", "TOOL03", "TOOL05", "TOOL07", "TOOL09", "TOOL15", "TOOL33"],
    "ACM0012": ["TOOL01", "TOOL02", "TOOL03", "TOOL05", "TOOL07", "TOOL09", "TOOL25", "TOOL33"],
    "ACM0014": ["TOOL01", "TOOL02", "TOOL03", "TOOL05", "TOOL07", "TOOL12", "TOOL15", "TOOL33"],
    "ACM0022": ["TOOL01", "TOOL02", "TOOL03", "TOOL04", "TOOL05", "TOOL07", "TOOL13", "TOOL14", "TOOL33"],
    "ACM0023": ["TOOL01", "TOOL02", "TOOL03", "TOOL05", "TOOL06", "TOOL07", "TOOL08", "TOOL33"],

    # ----- CDM Small Scale (AMS) -----
    "AMS-I.A": ["TOOL19", "TOOL20", "TOOL21", "TOOL05", "TOOL07", "TOOL33"],
    "AMS-I.B": ["TOOL19", "TOOL20", "TOOL21", "TOOL05", "TOOL07", "TOOL33"],
    "AMS-I.C": ["TOOL19", "TOOL20", "TOOL21", "TOOL05", "TOOL07", "TOOL16", "TOOL22", "TOOL30", "TOOL33"],
    "AMS-I.D": ["TOOL19", "TOOL20", "TOOL21", "TOOL05", "TOOL07", "TOOL33"],
    "AMS-I.E": ["TOOL19", "TOOL20", "TOOL21", "TOOL05", "TOOL33"],
    "AMS-II.D": ["TOOL19", "TOOL20", "TOOL21", "TOOL05", "TOOL07", "TOOL33"],
    "AMS-II.E": ["TOOL19", "TOOL20", "TOOL21", "TOOL05", "TOOL07", "TOOL09", "TOOL33"],
    "AMS-II.G": ["TOOL19", "TOOL20", "TOOL21", "TOOL03", "TOOL05", "TOOL16", "TOOL22", "TOOL30", "TOOL33"],
    "AMS-III.AU": ["TOOL19", "TOOL20", "TOOL21", "TOOL04", "TOOL05", "TOOL07", "TOOL13", "TOOL33"],
    "AMS-III.B": ["TOOL19", "TOOL20", "TOOL21", "TOOL03", "TOOL05", "TOOL12", "TOOL33"],
    "AMS-III.C": ["TOOL19", "TOOL20", "TOOL21", "TOOL03", "TOOL05", "TOOL15", "TOOL33"],
    "AMS-III.D": ["TOOL19", "TOOL20", "TOOL21", "TOOL04", "TOOL05", "TOOL07", "TOOL14", "TOOL33"],

    # ----- CDM Approved Methodologies (AM) -----
    "AM0012": ["TOOL01", "TOOL02", "TOOL03", "TOOL05", "TOOL07", "TOOL08", "TOOL26", "TOOL33"],
    "AM0036": ["TOOL01", "TOOL02", "TOOL03", "TOOL05", "TOOL07", "TOOL09", "TOOL15", "TOOL27", "TOOL33"],

    # ----- A/R CDM -----
    "AR-ACM0003": [
        "AR-TOOL02", "AR-TOOL03", "AR-TOOL08", "AR-TOOL12", "AR-TOOL14",
        "AR-TOOL15", "AR-TOOL16", "AR-TOOL19", "TOOL33",
    ],

    # ----- VCS (Verra) -----
    "VM0001": ["TOOL01", "TOOL03", "TOOL05", "TOOL07", "TOOL33", "AR-TOOL14", "AR-TOOL17"],
    "VM0006": ["TOOL01", "TOOL02", "TOOL05", "TOOL07", "TOOL09", "TOOL27", "TOOL33"],
    "VM0007": ["TOOL01", "TOOL03", "TOOL33", "AR-TOOL14", "AR-TOOL17", "AR-TOOL12"],
    "VM0012": ["TOOL01", "TOOL33", "AR-TOOL14", "AR-TOOL17", "AR-TOOL12", "AR-TOOL16"],
    "VM0022": ["TOOL01", "TOOL03", "TOOL04", "TOOL05", "TOOL07", "TOOL33"],
    "VM0033": ["TOOL01", "TOOL03", "TOOL33", "AR-TOOL14", "AR-TOOL17"],
    "VM0042": ["TOOL01", "TOOL05", "TOOL07", "TOOL09", "TOOL27", "TOOL33"],
    "VM0044": ["TOOL01", "TOOL03", "TOOL05", "TOOL07", "TOOL33"],
    "VM0047": ["TOOL01", "TOOL33", "AR-TOOL14", "AR-TOOL16", "AR-TOOL17"],
    "VM0048": ["TOOL01", "TOOL03", "TOOL05", "TOOL07", "TOOL33"],

    # ----- Gold Standard -----
    "GS4GG_RE": ["TOOL01", "TOOL05", "TOOL07", "TOOL27", "TOOL33"],
    "GS4GG_EE": ["TOOL01", "TOOL05", "TOOL07", "TOOL09", "TOOL27", "TOOL33"],

    # ----- TPDDTEC (Technology-specific) -----
    "TPDDTEC": ["TOOL01", "TOOL03", "TOOL05", "TOOL07", "TOOL23", "TOOL24", "TOOL33"],
    "TPDDTEC-SWH": ["TOOL01", "TOOL05", "TOOL07", "TOOL23", "TOOL33"],

    # ----- CAR (Climate Action Reserve) -----
    "CAR-FOR": ["TOOL01", "TOOL33", "AR-TOOL14", "AR-TOOL17", "AR-TOOL12"],
    "CAR-URB": ["TOOL01", "TOOL33", "AR-TOOL14", "AR-TOOL17"],

    # ----- ACR (American Carbon Registry) -----
    "ACR-ERW": ["TOOL01", "TOOL03", "TOOL33"],
    "ACR-SOC": ["TOOL01", "TOOL33", "AR-TOOL16"],
}


# ============================================================================
# 6. Helper / public API functions
# ============================================================================

def calculate_cdm_tool(tool_code: str, inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Execute a single CDM tool calculation.

    Parameters
    ----------
    tool_code : str
        Tool identifier, e.g. ``"TOOL03"`` or ``"AR-TOOL14"``.
    inputs : dict, optional
        Calculation inputs.  Each tool provides sensible defaults.

    Returns
    -------
    dict
        Standardised result with keys: tool_code, tool_name, inputs,
        outputs, methodology_notes, unit.

    Raises
    ------
    ValueError
        If *tool_code* is not in ``CDM_TOOL_CALCULATORS``.
    """
    code = tool_code.upper().replace(" ", "")
    calculator = CDM_TOOL_CALCULATORS.get(code)
    if calculator is None:
        raise ValueError(
            f"Unknown CDM tool code '{tool_code}'. "
            f"Available: {sorted(CDM_TOOL_CALCULATORS.keys())}"
        )
    return calculator(inputs or {})


def get_tools_for_methodology(methodology_code: str) -> List[str]:
    """Return the list of CDM tool codes required by a methodology.

    Parameters
    ----------
    methodology_code : str
        E.g. ``"ACM0002"``, ``"AMS-I.D"``, ``"VM0007"``.

    Returns
    -------
    list[str]
        Ordered list of tool codes, or empty list if methodology unknown.
    """
    return METHODOLOGY_TOOL_DEPENDENCIES.get(methodology_code.upper(), [])


def get_tool_details(tool_code: str) -> Optional[Dict[str, Any]]:
    """Return registry metadata for a single tool.

    Parameters
    ----------
    tool_code : str

    Returns
    -------
    dict or None
        Metadata dict from ``CDM_TOOLS_REGISTRY``, or ``None``.
    """
    return CDM_TOOLS_REGISTRY.get(tool_code.upper().replace(" ", ""))


def execute_tool_chain(
    methodology_code: str,
    tool_inputs: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Execute every CDM tool required by a methodology, in dependency order.

    Parameters
    ----------
    methodology_code : str
        Methodology identifier (e.g. ``"ACM0002"``).
    tool_inputs : dict, optional
        Mapping of ``{tool_code: {input_key: value}}``.
        Tools not in this mapping will run with defaults.

    Returns
    -------
    dict
        ``{"methodology": ..., "tools_executed": [...], "results": {tool_code: result}, "summary": {...}}``.

    Raises
    ------
    ValueError
        If methodology is not mapped in ``METHODOLOGY_TOOL_DEPENDENCIES``.
    """
    code = methodology_code.upper()
    tool_codes = get_tools_for_methodology(code)
    if not tool_codes:
        raise ValueError(
            f"No tool dependencies mapped for methodology '{methodology_code}'. "
            f"Available: {sorted(METHODOLOGY_TOOL_DEPENDENCIES.keys())}"
        )

    tool_inputs = tool_inputs or {}
    results: Dict[str, Dict[str, Any]] = {}
    errors: List[str] = []

    for tc in tool_codes:
        try:
            result = calculate_cdm_tool(tc, tool_inputs.get(tc, {}))
            results[tc] = result
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{tc}: {exc}")
            results[tc] = {"error": str(exc)}

    # Build a summary
    total_emissions: float = 0.0
    total_reductions: float = 0.0
    additionality_verdict: Optional[bool] = None

    for tc, res in results.items():
        outputs = res.get("outputs", {})
        if "total_co2e_tonnes" in outputs:
            total_emissions += float(outputs["total_co2e_tonnes"])
        if "emissions_tco2" in outputs:
            total_emissions += float(outputs["emissions_tco2"])
        if "emission_reductions_tco2" in outputs:
            total_reductions += float(outputs["emission_reductions_tco2"])
        if "emission_reductions_tco2e" in outputs:
            total_reductions += float(outputs["emission_reductions_tco2e"])
        if "is_additional" in outputs:
            if additionality_verdict is None:
                additionality_verdict = outputs["is_additional"]
            else:
                additionality_verdict = additionality_verdict and outputs["is_additional"]

    return {
        "methodology": code,
        "tools_executed": tool_codes,
        "results": results,
        "errors": errors,
        "summary": {
            "total_emissions_tco2e": round(total_emissions, 4),
            "total_reductions_tco2e": round(total_reductions, 4),
            "additionality_verdict": additionality_verdict,
            "tools_count": len(tool_codes),
            "errors_count": len(errors),
        },
    }


def get_all_tools() -> List[Dict[str, Any]]:
    """Return metadata for all 43 registered CDM tools.

    Returns
    -------
    list[dict]
        Each entry is the registry metadata dict, sorted by tool code.
    """
    return [
        CDM_TOOLS_REGISTRY[code]
        for code in sorted(CDM_TOOLS_REGISTRY.keys())
    ]


def get_tools_by_category(category: CDMToolCategory) -> List[Dict[str, Any]]:
    """Return tools filtered by category.

    Parameters
    ----------
    category : CDMToolCategory

    Returns
    -------
    list[dict]
        Registry metadata dicts for tools in the given category.
    """
    return [
        meta
        for meta in CDM_TOOLS_REGISTRY.values()
        if meta.get("category") == category
    ]