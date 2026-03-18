"""Add E76-E79 tables: Crypto Climate, AI Governance, Carbon Accounting AI, Climate Insurance

Revision ID: 077_add_e76_e79_tables
Revises: 071_add_e52_e55_tables
Create Date: 2026-03-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '077'
down_revision = '071'
branch_labels = None
depends_on = None


def upgrade():
    # ── E76: Digital Assets & Crypto Climate Risk ─────────────────────────────
    # Cambridge CBECI · MiCA 2023/1114 · PoW/PoS GHG intensity · PCAF Crypto
    op.execute("""
        CREATE TABLE IF NOT EXISTS crypto_climate_assessments (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            assessment_date             DATE,
            -- asset details
            asset_name                  TEXT,
            ticker                      TEXT,
            consensus_mechanism         TEXT,
            -- energy metrics
            annual_energy_twh           NUMERIC(12,4),
            lower_bound_twh             NUMERIC(12,4),
            upper_bound_twh             NUMERIC(12,4),
            ghg_intensity_gco2_per_tx   NUMERIC(12,4),
            mining_renewable_pct        NUMERIC(5,2),
            mining_carbon_intensity     NUMERIC(8,2),
            -- total footprint
            total_tco2e_per_year        NUMERIC(15,2),
            -- MiCA compliance
            mica_compliance_level       TEXT,
            mica_score                  NUMERIC(5,2),
            mica_gaps                   JSONB,
            -- tokenised green assets
            is_tokenised_green_asset    BOOLEAN DEFAULT FALSE,
            rwa_framework               TEXT,
            tokenisation_premium_bps    NUMERIC(6,2),
            -- PCAF financed emissions
            financed_emissions_tco2e    NUMERIC(15,2),
            pcaf_dqs                    INTEGER,
            -- scores
            overall_score               NUMERIC(5,2),
            climate_risk_tier           TEXT,
            -- metadata
            raw_input                   JSONB,
            full_result                 JSONB,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_crypto_climate_entity ON crypto_climate_assessments(entity_id);
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS crypto_portfolio_assessments (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            assessment_date             DATE,
            -- portfolio totals
            total_holdings              INTEGER,
            total_exposure_usd          NUMERIC(20,2),
            total_tco2e_per_year        NUMERIC(15,2),
            weighted_avg_ghg_intensity  NUMERIC(12,4),
            portfolio_renewable_pct     NUMERIC(5,2),
            -- by consensus mechanism
            pow_exposure_pct            NUMERIC(5,2),
            pos_exposure_pct            NUMERIC(5,2),
            -- MiCA
            mica_compliant_pct          NUMERIC(5,2),
            -- financed emissions
            total_financed_emissions    NUMERIC(15,2),
            weighted_avg_dqs            NUMERIC(4,2),
            -- scores
            portfolio_climate_score     NUMERIC(5,2),
            climate_risk_tier           TEXT,
            holdings_detail             JSONB,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_crypto_portfolio_entity ON crypto_portfolio_assessments(entity_id);
    """)

    # ── E77: AI Governance & ESG ───────────────────────────────────────────────
    # EU AI Act 2024/1689 · NIST AI RMF 1.0 · OECD AI Principles · AI Energy
    op.execute("""
        CREATE TABLE IF NOT EXISTS ai_governance_assessments (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            system_name                 TEXT,
            assessment_date             DATE,
            -- EU AI Act
            eu_ai_act_risk_tier         TEXT,
            eu_ai_act_score             NUMERIC(5,2),
            eu_ai_act_obligations       JSONB,
            eu_ai_act_gaps              JSONB,
            -- NIST AI RMF
            nist_rmf_score              NUMERIC(5,2),
            nist_govern_score           NUMERIC(5,2),
            nist_map_score              NUMERIC(5,2),
            nist_measure_score          NUMERIC(5,2),
            nist_manage_score           NUMERIC(5,2),
            -- OECD AI Principles
            oecd_score                  NUMERIC(5,2),
            oecd_gaps                   JSONB,
            -- AI Energy
            training_energy_mwh         NUMERIC(12,2),
            annual_inference_mwh        NUMERIC(12,2),
            annual_tco2e                NUMERIC(10,2),
            -- Algorithmic Bias
            bias_severity               TEXT,
            bias_metrics                JSONB,
            protected_characteristics   JSONB,
            -- Model Card
            model_card_completeness_pct NUMERIC(5,2),
            model_card_gaps             JSONB,
            -- Composite
            governance_score            NUMERIC(5,2),
            environmental_score         NUMERIC(5,2),
            social_score                NUMERIC(5,2),
            composite_score             NUMERIC(5,2),
            maturity_tier               TEXT,
            -- metadata
            raw_input                   JSONB,
            full_result                 JSONB,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_ai_governance_entity ON ai_governance_assessments(entity_id);
        CREATE INDEX IF NOT EXISTS idx_ai_governance_tier ON ai_governance_assessments(eu_ai_act_risk_tier);
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS ai_portfolio_assessments (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            assessment_date             DATE,
            -- portfolio summary
            total_systems               INTEGER,
            high_risk_systems           INTEGER,
            unacceptable_risk_systems   INTEGER,
            -- energy
            total_training_mwh          NUMERIC(15,2),
            total_inference_mwh_pa      NUMERIC(15,2),
            total_tco2e_pa              NUMERIC(12,2),
            -- governance
            avg_composite_score         NUMERIC(5,2),
            avg_eu_ai_act_score         NUMERIC(5,2),
            avg_nist_rmf_score          NUMERIC(5,2),
            avg_bias_severity_score     NUMERIC(5,2),
            -- portfolio tier
            portfolio_maturity_tier     TEXT,
            systems_detail              JSONB,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_ai_portfolio_entity ON ai_portfolio_assessments(entity_id);
    """)

    # ── E78: Carbon Accounting AI & Automation ────────────────────────────────
    # GHG Protocol AI compliance · EF matching · Scope 3 auto-classify · XBRL tagging
    op.execute("""
        CREATE TABLE IF NOT EXISTS carbon_accounting_ai_assessments (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            assessment_date             DATE,
            -- GHG Protocol compliance
            ghg_compliance_score        NUMERIC(5,2),
            ghg_compliance_status       TEXT,
            ghg_gaps                    JSONB,
            -- Emission Factor matching
            ef_match_count              INTEGER,
            ef_avg_confidence           NUMERIC(5,2),
            ef_avg_dqs                  NUMERIC(4,2),
            ef_matches                  JSONB,
            -- Scope 3 classification
            scope3_classified_count     INTEGER,
            scope3_avg_confidence       NUMERIC(5,2),
            scope3_categories_used      JSONB,
            flag_split                  JSONB,
            -- DQS derivation
            auto_dqs_score              NUMERIC(4,2),
            dqs_improvement_potential   NUMERIC(4,2),
            -- XBRL tagging
            xbrl_tagged_count           INTEGER,
            xbrl_completeness_pct       NUMERIC(5,2),
            xbrl_mandatory_gaps         JSONB,
            -- CDP scoring
            cdp_climate_score           TEXT,
            cdp_water_score             TEXT,
            cdp_composite               NUMERIC(5,2),
            -- Data gaps
            gap_count                   INTEGER,
            materiality_weighted_gap    NUMERIC(5,2),
            gap_recommendations         JSONB,
            -- overall
            automation_readiness_score  NUMERIC(5,2),
            -- metadata
            raw_input                   JSONB,
            full_result                 JSONB,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_carbon_ai_entity ON carbon_accounting_ai_assessments(entity_id);
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS ef_match_records (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            assessment_id               TEXT,
            activity_description        TEXT,
            matched_ef_source           TEXT,
            matched_ef_value            NUMERIC(12,6),
            matched_ef_unit             TEXT,
            scope3_category             TEXT,
            confidence_score            NUMERIC(5,4),
            dqs_level                   INTEGER,
            ghg_protocol_category       TEXT,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_ef_match_assessment ON ef_match_records(assessment_id);
    """)

    # ── E79: Climate Insurance & Parametric Risk ──────────────────────────────
    # IAIS AP 2021 · Parametric design · NatCat modelling · Climate VaR · ORSA
    op.execute("""
        CREATE TABLE IF NOT EXISTS climate_insurance_assessments (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            insurer_name                TEXT,
            insurer_type                TEXT,
            assessment_date             DATE,
            -- IAIS compliance
            iais_score                  NUMERIC(5,2),
            iais_status                 TEXT,
            iais_governance_score       NUMERIC(5,2),
            iais_strategy_score         NUMERIC(5,2),
            iais_risk_mgmt_score        NUMERIC(5,2),
            iais_disclosure_score       NUMERIC(5,2),
            iais_gaps                   JSONB,
            -- Climate VaR
            climate_var_physical        NUMERIC(15,2),
            climate_var_transition      NUMERIC(15,2),
            climate_var_liability       NUMERIC(15,2),
            climate_var_total           NUMERIC(15,2),
            climate_var_pct_capital     NUMERIC(6,2),
            -- ORSA stress
            pre_stress_solvency_ratio   NUMERIC(6,2),
            post_stress_solvency_ratio  NUMERIC(6,2),
            scr_uplift_pct              NUMERIC(6,2),
            worst_case_scenario         TEXT,
            orsa_checklist_score        NUMERIC(5,2),
            -- NatCat exposure
            total_exposure_bn           NUMERIC(15,2),
            aal_pct                     NUMERIC(6,4),
            pml_1_in_100_pct            NUMERIC(6,4),
            pml_1_in_250_pct            NUMERIC(6,4),
            -- Protection gap
            protection_gap_pct          NUMERIC(5,2),
            insured_loss_ratio          NUMERIC(5,2),
            -- casualty liability
            do_exposure_m               NUMERIC(12,2),
            eo_exposure_m               NUMERIC(12,2),
            pollution_exposure_m        NUMERIC(12,2),
            -- overall
            overall_climate_risk_score  NUMERIC(5,2),
            climate_risk_tier           TEXT,
            -- metadata
            raw_input                   JSONB,
            full_result                 JSONB,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_climate_insurance_entity ON climate_insurance_assessments(entity_id);
        CREATE INDEX IF NOT EXISTS idx_climate_insurance_type ON climate_insurance_assessments(insurer_type);
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS parametric_insurance_designs (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            product_name                TEXT,
            index_type                  TEXT,
            trigger_threshold           NUMERIC(12,4),
            exit_threshold              NUMERIC(12,4),
            max_payout_usd              NUMERIC(15,2),
            min_payout_usd              NUMERIC(15,2),
            annual_premium_usd          NUMERIC(15,2),
            premium_loading_pct         NUMERIC(5,2),
            basis_risk_score            NUMERIC(5,4),
            expected_annual_payout      NUMERIC(15,2),
            loss_ratio_expected         NUMERIC(5,2),
            payout_structure            JSONB,
            historical_trigger_freq     NUMERIC(5,2),
            climate_adj_trigger_freq    NUMERIC(5,2),
            country_code                TEXT,
            peril                       TEXT,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_parametric_entity ON parametric_insurance_designs(entity_id);
    """)


def downgrade():
    for table in [
        "parametric_insurance_designs",
        "climate_insurance_assessments",
        "ef_match_records",
        "carbon_accounting_ai_assessments",
        "ai_portfolio_assessments",
        "ai_governance_assessments",
        "crypto_portfolio_assessments",
        "crypto_climate_assessments",
    ]:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
