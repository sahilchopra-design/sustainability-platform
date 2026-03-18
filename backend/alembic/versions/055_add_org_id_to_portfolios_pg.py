"""Add org_id to portfolios_pg for multi-tenant isolation.

Revision ID: 055
Revises: 054
Create Date: 2026-03-16

Rationale (P0-2):
  Migration 025 created the organisations table and added org_id to users_pg,
  but portfolios_pg (the live portfolio table used by all analytics routes)
  never received an org_id FK.  This migration adds the column so that portfolio
  queries can be scoped per organisation.

  The column is nullable so existing rows are preserved unchanged; a NULL
  org_id means the portfolio is shared / unscoped (legacy rows).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "055"
down_revision = "054"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add org_id FK to portfolios_pg (nullable — legacy rows keep NULL)
    op.add_column(
        "portfolios_pg",
        sa.Column(
            "org_id",
            UUID(as_uuid=True),
            sa.ForeignKey("organisations.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
    )

    # Add org_id to assets_pg for asset-level isolation (optional, follows portfolio)
    op.add_column(
        "assets_pg",
        sa.Column(
            "org_id",
            UUID(as_uuid=True),
            nullable=True,
            index=True,
        ),
    )

    # Add org_id to analysis_runs_pg for report isolation
    op.add_column(
        "analysis_runs_pg",
        sa.Column(
            "org_id",
            UUID(as_uuid=True),
            nullable=True,
            index=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("analysis_runs_pg", "org_id")
    op.drop_column("assets_pg", "org_id")
    op.drop_column("portfolios_pg", "org_id")
