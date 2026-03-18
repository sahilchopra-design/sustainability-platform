"""Add E44-E47 tables: Biodiversity Finance v2, Prudential Climate Risk, Carbon Markets Intel, Just Transition

Revision ID: 069_add_e44_e47_tables
Revises: 068_add_e40_e43_tables
Create Date: 2026-03-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '069'
down_revision = '068'
branch_labels = None
depends_on = None


def upgrade():
    # ── E44: Biodiversity Finance v2 ────────────────────────────────────────────
    # TNFD v1.0 full LEAP · PBAF attribution · ENCORE 23 ecosystem services
    # GBF/COP15 30×30 · MSA footprint · BFFI · BNG Metric 4.0
    op.execute("""
        CREATE TABLE IF NOT EXISTS biodiversity_finance_v2_assessments (
            id                           TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                    TEXT NOT NULL,
            entity_name                  TEXT,
            assessment_date              DATE,
            assessment_type              TEXT,
            -- TNFD LEAP composite
            leap_locate_score            NUMERIC(5,2),
            leap_evaluate_score          NUMERIC(5,2),
            leap_assess_score            NUMERIC(5,2),
            leap_prepare_score           NUMERIC(5,2),
            leap_composite_score         NUMERIC(5,2),
            -- PBAF attribution
            pbaf_attribution_factor      NUMERIC(10,6),
            pbaf_method                  TEXT,
            -- ENCORE scoring
            nature_dependency_score      NUMERIC(5,2),
            nature_impact_score          NUMERIC(5,2),
            high_dependency_services     JSONB,
            -- MSA footprint (mean species abundance)
            msa_footprint_km2            NUMERIC(15,4),
            msa_loss_fraction            NUMERIC(8,6),
            -- GBF/COP15 30x30 alignment
            gbf_target15_aligned         BOOLEAN,
            cop15_30x30_contribution_pct NUMERIC(8,4),
            -- BNG (DEFRA Metric 4.0)
            bng_baseline_units           NUMERIC(10,2),
            bng_post_development_units   NUMERIC(10,2),
            bng_net_gain_pct             NUMERIC(8,2),
            bng_credit_required          BOOLEAN,
            -- BFFI (PDF/m2/yr)
            bffi_score                   NUMERIC(8,4),
            -- Materiality
            materiality_rating           TEXT,
            priority_ecosystems          JSONB,
            -- Cross-framework linkages
            tnfd_esrs_e4_aligned         BOOLEAN,
            gri_304_disclosure_score     NUMERIC(5,2),
            eu_taxonomy_dnsh_nature      BOOLEAN,
            sbtn_target_aligned          BOOLEAN,
            -- Meta
            notes                        TEXT,
            created_at                   TIMESTAMPTZ DEFAULT NOW(),
            updated_at                   TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS biodiversity_ecosystem_services (
            id                           TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            assessment_id                TEXT NOT NULL,
            ecosystem_service_id         TEXT NOT NULL,
            ecosystem_service_name       TEXT,
            encore_category              TEXT,
            dependency_level             TEXT,
            dependency_score             NUMERIC(5,2),
            impact_driver                TEXT,
            impact_magnitude             TEXT,
            impact_score                 NUMERIC(5,2),
            materiality_flag             BOOLEAN,
            mitigation_measure           TEXT,
            residual_risk_score          NUMERIC(5,2),
            location_specific            BOOLEAN,
            hotspot_flag                 BOOLEAN,
            created_at                   TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # ── E45: Prudential Climate Risk ─────────────────────────────────────────────
    # BOE/PRA BES 2021/2025 · ECB DFAST 2024 · NGFS v4 · ICAAP Pillar 2a/2b
    # Basel SRP 43.1 categorisation · EBA SREP climate overlay
    op.execute("""
        CREATE TABLE IF NOT EXISTS prudential_climate_risk_assessments (
            id                              TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                       TEXT NOT NULL,
            entity_name                     TEXT,
            institution_type                TEXT,
            reporting_date                  DATE,
            regulator                       TEXT,
            -- Scenario framework
            scenario_framework              TEXT,
            scenarios_assessed              JSONB,
            ngfs_version                    TEXT,
            -- CET1 stress results (percentage points)
            baseline_cet1_pct               NUMERIC(6,3),
            stressed_cet1_orderly           NUMERIC(6,3),
            stressed_cet1_disorderly        NUMERIC(6,3),
            stressed_cet1_hot_house         NUMERIC(6,3),
            cet1_depletion_max_ppts         NUMERIC(6,3),
            cet1_breaches_minimum           BOOLEAN,
            -- Credit risk impacts
            pd_migration_orderly_bps        NUMERIC(8,2),
            pd_migration_disorderly_bps     NUMERIC(8,2),
            lgd_increase_orderly_pct        NUMERIC(6,2),
            lgd_increase_disorderly_pct     NUMERIC(6,2),
            ecl_increase_orderly_musd       NUMERIC(15,2),
            ecl_increase_disorderly_musd    NUMERIC(15,2),
            -- Market risk
            market_risk_loss_orderly_musd   NUMERIC(15,2),
            market_risk_loss_disorderly_musd NUMERIC(15,2),
            -- ICAAP Pillar 2
            icaap_climate_add_on_pct        NUMERIC(6,3),
            pillar2b_buffer_recommendation_pct NUMERIC(6,3),
            srep_climate_finding            TEXT,
            -- Basel SRP 43.1
            srp431_categorisation           TEXT,
            srp431_review_date              DATE,
            -- EBA SREP
            eba_srep_climate_score          INTEGER,
            -- Total regulatory buffer
            total_climate_capital_buffer_pct NUMERIC(6,3),
            total_climate_rwa_uplift_pct    NUMERIC(6,3),
            -- Time horizons
            short_term_horizon_yrs          INTEGER,
            medium_term_horizon_yrs         INTEGER,
            long_term_horizon_yrs           INTEGER,
            -- BOE BES specific
            boe_bes_round                   TEXT,
            boe_bes_llt_loss_musd           NUMERIC(15,2),
            boe_bes_elt_loss_musd           NUMERIC(15,2),
            -- ECB CST specific
            ecb_cst_round                   TEXT,
            ecb_cst_transition_loss_musd    NUMERIC(15,2),
            ecb_cst_physical_loss_musd      NUMERIC(15,2),
            -- Notes
            notes                           TEXT,
            created_at                      TIMESTAMPTZ DEFAULT NOW(),
            updated_at                      TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS prudential_climate_capital_overlays (
            id                             TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            assessment_id                  TEXT NOT NULL,
            segment_name                   TEXT NOT NULL,
            segment_exposure_usd           NUMERIC(18,2),
            transition_risk_rating         TEXT,
            physical_risk_rating           TEXT,
            brown_share_pct                NUMERIC(6,2),
            stranded_asset_exposure_usd    NUMERIC(15,2),
            climate_var_95_pct_usd         NUMERIC(15,2),
            rwa_uplift_pct                 NUMERIC(6,3),
            capital_add_on_usd             NUMERIC(15,2),
            sector_nace                    TEXT,
            crrem_stranding_year           INTEGER,
            scenario_used                  TEXT,
            created_at                     TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # ── E46: Carbon Markets Intelligence ────────────────────────────────────────
    # Paris Art 6.2/6.4 · VCMI Claims Code (Gold/Silver/Bronze)
    # ICVCM CCPs (10 criteria) · CORSIA Phase 2 · VCM registries · pricing
    op.execute("""
        CREATE TABLE IF NOT EXISTS carbon_markets_intel_assessments (
            id                              TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                       TEXT NOT NULL,
            entity_name                     TEXT,
            assessment_date                 DATE,
            purpose                         TEXT,
            -- Portfolio totals
            total_credits_tco2e             NUMERIC(15,2),
            total_spend_usd                 NUMERIC(15,2),
            weighted_avg_price_usd          NUMERIC(8,2),
            -- VCMI Claims Code
            vcmi_claim_level                TEXT,
            vcmi_claim_eligible             BOOLEAN,
            vcmi_mitigation_contribution_pct NUMERIC(8,2),
            vcmi_credibility_score          NUMERIC(5,2),
            -- ICVCM CCPs (10 criteria)
            icvcm_ccp_pass_rate_pct         NUMERIC(6,2),
            icvcm_governance_score          NUMERIC(5,2),
            icvcm_emissions_impact_score    NUMERIC(5,2),
            icvcm_sustainable_dev_score     NUMERIC(5,2),
            icvcm_safeguards_score          NUMERIC(5,2),
            -- CORSIA Phase 2
            corsia_eligible_pct             NUMERIC(6,2),
            corsia_approved_schemes         JSONB,
            corsia_phase                    TEXT,
            -- Article 6.2 / 6.4
            article6_itmo_volume_tco2e      NUMERIC(15,2),
            article6_2_bilateral_pct        NUMERIC(6,2),
            article6_4_mechanism_pct        NUMERIC(6,2),
            corresponding_adjustment_pct    NUMERIC(6,2),
            -- Portfolio quality
            weighted_vintage_year           NUMERIC(6,1),
            methodologies_used              JSONB,
            co_benefit_premium_avg_pct      NUMERIC(6,2),
            high_integrity_share_pct        NUMERIC(6,2),
            registries_used                 JSONB,
            -- Pricing model
            fair_value_usd_per_tco2e        NUMERIC(8,2),
            price_premium_discount_pct      NUMERIC(6,2),
            vintage_discount_factor         NUMERIC(6,4),
            additionality_premium_usd       NUMERIC(6,2),
            co_benefit_premium_usd          NUMERIC(6,2),
            -- Notes
            notes                           TEXT,
            created_at                      TIMESTAMPTZ DEFAULT NOW(),
            updated_at                      TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS carbon_credit_registry_records (
            id                             TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            assessment_id                  TEXT NOT NULL,
            registry                       TEXT NOT NULL,
            project_id                     TEXT,
            project_name                   TEXT,
            methodology_code               TEXT,
            project_type                   TEXT,
            country_code                   TEXT,
            vintage_year                   INTEGER,
            volume_tco2e                   NUMERIC(15,2),
            price_usd                      NUMERIC(8,2),
            total_cost_usd                 NUMERIC(15,2),
            -- Quality flags
            icvcm_ccp_pass                 BOOLEAN,
            vcmi_eligible                  BOOLEAN,
            corsia_eligible                BOOLEAN,
            article6_corresponding_adj     BOOLEAN,
            sdg_contributions              JSONB,
            -- Integrity scores (0-10)
            additionality_score            NUMERIC(5,2),
            permanence_score               NUMERIC(5,2),
            leakage_score                  NUMERIC(5,2),
            measurability_score            NUMERIC(5,2),
            overall_quality_score          NUMERIC(5,2),
            -- Status
            retirement_status              TEXT,
            retirement_date                DATE,
            serial_number                  TEXT,
            created_at                     TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # ── E47: Just Transition & Social Risk ───────────────────────────────────────
    # ILO JT Guidelines (2015) 5 dimensions · CSRD ESRS S1-S4 social scoring
    # SEC Human Capital Item 101(c) · Living Wage (Anker) · Worker Displacement
    # JT Finance taxonomy (CBI) · Community impact
    op.execute("""
        CREATE TABLE IF NOT EXISTS just_transition_assessments (
            id                                  TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                           TEXT NOT NULL,
            entity_name                         TEXT,
            assessment_date                     DATE,
            sector                              TEXT,
            geography                           TEXT,
            -- ILO Just Transition (5 dimensions, score 0-100)
            ilo_dim1_macro_policy_score         NUMERIC(5,2),
            ilo_dim2_enterprise_policy_score    NUMERIC(5,2),
            ilo_dim3_social_protection_score    NUMERIC(5,2),
            ilo_dim4_active_labour_score        NUMERIC(5,2),
            ilo_dim5_community_score            NUMERIC(5,2),
            ilo_jt_composite_score              NUMERIC(5,2),
            ilo_jt_classification               TEXT,
            -- ESRS Social (scores 0-100)
            esrs_s1_own_workforce_score         NUMERIC(5,2),
            esrs_s2_supply_chain_score          NUMERIC(5,2),
            esrs_s3_affected_communities_score  NUMERIC(5,2),
            esrs_s4_consumers_users_score       NUMERIC(5,2),
            esrs_social_composite_score         NUMERIC(5,2),
            -- SEC Human Capital (Reg S-K Item 101c)
            sec_item101c_total_employees        INTEGER,
            sec_item101c_turnover_pct           NUMERIC(6,2),
            sec_item101c_union_pct              NUMERIC(6,2),
            sec_item101c_training_hrs_pa        NUMERIC(8,1),
            sec_hc_disclosure_quality           TEXT,
            -- Living Wage (Anker Methodology)
            living_wage_gap_pct                 NUMERIC(6,2),
            median_wage_to_living_wage_ratio    NUMERIC(6,3),
            living_wage_countries_covered       INTEGER,
            anker_benchmark_usd_month           NUMERIC(10,2),
            -- Worker Displacement
            automation_risk_high_pct            NUMERIC(6,2),
            transition_displacement_pct         NUMERIC(6,2),
            reskilling_investment_usd_pa        NUMERIC(12,2),
            displacement_timeline_yrs           NUMERIC(4,1),
            just_transition_fund_usd            NUMERIC(15,2),
            -- JT Finance (CBI — 8 criteria)
            cbi_jt_criteria_met                 INTEGER,
            jt_finance_eligible                 BOOLEAN,
            -- Overall
            overall_jt_score                    NUMERIC(5,2),
            risk_rating                         TEXT,
            key_gaps                            JSONB,
            recommendations                     JSONB,
            -- Cross-framework
            csrd_s_topics_material              JSONB,
            ungp_pillar_ii_aligned              BOOLEAN,
            oecd_rbc_aligned                    BOOLEAN,
            -- Meta
            notes                               TEXT,
            created_at                          TIMESTAMPTZ DEFAULT NOW(),
            updated_at                          TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS just_transition_stakeholder_impacts (
            id                               TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            assessment_id                    TEXT NOT NULL,
            stakeholder_type                 TEXT NOT NULL,
            stakeholder_group                TEXT,
            affected_count                   INTEGER,
            geography                        TEXT,
            -- Impact
            impact_severity                  TEXT,
            impact_type                      TEXT,
            impact_timeline                  TEXT,
            impact_description               TEXT,
            -- Mitigation
            mitigation_measures              JSONB,
            mitigation_effectiveness_pct     NUMERIC(5,2),
            residual_impact_score            NUMERIC(5,2),
            monitoring_mechanism             TEXT,
            -- Engagement
            stakeholder_engagement_done      BOOLEAN,
            engagement_quality               TEXT,
            grievance_mechanism_available    BOOLEAN,
            grievance_cases_open             INTEGER,
            -- ESRS linkage
            esrs_standard                    TEXT,
            material_topic                   TEXT,
            -- SBTi / ILO linkage
            sbti_flag_sector                 BOOLEAN,
            ilo_indicator_ref                TEXT,
            created_at                       TIMESTAMPTZ DEFAULT NOW()
        )
    """)


def downgrade():
    op.execute("DROP TABLE IF EXISTS just_transition_stakeholder_impacts")
    op.execute("DROP TABLE IF EXISTS just_transition_assessments")
    op.execute("DROP TABLE IF EXISTS carbon_credit_registry_records")
    op.execute("DROP TABLE IF EXISTS carbon_markets_intel_assessments")
    op.execute("DROP TABLE IF EXISTS prudential_climate_capital_overlays")
    op.execute("DROP TABLE IF EXISTS prudential_climate_risk_assessments")
    op.execute("DROP TABLE IF EXISTS biodiversity_ecosystem_services")
    op.execute("DROP TABLE IF EXISTS biodiversity_finance_v2_assessments")
