"""Add stranded asset tables (Standard PostgreSQL)

Revision ID: 002_add_stranded_asset_tables
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
    # 1. FossilFuelReserve
    op.create_table(
        'fossil_fuel_reserve',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('counterparty_id', UUID(as_uuid=True), nullable=True),
        sa.Column('asset_name', sa.String(255), nullable=False),
        sa.Column('asset_location', sa.String(100)),
        sa.Column('country_code', sa.String(2)),
        sa.Column('reserve_type', sa.String(50), nullable=False),  # oil, gas, coal
        sa.Column('reserve_category', sa.String(50), nullable=False),  # 1P, 2P, 3P
        sa.Column('proven_reserves_mmBOE', sa.Numeric(15, 4)),
        sa.Column('breakeven_price_USD', sa.Numeric(10, 2)),
        sa.Column('lifting_cost_USD', sa.Numeric(10, 2)),
        sa.Column('carbon_intensity_kgCO2_per_unit', sa.Numeric(10, 4)),
        sa.Column('production_start_year', sa.Integer),
        sa.Column('expected_depletion_year', sa.Integer),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_fossil_reserve_counterparty', 'fossil_fuel_reserve', ['counterparty_id'])
    op.create_index('idx_fossil_reserve_type', 'fossil_fuel_reserve', ['reserve_type'])
    op.create_index('idx_fossil_reserve_country', 'fossil_fuel_reserve', ['country_code'])
    op.create_index('idx_fossil_reserve_breakeven', 'fossil_fuel_reserve', ['breakeven_price_USD'])

    # 2. PowerPlant
    op.create_table(
        'power_plant',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('counterparty_id', UUID(as_uuid=True), nullable=True),
        sa.Column('plant_name', sa.String(255), nullable=False),
        sa.Column('plant_location', sa.String(100)),
        sa.Column('country_code', sa.String(2)),
        sa.Column('technology_type', sa.String(50), nullable=False),  # coal, gas_ccgt, gas_ocgt, oil
        sa.Column('capacity_mw', sa.Numeric(10, 2), nullable=False),
        sa.Column('commissioning_year', sa.Integer),
        sa.Column('original_retirement_year', sa.Integer),
        sa.Column('capacity_factor_baseline', sa.Numeric(5, 4)),
        sa.Column('co2_intensity_tco2_mwh', sa.Numeric(8, 4)),
        sa.Column('fixed_om_cost_usd_kw_year', sa.Numeric(10, 2)),
        sa.Column('fuel_cost_usd_mmbtu', sa.Numeric(8, 4)),
        sa.Column('offtake_type', sa.String(50)),  # merchant, ppa, regulated
        sa.Column('ppa_expiry_year', sa.Integer),
        sa.Column('repurposing_option', sa.String(100)),  # hydrogen, battery_storage, ccs, demolition
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_power_plant_counterparty', 'power_plant', ['counterparty_id'])
    op.create_index('idx_power_plant_technology', 'power_plant', ['technology_type'])
    op.create_index('idx_power_plant_country', 'power_plant', ['country_code'])
    op.create_index('idx_power_plant_retirement', 'power_plant', ['original_retirement_year'])

    # 3. InfrastructureAsset
    op.create_table(
        'infrastructure_asset',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('counterparty_id', UUID(as_uuid=True), nullable=True),
        sa.Column('asset_name', sa.String(255), nullable=False),
        sa.Column('asset_type', sa.String(50), nullable=False),  # pipeline, lng_terminal, refinery, coal_terminal
        sa.Column('asset_location', sa.String(100)),
        sa.Column('country_code', sa.String(2)),
        sa.Column('design_capacity', sa.String(100)),
        sa.Column('utilization_rate_percent', sa.Numeric(5, 2)),
        sa.Column('commissioning_year', sa.Integer),
        sa.Column('expected_retirement_year', sa.Integer),
        sa.Column('contract_maturity_profile', JSONB, server_default='{}'),
        sa.Column('take_or_pay_exposure_usd', sa.Numeric(15, 2)),
        sa.Column('hydrogen_ready', sa.Boolean, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_infra_counterparty', 'infrastructure_asset', ['counterparty_id'])
    op.create_index('idx_infra_type', 'infrastructure_asset', ['asset_type'])
    op.create_index('idx_infra_country', 'infrastructure_asset', ['country_code'])
    op.create_index('idx_infra_retirement', 'infrastructure_asset', ['expected_retirement_year'])

    # 4. StrandedAssetCalculation
    op.create_table(
        'stranded_asset_calculation',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('asset_type', sa.String(50), nullable=False),  # fossil_fuel_reserve, power_plant, infrastructure
        sa.Column('asset_id', UUID(as_uuid=True), nullable=False),
        sa.Column('counterparty_id', UUID(as_uuid=True), nullable=True),
        sa.Column('scenario_id', UUID(as_uuid=True), nullable=True),
        sa.Column('target_year', sa.Integer, nullable=False),
        sa.Column('stranded_volume_percent', sa.Numeric(5, 2)),
        sa.Column('stranded_value_usd', sa.Numeric(15, 2)),
        sa.Column('baseline_npv_usd', sa.Numeric(15, 2)),
        sa.Column('scenario_npv_usd', sa.Numeric(15, 2)),
        sa.Column('npv_impact_percent', sa.Numeric(5, 2)),
        sa.Column('carbon_price_usd_tco2', sa.Numeric(8, 2)),
        sa.Column('optimal_retirement_year', sa.Integer),
        sa.Column('stranding_risk_score', sa.Numeric(3, 2)),  # 0.00-1.00
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('asset_type', 'asset_id', 'scenario_id', 'target_year', name='uq_stranded_calc'),
    )
    op.create_index('idx_stranded_calc_asset', 'stranded_asset_calculation', ['asset_type', 'asset_id'])
    op.create_index('idx_stranded_calc_scenario', 'stranded_asset_calculation', ['scenario_id'])
    op.create_index('idx_stranded_calc_year', 'stranded_asset_calculation', ['target_year'])
    op.create_index('idx_stranded_calc_counterparty', 'stranded_asset_calculation', ['counterparty_id'])
    op.create_index('idx_stranded_calc_risk', 'stranded_asset_calculation', ['stranding_risk_score'])

    # 5. TechnologyDisruptionMetric (Standard PostgreSQL with optimized indexes — NO TimescaleDB)
    op.create_table(
        'technology_disruption_metric',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('metric_date', sa.Date, nullable=False),
        sa.Column('metric_type', sa.String(50), nullable=False),  # solar_lcoe, wind_lcoe, battery_cost, ev_share, coal_utilization
        sa.Column('region', sa.String(50), server_default='global'),
        sa.Column('country_code', sa.String(2)),
        sa.Column('value', sa.Numeric(15, 4)),
        sa.Column('value_unit', sa.String(20)),
        sa.Column('scenario_name', sa.String(50)),
        sa.Column('data_source', sa.String(100)),
        sa.Column('is_projection', sa.Boolean, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    # Optimized indexes for time-series queries (replacing TimescaleDB hypertable)
    op.create_index('idx_tech_metric_date_type', 'technology_disruption_metric', ['metric_date', 'metric_type'])
    op.create_index('idx_tech_metric_date_scenario', 'technology_disruption_metric', ['metric_date', 'scenario_name'])
    op.create_index('idx_tech_metric_date_range', 'technology_disruption_metric', [sa.text('metric_date DESC')])
    op.create_index('idx_tech_metric_region', 'technology_disruption_metric', ['region', 'metric_type'])
    op.create_index('idx_tech_metric_unique', 'technology_disruption_metric',
                    ['metric_date', 'metric_type', 'region', 'scenario_name'], unique=True)

    # 6. EnergyTransitionPathway
    op.create_table(
        'energy_transition_pathway',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('pathway_name', sa.String(100), nullable=False),
        sa.Column('sector', sa.String(50), nullable=False),  # power, oil_gas, coal, transport, industry
        sa.Column('region', sa.String(50), nullable=False),
        sa.Column('scenario_id', UUID(as_uuid=True), nullable=True),
        sa.Column('base_year', sa.Integer, nullable=False),
        sa.Column('target_year', sa.Integer, nullable=False),
        sa.Column('demand_trajectory', JSONB, server_default='{}'),  # {year: demand_value}
        sa.Column('price_trajectory', JSONB, server_default='{}'),  # {year: price_value}
        sa.Column('peak_demand_year', sa.Integer),
        sa.Column('net_zero_year', sa.Integer),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_pathway_sector', 'energy_transition_pathway', ['sector'])
    op.create_index('idx_pathway_region', 'energy_transition_pathway', ['region'])
    op.create_index('idx_pathway_scenario', 'energy_transition_pathway', ['scenario_id'])
    op.create_index('idx_pathway_sector_region', 'energy_transition_pathway', ['sector', 'region'])


def downgrade():
    op.drop_table('energy_transition_pathway')
    op.drop_table('technology_disruption_metric')
    op.drop_table('stranded_asset_calculation')
    op.drop_table('infrastructure_asset')
    op.drop_table('power_plant')
    op.drop_table('fossil_fuel_reserve')
