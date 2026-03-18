"""Add E96-E99 tables: VCM Integrity, Social Taxonomy, Green Hydrogen, Transition Finance

Revision ID: 082
Revises: 081
Create Date: 2026-03-17

Engines:
  E96 — Voluntary Carbon Market Integrity (ICVCM CCP 2023 · VCMI Claims · Oxford Offsetting Principles · Verra/GS/ACR/CAR registries)
  E97 — EU Social Taxonomy & Human Rights DD (EU SocTax 2022/2023 · ILO 8 core conventions · UNGP HRDD · CSDDD Annex I/II social · Decent Work)
  E98 — Green Hydrogen & RFNBO Compliance (EU Del. Act 2023/1184 · GHG < 3.38 kgCO2/kgH2 · Additionality · Temporal/Geo correlation · IEA)
  E99 — Transition Finance Credibility (GFANZ/TPT · SBTi validation · Race to Zero · TNFD LEAP nature integration · Portfolio temperature alignment)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '082'
down_revision = '081'
branch_labels = None
depends_on = None


def upgrade():
    # ── E96: Voluntary Carbon Market Integrity ─────────────────────────────
    op.create_table(
        'vcm_integrity_assessments',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('assessment_ref', sa.String(64), nullable=False, unique=True),
        sa.Column('project_id', sa.String(64)),
        sa.Column('registry', sa.String(32)),           # verra_vcs | gold_standard | acr | car | art6_itmo
        sa.Column('methodology', sa.String(64)),
        sa.Column('project_type', sa.String(64)),       # afolu | redd+ | arr | blue_carbon | cookstoves | ...
        sa.Column('vintage_year', sa.Integer),
        sa.Column('volume_tco2e', sa.Numeric(18, 4)),
        sa.Column('price_usd_t', sa.Numeric(10, 4)),

        # ICVCM CCP scoring (10 criteria)
        sa.Column('ccp_scores', JSONB),                 # {criterion: score} for all 10
        sa.Column('ccp_composite', sa.Numeric(5, 4)),
        sa.Column('ccp_label_eligible', sa.Boolean),
        sa.Column('ccp_blocking_issues', JSONB),

        # VCMI Claims Code of Practice
        sa.Column('vcmi_claim_tier', sa.String(32)),    # no_claim | silver | gold | platinum
        sa.Column('vcmi_score', sa.Numeric(5, 4)),
        sa.Column('vcmi_sbti_aligned', sa.Boolean),
        sa.Column('vcmi_residual_emissions_pct', sa.Numeric(5, 4)),

        # Oxford Offsetting Principles (4)
        sa.Column('oxford_score', sa.Numeric(5, 4)),
        sa.Column('oxford_principle_scores', JSONB),    # {p1: score, p2: score, p3: score, p4: score}
        sa.Column('oxford_shift_to_removal', sa.Boolean),
        sa.Column('oxford_storage_type', sa.String(32)), # geological | biological | ocean | technological

        # Integrity flags
        sa.Column('permanence_risk', sa.String(16)),    # low | medium | high | critical
        sa.Column('additionality_score', sa.Numeric(5, 4)),
        sa.Column('leakage_risk_pct', sa.Numeric(5, 4)),
        sa.Column('mrvv_quality', sa.String(16)),       # high | medium | low
        sa.Column('corsia_eligible', sa.Boolean),
        sa.Column('article6_eligible', sa.Boolean),
        sa.Column('integrity_tier', sa.String(8)),      # A | B | C | D

        sa.Column('recommendations', JSONB),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        'carbon_credit_registry',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('registry_name', sa.String(32), nullable=False),  # verra | gold_standard | acr | car | art6
        sa.Column('serial_number', sa.String(128)),
        sa.Column('project_id', sa.String(64)),
        sa.Column('vintage_start', sa.Date),
        sa.Column('vintage_end', sa.Date),
        sa.Column('quantity_issued', sa.Numeric(18, 4)),
        sa.Column('quantity_retired', sa.Numeric(18, 4)),
        sa.Column('retirement_reason', sa.String(64)),
        sa.Column('retirement_beneficiary', sa.String(128)),
        sa.Column('country_of_origin', sa.String(3)),
        sa.Column('ccp_label', sa.Boolean),
        sa.Column('corsia_eligible', sa.Boolean),
        sa.Column('metadata', JSONB),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # ── E97: EU Social Taxonomy & Human Rights DD ─────────────────────────
    op.create_table(
        'social_taxonomy_assessments',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('assessment_ref', sa.String(64), nullable=False, unique=True),
        sa.Column('entity_name', sa.String(256)),
        sa.Column('entity_lei', sa.String(20)),
        sa.Column('nace_code', sa.String(8)),
        sa.Column('sector', sa.String(64)),

        # EU Social Taxonomy 3 objectives
        sa.Column('obj1_decent_work_score', sa.Numeric(5, 4)),     # Obj 1: Adequate wages, H&S, job security
        sa.Column('obj2_access_services_score', sa.Numeric(5, 4)), # Obj 2: Healthcare, housing, education
        sa.Column('obj3_inclusive_communities', sa.Numeric(5, 4)), # Obj 3: Inclusive growth, development
        sa.Column('social_taxonomy_composite', sa.Numeric(5, 4)),
        sa.Column('social_taxonomy_eligible', sa.Boolean),
        sa.Column('social_taxonomy_aligned', sa.Boolean),
        sa.Column('social_dnsh_pass', sa.Boolean),

        # ILO 8 core conventions (scoring per convention)
        sa.Column('ilo_convention_scores', JSONB),     # {C029, C087, C098, C100, C105, C111, C138, C182}
        sa.Column('ilo_composite', sa.Numeric(5, 4)),
        sa.Column('ilo_violations', JSONB),

        # CSDDD Annex I/II social adverse impacts
        sa.Column('csddd_social_impacts', JSONB),      # [{impact_id, severity, likelihood, priority}]
        sa.Column('csddd_social_score', sa.Numeric(5, 4)),
        sa.Column('csddd_hrdd_compliance', sa.String(16)),  # compliant | partial | non_compliant

        # UNGP HRDD (6 steps)
        sa.Column('ungp_hrdd_scores', JSONB),          # {policy_commitment, due_diligence, remediation, ...}
        sa.Column('ungp_composite', sa.Numeric(5, 4)),

        # Decent Work Framework (ILO/SDG 8)
        sa.Column('living_wage_compliance', sa.Boolean),
        sa.Column('gender_pay_gap_pct', sa.Numeric(5, 2)),
        sa.Column('union_coverage_pct', sa.Numeric(5, 2)),
        sa.Column('injury_rate_per_200k', sa.Numeric(8, 4)),
        sa.Column('child_labour_flag', sa.Boolean),
        sa.Column('forced_labour_flag', sa.Boolean),

        sa.Column('gap_analysis', JSONB),
        sa.Column('action_plan', JSONB),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        'supply_chain_hrdd_assessments',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('assessment_ref', sa.String(64), nullable=False, unique=True),
        sa.Column('company_name', sa.String(256)),
        sa.Column('supply_chain_tier', sa.Integer),     # 1 | 2 | 3
        sa.Column('supplier_country', sa.String(3)),
        sa.Column('sector', sa.String(64)),
        sa.Column('ungp_risk_tier', sa.String(16)),     # high | medium | low
        sa.Column('oecd_ddg_step_scores', JSONB),       # steps 1-5
        sa.Column('ilo_core_breaches', JSONB),
        sa.Column('remediation_actions', JSONB),
        sa.Column('verification_status', sa.String(16)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # ── E98: Green Hydrogen & RFNBO Compliance ─────────────────────────────
    op.create_table(
        'green_hydrogen_assessments',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('assessment_ref', sa.String(64), nullable=False, unique=True),
        sa.Column('facility_name', sa.String(256)),
        sa.Column('country', sa.String(3)),
        sa.Column('production_capacity_mw', sa.Numeric(12, 2)),
        sa.Column('electrolyser_type', sa.String(32)),  # pem | alk | soec | aem
        sa.Column('electricity_source', sa.String(32)), # grid | ppa_wind | ppa_solar | dedicated_re | nuclear

        # EU Del. Act 2023/1184 RFNBO criteria
        sa.Column('rfnbo_eligible', sa.Boolean),
        sa.Column('ghg_intensity_kgco2_per_kgh2', sa.Numeric(8, 4)),  # threshold: < 3.38
        sa.Column('ghg_threshold_met', sa.Boolean),
        sa.Column('additionality_met', sa.Boolean),
        sa.Column('temporal_correlation_met', sa.Boolean),   # hourly matching from 2030
        sa.Column('geographical_correlation_met', sa.Boolean), # same bidding zone
        sa.Column('rfnbo_composite_score', sa.Numeric(5, 4)),

        # REPowerEU / EU Hydrogen Strategy targets
        sa.Column('repowereu_target_alignment', sa.String(32)), # on_track | lagging | not_aligned
        sa.Column('domestic_production_share', sa.Numeric(5, 4)), # vs 10Mt target by 2030
        sa.Column('import_share', sa.Numeric(5, 4)),

        # IEA hydrogen economics
        sa.Column('lcoh_usd_per_kgh2', sa.Numeric(8, 4)),     # levelised cost of hydrogen
        sa.Column('electrolyser_capex_usd_kw', sa.Numeric(10, 2)),
        sa.Column('capacity_factor', sa.Numeric(5, 4)),
        sa.Column('stack_lifetime_hrs', sa.Integer),
        sa.Column('efficiency_kwh_per_kgh2', sa.Numeric(6, 2)),

        # H2 contract for difference (H2 CfD)
        sa.Column('h2cfd_eligible', sa.Boolean),
        sa.Column('h2cfd_strike_price_usd_kg', sa.Numeric(8, 4)),
        sa.Column('h2cfd_reference_price_usd_kg', sa.Numeric(8, 4)),
        sa.Column('h2cfd_support_duration_yrs', sa.Integer),

        # Certification
        sa.Column('certification_scheme', sa.String(32)),  # regreen | tuv_sud | dnv | bureau_veritas
        sa.Column('certification_status', sa.String(16)),

        sa.Column('recommendations', JSONB),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        'rfnbo_compliance_checks',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('assessment_ref', sa.String(64), nullable=False),
        sa.Column('check_date', sa.Date),
        sa.Column('electricity_source_verified', sa.Boolean),
        sa.Column('hourly_matching_evidence', sa.String(256)),
        sa.Column('ghg_audit_report_ref', sa.String(128)),
        sa.Column('certification_body', sa.String(64)),
        sa.Column('compliance_status', sa.String(16)),
        sa.Column('next_audit_date', sa.Date),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # ── E99: Transition Finance Credibility ───────────────────────────────
    op.create_table(
        'transition_finance_assessments',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('assessment_ref', sa.String(64), nullable=False, unique=True),
        sa.Column('entity_name', sa.String(256)),
        sa.Column('entity_lei', sa.String(20)),
        sa.Column('sector', sa.String(64)),
        sa.Column('nace_code', sa.String(8)),
        sa.Column('assessment_date', sa.Date),

        # GFANZ/TPT Transition Plan Credibility (6 elements)
        sa.Column('tpt_foundations_score', sa.Numeric(5, 4)),
        sa.Column('tpt_implementation_score', sa.Numeric(5, 4)),
        sa.Column('tpt_engagement_score', sa.Numeric(5, 4)),
        sa.Column('tpt_metrics_score', sa.Numeric(5, 4)),
        sa.Column('tpt_governance_score', sa.Numeric(5, 4)),
        sa.Column('tpt_finance_score', sa.Numeric(5, 4)),
        sa.Column('tpt_composite', sa.Numeric(5, 4)),
        sa.Column('tpt_quality_tier', sa.String(16)),        # initial | developing | advanced | leading

        # SBTi Validation Criteria (5 key criteria)
        sa.Column('sbti_near_term_validated', sa.Boolean),
        sa.Column('sbti_long_term_validated', sa.Boolean),
        sa.Column('sbti_net_zero_target', sa.Boolean),
        sa.Column('sbti_flag_sector', sa.Boolean),           # FLAG (forest, land, agriculture)
        sa.Column('sbti_1_5c_aligned', sa.Boolean),
        sa.Column('sbti_score', sa.Numeric(5, 4)),

        # Race to Zero (5 campaign criteria)
        sa.Column('rtz_pledge', sa.Boolean),
        sa.Column('rtz_plan', sa.Boolean),
        sa.Column('rtz_proceed', sa.Boolean),
        sa.Column('rtz_publish', sa.Boolean),
        sa.Column('rtz_account', sa.Boolean),
        sa.Column('rtz_score', sa.Numeric(5, 4)),
        sa.Column('rtz_membership', sa.String(64)),          # GFANZ | RE100 | EP100 | EV100 | etc.

        # Portfolio temperature alignment
        sa.Column('portfolio_temperature_c', sa.Numeric(4, 2)),
        sa.Column('waci_tco2e_per_m_revenue', sa.Numeric(10, 4)),
        sa.Column('engagement_coverage_pct', sa.Numeric(5, 4)),
        sa.Column('paris_aligned_assets_pct', sa.Numeric(5, 4)),

        # TNFD LEAP nature integration
        sa.Column('tnfd_leap_integrated', sa.Boolean),
        sa.Column('nature_dependencies_identified', sa.Boolean),
        sa.Column('nature_targets_set', sa.Boolean),
        sa.Column('sbtn_steps_completed', sa.Integer),        # 0-5

        # Transition instrument
        sa.Column('transition_instrument', sa.String(32)),   # transition_bond | SLL | TLF | blended | equity
        sa.Column('kpi_ambition_score', sa.Numeric(5, 4)),
        sa.Column('spt_calibration', sa.String(16)),         # ambitious | credible | insufficient

        sa.Column('credibility_score', sa.Numeric(5, 4)),
        sa.Column('credibility_tier', sa.String(16)),        # high | medium | low | greenwash_risk
        sa.Column('red_flags', JSONB),
        sa.Column('recommendations', JSONB),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        'net_zero_commitment_tracker',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('entity_name', sa.String(256)),
        sa.Column('entity_lei', sa.String(20)),
        sa.Column('commitment_date', sa.Date),
        sa.Column('target_year', sa.Integer),
        sa.Column('interim_target_2030', sa.Numeric(5, 2)),  # % reduction vs base year
        sa.Column('interim_target_2035', sa.Numeric(5, 2)),
        sa.Column('interim_target_2040', sa.Numeric(5, 2)),
        sa.Column('base_year', sa.Integer),
        sa.Column('base_year_emissions_tco2e', sa.Numeric(18, 4)),
        sa.Column('current_year_emissions_tco2e', sa.Numeric(18, 4)),
        sa.Column('scope_coverage', sa.String(16)),           # s1 | s1s2 | s1s2s3
        sa.Column('initiative_memberships', JSONB),           # [GFANZ, NZBA, NZAM, NZI, NZAOA, RE100 ...]
        sa.Column('status', sa.String(16)),                   # on_track | lagging | at_risk | breached
        sa.Column('last_verified', sa.Date),
        sa.Column('verification_body', sa.String(64)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table('net_zero_commitment_tracker')
    op.drop_table('transition_finance_assessments')
    op.drop_table('rfnbo_compliance_checks')
    op.drop_table('green_hydrogen_assessments')
    op.drop_table('supply_chain_hrdd_assessments')
    op.drop_table('social_taxonomy_assessments')
    op.drop_table('carbon_credit_registry')
    op.drop_table('vcm_integrity_assessments')
