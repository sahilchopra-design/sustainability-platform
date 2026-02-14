"""
Seed all 24 NGFS scenarios with parameters and time series data.
"""

from sqlalchemy.orm import Session
import math

from db.models.ngfs_v2 import NGFSScenario, NGFSScenarioParameter, NGFSScenarioTimeSeries

SCENARIOS = [
    # ===== PHASE 1 (2020) =====
    {"name": "Orderly (Below 2°C)", "slug": "orderly-below-2c", "phase": 1, "phase_year": 2020,
     "category": "Orderly", "temperature_target": 1.5, "temperature_by_2100": 1.5,
     "carbon_neutral_year": 2050,
     "description": "Immediate, ambitious climate action with smooth transition to a low-carbon economy.",
     "policy_implications": "Early, coordinated carbon pricing and regulation drives efficient decarbonization across all sectors.",
     "physical_risk_level": "Low", "transition_risk_level": "Moderate",
     "key_assumptions": {"policy_start": 2020, "cooperation": "High", "tech_progress": "Moderate"},
     "carbon_price": {"2025": 50, "2030": 100, "2040": 180, "2050": 250, "2060": 280, "2070": 300, "2080": 310, "2090": 315, "2100": 320},
     "emissions": {"2025": 38, "2030": 28, "2040": 12, "2050": 0, "2060": -3, "2070": -5, "2080": -5, "2090": -4, "2100": -3},
     "temperature": {"2025": 1.2, "2030": 1.3, "2040": 1.4, "2050": 1.45, "2060": 1.47, "2070": 1.48, "2080": 1.49, "2090": 1.5, "2100": 1.5},
     "gdp_impact": {"2025": -1.0, "2030": -2.0, "2040": -0.5, "2050": 1.0, "2060": 2.0, "2070": 2.5, "2080": 2.8, "2090": 3.0, "2100": 3.0}},

    {"name": "Disorderly (Below 2°C)", "slug": "disorderly-below-2c", "phase": 1, "phase_year": 2020,
     "category": "Disorderly", "temperature_target": 1.7, "temperature_by_2100": 1.7,
     "carbon_neutral_year": 2070,
     "description": "Delayed, sudden climate action causing economic disruption before reaching targets.",
     "policy_implications": "Delayed action followed by abrupt policy shifts creates market shocks and stranded assets.",
     "physical_risk_level": "Low-Moderate", "transition_risk_level": "High",
     "key_assumptions": {"policy_start": 2030, "cooperation": "Moderate", "tech_progress": "Moderate"},
     "carbon_price": {"2025": 20, "2030": 50, "2040": 200, "2050": 400, "2060": 380, "2070": 350, "2080": 320, "2090": 300, "2100": 280},
     "emissions": {"2025": 40, "2030": 38, "2040": 20, "2050": 5, "2060": -2, "2070": 0, "2080": -1, "2090": -1, "2100": -1},
     "temperature": {"2025": 1.2, "2030": 1.35, "2040": 1.5, "2050": 1.6, "2060": 1.65, "2070": 1.68, "2080": 1.69, "2090": 1.7, "2100": 1.7},
     "gdp_impact": {"2025": -0.5, "2030": -2.0, "2040": -4.0, "2050": -1.5, "2060": 0.5, "2070": 1.5, "2080": 2.0, "2090": 2.0, "2100": 2.0}},

    {"name": "Hot House World", "slug": "hot-house-world", "phase": 1, "phase_year": 2020,
     "category": "Hot House World", "temperature_target": 3.5, "temperature_by_2100": 3.5,
     "carbon_neutral_year": None,
     "description": "Minimal climate action leads to severe physical risks and irreversible climate damage.",
     "policy_implications": "Failure to act results in catastrophic physical risks dominating the economic landscape.",
     "physical_risk_level": "Catastrophic", "transition_risk_level": "Minimal",
     "key_assumptions": {"policy_start": None, "cooperation": "None", "tech_progress": "Low"},
     "carbon_price": {"2025": 5, "2030": 8, "2040": 12, "2050": 15, "2060": 15, "2070": 15, "2080": 15, "2090": 15, "2100": 15},
     "emissions": {"2025": 42, "2030": 44, "2040": 45, "2050": 44, "2060": 43, "2070": 42, "2080": 40, "2090": 38, "2100": 36},
     "temperature": {"2025": 1.2, "2030": 1.4, "2040": 1.8, "2050": 2.2, "2060": 2.6, "2070": 2.9, "2080": 3.1, "2090": 3.3, "2100": 3.5},
     "gdp_impact": {"2025": 0, "2030": -0.5, "2040": -2.0, "2050": -4.0, "2060": -5.5, "2070": -6.5, "2080": -7.0, "2090": -7.5, "2100": -8.0}},

    {"name": "Orderly (2°C)", "slug": "orderly-2c", "phase": 1, "phase_year": 2020,
     "category": "Orderly", "temperature_target": 2.0, "temperature_by_2100": 2.0,
     "carbon_neutral_year": 2060,
     "description": "Moderate, well-planned climate action keeping warming below 2°C.",
     "policy_implications": "Steady policy ramp-up allows industries to adapt gradually.",
     "physical_risk_level": "Low-Moderate", "transition_risk_level": "Moderate",
     "key_assumptions": {"policy_start": 2020, "cooperation": "Moderate-High", "tech_progress": "Moderate"},
     "carbon_price": {"2025": 40, "2030": 75, "2040": 130, "2050": 180, "2060": 200, "2070": 210, "2080": 215, "2090": 218, "2100": 220},
     "emissions": {"2025": 39, "2030": 32, "2040": 18, "2050": 5, "2060": 0, "2070": -2, "2080": -3, "2090": -3, "2100": -2},
     "temperature": {"2025": 1.2, "2030": 1.3, "2040": 1.5, "2050": 1.7, "2060": 1.8, "2070": 1.9, "2080": 1.95, "2090": 1.98, "2100": 2.0},
     "gdp_impact": {"2025": -0.8, "2030": -1.5, "2040": -0.5, "2050": 0.5, "2060": 1.5, "2070": 2.0, "2080": 2.3, "2090": 2.5, "2100": 2.5}},

    {"name": "Disorderly (2°C)", "slug": "disorderly-2c", "phase": 1, "phase_year": 2020,
     "category": "Disorderly", "temperature_target": 2.2, "temperature_by_2100": 2.2,
     "carbon_neutral_year": 2080,
     "description": "Delayed moderate action reaching 2°C target with higher economic costs.",
     "policy_implications": "Late start requires aggressive catch-up policies causing market disruptions.",
     "physical_risk_level": "Moderate", "transition_risk_level": "High",
     "key_assumptions": {"policy_start": 2030, "cooperation": "Low-Moderate", "tech_progress": "Moderate"},
     "carbon_price": {"2025": 15, "2030": 40, "2040": 150, "2050": 300, "2060": 290, "2070": 270, "2080": 250, "2090": 240, "2100": 230},
     "emissions": {"2025": 41, "2030": 40, "2040": 25, "2050": 10, "2060": 2, "2070": -1, "2080": 0, "2090": -1, "2100": -1},
     "temperature": {"2025": 1.2, "2030": 1.35, "2040": 1.55, "2050": 1.75, "2060": 1.9, "2070": 2.0, "2080": 2.1, "2090": 2.15, "2100": 2.2},
     "gdp_impact": {"2025": -0.3, "2030": -1.5, "2040": -3.0, "2050": -1.0, "2060": 0, "2070": 1.0, "2080": 1.5, "2090": 1.5, "2100": 1.5}},

    {"name": "Current Policies", "slug": "current-policies-p1", "phase": 1, "phase_year": 2020,
     "category": "Hot House World", "temperature_target": 2.8, "temperature_by_2100": 2.8,
     "carbon_neutral_year": None,
     "description": "Continuation of current policies with no additional climate ambition.",
     "policy_implications": "Business as usual leads to significant physical risks by mid-century.",
     "physical_risk_level": "High", "transition_risk_level": "Low",
     "key_assumptions": {"policy_start": None, "cooperation": "Low", "tech_progress": "Low"},
     "carbon_price": {"2025": 10, "2030": 20, "2040": 35, "2050": 50, "2060": 55, "2070": 55, "2080": 55, "2090": 55, "2100": 55},
     "emissions": {"2025": 41, "2030": 42, "2040": 40, "2050": 36, "2060": 32, "2070": 28, "2080": 25, "2090": 23, "2100": 20},
     "temperature": {"2025": 1.2, "2030": 1.35, "2040": 1.6, "2050": 1.9, "2060": 2.15, "2070": 2.35, "2080": 2.55, "2090": 2.7, "2100": 2.8},
     "gdp_impact": {"2025": 0, "2030": -0.5, "2040": -1.5, "2050": -3.0, "2060": -4.0, "2070": -4.5, "2080": -5.0, "2090": -5.0, "2100": -5.0}},

    # ===== PHASE 2 (2021) =====
    {"name": "NDCs", "slug": "ndcs", "phase": 2, "phase_year": 2021,
     "category": "Insufficient", "temperature_target": 2.5, "temperature_by_2100": 2.5, "carbon_neutral_year": 2080,
     "description": "Nationally Determined Contributions pathway — current pledges implemented but insufficient.",
     "physical_risk_level": "Moderate-High", "transition_risk_level": "Low-Moderate",
     "carbon_price": {"2025": 25, "2030": 50, "2040": 85, "2050": 120, "2060": 130, "2070": 135, "2080": 138, "2090": 140, "2100": 140},
     "emissions": {"2025": 40, "2030": 36, "2040": 28, "2050": 18, "2060": 10, "2070": 4, "2080": 0, "2090": -1, "2100": -1},
     "temperature": {"2025": 1.2, "2030": 1.35, "2040": 1.6, "2050": 1.85, "2060": 2.1, "2070": 2.25, "2080": 2.35, "2090": 2.45, "2100": 2.5},
     "gdp_impact": {"2025": -0.3, "2030": -1.0, "2040": -1.5, "2050": -2.0, "2060": -2.5, "2070": -3.0, "2080": -3.5, "2090": -3.5, "2100": -3.5}},

    {"name": "Divergent Net Zero", "slug": "divergent-net-zero", "phase": 2, "phase_year": 2021,
     "category": "Disorderly", "temperature_target": 1.5, "temperature_by_2100": 1.5, "carbon_neutral_year": 2050,
     "description": "Regional differences in timing — advanced economies by 2050, emerging by 2070.",
     "physical_risk_level": "Low", "transition_risk_level": "High",
     "carbon_price": {"2025": 60, "2030": 140, "2040": 260, "2050": 350, "2060": 330, "2070": 310, "2080": 290, "2090": 280, "2100": 270},
     "emissions": {"2025": 38, "2030": 26, "2040": 10, "2050": -1, "2060": -3, "2070": -4, "2080": -4, "2090": -3, "2100": -3},
     "temperature": {"2025": 1.2, "2030": 1.3, "2040": 1.4, "2050": 1.45, "2060": 1.47, "2070": 1.48, "2080": 1.49, "2090": 1.5, "2100": 1.5},
     "gdp_impact": {"2025": -1.5, "2030": -2.5, "2040": -1.0, "2050": 0.5, "2060": 1.5, "2070": 2.0, "2080": 2.5, "2090": 2.5, "2100": 2.5}},

    {"name": "Delayed Transition", "slug": "delayed-transition-p2", "phase": 2, "phase_year": 2021,
     "category": "Disorderly", "temperature_target": 1.8, "temperature_by_2100": 1.8, "carbon_neutral_year": 2060,
     "description": "Climate action starts in 2030, requiring much steeper emission reductions.",
     "physical_risk_level": "Moderate", "transition_risk_level": "Very High",
     "carbon_price": {"2025": 10, "2030": 80, "2040": 300, "2050": 500, "2060": 450, "2070": 400, "2080": 360, "2090": 340, "2100": 320},
     "emissions": {"2025": 42, "2030": 40, "2040": 18, "2050": 2, "2060": 0, "2070": -2, "2080": -3, "2090": -3, "2100": -2},
     "temperature": {"2025": 1.2, "2030": 1.38, "2040": 1.5, "2050": 1.6, "2060": 1.68, "2070": 1.73, "2080": 1.76, "2090": 1.78, "2100": 1.8},
     "gdp_impact": {"2025": 0, "2030": -2.5, "2040": -4.5, "2050": -2.0, "2060": 0, "2070": 1.5, "2080": 2.0, "2090": 2.0, "2100": 2.0}},

    {"name": "Low Demand", "slug": "low-demand", "phase": 2, "phase_year": 2021,
     "category": "Orderly", "temperature_target": 1.5, "temperature_by_2100": 1.5, "carbon_neutral_year": 2045,
     "description": "Rapid demand reduction through behavioral change and efficiency gains.",
     "physical_risk_level": "Low", "transition_risk_level": "Moderate",
     "carbon_price": {"2025": 70, "2030": 120, "2040": 170, "2050": 200, "2060": 210, "2070": 215, "2080": 218, "2090": 220, "2100": 220},
     "emissions": {"2025": 36, "2030": 22, "2040": 8, "2050": -2, "2060": -4, "2070": -5, "2080": -5, "2090": -4, "2100": -3},
     "temperature": {"2025": 1.2, "2030": 1.28, "2040": 1.38, "2050": 1.42, "2060": 1.45, "2070": 1.47, "2080": 1.48, "2090": 1.49, "2100": 1.5},
     "gdp_impact": {"2025": -1.2, "2030": -1.5, "2040": -0.5, "2050": 0.8, "2060": 1.8, "2070": 2.5, "2080": 2.8, "2090": 3.0, "2100": 3.0}},

    {"name": "Fragmented World", "slug": "fragmented-world", "phase": 2, "phase_year": 2021,
     "category": "Hot House World", "temperature_target": 3.2, "temperature_by_2100": 3.2, "carbon_neutral_year": None,
     "description": "Limited international cooperation leads to fragmented, ineffective climate action.",
     "physical_risk_level": "Very High", "transition_risk_level": "Low",
     "carbon_price": {"2025": 5, "2030": 10, "2040": 20, "2050": 30, "2060": 30, "2070": 30, "2080": 30, "2090": 30, "2100": 30},
     "emissions": {"2025": 42, "2030": 43, "2040": 42, "2050": 40, "2060": 37, "2070": 34, "2080": 31, "2090": 28, "2100": 26},
     "temperature": {"2025": 1.2, "2030": 1.4, "2040": 1.7, "2050": 2.1, "2060": 2.4, "2070": 2.65, "2080": 2.85, "2090": 3.05, "2100": 3.2},
     "gdp_impact": {"2025": 0, "2030": -0.5, "2040": -2.0, "2050": -3.5, "2060": -5.0, "2070": -6.0, "2080": -6.5, "2090": -7.0, "2100": -7.0}},

    {"name": "High Growth", "slug": "high-growth", "phase": 2, "phase_year": 2021,
     "category": "Orderly", "temperature_target": 2.2, "temperature_by_2100": 2.2, "carbon_neutral_year": 2055,
     "description": "High economic growth combined with strong climate policies.",
     "physical_risk_level": "Moderate", "transition_risk_level": "Moderate",
     "carbon_price": {"2025": 45, "2030": 90, "2040": 160, "2050": 220, "2060": 230, "2070": 235, "2080": 238, "2090": 240, "2100": 240},
     "emissions": {"2025": 40, "2030": 33, "2040": 18, "2050": 5, "2060": 0, "2070": -2, "2080": -3, "2090": -3, "2100": -2},
     "temperature": {"2025": 1.2, "2030": 1.35, "2040": 1.55, "2050": 1.75, "2060": 1.9, "2070": 2.0, "2080": 2.1, "2090": 2.15, "2100": 2.2},
     "gdp_impact": {"2025": 0.5, "2030": 0, "2040": 1.0, "2050": 2.5, "2060": 3.5, "2070": 4.0, "2080": 4.5, "2090": 4.5, "2100": 4.5}},

    {"name": "Low Growth", "slug": "low-growth", "phase": 2, "phase_year": 2021,
     "category": "Insufficient", "temperature_target": 2.8, "temperature_by_2100": 2.8, "carbon_neutral_year": 2090,
     "description": "Economic stagnation limits climate investment capacity.",
     "physical_risk_level": "High", "transition_risk_level": "Low",
     "carbon_price": {"2025": 20, "2030": 35, "2040": 55, "2050": 80, "2060": 85, "2070": 88, "2080": 90, "2090": 90, "2100": 90},
     "emissions": {"2025": 41, "2030": 40, "2040": 35, "2050": 28, "2060": 20, "2070": 14, "2080": 8, "2090": 2, "2100": 0},
     "temperature": {"2025": 1.2, "2030": 1.35, "2040": 1.6, "2050": 1.9, "2060": 2.15, "2070": 2.35, "2080": 2.55, "2090": 2.7, "2100": 2.8},
     "gdp_impact": {"2025": -0.5, "2030": -1.0, "2040": -1.5, "2050": -2.5, "2060": -3.0, "2070": -3.5, "2080": -4.0, "2090": -4.0, "2100": -4.0}},

    {"name": "Technology Breakthrough", "slug": "technology-breakthrough", "phase": 2, "phase_year": 2021,
     "category": "Orderly", "temperature_target": 1.4, "temperature_by_2100": 1.4, "carbon_neutral_year": 2040,
     "description": "Rapid technological advancement enables faster, cheaper decarbonization.",
     "physical_risk_level": "Low", "transition_risk_level": "Low-Moderate",
     "carbon_price": {"2025": 30, "2030": 55, "2040": 80, "2050": 100, "2060": 105, "2070": 108, "2080": 110, "2090": 110, "2100": 110},
     "emissions": {"2025": 36, "2030": 22, "2040": 5, "2050": -5, "2060": -7, "2070": -8, "2080": -7, "2090": -6, "2100": -5},
     "temperature": {"2025": 1.18, "2030": 1.25, "2040": 1.32, "2050": 1.35, "2060": 1.37, "2070": 1.38, "2080": 1.39, "2090": 1.4, "2100": 1.4},
     "gdp_impact": {"2025": -0.5, "2030": -0.5, "2040": 1.0, "2050": 3.0, "2060": 4.0, "2070": 4.5, "2080": 5.0, "2090": 5.0, "2100": 5.0}},

    {"name": "Carbon Price Floor", "slug": "carbon-price-floor", "phase": 2, "phase_year": 2021,
     "category": "Orderly", "temperature_target": 1.6, "temperature_by_2100": 1.6, "carbon_neutral_year": 2050,
     "description": "Coordinated global carbon pricing with minimum floor price.",
     "physical_risk_level": "Low", "transition_risk_level": "Moderate-High",
     "carbon_price": {"2025": 75, "2030": 150, "2040": 280, "2050": 400, "2060": 390, "2070": 380, "2080": 370, "2090": 360, "2100": 350},
     "emissions": {"2025": 37, "2030": 24, "2040": 8, "2050": -1, "2060": -4, "2070": -5, "2080": -5, "2090": -4, "2100": -4},
     "temperature": {"2025": 1.2, "2030": 1.28, "2040": 1.4, "2050": 1.48, "2060": 1.52, "2070": 1.55, "2080": 1.57, "2090": 1.59, "2100": 1.6},
     "gdp_impact": {"2025": -1.5, "2030": -2.5, "2040": -1.0, "2050": 0.5, "2060": 1.5, "2070": 2.0, "2080": 2.5, "2090": 2.5, "2100": 2.5}},

    {"name": "Climate Finance Gap", "slug": "climate-finance-gap", "phase": 2, "phase_year": 2021,
     "category": "Insufficient", "temperature_target": 2.3, "temperature_by_2100": 2.3, "carbon_neutral_year": 2065,
     "description": "Insufficient climate finance limits the pace of energy transition.",
     "physical_risk_level": "Moderate-High", "transition_risk_level": "Moderate",
     "carbon_price": {"2025": 35, "2030": 65, "2040": 110, "2050": 150, "2060": 155, "2070": 158, "2080": 160, "2090": 160, "2100": 160},
     "emissions": {"2025": 40, "2030": 35, "2040": 24, "2050": 12, "2060": 4, "2070": 0, "2080": -2, "2090": -2, "2100": -2},
     "temperature": {"2025": 1.2, "2030": 1.35, "2040": 1.55, "2050": 1.75, "2060": 1.95, "2070": 2.08, "2080": 2.18, "2090": 2.25, "2100": 2.3},
     "gdp_impact": {"2025": -0.5, "2030": -1.2, "2040": -1.8, "2050": -2.0, "2060": -1.5, "2070": -1.0, "2080": -0.5, "2090": 0, "2100": 0}},

    # ===== PHASE 3 (2023) =====
    {"name": "Net Zero 2050", "slug": "net-zero-2050", "phase": 3, "phase_year": 2023,
     "category": "Orderly", "temperature_target": 1.5, "temperature_by_2100": 1.5, "carbon_neutral_year": 2050,
     "description": "Most ambitious global pathway — net zero by 2050 with coordinated action.",
     "physical_risk_level": "Low", "transition_risk_level": "High initially, declining",
     "carbon_price": {"2025": 80, "2030": 180, "2040": 340, "2050": 450, "2060": 430, "2070": 410, "2080": 400, "2090": 390, "2100": 380},
     "emissions": {"2025": 37, "2030": 24, "2040": 6, "2050": 0, "2060": -4, "2070": -6, "2080": -6, "2090": -5, "2100": -4},
     "temperature": {"2025": 1.2, "2030": 1.28, "2040": 1.38, "2050": 1.43, "2060": 1.46, "2070": 1.48, "2080": 1.49, "2090": 1.5, "2100": 1.5},
     "gdp_impact": {"2025": -1.8, "2030": -3.0, "2040": -1.0, "2050": 1.0, "2060": 2.5, "2070": 3.5, "2080": 4.0, "2090": 4.0, "2100": 4.0}},

    {"name": "Below 2°C (Phase 3)", "slug": "below-2c-p3", "phase": 3, "phase_year": 2023,
     "category": "Orderly", "temperature_target": 1.7, "temperature_by_2100": 1.7, "carbon_neutral_year": 2060,
     "description": "Moderate global action keeping temperature well below 2°C.",
     "physical_risk_level": "Moderate", "transition_risk_level": "Moderate",
     "carbon_price": {"2025": 55, "2030": 120, "2040": 210, "2050": 280, "2060": 275, "2070": 270, "2080": 265, "2090": 260, "2100": 260},
     "emissions": {"2025": 38, "2030": 28, "2040": 14, "2050": 3, "2060": 0, "2070": -3, "2080": -4, "2090": -3, "2100": -3},
     "temperature": {"2025": 1.2, "2030": 1.3, "2040": 1.45, "2050": 1.55, "2060": 1.6, "2070": 1.65, "2080": 1.68, "2090": 1.7, "2100": 1.7},
     "gdp_impact": {"2025": -1.0, "2030": -2.0, "2040": -0.8, "2050": 0.5, "2060": 1.5, "2070": 2.0, "2080": 2.5, "2090": 2.5, "2100": 2.5}},

    {"name": "NDCs (Phase 3)", "slug": "ndcs-p3", "phase": 3, "phase_year": 2023,
     "category": "Insufficient", "temperature_target": 2.4, "temperature_by_2100": 2.4, "carbon_neutral_year": 2080,
     "description": "Current pledges pathway — updated NDCs still insufficient for 2°C.",
     "physical_risk_level": "Moderate-High", "transition_risk_level": "Low",
     "carbon_price": {"2025": 30, "2030": 60, "2040": 100, "2050": 140, "2060": 145, "2070": 148, "2080": 150, "2090": 150, "2100": 150},
     "emissions": {"2025": 40, "2030": 35, "2040": 25, "2050": 15, "2060": 8, "2070": 3, "2080": 0, "2090": -1, "2100": -1},
     "temperature": {"2025": 1.2, "2030": 1.35, "2040": 1.58, "2050": 1.8, "2060": 2.0, "2070": 2.15, "2080": 2.28, "2090": 2.35, "2100": 2.4},
     "gdp_impact": {"2025": -0.3, "2030": -0.8, "2040": -1.5, "2050": -2.0, "2060": -2.5, "2070": -3.0, "2080": -3.5, "2090": -3.5, "2100": -3.5}},

    {"name": "Current Policies (Phase 3)", "slug": "current-policies-p3", "phase": 3, "phase_year": 2023,
     "category": "Hot House World", "temperature_target": 2.7, "temperature_by_2100": 2.7, "carbon_neutral_year": None,
     "description": "No new policies beyond currently implemented ones.",
     "physical_risk_level": "High", "transition_risk_level": "Low",
     "carbon_price": {"2025": 15, "2030": 25, "2040": 40, "2050": 60, "2060": 62, "2070": 63, "2080": 64, "2090": 65, "2100": 65},
     "emissions": {"2025": 41, "2030": 41, "2040": 38, "2050": 33, "2060": 28, "2070": 24, "2080": 21, "2090": 18, "2100": 16},
     "temperature": {"2025": 1.2, "2030": 1.35, "2040": 1.58, "2050": 1.85, "2060": 2.1, "2070": 2.3, "2080": 2.48, "2090": 2.6, "2100": 2.7},
     "gdp_impact": {"2025": 0, "2030": -0.5, "2040": -1.5, "2050": -2.5, "2060": -3.5, "2070": -4.0, "2080": -4.5, "2090": -5.0, "2100": -5.0}},

    {"name": "Delayed Transition (Phase 3)", "slug": "delayed-transition-p3", "phase": 3, "phase_year": 2023,
     "category": "Disorderly", "temperature_target": 1.9, "temperature_by_2100": 1.9, "carbon_neutral_year": 2065,
     "description": "Climate action starts from 2035, requiring extremely steep emission cuts.",
     "physical_risk_level": "Moderate", "transition_risk_level": "Very High",
     "carbon_price": {"2025": 12, "2030": 20, "2040": 350, "2050": 600, "2060": 550, "2070": 500, "2080": 460, "2090": 430, "2100": 400},
     "emissions": {"2025": 42, "2030": 42, "2040": 20, "2050": 3, "2060": -1, "2070": -3, "2080": -4, "2090": -3, "2100": -3},
     "temperature": {"2025": 1.2, "2030": 1.4, "2040": 1.55, "2050": 1.65, "2060": 1.73, "2070": 1.8, "2080": 1.85, "2090": 1.88, "2100": 1.9},
     "gdp_impact": {"2025": 0, "2030": -0.5, "2040": -5.0, "2050": -3.0, "2060": -1.0, "2070": 0.5, "2080": 1.5, "2090": 2.0, "2100": 2.0}},

    {"name": "Fragmented Net Zero", "slug": "fragmented-net-zero", "phase": 3, "phase_year": 2023,
     "category": "Disorderly", "temperature_target": 1.8, "temperature_by_2100": 1.8, "carbon_neutral_year": 2055,
     "description": "Advanced economies reach net zero by 2045, emerging economies by 2065.",
     "physical_risk_level": "Moderate", "transition_risk_level": "High",
     "carbon_price": {"2025": 65, "2030": 150, "2040": 280, "2050": 380, "2060": 360, "2070": 340, "2080": 320, "2090": 310, "2100": 300},
     "emissions": {"2025": 38, "2030": 27, "2040": 12, "2050": 2, "2060": -2, "2070": -4, "2080": -4, "2090": -3, "2100": -3},
     "temperature": {"2025": 1.2, "2030": 1.3, "2040": 1.45, "2050": 1.55, "2060": 1.63, "2070": 1.7, "2080": 1.75, "2090": 1.78, "2100": 1.8},
     "gdp_impact": {"2025": -1.2, "2030": -2.5, "2040": -1.5, "2050": 0, "2060": 1.0, "2070": 2.0, "2080": 2.5, "2090": 2.5, "2100": 2.5}},

    {"name": "Low International Ambition", "slug": "low-international-ambition", "phase": 3, "phase_year": 2023,
     "category": "Hot House World", "temperature_target": 3.2, "temperature_by_2100": 3.2, "carbon_neutral_year": None,
     "description": "Very limited international cooperation on climate action.",
     "physical_risk_level": "Very High", "transition_risk_level": "Low",
     "carbon_price": {"2025": 8, "2030": 12, "2040": 18, "2050": 25, "2060": 25, "2070": 25, "2080": 25, "2090": 25, "2100": 25},
     "emissions": {"2025": 42, "2030": 43, "2040": 43, "2050": 42, "2060": 40, "2070": 37, "2080": 34, "2090": 31, "2100": 28},
     "temperature": {"2025": 1.2, "2030": 1.4, "2040": 1.7, "2050": 2.1, "2060": 2.4, "2070": 2.65, "2080": 2.85, "2090": 3.05, "2100": 3.2},
     "gdp_impact": {"2025": 0, "2030": -0.5, "2040": -2.0, "2050": -3.5, "2060": -5.0, "2070": -6.0, "2080": -6.5, "2090": -7.0, "2100": -7.5}},

    {"name": "High Physical Risk", "slug": "high-physical-risk", "phase": 3, "phase_year": 2023,
     "category": "Hot House World", "temperature_target": 3.5, "temperature_by_2100": 3.5, "carbon_neutral_year": None,
     "description": "Worst-case scenario with catastrophic physical climate impacts.",
     "physical_risk_level": "Catastrophic", "transition_risk_level": "Minimal",
     "carbon_price": {"2025": 5, "2030": 8, "2040": 12, "2050": 20, "2060": 20, "2070": 20, "2080": 20, "2090": 20, "2100": 20},
     "emissions": {"2025": 43, "2030": 45, "2040": 46, "2050": 45, "2060": 44, "2070": 42, "2080": 40, "2090": 38, "2100": 36},
     "temperature": {"2025": 1.22, "2030": 1.45, "2040": 1.85, "2050": 2.3, "2060": 2.7, "2070": 3.0, "2080": 3.2, "2090": 3.35, "2100": 3.5},
     "gdp_impact": {"2025": 0, "2030": -0.8, "2040": -2.5, "2050": -5.0, "2060": -6.5, "2070": -7.5, "2080": -8.0, "2090": -8.5, "2100": -9.0}},
]

