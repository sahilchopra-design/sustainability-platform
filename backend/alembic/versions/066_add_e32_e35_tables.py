"""Add E32-E35 tables: TNFD LEAP, Net Zero Targets, ESG Data Quality, Regulatory Penalties

Revision ID: 066
Revises: 065
Create Date: 2026-03-17

Tables created:
  tnfd_leap_assessments          — TNFD LEAP 4-step process assessments (E32)
  net_zero_target_assessments    — SBTi / NZBA / NZAMI / NZAOA target setting (E33)
  net_zero_pathway_records       — Per-year pathway milestones (soft ref to net_zero_target_assessments) (E33)
  esg_data_quality_reports       — ESG data quality scoring and coverage analysis (E34)
  esg_data_quality_indicators    — Per-indicator quality scores (soft ref to esg_data_quality_reports) (E34)
  regulatory_penalty_assessments — EU ESG enforcement & penalty calculation (E35)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "066"
down_revision = "065"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # E32 — TNFD LEAP: tnfd_leap_assessments
    # ------------------------------------------------------------------
    op.create_table(
        "tnfd_leap_assessments",
        sa.Column("id", sa.Text, primary_key=True, server_default=sa.text("gen_random_uuid()::text")),
        sa.Column("assessment_id", sa.Text, nullable=False, unique=True),
        sa.Column("entity_id", sa.Text, nullable=False),
        sa.Column("entity_name", sa.Text, nullable=False),
        sa.Column("sector", sa.Text, nullable=True),
        sa.Column("reporting_period", sa.Text, nullable=True),
        # L — Locate
        sa.Column("locate_score", sa.Float, nullable=True),
        sa.Column("priority_locations", JSONB, nullable=True),       # list of {location, biome, sensitivity}
        sa.Column("value_chain_scope", JSONB, nullable=True),        # upstream/ops/downstream coverage
        sa.Column("sensitive_ecosystems", JSONB, nullable=True),
        # E — Evaluate
        sa.Column("evaluate_score", sa.Float, nullable=True),
        sa.Column("dependencies", JSONB, nullable=True),             # ENCORE-based dependency list
        sa.Column("impacts", JSONB, nullable=True),                  # impact drivers list
        sa.Column("ecosystem_condition", JSONB, nullable=True),
        # A — Assess
        sa.Column("assess_score", sa.Float, nullable=True),
        sa.Column("material_risks", JSONB, nullable=True),
        sa.Column("material_opportunities", JSONB, nullable=True),
        sa.Column("risk_magnitude", sa.Text, nullable=True),         # low/medium/high/very_high
        sa.Column("opportunity_magnitude", sa.Text, nullable=True),
        # P — Prepare
        sa.Column("prepare_score", sa.Float, nullable=True),
        sa.Column("strategy_response", JSONB, nullable=True),
        sa.Column("targets_set", JSONB, nullable=True),
        sa.Column("disclosure_completeness_pct", sa.Float, nullable=True),
        # Overall
        sa.Column("overall_leap_score", sa.Float, nullable=True),
        sa.Column("leap_maturity", sa.Text, nullable=True),          # initial/developing/established/leading
        sa.Column("cross_framework", JSONB, nullable=True),
        sa.Column("priority_actions", JSONB, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_tnfd_leap_assessments_entity_id", "tnfd_leap_assessments", ["entity_id"])

    # ------------------------------------------------------------------
    # E33 — Net Zero Targets: net_zero_target_assessments
    # ------------------------------------------------------------------
    op.create_table(
        "net_zero_target_assessments",
        sa.Column("id", sa.Text, primary_key=True, server_default=sa.text("gen_random_uuid()::text")),
        sa.Column("assessment_id", sa.Text, nullable=False, unique=True),
        sa.Column("entity_id", sa.Text, nullable=False),
        sa.Column("entity_name", sa.Text, nullable=False),
        sa.Column("entity_type", sa.Text, nullable=True),            # corporate/bank/asset_manager/asset_owner
        sa.Column("framework", sa.Text, nullable=True),              # sbti/nzba/nzami/nzaoa/combined
        sa.Column("base_year", sa.Integer, nullable=True),
        sa.Column("net_zero_target_year", sa.Integer, nullable=True),
        sa.Column("near_term_target_year", sa.Integer, nullable=True),
        sa.Column("near_term_reduction_pct", sa.Float, nullable=True),
        sa.Column("long_term_reduction_pct", sa.Float, nullable=True),
        sa.Column("scope1_covered", sa.Boolean, nullable=True),
        sa.Column("scope2_covered", sa.Boolean, nullable=True),
        sa.Column("scope3_covered", sa.Boolean, nullable=True),
        sa.Column("sbti_validation_status", sa.Text, nullable=True), # committed/submitted/approved/achieved
        sa.Column("sbti_pathway", sa.Text, nullable=True),           # 1_5c/well_below_2c/2c
        sa.Column("flag_target", sa.Boolean, nullable=True),
        sa.Column("temperature_score", sa.Float, nullable=True),     # implied temp of portfolio/company
        sa.Column("pathway_gap_pct", sa.Float, nullable=True),       # gap vs required pathway
        sa.Column("interim_milestones", JSONB, nullable=True),
        sa.Column("residual_emissions_plan", JSONB, nullable=True),
        sa.Column("beyond_value_chain", JSONB, nullable=True),       # BVCM / carbon removal plan
        sa.Column("cross_framework", JSONB, nullable=True),
        sa.Column("warnings", JSONB, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_net_zero_target_assessments_entity_id", "net_zero_target_assessments", ["entity_id"])

    op.create_table(
        "net_zero_pathway_records",
        sa.Column("id", sa.Text, primary_key=True, server_default=sa.text("gen_random_uuid()::text")),
        sa.Column("assessment_id", sa.Text, nullable=False),         # soft ref
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("required_emissions_tco2e", sa.Float, nullable=True),
        sa.Column("projected_emissions_tco2e", sa.Float, nullable=True),
        sa.Column("gap_tco2e", sa.Float, nullable=True),
        sa.Column("on_track", sa.Boolean, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_net_zero_pathway_records_assessment_id", "net_zero_pathway_records", ["assessment_id"])

    # ------------------------------------------------------------------
    # E34 — ESG Data Quality: esg_data_quality_reports
    # ------------------------------------------------------------------
    op.create_table(
        "esg_data_quality_reports",
        sa.Column("id", sa.Text, primary_key=True, server_default=sa.text("gen_random_uuid()::text")),
        sa.Column("report_id", sa.Text, nullable=False, unique=True),
        sa.Column("entity_id", sa.Text, nullable=False),
        sa.Column("entity_name", sa.Text, nullable=False),
        sa.Column("reporting_period", sa.Text, nullable=True),
        sa.Column("overall_quality_score", sa.Float, nullable=True),
        sa.Column("overall_coverage_pct", sa.Float, nullable=True),
        sa.Column("e_pillar_score", sa.Float, nullable=True),
        sa.Column("s_pillar_score", sa.Float, nullable=True),
        sa.Column("g_pillar_score", sa.Float, nullable=True),
        sa.Column("estimated_indicators_pct", sa.Float, nullable=True),
        sa.Column("provider_divergence", JSONB, nullable=True),      # Bloomberg vs MSCI vs Sustainalytics
        sa.Column("dqs_profile", JSONB, nullable=True),              # PCAF DQS-style by module
        sa.Column("data_gaps", JSONB, nullable=True),
        sa.Column("material_gaps", JSONB, nullable=True),            # gaps in material indicators
        sa.Column("improvement_actions", JSONB, nullable=True),
        sa.Column("bcbs239_score", sa.Float, nullable=True),         # BCBS 239 data governance compliance
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_esg_data_quality_reports_entity_id", "esg_data_quality_reports", ["entity_id"])

    op.create_table(
        "esg_data_quality_indicators",
        sa.Column("id", sa.Text, primary_key=True, server_default=sa.text("gen_random_uuid()::text")),
        sa.Column("report_id", sa.Text, nullable=False),             # soft ref
        sa.Column("indicator_id", sa.Text, nullable=False),
        sa.Column("indicator_name", sa.Text, nullable=True),
        sa.Column("pillar", sa.Text, nullable=True),                 # E/S/G
        sa.Column("source", sa.Text, nullable=True),                 # reported/estimated/modelled/proxy
        sa.Column("coverage_pct", sa.Float, nullable=True),
        sa.Column("quality_score", sa.Float, nullable=True),
        sa.Column("dqs", sa.Integer, nullable=True),
        sa.Column("estimation_method", sa.Text, nullable=True),
        sa.Column("is_material", sa.Boolean, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_esg_data_quality_indicators_report_id", "esg_data_quality_indicators", ["report_id"])

    # ------------------------------------------------------------------
    # E35 — Regulatory Penalties: regulatory_penalty_assessments
    # ------------------------------------------------------------------
    op.create_table(
        "regulatory_penalty_assessments",
        sa.Column("id", sa.Text, primary_key=True, server_default=sa.text("gen_random_uuid()::text")),
        sa.Column("assessment_id", sa.Text, nullable=False, unique=True),
        sa.Column("entity_id", sa.Text, nullable=False),
        sa.Column("entity_name", sa.Text, nullable=False),
        sa.Column("annual_turnover_mn", sa.Float, nullable=True),
        sa.Column("regulations_assessed", JSONB, nullable=True),     # list of regulation IDs
        sa.Column("violations_found", sa.Integer, nullable=True),
        sa.Column("max_penalty_mn", sa.Float, nullable=True),
        sa.Column("expected_penalty_mn", sa.Float, nullable=True),
        sa.Column("penalty_by_regulation", JSONB, nullable=True),    # per-regulation max/expected
        sa.Column("csrd_compliance_pct", sa.Float, nullable=True),
        sa.Column("sfdr_compliance_pct", sa.Float, nullable=True),
        sa.Column("taxonomy_compliance_pct", sa.Float, nullable=True),
        sa.Column("eudr_compliance_pct", sa.Float, nullable=True),
        sa.Column("csddd_compliance_pct", sa.Float, nullable=True),
        sa.Column("supervisory_authority", JSONB, nullable=True),    # NCA/ESMA/EBA/EIOPA mapping
        sa.Column("whistleblower_risk", sa.Text, nullable=True),     # low/medium/high
        sa.Column("remediation_priority", JSONB, nullable=True),
        sa.Column("enforcement_timeline", JSONB, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_regulatory_penalty_assessments_entity_id", "regulatory_penalty_assessments", ["entity_id"])


def downgrade() -> None:
    op.drop_table("regulatory_penalty_assessments")
    op.drop_table("esg_data_quality_indicators")
    op.drop_table("esg_data_quality_reports")
    op.drop_table("net_zero_pathway_records")
    op.drop_table("net_zero_target_assessments")
    op.drop_table("tnfd_leap_assessments")
