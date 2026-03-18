"""add facilitated_emissions_v2 and insurance_emissions tables

Revision ID: 041
Revises: 040
Create Date: 2026-03-08

PCAF Part C — Capital Markets Facilitated Emissions (expanded)
PCAF Part B — Insurance-Associated Emissions
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

revision = "041"
down_revision = "040"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Facilitated Emissions v2 (PCAF Part C expanded) ──────────────────
    op.create_table(
        "facilitated_emissions_v2",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("deal_id", sa.Text, unique=True, nullable=False),
        sa.Column("deal_type", sa.Text, nullable=False),
        # Issuer
        sa.Column("issuer_name", sa.Text, nullable=False),
        sa.Column("issuer_id", sa.Text),
        sa.Column("issuer_sector_gics", sa.Text),
        sa.Column("issuer_country_iso2", sa.Text),
        sa.Column("issuer_revenue_musd", sa.Numeric(16, 4)),
        # Deal economics
        sa.Column("underwritten_amount_musd", sa.Numeric(16, 4)),
        sa.Column("total_deal_size_musd", sa.Numeric(16, 4)),
        sa.Column("shares_placed_value_musd", sa.Numeric(16, 4)),
        sa.Column("market_cap_musd", sa.Numeric(16, 4)),
        sa.Column("tranche_held_musd", sa.Numeric(16, 4)),
        sa.Column("total_pool_musd", sa.Numeric(16, 4)),
        sa.Column("arranged_amount_musd", sa.Numeric(16, 4)),
        sa.Column("total_facility_musd", sa.Numeric(16, 4)),
        # Bond details
        sa.Column("bond_type", sa.Text),
        sa.Column("coupon_rate_pct", sa.Numeric(8, 4)),
        sa.Column("maturity_years", sa.Integer),
        sa.Column("credit_rating", sa.Text),
        # Equity details
        sa.Column("ipo_or_secondary", sa.Text),
        sa.Column("offer_price", sa.Numeric(16, 4)),
        sa.Column("shares_offered", sa.BigInteger),
        sa.Column("overallotment_pct", sa.Numeric(8, 4)),
        # Securitisation details
        sa.Column("securitisation_type", sa.Text),
        sa.Column("underlying_asset_count", sa.Integer),
        sa.Column("weighted_avg_life_years", sa.Numeric(8, 2)),
        # Green / sustainable
        sa.Column("green_bond", sa.Boolean, server_default="false"),
        sa.Column("use_of_proceeds", sa.Text),
        sa.Column("eu_taxonomy_aligned_pct", sa.Numeric(8, 4)),
        # Issuer emissions
        sa.Column("issuer_scope1_tco2e", sa.Numeric(20, 4)),
        sa.Column("issuer_scope2_tco2e", sa.Numeric(20, 4)),
        sa.Column("issuer_scope3_tco2e", sa.Numeric(20, 4)),
        sa.Column("include_scope3", sa.Boolean, server_default="false"),
        # Computed results
        sa.Column("attribution_factor", sa.Numeric(12, 6)),
        sa.Column("attribution_method", sa.Text),
        sa.Column("facilitated_scope1_tco2e", sa.Numeric(20, 4)),
        sa.Column("facilitated_scope2_tco2e", sa.Numeric(20, 4)),
        sa.Column("facilitated_scope3_tco2e", sa.Numeric(20, 4)),
        sa.Column("facilitated_total_tco2e", sa.Numeric(20, 4)),
        sa.Column("pcaf_dqs", sa.Integer),
        sa.Column("green_classification", sa.Text),
        sa.Column("methodology_note", sa.Text),
        sa.Column("warnings", ARRAY(sa.Text)),
        # Metadata
        sa.Column("transaction_date", sa.Date),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_fev2_deal_type", "facilitated_emissions_v2", ["deal_type"])
    op.create_index("ix_fev2_issuer_sector", "facilitated_emissions_v2", ["issuer_sector_gics"])
    op.create_index("ix_fev2_green_bond", "facilitated_emissions_v2", ["green_bond"])

    # ── Insurance-Associated Emissions (PCAF Part B) ─────────────────────
    op.create_table(
        "insurance_emissions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("policy_id", sa.Text, unique=True, nullable=False),
        sa.Column("line_of_business", sa.Text, nullable=False),
        # Policyholder
        sa.Column("policyholder_name", sa.Text, nullable=False),
        sa.Column("policyholder_id", sa.Text),
        sa.Column("policyholder_sector_gics", sa.Text),
        sa.Column("policyholder_country_iso2", sa.Text),
        # Premium & claims
        sa.Column("gross_written_premium_musd", sa.Numeric(16, 4)),
        sa.Column("net_earned_premium_musd", sa.Numeric(16, 4)),
        sa.Column("claims_paid_musd", sa.Numeric(16, 4)),
        sa.Column("loss_ratio_pct", sa.Numeric(8, 4)),
        # Motor-specific
        sa.Column("vehicle_count", sa.Integer),
        sa.Column("fuel_type", sa.Text),
        sa.Column("annual_km_per_vehicle", sa.Numeric(12, 2)),
        # Property-specific
        sa.Column("insured_property_area_m2", sa.Numeric(16, 2)),
        sa.Column("epc_rating", sa.Text),
        sa.Column("building_type", sa.Text),
        # Commercial-specific
        sa.Column("insured_revenue_musd", sa.Numeric(16, 4)),
        sa.Column("nace_sector", sa.Text),
        # Direct emissions data
        sa.Column("policyholder_scope1_tco2e", sa.Numeric(20, 4)),
        sa.Column("policyholder_scope2_tco2e", sa.Numeric(20, 4)),
        # Computed results
        sa.Column("attribution_factor", sa.Numeric(12, 6)),
        sa.Column("attribution_method", sa.Text),
        sa.Column("insured_scope1_tco2e", sa.Numeric(20, 4)),
        sa.Column("insured_scope2_tco2e", sa.Numeric(20, 4)),
        sa.Column("insured_total_tco2e", sa.Numeric(20, 4)),
        sa.Column("emission_intensity_per_m_premium", sa.Numeric(12, 4)),
        sa.Column("pcaf_dqs", sa.Integer),
        sa.Column("methodology_note", sa.Text),
        sa.Column("warnings", ARRAY(sa.Text)),
        # Metadata
        sa.Column("policy_inception_date", sa.Date),
        sa.Column("policy_expiry_date", sa.Date),
        sa.Column("reporting_year", sa.Integer),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_ins_lob", "insurance_emissions", ["line_of_business"])
    op.create_index("ix_ins_sector", "insurance_emissions", ["policyholder_sector_gics"])
    op.create_index("ix_ins_year", "insurance_emissions", ["reporting_year"])


def downgrade() -> None:
    op.drop_table("insurance_emissions")
    op.drop_table("facilitated_emissions_v2")
