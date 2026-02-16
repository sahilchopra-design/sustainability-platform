"""Add Stranded Asset tables

Revision ID: 002
Revises: 001_add_cbam_tables
Create Date: 2025-01-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '002_add_stranded_asset_tables'
down_revision = '001_add_cbam_tables'
branch_labels = None
depends_on = None


def upgrade():
    # 1. FossilFuelReserve - Oil, gas, coal reserves
    op.create_table(
        'fossil_fuel_reserve',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('counterparty_id', UUID(as_uuid=True), sa.ForeignKey('counterparty.id'), nullable=False),
        sa.Column('asset_name', sa.String(255), nullable=False),
        sa.Column('asset_location', sa.String(100)),
        sa.Column('latitude', sa.Numeric(10, 6)),
        sa.Column('longitude', sa.Numeric(10, 6)),
        sa.Column('reserve_type', sa.String(50), nullable=False),  # oil, gas, coal
        sa.Column('reserve_category', sa.String(50)),  # 1P, 2P, 3P
        sa.Column('proven_reserves_mmBOE', sa.Numeric(15, 4)),
        sa.Column('probable_reserves_mmBOE', sa.Numeric(15, 4)),
        sa.Column('possible_reserves_mmBOE', sa.Numeric(15, 4)),
        sa.Column('breakeven_price_USD', sa.Numeric(10, 2)),
        sa.Column('lifting_cost_USD', sa.Numeric(10, 2)),
        sa.Column('remaining_capex_USD', sa.Numeric(15, 2)),
        sa.Column('carbon_intensity_kgCO2_per_unit', sa.Numeric(10, 4)),
        sa.Column('methane_leakage_rate', sa.Numeric(5, 4)),
        sa.Column('production_start_year', sa.Integer),
        sa.Column('expected_depletion_year', sa.Integer),
        sa.Column('license_expiry_year', sa.Integer),
        sa.Column('is_operating', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    op.create_index('idx_reserve_counterparty', 'fossil_fuel_reserve', ['counterparty_id'])
    op.create_index('idx_reserve_type', 'fossil_fuel_reserve', ['reserve_type'])
    op.create_index('idx_reserve_location', 'fossil_fuel_reserve', ['latitude', 'longitude'])

    # 2. PowerPlant - Generation assets
    op.create_table(
        'power_plant',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('counterparty_id', UUID(as_uuid=True), sa.ForeignKey('counterparty.id'), nullable=False),
        sa.Column('plant_name', sa.String(255), nullable=False),
        sa.Column('plant_location', sa.String(100)),
        sa.Column('latitude', sa.Numeric(10, 6)),
        sa.Column('longitude', sa.Numeric(10, 6)),
        sa.Column('country_code', sa.String(2)),
        sa.Column('technology_type', sa.String(50), nullable=False),  # coal, gas_ccgt, gas_ocgt, nuclear, wind, solar, etc.
        sa.Column('capacity_mw', sa.Numeric(10, 2), nullable=False),
        sa.Column('commissioning_year', sa.Integer),
        sa.Column('original_retirement_year', sa.Integer),
        sa.Column('technical_lifetime_years', sa.Integer),
        sa.Column('capacity_factor_baseline', sa.Numeric(5, 4)),
        sa.Column('capacity_factor_current', sa.Numeric(5, 4)),
        sa.Column('heat_rate_btu_kwh', sa.Numeric(10, 2)),
        sa.Column('efficiency_percent', sa.Numeric(5, 2)),
        sa.Column('co2_intensity_tco2_mwh', sa.Numeric(8, 4)),
        sa.Column('nox_emissions_kg_mwh', sa.Numeric(8, 4)),
        sa.Column('so2_emissions_kg_mwh', sa.Numeric(8, 4)),
        sa.Column('has_ccs', sa.Boolean, default=False),
        sa.Column('ccs_capacity_mtpa', sa.Numeric(8, 4)),
        sa.Column('fixed_om_cost_usd_kw_year', sa.Numeric(10, 2)),
        sa.Column('variable_om_cost_usd_mwh', sa.Numeric(8, 2)),
        sa.Column('fuel_cost_usd_mmbtu', sa.Numeric(8, 4)),
        sa.Column('fuel_type', sa.String(50)),
        sa.Column('offtake_type', sa.String(50)),  # merchant, ppa, regulated
        sa.Column('ppa_expiry_year', sa.Integer),
        sa.Column('ppa_price_usd_mwh', sa.Numeric(8, 2)),
        sa.Column('grid_region', sa.String(100)),
        sa.Column('grid_carbon_intensity', sa.Numeric(8, 4)),
        sa.Column('repurposing_option', sa.String(100)),  # ccs, hydrogen, storage, retirement
        sa.Column('repurposing_cost_usd_mw', sa.Numeric(12, 2)),
        sa.Column('is_operating', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    op.create_index('idx_plant_counterparty', 'power_plant', ['counterparty_id'])
    op.create_index('idx_plant_technology', 'power_plant', ['technology_type'])
    op.create_index('idx_plant_location', 'power_plant', ['latitude', 'longitude'])
    op.create_index('idx_plant_capacity', 'power_plant', ['capacity_mw'])

    # 3. InfrastructureAsset - Pipelines, LNG terminals, refineries
    op.create_table(
        'infrastructure_asset',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('counterparty_id', UUID(as_uuid=True), sa.ForeignKey('counterparty.id'), nullable=False),
        sa.Column('asset_name', sa.String(255), nullable=False),
        sa.Column('asset_type', sa.String(50), nullable=False),  # pipeline_oil, pipeline_gas, lng_terminal, refinery, etc.
        sa.Column('asset_location', sa.String(100)),
        sa.Column('latitude', sa.Numeric(10, 6)),
        sa.Column('longitude', sa.Numeric(10, 6)),
        sa.Column('country_code', sa.String(2)),
        sa.Column('design_capacity', sa.String(100)),
        sa.Column('design_capacity_unit', sa.String(20)),
        sa.Column('current_capacity_utilized', sa.String(100)),
        sa.Column('utilization_rate_percent', sa.Numeric(5, 2)),
        sa.Column('commissioning_year', sa.Integer),
        sa.Column('expected_retirement_year', sa.Integer),
        sa.Column('remaining_book_value_usd', sa.Numeric(15, 2)),
        sa.Column('replacement_cost_usd', sa.Numeric(15, 2)),
        sa.Column('contract_maturity_profile', JSONB),  # {2025: 100000, 2026: 80000, ...}
        sa.Column('take_or_pay_exposure_usd', sa.Numeric(15, 2)),
        sa.Column('contracted_volume_percent', sa.Numeric(5, 2)),
        sa.Column('hydrogen_ready', sa.Boolean, default=False),
        sa.Column('ammonia_ready', sa.Boolean, default=False),
        sa.Column('ccs_compatible', sa.Boolean, default=False),
        sa.Column('regulatory_status', sa.String(50)),
        sa.Column('environmental_permits', JSONB),
        sa.Column('is_operating', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    op.create_index('idx_infra_counterparty', 'infrastructure_asset', ['counterparty_id'])
    op.create_index('idx_infra_type', 'infrastructure_asset', ['asset_type'])

    # 4. StrandedAssetCalculation - Calculation results
    op.create_table(
        'stranded_asset_calculation',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('asset_type', sa.String(50), nullable=False),  # reserve, power_plant, infrastructure
        sa.Column('asset_id', UUID(as_uuid=True), nullable=False),
        sa.Column('scenario_id', UUID(as_uuid=True), sa.ForeignKey('scenario.id')),
        sa.Column('target_year', sa.Integer, nullable=False),
        sa.Column('calculation_date', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('stranded_volume_percent', sa.Numeric(5, 2)),
        sa.Column('stranded_volume_unit', sa.String(20)),
        sa.Column('stranded_value_usd', sa.Numeric(15, 2)),
        sa.Column('baseline_npv_usd', sa.Numeric(15, 2)),
        sa.Column('scenario_npv_usd', sa.Numeric(15, 2)),
        sa.Column('npv_impact_percent', sa.Numeric(5, 2)),
        sa.Column('carbon_price_usd_tco2', sa.Numeric(8, 2)),
        sa.Column('commodity_price_usd', sa.Numeric(10, 2)),
        sa.Column('demand_reduction_percent', sa.Numeric(5, 2)),
        sa.Column('optimal_retirement_year', sa.Integer),
        sa.Column('early_retirement_value_usd', sa.Numeric(15, 2)),
        sa.Column('stranding_risk_score', sa.Numeric(3, 2)),
        sa.Column('risk_category', sa.String(50)),
        sa.Column('key_assumptions', JSONB),
        sa.Column('sensitivity_analysis', JSONB),
        sa.UniqueConstraint('asset_type', 'asset_id', 'scenario_id', 'target_year')
    )
    op.create_index('idx_calc_asset', 'stranded_asset_calculation', ['asset_type', 'asset_id'])
    op.create_index('idx_calc_scenario', 'stranded_asset_calculation', ['scenario_id', 'target_year'])
    op.create_index('idx_calc_risk_score', 'stranded_asset_calculation', ['stranding_risk_score'])

    # 5. TechnologyDisruptionMetric (TimescaleDB) - EVs, heat pumps, hydrogen
    op.create_table(
        'technology_disruption_metric',
        sa.Column('id', UUID(as_uuid=True)),
        sa.Column('time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metric_type', sa.String(50), nullable=False),
        # ev_sales_share, ev_stock_share, ev_oil_displacement_kbpd,
        # heat_pump_sales, heat_pump_gas_displacement_bcm,
        # green_hydrogen_capacity_mw, green_hydrogen_cost_usd_kg,
        # ccs_capacity_mtpa, battery_storage_gwh
        sa.Column('region', sa.String(50)),
        sa.Column('country_code', sa.String(2)),
        sa.Column('value', sa.Numeric(15, 4)),
        sa.Column('unit', sa.String(20)),
        sa.Column('scenario_name', sa.String(50)),  # IEA_NZE, IEA_STEPS, IEA_APS, NGFS_Orderly
        sa.Column('data_source', sa.String(100)),  # IEA, BloombergNEF, IRENA
        sa.Column('data_quality', sa.String(20)),
        sa.Column('is_projection', sa.Boolean, default=False)
    )
    # Note: Run manually: SELECT create_hypertable('technology_disruption_metric', 'time', chunk_time_interval => INTERVAL '1 year');
    op.create_index('idx_tech_metric_type', 'technology_disruption_metric', ['metric_type', 'time'])
    op.create_index('idx_tech_region', 'technology_disruption_metric', ['region', 'metric_type'])

    # 6. EnergyTransitionPathway - Sector trajectories
    op.create_table(
        'energy_transition_pathway',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('pathway_name', sa.String(100), nullable=False),
        sa.Column('sector', sa.String(50), nullable=False),  # oil, gas, coal, power
        sa.Column('region', sa.String(50)),
        sa.Column('country_code', sa.String(2)),
        sa.Column('scenario_id', UUID(as_uuid=True), sa.ForeignKey('scenario.id')),
        sa.Column('base_year', sa.Integer, nullable=False),
        sa.Column('target_year', sa.Integer, nullable=False),
        sa.Column('demand_trajectory', JSONB),  # {2025: 100, 2030: 85, ...}
        sa.Column('price_trajectory', JSONB),
        sa.Column('capacity_trajectory', JSONB),
        sa.Column('peak_demand_year', sa.Integer),
        sa.Column('net_zero_year', sa.Integer),
        sa.Column('carbon_price_trajectory', JSONB),
        sa.Column('policy_assumptions', JSONB),
        sa.Column('technology_assumptions', JSONB),
        sa.Column('source_document', sa.String(255)),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    op.create_index('idx_pathway_sector', 'energy_transition_pathway', ['sector', 'region'])
    op.create_index('idx_pathway_scenario', 'energy_transition_pathway', ['scenario_id'])


def downgrade():
    op.drop_table('energy_transition_pathway')
    op.drop_table('technology_disruption_metric')
    op.drop_table('stranded_asset_calculation')
    op.drop_table('infrastructure_asset')
    op.drop_table('power_plant')
    op.drop_table('fossil_fuel_reserve')
