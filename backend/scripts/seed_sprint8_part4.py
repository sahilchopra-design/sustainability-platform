"""Part 4: esrs2_general_disclosures, esrs_e1_ghg_emissions, esrs_e1_energy,
esrs_e1_financial_effects, esrs_e2_pollution, esrs_e3_water, esrs_e4_biodiversity,
esrs_e5_circular, esrs_s1_workforce, esrs_g1_conduct
Uses entity_registry_id from csrd_entity_registry (pre-existing).
"""
import psycopg2, json, uuid
from datetime import datetime

DB_URL = "postgresql://postgres.kytzcbipsghprsqoalvi:KimiaAImpact2026@aws-1-us-east-2.pooler.supabase.com:5432/postgres"
conn = psycopg2.connect(DB_URL)
cur = conn.cursor()

# ── csrd_entity_registry IDs ─────────────────────────────────────────────────
ER_ABN   = "24042b91-c1e4-49e9-8c2b-87c00795c189"
ER_BNP   = "311f362b-359f-49fc-8727-a79e09ccf466"
ER_EDP   = "dd83a823-bdab-4ac4-a1e6-a68413df02ee"
ER_ENGIE = "67d33cba-8df0-4cb6-9384-9f16f851f4b4"
ER_ING   = "5332a58e-7051-4a8e-a1f2-98be78f08bd4"
ER_ORST  = "2436ad78-7f83-4d2e-bbf8-a3180c51a5d3"
ER_RABO  = "8615bc35-8b5a-4085-bfcc-bb8d19f92e7c"
ER_RWE   = "02df2645-a112-41bd-8e3b-86c01adeeb03"

ENTITIES = [ER_ABN, ER_BNP, ER_EDP, ER_ENGIE, ER_ING, ER_ORST, ER_RABO, ER_RWE]