PARAMETER_DEFS = [
    {"name": "carbon_price", "display": "Carbon Price", "unit": "USD/tCO2", "category": "pricing",
     "min": 0, "max": 700, "step": 5},
    {"name": "emissions", "display": "CO2 Emissions", "unit": "Gt CO2/yr", "category": "emissions",
     "min": -10, "max": 50, "step": 1},
    {"name": "temperature", "display": "Global Temperature", "unit": "°C above pre-industrial", "category": "physical",
     "min": 1.0, "max": 4.0, "step": 0.05},
    {"name": "gdp_impact", "display": "GDP Impact", "unit": "% change from baseline", "category": "economic",
     "min": -10, "max": 6, "step": 0.5},
]


def seed_ngfs_scenarios(db: Session) -> dict:
    """Seed all 24 NGFS scenarios with parameters and time series."""
    # Check if already seeded
    existing = db.query(NGFSScenario).count()
    if existing >= 24:
        return {"message": "Already seeded", "count": existing}

    # Clear existing
    db.query(NGFSScenarioTimeSeries).delete()
    db.query(NGFSScenarioParameter).delete()
    db.query(NGFSScenario).delete()
    db.commit()

    created = 0
    for sc_data in SCENARIOS:
        sc = NGFSScenario(
            name=sc_data["name"], slug=sc_data["slug"],
            phase=sc_data["phase"], phase_year=sc_data.get("phase_year"),
            category=sc_data.get("category"),
            temperature_target=sc_data.get("temperature_target"),
            temperature_by_2100=sc_data.get("temperature_by_2100"),
            carbon_neutral_year=sc_data.get("carbon_neutral_year"),
            description=sc_data.get("description"),
            key_assumptions=sc_data.get("key_assumptions", {}),
            policy_implications=sc_data.get("policy_implications", ""),
            physical_risk_level=sc_data.get("physical_risk_level"),
            transition_risk_level=sc_data.get("transition_risk_level"),
        )
        db.add(sc)
        db.flush()

        # Add parameters and time series
        for pdef in PARAMETER_DEFS:
            ts_data = sc_data.get(pdef["name"], {})
            if not ts_data:
                continue

            param = NGFSScenarioParameter(
                scenario_id=sc.id, parameter_name=pdef["name"],
                display_name=pdef["display"], unit=pdef["unit"],
                category=pdef["category"], is_editable=True,
                min_value=pdef["min"], max_value=pdef["max"],
                default_value=list(ts_data.values())[0] if ts_data else 0,
                step_size=pdef["step"],
            )
            db.add(param)

            # Interpolate missing years
            years_with_data = sorted(ts_data.keys(), key=int)
            all_years = range(2025, 2101)
            for year in all_years:
                y_str = str(year)
                if y_str in ts_data:
                    val = ts_data[y_str]
                    interp = False
                else:
                    # Linear interpolation
                    prev_y = max((int(y) for y in years_with_data if int(y) <= year), default=None)
                    next_y = min((int(y) for y in years_with_data if int(y) >= year), default=None)
                    if prev_y is not None and next_y is not None and prev_y != next_y:
                        frac = (year - prev_y) / (next_y - prev_y)
                        val = ts_data[str(prev_y)] + frac * (ts_data[str(next_y)] - ts_data[str(prev_y)])
                    elif prev_y is not None:
                        val = ts_data[str(prev_y)]
                    elif next_y is not None:
                        val = ts_data[str(next_y)]
                    else:
                        continue
                    interp = True

                db.add(NGFSScenarioTimeSeries(
                    scenario_id=sc.id, parameter_name=pdef["name"],
                    year=year, value=round(val, 4), is_interpolated=interp,
                ))

        created += 1

    db.commit()
    return {"message": f"Seeded {created} NGFS scenarios", "count": created}
