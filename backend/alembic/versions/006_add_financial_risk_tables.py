"""
Add Financial Risk Tables

Revision ID: 006_add_financial_risk_tables
Revises: 005_add_portfolio_analytics_tables
Create Date: 2026-03-01

This migration adds tables for the Financial Risk module:
- ecl_assessments          : Portfolio-level ECL run metadata (IFRS 9 compliant)
- ecl_exposures            : Individual loan/bond exposure records with PD/LGD/EAD/ECL per stage
- ecl_scenario_results     : Multi-scenario ECL outputs (OPTIMISTIC/BASE/ADVERSE/SEVERE)
- ecl_climate_overlays     : NGFS/BoE climate scenario overlays on PD/LGD
- pcaf_portfolios          : PCAF financed-emissions portfolio entity
- pcaf_investees           : Per-investee attribution factors, emissions, DQ scores
- pcaf_portfolio_results   : Aggregated portfolio-level emissions metrics (WACI, ITR, carbon footprint)
- temperature_scores       : Portfolio / fund-level implied temperature rise (SBTi/PACTA methodology)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '006_add_financial_risk_tables'
down_revision = '005_add_portfolio_analytics_tables'
branch_labels = None
depends_on = None


def upgrade():
    """Create financial risk tables."""

    # -------------------------------------------------------------------------
    # 1. ECL ASSESSMENTS  (top-level run)
    # -------------------------------------------------------------------------
    op.create_table(
        'ecl_assessments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('portfolio_id', UUID(as_uuid=True)),                  # nullable — may reference portfolio_analytics
        sa.Column('entity_name', sa.String(255), nullable=False),
        sa.Column('reporting_date', sa.Date, nullable=False),
        sa.Column('base_currency', sa.String(3), default='GBP'),

        # Run configuration
        sa.Column('pd_model', sa.String(50), default='logistic_regression'),   # logistic_regression | merton | vasicek
        sa.Column('lgd_model', sa.String(50), default='supervisory_lgd'),       # supervisory_lgd | market_lgd | internal
        sa.Column('ead_approach', sa.String(50), default='outstanding_balance'),# outstanding_balance | ccf_adjusted
        sa.Column('scenario_method', sa.String(50), default='probability_weighted'), # probability_weighted | multiple_scenario
        sa.Column('macroeconomic_vintage', sa.String(20)),                      # e.g. '2026Q1'

        # Aggregate results (probability-weighted)
        sa.Column('total_ead_gbp', sa.Numeric(18, 2)),
        sa.Column('total_ecl_gbp', sa.Numeric(18, 2)),
        sa.Column('ecl_rate_bps', sa.Numeric(8, 4)),                    # ECL / EAD in basis points
        sa.Column('stage1_ead_gbp', sa.Numeric(18, 2)),
        sa.Column('stage2_ead_gbp', sa.Numeric(18, 2)),
        sa.Column('stage3_ead_gbp', sa.Numeric(18, 2)),
        sa.Column('stage1_ecl_gbp', sa.Numeric(18, 2)),
        sa.Column('stage2_ecl_gbp', sa.Numeric(18, 2)),
        sa.Column('stage3_ecl_gbp', sa.Numeric(18, 2)),

        # Climate overlay summary
        sa.Column('climate_ecl_uplift_gbp', sa.Numeric(18, 2)),         # additional ECL from climate risk overlay
        sa.Column('climate_ecl_uplift_pct', sa.Numeric(6, 4)),

        # Sector breakdown JSONB: {sector: {ead, ecl, stage_mix}}
        sa.Column('sector_breakdown', JSONB),
        # Geography breakdown JSONB: {country_iso: {ead, ecl}}
        sa.Column('geography_breakdown', JSONB),
        # Collateral type breakdown
        sa.Column('collateral_breakdown', JSONB),

        # Validation
        sa.Column('validation_summary', JSONB),                         # inputs, assumptions, outputs, QA flags
        sa.Column('status', sa.String(20), default='draft'),

        # Audit
        sa.Column('created_by', UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.CheckConstraint("pd_model IN ('logistic_regression','merton','vasicek','through_the_cycle','point_in_time')", name='ck_ecl_assessments_pd_model'),
        sa.CheckConstraint("lgd_model IN ('supervisory_lgd','market_lgd','internal','downturn_lgd')", name='ck_ecl_assessments_lgd_model'),
        sa.CheckConstraint("status IN ('draft','submitted','approved','archived')", name='ck_ecl_assessments_status'),
    )
    op.create_index('ix_ecl_assessments_portfolio', 'ecl_assessments', ['portfolio_id'])
    op.create_index('ix_ecl_assessments_date', 'ecl_assessments', ['reporting_date'])
    op.create_index('ix_ecl_assessments_entity', 'ecl_assessments', ['entity_name'])
    op.create_index('ix_ecl_assessments_status', 'ecl_assessments', ['status'])

    # -------------------------------------------------------------------------
    # 2. ECL EXPOSURES  (individual instrument / obligor records)
    # -------------------------------------------------------------------------
    op.create_table(
        'ecl_exposures',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('assessment_id', UUID(as_uuid=True), sa.ForeignKey('ecl_assessments.id', ondelete='CASCADE'), nullable=False),

        # Obligor / instrument identification
        sa.Column('instrument_id', sa.String(100)),                     # internal reference
        sa.Column('obligor_name', sa.String(255)),
        sa.Column('obligor_id', sa.String(100)),
        sa.Column('instrument_type', sa.String(50)),                    # mortgage | corporate_loan | bond | revolving_credit | trade_finance

        # Classification
        sa.Column('sector_gics', sa.String(50)),                        # GICS sector code
        sa.Column('country_iso', sa.String(3)),
        sa.Column('collateral_type', sa.String(50)),                    # real_estate | equipment | unsecured | guarantee
        sa.Column('seniority', sa.String(30)),                          # senior_secured | senior_unsecured | subordinated | mezzanine

        # Financial inputs
        sa.Column('outstanding_balance', sa.Numeric(18, 2)),
        sa.Column('committed_exposure', sa.Numeric(18, 2)),             # for revolving facilities
        sa.Column('ccf', sa.Numeric(5, 4)),                             # credit conversion factor 0-1
        sa.Column('ead', sa.Numeric(18, 2)),                            # EAD = balance + ccf * undrawn
        sa.Column('original_maturity_years', sa.Numeric(5, 2)),
        sa.Column('residual_maturity_years', sa.Numeric(5, 2)),
        sa.Column('origination_date', sa.Date),
        sa.Column('maturity_date', sa.Date),
        sa.Column('coupon_rate', sa.Numeric(6, 4)),
        sa.Column('collateral_value', sa.Numeric(18, 2)),
        sa.Column('ltv_ratio', sa.Numeric(5, 4)),                       # loan-to-value for mortgage / RE

        # IFRS 9 stage
        sa.Column('ifrs9_stage', sa.SmallInteger, default=1),           # 1, 2, or 3
        sa.Column('days_past_due', sa.Integer, default=0),
        sa.Column('is_forbearance', sa.Boolean, default=False),
        sa.Column('is_credit_impaired', sa.Boolean, default=False),
        sa.Column('internal_rating', sa.String(10)),                    # e.g. 'BBB', '5', 'Pass'

        # PD parameters
        sa.Column('pd_12m', sa.Numeric(7, 6)),                         # 12-month PD (0-1)
        sa.Column('pd_lifetime', sa.Numeric(7, 6)),                    # lifetime PD
        sa.Column('pd_ttc', sa.Numeric(7, 6)),                         # through-the-cycle PD
        sa.Column('pd_pit', sa.Numeric(7, 6)),                         # point-in-time PD
        sa.Column('pd_macro_adjusted', sa.Numeric(7, 6)),              # macro-scenario-adjusted PD
        sa.Column('pd_climate_adjusted', sa.Numeric(7, 6)),            # climate-adjusted PD

        # LGD parameters
        sa.Column('lgd_downturn', sa.Numeric(5, 4)),                   # regulatory/internal downturn LGD
        sa.Column('lgd_market', sa.Numeric(5, 4)),                     # market LGD from secondary prices
        sa.Column('lgd_pit', sa.Numeric(5, 4)),                        # point-in-time LGD
        sa.Column('cure_rate', sa.Numeric(5, 4)),                      # for stage 3

        # ECL outputs
        sa.Column('ecl_12m', sa.Numeric(18, 2)),                       # 12-month ECL (Stage 1)
        sa.Column('ecl_lifetime', sa.Numeric(18, 2)),                  # Lifetime ECL (Stage 2/3)
        sa.Column('ecl_recognised', sa.Numeric(18, 2)),                # ECL actually booked (= 12m for S1, lifetime for S2/3)
        sa.Column('discount_rate', sa.Numeric(5, 4)),                  # effective interest rate for discounting

        # Climate risk scores
        sa.Column('physical_risk_score', sa.Numeric(4, 2)),            # 0-10
        sa.Column('transition_risk_score', sa.Numeric(4, 2)),          # 0-10
        sa.Column('stranded_asset_flag', sa.Boolean, default=False),
        sa.Column('climate_pd_uplift_bps', sa.Numeric(8, 4)),
        sa.Column('climate_lgd_uplift_bps', sa.Numeric(8, 4)),

        # Raw scenario PDxLGD arrays stored for audit
        sa.Column('scenario_cashflows', JSONB),                        # {optimistic:{pd,lgd,ecl}, base:{...}, ...}

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.CheckConstraint("ifrs9_stage IN (1,2,3)", name='ck_ecl_exposures_stage'),
        sa.CheckConstraint("instrument_type IN ('mortgage','corporate_loan','bond','revolving_credit','trade_finance','project_finance','sme_loan','consumer_loan','auto_loan','leasing','other')", name='ck_ecl_exposures_instrument_type'),
    )
    op.create_index('ix_ecl_exposures_assessment', 'ecl_exposures', ['assessment_id'])
    op.create_index('ix_ecl_exposures_stage', 'ecl_exposures', ['ifrs9_stage'])
    op.create_index('ix_ecl_exposures_sector', 'ecl_exposures', ['sector_gics'])
    op.create_index('ix_ecl_exposures_country', 'ecl_exposures', ['country_iso'])
    op.create_index('ix_ecl_exposures_instrument_type', 'ecl_exposures', ['instrument_type'])
    op.create_index('ix_ecl_exposures_stranded', 'ecl_exposures', ['stranded_asset_flag'])

    # -------------------------------------------------------------------------
    # 3. ECL SCENARIO RESULTS  (probability-weighted multi-scenario decomposition)
    # -------------------------------------------------------------------------
    op.create_table(
        'ecl_scenario_results',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('assessment_id', UUID(as_uuid=True), sa.ForeignKey('ecl_assessments.id', ondelete='CASCADE'), nullable=False),

        sa.Column('scenario_name', sa.String(50), nullable=False),      # OPTIMISTIC | BASE | ADVERSE | SEVERE
        sa.Column('scenario_weight', sa.Numeric(4, 3), nullable=False), # 0-1, must sum to 1 across assessment
        sa.Column('scenario_description', sa.Text),

        # Macro assumptions for this scenario
        sa.Column('gdp_growth_pct', sa.Numeric(6, 3)),
        sa.Column('unemployment_rate_pct', sa.Numeric(5, 3)),
        sa.Column('base_rate_pct', sa.Numeric(5, 3)),
        sa.Column('hpi_growth_pct', sa.Numeric(6, 3)),                  # house price index growth
        sa.Column('credit_spread_bps', sa.Numeric(7, 2)),
        sa.Column('inflation_pct', sa.Numeric(5, 3)),

        # ECL for this scenario
        sa.Column('total_ead_gbp', sa.Numeric(18, 2)),
        sa.Column('total_ecl_gbp', sa.Numeric(18, 2)),
        sa.Column('ecl_rate_bps', sa.Numeric(8, 4)),
        sa.Column('stage1_ecl_gbp', sa.Numeric(18, 2)),
        sa.Column('stage2_ecl_gbp', sa.Numeric(18, 2)),
        sa.Column('stage3_ecl_gbp', sa.Numeric(18, 2)),

        # Year-by-year projected ECL JSONB: [{year: 2026, ecl: 1234567, ...}, ...]
        sa.Column('ecl_time_series', JSONB),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.CheckConstraint("scenario_name IN ('OPTIMISTIC','BASE','ADVERSE','SEVERE','CLIMATE_DISORDERLY','CLIMATE_ORDERLY','CLIMATE_HOT_HOUSE')", name='ck_ecl_scenario_name'),
    )
    op.create_index('ix_ecl_scenario_results_assessment', 'ecl_scenario_results', ['assessment_id'])
    op.create_index('ix_ecl_scenario_results_scenario', 'ecl_scenario_results', ['scenario_name'])

    # -------------------------------------------------------------------------
    # 4. ECL CLIMATE OVERLAYS  (NGFS / BoE / IPCC scenario overlays)
    # -------------------------------------------------------------------------
    op.create_table(
        'ecl_climate_overlays',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('assessment_id', UUID(as_uuid=True), sa.ForeignKey('ecl_assessments.id', ondelete='CASCADE'), nullable=False),

        sa.Column('climate_scenario', sa.String(50), nullable=False),   # NGFS_NET_ZERO_2050 | NGFS_DELAYED_TRANSITION | NGFS_HOT_HOUSE | RCP2.6 | RCP4.5 | RCP8.5
        sa.Column('horizon_years', sa.Integer, default=30),
        sa.Column('reference_year', sa.Integer, default=2025),

        # Physical risk overlay
        sa.Column('physical_pd_uplift_avg_bps', sa.Numeric(8, 4)),
        sa.Column('physical_lgd_uplift_avg_bps', sa.Numeric(8, 4)),
        sa.Column('physical_ecl_uplift_gbp', sa.Numeric(18, 2)),
        sa.Column('physical_ecl_uplift_pct', sa.Numeric(6, 4)),
        sa.Column('physical_risk_by_peril', JSONB),                     # {flood: {ead, ecl_uplift}, wildfire: {...}, ...}

        # Transition risk overlay
        sa.Column('transition_pd_uplift_avg_bps', sa.Numeric(8, 4)),
        sa.Column('transition_lgd_uplift_avg_bps', sa.Numeric(8, 4)),
        sa.Column('transition_ecl_uplift_gbp', sa.Numeric(18, 2)),
        sa.Column('transition_ecl_uplift_pct', sa.Numeric(6, 4)),
        sa.Column('transition_risk_by_sector', JSONB),                  # {energy: {ead, ecl_uplift}, transport: {...}, ...}

        # Combined climate ECL
        sa.Column('total_climate_ecl_uplift_gbp', sa.Numeric(18, 2)),
        sa.Column('total_climate_ecl_uplift_pct', sa.Numeric(6, 4)),

        # Year-by-year climate ECL trajectory
        sa.Column('climate_ecl_time_series', JSONB),                    # [{year, physical_ecl, transition_ecl, total_climate_ecl}]

        # Stranded assets
        sa.Column('stranded_ead_gbp', sa.Numeric(18, 2)),
        sa.Column('stranded_ecl_gbp', sa.Numeric(18, 2)),
        sa.Column('stranded_count', sa.Integer),

        # Source / methodology
        sa.Column('ngfs_vintage', sa.String(20)),                       # e.g. 'NGFS_v4'
        sa.Column('carbon_price_2030_usd', sa.Numeric(8, 2)),
        sa.Column('carbon_price_2050_usd', sa.Numeric(8, 2)),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.CheckConstraint("climate_scenario IN ('NGFS_NET_ZERO_2050','NGFS_DELAYED_TRANSITION','NGFS_HOT_HOUSE','NGFS_DIVERGENT','RCP2.6','RCP4.5','RCP8.5','SSP1-1.9','SSP2-4.5','SSP5-8.5')", name='ck_ecl_climate_scenario'),
    )
    op.create_index('ix_ecl_climate_overlays_assessment', 'ecl_climate_overlays', ['assessment_id'])
    op.create_index('ix_ecl_climate_overlays_scenario', 'ecl_climate_overlays', ['climate_scenario'])

    # -------------------------------------------------------------------------
    # 5. PCAF PORTFOLIOS  (entity / fund level)
    # -------------------------------------------------------------------------
    op.create_table(
        'pcaf_portfolios',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_name', sa.String(255), nullable=False),
        sa.Column('legal_entity_identifier', sa.String(20)),            # LEI code
        sa.Column('reporting_year', sa.Integer, nullable=False),
        sa.Column('base_currency', sa.String(3), default='GBP'),
        sa.Column('portfolio_type', sa.String(50), nullable=False),     # listed_equity | corporate_bonds | business_loans | mortgages | project_finance | sovereign_bonds

        # Total portfolio financials
        sa.Column('total_outstanding_gbp', sa.Numeric(18, 2)),
        sa.Column('total_enterprise_value_gbp', sa.Numeric(18, 2)),
        sa.Column('total_revenue_gbp', sa.Numeric(18, 2)),

        # PCAF aggregate financed emissions
        sa.Column('financed_scope1_tco2e', sa.Numeric(18, 4)),
        sa.Column('financed_scope2_tco2e', sa.Numeric(18, 4)),
        sa.Column('financed_scope3_tco2e', sa.Numeric(18, 4)),
        sa.Column('total_financed_emissions_tco2e', sa.Numeric(18, 4)),

        # Portfolio carbon metrics
        sa.Column('waci_tco2e_per_mrevenue', sa.Numeric(12, 4)),        # Weighted Average Carbon Intensity tCO2e/M revenue
        sa.Column('carbon_footprint_tco2e_per_mgbp_invested', sa.Numeric(12, 4)),
        sa.Column('portfolio_coverage_pct', sa.Numeric(5, 2)),          # % of portfolio with emissions data
        sa.Column('pcaf_data_quality_score_avg', sa.Numeric(3, 1)),     # PCAF DQ 1-5 weighted average

        # Implied Temperature Rise
        sa.Column('itr_1_5c_alignment_pct', sa.Numeric(5, 2)),         # % aligned with 1.5C
        sa.Column('itr_2c_alignment_pct', sa.Numeric(5, 2)),
        sa.Column('portfolio_temperature_c', sa.Numeric(4, 2)),         # implied portfolio temperature

        # SFDR mandatory PAI indicators (Annex I Table 1)
        sa.Column('sfdr_pai_indicators', JSONB),                        # {indicator_id: {value, unit, coverage_pct, data_quality}}

        # Optional SFDR PAI (Annex I Table 2)
        sa.Column('sfdr_pai_optional', JSONB),

        # Baseline / target
        sa.Column('base_year', sa.Integer),
        sa.Column('base_year_emissions_tco2e', sa.Numeric(18, 4)),
        sa.Column('target_year', sa.Integer),
        sa.Column('target_reduction_pct', sa.Numeric(5, 2)),

        # Validation
        sa.Column('validation_summary', JSONB),
        sa.Column('methodology_notes', sa.Text),
        sa.Column('status', sa.String(20), default='draft'),

        sa.Column('created_by', UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.CheckConstraint("portfolio_type IN ('listed_equity','corporate_bonds','business_loans','commercial_re_loans','mortgages','project_finance','sovereign_bonds','infrastructure','mixed')", name='ck_pcaf_portfolios_type'),
        sa.CheckConstraint("status IN ('draft','submitted','approved','published','archived')", name='ck_pcaf_portfolios_status'),
    )
    op.create_index('ix_pcaf_portfolios_entity', 'pcaf_portfolios', ['entity_name'])
    op.create_index('ix_pcaf_portfolios_year', 'pcaf_portfolios', ['reporting_year'])
    op.create_index('ix_pcaf_portfolios_type', 'pcaf_portfolios', ['portfolio_type'])

    # -------------------------------------------------------------------------
    # 6. PCAF INVESTEES  (per-investee / counterparty level detail)
    # -------------------------------------------------------------------------
    op.create_table(
        'pcaf_investees',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('portfolio_id', UUID(as_uuid=True), sa.ForeignKey('pcaf_portfolios.id', ondelete='CASCADE'), nullable=False),

        # Investee identification
        sa.Column('investee_name', sa.String(255), nullable=False),
        sa.Column('lei', sa.String(20)),
        sa.Column('isin', sa.String(12)),
        sa.Column('sector_gics', sa.String(50)),
        sa.Column('nace_code', sa.String(10)),
        sa.Column('country_iso', sa.String(3)),
        sa.Column('is_listed', sa.Boolean, default=True),

        # Financial inputs (PCAF attribution)
        sa.Column('outstanding_investment_gbp', sa.Numeric(18, 2)),     # Our loan / investment amount
        sa.Column('enterprise_value_gbp', sa.Numeric(18, 2)),           # EVIC = equity + debt
        sa.Column('equity_market_cap_gbp', sa.Numeric(18, 2)),
        sa.Column('total_debt_gbp', sa.Numeric(18, 2)),
        sa.Column('revenue_gbp', sa.Numeric(18, 2)),
        sa.Column('attribution_factor', sa.Numeric(8, 6)),              # = outstanding / EVIC  (0-1)
        sa.Column('attribution_method', sa.String(30)),                 # evic | revenue | balance_sheet | pcaf_own_use

        # Emissions data (absolute)
        sa.Column('scope1_tco2e', sa.Numeric(18, 4)),
        sa.Column('scope2_market_tco2e', sa.Numeric(18, 4)),
        sa.Column('scope2_location_tco2e', sa.Numeric(18, 4)),
        sa.Column('scope3_upstream_tco2e', sa.Numeric(18, 4)),
        sa.Column('scope3_downstream_tco2e', sa.Numeric(18, 4)),
        sa.Column('scope3_total_tco2e', sa.Numeric(18, 4)),
        sa.Column('total_emissions_tco2e', sa.Numeric(18, 4)),

        # PCAF Financed emissions (attributed)
        sa.Column('financed_scope1_tco2e', sa.Numeric(18, 4)),          # attribution_factor * scope1
        sa.Column('financed_scope2_tco2e', sa.Numeric(18, 4)),
        sa.Column('financed_scope3_tco2e', sa.Numeric(18, 4)),
        sa.Column('total_financed_emissions_tco2e', sa.Numeric(18, 4)),

        # Carbon intensity
        sa.Column('revenue_intensity_tco2e_per_mrevenue', sa.Numeric(12, 4)),   # WACI numerator
        sa.Column('carbon_footprint_tco2e_per_mevic', sa.Numeric(12, 4)),

        # PCAF Data Quality Score (1=best, 5=worst)
        sa.Column('pcaf_dq_scope1', sa.SmallInteger),                   # 1-5
        sa.Column('pcaf_dq_scope2', sa.SmallInteger),
        sa.Column('pcaf_dq_scope3', sa.SmallInteger),
        sa.Column('pcaf_dq_composite', sa.Numeric(3, 1)),               # weighted average DQ

        # Emissions data vintage
        sa.Column('emissions_reporting_year', sa.Integer),
        sa.Column('emissions_data_source', sa.String(50)),              # reported | estimated_revenue | estimated_eeio | estimated_sectoral
        sa.Column('third_party_verified', sa.Boolean, default=False),
        sa.Column('assurance_provider', sa.String(100)),

        # Temperature alignment
        sa.Column('implied_temperature_c', sa.Numeric(4, 2)),
        sa.Column('sbti_committed', sa.Boolean, default=False),
        sa.Column('sbti_approved', sa.Boolean, default=False),
        sa.Column('net_zero_target_year', sa.Integer),

        # Sector-specific data (stored as JSONB for flexibility)
        sa.Column('sector_specific_data', JSONB),                       # e.g. {energy_mix_pct: {coal, gas, wind}, ...}

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.CheckConstraint("pcaf_dq_scope1 IS NULL OR pcaf_dq_scope1 BETWEEN 1 AND 5", name='ck_pcaf_investees_dq_scope1'),
        sa.CheckConstraint("pcaf_dq_scope2 IS NULL OR pcaf_dq_scope2 BETWEEN 1 AND 5", name='ck_pcaf_investees_dq_scope2'),
        sa.CheckConstraint("pcaf_dq_scope3 IS NULL OR pcaf_dq_scope3 BETWEEN 1 AND 5", name='ck_pcaf_investees_dq_scope3'),
        sa.CheckConstraint("attribution_method IN ('evic','revenue','balance_sheet','pcaf_own_use','project_value','property_value')", name='ck_pcaf_investees_attribution_method'),
    )
    op.create_index('ix_pcaf_investees_portfolio', 'pcaf_investees', ['portfolio_id'])
    op.create_index('ix_pcaf_investees_sector', 'pcaf_investees', ['sector_gics'])
    op.create_index('ix_pcaf_investees_country', 'pcaf_investees', ['country_iso'])
    op.create_index('ix_pcaf_investees_sbti', 'pcaf_investees', ['sbti_committed'])
    op.create_index('ix_pcaf_investees_dq', 'pcaf_investees', ['pcaf_dq_composite'])

    # -------------------------------------------------------------------------
    # 7. PCAF PORTFOLIO RESULTS  (aggregation versions / snapshots)
    # -------------------------------------------------------------------------
    op.create_table(
        'pcaf_portfolio_results',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('portfolio_id', UUID(as_uuid=True), sa.ForeignKey('pcaf_portfolios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('calculation_date', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('version', sa.Integer, default=1),

        # Totals
        sa.Column('total_financed_scope1_tco2e', sa.Numeric(18, 4)),
        sa.Column('total_financed_scope2_tco2e', sa.Numeric(18, 4)),
        sa.Column('total_financed_scope3_tco2e', sa.Numeric(18, 4)),
        sa.Column('total_financed_emissions_tco2e', sa.Numeric(18, 4)),

        # Portfolio Carbon KPIs
        sa.Column('waci', sa.Numeric(12, 4)),                           # tCO2e / M revenue
        sa.Column('carbon_footprint', sa.Numeric(12, 4)),               # tCO2e / M GBP invested
        sa.Column('portfolio_coverage_pct', sa.Numeric(5, 2)),
        sa.Column('weighted_avg_dq', sa.Numeric(3, 1)),

        # Temperature
        sa.Column('portfolio_temperature_c', sa.Numeric(4, 2)),
        sa.Column('aligned_1_5c_pct', sa.Numeric(5, 2)),
        sa.Column('aligned_2c_pct', sa.Numeric(5, 2)),
        sa.Column('misaligned_pct', sa.Numeric(5, 2)),

        # Year-on-year delta (vs prior year snapshot)
        sa.Column('yoy_emissions_change_pct', sa.Numeric(7, 4)),
        sa.Column('vs_base_year_change_pct', sa.Numeric(7, 4)),

        # Sector breakdown JSONB: {sector: {financed_emissions, waci, coverage_pct}}
        sa.Column('sector_breakdown', JSONB),
        # Country breakdown
        sa.Column('country_breakdown', JSONB),
        # Asset class breakdown
        sa.Column('asset_class_breakdown', JSONB),

        # Full SFDR PAI disclosure table
        sa.Column('sfdr_pai_table', JSONB),

        # Validation
        sa.Column('validation_summary', JSONB),
        sa.Column('notes', sa.Text),
    )
    op.create_index('ix_pcaf_portfolio_results_portfolio', 'pcaf_portfolio_results', ['portfolio_id'])
    op.create_index('ix_pcaf_portfolio_results_date', 'pcaf_portfolio_results', ['calculation_date'])

    # -------------------------------------------------------------------------
    # 8. TEMPERATURE SCORES  (SBTi / PACTA methodology)
    # -------------------------------------------------------------------------
    op.create_table(
        'temperature_scores',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('portfolio_id', UUID(as_uuid=True), sa.ForeignKey('pcaf_portfolios.id', ondelete='CASCADE')),
        sa.Column('assessment_date', sa.Date, nullable=False),
        sa.Column('methodology', sa.String(50), default='SBTi'),        # SBTi | PACTA | MSCI_CTI | CDP

        # Scope coverage
        sa.Column('scope_coverage', sa.String(20), default='S1S2'),     # S1 | S1S2 | S1S2S3

        # Portfolio aggregation method
        sa.Column('aggregation_method', sa.String(30), default='WATS'), # WATS | TETS | MOTS | EOTS | ECOTS | AOTS

        # Results
        sa.Column('portfolio_temperature_c', sa.Numeric(4, 2)),
        sa.Column('portfolio_temperature_s1s2_c', sa.Numeric(4, 2)),
        sa.Column('portfolio_temperature_s3_c', sa.Numeric(4, 2)),

        # Alignment
        sa.Column('pct_aligned_1_5c', sa.Numeric(5, 2)),
        sa.Column('pct_aligned_2c', sa.Numeric(5, 2)),
        sa.Column('pct_below_2c', sa.Numeric(5, 2)),
        sa.Column('pct_high_ambition', sa.Numeric(5, 2)),
        sa.Column('pct_committed', sa.Numeric(5, 2)),
        sa.Column('pct_no_target', sa.Numeric(5, 2)),

        # Sector-level temperature scores
        sa.Column('sector_temperatures', JSONB),                        # {sector: {temp_c, weight, count}}

        # SBTi specifics
        sa.Column('sbti_tool_version', sa.String(20)),
        sa.Column('timeframe', sa.String(20), default='long'),          # short | mid | long

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.CheckConstraint("methodology IN ('SBTi','PACTA','MSCI_CTI','CDP','TCFD_CLIMATEQ')", name='ck_temperature_scores_method'),
        sa.CheckConstraint("aggregation_method IN ('WATS','TETS','MOTS','EOTS','ECOTS','AOTS')", name='ck_temperature_scores_aggregation'),
    )
    op.create_index('ix_temperature_scores_portfolio', 'temperature_scores', ['portfolio_id'])
    op.create_index('ix_temperature_scores_date', 'temperature_scores', ['assessment_date'])


def downgrade():
    """Drop financial risk tables."""
    op.drop_table('temperature_scores')
    op.drop_table('pcaf_portfolio_results')
    op.drop_table('pcaf_investees')
    op.drop_table('pcaf_portfolios')
    op.drop_table('ecl_climate_overlays')
    op.drop_table('ecl_scenario_results')
    op.drop_table('ecl_exposures')
    op.drop_table('ecl_assessments')
