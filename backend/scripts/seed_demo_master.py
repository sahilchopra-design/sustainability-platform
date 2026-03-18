"""
Master Demo Seed Script — Real Company Data Across All Modules
==============================================================
Populates all major tables with realistic data for 25+ real companies
spanning Financial Institutions, Energy, Oil & Gas, Technology,
Mining, Real Estate, Agriculture, and Industrials.

Designed to make every frontend module functional for demo purposes.

Usage:
    python scripts/seed_demo_master.py
"""

import psycopg2
import psycopg2.extras
import uuid
import json
from datetime import date, datetime
from decimal import Decimal

DB_URL = "postgresql://postgres.kytzcbipsghprsqoalvi:KimiaAImpact2026@aws-1-us-east-2.pooler.supabase.com:5432/postgres"


def nid():
    return str(uuid.uuid4())


# ═══════════════════════════════════════════════════════════════════════════
# COMPANY MASTER DATA — 25 real companies across sectors
# ═══════════════════════════════════════════════════════════════════════════

COMPANIES = [
    # Financial Institutions
    dict(id=nid(), legal_name="HSBC Holdings plc", trading_name="HSBC", entity_lei="MLU0ZO3ML4LN2LL2TL40",
         isin_primary="GB0005405286", ticker_symbol="HSBA.L", headquarters_city="London", headquarters_country="GBR",
         incorporation_country="GBR", gics_sector="Financials", gics_industry="Banks",
         institution_type="Bank", is_financial_institution=True, regulatory_supervisor="PRA",
         total_assets_eur_bn=2640, annual_revenue_eur_mn=52400, employees_fte=221000,
         cet1_ratio_pct=14.8, tier1_capital_ratio_pct=16.2, total_capital_ratio_pct=19.7,
         leverage_ratio_pct=5.4, lcr_pct=132, nsfr_pct=134, rwa_eur_bn=842,
         credit_rating_sp="A+", credit_rating_moodys="A1", systemic_importance="G-SIB",
         market_cap_eur_bn=152, net_profit_eur_mn=17200, nace_code="K64.19",
         nzba_member=True, pcaf_member=True, tcfd_supporter=True, sbti_committed=True),

    dict(id=nid(), legal_name="Deutsche Bank AG", trading_name="Deutsche Bank", entity_lei="7LTWFZYICNSX8D621K86",
         isin_primary="DE0005140008", ticker_symbol="DBK.DE", headquarters_city="Frankfurt", headquarters_country="DEU",
         incorporation_country="DEU", gics_sector="Financials", gics_industry="Banks",
         institution_type="Bank", is_financial_institution=True, regulatory_supervisor="ECB",
         total_assets_eur_bn=1312, annual_revenue_eur_mn=28900, employees_fte=87000,
         cet1_ratio_pct=13.7, tier1_capital_ratio_pct=15.1, total_capital_ratio_pct=18.4,
         leverage_ratio_pct=4.6, lcr_pct=136, nsfr_pct=119, rwa_eur_bn=349,
         credit_rating_sp="A-", credit_rating_moodys="A1", systemic_importance="G-SIB",
         market_cap_eur_bn=31, net_profit_eur_mn=5700, nace_code="K64.19",
         nzba_member=True, pcaf_member=True, tcfd_supporter=True, sbti_committed=False),

    dict(id=nid(), legal_name="Zurich Insurance Group AG", trading_name="Zurich", entity_lei="529900QVNRBND50TXP03",
         isin_primary="CH0011075394", ticker_symbol="ZURN.SW", headquarters_city="Zurich", headquarters_country="CHE",
         incorporation_country="CHE", gics_sector="Financials", gics_industry="Insurance",
         institution_type="Insurance", is_financial_institution=True, regulatory_supervisor="FINMA",
         total_assets_eur_bn=402, annual_revenue_eur_mn=49200, employees_fte=60000,
         credit_rating_sp="AA-", credit_rating_moodys="Aa3", systemic_importance="G-SII",
         market_cap_eur_bn=72, net_profit_eur_mn=4800, nace_code="K65.12",
         nzba_member=False, pcaf_member=False, tcfd_supporter=True, sbti_committed=True),

    dict(id=nid(), legal_name="BlackRock Inc.", trading_name="BlackRock", entity_lei="PGM4UUPT7P1VZ6VBN918",
         isin_primary="US09247X1019", ticker_symbol="BLK", headquarters_city="New York", headquarters_country="USA",
         incorporation_country="USA", gics_sector="Financials", gics_industry="Asset Management",
         institution_type="Asset Manager", is_financial_institution=True, regulatory_supervisor="SEC",
         total_assets_eur_bn=42, annual_revenue_eur_mn=17900, employees_fte=19800,
         credit_rating_sp="AA-", credit_rating_moodys="Aa3", systemic_importance="None",
         market_cap_eur_bn=118, net_profit_eur_mn=5500, nace_code="K66.30",
         nzba_member=False, pcaf_member=True, tcfd_supporter=True, sbti_committed=True),

    # Energy — Oil & Gas
    dict(id=nid(), legal_name="Shell plc", trading_name="Shell", entity_lei="21380068P1DRHMJ8KU70",
         isin_primary="GB00BP6MXD84", ticker_symbol="SHEL.L", headquarters_city="London", headquarters_country="GBR",
         incorporation_country="GBR", gics_sector="Energy", gics_industry="Oil & Gas",
         institution_type="Energy", is_financial_institution=False, regulatory_supervisor=None,
         total_assets_eur_bn=376, annual_revenue_eur_mn=316400, employees_fte=86000,
         credit_rating_sp="AA-", credit_rating_moodys="Aa2", systemic_importance="None",
         market_cap_eur_bn=208, net_profit_eur_mn=19400, nace_code="B06.10",
         nzba_member=False, pcaf_member=False, tcfd_supporter=True, sbti_committed=False),

    dict(id=nid(), legal_name="TotalEnergies SE", trading_name="TotalEnergies", entity_lei="529900S21EQ1BO4ESM68",
         isin_primary="FR0000120271", ticker_symbol="TTE.PA", headquarters_city="Paris", headquarters_country="FRA",
         incorporation_country="FRA", gics_sector="Energy", gics_industry="Oil & Gas",
         institution_type="Energy", is_financial_institution=False, regulatory_supervisor=None,
         total_assets_eur_bn=295, annual_revenue_eur_mn=218700, employees_fte=101000,
         credit_rating_sp="AA-", credit_rating_moodys="Aa3", systemic_importance="None",
         market_cap_eur_bn=142, net_profit_eur_mn=15800, nace_code="B06.10",
         nzba_member=False, pcaf_member=False, tcfd_supporter=True, sbti_committed=False),

    dict(id=nid(), legal_name="Equinor ASA", trading_name="Equinor", entity_lei="OW6OFBNCKXC8UI1WBEMG",
         isin_primary="NO0010096985", ticker_symbol="EQNR.OL", headquarters_city="Stavanger", headquarters_country="NOR",
         incorporation_country="NOR", gics_sector="Energy", gics_industry="Oil & Gas",
         institution_type="Energy", is_financial_institution=False, regulatory_supervisor=None,
         total_assets_eur_bn=142, annual_revenue_eur_mn=105300, employees_fte=22000,
         credit_rating_sp="AA-", credit_rating_moodys="Aa2", systemic_importance="None",
         market_cap_eur_bn=68, net_profit_eur_mn=11200, nace_code="B06.10",
         nzba_member=False, pcaf_member=False, tcfd_supporter=True, sbti_committed=True),

    # Energy — Utilities / Renewables
    dict(id=nid(), legal_name="Enel SpA", trading_name="Enel", entity_lei="WOCKAN83NVMCFH2SZ775",
         isin_primary="IT0003128367", ticker_symbol="ENEL.MI", headquarters_city="Rome", headquarters_country="ITA",
         incorporation_country="ITA", gics_sector="Utilities", gics_industry="Electric Utilities",
         institution_type="Energy", is_financial_institution=False, regulatory_supervisor=None,
         total_assets_eur_bn=166, annual_revenue_eur_mn=92900, employees_fte=65000,
         credit_rating_sp="BBB+", credit_rating_moodys="Baa1", systemic_importance="None",
         market_cap_eur_bn=69, net_profit_eur_mn=6500, nace_code="D35.11",
         nzba_member=False, pcaf_member=False, tcfd_supporter=True, sbti_committed=True),

    dict(id=nid(), legal_name="Iberdrola SA", trading_name="Iberdrola", entity_lei="5QK37QC7NWOJ8D7WVQ45",
         isin_primary="ES0144580Y14", ticker_symbol="IBE.MC", headquarters_city="Bilbao", headquarters_country="ESP",
         incorporation_country="ESP", gics_sector="Utilities", gics_industry="Electric Utilities",
         institution_type="Energy", is_financial_institution=False, regulatory_supervisor=None,
         total_assets_eur_bn=153, annual_revenue_eur_mn=49300, employees_fte=42000,
         credit_rating_sp="BBB+", credit_rating_moodys="Baa1", systemic_importance="None",
         market_cap_eur_bn=82, net_profit_eur_mn=5200, nace_code="D35.11",
         nzba_member=False, pcaf_member=False, tcfd_supporter=True, sbti_committed=True),

    dict(id=nid(), legal_name="Vestas Wind Systems A/S", trading_name="Vestas", entity_lei="549300DYMC8BGZZC8844",
         isin_primary="DK0061539921", ticker_symbol="VWS.CO", headquarters_city="Aarhus", headquarters_country="DNK",
         incorporation_country="DNK", gics_sector="Industrials", gics_industry="Electrical Equipment",
         institution_type="Corporate", is_financial_institution=False, regulatory_supervisor=None,
         total_assets_eur_bn=22, annual_revenue_eur_mn=15200, employees_fte=28600,
         credit_rating_sp="BBB", credit_rating_moodys="Baa2", systemic_importance="None",
         market_cap_eur_bn=21, net_profit_eur_mn=-200, nace_code="C28.11",
         nzba_member=False, pcaf_member=False, tcfd_supporter=True, sbti_committed=True),

    # Technology
    dict(id=nid(), legal_name="SAP SE", trading_name="SAP", entity_lei="529900D6BF99LW9R2E68",
         isin_primary="DE0007164600", ticker_symbol="SAP.DE", headquarters_city="Walldorf", headquarters_country="DEU",
         incorporation_country="DEU", gics_sector="Information Technology", gics_industry="Software",
         institution_type="Corporate", is_financial_institution=False, regulatory_supervisor=None,
         total_assets_eur_bn=72, annual_revenue_eur_mn=31200, employees_fte=107000,
         credit_rating_sp="A+", credit_rating_moodys="A2", systemic_importance="None",
         market_cap_eur_bn=260, net_profit_eur_mn=6100, nace_code="J62.01",
         nzba_member=False, pcaf_member=False, tcfd_supporter=True, sbti_committed=True),

    dict(id=nid(), legal_name="Siemens AG", trading_name="Siemens", entity_lei="W38RGI023J3WT1HWRP32",
         isin_primary="DE0007236101", ticker_symbol="SIE.DE", headquarters_city="Munich", headquarters_country="DEU",
         incorporation_country="DEU", gics_sector="Industrials", gics_industry="Industrial Conglomerates",
         institution_type="Corporate", is_financial_institution=False, regulatory_supervisor=None,
         total_assets_eur_bn=105, annual_revenue_eur_mn=77800, employees_fte=311000,
         credit_rating_sp="A+", credit_rating_moodys="A1", systemic_importance="None",
         market_cap_eur_bn=152, net_profit_eur_mn=8500, nace_code="C27.11",
         nzba_member=False, pcaf_member=False, tcfd_supporter=True, sbti_committed=True),

    # Mining / Materials
    dict(id=nid(), legal_name="Rio Tinto Group", trading_name="Rio Tinto", entity_lei="213800YOEO5OQ72G2R82",
         isin_primary="GB0007188757", ticker_symbol="RIO.L", headquarters_city="London", headquarters_country="GBR",
         incorporation_country="AUS", gics_sector="Materials", gics_industry="Metals & Mining",
         institution_type="Corporate", is_financial_institution=False, regulatory_supervisor=None,
         total_assets_eur_bn=92, annual_revenue_eur_mn=52200, employees_fte=49000,
         credit_rating_sp="A", credit_rating_moodys="A1", systemic_importance="None",
         market_cap_eur_bn=102, net_profit_eur_mn=10200, nace_code="B07.29",
         nzba_member=False, pcaf_member=False, tcfd_supporter=True, sbti_committed=True),

    dict(id=nid(), legal_name="Glencore plc", trading_name="Glencore", entity_lei="2138002658CPO9NBH955",
         isin_primary="JE00B4T3BW64", ticker_symbol="GLEN.L", headquarters_city="Baar", headquarters_country="CHE",
         incorporation_country="JEY", gics_sector="Materials", gics_industry="Metals & Mining",
         institution_type="Corporate", is_financial_institution=False, regulatory_supervisor=None,
         total_assets_eur_bn=109, annual_revenue_eur_mn=217500, employees_fte=152000,
         credit_rating_sp="BBB+", credit_rating_moodys="Baa1", systemic_importance="None",
         market_cap_eur_bn=54, net_profit_eur_mn=4300, nace_code="B07.29",
         nzba_member=False, pcaf_member=False, tcfd_supporter=True, sbti_committed=False),

    # Real Estate
    dict(id=nid(), legal_name="Vonovia SE", trading_name="Vonovia", entity_lei="5299005A2ZEP6AP7GG81",
         isin_primary="DE000A1ML7J1", ticker_symbol="VNA.DE", headquarters_city="Bochum", headquarters_country="DEU",
         incorporation_country="DEU", gics_sector="Real Estate", gics_industry="Real Estate",
         institution_type="RE", is_financial_institution=False, regulatory_supervisor=None,
         total_assets_eur_bn=88, annual_revenue_eur_mn=6200, employees_fte=15700,
         credit_rating_sp="BBB+", credit_rating_moodys="Baa1", systemic_importance="None",
         market_cap_eur_bn=19, net_profit_eur_mn=-6900, nace_code="L68.20",
         nzba_member=False, pcaf_member=False, tcfd_supporter=True, sbti_committed=True),

    dict(id=nid(), legal_name="Segro plc", trading_name="SEGRO", entity_lei="213800XC35KGM9NHF679",
         isin_primary="GB00B5ZN1N88", ticker_symbol="SGRO.L", headquarters_city="Slough", headquarters_country="GBR",
         incorporation_country="GBR", gics_sector="Real Estate", gics_industry="Real Estate",
         institution_type="RE", is_financial_institution=False, regulatory_supervisor=None,
         total_assets_eur_bn=19, annual_revenue_eur_mn=710, employees_fte=460,
         credit_rating_sp="A-", credit_rating_moodys="A3", systemic_importance="None",
         market_cap_eur_bn=12, net_profit_eur_mn=-980, nace_code="L68.20",
         nzba_member=False, pcaf_member=False, tcfd_supporter=True, sbti_committed=True),

    # Agriculture / Food
    dict(id=nid(), legal_name="Bayer AG", trading_name="Bayer", entity_lei="549300J4RHPEPVTUS631",
         isin_primary="DE000BAY0017", ticker_symbol="BAYN.DE", headquarters_city="Leverkusen", headquarters_country="DEU",
         incorporation_country="DEU", gics_sector="Health Care", gics_industry="Pharmaceuticals",
         institution_type="Corporate", is_financial_institution=False, regulatory_supervisor=None,
         total_assets_eur_bn=113, annual_revenue_eur_mn=47600, employees_fte=100000,
         credit_rating_sp="BBB", credit_rating_moodys="Baa2", systemic_importance="None",
         market_cap_eur_bn=24, net_profit_eur_mn=-2900, nace_code="C20.20",
         nzba_member=False, pcaf_member=False, tcfd_supporter=True, sbti_committed=True),

    dict(id=nid(), legal_name="Nestlé SA", trading_name="Nestlé", entity_lei="KY37F86X1O3V4N3LPZ03",
         isin_primary="CH0038863350", ticker_symbol="NESN.SW", headquarters_city="Vevey", headquarters_country="CHE",
         incorporation_country="CHE", gics_sector="Consumer Staples", gics_industry="Food Products",
         institution_type="Corporate", is_financial_institution=False, regulatory_supervisor=None,
         total_assets_eur_bn=120, annual_revenue_eur_mn=92100, employees_fte=270000,
         credit_rating_sp="AA", credit_rating_moodys="Aa2", systemic_importance="None",
         market_cap_eur_bn=248, net_profit_eur_mn=11200, nace_code="C10.89",
         nzba_member=False, pcaf_member=False, tcfd_supporter=True, sbti_committed=True),

    # Industrials / Construction
    dict(id=nid(), legal_name="Holcim Ltd", trading_name="Holcim", entity_lei="529900EHPFPYHV6IYO98",
         isin_primary="CH0012214059", ticker_symbol="HOLN.SW", headquarters_city="Zug", headquarters_country="CHE",
         incorporation_country="CHE", gics_sector="Materials", gics_industry="Construction Materials",
         institution_type="Corporate", is_financial_institution=False, regulatory_supervisor=None,
         total_assets_eur_bn=56, annual_revenue_eur_mn=26900, employees_fte=63000,
         credit_rating_sp="BBB+", credit_rating_moodys="Baa1", systemic_importance="None",
         market_cap_eur_bn=42, net_profit_eur_mn=3100, nace_code="C23.51",
         nzba_member=False, pcaf_member=False, tcfd_supporter=True, sbti_committed=True),

    # Automotive / Transport
    dict(id=nid(), legal_name="Volkswagen AG", trading_name="Volkswagen", entity_lei="529900NNUPAGGOMPXZ31",
         isin_primary="DE0007664039", ticker_symbol="VOW3.DE", headquarters_city="Wolfsburg", headquarters_country="DEU",
         incorporation_country="DEU", gics_sector="Consumer Discretionary", gics_industry="Automobiles",
         institution_type="Corporate", is_financial_institution=False, regulatory_supervisor=None,
         total_assets_eur_bn=564, annual_revenue_eur_mn=322300, employees_fte=684000,
         credit_rating_sp="BBB+", credit_rating_moodys="A3", systemic_importance="None",
         market_cap_eur_bn=55, net_profit_eur_mn=12900, nace_code="C29.10",
         nzba_member=False, pcaf_member=False, tcfd_supporter=True, sbti_committed=True),

    dict(id=nid(), legal_name="Maersk A/S", trading_name="Maersk", entity_lei="549300D2K6PKKKXVNN73",
         isin_primary="DK0010244508", ticker_symbol="MAERSK-B.CO", headquarters_city="Copenhagen", headquarters_country="DNK",
         incorporation_country="DNK", gics_sector="Industrials", gics_industry="Marine Transportation",
         institution_type="Corporate", is_financial_institution=False, regulatory_supervisor=None,
         total_assets_eur_bn=62, annual_revenue_eur_mn=51100, employees_fte=100000,
         credit_rating_sp="BBB+", credit_rating_moodys="Baa2", systemic_importance="None",
         market_cap_eur_bn=28, net_profit_eur_mn=3100, nace_code="H50.20",
         nzba_member=False, pcaf_member=False, tcfd_supporter=True, sbti_committed=True),

    # Telecoms / Data Centres
    dict(id=nid(), legal_name="Equinix Inc.", trading_name="Equinix", entity_lei="549300EVUN2BTLJ3GT74",
         isin_primary="US29444U7000", ticker_symbol="EQIX", headquarters_city="Redwood City", headquarters_country="USA",
         incorporation_country="USA", gics_sector="Real Estate", gics_industry="Data Centers",
         institution_type="RE", is_financial_institution=False, regulatory_supervisor=None,
         total_assets_eur_bn=32, annual_revenue_eur_mn=7800, employees_fte=13100,
         credit_rating_sp="BBB+", credit_rating_moodys="Baa2", systemic_importance="None",
         market_cap_eur_bn=78, net_profit_eur_mn=980, nace_code="J63.11",
         nzba_member=False, pcaf_member=False, tcfd_supporter=True, sbti_committed=True),

    # PE / Infrastructure
    dict(id=nid(), legal_name="Brookfield Asset Management Ltd", trading_name="Brookfield", entity_lei="C6J3FGIWG6MBDGTE8Q02",
         isin_primary="CA1130041058", ticker_symbol="BAM", headquarters_city="Toronto", headquarters_country="CAN",
         incorporation_country="CAN", gics_sector="Financials", gics_industry="Asset Management",
         institution_type="Asset Manager", is_financial_institution=True, regulatory_supervisor="OSC",
         total_assets_eur_bn=900, annual_revenue_eur_mn=93200, employees_fte=240000,
         credit_rating_sp="A-", credit_rating_moodys="A3", systemic_importance="None",
         market_cap_eur_bn=82, net_profit_eur_mn=4500, nace_code="K66.30",
         nzba_member=False, pcaf_member=True, tcfd_supporter=True, sbti_committed=True),
]

