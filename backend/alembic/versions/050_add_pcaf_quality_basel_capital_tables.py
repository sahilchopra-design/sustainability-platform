"""Add PCAF Quality Score and Basel III/IV Capital tables

Revision ID: 050
Revises: 049
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "050"
down_revision = "049"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── PCAF Data Quality Score ──────────────────────────────────────────────

    op.create_table(
        "pcaf_holding_quality_scores",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("holding_id", sa.String(100), nullable=False),
        sa.Column("entity_name", sa.String(255), nullable=False),
        sa.Column("asset_class", sa.String(50), nullable=False),
        sa.Column("outstanding_amount_eur", sa.Float, default=0.0),
        sa.Column("dqs_emissions", sa.Integer, default=5),
        sa.Column("dqs_completeness", sa.Integer, default=5),
        sa.Column("dqs_timeliness", sa.Integer, default=5),
        sa.Column("dqs_granularity", sa.Integer, default=5),
        sa.Column("dqs_methodology", sa.Integer, default=5),
        sa.Column("weighted_dqs", sa.Float, default=5.0),
        sa.Column("confidence_weight", sa.Float, default=0.2),
        sa.Column("estimated_emissions_tco2", sa.Float, default=0.0),
        sa.Column("attribution_factor", sa.Float, default=0.0),
        sa.Column("financed_emissions_tco2", sa.Float, default=0.0),
        sa.Column("data_gaps", JSONB, nullable=True),
        sa.Column("improvement_actions", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "pcaf_portfolio_quality_reports",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("portfolio_id", sa.String(100), nullable=False),
        sa.Column("portfolio_name", sa.String(255), nullable=False),
        sa.Column("reporting_year", sa.Integer, nullable=False),
        sa.Column("total_holdings", sa.Integer, default=0),
        sa.Column("scored_holdings", sa.Integer, default=0),
        sa.Column("portfolio_weighted_dqs", sa.Float, default=5.0),
        sa.Column("dqs_distribution", JSONB, nullable=True),
        sa.Column("total_financed_emissions_tco2", sa.Float, default=0.0),
        sa.Column("total_outstanding_eur", sa.Float, default=0.0),
        sa.Column("carbon_intensity_tco2_per_meur", sa.Float, default=0.0),
        sa.Column("asset_class_breakdown", JSONB, nullable=True),
        sa.Column("quality_improvement_roadmap", JSONB, nullable=True),
        sa.Column("sfdr_pai_indicators", JSONB, nullable=True),
        sa.Column("cross_framework_disclosures", JSONB, nullable=True),
        sa.Column("confidence_band", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "pcaf_data_quality_assessments",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("entity_name", sa.String(255), nullable=False),
        sa.Column("reporting_year", sa.Integer, nullable=False),
        sa.Column("dimension_scores", JSONB, nullable=True),
        sa.Column("overall_dqs", sa.Integer, default=5),
        sa.Column("weighted_dqs", sa.Float, default=5.0),
        sa.Column("improvement_priority", sa.String(100), nullable=True),
        sa.Column("gap_analysis", JSONB, nullable=True),
        sa.Column("benchmark_comparison", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # ── Basel III/IV Regulatory Capital ───────────────────────────────────────

    op.create_table(
        "basel_capital_requirements",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("entity_name", sa.String(255), nullable=False),
        sa.Column("reporting_date", sa.Date, nullable=False),
        sa.Column("approach", sa.String(30), default="standardised"),
        sa.Column("total_rwa_credit", sa.Float, default=0.0),
        sa.Column("total_rwa_market", sa.Float, default=0.0),
        sa.Column("total_rwa_operational", sa.Float, default=0.0),
        sa.Column("total_rwa", sa.Float, default=0.0),
        sa.Column("cet1_capital", sa.Float, default=0.0),
        sa.Column("at1_capital", sa.Float, default=0.0),
        sa.Column("tier1_capital", sa.Float, default=0.0),
        sa.Column("tier2_capital", sa.Float, default=0.0),
        sa.Column("total_capital", sa.Float, default=0.0),
        sa.Column("cet1_ratio", sa.Float, default=0.0),
        sa.Column("tier1_ratio", sa.Float, default=0.0),
        sa.Column("total_capital_ratio", sa.Float, default=0.0),
        sa.Column("leverage_ratio", sa.Float, default=0.0),
        sa.Column("capital_conservation_buffer", sa.Float, default=0.025),
        sa.Column("countercyclical_buffer", sa.Float, default=0.0),
        sa.Column("systemic_buffer", sa.Float, default=0.0),
        sa.Column("combined_buffer_requirement", sa.Float, default=0.025),
        sa.Column("cet1_surplus_deficit", sa.Float, default=0.0),
        sa.Column("tier1_surplus_deficit", sa.Float, default=0.0),
        sa.Column("total_surplus_deficit", sa.Float, default=0.0),
        sa.Column("climate_rwa_addon", sa.Float, default=0.0),
        sa.Column("exposure_class_breakdown", JSONB, nullable=True),
        sa.Column("regulatory_breaches", JSONB, nullable=True),
        sa.Column("recommendations", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "basel_liquidity_assessments",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("entity_name", sa.String(255), nullable=False),
        sa.Column("reporting_date", sa.Date, nullable=False),
        sa.Column("hqla_total", sa.Float, default=0.0),
        sa.Column("total_net_cash_outflows", sa.Float, default=0.0),
        sa.Column("lcr_ratio", sa.Float, default=0.0),
        sa.Column("lcr_compliant", sa.Boolean, default=False),
        sa.Column("available_stable_funding", sa.Float, default=0.0),
        sa.Column("required_stable_funding", sa.Float, default=0.0),
        sa.Column("nsfr_ratio", sa.Float, default=0.0),
        sa.Column("nsfr_compliant", sa.Boolean, default=False),
        sa.Column("hqla_composition", JSONB, nullable=True),
        sa.Column("lcr_stress_scenarios", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "basel_capital_adequacy_dashboard",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("entity_name", sa.String(255), nullable=False),
        sa.Column("reporting_date", sa.Date, nullable=False),
        sa.Column("capital_requirement_id", sa.String(64), nullable=True),
        sa.Column("liquidity_id", sa.String(64), nullable=True),
        sa.Column("climate_stress_impact", JSONB, nullable=True),
        sa.Column("bcbs239_compliance_score", sa.Float, default=0.0),
        sa.Column("pillar2_recommendations", JSONB, nullable=True),
        sa.Column("overall_rag_status", sa.String(10), default="RED"),
        sa.Column("cross_framework_mapping", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("basel_capital_adequacy_dashboard")
    op.drop_table("basel_liquidity_assessments")
    op.drop_table("basel_capital_requirements")
    op.drop_table("pcaf_data_quality_assessments")
    op.drop_table("pcaf_portfolio_quality_reports")
    op.drop_table("pcaf_holding_quality_scores")
