"""Add E20-E23 tables: EBA Pillar3, Scope3 Categories, SFDR Product Reporting, Biodiversity Finance

Revision ID: 063
Revises: 062
Create Date: 2026-03-17

Tables created:
  eba_pillar3_assessments      — EBA Pillar 3 ESG Disclosures (E20)
  scope3_category_assessments  — Scope 3 Category materiality + calculations (E21)
  sfdr_product_reports         — SFDR Art 8/9 periodic report records (E22)
  sfdr_product_pai_results     — Per-indicator PAI values (FK to sfdr_product_reports) (E22)
  biodiversity_assessments     — TNFD/SBTN/CBD GBF assessment records (E23)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers
revision = "063"
down_revision = "062"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # E20 — EBA Pillar 3: eba_pillar3_assessments
    # ------------------------------------------------------------------
    op.create_table(
        "eba_pillar3_assessments",
        sa.Column(
            "id",
            sa.Text,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()::text"),
        ),
        sa.Column("assessment_id", sa.Text, nullable=False, unique=True),
        sa.Column("entity_id", sa.Text, nullable=False),
        sa.Column("entity_name", sa.Text, nullable=False),
        sa.Column("institution_type", sa.Text, nullable=True),   # G-SII/O-SII/Other
        sa.Column("total_assets_bn", sa.Float, nullable=True),
        sa.Column("templates_completed", JSONB, nullable=True),  # list of T1-T10
        sa.Column("compliance_score", sa.Float, nullable=True),
        sa.Column("missing_mandatory", JSONB, nullable=True),
        sa.Column("template_scores", JSONB, nullable=True),
        sa.Column("next_disclosure_date", sa.Text, nullable=True),
        sa.Column("financed_emissions_intensity", sa.Float, nullable=True),
        sa.Column("carbon_related_assets_pct", sa.Float, nullable=True),
        sa.Column("taxonomy_aligned_pct", sa.Float, nullable=True),
        sa.Column("physical_risk_heatmap", JSONB, nullable=True),
        sa.Column("financed_emissions_by_sector", JSONB, nullable=True),
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
        "ix_eba_pillar3_assessments_entity_id",
        "eba_pillar3_assessments",
        ["entity_id"],
    )
    op.create_index(
        "ix_eba_pillar3_assessments_assessment_id",
        "eba_pillar3_assessments",
        ["assessment_id"],
    )

    # ------------------------------------------------------------------
    # E21 — Scope 3 Categories: scope3_category_assessments
    # ------------------------------------------------------------------
    op.create_table(
        "scope3_category_assessments",
        sa.Column(
            "id",
            sa.Text,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()::text"),
        ),
        sa.Column("assessment_id", sa.Text, nullable=False, unique=True),
        sa.Column("entity_id", sa.Text, nullable=False),
        sa.Column("entity_name", sa.Text, nullable=False),
        sa.Column("nace_code", sa.Text, nullable=True),
        sa.Column("revenue_bn", sa.Float, nullable=True),
        sa.Column("headcount", sa.Integer, nullable=True),
        sa.Column("material_categories", JSONB, nullable=True),    # list of category IDs
        sa.Column("flag_applicable", sa.Boolean, nullable=True),
        sa.Column("total_scope3_tco2e", sa.Float, nullable=True),
        sa.Column("sbti_coverage_pct", sa.Float, nullable=True),
        sa.Column("category_results", JSONB, nullable=True),       # per-category tCO2e + DQS
        sa.Column("portfolio_scope3", JSONB, nullable=True),       # C15 investment results
        sa.Column("flag_split", JSONB, nullable=True),
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
        "ix_scope3_category_assessments_entity_id",
        "scope3_category_assessments",
        ["entity_id"],
    )

    # ------------------------------------------------------------------
    # E22 — SFDR Product Reporting: sfdr_product_reports
    # ------------------------------------------------------------------
    op.create_table(
        "sfdr_product_reports",
        sa.Column(
            "id",
            sa.Text,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()::text"),
        ),
        sa.Column("report_id", sa.Text, nullable=False, unique=True),
        sa.Column("product_id", sa.Text, nullable=False),
        sa.Column("product_name", sa.Text, nullable=False),
        sa.Column("sfdr_article", sa.Text, nullable=True),          # "8" | "9"
        sa.Column("reporting_period", sa.Text, nullable=True),
        sa.Column("sustainable_investment_pct", sa.Float, nullable=True),
        sa.Column("taxonomy_aligned_pct", sa.Float, nullable=True),
        sa.Column("benchmark_index", sa.Text, nullable=True),
        sa.Column("report_completeness_pct", sa.Float, nullable=True),
        sa.Column("section_gaps", JSONB, nullable=True),
        sa.Column("warnings", JSONB, nullable=True),
        sa.Column("pai_coverage_pct", sa.Float, nullable=True),
        sa.Column("verified_sustainable_investment_pct", sa.Float, nullable=True),
        sa.Column("taxonomy_by_objective", JSONB, nullable=True),
        sa.Column("website_disclosure_complete", sa.Boolean, nullable=True),
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
        "ix_sfdr_product_reports_product_id",
        "sfdr_product_reports",
        ["product_id"],
    )

    # ------------------------------------------------------------------
    # E22 — SFDR Product PAI Results: sfdr_product_pai_results
    # ------------------------------------------------------------------
    op.create_table(
        "sfdr_product_pai_results",
        sa.Column(
            "id",
            sa.Text,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()::text"),
        ),
        sa.Column("report_id", sa.Text, nullable=False),           # soft ref to sfdr_product_reports
        sa.Column("indicator_id", sa.Text, nullable=False),
        sa.Column("indicator_name", sa.Text, nullable=True),
        sa.Column("value", sa.Float, nullable=True),
        sa.Column("unit", sa.Text, nullable=True),
        sa.Column("coverage_pct", sa.Float, nullable=True),
        sa.Column("benchmark_value", sa.Float, nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_sfdr_product_pai_results_report_id",
        "sfdr_product_pai_results",
        ["report_id"],
    )

    # ------------------------------------------------------------------
    # E23 — Biodiversity Finance: biodiversity_assessments
    # ------------------------------------------------------------------
    op.create_table(
        "biodiversity_assessments",
        sa.Column(
            "id",
            sa.Text,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()::text"),
        ),
        sa.Column("assessment_id", sa.Text, nullable=False, unique=True),
        sa.Column("entity_id", sa.Text, nullable=False),
        sa.Column("entity_name", sa.Text, nullable=False),
        sa.Column("sector", sa.Text, nullable=True),
        sa.Column("assessment_type", sa.Text, nullable=True),      # tnfd | msa | sbtn | cbd_gbf
        # TNFD
        sa.Column("tnfd_overall_maturity", sa.Integer, nullable=True),
        sa.Column("tnfd_pillar_scores", JSONB, nullable=True),
        sa.Column("tnfd_gaps", JSONB, nullable=True),
        # MSA
        sa.Column("msa_footprint_km2", sa.Float, nullable=True),
        sa.Column("msa_by_land_use", JSONB, nullable=True),
        # SBTN
        sa.Column("sbtn_readiness_score", sa.Float, nullable=True),
        sa.Column("sbtn_steps_complete", sa.Integer, nullable=True),
        sa.Column("sbtn_target_types", JSONB, nullable=True),
        # CBD GBF
        sa.Column("cbd_gbf_alignment", sa.Text, nullable=True),    # aligned/progressing/early-stage
        sa.Column("cbd_gbf_sub_element_scores", JSONB, nullable=True),
        sa.Column("transition_finance_pct", sa.Float, nullable=True),
        # Combined
        sa.Column("cross_framework", JSONB, nullable=True),
        sa.Column("priority_actions", JSONB, nullable=True),
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
        "ix_biodiversity_assessments_entity_id",
        "biodiversity_assessments",
        ["entity_id"],
    )
    op.create_index(
        "ix_biodiversity_assessments_assessment_id",
        "biodiversity_assessments",
        ["assessment_id"],
    )


def downgrade() -> None:
    op.drop_table("biodiversity_assessments")
    op.drop_table("sfdr_product_pai_results")
    op.drop_table("sfdr_product_reports")
    op.drop_table("scope3_category_assessments")
    op.drop_table("eba_pillar3_assessments")