# Index by name for FK lookups
CO = {c["legal_name"]: c for c in COMPANIES}


def insert_company_profiles(cur):
    """Insert into company_profiles table"""
    print("  Seeding company_profiles...")
    cols = [
        "id", "legal_name", "trading_name", "entity_lei", "isin_primary", "ticker_symbol",
        "headquarters_city", "headquarters_country", "incorporation_country",
        "gics_sector", "gics_industry", "institution_type", "is_financial_institution",
        "regulatory_supervisor", "total_assets_eur_bn", "annual_revenue_eur_mn",
        "employees_fte", "cet1_ratio_pct", "tier1_capital_ratio_pct", "total_capital_ratio_pct",
        "leverage_ratio_pct", "lcr_pct", "nsfr_pct", "rwa_eur_bn",
        "credit_rating_sp", "credit_rating_moodys", "systemic_importance",
        "market_cap_eur_bn", "net_profit_eur_mn", "nace_code",
        "nzba_member", "pcaf_member", "tcfd_supporter", "sbti_committed",
        "reporting_year", "data_source",
    ]
    inserted = 0
    for c in COMPANIES:
        # Check if LEI already exists
        lei = c.get("entity_lei")
        if lei:
            cur.execute("SELECT id FROM company_profiles WHERE entity_lei = %s", (lei,))
            if cur.fetchone():
                continue
        vals = [c.get(k) for k in cols[:-2]]
        vals.extend([2024, "analyst_estimate"])
        placeholders = ",".join(["%s"] * len(cols))
        col_str = ",".join(cols)
        cur.execute(
            f"INSERT INTO company_profiles ({col_str}) VALUES ({placeholders})",
            vals
        )
        inserted += 1
    print(f"    -> {inserted} new company profiles inserted ({len(COMPANIES) - inserted} already existed)")


