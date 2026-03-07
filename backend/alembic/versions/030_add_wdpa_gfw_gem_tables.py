"""
Migration 030 -- WDPA Protected Areas, GFW Tree Cover Loss, GEM Global Coal Plant Tracker

Tables (5):
  dh_wdpa_protected_areas     -- World Database on Protected Areas (UNEP-WCMC / IUCN)
  dh_gfw_tree_cover_loss      -- Global Forest Watch tree-cover-loss annual tiles
  dh_gem_coal_plants           -- Global Energy Monitor Global Coal Plant Tracker
  dh_gem_coal_plant_units      -- Per-unit detail (MW, status, fuel, commissioning)
  dh_nature_spatial_overlaps   -- Precomputed overlap between assets and WDPA/GFW

Revision chain: 030 -> down_revision = '029_china_trade_platform'
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers
revision = '030_add_wdpa_gfw_gem_tables'
down_revision = '029_china_trade_platform'
branch_labels = None
depends_on = None


def upgrade():
    # -- 1. WDPA Protected Areas -------------------------------------------------
    op.create_table(
        'dh_wdpa_protected_areas',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('source_id', UUID(as_uuid=True), nullable=True),
        sa.Column('wdpa_id', sa.Integer, nullable=False, unique=True, comment='WDPA Site ID'),
        sa.Column('wdpa_pid', sa.Integer, nullable=True, comment='WDPA Parcel ID'),
        sa.Column('name', sa.Text, nullable=False),
        sa.Column('orig_name', sa.Text, nullable=True),
        sa.Column('country_iso3', sa.String(3), nullable=True),
        sa.Column('country_name', sa.Text, nullable=True),
        sa.Column('desig', sa.Text, nullable=True, comment='Designation (e.g. National Park)'),
        sa.Column('desig_type', sa.String(50), nullable=True, comment='National / International / Regional'),
        sa.Column('iucn_cat', sa.String(20), nullable=True, comment='IUCN Management Category (Ia-VI, NR)'),
        sa.Column('int_crit', sa.Text, nullable=True, comment='International criteria'),
        sa.Column('marine', sa.SmallInteger, nullable=True, comment='0=terrestrial, 1=coastal, 2=marine'),
        sa.Column('rep_area_km2', sa.Numeric(14, 4), nullable=True, comment='Reported area km2'),
        sa.Column('gis_area_km2', sa.Numeric(14, 4), nullable=True, comment='GIS-calculated area km2'),
        sa.Column('no_take_area_km2', sa.Numeric(14, 4), nullable=True),
        sa.Column('status', sa.String(30), nullable=True, comment='Designated / Proposed / Inscribed'),
        sa.Column('status_yr', sa.Integer, nullable=True),
        sa.Column('gov_type', sa.Text, nullable=True),
        sa.Column('own_type', sa.Text, nullable=True),
        sa.Column('mang_auth', sa.Text, nullable=True, comment='Management authority'),
        # Bounding box (lat/lng) -- not PostGIS, just centroid + bbox
        sa.Column('latitude', sa.Numeric(10, 6), nullable=True),
        sa.Column('longitude', sa.Numeric(10, 6), nullable=True),
        sa.Column('bbox_north', sa.Numeric(10, 6), nullable=True),
        sa.Column('bbox_south', sa.Numeric(10, 6), nullable=True),
        sa.Column('bbox_east', sa.Numeric(10, 6), nullable=True),
        sa.Column('bbox_west', sa.Numeric(10, 6), nullable=True),
        sa.Column('raw_record', JSONB, nullable=True),
        sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index('ix_wdpa_country', 'dh_wdpa_protected_areas', ['country_iso3'])
    op.create_index('ix_wdpa_iucn', 'dh_wdpa_protected_areas', ['iucn_cat'])
    op.create_index('ix_wdpa_status', 'dh_wdpa_protected_areas', ['status'])

    # -- 2. GFW Tree Cover Loss --------------------------------------------------
    op.create_table(
        'dh_gfw_tree_cover_loss',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('source_id', UUID(as_uuid=True), nullable=True),
        sa.Column('country_iso3', sa.String(3), nullable=False),
        sa.Column('country_name', sa.Text, nullable=True),
        sa.Column('subnational1', sa.Text, nullable=True),
        sa.Column('subnational2', sa.Text, nullable=True),
        sa.Column('year', sa.Integer, nullable=False),
        sa.Column('tree_cover_loss_ha', sa.Numeric(14, 2), nullable=True),
        sa.Column('tree_cover_loss_pct', sa.Numeric(8, 4), nullable=True),
        sa.Column('tree_cover_extent_ha', sa.Numeric(14, 2), nullable=True),
        sa.Column('primary_forest_loss_ha', sa.Numeric(14, 2), nullable=True),
        sa.Column('tree_cover_gain_ha', sa.Numeric(14, 2), nullable=True),
        sa.Column('biomass_loss_mt', sa.Numeric(14, 2), nullable=True, comment='CO2 equivalent megatonnes'),
        sa.Column('co2_emissions_mt', sa.Numeric(14, 2), nullable=True),
        sa.Column('driver_category', sa.Text, nullable=True, comment='Commodity / Forestry / Shifting ag / etc'),
        sa.Column('threshold_pct', sa.Integer, nullable=True, comment='Canopy density threshold (usually 30)'),
        sa.Column('raw_record', JSONB, nullable=True),
        sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index('ix_gfw_country_year', 'dh_gfw_tree_cover_loss', ['country_iso3', 'year'])

    # -- 3. GEM Global Coal Plant Tracker (plants) ------------------------------
    op.create_table(
        'dh_gem_coal_plants',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('source_id', UUID(as_uuid=True), nullable=True),
        sa.Column('gem_id', sa.Text, nullable=False, unique=True, comment='GEM wiki ID e.g. G1234'),
        sa.Column('plant_name', sa.Text, nullable=False),
        sa.Column('country', sa.Text, nullable=True),
        sa.Column('country_iso3', sa.String(3), nullable=True),
        sa.Column('subnational', sa.Text, nullable=True),
        sa.Column('owner', sa.Text, nullable=True),
        sa.Column('parent_company', sa.Text, nullable=True),
        sa.Column('latitude', sa.Numeric(10, 6), nullable=True),
        sa.Column('longitude', sa.Numeric(10, 6), nullable=True),
        sa.Column('status', sa.String(30), nullable=True, comment='Operating / Announced / Construction / etc'),
        sa.Column('capacity_mw', sa.Numeric(10, 2), nullable=True),
        sa.Column('num_units', sa.Integer, nullable=True),
        sa.Column('year_opened', sa.Integer, nullable=True),
        sa.Column('year_retired', sa.Integer, nullable=True),
        sa.Column('planned_retire_year', sa.Integer, nullable=True),
        sa.Column('coal_type', sa.Text, nullable=True, comment='Bituminous / Lignite / Sub-bituminous / etc'),
        sa.Column('combustion_technology', sa.Text, nullable=True, comment='Subcritical / Supercritical / IGCC'),
        sa.Column('air_pollution_control', sa.Text, nullable=True),
        sa.Column('carbon_capture', sa.String(5), nullable=True, comment='Yes / No'),
        sa.Column('captive', sa.String(5), nullable=True, comment='Yes / No'),
        sa.Column('heat_rate_btu_kwh', sa.Numeric(8, 1), nullable=True),
        sa.Column('emission_factor_tco2_mwh', sa.Numeric(8, 4), nullable=True),
        sa.Column('annual_co2_mt', sa.Numeric(10, 3), nullable=True, comment='Megatonnes CO2/yr'),
        sa.Column('raw_record', JSONB, nullable=True),
        sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index('ix_gem_coal_country', 'dh_gem_coal_plants', ['country_iso3'])
    op.create_index('ix_gem_coal_status', 'dh_gem_coal_plants', ['status'])
    op.create_index('ix_gem_coal_parent', 'dh_gem_coal_plants', ['parent_company'])

    # -- 4. GEM Coal Plant Units ------------------------------------------------
    op.create_table(
        'dh_gem_coal_plant_units',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('plant_id', UUID(as_uuid=True), sa.ForeignKey('dh_gem_coal_plants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('gem_unit_id', sa.Text, nullable=True, comment='GEM unit ID'),
        sa.Column('unit_name', sa.Text, nullable=True),
        sa.Column('capacity_mw', sa.Numeric(10, 2), nullable=True),
        sa.Column('status', sa.String(30), nullable=True),
        sa.Column('fuel_type', sa.Text, nullable=True),
        sa.Column('combustion_technology', sa.Text, nullable=True),
        sa.Column('year_commissioned', sa.Integer, nullable=True),
        sa.Column('year_retired', sa.Integer, nullable=True),
        sa.Column('planned_retire_year', sa.Integer, nullable=True),
        sa.Column('heat_rate_btu_kwh', sa.Numeric(8, 1), nullable=True),
        sa.Column('emission_factor_tco2_mwh', sa.Numeric(8, 4), nullable=True),
        sa.Column('annual_co2_mt', sa.Numeric(10, 3), nullable=True),
        sa.Column('raw_record', JSONB, nullable=True),
        sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index('ix_gem_units_plant', 'dh_gem_coal_plant_units', ['plant_id'])

    # -- 5. Precomputed nature spatial overlaps ---------------------------------
    op.create_table(
        'dh_nature_spatial_overlaps',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('asset_id', UUID(as_uuid=True), nullable=False, comment='Platform asset (spatial_asset_mapping.id)'),
        sa.Column('protected_area_id', UUID(as_uuid=True), nullable=True, comment='dh_wdpa_protected_areas.id'),
        sa.Column('wdpa_id', sa.Integer, nullable=True),
        sa.Column('protected_area_name', sa.Text, nullable=True),
        sa.Column('iucn_cat', sa.String(20), nullable=True),
        sa.Column('overlap_km2', sa.Numeric(14, 4), nullable=True),
        sa.Column('overlap_pct', sa.Numeric(8, 4), nullable=True),
        sa.Column('distance_km', sa.Numeric(10, 3), nullable=True, comment='Distance from asset centroid to PA boundary'),
        sa.Column('gfw_loss_ha', sa.Numeric(14, 2), nullable=True, comment='Cumulative tree cover loss within buffer'),
        sa.Column('gfw_loss_year_start', sa.Integer, nullable=True),
        sa.Column('gfw_loss_year_end', sa.Integer, nullable=True),
        sa.Column('calculation_method', sa.String(30), nullable=True, comment='bbox / haversine / postgis'),
        sa.Column('buffer_radius_km', sa.Numeric(8, 2), nullable=True),
        sa.Column('computed_at', sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index('ix_nat_overlap_asset', 'dh_nature_spatial_overlaps', ['asset_id'])
    op.create_index('ix_nat_overlap_wdpa', 'dh_nature_spatial_overlaps', ['wdpa_id'])

    # -- Register data sources (matches actual dh_data_sources schema) ----------
    op.execute("""
        INSERT INTO dh_data_sources (id, name, category, sub_category, description, access_type, base_url, sync_enabled, sync_schedule, status, priority, created_at, updated_at)
        VALUES
          ('wdpa-protected-areas', 'WDPA Protected Areas', 'nature', 'protected_areas', 'UNEP-WCMC World Database on Protected Areas', 'public_api', 'https://www.protectedplanet.net/en/thematic-areas/wdpa', true, '0 3 1 * *', 'active', 'P1', now(), now()),
          ('gfw-tree-cover-loss', 'GFW Tree Cover Loss', 'nature', 'deforestation', 'Global Forest Watch annual tree cover loss', 'public_api', 'https://www.globalforestwatch.org/dashboards/global/', true, '0 3 * * 0', 'active', 'P1', now(), now()),
          ('gem-coal-plant-tracker', 'GEM Coal Plant Tracker', 'energy', 'coal', 'Global Energy Monitor Global Coal Plant Tracker', 'csv_download', 'https://globalenergymonitor.org/projects/global-coal-plant-tracker/', true, '0 2 1 * *', 'active', 'P1', now(), now())
        ON CONFLICT (id) DO NOTHING;
    """)


def downgrade():
    op.drop_table('dh_nature_spatial_overlaps')
    op.drop_table('dh_gem_coal_plant_units')
    op.drop_table('dh_gem_coal_plants')
    op.drop_table('dh_gfw_tree_cover_loss')
    op.drop_table('dh_wdpa_protected_areas')
    op.execute("DELETE FROM dh_data_sources WHERE id IN ('wdpa-protected-areas','gfw-tree-cover-loss','gem-coal-plant-tracker');")
