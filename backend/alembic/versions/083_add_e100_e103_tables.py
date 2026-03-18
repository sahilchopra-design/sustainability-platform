"""Add E100-E103 tables: Multi-Regulatory Stress Test Orchestrator, Sustainable Supply Chain Finance, CSRD Double Materiality, Temperature Alignment

Revision ID: 083
Revises: 082
Create Date: 2026-03-18
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '083'
down_revision = '082'
branch_labels = None
depends_on = None


def upgrade():
    # ─── E100: Multi-Regulatory Climate Stress Test Orchestrator ───────────────
    # ECB/EBA/BoE/APRA/MAS/RBI unified stress test runner — NGFS Phase IV
    op.create_table('stress_test_orchestrations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('entity_id', sa.String(36), nullable=False),
        sa.Column('entity_name', sa.String(255), nullable=False),
        sa.Column('entity_type', sa.String(50)),          # bank/insurer/pension/asset_manager
        sa.Column('jurisdiction', sa.String(10)),          # EU/UK/AU/SG/IN/US
        sa.Column('regulatory_framework', sa.String(50)), # ECB/EBA/BoE/APRA/MAS/RBI
        sa.Column('ngfs_phase', sa.String(10)),            # IV (2024)
        sa.Column('scenarios_run', postgresql.JSONB),      # list of scenario IDs run
        sa.Column('total_exposure_bn', sa.Numeric(18,4)),
        sa.Column('baseline_cet1_pct', sa.Numeric(8,4)),
        sa.Column('stressed_cet1_pct', sa.Numeric(8,4)),
        sa.Column('cet1_depletion_pp', sa.Numeric(8,4)),
        sa.Column('pass_threshold_pct', sa.Numeric(8,4)),
        sa.Column('stress_test_pass', sa.Boolean),
        sa.Column('physical_risk_el_bn', sa.Numeric(18,4)),
        sa.Column('transition_risk_el_bn', sa.Numeric(18,4)),
        sa.Column('macro_gdp_shock_pct', sa.Numeric(8,4)),
        sa.Column('macro_unemployment_shock_pp', sa.Numeric(8,4)),
        sa.Column('sector_breakdown', postgresql.JSONB),
        sa.Column('pd_migration_matrix', postgresql.JSONB),
        sa.Column('lgd_uplift_by_sector', postgresql.JSONB),
        sa.Column('regulatory_submission_ready', sa.Boolean),
        sa.Column('submission_template', postgresql.JSONB),
        sa.Column('assessment_date', sa.Date),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table('stress_test_scenario_results',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('orchestration_id', sa.String(36), nullable=False),
        sa.Column('scenario_id', sa.String(50)),           # net_zero_2050/delayed_transition/hot_house/below_2c/ndp
        sa.Column('scenario_name', sa.String(200)),
        sa.Column('time_horizon_year', sa.Integer),        # 2025/2030/2035/2040/2050
        sa.Column('expected_loss_bn', sa.Numeric(18,4)),
        sa.Column('pd_uplift_pct', sa.Numeric(8,4)),
        sa.Column('lgd_uplift_pct', sa.Numeric(8,4)),
        sa.Column('carbon_price_usd', sa.Numeric(10,2)),
        sa.Column('gdp_deviation_pct', sa.Numeric(8,4)),
        sa.Column('temp_rise_c', sa.Numeric(6,3)),
        sa.Column('physical_risk_el_bn', sa.Numeric(18,4)),
        sa.Column('transition_risk_el_bn', sa.Numeric(18,4)),
        sa.Column('climate_var_pct', sa.Numeric(8,4)),
        sa.Column('sector_results', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ─── E101: Sustainable Supply Chain Finance Engine ─────────────────────────
    # SSCF/SCF ESG incentives — OECD DDG / CSDDD supplier cascade / LMA SLL Principles
    op.create_table('sscf_assessments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('buyer_entity_id', sa.String(36)),
        sa.Column('buyer_name', sa.String(255), nullable=False),
        sa.Column('programme_type', sa.String(50)),        # reverse_factoring/dynamic_discounting/supply_chain_loan/scf_platform
        sa.Column('programme_size_mn', sa.Numeric(18,4)),
        sa.Column('currency', sa.String(3)),
        sa.Column('supplier_count', sa.Integer),
        sa.Column('tier_1_supplier_count', sa.Integer),
        sa.Column('tier_2_plus_count', sa.Integer),
        sa.Column('sscf_framework', sa.String(50)),        # LMA_SSCF/ICC_SCF/GSCFF
        sa.Column('esg_kpi_count', sa.Integer),
        sa.Column('kpi_categories', postgresql.JSONB),     # GHG/water/labour/safety/diversity
        sa.Column('spt_threshold_discount_bps', sa.Numeric(8,2)), # margin ratchet on meeting KPIs
        sa.Column('spt_penalty_bps', sa.Numeric(8,2)),
        sa.Column('oecd_ddg_step', sa.Integer),            # 1-5 achieved
        sa.Column('csddd_cascade_compliant', sa.Boolean),
        sa.Column('scope3_cat1_covered', sa.Boolean),
        sa.Column('supplier_esg_avg_score', sa.Numeric(8,4)),
        sa.Column('high_risk_suppliers_pct', sa.Numeric(8,4)),
        sa.Column('cahra_suppliers_pct', sa.Numeric(8,4)),
        sa.Column('conflict_mineral_exposure', sa.Boolean),
        sa.Column('overall_sscf_score', sa.Numeric(8,4)),
        sa.Column('sscf_eligible', sa.Boolean),
        sa.Column('assessment_date', sa.Date),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table('supplier_esg_scorecards',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('sscf_id', sa.String(36), nullable=False),
        sa.Column('supplier_name', sa.String(255)),
        sa.Column('supplier_country', sa.String(3)),
        sa.Column('tier', sa.Integer),                     # 1/2/3
        sa.Column('nace_code', sa.String(10)),
        sa.Column('annual_spend_mn', sa.Numeric(18,4)),
        sa.Column('ghg_intensity', sa.Numeric(12,4)),
        sa.Column('water_intensity', sa.Numeric(12,4)),
        sa.Column('labour_risk_score', sa.Numeric(8,4)),
        sa.Column('safety_ltifr', sa.Numeric(10,6)),
        sa.Column('diversity_score', sa.Numeric(8,4)),
        sa.Column('csddd_adverse_impacts', postgresql.JSONB),
        sa.Column('ilo_compliance', postgresql.JSONB),
        sa.Column('conflict_mineral_flag', sa.Boolean),
        sa.Column('cahra_flag', sa.Boolean),
        sa.Column('overall_esg_score', sa.Numeric(8,4)),
        sa.Column('risk_tier', sa.String(20)),             # low/medium/high/critical
        sa.Column('discount_rate_bps', sa.Numeric(8,2)),   # ESG-incentivised rate
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ─── E102: CSRD Double Materiality Assessment Engine ───────────────────────
    # ESRS 1 — impact materiality + financial materiality — IRO identification
    op.create_table('double_materiality_assessments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('entity_id', sa.String(36)),
        sa.Column('entity_name', sa.String(255), nullable=False),
        sa.Column('nace_sector', sa.String(10)),
        sa.Column('employee_count', sa.Integer),
        sa.Column('csrd_wave', sa.Integer),                # 1/2/3/4
        sa.Column('reporting_year', sa.Integer),
        sa.Column('esrs_topics_assessed', sa.Integer),
        sa.Column('material_topics_count', sa.Integer),
        sa.Column('impact_material_count', sa.Integer),
        sa.Column('financial_material_count', sa.Integer),
        sa.Column('double_material_count', sa.Integer),
        sa.Column('e1_climate_material', sa.Boolean),
        sa.Column('e2_pollution_material', sa.Boolean),
        sa.Column('e3_water_material', sa.Boolean),
        sa.Column('e4_biodiversity_material', sa.Boolean),
        sa.Column('e5_circular_material', sa.Boolean),
        sa.Column('s1_workforce_material', sa.Boolean),
        sa.Column('s2_workers_chain_material', sa.Boolean),
        sa.Column('s3_communities_material', sa.Boolean),
        sa.Column('s4_consumers_material', sa.Boolean),
        sa.Column('g1_conduct_material', sa.Boolean),
        sa.Column('stakeholder_engagement_complete', sa.Boolean),
        sa.Column('iro_identification_complete', sa.Boolean),
        sa.Column('materiality_matrix', postgresql.JSONB),
        sa.Column('esrs_omissions', postgresql.JSONB),
        sa.Column('completeness_score', sa.Numeric(8,4)),
        sa.Column('assurance_ready', sa.Boolean),
        sa.Column('assessment_date', sa.Date),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table('csrd_iro_registry',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('dma_id', sa.String(36), nullable=False),
        sa.Column('iro_type', sa.String(20)),               # impact/risk/opportunity
        sa.Column('esrs_topic', sa.String(10)),             # E1/E2/E3/E4/E5/S1/S2/S3/S4/G1
        sa.Column('iro_description', sa.Text),
        sa.Column('time_horizon', sa.String(20)),           # short/medium/long
        sa.Column('value_chain_position', sa.String(30)),   # own_operations/upstream/downstream
        sa.Column('impact_likelihood', sa.Numeric(8,4)),
        sa.Column('impact_severity', sa.Numeric(8,4)),
        sa.Column('impact_scale', sa.Numeric(8,4)),
        sa.Column('impact_scope', sa.Numeric(8,4)),
        sa.Column('impact_irremediable', sa.Boolean),
        sa.Column('financial_likelihood', sa.Numeric(8,4)),
        sa.Column('financial_magnitude', sa.Numeric(8,4)),
        sa.Column('impact_material', sa.Boolean),
        sa.Column('financial_material', sa.Boolean),
        sa.Column('double_material', sa.Boolean),
        sa.Column('linked_policy', sa.Text),
        sa.Column('linked_target', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ─── E103: Financed Emissions Temperature Alignment Engine ─────────────────
    # PCAF + SBTi FI + PACTA — portfolio implied temperature rise (ITR)
    op.create_table('temperature_alignment_assessments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('portfolio_id', sa.String(36)),
        sa.Column('portfolio_name', sa.String(255), nullable=False),
        sa.Column('fi_type', sa.String(50)),               # bank/insurer/asset_manager/pension
        sa.Column('total_aum_bn', sa.Numeric(18,4)),
        sa.Column('methodology', sa.String(50)),           # PCAF_SBTI/PACTA/WACI/SDA
        sa.Column('base_year', sa.Integer),
        sa.Column('target_year', sa.Integer),
        sa.Column('portfolio_itr_c', sa.Numeric(6,3)),     # implied temperature rise
        sa.Column('waci_tco2_mn_revenue', sa.Numeric(12,4)),
        sa.Column('scope1_financed_mtco2', sa.Numeric(18,4)),
        sa.Column('scope2_financed_mtco2', sa.Numeric(18,4)),
        sa.Column('scope3_financed_mtco2', sa.Numeric(18,4)),
        sa.Column('total_financed_mtco2', sa.Numeric(18,4)),
        sa.Column('portfolio_coverage_pct', sa.Numeric(8,4)),
        sa.Column('data_quality_score', sa.Numeric(8,4)),  # PCAF DQS 1-5
        sa.Column('paris_aligned', sa.Boolean),
        sa.Column('sbti_fi_target_set', sa.Boolean),
        sa.Column('sbti_near_term_yr', sa.Integer),
        sa.Column('sbti_long_term_yr', sa.Integer),
        sa.Column('reduction_required_pct', sa.Numeric(8,4)),
        sa.Column('reduction_achieved_pct', sa.Numeric(8,4)),
        sa.Column('on_track', sa.Boolean),
        sa.Column('engagement_priority_assets', postgresql.JSONB),
        sa.Column('sector_temperature_breakdown', postgresql.JSONB),
        sa.Column('pacta_results', postgresql.JSONB),
        sa.Column('assessment_date', sa.Date),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table('sector_alignment_targets',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('assessment_id', sa.String(36), nullable=False),
        sa.Column('sector', sa.String(50)),                # power/automotive/steel/cement/oil_gas/aviation/shipping/real_estate
        sa.Column('nace_codes', postgresql.JSONB),
        sa.Column('sector_exposure_bn', sa.Numeric(18,4)),
        sa.Column('sector_exposure_pct', sa.Numeric(8,4)),
        sa.Column('sector_itr_c', sa.Numeric(6,3)),
        sa.Column('sector_waci', sa.Numeric(12,4)),
        sa.Column('sbti_pathway_pct_reduction_2030', sa.Numeric(8,4)),
        sa.Column('sbti_pathway_pct_reduction_2050', sa.Numeric(8,4)),
        sa.Column('actual_reduction_pct', sa.Numeric(8,4)),
        sa.Column('alignment_gap_pp', sa.Numeric(8,4)),
        sa.Column('aligned', sa.Boolean),
        sa.Column('engagement_priority', sa.String(20)),   # high/medium/low
        sa.Column('pacta_aligned_pct', sa.Numeric(8,4)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table('sector_alignment_targets')
    op.drop_table('temperature_alignment_assessments')
    op.drop_table('csrd_iro_registry')
    op.drop_table('double_materiality_assessments')
    op.drop_table('supplier_esg_scorecards')
    op.drop_table('sscf_assessments')
    op.drop_table('stress_test_scenario_results')
    op.drop_table('stress_test_orchestrations')
