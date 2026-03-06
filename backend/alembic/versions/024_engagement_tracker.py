"""Client Engagement Tracker — counterparty climate engagement log

Revision ID: 024_engagement_tracker
Revises: 023_merge_branches
Create Date: 2026-03-04

Tables:
  - engagement_entities       : counterparties under active climate dialogue
  - engagement_log            : individual engagement interactions / milestones
  - engagement_commitments    : forward commitments made by the counterparty
  - engagement_escalations    : escalation flags (vote, divestment risk)

Aligned with:
  - PRI Active Ownership 2.0 (AO2.0)
  - TCFD Engagement Disclosure
  - CA100+ Net Zero Benchmark
  - SFDR PAI 10 (Board gender diversity used as engagement proxy here omitted)
  - NZBA Phase 2 Engagement Policy
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "024_engagement_tracker"
down_revision = "023_merge_branches"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Engagement Entities ──────────────────────────────────────────────────
    op.create_table(
        "engagement_entities",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("entity_name", sa.Text, nullable=False),
        sa.Column("lei", sa.Text),                           # Legal Entity Identifier
        sa.Column("isin", sa.Text),                          # Equity / bond ISIN
        sa.Column("sector_gics", sa.Text),
        sa.Column("country_iso2", sa.Text),
        sa.Column("engagement_theme", sa.Text),              # net_zero | deforestation | water | governance | just_transition
        sa.Column("engagement_strategy", sa.Text),           # direct | collaborative | voting | policy
        sa.Column("priority_tier", sa.Integer, default=2),   # 1 = highest
        sa.Column("ca100_focus", sa.Boolean, default=False),
        sa.Column("nzba_engagement", sa.Boolean, default=False),
        sa.Column("engagement_lead", sa.Text),               # internal portfolio manager
        sa.Column("engagement_start_date", sa.Date),
        sa.Column("target_close_date", sa.Date),
        sa.Column("status", sa.Text, default="active"),      # active | closed | escalated | paused
        sa.Column("overall_progress_pct", sa.Numeric(5, 1), default=0),
        sa.Column("baseline_temp_score", sa.Numeric(4, 2)), # issuer implied temp (°C) at start
        sa.Column("current_temp_score", sa.Numeric(4, 2)),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_engage_entity_name", "engagement_entities", ["entity_name"])
    op.create_index("ix_engage_status", "engagement_entities", ["status"])

    # ── Engagement Log ───────────────────────────────────────────────────────
    op.create_table(
        "engagement_log",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("entity_id", sa.Integer, sa.ForeignKey("engagement_entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("log_date", sa.Date, nullable=False),
        sa.Column("interaction_type", sa.Text),              # meeting | call | letter | agm_vote | proxy_alert | report_review
        sa.Column("milestone", sa.Text),                     # e.g. "Board met — NZE target discussed"
        sa.Column("outcome", sa.Text),                       # positive | neutral | negative | pending
        sa.Column("next_action", sa.Text),
        sa.Column("next_action_date", sa.Date),
        sa.Column("participants", sa.Text),                  # comma-separated internal participants
        sa.Column("counterparty_participants", sa.Text),
        sa.Column("attachments_refs", JSONB),                # [{"name": "...", "url": "..."}, ...]
        sa.Column("created_by", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_engage_log_entity", "engagement_log", ["entity_id"])

    # ── Engagement Commitments ───────────────────────────────────────────────
    op.create_table(
        "engagement_commitments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("entity_id", sa.Integer, sa.ForeignKey("engagement_entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("commitment_type", sa.Text),               # sbti_target | net_zero_pledge | scope3_disclosure | board_climate | capex_plan
        sa.Column("description", sa.Text),
        sa.Column("target_year", sa.Integer),
        sa.Column("target_value", sa.Numeric(12, 4)),        # e.g. 50 (% reduction)
        sa.Column("target_unit", sa.Text),                   # pct_reduction | tco2e | mw | GBP
        sa.Column("baseline_year", sa.Integer),
        sa.Column("status", sa.Text, default="open"),        # open | delivered | missed | revised
        sa.Column("verification_body", sa.Text),             # SBTi | CDP | auditor
        sa.Column("verified", sa.Boolean, default=False),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # ── Escalation Flags ─────────────────────────────────────────────────────
    op.create_table(
        "engagement_escalations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("entity_id", sa.Integer, sa.ForeignKey("engagement_entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("escalation_date", sa.Date, nullable=False),
        sa.Column("escalation_type", sa.Text),               # vote_against | co_filer | divestment_warning | public_statement | regulatory_referral
        sa.Column("trigger_reason", sa.Text),
        sa.Column("action_taken", sa.Text),
        sa.Column("resolution", sa.Text),
        sa.Column("resolved_at", sa.Date),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("engagement_escalations")
    op.drop_table("engagement_commitments")
    op.drop_table("engagement_log")
    op.drop_table("engagement_entities")