# ── esrs2_general_disclosures ─────────────────────────────────────────────────
print("Inserting esrs2_general_disclosures…")
gen_data = {
    ER_ABN:   dict(bex=7, bne=14, bsust=36.0, bgend=29.0, bind=71.0, vrem=18.0,
                   emp=22000, emp_seg={"Retail":8200,"Corporate":6400,"Private":3800,"Other":3600},
                   rev=8100, rev_sec={"Financial Services":8100}, fos_tot=0, coal=0, oil=0, gas=0, tax_gas=0,
                   chem=0, contr=0, tob=0, fin_risk=4100, fin_ant=12800),
    ER_BNP:   dict(bex=11, bne=14, bsust=45.0, bgend=36.0, bind=64.0, vrem=22.0,
                   emp=185000, emp_seg={"CIB":62000,"Retail":72000,"Investment":28000,"Other":23000},
                   rev=45000, rev_sec={"Financial Services":45000}, fos_tot=0, coal=0, oil=0, gas=0, tax_gas=0,
                   chem=0, contr=0, tob=0, fin_risk=22000, fin_ant=68000),
    ER_EDP:   dict(bex=5, bne=10, bsust=30.0, bgend=25.0, bind=60.0, vrem=28.0,
                   emp=13400, emp_seg={"Generation":4200,"Networks":3800,"Supply":2400,"Other":3000},
                   rev=19300, rev_sec={"Electricity":11200,"Gas":3800,"Networks":2400,"Services":1900},
                   fos_tot=3800, coal=0, oil=0, gas=3800, tax_gas=0,
                   chem=0, contr=0, tob=0, fin_risk=2800, fin_ant=8400),
    ER_ENGIE: dict(bex=8, bne=13, bsust=38.0, bgend=28.0, bind=62.0, vrem=32.0,
                   emp=97000, emp_seg={"Generation":28000,"Networks":24000,"Supply":22000,"Other":23000},
                   rev=74000, rev_sec={"Electricity":32000,"Gas":24000,"Networks":8000,"Services":10000},
                   fos_tot=24000, coal=0, oil=0, gas=24000, tax_gas=2400,
                   chem=0, contr=0, tob=0, fin_risk=12000, fin_ant=38000),
    ER_ING:   dict(bex=7, bne=10, bsust=40.0, bgend=38.0, bind=71.0, vrem=20.0,
                   emp=57000, emp_seg={"Retail":22000,"Wholesale":18000,"Corporate":12000,"Other":5000},
                   rev=20200, rev_sec={"Financial Services":20200}, fos_tot=0, coal=0, oil=0, gas=0, tax_gas=0,
                   chem=0, contr=0, tob=0, fin_risk=6800, fin_ant=22000),
    ER_ORST:  dict(bex=4, bne=9, bsust=44.0, bgend=32.0, bind=78.0, vrem=35.0,
                   emp=8300, emp_seg={"Offshore Wind":4800,"Onshore":1200,"Markets":800,"Other":1500},
                   rev=14800, rev_sec={"Offshore Wind":12400,"Onshore":1200,"Other":1200},
                   fos_tot=0, coal=0, oil=0, gas=0, tax_gas=0,
                   chem=0, contr=0, tob=0, fin_risk=1200, fin_ant=3800),
    ER_RABO:  dict(bex=5, bne=9, bsust=33.0, bgend=31.0, bind=67.0, vrem=16.0,
                   emp=42000, emp_seg={"Domestic":18000,"Wholesale":8200,"Rural":9800,"Other":6000},
                   rev=12000, rev_sec={"Financial Services":12000}, fos_tot=0, coal=0, oil=0, gas=0, tax_gas=0,
                   chem=0, contr=0, tob=0, fin_risk=2800, fin_ant=9200),
    ER_RWE:   dict(bex=7, bne=11, bsust=36.0, bgend=22.0, bind=64.0, vrem=30.0,
                   emp=19800, emp_seg={"Generation":8200,"Renewables":4800,"Trading":2800,"Other":4000},
                   rev=22400, rev_sec={"Electricity":14800,"Gas":2800,"Other":4800},
                   fos_tot=2800, coal=0, oil=0, gas=2800, tax_gas=280,
                   chem=0, contr=0, tob=0, fin_risk=8200, fin_ant=24000),
}
for er, d in gen_data.items():
    cur.execute("""INSERT INTO esrs2_general_disclosures
        (id,entity_registry_id,reporting_year,consolidation_approach,reporting_boundary_coverage_pct,
         is_assured,assurance_level,data_quality_score,status,
         board_executive_members_count,board_non_executive_members_count,
         board_sustainability_expertise_pct,board_gender_diversity_ratio,board_independent_members_pct,
         variable_remuneration_sustainability_linked_pct,
         total_employees_headcount,employees_headcount_by_segment,
         total_revenue_eur,revenue_by_esrs_sector,
         revenue_fossil_fuel_total_eur,revenue_coal_eur,revenue_oil_eur,revenue_gas_eur,
         revenue_taxonomy_aligned_fossil_gas_eur,
         revenue_chemicals_production_eur,revenue_controversial_weapons_eur,revenue_tobacco_eur,
         current_financial_effects_risks_eur,anticipated_financial_effects_risks_eur)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT DO NOTHING""",
        (str(uuid.uuid4()),er,2024,"FULL_CONSOLIDATION",100.0,
         True,"LIMITED",3,"PUBLISHED",
         d["bex"],d["bne"],d["bsust"],d["bgend"],d["bind"],d["vrem"],
         d["emp"],json.dumps(d["emp_seg"]),
         d["rev"]*1e6,json.dumps({k:v*1e6 for k,v in d["rev_sec"].items()}),
         d["fos_tot"]*1e6,d["coal"]*1e6,d["oil"]*1e6,d["gas"]*1e6,d["tax_gas"]*1e6,
         d["chem"]*1e6,d["contr"]*1e6,d["tob"]*1e6,
         d["fin_risk"]*1e6,d["fin_ant"]*1e6))

