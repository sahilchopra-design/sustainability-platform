"""
Add Regulatory Reporting Tables

Revision ID: 009_add_regulatory_tables
Revises: 008_add_sector_assessment_tables
Create Date: 2026-03-01

This migration adds tables for the Regulatory Reporting module:
- regulatory_entities         : Organisations subject to regulatory disclosure requirements
- sfdr_pai_disclosures        : SFDR Principal Adverse Impact (PAI) indicators (EU 2019/2088, RTS 2023)
- eu_taxonomy_assessments     : EU Taxonomy alignment assessments (EU 2020/852)
- eu_taxonomy_activities      : Per-activity taxonomy screening (technical screening criteria)
- tcfd_assessments            : TCFD recommended disclosures maturity scoring (TCFD 2023)
- csrd_readiness_assessments  : CSRD/ESRS readiness tracker with double materiality
- csrd_topic_assessments      : Per-ESRS-topic disclosure status and gap analysis
- issb_assessments            : ISSB IFRS S1 (General) + S2 (Climate) maturity assessments
- brsr_disclosures            : SEBI BRSR (Business Responsibility & Sustainability Report) disclosures
- brsr_principle_assessments  : Per-NVG-SEG principle readiness for BRSR
- sf_taxonomy_alignments      : Multi-jurisdiction sustainable finance taxonomy alignment tracker
- regulatory_action_plans     : Remediation / gap-closure action plans across all frameworks
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '009_add_regulatory_tables'
down_revision = '008_add_sector_assessment_tables'
branch_labels = None
depends_on = None


def upgrade():
    """Create regulatory reporting tables."""

    # -------------------------------------------------------------------------
    # 1. REGULATORY ENTITIES  (organisations subject to disclosure requirements)
    # -------------------------------------------------------------------------
    op.create_table(
        'regulatory_entities',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('legal_name', sa.String(255), nullable=False),
        sa.Column('lei', sa.String(20)),
        sa.Column('entity_type', sa.String(50), nullable=False),        # asset_manager | bank | insurer | pension_fund | corporate | nfrd_entity | listed_company
        sa.Column('jurisdiction', sa.String(3), nullable=False),        # ISO country code
        sa.Column('aum_gbp', sa.Numeric(18, 2)),                       # for financial entities
        sa.Column('annual_revenue_gbp', sa.Numeric(18, 2)),
        sa.Column('headcount', sa.Integer),
        sa.Column('is_listed', sa.Boolean, default=False),
        sa.Column('stock_exchange', sa.String(20)),
        sa.Column('market_cap_gbp', sa.Numeric(18, 2)),
        sa.Column('fiscal_year_end', sa.String(5)),                     # MM-DD

        # Applicable frameworks (checklist)
        sa.Column('applicable_frameworks', JSONB),                      # ['SFDR','EU_TAXONOMY','TCFD','CSRD','ISSB','BRSR','UK_TAXONOMY']

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.CheckConstraint("entity_type IN ('asset_manager','bank','insurer','pension_fund','corporate','nfrd_entity','listed_company','government','supra_national')", name='ck_reg_entities_type'),
    )
    op.create_index('ix_reg_entities_name', 'regulatory_entities', ['legal_name'])
    op.create_index('ix_reg_entities_type', 'regulatory_entities', ['entity_type'])
    op.create_index('ix_reg_entities_jurisdiction', 'regulatory_entities', ['jurisdiction'])

    # -------------------------------------------------------------------------
    # 2. SFDR PAI DISCLOSURES  (EU 2019/2088 + RTS 2023, Annex I)
    # -------------------------------------------------------------------------
    op.create_table(
        'sfdr_pai_disclosures',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_id', UUID(as_uuid=True), sa.ForeignKey('regulatory_entities.id', ondelete='SET NULL')),
        sa.Column('entity_name', sa.String(255), nullable=False),
        sa.Column('reporting_period_start', sa.Date, nullable=False),
        sa.Column('reporting_period_end', sa.Date, nullable=False),
        sa.Column('reference_date', sa.Date),                           # typically 31-Dec or quarter-end

        # Fund classification (for SFDR Article 6/8/9)
        sa.Column('sfdr_article', sa.SmallInteger, nullable=False),     # 6, 8, or 9
        sa.Column('is_pai_statement_published', sa.Boolean, default=False),
        sa.Column('number_of_investees', sa.Integer),
        sa.Column('portfolio_coverage_pct', sa.Numeric(5, 2)),          # % of portfolio with data

        # ---- MANDATORY PAI INDICATORS (Annex I Table 1) ----- #
        # Climate & environment
        sa.Column('pai_1_scope1_scope2_tco2e', sa.Numeric(14, 4)),          # Indicator 1: GHG emissions (S1+S2)
        sa.Column('pai_1_coverage_pct', sa.Numeric(5, 2)),
        sa.Column('pai_1_data_quality', sa.SmallInteger),

        sa.Column('pai_2_carbon_footprint', sa.Numeric(12, 4)),             # Indicator 2: Carbon footprint (tCO2e/MEUR AUM)
        sa.Column('pai_2_coverage_pct', sa.Numeric(5, 2)),

        sa.Column('pai_3_waci', sa.Numeric(12, 4)),                         # Indicator 3: WACI (tCO2e/MEUR revenue)
        sa.Column('pai_3_coverage_pct', sa.Numeric(5, 2)),

        sa.Column('pai_4_fossil_fuel_exposure_pct', sa.Numeric(5, 2)),      # Indicator 4: Fossil fuel exposure %
        sa.Column('pai_5_nonrenewable_energy_pct', sa.Numeric(5, 2)),       # Indicator 5: Non-renewable energy
        sa.Column('pai_6_energy_intensity', sa.Numeric(12, 4)),             # Indicator 6: Energy intensity (GJ/MEUR revenue)
        sa.Column('pai_7_biodiversity_violations_pct', sa.Numeric(5, 2)),   # Indicator 7: Biodiversity-sensitive areas
        sa.Column('pai_8_water_emissions_pct', sa.Numeric(5, 2)),           # Indicator 8: Emissions to water
        sa.Column('pai_9_hazardous_waste_tonnes', sa.Numeric(12, 4)),       # Indicator 9: Hazardous waste

        # Social & governance
        sa.Column('pai_10_un_global_compact_violations_pct', sa.Numeric(5, 2)),    # Indicator 10: UNGC/OECD violations
        sa.Column('pai_11_lack_of_ungc_compliance_pct', sa.Numeric(5, 2)),         # Indicator 11: Lack of monitoring processes
        sa.Column('pai_12_unadjusted_gender_pay_gap_pct', sa.Numeric(5, 2)),       # Indicator 12: Gender pay gap
        sa.Column('pai_13_board_gender_diversity_pct', sa.Numeric(5, 2)),          # Indicator 13: Board gender diversity
        sa.Column('pai_14_controversial_weapons_exposure_pct', sa.Numeric(5, 2)),  # Indicator 14: Controversial weapons
        sa.Column('pai_15_carbon_intensity_real_estate_kgco2_m2', sa.Numeric(10, 4)),  # Indicator 15 (RE): Carbon intensity
        sa.Column('pai_16_fossil_fuel_re_pct', sa.Numeric(5, 2)),                  # Indicator 16 (RE): Fossil fuel RE exposure
        sa.Column('pai_17_energy_inefficient_re_pct', sa.Numeric(5, 2)),           # Indicator 17 (RE): Inefficient RE
        sa.Column('pai_18_countries_inadequate_tax_pct', sa.Numeric(5, 2)),        # Indicator 18: Countries with inadequate tax policy

        # Optional indicators (selected set, stored in full in JSONB)
        sa.Column('optional_indicators', JSONB),                        # {indicator_id: {value, unit, coverage_pct, data_quality}}

        # Full mandatory table for reporting / export
        sa.Column('mandatory_indicators_full', JSONB),                  # [{indicator_id, name, value, unit, coverage_pct, dq, yoy_change}]

        # Data quality summary
        sa.Column('weighted_avg_dq_score', sa.Numeric(3, 1)),           # PCAF DQ 1-5
        sa.Column('engagement_actions', JSONB),                         # Actions taken re: PAI reduction

        sa.Column('validation_summary', JSONB),
        sa.Column('status', sa.String(20), default='draft'),
        sa.Column('created_by', UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.CheckConstraint("sfdr_article IN (6,8,9)", name='ck_sfdr_pai_article'),
        sa.CheckConstraint("status IN ('draft','submitted','approved','published','archived')", name='ck_sfdr_pai_status'),
    )
    op.create_index('ix_sfdr_pai_entity', 'sfdr_pai_disclosures', ['entity_id'])
    op.create_index('ix_sfdr_pai_period', 'sfdr_pai_disclosures', ['reporting_period_end'])
    op.create_index('ix_sfdr_pai_article', 'sfdr_pai_disclosures', ['sfdr_article'])

    # -------------------------------------------------------------------------
    # 3. EU TAXONOMY ASSESSMENTS  (EU 2020/852 + Climate/Environmental Delegated Acts)
    # -------------------------------------------------------------------------
    op.create_table(
        'eu_taxonomy_assessments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_id', UUID(as_uuid=True), sa.ForeignKey('regulatory_entities.id', ondelete='SET NULL')),
        sa.Column('entity_name', sa.String(255), nullable=False),
        sa.Column('reporting_year', sa.Integer, nullable=False),
        sa.Column('assessment_type', sa.String(20), default='nfrd'),    # nfrd | csrd | voluntary | investor

        # Key Performance Indicators — Turnover
        sa.Column('total_turnover_gbp', sa.Numeric(18, 2)),
        sa.Column('taxonomy_eligible_turnover_pct', sa.Numeric(5, 2)),
        sa.Column('taxonomy_aligned_turnover_pct', sa.Numeric(5, 2)),
        sa.Column('not_eligible_turnover_pct', sa.Numeric(5, 2)),

        # KPIs — CapEx
        sa.Column('total_capex_gbp', sa.Numeric(18, 2)),
        sa.Column('taxonomy_eligible_capex_pct', sa.Numeric(5, 2)),
        sa.Column('taxonomy_aligned_capex_pct', sa.Numeric(5, 2)),
        sa.Column('not_eligible_capex_pct', sa.Numeric(5, 2)),

        # KPIs — OpEx
        sa.Column('total_opex_gbp', sa.Numeric(18, 2)),
        sa.Column('taxonomy_eligible_opex_pct', sa.Numeric(5, 2)),
        sa.Column('taxonomy_aligned_opex_pct', sa.Numeric(5, 2)),
        sa.Column('not_eligible_opex_pct', sa.Numeric(5, 2)),

        # Per-objective alignment (6 EU Taxonomy environmental objectives)
        # obj1=Climate Mitigation, obj2=Climate Adaptation, obj3=Water, obj4=Circular Economy, obj5=Pollution, obj6=Biodiversity
        sa.Column('obj1_climate_mitigation_aligned_pct', sa.Numeric(5, 2)),
        sa.Column('obj2_climate_adaptation_aligned_pct', sa.Numeric(5, 2)),
        sa.Column('obj3_water_marine_aligned_pct', sa.Numeric(5, 2)),
        sa.Column('obj4_circular_economy_aligned_pct', sa.Numeric(5, 2)),
        sa.Column('obj5_pollution_prevention_aligned_pct', sa.Numeric(5, 2)),
        sa.Column('obj6_biodiversity_aligned_pct', sa.Numeric(5, 2)),

        # DNSH compliance summary (6 objectives × pass/fail flags)
        sa.Column('dnsh_compliance', JSONB),                            # {obj1: {pass: true, issues: []}, obj2: {...}}
        sa.Column('minimum_safeguards_met', sa.Boolean),                # OECD/UNGC minimum social safeguards

        # Delegated Acts applied
        sa.Column('climate_delegated_act_applied', sa.Boolean, default=True),      # EU 2021/2139
        sa.Column('environmental_delegated_act_applied', sa.Boolean, default=False), # EU 2023/2485

        sa.Column('validation_summary', JSONB),
        sa.Column('status', sa.String(20), default='draft'),
        sa.Column('created_by', UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.CheckConstraint("status IN ('draft','submitted','approved','published','archived')", name='ck_eu_tax_status'),
    )
    op.create_index('ix_eu_taxonomy_assessments_entity', 'eu_taxonomy_assessments', ['entity_id'])
    op.create_index('ix_eu_taxonomy_assessments_year', 'eu_taxonomy_assessments', ['reporting_year'])

    # -------------------------------------------------------------------------
    # 4. EU TAXONOMY ACTIVITIES  (per-economic-activity screening)
    # -------------------------------------------------------------------------
    op.create_table(
        'eu_taxonomy_activities',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('assessment_id', UUID(as_uuid=True), sa.ForeignKey('eu_taxonomy_assessments.id', ondelete='CASCADE'), nullable=False),

        # Activity identification (NACE / Taxonomy code)
        sa.Column('activity_code', sa.String(20), nullable=False),      # e.g. '4.1' (Electricity generation solar)
        sa.Column('activity_name', sa.String(255), nullable=False),
        sa.Column('nace_codes', JSONB),                                 # [{'code': 'D35.11', 'desc': '...'}]
        sa.Column('sector', sa.String(50)),                             # Climate Mitigation sector

        # Financial KPIs for this activity
        sa.Column('turnover_gbp', sa.Numeric(15, 2)),
        sa.Column('capex_gbp', sa.Numeric(15, 2)),
        sa.Column('opex_gbp', sa.Numeric(15, 2)),

        # Substantial contribution objective
        sa.Column('sc_objective', sa.SmallInteger),                     # 1-6 (which objective SC is claimed for)
        sa.Column('sc_criteria_met', sa.Boolean),                       # Technical Screening Criteria pass
        sa.Column('sc_criteria_evidence', sa.Text),
        sa.Column('sc_threshold_value', sa.Numeric(12, 4)),             # e.g. ≤100 gCO2/kWh
        sa.Column('sc_actual_value', sa.Numeric(12, 4)),

        # DNSH per objective (6 flags)
        sa.Column('dnsh_obj1', sa.Boolean),
        sa.Column('dnsh_obj2', sa.Boolean),
        sa.Column('dnsh_obj3', sa.Boolean),
        sa.Column('dnsh_obj4', sa.Boolean),
        sa.Column('dnsh_obj5', sa.Boolean),
        sa.Column('dnsh_obj6', sa.Boolean),
        sa.Column('dnsh_evidence', JSONB),                              # {obj: evidence_text}

        # Minimum safeguards
        sa.Column('minimum_safeguards_met', sa.Boolean),

        # Final alignment
        sa.Column('is_eligible', sa.Boolean, nullable=False),
        sa.Column('is_aligned', sa.Boolean, nullable=False),
        sa.Column('non_alignment_reasons', JSONB),                      # [{objective, reason}]

        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.CheckConstraint("sc_objective BETWEEN 1 AND 6", name='ck_eu_tax_activities_sc_obj'),
    )
    op.create_index('ix_eu_taxonomy_activities_assessment', 'eu_taxonomy_activities', ['assessment_id'])
    op.create_index('ix_eu_taxonomy_activities_code', 'eu_taxonomy_activities', ['activity_code'])
    op.create_index('ix_eu_taxonomy_activities_aligned', 'eu_taxonomy_activities', ['is_aligned'])

    # -------------------------------------------------------------------------
    # 5. TCFD ASSESSMENTS  (TCFD 2023, 11 recommended disclosures)
    # -------------------------------------------------------------------------
    op.create_table(
        'tcfd_assessments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_id', UUID(as_uuid=True), sa.ForeignKey('regulatory_entities.id', ondelete='SET NULL')),
        sa.Column('entity_name', sa.String(255), nullable=False),
        sa.Column('reporting_year', sa.Integer, nullable=False),
        sa.Column('assessment_type', sa.String(20), default='self_assessment'),  # self_assessment | third_party | regulatory

        # Governance pillar (2 disclosures)
        sa.Column('gov_1_board_oversight', sa.SmallInteger),           # 0-4 maturity
        sa.Column('gov_2_management_role', sa.SmallInteger),
        sa.Column('gov_score', sa.Numeric(4, 2)),                      # average 0-4

        # Strategy pillar (3 disclosures)
        sa.Column('strat_1_climate_risks_opps', sa.SmallInteger),
        sa.Column('strat_2_business_impact', sa.SmallInteger),
        sa.Column('strat_3_resilience', sa.SmallInteger),
        sa.Column('strat_score', sa.Numeric(4, 2)),

        # Risk Management pillar (3 disclosures)
        sa.Column('risk_1_identification_process', sa.SmallInteger),
        sa.Column('risk_2_management_process', sa.SmallInteger),
        sa.Column('risk_3_integration', sa.SmallInteger),
        sa.Column('risk_score', sa.Numeric(4, 2)),

        # Metrics & Targets pillar (3 disclosures)
        sa.Column('met_1_metrics_used', sa.SmallInteger),
        sa.Column('met_2_scope_123_emissions', sa.SmallInteger),
        sa.Column('met_3_targets', sa.SmallInteger),
        sa.Column('met_score', sa.Numeric(4, 2)),

        # Overall score
        sa.Column('overall_score', sa.Numeric(4, 2)),                  # 0-4
        sa.Column('maturity_level', sa.String(20)),                     # Emerging | Developing | Mature | Leading

        # Gap analysis
        sa.Column('gap_analysis', JSONB),                               # [{disclosure, score, gap, recommended_actions, priority}]
        sa.Column('disclosure_locations', JSONB),                       # where each disclosure appears in reports

        # Scenario analysis (TCFD recommended)
        sa.Column('scenarios_used', JSONB),                             # [{name, type, horizon_year, source}]
        sa.Column('transition_scenario_count', sa.SmallInteger, default=0),
        sa.Column('physical_scenario_count', sa.SmallInteger, default=0),
        sa.Column('has_quantified_financial_impacts', sa.Boolean, default=False),

        sa.Column('validation_summary', JSONB),
        sa.Column('status', sa.String(20), default='draft'),
        sa.Column('created_by', UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.CheckConstraint("gov_1_board_oversight IS NULL OR gov_1_board_oversight BETWEEN 0 AND 4", name='ck_tcfd_gov1'),
        sa.CheckConstraint("gov_2_management_role IS NULL OR gov_2_management_role BETWEEN 0 AND 4", name='ck_tcfd_gov2'),
        sa.CheckConstraint("strat_1_climate_risks_opps IS NULL OR strat_1_climate_risks_opps BETWEEN 0 AND 4", name='ck_tcfd_strat1'),
        sa.CheckConstraint("strat_2_business_impact IS NULL OR strat_2_business_impact BETWEEN 0 AND 4", name='ck_tcfd_strat2'),
        sa.CheckConstraint("strat_3_resilience IS NULL OR strat_3_resilience BETWEEN 0 AND 4", name='ck_tcfd_strat3'),
        sa.CheckConstraint("risk_1_identification_process IS NULL OR risk_1_identification_process BETWEEN 0 AND 4", name='ck_tcfd_risk1'),
        sa.CheckConstraint("risk_2_management_process IS NULL OR risk_2_management_process BETWEEN 0 AND 4", name='ck_tcfd_risk2'),
        sa.CheckConstraint("risk_3_integration IS NULL OR risk_3_integration BETWEEN 0 AND 4", name='ck_tcfd_risk3'),
        sa.CheckConstraint("met_1_metrics_used IS NULL OR met_1_metrics_used BETWEEN 0 AND 4", name='ck_tcfd_met1'),
        sa.CheckConstraint("met_2_scope_123_emissions IS NULL OR met_2_scope_123_emissions BETWEEN 0 AND 4", name='ck_tcfd_met2'),
        sa.CheckConstraint("met_3_targets IS NULL OR met_3_targets BETWEEN 0 AND 4", name='ck_tcfd_met3'),
        sa.CheckConstraint("status IN ('draft','submitted','approved','published','archived')", name='ck_tcfd_status'),
    )
    op.create_index('ix_tcfd_assessments_entity', 'tcfd_assessments', ['entity_id'])
    op.create_index('ix_tcfd_assessments_year', 'tcfd_assessments', ['reporting_year'])
    op.create_index('ix_tcfd_assessments_maturity', 'tcfd_assessments', ['maturity_level'])

    # -------------------------------------------------------------------------
    # 6. CSRD READINESS ASSESSMENTS  (CSRD/ESRS Set 1 — EU 2022/2464)
    # -------------------------------------------------------------------------
    op.create_table(
        'csrd_readiness_assessments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_id', UUID(as_uuid=True), sa.ForeignKey('regulatory_entities.id', ondelete='SET NULL')),
        sa.Column('entity_name', sa.String(255), nullable=False),
        sa.Column('reporting_year', sa.Integer, nullable=False),
        sa.Column('first_mandatory_year', sa.Integer),                  # when CSRD first applies to this entity
        sa.Column('entity_size', sa.String(20), default='large'),       # large | listed_sme | small_and_non_complex

        # Double Materiality Assessment
        sa.Column('dma_completed', sa.Boolean, default=False),
        sa.Column('dma_completion_date', sa.Date),
        sa.Column('dma_methodology', sa.String(100)),
        sa.Column('material_topics_count', sa.Integer),
        sa.Column('material_topics', JSONB),                            # [{esrs_standard, topic, impact_material, financial_material}]

        # ESRS cross-cutting (ESRS 2 mandatory for all)
        sa.Column('esrs2_general_disclosures_status', sa.String(30), default='not_started'),
        sa.Column('esrs2_completeness_pct', sa.Numeric(5, 2)),

        # Environment standards (E1–E5)
        sa.Column('e1_climate_status', sa.String(30), default='not_started'),
        sa.Column('e1_climate_material', sa.Boolean),
        sa.Column('e2_pollution_status', sa.String(30), default='not_started'),
        sa.Column('e2_pollution_material', sa.Boolean),
        sa.Column('e3_water_marine_status', sa.String(30), default='not_started'),
        sa.Column('e3_water_material', sa.Boolean),
        sa.Column('e4_biodiversity_status', sa.String(30), default='not_started'),
        sa.Column('e4_biodiversity_material', sa.Boolean),
        sa.Column('e5_circular_economy_status', sa.String(30), default='not_started'),
        sa.Column('e5_circular_material', sa.Boolean),

        # Social standards (S1–S4)
        sa.Column('s1_own_workforce_status', sa.String(30), default='not_started'),
        sa.Column('s1_own_workforce_material', sa.Boolean),
        sa.Column('s2_value_chain_workers_status', sa.String(30), default='not_started'),
        sa.Column('s2_value_chain_material', sa.Boolean),
        sa.Column('s3_affected_communities_status', sa.String(30), default='not_started'),
        sa.Column('s3_communities_material', sa.Boolean),
        sa.Column('s4_consumers_end_users_status', sa.String(30), default='not_started'),
        sa.Column('s4_consumers_material', sa.Boolean),

        # Governance standard (G1)
        sa.Column('g1_business_conduct_status', sa.String(30), default='not_started'),
        sa.Column('g1_business_conduct_material', sa.Boolean),

        # Overall readiness
        sa.Column('overall_readiness_pct', sa.Numeric(5, 2)),
        sa.Column('mandatory_standards_complete_count', sa.SmallInteger, default=0),  # out of applicable
        sa.Column('total_applicable_standards', sa.SmallInteger),

        # Assurance
        sa.Column('assurance_type', sa.String(20)),                     # none | limited | reasonable
        sa.Column('assurance_provider', sa.String(100)),
        sa.Column('assurance_standard', sa.String(50)),                 # ISAE3000 | ISAE3410 | IAASB_ISSA5000

        # Gap analysis and action plan
        sa.Column('gap_analysis', JSONB),                               # [{standard, gap_description, priority, effort, timeline}]
        sa.Column('data_gaps', JSONB),                                  # [{standard, data_point, gap_type, mitigation}]

        sa.Column('validation_summary', JSONB),
        sa.Column('status', sa.String(20), default='draft'),
        sa.Column('created_by', UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.CheckConstraint("entity_size IN ('large','listed_sme','small_and_non_complex')", name='ck_csrd_entity_size'),
        sa.CheckConstraint("e1_climate_status IN ('not_started','data_gap','in_progress','disclosed','assured','not_material')", name='ck_csrd_e1_status'),
        sa.CheckConstraint("status IN ('draft','submitted','approved','published','archived')", name='ck_csrd_status'),
    )
    op.create_index('ix_csrd_readiness_entity', 'csrd_readiness_assessments', ['entity_id'])
    op.create_index('ix_csrd_readiness_year', 'csrd_readiness_assessments', ['reporting_year'])

    # -------------------------------------------------------------------------
    # 7. ISSB ASSESSMENTS  (IFRS S1 General + S2 Climate, ISSB 2023)
    # -------------------------------------------------------------------------
    op.create_table(
        'issb_assessments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_id', UUID(as_uuid=True), sa.ForeignKey('regulatory_entities.id', ondelete='SET NULL')),
        sa.Column('entity_name', sa.String(255), nullable=False),
        sa.Column('reporting_year', sa.Integer, nullable=False),
        sa.Column('assessment_type', sa.String(20), default='self_assessment'),

        # ---- IFRS S1 (General Requirements) ----
        # Governance (2 disclosures)
        sa.Column('s1_gov_1_board_oversight', sa.SmallInteger),        # 0-4
        sa.Column('s1_gov_2_management_role', sa.SmallInteger),
        sa.Column('s1_gov_score', sa.Numeric(4, 2)),

        # Strategy (3 disclosures)
        sa.Column('s1_strat_1_risks_opps', sa.SmallInteger),
        sa.Column('s1_strat_2_current_business_model', sa.SmallInteger),
        sa.Column('s1_strat_3_resilience', sa.SmallInteger),
        sa.Column('s1_strat_score', sa.Numeric(4, 2)),

        # Risk Management (2 disclosures)
        sa.Column('s1_risk_1_process_identify', sa.SmallInteger),
        sa.Column('s1_risk_2_integrate', sa.SmallInteger),
        sa.Column('s1_risk_score', sa.Numeric(4, 2)),

        # Metrics & Targets (3 disclosures)
        sa.Column('s1_met_1_metrics', sa.SmallInteger),
        sa.Column('s1_met_2_targets', sa.SmallInteger),
        sa.Column('s1_met_3_progress', sa.SmallInteger),
        sa.Column('s1_met_score', sa.Numeric(4, 2)),

        sa.Column('s1_overall_score', sa.Numeric(4, 2)),

        # ---- IFRS S2 (Climate-related Disclosures) ----
        # Governance (2 disclosures)
        sa.Column('s2_gov_1_board_oversight', sa.SmallInteger),
        sa.Column('s2_gov_2_management_role', sa.SmallInteger),
        sa.Column('s2_gov_score', sa.Numeric(4, 2)),

        # Strategy (4 disclosures including transition plan)
        sa.Column('s2_strat_1_climate_risks_opps', sa.SmallInteger),
        sa.Column('s2_strat_2_current_impact', sa.SmallInteger),
        sa.Column('s2_strat_3_resilience_scenarios', sa.SmallInteger),
        sa.Column('s2_strat_4_transition_plan', sa.SmallInteger),
        sa.Column('s2_strat_score', sa.Numeric(4, 2)),

        # Risk Management (2 disclosures)
        sa.Column('s2_risk_1_identify_assess', sa.SmallInteger),
        sa.Column('s2_risk_2_manage', sa.SmallInteger),
        sa.Column('s2_risk_score', sa.Numeric(4, 2)),

        # Metrics & Targets — S2 cross-industry metrics (6 mandatory)
        sa.Column('s2_met_scope1_tco2e', sa.Numeric(14, 4)),           # Absolute scope 1
        sa.Column('s2_met_scope2_market_tco2e', sa.Numeric(14, 4)),
        sa.Column('s2_met_scope2_location_tco2e', sa.Numeric(14, 4)),
        sa.Column('s2_met_scope3_tco2e', sa.Numeric(14, 4)),
        sa.Column('s2_met_ghg_disclosure_score', sa.SmallInteger),      # 0-4 maturity of GHG disclosure
        sa.Column('s2_met_transition_risk_metric', sa.SmallInteger),    # 0-4
        sa.Column('s2_met_physical_risk_metric', sa.SmallInteger),      # 0-4
        sa.Column('s2_met_capital_deployment_gbp', sa.Numeric(15, 2)), # climate-related capital deployment
        sa.Column('s2_met_internal_carbon_price', sa.Numeric(8, 2)),   # £/tCO2e
        sa.Column('s2_met_remuneration_linked', sa.Boolean, default=False),
        sa.Column('s2_met_score', sa.Numeric(4, 2)),

        sa.Column('s2_overall_score', sa.Numeric(4, 2)),

        # Combined ISSB score
        sa.Column('combined_issb_score', sa.Numeric(4, 2)),
        sa.Column('maturity_level', sa.String(20)),                     # Emerging | Developing | Mature | Leading

        # Sector-specific disclosures (ISSB SASB-based industry modules)
        sa.Column('industry_classification_sasb', sa.String(50)),
        sa.Column('industry_specific_metrics', JSONB),                  # [{metric_id, name, value, unit, disclosure_score}]

        sa.Column('gap_analysis', JSONB),
        sa.Column('validation_summary', JSONB),
        sa.Column('status', sa.String(20), default='draft'),
        sa.Column('created_by', UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.CheckConstraint("status IN ('draft','submitted','approved','published','archived')", name='ck_issb_status'),
    )
    op.create_index('ix_issb_assessments_entity', 'issb_assessments', ['entity_id'])
    op.create_index('ix_issb_assessments_year', 'issb_assessments', ['reporting_year'])
    op.create_index('ix_issb_assessments_maturity', 'issb_assessments', ['maturity_level'])

    # -------------------------------------------------------------------------
    # 8. BRSR DISCLOSURES  (SEBI Circular CIR/CFD/CMD1/114/2023, India)
    # -------------------------------------------------------------------------
    op.create_table(
        'brsr_disclosures',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_id', UUID(as_uuid=True), sa.ForeignKey('regulatory_entities.id', ondelete='SET NULL')),
        sa.Column('entity_name', sa.String(255), nullable=False),
        sa.Column('cin', sa.String(21)),                               # Company Identification Number (India)
        sa.Column('reporting_year', sa.Integer, nullable=False),       # Financial year (e.g. 2024 = FY 2023-24)
        sa.Column('bse_scrip_code', sa.String(10)),
        sa.Column('nse_symbol', sa.String(20)),
        sa.Column('listed_exchange', sa.String(20)),                    # BSE | NSE | BOTH

        # Applicability
        sa.Column('is_mandatory', sa.Boolean, nullable=False, default=False), # Top 1000 listed (mandatory)
        sa.Column('brsr_core_applicable', sa.Boolean, default=False),  # Top 150 from FY2023-24 (3rd-party assurance)
        sa.Column('brsr_core_assured', sa.Boolean, default=False),
        sa.Column('assurance_provider', sa.String(100)),
        sa.Column('assurance_standard', sa.String(50)),                 # ISAE3000 | AA1000AS

        # Section A — General Disclosures
        sa.Column('section_a_status', sa.String(30), default='not_started'),
        sa.Column('employee_count_permanent', sa.Integer),
        sa.Column('employee_count_contract', sa.Integer),
        sa.Column('turnover_inr_cr', sa.Numeric(18, 2)),
        sa.Column('net_worth_inr_cr', sa.Numeric(18, 2)),

        # Section B — Management & Process Disclosures (9 NVG-SEG Principles)
        sa.Column('p1_ethics_status', sa.String(30), default='not_started'),
        sa.Column('p1_ethics_score', sa.SmallInteger),                  # 0-10
        sa.Column('p2_products_services_status', sa.String(30), default='not_started'),
        sa.Column('p2_products_score', sa.SmallInteger),
        sa.Column('p3_employee_wellbeing_status', sa.String(30), default='not_started'),
        sa.Column('p3_employee_score', sa.SmallInteger),
        sa.Column('p4_stakeholder_engagement_status', sa.String(30), default='not_started'),
        sa.Column('p4_stakeholder_score', sa.SmallInteger),
        sa.Column('p5_human_rights_status', sa.String(30), default='not_started'),
        sa.Column('p5_human_rights_score', sa.SmallInteger),
        sa.Column('p6_environment_status', sa.String(30), default='not_started'),
        sa.Column('p6_environment_score', sa.SmallInteger),
        sa.Column('p7_policy_advocacy_status', sa.String(30), default='not_started'),
        sa.Column('p7_policy_score', sa.SmallInteger),
        sa.Column('p8_inclusive_growth_status', sa.String(30), default='not_started'),
        sa.Column('p8_inclusive_score', sa.SmallInteger),
        sa.Column('p9_consumer_engagement_status', sa.String(30), default='not_started'),
        sa.Column('p9_consumer_score', sa.SmallInteger),

        # Section C — Performance Disclosures
        sa.Column('section_c_status', sa.String(30), default='not_started'),

        # BRSR Core KPIs (mandatory for Top 150 / Top 1000 per phase-in)
        # Environmental KPIs
        sa.Column('core_e1_ghg_scope1_tco2e', sa.Numeric(14, 4)),
        sa.Column('core_e2_ghg_scope2_tco2e', sa.Numeric(14, 4)),
        sa.Column('core_e3_ghg_scope3_tco2e', sa.Numeric(14, 4)),
        sa.Column('core_e4_total_energy_gj', sa.Numeric(14, 2)),
        sa.Column('core_e5_renewable_energy_pct', sa.Numeric(5, 2)),
        sa.Column('core_e6_water_intensity_m3_cr_revenue', sa.Numeric(10, 4)),
        sa.Column('core_e7_waste_intensity_kg_cr_revenue', sa.Numeric(10, 4)),

        # Social KPIs
        sa.Column('core_s1_csr_spend_inr_cr', sa.Numeric(12, 2)),
        sa.Column('core_s2_women_in_mgmt_pct', sa.Numeric(5, 2)),
        sa.Column('core_s3_attrition_rate_pct', sa.Numeric(5, 2)),
        sa.Column('core_s4_median_wage_ratio', sa.Numeric(6, 4)),      # median worker wage / median mgmt wage
        sa.Column('core_s5_training_hours_avg', sa.Numeric(6, 2)),

        # Governance KPIs
        sa.Column('core_g1_independent_directors_pct', sa.Numeric(5, 2)),
        sa.Column('core_g2_board_meetings_count', sa.SmallInteger),
        sa.Column('core_g3_cybersecurity_incidents', sa.Integer),

        # Overall BRSR readiness
        sa.Column('overall_readiness_pct', sa.Numeric(5, 2)),
        sa.Column('total_principles_disclosed', sa.SmallInteger),

        # Additional JSONB for full indicator set
        sa.Column('full_brsr_data', JSONB),                             # Complete BRSR disclosure data including all indicators
        sa.Column('gap_analysis', JSONB),
        sa.Column('validation_summary', JSONB),
        sa.Column('status', sa.String(20), default='draft'),
        sa.Column('created_by', UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.CheckConstraint("status IN ('draft','submitted','approved','published','archived')", name='ck_brsr_status'),
    )
    op.create_index('ix_brsr_disclosures_entity', 'brsr_disclosures', ['entity_id'])
    op.create_index('ix_brsr_disclosures_year', 'brsr_disclosures', ['reporting_year'])
    op.create_index('ix_brsr_disclosures_mandatory', 'brsr_disclosures', ['is_mandatory'])
    op.create_index('ix_brsr_disclosures_core', 'brsr_disclosures', ['brsr_core_applicable'])

    # -------------------------------------------------------------------------
    # 9. SF TAXONOMY ALIGNMENTS  (multi-jurisdiction sustainable finance taxonomies)
    # -------------------------------------------------------------------------
    op.create_table(
        'sf_taxonomy_alignments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_id', UUID(as_uuid=True), sa.ForeignKey('regulatory_entities.id', ondelete='SET NULL')),
        sa.Column('entity_name', sa.String(255), nullable=False),
        sa.Column('reporting_year', sa.Integer, nullable=False),

        # Taxonomy jurisdiction
        sa.Column('taxonomy_id', sa.String(30), nullable=False),        # eu_taxonomy | uk_taxonomy | singapore_taxonomy | asean_taxonomy | china_taxonomy | canada_taxonomy | australia_taxonomy | south_africa_taxonomy | india_taxonomy | oecd_sustainable
        sa.Column('taxonomy_name', sa.String(100), nullable=False),
        sa.Column('taxonomy_version', sa.String(20)),
        sa.Column('jurisdiction', sa.String(50)),

        # Eligibility and alignment
        sa.Column('turnover_eligible_pct', sa.Numeric(5, 2)),
        sa.Column('turnover_aligned_pct', sa.Numeric(5, 2)),
        sa.Column('capex_eligible_pct', sa.Numeric(5, 2)),
        sa.Column('capex_aligned_pct', sa.Numeric(5, 2)),
        sa.Column('opex_eligible_pct', sa.Numeric(5, 2)),
        sa.Column('opex_aligned_pct', sa.Numeric(5, 2)),

        # Environmental objectives covered by this taxonomy (varies by jurisdiction)
        sa.Column('objectives_covered', JSONB),                         # ['climate_mitigation', 'climate_adaptation', 'water', 'circular_economy', 'biodiversity', 'pollution']
        sa.Column('objectives_alignment', JSONB),                       # {objective: aligned_pct}

        # Activity-level detail
        sa.Column('activity_assessments', JSONB),                       # [{activity_code, activity_name, aligned, evidence}]

        # Cross-taxonomy comparison
        sa.Column('eu_taxonomy_comparable_pct', sa.Numeric(5, 2)),     # alignment gap vs EU Taxonomy (if not EU)
        sa.Column('cross_taxonomy_notes', sa.Text),

        # Data quality and coverage
        sa.Column('coverage_pct', sa.Numeric(5, 2)),
        sa.Column('data_sources', JSONB),

        sa.Column('validation_summary', JSONB),
        sa.Column('status', sa.String(20), default='draft'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.CheckConstraint("taxonomy_id IN ('eu_taxonomy','uk_taxonomy','singapore_taxonomy','asean_taxonomy','china_taxonomy','canada_taxonomy','australia_taxonomy','south_africa_taxonomy','india_taxonomy','oecd_sustainable','us_green_finance','japan_taxonomy')", name='ck_sf_taxonomy_id'),
        sa.CheckConstraint("status IN ('draft','submitted','approved','published','archived')", name='ck_sf_taxonomy_status'),
    )
    op.create_index('ix_sf_taxonomy_entity', 'sf_taxonomy_alignments', ['entity_id'])
    op.create_index('ix_sf_taxonomy_id', 'sf_taxonomy_alignments', ['taxonomy_id'])
    op.create_index('ix_sf_taxonomy_year', 'sf_taxonomy_alignments', ['reporting_year'])

    # -------------------------------------------------------------------------
    # 10. REGULATORY ACTION PLANS  (cross-framework remediation tracking)
    # -------------------------------------------------------------------------
    op.create_table(
        'regulatory_action_plans',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_id', UUID(as_uuid=True), sa.ForeignKey('regulatory_entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('framework', sa.String(30), nullable=False),          # SFDR | EU_TAXONOMY | TCFD | CSRD | ISSB | BRSR | SF_TAXONOMY
        sa.Column('linked_assessment_id', UUID(as_uuid=True)),          # FK to the relevant assessment table (polymorphic)
        sa.Column('linked_assessment_type', sa.String(50)),

        sa.Column('action_title', sa.String(255), nullable=False),
        sa.Column('action_description', sa.Text),
        sa.Column('priority', sa.String(10), default='Medium'),         # Critical | High | Medium | Low
        sa.Column('gap_reference', sa.String(100)),                     # reference to specific disclosure / indicator

        # Effort and timeline
        sa.Column('effort_days', sa.Integer),
        sa.Column('estimated_cost_gbp', sa.Numeric(12, 2)),
        sa.Column('target_completion_date', sa.Date),
        sa.Column('actual_completion_date', sa.Date),
        sa.Column('action_status', sa.String(20), default='open'),      # open | in_progress | completed | deferred | cancelled

        # Owner
        sa.Column('owner_name', sa.String(100)),
        sa.Column('owner_team', sa.String(100)),

        # Impact of remediation
        sa.Column('expected_score_improvement', sa.Numeric(4, 2)),
        sa.Column('expected_maturity_improvement', sa.SmallInteger),

        sa.Column('notes', sa.Text),
        sa.Column('created_by', UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.CheckConstraint("framework IN ('SFDR','EU_TAXONOMY','TCFD','CSRD','ISSB','BRSR','SF_TAXONOMY','UK_TAXONOMY','TCFD_MANDATORY')", name='ck_reg_action_framework'),
        sa.CheckConstraint("priority IN ('Critical','High','Medium','Low')", name='ck_reg_action_priority'),
        sa.CheckConstraint("action_status IN ('open','in_progress','completed','deferred','cancelled')", name='ck_reg_action_status'),
    )
    op.create_index('ix_reg_action_plans_entity', 'regulatory_action_plans', ['entity_id'])
    op.create_index('ix_reg_action_plans_framework', 'regulatory_action_plans', ['framework'])
    op.create_index('ix_reg_action_plans_status', 'regulatory_action_plans', ['action_status'])
    op.create_index('ix_reg_action_plans_priority', 'regulatory_action_plans', ['priority'])


def downgrade():
    """Drop regulatory reporting tables."""
    op.drop_table('regulatory_action_plans')
    op.drop_table('sf_taxonomy_alignments')
    op.drop_table('brsr_disclosures')
    op.drop_table('issb_assessments')
    op.drop_table('csrd_readiness_assessments')
    op.drop_table('tcfd_assessments')
    op.drop_table('eu_taxonomy_activities')
    op.drop_table('eu_taxonomy_assessments')
    op.drop_table('sfdr_pai_disclosures')
    op.drop_table('regulatory_entities')
