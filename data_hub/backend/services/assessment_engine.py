"""
Assessment engine — A2 Intelligence Reference Data Hub.

Priority logic:
  P0 ≥ 72  — Critical path: integrate immediately
  P1 50–71 — High value: next sprint
  P2  < 50  — Supplementary: backlog

Utility classification is multi-dimensional:
  primary        — main analytical role (benchmarking/referencing/approximation/supplementary)
  tangential     — secondary analytical role (different from primary)
  complementary_role — how this source enriches/validates another source's output
  supplementary_role — monitoring/context/verification role
  use_case_tags  — specific platform use-cases this source enables (directly or tangentially)
"""
from typing import Dict, List, Optional, Any

# ── Scoring tables ────────────────────────────────────────────────────────────

QUALITY_SCORES: Dict[str, float] = {
    "A+": 25, "A": 20, "A-": 18, "B+": 13, "B": 10, "B-": 7, "C": 4
}

COST_SCORES: Dict[str, float] = {
    "Free": 15, "Free tier": 11, "Free (limited)": 9,
    "Free (100/day)": 8, "Free (60/min)": 7, "Free (academic)": 6,
    "Paid": 2, "Subscription": 2,
}

ACCESS_SCORES: Dict[str, float] = {
    "REST API": 15, "OAuth API": 13, "S3 Download": 12,
    "Python Library": 12, "CSV Download": 9,
    "Apify Scraper": 7, "Web Scrape": 5,
    "Manual": 2, "MANUAL - See Instructions": 2,
}

FRESHNESS_SCORES: Dict[str, float] = {
    "Real-time": 15, "Hourly": 13, "Daily": 12, "Weekly": 9,
    "Monthly": 6, "Quarterly": 4, "Semi-annual": 3,
    "Annual": 2, "Per version release": 1, "Per methodology update": 1,
}

GEOGRAPHIC_SCORES: Dict[str, float] = {
    "Global": 15, "global": 15, "Worldwide": 15,
    "Asia-Pacific": 9, "Southeast Asia": 7,
    "EU": 6, "Europe": 6, "US": 6, "UK": 6, "Asia": 6,
}

STATUS_MODIFIERS: Dict[str, float] = {
    "active": 10, "configuring": 3, "planned": 0, "paused": -8, "error": -12
}

# ── Platform module mapping ────────────────────────────────────────────────────
# Maps source category → which platform modules it directly feeds.
# Based on confirmed built modules in MEMORY.md.

CATEGORY_TO_MODULES: Dict[str, List[str]] = {
    "Financial Data": [
        "portfolio_analytics", "pcaf_financed_emissions", "pd_calculator",
        "ecl_calculator", "scenario_analysis",
    ],
    "Macro": [
        "scenario_analysis", "portfolio_analytics", "stranded_assets",
        "carbon_calculator",
    ],
    "ESG Data": [
        "portfolio_analytics", "carbon_calculator", "csrd_issb_disclosure",
        "nature_risk_tnfd", "sustainability_calculator", "pcaf_financed_emissions",
    ],
    "ESG Ratings": [
        "portfolio_analytics", "pcaf_financed_emissions", "csrd_issb_disclosure",
        "sustainability_calculator",
    ],
    "ESG Framework": [
        "csrd_issb_disclosure", "regulatory_compliance", "sustainability_calculator",
    ],
    "Regulatory": [
        "csrd_issb_disclosure", "regulatory_compliance", "cbam_calculator",
        "supply_chain",
    ],
    "Government": [
        "carbon_calculator", "nature_risk_tnfd", "regulatory_compliance",
        "stranded_assets",
    ],
    "Reference": [
        "portfolio_analytics", "real_estate_valuation", "entity_resolution",
        "pcaf_financed_emissions",
    ],
    "Governance": [
        "csrd_issb_disclosure", "sustainability_calculator", "regulatory_compliance",
    ],
    "News": [
        "portfolio_analytics", "controversy_screening", "sustainability_calculator",
    ],
    "News & Events": [
        "portfolio_analytics", "controversy_screening", "scenario_analysis",
    ],
    "Financial News": [
        "portfolio_analytics", "scenario_analysis",
    ],
    "News & Text": [
        "portfolio_analytics", "sustainability_calculator",
    ],
    "Social": [
        "sustainability_calculator", "controversy_screening",
    ],
    "Social Media": [
        "controversy_screening", "sustainability_calculator",
    ],
    "Consumer": [
        "sustainability_calculator", "supply_chain",
    ],
    "Employment": [
        "csrd_issb_disclosure", "sustainability_calculator",
    ],
    "Employee Data": [
        "csrd_issb_disclosure", "sustainability_calculator",
    ],
    "Academic": [
        "methodology_engine", "carbon_calculator",
    ],
    "Technology": [
        "portfolio_analytics", "sustainability_calculator",
    ],
    "Geopolitical": [
        "scenario_analysis", "physical_risk_overlay",
    ],
    "Compliance": [
        "supply_chain", "regulatory_compliance",
    ],
    "Search Data": [
        "controversy_screening",
    ],
}