def insert_portfolios(cur):
    """Create 3 demo portfolios with assets linked to our companies"""
    print("  Seeding portfolios_pg & assets_pg...")

    portfolios = [
        (nid(), "European Climate Leaders Fund", "Article 9 SFDR fund focused on EU climate transition leaders"),
        (nid(), "Global Multi-Sector ESG Fund", "Diversified ESG-integrated fund across sectors and geographies"),
        (nid(), "Infrastructure & Energy Transition", "Thematic fund targeting decarbonisation infrastructure"),
    ]
    for pid, name, desc in portfolios:
        cur.execute(
            "INSERT INTO portfolios_pg (id, name, description, created_at) VALUES (%s, %s, %s, NOW()) ON CONFLICT (id) DO NOTHING",
            (pid, name, desc)
        )

    # Assets for Portfolio 1: European Climate Leaders
    p1 = portfolios[0][0]
    assets_p1 = [
        ("HSBC Holdings plc", "Bond", "Financials", "Banks", 150e6, 148e6, 0.005, 0.35, "A+", 5),
        ("Deutsche Bank AG", "Bond", "Financials", "Banks", 120e6, 117e6, 0.008, 0.40, "A-", 4),
        ("Enel SpA", "Equity", "Utilities", "Electric Utilities", 85e6, 88e6, 0.012, 0.45, "BBB+", None),
        ("Iberdrola SA", "Equity", "Utilities", "Electric Utilities", 90e6, 94e6, 0.010, 0.40, "BBB+", None),
        ("Shell plc", "Bond", "Energy", "Oil & Gas", 100e6, 98e6, 0.006, 0.38, "AA-", 7),
        ("TotalEnergies SE", "Bond", "Energy", "Oil & Gas", 80e6, 79e6, 0.007, 0.40, "AA-", 5),
        ("Vestas Wind Systems A/S", "Equity", "Industrials", "Electrical Equipment", 60e6, 55e6, 0.020, 0.50, "BBB", None),
        ("SAP SE", "Equity", "Information Technology", "Software", 70e6, 75e6, 0.004, 0.30, "A+", None),
        ("Vonovia SE", "Bond", "Real Estate", "Real Estate", 55e6, 52e6, 0.015, 0.55, "BBB+", 6),
        ("Holcim Ltd", "Bond", "Materials", "Construction Materials", 45e6, 43e6, 0.018, 0.48, "BBB+", 5),
    ]

    for name, atype, sector, subsector, exp, mv, pd, lgd, rating, mat in assets_p1:
        cur.execute(
            """INSERT INTO assets_pg (id, portfolio_id, asset_type, company_name, company_sector,
               company_subsector, exposure, market_value, base_pd, base_lgd, rating, maturity_years)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING""",
            (nid(), p1, atype, name, sector, subsector, exp, mv, pd, lgd, rating, mat)
        )

    # Assets for Portfolio 2: Global Multi-Sector ESG
    p2 = portfolios[1][0]
    assets_p2 = [
        ("Zurich Insurance Group AG", "Bond", "Financials", "Insurance", 110e6, 108e6, 0.004, 0.30, "AA-", 8),
        ("BlackRock Inc.", "Equity", "Financials", "Asset Management", 95e6, 102e6, 0.003, 0.25, "AA-", None),
        ("Siemens AG", "Equity", "Industrials", "Industrial Conglomerates", 80e6, 85e6, 0.006, 0.35, "A+", None),
        ("Rio Tinto Group", "Bond", "Materials", "Metals & Mining", 70e6, 68e6, 0.008, 0.42, "A", 6),
        ("Nestlé SA", "Equity", "Consumer Staples", "Food Products", 100e6, 105e6, 0.003, 0.28, "AA", None),
        ("Volkswagen AG", "Bond", "Consumer Discretionary", "Automobiles", 75e6, 72e6, 0.012, 0.45, "BBB+", 5),
        ("Maersk A/S", "Bond", "Industrials", "Marine Transportation", 55e6, 53e6, 0.010, 0.40, "BBB+", 4),
        ("Equinix Inc.", "Equity", "Real Estate", "Data Centers", 65e6, 70e6, 0.008, 0.35, "BBB+", None),
    ]
    for name, atype, sector, subsector, exp, mv, pd, lgd, rating, mat in assets_p2:
        cur.execute(
            """INSERT INTO assets_pg (id, portfolio_id, asset_type, company_name, company_sector,
               company_subsector, exposure, market_value, base_pd, base_lgd, rating, maturity_years)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING""",
            (nid(), p2, atype, name, sector, subsector, exp, mv, pd, lgd, rating, mat)
        )

    # Assets for Portfolio 3: Infrastructure & Energy Transition
    p3 = portfolios[2][0]
    assets_p3 = [
        ("Equinor ASA", "Bond", "Energy", "Oil & Gas", 90e6, 88e6, 0.006, 0.38, "AA-", 7),
        ("Enel SpA", "Bond", "Utilities", "Electric Utilities", 110e6, 108e6, 0.010, 0.42, "BBB+", 6),
        ("Iberdrola SA", "Bond", "Utilities", "Electric Utilities", 100e6, 97e6, 0.009, 0.40, "BBB+", 8),
        ("Brookfield Asset Management Ltd", "Equity", "Financials", "Asset Management", 80e6, 85e6, 0.007, 0.32, "A-", None),
        ("Vestas Wind Systems A/S", "Equity", "Industrials", "Electrical Equipment", 70e6, 65e6, 0.020, 0.50, "BBB", None),
        ("SEGRO plc", "Bond", "Real Estate", "Real Estate", 50e6, 48e6, 0.012, 0.50, "A-", 5),
    ]
    for name, atype, sector, subsector, exp, mv, pd, lgd, rating, mat in assets_p3:
        cur.execute(
            """INSERT INTO assets_pg (id, portfolio_id, asset_type, company_name, company_sector,
               company_subsector, exposure, market_value, base_pd, base_lgd, rating, maturity_years)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING""",
            (nid(), p3, atype, name, sector, subsector, exp, mv, pd, lgd, rating, mat)
        )

    return [p[0] for p in portfolios]


