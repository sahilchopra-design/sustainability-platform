"""Part 3: energy_entities (already done in part1), energy_financials, energy_generation_mix,
energy_csrd_e1_climate, energy_stranded_assets_register, energy_renewable_pipeline"""
import psycopg2, json, uuid
from datetime import datetime

DB_URL = "postgresql://postgres.kytzcbipsghprsqoalvi:KimiaAImpact2026@aws-1-us-east-2.pooler.supabase.com:5432/postgres"
conn = psycopg2.connect(DB_URL)
cur = conn.cursor()

# Re-fetch energy entity IDs
cur.execute("SELECT id,legal_name FROM energy_entities ORDER BY legal_name")
en_map = {row[1]: row[0] for row in cur.fetchall()}
print("Energy entities found:", list(en_map.keys()))

EN_EDP   = en_map["EDP \u2013 Energias de Portugal S.A."]
EN_ENGIE = en_map["ENGIE S.A."]
EN_ORST  = en_map["\u00d8rsted A/S"]
EN_RWE   = en_map["RWE Aktiengesellschaft"]

# ── energy_financials (2024) ──────────────────────────────────────────────────
print("Inserting energy_financials…")
ef_data = [
    # EDP 2024 — revenues ~€19.3B
    dict(id=str(uuid.uuid4()), eid=EN_EDP, year=2024, cu="EUR",
         rev=19300, e_rev=11200, g_rev=3800, n_rev=2400, s_rev=1900,
         ebitda=5800, ebitda_m=30.1, ebit=3200, da=2600, impair=180, fin=-820,
         pbt=2380, tax=620, net=1760, eps=0.48, roe=9.8, roce=8.2,
         ta=58000, ppe=38000, gi=4200, rou=1800, eq=18000, nd=18200, gd=22000,
         nd_ebitda=3.14, ic=6.8, hyb=1200, mktcap=14800, ev=33000, ev_eb=5.7,
         capex=4800, gcapex=3200, mcapex=1600, grncapex=3100, grn_pct=64.6,
         eu_tx=72.4, dps=0.19, dy=3.1, gb=8200, slb=3400, gf_pct=50.2),
    # ENGIE 2024 — revenues ~€74B
    dict(id=str(uuid.uuid4()), eid=EN_ENGIE, year=2024, cu="EUR",
         rev=74000, e_rev=32000, g_rev=24000, n_rev=8000, s_rev=10000,
         ebitda=13800, ebitda_m=18.6, ebit=7400, da=6400, impair=420, fin=-1800,
         pbt=5600, tax=1600, net=4000, eps=1.12, roe=12.4, roce=7.8,
         ta=168000, ppe=88000, gi=12000, rou=4200, eq=48000, nd=38000, gd=52000,
         nd_ebitda=2.75, ic=7.2, hyb=4200, mktcap=38000, ev=76000, ev_eb=5.5,
         capex=12000, gcapex=8200, mcapex=3800, grncapex=7800, grn_pct=65.0,
         eu_tx=68.2, dps=1.43, dy=7.8, gb=22000, slb=8400, gf_pct=58.4),
    # Ørsted 2024 — revenues ~€14.8B
    dict(id=str(uuid.uuid4()), eid=EN_ORST, year=2024, cu="EUR",
         rev=14800, e_rev=12400, g_rev=0, n_rev=0, s_rev=2400,
         ebitda=4200, ebitda_m=28.4, ebit=2100, da=2100, impair=380, fin=-620,
         pbt=1480, tax=380, net=1100, eps=4.62, roe=8.2, roce=6.8,
         ta=52000, ppe=38000, gi=2800, rou=1200, eq=14000, nd=24000, gd=26000,
         nd_ebitda=5.71, ic=3.2, hyb=1800, mktcap=18000, ev=42000, ev_eb=10.0,
         capex=8200, gcapex=7400, mcapex=800, grncapex=7400, grn_pct=90.2,
         eu_tx=96.8, dps=8.46, dy=8.4, gb=14000, slb=4200, gf_pct=68.4),
    # RWE 2024 — revenues ~€22.4B
    dict(id=str(uuid.uuid4()), eid=EN_RWE, year=2024, cu="EUR",
         rev=22400, e_rev=14800, g_rev=2800, n_rev=0, s_rev=4800,
         ebitda=8200, ebitda_m=36.6, ebit=4800, da=3400, impair=280, fin=-720,
         pbt=4080, tax=1100, net=2980, eps=4.82, roe=14.2, roce=9.4,
         ta=78000, ppe=48000, gi=6200, rou=2400, eq=28000, nd=18000, gd=22000,
         nd_ebitda=2.20, ic=11.2, hyb=2800, mktcap=24000, ev=42000, ev_eb=5.1,
         capex=6800, gcapex=5400, mcapex=1400, grncapex=5200, grn_pct=76.5,
         eu_tx=58.4, dps=1.00, dy=4.0, gb=12000, slb=4800, gf_pct=60.2),
]
for f in ef_data:
    cur.execute("""INSERT INTO energy_financials
        (id,entity_id,reporting_year,currency,total_revenues,electricity_revenues,
         gas_revenues,network_revenues,services_revenues,ebitda,ebitda_margin_pct,ebit,
         depreciation_amortization,impairment_charges,finance_costs_net,profit_before_tax,
         income_tax,net_profit_group,eps_diluted,roe,roce,total_assets,ppe_net,
         goodwill_intangibles,right_of_use_assets,total_equity,net_debt,gross_debt,
         net_debt_to_ebitda,interest_coverage_ratio,hybrid_capital,market_cap,enterprise_value,
         ev_to_ebitda,total_capex,growth_capex,maintenance_capex,green_capex,green_capex_pct,
         eu_taxonomy_aligned_capex_pct,dividend_per_share,dividend_yield_pct,
         green_bonds_outstanding_meur,sustainability_linked_bonds_meur,green_finance_total_pct_of_debt)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT DO NOTHING""",
        (f["id"],f["eid"],f["year"],f["cu"],f["rev"],f["e_rev"],f["g_rev"],f["n_rev"],f["s_rev"],
         f["ebitda"],f["ebitda_m"],f["ebit"],f["da"],f["impair"],f["fin"],f["pbt"],
         f["tax"],f["net"],f["eps"],f["roe"],f["roce"],f["ta"],f["ppe"],f["gi"],f["rou"],
         f["eq"],f["nd"],f["gd"],f["nd_ebitda"],f["ic"],f["hyb"],f["mktcap"],f["ev"],f["ev_eb"],
         f["capex"],f["gcapex"],f["mcapex"],f["grncapex"],f["grn_pct"],f["eu_tx"],
         f["dps"],f["dy"],f["gb"],f["slb"],f["gf_pct"]))

