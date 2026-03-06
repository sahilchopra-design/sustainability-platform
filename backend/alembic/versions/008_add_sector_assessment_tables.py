"""
Add Sector Assessment Tables

Revision ID: 008_add_sector_assessment_tables
Revises: 007_add_supply_chain_tables
Create Date: 2026-03-01

This migration adds tables for the Sector Assessments module:
- data_centre_facilities       : Data centre facility register
- data_centre_assessments      : ESG efficiency assessments (PUE, WUE, carbon intensity)
- data_centre_improvement_plans: Improvement targets and recommended actions
- cat_risk_properties          : Property / asset register for CAT risk
- cat_risk_assessments         : Catastrophe risk modelling results (return period losses, AAL, PML)
- cat_risk_climate_scenarios   : Forward-looking climate delta for CAT risk
- power_plants                 : Power plant register
- power_plant_assessments      : Decarbonisation trajectory and stranded asset analysis
- power_plant_trajectories     : Year-by-year carbon intensity milestones
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '008_add_sector_assessment_tables'
down_revision = '007_add_supply_chain_tables'
branch_labels = None
depends_on = None


def upgrade():
    """Create sector assessment tables."""

    # =========================================================================
    # DATA CENTRE MODULE
    # =========================================================================

    # -------------------------------------------------------------------------
    # 1. DATA CENTRE FACILITIES  (asset register)
    # -------------------------------------------------------------------------
    op.create_table(
        'data_centre_facilities',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('facility_name', sa.String(255), nullable=False),
        sa.Column('operator_name', sa.String(255)),
        sa.Column('facility_type', sa.String(30), default='enterprise'),  # enterprise | colocation | hyperscale | edge
        sa.Column('address', sa.Text),
        sa.Column('city', sa.String(100)),
        sa.Column('country_iso', sa.String(3), nullable=False),
        sa.Column('latitude', sa.Numeric(9, 6)),
        sa.Column('longitude', sa.Numeric(9, 6)),
        sa.Column('grid_region', sa.String(50)),

        # Physical characteristics
        sa.Column('total_floor_area_m2', sa.Numeric(10, 2)),
        sa.Column('white_space_m2', sa.Numeric(10, 2)),
        sa.Column('design_it_load_mw', sa.Numeric(8, 3)),
        sa.Column('installed_capacity_mw', sa.Numeric(8, 3)),
        sa.Column('year_built', sa.Integer),
        sa.Column('tier_classification', sa.String(10)),                # Tier I, II, III, IV (Uptime Institute)
        sa.Column('cooling_type', sa.String(30)),                       # air | liquid | direct_liquid | immersion | adiabatic | hybrid

        # Financial
        sa.Column('asset_value_gbp', sa.Numeric(15, 2)),
        sa.Column('annual_revenue_gbp', sa.Numeric(15, 2)),

        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.CheckConstraint("facility_type IN ('enterprise','colocation','hyperscale','edge','telco','government')", name='ck_dc_facilities_type'),
        sa.CheckConstraint("cooling_type IN ('air','liquid','direct_liquid','immersion','adiabatic','hybrid','free_cooling')", name='ck_dc_facilities_cooling'),
    )
    op.create_index('ix_dc_facilities_country', 'data_centre_facilities', ['country_iso'])
    op.create_index('ix_dc_facilities_name', 'data_centre_facilities', ['facility_name'])
    op.create_index('ix_dc_facilities_type', 'data_centre_facilities', ['facility_type'])

    # -------------------------------------------------------------------------
    # 2. DATA CENTRE ASSESSMENTS  (ESG efficiency metrics per assessment period)
    # -------------------------------------------------------------------------
    op.create_table(
        'data_centre_assessments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('facility_id', UUID(as_uuid=True), sa.ForeignKey('data_centre_facilities.id', ondelete='SET NULL')),
        sa.Column('facility_name', sa.String(255), nullable=False),
        sa.Column('assessment_year', sa.Integer, nullable=False),
        sa.Column('assessment_period', sa.String(20), default='annual'), # annual | quarterly | monthly

        # Energy metrics
        sa.Column('total_it_load_mw', sa.Numeric(8, 3)),               # average IT load
        sa.Column('total_it_load_kwh', sa.Numeric(14, 2)),             # annual kWh IT load
        sa.Column('total_facility_kwh', sa.Numeric(14, 2)),            # total facility energy consumption
        sa.Column('annual_energy_consumption_mwh', sa.Numeric(12, 2)),
        sa.Column('cooling_energy_kwh', sa.Numeric(14, 2)),
        sa.Column('power_supply_energy_kwh', sa.Numeric(14, 2)),

        # Efficiency KPIs (ISO/IEC 30134-2)
        sa.Column('pue', sa.Numeric(5, 3), nullable=False),            # Power Usage Effectiveness = total/IT
        sa.Column('pue_target', sa.Numeric(5, 3)),
        sa.Column('pue_industry_avg', sa.Numeric(5, 3), default=1.58),  # Uptime 2024 Global DC Survey
        sa.Column('cue', sa.Numeric(6, 4)),                            # Carbon Usage Effectiveness = CO2e / IT energy
        sa.Column('wue', sa.Numeric(6, 4)),                            # Water Usage Effectiveness (L/kWh)
        sa.Column('wue_target', sa.Numeric(6, 4)),
        sa.Column('rer', sa.Numeric(5, 4)),                            # Renewable Energy Ratio (0-1)
        sa.Column('gear', sa.Numeric(5, 4)),                           # Green Energy Adoption Ratio

        # Renewable energy
        sa.Column('renewable_energy_pct', sa.Numeric(5, 2)),
        sa.Column('renewable_energy_mwh', sa.Numeric(12, 2)),
        sa.Column('has_renewable_ppa', sa.Boolean, default=False),
        sa.Column('ppa_provider', sa.String(100)),
        sa.Column('ppa_capacity_mw', sa.Numeric(8, 3)),
        sa.Column('has_rec_certificates', sa.Boolean, default=False),
        sa.Column('has_on_site_generation', sa.Boolean, default=False),
        sa.Column('on_site_solar_mw', sa.Numeric(8, 3)),

        # Carbon emissions
        sa.Column('grid_emission_factor_kgco2e_kwh', sa.Numeric(8, 6)),
        sa.Column('carbon_intensity_kgco2e_kwh_it', sa.Numeric(8, 6)),  # carbon per kWh IT load
        sa.Column('annual_co2e_tco2e', sa.Numeric(12, 4)),
        sa.Column('scope2_market_tco2e', sa.Numeric(12, 4)),
        sa.Column('scope2_location_tco2e', sa.Numeric(12, 4)),
        sa.Column('scope1_backup_gen_tco2e', sa.Numeric(12, 4)),

        # Water usage
        sa.Column('water_consumption_litres', sa.Numeric(14, 2)),
        sa.Column('water_withdrawn_litres', sa.Numeric(14, 2)),
        sa.Column('water_recycled_pct', sa.Numeric(5, 2)),

        # Waste
        sa.Column('weee_generated_kg', sa.Numeric(10, 2)),
        sa.Column('weee_recycled_pct', sa.Numeric(5, 2)),

        # Certifications
        sa.Column('certifications', JSONB),                             # [{name, year, body}] e.g. ISO 14001, LEED Gold, BREEAM

        # Overall efficiency score and rating
        sa.Column('efficiency_score', sa.Numeric(5, 2)),               # 0-100
        sa.Column('efficiency_rating', sa.String(10)),                  # A+ | A | B | C | D | E
        sa.Column('benchmark_percentile', sa.Numeric(5, 2)),            # vs global DC benchmark

        # Gap vs benchmark
        sa.Column('gap_vs_1_5c_pathway', JSONB),                       # {energy_gap_mwh, carbon_gap_tco2e, investment_gbp}
        sa.Column('improvement_targets', JSONB),                        # [{metric, current, target, year, action}]
        sa.Column('recommended_actions', JSONB),                        # [{action, co2e_saving, cost_gbp, payback_years}]

        sa.Column('validation_summary', JSONB),
        sa.Column('status', sa.String(20), default='draft'),
        sa.Column('created_by', UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.CheckConstraint("status IN ('draft','submitted','approved','published','archived')", name='ck_dc_assessments_status'),
    )
    op.create_index('ix_dc_assessments_facility', 'data_centre_assessments', ['facility_id'])
    op.create_index('ix_dc_assessments_year', 'data_centre_assessments', ['assessment_year'])
    op.create_index('ix_dc_assessments_rating', 'data_centre_assessments', ['efficiency_rating'])

    # =========================================================================
    # CAT RISK MODULE
    # =========================================================================

    # -------------------------------------------------------------------------
    # 3. CAT RISK PROPERTIES  (asset / property register)
    # -------------------------------------------------------------------------
    op.create_table(
        'cat_risk_properties',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('property_reference', sa.String(100)),
        sa.Column('property_name', sa.String(255)),
        sa.Column('property_type', sa.String(50)),                      # residential | commercial_office | retail | industrial | hotel | data_centre | power_plant | infrastructure
        sa.Column('address', sa.Text),
        sa.Column('postcode', sa.String(20)),
        sa.Column('city', sa.String(100)),
        sa.Column('country_iso', sa.String(3), nullable=False),
        sa.Column('latitude', sa.Numeric(9, 6), nullable=False),
        sa.Column('longitude', sa.Numeric(9, 6), nullable=False),
        sa.Column('elevation_m', sa.Numeric(7, 2)),

        # Physical characteristics
        sa.Column('construction_type', sa.String(50)),                  # masonry | timber | steel | concrete | mixed
        sa.Column('construction_year', sa.Integer),
        sa.Column('number_of_storeys', sa.Integer),
        sa.Column('floor_area_m2', sa.Numeric(10, 2)),
        sa.Column('occupancy_type', sa.String(30)),                     # residential | commercial | mixed | vacant

        # Financial
        sa.Column('replacement_value_gbp', sa.Numeric(15, 2)),
        sa.Column('market_value_gbp', sa.Numeric(15, 2)),
        sa.Column('insured_value_gbp', sa.Numeric(15, 2)),
        sa.Column('annual_rental_income_gbp', sa.Numeric(12, 2)),

        # Ownership
        sa.Column('owner_entity_id', UUID(as_uuid=True)),
        sa.Column('portfolio_id', UUID(as_uuid=True)),

        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_cat_risk_properties_country', 'cat_risk_properties', ['country_iso'])
    op.create_index('ix_cat_risk_properties_type', 'cat_risk_properties', ['property_type'])
    op.create_index('ix_cat_risk_properties_postcode', 'cat_risk_properties', ['postcode'])

    # -------------------------------------------------------------------------
    # 4. CAT RISK ASSESSMENTS  (per-peril risk assessment)
    # -------------------------------------------------------------------------
    op.create_table(
        'cat_risk_assessments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('property_id', UUID(as_uuid=True), sa.ForeignKey('cat_risk_properties.id', ondelete='SET NULL')),
        sa.Column('property_reference', sa.String(100)),
        sa.Column('assessment_date', sa.Date, nullable=False),
        sa.Column('peril', sa.String(30), nullable=False),             # flood | earthquake | windstorm | wildfire | coastal_flood | subsidence | landslide | hail | volcanic

        # Model metadata
        sa.Column('cat_model_vendor', sa.String(50)),                   # RMS | AIR_Verisk | CoreLogic | JBA | Z_GIS | internal
        sa.Column('cat_model_version', sa.String(30)),
        sa.Column('exceedance_probability_method', sa.String(30), default='OEP'),  # OEP | AEP | AEL

        # Key risk metrics (£ losses)
        sa.Column('property_value_gbp', sa.Numeric(15, 2)),
        sa.Column('aal_gbp', sa.Numeric(15, 2)),                       # Average Annual Loss
        sa.Column('aal_pct_of_value', sa.Numeric(6, 4)),
        sa.Column('eml_gbp', sa.Numeric(15, 2)),                       # Estimated Maximum Loss (1-in-100yr)
        sa.Column('pml_gbp', sa.Numeric(15, 2)),                       # Probable Maximum Loss (1-in-250yr)

        # Return period losses (OEP)
        sa.Column('loss_1in10yr_gbp', sa.Numeric(15, 2)),
        sa.Column('loss_1in20yr_gbp', sa.Numeric(15, 2)),
        sa.Column('loss_1in50yr_gbp', sa.Numeric(15, 2)),
        sa.Column('loss_1in100yr_gbp', sa.Numeric(15, 2)),
        sa.Column('loss_1in200yr_gbp', sa.Numeric(15, 2)),
        sa.Column('loss_1in250yr_gbp', sa.Numeric(15, 2)),
        sa.Column('loss_1in500yr_gbp', sa.Numeric(15, 2)),
        sa.Column('loss_1in1000yr_gbp', sa.Numeric(15, 2)),

        # Severity metrics
        sa.Column('damage_ratio_mean', sa.Numeric(5, 4)),              # 0-1
        sa.Column('damage_ratio_1in100yr', sa.Numeric(5, 4)),
        sa.Column('vulnerability_class', sa.String(10)),               # A | B | C | D | E (low to high)

        # Hazard intensity (peril-specific)
        sa.Column('hazard_intensity', JSONB),                           # {flood_depth_m, wind_speed_ms, pga_g, etc.}

        # Lloyd's RDS (Realistic Disaster Scenario) — for insurance portfolios
        sa.Column('rds_scenario', sa.String(50)),
        sa.Column('rds_loss_gbp', sa.Numeric(15, 2)),

        # Solvency II / Cat capital
        sa.Column('sii_cat_capital_gbp', sa.Numeric(15, 2)),
        sa.Column('sii_scenario_loss_200yr_gbp', sa.Numeric(15, 2)),

        # Full return period curve (for charting)
        sa.Column('return_period_curve', JSONB),                        # [{return_period_yr, loss_gbp, damage_ratio}]

        # Insurance coverage
        sa.Column('is_insured', sa.Boolean, default=True),
        sa.Column('policy_limit_gbp', sa.Numeric(15, 2)),
        sa.Column('deductible_gbp', sa.Numeric(12, 2)),
        sa.Column('reinsurance_recovery_gbp', sa.Numeric(15, 2)),
        sa.Column('net_retained_loss_100yr_gbp', sa.Numeric(15, 2)),

        # Risk mitigation measures
        sa.Column('existing_mitigation', JSONB),                        # [{measure, effectiveness_pct, install_year}]
        sa.Column('recommended_mitigation', JSONB),                     # [{measure, cost_gbp, loss_reduction_gbp, benefit_cost_ratio}]

        # Risk rating
        sa.Column('risk_score', sa.Numeric(4, 2)),                     # 0-10
        sa.Column('risk_category', sa.String(10)),                      # Low | Medium | High | Very High
        sa.Column('validation_summary', JSONB),
        sa.Column('status', sa.String(20), default='draft'),
        sa.Column('created_by', UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.CheckConstraint("peril IN ('flood','earthquake','windstorm','wildfire','coastal_flood','subsidence','landslide','hail','volcanic','storm_surge','drought','extreme_heat','freeze')", name='ck_cat_risk_assessments_peril'),
        sa.CheckConstraint("risk_category IN ('Low','Medium','High','Very High')", name='ck_cat_risk_assessments_category'),
        sa.CheckConstraint("status IN ('draft','submitted','approved','published','archived')", name='ck_cat_risk_assessments_status'),
    )
    op.create_index('ix_cat_risk_assessments_property', 'cat_risk_assessments', ['property_id'])
    op.create_index('ix_cat_risk_assessments_peril', 'cat_risk_assessments', ['peril'])
    op.create_index('ix_cat_risk_assessments_date', 'cat_risk_assessments', ['assessment_date'])
    op.create_index('ix_cat_risk_assessments_category', 'cat_risk_assessments', ['risk_category'])

    # -------------------------------------------------------------------------
    # 5. CAT RISK CLIMATE SCENARIOS  (forward-looking climate delta)
    # -------------------------------------------------------------------------
    op.create_table(
        'cat_risk_climate_scenarios',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('assessment_id', UUID(as_uuid=True), sa.ForeignKey('cat_risk_assessments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('climate_scenario', sa.String(30), nullable=False),  # RCP2.6 | RCP4.5 | RCP8.5 | SSP1-1.9 | SSP2-4.5 | SSP5-8.5
        sa.Column('time_horizon_year', sa.Integer, nullable=False),    # 2030 | 2050 | 2075 | 2100

        # Climate delta (change relative to baseline 1981-2010)
        sa.Column('hazard_intensity_delta_pct', sa.Numeric(7, 3)),     # % change in hazard intensity
        sa.Column('frequency_delta_pct', sa.Numeric(7, 3)),            # % change in frequency
        sa.Column('aal_delta_pct', sa.Numeric(7, 3)),                  # % change in AAL
        sa.Column('aal_climate_adjusted_gbp', sa.Numeric(15, 2)),
        sa.Column('pml_delta_pct', sa.Numeric(7, 3)),
        sa.Column('pml_climate_adjusted_gbp', sa.Numeric(15, 2)),
        sa.Column('loss_1in100yr_climate_gbp', sa.Numeric(15, 2)),
        sa.Column('loss_1in250yr_climate_gbp', sa.Numeric(15, 2)),

        # Physical parameters for this scenario (peril-specific)
        sa.Column('climate_parameters', JSONB),                         # {temp_increase_c, sea_level_rise_m, precip_change_pct, ...}

        # Source and confidence
        sa.Column('climate_model', sa.String(50)),                      # CMIP6 | HighResMIP | CORDEX | IPCC_AR6
        sa.Column('confidence_level', sa.String(10)),                   # Low | Medium | High
        sa.Column('notes', sa.Text),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.CheckConstraint("climate_scenario IN ('RCP2.6','RCP4.5','RCP6.0','RCP8.5','SSP1-1.9','SSP1-2.6','SSP2-4.5','SSP3-7.0','SSP5-8.5')", name='ck_cat_climate_scenario'),
    )
    op.create_index('ix_cat_climate_assessment', 'cat_risk_climate_scenarios', ['assessment_id'])
    op.create_index('ix_cat_climate_scenario', 'cat_risk_climate_scenarios', ['climate_scenario'])

    # =========================================================================
    # POWER PLANT MODULE
    # =========================================================================

    # -------------------------------------------------------------------------
    # 6. POWER PLANTS  (plant register)
    # -------------------------------------------------------------------------
    op.create_table(
        'power_plants',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('plant_name', sa.String(255), nullable=False),
        sa.Column('plant_id_repd', sa.String(50)),                     # UK REPD ID or equivalent
        sa.Column('operator_name', sa.String(255)),
        sa.Column('owner_entity_id', UUID(as_uuid=True)),
        sa.Column('address', sa.Text),
        sa.Column('country_iso', sa.String(3), nullable=False),
        sa.Column('latitude', sa.Numeric(9, 6)),
        sa.Column('longitude', sa.Numeric(9, 6)),

        # Technology
        sa.Column('fuel_type', sa.String(30), nullable=False),          # coal | gas_ccgt | gas_ocgt | oil | nuclear | hydro | wind_onshore | wind_offshore | solar_pv | biomass | geothermal | tidal | other
        sa.Column('technology_type', sa.String(50)),                    # CCGT | OCGT | IGCC | CFPP | PC | CFB | combined_heat_power | etc.
        sa.Column('installed_capacity_mw', sa.Numeric(10, 3), nullable=False),
        sa.Column('net_capacity_mw', sa.Numeric(10, 3)),
        sa.Column('capacity_factor_pct', sa.Numeric(5, 2)),

        # Age and lifecycle
        sa.Column('year_commissioned', sa.Integer),
        sa.Column('year_decommission_planned', sa.Integer),
        sa.Column('remaining_useful_life_years', sa.Integer),
        sa.Column('design_lifetime_years', sa.Integer, default=25),
        sa.Column('is_operational', sa.Boolean, default=True),
        sa.Column('operational_status', sa.String(20), default='operational'),  # operational | mothballed | under_construction | decommissioned

        # Financial
        sa.Column('net_book_value_gbp', sa.Numeric(15, 2)),
        sa.Column('annual_revenue_gbp', sa.Numeric(15, 2)),
        sa.Column('lcoe_gbp_per_mwh', sa.Numeric(8, 2)),               # Levelised Cost of Energy

        # Grid connection
        sa.Column('grid_connection_voltage_kv', sa.Numeric(6, 1)),
        sa.Column('transmission_system_operator', sa.String(100)),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.CheckConstraint("fuel_type IN ('coal','gas_ccgt','gas_ocgt','oil','nuclear','hydro','wind_onshore','wind_offshore','solar_pv','solar_csp','biomass','geothermal','tidal','wave','hydrogen','other')", name='ck_power_plants_fuel_type'),
        sa.CheckConstraint("operational_status IN ('operational','mothballed','under_construction','decommissioned','care_and_maintenance')", name='ck_power_plants_status'),
    )
    op.create_index('ix_power_plants_country', 'power_plants', ['country_iso'])
    op.create_index('ix_power_plants_fuel', 'power_plants', ['fuel_type'])
    op.create_index('ix_power_plants_operator', 'power_plants', ['operator_name'])

    # -------------------------------------------------------------------------
    # 7. POWER PLANT ASSESSMENTS  (decarbonisation and stranded asset analysis)
    # -------------------------------------------------------------------------
    op.create_table(
        'power_plant_assessments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('plant_id', UUID(as_uuid=True), sa.ForeignKey('power_plants.id', ondelete='SET NULL')),
        sa.Column('plant_name', sa.String(255), nullable=False),
        sa.Column('assessment_date', sa.Date, nullable=False),

        # Current carbon performance
        sa.Column('current_ci_gco2_kwh', sa.Numeric(8, 3), nullable=False), # current carbon intensity gCO2/kWh
        sa.Column('annual_generation_mwh', sa.Numeric(14, 2)),
        sa.Column('annual_co2e_tco2e', sa.Numeric(14, 4)),
        sa.Column('thermal_efficiency_pct', sa.Numeric(5, 2)),

        # IEA NZE 2050 benchmarks (IEA World Energy Outlook / Net Zero Emissions by 2050)
        sa.Column('iea_nze_2030_threshold_gco2_kwh', sa.Numeric(8, 3)),  # pathway benchmark CI for 2030
        sa.Column('iea_nze_2040_threshold_gco2_kwh', sa.Numeric(8, 3)),
        sa.Column('iea_nze_2050_threshold_gco2_kwh', sa.Numeric(8, 3), default=0.0),

        # Current-year alignment
        sa.Column('is_above_2030_threshold', sa.Boolean),
        sa.Column('ci_gap_to_nze_2030_gco2_kwh', sa.Numeric(8, 3)),
        sa.Column('ci_gap_to_nze_2050_gco2_kwh', sa.Numeric(8, 3)),

        # Projected trajectory (accounting for retrofit plans)
        sa.Column('projected_ci_2030_gco2_kwh', sa.Numeric(8, 3)),
        sa.Column('projected_ci_2040_gco2_kwh', sa.Numeric(8, 3)),
        sa.Column('projected_ci_2050_gco2_kwh', sa.Numeric(8, 3)),
        sa.Column('technology_transition_planned', sa.String(100)),     # e.g. 'CCGT→H2 co-firing | CCS retrofit | decommission'

        # Stranded asset analysis
        sa.Column('stranded_asset_risk_score', sa.Numeric(4, 2)),      # 0-10
        sa.Column('stranded_asset_risk_category', sa.String(20)),       # Low | Medium | High | Critical
        sa.Column('implied_stranding_year', sa.Integer),                # year at which CI exceeds IEA NZE pathway
        sa.Column('regulatory_stranding_year', sa.Integer),             # year at which plant breaches regulation (e.g. UK CPS, EU ETS)
        sa.Column('commercial_stranding_year', sa.Integer),             # year uneconomic vs renewable LCOE
        sa.Column('stranded_value_at_risk_gbp', sa.Numeric(15, 2)),    # NPV of NBV exposed to stranding risk
        sa.Column('stranded_value_pct_of_nbv', sa.Numeric(5, 2)),

        # Carbon cost analysis
        sa.Column('carbon_price_assumption_gbp_t', sa.Numeric(8, 2)),  # e.g. £50/tCO2e (UK ETS 2024)
        sa.Column('annual_carbon_cost_gbp', sa.Numeric(12, 2)),
        sa.Column('cumulative_carbon_cost_to_2050_gbp', sa.Numeric(15, 2)),
        sa.Column('carbon_cost_scenario', sa.String(20), default='central'),  # low | central | high | NZE

        # Capex required for transition
        sa.Column('transition_capex_required_gbp', sa.Numeric(15, 2)),
        sa.Column('ccs_retrofit_cost_gbp', sa.Numeric(15, 2)),
        sa.Column('fuel_switch_cost_gbp', sa.Numeric(15, 2)),           # e.g. gas → hydrogen

        # Air quality
        sa.Column('nox_kg_per_mwh', sa.Numeric(8, 4)),
        sa.Column('sox_kg_per_mwh', sa.Numeric(8, 4)),
        sa.Column('pm25_kg_per_mwh', sa.Numeric(8, 4)),

        # Recommended actions
        sa.Column('recommended_actions', JSONB),                        # [{action, timeline, capex_gbp, co2e_saving_pa, npv_gbp}]

        sa.Column('validation_summary', JSONB),
        sa.Column('climate_scenario', sa.String(30)),
        sa.Column('status', sa.String(20), default='draft'),
        sa.Column('created_by', UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.CheckConstraint("stranded_asset_risk_category IN ('Low','Medium','High','Critical')", name='ck_plant_assessments_risk_category'),
        sa.CheckConstraint("status IN ('draft','submitted','approved','published','archived')", name='ck_plant_assessments_status'),
    )
    op.create_index('ix_plant_assessments_plant', 'power_plant_assessments', ['plant_id'])
    op.create_index('ix_plant_assessments_date', 'power_plant_assessments', ['assessment_date'])
    op.create_index('ix_plant_assessments_risk', 'power_plant_assessments', ['stranded_asset_risk_category'])

    # -------------------------------------------------------------------------
    # 8. POWER PLANT TRAJECTORIES  (year-by-year CI milestones)
    # -------------------------------------------------------------------------
    op.create_table(
        'power_plant_trajectories',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('assessment_id', UUID(as_uuid=True), sa.ForeignKey('power_plant_assessments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('year', sa.Integer, nullable=False),

        # Trajectory values
        sa.Column('baseline_ci_gco2_kwh', sa.Numeric(8, 3)),           # projected baseline (no action)
        sa.Column('target_ci_gco2_kwh', sa.Numeric(8, 3)),             # with planned transition actions
        sa.Column('nze_benchmark_ci_gco2_kwh', sa.Numeric(8, 3)),      # IEA NZE pathway benchmark

        # Generation and emissions
        sa.Column('projected_generation_mwh', sa.Numeric(14, 2)),
        sa.Column('projected_co2e_tco2e', sa.Numeric(14, 4)),
        sa.Column('projected_carbon_cost_gbp', sa.Numeric(12, 2)),

        # Annual carbon budget position
        sa.Column('cumulative_overshoot_tco2e', sa.Numeric(14, 4)),    # cumulative excess over NZE pathway
        sa.Column('alignment_gap_gco2_kwh', sa.Numeric(8, 3)),         # target_ci - nze_benchmark (positive = above benchmark)
        sa.Column('is_aligned_with_nze', sa.Boolean),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_plant_trajectories_assessment', 'power_plant_trajectories', ['assessment_id'])
    op.create_index('ix_plant_trajectories_year', 'power_plant_trajectories', ['year'])


def downgrade():
    """Drop sector assessment tables."""
    op.drop_table('power_plant_trajectories')
    op.drop_table('power_plant_assessments')
    op.drop_table('power_plants')
    op.drop_table('cat_risk_climate_scenarios')
    op.drop_table('cat_risk_assessments')
    op.drop_table('cat_risk_properties')
    op.drop_table('data_centre_assessments')
    op.drop_table('data_centre_facilities')
