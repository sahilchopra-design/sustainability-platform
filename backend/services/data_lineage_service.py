"""
Data Lineage Service
======================
Active cross-module dependency tracking with full input -> transformation ->
output chains. Builds a directed acyclic graph (DAG) of all platform module
data flows, propagates data quality scores, and identifies lineage gaps.

Data Flow:
  1. MODULE_SIGNATURES registry defines I/O for each of 105 services
  2. MODULE_DEPENDENCIES defines directed edges (source -> target + field mapping)
  3. trace_lineage() walks the graph from any starting module to produce a
     complete chain with quality scores at each node
  4. find_gaps() scans all edges for missing/broken links

Quality Propagation:
  - Each node carries a quality score (0.0 - 1.0)
  - Downstream quality = min(upstream_quality * confidence_weight, own_quality)
  - Weakest-link flagging: any node below 0.3 triggers a warning

References:
  - BCBS 239 (Risk Data Aggregation and Risk Reporting)
  - PCAF Data Quality Score framework (DQS 1-5)
  - EBA GL/2020/06 (ICT and security risk management)
  - ISO 8000 (Data Quality)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("platform.data_lineage")


# ---------------------------------------------------------------------------
# Reference Data — Module I/O Signatures
# ---------------------------------------------------------------------------

MODULE_SIGNATURES: dict[str, dict] = {
    # ---- Emissions ----
    "carbon_calculator": {
        "label": "Carbon Calculator v1",
        "category": "emissions",
        "inputs": ["activity_data_kwh", "fuel_type", "fleet_km", "refrigerant_kg",
                    "electricity_kwh", "grid_region", "scope3_categories"],
        "outputs": ["scope1_total_tco2e", "scope2_location_tco2e", "scope2_market_tco2e",
                     "scope3_total_tco2e", "total_tco2e", "intensity_tco2e_per_m_revenue"],
        "reference_data": ["ghg_protocol_ef_scope1", "iea_grid_ef", "defra_conversion_factors"],
        "quality_indicators": ["data_completeness_pct", "scope_coverage"],
    },
    "carbon_calculator_v2": {
        "label": "Carbon Calculator v2",
        "category": "emissions",
        "inputs": ["organisation_id", "reporting_year", "fuel_consumption",
                    "electricity_kwh", "fleet_data", "refrigerant_data", "scope3_data"],
        "outputs": ["scope1_tco2e", "scope2_lb_tco2e", "scope2_mb_tco2e",
                     "scope3_tco2e", "total_ghg_tco2e", "intensity_revenue", "intensity_fte"],
        "reference_data": ["ghg_protocol_ef_scope1", "iea_grid_ef", "defra_conversion_factors",
                           "gwp_ar5_100yr"],
        "quality_indicators": ["data_completeness_pct", "verification_status"],
    },
    "supply_chain_scope3": {
        "label": "Supply Chain / Scope 3 Engine",
        "category": "emissions",
        "inputs": ["supplier_activities", "spend_data_eur", "commodity_types",
                    "transport_modes", "waste_streams"],
        "outputs": ["scope3_by_category", "supplier_risk_scores", "sbti_target_status",
                     "total_scope3_tco2e", "hotspot_categories"],
        "reference_data": ["ghg_protocol_scope3_ef", "exiobase_sector_ef", "sbti_sector_pathways"],
        "quality_indicators": ["supplier_data_coverage_pct", "spend_vs_activity_ratio"],
    },
    # ---- Credit Risk ----
    "pd_calculator": {
        "label": "PD Calculator",
        "category": "credit",
        "inputs": ["financial_ratios", "sector", "country", "rating",
                    "years_in_business", "revenue_eur"],
        "outputs": ["pd_1yr", "pd_lifetime", "rating_implied", "migration_matrix"],
        "reference_data": ["moodys_default_rates", "sp_transition_matrices",
                           "eba_benchmark_pd"],
        "quality_indicators": ["model_validation_date", "sample_size"],
    },
    "lgd_calculator": {
        "label": "LGD Calculator",
        "category": "credit",
        "inputs": ["collateral_type", "collateral_value_eur", "seniority",
                    "jurisdiction", "pd_1yr"],
        "outputs": ["lgd_pct", "lgd_downturn_pct", "recovery_rate", "cure_rate"],
        "reference_data": ["eba_lgd_floors", "collateral_haircuts", "recovery_benchmarks"],
        "quality_indicators": ["collateral_valuation_date", "recovery_data_depth"],
    },
    "ead_calculator": {
        "label": "EAD Calculator",
        "category": "credit",
        "inputs": ["facility_type", "drawn_amount_eur", "undrawn_amount_eur",
                    "ccf_model_type"],
        "outputs": ["ead_eur", "ccf_pct", "ead_stressed_eur"],
        "reference_data": ["crr2_ccf_sa", "irb_ccf_estimates"],
        "quality_indicators": ["facility_data_completeness"],
    },
    "ecl_climate_engine": {
        "label": "ECL Climate Engine",
        "category": "credit",
        "inputs": ["pd_1yr", "lgd_pct", "ead_eur", "sector", "country",
                    "climate_scenario", "carbon_intensity_tco2e"],
        "outputs": ["ecl_base_eur", "ecl_climate_adj_eur", "climate_overlay_eur",
                     "pd_climate_adj", "lgd_climate_adj", "ecl_stage"],
        "reference_data": ["ngfs_scenario_params", "eba_climate_risk_weights",
                           "sector_transition_risk_scores"],
        "quality_indicators": ["scenario_vintage", "overlay_methodology_version"],
    },
    # ---- Financed Emissions ----
    "pcaf_waci_engine": {
        "label": "PCAF WACI Engine",
        "category": "financed_emissions",
        "inputs": ["portfolio_holdings", "investee_emissions_tco2e",
                    "investee_revenue_eur", "attribution_factor"],
        "outputs": ["waci_tco2e_per_m", "financed_emissions_tco2e",
                     "portfolio_temperature_c", "data_quality_score_avg"],
        "reference_data": ["pcaf_asset_class_rules", "pcaf_dqs_criteria"],
        "quality_indicators": ["pcaf_dqs_distribution", "reported_vs_estimated_pct"],
    },
    # ---- PCAF-ECL Bridge ----
    "pcaf_ecl_bridge": {
        "label": "PCAF-ECL Bridge",
        "category": "cross_module",
        "inputs": ["pcaf_investee_profile", "dqs_score", "waci_tco2e",
                    "implied_temperature_c", "sbti_committed"],
        "outputs": ["ecl_climate_inputs", "scenario_weights", "transition_risk_level",
                     "carbon_price_sensitivity", "confidence_weighted_overlay"],
        "reference_data": ["dqs_confidence_weights", "temperature_scenario_weights",
                           "waci_transition_risk_map"],
        "quality_indicators": ["bridge_confidence_score"],
    },
    # ---- Climate / Nature Risk ----
    "scenario_analysis_engine": {
        "label": "Scenario Analysis Engine",
        "category": "scenarios",
        "inputs": ["entity_sector", "carbon_intensity", "geography",
                    "ngfs_scenario_id", "time_horizon_years"],
        "outputs": ["transition_risk_score", "physical_risk_score", "combined_risk_score",
                     "carbon_price_impact_eur", "stranded_asset_risk_pct",
                     "scenario_alignment_score"],
        "reference_data": ["ngfs_scenario_v4_params", "ipcc_rcp_pathways",
                           "iea_weo_projections"],
        "quality_indicators": ["scenario_vintage", "parameter_completeness"],
    },
    "nature_risk_calculator": {
        "label": "Nature Risk Calculator",
        "category": "nature",
        "inputs": ["location_lat", "location_lng", "sector", "land_use_ha",
                    "water_consumption_m3", "biodiversity_proximity_km"],
        "outputs": ["nature_risk_score", "water_risk_score", "biodiversity_score",
                     "tnfd_leap_priority", "dependency_score", "impact_score"],
        "reference_data": ["wri_aqueduct_water_stress", "ibat_protected_areas",
                           "encore_dependency_matrix"],
        "quality_indicators": ["location_precision", "temporal_coverage"],
    },
    "stranded_asset_calculator": {
        "label": "Stranded Asset Calculator",
        "category": "risk",
        "inputs": ["asset_type", "reserves_mt", "production_rate",
                    "breakeven_price_eur", "decommission_year"],
        "outputs": ["stranding_probability", "stranding_year_median",
                     "value_at_risk_eur", "write_down_eur", "transition_cost_eur"],
        "reference_data": ["iea_nze_demand_curves", "carbon_budget_remaining_gt",
                           "technology_disruption_curves"],
        "quality_indicators": ["reserve_audit_date", "cost_curve_vintage"],
    },
    # ---- Regulatory ----
    "csrd_auto_populate": {
        "label": "CSRD Auto-Population Engine",
        "category": "regulatory",
        "inputs": ["entity_name", "module_outputs_list", "reporting_year"],
        "outputs": ["populated_dps", "population_rate_pct", "gaps",
                     "esrs_coverage", "readiness_rating"],
        "reference_data": ["esrs_data_point_mappings", "esrs_minimums_per_standard"],
        "quality_indicators": ["population_rate_pct", "confidence_distribution"],
    },
    "gar_calculator": {
        "label": "EU Taxonomy GAR Calculator",
        "category": "regulatory",
        "inputs": ["asset_book", "activity_classification", "turnover_eur",
                    "capex_eur", "opex_eur"],
        "outputs": ["gar_turnover_pct", "gar_capex_pct", "gar_opex_pct",
                     "taxonomy_eligible_pct", "taxonomy_aligned_pct",
                     "dnsh_pass_rate"],
        "reference_data": ["eu_taxonomy_tsc_climate", "eu_taxonomy_tsc_environment",
                           "nace_activity_classification"],
        "quality_indicators": ["activity_coverage_pct", "tsc_assessment_completeness"],
    },
    "sfdr_report_generator": {
        "label": "SFDR PAI Report Generator",
        "category": "regulatory",
        "inputs": ["portfolio_holdings", "investee_data", "reporting_period"],
        "outputs": ["pai_1_ghg_scope123", "pai_2_carbon_footprint",
                     "pai_3_ghg_intensity", "pai_4_fossil_exposure_pct",
                     "pai_count_flagged", "entity_pai_table"],
        "reference_data": ["sfdr_rts_pai_definitions", "pai_calculation_methodology"],
        "quality_indicators": ["investee_coverage_pct", "data_source_quality"],
    },
    # ---- Real Estate ----
    "real_estate_valuation_engine": {
        "label": "Real Estate Valuation Engine",
        "category": "valuation",
        "inputs": ["property_type", "location", "gla_sqm", "noi_eur",
                    "cap_rate_pct", "epc_rating", "comparables"],
        "outputs": ["market_value_eur", "income_value_eur", "cost_value_eur",
                     "sales_comparison_value_eur", "green_premium_pct"],
        "reference_data": ["rics_valuation_standards", "ivsc_framework",
                           "comparable_transactions"],
        "quality_indicators": ["valuation_date", "comparable_depth"],
    },
    "crrem_stranding_engine": {
        "label": "CRREM Stranding Engine",
        "category": "real_estate",
        "inputs": ["property_type", "country", "energy_intensity_kwh_sqm",
                    "carbon_intensity_kgco2_sqm", "current_epc"],
        "outputs": ["stranding_year", "excess_emissions_kgco2", "retrofit_cost_eur",
                     "pathway_aligned", "decarbonisation_rate_required_pct"],
        "reference_data": ["crrem_v2_decarbonisation_curves", "crrem_country_pathways",
                           "epc_rating_thresholds"],
        "quality_indicators": ["pathway_version", "energy_data_source"],
    },
    # ---- Entity 360 ----
    "entity360": {
        "label": "Entity 360 Engine",
        "category": "cross_module",
        "inputs": ["entity_id", "entity_type", "sector", "reporting_year",
                    "module_data_map"],
        "outputs": ["composite_risk_score", "risk_band", "esg_rating",
                     "data_completeness_pct", "regulatory_status",
                     "data_gaps", "recommendations"],
        "reference_data": ["module_registry", "entity_types", "sector_map"],
        "quality_indicators": ["modules_available_count", "data_completeness_pct"],
    },
    # ---- PE / Project Finance ----
    "pe_deal_engine": {
        "label": "PE Deal Engine",
        "category": "private_equity",
        "inputs": ["deal_type", "entry_ev_eur", "ebitda_eur", "leverage_x",
                    "hold_period_years", "sector", "esg_score"],
        "outputs": ["irr_base_pct", "irr_upside_pct", "irr_downside_pct",
                     "moic", "esg_value_creation_eur", "exit_ev_eur"],
        "reference_data": ["pe_benchmark_returns", "sector_ebitda_multiples",
                           "esg_premium_factors"],
        "quality_indicators": ["financial_data_audited", "esg_data_verified"],
    },
    "project_finance_engine": {
        "label": "Project Finance Engine",
        "category": "infrastructure",
        "inputs": ["project_type", "capex_eur", "opex_annual_eur",
                    "revenue_model", "debt_structure", "concession_years"],
        "outputs": ["project_irr_pct", "equity_irr_pct", "dscr_min",
                     "llcr", "payback_years", "npv_eur"],
        "reference_data": ["infrastructure_benchmarks", "country_risk_premiums",
                           "renewable_lcoe_curves"],
        "quality_indicators": ["feasibility_study_date", "financial_model_audit"],
    },
    # ---- China Trade / Geopolitical ----
    "china_trade_engine": {
        "label": "China Trade Engine",
        "category": "geopolitical",
        "inputs": ["entity_name", "sector", "trade_exposure_eur",
                    "supply_chain_china_pct", "ets_coverage"],
        "outputs": ["cbam_exposure_eur", "tariff_risk_score", "ets_cost_eur",
                     "supply_chain_resilience_score", "regulatory_alignment"],
        "reference_data": ["cets_price_history", "cbam_product_categories",
                           "sse_szse_disclosure_requirements", "ngfs_china_scenarios"],
        "quality_indicators": ["trade_data_vintage", "ets_price_date"],
    },
    # ---- Insurance ----
    "insurance_climate_risk": {
        "label": "Insurance Climate Risk",
        "category": "insurance",
        "inputs": ["portfolio_type", "geography", "peril_types",
                    "exposure_eur", "loss_history"],
        "outputs": ["climate_loss_ratio_adj", "nat_cat_aal_eur",
                     "combined_ratio_climate_delta", "capital_add_on_pct"],
        "reference_data": ["ipcc_hazard_multipliers", "cat_model_calibration",
                           "solvency2_nat_cat_factors"],
        "quality_indicators": ["loss_history_years", "cat_model_version"],
    },
    # ---- Mining / Agriculture ----
    "mining_risk_calculator": {
        "label": "Mining Risk Calculator",
        "category": "mining",
        "inputs": ["mineral_type", "reserves_mt", "extraction_rate",
                    "tailings_volume_m3", "water_usage_ml"],
        "outputs": ["environmental_liability_eur", "closure_cost_eur",
                     "tailings_risk_score", "water_stress_score",
                     "community_impact_score"],
        "reference_data": ["icmm_sustainability_framework", "gistm_standards",
                           "mineral_price_forecasts"],
        "quality_indicators": ["reserve_certification_date", "environmental_audit_date"],
    },
    "agriculture_risk_calculator": {
        "label": "Agriculture Risk Calculator",
        "category": "agriculture",
        "inputs": ["crop_types", "land_area_ha", "region", "irrigation_pct",
                    "fertiliser_use_kg_ha"],
        "outputs": ["yield_risk_score", "water_stress_score",
                     "soil_degradation_score", "ghg_intensity_tco2_ha",
                     "climate_adaptation_score"],
        "reference_data": ["fao_crop_calendars", "ipcc_agriculture_ef",
                           "wri_water_stress_baseline"],
        "quality_indicators": ["yield_data_years", "soil_survey_date"],
    },
    # ---- Sustainability Calculators ----
    "sustainability_calculator": {
        "label": "Sustainability Calculator",
        "category": "sustainability",
        "inputs": ["framework_id", "building_data", "operational_data",
                    "management_data"],
        "outputs": ["gresb_score", "leed_points", "breeam_rating",
                     "well_score", "nabers_stars", "casbee_rank"],
        "reference_data": ["gresb_benchmark_2024", "leed_v4_credits",
                           "breeam_2018_criteria", "well_v2_features"],
        "quality_indicators": ["certification_date", "data_verification_level"],
    },
    # ---- Insurance ----
    "insurance_risk_engine": {
        "label": "Insurance Risk Engine",
        "category": "insurance",
        "inputs": ["country_iso3", "sex", "warming_c", "total_lives",
                    "avg_sum_assured_eur", "avg_age", "natcat_exposure_eur",
                    "natcat_country", "perils", "gwp_eur", "net_earned_premium_eur",
                    "claims_incurred_eur", "expenses_eur", "reinsurance_layers",
                    "health_members", "claim_cost_per_member_eur"],
        "outputs": ["mortality_delta_pct", "life_expectancy_climate_adj",
                     "best_estimate_liability_eur", "longevity_scr_eur",
                     "nat_cat_scr_diversified_eur", "nat_cat_aal_eur",
                     "climate_frequency_multiplier", "climate_severity_multiplier",
                     "combined_ratio_climate_adj_pct", "underwriting_profit_eur",
                     "net_retained_eur", "cascade_failure_prob",
                     "medical_trend_effective_pct", "total_capital_at_risk_eur",
                     "aggregate_risk_score", "risk_rating"],
        "reference_data": ["who_mortality_tables", "ipcc_ar6_damage_functions",
                           "solvency2_nat_cat_factors"],
        "quality_indicators": ["mortality_data_year", "peril_model_vintage",
                                "reinsurance_confirmation_status"],
    },
    # ---- Banking Risk ----
    "banking_risk_engine": {
        "label": "Banking Risk Engine",
        "category": "banking",
        "inputs": ["total_exposure_eur", "portfolio_size", "avg_rating", "collateral_type",
                    "avg_maturity_years", "stage2_pct", "stage3_pct", "warming_c",
                    "hqla_holdings", "funding_sources", "asset_book",
                    "trading_book_eur", "equity_exposure_eur", "fx_exposure_eur",
                    "interest_rate_dv01_eur", "portfolio_volatility_pct", "stressed_volatility_pct",
                    "rate_shock_bps",
                    "gross_income_year1_eur", "gross_income_year2_eur", "gross_income_year3_eur",
                    "business_line_income",
                    "counterparty_countries", "exposure_by_country",
                    "cet1_capital_eur", "at1_capital_eur", "tier2_capital_eur",
                    "credit_rwa_eur", "market_rwa_eur", "operational_rwa_eur",
                    "leverage_exposure_eur", "countercyclical_buffer_pct"],
        "outputs": ["total_ecl_eur", "ecl_coverage_ratio_pct", "climate_overlay_eur",
                     "risk_weighted_assets_eur", "credit_risk_capital_eur",
                     "lcr_pct", "lcr_compliant", "nsfr_pct", "nsfr_compliant",
                     "var_99_1d_eur", "var_99_10d_eur", "stressed_var_99_10d_eur",
                     "expected_shortfall_97_5_eur", "market_risk_capital_eur",
                     "bia_charge_eur", "tsa_charge_eur", "operational_risk_capital_eur",
                     "overall_aml_risk_score", "grey_list_exposures", "black_list_exposures",
                     "cet1_ratio_pct", "tier1_ratio_pct", "total_capital_ratio_pct",
                     "leverage_ratio_pct", "surplus_to_mda_eur", "compliant",
                     "overall_risk_rating", "total_capital_requirement_eur"],
        "reference_data": ["pd_term_structures_by_rating", "lgd_by_collateral_type",
                           "basel3_risk_weights", "tsa_beta_factors",
                           "hqla_haircuts", "lcr_outflow_rates", "nsfr_factors",
                           "fatf_country_risk_tiers", "fatf_grey_list", "fatf_black_list"],
        "quality_indicators": ["rating_coverage_pct", "collateral_data_completeness",
                                "fatf_list_vintage", "capital_reporting_date"],
    },
    # ---- CBAM ----
    "cbam_calculator": {
        "label": "CBAM Calculator",
        "category": "regulatory",
        "inputs": ["product_cn_code", "origin_country", "mass_tonnes",
                    "embedded_emissions_tco2", "carbon_price_paid_eur"],
        "outputs": ["cbam_certificates_required", "cbam_cost_eur",
                     "effective_carbon_price_delta_eur",
                     "art7_obligation_status", "art31_financial_impact_eur"],
        "reference_data": ["cbam_product_registry", "eu_ets_benchmark_ef",
                           "third_country_carbon_prices"],
        "quality_indicators": ["emission_data_source", "verification_status"],
    },
    # ---- Asset Management Engine ----
    "am_esg_attribution": {
        "label": "AM ESG Attribution",
        "category": "asset_management",
        "inputs": ["holdings_weights", "holdings_esg_scores", "holdings_returns",
                    "benchmark_esg_score", "sector_allocations"],
        "outputs": ["active_return_bps", "esg_quality_contribution_bps",
                     "portfolio_esg_score", "sector_attribution_bps",
                     "factor_contributions"],
        "reference_data": ["fama_french_factor_premia", "sector_esg_benchmarks"],
        "quality_indicators": ["holding_coverage_pct", "esg_data_recency"],
    },
    "am_paris_alignment": {
        "label": "AM Paris Alignment (PACTA)",
        "category": "asset_management",
        "inputs": ["holdings_weights", "holdings_carbon_intensity",
                    "target_pathway", "base_year"],
        "outputs": ["portfolio_temperature_c", "alignment_gap_c",
                     "aligned_weight_pct", "misaligned_weight_pct",
                     "weighted_carbon_intensity", "sector_temperatures"],
        "reference_data": ["sbti_sector_pathways", "iea_nze_pathway",
                           "ipcc_carbon_budgets"],
        "quality_indicators": ["carbon_data_coverage_pct", "pathway_vintage"],
    },
    "am_green_bond_screening": {
        "label": "AM Green Bond Screening (ICMA/EU GBS)",
        "category": "asset_management",
        "inputs": ["bond_id", "issuer_name", "use_of_proceeds",
                    "taxonomy_aligned_pct", "external_review",
                    "impact_reporting", "dnsh_assessed"],
        "outputs": ["icma_eligible", "eu_gbs_eligible", "greenium_bps",
                     "overall_score", "disqualification_reasons"],
        "reference_data": ["icma_gbs_criteria", "eu_gbs_requirements",
                           "greenium_benchmarks"],
        "quality_indicators": ["external_review_status", "reporting_completeness"],
    },
    "am_climate_spreads": {
        "label": "AM Climate-Adjusted Spreads",
        "category": "asset_management",
        "inputs": ["issuer_id", "sector", "rating", "base_spread_bps",
                    "carbon_intensity_tco2e_m", "transition_risk_score",
                    "carbon_price_eur", "warming_scenario"],
        "outputs": ["climate_adjusted_spread_bps", "carbon_risk_premium_bps",
                     "transition_risk_premium_bps", "greenium_adjustment_bps",
                     "spread_delta_bps"],
        "reference_data": ["sector_carbon_intensity_benchmarks",
                           "transition_spread_factor_table",
                           "greenium_by_sector"],
        "quality_indicators": ["spread_data_source", "carbon_data_quality"],
    },
    "am_lp_analytics": {
        "label": "AM LP Analytics",
        "category": "asset_management",
        "inputs": ["fund_aum_eur", "investor_commitments",
                    "investor_types", "liquid_assets_pct",
                    "side_pocket_pct", "redemption_terms"],
        "outputs": ["hhi_concentration", "top5_concentration_pct",
                     "lcr_pct", "lcr_compliant", "stress_lcr_pct",
                     "key_person_risk_score"],
        "reference_data": ["aifmd_liquidity_requirements",
                           "institutional_investor_benchmarks"],
        "quality_indicators": ["investor_data_completeness", "aum_reporting_date"],
    },
    "am_optimisation": {
        "label": "AM ESG-Constrained Optimisation",
        "category": "asset_management",
        "inputs": ["holdings_weights", "holdings_returns", "holdings_esg_scores",
                    "holdings_carbon_intensity", "risk_free_rate",
                    "constraints_min_esg", "constraints_max_carbon",
                    "excluded_sectors", "max_tracking_error_pct"],
        "outputs": ["optimised_weights", "portfolio_return_pct",
                     "portfolio_risk_pct", "sharpe_ratio",
                     "tracking_error_pct", "esg_improvement_pct",
                     "carbon_reduction_pct"],
        "reference_data": ["covariance_estimation_params",
                           "sector_esg_floors"],
        "quality_indicators": ["return_data_length", "covariance_estimation_quality"],
    },
    # ---- Agriculture Risk Engine (Expanded) ----
    "agriculture_methane_intensity": {
        "label": "Livestock Methane Intensity (IPCC Tier 1)",
        "category": "agriculture",
        "inputs": ["entity_id", "livestock_type", "herd_size",
                    "feed_system", "region", "manure_management",
                    "current_abatement"],
        "outputs": ["total_ch4_tonnes_yr", "total_tco2e_yr",
                     "intensity_kgch4_per_head", "enteric_ch4",
                     "manure_ch4", "max_abatement_potential_pct",
                     "applicable_abatement_options"],
        "reference_data": ["ipcc_enteric_ch4_factors", "ipcc_manure_ch4_factors",
                           "ch4_gwp_ar5", "abatement_option_catalogue"],
        "quality_indicators": ["herd_data_source", "emission_factor_tier"],
    },
    "agriculture_disease_outbreak": {
        "label": "Disease Outbreak Risk (OIE/WOAH)",
        "category": "agriculture",
        "inputs": ["entity_id", "species", "herd_size", "herd_value_eur",
                    "biosecurity_level", "regional_disease_history",
                    "vaccination_programme", "climate_warming_c"],
        "outputs": ["combined_outbreak_prob_annual", "expected_annual_loss_eur",
                     "worst_case_loss_eur", "overall_disease_risk_score",
                     "risk_category", "disease_profiles"],
        "reference_data": ["oie_woah_disease_profiles", "biosecurity_adjustment_factors",
                           "climate_disease_multipliers"],
        "quality_indicators": ["disease_data_vintage", "biosecurity_assessment_date"],
    },
    "agriculture_bng": {
        "label": "Biodiversity Net Gain (DEFRA Metric 4.0)",
        "category": "agriculture",
        "inputs": ["entity_id", "site_area_ha", "baseline_habitats",
                    "proposed_habitats", "development_type",
                    "mandatory_gain_pct"],
        "outputs": ["baseline_habitat_units", "proposed_habitat_units",
                     "net_gain_pct", "meets_mandatory_requirement",
                     "bng_credits_required", "credit_cost_eur",
                     "risk_rating"],
        "reference_data": ["defra_metric_4_habitat_types",
                           "habitat_condition_multipliers",
                           "bng_credit_market_prices"],
        "quality_indicators": ["habitat_survey_date", "metric_version"],
    },
    # ---- Climate Risk ----
    "nace_cprs_mapper": {
        "label": "NACE-CPRS-IAM Sector Mapper",
        "category": "climate_risk",
        "inputs": ["nace_code", "nace_description", "revenue_share",
                    "ghg_intensity_tco2e_per_eur_m"],
        "outputs": ["cprs_category", "cprs_risk_weight", "iam_sectors",
                     "ghg_intensity_bucket", "sector_risk_score",
                     "dominant_cprs_category"],
        "reference_data": ["nace_rev2_classification", "cprs_battiston_2017",
                           "iam_sector_mapping", "ghg_intensity_buckets"],
        "quality_indicators": ["nace_code_resolution", "revenue_share_completeness"],
    },
    "climate_physical_risk_engine": {
        "label": "Climate Physical Risk Engine",
        "category": "climate_risk",
        "inputs": ["entity_id", "entity_name", "entity_type", "sector",
                    "asset_value_eur", "lat", "lon", "scenario_ssp",
                    "time_horizon", "building_age_years", "elevation_m",
                    "has_adaptation", "asset_type"],
        "outputs": ["physical_cvar_eur", "physical_risk_score", "risk_rating",
                     "expected_annual_loss_eur", "pd_adjustment", "lgd_adjustment",
                     "top_hazards", "hazard_scores", "exposure_result",
                     "vulnerability_by_hazard", "damage_by_hazard"],
        "reference_data": ["ipcc_ar6_hazard_types", "sector_vulnerability_matrix_20x13",
                           "damage_function_coefficients", "ssp_scenario_severity",
                           "time_horizon_scaling"],
        "quality_indicators": ["location_precision", "sector_match_quality",
                               "scenario_coverage"],
    },
    "climate_transition_risk_engine": {
        "label": "Climate Transition Risk Engine",
        "category": "climate_risk",
        "inputs": ["entity_id", "entity_name", "nace_codes_with_revenue",
                    "scope1_tco2e", "scope2_tco2e", "scope3_tco2e",
                    "revenue_eur", "fossil_reserve_value", "current_emission_intensity",
                    "readiness_data", "is_cbam_sector", "home_carbon_price",
                    "fossil_exposure_pct"],
        "outputs": ["composite_transition_score", "transition_risk_rating",
                     "category_scores", "max_transition_cvar_eur",
                     "max_pd_adjustment", "max_lgd_adjustment",
                     "sector_classification", "carbon_pricing_results",
                     "stranded_asset_result", "alignment_result",
                     "scenario_stress_results"],
        "reference_data": ["ngfs_phase5_scenarios", "iea_nze_pathway",
                           "tcfd_category_descriptions", "cbam_covered_sectors",
                           "writedown_curve_functions"],
        "quality_indicators": ["nace_resolution", "emissions_data_quality",
                               "readiness_indicator_coverage"],
    },
    # ---- Factor Overlays (Chunk 6) ----
    "factor_overlay_engine": {
        "label": "Factor Overlay Engine",
        "category": "overlay",
        "inputs": ["entity_id", "country_code", "sector_nace", "base_metrics",
                    "scenario", "as_of_date"],
        "outputs": ["enhanced_metrics", "esg_factors", "geo_factors", "tech_factors",
                     "composite_adjustment", "confidence", "audit_trail"],
        "reference_data": ["esg_transition_pd_multiplier", "green_bond_premium_bps",
                           "biodiversity_natcat_amplifier", "esg_alpha_decomposition",
                           "sovereign_risk_scores", "fx_climate_correlation",
                           "sanctions_cascade", "political_stability",
                           "food_security_index", "energy_independence",
                           "automation_disruption", "ai_adoption_score",
                           "digital_readiness", "smart_building_uplift",
                           "h2_blending_economics", "precision_ag_adoption",
                           "stranded_asset_tech_filter", "parametric_pricing_adj",
                           "air_quality_mortality", "medical_advancement_longevity",
                           "carbon_reduction_valuation_uplift", "green_premium_pct",
                           "methane_abatement_curve", "deforestation_free_premium",
                           "csrd_gap_closure_rates", "regulatory_complexity",
                           "fintech_nim_disruption", "supply_chain_digitisation",
                           "ai_assurance_confidence", "carbon_border_alignment",
                           "migration_mortality_adjustment"],
        "quality_indicators": ["factor_coverage", "country_data_availability",
                               "sector_data_availability", "overlay_confidence"],
    },
    # ---- Residential Real Estate ----
    "residential_re_engine": {
        "label": "Residential Real Estate Engine",
        "category": "real_estate",
        "inputs": ["property_id", "property_type", "floor_area_m2", "bedrooms", "bathrooms",
                    "age_years", "garden_m2", "parking_spaces", "epc_rating", "energy_kwh_m2_yr",
                    "in_flood_zone", "proximity_transport_km", "market_value_eur",
                    "mortgage_ltv", "mortgage_balance_eur", "country"],
        "outputs": ["hedonic_value_eur", "value_per_m2_eur", "epc_premium_pct", "flood_discount_pct",
                     "crrem_stranding_year", "years_to_stranding", "mees_compliant",
                     "retrofit_cost_to_c_eur", "retrofit_cost_to_b_eur",
                     "climate_adjusted_value_eur", "climate_ltv", "ltv_stress_bps",
                     "total_mortgage_exposure_eur", "avg_climate_ltv", "epc_distribution",
                     "stranding_before_2030_count", "total_retrofit_cost_to_c_eur",
                     "decarb_total_capex_eur", "decarb_payback_years", "co2_reduction_tco2_yr"],
        "reference_data": ["epc_energy_intensity_sap", "mees_timelines_gb_nl_fr_de",
                           "crrem_v2_3_residential_pathway", "hedonic_coefficients",
                           "retrofit_cost_per_m2", "decarb_measures_catalogue"],
        "quality_indicators": ["epc_data_available", "market_value_source", "energy_metered_vs_estimated",
                               "flood_zone_data_source"],
    },
    # ---- RICS Red Book ESG ----
    "rics_esg_engine": {
        "label": "RICS Red Book ESG Compliance Engine",
        "category": "real_estate",
        "inputs": ["property_id", "property_type", "country", "valuation_purpose",
                    "epc_rating", "epc_score", "green_certification", "green_cert_level",
                    "energy_kwh_m2_yr", "scope12_tco2e", "crrem_stranding_year",
                    "flood_risk_zone", "heat_risk_score", "biodiversity_proximity",
                    "indoor_air_quality", "accessibility_compliant", "iso14001_certified",
                    "gresb_score", "green_premium_pct", "brown_discount_pct",
                    "transition_risk_adjustment_pct", "physical_risk_adjustment_pct",
                    "num_esg_comparables", "comparable_evidence_quality"],
        "outputs": ["compliance_pct", "compliance_band", "checklist", "esg_narrative",
                     "materiality_scores", "material_factors", "uncertainty_pct",
                     "uncertainty_band", "uncertainty_narrative", "recommendations"],
        "reference_data": ["rics_red_book_2022_ps1_ps2", "rics_vps4_bases_of_value",
                           "rics_vpga12_esg_sustainability", "rics_vpg3_uncertainty",
                           "ivs_104_400_esg_integration", "esg_materiality_factors"],
        "quality_indicators": ["epc_data_provided", "certification_data_provided",
                               "energy_data_source", "comparable_evidence_quality"],
    },
    # ---- Validation Summary ----
    "validation_summary_engine": {
        "label": "Validation Summary Engine",
        "category": "cross_cutting",
        "inputs": ["engine_name", "engine_version", "methodology_reference",
                    "result_dict", "inputs_captured", "parameters_applied",
                    "data_sources", "data_quality_flags", "dqs_scores",
                    "input_completeness_pct", "methodology_maturity"],
        "outputs": ["validation_summary", "confidence_score", "confidence_band",
                     "outputs_hash_sha256", "methodology_reference", "timestamp_utc",
                     "data_quality_flags", "bcbs239_compliance_fields"],
        "reference_data": ["methodology_registry_25_engines", "pcaf_dqs_confidence_map",
                           "bcbs239_principle_6_accuracy"],
        "quality_indicators": ["dqs_avg", "input_completeness", "methodology_maturity"],
    },
    # ---- Nature-RE Integration ----
    "nature_re_integration_engine": {
        "label": "Nature-RE Integration Engine",
        "category": "real_estate",
        "inputs": ["property_id", "property_type", "market_value_eur", "noi_eur",
                    "cap_rate_pct", "latitude", "longitude",
                    "leap_overall_score", "leap_risk_rating",
                    "water_baseline_score", "water_projected_2030", "water_projected_2050",
                    "biodiversity_impact_score", "biodiversity_direct_overlaps",
                    "site_area_hectares", "habitat_type", "bng_units_required"],
        "outputs": ["nature_adjusted_value_eur", "nature_haircut_pct", "water_noi_adjustment_pct",
                     "biodiversity_cap_rate_adj_bps", "bng_capex_estimate_eur",
                     "composite_nature_score", "composite_nature_band",
                     "eu_taxonomy_nature_dnsh_pass", "nature_narrative"],
        "reference_data": ["tnfd_leap_v1_framework", "wri_aqueduct_water_risk",
                           "defra_biodiversity_metric_4_0", "eu_taxonomy_article_11_dnsh",
                           "rics_vpga12_esg", "ipbes_global_assessment"],
        "quality_indicators": ["leap_data_available", "water_data_source",
                               "biodiversity_spatial_data", "coordinate_precision"],
    },
    # ---- Spatial Hazard ----
    "spatial_hazard_service": {
        "label": "Spatial Hazard Service",
        "category": "cross_cutting",
        "inputs": ["latitude", "longitude", "country", "user_overrides"],
        "outputs": ["flood_zone", "flood_depth_100yr_m", "heat_days_above_35c",
                     "wildfire_proximity_km", "coastal_proximity_km", "subsidence_risk",
                     "water_stress_score", "sea_level_rise_cm_2050",
                     "cyclone_exposure", "permafrost_risk"],
        "reference_data": ["country_hazard_profiles_15", "wri_aqueduct_water_stress",
                           "ea_fema_flood_zones", "jrc_peseta_iv",
                           "ipcc_ar6_wg2_hazard_framework"],
        "quality_indicators": ["spatial_precision", "coordinate_available", "confidence_band"],
    },
    # ---- Technology Sector ----
    "technology_risk_engine": {
        "label": "Technology Sector Risk Engine",
        "category": "sector",
        "inputs": ["facility_name", "it_load_kw", "total_energy_mwh", "cooling_type",
                    "cloud_provider", "cloud_spend_eur", "workload_hours",
                    "model_type", "training_hours_gpu", "inference_requests_per_day",
                    "wafer_starts_per_month", "process_node_nm", "minerals_used",
                    "hardware_inventory", "avg_device_age_years", "recycling_partner"],
        "outputs": ["pue", "wue_l_kwh", "cue", "scope2_tco2e", "scope2_market_tco2e",
                     "embodied_carbon_tco2e", "annual_water_m3", "cloud_scope3_tco2e",
                     "ai_training_tco2e", "ai_inference_annual_tco2e",
                     "semiconductor_water_m3", "mineral_supply_hhi",
                     "ewaste_tonnes", "circularity_score",
                     "eed_compliant", "iso30134_kpis", "sci_score",
                     "composite_esg_score", "csrd_e1_datapoints", "csrd_e3_datapoints",
                     "csrd_e5_datapoints"],
        "reference_data": ["iea_grid_ef_2024", "cloud_provider_pue", "ai_training_benchmarks",
                           "semiconductor_water_intensity", "rare_earth_concentration_hhi",
                           "ewaste_recycling_rates", "pue_benchmarks", "wue_benchmarks",
                           "eu_eed_recast_2023_1791"],
        "quality_indicators": ["metered_vs_estimated", "provider_disclosure_level",
                               "iso30134_certification", "data_centre_count"],
    },
    # ---- Regulatory Report Compiler ----
    "regulatory_report_compiler": {
        "label": "Regulatory Report Compiler",
        "category": "regulatory",
        "inputs": ["entity_data", "fund_data", "period_start", "period_end",
                    "scope1_tco2e", "scope2_tco2e", "scope3_tco2e",
                    "pai_indicators", "taxonomy_alignment", "brsr_section_a",
                    "brsr_section_b", "brsr_principles", "brsr_core_attributes"],
        "outputs": ["compiled_report", "overall_completeness_pct", "overall_status",
                     "sections", "gaps_summary", "recommendations",
                     "gri_esrs_cross_reference", "brsr_core_completeness_pct"],
        "reference_data": ["tcfd_11_recommendations", "sfdr_14_pai_indicators",
                           "gri_305_disclosures", "sec_climate_items_1500_1507",
                           "apra_cpg229_sections", "issb_s1_s2_structure",
                           "brsr_9_principles", "brsr_core_9_attributes",
                           "brsr_gri_esrs_mapping"],
        "quality_indicators": ["framework_count_supported", "cross_reference_coverage",
                               "auto_population_sources"],
    },
    # ---- EUDR Compliance Engine ----
    "eudr_engine": {
        "label": "EUDR Compliance Engine",
        "category": "regulatory",
        "inputs": ["operator_id", "operator_name", "operator_type",
                    "commodities", "countries_of_origin", "hs_code",
                    "geolocation_latitude", "geolocation_longitude", "geolocation_type",
                    "plot_area_ha", "supplier_name", "supplier_address",
                    "production_date", "quantity_kg",
                    "local_law_evidence", "deforestation_free_evidence",
                    "certifications", "independent_audit", "satellite_monitoring"],
        "outputs": ["overall_compliance_score", "compliance_status", "due_diligence_level",
                     "information_score", "risk_assessment_score", "risk_mitigation_score",
                     "traceability_score", "country_risk_tier", "gaps",
                     "recommendations", "remediation_plan", "statement_ready",
                     "esrs_e4_linkage", "eu_taxonomy_biodiversity_dnsh",
                     "enforcement_deadline", "days_until_deadline"],
        "reference_data": ["eudr_annex_i_commodities_7",
                           "eudr_country_benchmarks_art29",
                           "eudr_hs_cn_code_mappings",
                           "certification_schemes_9",
                           "enforcement_timeline_milestones",
                           "eudr_cross_framework_esrs_e4_gri_taxonomy"],
        "quality_indicators": ["commodity_count_in_scope", "country_benchmark_coverage",
                               "geolocation_precision", "evidence_count"],
    },
    # ---- EU ETS Phase 4 Engine ----
    "eu_ets_engine": {
        "label": "EU ETS Phase 4 Engine",
        "category": "regulatory",
        "inputs": ["installation_id", "sector", "product_benchmark", "year",
                    "historical_activity_level", "carbon_leakage_listed",
                    "carbon_price_eur", "verified_emissions_tco2",
                    "fuel_type", "annual_fuel_volume_litres"],
        "outputs": ["final_allocation_tco2", "auction_exposure_tco2", "auction_cost_eur",
                     "compliance_status", "surplus_deficit_tco2", "penalty_exposure_eur",
                     "price_forecast_by_year", "cap_trajectory",
                     "ets2_allowance_cost_eur", "ets2_readiness_score"],
        "reference_data": ["eu_ets_product_benchmarks_2021_927",
                           "eu_ets_cap_parameters_lrf",
                           "carbon_price_scenarios_5",
                           "cbam_phaseout_schedule_2026_2035",
                           "carbon_leakage_tiers",
                           "ets2_fuel_emission_factors"],
        "quality_indicators": ["benchmark_version", "scenario_count", "cbam_year_range"],
    },
    # ---- CSDDD Engine (Directive 2024/1760) ----
    "csddd_engine": {
        "label": "EU CSDDD Engine",
        "category": "regulatory",
        "inputs": ["entity_name", "is_eu_company", "employees", "net_turnover_eur",
                    "eu_generated_turnover_eur", "nace_codes", "countries_of_operation",
                    "supplier_countries", "forced_labour_risk", "child_labour_risk",
                    "deforestation_exposure", "conflict_minerals_exposure",
                    "osh_incidents_per_1000", "water_stress_exposure", "ghg_intensity_high",
                    "dd_policy_integrated", "impact_identification_score",
                    "prevention_mitigation_score", "remediation_score",
                    "stakeholder_engagement_score", "monitoring_score",
                    "climate_plan_exists", "climate_plan_paris_aligned",
                    "grievance_mechanism_operational", "director_dd_oversight"],
        "outputs": ["in_scope", "scope_group", "applies_from", "high_risk_sectors",
                     "identified_impacts", "total_impacts", "critical_impacts", "risk_score",
                     "overall_score", "compliance_status", "climate_transition_plan_score",
                     "climate_plan_gaps", "director_duty_assessment",
                     "grievance_mechanism_status", "penalty_exposure",
                     "cross_framework_linkage", "eudr_overlap",
                     "value_chain_mapping_completeness", "recommendations"],
        "reference_data": ["csddd_scope_thresholds_6_groups",
                           "adverse_impact_categories_18",
                           "dd_obligation_categories_9",
                           "climate_transition_plan_requirements_8",
                           "penalty_framework_art30_33",
                           "high_risk_sectors_8_nace"],
        "quality_indicators": ["impact_identification_coverage", "value_chain_mapping_depth",
                               "grievance_mechanism_operational", "climate_plan_completeness"],
    },
    # ---- Sovereign Climate Risk Engine ----
    "sovereign_climate_risk_engine": {
        "label": "Sovereign Climate Risk Engine",
        "category": "climate_risk",
        "inputs": ["country_iso2", "scenario", "horizon",
                    "physical_risk_override", "transition_readiness_override",
                    "portfolio_name", "holdings"],
        "outputs": ["physical_risk_score", "transition_risk_score",
                     "fiscal_vulnerability_score", "adaptation_readiness_score",
                     "composite_climate_risk_score", "baseline_rating",
                     "climate_adjusted_rating", "notch_adjustment",
                     "climate_spread_delta_bps", "risk_decomposition",
                     "nd_gain_score", "ndc_ambition_score",
                     "weighted_avg_climate_risk", "total_climate_var_usd",
                     "risk_tier_distribution", "region_breakdown"],
        "reference_data": ["sovereign_profiles_60_countries",
                           "ngfs_climate_scenarios_5",
                           "sp_rating_notch_map_22",
                           "nd_gain_index"],
        "quality_indicators": ["country_coverage", "scenario_count", "nd_gain_freshness"],
    },
    # ---- SEC Climate Disclosure ----
    "sec_climate_engine": {
        "label": "SEC Climate Disclosure Engine",
        "category": "regulatory",
        "inputs": ["registrant_name", "cik", "filer_category", "fiscal_year",
                    "governance_score", "strategy_score", "risk_management_score",
                    "targets_goals_score", "ghg_emissions_score", "financial_effects_score",
                    "has_limited_assurance", "has_reasonable_assurance",
                    "scope_1_total_co2e_mt", "scope_2_location_co2e_mt",
                    "pre_tax_income_usd", "total_equity_usd",
                    "severe_weather_losses_usd", "transition_capex_usd",
                    "physical_risks", "transition_risks",
                    "scenario_analysis_used", "internal_carbon_price_usd_per_tco2e"],
        "outputs": ["ghg_disclosure_required", "assurance_required", "assurance_level",
                     "item_compliance", "overall_compliance_pct", "gaps", "critical_gaps",
                     "recommendations", "attestation_status", "safe_harbor_items",
                     "cross_framework_mapping",
                     "attestation_readiness_score", "data_quality_score",
                     "materiality_threshold_usd", "disclosure_required",
                     "material_physical_risks", "material_transition_risks",
                     "material_count", "strategy_impact"],
        "reference_data": ["sec_filer_categories_5",
                           "reg_sk_items_1500_1505",
                           "reg_sx_14_02_items_3",
                           "attestation_requirements_aicpa",
                           "pslra_safe_harbor",
                           "sec_cross_framework_map_6"],
        "quality_indicators": ["item_score_coverage", "filer_category_validity", "attestation_completeness"],
    },
    # ---- GRI Standards ----
    "gri_standards_engine": {
        "label": "GRI Standards 2021 Engine",
        "category": "regulatory",
        "inputs": ["entity_name", "reporting_period", "material_topics",
                    "disclosure_statuses", "sector_standard",
                    "scope_1_co2e_mt", "scope_2_location_co2e_mt", "scope_2_market_co2e_mt",
                    "scope_3_co2e_mt", "ghg_intensity",
                    "reductions_co2e_mt", "ods_tonnes_cfc11eq",
                    "nox_tonnes", "sox_tonnes", "pm_tonnes",
                    "topic_standard", "management_approach_score", "disclosures_reported"],
        "outputs": ["gri_compliance_level", "completeness_pct",
                     "total_applicable_disclosures", "total_reported",
                     "total_omitted", "by_category", "disclosure_index",
                     "omission_reasons", "sdg_linkage", "esrs_mapping",
                     "disclosure_completeness", "gaps",
                     "topic_title", "management_approach_score",
                     "disclosure_completeness_pct", "disclosures_omitted",
                     "esrs_equivalent"],
        "reference_data": ["gri_topic_standards_18",
                           "gri_sector_standards_4",
                           "gri_sdg_linkage_16",
                           "gri_esrs_mapping_18",
                           "gri_reporting_principles_8"],
        "quality_indicators": ["material_topic_coverage", "disclosure_completeness",
                               "sector_standard_applicability"],
    },
    "sasb_industry_engine": {
        "label": "SASB Industry Standards Engine",
        "category": "regulatory",
        "inputs": ["entity_name", "sasb_industry_code", "reporting_year",
                   "reported_metrics", "entity_overrides", "entity_metrics"],
        "outputs": ["completeness_pct", "materiality_coverage_pct", "avg_data_quality_score",
                    "metric_results", "topic_scores", "peer_comparison",
                    "issb_s2_cross_ref", "gri_cross_ref", "esrs_cross_ref",
                    "gaps", "ifrs_s1_para55_compliant", "peer_rank_label",
                    "material_topics", "double_materiality_flags", "issb_alignment_pct"],
        "reference_data": ["sasb_sics_sectors_20", "sasb_materiality_map_77_industries",
                           "sasb_issb_s2_appendix_b_mapping", "sasb_gri_interop",
                           "sasb_esrs_interop", "sector_benchmark_medians"],
        "quality_indicators": ["metric_completeness", "data_quality_score_avg",
                               "materiality_coverage"],
    },
    "model_validation_framework": {
        "label": "Model Validation Framework",
        "category": "governance",
        "inputs": ["model_id", "predicted_values", "actual_values",
                   "observation_window", "tests_to_run",
                   "champion_predicted", "challenger_predicted",
                   "comparison_metric", "target_state"],
        "outputs": ["backtest_result", "overall_traffic_light", "test_results",
                    "green_amber_red_counts", "regulatory_status",
                    "champion_challenger_winner", "p_value",
                    "model_inventory", "lifecycle_state", "validation_dashboard",
                    "bcbs239_compliance_pct", "eba_gl_2023_04_compliant"],
        "reference_data": ["model_inventory_18_models", "validation_test_suite_12_tests",
                           "lifecycle_state_machine", "regulatory_frameworks_5",
                           "traffic_light_thresholds"],
        "quality_indicators": ["backtest_traffic_light", "sample_size_adequacy",
                               "test_coverage_pct"],
    },
    "tnfd_assessment_engine": {
        "label": "TNFD Nature-Related Disclosures Engine",
        "category": "regulatory",
        "inputs": ["entity_name", "reporting_year", "disclosure_data",
                   "sector", "dependencies", "impacts", "leap_data"],
        "outputs": ["overall_compliance_pct", "disclosure_scores_14",
                    "leap_phase_results", "nature_risk_profile",
                    "priority_locations_count", "ecosystem_services_at_risk",
                    "cross_framework_mapping", "financial_materiality_score",
                    "impact_materiality_score", "double_materiality_topics",
                    "leap_readiness_level", "gaps", "recommendations"],
        "reference_data": ["tnfd_14_recommended_disclosures", "leap_4_phases_16_components",
                           "encore_21_ecosystem_services", "nature_risk_3_categories",
                           "sector_guidance_8_sectors", "cross_framework_map_8_mappings",
                           "priority_area_criteria_8"],
        "quality_indicators": ["disclosure_compliance_pct", "leap_readiness_level",
                               "sector_guidance_coverage"],
    },
    "cdp_scoring_engine": {
        "label": "CDP Climate & Water Scoring Engine",
        "category": "regulatory",
        "inputs": ["entity_name", "reporting_year", "activity_group",
                   "climate_responses", "water_responses", "entity_score_pct"],
        "outputs": ["overall_score_pct", "grade", "grade_label",
                    "module_scores_climate_15", "module_scores_water_9",
                    "scoring_breakdown_4_levels", "verification_status",
                    "sbti_alignment", "cross_framework_mapping",
                    "peer_comparison", "water_risk_exposure",
                    "gaps", "recommendations"],
        "reference_data": ["cdp_climate_15_modules", "cdp_water_9_modules",
                           "cdp_scoring_4_levels", "cdp_score_bands_8_grades",
                           "activity_groups_12", "peer_benchmark_medians_6"],
        "quality_indicators": ["climate_disclosure_completeness", "water_disclosure_completeness",
                               "verification_coverage_pct"],
    },
    "pcaf_quality_engine": {
        "label": "PCAF Data Quality Score Engine",
        "category": "financed_emissions",
        "inputs": ["holding_id", "entity_name", "asset_class", "outstanding_amount_eur",
                   "reported_emissions", "revenue_eur", "physical_activity_data",
                   "data_year", "verification_status", "portfolio_id", "portfolio_name",
                   "reporting_year", "holdings"],
        "outputs": ["dqs_emissions", "dqs_completeness", "dqs_timeliness",
                    "dqs_granularity", "dqs_methodology", "weighted_dqs",
                    "confidence_weight", "estimated_emissions_tco2",
                    "attribution_factor", "financed_emissions_tco2",
                    "portfolio_weighted_dqs", "dqs_distribution",
                    "carbon_intensity_tco2_per_meur", "sfdr_pai_indicators",
                    "quality_improvement_roadmap", "confidence_band",
                    "data_gaps", "improvement_actions"],
        "reference_data": ["pcaf_6_asset_classes", "pcaf_dqs_5_levels",
                           "pcaf_5_quality_dimensions", "sector_emission_factors_15",
                           "attribution_methods_4", "improvement_paths_4",
                           "cross_framework_map_8", "sector_benchmarks_10"],
        "quality_indicators": ["portfolio_weighted_dqs", "dqs_distribution_skew",
                               "scoring_coverage_pct"],
    },
    "basel_capital_engine": {
        "label": "Basel III/IV Regulatory Capital Engine",
        "category": "banking_risk",
        "inputs": ["entity_name", "reporting_date", "exposures",
                   "capital_cet1", "capital_at1", "capital_tier2",
                   "total_exposure_measure", "approach", "climate_adjusted",
                   "buffers", "assets_hqla", "liabilities",
                   "climate_scenarios"],
        "outputs": ["total_rwa", "total_rwa_credit", "total_rwa_market",
                    "total_rwa_operational", "cet1_ratio", "tier1_ratio",
                    "total_capital_ratio", "leverage_ratio",
                    "cet1_surplus_deficit", "climate_rwa_addon",
                    "lcr_ratio", "nsfr_ratio", "lcr_compliant", "nsfr_compliant",
                    "bcbs239_compliance_score", "overall_rag_status",
                    "regulatory_breaches", "pillar2_recommendations",
                    "exposure_class_breakdown"],
        "reference_data": ["crr_art112_13_exposure_classes", "sa_risk_weight_tables",
                           "irb_art153_parameters", "capital_minimums_4",
                           "buffer_requirements_5", "lcr_hqla_parameters",
                           "nsfr_asf_rsf_factors", "climate_adj_eba_2022",
                           "regulatory_frameworks_7", "sma_op_risk"],
        "quality_indicators": ["exposure_coverage_pct", "capital_data_completeness",
                               "liquidity_data_freshness"],
    },
    "eu_taxonomy_engine": {
        "label": "EU Taxonomy Alignment Engine",
        "category": "regulatory_taxonomy",
        "inputs": ["nace_code", "objective", "evidence_data", "entity_name",
                   "reporting_year", "activities_data", "financials",
                   "portfolio_id", "portfolio_name", "investees_data",
                   "turnover_eur", "capex_eur", "opex_eur",
                   "emission_intensity", "energy_source"],
        "outputs": ["taxonomy_aligned", "taxonomy_eligible",
                    "sc_score", "dnsh_results", "minimum_safeguards_met",
                    "turnover_alignment_pct", "capex_alignment_pct",
                    "opex_alignment_pct", "objective_breakdown",
                    "transitional_share_pct", "enabling_share_pct",
                    "green_asset_ratio", "btar",
                    "sfdr_article_classification",
                    "cross_framework_disclosures",
                    "improvement_recommendations", "data_quality_flags"],
        "reference_data": ["6_environmental_objectives", "30_nace_activities_tsc",
                           "dnsh_6x6_matrix", "minimum_safeguards_art18",
                           "kpi_definitions_3", "transitional_activities",
                           "enabling_activities", "cross_framework_map_7",
                           "financial_kpi_gar_btar", "sector_thresholds"],
        "quality_indicators": ["activity_coverage_pct", "tsc_evidence_completeness",
                               "dnsh_assessment_completeness"],
    },
    "transition_plan_engine": {
        "label": "Climate Transition Plan Assessment Engine",
        "category": "climate_transition",
        "inputs": ["entity_name", "sector", "reporting_year", "plan_data",
                   "targets_data", "current_metrics", "target_year",
                   "scope1_emissions", "scope2_emissions", "scope3_emissions",
                   "energy_consumption_mwh", "renewable_share_pct",
                   "capex_aligned_eur", "internal_carbon_price",
                   "carbon_credits_tco2", "board_climate_oversight",
                   "executive_remuneration_linked", "sbti_validated",
                   "net_zero_year", "interim_targets"],
        "outputs": ["overall_score", "overall_rating",
                    "tpt_assessment", "gfanz_assessment", "iigcc_assessment",
                    "csddd_compliance", "esrs_e1_coverage", "cdp_c4_alignment",
                    "target_credibility_score", "implementation_maturity_score",
                    "governance_strength_score", "financial_commitment_score",
                    "cross_framework_completeness", "inter_framework_gaps",
                    "improvement_roadmap", "regulatory_readiness",
                    "sector_pathway_alignment", "gap_to_pathway_pct",
                    "paris_aligned"],
        "reference_data": ["tpt_5_elements_16_sub", "gfanz_nzba_nzaoa_nzami_nzia",
                           "iigcc_nzif_v2_7_steps", "csddd_art22_8_requirements",
                           "esrs_e1_10_disclosures_50_dps", "cdp_c4_questions",
                           "cross_framework_mapping_50_datapoints",
                           "scoring_rubrics_5", "sector_pathways_iea_tpi_sbti",
                           "target_validation_criteria", "carbon_credit_quality",
                           "regulatory_timeline"],
        "quality_indicators": ["framework_coverage_pct", "datapoint_disclosure_pct",
                               "target_credibility_score"],
    },
    "double_materiality_engine": {
        "inputs": ["entity_name", "sector", "reporting_year", "impact_topic_scores",
                   "financial_topic_scores", "stakeholder_responses",
                   "impact_threshold", "financial_threshold", "time_horizons",
                   "sector_defaults", "prior_year_assessment"],
        "outputs": ["impact_materiality_scores", "financial_materiality_scores",
                    "combined_dma_result", "material_topics_list",
                    "materiality_matrix_data", "materiality_classification",
                    "stakeholder_engagement_quality", "dma_report",
                    "cross_framework_mapping", "sector_benchmark_comparison"],
        "reference_data": ["esrs_10_topics_catalog", "impact_factors_scale_scope_irremediability",
                           "financial_factors_risk_opportunity", "stakeholder_registry_10_groups",
                           "sector_benchmarks_6_sectors", "materiality_thresholds_calibration",
                           "cross_framework_map_gri_tcfd_issb_sdg"],
        "quality_indicators": ["topic_coverage_pct", "stakeholder_engagement_score",
                               "assessment_completeness"],
    },
    "sfdr_pai_engine": {
        "inputs": ["portfolio_holdings", "pai_indicator_id", "reporting_period",
                   "entity_classification_config", "peer_group",
                   "prior_period_pais", "taxonomy_objective",
                   "selected_additional_indicators"],
        "outputs": ["pai_calculated_value", "all_18_mandatory_pais",
                    "additional_pai_values", "dnsh_assessment",
                    "pai_statement_disclosure", "period_comparison",
                    "entity_classification_art6_8_9", "peer_benchmark_percentile",
                    "data_coverage_assessment", "pai_disclosure_document"],
        "reference_data": ["sfdr_18_mandatory_indicators_table1", "sfdr_46_additional_indicators_tables2_3",
                           "pai_calculation_methods_formulas", "entity_classification_art6_8_9_criteria",
                           "rts_disclosure_templates", "sector_pai_benchmarks"],
        "quality_indicators": ["data_coverage_ratio", "estimation_share_pct",
                               "indicator_completeness_pct"],
    },
    # ---- DME (Dynamic Materiality Engine) ----
    "dme_velocity_engine": {
        "label": "DME Velocity Engine",
        "category": "dme",
        "inputs": ["raw_metric_timeseries", "entity_id", "metric_key", "ewma_alpha",
                    "lookback_days", "z_thresholds"],
        "outputs": ["velocity_raw", "velocity_pct", "velocity_smoothed", "acceleration",
                     "z_score", "regime", "sigma_classification"],
        "reference_data": ["velocity_config"],
        "quality_indicators": ["timeseries_completeness", "lookback_coverage"],
    },
    "dme_greenwashing_engine": {
        "label": "DME Greenwashing Engine",
        "category": "dme",
        "inputs": ["marketing_scores", "operational_scores", "pcaf_quality",
                    "data_age", "timestamps"],
        "outputs": ["greenwashing_detected", "severity", "divergence_z_score",
                     "cusum_alert", "velocity_latest", "credibility_gap"],
        "reference_data": ["greenwash_config", "cusum_parameters"],
        "quality_indicators": ["score_coverage", "data_recency"],
    },
    "dme_nlp_pulse_engine": {
        "label": "DME NLP Pulse Engine",
        "category": "dme",
        "inputs": ["sentiment_score", "information_density", "source_tier",
                    "event_type", "is_self_reported"],
        "outputs": ["pulse_raw", "pulse_discounted", "greenwash_discount",
                     "decay_lambda", "credibility_adjusted_pulse", "aggregate_pulse"],
        "reference_data": ["decay_half_lives", "source_credibility_tiers"],
        "quality_indicators": ["source_diversity", "signal_freshness"],
    },
    "dme_policy_tracker_engine": {
        "label": "DME Policy Tracker Engine",
        "category": "dme",
        "inputs": ["carbon_prices", "bills_data", "sanctions_data",
                    "litigation_data", "disclosure_adoptions"],
        "outputs": ["carbon_price_velocity", "regulatory_pipeline_velocity",
                     "enforcement_velocity", "disclosure_mandate_velocity",
                     "composite_velocity"],
        "reference_data": ["sector_weights_isic"],
        "quality_indicators": ["policy_data_coverage", "jurisdiction_breadth"],
    },
    "dme_contagion_engine": {
        "label": "DME Contagion Engine",
        "category": "dme",
        "inputs": ["adjacency_matrix", "entity_events", "ead_exposure", "hhi",
                    "revenue_share", "mu_baseline", "beta_decay"],
        "outputs": ["l1_intensity", "l2_intensity", "l3_intensity",
                     "aggregated_intensity", "el_amplification", "var_amplification",
                     "es_amplification", "spectral_radius"],
        "reference_data": ["channel_weights", "cross_pillar_amplifiers",
                           "cross_sector_defaults"],
        "quality_indicators": ["network_completeness", "exposure_data_quality"],
    },
    "dme_alert_engine": {
        "label": "DME Alert Engine",
        "category": "dme",
        "inputs": ["velocity_z_score", "acceleration", "exposure_share",
                    "sensitivity_alpha", "factor_id"],
        "outputs": ["alert_tier", "trigger_type", "priority_score",
                     "priority_band", "response_sla_hours"],
        "reference_data": ["tier_thresholds", "suppression_config", "sla_config"],
        "quality_indicators": ["signal_latency", "false_positive_rate"],
    },
    "dme_dmi_engine": {
        "label": "DME DMI Engine",
        "category": "dme",
        "inputs": ["factor_scores", "factor_weights", "pcaf_quality",
                    "recency_years", "outstanding_amount", "entity_evic",
                    "entity_emissions", "concentration_metrics"],
        "outputs": ["dmi_score_base", "dmi_score_adjusted", "velocity_adjustment",
                     "concentration_penalty", "financed_emissions", "weighted_pcaf"],
        "reference_data": ["pcaf_confidence_map"],
        "quality_indicators": ["factor_coverage", "pcaf_dqs_distribution"],
    },

    # ---- Factor Registry ----
    "dme_factor_registry": {
        "label": "DME Factor Registry",
        "category": "dme",
        "inputs": ["factor_seed_json", "overlay_registry_keys"],
        "outputs": ["factor_definitions", "factor_id", "pillar", "topic",
                     "materiality_dimension", "velocity_method", "alert_thresholds",
                     "overlay_mapping", "regulatory_refs"],
        "reference_data": ["dme_627_taxonomy", "overlay_31_registries"],
        "quality_indicators": ["factor_coverage_pct", "overlay_mapping_completeness"],
    },

    # ---- Sentiment Analysis Engine ----
    "sentiment_analysis_engine": {
        "label": "Sentiment Analysis Engine",
        "category": "sentiment",
        "inputs": ["raw_signal", "entity_id", "source_name", "signal_type",
                    "raw_sentiment", "confidence", "stakeholder_group",
                    "esg_pillar", "topic_tags", "published_at",
                    "nlp_pulse_score", "greenwashing_divergence",
                    "gdelt_controversy", "engagement_outcome", "esg_factor_context"],
        "outputs": ["composite_score", "stakeholder_scores", "esg_scores",
                     "sentiment_velocity", "sentiment_acceleration", "regime",
                     "alert_tier", "pd_multiplier", "materiality_signal",
                     "reputation_score", "cascade_risk", "source_diversity",
                     "portfolio_sentiment", "topic_trend"],
        "reference_data": ["source_credibility_tiers", "stakeholder_weights",
                           "decay_half_lives", "regime_thresholds", "module_connections"],
        "quality_indicators": ["source_diversity_hhi", "signal_count", "credibility_coverage"],
    },
}


# ---------------------------------------------------------------------------
# Reference Data — Module Dependencies (Directed Edges)
# ---------------------------------------------------------------------------

MODULE_DEPENDENCIES: list[dict] = [
    # Carbon → downstream
    {"source": "carbon_calculator", "target": "csrd_auto_populate",
     "field_map": {"scope1_total_tco2e": "E1-6_GHG_scope1", "scope2_location_tco2e": "E1-6_GHG_scope2_lb",
                   "scope2_market_tco2e": "E1-6_GHG_scope2_mb", "scope3_total_tco2e": "E1-6_GHG_scope3_total"},
     "description": "GHG emissions feed CSRD E1 disclosures"},
    {"source": "carbon_calculator", "target": "pcaf_waci_engine",
     "field_map": {"total_tco2e": "investee_emissions_tco2e"},
     "description": "Entity emissions feed PCAF financed emissions attribution"},
    {"source": "carbon_calculator", "target": "sfdr_report_generator",
     "field_map": {"scope1_total_tco2e": "pai_1_ghg_scope123", "intensity_tco2e_per_m_revenue": "pai_3_ghg_intensity"},
     "description": "GHG data feeds SFDR PAI indicators 1-3"},
    {"source": "carbon_calculator", "target": "entity360",
     "field_map": {"total_tco2e": "total_tco2e", "intensity_tco2e_per_m_revenue": "intensity_revenue"},
     "description": "Emissions feed Entity 360 ESG profile"},

    # Supply Chain Scope 3 → Carbon
    {"source": "supply_chain_scope3", "target": "carbon_calculator",
     "field_map": {"total_scope3_tco2e": "scope3_categories"},
     "description": "Detailed Scope 3 breakdown feeds carbon calculator total"},

    # PCAF → ECL Bridge → ECL
    {"source": "pcaf_waci_engine", "target": "pcaf_ecl_bridge",
     "field_map": {"waci_tco2e_per_m": "waci_tco2e", "portfolio_temperature_c": "implied_temperature_c",
                   "data_quality_score_avg": "dqs_score"},
     "description": "PCAF emissions data feeds ECL climate bridge"},
    {"source": "pcaf_ecl_bridge", "target": "ecl_climate_engine",
     "field_map": {"ecl_climate_inputs": "climate_scenario", "scenario_weights": "scenario_weights",
                   "confidence_weighted_overlay": "climate_overlay_eur"},
     "description": "Bridge maps PCAF to ECL climate-adjusted risk parameters"},

    # PD/LGD/EAD → ECL
    {"source": "pd_calculator", "target": "ecl_climate_engine",
     "field_map": {"pd_1yr": "pd_1yr"},
     "description": "Base PD feeds climate-adjusted ECL engine"},
    {"source": "lgd_calculator", "target": "ecl_climate_engine",
     "field_map": {"lgd_pct": "lgd_pct"},
     "description": "Base LGD feeds climate-adjusted ECL engine"},
    {"source": "ead_calculator", "target": "ecl_climate_engine",
     "field_map": {"ead_eur": "ead_eur"},
     "description": "EAD feeds climate-adjusted ECL engine"},

    # ECL → Entity 360
    {"source": "ecl_climate_engine", "target": "entity360",
     "field_map": {"ecl_climate_adj_eur": "ecl_eur", "pd_climate_adj": "pd_1yr",
                   "ecl_stage": "ecl_stage"},
     "description": "Climate-adjusted ECL feeds Entity 360 credit risk profile"},

    # Scenario Analysis → downstream
    {"source": "scenario_analysis_engine", "target": "csrd_auto_populate",
     "field_map": {"carbon_price_impact_eur": "E1-9_carbon_price_internal"},
     "description": "Scenario carbon price feeds CSRD E1-9 disclosure"},
    {"source": "scenario_analysis_engine", "target": "ecl_climate_engine",
     "field_map": {"transition_risk_score": "climate_scenario"},
     "description": "NGFS scenario parameters feed ECL climate overlay"},
    {"source": "scenario_analysis_engine", "target": "entity360",
     "field_map": {"combined_risk_score": "scenario_alignment"},
     "description": "Scenario risk score feeds Entity 360 composite profile"},

    # Nature Risk → downstream
    {"source": "nature_risk_calculator", "target": "csrd_auto_populate",
     "field_map": {"water_risk_score": "E3-4_water_consumption",
                   "biodiversity_score": "E4-5_land_use_change"},
     "description": "Nature metrics feed CSRD E3/E4 disclosures"},
    {"source": "nature_risk_calculator", "target": "entity360",
     "field_map": {"nature_risk_score": "nature_risk_score"},
     "description": "Nature risk score feeds Entity 360 composite profile"},

    # RE Valuation → CRREM
    {"source": "real_estate_valuation_engine", "target": "crrem_stranding_engine",
     "field_map": {"market_value_eur": "property_value_eur"},
     "description": "Property valuation feeds CRREM stranding analysis"},
    {"source": "crrem_stranding_engine", "target": "entity360",
     "field_map": {"stranding_year": "crrem_stranding_year"},
     "description": "CRREM stranding year feeds Entity 360 RE profile"},

    # Taxonomy → Entity 360
    {"source": "gar_calculator", "target": "entity360",
     "field_map": {"taxonomy_aligned_pct": "taxonomy_aligned_pct"},
     "description": "GAR alignment feeds Entity 360 regulatory status"},

    # SFDR → Entity 360
    {"source": "sfdr_report_generator", "target": "entity360",
     "field_map": {"pai_count_flagged": "pai_count_flagged"},
     "description": "SFDR PAI flags feed Entity 360 regulatory status"},

    # China Trade cross-module bridges
    {"source": "china_trade_engine", "target": "supply_chain_scope3",
     "field_map": {"cbam_exposure_eur": "scope3_cat1_cbam_overlay"},
     "description": "CBAM exposure feeds Scope 3 Category 1 overlay"},
    {"source": "china_trade_engine", "target": "ecl_climate_engine",
     "field_map": {"tariff_risk_score": "ecl_cbam_overlay"},
     "description": "China trade tariff risk feeds ECL credit adjustment"},
    {"source": "china_trade_engine", "target": "csrd_auto_populate",
     "field_map": {"regulatory_alignment": "regulatory_csrd_china"},
     "description": "China regulatory mapping feeds CSRD disclosures"},

    # Stranded Asset → Entity 360
    {"source": "stranded_asset_calculator", "target": "entity360",
     "field_map": {"stranding_probability": "stranded_asset_risk"},
     "description": "Stranded asset probability feeds Entity 360 risk profile"},

    # PE Deal → Entity 360
    {"source": "pe_deal_engine", "target": "entity360",
     "field_map": {"irr_base_pct": "pe_irr", "esg_value_creation_eur": "esg_value_creation"},
     "description": "PE deal metrics feed Entity 360 valuation profile"},

    # CBAM → CSRD
    {"source": "cbam_calculator", "target": "csrd_auto_populate",
     "field_map": {"cbam_cost_eur": "cbam_financial_impact"},
     "description": "CBAM cost feeds CSRD financial effects disclosure"},

    # Insurance Risk Engine → Entity 360
    {"source": "insurance_risk_engine", "target": "entity360",
     "field_map": {"nat_cat_aal_eur": "insurance_aal", "total_capital_at_risk_eur": "insurance_capital_at_risk",
                   "aggregate_risk_score": "insurance_risk_score", "risk_rating": "insurance_risk_rating"},
     "description": "Insurance risk engine comprehensive metrics feed Entity 360 for insurer entities"},

    # Insurance Risk Engine → CSRD auto-populate
    {"source": "insurance_risk_engine", "target": "csrd_auto_populate",
     "field_map": {"nat_cat_aal_eur": "E1-9_physical_risk_eur",
                   "combined_ratio_climate_adj_pct": "insurance_combined_ratio"},
     "description": "Insurance nat-cat and underwriting metrics feed CSRD E1-9 physical risk disclosure"},

    # Scenario Analysis → Insurance Risk Engine
    {"source": "scenario_analysis_engine", "target": "insurance_risk_engine",
     "field_map": {"warming_trajectory_c": "warming_c"},
     "description": "NGFS warming trajectory feeds insurance climate scenario parameter"},

    # Legacy alias (keep backward compatibility)
    {"source": "insurance_climate_risk", "target": "entity360",
     "field_map": {"nat_cat_aal_eur": "insurance_aal", "capital_add_on_pct": "solvency_add_on"},
     "description": "Insurance climate metrics feed Entity 360 for insurer entities (legacy)"},

    # All modules → CSRD Auto-populate (comprehensive mapping)
    {"source": "pcaf_waci_engine", "target": "csrd_auto_populate",
     "field_map": {"financed_emissions_tco2e": "E1_financed_emissions",
                   "waci_tco2e_per_m": "E1_waci"},
     "description": "PCAF financed emissions feed CSRD E1 disclosures"},

    # Banking Risk Engine → Entity 360
    {"source": "banking_risk_engine", "target": "entity360",
     "field_map": {"total_ecl_eur": "bank_ecl_total", "cet1_ratio_pct": "bank_cet1_ratio",
                   "lcr_pct": "bank_lcr", "overall_risk_rating": "bank_risk_rating",
                   "overall_aml_risk_score": "bank_aml_score"},
     "description": "Banking risk metrics feed Entity 360 for bank entities"},

    # Banking Risk Engine → CSRD auto-populate
    {"source": "banking_risk_engine", "target": "csrd_auto_populate",
     "field_map": {"total_ecl_eur": "G1_credit_risk_exposure",
                   "climate_overlay_eur": "E1-9_transition_risk_eur",
                   "cet1_ratio_pct": "G1_capital_adequacy"},
     "description": "Banking credit/capital metrics feed CSRD G1 governance disclosures"},

    # ECL Climate Engine → Banking Risk Engine
    {"source": "ecl_climate_engine", "target": "banking_risk_engine",
     "field_map": {"pd_climate_adj": "avg_rating", "ecl_climate_adj_eur": "total_exposure_eur"},
     "description": "Climate-adjusted PD and ECL feed banking credit risk assessment"},

    # Scenario Analysis → Banking Risk Engine
    {"source": "scenario_analysis_engine", "target": "banking_risk_engine",
     "field_map": {"warming_trajectory_c": "warming_c"},
     "description": "NGFS warming trajectory feeds banking climate stress parameter"},

    # PD Calculator → Banking Risk Engine
    {"source": "pd_calculator", "target": "banking_risk_engine",
     "field_map": {"pd_1yr": "avg_rating", "rating_implied": "avg_rating"},
     "description": "PD model outputs feed banking credit risk assessment"},

    # NACE-CPRS Mapper → Transition Risk Engine
    {"source": "nace_cprs_mapper", "target": "climate_transition_risk_engine",
     "field_map": {"cprs_category": "cprs_category", "sector_risk_score": "sector_risk_score",
                   "iam_sectors": "iam_sectors"},
     "description": "Sector classification feeds transition risk analysis"},

    # Scenario Analysis → Physical Risk Engine
    {"source": "scenario_analysis_engine", "target": "climate_physical_risk_engine",
     "field_map": {"warming_trajectory_c": "scenario_ssp"},
     "description": "NGFS/SSP scenario paths feed physical risk hazard assessment"},

    # Physical Risk Engine → Entity 360
    {"source": "climate_physical_risk_engine", "target": "entity360",
     "field_map": {"physical_cvar_eur": "physical_cvar", "physical_risk_score": "physical_risk_score",
                   "risk_rating": "physical_risk_rating", "expected_annual_loss_eur": "physical_aal"},
     "description": "Physical risk metrics feed Entity 360 for all entity types"},

    # Transition Risk Engine → Entity 360
    {"source": "climate_transition_risk_engine", "target": "entity360",
     "field_map": {"composite_transition_score": "transition_risk_score",
                   "transition_risk_rating": "transition_risk_rating",
                   "max_transition_cvar_eur": "transition_cvar"},
     "description": "Transition risk composite score and CVaR feed Entity 360"},

    # Physical Risk Engine → CSRD auto-populate
    {"source": "climate_physical_risk_engine", "target": "csrd_auto_populate",
     "field_map": {"physical_cvar_eur": "E1-9_physical_risk_eur",
                   "expected_annual_loss_eur": "E1-9_physical_aal_eur"},
     "description": "Physical CVaR and AAL feed CSRD E1-9 physical risk disclosures"},

    # Transition Risk Engine → CSRD auto-populate
    {"source": "climate_transition_risk_engine", "target": "csrd_auto_populate",
     "field_map": {"max_transition_cvar_eur": "E1-9_transition_risk_eur",
                   "composite_transition_score": "E1_transition_score"},
     "description": "Transition CVaR and composite score feed CSRD E1 disclosures"},

    # Carbon Calculator → Transition Risk Engine
    {"source": "carbon_calculator_v2", "target": "climate_transition_risk_engine",
     "field_map": {"scope1_tco2e": "scope1_tco2e", "scope2_lb_tco2e": "scope2_tco2e",
                   "scope3_tco2e": "scope3_tco2e", "intensity_revenue": "current_emission_intensity"},
     "description": "Carbon calculator emissions feed transition risk carbon pricing"},

    # Stranded Asset Calculator → Transition Risk Engine
    {"source": "stranded_asset_calculator", "target": "climate_transition_risk_engine",
     "field_map": {"reserve_impairment_value": "fossil_reserve_value"},
     "description": "Stranded asset valuations feed transition risk writedown assessment"},

    # CBAM Calculator → Transition Risk Engine
    {"source": "cbam_calculator", "target": "climate_transition_risk_engine",
     "field_map": {"cbam_liability_eur": "is_cbam_sector"},
     "description": "CBAM liability indicator feeds transition risk CBAM assessment"},

    # ── AM Engine edges ──────────────────────────────────────────────────

    # Carbon → AM Paris Alignment (emissions feed temperature scoring)
    {"source": "carbon_calculator_v2", "target": "am_paris_alignment",
     "field_map": {"intensity_revenue": "holdings_carbon_intensity"},
     "description": "Carbon intensity feeds PACTA portfolio temperature scoring"},

    # AM ESG Attribution → Entity 360
    {"source": "am_esg_attribution", "target": "entity360",
     "field_map": {"portfolio_esg_score": "portfolio_esg_score",
                   "active_return_bps": "am_active_return"},
     "description": "ESG attribution results feed Entity 360 AM profile"},

    # AM Paris Alignment → Entity 360
    {"source": "am_paris_alignment", "target": "entity360",
     "field_map": {"portfolio_temperature_c": "am_temperature_c",
                   "alignment_gap_c": "am_alignment_gap"},
     "description": "PACTA temperature scoring feeds Entity 360 climate profile"},

    # AM Paris Alignment → CSRD auto-populate
    {"source": "am_paris_alignment", "target": "csrd_auto_populate",
     "field_map": {"portfolio_temperature_c": "E1_portfolio_temperature",
                   "weighted_carbon_intensity": "E1_waci_am"},
     "description": "AM temperature and WACI feed CSRD E1 disclosures"},

    # AM Green Bond Screening → Entity 360
    {"source": "am_green_bond_screening", "target": "entity360",
     "field_map": {"overall_score": "green_bond_score"},
     "description": "Green bond screening feeds Entity 360 green finance profile"},

    # AM Climate Spreads → ECL Climate Engine
    {"source": "am_climate_spreads", "target": "ecl_climate_engine",
     "field_map": {"climate_adjusted_spread_bps": "climate_spread_overlay"},
     "description": "Climate-adjusted spreads feed ECL credit risk overlay"},

    # AM LP Analytics → Entity 360
    {"source": "am_lp_analytics", "target": "entity360",
     "field_map": {"hhi_concentration": "am_lp_hhi",
                   "lcr_pct": "am_lcr_pct"},
     "description": "LP concentration and liquidity metrics feed Entity 360"},

    # AM Optimisation → Entity 360
    {"source": "am_optimisation", "target": "entity360",
     "field_map": {"sharpe_ratio": "am_sharpe_ratio",
                   "carbon_reduction_pct": "am_carbon_reduction"},
     "description": "Optimised portfolio metrics feed Entity 360"},

    # Scenario Analysis → AM Climate Spreads
    {"source": "scenario_analysis_engine", "target": "am_climate_spreads",
     "field_map": {"carbon_price_impact_eur": "carbon_price_eur"},
     "description": "NGFS carbon price feeds climate-adjusted spread calculation"},

    # PCAF → AM ESG Attribution (financed emissions context)
    {"source": "pcaf_waci_engine", "target": "am_esg_attribution",
     "field_map": {"waci_tco2e_per_m": "holdings_carbon_intensity"},
     "description": "PCAF WACI feeds ESG factor attribution carbon metric"},

    # ── Agriculture Expanded edges ───────────────────────────────────────

    # Agriculture Methane → Entity 360
    {"source": "agriculture_methane_intensity", "target": "entity360",
     "field_map": {"total_tco2e_yr": "ag_methane_tco2e",
                   "intensity_kgch4_per_head": "ag_methane_intensity"},
     "description": "Livestock methane emissions feed Entity 360 agriculture profile"},

    # Agriculture Methane → CSRD auto-populate
    {"source": "agriculture_methane_intensity", "target": "csrd_auto_populate",
     "field_map": {"total_tco2e_yr": "E1-6_agriculture_ghg",
                   "total_ch4_tonnes_yr": "E1_methane_tonnes"},
     "description": "Methane emissions feed CSRD E1 agriculture GHG disclosures"},

    # Agriculture Methane → Carbon Calculator
    {"source": "agriculture_methane_intensity", "target": "carbon_calculator_v2",
     "field_map": {"total_tco2e_yr": "scope1_agriculture_tco2e"},
     "description": "Livestock methane feeds carbon calculator agriculture Scope 1"},

    # Agriculture Disease → Entity 360
    {"source": "agriculture_disease_outbreak", "target": "entity360",
     "field_map": {"overall_disease_risk_score": "ag_disease_risk_score",
                   "expected_annual_loss_eur": "ag_disease_aal"},
     "description": "Disease outbreak risk feeds Entity 360 agriculture risk profile"},

    # Agriculture BNG → Entity 360
    {"source": "agriculture_bng", "target": "entity360",
     "field_map": {"net_gain_pct": "ag_bng_pct",
                   "risk_rating": "ag_bng_risk_rating"},
     "description": "Biodiversity net gain feeds Entity 360 nature profile"},

    # Agriculture BNG → CSRD auto-populate
    {"source": "agriculture_bng", "target": "csrd_auto_populate",
     "field_map": {"net_gain_pct": "E4_biodiversity_net_gain_pct",
                   "baseline_habitat_units": "E4_habitat_baseline_units"},
     "description": "BNG metrics feed CSRD E4 biodiversity disclosures"},

    # Agriculture BNG → Nature Risk Calculator
    {"source": "agriculture_bng", "target": "nature_risk_calculator",
     "field_map": {"net_gain_pct": "biodiversity_net_gain_context"},
     "description": "BNG assessment provides biodiversity context to nature risk"},

    # Scenario Analysis → Agriculture Disease (climate warming parameter)
    {"source": "scenario_analysis_engine", "target": "agriculture_disease_outbreak",
     "field_map": {"warming_trajectory_c": "climate_warming_c"},
     "description": "NGFS warming trajectory feeds disease outbreak climate factor"},

    # Agriculture base calculator → Agriculture Methane (base data context)
    {"source": "agriculture_risk_calculator", "target": "agriculture_methane_intensity",
     "field_map": {"ghg_intensity_tco2_ha": "baseline_intensity"},
     "description": "Base agriculture GHG intensity provides context for methane analysis"},
    # ---- Factor Overlay Engine (Chunk 6) ----
    {"source": "ecl_climate_engine", "target": "factor_overlay_engine",
     "field_map": {"pd_climate_adjusted": "base_pd", "lgd_climate_adjusted": "base_lgd"},
     "description": "ECL outputs feed credit overlay for ESG/Geo/Tech adjustment"},
    {"source": "scenario_analysis_engine", "target": "factor_overlay_engine",
     "field_map": {"scenario_nim": "base_nim_bps", "duration_gap": "base_duration_gap"},
     "description": "Scenario engine ALM metrics feed treasury overlay"},
    {"source": "csrd_auto_populate", "target": "factor_overlay_engine",
     "field_map": {"gap_count": "current_gap_count", "pillar_gaps": "esrs_pillars"},
     "description": "CSRD gap analysis feeds regulatory compliance overlay"},
    {"source": "insurance_risk_engine", "target": "factor_overlay_engine",
     "field_map": {"base_premium": "base_premium", "loss_ratio": "base_loss_ratio"},
     "description": "Insurance risk metrics feed UW and actuarial overlays"},
    {"source": "portfolio_analytics", "target": "factor_overlay_engine",
     "field_map": {"portfolio_return": "base_return_pct", "portfolio_var": "base_var_pct"},
     "description": "Portfolio analytics feed PM and risk overlays"},
    {"source": "pe_deal_engine", "target": "factor_overlay_engine",
     "field_map": {"ev_ebitda": "base_ev_ebitda"},
     "description": "PE deal engine feeds deal scoring overlay"},
    {"source": "real_estate_valuation_engine", "target": "factor_overlay_engine",
     "field_map": {"market_value": "base_value", "noi": "base_noi"},
     "description": "RE valuation feeds green premium overlay"},
    {"source": "agriculture_risk_calculator", "target": "factor_overlay_engine",
     "field_map": {"loan_value": "base_loan_value"},
     "description": "Agriculture risk feeds sustainable ag finance overlay"},
    {"source": "china_trade_engine", "target": "factor_overlay_engine",
     "field_map": {"trade_value": "base_trade_value"},
     "description": "China trade engine feeds geopolitical trade advisory overlay"},
    {"source": "factor_overlay_engine", "target": "entity360",
     "field_map": {"enhanced_metrics": "overlay_enhanced_metrics", "composite_adjustment": "overlay_adjustment"},
     "description": "Factor overlays feed Entity 360 for unified view"},
    {"source": "factor_overlay_engine", "target": "csrd_auto_populate",
     "field_map": {"esg_factors": "overlay_esg_factors", "audit_trail": "overlay_audit"},
     "description": "Factor overlays provide ESG context for CSRD disclosures"},
    # Technology Sector → downstream
    {"source": "technology_risk_engine", "target": "csrd_auto_populate",
     "field_map": {"scope2_tco2e": "E1-6_GHG_scope2_lb", "annual_water_m3": "E3_water_consumption_m3",
                   "ewaste_tonnes": "E5_waste_generated_t", "csrd_e1_datapoints": "E1_technology_dps"},
     "description": "Technology sector outputs feed CSRD E1/E3/E5 disclosures"},
    {"source": "technology_risk_engine", "target": "entity360",
     "field_map": {"composite_esg_score": "tech_esg_score", "pue": "data_centre_pue",
                   "eed_compliant": "eed_compliance_status"},
     "description": "Technology risk profile feeds Entity 360"},
    {"source": "carbon_calculator_v2", "target": "technology_risk_engine",
     "field_map": {"scope2_lb_tco2e": "grid_emission_factor_context"},
     "description": "Carbon calculator grid EFs provide context for data centre Scope 2"},
    {"source": "technology_risk_engine", "target": "factor_overlay_engine",
     "field_map": {"pue": "facility_pue", "circularity_score": "ewaste_circularity"},
     "description": "Technology metrics feed factor overlay for tech sector adjustments"},

    # Residential RE → downstream
    {"source": "residential_re_engine", "target": "entity360",
     "field_map": {"hedonic_value_eur": "property_value", "climate_ltv": "climate_adjusted_ltv",
                   "crrem_stranding_year": "stranding_year"},
     "description": "Residential valuations feed Entity 360 property profile"},
    {"source": "residential_re_engine", "target": "csrd_auto_populate",
     "field_map": {"energy_intensity_kwh_m2": "E1-5_energy_intensity",
                   "co2_reduction_tco2_yr": "E1-6_ghg_reduction"},
     "description": "Residential energy data feeds CSRD E1 disclosures"},
    {"source": "residential_re_engine", "target": "ecl_climate_engine",
     "field_map": {"climate_ltv": "climate_adjusted_ltv", "ltv_stress_bps": "ltv_stress_bps"},
     "description": "Climate-adjusted LTV feeds ECL mortgage exposure calculations"},
    {"source": "epc_transition_engine", "target": "residential_re_engine",
     "field_map": {"epc_rating": "epc_rating", "energy_kwh_m2": "energy_kwh_m2_yr"},
     "description": "EPC data feeds residential property valuation inputs"},

    # RICS ESG → downstream
    {"source": "rics_esg_engine", "target": "entity360",
     "field_map": {"compliance_pct": "rics_compliance_pct", "compliance_band": "rics_band",
                   "uncertainty_pct": "valuation_uncertainty_pct"},
     "description": "RICS compliance feeds Entity 360 ESG profile"},
    {"source": "rics_esg_engine", "target": "factor_overlay_engine",
     "field_map": {"green_premium_pct": "re_green_premium", "brown_discount_pct": "re_brown_discount"},
     "description": "RICS ESG adjustments feed factor overlay for RE valuation"},
    {"source": "green_premium_engine", "target": "rics_esg_engine",
     "field_map": {"green_premium_pct": "green_premium_pct"},
     "description": "Green premium estimates feed RICS compliance inputs"},
    {"source": "crrem_stranding_engine", "target": "rics_esg_engine",
     "field_map": {"stranding_year": "crrem_stranding_year"},
     "description": "CRREM stranding feeds RICS transition risk assessment"},

    # Validation Summary — cross-cutting (all engines → validation)
    {"source": "validation_summary_engine", "target": "entity360",
     "field_map": {"confidence_score": "calc_confidence", "outputs_hash_sha256": "result_hash"},
     "description": "Validation envelope provides confidence and audit hash to Entity 360"},

    # Nature-RE Integration — bridging nature risk to RE valuation
    {"source": "nature_risk_calculator", "target": "nature_re_integration_engine",
     "field_map": {"overall_score": "leap_overall_score", "overall_risk_rating": "leap_risk_rating",
                   "baseline_risk_score": "water_baseline_score",
                   "impact_score": "biodiversity_impact_score"},
     "description": "TNFD LEAP, water risk, and biodiversity outputs feed nature-RE integration"},
    {"source": "nature_re_integration_engine", "target": "entity360",
     "field_map": {"nature_adjusted_value_eur": "nature_adj_value",
                   "composite_nature_score": "nature_risk_score",
                   "eu_taxonomy_nature_dnsh_pass": "eu_tax_nature_dnsh"},
     "description": "Nature-adjusted valuations feed Entity 360 property profile"},
    {"source": "nature_re_integration_engine", "target": "re_clvar_engine",
     "field_map": {"water_baseline_score": "water_stress_score",
                   "biodiversity_cap_rate_adj_bps": "nature_cap_rate_adj_bps"},
     "description": "Nature risk scores feed CLVaR physical risk inputs"},
    {"source": "nature_re_integration_engine", "target": "residential_re_engine",
     "field_map": {"nature_haircut_pct": "nature_discount_pct",
                   "bng_capex_estimate_eur": "bng_capex_eur"},
     "description": "Nature adjustments feed residential RE climate-adjusted valuation"},

    # Spatial Hazard → downstream
    {"source": "spatial_hazard_service", "target": "re_clvar_engine",
     "field_map": {"flood_zone": "flood_zone", "flood_depth_100yr_m": "flood_depth_100yr_m",
                   "heat_days_above_35c": "heat_days_above_35c",
                   "wildfire_proximity_km": "wildfire_proximity_km",
                   "water_stress_score": "water_stress_score"},
     "description": "Spatial hazard profiles auto-populate CLVaR physical risk inputs"},
    {"source": "spatial_hazard_service", "target": "climate_physical_risk_engine",
     "field_map": {"flood_zone": "flood_zone", "water_stress_score": "water_stress_score",
                   "heat_days_above_35c": "heat_days", "cyclone_exposure": "cyclone_risk"},
     "description": "Spatial hazard data feeds climate physical risk assessment"},
    {"source": "spatial_hazard_service", "target": "nature_re_integration_engine",
     "field_map": {"water_stress_score": "water_baseline_context"},
     "description": "Spatial water stress baseline provides context for nature-RE integration"},

    # Regulatory Report Compiler — inbound from multiple modules
    {"source": "carbon_calculator", "target": "regulatory_report_compiler",
     "field_map": {"scope1_tco2e": "scope1_tco2e", "scope2_tco2e": "scope2_tco2e",
                   "scope3_tco2e": "scope3_tco2e", "ghg_intensity": "ghg_intensity"},
     "description": "GHG emissions auto-populate TCFD MT-b, GRI 305, SFDR PAI 1-3, BRSR P6/Core-1"},
    {"source": "scenario_analysis_engine", "target": "regulatory_report_compiler",
     "field_map": {"scenario_results": "scenario_resilience"},
     "description": "Scenario analysis feeds TCFD STR-c, ISSB S2-SCN, SEC 1504"},
    {"source": "pcaf_engine", "target": "regulatory_report_compiler",
     "field_map": {"financed_emissions": "sfdr_pai_data", "carbon_footprint": "carbon_footprint"},
     "description": "PCAF financed emissions feed SFDR PAI indicators 1-6"},
    {"source": "csrd_kpi_store", "target": "regulatory_report_compiler",
     "field_map": {"esrs_e1_kpis": "esrs_datapoints"},
     "description": "CSRD KPI store provides ESRS datapoints for cross-referencing with BRSR"},
    {"source": "disclosure_completeness", "target": "regulatory_report_compiler",
     "field_map": {"framework_scores": "baseline_completeness"},
     "description": "Disclosure completeness baseline informs compilation gap analysis"},

    # EU ETS Engine — inbound/outbound
    {"source": "cbam_calculator", "target": "eu_ets_engine",
     "field_map": {"cbam_sector": "sector", "carbon_intensity": "installation_emissions"},
     "description": "CBAM sector classification and carbon intensity feed ETS allocation assessment"},
    {"source": "eu_ets_engine", "target": "regulatory_report_compiler",
     "field_map": {"compliance_status": "ets_compliance", "auction_cost_eur": "ets_cost_exposure"},
     "description": "ETS compliance position feeds regulatory reporting (CSRD E1, TCFD metrics)"},
    {"source": "eu_ets_engine", "target": "climate_transition_risk_engine",
     "field_map": {"carbon_price_eur": "carbon_price_input", "cap_trajectory": "policy_tightening_path"},
     "description": "ETS carbon price and cap trajectory inform transition risk assessment"},

    # EUDR Engine — inbound/outbound
    {"source": "agriculture_risk_calculator", "target": "eudr_engine",
     "field_map": {"eudr_commodities": "commodities", "country_code": "country_iso2"},
     "description": "Agriculture risk data feeds EUDR commodity scope and country assessment"},
    {"source": "nature_risk_calculator", "target": "eudr_engine",
     "field_map": {"biodiversity_impact_score": "deforestation_risk_context",
                   "protected_area_overlaps": "protected_area_proximity"},
     "description": "Nature/biodiversity risk scores provide deforestation risk context for EUDR"},
    {"source": "supply_chain_scope3_engine", "target": "eudr_engine",
     "field_map": {"supplier_tier_mapping": "supply_chain_links",
                   "scope3_cat1_tco2e": "upstream_emissions_context"},
     "description": "Supply chain mapping feeds EUDR traceability and supplier identification"},
    {"source": "eudr_engine", "target": "regulatory_report_compiler",
     "field_map": {"compliance_status": "eudr_compliance", "overall_compliance_score": "eudr_score",
                   "esrs_e4_linkage": "biodiversity_disclosure_data"},
     "description": "EUDR compliance feeds regulatory reporting (CSRD ESRS E4 biodiversity, BRSR P6)"},
    {"source": "eudr_engine", "target": "entity360",
     "field_map": {"compliance_status": "eudr_status", "overall_compliance_score": "eudr_score",
                   "due_diligence_level": "eudr_dd_level"},
     "description": "EUDR compliance status feeds Entity 360 regulatory profile"},
    {"source": "eudr_engine", "target": "factor_overlay_engine",
     "field_map": {"compliance_status": "deforestation_free_status",
                   "eu_taxonomy_biodiversity_dnsh": "taxonomy_biodiversity_dnsh"},
     "description": "EUDR compliance informs deforestation-free premium in factor overlays"},

    # CSDDD Engine — inbound/outbound
    {"source": "eudr_engine", "target": "csddd_engine",
     "field_map": {"compliance_status": "eudr_dd_status", "commodities_assessed": "deforestation_commodities"},
     "description": "EUDR due diligence feeds CSDDD environmental impact identification (Art 6 ENV-02)"},
    {"source": "supply_chain_scope3_engine", "target": "csddd_engine",
     "field_map": {"supplier_tier_mapping": "value_chain_links", "supplier_countries": "supplier_countries"},
     "description": "Supply chain mapping feeds CSDDD value chain due diligence (Art 6, Art 14)"},
    {"source": "climate_transition_risk_engine", "target": "csddd_engine",
     "field_map": {"transition_risk_score": "ghg_intensity_context", "nace_sector": "nace_codes"},
     "description": "Transition risk data informs CSDDD climate transition plan assessment (Art 22)"},
    {"source": "csddd_engine", "target": "regulatory_report_compiler",
     "field_map": {"compliance_status": "csddd_compliance", "overall_score": "csddd_score",
                   "climate_transition_plan_score": "csddd_climate_plan_score"},
     "description": "CSDDD compliance feeds regulatory reporting (CSRD ESRS S1/S2, governance)"},
    {"source": "csddd_engine", "target": "entity360",
     "field_map": {"compliance_status": "csddd_status", "penalty_exposure": "csddd_penalty_risk",
                   "grievance_mechanism_status": "csddd_grievance_status"},
     "description": "CSDDD compliance status feeds Entity 360 regulatory profile"},
    {"source": "csddd_engine", "target": "factor_overlay_engine",
     "field_map": {"risk_score": "human_rights_risk_factor", "compliance_status": "csddd_compliance"},
     "description": "CSDDD human rights risk informs factor overlays for ESG-adjusted pricing"},

    # Sovereign Climate Risk Engine — inbound/outbound
    {"source": "climate_physical_risk_engine", "target": "sovereign_climate_risk_engine",
     "field_map": {"physical_risk_score": "physical_risk_override"},
     "description": "Physical risk scores can override sovereign physical risk component"},
    {"source": "climate_transition_risk_engine", "target": "sovereign_climate_risk_engine",
     "field_map": {"transition_readiness": "transition_readiness_override"},
     "description": "Transition risk readiness can override sovereign transition component"},
    {"source": "sovereign_climate_risk_engine", "target": "portfolio_analytics_engine_v2",
     "field_map": {"composite_climate_risk_score": "sovereign_climate_risk",
                   "climate_spread_delta_bps": "sovereign_spread_overlay",
                   "notch_adjustment": "sovereign_rating_adjustment"},
     "description": "Sovereign climate risk feeds portfolio analytics for FI bond holdings"},
    {"source": "sovereign_climate_risk_engine", "target": "factor_overlay_engine",
     "field_map": {"composite_climate_risk_score": "sovereign_climate_factor",
                   "climate_spread_delta_bps": "sovereign_spread_delta"},
     "description": "Sovereign climate risk informs geopolitical factor overlays"},
    {"source": "sovereign_climate_risk_engine", "target": "ecl_climate_engine",
     "field_map": {"notch_adjustment": "sovereign_pd_adjustment",
                   "climate_spread_delta_bps": "sovereign_lgd_adjustment"},
     "description": "Sovereign climate rating adjustments feed ECL climate overlays for sovereign exposures"},

    # ── SEC Climate Disclosure Engine edges ────────────────────────────────
    {"source": "carbon_calculator", "target": "sec_climate_engine",
     "field_map": {"scope1_total_tco2e": "scope_1_total_co2e_mt",
                   "scope2_location_tco2e": "scope_2_location_co2e_mt"},
     "description": "GHG emissions data feeds SEC Item 1505 GHG disclosure assessment"},
    {"source": "climate_transition_risk_engine", "target": "sec_climate_engine",
     "field_map": {"transition_risk_score": "strategy_score",
                   "regulatory_risk_score": "risk_management_score"},
     "description": "Transition risk scores inform SEC Items 1502-1503 strategy/risk management"},
    {"source": "sec_climate_engine", "target": "regulatory_report_compiler",
     "field_map": {"overall_compliance_pct": "sec_climate_compliance",
                   "gaps": "sec_climate_gaps",
                   "cross_framework_mapping": "sec_framework_mapping"},
     "description": "SEC compliance results feed regulatory report compiler"},
    {"source": "sec_climate_engine", "target": "entity360",
     "field_map": {"overall_compliance_pct": "sec_climate_compliance_pct",
                   "filer_category": "sec_filer_category"},
     "description": "SEC filer assessment populates Entity 360 regulatory profile"},
    {"source": "sec_climate_engine", "target": "factor_overlay_engine",
     "field_map": {"overall_compliance_pct": "sec_compliance_factor",
                   "critical_gaps": "sec_critical_gap_count"},
     "description": "SEC compliance gaps inform regulatory factor overlays"},

    # ── GRI Standards Engine edges ─────────────────────────────────────────
    {"source": "carbon_calculator", "target": "gri_standards_engine",
     "field_map": {"scope1_total_tco2e": "scope_1_co2e_mt",
                   "scope2_location_tco2e": "scope_2_location_co2e_mt",
                   "scope2_market_tco2e": "scope_2_market_co2e_mt",
                   "scope3_total_tco2e": "scope_3_co2e_mt"},
     "description": "GHG emissions data feeds GRI 305 emissions disclosure assessment"},
    {"source": "gri_standards_engine", "target": "regulatory_report_compiler",
     "field_map": {"gri_compliance_level": "gri_compliance_level",
                   "completeness_pct": "gri_completeness_pct",
                   "sdg_linkage": "gri_sdg_mapping"},
     "description": "GRI content index results feed regulatory report compiler GRI section"},
    {"source": "gri_standards_engine", "target": "entity360",
     "field_map": {"gri_compliance_level": "gri_status",
                   "completeness_pct": "gri_completeness_pct"},
     "description": "GRI compliance status populates Entity 360 ESG profile"},
    {"source": "gri_standards_engine", "target": "csrd_auto_populate",
     "field_map": {"esrs_mapping": "gri_esrs_interoperability",
                   "completeness_pct": "gri_disclosure_completeness"},
     "description": "GRI-ESRS interoperability mapping supports CSRD auto-population"},
    {"source": "gri_standards_engine", "target": "factor_overlay_engine",
     "field_map": {"completeness_pct": "gri_completeness_factor",
                   "gri_compliance_level": "gri_compliance_level"},
     "description": "GRI disclosure completeness informs ESG factor overlays"},

    # ── SASB Industry Engine edges ────────────────────────────────────────
    {"source": "carbon_calculator", "target": "sasb_industry_engine",
     "field_map": {"scope1_total_tco2e": "reported_metrics.ghg_scope1",
                   "scope2_location_tco2e": "reported_metrics.ghg_scope2",
                   "total_tco2e": "reported_metrics.ghg_total"},
     "description": "GHG emissions data feeds SASB GHG Emissions topic metrics"},
    {"source": "sasb_industry_engine", "target": "regulatory_report_compiler",
     "field_map": {"completeness_pct": "sasb_completeness_pct",
                   "ifrs_s1_para55_compliant": "ifrs_s1_para55_status",
                   "issb_s2_cross_ref": "sasb_issb_cross_ref"},
     "description": "SASB assessment results feed ISSB/regulatory report sections"},
    {"source": "sasb_industry_engine", "target": "entity360",
     "field_map": {"completeness_pct": "sasb_completeness_pct",
                   "peer_rank_label": "sasb_peer_rank",
                   "sasb_industry_code": "sasb_industry"},
     "description": "SASB industry classification and completeness populate Entity 360"},
    {"source": "sasb_industry_engine", "target": "peer_benchmark_engine",
     "field_map": {"peer_comparison": "sasb_peer_metrics",
                   "completeness_pct": "sasb_completeness_for_peer"},
     "description": "SASB peer comparison feeds cross-framework peer benchmarking"},
    {"source": "sasb_industry_engine", "target": "factor_overlay_engine",
     "field_map": {"materiality_coverage_pct": "sasb_materiality_factor",
                   "avg_data_quality_score": "sasb_dqs"},
     "description": "SASB materiality and DQS inform ESG factor overlays"},

    # ── Model Validation Framework edges ──────────────────────────────────
    {"source": "ecl_climate_engine", "target": "model_validation_framework",
     "field_map": {"pd_pit": "predicted_values.pd",
                   "lgd_downturn": "predicted_values.lgd"},
     "description": "ECL model outputs feed backtesting predicted values"},
    {"source": "climate_physical_risk_engine", "target": "model_validation_framework",
     "field_map": {"physical_risk_score": "predicted_values.physical_risk"},
     "description": "Physical risk scores feed model validation backtesting"},
    {"source": "climate_transition_risk_engine", "target": "model_validation_framework",
     "field_map": {"transition_risk_score": "predicted_values.transition_risk"},
     "description": "Transition risk scores feed model validation backtesting"},
    {"source": "model_validation_framework", "target": "regulatory_report_compiler",
     "field_map": {"overall_traffic_light": "model_validation_status",
                   "bcbs239_compliance_pct": "bcbs239_compliance",
                   "eba_gl_2023_04_compliant": "eba_model_risk_compliant"},
     "description": "Model validation results feed regulatory report (EBA GL/2023/04 section)"},
    {"source": "model_validation_framework", "target": "entity360",
     "field_map": {"validation_dashboard": "model_risk_dashboard",
                   "bcbs239_compliance_pct": "bcbs239_score"},
     "description": "Model validation dashboard populates Entity 360 governance tab"},

    # ── TNFD Nature-Related Disclosures Engine edges ──────────────────────
    {"source": "nature_risk_calculator", "target": "tnfd_assessment_engine",
     "field_map": {"leap_scores": "leap_data",
                   "water_risk_score": "dependencies.water_risk",
                   "biodiversity_score": "dependencies.biodiversity"},
     "description": "Nature risk LEAP scores and water/biodiversity data feed TNFD disclosure assessment"},
    {"source": "carbon_calculator", "target": "tnfd_assessment_engine",
     "field_map": {"scope1_total_tco2e": "disclosure_data.ghg_scope1",
                   "scope2_location_tco2e": "disclosure_data.ghg_scope2"},
     "description": "GHG emissions data feeds TNFD Metrics & Targets disclosures"},
    {"source": "tnfd_assessment_engine", "target": "regulatory_report_compiler",
     "field_map": {"overall_compliance_pct": "tnfd_compliance_pct",
                   "disclosure_scores_14": "tnfd_disclosure_scores",
                   "cross_framework_mapping": "tnfd_framework_mapping"},
     "description": "TNFD assessment results feed regulatory report compiler nature section"},
    {"source": "tnfd_assessment_engine", "target": "entity360",
     "field_map": {"overall_compliance_pct": "tnfd_compliance_pct",
                   "leap_readiness_level": "tnfd_leap_readiness"},
     "description": "TNFD compliance and LEAP readiness populate Entity 360 ESG profile"},
    {"source": "tnfd_assessment_engine", "target": "factor_overlay_engine",
     "field_map": {"nature_risk_profile": "tnfd_nature_risk_factors",
                   "ecosystem_services_at_risk": "tnfd_es_risk_count"},
     "description": "TNFD nature risk profile informs biodiversity/nature factor overlays"},

    # ── CDP Climate & Water Scoring Engine edges ──────────────────────────
    {"source": "carbon_calculator", "target": "cdp_scoring_engine",
     "field_map": {"scope1_total_tco2e": "responses.c6_scope1",
                   "scope2_location_tco2e": "responses.c6_scope2",
                   "scope3_total_tco2e": "responses.c6_scope3"},
     "description": "GHG emissions data feeds CDP C6 Emissions Data module responses"},
    {"source": "cdp_scoring_engine", "target": "regulatory_report_compiler",
     "field_map": {"grade": "cdp_grade",
                   "overall_score_pct": "cdp_score_pct",
                   "cross_framework_mapping": "cdp_framework_mapping"},
     "description": "CDP scores and grade feed regulatory report compiler"},
    {"source": "cdp_scoring_engine", "target": "entity360",
     "field_map": {"grade": "cdp_grade",
                   "overall_score_pct": "cdp_score_pct",
                   "activity_group": "cdp_activity_group"},
     "description": "CDP grade and activity group populate Entity 360 ESG profile"},
    {"source": "cdp_scoring_engine", "target": "peer_benchmark_engine",
     "field_map": {"peer_comparison": "cdp_peer_metrics",
                   "grade": "cdp_grade_for_peer"},
     "description": "CDP peer comparison feeds cross-framework peer benchmarking"},
    {"source": "cdp_scoring_engine", "target": "factor_overlay_engine",
     "field_map": {"overall_score_pct": "cdp_score_factor",
                   "grade": "cdp_grade"},
     "description": "CDP score and grade inform ESG factor overlays"},

    # ── PCAF Data Quality Score Engine edges ────────────────────────────
    {"source": "pcaf_waci_engine", "target": "pcaf_quality_engine",
     "field_map": {"financed_emissions_tco2e": "reported_emissions",
                   "attribution_factor": "attribution_factor",
                   "waci_tco2e_per_meur": "carbon_intensity"},
     "description": "PCAF WACI financed emissions feed DQS quality scoring per holding"},
    {"source": "carbon_calculator", "target": "pcaf_quality_engine",
     "field_map": {"scope1_total_tco2e": "reported_emissions.scope1",
                   "scope2_location_tco2e": "reported_emissions.scope2",
                   "scope3_total_tco2e": "reported_emissions.scope3"},
     "description": "GHG emissions data feeds PCAF holding-level emissions quality scoring"},
    {"source": "pcaf_quality_engine", "target": "sfdr_report_generator",
     "field_map": {"sfdr_pai_indicators": "pai_1_2_3_financed_emissions",
                   "portfolio_weighted_dqs": "pcaf_data_quality_score",
                   "total_financed_emissions_tco2": "total_financed_ghg"},
     "description": "PCAF DQS and PAI indicators feed SFDR Article 4 principal adverse impact reporting"},
    {"source": "pcaf_quality_engine", "target": "regulatory_report_compiler",
     "field_map": {"portfolio_weighted_dqs": "pcaf_dqs",
                   "dqs_distribution": "pcaf_dqs_breakdown",
                   "cross_framework_disclosures": "pcaf_framework_mapping"},
     "description": "PCAF quality reports feed regulatory report compiler financed emissions section"},
    {"source": "pcaf_quality_engine", "target": "entity360",
     "field_map": {"weighted_dqs": "pcaf_data_quality_score",
                   "financed_emissions_tco2": "pcaf_financed_emissions"},
     "description": "PCAF quality score populates Entity 360 financed emissions tab"},
    {"source": "pcaf_quality_engine", "target": "factor_overlay_engine",
     "field_map": {"confidence_weight": "pcaf_confidence_factor",
                   "weighted_dqs": "pcaf_dqs_factor"},
     "description": "PCAF confidence weights inform factor overlay uncertainty propagation"},

    # ── Basel III/IV Regulatory Capital Engine edges ────────────────────
    {"source": "ecl_climate_engine", "target": "basel_capital_engine",
     "field_map": {"pd_through_the_cycle": "exposures.pd",
                   "lgd_downturn": "exposures.lgd",
                   "ead_ccf": "exposures.ead_eur"},
     "description": "ECL climate PD/LGD/EAD feed Basel IRB capital requirement calculation"},
    {"source": "scenario_analysis_engine", "target": "basel_capital_engine",
     "field_map": {"scenario_results": "climate_scenarios",
                   "stress_multipliers": "climate_scenarios.stress_factors"},
     "description": "NGFS scenario analysis feeds Basel climate stress capital adequacy testing"},
    {"source": "basel_capital_engine", "target": "regulatory_report_compiler",
     "field_map": {"cet1_ratio": "basel_cet1_ratio",
                   "tier1_ratio": "basel_tier1_ratio",
                   "total_capital_ratio": "basel_total_ratio",
                   "leverage_ratio": "basel_leverage_ratio",
                   "lcr_ratio": "basel_lcr", "nsfr_ratio": "basel_nsfr"},
     "description": "Basel capital ratios feed regulatory report compiler Pillar 3 section"},
    {"source": "basel_capital_engine", "target": "entity360",
     "field_map": {"cet1_ratio": "capital_cet1_ratio",
                   "overall_rag_status": "capital_rag_status",
                   "lcr_ratio": "liquidity_lcr_ratio"},
     "description": "Basel capital adequacy populates Entity 360 banking risk tab"},
    {"source": "basel_capital_engine", "target": "factor_overlay_engine",
     "field_map": {"climate_rwa_addon": "climate_capital_addon_factor",
                   "cet1_surplus_deficit": "capital_headroom_factor"},
     "description": "Basel climate RWA add-ons inform factor overlay capital stress scenarios"},

    # ── EU Taxonomy Alignment Engine edges ─────────────────────────────
    {"source": "carbon_calculator", "target": "eu_taxonomy_engine",
     "field_map": {"scope1_total_tco2e": "emission_intensity",
                   "scope2_location_tco2e": "emission_intensity.scope2"},
     "description": "GHG emissions feed EU Taxonomy substantial contribution thresholds"},
    {"source": "csrd_engine", "target": "eu_taxonomy_engine",
     "field_map": {"esrs_e1_disclosures": "evidence_data.esrs_e1",
                   "esrs_e2_disclosures": "evidence_data.esrs_e2"},
     "description": "CSRD ESRS E1-E5 disclosures provide evidence for taxonomy DNSH checks"},
    {"source": "eu_taxonomy_engine", "target": "sfdr_report_generator",
     "field_map": {"turnover_alignment_pct": "taxonomy_turnover_alignment",
                   "capex_alignment_pct": "taxonomy_capex_alignment",
                   "sfdr_article_classification": "fund_article_classification"},
     "description": "EU Taxonomy alignment KPIs feed SFDR Art 5/6 disclosures"},
    {"source": "eu_taxonomy_engine", "target": "regulatory_report_compiler",
     "field_map": {"turnover_alignment_pct": "eu_taxonomy_turnover_kpi",
                   "capex_alignment_pct": "eu_taxonomy_capex_kpi",
                   "green_asset_ratio": "gar_ratio"},
     "description": "Taxonomy KPIs feed compiled regulatory report Art 8 section"},
    {"source": "eu_taxonomy_engine", "target": "entity360",
     "field_map": {"turnover_alignment_pct": "taxonomy_alignment_pct",
                   "taxonomy_aligned": "taxonomy_status"},
     "description": "Taxonomy alignment populates Entity 360 sustainability tab"},
    {"source": "eu_taxonomy_engine", "target": "factor_overlay_engine",
     "field_map": {"green_asset_ratio": "taxonomy_gar_factor",
                   "enabling_share_pct": "taxonomy_enabling_factor"},
     "description": "Taxonomy GAR and enabling share inform green premium factor overlays"},
    {"source": "eu_taxonomy_engine", "target": "transition_plan_engine",
     "field_map": {"capex_alignment_pct": "plan_data.capex_aligned_pct",
                   "turnover_alignment_pct": "plan_data.revenue_aligned_pct"},
     "description": "Taxonomy CapEx/Turnover alignment feeds transition plan financial commitment"},

    # ── Climate Transition Plan Assessment Engine edges ────────────────
    {"source": "carbon_calculator", "target": "transition_plan_engine",
     "field_map": {"scope1_total_tco2e": "scope1_emissions",
                   "scope2_location_tco2e": "scope2_emissions",
                   "scope3_total_tco2e": "scope3_emissions"},
     "description": "GHG emissions baseline feeds transition plan target assessment"},
    {"source": "scenario_analysis_engine", "target": "transition_plan_engine",
     "field_map": {"scenario_results": "plan_data.scenario_analysis",
                   "ngfs_scenarios": "plan_data.climate_scenarios"},
     "description": "NGFS scenarios feed transition plan pathway alignment assessment"},
    {"source": "csddd_engine", "target": "transition_plan_engine",
     "field_map": {"climate_transition_plan": "plan_data.csddd_plan",
                   "dd_compliance_score": "plan_data.csddd_dd_score"},
     "description": "CSDDD Art 22 climate plan requirements feed compliance assessment"},
    {"source": "csrd_engine", "target": "transition_plan_engine",
     "field_map": {"esrs_e1_transition_plan": "plan_data.esrs_e1_plan",
                   "esrs_e1_ghg_emissions": "plan_data.esrs_e1_ghg"},
     "description": "CSRD ESRS E1 transition plan disclosures feed cross-framework mapping"},
    {"source": "cdp_scoring_engine", "target": "transition_plan_engine",
     "field_map": {"module_scores.C4": "plan_data.cdp_c4_responses",
                   "overall_score_pct": "plan_data.cdp_overall_score"},
     "description": "CDP C4 targets and performance scores feed cross-framework assessment"},
    {"source": "transition_plan_engine", "target": "regulatory_report_compiler",
     "field_map": {"overall_score": "transition_plan_score",
                   "overall_rating": "transition_plan_rating",
                   "csddd_compliance": "csddd_art22_compliance"},
     "description": "Transition plan assessment feeds regulatory report climate section"},
    {"source": "transition_plan_engine", "target": "entity360",
     "field_map": {"overall_rating": "transition_plan_status",
                   "target_credibility_score": "target_credibility",
                   "paris_aligned": "paris_alignment_status"},
     "description": "Transition plan rating populates Entity 360 climate strategy tab"},
    {"source": "transition_plan_engine", "target": "factor_overlay_engine",
     "field_map": {"target_credibility_score": "transition_credibility_factor",
                   "implementation_maturity_score": "transition_maturity_factor"},
     "description": "Transition plan credibility and maturity inform ESG factor overlays"},

    # ── Double Materiality Assessment Engine edges ──────────────────────
    {"source": "csrd_engine", "target": "double_materiality_engine",
     "field_map": {"esrs_topics_disclosed": "topic_scores",
                   "materiality_assessment": "prior_assessment"},
     "description": "CSRD ESRS disclosure data feeds DMA topic scoring"},
    {"source": "gri_standards_engine", "target": "double_materiality_engine",
     "field_map": {"topics_reported": "impact_topics",
                   "sdg_coverage": "sdg_linkage"},
     "description": "GRI reported topics inform impact materiality assessment"},
    {"source": "double_materiality_engine", "target": "csrd_engine",
     "field_map": {"material_topics_list": "material_topics_input",
                   "materiality_classification": "topic_classification"},
     "description": "DMA results determine which ESRS topics require disclosure"},
    {"source": "double_materiality_engine", "target": "regulatory_report_compiler",
     "field_map": {"dma_report": "dma_section",
                   "material_topics_list": "material_topics"},
     "description": "DMA report feeds regulatory disclosure materiality section"},
    {"source": "double_materiality_engine", "target": "entity360",
     "field_map": {"material_topics_list": "material_esrs_topics",
                   "materiality_classification": "materiality_profile"},
     "description": "Material topics populate Entity 360 ESG materiality tab"},
    {"source": "double_materiality_engine", "target": "factor_overlay_engine",
     "field_map": {"impact_materiality_scores": "esrs_impact_factors",
                   "financial_materiality_scores": "esrs_financial_factors"},
     "description": "DMA scores inform factor overlay ESG adjustments"},

    # ── SFDR PAI Calculation Engine edges ───────────────────────────────
    {"source": "carbon_calculator", "target": "sfdr_pai_engine",
     "field_map": {"scope1_total_tco2e": "scope1_emissions",
                   "scope2_location_tco2e": "scope2_emissions",
                   "scope3_total_tco2e": "scope3_emissions"},
     "description": "GHG emissions feed PAI 1-3 (GHG emissions, carbon footprint, GHG intensity)"},
    {"source": "pcaf_waci_engine", "target": "sfdr_pai_engine",
     "field_map": {"financed_emissions": "pai_portfolio_emissions",
                   "data_quality_score": "pai_data_quality"},
     "description": "PCAF financed emissions feed PAI 1-2 portfolio-level calculations"},
    {"source": "nature_risk_engine", "target": "sfdr_pai_engine",
     "field_map": {"biodiversity_risk_score": "pai7_biodiversity",
                   "water_risk_score": "pai8_water_emissions"},
     "description": "Nature risk assessment feeds PAI 7 (biodiversity) and PAI 8 (water)"},
    {"source": "eu_taxonomy_engine", "target": "sfdr_pai_engine",
     "field_map": {"taxonomy_alignment": "taxonomy_alignment_pct",
                   "dnsh_assessment": "pai_dnsh_input"},
     "description": "EU Taxonomy alignment and DNSH feed SFDR PAI DNSH assessment"},
    {"source": "sfdr_pai_engine", "target": "regulatory_report_compiler",
     "field_map": {"pai_statement_disclosure": "sfdr_pai_section",
                   "entity_classification_art6_8_9": "sfdr_classification"},
     "description": "PAI statement and entity classification feed SFDR regulatory disclosure"},
    {"source": "sfdr_pai_engine", "target": "entity360",
     "field_map": {"all_18_mandatory_pais": "pai_indicators",
                   "entity_classification_art6_8_9": "sfdr_article"},
     "description": "PAI indicator values populate Entity 360 SFDR tab"},
    {"source": "sfdr_pai_engine", "target": "factor_overlay_engine",
     "field_map": {"pai_calculated_value": "pai_factor_adjustment",
                   "peer_benchmark_percentile": "pai_peer_position"},
     "description": "PAI values and benchmarks inform factor overlay regulatory adjustments"},
    {"source": "sfdr_pai_engine", "target": "double_materiality_engine",
     "field_map": {"all_18_mandatory_pais": "financial_materiality_input",
                   "data_coverage_assessment": "data_quality_input"},
     "description": "PAI indicators inform financial materiality scoring in DMA"},
    # ---- DME (Dynamic Materiality Engine) edges ----
    {"source": "dme_velocity_engine", "target": "dme_alert_engine",
     "field_map": {"z_score": "velocity_z_score", "acceleration": "acceleration"},
     "description": "Velocity z-scores and acceleration feed alert tier classification"},
    {"source": "dme_velocity_engine", "target": "dme_dmi_engine",
     "field_map": {"velocity_smoothed": "velocity_adjustment", "regime": "regime_input"},
     "description": "Smoothed velocity and regime feed DMI score adjustment"},
    {"source": "dme_velocity_engine", "target": "dme_greenwashing_engine",
     "field_map": {"velocity_raw": "velocity_latest", "sigma_classification": "sigma_flag"},
     "description": "Raw velocity and sigma classification feed greenwashing detection"},
    {"source": "dme_velocity_engine", "target": "portfolio_health_engine",
     "field_map": {"velocity_smoothed": "metric_velocity", "regime": "regime_signal"},
     "description": "Velocity signals feed portfolio health monitoring"},
    {"source": "dme_greenwashing_engine", "target": "entity360_engine",
     "field_map": {"greenwashing_detected": "greenwash_flag", "severity": "greenwash_severity",
                   "credibility_gap": "credibility_gap"},
     "description": "Greenwashing detection feeds Entity 360 ESG credibility profile"},
    {"source": "dme_greenwashing_engine", "target": "transition_plan_engine",
     "field_map": {"greenwashing_detected": "greenwash_alert", "divergence_z_score": "divergence_score"},
     "description": "Greenwashing signals inform transition plan credibility assessment"},
    {"source": "dme_nlp_pulse_engine", "target": "entity360_engine",
     "field_map": {"aggregate_pulse": "nlp_pulse_score", "credibility_adjusted_pulse": "adjusted_pulse"},
     "description": "NLP pulse scores feed Entity 360 sentiment profile"},
    {"source": "dme_nlp_pulse_engine", "target": "dme_greenwashing_engine",
     "field_map": {"pulse_discounted": "nlp_signal", "greenwash_discount": "nlp_greenwash_discount"},
     "description": "Discounted NLP pulse and greenwash discount feed greenwashing engine"},
    {"source": "gdelt_controversy", "target": "dme_nlp_pulse_engine",
     "field_map": {"controversy_score": "sentiment_score", "event_type": "event_type"},
     "description": "GDELT controversy events feed NLP pulse engine sentiment input"},
    {"source": "dme_policy_tracker_engine", "target": "carbon_prices",
     "field_map": {"carbon_price_velocity": "price_velocity_signal",
                   "composite_velocity": "policy_momentum"},
     "description": "Policy tracker carbon price velocity feeds carbon price forecasting"},
    {"source": "dme_policy_tracker_engine", "target": "eudr_engine",
     "field_map": {"regulatory_pipeline_velocity": "regulatory_velocity",
                   "enforcement_velocity": "enforcement_signal"},
     "description": "Regulatory pipeline velocity informs EUDR enforcement readiness"},
    {"source": "dme_policy_tracker_engine", "target": "sovereign_climate_risk_engine",
     "field_map": {"composite_velocity": "policy_velocity_input",
                   "disclosure_mandate_velocity": "disclosure_momentum"},
     "description": "Policy momentum feeds sovereign climate risk transition readiness"},
    {"source": "dme_contagion_engine", "target": "banking_risk_engine",
     "field_map": {"el_amplification": "contagion_el_multiplier",
                   "spectral_radius": "systemic_risk_indicator"},
     "description": "Contagion EL amplification and spectral radius feed banking risk"},
    {"source": "dme_contagion_engine", "target": "stress_test_runner",
     "field_map": {"var_amplification": "contagion_var_adj",
                   "es_amplification": "contagion_es_adj"},
     "description": "VaR and ES amplification feed stress test contagion overlays"},
    {"source": "dme_contagion_engine", "target": "ecl_climate_engine",
     "field_map": {"el_amplification": "contagion_multiplier",
                   "aggregated_intensity": "contagion_intensity"},
     "description": "Contagion intensity amplifies ECL climate overlay estimates"},
    {"source": "dme_alert_engine", "target": "portfolio_health_engine",
     "field_map": {"alert_tier": "alert_tier", "priority_score": "alert_priority",
                   "response_sla_hours": "sla_hours"},
     "description": "Alert tiers and priority scores feed portfolio health dashboard"},
    {"source": "dme_dmi_engine", "target": "double_materiality_engine",
     "field_map": {"dmi_score_adjusted": "dynamic_materiality_score",
                   "velocity_adjustment": "velocity_adj"},
     "description": "DMI adjusted scores feed double materiality assessment"},
    {"source": "dme_dmi_engine", "target": "factor_overlay_engine",
     "field_map": {"dmi_score_adjusted": "dmi_factor",
                   "concentration_penalty": "concentration_adj"},
     "description": "DMI scores and concentration penalties feed factor overlay engine"},
    {"source": "pcaf_waci_engine", "target": "dme_dmi_engine",
     "field_map": {"financed_emissions_tco2e": "entity_emissions",
                   "pcaf_dqs": "pcaf_quality"},
     "description": "PCAF financed emissions and DQS feed DMI financed emissions calculation"},

    # ---- Factor Registry edges ----
    {"source": "dme_factor_registry", "target": "factor_overlay_engine",
     "field_map": {"factor_definitions": "factor_metadata", "overlay_mapping": "registry_keys"},
     "description": "Unified factor registry provides metadata to overlay engine"},
    {"source": "dme_factor_registry", "target": "dme_velocity_engine",
     "field_map": {"ewma_alpha": "alpha", "alert_thresholds": "thresholds"},
     "description": "Factor-specific velocity parameters and alert thresholds"},
    {"source": "dme_factor_registry", "target": "dme_dmi_engine",
     "field_map": {"factor_definitions": "factor_weights", "pcaf_dq": "dqs"},
     "description": "Factor definitions with PCAF DQ tiers feed DMI scoring"},

    # ---- Sentiment Analysis Engine edges (inbound) ----
    {"source": "dme_nlp_pulse_engine", "target": "sentiment_analysis_engine",
     "field_map": {"pulse_score": "raw_sentiment", "source_tier": "credibility_tier"},
     "description": "NLP pulse scores with credibility feed sentiment aggregation"},
    {"source": "dme_greenwashing_engine", "target": "sentiment_analysis_engine",
     "field_map": {"divergence_flag": "controversy_flag", "cusum_signal": "greenwash_signal"},
     "description": "Greenwashing divergence flags feed controversy scoring"},
    {"source": "gdelt_controversy", "target": "sentiment_analysis_engine",
     "field_map": {"controversy_score": "raw_sentiment", "event_type": "signal_type"},
     "description": "GDELT event controversy scores feed sentiment pipeline"},
    {"source": "company_profiles", "target": "sentiment_analysis_engine",
     "field_map": {"lei": "entity_id", "sector_nace": "sector", "country": "geographic_scope"},
     "description": "Company profile data enriches entity matching in sentiment"},
    {"source": "engagement_tracker", "target": "sentiment_analysis_engine",
     "field_map": {"engagement_outcome": "raw_sentiment", "engagement_type": "signal_type"},
     "description": "CA100+ engagement outcomes feed investor sentiment channel"},
    {"source": "factor_overlay_engine", "target": "sentiment_analysis_engine",
     "field_map": {"esg_factor_scores": "esg_context", "confidence": "factor_confidence"},
     "description": "ESG factor context for sentiment credibility weighting"},

    # ---- Sentiment Analysis Engine edges (outbound) ----
    {"source": "sentiment_analysis_engine", "target": "ecl_calculator",
     "field_map": {"pd_multiplier": "sentiment_pd_adj", "sentiment_flag": "sentiment_regime"},
     "description": "Sentiment-based PD adjustment (±15%) feeds ECL credit risk"},
    {"source": "sentiment_analysis_engine", "target": "portfolio_analytics",
     "field_map": {"composite_score": "entity_sentiment", "regime": "sentiment_regime"},
     "description": "Entity sentiment scores feed portfolio analytics heatmap"},
    {"source": "sentiment_analysis_engine", "target": "dme_dmi_engine",
     "field_map": {"materiality_signal": "sentiment_materiality", "velocity_signal": "sentiment_velocity"},
     "description": "Sentiment materiality signal feeds DMI dynamic scoring"},
    {"source": "sentiment_analysis_engine", "target": "dme_alert_engine",
     "field_map": {"alert_tier": "sentiment_alert", "z_score": "sentiment_z"},
     "description": "Sentiment alert tiers feed DME alert engine for compound triggers"},
    {"source": "sentiment_analysis_engine", "target": "dme_greenwashing_engine",
     "field_map": {"media_sentiment": "public_perception", "ngo_sentiment": "ngo_assessment"},
     "description": "Media vs NGO sentiment divergence feeds greenwashing detection"},
    {"source": "sentiment_analysis_engine", "target": "sovereign_climate_risk_engine",
     "field_map": {"country_sentiment_adjustment": "sentiment_adj", "regime": "sentiment_regime"},
     "description": "Country-level sentiment context adjusts sovereign risk scores"},
    {"source": "sentiment_analysis_engine", "target": "double_materiality_engine",
     "field_map": {"stakeholder_salience": "stakeholder_weights", "esg_materiality": "esg_sentiment"},
     "description": "Stakeholder salience weighting feeds double materiality assessment"},
    {"source": "sentiment_analysis_engine", "target": "dme_contagion_engine",
     "field_map": {"sentiment_intensity": "cascade_intensity", "cascade_risk": "propagation_flag"},
     "description": "Sentiment cascade risk feeds contagion engine propagation model"},
    {"source": "sentiment_analysis_engine", "target": "pe_deal_pipeline",
     "field_map": {"reputation_score": "target_reputation", "stakeholder_risk_flags": "risk_flags"},
     "description": "Reputation scores and risk flags feed PE deal screening"},
    {"source": "sentiment_analysis_engine", "target": "real_estate_valuation",
     "field_map": {"reputation_adjustment_pct": "brand_adj", "community_sentiment": "neighborhood_score"},
     "description": "Brand/neighborhood reputation feeds real estate valuation adjustments"},
]


# ---------------------------------------------------------------------------
# Data Quality Configuration
# ---------------------------------------------------------------------------

DQS_TO_CONFIDENCE: dict[int, float] = {
    1: 1.00,  # Verified/audited data
    2: 0.90,  # Reported data
    3: 0.70,  # Physical activity-based estimates
    4: 0.50,  # Economic activity-based estimates
    5: 0.30,  # Estimated (revenue proxy)
}

QUALITY_THRESHOLDS = {
    "high": 0.70,
    "medium": 0.40,
    "low": 0.0,
}


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class LineageNode:
    """A single node in a data lineage chain."""
    module_id: str
    module_label: str
    category: str
    operation: str  # "source" | "transform" | "output" | "bridge"
    input_fields: list[str]
    output_fields: list[str]
    quality_score: float  # 0.0 - 1.0
    quality_label: str  # "high" | "medium" | "low"
    reference_data_used: list[str]
    depth: int  # 0 = root/source


@dataclass
class LineageGap:
    """A gap or broken link in the lineage chain."""
    source_module: str
    target_module: str
    missing_fields: list[str]
    severity: str  # "critical" | "high" | "medium" | "low"
    remediation: str
    reference_data_needed: list[str]


@dataclass
class LineageChain:
    """Complete lineage trace result."""
    entity_id: str
    target_module: str
    nodes: list[LineageNode]
    total_chain_length: int
    root_sources: list[str]  # Ultimate upstream modules
    data_quality_score: float  # Aggregate (weakest-link-weighted)
    quality_label: str
    gaps: list[LineageGap]
    reference_data_used: list[str]  # All ref data across the chain
    has_complete_lineage: bool


@dataclass
class ModuleGraphEdge:
    """An edge in the module dependency graph."""
    source: str
    target: str
    field_count: int
    description: str


@dataclass
class ModuleGraphResult:
    """Full module dependency graph."""
    total_modules: int
    total_edges: int
    modules: list[dict]  # [{id, label, category, input_count, output_count}]
    edges: list[ModuleGraphEdge]
    root_modules: list[str]  # Modules with no upstream dependencies
    leaf_modules: list[str]  # Modules with no downstream consumers
    orphan_modules: list[str]  # Modules not connected to any other
    bridge_modules: list[str]  # Cross-module bridges (high fan-in + fan-out)


@dataclass
class QualityPropagationResult:
    """Quality score propagation for an entity across modules."""
    entity_id: str
    module_quality: dict[str, float]  # {module_id: quality_score}
    weakest_links: list[dict]  # [{module_id, score, reason}]
    overall_quality: float
    quality_label: str
    recommendations: list[str]


@dataclass
class PlatformGapAnalysis:
    """Platform-wide lineage gap analysis."""
    total_edges: int
    complete_edges: int
    broken_edges: int
    completeness_pct: float
    gaps: list[LineageGap]
    critical_gaps: list[LineageGap]
    reference_data_missing: list[dict]  # [{dataset, needed_by, source}]
    recommendations: list[str]


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class DataLineageEngine:
    """
    Cross-module data lineage engine.

    Builds and queries a directed acyclic graph (DAG) of all platform module
    data flows. Traces lineage chains, propagates quality scores, and
    identifies gaps in the data pipeline.

    Calculation Logic:
      1. Module graph built from MODULE_DEPENDENCIES edges
      2. trace_lineage() performs reverse BFS from target module to all sources
      3. Quality propagation: downstream_q = min(upstream_q * edge_confidence, own_q)
      4. Gap detection: any edge where source outputs don't cover target inputs

    Stakeholder Insights:
      - Audit/Compliance: complete data provenance for any KPI
      - Risk Management: quality degradation points across calculation chains
      - Data Management: reference data freshness and completeness
      - Regulatory: BCBS 239 compliant data lineage documentation
    """

    def __init__(self):
        self._signatures = MODULE_SIGNATURES
        self._dependencies = MODULE_DEPENDENCIES
        self._adj_forward: dict[str, list[dict]] = {}  # source -> [edge]
        self._adj_reverse: dict[str, list[dict]] = {}  # target -> [edge]
        self._build_graph()

    def _build_graph(self):
        """Build adjacency lists from dependency edges."""
        for dep in self._dependencies:
            src = dep["source"]
            tgt = dep["target"]
            self._adj_forward.setdefault(src, []).append(dep)
            self._adj_reverse.setdefault(tgt, []).append(dep)

    # ----- Lineage Tracing -----

    def trace_lineage(
        self,
        target_module: str,
        entity_id: str = "generic",
        module_quality: dict[str, float] = None,
    ) -> LineageChain:
        """
        Trace the full upstream lineage for a target module.

        Performs reverse BFS from target_module, following all upstream
        dependencies to root sources. Computes quality propagation at
        each node.

        Parameters:
            target_module: Module to trace lineage for
            entity_id: Entity context (for quality lookup)
            module_quality: Override quality scores {module_id: 0.0-1.0}

        Returns:
            LineageChain with full node list, quality scores, and gaps
        """
        module_quality = module_quality or {}
        nodes = []
        visited = set()
        gaps = []
        all_ref_data = []
        root_sources = []

        def _walk(mod_id: str, depth: int):
            if mod_id in visited:
                return
            visited.add(mod_id)

            sig = self._signatures.get(mod_id)
            if sig is None:
                return

            # Quality for this node
            q_score = module_quality.get(mod_id, 0.7)  # Default medium
            q_label = self._quality_label(q_score)

            # Upstream edges
            upstream = self._adj_reverse.get(mod_id, [])

            if not upstream:
                operation = "source"
                root_sources.append(mod_id)
            elif mod_id in ("pcaf_ecl_bridge", "entity360", "china_trade_engine"):
                operation = "bridge"
            else:
                operation = "transform"

            ref_data = sig.get("reference_data", [])
            all_ref_data.extend(ref_data)

            nodes.append(LineageNode(
                module_id=mod_id,
                module_label=sig["label"],
                category=sig["category"],
                operation=operation,
                input_fields=sig.get("inputs", []),
                output_fields=sig.get("outputs", []),
                quality_score=round(q_score, 2),
                quality_label=q_label,
                reference_data_used=ref_data,
                depth=depth,
            ))

            # Walk upstream
            for edge in upstream:
                src = edge["source"]
                src_sig = self._signatures.get(src)
                if src_sig:
                    # Check for gaps — do source outputs cover the field mapping?
                    src_outputs = set(src_sig.get("outputs", []))
                    mapped_fields = set(edge.get("field_map", {}).keys())
                    missing = mapped_fields - src_outputs
                    if missing:
                        gaps.append(LineageGap(
                            source_module=src,
                            target_module=mod_id,
                            missing_fields=list(missing),
                            severity="high" if len(missing) > 2 else "medium",
                            remediation=f"Add outputs {missing} to {src}",
                            reference_data_needed=[],
                        ))

                _walk(src, depth + 1)

        _walk(target_module, 0)

        # Sort nodes by depth (deepest first = sources first)
        nodes.sort(key=lambda n: -n.depth)

        # Aggregate quality — weakest link
        if nodes:
            agg_quality = min(n.quality_score for n in nodes)
        else:
            agg_quality = 0.0

        unique_ref = sorted(set(all_ref_data))

        return LineageChain(
            entity_id=entity_id,
            target_module=target_module,
            nodes=nodes,
            total_chain_length=len(nodes),
            root_sources=root_sources,
            data_quality_score=round(agg_quality, 2),
            quality_label=self._quality_label(agg_quality),
            gaps=gaps,
            reference_data_used=unique_ref,
            has_complete_lineage=len(gaps) == 0,
        )

    # ----- Gap Analysis -----

    def find_gaps(self) -> PlatformGapAnalysis:
        """
        Scan all dependency edges for lineage gaps across the platform.

        Identifies:
          - Broken field mappings (source doesn't produce mapped field)
          - Missing module signatures (referenced but not registered)
          - Missing reference data (needed but not cataloged)

        Returns:
            PlatformGapAnalysis with all gaps, severity, and remediation
        """
        gaps = []
        complete = 0
        broken = 0
        ref_missing = []

        for dep in self._dependencies:
            src = dep["source"]
            tgt = dep["target"]
            src_sig = self._signatures.get(src)
            tgt_sig = self._signatures.get(tgt)

            if not src_sig:
                gaps.append(LineageGap(
                    source_module=src, target_module=tgt,
                    missing_fields=[], severity="critical",
                    remediation=f"Register module signature for '{src}'",
                    reference_data_needed=[],
                ))
                broken += 1
                continue

            if not tgt_sig:
                gaps.append(LineageGap(
                    source_module=src, target_module=tgt,
                    missing_fields=[], severity="critical",
                    remediation=f"Register module signature for '{tgt}'",
                    reference_data_needed=[],
                ))
                broken += 1
                continue

            # Check field mapping completeness
            field_map = dep.get("field_map", {})
            src_outputs = set(src_sig.get("outputs", []))
            missing = [f for f in field_map.keys() if f not in src_outputs]

            if missing:
                gaps.append(LineageGap(
                    source_module=src, target_module=tgt,
                    missing_fields=missing,
                    severity="high" if len(missing) > 2 else "medium",
                    remediation=f"Ensure {src} produces: {', '.join(missing)}",
                    reference_data_needed=[],
                ))
                broken += 1
            else:
                complete += 1

        # Identify modules not in any dependency
        all_in_deps = set()
        for dep in self._dependencies:
            all_in_deps.add(dep["source"])
            all_in_deps.add(dep["target"])

        orphans = set(self._signatures.keys()) - all_in_deps
        for orphan in orphans:
            sig = self._signatures[orphan]
            ref_data = sig.get("reference_data", [])
            if ref_data:
                for rd in ref_data:
                    ref_missing.append({
                        "dataset": rd,
                        "needed_by": [orphan],
                        "source": "embedded",
                    })

        total = len(self._dependencies)
        pct = (complete / total * 100) if total > 0 else 0

        critical = [g for g in gaps if g.severity == "critical"]

        recs = []
        if critical:
            recs.append(f"{len(critical)} critical lineage gaps — register missing module signatures")
        if broken > 0:
            recs.append(f"{broken} broken edges — verify field mappings between modules")
        if orphans:
            recs.append(f"{len(orphans)} orphan modules not in dependency graph — assess integration need")
        if pct < 80:
            recs.append(f"Lineage completeness {pct:.0f}% — target 90%+ for BCBS 239 compliance")

        return PlatformGapAnalysis(
            total_edges=total,
            complete_edges=complete,
            broken_edges=broken,
            completeness_pct=round(pct, 1),
            gaps=gaps,
            critical_gaps=critical,
            reference_data_missing=ref_missing,
            recommendations=recs,
        )

    # ----- Module Dependency Graph -----

    def get_module_graph(self) -> ModuleGraphResult:
        """
        Build the full module dependency graph.

        Returns:
            ModuleGraphResult with all modules, edges, and topology analysis
        """
        modules = []
        for mod_id, sig in self._signatures.items():
            modules.append({
                "id": mod_id,
                "label": sig["label"],
                "category": sig["category"],
                "input_count": len(sig.get("inputs", [])),
                "output_count": len(sig.get("outputs", [])),
                "reference_data_count": len(sig.get("reference_data", [])),
            })

        edges = []
        for dep in self._dependencies:
            edges.append(ModuleGraphEdge(
                source=dep["source"],
                target=dep["target"],
                field_count=len(dep.get("field_map", {})),
                description=dep.get("description", ""),
            ))

        # Topology
        sources = set(d["source"] for d in self._dependencies)
        targets = set(d["target"] for d in self._dependencies)
        all_connected = sources | targets

        root_mods = sorted(sources - targets)  # No upstream
        leaf_mods = sorted(targets - sources)  # No downstream
        orphans = sorted(set(self._signatures.keys()) - all_connected)

        # Bridge modules: both upstream and downstream, fan-in >= 2 AND fan-out >= 2
        bridge_mods = []
        for mod in all_connected:
            fan_in = len(self._adj_reverse.get(mod, []))
            fan_out = len(self._adj_forward.get(mod, []))
            if fan_in >= 2 and fan_out >= 2:
                bridge_mods.append(mod)

        return ModuleGraphResult(
            total_modules=len(self._signatures),
            total_edges=len(self._dependencies),
            modules=modules,
            edges=edges,
            root_modules=root_mods,
            leaf_modules=leaf_mods,
            orphan_modules=orphans,
            bridge_modules=sorted(bridge_mods),
        )

    # ----- Quality Propagation -----

    def propagate_quality(
        self,
        entity_id: str,
        module_quality: dict[str, float],
    ) -> QualityPropagationResult:
        """
        Propagate data quality scores through the dependency graph.

        Starting from source modules (with given quality scores), propagates
        downstream using weakest-link principle: downstream quality cannot
        exceed the minimum quality of its upstream sources.

        Parameters:
            entity_id: Entity identifier
            module_quality: {module_id: quality_score (0.0-1.0)}

        Returns:
            QualityPropagationResult with per-module scores and weakest links
        """
        # Initialise with given scores, default 0.5
        scores: dict[str, float] = {}
        for mod_id in self._signatures:
            scores[mod_id] = module_quality.get(mod_id, 0.5)

        # Topological propagation (BFS from roots)
        sources_set = set(d["source"] for d in self._dependencies)
        targets_set = set(d["target"] for d in self._dependencies)
        roots = sources_set - targets_set

        visited = set()
        queue = list(roots)

        while queue:
            mod = queue.pop(0)
            if mod in visited:
                continue
            visited.add(mod)

            # Propagate to downstream
            for edge in self._adj_forward.get(mod, []):
                tgt = edge["target"]
                # Target quality = min(own quality, upstream quality)
                upstream_q = scores.get(mod, 0.5)
                current_q = scores.get(tgt, 0.5)
                scores[tgt] = min(current_q, upstream_q)
                if tgt not in visited:
                    queue.append(tgt)

        # Identify weakest links
        weakest = []
        for mod_id, score in sorted(scores.items(), key=lambda x: x[1]):
            if score < 0.5:
                weakest.append({
                    "module_id": mod_id,
                    "score": round(score, 2),
                    "reason": f"Quality {score:.0%} — below threshold",
                })

        overall = sum(scores.values()) / len(scores) if scores else 0
        recs = []
        if weakest:
            recs.append(f"{len(weakest)} modules below quality threshold — prioritize data improvement")
        for w in weakest[:3]:
            sig = self._signatures.get(w["module_id"], {})
            recs.append(f"Improve data quality for {sig.get('label', w['module_id'])}")

        return QualityPropagationResult(
            entity_id=entity_id,
            module_quality={k: round(v, 2) for k, v in scores.items()},
            weakest_links=weakest[:10],
            overall_quality=round(overall, 2),
            quality_label=self._quality_label(overall),
            recommendations=recs[:6],
        )

    # ----- Reference Data -----

    def get_all_reference_data(self) -> list[dict]:
        """Get all reference data dependencies across all modules."""
        ref_data = {}
        for mod_id, sig in self._signatures.items():
            for rd in sig.get("reference_data", []):
                if rd not in ref_data:
                    ref_data[rd] = {"dataset": rd, "used_by": [], "category": sig["category"]}
                ref_data[rd]["used_by"].append(mod_id)
        return sorted(ref_data.values(), key=lambda x: len(x["used_by"]), reverse=True)

    def get_module_signatures(self) -> dict[str, dict]:
        """Get all module I/O signatures."""
        return self._signatures

    def get_dependencies(self) -> list[dict]:
        """Get all module dependency edges."""
        return self._dependencies

    # ----- Helpers -----

    @staticmethod
    def _quality_label(score: float) -> str:
        if score >= 0.70:
            return "high"
        elif score >= 0.40:
            return "medium"
        return "low"


# ---------------------------------------------------------------------------
# Climate Risk Engine Module Signatures
# Appended 2026-03-08 — registers new engines in the lineage graph
# ---------------------------------------------------------------------------

def _register_climate_risk_modules(service_instance) -> None:
    """
    Register all Climate Risk Engine modules in the DataLineageService
    module signatures registry and add dependency edges.

    Call once at application startup or after service initialisation.
    """
    # ── Module signatures ─────────────────────────────────────────────────
    new_signatures = {
        "climate_physical_risk_engine": {
            "inputs": [
                "entity_id", "sector_nace", "country_iso", "asset_value",
                "latitude", "longitude", "elevation_m", "coastal_proximity_km",
                "scenario", "time_horizon", "enabled_hazards", "damage_function",
                "adaptation_discount", "cascading_multiplier", "cvar_confidence",
            ],
            "outputs": [
                "composite_score", "acute_score", "chronic_score", "cvar",
                "per_hazard_scores",
            ],
            "reference_data": [
                "sector_vulnerability_matrix", "damage_function_coefficients",
                "hazard_intensity_scales",
            ],
            "quality_indicators": ["data_completeness", "spatial_precision"],
        },
        "climate_transition_risk_engine": {
            "inputs": [
                "entity_id", "sector_nace", "country_iso",
                "revenue", "scope1_emissions", "scope2_emissions", "scope3_emissions",
                "scenario", "time_horizon", "include_scope3_carbon",
                "cbam_rate", "writedown_curve", "residual_value_floor", "alignment_pathway",
            ],
            "outputs": [
                "composite_score", "sector_classification_score", "carbon_cost_score",
                "stranded_asset_score", "alignment_score", "scenario_stress_score",
                "policy_legal_score", "technology_score", "market_score", "reputation_score",
            ],
            "reference_data": [
                "nace_cprs_mapping", "ngfs_phase5_scenarios", "iea_nze_pathways",
                "cbam_price_paths", "phase_out_timelines",
            ],
            "quality_indicators": ["emissions_data_quality", "sector_classification_confidence"],
        },
        "nace_cprs_mapper": {
            "inputs": ["sector_nace"],
            "outputs": ["cprs_category", "iam_sector", "ghg_intensity_bucket", "cprs_risk_weight"],
            "reference_data": ["nace_cprs_mapping_table"],
            "quality_indicators": ["nace_coverage_pct"],
        },
        "climate_integrated_risk": {
            "inputs": [
                "physical_score", "transition_score",
                "physical_weight", "transition_weight",
                "interaction_mode", "interaction_alpha",
                "nature_risk_amplifier", "scenario_weighting",
            ],
            "outputs": ["integrated_score", "interaction_term", "nature_amplified_score"],
            "reference_data": ["encore_dependency_scores"],
            "quality_indicators": ["weight_consistency"],
        },
        "climate_risk_aggregator": {
            "inputs": [
                "entity_scores", "entity_weights", "aggregation_method",
                "weight_field", "diversification_benefit", "outlier_treatment",
            ],
            "outputs": [
                "portfolio_score", "fund_scores", "security_scores",
                "contribution_analysis", "diversification_benefit_pct",
            ],
            "reference_data": [],
            "quality_indicators": ["hierarchy_completeness"],
        },
        "assessment_methodology_manager": {
            "inputs": ["name", "description", "config", "target_sectors"],
            "outputs": ["methodology_id", "methodology_version", "validated_config"],
            "reference_data": ["methodology_templates", "weight_validation_rules"],
            "quality_indicators": ["config_validation_score"],
        },
        "assessment_runner": {
            "inputs": [
                "methodology_id", "target_entities", "scope",
                "scenarios", "time_horizons",
            ],
            "outputs": [
                "run_id", "entity_results", "portfolio_aggregate",
                "delta_report", "duration_seconds",
            ],
            "reference_data": [],
            "quality_indicators": ["run_completion_rate", "entity_coverage_pct"],
        },
    }

    for mod_id, sig in new_signatures.items():
        if mod_id not in service_instance._signatures:
            service_instance._signatures[mod_id] = sig

    # ── Dependency edges ─────────────────────────────────────────────────
    new_edges = [
        # Physical risk engine ← reference data
        {"from": "sector_vulnerability_matrix",    "to": "climate_physical_risk_engine", "type": "reference"},
        {"from": "nace_cprs_mapper",               "to": "climate_transition_risk_engine", "type": "data"},
        # Transition risk ← existing services
        {"from": "cbam_calculator",                "to": "climate_transition_risk_engine", "type": "data"},
        {"from": "stranded_asset_calculator",      "to": "climate_transition_risk_engine", "type": "data"},
        {"from": "scenario_analysis_engine",       "to": "climate_transition_risk_engine", "type": "data"},
        # Integration ← physical + transition
        {"from": "climate_physical_risk_engine",   "to": "climate_integrated_risk", "type": "data"},
        {"from": "climate_transition_risk_engine", "to": "climate_integrated_risk", "type": "data"},
        {"from": "nature_risk_calculator",         "to": "climate_integrated_risk", "type": "data"},
        # Aggregator ← integrated scores
        {"from": "climate_integrated_risk",        "to": "climate_risk_aggregator", "type": "data"},
        # ECL ← physical + transition risk
        {"from": "climate_physical_risk_engine",   "to": "ecl_climate_engine", "type": "data"},
        {"from": "climate_transition_risk_engine", "to": "ecl_climate_engine", "type": "data"},
        # Runner ← methodology + engines
        {"from": "assessment_methodology_manager", "to": "assessment_runner", "type": "config"},
        {"from": "climate_integrated_risk",        "to": "assessment_runner", "type": "data"},
        {"from": "climate_risk_aggregator",        "to": "assessment_runner", "type": "data"},
        # Entity 360 ← assessment runner
        {"from": "assessment_runner",              "to": "entity360", "type": "data"},
    ]

    existing_edge_keys = {
        (e.get("from"), e.get("to")) for e in service_instance._dependencies
    }
    for edge in new_edges:
        key = (edge.get("from"), edge.get("to"))
        if key not in existing_edge_keys:
            service_instance._dependencies.append(edge)
            existing_edge_keys.add(key)


def _register_e_series_modules(service_instance) -> None:
    """Register E6–E10 engine-series modules + E8 IORP II in data lineage."""
    new_signatures = {
        "stewardship_engine": {
            "inputs": ["portfolio_id", "entity_id", "engagement_type", "escalation_level", "proxy_vote_config"],
            "outputs": ["engagement_record", "escalation_status", "proxy_votes", "collaborative_initiative_alignment"],
            "reference_data": ["gfanz_engagement_framework", "nzami_stewardship", "ca100_targets", "nzif_v2", "unpri_p2"],
            "quality_indicators": ["engagement_coverage_pct", "escalation_completion_rate"],
        },
        "eiopa_stress_engine": {
            "inputs": ["insurer_id", "total_assets", "asset_allocation", "eligible_own_funds", "solvency_ii_scr", "solvency_ii_mcr", "scenario_ids"],
            "outputs": ["stressed_own_funds", "stressed_scr", "stressed_solvency_ratio", "recovery_capacity", "orsa_checklist_result"],
            "reference_data": ["eiopa_ngfs_scenarios", "orsa_checklist_art45a", "insurer_type_profiles"],
            "quality_indicators": ["scenario_coverage", "orsa_completion_rate"],
        },
        "iorp_pension_engine": {
            "inputs": ["fund_id", "iorp_type", "total_assets", "liabilities", "liability_duration", "asset_allocation", "sfdr_classification", "scenario_ids"],
            "outputs": ["pre_stress_funding_ratio", "post_stress_funding_ratio", "asset_loss", "liability_change", "ora_checklist", "recovery_plan_trigger", "sfdr_fmp_summary"],
            "reference_data": ["iorp_ii_ora_checklist", "eiopa_iorp_stress_scenarios_2022", "sfdr_fmp_categories", "iorp_type_profiles"],
            "quality_indicators": ["ora_completion_rate", "scenario_coverage", "funding_ratio_accuracy"],
        },
        "sfdr_annex_engine": {
            "inputs": ["fund_id", "fund_type", "pai_indicators", "taxonomy_alignment_pct", "sfdr_classification", "reporting_period"],
            "outputs": ["annex_i_disclosure", "annex_ii_disclosure", "annex_iii_disclosure", "annex_iv_disclosure", "annex_v_disclosure", "completeness_score", "compliance_status"],
            "reference_data": ["sfdr_rts_2022_1288", "pai_indicator_registry", "annex_mandatory_fields"],
            "quality_indicators": ["mandatory_field_completeness_pct", "pai_coverage_pct"],
        },
        "assurance_readiness_engine": {
            "inputs": ["entity_id", "reporting_framework", "assurance_standard_target", "csrd_wave", "module_flags", "criterion_overrides"],
            "outputs": ["readiness_score_pct", "readiness_tier", "blocking_gaps", "domain_scores", "remediation_weeks", "priority_actions"],
            "reference_data": ["isae3000", "isae3410", "issa5000", "csrd_art26a", "readiness_criteria_registry"],
            "quality_indicators": ["criterion_coverage_pct", "blocking_gap_resolution_rate"],
        },
    }

    for mod_id, sig in new_signatures.items():
        if mod_id not in service_instance._signatures:
            service_instance._signatures[mod_id] = sig

    new_edges = [
        # E6 Stewardship ← portfolio analytics, entity 360
        {"from": "portfolio_analytics",          "to": "stewardship_engine", "type": "data"},
        {"from": "entity360",                    "to": "stewardship_engine", "type": "data"},
        # E7 EIOPA ← insurance risk, factor overlay
        {"from": "insurance_risk_engine",        "to": "eiopa_stress_engine", "type": "data"},
        {"from": "factor_overlay_engine",        "to": "eiopa_stress_engine", "type": "data"},
        # E8 IORP ← sovereign climate, portfolio analytics, sfdr_pai
        {"from": "sovereign_climate_risk_engine","to": "iorp_pension_engine", "type": "data"},
        {"from": "portfolio_analytics",          "to": "iorp_pension_engine", "type": "data"},
        {"from": "sfdr_pai_engine",              "to": "iorp_pension_engine", "type": "data"},
        # E8 IORP → assurance readiness, entity 360
        {"from": "iorp_pension_engine",          "to": "assurance_readiness_engine", "type": "data"},
        {"from": "iorp_pension_engine",          "to": "entity360", "type": "data"},
        # E9 SFDR Annex ← sfdr_pai, double_materiality
        {"from": "sfdr_pai_engine",              "to": "sfdr_annex_engine", "type": "data"},
        {"from": "double_materiality_engine",    "to": "sfdr_annex_engine", "type": "data"},
        # E9 SFDR Annex → assurance readiness
        {"from": "sfdr_annex_engine",            "to": "assurance_readiness_engine", "type": "data"},
        # E10 Assurance ← CSRD, ESRS, GHG
        {"from": "csrd_engine",                  "to": "assurance_readiness_engine", "type": "data"},
        {"from": "carbon_calculator",            "to": "assurance_readiness_engine", "type": "data"},
        # E10 Assurance → regulatory report compiler
        {"from": "assurance_readiness_engine",   "to": "regulatory_report_compiler", "type": "data"},
    ]

    existing_edge_keys = {(e.get("from"), e.get("to")) for e in service_instance._dependencies}
    for edge in new_edges:
        key = (edge.get("from"), edge.get("to"))
        if key not in existing_edge_keys:
            service_instance._dependencies.append(edge)
            existing_edge_keys.add(key)


def _register_e11_modules(service_instance) -> None:
    """Register E11 UK SDR engine in the data lineage graph."""
    new_signatures = {
        "uk_sdr_engine": {
            "inputs": [
                "product_id", "product_type", "qualifying_sustainable_pct",
                "has_improvement_targets", "has_measurable_impact_kpis",
                "impact_additionality", "uses_sustainability_terms_in_name",
                "sustainability_evidence_quality", "methodology_published",
                "third_party_verified", "data_coverage_pct",
                "claims_reviewed_by_legal", "claims_updated_on_change",
                "pre_contractual_disclosure_produced", "ongoing_disclosure_produced",
                "entity_disclosure_produced", "sfdr_classification",
                "eu_taxonomy_alignment_pct",
            ],
            "outputs": [
                "recommended_label", "label_eligibility", "agr_compliant",
                "agr_blocking_gaps", "agr_results", "naming_assessment",
                "icis_score", "icis_tier", "sfdr_comparison",
                "disclosure_obligations", "priority_actions",
            ],
            "reference_data": [
                "fca_ps_23_16_labels", "agr_requirements_checklist",
                "sdr_naming_rules", "sdr_cross_framework_map",
                "fca_cobs_4_15",
            ],
            "quality_indicators": [
                "label_eligibility_pct", "agr_compliance_rate", "icis_score",
            ],
        },
    }

    existing_mod_keys = set(service_instance._module_signatures.keys())
    for mod_id, sig in new_signatures.items():
        if mod_id not in existing_mod_keys:
            service_instance._module_signatures[mod_id] = sig

    new_edges = [
        {"from": "sfdr_pai_engine",         "to": "uk_sdr_engine",              "type": "cross_framework_input"},
        {"from": "double_materiality",       "to": "uk_sdr_engine",              "type": "materiality_context"},
        {"from": "assurance_readiness_engine","to": "uk_sdr_engine",             "type": "evidence_quality_input"},
        {"from": "uk_sdr_engine",            "to": "regulatory_report_compiler", "type": "label_disclosure_output"},
        {"from": "uk_sdr_engine",            "to": "entity360",                  "type": "sdr_label_enrichment"},
    ]

    existing_edge_keys = {(e.get("from"), e.get("to")) for e in service_instance._dependencies}
    for edge in new_edges:
        key = (edge.get("from"), edge.get("to"))
        if key not in existing_edge_keys:
            service_instance._dependencies.append(edge)
            existing_edge_keys.add(key)


def _register_e12_e15_modules(service_instance) -> None:
    """Register E12-E15 engines in the data lineage graph."""
    new_signatures = {
        "mifid_spt_engine": {
            "inputs": ["client_id", "preference_category_a_min_pct", "preference_category_b_min_pct",
                       "preference_category_c", "investor_type", "risk_profile",
                       "product_id", "taxonomy_alignment_pct", "sfdr_sustainable_investment_pct",
                       "considers_pais", "sfdr_article"],
            "outputs": ["matched_products", "match_rate_pct", "match_score", "overall_match",
                        "adjustment_recommended", "suitability_report_text", "gap_notes"],
            "reference_data": ["ec_delegated_reg_2021_1253", "mifid_art_2_7_categories",
                               "esma_suitability_guidelines", "mifid_product_esg_types"],
            "quality_indicators": ["match_rate_pct", "preference_coverage_pct"],
        },
        "tcfd_metrics_engine": {
            "inputs": ["entity_id", "entity_name", "sector", "disclosure_year",
                       "g1_disclosed", "g2_disclosed", "s1_disclosed", "s2_disclosed", "s3_disclosed",
                       "rm1_disclosed", "rm2_disclosed", "rm3_disclosed",
                       "mt1_disclosed", "mt2_disclosed", "mt3_disclosed",
                       "disclosure_quality_per_rec", "elements_covered_per_rec"],
            "outputs": ["overall_score", "maturity_level", "maturity_name", "pillar_results",
                        "recommendation_assessments", "blocking_gaps", "priority_actions",
                        "sector_supplement"],
            "reference_data": ["tcfd_final_recommendations_2017", "tcfd_2021_annex",
                               "tcfd_sector_supplements_fi_energy_transport_buildings_agri"],
            "quality_indicators": ["overall_score", "maturity_level", "blocking_gap_count"],
        },
        "eu_gbs_engine": {
            "inputs": ["bond_id", "issuer_name", "bond_type", "principal_amount", "currency",
                       "taxonomy_alignment_pct", "dnsh_confirmed", "min_safeguards_confirmed",
                       "environmental_objectives", "has_external_reviewer", "er_name",
                       "has_pre_issuance_review", "refinancing_share_pct", "is_sovereign",
                       "total_allocated_pct", "impact_indicators"],
            "outputs": ["overall_compliant", "compliance_score", "blocking_gaps", "warnings",
                        "gbfs_completeness_pct", "taxonomy_alignment_pct", "dnsh_status",
                        "er_status", "standards_comparison", "priority_actions",
                        "gbfs_sections", "allocation_report", "impact_report"],
            "reference_data": ["eu_regulation_2023_2631", "eu_taxonomy_delegated_acts",
                               "esma_er_register", "icma_gbp", "climate_bonds_standard"],
            "quality_indicators": ["compliance_score", "gbfs_completeness_pct", "taxonomy_alignment_pct"],
        },
        "priips_kid_engine": {
            "inputs": ["product_id", "product_name", "product_type", "isin", "manufacturer",
                       "rhp_years", "annual_volatility", "credit_quality", "sfdr_classification",
                       "considers_pais", "taxonomy_alignment_pct", "entry_cost_pct",
                       "exit_cost_pct", "ongoing_cost_pct", "performance_fee_pct",
                       "expected_annual_return_pct"],
            "outputs": ["sri_score", "sri_description", "performance_scenarios", "cost_summary",
                        "riy_pct", "esg_inserts", "kid_completeness_pct", "validation_gaps",
                        "warnings"],
            "reference_data": ["eu_regulation_1286_2014", "eu_2021_2268_revised_kid",
                               "sfdr_2019_2088_art8_art9", "priips_sri_methodology"],
            "quality_indicators": ["kid_completeness_pct", "sri_score", "esg_insert_count"],
        },
    }

    existing_mod_keys = set(service_instance._module_signatures.keys())
    for mod_id, sig in new_signatures.items():
        if mod_id not in existing_mod_keys:
            service_instance._module_signatures[mod_id] = sig

    new_edges = [
        # E12 MiFID II SPT
        {"from": "sfdr_pai_engine",          "to": "mifid_spt_engine",   "type": "pai_consideration_input"},
        {"from": "eu_taxonomy_engine",        "to": "mifid_spt_engine",   "type": "taxonomy_alignment_input"},
        {"from": "mifid_spt_engine",          "to": "regulatory_report_compiler", "type": "suitability_report_output"},
        {"from": "mifid_spt_engine",          "to": "entity360",          "type": "preference_enrichment"},
        # E13 TCFD
        {"from": "climate_physical_risk",     "to": "tcfd_metrics_engine","type": "physical_risk_metrics_input"},
        {"from": "climate_transition_risk",   "to": "tcfd_metrics_engine","type": "transition_risk_metrics_input"},
        {"from": "double_materiality",         "to": "tcfd_metrics_engine","type": "materiality_scope_input"},
        {"from": "tcfd_metrics_engine",        "to": "regulatory_report_compiler", "type": "tcfd_report_output"},
        {"from": "tcfd_metrics_engine",        "to": "sec_climate_engine", "type": "tcfd_baseline_for_sec"},
        {"from": "tcfd_metrics_engine",        "to": "entity360",          "type": "tcfd_maturity_enrichment"},
        # E14 EU GBS
        {"from": "eu_taxonomy_engine",         "to": "eu_gbs_engine",      "type": "taxonomy_alignment_verification"},
        {"from": "double_materiality",          "to": "eu_gbs_engine",      "type": "dnsh_materiality_context"},
        {"from": "eu_gbs_engine",               "to": "regulatory_report_compiler", "type": "gbfs_output"},
        {"from": "eu_gbs_engine",               "to": "entity360",          "type": "gbs_label_enrichment"},
        # E15 PRIIPs KID
        {"from": "sfdr_pai_engine",             "to": "priips_kid_engine",  "type": "pai_disclosure_insert"},
        {"from": "mifid_spt_engine",            "to": "priips_kid_engine",  "type": "product_esg_classification"},
        {"from": "priips_kid_engine",           "to": "regulatory_report_compiler", "type": "kid_output"},
        {"from": "priips_kid_engine",           "to": "entity360",          "type": "kid_enrichment"},
    ]

    existing_edge_keys = {(e.get("from"), e.get("to")) for e in service_instance._dependencies}
    for edge in new_edges:
        key = (edge.get("from"), edge.get("to"))
        if key not in existing_edge_keys:
            service_instance._dependencies.append(edge)
            existing_edge_keys.add(key)


def _register_e16_e19_modules(service_instance) -> None:
    """Register E16-E19 engines in the data lineage graph."""
    new_signatures = {
        "esma_fund_names_engine": {
            "inputs": ["fund_id", "fund_name", "proposed_name", "fund_type",
                       "esg_investment_pct", "sustainability_investment_pct",
                       "transition_investment_pct", "exclusions_applied",
                       "pab_exclusions_met", "benchmark_type", "nace_exclusions"],
            "outputs": ["name_compliant", "compliance_score", "term_detected",
                        "threshold_required", "threshold_met", "exclusion_gaps",
                        "benchmark_requirement", "remediation_steps", "effective_date",
                        "phase_in_deadline"],
            "reference_data": ["esma_guidelines_2024_249", "esma_fund_name_terms_list",
                                "pab_exclusion_criteria", "eu_climate_benchmarks_reg_2019_2089"],
            "quality_indicators": ["compliance_score", "threshold_met", "exclusion_gaps_count"],
        },
        "sl_finance_engine": {
            "inputs": ["instrument_id", "instrument_type", "issuer_name", "notional",
                       "currency", "tenor_years", "kpi_id", "kpi_name", "kpi_unit",
                       "kpi_baseline", "kpi_target", "target_observation_date",
                       "spt_calibration_method", "step_up_bps", "external_review"],
            "outputs": ["kpi_smart_score", "spt_score", "overall_score", "compliant",
                        "coupon_adjustment_triggered", "step_up_amount_bps",
                        "verification_status", "gaps", "warnings",
                        "icma_alignment", "lma_alignment"],
            "reference_data": ["icma_slb_principles_2023", "lma_sll_principles_2023",
                                "lsta_sll_principles", "icma_kpi_registry"],
            "quality_indicators": ["kpi_smart_score", "spt_score", "overall_score"],
        },
        "ifrs_s1_engine": {
            "inputs": ["entity_id", "entity_name", "industry", "sasb_sector",
                       "reporting_period", "governance_disclosed", "strategy_disclosed",
                       "risk_mgmt_disclosed", "metrics_disclosed",
                       "significant_risks_count", "opportunities_count",
                       "transition_plan_exists", "scenario_analysis_conducted",
                       "scope1_ghg", "scope2_ghg", "scope3_ghg"],
            "outputs": ["overall_score", "compliance_level", "pillar_scores",
                        "disclosure_gaps", "priority_actions", "sasb_industry_metrics",
                        "cross_framework_links", "assurance_readiness"],
            "reference_data": ["ifrs_s1_june_2023", "ifrs_s2_june_2023",
                                "sasb_industry_standards", "tcfd_recommendations_2017"],
            "quality_indicators": ["overall_score", "compliance_level", "disclosure_gap_count"],
        },
        "eu_taxonomy_gar_engine": {
            "inputs": ["entity_id", "entity_name", "reporting_period",
                       "total_assets", "eligible_assets", "aligned_assets",
                       "loan_book_eligible_pct", "loan_book_aligned_pct",
                       "equity_investments_eligible_pct", "equity_investments_aligned_pct",
                       "debt_securities_eligible_pct", "debt_securities_aligned_pct",
                       "dnsh_confirmed", "min_safeguards_confirmed",
                       "environmental_objective_breakdown"],
            "outputs": ["gar", "btar", "bsar", "eligibility_ratio",
                        "alignment_ratio_by_objective", "dnsh_status",
                        "min_safeguards_status", "disclosure_completeness_pct",
                        "gaps", "warnings", "peer_benchmark"],
            "reference_data": ["eu_taxonomy_reg_2020_852", "delegated_act_2021_2139",
                                "delegated_act_2021_4987_art8", "eu_taxonomy_climate_criteria"],
            "quality_indicators": ["gar", "btar", "eligibility_ratio", "disclosure_completeness_pct"],
        },
    }

    existing_mod_keys = set(service_instance._module_signatures.keys())
    for mod_id, sig in new_signatures.items():
        if mod_id not in existing_mod_keys:
            service_instance._module_signatures[mod_id] = sig

    new_edges = [
        # E16 ESMA Fund Names
        {"from": "sfdr_pai_engine",         "to": "esma_fund_names_engine", "type": "pai_exclusion_input"},
        {"from": "eu_taxonomy_engine",       "to": "esma_fund_names_engine", "type": "taxonomy_threshold_input"},
        {"from": "esma_fund_names_engine",   "to": "regulatory_report_compiler", "type": "fund_name_compliance_output"},
        {"from": "esma_fund_names_engine",   "to": "entity360",              "type": "fund_name_label_enrichment"},
        # E17 SL Finance
        {"from": "carbon_calculator",        "to": "sl_finance_engine",     "type": "ghg_kpi_baseline_input"},
        {"from": "eu_taxonomy_engine",       "to": "sl_finance_engine",     "type": "taxonomy_kpi_alignment"},
        {"from": "sl_finance_engine",        "to": "regulatory_report_compiler", "type": "slb_sll_disclosure_output"},
        {"from": "sl_finance_engine",        "to": "entity360",             "type": "sustainability_linked_label"},
        # E18 IFRS S1
        {"from": "tcfd_metrics_engine",      "to": "ifrs_s1_engine",        "type": "tcfd_pillar_mapping"},
        {"from": "double_materiality",        "to": "ifrs_s1_engine",        "type": "materiality_input"},
        {"from": "ifrs_s1_engine",           "to": "regulatory_report_compiler", "type": "ifrs_s1_disclosure_output"},
        {"from": "ifrs_s1_engine",           "to": "sec_climate_engine",    "type": "ifrs_sec_cross_framework"},
        {"from": "ifrs_s1_engine",           "to": "entity360",             "type": "ifrs_s1_enrichment"},
        # E19 EU Taxonomy GAR
        {"from": "eu_taxonomy_engine",        "to": "eu_taxonomy_gar_engine", "type": "activity_alignment_input"},
        {"from": "portfolio_analytics",       "to": "eu_taxonomy_gar_engine", "type": "asset_class_exposure_input"},
        {"from": "eu_taxonomy_gar_engine",    "to": "regulatory_report_compiler", "type": "gar_btar_output"},
        {"from": "eu_taxonomy_gar_engine",    "to": "entity360",             "type": "gar_ratio_enrichment"},
    ]

    existing_edge_keys = {(e.get("from"), e.get("to")) for e in service_instance._dependencies}
    for edge in new_edges:
        key = (edge.get("from"), edge.get("to"))
        if key not in existing_edge_keys:
            service_instance._dependencies.append(edge)
            existing_edge_keys.add(key)


def _register_e20_e23_modules(service_instance) -> None:
    """Register E20-E23 engines in the data lineage graph."""
    new_signatures = {
        "eba_pillar3_engine": {
            "inputs": ["entity_id", "total_assets_bn", "institution_type",
                       "templates_completed", "nace_exposures", "taxonomy_aligned_pct",
                       "financed_emissions_intensity", "loan_book"],
            "outputs": ["compliance_score", "missing_mandatory", "template_scores",
                        "next_disclosure_date", "physical_risk_heatmap",
                        "financed_emissions_by_sector", "carbon_related_assets_pct"],
            "reference_data": ["eba_gl_2022_03", "crr_art_449a", "eba_its_2022_01",
                                "eba_nace_climate_classification"],
            "quality_indicators": ["compliance_score", "templates_completed_count"],
        },
        "scope3_categories_engine": {
            "inputs": ["entity_id", "nace_code", "revenue_bn", "headcount",
                       "category_inputs", "investment_portfolio"],
            "outputs": ["material_categories", "flag_applicable", "total_scope3_tco2e",
                        "sbti_coverage_pct", "category_results", "portfolio_scope3",
                        "flag_split", "dqs_scores"],
            "reference_data": ["ghg_protocol_scope3_standard_2011",
                                "sbti_flag_guidance_2023", "pcaf_c15_method"],
            "quality_indicators": ["sbti_coverage_pct", "avg_dqs_score", "total_scope3_tco2e"],
        },
        "sfdr_product_reporting_engine": {
            "inputs": ["product_id", "sfdr_article", "reporting_period",
                       "sustainable_investment_pct", "taxonomy_alignment",
                       "holding_pais", "benchmark_index"],
            "outputs": ["report_completeness_pct", "section_gaps", "pai_coverage_pct",
                        "verified_sustainable_investment_pct", "taxonomy_by_objective",
                        "website_disclosure_complete", "warnings"],
            "reference_data": ["rts_2022_1288_annex_iii", "rts_2022_1288_annex_v",
                                "sfdr_2019_2088", "eu_taxonomy_reg_2020_852"],
            "quality_indicators": ["report_completeness_pct", "pai_coverage_pct"],
        },
        "biodiversity_finance_engine": {
            "inputs": ["entity_id", "sector", "tnfd_disclosure_data",
                       "land_use_data", "nature_targets", "financial_data",
                       "portfolio_holdings"],
            "outputs": ["tnfd_overall_maturity", "tnfd_pillar_scores", "tnfd_gaps",
                        "msa_footprint_km2", "sbtn_readiness_score", "sbtn_steps_complete",
                        "cbd_gbf_alignment", "cbd_gbf_sub_element_scores",
                        "priority_actions", "cross_framework"],
            "reference_data": ["tnfd_v1_0_recommendations", "sbtn_guidance_2023",
                                "cbd_gbf_target_15", "pbaf_2023_standard",
                                "encore_ecosystem_services"],
            "quality_indicators": ["tnfd_overall_maturity", "msa_footprint_km2",
                                   "sbtn_steps_complete"],
        },
    }

    existing_mod_keys = set(service_instance._module_signatures.keys())
    for mod_id, sig in new_signatures.items():
        if mod_id not in existing_mod_keys:
            service_instance._module_signatures[mod_id] = sig

    new_edges = [
        # E20 EBA Pillar 3
        {"from": "climate_physical_risk",     "to": "eba_pillar3_engine",          "type": "physical_risk_heatmap_input"},
        {"from": "climate_transition_risk",   "to": "eba_pillar3_engine",          "type": "transition_risk_template_input"},
        {"from": "eu_taxonomy_gar_engine",    "to": "eba_pillar3_engine",          "type": "gar_btar_for_template_t10"},
        {"from": "eba_pillar3_engine",        "to": "regulatory_report_compiler",  "type": "pillar3_esg_disclosure_output"},
        {"from": "eba_pillar3_engine",        "to": "entity360",                   "type": "pillar3_compliance_enrichment"},
        # E21 Scope 3 Categories
        {"from": "carbon_calculator",         "to": "scope3_categories_engine",    "type": "scope1_2_baseline_for_scope3"},
        {"from": "supply_chain",              "to": "scope3_categories_engine",    "type": "upstream_activity_data"},
        {"from": "scope3_categories_engine",  "to": "regulatory_report_compiler",  "type": "scope3_disclosure_output"},
        {"from": "scope3_categories_engine",  "to": "sfdr_pai_engine",             "type": "scope3_pai_indicator_feed"},
        {"from": "scope3_categories_engine",  "to": "entity360",                   "type": "scope3_enrichment"},
        # E22 SFDR Product Reporting
        {"from": "sfdr_pai_engine",           "to": "sfdr_product_reporting_engine","type": "entity_pai_to_product_pai"},
        {"from": "eu_taxonomy_engine",        "to": "sfdr_product_reporting_engine","type": "taxonomy_product_disclosure"},
        {"from": "sfdr_product_reporting_engine","to": "regulatory_report_compiler","type": "sfdr_periodic_report_output"},
        {"from": "sfdr_product_reporting_engine","to": "entity360",                "type": "product_disclosure_enrichment"},
        # E23 Biodiversity Finance
        {"from": "nature_risk",               "to": "biodiversity_finance_engine", "type": "nature_risk_materiality_input"},
        {"from": "tnfd_assessment_engine",    "to": "biodiversity_finance_engine", "type": "tnfd_disclosure_baseline"},
        {"from": "biodiversity_finance_engine","to": "regulatory_report_compiler", "type": "biodiversity_disclosure_output"},
        {"from": "biodiversity_finance_engine","to": "entity360",                  "type": "biodiversity_enrichment"},
    ]

    existing_edge_keys = {(e.get("from"), e.get("to")) for e in service_instance._dependencies}
    for edge in new_edges:
        key = (edge.get("from"), edge.get("to"))
        if key not in existing_edge_keys:
            service_instance._dependencies.append(edge)
            existing_edge_keys.add(key)


def _register_e24_e27_modules(service_instance) -> None:
    """Register E24-E27 engines in the data lineage graph."""
    new_signatures = {
        "issb_s2_engine": {
            "inputs": ["entity_id", "industry_sector", "reporting_period",
                       "scope1_tco2e", "scope2_tco2e", "scope3_tco2e",
                       "financed_emissions", "physical_risk_inputs",
                       "transition_risk_inputs", "scenario_data",
                       "internal_carbon_price", "climate_capex"],
            "outputs": ["governance_score", "strategy_score", "risk_mgmt_score",
                        "metrics_targets_score", "overall_compliance_pct",
                        "scenario_analysis", "physical_risks", "transition_risks",
                        "climate_opportunities", "cross_industry_metrics",
                        "industry_metrics", "tcfd_cross_reference", "disclosure_gaps"],
            "reference_data": ["ifrs_s2_june_2023", "sasb_industry_standards",
                                "tcfd_2017_recommendations", "ngfs_scenarios"],
            "quality_indicators": ["overall_compliance_pct", "disclosure_gaps_count"],
        },
        "gri_standards_engine": {
            "inputs": ["entity_id", "reporting_period", "material_topics",
                       "gri_2_disclosures", "gri_301_materials", "gri_302_energy",
                       "gri_303_water", "gri_304_biodiversity", "gri_305_emissions",
                       "gri_306_waste", "gri_308_supplier_env"],
            "outputs": ["gri_1_compliance_pct", "gri_2_compliance_pct",
                        "gri_3_compliance_pct", "overall_compliance_pct",
                        "content_index", "gri_300_scores", "disclosure_gaps",
                        "assurance_level", "gri_service_level"],
            "reference_data": ["gri_1_foundation_2021", "gri_2_general_disclosures_2021",
                                "gri_3_material_topics_2021", "gri_300_environment_series"],
            "quality_indicators": ["overall_compliance_pct", "gri_service_level"],
        },
        "tpt_transition_plan_engine": {
            "inputs": ["entity_id", "entity_type", "plan_year",
                       "net_zero_target_year", "interim_targets",
                       "financed_emissions_trajectory", "capex_green_pct",
                       "engagement_policy", "governance_oversight",
                       "transition_finance_products"],
            "outputs": ["foundations_score", "implementation_score", "engagement_score",
                        "metrics_targets_score", "governance_score", "finance_score",
                        "overall_quality_score", "quality_tier",
                        "key_actions", "gap_analysis", "cross_framework"],
            "reference_data": ["tpt_disclosure_framework_2023", "fca_ps23_22",
                                "gfanz_transition_finance_guidance"],
            "quality_indicators": ["overall_quality_score", "quality_tier"],
        },
        "pcaf_sovereign_engine": {
            "inputs": ["entity_id", "country_code", "outstanding_amount_mn",
                       "government_debt_bn", "gdp_bn",
                       "sovereign_ghg_inventory", "ndc_target",
                       "lulucf_adjustment", "national_circumstances"],
            "outputs": ["attribution_factor", "financed_emissions_tco2e",
                        "emissions_intensity", "pcaf_dqs", "ndc_alignment",
                        "climate_risk_score", "portfolio_context"],
            "reference_data": ["pcaf_standard_part_d_2023", "unfccc_ghg_inventories",
                                "world_bank_gdp_data", "imf_government_debt_data",
                                "nd_gain_country_index"],
            "quality_indicators": ["pcaf_dqs", "emissions_intensity", "ndc_alignment"],
        },
    }

    existing_mod_keys = set(service_instance._module_signatures.keys())
    for mod_id, sig in new_signatures.items():
        if mod_id not in existing_mod_keys:
            service_instance._module_signatures[mod_id] = sig

    new_edges = [
        # E24 ISSB S2
        {"from": "climate_physical_risk",      "to": "issb_s2_engine",            "type": "physical_risk_scenario_input"},
        {"from": "climate_transition_risk",    "to": "issb_s2_engine",            "type": "transition_risk_scenario_input"},
        {"from": "carbon_calculator",          "to": "issb_s2_engine",            "type": "scope1_2_3_emissions_input"},
        {"from": "issb_s2_engine",             "to": "regulatory_report_compiler","type": "s2_disclosure_output"},
        {"from": "issb_s2_engine",             "to": "entity360",                 "type": "s2_enrichment"},
        # E25 GRI Standards
        {"from": "double_materiality_engine",  "to": "gri_standards_engine",      "type": "material_topics_input"},
        {"from": "carbon_calculator",          "to": "gri_standards_engine",      "type": "gri_305_emissions_input"},
        {"from": "nature_risk",                "to": "gri_standards_engine",      "type": "gri_304_biodiversity_input"},
        {"from": "gri_standards_engine",       "to": "regulatory_report_compiler","type": "gri_content_index_output"},
        {"from": "gri_standards_engine",       "to": "entity360",                 "type": "gri_enrichment"},
        # E26 TPT Transition Plan
        {"from": "issb_s2_engine",             "to": "tpt_transition_plan_engine","type": "s2_climate_targets_input"},
        {"from": "portfolio_analytics",        "to": "tpt_transition_plan_engine","type": "financed_emissions_trajectory"},
        {"from": "tpt_transition_plan_engine", "to": "regulatory_report_compiler","type": "tpt_plan_output"},
        {"from": "tpt_transition_plan_engine", "to": "entity360",                 "type": "tpt_enrichment"},
        # E27 PCAF Sovereign
        {"from": "sovereign_climate_risk_engine","to": "pcaf_sovereign_engine",   "type": "sovereign_climate_risk_score"},
        {"from": "portfolio_analytics",        "to": "pcaf_sovereign_engine",     "type": "sovereign_bond_holdings"},
        {"from": "pcaf_sovereign_engine",      "to": "regulatory_report_compiler","type": "sovereign_emissions_output"},
        {"from": "pcaf_sovereign_engine",      "to": "entity360",                 "type": "sovereign_enrichment"},
    ]

    existing_edge_keys = {(e.get("from"), e.get("to")) for e in service_instance._dependencies}
    for edge in new_edges:
        key = (edge.get("from"), edge.get("to"))
        if key not in existing_edge_keys:
            service_instance._dependencies.append(edge)
            existing_edge_keys.add(key)


def _register_e28_e31_modules(service_instance) -> None:
    """Register E28-E31 engines in the data lineage graph."""
    new_signatures = {
        "esrs_e2_e5_engine": {
            "inputs": ["entity_id", "reporting_period", "e2_pollution_data",
                       "e3_water_data", "e4_biodiversity_data", "e5_circular_data",
                       "materiality_assessment", "nace_sector"],
            "outputs": ["e2_compliance_pct", "e2_air_pollutants", "e2_water_pollutants",
                        "e3_water_withdrawal_m3", "e3_water_stress_pct",
                        "e4_sensitive_areas_pct", "e4_land_use_change_ha",
                        "e5_recycled_content_pct", "e5_circularity_rate_pct",
                        "overall_compliance_pct", "disclosure_gaps"],
            "reference_data": ["csrd_2022_2464", "esrs_e2_pollution_2023",
                                "esrs_e3_water_2023", "esrs_e4_biodiversity_2023",
                                "esrs_e5_circular_2023"],
            "quality_indicators": ["overall_compliance_pct", "material_topics_count"],
        },
        "greenwashing_engine": {
            "inputs": ["entity_id", "claims", "product_labels",
                       "sfdr_classification", "taxonomy_alignment_claimed",
                       "marketing_materials", "regulatory_filings"],
            "outputs": ["overall_risk_score", "risk_tier", "claims_flagged",
                        "misleading_terms_found", "substantiation_gaps",
                        "label_verification", "remediation_steps",
                        "eu_reg_score", "fca_score"],
            "reference_data": ["eu_reg_2023_2441_anti_greenwashing",
                                "fca_consumer_duty_2023", "esma_guidelines_supervisory",
                                "uk_sdr_anti_greenwashing_rule"],
            "quality_indicators": ["overall_risk_score", "claims_flagged_pct"],
        },
        "carbon_credit_quality_engine": {
            "inputs": ["project_id", "standard", "methodology", "project_type",
                       "vintage_year", "volume_tco2e", "additionality_docs",
                       "permanence_buffer", "co_benefits_data"],
            "outputs": ["ccp_label", "additionality_score", "permanence_risk_score",
                        "co_benefits_score", "overall_quality_score", "quality_tier",
                        "corsia_eligible", "article6_eligible", "price_range_usd"],
            "reference_data": ["icvcm_ccp_core_carbon_principles_2023",
                                "verra_vcs_standard", "gold_standard_v4",
                                "corsia_eligible_programmes", "paris_art6_rules"],
            "quality_indicators": ["overall_quality_score", "quality_tier", "ccp_label"],
        },
        "climate_stress_test_engine": {
            "inputs": ["entity_id", "loan_book_data", "nace_exposures",
                       "baseline_cet1_pct", "framework", "scenarios",
                       "time_horizon", "carbon_price_path"],
            "outputs": ["stressed_cet1_pct", "cet1_depletion_bps",
                        "total_credit_losses_bn", "pd_migration_by_sector",
                        "lgd_uplift_by_sector", "stranded_asset_pct",
                        "worst_scenario", "climate_var_pct", "summary_results"],
            "reference_data": ["ecb_climate_stress_test_2022",
                                "eba_climate_stress_test_2023",
                                "ngfs_scenarios_phase4", "boe_climate_scenario_2021"],
            "quality_indicators": ["cet1_depletion_bps", "total_credit_losses_bn"],
        },
    }

    existing_mod_keys = set(service_instance._module_signatures.keys())
    for mod_id, sig in new_signatures.items():
        if mod_id not in existing_mod_keys:
            service_instance._module_signatures[mod_id] = sig

    new_edges = [
        # E28 ESRS E2-E5
        {"from": "double_materiality_engine",  "to": "esrs_e2_e5_engine",         "type": "e2_e5_materiality_input"},
        {"from": "nature_risk",                "to": "esrs_e2_e5_engine",         "type": "e4_biodiversity_data"},
        {"from": "carbon_calculator",          "to": "esrs_e2_e5_engine",         "type": "e2_pollution_scope_data"},
        {"from": "esrs_e2_e5_engine",          "to": "regulatory_report_compiler","type": "esrs_e2_e5_disclosure_output"},
        {"from": "esrs_e2_e5_engine",          "to": "entity360",                 "type": "esrs_e2_e5_enrichment"},
        # E29 Greenwashing
        {"from": "sfdr_product_reporting_engine","to": "greenwashing_engine",     "type": "sfdr_label_claim_input"},
        {"from": "eu_taxonomy_gar_engine",     "to": "greenwashing_engine",       "type": "taxonomy_claim_verification"},
        {"from": "greenwashing_engine",        "to": "regulatory_report_compiler","type": "greenwashing_risk_output"},
        {"from": "greenwashing_engine",        "to": "entity360",                 "type": "greenwashing_risk_flag"},
        # E30 Carbon Credit Quality
        {"from": "carbon_calculator",          "to": "carbon_credit_quality_engine","type": "offset_credit_portfolio"},
        {"from": "carbon_credit_quality_engine","to": "regulatory_report_compiler","type": "credit_quality_disclosure"},
        {"from": "carbon_credit_quality_engine","to": "entity360",                "type": "credit_quality_enrichment"},
        # E31 Climate Stress Test
        {"from": "climate_physical_risk",      "to": "climate_stress_test_engine","type": "physical_shock_inputs"},
        {"from": "climate_transition_risk",    "to": "climate_stress_test_engine","type": "transition_shock_inputs"},
        {"from": "ecl_climate_engine",         "to": "climate_stress_test_engine","type": "baseline_ecl_for_stress"},
        {"from": "climate_stress_test_engine", "to": "regulatory_report_compiler","type": "stress_test_results_output"},
        {"from": "climate_stress_test_engine", "to": "portfolio_analytics",       "type": "stressed_portfolio_metrics"},
        {"from": "climate_stress_test_engine", "to": "entity360",                 "type": "stress_test_enrichment"},
    ]

    existing_edge_keys = {(e.get("from"), e.get("to")) for e in service_instance._dependencies}
    for edge in new_edges:
        key = (edge.get("from"), edge.get("to"))
        if key not in existing_edge_keys:
            service_instance._dependencies.append(edge)
            existing_edge_keys.add(key)


def _register_e32_e35_modules(service_instance) -> None:
    """Register E32-E35 engines in the data lineage graph."""
    new_signatures = {
        "tnfd_leap_engine": {
            "inputs": ["entity_id", "sector", "reporting_period",
                       "priority_locations", "value_chain_scope",
                       "dependencies", "impacts", "ecosystem_condition",
                       "material_risks", "material_opportunities"],
            "outputs": ["locate_score", "evaluate_score", "assess_score",
                        "prepare_score", "overall_leap_score", "leap_maturity",
                        "risk_magnitude", "opportunity_magnitude",
                        "strategy_response", "disclosure_completeness_pct",
                        "priority_actions", "cross_framework"],
            "reference_data": ["tnfd_framework_v1_2023", "encore_nature_tool",
                                "iucn_red_list", "wri_aqueduct", "ipbes_assessments"],
            "quality_indicators": ["overall_leap_score", "leap_maturity",
                                   "disclosure_completeness_pct"],
        },
        "net_zero_targets_engine": {
            "inputs": ["entity_id", "entity_type", "framework",
                       "base_year_emissions", "scope1_tco2e", "scope2_tco2e",
                       "scope3_tco2e", "net_zero_target_year",
                       "near_term_target_year", "interim_milestones",
                       "residual_emissions_plan", "beyond_value_chain"],
            "outputs": ["near_term_reduction_pct", "long_term_reduction_pct",
                        "sbti_validation_status", "temperature_score",
                        "pathway_gap_pct", "flag_target",
                        "net_zero_pathway_records", "warnings", "cross_framework"],
            "reference_data": ["sbti_corporate_criteria_v5", "sbti_flag_v1",
                                "nzba_guidelines_2021", "nzami_guidelines_2021",
                                "nzaoa_guidelines_2022", "ipcc_ar6_pathways"],
            "quality_indicators": ["temperature_score", "pathway_gap_pct",
                                   "sbti_validation_status"],
        },
        "esg_data_quality_engine": {
            "inputs": ["entity_id", "reporting_period",
                       "e_indicators", "s_indicators", "g_indicators",
                       "provider_data_bloomberg", "provider_data_msci",
                       "provider_data_sustainalytics", "materiality_map"],
            "outputs": ["overall_quality_score", "overall_coverage_pct",
                        "e_pillar_score", "s_pillar_score", "g_pillar_score",
                        "estimated_indicators_pct", "provider_divergence",
                        "dqs_profile", "material_gaps", "improvement_actions",
                        "bcbs239_score"],
            "reference_data": ["pcaf_dqs_framework", "bcbs_239_data_governance",
                                "esma_esg_provider_regulation_2023",
                                "iosco_esg_ratings_code_2021"],
            "quality_indicators": ["overall_quality_score", "bcbs239_score",
                                   "overall_coverage_pct"],
        },
        "regulatory_penalties_engine": {
            "inputs": ["entity_id", "annual_turnover_mn",
                       "csrd_compliance_pct", "sfdr_compliance_pct",
                       "taxonomy_compliance_pct", "eudr_compliance_pct",
                       "csddd_compliance_pct", "violation_evidence",
                       "supervisory_authority_jurisdiction"],
            "outputs": ["violations_found", "max_penalty_mn", "expected_penalty_mn",
                        "penalty_by_regulation", "whistleblower_risk",
                        "remediation_priority", "enforcement_timeline",
                        "supervisory_authority"],
            "reference_data": ["csrd_art19a_penalties", "sfdr_art14_penalties",
                                "eu_taxonomy_art22_penalties",
                                "eudr_art24_25_penalties", "csddd_art29_30_33",
                                "esma_convergence_supervisory_2023"],
            "quality_indicators": ["max_penalty_mn", "expected_penalty_mn",
                                   "violations_found"],
        },
    }

    existing_mod_keys = set(service_instance._module_signatures.keys())
    for mod_id, sig in new_signatures.items():
        if mod_id not in existing_mod_keys:
            service_instance._module_signatures[mod_id] = sig

    new_edges = [
        # E32 TNFD LEAP
        {"from": "nature_risk",                "to": "tnfd_leap_engine",           "type": "nature_risk_leap_input"},
        {"from": "eudr_engine",                "to": "tnfd_leap_engine",           "type": "deforestation_location_data"},
        {"from": "double_materiality_engine",  "to": "tnfd_leap_engine",           "type": "nature_materiality_assessment"},
        {"from": "tnfd_leap_engine",           "to": "regulatory_report_compiler", "type": "tnfd_leap_disclosure"},
        {"from": "tnfd_leap_engine",           "to": "entity360",                  "type": "tnfd_leap_enrichment"},
        {"from": "tnfd_leap_engine",           "to": "factor_overlay_engine",      "type": "nature_risk_factor_input"},
        # E33 Net Zero Targets
        {"from": "carbon_calculator",          "to": "net_zero_targets_engine",    "type": "base_year_emissions_input"},
        {"from": "climate_transition_risk",    "to": "net_zero_targets_engine",    "type": "transition_pathway_scenarios"},
        {"from": "net_zero_targets_engine",    "to": "regulatory_report_compiler", "type": "net_zero_targets_disclosure"},
        {"from": "net_zero_targets_engine",    "to": "portfolio_analytics",        "type": "portfolio_temperature_score"},
        {"from": "net_zero_targets_engine",    "to": "entity360",                  "type": "net_zero_targets_enrichment"},
        # E34 ESG Data Quality
        {"from": "data_lineage_service",       "to": "esg_data_quality_engine",    "type": "dqs_quality_propagation"},
        {"from": "esg_data_quality_engine",    "to": "regulatory_report_compiler", "type": "esg_data_quality_disclosure"},
        {"from": "esg_data_quality_engine",    "to": "entity360",                  "type": "data_quality_enrichment"},
        {"from": "esg_data_quality_engine",    "to": "factor_overlay_engine",      "type": "data_quality_confidence_weights"},
        # E35 Regulatory Penalties
        {"from": "csrd_engine",                "to": "regulatory_penalties_engine","type": "csrd_compliance_score"},
        {"from": "eudr_engine",                "to": "regulatory_penalties_engine","type": "eudr_compliance_score"},
        {"from": "csddd_engine",               "to": "regulatory_penalties_engine","type": "csddd_compliance_score"},
        {"from": "regulatory_penalties_engine","to": "regulatory_report_compiler", "type": "penalty_exposure_disclosure"},
        {"from": "regulatory_penalties_engine","to": "entity360",                  "type": "penalty_risk_enrichment"},
    ]

    existing_edge_keys = {(e.get("from"), e.get("to")) for e in service_instance._dependencies}
    for edge in new_edges:
        key = (edge.get("from"), edge.get("to"))
        if key not in existing_edge_keys:
            service_instance._dependencies.append(edge)
            existing_edge_keys.add(key)


def _register_e36_e39_modules(service_instance) -> None:
    """Register E36-E39 engines in the data lineage graph."""
    new_signatures = {
        "basel3_liquidity_engine": {
            "inputs": ["entity_id", "reporting_date", "scenario_id",
                       "hqla_level1_mn", "hqla_level2a_mn", "hqla_level2b_mn",
                       "gross_outflow_mn", "gross_inflow_mn",
                       "asf_mn", "rsf_mn", "time_buckets",
                       "rate_shock_scenarios"],
            "outputs": ["lcr_pct", "nsfr_pct", "survival_horizon_days",
                        "liquidity_at_risk_mn", "eve_sensitivity_pct",
                        "nii_sensitivity_pct", "duration_gap_years",
                        "concentration_risk_score", "regulatory_breaches",
                        "climate_hqla_haircut_bps", "monitoring_metrics"],
            "reference_data": ["bcbs238_monitoring_tools", "bcbs295_nsfr",
                                "crr2_art416_hqla", "eba_stress_2024",
                                "ngfs_climate_scenarios"],
            "quality_indicators": ["lcr_pct", "nsfr_pct", "survival_horizon_days"],
        },
        "social_taxonomy_engine": {
            "inputs": ["entity_id", "entity_name", "assessment_type",
                       "reporting_period", "workforce_indicators",
                       "community_indicators", "supply_chain_indicators",
                       "portfolio_holdings", "sdg_targets"],
            "outputs": ["decent_work_score", "living_standards_score",
                        "inclusive_communities_score", "social_taxonomy_aligned_pct",
                        "sfdr_sustainable_investment_pct", "imp_composite_score",
                        "sdg_alignment", "iris_plus_metrics",
                        "additionality_score", "cross_framework"],
            "reference_data": ["eu_social_taxonomy_2021", "imp_framework",
                                "iris_plus_catalog", "sfdr_art2_17",
                                "sdg_indicator_framework"],
            "quality_indicators": ["imp_composite_score", "social_taxonomy_aligned_pct"],
        },
        "forced_labour_engine": {
            "inputs": ["entity_id", "entity_name", "sector",
                       "supply_chain_nodes", "country_profiles",
                       "audit_reports", "grievance_cases",
                       "compliance_programme_data"],
            "outputs": ["eu_flr_import_risk", "art7_investigation_trigger",
                        "uk_msa_score", "uk_msa_disclosure_areas_met",
                        "lksg_prohibited_practice_flag", "ilo_indicator_flags",
                        "compliance_programme_maturity", "audit_coverage_pct",
                        "high_risk_suppliers_pct", "priority_actions"],
            "reference_data": ["eu_flr_2024_3015", "ilo_indicators_2012",
                                "uk_msa_2015_s54", "german_lksg_2023",
                                "california_scatca", "sa8000_standard"],
            "quality_indicators": ["eu_flr_import_risk", "compliance_programme_maturity"],
        },
        "transition_finance_engine": {
            "inputs": ["entity_id", "entity_name", "sector",
                       "emissions_intensity_current", "emissions_intensity_2030_target",
                       "capex_low_carbon_pct", "transition_plan_doc",
                       "loan_book_positions", "bond_type"],
            "outputs": ["gfanz_category", "tpt_sector_pathway_alignment_pct",
                        "transition_plan_credibility_score", "credibility_rating",
                        "transition_finance_ratio_pct", "gar_pct",
                        "bond_type_recommendation", "alignment_gap_pct",
                        "brown_overhang_mn", "kpi_ambition_score", "warnings"],
            "reference_data": ["gfanz_guidance_2022", "uk_tpt_sector_pathways",
                                "mas_singapore_gtt_2024", "japan_gx_roadmap",
                                "icma_ctf_handbook_2023", "ngfs_net_zero_2050"],
            "quality_indicators": ["transition_plan_credibility_score", "gfanz_category"],
        },
    }

    for module_name, signature in new_signatures.items():
        if module_name not in service_instance._module_signatures:
            service_instance._module_signatures[module_name] = signature

    new_edges = [
        # E36 Basel III Liquidity
        {"from": "portfolio_analytics",         "to": "basel3_liquidity_engine",    "type": "portfolio_liquidity_profile"},
        {"from": "climate_physical_risk",       "to": "basel3_liquidity_engine",    "type": "climate_hqla_haircut"},
        {"from": "sovereign_climate_risk",      "to": "basel3_liquidity_engine",    "type": "sovereign_bond_hqla_quality"},
        {"from": "basel3_liquidity_engine",     "to": "regulatory_report_compiler", "type": "lcr_nsfr_disclosure"},
        {"from": "basel3_liquidity_engine",     "to": "factor_overlay_engine",      "type": "liquidity_risk_overlay"},
        # E37 Social Taxonomy & Impact
        {"from": "csrd_engine",                 "to": "social_taxonomy_engine",     "type": "esrs_s1_s4_workforce_data"},
        {"from": "supply_chain_engine",         "to": "social_taxonomy_engine",     "type": "supply_chain_social_indicators"},
        {"from": "social_taxonomy_engine",      "to": "regulatory_report_compiler", "type": "social_taxonomy_disclosure"},
        {"from": "social_taxonomy_engine",      "to": "entity360",                  "type": "social_impact_enrichment"},
        {"from": "social_taxonomy_engine",      "to": "factor_overlay_engine",      "type": "social_factor_overlay"},
        # E38 Forced Labour
        {"from": "supply_chain_engine",         "to": "forced_labour_engine",       "type": "supplier_node_data"},
        {"from": "csddd_engine",                "to": "forced_labour_engine",       "type": "csddd_hr01_adverse_impact"},
        {"from": "forced_labour_engine",        "to": "regulatory_report_compiler", "type": "forced_labour_disclosure"},
        {"from": "forced_labour_engine",        "to": "entity360",                  "type": "forced_labour_risk_enrichment"},
        # E39 Transition Finance
        {"from": "climate_transition_risk",     "to": "transition_finance_engine",  "type": "transition_pathway_scenarios"},
        {"from": "net_zero_targets_engine",     "to": "transition_finance_engine",  "type": "net_zero_alignment_score"},
        {"from": "carbon_calculator",           "to": "transition_finance_engine",  "type": "current_emissions_intensity"},
        {"from": "transition_finance_engine",   "to": "portfolio_analytics",        "type": "transition_finance_ratio"},
        {"from": "transition_finance_engine",   "to": "regulatory_report_compiler", "type": "transition_finance_disclosure"},
        {"from": "transition_finance_engine",   "to": "entity360",                  "type": "transition_classification_enrichment"},
    ]

    existing_edge_keys = {(e.get("from"), e.get("to")) for e in service_instance._dependencies}
    for edge in new_edges:
        key = (edge.get("from"), edge.get("to"))
        if key not in existing_edge_keys:
            service_instance._dependencies.append(edge)
            existing_edge_keys.add(key)


def _register_e40_e43_modules(service_instance) -> None:
    """Register E40-E43 engines in the data lineage graph."""
    new_signatures = {
        "csrd_dma_engine": {
            "inputs": ["entity_id", "entity_name", "sector", "nace_code",
                       "reporting_period", "stakeholder_data", "impact_data",
                       "financial_risk_data", "value_chain_scope"],
            "outputs": ["material_topics", "non_material_topics", "material_topics_count",
                        "impact_material_count", "financial_material_count", "both_material_count",
                        "dma_process_completeness_pct", "esrs_standards_applicable",
                        "engagement_quality_score", "assurance_readiness_pct",
                        "priority_actions", "cross_framework"],
            "reference_data": ["esrs1_dma_guidance_2023", "efrag_implementation_guidance",
                                "esrs_topic_catalog", "sector_materiality_benchmarks"],
            "quality_indicators": ["dma_process_completeness_pct", "material_topics_count"],
        },
        "physical_hazard_engine": {
            "inputs": ["entity_id", "asset_name", "asset_type", "lat", "lng",
                       "country_code", "climate_scenario", "time_horizon",
                       "asset_characteristics"],
            "outputs": ["composite_hazard_score", "risk_tier", "primary_hazard",
                        "flood_risk_score", "wildfire_risk_score", "heat_stress_score",
                        "sea_level_rise_score", "cyclone_risk_score", "drought_risk_score",
                        "property_damage_pct", "stranded_value_risk_pct",
                        "adaptation_capex_mn", "stranding_year", "crrem_pathway_compliant"],
            "reference_data": ["ipcc_ar6_wg2_hazards", "jrc_climate_hazard_atlas",
                                "wri_aqueduct_4_0", "crrem_pathways", "ngfs_physical_scenarios"],
            "quality_indicators": ["composite_hazard_score", "risk_tier"],
        },
        "avoided_emissions_engine": {
            "inputs": ["entity_id", "entity_name", "assessment_type", "reporting_year",
                       "activities", "baseline_scenario", "methodology"],
            "outputs": ["enabled_emissions_tco2e", "substitution_emissions_tco2e",
                        "facilitated_avoided_tco2e", "total_avoided_tco2e",
                        "net_benefit_tco2e", "additionality_score", "attribution_factor",
                        "article6_eligible", "itmo_units_mn", "sbti_bvcm_eligible",
                        "science_based_claim", "warnings"],
            "reference_data": ["ghg_protocol_scope4_2022", "article6_paris_agreement",
                                "sbti_bvcm_guidance", "iso14064_3", "sector_baseline_factors"],
            "quality_indicators": ["total_avoided_tco2e", "additionality_score", "data_quality_score"],
        },
        "green_hydrogen_engine": {
            "inputs": ["entity_id", "project_name", "country_code", "production_pathway",
                       "electrolysis_technology", "capacity_mw", "renewable_electricity_pct",
                       "electricity_cost_mwh", "capex_per_kw", "h2_subsidy_scheme"],
            "outputs": ["eu_delegated_act_compliant", "carbon_intensity_kgco2e_kgh2",
                        "eu_taxonomy_aligned", "lcoh_usd_per_kgh2", "net_lcoh_after_subsidy",
                        "additionality_met", "temporal_correlation_met",
                        "gfanz_category", "sustainable_finance_label", "warnings"],
            "reference_data": ["eu_delegated_act_2023_1184", "eu_rfnbo_criteria",
                                "ira_45v_hydrogen_ptc", "japan_gx_roadmap",
                                "irena_h2_cost_curves", "ngfs_net_zero_h2"],
            "quality_indicators": ["lcoh_usd_per_kgh2", "carbon_intensity_kgco2e_kgh2",
                                   "eu_delegated_act_compliant"],
        },
    }

    for module_name, signature in new_signatures.items():
        if module_name not in service_instance._module_signatures:
            service_instance._module_signatures[module_name] = signature

    new_edges = [
        # E40 CSRD Double Materiality
        {"from": "csrd_engine",                "to": "csrd_dma_engine",           "type": "esrs_topic_catalog_input"},
        {"from": "double_materiality",         "to": "csrd_dma_engine",           "type": "existing_materiality_baseline"},
        {"from": "climate_physical_risk",      "to": "csrd_dma_engine",           "type": "physical_risk_topic_input"},
        {"from": "climate_transition_risk",    "to": "csrd_dma_engine",           "type": "transition_risk_topic_input"},
        {"from": "csrd_dma_engine",            "to": "regulatory_report_compiler","type": "dma_output_for_csrd_report"},
        {"from": "csrd_dma_engine",            "to": "entity360",                 "type": "material_topics_enrichment"},
        # E41 Physical Climate Hazard
        {"from": "climate_physical_risk",      "to": "physical_hazard_engine",    "type": "regional_hazard_data"},
        {"from": "nature_risk",                "to": "physical_hazard_engine",    "type": "ecosystem_vulnerability"},
        {"from": "physical_hazard_engine",     "to": "ecl_climate",               "type": "collateral_haircut_input"},
        {"from": "physical_hazard_engine",     "to": "portfolio_analytics",       "type": "physical_risk_var"},
        {"from": "physical_hazard_engine",     "to": "regulatory_report_compiler","type": "physical_risk_disclosure"},
        # E42 Scope 4 Avoided Emissions
        {"from": "carbon_calculator",          "to": "avoided_emissions_engine",  "type": "baseline_scope1_2_3_input"},
        {"from": "net_zero_targets_engine",    "to": "avoided_emissions_engine",  "type": "bvcm_framework_input"},
        {"from": "avoided_emissions_engine",   "to": "regulatory_report_compiler","type": "avoided_emissions_disclosure"},
        {"from": "avoided_emissions_engine",   "to": "entity360",                 "type": "scope4_enrichment"},
        # E43 Green Hydrogen
        {"from": "climate_transition_risk",    "to": "green_hydrogen_engine",     "type": "carbon_price_trajectory"},
        {"from": "eu_taxonomy_gar",            "to": "green_hydrogen_engine",     "type": "taxonomy_alignment_check"},
        {"from": "green_hydrogen_engine",      "to": "transition_finance_engine", "type": "h2_gfanz_classification"},
        {"from": "green_hydrogen_engine",      "to": "regulatory_report_compiler","type": "h2_disclosure"},
        {"from": "green_hydrogen_engine",      "to": "entity360",                 "type": "h2_project_enrichment"},
    ]

    existing_edge_keys = {(e.get("from"), e.get("to")) for e in service_instance._dependencies}
    for edge in new_edges:
        key = (edge.get("from"), edge.get("to"))
        if key not in existing_edge_keys:
            service_instance._dependencies.append(edge)
            existing_edge_keys.add(key)


def _register_e44_e47_modules(service_instance) -> None:
    """Register E44-E47 engines in the data lineage graph."""
    new_signatures = {
        "biodiversity_finance_v2_engine": {
            "label": "Biodiversity Finance v2 Engine",
            "category": "nature",
            "inputs": ["entity_id", "portfolio_holdings", "asset_locations", "sector_nace",
                       "activity_footprint_km2", "financial_year", "gbf_reporting_period"],
            "outputs": ["leap_composite_score", "pbaf_attribution_factor", "encore_dependency_scores",
                        "encore_impact_scores", "msa_footprint_km2", "msa_loss_fraction",
                        "gbf_target15_alignment", "cop15_30x30_contribution_pct",
                        "bng_net_gain_pct", "bffi_score", "materiality_rating",
                        "priority_ecosystems_list", "esrs_e4_alignment", "gri_304_score",
                        "eu_taxonomy_dnsh_nature", "sbtn_target_alignment"],
            "reference_data": ["tnfd_14_step_leap_framework", "pbaf_methodology_v2024",
                               "encore_23_ecosystem_services_matrix", "gbf_targets_1_23",
                               "msa_land_use_lookup_table", "bng_metric_4_habitat_values",
                               "bffi_methodology_pdf_m2yr", "iucn_red_list_categories"],
            "quality_indicators": ["location_data_completeness", "encore_sector_match_pct",
                                   "financial_data_vintage_months"],
        },
        "prudential_climate_risk_engine": {
            "label": "Prudential Climate Risk Engine",
            "category": "risk",
            "inputs": ["entity_id", "institution_type", "loan_book_segments", "market_portfolio",
                       "regulator", "scenario_framework", "baseline_cet1_pct",
                       "portfolio_brown_share_pct", "reporting_date"],
            "outputs": ["stressed_cet1_orderly", "stressed_cet1_disorderly", "stressed_cet1_hot_house",
                        "cet1_depletion_max_ppts", "pd_migration_bps", "lgd_increase_pct",
                        "ecl_increase_musd", "market_risk_loss_musd", "icaap_climate_add_on_pct",
                        "pillar2b_buffer_pct", "srep_climate_finding", "srp431_categorisation",
                        "eba_srep_climate_score", "total_climate_capital_buffer_pct",
                        "capital_overlays_by_segment", "ngfs_v4_scenario_results"],
            "reference_data": ["boe_bes_2025_scenarios", "ecb_dfast_2024_scenarios", "ngfs_v4_6_scenarios",
                               "icaap_climate_guidance_ss319", "basel_srp_431_categorisation",
                               "eba_srep_climate_scoring_gl", "pd_migration_matrices_by_sector"],
            "quality_indicators": ["loan_book_coverage_pct", "scenario_alignment_score",
                                   "capital_model_completeness"],
        },
        "carbon_markets_intel_engine": {
            "label": "Carbon Markets Intelligence Engine",
            "category": "carbon",
            "inputs": ["entity_id", "credit_portfolio", "purpose", "assessment_date",
                       "entity_abatement_plan", "sbti_target_type", "corsia_operator_flag"],
            "outputs": ["total_credits_tco2e", "weighted_avg_price_usd", "vcmi_claim_level",
                        "vcmi_eligible", "vcmi_mitigation_contribution_pct",
                        "icvcm_ccp_pass_rate_pct", "corsia_eligible_pct",
                        "article6_itmo_volume", "corresponding_adjustment_pct",
                        "high_integrity_share_pct", "fair_value_usd_tco2e",
                        "price_premium_discount_pct", "registry_records", "quality_scores"],
            "reference_data": ["vcmi_claims_code_2023_gold_silver_bronze", "icvcm_10_ccp_criteria",
                               "corsia_phase2_eligible_units_list", "article_6_2_bilateral_agreements",
                               "article_6_4_mechanism_rules", "verra_vcs_methodology_database",
                               "gold_standard_methodology_database", "carbon_credit_pricing_benchmarks"],
            "quality_indicators": ["registry_verification_pct", "vintage_recency_score",
                                   "additionality_evidence_completeness"],
        },
        "just_transition_engine": {
            "label": "Just Transition & Social Risk Engine",
            "category": "social",
            "inputs": ["entity_id", "sector", "geography", "workforce_data", "supply_chain_data",
                       "community_exposure_data", "wage_data", "automation_risk_profile",
                       "reskilling_programmes", "assessment_date"],
            "outputs": ["ilo_jt_composite_score", "ilo_jt_classification",
                        "esrs_s1_score", "esrs_s2_score", "esrs_s3_score", "esrs_s4_score",
                        "esrs_social_composite_score", "sec_hc_disclosure_quality",
                        "living_wage_gap_pct", "median_wage_to_living_wage_ratio",
                        "automation_risk_high_pct", "transition_displacement_pct",
                        "reskilling_investment_adequacy", "cbi_jt_criteria_met",
                        "jt_finance_eligible", "overall_jt_score", "risk_rating",
                        "stakeholder_impact_map", "key_gaps", "recommendations"],
            "reference_data": ["ilo_just_transition_guidelines_2015", "esrs_s1_s4_disclosure_requirements",
                               "sec_reg_sk_item_101c_guidance", "anker_living_wage_benchmarks_70_countries",
                               "cbi_jt_taxonomy_8_criteria", "automation_nace_risk_taxonomy",
                               "ungp_pillar_ii_operational_principles", "oecd_rbc_guidelines_ch4_5"],
            "quality_indicators": ["workforce_data_completeness", "wage_data_coverage_pct",
                                   "community_engagement_evidence"],
        },
    }

    for module_id, sig in new_signatures.items():
        if module_id not in service_instance._module_signatures:
            service_instance._module_signatures[module_id] = sig

    new_edges = [
        # E44 Biodiversity Finance v2
        {"from": "nature_risk",                    "to": "biodiversity_finance_v2_engine",  "type": "tnfd_leap_base_scores"},
        {"from": "tnfd_leap_engine",               "to": "biodiversity_finance_v2_engine",  "type": "leap_locate_evaluate_output"},
        {"from": "eu_taxonomy_gar",                "to": "biodiversity_finance_v2_engine",  "type": "dnsh_nature_check"},
        {"from": "biodiversity_finance_v2_engine", "to": "regulatory_report_compiler",      "type": "tnfd_pbaf_disclosure"},
        {"from": "biodiversity_finance_v2_engine", "to": "entity360",                       "type": "nature_risk_enrichment"},
        {"from": "biodiversity_finance_v2_engine", "to": "factor_overlay_engine",           "type": "biodiversity_nat_cat_factor"},
        # E45 Prudential Climate Risk
        {"from": "climate_physical_risk",          "to": "prudential_climate_risk_engine",  "type": "physical_risk_pd_migration"},
        {"from": "climate_transition_risk",        "to": "prudential_climate_risk_engine",  "type": "transition_risk_cet1_stress"},
        {"from": "sovereign_climate_risk_engine",  "to": "prudential_climate_risk_engine",  "type": "sovereign_spread_input"},
        {"from": "ecl_engine",                     "to": "prudential_climate_risk_engine",  "type": "baseline_ecl_for_stress"},
        {"from": "prudential_climate_risk_engine", "to": "portfolio_analytics",             "type": "stressed_capital_metrics"},
        {"from": "prudential_climate_risk_engine", "to": "regulatory_report_compiler",      "type": "pillar2_climate_disclosure"},
        {"from": "prudential_climate_risk_engine", "to": "factor_overlay_engine",           "type": "regulatory_capital_factor"},
        # E46 Carbon Markets Intelligence
        {"from": "carbon_credit_quality_engine",   "to": "carbon_markets_intel_engine",     "type": "existing_ccp_quality_scores"},
        {"from": "net_zero_targets_engine",        "to": "carbon_markets_intel_engine",     "type": "bvcm_abatement_residual"},
        {"from": "avoided_emissions_engine",       "to": "carbon_markets_intel_engine",     "type": "scope4_offset_demand"},
        {"from": "carbon_markets_intel_engine",    "to": "regulatory_report_compiler",      "type": "vcmi_art6_disclosure"},
        {"from": "carbon_markets_intel_engine",    "to": "entity360",                       "type": "carbon_portfolio_quality"},
        # E47 Just Transition
        {"from": "forced_labour_engine",           "to": "just_transition_engine",          "type": "forced_labour_esrs_s2_input"},
        {"from": "social_taxonomy_engine",         "to": "just_transition_engine",          "type": "social_taxonomy_alignment"},
        {"from": "factor_overlay_engine",          "to": "just_transition_engine",          "type": "automation_disruption_risk"},
        {"from": "just_transition_engine",         "to": "regulatory_report_compiler",      "type": "esrs_s1_s4_disclosure"},
        {"from": "just_transition_engine",         "to": "entity360",                       "type": "social_risk_enrichment"},
    ]

    existing_edge_keys = {(e.get("from"), e.get("to")) for e in service_instance._dependencies}
    for edge in new_edges:
        key = (edge.get("from"), edge.get("to"))
        if key not in existing_edge_keys:
            service_instance._dependencies.append(edge)
            existing_edge_keys.add(key)


def _register_e48_e51_modules(service_instance) -> None:
    """Register E48-E51 engines in the data lineage graph."""
    new_signatures = {
        "shipping_maritime_engine": {
            "label": "Shipping & Maritime Decarbonisation Engine",
            "category": "sector",
            "inputs": ["entity_id", "vessel_imo", "vessel_type", "gross_tonnage", "deadweight_tonnage",
                       "fuel_type", "annual_fuel_consumption_t", "voyage_data", "assessment_year"],
            "outputs": ["cii_attained", "cii_required", "cii_rating", "eexi_attained", "eexi_compliant",
                        "pp_alignment_score", "fueleu_ghg_intensity_wtw", "fueleu_penalty_eur",
                        "scc_aer_aligned", "ets_surrender_gap", "ets_cost_eur",
                        "alt_fuel_readiness", "fuel_switch_capex", "stranding_year", "fleet_portfolio_report"],
            "reference_data": ["imo_ghg_strategy_2023_cii_table", "eexi_required_values_by_vessel_type",
                               "poseidon_principles_required_trajectory", "fueleu_maritime_ghg_targets",
                               "sea_cargo_charter_aer_benchmarks", "eu_ets_shipping_phase_in_schedule",
                               "alternative_fuel_emission_factors"],
            "quality_indicators": ["voyage_data_completeness", "fuel_measurement_method",
                                   "imo_dnv_verification_status"],
        },
        "aviation_climate_engine": {
            "label": "Aviation Climate Risk Engine",
            "category": "sector",
            "inputs": ["entity_id", "icao_designator", "fleet_data", "routes_data",
                       "fuel_consumption_t", "revenue_tonne_km", "assessment_year"],
            "outputs": ["corsia_offsetting_obligation_tco2", "corsia_offset_cost_usd",
                        "saf_blend_pct", "saf_compliance_gap", "saf_cost_usd",
                        "ira_45z_credit_usd", "ets_aviation_surrender_gap", "ets_cost_eur",
                        "iata_nzc_alignment_score", "aircraft_stranding_risk_usd",
                        "stranding_year_median", "fleet_avg_age"],
            "reference_data": ["corsia_phase2_eligible_schemes", "refueleu_saf_mandates_2025_2050",
                               "ira_45z_saf_credit_schedule", "eu_ets_aviation_free_allocation",
                               "iata_nzc_pathway_split", "aircraft_co2_intensity_by_type"],
            "quality_indicators": ["rtk_data_completeness", "fuel_burn_measurement_accuracy",
                                   "corsia_monitoring_scheme"],
        },
        "commercial_re_engine": {
            "label": "Commercial Real Estate Net Zero Engine",
            "category": "real_estate",
            "inputs": ["entity_id", "asset_type", "gross_floor_area_m2", "location_country",
                       "annual_energy_kwh", "fuel_mix", "construction_year", "assessment_date"],
            "outputs": ["crrem_energy_intensity", "crrem_co2_intensity", "crrem_stranding_year",
                        "epc_rating", "epbd_renovation_required", "gresb_score",
                        "refi_composite_score", "nabers_energy_stars", "green_lease_score",
                        "retrofit_measures", "retrofit_npv", "retrofit_irr",
                        "green_premium_pct", "brown_discount_pct"],
            "reference_data": ["crrem_v2_pathways_by_type_country", "epc_rating_thresholds",
                               "epbd_2024_minimum_requirements", "gresb_re_2024_methodology",
                               "refi_risk_scoring_protocol", "nabers_energy_benchmarks",
                               "green_premium_research_jll_cbre"],
            "quality_indicators": ["energy_metering_coverage", "asset_data_vintage",
                                   "certification_verification"],
        },
        "infrastructure_finance_engine": {
            "label": "Infrastructure Climate Finance Engine",
            "category": "project_finance",
            "inputs": ["entity_id", "project_type", "sector", "country", "total_cost_usd",
                       "debt_amount_usd", "equity_amount_usd", "project_lifetime_yrs",
                       "annual_ghg_reduction_tco2", "mdb_participation"],
            "outputs": ["ep_category", "ep_10_principles_scores", "ifc_ps_composite_score",
                        "ifc_ps_1_8_scores", "oecd_tier", "pa_alignment_score",
                        "dscr_baseline", "dscr_physical_stress", "dscr_combined_stress",
                        "cbi_certified", "icma_gbf_aligned", "blended_finance_structure",
                        "crowding_in_ratio", "private_finance_mobilised"],
            "reference_data": ["equator_principles_iv_2020", "ifc_ps_1_8_requirements",
                               "oecd_common_approaches_2022", "idfc_paris_alignment_framework",
                               "cbi_climate_bonds_standard_v4", "icma_gbf_2021",
                               "oecd_blended_finance_additionality_criteria"],
            "quality_indicators": ["esap_completeness", "ifc_ps_evidence_quality",
                                   "financial_model_robustness"],
        },
    }

    for module_id, sig in new_signatures.items():
        if module_id not in service_instance._module_signatures:
            service_instance._module_signatures[module_id] = sig

    new_edges = [
        # E48 Shipping & Maritime
        {"from": "climate_physical_risk",          "to": "shipping_maritime_engine",        "type": "sea_level_storm_hazard"},
        {"from": "stranded_asset_calculator",      "to": "shipping_maritime_engine",        "type": "vessel_stranding_model"},
        {"from": "shipping_maritime_engine",       "to": "portfolio_analytics",             "type": "fleet_transition_risk"},
        {"from": "shipping_maritime_engine",       "to": "regulatory_report_compiler",      "type": "imo_ets_disclosure"},
        {"from": "shipping_maritime_engine",       "to": "factor_overlay_engine",           "type": "shipping_sector_overlay"},
        # E49 Aviation Climate
        {"from": "climate_physical_risk",          "to": "aviation_climate_engine",         "type": "airport_physical_risk"},
        {"from": "carbon_markets_intel_engine",    "to": "aviation_climate_engine",         "type": "corsia_offset_sourcing"},
        {"from": "aviation_climate_engine",        "to": "portfolio_analytics",             "type": "aviation_transition_risk"},
        {"from": "aviation_climate_engine",        "to": "regulatory_report_compiler",      "type": "corsia_ets_disclosure"},
        {"from": "aviation_climate_engine",        "to": "stranded_asset_calculator",       "type": "aircraft_stranding_input"},
        # E50 Commercial Real Estate
        {"from": "climate_physical_risk",          "to": "commercial_re_engine",            "type": "asset_physical_hazard"},
        {"from": "real_estate_valuation",          "to": "commercial_re_engine",            "type": "baseline_asset_value"},
        {"from": "commercial_re_engine",           "to": "ecl_engine",                      "type": "collateral_climate_haircut"},
        {"from": "commercial_re_engine",           "to": "portfolio_analytics",             "type": "re_stranding_risk"},
        {"from": "commercial_re_engine",           "to": "regulatory_report_compiler",      "type": "gresb_crrem_disclosure"},
        # E51 Infrastructure Finance
        {"from": "climate_physical_risk",          "to": "infrastructure_finance_engine",   "type": "project_physical_exposure"},
        {"from": "climate_transition_risk",        "to": "infrastructure_finance_engine",   "type": "capex_transition_overlay"},
        {"from": "ecl_engine",                     "to": "infrastructure_finance_engine",   "type": "baseline_dscr_ecl"},
        {"from": "infrastructure_finance_engine",  "to": "portfolio_analytics",             "type": "project_finance_risk"},
        {"from": "infrastructure_finance_engine",  "to": "regulatory_report_compiler",      "type": "ep4_ifc_ps_disclosure"},
        {"from": "infrastructure_finance_engine",  "to": "entity360",                       "type": "project_enrichment"},
    ]

    existing_edge_keys = {(e.get("from"), e.get("to")) for e in service_instance._dependencies}
    for edge in new_edges:
        key = (edge.get("from"), edge.get("to"))
        if key not in existing_edge_keys:
            service_instance._dependencies.append(edge)
            existing_edge_keys.add(key)


def _register_e52_e55_modules(service_instance) -> None:
    """Register E52-E55 engines in the data lineage graph."""
    new_signatures = {
        "nature_based_solutions_engine": {
            "label": "Nature-Based Solutions & Carbon Sequestration Engine",
            "category": "nature",
            "inputs": ["entity_id", "project_type", "area_ha", "country_code", "ecosystem_type",
                       "reference_level_tco2_pa", "actual_emissions_tco2_pa", "ipcc_tier",
                       "species_type", "co_benefits"],
            "outputs": ["iucn_gs_score", "iucn_gs_standard_met", "redd_net_credits_tco2_pa",
                        "blue_carbon_seq_tco2_pa", "soil_carbon_tco2_pa", "arr_total_tco2_pa",
                        "afolu_net_balance_tco2e_pa", "overall_credit_quality_score",
                        "icvcm_ccp_compatible", "estimated_credit_price_usd",
                        "sequestration_timeseries", "cobenefit_premium_pct"],
            "reference_data": ["iucn_global_standard_v2_criteria", "vcs_vm0007_redd_methodology",
                               "blue_carbon_vm0033_vm0024", "ipcc_ar6_soil_carbon_factors",
                               "icvcm_core_carbon_principles_2023"],
            "quality_indicators": ["project_verification_status", "measurement_methodology_tier",
                                   "permanence_risk_assessment"],
        },
        "water_risk_engine": {
            "label": "Water Risk & Security Engine",
            "category": "nature",
            "inputs": ["entity_id", "country_code", "sector", "basin_name", "latitude", "longitude",
                       "withdrawal_m3_pa", "consumption_m3_pa", "discharge_m3_pa", "recycled_pct",
                       "annual_revenue_usd", "governance_score", "risk_score"],
            "outputs": ["aqueduct_overall_score", "aqueduct_risk_tier", "cdp_water_grade",
                        "cdp_a_list_eligible", "esrs_e3_disclosure_score", "esrs_e3_water_intensive",
                        "tnfd_water_dependency_score", "water_footprint_m3",
                        "revenue_at_risk_pct", "compliance_cost_usd_pa", "materiality_rating",
                        "physical_risk_rcp26", "physical_risk_rcp45", "physical_risk_rcp85"],
            "reference_data": ["wri_aqueduct_4_indicators", "cdp_water_security_methodology",
                               "csrd_esrs_e3_disclosure_requirements", "tnfd_encore_water_services",
                               "un_sdg6_targets"],
            "quality_indicators": ["water_measurement_method", "basin_data_resolution",
                                   "cdp_reporting_completeness"],
        },
        "food_system_engine": {
            "label": "Food System & Land Use Finance Engine",
            "category": "agriculture",
            "inputs": ["entity_id", "sector", "commodities", "country_codes", "farm_area_ha",
                       "livestock_count", "crop_type", "base_year", "target_year",
                       "current_emissions_tco2e", "baseline_yield_t_ha"],
            "outputs": ["flag_scope", "required_reduction_pct", "land_mitigation_tco2_pa",
                        "fao_yield_impact_rcp26", "fao_yield_impact_rcp45", "fao_yield_impact_rcp85",
                        "tnfd_leap_composite", "eudr_deforestation_free", "eudr_compliant",
                        "ag_total_emissions_tco2e", "ldn_status", "restoration_potential_ha"],
            "reference_data": ["sbti_flag_sector_pathways", "fao_crop_yield_rcp_projections",
                               "tnfd_food_leap_framework", "eudr_2023_1115_annex_i",
                               "ipcc_tier1_livestock_emission_factors", "ldn_2030_targets"],
            "quality_indicators": ["supply_chain_traceability_tier", "geolocation_coverage_pct",
                                   "measurement_boundary_completeness"],
        },
        "circular_economy_engine": {
            "label": "Circular Economy Finance Engine",
            "category": "resources",
            "inputs": ["entity_id", "resource_inflows_t", "recycled_inflows_pct", "resource_outflows_t",
                       "waste_t", "materials_used", "packaging_tonnes", "ewaste_tonnes", "battery_tonnes",
                       "product_name", "annual_production", "sector"],
            "outputs": ["esrs_e5_disclosure_score", "esrs_e5_grade", "mci_score", "cti_composite_score",
                        "cti_tier", "epr_total_cost_eur_pa", "crm_dependency_score",
                        "lca_cradle_to_cradle_kgco2e", "lca_circularity_benefit_pct",
                        "overall_circularity_score", "risk_rating", "investment_needed_usd",
                        "green_finance_eligible"],
            "reference_data": ["csrd_esrs_e5_disclosure_requirements", "emf_mci_methodology",
                               "wbcsd_cti_v4_framework", "eu_cca_crm_list_2023",
                               "epr_directive_packaging_2018", "iso_14044_lca_standard"],
            "quality_indicators": ["material_flow_data_completeness", "lca_boundary_definition",
                                   "epr_reporting_coverage"],
        },
    }

    for module_id, sig in new_signatures.items():
        if module_id not in service_instance._module_signatures:
            service_instance._module_signatures[module_id] = sig

    new_edges = [
        # E52 Nature-Based Solutions
        {"from": "climate_physical_risk",          "to": "nature_based_solutions_engine",   "type": "climate_scenario_permanence_risk"},
        {"from": "biodiversity_finance_v2_engine", "to": "nature_based_solutions_engine",   "type": "biodiversity_cobenefit_scoring"},
        {"from": "carbon_markets_intel_engine",    "to": "nature_based_solutions_engine",   "type": "credit_quality_benchmark"},
        {"from": "nature_based_solutions_engine",  "to": "carbon_markets_intel_engine",     "type": "nbs_credit_supply"},
        {"from": "nature_based_solutions_engine",  "to": "regulatory_report_compiler",      "type": "nbs_csrd_e4_disclosure"},
        {"from": "nature_based_solutions_engine",  "to": "portfolio_analytics",             "type": "carbon_credit_valuation"},
        # E53 Water Risk
        {"from": "climate_physical_risk",          "to": "water_risk_engine",               "type": "precipitation_drought_hazard"},
        {"from": "nature_based_solutions_engine",  "to": "water_risk_engine",               "type": "watershed_restoration_cobenefits"},
        {"from": "water_risk_engine",              "to": "ecl_engine",                      "type": "water_stress_pd_overlay"},
        {"from": "water_risk_engine",              "to": "regulatory_report_compiler",      "type": "esrs_e3_cdp_disclosure"},
        {"from": "water_risk_engine",              "to": "factor_overlay_engine",           "type": "water_stress_sector_overlay"},
        # E54 Food System
        {"from": "agriculture_risk_engine",        "to": "food_system_engine",              "type": "crop_climate_risk_transfer"},
        {"from": "water_risk_engine",              "to": "food_system_engine",              "type": "agricultural_water_dependency"},
        {"from": "eudr_engine",                    "to": "food_system_engine",              "type": "deforestation_free_screening"},
        {"from": "food_system_engine",             "to": "portfolio_analytics",             "type": "ag_transition_risk"},
        {"from": "food_system_engine",             "to": "regulatory_report_compiler",      "type": "flag_csrd_e4_disclosure"},
        # E55 Circular Economy
        {"from": "climate_transition_risk",        "to": "circular_economy_engine",         "type": "carbon_price_material_cost"},
        {"from": "food_system_engine",             "to": "circular_economy_engine",         "type": "bio_based_material_flows"},
        {"from": "circular_economy_engine",        "to": "regulatory_report_compiler",      "type": "esrs_e5_disclosure"},
        {"from": "circular_economy_engine",        "to": "portfolio_analytics",             "type": "circular_transition_risk"},
    ]

    existing_edge_keys = {(e.get("from"), e.get("to")) for e in service_instance._dependencies}
    for edge in new_edges:
        key = (edge.get("from"), edge.get("to"))
        if key not in existing_edge_keys:
            service_instance._dependencies.append(edge)
            existing_edge_keys.add(key)


def _register_e56_e59_modules(service_instance) -> None:
    """Register E56-E59 engines in the data lineage graph."""
    new_signatures = {
        "climate_litigation_engine": {
            "label": "Climate Litigation & Legal Risk Engine",
            "category": "regulatory",
            "inputs": ["entity_id", "sector", "jurisdiction", "revenue_usd", "emissions_tco2e",
                       "tcfd_disclosure_score", "climate_targets_set", "green_claims",
                       "d_and_o_coverage_usd", "historical_cases"],
            "outputs": ["tcfd_liability_score", "greenwashing_risk_score", "do_exposure_score",
                        "sec_climate_compliance_score", "attribution_science_liability_pct",
                        "portfolio_litigation_risk_usd", "overall_litigation_risk",
                        "litigation_risk_rating", "regulatory_penalties_usd"],
            "reference_data": ["tcfd_recommendations_2017", "eu_green_claims_directive_2023_2441",
                               "fca_consumer_duty_2023", "sec_reg_sk_items_1501_1505",
                               "climate_attribution_science_ipcc_ar6"],
            "quality_indicators": ["disclosure_audit_status", "legal_counsel_assessment",
                                   "case_database_coverage"],
        },
        "esg_ratings_engine": {
            "label": "ESG Ratings Reform & Divergence Engine",
            "category": "regulatory",
            "inputs": ["entity_id", "sector", "country_code", "revenue_usd", "market_cap_usd",
                       "employees", "msci_rating", "sustainalytics_score", "bloomberg_score",
                       "ftse_score", "sp_score", "iss_score"],
            "outputs": ["esra_authorisation_score", "esra_compliant", "divergence_pct",
                        "scope_divergence_pct", "weight_divergence_pct", "measurement_divergence_pct",
                        "composite_esg_rating", "composite_score", "e_pillar_divergence",
                        "size_bias_detected", "geography_bias_detected", "sector_bias_detected",
                        "peer_benchmark_percentile"],
            "reference_data": ["eu_esra_2024_3005_requirements", "berg_et_al_divergence_taxonomy",
                               "msci_esg_methodology", "sustainalytics_risk_ratings",
                               "bloomberg_esg_framework"],
            "quality_indicators": ["rating_provider_coverage", "disclosure_completeness",
                                   "methodology_transparency_score"],
        },
        "methane_fugitive_engine": {
            "label": "Methane & Fugitive Emissions Engine",
            "category": "emissions",
            "inputs": ["entity_id", "sector", "production_volume", "production_unit",
                       "country_code", "baseline_methane_tpa", "reported_gwp_basis",
                       "ogmp_level", "ldar_programme", "super_emitter_events"],
            "outputs": ["gwp100_co2e_tpa", "gwp20_co2e_tpa", "eu_methane_reg_compliant",
                        "ogmp_level_current", "ogmp_level_target", "ogmp_gap_score",
                        "super_emitter_events_detected", "methane_intensity_pct",
                        "abatement_potential_tpa", "abatement_cost_usd_t", "ldar_compliance_score",
                        "unep_intensity_target_met"],
            "reference_data": ["eu_methane_regulation_2024_1787", "ogmp_2_0_framework",
                               "ipcc_ar6_gwp100_gwp20", "iea_methane_abatement_curve",
                               "epa_ooooa_ooob_ldar_requirements", "unep_imeo_satellite_data"],
            "quality_indicators": ["measurement_level", "satellite_verification_coverage",
                                   "ldar_survey_frequency"],
        },
        "health_climate_engine": {
            "label": "Health-Climate Nexus Engine",
            "category": "physical_risk",
            "inputs": ["entity_id", "country_code", "sector", "outdoor_workers_pct",
                       "facility_locations", "pm25_baseline_ug_m3", "wbgt_baseline_c",
                       "annual_revenue_usd", "workforce_size", "insurance_premium_usd"],
            "outputs": ["wbgt_heat_stress_score", "productivity_loss_pct", "labour_capacity_reduction_pct",
                        "pm25_health_risk_score", "who_aqg_exceedance", "eu_aqd_exceedance",
                        "vector_disease_rcp26_risk", "vector_disease_rcp45_risk", "vector_disease_rcp85_risk",
                        "health_financial_impact_usd", "healthcare_uplift_usd", "productivity_loss_usd",
                        "composite_health_climate_score", "who_ccs_readiness"],
            "reference_data": ["who_aqg_2021_pm25_guidelines", "eu_air_quality_directive_2024",
                               "lancet_countdown_rcp_projections", "wbgt_iso_7243_standard",
                               "who_country_climate_health_profiles", "vector_disease_climate_models"],
            "quality_indicators": ["health_data_source_quality", "spatial_resolution",
                                   "workforce_exposure_assessment"],
        },
    }

    for module_id, sig in new_signatures.items():
        if module_id not in service_instance._module_signatures:
            service_instance._module_signatures[module_id] = sig

    new_edges = [
        # E56 Climate Litigation
        {"from": "regulatory_report_compiler",     "to": "climate_litigation_engine",   "type": "disclosure_liability_audit"},
        {"from": "sec_climate_engine",             "to": "climate_litigation_engine",   "type": "sec_filer_compliance_gap"},
        {"from": "climate_litigation_engine",      "to": "ecl_engine",                  "type": "litigation_pd_uplift"},
        {"from": "climate_litigation_engine",      "to": "portfolio_analytics",         "type": "legal_risk_exposure_aggregation"},
        {"from": "climate_litigation_engine",      "to": "factor_overlay_engine",       "type": "greenwashing_reputation_factor"},
        # E57 ESG Ratings Reform
        {"from": "csrd_engine",                    "to": "esg_ratings_engine",          "type": "csrd_disclosure_score_input"},
        {"from": "esg_ratings_engine",             "to": "portfolio_analytics",         "type": "composite_esg_rating_overlay"},
        {"from": "esg_ratings_engine",             "to": "regulatory_report_compiler",  "type": "esra_authorisation_reporting"},
        {"from": "esg_ratings_engine",             "to": "factor_overlay_engine",       "type": "divergence_uncertainty_factor"},
        # E58 Methane & Fugitive
        {"from": "carbon_accounting_engine",       "to": "methane_fugitive_engine",     "type": "scope1_methane_extraction"},
        {"from": "methane_fugitive_engine",        "to": "carbon_markets_intel_engine", "type": "methane_credit_abatement"},
        {"from": "methane_fugitive_engine",        "to": "regulatory_report_compiler",  "type": "eu_methane_reg_compliance"},
        {"from": "methane_fugitive_engine",        "to": "portfolio_analytics",         "type": "methane_stranded_asset_risk"},
        # E59 Health-Climate
        {"from": "climate_physical_risk",          "to": "health_climate_engine",       "type": "heat_stress_temperature_hazard"},
        {"from": "health_climate_engine",          "to": "ecl_engine",                  "type": "workforce_productivity_credit_risk"},
        {"from": "health_climate_engine",          "to": "portfolio_analytics",         "type": "health_transition_risk_overlay"},
    ]

    existing_edge_keys = {(e.get("from"), e.get("to")) for e in service_instance._dependencies}
    for edge in new_edges:
        key = (edge.get("from"), edge.get("to"))
        if key not in existing_edge_keys:
            service_instance._dependencies.append(edge)
            existing_edge_keys.add(key)


def _register_e60_e63_modules(service_instance) -> None:
    """Register E60-E63 engines in the data lineage graph."""
    new_signatures = {
        "maritime_engine": {
            "label": "Maritime & Shipping Decarbonisation Engine",
            "category": "sector_specific",
            "inputs": ["entity_id", "ship_type", "gross_tonnage", "deadweight_tonnes",
                       "annual_fuel_consumption_t", "annual_distance_nm", "fuel_type",
                       "build_year", "eu_route_share_pct", "installed_power_kw"],
            "outputs": ["cii_attained", "cii_required", "cii_rating", "eexi_attained",
                        "eexi_compliant", "eu_ets_allowances_required", "eu_ets_cost_eur",
                        "fueleu_ghg_intensity", "fueleu_compliant", "fueleu_penalty_eur",
                        "stranding_year", "retrofit_cost_usd", "overall_risk_score", "risk_rating"],
            "reference_data": ["imo_ghg_strategy_2023", "marpol_annex_vi_cii_eexi",
                               "eu_ets_regulation_2023_957", "fueleu_maritime_2023_1805",
                               "iea_alternative_fuels_shipping"],
            "quality_indicators": ["fuel_consumption_measurement_method", "voyage_data_completeness",
                                   "eu_mrv_report_status"],
        },
        "hydrogen_economy_engine": {
            "label": "Hydrogen Economy Finance Engine",
            "category": "energy_transition",
            "inputs": ["entity_id", "h2_colour", "production_pathway", "capacity_mw_el",
                       "country_code", "capacity_factor_pct", "financing_cost_pct",
                       "demand_sector", "annual_h2_demand_t", "re_source"],
            "outputs": ["lcoh_usd_kg", "ghg_intensity_kgco2e_kgh2", "rfnbo_compliant",
                        "eu_taxonomy_eligible", "eu_h2_bank_eligible", "subsidy_eur_kg",
                        "abatement_tco2_pa", "break_even_carbon_price", "project_irr_pct",
                        "lcoh_2030", "lcoh_2040", "lcoh_2050", "grid_parity_year"],
            "reference_data": ["eu_hydrogen_strategy_2020", "rfnbo_delegated_act_2023_1184",
                               "eu_h2_bank_innovation_fund", "iea_global_h2_review_2023",
                               "bloombergnef_h2_outlook"],
            "quality_indicators": ["electricity_source_verification", "capacity_factor_monitoring",
                                   "rfnbo_additionality_proof"],
        },
        "just_transition_engine": {
            "label": "Just Transition & Social Risk Finance Engine",
            "category": "social",
            "inputs": ["entity_id", "region_name", "country_code", "sector", "fossil_employment",
                       "total_employment", "fiscal_dependency_pct", "policy_score",
                       "social_dialogue_score", "worker_protection_score", "affected_workers",
                       "avg_wage_usd", "face_value_usd", "issuer_type"],
            "outputs": ["employment_concentration_pct", "fiscal_vulnerability_score",
                        "ilo_overall_score", "ilo_compliance_level", "retraining_cost_usd",
                        "total_social_cost_usd", "jt_bond_icma_score", "eu_social_taxonomy_eligible",
                        "jetp_alignment_score", "vulnerability_rating", "greenium_bps"],
            "reference_data": ["ilo_just_transition_guidelines_2015", "eu_jtm_regulation_2021_1056",
                               "icma_social_bond_principles_2023", "world_bank_jt_framework_2022",
                               "cop26_jetp_pledges"],
            "quality_indicators": ["employment_data_source", "fiscal_data_completeness",
                                   "stakeholder_consultation_coverage"],
        },
        "cdr_engine": {
            "label": "Carbon Removal & CDR Finance Engine",
            "category": "carbon_markets",
            "inputs": ["entity_id", "cdr_method", "annual_removal_tco2", "permanence_yrs",
                       "verification_standard", "additionality_score", "leakage_risk_pct",
                       "capex_usd", "opex_usd_pa", "lifetime_yrs", "discount_rate_pct",
                       "scope1_sbti_aligned", "residual_emissions_tco2", "host_country_code"],
            "outputs": ["bezero_rating", "quality_score", "permanence_rating", "net_credits_tco2",
                        "lcor_usd_tco2", "project_irr_pct", "oxford_alignment_score",
                        "article_6_4_eligible", "corresponding_adjustment", "vcmi_claims_level",
                        "vcmi_claims_eligible", "overall_cdr_quality_score"],
            "reference_data": ["ipcc_ar6_cdr_taxonomy", "bezero_carbon_rating_methodology",
                               "oxford_principles_net_zero_2024", "vcmi_claims_code_2023",
                               "paris_agreement_article_6_4", "puro_earth_standards",
                               "isometric_verification_framework"],
            "quality_indicators": ["measurement_verification_tier", "permanence_monitoring_protocol",
                                   "third_party_audit_frequency"],
        },
    }

    for module_id, sig in new_signatures.items():
        if module_id not in service_instance._module_signatures:
            service_instance._module_signatures[module_id] = sig

    new_edges = [
        # E60 Maritime
        {"from": "climate_transition_risk",        "to": "maritime_engine",             "type": "carbon_price_fuel_cost_impact"},
        {"from": "factor_overlay_engine",          "to": "maritime_engine",             "type": "sector_decarbonisation_factor"},
        {"from": "maritime_engine",                "to": "ecl_engine",                  "type": "cii_rating_pd_adjustment"},
        {"from": "maritime_engine",                "to": "portfolio_analytics",         "type": "shipping_stranding_exposure"},
        {"from": "maritime_engine",                "to": "regulatory_report_compiler",  "type": "eu_ets_mrv_disclosure"},
        # E61 Hydrogen
        {"from": "climate_transition_risk",        "to": "hydrogen_economy_engine",     "type": "carbon_price_green_premium"},
        {"from": "sovereign_climate_risk_engine",  "to": "hydrogen_economy_engine",     "type": "country_energy_independence"},
        {"from": "hydrogen_economy_engine",        "to": "portfolio_analytics",         "type": "h2_project_irr_overlay"},
        {"from": "hydrogen_economy_engine",        "to": "factor_overlay_engine",       "type": "h2_blending_economics_factor"},
        {"from": "hydrogen_economy_engine",        "to": "methane_fugitive_engine",     "type": "blue_h2_upstream_methane"},
        # E62 Just Transition
        {"from": "climate_transition_risk",        "to": "just_transition_engine",      "type": "fossil_asset_retirement_timeline"},
        {"from": "sovereign_climate_risk_engine",  "to": "just_transition_engine",      "type": "country_fiscal_resilience"},
        {"from": "just_transition_engine",         "to": "ecl_engine",                  "type": "social_unrest_credit_risk"},
        {"from": "just_transition_engine",         "to": "portfolio_analytics",         "type": "jt_bond_impact_overlay"},
        {"from": "just_transition_engine",         "to": "regulatory_report_compiler",  "type": "csrd_s1_workforce_disclosure"},
        # E63 CDR
        {"from": "nature_based_solutions_engine",  "to": "cdr_engine",                  "type": "nbs_credit_quality_input"},
        {"from": "carbon_markets_intel_engine",    "to": "cdr_engine",                  "type": "credit_price_benchmarks"},
        {"from": "cdr_engine",                     "to": "portfolio_analytics",         "type": "net_zero_residual_offset"},
        {"from": "cdr_engine",                     "to": "regulatory_report_compiler",  "type": "vcmi_claims_disclosure"},
        {"from": "cdr_engine",                     "to": "factor_overlay_engine",       "type": "cdr_quality_credit_factor"},
    ]

    existing_edge_keys = {(e.get("from"), e.get("to")) for e in service_instance._dependencies}
    for edge in new_edges:
        key = (edge.get("from"), edge.get("to"))
        if key not in existing_edge_keys:
            service_instance._dependencies.append(edge)
            existing_edge_keys.add(key)


def _register_e64_e67_modules(service_instance) -> None:
    """Register E64-E67 engines in the data lineage graph."""
    new_signatures = {
        "transition_finance_engine": {
            "label": "Transition Finance Alignment Engine",
            "category": "regulatory",
            "inputs": ["entity_id", "sector", "revenue_usd", "scope1_tco2e", "scope2_tco2e",
                       "scope3_tco2e", "has_transition_plan", "net_zero_target_year",
                       "near_term_sbti", "long_term_sbti", "strategy_score", "governance_score",
                       "capex_alignment_pct", "pacta_technology_mix"],
            "outputs": ["gfanz_category", "gfanz_score", "sbti_nz_status", "sbti_nz_score",
                        "tpt_disclosure_level", "tpt_overall_score", "ca100_composite",
                        "pacta_score", "pacta_alignment_2030", "transition_capex_gap_usd",
                        "overall_alignment_score", "overall_rating", "financing_eligibility"],
            "reference_data": ["gfanz_transition_finance_recs_2023", "sbti_nz_standard_v1_2",
                               "tpt_disclosure_framework_2023", "ca100_nz_benchmark_v2",
                               "pacta_methodology_2022", "eu_green_bond_standard_2023"],
            "quality_indicators": ["transition_plan_completeness", "target_validation_status",
                                   "capital_allocation_disclosure"],
        },
        "biodiversity_credits_engine": {
            "label": "Biodiversity Credits & Nature Markets Engine",
            "category": "nature",
            "inputs": ["entity_id", "habitat_type", "area_ha", "baseline_condition",
                       "post_condition", "country_code", "sector", "freshwater_pressures",
                       "land_footprint_ha", "ecosystem_type"],
            "outputs": ["bng_net_gain_units", "bng_net_gain_pct", "bng_compliant_10pct",
                        "sbtn_overall", "sbtn_compliance_level", "eu_nrl_compliance_score",
                        "tnfd_msa_score", "tnfd_hii_score", "credit_value_usd",
                        "market_liquidity", "overall_biodiversity_score"],
            "reference_data": ["uk_bng_environment_act_2021", "defra_metric_4_0",
                               "eu_nrl_2024_1991", "sbtn_v1_1_targets",
                               "tnfd_leap_v1_advanced_metrics", "iucn_red_list_ecosystems"],
            "quality_indicators": ["habitat_survey_recency", "condition_assessment_method",
                                   "sbtn_data_coverage"],
        },
        "climate_stress_test_engine": {
            "label": "Climate Stress Testing Engine",
            "category": "risk_management",
            "inputs": ["entity_id", "institution_type", "framework", "scenario",
                       "portfolio_sectors", "total_assets_usd", "cet1_ratio_pct",
                       "uk_mortgage_exposure_pct", "eu_sector_exposures", "time_horizon"],
            "outputs": ["bcbs_climate_var_pct", "bcbs_credit_loss_pct", "boe_physical_loss_pct",
                        "boe_transition_loss_pct", "ecb_cet1_impact_ppts", "ecb_npe_impact",
                        "apra_capital_impact_ppts", "total_portfolio_loss_pct",
                        "capital_adequacy_post_pct", "stress_test_passed",
                        "overall_resilience_score", "remediation_capital_usd"],
            "reference_data": ["bcbs_517_principles_2022", "boe_cbes_2021_scenarios",
                               "ecb_climate_stress_test_2022", "apra_cpg229_2023",
                               "fed_pilot_csa_2023", "ngfs_phase4_scenarios_2023"],
            "quality_indicators": ["scenario_coverage_count", "time_horizon_adequacy",
                                   "model_validation_status"],
        },
        "scope3_analytics_engine": {
            "label": "Scope 3 Deep-Dive Analytics Engine",
            "category": "emissions",
            "inputs": ["entity_id", "sector", "reported_categories", "total_scope3_tco2e",
                       "scope12_total_tco2e", "category_inputs", "supplier_engagement_pct",
                       "downstream_coverage_pct", "flag_tco2e", "product_type",
                       "category_methods"],
            "outputs": ["categories_covered", "material_categories_missing", "coverage_score",
                        "total_scope3_tco2e_calculated", "flag_tco2e", "scope3_intensity",
                        "dqs_by_category", "weighted_dqs", "sbti_scope3_compliant",
                        "engagement_target_met", "avoided_emissions_tco2e",
                        "double_counting_risk_pairs", "completeness_rating"],
            "reference_data": ["ghg_protocol_scope3_standard_2011", "ghg_protocol_technical_guidance_2013",
                               "pcaf_standard_part_a_cat15", "sbti_scope3_guidance_2022",
                               "flag_guidance_2023", "ghg_protocol_avoided_emissions_2023"],
            "quality_indicators": ["category_15_coverage_pct", "supplier_data_share_pct",
                                   "third_party_verification_scope"],
        },
    }

    for module_id, sig in new_signatures.items():
        if module_id not in service_instance._module_signatures:
            service_instance._module_signatures[module_id] = sig

    new_edges = [
        # E64 Transition Finance
        {"from": "csrd_engine",                    "to": "transition_finance_engine",   "type": "csrd_transition_plan_input"},
        {"from": "climate_transition_risk",        "to": "transition_finance_engine",   "type": "sector_decarbonisation_pathway"},
        {"from": "carbon_accounting_engine",       "to": "transition_finance_engine",   "type": "scope_1_2_3_baseline"},
        {"from": "transition_finance_engine",      "to": "portfolio_analytics",         "type": "gfanz_portfolio_classification"},
        {"from": "transition_finance_engine",      "to": "ecl_engine",                  "type": "transition_alignment_pd_overlay"},
        {"from": "transition_finance_engine",      "to": "regulatory_report_compiler",  "type": "tpt_ca100_disclosure"},
        # E65 Biodiversity Credits
        {"from": "nature_based_solutions_engine",  "to": "biodiversity_credits_engine", "type": "nbs_habitat_quality_input"},
        {"from": "biodiversity_finance_v2_engine", "to": "biodiversity_credits_engine", "type": "tnfd_dependency_score"},
        {"from": "biodiversity_credits_engine",    "to": "portfolio_analytics",         "type": "biodiversity_credit_valuation"},
        {"from": "biodiversity_credits_engine",    "to": "regulatory_report_compiler",  "type": "eu_nrl_sbtn_disclosure"},
        {"from": "biodiversity_credits_engine",    "to": "factor_overlay_engine",       "type": "biodiversity_premium_factor"},
        # E66 Climate Stress Testing
        {"from": "climate_physical_risk",          "to": "climate_stress_test_engine",  "type": "physical_hazard_damage_function"},
        {"from": "climate_transition_risk",        "to": "climate_stress_test_engine",  "type": "transition_scenario_input"},
        {"from": "sovereign_climate_risk_engine",  "to": "climate_stress_test_engine",  "type": "country_climate_risk_proxy"},
        {"from": "climate_stress_test_engine",     "to": "ecl_engine",                  "type": "stress_test_pd_lgd_override"},
        {"from": "climate_stress_test_engine",     "to": "portfolio_analytics",         "type": "capital_adequacy_post_stress"},
        {"from": "climate_stress_test_engine",     "to": "regulatory_report_compiler",  "type": "bcbs_boe_ecb_disclosure"},
        # E67 Scope 3
        {"from": "carbon_accounting_engine",       "to": "scope3_analytics_engine",     "type": "scope_1_2_baseline_for_ratio"},
        {"from": "food_system_engine",             "to": "scope3_analytics_engine",     "type": "flag_cat1_emission_factors"},
        {"from": "supply_chain_engine",            "to": "scope3_analytics_engine",     "type": "cat1_supplier_data"},
        {"from": "scope3_analytics_engine",        "to": "portfolio_analytics",         "type": "scope3_financed_emissions"},
        {"from": "scope3_analytics_engine",        "to": "regulatory_report_compiler",  "type": "ghg_protocol_scope3_report"},
        {"from": "scope3_analytics_engine",        "to": "transition_finance_engine",   "type": "scope3_sbti_target_input"},
    ]

    existing_edge_keys = {(e.get("from"), e.get("to")) for e in service_instance._dependencies}
    for edge in new_edges:
        key = (edge.get("from"), edge.get("to"))
        if key not in existing_edge_keys:
            service_instance._dependencies.append(edge)
            existing_edge_keys.add(key)


def _register_e68_e71_modules(service_instance) -> None:
    """Register E68-E71 engines: Blue Economy, Sovereign Debt Climate, Loss & Damage, Carbon Price ETS."""
    new_signatures = {
        "blue_economy_engine": {
            "inputs": ["ocean_risk_data", "blue_carbon_projects", "bond_terms", "sovereign_profiles"],
            "outputs": ["blue_bond_alignment", "blue_carbon_sequestration", "ocean_acidification_score",
                        "bbnj_compliance", "sof_score", "ocean_economy_exposure"],
            "reference_data": ["icma_blue_bond_principles_2023", "oecd_ocean_finance", "ipcc_ar6_ocean",
                                "bbnj_high_seas_treaty_2023", "unep_fi_sof"],
            "description": "ICMA Blue Bond Principles 2023, Sustainable Ocean Finance, Blue Carbon (mangroves/seagrass/saltmarsh), High Seas Treaty BBNJ 2023",
        },
        "sovereign_debt_climate_engine": {
            "inputs": ["sovereign_profiles", "debt_terms", "climate_vulnerability", "macro_data"],
            "outputs": ["crdc_eligibility", "dfn_swap_value", "imf_rst_score", "sids_vulnerability",
                        "catastrophe_deferred_amount", "climate_debt_relief_score"],
            "reference_data": ["imf_resilience_sustainability_trust", "paris_club_mou", "v20_sids_list",
                                "world_bank_climate_debt_framework", "crdc_term_sheet"],
            "description": "Climate Resilience Debt Clauses, Debt-for-Nature Swaps, IMF RST, Paris Club, SIDS Vulnerability Index",
        },
        "loss_damage_finance_engine": {
            "inputs": ["country_vulnerability", "loss_event_data", "parametric_triggers", "insurance_coverage"],
            "outputs": ["frld_eligibility", "wim_access_score", "global_shield_allocation",
                        "v20_allocation", "parametric_payout", "residual_ld_gap"],
            "reference_data": ["cop28_frld_framework", "wim_santiago_network", "global_shield_v2",
                                "v20_vulnerable_group", "warsaw_international_mechanism"],
            "description": "COP28 Fund for Response to Loss & Damage, WIM Santiago Network, Global Shield v2, V20 Vulnerable Group, Parametric Triggers",
        },
        "carbon_price_ets_engine": {
            "inputs": ["sector_emissions", "ets_registry", "policy_scenarios", "cbam_exposure"],
            "outputs": ["eu_ets_price_forecast", "uk_ets_price", "california_allowance_price",
                        "china_ets_compliance_cost", "rggi_price", "cross_border_leakage_risk",
                        "cbam_cost", "carbon_price_portfolio_impact"],
            "reference_data": ["eu_ets_phase4_lrf", "uk_ets_cap_trajectory", "california_scoping_plan",
                                "china_ets_mrvp", "iea_sds_aps_carbon_price", "rggi_model_rule"],
            "description": "EU ETS Phase 4 (LRF 4.3%), UK ETS, California Cap-and-Trade, China ETS 8 sectors, RGGI, Korea ETS, IEA SDS/APS pathways",
        },
    }
    for mod_id, sig in new_signatures.items():
        if mod_id not in service_instance._module_registry:
            service_instance._module_registry[mod_id] = sig

    new_edges = [
        # Blue Economy (E68) — inbound
        {"from": "nature_risk_engine", "to": "blue_economy_engine",
         "fields": ["biodiversity_score", "habitat_quality"], "type": "risk_feed"},
        {"from": "carbon_markets_intel", "to": "blue_economy_engine",
         "fields": ["blue_carbon_credits", "article6_eligibility"], "type": "credit_feed"},
        # Blue Economy (E68) — outbound
        {"from": "blue_economy_engine", "to": "portfolio_analytics_engine",
         "fields": ["sof_score", "blue_bond_alignment"], "type": "portfolio_integration"},
        {"from": "blue_economy_engine", "to": "regulatory_report_compiler",
         "fields": ["bbnj_compliance", "icma_alignment"], "type": "disclosure_feed"},
        {"from": "blue_economy_engine", "to": "factor_overlay_engine",
         "fields": ["ocean_acidification_score", "blue_carbon_sequestration"], "type": "factor_update"},

        # Sovereign Debt Climate (E69) — inbound
        {"from": "sovereign_climate_risk_engine", "to": "sovereign_debt_climate_engine",
         "fields": ["composite_score", "rating_notch_adj", "climate_spread_delta"], "type": "risk_feed"},
        {"from": "climate_transition_engine", "to": "sovereign_debt_climate_engine",
         "fields": ["transition_cost", "ndc_ambition"], "type": "scenario_feed"},
        # Sovereign Debt Climate (E69) — outbound
        {"from": "sovereign_debt_climate_engine", "to": "portfolio_analytics_engine",
         "fields": ["crdc_eligibility", "dfn_swap_value"], "type": "portfolio_integration"},
        {"from": "sovereign_debt_climate_engine", "to": "ecl_engine",
         "fields": ["climate_debt_relief_score", "sids_vulnerability"], "type": "pd_adjustment"},

        # Loss & Damage Finance (E70) — inbound
        {"from": "climate_physical_risk_engine", "to": "loss_damage_finance_engine",
         "fields": ["hazard_intensity", "exposure_value"], "type": "hazard_feed"},
        {"from": "sovereign_debt_climate_engine", "to": "loss_damage_finance_engine",
         "fields": ["sids_vulnerability", "climate_debt_relief_score"], "type": "vulnerability_feed"},
        # Loss & Damage Finance (E70) — outbound
        {"from": "loss_damage_finance_engine", "to": "portfolio_analytics_engine",
         "fields": ["residual_ld_gap", "v20_allocation"], "type": "risk_integration"},
        {"from": "loss_damage_finance_engine", "to": "regulatory_report_compiler",
         "fields": ["frld_eligibility", "wim_access_score"], "type": "disclosure_feed"},

        # Carbon Price ETS (E71) — inbound
        {"from": "carbon_accounting_engine", "to": "carbon_price_ets_engine",
         "fields": ["scope1_emissions", "scope2_emissions", "cbam_exposure"], "type": "emissions_feed"},
        {"from": "climate_transition_engine", "to": "carbon_price_ets_engine",
         "fields": ["policy_scenario", "carbon_price_pathway"], "type": "scenario_feed"},
        {"from": "cbam_calculator", "to": "carbon_price_ets_engine",
         "fields": ["cbam_cost", "embedded_carbon"], "type": "cost_feed"},
        # Carbon Price ETS (E71) — outbound
        {"from": "carbon_price_ets_engine", "to": "portfolio_analytics_engine",
         "fields": ["carbon_price_portfolio_impact", "eu_ets_price_forecast"], "type": "portfolio_integration"},
        {"from": "carbon_price_ets_engine", "to": "ecl_engine",
         "fields": ["carbon_cost_stress", "cross_border_leakage_risk"], "type": "pd_adjustment"},
        {"from": "carbon_price_ets_engine", "to": "regulatory_report_compiler",
         "fields": ["ets_compliance_cost", "cbam_cost"], "type": "disclosure_feed"},
        {"from": "carbon_price_ets_engine", "to": "factor_overlay_engine",
         "fields": ["eu_ets_price_forecast", "carbon_price_portfolio_impact"], "type": "factor_update"},
    ]

    existing_edge_keys = {(e.get("from"), e.get("to")) for e in service_instance._dependencies}
    for edge in new_edges:
        key = (edge.get("from"), edge.get("to"))
        if key not in existing_edge_keys:
            service_instance._dependencies.append(edge)
            existing_edge_keys.add(key)


def _register_e76_e79_sprint29_modules(service_instance) -> None:
    new_signatures = {
        "ai_risk_engine": {
            "module_id": "ai_risk_engine", "name": "AI & ML Risk Finance",
            "version": "1.0", "regulatory_frameworks": ["EU_AI_Act_2024", "NIST_AI_RMF", "GDPR_Art22", "EU_AI_Liability_Directive"],
            "input_data_types": ["ai_system_metadata", "model_performance", "harm_scenarios"],
            "output_data_types": ["risk_category", "bias_scores", "liability_exposure"],
            "quality_score": 0.88, "completeness": 0.86
        },
        "nature_capital_engine": {
            "module_id": "nature_capital_engine", "name": "Nature Capital Accounting",
            "version": "1.0", "regulatory_frameworks": ["SEEA_EA_2021", "TNFD_v1", "CSRD_ESRS_E4", "CBD_GBF"],
            "input_data_types": ["ecosystem_data", "extent_condition", "service_flows"],
            "output_data_types": ["natural_capital_value", "dependency_scores", "balance_sheet"],
            "quality_score": 0.87, "completeness": 0.85
        },
        "climate_finance_engine": {
            "module_id": "climate_finance_engine", "name": "Climate Finance Flows Tracking",
            "version": "1.0", "regulatory_frameworks": ["UNFCCC_Art21c", "OECD_CRS", "CPI_Methodology", "NCQG_COP29"],
            "input_data_types": ["financial_flows", "instrument_data", "recipient_data"],
            "output_data_types": ["climate_finance_tracking", "ncqg_contribution", "mobilisation_metrics"],
            "quality_score": 0.89, "completeness": 0.87
        },
        "esg_ma_engine": {
            "module_id": "esg_ma_engine", "name": "ESG M&A Due Diligence",
            "version": "1.0", "regulatory_frameworks": ["UNGP_31", "CSDDD_Art3", "OECD_RBC", "SFDR", "EU_Taxonomy"],
            "input_data_types": ["deal_data", "target_profiles", "esg_findings"],
            "output_data_types": ["dd_report", "valuation_adjustment", "integration_plan"],
            "quality_score": 0.90, "completeness": 0.88
        },
    }
    new_edges = [
        # E76 AI Risk
        {"from": "esg_data_quality", "to": "ai_risk_engine", "type": "feeds", "strength": 0.8},
        {"from": "regulatory_penalties", "to": "ai_risk_engine", "type": "feeds", "strength": 0.7},
        {"from": "ai_risk_engine", "to": "portfolio_analytics", "type": "enriches", "strength": 0.7},
        {"from": "ai_risk_engine", "to": "regulatory_report_compiler", "type": "feeds", "strength": 0.8},
        {"from": "ai_risk_engine", "to": "factor_overlay_engine", "type": "feeds", "strength": 0.6},
        # E77 Nature Capital
        {"from": "nature_risk", "to": "nature_capital_engine", "type": "feeds", "strength": 0.9},
        {"from": "biodiversity_finance_v2", "to": "nature_capital_engine", "type": "feeds", "strength": 0.9},
        {"from": "nature_capital_engine", "to": "portfolio_analytics", "type": "enriches", "strength": 0.8},
        {"from": "nature_capital_engine", "to": "regulatory_report_compiler", "type": "feeds", "strength": 0.8},
        {"from": "nature_capital_engine", "to": "real_estate_valuation", "type": "enriches", "strength": 0.7},
        # E78 Climate Finance
        {"from": "portfolio_analytics", "to": "climate_finance_engine", "type": "feeds", "strength": 0.8},
        {"from": "blended_finance_engine", "to": "climate_finance_engine", "type": "feeds", "strength": 0.8},
        {"from": "sovereign_climate_risk", "to": "climate_finance_engine", "type": "feeds", "strength": 0.7},
        {"from": "climate_finance_engine", "to": "regulatory_report_compiler", "type": "feeds", "strength": 0.9},
        {"from": "climate_finance_engine", "to": "portfolio_analytics", "type": "enriches", "strength": 0.7},
        # E79 ESG M&A
        {"from": "supply_chain_engine", "to": "esg_ma_engine", "type": "feeds", "strength": 0.8},
        {"from": "csddd_engine", "to": "esg_ma_engine", "type": "feeds", "strength": 0.9},
        {"from": "climate_transition_engine", "to": "esg_ma_engine", "type": "feeds", "strength": 0.8},
        {"from": "esg_ma_engine", "to": "portfolio_analytics", "type": "enriches", "strength": 0.8},
        {"from": "esg_ma_engine", "to": "regulatory_report_compiler", "type": "feeds", "strength": 0.8},
        {"from": "esg_ma_engine", "to": "factor_overlay_engine", "type": "feeds", "strength": 0.6},
    ]
    for module_id, sig in new_signatures.items():
        if module_id not in service_instance._module_signatures:
            service_instance._module_signatures[module_id] = sig
    existing_edge_keys = {(e.get("from"), e.get("to")) for e in service_instance._dependencies}
    for edge in new_edges:
        key = (edge.get("from"), edge.get("to"))
        if key not in existing_edge_keys:
            service_instance._dependencies.append(edge)
            existing_edge_keys.add(key)


def _register_e72_e75_modules(service_instance) -> None:
    """Register E72-E75 engines in the data lineage graph."""
    new_signatures = {
        "blended_finance_engine": {
            "module_id": "blended_finance_engine", "name": "Blended Finance & DFI",
            "version": "1.0", "regulatory_frameworks": ["IFC_PS", "OECD_DAC", "Convergence", "MIGA", "EBRD"],
            "input_data_types": ["project_data", "sector_profiles", "country_risk"],
            "output_data_types": ["blended_structure", "mobilisation_metrics", "dfi_scores"],
            "quality_score": 0.87, "completeness": 0.85,
            # legacy fields retained for compatibility
            "label": "Blended Finance & DFI Engine",
            "category": "development_finance",
            "inputs": ["entity_id", "instrument_type", "project_size_usd", "sector", "country"],
            "outputs": ["concessional_layer", "mobilisation_ratio", "dfi_standards_score", "ifc_ps_compliance"],
            "reference_data": ["convergence_2023_benchmarks", "oecd_dac_blended_finance_2023",
                                "ifc_performance_standards_8", "dfi_provider_profiles_6"],
            "quality_indicators": ["mobilisation_ratio", "dfi_standards_score"],
        },
        "mrv_engine": {
            "module_id": "mrv_engine", "name": "Climate Data & MRV Infrastructure",
            "version": "1.0", "regulatory_frameworks": ["ISO_14064_3", "IPCC_AR6", "CDP_CDSB", "ISAE_3410", "ISSA_5000"],
            "input_data_types": ["facility_data", "emission_sources", "satellite_data"],
            "output_data_types": ["mrv_tiers", "data_quality_scores", "verification_readiness"],
            "quality_score": 0.91, "completeness": 0.89,
            # legacy fields
            "label": "Climate Data & MRV Engine",
            "category": "emissions",
            "inputs": ["entity_id", "facility_type", "current_capabilities", "emission_sources", "lat", "lng"],
            "outputs": ["mrv_tier", "uncertainty_pct", "dqs_score", "verification_readiness", "ai_quality_score"],
            "reference_data": ["iso_14064_3_2019", "ipcc_uncertainty_tiers", "cdp_cdsb_2022",
                                "satellite_platforms_4", "mrv_tiers_5"],
            "quality_indicators": ["dqs_score", "ai_quality_score", "mrv_tier"],
        },
        "real_asset_decarb_engine": {
            "module_id": "real_asset_decarb_engine", "name": "Real Asset Decarbonisation",
            "version": "1.0", "regulatory_frameworks": ["CRREM_2", "SBTi", "TCFD", "IFRS_S2", "EU_Taxonomy"],
            "input_data_types": ["asset_data", "energy_data", "capex_plans"],
            "output_data_types": ["lock_in_risk", "capex_roadmap", "retrofit_npv", "decarb_trajectory"],
            "quality_score": 0.88, "completeness": 0.86,
            # legacy fields
            "label": "Real Asset Decarbonisation Engine",
            "category": "climate_transition",
            "inputs": ["entity_id", "asset_type", "age_years", "current_intensity", "budget_usd"],
            "outputs": ["lock_in_risk_score", "stranded_cost_usd", "retrofit_npv", "capex_stack"],
            "reference_data": ["crrem_2_pathways", "sbti_sector_rates", "carbon_price_scenarios",
                                "retrofit_measure_library", "capex_abatement_technologies"],
            "quality_indicators": ["lock_in_risk_score", "crrem_alignment"],
        },
        "trade_finance_esg_engine": {
            "module_id": "trade_finance_esg_engine", "name": "Sustainable Trade Finance",
            "version": "1.0", "regulatory_frameworks": ["EP4", "OECD_Arrangement", "ICC_STF_2022", "IFC_PS", "GHG_Protocol"],
            "input_data_types": ["trade_data", "supplier_profiles", "project_data"],
            "output_data_types": ["ep4_assessment", "eca_scores", "supply_chain_esg", "trade_emissions"],
            "quality_score": 0.86, "completeness": 0.84,
            # legacy fields
            "label": "Sustainable Trade Finance Engine",
            "category": "trade_finance",
            "inputs": ["entity_id", "project_type", "project_cost_usd", "suppliers", "trade_lanes"],
            "outputs": ["ep4_category", "ep4_score", "eca_tier", "esg_tier", "scope3_cat1_tco2e", "scope3_cat4_tco2e"],
            "reference_data": ["equator_principles_4_2020", "oecd_arrangement_2023",
                                "icc_stf_principles_2022", "transport_emission_factors", "product_ghg_intensity"],
            "quality_indicators": ["ep4_score", "esg_tier", "icc_stf_score"],
        },
        # alias for legacy references to climate_mrv_engine module name
        "climate_mrv_engine": {
            "label": "Climate Data & MRV Engine",
            "category": "emissions",
            "inputs": [
                "entity_id", "facility_name", "sector", "mrv_system_type",
                "annual_emissions_tco2e", "lat", "lng", "facility_type",
                "data_sources", "current_systems",
            ],
            "outputs": [
                "iso14064_level", "data_quality_score", "accuracy_pct",
                "completeness_pct", "timeliness_score", "digital_mrv_maturity",
                "verification_readiness", "pcaf_dqs", "confidence_weight",
                "ipcc_tier", "uncertainty_pct", "tropomi_detection_probability_pct",
                "ghgsat_point_source_resolution_m", "overall_satellite_coverage_score",
                "cdp_submission_status", "upgrade_roadmap", "estimated_cost_usd",
            ],
            "reference_data": [
                "iso_14064_3_2019_checklist_12", "satellite_systems_5",
                "pcaf_dqs_5_levels", "mrv_system_types_6", "maturity_levels_5",
                "sector_emission_factors_8", "emas_reg_1221_2009",
                "uk_secr_si_2018_1155", "eu_ets_mrv_reg_2018_2066",
            ],
            "quality_indicators": [
                "data_quality_score", "pcaf_dqs", "digital_mrv_maturity",
                "iso14064_level",
            ],
        },
        "real_asset_decarb_engine": {
            "label": "Real Asset Decarbonisation Engine",
            "category": "climate_transition",
            "inputs": [
                "entity_id", "asset_name", "asset_type", "sector",
                "current_emissions", "target_year", "asset_value",
                "remaining_life_years", "carbon_price_scenario",
                "total_capex", "milestones", "current_tech", "target_tech",
            ],
            "outputs": [
                "technology_readiness_level", "abatement_cost_per_tco2e",
                "capex_required_usd", "lock_in_years", "net_zero_pathway",
                "feasibility_score", "iea_nze_benchmark_comparison",
                "stranded_cost_1_5c_usd", "stranded_cost_2c_usd", "stranded_cost_3c_usd",
                "write_down_risk_1_5c_pct", "stranding_year_1_5c", "npv_stranded_assets_usd",
                "irr_of_decarb_investment_pct", "payback_period_years", "green_capex_ratio_pct",
                "gfanz_category", "transition_readiness_score", "technology_substitution_risk",
            ],
            "reference_data": [
                "iea_nze_2050_trajectories_8_sectors", "gfanz_transition_categories_4",
                "technology_pathways_15", "trl_levels_9", "carbon_price_scenarios_3",
                "abatement_cost_curve", "mission_possible_partnership",
                "sbti_flag_criteria",
            ],
            "quality_indicators": [
                "technology_readiness_level", "feasibility_score",
                "green_capex_ratio_pct",
            ],
        },
        "sustainable_trade_finance_engine": {
            "label": "Sustainable Trade Finance Engine",
            "category": "trade_finance",
            "inputs": [
                "entity_id", "project_name", "sector", "country", "total_cost_usd",
                "technology", "oecd_classification", "base_margin_bps",
                "kpis", "performance_data", "commodity", "origin_country",
                "tier1_supplier", "certifications",
            ],
            "outputs": [
                "ep4_category", "overall_score", "esap_requirements",
                "independent_review_required", "compliance_status",
                "environmental_review_score", "sector_sustainability_standard",
                "oecd_common_approaches_tier", "green_classification_tier",
                "adjusted_margin_bps", "margin_adjustment_bps",
                "kpi_results", "spt_calibration", "icc_stf_principles_assessment",
                "eudr_overlay", "modern_slavery_risk", "deforestation_risk",
                "conflict_minerals_risk", "overall_esg_score", "risk_tier",
            ],
            "reference_data": [
                "equator_principles_4_2020", "ifc_performance_standards_8",
                "oecd_common_approaches_2016", "oecd_cre_arrangement_2023",
                "icc_stf_principles_4_2019", "eca_country_risk_ratings_55",
                "commodity_supply_chain_risks_8", "sector_sustainability_standards",
                "eudr_reg_2023_1115", "oecd_due_diligence_guidance_rbc",
            ],
            "quality_indicators": [
                "ep4_compliance_score", "overall_esg_score",
                "eca_green_score", "spt_calibration",
            ],
        },
    }

    for mod_id, sig in new_signatures.items():
        if mod_id not in service_instance._signatures:
            service_instance._signatures[mod_id] = sig
        if hasattr(service_instance, "_module_signatures") and mod_id not in service_instance._module_signatures:
            service_instance._module_signatures[mod_id] = sig

    new_edges = [
        # E72 Blended Finance — inbound
        {"from": "portfolio_analytics_engine_v2",     "to": "blended_finance_engine",
         "fields": ["portfolio_return", "sector_exposures"],        "type": "portfolio_context"},
        {"from": "sovereign_climate_risk_engine",      "to": "blended_finance_engine",
         "fields": ["composite_climate_risk_score", "climate_spread_delta_bps"], "type": "country_risk_input"},
        {"from": "climate_physical_risk_engine",       "to": "blended_finance_engine",
         "fields": ["physical_risk_score", "cvar"],                 "type": "physical_risk_input"},
        # E72 Blended Finance — outbound
        {"from": "blended_finance_engine",             "to": "regulatory_report_compiler",
         "fields": ["mobilisation_ratio", "development_impact_score"], "type": "development_finance_disclosure"},
        {"from": "blended_finance_engine",             "to": "entity360",
         "fields": ["mobilisation_ratio", "additionality_score"],   "type": "blended_finance_enrichment"},

        # E73 Climate MRV — inbound
        {"from": "carbon_accounting_engine",           "to": "climate_mrv_engine",
         "fields": ["scope1_emissions", "scope2_emissions"],         "type": "ghg_baseline_input"},
        {"from": "scope3_analytics_engine",            "to": "climate_mrv_engine",
         "fields": ["scope3_by_category", "weighted_dqs"],          "type": "scope3_quality_input"},
        {"from": "methane_ogmp_engine",                "to": "climate_mrv_engine",
         "fields": ["methane_emissions_tco2e", "tier_level"],       "type": "methane_mrv_input"},
        # E73 Climate MRV — outbound
        {"from": "climate_mrv_engine",                 "to": "regulatory_report_compiler",
         "fields": ["iso14064_level", "data_quality_score"],        "type": "mrv_disclosure"},
        {"from": "climate_mrv_engine",                 "to": "csrd_auto_populate",
         "fields": ["pcaf_dqs", "completeness_pct", "ghg_inventory_summary"], "type": "esrs_e1_mrv_data"},
        {"from": "climate_mrv_engine",                 "to": "assurance_readiness_engine",
         "fields": ["verification_readiness", "iso14064_level"],    "type": "verification_readiness_input"},

        # E74 Real Asset Decarb — inbound
        {"from": "climate_transition_risk_engine",     "to": "real_asset_decarb_engine",
         "fields": ["transition_risk_score", "stranded_asset_score"], "type": "transition_risk_context"},
        {"from": "climate_physical_risk_engine",       "to": "real_asset_decarb_engine",
         "fields": ["physical_risk_score", "physical_cvar_eur"],    "type": "physical_hazard_context"},
        {"from": "scenario_analysis_engine",           "to": "real_asset_decarb_engine",
         "fields": ["carbon_price_scenario", "scenario_results"],   "type": "scenario_pathway_input"},
        # E74 Real Asset Decarb — outbound
        {"from": "real_asset_decarb_engine",           "to": "portfolio_analytics_engine_v2",
         "fields": ["stranded_cost_2c_usd", "green_capex_ratio_pct"], "type": "stranded_risk_portfolio_output"},
        {"from": "real_asset_decarb_engine",           "to": "ecl_climate_engine",
         "fields": ["write_down_risk_2c_pct", "npv_stranded_assets_usd"], "type": "collateral_impairment_input"},
        {"from": "real_asset_decarb_engine",           "to": "regulatory_report_compiler",
         "fields": ["gfanz_category", "net_zero_pathway", "feasibility_score"], "type": "transition_plan_disclosure"},

        # E75 Sustainable Trade Finance — inbound
        {"from": "supply_chain_scope3",                "to": "sustainable_trade_finance_engine",
         "fields": ["supplier_risk_scores", "scope3_by_category"],  "type": "supply_chain_esg_context"},
        {"from": "eudr_engine",                        "to": "sustainable_trade_finance_engine",
         "fields": ["compliance_status", "deforestation_risk"],     "type": "eudr_deforestation_overlay"},
        {"from": "factor_overlay_engine",              "to": "sustainable_trade_finance_engine",
         "fields": ["esg_factors", "geo_factors"],                   "type": "factor_esg_context"},
        # E75 Sustainable Trade Finance — outbound
        {"from": "sustainable_trade_finance_engine",   "to": "portfolio_analytics_engine_v2",
         "fields": ["adjusted_margin_bps", "overall_esg_score"],    "type": "trade_finance_portfolio_output"},
        {"from": "sustainable_trade_finance_engine",   "to": "regulatory_report_compiler",
         "fields": ["ep4_category", "compliance_status"],           "type": "ep4_disclosure"},
        {"from": "sustainable_trade_finance_engine",   "to": "entity360",
         "fields": ["risk_tier", "overall_esg_score", "ep4_category"], "type": "trade_finance_enrichment"},
        # Sprint-28 canonical engine names (mrv_engine / trade_finance_esg_engine)
        {"from": "carbon_accounting", "to": "mrv_engine", "type": "feeds", "strength": 0.9},
        {"from": "nature_risk", "to": "mrv_engine", "type": "feeds", "strength": 0.7},
        {"from": "mrv_engine", "to": "carbon_accounting", "type": "validates", "strength": 0.9},
        {"from": "mrv_engine", "to": "esg_data_quality", "type": "enriches", "strength": 0.8},
        {"from": "mrv_engine", "to": "regulatory_report_compiler", "type": "feeds", "strength": 0.8},
        {"from": "supply_chain_engine", "to": "trade_finance_esg_engine", "type": "feeds", "strength": 0.9},
        {"from": "scope3_analytics_engine", "to": "trade_finance_esg_engine", "type": "feeds", "strength": 0.8},
        {"from": "eudr_engine", "to": "trade_finance_esg_engine", "type": "feeds", "strength": 0.7},
        {"from": "trade_finance_esg_engine", "to": "portfolio_analytics", "type": "enriches", "strength": 0.7},
        {"from": "trade_finance_esg_engine", "to": "regulatory_report_compiler", "type": "feeds", "strength": 0.7},
        {"from": "trade_finance_esg_engine", "to": "blended_finance_engine", "type": "feeds", "strength": 0.6},
    ]

    existing_edge_keys = {(e.get("from"), e.get("to")) for e in service_instance._dependencies}
    for edge in new_edges:
        key = (edge.get("from"), edge.get("to"))
        if key not in existing_edge_keys:
            service_instance._dependencies.append(edge)
            existing_edge_keys.add(key)


def _register_e76_e79_modules(service_instance) -> None:
    """Register E76-E79 dependency edges: Crypto Climate, AI Governance, Carbon Accounting AI, Climate Insurance."""
    new_edges = [
        # E76 Crypto Climate — inbound
        {"from": "carbon_accounting",              "to": "crypto_climate_engine",
         "fields": ["financed_emissions", "pcaf_dqs"],              "type": "pcaf_crypto_context"},
        {"from": "portfolio_analytics_engine_v2",  "to": "crypto_climate_engine",
         "fields": ["portfolio_holdings", "exposure_usd"],          "type": "portfolio_exposure_context"},
        # E76 Crypto Climate — outbound
        {"from": "crypto_climate_engine",          "to": "regulatory_report_compiler",
         "fields": ["mica_compliance_level", "total_tco2e_per_year"], "type": "mica_disclosure"},
        {"from": "crypto_climate_engine",          "to": "portfolio_analytics_engine_v2",
         "fields": ["portfolio_climate_score", "climate_risk_tier"], "type": "crypto_risk_portfolio"},
        {"from": "crypto_climate_engine",          "to": "entity360",
         "fields": ["mica_compliance_level", "ghg_intensity_gco2_per_tx"], "type": "crypto_esg_enrichment"},
        {"from": "crypto_climate_engine",          "to": "factor_overlay_engine",
         "fields": ["climate_risk_tier", "pow_exposure_pct"],       "type": "crypto_factor_overlay"},

        # E77 AI Governance — inbound
        {"from": "double_materiality_engine",      "to": "ai_governance_engine",
         "fields": ["material_topics", "impact_materiality"],       "type": "ai_materiality_context"},
        {"from": "esg_data_quality_engine",        "to": "ai_governance_engine",
         "fields": ["data_quality_score", "coverage_pct"],          "type": "ai_data_quality_input"},
        # E77 AI Governance — outbound
        {"from": "ai_governance_engine",           "to": "regulatory_report_compiler",
         "fields": ["eu_ai_act_risk_tier", "composite_score"],      "type": "eu_ai_act_disclosure"},
        {"from": "ai_governance_engine",           "to": "entity360",
         "fields": ["maturity_tier", "composite_score"],            "type": "ai_esg_enrichment"},
        {"from": "ai_governance_engine",           "to": "factor_overlay_engine",
         "fields": ["eu_ai_act_risk_tier", "total_tco2e_pa"],       "type": "ai_factor_overlay"},

        # E78 Carbon Accounting AI — inbound
        {"from": "carbon_accounting",              "to": "carbon_accounting_ai_engine",
         "fields": ["scope1", "scope2", "scope3_total"],            "type": "ghg_base_data"},
        {"from": "scope3_analytics_engine",        "to": "carbon_accounting_ai_engine",
         "fields": ["category_results", "flag_split"],              "type": "scope3_detail_input"},
        {"from": "esg_data_quality_engine",        "to": "carbon_accounting_ai_engine",
         "fields": ["data_coverage_pct", "dqs_weighted_avg"],       "type": "data_quality_input"},
        # E78 Carbon Accounting AI — outbound
        {"from": "carbon_accounting_ai_engine",    "to": "regulatory_report_compiler",
         "fields": ["ghg_compliance_score", "xbrl_completeness_pct"], "type": "xbrl_disclosure"},
        {"from": "carbon_accounting_ai_engine",    "to": "mrv_engine",
         "fields": ["ef_avg_dqs", "automation_readiness_score"],    "type": "mrv_quality_feedback"},
        {"from": "carbon_accounting_ai_engine",    "to": "entity360",
         "fields": ["ghg_compliance_status", "cdp_climate_score"],  "type": "ghg_ai_enrichment"},

        # E79 Climate Insurance — inbound
        {"from": "climate_physical_risk_engine",   "to": "climate_insurance_engine",
         "fields": ["physical_risk_score", "natcat_aal"],           "type": "natcat_physical_input"},
        {"from": "climate_transition_risk_engine", "to": "climate_insurance_engine",
         "fields": ["transition_risk_score"],                       "type": "transition_liability_input"},
        {"from": "sovereign_climate_risk_engine",  "to": "climate_insurance_engine",
         "fields": ["composite_score", "country_profiles"],         "type": "sovereign_exposure_input"},
        # E79 Climate Insurance — outbound
        {"from": "climate_insurance_engine",       "to": "regulatory_report_compiler",
         "fields": ["iais_score", "orsa_checklist_score"],          "type": "iais_orsa_disclosure"},
        {"from": "climate_insurance_engine",       "to": "portfolio_analytics_engine_v2",
         "fields": ["climate_var_total", "climate_risk_tier"],      "type": "insurance_climate_var"},
        {"from": "climate_insurance_engine",       "to": "ecl_climate_engine",
         "fields": ["protection_gap_pct", "natcat_aal_pct"],        "type": "natcat_loss_feedback"},
        {"from": "climate_insurance_engine",       "to": "factor_overlay_engine",
         "fields": ["climate_risk_tier", "premium_loading_pct"],    "type": "insurance_factor_overlay"},
    ]

    existing_edge_keys = {(e.get("from"), e.get("to")) for e in service_instance._dependencies}
    for edge in new_edges:
        key = (edge.get("from"), edge.get("to"))
        if key not in existing_edge_keys:
            service_instance._dependencies.append(edge)
            existing_edge_keys.add(key)


def _register_e80_e83_modules(service_instance) -> None:
    """Register E80-E83 dependency edges: Corporate Nature Strategy, Green Securitisation, Digital Product Passport, Adaptation Finance."""
    new_edges = [
        # E80 Corporate Nature Strategy — inbound
        {"from": "biodiversity_finance_engine",    "to": "corporate_nature_strategy_engine",
         "fields": ["msa_km2_footprint", "sbtn_readiness"],               "type": "sbtn_nature_input"},
        {"from": "nature_risk_calculator",         "to": "corporate_nature_strategy_engine",
         "fields": ["physical_risk_score", "dependency_score"],           "type": "nature_risk_input"},
        {"from": "eudr_engine",                    "to": "corporate_nature_strategy_engine",
         "fields": ["deforestation_risk", "commodity_exposure"],          "type": "eudr_nature_linkage"},
        {"from": "supply_chain_scope3_engine",     "to": "corporate_nature_strategy_engine",
         "fields": ["land_use_emissions", "biodiversity_impact"],         "type": "supply_chain_nature"},
        # E80 Corporate Nature Strategy — outbound
        {"from": "corporate_nature_strategy_engine", "to": "regulatory_report_compiler",
         "fields": ["tnfd_composite", "nature_strategy_score"],           "type": "tnfd_disclosure"},
        {"from": "corporate_nature_strategy_engine", "to": "csrd_auto_populate",
         "fields": ["step5_disclosure_score", "nrl_exposure_score"],      "type": "esrs_e4_nature_data"},
        {"from": "corporate_nature_strategy_engine", "to": "entity360",
         "fields": ["nature_maturity_tier", "encore_financial_exposure_m"], "type": "nature_strategy_enrichment"},

        # E81 Green Securitisation — inbound
        {"from": "eu_taxonomy_engine",             "to": "green_securitisation_engine",
         "fields": ["taxonomy_alignment_pct", "dnsh_pass"],               "type": "taxonomy_pool_input"},
        {"from": "climate_physical_risk_engine",   "to": "green_securitisation_engine",
         "fields": ["physical_risk_score", "flood_exposure"],             "type": "climate_var_pool_input"},
        {"from": "ecl_climate_engine",             "to": "green_securitisation_engine",
         "fields": ["pd_climate_stressed", "lgd_climate_stressed"],       "type": "credit_quality_pool"},
        {"from": "residential_re_engine",          "to": "green_securitisation_engine",
         "fields": ["epc_distribution", "crrem_aligned_pct"],             "type": "rmbs_epc_input"},
        # E81 Green Securitisation — outbound
        {"from": "green_securitisation_engine",    "to": "portfolio_analytics_engine_v2",
         "fields": ["green_securitisation_score", "greenium_bps"],        "type": "structured_product_risk"},
        {"from": "green_securitisation_engine",    "to": "regulatory_report_compiler",
         "fields": ["eu_gbs_score", "taxonomy_alignment_pct"],            "type": "eu_gbs_disclosure"},
        {"from": "green_securitisation_engine",    "to": "factor_overlay_engine",
         "fields": ["deal_tier", "climate_credit_enhancement"],           "type": "securitisation_factor_overlay"},

        # E82 Digital Product Passport — inbound
        {"from": "carbon_accounting",              "to": "digital_product_passport_engine",
         "fields": ["scope3_total", "product_carbon_footprint"],          "type": "lifecycle_ghg_input"},
        {"from": "supply_chain_scope3_engine",     "to": "digital_product_passport_engine",
         "fields": ["scope3_categories", "tier1_supplier_data"],          "type": "supply_chain_dpp"},
        {"from": "eudr_engine",                    "to": "digital_product_passport_engine",
         "fields": ["commodity_screening", "traceability_score"],         "type": "dpp_traceability"},
        # E82 Digital Product Passport — outbound
        {"from": "digital_product_passport_engine", "to": "regulatory_report_compiler",
         "fields": ["espr_score", "dpp_completeness_pct"],               "type": "espr_disclosure"},
        {"from": "digital_product_passport_engine", "to": "csrd_auto_populate",
         "fields": ["lifecycle_total_tco2e", "circularity_index"],        "type": "esrs_e5_circular_data"},
        {"from": "digital_product_passport_engine", "to": "entity360",
         "fields": ["espr_tier", "carbon_footprint_per_unit"],            "type": "dpp_product_enrichment"},

        # E83 Adaptation Finance — inbound
        {"from": "climate_physical_risk_engine",   "to": "adaptation_finance_engine",
         "fields": ["physical_risk_score", "hazard_profiles"],            "type": "hazard_baseline_input"},
        {"from": "sovereign_climate_risk_engine",  "to": "adaptation_finance_engine",
         "fields": ["adaptation_score", "ndc_ambition"],                  "type": "sovereign_nap_input"},
        {"from": "nature_based_solutions_engine",  "to": "adaptation_finance_engine",
         "fields": ["nbs_effectiveness", "ecosystem_co_benefits"],        "type": "nbs_adaptation_linkage"},
        # E83 Adaptation Finance — outbound
        {"from": "adaptation_finance_engine",      "to": "portfolio_analytics_engine_v2",
         "fields": ["adaptation_score", "bankability_tier"],              "type": "adaptation_portfolio_risk"},
        {"from": "adaptation_finance_engine",      "to": "regulatory_report_compiler",
         "fields": ["gfma_score", "gari_score"],                          "type": "adaptation_finance_disclosure"},
        {"from": "adaptation_finance_engine",      "to": "factor_overlay_engine",
         "fields": ["bankability_tier", "resilience_delta"],              "type": "adaptation_factor_overlay"},
    ]

    existing_edge_keys = {(e.get("from"), e.get("to")) for e in service_instance._dependencies}
    for edge in new_edges:
        key = (edge.get("from"), edge.get("to"))
        if key not in existing_edge_keys:
            service_instance._dependencies.append(edge)
            existing_edge_keys.add(key)


def _register_e84_e87_modules(service_instance) -> None:
    """Register E84-E87 dependency edges: Internal Carbon Pricing, Social Bond, Climate Financial Statements, EM Climate Risk."""
    new_edges = [
        # E84 Internal Carbon Pricing — inbound
        {"from": "carbon_accounting",              "to": "internal_carbon_price_engine",
         "fields": ["scope1_tco2", "scope2_tco2", "scope3_tco2"],           "type": "emissions_icp_input"},
        {"from": "eu_ets_engine",                  "to": "internal_carbon_price_engine",
         "fields": ["ets_price_forecast", "phase4_allocation"],             "type": "ets_shadow_price"},
        {"from": "climate_transition_risk_engine", "to": "internal_carbon_price_engine",
         "fields": ["carbon_price_scenario", "transition_cost_m"],          "type": "transition_icp_linkage"},
        # E84 Internal Carbon Pricing — outbound
        {"from": "internal_carbon_price_engine",   "to": "portfolio_analytics_engine_v2",
         "fields": ["icp_score", "total_carbon_cost_eur"],                  "type": "icp_portfolio_overlay"},
        {"from": "internal_carbon_price_engine",   "to": "regulatory_report_compiler",
         "fields": ["icp_maturity_tier", "sbti_icp_guidance_met"],          "type": "icp_disclosure"},
        {"from": "internal_carbon_price_engine",   "to": "csrd_auto_populate",
         "fields": ["shadow_price_eur_tco2", "carbon_cost_pct_ebitda"],     "type": "esrs_e1_carbon_price"},
        {"from": "internal_carbon_price_engine",   "to": "factor_overlay_engine",
         "fields": ["icp_maturity_tier", "nze_irr_pct"],                    "type": "nze_factor_overlay"},

        # E85 Social Bond — inbound
        {"from": "sustainable_lending_engine",     "to": "social_bond_engine",
         "fields": ["sllp_kpi_score", "impact_metrics"],                    "type": "sll_social_linkage"},
        {"from": "csddd_engine",                   "to": "social_bond_engine",
         "fields": ["adverse_impacts_hr", "value_chain_coverage"],          "type": "social_dd_input"},
        # E85 Social Bond — outbound
        {"from": "social_bond_engine",             "to": "portfolio_analytics_engine_v2",
         "fields": ["sbp_composite_score", "impact_score"],                 "type": "social_bond_portfolio"},
        {"from": "social_bond_engine",             "to": "regulatory_report_compiler",
         "fields": ["sbp_aligned", "bond_tier"],                            "type": "social_bond_disclosure"},
        {"from": "social_bond_engine",             "to": "factor_overlay_engine",
         "fields": ["impact_score", "sdg_alignment"],                       "type": "social_impact_factor"},

        # E86 Climate Financial Statements — inbound
        {"from": "climate_transition_risk_engine", "to": "climate_financial_statements_engine",
         "fields": ["transition_risk_revenue_m", "transition_cost_m"],      "type": "transition_financial_effects"},
        {"from": "climate_physical_risk_engine",   "to": "climate_financial_statements_engine",
         "fields": ["physical_risk_asset_impact_m", "impairment_triggers"], "type": "physical_ias36_input"},
        {"from": "eu_ets_engine",                  "to": "climate_financial_statements_engine",
         "fields": ["ets_compliance_cost", "allowance_deficit"],            "type": "carbon_provision_input"},
        {"from": "stranded_asset_engine",          "to": "climate_financial_statements_engine",
         "fields": ["stranded_asset_exposure_m", "write_down_year"],        "type": "stranded_asset_fs_input"},
        # E86 Climate Financial Statements — outbound
        {"from": "climate_financial_statements_engine", "to": "regulatory_report_compiler",
         "fields": ["ifrs_s2_score", "disclosure_completeness_pct"],        "type": "ifrs_s2_disclosure"},
        {"from": "climate_financial_statements_engine", "to": "entity360",
         "fields": ["climate_financial_risk_score", "materiality_tier"],    "type": "climate_fs_entity_enrichment"},
        {"from": "climate_financial_statements_engine", "to": "csrd_auto_populate",
         "fields": ["climate_adjusted_ebitda_m", "scenario_detail"],        "type": "esrs_e1_financial_effects"},

        # E87 EM Climate Risk — inbound
        {"from": "sovereign_climate_risk_engine",  "to": "em_climate_risk_engine",
         "fields": ["sovereign_risk_score", "ndc_ambition"],                "type": "sovereign_em_input"},
        {"from": "biodiversity_finance_engine",    "to": "em_climate_risk_engine",
         "fields": ["ifc_ps6_score", "critical_habitat_exposure"],          "type": "ps6_em_linkage"},
        {"from": "climate_physical_risk_engine",   "to": "em_climate_risk_engine",
         "fields": ["physical_risk_score", "climate_vulnerability_index"],  "type": "physical_em_risk"},
        # E87 EM Climate Risk — outbound
        {"from": "em_climate_risk_engine",         "to": "portfolio_analytics_engine_v2",
         "fields": ["em_climate_composite", "risk_tier"],                   "type": "em_portfolio_risk"},
        {"from": "em_climate_risk_engine",         "to": "factor_overlay_engine",
         "fields": ["opportunity_tier", "blended_finance_potential"],       "type": "em_concessional_factor"},
        {"from": "em_climate_risk_engine",         "to": "adaptation_finance_engine",
         "fields": ["gcf_allocation_bn", "gems_climate_uplift_pct"],        "type": "em_adaptation_linkage"},
    ]

    existing_edge_keys = {(e.get("from"), e.get("to")) for e in service_instance._dependencies}
    for edge in new_edges:
        key = (edge.get("from"), edge.get("to"))
        if key not in existing_edge_keys:
            service_instance._dependencies.append(edge)
            existing_edge_keys.add(key)


# Auto-register on import if the module-level singleton exists
try:
    from services.data_lineage_service import _default_lineage_service  # noqa
    _register_climate_risk_modules(_default_lineage_service)
    _register_e_series_modules(_default_lineage_service)
    _register_e11_modules(_default_lineage_service)
    _register_e12_e15_modules(_default_lineage_service)
    _register_e16_e19_modules(_default_lineage_service)
    _register_e20_e23_modules(_default_lineage_service)
    _register_e24_e27_modules(_default_lineage_service)
    _register_e28_e31_modules(_default_lineage_service)
    _register_e32_e35_modules(_default_lineage_service)
    _register_e36_e39_modules(_default_lineage_service)
    _register_e40_e43_modules(_default_lineage_service)
    _register_e44_e47_modules(_default_lineage_service)
    _register_e48_e51_modules(_default_lineage_service)
    _register_e52_e55_modules(_default_lineage_service)
    _register_e56_e59_modules(_default_lineage_service)
    _register_e60_e63_modules(_default_lineage_service)
    _register_e64_e67_modules(_default_lineage_service)
    _register_e68_e71_modules(_default_lineage_service)
    _register_e72_e75_modules(_default_lineage_service)
    _register_e76_e79_modules(_default_lineage_service)
    _register_e76_e79_sprint29_modules(_default_lineage_service)
    _register_e80_e83_modules(_default_lineage_service)
    _register_e84_e87_modules(_default_lineage_service)
    _register_e88_e91_modules(_default_lineage_service)
    _register_e92_e95_modules(_default_lineage_service)
    _register_e96_e99_modules(_default_lineage_service)
    _register_e100_e103_modules(_default_lineage_service)
except (ImportError, AttributeError):
    pass  # Will be registered at runtime when service initialises


def _register_e88_e91_modules(service_instance) -> None:
    """Register E88-E91 dependency edges: Biodiversity Credits, Just Transition, Carbon Removal, Climate Litigation."""
    new_edges = [
        # E88 Biodiversity Credits — inbound
        {"from": "biodiversity_finance_engine",    "to": "biodiversity_credit_engine",
         "fields": ["msa_km2_footprint", "sbtn_steps"],                     "type": "biodiversity_credit_input"},
        {"from": "corporate_nature_strategy_engine","to": "biodiversity_credit_engine",
         "fields": ["tnfd_composite", "encore_dependencies"],               "type": "nature_strategy_credit_link"},
        {"from": "nature_risk_engine",             "to": "biodiversity_credit_engine",
         "fields": ["ecosystem_service_values", "habitat_condition"],       "type": "nature_risk_credit_input"},
        # E88 Biodiversity Credits — outbound
        {"from": "biodiversity_credit_engine",     "to": "portfolio_analytics_engine_v2",
         "fields": ["biodiversity_credit_score", "credit_quality_tier"],    "type": "bio_credit_portfolio"},
        {"from": "biodiversity_credit_engine",     "to": "regulatory_report_compiler",
         "fields": ["gbf_t15_disclosure_score", "tnfd_composite"],          "type": "gbf_t15_disclosure"},
        {"from": "biodiversity_credit_engine",     "to": "factor_overlay_engine",
         "fields": ["credit_quality_tier", "total_ecosystem_value_m"],      "type": "nature_market_factor"},
        # E89 Just Transition — inbound
        {"from": "climate_transition_risk_engine", "to": "just_transition_engine",
         "fields": ["stranded_asset_exposure", "sector_transition_score"],  "type": "transition_jt_input"},
        {"from": "sovereign_climate_risk_engine",  "to": "just_transition_engine",
         "fields": ["ndc_ambition", "fiscal_resilience_score"],             "type": "sovereign_jt_input"},
        {"from": "em_climate_risk_engine",         "to": "just_transition_engine",
         "fields": ["just_transition_risk", "gcf_allocation_bn"],           "type": "em_jt_linkage"},
        # E89 Just Transition — outbound
        {"from": "just_transition_engine",         "to": "portfolio_analytics_engine_v2",
         "fields": ["just_transition_score", "transition_risk_tier"],       "type": "jt_portfolio_risk"},
        {"from": "just_transition_engine",         "to": "regulatory_report_compiler",
         "fields": ["ilo_composite_score", "eu_jtf_eligible"],              "type": "jt_disclosure"},
        {"from": "just_transition_engine",         "to": "factor_overlay_engine",
         "fields": ["transition_risk_tier", "net_jobs_impact"],             "type": "jt_factor_overlay"},
        # E90 Carbon Removal — inbound
        {"from": "carbon_credit_quality_engine",   "to": "carbon_removal_engine",
         "fields": ["credit_quality_tier", "permanence_risk"],              "type": "cdr_quality_input"},
        {"from": "internal_carbon_price_engine",   "to": "carbon_removal_engine",
         "fields": ["nze_irr_pct", "abatement_cost_curve"],                 "type": "icp_cdr_linkage"},
        {"from": "carbon_accounting",              "to": "carbon_removal_engine",
         "fields": ["residual_emissions_tco2", "scope3_total"],             "type": "residual_cdr_demand"},
        # E90 Carbon Removal — outbound
        {"from": "carbon_removal_engine",          "to": "portfolio_analytics_engine_v2",
         "fields": ["cdr_quality_score", "cdr_quality_tier"],               "type": "cdr_portfolio_overlay"},
        {"from": "carbon_removal_engine",          "to": "regulatory_report_compiler",
         "fields": ["oxford_composite_score", "article_64_eligible"],       "type": "cdr_disclosure"},
        {"from": "carbon_removal_engine",          "to": "factor_overlay_engine",
         "fields": ["frontier_eligible", "lcoe_usd_tco2"],                  "type": "cdr_factor_overlay"},
        # E91 Climate Litigation — inbound
        {"from": "greenwashing_risk_engine",       "to": "climate_litigation_engine",
         "fields": ["greenwashing_risk_score", "misleading_claims"],        "type": "greenwashing_litigation_input"},
        {"from": "climate_financial_statements_engine","to": "climate_litigation_engine",
         "fields": ["disclosure_completeness_pct", "ifrs_s2_score"],        "type": "disclosure_litigation_input"},
        {"from": "stranded_asset_engine",          "to": "climate_litigation_engine",
         "fields": ["stranded_asset_exposure_m", "write_down_year"],        "type": "stranded_liability_input"},
        # E91 Climate Litigation — outbound
        {"from": "climate_litigation_engine",      "to": "portfolio_analytics_engine_v2",
         "fields": ["litigation_risk_score", "max_litigation_exposure_m"],  "type": "litigation_portfolio_risk"},
        {"from": "climate_litigation_engine",      "to": "regulatory_report_compiler",
         "fields": ["risk_tier", "litigation_provision_m"],                 "type": "litigation_disclosure"},
        {"from": "climate_litigation_engine",      "to": "entity360",
         "fields": ["litigation_risk_score", "risk_tier"],                  "type": "litigation_entity_enrichment"},
    ]

    existing_edge_keys = {(e.get("from"), e.get("to")) for e in service_instance._dependencies}
    for edge in new_edges:
        key = (edge.get("from"), edge.get("to"))
        if key not in existing_edge_keys:
            service_instance._dependencies.append(edge)
            existing_edge_keys.add(key)


def _register_e92_e95_modules(service_instance) -> None:
    """Register E92-E95 dependency edges: Water Risk, Critical Minerals, NbS Finance, SFDR Art 9."""
    new_edges = [
        # E92 Water Risk — inbound
        {"from": "nature_risk_engine",             "to": "water_risk_engine",
         "fields": ["water_withdrawal_m3", "water_stress_pct"],             "type": "nature_water_input"},
        {"from": "climate_transition_risk_engine", "to": "water_risk_engine",
         "fields": ["physical_risk_score", "scenario_temp"],                "type": "climate_water_physical"},
        {"from": "sovereign_climate_risk_engine",  "to": "water_risk_engine",
         "fields": ["physical_risk_score", "adaptation_capacity"],          "type": "sovereign_water_stress"},
        # E92 Water Risk — outbound
        {"from": "water_risk_engine",              "to": "portfolio_analytics_engine_v2",
         "fields": ["water_risk_score", "water_risk_tier"],                 "type": "water_portfolio_overlay"},
        {"from": "water_risk_engine",              "to": "regulatory_report_compiler",
         "fields": ["tnfd_water_disclosure_score", "aqueduct_overall_score"], "type": "water_disclosure"},
        {"from": "water_risk_engine",              "to": "factor_overlay_engine",
         "fields": ["water_risk_tier", "total_water_financial_risk_m"],     "type": "water_factor_overlay"},
        {"from": "water_risk_engine",              "to": "nbs_finance_engine",
         "fields": ["water_stressed_area_pct", "watershed_protection_m3_yr"], "type": "water_nbs_linkage"},
        # E93 Critical Minerals — inbound
        {"from": "climate_transition_risk_engine", "to": "critical_minerals_engine",
         "fields": ["ev_exposure", "solar_exposure"],                       "type": "transition_crm_demand"},
        {"from": "supply_chain_engine",            "to": "critical_minerals_engine",
         "fields": ["supply_chain_tiers", "supplier_countries"],            "type": "sc_crm_input"},
        {"from": "sovereign_climate_risk_engine",  "to": "critical_minerals_engine",
         "fields": ["political_stability_score", "geopolitical_risk"],      "type": "sovereign_crm_risk"},
        # E93 Critical Minerals — outbound
        {"from": "critical_minerals_engine",       "to": "portfolio_analytics_engine_v2",
         "fields": ["crm_risk_score", "crm_risk_tier"],                     "type": "crm_portfolio_risk"},
        {"from": "critical_minerals_engine",       "to": "regulatory_report_compiler",
         "fields": ["eu_crm_compliance_score", "oecd_ddg_score"],           "type": "crm_disclosure"},
        {"from": "critical_minerals_engine",       "to": "factor_overlay_engine",
         "fields": ["crm_risk_tier", "supply_disruption_prob_pct"],         "type": "crm_factor_overlay"},
        # E94 NbS Finance — inbound
        {"from": "biodiversity_credit_engine",     "to": "nbs_finance_engine",
         "fields": ["habitat_area_ha", "msa_uplift_pct"],                   "type": "bio_nbs_linkage"},
        {"from": "carbon_removal_engine",          "to": "nbs_finance_engine",
         "fields": ["carbon_sequestration_tco2_yr", "permanence_years"],    "type": "cdr_nbs_carbon"},
        {"from": "water_risk_engine",              "to": "nbs_finance_engine",
         "fields": ["water_stressed_area_pct", "watershed_protection_m3_yr"], "type": "water_nbs_cobenefit"},
        # E94 NbS Finance — outbound
        {"from": "nbs_finance_engine",             "to": "portfolio_analytics_engine_v2",
         "fields": ["nbs_quality_score", "nbs_bankability_tier"],           "type": "nbs_portfolio_overlay"},
        {"from": "nbs_finance_engine",             "to": "regulatory_report_compiler",
         "fields": ["iucn_composite_score", "gbf_target_2_contribution"],   "type": "nbs_disclosure"},
        {"from": "nbs_finance_engine",             "to": "factor_overlay_engine",
         "fields": ["nbs_bankability_tier", "npv_m"],                       "type": "nbs_factor_overlay"},
        {"from": "nbs_finance_engine",             "to": "carbon_credit_quality_engine",
         "fields": ["vcmi_integrity_score", "carbon_credit_standard"],      "type": "nbs_carbon_credit"},
        # E95 SFDR Art 9 — inbound
        {"from": "sfdr_product_engine",            "to": "sfdr_art9_engine",
         "fields": ["sustainable_investment_pct", "taxonomy_aligned_pct"],  "type": "sfdr_art9_upgrade"},
        {"from": "eu_taxonomy_gar_btar_engine",    "to": "sfdr_art9_engine",
         "fields": ["taxonomy_aligned_pct", "dnsh_all_pass"],               "type": "taxonomy_art9_input"},
        {"from": "sfdr_pai_engine",                "to": "sfdr_art9_engine",
         "fields": ["pai_completeness_pct", "mandatory_pai_count"],         "type": "pai_art9_completeness"},
        # E95 SFDR Art 9 — outbound
        {"from": "sfdr_art9_engine",               "to": "portfolio_analytics_engine_v2",
         "fields": ["art9_eligibility_score", "art9_eligible"],             "type": "art9_portfolio_classification"},
        {"from": "sfdr_art9_engine",               "to": "regulatory_report_compiler",
         "fields": ["compliance_tier", "rts_annex_completeness_pct"],       "type": "art9_disclosure"},
        {"from": "sfdr_art9_engine",               "to": "entity360",
         "fields": ["art9_eligible", "compliance_tier"],                    "type": "art9_entity_enrichment"},
    ]

    existing_edge_keys = {(e.get("from"), e.get("to")) for e in service_instance._dependencies}
    for edge in new_edges:
        key = (edge.get("from"), edge.get("to"))
        if key not in existing_edge_keys:
            service_instance._dependencies.append(edge)
            existing_edge_keys.add(key)


def _register_e96_e99_modules(service_instance) -> None:
    """Register E96-E99 dependency edges: VCM Integrity, Social Taxonomy, Green Hydrogen, Transition Finance."""
    new_edges = [
        # E96 VCM Integrity — inbound
        {"from": "carbon_credit_quality_engine",   "to": "vcm_integrity_engine",
         "fields": ["quality_tier", "ccp_label_eligible"],              "type": "carbon_credit_base"},
        {"from": "nbs_finance_engine",             "to": "vcm_integrity_engine",
         "fields": ["vcmi_integrity_score", "carbon_credit_standard"],  "type": "nbs_vcm_link"},
        {"from": "carbon_removal_engine",          "to": "vcm_integrity_engine",
         "fields": ["cdr_type", "permanence_years", "ghg_removal_tco2"], "type": "cdr_vcm_registry"},
        # E96 VCM Integrity — outbound
        {"from": "vcm_integrity_engine",           "to": "portfolio_analytics_engine_v2",
         "fields": ["integrity_tier", "vcm_price_usd_t"],               "type": "vcm_portfolio_valuation"},
        {"from": "vcm_integrity_engine",           "to": "regulatory_report_compiler",
         "fields": ["ccp_label_eligible", "vcmi_claim_tier"],           "type": "vcm_disclosure"},
        {"from": "vcm_integrity_engine",           "to": "greenwashing_risk_engine",
         "fields": ["integrity_tier", "oxford_score"],                  "type": "vcm_greenwash_check"},
        # E97 Social Taxonomy — inbound
        {"from": "csddd_engine",                   "to": "social_taxonomy_engine",
         "fields": ["adverse_impact_score", "social_adverse_count"],    "type": "csddd_social_input"},
        {"from": "supply_chain_engine",            "to": "social_taxonomy_engine",
         "fields": ["supplier_countries", "supply_chain_tiers"],        "type": "sc_social_hrdd"},
        {"from": "factor_overlay_engine",          "to": "social_taxonomy_engine",
         "fields": ["automation_disruption_score", "labour_market"],    "type": "factor_social_input"},
        # E97 Social Taxonomy — outbound
        {"from": "social_taxonomy_engine",         "to": "eu_taxonomy_gar_btar_engine",
         "fields": ["social_taxonomy_aligned", "minimum_social_safeguards"], "type": "social_taxonomy_ms"},
        {"from": "social_taxonomy_engine",         "to": "regulatory_report_compiler",
         "fields": ["social_taxonomy_score", "ilo_composite"],          "type": "social_disclosure"},
        {"from": "social_taxonomy_engine",         "to": "entity360",
         "fields": ["social_taxonomy_eligible", "ilo_violations"],      "type": "social_entity_enrichment"},
        # E98 Green Hydrogen — inbound
        {"from": "eu_taxonomy_gar_btar_engine",    "to": "green_hydrogen_engine",
         "fields": ["taxonomy_aligned_pct", "dnsh_climate_pass"],       "type": "taxonomy_h2_eligibility"},
        {"from": "climate_transition_risk_engine", "to": "green_hydrogen_engine",
         "fields": ["energy_transition_score", "carbon_price"],         "type": "transition_h2_economics"},
        {"from": "factor_overlay_engine",          "to": "green_hydrogen_engine",
         "fields": ["h2_blending_economics", "energy_independence"],    "type": "factor_h2_input"},
        # E98 Green Hydrogen — outbound
        {"from": "green_hydrogen_engine",          "to": "portfolio_analytics_engine_v2",
         "fields": ["rfnbo_eligible", "lcoh_usd_per_kgh2"],             "type": "h2_portfolio_overlay"},
        {"from": "green_hydrogen_engine",          "to": "regulatory_report_compiler",
         "fields": ["rfnbo_composite_score", "ghg_intensity_kgco2_per_kgh2"], "type": "h2_disclosure"},
        {"from": "green_hydrogen_engine",          "to": "eu_green_bond_standard_engine",
         "fields": ["rfnbo_eligible", "h2cfd_eligible"],                "type": "h2_green_bond"},
        # E99 Transition Finance — inbound
        {"from": "tpt_transition_plan_engine",     "to": "transition_finance_engine",
         "fields": ["tpt_composite", "quality_tier"],                   "type": "tpt_credibility_input"},
        {"from": "sbti_engine",                    "to": "transition_finance_engine",
         "fields": ["sbti_validated", "temperature_score"],             "type": "sbti_transition_input"},
        {"from": "sovereign_climate_risk_engine",  "to": "transition_finance_engine",
         "fields": ["ndc_ambition", "transition_readiness"],            "type": "sovereign_transition_context"},
        {"from": "tnfd_engine",                    "to": "transition_finance_engine",
         "fields": ["leap_status", "nature_target_score"],              "type": "tnfd_transition_nature"},
        # E99 Transition Finance — outbound
        {"from": "transition_finance_engine",      "to": "portfolio_analytics_engine_v2",
         "fields": ["credibility_score", "portfolio_temperature_c"],    "type": "transition_portfolio_score"},
        {"from": "transition_finance_engine",      "to": "regulatory_report_compiler",
         "fields": ["tpt_composite", "credibility_tier"],               "type": "transition_disclosure"},
        {"from": "transition_finance_engine",      "to": "greenwashing_risk_engine",
         "fields": ["credibility_tier", "red_flags"],                   "type": "transition_greenwash_screen"},
        {"from": "transition_finance_engine",      "to": "factor_overlay_engine",
         "fields": ["credibility_tier", "kpi_ambition_score"],          "type": "transition_factor_overlay"},
    ]

    existing_edge_keys = {(e.get("from"), e.get("to")) for e in service_instance._dependencies}
    for edge in new_edges:
        key = (edge.get("from"), edge.get("to"))
        if key not in existing_edge_keys:
            service_instance._dependencies.append(edge)
            existing_edge_keys.add(key)


def _register_e100_e103_modules(service_instance) -> None:
    """Register E100-E103 dependency edges: Stress Test Orchestrator, SSCF, Double Materiality, Temperature Alignment."""
    new_edges = [
        # E100 Stress Test Orchestrator — inbound
        {"from": "climate_stress_testing_engine",  "to": "stress_test_orchestrator_engine",
         "fields": ["sector_pd_migration", "cet1_depletion_pp"],        "type": "stress_test_base_input"},
        {"from": "sovereign_climate_risk_engine",  "to": "stress_test_orchestrator_engine",
         "fields": ["gdp_deviation_pct", "fiscal_resilience_score"],    "type": "sovereign_macro_stress"},
        {"from": "portfolio_analytics_engine_v2",  "to": "stress_test_orchestrator_engine",
         "fields": ["sector_breakdown", "total_exposure_bn"],           "type": "portfolio_stress_input"},
        {"from": "em_climate_risk_engine",         "to": "stress_test_orchestrator_engine",
         "fields": ["concessional_finance_gap", "country_risk_score"],  "type": "em_stress_scenario"},
        # E100 Stress Test Orchestrator — outbound
        {"from": "stress_test_orchestrator_engine","to": "regulatory_report_compiler",
         "fields": ["stress_test_pass", "regulatory_submission_ready"], "type": "stress_submission"},
        {"from": "stress_test_orchestrator_engine","to": "portfolio_analytics_engine_v2",
         "fields": ["stressed_cet1_pct", "climate_var_pct"],            "type": "stress_portfolio_overlay"},
        {"from": "stress_test_orchestrator_engine","to": "factor_overlay_engine",
         "fields": ["cet1_depletion_pp", "physical_risk_el_bn"],        "type": "stress_factor_overlay"},
        # E101 SSCF — inbound
        {"from": "supply_chain_engine",            "to": "sscf_engine",
         "fields": ["scope3_cat1_coverage", "supplier_risk_tier"],      "type": "sc_sscf_base"},
        {"from": "csddd_engine",                   "to": "sscf_engine",
         "fields": ["adverse_impact_categories", "dd_compliance_score"],"type": "csddd_sscf_cascade"},
        {"from": "social_taxonomy_engine",         "to": "sscf_engine",
         "fields": ["ilo_compliance_score", "cahra_flag"],              "type": "social_sscf_input"},
        {"from": "eudr_engine",                    "to": "sscf_engine",
         "fields": ["commodity_risk_tier", "deforestation_free"],       "type": "eudr_sscf_traceability"},
        # E101 SSCF — outbound
        {"from": "sscf_engine",                    "to": "portfolio_analytics_engine_v2",
         "fields": ["sscf_eligible", "overall_sscf_score"],             "type": "sscf_portfolio_risk"},
        {"from": "sscf_engine",                    "to": "regulatory_report_compiler",
         "fields": ["oecd_ddg_step", "scope3_cat1_covered"],            "type": "sscf_disclosure"},
        {"from": "sscf_engine",                    "to": "greenwashing_risk_engine",
         "fields": ["sscf_framework", "kpi_materiality_score"],         "type": "sscf_greenwash_screen"},
        # E102 Double Materiality — inbound
        {"from": "csrd_dma_engine",                "to": "double_materiality_engine",
         "fields": ["material_topics", "completeness_score"],           "type": "dma_base_input"},
        {"from": "assurance_readiness_engine",     "to": "double_materiality_engine",
         "fields": ["readiness_tier", "blocking_criteria_count"],       "type": "assurance_dma_link"},
        {"from": "eu_taxonomy_gar_btar_engine",    "to": "double_materiality_engine",
         "fields": ["taxonomy_aligned_pct", "dnsh_all_pass"],           "type": "taxonomy_dma_input"},
        {"from": "biodiversity_finance_engine",    "to": "double_materiality_engine",
         "fields": ["tnfd_composite", "e4_material_flag"],              "type": "bio_dma_e4"},
        # E102 Double Materiality — outbound
        {"from": "double_materiality_engine",      "to": "regulatory_report_compiler",
         "fields": ["material_topics_count", "completeness_score"],     "type": "dma_csrd_report"},
        {"from": "double_materiality_engine",      "to": "assurance_readiness_engine",
         "fields": ["assurance_ready", "double_material_count"],        "type": "dma_assurance_gate"},
        {"from": "double_materiality_engine",      "to": "entity360",
         "fields": ["e1_climate_material", "s1_workforce_material"],   "type": "dma_entity_enrichment"},
        # E103 Temperature Alignment — inbound
        {"from": "portfolio_analytics_engine_v2",  "to": "temperature_alignment_engine",
         "fields": ["total_exposure_bn", "sector_breakdown"],           "type": "portfolio_itr_input"},
        {"from": "pcaf_waci_engine",               "to": "temperature_alignment_engine",
         "fields": ["waci_tco2_mn_revenue", "pcaf_dqs_weighted"],       "type": "pcaf_itr_base"},
        {"from": "scope3_categories_engine",       "to": "temperature_alignment_engine",
         "fields": ["c15_financed_mtco2", "dqs_weighted_score"],        "type": "scope3_c15_itr"},
        {"from": "sbti_engine",                    "to": "temperature_alignment_engine",
         "fields": ["near_term_target_pct", "long_term_target_pct"],   "type": "sbti_itr_targets"},
        # E103 Temperature Alignment — outbound
        {"from": "temperature_alignment_engine",   "to": "portfolio_analytics_engine_v2",
         "fields": ["portfolio_itr_c", "paris_aligned"],                "type": "itr_portfolio_overlay"},
        {"from": "temperature_alignment_engine",   "to": "regulatory_report_compiler",
         "fields": ["sbti_fi_target_set", "reduction_required_pct"],   "type": "itr_disclosure"},
        {"from": "temperature_alignment_engine",   "to": "stress_test_orchestrator_engine",
         "fields": ["portfolio_itr_c", "sector_temperature_breakdown"], "type": "itr_stress_calibration"},
        {"from": "temperature_alignment_engine",   "to": "entity360",
         "fields": ["portfolio_itr_c", "on_track"],                     "type": "itr_entity_enrichment"},
    ]

    existing_edge_keys = {(e.get("from"), e.get("to")) for e in service_instance._dependencies}
    for edge in new_edges:
        key = (edge.get("from"), edge.get("to"))
        if key not in existing_edge_keys:
            service_instance._dependencies.append(edge)
            existing_edge_keys.add(key)
