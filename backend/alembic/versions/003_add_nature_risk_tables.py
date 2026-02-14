"""Add nature risk tables (Standard PostgreSQL — no PostGIS, uses lat/lng columns)

Revision ID: 003_add_nature_risk_tables
Revises: 002_add_stranded_asset_tables
Create Date: 2025-01-15

Note: PostGIS geometry columns replaced with latitude/longitude float columns
and bounding box columns for spatial queries. For production PostGIS deployments,
these can be migrated to native geometry types.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '003_add_nature_risk_tables'
down_revision = '002_add_stranded_asset_tables'
branch_labels = None
depends_on = None


def upgrade():
    # 1. nature_risk_assessment (TNFD LEAP framework)
    op.create_table(
        'nature_risk_assessment',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('portfolio_id', UUID(as_uuid=True), nullable=True),
        sa.Column('assessment_name', sa.String(255), nullable=False),
        sa.Column('assessment_date', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('assessment_status', sa.String(50), server_default='in_progress'),  # in_progress, complete, reviewed
        sa.Column('locate_results', JSONB, server_default='{}'),   # LEAP: Locate
        sa.Column('evaluate_results', JSONB, server_default='{}'), # LEAP: Evaluate
        sa.Column('assess_results', JSONB, server_default='{}'),   # LEAP: Assess
        sa.Column('prepare_results', JSONB, server_default='{}'),  # LEAP: Prepare
        sa.Column('tnfd_alignment_score', sa.Numeric(5, 2)),       # 0-100
        sa.Column('scenario_id', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_nra_portfolio', 'nature_risk_assessment', ['portfolio_id'])
    op.create_index('idx_nra_status', 'nature_risk_assessment', ['assessment_status'])

    # 2. ecosystem_dependency
    op.create_table(
        'ecosystem_dependency',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('asset_id', UUID(as_uuid=True), nullable=True),
        sa.Column('counterparty_id', UUID(as_uuid=True), nullable=True),
        sa.Column('ecosystem_type', sa.String(100), nullable=False),     # tropical_forest, freshwater, marine, grassland, wetland
        sa.Column('ecosystem_service', sa.String(100), nullable=False),  # water_purification, pollination, flood_protection, carbon_sequestration
        sa.Column('dependency_score', sa.Numeric(3, 2)),                 # 0.00-1.00
        sa.Column('dependency_category', sa.String(20)),                 # very_high, high, medium, low
        sa.Column('materiality_rating', sa.String(20)),                  # material, potentially_material, not_material
        sa.Column('financial_exposure_usd', sa.Numeric(18, 2)),
        sa.Column('assessment_date', sa.Date, server_default=sa.func.current_date()),
        sa.UniqueConstraint('asset_id', 'ecosystem_type', 'ecosystem_service', name='uq_eco_dependency'),
    )
    op.create_index('idx_eco_dep_asset', 'ecosystem_dependency', ['asset_id'])
    op.create_index('idx_eco_dep_counterparty', 'ecosystem_dependency', ['counterparty_id'])
    op.create_index('idx_eco_dep_score', 'ecosystem_dependency', ['dependency_score'])
    op.create_index('idx_eco_dep_type', 'ecosystem_dependency', ['ecosystem_type'])

    # 3. spatial_asset_mapping (lat/lng instead of PostGIS geometry)
    op.create_table(
        'spatial_asset_mapping',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('asset_id', UUID(as_uuid=True), nullable=True),
        sa.Column('counterparty_id', UUID(as_uuid=True), nullable=True),
        sa.Column('asset_name', sa.String(255)),
        sa.Column('country_code', sa.String(2)),
        # Centroid coordinates (replaces PostGIS POINT geometry)
        sa.Column('latitude', sa.Numeric(9, 6)),    # -90 to +90
        sa.Column('longitude', sa.Numeric(10, 6)),   # -180 to +180
        # Bounding box (replaces PostGIS POLYGON geometry for area queries)
        sa.Column('bbox_min_lat', sa.Numeric(9, 6)),
        sa.Column('bbox_max_lat', sa.Numeric(9, 6)),
        sa.Column('bbox_min_lng', sa.Numeric(10, 6)),
        sa.Column('bbox_max_lng', sa.Numeric(10, 6)),
        sa.Column('area_hectares', sa.Numeric(15, 4)),
        sa.Column('ecosystem_type', sa.String(100)),
        sa.Column('protected_area_status', sa.String(50)),      # iucn_ia, iucn_ib, iucn_ii, ... none
        sa.Column('protected_area_overlap_pct', sa.Numeric(5, 2)),
        sa.Column('kba_overlap', sa.Boolean, server_default=sa.false()),  # Key Biodiversity Area
        sa.Column('deforestation_rate_pct', sa.Numeric(5, 2)),
        sa.Column('water_stress_level', sa.String(20)),         # low, low_medium, medium_high, high, extremely_high
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_sam_asset', 'spatial_asset_mapping', ['asset_id'])
    op.create_index('idx_sam_counterparty', 'spatial_asset_mapping', ['counterparty_id'])
    op.create_index('idx_sam_country', 'spatial_asset_mapping', ['country_code'])
    # Spatial indexes using lat/lng (for bounding box queries)
    op.create_index('idx_sam_lat_lng', 'spatial_asset_mapping', ['latitude', 'longitude'])
    op.create_index('idx_sam_bbox', 'spatial_asset_mapping', ['bbox_min_lat', 'bbox_max_lat', 'bbox_min_lng', 'bbox_max_lng'])
    op.create_index('idx_sam_protected', 'spatial_asset_mapping', ['protected_area_status'])

    # 4. biodiversity_metric (Standard PostgreSQL with optimized indexes — NO TimescaleDB)
    op.create_table(
        'biodiversity_metric',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('scenario_id', UUID(as_uuid=True), nullable=True),
        sa.Column('metric_type', sa.String(100), nullable=False),  # msa, bii, species_richness, habitat_integrity, extinction_risk
        sa.Column('location_id', UUID(as_uuid=True), nullable=True),  # FK to spatial_asset_mapping
        sa.Column('country_code', sa.String(2)),
        sa.Column('latitude', sa.Numeric(9, 6)),
        sa.Column('longitude', sa.Numeric(10, 6)),
        sa.Column('basin_id', sa.String(50)),
        sa.Column('baseline_value', sa.Numeric(15, 6)),
        sa.Column('target_value', sa.Numeric(15, 6)),
        sa.Column('measurement_date', sa.Date, nullable=False),
        sa.Column('value', sa.Numeric(15, 6)),
        sa.Column('data_source', sa.String(100)),   # globio, iucn, unep_wcmc, copernicus
        sa.Column('is_projected', sa.Boolean, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    # Optimized indexes for time-series queries (replacing TimescaleDB hypertable)
    op.create_index('idx_bm_date_type', 'biodiversity_metric', ['measurement_date', 'metric_type'])
    op.create_index('idx_bm_date_scenario', 'biodiversity_metric', ['measurement_date', 'scenario_id'])
    op.create_index('idx_bm_date_range', 'biodiversity_metric', [sa.text('measurement_date DESC')])
    op.create_index('idx_bm_location', 'biodiversity_metric', ['location_id'])
    op.create_index('idx_bm_lat_lng', 'biodiversity_metric', ['latitude', 'longitude'])
    op.create_index('idx_bm_country', 'biodiversity_metric', ['country_code', 'metric_type'])

    # 5. water_risk_assessment
    op.create_table(
        'water_risk_assessment',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('asset_id', UUID(as_uuid=True), nullable=True),
        sa.Column('country_code', sa.String(2), nullable=False),
        sa.Column('basin_id', sa.String(50)),
        sa.Column('basin_name', sa.String(100)),
        sa.Column('latitude', sa.Numeric(9, 6)),
        sa.Column('longitude', sa.Numeric(10, 6)),
        sa.Column('baseline_overall_risk', sa.Numeric(3, 2)),  # WRI Aqueduct 0-5 scale
        sa.Column('projected_risk_2030', JSONB, server_default='{}'),
        sa.Column('projected_risk_2040', JSONB, server_default='{}'),
        sa.Column('projected_risk_2050', JSONB, server_default='{}'),
        sa.Column('aqueduct_bws_score', sa.Numeric(5, 2)),     # Baseline Water Stress
        sa.Column('risk_category', sa.Integer),                  # 1-5
        sa.Column('risk_category_label', sa.String(20)),         # Low, Low-Medium, Medium-High, High, Extremely High
        sa.Column('water_risk_exposure_usd', sa.Numeric(18, 2)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_wra_asset', 'water_risk_assessment', ['asset_id'])
    op.create_index('idx_wra_risk', 'water_risk_assessment', ['risk_category'])
    op.create_index('idx_wra_country', 'water_risk_assessment', ['country_code'])
    op.create_index('idx_wra_basin', 'water_risk_assessment', ['basin_id'])

    # 6. nature_scenario (TNFD/IPBES-aligned)
    op.create_table(
        'nature_scenario',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('scenario_type', sa.String(100), nullable=False),  # tnfd_current_trajectory, tnfd_sustainable, ipbes_ssps, custom
        sa.Column('gbf_target_alignment', JSONB, server_default='[]'),  # Global Biodiversity Framework targets
        sa.Column('gbf_alignment_score', sa.Numeric(5, 2)),            # 0-100
        sa.Column('parameters', JSONB, server_default='{}'),
        sa.Column('baseline_year', sa.Integer, server_default='2020'),
        sa.Column('short_term_year', sa.Integer, server_default='2030'),
        sa.Column('medium_term_year', sa.Integer, server_default='2040'),
        sa.Column('long_term_year', sa.Integer, server_default='2050'),
        sa.Column('is_active', sa.Boolean, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_nature_scenario_type', 'nature_scenario', ['scenario_type'])
    op.create_index('idx_nature_scenario_active', 'nature_scenario', ['is_active'])

    # 7. nature_impact_pathway (TNFD impact/dependency driver mapping)
    op.create_table(
        'nature_impact_pathway',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('assessment_id', UUID(as_uuid=True), nullable=True),
        sa.Column('asset_id', UUID(as_uuid=True), nullable=True),
        sa.Column('pathway_type', sa.String(50), nullable=False),       # dependency, impact
        sa.Column('driver_category', sa.String(50), nullable=False),    # land_use_change, pollution, overexploitation, invasive_species, climate_change
        sa.Column('ecosystem_service', sa.String(100)),
        sa.Column('impact_magnitude', sa.Numeric(5, 2)),                # 0-10
        sa.Column('impact_probability', sa.Numeric(3, 2)),              # 0-1
        sa.Column('financial_impact_usd', sa.Numeric(18, 2)),
        sa.Column('risk_rating', sa.String(20)),                        # critical, high, medium, low
        sa.Column('mitigation_actions', JSONB, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_nip_assessment', 'nature_impact_pathway', ['assessment_id'])
    op.create_index('idx_nip_asset', 'nature_impact_pathway', ['asset_id'])
    op.create_index('idx_nip_driver', 'nature_impact_pathway', ['driver_category'])
    op.create_index('idx_nip_rating', 'nature_impact_pathway', ['risk_rating'])

    # 8. tnfd_disclosure_metric (TNFD recommended disclosures)
    op.create_table(
        'tnfd_disclosure_metric',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('assessment_id', UUID(as_uuid=True), nullable=True),
        sa.Column('portfolio_id', UUID(as_uuid=True), nullable=True),
        sa.Column('metric_id', sa.String(50), nullable=False),         # e.g., C1.1, C2.1, C3.1
        sa.Column('metric_name', sa.String(255)),
        sa.Column('metric_category', sa.String(50)),                   # governance, strategy, risk_management, metrics_targets
        sa.Column('gbf_target', sa.String(20)),                        # e.g., T1, T2, T3, ...
        sa.Column('metric_value', sa.Numeric(18, 6)),
        sa.Column('metric_unit', sa.String(50)),
        sa.Column('scope', sa.String(50)),                             # direct_operations, upstream, downstream
        sa.Column('baseline_year', sa.Integer),
        sa.Column('reporting_year', sa.Integer),
        sa.Column('is_compliant', sa.Boolean, server_default=sa.false()),
        sa.Column('evidence_notes', sa.Text),
        sa.UniqueConstraint('assessment_id', 'metric_id', name='uq_tnfd_metric'),
    )
    op.create_index('idx_tnfd_assessment', 'tnfd_disclosure_metric', ['assessment_id'])
    op.create_index('idx_tnfd_portfolio', 'tnfd_disclosure_metric', ['portfolio_id'])
    op.create_index('idx_tnfd_category', 'tnfd_disclosure_metric', ['metric_category'])
    op.create_index('idx_tnfd_gbf', 'tnfd_disclosure_metric', ['gbf_target'])

    # 9. external_data_cache (for GBIF, IUCN, WRI Aqueduct API responses)
    op.create_table(
        'external_data_cache',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('data_source', sa.String(100), nullable=False),  # gbif, iucn_red_list, wri_aqueduct, unep_wcmc, copernicus
        sa.Column('endpoint', sa.String(255), nullable=False),
        sa.Column('query_params', JSONB, server_default='{}'),
        sa.Column('response_data', JSONB),
        sa.Column('latitude', sa.Numeric(9, 6)),
        sa.Column('longitude', sa.Numeric(10, 6)),
        sa.Column('bbox_min_lat', sa.Numeric(9, 6)),
        sa.Column('bbox_max_lat', sa.Numeric(9, 6)),
        sa.Column('bbox_min_lng', sa.Numeric(10, 6)),
        sa.Column('bbox_max_lng', sa.Numeric(10, 6)),
        sa.Column('fetched_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True)),
        sa.Column('is_valid', sa.Boolean, server_default=sa.true()),
    )
    op.create_index('idx_edc_source', 'external_data_cache', ['data_source'])
    op.create_index('idx_edc_source_endpoint', 'external_data_cache', ['data_source', 'endpoint'])
    op.create_index('idx_edc_lat_lng', 'external_data_cache', ['latitude', 'longitude'])
    op.create_index('idx_edc_valid', 'external_data_cache', ['is_valid', 'expires_at'])

    # 10. nature_risk_adjustment (PD adjustments from nature risks)
    op.create_table(
        'nature_risk_adjustment',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('asset_id', UUID(as_uuid=True), nullable=True),
        sa.Column('counterparty_id', UUID(as_uuid=True), nullable=True),
        sa.Column('base_pd', sa.Numeric(8, 6)),
        sa.Column('water_risk_multiplier', sa.Numeric(5, 4), server_default='1.0'),
        sa.Column('biodiversity_risk_multiplier', sa.Numeric(5, 4), server_default='1.0'),
        sa.Column('deforestation_risk_multiplier', sa.Numeric(5, 4), server_default='1.0'),
        sa.Column('nature_pd_multiplier', sa.Numeric(5, 4), server_default='1.0'),  # combined
        sa.Column('adjusted_pd', sa.Numeric(8, 6)),
        sa.Column('assessment_date', sa.Date, server_default=sa.func.current_date()),
        sa.Column('scenario_id', UUID(as_uuid=True), nullable=True),
        sa.Column('methodology_notes', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_nature_adj_asset', 'nature_risk_adjustment', ['asset_id'])
    op.create_index('idx_nature_adj_counterparty', 'nature_risk_adjustment', ['counterparty_id'])
    op.create_index('idx_nature_adj_scenario', 'nature_risk_adjustment', ['scenario_id'])
    op.create_index('idx_nature_adj_date', 'nature_risk_adjustment', ['assessment_date'])


def downgrade():
    op.drop_table('nature_risk_adjustment')
    op.drop_table('external_data_cache')
    op.drop_table('tnfd_disclosure_metric')
    op.drop_table('nature_impact_pathway')
    op.drop_table('nature_scenario')
    op.drop_table('water_risk_assessment')
    op.drop_table('biodiversity_metric')
    op.drop_table('spatial_asset_mapping')
    op.drop_table('ecosystem_dependency')
    op.drop_table('nature_risk_assessment')
