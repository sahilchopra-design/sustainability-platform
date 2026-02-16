"""
Add Real Estate Valuation Tables

Revision ID: 004_add_real_estate_valuation_tables
Revises: 003_add_nature_risk_tables
Create Date: 2025-01-15

This migration adds tables for the Real Estate Valuation Engine:
- properties: Core property data
- valuations: Valuation results with all three approaches
- comparable_sales: Market comparables for sales comparison approach
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


def upgrade():
    """Create real estate valuation tables."""
    
    # 1. Properties Table
    op.create_table(
        'properties',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('property_name', sa.String(255), nullable=False),
        sa.Column('property_type', sa.String(50), nullable=False),
        sa.Column('subcategory', sa.String(100)),
        
        # Location
        sa.Column('address', sa.Text),
        sa.Column('city', sa.String(100)),
        sa.Column('state_province', sa.String(100)),
        sa.Column('country', sa.String(100)),
        sa.Column('postal_code', sa.String(20)),
        sa.Column('latitude', sa.Numeric(10, 8)),
        sa.Column('longitude', sa.Numeric(11, 8)),
        
        # Physical Characteristics
        sa.Column('year_built', sa.Integer),
        sa.Column('gross_floor_area_m2', sa.Numeric(10, 2)),
        sa.Column('rentable_area_sf', sa.Numeric(10, 2)),
        sa.Column('land_area_acres', sa.Numeric(8, 4)),
        sa.Column('num_floors', sa.Integer),
        sa.Column('num_units', sa.Integer),
        sa.Column('construction_type', sa.String(50)),
        sa.Column('quality_rating', sa.String(20)),
        sa.Column('condition_rating', sa.String(20)),
        sa.Column('effective_age', sa.Integer),
        sa.Column('total_economic_life', sa.Integer),
        
        # Financial Data
        sa.Column('market_value', sa.Numeric(15, 2)),
        sa.Column('replacement_value', sa.Numeric(15, 2)),
        sa.Column('land_value', sa.Numeric(15, 2)),
        sa.Column('annual_rental_income', sa.Numeric(12, 2)),
        sa.Column('potential_gross_income', sa.Numeric(12, 2)),
        sa.Column('effective_gross_income', sa.Numeric(12, 2)),
        sa.Column('operating_expenses', sa.Numeric(12, 2)),
        sa.Column('noi', sa.Numeric(12, 2)),
        sa.Column('cap_rate', sa.Numeric(5, 4)),
        sa.Column('discount_rate', sa.Numeric(5, 4)),
        
        # Operating Metrics
        sa.Column('vacancy_rate', sa.Numeric(5, 4)),
        sa.Column('collection_loss_rate', sa.Numeric(5, 4)),
        sa.Column('expense_ratio', sa.Numeric(5, 4)),
        
        # Energy & Sustainability
        sa.Column('epc_rating', sa.String(10)),
        sa.Column('epc_score', sa.Numeric(5, 2)),
        sa.Column('energy_intensity_kwh_m2', sa.Numeric(8, 2)),
        
        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        
        # Constraints
        sa.CheckConstraint(
            "property_type IN ('office', 'retail', 'industrial', 'multifamily', 'hotel', "
            "'self_storage', 'healthcare', 'data_center', 'mixed_use')",
            name='ck_properties_property_type'
        ),
        sa.CheckConstraint(
            "quality_rating IS NULL OR quality_rating IN ('class_a', 'class_b', 'class_c')",
            name='ck_properties_quality_rating'
        ),
        sa.CheckConstraint(
            "condition_rating IS NULL OR condition_rating IN ('excellent', 'good', 'fair', 'poor')",
            name='ck_properties_condition_rating'
        ),
    )
    
    # Create indexes for properties
    op.create_index('ix_properties_property_type', 'properties', ['property_type'])
    op.create_index('ix_properties_city', 'properties', ['city'])
    op.create_index('ix_properties_quality_rating', 'properties', ['quality_rating'])
    op.create_index('ix_properties_location', 'properties', ['latitude', 'longitude'])
    
    # 2. Valuations Table
    op.create_table(
        'valuations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('property_id', UUID(as_uuid=True), sa.ForeignKey('properties.id', ondelete='CASCADE'), nullable=False),
        sa.Column('valuation_date', sa.Date, nullable=False),
        
        # Income Approach
        sa.Column('income_approach_value', sa.Numeric(15, 2)),
        sa.Column('income_method', sa.String(20)),
        sa.Column('pgi', sa.Numeric(12, 2)),
        sa.Column('egi', sa.Numeric(12, 2)),
        sa.Column('noi', sa.Numeric(12, 2)),
        sa.Column('cap_rate_used', sa.Numeric(5, 4)),
        sa.Column('dcf_npv', sa.Numeric(15, 2)),
        sa.Column('dcf_irr', sa.Numeric(5, 4)),
        
        # Cost Approach
        sa.Column('cost_approach_value', sa.Numeric(15, 2)),
        sa.Column('land_value', sa.Numeric(15, 2)),
        sa.Column('rcn', sa.Numeric(15, 2)),
        sa.Column('physical_depreciation', sa.Numeric(15, 2)),
        sa.Column('functional_obsolescence', sa.Numeric(15, 2)),
        sa.Column('external_obsolescence', sa.Numeric(15, 2)),
        sa.Column('total_depreciation', sa.Numeric(15, 2)),
        sa.Column('depreciated_improvements', sa.Numeric(15, 2)),
        
        # Sales Comparison
        sa.Column('sales_comparison_value', sa.Numeric(15, 2)),
        sa.Column('num_comparables_used', sa.Integer),
        sa.Column('avg_adjustment_pct', sa.Numeric(5, 2)),
        
        # Reconciliation
        sa.Column('reconciled_base_value', sa.Numeric(15, 2)),
        sa.Column('income_weight', sa.Numeric(3, 2)),
        sa.Column('cost_weight', sa.Numeric(3, 2)),
        sa.Column('sales_weight', sa.Numeric(3, 2)),
        
        # Final Adjusted Value
        sa.Column('adjusted_value', sa.Numeric(15, 2)),
        sa.Column('value_per_sf', sa.Numeric(10, 2)),
        sa.Column('confidence_range_low', sa.Numeric(15, 2)),
        sa.Column('confidence_range_high', sa.Numeric(15, 2)),
        
        # Additional data
        sa.Column('calculation_inputs', JSONB),
        sa.Column('calculation_details', JSONB),
        
        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Create indexes for valuations
    op.create_index('ix_valuations_property_id', 'valuations', ['property_id'])
    op.create_index('ix_valuations_valuation_date', 'valuations', ['valuation_date'])
    
    # 3. Comparable Sales Table
    op.create_table(
        'comparable_sales',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('property_type', sa.String(50), nullable=False),
        sa.Column('address', sa.Text),
        sa.Column('city', sa.String(100)),
        sa.Column('state_province', sa.String(100)),
        sa.Column('country', sa.String(100)),
        sa.Column('latitude', sa.Numeric(10, 8)),
        sa.Column('longitude', sa.Numeric(11, 8)),
        
        # Sale details
        sa.Column('sale_date', sa.Date),
        sa.Column('sale_price', sa.Numeric(15, 2)),
        sa.Column('size_sf', sa.Numeric(10, 2)),
        sa.Column('price_per_sf', sa.Numeric(10, 2)),
        
        # Property characteristics
        sa.Column('year_built', sa.Integer),
        sa.Column('num_units', sa.Integer),
        sa.Column('occupancy_rate', sa.Numeric(5, 4)),
        sa.Column('quality_rating', sa.String(20)),
        sa.Column('condition_rating', sa.String(20)),
        
        # Adjustment factors
        sa.Column('location_adjustment', sa.Numeric(8, 4)),
        sa.Column('size_adjustment', sa.Numeric(8, 4)),
        sa.Column('age_adjustment', sa.Numeric(8, 4)),
        sa.Column('quality_adjustment', sa.Numeric(8, 4)),
        sa.Column('time_adjustment', sa.Numeric(8, 4)),
        sa.Column('condition_adjustment', sa.Numeric(8, 4)),
        
        sa.Column('total_adjustment', sa.Numeric(8, 4)),
        sa.Column('adjusted_price', sa.Numeric(15, 2)),
        
        # Data source
        sa.Column('data_source', sa.String(100)),
        sa.Column('verified', sa.Boolean, default=False),
        
        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Create indexes for comparable_sales
    op.create_index('ix_comparable_sales_property_type', 'comparable_sales', ['property_type'])
    op.create_index('ix_comparable_sales_city', 'comparable_sales', ['city'])
    op.create_index('ix_comparable_sales_sale_date', 'comparable_sales', ['sale_date'])
    op.create_index('ix_comparable_sales_location', 'comparable_sales', ['latitude', 'longitude'])


def downgrade():
    """Drop real estate valuation tables."""
    op.drop_table('comparable_sales')
    op.drop_table('valuations')
    op.drop_table('properties')
