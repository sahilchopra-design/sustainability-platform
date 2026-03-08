"""
034 – Enhance csrd_esrs_catalog with AR/DR text, module mapping, and
      regulatory cross-reference columns.

Adds 11 new columns to support:
  - Application Requirement (AR) text and references
  - Disclosure Requirement (DR) full text
  - Module mapping to platform modules
  - Phase-in / voluntary / conditional flags from EFRAG IG3
  - SFDR / Pillar 3 / Benchmark cross-references
"""

from alembic import op
import sqlalchemy as sa

revision = '034_enhance_esrs_catalog_ar_dr'
down_revision = '033_add_ca100_country_risk'
branch_labels = None
depends_on = None


def upgrade():
    # --- Application Requirement (AR) fields ---
    op.add_column('csrd_esrs_catalog',
                  sa.Column('related_ar', sa.Text(), nullable=True,
                            comment='AR paragraph references from EFRAG IG3 (e.g. "AR 1", "AR 1- AR 8")'))
    op.add_column('csrd_esrs_catalog',
                  sa.Column('ar_text', sa.Text(), nullable=True,
                            comment='Full Application Requirement text from ESRS Set 1'))
    # --- Disclosure Requirement (DR) fields ---
    op.add_column('csrd_esrs_catalog',
                  sa.Column('dr_text', sa.Text(), nullable=True,
                            comment='Full Disclosure Requirement paragraph text from ESRS Set 1'))
    op.add_column('csrd_esrs_catalog',
                  sa.Column('dr_full_name', sa.Text(), nullable=True,
                            comment='Full DR name (e.g. "Transition plan for climate change mitigation")'))
    # --- EFRAG IG3 classification flags ---
    op.add_column('csrd_esrs_catalog',
                  sa.Column('conditional_or_alternative', sa.String(30), nullable=True,
                            comment='Conditional, Alternative, or null'))
    op.add_column('csrd_esrs_catalog',
                  sa.Column('is_voluntary', sa.Boolean(), server_default='false',
                            comment='May [V] flag from EFRAG IG3'))
    op.add_column('csrd_esrs_catalog',
                  sa.Column('sfdr_pillar3_benchmark', sa.Text(), nullable=True,
                            comment='Appendix B cross-ref (SFDR + PILLAR 3 + Benchmark + CL)'))
    op.add_column('csrd_esrs_catalog',
                  sa.Column('phase_in_less_750', sa.Text(), nullable=True,
                            comment='Appendix C phasing-in for undertakings with <750 employees'))
    op.add_column('csrd_esrs_catalog',
                  sa.Column('phase_in_all_undertakings', sa.Text(), nullable=True,
                            comment='Appendix C phasing-in applicable to all undertakings'))
    # --- Platform mapping ---
    op.add_column('csrd_esrs_catalog',
                  sa.Column('module_mapping', sa.String(100), nullable=True,
                            comment='Platform module this DP maps to'))
    op.add_column('csrd_esrs_catalog',
                  sa.Column('reporting_area', sa.String(30), nullable=True,
                            comment='ESRS reporting area: GOV, SBM, IRO, MT'))

    # Additional index for module-based queries
    op.create_index('ix_esrs_catalog_module', 'csrd_esrs_catalog', ['module_mapping'])
    op.create_index('ix_esrs_catalog_reporting_area', 'csrd_esrs_catalog', ['reporting_area'])


def downgrade():
    op.drop_index('ix_esrs_catalog_reporting_area', 'csrd_esrs_catalog')
    op.drop_index('ix_esrs_catalog_module', 'csrd_esrs_catalog')
    op.drop_column('csrd_esrs_catalog', 'reporting_area')
    op.drop_column('csrd_esrs_catalog', 'module_mapping')
    op.drop_column('csrd_esrs_catalog', 'phase_in_all_undertakings')
    op.drop_column('csrd_esrs_catalog', 'phase_in_less_750')
    op.drop_column('csrd_esrs_catalog', 'sfdr_pillar3_benchmark')
    op.drop_column('csrd_esrs_catalog', 'is_voluntary')
    op.drop_column('csrd_esrs_catalog', 'conditional_or_alternative')
    op.drop_column('csrd_esrs_catalog', 'dr_full_name')
    op.drop_column('csrd_esrs_catalog', 'dr_text')
    op.drop_column('csrd_esrs_catalog', 'ar_text')
    op.drop_column('csrd_esrs_catalog', 'related_ar')