# ── Multi-dimensional utility classification ──────────────────────────────────
#
# Each category carries FOUR utility dimensions:
#   primary         — load-bearing analytical role
#   tangential      — secondary analytical value (different axis from primary)
#   complementary_role — how this data enriches or validates output from other sources
#   supplementary_role — the monitoring/context/verification role
#   use_case_tags   — specific named use-cases (direct and tangential)
#
# Design rationale:
#   - "tangential" captures cross-cutting value not obvious from the primary label
#   - "complementary_role" makes source interdependencies explicit for fallback design
#   - "supplementary_role" surfaces monitoring value even for low-priority sources
#   - "use_case_tags" provide machine-readable hooks for module-to-source discovery

UTILITY_DIMENSIONS: Dict[str, Dict[str, Any]] = {
    "Financial Data": {
        "primary": "benchmarking",
        "tangential": "referencing",
        "complementary_role": (
            "Cross-validates entity financial KPIs against regulatory filings and ratings data. "
            "Anchors PCAF DQS attribution and provides EVIC/market cap denominators for financed-emissions intensity."
        ),
        "supplementary_role": (
            "Market valuation context for portfolio dashboards; signals earnings regime changes that alter transition risk."
        ),
        "use_case_tags": [
            "portfolio_valuation", "financed_emissions_pcaf", "pd_modelling",
            "ecl_calculation", "evic_denominator", "market_cap_benchmarking",
        ],
    },
    "Macro": {
        "primary": "benchmarking",
        "tangential": "approximation",
        "complementary_role": (
            "Calibrates NGFS/IEA scenario pathways and validates carbon-price trajectories. "
            "Provides GDP/inflation/rate inputs for ECL stress-test scenarios."
        ),
        "supplementary_role": (
            "Economic backdrop for portfolio sensitivity analysis; commodity price context for stranded-asset modelling."
        ),
        "use_case_tags": [
            "scenario_calibration", "carbon_price_trajectory", "gdp_stress_test",
            "interest_rate_sensitivity", "energy_price_modelling", "inflation_adjustment",
        ],
    },
    "ESG Data": {
        "primary": "benchmarking",
        "tangential": "referencing",
        "complementary_role": (
            "Primary GHG source for PCAF DQS scoring and CSRD E1/E2 disclosure inputs. "
            "Scope 3 categories feed supply-chain attribution and product-life-cycle accounting."
        ),
        "supplementary_role": (
            "ESG performance trend monitoring across portfolio companies; emission-intensity drift alerts."
        ),
        "use_case_tags": [
            "ghg_accounting", "pcaf_dqs", "csrd_e1", "scope3_category_mapping",
            "waci_calculation", "water_accounting", "biodiversity_pressure_indicator",
        ],
    },
    "ESG Ratings": {
        "primary": "benchmarking",
        "tangential": "referencing",
        "complementary_role": (
            "Rating convergence analysis across MSCI/Sustainalytics/Refinitiv; validates and triangulates internal ESG scores. "
            "Used as DQS 3 proxy when entity-level disclosure unavailable."
        ),
        "supplementary_role": (
            "ESG controversy flag and rating migration monitoring; engagement-priority signalling for active ownership."
        ),
        "use_case_tags": [
            "portfolio_esg_score", "sfdr_pai", "engagement_targeting",
            "esg_rating_overlay", "dqs3_proxy", "controversy_flag",
        ],
    },
    "ESG Framework": {
        "primary": "referencing",
        "tangential": "benchmarking",
        "complementary_role": (
            "Maps disclosure requirements to internal KPIs; aligns ESRS/ISSB data models with existing module schemas. "
            "Sector-specific SASB standards feed KPI Finder source-chain resolution."
        ),
        "supplementary_role": (
            "Regulatory horizon scanning; framework evolution tracking (ESRS amendments, ISSB updates)."
        ),
        "use_case_tags": [
            "csrd_esrs_mapping", "issb_s2_disclosure", "tcfd_alignment",
            "gri_sasb_mapping", "kpi_ontology_anchoring", "sector_standard_reference",
        ],
    },
    "Regulatory": {
        "primary": "referencing",
        "tangential": "benchmarking",
        "complementary_role": (
            "Sanctions/PEP screening cross-checks entity registry for portfolio due diligence. "
            "CBAM embedded-carbon data feeds supply-chain carbon accounting and border adjustment calculations."
        ),
        "supplementary_role": (
            "Compliance calendar and regulatory deadline monitoring; policy change alerting."
        ),
        "use_case_tags": [
            "sanctions_screening", "cbam_embedded_carbon", "sfdr_disclosure",
            "eu_taxonomy_alignment", "regulatory_filing_tracking", "compliance_calendar",
        ],
    },
    "Government": {
        "primary": "referencing",
        "tangential": "benchmarking",
        "complementary_role": (
            "Grid emission factors feed Scope 2 market-based calculation; national GHG inventories calibrate entity estimates. "
            "Policy carbon-price data anchors transition-risk scenario pathways."
        ),
        "supplementary_role": (
            "National statistics cross-validation for entity-level GHG estimates; biodiversity-area baseline."
        ),
        "use_case_tags": [
            "scope2_grid_ef", "national_ghg_benchmarking", "biodiversity_protected_area",
            "policy_carbon_price", "grid_emission_factor", "transition_risk_policy_anchor",
        ],
    },
    "Reference": {
        "primary": "referencing",
        "tangential": "benchmarking",
        "complementary_role": (
            "Entity disambiguation backbone — resolves LEI/ISIN/ticker across all modules. "
            "Parent-subsidiary hierarchy feeds consolidated PCAF financed-emissions attribution."
        ),
        "supplementary_role": (
            "Data lineage and provenance anchoring for audit trail; master data validation layer."
        ),
        "use_case_tags": [
            "entity_resolution", "lei_mapping", "isin_lookup",
            "parent_subsidiary_hierarchy", "data_lineage_anchor", "master_data_validation",
        ],
    },
    "Governance": {
        "primary": "referencing",
        "tangential": "benchmarking",
        "complementary_role": (
            "Board independence and diversity metrics feed CSRD G1 and ISSB S2 governance disclosures. "
            "CEO pay ratio and audit committee data complement ESG ratings governance sub-score."
        ),
        "supplementary_role": (
            "Executive compensation and whistleblower policy tracking; corporate governance watchlist."
        ),
        "use_case_tags": [
            "csrd_g1_governance", "board_diversity_disclosure", "esg_governance_score",
            "anti_corruption_screening", "ceo_pay_ratio", "audit_committee_tracking",
        ],
    },
    "News": {
        "primary": "approximation",
        "tangential": "supplementary",
        "complementary_role": (
            "Controversy signals cross-referenced against ESG ratings to detect rating divergence and greenwashing flags. "
            "Real-time event flags used as DQS 5 proxy when structured ESG disclosure is absent."
        ),
        "supplementary_role": (
            "Real-time ESG risk monitoring and reputational event alerts for active portfolio management."
        ),
        "use_case_tags": [
            "controversy_screening", "esg_sentiment_proxy", "news_based_esg_flag",
            "media_risk_overlay", "greenwashing_signal", "reputational_alert",
        ],
    },
    "News & Events": {
        "primary": "approximation",
        "tangential": "supplementary",
        "complementary_role": (
            "Event-driven risk proxy (spills, fines, disasters) feeds physical risk overlay and supply-chain disruption model. "
            "Catastrophic event data complements CAT risk assessment scoring."
        ),
        "supplementary_role": (
            "Market intelligence feed for scenario analysis trigger events; supply-chain disruption early warning."
        ),
        "use_case_tags": [
            "event_risk_proxy", "physical_risk_trigger", "supply_chain_disruption_flag",
            "cat_risk_complement", "scenario_trigger_event",
        ],
    },
    "Financial News": {
        "primary": "approximation",
        "tangential": "supplementary",
        "complementary_role": (
            "Analyst sentiment proxy for earnings deviation in PD behavioural overlay. "
            "Guidance revision data complements ECL forward-looking economic adjustments."
        ),
        "supplementary_role": (
            "Market narrative context for portfolio manager decision support; M&A and restructuring signal monitoring."
        ),
        "use_case_tags": [
            "earnings_sentiment_proxy", "analyst_rating_signal",
            "pd_behavioural_overlay", "ecl_forward_looking_proxy",
        ],
    },
    "News & Text": {
        "primary": "approximation",
        "tangential": "supplementary",
        "complementary_role": (
            "Disclosure keyword analysis complements structured CSRD gap-analysis by identifying partial disclosures. "
            "NLP-extracted ESG metrics serve as DQS 4/5 proxy when structured data is unavailable."
        ),
        "supplementary_role": (
            "ESG narrative trend monitoring across reporting cycles; regulatory language drift tracking."
        ),
        "use_case_tags": [
            "csrd_gap_proxy", "disclosure_nlp", "esg_text_sentiment",
            "partial_disclosure_detection", "regulatory_language_tracking",
        ],
    },
    "Social": {
        "primary": "approximation",
        "tangential": "supplementary",
        "complementary_role": (
            "Employee satisfaction scores serve as CSRD S1 workforce-sentiment proxy. "
            "Glassdoor ratings complement structured HR headcount and turnover disclosure."
        ),
        "supplementary_role": (
            "Human capital risk monitoring for social pillar; labour relations watchlist for portfolio companies."
        ),
        "use_case_tags": [
            "csrd_s1_proxy", "workforce_sentiment", "social_risk_indicator",
            "employee_satisfaction_proxy", "human_capital_monitoring",
        ],
    },
    "Social Media": {
        "primary": "approximation",
        "tangential": "supplementary",
        "complementary_role": (
            "Social brand-risk scores complement news controversy counts for triangulated reputational assessment. "
            "Real-time sentiment amplification signals used alongside structured ESG ratings."
        ),
        "supplementary_role": (
            "Reputational risk monitoring for portfolio company watch-list; ESG controversy amplification tracking."
        ),
        "use_case_tags": [
            "brand_risk_proxy", "controversy_amplification", "reputational_monitoring",
            "sentiment_triangulation", "esg_controversy_velocity",
        ],
    },
    "Consumer": {
        "primary": "approximation",
        "tangential": "supplementary",
        "complementary_role": (
            "Consumer spending patterns proxy for sector demand in transition-risk scenario analysis. "
            "Discretionary-spend shifts signal stranded-asset demand destruction for fossil sectors."
        ),
        "supplementary_role": (
            "Market trend context for transition risk sector scoring; demand-shock early warning."
        ),
        "use_case_tags": [
            "demand_shock_proxy", "sector_transition_signal", "consumer_behaviour_indicator",
            "stranded_asset_demand_proxy", "transition_risk_demand_factor",
        ],
    },
    "Employment": {
        "primary": "referencing",
        "tangential": "benchmarking",
        "complementary_role": (
            "Workforce headcount, diversity and pay-gap data for CSRD S1 and ISSB S2 social disclosures. "
            "Turnover and injury rates complement Sustainalytics/MSCI social sub-scores."
        ),
        "supplementary_role": (
            "Labour market trend monitoring for supply chain social risk; living-wage compliance signal."
        ),
        "use_case_tags": [
            "csrd_s1_workforce", "gender_pay_gap_disclosure", "headcount_benchmarking",
            "turnover_risk", "issb_s2_social", "brsr_workforce",
        ],
    },
    "Employee Data": {
        "primary": "referencing",
        "tangential": "benchmarking",
        "complementary_role": (
            "Employee coverage and segmentation for CSRD S1 own-workforce reporting. "
            "Workforce coverage percentage feeds BRSR and GRI disclosure completeness assessment."
        ),
        "supplementary_role": (
            "HR data quality cross-check; disclosure completeness gap identification."
        ),
        "use_case_tags": [
            "csrd_s1_own_workforce", "brsr_disclosure", "workforce_coverage_pct",
            "hr_data_validation", "gri_social_metrics",
        ],
    },
    "Academic": {
        "primary": "supplementary",
        "tangential": "referencing",
        "complementary_role": (
            "Methodology validation source for carbon credit DQS and emission-factor peer review. "
            "Peer-reviewed emission factors complement IPCC/EPA defaults as DQS quality anchor."
        ),
        "supplementary_role": (
            "Research trend monitoring for emerging ESG metrics, regulatory signals and methodology updates."
        ),
        "use_case_tags": [
            "methodology_validation", "emission_factor_peer_review", "academic_benchmarking",
            "ipcc_complement", "dqs_quality_anchor", "research_trend_monitoring",
        ],
    },
    "Technology": {
        "primary": "supplementary",
        "tangential": "approximation",
        "complementary_role": (
            "Clean-tech adoption data complements stranded-asset transition-pathway modelling. "
            "Patent and R&D data proxy innovation pace for technology-disruption risk in sector assessments."
        ),
        "supplementary_role": (
            "Innovation risk scoring for sector assessments; data-centre and power-plant technology transition tracking."
        ),
        "use_case_tags": [
            "clean_tech_adoption", "stranded_asset_tech_disruption", "innovation_risk_proxy",
            "data_centre_transition", "power_plant_tech_transition",
        ],
    },
    "Geopolitical": {
        "primary": "supplementary",
        "tangential": "approximation",
        "complementary_role": (
            "Political and conflict risk overlays complement physical risk assessment in nature/real-estate modules. "
            "Country risk scores feed supply-chain due diligence and forced-labour screening."
        ),
        "supplementary_role": (
            "Macro geopolitical context for scenario stress-test narratives; country risk monitoring for cross-border investments."
        ),
        "use_case_tags": [
            "physical_risk_overlay", "country_risk_proxy", "supply_chain_geopolitical_flag",
            "scenario_narrative", "forced_labour_country_signal", "cross_border_risk",
        ],
    },
    "Compliance": {
        "primary": "referencing",
        "tangential": "supplementary",
        "complementary_role": (
            "AML/PEP flags complement GLEIF entity registry and sanctions lists for comprehensive due diligence. "
            "Adverse media feeds supplement structured ESG controversy data for supply-chain supplier vetting."
        ),
        "supplementary_role": (
            "Adverse media and compliance violation monitoring for portfolio watchlist; ongoing supplier screening."
        ),
        "use_case_tags": [
            "aml_screening", "pep_flag", "adverse_media", "supply_chain_compliance",
            "sanctions_overlay", "supplier_due_diligence", "entity_due_diligence",
        ],
    },
    "Search Data": {
        "primary": "supplementary",
        "tangential": "approximation",
        "complementary_role": (
            "Search volume proxies public awareness and velocity of ESG controversy events. "
            "Trend data complements social-media sentiment for reputational-risk triangulation."
        ),
        "supplementary_role": (
            "Brand-risk trend analysis; consumer and investor attention monitoring for portfolio companies."
        ),
        "use_case_tags": [
            "controversy_awareness_proxy", "reputational_trend", "brand_search_risk",
            "controversy_velocity", "investor_attention_proxy",
        ],
    },
}

