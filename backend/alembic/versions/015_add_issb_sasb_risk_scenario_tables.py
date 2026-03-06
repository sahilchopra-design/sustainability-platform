"""Extend IFRS S1/S2 taxonomy — SASB industry metrics, scenario analysis,
carbon offset plans, disclosure relief tracking, risk/opportunity register,
and entity-defined time horizons.

Revision ID: 015_add_issb_sasb_risk_scenario_tables
Revises: 014_add_esrs_ig3_issb_s1s2_tables
Create Date: 2026-03-01

Source: IFRS S1 General Requirements (IFRS Foundation, June 2023)
        IFRS S2 Climate-Related Disclosures (IFRS Foundation, June 2023)
        SASB Standards — 20 industry sectors mapped in IFRS S2 Appendix B
        IFRS S2 Appendix B Cross-industry Metrics Reference

Rationale:
  Migration 014 stored SASB metrics, risk lists, scenario results, and
  offset plan data as JSONB arrays inside issb_s1_general and issb_s2_climate.
  This migration normalises those into proper relational tables to enable:
    - Per-metric filtering and aggregation for SASB compliance dashboards
    - Scenario-by-scenario comparison across entities / years
    - Granular offset tracking against SBTi and IFRS S2 §§13-16 requirements
    - Automated flagging of relief eligibility and deadlines
    - Risk/opportunity heat maps and portfolio-level aggregation

Tables (6):
  issb_sasb_industry_metrics      — one row per entity × year × SASB metric
  issb_s2_scenario_analysis       — one row per entity × year × scenario
  issb_s2_offset_plan             — carbon offset / carbon credit plan
  issb_disclosure_relief_tracker  — per-paragraph disclosure relief log
  issb_risk_opportunity_register  — typed physical / transition risk + opportunity
  issb_s2_time_horizons           — entity-defined time horizons with rationale

Down-revision: drops all six tables in reverse dependency order.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '015_add_issb_sasb_risk_scenario_tables'
down_revision = '014_add_esrs_ig3_issb_s1s2_tables'
branch_labels = None
depends_on = None


# ---------------------------------------------------------------------------
# Valid SASB industry codes referenced in IFRS S2 Appendix B
# Used for CHECK constraints — keeps data clean against the standard.
# ---------------------------------------------------------------------------
SASB_INDUSTRY_CODES = (
    'EM-CO',   # Coal Operations
    'EM-EP',   # Oil & Gas — Exploration & Production
    'EM-MD',   # Oil & Gas — Midstream
    'EM-RM',   # Oil & Gas — Refining & Marketing
    'EM-MM',   # Metals & Mining
    'IF-EU',   # Electric Utilities & Power
    'IF-GU',   # Gas Utilities & Distributors
    'IF-RE',   # Real Estate
    'IF-EN',   # Construction & Engineering
    'FN-CB',   # Commercial Banks
    'FN-IN',   # Insurance
    'FN-AC',   # Asset Management & Custody Activities
    'TR-AU',   # Automobiles
    'TR-TR',   # Road Transportation
    'TR-MT',   # Marine Transportation
    'TR-AL',   # Airlines
    'RT-CH',   # Chemicals
    'FB-AG',   # Agricultural Products
    'FB-PF',   # Food & Beverage Processing
    'RR-RE',   # Renewable Energy (separate from IF-RE Real Estate)
)

# GHG scenario names recognised in IFRS S2 §22 guidance
RECOGNISED_SCENARIOS = (
    'IEA_NZE',        # IEA Net Zero Emissions by 2050
    'IEA_APS',        # IEA Announced Pledges Scenario
    'IEA_SDS',        # IEA Sustainable Development Scenario
    'IEA_STEPS',      # IEA Stated Policies Scenario
    'NGFS_NZ2050',    # NGFS Net Zero 2050
    'NGFS_DT',        # NGFS Delayed Transition
    'NGFS_DISORDERLY',# NGFS Disorderly
    'NGFS_CT',        # NGFS Current Policies
    'IPCC_SSP1_19',   # IPCC SSP1-1.9 (~1.5°C)
    'IPCC_SSP1_26',   # IPCC SSP1-2.6 (~2°C)
    'IPCC_SSP2_45',   # IPCC SSP2-4.5 (~3°C)
    'IPCC_SSP5_85',   # IPCC SSP5-8.5 (>4°C)
    'RCP_26',         # RCP 2.6
    'RCP_45',         # RCP 4.5
    'RCP_85',         # RCP 8.5
    'ENTITY_DEFINED', # Entity's own proprietary scenario
    'OTHER',          # Any other recognised external scenario
)


def upgrade():

    # ======================================================================
    # 1. issb_sasb_industry_metrics
    #    One row per entity × reporting_year × SASB industry × metric.
    #    Covers all 20 SASB industry sectors referenced in IFRS S2 Appendix B.
    #    Source: IFRS S2 Appendix B §B4 – "Industry-based metrics"
    # ======================================================================
    op.create_table(
        'issb_sasb_industry_metrics',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_registry_id', UUID(as_uuid=True), nullable=False),
        sa.Column('reporting_year', sa.Integer(), nullable=False),

        # ---- SASB classification ----
        sa.Column('sasb_industry_code', sa.String(10), nullable=False),
        # Valid values: EM-CO, EM-EP, EM-MD, EM-RM, EM-MM, IF-EU, IF-GU, IF-RE,
        #   IF-EN, FN-CB, FN-IN, FN-AC, TR-AU, TR-TR, TR-MT, TR-AL, RT-CH,
        #   FB-AG, FB-PF, RR-RE

        sa.Column('sasb_industry_name', sa.String(200)),
        # e.g. 'Commercial Banks', 'Electric Utilities & Power'

        sa.Column('sasb_topic', sa.String(200)),
        # e.g. 'GHG Emissions', 'Energy Management', 'Water Management'

        sa.Column('sasb_metric_code', sa.String(50)),
        # SASB-assigned metric ID, e.g. 'FN-CB-110a.1', 'IF-EU-110a.1'

        sa.Column('sasb_metric_name', sa.String(500), nullable=False),
        # Full metric name as published, e.g. 'Gross global Scope 1 emissions'

        sa.Column('ifrs_s2_appendix_b_para', sa.String(50)),
        # e.g. 'B4', 'B5', 'B6' – IFRS S2 Appendix B paragraph

        # ---- Value capture ----
        sa.Column('value_numeric', sa.Numeric(24, 6)),
        # Quantitative value; precision covers MWh/tCO2e/m3/% etc.

        sa.Column('value_text', sa.Text()),
        # Narrative or categorical value (when metric is qualitative)

        sa.Column('unit_of_measurement', sa.String(100)),
        # e.g. 'tCO2e', 'MWh', '%', 'USD', 'ratio', 'm3'

        sa.Column('metric_is_mandatory', sa.Boolean(), server_default='true'),
        # Per IFRS S2 Appendix B designation (M = mandatory)

        sa.Column('disclosure_relief_applied', sa.Boolean(), server_default='false'),
        # True if entity is using phased-in relief (IFRS S2 §C3)

        # ---- Physical & transition risk context ----
        sa.Column('physical_risk_focus', sa.Text()),
        # Industry-specific physical risk narrative (from SASB standard)
        # e.g. 'Flooding, extreme heat affecting operations' (EM-CO)

        sa.Column('transition_risk_focus', sa.Text()),
        # Industry-specific transition risk narrative
        # e.g. 'Declining demand, stranded assets, carbon pricing' (EM-CO)

        # ---- Data quality ----
        sa.Column('calculation_methodology', sa.Text()),
        sa.Column('data_source', sa.String(500)),
        sa.Column('estimation_uncertainty_pct', sa.Numeric(5, 2)),
        sa.Column('is_third_party_verified', sa.Boolean(), server_default='false'),

        # ---- Timestamps ----
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()')),

        sa.ForeignKeyConstraint(
            ['entity_registry_id'], ['csrd_entity_registry.id'],
            ondelete='CASCADE'),
        sa.UniqueConstraint(
            'entity_registry_id', 'reporting_year',
            'sasb_industry_code', 'sasb_metric_code',
            name='uq_issb_sasb_metric_entity_year'),
        sa.CheckConstraint(
            "sasb_industry_code IN ("
            "'EM-CO','EM-EP','EM-MD','EM-RM','EM-MM',"
            "'IF-EU','IF-GU','IF-RE','IF-EN',"
            "'FN-CB','FN-IN','FN-AC',"
            "'TR-AU','TR-TR','TR-MT','TR-AL',"
            "'RT-CH','FB-AG','FB-PF','RR-RE')",
            name='ck_issb_sasb_industry_code'),
    )
    op.create_index(
        'ix_issb_sasb_entity_year',
        'issb_sasb_industry_metrics',
        ['entity_registry_id', 'reporting_year'])
    op.create_index(
        'ix_issb_sasb_industry_code',
        'issb_sasb_industry_metrics',
        ['sasb_industry_code'])

    # ======================================================================
    # 2. issb_s2_scenario_analysis
    #    One row per entity × reporting_year × climate scenario.
    #    IFRS S2 §§22-23: mandatory scenario analysis disclosure.
    #    Each scenario gets its own record with inputs, assumptions, results.
    # ======================================================================
    op.create_table(
        'issb_s2_scenario_analysis',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_registry_id', UUID(as_uuid=True), nullable=False),
        sa.Column('reporting_year', sa.Integer(), nullable=False),

        # ---- Scenario identification (IFRS S2 §22(b)(i)) ----
        sa.Column('scenario_name', sa.String(200), nullable=False),
        # Standardised name, e.g. 'IEA_NZE', 'NGFS_NZ2050', 'IPCC_SSP1_19'

        sa.Column('scenario_provider', sa.String(100)),
        # e.g. 'IEA', 'NGFS', 'IPCC', 'Entity-defined'

        sa.Column('scenario_type', sa.String(20)),
        # 'physical' | 'transition' | 'both'

        sa.Column('temperature_pathway_c', sa.Numeric(4, 2)),
        # Representative warming outcome: 1.5, 2.0, 3.0, 4.0 etc.

        sa.Column('scenario_version_year', sa.Integer()),
        # Publication year of the scenario version used, e.g. 2022 (IEA WEO 2022)

        # ---- Inputs and assumptions (IFRS S2 §22(b)(ii)) ----
        sa.Column('policy_stringency', sa.String(50)),
        # 'low' | 'medium' | 'high' — relative to current policies

        sa.Column('carbon_price_2030_eur_tco2e', sa.Numeric(10, 2)),
        sa.Column('carbon_price_2040_eur_tco2e', sa.Numeric(10, 2)),
        sa.Column('carbon_price_2050_eur_tco2e', sa.Numeric(10, 2)),

        sa.Column('technology_deployment_assumption', sa.String(200)),
        # e.g. 'Rapid CCS deployment assumed', 'EV fleet 100% by 2040'

        sa.Column('key_assumptions', JSONB()),
        # Full set of scenario inputs:
        # {gdp_growth_rate, energy_mix_2050, renewable_share_pct,
        #  policy_changes: [...], technology_milestones: [...]}

        # ---- Time horizons covered (IFRS S2 §22(b)(iii)) ----
        sa.Column('time_horizon', sa.String(20)),
        # 'short' (0-2y) | 'medium' (2-5y) | 'long' (5+y) | 'all'

        sa.Column('analysis_year_start', sa.Integer()),
        sa.Column('analysis_year_end', sa.Integer()),

        # ---- Results and implications (IFRS S2 §22(c)) ----
        sa.Column('financial_assets_at_risk_eur', sa.Numeric(18, 2)),
        # Total assets exposed to material risk under this scenario

        sa.Column('financial_assets_at_risk_pct', sa.Numeric(6, 3)),

        sa.Column('revenue_at_risk_eur', sa.Numeric(18, 2)),
        sa.Column('revenue_at_risk_pct', sa.Numeric(6, 3)),

        sa.Column('capex_required_eur', sa.Numeric(18, 2)),
        # Additional CapEx required to adapt / transition under this scenario

        sa.Column('opex_impact_eur', sa.Numeric(18, 2)),
        # Net OpEx impact (positive = cost, negative = saving)

        sa.Column('npv_impact_eur', sa.Numeric(18, 2)),
        # Net present value impact of strategy under this scenario

        sa.Column('resilience_conclusion', sa.String(20)),
        # 'resilient' | 'partially_resilient' | 'vulnerable'

        sa.Column('strategy_implications', sa.Text()),
        # Qualitative narrative: how strategy is affected / adapted

        sa.Column('business_model_resilience_description', sa.Text()),
        # Per IFRS S2 §22(c): business model resilience narrative

        sa.Column('scenario_results_quantitative', JSONB()),
        # Full quantitative results table for complex scenarios:
        # [{metric, value_2025, value_2030, value_2035, value_2040, value_2050}]

        # ---- Methodology ----
        sa.Column('analysis_conducted_by', sa.String(200)),
        # 'Internal' | 'External: [firm name]'

        sa.Column('analysis_date', sa.Date()),
        sa.Column('methodology_notes', sa.Text()),
        sa.Column('is_impracticable', sa.Boolean(), server_default='false'),
        # True if entity invokes IFRS S2 §C4 impracticability relief

        sa.Column('impracticability_reason', sa.Text()),

        # ---- Timestamps ----
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()')),

        sa.ForeignKeyConstraint(
            ['entity_registry_id'], ['csrd_entity_registry.id'],
            ondelete='CASCADE'),
        sa.UniqueConstraint(
            'entity_registry_id', 'reporting_year', 'scenario_name',
            name='uq_issb_scenario_entity_year'),
        sa.CheckConstraint(
            "scenario_type IN ('physical','transition','both')",
            name='ck_issb_scenario_type'),
        sa.CheckConstraint(
            "resilience_conclusion IN ('resilient','partially_resilient','vulnerable') "
            "OR resilience_conclusion IS NULL",
            name='ck_issb_resilience_conclusion'),
        sa.CheckConstraint(
            "time_horizon IN ('short','medium','long','all') "
            "OR time_horizon IS NULL",
            name='ck_issb_scenario_time_horizon'),
    )
    op.create_index(
        'ix_issb_scenario_entity_year',
        'issb_s2_scenario_analysis',
        ['entity_registry_id', 'reporting_year'])

    # ======================================================================
    # 3. issb_s2_offset_plan
    #    Carbon offset and carbon credit plan per entity × year.
    #    IFRS S2 §§13-16: entities using offsets to meet targets must disclose
    #    dependency, type (nature-based vs technology-based), and volumes.
    # ======================================================================
    op.create_table(
        'issb_s2_offset_plan',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_registry_id', UUID(as_uuid=True), nullable=False),
        sa.Column('reporting_year', sa.Integer(), nullable=False),

        # ---- Offset dependency (IFRS S2 §14) ----
        sa.Column('relies_on_carbon_offsets', sa.Boolean(), server_default='false'),

        sa.Column('total_reduction_target_pct_by_2030', sa.Numeric(6, 3)),
        # % of base-year emissions the entity targets to reduce by 2030

        sa.Column('total_reduction_target_pct_by_2035', sa.Numeric(6, 3)),
        sa.Column('total_reduction_target_pct_by_2040', sa.Numeric(6, 3)),
        sa.Column('total_reduction_target_pct_by_2050', sa.Numeric(6, 3)),

        sa.Column('reduction_via_internal_pct', sa.Numeric(6, 3)),
        # % of the total target met by genuine internal reductions
        # (excludes purchased offsets) — from IFRS S2 §14 guidance

        sa.Column('reduction_via_offsets_pct', sa.Numeric(6, 3)),
        # % of the total target reliant on external carbon credits

        # ---- Current offset use (IFRS S2 §15(a)) ----
        sa.Column('current_nature_based_offsets_tco2e', sa.Numeric(18, 3)),
        # Tonnes retired in reporting year: forestry, blue carbon, soil etc.

        sa.Column('current_tech_based_offsets_tco2e', sa.Numeric(18, 3)),
        # DAC, BECCS, mineralisation etc.

        sa.Column('total_offsets_retired_tco2e', sa.Numeric(18, 3)),
        # Sum of all credits retired during reporting year

        # ---- Planned future offset use (IFRS S2 §15(b)) ----
        sa.Column('planned_nature_based_offsets_tco2e_2030', sa.Numeric(18, 3)),
        sa.Column('planned_nature_based_offsets_tco2e_2040', sa.Numeric(18, 3)),
        sa.Column('planned_nature_based_offsets_tco2e_2050', sa.Numeric(18, 3)),

        sa.Column('planned_tech_based_offsets_tco2e_2030', sa.Numeric(18, 3)),
        sa.Column('planned_tech_based_offsets_tco2e_2040', sa.Numeric(18, 3)),
        sa.Column('planned_tech_based_offsets_tco2e_2050', sa.Numeric(18, 3)),

        # ---- Credit quality (IFRS S2 §16) ----
        sa.Column('offset_verification_standards', JSONB()),
        # List of standards used: ['VCS', 'Gold Standard', 'CAR', 'ACR',
        #   'Article 6.2 Compliant', 'Article 6.4 Compliant']

        sa.Column('corresponding_adjustment_required', sa.Boolean()),
        # True = host country applies CA under Paris Agreement Article 6

        sa.Column('corresponding_adjustment_secured_pct', sa.Numeric(6, 3)),
        # % of planned credits with confirmed corresponding adjustment

        sa.Column('additionality_verified', sa.Boolean()),
        sa.Column('permanence_risk_buffer_pct', sa.Numeric(6, 3)),
        # Buffer pool % held against reversal risk (e.g. wildfire destroying forest)

        sa.Column('offset_quality_criteria', JSONB()),
        # Checklist: {additionality, permanence, measurable, verifiable,
        #   co_benefits: bool, sdg_alignment: [goal_numbers]}

        # ---- Reversal tracking ----
        sa.Column('reversals_reported_tco2e', sa.Numeric(18, 3)),
        # Reversals of previously credited removals in reporting year

        sa.Column('replacement_credits_procured_tco2e', sa.Numeric(18, 3)),
        # Credits procured to replace reversed credits

        # ---- Providers and strategy ----
        sa.Column('primary_offset_providers', JSONB()),
        # [{provider_name, country, project_type, annual_volume_tco2e}]

        sa.Column('offset_procurement_strategy', sa.Text()),
        # Narrative description of the procurement strategy

        sa.Column('sbti_offset_boundary_compliant', sa.Boolean()),
        # Whether offset use complies with SBTi's 10% residual emissions rule

        sa.Column('target_year_net_zero', sa.Integer()),

        # ---- Notes ----
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()')),

        sa.ForeignKeyConstraint(
            ['entity_registry_id'], ['csrd_entity_registry.id'],
            ondelete='CASCADE'),
        sa.UniqueConstraint(
            'entity_registry_id', 'reporting_year',
            name='uq_issb_offset_plan_entity_year'),
    )

    # ======================================================================
    # 4. issb_disclosure_relief_tracker
    #    Per-paragraph disclosure relief log.
    #    Tracks each IFRS S1/S2 paragraph where an entity applies relief,
    #    including basis, partial disclosures, and remediation timeline.
    #
    #    Relief provisions:
    #      - IFRS S1 §C1: Comparative information relief (Year 1)
    #      - IFRS S2 §C2: Scope 3 relief (Year 1 optional; Years 2+ with cats)
    #      - IFRS S2 §C4: Scenario analysis impracticability
    #      - IFRS S2 §C5: Financed emissions relief for FIs (Year 1)
    #      - Proportionality / undue cost provisions
    # ======================================================================
    op.create_table(
        'issb_disclosure_relief_tracker',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_registry_id', UUID(as_uuid=True), nullable=False),
        sa.Column('reporting_year', sa.Integer(), nullable=False),

        # ---- Disclosure reference ----
        sa.Column('standard', sa.String(10), nullable=False),
        # 'IFRS S1' | 'IFRS S2'

        sa.Column('paragraph_ref', sa.String(50), nullable=False),
        # e.g. 'Para 29(a)(iii)', 'Para 22', 'Appendix B Para B4'

        sa.Column('metric_category', sa.String(200)),
        # e.g. 'Scope 3 GHG Emissions', 'Scenario Analysis', 'SASB Metrics'
        # Matches column 'Metric Category' from IFRS S2 Metrics Reference sheet

        sa.Column('metric_name', sa.String(500)),
        # e.g. 'Absolute Scope 3 GHG emissions'

        # ---- Relief basis ----
        sa.Column('relief_basis', sa.String(100), nullable=False),
        # 'Year1_Optional' | 'Impracticable' | 'Undue_Cost' |
        # 'Commercially_Sensitive' | 'Phase_In_Year1' | 'Phase_In_Year2'

        sa.Column('relief_active', sa.Boolean(), nullable=False,
                  server_default='true'),

        sa.Column('relief_description', sa.Text()),
        # Specific explanation of why relief is being applied

        # ---- Partial disclosure ----
        sa.Column('partial_disclosure_provided', sa.Boolean(),
                  server_default='false'),
        # True if entity provides partial disclosure even while claiming relief

        sa.Column('partial_disclosure_description', sa.Text()),
        # What partial information was provided

        sa.Column('partial_value_numeric', sa.Numeric(18, 3)),
        # If a partial quantitative estimate is disclosed

        sa.Column('partial_value_unit', sa.String(50)),

        # ---- Remediation timeline ----
        sa.Column('expected_full_disclosure_year', sa.Integer()),
        # Year by which entity expects to provide full disclosure

        sa.Column('remediation_actions', sa.Text()),
        # Steps being taken to achieve full disclosure capability

        sa.Column('data_gap_identified', sa.Text()),
        # Specific data gap preventing full disclosure

        # ---- Governance / audit ----
        sa.Column('board_approved_relief', sa.Boolean(), server_default='false'),
        sa.Column('auditor_acknowledged', sa.Boolean(), server_default='false'),
        sa.Column('regulator_notified', sa.Boolean(), server_default='false'),

        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()')),

        sa.ForeignKeyConstraint(
            ['entity_registry_id'], ['csrd_entity_registry.id'],
            ondelete='CASCADE'),
        sa.UniqueConstraint(
            'entity_registry_id', 'reporting_year', 'standard', 'paragraph_ref',
            name='uq_issb_relief_entity_year_para'),
        sa.CheckConstraint(
            "standard IN ('IFRS S1','IFRS S2')",
            name='ck_issb_relief_standard'),
        sa.CheckConstraint(
            "relief_basis IN ("
            "'Year1_Optional','Impracticable','Undue_Cost',"
            "'Commercially_Sensitive','Phase_In_Year1','Phase_In_Year2')",
            name='ck_issb_relief_basis'),
    )
    op.create_index(
        'ix_issb_relief_entity_year',
        'issb_disclosure_relief_tracker',
        ['entity_registry_id', 'reporting_year'])

    # ======================================================================
    # 5. issb_risk_opportunity_register
    #    Granular, typed risk and opportunity register.
    #    Replaces JSONB arrays in issb_s2_climate.physical_risks_identified
    #    and issb_s2_climate.transition_risks_identified with proper rows,
    #    enabling heat maps, aggregation, and portfolio-level analytics.
    #
    #    Physical risks: IFRS S2 §18(a) acute + chronic
    #    Transition risks: IFRS S2 §18(b) policy/legal, technology, market, rep.
    #    Opportunities: IFRS S2 §19 resource efficiency, energy, products, markets
    # ======================================================================
    op.create_table(
        'issb_risk_opportunity_register',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_registry_id', UUID(as_uuid=True), nullable=False),
        sa.Column('reporting_year', sa.Integer(), nullable=False),

        # ---- Classification ----
        sa.Column('entry_type', sa.String(20), nullable=False),
        # 'physical_risk' | 'transition_risk' | 'opportunity'

        sa.Column('physical_risk_category', sa.String(20)),
        # 'acute' | 'chronic' | NULL (for non-physical entries)

        sa.Column('physical_hazard_type', sa.String(100)),
        # For physical risks: 'flood', 'wildfire', 'extreme_heat', 'hurricane',
        # 'drought', 'sea_level_rise', 'permafrost_thaw', 'precipitation_shift',
        # 'water_stress', 'cold_wave', 'landslide', 'other'

        sa.Column('transition_risk_category', sa.String(30)),
        # 'policy_legal' | 'technology' | 'market' | 'reputation' | NULL

        sa.Column('opportunity_category', sa.String(30)),
        # 'resource_efficiency' | 'energy_source' | 'products_services' |
        # 'markets' | 'resilience' | NULL

        # ---- Description and location ----
        sa.Column('name', sa.String(500), nullable=False),
        # Short name, e.g. 'Coastal flooding at Rotterdam refinery'

        sa.Column('description', sa.Text()),

        sa.Column('tcfd_category', sa.String(50)),
        # TCFD alignment: 'Physical - Acute', 'Physical - Chronic',
        # 'Transition - Policy', 'Transition - Technology', 'Opportunity'

        sa.Column('value_chain_position', sa.String(30)),
        # 'upstream' | 'own_operations' | 'downstream' | 'all'

        sa.Column('affected_business_segment', sa.String(200)),
        # Business unit, geography, or asset type affected

        sa.Column('geographic_scope', JSONB()),
        # List of countries / regions where this risk/opportunity manifests

        # ---- Time horizon (IFRS S2 §22(b)(iii)) ----
        sa.Column('time_horizon', sa.String(20), nullable=False),
        # 'short' | 'medium' | 'long' | 'all'

        # ---- Assessment ----
        sa.Column('likelihood', sa.String(20)),
        # 'low' | 'medium' | 'high' | 'very_high'

        sa.Column('magnitude', sa.String(20)),
        # 'low' | 'medium' | 'high' | 'very_high'

        sa.Column('risk_score', sa.Numeric(5, 2)),
        # Composite: likelihood × magnitude (normalised 0-100)

        sa.Column('is_material', sa.Boolean(), server_default='false'),

        # ---- Financial effects ----
        sa.Column('financial_effect_direction', sa.String(20)),
        # 'positive' | 'negative' | 'neutral'

        sa.Column('estimated_financial_effect_eur', sa.Numeric(18, 2)),
        # BENCHMARK flag — estimated impact on profit/loss (+ = opportunity gain)

        sa.Column('assets_affected_eur', sa.Numeric(18, 2)),
        # Total asset book value exposed (S2 §B12-B13)

        sa.Column('assets_affected_pct', sa.Numeric(6, 3)),

        sa.Column('revenue_affected_eur', sa.Numeric(18, 2)),
        sa.Column('revenue_affected_pct', sa.Numeric(6, 3)),

        sa.Column('capex_required_to_address_eur', sa.Numeric(18, 2)),
        # CapEx needed to mitigate this risk or capture this opportunity

        # ---- Scenario linkage ----
        sa.Column('scenario_name_ref', sa.String(200)),
        # Scenario under which this assessment was made (FK-free, soft ref)

        sa.Column('scenario_temperature_c', sa.Numeric(4, 2)),

        # ---- Management response ----
        sa.Column('management_response', sa.Text()),
        # How the entity is managing / responding to this entry

        sa.Column('adaptation_mitigation_measures', JSONB()),
        # [{measure, cost_eur, expected_reduction_pct, implementation_year}]

        sa.Column('residual_risk_after_response', sa.String(20)),
        # 'low' | 'medium' | 'high' — after applying management measures

        # ---- Reference ----
        sa.Column('ifrs_s2_para_ref', sa.String(50)),
        # e.g. 'Para 18(a)', 'Para 18(b)', 'Para 19'

        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()')),

        sa.ForeignKeyConstraint(
            ['entity_registry_id'], ['csrd_entity_registry.id'],
            ondelete='CASCADE'),
        sa.CheckConstraint(
            "entry_type IN ('physical_risk','transition_risk','opportunity')",
            name='ck_issb_ror_entry_type'),
        sa.CheckConstraint(
            "physical_risk_category IN ('acute','chronic') "
            "OR physical_risk_category IS NULL",
            name='ck_issb_ror_physical_cat'),
        sa.CheckConstraint(
            "transition_risk_category IN "
            "('policy_legal','technology','market','reputation') "
            "OR transition_risk_category IS NULL",
            name='ck_issb_ror_transition_cat'),
        sa.CheckConstraint(
            "opportunity_category IN "
            "('resource_efficiency','energy_source','products_services',"
            "'markets','resilience') "
            "OR opportunity_category IS NULL",
            name='ck_issb_ror_opportunity_cat'),
        sa.CheckConstraint(
            "time_horizon IN ('short','medium','long','all')",
            name='ck_issb_ror_time_horizon'),
        sa.CheckConstraint(
            "likelihood IN ('low','medium','high','very_high') "
            "OR likelihood IS NULL",
            name='ck_issb_ror_likelihood'),
        sa.CheckConstraint(
            "magnitude IN ('low','medium','high','very_high') "
            "OR magnitude IS NULL",
            name='ck_issb_ror_magnitude'),
        sa.CheckConstraint(
            "financial_effect_direction IN ('positive','negative','neutral') "
            "OR financial_effect_direction IS NULL",
            name='ck_issb_ror_effect_direction'),
        sa.CheckConstraint(
            "value_chain_position IN ('upstream','own_operations','downstream','all') "
            "OR value_chain_position IS NULL",
            name='ck_issb_ror_value_chain'),
    )
    op.create_index(
        'ix_issb_ror_entity_year',
        'issb_risk_opportunity_register',
        ['entity_registry_id', 'reporting_year'])
    op.create_index(
        'ix_issb_ror_entry_type',
        'issb_risk_opportunity_register',
        ['entry_type'])
    op.create_index(
        'ix_issb_ror_material',
        'issb_risk_opportunity_register',
        ['entity_registry_id', 'is_material'])

    # ======================================================================
    # 6. issb_s2_time_horizons
    #    Entity-defined time horizons with rationale.
    #    IFRS S2 §22(b)(iii): entities must disclose the time horizons they
    #    use for scenario analysis and risk/opportunity assessments, and the
    #    basis for defining them.
    #    One row per entity × reporting_year × horizon_type (3 rows per cycle).
    # ======================================================================
    op.create_table(
        'issb_s2_time_horizons',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_registry_id', UUID(as_uuid=True), nullable=False),
        sa.Column('reporting_year', sa.Integer(), nullable=False),

        sa.Column('horizon_type', sa.String(10), nullable=False),
        # 'short' | 'medium' | 'long'

        # ---- Time horizon definition ----
        sa.Column('start_year', sa.Integer()),
        # Relative to reporting_year; e.g. 0 for current year, 3 for 3 years out

        sa.Column('end_year', sa.Integer()),
        # e.g. 2, 5, 30 — aligned with industry planning cycles

        sa.Column('typical_definition', sa.String(50)),
        # From IFRS S2 guidance: '0-2 years', '2-5 years', '5+ years'

        sa.Column('entity_specific_rationale', sa.Text()),
        # Why the entity uses these specific boundaries
        # e.g. 'Aligned with 5-year strategic plan review cycle'

        sa.Column('differs_from_typical', sa.Boolean(), server_default='false'),
        # True if entity's definition differs from the IFRS S2 typical range

        sa.Column('deviation_explanation', sa.Text()),
        # Explanation if differs_from_typical = true

        # ---- Risk-type overrides ----
        sa.Column('has_risk_type_specific_horizons', sa.Boolean(),
                  server_default='false'),
        # True if entity uses different horizons for physical vs transition risk

        sa.Column('physical_risk_end_year_override', sa.Integer()),
        # End year override for physical risk (often longer: 30+ years for RE)

        sa.Column('transition_risk_end_year_override', sa.Integer()),
        # End year override for transition risk (often shorter: 10-15 years)

        # ---- Disclosure context ----
        sa.Column('disclosed_in_report', sa.Boolean(), server_default='true'),
        sa.Column('report_section_reference', sa.String(200)),

        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()')),

        sa.ForeignKeyConstraint(
            ['entity_registry_id'], ['csrd_entity_registry.id'],
            ondelete='CASCADE'),
        sa.UniqueConstraint(
            'entity_registry_id', 'reporting_year', 'horizon_type',
            name='uq_issb_time_horizon_entity_year_type'),
        sa.CheckConstraint(
            "horizon_type IN ('short','medium','long')",
            name='ck_issb_horizon_type'),
    )
    op.create_index(
        'ix_issb_time_horizons_entity_year',
        'issb_s2_time_horizons',
        ['entity_registry_id', 'reporting_year'])


def downgrade():
    op.drop_index('ix_issb_time_horizons_entity_year',
                  table_name='issb_s2_time_horizons')
    op.drop_table('issb_s2_time_horizons')

    op.drop_index('ix_issb_ror_material', table_name='issb_risk_opportunity_register')
    op.drop_index('ix_issb_ror_entry_type', table_name='issb_risk_opportunity_register')
    op.drop_index('ix_issb_ror_entity_year', table_name='issb_risk_opportunity_register')
    op.drop_table('issb_risk_opportunity_register')

    op.drop_index('ix_issb_relief_entity_year',
                  table_name='issb_disclosure_relief_tracker')
    op.drop_table('issb_disclosure_relief_tracker')

    op.drop_table('issb_s2_offset_plan')

    op.drop_index('ix_issb_scenario_entity_year',
                  table_name='issb_s2_scenario_analysis')
    op.drop_table('issb_s2_scenario_analysis')

    op.drop_index('ix_issb_sasb_industry_code',
                  table_name='issb_sasb_industry_metrics')
    op.drop_index('ix_issb_sasb_entity_year',
                  table_name='issb_sasb_industry_metrics')
    op.drop_table('issb_sasb_industry_metrics')
