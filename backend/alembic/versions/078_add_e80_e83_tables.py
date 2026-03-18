"""Add E80-E83 tables: Corporate Nature Strategy, Green Securitisation, Digital Product Passport, Adaptation Finance

Revision ID: 078_add_e80_e83_tables
Revises: 077_add_e76_e79_tables
Create Date: 2026-03-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '078'
down_revision = '077'
branch_labels = None
depends_on = None


def upgrade():
    # ── E80: Corporate Nature Strategy & SBTN ────────────────────────────────
    # SBTN v1.0 · TNFD v1.0 · EU NRL 2024/1991 · GBF Target 3 · ENCORE
    op.execute("""
        CREATE TABLE IF NOT EXISTS sbtn_assessments (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            assessment_date             DATE,
            -- SBTN 5-Step process
            step1_assess_score          NUMERIC(5,2),
            step1_high_impact_sectors   JSONB,
            step1_dependency_exposure   JSONB,
            step2_interpret_score       NUMERIC(5,2),
            step2_material_locations    JSONB,
            step2_priority_areas        JSONB,
            step3_measure_score         NUMERIC(5,2),
            step3_msa_km2_footprint     NUMERIC(15,4),
            step3_ecosystem_services    JSONB,
            step4_targets_set           INTEGER,
            step4_science_based_pct     NUMERIC(5,2),
            step4_target_detail         JSONB,
            step5_disclosure_score      NUMERIC(5,2),
            step5_tnfd_aligned          BOOLEAN DEFAULT FALSE,
            -- TNFD v1.0 metrics
            tnfd_governance_score       NUMERIC(5,2),
            tnfd_strategy_score         NUMERIC(5,2),
            tnfd_risk_mgmt_score        NUMERIC(5,2),
            tnfd_metrics_score          NUMERIC(5,2),
            tnfd_composite              NUMERIC(5,2),
            tnfd_gaps                   JSONB,
            -- EU Nature Restoration Law
            nrl_exposure_score          NUMERIC(5,2),
            nrl_habitat_types           JSONB,
            nrl_restoration_liability_m NUMERIC(12,2),
            -- GBF Target 3 (30x30)
            gbf_t3_protected_area_pct   NUMERIC(5,2),
            gbf_t3_exposure             JSONB,
            -- ENCORE ecosystem services
            encore_dependencies         JSONB,
            encore_impacts              JSONB,
            encore_financial_exposure_m NUMERIC(15,2),
            -- composite
            nature_strategy_score       NUMERIC(5,2),
            nature_maturity_tier        TEXT,
            -- metadata
            raw_input                   JSONB,
            full_result                 JSONB,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_sbtn_entity ON sbtn_assessments(entity_id);
        CREATE INDEX IF NOT EXISTS idx_sbtn_tier ON sbtn_assessments(nature_maturity_tier);
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS nature_target_registry (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            target_type                 TEXT,
            target_scope                TEXT,
            baseline_year               INTEGER,
            target_year                 INTEGER,
            baseline_value              NUMERIC(15,4),
            target_value                NUMERIC(15,4),
            unit                        TEXT,
            science_based               BOOLEAN DEFAULT FALSE,
            sbtn_step                   INTEGER,
            verification_body           TEXT,
            status                      TEXT DEFAULT 'set',
            progress_pct                NUMERIC(5,2),
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_nature_target_entity ON nature_target_registry(entity_id);
    """)

    # ── E81: Green Securitisation & ESG Structured Finance ───────────────────
    # EU GBS Art 19 · EU ESRS SPV · ABS/RMBS Climate VaR · Covered Bond ESG
    op.execute("""
        CREATE TABLE IF NOT EXISTS green_securitisation_assessments (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            deal_name                   TEXT,
            assessment_date             DATE,
            -- structure
            structure_type              TEXT,
            total_issuance_m            NUMERIC(15,2),
            senior_tranche_m            NUMERIC(15,2),
            mezzanine_tranche_m         NUMERIC(15,2),
            junior_tranche_m            NUMERIC(15,2),
            -- EU GBS compliance
            eu_gbs_aligned              BOOLEAN DEFAULT FALSE,
            eu_gbs_score                NUMERIC(5,2),
            eu_gbs_gaps                 JSONB,
            taxonomy_alignment_pct      NUMERIC(5,2),
            dnsh_pass                   BOOLEAN,
            min_safeguards_pass         BOOLEAN,
            -- Climate VaR pass-through
            pool_climate_var_physical   NUMERIC(15,2),
            pool_climate_var_transition NUMERIC(15,2),
            pool_weighted_pd_climate    NUMERIC(5,4),
            pool_weighted_lgd_climate   NUMERIC(5,4),
            climate_credit_enhancement  NUMERIC(5,2),
            -- covered bond ESG
            is_covered_bond             BOOLEAN DEFAULT FALSE,
            ecbc_label_eligible         BOOLEAN DEFAULT FALSE,
            covered_bond_esv_score      NUMERIC(5,2),
            -- ABS/RMBS
            is_rmbs                     BOOLEAN DEFAULT FALSE,
            energy_efficiency_pct       NUMERIC(5,2),
            epc_distribution            JSONB,
            crrem_aligned_pct           NUMERIC(5,2),
            -- ESRS SPV disclosure
            esrs_spv_applicable         BOOLEAN DEFAULT FALSE,
            esrs_spv_disclosure_score   NUMERIC(5,2),
            -- overall
            green_securitisation_score  NUMERIC(5,2),
            deal_tier                   TEXT,
            greenium_bps                NUMERIC(6,2),
            -- metadata
            raw_input                   JSONB,
            full_result                 JSONB,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_green_sec_entity ON green_securitisation_assessments(entity_id);
        CREATE INDEX IF NOT EXISTS idx_green_sec_type ON green_securitisation_assessments(structure_type);
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS structured_pool_assets (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            deal_id                     TEXT,
            asset_type                  TEXT,
            asset_count                 INTEGER,
            total_balance_m             NUMERIC(15,2),
            avg_ltv                     NUMERIC(5,2),
            avg_dscr                    NUMERIC(5,2),
            taxonomy_eligible_pct       NUMERIC(5,2),
            taxonomy_aligned_pct        NUMERIC(5,2),
            epc_a_b_pct                 NUMERIC(5,2),
            physical_risk_exposure_pct  NUMERIC(5,2),
            transition_risk_exposure_pct NUMERIC(5,2),
            avg_pd_base                 NUMERIC(5,4),
            avg_pd_climate              NUMERIC(5,4),
            sector_breakdown            JSONB,
            geography_breakdown         JSONB,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_pool_deal ON structured_pool_assets(deal_id);
    """)

    # ── E82: Digital Product Passport & Lifecycle Finance (EU ESPR) ──────────
    # EU ESPR 2024/1781 · EU Battery Reg 2023/1542 · EU Textile · EPR · LCA
    op.execute("""
        CREATE TABLE IF NOT EXISTS digital_product_passport_assessments (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            product_name                TEXT,
            product_category            TEXT,
            gtin_ean                    TEXT,
            assessment_date             DATE,
            -- EU ESPR compliance
            espr_applicable             BOOLEAN DEFAULT FALSE,
            espr_regulation_ref         TEXT,
            espr_score                  NUMERIC(5,2),
            espr_status                 TEXT,
            espr_gaps                   JSONB,
            -- DPP schema completeness
            dpp_completeness_pct        NUMERIC(5,2),
            dpp_mandatory_fields        INTEGER,
            dpp_completed_fields        INTEGER,
            dpp_schema_version          TEXT,
            -- Lifecycle GHG
            lifecycle_scope1_tco2e      NUMERIC(12,4),
            lifecycle_scope2_tco2e      NUMERIC(12,4),
            lifecycle_scope3_tco2e      NUMERIC(12,4),
            lifecycle_total_tco2e       NUMERIC(12,4),
            lifecycle_method            TEXT,
            carbon_footprint_per_unit   NUMERIC(10,6),
            -- Circularity
            recycled_content_pct        NUMERIC(5,2),
            recyclability_score         NUMERIC(5,2),
            durability_score            NUMERIC(5,2),
            repairability_score         NUMERIC(5,2),
            circularity_index           NUMERIC(5,2),
            -- EU Battery Regulation
            is_battery_product          BOOLEAN DEFAULT FALSE,
            battery_carbon_footprint    NUMERIC(10,4),
            battery_recycled_content    JSONB,
            battery_supply_chain_dd     BOOLEAN DEFAULT FALSE,
            battery_regulation_score    NUMERIC(5,2),
            -- EPR liability
            epr_scheme_country          TEXT,
            epr_annual_levy_eur         NUMERIC(12,2),
            epr_exemption_applicable    BOOLEAN DEFAULT FALSE,
            -- overall
            dpp_readiness_score         NUMERIC(5,2),
            espr_tier                   TEXT,
            -- metadata
            raw_input                   JSONB,
            full_result                 JSONB,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_dpp_entity ON digital_product_passport_assessments(entity_id);
        CREATE INDEX IF NOT EXISTS idx_dpp_category ON digital_product_passport_assessments(product_category);
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS product_lifecycle_stages (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            assessment_id               TEXT,
            stage_name                  TEXT,
            stage_code                  TEXT,
            tco2e                       NUMERIC(12,6),
            energy_mwh                  NUMERIC(12,4),
            water_m3                    NUMERIC(12,4),
            waste_tonnes                NUMERIC(12,4),
            primary_activity            TEXT,
            ef_source                   TEXT,
            data_quality_score          INTEGER,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_lifecycle_assessment ON product_lifecycle_stages(assessment_id);
    """)

    # ── E83: Adaptation Finance & Resilience Economics ───────────────────────
    # GARI · GFMA Adaptation Taxonomy · MDB PCRAFI · UNFCCC LT-LEDS · NAPs
    op.execute("""
        CREATE TABLE IF NOT EXISTS adaptation_finance_assessments (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            project_name                TEXT,
            country_code                TEXT,
            assessment_date             DATE,
            -- GFMA adaptation taxonomy
            adaptation_category         TEXT,
            adaptation_subcategory      TEXT,
            gfma_aligned                BOOLEAN DEFAULT FALSE,
            gfma_score                  NUMERIC(5,2),
            -- resilience delta
            baseline_physical_risk_score NUMERIC(5,2),
            post_investment_risk_score  NUMERIC(5,2),
            resilience_delta            NUMERIC(5,2),
            risk_reduction_pct          NUMERIC(5,2),
            -- GARI methodology
            gari_score                  NUMERIC(5,2),
            gari_tier                   TEXT,
            adaptation_effectiveness    NUMERIC(5,2),
            maladaptation_risk          NUMERIC(5,2),
            -- investment sizing
            total_investment_m          NUMERIC(15,2),
            public_finance_m            NUMERIC(15,2),
            private_finance_m           NUMERIC(15,2),
            blended_ratio               NUMERIC(5,2),
            expected_lives_protected    INTEGER,
            cost_per_beneficiary_usd    NUMERIC(10,2),
            -- NPV / BCR
            adaptation_npv_m            NUMERIC(15,2),
            benefit_cost_ratio          NUMERIC(6,2),
            discount_rate_pct           NUMERIC(4,2),
            appraisal_horizon_years     INTEGER,
            -- NAP alignment
            nap_country_aligned         BOOLEAN DEFAULT FALSE,
            nap_priority_area           TEXT,
            ndcs_aligned                BOOLEAN DEFAULT FALSE,
            -- MDB / climate finance
            mdb_financing_eligible      BOOLEAN DEFAULT FALSE,
            mdb_facility               TEXT,
            gcf_eligible                BOOLEAN DEFAULT FALSE,
            gef_eligible                BOOLEAN DEFAULT FALSE,
            -- UNFCCC LT-LEDS
            lt_leds_aligned             BOOLEAN DEFAULT FALSE,
            rcp_scenario_designed_for   TEXT,
            climate_horizon_year        INTEGER,
            -- physical hazards addressed
            hazards_addressed           JSONB,
            sector                      TEXT,
            -- overall
            adaptation_score            NUMERIC(5,2),
            bankability_tier            TEXT,
            -- metadata
            raw_input                   JSONB,
            full_result                 JSONB,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_adaptation_entity ON adaptation_finance_assessments(entity_id);
        CREATE INDEX IF NOT EXISTS idx_adaptation_country ON adaptation_finance_assessments(country_code);
        CREATE INDEX IF NOT EXISTS idx_adaptation_tier ON adaptation_finance_assessments(bankability_tier);
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS adaptation_portfolio_assessments (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            assessment_date             DATE,
            -- portfolio summary
            total_projects              INTEGER,
            total_investment_m          NUMERIC(15,2),
            avg_resilience_delta        NUMERIC(5,2),
            avg_benefit_cost_ratio      NUMERIC(6,2),
            avg_gari_score              NUMERIC(5,2),
            -- by category
            category_breakdown          JSONB,
            country_breakdown           JSONB,
            hazard_breakdown            JSONB,
            -- finance structure
            public_finance_pct          NUMERIC(5,2),
            private_finance_pct         NUMERIC(5,2),
            blended_pct                 NUMERIC(5,2),
            gcf_eligible_pct            NUMERIC(5,2),
            -- alignment
            nap_aligned_pct             NUMERIC(5,2),
            ndc_aligned_pct             NUMERIC(5,2),
            gfma_aligned_pct            NUMERIC(5,2),
            -- portfolio score
            portfolio_adaptation_score  NUMERIC(5,2),
            portfolio_tier              TEXT,
            projects_detail             JSONB,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_adapt_portfolio_entity ON adaptation_portfolio_assessments(entity_id);
    """)


def downgrade():
    for table in [
        "adaptation_portfolio_assessments",
        "adaptation_finance_assessments",
        "product_lifecycle_stages",
        "digital_product_passport_assessments",
        "structured_pool_assets",
        "green_securitisation_assessments",
        "nature_target_registry",
        "sbtn_assessments",
    ]:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
