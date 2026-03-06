"""Add CSRD cross-sector KPI store

Revision ID: 013_add_csrd_kpi_store
Revises: 012_add_energy_developer_tables
Create Date: 2026-03-01

Tables created (13):
  csrd_entity_registry        — canonical entity record linking all sector tables
  csrd_framework_applicability — per-entity regulatory framework applicability + phase-in calendar
  csrd_esrs_catalog           — master reference of every ESRS data point code + metadata
  csrd_kpi_values             — time-series KPI store: one row per entity × indicator × year
  csrd_materiality_topics     — double materiality assessment results per IRO topic
  csrd_disclosure_index       — where each ESRS disclosure appears in the published report
  csrd_peer_benchmarks        — sector-level percentile benchmarks per KPI
  csrd_gap_tracker            — structured gap between current state and target disclosure
  csrd_data_lineage           — audit trail: source → transformation → output per KPI value
  csrd_assurance_log          — third-party assurance engagements + scope per reporting year
  csrd_action_tracker         — remediation actions linked to gaps, with owner + due date
  csrd_target_registry        — all climate / sustainability targets declared by entity
  csrd_transition_plan        — transition plan milestones under ESRS E1 + IFRS S2
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '013_add_csrd_kpi_store'
down_revision = '012_add_energy_developer_tables'
branch_labels = None
depends_on = None


def upgrade():

    # ------------------------------------------------------------------
    # 1. csrd_entity_registry
    #    Canonical cross-sector entity record.  All sector-specific tables
    #    (fi_entities, energy_entities, sc_entities, etc.) are linked here
    #    via entity_registry_id FK so analytics can span sectors.
    # ------------------------------------------------------------------
    op.create_table(
        'csrd_entity_registry',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('legal_name', sa.String(255), nullable=False),
        sa.Column('trading_name', sa.String(255)),
        sa.Column('lei', sa.String(20)),                         # ISO 17442
        sa.Column('isin', sa.String(12)),
        sa.Column('ticker', sa.String(20)),
        sa.Column('country_iso', sa.String(3), nullable=False),
        sa.Column('jurisdiction', sa.String(100)),               # EU, UK, US, IN, etc.
        # Sector classification
        sa.Column('primary_sector', sa.String(100), nullable=False),
        # financial_institution | energy_developer | technology | supply_chain |
        # real_estate | agriculture | mining | insurance | asset_manager | other
        sa.Column('sector_subtype', sa.String(100)),
        sa.Column('nace_code', sa.String(10)),
        sa.Column('sic_code', sa.String(10)),
        sa.Column('isic_code', sa.String(10)),
        sa.Column('gics_sector', sa.String(100)),
        sa.Column('gics_industry', sa.String(100)),
        # Size classification (CSRD Article 3/4 thresholds)
        sa.Column('is_large_undertaking', sa.Boolean(), server_default='false'),
        sa.Column('is_listed_sme', sa.Boolean(), server_default='false'),
        sa.Column('is_non_listed_sme', sa.Boolean(), server_default='false'),
        sa.Column('employee_count', sa.Integer()),
        sa.Column('net_turnover_meur', sa.Numeric(18, 2)),
        sa.Column('balance_sheet_total_meur', sa.Numeric(18, 2)),
        # Regulatory perimeter
        sa.Column('is_in_scope_csrd', sa.Boolean(), server_default='false'),
        sa.Column('csrd_first_reporting_year', sa.Integer()),
        sa.Column('is_in_scope_sfdr', sa.Boolean(), server_default='false'),
        sa.Column('sfdr_article_classification', sa.String(2)),  # 6 | 8 | 9
        sa.Column('is_in_scope_eu_taxonomy', sa.Boolean(), server_default='false'),
        sa.Column('is_in_scope_tcfd', sa.Boolean(), server_default='false'),
        sa.Column('is_in_scope_issb', sa.Boolean(), server_default='false'),
        sa.Column('is_in_scope_brsr', sa.Boolean(), server_default='false'),
        # Cross-table foreign keys (nullable — filled when sector record exists)
        sa.Column('fi_entity_id', UUID(as_uuid=True)),
        sa.Column('energy_entity_id', UUID(as_uuid=True)),
        sa.Column('sc_entity_id', UUID(as_uuid=True)),
        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()')),
        sa.Column('created_by', sa.String(100)),
        sa.CheckConstraint(
            "sfdr_article_classification IN ('6','8','9') "
            "OR sfdr_article_classification IS NULL",
            name='ck_csrd_registry_sfdr_article'
        ),
        sa.CheckConstraint(
            "primary_sector IN ("
            "'financial_institution','energy_developer','technology',"
            "'supply_chain','real_estate','agriculture','mining',"
            "'insurance','asset_manager','other')",
            name='ck_csrd_registry_sector'
        ),
    )

    # ------------------------------------------------------------------
    # 2. csrd_framework_applicability
    #    Records which frameworks apply to an entity, their first reporting
    #    year, phase-in timeline, and current compliance status.
    # ------------------------------------------------------------------
    op.create_table(
        'csrd_framework_applicability',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_registry_id', UUID(as_uuid=True), nullable=False),
        sa.Column('framework', sa.String(50), nullable=False),
        # CSRD | SFDR | EU_TAXONOMY | TCFD | ISSB | BRSR | GRI | CDP | UN_SDG
        # UK_SDR | MAS_ESG | SEC_CLIMATE | TNFD | BRSR_CORE
        sa.Column('framework_version', sa.String(50)),            # e.g. ESRS Set 1 2023
        sa.Column('mandatory_flag', sa.Boolean(), server_default='false'),
        sa.Column('first_reporting_year', sa.Integer()),
        sa.Column('phase_in_year_1', sa.Integer()),
        sa.Column('phase_in_year_2', sa.Integer()),
        sa.Column('phase_in_year_3', sa.Integer()),
        sa.Column('current_status', sa.String(50)),
        # not_started | scoping | gap_analysis | implementation | first_disclosure
        # ongoing | assurance | complete
        sa.Column('compliance_score_pct', sa.Numeric(5, 2)),      # 0-100
        sa.Column('next_milestone', sa.String(255)),
        sa.Column('next_milestone_date', sa.Date()),
        sa.Column('external_assurance_required', sa.Boolean(), server_default='false'),
        sa.Column('assurance_level', sa.String(50)),               # limited | reasonable
        sa.Column('auditor_name', sa.String(200)),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['entity_registry_id'], ['csrd_entity_registry.id'],
                                ondelete='CASCADE'),
        sa.CheckConstraint(
            "compliance_score_pct BETWEEN 0 AND 100 "
            "OR compliance_score_pct IS NULL",
            name='ck_framework_compliance_pct'
        ),
        sa.CheckConstraint(
            "current_status IN ("
            "'not_started','scoping','gap_analysis','implementation',"
            "'first_disclosure','ongoing','assurance','complete') "
            "OR current_status IS NULL",
            name='ck_framework_status'
        ),
    )

    # ------------------------------------------------------------------
    # 3. csrd_esrs_catalog
    #    Master reference table of every ESRS data point / disclosure
    #    requirement.  Populated once; referenced by csrd_kpi_values.
    # ------------------------------------------------------------------
    op.create_table(
        'csrd_esrs_catalog',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        # Identification
        sa.Column('indicator_code', sa.String(60), nullable=False, unique=True),
        # e.g. E1-6_1, S1-7_3, G1-1_2, ESRS2_GOV-1_1
        sa.Column('standard_code', sa.String(20), nullable=False),
        # ESRS2 | E1..E5 | S1..S4 | G1
        sa.Column('disclosure_requirement', sa.String(60), nullable=False),
        # e.g. E1-6, S1-7, G1-1
        sa.Column('data_point_code', sa.String(60)),              # EFRAG DP numbering
        sa.Column('paragraph_ref', sa.String(20)),                # e.g. para 44(a)(iii)
        # Description
        sa.Column('topic', sa.String(100)),                       # Climate | Pollution | etc.
        sa.Column('sub_topic', sa.String(100)),
        sa.Column('indicator_name', sa.Text(), nullable=False),
        sa.Column('indicator_description', sa.Text()),
        # Classification
        sa.Column('disclosure_type', sa.String(30)),
        # quantitative | qualitative | policy | target | action | metric
        sa.Column('is_mandatory', sa.Boolean(), server_default='true'),
        sa.Column('is_sector_specific', sa.Boolean(), server_default='false'),
        sa.Column('applicable_sectors', JSONB()),                  # list of sector strings
        sa.Column('esrs_phase_in', sa.String(20)),
        # none | phase_in_year_1 | phase_in_year_2 | voluntary
        sa.Column('smei_exemption', sa.Boolean(), server_default='false'),
        # Measurement
        sa.Column('unit_of_measure', sa.String(60)),
        sa.Column('preferred_unit', sa.String(60)),
        sa.Column('allowed_units', JSONB()),                       # list
        sa.Column('calculation_method', sa.Text()),
        sa.Column('reference_standard', sa.String(200)),          # GHG Protocol, PCAF, etc.
        sa.Column('xbrl_tag', sa.String(200)),                    # ESRS XBRL taxonomy tag
        # Cross-references
        sa.Column('gri_equivalent', sa.String(60)),
        sa.Column('tcfd_pillar', sa.String(30)),
        sa.Column('issb_equivalent', sa.String(60)),
        sa.Column('brsr_equivalent', sa.String(60)),
        sa.Column('sdg_alignment', JSONB()),                       # list of SDG numbers
        # Materiality guidance
        sa.Column('always_material', sa.Boolean(), server_default='false'),
        sa.Column('materiality_assessment_guidance', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()')),
        sa.CheckConstraint(
            "disclosure_type IN ("
            "'quantitative','qualitative','policy','target','action','metric') "
            "OR disclosure_type IS NULL",
            name='ck_esrs_catalog_dtype'
        ),
    )
    op.create_index('ix_esrs_catalog_standard', 'csrd_esrs_catalog',
                    ['standard_code', 'disclosure_requirement'])

    # ------------------------------------------------------------------
    # 4. csrd_kpi_values
    #    Time-series KPI store.  One row per entity × indicator_code × year.
    #    Handles numeric, text, boolean and JSON payloads.
    # ------------------------------------------------------------------
    op.create_table(
        'csrd_kpi_values',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_registry_id', UUID(as_uuid=True), nullable=False),
        sa.Column('indicator_code', sa.String(60), nullable=False),
        sa.Column('reporting_year', sa.Integer(), nullable=False),
        # Values — exactly one should be non-null per row
        sa.Column('numeric_value', sa.Numeric(24, 6)),
        sa.Column('text_value', sa.Text()),
        sa.Column('boolean_value', sa.Boolean()),
        sa.Column('json_value', JSONB()),
        # Unit and coverage
        sa.Column('unit', sa.String(60)),
        sa.Column('coverage_pct', sa.Numeric(5, 2)),              # % of entity scope covered
        sa.Column('coverage_basis', sa.String(100)),              # operational control | equity share | etc.
        # Data quality
        sa.Column('data_quality_score', sa.Integer()),            # 1 (best) – 5 (worst), PCAF scale
        sa.Column('estimation_method', sa.String(200)),
        sa.Column('estimation_uncertainty_pct', sa.Numeric(6, 2)),
        # Assurance
        sa.Column('is_assured', sa.Boolean(), server_default='false'),
        sa.Column('assurance_level', sa.String(20)),              # limited | reasonable
        sa.Column('assurance_provider', sa.String(200)),
        # Provenance
        sa.Column('data_source_type', sa.String(50)),
        # primary_measurement | secondary_estimation | third_party | public_registry
        # industry_database | model_output | management_estimate
        sa.Column('data_source_name', sa.String(200)),
        sa.Column('data_source_url', sa.Text()),
        sa.Column('report_page_reference', sa.String(50)),
        sa.Column('extraction_method', sa.String(50)),
        # manual | automated_etl | nlp_extraction | api_feed | verified_import
        # Comparatives
        sa.Column('prior_year_value', sa.Numeric(24, 6)),
        sa.Column('yoy_change_pct', sa.Numeric(8, 2)),
        sa.Column('base_year', sa.Integer()),
        sa.Column('base_year_value', sa.Numeric(24, 6)),
        sa.Column('change_vs_base_year_pct', sa.Numeric(8, 2)),
        # Restatement
        sa.Column('is_restated', sa.Boolean(), server_default='false'),
        sa.Column('restatement_reason', sa.Text()),
        sa.Column('original_value', sa.Numeric(24, 6)),
        # Metadata
        sa.Column('status', sa.String(30), server_default='draft'),
        # draft | under_review | approved | published | archived
        sa.Column('submitted_by', sa.String(100)),
        sa.Column('reviewed_by', sa.String(100)),
        sa.Column('approved_by', sa.String(100)),
        sa.Column('approved_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['entity_registry_id'], ['csrd_entity_registry.id'],
                                ondelete='CASCADE'),
        sa.CheckConstraint(
            "data_quality_score BETWEEN 1 AND 5 OR data_quality_score IS NULL",
            name='ck_kpi_dq_score'
        ),
        sa.CheckConstraint(
            "coverage_pct BETWEEN 0 AND 100 OR coverage_pct IS NULL",
            name='ck_kpi_coverage_pct'
        ),
        sa.CheckConstraint(
            "status IN ('draft','under_review','approved','published','archived')",
            name='ck_kpi_status'
        ),
        sa.CheckConstraint(
            "data_source_type IN ("
            "'primary_measurement','secondary_estimation','third_party',"
            "'public_registry','industry_database','model_output',"
            "'management_estimate') OR data_source_type IS NULL",
            name='ck_kpi_source_type'
        ),
        sa.UniqueConstraint('entity_registry_id', 'indicator_code', 'reporting_year',
                            name='uq_kpi_entity_indicator_year'),
    )
    op.create_index('ix_kpi_values_entity_year', 'csrd_kpi_values',
                    ['entity_registry_id', 'reporting_year'])
    op.create_index('ix_kpi_values_indicator', 'csrd_kpi_values',
                    ['indicator_code', 'reporting_year'])

    # ------------------------------------------------------------------
    # 5. csrd_materiality_topics
    #    Double materiality assessment per ESRS topic / sub-topic / IRO.
    #    Captures both impact materiality and financial materiality scores.
    # ------------------------------------------------------------------
    op.create_table(
        'csrd_materiality_topics',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_registry_id', UUID(as_uuid=True), nullable=False),
        sa.Column('reporting_year', sa.Integer(), nullable=False),
        # Topic identification
        sa.Column('esrs_topic', sa.String(10), nullable=False),
        # ESRS2 | E1..E5 | S1..S4 | G1
        sa.Column('sub_topic', sa.String(100)),
        sa.Column('iro_type', sa.String(20)),                     # impact | risk | opportunity
        sa.Column('iro_description', sa.Text()),
        sa.Column('value_chain_position', sa.String(50)),
        # own_operations | upstream | downstream | both
        # Impact materiality (ESRS AR16)
        sa.Column('impact_actual_negative', sa.Boolean(), server_default='false'),
        sa.Column('impact_potential_negative', sa.Boolean(), server_default='false'),
        sa.Column('impact_actual_positive', sa.Boolean(), server_default='false'),
        sa.Column('impact_potential_positive', sa.Boolean(), server_default='false'),
        sa.Column('impact_severity_score', sa.Integer()),          # 1–5
        sa.Column('impact_likelihood_score', sa.Integer()),        # 1–5
        sa.Column('impact_scale', sa.String(20)),                  # limited | moderate | severe
        sa.Column('impact_scope', sa.String(20)),                  # limited | moderate | widespread
        sa.Column('impact_irremediability', sa.String(20)),        # low | medium | high
        sa.Column('impact_materiality_score', sa.Numeric(4, 2)),   # 1.0 – 5.0
        sa.Column('is_material_impact', sa.Boolean(), server_default='false'),
        # Financial materiality (ESRS AR17)
        sa.Column('financial_risk_flag', sa.Boolean(), server_default='false'),
        sa.Column('financial_opportunity_flag', sa.Boolean(), server_default='false'),
        sa.Column('financial_time_horizon', sa.String(20)),        # short | medium | long
        sa.Column('financial_probability_score', sa.Integer()),    # 1–5
        sa.Column('financial_magnitude_score', sa.Integer()),      # 1–5
        sa.Column('financial_materiality_score', sa.Numeric(4, 2)),  # 1.0–5.0
        sa.Column('is_material_financial', sa.Boolean(), server_default='false'),
        # Overall materiality
        sa.Column('is_material_overall', sa.Boolean(), server_default='false'),
        sa.Column('materiality_conclusion', sa.Text()),
        # Stakeholder input
        sa.Column('stakeholder_groups_consulted', JSONB()),
        sa.Column('engagement_method', sa.String(200)),
        sa.Column('expert_input', sa.Text()),
        # Policy response
        sa.Column('disclosure_required', sa.Boolean(), server_default='false'),
        sa.Column('disclosure_requirement_codes', JSONB()),        # list of ESRS DRs triggered
        sa.Column('board_reviewed', sa.Boolean(), server_default='false'),
        sa.Column('board_review_date', sa.Date()),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['entity_registry_id'], ['csrd_entity_registry.id'],
                                ondelete='CASCADE'),
        sa.CheckConstraint(
            "impact_severity_score BETWEEN 1 AND 5 "
            "OR impact_severity_score IS NULL",
            name='ck_mat_impact_severity'
        ),
        sa.CheckConstraint(
            "financial_magnitude_score BETWEEN 1 AND 5 "
            "OR financial_magnitude_score IS NULL",
            name='ck_mat_financial_mag'
        ),
        sa.CheckConstraint(
            "iro_type IN ('impact','risk','opportunity') OR iro_type IS NULL",
            name='ck_mat_iro_type'
        ),
    )
    op.create_index('ix_materiality_entity_year', 'csrd_materiality_topics',
                    ['entity_registry_id', 'reporting_year', 'esrs_topic'])

    # ------------------------------------------------------------------
    # 6. csrd_disclosure_index
    #    Maps each ESRS disclosure requirement to where it appears in the
    #    published sustainability report (page, section, document URL).
    #    Enables automated completeness checking.
    # ------------------------------------------------------------------
    op.create_table(
        'csrd_disclosure_index',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_registry_id', UUID(as_uuid=True), nullable=False),
        sa.Column('reporting_year', sa.Integer(), nullable=False),
        sa.Column('indicator_code', sa.String(60), nullable=False),
        # Location in published report
        sa.Column('document_title', sa.String(500)),
        sa.Column('document_url', sa.Text()),
        sa.Column('document_type', sa.String(50)),
        # integrated_report | standalone_sustainability | annual_report
        # pillar3 | sfdr_periodic | taxonomy_appendix | website
        sa.Column('section_name', sa.String(500)),
        sa.Column('page_start', sa.Integer()),
        sa.Column('page_end', sa.Integer()),
        sa.Column('paragraph_ref', sa.String(100)),
        sa.Column('table_ref', sa.String(100)),
        # Disclosure status
        sa.Column('disclosure_status', sa.String(30)),
        # disclosed | omitted_immaterial | omitted_disproportionate
        # omitted_confidential | partial | not_applicable | not_assessed
        sa.Column('omission_reason', sa.Text()),
        sa.Column('omission_approved_by', sa.String(200)),
        # Quality flags
        sa.Column('meets_esrs_requirements', sa.Boolean()),
        sa.Column('completeness_score_pct', sa.Numeric(5, 2)),
        sa.Column('reviewer_notes', sa.Text()),
        sa.Column('xbrl_tagged', sa.Boolean(), server_default='false'),
        sa.Column('xbrl_tag_ref', sa.String(200)),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['entity_registry_id'], ['csrd_entity_registry.id'],
                                ondelete='CASCADE'),
        sa.CheckConstraint(
            "disclosure_status IN ("
            "'disclosed','omitted_immaterial','omitted_disproportionate',"
            "'omitted_confidential','partial','not_applicable','not_assessed') "
            "OR disclosure_status IS NULL",
            name='ck_disclosure_status'
        ),
    )
    op.create_index('ix_disclosure_index_entity_year', 'csrd_disclosure_index',
                    ['entity_registry_id', 'reporting_year'])

    # ------------------------------------------------------------------
    # 7. csrd_peer_benchmarks
    #    Sector-level percentile benchmarks for each KPI, computed from
    #    the aggregated csrd_kpi_values across all entities in the sector.
    # ------------------------------------------------------------------
    op.create_table(
        'csrd_peer_benchmarks',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('indicator_code', sa.String(60), nullable=False),
        sa.Column('reporting_year', sa.Integer(), nullable=False),
        sa.Column('sector', sa.String(100), nullable=False),
        sa.Column('region', sa.String(50)),                        # Global | EU | NA | APAC
        sa.Column('entity_count', sa.Integer()),
        # Descriptive statistics
        sa.Column('mean_value', sa.Numeric(24, 6)),
        sa.Column('median_value', sa.Numeric(24, 6)),
        sa.Column('p10_value', sa.Numeric(24, 6)),
        sa.Column('p25_value', sa.Numeric(24, 6)),
        sa.Column('p75_value', sa.Numeric(24, 6)),
        sa.Column('p90_value', sa.Numeric(24, 6)),
        sa.Column('min_value', sa.Numeric(24, 6)),
        sa.Column('max_value', sa.Numeric(24, 6)),
        sa.Column('std_dev', sa.Numeric(24, 6)),
        sa.Column('unit', sa.String(60)),
        # Best-in-class / worst-in-class
        sa.Column('best_in_class_entity_lei', sa.String(20)),
        sa.Column('best_in_class_value', sa.Numeric(24, 6)),
        sa.Column('worst_in_class_value', sa.Numeric(24, 6)),
        # Trend
        sa.Column('prior_year_median', sa.Numeric(24, 6)),
        sa.Column('yoy_median_change_pct', sa.Numeric(8, 2)),
        # Data source
        sa.Column('data_sources', JSONB()),                        # list of sources used
        sa.Column('benchmark_methodology', sa.Text()),
        sa.Column('computed_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()')),
        sa.UniqueConstraint('indicator_code', 'reporting_year', 'sector', 'region',
                            name='uq_peer_benchmark'),
    )
    op.create_index('ix_peer_benchmarks_indicator_year', 'csrd_peer_benchmarks',
                    ['indicator_code', 'reporting_year', 'sector'])

    # ------------------------------------------------------------------
    # 8. csrd_gap_tracker
    #    Structured gap between an entity's current disclosure state and
    #    the target state required by applicable ESRS / framework rules.
    # ------------------------------------------------------------------
    op.create_table(
        'csrd_gap_tracker',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_registry_id', UUID(as_uuid=True), nullable=False),
        sa.Column('assessment_date', sa.Date(), nullable=False),
        sa.Column('reporting_year_target', sa.Integer(), nullable=False),
        sa.Column('indicator_code', sa.String(60), nullable=False),
        sa.Column('framework', sa.String(50), nullable=False),
        # Gap description
        sa.Column('current_status', sa.String(50)),
        # not_started | data_not_available | partial | methodology_gap
        # system_gap | assurance_gap | complete
        sa.Column('target_status', sa.String(50), server_default='complete'),
        sa.Column('gap_description', sa.Text()),
        sa.Column('gap_category', sa.String(50)),
        # data_availability | methodology | system | governance | assurance
        # expertise | legal_constraint
        # Prioritisation
        sa.Column('priority', sa.String(10)),                      # critical | high | medium | low
        sa.Column('effort_estimate_days', sa.Integer()),
        sa.Column('cost_estimate_keur', sa.Numeric(10, 2)),
        sa.Column('risk_if_unaddressed', sa.Text()),
        sa.Column('regulatory_risk_flag', sa.Boolean(), server_default='false'),
        # Timeline
        sa.Column('target_close_date', sa.Date()),
        sa.Column('actual_close_date', sa.Date()),
        sa.Column('gap_status', sa.String(30), server_default='open'),
        # open | in_progress | closed | deferred | accepted_risk
        sa.Column('assigned_owner', sa.String(200)),
        sa.Column('assigned_team', sa.String(200)),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['entity_registry_id'], ['csrd_entity_registry.id'],
                                ondelete='CASCADE'),
        sa.CheckConstraint(
            "priority IN ('critical','high','medium','low') OR priority IS NULL",
            name='ck_gap_priority'
        ),
        sa.CheckConstraint(
            "gap_status IN ('open','in_progress','closed','deferred','accepted_risk')",
            name='ck_gap_status'
        ),
        sa.CheckConstraint(
            "gap_category IN ("
            "'data_availability','methodology','system','governance',"
            "'assurance','expertise','legal_constraint') OR gap_category IS NULL",
            name='ck_gap_category'
        ),
    )
    op.create_index('ix_gap_tracker_entity', 'csrd_gap_tracker',
                    ['entity_registry_id', 'reporting_year_target', 'gap_status'])

    # ------------------------------------------------------------------
    # 9. csrd_data_lineage
    #    Immutable audit trail: source → transformation → output for each
    #    KPI value.  Supports regulatory audit / spot-check workflows.
    # ------------------------------------------------------------------
    op.create_table(
        'csrd_data_lineage',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('kpi_value_id', UUID(as_uuid=True), nullable=False),
        sa.Column('entity_registry_id', UUID(as_uuid=True), nullable=False),
        sa.Column('indicator_code', sa.String(60), nullable=False),
        sa.Column('reporting_year', sa.Integer(), nullable=False),
        # Source
        sa.Column('source_system', sa.String(200)),
        sa.Column('source_table', sa.String(200)),
        sa.Column('source_record_id', sa.String(200)),
        sa.Column('source_document_url', sa.Text()),
        sa.Column('source_extraction_date', sa.DateTime(timezone=True)),
        sa.Column('raw_value', sa.Text()),
        sa.Column('raw_unit', sa.String(60)),
        # Transformation
        sa.Column('transformation_applied', sa.Text()),
        sa.Column('conversion_factor', sa.Numeric(20, 10)),
        sa.Column('emission_factor_used', sa.String(200)),
        sa.Column('emission_factor_value', sa.Numeric(20, 10)),
        sa.Column('emission_factor_source', sa.String(200)),
        sa.Column('gwp_basis', sa.String(30)),                     # AR4 | AR5 | AR6
        sa.Column('boundary_adjustment_notes', sa.Text()),
        # Output
        sa.Column('output_value', sa.Numeric(24, 6)),
        sa.Column('output_unit', sa.String(60)),
        sa.Column('calculation_formula', sa.Text()),
        sa.Column('calculation_script_ref', sa.String(500)),
        # Responsible parties
        sa.Column('calculated_by', sa.String(100)),
        sa.Column('reviewed_by', sa.String(100)),
        sa.Column('tool_name', sa.String(200)),
        sa.Column('tool_version', sa.String(50)),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['kpi_value_id'], ['csrd_kpi_values.id'],
                                ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['entity_registry_id'], ['csrd_entity_registry.id'],
                                ondelete='CASCADE'),
    )
    op.create_index('ix_lineage_kpi_value', 'csrd_data_lineage', ['kpi_value_id'])

    # ------------------------------------------------------------------
    # 10. csrd_assurance_log
    #     Third-party assurance engagement records per entity per year.
    # ------------------------------------------------------------------
    op.create_table(
        'csrd_assurance_log',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_registry_id', UUID(as_uuid=True), nullable=False),
        sa.Column('reporting_year', sa.Integer(), nullable=False),
        sa.Column('assurance_provider', sa.String(300), nullable=False),
        sa.Column('assurance_standard', sa.String(100)),
        # ISAE3000 | ISAE3410 | AA1000AS | IAASB_ISSA5000 | GRI | custom
        sa.Column('assurance_level', sa.String(20)),               # limited | reasonable
        sa.Column('engagement_start_date', sa.Date()),
        sa.Column('engagement_end_date', sa.Date()),
        sa.Column('opinion_date', sa.Date()),
        sa.Column('opinion_type', sa.String(30)),
        # unqualified | qualified | adverse | disclaimer
        sa.Column('scope_esrs_topics', JSONB()),                   # list e.g. ['E1','S1','G1']
        sa.Column('scope_indicators', JSONB()),                    # list of indicator_codes
        sa.Column('scope_boundary', sa.Text()),
        sa.Column('material_misstatement_found', sa.Boolean(), server_default='false'),
        sa.Column('material_misstatement_details', sa.Text()),
        sa.Column('key_findings', sa.Text()),
        sa.Column('recommendations', sa.Text()),
        sa.Column('management_response', sa.Text()),
        sa.Column('report_url', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['entity_registry_id'], ['csrd_entity_registry.id'],
                                ondelete='CASCADE'),
        sa.CheckConstraint(
            "assurance_level IN ('limited','reasonable') OR assurance_level IS NULL",
            name='ck_assurance_level'
        ),
        sa.CheckConstraint(
            "opinion_type IN ('unqualified','qualified','adverse','disclaimer') "
            "OR opinion_type IS NULL",
            name='ck_assurance_opinion'
        ),
    )

    # ------------------------------------------------------------------
    # 11. csrd_action_tracker
    #     Remediation actions linked to gaps, with owner, due date,
    #     status and evidence of completion.
    # ------------------------------------------------------------------
    op.create_table(
        'csrd_action_tracker',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_registry_id', UUID(as_uuid=True), nullable=False),
        sa.Column('gap_id', UUID(as_uuid=True)),                   # optional link to gap_tracker
        sa.Column('indicator_code', sa.String(60)),
        sa.Column('framework', sa.String(50)),
        sa.Column('action_title', sa.String(500), nullable=False),
        sa.Column('action_description', sa.Text()),
        sa.Column('action_category', sa.String(60)),
        # data_collection | methodology | system_build | governance
        # policy_development | training | reporting | assurance | legal
        sa.Column('priority', sa.String(10)),                      # critical | high | medium | low
        sa.Column('owner_name', sa.String(200)),
        sa.Column('owner_team', sa.String(200)),
        sa.Column('owner_email', sa.String(200)),
        sa.Column('sponsor_name', sa.String(200)),
        sa.Column('due_date', sa.Date()),
        sa.Column('completion_date', sa.Date()),
        sa.Column('reporting_year_target', sa.Integer()),
        sa.Column('status', sa.String(30), server_default='planned'),
        # planned | in_progress | completed | overdue | cancelled | on_hold
        sa.Column('completion_pct', sa.Integer()),                  # 0–100
        sa.Column('dependencies', JSONB()),                        # list of action IDs
        sa.Column('resources_required', sa.Text()),
        sa.Column('budget_keur', sa.Numeric(10, 2)),
        sa.Column('evidence_document_url', sa.Text()),
        sa.Column('last_update_notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['entity_registry_id'], ['csrd_entity_registry.id'],
                                ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['gap_id'], ['csrd_gap_tracker.id'],
                                ondelete='SET NULL'),
        sa.CheckConstraint(
            "status IN ("
            "'planned','in_progress','completed','overdue','cancelled','on_hold')",
            name='ck_action_status'
        ),
        sa.CheckConstraint(
            "completion_pct BETWEEN 0 AND 100 OR completion_pct IS NULL",
            name='ck_action_completion'
        ),
        sa.CheckConstraint(
            "priority IN ('critical','high','medium','low') OR priority IS NULL",
            name='ck_action_priority'
        ),
    )
    op.create_index('ix_action_tracker_entity', 'csrd_action_tracker',
                    ['entity_registry_id', 'status', 'due_date'])

    # ------------------------------------------------------------------
    # 12. csrd_target_registry
    #     All climate / sustainability targets declared by an entity
    #     across any framework (SBTi, CDP, Paris, SDG, CSRD E1-4, ISSB).
    # ------------------------------------------------------------------
    op.create_table(
        'csrd_target_registry',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_registry_id', UUID(as_uuid=True), nullable=False),
        sa.Column('target_name', sa.String(500), nullable=False),
        sa.Column('target_type', sa.String(60), nullable=False),
        # ghg_absolute | ghg_intensity | renewable_energy | energy_efficiency
        # water | waste | biodiversity | social | governance | finance_green
        # net_zero | carbon_neutral | science_based
        sa.Column('framework_source', sa.String(100)),
        # CSRD_E1-4 | SBTi | CDP | Paris_Agreement | ISSB_S2 | internal | other
        sa.Column('sbti_reference_number', sa.String(100)),
        sa.Column('scope_covered', JSONB()),                       # ['S1','S2','S3'] etc.
        sa.Column('base_year', sa.Integer()),
        sa.Column('base_year_value', sa.Numeric(20, 6)),
        sa.Column('base_year_unit', sa.String(60)),
        sa.Column('target_year', sa.Integer()),
        sa.Column('target_value', sa.Numeric(20, 6)),
        sa.Column('target_unit', sa.String(60)),
        sa.Column('target_reduction_pct', sa.Numeric(6, 2)),
        sa.Column('pathway', sa.String(60)),
        # 1.5C | WB2C | 2C | NGFS_NZ2050 | NGFS_DT | IEA_NZE | Paris_NDC | custom
        sa.Column('target_horizon', sa.String(20)),                # near_term | long_term | net_zero
        sa.Column('boundary', sa.String(100)),                     # operational_control | equity_share | etc.
        sa.Column('included_gases', JSONB()),                      # ['CO2','CH4','N2O','HFCs','PFCs','SF6','NF3']
        # Progress
        sa.Column('latest_year', sa.Integer()),
        sa.Column('latest_actual_value', sa.Numeric(20, 6)),
        sa.Column('progress_pct', sa.Numeric(6, 2)),              # % reduction achieved vs base
        sa.Column('on_track', sa.Boolean()),
        sa.Column('trajectory_data', JSONB()),                     # year → value series
        # Governance
        sa.Column('board_approved', sa.Boolean(), server_default='false'),
        sa.Column('board_approval_date', sa.Date()),
        sa.Column('externally_validated', sa.Boolean(), server_default='false'),
        sa.Column('validation_body', sa.String(200)),
        sa.Column('validation_date', sa.Date()),
        sa.Column('target_status', sa.String(30)),
        # active | achieved | cancelled | superseded | under_review
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['entity_registry_id'], ['csrd_entity_registry.id'],
                                ondelete='CASCADE'),
        sa.CheckConstraint(
            "target_horizon IN ('near_term','long_term','net_zero') "
            "OR target_horizon IS NULL",
            name='ck_target_horizon'
        ),
        sa.CheckConstraint(
            "target_status IN ("
            "'active','achieved','cancelled','superseded','under_review') "
            "OR target_status IS NULL",
            name='ck_target_status'
        ),
    )
    op.create_index('ix_target_registry_entity', 'csrd_target_registry',
                    ['entity_registry_id', 'target_type', 'target_year'])

    # ------------------------------------------------------------------
    # 13. csrd_transition_plan
    #     Transition plan milestones per ESRS E1-1 and IFRS S2.
    #     Captures decarbonisation pathway, capex plan, and CapEx-OpEx
    #     allocation by technology / abatement lever.
    # ------------------------------------------------------------------
    op.create_table(
        'csrd_transition_plan',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_registry_id', UUID(as_uuid=True), nullable=False),
        sa.Column('plan_version', sa.String(20), server_default='v1.0'),
        sa.Column('plan_published_date', sa.Date()),
        sa.Column('plan_review_date', sa.Date()),
        sa.Column('reporting_year', sa.Integer(), nullable=False),
        # Ambition level
        sa.Column('net_zero_target_year', sa.Integer()),
        sa.Column('interim_target_2030_pct_reduction', sa.Numeric(5, 2)),
        sa.Column('interim_target_2035_pct_reduction', sa.Numeric(5, 2)),
        sa.Column('interim_target_2040_pct_reduction', sa.Numeric(5, 2)),
        sa.Column('aligned_with_pathway', sa.String(60)),
        # 1.5C | WB2C | IEA_NZE | NGFS_NZ2050 | Paris_NDC | sector_pathway
        # Key levers (free-form JSONB for flexibility)
        sa.Column('abatement_levers', JSONB()),
        # [{lever, description, scope_covered, reduction_tco2e_by_2030,
        #   reduction_tco2e_by_2040, reduction_tco2e_by_2050, capex_required_meur}]
        # Financial plan
        sa.Column('total_green_capex_2025_2030_meur', sa.Numeric(14, 2)),
        sa.Column('total_green_capex_2031_2040_meur', sa.Numeric(14, 2)),
        sa.Column('total_green_capex_2041_2050_meur', sa.Numeric(14, 2)),
        sa.Column('carbon_price_assumption_2030_eur', sa.Numeric(8, 2)),
        sa.Column('carbon_price_assumption_2040_eur', sa.Numeric(8, 2)),
        sa.Column('carbon_price_assumption_2050_eur', sa.Numeric(8, 2)),
        sa.Column('stranded_asset_risk_meur', sa.Numeric(14, 2)),
        # Residual emissions plan
        sa.Column('residual_emissions_2050_tco2e', sa.Numeric(14, 2)),
        sa.Column('residual_emissions_offset_method', sa.String(200)),
        # nature_based | tech_ccs | high_quality_credits | direct_air_capture
        sa.Column('cdr_procurement_plan', sa.Text()),
        # Dependencies & risks
        sa.Column('policy_dependencies', sa.Text()),
        sa.Column('technology_dependencies', sa.Text()),
        sa.Column('transition_risks_identified', JSONB()),
        sa.Column('transition_opportunities_identified', JSONB()),
        # Governance
        sa.Column('board_oversight_mechanism', sa.Text()),
        sa.Column('management_incentives_linked', sa.Boolean(), server_default='false'),
        sa.Column('incentive_description', sa.Text()),
        sa.Column('external_review_body', sa.String(200)),
        sa.Column('external_review_date', sa.Date()),
        sa.Column('lock_in_asset_exposure_meur', sa.Numeric(14, 2)),
        sa.Column('just_transition_plan_in_place', sa.Boolean(), server_default='false'),
        sa.Column('just_transition_notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['entity_registry_id'], ['csrd_entity_registry.id'],
                                ondelete='CASCADE'),
        sa.UniqueConstraint('entity_registry_id', 'reporting_year', 'plan_version',
                            name='uq_transition_plan_entity_year_ver'),
    )


def downgrade():
    # Drop in reverse order to respect FK dependencies
    op.drop_table('csrd_transition_plan')
    op.drop_index('ix_target_registry_entity', table_name='csrd_target_registry')
    op.drop_table('csrd_target_registry')
    op.drop_index('ix_action_tracker_entity', table_name='csrd_action_tracker')
    op.drop_table('csrd_action_tracker')
    op.drop_table('csrd_assurance_log')
    op.drop_index('ix_lineage_kpi_value', table_name='csrd_data_lineage')
    op.drop_table('csrd_data_lineage')
    op.drop_index('ix_gap_tracker_entity', table_name='csrd_gap_tracker')
    op.drop_table('csrd_gap_tracker')
    op.drop_index('ix_peer_benchmarks_indicator_year', table_name='csrd_peer_benchmarks')
    op.drop_table('csrd_peer_benchmarks')
    op.drop_index('ix_disclosure_index_entity_year', table_name='csrd_disclosure_index')
    op.drop_table('csrd_disclosure_index')
    op.drop_index('ix_materiality_entity_year', table_name='csrd_materiality_topics')
    op.drop_table('csrd_materiality_topics')
    op.drop_index('ix_kpi_values_indicator', table_name='csrd_kpi_values')
    op.drop_index('ix_kpi_values_entity_year', table_name='csrd_kpi_values')
    op.drop_table('csrd_kpi_values')
    op.drop_index('ix_esrs_catalog_standard', table_name='csrd_esrs_catalog')
    op.drop_table('csrd_esrs_catalog')
    op.drop_table('csrd_framework_applicability')
    op.drop_table('csrd_entity_registry')
