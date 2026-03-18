"""Add SASB assessment and Model Validation tables

Revision ID: 048
Revises: 047
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "048"
down_revision = "047"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── SASB Industry Assessments ──────────────────────────────────────────

    op.create_table(
        "sasb_industry_assessments",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("entity_name", sa.String(255), nullable=False),
        sa.Column("sasb_industry_code", sa.String(10), nullable=False),
        sa.Column("sasb_industry_name", sa.String(200), nullable=True),
        sa.Column("reporting_year", sa.Integer, nullable=False),
        sa.Column("sics_sector", sa.String(100), nullable=True),
        sa.Column("total_applicable_metrics", sa.Integer, default=0),
        sa.Column("total_reported_metrics", sa.Integer, default=0),
        sa.Column("total_omitted_metrics", sa.Integer, default=0),
        sa.Column("completeness_pct", sa.Float, default=0.0),
        sa.Column("materiality_coverage_pct", sa.Float, default=0.0),
        sa.Column("avg_data_quality_score", sa.Float, default=5.0),
        sa.Column("metric_results", JSONB, nullable=True),
        sa.Column("materiality_map", JSONB, nullable=True),
        sa.Column("topic_scores", JSONB, nullable=True),
        sa.Column("peer_comparison", JSONB, nullable=True),
        sa.Column("issb_s2_cross_ref", JSONB, nullable=True),
        sa.Column("gri_cross_ref", JSONB, nullable=True),
        sa.Column("esrs_cross_ref", JSONB, nullable=True),
        sa.Column("gaps", JSONB, nullable=True),
        sa.Column("recommendations", JSONB, nullable=True),
        sa.Column("ifrs_s1_para55_compliant", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "sasb_materiality_assessments",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("entity_name", sa.String(255), nullable=False),
        sa.Column("sasb_industry_code", sa.String(10), nullable=False),
        sa.Column("reporting_year", sa.Integer, nullable=False),
        sa.Column("total_material_topics", sa.Integer, default=0),
        sa.Column("total_potentially_material", sa.Integer, default=0),
        sa.Column("total_not_material", sa.Integer, default=0),
        sa.Column("material_topics", JSONB, nullable=True),
        sa.Column("risk_exposure_by_category", JSONB, nullable=True),
        sa.Column("double_materiality_flags", JSONB, nullable=True),
        sa.Column("issb_alignment_pct", sa.Float, default=0.0),
        sa.Column("recommendations", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "sasb_peer_comparisons",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("entity_name", sa.String(255), nullable=False),
        sa.Column("sasb_industry_code", sa.String(10), nullable=False),
        sa.Column("reporting_year", sa.Integer, nullable=False),
        sa.Column("metrics_compared", sa.Integer, default=0),
        sa.Column("above_median_count", sa.Integer, default=0),
        sa.Column("below_median_count", sa.Integer, default=0),
        sa.Column("at_median_count", sa.Integer, default=0),
        sa.Column("peer_rank_label", sa.String(30), nullable=True),
        sa.Column("metric_comparisons", JSONB, nullable=True),
        sa.Column("sector_median_benchmarks", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # ── Model Validation Framework ─────────────────────────────────────────

    op.create_table(
        "model_validation_inventory",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("model_id", sa.String(100), nullable=False, unique=True),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("model_type", sa.String(50), nullable=True),
        sa.Column("risk_tier", sa.Integer, nullable=False),
        sa.Column("regulatory_framework", JSONB, nullable=True),
        sa.Column("validation_frequency", sa.String(30), nullable=True),
        sa.Column("lifecycle_state", sa.String(30), default="DEVELOPMENT"),
        sa.Column("last_validation_date", sa.DateTime, nullable=True),
        sa.Column("last_validation_result", sa.String(30), nullable=True),
        sa.Column("next_validation_due", sa.DateTime, nullable=True),
        sa.Column("owner", sa.String(100), nullable=True),
        sa.Column("engine_module", sa.String(100), nullable=True),
        sa.Column("key_outputs", JSONB, nullable=True),
        sa.Column("change_log", JSONB, nullable=True),
        sa.Column("findings", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "model_validation_backtests",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("model_id", sa.String(100), nullable=False),
        sa.Column("model_label", sa.String(255), nullable=True),
        sa.Column("backtest_date", sa.DateTime, nullable=False),
        sa.Column("observation_window_start", sa.Date, nullable=True),
        sa.Column("observation_window_end", sa.Date, nullable=True),
        sa.Column("sample_size", sa.Integer, default=0),
        sa.Column("test_results", JSONB, nullable=True),
        sa.Column("overall_traffic_light", sa.String(10), nullable=True),
        sa.Column("overall_pass_fail", sa.String(10), nullable=True),
        sa.Column("green_count", sa.Integer, default=0),
        sa.Column("amber_count", sa.Integer, default=0),
        sa.Column("red_count", sa.Integer, default=0),
        sa.Column("recommendations", JSONB, nullable=True),
        sa.Column("regulatory_status", sa.String(30), nullable=True),
        sa.Column("next_validation_due", sa.Date, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "model_validation_champion_challenger",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("champion_model_id", sa.String(100), nullable=False),
        sa.Column("challenger_model_id", sa.String(100), nullable=False),
        sa.Column("comparison_date", sa.DateTime, nullable=False),
        sa.Column("sample_size", sa.Integer, default=0),
        sa.Column("champion_metrics", JSONB, nullable=True),
        sa.Column("challenger_metrics", JSONB, nullable=True),
        sa.Column("winner", sa.String(20), nullable=True),
        sa.Column("significance_test", sa.String(200), nullable=True),
        sa.Column("p_value", sa.Float, nullable=True),
        sa.Column("recommendation", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "model_lifecycle_transitions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("model_id", sa.String(100), nullable=False),
        sa.Column("previous_state", sa.String(30), nullable=False),
        sa.Column("new_state", sa.String(30), nullable=False),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("transitioned_by", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("model_lifecycle_transitions")
    op.drop_table("model_validation_champion_challenger")
    op.drop_table("model_validation_backtests")
    op.drop_table("model_validation_inventory")
    op.drop_table("sasb_peer_comparisons")
    op.drop_table("sasb_materiality_assessments")
    op.drop_table("sasb_industry_assessments")
