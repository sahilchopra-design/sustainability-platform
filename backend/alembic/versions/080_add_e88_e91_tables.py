"""Add E88-E91 tables: Biodiversity Credits, Just Transition, Carbon Removal, Climate Litigation

Revision ID: 080_add_e88_e91_tables
Revises: 079_add_e84_e87_tables
Create Date: 2026-03-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '080'
down_revision = '079'
branch_labels = None
depends_on = None


def upgrade():
    # ── E88: Biodiversity Credits & Nature Markets ────────────────────────────
    # TNFD v1.0 · Verra VM0033 · Plan Vivo · GBF KM Target 15 · BNG DEFRA Metric 4.0 · SBTN
    op.execute("""
        CREATE TABLE IF NOT EXISTS biodiversity_credit_assessments (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            project_name                TEXT,
            assessment_date             DATE,
            -- Credit type & standard
            credit_type                 TEXT,
            standard                    TEXT,
            methodology_code            TEXT,
            -- BNG DEFRA Metric 4.0
            habitat_units_baseline      NUMERIC(12,4),
            habitat_units_post          NUMERIC(12,4),
            biodiversity_net_gain_pct   NUMERIC(5,2),
            bng_10pct_met               BOOLEAN DEFAULT FALSE,
            distinctiveness_score       NUMERIC(5,2),
            -- Verra VM0033 / TNFD
            msa_km2_baseline            NUMERIC(15,4),
            msa_km2_post                NUMERIC(15,4),
            msa_uplift_pct              NUMERIC(5,2),
            tnfd_pillar_scores          JSONB,
            tnfd_composite              NUMERIC(5,2),
            -- Ecosystem services valuation
            provisioning_services_m     NUMERIC(12,2),
            regulating_services_m       NUMERIC(12,2),
            cultural_services_m         NUMERIC(12,2),
            supporting_services_m       NUMERIC(12,2),
            total_ecosystem_value_m     NUMERIC(12,2),
            -- GBF Kunming-Montreal Target 15
            gbf_t15_disclosure_score    NUMERIC(5,2),
            gbf_t15_dependencies        JSONB,
            gbf_t15_impacts             JSONB,
            gbf_t15_gaps                JSONB,
            -- Credit pricing & market
            credit_price_usd            NUMERIC(8,2),
            credits_generated           NUMERIC(12,2),
            market_value_usd_m          NUMERIC(12,2),
            additionality_score         NUMERIC(5,2),
            permanence_risk_score       NUMERIC(5,2),
            -- SBTN alignment
            sbtn_step1_score            NUMERIC(5,2),
            sbtn_step3_msa_footprint    NUMERIC(15,4),
            sbtn_aligned                BOOLEAN DEFAULT FALSE,
            -- Plan Vivo
            plan_vivo_eligible          BOOLEAN DEFAULT FALSE,
            community_benefit_pct       NUMERIC(5,2),
            -- overall
            biodiversity_credit_score   NUMERIC(5,2),
            credit_quality_tier         TEXT,
            -- metadata
            raw_input                   JSONB,
            full_result                 JSONB,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_bio_credit_entity ON biodiversity_credit_assessments(entity_id);
        CREATE INDEX IF NOT EXISTS idx_bio_credit_standard ON biodiversity_credit_assessments(standard);
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS nature_market_transactions (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            transaction_date            DATE,
            transaction_type            TEXT,
            credit_standard             TEXT,
            habitat_type                TEXT,
            units_transacted            NUMERIC(12,4),
            price_per_unit_usd          NUMERIC(8,2),
            total_value_usd             NUMERIC(15,2),
            registry_id                 TEXT,
            project_country             TEXT,
            vintate_year                INTEGER,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_nature_mkt_entity ON nature_market_transactions(entity_id);
    """)

    # ── E89: Just Transition Finance ─────────────────────────────────────────
    # ILO Just Transition Guidelines 2015 · EU JTF Reg 2021/1056 · OECD · PPCA · CIF
    op.execute("""
        CREATE TABLE IF NOT EXISTS just_transition_assessments (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            project_name                TEXT,
            country_code                TEXT,
            region                      TEXT,
            assessment_date             DATE,
            -- Sector & workforce impact
            primary_sector              TEXT,
            affected_workers            INTEGER,
            fossil_fuel_jobs_at_risk    INTEGER,
            green_jobs_created          INTEGER,
            net_jobs_impact             INTEGER,
            avg_wage_fossil_eur         NUMERIC(8,2),
            avg_wage_green_eur          NUMERIC(8,2),
            wage_transition_gap_pct     NUMERIC(5,2),
            -- ILO Just Transition scoring
            ilo_social_dialogue_score   NUMERIC(5,2),
            ilo_skills_reskilling_score NUMERIC(5,2),
            ilo_social_protection_score NUMERIC(5,2),
            ilo_active_labour_score     NUMERIC(5,2),
            ilo_community_invest_score  NUMERIC(5,2),
            ilo_composite_score         NUMERIC(5,2),
            ilo_jt_tier                 TEXT,
            -- EU Just Transition Fund eligibility
            eu_jtf_eligible             BOOLEAN DEFAULT FALSE,
            eu_jtf_allocation_m         NUMERIC(12,2),
            territorial_just_plan_score NUMERIC(5,2),
            -- PPCA & coal community risk
            ppca_aligned                BOOLEAN DEFAULT FALSE,
            coal_dependency_pct         NUMERIC(5,2),
            coal_community_risk_score   NUMERIC(5,2),
            phase_out_year              INTEGER,
            -- Climate Investment Funds
            cif_eligible                BOOLEAN DEFAULT FALSE,
            cif_facility               TEXT,
            concessional_finance_m      NUMERIC(12,2),
            -- Community resilience
            community_gdp_dependency_pct NUMERIC(5,2),
            stranded_infrastructure_m   NUMERIC(12,2),
            reskilling_cost_m           NUMERIC(12,2),
            transition_timeline_years   INTEGER,
            -- overall
            just_transition_score       NUMERIC(5,2),
            transition_risk_tier        TEXT,
            -- metadata
            raw_input                   JSONB,
            full_result                 JSONB,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_jt_entity ON just_transition_assessments(entity_id);
        CREATE INDEX IF NOT EXISTS idx_jt_country ON just_transition_assessments(country_code);
        CREATE INDEX IF NOT EXISTS idx_jt_tier ON just_transition_assessments(transition_risk_tier);
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS community_impact_assessments (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            assessment_id               TEXT,
            community_name              TEXT,
            community_type              TEXT,
            population                  INTEGER,
            fossil_employment_pct       NUMERIC(5,2),
            alternative_employers       INTEGER,
            skills_transferability_score NUMERIC(5,2),
            infrastructure_quality_score NUMERIC(5,2),
            social_cohesion_score       NUMERIC(5,2),
            transition_vulnerability    TEXT,
            recommended_interventions   JSONB,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_community_impact_assessment ON community_impact_assessments(assessment_id);
    """)

    # ── E90: Carbon Removal & CDR Finance ────────────────────────────────────
    # IPCC AR6 CDR · Oxford CDR Principles · Article 6.4 · BECCS/DACS/EW/Blue Carbon/Biochar
    op.execute("""
        CREATE TABLE IF NOT EXISTS cdr_assessments (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            project_name                TEXT,
            cdr_type                    TEXT,
            assessment_date             DATE,
            -- CDR volumes
            removal_capacity_tco2_yr    NUMERIC(15,2),
            actual_removal_tco2_yr      NUMERIC(15,2),
            utilisation_rate_pct        NUMERIC(5,2),
            cumulative_removal_tco2     NUMERIC(15,2),
            -- Oxford CDR Principles scoring
            oxford_additionality_score  NUMERIC(5,2),
            oxford_permanence_score     NUMERIC(5,2),
            oxford_monitoring_score     NUMERIC(5,2),
            oxford_leakage_score        NUMERIC(5,2),
            oxford_composite_score      NUMERIC(5,2),
            oxford_tier                 TEXT,
            -- Permanence risk
            permanence_years            INTEGER,
            reversal_risk_score         NUMERIC(5,2),
            buffer_pool_pct             NUMERIC(5,2),
            -- Article 6.4 (Paris Agreement)
            article_64_eligible         BOOLEAN DEFAULT FALSE,
            itmo_eligible               BOOLEAN DEFAULT FALSE,
            corresponding_adjustment    BOOLEAN DEFAULT FALSE,
            host_country_ndc_contrib    BOOLEAN DEFAULT FALSE,
            -- Technology readiness
            trl_level                   INTEGER,
            lcoe_usd_tco2              NUMERIC(8,2),
            cost_trajectory_2030        NUMERIC(8,2),
            cost_trajectory_2050        NUMERIC(8,2),
            -- Co-benefits
            biodiversity_cobenefit      NUMERIC(5,2),
            water_cobenefit             NUMERIC(5,2),
            social_cobenefit            NUMERIC(5,2),
            sdg_alignment               JSONB,
            -- Financing
            capex_m                     NUMERIC(12,2),
            opex_m_yr                   NUMERIC(12,2),
            blended_finance_eligible    BOOLEAN DEFAULT FALSE,
            frontier_eligible           BOOLEAN DEFAULT FALSE,
            credit_price_usd_tco2       NUMERIC(8,2),
            -- IPCC AR6 alignment
            ipcc_cdr_category           TEXT,
            ipcc_scalability_rating     TEXT,
            -- overall
            cdr_quality_score           NUMERIC(5,2),
            cdr_quality_tier            TEXT,
            -- metadata
            raw_input                   JSONB,
            full_result                 JSONB,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_cdr_entity ON cdr_assessments(entity_id);
        CREATE INDEX IF NOT EXISTS idx_cdr_type ON cdr_assessments(cdr_type);
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS cdr_project_registry (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            project_type                TEXT,
            registry                    TEXT,
            country_code                TEXT,
            capacity_tco2_yr            NUMERIC(15,2),
            status                      TEXT DEFAULT 'pipeline',
            first_delivery_year         INTEGER,
            offtake_price_usd           NUMERIC(8,2),
            offtake_volume_tco2_yr      NUMERIC(12,2),
            buyer_type                  TEXT,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_cdr_registry_entity ON cdr_project_registry(entity_id);
    """)

    # ── E91: Climate Litigation Risk ──────────────────────────────────────────
    # UNEP Climate Litigation v3 · Sabin Center · Grantham RI · Duties X Framework · D&O
    op.execute("""
        CREATE TABLE IF NOT EXISTS climate_litigation_risk_assessments (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            assessment_date             DATE,
            -- Litigation exposure profile
            sector                      TEXT,
            jurisdiction                TEXT,
            entity_type                 TEXT,
            -- UNEP/Sabin case taxonomy
            greenwashing_risk_score     NUMERIC(5,2),
            disclosure_liability_score  NUMERIC(5,2),
            transition_planning_risk    NUMERIC(5,2),
            physical_risk_liability     NUMERIC(5,2),
            carbon_major_exposure       NUMERIC(5,2),
            human_rights_climate_risk   NUMERIC(5,2),
            -- Fiduciary duty (Duties X Framework)
            fiduciary_duty_score        NUMERIC(5,2),
            fiduciary_gaps              JSONB,
            stewardship_adequacy_score  NUMERIC(5,2),
            -- D&O liability
            do_exposure_m               NUMERIC(12,2),
            do_trigger_scenarios        JSONB,
            securities_litigation_risk  NUMERIC(5,2),
            -- Attribution science risk
            attribution_science_applicable BOOLEAN DEFAULT FALSE,
            mhc_attribution_score       NUMERIC(5,2),
            physical_damage_attributable_pct NUMERIC(5,2),
            -- Regulatory enforcement risk
            sec_risk_score              NUMERIC(5,2),
            fca_risk_score              NUMERIC(5,2),
            esma_risk_score             NUMERIC(5,2),
            csrd_penalty_exposure_m     NUMERIC(12,2),
            -- Active cases / precedents
            active_cases_count          INTEGER DEFAULT 0,
            precedent_cases             JSONB,
            jurisdiction_risk_score     NUMERIC(5,2),
            -- Financial quantification
            max_litigation_exposure_m   NUMERIC(15,2),
            expected_litigation_cost_m  NUMERIC(15,2),
            litigation_provision_m      NUMERIC(12,2),
            insurance_coverage_m        NUMERIC(12,2),
            -- overall
            litigation_risk_score       NUMERIC(5,2),
            risk_tier                   TEXT,
            -- metadata
            raw_input                   JSONB,
            full_result                 JSONB,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_litigation_entity ON climate_litigation_risk_assessments(entity_id);
        CREATE INDEX IF NOT EXISTS idx_litigation_sector ON climate_litigation_risk_assessments(sector);
        CREATE INDEX IF NOT EXISTS idx_litigation_tier ON climate_litigation_risk_assessments(risk_tier);
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS litigation_case_registry (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            case_name                   TEXT,
            case_type                   TEXT,
            jurisdiction                TEXT,
            court_level                 TEXT,
            filing_year                 INTEGER,
            status                      TEXT DEFAULT 'active',
            plaintiff_type              TEXT,
            claim_amount_m              NUMERIC(12,2),
            outcome                     TEXT,
            settlement_amount_m         NUMERIC(12,2),
            precedent_value             TEXT,
            sabin_case_id               TEXT,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_lit_case_entity ON litigation_case_registry(entity_id);
    """)


def downgrade():
    for table in [
        "litigation_case_registry",
        "climate_litigation_risk_assessments",
        "cdr_project_registry",
        "cdr_assessments",
        "community_impact_assessments",
        "just_transition_assessments",
        "nature_market_transactions",
        "biodiversity_credit_assessments",
    ]:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