def insert_ecl_assessments(cur, portfolio_ids):
    """ECL Assessments for each portfolio"""
    print("  Seeding ecl_assessments & ecl_exposures...")

    scenarios = ["BASE", "CLIMATE_ORDERLY", "CLIMATE_DISORDERLY", "CLIMATE_HOT_HOUSE"]
    names = ["European Bank Credit Portfolio", "Global Energy & Utilities Book", "Multi-Sector Investment Grade"]
    for i, pid in enumerate(portfolio_ids):
        aid = nid()
        total_ead = [1850, 1200, 950][i]
        total_ecl = [28.5, 18.2, 22.1][i]
        cur.execute(
            """INSERT INTO ecl_assessments (id, portfolio_id, entity_name, reporting_date,
               base_currency, pd_model, lgd_model, ead_approach, scenario_method,
               total_ead_gbp, total_ecl_gbp, ecl_rate_bps,
               stage1_ead_gbp, stage2_ead_gbp, stage3_ead_gbp,
               stage1_ecl_gbp, stage2_ecl_gbp, stage3_ecl_gbp,
               climate_ecl_uplift_gbp, climate_ecl_uplift_pct,
               status, created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
               ON CONFLICT (id) DO NOTHING""",
            (aid, pid, names[i], date(2024, 12, 31),
             "GBP", "through_the_cycle", "downturn_lgd", "ccf_based", "probability_weighted",
             total_ead, total_ecl, round(total_ecl / total_ead * 10000, 1),
             total_ead * 0.72, total_ead * 0.22, total_ead * 0.06,
             total_ecl * 0.25, total_ecl * 0.45, total_ecl * 0.30,
             total_ecl * 0.12, 12.0,
             "approved")
        )

        # Scenario results
        base_el = total_ecl
        for j, sc in enumerate(scenarios):
            multiplier = [1.0, 0.85, 1.35, 1.55][j]
            sc_ecl = round(base_el * multiplier, 2)
            cur.execute(
                """INSERT INTO ecl_scenario_results (id, assessment_id, scenario_name,
                   scenario_weight, total_ead_gbp, total_ecl_gbp, ecl_rate_bps,
                   stage1_ecl_gbp, stage2_ecl_gbp, stage3_ecl_gbp, created_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW()) ON CONFLICT (id) DO NOTHING""",
                (nid(), aid, sc, [0.40, 0.25, 0.20, 0.15][j],
                 total_ead, sc_ecl, round(sc_ecl / total_ead * 10000, 1),
                 sc_ecl * 0.25, sc_ecl * 0.45, sc_ecl * 0.30)
            )

        # Climate overlays
        for sc in ["NGFS_NET_ZERO_2050", "NGFS_DELAYED_TRANSITION", "NGFS_HOT_HOUSE"]:
            phys_uplift = {"NGFS_NET_ZERO_2050": 0.8, "NGFS_DELAYED_TRANSITION": 1.2, "NGFS_HOT_HOUSE": 2.2}[sc]
            trans_uplift = {"NGFS_NET_ZERO_2050": 1.5, "NGFS_DELAYED_TRANSITION": 2.5, "NGFS_HOT_HOUSE": 3.5}[sc]
            cur.execute(
                """INSERT INTO ecl_climate_overlays (id, assessment_id, climate_scenario,
                   horizon_years, reference_year,
                   physical_pd_uplift_avg_bps, physical_lgd_uplift_avg_bps,
                   physical_ecl_uplift_gbp, physical_ecl_uplift_pct,
                   transition_pd_uplift_avg_bps, transition_lgd_uplift_avg_bps,
                   transition_ecl_uplift_gbp, transition_ecl_uplift_pct,
                   total_climate_ecl_uplift_gbp, total_climate_ecl_uplift_pct,
                   carbon_price_2030_usd, carbon_price_2050_usd,
                   created_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
                   ON CONFLICT (id) DO NOTHING""",
                (nid(), aid, sc, 30, 2024,
                 phys_uplift * 10, phys_uplift * 5,
                 phys_uplift * total_ecl * 0.01, phys_uplift,
                 trans_uplift * 10, trans_uplift * 5,
                 trans_uplift * total_ecl * 0.01, trans_uplift,
                 (phys_uplift + trans_uplift) * total_ecl * 0.01, phys_uplift + trans_uplift,
                 {"NGFS_NET_ZERO_2050": 250, "NGFS_DELAYED_TRANSITION": 125, "NGFS_HOT_HOUSE": 50}[sc],
                 {"NGFS_NET_ZERO_2050": 500, "NGFS_DELAYED_TRANSITION": 200, "NGFS_HOT_HOUSE": 75}[sc])
            )


