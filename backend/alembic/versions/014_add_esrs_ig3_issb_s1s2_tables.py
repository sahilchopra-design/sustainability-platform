"""Add comprehensive ESRS IG3 + ISSB S1/S2 taxonomy structured tables

Revision ID: 014_add_esrs_ig3_issb_s1s2_tables
Revises: 013_add_csrd_kpi_store
Create Date: 2026-03-01

Source: EFRAG IG 3 Draft List of ESRS Data Points (23-Nov-2023 SRB version)
        IFRS S1 General Requirements + IFRS S2 Climate-Related Disclosures

All column names map 1-to-1 to IG3 data point IDs referenced in comments.
Quantitative DPs extracted: ~330 numeric / monetary / percent / area / volume / mass.

Tables (14):
  esrs2_general_disclosures  — ESRS 2 GOV-1, GOV-3, SBM-1 quantitative DPs
  esrs_e1_energy             — E1-5  all energy consumption & mix data points
  esrs_e1_ghg_emissions      — E1-6  Scope 1, 2, 3 with every IG3 sub-breakdown
  esrs_e1_ghg_removals       — E1-7  GHG removals, carbon credits, reversals
  esrs_e1_carbon_price       — E1-8  internal carbon pricing scheme data
  esrs_e1_financial_effects  — E1-9  physical + transition financial effects
  esrs_e2_pollution          — E2-4 air/water/soil pollutants + E2-5 substances + E2-6
  esrs_e3_water              — E3-4 water consumption + E3-5 financial effects
  esrs_e4_biodiversity       — E4-3 / E4-5 / E4-6 biodiversity + financial effects
  esrs_e5_circular           — E5-4 resource inflows + E5-5 waste + E5-6
  esrs_s1_workforce          — S1-6 to S1-17 all workforce quantitative DPs
  esrs_g1_conduct            — G1-3 to G1-6 all business conduct quantitative DPs
  issb_s1_general            — IFRS S1 governance, strategy, risk mgmt, metrics
  issb_s2_climate            — IFRS S2 6 cross-industry metric categories + strategy
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '014_add_esrs_ig3_issb_s1s2_tables'
down_revision = '013_add_csrd_kpi_store'
branch_labels = None
depends_on = None

# ---------------------------------------------------------------------------
# Helper: standard common columns appended to every table
# ---------------------------------------------------------------------------
def _common(table_name):
    return [
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_registry_id', UUID(as_uuid=True), nullable=False),
        sa.Column('reporting_year', sa.Integer(), nullable=False),
        # Reporting boundary
        sa.Column('consolidation_approach', sa.String(50)),
        # operational_control | financial_control | equity_share
        sa.Column('reporting_boundary_coverage_pct', sa.Numeric(5, 2)),
        # Data quality & assurance
        sa.Column('is_assured', sa.Boolean(), server_default='false'),
        sa.Column('assurance_level', sa.String(20)),   # limited | reasonable
        sa.Column('data_quality_score', sa.Integer()),  # 1 (best) – 5 (worst)
        # Restatement
        sa.Column('is_restated', sa.Boolean(), server_default='false'),
        sa.Column('restatement_reason', sa.Text()),
        # Workflow
        sa.Column('status', sa.String(20), server_default='draft'),
        # draft | approved | published
        sa.Column('submitted_by', sa.String(100)),
        sa.Column('approved_by', sa.String(100)),
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(
            ['entity_registry_id'], ['csrd_entity_registry.id'],
            ondelete='CASCADE'),
        sa.UniqueConstraint('entity_registry_id', 'reporting_year',
                            name=f'uq_{table_name}_entity_year'),
    ]


def upgrade():

    # ======================================================================
    # 1. esrs2_general_disclosures
    #    ESRS 2 GOV-1 (par 21), GOV-3 (par 29), SBM-1 (par 40) quantitative
    # ======================================================================
    op.create_table(
        'esrs2_general_disclosures',
        # GOV-1 Board composition (par 21a, 21d, 21e)
        sa.Column('board_executive_members_count', sa.Integer()),           # par 21a
        sa.Column('board_non_executive_members_count', sa.Integer()),       # par 21a
        sa.Column('board_sustainability_expertise_pct', sa.Numeric(5, 2)), # par 21d
        sa.Column('board_gender_diversity_ratio', sa.Numeric(5, 2)),       # par 21d SFDR
        sa.Column('board_independent_members_pct', sa.Numeric(5, 2)),      # par 21e SFDR
        # GOV-3 Remuneration (par 29d)
        sa.Column('variable_remuneration_sustainability_linked_pct',
                  sa.Numeric(5, 2)),   # par 29d
        # SBM-1 Business model & value chain (par 40)
        sa.Column('total_employees_headcount', sa.Integer()),              # par 40a iii
        sa.Column('employees_headcount_by_segment', JSONB()),              # par 40a iii by segment
        sa.Column('total_revenue_eur', sa.Numeric(18, 2)),                 # par 40b
        sa.Column('revenue_by_esrs_sector', JSONB()),                      # par 40b table
        sa.Column('revenue_fossil_fuel_total_eur', sa.Numeric(18, 2)),     # par 40d i
        sa.Column('revenue_coal_eur', sa.Numeric(18, 2)),                  # par 40d i
        sa.Column('revenue_oil_eur', sa.Numeric(18, 2)),                   # par 40d i
        sa.Column('revenue_gas_eur', sa.Numeric(18, 2)),                   # par 40d i
        sa.Column('revenue_taxonomy_aligned_fossil_gas_eur',
                  sa.Numeric(18, 2)),  # par 40d i
        sa.Column('revenue_chemicals_production_eur', sa.Numeric(18, 2)), # par 40d ii SFDR
        sa.Column('revenue_controversial_weapons_eur', sa.Numeric(18, 2)),# par 40d iii SFDR
        sa.Column('revenue_tobacco_eur', sa.Numeric(18, 2)),              # par 40d iv SFDR
        # SBM-3 Financial effects (par 48d, 48e) — monetary narrative
        sa.Column('current_financial_effects_risks_eur', sa.Numeric(18, 2)),     # par 48d
        sa.Column('anticipated_financial_effects_risks_eur', sa.Numeric(18, 2)),# par 48e
        *_common('esrs2_general_disclosures'),
    )

    # ======================================================================
    # 2. esrs_e1_energy  —  ESRS E1-5 (all energy DP codes)
    # ======================================================================
    op.create_table(
        'esrs_e1_energy',
        # ---- Total energy (E1-5|37) ----
        sa.Column('total_energy_consumption_mwh', sa.Numeric(18, 3)),
        # SFDR: E1-5|37
        # ---- Fossil sources (E1-5|37a, 38a-38e) ----
        sa.Column('energy_from_fossil_sources_mwh', sa.Numeric(18, 3)),    # E1-5|37a SFDR
        sa.Column('fuel_from_coal_coal_products_mwh', sa.Numeric(18, 3)), # E1-5|38a SFDR
        sa.Column('fuel_from_crude_oil_petroleum_mwh', sa.Numeric(18, 3)),# E1-5|38b SFDR
        sa.Column('fuel_from_natural_gas_mwh', sa.Numeric(18, 3)),        # E1-5|38c SFDR
        sa.Column('fuel_from_other_fossil_sources_mwh', sa.Numeric(18, 3)),# E1-5|38d SFDR
        sa.Column('elec_heat_steam_cooling_fossil_mwh', sa.Numeric(18, 3)),# E1-5|38e SFDR
        sa.Column('fossil_energy_pct', sa.Numeric(6, 3)),                 # E1-5|AR 34
        # ---- Nuclear (E1-5|37b) ----
        sa.Column('energy_from_nuclear_sources_mwh', sa.Numeric(18, 3)), # E1-5|37b SFDR
        sa.Column('nuclear_energy_pct', sa.Numeric(6, 3)),               # E1-5|AR 34
        # ---- Renewable sources (E1-5|37c, 37ci, 37cii, 37ciii) ----
        sa.Column('energy_from_renewable_sources_mwh', sa.Numeric(18, 3)),# E1-5|37c SFDR
        sa.Column('fuel_from_renewable_sources_mwh', sa.Numeric(18, 3)), # E1-5|37ci SFDR
        sa.Column('elec_heat_steam_cooling_renewables_mwh',
                  sa.Numeric(18, 3)),  # E1-5|37cii SFDR
        sa.Column('self_generated_non_fuel_renewable_mwh',
                  sa.Numeric(18, 3)),  # E1-5|37ciii SFDR
        sa.Column('renewable_energy_pct', sa.Numeric(6, 3)),             # E1-5|AR 34
        # ---- Production (E1-5|39) ----
        sa.Column('non_renewable_energy_production_mwh', sa.Numeric(18, 3)),# E1-5|39
        sa.Column('renewable_energy_production_mwh', sa.Numeric(18, 3)),    # E1-5|39
        # ---- High climate impact sector metrics (E1-5|40, 41, AR38b) ----
        sa.Column('is_high_climate_impact_sector', sa.Boolean(),
                  server_default='false'),
        sa.Column('energy_intensity_high_climate_impact_pct',
                  sa.Numeric(10, 6)),  # E1-5|40 SFDR: MWh/net revenue
        sa.Column('energy_consumption_high_climate_impact_mwh',
                  sa.Numeric(18, 3)),  # E1-5|41 SFDR
        sa.Column('net_revenue_high_climate_impact_eur', sa.Numeric(18, 2)),# E1-5|AR38b
        sa.Column('net_revenue_other_activities_eur', sa.Numeric(18, 2)),   # E1-5|AR38b
        # ---- Renewable energy certificates / GOs / PPAs (voluntary) ----
        sa.Column('renewable_certificates_gos_mwh', sa.Numeric(18, 3)),
        sa.Column('ppa_renewable_volumes_mwh', sa.Numeric(18, 3)),
        *_common('esrs_e1_energy'),
    )
    op.create_index('ix_esrs_e1_energy_entity_year', 'esrs_e1_energy',
                    ['entity_registry_id', 'reporting_year'])

    # ======================================================================
    # 3. esrs_e1_ghg_emissions  —  ESRS E1-6
    # ======================================================================
    op.create_table(
        'esrs_e1_ghg_emissions',
        sa.Column('gwp_standard', sa.String(10)),     # AR4 | AR5 | AR6
        # ---- Scope 1 (E1-6|48a, 48b) ----
        sa.Column('scope1_gross_tco2e', sa.Numeric(18, 3)),          # E1-6|48a SFDR+P3+BENCH
        sa.Column('scope1_ets_covered_pct', sa.Numeric(6, 3)),       # E1-6|48b SFDR: % from ETS
        # Scope 1 gas breakdown (voluntary / AR 41 table)
        sa.Column('scope1_co2_tco2', sa.Numeric(18, 3)),
        sa.Column('scope1_ch4_tco2e', sa.Numeric(18, 3)),
        sa.Column('scope1_n2o_tco2e', sa.Numeric(18, 3)),
        sa.Column('scope1_hfcs_tco2e', sa.Numeric(18, 3)),
        sa.Column('scope1_pfcs_tco2e', sa.Numeric(18, 3)),
        sa.Column('scope1_sf6_tco2e', sa.Numeric(18, 3)),
        sa.Column('scope1_nf3_tco2e', sa.Numeric(18, 3)),
        sa.Column('scope1_biogenic_co2_tco2', sa.Numeric(18, 3)),    # E1-6|AR43c
        # ---- Scope 2 (E1-6|49a, 49b, 52a, 52b) ----
        sa.Column('scope2_location_based_tco2e', sa.Numeric(18, 3)), # E1-6|49a SFDR+P3+BENCH
        sa.Column('scope2_market_based_tco2e', sa.Numeric(18, 3)),   # E1-6|49b SFDR+P3+BENCH
        # Contractual instruments (E1-6|AR45d)
        sa.Column('scope2_contractual_instruments_pct', sa.Numeric(6, 3)),
        sa.Column('scope2_bundled_instruments_pct', sa.Numeric(6, 3)),
        sa.Column('scope2_go_rec_pct', sa.Numeric(6, 3)),
        sa.Column('scope2_unbundled_claims_pct', sa.Numeric(6, 3)),
        sa.Column('scope2_biogenic_co2_tco2', sa.Numeric(18, 3)),    # E1-6|AR45e
        # ---- Scope 3 total (E1-6|51) ----
        sa.Column('scope3_total_tco2e', sa.Numeric(18, 3)),          # E1-6|51 SFDR+P3+BENCH
        sa.Column('scope3_primary_data_pct', sa.Numeric(6, 3)),      # E1-6|AR46g
        sa.Column('scope3_biogenic_co2_tco2', sa.Numeric(18, 3)),    # E1-6|AR46j
        # GHG Protocol 15 categories (E1-6|AR46d table)
        sa.Column('scope3_cat01_purchased_goods_services_tco2e', sa.Numeric(18, 3)),
        sa.Column('scope3_cat02_capital_goods_tco2e', sa.Numeric(18, 3)),
        sa.Column('scope3_cat03_fuel_energy_tco2e', sa.Numeric(18, 3)),
        sa.Column('scope3_cat04_upstream_transport_tco2e', sa.Numeric(18, 3)),
        sa.Column('scope3_cat05_waste_operations_tco2e', sa.Numeric(18, 3)),
        sa.Column('scope3_cat06_business_travel_tco2e', sa.Numeric(18, 3)),
        sa.Column('scope3_cat07_employee_commuting_tco2e', sa.Numeric(18, 3)),
        sa.Column('scope3_cat08_upstream_leased_assets_tco2e', sa.Numeric(18, 3)),
        sa.Column('scope3_cat09_downstream_transport_tco2e', sa.Numeric(18, 3)),
        sa.Column('scope3_cat10_processing_sold_products_tco2e', sa.Numeric(18, 3)),
        sa.Column('scope3_cat11_use_of_sold_products_tco2e', sa.Numeric(18, 3)),
        sa.Column('scope3_cat12_end_of_life_treatment_tco2e', sa.Numeric(18, 3)),
        sa.Column('scope3_cat13_downstream_leased_assets_tco2e', sa.Numeric(18, 3)),
        sa.Column('scope3_cat14_franchises_tco2e', sa.Numeric(18, 3)),
        sa.Column('scope3_cat15_investments_tco2e', sa.Numeric(18, 3)),
        # Scope 3 DQ score per category (PCAF/GHG Protocol)
        sa.Column('scope3_cat_dq_scores', JSONB()),   # {cat1: score, cat2: score, ...}
        # ---- Total GHG (E1-6|44+52) ----
        sa.Column('total_ghg_tco2e', sa.Numeric(18, 3)),             # E1-6|44+52 SFDR+P3+BENCH
        sa.Column('total_ghg_location_based_tco2e', sa.Numeric(18, 3)), # E1-6|44+52a
        sa.Column('total_ghg_market_based_tco2e', sa.Numeric(18, 3)),   # E1-6|44+52b
        # ---- GHG intensity (E1-6|53) ----
        sa.Column('ghg_intensity_location_based_tco2e_per_meur',
                  sa.Numeric(14, 6)),  # E1-6|53 SFDR+P3+BENCH
        sa.Column('ghg_intensity_market_based_tco2e_per_meur',
                  sa.Numeric(14, 6)),  # E1-6|53 SFDR+P3+BENCH
        sa.Column('net_revenue_for_intensity_meur', sa.Numeric(18, 2)),  # E1-6|AR55
        sa.Column('net_revenue_other_meur', sa.Numeric(18, 2)),          # E1-6|AR55
        # Additional breakdown (voluntary AR 41 table)
        sa.Column('scope1_stationary_combustion_tco2e', sa.Numeric(18, 3)),
        sa.Column('scope1_mobile_combustion_tco2e', sa.Numeric(18, 3)),
        sa.Column('scope1_process_emissions_tco2e', sa.Numeric(18, 3)),
        sa.Column('scope1_fugitive_emissions_tco2e', sa.Numeric(18, 3)),
        # Base year for target tracking
        sa.Column('base_year', sa.Integer()),
        sa.Column('base_year_scope1_tco2e', sa.Numeric(18, 3)),
        sa.Column('base_year_scope2_market_tco2e', sa.Numeric(18, 3)),
        sa.Column('base_year_scope3_tco2e', sa.Numeric(18, 3)),
        *_common('esrs_e1_ghg_emissions'),
    )
    op.create_index('ix_esrs_e1_ghg_entity_year', 'esrs_e1_ghg_emissions',
                    ['entity_registry_id', 'reporting_year'])

    # ======================================================================
    # 4. esrs_e1_ghg_removals  —  ESRS E1-7
    # ======================================================================
    op.create_table(
        'esrs_e1_ghg_removals',
        # Total removals (E1-7|58a)
        sa.Column('total_ghg_removals_storage_tco2e', sa.Numeric(18, 3)),  # E1-7|58a
        sa.Column('ghg_emissions_from_removal_activity_tco2e',
                  sa.Numeric(18, 3)),  # E1-7|AR58f
        # Removals breakdown by activity (voluntary AR 58)
        sa.Column('removals_afforestation_tco2e', sa.Numeric(18, 3)),
        sa.Column('removals_reforestation_tco2e', sa.Numeric(18, 3)),
        sa.Column('removals_improved_forest_mgmt_tco2e', sa.Numeric(18, 3)),
        sa.Column('removals_soil_carbon_tco2e', sa.Numeric(18, 3)),
        sa.Column('removals_blue_carbon_tco2e', sa.Numeric(18, 3)),
        sa.Column('removals_direct_air_capture_tco2e', sa.Numeric(18, 3)),
        sa.Column('removals_bioenergy_ccs_tco2e', sa.Numeric(18, 3)),
        sa.Column('removals_geological_storage_tco2e', sa.Numeric(18, 3)),
        # Carbon credits (E1-7|59a, 59b)
        sa.Column('carbon_credits_verified_retired_tco2e', sa.Numeric(18, 3)),  # E1-7|59a
        sa.Column('carbon_credits_planned_retirement_tco2e', sa.Numeric(18, 3)),# E1-7|59b
        sa.Column('carbon_credits_reversals_tco2e', sa.Numeric(18, 3)),         # E1-7|AR60
        # Carbon credit quality metrics (E1-7|AR62)
        sa.Column('credits_reduction_projects_pct', sa.Numeric(6, 3)),  # E1-7|AR62a
        sa.Column('credits_removal_projects_pct', sa.Numeric(6, 3)),    # E1-7|AR62a
        sa.Column('credits_quality_standard_pct', sa.Numeric(6, 3)),    # E1-7|AR62c
        sa.Column('credits_eu_projects_pct', sa.Numeric(6, 3)),         # E1-7|AR62d
        sa.Column('credits_corresponding_adjustment_pct', sa.Numeric(6, 3)), # E1-7|AR62e
        sa.Column('carbon_credits_registry', sa.String(200)),
        sa.Column('carbon_credits_standard', sa.String(200)),
        # Climate neutrality claim
        sa.Column('makes_climate_neutral_claim', sa.Boolean(), server_default='false'),
        sa.Column('claim_complies_iso14068', sa.Boolean()),
        *_common('esrs_e1_ghg_removals'),
    )

    # ======================================================================
    # 5. esrs_e1_carbon_price  —  ESRS E1-8
    # ======================================================================
    op.create_table(
        'esrs_e1_carbon_price',
        sa.Column('has_internal_carbon_price', sa.Boolean(), server_default='false'),
        sa.Column('carbon_price_scheme_types', JSONB()),     # E1-8|63a: list of scheme types
        # Carbon price values (E1-8|63c)
        sa.Column('carbon_price_min_eur_per_tco2e', sa.Numeric(10, 2)),  # E1-8|63c
        sa.Column('carbon_price_max_eur_per_tco2e', sa.Numeric(10, 2)),  # E1-8|63c
        sa.Column('carbon_price_weighted_avg_eur_per_tco2e', sa.Numeric(10, 2)),
        # Scope coverage (E1-8|63d)
        sa.Column('scope1_emissions_covered_by_icp_pct', sa.Numeric(6, 3)), # E1-8|63d
        sa.Column('scope2_emissions_covered_by_icp_pct', sa.Numeric(6, 3)), # E1-8|63d
        sa.Column('scope3_emissions_covered_by_icp_pct', sa.Numeric(6, 3)), # E1-8|63d
        sa.Column('carbon_price_type', sa.String(50)),
        # shadow | internal_charge | explicit | none
        sa.Column('carbon_price_application', sa.String(200)),
        # investment decisions | target setting | both
        sa.Column('year_internal_price_implemented', sa.Integer()),
        # External carbon costs (EU ETS + other levies)
        sa.Column('eu_ets_allowance_cost_meur', sa.Numeric(14, 2)),
        sa.Column('other_carbon_levy_cost_meur', sa.Numeric(14, 2)),
        # Forward price assumptions (voluntary)
        sa.Column('carbon_price_assumption_2030_eur', sa.Numeric(10, 2)),
        sa.Column('carbon_price_assumption_2040_eur', sa.Numeric(10, 2)),
        sa.Column('carbon_price_assumption_2050_eur', sa.Numeric(10, 2)),
        *_common('esrs_e1_carbon_price'),
    )

    # ======================================================================
    # 6. esrs_e1_financial_effects  —  ESRS E1-9
    # ======================================================================
    op.create_table(
        'esrs_e1_financial_effects',
        sa.Column('scenario_set_used', sa.String(200)),   # NGFS / IEA / IPCC / proprietary
        # ---- Physical risk — financial effects (E1-9|66a-66d) ----
        sa.Column('assets_at_material_physical_risk_eur', sa.Numeric(18, 2)), # E1-9|66a P3
        sa.Column('assets_at_acute_physical_risk_eur', sa.Numeric(18, 2)),   # E1-9|66a P3
        sa.Column('assets_at_chronic_physical_risk_eur', sa.Numeric(18, 2)), # E1-9|66a P3
        sa.Column('assets_at_physical_risk_pct', sa.Numeric(6, 3)),          # E1-9|66a P3
        sa.Column('physical_risk_adaptation_coverage_pct', sa.Numeric(6, 3)),# E1-9|66b
        sa.Column('net_revenue_physical_risk_eur', sa.Numeric(18, 2)),        # E1-9|66d
        sa.Column('net_revenue_physical_risk_pct', sa.Numeric(6, 3)),         # E1-9|66d
        # Real estate by energy class (E1-9|67c P3) — JSON table
        sa.Column('re_assets_by_energy_efficiency_class', JSONB()),
        # {A+, A, B, C, D, E, F, G: carrying_amount_eur}
        # ---- Transition risk — financial effects (E1-9|67a-67e) ----
        sa.Column('assets_at_material_transition_risk_eur', sa.Numeric(18, 2)), # E1-9|67a
        sa.Column('assets_at_transition_risk_pct', sa.Numeric(6, 3)),           # E1-9|67a
        sa.Column('transition_risk_mitigation_coverage_pct', sa.Numeric(6, 3)), # E1-9|67b
        sa.Column('liabilities_transition_risk_eur', sa.Numeric(18, 2)),        # E1-9|67d
        sa.Column('net_revenue_transition_risk_eur', sa.Numeric(18, 2)),        # E1-9|67e
        sa.Column('net_revenue_coal_customers_eur', sa.Numeric(18, 2)),         # E1-9|67e
        sa.Column('net_revenue_oil_customers_eur', sa.Numeric(18, 2)),          # E1-9|67e
        sa.Column('net_revenue_gas_customers_eur', sa.Numeric(18, 2)),          # E1-9|67e
        sa.Column('coal_customer_revenue_pct', sa.Numeric(6, 3)),               # E1-9|67e
        sa.Column('oil_customer_revenue_pct', sa.Numeric(6, 3)),                # E1-9|67e
        sa.Column('gas_customer_revenue_pct', sa.Numeric(6, 3)),                # E1-9|67e
        sa.Column('transition_risk_revenue_pct', sa.Numeric(6, 3)),             # E1-9|AR76
        # Stranded assets (E1-9|AR73a, AR73b)
        sa.Column('stranded_assets_estimated_eur', sa.Numeric(18, 2)),    # E1-9|AR73a
        sa.Column('stranded_assets_pct_of_transition_risk', sa.Numeric(6, 3)), # E1-9|AR73a
        sa.Column('re_assets_internal_energy_estimate_eur', sa.Numeric(18, 2)), # E1-9|AR73b
        # ETS allowances (E1-9|AR74c)
        sa.Column('ets_allowances_scope1_count', sa.Integer()),           # E1-9|AR74c
        sa.Column('ets_allowances_stored_beginning_count', sa.Integer()), # E1-9|AR74c
        sa.Column('potential_liabilities_carbon_credits_eur', sa.Numeric(18, 2)), # E1-9|AR74d
        sa.Column('monetised_scope1_scope2_ghg_eur', sa.Numeric(18, 2)), # E1-9|AR74e
        sa.Column('monetised_total_ghg_eur', sa.Numeric(18, 2)),         # E1-9|AR74e
        # Climate opportunities (E1-9|69a, 69b) — BENCHMARK
        sa.Column('cost_savings_climate_mitigation_eur', sa.Numeric(18, 2)), # E1-9|69a BENCH
        sa.Column('cost_savings_climate_adaptation_eur', sa.Numeric(18, 2)), # E1-9|69a BENCH
        sa.Column('low_carbon_market_size_potential_eur', sa.Numeric(18, 2)),# E1-9|69b BENCH
        sa.Column('net_revenue_change_low_carbon_eur', sa.Numeric(18, 2)),   # E1-9|69b BENCH
        *_common('esrs_e1_financial_effects'),
    )

    # ======================================================================
    # 7. esrs_e2_pollution  —  ESRS E2-4, E2-5, E2-6
    # ======================================================================
    op.create_table(
        'esrs_e2_pollution',
        # ---- Air emissions (E2-4|28a, Table/mass, SFDR) ----
        # EFRAG IG3 requires by pollutant per medium; key named columns:
        sa.Column('air_nox_tonnes', sa.Numeric(14, 4)),          # E2-4|28a SFDR
        sa.Column('air_sox_tonnes', sa.Numeric(14, 4)),          # E2-4|28a SFDR
        sa.Column('air_pm10_tonnes', sa.Numeric(14, 4)),         # E2-4|28a SFDR
        sa.Column('air_pm25_tonnes', sa.Numeric(14, 4)),         # E2-4|28a SFDR
        sa.Column('air_voc_tonnes', sa.Numeric(14, 4)),          # E2-4|28a SFDR
        sa.Column('air_hap_tonnes', sa.Numeric(14, 4)),          # E2-4|28a — hazardous air
        sa.Column('air_pah_tonnes', sa.Numeric(14, 4)),          # E2-4|28a
        sa.Column('air_mercury_hg_kg', sa.Numeric(14, 4)),
        sa.Column('air_lead_pb_kg', sa.Numeric(14, 4)),
        sa.Column('air_dioxins_furans_grams', sa.Numeric(14, 6)),
        sa.Column('air_ammonia_nh3_tonnes', sa.Numeric(14, 4)),
        sa.Column('air_co_tonnes', sa.Numeric(14, 4)),
        sa.Column('air_sf6_kg', sa.Numeric(14, 4)),
        sa.Column('air_other_pollutants_tonnes', sa.Numeric(14, 4)),
        sa.Column('air_emissions_full_table', JSONB()),           # E2-4|28a full table
        # ---- Water emissions (E2-4|28a, Table/mass, SFDR) ----
        sa.Column('water_nitrogen_tonnes', sa.Numeric(14, 4)),   # E2-4|28a SFDR
        sa.Column('water_phosphorus_tonnes', sa.Numeric(14, 4)), # E2-4|28a SFDR
        sa.Column('water_heavy_metals_kg', sa.Numeric(14, 4)),
        sa.Column('water_organic_pollutants_cod_tonnes', sa.Numeric(14, 4)),
        sa.Column('water_hydrocarbons_oil_tonnes', sa.Numeric(14, 4)),
        sa.Column('water_pesticides_kg', sa.Numeric(14, 4)),
        sa.Column('water_pharmaceuticals_kg', sa.Numeric(14, 4)),
        sa.Column('water_other_pollutants_tonnes', sa.Numeric(14, 4)),
        sa.Column('water_in_water_risk_area_pct', sa.Numeric(6, 3)), # E2-4|AR23c
        sa.Column('water_in_high_stress_area_pct', sa.Numeric(6, 3)),# E2-4|AR23c
        sa.Column('water_emissions_full_table', JSONB()),              # E2-4|28a full table
        # ---- Soil emissions (E2-4|28a, Table/mass, SFDR) ----
        sa.Column('soil_total_pollutants_tonnes', sa.Numeric(14, 4)),
        sa.Column('soil_hazardous_waste_deposited_tonnes', sa.Numeric(14, 4)),
        sa.Column('soil_in_water_risk_area_pct', sa.Numeric(6, 3)),  # E2-4|AR23c
        sa.Column('soil_in_high_stress_area_pct', sa.Numeric(6, 3)), # E2-4|AR23c
        sa.Column('soil_emissions_full_table', JSONB()),
        # ---- Microplastics (E2-4|28b) ----
        sa.Column('microplastics_generated_kg', sa.Numeric(14, 4)),  # E2-4|28b
        sa.Column('microplastics_used_kg', sa.Numeric(14, 4)),        # E2-4|28b
        # ---- Substances of concern (E2-5|34, 35) ----
        sa.Column('substances_of_concern_generated_or_used_tonnes',
                  sa.Numeric(14, 4)),   # E2-5|34
        sa.Column('substances_of_concern_emitted_tonnes', sa.Numeric(14, 4)),  # E2-5|34
        sa.Column('substances_of_concern_in_products_tonnes', sa.Numeric(14, 4)),# E2-5|34
        sa.Column('substances_of_concern_in_services_tonnes', sa.Numeric(14, 4)),# E2-5|35
        sa.Column('substances_of_concern_by_hazard_class', JSONB()),  # E2-5|34
        sa.Column('svhc_generated_or_used_tonnes', sa.Numeric(14, 4)),  # E2-5|35 SVHC
        sa.Column('svhc_emitted_tonnes', sa.Numeric(14, 4)),            # E2-5|35
        sa.Column('svhc_in_products_tonnes', sa.Numeric(14, 4)),        # E2-5|35
        sa.Column('svhc_in_services_tonnes', sa.Numeric(14, 4)),        # E2-5|35
        sa.Column('svhc_by_hazard_class', JSONB()),                     # E2-5|35
        # ---- Financial effects (E2-6) ----
        sa.Column('pollution_financial_effects_risk_eur', sa.Numeric(14, 2)),  # E2-6|39a
        sa.Column('revenue_products_with_substances_of_concern_pct',
                  sa.Numeric(6, 3)),  # E2-6|40a
        sa.Column('revenue_products_with_svhc_pct', sa.Numeric(6, 3)),         # E2-6|40a
        sa.Column('pollution_opex_major_incidents_eur', sa.Numeric(14, 2)),    # E2-6|40b
        sa.Column('pollution_capex_major_incidents_eur', sa.Numeric(14, 2)),   # E2-6|40b
        sa.Column('environmental_remediation_provisions_eur', sa.Numeric(14, 2)),# E2-6|40c
        *_common('esrs_e2_pollution'),
    )

    # ======================================================================
    # 8. esrs_e3_water  —  ESRS E3-4, E3-5
    # ======================================================================
    op.create_table(
        'esrs_e3_water',
        # ---- Water consumption (E3-4|28a-28d) ----
        sa.Column('total_water_consumption_m3', sa.Numeric(18, 3)),          # E3-4|28a
        sa.Column('water_consumption_at_water_risk_m3', sa.Numeric(18, 3)), # E3-4|28b SFDR
        sa.Column('total_water_recycled_reused_m3', sa.Numeric(18, 3)),     # E3-4|28c SFDR
        sa.Column('total_water_stored_m3', sa.Numeric(18, 3)),              # E3-4|28d
        sa.Column('changes_in_water_storage_m3', sa.Numeric(18, 3)),        # E3-4|28d
        # ---- Water intensity (E3-4|29, AR31) ----
        sa.Column('water_intensity_m3_per_net_revenue', sa.Numeric(14, 6)), # E3-4|29 SFDR
        sa.Column('additional_water_intensity_ratio', sa.Numeric(14, 6)),   # E3-4|AR31
        sa.Column('water_intensity_denominator', sa.String(100)),
        # ---- Water withdrawals and discharges (E3-4|AR32) ----
        sa.Column('total_water_withdrawals_m3', sa.Numeric(18, 3)),         # E3-4|AR32
        sa.Column('withdrawal_surface_water_m3', sa.Numeric(18, 3)),
        sa.Column('withdrawal_groundwater_m3', sa.Numeric(18, 3)),
        sa.Column('withdrawal_seawater_desalinated_m3', sa.Numeric(18, 3)),
        sa.Column('withdrawal_produced_process_water_m3', sa.Numeric(18, 3)),
        sa.Column('withdrawal_third_party_municipal_m3', sa.Numeric(18, 3)),
        sa.Column('withdrawal_freshwater_tds_below_1000_m3', sa.Numeric(18, 3)),
        sa.Column('withdrawal_other_water_tds_above_1000_m3', sa.Numeric(18, 3)),
        sa.Column('withdrawal_high_stress_areas_m3', sa.Numeric(18, 3)),
        sa.Column('withdrawal_high_stress_areas_pct', sa.Numeric(6, 3)),
        sa.Column('total_water_discharges_m3', sa.Numeric(18, 3)),          # E3-4|AR32
        sa.Column('discharge_surface_water_m3', sa.Numeric(18, 3)),
        sa.Column('discharge_groundwater_m3', sa.Numeric(18, 3)),
        sa.Column('discharge_seawater_m3', sa.Numeric(18, 3)),
        sa.Column('discharge_third_party_m3', sa.Numeric(18, 3)),
        sa.Column('discharge_freshwater_treated_pct', sa.Numeric(6, 3)),
        # Sector table (E3-4|AR30)
        sa.Column('water_consumption_by_sector', JSONB()),                  # E3-4|AR30
        sa.Column('water_stress_methodology', sa.String(200)),
        # ---- Financial effects (E3-5|33a) ----
        sa.Column('water_financial_effects_risk_eur', sa.Numeric(14, 2)),   # E3-5|33a
        *_common('esrs_e3_water'),
    )

    # ======================================================================
    # 9. esrs_e4_biodiversity  —  ESRS E4-3, E4-5, E4-6
    # ======================================================================
    op.create_table(
        'esrs_e4_biodiversity',
        # ---- Biodiversity offset costs (E4-3|28b ii) ----
        sa.Column('biodiversity_offset_financing_costs_eur', sa.Numeric(14, 2)), # E4-3|28b(ii)
        # ---- Sites in/near protected areas (E4-5|35) ----
        sa.Column('sites_in_near_protected_or_kba_count', sa.Integer()),   # E4-5|35
        sa.Column('sites_in_near_protected_or_kba_area_ha', sa.Numeric(14, 4)), # E4-5|35
        # ---- Land use metrics (E4-5|AR34) ----
        sa.Column('total_land_use_area_ha', sa.Numeric(14, 4)),             # E4-5|AR34a
        sa.Column('sealed_area_ha', sa.Numeric(14, 4)),                     # E4-5|AR34b
        sa.Column('nature_oriented_area_on_site_ha', sa.Numeric(14, 4)),    # E4-5|AR34c
        sa.Column('nature_oriented_area_off_site_ha', sa.Numeric(14, 4)),   # E4-5|AR34d
        # ---- Invasive alien species (E4-5|AR32) ----
        sa.Column('invasive_alien_species_count', sa.Integer()),             # E4-5|AR32
        sa.Column('invasive_alien_species_area_ha', sa.Numeric(14, 4)),     # E4-5|AR32
        # ---- Species data (voluntary / additional KPIs) ----
        sa.Column('threatened_species_affected_count', sa.Integer()),
        sa.Column('threatened_species_iucn_red_list_count', sa.Integer()),
        sa.Column('endemic_species_affected_count', sa.Integer()),
        # ---- BNG metrics (UK BNG Metric 4.0) ----
        sa.Column('habitat_units_baseline', sa.Numeric(14, 4)),
        sa.Column('habitat_units_current', sa.Numeric(14, 4)),
        sa.Column('hedgerow_units_baseline', sa.Numeric(14, 4)),
        sa.Column('watercourse_units_baseline', sa.Numeric(14, 4)),
        sa.Column('bng_net_gain_pct', sa.Numeric(6, 3)),
        # ---- TNFD LEAP progress flags ----
        sa.Column('tnfd_locate_complete', sa.Boolean(), server_default='false'),
        sa.Column('tnfd_evaluate_complete', sa.Boolean(), server_default='false'),
        sa.Column('tnfd_assess_complete', sa.Boolean(), server_default='false'),
        sa.Column('tnfd_prepare_complete', sa.Boolean(), server_default='false'),
        sa.Column('tnfd_high_priority_locations', JSONB()),
        # ---- Financial effects (E4-6|45a) ----
        sa.Column('biodiversity_financial_effects_risk_eur', sa.Numeric(14, 2)), # E4-6|45a
        sa.Column('ecosystem_services_value_at_risk_eur', sa.Numeric(14, 2)),
        *_common('esrs_e4_biodiversity'),
    )

    # ======================================================================
    # 10. esrs_e5_circular  —  ESRS E5-4, E5-5, E5-6
    # ======================================================================
    op.create_table(
        'esrs_e5_circular',
        # ---- Resource inflows (E5-4|31) ----
        sa.Column('total_materials_consumed_tonnes', sa.Numeric(18, 3)),       # E5-4|31a
        sa.Column('biological_materials_biofuels_pct', sa.Numeric(6, 3)),      # E5-4|31b
        sa.Column('secondary_reused_recycled_materials_tonnes',
                  sa.Numeric(18, 3)),  # E5-4|31c
        sa.Column('secondary_reused_recycled_materials_pct', sa.Numeric(6, 3)),# E5-4|31c
        sa.Column('critical_raw_materials_tonnes', sa.Numeric(18, 3)),
        sa.Column('water_as_input_m3', sa.Numeric(18, 3)),
        # ---- Products / recyclability (E5-5|36a, 36c) ----
        sa.Column('products_expected_durability_vs_industry_pct', JSONB()),    # E5-5|36a table
        sa.Column('recyclable_content_in_products_pct', sa.Numeric(6, 3)),    # E5-5|36c
        sa.Column('recyclable_content_in_packaging_pct', sa.Numeric(6, 3)),   # E5-5|36c
        # ---- Waste (E5-5|37) ----
        sa.Column('total_waste_generated_tonnes', sa.Numeric(18, 3)),          # E5-5|37a
        # Hazardous waste diverted from disposal (E5-5|37b i-iii)
        sa.Column('hazardous_waste_diverted_from_disposal_tonnes',
                  sa.Numeric(18, 3)),  # E5-5|37b
        sa.Column('hazardous_waste_diverted_reuse_tonnes', sa.Numeric(18, 3)), # E5-5|37b(i)
        sa.Column('hazardous_waste_diverted_recycling_tonnes', sa.Numeric(18, 3)),# E5-5|37b(ii)
        sa.Column('hazardous_waste_diverted_other_recovery_tonnes',
                  sa.Numeric(18, 3)),  # E5-5|37b(iii)
        # Non-hazardous waste diverted from disposal (E5-5|37b i-iii)
        sa.Column('non_hazardous_waste_diverted_from_disposal_tonnes',
                  sa.Numeric(18, 3)),  # E5-5|37b
        sa.Column('non_hazardous_waste_diverted_reuse_tonnes', sa.Numeric(18, 3)),
        sa.Column('non_hazardous_waste_diverted_recycling_tonnes', sa.Numeric(18, 3)),
        sa.Column('non_hazardous_waste_diverted_other_recovery_tonnes',
                  sa.Numeric(18, 3)),
        # Hazardous waste directed to disposal (E5-5|37c i-iii)
        sa.Column('hazardous_waste_directed_to_disposal_tonnes',
                  sa.Numeric(18, 3)),  # E5-5|37c
        sa.Column('hazardous_waste_incinerated_tonnes', sa.Numeric(18, 3)),    # E5-5|37c(i)
        sa.Column('hazardous_waste_landfilled_tonnes', sa.Numeric(18, 3)),     # E5-5|37c(ii)
        sa.Column('hazardous_waste_other_disposal_tonnes', sa.Numeric(18, 3)), # E5-5|37c(iii)
        # Non-hazardous waste directed to disposal (E5-5|37c i-iii)
        sa.Column('non_hazardous_waste_directed_to_disposal_tonnes',
                  sa.Numeric(18, 3)),  # E5-5|37c
        sa.Column('non_hazardous_waste_incinerated_tonnes', sa.Numeric(18, 3)),
        sa.Column('non_hazardous_waste_landfilled_tonnes', sa.Numeric(18, 3)),
        sa.Column('non_hazardous_waste_other_disposal_tonnes', sa.Numeric(18, 3)),
        # Non-recycled / total waste totals (E5-5|37d SFDR)
        sa.Column('non_recycled_waste_tonnes', sa.Numeric(18, 3)),             # E5-5|37d SFDR
        sa.Column('non_recycled_waste_pct', sa.Numeric(6, 3)),                # E5-5|37d SFDR
        sa.Column('total_hazardous_waste_tonnes', sa.Numeric(18, 3)),         # E5-5|39 SFDR
        sa.Column('total_radioactive_waste_tonnes', sa.Numeric(18, 3)),       # E5-5|39 SFDR
        # ---- Financial effects (E5-6|43a) ----
        sa.Column('resource_use_financial_effects_risk_eur', sa.Numeric(14, 2)), # E5-6|43a
        sa.Column('circular_economy_opportunity_eur', sa.Numeric(14, 2)),
        *_common('esrs_e5_circular'),
    )

    # ======================================================================
    # 11. esrs_s1_workforce  —  ESRS S1-6 to S1-17
    # ======================================================================
    op.create_table(
        'esrs_s1_workforce',
        # ---- S1-6: Employees (par 50, 51, 52) ----
        sa.Column('employees_headcount', sa.Integer()),                     # S1-6|50a Table A
        sa.Column('employees_headcount_average', sa.Integer()),             # S1-6|50a Table A
        sa.Column('employees_headcount_by_country', JSONB()),              # S1-6|50a Table B
        sa.Column('employees_headcount_by_gender_contract', JSONB()),      # S1-6|50b+51 Table C
        sa.Column('employees_who_left_count', sa.Integer()),               # S1-6|50c
        sa.Column('employee_turnover_rate_pct', sa.Numeric(5, 2)),         # S1-6|50c
        sa.Column('employees_full_time_headcount', sa.Integer()),          # S1-6|52a Table D
        sa.Column('employees_full_time_fte', sa.Numeric(10, 2)),           # S1-6|52a Table D
        sa.Column('employees_part_time_headcount', sa.Integer()),          # S1-6|52b Table D
        sa.Column('employees_part_time_fte', sa.Numeric(10, 2)),           # S1-6|52b Table D
        # Breakdown by gender (from Table C — standard decomposition)
        sa.Column('employees_male', sa.Integer()),
        sa.Column('employees_female', sa.Integer()),
        sa.Column('employees_non_binary', sa.Integer()),
        sa.Column('employees_gender_undisclosed', sa.Integer()),
        # Breakdown by contract type (permanent / temporary)
        sa.Column('employees_permanent', sa.Integer()),
        sa.Column('employees_temporary', sa.Integer()),
        # ---- S1-7: Non-employees (par 55a) ----
        sa.Column('non_employees_total', sa.Numeric(10, 2)),               # S1-7|55a
        sa.Column('non_employees_self_employed', sa.Numeric(10, 2)),       # S1-7|55a
        sa.Column('non_employees_staffing_agency', sa.Numeric(10, 2)),     # S1-7|55a
        sa.Column('non_employees_other', sa.Numeric(10, 2)),               # S1-7|55a
        # ---- S1-8: Collective bargaining (par 60, 63) ----
        sa.Column('employees_covered_by_cba_pct', sa.Numeric(5, 2)),      # S1-8|60a
        sa.Column('employees_cba_coverage_by_country', JSONB()),          # S1-8|60b Table
        sa.Column('employees_cba_outside_eea_by_region', JSONB()),        # S1-8|60c Table
        sa.Column('employees_in_eea_covered_by_representatives_pct',
                  sa.Numeric(5, 2)),   # S1-8|63a
        # ---- S1-9: Diversity (par 66) ----
        sa.Column('top_management_headcount', sa.Integer()),               # S1-9|66a
        sa.Column('women_top_management_pct', sa.Numeric(5, 2)),          # S1-9|66a
        sa.Column('employees_under_30_count', sa.Integer()),               # S1-9|66b
        sa.Column('employees_under_30_pct', sa.Numeric(5, 2)),            # S1-9|66b
        sa.Column('employees_30_50_count', sa.Integer()),                  # S1-9|66b
        sa.Column('employees_30_50_pct', sa.Numeric(5, 2)),               # S1-9|66b
        sa.Column('employees_over_50_count', sa.Integer()),                # S1-9|66b
        sa.Column('employees_over_50_pct', sa.Numeric(5, 2)),             # S1-9|66b
        # ---- S1-10: Adequate wages (par 70, 71) ----
        sa.Column('employees_below_adequate_wage_pct', JSONB()),           # S1-10|70 Table E
        sa.Column('non_employees_below_adequate_wage_pct', JSONB()),       # S1-10|71 Table E
        # ---- S1-11: Social protection (par 75) ----
        sa.Column('social_protection_by_country_event_type', JSONB()),    # S1-11|75 Table
        sa.Column('social_protection_sickness_pct', sa.Numeric(5, 2)),
        sa.Column('social_protection_unemployment_pct', sa.Numeric(5, 2)),
        sa.Column('social_protection_work_accident_pct', sa.Numeric(5, 2)),
        sa.Column('social_protection_parental_pct', sa.Numeric(5, 2)),
        sa.Column('social_protection_retirement_pct', sa.Numeric(5, 2)),
        sa.Column('social_protection_disability_pct', sa.Numeric(5, 2)),
        # ---- S1-12: Persons with disabilities (par 79, 80) ----
        sa.Column('employees_with_disability_pct', sa.Numeric(5, 2)),     # S1-12|79
        sa.Column('employees_with_disability_by_gender', JSONB()),        # S1-12|80 Table
        # ---- S1-13: Training (par 83, 84, 85) ----
        sa.Column('employees_performance_career_review_pct', JSONB()),    # S1-13|83a Table F
        sa.Column('avg_training_hours_per_employee', sa.Numeric(7, 2)),   # S1-13|83b Table G
        sa.Column('avg_training_hours_by_gender', JSONB()),               # S1-13|84 Table G
        sa.Column('pct_employees_career_review_by_gender', JSONB()),      # S1-13|84 Table G
        sa.Column('non_employees_career_review_pct', sa.Numeric(5, 2)),  # S1-13|85 Table G
        # ---- S1-14: Health and safety (par 88, 89, 90, AR82, AR94) ----
        sa.Column('h_s_management_system_coverage_pct', sa.Numeric(5, 2)),# S1-14|88a
        # Fatalities — employees
        sa.Column('fatalities_work_injury_employees', sa.Integer()),       # S1-14|88b, AR82
        sa.Column('fatalities_work_ill_health_employees', sa.Integer()),   # S1-14|AR82
        sa.Column('fatalities_total_own_workforce', sa.Integer()),         # S1-14|88b
        # Fatalities — other workers on site (contractors etc.)
        sa.Column('fatalities_work_injury_other_workers', sa.Integer()),   # S1-14|AR82
        sa.Column('fatalities_work_ill_health_other_workers', sa.Integer()),# S1-14|AR82
        sa.Column('fatalities_total_other_workers', sa.Integer()),         # S1-14|88b
        # Recordable accidents (own workforce)
        sa.Column('recordable_accidents_own_workforce_count', sa.Integer()),# S1-14|88c
        sa.Column('recordable_accidents_own_workforce_rate', sa.Numeric(8, 4)),# S1-14|88c
        # Work-related ill health (own workforce)
        sa.Column('recordable_ill_health_cases_employees', sa.Integer()),  # S1-14|88d
        sa.Column('recordable_ill_health_cases_former_employees',
                  sa.Integer()),  # S1-14|AR94
        # Days lost
        sa.Column('days_lost_own_workforce', sa.Integer()),                # S1-14|88e
        sa.Column('days_lost_other_workers', sa.Integer()),                # S1-14|89
        # Non-employees H&S data (S1-14|89)
        sa.Column('recordable_ill_health_non_employees', sa.Integer()),    # S1-14|89
        sa.Column('h_s_management_legal_req_coverage_pct', sa.Numeric(5, 2)),# S1-14|90
        # ---- S1-15: Work-life balance (par 93) ----
        sa.Column('employees_entitled_family_leave_pct', sa.Numeric(5, 2)),# S1-15|93a
        sa.Column('employees_who_took_family_leave_pct', sa.Numeric(5, 2)),# S1-15|93b
        sa.Column('family_leave_taken_by_gender', JSONB()),               # S1-15|93b Table
        # ---- S1-16: Compensation (par 97, 98, 99) ----
        sa.Column('gender_pay_gap_pct', sa.Numeric(6, 2)),                # S1-16|97a SFDR/BENCH
        sa.Column('annual_total_remuneration_ratio', sa.Numeric(8, 2)),   # S1-16|97b SFDR
        # CEO pay ratio = CEO total / median employee total
        sa.Column('gender_pay_gap_by_category_country', JSONB()),         # S1-16|98 Table
        sa.Column('gender_pay_gap_by_component', JSONB()),                # S1-16|98 Table
        sa.Column('remuneration_ratio_ppp_adjusted', sa.Numeric(8, 2)),  # S1-16|99
        # ---- S1-17: Incidents, complaints, human rights (par 103, 104, AR106) ----
        sa.Column('discrimination_incidents_count', JSONB()),             # S1-17|103a Table I
        sa.Column('complaints_internal_channels_count', sa.Integer()),    # S1-17|103b
        sa.Column('complaints_oecd_ncp_count', sa.Integer()),             # S1-17|103b
        sa.Column('fines_penalties_hr_violations_eur', sa.Numeric(14, 2)),# S1-17|103c
        sa.Column('severe_human_rights_incidents_count', sa.Integer()),   # S1-17|104a SFDR/BENCH
        sa.Column('severe_hr_non_respect_un_principles_count', sa.Integer()), # S1-17|104a
        sa.Column('fines_severe_hr_incidents_eur', sa.Numeric(14, 2)),    # S1-17|104b
        sa.Column('severe_hr_remedy_secured_count', sa.Integer()),        # S1-17|AR106
        *_common('esrs_s1_workforce'),
    )
    op.create_index('ix_esrs_s1_workforce_entity_year', 'esrs_s1_workforce',
                    ['entity_registry_id', 'reporting_year'])

    # ======================================================================
    # 12. esrs_g1_conduct  —  ESRS G1-1 to G1-6
    # ======================================================================
    op.create_table(
        'esrs_g1_conduct',
        # ---- G1-1: Policies (binary — yes/no) ----
        sa.Column('code_of_conduct_published', sa.Boolean()),
        sa.Column('anti_corruption_policy_published', sa.Boolean()),
        sa.Column('anti_bribery_policy_published', sa.Boolean()),
        sa.Column('whistleblowing_mechanism_exists', sa.Boolean()),
        sa.Column('whistleblowing_anonymous_available', sa.Boolean()),
        sa.Column('supplier_code_of_conduct_published', sa.Boolean()),
        # ---- G1-3: Anti-corruption training (par 21b, AR8) ----
        sa.Column('functions_at_risk_covered_by_training_pct', sa.Numeric(5, 2)), # G1-3|21b
        sa.Column('anti_corruption_training_table', JSONB()),                      # G1-3|AR8 Table
        # Training detail (voluntary expanded)
        sa.Column('governance_body_anti_corruption_training_pct', sa.Numeric(5, 2)),
        sa.Column('employees_anti_corruption_training_pct', sa.Numeric(5, 2)),
        # ---- G1-4: Incidents (par 24, 25) ----
        sa.Column('convictions_anticorruption_antibribery_count', sa.Integer()),  # G1-4|24a SFDR
        sa.Column('fines_anticorruption_antibribery_eur', sa.Numeric(14, 2)),    # G1-4|24a SFDR
        sa.Column('confirmed_corruption_incidents_count', sa.Integer()),          # G1-4|25a
        sa.Column('employees_dismissed_corruption_count', sa.Integer()),          # G1-4|25b
        sa.Column('contracts_terminated_corruption_count', sa.Integer()),         # G1-4|25c
        # ---- G1-5: Political influence (par 29b, AR12) ----
        sa.Column('financial_political_contributions_eur', sa.Numeric(14, 2)),   # G1-5|29bi
        sa.Column('in_kind_political_contributions_eur', sa.Numeric(14, 2)),     # G1-5|29bi
        sa.Column('political_contributions_table', JSONB()),                      # G1-5|29bii Table
        sa.Column('lobbying_expenses_eur', sa.Numeric(14, 2)),                   # G1-5|AR12a
        sa.Column('lobbying_association_membership_fees_eur', sa.Numeric(14, 2)),# G1-5|AR12b
        sa.Column('eu_transparency_register_id', sa.String(100)),
        # ---- G1-6: Payment practices (par 33) ----
        sa.Column('avg_days_to_pay_invoice', sa.Integer()),                       # G1-6|33a
        sa.Column('payments_aligned_standard_terms_pct', sa.Numeric(5, 2)),      # G1-6|33b
        sa.Column('outstanding_legal_proceedings_late_payment_count', sa.Integer()), # G1-6|33c
        *_common('esrs_g1_conduct'),
    )

    # ======================================================================
    # 13. issb_s1_general  —  IFRS S1 General Requirements taxonomy
    # ======================================================================
    op.create_table(
        'issb_s1_general',
        # Governance (IFRS S1 §§14-24)
        sa.Column('governance_body_oversees_sustainability_risks', sa.Boolean()),
        sa.Column('governance_body_sustainability_expertise', sa.Boolean()),
        sa.Column('governance_sustainability_oversight_mechanism', sa.Text()),
        sa.Column('management_role_in_sustainability', sa.Text()),
        sa.Column('sustainability_committee_exists', sa.Boolean()),
        sa.Column('sustainability_integrated_in_remuneration', sa.Boolean()),
        sa.Column('sustainability_pay_link_description', sa.Text()),
        # Strategy (IFRS S1 §§25-41)
        sa.Column('short_term_horizon_years', sa.Integer()),      # e.g. 1
        sa.Column('medium_term_horizon_years', sa.Integer()),     # e.g. 5
        sa.Column('long_term_horizon_years', sa.Integer()),       # e.g. 30
        sa.Column('sustainability_risks_opportunities_identified', JSONB()),
        # list of {topic, category, type risk/opportunity, time_horizon, magnitude}
        sa.Column('current_financial_effects_description', sa.Text()),
        sa.Column('anticipated_financial_effects_description', sa.Text()),
        sa.Column('strategy_adjusted_for_sustainability', sa.Boolean()),
        sa.Column('resilience_assessment_conducted', sa.Boolean()),
        sa.Column('resilience_assessment_methodology', sa.Text()),
        # Risk management (IFRS S1 §§42-45)
        sa.Column('sustainability_risk_process_description', sa.Text()),
        sa.Column('sustainability_risk_integrated_in_erm', sa.Boolean()),
        sa.Column('sustainability_risk_appetite_defined', sa.Boolean()),
        sa.Column('sustainability_risk_register_exists', sa.Boolean()),
        # Metrics and targets (IFRS S1 §§46-51)
        sa.Column('cross_industry_metrics_reported', JSONB()),
        # list of metric codes with values
        sa.Column('industry_based_metrics_sasb_standard', sa.String(200)),
        sa.Column('entity_specific_metrics', JSONB()),
        sa.Column('sustainability_targets_count', sa.Integer()),
        # SASB industry metrics (free-form JSONB per industry)
        sa.Column('sasb_metrics', JSONB()),
        # Connectivity with financial statements
        sa.Column('sustainability_linked_to_fs_disclosed', sa.Boolean()),
        sa.Column('sustainability_fs_linkage_description', sa.Text()),
        *_common('issb_s1_general'),
    )

    # ======================================================================
    # 14. issb_s2_climate  —  IFRS S2 Climate-Related Disclosures (full taxonomy)
    # ======================================================================
    op.create_table(
        'issb_s2_climate',
        # ---- Governance (S2 §§14-24) ----
        sa.Column('board_climate_oversight_mechanism', sa.Text()),
        sa.Column('board_climate_expertise', sa.Boolean()),
        sa.Column('management_climate_role', sa.Text()),
        sa.Column('executive_climate_incentives', sa.Boolean()),
        sa.Column('executive_climate_incentive_pct_of_variable', sa.Numeric(5, 2)),
        # ---- Strategy (S2 §§25-41) ----
        sa.Column('short_term_horizon_years', sa.Integer()),
        sa.Column('medium_term_horizon_years', sa.Integer()),
        sa.Column('long_term_horizon_years', sa.Integer()),
        sa.Column('physical_risks_identified', JSONB()),
        # [{hazard, acute/chronic, value_chain_position, time_horizon, magnitude}]
        sa.Column('transition_risks_identified', JSONB()),
        # [{category_tcfd, description, time_horizon, magnitude}]
        sa.Column('climate_opportunities_identified', JSONB()),
        # [{description, time_horizon, financial_effect_eur}]
        sa.Column('climate_resilience_assessment_conducted', sa.Boolean()),
        sa.Column('climate_scenarios_used', JSONB()),
        # ['IEA_NZE', 'IEA_APS', 'NGFS_NZ2050', 'NGFS_DT', 'RCP2.6', 'RCP4.5', 'RCP8.5']
        sa.Column('scenario_time_horizons', JSONB()),
        sa.Column('transition_plan_in_place', sa.Boolean()),
        sa.Column('transition_plan_net_zero_year', sa.Integer()),
        # ---- Risk management (S2 §§42-44) ----
        sa.Column('climate_risk_integrated_in_erm', sa.Boolean()),
        sa.Column('climate_risk_identification_process', sa.Text()),
        sa.Column('scenario_analysis_frequency', sa.String(50)),
        # ---- Cross-industry metric category 1: GHG (S2 App B §B1-B3) ----
        sa.Column('scope1_gross_tco2e', sa.Numeric(18, 3)),        # S2 B1
        sa.Column('scope2_location_based_tco2e', sa.Numeric(18, 3)),# S2 B2
        sa.Column('scope2_market_based_tco2e', sa.Numeric(18, 3)), # S2 B2
        sa.Column('scope3_total_tco2e', sa.Numeric(18, 3)),        # S2 B3
        sa.Column('scope3_by_category', JSONB()),                  # S2 B3: {cat1..cat15}
        sa.Column('ghg_protocol_standard_used', sa.String(50)),
        sa.Column('gwp_standard', sa.String(10)),
        # Link to ESRS table for GHG detail
        sa.Column('esrs_e1_ghg_id', UUID(as_uuid=True)),           # FK to esrs_e1_ghg_emissions
        # ---- Category 2: Transition risks (S2 B8-B11) ----
        sa.Column('revenue_from_coal_pct', sa.Numeric(6, 3)),      # S2 B8
        sa.Column('revenue_from_oil_and_gas_pct', sa.Numeric(6, 3)),# S2 B9
        sa.Column('revenue_from_other_fossil_pct', sa.Numeric(6, 3)),
        sa.Column('carbon_intensive_revenue_meur', sa.Numeric(18, 2)),
        sa.Column('transition_risk_asset_exposure_meur', sa.Numeric(18, 2)),
        # ---- Category 3: Physical risks (S2 B12-B20) ----
        sa.Column('physical_risk_revenue_pct', sa.Numeric(6, 3)),  # S2 B12
        sa.Column('physical_risk_assets_pct', sa.Numeric(6, 3)),   # S2 B13
        sa.Column('acute_physical_risk_assessed', sa.Boolean(), server_default='false'),
        sa.Column('chronic_physical_risk_assessed', sa.Boolean(), server_default='false'),
        sa.Column('physical_risk_scenarios_used', JSONB()),
        sa.Column('acute_risks_by_hazard', JSONB()),
        # {flood: {assets_eur, revenue_eur}, heat: {...}, cyclone: {...}, ...}
        sa.Column('chronic_risks_by_hazard', JSONB()),
        sa.Column('assets_at_physical_risk_by_location', JSONB()),
        # ---- Category 4: Climate opportunities (S2 B21-B25) ----
        sa.Column('climate_opportunity_revenue_meur', sa.Numeric(18, 2)),   # S2 B21
        sa.Column('climate_opportunity_revenue_pct', sa.Numeric(6, 3)),     # S2 B22
        sa.Column('low_carbon_products_revenue_meur', sa.Numeric(18, 2)),   # S2 B23
        sa.Column('green_revenue_taxonomy_aligned_pct', sa.Numeric(6, 3)), # S2 B24
        sa.Column('climate_adaptation_revenue_meur', sa.Numeric(18, 2)),
        # ---- Category 5: Capital deployment (S2 B26-B27) ----
        sa.Column('climate_total_capex_meur', sa.Numeric(18, 2)),           # S2 B26
        sa.Column('climate_capex_pct_of_total', sa.Numeric(6, 3)),          # S2 B26
        sa.Column('transition_capex_meur', sa.Numeric(18, 2)),              # S2 B27
        sa.Column('physical_risk_adaptation_capex_meur', sa.Numeric(18, 2)),
        sa.Column('climate_opex_meur', sa.Numeric(18, 2)),
        # ---- Category 6: Internal carbon prices (S2 B28-B29) ----
        sa.Column('has_internal_carbon_price', sa.Boolean(), server_default='false'),
        sa.Column('internal_carbon_price_eur_per_tco2e', sa.Numeric(10, 2)),# S2 B28
        sa.Column('internal_carbon_price_scope', sa.String(200)),           # S2 B29
        sa.Column('internal_carbon_price_application', sa.String(200)),
        # ---- Remuneration linkage (S2 additional) ----
        sa.Column('climate_linked_executive_pay_pct_of_variable', sa.Numeric(5, 2)),
        # ---- SASB industry-specific metrics ----
        sa.Column('sasb_industry_standard_applied', sa.String(200)),
        sa.Column('sasb_metrics', JSONB()),
        # ---- Financed emissions (financial institutions) ----
        sa.Column('financed_emissions_total_tco2e', sa.Numeric(18, 3)),
        sa.Column('financed_emissions_methodology', sa.String(100)),  # PCAF
        sa.Column('portfolio_temperature_alignment_c', sa.Numeric(4, 2)),
        sa.Column('green_asset_ratio_pct', sa.Numeric(6, 3)),
        *_common('issb_s2_climate'),
    )
    # FK from issb_s2 → esrs_e1_ghg (nullable cross-reference)
    op.create_foreign_key(
        'fk_issb_s2_esrs_e1_ghg',
        'issb_s2_climate', 'esrs_e1_ghg_emissions',
        ['esrs_e1_ghg_id'], ['id'],
        ondelete='SET NULL')

    op.create_index('ix_issb_s2_entity_year', 'issb_s2_climate',
                    ['entity_registry_id', 'reporting_year'])


def downgrade():
    op.drop_constraint('fk_issb_s2_esrs_e1_ghg', 'issb_s2_climate', type_='foreignkey')
    op.drop_index('ix_issb_s2_entity_year', table_name='issb_s2_climate')
    op.drop_table('issb_s2_climate')
    op.drop_table('issb_s1_general')
    op.drop_table('esrs_g1_conduct')
    op.drop_index('ix_esrs_s1_workforce_entity_year', table_name='esrs_s1_workforce')
    op.drop_table('esrs_s1_workforce')
    op.drop_table('esrs_e5_circular')
    op.drop_table('esrs_e4_biodiversity')
    op.drop_table('esrs_e3_water')
    op.drop_table('esrs_e2_pollution')
    op.drop_table('esrs_e1_financial_effects')
    op.drop_table('esrs_e1_carbon_price')
    op.drop_table('esrs_e1_ghg_removals')
    op.drop_index('ix_esrs_e1_ghg_entity_year', table_name='esrs_e1_ghg_emissions')
    op.drop_table('esrs_e1_ghg_emissions')
    op.drop_index('ix_esrs_e1_energy_entity_year', table_name='esrs_e1_energy')
    op.drop_table('esrs_e1_energy')
    op.drop_table('esrs2_general_disclosures')
