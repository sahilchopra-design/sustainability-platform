"""Add SEC Climate Disclosure and GRI Standards tables

Revision ID: 047
Revises: 046
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "047"
down_revision = "046"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── SEC Climate Disclosure ────────────────────────────────────────────

    op.create_table(
        "sec_filer_assessments",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("registrant_name", sa.String(255), nullable=False),
        sa.Column("cik", sa.String(20), nullable=True),
        sa.Column("filer_category", sa.String(50), nullable=False),
        sa.Column("fiscal_year", sa.Integer, nullable=False),
        sa.Column("ghg_disclosure_required", sa.Boolean, default=False),
        sa.Column("ghg_disclosure_start_fy", sa.Integer, nullable=True),
        sa.Column("assurance_required", sa.Boolean, default=False),
        sa.Column("assurance_level", sa.String(30), nullable=True),
        sa.Column("assurance_start_fy", sa.Integer, nullable=True),
        sa.Column("financial_effects_required", sa.Boolean, default=True),
        sa.Column("item_compliance", JSONB, nullable=True),
        sa.Column("overall_compliance_pct", sa.Float, default=0.0),
        sa.Column("gaps", JSONB, nullable=True),
        sa.Column("critical_gaps", sa.Integer, default=0),
        sa.Column("recommendations", JSONB, nullable=True),
        sa.Column("safe_harbor_items", JSONB, nullable=True),
        sa.Column("cross_framework_mapping", JSONB, nullable=True),
        sa.Column("attestation_status", JSONB, nullable=True),
        sa.Column("notes", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "sec_ghg_disclosures",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("registrant_name", sa.String(255), nullable=False),
        sa.Column("fiscal_year", sa.Integer, nullable=False),
        sa.Column("scope_1_total_co2e_mt", sa.Float, default=0.0),
        sa.Column("scope_1_by_gas", JSONB, nullable=True),
        sa.Column("scope_1_methodology", sa.String(100), nullable=True),
        sa.Column("scope_2_location_co2e_mt", sa.Float, default=0.0),
        sa.Column("scope_2_market_co2e_mt", sa.Float, default=0.0),
        sa.Column("scope_2_methodology", sa.String(100), nullable=True),
        sa.Column("org_boundary", sa.String(50), nullable=True),
        sa.Column("operational_boundary", sa.String(50), nullable=True),
        sa.Column("consolidation_approach", sa.String(50), nullable=True),
        sa.Column("prior_year_scope_1", sa.Float, default=0.0),
        sa.Column("prior_year_scope_2", sa.Float, default=0.0),
        sa.Column("yoy_change_scope_1_pct", sa.Float, default=0.0),
        sa.Column("yoy_change_scope_2_pct", sa.Float, default=0.0),
        sa.Column("intensity_metric", sa.String(50), nullable=True),
        sa.Column("intensity_value", sa.Float, default=0.0),
        sa.Column("attestation_readiness_score", sa.Float, default=0.0),
        sa.Column("attestation_gaps", JSONB, nullable=True),
        sa.Column("data_quality_score", sa.Float, default=0.0),
        sa.Column("data_quality_notes", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "sec_financial_effects",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("registrant_name", sa.String(255), nullable=False),
        sa.Column("fiscal_year", sa.Integer, nullable=False),
        sa.Column("pre_tax_income_usd", sa.Float, default=0.0),
        sa.Column("total_equity_usd", sa.Float, default=0.0),
        sa.Column("materiality_threshold_usd", sa.Float, default=0.0),
        sa.Column("severe_weather_losses_usd", sa.Float, default=0.0),
        sa.Column("severe_weather_material", sa.Boolean, default=False),
        sa.Column("severe_weather_events", JSONB, nullable=True),
        sa.Column("transition_expenses_usd", sa.Float, default=0.0),
        sa.Column("transition_capex_usd", sa.Float, default=0.0),
        sa.Column("transition_material", sa.Boolean, default=False),
        sa.Column("transition_details", JSONB, nullable=True),
        sa.Column("climate_impairments_usd", sa.Float, default=0.0),
        sa.Column("climate_contingencies_usd", sa.Float, default=0.0),
        sa.Column("estimates_material", sa.Boolean, default=False),
        sa.Column("estimate_details", JSONB, nullable=True),
        sa.Column("total_climate_financial_impact_usd", sa.Float, default=0.0),
        sa.Column("disclosure_required", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "sec_materiality_assessments",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("registrant_name", sa.String(255), nullable=False),
        sa.Column("fiscal_year", sa.Integer, nullable=False),
        sa.Column("material_physical_risks", JSONB, nullable=True),
        sa.Column("material_transition_risks", JSONB, nullable=True),
        sa.Column("immaterial_risks", JSONB, nullable=True),
        sa.Column("total_risks_assessed", sa.Integer, default=0),
        sa.Column("material_count", sa.Integer, default=0),
        sa.Column("time_horizons", JSONB, nullable=True),
        sa.Column("strategy_impact", JSONB, nullable=True),
        sa.Column("scenario_analysis_used", sa.Boolean, default=False),
        sa.Column("internal_carbon_price", sa.Float, nullable=True),
        sa.Column("notes", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # ── GRI Standards ─────────────────────────────────────────────────────

    op.create_table(
        "gri_content_index_assessments",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("entity_name", sa.String(255), nullable=False),
        sa.Column("reporting_period", sa.String(20), nullable=False),
        sa.Column("gri_compliance_level", sa.String(30), nullable=True),
        sa.Column("total_applicable_disclosures", sa.Integer, default=0),
        sa.Column("total_reported", sa.Integer, default=0),
        sa.Column("total_partially_reported", sa.Integer, default=0),
        sa.Column("total_omitted", sa.Integer, default=0),
        sa.Column("completeness_pct", sa.Float, default=0.0),
        sa.Column("by_category", JSONB, nullable=True),
        sa.Column("disclosure_index", JSONB, nullable=True),
        sa.Column("material_topics", JSONB, nullable=True),
        sa.Column("omission_reasons", JSONB, nullable=True),
        sa.Column("sdg_linkage", JSONB, nullable=True),
        sa.Column("esrs_mapping", JSONB, nullable=True),
        sa.Column("recommendations", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "gri_emissions_disclosures",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("entity_name", sa.String(255), nullable=False),
        sa.Column("reporting_period", sa.String(20), nullable=False),
        sa.Column("scope_1_co2e_mt", sa.Float, default=0.0),
        sa.Column("scope_1_biogenic_co2_mt", sa.Float, default=0.0),
        sa.Column("scope_1_base_year", sa.String(10), nullable=True),
        sa.Column("scope_2_location_co2e_mt", sa.Float, default=0.0),
        sa.Column("scope_2_market_co2e_mt", sa.Float, default=0.0),
        sa.Column("scope_3_co2e_mt", sa.Float, default=0.0),
        sa.Column("scope_3_categories_reported", JSONB, nullable=True),
        sa.Column("ghg_intensity", sa.Float, default=0.0),
        sa.Column("ghg_intensity_denominator", sa.String(50), nullable=True),
        sa.Column("reductions_co2e_mt", sa.Float, default=0.0),
        sa.Column("reduction_initiatives", JSONB, nullable=True),
        sa.Column("ods_tonnes_cfc11eq", sa.Float, default=0.0),
        sa.Column("nox_tonnes", sa.Float, default=0.0),
        sa.Column("sox_tonnes", sa.Float, default=0.0),
        sa.Column("pm_tonnes", sa.Float, default=0.0),
        sa.Column("disclosure_completeness", JSONB, nullable=True),
        sa.Column("completeness_pct", sa.Float, default=0.0),
        sa.Column("gaps", JSONB, nullable=True),
        sa.Column("methodology_notes", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "gri_material_topic_assessments",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("entity_name", sa.String(255), nullable=False),
        sa.Column("topic_standard", sa.String(10), nullable=False),
        sa.Column("topic_title", sa.String(100), nullable=True),
        sa.Column("material", sa.Boolean, default=True),
        sa.Column("stakeholders_impacted", JSONB, nullable=True),
        sa.Column("boundary", sa.String(100), nullable=True),
        sa.Column("management_approach_score", sa.Float, default=0.0),
        sa.Column("disclosure_completeness_pct", sa.Float, default=0.0),
        sa.Column("disclosures_reported", JSONB, nullable=True),
        sa.Column("disclosures_omitted", JSONB, nullable=True),
        sa.Column("sdg_linkage", JSONB, nullable=True),
        sa.Column("esrs_equivalent", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("gri_material_topic_assessments")
    op.drop_table("gri_emissions_disclosures")
    op.drop_table("gri_content_index_assessments")
    op.drop_table("sec_materiality_assessments")
    op.drop_table("sec_financial_effects")
    op.drop_table("sec_ghg_disclosures")
    op.drop_table("sec_filer_assessments")
