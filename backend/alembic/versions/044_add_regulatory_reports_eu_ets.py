"""Add regulatory report compilations + EU ETS tables

Revision ID: 044
Revises: 043
Create Date: 2026-03-09

New tables:
1. compiled_regulatory_reports — persists compiled report outputs
2. compiled_report_sections — individual sections with completeness tracking
3. eu_ets_installations — installation registry for EU ETS
4. eu_ets_allocations — free allocation calculations
5. eu_ets_compliance — compliance positions per year
6. eu_ets_price_forecasts — carbon price forecast results
7. brsr_entity_disclosures — BRSR/BRSR Core disclosure tracking (India-specific)

Indexes for common join paths + updated_at trigger.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "044"
down_revision = "043"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Compiled Regulatory Reports ──────────────────────────────────
    op.create_table(
        "compiled_regulatory_reports",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_profile_id", UUID(as_uuid=True), nullable=True),
        sa.Column("report_id", sa.String(100), nullable=False),
        sa.Column("framework", sa.String(30), nullable=False),
        sa.Column("entity_name", sa.String(200)),
        sa.Column("reporting_period_start", sa.Date),
        sa.Column("reporting_period_end", sa.Date),
        sa.Column("compilation_date", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("overall_completeness_pct", sa.Numeric(6, 2)),
        sa.Column("overall_status", sa.String(20), server_default="draft"),
        sa.Column("summary", JSONB),
        sa.Column("gaps_summary", JSONB),
        sa.Column("recommendations", JSONB),
        sa.Column("metadata", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        # FK
        sa.ForeignKeyConstraint(["company_profile_id"], ["company_profiles.id"],
                                name="fk_compiled_report_company_profile", ondelete="SET NULL"),
    )
    op.create_index("ix_crr_framework", "compiled_regulatory_reports", ["framework"])
    op.create_index("ix_crr_report_id", "compiled_regulatory_reports", ["report_id"])
    op.create_index("ix_crr_cp", "compiled_regulatory_reports", ["company_profile_id"])
    op.create_index("ix_crr_status", "compiled_regulatory_reports", ["overall_status"])

    # ── 2. Compiled Report Sections ─────────────────────────────────────
    op.create_table(
        "compiled_report_sections",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("report_id", UUID(as_uuid=True), nullable=False),
        sa.Column("section_id", sa.String(30), nullable=False),
        sa.Column("title", sa.String(200)),
        sa.Column("framework", sa.String(30)),
        sa.Column("status", sa.String(20), server_default="incomplete"),
        sa.Column("completeness_pct", sa.Numeric(6, 2)),
        sa.Column("disclosures", JSONB),
        sa.Column("narrative", sa.Text),
        sa.Column("data_points", JSONB),
        sa.Column("gaps", JSONB),
        sa.Column("sources", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        # FK
        sa.ForeignKeyConstraint(["report_id"], ["compiled_regulatory_reports.id"],
                                name="fk_report_section_report", ondelete="CASCADE"),
    )
    op.create_index("ix_crs_report", "compiled_report_sections", ["report_id"])
    op.create_index("ix_crs_section", "compiled_report_sections", ["section_id"])

    # ── 3. EU ETS Installations ─────────────────────────────────────────
    op.create_table(
        "eu_ets_installations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_profile_id", UUID(as_uuid=True), nullable=True),
        sa.Column("installation_id", sa.String(50), nullable=False, unique=True),
        sa.Column("installation_name", sa.String(200)),
        sa.Column("sector", sa.String(50)),
        sa.Column("country", sa.String(3)),
        sa.Column("product_benchmark", sa.String(50)),
        sa.Column("carbon_leakage_listed", sa.Boolean, server_default="true"),
        sa.Column("nace_code", sa.String(10)),
        sa.Column("permit_id", sa.String(50)),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        # FK
        sa.ForeignKeyConstraint(["company_profile_id"], ["company_profiles.id"],
                                name="fk_ets_inst_company_profile", ondelete="SET NULL"),
    )
    op.create_index("ix_ets_inst_id", "eu_ets_installations", ["installation_id"])
    op.create_index("ix_ets_inst_sector", "eu_ets_installations", ["sector"])
    op.create_index("ix_ets_inst_cp", "eu_ets_installations", ["company_profile_id"])

    # ── 4. EU ETS Allocations ───────────────────────────────────────────
    op.create_table(
        "eu_ets_allocations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("installation_id", sa.String(50), nullable=False),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("historical_activity_level", sa.Numeric(14, 2)),
        sa.Column("benchmark_value", sa.Numeric(10, 6)),
        sa.Column("preliminary_allocation_tco2", sa.Numeric(14, 2)),
        sa.Column("carbon_leakage_factor", sa.Numeric(6, 4)),
        sa.Column("cross_sectoral_correction", sa.Numeric(6, 4)),
        sa.Column("cbam_reduction_factor", sa.Numeric(6, 4)),
        sa.Column("final_allocation_tco2", sa.Numeric(14, 2)),
        sa.Column("auction_exposure_tco2", sa.Numeric(14, 2)),
        sa.Column("auction_cost_eur", sa.Numeric(16, 2)),
        sa.Column("carbon_price_eur", sa.Numeric(10, 2)),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_ets_alloc_inst_year", "eu_ets_allocations",
                    ["installation_id", "year"], unique=True)

    # ── 5. EU ETS Compliance ────────────────────────────────────────────
    op.create_table(
        "eu_ets_compliance",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("installation_id", sa.String(50), nullable=False),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("verified_emissions_tco2", sa.Numeric(14, 2)),
        sa.Column("free_allocation_tco2", sa.Numeric(14, 2)),
        sa.Column("purchased_allowances_tco2", sa.Numeric(14, 2)),
        sa.Column("banked_allowances_tco2", sa.Numeric(14, 2)),
        sa.Column("total_holdings_tco2", sa.Numeric(14, 2)),
        sa.Column("surrender_obligation_tco2", sa.Numeric(14, 2)),
        sa.Column("surplus_deficit_tco2", sa.Numeric(14, 2)),
        sa.Column("compliance_status", sa.String(20)),
        sa.Column("estimated_purchase_cost_eur", sa.Numeric(16, 2)),
        sa.Column("penalty_exposure_eur", sa.Numeric(16, 2)),
        sa.Column("carbon_price_eur", sa.Numeric(10, 2)),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_ets_comp_inst_year", "eu_ets_compliance",
                    ["installation_id", "year"], unique=True)
    op.create_index("ix_ets_comp_status", "eu_ets_compliance", ["compliance_status"])

    # ── 6. EU ETS Price Forecasts ───────────────────────────────────────
    op.create_table(
        "eu_ets_price_forecasts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("scenario", sa.String(30), nullable=False),
        sa.Column("base_price_eur", sa.Numeric(10, 2)),
        sa.Column("price_2030_eur", sa.Numeric(10, 2)),
        sa.Column("price_2050_eur", sa.Numeric(10, 2)),
        sa.Column("cagr_pct", sa.Numeric(6, 3)),
        sa.Column("volatility_annual_pct", sa.Numeric(6, 3)),
        sa.Column("prices_by_year", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_ets_pf_scenario", "eu_ets_price_forecasts", ["scenario"])

    # ── 7. BRSR Entity Disclosures ──────────────────────────────────────
    op.create_table(
        "brsr_entity_disclosures",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_profile_id", UUID(as_uuid=True), nullable=True),
        sa.Column("entity_name", sa.String(200), nullable=False),
        sa.Column("cin", sa.String(25)),
        sa.Column("financial_year", sa.String(10)),
        # BRSR Core completeness
        sa.Column("brsr_core_completeness_pct", sa.Numeric(6, 2)),
        sa.Column("brsr_full_completeness_pct", sa.Numeric(6, 2)),
        # BRSR Core attribute scores (9 attributes)
        sa.Column("core_ghg_score_pct", sa.Numeric(6, 2)),
        sa.Column("core_water_score_pct", sa.Numeric(6, 2)),
        sa.Column("core_energy_score_pct", sa.Numeric(6, 2)),
        sa.Column("core_waste_score_pct", sa.Numeric(6, 2)),
        sa.Column("core_employee_safety_score_pct", sa.Numeric(6, 2)),
        sa.Column("core_gender_diversity_score_pct", sa.Numeric(6, 2)),
        sa.Column("core_inclusive_dev_score_pct", sa.Numeric(6, 2)),
        sa.Column("core_customer_fairness_score_pct", sa.Numeric(6, 2)),
        sa.Column("core_openness_score_pct", sa.Numeric(6, 2)),
        # Principle-level scores
        sa.Column("principle_scores", JSONB),
        # GRI/ESRS mapping coverage
        sa.Column("gri_mapped_count", sa.Integer),
        sa.Column("esrs_mapped_count", sa.Integer),
        # Full data
        sa.Column("section_a_data", JSONB),
        sa.Column("section_b_data", JSONB),
        sa.Column("section_c_data", JSONB),
        sa.Column("brsr_core_data", JSONB),
        sa.Column("recommendations", JSONB),
        # Assurance
        sa.Column("assurance_provider", sa.String(200)),
        sa.Column("assurance_type", sa.String(30)),
        # Audit
        sa.Column("assessed_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        # FK
        sa.ForeignKeyConstraint(["company_profile_id"], ["company_profiles.id"],
                                name="fk_brsr_disc_company_profile", ondelete="SET NULL"),
    )
    op.create_index("ix_brsr_disc_cp", "brsr_entity_disclosures", ["company_profile_id"])
    op.create_index("ix_brsr_disc_fy", "brsr_entity_disclosures", ["financial_year"])
    op.create_index("ix_brsr_disc_cin", "brsr_entity_disclosures", ["cin"])


def downgrade() -> None:
    op.drop_table("brsr_entity_disclosures")
    op.drop_table("eu_ets_price_forecasts")
    op.drop_table("eu_ets_compliance")
    op.drop_table("eu_ets_allocations")
    op.drop_table("eu_ets_installations")
    op.drop_table("compiled_report_sections")
    op.drop_table("compiled_regulatory_reports")
