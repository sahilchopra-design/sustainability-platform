"""
Sprint 6 Seed Script — ECL/PCAF + Supply Chain Data
=====================================================
Populates:
  - ecl_assessments (3 runs: GS Article 8 Fund, Ørsted credit facility, RWE green bond)
  - ecl_exposures (8 exposures per assessment)
  - ecl_scenario_results (4 scenarios per assessment)
  - ecl_climate_overlays (3 climate scenarios per assessment)
  - pcaf_portfolios (3 PCAF portfolio entities)
  - pcaf_investees (8 investees: the GS Article 8 Fund holdings)
  - pcaf_portfolio_results (1 snapshot per portfolio)
  - temperature_scores (1 per portfolio)
  - sc_entities (10 corporate entities)
  - scope3_assessments (1 per sc_entity)
  - scope3_activities (8 category rows per assessment)
  - sbti_targets (for 6 entities with committed targets)
  - sbti_trajectories (2024-2035 per target)
  - emission_factor_library (30 reference EFs from DEFRA/IEA/EPA)
  - supply_chain_tiers (tier 1/2 suppliers per entity)

Data anchored to GS Portfolio Lead Analyst test case (€2B Article 8 fund).
WACI = 71.1 tCO2e/MEUR, Portfolio Temperature = 1.86°C
"""

import psycopg2
import uuid
import json
from datetime import date, datetime
from decimal import Decimal

DB_URL = "postgresql://postgres.kytzcbipsghprsqoalvi:KimiaAImpact2026@aws-1-us-east-2.pooler.supabase.com:5432/postgres"


def new_id():
    return str(uuid.uuid4())


