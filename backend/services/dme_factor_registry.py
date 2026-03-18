"""
DME Factor Registry — Unified Factor Taxonomy
================================================
Merges DME's 627-factor taxonomy (209 base × 3 materiality dimensions)
with Risk Analytics' 31 hardcoded overlay registries into a single
queryable interface.

Architecture
------------
  Layer 1: FactorDefinition  — canonical factor metadata
  Layer 2: FactorValue       — time-series snapshots per entity
  Layer 3: FactorVelocity    — EWMA velocity/acceleration (from dme_velocity_engine)
  Layer 4: FactorOverlayLink — maps to existing overlay_engine registries

Key Design Decisions
--------------------
  - DME factors retain their IDs (ENV-001-I, ENV-001-R, ENV-001-O, etc.)
  - Risk Analytics overlay registries mapped as OVR-ESG-xxx, OVR-GEO-xxx, OVR-TEC-xxx
  - Both systems queryable via single get_factors() / get_factor() interface
  - Velocity tracking optional for overlay factors (static by default)
  - Backward compatible: factor_overlay_engine.py unchanged, this is additive

References
----------
  - DME: config/factor_registry_seed.json (627 entries)
  - Risk Analytics: services/factor_overlay_engine.py (31 registries)
  - PCAF Data Quality Score: 1 (highest) — 5 (lowest)
  - ESRS IG3, ISSB S2, TCFD cross-references
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════
# 1.  Enums & Constants
# ═══════════════════════════════════════════════════════════════════════

class Pillar(str, Enum):
    ENVIRONMENTAL = "environmental"
    SOCIAL = "social"
    GOVERNANCE = "governance"
    TECHNOLOGY = "technology"
    CAPITAL_ACCESS = "capitalAccess"
    SECTORAL_STRUCTURE = "sectoralStructure"


class MaterialityDimension(str, Enum):
    IMPACT = "impact"
    RISK = "risk"
    OPPORTUNITY = "opportunity"


class VelocityMethod(str, Enum):
    Z_SCORE = "z_score"
    EXPOSURE_LED = "exposure_led"
    SENTIMENT_LED = "sentiment_led"
    POLICY_LED = "policy_led"
    HAWKES_PROCESS = "hawkes_process"
    PERCENTAGE = "percentage"
    STATIC = "static"  # for overlay factors with no time-series


class DataFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    PER_EVENT = "per_event"
    STATIC = "static"


class SignalDecay(str, Enum):
    INSTANT = "instant"
    FAST = "fast"
    MEDIUM = "medium"
    SLOW = "slow"
    CHRONIC = "chronic"
    PERMANENT = "permanent"


class FactorSource(str, Enum):
    DME = "dme"
    OVERLAY_ESG = "overlay_esg"
    OVERLAY_GEO = "overlay_geo"
    OVERLAY_TECH = "overlay_tech"


# ═══════════════════════════════════════════════════════════════════════
# 2.  Pydantic Schemas
# ═══════════════════════════════════════════════════════════════════════

class RegulatoryRef(BaseModel):
    framework: str
    reference: str
    relevance: Optional[str] = None


class FactorDefinition(BaseModel):
    """Canonical factor definition — one row per factor in the registry."""
    factor_id: str = Field(..., description="Unique ID (ENV-001-I or OVR-ESG-001)")
    factor_name: str
    pillar: str
    topic: Optional[str] = None
    sub_topic: Optional[str] = None
    materiality_dimension: Optional[str] = None
    source: str = Field(default="dme", description="dme | overlay_esg | overlay_geo | overlay_tech")
    data_frequency: str = Field(default="monthly")
    velocity_method: str = Field(default="z_score")
    ewma_alpha: float = Field(default=0.2)
    signal_decay: str = Field(default="medium")
    alert_watch: float = Field(default=1.5)
    alert_elevated: float = Field(default=2.0)
    alert_critical: float = Field(default=3.0)
    alert_extreme: float = Field(default=4.0)
    pcaf_dq: Optional[int] = Field(default=None, ge=1, le=5)
    overlay_registry_key: Optional[str] = Field(default=None, description="Key in factor_overlay_engine.py (for overlay factors)")
    regulatory_refs: list[RegulatoryRef] = Field(default_factory=list)
    unit: Optional[str] = None
    description: Optional[str] = None


class FactorValueSnapshot(BaseModel):
    """Point-in-time value for a factor × entity combination."""
    factor_id: str
    entity_id: str
    value: float
    data_quality_score: Optional[int] = None
    as_of_date: str
    source_description: Optional[str] = None


class FactorSearchRequest(BaseModel):
    pillar: Optional[str] = None
    topic: Optional[str] = None
    source: Optional[str] = None
    materiality_dimension: Optional[str] = None
    velocity_method: Optional[str] = None
    search_text: Optional[str] = None
    limit: int = Field(default=50, le=500)
    offset: int = Field(default=0, ge=0)


class FactorCompareRequest(BaseModel):
    """Compare a DME factor with its closest overlay registry counterpart."""
    dme_factor_id: str


class RegistryStatsResponse(BaseModel):
    total_factors: int
    by_source: dict[str, int]
    by_pillar: dict[str, int]
    by_materiality: dict[str, int]
    by_velocity_method: dict[str, int]
    overlay_registries_mapped: int
    dme_base_factors: int


# ═══════════════════════════════════════════════════════════════════════
# 3.  Overlay → Factor Mapping
# ═══════════════════════════════════════════════════════════════════════

# Maps each of the 31 Risk Analytics overlay registries to a canonical
# factor definition with DME-compatible metadata.

OVERLAY_TO_FACTOR_MAP: list[dict] = [
    # ── ESG Factor Registries (10) ──
    {
        "factor_id": "OVR-ESG-001", "factor_name": "Transition Risk PD Multiplier",
        "pillar": "environmental", "topic": "Climate Transition",
        "materiality_dimension": "risk", "source": "overlay_esg",
        "overlay_registry_key": "ESG_TRANSITION_PD_MULTIPLIER",
        "data_frequency": "quarterly", "velocity_method": "static",
        "unit": "multiplier", "signal_decay": "slow",
        "regulatory_refs": [{"framework": "ESRS", "reference": "E1-6", "relevance": "Transition risk exposure"},
                            {"framework": "TCFD", "reference": "Strategy-b", "relevance": "Business impact"}],
        "description": "NACE sector-level PD multiplier from climate transition risk (PRI IPR 2024)"
    },
    {
        "factor_id": "OVR-ESG-002", "factor_name": "Green Bond Premium",
        "pillar": "environmental", "topic": "Green Finance",
        "materiality_dimension": "opportunity", "source": "overlay_esg",
        "overlay_registry_key": "GREEN_BOND_PREMIUM_BPS",
        "data_frequency": "monthly", "velocity_method": "static",
        "unit": "bps", "signal_decay": "slow",
        "regulatory_refs": [{"framework": "EU GBS", "reference": "Art 6-8", "relevance": "Green bond standard"}],
        "description": "Green bond spread tightening by credit quality (CBI 2024)"
    },
    {
        "factor_id": "OVR-ESG-003", "factor_name": "Biodiversity NatCat Amplifier",
        "pillar": "environmental", "topic": "Biodiversity Loss",
        "materiality_dimension": "risk", "source": "overlay_esg",
        "overlay_registry_key": "BIODIVERSITY_NATCAT_AMPLIFIER",
        "data_frequency": "annual", "velocity_method": "static",
        "unit": "multiplier", "signal_decay": "chronic",
        "regulatory_refs": [{"framework": "ESRS", "reference": "E4-5", "relevance": "Biodiversity impact"},
                            {"framework": "TNFD", "reference": "LEAP-A3", "relevance": "Dependencies"}],
        "description": "Biome-level nat-cat frequency amplifier from biodiversity loss (IPBES/Swiss Re)"
    },
    {
        "factor_id": "OVR-ESG-004", "factor_name": "ESG Alpha Decomposition",
        "pillar": "environmental", "topic": "ESG Performance",
        "materiality_dimension": "opportunity", "source": "overlay_esg",
        "overlay_registry_key": "ESG_ALPHA_DECOMPOSITION",
        "data_frequency": "quarterly", "velocity_method": "static",
        "unit": "pct", "signal_decay": "medium",
        "regulatory_refs": [{"framework": "SFDR", "reference": "Art 7", "relevance": "Principal adverse impacts"}],
        "description": "ESG-attributable alpha by E/S/G pillar and NACE sector (MSCI 2024)"
    },
    {
        "factor_id": "OVR-ESG-005", "factor_name": "Air Quality Mortality Factor",
        "pillar": "social", "topic": "Health & Safety",
        "materiality_dimension": "impact", "source": "overlay_esg",
        "overlay_registry_key": "AIR_QUALITY_MORTALITY",
        "data_frequency": "annual", "velocity_method": "static",
        "unit": "multiplier", "signal_decay": "chronic",
        "regulatory_refs": [{"framework": "ESRS", "reference": "E2-4", "relevance": "Pollution impacts"}],
        "description": "WHO PM2.5-band mortality adjustment factor (WHO/Lancet 2024)"
    },
    {
        "factor_id": "OVR-ESG-006", "factor_name": "Carbon Reduction Valuation Uplift",
        "pillar": "environmental", "topic": "Carbon Reduction",
        "materiality_dimension": "opportunity", "source": "overlay_esg",
        "overlay_registry_key": "CARBON_REDUCTION_VALUATION_UPLIFT",
        "data_frequency": "quarterly", "velocity_method": "static",
        "unit": "EV/EBITDA turns", "signal_decay": "slow",
        "description": "PE valuation multiple uplift from verified CO2 reduction"
    },
    {
        "factor_id": "OVR-ESG-007", "factor_name": "Green Premium (Real Estate)",
        "pillar": "environmental", "topic": "Green Buildings",
        "materiality_dimension": "opportunity", "source": "overlay_esg",
        "overlay_registry_key": "GREEN_PREMIUM_PCT",
        "data_frequency": "annual", "velocity_method": "static",
        "unit": "pct", "signal_decay": "slow",
        "regulatory_refs": [{"framework": "EU Taxonomy", "reference": "CC-M7.1", "relevance": "Building renovation"}],
        "description": "Property value premium by certification tier (JLL/CBRE 2024)"
    },
    {
        "factor_id": "OVR-ESG-008", "factor_name": "Methane Abatement Curve",
        "pillar": "environmental", "topic": "Methane Emissions",
        "materiality_dimension": "opportunity", "source": "overlay_esg",
        "overlay_registry_key": "METHANE_ABATEMENT_CURVE",
        "data_frequency": "annual", "velocity_method": "static",
        "unit": "USD/tCO2e", "signal_decay": "medium",
        "regulatory_refs": [{"framework": "EU Methane Reg", "reference": "2024/1787", "relevance": "MRV requirements"}],
        "description": "Methane abatement cost curve by technology option (IEA 2024)"
    },
    {
        "factor_id": "OVR-ESG-009", "factor_name": "Deforestation-Free Premium",
        "pillar": "environmental", "topic": "Land Use",
        "materiality_dimension": "opportunity", "source": "overlay_esg",
        "overlay_registry_key": "DEFORESTATION_FREE_PREMIUM",
        "data_frequency": "annual", "velocity_method": "static",
        "unit": "pct", "signal_decay": "slow",
        "regulatory_refs": [{"framework": "EUDR", "reference": "2023/1115", "relevance": "Due diligence requirement"}],
        "description": "Value uplift from deforestation-free certification (RSPO/FSC/EUDR)"
    },
    {
        "factor_id": "OVR-ESG-010", "factor_name": "CSRD Gap Closure Rates",
        "pillar": "governance", "topic": "Regulatory Compliance",
        "materiality_dimension": "opportunity", "source": "overlay_esg",
        "overlay_registry_key": "CSRD_GAP_CLOSURE_RATES",
        "data_frequency": "quarterly", "velocity_method": "static",
        "unit": "pct", "signal_decay": "medium",
        "regulatory_refs": [{"framework": "CSRD", "reference": "ESRS 1", "relevance": "General requirements"}],
        "description": "Automated gap closure rates by ESRS pillar"
    },

    # ── Geopolitical Factor Registries (9) ──
    {
        "factor_id": "OVR-GEO-001", "factor_name": "Sovereign Risk Score",
        "pillar": "governance", "topic": "Country Risk",
        "materiality_dimension": "risk", "source": "overlay_geo",
        "overlay_registry_key": "SOVEREIGN_RISK_SCORES",
        "data_frequency": "quarterly", "velocity_method": "static",
        "unit": "score_0_100", "signal_decay": "slow",
        "description": "Composite sovereign risk score (WB WGI + OECD CRC + Maplecroft)"
    },
    {
        "factor_id": "OVR-GEO-002", "factor_name": "FX-Climate Correlation",
        "pillar": "environmental", "topic": "Climate Finance",
        "materiality_dimension": "risk", "source": "overlay_geo",
        "overlay_registry_key": "FX_CLIMATE_CORRELATION",
        "data_frequency": "monthly", "velocity_method": "static",
        "unit": "correlation", "signal_decay": "medium",
        "description": "Currency sensitivity to climate events (BIS/IMF 2024)"
    },
    {
        "factor_id": "OVR-GEO-003", "factor_name": "Sanctions Cascade Probability",
        "pillar": "governance", "topic": "Geopolitical Risk",
        "materiality_dimension": "risk", "source": "overlay_geo",
        "overlay_registry_key": "SANCTIONS_CASCADE",
        "data_frequency": "monthly", "velocity_method": "static",
        "unit": "probability", "signal_decay": "fast",
        "description": "Cross-sector sanctions cascade probability by country"
    },
    {
        "factor_id": "OVR-GEO-004", "factor_name": "Political Stability Index",
        "pillar": "governance", "topic": "Political Risk",
        "materiality_dimension": "risk", "source": "overlay_geo",
        "overlay_registry_key": "POLITICAL_STABILITY",
        "data_frequency": "annual", "velocity_method": "static",
        "unit": "fragility_index", "signal_decay": "slow",
        "description": "Fund for Peace fragility index"
    },
    {
        "factor_id": "OVR-GEO-005", "factor_name": "Food Security Index",
        "pillar": "social", "topic": "Food Security",
        "materiality_dimension": "risk", "source": "overlay_geo",
        "overlay_registry_key": "FOOD_SECURITY_INDEX",
        "data_frequency": "annual", "velocity_method": "static",
        "unit": "eiu_index", "signal_decay": "chronic",
        "description": "EIU Global Food Security Index by country"
    },
    {
        "factor_id": "OVR-GEO-006", "factor_name": "Energy Independence Score",
        "pillar": "environmental", "topic": "Energy Security",
        "materiality_dimension": "risk", "source": "overlay_geo",
        "overlay_registry_key": "ENERGY_INDEPENDENCE",
        "data_frequency": "annual", "velocity_method": "static",
        "unit": "score_0_100", "signal_decay": "slow",
        "description": "Country-level energy independence score"
    },
    {
        "factor_id": "OVR-GEO-007", "factor_name": "Regulatory Complexity Multiplier",
        "pillar": "governance", "topic": "Regulatory Environment",
        "materiality_dimension": "risk", "source": "overlay_geo",
        "overlay_registry_key": "REGULATORY_COMPLEXITY",
        "data_frequency": "quarterly", "velocity_method": "static",
        "unit": "multiplier", "signal_decay": "slow",
        "description": "Cross-jurisdiction regulatory effort multiplier"
    },
    {
        "factor_id": "OVR-GEO-008", "factor_name": "Migration Mortality Adjustment",
        "pillar": "social", "topic": "Demographics",
        "materiality_dimension": "impact", "source": "overlay_geo",
        "overlay_registry_key": "MIGRATION_MORTALITY_ADJUSTMENT",
        "data_frequency": "annual", "velocity_method": "static",
        "unit": "multiplier", "signal_decay": "chronic",
        "description": "Life insurance longevity adjustment for migration patterns"
    },
    {
        "factor_id": "OVR-GEO-009", "factor_name": "Carbon Border Alignment",
        "pillar": "environmental", "topic": "Trade & Carbon",
        "materiality_dimension": "risk", "source": "overlay_geo",
        "overlay_registry_key": "CARBON_BORDER_ALIGNMENT",
        "data_frequency": "quarterly", "velocity_method": "static",
        "unit": "score_0_1", "signal_decay": "medium",
        "regulatory_refs": [{"framework": "CBAM", "reference": "2023/956", "relevance": "Border adjustment"}],
        "description": "Country-level CBAM compliance alignment score"
    },

    # ── Technology Factor Registries (12) ──
    {
        "factor_id": "OVR-TEC-001", "factor_name": "Automation Disruption Risk",
        "pillar": "technology", "topic": "Automation",
        "materiality_dimension": "risk", "source": "overlay_tech",
        "overlay_registry_key": "AUTOMATION_DISRUPTION",
        "data_frequency": "annual", "velocity_method": "static",
        "unit": "risk_0_1", "signal_decay": "chronic",
        "description": "NACE sector-level automation disruption risk (19 sectors)"
    },
    {
        "factor_id": "OVR-TEC-002", "factor_name": "Fintech NIM Disruption",
        "pillar": "technology", "topic": "Financial Innovation",
        "materiality_dimension": "risk", "source": "overlay_tech",
        "overlay_registry_key": "FINTECH_NIM_DISRUPTION",
        "data_frequency": "quarterly", "velocity_method": "static",
        "unit": "bps", "signal_decay": "medium",
        "description": "Net interest margin erosion by banking segment from fintech"
    },
    {
        "factor_id": "OVR-TEC-003", "factor_name": "AI Adoption Score",
        "pillar": "technology", "topic": "AI Adoption",
        "materiality_dimension": "opportunity", "source": "overlay_tech",
        "overlay_registry_key": "AI_ADOPTION_SCORE",
        "data_frequency": "annual", "velocity_method": "static",
        "unit": "score_0_1", "signal_decay": "medium",
        "description": "Sector-level AI adoption maturity (19 NACE sectors)"
    },
    {
        "factor_id": "OVR-TEC-004", "factor_name": "Smart Building Uplift",
        "pillar": "technology", "topic": "PropTech",
        "materiality_dimension": "opportunity", "source": "overlay_tech",
        "overlay_registry_key": "SMART_BUILDING_UPLIFT",
        "data_frequency": "annual", "velocity_method": "static",
        "unit": "pct", "signal_decay": "slow",
        "description": "Property value boost by smart building tech tier"
    },
    {
        "factor_id": "OVR-TEC-005", "factor_name": "Digital Readiness",
        "pillar": "technology", "topic": "Digital Transformation",
        "materiality_dimension": "opportunity", "source": "overlay_tech",
        "overlay_registry_key": "DIGITAL_READINESS",
        "data_frequency": "annual", "velocity_method": "static",
        "unit": "score_0_100", "signal_decay": "medium",
        "description": "Country-level DESI digital competitiveness score (25 countries)"
    },
    {
        "factor_id": "OVR-TEC-006", "factor_name": "Parametric Pricing Adjustment",
        "pillar": "technology", "topic": "InsurTech",
        "materiality_dimension": "opportunity", "source": "overlay_tech",
        "overlay_registry_key": "PARAMETRIC_PRICING_ADJ",
        "data_frequency": "annual", "velocity_method": "static",
        "unit": "pct", "signal_decay": "medium",
        "description": "Insurance premium adjustment from parametric trigger tech"
    },
    {
        "factor_id": "OVR-TEC-007", "factor_name": "Hydrogen Blending Economics",
        "pillar": "technology", "topic": "Hydrogen Economy",
        "materiality_dimension": "opportunity", "source": "overlay_tech",
        "overlay_registry_key": "H2_BLENDING_ECONOMICS",
        "data_frequency": "annual", "velocity_method": "static",
        "unit": "composite", "signal_decay": "slow",
        "description": "H2 type economics: cost premium, CO2 reduction, tech readiness"
    },
    {
        "factor_id": "OVR-TEC-008", "factor_name": "Precision Agriculture Adoption",
        "pillar": "technology", "topic": "AgriTech",
        "materiality_dimension": "opportunity", "source": "overlay_tech",
        "overlay_registry_key": "PRECISION_AG_ADOPTION",
        "data_frequency": "annual", "velocity_method": "static",
        "unit": "pct_yield_uplift", "signal_decay": "slow",
        "description": "Crop yield uplift by precision agriculture adoption tier"
    },
    {
        "factor_id": "OVR-TEC-009", "factor_name": "Supply Chain Digitisation",
        "pillar": "technology", "topic": "Supply Chain Tech",
        "materiality_dimension": "opportunity", "source": "overlay_tech",
        "overlay_registry_key": "SUPPLY_CHAIN_DIGITISATION",
        "data_frequency": "annual", "velocity_method": "static",
        "unit": "score_0_1", "signal_decay": "medium",
        "description": "Supply chain digitisation maturity score by tier"
    },
    {
        "factor_id": "OVR-TEC-010", "factor_name": "AI Assurance Confidence",
        "pillar": "technology", "topic": "AI Governance",
        "materiality_dimension": "opportunity", "source": "overlay_tech",
        "overlay_registry_key": "AI_ASSURANCE_CONFIDENCE",
        "data_frequency": "quarterly", "velocity_method": "static",
        "unit": "score_0_1", "signal_decay": "medium",
        "description": "Regulatory confidence in AI-assisted assurance"
    },
    {
        "factor_id": "OVR-TEC-011", "factor_name": "Medical Advancement Longevity",
        "pillar": "technology", "topic": "MedTech",
        "materiality_dimension": "opportunity", "source": "overlay_tech",
        "overlay_registry_key": "MEDICAL_ADVANCEMENT_LONGEVITY",
        "data_frequency": "annual", "velocity_method": "static",
        "unit": "years", "signal_decay": "chronic",
        "description": "Life expectancy gain by medical technology type"
    },
    {
        "factor_id": "OVR-TEC-012", "factor_name": "Stranded Asset Tech Filter",
        "pillar": "technology", "topic": "Technology Disruption",
        "materiality_dimension": "risk", "source": "overlay_tech",
        "overlay_registry_key": "STRANDED_ASSET_TECH_FILTER",
        "data_frequency": "annual", "velocity_method": "static",
        "unit": "composite", "signal_decay": "chronic",
        "description": "Stranding probability and horizon by asset type"
    },
]


# ═══════════════════════════════════════════════════════════════════════
# 4.  DME 209 Base Factor Topics
# ═══════════════════════════════════════════════════════════════════════

# Condensed from DME's generate_factor_registry.py — 209 unique topics
# grouped by pillar.  Each generates 3 rows (I/R/O dimensions) = 627.

DME_BASE_TOPICS: dict[str, list[dict]] = {
    "environmental": [
        {"id": "ENV", "start": 1, "topics": [
            "Climate Transition", "GHG Emissions", "Carbon Intensity", "Scope 3 Supply Chain",
            "Energy Mix", "Renewable Capacity", "Energy Efficiency", "Fossil Fuel Reserves",
            "Stranded Asset Exposure", "Carbon Price Sensitivity", "Physical Climate Risk",
            "Acute Weather Events", "Chronic Climate Shift", "Sea Level Rise Exposure",
            "Water Stress", "Water Consumption Intensity", "Pollution Emissions",
            "Hazardous Waste", "Air Quality Impact", "Soil Contamination",
            "Biodiversity Dependency", "Ecosystem Service Loss", "Deforestation Risk",
            "Land Use Change", "Marine Ecosystem Impact", "Invasive Species Risk",
            "Circular Economy Readiness", "Waste Reduction", "Material Recovery",
            "Product Lifecycle Extension", "Packaging Sustainability",
            "Microplastics Exposure", "PFAS Contamination", "Ozone Depletion",
            "Light Pollution", "Noise Pollution", "Thermal Pollution",
            "E-Waste Generation", "Nuclear Waste Risk", "Mining Tailings Risk",
            "Freshwater Ecosystem Impact", "Wetland Degradation", "Coral Reef Exposure",
            "Permafrost Thaw Risk", "Glacier Melt Exposure", "Wildfire Risk",
            "Drought Frequency", "Flood Exposure", "Storm Surge Vulnerability",
            "Urban Heat Island", "Agricultural Yield Impact", "Pollinator Decline",
            "Soil Erosion", "Desertification Risk", "Ocean Acidification",
            "Methane Emissions", "N2O Emissions", "HFC Phase-Down",
            "Carbon Capture Readiness", "Nature-Based Solutions", "Coastal Erosion",
            "Groundwater Depletion", "Eutrophication Risk", "Palm Oil Exposure",
            "Soy Deforestation Link", "Timber Legality", "Fisheries Sustainability",
            "Animal Welfare Standards", "Genetic Biodiversity", "Rewilding Potential",
        ]},
    ],
    "social": [
        {"id": "SOC", "start": 1, "topics": [
            "Labour Rights", "Fair Wages", "Working Hours", "Forced Labour Risk",
            "Child Labour Risk", "Freedom of Association", "Collective Bargaining",
            "Health & Safety", "Occupational Disease", "Mental Health",
            "Gender Pay Gap", "Board Diversity", "Ethnic Diversity",
            "Disability Inclusion", "LGBTQ+ Rights", "Age Discrimination",
            "Community Relations", "Indigenous Rights", "Land Tenure",
            "Access to Healthcare", "Access to Education", "Digital Divide",
            "Product Safety", "Data Privacy", "Consumer Protection",
            "Responsible Marketing", "Nutritional Quality", "Addiction Risk",
            "Affordable Housing", "Financial Inclusion", "Microfinance Impact",
            "Human Rights Due Diligence", "Conflict Minerals", "Modern Slavery",
            "Supply Chain Labour", "Migrant Worker Rights", "Living Wage Gap",
            "Social Dialogue Quality", "Employee Engagement", "Training Investment",
            "Redundancy Practices", "Gig Economy Exposure", "Automation Displacement",
            "Pension Adequacy", "Healthcare Benefits", "Parental Leave",
            "Remote Work Readiness", "Workplace Culture", "Whistleblower Protection",
            "Customer Satisfaction", "Complaint Resolution", "Vulnerable Customer",
            "Water Access Impact", "Sanitation Impact", "Food Security Contribution",
            "Vaccine Access", "Medicine Pricing",
        ]},
    ],
    "governance": [
        {"id": "GOV", "start": 1, "topics": [
            "Board Composition", "Board Independence", "CEO Duality",
            "Director Tenure", "Board Skills Matrix", "Succession Planning",
            "Executive Compensation", "Pay-Performance Link", "Clawback Provisions",
            "Say-on-Pay", "Long-Term Incentives", "ESG-Linked Pay",
            "Anti-Corruption", "Bribery Risk", "Political Donations",
            "Lobbying Transparency", "Tax Transparency", "Transfer Pricing",
            "Audit Committee Quality", "Internal Controls", "Risk Committee Effectiveness",
            "Related Party Transactions", "Shareholder Rights", "Minority Protection",
            "Dual-Class Shares", "Poison Pills", "Proxy Access",
            "AGM Attendance", "Voting Transparency", "Stakeholder Engagement",
            "ESG Governance Structure", "Sustainability Committee", "Climate Competence",
            "Materiality Assessment Process", "Integrated Reporting Quality",
            "Assurance Coverage", "Data Governance", "Cybersecurity Governance",
            "AI Ethics Framework", "Responsible Innovation", "IP Protection",
            "Regulatory Compliance History",
        ]},
    ],
    "technology": [
        {"id": "TEC", "start": 1, "topics": [
            "AI Readiness", "Machine Learning Maturity", "NLP Capability",
            "Computer Vision Adoption", "Robotic Process Automation",
            "Blockchain Integration", "IoT Deployment", "Edge Computing",
            "Cloud Migration", "Quantum Computing Exposure", "5G Infrastructure",
            "Digital Twin Adoption", "Cybersecurity Maturity", "Data Analytics Maturity",
            "API Economy Readiness", "Low-Code Adoption", "DevOps Maturity",
            "Green IT Practices", "Tech Debt Ratio", "Innovation Pipeline",
            "R&D Intensity", "Patent Portfolio Strength", "Open Source Contribution",
            "Tech Talent Density",
        ]},
    ],
    "sectoralStructure": [
        {"id": "SEC", "start": 1, "topics": [
            "Market Concentration", "Barriers to Entry", "Regulatory Capture Risk",
            "Subsidy Dependency", "Value Chain Position", "Vertical Integration",
            "Horizontal Diversification", "Geographic Concentration",
            "Customer Concentration", "Supplier Concentration",
            "Commodity Price Sensitivity", "Interest Rate Sensitivity",
            "FX Translation Risk", "Inflation Pass-Through",
            "Cyclicality Index", "Secular Growth Potential",
            "Disruption Vulnerability", "Platform Economy Exposure",
        ]},
    ],
}


# ═══════════════════════════════════════════════════════════════════════
# 5.  Factor Registry Engine
# ═══════════════════════════════════════════════════════════════════════

class FactorRegistryEngine:
    """
    Unified factor registry combining DME's 627-factor taxonomy
    with Risk Analytics' 31 overlay registries.

    All methods are stateless class methods — no DB required.
    DB persistence handled by migration 054 tables.
    """

    # ── Build full registry (cached on first call) ──
    _cache: list[FactorDefinition] | None = None

    @classmethod
    def _build_registry(cls) -> list[FactorDefinition]:
        if cls._cache is not None:
            return cls._cache

        factors: list[FactorDefinition] = []

        # 1. DME 627 factors (209 base × 3 dimensions)
        dimensions = [
            ("I", "impact", "annual"),
            ("R", "risk", "monthly"),
            ("O", "opportunity", "annual"),
        ]

        for pillar_key, groups in DME_BASE_TOPICS.items():
            for group in groups:
                prefix = group["id"]
                for i, topic in enumerate(group["topics"], start=group["start"]):
                    for suffix, dim, freq in dimensions:
                        fid = f"{prefix}-{i:03d}-{suffix}"
                        factors.append(FactorDefinition(
                            factor_id=fid,
                            factor_name=f"{topic} - {dim.title()}",
                            pillar=pillar_key,
                            topic=topic,
                            sub_topic=f"{topic} Detail {i}",
                            materiality_dimension=dim,
                            source="dme",
                            data_frequency=freq,
                            velocity_method="z_score",
                            ewma_alpha=0.2,
                            signal_decay="medium",
                            pcaf_dq=4 if "GHG" in topic or "Carbon" in topic or "Emission" in topic else None,
                        ))

        # 2. Overlay factors (31)
        for m in OVERLAY_TO_FACTOR_MAP:
            refs = [RegulatoryRef(**r) for r in m.get("regulatory_refs", [])]
            factors.append(FactorDefinition(
                factor_id=m["factor_id"],
                factor_name=m["factor_name"],
                pillar=m["pillar"],
                topic=m.get("topic"),
                materiality_dimension=m.get("materiality_dimension"),
                source=m["source"],
                overlay_registry_key=m.get("overlay_registry_key"),
                data_frequency=m.get("data_frequency", "static"),
                velocity_method=m.get("velocity_method", "static"),
                unit=m.get("unit"),
                signal_decay=m.get("signal_decay", "medium"),
                regulatory_refs=refs,
                description=m.get("description"),
            ))

        cls._cache = factors
        return factors

    # ── Query methods ──

    @classmethod
    def get_all_factors(cls, limit: int = 50, offset: int = 0) -> list[dict]:
        registry = cls._build_registry()
        return [f.model_dump() for f in registry[offset:offset + limit]]

    @classmethod
    def get_factor(cls, factor_id: str) -> dict | None:
        registry = cls._build_registry()
        for f in registry:
            if f.factor_id == factor_id:
                return f.model_dump()
        return None

    @classmethod
    def search_factors(cls, req: FactorSearchRequest) -> dict:
        registry = cls._build_registry()
        results = registry

        if req.pillar:
            results = [f for f in results if f.pillar == req.pillar]
        if req.topic:
            results = [f for f in results if f.topic and req.topic.lower() in f.topic.lower()]
        if req.source:
            results = [f for f in results if f.source == req.source]
        if req.materiality_dimension:
            results = [f for f in results if f.materiality_dimension == req.materiality_dimension]
        if req.velocity_method:
            results = [f for f in results if f.velocity_method == req.velocity_method]
        if req.search_text:
            q = req.search_text.lower()
            results = [f for f in results if q in f.factor_name.lower()
                       or (f.topic and q in f.topic.lower())
                       or (f.description and q in f.description.lower())]

        total = len(results)
        page = results[req.offset:req.offset + req.limit]
        return {
            "total": total,
            "limit": req.limit,
            "offset": req.offset,
            "factors": [f.model_dump() for f in page],
        }

    @classmethod
    def get_stats(cls) -> dict:
        registry = cls._build_registry()
        by_source: dict[str, int] = {}
        by_pillar: dict[str, int] = {}
        by_mat: dict[str, int] = {}
        by_vel: dict[str, int] = {}
        overlay_count = 0
        dme_base = set()

        for f in registry:
            by_source[f.source] = by_source.get(f.source, 0) + 1
            by_pillar[f.pillar] = by_pillar.get(f.pillar, 0) + 1
            dim = f.materiality_dimension or "unspecified"
            by_mat[dim] = by_mat.get(dim, 0) + 1
            by_vel[f.velocity_method] = by_vel.get(f.velocity_method, 0) + 1
            if f.overlay_registry_key:
                overlay_count += 1
            if f.source == "dme":
                base = f.factor_id.rsplit("-", 1)[0]
                dme_base.add(base)

        return RegistryStatsResponse(
            total_factors=len(registry),
            by_source=by_source,
            by_pillar=by_pillar,
            by_materiality=by_mat,
            by_velocity_method=by_vel,
            overlay_registries_mapped=overlay_count,
            dme_base_factors=len(dme_base),
        ).model_dump()

    @classmethod
    def get_overlay_mapping(cls) -> list[dict]:
        """Return the 31 overlay→factor mappings."""
        return OVERLAY_TO_FACTOR_MAP

    @classmethod
    def get_pillars(cls) -> dict:
        return {
            "pillars": [p.value for p in Pillar],
            "materiality_dimensions": [d.value for d in MaterialityDimension],
            "velocity_methods": [v.value for v in VelocityMethod],
            "data_frequencies": [f.value for f in DataFrequency],
            "signal_decay_categories": [s.value for s in SignalDecay],
            "sources": [s.value for s in FactorSource],
        }

    @classmethod
    def get_dme_topics(cls) -> dict:
        """Return base topic list per pillar (209 topics)."""
        result = {}
        for pillar, groups in DME_BASE_TOPICS.items():
            topics = []
            for g in groups:
                for i, t in enumerate(g["topics"], start=g["start"]):
                    topics.append({"id": f"{g['id']}-{i:03d}", "topic": t})
            result[pillar] = topics
        return result

    @classmethod
    def compare_factor(cls, dme_factor_id: str) -> dict:
        """
        Find the closest overlay registry match for a DME factor,
        enabling side-by-side comparison of coverage.
        """
        registry = cls._build_registry()
        dme_factor = None
        for f in registry:
            if f.factor_id == dme_factor_id:
                dme_factor = f
                break

        if not dme_factor:
            return {"error": f"Factor {dme_factor_id} not found"}

        # Find overlay factors with matching topic or pillar
        overlay_matches = []
        for f in registry:
            if f.source == "dme":
                continue
            score = 0
            if f.pillar == dme_factor.pillar:
                score += 1
            if f.materiality_dimension == dme_factor.materiality_dimension:
                score += 1
            if f.topic and dme_factor.topic and (
                f.topic.lower() in dme_factor.topic.lower()
                or dme_factor.topic.lower() in f.topic.lower()
            ):
                score += 3
            if score > 0:
                overlay_matches.append({"factor": f.model_dump(), "relevance_score": score})

        overlay_matches.sort(key=lambda x: x["relevance_score"], reverse=True)

        return {
            "dme_factor": dme_factor.model_dump(),
            "overlay_matches": overlay_matches[:5],
            "has_overlay_coverage": len(overlay_matches) > 0,
        }
