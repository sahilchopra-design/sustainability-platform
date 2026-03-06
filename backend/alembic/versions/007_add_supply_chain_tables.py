"""
Add Supply Chain Tables

Revision ID: 007_add_supply_chain_tables
Revises: 006_add_financial_risk_tables
Create Date: 2026-03-01

This migration adds tables for the Supply Chain Sustainability module:
- sc_entities               : Corporate entities subject to supply chain assessment
- scope3_assessments        : Portfolio-level GHG Protocol Scope 3 assessments (15 categories)
- scope3_activities         : Individual activity-level data rows (granular inventory)
- scope3_hotspots           : Identified emission hotspots and reduction opportunities
- sbti_targets              : Science Based Targets (SBTi Corporate Net-Zero Standard v2.0)
- sbti_trajectories         : Year-by-year emission trajectory milestones
- emission_factor_library   : Reference emission factors (IEA, DEFRA, EPA, ecoinvent, IPCC)
- supply_chain_tiers        : Tier 1 / 2 / 3 supplier mapping and emission data
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '007_add_supply_chain_tables'
down_revision = '006_add_financial_risk_tables'
branch_labels = None
depends_on = None


def upgrade():
    """Create supply chain tables."""

    # -------------------------------------------------------------------------
    # 1. SC ENTITIES  (corporate entities / reporting organisations)
    # -------------------------------------------------------------------------
    op.create_table(
        'sc_entities',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('legal_name', sa.String(255), nullable=False),
        sa.Column('trading_name', sa.String(255)),
        sa.Column('lei', sa.String(20)),
        sa.Column('duns_number', sa.String(15)),
        sa.Column('sector_gics', sa.String(50)),
        sa.Column('nace_code', sa.String(10)),
        sa.Column('naics_code', sa.String(10)),
        sa.Column('country_iso', sa.String(3), nullable=False),
        sa.Column('headquarters_city', sa.String(100)),
        sa.Column('annual_revenue_gbp', sa.Numeric(18, 2)),
        sa.Column('headcount', sa.Integer),
        sa.Column('is_listed', sa.Boolean, default=False),
        sa.Column('entity_type', sa.String(30), default='corporate'),   # corporate | sme | government | ngo
        sa.Column('fiscal_year_end', sa.String(5)),                     # MM-DD format e.g. '12-31'
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_sc_entities_name', 'sc_entities', ['legal_name'])
    op.create_index('ix_sc_entities_sector', 'sc_entities', ['sector_gics'])
    op.create_index('ix_sc_entities_country', 'sc_entities', ['country_iso'])

    # -------------------------------------------------------------------------
    # 2. SCOPE3 ASSESSMENTS  (top-level Scope 3 inventory run)
    # -------------------------------------------------------------------------
    op.create_table(
        'scope3_assessments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_id', UUID(as_uuid=True), sa.ForeignKey('sc_entities.id', ondelete='SET NULL')),
        sa.Column('entity_name', sa.String(255), nullable=False),       # denormalised for portability
        sa.Column('reporting_year', sa.Integer, nullable=False),
        sa.Column('base_currency', sa.String(3), default='GBP'),
        sa.Column('calculation_approach', sa.String(30), default='activity_based'),  # activity_based | spend_based | hybrid | eeio

        # Scope 1 & 2 (contextual, not calculated here)
        sa.Column('scope1_tco2e', sa.Numeric(14, 4)),
        sa.Column('scope2_market_tco2e', sa.Numeric(14, 4)),
        sa.Column('scope2_location_tco2e', sa.Numeric(14, 4)),

        # Scope 3 category totals (GHG Protocol 15 categories)
        sa.Column('cat1_purchased_goods_tco2e', sa.Numeric(14, 4)),
        sa.Column('cat2_capital_goods_tco2e', sa.Numeric(14, 4)),
        sa.Column('cat3_fuel_energy_tco2e', sa.Numeric(14, 4)),
        sa.Column('cat4_upstream_transport_tco2e', sa.Numeric(14, 4)),
        sa.Column('cat5_waste_tco2e', sa.Numeric(14, 4)),
        sa.Column('cat6_business_travel_tco2e', sa.Numeric(14, 4)),
        sa.Column('cat7_employee_commuting_tco2e', sa.Numeric(14, 4)),
        sa.Column('cat8_upstream_leased_tco2e', sa.Numeric(14, 4)),
        sa.Column('cat9_downstream_transport_tco2e', sa.Numeric(14, 4)),
        sa.Column('cat10_processing_tco2e', sa.Numeric(14, 4)),
        sa.Column('cat11_use_of_sold_products_tco2e', sa.Numeric(14, 4)),
        sa.Column('cat12_eol_treatment_tco2e', sa.Numeric(14, 4)),
        sa.Column('cat13_downstream_leased_tco2e', sa.Numeric(14, 4)),
        sa.Column('cat14_franchises_tco2e', sa.Numeric(14, 4)),
        sa.Column('cat15_investments_tco2e', sa.Numeric(14, 4)),

        # Totals
        sa.Column('total_scope3_upstream_tco2e', sa.Numeric(14, 4)),
        sa.Column('total_scope3_downstream_tco2e', sa.Numeric(14, 4)),
        sa.Column('total_scope3_tco2e', sa.Numeric(14, 4)),
        sa.Column('total_scope123_tco2e', sa.Numeric(14, 4)),

        # Data quality
        sa.Column('data_quality_score_avg', sa.Numeric(3, 1)),          # 1-5 (GHG Protocol DQ tiers)
        sa.Column('primary_data_pct', sa.Numeric(5, 2)),                # % of emissions with primary data
        sa.Column('coverage_completeness_pct', sa.Numeric(5, 2)),       # % of categories assessed

        # Category coverage flags (array of included categories)
        sa.Column('categories_included', JSONB),                        # [1,2,3,...] category numbers
        sa.Column('categories_excluded', JSONB),                        # [{cat: 10, reason: 'not applicable'}]

        # Intensity metrics
        sa.Column('intensity_revenue_tco2e_per_mrevenue', sa.Numeric(12, 4)),
        sa.Column('intensity_headcount_tco2e_per_fte', sa.Numeric(10, 4)),

        # Summary and validation
        sa.Column('hotspot_summary', JSONB),                            # [{category, tco2e, pct_share, priority}]
        sa.Column('reduction_opportunities', JSONB),                    # [{description, estimated_reduction_tco2e, cost_gbp, payback_years}]
        sa.Column('validation_summary', JSONB),
        sa.Column('methodology_notes', sa.Text),
        sa.Column('boundary', sa.String(30), default='operational_control'),  # operational_control | equity_share | financial_control
        sa.Column('assurance_type', sa.String(20)),                     # none | limited | reasonable
        sa.Column('assurance_provider', sa.String(100)),

        sa.Column('status', sa.String(20), default='draft'),
        sa.Column('created_by', UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.CheckConstraint("calculation_approach IN ('activity_based','spend_based','hybrid','eeio','supplier_specific')", name='ck_scope3_assessments_approach'),
        sa.CheckConstraint("boundary IN ('operational_control','equity_share','financial_control')", name='ck_scope3_assessments_boundary'),
        sa.CheckConstraint("status IN ('draft','submitted','approved','published','archived')", name='ck_scope3_assessments_status'),
    )
    op.create_index('ix_scope3_assessments_entity', 'scope3_assessments', ['entity_id'])
    op.create_index('ix_scope3_assessments_year', 'scope3_assessments', ['reporting_year'])
    op.create_index('ix_scope3_assessments_status', 'scope3_assessments', ['status'])

    # -------------------------------------------------------------------------
    # 3. SCOPE3 ACTIVITIES  (granular activity-level data rows)
    # -------------------------------------------------------------------------
    op.create_table(
        'scope3_activities',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('assessment_id', UUID(as_uuid=True), sa.ForeignKey('scope3_assessments.id', ondelete='CASCADE'), nullable=False),

        # Category
        sa.Column('category_number', sa.SmallInteger, nullable=False),  # 1-15
        sa.Column('category_label', sa.String(100)),
        sa.Column('sub_category', sa.String(100)),                      # e.g. 'air travel long haul', 'grid electricity UK'

        # Activity data
        sa.Column('activity_description', sa.String(255)),
        sa.Column('activity_quantity', sa.Numeric(18, 4), nullable=False),
        sa.Column('activity_unit', sa.String(30), nullable=False),      # tonne | kg | kWh | MWh | GJ | litre | km | tonne-km | GBP_spend | m2 | unit | pass-km
        sa.Column('data_source', sa.String(100)),                       # metered | invoiced | modelled | estimated | supplier_reported
        sa.Column('data_collection_period', sa.String(50)),             # e.g. 'Jan 2025 - Dec 2025'

        # Supplier / asset reference (optional)
        sa.Column('supplier_name', sa.String(255)),
        sa.Column('supplier_country_iso', sa.String(3)),
        sa.Column('asset_id', sa.String(100)),
        sa.Column('cost_centre', sa.String(50)),

        # Emission factor applied
        sa.Column('emission_factor_id', UUID(as_uuid=True)),            # FK to emission_factor_library
        sa.Column('emission_factor_value', sa.Numeric(14, 8)),          # kgCO2e per unit
        sa.Column('emission_factor_unit', sa.String(30)),
        sa.Column('emission_factor_source', sa.String(50)),             # DEFRA | IEA | EPA | ecoinvent | supplier
        sa.Column('emission_factor_year', sa.Integer),
        sa.Column('global_warming_potential', sa.String(10), default='AR6'),  # AR4 | AR5 | AR6

        # Gas-level breakdown (stored as JSONB for flexibility with non-CO2 gases)
        sa.Column('emissions_by_gas', JSONB),                           # {co2: x, ch4: y, n2o: z, hfc: ..., pfc: ..., sf6: ...}

        # GHG totals
        sa.Column('co2e_tco2e', sa.Numeric(14, 6), nullable=False),     # total tCO2e for this row
        sa.Column('biogenic_co2_tco2e', sa.Numeric(14, 6)),            # separately reported per GHG Protocol

        # Data quality
        sa.Column('pcaf_dq_score', sa.SmallInteger),                    # 1-5
        sa.Column('ghg_protocol_dq_tier', sa.String(20)),               # primary | secondary | proxy | default
        sa.Column('uncertainty_pct', sa.Numeric(5, 2)),                 # ± percentage uncertainty

        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.CheckConstraint("category_number BETWEEN 1 AND 15", name='ck_scope3_activities_category'),
        sa.CheckConstraint("pcaf_dq_score IS NULL OR pcaf_dq_score BETWEEN 1 AND 5", name='ck_scope3_activities_dq'),
    )
    op.create_index('ix_scope3_activities_assessment', 'scope3_activities', ['assessment_id'])
    op.create_index('ix_scope3_activities_category', 'scope3_activities', ['category_number'])
    op.create_index('ix_scope3_activities_supplier', 'scope3_activities', ['supplier_name'])
    op.create_index('ix_scope3_activities_dq', 'scope3_activities', ['pcaf_dq_score'])

    # -------------------------------------------------------------------------
    # 4. SBTI TARGETS  (Science Based Targets Corporate Net-Zero Standard v2.0)
    # -------------------------------------------------------------------------
    op.create_table(
        'sbti_targets',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_id', UUID(as_uuid=True), sa.ForeignKey('sc_entities.id', ondelete='SET NULL')),
        sa.Column('entity_name', sa.String(255), nullable=False),

        # Target parameters
        sa.Column('target_type', sa.String(30), nullable=False),        # near_term | long_term | net_zero
        sa.Column('sbti_pathway', sa.String(30), nullable=False),       # 1.5C_absolute | well_below_2C | 2C_sda | 2C_absolute
        sa.Column('sbti_sector', sa.String(50)),                        # for sector-specific pathways (power | transport | buildings | ...)
        sa.Column('scope_coverage', sa.String(20), default='S1S2S3'),   # S1 | S1S2 | S1S2S3
        sa.Column('sbti_status', sa.String(30), default='committed'),   # committed | submitted | approved | achieved | lapsed

        # Baseline
        sa.Column('base_year', sa.Integer, nullable=False),
        sa.Column('base_year_scope1_tco2e', sa.Numeric(14, 4)),
        sa.Column('base_year_scope2_tco2e', sa.Numeric(14, 4)),
        sa.Column('base_year_scope3_tco2e', sa.Numeric(14, 4)),
        sa.Column('base_year_total_tco2e', sa.Numeric(14, 4), nullable=False),

        # Near-term target (2030 or 5–10 years from base)
        sa.Column('near_term_target_year', sa.Integer),
        sa.Column('near_term_reduction_pct', sa.Numeric(5, 2)),         # % reduction vs base year
        sa.Column('near_term_target_tco2e', sa.Numeric(14, 4)),

        # Long-term / net-zero target (2050 or earlier)
        sa.Column('long_term_target_year', sa.Integer),
        sa.Column('long_term_reduction_pct', sa.Numeric(5, 2)),         # ≥90% per SBTi Net-Zero Standard
        sa.Column('long_term_target_tco2e', sa.Numeric(14, 4)),

        # Residual emissions and offsets
        sa.Column('residual_emissions_tco2e', sa.Numeric(14, 4)),       # max 10% of base year
        sa.Column('carbon_removal_required_tco2e', sa.Numeric(14, 4)),
        sa.Column('removal_mechanism', sa.String(100)),                 # BECCS | DACCS | Afforestation | etc.

        # Annual CAGR reduction rate
        sa.Column('near_term_annual_reduction_rate_pct', sa.Numeric(5, 4)),
        sa.Column('long_term_annual_reduction_rate_pct', sa.Numeric(5, 4)),

        # SBTi validation
        sa.Column('sbti_submission_date', sa.Date),
        sa.Column('sbti_approval_date', sa.Date),
        sa.Column('sbti_reference_number', sa.String(50)),
        sa.Column('sbti_tool_version', sa.String(20)),

        # Validation summary
        sa.Column('validation_summary', JSONB),
        sa.Column('notes', sa.Text),

        sa.Column('created_by', UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.CheckConstraint("target_type IN ('near_term','long_term','net_zero','interim')", name='ck_sbti_targets_type'),
        sa.CheckConstraint("sbti_pathway IN ('1.5C_absolute','well_below_2C','2C_sda','2C_absolute','1.5C_sda')", name='ck_sbti_targets_pathway'),
        sa.CheckConstraint("sbti_status IN ('committed','submitted','approved','achieved','lapsed','withdrawn')", name='ck_sbti_targets_status'),
    )
    op.create_index('ix_sbti_targets_entity', 'sbti_targets', ['entity_id'])
    op.create_index('ix_sbti_targets_status', 'sbti_targets', ['sbti_status'])
    op.create_index('ix_sbti_targets_pathway', 'sbti_targets', ['sbti_pathway'])

    # -------------------------------------------------------------------------
    # 5. SBTI TRAJECTORIES  (year-by-year emission milestones)
    # -------------------------------------------------------------------------
    op.create_table(
        'sbti_trajectories',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('target_id', UUID(as_uuid=True), sa.ForeignKey('sbti_targets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('year', sa.Integer, nullable=False),

        # Target pathway (calculated from SBTi tool)
        sa.Column('target_emissions_tco2e', sa.Numeric(14, 4), nullable=False),
        sa.Column('scope1_target_tco2e', sa.Numeric(14, 4)),
        sa.Column('scope2_target_tco2e', sa.Numeric(14, 4)),
        sa.Column('scope3_target_tco2e', sa.Numeric(14, 4)),

        # Cumulative reduction
        sa.Column('cumulative_reduction_pct', sa.Numeric(6, 4)),

        # Actual reported emissions (filled in retrospectively)
        sa.Column('actual_emissions_tco2e', sa.Numeric(14, 4)),
        sa.Column('actual_scope1_tco2e', sa.Numeric(14, 4)),
        sa.Column('actual_scope2_tco2e', sa.Numeric(14, 4)),
        sa.Column('actual_scope3_tco2e', sa.Numeric(14, 4)),

        # On-track flag
        sa.Column('is_on_track', sa.Boolean),
        sa.Column('deviation_pct', sa.Numeric(7, 4)),                  # (actual - target) / target * 100

        # Pathway benchmark (1.5°C / WB2C / 2°C aligned threshold)
        sa.Column('benchmark_1_5c_tco2e', sa.Numeric(14, 4)),
        sa.Column('benchmark_2c_tco2e', sa.Numeric(14, 4)),
        sa.Column('carbon_budget_remaining_tco2e', sa.Numeric(14, 4)),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_sbti_trajectories_target', 'sbti_trajectories', ['target_id'])
    op.create_index('ix_sbti_trajectories_year', 'sbti_trajectories', ['year'])
    op.create_index('ix_sbti_trajectories_on_track', 'sbti_trajectories', ['is_on_track'])

    # -------------------------------------------------------------------------
    # 6. EMISSION FACTOR LIBRARY  (reference database)
    # -------------------------------------------------------------------------
    op.create_table(
        'emission_factor_library',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),

        # Classification
        sa.Column('activity_type', sa.String(100), nullable=False),     # e.g. 'grid_electricity' | 'diesel_road_freight' | 'natural_gas_combustion'
        sa.Column('activity_sub_type', sa.String(100)),                 # e.g. 'UK grid average' | 'long haul air'
        sa.Column('scope', sa.SmallInteger),                            # 1, 2, or 3
        sa.Column('category_number', sa.SmallInteger),                  # Scope 3 category 1-15 (NULL for S1/S2)
        sa.Column('ghg', sa.String(10), default='CO2e'),                # CO2e | CO2 | CH4 | N2O | HFCs | PFCs | SF6

        # Geographic coverage
        sa.Column('country_iso', sa.String(3)),                         # NULL = global
        sa.Column('region', sa.String(50)),                             # e.g. 'Europe' | 'Asia-Pacific'
        sa.Column('grid_region', sa.String(50)),                        # for electricity factors

        # Temporal
        sa.Column('valid_from_year', sa.Integer),
        sa.Column('valid_to_year', sa.Integer),

        # Factor value
        sa.Column('factor_value', sa.Numeric(14, 8), nullable=False),  # e.g. 0.23314 kgCO2e/kWh
        sa.Column('factor_unit', sa.String(50), nullable=False),        # kgCO2e/kWh | kgCO2e/tonne | kgCO2e/km | tCO2e/MWh
        sa.Column('factor_per_unit', sa.String(50)),                    # denominator unit only (kWh, tonne, km, ...)

        # Confidence / uncertainty
        sa.Column('uncertainty_low_pct', sa.Numeric(5, 2)),
        sa.Column('uncertainty_high_pct', sa.Numeric(5, 2)),
        sa.Column('data_quality_tier', sa.String(20), default='secondary'),  # primary | secondary | proxy | default

        # Source
        sa.Column('source_name', sa.String(100), nullable=False),       # DEFRA | IEA | EPA_eGRID | ecoinvent | IPCC | GHG_Protocol | supplier
        sa.Column('source_url', sa.String(500)),
        sa.Column('source_year', sa.Integer),
        sa.Column('source_version', sa.String(30)),

        # GWP characterisation factors
        sa.Column('gwp_basis', sa.String(10), default='AR6'),           # AR4 | AR5 | AR6

        # Additional context
        sa.Column('technology_type', sa.String(50)),                    # for electricity: 'wind', 'solar', 'coal', ...
        sa.Column('fuel_type', sa.String(50)),
        sa.Column('transport_mode', sa.String(30)),                     # road | rail | sea | air | pipeline
        sa.Column('load_factor', sa.Numeric(5, 4)),                     # for transport EFs
        sa.Column('notes', sa.Text),
        sa.Column('is_active', sa.Boolean, default=True),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.CheckConstraint("scope IN (1,2,3)", name='ck_ef_library_scope'),
        sa.CheckConstraint("category_number IS NULL OR category_number BETWEEN 1 AND 15", name='ck_ef_library_category'),
    )
    op.create_index('ix_ef_library_activity_type', 'emission_factor_library', ['activity_type'])
    op.create_index('ix_ef_library_country', 'emission_factor_library', ['country_iso'])
    op.create_index('ix_ef_library_year', 'emission_factor_library', ['valid_from_year', 'valid_to_year'])
    op.create_index('ix_ef_library_source', 'emission_factor_library', ['source_name'])
    op.create_index('ix_ef_library_active', 'emission_factor_library', ['is_active'])

    # -------------------------------------------------------------------------
    # 7. SUPPLY CHAIN TIERS  (multi-tier supplier mapping)
    # -------------------------------------------------------------------------
    op.create_table(
        'supply_chain_tiers',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('buyer_entity_id', UUID(as_uuid=True), sa.ForeignKey('sc_entities.id', ondelete='CASCADE')),
        sa.Column('buyer_entity_name', sa.String(255)),

        # Supplier details
        sa.Column('supplier_name', sa.String(255), nullable=False),
        sa.Column('supplier_lei', sa.String(20)),
        sa.Column('supplier_duns', sa.String(15)),
        sa.Column('supplier_country_iso', sa.String(3)),
        sa.Column('supplier_sector_gics', sa.String(50)),
        sa.Column('tier', sa.SmallInteger, nullable=False),             # 1, 2, or 3
        sa.Column('spend_gbp', sa.Numeric(14, 2)),
        sa.Column('spend_pct_of_total', sa.Numeric(5, 2)),

        # Emissions (from supplier or modelled)
        sa.Column('scope1_tco2e', sa.Numeric(14, 4)),
        sa.Column('scope2_tco2e', sa.Numeric(14, 4)),
        sa.Column('scope12_tco2e', sa.Numeric(14, 4)),
        sa.Column('attributed_scope3_tco2e', sa.Numeric(14, 4)),        # our proportional share (cat 1)

        # Data source
        sa.Column('emissions_data_source', sa.String(50)),              # supplier_reported | spend_based | eeio | modelled
        sa.Column('pcaf_dq_score', sa.SmallInteger),
        sa.Column('reporting_year', sa.Integer),
        sa.Column('has_sbti_target', sa.Boolean, default=False),
        sa.Column('has_cdp_disclosure', sa.Boolean, default=False),

        # Engagement status
        sa.Column('engagement_status', sa.String(30), default='not_engaged'), # not_engaged | contacted | committed | reporting
        sa.Column('engagement_date', sa.Date),
        sa.Column('reduction_target_pct', sa.Numeric(5, 2)),
        sa.Column('contract_leverage', sa.Boolean, default=False),

        # Risk flags
        sa.Column('high_emission_flag', sa.Boolean, default=False),
        sa.Column('deforestation_risk', sa.Boolean, default=False),
        sa.Column('human_rights_risk', sa.Boolean, default=False),

        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.CheckConstraint("tier BETWEEN 1 AND 3", name='ck_supply_chain_tiers_tier'),
        sa.CheckConstraint("pcaf_dq_score IS NULL OR pcaf_dq_score BETWEEN 1 AND 5", name='ck_supply_chain_tiers_dq'),
        sa.CheckConstraint("engagement_status IN ('not_engaged','contacted','committed','reporting','achieved')", name='ck_supply_chain_tiers_engagement'),
    )
    op.create_index('ix_supply_chain_tiers_buyer', 'supply_chain_tiers', ['buyer_entity_id'])
    op.create_index('ix_supply_chain_tiers_supplier', 'supply_chain_tiers', ['supplier_name'])
    op.create_index('ix_supply_chain_tiers_tier', 'supply_chain_tiers', ['tier'])
    op.create_index('ix_supply_chain_tiers_country', 'supply_chain_tiers', ['supplier_country_iso'])
    op.create_index('ix_supply_chain_tiers_high_emission', 'supply_chain_tiers', ['high_emission_flag'])


def downgrade():
    """Drop supply chain tables."""
    op.drop_table('supply_chain_tiers')
    op.drop_table('emission_factor_library')
    op.drop_table('sbti_trajectories')
    op.drop_table('sbti_targets')
    op.drop_table('scope3_activities')
    op.drop_table('scope3_assessments')
    op.drop_table('sc_entities')
