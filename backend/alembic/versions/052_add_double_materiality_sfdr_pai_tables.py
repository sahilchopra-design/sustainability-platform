"""Add double materiality and SFDR PAI tables

Revision ID: 052
Revises: 051
Create Date: 2026-03-09
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "052"
down_revision = "051"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Double Materiality Assessment ─────────────────────────────────
    op.create_table(
        "dma_assessments",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("entity_name", sa.String(255), nullable=False),
        sa.Column("sector", sa.String(100), nullable=False),
        sa.Column("reporting_year", sa.Integer),
        sa.Column("assessment_type", sa.String(50), default="full"),  # full, impact_only, financial_only
        sa.Column("impact_threshold", sa.Float, default=3.0),
        sa.Column("financial_threshold", sa.Float, default=3.0),
        sa.Column("impact_scores", JSONB),
        sa.Column("financial_scores", JSONB),
        sa.Column("combined_result", JSONB),
        sa.Column("material_topics", JSONB),
        sa.Column("matrix_data", JSONB),
        sa.Column("cross_framework_mapping", JSONB),
        sa.Column("assessor", sa.String(255)),
        sa.Column("status", sa.String(50), default="draft"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # ── DMA Topic Scores (per-topic detail) ────────────────────────────
    op.create_table(
        "dma_topic_scores",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("assessment_id", sa.Integer, sa.ForeignKey("dma_assessments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("esrs_topic", sa.String(20), nullable=False),  # E1, E2, ..., G1
        sa.Column("topic_name", sa.String(255)),
        sa.Column("impact_scale", sa.Float),
        sa.Column("impact_scope", sa.Float),
        sa.Column("impact_irremediability", sa.Float),
        sa.Column("impact_severity", sa.Float),  # computed
        sa.Column("financial_risk_likelihood", sa.Float),
        sa.Column("financial_risk_magnitude", sa.Float),
        sa.Column("financial_opportunity_magnitude", sa.Float),
        sa.Column("financial_score", sa.Float),  # computed
        sa.Column("is_material", sa.Boolean, default=False),
        sa.Column("materiality_class", sa.String(50)),  # impact_only, financial_only, double_material
        sa.Column("time_horizon", sa.String(20)),  # short, medium, long
        sa.Column("rationale", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # ── Stakeholder Engagement ─────────────────────────────────────────
    op.create_table(
        "dma_stakeholder_engagements",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("assessment_id", sa.Integer, sa.ForeignKey("dma_assessments.id", ondelete="CASCADE")),
        sa.Column("stakeholder_group", sa.String(100), nullable=False),
        sa.Column("engagement_method", sa.String(100)),
        sa.Column("topics_covered", JSONB),
        sa.Column("quality_score", sa.Float),
        sa.Column("coverage_pct", sa.Float),
        sa.Column("feedback_summary", sa.Text),
        sa.Column("engagement_date", sa.Date),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # ── SFDR PAI Assessments ───────────────────────────────────────────
    op.create_table(
        "sfdr_pai_assessments",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("entity_name", sa.String(255), nullable=False),
        sa.Column("entity_classification", sa.String(20)),  # article_6, article_8, article_9
        sa.Column("reporting_period", sa.String(20), nullable=False),
        sa.Column("portfolio_aum", sa.Float),
        sa.Column("portfolio_holdings_count", sa.Integer),
        sa.Column("mandatory_pais", JSONB),
        sa.Column("additional_pais", JSONB),
        sa.Column("data_coverage", JSONB),
        sa.Column("disclosure_status", sa.String(50), default="draft"),
        sa.Column("assessor", sa.String(255)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # ── SFDR PAI Indicator Values (per-indicator detail) ───────────────
    op.create_table(
        "sfdr_pai_indicator_values",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("assessment_id", sa.Integer, sa.ForeignKey("sfdr_pai_assessments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("indicator_id", sa.String(20), nullable=False),  # PAI_1 ... PAI_18
        sa.Column("indicator_name", sa.String(255)),
        sa.Column("category", sa.String(50)),  # environmental, social, governance
        sa.Column("asset_class", sa.String(50)),  # company, sovereign, real_estate
        sa.Column("is_mandatory", sa.Boolean, default=True),
        sa.Column("calculated_value", sa.Float),
        sa.Column("unit", sa.String(50)),
        sa.Column("data_quality_score", sa.Float),
        sa.Column("coverage_ratio", sa.Float),
        sa.Column("estimation_method", sa.String(100)),
        sa.Column("prior_period_value", sa.Float),
        sa.Column("trend", sa.String(20)),  # improved, deteriorated, stable
        sa.Column("benchmark_percentile", sa.Float),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # ── SFDR Entity Classification ─────────────────────────────────────
    op.create_table(
        "sfdr_entity_classifications",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("entity_name", sa.String(255), nullable=False),
        sa.Column("classification", sa.String(20), nullable=False),  # article_6, article_8, article_9
        sa.Column("classification_rationale", JSONB),
        sa.Column("sustainability_objective", sa.Boolean, default=False),
        sa.Column("promotes_esg", sa.Boolean, default=False),
        sa.Column("minimum_sustainable_investment_pct", sa.Float),
        sa.Column("taxonomy_alignment_pct", sa.Float),
        sa.Column("pai_consideration", sa.Boolean, default=False),
        sa.Column("exclusion_criteria", JSONB),
        sa.Column("effective_date", sa.Date),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # Indexes
    op.create_index("idx_dma_entity_year", "dma_assessments", ["entity_name", "reporting_year"])
    op.create_index("idx_dma_topic_assessment", "dma_topic_scores", ["assessment_id", "esrs_topic"])
    op.create_index("idx_sfdr_entity_period", "sfdr_pai_assessments", ["entity_name", "reporting_period"])
    op.create_index("idx_sfdr_indicator", "sfdr_pai_indicator_values", ["assessment_id", "indicator_id"])
    op.create_index("idx_sfdr_classification", "sfdr_entity_classifications", ["entity_name"])


def downgrade() -> None:
    op.drop_index("idx_sfdr_classification")
    op.drop_index("idx_sfdr_indicator")
    op.drop_index("idx_sfdr_entity_period")
    op.drop_index("idx_dma_topic_assessment")
    op.drop_index("idx_dma_entity_year")
    op.drop_table("sfdr_entity_classifications")
    op.drop_table("sfdr_pai_indicator_values")
    op.drop_table("sfdr_pai_assessments")
    op.drop_table("dma_stakeholder_engagements")
    op.drop_table("dma_topic_scores")
    op.drop_table("dma_assessments")
