"""
Add Unified Valuation Tables

Revision ID: 010_add_unified_valuation_tables
Revises: 009_add_regulatory_tables
Create Date: 2026-03-01

This migration adds tables for the Unified Valuation Engine module:
- valuation_assets              : Asset register (all asset classes — RE, infrastructure, energy, corporate)
- unified_valuations            : Top-level valuation run metadata and results
- valuation_method_results      : Per-methodology output detail (DCF, Sales Comp, Cost, Income, NAV, etc.)
- valuation_esg_adjustments     : ESG factor adjustments applied to valuations
- valuation_scenarios           : Scenario analysis (base / bull / bear / climate stress)
- nature_assessments            : TNFD/LEAP nature-related financial risk assessments (real estate / land)
- climate_valuation_adjustments : Forward-looking climate risk adjustments (physical + transition)
- valuation_comparable_sales    : Comparable evidence used in sales comparison approaches
- valuation_audit_log           : Immutable audit trail for valuation changes
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '010_add_unified_valuation_tables'
down_revision = '009_add_regulatory_tables'
branch_labels = None
depends_on = None


def upgrade():
    """Create unified valuation tables."""

    # -------------------------------------------------------------------------
    # 1. VALUATION ASSETS  (multi-class asset register)
    # -------------------------------------------------------------------------
    op.create_table(
        'valuation_assets',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('asset_reference', sa.String(100)),                   # internal reference / UPRN / GPIN
        sa.Column('asset_name', sa.String(255), nullable=False),
        sa.Column('asset_class', sa.String(50), nullable=False),        # real_estate | infrastructure | energy | corporate_equity | corporate_debt | private_equity | natural_capital
        sa.Column('asset_sub_class', sa.String(50)),                    # office | retail | industrial | residential | hotel | data_centre | wind_farm | solar_farm | coal_plant | gas_plant | timberland | ...

        # Location
        sa.Column('address', sa.Text),
        sa.Column('postcode', sa.String(20)),
        sa.Column('city', sa.String(100)),
        sa.Column('country_iso', sa.String(3), nullable=False),
        sa.Column('region', sa.String(100)),
        sa.Column('latitude', sa.Numeric(9, 6)),
        sa.Column('longitude', sa.Numeric(9, 6)),

        # Physical characteristics
        sa.Column('gross_internal_area_m2', sa.Numeric(10, 2)),
        sa.Column('net_internal_area_m2', sa.Numeric(10, 2)),
        sa.Column('site_area_ha', sa.Numeric(10, 4)),
        sa.Column('year_built', sa.Integer),
        sa.Column('year_last_refurbished', sa.Integer),
        sa.Column('number_of_units', sa.Integer),
        sa.Column('installed_capacity_mw', sa.Numeric(10, 3)),          # for energy assets

        # Financial context
        sa.Column('currency', sa.String(3), default='GBP'),
        sa.Column('book_value', sa.Numeric(15, 2)),
        sa.Column('acquisition_date', sa.Date),
        sa.Column('acquisition_cost', sa.Numeric(15, 2)),
        sa.Column('annual_income', sa.Numeric(12, 2)),
        sa.Column('ownership_percentage', sa.Numeric(5, 4), default=1.0),

        # Sustainability
        sa.Column('epc_rating', sa.String(2)),                          # A+ | A | B | C | D | E | F | G
        sa.Column('breeam_rating', sa.String(20)),                      # Outstanding | Excellent | Very Good | Good | Pass
        sa.Column('leed_rating', sa.String(20)),                        # Platinum | Gold | Silver | Certified
        sa.Column('gresb_score', sa.Integer),
        sa.Column('certifications', JSONB),
        sa.Column('green_lease_in_place', sa.Boolean, default=False),
        sa.Column('on_site_renewables_mw', sa.Numeric(8, 3)),

        # Portfolio linkage
        sa.Column('portfolio_id', UUID(as_uuid=True)),

        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.CheckConstraint("asset_class IN ('real_estate','infrastructure','energy','corporate_equity','corporate_debt','private_equity','natural_capital','agriculture','timberland','other')", name='ck_val_assets_class'),
    )
    op.create_index('ix_val_assets_name', 'valuation_assets', ['asset_name'])
    op.create_index('ix_val_assets_class', 'valuation_assets', ['asset_class'])
    op.create_index('ix_val_assets_country', 'valuation_assets', ['country_iso'])
    op.create_index('ix_val_assets_epc', 'valuation_assets', ['epc_rating'])

    # -------------------------------------------------------------------------
    # 2. UNIFIED VALUATIONS  (top-level valuation run)
    # -------------------------------------------------------------------------
    op.create_table(
        'unified_valuations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('asset_id', UUID(as_uuid=True), sa.ForeignKey('valuation_assets.id', ondelete='SET NULL')),
        sa.Column('asset_name', sa.String(255), nullable=False),
        sa.Column('asset_class', sa.String(50), nullable=False),
        sa.Column('valuation_date', sa.Date, nullable=False),
        sa.Column('currency', sa.String(3), default='GBP'),

        # Purpose
        sa.Column('valuation_purpose', sa.String(50), default='market_value'),  # market_value | fair_value | investment_value | insurance_reinstatement | loan_security | gndi | esg_adjusted
        sa.Column('valuation_basis', sa.String(30), default='RICS_Red_Book'),   # RICS_Red_Book | IVSC_IVS | USPAP | TEGoVA | ARICS | AIQS

        # Primary methodology
        sa.Column('primary_method', sa.String(50), nullable=False),    # dcf | income_capitalisation | sales_comparison | cost | nav | multiples | dividend_discount | option_pricing | hybrid
        sa.Column('secondary_methods', JSONB),                          # [method1, method2, ...]

        # Key financial inputs
        sa.Column('passing_rent_pa', sa.Numeric(15, 2)),               # for income-producing RE
        sa.Column('erv_pa', sa.Numeric(15, 2)),                        # Estimated Rental Value
        sa.Column('equivalent_yield_pct', sa.Numeric(5, 4)),
        sa.Column('net_initial_yield_pct', sa.Numeric(5, 4)),
        sa.Column('reversionary_yield_pct', sa.Numeric(5, 4)),
        sa.Column('discount_rate_pct', sa.Numeric(5, 4)),
        sa.Column('terminal_cap_rate_pct', sa.Numeric(5, 4)),
        sa.Column('exit_yield_pct', sa.Numeric(5, 4)),
        sa.Column('noi', sa.Numeric(15, 2)),                           # Net Operating Income
        sa.Column('ebitda', sa.Numeric(15, 2)),                        # for corporate / infrastructure
        sa.Column('wacc', sa.Numeric(5, 4)),

        # Valuation outputs (before ESG adjustments)
        sa.Column('gross_value', sa.Numeric(15, 2), nullable=False),
        sa.Column('gross_value_per_m2', sa.Numeric(12, 2)),
        sa.Column('gross_value_per_unit', sa.Numeric(12, 2)),

        # ESG adjustment
        sa.Column('esg_adjustment_total_pct', sa.Numeric(7, 4)),       # net ESG uplift/discount (positive = premium)
        sa.Column('esg_adjustment_gbp', sa.Numeric(15, 2)),
        sa.Column('esg_adjusted_value', sa.Numeric(15, 2), nullable=False),  # gross_value × (1 + esg_adj)

        # Climate risk adjustment
        sa.Column('physical_risk_discount_pct', sa.Numeric(7, 4)),
        sa.Column('transition_risk_discount_pct', sa.Numeric(7, 4)),
        sa.Column('stranded_asset_discount_pct', sa.Numeric(7, 4)),
        sa.Column('climate_adjusted_value', sa.Numeric(15, 2)),

        # Final value
        sa.Column('final_value', sa.Numeric(15, 2), nullable=False),   # esg_adjusted_value after climate discounts
        sa.Column('value_confidence_pct', sa.Numeric(5, 2)),           # valuer confidence level
        sa.Column('value_range_low', sa.Numeric(15, 2)),
        sa.Column('value_range_high', sa.Numeric(15, 2)),

        # Multi-method reconciliation
        sa.Column('method_weights', JSONB),                             # {dcf: 0.5, income_cap: 0.3, sales_comp: 0.2}
        sa.Column('method_crosscheck', JSONB),                         # {dcf_value: x, income_cap_value: y, sales_comp_value: z}
        sa.Column('reconciliation_notes', sa.Text),

        # Certification (RICS-standard signatures)
        sa.Column('valuer_name', sa.String(100)),
        sa.Column('valuer_mrics_number', sa.String(20)),                # MRICS / FRICS membership number
        sa.Column('valuer_firm', sa.String(100)),
        sa.Column('review_valuer_name', sa.String(100)),                # for independent review
        sa.Column('is_independent', sa.Boolean, default=True),         # RICS PS 2 compliance

        # Validation summary
        sa.Column('validation_summary', JSONB),                        # {methodology, inputs, outputs, quality_flags, warnings}
        sa.Column('status', sa.String(20), default='draft'),
        sa.Column('created_by', UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.CheckConstraint("primary_method IN ('dcf','income_capitalisation','sales_comparison','cost','nav','multiples','dividend_discount','option_pricing','hybrid','residual_land','profits_method')", name='ck_unified_val_method'),
        sa.CheckConstraint("valuation_purpose IN ('market_value','fair_value','investment_value','insurance_reinstatement','loan_security','gndi','esg_adjusted','liquidation_value')", name='ck_unified_val_purpose'),
        sa.CheckConstraint("status IN ('draft','under_review','signed_off','published','superseded','archived')", name='ck_unified_val_status'),
    )
    op.create_index('ix_unified_val_asset', 'unified_valuations', ['asset_id'])
    op.create_index('ix_unified_val_date', 'unified_valuations', ['valuation_date'])
    op.create_index('ix_unified_val_class', 'unified_valuations', ['asset_class'])
    op.create_index('ix_unified_val_method', 'unified_valuations', ['primary_method'])
    op.create_index('ix_unified_val_status', 'unified_valuations', ['status'])

    # -------------------------------------------------------------------------
    # 3. VALUATION METHOD RESULTS  (per-methodology detail)
    # -------------------------------------------------------------------------
    op.create_table(
        'valuation_method_results',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('valuation_id', UUID(as_uuid=True), sa.ForeignKey('unified_valuations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('method', sa.String(50), nullable=False),
        sa.Column('is_primary', sa.Boolean, default=False),
        sa.Column('weight_in_reconciliation', sa.Numeric(4, 3)),        # 0-1

        # Method-specific inputs (JSONB for flexibility across all asset classes)
        sa.Column('inputs', JSONB, nullable=False),                     # Full set of methodology-specific inputs
        # Examples:
        # DCF: {projection_years, revenue_growth_pct, opex_ratio_pct, capex_schedule, exit_cap_rate, wacc, terminal_value}
        # Income Cap: {passing_rent, erv, void_pct, management_fee_pct, capex_reserve, equiv_yield, reversionary_yield}
        # Sales Comparison: {comparable_sales: [{address, date, price_psm, adjustment_pct, adjusted_price}], weighting}
        # Cost: {land_value, construction_cost_psm, professional_fees_pct, contingency_pct, developer_profit_pct, ext_obs}
        # Multiples: {ebitda, ev_ebitda_multiple, net_debt, minority_interest, adjustments}

        # Results
        sa.Column('indicated_value', sa.Numeric(15, 2), nullable=False),
        sa.Column('value_per_m2', sa.Numeric(12, 2)),
        sa.Column('value_per_unit', sa.Numeric(12, 2)),
        sa.Column('irr_pct', sa.Numeric(6, 4)),                        # for DCF
        sa.Column('equity_multiple', sa.Numeric(5, 3)),                 # for DCF / private equity
        sa.Column('implied_cap_rate_pct', sa.Numeric(5, 4)),

        # Sensitivity / range
        sa.Column('value_low', sa.Numeric(15, 2)),
        sa.Column('value_high', sa.Numeric(15, 2)),
        sa.Column('sensitivity_table', JSONB),                          # {variable: [{value, result}]}

        # Cash flow schedule (for DCF)
        sa.Column('cashflow_schedule', JSONB),                          # [{year, revenue, opex, noi, capex, fcf, pv_factor, pv_fcf}]

        # Comparables used (for sales comparison)
        sa.Column('comparables_used', JSONB),                           # [{id, address, date, price, adj_pct, adj_price, weight}]

        sa.Column('methodology_notes', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_val_method_results_valuation', 'valuation_method_results', ['valuation_id'])
    op.create_index('ix_val_method_results_method', 'valuation_method_results', ['method'])
    op.create_index('ix_val_method_results_primary', 'valuation_method_results', ['is_primary'])

    # -------------------------------------------------------------------------
    # 4. VALUATION ESG ADJUSTMENTS  (ESG factor discount/premium decomposition)
    # -------------------------------------------------------------------------
    op.create_table(
        'valuation_esg_adjustments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('valuation_id', UUID(as_uuid=True), sa.ForeignKey('unified_valuations.id', ondelete='CASCADE'), nullable=False),

        # Environmental adjustments
        sa.Column('epc_rating', sa.String(2)),
        sa.Column('epc_adjustment_pct', sa.Numeric(6, 4)),             # e.g. -5% for F/G vs A/B premium
        sa.Column('green_premium_pct', sa.Numeric(6, 4)),              # BREEAM/LEED premium
        sa.Column('stranded_risk_discount_pct', sa.Numeric(6, 4)),     # forward-looking stranding risk
        sa.Column('flood_risk_discount_pct', sa.Numeric(6, 4)),
        sa.Column('physical_climate_risk_discount_pct', sa.Numeric(6, 4)),
        sa.Column('transition_risk_discount_pct', sa.Numeric(6, 4)),
        sa.Column('carbon_cost_discount_pct', sa.Numeric(6, 4)),       # NPV of future carbon costs
        sa.Column('energy_capex_discount_pct', sa.Numeric(6, 4)),      # retrofit capex required
        sa.Column('renewable_energy_premium_pct', sa.Numeric(6, 4)),
        sa.Column('water_efficiency_adjustment_pct', sa.Numeric(6, 4)),
        sa.Column('biodiversity_net_gain_pct', sa.Numeric(6, 4)),
        sa.Column('nature_risk_discount_pct', sa.Numeric(6, 4)),       # TNFD nature-related risk

        # Social adjustments
        sa.Column('social_value_premium_pct', sa.Numeric(6, 4)),       # mixed-use / community benefit
        sa.Column('wellbeing_premium_pct', sa.Numeric(6, 4)),          # WELL certification
        sa.Column('accessibility_adjustment_pct', sa.Numeric(6, 4)),
        sa.Column('community_infrastructure_pct', sa.Numeric(6, 4)),

        # Governance adjustments
        sa.Column('management_quality_adjustment_pct', sa.Numeric(6, 4)),
        sa.Column('esg_data_quality_adjustment_pct', sa.Numeric(6, 4)),
        sa.Column('reporting_quality_adjustment_pct', sa.Numeric(6, 4)),
        sa.Column('third_party_verification_premium_pct', sa.Numeric(6, 4)),

        # Net ESG adjustment
        sa.Column('total_esg_adjustment_pct', sa.Numeric(7, 4), nullable=False),
        sa.Column('total_esg_adjustment_gbp', sa.Numeric(15, 2)),

        # Evidence and sources
        sa.Column('research_sources', JSONB),                           # [{factor, source, evidence, peer_reviewed}]
        sa.Column('adjustment_methodology', sa.String(50)),             # hedonic_regression | delphi | comparable_pairs | literature_review | explicit_capex | dcf_based
        sa.Column('adjustment_references', JSONB),                      # [{author, year, finding, adjustment_pct_range}]

        sa.Column('validation_summary', JSONB),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_val_esg_adj_valuation', 'valuation_esg_adjustments', ['valuation_id'])

    # -------------------------------------------------------------------------
    # 5. VALUATION SCENARIOS  (base/bull/bear/climate stress)
    # -------------------------------------------------------------------------
    op.create_table(
        'valuation_scenarios',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('valuation_id', UUID(as_uuid=True), sa.ForeignKey('unified_valuations.id', ondelete='CASCADE'), nullable=False),

        sa.Column('scenario_name', sa.String(50), nullable=False),      # base | bull | bear | climate_orderly | climate_disorderly | climate_hot_house | regulatory_tightening | market_stress
        sa.Column('scenario_description', sa.Text),
        sa.Column('probability_weight', sa.Numeric(4, 3)),

        # Macro assumptions for this scenario
        sa.Column('gdp_growth_pct', sa.Numeric(6, 3)),
        sa.Column('inflation_pct', sa.Numeric(5, 3)),
        sa.Column('base_rate_pct', sa.Numeric(5, 3)),
        sa.Column('credit_spread_bps', sa.Numeric(7, 2)),
        sa.Column('hpi_growth_pct', sa.Numeric(6, 3)),
        sa.Column('rental_growth_pct', sa.Numeric(6, 3)),
        sa.Column('yield_expansion_bps', sa.Numeric(7, 2)),            # positive = yield expansion = value fall

        # Climate-specific assumptions (for climate scenarios)
        sa.Column('carbon_price_gbp_t', sa.Numeric(8, 2)),
        sa.Column('temperature_increase_c', sa.Numeric(4, 2)),
        sa.Column('energy_cost_inflation_pct', sa.Numeric(5, 3)),
        sa.Column('regulatory_capex_required_gbp', sa.Numeric(15, 2)),
        sa.Column('stranded_value_discount_pct', sa.Numeric(6, 4)),

        # Scenario valuation output
        sa.Column('scenario_value', sa.Numeric(15, 2), nullable=False),
        sa.Column('scenario_irr_pct', sa.Numeric(6, 4)),
        sa.Column('scenario_equity_multiple', sa.Numeric(5, 3)),
        sa.Column('vs_base_value_pct', sa.Numeric(7, 4)),              # (scenario_value - base_value) / base_value

        # Year-by-year NPV trajectory
        sa.Column('npv_trajectory', JSONB),                             # [{year, value, yield, rental_income, capex}]

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.CheckConstraint("scenario_name IN ('base','bull','bear','climate_orderly','climate_disorderly','climate_hot_house','regulatory_tightening','market_stress','covid_stress','interest_rate_shock')", name='ck_val_scenarios_name'),
    )
    op.create_index('ix_val_scenarios_valuation', 'valuation_scenarios', ['valuation_id'])
    op.create_index('ix_val_scenarios_name', 'valuation_scenarios', ['scenario_name'])

    # -------------------------------------------------------------------------
    # 6. NATURE ASSESSMENTS  (TNFD LEAP / SBTN for land-dependent assets)
    # -------------------------------------------------------------------------
    op.create_table(
        'nature_assessments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('asset_id', UUID(as_uuid=True), sa.ForeignKey('valuation_assets.id', ondelete='SET NULL')),
        sa.Column('valuation_id', UUID(as_uuid=True), sa.ForeignKey('unified_valuations.id', ondelete='SET NULL')),
        sa.Column('asset_name', sa.String(255), nullable=False),
        sa.Column('assessment_date', sa.Date, nullable=False),
        sa.Column('assessment_framework', sa.String(30), default='TNFD_LEAP'),  # TNFD_LEAP | SBTN | GRI_BIODIVERSITY | CBD | ENCORE

        # Location context
        sa.Column('latitude', sa.Numeric(9, 6)),
        sa.Column('longitude', sa.Numeric(9, 6)),
        sa.Column('country_iso', sa.String(3)),
        sa.Column('site_area_ha', sa.Numeric(10, 4)),
        sa.Column('protected_area_within_5km', sa.Boolean, default=False),
        sa.Column('protected_area_names', JSONB),                       # [{name, designation, distance_km}]
        sa.Column('key_biodiversity_area', sa.Boolean, default=False),
        sa.Column('ramsar_wetland', sa.Boolean, default=False),
        sa.Column('biome', sa.String(50)),                              # temperate_forest | tropical_forest | grassland | wetland | marine | freshwater | ...

        # TNFD LEAP Phase 1 — Locate
        sa.Column('locate_ecosystem_services', JSONB),                  # [{ecosystem_service, relevance, dependency_score}]
        sa.Column('locate_biodiversity_intactness_index', sa.Numeric(5, 3)),  # BII 0-1

        # TNFD LEAP Phase 2 — Evaluate
        sa.Column('evaluate_dependencies', JSONB),                      # [{service, high_dependency, notes}]
        sa.Column('evaluate_impacts', JSONB),                           # [{impact_driver, magnitude, spatial_scope, reversibility}]
        sa.Column('land_cover_change_ha', sa.Numeric(10, 4)),          # area converted / disturbed
        sa.Column('water_use_m3_pa', sa.Numeric(14, 2)),
        sa.Column('pollution_type', JSONB),                             # [{pollutant, load_pa, unit}]

        # TNFD LEAP Phase 3 — Assess
        sa.Column('nature_related_risks', JSONB),                       # [{risk_type, driver, likelihood, impact_gbp, time_horizon}]
        sa.Column('nature_related_opportunities', JSONB),               # [{opportunity_type, value_gbp, timeline}]
        sa.Column('nature_risk_score', sa.Numeric(4, 2)),              # 0-10
        sa.Column('nature_risk_category', sa.String(10)),               # Low | Medium | High | Critical

        # TNFD LEAP Phase 4 — Prepare
        sa.Column('nature_targets', JSONB),                             # [{target, timeline, kpi, progress}]
        sa.Column('mitigation_actions', JSONB),                         # [{action, cost_gbp, benefit, timeline}]

        # Biodiversity Net Gain (BNG) — UK Infrastructure Act 2023
        sa.Column('bng_baseline_units', sa.Numeric(8, 4)),
        sa.Column('bng_target_units', sa.Numeric(8, 4)),                # baseline × 1.1 (min 10% net gain)
        sa.Column('bng_achieved_units', sa.Numeric(8, 4)),
        sa.Column('bng_gap_units', sa.Numeric(8, 4)),
        sa.Column('bng_metric_version', sa.String(20)),                 # DEFRA BNG Metric 4.0

        # ENCORE dependencies (Natural Capital Finance Alliance)
        sa.Column('encore_dependencies', JSONB),                        # [{process, materiality: 'very_high|high|medium|low'}]

        # Valuation impact
        sa.Column('nature_value_discount_pct', sa.Numeric(6, 4)),       # % value discount from nature risk
        sa.Column('nature_value_discount_gbp', sa.Numeric(15, 2)),
        sa.Column('bng_value_premium_gbp', sa.Numeric(15, 2)),          # value of biodiversity credits held

        sa.Column('validation_summary', JSONB),
        sa.Column('status', sa.String(20), default='draft'),
        sa.Column('created_by', UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.CheckConstraint("nature_risk_category IN ('Low','Medium','High','Critical')", name='ck_nature_assessments_category'),
        sa.CheckConstraint("status IN ('draft','submitted','approved','published','archived')", name='ck_nature_assessments_status'),
    )
    op.create_index('ix_nature_assessments_asset', 'nature_assessments', ['asset_id'])
    op.create_index('ix_nature_assessments_valuation', 'nature_assessments', ['valuation_id'])
    op.create_index('ix_nature_assessments_country', 'nature_assessments', ['country_iso'])
    op.create_index('ix_nature_assessments_risk', 'nature_assessments', ['nature_risk_category'])

    # -------------------------------------------------------------------------
    # 7. CLIMATE VALUATION ADJUSTMENTS  (forward-looking climate risk per horizon)
    # -------------------------------------------------------------------------
    op.create_table(
        'climate_valuation_adjustments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('valuation_id', UUID(as_uuid=True), sa.ForeignKey('unified_valuations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('climate_scenario', sa.String(30), nullable=False),   # RCP2.6 | RCP4.5 | RCP8.5 | NGFS_NZE | NGFS_DELAYED | NGFS_HOT_HOUSE
        sa.Column('time_horizon_year', sa.Integer, nullable=False),     # 2030 | 2050 | 2075 | 2100

        # Physical risk
        sa.Column('flood_risk_uplift_pct', sa.Numeric(6, 4)),
        sa.Column('heat_stress_discount_pct', sa.Numeric(6, 4)),
        sa.Column('sea_level_rise_discount_pct', sa.Numeric(6, 4)),
        sa.Column('storm_risk_discount_pct', sa.Numeric(6, 4)),
        sa.Column('wildfire_discount_pct', sa.Numeric(6, 4)),
        sa.Column('drought_discount_pct', sa.Numeric(6, 4)),
        sa.Column('total_physical_risk_discount_pct', sa.Numeric(7, 4)),

        # Transition risk
        sa.Column('carbon_cost_pv_discount_pct', sa.Numeric(6, 4)),    # NPV of future carbon cost
        sa.Column('stranded_asset_discount_pct', sa.Numeric(6, 4)),
        sa.Column('retrofit_capex_discount_pct', sa.Numeric(6, 4)),    # upfront capex to meet future regs
        sa.Column('regulatory_compliance_discount_pct', sa.Numeric(6, 4)),
        sa.Column('energy_cost_inflation_discount_pct', sa.Numeric(6, 4)),
        sa.Column('green_premium_uplift_pct', sa.Numeric(6, 4)),       # premium for low-carbon assets
        sa.Column('total_transition_risk_discount_pct', sa.Numeric(7, 4)),

        # Combined climate adjustment
        sa.Column('total_climate_adjustment_pct', sa.Numeric(7, 4)),
        sa.Column('climate_adjusted_value', sa.Numeric(15, 2)),

        # Assumptions
        sa.Column('carbon_price_assumption_gbp_t', sa.Numeric(8, 2)),
        sa.Column('temperature_increase_c', sa.Numeric(4, 2)),
        sa.Column('climate_model', sa.String(50)),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.CheckConstraint("climate_scenario IN ('RCP2.6','RCP4.5','RCP6.0','RCP8.5','SSP1-1.9','SSP2-4.5','SSP5-8.5','NGFS_NET_ZERO_2050','NGFS_DELAYED_TRANSITION','NGFS_HOT_HOUSE')", name='ck_climate_val_adj_scenario'),
    )
    op.create_index('ix_climate_val_adj_valuation', 'climate_valuation_adjustments', ['valuation_id'])
    op.create_index('ix_climate_val_adj_scenario', 'climate_valuation_adjustments', ['climate_scenario'])

    # -------------------------------------------------------------------------
    # 8. VALUATION COMPARABLE SALES  (evidence register for sales comparison)
    # -------------------------------------------------------------------------
    op.create_table(
        'valuation_comparable_sales',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('asset_id', UUID(as_uuid=True), sa.ForeignKey('valuation_assets.id', ondelete='SET NULL')),
        sa.Column('valuation_id', UUID(as_uuid=True), sa.ForeignKey('unified_valuations.id', ondelete='SET NULL')),

        # Comparable transaction details
        sa.Column('transaction_date', sa.Date, nullable=False),
        sa.Column('property_address', sa.Text),
        sa.Column('postcode', sa.String(20)),
        sa.Column('country_iso', sa.String(3), nullable=False),
        sa.Column('asset_class', sa.String(50)),
        sa.Column('asset_sub_class', sa.String(50)),
        sa.Column('gross_area_m2', sa.Numeric(10, 2)),
        sa.Column('net_area_m2', sa.Numeric(10, 2)),

        # Transaction price
        sa.Column('transaction_price', sa.Numeric(15, 2), nullable=False),
        sa.Column('currency', sa.String(3), default='GBP'),
        sa.Column('price_per_m2', sa.Numeric(12, 2)),
        sa.Column('price_per_unit', sa.Numeric(12, 2)),
        sa.Column('passing_rent_pa', sa.Numeric(12, 2)),
        sa.Column('net_initial_yield_pct', sa.Numeric(5, 4)),
        sa.Column('equivalent_yield_pct', sa.Numeric(5, 4)),

        # Quality and adjustments
        sa.Column('epc_rating', sa.String(2)),
        sa.Column('breeam_rating', sa.String(20)),
        sa.Column('condition', sa.String(20)),                          # Prime | Secondary | Tertiary

        # Adjustments to make comparable to subject (additive percentages)
        sa.Column('time_adjustment_pct', sa.Numeric(6, 4)),            # time since sale
        sa.Column('location_adjustment_pct', sa.Numeric(6, 4)),
        sa.Column('size_adjustment_pct', sa.Numeric(6, 4)),
        sa.Column('quality_adjustment_pct', sa.Numeric(6, 4)),
        sa.Column('esg_adjustment_pct', sa.Numeric(6, 4)),             # green premium / brown discount
        sa.Column('other_adjustments_pct', sa.Numeric(6, 4)),
        sa.Column('total_adjustment_pct', sa.Numeric(7, 4)),
        sa.Column('adjusted_price', sa.Numeric(15, 2)),
        sa.Column('adjusted_price_per_m2', sa.Numeric(12, 2)),

        # Weight in final value
        sa.Column('weight_in_valuation', sa.Numeric(4, 3)),            # 0-1

        # Source
        sa.Column('data_source', sa.String(50)),                        # CoStar | EGi | MSCI_Real_Estate | RICS | public_registry | internal
        sa.Column('is_confidential', sa.Boolean, default=False),
        sa.Column('notes', sa.Text),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_val_comparables_asset', 'valuation_comparable_sales', ['asset_id'])
    op.create_index('ix_val_comparables_valuation', 'valuation_comparable_sales', ['valuation_id'])
    op.create_index('ix_val_comparables_country', 'valuation_comparable_sales', ['country_iso'])
    op.create_index('ix_val_comparables_date', 'valuation_comparable_sales', ['transaction_date'])

    # -------------------------------------------------------------------------
    # 9. VALUATION AUDIT LOG  (immutable change history)
    # -------------------------------------------------------------------------
    op.create_table(
        'valuation_audit_log',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('valuation_id', UUID(as_uuid=True), sa.ForeignKey('unified_valuations.id', ondelete='CASCADE'), nullable=False),

        sa.Column('event_type', sa.String(30), nullable=False),         # created | updated | signed_off | published | superseded | archived | recalculated
        sa.Column('event_timestamp', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('actor_id', UUID(as_uuid=True)),
        sa.Column('actor_name', sa.String(100)),
        sa.Column('actor_role', sa.String(50)),                         # valuer | reviewer | approver | system

        # Snapshot of values at this point
        sa.Column('value_before', sa.Numeric(15, 2)),
        sa.Column('value_after', sa.Numeric(15, 2)),
        sa.Column('status_before', sa.String(20)),
        sa.Column('status_after', sa.String(20)),

        # What changed
        sa.Column('fields_changed', JSONB),                             # [{field, old_value, new_value}]
        sa.Column('change_reason', sa.Text),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.String(200)),

        sa.CheckConstraint("event_type IN ('created','updated','signed_off','published','superseded','archived','recalculated','reviewed','approved')", name='ck_val_audit_event_type'),
    )
    op.create_index('ix_val_audit_log_valuation', 'valuation_audit_log', ['valuation_id'])
    op.create_index('ix_val_audit_log_timestamp', 'valuation_audit_log', ['event_timestamp'])
    op.create_index('ix_val_audit_log_type', 'valuation_audit_log', ['event_type'])
    op.create_index('ix_val_audit_log_actor', 'valuation_audit_log', ['actor_id'])


def downgrade():
    """Drop unified valuation tables."""
    op.drop_table('valuation_audit_log')
    op.drop_table('valuation_comparable_sales')
    op.drop_table('climate_valuation_adjustments')
    op.drop_table('nature_assessments')
    op.drop_table('valuation_scenarios')
    op.drop_table('valuation_esg_adjustments')
    op.drop_table('valuation_method_results')
    op.drop_table('unified_valuations')
    op.drop_table('valuation_assets')
