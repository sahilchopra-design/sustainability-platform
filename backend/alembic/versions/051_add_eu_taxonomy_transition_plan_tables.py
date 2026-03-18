"""Add EU Taxonomy Alignment and Climate Transition Plan Assessment tables

Revision ID: 051
Revises: 050
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "051"
down_revision = "050"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── EU Taxonomy Alignment ─────────────────────────────────────────────────

    op.create_table(
        "taxonomy_activity_assessments",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("activity_id", sa.String(100), nullable=False),
        sa.Column("nace_code", sa.String(20), nullable=False),
        sa.Column("activity_name", sa.String(255), nullable=False),
        sa.Column("sector", sa.String(100), nullable=False),
        sa.Column("objective_assessed", sa.String(10), nullable=False),
        sa.Column("substantial_contribution_met", sa.Boolean, default=False),
        sa.Column("sc_score", sa.Float, default=0.0),
        sa.Column("sc_evidence", JSONB, nullable=True),
        sa.Column("dnsh_results", JSONB, nullable=True),
        sa.Column("minimum_safeguards_met", sa.Boolean, default=False),
        sa.Column("ms_evidence", JSONB, nullable=True),
        sa.Column("taxonomy_aligned", sa.Boolean, default=False),
        sa.Column("taxonomy_eligible", sa.Boolean, default=False),
        sa.Column("transitional_activity", sa.Boolean, default=False),
        sa.Column("enabling_activity", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "taxonomy_entity_alignments",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("entity_name", sa.String(255), nullable=False),
        sa.Column("reporting_year", sa.Integer, nullable=False),
        sa.Column("total_turnover_eur", sa.Float, default=0.0),
        sa.Column("aligned_turnover_eur", sa.Float, default=0.0),
        sa.Column("turnover_alignment_pct", sa.Float, default=0.0),
        sa.Column("total_capex_eur", sa.Float, default=0.0),
        sa.Column("aligned_capex_eur", sa.Float, default=0.0),
        sa.Column("capex_alignment_pct", sa.Float, default=0.0),
        sa.Column("total_opex_eur", sa.Float, default=0.0),
        sa.Column("aligned_opex_eur", sa.Float, default=0.0),
        sa.Column("opex_alignment_pct", sa.Float, default=0.0),
        sa.Column("objective_breakdown", JSONB, nullable=True),
        sa.Column("eligibility_vs_alignment", JSONB, nullable=True),
        sa.Column("transitional_share_pct", sa.Float, default=0.0),
        sa.Column("enabling_share_pct", sa.Float, default=0.0),
        sa.Column("cross_framework_disclosures", JSONB, nullable=True),
        sa.Column("improvement_recommendations", JSONB, nullable=True),
        sa.Column("data_quality_flags", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "taxonomy_portfolio_alignments",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("portfolio_id", sa.String(100), nullable=False),
        sa.Column("portfolio_name", sa.String(255), nullable=False),
        sa.Column("reporting_year", sa.Integer, nullable=False),
        sa.Column("green_asset_ratio", sa.Float, default=0.0),
        sa.Column("btar", sa.Float, default=0.0),
        sa.Column("weighted_alignment_by_objective", JSONB, nullable=True),
        sa.Column("sector_breakdown", JSONB, nullable=True),
        sa.Column("sfdr_article_classification", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # ── Climate Transition Plan Assessment ────────────────────────────────────

    op.create_table(
        "transition_plan_assessments",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("entity_name", sa.String(255), nullable=False),
        sa.Column("sector", sa.String(100), nullable=False),
        sa.Column("reporting_year", sa.Integer, nullable=False),
        sa.Column("overall_score", sa.Float, default=0.0),
        sa.Column("overall_rating", sa.String(30), default="No Plan"),
        sa.Column("tpt_assessment", JSONB, nullable=True),
        sa.Column("gfanz_assessment", JSONB, nullable=True),
        sa.Column("iigcc_assessment", JSONB, nullable=True),
        sa.Column("csddd_compliance", JSONB, nullable=True),
        sa.Column("esrs_e1_coverage", JSONB, nullable=True),
        sa.Column("cdp_c4_alignment", JSONB, nullable=True),
        sa.Column("target_credibility_score", sa.Float, default=0.0),
        sa.Column("implementation_maturity_score", sa.Float, default=0.0),
        sa.Column("governance_strength_score", sa.Float, default=0.0),
        sa.Column("financial_commitment_score", sa.Float, default=0.0),
        sa.Column("cross_framework_completeness", JSONB, nullable=True),
        sa.Column("inter_framework_gaps", JSONB, nullable=True),
        sa.Column("improvement_roadmap", JSONB, nullable=True),
        sa.Column("regulatory_readiness", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "transition_plan_targets",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("assessment_id", sa.String(64), nullable=True),
        sa.Column("target_type", sa.String(30), nullable=False),
        sa.Column("target_year", sa.Integer, nullable=False),
        sa.Column("base_year", sa.Integer, nullable=True),
        sa.Column("interim_years", JSONB, nullable=True),
        sa.Column("scope_coverage", JSONB, nullable=True),
        sa.Column("reduction_pct", sa.Float, default=0.0),
        sa.Column("science_based", sa.Boolean, default=False),
        sa.Column("sbti_validated", sa.Boolean, default=False),
        sa.Column("paris_aligned", sa.Boolean, default=False),
        sa.Column("methodology", sa.String(255), nullable=True),
        sa.Column("credibility_score", sa.Float, default=0.0),
        sa.Column("gap_to_pathway", sa.Float, default=0.0),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "transition_plan_sector_pathways",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("entity_name", sa.String(255), nullable=True),
        sa.Column("sector", sa.String(100), nullable=False),
        sa.Column("pathway_source", sa.String(50), nullable=True),
        sa.Column("current_intensity", sa.Float, default=0.0),
        sa.Column("target_intensity", sa.Float, default=0.0),
        sa.Column("pathway_intensity_for_year", sa.Float, default=0.0),
        sa.Column("aligned", sa.Boolean, default=False),
        sa.Column("gap_pct", sa.Float, default=0.0),
        sa.Column("peer_comparison", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "transition_plan_cross_framework_maps",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("entity_name", sa.String(255), nullable=True),
        sa.Column("reporting_year", sa.Integer, nullable=True),
        sa.Column("framework_completeness", JSONB, nullable=True),
        sa.Column("datapoint_coverage", JSONB, nullable=True),
        sa.Column("gaps_identified", JSONB, nullable=True),
        sa.Column("overlap_analysis", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("transition_plan_cross_framework_maps")
    op.drop_table("transition_plan_sector_pathways")
    op.drop_table("transition_plan_targets")
    op.drop_table("transition_plan_assessments")
    op.drop_table("taxonomy_portfolio_alignments")
    op.drop_table("taxonomy_entity_alignments")
    op.drop_table("taxonomy_activity_assessments")
