"""Add calculation_parameters governance table + sector tables for agriculture/mining/insurance

Revision ID: 027_add_parameter_governance
Revises: 026_add_audit_log
Create Date: 2026-03-04

Tables created:
  calculation_parameters      — versioned, org-scoped parameter store with approval workflow
  parameter_change_requests   — four-eyes approval queue for parameter changes
  agriculture_entities        — farm / agribusiness entities
  agriculture_risk_assessments — crop yield, EUDR, soil carbon, water stress per entity
  mining_entities             — mine site entities
  mining_risk_assessments     — tailings, water intensity, closure cost, critical minerals
  insurance_climate_entities  — insurer entities
  insurance_climate_assessments — CAT risk, Solvency II provisions, reserve adequacy
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "027_add_parameter_governance"
down_revision = "026_add_audit_log"
branch_labels = None
depends_on = None


def upgrade():

    # ── calculation_parameters ─────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS calculation_parameters (
            id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id           UUID REFERENCES organisations(id) ON DELETE CASCADE,
                -- NULL = platform-wide default visible to all orgs
            parameter_name   VARCHAR(200) NOT NULL,
            category         VARCHAR(100) NOT NULL,
                -- carbon_price | discount_rate | emission_factor | scenario_variable |
                --  credit_risk | physical_risk | transition_risk | regulatory_threshold
            sub_category     VARCHAR(100),
            value            NUMERIC(24, 8) NOT NULL,
            value_type       VARCHAR(20)  DEFAULT 'point',  -- point | lower_bound | upper_bound | p50
            unit             VARCHAR(50),
            effective_date   DATE         NOT NULL,
            expiry_date      DATE,
            source           TEXT,
            methodology_ref  TEXT,
            notes            TEXT,
            -- Governance
            status           VARCHAR(20)  NOT NULL DEFAULT 'active',
                -- active | superseded | under_review | rejected
            version          INTEGER      NOT NULL DEFAULT 1,
            approved_by      VARCHAR(100),  -- user_id of approver
            approved_at      TIMESTAMPTZ,
            proposed_by      VARCHAR(100),  -- user_id of proposer
            proposed_at      TIMESTAMPTZ    DEFAULT now(),
            is_platform_default BOOLEAN    DEFAULT false,
            created_at       TIMESTAMPTZ    NOT NULL DEFAULT now()
        );
    """)

    # Add missing columns to calculation_parameters if it pre-existed with a different schema
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='calculation_parameters' AND column_name='status') THEN
                ALTER TABLE calculation_parameters ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'active';
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='calculation_parameters' AND column_name='version') THEN
                ALTER TABLE calculation_parameters ADD COLUMN version INTEGER NOT NULL DEFAULT 1;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='calculation_parameters' AND column_name='value_type') THEN
                ALTER TABLE calculation_parameters ADD COLUMN value_type VARCHAR(20) DEFAULT 'point';
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='calculation_parameters' AND column_name='methodology_ref') THEN
                ALTER TABLE calculation_parameters ADD COLUMN methodology_ref TEXT;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='calculation_parameters' AND column_name='proposed_by') THEN
                ALTER TABLE calculation_parameters ADD COLUMN proposed_by VARCHAR(100);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='calculation_parameters' AND column_name='proposed_at') THEN
                ALTER TABLE calculation_parameters ADD COLUMN proposed_at TIMESTAMPTZ DEFAULT now();
            END IF;
        END$$;
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_calc_params_org_cat
            ON calculation_parameters (org_id, category, effective_date DESC);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_calc_params_name
            ON calculation_parameters (parameter_name, org_id, status);
    """)

    # ── parameter_change_requests (four-eyes) ─────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS parameter_change_requests (
            id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id           UUID REFERENCES organisations(id) ON DELETE CASCADE,
            parameter_id     UUID REFERENCES calculation_parameters(id) ON DELETE CASCADE,
            requested_by     VARCHAR(100) NOT NULL,
            requested_at     TIMESTAMPTZ  NOT NULL DEFAULT now(),
            old_value        NUMERIC(24, 8),
            new_value        NUMERIC(24, 8) NOT NULL,
            justification    TEXT         NOT NULL,
            supporting_docs  JSONB,
            -- Review
            status           VARCHAR(20)  NOT NULL DEFAULT 'pending',
                -- pending | approved | rejected | withdrawn
            reviewed_by      VARCHAR(100),
            reviewed_at      TIMESTAMPTZ,
            review_notes     TEXT,
            effective_date   DATE
        );
    """)

    # ── agriculture_entities ───────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS agriculture_entities (
            id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id           UUID REFERENCES organisations(id) ON DELETE SET NULL,
            entity_registry_id UUID,  -- FK to csrd_entity_registry if available
            entity_name      VARCHAR(500) NOT NULL,
            country_iso      CHAR(3)      NOT NULL,
            region           VARCHAR(200),
            farm_type        VARCHAR(100),
                -- arable | livestock | mixed | horticulture | aquaculture | forestry | agribusiness
            total_area_ha    NUMERIC(14, 2),
            primary_crop     VARCHAR(100),
            crops_grown      JSONB,          -- [{crop, area_ha, yield_t_ha}]
            annual_revenue_eur NUMERIC(18, 2),
            employee_count   INTEGER,
            organic_certified BOOLEAN DEFAULT false,
            eudr_in_scope    BOOLEAN DEFAULT false,
                -- EU Deforestation Regulation applies (soy, beef, palm oil, cocoa, coffee, wood)
            created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
        );
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_agri_entities_org
            ON agriculture_entities (org_id, country_iso);
    """)

    # ── agriculture_risk_assessments ──────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS agriculture_risk_assessments (
            id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            entity_id        UUID NOT NULL REFERENCES agriculture_entities(id) ON DELETE CASCADE,
            assessment_date  DATE NOT NULL DEFAULT CURRENT_DATE,
            scenario         VARCHAR(50) DEFAULT '2C',  -- 1.5C | 2C | 3C | BAU
            horizon_year     INTEGER DEFAULT 2050,

            -- Crop yield risk
            baseline_yield_t_ha      NUMERIC(10, 3),
            projected_yield_change_pct NUMERIC(8, 4),
                -- % change vs baseline under scenario (negative = yield loss)
            crop_failure_probability NUMERIC(6, 4),  -- annual probability 0-1
            heat_stress_days_increase INTEGER,
            precipitation_change_pct NUMERIC(8, 4),

            -- EUDR compliance (EU 2023/1115)
            eudr_status       VARCHAR(30) DEFAULT 'not_assessed',
                -- compliant | non_compliant | under_review | not_assessed
            deforestation_risk_score NUMERIC(5, 2),  -- 0-100
            eudr_due_diligence_complete BOOLEAN DEFAULT false,
            eudr_geolocation_provided   BOOLEAN DEFAULT false,
            eudr_supply_chain_traced    BOOLEAN DEFAULT false,

            -- Soil carbon
            current_soil_carbon_t_ha     NUMERIC(10, 3),
            potential_seq_t_co2_ha_yr    NUMERIC(10, 3),
            regenerative_potential_score NUMERIC(5, 2),  -- 0-100 (IPCC-aligned)

            -- Water stress (WRI Aqueduct categories)
            water_stress_level   VARCHAR(30),  -- low | medium-high | high | extremely_high | arid
            irrigation_dependency_pct NUMERIC(6, 3),
            water_cost_risk_score NUMERIC(5, 2),

            -- Financial impact
            revenue_at_risk_pct  NUMERIC(8, 4),  -- % of annual revenue at risk
            adaptation_capex_eur NUMERIC(18, 2),  -- estimated adaptation investment
            carbon_credit_potential_tco2 NUMERIC(14, 3),  -- from soil/forestry credits

            -- Methodology
            methodology_ref  TEXT DEFAULT 'IPCC AR6 WG2 Ch.5 / FAO GAEZ v4 / WRI Aqueduct 4.0 / EU 2023/1115',
            data_quality_score NUMERIC(4, 2),
            notes            TEXT,
            created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
        );
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_agri_assessments_entity
            ON agriculture_risk_assessments (entity_id, assessment_date DESC);
    """)

    # ── mining_entities ────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS mining_entities (
            id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id           UUID REFERENCES organisations(id) ON DELETE SET NULL,
            entity_registry_id UUID,
            entity_name      VARCHAR(500) NOT NULL,
            country_iso      CHAR(3)      NOT NULL,
            mine_type        VARCHAR(100),
                -- open_pit | underground | in_situ_leach | placer | surface | submarine
            primary_commodity VARCHAR(100) NOT NULL,
                -- coal | iron_ore | copper | gold | lithium | cobalt | nickel |
                --  bauxite | zinc | silver | platinum_group | uranium | other
            is_critical_mineral BOOLEAN DEFAULT false,
                -- IEA/EU critical raw materials list
            annual_production_kt NUMERIC(14, 3),
            reserve_life_years INTEGER,
            employee_count   INTEGER,
            annual_revenue_eur NUMERIC(18, 2),
            latitude         NUMERIC(10, 7),
            longitude        NUMERIC(10, 7),
            created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
        );
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_mining_entities_org
            ON mining_entities (org_id, primary_commodity);
    """)

    # ── mining_risk_assessments ────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS mining_risk_assessments (
            id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            entity_id            UUID NOT NULL REFERENCES mining_entities(id) ON DELETE CASCADE,
            assessment_date      DATE NOT NULL DEFAULT CURRENT_DATE,
            scenario             VARCHAR(50) DEFAULT '2C',
            horizon_year         INTEGER DEFAULT 2050,

            -- Tailings (GISTM — Global Industry Standard on Tailings Management)
            tailings_facility_count INTEGER DEFAULT 0,
            gistm_compliance_level VARCHAR(30),  -- non_compliant | developing | advanced | leading
            tailings_consequence_class VARCHAR(10),  -- EXTREME | VERY_HIGH | HIGH | LOW
            tailings_failure_probability NUMERIC(8, 6),  -- annual probability
            tailings_liability_eur NUMERIC(18, 2),

            -- Water intensity
            water_use_ml_per_kt   NUMERIC(12, 4),
                -- megalitres per thousand tonnes of ore processed
            water_stress_index    NUMERIC(6, 3),  -- 0-5 (WRI Aqueduct)
            water_recycling_rate  NUMERIC(6, 4),  -- 0-1
            acid_mine_drainage_risk VARCHAR(20),  -- low | medium | high | critical

            -- Stranding / closure
            stranding_scenario   VARCHAR(50),
            stranding_year       INTEGER,
            closure_cost_eur     NUMERIC(18, 2),  -- full closure + remediation cost
            closure_provision_eur NUMERIC(18, 2), -- amount provisioned on balance sheet
            provision_coverage_pct NUMERIC(6, 3), -- coverage ratio

            -- Community / Social (FPIC — Free, Prior and Informed Consent)
            fpic_status          VARCHAR(30) DEFAULT 'not_assessed',
                -- obtained | partially_obtained | not_obtained | not_required | not_assessed
            community_consent_score NUMERIC(5, 2),  -- 0-100
            modern_slavery_risk  VARCHAR(20),  -- low | medium | high

            -- Critical minerals supply chain
            supply_chain_concentration_hhi NUMERIC(8, 2),
                -- Herfindahl-Hirschman Index for supply concentration
            geopolitical_risk_score NUMERIC(5, 2),  -- 0-100
            substitutability_score  NUMERIC(5, 2),  -- 0-100 (ease of substitution)
            recycling_rate_pct      NUMERIC(6, 3),

            -- Transition demand
            ev_battery_demand_exposure NUMERIC(8, 4),  -- % revenue from EV-related demand
            renewable_energy_demand_exposure NUMERIC(8, 4),

            -- Financial impact
            stranded_value_eur   NUMERIC(18, 2),
            carbon_cost_exposure_eur NUMERIC(18, 2),  -- Scope 1+2 at modelled carbon price
            revenue_at_risk_pct  NUMERIC(8, 4),

            methodology_ref  TEXT DEFAULT 'GISTM 2020 / WRI Aqueduct 4.0 / IPCC AR6 / IEA CRM 2023',
            data_quality_score NUMERIC(4, 2),
            notes            TEXT,
            created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
        );
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_mining_assessments_entity
            ON mining_risk_assessments (entity_id, assessment_date DESC);
    """)

    # ── insurance_climate_entities ────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS insurance_climate_entities (
            id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id            UUID REFERENCES organisations(id) ON DELETE SET NULL,
            entity_registry_id UUID,
            entity_name       VARCHAR(500) NOT NULL,
            country_iso       CHAR(3)      NOT NULL,
            insurer_type      VARCHAR(50),
                -- primary | reinsurer | captive | lloyds_syndicate | composite
            lines_of_business JSONB,
                -- [{lob: "property_catastrophe", gross_premium_eur: 500000000}]
            total_gross_written_premium_eur NUMERIC(18, 2),
            total_assets_eur  NUMERIC(18, 2),
            scr_eur           NUMERIC(18, 2),  -- Solvency Capital Requirement
            mcr_eur           NUMERIC(18, 2),  -- Minimum Capital Requirement
            solvency_ratio_pct NUMERIC(8, 3),  -- own funds / SCR
            created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
        );
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_ins_entities_org
            ON insurance_climate_entities (org_id, insurer_type);
    """)

    # ── insurance_climate_assessments ────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS insurance_climate_assessments (
            id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            entity_id           UUID NOT NULL REFERENCES insurance_climate_entities(id) ON DELETE CASCADE,
            assessment_date     DATE NOT NULL DEFAULT CURRENT_DATE,
            scenario            VARCHAR(50) DEFAULT '2C',
            horizon_year        INTEGER DEFAULT 2050,

            -- CAT risk (physical underwriting)
            cat_peril           VARCHAR(50),
                -- tropical_cyclone | flood | wildfire | earthquake | hail | drought | winter_storm
            gross_loss_1_in_100_eur NUMERIC(18, 2),  -- 1% AEP gross loss
            gross_loss_1_in_250_eur NUMERIC(18, 2),  -- 0.4% AEP gross loss
            net_loss_1_in_100_eur   NUMERIC(18, 2),  -- post-reinsurance
            net_loss_1_in_250_eur   NUMERIC(18, 2),
            probable_max_loss_eur   NUMERIC(18, 2),  -- PML
            average_annual_loss_eur NUMERIC(18, 2),  -- AAL
            cat_risk_change_2050_pct NUMERIC(8, 4),  -- % change in AAL by 2050 under scenario

            -- Solvency II (Article 44a — climate-adjusted technical provisions)
            technical_provisions_eur        NUMERIC(18, 2),
            climate_adjusted_tp_eur         NUMERIC(18, 2),  -- TP + climate loading
            tp_climate_uplift_pct           NUMERIC(8, 4),   -- uplift factor
            scr_climate_addon_eur           NUMERIC(18, 2),  -- Pillar 2 capital add-on
            scr_coverage_ratio_post_addon   NUMERIC(8, 3),

            -- Reserve adequacy under scenarios
            reserve_adequacy_1p5c  VARCHAR(20),  -- adequate | marginal | deficient
            reserve_adequacy_2c    VARCHAR(20),
            reserve_adequacy_3c    VARCHAR(20),
            reserve_deficiency_eur NUMERIC(18, 2),  -- shortfall under worst scenario

            -- Underwriting ESG screening
            coal_exclusion_policy     BOOLEAN DEFAULT false,
            oil_sands_exclusion       BOOLEAN DEFAULT false,
            arctic_drilling_exclusion BOOLEAN DEFAULT false,
            new_fossil_fuel_underwriting_limit_pct NUMERIC(6, 3),

            -- Protection gap
            total_economic_loss_eur   NUMERIC(18, 2),
            insured_loss_eur          NUMERIC(18, 2),
            protection_gap_eur        NUMERIC(18, 2),  -- uninsured portion
            protection_gap_pct        NUMERIC(6, 3),

            -- Reinsurance
            reinsurance_retention_pct NUMERIC(6, 3),
            reinsurance_coverage_adequate BOOLEAN DEFAULT true,

            methodology_ref  TEXT DEFAULT 'Solvency II Art.44a / EIOPA ORSA 2022 / Lloyd''s CAT model / Swiss Re sigma',
            data_quality_score NUMERIC(4, 2),
            notes            TEXT,
            created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
        );
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_ins_assessments_entity
            ON insurance_climate_assessments (entity_id, assessment_date DESC);
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_ins_assessments_peril
            ON insurance_climate_assessments (cat_peril, scenario);
    """)


def downgrade():
    for tbl in (
        "insurance_climate_assessments", "insurance_climate_entities",
        "mining_risk_assessments", "mining_entities",
        "agriculture_risk_assessments", "agriculture_entities",
        "parameter_change_requests", "calculation_parameters",
    ):
        op.execute(f"DROP TABLE IF EXISTS {tbl} CASCADE;")
