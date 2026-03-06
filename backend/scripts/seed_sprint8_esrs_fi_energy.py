"""
Sprint 8 Seed Script — ESRS/ISSB + FI Sector + Energy Sector + Portfolio Analytics
Covers: fi_entities, fi_financials, fi_financed_emissions, fi_paris_alignment,
        fi_csrd_e1_climate, fi_green_finance, fi_loan_books,
        energy_entities, energy_financials, energy_generation_mix,
        energy_csrd_e1_climate, energy_stranded_assets_register, energy_renewable_pipeline,
        esrs2_general_disclosures, esrs_e1_ghg_emissions, esrs_e1_energy,
        esrs_e1_financial_effects, esrs_e2_pollution, esrs_e3_water,
        esrs_e4_biodiversity, esrs_e5_circular, esrs_s1_workforce,
        esrs_g1_conduct, issb_s1_general, issb_s2_climate
Anchor entities from csrd_entity_registry (pre-existing from CSRD pipeline):
  ABN AMRO   24042b91-c1e4-49e9-8c2b-87c00795c189  NLD FI
  BNP Paribas 311f362b-359f-49fc-8727-a79e09ccf466 FRA FI
  EDP        dd83a823-bdab-4ac4-a1e6-a68413df02ee  PRT Energy
  ENGIE      67d33cba-8df0-4cb6-9384-9f16f851f4b4  FRA Energy
  ING Group  5332a58e-7051-4a8e-a1f2-98be78f08bd4  NLD FI
  Ørsted     2436ad78-7f83-4d2e-bbf8-a3180c51a5d3  DNK Energy
  Rabobank   8615bc35-8b5a-4085-bfcc-bb8d19f92e7c  NLD FI
  RWE Group  02df2645-a112-41bd-8e3b-86c01adeeb03  DEU Energy
"""

import psycopg2, json, uuid
from datetime import datetime, date

DB_URL = "postgresql://postgres.kytzcbipsghprsqoalvi:KimiaAImpact2026@aws-1-us-east-2.pooler.supabase.com:5432/postgres"

# ── csrd_entity_registry IDs (pre-existing) ──────────────────────────────────
ER_ABN   = "24042b91-c1e4-49e9-8c2b-87c00795c189"
ER_BNP   = "311f362b-359f-49fc-8727-a79e09ccf466"
ER_EDP   = "dd83a823-bdab-4ac4-a1e6-a68413df02ee"
ER_ENGIE = "67d33cba-8df0-4cb6-9384-9f16f851f4b4"
ER_ING   = "5332a58e-7051-4a8e-a1f2-98be78f08bd4"
ER_ORSTED = "2436ad78-7f83-4d2e-bbf8-a3180c51a5d3"
ER_RABO  = "8615bc35-8b5a-4085-bfcc-bb8d19f92e7c"
ER_RWE   = "02df2645-a112-41bd-8e3b-86c01adeeb03"

# ── New UUIDs for fi_entities ─────────────────────────────────────────────────
FI_ABN   = str(uuid.uuid4())
FI_BNP   = str(uuid.uuid4())
FI_ING   = str(uuid.uuid4())
FI_RABO  = str(uuid.uuid4())

# ── New UUIDs for energy_entities ────────────────────────────────────────────
EN_EDP   = str(uuid.uuid4())
EN_ENGIE = str(uuid.uuid4())
EN_ORSTED= str(uuid.uuid4())
EN_RWE   = str(uuid.uuid4())

def j(obj): return json.dumps(obj)

