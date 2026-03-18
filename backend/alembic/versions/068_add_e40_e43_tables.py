"""Add E40-E43 tables: CSRD Double Materiality, Physical Climate Hazard, Scope 4 Avoided Emissions, Green Hydrogen

Revision ID: 068
Revises: 067
Create Date: 2026-03-17

Tables created:
  csrd_dma_assessments        — CSRD ESRS 1 DMA process: impact + financial materiality (E40)
  csrd_dma_topics             — Per-topic materiality scores, stakeholder weights, priority (E40)
  physical_hazard_assessments — Asset-level physical climate hazard composite (E41)
  physical_hazard_scores      — Per-hazard scores (flood/wildfire/heat/sea-level/cyclone) (E41)
  avoided_emissions_assessments — Scope 4 avoided/enabled emissions baseline (E42)
  avoided_emissions_activities  — Per-activity avoided emission quantities & methods (E42)
  green_hydrogen_assessments  — H2 production pathway classification & economics (E43)
  hydrogen_project_scenarios  — Per-scenario LCOH, capex, carbon intensity (E43)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "068"
down_revision = "067"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # E40 — CSRD Double Materiality: csrd_dma_assessments
    # ------------------------------------------------------------------
    op.create_table(
        "csrd_dma_assessments",
        sa.Column("id", sa.Text, primary_key=True, server_default=sa.text("gen_random_uuid()::text")),
        sa.Column("assessment_id", sa.Text, nullable=False, unique=True),
        sa.Column("entity_id", sa.Text, nullable=False),
        sa.Column("entity_name", sa.Text, nullable=False),
        sa.Column("reporting_period", sa.Text, nullable=True),
        sa.Column("sector", sa.Text, nullable=True),
        sa.Column("nace_code", sa.Text, nullable=True),
        # DMA Process scores (ESRS 1 §§42-49)
        sa.Column("context_understanding_score", sa.Float, nullable=True),
        sa.Column("stakeholder_identification_score", sa.Float, nullable=True),
        sa.Column("impact_identification_score", sa.Float, nullable=True),
        sa.Column("financial_materiality_score", sa.Float, nullable=True),
        sa.Column("dma_process_completeness_pct", sa.Float, nullable=True),
        # Materiality outcomes
        sa.Column("material_topics_count", sa.Integer, nullable=True),
        sa.Column("impact_material_count", sa.Integer, nullable=True),
        sa.Column("financial_material_count", sa.Integer, nullable=True),
        sa.Column("both_material_count", sa.Integer, nullable=True),
        # Stakeholder engagement
        sa.Column("stakeholders_engaged", sa.Integer, nullable=True),
        sa.Column("stakeholder_types", JSONB, nullable=True),       # employees/investors/customers/NGOs/regulators
        sa.Column("engagement_quality_score", sa.Float, nullable=True),
        # Outputs
        sa.Column("material_topics", JSONB, nullable=True),          # list of material topic names
        sa.Column("non_material_topics", JSONB, nullable=True),
        sa.Column("esrs_standards_applicable", JSONB, nullable=True),# e.g. [E1, E2, S1, G1]
        sa.Column("assurance_readiness_pct", sa.Float, nullable=True),
        sa.Column("cross_framework", JSONB, nullable=True),
        sa.Column("priority_actions", JSONB, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_csrd_dma_assessments_entity_id", "csrd_dma_assessments", ["entity_id"])

    op.create_table(
        "csrd_dma_topics",
        sa.Column("id", sa.Text, primary_key=True, server_default=sa.text("gen_random_uuid()::text")),
        sa.Column("assessment_id", sa.Text, nullable=False),        # soft ref
        sa.Column("topic_id", sa.Text, nullable=False),             # e.g. climate_change, water, workforce
        sa.Column("topic_name", sa.Text, nullable=True),
        sa.Column("esrs_standard", sa.Text, nullable=True),         # E1/E2/E3/E4/E5/S1/S2/S3/S4/G1
        # Impact materiality (ESRS 1 §§43-46)
        sa.Column("impact_severity_score", sa.Float, nullable=True),# scale/scope/irremediability
        sa.Column("impact_likelihood_score", sa.Float, nullable=True),
        sa.Column("impact_materiality_score", sa.Float, nullable=True),# combined
        sa.Column("impact_type", sa.Text, nullable=True),           # actual_positive/actual_negative/potential
        sa.Column("value_chain_location", sa.Text, nullable=True),  # own_operations/upstream/downstream
        # Financial materiality (ESRS 1 §§47-48)
        sa.Column("financial_magnitude_score", sa.Float, nullable=True),
        sa.Column("financial_likelihood_score", sa.Float, nullable=True),
        sa.Column("financial_materiality_score", sa.Float, nullable=True),
        sa.Column("financial_risk_type", sa.Text, nullable=True),   # physical/transition/systemic
        # Combined
        sa.Column("is_material", sa.Boolean, nullable=True),
        sa.Column("materiality_basis", sa.Text, nullable=True),     # impact_only/financial_only/both/neither
        sa.Column("stakeholder_salience_score", sa.Float, nullable=True),
        sa.Column("priority_rank", sa.Integer, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_csrd_dma_topics_assessment_id", "csrd_dma_topics", ["assessment_id"])

    # ------------------------------------------------------------------
    # E41 — Physical Climate Hazard: physical_hazard_assessments
    # ------------------------------------------------------------------
    op.create_table(
        "physical_hazard_assessments",
        sa.Column("id", sa.Text, primary_key=True, server_default=sa.text("gen_random_uuid()::text")),
        sa.Column("assessment_id", sa.Text, nullable=False, unique=True),
        sa.Column("entity_id", sa.Text, nullable=False),
        sa.Column("asset_name", sa.Text, nullable=False),
        sa.Column("asset_type", sa.Text, nullable=True),            # building/infrastructure/land/portfolio
        sa.Column("lat", sa.Float, nullable=True),
        sa.Column("lng", sa.Float, nullable=True),
        sa.Column("country_code", sa.Text, nullable=True),
        sa.Column("climate_scenario", sa.Text, nullable=True),      # RCP2.6/RCP4.5/RCP8.5/SSP1/SSP2/SSP5
        sa.Column("time_horizon", sa.Text, nullable=True),          # 2030/2050/2080
        # Composite risk
        sa.Column("composite_hazard_score", sa.Float, nullable=True),# 0-100
        sa.Column("risk_tier", sa.Text, nullable=True),             # low/medium/high/very_high/critical
        sa.Column("primary_hazard", sa.Text, nullable=True),        # dominant hazard type
        # Individual hazard scores
        sa.Column("flood_risk_score", sa.Float, nullable=True),
        sa.Column("wildfire_risk_score", sa.Float, nullable=True),
        sa.Column("heat_stress_score", sa.Float, nullable=True),
        sa.Column("sea_level_rise_score", sa.Float, nullable=True),
        sa.Column("cyclone_risk_score", sa.Float, nullable=True),
        sa.Column("drought_risk_score", sa.Float, nullable=True),
        sa.Column("subsidence_risk_score", sa.Float, nullable=True),
        # Financial impact
        sa.Column("property_damage_pct", sa.Float, nullable=True),  # expected annual damage %
        sa.Column("business_interruption_days", sa.Integer, nullable=True),
        sa.Column("stranded_value_risk_pct", sa.Float, nullable=True),
        sa.Column("adaptation_capex_mn", sa.Float, nullable=True),
        # CRREM alignment
        sa.Column("crrem_pathway_compliant", sa.Boolean, nullable=True),
        sa.Column("stranding_year", sa.Integer, nullable=True),
        sa.Column("cross_framework", JSONB, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_physical_hazard_assessments_entity_id", "physical_hazard_assessments", ["entity_id"])

    op.create_table(
        "physical_hazard_scores",
        sa.Column("id", sa.Text, primary_key=True, server_default=sa.text("gen_random_uuid()::text")),
        sa.Column("assessment_id", sa.Text, nullable=False),        # soft ref
        sa.Column("hazard_type", sa.Text, nullable=False),          # flood/wildfire/heat/sea_level/cyclone/drought/subsidence
        sa.Column("hazard_score", sa.Float, nullable=True),         # 0-100
        sa.Column("return_period_20yr", sa.Float, nullable=True),   # 1-in-20 year event intensity
        sa.Column("return_period_100yr", sa.Float, nullable=True),  # 1-in-100 year event intensity
        sa.Column("exposure_level", sa.Text, nullable=True),        # negligible/low/medium/high/very_high
        sa.Column("vulnerability_score", sa.Float, nullable=True),  # asset vulnerability to hazard
        sa.Column("adaptation_measure", sa.Text, nullable=True),    # recommended adaptation
        sa.Column("data_source", sa.Text, nullable=True),           # IPCC_AR6/JRC/WRI_Aqueduct/etc
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_physical_hazard_scores_assessment_id", "physical_hazard_scores", ["assessment_id"])

    # ------------------------------------------------------------------
    # E42 — Scope 4 Avoided Emissions: avoided_emissions_assessments
    # ------------------------------------------------------------------
    op.create_table(
        "avoided_emissions_assessments",
        sa.Column("id", sa.Text, primary_key=True, server_default=sa.text("gen_random_uuid()::text")),
        sa.Column("assessment_id", sa.Text, nullable=False, unique=True),
        sa.Column("entity_id", sa.Text, nullable=False),
        sa.Column("entity_name", sa.Text, nullable=False),
        sa.Column("reporting_year", sa.Integer, nullable=True),
        sa.Column("assessment_type", sa.Text, nullable=True),       # product/service/portfolio/company
        sa.Column("methodology", sa.Text, nullable=True),           # ghg_protocol_2022/iso14064/sector_specific
        # Emission categories
        sa.Column("enabled_emissions_tco2e", sa.Float, nullable=True),   # enablement (products enabling low-carbon)
        sa.Column("substitution_emissions_tco2e", sa.Float, nullable=True),# substitution for higher-carbon alternatives
        sa.Column("facilitated_avoided_tco2e", sa.Float, nullable=True), # financed avoided emissions
        sa.Column("total_avoided_tco2e", sa.Float, nullable=True),
        sa.Column("baseline_scenario_emissions_tco2e", sa.Float, nullable=True),
        sa.Column("net_benefit_tco2e", sa.Float, nullable=True),    # avoided - own scope 1+2+3
        # Quality
        sa.Column("additionality_score", sa.Float, nullable=True),
        sa.Column("attribution_factor", sa.Float, nullable=True),   # 0-1 share attributable to entity
        sa.Column("data_quality_score", sa.Float, nullable=True),   # DQS 1-5
        sa.Column("third_party_verified", sa.Boolean, nullable=True),
        # Article 6 linkage
        sa.Column("article6_eligible", sa.Boolean, nullable=True),
        sa.Column("itmo_units_mn", sa.Float, nullable=True),
        sa.Column("credit_price_usd", sa.Float, nullable=True),
        # Cross-framework
        sa.Column("sbti_bvcm_eligible", sa.Boolean, nullable=True),
        sa.Column("science_based_claim", sa.Boolean, nullable=True),
        sa.Column("cross_framework", JSONB, nullable=True),
        sa.Column("warnings", JSONB, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_avoided_emissions_assessments_entity_id", "avoided_emissions_assessments", ["entity_id"])

    op.create_table(
        "avoided_emissions_activities",
        sa.Column("id", sa.Text, primary_key=True, server_default=sa.text("gen_random_uuid()::text")),
        sa.Column("assessment_id", sa.Text, nullable=False),        # soft ref
        sa.Column("activity_id", sa.Text, nullable=False),
        sa.Column("activity_name", sa.Text, nullable=True),
        sa.Column("activity_type", sa.Text, nullable=True),         # enabled/substitution/facilitated
        sa.Column("product_service", sa.Text, nullable=True),
        sa.Column("functional_unit", sa.Text, nullable=True),
        sa.Column("quantity", sa.Float, nullable=True),
        sa.Column("baseline_intensity_kgco2e", sa.Float, nullable=True),
        sa.Column("solution_intensity_kgco2e", sa.Float, nullable=True),
        sa.Column("avoided_per_unit_kgco2e", sa.Float, nullable=True),
        sa.Column("total_avoided_tco2e", sa.Float, nullable=True),
        sa.Column("attribution_factor", sa.Float, nullable=True),
        sa.Column("additionality_basis", sa.Text, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_avoided_emissions_activities_assessment_id", "avoided_emissions_activities", ["assessment_id"])

    # ------------------------------------------------------------------
    # E43 — Green Hydrogen: green_hydrogen_assessments
    # ------------------------------------------------------------------
    op.create_table(
        "green_hydrogen_assessments",
        sa.Column("id", sa.Text, primary_key=True, server_default=sa.text("gen_random_uuid()::text")),
        sa.Column("assessment_id", sa.Text, nullable=False, unique=True),
        sa.Column("entity_id", sa.Text, nullable=False),
        sa.Column("project_name", sa.Text, nullable=False),
        sa.Column("country_code", sa.Text, nullable=True),
        sa.Column("production_pathway", sa.Text, nullable=True),    # green/blue/turquoise/pink/grey/brown
        sa.Column("electrolysis_technology", sa.Text, nullable=True),# PEM/ALK/SOEC/AEM
        sa.Column("capacity_mw", sa.Float, nullable=True),
        sa.Column("annual_production_ktpa", sa.Float, nullable=True),
        # EU Classification (Delegated Act 2023/1184)
        sa.Column("eu_delegated_act_compliant", sa.Boolean, nullable=True),
        sa.Column("renewable_electricity_pct", sa.Float, nullable=True),
        sa.Column("additionality_met", sa.Boolean, nullable=True),  # Art 3 additionality
        sa.Column("temporal_correlation_met", sa.Boolean, nullable=True),
        sa.Column("geographical_correlation_met", sa.Boolean, nullable=True),
        sa.Column("carbon_intensity_kgco2e_kgh2", sa.Float, nullable=True),# must be <3.38
        sa.Column("eu_taxonomy_aligned", sa.Boolean, nullable=True),
        # Economics
        sa.Column("lcoh_usd_per_kgh2", sa.Float, nullable=True),    # levelised cost of hydrogen
        sa.Column("capex_per_kw", sa.Float, nullable=True),         # electrolyser CAPEX
        sa.Column("opex_annual_mn", sa.Float, nullable=True),
        sa.Column("electricity_cost_mwh", sa.Float, nullable=True),
        sa.Column("capacity_factor_pct", sa.Float, nullable=True),
        sa.Column("discount_rate_pct", sa.Float, nullable=True),
        # Policy incentives
        sa.Column("h2_subsidy_scheme", sa.Text, nullable=True),     # eu_h2_bank/ira_45v/uk_ren_hydrogen/japan_gx
        sa.Column("subsidy_value_usd_per_kgh2", sa.Float, nullable=True),
        sa.Column("net_lcoh_after_subsidy", sa.Float, nullable=True),
        # Cross-framework
        sa.Column("gfanz_category", sa.Text, nullable=True),        # climate_solutions/aligned
        sa.Column("sustainable_finance_label", sa.Text, nullable=True),
        sa.Column("cross_framework", JSONB, nullable=True),
        sa.Column("warnings", JSONB, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_green_hydrogen_assessments_entity_id", "green_hydrogen_assessments", ["entity_id"])

    op.create_table(
        "hydrogen_project_scenarios",
        sa.Column("id", sa.Text, primary_key=True, server_default=sa.text("gen_random_uuid()::text")),
        sa.Column("assessment_id", sa.Text, nullable=False),        # soft ref
        sa.Column("scenario_name", sa.Text, nullable=False),        # base/optimistic/pessimistic/policy_support
        sa.Column("year", sa.Integer, nullable=True),
        sa.Column("electrolyser_cost_per_kw", sa.Float, nullable=True),
        sa.Column("electricity_price_mwh", sa.Float, nullable=True),
        sa.Column("capacity_factor_pct", sa.Float, nullable=True),
        sa.Column("carbon_intensity_kgco2e_kgh2", sa.Float, nullable=True),
        sa.Column("lcoh_usd_per_kgh2", sa.Float, nullable=True),
        sa.Column("parity_achieved", sa.Boolean, nullable=True),    # vs grey H2 at ~$1-2/kgH2
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_hydrogen_project_scenarios_assessment_id", "hydrogen_project_scenarios", ["assessment_id"])


def downgrade() -> None:
    op.drop_table("hydrogen_project_scenarios")
    op.drop_table("green_hydrogen_assessments")
    op.drop_table("avoided_emissions_activities")
    op.drop_table("avoided_emissions_assessments")
    op.drop_table("physical_hazard_scores")
    op.drop_table("physical_hazard_assessments")
    op.drop_table("csrd_dma_topics")
    op.drop_table("csrd_dma_assessments")
