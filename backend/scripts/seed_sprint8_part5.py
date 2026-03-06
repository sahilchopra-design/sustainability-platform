"""Part 5: issb_s1_general, issb_s2_climate, and update csrd_entity_registry FK links"""
import psycopg2, json, uuid
from datetime import datetime

DB_URL = "postgresql://postgres.kytzcbipsghprsqoalvi:KimiaAImpact2026@aws-1-us-east-2.pooler.supabase.com:5432/postgres"
conn = psycopg2.connect(DB_URL)
cur = conn.cursor()

ER_ABN   = "24042b91-c1e4-49e9-8c2b-87c00795c189"
ER_BNP   = "311f362b-359f-49fc-8727-a79e09ccf466"
ER_EDP   = "dd83a823-bdab-4ac4-a1e6-a68413df02ee"
ER_ENGIE = "67d33cba-8df0-4cb6-9384-9f16f851f4b4"
ER_ING   = "5332a58e-7051-4a8e-a1f2-98be78f08bd4"
ER_ORST  = "2436ad78-7f83-4d2e-bbf8-a3180c51a5d3"
ER_RABO  = "8615bc35-8b5a-4085-bfcc-bb8d19f92e7c"
ER_RWE   = "02df2645-a112-41bd-8e3b-86c01adeeb03"

ENTITIES = [ER_ABN, ER_BNP, ER_EDP, ER_ENGIE, ER_ING, ER_ORST, ER_RABO, ER_RWE]

# ── issb_s1_general ───────────────────────────────────────────────────────────
print("Inserting issb_s1_general…")
s1_data = {
    ER_ABN:  dict(gov=True, exp=True, comm=True, mgmt="CRO oversees climate/ESG risks monthly",
                  com=True, rem=True, rem_d="25% of variable compensation linked to sustainability KPIs",
                  sh=1, mh=3, lh=10, res=True, meth="Scenario analysis using NGFS 2023 + IEA WEO",
                  erm=True, app=True, reg=True, tgt=12, sasb="Commercial Banks"),
    ER_BNP:  dict(gov=True, exp=True, comm=True, mgmt="Group Chief Sustainability Officer reports to Board quarterly",
                  com=True, rem=True, rem_d="30% of LTIP linked to financed emissions reduction and social KPIs",
                  sh=1, mh=3, lh=10, res=True, meth="NGFS 2023 + proprietary scenario models",
                  erm=True, app=True, reg=True, tgt=18, sasb="Commercial Banks"),
    ER_EDP:  dict(gov=True, exp=True, comm=True, mgmt="CEO and CFO accountable for climate targets; quarterly board review",
                  com=True, rem=True, rem_d="25% LTI linked to GHG reductions and renewable capacity",
                  sh=1, mh=5, lh=10, res=True, meth="IEA WEO 2023 + NGFS + EDP proprietary model",
                  erm=True, app=True, reg=True, tgt=8, sasb="Electric Utilities & Power Generators"),
    ER_ENGIE:dict(gov=True, exp=True, comm=True, mgmt="Chief Transformation Officer + dedicated Climate Committee",
                  com=True, rem=True, rem_d="35% variable pay linked to decarbonisation milestones and ESG index",
                  sh=1, mh=5, lh=10, res=True, meth="NGFS 2023 + IEA NZE 2050 + RCP scenarios",
                  erm=True, app=True, reg=True, tgt=14, sasb="Electric Utilities & Power Generators"),
    ER_ING:  dict(gov=True, exp=True, comm=True, mgmt="Chief Sustainability Officer with direct board access; monthly updates",
                  com=True, rem=True, rem_d="20% of variable pay linked to Terra portfolio alignment targets",
                  sh=1, mh=3, lh=10, res=True, meth="PACTA + NGFS 2023 + client-level scenario analysis",
                  erm=True, app=True, reg=True, tgt=16, sasb="Commercial Banks"),
    ER_ORST: dict(gov=True, exp=True, comm=True, mgmt="Board-level ESG Committee; CEO accountability for net zero delivery",
                  com=True, rem=True, rem_d="40% of LTI linked to offshore wind build-out and carbon intensity",
                  sh=1, mh=5, lh=10, res=True, meth="IEA NZE 2050 + NGFS 2023 + IPCC AR6",
                  erm=True, app=True, reg=True, tgt=10, sasb="Electric Utilities & Power Generators"),
    ER_RABO: dict(gov=True, exp=True, comm=True, mgmt="Managing Board ESG Committee; sustainability embedded in credit decisions",
                  com=True, rem=True, rem_d="18% of variable pay tied to financed emissions and food systems targets",
                  sh=1, mh=3, lh=10, res=True, meth="NGFS 2023 + PACTA + food & agriculture scenario models",
                  erm=True, app=True, reg=True, tgt=14, sasb="Commercial Banks"),
    ER_RWE:  dict(gov=True, exp=True, comm=True, mgmt="Supervisory Board sustainability committee; quarterly KPI reporting",
                  com=True, rem=True, rem_d="30% of LTI linked to green capacity additions and lignite exit progress",
                  sh=1, mh=5, lh=10, res=True, meth="NGFS 2023 + IEA WEO + EU ETS price scenarios",
                  erm=True, app=True, reg=True, tgt=12, sasb="Electric Utilities & Power Generators"),
}
for er, d in s1_data.items():
    cur.execute("""INSERT INTO issb_s1_general
        (id,entity_registry_id,reporting_year,consolidation_approach,reporting_boundary_coverage_pct,
         is_assured,assurance_level,data_quality_score,status,
         governance_body_oversees_sustainability_risks,governance_body_sustainability_expertise,
         governance_sustainability_oversight_mechanism,management_role_in_sustainability,
         sustainability_committee_exists,sustainability_integrated_in_remuneration,
         sustainability_pay_link_description,short_term_horizon_years,medium_term_horizon_years,
         long_term_horizon_years,resilience_assessment_conducted,resilience_assessment_methodology,
         sustainability_risk_integrated_in_erm,sustainability_risk_appetite_defined,
         sustainability_risk_register_exists,sustainability_targets_count,industry_based_metrics_sasb_standard)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT DO NOTHING""",
        (str(uuid.uuid4()),er,2024,"FULL_CONSOLIDATION",100.0,
         True,"LIMITED",3,"PUBLISHED",
         d["gov"],d["exp"],d["comm"],d["mgmt"],d["com"],d["rem"],d["rem_d"],
         d["sh"],d["mh"],d["lh"],d["res"],d["meth"],d["erm"],d["app"],d["reg"],
         d["tgt"],d["sasb"]))

