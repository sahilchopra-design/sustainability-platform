"""028 — Asia Regulatory + CBI tables

HKMA GS-1, Bank of Japan climate scenarios, ASEAN Taxonomy v3,
PBoC Green Finance, Climate Bond Initiative (CBI).

BRSR is already in migration 009 (brsr_disclosures table — comprehensive).
No duplicate BRSR table added here.

Revision ID: 028_asia_regulatory_cbi
Revises:     027_add_parameter_governance
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
import uuid

# ---------------------------------------------------------------------------
revision       = '028_asia_regulatory_cbi'
down_revision  = '027_add_parameter_governance'
branch_labels  = None
depends_on     = None
# ---------------------------------------------------------------------------


def upgrade() -> None:
    # ── HKMA GS-1 ──────────────────────────────────────────────────────────
    op.create_table(
        'hkma_entities',
        sa.Column('id',              sa.String(36),  primary_key=True,  default=str(uuid.uuid4())),
        sa.Column('entity_name',     sa.String(255), nullable=False),
        sa.Column('entity_type',     sa.String(50),  nullable=False),   # 'bank' | 'insurer' | 'securities'
        sa.Column('country_code',    sa.String(10),  server_default='HK'),
        sa.Column('hkma_lei',        sa.String(30)),
        sa.Column('total_assets_hkd',sa.Numeric(22, 2)),
        sa.Column('reporting_year',  sa.Integer()),
        sa.Column('created_at',      sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at',      sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_table(
        'hkma_climate_assessments',
        sa.Column('id',                   sa.String(36), primary_key=True, default=str(uuid.uuid4())),
        sa.Column('entity_id',            sa.String(36), sa.ForeignKey('hkma_entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('assessment_date',      sa.Date()),
        sa.Column('reporting_year',       sa.Integer()),
        # 4 pillars — maturity 1-5
        sa.Column('pillar_governance',    sa.Numeric(4, 2)),
        sa.Column('pillar_strategy',      sa.Numeric(4, 2)),
        sa.Column('pillar_risk_mgmt',     sa.Numeric(4, 2)),
        sa.Column('pillar_metrics',       sa.Numeric(4, 2)),
        sa.Column('overall_maturity',     sa.Numeric(4, 2)),
        # Risk scores
        sa.Column('physical_risk_score',     sa.Numeric(6, 3)),
        sa.Column('transition_risk_score',   sa.Numeric(6, 3)),
        # Climate targets
        sa.Column('net_zero_target_year',    sa.Integer()),
        sa.Column('interim_target_2030_pct', sa.Numeric(6, 2)),
        # KPIs
        sa.Column('financed_emissions_tco2e',  sa.Numeric(18, 2)),
        sa.Column('green_asset_ratio_pct',     sa.Numeric(6, 2)),
        sa.Column('climate_var_1yr_hkd',       sa.Numeric(22, 2)),
        sa.Column('tcfd_disclosure_complete',  sa.Boolean(), server_default='false'),
        sa.Column('hkma_supervisory_rating',   sa.String(20)),   # 'Satisfactory' | 'Needs Improvement' | 'Unsatisfactory'
        sa.Column('notes',                     sa.Text()),
        sa.Column('created_at',                sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        'hkma_stress_scenarios',
        sa.Column('id',                   sa.String(36), primary_key=True, default=str(uuid.uuid4())),
        sa.Column('entity_id',            sa.String(36), sa.ForeignKey('hkma_entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('scenario_name',        sa.String(100), nullable=False),   # 'Below2C' | '2-3C' | 'Above3C'
        sa.Column('scenario_type',        sa.String(50)),                    # 'transition' | 'physical' | 'combined'
        sa.Column('warming_pathway',      sa.String(20)),                    # '<2°C' | '2–3°C' | '>3°C'
        sa.Column('time_horizon',         sa.String(20)),                    # '2030' | '2050'
        sa.Column('sector',               sa.String(100)),
        sa.Column('credit_loss_pct',      sa.Numeric(8, 4)),
        sa.Column('pd_change_bps',        sa.Numeric(8, 2)),
        sa.Column('lgd_change_bps',       sa.Numeric(8, 2)),
        sa.Column('nii_impact_hkd_mn',    sa.Numeric(18, 2)),
        sa.Column('car_impact_bps',       sa.Numeric(8, 2)),               # Capital Adequacy Ratio impact
        sa.Column('methodology',          sa.String(100)),                  # e.g. 'NGFS v3 + HKMA overlay'
        sa.Column('created_at',           sa.DateTime(), server_default=sa.func.now()),
    )

    # ── Bank of Japan climate scenarios ────────────────────────────────────
    op.create_table(
        'boj_entity_assessments',
        sa.Column('id',              sa.String(36), primary_key=True, default=str(uuid.uuid4())),
        sa.Column('entity_name',     sa.String(255), nullable=False),
        sa.Column('entity_type',     sa.String(50)),   # 'bank' | 'insurer' | 'corporate'
        sa.Column('country_code',    sa.String(10), server_default='JP'),
        sa.Column('boj_lei',         sa.String(30)),
        sa.Column('total_assets_jpy',sa.Numeric(22, 2)),
        sa.Column('reporting_year',  sa.Integer()),
        sa.Column('created_at',      sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at',      sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        'boj_scenario_results',
        sa.Column('id',                    sa.String(36), primary_key=True, default=str(uuid.uuid4())),
        sa.Column('entity_id',             sa.String(36), sa.ForeignKey('boj_entity_assessments.id', ondelete='CASCADE'), nullable=False),
        # Scenario dimensions
        sa.Column('scenario_name',         sa.String(100), nullable=False),
        sa.Column('scenario_type',         sa.String(50)),   # 'transition' | 'physical'
        sa.Column('warming_pathway',       sa.String(20)),   # '1.5C' | '2C' | '3C' | '4C'
        sa.Column('time_horizon',          sa.String(10)),   # '2030' | '2050' | '2100'
        sa.Column('sector',                sa.String(100)),  # GICS sector
        # Credit risk impacts
        sa.Column('pd_change_bps',         sa.Numeric(10, 3)),
        sa.Column('lgd_change_bps',        sa.Numeric(10, 3)),
        sa.Column('credit_loss_ratio_pct', sa.Numeric(8, 4)),
        sa.Column('ecl_change_jpy_bn',     sa.Numeric(18, 3)),
        # Earnings / capital
        sa.Column('roe_impact_pp',         sa.Numeric(8, 4)),   # Return on equity impact (percentage points)
        sa.Column('cet1_impact_pp',        sa.Numeric(8, 4)),   # CET1 ratio impact
        sa.Column('npl_ratio_change_pp',   sa.Numeric(8, 4)),   # Non-performing loan ratio change
        # Physical risk metrics
        sa.Column('physical_damage_jpy_bn',sa.Numeric(18, 3)),
        sa.Column('stranded_asset_ratio_pct', sa.Numeric(8, 4)),
        # Methodology
        sa.Column('boj_scenario_version',  sa.String(20)),   # e.g. '2023-Exercise'
        sa.Column('model_type',            sa.String(100)),  # 'Macro-financial' | 'Bottom-up'
        sa.Column('created_at',            sa.DateTime(), server_default=sa.func.now()),
    )

    # ── ASEAN Taxonomy v3 ───────────────────────────────────────────────────
    op.create_table(
        'asean_entities',
        sa.Column('id',              sa.String(36), primary_key=True, default=str(uuid.uuid4())),
        sa.Column('entity_name',     sa.String(255), nullable=False),
        sa.Column('entity_type',     sa.String(50)),
        sa.Column('country_code',    sa.String(10), nullable=False),   # SG | MY | TH | ID | PH | VN | MM | BN | LA | KH
        sa.Column('sector',          sa.String(100)),
        sa.Column('total_assets_usd',sa.Numeric(22, 2)),
        sa.Column('reporting_year',  sa.Integer()),
        sa.Column('created_at',      sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at',      sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        'asean_taxonomy_activities',
        sa.Column('id',                  sa.String(36), primary_key=True, default=str(uuid.uuid4())),
        sa.Column('entity_id',           sa.String(36), sa.ForeignKey('asean_entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('assessment_date',     sa.Date()),
        sa.Column('reporting_year',      sa.Integer()),
        # Activity classification
        sa.Column('activity_name',       sa.String(255), nullable=False),
        sa.Column('activity_code',       sa.String(50)),
        sa.Column('focus_area',          sa.String(100)),   # 'Climate Change Mitigation' | 'Climate Change Adaptation' | 'Protection of Healthy Ecosystems' | 'Resource Resilience' | 'Transition to Circular Economy'
        sa.Column('sector',              sa.String(100)),
        # Tier classification — ASEAN Taxonomy has Foundation + Plus tiers
        sa.Column('tier',                sa.String(20)),    # 'Foundation' | 'Plus'
        sa.Column('traffic_light',       sa.String(10)),    # 'Green' | 'Amber' | 'Red'
        # Thresholds
        sa.Column('substantial_contribution_met', sa.Boolean(), server_default='false'),
        sa.Column('dnsh_met',            sa.Boolean(), server_default='false'),   # Do No Significant Harm
        sa.Column('social_safeguards_met', sa.Boolean(), server_default='false'),
        sa.Column('minimum_safeguards_met', sa.Boolean(), server_default='false'),
        # DNSh criteria details
        sa.Column('dnsh_criteria',       JSONB()),
        # Exposure
        sa.Column('exposure_usd',        sa.Numeric(18, 2)),
        sa.Column('eligible_pct',        sa.Numeric(6, 2)),
        sa.Column('aligned_pct',         sa.Numeric(6, 2)),
        # Country-specific guidance
        sa.Column('country_overlay',     JSONB()),
        sa.Column('notes',               sa.Text()),
        sa.Column('created_at',          sa.DateTime(), server_default=sa.func.now()),
    )

    # ── PBoC Green Finance ──────────────────────────────────────────────────
    op.create_table(
        'pboc_entities',
        sa.Column('id',              sa.String(36), primary_key=True, default=str(uuid.uuid4())),
        sa.Column('entity_name',     sa.String(255), nullable=False),
        sa.Column('entity_type',     sa.String(50)),   # 'bank' | 'securities' | 'insurer' | 'corporate'
        sa.Column('country_code',    sa.String(10), server_default='CN'),
        sa.Column('pboc_code',       sa.String(30)),   # PBOC registration code
        sa.Column('total_assets_cny',sa.Numeric(22, 2)),
        sa.Column('reporting_year',  sa.Integer()),
        sa.Column('created_at',      sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at',      sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        'pboc_green_finance_records',
        sa.Column('id',                     sa.String(36), primary_key=True, default=str(uuid.uuid4())),
        sa.Column('entity_id',              sa.String(36), sa.ForeignKey('pboc_entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('assessment_date',        sa.Date()),
        sa.Column('reporting_year',         sa.Integer()),
        # Instrument classification
        sa.Column('instrument_type',        sa.String(50)),   # 'green_loan' | 'green_bond' | 'green_fund' | 'green_equity'
        sa.Column('instrument_name',        sa.String(255)),
        sa.Column('isin',                   sa.String(20)),
        # GBEPC 2021 — Green Bond Endorsed Project Catalogue classification
        sa.Column('gbepc_category',         sa.String(100)),  # e.g. 'Energy Conservation' | 'Clean Transportation' | 'Clean Energy' | 'Ecological Environment' | 'Green Upgrading' | 'Green Services'
        sa.Column('gbepc_subcategory',      sa.String(200)),
        sa.Column('gbepc_code',             sa.String(30)),
        # China Transition Finance Guidance alignment
        sa.Column('cgt_aligned',            sa.Boolean(), server_default='false'),  # Carbon-Guided Transition
        sa.Column('transition_category',    sa.String(100)),
        # Financial data
        sa.Column('outstanding_cny_mn',     sa.Numeric(18, 2)),
        sa.Column('outstanding_usd_mn',     sa.Numeric(18, 2)),
        sa.Column('maturity_date',          sa.Date()),
        sa.Column('coupon_rate_pct',        sa.Numeric(6, 4)),
        # Use of proceeds
        sa.Column('use_of_proceeds',        JSONB()),   # breakdown by GBEPC category
        sa.Column('co2_avoided_tco2e',      sa.Numeric(18, 2)),
        sa.Column('renewable_mwh',          sa.Numeric(18, 2)),
        # Verification
        sa.Column('external_review',        sa.Boolean(), server_default='false'),
        sa.Column('reviewer_name',          sa.String(255)),
        sa.Column('verification_standard',  sa.String(100)),   # 'CBI' | 'Sustainalytics' | 'ISS' | etc.
        sa.Column('green_label',            sa.String(50)),    # 'PBOC Certified' | 'SSE Green' | 'CBI Certified' | etc.
        # Ratios
        sa.Column('green_asset_ratio_pct',  sa.Numeric(6, 2)),
        sa.Column('green_credit_ratio_pct', sa.Numeric(6, 2)),
        sa.Column('notes',                  sa.Text()),
        sa.Column('created_at',             sa.DateTime(), server_default=sa.func.now()),
    )

    # ── Climate Bond Initiative (CBI) ───────────────────────────────────────
    op.create_table(
        'cbi_certified_bonds',
        sa.Column('id',                  sa.String(36), primary_key=True, default=str(uuid.uuid4())),
        sa.Column('isin',                sa.String(20), unique=True),
        sa.Column('bond_name',           sa.String(500)),
        sa.Column('issuer_name',         sa.String(255)),
        sa.Column('issuer_country',      sa.String(10)),
        sa.Column('issuer_type',         sa.String(50)),   # 'corporate' | 'sovereign' | 'municipality' | 'fin_institution' | 'development_bank'
        sa.Column('sector',              sa.String(100)),
        # Amounts
        sa.Column('amount_usd_mn',       sa.Numeric(18, 2)),
        sa.Column('currency',            sa.String(10)),
        sa.Column('amount_local_mn',     sa.Numeric(18, 2)),
        # Dates
        sa.Column('issue_date',          sa.Date()),
        sa.Column('maturity_date',       sa.Date()),
        # CBI classification
        sa.Column('cbi_label',           sa.String(100)),   # 'CBI Certified' | 'CBI Verified' | 'Climate Aligned'
        sa.Column('cbi_taxonomy_sector', sa.String(200)),   # CBI taxonomy sector (energy, transport, water, etc.)
        sa.Column('certification_date',  sa.Date()),
        sa.Column('certification_expiry',sa.Date()),
        sa.Column('verifier_name',       sa.String(255)),
        # Use of proceeds
        sa.Column('use_of_proceeds',     JSONB()),          # {'energy': 45.0, 'transport': 30.0, ...}
        sa.Column('uop_categories',      JSONB()),          # list of CBI UoP categories
        # Impact metrics
        sa.Column('co2_avoided_tco2e',   sa.Numeric(18, 2)),
        sa.Column('renewable_mwh',       sa.Numeric(18, 2)),
        sa.Column('green_buildings_sqm', sa.Numeric(18, 2)),
        # Compliance
        sa.Column('icma_gbp_aligned',    sa.Boolean(), server_default='false'),   # ICMA Green Bond Principles
        sa.Column('eu_gbr_aligned',      sa.Boolean(), server_default='false'),   # EU Green Bond Regulation
        sa.Column('paris_aligned',       sa.Boolean(), server_default='false'),
        # Data provenance
        sa.Column('data_source',         sa.String(100), server_default='cbi_api'),
        sa.Column('last_fetched_at',     sa.DateTime()),
        sa.Column('created_at',          sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at',          sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        'cbi_market_snapshots',
        sa.Column('id',                   sa.String(36), primary_key=True, default=str(uuid.uuid4())),
        sa.Column('snapshot_date',        sa.Date(), nullable=False),
        sa.Column('snapshot_type',        sa.String(50), server_default='daily'),  # 'daily' | 'monthly' | 'annual'
        # Issuance totals (cumulative, USD bn)
        sa.Column('total_issuance_usd_bn',sa.Numeric(12, 2)),
        sa.Column('green_usd_bn',         sa.Numeric(12, 2)),
        sa.Column('social_usd_bn',        sa.Numeric(12, 2)),
        sa.Column('sustainability_usd_bn',sa.Numeric(12, 2)),
        sa.Column('sll_usd_bn',           sa.Numeric(12, 2)),   # Sustainability-Linked Loans
        sa.Column('slb_usd_bn',           sa.Numeric(12, 2)),   # Sustainability-Linked Bonds
        sa.Column('transition_usd_bn',    sa.Numeric(12, 2)),
        sa.Column('cbi_certified_usd_bn', sa.Numeric(12, 2)),
        sa.Column('cbi_certified_pct',    sa.Numeric(6, 2)),
        # Issuance by country (top 20) — JSONB: {'US': 123.4, 'CN': 89.2, ...}
        sa.Column('by_country',           JSONB()),
        # Issuance by sector
        sa.Column('by_sector',            JSONB()),
        # Issuance by issuer type
        sa.Column('by_issuer_type',       JSONB()),
        # YTD figures
        sa.Column('ytd_issuance_usd_bn',  sa.Numeric(12, 2)),
        sa.Column('ytd_deal_count',       sa.Integer()),
        # Deal feed — list of recent deals
        sa.Column('recent_deals',         JSONB()),   # list of {isin, issuer, amount, label, date, sector}
        sa.Column('data_source',          sa.String(100), server_default='cbi_api'),
        sa.Column('fetched_at',           sa.DateTime(), server_default=sa.func.now()),
        sa.Column('created_at',           sa.DateTime(), server_default=sa.func.now()),
    )

    # ── Indexes ─────────────────────────────────────────────────────────────
    op.create_index('ix_hkma_entity_type',         'hkma_entities',              ['entity_type'])
    op.create_index('ix_hkma_assessments_entity',  'hkma_climate_assessments',   ['entity_id'])
    op.create_index('ix_hkma_stress_entity',       'hkma_stress_scenarios',      ['entity_id', 'scenario_name'])
    op.create_index('ix_boj_entity_type',          'boj_entity_assessments',     ['entity_type', 'country_code'])
    op.create_index('ix_boj_results_entity',       'boj_scenario_results',       ['entity_id', 'scenario_type', 'time_horizon'])
    op.create_index('ix_asean_entity_country',     'asean_entities',             ['country_code'])
    op.create_index('ix_asean_taxonomy_entity',    'asean_taxonomy_activities',  ['entity_id', 'traffic_light'])
    op.create_index('ix_asean_taxonomy_tier',      'asean_taxonomy_activities',  ['tier', 'focus_area'])
    op.create_index('ix_pboc_entity_type',         'pboc_entities',              ['entity_type'])
    op.create_index('ix_pboc_green_entity',        'pboc_green_finance_records', ['entity_id', 'instrument_type'])
    op.create_index('ix_pboc_gbepc',               'pboc_green_finance_records', ['gbepc_category'])
    op.create_index('ix_cbi_bonds_issuer_country', 'cbi_certified_bonds',        ['issuer_country'])
    op.create_index('ix_cbi_bonds_label',          'cbi_certified_bonds',        ['cbi_label'])
    op.create_index('ix_cbi_bonds_sector',         'cbi_certified_bonds',        ['cbi_taxonomy_sector'])
    op.create_index('ix_cbi_snapshots_date',       'cbi_market_snapshots',       ['snapshot_date'])


def downgrade() -> None:
    # Drop indexes
    for idx, tbl in [
        ('ix_cbi_snapshots_date',       'cbi_market_snapshots'),
        ('ix_cbi_bonds_sector',         'cbi_certified_bonds'),
        ('ix_cbi_bonds_label',          'cbi_certified_bonds'),
        ('ix_cbi_bonds_issuer_country', 'cbi_certified_bonds'),
        ('ix_pboc_gbepc',               'pboc_green_finance_records'),
        ('ix_pboc_green_entity',        'pboc_green_finance_records'),
        ('ix_pboc_entity_type',         'pboc_entities'),
        ('ix_asean_taxonomy_tier',      'asean_taxonomy_activities'),
        ('ix_asean_taxonomy_entity',    'asean_taxonomy_activities'),
        ('ix_asean_entity_country',     'asean_entities'),
        ('ix_boj_results_entity',       'boj_scenario_results'),
        ('ix_boj_entity_type',          'boj_entity_assessments'),
        ('ix_hkma_stress_entity',       'hkma_stress_scenarios'),
        ('ix_hkma_assessments_entity',  'hkma_climate_assessments'),
        ('ix_hkma_entity_type',         'hkma_entities'),
    ]:
        op.drop_index(idx, table_name=tbl)

    # Drop tables (reverse order of FKs)
    op.drop_table('cbi_market_snapshots')
    op.drop_table('cbi_certified_bonds')
    op.drop_table('pboc_green_finance_records')
    op.drop_table('pboc_entities')
    op.drop_table('asean_taxonomy_activities')
    op.drop_table('asean_entities')
    op.drop_table('boj_scenario_results')
    op.drop_table('boj_entity_assessments')
    op.drop_table('hkma_stress_scenarios')
    op.drop_table('hkma_climate_assessments')
    op.drop_table('hkma_entities')
