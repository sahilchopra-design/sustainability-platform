"""Add TNFD and CDP assessment tables

Revision ID: 049
Revises: 048
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "049"
down_revision = "048"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── TNFD Nature-Related Disclosures ─────────────────────────────────────

    op.create_table(
        "tnfd_disclosure_assessments",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("entity_name", sa.String(255), nullable=False),
        sa.Column("reporting_year", sa.Integer, nullable=False),
        sa.Column("overall_compliance_pct", sa.Float, default=0.0),
        sa.Column("sector", sa.String(100), nullable=True),
        sa.Column("disclosure_scores", JSONB, nullable=True),
        sa.Column("leap_results", JSONB, nullable=True),
        sa.Column("nature_risk_profile", JSONB, nullable=True),
        sa.Column("priority_locations_count", sa.Integer, default=0),
        sa.Column("ecosystem_services_at_risk", JSONB, nullable=True),
        sa.Column("sector_guidance_applied", sa.String(100), nullable=True),
        sa.Column("cross_framework_mapping", JSONB, nullable=True),
        sa.Column("gaps", JSONB, nullable=True),
        sa.Column("recommendations", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "tnfd_materiality_assessments",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("entity_name", sa.String(255), nullable=False),
        sa.Column("reporting_year", sa.Integer, nullable=False),
        sa.Column("sector", sa.String(100), nullable=True),
        sa.Column("material_dependencies", JSONB, nullable=True),
        sa.Column("material_impacts", JSONB, nullable=True),
        sa.Column("financial_materiality_score", sa.Float, default=0.0),
        sa.Column("impact_materiality_score", sa.Float, default=0.0),
        sa.Column("double_materiality_topics", JSONB, nullable=True),
        sa.Column("priority_ecosystem_services", JSONB, nullable=True),
        sa.Column("recommendations", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "tnfd_leap_readiness",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("entity_name", sa.String(255), nullable=False),
        sa.Column("reporting_year", sa.Integer, nullable=False),
        sa.Column("overall_readiness", sa.String(30), nullable=True),
        sa.Column("overall_score", sa.Float, default=0.0),
        sa.Column("locate_score", sa.Float, default=0.0),
        sa.Column("evaluate_score", sa.Float, default=0.0),
        sa.Column("assess_score", sa.Float, default=0.0),
        sa.Column("prepare_score", sa.Float, default=0.0),
        sa.Column("phase_details", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # ── CDP Climate & Water Scoring ─────────────────────────────────────────

    op.create_table(
        "cdp_climate_assessments",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("entity_name", sa.String(255), nullable=False),
        sa.Column("reporting_year", sa.Integer, nullable=False),
        sa.Column("questionnaire", sa.String(20), default="climate"),
        sa.Column("overall_score_pct", sa.Float, default=0.0),
        sa.Column("grade", sa.String(5), nullable=True),
        sa.Column("grade_label", sa.String(30), nullable=True),
        sa.Column("activity_group", sa.String(10), nullable=True),
        sa.Column("module_scores", JSONB, nullable=True),
        sa.Column("scoring_breakdown", JSONB, nullable=True),
        sa.Column("verification_status", JSONB, nullable=True),
        sa.Column("sbti_alignment", JSONB, nullable=True),
        sa.Column("cross_framework_mapping", JSONB, nullable=True),
        sa.Column("peer_comparison", JSONB, nullable=True),
        sa.Column("gaps", JSONB, nullable=True),
        sa.Column("recommendations", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "cdp_water_assessments",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("entity_name", sa.String(255), nullable=False),
        sa.Column("reporting_year", sa.Integer, nullable=False),
        sa.Column("overall_score_pct", sa.Float, default=0.0),
        sa.Column("grade", sa.String(5), nullable=True),
        sa.Column("grade_label", sa.String(30), nullable=True),
        sa.Column("module_scores", JSONB, nullable=True),
        sa.Column("water_risk_exposure", JSONB, nullable=True),
        sa.Column("facility_water_accounting", JSONB, nullable=True),
        sa.Column("cross_framework_mapping", JSONB, nullable=True),
        sa.Column("gaps", JSONB, nullable=True),
        sa.Column("recommendations", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("cdp_water_assessments")
    op.drop_table("cdp_climate_assessments")
    op.drop_table("tnfd_leap_readiness")
    op.drop_table("tnfd_materiality_assessments")
    op.drop_table("tnfd_disclosure_assessments")
