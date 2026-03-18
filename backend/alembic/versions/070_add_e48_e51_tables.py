"""Add E48-E51 tables: Shipping Maritime, Aviation Climate, Commercial RE, Infrastructure Finance

Revision ID: 070_add_e48_e51_tables
Revises: 069_add_e44_e47_tables
Create Date: 2026-03-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '070'
down_revision = '069'
branch_labels = None
depends_on = None


def upgrade():
    # ── E48: Shipping & Maritime Decarbonisation ────────────────────────────────
    # IMO GHG Strategy 2023 · CII A-E · EEXI · Poseidon Principles
    # FuelEU Maritime · Sea Cargo Charter · EU ETS Shipping (2024)
    op.execute("""
        CREATE TABLE IF NOT EXISTS shipping_vessel_assessments (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            vessel_name                 TEXT,
            imo_number                  TEXT,
            vessel_type                 TEXT,
            gross_tonnage               NUMERIC(12,2),
            deadweight_tonnage          NUMERIC(12,2),
            built_year                  INTEGER,
            flag_state                  TEXT,
            assessment_year             INTEGER,
            -- CII Annual Rating
            cii_attained                NUMERIC(8,4),
            cii_required                NUMERIC(8,4),
            cii_rating                  TEXT,
            cii_reduction_target_pct    NUMERIC(6,2),
            cii_stranding_year          INTEGER,
            -- EEXI Technical Efficiency
            eexi_attained               NUMERIC(8,4),
            eexi_required               NUMERIC(8,4),
            eexi_compliant              BOOLEAN,
            epl_applied                 BOOLEAN,
            epl_power_limit_kw          NUMERIC(10,2),
            -- Poseidon Principles
            pp_alignment_score          NUMERIC(8,4),
            pp_climate_score            NUMERIC(8,4),
            pp_required_trajectory      NUMERIC(8,4),
            pp_reporting_year           INTEGER,
            -- FuelEU Maritime
            fueleu_ghg_intensity_wtw    NUMERIC(10,4),
            fueleu_target_2025          NUMERIC(10,4),
            fueleu_target_2030          NUMERIC(10,4),
            fueleu_target_2050          NUMERIC(10,4),
            fueleu_penalty_eur          NUMERIC(15,2),
            fueleu_compliant_2025       BOOLEAN,
            -- Sea Cargo Charter
            scc_aer_attained            NUMERIC(8,4),
            scc_aer_required            NUMERIC(8,4),
            scc_aligned                 BOOLEAN,
            -- EU ETS Shipping
            ets_obligation_allowances   NUMERIC(12,2),
            ets_free_allocation         NUMERIC(12,2),
            ets_surrender_gap           NUMERIC(12,2),
            ets_surrender_cost_eur      NUMERIC(15,2),
            -- Alternative Fuels
            current_fuel_type           TEXT,
            alternative_fuel_readiness  TEXT,
            lcv_current_mjt             NUMERIC(8,2),
            lcv_alternative_mjt         NUMERIC(8,2),
            fuel_switch_capex_usd       NUMERIC(15,2),
            fuel_switch_payback_yrs     NUMERIC(6,2),
            -- Notes
            notes                       TEXT,
            created_at                  TIMESTAMPTZ DEFAULT NOW(),
            updated_at                  TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS shipping_fleet_portfolios (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            portfolio_entity_id         TEXT NOT NULL,
            portfolio_name              TEXT,
            assessment_date             DATE,
            total_vessels               INTEGER,
            total_dwt                   NUMERIC(15,2),
            -- Fleet CII Distribution
            cii_a_count                 INTEGER,
            cii_b_count                 INTEGER,
            cii_c_count                 INTEGER,
            cii_d_count                 INTEGER,
            cii_e_count                 INTEGER,
            fleet_avg_cii_rating        TEXT,
            -- Portfolio Alignment
            pp_portfolio_alignment_score NUMERIC(8,4),
            pp_aligned_pct              NUMERIC(6,2),
            -- FuelEU Portfolio
            fueleu_fleet_avg_ghg        NUMERIC(10,4),
            fueleu_total_penalty_eur    NUMERIC(18,2),
            fueleu_compliant_vessels_pct NUMERIC(6,2),
            -- EU ETS Portfolio
            ets_total_obligation        NUMERIC(15,2),
            ets_total_surrender_gap     NUMERIC(15,2),
            -- Transition Plan
            fleet_renewal_plan          JSONB,
            alt_fuel_investment_usd     NUMERIC(18,2),
            stranding_risk_summary      JSONB,
            created_at                  TIMESTAMPTZ DEFAULT NOW(),
            updated_at                  TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # ── E49: Aviation Climate Risk ───────────────────────────────────────────────
    # CORSIA Phase 2 · SAF Blending Mandates (ReFuelEU/IRA 45Z)
    # EU ETS Aviation · IATA Net Zero 2050 · Aircraft Asset Stranding
    op.execute("""
        CREATE TABLE IF NOT EXISTS aviation_operator_assessments (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            operator_name               TEXT,
            icao_designator             TEXT,
            operator_type               TEXT,
            assessment_year             INTEGER,
            -- CORSIA Phase 2
            corsia_phase                TEXT,
            corsia_eligible             BOOLEAN,
            corsia_baseline_tco2        NUMERIC(15,2),
            corsia_actual_tco2          NUMERIC(15,2),
            corsia_growth_factor        NUMERIC(8,6),
            corsia_offsetting_obligation_tco2 NUMERIC(15,2),
            corsia_offset_cost_usd      NUMERIC(15,2),
            corsia_eligible_units_used  JSONB,
            -- SAF Blending
            saf_blend_pct_current       NUMERIC(6,3),
            saf_blend_mandate_2025      NUMERIC(6,3),
            saf_blend_mandate_2030      NUMERIC(6,3),
            saf_blend_mandate_2050      NUMERIC(6,3),
            saf_compliance_gap_pct      NUMERIC(6,3),
            saf_cost_premium_usd_tonne  NUMERIC(8,2),
            saf_total_compliance_cost_usd NUMERIC(15,2),
            ira_45z_credit_eligible     BOOLEAN,
            ira_45z_credit_usd_per_gge  NUMERIC(6,2),
            -- EU ETS Aviation
            ets_aviation_allowances_free NUMERIC(12,2),
            ets_aviation_obligation      NUMERIC(12,2),
            ets_aviation_surrender_gap   NUMERIC(12,2),
            ets_aviation_cost_eur        NUMERIC(15,2),
            -- IATA NZC Pathway
            iata_nzc_efficiency_pct      NUMERIC(6,2),
            iata_nzc_saf_pct             NUMERIC(6,2),
            iata_nzc_carbon_removal_pct  NUMERIC(6,2),
            iata_nzc_offset_pct          NUMERIC(6,2),
            iata_nzc_alignment_score     NUMERIC(5,2),
            -- Aircraft Stranding
            fleet_avg_age_yrs            NUMERIC(5,1),
            high_emission_aircraft_pct   NUMERIC(6,2),
            stranded_asset_risk_usd      NUMERIC(15,2),
            stranding_year_median        INTEGER,
            -- Notes
            notes                        TEXT,
            created_at                   TIMESTAMPTZ DEFAULT NOW(),
            updated_at                   TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS aviation_aircraft_profiles (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            assessment_id               TEXT NOT NULL,
            aircraft_type               TEXT NOT NULL,
            aircraft_count              INTEGER,
            avg_age_yrs                 NUMERIC(5,1),
            fuel_burn_kg_per_hr         NUMERIC(8,2),
            co2_intensity_gco2_per_pkm  NUMERIC(8,4),
            range_km                    NUMERIC(8,1),
            -- Stranding analysis
            stranding_year              INTEGER,
            remaining_useful_life_yrs   NUMERIC(5,1),
            book_value_usd              NUMERIC(15,2),
            climate_adjusted_value_usd  NUMERIC(15,2),
            stranded_value_usd          NUMERIC(15,2),
            -- SAF compatibility
            saf_compatible              BOOLEAN,
            saf_blend_max_pct           NUMERIC(6,2),
            hydrogen_ready              BOOLEAN,
            electric_hybrid_candidate   BOOLEAN,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # ── E50: Commercial Real Estate Net Zero ─────────────────────────────────────
    # CRREM 2.0 · EPC/EPBD 2024 · GRESB Real Estate (2024)
    # REFI Protocol · NABERS · Green Lease · Retrofit NPV
    op.execute("""
        CREATE TABLE IF NOT EXISTS commercial_re_assessments (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            asset_name                  TEXT,
            asset_type                  TEXT,
            gross_floor_area_m2         NUMERIC(12,2),
            location_country            TEXT,
            location_city               TEXT,
            construction_year           INTEGER,
            assessment_date             DATE,
            -- CRREM 2.0
            crrem_asset_type            TEXT,
            crrem_energy_intensity_kwh_m2 NUMERIC(10,2),
            crrem_co2_intensity_kgco2_m2 NUMERIC(10,4),
            crrem_pathway_2030          NUMERIC(10,4),
            crrem_pathway_2050          NUMERIC(10,4),
            crrem_stranding_year        INTEGER,
            crrem_stranding_risk        TEXT,
            crrem_overconsumption_gap   NUMERIC(10,4),
            -- EPC / EPBD 2024
            epc_rating_current          TEXT,
            epc_rating_target_2030      TEXT,
            epc_primary_energy_kwh_m2   NUMERIC(10,2),
            epbd_renovation_required    BOOLEAN,
            epbd_minimum_threshold      TEXT,
            epbd_compliance_deadline    TEXT,
            -- GRESB Real Estate
            gresb_score                 NUMERIC(5,1),
            gresb_management_score      NUMERIC(5,1),
            gresb_performance_score     NUMERIC(5,1),
            gresb_rating                TEXT,
            gresb_peer_group            TEXT,
            gresb_data_coverage_pct     NUMERIC(6,2),
            -- REFI Protocol
            refi_physical_risk_score    NUMERIC(5,2),
            refi_transition_risk_score  NUMERIC(5,2),
            refi_composite_score        NUMERIC(5,2),
            refi_risk_tier              TEXT,
            -- NABERS
            nabers_energy_stars         NUMERIC(3,1),
            nabers_water_stars          NUMERIC(3,1),
            nabers_indoor_stars         NUMERIC(3,1),
            nabers_waste_stars          NUMERIC(3,1),
            -- Green Lease
            green_lease_present         BOOLEAN,
            green_lease_clauses         JSONB,
            green_lease_score           NUMERIC(5,2),
            -- Financial
            asset_value_usd             NUMERIC(18,2),
            annual_noi_usd              NUMERIC(15,2),
            green_premium_pct           NUMERIC(6,2),
            brown_discount_pct          NUMERIC(6,2),
            -- Notes
            notes                       TEXT,
            created_at                  TIMESTAMPTZ DEFAULT NOW(),
            updated_at                  TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS commercial_re_retrofit_plans (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            assessment_id               TEXT NOT NULL,
            retrofit_measure            TEXT NOT NULL,
            measure_category            TEXT,
            capex_usd                   NUMERIC(12,2),
            annual_energy_saving_kwh    NUMERIC(12,2),
            annual_co2_saving_kgco2     NUMERIC(12,2),
            annual_cost_saving_usd      NUMERIC(12,2),
            simple_payback_yrs          NUMERIC(6,2),
            npv_usd                     NUMERIC(12,2),
            irr_pct                     NUMERIC(6,2),
            epc_improvement             TEXT,
            crrem_year_improvement      INTEGER,
            implementation_priority     TEXT,
            implementation_timeline     TEXT,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # ── E51: Infrastructure Climate Finance ──────────────────────────────────────
    # Equator Principles IV (2020) · IFC Performance Standards 1-8
    # OECD Common Approaches 2022 · Paris Alignment for MDBs/DFIs
    # Blended Finance · DSCR Climate Stress · SDG Bond Framework
    op.execute("""
        CREATE TABLE IF NOT EXISTS infrastructure_project_assessments (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            project_name                TEXT,
            project_type                TEXT,
            sector                      TEXT,
            country                     TEXT,
            total_project_cost_usd      NUMERIC(18,2),
            debt_amount_usd             NUMERIC(18,2),
            equity_amount_usd           NUMERIC(15,2),
            construction_start          DATE,
            operation_start             DATE,
            project_lifetime_yrs        INTEGER,
            assessment_date             DATE,
            -- Equator Principles IV
            ep_category                 TEXT,
            ep_requirements_score       NUMERIC(5,2),
            ep_esap_required            BOOLEAN,
            ep_monitoring_required      BOOLEAN,
            ep_grievance_mechanism      BOOLEAN,
            ep_independent_review       BOOLEAN,
            ep_10_principles_scores     JSONB,
            ep_overall_compliant        BOOLEAN,
            -- IFC Performance Standards
            ifc_ps1_score               NUMERIC(5,2),
            ifc_ps2_score               NUMERIC(5,2),
            ifc_ps3_score               NUMERIC(5,2),
            ifc_ps4_score               NUMERIC(5,2),
            ifc_ps5_score               NUMERIC(5,2),
            ifc_ps6_score               NUMERIC(5,2),
            ifc_ps7_score               NUMERIC(5,2),
            ifc_ps8_score               NUMERIC(5,2),
            ifc_composite_score         NUMERIC(5,2),
            ifc_overall_compliant       BOOLEAN,
            -- OECD Common Approaches
            oecd_tier                   TEXT,
            oecd_env_screening          TEXT,
            oecd_env_review_required    BOOLEAN,
            -- Paris Alignment
            pa_mitigation_aligned       BOOLEAN,
            pa_adaptation_aligned       BOOLEAN,
            pa_climate_governance       BOOLEAN,
            pa_overall_aligned          BOOLEAN,
            pa_alignment_score          NUMERIC(5,2),
            pa_ghg_reduction_tco2_pa    NUMERIC(15,2),
            -- DSCR Climate Stress
            dscr_baseline               NUMERIC(6,3),
            dscr_physical_stress        NUMERIC(6,3),
            dscr_transition_stress      NUMERIC(6,3),
            dscr_combined_stress        NUMERIC(6,3),
            dscr_breaches_covenant      BOOLEAN,
            -- Climate Label
            cbi_certified               BOOLEAN,
            icma_gbf_aligned            BOOLEAN,
            sdg_label                   TEXT,
            -- Notes
            notes                       TEXT,
            created_at                  TIMESTAMPTZ DEFAULT NOW(),
            updated_at                  TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS infrastructure_blended_finance (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            assessment_id               TEXT NOT NULL,
            structure_type              TEXT NOT NULL,
            -- Tranche structure
            senior_debt_usd             NUMERIC(15,2),
            senior_debt_rate_pct        NUMERIC(6,3),
            mezzanine_debt_usd          NUMERIC(15,2),
            mezzanine_rate_pct          NUMERIC(6,3),
            first_loss_tranche_usd      NUMERIC(15,2),
            first_loss_provider         TEXT,
            equity_usd                  NUMERIC(15,2),
            grant_component_usd         NUMERIC(15,2),
            -- MDB/DFI participation
            mdb_guarantee_usd           NUMERIC(15,2),
            mdb_name                    TEXT,
            concessional_debt_usd       NUMERIC(15,2),
            concessional_rate_pct       NUMERIC(6,3),
            -- Additionality
            additionality_type          TEXT,
            crowding_in_ratio           NUMERIC(6,3),
            private_finance_mobilised   NUMERIC(15,2),
            -- Blended finance metrics
            oecd_additionality_score    NUMERIC(5,2),
            blended_irr_pct             NUMERIC(6,3),
            private_sector_irr_pct      NUMERIC(6,3),
            -- SDG alignment
            sdg_targets                 JSONB,
            impact_metrics              JSONB,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        )
    """)


def downgrade():
    op.execute("DROP TABLE IF EXISTS infrastructure_blended_finance")
    op.execute("DROP TABLE IF EXISTS infrastructure_project_assessments")
    op.execute("DROP TABLE IF EXISTS commercial_re_retrofit_plans")
    op.execute("DROP TABLE IF EXISTS commercial_re_assessments")
    op.execute("DROP TABLE IF EXISTS aviation_aircraft_profiles")
    op.execute("DROP TABLE IF EXISTS aviation_operator_assessments")
    op.execute("DROP TABLE IF EXISTS shipping_fleet_portfolios")
    op.execute("DROP TABLE IF EXISTS shipping_vessel_assessments")