def run():
    conn = psycopg2.connect(DB_URL)
    cur  = conn.cursor()
    now  = datetime.utcnow()

    # ── 1. fi_entities ────────────────────────────────────────────────────────
    print("Inserting fi_entities…")
    fi_rows = [
        (FI_ABN,  "ABN AMRO Bank N.V.", "ABN AMRO", "724500HEBSOB36860721", "ABNANL2A",
         "universal_bank", "ECB_SSM", "NLD", "EURONEXT", "NL0011540547", "ABN", 2024, True),
        (FI_BNP,  "BNP Paribas S.A.", "BNP Paribas", "R0MUWSFPU8MPRO8K5P83", "BNPAFRPP",
         "universal_bank", "ECB_SSM", "FRA", "EURONEXT", "FR0000131104", "BNP", 2024, True),
        (FI_ING,  "ING Groep N.V.", "ING", "3TK20IVIUJ8J3ZU0QE75", "INGBNL2A",
         "universal_bank", "ECB_SSM", "NLD", "EURONEXT", "NL0011821202", "INGA", 2024, True),
        (FI_RABO, "Coöperatieve Rabobank U.A.", "Rabobank", "DG3RU1DBUFHT4ZF9WN62", "RABONL2U",
         "cooperative_bank", "ECB_SSM", "NLD", None, None, None, 2024, True),
    ]
    for row in fi_rows:
        cur.execute("""INSERT INTO fi_entities
            (id,legal_name,trading_name,lei,swift_bic,institution_type,supervision_type,
             headquarters_country,listing_exchange,isin,stock_ticker,csrd_first_mandatory_year,is_active)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (id) DO NOTHING""", row)
    print(f"  {len(fi_rows)} fi_entities inserted")

    # ── 2. energy_entities ───────────────────────────────────────────────────
    print("Inserting energy_entities…")
    en_rows = [
        (EN_EDP,   "EDP – Energias de Portugal S.A.", "EDP", "EDPEPTENERGY00000001",
         "vertically_integrated", "PRT", "EURONEXT", "PTEDP0AM0009", "BBB+", "Baa1", "BBB+", 12, "EU-ETS-PT-001", 2024, True),
        (EN_ENGIE, "ENGIE S.A.", "ENGIE", "V9XEVL1ENGIE00000001",
         "vertically_integrated", "FRA", "EURONEXT", "FR0010208488", "BBB+", "Baa1", "BBB+", 683, "EU-ETS-FR-002", 2024, True),
        (EN_ORSTED,"Ørsted A/S", "Ørsted", "ORSTEDDK000000000001",
         "pure_renewables", "DNK", "NASDAQ_CPH", "DK0060094928", "BBB+", "Baa1", "BBB+", 8, "EU-ETS-DK-003", 2024, True),
        (EN_RWE,   "RWE Aktiengesellschaft", "RWE", "RWEDEENERGY000000001",
         "vertically_integrated", "DEU", "XETRA", "DE0007037129", "BBB+", "Baa2", "BBB+", 94, "EU-ETS-DE-004", 2024, True),
    ]
    for row in en_rows:
        cur.execute("""INSERT INTO energy_entities
            (id,legal_name,trading_name,lei,entity_type,headquarters_country,
             listing_exchange,isin,credit_rating_sp,credit_rating_moodys,credit_rating_fitch,
             eu_ets_installation_count,eu_ets_id,csrd_first_mandatory_year,is_active)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (id) DO NOTHING""", row)
    print(f"  {len(en_rows)} energy_entities inserted")

    # ── 3. fi_financials (2024) ───────────────────────────────────────────────
    print("Inserting fi_financials…")
    fi_fin = [
        # ABN AMRO 2024 — public figures (EUR bn converted to EUR mn)
        dict(id=str(uuid.uuid4()), entity_id=FI_ABN, year=2024, currency="EUR",
             nii=6280, noni=1820, fee=1210, trading=380, tot_op_inc=8100, tot_op_exp=5100,
             cir=63.0, staff=3100, impair=420, pbt=2580, tax=640, net_profit=1940,
             attr_sh=1860, eps=2.12, roe=11.8, rote=13.2, roa=0.5,
             tot_assets=411000, loans_gr=253000, loans_net=249000, llp=4200,
             inv_sec=68000, trad_assets=12000, dep=248000, eq=20100, tang_eq=18400,
             debt=28000, aum=None, cet1=14.0, t1=15.1, tc=17.3, cet1_fl=13.9,
             lev=4.7, rwa=121000, lcr=168, nsfr=136, mrel=30.2,
             npl=2.1, npl_cov=65, cor=17, s1=73, s2=20, s3=7,
             mktcap=15200, pb=0.82, dps=0.87, dpayout=41),
        # BNP Paribas 2024
        dict(id=str(uuid.uuid4()), entity_id=FI_BNP, year=2024, currency="EUR",
             nii=23800, noni=21200, fee=14200, trading=7100, tot_op_inc=45000, tot_op_exp=30100,
             cir=66.9, staff=17200, impair=3800, pbt=11100, tax=3200, net_profit=7900,
             attr_sh=7600, eps=6.21, roe=10.4, rote=13.8, roa=0.3,
             tot_assets=2695000, loans_gr=856000, loans_net=840000, llp=18200,
             inv_sec=520000, trad_assets=310000, dep=980000, eq=128000, tang_eq=101000,
             debt=220000, aum=1200000, cet1=13.7, t1=15.0, tc=17.1, cet1_fl=13.5,
             lev=4.6, rwa=694000, lcr=148, nsfr=116, mrel=31.8,
             npl=2.4, npl_cov=68, cor=44, s1=70, s2=22, s3=8,
             mktcap=68400, pb=0.59, dps=3.90, dpayout=50),
        # ING Group 2024
        dict(id=str(uuid.uuid4()), entity_id=FI_ING, year=2024, currency="EUR",
             nii=15300, noni=4900, fee=3200, trading=1300, tot_op_inc=20200, tot_op_exp=12400,
             cir=61.4, staff=7600, impair=1100, pbt=6700, tax=1600, net_profit=5100,
             attr_sh=4900, eps=1.44, roe=13.2, rote=14.1, roa=0.52,
             tot_assets=1004000, loans_gr=637000, loans_net=628000, llp=9200,
             inv_sec=168000, trad_assets=42000, dep=680000, eq=58000, tang_eq=52000,
             debt=95000, aum=None, cet1=14.5, t1=15.7, tc=18.0, cet1_fl=14.3,
             lev=4.8, rwa=332000, lcr=158, nsfr=128, mrel=28.4,
             npl=1.8, npl_cov=71, cor=17, s1=72, s2=21, s3=7,
             mktcap=53100, pb=0.92, dps=0.756, dpayout=52),
        # Rabobank 2024
        dict(id=str(uuid.uuid4()), entity_id=FI_RABO, year=2024, currency="EUR",
             nii=9800, noni=2200, fee=1600, trading=400, tot_op_inc=12000, tot_op_exp=7800,
             cir=65.0, staff=4500, impair=580, pbt=3620, tax=900, net_profit=2720,
             attr_sh=2720, eps=None, roe=9.8, rote=10.2, roa=0.42,
             tot_assets=650000, loans_gr=395000, loans_net=390000, llp=5800,
             inv_sec=98000, trad_assets=None, dep=405000, eq=47000, tang_eq=43000,
             debt=72000, aum=None, cet1=17.2, t1=18.4, tc=22.1, cet1_fl=17.0,
             lev=5.5, rwa=196000, lcr=176, nsfr=142, mrel=None,
             npl=2.8, npl_cov=61, cor=15, s1=74, s2=19, s3=7,
             mktcap=None, pb=None, dps=None, dpayout=None),
    ]
    for f in fi_fin:
        cur.execute("""INSERT INTO fi_financials
            (id,entity_id,reporting_year,currency,net_interest_income,non_interest_income,
             net_fee_commission_income,trading_income,total_operating_income,total_operating_expenses,
             cost_income_ratio,staff_costs,impairment_charges,profit_before_tax,income_tax,net_profit,
             attributable_to_shareholders,eps_diluted,roe,rote,roa,total_assets,loans_and_advances_gross,
             loans_and_advances_net,loan_loss_provisions,investment_securities,trading_assets,
             total_customer_deposits,total_equity,tangible_equity,total_debt,aum,
             cet1_ratio_pct,tier1_ratio_pct,total_capital_ratio_pct,cet1_fully_loaded_pct,
             leverage_ratio_pct,rwa,lcr_pct,nsfr_pct,mrel_ratio_pct,
             npl_ratio_pct,npl_coverage_ratio_pct,cost_of_risk_bps,
             stage1_loans_pct,stage2_loans_pct,stage3_loans_pct,
             market_cap,price_to_book,dividend_per_share,dividend_payout_ratio_pct)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT DO NOTHING""",
            (f["id"],f["entity_id"],f["year"],f["currency"],
             f["nii"],f["noni"],f["fee"],f["trading"],f["tot_op_inc"],f["tot_op_exp"],
             f["cir"],f["staff"],f["impair"],f["pbt"],f["tax"],f["net_profit"],
             f["attr_sh"],f["eps"],f["roe"],f["rote"],f["roa"],f["tot_assets"],f["loans_gr"],
             f["loans_net"],f["llp"],f["inv_sec"],f["trad_assets"],f["dep"],f["eq"],f["tang_eq"],
             f["debt"],f["aum"],f["cet1"],f["t1"],f["tc"],f["cet1_fl"],f["lev"],f["rwa"],
             f["lcr"],f["nsfr"],f["mrel"],f["npl"],f["npl_cov"],f["cor"],
             f["s1"],f["s2"],f["s3"],f["mktcap"],f["pb"],f["dps"],f["dpayout"]))
    print(f"  {len(fi_fin)} fi_financials inserted")

    # ── 4. fi_financed_emissions (2024) ───────────────────────────────────────
    print("Inserting fi_financed_emissions…")
    fe_rows = [
        # ABN AMRO — 2024 PCAF report aligned
        dict(id=str(uuid.uuid4()), eid=FI_ABN, year=2024,
             pcaf_ver="PCAF Standard v1.1",
             own_s1=6200, own_s2_mkt=2100, own_s2_loc=2800, own_s3=18400, own_total=26700,
             own_energy_mwh=312000, own_ren_pct=68.0, own_offices_m2=521000,
             own_ei_kwh=598, own_ci_kg=12.1,
             own_travel_km=142000000, own_fleet=1820, own_ev_pct=22.0,
             fin_s1=7820000, fin_s2=2340000, fin_s3=12800000, tot_fin=22960000,
             waci=62.4, cf=48.2, cov_pct=74.0, dq=2.8, temp=1.92,
             aln15=18.0, aln2=28.0, misaln=31.0, notrg=23.0,
             nzy=2050, inty=2030, int_red=40.0, base=2019, base_em=28400000),
        # BNP Paribas — 2024 PCAF + NZBA aligned
        dict(id=str(uuid.uuid4()), eid=FI_BNP, year=2024,
             pcaf_ver="PCAF Standard v1.1",
             own_s1=18400, own_s2_mkt=4200, own_s2_loc=5600, own_s3=42000, own_total=64600,
             own_energy_mwh=810000, own_ren_pct=72.0, own_offices_m2=1820000,
             own_ei_kwh=445, own_ci_kg=10.3,
             own_travel_km=380000000, own_fleet=4200, own_ev_pct=31.0,
             fin_s1=182000000, fin_s2=48000000, fin_s3=241000000, tot_fin=471000000,
             waci=71.1, cf=56.8, cov_pct=68.0, dq=2.6, temp=1.86,
             aln15=14.0, aln2=22.0, misaln=38.0, notrg=26.0,
             nzy=2050, inty=2030, int_red=30.0, base=2019, base_em=610000000),
        # ING Group
        dict(id=str(uuid.uuid4()), eid=FI_ING, year=2024,
             pcaf_ver="PCAF Standard v1.1",
             own_s1=9100, own_s2_mkt=2800, own_s2_loc=3600, own_s3=26000, own_total=37900,
             own_energy_mwh=420000, own_ren_pct=100.0, own_offices_m2=740000,
             own_ei_kwh=568, own_ci_kg=0.0,
             own_travel_km=210000000, own_fleet=2100, own_ev_pct=38.0,
             fin_s1=58000000, fin_s2=14000000, fin_s3=78000000, tot_fin=150000000,
             waci=55.2, cf=43.0, cov_pct=71.0, dq=2.7, temp=1.79,
             aln15=19.0, aln2=26.0, misaln=30.0, notrg=25.0,
             nzy=2050, inty=2030, int_red=50.0, base=2019, base_em=196000000),
        # Rabobank
        dict(id=str(uuid.uuid4()), eid=FI_RABO, year=2024,
             pcaf_ver="PCAF Standard v1.1",
             own_s1=4800, own_s2_mkt=1200, own_s2_loc=1800, own_s3=14000, own_total=20000,
             own_energy_mwh=198000, own_ren_pct=100.0, own_offices_m2=380000,
             own_ei_kwh=521, own_ci_kg=0.0,
             own_travel_km=88000000, own_fleet=1200, own_ev_pct=45.0,
             fin_s1=24000000, fin_s2=6200000, fin_s3=32000000, tot_fin=62200000,
             waci=49.8, cf=38.1, cov_pct=69.0, dq=2.9, temp=1.74,
             aln15=21.0, aln2=30.0, misaln=28.0, notrg=21.0,
             nzy=2050, inty=2030, int_red=45.0, base=2019, base_em=81000000),
    ]
    for f in fe_rows:
        cur.execute("""INSERT INTO fi_financed_emissions
            (id,entity_id,reporting_year,pcaf_methodology_version,
             own_scope1_tco2e,own_scope2_market_tco2e,own_scope2_location_tco2e,own_scope3_total_tco2e,own_total_tco2e,
             own_energy_consumption_mwh,own_renewable_energy_pct,own_offices_m2,
             own_energy_intensity_kwh_m2,own_carbon_intensity_kgco2_m2,
             own_business_travel_km,own_fleet_vehicles,own_electric_vehicles_pct,
             financed_scope1_tco2e,financed_scope2_tco2e,financed_scope3_tco2e,total_financed_tco2e,
             waci_tco2e_per_mrevenue,carbon_footprint_tco2e_per_meur_invested,
             portfolio_coverage_pct,weighted_avg_dq,portfolio_temperature_c,
             aligned_1_5c_pct,aligned_2c_pct,misaligned_pct,no_target_pct,
             net_zero_target_year,intermediate_target_year,intermediate_reduction_vs_base_pct,
             base_year,base_year_financed_emissions_tco2e)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT DO NOTHING""",
            (f["id"],f["eid"],f["year"],f["pcaf_ver"],
             f["own_s1"],f["own_s2_mkt"],f["own_s2_loc"],f["own_s3"],f["own_total"],
             f["own_energy_mwh"],f["own_ren_pct"],f["own_offices_m2"],
             f["own_ei_kwh"],f["own_ci_kg"],
             f["own_travel_km"],f["own_fleet"],f["own_ev_pct"],
             f["fin_s1"],f["fin_s2"],f["fin_s3"],f["tot_fin"],
             f["waci"],f["cf"],f["cov_pct"],f["dq"],f["temp"],
             f["aln15"],f["aln2"],f["misaln"],f["notrg"],
             f["nzy"],f["inty"],f["int_red"],f["base"],f["base_em"]))
    print(f"  {len(fe_rows)} fi_financed_emissions inserted")

    conn.commit()
    print("Part 1 committed (fi_entities, fi_financials, fi_financed_emissions)")
    return conn, cur

conn, cur = run()