# ── issb_s2_climate ────────────────────────────────────────────────────────────
print("Inserting issb_s2_climate…")
s2_data = {
    ER_ABN:  dict(bc_exp=True, bc_mech="Board reviews climate risk annually; TCFD aligned",
                  mgmt="CRO quarterly climate risk report", exec_inc=True, exec_pct=18.0,
                  sh=1, mh=3, lh=10, phy_r=True, tr_r=True, opp=True,
                  res=True, scen=True, tp=True, nzy=2050, erm=True, freq="ANNUAL",
                  s1=6200, s2l=2800, s2m=2100, s3=18400,
                  ghp="GHG Protocol Corporate Standard", gwp="AR6",
                  coal_pct=0.0, og_pct=2.8, oth_fos=0.0, fi_em=22960000, fi_meth="PCAF Standard v1.1",
                  temp=1.92, gar=16.2, capex_cl=1200, capex_pct=14.8, icp=True, icp_e=65.0),
    ER_BNP:  dict(bc_exp=True, bc_mech="Dedicated Board Climate Committee; quarterly deep dives",
                  mgmt="Group CSO reports to CEO; climate integrated in risk appetite",
                  exec_inc=True, exec_pct=22.0, sh=1, mh=3, lh=10,
                  phy_r=True, tr_r=True, opp=True, res=True, scen=True, tp=True, nzy=2050,
                  erm=True, freq="QUARTERLY",
                  s1=18400, s2l=5600, s2m=4200, s3=42000,
                  ghp="GHG Protocol Corporate Standard", gwp="AR6",
                  coal_pct=0.2, og_pct=4.8, oth_fos=0.1, fi_em=471000000, fi_meth="PCAF Standard v1.1",
                  temp=1.86, gar=12.7, capex_cl=2800, capex_pct=6.2, icp=True, icp_e=55.0),
    ER_EDP:  dict(bc_exp=True, bc_mech="Board-level Sustainability & Climate Committee",
                  mgmt="CEO/CFO climate KPIs; dedicated Climate Risk Unit in CRO",
                  exec_inc=True, exec_pct=25.0, sh=1, mh=5, lh=10,
                  phy_r=True, tr_r=True, opp=True, res=True, scen=True, tp=True, nzy=2040,
                  erm=True, freq="SEMI_ANNUAL",
                  s1=4200000, s2l=620000, s2m=280000, s3=10200000,
                  ghp="GHG Protocol Corporate Standard", gwp="AR6",
                  coal_pct=0.0, og_pct=19.7, oth_fos=0.0, fi_em=0, fi_meth=None,
                  temp=None, gar=72.4, capex_cl=3100, capex_pct=64.6, icp=True, icp_e=75.0),
    ER_ENGIE:dict(bc_exp=True, bc_mech="Ethics, Environment & Sustainable Development Committee",
                  mgmt="Chief Transformation Officer; integrated ERM climate overlay",
                  exec_inc=True, exec_pct=28.0, sh=1, mh=5, lh=10,
                  phy_r=True, tr_r=True, opp=True, res=True, scen=True, tp=True, nzy=2045,
                  erm=True, freq="QUARTERLY",
                  s1=48000000, s2l=2800000, s2m=1200000, s3=94000000,
                  ghp="GHG Protocol Corporate Standard", gwp="AR6",
                  coal_pct=0.0, og_pct=32.4, oth_fos=0.0, fi_em=0, fi_meth=None,
                  temp=None, gar=68.2, capex_cl=7800, capex_pct=65.0, icp=True, icp_e=55.0),
    ER_ING:  dict(bc_exp=True, bc_mech="Board Risk Committee with dedicated climate slot quarterly",
                  mgmt="CRO owns climate risk; Terra programme lead reports monthly",
                  exec_inc=True, exec_pct=15.0, sh=1, mh=3, lh=10,
                  phy_r=True, tr_r=True, opp=True, res=True, scen=True, tp=True, nzy=2050,
                  erm=True, freq="QUARTERLY",
                  s1=9100, s2l=3600, s2m=2800, s3=26000,
                  ghp="GHG Protocol Corporate Standard", gwp="AR6",
                  coal_pct=0.0, og_pct=2.2, oth_fos=0.0, fi_em=150000000, fi_meth="PCAF Standard v1.1",
                  temp=1.79, gar=14.7, capex_cl=820, capex_pct=4.1, icp=True, icp_e=75.0),
    ER_ORST: dict(bc_exp=True, bc_mech="Full Board oversees climate; Board member sustainability expertise required",
                  mgmt="CEO primary accountability; dedicated Head of Climate Risk",
                  exec_inc=True, exec_pct=32.0, sh=1, mh=5, lh=10,
                  phy_r=True, tr_r=True, opp=True, res=True, scen=True, tp=True, nzy=2040,
                  erm=True, freq="QUARTERLY",
                  s1=1820000, s2l=88000, s2m=42000, s3=3680000,
                  ghp="GHG Protocol Corporate Standard", gwp="AR6",
                  coal_pct=0.0, og_pct=0.0, oth_fos=0.0, fi_em=0, fi_meth=None,
                  temp=None, gar=96.8, capex_cl=7400, capex_pct=90.2, icp=True, icp_e=100.0),
    ER_RABO: dict(bc_exp=True, bc_mech="Supervisory Board receives quarterly climate risk updates",
                  mgmt="Managing Board ESG Committee; climate risk integrated in credit process",
                  exec_inc=True, exec_pct=14.0, sh=1, mh=3, lh=10,
                  phy_r=True, tr_r=True, opp=True, res=True, scen=True, tp=True, nzy=2050,
                  erm=True, freq="ANNUAL",
                  s1=4800, s2l=1800, s2m=1200, s3=14000,
                  ghp="GHG Protocol Corporate Standard", gwp="AR6",
                  coal_pct=0.0, og_pct=1.8, oth_fos=0.0, fi_em=62200000, fi_meth="PCAF Standard v1.1",
                  temp=1.74, gar=15.4, capex_cl=280, capex_pct=2.3, icp=True, icp_e=60.0),
    ER_RWE:  dict(bc_exp=True, bc_mech="Supervisory Board Sustainability Committee; monthly CEO briefs",
                  mgmt="Chief Sustainability Officer reports to CEO; Board KPI dashboard",
                  exec_inc=True, exec_pct=26.0, sh=1, mh=5, lh=10,
                  phy_r=True, tr_r=True, opp=True, res=True, scen=True, tp=True, nzy=2040,
                  erm=True, freq="QUARTERLY",
                  s1=38000000, s2l=1800000, s2m=820000, s3=50200000,
                  ghp="GHG Protocol Corporate Standard", gwp="AR6",
                  coal_pct=0.0, og_pct=12.5, oth_fos=0.0, fi_em=0, fi_meth=None,
                  temp=None, gar=58.4, capex_cl=5200, capex_pct=76.5, icp=True, icp_e=80.0),
}
for er, d in s2_data.items():
    cur.execute("""INSERT INTO issb_s2_climate
        (id,entity_registry_id,reporting_year,consolidation_approach,reporting_boundary_coverage_pct,
         is_assured,assurance_level,data_quality_score,status,
         board_climate_oversight_mechanism,board_climate_expertise,management_climate_role,
         executive_climate_incentives,executive_climate_incentive_pct_of_variable,
         short_term_horizon_years,medium_term_horizon_years,long_term_horizon_years,
         physical_risks_identified,transition_risks_identified,climate_opportunities_identified,
         climate_resilience_assessment_conducted,climate_scenarios_used,
         transition_plan_in_place,transition_plan_net_zero_year,climate_risk_integrated_in_erm,
         scenario_analysis_frequency,
         scope1_gross_tco2e,scope2_location_based_tco2e,scope2_market_based_tco2e,scope3_total_tco2e,
         ghg_protocol_standard_used,gwp_standard,
         revenue_from_coal_pct,revenue_from_oil_and_gas_pct,revenue_from_other_fossil_pct,
         financed_emissions_total_tco2e,financed_emissions_methodology,
         portfolio_temperature_alignment_c,green_asset_ratio_pct,
         climate_total_capex_meur,climate_capex_pct_of_total,
         has_internal_carbon_price,internal_carbon_price_eur_per_tco2e)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT DO NOTHING""",
        (str(uuid.uuid4()),er,2024,"FULL_CONSOLIDATION",100.0,
         True,"LIMITED",3,"PUBLISHED",
         d["bc_mech"],d["bc_exp"],d["mgmt"],d["exec_inc"],d["exec_pct"],
         d["sh"],d["mh"],d["lh"],
         json.dumps({"physical_risks_identified": True}),
         json.dumps({"transition_risks_identified": True}),
         json.dumps({"opportunities": True}),
         d["res"],json.dumps({"scenarios": ["NGFS Net Zero 2050","Delayed Transition","Hot House World"]}),
         d["tp"],d["nzy"],d["erm"],d["freq"],
         d["s1"],d["s2l"],d["s2m"],d["s3"],d["ghp"],d["gwp"],
         d["coal_pct"],d["og_pct"],d["oth_fos"],
         d["fi_em"],d["fi_meth"],d["temp"],d["gar"],
         d["capex_cl"],d["capex_pct"],d["icp"],d["icp_e"]))

