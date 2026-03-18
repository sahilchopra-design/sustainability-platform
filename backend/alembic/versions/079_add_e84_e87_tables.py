"""Add E84-E87 tables: Internal Carbon Pricing, Social Bond, Climate Financial Statements, EM Climate Risk

Revision ID: 079_add_e84_e87_tables
Revises: 078_add_e80_e83_tables
Create Date: 2026-03-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '079'
down_revision = '078'
branch_labels = None
depends_on = None


def upgrade():
    # ── E84: Internal Carbon Pricing & Net-Zero Economics ────────────────────
    # SBTi ICP Guidance · EU ETS shadow price · ICP mechanism design · carbon budget
    op.execute("""
        CREATE TABLE IF NOT EXISTS internal_carbon_price_assessments (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            assessment_date             DATE,
            -- ICP mechanism
            mechanism_type              TEXT,
            shadow_price_eur_tco2       NUMERIC(8,2),
            fee_eur_tco2                NUMERIC(8,2),
            price_trajectory            JSONB,
            price_scenario              TEXT,
            -- SBTi alignment
            sbti_icp_guidance_met       BOOLEAN DEFAULT FALSE,
            sbti_recommended_min_eur    NUMERIC(8,2),
            sbti_alignment_score        NUMERIC(5,2),
            -- Scope cost allocation
            scope1_cost_eur             NUMERIC(15,2),
            scope2_cost_eur             NUMERIC(15,2),
            scope3_cost_eur             NUMERIC(15,2),
            total_carbon_cost_eur       NUMERIC(15,2),
            carbon_cost_pct_ebitda      NUMERIC(5,2),
            -- Carbon budget
            remaining_budget_tco2       NUMERIC(15,2),
            budget_exhaustion_year      INTEGER,
            annual_reduction_required_pct NUMERIC(5,2),
            -- Net-zero economics
            nze_investment_eur          NUMERIC(15,2),
            nze_opex_savings_eur        NUMERIC(15,2),
            nze_npv_eur                 NUMERIC(15,2),
            nze_payback_years           NUMERIC(5,2),
            nze_irr_pct                 NUMERIC(5,2),
            abatement_cost_curve        JSONB,
            -- EU ETS shadow
            ets_shadow_price_eur        NUMERIC(8,2),
            ets_phase4_exposure_eur     NUMERIC(15,2),
            ets2_exposure_eur           NUMERIC(15,2),
            -- overall
            icp_maturity_score          NUMERIC(5,2),
            icp_maturity_tier           TEXT,
            -- metadata
            raw_input                   JSONB,
            full_result                 JSONB,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_icp_entity ON internal_carbon_price_assessments(entity_id);
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS carbon_budget_tracking (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            budget_year                 INTEGER NOT NULL,
            scenario                    TEXT,
            budget_tco2                 NUMERIC(15,2),
            actual_tco2                 NUMERIC(15,2),
            variance_tco2               NUMERIC(15,2),
            cumulative_budget_tco2      NUMERIC(15,2),
            cumulative_actual_tco2      NUMERIC(15,2),
            on_track                    BOOLEAN DEFAULT TRUE,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_budget_entity_year ON carbon_budget_tracking(entity_id, budget_year);
    """)

    # ── E85: Social Bond & Impact Finance ────────────────────────────────────
    # ICMA SBP 2023 · UN SDG · Social KPIs · Target Population · ICMA SBP Registry
    op.execute("""
        CREATE TABLE IF NOT EXISTS social_bond_assessments (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            bond_name                   TEXT,
            assessment_date             DATE,
            total_issuance_m            NUMERIC(15,2),
            currency                    TEXT DEFAULT 'EUR',
            -- ICMA SBP 4 core components
            use_of_proceeds_score       NUMERIC(5,2),
            process_evaluation_score    NUMERIC(5,2),
            management_proceeds_score   NUMERIC(5,2),
            reporting_score             NUMERIC(5,2),
            sbp_composite_score         NUMERIC(5,2),
            sbp_aligned                 BOOLEAN DEFAULT FALSE,
            sbp_gaps                    JSONB,
            -- Use of proceeds
            project_categories          JSONB,
            primary_category            TEXT,
            excluded_activities         JSONB,
            -- Target population
            target_populations          JSONB,
            beneficiaries_count         INTEGER,
            geographic_coverage         JSONB,
            -- Social KPIs
            kpis_defined                INTEGER,
            kpis_quantified             INTEGER,
            kpi_details                 JSONB,
            -- SDG mapping
            sdg_alignment               JSONB,
            primary_sdg                 INTEGER,
            sdg_count                   INTEGER,
            -- Impact reporting
            impact_report_committed     BOOLEAN DEFAULT FALSE,
            impact_report_score         NUMERIC(5,2),
            -- External review
            has_spo                     BOOLEAN DEFAULT FALSE,
            spo_provider                TEXT,
            -- overall
            impact_score                NUMERIC(5,2),
            bond_tier                   TEXT,
            -- metadata
            raw_input                   JSONB,
            full_result                 JSONB,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_social_bond_entity ON social_bond_assessments(entity_id);
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS social_impact_kpis (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            assessment_id               TEXT,
            kpi_name                    TEXT,
            kpi_category                TEXT,
            baseline_value              NUMERIC(15,4),
            target_value                NUMERIC(15,4),
            unit                        TEXT,
            measurement_method          TEXT,
            verification_source         TEXT,
            sdg_target                  TEXT,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_social_kpi_assessment ON social_impact_kpis(assessment_id);
    """)

    # ── E86: Climate Financial Statement Adjustments ──────────────────────────
    # IFRS S2 financial effects · IAS 36 climate impairment · TCFD financial tables
    op.execute("""
        CREATE TABLE IF NOT EXISTS climate_financial_statement_assessments (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            reporting_period            TEXT,
            assessment_date             DATE,
            -- IFRS S2 financial effects
            ifrs_s2_score               NUMERIC(5,2),
            financial_effects_disclosed BOOLEAN DEFAULT FALSE,
            transition_risk_revenue_impact_m  NUMERIC(15,2),
            transition_risk_cost_impact_m     NUMERIC(15,2),
            physical_risk_asset_impact_m      NUMERIC(15,2),
            climate_opportunity_revenue_m     NUMERIC(15,2),
            -- IAS 36 climate impairment
            ias36_assessment_required   BOOLEAN DEFAULT FALSE,
            ias36_climate_triggers      JSONB,
            potential_impairment_m      NUMERIC(15,2),
            impairment_tested_assets    JSONB,
            -- Carbon provision
            carbon_provision_required_m NUMERIC(15,2),
            carbon_provision_basis      TEXT,
            ets_allowance_deficit       NUMERIC(10,2),
            -- Stranded asset write-down
            stranded_asset_exposure_m   NUMERIC(15,2),
            write_down_trigger_year     INTEGER,
            write_down_amount_m         NUMERIC(15,2),
            -- Climate P&L
            climate_adjusted_revenue_m  NUMERIC(15,2),
            climate_adjusted_ebitda_m   NUMERIC(15,2),
            climate_adjusted_pat_m      NUMERIC(15,2),
            climate_ebitda_impact_pct   NUMERIC(5,2),
            -- TCFD financial scenario table
            scenario_1_5c_impact_m      NUMERIC(15,2),
            scenario_2c_impact_m        NUMERIC(15,2),
            scenario_3c_impact_m        NUMERIC(15,2),
            scenario_detail             JSONB,
            -- Disclosure completeness
            disclosure_completeness_pct NUMERIC(5,2),
            disclosure_gaps             JSONB,
            -- overall
            climate_financial_risk_score NUMERIC(5,2),
            materiality_tier            TEXT,
            -- metadata
            raw_input                   JSONB,
            full_result                 JSONB,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_climate_fs_entity ON climate_financial_statement_assessments(entity_id);
    """)

    # ── E87: Emerging Market Climate & Transition Risk ────────────────────────
    # IFC PS6 · MSCI EM climate indices · EM green bond market · GEMS loss · NDC gaps
    op.execute("""
        CREATE TABLE IF NOT EXISTS em_climate_risk_assessments (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            country_code                TEXT NOT NULL,
            assessment_date             DATE,
            -- Country climate risk
            physical_risk_score         NUMERIC(5,2),
            transition_readiness_score  NUMERIC(5,2),
            ndc_ambition_score          NUMERIC(5,2),
            climate_vulnerability_index NUMERIC(5,2),
            nd_gain_score               NUMERIC(5,2),
            -- IFC PS6 biodiversity
            ifc_ps6_applicable          BOOLEAN DEFAULT FALSE,
            ifc_ps6_score               NUMERIC(5,2),
            critical_habitat_exposure   BOOLEAN DEFAULT FALSE,
            biodiversity_offset_required BOOLEAN DEFAULT FALSE,
            -- Green finance market
            green_bond_market_size_bn   NUMERIC(10,2),
            green_bond_pipeline_bn      NUMERIC(10,2),
            sustainable_finance_depth   NUMERIC(5,2),
            local_currency_risk         NUMERIC(5,2),
            -- Transition risk factors
            fossil_fuel_dependency_pct  NUMERIC(5,2),
            renewable_capacity_gw       NUMERIC(8,2),
            carbon_intensity_gdp        NUMERIC(8,4),
            just_transition_risk        NUMERIC(5,2),
            policy_regulatory_risk      NUMERIC(5,2),
            -- Concessional finance opportunity
            gcf_allocation_bn           NUMERIC(8,2),
            dfi_pipeline_bn             NUMERIC(8,2),
            blended_finance_potential   NUMERIC(5,2),
            -- GEMS loss data
            gems_historical_loss_bn     NUMERIC(10,2),
            gems_climate_uplift_pct     NUMERIC(5,2),
            -- overall
            em_climate_composite        NUMERIC(5,2),
            risk_tier                   TEXT,
            opportunity_tier            TEXT,
            -- metadata
            raw_input                   JSONB,
            full_result                 JSONB,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_em_climate_entity ON em_climate_risk_assessments(entity_id);
        CREATE INDEX IF NOT EXISTS idx_em_climate_country ON em_climate_risk_assessments(country_code);
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS em_portfolio_assessments (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            assessment_date             DATE,
            total_countries             INTEGER,
            total_exposure_m            NUMERIC(15,2),
            avg_physical_risk           NUMERIC(5,2),
            avg_transition_risk         NUMERIC(5,2),
            avg_ndc_ambition            NUMERIC(5,2),
            high_risk_exposure_pct      NUMERIC(5,2),
            climate_var_em_m            NUMERIC(15,2),
            green_finance_opportunity_m NUMERIC(15,2),
            country_breakdown           JSONB,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_em_portfolio_entity ON em_portfolio_assessments(entity_id);
    """)


def downgrade():
    for table in [
        "em_portfolio_assessments",
        "em_climate_risk_assessments",
        "climate_financial_statement_assessments",
        "social_impact_kpis",
        "social_bond_assessments",
        "carbon_budget_tracking",
        "internal_carbon_price_assessments",
    ]:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