# Backward-compat: primary utility per category
CATEGORY_TO_UTILITY: Dict[str, str] = {
    cat: dims["primary"] for cat, dims in UTILITY_DIMENSIONS.items()
}

# ── Business vertical bonus ────────────────────────────────────────────────────

VERTICAL_BONUS_SOURCES: Dict[str, float] = {
    # Financial institutions
    "GLEIF LEI Database": 10,
    "SEC EDGAR": 10,
    "MSCI ESG Ratings": 8,
    "CDP": 8,
    "Sustainalytics (Morningstar)": 8,
    "Refinitiv ESG": 7,
    "OFAC SDN + EU + UN Sanctions": 10,
    "yfinance": 7,
    "Finnhub API": 5,
    # Energy / stranded assets
    "Global Energy Monitor (GCPT)": 10,
    "NGFS Scenarios": 10,
    "Climate TRACE": 9,
    "IEA World Energy Outlook": 9,
    "Our World in Data (OWID)": 7,
    "IRENA LCOE Statistics": 7,
    "Global Power Plant Database": 8,
    # PCAF / financed emissions
    "EPA Greenhouse Gas": 7,
    "EDGAR (EU JRC)": 7,
    # Nature / real estate
    "WRI Aqueduct": 8,
    "WDPA Protected Areas": 7,
    "Global Forest Watch": 7,
    "CRREM Pathways": 9,
    # Supply chain
    "SBTi Target Registry": 8,
    "Open Supply Chain": 7,
    "Violation Tracker": 7,
    # CSRD / regulatory
    "EU Taxonomy Navigator": 8,
    "SFDR PAI": 7,
}

