"""Add csrd_report_uploads tracking table

Revision ID: 016
Revises: 015
Create Date: 2026-03-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "016_add_csrd_report_uploads"
down_revision = "015_add_issb_sasb_risk_scenario_tables"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "csrd_report_uploads",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("file_path", sa.Text, nullable=False),
        sa.Column("file_size_bytes", sa.Integer),
        sa.Column("entity_name_override", sa.String(512)),
        sa.Column("reporting_year_override", sa.Integer),
        sa.Column("primary_sector", sa.String(64), server_default="other"),
        sa.Column("country_iso", sa.String(3), server_default="UNK"),
        sa.Column("entity_registry_id", sa.String(36)),
        sa.Column("status", sa.String(32), server_default="uploaded"),
        sa.Column("kpis_extracted", sa.Integer, server_default="0"),
        sa.Column("kpis_updated", sa.Integer, server_default="0"),
        sa.Column("gaps_found", sa.Integer, server_default="0"),
        sa.Column("lineage_entries", sa.Integer, server_default="0"),
        sa.Column("extraction_summary", postgresql.JSONB),
        sa.Column("error_message", sa.Text),
        sa.Column("uploaded_by", sa.String(128), server_default="user"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_csrd_report_uploads_entity",
        "csrd_report_uploads",
        ["entity_registry_id"],
    )
    op.create_index(
        "ix_csrd_report_uploads_status",
        "csrd_report_uploads",
        ["status"],
    )


def downgrade():
    op.drop_index("ix_csrd_report_uploads_status", table_name="csrd_report_uploads")
    op.drop_index("ix_csrd_report_uploads_entity", table_name="csrd_report_uploads")
    op.drop_table("csrd_report_uploads")