# ── Update csrd_entity_registry FK links ──────────────────────────────────────
print("Updating csrd_entity_registry FK links (fi_entity_id, energy_entity_id)…")
cur.execute("SELECT id,legal_name FROM fi_entities")
fi_map = {row[1]: row[0] for row in cur.fetchall()}
cur.execute("SELECT id,legal_name FROM energy_entities")
en_map = {row[1]: row[0] for row in cur.fetchall()}

links = {
    ER_ABN:   ("fi_entity_id",     fi_map["ABN AMRO Bank N.V."]),
    ER_BNP:   ("fi_entity_id",     fi_map["BNP Paribas S.A."]),
    ER_ING:   ("fi_entity_id",     fi_map["ING Groep N.V."]),
    ER_RABO:  ("fi_entity_id",     fi_map["Coöperatieve Rabobank U.A."]),
    ER_EDP:   ("energy_entity_id", en_map["EDP \u2013 Energias de Portugal S.A."]),
    ER_ENGIE: ("energy_entity_id", en_map["ENGIE S.A."]),
    ER_ORST:  ("energy_entity_id", en_map["\u00d8rsted A/S"]),
    ER_RWE:   ("energy_entity_id", en_map["RWE Aktiengesellschaft"]),
}
for er_id, (col, val) in links.items():
    cur.execute(f"UPDATE csrd_entity_registry SET {col} = %s WHERE id = %s", (val, er_id))
    print(f"  Updated {er_id[:8]}... -> {col} = {val[:8]}...")

conn.commit()
print("Part 5 DONE: issb_s1_general, issb_s2_climate, csrd_entity_registry FK links updated")
conn.close()