# ── esrs_e1_ghg_emissions ─────────────────────────────────────────────────────
print("Inserting esrs_e1_ghg_emissions…")
ghg_data = {
    ER_ABN:   dict(gwp="AR6",s1=6200,s2l=2800,s2m=2100,s3t=18400,
                   cats={1:1820,2:0,3:2400,4:820,5:180,6:0,7:1200,8:420,9:280,
                         10:680,11:0,12:4800,13:1600,14:820,15:22960000},
                   meth="GHG Protocol Corporate Standard"),
    ER_BNP:   dict(gwp="AR6",s1=18400,s2l=5600,s2m=4200,s3t=42000,
                   cats={1:4800,2:0,3:5400,4:2200,5:480,6:0,7:3200,8:1100,9:820,
                         10:1820,11:0,12:12000,13:4200,14:2100,15:471000000},
                   meth="GHG Protocol Corporate Standard"),
    ER_EDP:   dict(gwp="AR6",s1=4200000,s2l=620000,s2m=280000,s3t=10200000,
                   cats={1:1200000,2:0,3:1800000,4:420000,5:0,6:0,7:480000,8:0,9:0,
                         10:0,11:6800000,12:0,13:0,14:0,15:0},
                   meth="GHG Protocol Corporate Standard + PCAF"),
    ER_ENGIE: dict(gwp="AR6",s1=48000000,s2l=2800000,s2m=1200000,s3t=94000000,
                   cats={1:12000000,2:0,3:8200000,4:2400000,5:0,6:0,7:1800000,8:0,9:0,
                         10:0,11:68000000,12:0,13:0,14:0,15:0},
                   meth="GHG Protocol Corporate Standard + PCAF"),
    ER_ING:   dict(gwp="AR6",s1=9100,s2l=3600,s2m=2800,s3t=26000,
                   cats={1:2400,2:0,3:3200,4:1100,5:240,6:0,7:1800,8:620,9:420,
                         10:980,11:0,12:6800,13:2400,14:1200,15:150000000},
                   meth="GHG Protocol Corporate Standard"),
    ER_ORST:  dict(gwp="AR6",s1=1820000,s2l=88000,s2m=42000,s3t=3680000,
                   cats={1:320000,2:0,3:480000,4:120000,5:0,6:0,7:80000,8:0,9:0,
                         10:0,11:2800000,12:0,13:0,14:0,15:0},
                   meth="GHG Protocol Corporate Standard"),
    ER_RABO:  dict(gwp="AR6",s1=4800,s2l=1800,s2m=1200,s3t=14000,
                   cats={1:1200,2:0,3:1800,4:620,5:120,6:0,7:820,8:280,9:180,
                         10:480,11:0,12:4200,13:1400,14:680,15:62200000},
                   meth="GHG Protocol Corporate Standard"),
    ER_RWE:   dict(gwp="AR6",s1=38000000,s2l=1800000,s2m=820000,s3t=50200000,
                   cats={1:8200000,2:0,3:6200000,4:1800000,5:0,6:0,7:1200000,8:0,9:0,
                         10:0,11:34000000,12:0,13:0,14:0,15:0},
                   meth="GHG Protocol Corporate Standard"),
}
for er, d in ghg_data.items():
    cats = d["cats"]
    cur.execute("""INSERT INTO esrs_e1_ghg_emissions
        (id,entity_registry_id,reporting_year,consolidation_approach,reporting_boundary_coverage_pct,
         is_assured,assurance_level,data_quality_score,status,
         gwp_standard,scope1_gross_tco2e,scope2_location_based_tco2e,scope2_market_based_tco2e,scope3_total_tco2e,
         scope3_cat01_purchased_goods_services_tco2e,scope3_cat02_capital_goods_tco2e,scope3_cat03_fuel_energy_tco2e,
         scope3_cat04_upstream_transport_tco2e,scope3_cat05_waste_operations_tco2e,scope3_cat06_business_travel_tco2e,
         scope3_cat07_employee_commuting_tco2e,scope3_cat08_upstream_leased_assets_tco2e,scope3_cat09_downstream_transport_tco2e,
         scope3_cat10_processing_sold_products_tco2e,scope3_cat11_use_of_sold_products_tco2e,scope3_cat12_end_of_life_treatment_tco2e,
         scope3_cat13_downstream_leased_assets_tco2e,scope3_cat14_franchises_tco2e,scope3_cat15_investments_tco2e)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT DO NOTHING""",
        (str(uuid.uuid4()),er,2024,"FULL_CONSOLIDATION",100.0,
         True,"LIMITED",3,"PUBLISHED",
         d["gwp"],d["s1"],d["s2l"],d["s2m"],d["s3t"],
         cats[1],cats[2],cats[3],cats[4],cats[5],cats[6],cats[7],cats[8],cats[9],
         cats[10],cats[11],cats[12],cats[13],cats[14],cats[15]))