# ── KPI catalogue: source category → key datapoints ──────────────────────────

CATEGORY_TO_DATAPOINTS: Dict[str, List[str]] = {
    "Financial Data": [
        "market_cap", "enterprise_value", "evic", "revenue",
        "total_assets", "ebitda", "net_income", "pe_ratio",
        "beta", "dividend_yield", "stock_price",
    ],
    "Macro": [
        "gdp_growth_rate", "inflation_rate", "carbon_price_usd_tco2e",
        "risk_free_rate", "credit_spread", "unemployment_rate",
        "energy_price_index", "commodity_price",
    ],
    "ESG Data": [
        "scope1_ghg_tco2e", "scope2_ghg_tco2e", "scope3_ghg_tco2e",
        "carbon_intensity_revenue", "carbon_intensity_asset",
        "waci", "water_consumption_m3", "waste_generated_tonnes",
        "renewable_energy_pct", "energy_intensity_kwh",
    ],
    "ESG Ratings": [
        "esg_score_overall", "environmental_score", "social_score",
        "governance_score", "esg_rating_letter", "esg_controversy_score",
        "esg_percentile",
    ],
    "ESG Framework": [
        "gri_disclosure_status", "sasb_metric_value", "tcfd_alignment_score",
        "csrd_esrs_dp_value", "issb_s2_kpi",
    ],
    "Regulatory": [
        "sanctions_flag", "regulatory_filing_date", "compliance_score",
        "cbam_embedded_carbon", "sfdr_pai_value", "eu_taxonomy_aligned_pct",
    ],
    "Government": [
        "grid_emission_factor_tco2e_mwh", "national_ghg_inventory",
        "policy_carbon_price", "regulatory_target_year",
        "biodiversity_area_protected_pct",
    ],
    "Reference": [
        "lei_number", "isin", "legal_entity_name", "jurisdiction",
        "entity_type", "parent_lei", "ultimate_parent_lei",
    ],
    "Governance": [
        "board_independence_pct", "board_gender_diversity_pct",
        "ceo_pay_ratio", "anti_corruption_policy",
        "whistleblower_policy", "audit_committee_independence",
    ],
    "News": ["esg_news_sentiment", "controversy_count", "esg_topic_tag"],
    "News & Events": ["event_tone_score", "esg_event_category", "controversy_flag"],
    "Financial News": ["news_sentiment_score", "analyst_rating_change"],
    "News & Text": ["esg_text_sentiment", "disclosure_keyword_count"],
    "Social": ["employee_glassdoor_rating", "review_sentiment_score"],
    "Social Media": ["social_sentiment_score", "brand_risk_score"],
    "Consumer": ["consumer_confidence_index", "sector_spending_growth"],
    "Employment": ["headcount", "gender_pay_gap_pct", "turnover_rate"],
    "Employee Data": ["total_employees", "workforce_coverage_pct"],
    "Academic": ["research_paper_count", "citation_index"],
    "Technology": ["patent_count", "rd_spend_usd", "clean_tech_index"],
    "Geopolitical": ["conflict_events_count", "political_risk_score"],
    "Compliance": ["aml_flag", "pep_flag", "adverse_media_count"],
    "Search Data": ["search_volume_index", "trend_score"],
}

