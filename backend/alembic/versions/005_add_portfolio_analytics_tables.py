"""
Add Portfolio Analytics Tables

Revision ID: 005_add_portfolio_analytics_tables
Revises: 004_add_real_estate_valuation_tables
Create Date: 2025-01-15

This migration adds tables for the Portfolio Aggregation and Reporting Module:
- portfolio_analytics: Main portfolio entity
- portfolio_property_holdings: Properties held in portfolios
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '005_add_portfolio_analytics_tables'
down_revision = '004_add_real_estate_valuation_tables'
branch_labels = None
depends_on = None


def upgrade():
    """Create portfolio analytics tables."""
    
    # 1. Portfolio Analytics Table
    op.create_table(
        'portfolio_analytics',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('portfolio_type', sa.String(50), nullable=False, default='fund'),
        sa.Column('investment_strategy', sa.String(50)),
        sa.Column('target_return', sa.Numeric(5, 2)),
        sa.Column('aum', sa.Numeric(15, 2), nullable=False, default=0),
        sa.Column('currency', sa.String(3), default='USD'),
        sa.Column('inception_date', sa.Date),
        sa.Column('owner_id', UUID(as_uuid=True)),
        
        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        
        # Constraints
        sa.CheckConstraint(
            "portfolio_type IN ('fund', 'reit', 'separate_account', 'index', 'pension', 'insurance')",
            name='ck_portfolio_analytics_type'
        ),
        sa.CheckConstraint(
            "investment_strategy IS NULL OR investment_strategy IN ('core', 'core_plus', 'value_add', 'opportunistic', 'debt')",
            name='ck_portfolio_analytics_strategy'
        ),
    )
    
    # Create indexes
    op.create_index('ix_portfolio_analytics_name', 'portfolio_analytics', ['name'])
    op.create_index('ix_portfolio_analytics_type', 'portfolio_analytics', ['portfolio_type'])
    op.create_index('ix_portfolio_analytics_owner', 'portfolio_analytics', ['owner_id'])
    
    # 2. Portfolio Property Holdings Table
    op.create_table(
        'portfolio_property_holdings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('portfolio_id', UUID(as_uuid=True), sa.ForeignKey('portfolio_analytics.id', ondelete='CASCADE'), nullable=False),
        sa.Column('property_id', UUID(as_uuid=True)),
        
        # Property details (denormalized for performance)
        sa.Column('property_name', sa.String(255)),
        sa.Column('property_type', sa.String(50)),
        sa.Column('property_location', sa.String(255)),
        
        # Acquisition info
        sa.Column('acquisition_date', sa.Date),
        sa.Column('acquisition_cost', sa.Numeric(15, 2)),
        sa.Column('current_value', sa.Numeric(15, 2)),
        sa.Column('ownership_percentage', sa.Numeric(5, 4), default=1.0),
        
        # Income
        sa.Column('annual_income', sa.Numeric(12, 2)),
        sa.Column('unrealized_gain_loss', sa.Numeric(15, 2)),
        
        # Sustainability
        sa.Column('gresb_score', sa.Integer),
        sa.Column('certifications', JSONB),  # Array of certification names
        
        # Risk
        sa.Column('risk_score', sa.Integer),
        sa.Column('is_stranded', sa.Boolean, default=False),
        sa.Column('years_to_stranding', sa.Integer),
        
        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Create indexes
    op.create_index('ix_portfolio_holdings_portfolio', 'portfolio_property_holdings', ['portfolio_id'])
    op.create_index('ix_portfolio_holdings_property', 'portfolio_property_holdings', ['property_id'])
    op.create_index('ix_portfolio_holdings_type', 'portfolio_property_holdings', ['property_type'])
    op.create_index('ix_portfolio_holdings_stranded', 'portfolio_property_holdings', ['is_stranded'])
    
    # 3. Portfolio Reports Table
    op.create_table(
        'portfolio_reports',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('portfolio_id', UUID(as_uuid=True), sa.ForeignKey('portfolio_analytics.id', ondelete='CASCADE'), nullable=False),
        sa.Column('report_type', sa.String(50), nullable=False),
        sa.Column('report_format', sa.String(20), default='json'),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('content', JSONB),
        sa.Column('error_message', sa.Text),
        
        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        
        # Constraints
        sa.CheckConstraint(
            "report_type IN ('valuation', 'climate_risk', 'sustainability', 'tcfd', 'investor', 'executive')",
            name='ck_portfolio_reports_type'
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed')",
            name='ck_portfolio_reports_status'
        ),
    )
    
    op.create_index('ix_portfolio_reports_portfolio', 'portfolio_reports', ['portfolio_id'])
    op.create_index('ix_portfolio_reports_type', 'portfolio_reports', ['report_type'])


def downgrade():
    """Drop portfolio analytics tables."""
    op.drop_table('portfolio_reports')
    op.drop_table('portfolio_property_holdings')
    op.drop_table('portfolio_analytics')
