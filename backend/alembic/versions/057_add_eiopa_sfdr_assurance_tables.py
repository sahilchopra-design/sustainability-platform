"""Add EIOPA stress, SFDR annex, and assurance readiness tables

Revision ID: 057_add_eiopa_sfdr_assurance_tables
Revises: 056_add_ets_product_benchmarks
Create Date: 2026-03-17

Sprint 8 — E7 (EIOPA Stress) + E9 (SFDR Annex) + E10 (Assurance Readiness)

New tables:
  eiopa_stress_runs       — EIOPA ORSA climate stress test run header
  eiopa_stress_scenarios  — Per-scenario SCR/MCR results
  sfdr_annex_runs         — SFDR Annex I–V disclosure template generation run
  sfdr_annex_sections     — Per-section completeness detail
  assurance_readiness_runs — Assurance readiness assessment run header
  assurance_criterion_results — Per-criterion scoring detail

References:
  - Solvency II Art 45a / EIOPA 2022/2023 Stress Test
  - SFDR (EU) 2019/2088 + RTS (EU) 2022/1288 Annexes I–V
  - ISAE 3000/3410 / ISSA 5000 / CSRD Art 26a
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "057_add_eiopa_sfdr_assurance_tables"
down_revision = "056_add_ets_product_benchmarks"
branch_labels = None
depends_on = None


def upgrade():
    # ------------------------------------------------------------------
    # E7: EIOPA ORSA Climate Stress Test
    # ------------------------------------------------------------------
    op.create_table(
        "eiopa_stress_runs",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.Text, nullable=False, unique=True),
        sa.Column("entity_id", sa.Text, nullable=False),
        sa.Column("entity_name", sa.Text, nullable=False),
        sa.Column("insurer_type", sa.Text, nullable=False),   # life|non_life|composite|reinsurer|captive
        sa.Column("assessment_date", sa.Date, nullable=False),
        sa.Column("scenarios_run", JSONB, nullable=False, server_default="[]"),

        # Balance sheet snapshot
        sa.Column("total_assets_eur", sa.Numeric(20, 2)),
        sa.Column("total_tp_eur", sa.Numeric(20, 2)),
        sa.Column("eligible_own_funds_eur", sa.Numeric(20, 2)),
        sa.Column("scr_eur", sa.Numeric(20, 2)),
        sa.Column("mcr_eur", sa.Numeric(20, 2)),

        # Headline results
        sa.Column("worst_scenario_id", sa.Text),
        sa.Column("worst_solvency_ratio_pct", sa.Numeric(8, 2)),
        sa.Column("worst_capital_shortfall_eur", sa.Numeric(20, 2)),
        sa.Column("any_scr_breach", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("any_mcr_breach", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("overall_resilience", sa.Text),   # resilient|vulnerable|at_risk|critical

        # ORSA checklist
        sa.Column("orsa_completeness_pct", sa.Numeric(5, 1)),
        sa.Column("orsa_items_met", sa.Integer),
        sa.Column("orsa_items_total", sa.Integer),

        sa.Column("gaps", JSONB, nullable=False, server_default="[]"),
        sa.Column("priority_actions", JSONB, nullable=False, server_default="[]"),
        sa.Column("metadata", JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "eiopa_stress_scenarios",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.Text, nullable=False,
                  sa.ForeignKey("eiopa_stress_runs.run_id", ondelete="CASCADE")),
        sa.Column("scenario_id", sa.Text, nullable=False),   # sudden_transition etc.
        sa.Column("scenario_name", sa.Text),
        sa.Column("temp_outcome_c", sa.Numeric(4, 2)),
        sa.Column("horizon_years", sa.Integer),

        # Asset shocks (EUR)
        sa.Column("equity_loss_eur", sa.Numeric(20, 2)),
        sa.Column("re_loss_eur", sa.Numeric(20, 2)),
        sa.Column("sovereign_bond_loss_eur", sa.Numeric(20, 2)),
        sa.Column("ig_corp_bond_loss_eur", sa.Numeric(20, 2)),
        sa.Column("hy_corp_bond_loss_eur", sa.Numeric(20, 2)),
        sa.Column("total_asset_loss_eur", sa.Numeric(20, 2)),

        # Underwriting shocks (EUR)
        sa.Column("natcat_additional_loss_eur", sa.Numeric(20, 2)),
        sa.Column("reserve_deterioration_eur", sa.Numeric(20, 2)),
        sa.Column("total_uw_shock_eur", sa.Numeric(20, 2)),

        # Capital impact
        sa.Column("post_stress_scr_eur", sa.Numeric(20, 2)),
        sa.Column("post_stress_own_funds_eur", sa.Numeric(20, 2)),
        sa.Column("post_stress_solvency_ratio_pct", sa.Numeric(8, 2)),
        sa.Column("scr_breach", sa.Boolean),
        sa.Column("mcr_breach", sa.Boolean),
        sa.Column("capital_shortfall_eur", sa.Numeric(20, 2)),

        # Summary
        sa.Column("total_stress_loss_eur", sa.Numeric(20, 2)),
        sa.Column("total_stress_loss_pct_of_own_funds", sa.Numeric(8, 2)),
        sa.Column("stress_severity", sa.Text),
        sa.Column("recovery_feasible", sa.Boolean),
        sa.Column("key_drivers", JSONB, nullable=False, server_default="[]"),
        sa.Column("narrative", sa.Text),

        sa.UniqueConstraint("run_id", "scenario_id", name="uq_eiopa_stress_scenario"),
    )
    op.create_index("ix_eiopa_stress_runs_entity_id", "eiopa_stress_runs", ["entity_id"])
    op.create_index("ix_eiopa_stress_runs_assessment_date", "eiopa_stress_runs", ["assessment_date"])

    # ------------------------------------------------------------------
    # E9: SFDR Annex Disclosure Template Runs
    # ------------------------------------------------------------------
    op.create_table(
        "sfdr_annex_runs",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.Text, nullable=False, unique=True),
        sa.Column("annex_id", sa.Text, nullable=False),        # I | II | III | IV | V
        sa.Column("annex_title", sa.Text),
        sa.Column("fund_id", sa.Text, nullable=False),
        sa.Column("fund_name", sa.Text, nullable=False),
        sa.Column("sfdr_classification", sa.Text),             # art6|art8|art8plus|art9
        sa.Column("isin", sa.Text),
        sa.Column("legal_entity_identifier", sa.Text),
        sa.Column("report_date", sa.Date, nullable=False),

        # Reference period
        sa.Column("reference_period_start", sa.Date),
        sa.Column("reference_period_end", sa.Date),

        # Completeness
        sa.Column("completeness_pct", sa.Numeric(5, 1)),
        sa.Column("compliance_status", sa.Text),               # compliant|partial|non_compliant
        sa.Column("mandatory_fields_total", sa.Integer),
        sa.Column("mandatory_fields_populated", sa.Integer),
        sa.Column("optional_fields_total", sa.Integer),
        sa.Column("optional_fields_populated", sa.Integer),

        # PAI coverage
        sa.Column("pai_mandatory_indicators_total", sa.Integer),
        sa.Column("pai_mandatory_indicators_populated", sa.Integer),
        sa.Column("pai_coverage_pct", sa.Numeric(5, 1)),

        # Fund financials
        sa.Column("total_aum_eur", sa.Numeric(20, 2)),
        sa.Column("proportion_sustainable_pct", sa.Numeric(5, 1)),
        sa.Column("proportion_taxonomy_aligned_pct", sa.Numeric(5, 1)),

        sa.Column("gaps", JSONB, nullable=False, server_default="[]"),
        sa.Column("priority_actions", JSONB, nullable=False, server_default="[]"),
        sa.Column("metadata", JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "sfdr_annex_sections",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.Text, nullable=False,
                  sa.ForeignKey("sfdr_annex_runs.run_id", ondelete="CASCADE")),
        sa.Column("section_id", sa.Text, nullable=False),
        sa.Column("section_title", sa.Text),
        sa.Column("is_mandatory", sa.Boolean),
        sa.Column("is_populated", sa.Boolean),
        sa.Column("missing_fields", JSONB, nullable=False, server_default="[]"),
        sa.Column("content_snapshot", JSONB, nullable=False, server_default="{}"),
    )
    op.create_index("ix_sfdr_annex_runs_fund_id", "sfdr_annex_runs", ["fund_id"])
    op.create_index("ix_sfdr_annex_runs_annex_id", "sfdr_annex_runs", ["annex_id"])

    # ------------------------------------------------------------------
    # E10: Assurance Readiness Assessment
    # ------------------------------------------------------------------
    op.create_table(
        "assurance_readiness_runs",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.Text, nullable=False, unique=True),
        sa.Column("entity_id", sa.Text, nullable=False),
        sa.Column("entity_name", sa.Text, nullable=False),
        sa.Column("reporting_framework", sa.Text),             # CSRD_ESRS|GRI|ISSB|SFDR_ONLY
        sa.Column("assurance_standard_target", sa.Text),       # ISAE3000|ISAE3410|ISSA5000|CSRD_ART26A
        sa.Column("target_assurance_level", sa.Text),          # limited|reasonable
        sa.Column("csrd_wave", sa.Integer),
        sa.Column("reporting_year", sa.Text),
        sa.Column("assessment_date", sa.Date, nullable=False),

        # Headline scores
        sa.Column("overall_readiness_score_pct", sa.Numeric(5, 1)),
        sa.Column("readiness_tier", sa.Text),                  # ready|nearly_ready|requires_remediation|not_ready
        sa.Column("weighted_score", sa.Numeric(8, 3)),
        sa.Column("blocking_gaps_count", sa.Integer),
        sa.Column("estimated_remediation_weeks", sa.Integer),

        # Domain scores (snapshot)
        sa.Column("domain_scores", JSONB, nullable=False, server_default="{}"),

        # Standards coverage
        sa.Column("standards_coverage", JSONB, nullable=False, server_default="{}"),

        sa.Column("blocking_gaps", JSONB, nullable=False, server_default="[]"),
        sa.Column("gaps", JSONB, nullable=False, server_default="[]"),
        sa.Column("priority_actions", JSONB, nullable=False, server_default="[]"),
        sa.Column("metadata", JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "assurance_criterion_results",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.Text, nullable=False,
                  sa.ForeignKey("assurance_readiness_runs.run_id", ondelete="CASCADE")),
        sa.Column("criterion_id", sa.Text, nullable=False),
        sa.Column("domain", sa.Text),
        sa.Column("title", sa.Text),
        sa.Column("weight", sa.Numeric(5, 3)),
        sa.Column("blocking", sa.Boolean),
        sa.Column("score", sa.Numeric(4, 3)),               # 0.0 | 0.5 | 1.0
        sa.Column("weighted_score", sa.Numeric(8, 3)),
        sa.Column("status", sa.Text),                       # met|partial|not_met
        sa.Column("evidence_quality", sa.Text),
        sa.Column("evidence_description", sa.Text),
        sa.Column("gaps", JSONB, nullable=False, server_default="[]"),

        sa.UniqueConstraint("run_id", "criterion_id", name="uq_assurance_criterion"),
    )
    op.create_index("ix_assurance_readiness_entity_id", "assurance_readiness_runs", ["entity_id"])
    op.create_index("ix_assurance_readiness_tier", "assurance_readiness_runs", ["readiness_tier"])
    op.create_index("ix_assurance_readiness_date", "assurance_readiness_runs", ["assessment_date"])


def downgrade():
    op.drop_table("assurance_criterion_results")
    op.drop_table("assurance_readiness_runs")
    op.drop_table("sfdr_annex_sections")
    op.drop_table("sfdr_annex_runs")
    op.drop_table("eiopa_stress_scenarios")
    op.drop_table("eiopa_stress_runs")