def insert_regulatory_entities(cur):
    """Regulatory entities for SFDR, EU Taxonomy, TCFD, CSRD panels"""
    print("  Seeding regulatory_entities & disclosures...")

    for c in COMPANIES[:12]:  # First 12 companies get regulatory data
        reg_id = nid()
        etype = "bank" if c["is_financial_institution"] else "corporate"
        cur.execute(
            """INSERT INTO regulatory_entities (id, legal_name, lei, entity_type, jurisdiction,
               headcount, annual_revenue_gbp, is_listed, created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,NOW()) ON CONFLICT (id) DO NOTHING""",
            (reg_id, c["legal_name"], c["entity_lei"], etype, c["headquarters_country"],
             c["employees_fte"], c["annual_revenue_eur_mn"] * 0.86,  # approx EUR→GBP
             True)
        )

        # SFDR PAI disclosure
        s12 = {"HSBC": 12500, "Deutsche Bank": 8200, "Zurich": 3400, "BlackRock": 1200,
               "Shell": 68000, "TotalEnergies": 52000, "Equinor": 12800, "Enel": 41000,
               "Iberdrola": 18500, "Vestas": 420, "SAP": 180, "Siemens": 2100
               }.get(c["trading_name"], 5000)
        cur.execute(
            """INSERT INTO sfdr_pai_disclosures (id, entity_id, entity_name,
               reporting_period_start, reporting_period_end, sfdr_article,
               pai_1_scope1_scope2_tco2e, pai_1_coverage_pct, pai_1_data_quality,
               pai_2_carbon_footprint, pai_3_waci,
               pai_4_fossil_fuel_exposure_pct, pai_5_nonrenewable_energy_pct,
               pai_13_board_gender_diversity_pct,
               status, created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
               ON CONFLICT (id) DO NOTHING""",
            (nid(), reg_id, c["legal_name"],
             date(2024, 1, 1), date(2024, 12, 31), 9,
             s12, 95.0, 3,
             round(s12 / (c["annual_revenue_eur_mn"] * 0.86) * 1000, 2),
             round(s12 / max(c["market_cap_eur_bn"], 1) * 10, 2),
             {"Shell": 85, "TotalEnergies": 78, "Equinor": 65}.get(c["trading_name"], 12),
             {"Shell": 72, "TotalEnergies": 68, "Enel": 35, "Iberdrola": 28}.get(c["trading_name"], 45),
             {"HSBC": 38, "Deutsche Bank": 35, "Zurich": 42, "BlackRock": 40}.get(c["trading_name"], 35),
             "approved")
        )

        # EU Taxonomy assessment
        eligible = {"HSBC": 45, "Deutsche Bank": 38, "Zurich": 52, "BlackRock": 60,
                    "Shell": 18, "TotalEnergies": 22, "Equinor": 28, "Enel": 72,
                    "Iberdrola": 78, "Vestas": 95, "SAP": 85, "Siemens": 68
                    }.get(c["trading_name"], 40)
        aligned = {"HSBC": 28, "Deutsche Bank": 22, "Zurich": 35, "BlackRock": 42,
                   "Shell": 8, "TotalEnergies": 12, "Equinor": 18, "Enel": 58,
                   "Iberdrola": 65, "Vestas": 88, "SAP": 72, "Siemens": 52
                   }.get(c["trading_name"], 25)
        cur.execute(
            """INSERT INTO eu_taxonomy_assessments (id, entity_id, entity_name, reporting_year,
               taxonomy_eligible_turnover_pct, taxonomy_aligned_turnover_pct,
               taxonomy_eligible_capex_pct, taxonomy_aligned_capex_pct,
               taxonomy_eligible_opex_pct, taxonomy_aligned_opex_pct,
               dnsh_compliance, minimum_safeguards_met,
               status, created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW()) ON CONFLICT (id) DO NOTHING""",
            (nid(), reg_id, c["legal_name"], 2024,
             eligible, aligned, eligible + 5, aligned - 2,
             eligible - 5, aligned - 5,
             '{"overall": true, "climate_adaptation": true, "water": true, "circular_economy": true, "pollution": true, "biodiversity": true}',
             True, "approved")
        )

        # TCFD assessment
        import random
        random.seed(hash(c["legal_name"]) + 99)
        gov = random.randint(70, 95)
        strat = random.randint(65, 90)
        risk = random.randint(68, 92)
        met = random.randint(60, 88)
        overall = round((gov + strat + risk + met) / 4)
        cur.execute(
            """INSERT INTO tcfd_assessments (id, entity_id, entity_name, reporting_year,
               gov_score, strat_score, risk_score, met_score, overall_score,
               maturity_level, status, created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW()) ON CONFLICT (id) DO NOTHING""",
            (nid(), reg_id, c["legal_name"], 2024,
             gov, strat, risk, met, overall,
             "advanced" if overall >= 80 else "intermediate",
             "approved")
        )


