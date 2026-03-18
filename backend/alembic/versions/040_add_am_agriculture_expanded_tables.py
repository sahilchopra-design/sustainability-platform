"""Add AM engine + agriculture expanded tables

Revision ID: 040
Revises: 039
Create Date: 2026-03-08

Tables:
  am_assessments                      — generic AM assessment log (all 6 sub-modules)
  agriculture_methane_assessments     — livestock methane intensity results
  agriculture_disease_assessments     — disease outbreak risk results
  agriculture_bng_assessments         — biodiversity net gain results
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers
revision = "040"
down_revision = "039"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # am_assessments — generic store for all AM Engine sub-module results
    # ------------------------------------------------------------------
    op.create_table(
        "am_assessments",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("module", sa.Text, nullable=False),
        # esg_attribution | paris_alignment | green_bond_screening |
        # climate_spreads | lp_analytics | optimisation
        sa.Column("payload", JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_am_assessments_module", "am_assessments", ["module"])
    op.create_index("ix_am_assessments_created_at", "am_assessments", ["created_at"])

    # ------------------------------------------------------------------
    # agriculture_methane_assessments
    # ------------------------------------------------------------------
    op.create_table(
        "agriculture_methane_assessments",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("entity_id", sa.Text, nullable=False),
        sa.Column("entity_name", sa.Text, nullable=True),
        sa.Column("livestock_type", sa.Text, nullable=False),
        sa.Column("herd_size", sa.Integer, nullable=False),
        sa.Column("total_ch4_tonnes_yr", sa.Numeric(12, 3), nullable=True),
        sa.Column("total_tco2e_yr", sa.Numeric(14, 1), nullable=True),
        sa.Column("intensity_kgch4_per_head", sa.Numeric(10, 2), nullable=True),
        sa.Column("max_abatement_pct", sa.Numeric(6, 1), nullable=True),
        sa.Column("assessed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_ag_methane_entity_id",
        "agriculture_methane_assessments", ["entity_id"]
    )

    # ------------------------------------------------------------------
    # agriculture_disease_assessments
    # ------------------------------------------------------------------
    op.create_table(
        "agriculture_disease_assessments",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("entity_id", sa.Text, nullable=False),
        sa.Column("entity_name", sa.Text, nullable=True),
        sa.Column("species", sa.Text, nullable=False),
        sa.Column("herd_value_eur", sa.Numeric(18, 2), nullable=True),
        sa.Column("combined_prob", sa.Numeric(8, 4), nullable=True),
        sa.Column("expected_loss_eur", sa.Numeric(18, 2), nullable=True),
        sa.Column("worst_case_eur", sa.Numeric(18, 2), nullable=True),
        sa.Column("risk_score", sa.Numeric(6, 1), nullable=True),
        sa.Column("risk_category", sa.Text, nullable=True),
        sa.Column("assessed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_ag_disease_entity_id",
        "agriculture_disease_assessments", ["entity_id"]
    )

    # ------------------------------------------------------------------
    # agriculture_bng_assessments
    # ------------------------------------------------------------------
    op.create_table(
        "agriculture_bng_assessments",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("entity_id", sa.Text, nullable=False),
        sa.Column("entity_name", sa.Text, nullable=True),
        sa.Column("site_area_ha", sa.Numeric(12, 2), nullable=True),
        sa.Column("baseline_units", sa.Numeric(10, 2), nullable=True),
        sa.Column("proposed_units", sa.Numeric(10, 2), nullable=True),
        sa.Column("net_gain_pct", sa.Numeric(8, 1), nullable=True),
        sa.Column("meets_requirement", sa.Boolean, server_default="false"),
        sa.Column("credits_required", sa.Numeric(10, 2), nullable=True),
        sa.Column("credit_cost_eur", sa.Numeric(14, 0), nullable=True),
        sa.Column("risk_rating", sa.Text, nullable=True),
        sa.Column("assessed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_ag_bng_entity_id",
        "agriculture_bng_assessments", ["entity_id"]
    )


def downgrade() -> None:
    op.drop_table("agriculture_bng_assessments")
    op.drop_table("agriculture_disease_assessments")
    op.drop_table("agriculture_methane_assessments")
    op.drop_table("am_assessments")