# ── Fallback catalogue ────────────────────────────────────────────────────────

FALLBACK_CHAIN: Dict[str, List[Dict[str, str]]] = {
    "MSCI ESG Ratings": [
        {"source": "Sustainalytics (Morningstar)", "method": "direct_substitute",
         "assumption": "Similar ESG rating methodology; minor scale differences. Apply linear rescale if needed."},
        {"source": "Refinitiv ESG", "method": "peer_average",
         "assumption": "Refinitiv E/S/G sub-scores averaged. 0.85x adjustment for scale."},
        {"source": "CDP", "method": "sector_proxy",
         "assumption": "CDP Climate Score used as proxy for MSCI Climate pillar. Not a full substitute."},
    ],
    "Climate TRACE": [
        {"source": "Our World in Data (OWID)", "method": "sector_proxy",
         "assumption": "Country-level sector intensity × entity revenue/output. PCAF DQS 4 estimate."},
        {"source": "EPA Greenhouse Gas", "method": "direct_substitute",
         "assumption": "US facilities only. Verified facility-level Scope 1 data."},
        {"source": "EDGAR (EU JRC)", "method": "sector_proxy",
         "assumption": "Country/sector grid data for Scope 2 grid emission factor where entity-level unavailable."},
    ],
    "NGFS Scenarios": [
        {"source": "IEA World Energy Outlook", "method": "direct_substitute",
         "assumption": "IEA NZE/SDS/STEPS pathways map to NGFS NZE2050/Delayed/CP. Align variable names."},
    ],
    "GLEIF LEI Database": [
        {"source": "Open Corporates", "method": "partial_substitute",
         "assumption": "Legal entity name + jurisdiction lookup. LEI not always available; match confidence lower."},
    ],
    "yfinance": [
        {"source": "Finnhub API", "method": "direct_substitute",
         "assumption": "Align on adjusted close prices. Same market data, different vendor."},
    ],
    "SEC EDGAR": [
        {"source": "Open Corporates", "method": "partial_substitute",
         "assumption": "Non-US entities. Use Open Corporates filing metadata where SEC unavailable."},
    ],
    "WRI Aqueduct": [
        {"source": "Global Forest Watch", "method": "partial_substitute",
         "assumption": "GFW covers deforestation/land-use risk but not water stress specifically."},
    ],
    "CRREM Pathways": [
        {"source": "IEA World Energy Outlook", "method": "sector_proxy",
         "assumption": "IEA building-sector energy-intensity pathways used as fallback glidepath."},
    ],
    "SBTi Target Registry": [
        {"source": "CDP", "method": "partial_substitute",
         "assumption": "CDP responses indicate SBTi status. Not real-time; annual cadence."},
    ],
}


