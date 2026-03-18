"""Add E52-E55 tables: Nature-Based Solutions, Water Risk, Food System, Circular Economy

Revision ID: 071_add_e52_e55_tables
Revises: 070_add_e48_e51_tables
Create Date: 2026-03-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '071'
down_revision = '070'
branch_labels = None
depends_on = None


def upgrade():
    # ── E52: Nature-Based Solutions & Carbon Sequestration ───────────────────────
    # IUCN Global Standard v2.0 · REDD+ VCS VM0007 · Blue Carbon VM0033/VM0024
    # Soil Carbon IPCC Tier 1-3 · ARR afforestation · AFOLU net GHG
    op.execute("""
        CREATE TABLE IF NOT EXISTS nbs_project_assessments (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            project_name                TEXT,
            project_type                TEXT,
            country_code                TEXT,
            area_ha                     NUMERIC(15,2),
            assessment_date             DATE,
            -- IUCN Global Standard v2.0
            iucn_gs_criteria_met        INTEGER,
            iucn_gs_total_criteria      INTEGER,
            iucn_gs_score               NUMERIC(5,2),
            iucn_gs_standard_met        BOOLEAN,
            iucn_gs_safeguards_score    NUMERIC(5,2),
            -- REDD+
            redd_reference_level_tco2_pa NUMERIC(15,2),
            redd_actual_emissions_tco2_pa NUMERIC(15,2),
            redd_avoided_deforestation_tco2_pa NUMERIC(15,2),
            redd_leakage_belt_pct       NUMERIC(6,2),
            redd_buffer_pool_pct        NUMERIC(6,2),
            redd_net_credits_tco2_pa    NUMERIC(15,2),
            redd_methodology            TEXT,
            redd_jurisdictional         BOOLEAN,
            -- Blue Carbon
            blue_carbon_type            TEXT,
            blue_carbon_area_ha         NUMERIC(12,2),
            blue_carbon_seq_rate_tco2_ha_pa NUMERIC(8,4),
            blue_carbon_total_seq_tco2_pa NUMERIC(15,2),
            blue_carbon_permanence_risk TEXT,
            tidal_hydrology_restored    BOOLEAN,
            -- Soil Carbon
            soil_carbon_ipcc_tier       INTEGER,
            soil_carbon_delta_tco2_ha_pa NUMERIC(8,4),
            soil_carbon_total_tco2_pa   NUMERIC(15,2),
            soil_carbon_permanence_risk TEXT,
            soil_carbon_measurement_uncertainty_pct NUMERIC(6,2),
            -- ARR
            arr_above_ground_tco2_pa    NUMERIC(15,2),
            arr_below_ground_tco2_pa    NUMERIC(15,2),
            arr_soil_carbon_tco2_pa     NUMERIC(15,2),
            arr_total_tco2_pa           NUMERIC(15,2),
            arr_native_species          BOOLEAN,
            -- AFOLU net balance
            afolu_sequestration_tco2_pa NUMERIC(15,2),
            afolu_n2o_emissions_tco2e_pa NUMERIC(12,2),
            afolu_ch4_emissions_tco2e_pa NUMERIC(12,2),
            afolu_net_balance_tco2e_pa  NUMERIC(15,2),
            -- Co-benefits
            biodiversity_cobenefit_score NUMERIC(5,2),
            water_cobenefit_score       NUMERIC(5,2),
            livelihoods_cobenefit_score NUMERIC(5,2),
            cobenefit_premium_pct       NUMERIC(6,2),
            -- Credit quality
            icvcm_ccp_compatible        BOOLEAN,
            overall_credit_quality_score NUMERIC(5,2),
            estimated_credit_price_usd  NUMERIC(8,2),
            -- Notes
            notes                       TEXT,
            created_at                  TIMESTAMPTZ DEFAULT NOW(),
            updated_at                  TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS nbs_sequestration_timeseries (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            assessment_id               TEXT NOT NULL,
            year                        INTEGER NOT NULL,
            sequestration_tco2          NUMERIC(15,2),
            emissions_tco2e             NUMERIC(12,2),
            net_balance_tco2e           NUMERIC(15,2),
            cumulative_tco2e            NUMERIC(15,2),
            buffer_pool_contribution    NUMERIC(12,2),
            credits_issued_tco2         NUMERIC(12,2),
            reversal_risk_flag          BOOLEAN,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # ── E53: Water Risk & Security ────────────────────────────────────────────────
    # WRI Aqueduct 4.0 · CDP Water Security A-List · CSRD ESRS E3
    # TNFD Water Dependency · CEO Water Mandate · UN SDG 6
    op.execute("""
        CREATE TABLE IF NOT EXISTS water_risk_assessments (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            facility_name               TEXT,
            latitude                    NUMERIC(10,6),
            longitude                   NUMERIC(10,6),
            country_code                TEXT,
            basin_name                  TEXT,
            sector                      TEXT,
            assessment_date             DATE,
            -- WRI Aqueduct 4.0
            aqueduct_water_stress       NUMERIC(5,2),
            aqueduct_water_depletion    NUMERIC(5,2),
            aqueduct_interannual_variability NUMERIC(5,2),
            aqueduct_seasonal_variability NUMERIC(5,2),
            aqueduct_groundwater_decline NUMERIC(5,2),
            aqueduct_coastal_eutrophication NUMERIC(5,2),
            aqueduct_untreated_wastewater NUMERIC(5,2),
            aqueduct_overall_score      NUMERIC(5,2),
            aqueduct_risk_tier          TEXT,
            -- CDP Water Security
            cdp_water_score             TEXT,
            cdp_a_list_eligible         BOOLEAN,
            cdp_governance_score        NUMERIC(5,2),
            cdp_risk_quantification_score NUMERIC(5,2),
            cdp_target_score            NUMERIC(5,2),
            -- ESRS E3
            esrs_e3_withdrawal_m3_pa    NUMERIC(15,2),
            esrs_e3_consumption_m3_pa   NUMERIC(15,2),
            esrs_e3_discharge_m3_pa     NUMERIC(15,2),
            esrs_e3_recycled_pct        NUMERIC(6,2),
            esrs_e3_water_intensive     BOOLEAN,
            esrs_e3_disclosure_score    NUMERIC(5,2),
            -- TNFD water dependency
            tnfd_water_dependency_score NUMERIC(5,2),
            tnfd_encore_water_services  JSONB,
            -- Financial impact
            revenue_at_risk_pct         NUMERIC(6,2),
            compliance_cost_usd_pa      NUMERIC(12,2),
            capex_resilience_usd        NUMERIC(12,2),
            -- Physical risk (RCP scenarios)
            physical_risk_rcp26         TEXT,
            physical_risk_rcp45         TEXT,
            physical_risk_rcp85         TEXT,
            -- Overall
            materiality_rating          TEXT,
            notes                       TEXT,
            created_at                  TIMESTAMPTZ DEFAULT NOW(),
            updated_at                  TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS water_footprint_calculations (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            assessment_id               TEXT NOT NULL,
            product_or_process          TEXT NOT NULL,
            blue_water_m3_per_unit      NUMERIC(12,4),
            green_water_m3_per_unit     NUMERIC(12,4),
            grey_water_m3_per_unit      NUMERIC(12,4),
            total_footprint_m3_per_unit NUMERIC(12,4),
            annual_volume_units         NUMERIC(15,2),
            total_blue_m3_pa            NUMERIC(15,2),
            total_green_m3_pa           NUMERIC(15,2),
            total_grey_m3_pa            NUMERIC(15,2),
            hotspot_flag                BOOLEAN,
            methodology                 TEXT,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # ── E54: Food System & Land Use Finance ──────────────────────────────────────
    # SBTi FLAG (Forest Land Agriculture) · FAO crop yield · TNFD Food LEAP
    # EUDR deforestation-free · ICTI · FOLU · Agricultural financed emissions
    op.execute("""
        CREATE TABLE IF NOT EXISTS food_system_assessments (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            entity_name                 TEXT,
            sector                      TEXT,
            assessment_date             DATE,
            reporting_year              INTEGER,
            -- SBTi FLAG
            flag_sector                 TEXT,
            flag_land_mitigation_tco2_pa NUMERIC(15,2),
            flag_removal_tco2_pa        NUMERIC(15,2),
            flag_reduction_tco2_pa      NUMERIC(15,2),
            flag_target_year            INTEGER,
            flag_base_year              INTEGER,
            flag_target_pct             NUMERIC(6,2),
            flag_target_met             BOOLEAN,
            flag_science_based          BOOLEAN,
            -- FAO crop yield impact
            primary_crop                TEXT,
            growing_region              TEXT,
            baseline_yield_t_ha         NUMERIC(8,3),
            yield_impact_rcp26_pct      NUMERIC(6,2),
            yield_impact_rcp45_pct      NUMERIC(6,2),
            yield_impact_rcp85_pct      NUMERIC(6,2),
            adaptation_yield_gain_pct   NUMERIC(6,2),
            revenue_at_risk_usd_pa      NUMERIC(15,2),
            -- TNFD Food LEAP
            tnfd_leap_score             NUMERIC(5,2),
            nature_dependency_score     NUMERIC(5,2),
            nature_impact_score         NUMERIC(5,2),
            tnfd_water_dependency       NUMERIC(5,2),
            tnfd_biodiversity_risk      TEXT,
            -- EUDR deforestation-free
            eudr_commodity_screened     TEXT,
            eudr_country_risk_tier      TEXT,
            eudr_deforestation_free     BOOLEAN,
            eudr_cutoff_date_compliant  BOOLEAN,
            eudr_geolocation_verified   BOOLEAN,
            -- ICTI
            icti_scope                  TEXT,
            icti_score                  NUMERIC(5,2),
            -- Agricultural financed emissions
            ag_scope1_tco2e_pa          NUMERIC(15,2),
            ag_scope2_tco2e_pa          NUMERIC(12,2),
            ag_scope3_cat1_tco2e_pa     NUMERIC(15,2),
            ag_total_emissions_tco2e_pa NUMERIC(15,2),
            -- LDN
            ldn_status                  TEXT,
            notes                       TEXT,
            created_at                  TIMESTAMPTZ DEFAULT NOW(),
            updated_at                  TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS flag_target_settings (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            assessment_id               TEXT NOT NULL,
            target_type                 TEXT NOT NULL,
            sector                      TEXT,
            commodity                   TEXT,
            base_year                   INTEGER,
            target_year                 INTEGER,
            base_emissions_tco2e        NUMERIC(15,2),
            target_emissions_tco2e      NUMERIC(15,2),
            required_reduction_pct      NUMERIC(6,2),
            current_trajectory_pct      NUMERIC(6,2),
            gap_pct                     NUMERIC(6,2),
            interventions               JSONB,
            sbti_approved               BOOLEAN,
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # ── E55: Circular Economy Finance ────────────────────────────────────────────
    # CSRD ESRS E5 · Ellen MacArthur Foundation MCI · WBCSD CTI
    # EU CEAP 2020 · EPR Schemes · CRM Act 2023 · ISO 14044 LCA
    op.execute("""
        CREATE TABLE IF NOT EXISTS circular_economy_assessments (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            entity_id                   TEXT NOT NULL,
            entity_name                 TEXT,
            sector                      TEXT,
            assessment_date             DATE,
            reporting_year              INTEGER,
            -- ESRS E5
            esrs_e5_resource_inflows_t  NUMERIC(15,2),
            esrs_e5_recycled_inflows_pct NUMERIC(6,2),
            esrs_e5_resource_outflows_t NUMERIC(15,2),
            esrs_e5_waste_t             NUMERIC(12,2),
            esrs_e5_recycled_outflows_pct NUMERIC(6,2),
            esrs_e5_crm_dependency      BOOLEAN,
            esrs_e5_crm_list            JSONB,
            esrs_e5_disclosure_score    NUMERIC(5,2),
            esrs_e5_target_set          BOOLEAN,
            -- EMF Material Circularity Indicator
            mci_recycled_input_fraction NUMERIC(6,4),
            mci_waste_recovery_fraction NUMERIC(6,4),
            mci_utility_factor          NUMERIC(6,4),
            mci_score                   NUMERIC(6,4),
            mci_benchmark               NUMERIC(6,4),
            mci_gap_to_benchmark        NUMERIC(6,4),
            -- WBCSD CTI
            cti_circular_product_design NUMERIC(5,2),
            cti_waste_recovery          NUMERIC(5,2),
            cti_recycled_content        NUMERIC(5,2),
            cti_product_lifetime        NUMERIC(5,2),
            cti_composite_score         NUMERIC(5,2),
            cti_tier                    TEXT,
            -- EPR Compliance
            epr_packaging_liable        BOOLEAN,
            epr_packaging_cost_eur_pa   NUMERIC(12,2),
            epr_ewaste_liable           BOOLEAN,
            epr_ewaste_cost_eur_pa      NUMERIC(12,2),
            epr_battery_liable          BOOLEAN,
            epr_battery_cost_eur_pa     NUMERIC(12,2),
            epr_total_cost_eur_pa       NUMERIC(12,2),
            -- CRM (EU CRM Act 2023)
            crm_dependency_score        NUMERIC(5,2),
            crm_supply_risk_score       NUMERIC(5,2),
            crm_recycled_content_pct    NUMERIC(6,2),
            crm_2030_target_gap         NUMERIC(6,2),
            -- LCA
            lca_cradle_to_gate_kgco2e   NUMERIC(12,4),
            lca_cradle_to_cradle_kgco2e NUMERIC(12,4),
            lca_circularity_benefit_pct NUMERIC(6,2),
            -- Overall
            overall_circularity_score   NUMERIC(5,2),
            risk_rating                 TEXT,
            investment_needed_usd       NUMERIC(15,2),
            notes                       TEXT,
            created_at                  TIMESTAMPTZ DEFAULT NOW(),
            updated_at                  TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS material_flow_analyses (
            id                          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            assessment_id               TEXT NOT NULL,
            material_name               TEXT NOT NULL,
            material_category           TEXT,
            crm_flag                    BOOLEAN,
            -- Inflows
            primary_input_t_pa          NUMERIC(12,2),
            recycled_input_t_pa         NUMERIC(12,2),
            bio_based_input_t_pa        NUMERIC(12,2),
            total_inflow_t_pa           NUMERIC(12,2),
            recycled_input_pct          NUMERIC(6,2),
            -- Outflows
            product_output_t_pa         NUMERIC(12,2),
            reused_output_t_pa          NUMERIC(12,2),
            recycled_output_t_pa        NUMERIC(12,2),
            waste_disposed_t_pa         NUMERIC(12,2),
            recovery_rate_pct           NUMERIC(6,2),
            -- Supply risk
            hhi_supply_concentration    NUMERIC(6,2),
            top_supplier_country        TEXT,
            supply_risk_score           NUMERIC(5,2),
            -- Decarbonisation
            embodied_carbon_kgco2e_t    NUMERIC(10,4),
            recycled_carbon_saving_pct  NUMERIC(6,2),
            -- EU 2030 targets
            eu_2030_extraction_target_pct NUMERIC(6,2),
            eu_2030_processing_target_pct NUMERIC(6,2),
            eu_2030_recycling_target_pct NUMERIC(6,2),
            created_at                  TIMESTAMPTZ DEFAULT NOW()
        )
    """)


def downgrade():
    op.execute("DROP TABLE IF EXISTS material_flow_analyses")
    op.execute("DROP TABLE IF EXISTS circular_economy_assessments")
    op.execute("DROP TABLE IF EXISTS flag_target_settings")
    op.execute("DROP TABLE IF EXISTS food_system_assessments")
    op.execute("DROP TABLE IF EXISTS water_footprint_calculations")
    op.execute("DROP TABLE IF EXISTS water_risk_assessments")
    op.execute("DROP TABLE IF EXISTS nbs_sequestration_timeseries")
    op.execute("DROP TABLE IF EXISTS nbs_project_assessments")
