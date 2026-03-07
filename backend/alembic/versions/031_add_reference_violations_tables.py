"""
Migration 031 -- IRENA LCOE Benchmarks, CRREM Pathways, Grid Emission Factors, Violation Tracker

Tables (4):
  dh_irena_lcoe              -- IRENA levelized cost of electricity by technology/year/region
  dh_crrem_pathways          -- CRREM decarbonization pathways (1.5C / 2C) by property type
  dh_grid_emission_factors   -- Country-level grid emission factors (kgCO2/kWh) by year
  dh_violation_tracker       -- Corporate violations/penalties from Good Jobs First et al.

Revision chain: 031 -> down_revision = '030_add_wdpa_gfw_gem_tables'
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers
revision = '031_add_reference_violations_tables'
down_revision = '030_add_wdpa_gfw_gem_tables'
branch_labels = None
depends_on = None


def upgrade():
    # -- 1. IRENA Levelized Cost of Electricity ---------------------------------
    op.create_table(
        'dh_irena_lcoe',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('source_id', sa.String(100), nullable=True),
        sa.Column('technology', sa.Text, nullable=False, comment='Solar PV / Onshore Wind / Offshore Wind / CSP / Hydro / Bioenergy / Geothermal'),
        sa.Column('sub_technology', sa.Text, nullable=True, comment='Utility-scale / Rooftop / Fixed-tilt / Tracking etc'),
        sa.Column('year', sa.Integer, nullable=False),
        sa.Column('country_iso3', sa.String(3), nullable=True, comment='NULL = global average'),
        sa.Column('region', sa.Text, nullable=True, comment='IRENA region grouping'),
        sa.Column('lcoe_usd_mwh', sa.Numeric(10, 2), nullable=True, comment='Weighted average LCOE USD/MWh'),
        sa.Column('lcoe_min_usd_mwh', sa.Numeric(10, 2), nullable=True),
        sa.Column('lcoe_max_usd_mwh', sa.Numeric(10, 2), nullable=True),
        sa.Column('capacity_factor_pct', sa.Numeric(6, 2), nullable=True),
        sa.Column('installed_cost_usd_kw', sa.Numeric(10, 2), nullable=True, comment='Total installed cost USD/kW'),
        sa.Column('capex_usd_kw', sa.Numeric(10, 2), nullable=True),
        sa.Column('opex_usd_kw_yr', sa.Numeric(10, 2), nullable=True, comment='Annual O&M USD/kW/yr'),
        sa.Column('wacc_pct', sa.Numeric(6, 2), nullable=True, comment='Assumed WACC'),
        sa.Column('plant_life_years', sa.Integer, nullable=True),
        sa.Column('newly_installed_gw', sa.Numeric(10, 3), nullable=True, comment='Capacity added that year'),
        sa.Column('cumulative_installed_gw', sa.Numeric(12, 3), nullable=True),
        sa.Column('raw_record', JSONB, nullable=True),
        sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index('ix_irena_tech_year', 'dh_irena_lcoe', ['technology', 'year'])
    op.create_index('ix_irena_country', 'dh_irena_lcoe', ['country_iso3'])

    # -- 2. CRREM Decarbonization Pathways --------------------------------------
    op.create_table(
        'dh_crrem_pathways',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('source_id', sa.String(100), nullable=True),
        sa.Column('property_type', sa.Text, nullable=False, comment='Office / Retail / Industrial / Multifamily / Hotel / Logistics / Healthcare'),
        sa.Column('country_iso3', sa.String(3), nullable=True, comment='NULL = global'),
        sa.Column('region', sa.Text, nullable=True),
        sa.Column('scenario', sa.String(20), nullable=False, comment='1.5C / 2C / 2.5C / 3C'),
        sa.Column('year', sa.Integer, nullable=False),
        sa.Column('energy_intensity_kwh_m2', sa.Numeric(10, 2), nullable=True, comment='Target kWh/m2/yr'),
        sa.Column('carbon_intensity_kgco2_m2', sa.Numeric(10, 4), nullable=True, comment='Target kgCO2/m2/yr'),
        sa.Column('grid_factor_kgco2_kwh', sa.Numeric(8, 6), nullable=True, comment='Assumed grid factor for pathway'),
        sa.Column('cumulative_reduction_pct', sa.Numeric(6, 2), nullable=True, comment='% reduction from baseline'),
        sa.Column('stranding_risk', sa.String(20), nullable=True, comment='Low / Medium / High / Stranded'),
        sa.Column('retrofit_cost_usd_m2', sa.Numeric(10, 2), nullable=True, comment='Estimated retrofit cost'),
        sa.Column('raw_record', JSONB, nullable=True),
        sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index('ix_crrem_type_scenario', 'dh_crrem_pathways', ['property_type', 'scenario'])
    op.create_index('ix_crrem_country_year', 'dh_crrem_pathways', ['country_iso3', 'year'])

    # -- 3. Grid Emission Factors -----------------------------------------------
    op.create_table(
        'dh_grid_emission_factors',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('source_id', sa.String(100), nullable=True),
        sa.Column('country_iso3', sa.String(3), nullable=False),
        sa.Column('country_name', sa.Text, nullable=True),
        sa.Column('year', sa.Integer, nullable=False),
        sa.Column('grid_ef_kgco2_kwh', sa.Numeric(8, 6), nullable=False, comment='Grid emission factor kgCO2/kWh'),
        sa.Column('grid_ef_tco2_mwh', sa.Numeric(8, 6), nullable=True, comment='Same in tCO2/MWh'),
        sa.Column('generation_mix_coal_pct', sa.Numeric(6, 2), nullable=True),
        sa.Column('generation_mix_gas_pct', sa.Numeric(6, 2), nullable=True),
        sa.Column('generation_mix_nuclear_pct', sa.Numeric(6, 2), nullable=True),
        sa.Column('generation_mix_hydro_pct', sa.Numeric(6, 2), nullable=True),
        sa.Column('generation_mix_wind_pct', sa.Numeric(6, 2), nullable=True),
        sa.Column('generation_mix_solar_pct', sa.Numeric(6, 2), nullable=True),
        sa.Column('generation_mix_other_re_pct', sa.Numeric(6, 2), nullable=True),
        sa.Column('generation_mix_other_pct', sa.Numeric(6, 2), nullable=True),
        sa.Column('total_generation_twh', sa.Numeric(12, 3), nullable=True),
        sa.Column('data_source_org', sa.Text, nullable=True, comment='IEA / UNFCCC / Ember / OWID'),
        sa.Column('raw_record', JSONB, nullable=True),
        sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index('ix_grid_ef_country_year', 'dh_grid_emission_factors', ['country_iso3', 'year'], unique=True)

    # -- 4. Violation Tracker ---------------------------------------------------
    op.create_table(
        'dh_violation_tracker',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('source_id', sa.String(100), nullable=True),
        sa.Column('company_name', sa.Text, nullable=False),
        sa.Column('parent_company', sa.Text, nullable=True),
        sa.Column('lei', sa.String(20), nullable=True, comment='Legal Entity Identifier if available'),
        sa.Column('country_iso3', sa.String(3), nullable=True),
        sa.Column('state_province', sa.Text, nullable=True),
        sa.Column('sector', sa.Text, nullable=True, comment='Industry sector'),
        sa.Column('sub_sector', sa.Text, nullable=True),
        sa.Column('violation_type', sa.Text, nullable=False, comment='Environmental / Labor / Safety / Financial / Antitrust / Consumer'),
        sa.Column('sub_type', sa.Text, nullable=True, comment='Detailed category'),
        sa.Column('agency', sa.Text, nullable=True, comment='Regulatory agency (EPA / OSHA / SEC / DOJ / FCA / etc)'),
        sa.Column('violation_date', sa.Date, nullable=True),
        sa.Column('resolution_date', sa.Date, nullable=True),
        sa.Column('penalty_amount_usd', sa.Numeric(16, 2), nullable=True),
        sa.Column('penalty_currency', sa.String(3), nullable=True, comment='Original currency'),
        sa.Column('penalty_original', sa.Numeric(16, 2), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('case_id', sa.Text, nullable=True, comment='External case/docket ID'),
        sa.Column('source_url', sa.Text, nullable=True),
        sa.Column('severity', sa.String(20), nullable=True, comment='Low / Medium / High / Critical'),
        sa.Column('status', sa.String(30), nullable=True, comment='Pending / Settled / Adjudicated / Appealed'),
        sa.Column('repeat_offender', sa.Boolean, nullable=True),
        sa.Column('raw_record', JSONB, nullable=True),
        sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index('ix_viol_company', 'dh_violation_tracker', ['company_name'])
    op.create_index('ix_viol_parent', 'dh_violation_tracker', ['parent_company'])
    op.create_index('ix_viol_type', 'dh_violation_tracker', ['violation_type'])
    op.create_index('ix_viol_country', 'dh_violation_tracker', ['country_iso3'])
    op.create_index('ix_viol_date', 'dh_violation_tracker', ['violation_date'])
    op.create_index('ix_viol_agency', 'dh_violation_tracker', ['agency'])

    # -- Register data sources ---------------------------------------------------
    op.execute("""
        INSERT INTO dh_data_sources (id, name, category, sub_category, description, access_type, base_url, sync_enabled, sync_schedule, status, priority, created_at, updated_at)
        VALUES
          ('irena-lcoe-benchmarks', 'IRENA LCOE Benchmarks', 'reference', 'cost_benchmarks', 'IRENA Renewable Power Generation Costs — LCOE by technology, year, region', 'csv_download', 'https://www.irena.org/costs/Power-Generation-Costs', true, '0 3 1 1 *', 'active', 'P1', now(), now()),
          ('crrem-decarbonization-pathways', 'CRREM Decarbonization Pathways', 'reference', 'real_estate', 'CRREM v2.0 energy/carbon intensity pathways for commercial RE types', 'csv_download', 'https://www.crrem.eu/pathways/', true, '0 3 1 1 *', 'active', 'P1', now(), now()),
          ('grid-emission-factors', 'Grid Emission Factors', 'reference', 'emission_factors', 'Country-level grid emission factors from IEA/Ember/OWID', 'public_api', 'https://ember-climate.org/data/', true, '0 3 1 * *', 'active', 'P1', now(), now()),
          ('violation-tracker', 'Violation Tracker', 'governance', 'violations', 'Corporate penalties and violations from Good Jobs First Violation Tracker', 'scrape', 'https://violationtracker.goodjobsfirst.org/', true, '0 4 * * 0', 'active', 'P2', now(), now())
        ON CONFLICT (id) DO NOTHING;
    """)


def downgrade():
    op.drop_table('dh_violation_tracker')
    op.drop_table('dh_grid_emission_factors')
    op.drop_table('dh_crrem_pathways')
    op.drop_table('dh_irena_lcoe')
    op.execute("DELETE FROM dh_data_sources WHERE id IN ('irena-lcoe-benchmarks','crrem-decarbonization-pathways','grid-emission-factors','violation-tracker');")