# ── Main scoring function ─────────────────────────────────────────────────────

def assess_source(source: Dict[str, Any]) -> Dict[str, Any]:
    """
    Full multi-dimensional assessment for a source record.
    Works with both DB model column names and raw Excel column names.
    """
    def get(key: str, alt: str = "") -> str:
        return str(source.get(key) or source.get(alt) or "").strip()

    quality_str   = get("quality_rating",  "Quality")
    cost_str      = get("cost",             "Cost")
    access_str    = get("access_type",      "API/Access")
    freshness_str = get("update_freq",      "Update Freq")
    geo_str       = get("geographic",       "Geographic")
    status_str    = get("status",           "Status")
    category_str  = get("category",         "Category")
    name_str      = get("name",             "Source Name")

    # Component scores
    q_score  = _score_quality(quality_str)
    c_score  = _score_cost(cost_str)
    a_score  = _score_access(access_str)
    f_score  = _score_freshness(freshness_str)
    g_score  = _score_coverage(geo_str)
    e_score  = _score_effort(access_str)
    s_mod    = STATUS_MODIFIERS.get(status_str.lower(), 0)
    v_bonus  = VERTICAL_BONUS_SOURCES.get(name_str, 0)

    total = q_score + c_score + a_score + f_score + g_score + e_score + s_mod + v_bonus
    total = min(max(total, 0.0), 100.0)

    # Priority
    priority = "P0" if total >= 72 else ("P1" if total >= 50 else "P2")

    # Multi-dimensional utility
    dims = UTILITY_DIMENSIONS.get(category_str, {
        "primary": "supplementary",
        "tangential": "referencing",
        "complementary_role": "General reference and context data.",
        "supplementary_role": "Background monitoring and trend analysis.",
        "use_case_tags": [],
    })

    primary_utility = dims["primary"]
    modules         = CATEGORY_TO_MODULES.get(category_str, [])
    datapoints      = CATEGORY_TO_DATAPOINTS.get(category_str, [])
    fallbacks       = FALLBACK_CHAIN.get(name_str, [])
    value_desc      = _value_description(source, quality_str, freshness_str, priority, primary_utility, modules)

    return {
        "total_score":               round(total, 1),
        "quality_score":             round(q_score, 1),
        "cost_score":                round(c_score, 1),
        "access_score":              round(a_score, 1),
        "freshness_score":           round(f_score, 1),
        "coverage_score":            round(g_score, 1),
        "integration_effort_score":  round(e_score, 1),
        "priority":                  priority,
        "utility":                   primary_utility,
        "utility_dimensions": {
            "primary":             dims["primary"],
            "tangential":          dims["tangential"],
            "complementary_role":  dims["complementary_role"],
            "supplementary_role":  dims["supplementary_role"],
            "use_case_tags":       dims["use_case_tags"],
        },
        "value_description":         value_desc,
        "key_datapoints":            datapoints,
        "target_modules":            modules,
        "fallback_sources":          fallbacks,
    }