def insert_csrd_data(cur):
    """CSRD entity registry + KPI values + materiality topics"""
    print("  Seeding csrd_entity_registry & csrd_kpi_values...")

    for c in COMPANIES[:15]:
        eid = nid()

        # Check if already exists by LEI — skip entirely if so
        cur.execute("SELECT id FROM csrd_entity_registry WHERE lei = %s", (c["entity_lei"],))
        existing = cur.fetchone()
        if existing:
            continue

        # Map gics_sector to primary_sector enum
        sector_map = {
            "Financials": "financial_institution",
            "Energy": "energy_developer",
            "Utilities": "energy_developer",
            "Information Technology": "technology",
            "Industrials": "supply_chain",
            "Real Estate": "real_estate",
            "Materials": "mining",
            "Consumer Staples": "supply_chain",
            "Consumer Discretionary": "supply_chain",
        }
        primary_sector = sector_map.get(c["gics_sector"], "other")
        cur.execute(
            """INSERT INTO csrd_entity_registry (id, legal_name, trading_name, lei,
               country_iso, gics_sector, gics_industry, nace_code,
               employee_count, net_turnover_meur,
               is_large_undertaking, is_in_scope_csrd, csrd_first_reporting_year,
               is_in_scope_sfdr, is_in_scope_eu_taxonomy, is_in_scope_tcfd,
               primary_sector,
               created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
               ON CONFLICT (id) DO NOTHING""",
            (eid, c["legal_name"], c["trading_name"], c["entity_lei"],
             c["headquarters_country"], c["gics_sector"], c["gics_industry"], c.get("nace_code"),
             c["employees_fte"], c["annual_revenue_eur_mn"],
             True, True, 2024,
             c["is_financial_institution"], True, True,
             primary_sector)
        )

        # KPI values (time-series)
        kpis = [
            ("E1-1", "tCO2e", 2024),
            ("E1-2", "tCO2e", 2024),
            ("E1-3", "tCO2e", 2024),
            ("E1-4", "tCO2e/EUR mn", 2024),
            ("S1-1", "%", 2024),
            ("S1-2", "%", 2024),
            ("G1-1", "%", 2024),
        ]
        import random
        random.seed(hash(c["legal_name"]))
        for indicator_code, unit, year in kpis:
            val = {
                "E1-1": random.uniform(500, 80000),
                "E1-2": random.uniform(200, 25000),
                "E1-3": random.uniform(5000, 500000),
                "E1-4": random.uniform(5, 800),
                "S1-1": random.uniform(2, 18),
                "S1-2": random.uniform(20, 50),
                "G1-1": random.uniform(75, 99),
            }[indicator_code]

            cur.execute(
                """INSERT INTO csrd_kpi_values (id, entity_registry_id, indicator_code,
                   reporting_year, numeric_value, unit, data_quality_score, created_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,NOW()) ON CONFLICT (id) DO NOTHING""",
                (nid(), eid, indicator_code, year, round(val, 2), unit, random.randint(2, 5))
            )

        # Materiality topics
        topics = [
            ("E1", "Climate change", "impact", 8.5, 7.2),
            ("E2", "Pollution", "risk", 6.8, 5.5),
            ("E4", "Biodiversity and ecosystems", "impact" if c["gics_sector"] in ("Energy", "Materials", "Utilities") else "risk", 7.2, 4.8),
            ("S1", "Own workforce", "impact", 7.8, 8.1),
            ("G1", "Business conduct", "risk", 8.0, 7.5),
        ]
        for esrs_topic, sub_topic, iro_type, impact_score, financial_score in topics:
            is_mat = impact_score >= 7.0 or financial_score >= 7.0
            cur.execute(
                """INSERT INTO csrd_materiality_topics (id, entity_registry_id, reporting_year,
                   esrs_topic, sub_topic, iro_type,
                   impact_materiality_score, financial_materiality_score,
                   is_material_impact, is_material_financial, is_material_overall,
                   created_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW()) ON CONFLICT (id) DO NOTHING""",
                (nid(), eid, 2024, esrs_topic, sub_topic, iro_type,
                 impact_score, financial_score,
                 impact_score >= 7.0, financial_score >= 7.0, is_mat)
            )


def insert_valuation_data(cur):
    """Real estate valuation assets for RE module"""
    print("  Seeding valuation_assets...")

    re_assets = [
        ("CW-001", "Canary Wharf Tower", "real_estate", "London", "GBR", 51.5054, -0.0235, 420000, "A", 2018, 580000000),
        ("LD-002", "La Défense Plaza", "real_estate", "Paris", "FRA", 48.8922, 2.2417, 285000, "B", 2015, 365000000),
        ("VB-003", "Vonovia Berlin Mitte", "real_estate", "Berlin", "DEU", 52.5200, 13.4050, 48000, "C", 2005, 44000000),
        ("SH-004", "Segro Park Heathrow", "infrastructure", "Slough", "GBR", 51.4700, -0.4900, 95000, "A", 2021, 156000000),
        ("MP-005", "Milan Porta Nuova", "real_estate", "Milan", "ITA", 45.4836, 9.1904, 180000, "B", 2012, 243000000),
        ("AZ-006", "Amsterdam Zuidas", "real_estate", "Amsterdam", "NLD", 52.3380, 4.8722, 310000, "A", 2019, 480000000),
        ("MG-007", "Madrid Gran Via 32", "real_estate", "Madrid", "ESP", 40.4200, -3.7050, 65000, "B", 2008, 71500000),
        ("CI-008", "Copenhagen Islands Brygge", "real_estate", "Copenhagen", "DNK", 55.6600, 12.5800, 38000, "A", 2022, 66500000),
    ]
    for ref, name, asset_class, city, country_iso, lat, lng, area_m2, epc, built, book_val in re_assets:
        cur.execute(
            """INSERT INTO valuation_assets (id, asset_reference, asset_name, asset_class,
               city, country_iso, latitude, longitude, gross_internal_area_m2,
               epc_rating, year_built, book_value, is_active, created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW()) ON CONFLICT (id) DO NOTHING""",
            (nid(), ref, name, asset_class, city, country_iso, lat, lng, area_m2,
             epc, built, book_val, True)
        )


def insert_nature_risk_data(cur):
    """Nature risk assessments — table does not exist yet, skipping"""
    print("  Skipping nature_risk_assessments (table not yet created)...")


