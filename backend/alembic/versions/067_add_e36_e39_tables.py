"""Add E36-E39 tables: Basel III Liquidity, Social Taxonomy, Forced Labour, Transition Finance

Revision ID: 067
Revises: 066
Create Date: 2026-03-17

Tables created:
  basel3_liquidity_assessments    — LCR / NSFR / ALM gap / liquidity stress (E36)
  basel3_liquidity_time_buckets   — Per-bucket repricing gap / EVE / NII (E36)
  social_taxonomy_assessments     — EU Social Taxonomy 3-objective + IMP 5-dim scoring (E37)
  impact_portfolio_holdings       — Per-holding IMP scores, SDG alignment, Art 9 eligibility (E37)
  forced_labour_assessments       — ILO 11-indicator + UK MSA + EU FLR import risk (E38)
  forced_labour_supplier_nodes    — Per-supplier forced labour risk scores (E38)
  transition_finance_classifications — GFANZ 4-category + TPT credibility + loan book TFR (E39)
  transition_loan_book_positions  — Per-exposure GFANZ category + sector pathway gap (E39)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "067"
down_revision = "066"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # E36 — Basel III Liquidity: basel3_liquidity_assessments
    # ------------------------------------------------------------------
    op.create_table(
        "basel3_liquidity_assessments",
        sa.Column("id", sa.Text, primary_key=True, server_default=sa.text("gen_random_uuid()::text")),
        sa.Column("assessment_id", sa.Text, nullable=False, unique=True),
        sa.Column("entity_id", sa.Text, nullable=False),
        sa.Column("entity_name", sa.Text, nullable=False),
        sa.Column("reporting_date", sa.Text, nullable=True),
        sa.Column("scenario_id", sa.Text, nullable=True),          # NGFS/EBA scenario
        # LCR
        sa.Column("lcr_pct", sa.Float, nullable=True),             # min 100%
        sa.Column("hqla_stock_mn", sa.Float, nullable=True),       # Level 1 + 2A + 2B
        sa.Column("hqla_level1_mn", sa.Float, nullable=True),
        sa.Column("hqla_level2a_mn", sa.Float, nullable=True),
        sa.Column("hqla_level2b_mn", sa.Float, nullable=True),
        sa.Column("net_outflow_30d_mn", sa.Float, nullable=True),
        sa.Column("gross_outflow_mn", sa.Float, nullable=True),
        sa.Column("gross_inflow_mn", sa.Float, nullable=True),
        sa.Column("climate_hqla_haircut_bps", sa.Float, nullable=True),
        # NSFR
        sa.Column("nsfr_pct", sa.Float, nullable=True),            # min 100%
        sa.Column("asf_mn", sa.Float, nullable=True),
        sa.Column("rsf_mn", sa.Float, nullable=True),
        sa.Column("asf_breakdown", JSONB, nullable=True),          # by liability class
        sa.Column("rsf_breakdown", JSONB, nullable=True),          # by asset class
        # Liquidity Stress
        sa.Column("survival_horizon_days", sa.Integer, nullable=True),
        sa.Column("liquidity_at_risk_mn", sa.Float, nullable=True),
        sa.Column("stress_outflow_deposit_mn", sa.Float, nullable=True),
        sa.Column("stress_outflow_wholesale_mn", sa.Float, nullable=True),
        # IRRBB / ALM
        sa.Column("eve_sensitivity_pct", sa.Float, nullable=True), # +200bps shock
        sa.Column("nii_sensitivity_pct", sa.Float, nullable=True), # 12m NII
        sa.Column("duration_gap_years", sa.Float, nullable=True),
        sa.Column("concentration_risk_score", sa.Float, nullable=True),
        # Monitoring tools (BCBS 238)
        sa.Column("monitoring_metrics", JSONB, nullable=True),     # CONC, CASHF, ILP, RunOff
        sa.Column("stress_assumptions", JSONB, nullable=True),
        sa.Column("regulatory_breaches", JSONB, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_basel3_liquidity_assessments_entity_id", "basel3_liquidity_assessments", ["entity_id"])

    op.create_table(
        "basel3_liquidity_time_buckets",
        sa.Column("id", sa.Text, primary_key=True, server_default=sa.text("gen_random_uuid()::text")),
        sa.Column("assessment_id", sa.Text, nullable=False),       # soft ref
        sa.Column("bucket", sa.Text, nullable=False),              # overnight/1w/1m/3m/6m/1y/>1y
        sa.Column("assets_mn", sa.Float, nullable=True),
        sa.Column("liabilities_mn", sa.Float, nullable=True),
        sa.Column("gap_mn", sa.Float, nullable=True),
        sa.Column("cumulative_gap_mn", sa.Float, nullable=True),
        sa.Column("eve_delta_mn", sa.Float, nullable=True),
        sa.Column("nii_delta_mn", sa.Float, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_basel3_liquidity_time_buckets_assessment_id", "basel3_liquidity_time_buckets", ["assessment_id"])

    # ------------------------------------------------------------------
    # E37 — Social Taxonomy & Impact: social_taxonomy_assessments
    # ------------------------------------------------------------------
    op.create_table(
        "social_taxonomy_assessments",
        sa.Column("id", sa.Text, primary_key=True, server_default=sa.text("gen_random_uuid()::text")),
        sa.Column("assessment_id", sa.Text, nullable=False, unique=True),
        sa.Column("entity_id", sa.Text, nullable=False),
        sa.Column("entity_name", sa.Text, nullable=False),
        sa.Column("reporting_period", sa.Text, nullable=True),
        sa.Column("assessment_type", sa.Text, nullable=True),      # company/fund/project/bond
        # EU Social Taxonomy 3 objectives
        sa.Column("decent_work_score", sa.Float, nullable=True),
        sa.Column("living_standards_score", sa.Float, nullable=True),
        sa.Column("inclusive_communities_score", sa.Float, nullable=True),
        sa.Column("social_taxonomy_aligned_pct", sa.Float, nullable=True),
        sa.Column("dnsh_social_flags", sa.Integer, nullable=True),
        # SFDR Art 2(17) sustainable investment
        sa.Column("sfdr_sustainable_investment_pct", sa.Float, nullable=True),
        sa.Column("sfdr_dnsh_pass", sa.Boolean, nullable=True),
        sa.Column("sfdr_governance_pass", sa.Boolean, nullable=True),
        # IMP 5 dimensions
        sa.Column("imp_what_score", sa.Float, nullable=True),
        sa.Column("imp_who_score", sa.Float, nullable=True),
        sa.Column("imp_how_much_score", sa.Float, nullable=True),
        sa.Column("imp_contribution_score", sa.Float, nullable=True),
        sa.Column("imp_risk_score", sa.Float, nullable=True),
        sa.Column("imp_composite_score", sa.Float, nullable=True),
        # Impact outputs
        sa.Column("sdg_alignment", JSONB, nullable=True),          # per-SDG contribution
        sa.Column("iris_plus_metrics", JSONB, nullable=True),      # key IRIS+ indicators
        sa.Column("additionality_score", sa.Float, nullable=True),
        sa.Column("beneficiaries_reached", sa.Integer, nullable=True),
        sa.Column("living_wage_coverage_pct", sa.Float, nullable=True),
        sa.Column("gender_pay_gap_pct", sa.Float, nullable=True),
        sa.Column("reporting_standard", sa.Text, nullable=True),   # sdg_impact/eu_social_bond/imp/combined
        sa.Column("cross_framework", JSONB, nullable=True),        # SFDR PAI #9-14, ESRS S1-S4 mapping
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_social_taxonomy_assessments_entity_id", "social_taxonomy_assessments", ["entity_id"])

    op.create_table(
        "impact_portfolio_holdings",
        sa.Column("id", sa.Text, primary_key=True, server_default=sa.text("gen_random_uuid()::text")),
        sa.Column("assessment_id", sa.Text, nullable=False),       # soft ref
        sa.Column("holding_id", sa.Text, nullable=False),
        sa.Column("holding_name", sa.Text, nullable=True),
        sa.Column("weight_pct", sa.Float, nullable=True),
        sa.Column("imp_composite_score", sa.Float, nullable=True),
        sa.Column("sdg_primary", sa.Text, nullable=True),          # primary SDG e.g. "SDG 7"
        sa.Column("art9_eligible", sa.Boolean, nullable=True),
        sa.Column("dnsh_flag", sa.Boolean, nullable=True),
        sa.Column("governance_flag", sa.Boolean, nullable=True),
        sa.Column("additionality_score", sa.Float, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_impact_portfolio_holdings_assessment_id", "impact_portfolio_holdings", ["assessment_id"])

    # ------------------------------------------------------------------
    # E38 — Forced Labour: forced_labour_assessments
    # ------------------------------------------------------------------
    op.create_table(
        "forced_labour_assessments",
        sa.Column("id", sa.Text, primary_key=True, server_default=sa.text("gen_random_uuid()::text")),
        sa.Column("assessment_id", sa.Text, nullable=False, unique=True),
        sa.Column("entity_id", sa.Text, nullable=False),
        sa.Column("entity_name", sa.Text, nullable=False),
        sa.Column("sector", sa.Text, nullable=True),
        sa.Column("reporting_year", sa.Integer, nullable=True),
        sa.Column("supply_chain_nodes_screened", sa.Integer, nullable=True),
        sa.Column("high_risk_suppliers_pct", sa.Float, nullable=True),
        sa.Column("ilo_indicator_flags", JSONB, nullable=True),    # count per ILO indicator
        # EU Forced Labour Regulation 2024/3015
        sa.Column("eu_flr_import_risk", sa.Text, nullable=True),  # low/medium/high/critical
        sa.Column("art7_investigation_trigger", sa.Boolean, nullable=True),
        sa.Column("art8_database_match", sa.Boolean, nullable=True),
        # UK Modern Slavery Act
        sa.Column("uk_msa_score", sa.Float, nullable=True),        # 0-30
        sa.Column("uk_msa_disclosure_areas_met", sa.Integer, nullable=True), # of 6
        # Other jurisdictions
        sa.Column("california_scatca_compliance", sa.Boolean, nullable=True),
        sa.Column("lksg_prohibited_practice_flag", sa.Boolean, nullable=True),
        # Compliance programme
        sa.Column("compliance_programme_maturity", sa.Text, nullable=True),
        sa.Column("audit_coverage_pct", sa.Float, nullable=True),
        sa.Column("grievance_mechanism_score", sa.Float, nullable=True),
        sa.Column("remediation_cases_open", sa.Integer, nullable=True),
        # Cross-framework
        sa.Column("csrd_s2_linkage", JSONB, nullable=True),
        sa.Column("csddd_hr01_linkage", JSONB, nullable=True),
        sa.Column("priority_actions", JSONB, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_forced_labour_assessments_entity_id", "forced_labour_assessments", ["entity_id"])

    op.create_table(
        "forced_labour_supplier_nodes",
        sa.Column("id", sa.Text, primary_key=True, server_default=sa.text("gen_random_uuid()::text")),
        sa.Column("assessment_id", sa.Text, nullable=False),       # soft ref
        sa.Column("supplier_id", sa.Text, nullable=False),
        sa.Column("supplier_name", sa.Text, nullable=True),
        sa.Column("country_code", sa.Text, nullable=True),
        sa.Column("sector", sa.Text, nullable=True),
        sa.Column("tier", sa.Integer, nullable=True),              # 1/2/3+
        sa.Column("ilo_risk_score", sa.Float, nullable=True),      # 0-100
        sa.Column("eu_flr_risk_level", sa.Text, nullable=True),
        sa.Column("audit_status", sa.Text, nullable=True),         # audited/unaudited/scheduled
        sa.Column("sa8000_certified", sa.Boolean, nullable=True),
        sa.Column("ilo_indicators_triggered", JSONB, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_forced_labour_supplier_nodes_assessment_id", "forced_labour_supplier_nodes", ["assessment_id"])

    # ------------------------------------------------------------------
    # E39 — Transition Finance: transition_finance_classifications
    # ------------------------------------------------------------------
    op.create_table(
        "transition_finance_classifications",
        sa.Column("id", sa.Text, primary_key=True, server_default=sa.text("gen_random_uuid()::text")),
        sa.Column("classification_id", sa.Text, nullable=False, unique=True),
        sa.Column("entity_id", sa.Text, nullable=False),
        sa.Column("entity_name", sa.Text, nullable=False),
        sa.Column("sector", sa.Text, nullable=True),
        sa.Column("reporting_period", sa.Text, nullable=True),
        # GFANZ classification
        sa.Column("gfanz_category", sa.Text, nullable=True),       # climate_solutions/aligned/aligning/managed_phaseout/unclassified
        sa.Column("tpt_sector_pathway_alignment_pct", sa.Float, nullable=True),
        sa.Column("singapore_gtt_tier", sa.Text, nullable=True),   # Green/Transition/Excluded
        sa.Column("japan_gx_eligible", sa.Boolean, nullable=True),
        # Transition plan credibility (ICMA 4-pillar)
        sa.Column("transition_plan_credibility_score", sa.Float, nullable=True),
        sa.Column("credibility_rating", sa.Text, nullable=True),   # insufficient/developing/credible/leading
        sa.Column("strategy_score", sa.Float, nullable=True),
        sa.Column("implementation_score", sa.Float, nullable=True),
        sa.Column("governance_score", sa.Float, nullable=True),
        sa.Column("disclosure_score", sa.Float, nullable=True),
        # Emissions / pathway alignment
        sa.Column("emissions_intensity_current", sa.Float, nullable=True),
        sa.Column("emissions_intensity_2030_target", sa.Float, nullable=True),
        sa.Column("ngfs_pathway_benchmark_2030", sa.Float, nullable=True),
        sa.Column("alignment_gap_pct", sa.Float, nullable=True),
        sa.Column("capex_low_carbon_pct", sa.Float, nullable=True),
        # Portfolio metrics
        sa.Column("transition_finance_ratio_pct", sa.Float, nullable=True),
        sa.Column("gar_pct", sa.Float, nullable=True),
        sa.Column("brown_overhang_mn", sa.Float, nullable=True),
        # Bond structuring
        sa.Column("bond_type_recommendation", sa.Text, nullable=True), # green/transition/slb/excluded
        sa.Column("kpi_ambition_score", sa.Float, nullable=True),
        sa.Column("cross_framework", JSONB, nullable=True),
        sa.Column("warnings", JSONB, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_transition_finance_classifications_entity_id", "transition_finance_classifications", ["entity_id"])

    op.create_table(
        "transition_loan_book_positions",
        sa.Column("id", sa.Text, primary_key=True, server_default=sa.text("gen_random_uuid()::text")),
        sa.Column("classification_id", sa.Text, nullable=False),  # soft ref
        sa.Column("exposure_id", sa.Text, nullable=False),
        sa.Column("borrower_name", sa.Text, nullable=True),
        sa.Column("sector", sa.Text, nullable=True),
        sa.Column("exposure_mn", sa.Float, nullable=True),
        sa.Column("gfanz_category", sa.Text, nullable=True),
        sa.Column("sector_pathway_gap_pct", sa.Float, nullable=True),
        sa.Column("credibility_score", sa.Float, nullable=True),
        sa.Column("financing_type", sa.Text, nullable=True),      # loan/bond/equity/guarantee
        sa.Column("maturity_year", sa.Integer, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_transition_loan_book_positions_classification_id", "transition_loan_book_positions", ["classification_id"])


def downgrade() -> None:
    op.drop_table("transition_loan_book_positions")
    op.drop_table("transition_finance_classifications")
    op.drop_table("forced_labour_supplier_nodes")
    op.drop_table("forced_labour_assessments")
    op.drop_table("impact_portfolio_holdings")
    op.drop_table("social_taxonomy_assessments")
    op.drop_table("basel3_liquidity_time_buckets")
    op.drop_table("basel3_liquidity_assessments")
