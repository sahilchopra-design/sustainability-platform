"""Add E28-E31 tables: ESRS E2-E5, Greenwashing Risk, Carbon Credit Quality, Climate Stress Test

Revision ID: 065
Revises: 064
Create Date: 2026-03-17

Tables created:
  esrs_e2_e5_assessments         — CSRD ESRS E2 Pollution / E3 Water / E4 Biodiversity / E5 Circular (E28)
  greenwashing_assessments       — EU Anti-Greenwashing / FCA substantiation assessment (E29)
  greenwashing_claim_results     — Per-claim scoring (FK soft ref to greenwashing_assessments) (E29)
  carbon_credit_quality_scores   — ICVCM CCP / VCS / Gold Standard quality scoring (E30)
  climate_stress_test_runs       — ECB/EBA climate stress test run records (E31)
  climate_stress_test_results    — Per-scenario/sector stress test outputs (E31)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "065"
down_revision = "064"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # E28 — CSRD ESRS E2-E5: esrs_e2_e5_assessments
    # ------------------------------------------------------------------
    op.create_table(
        "esrs_e2_e5_assessments",
        sa.Column("id", sa.Text, primary_key=True, server_default=sa.text("gen_random_uuid()::text")),
        sa.Column("assessment_id", sa.Text, nullable=False, unique=True),
        sa.Column("entity_id", sa.Text, nullable=False),
        sa.Column("entity_name", sa.Text, nullable=False),
        sa.Column("reporting_period", sa.Text, nullable=True),
        # E2 Pollution
        sa.Column("e2_material", sa.Boolean, nullable=True),
        sa.Column("e2_compliance_pct", sa.Float, nullable=True),
        sa.Column("e2_air_pollutants", JSONB, nullable=True),       # NOx, SOx, PM2.5, NMVOC
        sa.Column("e2_water_pollutants", JSONB, nullable=True),
        sa.Column("e2_soil_pollutants", JSONB, nullable=True),
        sa.Column("e2_substances_of_concern", JSONB, nullable=True),
        sa.Column("e2_disclosure_gaps", JSONB, nullable=True),
        # E3 Water & Marine
        sa.Column("e3_material", sa.Boolean, nullable=True),
        sa.Column("e3_compliance_pct", sa.Float, nullable=True),
        sa.Column("e3_water_withdrawal_m3", sa.Float, nullable=True),
        sa.Column("e3_water_discharge_m3", sa.Float, nullable=True),
        sa.Column("e3_water_consumption_m3", sa.Float, nullable=True),
        sa.Column("e3_water_stress_pct", sa.Float, nullable=True),  # % ops in water-stressed areas
        sa.Column("e3_water_intensity", sa.Float, nullable=True),
        sa.Column("e3_disclosure_gaps", JSONB, nullable=True),
        # E4 Biodiversity & Ecosystems
        sa.Column("e4_material", sa.Boolean, nullable=True),
        sa.Column("e4_compliance_pct", sa.Float, nullable=True),
        sa.Column("e4_sensitive_areas_pct", sa.Float, nullable=True),
        sa.Column("e4_land_use_change_ha", sa.Float, nullable=True),
        sa.Column("e4_species_affected", JSONB, nullable=True),
        sa.Column("e4_ecosystem_services_dep", JSONB, nullable=True),
        sa.Column("e4_disclosure_gaps", JSONB, nullable=True),
        # E5 Circular Economy
        sa.Column("e5_material", sa.Boolean, nullable=True),
        sa.Column("e5_compliance_pct", sa.Float, nullable=True),
        sa.Column("e5_material_inflows_t", sa.Float, nullable=True),
        sa.Column("e5_recycled_content_pct", sa.Float, nullable=True),
        sa.Column("e5_waste_generated_t", sa.Float, nullable=True),
        sa.Column("e5_circularity_rate_pct", sa.Float, nullable=True),
        sa.Column("e5_disclosure_gaps", JSONB, nullable=True),
        # Combined
        sa.Column("overall_compliance_pct", sa.Float, nullable=True),
        sa.Column("material_topics_count", sa.Integer, nullable=True),
        sa.Column("warnings", JSONB, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_esrs_e2_e5_assessments_entity_id", "esrs_e2_e5_assessments", ["entity_id"])

    # ------------------------------------------------------------------
    # E29 — Greenwashing Risk: greenwashing_assessments
    # ------------------------------------------------------------------
    op.create_table(
        "greenwashing_assessments",
        sa.Column("id", sa.Text, primary_key=True, server_default=sa.text("gen_random_uuid()::text")),
        sa.Column("assessment_id", sa.Text, nullable=False, unique=True),
        sa.Column("entity_id", sa.Text, nullable=False),
        sa.Column("entity_name", sa.Text, nullable=False),
        sa.Column("product_or_entity", sa.Text, nullable=True),     # product | entity_level
        sa.Column("claims_submitted", sa.Integer, nullable=True),
        sa.Column("claims_flagged", sa.Integer, nullable=True),
        sa.Column("overall_risk_score", sa.Float, nullable=True),
        sa.Column("risk_tier", sa.Text, nullable=True),             # low/medium/high/very_high
        sa.Column("eu_reg_2023_2441_score", sa.Float, nullable=True),
        sa.Column("fca_consumer_duty_score", sa.Float, nullable=True),
        sa.Column("substantiation_gaps", JSONB, nullable=True),
        sa.Column("misleading_terms_found", JSONB, nullable=True),
        sa.Column("label_verification", JSONB, nullable=True),      # SFDR/EU Taxonomy/SDR label checks
        sa.Column("remediation_steps", JSONB, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_greenwashing_assessments_entity_id", "greenwashing_assessments", ["entity_id"])

    # E29 — Per-claim results
    op.create_table(
        "greenwashing_claim_results",
        sa.Column("id", sa.Text, primary_key=True, server_default=sa.text("gen_random_uuid()::text")),
        sa.Column("assessment_id", sa.Text, nullable=False),        # soft ref to greenwashing_assessments
        sa.Column("claim_text", sa.Text, nullable=True),
        sa.Column("claim_type", sa.Text, nullable=True),            # quantitative/qualitative/label/comparative
        sa.Column("risk_level", sa.Text, nullable=True),            # low/medium/high
        sa.Column("substantiation_score", sa.Float, nullable=True),
        sa.Column("issues_found", JSONB, nullable=True),
        sa.Column("regulatory_refs", JSONB, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_greenwashing_claim_results_assessment_id", "greenwashing_claim_results", ["assessment_id"])

    # ------------------------------------------------------------------
    # E30 — Carbon Credit Quality: carbon_credit_quality_scores
    # ------------------------------------------------------------------
    op.create_table(
        "carbon_credit_quality_scores",
        sa.Column("id", sa.Text, primary_key=True, server_default=sa.text("gen_random_uuid()::text")),
        sa.Column("score_id", sa.Text, nullable=False, unique=True),
        sa.Column("entity_id", sa.Text, nullable=False),
        sa.Column("project_id", sa.Text, nullable=True),
        sa.Column("project_name", sa.Text, nullable=True),
        sa.Column("standard", sa.Text, nullable=True),              # vcs/gold_standard/cdm/art6/ccp
        sa.Column("methodology", sa.Text, nullable=True),
        sa.Column("project_type", sa.Text, nullable=True),          # avoidance/removal/reduction
        sa.Column("vintage_year", sa.Integer, nullable=True),
        sa.Column("volume_tco2e", sa.Float, nullable=True),
        sa.Column("ccp_label", sa.Boolean, nullable=True),          # ICVCM CCP label
        sa.Column("additionality_score", sa.Float, nullable=True),  # 0-100
        sa.Column("permanence_risk_score", sa.Float, nullable=True),
        sa.Column("co_benefits_score", sa.Float, nullable=True),
        sa.Column("overall_quality_score", sa.Float, nullable=True),
        sa.Column("quality_tier", sa.Text, nullable=True),          # A/B/C/D
        sa.Column("corsia_eligible", sa.Boolean, nullable=True),
        sa.Column("article6_eligible", sa.Boolean, nullable=True),
        sa.Column("price_range_usd", JSONB, nullable=True),         # min/mid/max
        sa.Column("issues", JSONB, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_carbon_credit_quality_scores_entity_id", "carbon_credit_quality_scores", ["entity_id"])
    op.create_index("ix_carbon_credit_quality_scores_standard", "carbon_credit_quality_scores", ["standard"])

    # ------------------------------------------------------------------
    # E31 — Climate Stress Test: climate_stress_test_runs
    # ------------------------------------------------------------------
    op.create_table(
        "climate_stress_test_runs",
        sa.Column("id", sa.Text, primary_key=True, server_default=sa.text("gen_random_uuid()::text")),
        sa.Column("run_id", sa.Text, nullable=False, unique=True),
        sa.Column("entity_id", sa.Text, nullable=False),
        sa.Column("entity_name", sa.Text, nullable=False),
        sa.Column("framework", sa.Text, nullable=True),             # ecb_2022/eba_2023/boe_cs2/custom
        sa.Column("scenarios", JSONB, nullable=True),               # list of scenario IDs used
        sa.Column("time_horizon", sa.Text, nullable=True),          # short/medium/long
        sa.Column("loan_book_bn", sa.Float, nullable=True),
        sa.Column("total_exposure_bn", sa.Float, nullable=True),
        sa.Column("baseline_cet1_pct", sa.Float, nullable=True),
        sa.Column("stressed_cet1_pct", sa.Float, nullable=True),
        sa.Column("cet1_depletion_bps", sa.Float, nullable=True),
        sa.Column("total_credit_losses_bn", sa.Float, nullable=True),
        sa.Column("total_impairment_pct", sa.Float, nullable=True),
        sa.Column("worst_scenario", sa.Text, nullable=True),
        sa.Column("climate_var_pct", sa.Float, nullable=True),
        sa.Column("summary_results", JSONB, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_climate_stress_test_runs_entity_id", "climate_stress_test_runs", ["entity_id"])

    # E31 — Per-scenario/sector results
    op.create_table(
        "climate_stress_test_results",
        sa.Column("id", sa.Text, primary_key=True, server_default=sa.text("gen_random_uuid()::text")),
        sa.Column("run_id", sa.Text, nullable=False),               # soft ref to climate_stress_test_runs
        sa.Column("scenario_id", sa.Text, nullable=False),
        sa.Column("nace_sector", sa.Text, nullable=True),
        sa.Column("exposure_bn", sa.Float, nullable=True),
        sa.Column("pd_migration_bps", sa.Float, nullable=True),     # PD increase in bps
        sa.Column("lgd_uplift_pct", sa.Float, nullable=True),
        sa.Column("expected_loss_bn", sa.Float, nullable=True),
        sa.Column("collateral_haircut_pct", sa.Float, nullable=True),
        sa.Column("stranded_asset_pct", sa.Float, nullable=True),
        sa.Column("carbon_cost_impact_mn", sa.Float, nullable=True),
        sa.Column("revenue_impact_pct", sa.Float, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_climate_stress_test_results_run_id", "climate_stress_test_results", ["run_id"])


def downgrade() -> None:
    op.drop_table("climate_stress_test_results")
    op.drop_table("climate_stress_test_runs")
    op.drop_table("carbon_credit_quality_scores")
    op.drop_table("greenwashing_claim_results")
    op.drop_table("greenwashing_assessments")
    op.drop_table("esrs_e2_e5_assessments")
