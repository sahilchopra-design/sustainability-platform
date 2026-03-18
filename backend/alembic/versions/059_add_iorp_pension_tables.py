"""Add IORP II pension climate risk tables (E8)

Revision ID: 059
Revises: 058c_postgis_views_final
Create Date: 2026-03-17

Tables:
  iorp_stress_runs       — top-level IORP II stress assessment run
  iorp_scenario_results  — per-scenario stress results (assets, liabilities, funding ratio)
  iorp_ora_results       — per-item ORA Art 28 checklist results
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "059"
down_revision = "058c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. iorp_stress_runs
    # ------------------------------------------------------------------
    op.create_table(
        "iorp_stress_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("fund_id", sa.Text, nullable=False),
        sa.Column("fund_name", sa.Text, nullable=False),
        sa.Column("iorp_type", sa.Text, nullable=False),
        sa.Column("member_count", sa.Integer),
        sa.Column("country_iso3", sa.CHAR(3)),
        sa.Column("reporting_currency", sa.CHAR(3)),

        # Balance sheet snapshot
        sa.Column("total_assets_eur", sa.Numeric(20, 2)),
        sa.Column("liabilities_eur", sa.Numeric(20, 2)),
        sa.Column("liability_duration_y", sa.Numeric(6, 2)),

        # Asset allocation snapshot (%)
        sa.Column("equity_pct", sa.Numeric(6, 2)),
        sa.Column("sovereign_bonds_pct", sa.Numeric(6, 2)),
        sa.Column("corp_bonds_ig_pct", sa.Numeric(6, 2)),
        sa.Column("corp_bonds_hy_pct", sa.Numeric(6, 2)),
        sa.Column("real_estate_pct", sa.Numeric(6, 2)),
        sa.Column("infrastructure_pct", sa.Numeric(6, 2)),

        # Headline results
        sa.Column("pre_stress_funding_ratio_pct", sa.Numeric(8, 2)),
        sa.Column("worst_case_scenario_id", sa.Text),
        sa.Column("worst_case_funding_ratio_drop_pct", sa.Numeric(8, 2)),
        sa.Column("sfdr_classification", sa.Text),
        sa.Column("ora_compliance_status", sa.Text),
        sa.Column("ora_items_met", sa.Integer),
        sa.Column("ora_items_gap", sa.Integer),
        sa.Column("ora_blocking_gaps", postgresql.JSONB),

        # Misc
        sa.Column("scenarios_run", sa.Integer),
        sa.Column("recommendations", postgresql.JSONB),
        sa.Column("assessment_date", sa.Date),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()")),
    )
    op.create_index("ix_iorp_stress_runs_fund_id", "iorp_stress_runs", ["fund_id"])
    op.create_index("ix_iorp_stress_runs_assessment_date", "iorp_stress_runs", ["assessment_date"])

    # ------------------------------------------------------------------
    # 2. iorp_scenario_results
    # ------------------------------------------------------------------
    op.create_table(
        "iorp_scenario_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("run_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("iorp_stress_runs.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("scenario_id", sa.Text, nullable=False),
        sa.Column("scenario_label", sa.Text),

        # Asset stress
        sa.Column("equity_loss_eur", sa.Numeric(20, 2)),
        sa.Column("sovereign_bond_loss_eur", sa.Numeric(20, 2)),
        sa.Column("corp_ig_loss_eur", sa.Numeric(20, 2)),
        sa.Column("corp_hy_loss_eur", sa.Numeric(20, 2)),
        sa.Column("real_estate_loss_eur", sa.Numeric(20, 2)),
        sa.Column("infrastructure_loss_eur", sa.Numeric(20, 2)),
        sa.Column("total_asset_loss_eur", sa.Numeric(20, 2)),
        sa.Column("stressed_assets_eur", sa.Numeric(20, 2)),

        # Liability stress
        sa.Column("discount_rate_shift_bps", sa.Numeric(8, 1)),
        sa.Column("liability_duration_impact_eur", sa.Numeric(20, 2)),
        sa.Column("longevity_shock_eur", sa.Numeric(20, 2)),
        sa.Column("inflation_liability_uplift_eur", sa.Numeric(20, 2)),
        sa.Column("total_liability_change_eur", sa.Numeric(20, 2)),
        sa.Column("stressed_liabilities_eur", sa.Numeric(20, 2)),

        # Funding ratio
        sa.Column("pre_stress_ratio_pct", sa.Numeric(8, 2)),
        sa.Column("post_stress_ratio_pct", sa.Numeric(8, 2)),
        sa.Column("ratio_change_pct", sa.Numeric(8, 2)),
        sa.Column("triggers_recovery_plan", sa.Boolean, server_default="false"),
        sa.Column("triggers_supervisory_review", sa.Boolean, server_default="false"),
        sa.Column("sponsor_covenant_buffer_eur", sa.Numeric(20, 2)),

        # Composite
        sa.Column("net_stress_impact_eur", sa.Numeric(20, 2)),
        sa.Column("member_benefit_erosion_pct", sa.Numeric(8, 2)),
    )
    op.create_index("ix_iorp_scenario_results_run_id", "iorp_scenario_results", ["run_id"])
    op.create_index("ix_iorp_scenario_results_scenario_id", "iorp_scenario_results", ["scenario_id"])

    # ------------------------------------------------------------------
    # 3. iorp_ora_results
    # ------------------------------------------------------------------
    op.create_table(
        "iorp_ora_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("run_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("iorp_stress_runs.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("item_id", sa.Text, nullable=False),     # ORA-01..ORA-12
        sa.Column("title", sa.Text),
        sa.Column("article", sa.Text),
        sa.Column("blocking", sa.Boolean),
        sa.Column("met", sa.Boolean),
        sa.Column("status", sa.Text),                      # met | gap
    )
    op.create_index("ix_iorp_ora_results_run_id", "iorp_ora_results", ["run_id"])


def downgrade() -> None:
    op.drop_table("iorp_ora_results")
    op.drop_table("iorp_scenario_results")
    op.drop_table("iorp_stress_runs")
