"""
Water Risk & Stewardship Finance Engine — E92
Standards: WRI AQUEDUCT 4.0, CDP Water Security A-List, TNFD E3,
AWS Alliance for Water Stewardship Standard v2.0, CEO Water Mandate,
ICMA Green Bond Principles (Water UoP), SBTN Corporate Water Targets
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Reference Data — WRI AQUEDUCT 4.0
# ---------------------------------------------------------------------------

AQUEDUCT_INDICATORS: Dict[str, Dict] = {
    "baseline_water_stress": {
        "description": "Ratio of total water demand to available renewable surface water supply",
        "unit": "ratio 0-5",
        "thresholds": {
            "low": (0.0, 0.1),
            "low_medium": (0.1, 0.2),
            "medium_high": (0.2, 0.4),
            "high": (0.4, 0.8),
            "extremely_high": (0.8, 5.0),
        },
        "weight": 0.25,
        "source": "WRI AQUEDUCT 4.0 (2023)",
    },
    "interannual_variability": {
        "description": "Year-to-year variation in water supply (coefficient of variation)",
        "unit": "CV 0-2",
        "thresholds": {
            "low": (0.0, 0.25),
            "low_medium": (0.25, 0.50),
            "medium_high": (0.50, 0.75),
            "high": (0.75, 1.00),
            "extremely_high": (1.00, 2.00),
        },
        "weight": 0.15,
        "source": "WRI AQUEDUCT 4.0 (2023)",
    },
    "seasonal_variability": {
        "description": "Within-year variation in water supply between months",
        "unit": "CV 0-2",
        "thresholds": {
            "low": (0.0, 0.33),
            "low_medium": (0.33, 0.67),
            "medium_high": (0.67, 1.00),
            "high": (1.00, 1.33),
            "extremely_high": (1.33, 2.00),
        },
        "weight": 0.15,
        "source": "WRI AQUEDUCT 4.0 (2023)",
    },
    "groundwater_depletion": {
        "description": "Absolute groundwater depletion rate (recharge minus withdrawals)",
        "unit": "cm/yr",
        "thresholds": {
            "low": (0.0, 1.0),
            "low_medium": (1.0, 3.0),
            "medium_high": (3.0, 6.0),
            "high": (6.0, 12.0),
            "extremely_high": (12.0, 30.0),
        },
        "weight": 0.20,
        "source": "WRI AQUEDUCT 4.0 (2023)",
    },
    "riverine_flood_risk": {
        "description": "Population exposed to 1-in-100-year riverine flood events",
        "unit": "% population",
        "thresholds": {
            "low": (0.0, 5.0),
            "low_medium": (5.0, 10.0),
            "medium_high": (10.0, 20.0),
            "high": (20.0, 40.0),
            "extremely_high": (40.0, 100.0),
        },
        "weight": 0.15,
        "source": "WRI AQUEDUCT Floods (2023)",
    },
    "coastal_eutrophication": {
        "description": "Nutrient loading potential contributing to coastal eutrophication",
        "unit": "score 0-5",
        "thresholds": {
            "low": (0.0, 1.0),
            "low_medium": (1.0, 2.0),
            "medium_high": (2.0, 3.0),
            "high": (3.0, 4.0),
            "extremely_high": (4.0, 5.0),
        },
        "weight": 0.10,
        "source": "WRI AQUEDUCT 4.0 (2023)",
    },
}

AQUEDUCT_RISK_TIERS: Dict[str, Dict] = {
    "low":      {"score_range": [0, 20],  "label": "Low",      "color": "#006400", "recommended_action": "Monitor annually via AQUEDUCT online tool"},
    "medium":   {"score_range": [20, 40], "label": "Medium",   "color": "#FFD700", "recommended_action": "Engage supplier; set facility-level reduction targets"},
    "high":     {"score_range": [40, 60], "label": "High",     "color": "#FF8C00", "recommended_action": "Basin water stewardship plan required within 12 months"},
    "critical": {"score_range": [60, 100],"label": "Critical", "color": "#DC143C", "recommended_action": "Board escalation; capital reallocation review; immediate stewardship plan"},
}

AQUEDUCT_BASIN_BENCHMARKS: Dict[str, Dict] = {
    "Indus":              {"baseline_water_stress": 4.8, "groundwater_depletion": 28.0, "riverine_flood_risk": 28.0, "region": "South Asia",     "country": "India/Pakistan",     "aqueduct_overall_score": 88},
    "Yellow River":       {"baseline_water_stress": 4.2, "groundwater_depletion": 15.0, "riverine_flood_risk": 22.0, "region": "East Asia",      "country": "China",              "aqueduct_overall_score": 82},
    "Colorado":           {"baseline_water_stress": 4.5, "groundwater_depletion": 12.5, "riverine_flood_risk": 8.0,  "region": "North America",  "country": "USA/Mexico",         "aqueduct_overall_score": 79},
    "Ganges-Brahmaputra": {"baseline_water_stress": 3.9, "groundwater_depletion": 22.0, "riverine_flood_risk": 35.0, "region": "South Asia",     "country": "India/Bangladesh",   "aqueduct_overall_score": 77},
    "Tigris-Euphrates":   {"baseline_water_stress": 4.1, "groundwater_depletion": 18.0, "riverine_flood_risk": 15.0, "region": "Middle East",    "country": "Iraq/Turkey/Syria",  "aqueduct_overall_score": 83},
    "Murray-Darling":     {"baseline_water_stress": 3.2, "groundwater_depletion": 4.5,  "riverine_flood_risk": 12.0, "region": "Oceania",        "country": "Australia",          "aqueduct_overall_score": 64},
    "Nile":               {"baseline_water_stress": 4.6, "groundwater_depletion": 9.0,  "riverine_flood_risk": 18.0, "region": "Africa",         "country": "Egypt/Sudan/Ethiopia","aqueduct_overall_score": 81},
    "Mekong":             {"baseline_water_stress": 1.2, "groundwater_depletion": 2.0,  "riverine_flood_risk": 30.0, "region": "Southeast Asia", "country": "Vietnam/Cambodia",   "aqueduct_overall_score": 38},
    "Amazon":             {"baseline_water_stress": 0.1, "groundwater_depletion": 0.1,  "riverine_flood_risk": 40.0, "region": "South America",  "country": "Brazil",             "aqueduct_overall_score": 7},
    "Rhine":              {"baseline_water_stress": 0.8, "groundwater_depletion": 0.5,  "riverine_flood_risk": 10.0, "region": "Europe",         "country": "Germany/Netherlands","aqueduct_overall_score": 21},
    "Danube":             {"baseline_water_stress": 0.6, "groundwater_depletion": 0.4,  "riverine_flood_risk": 8.0,  "region": "Europe",         "country": "Romania/Austria",    "aqueduct_overall_score": 18},
    "Mississippi":        {"baseline_water_stress": 1.1, "groundwater_depletion": 3.5,  "riverine_flood_risk": 14.0, "region": "North America",  "country": "USA",                "aqueduct_overall_score": 33},
    "Yangtze":            {"baseline_water_stress": 1.8, "groundwater_depletion": 5.0,  "riverine_flood_risk": 25.0, "region": "East Asia",      "country": "China",              "aqueduct_overall_score": 44},
    "Zambezi":            {"baseline_water_stress": 0.9, "groundwater_depletion": 0.8,  "riverine_flood_risk": 20.0, "region": "Africa",         "country": "Zambia/Zimbabwe",    "aqueduct_overall_score": 24},
    "Jordan":             {"baseline_water_stress": 4.9, "groundwater_depletion": 14.0, "riverine_flood_risk": 5.0,  "region": "Middle East",    "country": "Jordan/Israel",      "aqueduct_overall_score": 85},
}

# ---------------------------------------------------------------------------
# Reference Data — CDP Water Security A-List
# ---------------------------------------------------------------------------

CDP_WATER_CRITERIA: Dict[str, Dict] = {
    "governance": {
        "weight": 0.25,
        "description": "Board oversight; water policy; management accountability; executive remuneration linkage",
        "sub_criteria": [
            "Board-level oversight of water risk (Module W1.1)",
            "Dedicated water policy statement publicly available",
            "Water risk formally integrated into enterprise risk management framework",
            "Water-related KPIs explicitly linked to executive remuneration",
        ],
        "a_list_minimum": 0.80,
        "questionnaire_module": "CDP Water W1",
    },
    "risk_identification": {
        "weight": 0.25,
        "description": "AQUEDUCT basin screening; value chain water risk mapping; regulatory risk quantification",
        "sub_criteria": [
            "Facility-level water risk assessment using AQUEDUCT 4.0 or Waterfall equivalent",
            "Tier 1 and key Tier 2 supply chain water risk mapping",
            "Quantified regulatory exposure and reputational risk from water",
            "Climate change water scenario modelling (minimum 2 scenarios, 2 time horizons)",
        ],
        "a_list_minimum": 0.80,
        "questionnaire_module": "CDP Water W2",
    },
    "targets": {
        "weight": 0.25,
        "description": "Science-based water targets (SBTN); location-specific; timebound; wastewater quality",
        "sub_criteria": [
            "Absolute water withdrawal reduction target (minimum 10% by 2030, 25% preferred)",
            "Location-specific context-based targets for water-stressed area facilities",
            "Wastewater quality discharge targets with monitoring programme",
            "Formal alignment with SBTN Corporate Water Targets v1.0 guidance",
        ],
        "a_list_minimum": 0.80,
        "questionnaire_module": "CDP Water W4",
    },
    "performance": {
        "weight": 0.25,
        "description": "GRI 303 disclosure quality; third-party verified data; year-on-year improvement",
        "sub_criteria": [
            "Third-party verified water withdrawal and consumption data (limited assurance minimum)",
            "Full GRI 303: Water and Effluents 2018 disclosure (303-1 through 303-5)",
            "Demonstrated year-on-year absolute or intensity performance improvement",
            "Documented water-stressed facility engagement and stewardship outcomes",
        ],
        "a_list_minimum": 0.80,
        "questionnaire_module": "CDP Water W6",
    },
}

CDP_GRADE_THRESHOLDS: Dict[str, Dict] = {
    "A":  {"min_score": 0.90, "label": "A-List Leadership",  "eligible": True,  "description": "All criteria above 80%; verified data; demonstrated catchment impact"},
    "A-": {"min_score": 0.80, "label": "A-List Borderline",  "eligible": True,  "description": "Strong governance and targets; minor verification or data gaps"},
    "B":  {"min_score": 0.65, "label": "Management",         "eligible": False, "description": "Addressing water risk; targets set but not science-based; no third-party verification"},
    "C":  {"min_score": 0.50, "label": "Awareness",          "eligible": False, "description": "Basic water disclosure; AQUEDUCT screening completed; no formal targets"},
    "D":  {"min_score": 0.30, "label": "Disclosure only",    "eligible": False, "description": "Minimal water action; disclosure only; no risk assessment"},
    "F":  {"min_score": 0.00, "label": "Non-disclosure / F", "eligible": False, "description": "No meaningful water security disclosure or CDP F score"},
}

# ---------------------------------------------------------------------------
# Reference Data — TNFD E3 Water Metrics
# ---------------------------------------------------------------------------

TNFD_E3_METRICS: Dict[str, Dict] = {
    "WD-1_withdrawal": {
        "label": "Total water withdrawal",
        "unit": "ML/yr",
        "gri_reference": "GRI 303-3",
        "tnfd_metric_id": "WD-1",
        "disclosure_level": "mandatory",
        "description": "Total water withdrawn from all sources (surface water, groundwater, rainwater, municipal supply)",
        "breakdown_required": ["surface_water_ML", "groundwater_ML", "rainwater_collected_ML", "municipal_supply_ML"],
        "sector_benchmarks_intensity_m3_per_revenue_m": {
            "food_beverage": 850, "textile": 1200, "chemicals": 600, "technology": 45, "mining": 2200, "energy": 380,
        },
    },
    "WD-2_consumption": {
        "label": "Total water consumption",
        "unit": "ML/yr",
        "gri_reference": "GRI 303-5",
        "tnfd_metric_id": "WD-2",
        "disclosure_level": "mandatory",
        "description": "Total water consumed (withdrawn minus discharged); water not returned to source",
    },
    "WD-3_discharge": {
        "label": "Total water discharge",
        "unit": "ML/yr",
        "gri_reference": "GRI 303-4",
        "tnfd_metric_id": "WD-3",
        "disclosure_level": "mandatory",
        "description": "Total water discharged by destination type and treatment quality level",
        "breakdown_required": ["freshwater_bodies_ML", "seawater_ML", "groundwater_ML", "third_party_treatment_ML"],
    },
    "WD-4_recycled_pct": {
        "label": "Water recycled or reused",
        "unit": "%",
        "gri_reference": "GRI 303-3a",
        "tnfd_metric_id": "WD-4",
        "disclosure_level": "encouraged",
        "description": "Percentage of total water volume recycled or reused at facility level",
        "sector_benchmark_pct": {"technology": 22, "chemicals": 35, "mining": 18, "food_beverage": 28, "textile": 15, "energy": 20},
    },
    "WD-5_stressed_area_pct": {
        "label": "Operations in water-stressed areas",
        "unit": "% of total operations",
        "gri_reference": "AQUEDUCT High / Extremely High stress zones",
        "tnfd_metric_id": "WD-5",
        "disclosure_level": "mandatory",
        "description": "Share of operational footprint (revenue or headcount weighted) in AQUEDUCT high or extremely high stress areas",
    },
    "WD-6_pollutant_load": {
        "label": "Key discharge pollutant loads",
        "unit": "tonnes/yr or mg/L",
        "gri_reference": "GRI 303-4",
        "tnfd_metric_id": "WD-6",
        "disclosure_level": "mandatory",
        "description": "Nitrogen, phosphorus, COD, BOD, and suspended solids in discharge; eutrophication potential",
    },
    "WD-7_catchment_engagement": {
        "label": "Catchment-level stakeholder engagement",
        "unit": "binary + qualitative description",
        "gri_reference": "TNFD E3 DR3 / AWS Standard engagement pillar",
        "tnfd_metric_id": "WD-7",
        "disclosure_level": "encouraged",
        "description": "Evidence of participation in collective basin or catchment stewardship initiatives",
    },
}

# ---------------------------------------------------------------------------
# Reference Data — AWS Alliance for Water Stewardship Standard v2.0
# ---------------------------------------------------------------------------

AWS_STANDARD_v2: Dict[str, Dict] = {
    "water_balance": {
        "pillar": "Water Balance",
        "code": "WB",
        "weight": 0.20,
        "requirement": "Quantify all water inflows and outflows at site level and verify accuracy annually",
        "core_criteria": ["WB1 — Quantified site water balance", "WB2 — Water accounting and public reporting"],
        "verification_required": True,
        "key_assessment_questions": [
            "Is a full water balance (inflows + outflows) quantified and documented at site level?",
            "Are measurement uncertainties documented and third-party verified?",
        ],
    },
    "governance": {
        "pillar": "Governance",
        "code": "G",
        "weight": 0.20,
        "requirement": "Water policy, clear roles and responsibilities, staff training, regulatory compliance",
        "core_criteria": ["G1 — Water stewardship policy", "G2 — Responsibilities assigned at senior level", "G3 — Staff trained on water stewardship"],
        "verification_required": True,
        "key_assessment_questions": [
            "Is there a documented, publicly available water stewardship policy signed by the CEO or equivalent?",
            "Are accountabilities for water management clearly defined at board and operational levels?",
        ],
    },
    "site_water_status": {
        "pillar": "Site Water Status",
        "code": "SWS",
        "weight": 0.20,
        "requirement": "Shared water challenges at catchment level identified; water dependencies and impacts mapped",
        "core_criteria": ["SWS1 — Catchment-level context understood", "SWS2 — Risks and opportunities identified and prioritised"],
        "verification_required": True,
        "key_assessment_questions": [
            "Has AQUEDUCT 4.0 or equivalent catchment-level screening been completed?",
            "Are shared water challenges with other basin users (agriculture, municipalities) documented?",
        ],
    },
    "engagement": {
        "pillar": "Engagement",
        "code": "E",
        "weight": 0.20,
        "requirement": "Meaningful, documented engagement with catchment-level stakeholders; collective action plans developed",
        "core_criteria": ["E1 — Stakeholder mapping and identification", "E2 — Engagement plan developed and implemented", "E3 — Engagement outcomes documented"],
        "verification_required": True,
        "key_assessment_questions": [
            "Is there documented engagement with government water agencies, NGOs, local communities, and co-basin users?",
            "Has collective catchment action been initiated or actively contributed to?",
        ],
    },
    "site_outcomes": {
        "pillar": "Site Outcomes",
        "code": "SO",
        "weight": 0.20,
        "requirement": "Measurable, time-bound outcomes for water efficiency, discharge quality, and governance improvement",
        "core_criteria": [
            "SO1 — Improved water use efficiency outcome achieved",
            "SO2 — Improved discharge water quality outcome achieved",
            "SO3 — Improved local water governance outcome achieved",
        ],
        "verification_required": True,
        "key_assessment_questions": [
            "Are measurable, time-bound water efficiency targets demonstrated as achieved and third-party verified?",
            "Is certified discharge quality data publicly available?",
        ],
    },
}

AWS_CERTIFICATION_TIERS: Dict[str, Dict] = {
    "none":     {"min_score_pct": 0,  "label": "Not Eligible",  "description": "Below AWS Core threshold; fundamental gaps across multiple pillars"},
    "core":     {"min_score_pct": 60, "label": "AWS Core",      "description": "Entry-level certification; basic water stewardship practices demonstrated"},
    "gold":     {"min_score_pct": 75, "label": "AWS Gold",      "description": "Advanced stewardship; strong engagement pillar and measurable site outcomes"},
    "platinum": {"min_score_pct": 90, "label": "AWS Platinum",  "description": "Leadership level; collective catchment action demonstrated; verified outcomes across all pillars"},
}

# ---------------------------------------------------------------------------
# Reference Data — CEO Water Mandate
# ---------------------------------------------------------------------------

CEO_WATER_MANDATE: Dict[str, Dict] = {
    "direct_operations": {
        "description": "Assess, improve, and publicly disclose water performance in own operations",
        "sdg_alignment": "SDG 6.4",
        "reporting_framework": "CDP Water Security Questionnaire; GRI 303",
        "commitment_weight": 0.25,
        "minimum_action": "Annual water balance disclosure plus absolute or intensity reduction target",
    },
    "supply_chain_watershed": {
        "description": "Engage key suppliers on water stewardship; screen Tier 1 supply chain for water risk",
        "sdg_alignment": "SDG 12.6",
        "reporting_framework": "CDP Supply Chain Water Security module",
        "commitment_weight": 0.20,
        "minimum_action": "Tier 1 supplier water risk assessment covering 80% of procurement spend in stressed basins",
    },
    "collective_action": {
        "description": "Participate in basin-level collective action with peers, governments, and civil society",
        "sdg_alignment": "SDG 17.17",
        "reporting_framework": "AWS Standard; Water Action Hub; 2030 WRG partnerships",
        "commitment_weight": 0.20,
        "minimum_action": "Active membership and contribution to at least one basin stewardship initiative",
    },
    "public_policy": {
        "description": "Engage constructively with policymakers on sustainable integrated water resources management",
        "sdg_alignment": "SDG 6.5",
        "reporting_framework": "CEO Water Mandate Annual Progress Report to UN Global Compact",
        "commitment_weight": 0.15,
        "minimum_action": "Documented policy engagement or response to government water consultation per year",
    },
    "community_engagement": {
        "description": "Respect and actively support the human right to water and sanitation for surrounding communities",
        "sdg_alignment": "SDG 6.1; SDG 6.2",
        "reporting_framework": "UN Resolution 64/292; CEO Water Mandate Guidance Note",
        "commitment_weight": 0.10,
        "minimum_action": "Community water access programme or WASH initiative in high-risk operating communities",
    },
    "transparency": {
        "description": "Measure, independently verify and disclose water stewardship performance annually",
        "sdg_alignment": "SDG 6.4; SDG 17.18",
        "reporting_framework": "CDP A-List; GRI 303; TNFD E3; IFRS S2",
        "commitment_weight": 0.10,
        "minimum_action": "Annual water data disclosure with at minimum limited third-party assurance",
    },
}

# ---------------------------------------------------------------------------
# Reference Data — Water Stewardship Bond Framework
# ---------------------------------------------------------------------------

WATER_BOND_FRAMEWORK: Dict[str, Any] = {
    "icma_alignment": "ICMA Green Bond Principles 2021 — Water and Wastewater Management Use of Proceeds Category",
    "eu_taxonomy_objective": "EU Taxonomy Objective 3 — Sustainable Use and Protection of Water and Marine Resources (Regulation EU 2020/852)",
    "sdg_alignment": ["SDG 6 — Clean Water and Sanitation", "SDG 14 — Life Below Water", "SDG 15 — Life on Land"],
    "eligible_use_of_proceeds": [
        {"category": "Water efficiency infrastructure",    "description": "Projects achieving >=20% operational water withdrawal reduction vs. baseline",          "eu_taxonomy_eligible": True,  "kpi_example": "ML water saved per annum"},
        {"category": "Wastewater treatment and recycling", "description": "Advanced treatment systems achieving WHO Class A or equivalent reuse standards",         "eu_taxonomy_eligible": True,  "kpi_example": "ML wastewater treated and reused"},
        {"category": "Nature-based water solutions",       "description": "Wetland restoration, riparian buffer zones, floodplain rehabilitation, managed recharge", "eu_taxonomy_eligible": True,  "kpi_example": "Ha of wetland or aquifer restored"},
        {"category": "Smart water metering / leak detect", "description": "Digital infrastructure reducing non-revenue water (distribution losses) by >=15%",       "eu_taxonomy_eligible": True,  "kpi_example": "% reduction in non-revenue water"},
        {"category": "Managed aquifer recharge (MAR)",     "description": "Groundwater recharge schemes in AQUEDUCT high/critical stress basins",                   "eu_taxonomy_eligible": True,  "kpi_example": "ML groundwater recharged per annum"},
        {"category": "Renewable-powered desalination",     "description": "RO desalination powered >=80% by on-site or PPAed renewable energy sources",             "eu_taxonomy_eligible": True,  "kpi_example": "ML potable water produced per GWh renewables"},
        {"category": "Drought-resilient agriculture",      "description": "Precision irrigation, deficit irrigation or soil moisture systems achieving >=30% savings","eu_taxonomy_eligible": True,  "kpi_example": "% water saving vs. flood irrigation baseline"},
        {"category": "Freshwater biodiversity corridors",  "description": "Fish passage restoration, river connectivity, in-stream habitat and IUCN species support", "eu_taxonomy_eligible": True,  "kpi_example": "km of river connectivity restored"},
    ],
    "framework_minimum_scores": {
        "icma_use_of_proceeds_alignment": 0.75,
        "eu_taxonomy_dnsh_water_check": 0.70,
        "impact_kpi_coverage": 0.80,
        "governance_quality": 0.70,
    },
    "reporting_requirements": {
        "allocation_reporting": "Annual allocation report within 12 months of issuance date",
        "impact_reporting": "Annual quantitative impact KPIs per eligible UoP category",
        "assurance": "Second Party Opinion pre-issuance; limited assurance on impact data post-issuance",
        "gri_standard": "GRI 303: Water and Effluents 2018",
        "tnfd_alignment": "TNFD E3 mandatory metrics (WD-1 to WD-5) required",
    },
    "greenium_estimate_bps": {
        "low_stress_basin":      3,
        "medium_stress_basin":   5,
        "high_stress_basin":     8,
        "critical_stress_basin": 12,
    },
}

# ---------------------------------------------------------------------------
# Pydantic Request Models
# ---------------------------------------------------------------------------


class WaterRiskAssessRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    entity_name: Optional[str] = "Unknown Entity"
    sector: Optional[str] = "industrial"
    basin_name: Optional[str] = None

    # WRI AQUEDUCT 4.0 indicator inputs
    baseline_water_stress: Optional[float] = Field(None, ge=0.0, le=5.0,   description="AQUEDUCT baseline water stress ratio 0-5")
    interannual_variability: Optional[float] = Field(None, ge=0.0, le=2.0, description="CV year-to-year variability 0-2")
    seasonal_variability: Optional[float] = Field(None, ge=0.0, le=2.0,    description="CV within-year variability 0-2")
    groundwater_depletion: Optional[float] = Field(None, ge=0.0, le=30.0,  description="Absolute depletion rate cm/yr")
    riverine_flood_risk: Optional[float] = Field(None, ge=0.0, le=100.0,   description="% population exposed to 100-yr riverine flood")
    coastal_eutrophication: Optional[float] = Field(None, ge=0.0, le=5.0,  description="Eutrophication potential score 0-5")

    # TNFD E3 operational metrics
    water_withdrawal_ml_yr: Optional[float] = Field(None, ge=0.0, description="Total water withdrawal ML/yr (GRI 303-3)")
    water_consumption_ml_yr: Optional[float] = Field(None, ge=0.0, description="Total water consumed ML/yr (GRI 303-5)")
    water_discharge_ml_yr: Optional[float] = Field(None, ge=0.0, description="Total water discharged ML/yr (GRI 303-4)")
    recycled_water_pct: Optional[float] = Field(None, ge=0.0, le=100.0, description="% of withdrawal recycled or reused")
    water_stressed_ops_pct: Optional[float] = Field(None, ge=0.0, le=100.0, description="% operations in AQUEDUCT high/extremely high stress areas")

    # CDP Water Security sub-scores (0-1)
    cdp_governance_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    cdp_risk_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    cdp_targets_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    cdp_performance_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    cdp_data_verified: Optional[bool] = False

    # AWS Standard v2.0 pillar scores (0-1)
    aws_water_balance_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    aws_governance_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    aws_site_water_status_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    aws_engagement_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    aws_site_outcomes_score: Optional[float] = Field(None, ge=0.0, le=1.0)

    # CEO Water Mandate
    cwm_committed: Optional[bool] = False
    cwm_commitment_scores: Optional[Dict[str, float]] = None

    # Financial context
    total_assets_m: Optional[float] = Field(100.0, ge=0.0)
    water_dependent_revenue_pct: Optional[float] = Field(30.0, ge=0.0, le=100.0)
    annual_water_opex_m: Optional[float] = Field(None, ge=0.0)


class StewardshipTargetRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    entity_name: Optional[str] = "Unknown Entity"
    target_type: Optional[str] = "withdrawal_reduction"
    baseline_year: Optional[int] = 2022
    target_year: Optional[int] = 2030
    baseline_withdrawal_ml_yr: Optional[float] = 500.0
    target_reduction_pct: Optional[float] = 25.0
    water_stressed_ops_pct: Optional[float] = 40.0
    sbtn_aligned: Optional[bool] = False
    third_party_verified: Optional[bool] = False


# ---------------------------------------------------------------------------
# Result Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class WaterRiskResult:
    entity_id: str
    entity_name: str
    sector: str
    basin_name: Optional[str]

    # AQUEDUCT 4.0
    aqueduct_indicator_scores: Dict[str, float]
    aqueduct_overall_score: float
    aqueduct_risk_tier: str

    # TNFD E3
    water_withdrawal_ml_yr: float
    water_consumption_ml_yr: float
    water_discharge_ml_yr: float
    recycled_pct: float
    water_stressed_area_pct: float
    tnfd_water_disclosure_score: float

    # CDP Water Security
    cdp_governance_score: float
    cdp_risk_score: float
    cdp_targets_score: float
    cdp_performance_score: float
    cdp_composite_score: float
    cdp_grade: str
    cdp_a_list_eligible: bool

    # AWS Standard v2.0
    aws_water_balance_score: float
    aws_governance_score: float
    aws_site_water_status_score: float
    aws_engagement_score: float
    aws_site_outcomes_score: float
    aws_overall_score: float
    aws_certification_level: str
    aws_certification_eligible: bool

    # CEO Water Mandate
    cwm_committed: bool
    cwm_targets_set: bool
    cwm_stewardship_score: float

    # Financial exposure
    water_opex_risk_m: float
    water_regulatory_risk_m: float
    water_stranded_asset_risk_m: float
    total_water_financial_risk_m: float

    # Stewardship bond
    water_bond_eligible: bool
    water_bond_framework_score: float

    # Overall
    water_risk_score: float
    water_risk_tier: str
    key_findings: List[str]
    recommendations: List[str]
    standards_applied: List[str]


@dataclass
class StewardshipTargetResult:
    entity_id: str
    entity_name: str
    target_type: str
    baseline_year: int
    target_year: int
    baseline_withdrawal_ml_yr: float
    target_reduction_pct: float
    target_withdrawal_ml_yr: float
    annual_reduction_ml_yr: float
    cagr_pct: float
    sbtn_aligned: bool
    aws_target_compatible: bool
    cdp_target_quality_score: float
    sdg_6_contribution: str
    target_validity_assessment: str
    recommendations: List[str]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _seed_float(entity_id: str, key: str, lo: float, hi: float) -> float:
    """Deterministic seeded float — reproducible demo data without randomness."""
    h = hash(f"{entity_id}:{key}") & 0xFFFFFF
    return round(lo + (h / 0xFFFFFF) * (hi - lo), 3)


def _normalise(value: float, lo: float, hi: float) -> float:
    """Map a raw value to 0-100 normalised score (higher = higher risk)."""
    span = max(hi - lo, 1e-9)
    return round(min(max((value - lo) / span, 0.0), 1.0) * 100.0, 2)


def _aqueduct_composite(data: Dict[str, Any], eid: str) -> Dict[str, Any]:
    """Compute AQUEDUCT 4.0 weighted composite risk score 0-100."""
    spec = {
        "baseline_water_stress":   (0.0, 5.0,   0.25, _seed_float(eid, "aq_bws", 0.5,  3.8)),
        "interannual_variability": (0.0, 2.0,   0.15, _seed_float(eid, "aq_iav", 0.2,  1.5)),
        "seasonal_variability":    (0.0, 2.0,   0.15, _seed_float(eid, "aq_sav", 0.2,  1.6)),
        "groundwater_depletion":   (0.0, 30.0,  0.20, _seed_float(eid, "aq_gwd", 0.0,  22.0)),
        "riverine_flood_risk":     (0.0, 100.0, 0.15, _seed_float(eid, "aq_rfr", 2.0,  45.0)),
        "coastal_eutrophication":  (0.0, 5.0,   0.10, _seed_float(eid, "aq_ceu", 0.5,  4.5)),
    }
    indicator_scores: Dict[str, float] = {}
    composite = 0.0
    for name, (lo, hi, wt, default) in spec.items():
        raw = data.get(name)
        if raw is None:
            raw = default
        score = _normalise(raw, lo, hi)
        indicator_scores[name] = score
        composite += score * wt
    return {"indicator_scores": indicator_scores, "composite": round(composite, 2)}


def _tier(score: float) -> str:
    if score < 20:
        return "low"
    elif score < 40:
        return "medium"
    elif score < 60:
        return "high"
    return "critical"


def _cdp_grade(composite: float) -> str:
    if composite >= 0.90:
        return "A"
    elif composite >= 0.80:
        return "A-"
    elif composite >= 0.65:
        return "B"
    elif composite >= 0.50:
        return "C"
    elif composite >= 0.30:
        return "D"
    return "F"


def _tnfd_disclosure_score(data: Dict) -> float:
    """Score TNFD E3 disclosure completeness 0-100."""
    score = 0.0
    for f in ("water_withdrawal_ml_yr", "water_consumption_ml_yr", "water_discharge_ml_yr", "water_stressed_ops_pct"):
        if data.get(f) is not None:
            score += 22.5
    if data.get("recycled_water_pct") is not None:
        score += 10.0
    return min(score, 100.0)


# ---------------------------------------------------------------------------
# Public Service Functions
# ---------------------------------------------------------------------------

def assess_water_risk(request_data: Dict) -> WaterRiskResult:
    """
    Full water risk and stewardship assessment per:
    WRI AQUEDUCT 4.0 | CDP Water Security A-List | TNFD E3 |
    AWS Standard v2.0 | CEO Water Mandate.
    Returns WaterRiskResult dataclass.
    """
    eid    = request_data.get("entity_id", "unknown")
    ename  = request_data.get("entity_name", "Unknown Entity")
    sector = request_data.get("sector", "industrial")
    basin  = request_data.get("basin_name")

    # ---- WRI AQUEDUCT 4.0 ----
    aq        = _aqueduct_composite(request_data, eid)
    aq_scores = aq["indicator_scores"]
    aq_score  = aq["composite"]
    aq_tier   = _tier(aq_score)

    # ---- TNFD E3 operational metrics ----
    withdrawal  = request_data.get("water_withdrawal_ml_yr") or _seed_float(eid, "wdraw",  50.0,   2000.0)
    consumption = request_data.get("water_consumption_ml_yr") or round(withdrawal * _seed_float(eid, "crat", 0.35, 0.68), 1)
    discharge   = request_data.get("water_discharge_ml_yr") or round(max(withdrawal - consumption, 0.0), 1)
    recycled    = request_data.get("recycled_water_pct") or _seed_float(eid, "recyc", 5.0, 40.0)
    stressed    = request_data.get("water_stressed_ops_pct") or _seed_float(eid, "strs",  10.0,  85.0)
    tnfd_score  = _tnfd_disclosure_score({
        "water_withdrawal_ml_yr":  withdrawal,
        "water_consumption_ml_yr": consumption,
        "water_discharge_ml_yr":   discharge,
        "water_stressed_ops_pct":  stressed,
        "recycled_water_pct":      recycled,
    })

    # ---- CDP Water Security ----
    cdp_gov  = request_data.get("cdp_governance_score")  or _seed_float(eid, "cdp_g", 0.38, 0.96)
    cdp_risk = request_data.get("cdp_risk_score")        or _seed_float(eid, "cdp_r", 0.38, 0.96)
    cdp_tgt  = request_data.get("cdp_targets_score")     or _seed_float(eid, "cdp_t", 0.28, 0.92)
    cdp_perf = request_data.get("cdp_performance_score") or _seed_float(eid, "cdp_p", 0.32, 0.92)
    verified = bool(request_data.get("cdp_data_verified", False))

    cdp_composite = cdp_gov * 0.25 + cdp_risk * 0.25 + cdp_tgt * 0.25 + cdp_perf * 0.25
    if verified:
        cdp_composite = min(cdp_composite * 1.04, 1.0)
    cdp_grade_str  = _cdp_grade(cdp_composite)
    cdp_a_eligible = cdp_grade_str in ("A", "A-")

    # ---- AWS Standard v2.0 ----
    aws_wb  = request_data.get("aws_water_balance_score")     or _seed_float(eid, "aws_wb", 0.38, 0.96)
    aws_gov = request_data.get("aws_governance_score")        or _seed_float(eid, "aws_gv", 0.38, 0.96)
    aws_sws = request_data.get("aws_site_water_status_score") or _seed_float(eid, "aws_sw", 0.38, 0.92)
    aws_eng = request_data.get("aws_engagement_score")        or _seed_float(eid, "aws_en", 0.30, 0.92)
    aws_out = request_data.get("aws_site_outcomes_score")     or _seed_float(eid, "aws_so", 0.30, 0.92)

    aws_overall = (aws_wb + aws_gov + aws_sws + aws_eng + aws_out) / 5.0
    aws_pct     = round(aws_overall * 100.0, 1)

    if aws_pct >= 90:
        aws_cert = "platinum"
    elif aws_pct >= 75:
        aws_cert = "gold"
    elif aws_pct >= 60:
        aws_cert = "core"
    else:
        aws_cert = "none"
    aws_eligible = aws_cert != "none"

    # ---- CEO Water Mandate ----
    cwm_committed = bool(request_data.get("cwm_committed", False))
    cwm_scores    = request_data.get("cwm_commitment_scores") or {}

    if cwm_committed:
        cwm_stewardship = round(
            sum(
                cwm_scores.get(k, _seed_float(eid, f"cwm_{k}", 0.48, 0.90)) * v["commitment_weight"]
                for k, v in CEO_WATER_MANDATE.items()
            ),
            3,
        )
        cwm_targets_set = cwm_scores.get("direct_operations", _seed_float(eid, "cwm_do", 0.50, 0.90)) >= 0.65
    else:
        cwm_stewardship = round(_seed_float(eid, "cwm_ns", 0.08, 0.38), 3)
        cwm_targets_set = False

    # ---- Financial exposure ----
    assets_m  = float(request_data.get("total_assets_m") or 100.0)
    rev_pct   = float(request_data.get("water_dependent_revenue_pct") or 30.0)
    opex_m    = float(request_data.get("annual_water_opex_m") or round(assets_m * 0.018, 2))

    stress_mult = {"low": 1.10, "medium": 1.50, "high": 2.60, "critical": 4.20}[aq_tier]
    opex_risk_m   = round(opex_m * (stress_mult - 1.0), 2)
    reg_risk_m    = round(assets_m * (rev_pct / 100.0) * 0.032 * stress_mult, 2)
    strand_risk_m = round(assets_m * (rev_pct / 100.0) * 0.048 * (aq_score / 100.0), 2)
    total_fin_m   = round(opex_risk_m + reg_risk_m + strand_risk_m, 2)

    # ---- Water stewardship bond eligibility ----
    cwm_input  = cwm_stewardship if cwm_committed else 0.28
    bond_score = round(
        cdp_composite * 0.30 + aws_overall * 0.30 + cwm_input * 0.20 + (tnfd_score / 100.0) * 0.20,
        3,
    )
    bond_eligible = bond_score >= 0.70

    # ---- Overall water risk score (physical risk net of governance strength) ----
    governance_bonus = round((cdp_composite * 0.50 + aws_overall * 0.50) * 22.0, 2)
    risk_score = round(min(max(aq_score - governance_bonus, 0.0), 100.0), 1)
    risk_tier  = _tier(risk_score)

    # ---- Findings and recommendations ----
    findings: List[str] = []
    recs:     List[str] = []

    if aq_tier in ("high", "critical"):
        findings.append(f"WRI AQUEDUCT 4.0 composite {aq_score}/100 — {aq_tier.upper()} physical water stress in operating basin.")
        recs.append("Develop basin-level water stewardship plan aligned with AWS Standard v2.0 within 12 months.")
    if stressed > 50.0:
        findings.append(f"{stressed:.1f}% of operations located in AQUEDUCT high/extremely high stress zones — above 50% materiality threshold.")
        recs.append("Set location-specific reduction targets for water-stressed facilities per SBTN Corporate Water Targets v1.0.")
    if not cdp_a_eligible:
        findings.append(f"CDP Water grade '{cdp_grade_str}' (composite {cdp_composite:.2f}) — A-List threshold (>=0.80) not achieved.")
        recs.append("Strengthen CDP governance pillar (W1) and adopt SBTN-aligned science-based targets (W4) for A-List eligibility.")
    if not aws_eligible:
        findings.append(f"AWS Standard v2.0 overall score {aws_pct:.1f}% — below AWS Core certification threshold (60%).")
        recs.append("Prioritise AWS engagement and site outcomes pillars to reach Core certification (>=60%) within 18 months.")
    if not cwm_committed:
        findings.append("Entity has not formally committed to the CEO Water Mandate (UN Global Compact).")
        recs.append("Formal CEO Water Mandate commitment unlocks Water Action Hub collective catchment initiatives and peer benchmarking.")
    if recycled < 15.0:
        findings.append(f"Water recycling rate {recycled:.1f}% — below sector best-practice benchmark (>=20%).")
        recs.append("Invest in closed-loop water systems to increase recycling rate to >=20% and reduce withdrawal intensity.")
    if bond_eligible:
        findings.append(f"Water stewardship bond framework score {bond_score:.2f} — eligible for ICMA Green Bond issuance (Water UoP category).")
    else:
        findings.append(f"Water bond framework score {bond_score:.2f} — below eligibility threshold (0.70).")
        recs.append("Improve CDP composite and AWS certification level to reach water stewardship bond eligibility (score >= 0.70).")

    return WaterRiskResult(
        entity_id=eid,
        entity_name=ename,
        sector=sector,
        basin_name=basin,
        aqueduct_indicator_scores=aq_scores,
        aqueduct_overall_score=aq_score,
        aqueduct_risk_tier=aq_tier,
        water_withdrawal_ml_yr=round(withdrawal, 1),
        water_consumption_ml_yr=round(consumption, 1),
        water_discharge_ml_yr=round(discharge, 1),
        recycled_pct=round(recycled, 1),
        water_stressed_area_pct=round(stressed, 1),
        tnfd_water_disclosure_score=round(tnfd_score, 1),
        cdp_governance_score=round(cdp_gov, 3),
        cdp_risk_score=round(cdp_risk, 3),
        cdp_targets_score=round(cdp_tgt, 3),
        cdp_performance_score=round(cdp_perf, 3),
        cdp_composite_score=round(cdp_composite, 3),
        cdp_grade=cdp_grade_str,
        cdp_a_list_eligible=cdp_a_eligible,
        aws_water_balance_score=round(aws_wb, 3),
        aws_governance_score=round(aws_gov, 3),
        aws_site_water_status_score=round(aws_sws, 3),
        aws_engagement_score=round(aws_eng, 3),
        aws_site_outcomes_score=round(aws_out, 3),
        aws_overall_score=aws_pct,
        aws_certification_level=aws_cert,
        aws_certification_eligible=aws_eligible,
        cwm_committed=cwm_committed,
        cwm_targets_set=cwm_targets_set,
        cwm_stewardship_score=cwm_stewardship,
        water_opex_risk_m=opex_risk_m,
        water_regulatory_risk_m=reg_risk_m,
        water_stranded_asset_risk_m=strand_risk_m,
        total_water_financial_risk_m=total_fin_m,
        water_bond_eligible=bond_eligible,
        water_bond_framework_score=bond_score,
        water_risk_score=risk_score,
        water_risk_tier=risk_tier,
        key_findings=findings,
        recommendations=recs,
        standards_applied=[
            "WRI AQUEDUCT 4.0 (2023)",
            "CDP Water Security A-List Criteria 2024",
            "TNFD E3 Water and Marine Metrics v1.0 (2023)",
            "Alliance for Water Stewardship (AWS) Standard v2.0 (2022)",
            "CEO Water Mandate — UN Global Compact",
            "SBTN Corporate Water Targets v1.0 (2023)",
            "GRI 303: Water and Effluents 2018",
            "ICMA Green Bond Principles 2021 — Water UoP Category",
            "EU Taxonomy Objective 3 — Sustainable Water Use (Regulation EU 2020/852)",
            "UN SDG 6 — Clean Water and Sanitation",
        ],
    )


def create_stewardship_target(request_data: Dict) -> StewardshipTargetResult:
    """
    Create and validate a water stewardship target against SBTN, CDP, and AWS criteria.
    Returns StewardshipTargetResult dataclass.
    """
    eid          = request_data.get("entity_id", "unknown")
    ename        = request_data.get("entity_name", "Unknown Entity")
    ttype        = request_data.get("target_type", "withdrawal_reduction")
    base_yr      = int(request_data.get("baseline_year") or 2022)
    tgt_yr       = int(request_data.get("target_year") or 2030)
    base_ml      = float(request_data.get("baseline_withdrawal_ml_yr") or 500.0)
    red_pct      = float(request_data.get("target_reduction_pct") or 25.0)
    stressed_pct = float(request_data.get("water_stressed_ops_pct") or 40.0)
    sbtn         = bool(request_data.get("sbtn_aligned", False))
    verified     = bool(request_data.get("third_party_verified", False))

    years     = max(tgt_yr - base_yr, 1)
    target_ml = round(base_ml * (1.0 - red_pct / 100.0), 1)
    annual_ml = round((base_ml - target_ml) / years, 1)
    cagr      = round((1.0 - (target_ml / base_ml) ** (1.0 / years)) * 100.0, 2)

    # CDP target quality scoring (0-1)
    tq = 0.0
    if red_pct >= 25.0:
        tq += 0.30
    elif red_pct >= 15.0:
        tq += 0.18
    elif red_pct >= 10.0:
        tq += 0.10
    if tgt_yr <= 2030:
        tq += 0.25
    elif tgt_yr <= 2035:
        tq += 0.12
    if sbtn:
        tq += 0.25
    if stressed_pct >= 30.0:
        tq += 0.20
    if verified:
        tq = min(tq * 1.05, 1.0)
    tq = round(min(tq, 1.0), 3)

    aws_compat = red_pct >= 15.0 and tgt_yr <= 2035

    if tq >= 0.80:
        validity = "High quality — CDP A-List target criteria met; SBTN-aligned and timebound to 2030 or earlier."
    elif tq >= 0.60:
        validity = "Medium quality — additional ambition or science-based calibration recommended for A-List."
    else:
        validity = "Low quality — target lacks sufficient ambition, near-term timeframe, or water-stressed context."

    recs: List[str] = []
    if not sbtn:
        recs.append("Align target with SBTN Corporate Water Targets v1.0 guidance for science-based credibility (CDP A-List requirement).")
    if red_pct < 20.0:
        recs.append("Increase reduction ambition to >= 20% (25% preferred) to meet CDP A-List target quality scoring.")
    if tgt_yr > 2030:
        recs.append("Advance target date to 2030 to align with SDG 6.4 deadline and CDP A-List assessment criteria.")
    if stressed_pct < 50.0:
        recs.append("Define separate location-specific targets for water-stressed facilities per AWS site outcomes pillar.")
    if not verified:
        recs.append("Commission third-party verification of baseline and interim progress data for CDP performance sub-score uplift.")

    return StewardshipTargetResult(
        entity_id=eid,
        entity_name=ename,
        target_type=ttype,
        baseline_year=base_yr,
        target_year=tgt_yr,
        baseline_withdrawal_ml_yr=base_ml,
        target_reduction_pct=red_pct,
        target_withdrawal_ml_yr=target_ml,
        annual_reduction_ml_yr=annual_ml,
        cagr_pct=cagr,
        sbtn_aligned=sbtn,
        aws_target_compatible=aws_compat,
        cdp_target_quality_score=tq,
        sdg_6_contribution="SDG 6.4 — Substantially increase water-use efficiency across all sectors and ensure sustainable withdrawals by 2030",
        target_validity_assessment=validity,
        recommendations=recs,
    )


def get_benchmark_data() -> Dict[str, Any]:
    """Return all reference data: AQUEDUCT basins, CDP criteria, TNFD E3, AWS, CEO WM, bond framework."""
    return {
        "aqueduct_basin_benchmarks": AQUEDUCT_BASIN_BENCHMARKS,
        "aqueduct_indicator_definitions": AQUEDUCT_INDICATORS,
        "aqueduct_risk_tiers": AQUEDUCT_RISK_TIERS,
        "cdp_water_criteria": CDP_WATER_CRITERIA,
        "cdp_grade_thresholds": CDP_GRADE_THRESHOLDS,
        "tnfd_e3_metrics": TNFD_E3_METRICS,
        "aws_standard_v2_criteria": AWS_STANDARD_v2,
        "aws_certification_tiers": AWS_CERTIFICATION_TIERS,
        "ceo_water_mandate_pillars": CEO_WATER_MANDATE,
        "water_bond_framework": WATER_BOND_FRAMEWORK,
    }
