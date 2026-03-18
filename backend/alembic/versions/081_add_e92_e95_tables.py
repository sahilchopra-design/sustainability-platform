"""Add E92-E95 tables: Water Risk, Critical Minerals, Nature-Based Solutions, SFDR Art 9

Revision ID: 081_add_e92_e95_tables
Revises: 080_add_e88_e91_tables
Create Date: 2026-03-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '081'
down_revision = '080'
branch_labels = None
depends_on = None


def upgrade():
    # ── E92: Water Risk & Stewardship Finance ────────────────────────────────
    # CDP Water Security A-list · WRI AQUEDUCT 4.0 · TNFD E3 · AWS Standard v2 · CEO Water Mandate
    op.execute("""
        CREATE TABLE IF NOT EXISTS water_risk_assessments (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            assessment_date             DATE,
            -- WRI AQUEDUCT 4.0 scores
            baseline_water_stress       NUMERIC(5,2),
            interannual_variability     NUMERIC(5,2),
            seasonal_variability        NUMERIC(5,2),
            groundwater_depletion       NUMERIC(5,2),
            riverine_flood_risk         NUMERIC(5,2),
            coastal_eutrophication      NUMERIC(5,2),
            aqueduct_overall_score      NUMERIC(5,2),
            aqueduct_risk_tier          TEXT,
            -- CDP Water Security scoring
            cdp_water_score             TEXT,
            cdp_governance_score        NUMERIC(5,2),
            cdp_risk_assessment_score   NUMERIC(5,2),
            cdp_targets_score           NUMERIC(5,2),
            cdp_performance_score       NUMERIC(5,2),
            cdp_a_list_eligible         BOOLEAN DEFAULT FALSE,
            -- TNFD E3 water metrics
            water_withdrawal_m3         NUMERIC(15,2),
            water_consumption_m3        NUMERIC(15,2),
            water_discharge_m3          NUMERIC(15,2),
            water_recycled_pct          NUMERIC(5,2),
            water_stressed_area_pct     NUMERIC(5,2),
            tnfd_water_disclosure_score NUMERIC(5,2),
            -- AWS Standard v2.0
            aws_balance_score           NUMERIC(5,2),
            aws_engagement_score        NUMERIC(5,2),
            aws_governance_score        NUMERIC(5,2),
            aws_overall_score           NUMERIC(5,2),
            aws_certification_eligible  BOOLEAN DEFAULT FALSE,
            -- CEO Water Mandate commitment
            cwm_committed               BOOLEAN DEFAULT FALSE,
            cwm_targets_set             INTEGER DEFAULT 0,
            cwm_stewardship_score       NUMERIC(5,2),
            -- Financial exposure
            water_opex_risk_m           NUMERIC(12,2),
            water_regulatory_risk_m     NUMERIC(12,2),
            water_stranded_asset_risk_m NUMERIC(12,2),
            total_water_financial_risk_m NUMERIC(15,2),
            -- Stewardship bond eligibility
            water_bond_eligible         BOOLEAN DEFAULT FALSE,
            water_bond_framework_score  NUMERIC(5,2),
            -- overall
            water_risk_score            NUMERIC(5,2),
            water_risk_tier             TEXT,
            -- metadata
            raw_input                   JSONB,
            full_result                 JSONB,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_water_risk_entity ON water_risk_assessments(entity_id);
        CREATE INDEX IF NOT EXISTS idx_water_risk_tier ON water_risk_assessments(water_risk_tier);
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS water_stewardship_targets (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            target_type                 TEXT,
            baseline_year               INTEGER,
            target_year                 INTEGER,
            baseline_m3                 NUMERIC(15,2),
            target_m3                   NUMERIC(15,2),
            reduction_pct               NUMERIC(5,2),
            verification_standard       TEXT,
            catchment_specific          BOOLEAN DEFAULT FALSE,
            progress_pct                NUMERIC(5,2),
            on_track                    BOOLEAN DEFAULT TRUE,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_water_target_entity ON water_stewardship_targets(entity_id);
    """)

    # ── E93: Critical Minerals & Transition Metals Risk ───────────────────────
    # IEA CRM 2024 · EU CRM Act 2024/1252 · IRMA Standard · OECD DDG · RMI · DRC conflict
    op.execute("""
        CREATE TABLE IF NOT EXISTS critical_minerals_assessments (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            assessment_date             DATE,
            -- Supply chain exposure
            minerals_assessed           JSONB,
            primary_mineral             TEXT,
            total_spend_m               NUMERIC(12,2),
            supply_chain_tiers_covered  INTEGER,
            -- IEA criticality scores
            iea_demand_growth_score     NUMERIC(5,2),
            iea_supply_concentration    NUMERIC(5,2),
            iea_geopolitical_risk       NUMERIC(5,2),
            iea_substitutability        NUMERIC(5,2),
            iea_criticality_composite   NUMERIC(5,2),
            -- EU CRM Act compliance
            eu_crm_act_applicable       BOOLEAN DEFAULT FALSE,
            eu_crm_strategic_mineral    BOOLEAN DEFAULT FALSE,
            eu_crm_critical_mineral     BOOLEAN DEFAULT FALSE,
            eu_crm_audit_required       BOOLEAN DEFAULT FALSE,
            eu_crm_compliance_score     NUMERIC(5,2),
            eu_crm_gaps                 JSONB,
            -- IRMA responsible mining
            irma_applicable             BOOLEAN DEFAULT FALSE,
            irma_score                  NUMERIC(5,2),
            irma_tier                   TEXT,
            irma_gaps                   JSONB,
            -- OECD Due Diligence
            oecd_ddg_score              NUMERIC(5,2),
            oecd_5step_compliance       JSONB,
            conflict_mineral_risk       BOOLEAN DEFAULT FALSE,
            conflict_region_exposure    JSONB,
            -- Transition exposure
            ev_battery_exposure_m       NUMERIC(12,2),
            solar_pv_exposure_m         NUMERIC(12,2),
            wind_turbine_exposure_m     NUMERIC(12,2),
            grid_storage_exposure_m     NUMERIC(12,2),
            total_transition_exposure_m NUMERIC(15,2),
            -- Price & supply risk
            price_volatility_score      NUMERIC(5,2),
            supply_disruption_prob_pct  NUMERIC(5,2),
            concentration_hhi           NUMERIC(8,2),
            top3_country_share_pct      NUMERIC(5,2),
            -- overall
            crm_risk_score              NUMERIC(5,2),
            crm_risk_tier               TEXT,
            -- metadata
            raw_input                   JSONB,
            full_result                 JSONB,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_crm_entity ON critical_minerals_assessments(entity_id);
        CREATE INDEX IF NOT EXISTS idx_crm_mineral ON critical_minerals_assessments(primary_mineral);
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS mineral_supply_chain_map (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            assessment_id               TEXT,
            mineral_name                TEXT,
            tier_level                  INTEGER,
            supplier_country            TEXT,
            supplier_name               TEXT,
            annual_volume_t             NUMERIC(12,2),
            spend_m                     NUMERIC(10,2),
            conflict_risk               BOOLEAN DEFAULT FALSE,
            irma_certified              BOOLEAN DEFAULT FALSE,
            certification_body          TEXT,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_mineral_scm_assessment ON mineral_supply_chain_map(assessment_id);
    """)

    # ── E94: Nature-Based Solutions Finance ──────────────────────────────────
    # IUCN NbS Global Standard v2 · ICROA NbS · VCMI Core Claims · REDD+ VCS · GBF KM Target 2
    op.execute("""
        CREATE TABLE IF NOT EXISTS nbs_finance_assessments (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            project_name                TEXT,
            nbs_category                TEXT,
            country_code                TEXT,
            biome_type                  TEXT,
            assessment_date             DATE,
            -- IUCN NbS Global Standard v2.0
            iucn_criterion_1_score      NUMERIC(5,2),
            iucn_criterion_2_score      NUMERIC(5,2),
            iucn_criterion_3_score      NUMERIC(5,2),
            iucn_criterion_4_score      NUMERIC(5,2),
            iucn_criterion_5_score      NUMERIC(5,2),
            iucn_criterion_6_score      NUMERIC(5,2),
            iucn_criterion_7_score      NUMERIC(5,2),
            iucn_criterion_8_score      NUMERIC(5,2),
            iucn_composite_score        NUMERIC(5,2),
            iucn_nbs_tier               TEXT,
            -- Carbon co-benefits
            carbon_sequestration_tco2_yr NUMERIC(12,2),
            carbon_sequestration_total  NUMERIC(15,2),
            carbon_credit_eligible      BOOLEAN DEFAULT FALSE,
            carbon_credit_standard      TEXT,
            vcm_credit_price_usd        NUMERIC(8,2),
            -- Biodiversity co-benefits
            species_protected_count     INTEGER,
            habitat_area_ha             NUMERIC(12,2),
            msa_uplift_pct              NUMERIC(5,2),
            gbf_target_2_contribution   NUMERIC(5,2),
            -- Water co-benefits
            watershed_protection_m3_yr  NUMERIC(12,2),
            water_quality_improvement   NUMERIC(5,2),
            -- Social co-benefits
            communities_benefited       INTEGER,
            indigenous_peoples_involved BOOLEAN DEFAULT FALSE,
            livelihoods_supported       INTEGER,
            -- VCMI Core Carbon Claims
            vcmi_claim_eligible         TEXT,
            vcmi_integrity_score        NUMERIC(5,2),
            -- Economics
            total_investment_m          NUMERIC(12,2),
            annual_maintenance_m        NUMERIC(10,2),
            carbon_revenue_m_yr         NUMERIC(10,2),
            ecosystem_service_revenue_m NUMERIC(10,2),
            npv_m                       NUMERIC(12,2),
            irr_pct                     NUMERIC(5,2),
            payback_years               NUMERIC(5,2),
            -- Blended finance
            public_finance_m            NUMERIC(10,2),
            private_finance_m           NUMERIC(10,2),
            philanthropic_m             NUMERIC(10,2),
            gcf_eligible                BOOLEAN DEFAULT FALSE,
            -- overall
            nbs_quality_score           NUMERIC(5,2),
            nbs_bankability_tier        TEXT,
            -- metadata
            raw_input                   JSONB,
            full_result                 JSONB,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_nbs_entity ON nbs_finance_assessments(entity_id);
        CREATE INDEX IF NOT EXISTS idx_nbs_category ON nbs_finance_assessments(nbs_category);
        CREATE INDEX IF NOT EXISTS idx_nbs_tier ON nbs_finance_assessments(nbs_bankability_tier);
    """)

    # ── E95: SFDR Article 9 Impact Fund Assessment ───────────────────────────
    # SFDR RTS 2022/1288 · ESMA SFDR Q&A 2023 · SFDR Level 2 Art 9 · EC Platform on SF · TCFD
    op.execute("""
        CREATE TABLE IF NOT EXISTS sfdr_art9_assessments (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            fund_name                   TEXT,
            assessment_date             DATE,
            -- Fund classification
            current_article_classification TEXT,
            target_article              TEXT,
            aum_m                       NUMERIC(15,2),
            currency                    TEXT DEFAULT 'EUR',
            -- Art 9 eligibility criteria
            sustainable_investment_pct  NUMERIC(5,2),
            taxonomy_aligned_pct        NUMERIC(5,2),
            social_sustainable_pct      NUMERIC(5,2),
            governance_screen_pass      BOOLEAN DEFAULT FALSE,
            -- RTS Annex I/II pre-contractual
            investment_objective_score  NUMERIC(5,2),
            impact_strategy_score       NUMERIC(5,2),
            additionality_claim         TEXT,
            impact_measurement_score    NUMERIC(5,2),
            engagement_policy_score     NUMERIC(5,2),
            rts_annex_completeness_pct  NUMERIC(5,2),
            -- PAI indicators (14 mandatory)
            pai_ghg_scope1_2            NUMERIC(12,4),
            pai_carbon_footprint        NUMERIC(8,4),
            pai_ghg_intensity           NUMERIC(8,4),
            pai_fossil_fuel_exposure    NUMERIC(5,2),
            pai_renewable_energy_pct    NUMERIC(5,2),
            pai_energy_consumption      NUMERIC(10,2),
            pai_biodiversity_violation  BOOLEAN DEFAULT FALSE,
            pai_water_emission          NUMERIC(10,2),
            pai_hazardous_waste         NUMERIC(10,2),
            pai_ungc_oecd_violation     BOOLEAN DEFAULT FALSE,
            pai_ungc_compliance_pct     NUMERIC(5,2),
            pai_gender_pay_gap          NUMERIC(5,2),
            pai_board_gender_diversity  NUMERIC(5,2),
            pai_controversial_weapons   BOOLEAN DEFAULT FALSE,
            -- Impact KPIs
            impact_kpis_defined         INTEGER DEFAULT 0,
            impact_kpis_measured        INTEGER DEFAULT 0,
            impact_kpis                 JSONB,
            -- SFDR downgrades (post-ESMA Q&A 2023)
            downgrade_risk_score        NUMERIC(5,2),
            downgrade_triggers          JSONB,
            esma_qa_compliance          BOOLEAN DEFAULT FALSE,
            -- DNSH verification
            dnsh_climate_mitigation     BOOLEAN DEFAULT FALSE,
            dnsh_climate_adaptation     BOOLEAN DEFAULT FALSE,
            dnsh_water                  BOOLEAN DEFAULT FALSE,
            dnsh_circular               BOOLEAN DEFAULT FALSE,
            dnsh_pollution              BOOLEAN DEFAULT FALSE,
            dnsh_biodiversity           BOOLEAN DEFAULT FALSE,
            dnsh_all_pass               BOOLEAN DEFAULT FALSE,
            -- Overall
            art9_eligibility_score      NUMERIC(5,2),
            art9_eligible               BOOLEAN DEFAULT FALSE,
            compliance_tier             TEXT,
            -- metadata
            raw_input                   JSONB,
            full_result                 JSONB,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_art9_entity ON sfdr_art9_assessments(entity_id);
        CREATE INDEX IF NOT EXISTS idx_art9_fund ON sfdr_art9_assessments(fund_name);
        CREATE INDEX IF NOT EXISTS idx_art9_eligible ON sfdr_art9_assessments(art9_eligible);
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS sfdr_art9_portfolio_holdings (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            assessment_id               TEXT,
            holding_name                TEXT,
            isin                        TEXT,
            weight_pct                  NUMERIC(6,3),
            sustainable_investment      BOOLEAN DEFAULT FALSE,
            taxonomy_aligned_pct        NUMERIC(5,2),
            pai_data_quality            INTEGER,
            engagement_active           BOOLEAN DEFAULT FALSE,
            exclusion_criteria_met      BOOLEAN DEFAULT TRUE,
            dnsh_pass                   BOOLEAN DEFAULT FALSE,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_art9_holdings_assessment ON sfdr_art9_portfolio_holdings(assessment_id);
    """)


def downgrade():
    for table in [
        "sfdr_art9_portfolio_holdings",
        "sfdr_art9_assessments",
        "nbs_finance_assessments",
        "mineral_supply_chain_map",
        "critical_minerals_assessments",
        "water_stewardship_targets",
        "water_risk_assessments",
    ]:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
