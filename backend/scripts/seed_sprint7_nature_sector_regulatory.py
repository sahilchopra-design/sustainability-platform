"""
Sprint 7 Seed Script — Nature Risk + Sector Assessments + Regulatory
=====================================================================
Populates:
  Nature Risk (migration 010):
  - nature_assessments (TNFD LEAP for 6 energy/RE assets)

  Sector Assessments (migration 008):
  - data_centre_facilities  (4 hyperscale/enterprise DCs)
  - data_centre_assessments (1 per facility, 2024 and 2023)
  - cat_risk_properties     (8 properties across EU/UK)
  - cat_risk_assessments    (flood + windstorm per property)
  - cat_risk_climate_scenarios (2 climate scenarios per CAT assessment)
  - power_plants            (8 plants: coal, CCGT, offshore wind, solar)
  - power_plant_assessments (1 per plant)
  - power_plant_trajectories (2025-2040 per plant)

  Regulatory (migration 009):
  - regulatory_entities     (6 entities: 3 asset managers, 2 banks, 1 corporate)
  - sfdr_pai_disclosures    (1 per Article 8/9 fund)
  - eu_taxonomy_assessments (1 per corporate/bank)
  - eu_taxonomy_activities  (3 activities per assessment)
  - tcfd_assessments        (1 per entity)
  - csrd_readiness_assessments (1 per entity)
  - issb_assessments        (1 per entity)
"""

import psycopg2
import uuid
import json
from datetime import date

DB_URL = "postgresql://postgres.kytzcbipsghprsqoalvi:KimiaAImpact2026@aws-1-us-east-2.pooler.supabase.com:5432/postgres"


def new_id():
    return str(uuid.uuid4())


