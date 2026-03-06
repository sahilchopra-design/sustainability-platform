"""Merge branches: unite 019_extend_assets_pcaf + 022_add_data_intake_tables

Revision ID: 023_merge_branches
Revises: 019_extend_assets_pcaf, 022_add_data_intake_tables
Create Date: 2026-03-04

Merge migration: unites the asset-PCAF branch (017→018→019) with the
data-intake branch (021→022) into a single linear head.
"""
from alembic import op

revision = "023_merge_branches"
down_revision = ("019_extend_assets_pcaf", "022_add_data_intake_tables")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass  # merge only — no DDL


def downgrade() -> None:
    pass