# ── esrs_e1_energy ─────────────────────────────────────────────────────────────
print("Inserting esrs_e1_energy…")
en_data = {
    ER_ABN:   dict(tot=312000,  fos=98000,  nuc=0,       ren=214000, ei=39.0),
    ER_BNP:   dict(tot=810000,  fos=228000, nuc=0,       ren=582000, ei=4.4),
    ER_EDP:   dict(tot=4200000, fos=420000, nuc=0,       ren=3780000, ei=217.6),
    ER_ENGIE: dict(tot=18400000, fos=5520000, nuc=3312000, ren=9568000, ei=248.6),
    ER_ING:   dict(tot=420000,  fos=0,      nuc=0,       ren=420000, ei=7.4),
    ER_ORST:  dict(tot=1820000, fos=76440,  nuc=0,       ren=1743560, ei=123.0),
    ER_RABO:  dict(tot=198000,  fos=0,      nuc=0,       ren=198000, ei=4.7),
    ER_RWE:   dict(tot=8200000, fos=3116000, nuc=0,      ren=5084000, ei=365.6),
}
for er, d in en_data.items():
    ren_pct = round(d["ren"]/d["tot"]*100, 1) if d["tot"] else 0
    cur.execute("""INSERT INTO esrs_e1_energy
        (id,entity_registry_id,reporting_year,consolidation_approach,reporting_boundary_coverage_pct,
         is_assured,assurance_level,data_quality_score,status,
         total_energy_consumption_mwh,energy_from_fossil_sources_mwh,energy_from_nuclear_sources_mwh,
         energy_from_renewable_sources_mwh,renewable_energy_pct)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT DO NOTHING""",
        (str(uuid.uuid4()),er,2024,"FULL_CONSOLIDATION",100.0,
         True,"LIMITED",3,"PUBLISHED",
         d["tot"],d["fos"],d["nuc"],d["ren"],ren_pct))

# ── esrs_e1_financial_effects ──────────────────────────────────────────────────
print("Inserting esrs_e1_financial_effects…")
fe_data = {
    ER_ABN:   dict(scen="NGFS 2023",phys_mat=4100e6, phys_ac=1900e6, phys_ch=2200e6, phys_pct=1.0,
                   tr_mat=8200e6, tr_pct=2.0, str_est=None, mon_s12=1.04e6, mon_tot=1.82e6),
    ER_BNP:   dict(scen="NGFS 2023",phys_mat=22000e6, phys_ac=9800e6, phys_ch=12200e6, phys_pct=2.6,
                   tr_mat=42000e6, tr_pct=4.9, str_est=None, mon_s12=4.22e6, mon_tot=7.84e6),
    ER_EDP:   dict(scen="NGFS 2023 + IEA WEO",phys_mat=2800e6, phys_ac=1200e6, phys_ch=1600e6, phys_pct=14.5,
                   tr_mat=4200e6, tr_pct=21.8, str_est=180e6, mon_s12=228e6, mon_tot=504e6),
    ER_ENGIE: dict(scen="NGFS 2023 + IEA WEO",phys_mat=12000e6, phys_ac=5200e6, phys_ch=6800e6, phys_pct=16.2,
                   tr_mat=24000e6, tr_pct=32.4, str_est=1200e6, mon_s12=2484e6, mon_tot=4702e6),
    ER_ING:   dict(scen="NGFS 2023",phys_mat=3600e6, phys_ac=1600e6, phys_ch=2000e6, phys_pct=0.9,
                   tr_mat=6800e6, tr_pct=1.7, str_est=None, mon_s12=1.19e6, mon_tot=2.39e6),
    ER_ORST:  dict(scen="NGFS 2023 + IPCC AR6",phys_mat=1200e6, phys_ac=800e6, phys_ch=400e6, phys_pct=23.1,
                   tr_mat=480e6, tr_pct=9.2, str_est=None, mon_s12=96.2e6, mon_tot=294e6),
    ER_RABO:  dict(scen="NGFS 2023",phys_mat=2900e6, phys_ac=1200e6, phys_ch=1700e6, phys_pct=0.7,
                   tr_mat=5400e6, tr_pct=1.4, str_est=None, mon_s12=0.62e6, mon_tot=1.23e6),
    ER_RWE:   dict(scen="NGFS 2023 + IEA WEO",phys_mat=8200e6, phys_ac=3600e6, phys_ch=4600e6, phys_pct=10.5,
                   tr_mat=16000e6, tr_pct=20.5, str_est=2800e6, mon_s12=2068e6, mon_tot=4730e6),
}
for er, d in fe_data.items():
    cur.execute("""INSERT INTO esrs_e1_financial_effects
        (id,entity_registry_id,reporting_year,consolidation_approach,reporting_boundary_coverage_pct,
         is_assured,assurance_level,data_quality_score,status,
         scenario_set_used,assets_at_material_physical_risk_eur,
         assets_at_acute_physical_risk_eur,assets_at_chronic_physical_risk_eur,assets_at_physical_risk_pct,
         assets_at_material_transition_risk_eur,assets_at_transition_risk_pct,
         stranded_assets_estimated_eur,monetised_scope1_scope2_ghg_eur,monetised_total_ghg_eur)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT DO NOTHING""",
        (str(uuid.uuid4()),er,2024,"FULL_CONSOLIDATION",100.0,
         True,"LIMITED",3,"PUBLISHED",
         d["scen"],d["phys_mat"],d["phys_ac"],d["phys_ch"],d["phys_pct"],
         d["tr_mat"],d["tr_pct"],d["str_est"],d["mon_s12"],d["mon_tot"]))

