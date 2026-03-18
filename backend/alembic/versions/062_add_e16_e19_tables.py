"""062 — Add E16-E19 tables: ESMA Fund Names, SL Finance, IFRS S1, EU Taxonomy GAR

Revision ID: 062
Revises: 061
Create Date: 2026-03-17

Tables created:
  - esma_fund_name_assessments  (E16 — ESMA/2024/249 Fund Names ESG Guidelines)
  - sl_finance_assessments      (E17 — ICMA SLB / LMA SLL Principles)
  - ifrs_s1_assessments         (E18 — IFRS S1 General Sustainability Disclosures)
  - eu_taxonomy_gar_runs        (E19 — EU Taxonomy GAR/BTAR Art 8 Delegated Act)

All UUIDs generated in DB via gen_random_uuid()::text.
No FK constraints — soft references via TEXT columns only.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# ---------------------------------------------------------------------------
# Revision identifiers
# ---------------------------------------------------------------------------
revision = "062"
down_revision = "061"
branch_labels = None
depends_on = None


# ---------------------------------------------------------------------------
# Upgrade
# ---------------------------------------------------------------------------

def upgrade() -> None:
    # ------------------------------------------------------------------
    # E16 — ESMA Fund Names ESG Guidelines assessments
    # ------------------------------------------------------------------
    op.create_table(
        "esma_fund_name_assessments",
        sa.Column(
            "id",
            sa.Text(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()::text"),
        ),
        sa.Column("assessment_id", sa.Text(), nullable=False, unique=True),
        sa.Column("fund_id", sa.Text(), nullable=False),
        sa.Column("fund_name", sa.Text(), nullable=False),
        sa.Column("fund_type", sa.Text(), nullable=True),
        sa.Column("sfdr_classification", sa.Text(), nullable=True),
        sa.Column("esg_investment_pct", sa.Float(), nullable=True),
        sa.Column("required_threshold_pct", sa.Float(), nullable=True),
        sa.Column("threshold_met", sa.Boolean(), nullable=True),
        sa.Column("overall_compliant", sa.Boolean(), nullable=True),
        sa.Column("compliance_score", sa.Float(), nullable=True),
        sa.Column("detected_terms", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("term_categories", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("blocking_gaps", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("compliance_gaps", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("applicable_exclusions", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("recommendations", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("sfdr_alignment", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_esma_fund_name_assessments_fund_id",
        "esma_fund_name_assessments",
        ["fund_id"],
    )

    # ------------------------------------------------------------------
    # E17 — Sustainability-Linked Finance assessments
    # ------------------------------------------------------------------
    op.create_table(
        "sl_finance_assessments",
        sa.Column(
            "id",
            sa.Text(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()::text"),
        ),
        sa.Column("assessment_id", sa.Text(), nullable=False, unique=True),
        sa.Column("instrument_id", sa.Text(), nullable=False),
        sa.Column("issuer_name", sa.Text(), nullable=False),
        sa.Column("instrument_type", sa.Text(), nullable=False),
        sa.Column("tenor_years", sa.Integer(), nullable=True),
        sa.Column("issuance_amount", sa.Float(), nullable=True),
        sa.Column("currency", sa.Text(), nullable=True),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column("principles_compliant", sa.Boolean(), nullable=True),
        sa.Column("step_up_triggered", sa.Boolean(), nullable=True),
        sa.Column("coupon_step_up_bps", sa.Float(), nullable=True),
        sa.Column("spo_required", sa.Boolean(), nullable=True),
        sa.Column("spo_status", sa.Text(), nullable=True),
        sa.Column("blocking_gaps", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("kpi_assessments", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("component_assessments", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("recommendations", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_sl_finance_assessments_instrument_id",
        "sl_finance_assessments",
        ["instrument_id"],
    )
    op.create_index(
        "ix_sl_finance_assessments_issuer_name",
        "sl_finance_assessments",
        ["issuer_name"],
    )

    # ------------------------------------------------------------------
    # E18 — IFRS S1 assessments
    # ------------------------------------------------------------------
    op.create_table(
        "ifrs_s1_assessments",
        sa.Column(
            "id",
            sa.Text(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()::text"),
        ),
        sa.Column("assessment_id", sa.Text(), nullable=False, unique=True),
        sa.Column("entity_id", sa.Text(), nullable=False),
        sa.Column("entity_name", sa.Text(), nullable=False),
        sa.Column("industry", sa.Text(), nullable=True),
        sa.Column("reporting_year", sa.Integer(), nullable=True),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column("overall_compliant", sa.Boolean(), nullable=True),
        sa.Column("blocking_gaps", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("pillar_results", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("applied_reliefs", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("industry_sasb_codes", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("priority_actions", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_ifrs_s1_assessments_entity_id",
        "ifrs_s1_assessments",
        ["entity_id"],
    )
    op.create_index(
        "ix_ifrs_s1_assessments_reporting_year",
        "ifrs_s1_assessments",
        ["reporting_year"],
    )

    # ------------------------------------------------------------------
    # E19 — EU Taxonomy GAR runs
    # ------------------------------------------------------------------
    op.create_table(
        "eu_taxonomy_gar_runs",
        sa.Column(
            "id",
            sa.Text(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()::text"),
        ),
        sa.Column("assessment_id", sa.Text(), nullable=False, unique=True),
        sa.Column("entity_id", sa.Text(), nullable=False),
        sa.Column("entity_name", sa.Text(), nullable=False),
        sa.Column("reporting_year", sa.Integer(), nullable=True),
        sa.Column("total_covered_assets", sa.Float(), nullable=True),
        sa.Column("gar_numerator", sa.Float(), nullable=True),
        sa.Column("gar_pct", sa.Float(), nullable=True),
        sa.Column("btar_numerator", sa.Float(), nullable=True),
        sa.Column("btar_covered_assets", sa.Float(), nullable=True),
        sa.Column("btar_pct", sa.Float(), nullable=True),
        sa.Column("bsar_pct", sa.Float(), nullable=True),
        sa.Column("taxonomy_eligible_pct", sa.Float(), nullable=True),
        sa.Column("taxonomy_aligned_pct", sa.Float(), nullable=True),
        sa.Column("asset_breakdown", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("dnsh_assessments", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("min_safeguards", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("gaps", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("recommendations", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_eu_taxonomy_gar_runs_entity_id",
        "eu_taxonomy_gar_runs",
        ["entity_id"],
    )
    op.create_index(
        "ix_eu_taxonomy_gar_runs_reporting_year",
        "eu_taxonomy_gar_runs",
        ["reporting_year"],
    )


# ---------------------------------------------------------------------------
# Downgrade
# ---------------------------------------------------------------------------

def downgrade() -> None:
    op.drop_index("ix_eu_taxonomy_gar_runs_reporting_year", "eu_taxonomy_gar_runs")
    op.drop_index("ix_eu_taxonomy_gar_runs_entity_id", "eu_taxonomy_gar_runs")
    op.drop_table("eu_taxonomy_gar_runs")

    op.drop_index("ix_ifrs_s1_assessments_reporting_year", "ifrs_s1_assessments")
    op.drop_index("ix_ifrs_s1_assessments_entity_id", "ifrs_s1_assessments")
    op.drop_table("ifrs_s1_assessments")

    op.drop_index("ix_sl_finance_assessments_issuer_name", "sl_finance_assessments")
    op.drop_index("ix_sl_finance_assessments_instrument_id", "sl_finance_assessments")
    op.drop_table("sl_finance_assessments")

    op.drop_index("ix_esma_fund_name_assessments_fund_id", "esma_fund_name_assessments")
    op.drop_table("esma_fund_name_assessments")
