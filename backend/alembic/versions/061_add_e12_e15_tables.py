"""Add E12-E15 tables: MiFID II SPT, TCFD Metrics, EU GBS, PRIIPs KID

Revision ID: 061
Revises: 060
Create Date: 2026-03-17

Tables created:
  mifid_preference_assessments  — MiFID II SPT assessment records (E12)
  tcfd_assessments              — TCFD 11-recommendation assessment runs (E13)
  tcfd_pillar_results           — Per-pillar TCFD result (FK to tcfd_assessments)
  eu_gbs_issuances              — EU Green Bond issuance assessments (E14)
  eu_gbs_reports                — Allocation/impact report records (FK to eu_gbs_issuances)
  priips_kid_records            — PRIIPs KID generation records (E15)
  priips_esg_inserts            — Per-insert records (FK to priips_kid_records)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers
revision = "061"
down_revision = "060"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # E12 — MiFID II SPT: mifid_preference_assessments
    # ------------------------------------------------------------------
    op.create_table(
        "mifid_preference_assessments",
        sa.Column(
            "id",
            sa.Text,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()::text"),
        ),
        sa.Column("assessment_id", sa.Text, nullable=False, unique=True),
        sa.Column("client_id", sa.Text, nullable=False),
        sa.Column("client_name", sa.Text, nullable=False),
        sa.Column("investor_type", sa.Text, nullable=True),
        sa.Column("risk_profile", sa.Text, nullable=True),
        # Category A / B / C preferences
        sa.Column("preference_category_a_min_pct", sa.Float, nullable=True),
        sa.Column("preference_category_b_min_pct", sa.Float, nullable=True),
        sa.Column("preference_category_c", sa.Boolean, nullable=True),
        # Outcome
        sa.Column("total_products_assessed", sa.Integer, nullable=True),
        sa.Column("matched_count", sa.Integer, nullable=True),
        sa.Column("match_rate_pct", sa.Float, nullable=True),
        sa.Column("adjustment_recommended", sa.Boolean, nullable=True),
        # Full result payload
        sa.Column("matched_products", JSONB, nullable=True),
        sa.Column("suitability_notes", JSONB, nullable=True),
        sa.Column("preferences_snapshot", JSONB, nullable=True),
        sa.Column("cross_framework", JSONB, nullable=True),
        # Timestamps
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
        "ix_mifid_preference_assessments_client_id",
        "mifid_preference_assessments",
        ["client_id"],
    )
    op.create_index(
        "ix_mifid_preference_assessments_assessment_id",
        "mifid_preference_assessments",
        ["assessment_id"],
    )

    # ------------------------------------------------------------------
    # E13 — TCFD: tcfd_assessments
    # ------------------------------------------------------------------
    op.create_table(
        "tcfd_assessments",
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
        sa.Column("disclosure_year", sa.Integer, nullable=True),
        sa.Column("overall_score", sa.Float, nullable=True),
        sa.Column("maturity_level", sa.Integer, nullable=True),
        sa.Column("maturity_name", sa.Text, nullable=True),
        sa.Column("blocking_gaps", JSONB, nullable=True),
        sa.Column("priority_actions", JSONB, nullable=True),
        sa.Column("recommendation_assessments", JSONB, nullable=True),
        sa.Column("sector_supplement", JSONB, nullable=True),
        sa.Column("cross_framework", JSONB, nullable=True),
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
        "ix_tcfd_assessments_entity_id",
        "tcfd_assessments",
        ["entity_id"],
    )
    op.create_index(
        "ix_tcfd_assessments_assessment_id",
        "tcfd_assessments",
        ["assessment_id"],
    )

    # ------------------------------------------------------------------
    # E13 — TCFD: tcfd_pillar_results
    # ------------------------------------------------------------------
    op.create_table(
        "tcfd_pillar_results",
        sa.Column(
            "id",
            sa.Text,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()::text"),
        ),
        sa.Column("tcfd_assessment_id", sa.Text, nullable=False),
        sa.Column("pillar_id", sa.Text, nullable=False),
        sa.Column("pillar_name", sa.Text, nullable=True),
        sa.Column("total_recommendations", sa.Integer, nullable=True),
        sa.Column("fully_disclosed", sa.Integer, nullable=True),
        sa.Column("partially_disclosed", sa.Integer, nullable=True),
        sa.Column("not_disclosed", sa.Integer, nullable=True),
        sa.Column("pillar_score", sa.Float, nullable=True),
        sa.Column("blocking_gaps", JSONB, nullable=True),
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
        sa.ForeignKeyConstraint(
            ["tcfd_assessment_id"],
            ["tcfd_assessments.assessment_id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_tcfd_pillar_results_tcfd_assessment_id",
        "tcfd_pillar_results",
        ["tcfd_assessment_id"],
    )

    # ------------------------------------------------------------------
    # E14 — EU GBS: eu_gbs_issuances
    # ------------------------------------------------------------------
    op.create_table(
        "eu_gbs_issuances",
        sa.Column(
            "id",
            sa.Text,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()::text"),
        ),
        sa.Column("assessment_id", sa.Text, nullable=False, unique=True),
        sa.Column("bond_id", sa.Text, nullable=False),
        sa.Column("issuer_name", sa.Text, nullable=False),
        sa.Column("bond_type", sa.Text, nullable=True),
        sa.Column("principal_amount", sa.Float, nullable=True),
        sa.Column("currency", sa.Text, nullable=True),
        sa.Column("overall_compliant", sa.Boolean, nullable=True),
        sa.Column("compliance_score", sa.Float, nullable=True),
        sa.Column("taxonomy_alignment_pct", sa.Float, nullable=True),
        sa.Column("dnsh_status", sa.Text, nullable=True),
        sa.Column("er_status", sa.Text, nullable=True),
        sa.Column("gbfs_completeness_pct", sa.Float, nullable=True),
        sa.Column("is_sovereign", sa.Boolean, nullable=True),
        sa.Column("blocking_gaps", JSONB, nullable=True),
        sa.Column("warnings", JSONB, nullable=True),
        sa.Column("environmental_objectives", JSONB, nullable=True),
        sa.Column("priority_actions", JSONB, nullable=True),
        sa.Column("standards_comparison", JSONB, nullable=True),
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
        "ix_eu_gbs_issuances_bond_id",
        "eu_gbs_issuances",
        ["bond_id"],
    )
    op.create_index(
        "ix_eu_gbs_issuances_issuer_name",
        "eu_gbs_issuances",
        ["issuer_name"],
    )

    # ------------------------------------------------------------------
    # E14 — EU GBS: eu_gbs_reports
    # ------------------------------------------------------------------
    op.create_table(
        "eu_gbs_reports",
        sa.Column(
            "id",
            sa.Text,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()::text"),
        ),
        sa.Column("bond_id", sa.Text, nullable=False),
        sa.Column("report_type", sa.Text, nullable=False),  # "allocation" | "impact"
        sa.Column("reporting_period", sa.Text, nullable=True),
        sa.Column("compliant", sa.Boolean, nullable=True),
        sa.Column("total_allocated_pct", sa.Float, nullable=True),
        sa.Column("taxonomy_aligned_pct", sa.Float, nullable=True),
        sa.Column("unallocated_pct", sa.Float, nullable=True),
        sa.Column("allocation_by_objective", JSONB, nullable=True),
        sa.Column("geographic_breakdown", JSONB, nullable=True),
        sa.Column("impact_indicators", JSONB, nullable=True),
        sa.Column("alignment_maintained", sa.Boolean, nullable=True),
        sa.Column("gaps", JSONB, nullable=True),
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
        sa.ForeignKeyConstraint(
            ["bond_id"],
            ["eu_gbs_issuances.bond_id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_eu_gbs_reports_bond_id",
        "eu_gbs_reports",
        ["bond_id"],
    )

    # ------------------------------------------------------------------
    # E15 — PRIIPs KID: priips_kid_records
    # ------------------------------------------------------------------
    op.create_table(
        "priips_kid_records",
        sa.Column(
            "id",
            sa.Text,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()::text"),
        ),
        sa.Column("kid_id", sa.Text, nullable=False, unique=True),
        sa.Column("product_id", sa.Text, nullable=False),
        sa.Column("product_name", sa.Text, nullable=False),
        sa.Column("product_type", sa.Text, nullable=True),
        sa.Column("isin", sa.Text, nullable=True),
        sa.Column("manufacturer", sa.Text, nullable=True),
        sa.Column("sfdr_classification", sa.Text, nullable=True),
        sa.Column("rhp_years", sa.Integer, nullable=True),
        sa.Column("annual_volatility", sa.Float, nullable=True),
        sa.Column("credit_quality", sa.Text, nullable=True),
        sa.Column("taxonomy_alignment_pct", sa.Float, nullable=True),
        # SRI
        sa.Column("market_risk_class", sa.Integer, nullable=True),
        sa.Column("credit_risk_class", sa.Integer, nullable=True),
        sa.Column("final_sri", sa.Integer, nullable=True),
        # Costs
        sa.Column("total_cost_pct", sa.Float, nullable=True),
        sa.Column("riy_pct", sa.Float, nullable=True),
        sa.Column("ongoing_cost_pct", sa.Float, nullable=True),
        # KID quality
        sa.Column("kid_completeness_pct", sa.Float, nullable=True),
        sa.Column("validation_gaps", JSONB, nullable=True),
        sa.Column("warnings", JSONB, nullable=True),
        # JSONB payloads
        sa.Column("performance_scenarios", JSONB, nullable=True),
        sa.Column("cost_summary", JSONB, nullable=True),
        sa.Column("cross_framework", JSONB, nullable=True),
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
        "ix_priips_kid_records_product_id",
        "priips_kid_records",
        ["product_id"],
    )
    op.create_index(
        "ix_priips_kid_records_isin",
        "priips_kid_records",
        ["isin"],
    )

    # ------------------------------------------------------------------
    # E15 — PRIIPs KID: priips_esg_inserts
    # ------------------------------------------------------------------
    op.create_table(
        "priips_esg_inserts",
        sa.Column(
            "id",
            sa.Text,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()::text"),
        ),
        sa.Column("kid_id", sa.Text, nullable=False),
        sa.Column("insert_type", sa.Text, nullable=False),
        sa.Column("required", sa.Boolean, nullable=True),
        sa.Column("sfdr_article", sa.Text, nullable=True),
        sa.Column("text_block", sa.Text, nullable=True),
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
        sa.ForeignKeyConstraint(
            ["kid_id"],
            ["priips_kid_records.kid_id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_priips_esg_inserts_kid_id",
        "priips_esg_inserts",
        ["kid_id"],
    )


def downgrade() -> None:
    op.drop_table("priips_esg_inserts")
    op.drop_table("priips_kid_records")
    op.drop_table("eu_gbs_reports")
    op.drop_table("eu_gbs_issuances")
    op.drop_table("tcfd_pillar_results")
    op.drop_table("tcfd_assessments")
    op.drop_table("mifid_preference_assessments")