# ── esrs_e2_pollution ──────────────────────────────────────────────────────────
print("Inserting esrs_e2_pollution…")
pol_data = {
    ER_ABN:   dict(nox=12.4, sox=1.8, pm25=0.8, voc=4.2, n_kg=420, p_kg=82),
    ER_BNP:   dict(nox=28.4, sox=4.2, pm25=1.8, voc=9.8, n_kg=980, p_kg=188),
    ER_EDP:   dict(nox=12400, sox=8200, pm25=3400, voc=2800, n_kg=None, p_kg=None),
    ER_ENGIE: dict(nox=84000, sox=42000, pm25=18000, voc=12000, n_kg=None, p_kg=None),
    ER_ING:   dict(nox=8.2, sox=1.2, pm25=0.6, voc=2.8, n_kg=280, p_kg=54),
    ER_ORST:  dict(nox=2400, sox=420, pm25=180, voc=480, n_kg=None, p_kg=None),
    ER_RABO:  dict(nox=4.8, sox=0.8, pm25=0.4, voc=1.8, n_kg=180, p_kg=34),
    ER_RWE:   dict(nox=48000, sox=28000, pm25=12000, voc=8200, n_kg=None, p_kg=None),
}
for er, d in pol_data.items():
    cur.execute("""INSERT INTO esrs_e2_pollution
        (id,entity_registry_id,reporting_year,consolidation_approach,reporting_boundary_coverage_pct,
         is_assured,assurance_level,data_quality_score,status,
         air_nox_tonnes,air_sox_tonnes,air_pm25_tonnes,air_voc_tonnes,
         water_nitrogen_tonnes,water_phosphorus_tonnes)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT DO NOTHING""",
        (str(uuid.uuid4()),er,2024,"FULL_CONSOLIDATION",100.0,
         True,"LIMITED",3,"PUBLISHED",
         d["nox"],d["sox"],d["pm25"],d["voc"],d["n_kg"],d["p_kg"]))

