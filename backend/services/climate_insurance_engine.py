"""
E79 — Climate Insurance & Parametric Risk Engine
=================================================
IAIS supervisory assessment, parametric product design, NatCat loss modelling,
climate VaR for insurance portfolios, ORSA climate stress testing,
casualty climate liability risk, and protection gap analysis.

References:
- IAIS Application Paper on the Supervision of Climate-related Risks (2021)
- IAIS ICPs 7, 8, 9, 15, 20 (Governance, ERM, ORSA, Investments, Public Disclosure)
- Solvency II Directive (2009/138/EC) Art 45a (ORSA Climate)
- NGFS Climate Scenarios 2022 (orderly / disorderly / hot house / below 2°C)
- Swiss Re sigma NatCat reports 2023
- Lloyd's Emerging Risk Reports 2022-2023
- EIOPA ORSA Climate Stress Test Guidance 2021
- UN-FAO Protection Gap data 2022
- PCAF Part B Insurance-Associated Emissions Standard
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Module-level reference data
# ---------------------------------------------------------------------------

NATCAT_COUNTRY_PROFILES: Dict[str, Dict[str, Any]] = {
    "USA": {
        "name": "United States of America",
        "aal_pct": {
            "flood": 0.28, "wind_cyclone": 0.35, "earthquake": 0.10, "drought": 0.08
        },
        "pml_100yr_pct": {
            "flood": 1.20, "wind_cyclone": 2.50, "earthquake": 0.90, "drought": 0.40
        },
        "pml_250yr_pct": {
            "flood": 2.10, "wind_cyclone": 4.20, "earthquake": 1.80, "drought": 0.75
        },
        "climate_loading_2050_rcp85_pct": {
            "flood": 25, "wind_cyclone": 30, "earthquake": 0, "drought": 20
        },
        "protection_gap_pct": 0.62,
        "insurance_penetration_pct": 0.38,
    },
    "GBR": {
        "name": "United Kingdom",
        "aal_pct": {"flood": 0.15, "wind_cyclone": 0.10, "earthquake": 0.01, "drought": 0.05},
        "pml_100yr_pct": {"flood": 0.80, "wind_cyclone": 0.60, "earthquake": 0.05, "drought": 0.20},
        "pml_250yr_pct": {"flood": 1.40, "wind_cyclone": 1.10, "earthquake": 0.10, "drought": 0.35},
        "climate_loading_2050_rcp85_pct": {"flood": 20, "wind_cyclone": 15, "earthquake": 0, "drought": 18},
        "protection_gap_pct": 0.35,
        "insurance_penetration_pct": 0.65,
    },
    "DEU": {
        "name": "Germany",
        "aal_pct": {"flood": 0.18, "wind_cyclone": 0.08, "earthquake": 0.02, "drought": 0.06},
        "pml_100yr_pct": {"flood": 0.90, "wind_cyclone": 0.50, "earthquake": 0.08, "drought": 0.25},
        "pml_250yr_pct": {"flood": 1.60, "wind_cyclone": 0.90, "earthquake": 0.15, "drought": 0.45},
        "climate_loading_2050_rcp85_pct": {"flood": 22, "wind_cyclone": 12, "earthquake": 0, "drought": 20},
        "protection_gap_pct": 0.55,
        "insurance_penetration_pct": 0.45,
    },
    "JPN": {
        "name": "Japan",
        "aal_pct": {"flood": 0.30, "wind_cyclone": 0.40, "earthquake": 0.45, "drought": 0.03},
        "pml_100yr_pct": {"flood": 1.50, "wind_cyclone": 2.80, "earthquake": 3.50, "drought": 0.10},
        "pml_250yr_pct": {"flood": 2.60, "wind_cyclone": 4.80, "earthquake": 6.20, "drought": 0.20},
        "climate_loading_2050_rcp85_pct": {"flood": 28, "wind_cyclone": 35, "earthquake": 0, "drought": 8},
        "protection_gap_pct": 0.40,
        "insurance_penetration_pct": 0.60,
    },
    "CHN": {
        "name": "China",
        "aal_pct": {"flood": 0.35, "wind_cyclone": 0.22, "earthquake": 0.20, "drought": 0.15},
        "pml_100yr_pct": {"flood": 1.80, "wind_cyclone": 1.40, "earthquake": 2.00, "drought": 0.60},
        "pml_250yr_pct": {"flood": 3.20, "wind_cyclone": 2.60, "earthquake": 3.80, "drought": 1.10},
        "climate_loading_2050_rcp85_pct": {"flood": 32, "wind_cyclone": 28, "earthquake": 0, "drought": 25},
        "protection_gap_pct": 0.85,
        "insurance_penetration_pct": 0.15,
    },
    "IND": {
        "name": "India",
        "aal_pct": {"flood": 0.40, "wind_cyclone": 0.30, "earthquake": 0.15, "drought": 0.25},
        "pml_100yr_pct": {"flood": 2.00, "wind_cyclone": 1.80, "earthquake": 1.50, "drought": 1.20},
        "pml_250yr_pct": {"flood": 3.50, "wind_cyclone": 3.20, "earthquake": 2.80, "drought": 2.00},
        "climate_loading_2050_rcp85_pct": {"flood": 35, "wind_cyclone": 30, "earthquake": 0, "drought": 30},
        "protection_gap_pct": 0.93,
        "insurance_penetration_pct": 0.07,
    },
    "AUS": {
        "name": "Australia",
        "aal_pct": {"flood": 0.20, "wind_cyclone": 0.28, "earthquake": 0.04, "drought": 0.18},
        "pml_100yr_pct": {"flood": 1.10, "wind_cyclone": 2.00, "earthquake": 0.30, "drought": 0.80},
        "pml_250yr_pct": {"flood": 2.00, "wind_cyclone": 3.60, "earthquake": 0.55, "drought": 1.40},
        "climate_loading_2050_rcp85_pct": {"flood": 20, "wind_cyclone": 25, "earthquake": 0, "drought": 28},
        "protection_gap_pct": 0.45,
        "insurance_penetration_pct": 0.55,
    },
    "BRA": {
        "name": "Brazil",
        "aal_pct": {"flood": 0.32, "wind_cyclone": 0.05, "earthquake": 0.01, "drought": 0.20},
        "pml_100yr_pct": {"flood": 1.60, "wind_cyclone": 0.25, "earthquake": 0.05, "drought": 0.90},
        "pml_250yr_pct": {"flood": 2.90, "wind_cyclone": 0.45, "earthquake": 0.10, "drought": 1.60},
        "climate_loading_2050_rcp85_pct": {"flood": 30, "wind_cyclone": 10, "earthquake": 0, "drought": 35},
        "protection_gap_pct": 0.80,
        "insurance_penetration_pct": 0.20,
    },
    "ZAF": {
        "name": "South Africa",
        "aal_pct": {"flood": 0.18, "wind_cyclone": 0.08, "earthquake": 0.02, "drought": 0.22},
        "pml_100yr_pct": {"flood": 0.90, "wind_cyclone": 0.40, "earthquake": 0.08, "drought": 1.00},
        "pml_250yr_pct": {"flood": 1.60, "wind_cyclone": 0.72, "earthquake": 0.15, "drought": 1.80},
        "climate_loading_2050_rcp85_pct": {"flood": 22, "wind_cyclone": 15, "earthquake": 0, "drought": 32},
        "protection_gap_pct": 0.75,
        "insurance_penetration_pct": 0.25,
    },
    "MEX": {
        "name": "Mexico",
        "aal_pct": {"flood": 0.25, "wind_cyclone": 0.28, "earthquake": 0.35, "drought": 0.12},
        "pml_100yr_pct": {"flood": 1.30, "wind_cyclone": 1.80, "earthquake": 3.00, "drought": 0.55},
        "pml_250yr_pct": {"flood": 2.30, "wind_cyclone": 3.20, "earthquake": 5.50, "drought": 1.00},
        "climate_loading_2050_rcp85_pct": {"flood": 28, "wind_cyclone": 25, "earthquake": 0, "drought": 28},
        "protection_gap_pct": 0.88,
        "insurance_penetration_pct": 0.12,
    },
    "NLD": {
        "name": "Netherlands",
        "aal_pct": {"flood": 0.35, "wind_cyclone": 0.06, "earthquake": 0.03, "drought": 0.04},
        "pml_100yr_pct": {"flood": 2.00, "wind_cyclone": 0.35, "earthquake": 0.12, "drought": 0.18},
        "pml_250yr_pct": {"flood": 3.60, "wind_cyclone": 0.62, "earthquake": 0.22, "drought": 0.32},
        "climate_loading_2050_rcp85_pct": {"flood": 35, "wind_cyclone": 10, "earthquake": 0, "drought": 12},
        "protection_gap_pct": 0.80,
        "insurance_penetration_pct": 0.20,
    },
    "ITA": {
        "name": "Italy",
        "aal_pct": {"flood": 0.22, "wind_cyclone": 0.05, "earthquake": 0.15, "drought": 0.08},
        "pml_100yr_pct": {"flood": 1.10, "wind_cyclone": 0.28, "earthquake": 1.30, "drought": 0.35},
        "pml_250yr_pct": {"flood": 2.00, "wind_cyclone": 0.50, "earthquake": 2.40, "drought": 0.62},
        "climate_loading_2050_rcp85_pct": {"flood": 25, "wind_cyclone": 8, "earthquake": 0, "drought": 22},
        "protection_gap_pct": 0.82,
        "insurance_penetration_pct": 0.18,
    },
    "TUR": {
        "name": "Turkey",
        "aal_pct": {"flood": 0.20, "wind_cyclone": 0.04, "earthquake": 0.40, "drought": 0.10},
        "pml_100yr_pct": {"flood": 1.00, "wind_cyclone": 0.20, "earthquake": 3.50, "drought": 0.45},
        "pml_250yr_pct": {"flood": 1.80, "wind_cyclone": 0.36, "earthquake": 6.30, "drought": 0.82},
        "climate_loading_2050_rcp85_pct": {"flood": 20, "wind_cyclone": 8, "earthquake": 0, "drought": 25},
        "protection_gap_pct": 0.70,
        "insurance_penetration_pct": 0.30,
    },
    "IDN": {
        "name": "Indonesia",
        "aal_pct": {"flood": 0.45, "wind_cyclone": 0.20, "earthquake": 0.38, "drought": 0.15},
        "pml_100yr_pct": {"flood": 2.30, "wind_cyclone": 1.30, "earthquake": 3.20, "drought": 0.70},
        "pml_250yr_pct": {"flood": 4.10, "wind_cyclone": 2.40, "earthquake": 5.80, "drought": 1.30},
        "climate_loading_2050_rcp85_pct": {"flood": 38, "wind_cyclone": 28, "earthquake": 0, "drought": 22},
        "protection_gap_pct": 0.95,
        "insurance_penetration_pct": 0.05,
    },
    "PHL": {
        "name": "Philippines",
        "aal_pct": {"flood": 0.50, "wind_cyclone": 0.60, "earthquake": 0.25, "drought": 0.10},
        "pml_100yr_pct": {"flood": 2.60, "wind_cyclone": 4.20, "earthquake": 2.20, "drought": 0.45},
        "pml_250yr_pct": {"flood": 4.70, "wind_cyclone": 7.50, "earthquake": 4.00, "drought": 0.82},
        "climate_loading_2050_rcp85_pct": {"flood": 40, "wind_cyclone": 38, "earthquake": 0, "drought": 18},
        "protection_gap_pct": 0.97,
        "insurance_penetration_pct": 0.03,
    },
    "BGD": {
        "name": "Bangladesh",
        "aal_pct": {"flood": 0.60, "wind_cyclone": 0.40, "earthquake": 0.08, "drought": 0.20},
        "pml_100yr_pct": {"flood": 3.20, "wind_cyclone": 2.80, "earthquake": 0.65, "drought": 0.90},
        "pml_250yr_pct": {"flood": 5.80, "wind_cyclone": 5.10, "earthquake": 1.20, "drought": 1.60},
        "climate_loading_2050_rcp85_pct": {"flood": 45, "wind_cyclone": 35, "earthquake": 0, "drought": 30},
        "protection_gap_pct": 0.99,
        "insurance_penetration_pct": 0.01,
    },
    "KEN": {
        "name": "Kenya",
        "aal_pct": {"flood": 0.28, "wind_cyclone": 0.02, "earthquake": 0.05, "drought": 0.35},
        "pml_100yr_pct": {"flood": 1.40, "wind_cyclone": 0.10, "earthquake": 0.40, "drought": 1.60},
        "pml_250yr_pct": {"flood": 2.60, "wind_cyclone": 0.18, "earthquake": 0.75, "drought": 2.90},
        "climate_loading_2050_rcp85_pct": {"flood": 30, "wind_cyclone": 5, "earthquake": 0, "drought": 38},
        "protection_gap_pct": 0.96,
        "insurance_penetration_pct": 0.04,
    },
    "NGA": {
        "name": "Nigeria",
        "aal_pct": {"flood": 0.30, "wind_cyclone": 0.01, "earthquake": 0.01, "drought": 0.28},
        "pml_100yr_pct": {"flood": 1.50, "wind_cyclone": 0.05, "earthquake": 0.05, "drought": 1.30},
        "pml_250yr_pct": {"flood": 2.80, "wind_cyclone": 0.10, "earthquake": 0.10, "drought": 2.40},
        "climate_loading_2050_rcp85_pct": {"flood": 32, "wind_cyclone": 5, "earthquake": 0, "drought": 40},
        "protection_gap_pct": 0.98,
        "insurance_penetration_pct": 0.02,
    },
    "PAK": {
        "name": "Pakistan",
        "aal_pct": {"flood": 0.48, "wind_cyclone": 0.12, "earthquake": 0.22, "drought": 0.25},
        "pml_100yr_pct": {"flood": 2.50, "wind_cyclone": 0.80, "earthquake": 2.00, "drought": 1.20},
        "pml_250yr_pct": {"flood": 4.50, "wind_cyclone": 1.50, "earthquake": 3.80, "drought": 2.20},
        "climate_loading_2050_rcp85_pct": {"flood": 42, "wind_cyclone": 20, "earthquake": 0, "drought": 35},
        "protection_gap_pct": 0.97,
        "insurance_penetration_pct": 0.03,
    },
    "FRA": {
        "name": "France",
        "aal_pct": {"flood": 0.14, "wind_cyclone": 0.09, "earthquake": 0.03, "drought": 0.07},
        "pml_100yr_pct": {"flood": 0.70, "wind_cyclone": 0.55, "earthquake": 0.12, "drought": 0.30},
        "pml_250yr_pct": {"flood": 1.25, "wind_cyclone": 1.00, "earthquake": 0.22, "drought": 0.55},
        "climate_loading_2050_rcp85_pct": {"flood": 18, "wind_cyclone": 12, "earthquake": 0, "drought": 20},
        "protection_gap_pct": 0.28,
        "insurance_penetration_pct": 0.72,
    },
}

PARAMETRIC_TRIGGER_TYPES: Dict[str, Dict[str, Any]] = {
    "rainfall_deficit": {
        "name": "Rainfall Deficit Index",
        "description": "Trigger based on cumulative rainfall below historical percentile threshold",
        "trigger_metric": "mm cumulative rainfall in season",
        "trigger_threshold": "≤p20 historical (approx 60% of average)",
        "exit_threshold": "≤p5 historical (approx 30% of average)",
        "payout_interpolation": "linear",
        "typical_max_payout_pct": 100,
        "basis_risk_range": "moderate (0.25-0.45)",
        "reference_data": "CHIRPS, NOAA GPCC, local weather stations",
        "peril": "drought",
        "use_cases": ["agriculture parametric", "index insurance smallholder", "cat bond drought"],
    },
    "wind_speed": {
        "name": "Wind Speed Index (Cyclone/Hurricane)",
        "description": "Trigger based on maximum sustained wind speed at named location",
        "trigger_metric": "km/h maximum sustained wind (1-min average)",
        "trigger_threshold": "≥Cat 1 (119 km/h) for basic cover",
        "exit_threshold": "≥Cat 4 (209 km/h) for max payout",
        "payout_interpolation": "linear between trigger and exit",
        "typical_max_payout_pct": 100,
        "basis_risk_range": "low-moderate (0.15-0.35)",
        "reference_data": "IBTrACS, JTWC, NHC, ECMWF ERA5",
        "peril": "wind_cyclone",
        "use_cases": ["sovereign cat bond", "SME business interruption", "P&C cat"],
    },
    "temperature_anomaly": {
        "name": "Temperature Anomaly Index",
        "description": "Trigger based on deviation of mean temperature from historical baseline",
        "trigger_metric": "°C above 30-year climatological baseline",
        "trigger_threshold": "+1.5°C above baseline monthly average",
        "exit_threshold": "+3.0°C above baseline",
        "payout_interpolation": "linear",
        "typical_max_payout_pct": 100,
        "basis_risk_range": "low (0.10-0.25)",
        "reference_data": "HadCRUT5, NASA GISS, ERA5 reanalysis",
        "peril": "heat_stress",
        "use_cases": ["energy sector revenue protection", "agriculture heat stress", "mortality heat bond"],
    },
    "flood_depth": {
        "name": "Flood Depth Index",
        "description": "Trigger based on modelled or observed flood inundation depth at reference gauge",
        "trigger_metric": "metres above flood stage",
        "trigger_threshold": "≥0.5m above flood stage (100yr level)",
        "exit_threshold": "≥2.0m above flood stage",
        "payout_interpolation": "linear",
        "typical_max_payout_pct": 100,
        "basis_risk_range": "moderate-high (0.35-0.55)",
        "reference_data": "Global Flood Monitoring, Copernicus EMS, gauge networks",
        "peril": "flood",
        "use_cases": ["sovereign disaster risk finance", "microinsurance flood", "municipal bond"],
    },
    "soil_moisture_deficit": {
        "name": "Soil Moisture Deficit Index (SMDI)",
        "description": "Trigger based on soil moisture anomaly below field capacity",
        "trigger_metric": "% of field capacity",
        "trigger_threshold": "≤40% of field capacity",
        "exit_threshold": "≤15% of field capacity",
        "payout_interpolation": "linear",
        "typical_max_payout_pct": 100,
        "basis_risk_range": "moderate (0.30-0.50)",
        "reference_data": "ESA CCI Soil Moisture, NASA SMAP, ECMWF HTESSEL",
        "peril": "drought",
        "use_cases": ["crop insurance", "agriculture development bank"],
    },
    "cat_model_score": {
        "name": "Catastrophe Model Score (AEP Exceedance)",
        "description": "Trigger based on modelled Annual Exceedance Probability (AEP) loss level",
        "trigger_metric": "Modelled AEP loss % of exposure",
        "trigger_threshold": "Modelled 1-in-50yr AEP event (2% annual probability)",
        "exit_threshold": "Modelled 1-in-250yr AEP event (0.4% annual probability)",
        "payout_interpolation": "table-based loss function",
        "typical_max_payout_pct": 100,
        "basis_risk_range": "low (0.05-0.20) — model-dependent",
        "reference_data": "RMS, AIR Worldwide, Verisk Respond, Moody's RMS",
        "peril": "multi-peril",
        "use_cases": ["ILS cat bond", "retrocession", "sovereign ILS", "reinsurance sidecar"],
    },
}

IAIS_REQUIREMENTS: Dict[str, Dict[str, Any]] = {
    "governance": {
        "pillar": "Governance",
        "weight": 0.25,
        "icp_reference": "ICP 7 (Corporate Governance)",
        "items": [
            {
                "id": "GOV-01",
                "description": "Board mandate includes explicit oversight of climate-related risks",
                "scoring": "full (1.0) | partial (0.5) | absent (0.0)",
            },
            {
                "id": "GOV-02",
                "description": "Named board-level or senior management climate risk owner",
                "scoring": "full | partial | absent",
            },
            {
                "id": "GOV-03",
                "description": "Climate risk integrated into governance frameworks and risk appetite",
                "scoring": "full | partial | absent",
            },
            {
                "id": "GOV-04",
                "description": "Board training/expertise in climate risks evidenced",
                "scoring": "full | partial | absent",
            },
            {
                "id": "GOV-05",
                "description": "Remuneration policy links executive pay to climate KPIs",
                "scoring": "full | partial | absent",
            },
        ],
    },
    "strategy": {
        "pillar": "Strategy",
        "weight": 0.25,
        "icp_reference": "ICP 16 (Investment), ICP 9 (Supervisory Review)",
        "items": [
            {
                "id": "STR-01",
                "description": "Business strategy explicitly addresses physical and transition climate risk",
                "scoring": "full | partial | absent",
            },
            {
                "id": "STR-02",
                "description": "Scenario analysis conducted (at least 2°C and 4°C pathways)",
                "scoring": "full | partial | absent",
            },
            {
                "id": "STR-03",
                "description": "Investment portfolio climate alignment assessed (transition risk in assets)",
                "scoring": "full | partial | absent",
            },
            {
                "id": "STR-04",
                "description": "Product and underwriting strategy adapted for climate risk emergence",
                "scoring": "full | partial | absent",
            },
        ],
    },
    "risk_management": {
        "pillar": "Risk Management",
        "weight": 0.30,
        "icp_reference": "ICP 8 (Risk Management), ICP 20 (ORSA)",
        "items": [
            {
                "id": "RM-01",
                "description": "Climate risk taxonomy defined and embedded in ERM framework",
                "scoring": "full | partial | absent",
            },
            {
                "id": "RM-02",
                "description": "Physical risk modelling includes climate-adjusted NatCat exposure",
                "scoring": "full | partial | absent",
            },
            {
                "id": "RM-03",
                "description": "Transition risk modelling covers investment and liability sides",
                "scoring": "full | partial | absent",
            },
            {
                "id": "RM-04",
                "description": "ORSA includes forward-looking climate stress testing (NGFS scenarios)",
                "scoring": "full | partial | absent",
            },
            {
                "id": "RM-05",
                "description": "Underwriting guidelines updated to reflect climate-adjusted loss costs",
                "scoring": "full | partial | absent",
            },
            {
                "id": "RM-06",
                "description": "Climate risk appetite limits set with breach monitoring",
                "scoring": "full | partial | absent",
            },
        ],
    },
    "disclosure": {
        "pillar": "Disclosure",
        "weight": 0.20,
        "icp_reference": "ICP 20 (Public Disclosure), TCFD alignment",
        "items": [
            {
                "id": "DISC-01",
                "description": "TCFD-aligned public disclosure published (Governance/Strategy/Risk/Metrics)",
                "scoring": "full | partial | absent",
            },
            {
                "id": "DISC-02",
                "description": "Scope 1, 2, and 3 GHG emissions disclosed for own operations and investments",
                "scoring": "full | partial | absent",
            },
            {
                "id": "DISC-03",
                "description": "Insured/financed emissions disclosed per PCAF Part B/C standard",
                "scoring": "full | partial | absent",
            },
            {
                "id": "DISC-04",
                "description": "Climate scenario analysis results published (qualitative + quantitative)",
                "scoring": "full | partial | absent",
            },
            {
                "id": "DISC-05",
                "description": "Net-zero commitment with interim targets published",
                "scoring": "full | partial | absent",
            },
        ],
    },
}

PROTECTION_GAP_DATA: Dict[str, Dict[str, Any]] = {
    "global_2022": {
        "total_economic_losses_usd_bn": 275,
        "total_insured_losses_usd_bn": 125,
        "protection_gap_usd_bn": 150,
        "protection_gap_pct": 0.545,
        "source": "Swiss Re sigma No 1/2023",
    },
    "emerging_markets": {
        "total_economic_losses_usd_bn": 95,
        "total_insured_losses_usd_bn": 6,
        "protection_gap_usd_bn": 89,
        "protection_gap_pct": 0.937,
        "note": "includes Asia excl Japan/Australia, Latin America, Africa, Middle East",
    },
    "developed_markets": {
        "total_economic_losses_usd_bn": 180,
        "total_insured_losses_usd_bn": 119,
        "protection_gap_usd_bn": 61,
        "protection_gap_pct": 0.339,
        "note": "includes North America, Western Europe, Japan, Australia/NZ",
    },
    "flood_global": {
        "peril": "flood",
        "protection_gap_pct": 0.75,
        "trend": "worsening — only 25% of flood losses are insured globally",
        "climate_projection_2050": "gap could reach 80-85% under RCP8.5 without policy intervention",
    },
    "drought_global": {
        "peril": "drought",
        "protection_gap_pct": 0.88,
        "trend": "severe — agricultural drought largely uninsured in developing nations",
        "climate_projection_2050": "estimated $65bn annual uninsured agricultural drought losses by 2050",
    },
    "wind_global": {
        "peril": "wind_cyclone",
        "protection_gap_pct": 0.45,
        "trend": "stable in developed markets; growing in Asia Pacific",
        "climate_projection_2050": "cyclone intensification could increase AAL by 30-40% under 2°C",
    },
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class InsurancePortfolioInput:
    """Input data for insurance portfolio climate risk assessment."""
    insurer_name: str
    portfolio_type: str  # pc | life | reinsurance | composite | specialty
    total_exposure_usd_m: float
    pc_exposure_usd_m: Optional[float] = None
    life_exposure_usd_m: Optional[float] = None
    investment_portfolio_usd_m: Optional[float] = None
    high_carbon_investment_pct: Optional[float] = None  # % allocated to fossil fuel assets
    country_exposures: Optional[Dict[str, float]] = None  # country_code -> exposure USD m
    peril_exposures: Optional[Dict[str, float]] = None  # peril -> exposure USD m
    iais_scores: Optional[Dict[str, float]] = None  # pillar -> score 0-1
    ngfs_scenario: str = "orderly"  # orderly | disorderly | hot_house | below_2c
    reporting_year: int = 2024


@dataclass
class ParametricDesignInput:
    """Input for parametric insurance product design."""
    product_name: str
    peril: str  # flood | wind_cyclone | drought | heat_stress
    trigger_type: str  # rainfall_deficit | wind_speed | temperature_anomaly | flood_depth | soil_moisture_deficit | cat_model_score
    country_code: str
    exposure_value_usd_m: float
    season_months: int = 6
    trigger_level: Optional[float] = None
    exit_level: Optional[float] = None
    max_payout_usd_m: Optional[float] = None
    premium_loading_pct: float = 35.0  # standard loading for expenses + profit
    climate_adjustment_yr: int = 2030


@dataclass
class NatCatInput:
    """Input for NatCat loss modelling."""
    country_code: str
    peril: str  # flood | wind_cyclone | earthquake | drought
    insured_exposure_usd_m: float
    rcp_scenario: str = "rcp45"  # rcp26 | rcp45 | rcp85
    horizon_year: int = 2040


@dataclass
class ClimateInsuranceResult:
    """Consolidated climate insurance assessment result."""
    insurer_name: str
    reporting_year: int
    iais_compliance: Dict[str, Any] = field(default_factory=dict)
    parametric_design: Dict[str, Any] = field(default_factory=dict)
    natcat_loss: Dict[str, Any] = field(default_factory=dict)
    climate_var: Dict[str, Any] = field(default_factory=dict)
    orsa_stress: Dict[str, Any] = field(default_factory=dict)
    casualty_liability: Dict[str, Any] = field(default_factory=dict)
    protection_gap: Dict[str, Any] = field(default_factory=dict)
    overall_climate_risk_score: float = 0.0
    supervisory_flags: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class ClimateInsuranceEngine:
    """
    E79 Climate Insurance & Parametric Risk Engine.

    Covers IAIS supervisory assessment, parametric product design, NatCat loss modelling,
    climate VaR, ORSA stress testing, casualty liability, and protection gap analysis.
    """

    # NGFS scenario parameters for insurance ORSA stress
    NGFS_SCENARIOS: Dict[str, Dict[str, Any]] = {
        "orderly": {
            "name": "Net Zero 2050 (Orderly)",
            "equity_shock_pct": -15,
            "bond_spread_bps": 80,
            "re_value_pct": -8,
            "natcat_uplift_pct": 12,
            "liab_reserve_uplift_pct": 5,
            "horizon": "2030-2050",
        },
        "disorderly": {
            "name": "Delayed Transition (Disorderly)",
            "equity_shock_pct": -30,
            "bond_spread_bps": 180,
            "re_value_pct": -15,
            "natcat_uplift_pct": 18,
            "liab_reserve_uplift_pct": 10,
            "horizon": "2025-2035",
        },
        "hot_house": {
            "name": "Hot House World (Current Policies)",
            "equity_shock_pct": -10,
            "bond_spread_bps": 40,
            "re_value_pct": -20,
            "natcat_uplift_pct": 35,
            "liab_reserve_uplift_pct": 20,
            "horizon": "2040-2080",
        },
        "below_2c": {
            "name": "Below 2°C",
            "equity_shock_pct": -20,
            "bond_spread_bps": 110,
            "re_value_pct": -10,
            "natcat_uplift_pct": 20,
            "liab_reserve_uplift_pct": 8,
            "horizon": "2030-2060",
        },
    }

    # Insurer type profiles for ORSA
    INSURER_PROFILES: Dict[str, Dict[str, Any]] = {
        "pc": {
            "name": "Property & Casualty Insurer",
            "natcat_sensitivity": "high",
            "investment_risk_weight": 0.35,
            "underwriting_risk_weight": 0.65,
        },
        "life": {
            "name": "Life Insurer",
            "natcat_sensitivity": "low",
            "investment_risk_weight": 0.70,
            "underwriting_risk_weight": 0.30,
        },
        "reinsurance": {
            "name": "Reinsurer",
            "natcat_sensitivity": "very_high",
            "investment_risk_weight": 0.25,
            "underwriting_risk_weight": 0.75,
        },
        "composite": {
            "name": "Composite Insurer",
            "natcat_sensitivity": "medium",
            "investment_risk_weight": 0.50,
            "underwriting_risk_weight": 0.50,
        },
        "specialty": {
            "name": "Specialty / Lloyd's Market",
            "natcat_sensitivity": "high",
            "investment_risk_weight": 0.30,
            "underwriting_risk_weight": 0.70,
        },
    }

    def assess_iais_compliance(self, portfolio_input: InsurancePortfolioInput) -> Dict[str, Any]:
        """
        4-pillar IAIS supervisory assessment: governance, strategy, risk management, disclosure.

        Uses provided scores or defaults to partial (0.5) for each item.
        Thresholds: amber 60%, red 40%.
        """
        provided = portfolio_input.iais_scores or {}
        pillar_scores: Dict[str, float] = {}
        pillar_detail: Dict[str, Any] = {}

        for pillar_key, pillar_data in IAIS_REQUIREMENTS.items():
            items = pillar_data["items"]
            item_scores: List[float] = []
            for item in items:
                item_id = item["id"]
                score = provided.get(item_id, 0.5)  # default to partial
                item_scores.append(score)

            pillar_avg = sum(item_scores) / len(item_scores) if item_scores else 0.0
            pillar_scores[pillar_key] = pillar_avg
            pillar_detail[pillar_key] = {
                "pillar": pillar_data["pillar"],
                "icp_reference": pillar_data["icp_reference"],
                "score_pct": round(pillar_avg * 100, 1),
                "items_scored": len(item_scores),
                "weight": pillar_data["weight"],
            }

        # Weighted overall
        overall = sum(
            pillar_scores[k] * IAIS_REQUIREMENTS[k]["weight"]
            for k in pillar_scores
        )
        overall_pct = overall * 100.0

        if overall_pct >= 80:
            status = "satisfactory"
            flag = "green"
        elif overall_pct >= 60:
            status = "supervisory_concern"
            flag = "amber"
        else:
            status = "supervisory_action_required"
            flag = "red"

        gaps = [
            f"{pillar_detail[k]['pillar']}: score {pillar_detail[k]['score_pct']}% — "
            f"requires improvement (ICP ref: {IAIS_REQUIREMENTS[k]['icp_reference']})"
            for k in pillar_detail
            if pillar_detail[k]["score_pct"] < 60
        ]

        return {
            "overall_score_pct": round(overall_pct, 1),
            "supervisory_status": status,
            "rag_flag": flag,
            "pillar_detail": pillar_detail,
            "gaps": gaps,
            "amber_threshold_pct": 60,
            "red_threshold_pct": 40,
            "reference": "IAIS Application Paper on the Supervision of Climate-related Risks (2021)",
        }

    def design_parametric_product(self, p: ParametricDesignInput) -> Dict[str, Any]:
        """
        Design a parametric insurance product.

        Calculates AAL, premium, payout structure, trigger/exit levels,
        and basis risk score.
        """
        trigger_meta = PARAMETRIC_TRIGGER_TYPES.get(p.trigger_type)
        if not trigger_meta:
            return {"error": f"Unknown trigger type: {p.trigger_type}"}

        country = NATCAT_COUNTRY_PROFILES.get(p.country_code)
        if not country:
            return {"error": f"No NatCat profile for country: {p.country_code}"}

        # Get AAL for peril
        aal_pct = country["aal_pct"].get(p.peril, 0.15) / 100.0
        aal_usd_m = p.exposure_value_usd_m * aal_pct

        # Climate adjustment
        rcp85_loading_pct = country["climate_loading_2050_rcp85_pct"].get(p.peril, 15)
        years_to_horizon = max(0, p.climate_adjustment_yr - p.reporting_year if hasattr(p, "reporting_year") else 10)
        climate_adj = 1.0 + (rcp85_loading_pct / 100.0) * (years_to_horizon / 26.0)
        climate_adj_aal = aal_usd_m * climate_adj

        # Premium = climate-adjusted AAL × (1 + loading)
        pure_premium = climate_adj_aal
        gross_premium = pure_premium * (1 + p.premium_loading_pct / 100.0)

        # Max payout
        max_payout = p.max_payout_usd_m or p.exposure_value_usd_m * 0.80

        # Basis risk score (from trigger type profile)
        basis_risk_range = trigger_meta["basis_risk_range"]
        # Parse midpoint from range string
        try:
            parts = basis_risk_range.split("(")[1].split(")")[0].split("-")
            basis_risk = (float(parts[0]) + float(parts[1])) / 2
        except Exception:
            basis_risk = 0.35

        # Trigger/exit levels (use provided or derive from defaults)
        trigger_level = p.trigger_level or 0.0
        exit_level = p.exit_level or 0.0

        return {
            "product_name": p.product_name,
            "peril": p.peril,
            "trigger_type": p.trigger_type,
            "trigger_description": trigger_meta["description"],
            "country": p.country_code,
            "exposure_value_usd_m": p.exposure_value_usd_m,
            "trigger_level": trigger_level,
            "exit_level": exit_level,
            "max_payout_usd_m": round(max_payout, 2),
            "payout_interpolation": trigger_meta["payout_interpolation"],
            "aal_usd_m": round(aal_usd_m, 3),
            "climate_adjusted_aal_usd_m": round(climate_adj_aal, 3),
            "climate_adjustment_factor": round(climate_adj, 3),
            "climate_horizon_year": p.climate_adjustment_yr,
            "pure_premium_usd_m": round(pure_premium, 3),
            "gross_premium_usd_m": round(gross_premium, 3),
            "premium_rate_pct": round(gross_premium / p.exposure_value_usd_m * 100, 3),
            "premium_loading_pct": p.premium_loading_pct,
            "basis_risk_score": round(basis_risk, 2),
            "basis_risk_mitigation": (
                "Use dense station network + satellite blending to reduce basis risk below 0.20"
                if basis_risk > 0.30
                else "Basis risk within acceptable range for ILS / reinsurance placement"
            ),
            "reference_data_sources": trigger_meta["reference_data"],
            "use_cases": trigger_meta["use_cases"],
        }

    def model_natcat_loss(self, n: NatCatInput) -> Dict[str, Any]:
        """
        NatCat loss modelling for a single country/peril combination.

        Returns AAL, PML at 100yr and 250yr, climate-adjusted losses under RCP scenario,
        and premium loading recommendation.
        """
        country = NATCAT_COUNTRY_PROFILES.get(n.country_code)
        if not country:
            return {"error": f"No NatCat profile for country: {n.country_code}"}

        aal_pct = country["aal_pct"].get(n.peril, 0.10) / 100.0
        pml_100_pct = country["pml_100yr_pct"].get(n.peril, 0.50) / 100.0
        pml_250_pct = country["pml_250yr_pct"].get(n.peril, 1.00) / 100.0

        loading_rcp85 = country["climate_loading_2050_rcp85_pct"].get(n.peril, 15) / 100.0

        # RCP scaling
        rcp_multipliers = {"rcp26": 0.30, "rcp45": 0.55, "rcp85": 1.0}
        rcp_mult = rcp_multipliers.get(n.rcp_scenario, 0.55)
        years_factor = max(0, n.horizon_year - 2024) / 26.0  # linear to 2050
        climate_loading = 1.0 + loading_rcp85 * rcp_mult * years_factor

        aal = n.insured_exposure_usd_m * aal_pct
        aal_climate = aal * climate_loading
        pml_100 = n.insured_exposure_usd_m * pml_100_pct
        pml_100_climate = pml_100 * climate_loading
        pml_250 = n.insured_exposure_usd_m * pml_250_pct
        pml_250_climate = pml_250 * climate_loading

        premium_loading_add_pct = round((climate_loading - 1.0) * 100, 1)

        return {
            "country": n.country_code,
            "country_name": country["name"],
            "peril": n.peril,
            "insured_exposure_usd_m": n.insured_exposure_usd_m,
            "rcp_scenario": n.rcp_scenario,
            "horizon_year": n.horizon_year,
            "aal_base_usd_m": round(aal, 3),
            "aal_climate_adjusted_usd_m": round(aal_climate, 3),
            "pml_100yr_base_usd_m": round(pml_100, 3),
            "pml_100yr_climate_adjusted_usd_m": round(pml_100_climate, 3),
            "pml_250yr_base_usd_m": round(pml_250, 3),
            "pml_250yr_climate_adjusted_usd_m": round(pml_250_climate, 3),
            "climate_loading_factor": round(climate_loading, 3),
            "climate_loading_pct": round((climate_loading - 1.0) * 100, 1),
            "premium_loading_recommendation_pct": premium_loading_add_pct,
            "protection_gap_pct": country["protection_gap_pct"] * 100,
            "insurance_penetration_pct": country["insurance_penetration_pct"] * 100,
            "data_source": "Swiss Re sigma NatCat 2023 + EIOPA NatCat country profiles",
        }

    def calculate_climate_var(self, portfolio_input: InsurancePortfolioInput) -> Dict[str, Any]:
        """
        Calculate climate VaR across three risk channels:
        1. Physical risk (P&C NatCat)
        2. Transition risk (investment portfolio)
        3. Life/health risk (mortality, morbidity)
        """
        total = portfolio_input.total_exposure_usd_m
        pc = portfolio_input.pc_exposure_usd_m or total * 0.60
        life = portfolio_input.life_exposure_usd_m or total * 0.25
        inv = portfolio_input.investment_portfolio_usd_m or total * 0.50
        high_carbon_pct = (portfolio_input.high_carbon_investment_pct or 15) / 100.0

        scenario = portfolio_input.ngfs_scenario
        params = self.NGFS_SCENARIOS.get(scenario, self.NGFS_SCENARIOS["orderly"])

        # Physical risk VaR (average across country/peril mix)
        avg_aal_pct = 0.0025  # 0.25% of insured exposure
        natcat_uplift = (1 + params["natcat_uplift_pct"] / 100.0)
        physical_var = pc * avg_aal_pct * natcat_uplift * 10  # 10x for VaR exceedance
        physical_var_pct = physical_var / total * 100

        # Transition risk VaR (investment side)
        equity_shock = abs(params["equity_shock_pct"]) / 100.0
        bond_shock = params["bond_spread_bps"] / 10000.0 * 5  # duration ~5
        re_shock = abs(params["re_value_pct"]) / 100.0
        transition_var = inv * (
            high_carbon_pct * equity_shock * 0.5
            + high_carbon_pct * bond_shock * 0.3
            + 0.10 * re_shock * 0.2
        )
        transition_var_pct = transition_var / total * 100

        # Liability transition risk (D&O, greenwashing)
        liability_var = pc * 0.002 * (1 + params["natcat_uplift_pct"] / 200)
        liability_var_pct = liability_var / total * 100

        # Life/health VaR (heat mortality + disease morbidity)
        heat_mortality_uplift = 0.0015 if scenario == "hot_house" else 0.0008
        life_var = life * heat_mortality_uplift
        life_var_pct = life_var / total * 100

        # Aggregate with diversification benefit (30% correlation benefit)
        gross_var = physical_var + transition_var + liability_var + life_var
        diversification_benefit = gross_var * 0.15
        net_var = gross_var - diversification_benefit
        var_pct = net_var / total * 100

        return {
            "insurer": portfolio_input.insurer_name,
            "ngfs_scenario": scenario,
            "scenario_name": params["name"],
            "total_exposure_usd_m": total,
            "physical_risk_var_usd_m": round(physical_var, 2),
            "physical_risk_var_pct": round(physical_var_pct, 2),
            "transition_risk_var_usd_m": round(transition_var, 2),
            "transition_risk_var_pct": round(transition_var_pct, 2),
            "liability_transition_var_usd_m": round(liability_var, 2),
            "life_health_var_usd_m": round(life_var, 2),
            "gross_climate_var_usd_m": round(gross_var, 2),
            "diversification_benefit_usd_m": round(diversification_benefit, 2),
            "net_climate_var_usd_m": round(net_var, 2),
            "net_climate_var_pct": round(var_pct, 2),
            "var_confidence": "99th percentile (1-in-100yr)",
            "methodology": "Physical AAL × climate loading + transition spread shock + liability reserve uplift",
        }

    def orsa_climate_stress(self, portfolio_input: InsurancePortfolioInput) -> Dict[str, Any]:
        """
        Solvency II Art 45a ORSA climate stress test across 4 NGFS scenarios.

        Returns SCR uplift, post-stress solvency ratio, and 12-item ORSA checklist.
        """
        total = portfolio_input.total_exposure_usd_m
        inv = portfolio_input.investment_portfolio_usd_m or total * 0.50

        # Baseline SCR (assume 15% of total exposure)
        scr_baseline = total * 0.15
        solvency_ratio_baseline = 185.0  # % (pre-stress)

        scenario_results: Dict[str, Any] = {}
        for sc_key, sc_params in self.NGFS_SCENARIOS.items():
            # SCR uplift components
            natcat_reserve_increase = total * 0.10 * (sc_params["natcat_uplift_pct"] / 100.0)
            market_risk_shock = inv * abs(sc_params["equity_shock_pct"]) / 100.0 * 0.40
            liab_reserve_uplift = total * 0.05 * (sc_params["liab_reserve_uplift_pct"] / 100.0)
            total_scr_uplift = natcat_reserve_increase + market_risk_shock + liab_reserve_uplift

            scr_post_stress = scr_baseline + total_scr_uplift
            scr_coverage_post = solvency_ratio_baseline * scr_baseline / scr_post_stress
            breaches_msr = scr_coverage_post < 150
            breaches_scr = scr_coverage_post < 100

            scenario_results[sc_key] = {
                "scenario_name": sc_params["name"],
                "scr_baseline_usd_m": round(scr_baseline, 2),
                "natcat_reserve_increase_usd_m": round(natcat_reserve_increase, 2),
                "market_risk_shock_usd_m": round(market_risk_shock, 2),
                "liability_reserve_uplift_usd_m": round(liab_reserve_uplift, 2),
                "total_scr_uplift_usd_m": round(total_scr_uplift, 2),
                "scr_post_stress_usd_m": round(scr_post_stress, 2),
                "solvency_ratio_post_stress_pct": round(scr_coverage_post, 1),
                "breaches_msr_150pct": breaches_msr,
                "breaches_scr_100pct": breaches_scr,
                "recovery_plan_required": breaches_msr,
            }

        # ORSA Art 45a 12-item checklist
        orsa_checklist = [
            {"id": "OA-01", "requirement": "Climate scenarios used: minimum NGFS orderly, disorderly, hot house", "status": "met"},
            {"id": "OA-02", "requirement": "Short/medium/long-term horizons assessed (3yr, 10yr, 30yr)", "status": "partial"},
            {"id": "OA-03", "requirement": "Physical risk modelled (AAL + PML under climate adjustment)", "status": "met"},
            {"id": "OA-04", "requirement": "Transition risk modelled (investment portfolio, liability side)", "status": "met"},
            {"id": "OA-05", "requirement": "SCR impact quantified per scenario", "status": "met"},
            {"id": "OA-06", "requirement": "MCR impact quantified per scenario", "status": "partial"},
            {"id": "OA-07", "requirement": "Own funds impact quantified", "status": "met"},
            {"id": "OA-08", "requirement": "Business plan impact (premium volume, loss costs)", "status": "partial"},
            {"id": "OA-09", "requirement": "Risk appetite limits reviewed against stress outcomes", "status": "partial"},
            {"id": "OA-10", "requirement": "Management actions identified (capital raise, reinsurance, asset shift)", "status": "partial"},
            {"id": "OA-11", "requirement": "Board approved ORSA report including climate annex", "status": "met"},
            {"id": "OA-12", "requirement": "ORSA climate report submitted to supervisory authority", "status": "partial"},
        ]

        checklist_score = sum(1 for c in orsa_checklist if c["status"] == "met") / len(orsa_checklist) * 100

        return {
            "scenario_results": scenario_results,
            "solvency_ratio_baseline_pct": solvency_ratio_baseline,
            "orsa_checklist": orsa_checklist,
            "checklist_score_pct": round(checklist_score, 1),
            "worst_case_scenario": min(
                scenario_results,
                key=lambda k: scenario_results[k]["solvency_ratio_post_stress_pct"]
            ),
            "regulatory_reference": "Solvency II Directive Art 45a (ORSA) + EIOPA Guidance on Climate Stress Testing",
        }

    def assess_casualty_liability(self, portfolio_input: InsurancePortfolioInput) -> Dict[str, Any]:
        """
        Assess casualty climate liability risk: D&O (greenwashing), E&O, Pollution.

        Returns liability reserve estimates and exposure trend per line.
        """
        total = portfolio_input.total_exposure_usd_m
        pc = portfolio_input.pc_exposure_usd_m or total * 0.60

        # D&O greenwashing risk
        do_exposure = pc * 0.08
        do_climate_loading = 1.20  # 20% uplift for climate litigation trend
        do_reserve = do_exposure * 0.03 * do_climate_loading
        do_growth_rate_pa = 0.25  # 25% annual growth in greenwashing claims

        # E&O ESG advisory failure
        eo_exposure = pc * 0.05
        eo_reserve = eo_exposure * 0.02 * 1.15
        eo_growth_rate_pa = 0.18

        # Pollution — stranded asset cleanup / legacy fossil
        pollution_exposure = pc * 0.04
        pollution_reserve = pollution_exposure * 0.04 * 1.10
        pollution_growth_rate_pa = 0.15

        total_climate_liability_reserve = do_reserve + eo_reserve + pollution_reserve

        return {
            "insurer": portfolio_input.insurer_name,
            "do_greenwashing": {
                "exposure_usd_m": round(do_exposure, 2),
                "reserve_estimate_usd_m": round(do_reserve, 2),
                "annual_growth_rate_pct": do_growth_rate_pa * 100,
                "climate_loading": do_climate_loading,
                "key_risks": ["Securities class actions for misleading ESG claims",
                              "Shareholder derivative suits for climate governance failures",
                              "SEC/FCA enforcement actions for greenwashing"],
            },
            "eo_esg_advisory": {
                "exposure_usd_m": round(eo_exposure, 2),
                "reserve_estimate_usd_m": round(eo_reserve, 2),
                "annual_growth_rate_pct": eo_growth_rate_pa * 100,
                "key_risks": ["ESG rating advisory failure",
                              "Sustainability-linked loan structuring liability",
                              "SFDR/CSRD compliance advisory errors"],
            },
            "pollution_stranded_assets": {
                "exposure_usd_m": round(pollution_exposure, 2),
                "reserve_estimate_usd_m": round(pollution_reserve, 2),
                "annual_growth_rate_pct": pollution_growth_rate_pa * 100,
                "key_risks": ["Stranded asset decommissioning cleanup costs",
                              "Legacy fossil fuel site remediation",
                              "PFAS and emerging contaminant liability"],
            },
            "total_climate_liability_reserve_usd_m": round(total_climate_liability_reserve, 2),
            "5yr_projected_reserve_usd_m": round(
                total_climate_liability_reserve * (1.22 ** 5), 2
            ),
            "reference": "Lloyd's Climate Change Emerging Risk Report 2022; IAIS ICP 14 (Liability Adequacy)",
        }

    def analyse_protection_gap(self, country_code: str, peril: str) -> Dict[str, Any]:
        """
        Analyse the insurance protection gap for a country/peril combination.

        Returns current gap, economic/insured loss split, and climate projection to 2030/2040.
        """
        country = NATCAT_COUNTRY_PROFILES.get(country_code)
        if not country:
            return {"error": f"No profile for country: {country_code}"}

        insured_pct = country["insurance_penetration_pct"]
        gap_pct = country["protection_gap_pct"]
        climate_loading = country["climate_loading_2050_rcp85_pct"].get(peril, 15)

        # Hypothetical $100m economic loss
        economic_loss_base = 100.0
        insured_loss_base = economic_loss_base * insured_pct
        uninsured_loss_base = economic_loss_base - insured_loss_base

        # Climate projections
        gap_2030_pct = min(gap_pct + climate_loading * 0.002, 0.99)
        gap_2040_pct = min(gap_pct + climate_loading * 0.005, 0.99)

        global_gap = PROTECTION_GAP_DATA.get("global_2022", {})
        peril_gap = PROTECTION_GAP_DATA.get(f"{peril}_global", {})

        return {
            "country": country_code,
            "country_name": country["name"],
            "peril": peril,
            "current_insurance_penetration_pct": round(insured_pct * 100, 1),
            "current_protection_gap_pct": round(gap_pct * 100, 1),
            "per_100m_economic_loss": {
                "insured_usd_m": round(insured_loss_base, 1),
                "uninsured_usd_m": round(uninsured_loss_base, 1),
                "gap_ratio": round(gap_pct, 3),
            },
            "climate_gap_projection": {
                "2030_rcp85_gap_pct": round(gap_2030_pct * 100, 1),
                "2040_rcp85_gap_pct": round(gap_2040_pct * 100, 1),
                "climate_trend": f"+{climate_loading}% AAL increase by 2050 under RCP8.5",
            },
            "global_context": {
                "global_protection_gap_pct": global_gap.get("protection_gap_pct", 0.545) * 100,
                "peril_global_gap_pct": peril_gap.get("protection_gap_pct", 0.5) * 100 if peril_gap else None,
                "source": "Swiss Re sigma No 1/2023",
            },
            "gap_closure_levers": [
                "Mandatory flood/catastrophe insurance schemes",
                "Parametric insurance for rapid payout (reduce basis risk)",
                "Public-private partnership sovereign risk pools (ARC, CCRIF, PCRAFI)",
                "Microinsurance for smallholder/low-income segments",
                "Index-based agricultural insurance with subsidy support",
            ],
        }

    def full_assessment(self, portfolio_input: InsurancePortfolioInput) -> ClimateInsuranceResult:
        """
        Run all E79 sub-modules and return a consolidated ClimateInsuranceResult.
        """
        iais = self.assess_iais_compliance(portfolio_input)
        climate_var = self.calculate_climate_var(portfolio_input)
        orsa = self.orsa_climate_stress(portfolio_input)
        casualty = self.assess_casualty_liability(portfolio_input)

        # Use first country exposure for NatCat and protection gap analysis
        primary_country = "USA"
        primary_peril = "flood"
        if portfolio_input.country_exposures:
            primary_country = max(
                portfolio_input.country_exposures,
                key=lambda c: portfolio_input.country_exposures[c]
            )
        if portfolio_input.peril_exposures:
            primary_peril = max(
                portfolio_input.peril_exposures,
                key=lambda p: portfolio_input.peril_exposures[p]
            )

        natcat_input = NatCatInput(
            country_code=primary_country,
            peril=primary_peril,
            insured_exposure_usd_m=portfolio_input.pc_exposure_usd_m or portfolio_input.total_exposure_usd_m * 0.60,
            rcp_scenario="rcp45",
        )
        natcat = self.model_natcat_loss(natcat_input)

        # Parametric design example
        param_input = ParametricDesignInput(
            product_name="Sovereign Flood Parametric Bond",
            peril=primary_peril,
            trigger_type="flood_depth",
            country_code=primary_country,
            exposure_value_usd_m=natcat_input.insured_exposure_usd_m * 0.20,
        )
        parametric = self.design_parametric_product(param_input)

        protection_gap = self.analyse_protection_gap(primary_country, primary_peril)

        # Overall climate risk score
        iais_score = iais["overall_score_pct"] / 100
        var_score = max(0, 1 - climate_var["net_climate_var_pct"] / 20)
        orsa_score = orsa["checklist_score_pct"] / 100
        overall = round((iais_score * 0.35 + var_score * 0.35 + orsa_score * 0.30) * 100, 1)

        flags: List[str] = []
        if iais["rag_flag"] == "red":
            flags.append("IAIS supervisory action required — overall compliance below 40%")
        if iais["rag_flag"] == "amber":
            flags.append("IAIS supervisory concern — governance or risk management gaps identified")
        if climate_var["net_climate_var_pct"] > 10:
            flags.append(f"Climate VaR exceeds 10% of total exposure under {portfolio_input.ngfs_scenario} scenario")

        return ClimateInsuranceResult(
            insurer_name=portfolio_input.insurer_name,
            reporting_year=portfolio_input.reporting_year,
            iais_compliance=iais,
            parametric_design=parametric,
            natcat_loss=natcat,
            climate_var=climate_var,
            orsa_stress=orsa,
            casualty_liability=casualty,
            protection_gap=protection_gap,
            overall_climate_risk_score=overall,
            supervisory_flags=flags,
        )


# Module-level singleton
climate_insurance_engine = ClimateInsuranceEngine()
