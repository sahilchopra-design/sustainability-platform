"""Add climate risk assessment tables

Revision ID: 039
Revises: 038
Create Date: 2026-03-08

Tables:
  climate_assessment_methodologies   — methodology registry with lifecycle + config JSONB
  climate_methodology_templates      — 9 pre-calibrated read-only templates
  climate_assessment_runs            — run records with status, config, timing
  climate_assessment_results         — per-entity × scenario × horizon scores
  climate_physical_risk_scores       — per-hazard decomposition (child of results)
  climate_transition_risk_scores     — per-TCFD-category decomposition (child of results)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers
revision = "039"
down_revision = "038"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # climate_assessment_methodologies
    # ------------------------------------------------------------------
    op.create_table(
        "climate_assessment_methodologies",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", sa.Text, nullable=False, server_default="DRAFT"),
        # DRAFT | PUBLISHED | RETIRED | ARCHIVED
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("target_sectors", JSONB, nullable=False, server_default="[]"),
        # e.g. ["A", "C", "D"] — NACE section codes; empty = all sectors
        sa.Column("config", JSONB, nullable=False, server_default="{}"),
        # Full MethodologyConfig dict — physical, transition, integration, aggregation, output sub-objects
        sa.Column("change_log", JSONB, nullable=False, server_default="[]"),
        # [{field, old_value, new_value, changed_by, timestamp}, ...]
        sa.Column("approval_chain", JSONB, nullable=True),
        # [{action, by, at, version}, ...]
        sa.Column("is_template", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("template_name", sa.Text, nullable=True),
        # slug key for built-in templates
        sa.Column("created_by", sa.Text, nullable=False, server_default="system"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index(
        "ix_climate_methodologies_status",
        "climate_assessment_methodologies", ["status"]
    )
    op.create_index(
        "ix_climate_methodologies_template_name",
        "climate_assessment_methodologies", ["template_name"]
    )

    # ------------------------------------------------------------------
    # climate_assessment_runs
    # ------------------------------------------------------------------
    op.create_table(
        "climate_assessment_runs",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column(
            "methodology_id", sa.Text,
            sa.ForeignKey("climate_assessment_methodologies.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("methodology_name", sa.Text, nullable=True),
        sa.Column("methodology_version", sa.Integer, nullable=True),
        sa.Column("status", sa.Text, nullable=False, server_default="pending"),
        # pending | running | completed | failed | cancelled
        sa.Column("run_label", sa.Text, nullable=True),
        sa.Column("triggered_by", sa.Text, nullable=False, server_default="system"),
        sa.Column("scope", sa.Text, nullable=False, server_default="full_hierarchy"),
        # entity_only | full_hierarchy | securities_only
        sa.Column("target_entities", JSONB, nullable=False, server_default="[]"),
        # [EntityInput dicts] — input snapshot
        sa.Column("scenarios", JSONB, nullable=False, server_default="[]"),
        sa.Column("time_horizons", JSONB, nullable=False, server_default="[]"),
        sa.Column("entity_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("scenario_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("horizon_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("portfolio_aggregate", JSONB, nullable=True),
        # portfolio-level summary dict
        sa.Column("delta_against_run_id", sa.Text, nullable=True),
        sa.Column("delta_threshold", sa.Numeric(6, 4), nullable=False, server_default="0.05"),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Numeric(10, 3), nullable=True),
    )
    op.create_index("ix_climate_runs_methodology_id", "climate_assessment_runs", ["methodology_id"])
    op.create_index("ix_climate_runs_status", "climate_assessment_runs", ["status"])
    op.create_index("ix_climate_runs_started_at", "climate_assessment_runs", ["started_at"])

    # ------------------------------------------------------------------
    # climate_assessment_results
    # ------------------------------------------------------------------
    op.create_table(
        "climate_assessment_results",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column(
            "run_id", sa.Text,
            sa.ForeignKey("climate_assessment_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("entity_id", sa.Text, nullable=False),
        sa.Column("entity_name", sa.Text, nullable=True),
        sa.Column("entity_type", sa.Text, nullable=False),
        # portfolio | fund | security | asset | counterparty
        sa.Column("entity_level", sa.Integer, nullable=False, server_default="1"),
        # 1=portfolio, 2=fund, 3=security, 4=asset
        sa.Column("parent_result_id", sa.Text, nullable=True),
        # FK to parent in hierarchy (NULL for root)
        sa.Column("scenario", sa.Text, nullable=False),
        sa.Column("time_horizon", sa.Integer, nullable=False),
        # years from base
        sa.Column("integrated_score", sa.Numeric(8, 4), nullable=True),
        # 0-100 composite score
        sa.Column("physical_score", JSONB, nullable=True),
        # {composite_score, acute_score, chronic_score, cvar}
        sa.Column("transition_score", JSONB, nullable=True),
        # {composite_score, sector_classification, carbon_cost, stranded_asset, alignment, scenario_stress}
        sa.Column("nature_amplifier_applied", sa.Boolean, server_default="false"),
        sa.Column("drill_down", JSONB, nullable=True),
        # child entity scores stored inline for fast retrieval
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_climate_results_run_id", "climate_assessment_results", ["run_id"])
    op.create_index("ix_climate_results_entity_id", "climate_assessment_results", ["entity_id"])
    op.create_index(
        "ix_climate_results_scenario_horizon",
        "climate_assessment_results", ["scenario", "time_horizon"]
    )

    # ------------------------------------------------------------------
    # climate_physical_risk_scores   (per-hazard decomposition)
    # ------------------------------------------------------------------
    op.create_table(
        "climate_physical_risk_scores",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column(
            "result_id", sa.Text,
            sa.ForeignKey("climate_assessment_results.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("hazard_type", sa.Text, nullable=False),
        # riverine_flood | coastal_flood | tropical_cyclone | extreme_heat | wildfire | ...
        sa.Column("hazard_category", sa.Text, nullable=False, server_default="acute"),
        # acute | chronic
        sa.Column("hazard_score", sa.Numeric(8, 4), nullable=True),
        sa.Column("exposure_score", sa.Numeric(8, 4), nullable=True),
        sa.Column("vulnerability_score", sa.Numeric(8, 4), nullable=True),
        sa.Column("damage_estimate", sa.Numeric(18, 4), nullable=True),
        # EUR
        sa.Column("cvar", sa.Numeric(18, 4), nullable=True),
        # EUR CVaR at configured confidence
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_phys_scores_result_id", "climate_physical_risk_scores", ["result_id"])

    # ------------------------------------------------------------------
    # climate_transition_risk_scores  (per-TCFD-category decomposition)
    # ------------------------------------------------------------------
    op.create_table(
        "climate_transition_risk_scores",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column(
            "result_id", sa.Text,
            sa.ForeignKey("climate_assessment_results.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", sa.Text, nullable=False),
        # policy_legal | technology | market | reputation | sector_classification | carbon_cost | stranded_asset | alignment | scenario_stress
        sa.Column("score", sa.Numeric(8, 4), nullable=True),
        sa.Column("details", JSONB, nullable=True),
        # Extra breakdown: carbon_cost_eur, alignment_gap_pct, cprs_category, etc.
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_trans_scores_result_id", "climate_transition_risk_scores", ["result_id"])

    # ------------------------------------------------------------------
    # climate_delta_reports  (change tracking between runs)
    # ------------------------------------------------------------------
    op.create_table(
        "climate_delta_reports",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("current_run_id", sa.Text,
                  sa.ForeignKey("climate_assessment_runs.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("previous_run_id", sa.Text, nullable=False),
        sa.Column("entity_id", sa.Text, nullable=False),
        sa.Column("entity_name", sa.Text, nullable=True),
        sa.Column("metric_field", sa.Text, nullable=False),
        sa.Column("previous_value", sa.Numeric(10, 4), nullable=True),
        sa.Column("current_value", sa.Numeric(10, 4), nullable=True),
        sa.Column("change_pct", sa.Numeric(8, 2), nullable=True),
        sa.Column("is_significant", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_delta_reports_current_run", "climate_delta_reports", ["current_run_id"])


def downgrade() -> None:
    op.drop_table("climate_delta_reports")
    op.drop_table("climate_transition_risk_scores")
    op.drop_table("climate_physical_risk_scores")
    op.drop_table("climate_assessment_results")
    op.drop_table("climate_assessment_runs")
    op.drop_table("climate_assessment_methodologies")
