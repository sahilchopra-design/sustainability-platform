"""Extend assets_pg with PCAF, emissions, LEI, and transition columns

Revision ID: 019
Revises: 018
Create Date: 2026-03-03

Adds to assets_pg:
  - evic_eur              NUMERIC  — Enterprise Value Including Cash (for PCAF AF)
  - scope1_tco2e          NUMERIC  — Scope 1 emissions (tCO2e/year)
  - scope2_tco2e          NUMERIC  — Scope 2 emissions (tCO2e/year)
  - scope3_tco2e          NUMERIC  — Scope 3 emissions (tCO2e/year, optional)
  - pcaf_dqs              SMALLINT — PCAF Data Quality Score 1–5
  - attribution_factor    NUMERIC  — Computed AF = outstanding / EVIC
  - annual_revenue_eur    NUMERIC  — Borrower annual revenue (for WACI denominator)
  - entity_lei            VARCHAR  — GLEIF Legal Entity Identifier (cross-module key)
  - isin                  VARCHAR  — ISIN for listed equity/bond asset classes
  - sbti_aligned          BOOLEAN  — SBTi target validated
  - net_zero_committed    BOOLEAN  — Net-zero commitment (public pledge)
  - transition_plan_status VARCHAR — not_started | committed | plan_received | validated | on_track | escalated

These columns convert the basic assets_pg record into a full PCAF InvesteeData carrier,
enabling real WACI/ITR/Attribution calculations without a separate investee table.
"""
from alembic import op
import sqlalchemy as sa

revision = "019_extend_assets_pcaf"
down_revision = "018_time_series_tables"
branch_labels = None
depends_on = None

# ── New columns to add (name, type, kwargs) ────────────────────────────────────
_NEW_COLUMNS = [
    ("evic_eur",             sa.Numeric(18, 2),  {"nullable": True, "comment": "Enterprise Value Including Cash (EUR) — PCAF AF denominator for corporate loans/bonds/equity"}),
    ("scope1_tco2e",         sa.Numeric(18, 2),  {"nullable": True, "comment": "Scope 1 GHG emissions (tCO2e/year)"}),
    ("scope2_tco2e",         sa.Numeric(18, 2),  {"nullable": True, "comment": "Scope 2 GHG emissions location-based (tCO2e/year)"}),
    ("scope3_tco2e",         sa.Numeric(18, 2),  {"nullable": True, "comment": "Scope 3 GHG emissions (tCO2e/year) — optional, DQS typically 4-5 when used"}),
    ("pcaf_dqs",             sa.SmallInteger(),  {"nullable": True, "comment": "PCAF Data Quality Score 1 (best) – 5 (modelled estimate)"}),
    ("attribution_factor",   sa.Numeric(10, 6),  {"nullable": True, "comment": "Computed: outstanding_amount / EVIC — capped at 1.0"}),
    ("annual_revenue_eur",   sa.Numeric(18, 2),  {"nullable": True, "comment": "Borrower annual revenue (EUR) — WACI denominator"}),
    ("entity_lei",           sa.String(20),       {"nullable": True, "comment": "GLEIF LEI — primary cross-module entity linkage key"}),
    ("isin",                 sa.String(12),       {"nullable": True, "comment": "ISIN code for listed equity / corporate bond asset classes"}),
    ("sbti_aligned",         sa.Boolean(),        {"server_default": "false", "nullable": False, "comment": "SBTi-validated near-term or net-zero target"}),
    ("net_zero_committed",   sa.Boolean(),        {"server_default": "false", "nullable": False, "comment": "Public net-zero commitment (e.g. Race to Zero pledge)"}),
    ("transition_plan_status", sa.String(50),     {"nullable": True, "comment": "not_started | committed | plan_received | validated | on_track | escalated"}),
    ("pcaf_asset_class",     sa.String(50),       {"nullable": True, "comment": "PCAF Standard Part A asset class: listed_equity | corporate_bonds | business_loans | project_finance | mortgages | ..."}),
]


def upgrade():
    for col_name, col_type, kwargs in _NEW_COLUMNS:
        op.add_column(
            "assets_pg",
            sa.Column(col_name, col_type, **{k: v for k, v in kwargs.items() if k != "comment"}),
        )

    # Add CHECK constraint for PCAF DQS range
    op.execute("""
        ALTER TABLE assets_pg
        ADD CONSTRAINT chk_assets_pcaf_dqs
        CHECK (pcaf_dqs IS NULL OR (pcaf_dqs >= 1 AND pcaf_dqs <= 5));
    """)

    # Add CHECK constraint for transition_plan_status allowed values
    op.execute("""
        ALTER TABLE assets_pg
        ADD CONSTRAINT chk_assets_transition_status
        CHECK (
            transition_plan_status IS NULL OR
            transition_plan_status IN (
                'not_started', 'committed', 'plan_received',
                'validated', 'on_track', 'escalated'
            )
        );
    """)

    # Index on LEI for fast cross-module joins
    op.create_index("idx_assets_pg_lei", "assets_pg", ["entity_lei"])
    # Index on SBTi / NZ flags for transition readiness score computation
    op.create_index(
        "idx_assets_pg_transition",
        "assets_pg",
        ["portfolio_id", "sbti_aligned", "net_zero_committed"],
    )


def downgrade():
    op.drop_index("idx_assets_pg_transition", table_name="assets_pg")
    op.drop_index("idx_assets_pg_lei", table_name="assets_pg")
    op.execute("ALTER TABLE assets_pg DROP CONSTRAINT IF EXISTS chk_assets_transition_status;")
    op.execute("ALTER TABLE assets_pg DROP CONSTRAINT IF EXISTS chk_assets_pcaf_dqs;")
    for col_name, _, _ in reversed(_NEW_COLUMNS):
        op.drop_column("assets_pg", col_name)
