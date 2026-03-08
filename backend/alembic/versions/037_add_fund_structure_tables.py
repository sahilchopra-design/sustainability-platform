"""Add fund structure tables for asset manager module

Revision ID: 037_add_fund_structure_tables
Revises: 036_add_cdm_tools_tables
Create Date: 2026-03-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from datetime import datetime

# revision identifiers
revision = '037_add_fund_structure_tables'
down_revision = '036_add_cdm_tools_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ---- Funds ----
    op.create_table(
        'funds',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('fund_name', sa.String(255), nullable=False),
        sa.Column('fund_code', sa.String(50), unique=True),
        sa.Column('sfdr_classification', sa.String(20), nullable=False),  # art6 / art8 / art8plus / art9
        sa.Column('fund_type', sa.String(50)),  # ucits / aif / etf / mandate
        sa.Column('domicile', sa.String(3)),  # ISO country
        sa.Column('base_currency', sa.String(3), nullable=False, server_default='EUR'),
        sa.Column('inception_date', sa.Date),
        sa.Column('aum', sa.Numeric(18, 2)),  # Assets Under Management
        sa.Column('aum_date', sa.Date),
        sa.Column('benchmark_index', sa.String(255)),  # e.g. MSCI World, S&P 500
        sa.Column('benchmark_ticker', sa.String(50)),
        sa.Column('investment_strategy', sa.String(100)),  # core / value / growth / balanced / thematic
        sa.Column('esg_strategy', sa.String(100)),  # exclusion / best-in-class / integration / impact / engagement
        sa.Column('taxonomy_objective', sa.String(100)),  # climate_mitigation / adaptation / water / circular / pollution / biodiversity
        sa.Column('minimum_taxonomy_pct', sa.Numeric(5, 2)),  # % committed to taxonomy-aligned investments
        sa.Column('minimum_sustainable_pct', sa.Numeric(5, 2)),  # % committed to sustainable investments
        sa.Column('manager_name', sa.String(255)),
        sa.Column('organisation_id', UUID(as_uuid=True)),
        sa.Column('metadata', JSONB, server_default='{}'),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('now()')),
    )

    # ---- Share Classes ----
    op.create_table(
        'fund_share_classes',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('fund_id', UUID(as_uuid=True), sa.ForeignKey('funds.id', ondelete='CASCADE'), nullable=False),
        sa.Column('class_name', sa.String(100), nullable=False),  # e.g. "Class A EUR Acc"
        sa.Column('isin', sa.String(12), unique=True),
        sa.Column('currency', sa.String(3), nullable=False, server_default='EUR'),
        sa.Column('nav_per_share', sa.Numeric(18, 6)),
        sa.Column('nav_date', sa.Date),
        sa.Column('total_shares_outstanding', sa.Numeric(18, 4)),
        sa.Column('ter_pct', sa.Numeric(5, 4)),  # Total Expense Ratio
        sa.Column('management_fee_pct', sa.Numeric(5, 4)),
        sa.Column('performance_fee_pct', sa.Numeric(5, 4)),
        sa.Column('distribution_type', sa.String(20)),  # acc / dist
        sa.Column('minimum_investment', sa.Numeric(18, 2)),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
    )

    # ---- Holdings (Position Level) ----
    op.create_table(
        'fund_holdings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('fund_id', UUID(as_uuid=True), sa.ForeignKey('funds.id', ondelete='CASCADE'), nullable=False),
        sa.Column('as_of_date', sa.Date, nullable=False),
        sa.Column('security_name', sa.String(255), nullable=False),
        sa.Column('isin', sa.String(12)),
        sa.Column('sedol', sa.String(7)),
        sa.Column('ticker', sa.String(20)),
        sa.Column('asset_class', sa.String(50)),  # equity / fixed_income / cash / alternative / derivative
        sa.Column('sector', sa.String(100)),  # GICS sector
        sa.Column('country', sa.String(3)),  # ISO country of issuer
        sa.Column('weight_pct', sa.Numeric(8, 5)),  # Portfolio weight %
        sa.Column('market_value', sa.Numeric(18, 2)),
        sa.Column('notional_value', sa.Numeric(18, 2)),
        sa.Column('acquisition_cost', sa.Numeric(18, 2)),
        sa.Column('quantity', sa.Numeric(18, 6)),
        sa.Column('entry_date', sa.Date),
        sa.Column('carbon_intensity_tco2_meur', sa.Numeric(12, 4)),  # tCO2e/M EUR revenue
        sa.Column('esg_score', sa.Numeric(5, 2)),
        sa.Column('esg_provider', sa.String(50)),  # msci / sustainalytics / iss / refinitiv
        sa.Column('taxonomy_aligned_pct', sa.Numeric(5, 2)),  # % of company revenue taxonomy-aligned
        sa.Column('dnsh_compliant', sa.Boolean),  # Do No Significant Harm
        sa.Column('exclusion_flag', sa.Boolean, server_default='false'),
        sa.Column('exclusion_reason', sa.String(255)),
        sa.Column('metadata', JSONB, server_default='{}'),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
    )
    op.create_index('ix_fund_holdings_fund_date', 'fund_holdings', ['fund_id', 'as_of_date'])
    op.create_index('ix_fund_holdings_isin', 'fund_holdings', ['isin'])

    # ---- Benchmark Holdings (for attribution) ----
    op.create_table(
        'benchmark_holdings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('benchmark_name', sa.String(255), nullable=False),
        sa.Column('as_of_date', sa.Date, nullable=False),
        sa.Column('security_name', sa.String(255)),
        sa.Column('isin', sa.String(12)),
        sa.Column('sector', sa.String(100)),
        sa.Column('country', sa.String(3)),
        sa.Column('weight_pct', sa.Numeric(8, 5)),
        sa.Column('carbon_intensity_tco2_meur', sa.Numeric(12, 4)),
        sa.Column('esg_score', sa.Numeric(5, 2)),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
    )
    op.create_index('ix_benchmark_holdings_name_date', 'benchmark_holdings', ['benchmark_name', 'as_of_date'])

    # ---- LP / Investor ----
    op.create_table(
        'fund_investors',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('fund_id', UUID(as_uuid=True), sa.ForeignKey('funds.id', ondelete='CASCADE'), nullable=False),
        sa.Column('investor_name', sa.String(255), nullable=False),
        sa.Column('investor_type', sa.String(50)),  # pension / insurance / endowment / family_office / sovereign / retail
        sa.Column('commitment', sa.Numeric(18, 2)),
        sa.Column('called', sa.Numeric(18, 2)),
        sa.Column('distributed', sa.Numeric(18, 2)),
        sa.Column('nav_share', sa.Numeric(18, 2)),  # LP's share of fund NAV
        sa.Column('dpi', sa.Numeric(8, 4)),  # Distributions / Paid-In
        sa.Column('tvpi', sa.Numeric(8, 4)),  # Total Value / Paid-In
        sa.Column('ownership_pct', sa.Numeric(5, 2)),
        sa.Column('vintage_year', sa.Integer),
        sa.Column('domicile', sa.String(3)),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('now()')),
    )

    # ---- Fund ESG Snapshot (periodic) ----
    op.create_table(
        'fund_esg_snapshots',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('fund_id', UUID(as_uuid=True), sa.ForeignKey('funds.id', ondelete='CASCADE'), nullable=False),
        sa.Column('snapshot_date', sa.Date, nullable=False),
        sa.Column('waci_tco2_meur', sa.Numeric(12, 4)),  # Weighted Avg Carbon Intensity
        sa.Column('carbon_footprint_tco2_meur', sa.Numeric(12, 4)),
        sa.Column('total_financed_emissions_tco2', sa.Numeric(18, 4)),
        sa.Column('avg_esg_score', sa.Numeric(5, 2)),
        sa.Column('taxonomy_aligned_pct', sa.Numeric(5, 2)),
        sa.Column('sustainable_investment_pct', sa.Numeric(5, 2)),
        sa.Column('active_share_pct', sa.Numeric(5, 2)),
        sa.Column('tracking_error_pct', sa.Numeric(8, 4)),
        sa.Column('holdings_count', sa.Integer),
        sa.Column('exclusion_breach_count', sa.Integer, server_default='0'),
        sa.Column('pai_indicators', JSONB, server_default='{}'),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
    )
    op.create_index('ix_fund_esg_snapshots_fund_date', 'fund_esg_snapshots', ['fund_id', 'snapshot_date'])


def downgrade() -> None:
    op.drop_table('fund_esg_snapshots')
    op.drop_table('fund_investors')
    op.drop_table('benchmark_holdings')
    op.drop_table('fund_holdings')
    op.drop_table('fund_share_classes')
    op.drop_table('funds')
