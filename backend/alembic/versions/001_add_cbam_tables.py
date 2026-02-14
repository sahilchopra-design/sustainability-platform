"""Add CBAM tables (Standard PostgreSQL)

Revision ID: 001_add_cbam_tables
Revises: 133e9046d191
Create Date: 2025-01-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '001_add_cbam_tables'
down_revision = '133e9046d191'
branch_labels = None
depends_on = None


def upgrade():
    # 1. cbam_product_category
    op.create_table(
        'cbam_product_category',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('cn_code', sa.String(8), nullable=False, unique=True),
        sa.Column('hs_code', sa.String(6), nullable=False),
        sa.Column('sector', sa.String(50), nullable=False),
        sa.Column('product_name', sa.String(255), nullable=False),
        sa.Column('default_direct_emissions', sa.Numeric(10, 4)),
        sa.Column('default_indirect_emissions', sa.Numeric(10, 4)),
        sa.Column('default_total_emissions', sa.Numeric(10, 4)),
        sa.Column('is_active', sa.Boolean, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_cbam_product_sector', 'cbam_product_category', ['sector'])
    op.create_index('idx_cbam_product_cn_code', 'cbam_product_category', ['cn_code'])

    # 2. cbam_supplier
    op.create_table(
        'cbam_supplier',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('counterparty_id', UUID(as_uuid=True), nullable=True),
        sa.Column('supplier_name', sa.String(255), nullable=False),
        sa.Column('country_code', sa.String(2), nullable=False),
        sa.Column('verification_status', sa.String(50), server_default='unverified'),
        sa.Column('has_domestic_carbon_price', sa.Boolean, server_default=sa.false()),
        sa.Column('domestic_carbon_price', sa.Numeric(10, 2)),
        sa.Column('risk_score', sa.Numeric(3, 2)),
        sa.Column('risk_category', sa.String(50)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_cbam_supplier_country', 'cbam_supplier', ['country_code'])
    op.create_index('idx_cbam_supplier_counterparty', 'cbam_supplier', ['counterparty_id'])
    op.create_index('idx_cbam_supplier_risk', 'cbam_supplier', ['risk_category', 'country_code'])

    # 3. cbam_embedded_emissions
    op.create_table(
        'cbam_embedded_emissions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('supplier_id', UUID(as_uuid=True), sa.ForeignKey('cbam_supplier.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_category_id', UUID(as_uuid=True), sa.ForeignKey('cbam_product_category.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reporting_year', sa.Integer, nullable=False),
        sa.Column('reporting_quarter', sa.Integer),
        sa.Column('import_volume_tonnes', sa.Numeric(15, 2)),
        sa.Column('direct_attributed_emissions', sa.Numeric(12, 4)),
        sa.Column('indirect_attributed_emissions', sa.Numeric(12, 4)),
        sa.Column('specific_direct_emissions', sa.Numeric(10, 6)),
        sa.Column('specific_indirect_emissions', sa.Numeric(10, 6)),
        sa.Column('specific_total_emissions', sa.Numeric(10, 6)),
        sa.Column('is_verified', sa.Boolean, server_default=sa.false()),
        sa.Column('uses_default_values', sa.Boolean, server_default=sa.false()),
        sa.UniqueConstraint('supplier_id', 'product_category_id', 'reporting_year', 'reporting_quarter', name='uq_cbam_emissions_period'),
    )
    op.create_index('idx_cbam_emissions_supplier', 'cbam_embedded_emissions', ['supplier_id'])
    op.create_index('idx_cbam_emissions_period', 'cbam_embedded_emissions', ['reporting_year', 'reporting_quarter'])
    op.create_index('idx_cbam_emissions_product', 'cbam_embedded_emissions', ['product_category_id'])

    # 4. cbam_cost_projection (Standard PostgreSQL with optimized indexes — NO TimescaleDB)
    op.create_table(
        'cbam_cost_projection',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('portfolio_id', UUID(as_uuid=True), nullable=True),
        sa.Column('holding_id', UUID(as_uuid=True), nullable=True),
        sa.Column('counterparty_id', UUID(as_uuid=True), nullable=True),
        sa.Column('projection_date', sa.Date, nullable=False),
        sa.Column('scenario_id', UUID(as_uuid=True), nullable=True),
        sa.Column('import_volume_tonnes', sa.Numeric(15, 2)),
        sa.Column('embedded_emissions_tco2', sa.Numeric(15, 4)),
        sa.Column('eu_ets_price_eur', sa.Numeric(10, 2)),
        sa.Column('domestic_carbon_price_eur', sa.Numeric(10, 2), server_default='0'),
        sa.Column('net_cbam_cost_eur', sa.Numeric(15, 2)),
        sa.Column('cost_as_pct_of_revenue', sa.Numeric(5, 2)),
        sa.Column('pd_impact_basis_points', sa.Integer),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    # Optimized indexes for time-series queries (replacing TimescaleDB hypertable)
    op.create_index('idx_cbam_cost_portfolio_date', 'cbam_cost_projection', ['portfolio_id', 'projection_date'])
    op.create_index('idx_cbam_cost_date_scenario', 'cbam_cost_projection', ['projection_date', 'scenario_id'])
    op.create_index('idx_cbam_cost_date_range', 'cbam_cost_projection', [sa.text('projection_date DESC')])
    op.create_index('idx_cbam_cost_counterparty', 'cbam_cost_projection', ['counterparty_id'])

    # 5. cbam_compliance_report
    op.create_table(
        'cbam_compliance_report',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('portfolio_id', UUID(as_uuid=True), nullable=True),
        sa.Column('reporting_entity_id', UUID(as_uuid=True), nullable=True),
        sa.Column('report_year', sa.Integer, nullable=False),
        sa.Column('report_quarter', sa.Integer, nullable=False),
        sa.Column('submission_status', sa.String(50), server_default='draft'),
        sa.Column('total_embedded_emissions', sa.Numeric(15, 4)),
        sa.Column('total_certificate_cost', sa.Numeric(15, 2)),
        sa.Column('compliance_status', sa.String(50)),
        sa.UniqueConstraint('reporting_entity_id', 'report_year', 'report_quarter', name='uq_cbam_report_period'),
    )
    op.create_index('idx_cbam_report_entity', 'cbam_compliance_report', ['reporting_entity_id'])
    op.create_index('idx_cbam_report_period', 'cbam_compliance_report', ['report_year', 'report_quarter'])

    # 6. cbam_country_risk
    op.create_table(
        'cbam_country_risk',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('country_code', sa.String(2), nullable=False, unique=True),
        sa.Column('country_name', sa.String(100)),
        sa.Column('has_carbon_pricing', sa.Boolean, server_default=sa.false()),
        sa.Column('carbon_price_eur', sa.Numeric(10, 2)),
        sa.Column('grid_emission_factor', sa.Numeric(10, 6)),
        sa.Column('overall_risk_score', sa.Numeric(3, 2)),
        sa.Column('risk_category', sa.String(50)),
        sa.Column('default_value_markup', sa.Numeric(5, 2), server_default='0.30'),
    )

    # 7. cbam_verifier
    op.create_table(
        'cbam_verifier',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('verifier_name', sa.String(255), nullable=False),
        sa.Column('accreditation_body', sa.String(100)),
        sa.Column('accreditation_number', sa.String(50)),
        sa.Column('country_code', sa.String(2), nullable=False),
        sa.Column('accredited_sectors', JSONB, server_default='[]'),
        sa.Column('accreditation_status', sa.String(50), server_default='active'),
    )

    # 8. cbam_certificate_price (Standard PostgreSQL with optimized indexes — NO TimescaleDB)
    op.create_table(
        'cbam_certificate_price',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('price_date', sa.Date, nullable=False),
        sa.Column('eu_ets_auction_price_eur', sa.Numeric(10, 2)),
        sa.Column('cbam_certificate_price_eur', sa.Numeric(10, 2)),
        sa.Column('scenario_id', UUID(as_uuid=True), nullable=True),
        sa.Column('is_projection', sa.Boolean, server_default=sa.false()),
    )
    # Optimized indexes for time-series queries (replacing TimescaleDB hypertable)
    op.create_index('idx_cbam_price_date_scenario', 'cbam_certificate_price', ['price_date', 'scenario_id'])
    op.create_index('idx_cbam_price_date_range', 'cbam_certificate_price', [sa.text('price_date DESC')])
    op.create_index('idx_cbam_price_unique', 'cbam_certificate_price', ['price_date', 'scenario_id'], unique=True)


def downgrade():
    op.drop_table('cbam_certificate_price')
    op.drop_table('cbam_verifier')
    op.drop_table('cbam_country_risk')
    op.drop_table('cbam_compliance_report')
    op.drop_table('cbam_cost_projection')
    op.drop_table('cbam_embedded_emissions')
    op.drop_table('cbam_supplier')
    op.drop_table('cbam_product_category')