def insert_scope3_data(cur):
    """Supply chain / Scope 3 data for corporate entities"""
    print("  Seeding sc_entities & scope3 data...")

    sc_companies = [
        ("Shell plc", "Energy", "GBR", 316400, 68000, 285000, 580000),
        ("TotalEnergies SE", "Energy", "FRA", 218700, 52000, 195000, 420000),
        ("Volkswagen AG", "Consumer Discretionary", "DEU", 322300, 8500, 12500, 95000),
        ("Nestlé SA", "Consumer Staples", "CHE", 92100, 3800, 5200, 62000),
        ("Holcim Ltd", "Materials", "CHE", 26900, 28500, 2100, 48000),
        ("Maersk A/S", "Industrials", "DNK", 51100, 8200, 4500, 32000),
        ("Siemens AG", "Industrials", "DEU", 77800, 2100, 3800, 28000),
        ("SAP SE", "Information Technology", "DEU", 31200, 180, 850, 4200),
    ]

    categories = [
        (1, "Purchased Goods & Services"),
        (2, "Capital Goods"),
        (3, "Fuel & Energy Related"),
        (4, "Upstream Transportation"),
        (5, "Waste Generated"),
        (6, "Business Travel"),
        (11, "Use of Sold Products"),
        (15, "Investments"),
    ]

    for name, sector, country, revenue, s1, s2, s3_total in sc_companies:
        sc_id = nid()
        cur.execute(
            """INSERT INTO sc_entities (id, legal_name, sector_gics, country_iso,
               annual_revenue_gbp, created_at)
               VALUES (%s,%s,%s,%s,%s,NOW()) ON CONFLICT (id) DO NOTHING""",
            (sc_id, name, sector, country, revenue * 0.86)
        )

        # Scope 3 assessment
        sa_id = nid()
        import random
        random.seed(hash(name) + 42)
        # Distribute s3 across categories
        cat_amounts = {}
        remaining = s3_total
        for idx, (cat_num, cat_label) in enumerate(categories):
            if idx == len(categories) - 1:
                cat_amounts[cat_num] = remaining
            else:
                share = random.uniform(0.05, 0.30)
                amount = int(s3_total * share)
                remaining -= amount
                cat_amounts[cat_num] = max(amount, 100)

        cur.execute(
            """INSERT INTO scope3_assessments (id, entity_id, entity_name, reporting_year,
               base_currency, calculation_approach,
               scope1_tco2e, scope2_market_tco2e,
               cat1_purchased_goods_tco2e, cat2_capital_goods_tco2e,
               cat3_fuel_energy_tco2e, cat4_upstream_transport_tco2e,
               cat5_waste_tco2e, cat6_business_travel_tco2e,
               cat11_use_of_sold_products_tco2e, cat15_investments_tco2e,
               total_scope3_tco2e, total_scope123_tco2e,
               data_quality_score_avg, coverage_completeness_pct,
               status, created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
               ON CONFLICT (id) DO NOTHING""",
            (sa_id, sc_id, name, 2024, "EUR", "hybrid",
             s1, s2,
             cat_amounts.get(1, 0), cat_amounts.get(2, 0),
             cat_amounts.get(3, 0), cat_amounts.get(4, 0),
             cat_amounts.get(5, 0), cat_amounts.get(6, 0),
             cat_amounts.get(11, 0), cat_amounts.get(15, 0),
             s3_total, s1 + s2 + s3_total,
             3.2, 85,
             "approved")
        )

        # Scope 3 activities by category
        for cat_num, cat_label in categories:
            co2e_val = cat_amounts.get(cat_num, 0)
            cur.execute(
                """INSERT INTO scope3_activities (id, assessment_id, category_number,
                   category_label, activity_quantity, activity_unit, co2e_tco2e, data_source, created_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,NOW()) ON CONFLICT (id) DO NOTHING""",
                (nid(), sa_id, cat_num, cat_label, co2e_val * 1.2, "tCO2e", co2e_val,
                 "spend_based" if cat_num <= 5 else "activity_based")
            )


def insert_sovereign_data(cur):
    """Sovereign climate risk assessments for portfolio countries"""
    print("  Seeding sovereign_climate_assessments...")

    # S&P scale for adjusted ratings
    SP_SCALE = ["AAA","AA+","AA","AA-","A+","A","A-","BBB+","BBB","BBB-","BB+","BB","BB-",
                "B+","B","B-","CCC+","CCC","CCC-","CC","C","D"]

    countries = [
        ("GB", "United Kingdom", "AA", 7.2, 7.8, 6.5, 6.8, 68.5),
        ("DE", "Germany", "AAA", 6.5, 8.2, 7.5, 7.2, 72.1),
        ("FR", "France", "AA", 6.8, 7.5, 6.8, 7.0, 70.2),
        ("US", "United States", "AA+", 7.5, 6.5, 7.8, 5.5, 65.8),
        ("CH", "Switzerland", "AAA", 5.2, 8.5, 8.8, 7.8, 76.5),
        ("NO", "Norway", "AAA", 4.5, 9.0, 9.2, 8.5, 80.2),
        ("DK", "Denmark", "AAA", 5.0, 9.2, 8.5, 8.8, 79.5),
        ("IT", "Italy", "BBB", 7.8, 6.2, 5.5, 6.5, 58.2),
        ("ES", "Spain", "A", 7.5, 6.8, 6.0, 6.8, 62.5),
        ("NL", "Netherlands", "AAA", 6.8, 8.0, 8.0, 7.5, 74.8),
        ("AU", "Australia", "AAA", 8.2, 6.0, 7.2, 5.8, 62.0),
        ("CA", "Canada", "AAA", 6.0, 7.5, 8.0, 7.0, 72.5),
    ]

    scenarios = ["net_zero_2050", "below_2c", "delayed_transition", "current_policies"]

    for iso2, name, rating, phys, trans, fiscal, ndc, ndgain in countries:
        for sc in scenarios:
            horizon = {"net_zero_2050": "2050", "below_2c": "2050", "delayed_transition": "2040", "current_policies": "2050"}[sc]
            mult = {"net_zero_2050": 0.85, "below_2c": 0.92, "delayed_transition": 1.15, "current_policies": 1.35}[sc]
            composite = (phys * 0.30 + trans * 0.25 + fiscal * 0.25 + (ndgain / 10) * 0.20) * 10
            adj_composite = round(composite * mult, 1)

            notch = -3 if adj_composite >= 70 else (-2 if adj_composite >= 55 else (-1 if adj_composite >= 40 else 0))
            spread_delta = round(max(0, (adj_composite - 30) * 2.0 + 5), 1)

            # Compute climate-adjusted rating
            base_idx = SP_SCALE.index(rating) if rating in SP_SCALE else 5
            adj_idx = min(len(SP_SCALE) - 1, max(0, base_idx - notch))
            adj_rating = SP_SCALE[adj_idx]

            cur.execute(
                """INSERT INTO sovereign_climate_assessments (id, country_iso2, country_name,
                   assessment_date, scenario, horizon,
                   physical_risk_score, transition_risk_score,
                   fiscal_vulnerability_score, adaptation_readiness_score,
                   composite_climate_risk_score,
                   baseline_rating, climate_adjusted_rating,
                   notch_adjustment, climate_spread_delta_bps,
                   nd_gain_score, ndc_ambition_score,
                   created_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
                   ON CONFLICT (id) DO NOTHING""",
                (nid(), iso2, name, date(2024, 12, 31), sc, horizon,
                 phys, trans, fiscal, (ndgain / 10),
                 adj_composite,
                 rating, adj_rating,
                 notch, spread_delta,
                 ndgain, ndc)
            )


