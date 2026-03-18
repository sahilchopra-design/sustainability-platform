"""Add UK SDR assessment tables (E11)

Revision ID: 060
Revises: 059
Create Date: 2026-03-17

Tables:
  uk_sdr_assessments      — top-level SDR label eligibility + AGR assessment run
  uk_sdr_label_results    — per-label eligibility detail
  uk_sdr_agr_results      — per-requirement AGR check result
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "060"
down_revision = "059"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. uk_sdr_assessments
    op.create_table(
        "uk_sdr_assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("product_id", sa.Text, nullable=False),
        sa.Column("product_name", sa.Text, nullable=False),
        sa.Column("product_type", sa.Text),
        sa.Column("aum_gbp", sa.Numeric(20, 2)),
        sa.Column("domicile", sa.CHAR(3)),
        sa.Column("distributor_type", sa.Text),
        sa.Column("fca_authorised", sa.Boolean),
        sa.Column("qualifying_sustainable_pct", sa.Numeric(6, 2)),
        sa.Column("sustainability_evidence_quality", sa.Text),
        sa.Column("data_coverage_pct", sa.Numeric(6, 2)),
        sa.Column("recommended_label", sa.Text),
        sa.Column("overall_status", sa.Text),
        sa.Column("agr_compliant", sa.Boolean),
        sa.Column("agr_blocking_gaps", sa.Integer),
        sa.Column("icis_score", sa.Numeric(5, 1)),
        sa.Column("icis_tier", sa.Text),
        sa.Column("naming_compliant", sa.Boolean),
        sa.Column("naming_prohibited_terms", postgresql.JSONB),
        sa.Column("sfdr_classification", sa.Text),
        sa.Column("disclosure_obligations", postgresql.JSONB),
        sa.Column("priority_actions", postgresql.JSONB),
        sa.Column("assessment_date", sa.Date),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()")),
    )
    op.create_index("ix_uk_sdr_assessments_product_id", "uk_sdr_assessments", ["product_id"])
    op.create_index("ix_uk_sdr_assessments_date", "uk_sdr_assessments", ["assessment_date"])

    # 2. uk_sdr_label_results
    op.create_table(
        "uk_sdr_label_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("assessment_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("uk_sdr_assessments.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("label_id", sa.Text, nullable=False),
        sa.Column("label_name", sa.Text),
        sa.Column("eligible", sa.Boolean),
        sa.Column("qualifying_pct", sa.Numeric(6, 2)),
        sa.Column("threshold_pct", sa.Numeric(6, 2)),
        sa.Column("gaps", postgresql.JSONB),
        sa.Column("conditions", postgresql.JSONB),
    )
    op.create_index("ix_uk_sdr_label_results_assessment_id", "uk_sdr_label_results", ["assessment_id"])

    # 3. uk_sdr_agr_results
    op.create_table(
        "uk_sdr_agr_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("assessment_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("uk_sdr_assessments.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("req_id", sa.Text, nullable=False),
        sa.Column("title", sa.Text),
        sa.Column("source", sa.Text),
        sa.Column("blocking", sa.Boolean),
        sa.Column("compliant", sa.Boolean),
        sa.Column("status", sa.Text),
    )
    op.create_index("ix_uk_sdr_agr_results_assessment_id", "uk_sdr_agr_results", ["assessment_id"])


def downgrade() -> None:
    op.drop_table("uk_sdr_agr_results")
    op.drop_table("uk_sdr_label_results")
    op.drop_table("uk_sdr_assessments")
