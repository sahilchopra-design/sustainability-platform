"""Add CSDDD + Sovereign Climate Risk tables

Revision ID: 046
Revises: 045
Create Date: 2026-03-09

New tables:
1. csddd_entities — Companies in scope of CSDDD
2. csddd_assessments — Due diligence compliance assessment records
3. csddd_adverse_impacts — Identified adverse impact register
4. csddd_value_chain_links — Value chain mapping for CSDDD
5. csddd_grievance_cases — Grievance mechanism / complaints log
6. sovereign_climate_assessments — Sovereign climate risk assessment records
7. sovereign_portfolio_assessments — Portfolio-level sovereign climate risk

Indexes for common join paths.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "046"
down_revision = "045"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. CSDDD Entities ─────────────────────────────────────────────────
    op.create_table(
        "csddd_entities",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_profile_id", UUID(as_uuid=True), nullable=True),
        sa.Column("entity_name", sa.String(300), nullable=False),
        sa.Column("is_eu_company", sa.Boolean, server_default="true"),
        sa.Column("employees", sa.Integer),
        sa.Column("net_turnover_eur", sa.Numeric(16, 2)),
        sa.Column("eu_generated_turnover_eur", sa.Numeric(16, 2)),
        sa.Column("scope_group", sa.String(30)),  # group_1/2/3, non_eu_group_1/2/3, out_of_scope
        sa.Column("in_scope", sa.Boolean, server_default="false"),
        sa.Column("applies_from", sa.Date),
        sa.Column("nace_codes", JSONB),
        sa.Column("high_risk_sectors", JSONB),
        sa.Column("country_iso2", sa.String(3)),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["company_profile_id"], ["company_profiles.id"],
                                name="fk_csddd_entity_cp", ondelete="SET NULL"),
    )
    op.create_index("ix_csddd_entity_cp", "csddd_entities", ["company_profile_id"])
    op.create_index("ix_csddd_entity_scope", "csddd_entities", ["scope_group"])
    op.create_index("ix_csddd_entity_in_scope", "csddd_entities", ["in_scope"])

    # ── 2. CSDDD Assessments ──────────────────────────────────────────────
    op.create_table(
        "csddd_assessments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_id", UUID(as_uuid=True), nullable=True),
        sa.Column("entity_name", sa.String(300), nullable=False),
        sa.Column("assessment_date", sa.Date, nullable=False),
        sa.Column("scope_group", sa.String(30)),
        # Obligation scores (0-100)
        sa.Column("dd_policy_score", sa.Numeric(6, 2)),
        sa.Column("impact_identification_score", sa.Numeric(6, 2)),
        sa.Column("prevention_mitigation_score", sa.Numeric(6, 2)),
        sa.Column("remediation_score", sa.Numeric(6, 2)),
        sa.Column("stakeholder_engagement_score", sa.Numeric(6, 2)),
        sa.Column("grievance_mechanism_score", sa.Numeric(6, 2)),
        sa.Column("monitoring_score", sa.Numeric(6, 2)),
        sa.Column("reporting_score", sa.Numeric(6, 2)),
        # Overall
        sa.Column("overall_score", sa.Numeric(6, 2)),
        sa.Column("compliance_status", sa.String(30)),
        # Climate transition plan
        sa.Column("climate_plan_score", sa.Numeric(6, 2)),
        sa.Column("climate_plan_gaps", JSONB),
        # Director duty
        sa.Column("director_duty_assessment", JSONB),
        sa.Column("grievance_mechanism_status", sa.String(30)),
        # Gaps & recs
        sa.Column("total_gaps", sa.Integer),
        sa.Column("critical_gaps", sa.Integer),
        sa.Column("obligation_scores", JSONB),
        sa.Column("recommendations", JSONB),
        # Penalty
        sa.Column("penalty_exposure", JSONB),
        # EUDR overlap
        sa.Column("eudr_overlap", JSONB),
        # Cross-framework
        sa.Column("cross_framework_linkage", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["entity_id"], ["csddd_entities.id"],
                                name="fk_csddd_assess_entity", ondelete="SET NULL"),
    )
    op.create_index("ix_csddd_assess_entity", "csddd_assessments", ["entity_id"])
    op.create_index("ix_csddd_assess_status", "csddd_assessments", ["compliance_status"])
    op.create_index("ix_csddd_assess_date", "csddd_assessments", ["assessment_date"])

    # ── 3. CSDDD Adverse Impacts ──────────────────────────────────────────
    op.create_table(
        "csddd_adverse_impacts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_id", UUID(as_uuid=True), nullable=True),
        sa.Column("assessment_id", UUID(as_uuid=True), nullable=True),
        sa.Column("impact_code", sa.String(10), nullable=False),
        sa.Column("title", sa.String(200)),
        sa.Column("category", sa.String(20)),  # human_rights / environment
        sa.Column("severity_weight", sa.Numeric(4, 2)),
        sa.Column("likelihood", sa.String(20)),  # actual / potential
        sa.Column("priority", sa.String(20)),
        sa.Column("value_chain_location", sa.String(30)),
        sa.Column("source", sa.String(100)),
        sa.Column("mitigation_action", sa.Text),
        sa.Column("remediation_status", sa.String(30)),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["entity_id"], ["csddd_entities.id"],
                                name="fk_csddd_impact_entity", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assessment_id"], ["csddd_assessments.id"],
                                name="fk_csddd_impact_assess", ondelete="SET NULL"),
    )
    op.create_index("ix_csddd_impact_entity", "csddd_adverse_impacts", ["entity_id"])
    op.create_index("ix_csddd_impact_code", "csddd_adverse_impacts", ["impact_code"])
    op.create_index("ix_csddd_impact_cat", "csddd_adverse_impacts", ["category"])
    op.create_index("ix_csddd_impact_priority", "csddd_adverse_impacts", ["priority"])

    # ── 4. CSDDD Value Chain Links ────────────────────────────────────────
    op.create_table(
        "csddd_value_chain_links",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_id", UUID(as_uuid=True), nullable=True),
        sa.Column("direction", sa.String(20), nullable=False),  # upstream / downstream
        sa.Column("tier", sa.Integer, server_default="1"),
        sa.Column("partner_name", sa.String(300)),
        sa.Column("partner_country", sa.String(3)),
        sa.Column("sector", sa.String(50)),
        sa.Column("nace_code", sa.String(10)),
        sa.Column("risk_tier", sa.String(20)),
        sa.Column("contractual_cascading", sa.Boolean, server_default="false"),
        sa.Column("last_audit_date", sa.Date),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["entity_id"], ["csddd_entities.id"],
                                name="fk_csddd_vc_entity", ondelete="SET NULL"),
    )
    op.create_index("ix_csddd_vc_entity", "csddd_value_chain_links", ["entity_id"])
    op.create_index("ix_csddd_vc_direction", "csddd_value_chain_links", ["direction"])
    op.create_index("ix_csddd_vc_tier", "csddd_value_chain_links", ["tier"])

    # ── 5. CSDDD Grievance Cases ──────────────────────────────────────────
    op.create_table(
        "csddd_grievance_cases",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_id", UUID(as_uuid=True), nullable=True),
        sa.Column("case_reference", sa.String(100), nullable=False),
        sa.Column("complaint_date", sa.Date),
        sa.Column("category", sa.String(20)),  # human_rights / environment
        sa.Column("impact_code", sa.String(10)),
        sa.Column("description", sa.Text),
        sa.Column("complainant_type", sa.String(50)),
        sa.Column("value_chain_location", sa.String(30)),
        sa.Column("status", sa.String(30), server_default="open"),
        sa.Column("resolution_date", sa.Date),
        sa.Column("resolution_description", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["entity_id"], ["csddd_entities.id"],
                                name="fk_csddd_grievance_entity", ondelete="SET NULL"),
    )
    op.create_index("ix_csddd_griev_entity", "csddd_grievance_cases", ["entity_id"])
    op.create_index("ix_csddd_griev_status", "csddd_grievance_cases", ["status"])
    op.create_index("ix_csddd_griev_cat", "csddd_grievance_cases", ["category"])

    # ── 6. Sovereign Climate Assessments ──────────────────────────────────
    op.create_table(
        "sovereign_climate_assessments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("country_iso2", sa.String(3), nullable=False),
        sa.Column("country_name", sa.String(100)),
        sa.Column("assessment_date", sa.Date, nullable=False),
        sa.Column("scenario", sa.String(30), nullable=False),
        sa.Column("horizon", sa.String(4), nullable=False),
        # Scores
        sa.Column("physical_risk_score", sa.Numeric(6, 2)),
        sa.Column("transition_risk_score", sa.Numeric(6, 2)),
        sa.Column("fiscal_vulnerability_score", sa.Numeric(6, 2)),
        sa.Column("adaptation_readiness_score", sa.Numeric(6, 2)),
        sa.Column("composite_climate_risk_score", sa.Numeric(6, 2)),
        # Rating
        sa.Column("baseline_rating", sa.String(5)),
        sa.Column("climate_adjusted_rating", sa.String(5)),
        sa.Column("notch_adjustment", sa.Integer),
        sa.Column("climate_spread_delta_bps", sa.Numeric(8, 2)),
        # Decomposition
        sa.Column("risk_decomposition", JSONB),
        sa.Column("nd_gain_score", sa.Numeric(6, 2)),
        sa.Column("ndc_ambition_score", sa.Numeric(4, 1)),
        sa.Column("notes", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_sov_clim_country", "sovereign_climate_assessments", ["country_iso2"])
    op.create_index("ix_sov_clim_scenario", "sovereign_climate_assessments", ["scenario"])
    op.create_index("ix_sov_clim_horizon", "sovereign_climate_assessments", ["horizon"])
    op.create_index("ix_sov_clim_composite", "sovereign_climate_assessments",
                    ["composite_climate_risk_score"])

    # ── 7. Sovereign Portfolio Assessments ─────────────────────────────────
    op.create_table(
        "sovereign_portfolio_assessments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("portfolio_name", sa.String(200), nullable=False),
        sa.Column("assessment_date", sa.Date, nullable=False),
        sa.Column("scenario", sa.String(30)),
        sa.Column("horizon", sa.String(4)),
        sa.Column("total_exposure_usd", sa.Numeric(18, 2)),
        sa.Column("country_count", sa.Integer),
        sa.Column("weighted_avg_climate_risk", sa.Numeric(6, 2)),
        sa.Column("weighted_avg_notch_adjustment", sa.Numeric(6, 2)),
        sa.Column("weighted_avg_spread_delta_bps", sa.Numeric(8, 2)),
        sa.Column("total_climate_var_usd", sa.Numeric(18, 2)),
        sa.Column("country_results", JSONB),
        sa.Column("risk_tier_distribution", JSONB),
        sa.Column("region_breakdown", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_sov_port_scenario", "sovereign_portfolio_assessments", ["scenario"])
    op.create_index("ix_sov_port_date", "sovereign_portfolio_assessments", ["assessment_date"])


def downgrade() -> None:
    op.drop_table("sovereign_portfolio_assessments")
    op.drop_table("sovereign_climate_assessments")
    op.drop_table("csddd_grievance_cases")
    op.drop_table("csddd_value_chain_links")
    op.drop_table("csddd_adverse_impacts")
    op.drop_table("csddd_assessments")
    op.drop_table("csddd_entities")