# ── Component scorers ─────────────────────────────────────────────────────────

def _score_quality(s: str) -> float:
    return float(QUALITY_SCORES.get(s, 8))

def _score_cost(s: str) -> float:
    for k, v in COST_SCORES.items():
        if s.lower().startswith(k.lower()):
            return float(v)
    return 5.0

def _score_access(s: str) -> float:
    score = ACCESS_SCORES.get(s)
    if score is not None:
        return float(score)
    sl = s.lower()
    if "rest" in sl or "api" in sl: return 15.0
    if "csv" in sl or "download" in sl: return 9.0
    if "scrape" in sl or "puppeteer" in sl: return 5.0
    if "python" in sl or "library" in sl: return 12.0
    if "apify" in sl: return 7.0
    if "manual" in sl: return 2.0
    return 5.0

def _score_freshness(s: str) -> float:
    score = FRESHNESS_SCORES.get(s)
    if score is not None:
        return float(score)
    sl = s.lower()
    if "real" in sl: return 15.0
    if "hourly" in sl: return 13.0
    if "daily" in sl or "day" in sl: return 12.0
    if "week" in sl: return 9.0
    if "month" in sl: return 6.0
    if "quarter" in sl: return 4.0
    if "semi" in sl: return 3.0
    if "annual" in sl or "year" in sl: return 2.0
    return 3.0