def run():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    print("Sprint 6 seed starting...")

    # ==========================================================================
    # EMISSION FACTOR LIBRARY  (30 reference factors)
    # ==========================================================================
    print("  Seeding emission_factor_library...")
    ef_rows = [
        # Scope 2 electricity grid factors (IEA 2024)
        ("grid_electricity", "UK National Grid Average", 2, None, "CO2e", "GBR", None, 2024, 2025, 0.20700, "kgCO2e/kWh", "kWh", 5.0, 8.0, "secondary", "IEA", "https://www.iea.org/data-and-statistics/data-product/emissions-factors-2024", 2024, "2024", "AR6", "grid_mix", None, None, None, True),
        ("grid_electricity", "Germany National Grid Average", 2, None, "CO2e", "DEU", None, 2024, 2025, 0.38500, "kgCO2e/kWh", "kWh", 5.0, 8.0, "secondary", "IEA", "https://www.iea.org", 2024, "2024", "AR6", "grid_mix", None, None, None, True),
        ("grid_electricity", "France National Grid Average", 2, None, "CO2e", "FRA", None, 2024, 2025, 0.05600, "kgCO2e/kWh", "kWh", 3.0, 6.0, "secondary", "IEA", "https://www.iea.org", 2024, "2024", "AR6", "nuclear_mix", None, None, None, True),
        ("grid_electricity", "Netherlands National Grid Average", 2, None, "CO2e", "NLD", None, 2024, 2025, 0.28900, "kgCO2e/kWh", "kWh", 5.0, 8.0, "secondary", "IEA", "https://www.iea.org", 2024, "2024", "AR6", "gas_dominant", None, None, None, True),
        ("grid_electricity", "Norway National Grid Average", 2, None, "CO2e", "NOR", None, 2024, 2025, 0.01800, "kgCO2e/kWh", "kWh", 2.0, 4.0, "secondary", "IEA", "https://www.iea.org", 2024, "2024", "AR6", "hydro_dominant", None, None, None, True),
        ("grid_electricity", "Denmark National Grid Average", 2, None, "CO2e", "DNK", None, 2024, 2025, 0.13400, "kgCO2e/kWh", "kWh", 3.0, 6.0, "secondary", "IEA", "https://www.iea.org", 2024, "2024", "AR6", "wind_dominant", None, None, None, True),
        ("grid_electricity", "Sweden National Grid Average", 2, None, "CO2e", "SWE", None, 2024, 2025, 0.04100, "kgCO2e/kWh", "kWh", 2.0, 5.0, "secondary", "IEA", "https://www.iea.org", 2024, "2024", "AR6", "hydro_nuclear_mix", None, None, None, True),
        ("grid_electricity", "European Average", 2, None, "CO2e", None, "Europe", 2024, 2025, 0.25600, "kgCO2e/kWh", "kWh", 5.0, 10.0, "secondary", "IEA", "https://www.iea.org", 2024, "2024", "AR6", "grid_mix", None, None, None, True),

        # Scope 1 combustion factors (DEFRA 2024)
        ("natural_gas_combustion", "Natural Gas — DEFRA 2024", 1, None, "CO2e", "GBR", None, 2024, 2025, 2.02420, "kgCO2e/therm", "therm", 1.0, 3.0, "secondary", "DEFRA", "https://www.gov.uk/government/collections/government-conversion-factors-for-company-reporting", 2024, "2024", "AR6", None, "natural_gas", None, None, True),
        ("diesel_combustion_stationary", "Diesel — Stationary DEFRA 2024", 1, None, "CO2e", "GBR", None, 2024, 2025, 2.54620, "kgCO2e/litre", "litre", 1.0, 3.0, "secondary", "DEFRA", "https://www.gov.uk/government/collections/government-conversion-factors-for-company-reporting", 2024, "2024", "AR6", None, "diesel", None, None, True),
        ("coal_combustion", "Coal — Bituminous DEFRA 2024", 1, None, "CO2e", "GBR", None, 2024, 2025, 2.42296, "kgCO2e/kg", "kg", 2.0, 5.0, "secondary", "DEFRA", "https://www.gov.uk/government/collections/government-conversion-factors-for-company-reporting", 2024, "2024", "AR6", None, "coal", None, None, True),
        ("lpg_combustion", "LPG — DEFRA 2024", 1, None, "CO2e", "GBR", None, 2024, 2025, 1.54940, "kgCO2e/litre", "litre", 1.0, 3.0, "secondary", "DEFRA", "https://www.gov.uk/government/collections/government-conversion-factors-for-company-reporting", 2024, "2024", "AR6", None, "lpg", None, None, True),

        # Scope 3 transport (DEFRA 2024)
        ("air_travel", "Short Haul Economy < 3700km", 3, 6, "CO2e", None, "Global", 2024, 2025, 0.15353, "kgCO2e/pass-km", "pass-km", 5.0, 15.0, "secondary", "DEFRA", "https://www.gov.uk/government/collections/government-conversion-factors-for-company-reporting", 2024, "2024", "AR6", None, None, "air", 0.82, True),
        ("air_travel", "Long Haul Economy > 3700km", 3, 6, "CO2e", None, "Global", 2024, 2025, 0.19499, "kgCO2e/pass-km", "pass-km", 5.0, 15.0, "secondary", "DEFRA", "https://www.gov.uk/government/collections/government-conversion-factors-for-company-reporting", 2024, "2024", "AR6", None, None, "air", 0.82, True),
        ("road_freight", "HGV Diesel >17t, general freight", 3, 4, "CO2e", "GBR", None, 2024, 2025, 0.11217, "kgCO2e/tonne-km", "tonne-km", 5.0, 12.0, "secondary", "DEFRA", "https://www.gov.uk", 2024, "2024", "AR6", None, "diesel", "road", 0.58, True),
        ("sea_freight", "Container Ship — average", 3, 4, "CO2e", None, "Global", 2024, 2025, 0.01569, "kgCO2e/tonne-km", "tonne-km", 8.0, 20.0, "secondary", "DEFRA", "https://www.gov.uk", 2024, "2024", "AR6", None, "bunker_fuel", "sea", 0.70, True),
        ("rail_freight", "UK rail freight", 3, 4, "CO2e", "GBR", None, 2024, 2025, 0.02785, "kgCO2e/tonne-km", "tonne-km", 5.0, 10.0, "secondary", "DEFRA", "https://www.gov.uk", 2024, "2024", "AR6", None, "diesel_electric", "rail", 0.75, True),

        # Scope 3 upstream purchased goods (IEA / EPA EEIO)
        ("steel_production", "Steel — global average", 3, 1, "CO2e", None, "Global", 2023, 2026, 2.10000, "tCO2e/tonne", "tonne", 10.0, 25.0, "secondary", "IEA", "https://www.iea.org/reports/iron-and-steel-technology-roadmap", 2023, "2023", "AR6", "blast_furnace", "iron_ore", None, None, True),
        ("aluminium_production", "Aluminium — global average", 3, 1, "CO2e", None, "Global", 2023, 2026, 11.70000, "tCO2e/tonne", "tonne", 10.0, 30.0, "secondary", "IEA", "https://www.iea.org", 2023, "2023", "AR6", "primary_smelting", None, None, None, True),
        ("cement_production", "Cement — global average", 3, 1, "CO2e", None, "Global", 2023, 2026, 0.84000, "tCO2e/tonne", "tonne", 8.0, 15.0, "secondary", "IEA", "https://www.iea.org/reports/cement", 2023, "2023", "AR6", "wet_kiln", None, None, None, True),
        ("plastics_production", "Plastics — general thermoplastics", 3, 1, "CO2e", None, "Global", 2023, 2026, 3.10000, "tCO2e/tonne", "tonne", 10.0, 25.0, "secondary", "EPA", "https://cfpub.epa.gov/si/si_public_record_report.cfm?Lab=NRMRL&dirEntryId=336332", 2023, "2023", "AR6", "petrochemical", None, None, None, True),

        # Waste treatment (DEFRA 2024)
        ("waste_landfill", "Mixed waste to landfill", 3, 5, "CO2e", "GBR", None, 2024, 2025, 0.46700, "tCO2e/tonne", "tonne", 5.0, 15.0, "secondary", "DEFRA", "https://www.gov.uk", 2024, "2024", "AR6", None, None, None, None, True),
        ("waste_incineration", "Mixed waste to incineration", 3, 5, "CO2e", "GBR", None, 2024, 2025, 0.02100, "tCO2e/tonne", "tonne", 5.0, 15.0, "secondary", "DEFRA", "https://www.gov.uk", 2024, "2024", "AR6", None, None, None, None, True),
        ("waste_recycling", "Mixed waste to recycling", 3, 5, "CO2e", "GBR", None, 2024, 2025, -0.04900, "tCO2e/tonne", "tonne", 5.0, 10.0, "secondary", "DEFRA", "https://www.gov.uk", 2024, "2024", "AR6", None, None, None, None, True),

        # Water
        ("water_supply", "Water supply — UK", 3, 1, "CO2e", "GBR", None, 2024, 2025, 0.00149, "kgCO2e/litre", "litre", 5.0, 10.0, "secondary", "DEFRA", "https://www.gov.uk", 2024, "2024", "AR6", None, None, None, None, True),
        ("water_treatment", "Wastewater treatment — UK", 3, 5, "CO2e", "GBR", None, 2024, 2025, 0.00272, "kgCO2e/litre", "litre", 5.0, 10.0, "secondary", "DEFRA", "https://www.gov.uk", 2024, "2024", "AR6", None, None, None, None, True),

        # Spend-based upstream EEIO (EPA 2021 USEEIO)
        ("purchased_goods_services_spend", "General manufacturing — spend-based EEIO", 3, 1, "CO2e", "USA", None, 2021, 2026, 0.00042, "tCO2e/USD_spend", "USD", 25.0, 50.0, "proxy", "EPA", "https://cfpub.epa.gov/si/si_public_record_report.cfm?Lab=NRMRL&dirEntryId=349324", 2021, "2021", "AR6", None, None, None, None, True),
        ("professional_services_spend", "Professional services — spend-based EEIO", 3, 1, "CO2e", "USA", None, 2021, 2026, 0.00015, "tCO2e/USD_spend", "USD", 20.0, 40.0, "proxy", "EPA", "https://cfpub.epa.gov", 2021, "2021", "AR6", None, None, None, None, True),

        # Renewable energy EF (nearly zero)
        ("wind_generation", "Onshore Wind — lifecycle", 1, None, "CO2e", None, "Global", 2023, 2030, 0.00700, "kgCO2e/kWh", "kWh", 2.0, 5.0, "secondary", "IPCC", "https://www.ipcc.ch/site/assets/uploads/2018/02/ipcc_wg3_ar5_annex-ii.pdf", 2022, "AR6 WG3", "AR6", "onshore_wind", None, None, None, True),
        ("solar_pv_generation", "Solar PV — lifecycle", 1, None, "CO2e", None, "Global", 2023, 2030, 0.00500, "kgCO2e/kWh", "kWh", 2.0, 5.0, "secondary", "IPCC", "https://www.ipcc.ch", 2022, "AR6 WG3", "AR6", "solar_pv", None, None, None, True),
    ]

    ef_ids = {}
    for row in ef_rows:
        ef_id = new_id()
        (activity_type, activity_sub_type, scope, cat_num, ghg, country, region,
         valid_from, valid_to, factor_val, factor_unit, per_unit,
         unc_low, unc_high, dq_tier, source_name, source_url, source_year, source_ver, gwp_basis,
         tech_type, fuel_type, transport_mode, load_factor, is_active) = row

        cur.execute("""
            INSERT INTO emission_factor_library
              (id, activity_type, activity_sub_type, scope, category_number, ghg,
               country_iso, region, valid_from_year, valid_to_year,
               factor_value, factor_unit, factor_per_unit,
               uncertainty_low_pct, uncertainty_high_pct, data_quality_tier,
               source_name, source_url, source_year, source_version, gwp_basis,
               technology_type, fuel_type, transport_mode, load_factor, is_active)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (ef_id, activity_type, activity_sub_type, scope, cat_num, ghg,
              country, region, valid_from, valid_to,
              factor_val, factor_unit, per_unit,
              unc_low, unc_high, dq_tier,
              source_name, source_url, source_year, source_ver, gwp_basis,
              tech_type, fuel_type, transport_mode, load_factor, is_active))
        ef_ids[activity_type] = ef_id  # store first of each type

    conn.commit()
    print(f"    emission_factor_library: {len(ef_rows)} rows")

    # ==========================================================================
    # ECL ASSESSMENTS
    # ==========================================================================
    print("  Seeding ECL tables...")

    ecl_assessments = [
        {
            "id": new_id(),
            "entity_name": "GS Sustainable Finance Article 8 Fund",
            "reporting_date": date(2025, 12, 31),
            "pd_model": "logistic_regression",
            "lgd_model": "supervisory_lgd",
            "total_ead_gbp": 1_820_000_000,
            "total_ecl_gbp": 12_740_000,
            "ecl_rate_bps": 70.0,
            "stage1_ead_gbp": 1_456_000_000,
            "stage2_ead_gbp": 273_000_000,
            "stage3_ead_gbp": 91_000_000,
            "stage1_ecl_gbp": 3_640_000,
            "stage2_ecl_gbp": 5_460_000,
            "stage3_ecl_gbp": 3_640_000,
            "climate_ecl_uplift_gbp": 1_274_000,
            "climate_ecl_uplift_pct": 0.1000,
        },
        {
            "id": new_id(),
            "entity_name": "RWE AG Climate Transition Facility",
            "reporting_date": date(2025, 12, 31),
            "pd_model": "merton",
            "lgd_model": "market_lgd",
            "total_ead_gbp": 450_000_000,
            "total_ecl_gbp": 4_200_000,
            "ecl_rate_bps": 93.3,
            "stage1_ead_gbp": 360_000_000,
            "stage2_ead_gbp": 67_500_000,
            "stage3_ead_gbp": 22_500_000,
            "stage1_ecl_gbp": 900_000,
            "stage2_ecl_gbp": 1_800_000,
            "stage3_ecl_gbp": 1_500_000,
            "climate_ecl_uplift_gbp": 630_000,
            "climate_ecl_uplift_pct": 0.1500,
        },
        {
            "id": new_id(),
            "entity_name": "Ørsted Offshore Wind Project Finance",
            "reporting_date": date(2025, 12, 31),
            "pd_model": "vasicek",
            "lgd_model": "supervisory_lgd",
            "total_ead_gbp": 320_000_000,
            "total_ecl_gbp": 1_120_000,
            "ecl_rate_bps": 35.0,
            "stage1_ead_gbp": 288_000_000,
            "stage2_ead_gbp": 25_600_000,
            "stage3_ead_gbp": 6_400_000,
            "stage1_ecl_gbp": 576_000,
            "stage2_ecl_gbp": 384_000,
            "stage3_ecl_gbp": 160_000,
            "climate_ecl_uplift_gbp": 56_000,
            "climate_ecl_uplift_pct": 0.0500,
        },
    ]

    ecl_ids = {}
    for a in ecl_assessments:
        cur.execute("""
            INSERT INTO ecl_assessments
              (id, entity_name, reporting_date, pd_model, lgd_model, ead_approach,
               scenario_method, macroeconomic_vintage,
               total_ead_gbp, total_ecl_gbp, ecl_rate_bps,
               stage1_ead_gbp, stage2_ead_gbp, stage3_ead_gbp,
               stage1_ecl_gbp, stage2_ecl_gbp, stage3_ecl_gbp,
               climate_ecl_uplift_gbp, climate_ecl_uplift_pct, status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (a["id"], a["entity_name"], a["reporting_date"],
              a["pd_model"], a["lgd_model"], "outstanding_balance", "probability_weighted", "2025Q4",
              a["total_ead_gbp"], a["total_ecl_gbp"], a["ecl_rate_bps"],
              a["stage1_ead_gbp"], a["stage2_ead_gbp"], a["stage3_ead_gbp"],
              a["stage1_ecl_gbp"], a["stage2_ecl_gbp"], a["stage3_ecl_gbp"],
              a["climate_ecl_uplift_gbp"], a["climate_ecl_uplift_pct"], "approved"))
        ecl_ids[a["entity_name"]] = a["id"]

    conn.commit()

    # ECL Exposures — 8 GS fund holdings
    gs_holdings_ecl = [
        ("Shell plc", "NLD", "Energy", "corporate_loan", 275_000_000, 1, 0.002100, 0.35, 0.001200, 4.2, 2.1),
        ("TotalEnergies SE", "FRA", "Energy", "bond", 250_000_000, 1, 0.001900, 0.32, 0.001100, 4.0, 2.3),
        ("BP plc", "GBR", "Energy", "bond", 220_000_000, 2, 0.003800, 0.38, 0.002200, 5.8, 3.2),
        ("RWE AG", "DEU", "Utilities", "corporate_loan", 230_000_000, 1, 0.002400, 0.30, 0.001400, 3.9, 4.5),
        ("Vattenfall AB", "SWE", "Utilities", "corporate_loan", 180_000_000, 1, 0.001500, 0.28, 0.000900, 2.8, 2.9),
        ("Ørsted A/S", "DNK", "Utilities", "bond", 210_000_000, 1, 0.001800, 0.25, 0.001000, 2.1, 1.8),
        ("Equinor ASA", "NOR", "Energy", "bond", 240_000_000, 1, 0.002000, 0.33, 0.001150, 4.5, 2.2),
        ("Siemens Energy AG", "DEU", "Industrials", "revolving_credit", 215_000_000, 2, 0.004200, 0.40, 0.002500, 3.2, 3.8),
    ]

    gs_ecl_id = ecl_ids["GS Sustainable Finance Article 8 Fund"]
    for (obligor, country, sector, inst_type, balance, stage, pd_12m, lgd, ecl_12m, phys_risk, trans_risk) in gs_holdings_ecl:
        ead = balance
        ecl = ead * pd_12m * lgd if stage == 1 else ead * (pd_12m * 3) * lgd
        cur.execute("""
            INSERT INTO ecl_exposures
              (id, assessment_id, obligor_name, country_iso, sector_gics,
               instrument_type, outstanding_balance, ead, ifrs9_stage,
               internal_rating, pd_12m, lgd_pit, ecl_12m, ecl_recognised,
               discount_rate, physical_risk_score, transition_risk_score,
               climate_pd_uplift_bps, climate_lgd_uplift_bps)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (new_id(), gs_ecl_id, obligor, country, sector,
              inst_type, balance, ead, stage,
              "BBB" if stage == 1 else "BB",
              pd_12m, lgd, balance * pd_12m * lgd,
              balance * (pd_12m if stage == 1 else pd_12m * 3) * lgd,
              0.0450, phys_risk, trans_risk,
              round(pd_12m * 10000 * 0.15, 2), round(lgd * 10000 * 0.08, 2)))

    conn.commit()

    # ECL Scenario Results
    scenarios_ecl = [
        ("OPTIMISTIC", 0.20, 1.5, 3.2, 4.25, 5.0, 45.0, 2.0, 0.92, 0.18, 0.10),
        ("BASE", 0.50, 2.1, 4.1, 4.75, 2.5, 120.0, 3.5, 0.98, 0.72, 0.27),
        ("ADVERSE", 0.20, -0.8, 6.5, 5.25, -3.0, 280.0, 12.0, 1.12, 3.28, 1.47),
        ("SEVERE", 0.10, -2.5, 8.9, 5.75, -8.5, 480.0, 18.5, 1.24, 5.86, 2.94),
    ]

    for ecl_assess_id in ecl_ids.values():
        base_ead = 1_820_000_000 if "Article 8" in [k for k, v in ecl_ids.items() if v == ecl_assess_id][0] else 450_000_000
        for (scenario, weight, gdp, unemp, base_rate, hpi, spread, inflation,
             ecl_mult, s2_ecl, s3_ecl) in scenarios_ecl:
            total_ecl = base_ead * 0.007 * ecl_mult
            cur.execute("""
                INSERT INTO ecl_scenario_results
                  (id, assessment_id, scenario_name, scenario_weight,
                   gdp_growth_pct, unemployment_rate_pct, base_rate_pct,
                   hpi_growth_pct, credit_spread_bps, inflation_pct,
                   total_ead_gbp, total_ecl_gbp, ecl_rate_bps,
                   stage1_ecl_gbp, stage2_ecl_gbp, stage3_ecl_gbp)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (new_id(), ecl_assess_id, scenario, weight,
                  gdp, unemp, base_rate, hpi, spread, inflation,
                  base_ead, total_ecl, round(total_ecl / base_ead * 10000, 4),
                  total_ecl * 0.286, total_ecl * 0.429, total_ecl * 0.286))

    conn.commit()

    # ECL Climate Overlays
    climate_scenarios = [
        ("NGFS_NET_ZERO_2050", 30, 2025, 12.5, 8.0, 985_000, 0.054, 8.0, 5.5, 1_420_000, 0.078, 150, 600),
        ("NGFS_DELAYED_TRANSITION", 30, 2025, 18.0, 12.5, 1_580_000, 0.087, 12.0, 8.0, 2_240_000, 0.123, 200, 800),
        ("NGFS_HOT_HOUSE", 30, 2025, 35.0, 28.0, 4_200_000, 0.231, 22.0, 15.0, 5_600_000, 0.308, 350, 1200),
    ]

    for ecl_assess_id in ecl_ids.values():
        for (scenario, horizon, ref_year,
             phys_pd, phys_lgd, phys_ecl_uplift, phys_pct,
             trans_pd, trans_lgd, trans_ecl_uplift, trans_pct,
             cp_2030, cp_2050) in climate_scenarios:
            cur.execute("""
                INSERT INTO ecl_climate_overlays
                  (id, assessment_id, climate_scenario, horizon_years, reference_year,
                   physical_pd_uplift_avg_bps, physical_lgd_uplift_avg_bps,
                   physical_ecl_uplift_gbp, physical_ecl_uplift_pct,
                   transition_pd_uplift_avg_bps, transition_lgd_uplift_avg_bps,
                   transition_ecl_uplift_gbp, transition_ecl_uplift_pct,
                   total_climate_ecl_uplift_gbp, total_climate_ecl_uplift_pct,
                   ngfs_vintage, carbon_price_2030_usd, carbon_price_2050_usd)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (new_id(), ecl_assess_id, scenario, horizon, ref_year,
                  phys_pd, phys_lgd, phys_ecl_uplift, phys_pct,
                  trans_pd, trans_lgd, trans_ecl_uplift, trans_pct,
                  phys_ecl_uplift + trans_ecl_uplift, phys_pct + trans_pct,
                  "NGFS_v4.2", cp_2030, cp_2050))

    conn.commit()
    print("    ecl_assessments / exposures / scenario_results / climate_overlays: done")

    # ==========================================================================
    # PCAF PORTFOLIOS + INVESTEES + RESULTS
    # ==========================================================================
    print("  Seeding PCAF tables...")

    pcaf_port_id = new_id()
    cur.execute("""
        INSERT INTO pcaf_portfolios
          (id, entity_name, legal_entity_identifier, reporting_year,
           base_currency, portfolio_type,
           total_outstanding_gbp, total_enterprise_value_gbp, total_revenue_gbp,
           financed_scope1_tco2e, financed_scope2_tco2e, financed_scope3_tco2e,
           total_financed_emissions_tco2e,
           waci_tco2e_per_mrevenue, carbon_footprint_tco2e_per_mgbp_invested,
           portfolio_coverage_pct, pcaf_data_quality_score_avg,
           itr_1_5c_alignment_pct, itr_2c_alignment_pct, portfolio_temperature_c,
           base_year, base_year_emissions_tco2e, target_year, target_reduction_pct,
           status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (pcaf_port_id, "GS Sustainable Finance Article 8 Fund",
          "5967007LIEEXZXHY5693", 2025,
          "EUR", "listed_equity",
          1_820_000_000, 8_420_000_000, 12_850_000_000,
          42_150.4, 18_320.2, 68_941.8, 129_412.4,
          71.1, 71.1,
          91.3, 2.3,
          12.5, 37.5, 1.86,
          2019, 185_000.0, 2030, 45.0,
          "published"))

    # PCAF Investees — 8 GS Article 8 holdings
    # EVIC attribution: outstanding / EVIC
    investees = [
        # name, country, sector_gics, nace, outstanding, evic, equity, debt, revenue, s1, s2, s3, dq1, dq2, dq3, itr, sbti_committed, sbti_approved
        ("Shell plc", "NLD", "Energy — Integrated Oil & Gas", "B.06.10", 275_000_000, 1_920_000_000, 1_380_000_000, 540_000_000, 2_850_000_000, 56_200.0, 3_100.0, 148_500.0, 2, 2, 4, 1.95, True, True),
        ("TotalEnergies SE", "FRA", "Energy — Integrated Oil & Gas", "B.06.10", 250_000_000, 1_580_000_000, 1_120_000_000, 460_000_000, 2_420_000_000, 44_800.0, 2_600.0, 118_200.0, 2, 2, 4, 1.88, True, False),
        ("BP plc", "GBR", "Energy — Integrated Oil & Gas", "B.06.10", 220_000_000, 1_240_000_000, 860_000_000, 380_000_000, 1_980_000_000, 38_900.0, 2_100.0, 92_400.0, 2, 2, 3, 1.92, True, True),
        ("RWE AG", "DEU", "Utilities — Electric", "D.35.11", 230_000_000, 980_000_000, 640_000_000, 340_000_000, 1_420_000_000, 18_200.0, 4_800.0, 28_600.0, 1, 2, 3, 1.72, True, True),
        ("Vattenfall AB", "SWE", "Utilities — Electric", "D.35.11", 180_000_000, 560_000_000, 560_000_000, 0, 980_000_000, 9_800.0, 2_200.0, 14_400.0, 1, 1, 3, 1.68, True, True),
        ("Ørsted A/S", "DNK", "Utilities — Renewables", "D.35.11", 210_000_000, 680_000_000, 680_000_000, 0, 1_120_000_000, 4_200.0, 980.0, 8_400.0, 1, 1, 2, 1.52, True, True),
        ("Equinor ASA", "NOR", "Energy — E&P", "B.06.10", 240_000_000, 1_480_000_000, 1_100_000_000, 380_000_000, 2_180_000_000, 38_100.0, 1_820.0, 82_500.0, 2, 2, 4, 1.84, True, True),
        ("Siemens Energy AG", "DEU", "Industrials — Capital Goods", "C.27.11", 215_000_000, 580_000_000, 580_000_000, 0, 1_380_000_000, 3_200.0, 1_850.0, 12_400.0, 1, 2, 3, 1.75, True, False),
    ]

    for (name, country, sector_gics, nace, outstanding, evic, equity, debt, revenue,
         s1, s2, s3, dq1, dq2, dq3, itr, sbti_committed, sbti_approved) in investees:
        attrib = round(outstanding / evic, 6) if evic > 0 else 0.0
        fin_s1 = round(attrib * s1, 4)
        fin_s2 = round(attrib * s2, 4)
        fin_s3 = round(attrib * s3, 4)
        rev_intensity = round((s1 + s2 + s3) / (revenue / 1_000_000), 4)

        cur.execute("""
            INSERT INTO pcaf_investees
              (id, portfolio_id, investee_name, country_iso, sector_gics, nace_code,
               is_listed, outstanding_investment_gbp, enterprise_value_gbp,
               equity_market_cap_gbp, total_debt_gbp, revenue_gbp,
               attribution_factor, attribution_method,
               scope1_tco2e, scope2_market_tco2e, scope3_total_tco2e, total_emissions_tco2e,
               financed_scope1_tco2e, financed_scope2_tco2e, financed_scope3_tco2e,
               total_financed_emissions_tco2e,
               revenue_intensity_tco2e_per_mrevenue,
               pcaf_dq_scope1, pcaf_dq_scope2, pcaf_dq_scope3, pcaf_dq_composite,
               emissions_reporting_year, emissions_data_source, third_party_verified,
               implied_temperature_c, sbti_committed, sbti_approved, net_zero_target_year)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (new_id(), pcaf_port_id, name, country, sector_gics, nace,
              True, outstanding, evic, equity, debt, revenue,
              attrib, "evic",
              s1, s2, s3, s1 + s2 + s3,
              fin_s1, fin_s2, fin_s3, fin_s1 + fin_s2 + fin_s3,
              rev_intensity,
              dq1, dq2, dq3, round((dq1 + dq2 + dq3) / 3, 1),
              2024, "reported", True,
              itr, sbti_committed, sbti_approved,
              2050 if sbti_committed else None))

    # PCAF Portfolio Result snapshot
    cur.execute("""
        INSERT INTO pcaf_portfolio_results
          (id, portfolio_id, version,
           total_financed_scope1_tco2e, total_financed_scope2_tco2e,
           total_financed_scope3_tco2e, total_financed_emissions_tco2e,
           waci, carbon_footprint, portfolio_coverage_pct, weighted_avg_dq,
           portfolio_temperature_c, aligned_1_5c_pct, aligned_2c_pct, misaligned_pct,
           yoy_emissions_change_pct, vs_base_year_change_pct)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (new_id(), pcaf_port_id, 1,
          42_150.4, 18_320.2, 68_941.8, 129_412.4,
          71.1, 71.1, 91.3, 2.3,
          1.86, 12.5, 37.5, 50.0,
          -8.4, -30.2))

    # Temperature Score
    cur.execute("""
        INSERT INTO temperature_scores
          (id, portfolio_id, assessment_date, methodology, scope_coverage,
           aggregation_method, portfolio_temperature_c, portfolio_temperature_s1s2_c,
           pct_aligned_1_5c, pct_aligned_2c, pct_below_2c, pct_committed, pct_no_target,
           sbti_tool_version, timeframe)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (new_id(), pcaf_port_id, date(2025, 12, 31),
          "SBTi", "S1S2S3", "WATS",
          1.86, 1.72,
          12.5, 37.5, 75.0, 87.5, 12.5,
          "2.0", "long"))

    conn.commit()
    print("    pcaf_portfolios / pcaf_investees / results / temperature_scores: done")

    # ==========================================================================
    # SUPPLY CHAIN: SC_ENTITIES + SCOPE3 + SBTI + TIERS
    # ==========================================================================
    print("  Seeding Supply Chain tables...")

    sc_entities_data = [
        ("Shell plc", "NLD", "B.06.10", "Energy — Integrated Oil & Gas", 322_000_000_000, 103_000, True),
        ("TotalEnergies SE", "FRA", "B.06.10", "Energy — Integrated Oil & Gas", 218_000_000_000, 101_000, True),
        ("BP plc", "GBR", "B.06.10", "Energy — Integrated Oil & Gas", 162_000_000_000, 87_000, True),
        ("RWE AG", "DEU", "D.35.11", "Utilities — Electric", 47_000_000_000, 21_000, True),
        ("Vattenfall AB", "SWE", "D.35.11", "Utilities — Electric", 26_000_000_000, 20_000, False),
        ("Ørsted A/S", "DNK", "D.35.11", "Utilities — Renewables", 18_000_000_000, 8_800, True),
        ("Equinor ASA", "NOR", "B.06.10", "Energy — E&P", 145_000_000_000, 22_000, True),
        ("Siemens Energy AG", "DEU", "C.27.11", "Industrials — Capital Goods", 38_000_000_000, 99_000, True),
        ("Vestas Wind Systems A/S", "DNK", "C.28.11", "Industrials — Wind Turbines", 16_000_000_000, 29_000, True),
        ("Schneider Electric SE", "FRA", "C.27.12", "Industrials — Electrical Equipment", 38_000_000_000, 150_000, True),
    ]

    sc_entity_ids = {}
    for (name, country, nace, sector, revenue, headcount, is_listed) in sc_entities_data:
        eid = new_id()
        cur.execute("""
            INSERT INTO sc_entities
              (id, legal_name, country_iso, nace_code, sector_gics,
               annual_revenue_gbp, headcount, is_listed, entity_type, fiscal_year_end)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (eid, name, country, nace, sector, revenue, headcount, is_listed, "corporate", "12-31"))
        sc_entity_ids[name] = eid

    conn.commit()

    # Scope3 Assessments — one per entity
    scope3_data = [
        # name, s1, s2_mkt, cat1, cat3, cat4, cat6, cat7, cat11, cat15, s3_total
        ("Shell plc", 56_200_000, 3_100_000, 28_420_000, 8_150_000, 4_820_000, 580_000, 290_000, 148_500_000, 0, 198_200_000),
        ("TotalEnergies SE", 44_800_000, 2_600_000, 22_800_000, 6_400_000, 3_850_000, 480_000, 240_000, 118_200_000, 0, 159_100_000),
        ("BP plc", 38_900_000, 2_100_000, 19_200_000, 5_600_000, 3_200_000, 420_000, 210_000, 92_400_000, 0, 128_900_000),
        ("RWE AG", 18_200_000, 4_800_000, 4_200_000, 12_800_000, 1_840_000, 180_000, 90_000, 0, 28_600_000, 52_800_000),
        ("Vattenfall AB", 9_800_000, 2_200_000, 2_100_000, 6_200_000, 980_000, 95_000, 48_000, 0, 14_400_000, 28_600_000),
        ("Ørsted A/S", 4_200_000, 980_000, 1_820_000, 2_400_000, 420_000, 42_000, 21_000, 0, 8_400_000, 14_200_000),
        ("Equinor ASA", 38_100_000, 1_820_000, 19_800_000, 5_200_000, 3_480_000, 385_000, 195_000, 82_500_000, 0, 118_200_000),
        ("Siemens Energy AG", 3_200_000, 1_850_000, 8_600_000, 4_800_000, 2_200_000, 320_000, 160_000, 0, 12_400_000, 32_800_000),
        ("Vestas Wind Systems A/S", 1_800_000, 920_000, 4_200_000, 2_800_000, 1_400_000, 180_000, 90_000, 0, 0, 12_400_000),
        ("Schneider Electric SE", 1_200_000, 1_480_000, 5_800_000, 3_600_000, 1_800_000, 240_000, 120_000, 0, 0, 14_800_000),
    ]

    scope3_ids = {}
    for (name, s1, s2_mkt, cat1, cat3, cat4, cat6, cat7, cat11, cat15, s3_total) in scope3_data:
        eid = sc_entity_ids[name]
        rev_intensity = round((s1 + s2_mkt + s3_total) / (1_000_000), 4)  # approximate
        s3id = new_id()
        cur.execute("""
            INSERT INTO scope3_assessments
              (id, entity_id, entity_name, reporting_year, base_currency,
               calculation_approach, scope1_tco2e, scope2_market_tco2e,
               cat1_purchased_goods_tco2e, cat3_fuel_energy_tco2e, cat4_upstream_transport_tco2e,
               cat6_business_travel_tco2e, cat7_employee_commuting_tco2e,
               cat11_use_of_sold_products_tco2e, cat15_investments_tco2e,
               total_scope3_tco2e, total_scope123_tco2e,
               data_quality_score_avg, primary_data_pct, coverage_completeness_pct,
               categories_included, boundary, assurance_type, status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (s3id, eid, name, 2024, "GBP",
              "activity_based", s1, s2_mkt,
              cat1, cat3, cat4, cat6, cat7, cat11, cat15,
              s3_total, s1 + s2_mkt + s3_total,
              2.5, 45.0, 80.0,
              json.dumps([1, 3, 4, 6, 7, 11, 15]),
              "operational_control", "limited", "published"))
        scope3_ids[name] = s3id

    conn.commit()

    # Scope3 Activities — sampled rows per entity (2 per entity = 20 total)
    for (name, s1, s2_mkt, cat1, cat3, cat4, cat6, cat7, cat11, cat15, s3_total) in scope3_data[:5]:
        s3id = scope3_ids[name]
        # Cat 1 purchased goods row
        if cat1 > 0:
            cur.execute("""
                INSERT INTO scope3_activities
                  (id, assessment_id, category_number, category_label, sub_category,
                   activity_description, activity_quantity, activity_unit,
                   data_source, emission_factor_value, emission_factor_unit,
                   emission_factor_source, emission_factor_year, global_warming_potential,
                   co2e_tco2e, pcaf_dq_score, ghg_protocol_dq_tier)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (new_id(), s3id, 1, "Purchased Goods & Services", "Steel and metals",
                  "Structural steel for infrastructure and processing facilities",
                  round(cat1 / 2.1, 0), "tonne",
                  "supplier_reported", 2.10, "tCO2e/tonne",
                  "IEA", 2023, "AR6",
                  cat1 / 1e6, 2, "secondary"))
        # Cat 6 business travel row
        if cat6 > 0:
            cur.execute("""
                INSERT INTO scope3_activities
                  (id, assessment_id, category_number, category_label, sub_category,
                   activity_description, activity_quantity, activity_unit,
                   data_source, emission_factor_value, emission_factor_unit,
                   emission_factor_source, emission_factor_year, global_warming_potential,
                   co2e_tco2e, pcaf_dq_score, ghg_protocol_dq_tier)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (new_id(), s3id, 6, "Business Travel", "Long haul air travel",
                  "Executive and operational air travel",
                  round(cat6 / 0.195, 0), "pass-km",
                  "invoiced", 0.195, "kgCO2e/pass-km",
                  "DEFRA", 2024, "AR6",
                  cat6 / 1e6, 2, "secondary"))

    conn.commit()

    # SBTi Targets (for 7 of 10 entities)
    sbti_target_data = [
        ("Shell plc", "near_term", "1.5C_absolute", "S1S2", "approved", 2019, 68_600_000, 2030, 30.0, 2050, 90.0),
        ("TotalEnergies SE", "near_term", "1.5C_absolute", "S1S2", "approved", 2015, 55_200_000, 2030, 25.0, 2050, 90.0),
        ("RWE AG", "net_zero", "1.5C_absolute", "S1S2S3", "committed", 2019, 24_200_000, 2030, 40.0, 2040, 95.0),
        ("Vattenfall AB", "net_zero", "1.5C_absolute", "S1S2S3", "approved", 2019, 13_200_000, 2030, 35.0, 2045, 95.0),
        ("Ørsted A/S", "net_zero", "1.5C_absolute", "S1S2S3", "approved", 2019, 6_800_000, 2030, 50.0, 2040, 99.0),
        ("Equinor ASA", "near_term", "1.5C_absolute", "S1S2", "approved", 2019, 44_600_000, 2030, 50.0, 2050, 90.0),
        ("Siemens Energy AG", "near_term", "1.5C_absolute", "S1S2S3", "committed", 2019, 7_100_000, 2030, 45.0, 2050, 90.0),
    ]

    sbti_ids = {}
    for (name, ttype, pathway, scope, status, base_yr, base_tco2e, nt_yr, nt_pct, lt_yr, lt_pct) in sbti_target_data:
        if name not in sc_entity_ids:
            continue
        eid = sc_entity_ids[name]
        tid = new_id()
        nt_target = round(base_tco2e * (1 - nt_pct / 100), 4)
        lt_target = round(base_tco2e * (1 - lt_pct / 100), 4)
        cur.execute("""
            INSERT INTO sbti_targets
              (id, entity_id, entity_name, target_type, sbti_pathway, scope_coverage,
               sbti_status, base_year, base_year_total_tco2e,
               near_term_target_year, near_term_reduction_pct, near_term_target_tco2e,
               long_term_target_year, long_term_reduction_pct, long_term_target_tco2e,
               near_term_annual_reduction_rate_pct, long_term_annual_reduction_rate_pct,
               sbti_submission_date, sbti_approval_date, sbti_tool_version)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (tid, eid, name, ttype, pathway, scope, status,
              base_yr, base_tco2e, nt_yr, nt_pct, nt_target,
              lt_yr, lt_pct, lt_target,
              round(nt_pct / (nt_yr - base_yr), 4),
              round(lt_pct / (lt_yr - base_yr), 4),
              date(2021, 9, 1), date(2022, 3, 15) if status == "approved" else None,
              "2.0.0"))
        sbti_ids[name] = tid

    conn.commit()

    # SBTi Trajectories (2024-2035 per target)
    for (name, ttype, pathway, scope, status, base_yr, base_tco2e, nt_yr, nt_pct, lt_yr, lt_pct) in sbti_target_data:
        if name not in sbti_ids:
            continue
        tid = sbti_ids[name]
        annual_rate = nt_pct / (nt_yr - base_yr) / 100
        for year in range(2024, 2036):
            years_from_base = year - base_yr
            target_tco2e = round(base_tco2e * (1 - annual_rate) ** years_from_base, 4)
            benchmark_1_5 = round(base_tco2e * (1 - 0.042) ** years_from_base, 4)
            benchmark_2c = round(base_tco2e * (1 - 0.025) ** years_from_base, 4)
            actual = round(target_tco2e * (0.95 + (year - 2024) * 0.01), 4) if year <= 2025 else None
            on_track = True if actual and actual <= target_tco2e else None
            cur.execute("""
                INSERT INTO sbti_trajectories
                  (id, target_id, year, target_emissions_tco2e, cumulative_reduction_pct,
                   actual_emissions_tco2e, is_on_track, benchmark_1_5c_tco2e, benchmark_2c_tco2e)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (new_id(), tid, year, target_tco2e,
                  round((base_tco2e - target_tco2e) / base_tco2e * 100, 4),
                  actual, on_track, benchmark_1_5, benchmark_2c))

    conn.commit()

    # Supply Chain Tiers — tier 1 suppliers for top 3 entities
    tier1_suppliers = [
        # (buyer_name, supplier_name, country, sector, tier, spend_gbp, scope12_tco2e, has_sbti, has_cdp, dq)
        ("Shell plc", "Baker Hughes Co", "USA", "Energy Equipment", 1, 2_840_000_000, 4_200_000, True, True, 2),
        ("Shell plc", "TechnipFMC plc", "FRA", "Energy Equipment", 1, 1_920_000_000, 1_800_000, False, True, 3),
        ("Shell plc", "SLB (Schlumberger)", "USA", "Oil Services", 1, 3_650_000_000, 3_600_000, True, True, 2),
        ("RWE AG", "Vestas Wind Systems A/S", "DNK", "Wind Turbines", 1, 980_000_000, 2_700_000, True, True, 2),
        ("RWE AG", "Siemens Gamesa Renewable Energy", "DEU", "Wind Turbines", 1, 1_240_000_000, 3_100_000, True, True, 2),
        ("Ørsted A/S", "Vestas Wind Systems A/S", "DNK", "Wind Turbines", 1, 640_000_000, 1_800_000, True, True, 2),
        ("Ørsted A/S", "Nexans SA", "FRA", "Subsea Cables", 1, 420_000_000, 1_200_000, False, False, 3),
    ]

    for (buyer, supplier, s_country, s_sector, tier, spend, scope12, has_sbti, has_cdp, dq) in tier1_suppliers:
        if buyer not in sc_entity_ids:
            continue
        buyer_id = sc_entity_ids[buyer]
        attrib_scope3 = round(spend / 1_000_000_000 * scope12 * 0.15, 4)
        cur.execute("""
            INSERT INTO supply_chain_tiers
              (id, buyer_entity_id, buyer_entity_name, supplier_name,
               supplier_country_iso, supplier_sector_gics, tier, spend_gbp,
               scope12_tco2e, attributed_scope3_tco2e,
               emissions_data_source, pcaf_dq_score, reporting_year,
               has_sbti_target, has_cdp_disclosure,
               engagement_status, high_emission_flag)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (new_id(), buyer_id, buyer, supplier,
              s_country, s_sector, tier, spend,
              scope12, attrib_scope3,
              "supplier_reported", dq, 2024,
              has_sbti, has_cdp,
              "committed" if has_sbti else "contacted",
              scope12 > 3_000_000))

    conn.commit()
    print("    sc_entities / scope3 / sbti / supply_chain_tiers: done")

    # Verify
    for tbl in ["emission_factor_library", "ecl_assessments", "ecl_exposures",
                "ecl_scenario_results", "ecl_climate_overlays",
                "pcaf_portfolios", "pcaf_investees", "pcaf_portfolio_results",
                "temperature_scores", "sc_entities", "scope3_assessments",
                "scope3_activities", "sbti_targets", "sbti_trajectories",
                "supply_chain_tiers"]:
        cur.execute(f"SELECT COUNT(*) FROM {tbl}")
        print(f"    {tbl}: {cur.fetchone()[0]} rows")

    conn.close()
    print("\nSprint 6 seed COMPLETE.")


if __name__ == "__main__":
    run()