# ── esrs_e3_water ──────────────────────────────────────────────────────────────
print("Inserting esrs_e3_water…")
wat_data = {
    ER_ABN:   dict(tot=42000, risk=8200, rec=18000, wd=52000, wg=28000, wt=24000, hi=8200, hi_pct=15.8),
    ER_BNP:   dict(tot=128000, risk=24000, rec=48000, wd=148000, wg=82000, wt=66000, hi=22000, hi_pct=14.9),
    ER_EDP:   dict(tot=28000000, risk=4200000, rec=2800000, wd=48000000, wg=12000000, wt=36000000, hi=8200000, hi_pct=17.1),
    ER_ENGIE: dict(tot=182000000, risk=28000000, rec=14000000, wd=248000000, wg=82000000, wt=166000000, hi=42000000, hi_pct=16.9),
    ER_ING:   dict(tot=28000, risk=4800, rec=12000, wd=32000, wg=18000, wt=14000, hi=4800, hi_pct=15.0),
    ER_ORST:  dict(tot=4200000, risk=420000, rec=840000, wd=8200000, wg=2400000, wt=5800000, hi=420000, hi_pct=5.1),
    ER_RABO:  dict(tot=18000, risk=2800, rec=8200, wd=22000, wg=12000, wt=10000, hi=2800, hi_pct=12.7),
    ER_RWE:   dict(tot=120000000, risk=18000000, rec=9200000, wd=168000000, wg=48000000, wt=120000000, hi=28000000, hi_pct=16.7),
}
for er, d in wat_data.items():
    cur.execute("""INSERT INTO esrs_e3_water
        (id,entity_registry_id,reporting_year,consolidation_approach,reporting_boundary_coverage_pct,
         is_assured,assurance_level,data_quality_score,status,
         total_water_consumption_m3,water_consumption_at_water_risk_m3,total_water_recycled_reused_m3,
         total_water_withdrawals_m3,withdrawal_groundwater_m3,withdrawal_third_party_municipal_m3,
         withdrawal_high_stress_areas_m3,withdrawal_high_stress_areas_pct)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT DO NOTHING""",
        (str(uuid.uuid4()),er,2024,"FULL_CONSOLIDATION",100.0,
         True,"LIMITED",3,"PUBLISHED",
         d["tot"],d["risk"],d["rec"],d["wd"],d["wg"],d["wt"],d["hi"],d["hi_pct"]))

# ── esrs_e4_biodiversity ───────────────────────────────────────────────────────
print("Inserting esrs_e4_biodiversity…")
bio_data = {
    ER_ABN:   dict(sites_kba=2, sites_ha=18.4, land=52000, seal=28000, tnfd_loc=True, tnfd_eval=True, tnfd_ass=False, tnfd_prep=False, f_risk=420e6),
    ER_BNP:   dict(sites_kba=5, sites_ha=48.2, land=182000, seal=98000, tnfd_loc=True, tnfd_eval=True, tnfd_ass=True, tnfd_prep=False, f_risk=1800e6),
    ER_EDP:   dict(sites_kba=12, sites_ha=2840, land=82000, seal=8200, tnfd_loc=True, tnfd_eval=True, tnfd_ass=True, tnfd_prep=True, f_risk=680e6),
    ER_ENGIE: dict(sites_kba=28, sites_ha=14200, land=248000, seal=28000, tnfd_loc=True, tnfd_eval=True, tnfd_ass=True, tnfd_prep=True, f_risk=2400e6),
    ER_ING:   dict(sites_kba=1, sites_ha=8.2, land=74000, seal=42000, tnfd_loc=True, tnfd_eval=False, tnfd_ass=False, tnfd_prep=False, f_risk=280e6),
    ER_ORST:  dict(sites_kba=18, sites_ha=8420, land=28000, seal=4200, tnfd_loc=True, tnfd_eval=True, tnfd_ass=True, tnfd_prep=True, f_risk=480e6),
    ER_RABO:  dict(sites_kba=1, sites_ha=4.8, land=38000, seal=18000, tnfd_loc=True, tnfd_eval=False, tnfd_ass=False, tnfd_prep=False, f_risk=180e6),
    ER_RWE:   dict(sites_kba=22, sites_ha=12400, land=182000, seal=22000, tnfd_loc=True, tnfd_eval=True, tnfd_ass=True, tnfd_prep=False, f_risk=1600e6),
}
for er, d in bio_data.items():
    cur.execute("""INSERT INTO esrs_e4_biodiversity
        (id,entity_registry_id,reporting_year,consolidation_approach,reporting_boundary_coverage_pct,
         is_assured,assurance_level,data_quality_score,status,
         sites_in_near_protected_or_kba_count,sites_in_near_protected_or_kba_area_ha,
         total_land_use_area_ha,sealed_area_ha,
         tnfd_locate_complete,tnfd_evaluate_complete,tnfd_assess_complete,tnfd_prepare_complete,
         biodiversity_financial_effects_risk_eur)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT DO NOTHING""",
        (str(uuid.uuid4()),er,2024,"FULL_CONSOLIDATION",100.0,
         True,"LIMITED",3,"PUBLISHED",
         d["sites_kba"],d["sites_ha"],d["land"],d["seal"],
         d["tnfd_loc"],d["tnfd_eval"],d["tnfd_ass"],d["tnfd_prep"],d["f_risk"]))

