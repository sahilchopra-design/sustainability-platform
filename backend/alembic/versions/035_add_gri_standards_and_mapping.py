"""
035 – Add GRI Standards catalog and ESRS-GRI data-point mapping tables.

Creates:
  - gri_standards: Master GRI disclosure catalog (from GRI Sustainability
    Taxonomy 2025 XBRL schema + label linkbase).
  - gri_esrs_mapping: Row-level mapping between ESRS data points and GRI
    disclosures (from EFRAG draft ESRS-GRI mapping tool).

Also adds a gri_disclosure_ref column on csrd_esrs_catalog for quick
single-column lookup of the primary GRI reference per ESRS data point.
"""

from alembic import op
import sqlalchemy as sa

revision = '035_add_gri_standards_and_mapping'
down_revision = '034_enhance_esrs_catalog_ar_dr'
branch_labels = None
depends_on = None


def upgrade():
    # ------------------------------------------------------------------
    # 1) GRI Standards catalog – one row per concrete XBRL element
    # ------------------------------------------------------------------
    op.create_table(
        'gri_standards',
        sa.Column('id', sa.Text(), primary_key=True,
                  comment='Deterministic UUID from element_id'),
        sa.Column('element_id', sa.Text(), nullable=False, unique=True,
                  comment='XBRL element ID (e.g. gri_TotalNumberOfEmployees)'),
        sa.Column('element_name', sa.Text(), nullable=False,
                  comment='CamelCase element name'),
        sa.Column('standard_code', sa.String(20), nullable=True,
                  comment='GRI standard number (e.g. "GRI 2", "GRI 305")'),
        sa.Column('disclosure_code', sa.String(30), nullable=True,
                  comment='Disclosure ref (e.g. "2-1", "305-1")'),
        sa.Column('disclosure_name', sa.Text(), nullable=True,
                  comment='Full disclosure title'),
        sa.Column('label', sa.Text(), nullable=True,
                  comment='Standard label (en)'),
        sa.Column('verbose_label', sa.Text(), nullable=True,
                  comment='Verbose label with paragraph refs'),
        sa.Column('documentation', sa.Text(), nullable=True,
                  comment='Documentation / guidance text'),
        sa.Column('data_type', sa.String(60), nullable=True,
                  comment='XBRL data type (e.g. xbrli:decimalItemType)'),
        sa.Column('period_type', sa.String(20), nullable=True,
                  comment='instant | duration'),
        sa.Column('is_abstract', sa.Boolean(), server_default='false',
                  comment='True for abstract grouping elements'),
        sa.Column('substitution_group', sa.String(40), nullable=True),
        sa.Column('topic_area', sa.String(60), nullable=True,
                  comment='Derived topic: Environmental, Social, Governance, Economic, General'),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()')),
    )
    op.create_index('ix_gri_std_standard', 'gri_standards', ['standard_code'])
    op.create_index('ix_gri_std_disclosure', 'gri_standards', ['disclosure_code'])
    op.create_index('ix_gri_std_topic', 'gri_standards', ['topic_area'])

    # ------------------------------------------------------------------
    # 2) ESRS ↔ GRI mapping (from EFRAG draft tool)
    # ------------------------------------------------------------------
    op.create_table(
        'gri_esrs_mapping',
        sa.Column('id', sa.Text(), primary_key=True,
                  comment='Deterministic UUID'),
        sa.Column('esrs_indicator_code', sa.String(120), nullable=False,
                  comment='FK-like ref to csrd_esrs_catalog.indicator_code'),
        sa.Column('esrs_standard', sa.String(20), nullable=False,
                  comment='E1, S1, ESRS 2, etc.'),
        sa.Column('esrs_dr', sa.String(60), nullable=True,
                  comment='Disclosure Requirement (E1-1, GOV-1, MDR-P, ...)'),
        sa.Column('esrs_paragraph', sa.String(40), nullable=True),
        sa.Column('esrs_dp_name', sa.Text(), nullable=True,
                  comment='ESRS data point name'),
        sa.Column('gri_standard', sa.String(30), nullable=True,
                  comment='GRI standard (GRI 2, GRI 305, ...)'),
        sa.Column('gri_disclosure', sa.String(30), nullable=True,
                  comment='GRI disclosure ref (2-19, 305-1, ...)'),
        sa.Column('gri_sub_item', sa.String(20), nullable=True,
                  comment='Sub-item letter (a, b, c, ...)'),
        sa.Column('gri_dp_name', sa.Text(), nullable=True,
                  comment='GRI data point description'),
        sa.Column('mapping_notes', sa.Text(), nullable=True,
                  comment='Notes column from EFRAG tool'),
        sa.Column('mapping_quality', sa.String(20), nullable=True,
                  comment='exact | partial | thematic'),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()')),
    )
    op.create_index('ix_gri_map_esrs', 'gri_esrs_mapping', ['esrs_indicator_code'])
    op.create_index('ix_gri_map_gri', 'gri_esrs_mapping', ['gri_standard', 'gri_disclosure'])
    op.create_index('ix_gri_map_esrs_std', 'gri_esrs_mapping', ['esrs_standard'])

    # ------------------------------------------------------------------
    # 3) Quick-lookup column on existing ESRS catalog
    # ------------------------------------------------------------------
    op.add_column('csrd_esrs_catalog',
                  sa.Column('gri_disclosure_ref', sa.String(60), nullable=True,
                            comment='Primary GRI disclosure ref (e.g. "GRI 305-1-a")'))


def downgrade():
    op.drop_column('csrd_esrs_catalog', 'gri_disclosure_ref')
    op.drop_table('gri_esrs_mapping')
    op.drop_table('gri_standards')