def _score_coverage(s: str) -> float:
    score = GEOGRAPHIC_SCORES.get(s)
    if score is not None:
        return float(score)
    sl = s.lower()
    if "global" in sl or "worldwide" in sl: return 15.0
    if "asia" in sl: return 7.0
    if any(x in sl for x in ["eu", "europe", "us", "uk"]): return 6.0
    return 5.0

def _score_effort(s: str) -> float:
    """Ease of integration — higher = simpler."""
    sl = s.lower()
    if "rest api" in sl: return 15.0
    if "s3" in sl: return 12.0
    if "python" in sl or "library" in sl: return 12.0
    if "oauth" in sl: return 11.0
    if "csv" in sl or "download" in sl: return 9.0
    if "apify" in sl: return 7.0
    if "scrape" in sl or "puppeteer" in sl: return 5.0
    if "manual" in sl: return 2.0
    return 5.0

def _value_description(
    source: Dict, quality: str, freshness: str,
    priority: str, utility: str, modules: List[str]
) -> str:
    def get(k: str, alt: str = "") -> str:
        return str(source.get(k) or source.get(alt) or "").strip()

    name       = get("name", "Source Name")
    rationale  = get("rationale", "Rationale")
    geo        = get("geographic", "Geographic") or "Global"
    freq       = get("update_freq", "Update Freq")
    cost       = get("cost", "Cost")

    parts = []
    if rationale:
        parts.append(rationale.rstrip(".") + ".")
    if geo and freq:
        parts.append(f"{geo} coverage updated {freq.lower()}.")
    if "free" in cost.lower():
        parts.append("No-cost integration.")
    if quality in ("A+", "A"):
        parts.append("High data quality (A/A+ rated).")

    mod_label = ", ".join(modules[:3]) if modules else "platform"
    parts.append(f"Feeds: {mod_label}.")

    if priority == "P0":
        parts.append("Priority: P0 — integrate first.")
    elif priority == "P1":
        parts.append("Priority: P1 — next sprint.")

    return " ".join(parts)