# ── esrs_e5_circular ────────────────────────────────────────────────────────────
print("Inserting esrs_e5_circular…")
cir_data = {
    ER_ABN:   dict(mat=8200, sec=1640, sec_pct=20.0, waste=420, haz=42, nohaz=378),
    ER_BNP:   dict(mat=22000, sec=4400, sec_pct=20.0, waste=1100, haz=110, nohaz=990),
    ER_EDP:   dict(mat=48000, sec=14400, sec_pct=30.0, waste=8200, haz=1640, nohaz=6560),
    ER_ENGIE: dict(mat=182000, sec=54600, sec_pct=30.0, waste=28000, haz=5600, nohaz=22400),
    ER_ING:   dict(mat=4800, sec=960, sec_pct=20.0, waste=280, haz=28, nohaz=252),
    ER_ORST:  dict(mat=12000, sec=3600, sec_pct=30.0, waste=1800, haz=360, nohaz=1440),
    ER_RABO:  dict(mat=2400, sec=480, sec_pct=20.0, waste=140, haz=14, nohaz=126),
    ER_RWE:   dict(mat=82000, sec=24600, sec_pct=30.0, waste=18000, haz=3600, nohaz=14400),
}
for er, d in cir_data.items():
    cur.execute("""INSERT INTO esrs_e5_circular
        (id,entity_registry_id,reporting_year,consolidation_approach,reporting_boundary_coverage_pct,
         is_assured,assurance_level,data_quality_score,status,
         total_materials_consumed_tonnes,secondary_reused_recycled_materials_tonnes,
         secondary_reused_recycled_materials_pct,total_waste_generated_tonnes,
         total_hazardous_waste_tonnes,non_hazardous_waste_directed_to_disposal_tonnes)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT DO NOTHING""",
        (str(uuid.uuid4()),er,2024,"FULL_CONSOLIDATION",100.0,
         True,"LIMITED",3,"PUBLISHED",
         d["mat"],d["sec"],d["sec_pct"],d["waste"],d["haz"],d["nohaz"]))

# ── esrs_s1_workforce ───────────────────────────────────────────────────────────
print("Inserting esrs_s1_workforce…")
wf_data = {
    ER_ABN:   dict(hc=22000, male=11660, fem=9900, perm=20240, temp=1760, cba=82.0, gpg=-8.4, acc=0, days=0, rem_ratio=42.0),
    ER_BNP:   dict(hc=185000, male=98050, fem=83250, perm=172400, temp=12600, cba=78.0, gpg=-12.8, acc=1, days=2, rem_ratio=68.0),
    ER_EDP:   dict(hc=13400, male=9380, fem=4020, perm=12600, temp=800, cba=68.0, gpg=-14.2, acc=0, days=0, rem_ratio=38.0),
    ER_ENGIE: dict(hc=97000, male=67900, fem=27160, perm=89240, temp=7760, cba=72.0, gpg=-16.8, acc=1, days=4, rem_ratio=52.0),
    ER_ING:   dict(hc=57000, male=30210, fem=25650, perm=52440, temp=4560, cba=84.0, gpg=-9.2, acc=0, days=0, rem_ratio=44.0),
    ER_ORST:  dict(hc=8300, male=5810, fem=2490, perm=7800, temp=500, cba=62.0, gpg=-11.4, acc=0, days=0, rem_ratio=34.0),
    ER_RABO:  dict(hc=42000, male=21840, fem=18900, perm=38640, temp=3360, cba=86.0, gpg=-7.8, acc=0, days=0, rem_ratio=38.0),
    ER_RWE:   dict(hc=19800, male=13860, fem=5940, perm=18216, temp=1584, cba=76.0, gpg=-18.2, acc=2, days=8, rem_ratio=48.0),
}
for er, d in wf_data.items():
    cur.execute("""INSERT INTO esrs_s1_workforce
        (id,entity_registry_id,reporting_year,consolidation_approach,reporting_boundary_coverage_pct,
         is_assured,assurance_level,data_quality_score,status,
         employees_headcount,employees_male,employees_female,
         employees_permanent,employees_temporary,employees_covered_by_cba_pct,
         gender_pay_gap_pct,fatalities_total_own_workforce,days_lost_own_workforce,
         annual_total_remuneration_ratio)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT DO NOTHING""",
        (str(uuid.uuid4()),er,2024,"FULL_CONSOLIDATION",100.0,
         True,"LIMITED",3,"PUBLISHED",
         d["hc"],d["male"],d["fem"],d["perm"],d["temp"],d["cba"],
         d["gpg"],d["acc"],d["days"],d["rem_ratio"]))