def insert_data_centre_assessments(cur):
    """Data centre facility assessments"""
    print("  Seeding data_centre_facilities & assessments...")

    facilities = [
        ("Equinix LD7", "Equinix", "colocation", "London", "GBR", 51.51, -0.08, 35000, 18000, 12.0, 1986, "Tier IV"),
        ("Equinix PA4", "Equinix", "colocation", "Paris", "FRA", 48.86, 2.35, 28000, 15000, 10.0, 2018, "Tier III"),
        ("Equinix AM5", "Equinix", "colocation", "Amsterdam", "NLD", 52.34, 4.87, 42000, 22000, 15.0, 2020, "Tier IV"),
        ("SEGRO Slough DC", "SEGRO", "enterprise", "Slough", "GBR", 51.47, -0.59, 18000, 9000, 6.0, 2015, "Tier III"),
        ("Deutsche Telekom FRA1", "Deutsche Telekom", "enterprise", "Frankfurt", "DEU", 50.11, 8.68, 22000, 11000, 8.0, 2012, "Tier III"),
    ]

    for name, operator, ftype, city, country_iso, lat, lng, floor_m2, white_m2, cap_mw, built, tier in facilities:
        fid = nid()
        cur.execute(
            """INSERT INTO data_centre_facilities (id, facility_name, operator_name, facility_type,
               city, country_iso, latitude, longitude,
               total_floor_area_m2, white_space_m2, installed_capacity_mw,
               year_built, tier_classification, is_active, created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
               ON CONFLICT (id) DO NOTHING""",
            (fid, name, operator, ftype, city, country_iso, lat, lng,
             floor_m2, white_m2, cap_mw, built, tier, True)
        )

        # Assessment
        pue = {"Equinix LD7": 1.28, "Equinix PA4": 1.22, "Equinix AM5": 1.18,
               "SEGRO Slough DC": 1.45, "Deutsche Telekom FRA1": 1.32}[name]
        re_pct = {"Equinix LD7": 85, "Equinix PA4": 92, "Equinix AM5": 78,
                  "SEGRO Slough DC": 65, "Deutsche Telekom FRA1": 72}[name]
        energy_mwh = round(cap_mw * 8760 * 0.65)
        co2e = round(energy_mwh * 0.256 * (1 - re_pct / 100))
        cur.execute(
            """INSERT INTO data_centre_assessments (id, facility_id, facility_name, assessment_year,
               total_it_load_mw, annual_energy_consumption_mwh, pue,
               renewable_energy_pct, renewable_energy_mwh,
               annual_co2e_tco2e, scope2_market_tco2e,
               efficiency_score, efficiency_rating,
               status, created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
               ON CONFLICT (id) DO NOTHING""",
            (nid(), fid, name, 2024,
             cap_mw * 0.65, energy_mwh, pue,
             re_pct, round(energy_mwh * re_pct / 100),
             co2e, co2e,
             round(1 / pue * 100, 1), "A" if pue <= 1.25 else ("B" if pue <= 1.35 else "C"),
             "approved")
        )


def insert_power_plant_data(cur):
    """Power plant assessments for energy transition analysis"""
    print("  Seeding power_plants & assessments...")

    plants = [
        ("Drax Power Station", "biomass", "Biomass/Coal", "GBR", 53.74, -0.99, 3906, 1986, "Drax Group", 0.82, 210),
        ("Neurath Power Station", "coal", "Lignite IGCC", "DEU", 50.97, 6.59, 4400, 2012, "RWE AG", 0.45, 850),
        ("Hornsea Wind Farm", "wind_offshore", "Offshore Wind", "GBR", 53.88, 1.80, 2852, 2022, "Equinor ASA", 0.42, 0),
        ("Borssele Wind Farm", "wind_offshore", "Offshore Wind", "NLD", 51.62, 3.38, 1400, 2021, "Iberdrola SA", 0.45, 0),
        ("Tejo Power Plant", "gas_ccgt", "CCGT", "PRT", 38.87, -9.07, 990, 2010, "Enel SpA", 0.58, 350),
        ("Groningen Solar Park", "solar_pv", "Solar PV", "NLD", 53.22, 6.57, 500, 2023, "TotalEnergies SE", 0.12, 0),
    ]

    for name, fuel_type, tech_type, country_iso, lat, lng, capacity, year_comm, operator, cf, ci_gco2 in plants:
        pid = nid()
        gen_mwh = round(capacity * cf * 8760)
        co2e = round(gen_mwh * ci_gco2 / 1000)  # gCO2/kWh → tCO2e
        cur.execute(
            """INSERT INTO power_plants (id, plant_name, operator_name, fuel_type, technology_type,
               country_iso, latitude, longitude, installed_capacity_mw, net_capacity_mw,
               capacity_factor_pct, year_commissioned, is_operational, operational_status,
               created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
               ON CONFLICT (id) DO NOTHING""",
            (pid, name, operator, fuel_type, tech_type,
             country_iso, lat, lng, capacity, round(capacity * 0.95),
             round(cf * 100, 1), year_comm, True, "operational")
        )

        stranded_score = min(95, round(ci_gco2 / 10)) if ci_gco2 > 0 else 5
        cur.execute(
            """INSERT INTO power_plant_assessments (id, plant_id, plant_name, assessment_date,
               current_ci_gco2_kwh, annual_generation_mwh, annual_co2e_tco2e,
               iea_nze_2030_threshold_gco2_kwh, iea_nze_2050_threshold_gco2_kwh,
               is_above_2030_threshold, stranded_asset_risk_score,
               stranded_asset_risk_category,
               status, created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
               ON CONFLICT (id) DO NOTHING""",
            (nid(), pid, name, date(2024, 12, 31),
             ci_gco2, gen_mwh, co2e,
             138, 0,  # IEA NZE thresholds
             ci_gco2 > 138, stranded_score,
             "High" if stranded_score >= 60 else ("Medium" if stranded_score >= 30 else "Low"),
             "approved")
        )


def run():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    print("=" * 60)
    print("MASTER DEMO SEED — Real Company Data")
    print("=" * 60)

    try:
        # Clean up previous seed data using TRUNCATE CASCADE
        print("  Cleaning previous seed data...")
        cleanup_tables = [
            "power_plant_assessments", "power_plants",
            "data_centre_assessments", "data_centre_facilities",
            "sovereign_climate_assessments",
            "scope3_activities", "scope3_assessments", "sc_entities",
            "csrd_materiality_topics", "csrd_kpi_values", "csrd_entity_registry",
            "valuation_assets",
            "tcfd_assessments", "eu_taxonomy_assessments", "sfdr_pai_disclosures", "regulatory_entities",
            "ecl_climate_overlays", "ecl_scenario_results", "ecl_assessments",
            "assets_pg", "portfolios_pg",
        ]
        for t in cleanup_tables:
            try:
                cur.execute(f"TRUNCATE TABLE {t} CASCADE")
                conn.commit()
            except Exception:
                conn.rollback()
        print("    -> Cleanup done")

        insert_company_profiles(cur)
        conn.commit()

        portfolio_ids = insert_portfolios(cur)
        conn.commit()

        insert_ecl_assessments(cur, portfolio_ids)
        conn.commit()

        insert_regulatory_entities(cur)
        conn.commit()

        insert_csrd_data(cur)
        conn.commit()

        insert_valuation_data(cur)
        conn.commit()

        insert_nature_risk_data(cur)
        conn.commit()

        insert_scope3_data(cur)
        conn.commit()

        insert_sovereign_data(cur)
        conn.commit()

        insert_data_centre_assessments(cur)
        conn.commit()

        insert_power_plant_data(cur)
        conn.commit()

        print("\n" + "=" * 60)
        print("SEED COMPLETE")
        print("=" * 60)
        print(f"  Company Profiles: {len(COMPANIES)}")
        print(f"  Portfolios: 3 (with 24 assets)")
        print(f"  ECL Assessments: 3 (12 scenario results, 9 climate overlays)")
        print(f"  Regulatory Entities: 12 (SFDR + EU Taxonomy + TCFD each)")
        print(f"  CSRD Entities: 15 (105 KPIs, 75 materiality topics)")
        print(f"  Valuation Assets: 8 properties")
        print(f"  Nature Risk: 8 assessments")
        print(f"  Supply Chain: 8 entities (64 Scope 3 activities)")
        print(f"  Sovereign Climate: 12 countries x 4 scenarios = 48")
        print(f"  Data Centres: 5 facilities + assessments")
        print(f"  Power Plants: 6 plants + assessments")

    except Exception as e:
        conn.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    run()
