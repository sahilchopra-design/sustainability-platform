"""Part 2: fi_paris_alignment, fi_csrd_e1_climate, fi_green_finance, fi_loan_books"""
import psycopg2, json, uuid
from datetime import datetime, date

DB_URL = "postgresql://postgres.kytzcbipsghprsqoalvi:KimiaAImpact2026@aws-1-us-east-2.pooler.supabase.com:5432/postgres"

# ── FI entity IDs — must match Part 1 UUIDs; we re-query them from DB ─────────
conn = psycopg2.connect(DB_URL)
cur = conn.cursor()
cur.execute("SELECT id,legal_name FROM fi_entities ORDER BY legal_name")
fi_map = {row[1]: row[0] for row in cur.fetchall()}
print("FI entities found:", list(fi_map.keys()))

FI_ABN  = fi_map["ABN AMRO Bank N.V."]
FI_BNP  = fi_map["BNP Paribas S.A."]
FI_ING  = fi_map["ING Groep N.V."]
FI_RABO = fi_map["Coöperatieve Rabobank U.A."]

# ── fi_paris_alignment ────────────────────────────────────────────────────────
print("Inserting fi_paris_alignment…")
pa_rows = [
    dict(id=str(uuid.uuid4()), eid=FI_ABN, year=2024, method="PACTA 2023",
         port_score=2.1, port_cat="PARTIALLY_ALIGNED", engaged=48, voted_climate=32,
         voted_for_pct=72.0, escal=8, divest=2, coal_thr=5.0,
         coal_excl=True, oil_sands=True, arctic=True, mtr=True, new_coal=True),
    dict(id=str(uuid.uuid4()), eid=FI_BNP, year=2024, method="PACTA 2023",
         port_score=2.3, port_cat="PARTIALLY_ALIGNED", engaged=120, voted_climate=94,
         voted_for_pct=68.0, escal=18, divest=5, coal_thr=5.0,
         coal_excl=True, oil_sands=True, arctic=True, mtr=True, new_coal=True),
    dict(id=str(uuid.uuid4()), eid=FI_ING, year=2024, method="PACTA 2023",
         port_score=1.9, port_cat="ALIGNED", engaged=62, voted_climate=48,
         voted_for_pct=79.0, escal=11, divest=3, coal_thr=5.0,
         coal_excl=True, oil_sands=True, arctic=True, mtr=True, new_coal=True),
    dict(id=str(uuid.uuid4()), eid=FI_RABO, year=2024, method="PACTA 2023",
         port_score=1.8, port_cat="ALIGNED", engaged=34, voted_climate=None,
         voted_for_pct=None, escal=6, divest=1, coal_thr=5.0,
         coal_excl=True, oil_sands=True, arctic=True, mtr=True, new_coal=True),
]
for p in pa_rows:
    cur.execute("""INSERT INTO fi_paris_alignment
        (id,entity_id,reporting_year,methodology,portfolio_alignment_score,
         portfolio_alignment_category,engaged_companies_count,
         voted_resolutions_climate_count,voted_for_climate_pct,
         escalation_actions_count,divestment_count,thermal_coal_threshold_revenue_pct,
         oil_sands_excluded,arctic_drilling_excluded,mountaintop_removal_excluded,new_coal_power_excluded)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
        (p["id"],p["eid"],p["year"],p["method"],p["port_score"],p["port_cat"],
         p["engaged"],p["voted_climate"],p["voted_for_pct"],p["escal"],p["divest"],
         p["coal_thr"],p["oil_sands"],p["arctic"],p["mtr"],p["new_coal"]))

# ── fi_csrd_e1_climate ────────────────────────────────────────────────────────
print("Inserting fi_csrd_e1_climate…")
cl_data = [
    dict(id=str(uuid.uuid4()), eid=FI_ABN,  year=2024,
         tp=True, tp_par=True, tp_sc="OPERATIONAL_AND_FINANCED", tp_base=2019, tp_tgt=2050,
         sbti=True, sbti_dt=date(2022,10,12), nzy=2050, pol=True, pol_b=True,
         a1=-42.0, a2=-56.0, a3=-16.0, fe=-40.0, re_tgt=100.0,
         en=312000, fos=98000, nuc=0, ren=214000, ren_pct=68.0, re100=True, re100c=True, ppa=450.0,
         s1=6200, s2m=2100, s2l=2800, s3=18400, s3c15=22960000, bio=820, rem=0, cr=180000, cr_std="Gold Standard",
         s1b=2019, s1bt=14800, s1y=-8.2, s2y=-12.1, fey=-5.3,
         pd=True, ac=2800, ch=4100, fl=1900, ht=3200, icp=True, icp_e=65.0, shad=100.0,
         scen=True, tr_q=True, tr_c=1.8, ph_c=2.4),
    dict(id=str(uuid.uuid4()), eid=FI_BNP,  year=2024,
         tp=True, tp_par=True, tp_sc="OPERATIONAL_AND_FINANCED", tp_base=2019, tp_tgt=2050,
         sbti=True, sbti_dt=date(2023,2,8), nzy=2050, pol=True, pol_b=True,
         a1=-52.0, a2=-61.0, a3=-20.0, fe=-30.0, re_tgt=100.0,
         en=810000, fos=228000, nuc=0, ren=582000, ren_pct=72.0, re100=True, re100c=True, ppa=1200.0,
         s1=18400, s2m=4200, s2l=5600, s3=42000, s3c15=471000000, bio=1820, rem=0, cr=420000, cr_std="Verra VCS",
         s1b=2019, s1bt=38400, s1y=-9.1, s2y=-14.2, fey=-6.1,
         pd=True, ac=8400, ch=12200, fl=6800, ht=11000, icp=True, icp_e=55.0, shad=100.0,
         scen=True, tr_q=True, tr_c=2.1, ph_c=2.9),
    dict(id=str(uuid.uuid4()), eid=FI_ING,  year=2024,
         tp=True, tp_par=True, tp_sc="OPERATIONAL_AND_FINANCED", tp_base=2019, tp_tgt=2050,
         sbti=True, sbti_dt=date(2022,4,21), nzy=2050, pol=True, pol_b=True,
         a1=-48.0, a2=-63.0, a3=-50.0, fe=-50.0, re_tgt=100.0,
         en=420000, fos=0, nuc=0, ren=420000, ren_pct=100.0, re100=True, re100c=True, ppa=680.0,
         s1=9100, s2m=2800, s2l=3600, s3=26000, s3c15=150000000, bio=940, rem=0, cr=210000, cr_std="Gold Standard",
         s1b=2019, s1bt=17400, s1y=-7.6, s2y=-15.4, fey=-8.2,
         pd=True, ac=4200, ch=6800, fl=3600, ht=5900, icp=True, icp_e=75.0, shad=100.0,
         scen=True, tr_q=True, tr_c=1.6, ph_c=2.1),
    dict(id=str(uuid.uuid4()), eid=FI_RABO, year=2024,
         tp=True, tp_par=True, tp_sc="OPERATIONAL_AND_FINANCED", tp_base=2019, tp_tgt=2050,
         sbti=True, sbti_dt=date(2022,9,15), nzy=2050, pol=True, pol_b=True,
         a1=-38.0, a2=-58.0, a3=-45.0, fe=-45.0, re_tgt=100.0,
         en=198000, fos=0, nuc=0, ren=198000, ren_pct=100.0, re100=True, re100c=True, ppa=320.0,
         s1=4800, s2m=1200, s2l=1800, s3=14000, s3c15=62200000, bio=480, rem=0, cr=85000, cr_std="Gold Standard",
         s1b=2019, s1bt=7800, s1y=-6.9, s2y=-12.8, fey=-4.8,
         pd=True, ac=1800, ch=2900, fl=2200, ht=1400, icp=True, icp_e=60.0, shad=100.0,
         scen=True, tr_q=True, tr_c=1.4, ph_c=1.9),
]
for c in cl_data:
    cur.execute("""INSERT INTO fi_csrd_e1_climate
        (id,entity_id,reporting_year,has_transition_plan,transition_plan_aligned_paris,
         transition_plan_scope,transition_plan_base_year,transition_plan_target_year,
         sbti_committed,sbti_approval_date,net_zero_target_year,
         climate_policy_in_place,climate_policy_board_approved,
         absolute_scope1_target_pct,absolute_scope2_target_pct,absolute_scope3_target_pct,
         financed_emissions_target_pct,renewable_energy_target_pct,
         total_energy_consumption_mwh,fossil_fuel_consumption_mwh,nuclear_consumption_mwh,
         renewable_consumption_mwh,renewable_energy_pct,has_100pct_renewable_electricity,
         re100_committed,ppa_capacity_mw,
         scope1_tco2e,scope2_market_tco2e,scope2_location_tco2e,scope3_total_tco2e,
         scope3_cat15_financed_tco2e,biogenic_co2_tco2e,ghg_removals_tco2e,
         carbon_credits_retired_tco2e,carbon_credit_standard,
         scope1_base_year,scope1_base_year_tco2e,scope1_yoy_change_pct,
         scope2_yoy_change_pct,financed_yoy_change_pct,
         physical_risk_assessment_completed,acute_risk_high_ead_meur,chronic_risk_high_ead_meur,
         flood_exposed_re_ead_meur,heat_stress_exposed_ead_meur,
         has_internal_carbon_price,internal_carbon_price_eur_t,shadow_carbon_price_eur_t,
         transition_risk_quantified,transition_risk_max_impact_pct_cet1,physical_risk_max_impact_pct_cet1)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT DO NOTHING""",
        (c["id"],c["eid"],c["year"],c["tp"],c["tp_par"],c["tp_sc"],c["tp_base"],c["tp_tgt"],
         c["sbti"],c["sbti_dt"],c["nzy"],c["pol"],c["pol_b"],
         c["a1"],c["a2"],c["a3"],c["fe"],c["re_tgt"],
         c["en"],c["fos"],c["nuc"],c["ren"],c["ren_pct"],c["re100"],c["re100c"],c["ppa"],
         c["s1"],c["s2m"],c["s2l"],c["s3"],c["s3c15"],c["bio"],c["rem"],c["cr"],c["cr_std"],
         c["s1b"],c["s1bt"],c["s1y"],c["s2y"],c["fey"],
         c["pd"],c["ac"],c["ch"],c["fl"],c["ht"],c["icp"],c["icp_e"],c["shad"],
         c["scen"],c["tr_c"],c["ph_c"]))

# ── fi_green_finance ──────────────────────────────────────────────────────────
print("Inserting fi_green_finance…")
gf_data = [
    dict(id=str(uuid.uuid4()), eid=FI_ABN,  year=2024, cu="EUR",
         sf=42.0, sf_a=9.2, gl=8.1, gb_uw=6.2, gb_is=2.0, sll=12.4, slb=4.1,
         sol=1.2, sob=0.8, tr=3.6, bl=0.4, cl=14.2, na=0.6,
         ah=2.1, sm=3.8, eal=5.8, eel=12.0, ep=13.8,
         ct=60.0, ty=2025, pr=70.0, gbf=True, gbfv="DNV GL", sff=True,
         cpo=True, cpy=2030, ncm=False),
    dict(id=str(uuid.uuid4()), eid=FI_BNP,  year=2024, cu="EUR",
         sf=300.0, sf_a=68.0, gl=52.0, gb_uw=88.0, gb_is=12.0, sll=82.0, slb=28.0,
         sol=9.0, sob=6.0, tr=18.0, bl=2.2, cl=98.0, na=4.2,
         ah=12.0, sm=22.0, eal=38.0, eel=84.0, ep=12.7,
         ct=400.0, ty=2025, pr=75.0, gbf=True, gbfv="ISS ESG", sff=True,
         cpo=True, cpy=2030, ncm=False),
    dict(id=str(uuid.uuid4()), eid=FI_ING,  year=2024, cu="EUR",
         sf=150.0, sf_a=32.0, gl=28.0, gb_uw=42.0, gb_is=8.0, sll=48.0, slb=14.0,
         sol=4.2, sob=2.8, tr=9.0, bl=1.2, cl=52.0, na=2.4,
         ah=7.0, sm=12.0, eal=22.0, eel=48.0, ep=14.7,
         ct=200.0, ty=2025, pr=75.0, gbf=True, gbfv="Sustainalytics", sff=True,
         cpo=True, cpy=2025, ncm=False),
    dict(id=str(uuid.uuid4()), eid=FI_RABO, year=2024, cu="EUR",
         sf=78.0, sf_a=16.0, gl=18.0, gb_uw=12.0, gb_is=4.0, sll=24.0, slb=8.0,
         sol=3.2, sob=1.8, tr=6.0, bl=0.8, cl=28.0, na=3.8,
         ah=4.2, sm=8.0, eal=12.0, eel=26.0, ep=15.4,
         ct=100.0, ty=2025, pr=78.0, gbf=True, gbfv="Vigeo Eiris", sff=True,
         cpo=True, cpy=2025, ncm=False),
]
for g in gf_data:
    cur.execute("""INSERT INTO fi_green_finance
        (id,entity_id,reporting_year,currency,sustainable_finance_total_bn,
         sustainable_finance_annual_bn,green_loans_bn,green_bonds_underwritten_bn,
         green_bonds_issued_bn,sustainability_linked_loans_bn,sustainability_linked_bonds_bn,
         social_loans_bn,social_bonds_bn,transition_finance_bn,blended_finance_bn,
         climate_finance_bn,nature_finance_bn,affordable_housing_bn,sme_sustainability_bn,
         eu_taxonomy_aligned_green_bn,eu_taxonomy_eligible_green_bn,eu_taxonomy_aligned_pct,
         cumulative_target_bn,target_year,progress_pct,
         has_green_bond_framework,green_bond_framework_verifier,has_sustainable_finance_framework,
         coal_phase_out_committed,coal_phase_out_year,new_coal_mines_committed)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT DO NOTHING""",
        (g["id"],g["eid"],g["year"],g["cu"],g["sf"],g["sf_a"],g["gl"],g["gb_uw"],
         g["gb_is"],g["sll"],g["slb"],g["sol"],g["sob"],g["tr"],g["bl"],
         g["cl"],g["na"],g["ah"],g["sm"],g["eal"],g["eel"],g["ep"],
         g["ct"],g["ty"],g["pr"],g["gbf"],g["gbfv"],g["sff"],g["cpo"],g["cpy"],g["ncm"]))

# ── fi_loan_books ─────────────────────────────────────────────────────────────
print("Inserting fi_loan_books…")
lb_data = [
    dict(uid=str(uuid.uuid4()), eid=FI_ABN, year=2024, cu="EUR",
         rc=38000, rr=82000, eo=6200, er=4100, ut=3800, ch=1200, ind=8400, tr=9200, ag=7600, mi=1400,
         cd=14000, cs=8200, fi=12000, te=6800, he=4200, gv=9800, sm=28000, mo=62000, co=18000,
         ffe=4800, cm=800, tp=1600, ci=14200, cp=5.6, gl=6200, sl=8400, pa=42000, pp=16.8,
         fl=8200, ca=4100, wi=1200, ph=9800, php=3.9, te2=253000, tg=253000),
    dict(uid=str(uuid.uuid4()), eid=FI_BNP, year=2024, cu="EUR",
         rc=98000, rr=142000, eo=52000, er=28000, ut=18000, ch=12000, ind=42000, tr=38000, ag=22000, mi=8200,
         cd=48000, cs=32000, fi=68000, te=42000, he=18000, gv=62000, sm=88000, mo=142000, co=48000,
         ffe=32000, cm=4200, tp=8800, ci=68000, cp=7.9, gl=28000, sl=42000, pa=168000, pp=19.6,
         fl=38000, ca=22000, wi=8400, ph=48000, php=5.6, te2=856000, tg=856000),
    dict(uid=str(uuid.uuid4()), eid=FI_ING, year=2024, cu="EUR",
         rc=62000, rr=128000, eo=28000, er=18000, ut=12000, ch=8200, ind=28000, tr=24000, ag=32000, mi=4200,
         cd=32000, cs=22000, fi=42000, te=28000, he=12000, gv=38000, sm=62000, mo=128000, co=38000,
         ffe=18000, cm=2200, tp=4800, ci=38000, cp=5.9, gl=18000, sl=28000, pa=118000, pp=18.5,
         fl=28000, ca=14000, wi=4200, ph=32000, php=5.0, te2=637000, tg=637000),
    dict(uid=str(uuid.uuid4()), eid=FI_RABO, year=2024, cu="EUR",
         rc=42000, rr=88000, eo=12000, er=8200, ut=6200, ch=3800, ind=14000, tr=12000, ag=62000, mi=2200,
         cd=14000, cs=12000, fi=18000, te=8200, he=6200, gv=18000, sm=42000, mo=88000, co=22000,
         ffe=8200, cm=800, tp=1800, ci=18000, cp=4.6, gl=8200, sl=12000, pa=68000, pp=17.2,
         fl=14000, ca=6200, wi=2200, ph=16000, php=4.1, te2=395000, tg=395000),
]
for lb in lb_data:
    cur.execute("""INSERT INTO fi_loan_books
        (id,entity_id,reporting_year,currency,
         real_estate_commercial_ead,real_estate_residential_ead,
         energy_oil_gas_ead,energy_renewables_ead,utilities_ead,chemicals_ead,
         industrials_ead,transport_ead,agriculture_ead,mining_ead,
         consumer_discretionary_ead,consumer_staples_ead,financials_ead,
         technology_ead,healthcare_ead,government_public_ead,
         sme_ead,retail_mortgage_ead,retail_consumer_ead,
         fossil_fuel_extraction_ead,coal_mining_ead,thermal_power_ead,
         carbon_intensive_sectors_ead,carbon_intensive_sectors_pct,
         green_loans_ead,sustainability_linked_loans_ead,
         paris_aligned_ead,paris_aligned_pct,
         flood_zone_re_ead,coastal_re_ead,wildfire_risk_ead,
         physical_risk_high_ead,physical_risk_high_pct,
         total_ead,total_loans_gross)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT DO NOTHING""",
        (lb["uid"],lb["eid"],lb["year"],lb["cu"],
         lb["rc"],lb["rr"],lb["eo"],lb["er"],lb["ut"],lb["ch"],
         lb["ind"],lb["tr"],lb["ag"],lb["mi"],
         lb["cd"],lb["cs"],lb["fi"],lb["te"],lb["he"],lb["gv"],
         lb["sm"],lb["mo"],lb["co"],
         lb["ffe"],lb["cm"],lb["tp"],lb["ci"],lb["cp"],
         lb["gl"],lb["sl"],lb["pa"],lb["pp"],
         lb["fl"],lb["ca"],lb["wi"],lb["ph"],lb["php"],
         lb["te2"],lb["tg"]))

conn.commit()
print("Part 2 DONE: fi_paris_alignment, fi_csrd_e1_climate, fi_green_finance, fi_loan_books")
conn.close()