# ── esrs_g1_conduct ─────────────────────────────────────────────────────────────
print("Inserting esrs_g1_conduct…")
gov_data = {
    ER_ABN:   dict(coc=True,ac=True,ab=True,wb=True,wba=True,sc=True,tr=98.0,gb_tr=92.0,emp_tr=96.0,conv=0,fin=0,inc=0,days=28,pmt=94.0),
    ER_BNP:   dict(coc=True,ac=True,ab=True,wb=True,wba=True,sc=True,tr=96.0,gb_tr=88.0,emp_tr=94.0,conv=0,fin=0,inc=1,days=32,pmt=91.0),
    ER_EDP:   dict(coc=True,ac=True,ab=True,wb=True,wba=True,sc=True,tr=94.0,gb_tr=90.0,emp_tr=92.0,conv=0,fin=0,inc=0,days=38,pmt=88.0),
    ER_ENGIE: dict(coc=True,ac=True,ab=True,wb=True,wba=True,sc=True,tr=92.0,gb_tr=86.0,emp_tr=90.0,conv=0,fin=0,inc=2,days=42,pmt=86.0),
    ER_ING:   dict(coc=True,ac=True,ab=True,wb=True,wba=True,sc=True,tr=97.0,gb_tr=94.0,emp_tr=96.0,conv=0,fin=0,inc=0,days=26,pmt=95.0),
    ER_ORST:  dict(coc=True,ac=True,ab=True,wb=True,wba=True,sc=True,tr=99.0,gb_tr=96.0,emp_tr=98.0,conv=0,fin=0,inc=0,days=24,pmt=97.0),
    ER_RABO:  dict(coc=True,ac=True,ab=True,wb=True,wba=True,sc=True,tr=98.0,gb_tr=94.0,emp_tr=97.0,conv=0,fin=0,inc=0,days=28,pmt=96.0),
    ER_RWE:   dict(coc=True,ac=True,ab=True,wb=True,wba=True,sc=True,tr=94.0,gb_tr=88.0,emp_tr=92.0,conv=0,fin=0,inc=1,days=36,pmt=89.0),
}
for er, d in gov_data.items():
    cur.execute("""INSERT INTO esrs_g1_conduct
        (id,entity_registry_id,reporting_year,consolidation_approach,reporting_boundary_coverage_pct,
         is_assured,assurance_level,data_quality_score,status,
         code_of_conduct_published,anti_corruption_policy_published,anti_bribery_policy_published,
         whistleblowing_mechanism_exists,whistleblowing_anonymous_available,supplier_code_of_conduct_published,
         functions_at_risk_covered_by_training_pct,governance_body_anti_corruption_training_pct,
         employees_anti_corruption_training_pct,convictions_anticorruption_antibribery_count,
         fines_anticorruption_antibribery_eur,confirmed_corruption_incidents_count,
         avg_days_to_pay_invoice,payments_aligned_standard_terms_pct)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT DO NOTHING""",
        (str(uuid.uuid4()),er,2024,"FULL_CONSOLIDATION",100.0,
         True,"LIMITED",3,"PUBLISHED",
         d["coc"],d["ac"],d["ab"],d["wb"],d["wba"],d["sc"],
         d["tr"],d["gb_tr"],d["emp_tr"],d["conv"],d["fin"],d["inc"],
         d["days"],d["pmt"]))

conn.commit()
print("Part 4 DONE: all ESRS E1-E5/S1/G1 tables populated for 8 entities")
conn.close()
