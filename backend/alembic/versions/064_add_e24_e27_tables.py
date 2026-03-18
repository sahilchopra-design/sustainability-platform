"""Add E24-E27 tables: ISSB S2, GRI Standards, TPT Transition Plan, PCAF Sovereign Bonds

Revision ID: 064
Revises: 063
Create Date: 2026-03-17

Tables created:
  issb_s2_assessments        — IFRS S2 Climate-Related Disclosures (E24)
  gri_standards_reports      — GRI Universal Standards 2021 + GRI 300 Environment series (E25)
  gri_topic_disclosures      — Per-topic GRI disclosure completeness (FK soft ref to gri_standards_reports) (E25)
  tpt_transition_plans       — TPT Disclosure Framework 2023 assessment records (E26)
  pcaf_sovereign_assessments — PCAF Part D Sovereign Bonds & Loans attribution records (E27)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers
revision = "064"
down_revision = "063"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # E24 — ISSB S2 Climate-Related Disclosures: issb_s2_assessments
    # ------------------------------------------------------------------
    op.create_table(
        "issb_s2_assessments",
        sa.Column(
            "id",
            sa.Text,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()::text"),
        ),
        sa.Column("assessment_id", sa.Text, nullable=False, unique=True),
        sa.Column("entity_id", sa.Text, nullable=False),
        sa.Column("entity_name", sa.Text, nullable=False),
        sa.Column("industry_sector", sa.Text, nullable=True),       # SASB industry
        sa.Column("reporting_period", sa.Text, nullable=True),
        sa.Column("governance_score", sa.Float, nullable=True),
        sa.Column("strategy_score", sa.Float, nullable=True),
        sa.Column("risk_mgmt_score", sa.Float, nullable=True),
        sa.Column("metrics_targets_score", sa.Float, nullable=True),
        sa.Column("overall_compliance_pct", sa.Float, nullable=True),
        sa.Column("scenario_analysis", JSONB, nullable=True),       # 3 scenarios with outputs
        sa.Column("physical_risks", JSONB, nullable=True),          # identified physical risks
        sa.Column("transition_risks", JSONB, nullable=True),        # identified transition risks
        sa.Column("climate_opportunities", JSONB, nullable=True),
        sa.Column("scope1_tco2e", sa.Float, nullable=True),
        sa.Column("scope2_tco2e", sa.Float, nullable=True),
        sa.Column("scope3_tco2e", sa.Float, nullable=True),
        sa.Column("financed_emissions_tco2e", sa.Float, nullable=True),
        sa.Column("internal_carbon_price", sa.Float, nullable=True),
        sa.Column("climate_capex_pct", sa.Float, nullable=True),
        sa.Column("cross_industry_metrics", JSONB, nullable=True),
        sa.Column("industry_metrics", JSONB, nullable=True),        # SASB climate metrics
        sa.Column("disclosure_gaps", JSONB, nullable=True),
        sa.Column("tcfd_cross_reference", JSONB, nullable=True),
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
        "ix_issb_s2_assessments_entity_id",
        "issb_s2_assessments",
        ["entity_id"],
    )
    op.create_index(
        "ix_issb_s2_assessments_assessment_id",
        "issb_s2_assessments",
        ["assessment_id"],
    )

    # ------------------------------------------------------------------
    # E25 — GRI Standards: gri_standards_reports
    # ------------------------------------------------------------------
    op.create_table(
        "gri_standards_reports",
        sa.Column(
            "id",
            sa.Text,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()::text"),
        ),
        sa.Column("report_id", sa.Text, nullable=False, unique=True),
        sa.Column("entity_id", sa.Text, nullable=False),
        sa.Column("entity_name", sa.Text, nullable=False),
        sa.Column("reporting_period", sa.Text, nullable=True),
        sa.Column("gri_1_compliance_pct", sa.Float, nullable=True),  # GRI 1 Foundation
        sa.Column("gri_2_compliance_pct", sa.Float, nullable=True),  # GRI 2 General Disclosures
        sa.Column("gri_3_compliance_pct", sa.Float, nullable=True),  # GRI 3 Material Topics
        sa.Column("material_topics", JSONB, nullable=True),          # list of material GRI topics
        sa.Column("topic_boundary", JSONB, nullable=True),           # inside/outside org boundary
        sa.Column("gri_300_scores", JSONB, nullable=True),           # per GRI 301-308 scores
        sa.Column("content_index", JSONB, nullable=True),            # GRI Content Index structure
        sa.Column("overall_compliance_pct", sa.Float, nullable=True),
        sa.Column("assurance_level", sa.Text, nullable=True),        # none/limited/reasonable
        sa.Column("gri_service_level", sa.Text, nullable=True),      # core/comprehensive/with_reference
        sa.Column("disclosure_gaps", JSONB, nullable=True),
        sa.Column("warnings", JSONB, nullable=True),
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
        "ix_gri_standards_reports_entity_id",
        "gri_standards_reports",
        ["entity_id"],
    )

    # E25 — GRI per-topic disclosures: gri_topic_disclosures
    op.create_table(
        "gri_topic_disclosures",
        sa.Column(
            "id",
            sa.Text,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()::text"),
        ),
        sa.Column("report_id", sa.Text, nullable=False),             # soft ref to gri_standards_reports
        sa.Column("gri_standard", sa.Text, nullable=False),          # e.g. GRI 305
        sa.Column("standard_name", sa.Text, nullable=True),
        sa.Column("is_material", sa.Boolean, nullable=True),
        sa.Column("disclosures_completed", JSONB, nullable=True),
        sa.Column("disclosures_omitted", JSONB, nullable=True),
        sa.Column("compliance_pct", sa.Float, nullable=True),
        sa.Column("data_quality", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_gri_topic_disclosures_report_id",
        "gri_topic_disclosures",
        ["report_id"],
    )

    # ------------------------------------------------------------------
    # E26 — TPT Transition Plan: tpt_transition_plans
    # ------------------------------------------------------------------
    op.create_table(
        "tpt_transition_plans",
        sa.Column(
            "id",
            sa.Text,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()::text"),
        ),
        sa.Column("plan_id", sa.Text, nullable=False, unique=True),
        sa.Column("entity_id", sa.Text, nullable=False),
        sa.Column("entity_name", sa.Text, nullable=False),
        sa.Column("entity_type", sa.Text, nullable=True),            # bank/insurer/asset_manager/pension
        sa.Column("plan_year", sa.Integer, nullable=True),
        sa.Column("foundations_score", sa.Float, nullable=True),     # Element 1
        sa.Column("implementation_score", sa.Float, nullable=True),  # Element 2
        sa.Column("engagement_score", sa.Float, nullable=True),      # Element 3
        sa.Column("metrics_targets_score", sa.Float, nullable=True), # Element 4
        sa.Column("governance_score", sa.Float, nullable=True),      # Element 5
        sa.Column("finance_score", sa.Float, nullable=True),         # Element 6
        sa.Column("overall_quality_score", sa.Float, nullable=True),
        sa.Column("quality_tier", sa.Text, nullable=True),           # initial/developing/advanced/leading
        sa.Column("net_zero_target_year", sa.Integer, nullable=True),
        sa.Column("interim_targets", JSONB, nullable=True),          # 2025/2030/2035/2040 targets
        sa.Column("key_actions", JSONB, nullable=True),
        sa.Column("gap_analysis", JSONB, nullable=True),
        sa.Column("cross_framework", JSONB, nullable=True),          # TCFD/ISSB S2/CSRD cross-map
        sa.Column("financed_emissions_target", JSONB, nullable=True),
        sa.Column("capex_green_pct", sa.Float, nullable=True),
        sa.Column("warnings", JSONB, nullable=True),
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
        "ix_tpt_transition_plans_entity_id",
        "tpt_transition_plans",
        ["entity_id"],
    )
    op.create_index(
        "ix_tpt_transition_plans_plan_id",
        "tpt_transition_plans",
        ["plan_id"],
    )

    # ------------------------------------------------------------------
    # E27 — PCAF Sovereign Bonds: pcaf_sovereign_assessments
    # ------------------------------------------------------------------
    op.create_table(
        "pcaf_sovereign_assessments",
        sa.Column(
            "id",
            sa.Text,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()::text"),
        ),
        sa.Column("assessment_id", sa.Text, nullable=False, unique=True),
        sa.Column("entity_id", sa.Text, nullable=False),             # FI entity
        sa.Column("entity_name", sa.Text, nullable=False),
        sa.Column("country_code", sa.Text, nullable=False),
        sa.Column("country_name", sa.Text, nullable=False),
        sa.Column("outstanding_amount_mn", sa.Float, nullable=True),
        sa.Column("gdp_bn", sa.Float, nullable=True),
        sa.Column("government_debt_bn", sa.Float, nullable=True),
        sa.Column("attribution_factor", sa.Float, nullable=True),    # outstanding / gov debt
        sa.Column("sovereign_ghg_inventory_tco2e", sa.Float, nullable=True),
        sa.Column("financed_emissions_tco2e", sa.Float, nullable=True),
        sa.Column("emissions_intensity", sa.Float, nullable=True),   # tCO2e per €M invested
        sa.Column("pcaf_dqs", sa.Integer, nullable=True),            # 1-5
        sa.Column("ndc_target_pct", sa.Float, nullable=True),        # NDC 2030 reduction
        sa.Column("ndc_alignment", sa.Text, nullable=True),          # aligned/partial/misaligned
        sa.Column("climate_risk_score", sa.Float, nullable=True),    # from sovereign climate engine
        sa.Column("national_circumstances", JSONB, nullable=True),   # LULUCF, annexes, etc.
        sa.Column("portfolio_context", JSONB, nullable=True),        # weight in portfolio
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
        "ix_pcaf_sovereign_assessments_entity_id",
        "pcaf_sovereign_assessments",
        ["entity_id"],
    )
    op.create_index(
        "ix_pcaf_sovereign_assessments_country_code",
        "pcaf_sovereign_assessments",
        ["country_code"],
    )


def downgrade() -> None:
    op.drop_table("pcaf_sovereign_assessments")
    op.drop_table("tpt_transition_plans")
    op.drop_table("gri_topic_disclosures")
    op.drop_table("gri_standards_reports")
    op.drop_table("issb_s2_assessments")