def run():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    print("Sprint 7 seed starting...")

    # ==========================================================================
    # NATURE ASSESSMENTS (TNFD LEAP)
    # ==========================================================================
    print("  Seeding nature_assessments...")

    nature_data = [
        # asset_name, country, lat, lng, biome, area_ha, protected_5km, kba, ramsar
        ("Shell Pernis Refinery, Rotterdam", "NLD", 51.8870, 4.3690, "temperate_broadleaf_forest", 420.0, True, False, True),
        ("RWE Lignite Mining, Rhineland", "DEU", 50.9300, 6.4200, "temperate_grassland", 1850.0, True, True, False),
        ("Ørsted Hornsea 2 OWF", "GBR", 54.0600, 1.7500, "marine_and_coastal", 260.0, False, True, False),
        ("Equinor Hammerfest LNG", "NOR", 70.6600, 23.6800, "boreal_forest", 185.0, True, False, False),
        ("TotalEnergies Lacq Gas Field", "FRA", 43.4100, -0.6100, "mediterranean_forest", 320.0, False, False, True),
        ("Vattenfall Vattenfall Barsebäck", "SWE", 55.7500, 12.8700, "temperate_broadleaf_forest", 95.0, True, False, False),
    ]

    for (name, country, lat, lng, biome, area, prot, kba, ramsar) in nature_data:
        cur.execute("""
            INSERT INTO nature_assessments
              (id, asset_name, assessment_date, assessment_framework,
               latitude, longitude, country_iso, site_area_ha,
               protected_area_within_5km, key_biodiversity_area, ramsar_wetland,
               biome,
               locate_ecosystem_services,
               evaluate_dependencies,
               evaluate_impacts)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            new_id(), name, date(2025, 6, 30), "TNFD_LEAP_v1.1",
            lat, lng, country, area,
            prot, kba, ramsar, biome,
            json.dumps({
                "water_purification": {"dependency": "high", "score": 0.72},
                "flood_regulation": {"dependency": "medium", "score": 0.45},
                "pollination": {"dependency": "low", "score": 0.18},
                "carbon_sequestration": {"dependency": "medium", "score": 0.55},
            }),
            json.dumps([
                {"service": "freshwater_availability", "magnitude": "high", "trend": "declining"},
                {"service": "soil_quality", "magnitude": "medium", "trend": "stable"},
            ]),
            json.dumps([
                {"driver": "land_use_change", "magnitude": 6.2, "probability": 0.55, "financial_impact_usd": 4_200_000},
                {"driver": "water_pollution", "magnitude": 4.1, "probability": 0.35, "financial_impact_usd": 1_800_000},
                {"driver": "climate_change", "magnitude": 5.8, "probability": 0.75, "financial_impact_usd": 8_500_000},
            ]),
        ))

    conn.commit()
    print(f"    nature_assessments: {len(nature_data)} rows")

    # ==========================================================================
    # DATA CENTRE FACILITIES + ASSESSMENTS
    # ==========================================================================
    print("  Seeding data_centre_facilities + assessments...")

    dc_data = [
        ("Microsoft Azure West Europe", "Microsoft Corporation", "hyperscale", "Amsterdam, Netherlands", "Amsterdam", "NLD", 52.3676, 4.9041, "AMS", 48000, 35000, 120.0, 160.0, 2018, "Tier IV", "liquid"),
        ("Google Cloud europe-west4", "Google LLC", "hyperscale", "Eemshaven, Netherlands", "Eemshaven", "NLD", 53.4355, 6.8343, "NL", 42000, 30000, 95.0, 130.0, 2016, "Tier IV", "liquid"),
        ("Equinix AM5 Amsterdam", "Equinix Inc", "colocation", "Amsterdam, Netherlands", "Amsterdam", "NLD", 52.3580, 4.8960, "AMS", 12000, 8500, 18.0, 22.0, 2010, "Tier III", "air"),
        ("Deutsche Telekom DCO Frankfurt", "Deutsche Telekom AG", "enterprise", "Frankfurt, Germany", "Frankfurt", "DEU", 50.1109, 8.6821, "DE_TENNET", 8500, 6000, 12.0, 15.0, 2015, "Tier III", "adiabatic"),
    ]

    dc_ids = {}
    for (name, op, ftype, addr, city, country, lat, lng, grid, floor_m2, white_m2, it_mw, inst_mw, yr, tier, cool) in dc_data:
        did = new_id()
        cur.execute("""
            INSERT INTO data_centre_facilities
              (id, facility_name, operator_name, facility_type, address, city,
               country_iso, latitude, longitude, grid_region,
               total_floor_area_m2, white_space_m2, design_it_load_mw, installed_capacity_mw,
               year_built, tier_classification, cooling_type, is_active)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (did, name, op, ftype, addr, city, country, lat, lng, grid,
              floor_m2, white_m2, it_mw, inst_mw, yr, tier, cool, True))
        dc_ids[name] = did

    conn.commit()

    # Assessments — 2024 per facility
    dc_assess_data = [
        # name, it_load_mw, it_kwh, facility_kwh, pue, cue, wue, rer, ren_pct, ren_mwh, grid_ef, co2e, scope2, score, rating
        ("Microsoft Azure West Europe", 105.2, 921_552_000, 1_013_707_200, 1.099, 0.0234, 0.285, 0.978, 97.8, 900_802_000, 0.2070, 21_022, 4_558, 94.2, "A"),
        ("Google Cloud europe-west4", 88.4, 774_384_000, 851_822_400, 1.100, 0.0025, 0.180, 0.999, 99.9, 851_000_000, 0.2070, 1_763, 421, 96.8, "A+"),
        ("Equinix AM5 Amsterdam", 14.2, 124_392_000, 172_503_600, 1.387, 0.0328, 0.420, 0.620, 62.0, 106_952_000, 0.2070, 5_657, 4_186, 71.4, "B"),
        ("Deutsche Telekom DCO Frankfurt", 9.8, 85_848_000, 120_187_200, 1.400, 0.0556, 0.480, 0.480, 48.0, 57_689_000, 0.3850, 33_072, 24_531, 64.8, "C"),
    ]

    for (name, it_mw, it_kwh, fac_kwh, pue, cue, wue, rer, ren_pct, ren_mwh, grid_ef, co2e, scope2, score, rating) in dc_assess_data:
        dcid = dc_ids[name]
        cur.execute("""
            INSERT INTO data_centre_assessments
              (id, facility_id, facility_name, assessment_year, assessment_period,
               total_it_load_mw, total_it_load_kwh, total_facility_kwh,
               annual_energy_consumption_mwh,
               pue, pue_target, pue_industry_avg, cue, wue, wue_target, rer, gear,
               renewable_energy_pct, renewable_energy_mwh,
               has_renewable_ppa, has_rec_certificates,
               grid_emission_factor_kgco2e_kwh, carbon_intensity_kgco2e_kwh_it,
               annual_co2e_tco2e, scope2_market_tco2e,
               efficiency_score, efficiency_rating, benchmark_percentile, status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            new_id(), dcid, name, 2024, "annual",
            it_mw, it_kwh, fac_kwh,
            fac_kwh / 1000,
            pue, pue * 0.90, 1.58, cue, wue, wue * 0.85, rer, rer * 0.95,
            ren_pct, ren_mwh / 1000,
            ren_pct > 80, ren_pct > 60,
            grid_ef, cue, co2e, scope2,
            score, rating, min(score, 100), "published"
        ))

    conn.commit()
    print(f"    data_centre_facilities: {len(dc_ids)}, data_centre_assessments: {len(dc_ids)}")

    # ==========================================================================
    # CAT RISK PROPERTIES + ASSESSMENTS + CLIMATE SCENARIOS
    # ==========================================================================
    print("  Seeding cat_risk tables...")

    cat_props = [
        # ref, name, type, city, country, lat, lng, elev, construction, yr, storeys, area, repl_value, mkt_value, insured
        ("CAT-001", "Canary Wharf HSBC Tower", "commercial_office", "London", "GBR", 51.5031, -0.0200, 4.2, "steel", 2002, 45, 58_200, 285_000_000, 242_000_000, 220_000_000),
        ("CAT-002", "Dresden Retail Complex", "retail", "Dresden", "DEU", 51.0504, 13.7373, 112.5, "concrete", 1998, 3, 32_000, 48_000_000, 41_000_000, 38_000_000),
        ("CAT-003", "Rotterdam Warehouse Logistics", "industrial", "Rotterdam", "NLD", 51.9244, 4.4777, 0.8, "steel", 2012, 1, 85_000, 62_000_000, 55_000_000, 52_000_000),
        ("CAT-004", "Hamburg Residential Block", "residential", "Hamburg", "DEU", 53.5753, 9.9957, 8.4, "masonry", 1975, 8, 12_500, 22_000_000, 18_500_000, 16_000_000),
        ("CAT-005", "Madrid Office Park", "commercial_office", "Madrid", "ESP", 40.4168, -3.7038, 667.0, "concrete", 2008, 6, 28_000, 71_000_000, 65_000_000, 60_000_000),
        ("CAT-006", "Amsterdam Canal Retail", "retail", "Amsterdam", "NLD", 52.3702, 4.8952, 1.2, "masonry", 1895, 4, 4_800, 12_000_000, 9_800_000, 8_500_000),
        ("CAT-007", "Zurich Data Centre", "data_centre", "Zurich", "CHE", 47.3769, 8.5417, 408.0, "concrete", 2015, 3, 15_000, 45_000_000, 41_000_000, 40_000_000),
        ("CAT-008", "Bristol Multifamily Residential", "residential", "Bristol", "GBR", 51.4545, -2.5879, 42.0, "masonry", 1988, 5, 9_200, 18_500_000, 16_000_000, 14_000_000),
    ]

    cat_prop_ids = {}
    for (ref, name, ptype, city, country, lat, lng, elev, constr, yr, storeys, area, repl, mkt, insured) in cat_props:
        pid = new_id()
        cur.execute("""
            INSERT INTO cat_risk_properties
              (id, property_reference, property_name, property_type,
               city, country_iso, latitude, longitude, elevation_m,
               construction_type, construction_year, number_of_storeys, floor_area_m2,
               replacement_value_gbp, market_value_gbp, insured_value_gbp, is_active)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (pid, ref, name, ptype, city, country, lat, lng, elev,
              constr, yr, storeys, area, repl, mkt, insured, True))
        cat_prop_ids[ref] = pid

    conn.commit()

    # CAT Risk Assessments — flood and windstorm for each property
    perils_data = [
        # (ref, peril, model_vendor, prop_val, aal, aal_pct, 100yr_loss, 250yr_loss, 500yr_loss, vuln_class)
        ("CAT-001", "flood", "JBA", 285_000_000, 285_000, 0.10, 5_700_000, 9_975_000, 14_250_000, "low"),
        ("CAT-001", "windstorm", "RMS", 285_000_000, 570_000, 0.20, 8_550_000, 14_250_000, 19_950_000, "low"),
        ("CAT-002", "flood", "JBA", 48_000_000, 720_000, 1.50, 7_200_000, 10_560_000, 14_400_000, "medium"),
        ("CAT-002", "windstorm", "RMS", 48_000_000, 480_000, 1.00, 5_760_000, 8_640_000, 12_000_000, "low"),
        ("CAT-003", "flood", "JBA", 62_000_000, 1_860_000, 3.00, 12_400_000, 18_600_000, 24_800_000, "high"),
        ("CAT-003", "windstorm", "RMS", 62_000_000, 620_000, 1.00, 7_440_000, 10_540_000, 14_880_000, "low"),
        ("CAT-004", "flood", "JBA", 22_000_000, 440_000, 2.00, 4_400_000, 6_600_000, 8_800_000, "medium"),
        ("CAT-005", "windstorm", "AIR_Verisk", 71_000_000, 355_000, 0.50, 4_970_000, 7_810_000, 10_650_000, "low"),
        ("CAT-006", "flood", "JBA", 12_000_000, 600_000, 5.00, 5_400_000, 7_800_000, 9_600_000, "very_high"),
        ("CAT-007", "flood", "JBA", 45_000_000, 450_000, 1.00, 3_150_000, 4_950_000, 6_750_000, "low"),
        ("CAT-008", "flood", "JBA", 18_500_000, 555_000, 3.00, 4_625_000, 6_475_000, 8_325_000, "medium"),
        ("CAT-008", "windstorm", "RMS", 18_500_000, 370_000, 2.00, 3_700_000, 5_550_000, 7_400_000, "medium"),
    ]

    cat_assess_ids = {}
    for (ref, peril, vendor, prop_val, aal, aal_pct, loss_100, loss_250, loss_500, vuln) in perils_data:
        pid = cat_prop_ids[ref]
        aid = new_id()
        cur.execute("""
            INSERT INTO cat_risk_assessments
              (id, property_id, property_reference, assessment_date, peril,
               cat_model_vendor, cat_model_version, exceedance_probability_method,
               property_value_gbp, aal_gbp, aal_pct_of_value,
               loss_1in100yr_gbp, loss_1in250yr_gbp, loss_1in500yr_gbp,
               damage_ratio_mean, damage_ratio_1in100yr,
               vulnerability_class)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (aid, pid, ref, date(2025, 9, 30), peril,
              vendor, "2024.1", "OEP",
              prop_val, aal, aal_pct,
              loss_100, loss_250, loss_500,
              round(aal / prop_val, 6), round(loss_100 / prop_val, 6),
              vuln))
        cat_assess_ids[(ref, peril)] = aid

    conn.commit()

    # CAT Climate Scenarios
    climate_delta_data = {
        "flood": {
            "RCP4.5": (12.5, 8.0, 15.0),
            "RCP8.5": (28.0, 18.0, 32.0),
        },
        "windstorm": {
            "RCP4.5": (5.0, 3.0, 6.0),
            "RCP8.5": (10.0, 6.0, 12.0),
        },
    }

    for (ref, peril), aid in cat_assess_ids.items():
        for scenario, (haz_delta, freq_delta, aal_delta) in climate_delta_data.get(peril, {}).items():
            # find the aal for this assess
            cur.execute("SELECT aal_gbp, loss_1in100yr_gbp, loss_1in250yr_gbp FROM cat_risk_assessments WHERE id=%s", (aid,))
            row = cur.fetchone()
            if row:
                aal, l100, l250 = row
                cur.execute("""
                    INSERT INTO cat_risk_climate_scenarios
                      (id, assessment_id, climate_scenario, time_horizon_year,
                       hazard_intensity_delta_pct, frequency_delta_pct, aal_delta_pct,
                       aal_climate_adjusted_gbp, pml_delta_pct,
                       loss_1in100yr_climate_gbp, loss_1in250yr_climate_gbp,
                       climate_model, confidence_level)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (new_id(), aid, scenario, 2050,
                      haz_delta, freq_delta, aal_delta,
                      float(aal) * (1 + aal_delta / 100),
                      aal_delta * 0.8,
                      float(l100) * (1 + aal_delta / 100),
                      float(l250) * (1 + aal_delta / 100),
                      "CMIP6_ensemble", "medium"))

    conn.commit()
    print(f"    cat_risk_properties: {len(cat_prop_ids)}, assessments: {len(cat_assess_ids)}")

    # ==========================================================================
    # POWER PLANTS + ASSESSMENTS + TRAJECTORIES
    # ==========================================================================
    print("  Seeding power_plants...")

    pp_data = [
        # name, repd_id, operator, country, lat, lng, fuel, tech, cap_mw, net_cap, cf, yr_comm, yr_decomm, status, ci
        ("Drax Unit 4 Biomass", "REPD-0001", "Drax Group", "GBR", 53.7359, -1.0636, "biomass", "steam_turbine", 645.0, 620.0, 0.72, 2013, 2040, "operational", 23.5),
        ("Pembroke CCGT", "REPD-0002", "RWE Generation", "GBR", 51.6854, -4.9658, "gas_ccgt", "ccgt", 2188.0, 2100.0, 0.45, 2012, 2040, "operational", 368.2),
        ("Hornsea One OWF", "REPD-0003", "Ørsted", "GBR", 53.9000, 1.7000, "wind_offshore", "wind_turbine", 1218.0, 1160.0, 0.44, 2019, 2049, "operational", 9.8),
        ("RWE Innovation OWF Kaskasi", "REPD-0004", "RWE Renewables", "DEU", 54.3167, 7.4333, "wind_offshore", "wind_turbine", 342.0, 328.0, 0.46, 2022, 2052, "operational", 8.2),
        ("Vattenfall Onshore Wind Markbygden", "REPD-0005", "Vattenfall AB", "SWE", 65.6800, 19.2700, "wind_onshore", "wind_turbine", 650.0, 620.0, 0.38, 2021, 2051, "operational", 7.5),
        ("Equinor Hywind Scotland", "REPD-0006", "Equinor ASA", "GBR", 57.4833, -1.6000, "wind_offshore", "wind_turbine", 30.0, 29.0, 0.48, 2017, 2047, "operational", 7.8),
        ("TotalEnergies Seagreen OWF", "REPD-0007", "TotalEnergies SE", "GBR", 56.5167, -0.8667, "wind_offshore", "wind_turbine", 1075.0, 1030.0, 0.47, 2023, 2053, "operational", 8.5),
        ("RWE Neurath Coal Phase-out", "REPD-0008", "RWE AG", "DEU", 51.0121, 6.5543, "coal", "steam_turbine", 4400.0, 4200.0, 0.52, 1972, 2038, "operational", 1042.0),
    ]

    pp_ids = {}
    for (name, repd, op, country, lat, lng, fuel, tech, cap, net_cap, cf, yr_c, yr_d, status, ci) in pp_data:
        ppid = new_id()
        cur.execute("""
            INSERT INTO power_plants
              (id, plant_name, plant_id_repd, operator_name, country_iso,
               latitude, longitude, fuel_type, technology_type,
               installed_capacity_mw, net_capacity_mw, capacity_factor_pct,
               year_commissioned, year_decommission_planned,
               remaining_useful_life_years, design_lifetime_years,
               is_operational, operational_status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (ppid, name, repd, op, country, lat, lng, fuel, tech,
              cap, net_cap, cf * 100, yr_c, yr_d,
              yr_d - 2025, 30, True, status))
        pp_ids[name] = (ppid, fuel, cap, cf, ci)

    conn.commit()

    # Power Plant Assessments
    pp_assess_ids = {}
    iea_nze_thresholds = {"2030": 100.0, "2040": 45.0, "2050": 10.0}

    for name, (ppid, fuel, cap, cf, ci) in pp_ids.items():
        annual_gen_mwh = cap * cf * 8760
        annual_co2e = (annual_gen_mwh * ci) / 1_000  # tCO2e
        stranded_risk = 9.0 if fuel == "coal" else (3.5 if fuel in ("gas_ccgt", "gas_ocgt") else 0.8)
        stranded_cat = "High" if fuel == "coal" else ("Medium" if fuel in ("gas_ccgt", "gas_ocgt") else "Low")
        proj_ci_2030 = ci * 0.72 if fuel == "coal" else (ci * 0.85 if fuel == "natural_gas" else ci * 0.98)
        proj_ci_2040 = ci * 0.45 if fuel == "coal" else (ci * 0.65 if fuel == "natural_gas" else ci * 0.95)
        proj_ci_2050 = ci * 0.20 if fuel == "coal" else (ci * 0.40 if fuel == "natural_gas" else ci * 0.90)
        is_above = ci > iea_nze_thresholds["2030"]

        paid = new_id()
        cur.execute("""
            INSERT INTO power_plant_assessments
              (id, plant_id, plant_name, assessment_date,
               current_ci_gco2_kwh, annual_generation_mwh, annual_co2e_tco2e,
               iea_nze_2030_threshold_gco2_kwh, iea_nze_2040_threshold_gco2_kwh, iea_nze_2050_threshold_gco2_kwh,
               is_above_2030_threshold,
               ci_gap_to_nze_2030_gco2_kwh, ci_gap_to_nze_2050_gco2_kwh,
               projected_ci_2030_gco2_kwh, projected_ci_2040_gco2_kwh, projected_ci_2050_gco2_kwh,
               stranded_asset_risk_score, stranded_asset_risk_category)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (paid, ppid, name, date(2025, 12, 31),
              ci, annual_gen_mwh, annual_co2e,
              100.0, 45.0, 10.0, is_above,
              max(0, ci - 100.0), max(0, ci - 10.0),
              proj_ci_2030, proj_ci_2040, proj_ci_2050,
              stranded_risk, stranded_cat))
        pp_assess_ids[name] = paid

    conn.commit()

    # Power Plant Trajectories 2025-2040
    for name, aid in pp_assess_ids.items():
        _, fuel, cap, cf, ci = pp_ids[name]
        for year in range(2025, 2041):
            yr_frac = (year - 2025) / 15.0
            # Coal declines rapidly, gas moderately, renewables near zero
            if fuel == "coal":
                tgt_ci = ci * (1 - 0.05 * (year - 2025))
                baseline_ci = ci
            elif fuel in ("gas_ccgt", "gas_ocgt"):
                tgt_ci = ci * (1 - 0.02 * (year - 2025))
                baseline_ci = ci
            else:
                tgt_ci = ci
                baseline_ci = ci
            nze_bench = max(10.0, 100.0 - 90.0 * yr_frac)
            gen = cap * cf * 8760
            co2e = gen * tgt_ci / 1_000
            cur.execute("""
                INSERT INTO power_plant_trajectories
                  (id, assessment_id, year, baseline_ci_gco2_kwh, target_ci_gco2_kwh,
                   nze_benchmark_ci_gco2_kwh, projected_generation_mwh, projected_co2e_tco2e,
                   is_aligned_with_nze)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (new_id(), aid, year, baseline_ci, max(0, tgt_ci),
                  nze_bench, gen, co2e,
                  tgt_ci <= nze_bench))

    conn.commit()
    print(f"    power_plants: {len(pp_ids)}, assessments: {len(pp_assess_ids)}, trajectories: {len(pp_ids)*16}")

    # ==========================================================================
    # REGULATORY ENTITIES
    # ==========================================================================
    print("  Seeding regulatory tables...")

    reg_entities = [
        # name, lei, type, jurisdiction, aum/revenue, headcount, listed, frameworks
        ("GS Sustainable Finance Ltd", "5967007LIEEXZXHY5693", "asset_manager", "GBR", 18_500_000_000, 4_200, True, ["SFDR", "EU_TAXONOMY", "TCFD", "CSRD"]),
        ("RWE AG", "529900WI7ZK2D6IMEJ62", "corporate", "DEU", 47_000_000_000, 21_000, True, ["EU_TAXONOMY", "TCFD", "CSRD", "ISSB"]),
        ("Ørsted A/S", "MAES062Z21O4RZ2U7M96", "corporate", "DNK", 18_000_000_000, 8_800, True, ["EU_TAXONOMY", "TCFD", "CSRD", "ISSB"]),
        ("Rabobank N.A.", "DG3RU1DBUFHT4ZF9WN62", "bank", "NLD", 125_000_000_000, 43_000, False, ["EU_TAXONOMY", "TCFD", "CSRD", "SFDR"]),
        ("BNP Paribas SA", "R0MUWSFPU8MPRO8K5P83", "bank", "FRA", 2_200_000_000_000, 185_000, True, ["SFDR", "EU_TAXONOMY", "TCFD", "CSRD", "ISSB"]),
        ("TotalEnergies SE", "529900S21EQ1BO4ESM68", "corporate", "FRA", 218_000_000_000, 101_000, True, ["EU_TAXONOMY", "TCFD", "CSRD", "ISSB"]),
    ]

    reg_entity_ids = {}
    for (name, lei, etype, juri, aum_rev, headcount, is_listed, frameworks) in reg_entities:
        reid = new_id()
        cur.execute("""
            INSERT INTO regulatory_entities
              (id, legal_name, lei, entity_type, jurisdiction,
               aum_gbp, annual_revenue_gbp, headcount, is_listed,
               applicable_frameworks)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (reid, name, lei, etype, juri,
              aum_rev if etype in ("asset_manager", "bank") else None,
              aum_rev if etype in ("corporate",) else None,
              headcount, is_listed, json.dumps(frameworks)))
        reg_entity_ids[name] = reid

    conn.commit()

    # SFDR PAI Disclosures (for GS Article 8 fund + BNP Article 8)
    sfdr_data = [
        ("GS Sustainable Finance Ltd", 8, 8, 1_820_000_000, 91.3, 2.3,
         129_412, 85.0, 2, 71.1, 85.0, 71.1, 85.0,
         62.5, 45.2, 18.4, 2.8, 0.0, 84_000, 2.1, 4.2, 8.8, 0.0, 0.0),
        ("BNP Paribas SA", 8, 45, 14_200_000_000, 78.4, 2.6,
         2_890_000, 72.0, 2, 112.4, 72.0, 112.4, 72.0,
         78.2, 68.4, 24.1, 3.2, 0.8, 156_000, 4.8, 7.2, 14.2, 2.1, 0.8),
    ]

    for (ename, article, n_investees, aum, coverage, dq,
         s1s2_tco2e, s1s2_cov, s1s2_quality,
         cf, cf_cov, waci, waci_cov,
         fossil_pct, nonren_pct, energy_int, bio_pct, water_pct,
         haz_waste, ungc_pct, ungc2_pct, pay_gap, board_div, weapons_pct) in sfdr_data:
        if ename not in reg_entity_ids:
            continue
        reid = reg_entity_ids[ename]
        cur.execute("""
            INSERT INTO sfdr_pai_disclosures
              (id, entity_id, entity_name, reporting_period_start, reporting_period_end,
               reference_date, sfdr_article, is_pai_statement_published,
               number_of_investees, portfolio_coverage_pct,
               pai_1_scope1_scope2_tco2e, pai_1_coverage_pct, pai_1_data_quality,
               pai_2_carbon_footprint, pai_2_coverage_pct,
               pai_3_waci, pai_3_coverage_pct,
               pai_4_fossil_fuel_exposure_pct, pai_5_nonrenewable_energy_pct,
               pai_6_energy_intensity, pai_7_biodiversity_violations_pct,
               pai_8_water_emissions_pct, pai_9_hazardous_waste_tonnes,
               pai_10_un_global_compact_violations_pct, pai_11_lack_of_ungc_compliance_pct,
               pai_12_unadjusted_gender_pay_gap_pct, pai_13_board_gender_diversity_pct,
               pai_14_controversial_weapons_exposure_pct)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (new_id(), reid, ename,
              date(2025, 1, 1), date(2025, 12, 31), date(2025, 12, 31),
              article, True, n_investees, coverage,
              s1s2_tco2e, s1s2_cov, s1s2_quality,
              cf, cf_cov, waci, waci_cov,
              fossil_pct, nonren_pct, energy_int,
              bio_pct, water_pct, haz_waste,
              ungc_pct, ungc2_pct, pay_gap, board_div, weapons_pct))

    conn.commit()

    # EU Taxonomy Assessments (for corporates and banks)
    eu_tax_data = [
        # name, yr, total_turnover, elig_turn_pct, aligned_turn_pct, elig_cap_pct, aligned_cap_pct, obj1_pct, obj2_pct
        ("RWE AG", 2025, 47_000_000_000, 78.4, 52.3, 82.1, 68.4, 52.3, 5.2),
        ("Ørsted A/S", 2025, 18_000_000_000, 94.2, 87.6, 96.8, 91.4, 87.6, 6.1),
        ("TotalEnergies SE", 2025, 218_000_000_000, 41.2, 22.8, 38.6, 24.2, 22.8, 2.1),
        ("Rabobank N.A.", 2025, 125_000_000_000, 28.4, 18.2, 32.1, 22.4, 18.2, 1.8),
        ("BNP Paribas SA", 2025, 2_200_000_000_000, 24.8, 15.6, 28.4, 18.4, 15.6, 1.2),
    ]

    eu_tax_ids = {}
    for (name, yr, turnover, elig_t, align_t, elig_c, align_c, obj1, obj2) in eu_tax_data:
        if name not in reg_entity_ids:
            continue
        reid = reg_entity_ids[name]
        tid = new_id()
        cur.execute("""
            INSERT INTO eu_taxonomy_assessments
              (id, entity_id, entity_name, reporting_year, assessment_type,
               total_turnover_gbp, taxonomy_eligible_turnover_pct, taxonomy_aligned_turnover_pct, not_eligible_turnover_pct,
               total_capex_gbp, taxonomy_eligible_capex_pct, taxonomy_aligned_capex_pct, not_eligible_capex_pct,
               obj1_climate_mitigation_aligned_pct, obj2_climate_adaptation_aligned_pct)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (tid, reid, name, yr, "full_assessment",
              turnover, elig_t, align_t, 100 - elig_t,
              turnover * 0.12, elig_c, align_c, 100 - elig_c,
              obj1, obj2))
        eu_tax_ids[name] = tid

    conn.commit()

    # EU Taxonomy Activities (3 per assessment for energy companies)
    eu_activities = {
        "RWE AG": [
            ("4.3", "Electricity generation from wind energy", "D.35.11", 24_600_000_000, 1, True, None, 80.0, 0.0, True, True, True, True, True, True),
            ("4.1", "Electricity generation using solar photovoltaic technology", "D.35.11", 8_200_000_000, 1, True, None, 92.0, 1.5, True, True, True, True, True, True),
            ("3.1", "Electricity generation from renewable non-fossil gaseous and liquid fuels", "D.35.11", 4_200_000_000, 1, False, 100.0, 42.0, None, False, True, True, True, True, True),
        ],
        "Ørsted A/S": [
            ("4.3", "Electricity generation from wind energy", "D.35.11", 16_900_000_000, 1, True, None, 94.0, 0.0, True, True, True, True, True, True),
            ("4.7", "Production of heat/cool from renewable non-fossil gaseous and liquid fuels", "D.35.30", 980_000_000, 1, True, None, 88.0, 2.1, True, True, True, True, True, True),
            ("6.15", "Infrastructure enabling low-carbon road transport and public transport", "H.49", 220_000_000, 1, True, None, 78.0, 5.2, True, False, True, True, True, True),
        ],
        "TotalEnergies SE": [
            ("4.3", "Electricity generation from wind energy", "D.35.11", 8_400_000_000, 1, True, None, 92.0, 0.0, True, True, True, True, True, True),
            ("4.1", "Electricity generation using solar photovoltaic technology", "D.35.11", 12_600_000_000, 1, True, None, 88.0, 0.0, True, True, True, True, True, True),
            ("3.3", "Manufacture of low carbon technologies for transport", "C.29.10", 6_800_000_000, 1, False, 150.0, 24.0, None, True, True, True, True, True, True),
        ],
    }

    for entity_name, activities in eu_activities.items():
        if entity_name not in eu_tax_ids:
            continue
        tid = eu_tax_ids[entity_name]
        for (code, aname, nace, turnover, sc_obj, sc_met, sc_threshold, sc_actual, sc_val,
             dnsh1, dnsh2, dnsh3, dnsh4, dnsh5, dnsh6) in activities:
            is_eligible = True  # all listed activities are taxonomy-eligible
            is_aligned = bool(sc_met) if sc_met is not None else False
            cur.execute("""
                INSERT INTO eu_taxonomy_activities
                  (id, assessment_id, activity_code, activity_name, nace_codes, sector,
                   turnover_gbp, sc_objective, sc_criteria_met,
                   sc_threshold_value, sc_actual_value,
                   dnsh_obj1, dnsh_obj2, dnsh_obj3, dnsh_obj4, dnsh_obj5, dnsh_obj6,
                   is_eligible, is_aligned)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (new_id(), tid, code, aname, json.dumps([nace]), "Energy",
                  turnover, sc_obj, sc_met,
                  sc_threshold, sc_actual,
                  dnsh1, dnsh2, dnsh3, dnsh4, dnsh5, dnsh6,
                  is_eligible, is_aligned))

    conn.commit()

    # TCFD Assessments (1 per regulatory entity)
    tcfd_scores = {
        "GS Sustainable Finance Ltd": (4, 4, 4.0, 4, 4, 3, 3.67, 4, 4, 4, 4.0, 4, 4, 4, 4.0),
        "RWE AG": (4, 4, 4.0, 4, 3, 4, 3.67, 4, 4, 4, 4.0, 4, 4, 4, 4.0),
        "Ørsted A/S": (4, 4, 4.0, 4, 4, 4, 4.0, 4, 4, 4, 4.0, 4, 4, 4, 4.0),
        "TotalEnergies SE": (4, 3, 3.5, 3, 3, 3, 3.0, 4, 4, 3, 3.67, 4, 4, 4, 4.0),
        "Rabobank N.A.": (4, 4, 4.0, 4, 3, 3, 3.33, 4, 4, 4, 4.0, 4, 4, 4, 4.0),
        "BNP Paribas SA": (4, 4, 4.0, 4, 4, 3, 3.67, 4, 4, 3, 3.67, 4, 4, 4, 4.0),
    }

    for ename, (g1, g2, g_sc, s1, s2, s3, s_sc, r1, r2, r3, r_sc, m1, m2, m3, m_sc) in tcfd_scores.items():
        if ename not in reg_entity_ids:
            continue
        reid = reg_entity_ids[ename]
        overall = round((g_sc + s_sc + r_sc + m_sc) / 4, 2)
        cur.execute("""
            INSERT INTO tcfd_assessments
              (id, entity_id, entity_name, reporting_year, assessment_type,
               gov_1_board_oversight, gov_2_management_role, gov_score,
               strat_1_climate_risks_opps, strat_2_business_impact, strat_3_resilience, strat_score,
               risk_1_identification_process, risk_2_management_process, risk_3_integration, risk_score,
               met_1_metrics_used, met_2_scope_123_emissions, met_3_targets, met_score)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (new_id(), reid, ename, 2025, "internal_assessment",
              g1, g2, g_sc, s1, s2, s3, s_sc,
              r1, r2, r3, r_sc, m1, m2, m3, m_sc))

    conn.commit()

    # CSRD Readiness Assessments
    csrd_data = {
        "RWE AG": ("large", 2024, True, date(2024, 9, 1), "double_materiality_iros", 12, "completed", True, 88.2, "disclosed", True, "completed", True, "in_progress", False),
        "Ørsted A/S": ("large", 2024, True, date(2024, 8, 1), "double_materiality_iros", 10, "completed", True, 94.6, "disclosed", True, "in_progress", False, "in_progress", False),
        "TotalEnergies SE": ("large", 2024, True, date(2024, 10, 1), "double_materiality_iros", 14, "completed", True, 78.4, "disclosed", True, "completed", True, "not_started", False),
        "Rabobank N.A.": ("large", 2025, True, date(2025, 1, 15), "impact_materiality_only", 8, "in_progress", False, 52.4, "in_progress", True, "not_started", False, "not_started", False),
        "BNP Paribas SA": ("large", 2024, True, date(2024, 7, 1), "double_materiality_iros", 16, "completed", True, 82.8, "disclosed", True, "completed", True, "in_progress", False),
        "GS Sustainable Finance Ltd": ("large", 2026, False, None, "not_started", 0, "not_started", False, 0.0, "not_started", False, "not_started", False, "not_started", False),
    }

    for ename, (size, first_yr, dma_done, dma_date, dma_method, mat_count,
                esrs2_status, e1_mat, e1_cov, e1_status, e2_mat, e3_status, e3_mat, e4_status, e4_mat) in csrd_data.items():
        if ename not in reg_entity_ids:
            continue
        reid = reg_entity_ids[ename]
        cur.execute("""
            INSERT INTO csrd_readiness_assessments
              (id, entity_id, entity_name, reporting_year, first_mandatory_year,
               entity_size, dma_completed, dma_completion_date, dma_methodology,
               material_topics_count,
               esrs2_general_disclosures_status, esrs2_completeness_pct,
               e1_climate_status, e1_climate_material,
               e2_pollution_status, e2_pollution_material,
               e3_water_marine_status, e3_water_material,
               e4_biodiversity_status, e4_biodiversity_material)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (new_id(), reid, ename, 2025, first_yr,
              size, dma_done, dma_date, dma_method, mat_count,
              esrs2_status, e1_cov, e1_status, e1_mat,
              "not_started", e2_mat,
              e3_status, e3_mat, e4_status, e4_mat))

    conn.commit()

    # ISSB Assessments
    issb_scores = {
        "RWE AG": (4, 4, 4.0, 4, 4, 4, 4.0, 4, 4, 4.0, 4, 4, 4, 4.0, 4.0),
        "Ørsted A/S": (5, 5, 5.0, 5, 5, 4, 4.67, 5, 5, 5.0, 5, 5, 5, 5.0, 4.92),
        "TotalEnergies SE": (4, 3, 3.5, 3, 3, 3, 3.0, 4, 4, 4.0, 4, 4, 4, 4.0, 3.63),
        "BNP Paribas SA": (4, 4, 4.0, 4, 3, 3, 3.33, 4, 4, 4.0, 4, 3, 4, 3.67, 3.75),
        "GS Sustainable Finance Ltd": (3, 3, 3.0, 3, 3, 2, 2.67, 3, 3, 3.0, 3, 3, 3, 3.0, 2.92),
    }

    for ename, (g1, g2, g_sc, s1, s2, s3, s_sc, r1, r2, r_sc, m1, m2, m3, m_sc, overall) in issb_scores.items():
        if ename not in reg_entity_ids:
            continue
        reid = reg_entity_ids[ename]
        cur.execute("""
            INSERT INTO issb_assessments
              (id, entity_id, entity_name, reporting_year, assessment_type,
               s1_gov_1_board_oversight, s1_gov_2_management_role, s1_gov_score,
               s1_strat_1_risks_opps, s1_strat_2_current_business_model, s1_strat_3_resilience, s1_strat_score,
               s1_risk_1_process_identify, s1_risk_2_integrate, s1_risk_score,
               s1_met_1_metrics, s1_met_2_targets, s1_met_3_progress, s1_met_score,
               s1_overall_score)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (new_id(), reid, ename, 2025, "internal_assessment",
              g1, g2, g_sc, s1, s2, s3, s_sc,
              r1, r2, r_sc, m1, m2, m3, m_sc, overall))

    conn.commit()

    # Verify row counts
    for tbl in ["nature_assessments", "data_centre_facilities", "data_centre_assessments",
                "cat_risk_properties", "cat_risk_assessments", "cat_risk_climate_scenarios",
                "power_plants", "power_plant_assessments", "power_plant_trajectories",
                "regulatory_entities", "sfdr_pai_disclosures",
                "eu_taxonomy_assessments", "eu_taxonomy_activities",
                "tcfd_assessments", "csrd_readiness_assessments", "issb_assessments"]:
        cur.execute(f"SELECT COUNT(*) FROM {tbl}")
        print(f"    {tbl}: {cur.fetchone()[0]} rows")

    conn.close()
    print("\nSprint 7 seed COMPLETE.")


if __name__ == "__main__":
    run()
