"""
Add Energy Developer Tables

Revision ID: 012_add_energy_developer_tables
Revises: 011_add_financial_institution_tables
Create Date: 2026-03-01

Tables covering energy developers (utilities, IPPs, renewables developers):
- energy_entities                : Entity master record
- energy_financials              : P&L, balance sheet, credit metrics (annual)
- energy_generation_mix          : Installed capacity and generation by fuel/technology
- energy_csrd_e1_climate         : ESRS E1 — GHG inventory, transition plan, targets, Paris alignment
- energy_csrd_e2_pollution       : ESRS E2 — Air pollutants (NOx, SOx, PM2.5, CO, VOC, PFAS)
- energy_csrd_e3_water           : ESRS E3 — Water withdrawal, discharge, recycling
- energy_csrd_e4_biodiversity    : ESRS E4 — Biodiversity, habitat, protected areas, land use
- energy_csrd_e5_circular        : ESRS E5 — Waste, hazardous materials, circular economy
- energy_csrd_s1_workforce       : ESRS S1 — Safety, headcount, diversity, wages
- energy_csrd_g1_governance      : ESRS G1 — Board, anti-corruption, lobbying
- energy_renewable_pipeline      : Renewables development pipeline (projects under development)
- energy_stranded_assets         : Stranded asset register (coal/gas plants facing early closure)

Based on CSRD disclosures: EDP (2024), ENGIE (2024), Ørsted (2024), RWE (2024)
ESRS standards: ESRS 2, E1–E5, S1, S2, S4, G1
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '012_add_energy_developer_tables'
down_revision = '011_add_financial_institution_tables'
branch_labels = None
depends_on = None


def upgrade():

    # =========================================================================
    # 1. ENERGY ENTITIES
    # =========================================================================
    op.create_table(
        'energy_entities',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('legal_name', sa.String(255), nullable=False),
        sa.Column('trading_name', sa.String(255)),
        sa.Column('lei', sa.String(20)),
        sa.Column('entity_type', sa.String(40), nullable=False),        # vertically_integrated | pure_renewables | ipp | grid_operator | gas_network | oil_major | lng | nuclear_operator | offshore_wind
        sa.Column('headquarters_country', sa.String(3), nullable=False),
        sa.Column('listing_exchange', sa.String(20)),
        sa.Column('isin', sa.String(12)),
        sa.Column('credit_rating_sp', sa.String(10)),
        sa.Column('credit_rating_moodys', sa.String(10)),
        sa.Column('credit_rating_fitch', sa.String(10)),
        sa.Column('eu_ets_installation_count', sa.Integer),
        sa.Column('eu_ets_id', sa.String(50)),
        sa.Column('csrd_first_mandatory_year', sa.Integer, default=2024),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.CheckConstraint("entity_type IN ('vertically_integrated','pure_renewables','ipp','grid_operator','gas_network','oil_major','lng','nuclear_operator','offshore_wind','hydro','geothermal','storage','other')", name='ck_energy_entities_type'),
    )
    op.create_index('ix_energy_entities_lei', 'energy_entities', ['lei'])
    op.create_index('ix_energy_entities_country', 'energy_entities', ['headquarters_country'])
    op.create_index('ix_energy_entities_type', 'energy_entities', ['entity_type'])

    # =========================================================================
    # 2. ENERGY FINANCIALS  (P&L, balance sheet, capex, credit)
    # =========================================================================
    op.create_table(
        'energy_financials',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_id', UUID(as_uuid=True), sa.ForeignKey('energy_entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reporting_year', sa.Integer, nullable=False),
        sa.Column('currency', sa.String(3), default='EUR'),

        # --- P&L ---
        sa.Column('total_revenues', sa.Numeric(18, 2)),                 # EUR millions
        sa.Column('electricity_revenues', sa.Numeric(18, 2)),
        sa.Column('gas_revenues', sa.Numeric(18, 2)),
        sa.Column('network_revenues', sa.Numeric(18, 2)),
        sa.Column('services_revenues', sa.Numeric(18, 2)),
        sa.Column('ebitda', sa.Numeric(18, 2)),
        sa.Column('ebitda_margin_pct', sa.Numeric(5, 2)),
        sa.Column('ebit', sa.Numeric(18, 2)),
        sa.Column('depreciation_amortization', sa.Numeric(18, 2)),
        sa.Column('impairment_charges', sa.Numeric(18, 2)),             # incl. stranded asset impairments
        sa.Column('finance_costs_net', sa.Numeric(18, 2)),
        sa.Column('profit_before_tax', sa.Numeric(18, 2)),
        sa.Column('income_tax', sa.Numeric(18, 2)),
        sa.Column('net_profit_group', sa.Numeric(18, 2)),
        sa.Column('eps_diluted', sa.Numeric(8, 4)),
        sa.Column('roe', sa.Numeric(6, 3)),
        sa.Column('roce', sa.Numeric(6, 3)),                           # Return on Capital Employed

        # --- Balance Sheet ---
        sa.Column('total_assets', sa.Numeric(18, 2)),
        sa.Column('ppe_net', sa.Numeric(18, 2)),                       # Property, Plant & Equipment
        sa.Column('goodwill_intangibles', sa.Numeric(18, 2)),
        sa.Column('right_of_use_assets', sa.Numeric(18, 2)),
        sa.Column('total_equity', sa.Numeric(18, 2)),
        sa.Column('net_debt', sa.Numeric(18, 2)),
        sa.Column('gross_debt', sa.Numeric(18, 2)),
        sa.Column('net_debt_to_ebitda', sa.Numeric(5, 2)),
        sa.Column('interest_coverage_ratio', sa.Numeric(5, 2)),
        sa.Column('hybrid_capital', sa.Numeric(18, 2)),                 # hybrid bonds (50% equity treatment)
        sa.Column('market_cap', sa.Numeric(18, 2)),
        sa.Column('enterprise_value', sa.Numeric(18, 2)),
        sa.Column('ev_to_ebitda', sa.Numeric(5, 2)),

        # --- Capital Expenditure ---
        sa.Column('total_capex', sa.Numeric(18, 2)),
        sa.Column('growth_capex', sa.Numeric(18, 2)),                   # new capacity additions
        sa.Column('maintenance_capex', sa.Numeric(18, 2)),
        sa.Column('green_capex', sa.Numeric(18, 2)),                    # renewables + storage + green H2 + efficiency
        sa.Column('green_capex_pct', sa.Numeric(5, 2)),
        sa.Column('eu_taxonomy_aligned_capex_pct', sa.Numeric(5, 2)),

        # --- Dividends ---
        sa.Column('dividend_per_share', sa.Numeric(8, 4)),
        sa.Column('dividend_yield_pct', sa.Numeric(5, 2)),

        # --- Green Finance Instruments ---
        sa.Column('green_bonds_outstanding_meur', sa.Numeric(14, 2)),
        sa.Column('sustainability_linked_bonds_meur', sa.Numeric(14, 2)),
        sa.Column('green_finance_total_pct_of_debt', sa.Numeric(5, 2)),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_energy_financials_entity', 'energy_financials', ['entity_id'])
    op.create_index('ix_energy_financials_year', 'energy_financials', ['reporting_year'])

    # =========================================================================
    # 3. ENERGY GENERATION MIX  (capacity, generation, efficiency by fuel)
    # =========================================================================
    op.create_table(
        'energy_generation_mix',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_id', UUID(as_uuid=True), sa.ForeignKey('energy_entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reporting_year', sa.Integer, nullable=False),

        # --- Installed Capacity (GW) ---
        sa.Column('total_installed_gw', sa.Numeric(8, 3)),
        sa.Column('coal_installed_gw', sa.Numeric(8, 3)),
        sa.Column('lignite_installed_gw', sa.Numeric(8, 3)),
        sa.Column('gas_ccgt_installed_gw', sa.Numeric(8, 3)),
        sa.Column('gas_ocgt_installed_gw', sa.Numeric(8, 3)),
        sa.Column('oil_installed_gw', sa.Numeric(8, 3)),
        sa.Column('nuclear_installed_gw', sa.Numeric(8, 3)),
        sa.Column('hydro_installed_gw', sa.Numeric(8, 3)),
        sa.Column('pumped_hydro_installed_gw', sa.Numeric(8, 3)),
        sa.Column('wind_onshore_installed_gw', sa.Numeric(8, 3)),
        sa.Column('wind_offshore_installed_gw', sa.Numeric(8, 3)),
        sa.Column('solar_pv_installed_gw', sa.Numeric(8, 3)),
        sa.Column('solar_csp_installed_gw', sa.Numeric(8, 3)),
        sa.Column('biomass_installed_gw', sa.Numeric(8, 3)),
        sa.Column('geothermal_installed_gw', sa.Numeric(8, 3)),
        sa.Column('tidal_wave_installed_gw', sa.Numeric(8, 3)),
        sa.Column('battery_storage_gwh', sa.Numeric(8, 3)),
        sa.Column('hydrogen_electrolyser_gw', sa.Numeric(8, 3)),

        # Renewables subtotal
        sa.Column('total_renewables_installed_gw', sa.Numeric(8, 3)),
        sa.Column('renewables_capacity_share_pct', sa.Numeric(5, 2)),
        sa.Column('low_carbon_capacity_share_pct', sa.Numeric(5, 2)),  # renewables + nuclear

        # --- Electricity Generation (TWh) ---
        sa.Column('total_generation_twh', sa.Numeric(10, 3)),
        sa.Column('coal_generation_twh', sa.Numeric(10, 3)),
        sa.Column('lignite_generation_twh', sa.Numeric(10, 3)),
        sa.Column('gas_generation_twh', sa.Numeric(10, 3)),
        sa.Column('oil_generation_twh', sa.Numeric(10, 3)),
        sa.Column('nuclear_generation_twh', sa.Numeric(10, 3)),
        sa.Column('hydro_generation_twh', sa.Numeric(10, 3)),
        sa.Column('wind_generation_twh', sa.Numeric(10, 3)),
        sa.Column('solar_generation_twh', sa.Numeric(10, 3)),
        sa.Column('biomass_generation_twh', sa.Numeric(10, 3)),
        sa.Column('other_renewables_twh', sa.Numeric(10, 3)),
        sa.Column('total_renewables_twh', sa.Numeric(10, 3)),
        sa.Column('renewables_generation_share_pct', sa.Numeric(5, 2)),

        # --- Carbon performance ---
        sa.Column('avg_carbon_intensity_gco2_kwh', sa.Numeric(8, 3)), # gCO2e/kWh (portfolio-level)
        sa.Column('coal_ci_gco2_kwh', sa.Numeric(8, 3)),
        sa.Column('gas_ci_gco2_kwh', sa.Numeric(8, 3)),
        sa.Column('nuclear_ci_gco2_kwh', sa.Numeric(8, 3), default=12.0),
        sa.Column('hydro_ci_gco2_kwh', sa.Numeric(8, 3)),
        sa.Column('wind_ci_gco2_kwh', sa.Numeric(8, 3), default=11.0),
        sa.Column('solar_pv_ci_gco2_kwh', sa.Numeric(8, 3), default=45.0),

        # --- EU ETS ---
        sa.Column('eu_ets_allowances_allocated', sa.Numeric(12, 2)),   # free allocation
        sa.Column('eu_ets_allowances_purchased', sa.Numeric(12, 2)),
        sa.Column('eu_ets_cost_meur', sa.Numeric(12, 2)),
        sa.Column('eu_ets_price_avg_eur_t', sa.Numeric(7, 2)),

        # --- Heat / District Heating ---
        sa.Column('heat_generation_twh', sa.Numeric(10, 3)),
        sa.Column('district_heating_connections', sa.Integer),

        # --- Gas networks ---
        sa.Column('gas_transported_twh', sa.Numeric(10, 3)),
        sa.Column('gas_network_length_km', sa.Numeric(10, 1)),
        sa.Column('biomethane_injected_twh', sa.Numeric(10, 3)),
        sa.Column('green_hydrogen_produced_twh', sa.Numeric(10, 3)),

        # --- Capacity factors ---
        sa.Column('wind_onshore_cf_pct', sa.Numeric(5, 2)),
        sa.Column('wind_offshore_cf_pct', sa.Numeric(5, 2)),
        sa.Column('solar_cf_pct', sa.Numeric(5, 2)),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_energy_gen_mix_entity', 'energy_generation_mix', ['entity_id'])
    op.create_index('ix_energy_gen_mix_year', 'energy_generation_mix', ['reporting_year'])

    # =========================================================================
    # 4. ENERGY CSRD E1 CLIMATE  (ESRS E1 disclosures for energy sector)
    # =========================================================================
    op.create_table(
        'energy_csrd_e1_climate',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_id', UUID(as_uuid=True), sa.ForeignKey('energy_entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reporting_year', sa.Integer, nullable=False),

        # ESRS E1-6: GHG emissions
        sa.Column('scope1_tco2e', sa.Numeric(14, 4)),                   # power + industrial combustion
        sa.Column('scope2_market_tco2e', sa.Numeric(14, 4)),
        sa.Column('scope2_location_tco2e', sa.Numeric(14, 4)),
        sa.Column('scope3_upstream_tco2e', sa.Numeric(14, 4)),          # cat 1-8
        sa.Column('scope3_downstream_tco2e', sa.Numeric(14, 4)),        # cat 9-15
        sa.Column('scope3_total_tco2e', sa.Numeric(14, 4)),
        sa.Column('scope3_cat3_energy_related_tco2e', sa.Numeric(14, 4)),  # upstream fuel extraction (large for gas companies)
        sa.Column('scope3_cat11_use_of_sold_energy_tco2e', sa.Numeric(14, 4)),  # CRITICAL for gas retailers
        sa.Column('total_ghg_tco2e', sa.Numeric(14, 4)),
        sa.Column('total_ghg_vs_baseline_pct', sa.Numeric(7, 3)),
        sa.Column('biogenic_co2_tco2e', sa.Numeric(12, 4)),
        sa.Column('non_co2_ghg_tco2e', sa.Numeric(12, 4)),             # CH4 (methane from gas networks), N2O, SF6
        sa.Column('methane_leakage_tco2e', sa.Numeric(12, 4)),          # gas network methane losses
        sa.Column('methane_leakage_rate_pct', sa.Numeric(5, 4)),        # % of gas transported

        # ESRS E1-5: Energy consumption
        sa.Column('total_primary_energy_twh', sa.Numeric(14, 3)),
        sa.Column('fossil_fuel_input_twh', sa.Numeric(14, 3)),
        sa.Column('nuclear_input_twh', sa.Numeric(14, 3)),
        sa.Column('renewable_input_twh', sa.Numeric(14, 3)),
        sa.Column('own_energy_consumption_mwh', sa.Numeric(14, 2)),     # for own operations (offices, vehicles, etc.)
        sa.Column('renewable_energy_own_use_pct', sa.Numeric(5, 2)),

        # ESRS E1-4: GHG reduction targets
        sa.Column('scope1_base_year', sa.Integer),
        sa.Column('scope1_base_year_tco2e', sa.Numeric(14, 4)),
        sa.Column('scope1_target_reduction_pct_2030', sa.Numeric(5, 2)),
        sa.Column('scope1_target_reduction_pct_2050', sa.Numeric(5, 2)),
        sa.Column('scope12_target_reduction_pct_2030', sa.Numeric(5, 2)),
        sa.Column('scope3_target_reduction_pct_2030', sa.Numeric(5, 2)),
        sa.Column('scope3_target_reduction_pct_2050', sa.Numeric(5, 2)),
        sa.Column('absolute_target_tco2e_2030', sa.Numeric(14, 4)),
        sa.Column('carbon_intensity_target_gco2_kwh_2030', sa.Numeric(8, 3)),
        sa.Column('carbon_intensity_target_gco2_kwh_2040', sa.Numeric(8, 3)),
        sa.Column('carbon_intensity_target_gco2_kwh_2050', sa.Numeric(8, 3), default=0.0),
        sa.Column('net_zero_target_year', sa.Integer),
        sa.Column('sbti_committed', sa.Boolean, default=False),
        sa.Column('sbti_pathway', sa.String(30)),

        # ESRS E1-1: Transition plan
        sa.Column('coal_exit_year', sa.Integer),                        # e.g. RWE 2030, ENGIE 2025
        sa.Column('coal_capacity_remaining_gw', sa.Numeric(8, 3)),
        sa.Column('new_renewable_capacity_target_gw_2030', sa.Numeric(8, 3)),
        sa.Column('renewable_capacity_current_gw', sa.Numeric(8, 3)),
        sa.Column('capex_renewables_committed_bn', sa.Numeric(8, 2)),

        # Carbon credits
        sa.Column('carbon_credits_purchased_tco2e', sa.Numeric(12, 4)),
        sa.Column('carbon_credits_retired_tco2e', sa.Numeric(12, 4)),
        sa.Column('carbon_credit_standard', sa.String(50)),
        sa.Column('has_internal_carbon_price', sa.Boolean, default=False),
        sa.Column('internal_carbon_price_eur_t', sa.Numeric(8, 2)),

        # CCS
        sa.Column('ccs_capacity_mtco2_pa', sa.Numeric(8, 3)),          # operational CCS capture
        sa.Column('ccs_target_mtco2_pa_2030', sa.Numeric(8, 3)),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_energy_csrd_e1_entity', 'energy_csrd_e1_climate', ['entity_id'])
    op.create_index('ix_energy_csrd_e1_year', 'energy_csrd_e1_climate', ['reporting_year'])

    # =========================================================================
    # 5. ENERGY CSRD E2 POLLUTION  (ESRS E2 — air quality and pollutants)
    # =========================================================================
    op.create_table(
        'energy_csrd_e2_pollution',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_id', UUID(as_uuid=True), sa.ForeignKey('energy_entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reporting_year', sa.Integer, nullable=False),

        # Air emissions to air (tonnes)
        sa.Column('nox_tonnes', sa.Numeric(12, 2)),                     # nitrogen oxides (NO + NO₂)
        sa.Column('sox_tonnes', sa.Numeric(12, 2)),                     # sulphur oxides (SO₂ + SO₃)
        sa.Column('pm10_tonnes', sa.Numeric(12, 2)),                    # particulate matter ≤10 µm
        sa.Column('pm25_tonnes', sa.Numeric(12, 2)),                    # fine particulate matter ≤2.5 µm
        sa.Column('co_tonnes', sa.Numeric(12, 2)),                      # carbon monoxide
        sa.Column('voc_tonnes', sa.Numeric(12, 2)),                     # volatile organic compounds
        sa.Column('ammonia_tonnes', sa.Numeric(12, 2)),                 # NH₃
        sa.Column('heavy_metals_kg', sa.Numeric(10, 2)),
        sa.Column('mercury_kg', sa.Numeric(10, 2)),                     # Hg
        sa.Column('dioxins_furans_g', sa.Numeric(10, 4)),               # PCDDs/PCDFs (g I-TEQ)
        sa.Column('sf6_tonnes', sa.Numeric(10, 4)),                     # from grid equipment (potent GHG + air pollutant)

        # Intensity per MWh generated
        sa.Column('nox_g_per_kwh', sa.Numeric(8, 4)),
        sa.Column('sox_g_per_kwh', sa.Numeric(8, 4)),
        sa.Column('pm25_g_per_kwh', sa.Numeric(8, 4)),

        # IED / BREF compliance
        sa.Column('ied_compliant_capacity_pct', sa.Numeric(5, 2)),      # Industrial Emissions Directive
        sa.Column('exceedances_nox', sa.Integer, default=0),
        sa.Column('exceedances_sox', sa.Integer, default=0),

        # Emissions to water
        sa.Column('thermal_discharge_twh_heat', sa.Numeric(10, 3)),    # thermal discharge from cooling
        sa.Column('water_pollutants_tonnes', sa.Numeric(10, 2)),
        sa.Column('nitrates_to_water_tonnes', sa.Numeric(10, 2)),

        # Emissions to soil
        sa.Column('contaminated_sites_count', sa.Integer, default=0),
        sa.Column('contaminated_land_remediated_ha', sa.Numeric(10, 2)),

        # Hazardous substances
        sa.Column('substances_of_very_high_concern_kg', sa.Numeric(12, 2)),

        # Pollution incidents
        sa.Column('major_pollution_incidents', sa.Integer, default=0),
        sa.Column('minor_pollution_incidents', sa.Integer, default=0),
        sa.Column('fines_pollution_meur', sa.Numeric(10, 2), default=0),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_energy_csrd_e2_entity', 'energy_csrd_e2_pollution', ['entity_id'])
    op.create_index('ix_energy_csrd_e2_year', 'energy_csrd_e2_pollution', ['reporting_year'])

    # =========================================================================
    # 6. ENERGY CSRD E3 WATER  (ESRS E3 — water use)
    # =========================================================================
    op.create_table(
        'energy_csrd_e3_water',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_id', UUID(as_uuid=True), sa.ForeignKey('energy_entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reporting_year', sa.Integer, nullable=False),

        # Water volumes (million m³)
        sa.Column('total_water_withdrawal_mm3', sa.Numeric(12, 4)),     # gross withdrawal from all sources
        sa.Column('surface_water_withdrawal_mm3', sa.Numeric(12, 4)),
        sa.Column('groundwater_withdrawal_mm3', sa.Numeric(12, 4)),
        sa.Column('seawater_withdrawal_mm3', sa.Numeric(12, 4)),
        sa.Column('municipal_water_withdrawal_mm3', sa.Numeric(12, 4)),
        sa.Column('total_water_discharge_mm3', sa.Numeric(12, 4)),
        sa.Column('total_water_consumption_mm3', sa.Numeric(12, 4)),    # withdrawal − discharge
        sa.Column('water_recycled_pct', sa.Numeric(5, 2)),
        sa.Column('water_reused_mm3', sa.Numeric(12, 4)),

        # Water intensity
        sa.Column('water_intensity_l_per_kwh_gen', sa.Numeric(8, 4)),  # litres per kWh generated (once-through cooling)
        sa.Column('consumptive_water_l_per_kwh', sa.Numeric(8, 4)),    # consumptive use (evaporation from cooling towers)

        # Water stress
        sa.Column('withdrawal_in_high_stress_areas_pct', sa.Numeric(5, 2)),  # WRI Aqueduct high water stress
        sa.Column('sites_in_water_scarce_regions', sa.Integer),
        sa.Column('water_risk_score', sa.Numeric(4, 2)),

        # Targets
        sa.Column('water_withdrawal_target_reduction_pct', sa.Numeric(5, 2)),
        sa.Column('water_target_year', sa.Integer),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_energy_csrd_e3_entity', 'energy_csrd_e3_water', ['entity_id'])
    op.create_index('ix_energy_csrd_e3_year', 'energy_csrd_e3_water', ['reporting_year'])

    # =========================================================================
    # 7. ENERGY CSRD E4 BIODIVERSITY  (ESRS E4)
    # =========================================================================
    op.create_table(
        'energy_csrd_e4_biodiversity',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_id', UUID(as_uuid=True), sa.ForeignKey('energy_entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reporting_year', sa.Integer, nullable=False),

        # Land use
        sa.Column('total_land_use_ha', sa.Numeric(12, 2)),
        sa.Column('land_sealed_ha', sa.Numeric(12, 2)),
        sa.Column('land_rehabilitated_ha', sa.Numeric(12, 2)),
        sa.Column('sites_in_protected_areas', sa.Integer),
        sa.Column('sites_adjacent_protected_areas', sa.Integer),
        sa.Column('kba_sensitive_sites', sa.Integer),                   # Key Biodiversity Areas

        # Habitat
        sa.Column('habitat_restored_ha', sa.Numeric(10, 2)),
        sa.Column('biodiversity_offsetting_ha', sa.Numeric(10, 2)),
        sa.Column('species_impacted_count', sa.Integer),                # species at risk from operations
        sa.Column('invasive_species_incidents', sa.Integer, default=0),

        # Bird strike / wildlife
        sa.Column('bird_mortality_per_turbine', sa.Numeric(6, 3)),     # wind farm bird strike
        sa.Column('bat_mortality_per_turbine', sa.Numeric(6, 3)),

        # Offshore
        sa.Column('offshore_wind_marine_protected_areas_count', sa.Integer),
        sa.Column('marine_habitat_impact_ha', sa.Numeric(10, 2)),

        # Biodiversity management
        sa.Column('has_biodiversity_policy', sa.Boolean, default=False),
        sa.Column('has_biodiversity_action_plans', sa.Boolean, default=False),
        sa.Column('tnfd_disclosure', sa.Boolean, default=False),
        sa.Column('nature_positive_commitment_year', sa.Integer),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_energy_csrd_e4_entity', 'energy_csrd_e4_biodiversity', ['entity_id'])
    op.create_index('ix_energy_csrd_e4_year', 'energy_csrd_e4_biodiversity', ['reporting_year'])

    # =========================================================================
    # 8. ENERGY CSRD E5 CIRCULAR  (ESRS E5 — waste, hazardous materials)
    # =========================================================================
    op.create_table(
        'energy_csrd_e5_circular',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_id', UUID(as_uuid=True), sa.ForeignKey('energy_entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reporting_year', sa.Integer, nullable=False),

        # Waste generated (tonnes)
        sa.Column('total_waste_tonnes', sa.Numeric(14, 2)),
        sa.Column('hazardous_waste_tonnes', sa.Numeric(14, 2)),
        sa.Column('non_hazardous_waste_tonnes', sa.Numeric(14, 2)),
        sa.Column('radioactive_waste_tonnes', sa.Numeric(14, 2)),       # nuclear operators only

        # Waste fate
        sa.Column('waste_recycled_pct', sa.Numeric(5, 2)),
        sa.Column('waste_reused_pct', sa.Numeric(5, 2)),
        sa.Column('waste_energy_recovery_pct', sa.Numeric(5, 2)),
        sa.Column('waste_landfill_pct', sa.Numeric(5, 2)),
        sa.Column('waste_incineration_pct', sa.Numeric(5, 2)),

        # Energy-sector specific waste
        sa.Column('coal_ash_tonnes', sa.Numeric(14, 2)),               # fly ash + bottom ash
        sa.Column('coal_ash_recycled_pct', sa.Numeric(5, 2)),
        sa.Column('gypsum_tonnes', sa.Numeric(12, 2)),                  # FGD gypsum from coal desulphurisation
        sa.Column('wind_blade_recycled_pct', sa.Numeric(5, 2)),         # end-of-life wind blade recycling
        sa.Column('solar_panel_recycled_pct', sa.Numeric(5, 2)),
        sa.Column('battery_recycled_pct', sa.Numeric(5, 2)),            # BESS end-of-life

        # Circular economy
        sa.Column('circular_procurement_pct', sa.Numeric(5, 2)),        # % circular/recycled content in procurement
        sa.Column('waste_intensity_kg_per_gwh', sa.Numeric(10, 4)),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_energy_csrd_e5_entity', 'energy_csrd_e5_circular', ['entity_id'])
    op.create_index('ix_energy_csrd_e5_year', 'energy_csrd_e5_circular', ['reporting_year'])

    # =========================================================================
    # 9. ENERGY CSRD S1 WORKFORCE  (ESRS S1 — health & safety critical for energy)
    # =========================================================================
    op.create_table(
        'energy_csrd_s1_workforce',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_id', UUID(as_uuid=True), sa.ForeignKey('energy_entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reporting_year', sa.Integer, nullable=False),

        # Headcount
        sa.Column('total_headcount', sa.Integer),
        sa.Column('total_fte', sa.Numeric(10, 1)),
        sa.Column('employees_count', sa.Integer),
        sa.Column('contractors_count', sa.Integer),
        sa.Column('permanent_pct', sa.Numeric(5, 2)),
        sa.Column('female_pct', sa.Numeric(5, 2)),
        sa.Column('women_in_technical_roles_pct', sa.Numeric(5, 2)),   # STEM roles
        sa.Column('women_in_senior_leadership_pct', sa.Numeric(5, 2)),
        sa.Column('women_on_board_pct', sa.Numeric(5, 2)),
        sa.Column('headcount_by_country', JSONB),
        sa.Column('new_hires_count', sa.Integer),
        sa.Column('attrition_rate_pct', sa.Numeric(5, 2)),

        # Pay
        sa.Column('avg_salary_eur', sa.Numeric(10, 2)),
        sa.Column('unadjusted_gender_pay_gap_pct', sa.Numeric(5, 2)),
        sa.Column('ceo_pay_ratio', sa.Numeric(6, 1)),
        sa.Column('esg_linked_exec_pay_pct', sa.Numeric(5, 2)),
        sa.Column('collective_bargaining_coverage_pct', sa.Numeric(5, 2)),

        # ---- Health & Safety (CRITICAL for energy sector) ----
        sa.Column('fatalities_employees', sa.Integer, default=0),       # employee fatalities
        sa.Column('fatalities_contractors', sa.Integer, default=0),     # contractor fatalities
        sa.Column('lost_time_injuries_employees', sa.Integer, default=0),
        sa.Column('lost_time_injuries_contractors', sa.Integer, default=0),
        sa.Column('ltir_employees', sa.Numeric(7, 4)),                  # per million hours
        sa.Column('ltir_contractors', sa.Numeric(7, 4)),
        sa.Column('trir_employees', sa.Numeric(7, 4)),                  # Total Recordable Incident Rate
        sa.Column('trir_contractors', sa.Numeric(7, 4)),
        sa.Column('severity_rate', sa.Numeric(7, 4)),                   # days lost per accident
        sa.Column('work_related_ill_health_employees', sa.Integer),
        sa.Column('near_misses_reported', sa.Integer),
        sa.Column('safety_culture_score', sa.Numeric(4, 2)),            # internal safety maturity score

        # Process safety (major accident risk)
        sa.Column('process_safety_tier1_events', sa.Integer, default=0),   # API RP754 Tier 1
        sa.Column('process_safety_tier2_events', sa.Integer, default=0),   # API RP754 Tier 2
        sa.Column('fire_explosions', sa.Integer, default=0),
        sa.Column('environmental_incidents_major', sa.Integer, default=0),

        # Training
        sa.Column('safety_training_hours_avg', sa.Numeric(6, 2)),
        sa.Column('avg_training_hours_total', sa.Numeric(6, 2)),

        # Employee engagement
        sa.Column('engagement_score_pct', sa.Numeric(5, 2)),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_energy_csrd_s1_entity', 'energy_csrd_s1_workforce', ['entity_id'])
    op.create_index('ix_energy_csrd_s1_year', 'energy_csrd_s1_workforce', ['reporting_year'])

    # =========================================================================
    # 10. ENERGY CSRD G1 GOVERNANCE  (ESRS G1)
    # =========================================================================
    op.create_table(
        'energy_csrd_g1_governance',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_id', UUID(as_uuid=True), sa.ForeignKey('energy_entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reporting_year', sa.Integer, nullable=False),

        # Board
        sa.Column('board_members_total', sa.SmallInteger),
        sa.Column('board_independent_pct', sa.Numeric(5, 2)),
        sa.Column('board_female_pct', sa.Numeric(5, 2)),
        sa.Column('board_climate_expertise_count', sa.SmallInteger),
        sa.Column('sustainability_committee_in_place', sa.Boolean, default=True),
        sa.Column('board_meetings_per_year', sa.SmallInteger),
        sa.Column('ceo_cso_combined', sa.Boolean, default=False),       # Chief Sustainability Officer separate from CEO

        # Anti-corruption
        sa.Column('corruption_incidents', sa.Integer, default=0),
        sa.Column('regulatory_fines_meur', sa.Numeric(10, 2)),
        sa.Column('whistleblower_reports_received', sa.Integer),
        sa.Column('third_party_anti_corruption_audits', sa.Integer),

        # Lobbying
        sa.Column('lobbying_spend_meur', sa.Numeric(10, 2)),
        sa.Column('eu_transparency_register_id', sa.String(50)),
        sa.Column('policy_positions_published', sa.Boolean, default=False),

        # Tax
        sa.Column('effective_tax_rate_pct', sa.Numeric(5, 2)),
        sa.Column('country_by_country_reporting_published', sa.Boolean, default=False),

        # Supply chain
        sa.Column('supplier_esg_assessed_pct', sa.Numeric(5, 2)),      # % of tier 1 suppliers ESG assessed
        sa.Column('suppliers_with_violations_count', sa.Integer),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_energy_csrd_g1_entity', 'energy_csrd_g1_governance', ['entity_id'])
    op.create_index('ix_energy_csrd_g1_year', 'energy_csrd_g1_governance', ['reporting_year'])

    # =========================================================================
    # 11. ENERGY RENEWABLE PIPELINE  (development project register)
    # =========================================================================
    op.create_table(
        'energy_renewable_pipeline',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_id', UUID(as_uuid=True), sa.ForeignKey('energy_entities.id', ondelete='CASCADE'), nullable=False),

        sa.Column('project_name', sa.String(255), nullable=False),
        sa.Column('project_type', sa.String(30), nullable=False),       # wind_onshore | wind_offshore | solar_pv | solar_csp | hydro | battery | green_hydrogen | biomass | geothermal
        sa.Column('country_iso', sa.String(3), nullable=False),
        sa.Column('region', sa.String(100)),
        sa.Column('capacity_mw', sa.Numeric(10, 3), nullable=False),
        sa.Column('capacity_factor_pct', sa.Numeric(5, 2)),
        sa.Column('expected_generation_gwh_pa', sa.Numeric(10, 3)),
        sa.Column('co2_avoided_tco2e_pa', sa.Numeric(14, 4)),

        # Development stage
        sa.Column('stage', sa.String(30), nullable=False),              # early_development | permitting | consented | under_construction | commissioned
        sa.Column('cod_year', sa.Integer),                              # Commercial Operation Date
        sa.Column('grid_connection_year', sa.Integer),

        # Economics
        sa.Column('total_capex_meur', sa.Numeric(12, 2)),
        sa.Column('equity_capex_meur', sa.Numeric(12, 2)),
        sa.Column('project_irr_pct', sa.Numeric(6, 3)),
        sa.Column('equity_irr_pct', sa.Numeric(6, 3)),
        sa.Column('lcoe_eur_per_mwh', sa.Numeric(8, 2)),
        sa.Column('ppa_price_eur_per_mwh', sa.Numeric(8, 2)),
        sa.Column('ppa_term_years', sa.SmallInteger),
        sa.Column('ppa_counterparty', sa.String(100)),
        sa.Column('subsidy_type', sa.String(50)),                       # CfD | FiT | REC | none

        # EU Taxonomy alignment
        sa.Column('eu_taxonomy_aligned', sa.Boolean),
        sa.Column('taxonomy_objective', sa.SmallInteger, default=1),    # 1=climate mitigation

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.CheckConstraint("stage IN ('early_development','permitting','consented','under_construction','commissioned','decommissioned')", name='ck_energy_pipeline_stage'),
    )
    op.create_index('ix_energy_pipeline_entity', 'energy_renewable_pipeline', ['entity_id'])
    op.create_index('ix_energy_pipeline_type', 'energy_renewable_pipeline', ['project_type'])
    op.create_index('ix_energy_pipeline_country', 'energy_renewable_pipeline', ['country_iso'])
    op.create_index('ix_energy_pipeline_stage', 'energy_renewable_pipeline', ['stage'])
    op.create_index('ix_energy_pipeline_cod', 'energy_renewable_pipeline', ['cod_year'])

    # =========================================================================
    # 12. ENERGY STRANDED ASSETS  (fossil fuel plant stranding register)
    # =========================================================================
    op.create_table(
        'energy_stranded_assets_register',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_id', UUID(as_uuid=True), sa.ForeignKey('energy_entities.id', ondelete='CASCADE'), nullable=False),

        sa.Column('plant_name', sa.String(255), nullable=False),
        sa.Column('fuel_type', sa.String(30), nullable=False),          # coal | lignite | gas | oil
        sa.Column('country_iso', sa.String(3), nullable=False),
        sa.Column('capacity_mw', sa.Numeric(10, 3), nullable=False),
        sa.Column('year_commissioned', sa.Integer),
        sa.Column('original_decommission_year', sa.Integer),           # planned lifetime
        sa.Column('revised_decommission_year', sa.Integer),            # accelerated under transition plan
        sa.Column('early_closure_years', sa.Integer),                  # original − revised

        # Financial impact
        sa.Column('net_book_value_meur', sa.Numeric(12, 2)),
        sa.Column('impairment_recognised_meur', sa.Numeric(12, 2)),    # already booked
        sa.Column('residual_impairment_risk_meur', sa.Numeric(12, 2)),  # future risk
        sa.Column('decommissioning_provision_meur', sa.Numeric(12, 2)),
        sa.Column('annual_fcf_meur', sa.Numeric(12, 2)),               # free cash flow from plant

        # Carbon
        sa.Column('current_ci_gco2_kwh', sa.Numeric(8, 3)),
        sa.Column('annual_scope1_tco2e', sa.Numeric(14, 4)),
        sa.Column('annual_eu_ets_cost_meur', sa.Numeric(10, 2)),
        sa.Column('cumulative_eu_ets_cost_to_closure_meur', sa.Numeric(12, 2)),

        # Regulatory risk
        sa.Column('breaches_eu_ets_msfr', sa.Boolean, default=False),  # breaches Medium-term Sulphur, Flue Gas Regs
        sa.Column('below_mrbr_threshold', sa.Boolean, default=False),  # below Minimum Revenue Base Rate

        sa.Column('status', sa.String(20), default='operating'),        # operating | mothballed | under_decommission | decommissioned
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.CheckConstraint("fuel_type IN ('coal','lignite','gas','oil','peat','other_fossil')", name='ck_energy_stranded_fuel'),
        sa.CheckConstraint("status IN ('operating','mothballed','under_decommission','decommissioned','care_and_maintenance')", name='ck_energy_stranded_status'),
    )
    op.create_index('ix_energy_stranded_entity', 'energy_stranded_assets_register', ['entity_id'])
    op.create_index('ix_energy_stranded_fuel', 'energy_stranded_assets_register', ['fuel_type'])
    op.create_index('ix_energy_stranded_country', 'energy_stranded_assets_register', ['country_iso'])
    op.create_index('ix_energy_stranded_status', 'energy_stranded_assets_register', ['status'])


def downgrade():
    op.drop_table('energy_stranded_assets_register')
    op.drop_table('energy_renewable_pipeline')
    op.drop_table('energy_csrd_g1_governance')
    op.drop_table('energy_csrd_s1_workforce')
    op.drop_table('energy_csrd_e5_circular')
    op.drop_table('energy_csrd_e4_biodiversity')
    op.drop_table('energy_csrd_e3_water')
    op.drop_table('energy_csrd_e2_pollution')
    op.drop_table('energy_csrd_e1_climate')
    op.drop_table('energy_generation_mix')
    op.drop_table('energy_financials')
    op.drop_table('energy_entities')