# ── energy_generation_mix (2024) ──────────────────────────────────────────────
print("Inserting energy_generation_mix…")
gm_data = [
    # EDP: heavy hydro+wind (29 GW total)
    dict(eid=EN_EDP, yr=2024, tot=29.0, coal=0, lig=0, gas_cc=2.4, gas_oc=0.8,
         wind_on=10.2, wind_off=0.9, solar=8.4, bio=0.8, batt=1.2),
    # ENGIE: diversified (78 GW total)
    dict(eid=EN_ENGIE, yr=2024, tot=78.0, coal=2.1, lig=0, gas_cc=18.4, gas_oc=4.2,
         wind_on=14.8, wind_off=3.2, solar=22.0, bio=3.8, batt=2.4),
    # Ørsted: mostly offshore wind (16 GW)
    dict(eid=EN_ORST, yr=2024, tot=16.4, coal=0, lig=0, gas_cc=0.4, gas_oc=0,
         wind_on=0.8, wind_off=13.2, solar=0.6, bio=0.8, batt=0.6),
    # RWE: mixed transitioning (34 GW)
    dict(eid=EN_RWE, yr=2024, tot=34.0, coal=2.8, lig=4.2, gas_cc=6.4, gas_oc=2.1,
         wind_on=5.8, wind_off=3.4, solar=7.2, bio=0.8, batt=1.2),
]
for g in gm_data:
    cur.execute("""INSERT INTO energy_generation_mix
        (entity_id,reporting_year,total_installed_gw,coal_installed_gw,lignite_installed_gw,
         gas_ccgt_installed_gw,gas_ocgt_installed_gw,wind_onshore_installed_gw,
         wind_offshore_installed_gw,solar_pv_installed_gw,biomass_installed_gw,battery_storage_gwh)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
        (g["eid"],g["yr"],g["tot"],g["coal"],g["lig"],g["gas_cc"],g["gas_oc"],
         g["wind_on"],g["wind_off"],g["solar"],g["bio"],g["batt"]))

# ── energy_csrd_e1_climate (2024) ─────────────────────────────────────────────
print("Inserting energy_csrd_e1_climate…")
ec_data = [
    dict(id=str(uuid.uuid4()), eid=EN_EDP, yr=2024,
         s1=4200000, s2m=280000, s2l=620000, s3up=1800000, s3dn=8400000, s3tot=10200000,
         s3c3=1200000, s3c11=6800000, tot_ghg=14680000, tot_vs_base=-38.2,
         bio=82000, nonco2=280000, meth=18000, meth_r=0.12,
         prim=124.0, fos=18.4, nuc=0, ren=105.6, own_mwh=4200000, own_ren_pct=92.0,
         s1_base=2015, s1_base_t=6800000, s1_tgt30=-40.0, s1_tgt50=-100.0,
         s12_tgt30=-42.0, s3_tgt30=-30.0, s3_tgt50=-55.0,
         abs_tgt=2520000, ci_tgt30=42.0, ci_tgt40=22.0, ci_tgt50=0.0,
         nzy=2040, sbti=True, sbti_path="1.5C", coal_exit=None, coal_gw=None,
         ren_tgt_gw=50.0, ren_cur_gw=20.3, capex_ren=24.0,
         cr_pur=0, cr_ret=680000, cr_std="Gold Standard",
         icp=True, icp_e=75.0, ccs=0, ccs_tgt=0),
    dict(id=str(uuid.uuid4()), eid=EN_ENGIE, yr=2024,
         s1=48000000, s2m=1200000, s2l=2800000, s3up=12000000, s3dn=82000000, s3tot=94000000,
         s3c3=8200000, s3c11=68000000, tot_ghg=143200000, tot_vs_base=-31.4,
         bio=2400000, nonco2=1800000, meth=380000, meth_r=0.18,
         prim=842.0, fos=248.0, nuc=112.0, ren=482.0, own_mwh=18400000, own_ren_pct=74.0,
         s1_base=2017, s1_base_t=70000000, s1_tgt30=-33.0, s1_tgt50=-100.0,
         s12_tgt30=-38.0, s3_tgt30=-25.0, s3_tgt50=-50.0,
         abs_tgt=46900000, ci_tgt30=72.0, ci_tgt40=38.0, ci_tgt50=0.0,
         nzy=2045, sbti=True, sbti_path="WELL_BELOW_2C", coal_exit=2027, coal_gw=2.1,
         ren_tgt_gw=80.0, ren_cur_gw=40.8, capex_ren=22.0,
         cr_pur=0, cr_ret=4200000, cr_std="Verra VCS",
         icp=True, icp_e=55.0, ccs=0.8, ccs_tgt=4.0),
    dict(id=str(uuid.uuid4()), eid=EN_ORST, yr=2024,
         s1=1820000, s2m=42000, s2l=88000, s3up=480000, s3dn=3200000, s3tot=3680000,
         s3c3=320000, s3c11=2800000, tot_ghg=5542000, tot_vs_base=-72.1,
         bio=42000, nonco2=28000, meth=8000, meth_r=0.04,
         prim=62.0, fos=4.2, nuc=0, ren=57.8, own_mwh=1820000, own_ren_pct=96.0,
         s1_base=2006, s1_base_t=6520000, s1_tgt30=-50.0, s1_tgt50=-100.0,
         s12_tgt30=-55.0, s3_tgt30=-35.0, s3_tgt50=-67.0,
         abs_tgt=910000, ci_tgt30=18.0, ci_tgt40=8.0, ci_tgt50=0.0,
         nzy=2040, sbti=True, sbti_path="1.5C", coal_exit=None, coal_gw=None,
         ren_tgt_gw=35.0, ren_cur_gw=14.8, capex_ren=12.0,
         cr_pur=0, cr_ret=280000, cr_std="Gold Standard",
         icp=True, icp_e=100.0, ccs=0, ccs_tgt=0),
    dict(id=str(uuid.uuid4()), eid=EN_RWE, yr=2024,
         s1=38000000, s2m=820000, s2l=1800000, s3up=8200000, s3dn=42000000, s3tot=50200000,
         s3c3=6200000, s3c11=34000000, tot_ghg=89020000, tot_vs_base=-42.8,
         bio=1200000, nonco2=1400000, meth=180000, meth_r=0.14,
         prim=482.0, fos=184.0, nuc=0, ren=298.0, own_mwh=8200000, own_ren_pct=62.0,
         s1_base=2019, s1_base_t=66400000, s1_tgt30=-50.0, s1_tgt50=-100.0,
         s12_tgt30=-54.0, s3_tgt30=-30.0, s3_tgt50=-55.0,
         abs_tgt=33200000, ci_tgt30=82.0, ci_tgt40=42.0, ci_tgt50=0.0,
         nzy=2040, sbti=True, sbti_path="WELL_BELOW_2C", coal_exit=2030, coal_gw=7.0,
         ren_tgt_gw=65.0, ren_cur_gw=16.4, capex_ren=55.0,
         cr_pur=0, cr_ret=2800000, cr_std="Verra VCS",
         icp=True, icp_e=80.0, ccs=0, ccs_tgt=2.0),
]
for e in ec_data:
    cur.execute("""INSERT INTO energy_csrd_e1_climate
        (id,entity_id,reporting_year,scope1_tco2e,scope2_market_tco2e,scope2_location_tco2e,
         scope3_upstream_tco2e,scope3_downstream_tco2e,scope3_total_tco2e,
         scope3_cat3_energy_related_tco2e,scope3_cat11_use_of_sold_energy_tco2e,
         total_ghg_tco2e,total_ghg_vs_baseline_pct,biogenic_co2_tco2e,
         non_co2_ghg_tco2e,methane_leakage_tco2e,methane_leakage_rate_pct,
         total_primary_energy_twh,fossil_fuel_input_twh,nuclear_input_twh,renewable_input_twh,
         own_energy_consumption_mwh,renewable_energy_own_use_pct,
         scope1_base_year,scope1_base_year_tco2e,scope1_target_reduction_pct_2030,
         scope1_target_reduction_pct_2050,scope12_target_reduction_pct_2030,
         scope3_target_reduction_pct_2030,scope3_target_reduction_pct_2050,
         absolute_target_tco2e_2030,carbon_intensity_target_gco2_kwh_2030,
         carbon_intensity_target_gco2_kwh_2040,carbon_intensity_target_gco2_kwh_2050,
         net_zero_target_year,sbti_committed,sbti_pathway,coal_exit_year,coal_capacity_remaining_gw,
         new_renewable_capacity_target_gw_2030,renewable_capacity_current_gw,
         capex_renewables_committed_bn,carbon_credits_purchased_tco2e,
         carbon_credits_retired_tco2e,carbon_credit_standard,
         has_internal_carbon_price,internal_carbon_price_eur_t,
         ccs_capacity_mtco2_pa,ccs_target_mtco2_pa_2030)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT DO NOTHING""",
        (e["id"],e["eid"],e["yr"],e["s1"],e["s2m"],e["s2l"],
         e["s3up"],e["s3dn"],e["s3tot"],e["s3c3"],e["s3c11"],
         e["tot_ghg"],e["tot_vs_base"],e["bio"],e["nonco2"],e["meth"],e["meth_r"],
         e["prim"],e["fos"],e["nuc"],e["ren"],e["own_mwh"],e["own_ren_pct"],
         e["s1_base"],e["s1_base_t"],e["s1_tgt30"],e["s1_tgt50"],e["s12_tgt30"],
         e["s3_tgt30"],e["s3_tgt50"],e["abs_tgt"],e["ci_tgt30"],e["ci_tgt40"],e["ci_tgt50"],
         e["nzy"],e["sbti"],e["sbti_path"],e["coal_exit"],e["coal_gw"],
         e["ren_tgt_gw"],e["ren_cur_gw"],e["capex_ren"],
         e["cr_pur"],e["cr_ret"],e["cr_std"],e["icp"],e["icp_e"],e["ccs"],e["ccs_tgt"]))

# ── energy_stranded_assets_register ──────────────────────────────────────────
print("Inserting energy_stranded_assets_register…")
sa_data = [
    # ENGIE coal/lignite plants
    dict(id=str(uuid.uuid4()), eid=EN_ENGIE, nm="Hazelwood Power Station",
         ft="coal", co="AUS", cap=1600, comm=1971, orig_dec=2032, rev_dec=2027,
         ecly=5, nbv=480, imp=120, res=80, decom=42, fcf=28.0, ci=820.0,
         s1=4200000, ets_cost=168.0, ets_cum=840.0, breach=True, mrbr=True,
         status="under_decommission", notes="Coal phase-out 2027 aligned"),
    dict(id=str(uuid.uuid4()), eid=EN_ENGIE, nm="Fos-sur-Mer CCGT",
         ft="gas", co="FRA", cap=800, comm=1998, orig_dec=2038, rev_dec=2034,
         ecly=4, nbv=210, imp=40, res=25, decom=18, fcf=42.0, ci=380.0,
         s1=480000, ets_cost=19.2, ets_cum=76.8, breach=False, mrbr=False,
         status="operating", notes="Gas bridge asset; transition risk assessed"),
    # RWE lignite plants
    dict(id=str(uuid.uuid4()), eid=EN_RWE, nm="Niederaussem Power Plant",
         ft="lignite", co="DEU", cap=2800, comm=1963, orig_dec=2035, rev_dec=2030,
         ecly=5, nbv=820, imp=280, res=180, decom=84, fcf=38.0, ci=1180.0,
         s1=14800000, ets_cost=592.0, ets_cum=2960.0, breach=True, mrbr=True,
         status="under_decommission", notes="German coal exit law 2038; RWE voluntary 2030"),
    dict(id=str(uuid.uuid4()), eid=EN_RWE, nm="Neurath Power Plant",
         ft="lignite", co="DEU", cap=2200, comm=1972, orig_dec=2038, rev_dec=2030,
         ecly=8, nbv=640, imp=320, res=220, decom=62, fcf=32.0, ci=1220.0,
         s1=11200000, ets_cost=448.0, ets_cum=3584.0, breach=True, mrbr=True,
         status="under_decommission", notes="Rhineland lignite phase-out 2030"),
    # Ørsted legacy gas (already mostly wound down)
    dict(id=str(uuid.uuid4()), eid=EN_ORST, nm="Esbjerg Power Station",
         ft="gas", co="DNK", cap=626, comm=1992, orig_dec=2028, rev_dec=2024,
         ecly=4, nbv=28, imp=82, res=0, decom=22, fcf=0.0, ci=420.0,
         s1=180000, ets_cost=7.2, ets_cum=7.2, breach=False, mrbr=False,
         status="decommissioned", notes="Converted to energy island support 2024"),
]
for s in sa_data:
    cur.execute("""INSERT INTO energy_stranded_assets_register
        (id,entity_id,plant_name,fuel_type,country_iso,capacity_mw,year_commissioned,
         original_decommission_year,revised_decommission_year,early_closure_years,
         net_book_value_meur,impairment_recognised_meur,residual_impairment_risk_meur,
         decommissioning_provision_meur,annual_fcf_meur,current_ci_gco2_kwh,
         annual_scope1_tco2e,annual_eu_ets_cost_meur,cumulative_eu_ets_cost_to_closure_meur,
         breaches_eu_ets_msfr,below_mrbr_threshold,status,notes)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT DO NOTHING""",
        (s["id"],s["eid"],s["nm"],s["ft"],s["co"],s["cap"],s["comm"],
         s["orig_dec"],s["rev_dec"],s["ecly"],s["nbv"],s["imp"],s["res"],
         s["decom"],s["fcf"],s["ci"],s["s1"],s["ets_cost"],s["ets_cum"],
         s["breach"],s["mrbr"],s["status"],s["notes"]))

# ── energy_renewable_pipeline ─────────────────────────────────────────────────
print("Inserting energy_renewable_pipeline…")
rp_data = [
    # Ørsted — North Sea offshore wind
    dict(id=str(uuid.uuid4()), eid=EN_ORST, nm="Hornsea 4 Offshore Wind",
         pt="WIND_OFFSHORE", co="GBR", reg="North Sea", cap=2600, cf=52.0,
         gen=11882, co2av=4988440, stage="under_construction", cod=2027, grid=2027,
         capex=5800, eq_capex=2900, p_irr=8.4, eq_irr=12.8, lcoe=62.0,
         ppa=0, ppa_t=0, ppa_cp=None, sub="CFD", tax_aln=True, tax_obj=1),
    dict(id=str(uuid.uuid4()), eid=EN_ORST, nm="Baltica 3 Offshore Wind",
         pt="WIND_OFFSHORE", co="POL", reg="Baltic Sea", cap=1500, cf=48.0,
         gen=6307, co2av=2649, stage="early_development", cod=2030, grid=2030,
         capex=3800, eq_capex=1900, p_irr=9.2, eq_irr=13.4, lcoe=68.0,
         ppa=0, ppa_t=0, ppa_cp=None, sub="CFD_POLISH", tax_aln=True, tax_obj=1),
    # RWE — offshore + solar
    dict(id=str(uuid.uuid4()), eid=EN_RWE, nm="Sofia Offshore Wind",
         pt="WIND_OFFSHORE", co="GBR", reg="Dogger Bank", cap=1400, cf=51.0,
         gen=6240, co2av=2620800, stage="under_construction", cod=2026, grid=2026,
         capex=4200, eq_capex=1680, p_irr=7.8, eq_irr=11.8, lcoe=64.0,
         ppa=0, ppa_t=0, ppa_cp=None, sub="CFD", tax_aln=True, tax_obj=1),
    dict(id=str(uuid.uuid4()), eid=EN_RWE, nm="Sunfire TX Solar+Storage",
         pt="SOLAR_PV", co="USA", reg="Texas", cap=1200, cf=28.0,
         gen=2938, co2av=1234960, stage="consented", cod=2026, grid=2026,
         capex=1100, eq_capex=550, p_irr=9.4, eq_irr=13.8, lcoe=32.0,
         ppa=42.0, ppa_t=15, ppa_cp="Google LLC", sub=None, tax_aln=True, tax_obj=1),
    # ENGIE — diverse pipeline
    dict(id=str(uuid.uuid4()), eid=EN_ENGIE, nm="Seagreen Phase 2",
         pt="WIND_OFFSHORE", co="GBR", reg="North Sea", cap=800, cf=49.0,
         gen=3430, co2av=1440600, stage="permitting", cod=2028, grid=2028,
         capex=2400, eq_capex=960, p_irr=8.8, eq_irr=12.4, lcoe=66.0,
         ppa=0, ppa_t=0, ppa_cp=None, sub="CFD", tax_aln=True, tax_obj=1),
    dict(id=str(uuid.uuid4()), eid=EN_ENGIE, nm="Cres Solar Farm FR",
         pt="SOLAR_PV", co="FRA", reg="Occitanie", cap=600, cf=19.0,
         gen=998, co2av=419160, stage="consented", cod=2025, grid=2025,
         capex=480, eq_capex=192, p_irr=8.2, eq_irr=11.4, lcoe=38.0,
         ppa=0, ppa_t=0, ppa_cp=None, sub="FIT", tax_aln=True, tax_obj=1),
    # EDP — Iberian + LATAM
    dict(id=str(uuid.uuid4()), eid=EN_EDP, nm="Terras Altas Wind Farm",
         pt="WIND_ONSHORE", co="PRT", reg="Northern Portugal", cap=420, cf=34.0,
         gen=1249, co2av=524580, stage="under_construction", cod=2026, grid=2026,
         capex=420, eq_capex=168, p_irr=9.8, eq_irr=14.2, lcoe=42.0,
         ppa=52.0, ppa_t=12, ppa_cp="EDP Comercial", sub=None, tax_aln=True, tax_obj=1),
    dict(id=str(uuid.uuid4()), eid=EN_EDP, nm="Ventos do Araripe IV Wind",
         pt="WIND_ONSHORE", co="BRA", reg="Piaui", cap=780, cf=42.0,
         gen=2869, co2av=1204980, stage="permitting", cod=2027, grid=2027,
         capex=680, eq_capex=272, p_irr=11.4, eq_irr=16.2, lcoe=28.0,
         ppa=38.0, ppa_t=20, ppa_cp="Enel Brasil", sub=None, tax_aln=True, tax_obj=1),
]
for r in rp_data:
    cur.execute("""INSERT INTO energy_renewable_pipeline
        (id,entity_id,project_name,project_type,country_iso,region,capacity_mw,
         capacity_factor_pct,expected_generation_gwh_pa,co2_avoided_tco2e_pa,stage,
         cod_year,grid_connection_year,total_capex_meur,equity_capex_meur,
         project_irr_pct,equity_irr_pct,lcoe_eur_per_mwh,ppa_price_eur_per_mwh,
         ppa_term_years,ppa_counterparty,subsidy_type,eu_taxonomy_aligned,taxonomy_objective)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT DO NOTHING""",
        (r["id"],r["eid"],r["nm"],r["pt"],r["co"],r["reg"],r["cap"],
         r["cf"],r["gen"],r["co2av"],r["stage"],r["cod"],r["grid"],
         r["capex"],r["eq_capex"],r["p_irr"],r["eq_irr"],r["lcoe"],
         r["ppa"],r["ppa_t"],r["ppa_cp"],r["sub"],r["tax_aln"],r["tax_obj"]))

conn.commit()
print("Part 3 DONE: energy_financials, generation_mix, csrd_e1_climate, stranded_assets, renewable_pipeline")
conn.close()
