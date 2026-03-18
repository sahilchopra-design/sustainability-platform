"""
Adaptation Finance & Resilience Economics Engine — E83
=======================================================
Covers the full investment appraisal, taxonomy alignment and resilience-
economics methodology for climate adaptation finance, referencing:

  - GFMA Adaptation Finance Framework (Green Finance for Adaptation, 2022)
  - GARI (Global Adaptation & Resilience Investment Framework) — Climate Policy
    Initiative / Global Adaptation Commission, 2023
  - UNFCCC National Adaptation Plans (NAP) — COP29 NAP workstream
  - NDC adaptation components — Paris Agreement Art 7; UNFCCC synthesis 2024
  - GCF (Green Climate Fund) — Accreditation Master Agreement terms
  - GEF (Global Environment Facility) — GEF-8 programming directions
  - ADB, AIIB, IDB, EIB, AFD, World Bank — climate finance eligibility criteria
  - IPCC AR6 WG2 — Physical risk projections by RCP/SSP scenario
  - ISO 14091:2021 — Adaptation to climate change (vulnerability/risk assessment)
  - ISO 14093:2022 — Mechanism for financing local adaptation
  - Benefit-Cost Analysis (HM Treasury Green Book 2022; EU JASPERS methodology)

Sub-modules:
  1. GFMA Alignment          — adaptation taxonomy category scoring
  2. Resilience Delta         — physical risk reduction quantification
  3. GARI Scoring             — 6-criteria investment quality assessment
  4. Adaptation NPV           — BCR, NPV, SROI, cost per beneficiary
  5. MDB Eligibility          — GCF, GEF, multilateral facility matching
  6. NAP/NDC Alignment        — national adaptation plan linkage
  7. Full Assessment          — composite adaptation_score + bankability_tier
  8. Portfolio Aggregation    — portfolio-level adaptation metrics
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 1. GFMA Adaptation Categories — 8 categories
# ---------------------------------------------------------------------------

GFMA_ADAPTATION_CATEGORIES: Dict[str, Dict[str, Any]] = {
    "water_infrastructure": {
        "gfma_code": "WI",
        "description": "Drought-resilient water supply, desalination, catchment restoration, WASH",
        "taxonomy_alignment": "EU Taxonomy — Climate Adaptation (Objective 2); ICMA GBP Use of Proceeds",
        "typical_bcr_range": [3.5, 8.0],
        "co_benefits": [
            "food security",
            "public health",
            "ecosystem services",
            "economic productivity",
        ],
        "primary_hazards": ["drought", "water_scarcity", "flooding"],
        "sdg_alignment": ["SDG 6", "SDG 3", "SDG 2"],
        "gfma_ref": "GFMA Adaptation Finance Framework Section 3.1",
    },
    "coastal_protection": {
        "gfma_code": "CP",
        "description": "Sea walls, mangrove restoration, coral reef protection, managed retreat",
        "taxonomy_alignment": "EU Taxonomy Annex II Delegated Act; GCF B.31 Result Areas",
        "typical_bcr_range": [4.0, 11.0],
        "co_benefits": [
            "biodiversity",
            "fisheries",
            "tourism",
            "carbon sequestration",
        ],
        "primary_hazards": ["sea_level_rise", "storm_surge", "coastal_flooding"],
        "sdg_alignment": ["SDG 14", "SDG 11", "SDG 13"],
        "gfma_ref": "GFMA Adaptation Finance Framework Section 3.2",
    },
    "agriculture_resilience": {
        "gfma_code": "AR",
        "description": "Climate-smart agriculture, drought-tolerant varieties, irrigation efficiency",
        "taxonomy_alignment": "EU Taxonomy — Sustainable Agriculture; GARI Pillar 1",
        "typical_bcr_range": [2.5, 6.5],
        "co_benefits": [
            "food security",
            "smallholder livelihoods",
            "soil carbon",
            "biodiversity",
        ],
        "primary_hazards": ["drought", "heat_stress", "flooding", "pest_disease"],
        "sdg_alignment": ["SDG 2", "SDG 1", "SDG 15"],
        "gfma_ref": "GFMA Adaptation Finance Framework Section 3.3",
    },
    "urban_heat_resilience": {
        "gfma_code": "UH",
        "description": "Urban greening, cool roofs, green corridors, early warning systems",
        "taxonomy_alignment": "EU Taxonomy Annex II; C40 Cities Finance Facility criteria",
        "typical_bcr_range": [2.0, 5.0],
        "co_benefits": [
            "public health",
            "energy savings",
            "air quality",
            "biodiversity",
        ],
        "primary_hazards": ["heat_waves", "urban_heat_island"],
        "sdg_alignment": ["SDG 11", "SDG 3", "SDG 13"],
        "gfma_ref": "GFMA Adaptation Finance Framework Section 3.4",
    },
    "health_systems": {
        "gfma_code": "HS",
        "description": "Climate-resilient hospitals, disease surveillance, heat-health action plans",
        "taxonomy_alignment": "GARI Pillar 2; GCF B.17 Result Areas",
        "typical_bcr_range": [3.0, 7.0],
        "co_benefits": [
            "pandemic preparedness",
            "workforce productivity",
            "gender equity",
        ],
        "primary_hazards": ["heat_waves", "flooding", "vector_borne_disease"],
        "sdg_alignment": ["SDG 3", "SDG 1", "SDG 10"],
        "gfma_ref": "GFMA Adaptation Finance Framework Section 3.5",
    },
    "transport_infrastructure": {
        "gfma_code": "TI",
        "description": "Climate-resilient roads, bridges, ports, rail — flood/heat proofing",
        "taxonomy_alignment": "EU Taxonomy — Transport (climate adaptation screening); MDB CCAP",
        "typical_bcr_range": [2.0, 4.5],
        "co_benefits": [
            "trade connectivity",
            "disaster risk reduction",
            "rural access",
        ],
        "primary_hazards": ["flooding", "heat_stress", "permafrost_thaw"],
        "sdg_alignment": ["SDG 9", "SDG 11", "SDG 17"],
        "gfma_ref": "GFMA Adaptation Finance Framework Section 3.6",
    },
    "energy_resilience": {
        "gfma_code": "ER",
        "description": "Grid hardening, microgrids, climate-resilient energy infrastructure",
        "taxonomy_alignment": "EU Taxonomy — Energy (climate adaptation); GCF B.07",
        "typical_bcr_range": [2.5, 6.0],
        "co_benefits": [
            "energy security",
            "economic development",
            "disaster recovery",
        ],
        "primary_hazards": ["flooding", "heat_stress", "extreme_wind", "wildfire"],
        "sdg_alignment": ["SDG 7", "SDG 9", "SDG 13"],
        "gfma_ref": "GFMA Adaptation Finance Framework Section 3.7",
    },
    "nature_based_solutions": {
        "gfma_code": "NbS",
        "description": "Ecosystem-based adaptation: wetlands, forests, floodplains, green infrastructure",
        "taxonomy_alignment": "EU Taxonomy Objective 6 (Biodiversity); TNFD LEAP; GBF Target 8",
        "typical_bcr_range": [5.0, 15.0],
        "co_benefits": [
            "carbon sequestration",
            "biodiversity",
            "water regulation",
            "food security",
            "cultural services",
        ],
        "primary_hazards": ["flooding", "drought", "coastal_flooding", "heat_waves"],
        "sdg_alignment": ["SDG 13", "SDG 15", "SDG 6", "SDG 14"],
        "gfma_ref": "GFMA Adaptation Finance Framework Section 3.8",
    },
}

# ---------------------------------------------------------------------------
# 2. GARI Scoring Criteria — 6 criteria + weights
# ---------------------------------------------------------------------------

GARI_SCORING_CRITERIA: Dict[str, Dict[str, Any]] = {
    "additionality": {
        "weight": 0.20,
        "description": "Does the project address a risk not covered by baseline/BAU investment?",
        "sub_criteria": ["counterfactual baseline established", "market failure addressed", "public good element"],
        "gari_ref": "GARI Framework Criterion 1 — Additionality",
    },
    "effectiveness": {
        "weight": 0.25,
        "description": "Measurable reduction in climate risk exposure / vulnerability",
        "sub_criteria": [
            "quantified risk reduction metric",
            "beneficiary count",
            "monitoring and evaluation plan",
            "time to impact",
        ],
        "gari_ref": "GARI Framework Criterion 2 — Effectiveness",
    },
    "sustainability": {
        "weight": 0.15,
        "description": "Long-term maintenance funding, institutional capacity, political durability",
        "sub_criteria": ["O&M funding secured", "local ownership", "regulatory anchoring"],
        "gari_ref": "GARI Framework Criterion 3 — Sustainability",
    },
    "scalability": {
        "weight": 0.15,
        "description": "Potential for replication, scale-up, systemic change",
        "sub_criteria": ["replication potential", "enabling environment created", "private capital catalysed"],
        "gari_ref": "GARI Framework Criterion 4 — Scalability",
    },
    "co_benefits": {
        "weight": 0.15,
        "description": "Non-climate co-benefits: biodiversity, health, gender, poverty reduction",
        "sub_criteria": ["biodiversity positive", "gender-responsive", "economic co-benefits", "health co-benefits"],
        "gari_ref": "GARI Framework Criterion 5 — Co-benefits",
    },
    "governance": {
        "weight": 0.10,
        "description": "Sound governance, stakeholder engagement, fiduciary standards",
        "sub_criteria": ["stakeholder consultation", "grievance mechanism", "anti-corruption policy", "transparency"],
        "gari_ref": "GARI Framework Criterion 6 — Governance",
    },
}

# ---------------------------------------------------------------------------
# 3. Hazard Risk Reduction Profiles — 10 hazards
# ---------------------------------------------------------------------------

HAZARD_RISK_REDUCTION_PROFILES: Dict[str, Dict[str, Any]] = {
    "flooding": {
        "risk_reduction_by_measure": {
            "dyke_levee": 0.70, "floodplain_restoration": 0.40,
            "early_warning_system": 0.30, "drainage_improvement": 0.50,
            "building_elevation": 0.60, "mangrove_restoration": 0.35,
        },
        "time_horizon_years": 30,
        "residual_risk_floor": 0.05,
        "aar_percent_gdp": {"LIC": 0.8, "LMIC": 0.5, "UMIC": 0.3, "HIC": 0.15},
    },
    "drought": {
        "risk_reduction_by_measure": {
            "water_storage": 0.55, "irrigation_efficiency": 0.40,
            "drought_tolerant_crops": 0.30, "groundwater_recharge": 0.45,
            "desalination": 0.60, "demand_management": 0.25,
        },
        "time_horizon_years": 25,
        "residual_risk_floor": 0.08,
        "aar_percent_gdp": {"LIC": 1.2, "LMIC": 0.7, "UMIC": 0.4, "HIC": 0.2},
    },
    "sea_level_rise": {
        "risk_reduction_by_measure": {
            "sea_wall": 0.75, "beach_nourishment": 0.35,
            "mangrove_restoration": 0.40, "coral_reef_restoration": 0.30,
            "managed_retreat": 0.90, "surge_barrier": 0.80,
        },
        "time_horizon_years": 50,
        "residual_risk_floor": 0.03,
        "aar_percent_gdp": {"LIC": 2.0, "LMIC": 1.2, "UMIC": 0.6, "HIC": 0.3},
    },
    "heat_waves": {
        "risk_reduction_by_measure": {
            "cool_roofs": 0.35, "urban_greening": 0.40,
            "early_warning_system": 0.50, "cool_centres": 0.45,
            "building_codes_update": 0.30, "green_corridors": 0.35,
        },
        "time_horizon_years": 20,
        "residual_risk_floor": 0.10,
        "aar_percent_gdp": {"LIC": 0.6, "LMIC": 0.4, "UMIC": 0.2, "HIC": 0.1},
    },
    "storm_surge": {
        "risk_reduction_by_measure": {
            "coastal_defences": 0.65, "mangrove_restoration": 0.40,
            "early_warning_system": 0.55, "building_codes": 0.35,
            "managed_retreat": 0.80,
        },
        "time_horizon_years": 30,
        "residual_risk_floor": 0.05,
        "aar_percent_gdp": {"LIC": 1.5, "LMIC": 0.9, "UMIC": 0.5, "HIC": 0.25},
    },
    "tropical_cyclone": {
        "risk_reduction_by_measure": {
            "early_warning_system": 0.60, "building_codes": 0.40,
            "mangrove_restoration": 0.30, "shelter_construction": 0.50,
            "infrastructure_hardening": 0.45,
        },
        "time_horizon_years": 30,
        "residual_risk_floor": 0.08,
        "aar_percent_gdp": {"LIC": 2.5, "LMIC": 1.5, "UMIC": 0.8, "HIC": 0.4},
    },
    "wildfire": {
        "risk_reduction_by_measure": {
            "firebreak_creation": 0.45, "controlled_burning": 0.40,
            "early_warning_system": 0.50, "vegetation_management": 0.35,
            "building_codes": 0.30,
        },
        "time_horizon_years": 20,
        "residual_risk_floor": 0.10,
        "aar_percent_gdp": {"LIC": 0.5, "LMIC": 0.3, "UMIC": 0.2, "HIC": 0.1},
    },
    "permafrost_thaw": {
        "risk_reduction_by_measure": {
            "foundation_redesign": 0.70, "thermosyphon_installation": 0.65,
            "infrastructure_relocation": 0.85, "monitoring_systems": 0.20,
        },
        "time_horizon_years": 40,
        "residual_risk_floor": 0.15,
        "aar_percent_gdp": {"LIC": 0.3, "LMIC": 0.2, "UMIC": 0.4, "HIC": 0.5},
    },
    "vector_borne_disease": {
        "risk_reduction_by_measure": {
            "surveillance_strengthening": 0.45, "habitat_management": 0.30,
            "early_warning_system": 0.50, "health_system_capacity": 0.55,
            "community_education": 0.25,
        },
        "time_horizon_years": 15,
        "residual_risk_floor": 0.12,
        "aar_percent_gdp": {"LIC": 1.0, "LMIC": 0.6, "UMIC": 0.3, "HIC": 0.1},
    },
    "water_scarcity": {
        "risk_reduction_by_measure": {
            "aquifer_recharge": 0.50, "water_recycling": 0.60,
            "demand_management": 0.35, "desalination": 0.65,
            "ecosystem_restoration": 0.40,
        },
        "time_horizon_years": 30,
        "residual_risk_floor": 0.06,
        "aar_percent_gdp": {"LIC": 1.5, "LMIC": 0.8, "UMIC": 0.4, "HIC": 0.2},
    },
}

# ---------------------------------------------------------------------------
# 4. MDB Climate Finance Facilities — 8 facilities
# ---------------------------------------------------------------------------

MDB_CLIMATE_FACILITIES: Dict[str, Dict[str, Any]] = {
    "GCF": {
        "name": "Green Climate Fund",
        "url_ref": "https://www.greenclimate.fund",
        "min_project_size_m": 10.0,
        "eligible_countries": "UNFCCC developing country Parties",
        "max_grant_pct": 50,
        "concessional_loan_available": True,
        "eligibility_criteria": [
            "UNFCCC developing country party",
            "National designated authority (NDA) endorsement",
            "Adaptation or mitigation focus per Paris Agreement Art 9",
            "Results-based management framework",
            "Paradigm shift potential",
        ],
        "focus_areas": ["adaptation", "mitigation", "cross-cutting"],
        "result_areas": ["B.09 — Increased resilience of infrastructure", "B.17 — Health systems", "B.31 — Coastal"],
        "typical_grant_pct_adaptation": 60,
    },
    "GEF": {
        "name": "Global Environment Facility",
        "url_ref": "https://www.thegef.org",
        "min_project_size_m": 1.0,
        "eligible_countries": "GEF recipient countries (143)",
        "max_grant_pct": 100,
        "concessional_loan_available": False,
        "eligibility_criteria": [
            "GEF recipient country",
            "Operational focal point endorsement",
            "Global environmental benefit",
            "Incrementality principle",
        ],
        "focus_areas": ["biodiversity", "climate adaptation", "land degradation", "chemicals"],
        "result_areas": ["Adaptation", "Integrated programmes"],
        "typical_grant_pct_adaptation": 100,
    },
    "AIIB": {
        "name": "Asian Infrastructure Investment Bank",
        "url_ref": "https://www.aiib.org",
        "min_project_size_m": 50.0,
        "eligible_countries": "AIIB members (109 approved)",
        "max_grant_pct": 0,
        "concessional_loan_available": True,
        "eligibility_criteria": [
            "AIIB member country",
            "Sovereign or non-sovereign borrower",
            "Climate-proofed project design (climate risk screening required)",
            "Environmental and social framework compliance",
        ],
        "focus_areas": ["infrastructure", "energy", "urban", "rural development"],
        "result_areas": ["Climate adaptation", "Green infrastructure"],
        "typical_grant_pct_adaptation": 0,
    },
    "ADB": {
        "name": "Asian Development Bank",
        "url_ref": "https://www.adb.org",
        "min_project_size_m": 10.0,
        "eligible_countries": "ADB developing member countries",
        "max_grant_pct": 30,
        "concessional_loan_available": True,
        "eligibility_criteria": [
            "ADB developing member country",
            "ADB safeguards compliance (SPS 2009)",
            "ADB Climate Risk and Vulnerability Assessment",
            "ADF or OCR window eligibility",
        ],
        "focus_areas": ["infrastructure", "agriculture", "health", "water"],
        "result_areas": ["Climate change", "Disaster risk reduction"],
        "typical_grant_pct_adaptation": 25,
    },
    "IADB": {
        "name": "Inter-American Development Bank",
        "url_ref": "https://www.iadb.org",
        "min_project_size_m": 5.0,
        "eligible_countries": "IDB borrowing member countries (26 LAC)",
        "max_grant_pct": 20,
        "concessional_loan_available": True,
        "eligibility_criteria": [
            "IDB borrowing member country",
            "Environmental and social policy compliance",
            "Climate change and disaster risk lens",
        ],
        "focus_areas": ["climate change", "resilience", "urban", "agriculture"],
        "result_areas": ["Climate resilience", "DRM"],
        "typical_grant_pct_adaptation": 15,
    },
    "EIB": {
        "name": "European Investment Bank",
        "url_ref": "https://www.eib.org",
        "min_project_size_m": 25.0,
        "eligible_countries": "EU member states + partner countries",
        "max_grant_pct": 0,
        "concessional_loan_available": True,
        "eligibility_criteria": [
            "EU or EIB partner country",
            "EU Taxonomy climate adaptation alignment screening",
            "ESRS E1 climate risk assessment",
            "EIB environmental and social standards",
        ],
        "focus_areas": ["infrastructure", "urban", "NbS", "agriculture"],
        "result_areas": ["Climate adaptation", "Biodiversity"],
        "typical_grant_pct_adaptation": 0,
    },
    "AFD": {
        "name": "Agence Française de Développement",
        "url_ref": "https://www.afd.fr",
        "min_project_size_m": 5.0,
        "eligible_countries": "AFD partner countries (150+)",
        "max_grant_pct": 40,
        "concessional_loan_available": True,
        "eligibility_criteria": [
            "AFD partner country",
            "French ODA eligibility",
            "Climate co-benefits mandatory screening",
            "Gender and social inclusion indicators",
        ],
        "focus_areas": ["water", "urban", "agriculture", "health"],
        "result_areas": ["Resilience", "NbS", "WASH"],
        "typical_grant_pct_adaptation": 35,
    },
    "World_Bank": {
        "name": "World Bank Group (IBRD/IDA/IFC)",
        "url_ref": "https://www.worldbank.org",
        "min_project_size_m": 5.0,
        "eligible_countries": "World Bank borrowing member countries",
        "max_grant_pct": 100,  # IDA grants for LICs
        "concessional_loan_available": True,
        "eligibility_criteria": [
            "World Bank member country",
            "World Bank Environmental and Social Framework (ESF 2017)",
            "Climate co-benefits tagging (CPIA climate marker)",
            "World Bank Group climate adaptation principles",
        ],
        "focus_areas": ["cross-sectoral", "urban", "water", "agriculture", "DRM"],
        "result_areas": ["Adaptation", "Resilience", "DRM"],
        "typical_grant_pct_adaptation": 40,
    },
}

# ---------------------------------------------------------------------------
# 5. NAP Country Profiles — 30 developing countries
# ---------------------------------------------------------------------------

NAP_COUNTRY_PROFILES: Dict[str, Dict[str, Any]] = {
    "BD": {"name": "Bangladesh",   "nap_status": "Submitted",    "nap_year": 2023, "priority_sectors": ["water", "agriculture", "coastal", "health", "urban"], "ndc_adaptation": "Comprehensive", "adaptation_ambition_score": 82},
    "ET": {"name": "Ethiopia",     "nap_status": "Submitted",    "nap_year": 2022, "priority_sectors": ["agriculture", "water", "health", "dryland"], "ndc_adaptation": "Moderate", "adaptation_ambition_score": 68},
    "KE": {"name": "Kenya",        "nap_status": "Submitted",    "nap_year": 2016, "priority_sectors": ["agriculture", "water", "health", "urban", "energy"], "ndc_adaptation": "Comprehensive", "adaptation_ambition_score": 75},
    "NG": {"name": "Nigeria",      "nap_status": "In-Progress",  "nap_year": None, "priority_sectors": ["agriculture", "water", "health", "coastal"], "ndc_adaptation": "Moderate", "adaptation_ambition_score": 55},
    "PH": {"name": "Philippines",  "nap_status": "Submitted",    "nap_year": 2023, "priority_sectors": ["coastal", "agriculture", "health", "water", "DRR"], "ndc_adaptation": "Comprehensive", "adaptation_ambition_score": 80},
    "VN": {"name": "Vietnam",      "nap_status": "Submitted",    "nap_year": 2020, "priority_sectors": ["agriculture", "water", "coastal", "urban"], "ndc_adaptation": "Comprehensive", "adaptation_ambition_score": 78},
    "GH": {"name": "Ghana",        "nap_status": "Submitted",    "nap_year": 2022, "priority_sectors": ["agriculture", "water", "coastal", "health"], "ndc_adaptation": "Moderate", "adaptation_ambition_score": 65},
    "ID": {"name": "Indonesia",    "nap_status": "Submitted",    "nap_year": 2021, "priority_sectors": ["coastal", "agriculture", "water", "urban"], "ndc_adaptation": "Comprehensive", "adaptation_ambition_score": 77},
    "IN": {"name": "India",        "nap_status": "In-Progress",  "nap_year": None, "priority_sectors": ["water", "agriculture", "urban", "coastal", "health"], "ndc_adaptation": "Comprehensive", "adaptation_ambition_score": 72},
    "MX": {"name": "Mexico",       "nap_status": "Submitted",    "nap_year": 2018, "priority_sectors": ["water", "agriculture", "coastal", "urban", "health"], "ndc_adaptation": "Moderate", "adaptation_ambition_score": 65},
    "MA": {"name": "Morocco",      "nap_status": "Submitted",    "nap_year": 2022, "priority_sectors": ["water", "agriculture", "coastal", "urban"], "ndc_adaptation": "Comprehensive", "adaptation_ambition_score": 73},
    "TZ": {"name": "Tanzania",     "nap_status": "Submitted",    "nap_year": 2021, "priority_sectors": ["agriculture", "water", "health", "coastal"], "ndc_adaptation": "Moderate", "adaptation_ambition_score": 60},
    "PE": {"name": "Peru",         "nap_status": "Submitted",    "nap_year": 2021, "priority_sectors": ["water", "agriculture", "coastal", "health", "mountain"], "ndc_adaptation": "Comprehensive", "adaptation_ambition_score": 76},
    "SD": {"name": "Sudan",        "nap_status": "In-Progress",  "nap_year": None, "priority_sectors": ["agriculture", "water", "health", "dryland"], "ndc_adaptation": "Limited", "adaptation_ambition_score": 42},
    "MZ": {"name": "Mozambique",   "nap_status": "Submitted",    "nap_year": 2016, "priority_sectors": ["coastal", "agriculture", "water", "health"], "ndc_adaptation": "Moderate", "adaptation_ambition_score": 58},
    "KH": {"name": "Cambodia",     "nap_status": "Submitted",    "nap_year": 2023, "priority_sectors": ["agriculture", "water", "coastal", "health"], "ndc_adaptation": "Comprehensive", "adaptation_ambition_score": 71},
    "BO": {"name": "Bolivia",      "nap_status": "In-Progress",  "nap_year": None, "priority_sectors": ["water", "agriculture", "mountain", "health"], "ndc_adaptation": "Moderate", "adaptation_ambition_score": 55},
    "SN": {"name": "Senegal",      "nap_status": "Submitted",    "nap_year": 2022, "priority_sectors": ["agriculture", "coastal", "water", "health"], "ndc_adaptation": "Comprehensive", "adaptation_ambition_score": 68},
    "UG": {"name": "Uganda",       "nap_status": "Submitted",    "nap_year": 2015, "priority_sectors": ["agriculture", "water", "health", "energy"], "ndc_adaptation": "Moderate", "adaptation_ambition_score": 60},
    "ZM": {"name": "Zambia",       "nap_status": "In-Progress",  "nap_year": None, "priority_sectors": ["agriculture", "water", "health", "energy"], "ndc_adaptation": "Moderate", "adaptation_ambition_score": 52},
    "MW": {"name": "Malawi",       "nap_status": "Submitted",    "nap_year": 2019, "priority_sectors": ["agriculture", "water", "health", "DRR"], "ndc_adaptation": "Moderate", "adaptation_ambition_score": 57},
    "NP": {"name": "Nepal",        "nap_status": "Submitted",    "nap_year": 2021, "priority_sectors": ["water", "agriculture", "mountain", "health", "DRR"], "ndc_adaptation": "Comprehensive", "adaptation_ambition_score": 74},
    "GT": {"name": "Guatemala",    "nap_status": "Submitted",    "nap_year": 2022, "priority_sectors": ["agriculture", "water", "health", "DRR"], "ndc_adaptation": "Moderate", "adaptation_ambition_score": 62},
    "RW": {"name": "Rwanda",       "nap_status": "Submitted",    "nap_year": 2020, "priority_sectors": ["agriculture", "water", "urban", "health"], "ndc_adaptation": "Comprehensive", "adaptation_ambition_score": 72},
    "ML": {"name": "Mali",         "nap_status": "Submitted",    "nap_year": 2019, "priority_sectors": ["agriculture", "water", "dryland", "health"], "ndc_adaptation": "Moderate", "adaptation_ambition_score": 55},
    "ZW": {"name": "Zimbabwe",     "nap_status": "In-Progress",  "nap_year": None, "priority_sectors": ["agriculture", "water", "health", "energy"], "ndc_adaptation": "Limited", "adaptation_ambition_score": 45},
    "HN": {"name": "Honduras",     "nap_status": "Submitted",    "nap_year": 2018, "priority_sectors": ["agriculture", "water", "coastal", "DRR"], "ndc_adaptation": "Moderate", "adaptation_ambition_score": 63},
    "MM": {"name": "Myanmar",      "nap_status": "In-Progress",  "nap_year": None, "priority_sectors": ["agriculture", "coastal", "water", "health"], "ndc_adaptation": "Limited", "adaptation_ambition_score": 48},
    "SO": {"name": "Somalia",      "nap_status": "In-Progress",  "nap_year": None, "priority_sectors": ["dryland", "water", "coastal", "health"], "ndc_adaptation": "Limited", "adaptation_ambition_score": 35},
    "CD": {"name": "DRC",          "nap_status": "In-Progress",  "nap_year": None, "priority_sectors": ["agriculture", "water", "health", "NbS"], "ndc_adaptation": "Limited", "adaptation_ambition_score": 40},
}

# ---------------------------------------------------------------------------
# 6. RCP Hazard Projections — hazard severity by RCP scenario
# ---------------------------------------------------------------------------

RCP_HAZARD_PROJECTIONS: Dict[str, Dict[str, Dict[str, float]]] = {
    "flooding": {
        "1.5C": {"intensity_multiplier": 1.20, "frequency_multiplier": 1.15, "asset_damage_pct_gdp": 0.4},
        "2C":   {"intensity_multiplier": 1.40, "frequency_multiplier": 1.30, "asset_damage_pct_gdp": 0.7},
        "3C":   {"intensity_multiplier": 1.75, "frequency_multiplier": 1.65, "asset_damage_pct_gdp": 1.4},
        "4C":   {"intensity_multiplier": 2.20, "frequency_multiplier": 2.10, "asset_damage_pct_gdp": 2.6},
    },
    "drought": {
        "1.5C": {"intensity_multiplier": 1.15, "frequency_multiplier": 1.10, "asset_damage_pct_gdp": 0.5},
        "2C":   {"intensity_multiplier": 1.35, "frequency_multiplier": 1.25, "asset_damage_pct_gdp": 0.9},
        "3C":   {"intensity_multiplier": 1.80, "frequency_multiplier": 1.70, "asset_damage_pct_gdp": 2.0},
        "4C":   {"intensity_multiplier": 2.50, "frequency_multiplier": 2.40, "asset_damage_pct_gdp": 4.0},
    },
    "sea_level_rise": {
        "1.5C": {"intensity_multiplier": 1.10, "frequency_multiplier": 1.05, "asset_damage_pct_gdp": 0.3},
        "2C":   {"intensity_multiplier": 1.30, "frequency_multiplier": 1.20, "asset_damage_pct_gdp": 0.6},
        "3C":   {"intensity_multiplier": 1.70, "frequency_multiplier": 1.60, "asset_damage_pct_gdp": 1.5},
        "4C":   {"intensity_multiplier": 2.40, "frequency_multiplier": 2.30, "asset_damage_pct_gdp": 3.5},
    },
    "heat_waves": {
        "1.5C": {"intensity_multiplier": 1.50, "frequency_multiplier": 2.00, "asset_damage_pct_gdp": 0.2},
        "2C":   {"intensity_multiplier": 2.00, "frequency_multiplier": 3.00, "asset_damage_pct_gdp": 0.5},
        "3C":   {"intensity_multiplier": 3.00, "frequency_multiplier": 5.00, "asset_damage_pct_gdp": 1.2},
        "4C":   {"intensity_multiplier": 4.50, "frequency_multiplier": 9.00, "asset_damage_pct_gdp": 2.8},
    },
    "_default": {
        "1.5C": {"intensity_multiplier": 1.20, "frequency_multiplier": 1.20, "asset_damage_pct_gdp": 0.4},
        "2C":   {"intensity_multiplier": 1.40, "frequency_multiplier": 1.40, "asset_damage_pct_gdp": 0.8},
        "3C":   {"intensity_multiplier": 1.80, "frequency_multiplier": 1.80, "asset_damage_pct_gdp": 1.8},
        "4C":   {"intensity_multiplier": 2.50, "frequency_multiplier": 2.50, "asset_damage_pct_gdp": 3.5},
    },
}

# ---------------------------------------------------------------------------
# 7. Discount Rates by Context — adaptation project appraisal
# ---------------------------------------------------------------------------

DISCOUNT_RATES_BY_CONTEXT: Dict[str, Dict[str, Any]] = {
    "sovereign_hic": {
        "description": "Sovereign / public sector — High Income Country",
        "rate_pct": 3.5,
        "basis": "HM Treasury Green Book 2022; EU JASPERS methodology",
    },
    "sovereign_umic": {
        "description": "Sovereign / public sector — Upper-Middle Income Country",
        "rate_pct": 5.0,
        "basis": "World Bank discount rate guidance 2022",
    },
    "sovereign_lmic": {
        "description": "Sovereign / public sector — Lower-Middle Income Country",
        "rate_pct": 7.0,
        "basis": "GCF Financial Model guidance",
    },
    "sovereign_lic": {
        "description": "Sovereign / public sector — Low Income Country",
        "rate_pct": 10.0,
        "basis": "GCF/GEF appraisal discount rate for LICs",
    },
    "concessional": {
        "description": "Concessional finance (MDB/DFI blended)",
        "rate_pct": 2.0,
        "basis": "OECD DAC concessional loan terms; GCF floor",
    },
    "commercial": {
        "description": "Commercial / private sector finance",
        "rate_pct": 12.0,
        "basis": "Emerging market private sector hurdle rate",
    },
    "social": {
        "description": "Social discount rate (welfare / CBA appraisals)",
        "rate_pct": 1.5,
        "basis": "Stern Review / Ramsey rule social time preference",
    },
}


# ---------------------------------------------------------------------------
# Engine Class
# ---------------------------------------------------------------------------


class AdaptationFinanceEngine:
    """
    E83 — Adaptation Finance & Resilience Economics Engine.

    All public methods return plain Python dicts mapping to migration 078
    table columns. No external API calls; all calculations are self-contained.
    """

    # ------------------------------------------------------------------
    # 1. GFMA Alignment Assessment
    # ------------------------------------------------------------------

    def assess_gfma_alignment(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess project alignment with the GFMA Adaptation Finance Framework.

        Args:
            project_data: primary_sector (maps to GFMA category), project_description,
                          co_benefits (list), country_code.

        Returns:
            dict with gfma_category, subcategory, alignment_score, co_benefit_mapping,
                 bcr_range, taxonomy_reference.
        """
        sector = project_data.get("primary_sector", "").lower()

        # Map common sector names to GFMA categories
        _sector_map = {
            "water": "water_infrastructure",
            "coastal": "coastal_protection",
            "coast": "coastal_protection",
            "agriculture": "agriculture_resilience",
            "farming": "agriculture_resilience",
            "heat": "urban_heat_resilience",
            "urban": "urban_heat_resilience",
            "health": "health_systems",
            "transport": "transport_infrastructure",
            "road": "transport_infrastructure",
            "energy": "energy_resilience",
            "nature": "nature_based_solutions",
            "nbs": "nature_based_solutions",
            "ecosystem": "nature_based_solutions",
        }

        gfma_key = _sector_map.get(sector, sector)
        cat_data = GFMA_ADAPTATION_CATEGORIES.get(gfma_key)

        if cat_data is None:
            return {
                "gfma_category": None,
                "gfma_code": None,
                "alignment_score": 0,
                "co_benefit_mapping": [],
                "taxonomy_alignment": "Not mapped",
                "bcr_range": None,
                "message": f"Sector '{sector}' not directly mapped to GFMA category — manual classification required",
            }

        # Co-benefit alignment
        provided_co_benefits = [b.lower() for b in project_data.get("co_benefits", [])]
        cat_co_benefits = [b.lower() for b in cat_data["co_benefits"]]
        matched_co_benefits = [b for b in provided_co_benefits if b in cat_co_benefits]

        # Alignment score heuristic
        base_score = 60
        base_score += min(len(matched_co_benefits) * 8, 30)
        description = project_data.get("project_description", "")
        if any(h in description.lower() for h in cat_data["primary_hazards"]):
            base_score += 10
        alignment_score = min(round(base_score), 100)

        return {
            "gfma_category": gfma_key,
            "gfma_code": cat_data["gfma_code"],
            "gfma_description": cat_data["description"],
            "alignment_score": alignment_score,
            "co_benefit_mapping": {
                "provided": provided_co_benefits,
                "category_standard": cat_co_benefits,
                "matched": matched_co_benefits,
                "coverage_pct": round(len(matched_co_benefits) / max(len(cat_co_benefits), 1) * 100, 1),
            },
            "taxonomy_alignment": cat_data["taxonomy_alignment"],
            "bcr_range": cat_data["typical_bcr_range"],
            "primary_hazards": cat_data["primary_hazards"],
            "sdg_alignment": cat_data["sdg_alignment"],
            "gfma_ref": cat_data["gfma_ref"],
            "assessed_at": datetime.utcnow().isoformat(),
        }

    # ------------------------------------------------------------------
    # 2. Resilience Delta
    # ------------------------------------------------------------------

    def calculate_resilience_delta(
        self,
        baseline_risk: float,
        project_data: Dict[str, Any],
        rcp_scenario: str = "2C",
    ) -> Dict[str, Any]:
        """
        Quantify climate risk reduction from an adaptation project.

        Args:
            baseline_risk: current annual average loss or risk score (0-100 or USD M).
            project_data: hazard_type, adaptation_measure, time_horizon_years.
            rcp_scenario: '1.5C', '2C', '3C', '4C'.

        Returns:
            dict with risk_reduction_pct, post_investment_risk, resilience_delta,
                 residual_risk, maladaptation_risk, rcp_hazard_multiplier.
        """
        hazard = project_data.get("hazard_type", "flooding").lower()
        measure = project_data.get("adaptation_measure", "").lower()
        horizon = int(project_data.get("time_horizon_years", 20))

        hazard_profile = HAZARD_RISK_REDUCTION_PROFILES.get(hazard, HAZARD_RISK_REDUCTION_PROFILES["flooding"])
        rcp_data = RCP_HAZARD_PROJECTIONS.get(hazard, RCP_HAZARD_PROJECTIONS["_default"]).get(
            rcp_scenario, {"intensity_multiplier": 1.5, "frequency_multiplier": 1.5, "asset_damage_pct_gdp": 1.0}
        )

        # Closest matching risk reduction factor
        measure_reductions = hazard_profile["risk_reduction_by_measure"]
        matched_rr = 0.0
        for key, rr in measure_reductions.items():
            if key in measure or measure in key:
                matched_rr = rr
                break
        if matched_rr == 0.0 and measure_reductions:
            matched_rr = sum(measure_reductions.values()) / len(measure_reductions)  # average

        # Adjust risk reduction for time horizon decay (10% decay per decade beyond 20y)
        horizon_adj = 1.0 - max(0, (horizon - 20) / 100)
        effective_rr = matched_rr * horizon_adj

        # Maladaptation risk: high if locked-in grey infrastructure in high RCP
        high_rcp = rcp_scenario in ["3C", "4C"]
        grey_infra = any(k in measure for k in ["wall", "levee", "dyke", "dam"])
        maladaptation_risk = "High" if (high_rcp and grey_infra) else ("Medium" if high_rcp else "Low")

        residual_floor = hazard_profile["residual_risk_floor"]
        post_investment_risk = max(baseline_risk * (1 - effective_rr), baseline_risk * residual_floor)
        resilience_delta = baseline_risk - post_investment_risk

        return {
            "hazard_type": hazard,
            "adaptation_measure": measure,
            "rcp_scenario": rcp_scenario,
            "baseline_risk": round(baseline_risk, 2),
            "risk_reduction_pct": round(effective_rr * 100, 1),
            "post_investment_risk": round(post_investment_risk, 2),
            "resilience_delta": round(resilience_delta, 2),
            "residual_risk_floor_pct": round(residual_floor * 100, 1),
            "rcp_intensity_multiplier": rcp_data["intensity_multiplier"],
            "rcp_frequency_multiplier": rcp_data["frequency_multiplier"],
            "rcp_asset_damage_pct_gdp": rcp_data["asset_damage_pct_gdp"],
            "maladaptation_risk": maladaptation_risk,
            "time_horizon_years": horizon,
            "ref": "IPCC AR6 WG2; ISO 14091:2021; HAZARD_RISK_REDUCTION_PROFILES",
            "assessed_at": datetime.utcnow().isoformat(),
        }

    # ------------------------------------------------------------------
    # 3. GARI Scoring
    # ------------------------------------------------------------------

    def score_gari(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score project against 6 GARI (Global Adaptation & Resilience Investment)
        criteria.

        Args:
            project_data: additionality_evidence, effectiveness_data,
                          sustainability_plan, scalability_potential,
                          co_benefits_data, governance_structure
                          (each: 0-100 self-assessment score or text).

        Returns:
            dict with criterion_scores, composite_gari_score, gari_tier,
                 actionable_gaps.
        """
        criterion_inputs = {
            "additionality":  _parse_score(project_data.get("additionality_evidence",  50)),
            "effectiveness":  _parse_score(project_data.get("effectiveness_data",       50)),
            "sustainability": _parse_score(project_data.get("sustainability_plan",      50)),
            "scalability":    _parse_score(project_data.get("scalability_potential",    50)),
            "co_benefits":    _parse_score(project_data.get("co_benefits_data",         50)),
            "governance":     _parse_score(project_data.get("governance_structure",     50)),
        }

        criterion_scores: Dict[str, Dict[str, Any]] = {}
        weighted_total = 0.0
        actionable_gaps: List[str] = []

        for criterion, raw_score in criterion_inputs.items():
            criteria = GARI_SCORING_CRITERIA[criterion]
            score = min(100.0, max(0.0, float(raw_score)))
            weight = criteria["weight"]
            criterion_scores[criterion] = {
                "raw_score": score,
                "weight": weight,
                "weighted_contribution": round(score * weight, 2),
                "sub_criteria": criteria["sub_criteria"],
                "gari_ref": criteria["gari_ref"],
            }
            weighted_total += score * weight
            if score < 60:
                actionable_gaps.append(
                    f"{criterion.capitalize()} (score {score:.0f}/100): "
                    f"Improve — {criteria['description']}"
                )

        composite_gari = round(weighted_total, 1)

        if composite_gari >= 75:
            gari_tier = "Tier 1 — Investment Grade"
        elif composite_gari >= 55:
            gari_tier = "Tier 2 — Near Investment Grade"
        else:
            gari_tier = "Tier 3 — Requires Development"

        return {
            "criterion_scores": criterion_scores,
            "composite_gari_score": composite_gari,
            "gari_tier": gari_tier,
            "actionable_gaps": actionable_gaps,
            "ref": "GARI Framework — Climate Policy Initiative / Global Adaptation Commission 2023",
            "assessed_at": datetime.utcnow().isoformat(),
        }

    # ------------------------------------------------------------------
    # 4. Adaptation NPV / BCR
    # ------------------------------------------------------------------

    def calculate_adaptation_npv(
        self,
        project_data: Dict[str, Any],
        discount_rate: Optional[float] = None,
        horizon_years: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Compute adaptation project NPV, benefit-cost ratio (BCR), SROI,
        and human-welfare metrics.

        Args:
            project_data: total_investment_m, annual_benefits_m, annual_om_m,
                          beneficiaries_count, discount_rate (%), horizon_years.

        Returns:
            dict with npv_m, bcr, sroi, cost_per_beneficiary, lives_protected,
                 payback_years, irr_approx.
        """
        inv = float(project_data.get("total_investment_m", 10))
        ann_ben = float(project_data.get("annual_benefits_m", 2))
        ann_om = float(project_data.get("annual_om_m", 0.2))
        beneficiaries = max(1, int(project_data.get("beneficiaries_count", 10000)))
        dr = discount_rate if discount_rate is not None else float(project_data.get("discount_rate", 7.0))
        n = horizon_years if horizon_years is not None else int(project_data.get("horizon_years", 20))

        dr_dec = dr / 100.0

        # NPV calculation — annuity formula
        if dr_dec == 0:
            pv_benefits = ann_ben * n
            pv_costs = inv + ann_om * n
        else:
            annuity_factor = (1 - (1 + dr_dec) ** -n) / dr_dec
            pv_benefits = ann_ben * annuity_factor
            pv_costs = inv + ann_om * annuity_factor

        npv = round(pv_benefits - pv_costs, 2)
        bcr = round(pv_benefits / pv_costs, 2) if pv_costs > 0 else 0.0

        # SROI = social value created per £ invested
        sroi = round(pv_benefits / inv, 2) if inv > 0 else 0.0

        # Cost per beneficiary (total lifecycle cost / beneficiaries)
        total_lifecycle_cost_m = inv + ann_om * n
        cost_per_beneficiary = round(total_lifecycle_cost_m * 1_000_000 / beneficiaries, 2)

        # Lives protected — rough proxy: 1 per USD 50k for developing country adaptation
        lives_protected = int(pv_benefits * 1_000_000 / 50_000)

        # Payback period (simple)
        net_annual_benefit = ann_ben - ann_om
        payback_years = round(inv / net_annual_benefit, 1) if net_annual_benefit > 0 else 999

        # Approximate IRR (binary search — simplified)
        irr_approx = _approx_irr(inv, ann_ben - ann_om, n)

        return {
            "total_investment_m": inv,
            "annual_benefits_m": ann_ben,
            "annual_om_m": ann_om,
            "discount_rate_pct": dr,
            "horizon_years": n,
            "pv_benefits_m": round(pv_benefits, 2),
            "pv_costs_m": round(pv_costs, 2),
            "npv_m": npv,
            "bcr": bcr,
            "sroi": sroi,
            "beneficiaries_count": beneficiaries,
            "cost_per_beneficiary_usd": cost_per_beneficiary,
            "lives_protected_proxy": lives_protected,
            "payback_years": payback_years,
            "irr_approx_pct": round(irr_approx * 100, 1),
            "viability": "Viable" if bcr >= 1.0 else "Not Viable",
            "ref": "HM Treasury Green Book 2022; EU JASPERS methodology; ISO 14093:2022",
            "assessed_at": datetime.utcnow().isoformat(),
        }

    # ------------------------------------------------------------------
    # 5. MDB Eligibility Assessment
    # ------------------------------------------------------------------

    def assess_mdb_eligibility(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess project eligibility across 8 MDB climate finance facilities.

        Args:
            project_data: country_code, sector, total_investment_m,
                          public_component_m, adaptation_category, gfma_aligned.

        Returns:
            dict with eligible_facilities, gcf_gcef_eligibility, estimated_finance_mix.
        """
        country_code = project_data.get("country_code", "").upper()
        sector = project_data.get("sector", "").lower()
        total_inv_m = float(project_data.get("total_investment_m", 10))
        pub_pct = float(project_data.get("public_component_m", total_inv_m)) / max(total_inv_m, 1) * 100
        is_developing = country_code in NAP_COUNTRY_PROFILES
        gfma_aligned = project_data.get("gfma_aligned", True)

        eligible_facilities: List[Dict[str, Any]] = []
        for fac_id, fac in MDB_CLIMATE_FACILITIES.items():
            min_size = fac["min_project_size_m"]
            if total_inv_m < min_size:
                continue

            # Geographic eligibility heuristic
            if fac_id in ["GCF", "GEF", "AFD"] and not is_developing:
                continue
            if fac_id == "AIIB" and country_code not in [
                "BD", "IN", "ID", "VN", "PH", "KH", "MM", "NP", "CN", "PK", "LK"
            ]:
                continue
            if fac_id == "IADB" and country_code not in [
                "MX", "PE", "BO", "GT", "HN", "CO", "BR", "AR", "CL", "EC", "VE"
            ]:
                continue

            grant_pct = fac["typical_grant_pct_adaptation"] if "adaptation" in sector or gfma_aligned else fac.get("max_grant_pct", 0)
            eligible_facilities.append({
                "facility": fac_id,
                "name": fac["name"],
                "estimated_grant_pct": grant_pct,
                "concessional_loan_available": fac["concessional_loan_available"],
                "estimated_finance_m": round(total_inv_m * min(grant_pct / 100, 0.5), 2),
                "key_eligibility_criteria": fac["eligibility_criteria"][:3],
            })

        gcf_eligible = any(f["facility"] == "GCF" for f in eligible_facilities)
        gef_eligible = any(f["facility"] == "GEF" for f in eligible_facilities)

        total_grant_potential = sum(f["estimated_finance_m"] for f in eligible_facilities if f["estimated_grant_pct"] > 0)
        avg_grant_pct = (
            sum(f["estimated_grant_pct"] for f in eligible_facilities) / len(eligible_facilities)
            if eligible_facilities else 0
        )

        return {
            "country_code": country_code,
            "is_developing_country": is_developing,
            "total_investment_m": total_inv_m,
            "eligible_facilities": eligible_facilities,
            "eligible_facility_count": len(eligible_facilities),
            "gcf_eligible": gcf_eligible,
            "gef_eligible": gef_eligible,
            "total_grant_potential_m": round(total_grant_potential, 2),
            "average_grant_pct": round(avg_grant_pct, 1),
            "estimated_finance_mix": {
                "grant_m": round(total_grant_potential, 2),
                "concessional_loan_m": round(total_inv_m * 0.4, 2),
                "commercial_m": round(max(0, total_inv_m - total_grant_potential - total_inv_m * 0.4), 2),
            },
            "assessed_at": datetime.utcnow().isoformat(),
        }

    # ------------------------------------------------------------------
    # 6. NAP/NDC Alignment
    # ------------------------------------------------------------------

    def assess_nap_ndc_alignment(
        self, project_data: Dict[str, Any], country_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Assess alignment of project adaptation measures with the country's
        National Adaptation Plan (NAP) and NDC adaptation component.

        Args:
            project_data: adaptation_measures (list), sectors (list).
            country_code: ISO 3166-1 alpha-2.

        Returns:
            dict with nap_priority_match, ndc_adaptation_alignment,
                 country_adaptation_ambition_score, alignment_gap.
        """
        cc = (country_code or project_data.get("country_code", "")).upper()
        profile = NAP_COUNTRY_PROFILES.get(cc)

        measures = [m.lower() for m in project_data.get("adaptation_measures", [])]
        sectors = [s.lower() for s in project_data.get("sectors", [])]

        if profile is None:
            return {
                "country_code": cc,
                "nap_status": "Unknown",
                "nap_priority_match": [],
                "nap_match_score": 0,
                "ndc_adaptation_alignment": "Unknown",
                "country_adaptation_ambition_score": 0,
                "alignment_gap": [f"No NAP profile available for country code '{cc}'"],
                "assessed_at": datetime.utcnow().isoformat(),
            }

        priority_sectors = profile["priority_sectors"]
        matched_sectors = [s for s in sectors if s in priority_sectors]

        nap_match_score = round(len(matched_sectors) / max(len(priority_sectors), 1) * 100, 1)

        # NDC alignment scoring
        ndc_comp = profile["ndc_adaptation"]
        ndc_score = {"Comprehensive": 85, "Moderate": 60, "Limited": 35}.get(ndc_comp, 50)

        # Alignment gaps
        gaps: List[str] = []
        unmatched_priority = [s for s in priority_sectors if s not in sectors]
        if unmatched_priority:
            gaps.append(f"NAP priority sectors not addressed: {', '.join(unmatched_priority)}")
        if not measures:
            gaps.append("No specific adaptation measures provided")
        if profile["nap_status"] == "In-Progress":
            gaps.append(f"Country NAP not yet submitted — alignment may shift on finalisation")

        return {
            "country_code": cc,
            "country_name": profile["name"],
            "nap_status": profile["nap_status"],
            "nap_year": profile.get("nap_year"),
            "nap_priority_sectors": priority_sectors,
            "project_sectors": sectors,
            "matched_sectors": matched_sectors,
            "nap_match_score": nap_match_score,
            "ndc_adaptation_component": ndc_comp,
            "ndc_alignment_score": ndc_score,
            "country_adaptation_ambition_score": profile["adaptation_ambition_score"],
            "alignment_gap": gaps,
            "ref": "UNFCCC NAP portal; NDC Registry; Paris Agreement Art 7",
            "assessed_at": datetime.utcnow().isoformat(),
        }

    # ------------------------------------------------------------------
    # 7. Full Assessment Orchestrator
    # ------------------------------------------------------------------

    def run_full_assessment(
        self, entity_id: str, project_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Orchestrate all adaptation finance sub-modules.

        Composite adaptation_score:
            GFMA alignment    20%
            GARI scoring      30%
            NPV/BCR           25%
            MDB eligibility   15%
            NAP/NDC           10%

        bankability_tier:
            ≥75 → Highly Bankable
            ≥55 → Bankable
            ≥35 → Conditionally Bankable
            <35  → Pre-Bankable
        """
        assessment_id = str(uuid.uuid4())
        logger.info(
            "Adaptation full assessment started: entity=%s assessment=%s project=%s",
            entity_id, assessment_id, project_data.get("project_name"),
        )

        gfma = self.assess_gfma_alignment(project_data)
        resilience = self.calculate_resilience_delta(
            baseline_risk=float(project_data.get("baseline_exposure_m", 10.0)),
            project_data=project_data,
            rcp_scenario=project_data.get("rcp_scenario", "2C"),
        )
        gari = self.score_gari(project_data)
        npv = self.calculate_adaptation_npv(project_data)
        mdb = self.assess_mdb_eligibility(project_data)
        nap = self.assess_nap_ndc_alignment(
            project_data, country_code=project_data.get("country_code")
        )

        # Component contributions
        gfma_contrib = gfma.get("alignment_score", 50) * 0.20
        gari_contrib = gari.get("composite_gari_score", 50) * 0.30

        bcr = npv.get("bcr", 1.0)
        npv_raw_score = min(100, max(0, bcr * 40))   # BCR 2.5 → 100
        npv_contrib = npv_raw_score * 0.25

        mdb_score = min(100, mdb.get("eligible_facility_count", 0) * 20)
        mdb_contrib = mdb_score * 0.15

        nap_score = (
            nap.get("nap_match_score", 0) * 0.5
            + nap.get("ndc_alignment_score", 0) * 0.5
        )
        nap_contrib = nap_score * 0.10

        adaptation_score = round(
            gfma_contrib + gari_contrib + npv_contrib + mdb_contrib + nap_contrib, 1
        )

        if adaptation_score >= 75:
            bankability_tier = "Highly Bankable"
        elif adaptation_score >= 55:
            bankability_tier = "Bankable"
        elif adaptation_score >= 35:
            bankability_tier = "Conditionally Bankable"
        else:
            bankability_tier = "Pre-Bankable"

        result: Dict[str, Any] = {
            "assessment_id": assessment_id,
            "entity_id": entity_id,
            "project_name": project_data.get("project_name", ""),
            "country_code": project_data.get("country_code", ""),
            "adaptation_score": adaptation_score,
            "bankability_tier": bankability_tier,
            "component_scores": {
                "gfma_20pct": round(gfma_contrib, 1),
                "gari_30pct": round(gari_contrib, 1),
                "npv_bcr_25pct": round(npv_contrib, 1),
                "mdb_15pct": round(mdb_contrib, 1),
                "nap_ndc_10pct": round(nap_contrib, 1),
            },
            "gfma_assessment": gfma,
            "resilience_delta": resilience,
            "gari_assessment": gari,
            "npv_bcr_assessment": npv,
            "mdb_eligibility": mdb,
            "nap_ndc_alignment": nap,
            "regulation_refs": [
                "Paris Agreement Art 7 — Adaptation Goal",
                "GCF Accreditation Master Agreement",
                "GARI Framework (CPI / Global Adaptation Commission 2023)",
                "GFMA Adaptation Finance Framework 2022",
                "ISO 14091:2021 — Climate Change Adaptation",
                "ISO 14093:2022 — Financing Local Adaptation",
                "UNFCCC NAP workstream (COP29)",
            ],
            "assessed_at": datetime.utcnow().isoformat(),
        }

        logger.info(
            "Adaptation full assessment complete: entity=%s score=%.1f tier=%s",
            entity_id, adaptation_score, bankability_tier,
        )
        return result

    # ------------------------------------------------------------------
    # 8. Portfolio Aggregation
    # ------------------------------------------------------------------

    def aggregate_portfolio(
        self, entity_id: str, projects: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Aggregate adaptation metrics across a portfolio of projects.

        Args:
            entity_id: portfolio owner identifier.
            projects: list of project_data dicts.

        Returns:
            dict with portfolio-level weighted scores, total investment,
                 sector diversification, bankability distribution.
        """
        if not projects:
            return {
                "entity_id": entity_id,
                "portfolio_size": 0,
                "message": "No projects provided",
                "assessed_at": datetime.utcnow().isoformat(),
            }

        assessments = [self.run_full_assessment(entity_id, p) for p in projects]

        total_investment = sum(
            float(p.get("total_investment_m", 0)) for p in projects
        )

        # Weighted adaptation score by investment size
        weights = [float(p.get("total_investment_m", 1)) for p in projects]
        total_weight = sum(weights) or 1
        weighted_score = sum(
            a["adaptation_score"] * w
            for a, w in zip(assessments, weights)
        ) / total_weight

        # Bankability distribution
        tier_dist: Dict[str, int] = {}
        for a in assessments:
            t = a["bankability_tier"]
            tier_dist[t] = tier_dist.get(t, 0) + 1

        # Sector diversification
        sectors = [p.get("primary_sector", "unknown") for p in projects]
        unique_sectors = list(set(sectors))

        # Aggregate NPV and BCR
        total_npv = sum(
            a.get("npv_bcr_assessment", {}).get("npv_m", 0) for a in assessments
        )
        avg_bcr = sum(
            a.get("npv_bcr_assessment", {}).get("bcr", 0) for a in assessments
        ) / len(assessments)

        # Total beneficiaries
        total_beneficiaries = sum(
            a.get("npv_bcr_assessment", {}).get("beneficiaries_count", 0) for a in assessments
        )

        # MDB eligibility coverage
        total_grant_potential = sum(
            a.get("mdb_eligibility", {}).get("total_grant_potential_m", 0) for a in assessments
        )

        return {
            "entity_id": entity_id,
            "portfolio_size": len(projects),
            "total_investment_m": round(total_investment, 2),
            "weighted_adaptation_score": round(weighted_score, 1),
            "bankability_distribution": tier_dist,
            "sector_diversification": unique_sectors,
            "sector_count": len(unique_sectors),
            "total_portfolio_npv_m": round(total_npv, 2),
            "average_bcr": round(avg_bcr, 2),
            "total_beneficiaries": total_beneficiaries,
            "total_grant_potential_m": round(total_grant_potential, 2),
            "project_summaries": [
                {
                    "project_name": a.get("project_name"),
                    "country_code": a.get("country_code"),
                    "adaptation_score": a.get("adaptation_score"),
                    "bankability_tier": a.get("bankability_tier"),
                }
                for a in assessments
            ],
            "assessed_at": datetime.utcnow().isoformat(),
        }


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def _parse_score(value: Any) -> float:
    """Convert evidence text or numeric score to 0-100 float."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        # Simple heuristic: score by string length / keyword quality
        keywords_positive = ["comprehensive", "robust", "quantified", "verified", "approved", "third-party"]
        keywords_negative = ["none", "missing", "draft", "tbc"]
        score = 40.0
        lower = value.lower()
        score += sum(8 for k in keywords_positive if k in lower)
        score -= sum(10 for k in keywords_negative if k in lower)
        return max(0.0, min(100.0, score))
    return 50.0


def _approx_irr(investment: float, net_annual_benefit: float, n: int) -> float:
    """
    Approximate IRR using binary search (simplified DCF).
    Returns IRR as a decimal (e.g. 0.15 for 15%).
    """
    if net_annual_benefit <= 0 or investment <= 0:
        return 0.0

    low, high = 0.0, 10.0  # 0% to 1000%
    for _ in range(50):
        mid = (low + high) / 2
        if mid == 0:
            pv = net_annual_benefit * n
        else:
            pv = net_annual_benefit * (1 - (1 + mid) ** -n) / mid
        if pv > investment:
            low = mid
        else:
            high = mid

    return round((low + high) / 2, 4)
