"""038 — PE/VC deal pipeline, screening, portfolio company tables

Revision ID: 038
Revises: 037_add_fund_structure_tables
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

revision = "038"
down_revision = "037_add_fund_structure_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── PE Deals ──────────────────────────────────────────────────────────────
    op.create_table(
        "pe_deals",
        sa.Column("deal_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("sector", sa.String(100)),
        sa.Column("sub_sector", sa.String(100)),
        sa.Column("country", sa.String(10)),
        sa.Column("stage", sa.String(50), nullable=False),  # sourcing/screening/dd/ic/closing/portfolio/exited
        sa.Column("deal_type", sa.String(50)),  # buyout/growth/venture/secondary/co-invest
        sa.Column("deal_size_eur", sa.Numeric(20, 2)),
        sa.Column("equity_ticket_eur", sa.Numeric(20, 2)),
        sa.Column("enterprise_value_eur", sa.Numeric(20, 2)),
        sa.Column("revenue_eur", sa.Numeric(20, 2)),
        sa.Column("ebitda_eur", sa.Numeric(20, 2)),
        sa.Column("entry_multiple", sa.Float),
        sa.Column("source", sa.String(100)),  # broker/proprietary/network
        sa.Column("lead_partner", sa.String(255)),
        sa.Column("fund_id", sa.String(100)),
        sa.Column("esg_screening_status", sa.String(50), default="pending"),
        sa.Column("red_flags", JSONB, default=[]),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # ── PE ESG Screening Scores ───────────────────────────────────────────────
    op.create_table(
        "pe_screening_scores",
        sa.Column("score_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("deal_id", UUID(as_uuid=True), sa.ForeignKey("pe_deals.deal_id"), nullable=False),
        sa.Column("dimension", sa.String(50), nullable=False),  # environmental/social/governance/transition_risk/physical_risk
        sa.Column("sub_dimension", sa.String(100)),
        sa.Column("rating", sa.Integer),  # 1-5
        sa.Column("weight", sa.Float, default=1.0),
        sa.Column("rationale", sa.Text),
        sa.Column("data_source", sa.String(255)),
        sa.Column("assessed_by", sa.String(255)),
        sa.Column("assessed_at", sa.DateTime, server_default=sa.func.now()),
    )

    # ── PE Portfolio Companies ────────────────────────────────────────────────
    op.create_table(
        "pe_portfolio_companies",
        sa.Column("company_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("deal_id", UUID(as_uuid=True), sa.ForeignKey("pe_deals.deal_id")),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("sector", sa.String(100)),
        sa.Column("country", sa.String(10)),
        sa.Column("fund_id", sa.String(100)),
        sa.Column("investment_date", sa.Date),
        sa.Column("equity_invested_eur", sa.Numeric(20, 2)),
        sa.Column("current_nav_eur", sa.Numeric(20, 2)),
        sa.Column("ownership_pct", sa.Float),
        sa.Column("board_seats", sa.Integer, default=0),
        sa.Column("status", sa.String(50), default="active"),  # active/exited/written_off
        sa.Column("exit_date", sa.Date),
        sa.Column("exit_proceeds_eur", sa.Numeric(20, 2)),
        sa.Column("esg_score_current", sa.Float),
        sa.Column("esg_score_entry", sa.Float),
        sa.Column("sdg_alignment", JSONB, default=[]),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # ── PE Sector Risk Heatmap ────────────────────────────────────────────────
    op.create_table(
        "pe_sector_risk_heatmap",
        sa.Column("sector_risk_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("sector", sa.String(100), nullable=False),
        sa.Column("environmental_risk", sa.Integer),  # 1-5
        sa.Column("social_risk", sa.Integer),
        sa.Column("governance_risk", sa.Integer),
        sa.Column("transition_risk", sa.Integer),
        sa.Column("physical_risk", sa.Integer),
        sa.Column("overall_risk", sa.Integer),
        sa.Column("rationale", sa.Text),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_index("ix_pe_deals_stage", "pe_deals", ["stage"])
    op.create_index("ix_pe_deals_sector", "pe_deals", ["sector"])
    op.create_index("ix_pe_deals_fund_id", "pe_deals", ["fund_id"])
    op.create_index("ix_pe_screening_deal", "pe_screening_scores", ["deal_id"])
    op.create_index("ix_pe_portco_fund", "pe_portfolio_companies", ["fund_id"])
    op.create_index("ix_pe_portco_status", "pe_portfolio_companies", ["status"])


def downgrade() -> None:
    op.drop_index("ix_pe_portco_status")
    op.drop_index("ix_pe_portco_fund")
    op.drop_index("ix_pe_screening_deal")
    op.drop_index("ix_pe_deals_fund_id")
    op.drop_index("ix_pe_deals_sector")
    op.drop_index("ix_pe_deals_stage")
    op.drop_table("pe_sector_risk_heatmap")
    op.drop_table("pe_portfolio_companies")
    op.drop_table("pe_screening_scores")
    op.drop_table("pe_deals")
