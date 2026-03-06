"""
Seed China Trade Platform reference data into ctp_* tables.

Run from backend dir:
    python scripts/seed_china_trade_data.py

Idempotent: uses ON CONFLICT DO UPDATE so safe to re-run.
"""

from __future__ import annotations
import sys, os, datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.postgres import SessionLocal
from sqlalchemy import text

# ─── Master exporter data (20 companies) ────────────────────────────────────
EXPORTERS = [
    # Steel
    dict(entity_name="China Baowu Steel Group", entity_name_zh="中国宝武钢铁集团", sector="Steel",
         sub_sector="Integrated Steel", listed_exchange="SSE", ticker="600019.SS",
         cbam_applicable=True, hs_codes_cbam=["7208","7209","7210","7225"],
         avg_embedded_carbon_tco2_per_tonne=1.82, vs_eu_benchmark_pct=36.8,
         cbam_readiness_score=62, cbam_readiness_band="Advanced",
         annual_eu_export_volume_kt=4800.0, annual_eu_export_value_eur_mn=2880.0,
         annual_cbam_cost_est_eur_mn=189.4, cets_covered=True,
         cets_free_allocation_pct=68.0, iso14064_certified=True, sbt_committed=True,
         key_export_markets=["DE","FR","IT","NL","BE"], eu_customer_count=12),

    dict(entity_name="HBIS Group", entity_name_zh="河北钢铁集团", sector="Steel",
         sub_sector="Flat Steel", listed_exchange="SZSE", ticker="000709.SZ",
         cbam_applicable=True, hs_codes_cbam=["7208","7216"],
         avg_embedded_carbon_tco2_per_tonne=1.94, vs_eu_benchmark_pct=45.8,
         cbam_readiness_score=48, cbam_readiness_band="Developing",
         annual_eu_export_volume_kt=2100.0, annual_eu_export_value_eur_mn=1260.0,
         annual_cbam_cost_est_eur_mn=88.7, cets_covered=True,
         cets_free_allocation_pct=72.0, iso14064_certified=False, sbt_committed=False,
         key_export_markets=["DE","IT","TR","PL"], eu_customer_count=8),

    dict(entity_name="Ansteel Group", entity_name_zh="鞍钢集团", sector="Steel",
         sub_sector="Long Steel", listed_exchange="SSE", ticker="000898.SZ",
         cbam_applicable=True, hs_codes_cbam=["7213","7214","7215"],
         avg_embedded_carbon_tco2_per_tonne=2.01, vs_eu_benchmark_pct=51.0,
         cbam_readiness_score=39, cbam_readiness_band="Emerging",
         annual_eu_export_volume_kt=980.0, annual_eu_export_value_eur_mn=588.0,
         annual_cbam_cost_est_eur_mn=43.2, cets_covered=True,
         cets_free_allocation_pct=75.0, iso14064_certified=False, sbt_committed=False,
         key_export_markets=["DE","FR","ES"], eu_customer_count=5),

    # Aluminium
    dict(entity_name="Chalco (Aluminum Corp of China)", entity_name_zh="中国铝业", sector="Aluminium",
         sub_sector="Primary Aluminium", listed_exchange="SSE", ticker="601600.SS",
         cbam_applicable=True, hs_codes_cbam=["7601","7604","7605"],
         avg_embedded_carbon_tco2_per_tonne=12.4, vs_eu_benchmark_pct=119.6,
         cbam_readiness_score=55, cbam_readiness_band="Developing",
         annual_eu_export_volume_kt=620.0, annual_eu_export_value_eur_mn=1240.0,
         annual_cbam_cost_est_eur_mn=215.0, cets_covered=True,
         cets_free_allocation_pct=60.0, iso14064_certified=True, sbt_committed=False,
         key_export_markets=["DE","IT","FR","ES"], eu_customer_count=9),

    dict(entity_name="Xinfa Group", entity_name_zh="信发集团", sector="Aluminium",
         sub_sector="Primary Aluminium / Power", listed_exchange=None, ticker=None,
         cbam_applicable=True, hs_codes_cbam=["7601"],
         avg_embedded_carbon_tco2_per_tonne=14.8, vs_eu_benchmark_pct=162.2,
         cbam_readiness_score=22, cbam_readiness_band="Emerging",
         annual_eu_export_volume_kt=310.0, annual_eu_export_value_eur_mn=620.0,
         annual_cbam_cost_est_eur_mn=125.0, cets_covered=False,
         cets_free_allocation_pct=None, iso14064_certified=False, sbt_committed=False,
         key_export_markets=["NL","DE"], eu_customer_count=3),

    # Cement
    dict(entity_name="China Resources Cement", entity_name_zh="华润水泥", sector="Cement",
         sub_sector="Portland Cement", listed_exchange="HKEX", ticker="1313.HK",
         cbam_applicable=True, hs_codes_cbam=["2523","6811"],
         avg_embedded_carbon_tco2_per_tonne=0.74, vs_eu_benchmark_pct=30.1,
         cbam_readiness_score=68, cbam_readiness_band="Advanced",
         annual_eu_export_volume_kt=180.0, annual_eu_export_value_eur_mn=36.0,
         annual_cbam_cost_est_eur_mn=3.2, cets_covered=True,
         cets_free_allocation_pct=78.0, iso14064_certified=True, sbt_committed=True,
         key_export_markets=["DE","NL","BE"], eu_customer_count=4),

    dict(entity_name="CNBM (China National Building Material)", entity_name_zh="中国建材集团", sector="Cement",
         sub_sector="Special Cement", listed_exchange="HKEX", ticker="3323.HK",
         cbam_applicable=True, hs_codes_cbam=["2523"],
         avg_embedded_carbon_tco2_per_tonne=0.68, vs_eu_benchmark_pct=19.5,
         cbam_readiness_score=72, cbam_readiness_band="Advanced",
         annual_eu_export_volume_kt=95.0, annual_eu_export_value_eur_mn=19.0,
         annual_cbam_cost_est_eur_mn=1.6, cets_covered=True,
         cets_free_allocation_pct=80.0, iso14064_certified=True, sbt_committed=True,
         key_export_markets=["DE","AT","CH"], eu_customer_count=6),

    # Chemicals / Fertiliser
    dict(entity_name="Sinopec (China Petrochemical Corp)", entity_name_zh="中国石化", sector="Chemicals",
         sub_sector="Petrochemicals", listed_exchange="SSE", ticker="600028.SS",
         cbam_applicable=True, hs_codes_cbam=["2905","2917","3102"],
         avg_embedded_carbon_tco2_per_tonne=0.92, vs_eu_benchmark_pct=42.3,
         cbam_readiness_score=61, cbam_readiness_band="Advanced",
         annual_eu_export_volume_kt=1200.0, annual_eu_export_value_eur_mn=960.0,
         annual_cbam_cost_est_eur_mn=38.4, cets_covered=True,
         cets_free_allocation_pct=55.0, iso14064_certified=True, sbt_committed=False,
         key_export_markets=["DE","NL","BE","FR"], eu_customer_count=14),

    dict(entity_name="Sinochem Holdings", entity_name_zh="中化集团", sector="Chemicals",
         sub_sector="Specialty Chemicals", listed_exchange="SZSE", ticker="000728.SZ",
         cbam_applicable=True, hs_codes_cbam=["3102","3105"],
         avg_embedded_carbon_tco2_per_tonne=0.58, vs_eu_benchmark_pct=-10.2,
         cbam_readiness_score=74, cbam_readiness_band="Advanced",
         annual_eu_export_volume_kt=850.0, annual_eu_export_value_eur_mn=680.0,
         annual_cbam_cost_est_eur_mn=12.1, cets_covered=True,
         cets_free_allocation_pct=62.0, iso14064_certified=True, sbt_committed=True,
         key_export_markets=["DE","FR","IT","NL","PL"], eu_customer_count=11),

    # EV / Battery / Solar
    dict(entity_name="LONGi Green Energy", entity_name_zh="隆基绿能", sector="Solar",
         sub_sector="Monocrystalline Silicon / Modules", listed_exchange="SSE", ticker="601012.SS",
         cbam_applicable=False, hs_codes_cbam=[],
         avg_embedded_carbon_tco2_per_tonne=0.48, vs_eu_benchmark_pct=None,
         cbam_readiness_score=88, cbam_readiness_band="Leader",
         annual_eu_export_volume_kt=None, annual_eu_export_value_eur_mn=3200.0,
         annual_cbam_cost_est_eur_mn=0.0, cets_covered=False,
         cets_free_allocation_pct=None, iso14064_certified=True, sbt_committed=True,
         key_export_markets=["DE","NL","ES","IT","PL"], eu_customer_count=22),

    dict(entity_name="BYD Co.", entity_name_zh="比亚迪", sector="EV & Battery",
         sub_sector="Electric Vehicles / LFP Batteries", listed_exchange="SZSE", ticker="002594.SZ",
         cbam_applicable=False, hs_codes_cbam=[],
         avg_embedded_carbon_tco2_per_tonne=0.38, vs_eu_benchmark_pct=None,
         cbam_readiness_score=91, cbam_readiness_band="Leader",
         annual_eu_export_volume_kt=None, annual_eu_export_value_eur_mn=8400.0,
         annual_cbam_cost_est_eur_mn=0.0, cets_covered=False,
         cets_free_allocation_pct=None, iso14064_certified=True, sbt_committed=True,
         key_export_markets=["DE","FR","NO","SE","NL"], eu_customer_count=35),

    dict(entity_name="CATL (CNNB)", entity_name_zh="宁德时代", sector="EV & Battery",
         sub_sector="Lithium-Ion Battery Cells", listed_exchange="SZSE", ticker="300750.SZ",
         cbam_applicable=False, hs_codes_cbam=[],
         avg_embedded_carbon_tco2_per_tonne=0.29, vs_eu_benchmark_pct=None,
         cbam_readiness_score=94, cbam_readiness_band="Leader",
         annual_eu_export_volume_kt=None, annual_eu_export_value_eur_mn=6800.0,
         annual_cbam_cost_est_eur_mn=0.0, cets_covered=False,
         cets_free_allocation_pct=None, iso14064_certified=True, sbt_committed=True,
         key_export_markets=["DE","FR","HU","PL","SE"], eu_customer_count=28),

    # Energy / Mining
    dict(entity_name="CNOOC Limited", entity_name_zh="中海油", sector="Oil & Gas",
         sub_sector="Offshore Upstream", listed_exchange="HKEX", ticker="0883.HK",
         cbam_applicable=False, hs_codes_cbam=[],
         avg_embedded_carbon_tco2_per_tonne=0.12, vs_eu_benchmark_pct=None,
         cbam_readiness_score=57, cbam_readiness_band="Developing",
         annual_eu_export_volume_kt=None, annual_eu_export_value_eur_mn=1200.0,
         annual_cbam_cost_est_eur_mn=0.0, cets_covered=False,
         cets_free_allocation_pct=None, iso14064_certified=True, sbt_committed=False,
         key_export_markets=["GB","NL","DE"], eu_customer_count=6),

    dict(entity_name="China Shenhua Energy", entity_name_zh="中国神华能源", sector="Power & Coal",
         sub_sector="Thermal Coal / Power Generation", listed_exchange="SSE", ticker="601088.SS",
         cbam_applicable=True, hs_codes_cbam=["2716"],
         avg_embedded_carbon_tco2_per_tonne=0.98, vs_eu_benchmark_pct=254.3,
         cbam_readiness_score=31, cbam_readiness_band="Emerging",
         annual_eu_export_volume_kt=None, annual_eu_export_value_eur_mn=420.0,
         annual_cbam_cost_est_eur_mn=18.6, cets_covered=True,
         cets_free_allocation_pct=82.0, iso14064_certified=False, sbt_committed=False,
         key_export_markets=["DE","NL"], eu_customer_count=3),

    dict(entity_name="Zijin Mining Group", entity_name_zh="紫金矿业", sector="Mining",
         sub_sector="Gold / Copper", listed_exchange="SSE", ticker="601899.SS",
         cbam_applicable=False, hs_codes_cbam=[],
         avg_embedded_carbon_tco2_per_tonne=0.22, vs_eu_benchmark_pct=None,
         cbam_readiness_score=52, cbam_readiness_band="Developing",
         annual_eu_export_volume_kt=None, annual_eu_export_value_eur_mn=890.0,
         annual_cbam_cost_est_eur_mn=0.0, cets_covered=False,
         cets_free_allocation_pct=None, iso14064_certified=True, sbt_committed=False,
         key_export_markets=["DE","CH","IT"], eu_customer_count=7),

    dict(entity_name="Ganfeng Lithium", entity_name_zh="赣锋锂业", sector="Mining",
         sub_sector="Lithium Compounds", listed_exchange="SZSE", ticker="002460.SZ",
         cbam_applicable=False, hs_codes_cbam=[],
         avg_embedded_carbon_tco2_per_tonne=0.18, vs_eu_benchmark_pct=None,
         cbam_readiness_score=78, cbam_readiness_band="Advanced",
         annual_eu_export_volume_kt=None, annual_eu_export_value_eur_mn=2100.0,
         annual_cbam_cost_est_eur_mn=0.0, cets_covered=False,
         cets_free_allocation_pct=None, iso14064_certified=True, sbt_committed=True,
         key_export_markets=["DE","GB","FR","NO"], eu_customer_count=16),

    # Additional
    dict(entity_name="Xinyi Solar", entity_name_zh="信义光能", sector="Solar",
         sub_sector="Solar Glass", listed_exchange="HKEX", ticker="0968.HK",
         cbam_applicable=False, hs_codes_cbam=[],
         avg_embedded_carbon_tco2_per_tonne=0.62, vs_eu_benchmark_pct=None,
         cbam_readiness_score=66, cbam_readiness_band="Advanced",
         annual_eu_export_volume_kt=None, annual_eu_export_value_eur_mn=480.0,
         annual_cbam_cost_est_eur_mn=0.0, cets_covered=False,
         cets_free_allocation_pct=None, iso14064_certified=True, sbt_committed=False,
         key_export_markets=["DE","NL","ES"], eu_customer_count=9),

    dict(entity_name="Trina Solar", entity_name_zh="天合光能", sector="Solar",
         sub_sector="PV Modules", listed_exchange="SSE", ticker="688599.SS",
         cbam_applicable=False, hs_codes_cbam=[],
         avg_embedded_carbon_tco2_per_tonne=0.41, vs_eu_benchmark_pct=None,
         cbam_readiness_score=85, cbam_readiness_band="Leader",
         annual_eu_export_volume_kt=None, annual_eu_export_value_eur_mn=2800.0,
         annual_cbam_cost_est_eur_mn=0.0, cets_covered=False,
         cets_free_allocation_pct=None, iso14064_certified=True, sbt_committed=True,
         key_export_markets=["DE","NL","ES","IT","FR"], eu_customer_count=19),

    dict(entity_name="Sany Heavy Industry", entity_name_zh="三一重工", sector="Heavy Equipment",
         sub_sector="Construction Machinery", listed_exchange="SSE", ticker="600031.SS",
         cbam_applicable=False, hs_codes_cbam=[],
         avg_embedded_carbon_tco2_per_tonne=1.12, vs_eu_benchmark_pct=None,
         cbam_readiness_score=44, cbam_readiness_band="Developing",
         annual_eu_export_volume_kt=None, annual_eu_export_value_eur_mn=760.0,
         annual_cbam_cost_est_eur_mn=0.0, cets_covered=False,
         cets_free_allocation_pct=None, iso14064_certified=False, sbt_committed=False,
         key_export_markets=["DE","FR","IT","PL"], eu_customer_count=8),

    dict(entity_name="Midea Group", entity_name_zh="美的集团", sector="Electronics",
         sub_sector="White Goods / Appliances", listed_exchange="SZSE", ticker="000333.SZ",
         cbam_applicable=False, hs_codes_cbam=[],
         avg_embedded_carbon_tco2_per_tonne=0.31, vs_eu_benchmark_pct=None,
         cbam_readiness_score=80, cbam_readiness_band="Leader",
         annual_eu_export_volume_kt=None, annual_eu_export_value_eur_mn=4200.0,
         annual_cbam_cost_est_eur_mn=0.0, cets_covered=False,
         cets_free_allocation_pct=None, iso14064_certified=True, sbt_committed=True,
         key_export_markets=["DE","FR","IT","ES","PL"], eu_customer_count=24),
]

# ─── CETS positions (sector-level) ───────────────────────────────────────────
ETS_POSITIONS = [
    dict(entity_name=None, sector="Power", year=2024,
         covered_installations=2196, annual_emissions_mtco2=4280.0,
         allocated_allowances_mtco2=3518.0, free_allocation_pct=82.1,
         purchased_allowances_mtco2=762.0, total_carbon_cost_cny_mn=72390.0,
         cets_price_cny=95.0, compliance_status="Deficit"),
    dict(entity_name=None, sector="Steel", year=2024,
         covered_installations=520, annual_emissions_mtco2=1820.0,
         allocated_allowances_mtco2=1564.0, free_allocation_pct=85.9,
         purchased_allowances_mtco2=256.0, total_carbon_cost_cny_mn=24320.0,
         cets_price_cny=95.0, compliance_status="Deficit"),
    dict(entity_name=None, sector="Aluminium", year=2024,
         covered_installations=180, annual_emissions_mtco2=580.0,
         allocated_allowances_mtco2=476.0, free_allocation_pct=82.1,
         purchased_allowances_mtco2=104.0, total_carbon_cost_cny_mn=9880.0,
         cets_price_cny=95.0, compliance_status="Deficit"),
    dict(entity_name=None, sector="Cement", year=2024,
         covered_installations=310, annual_emissions_mtco2=1240.0,
         allocated_allowances_mtco2=1116.0, free_allocation_pct=90.0,
         purchased_allowances_mtco2=124.0, total_carbon_cost_cny_mn=11780.0,
         cets_price_cny=95.0, compliance_status="Deficit"),
    dict(entity_name=None, sector="Chemicals", year=2024,
         covered_installations=280, annual_emissions_mtco2=620.0,
         allocated_allowances_mtco2=567.0, free_allocation_pct=91.5,
         purchased_allowances_mtco2=53.0, total_carbon_cost_cny_mn=5035.0,
         cets_price_cny=95.0, compliance_status="Surplus"),
    dict(entity_name=None, sector="Paper", year=2024,
         covered_installations=80, annual_emissions_mtco2=98.0,
         allocated_allowances_mtco2=105.0, free_allocation_pct=107.1,
         purchased_allowances_mtco2=0.0, total_carbon_cost_cny_mn=0.0,
         cets_price_cny=95.0, compliance_status="Surplus"),
    dict(entity_name=None, sector="Aviation", year=2024,
         covered_installations=32, annual_emissions_mtco2=62.0,
         allocated_allowances_mtco2=52.0, free_allocation_pct=83.9,
         purchased_allowances_mtco2=10.0, total_carbon_cost_cny_mn=950.0,
         cets_price_cny=95.0, compliance_status="Deficit"),
]

# ─── Marketplace listings ────────────────────────────────────────────────────
LISTINGS = [
    dict(listing_ref="CTP-L-001", seller_name="China Baowu Steel Group",
         listing_type="Allowance", standard="CETS", sector="Steel",
         project_name="CETS Phase 2 Surplus Allowances — Baowu",
         volume_tco2=500_000, price_usd_per_tco2=13.10,
         vintage_year=2024, expiry_date="2025-12-31",
         cbam_art9_eligible=True, co_benefits=[],
         country_of_origin="CN", status="Active"),
    dict(listing_ref="CTP-L-002", seller_name="Sichuan Forestry Carbon",
         listing_type="Offset", standard="CCER", sector="Forestry & Land Use",
         project_name="Sichuan Forest Conservation CCER Project",
         volume_tco2=120_000, price_usd_per_tco2=8.50,
         vintage_year=2023, expiry_date="2026-06-30",
         cbam_art9_eligible=False, co_benefits=["Biodiversity", "Community"],
         country_of_origin="CN", status="Active"),
    dict(listing_ref="CTP-L-003", seller_name="Yunnan Wind Power Co.",
         listing_type="Offset", standard="VCS", sector="Renewable Energy",
         project_name="Yunnan Highland Wind VCS REDD+",
         volume_tco2=80_000, price_usd_per_tco2=5.80,
         vintage_year=2022, expiry_date="2025-09-30",
         cbam_art9_eligible=False, co_benefits=["SDG7", "SDG13"],
         country_of_origin="CN", status="Active"),
    dict(listing_ref="CTP-L-004", seller_name="Chalco (Aluminum Corp of China)",
         listing_type="Certificate", standard="ASI", sector="Aluminium",
         project_name="ASI Performance Standard — Chalco Qinghai Smelter",
         volume_tco2=200_000, price_usd_per_tco2=21.40,
         vintage_year=2024, expiry_date="2026-03-31",
         cbam_art9_eligible=True, co_benefits=["ResponsibleSourcing"],
         country_of_origin="CN", status="Active"),
    dict(listing_ref="CTP-L-005", seller_name="CBEEX Exchange Block",
         listing_type="Allowance", standard="EU_ETS",
         sector="Power",
         project_name="EU ETS Allowances — Secondary Market Block",
         volume_tco2=1_000_000, price_usd_per_tco2=78.20,
         vintage_year=2025, expiry_date="2025-12-31",
         cbam_art9_eligible=True, co_benefits=[],
         country_of_origin="EU", status="Active"),
    dict(listing_ref="CTP-L-006", seller_name="Inner Mongolia Solar Farm",
         listing_type="Offset", standard="Gold_Standard", sector="Renewable Energy",
         project_name="Inner Mongolia Distributed Solar Gold Standard VER",
         volume_tco2=45_000, price_usd_per_tco2=12.80,
         vintage_year=2023, expiry_date="2026-12-31",
         cbam_art9_eligible=False, co_benefits=["SDG7","SDG8","Community","Gender"],
         country_of_origin="CN", status="Active"),
    dict(listing_ref="CTP-L-007", seller_name="HBIS Group",
         listing_type="Allowance", standard="CETS", sector="Steel",
         project_name="CETS Surplus Allowances — HBIS Tangshan Plant",
         volume_tco2=280_000, price_usd_per_tco2=13.05,
         vintage_year=2024, expiry_date="2025-12-31",
         cbam_art9_eligible=True, co_benefits=[],
         country_of_origin="CN", status="Active"),
    dict(listing_ref="CTP-L-008", seller_name="Guizhou Cement Group",
         listing_type="Offset", standard="CCER", sector="Cement",
         project_name="Guizhou Waste-Heat Recovery CCER Cement",
         volume_tco2=60_000, price_usd_per_tco2=7.80,
         vintage_year=2023, expiry_date="2025-12-31",
         cbam_art9_eligible=False, co_benefits=["EnergyEfficiency"],
         country_of_origin="CN", status="Active"),
]


def seed_entities(db):
    print("Seeding ctp_entities …")
    for e in EXPORTERS:
        import json
        db.execute(text("""
            INSERT INTO ctp_entities (
                entity_name, entity_name_zh, sector, sub_sector,
                listed_exchange, ticker, cbam_applicable, hs_codes_cbam,
                avg_embedded_carbon_tco2_per_tonne, vs_eu_benchmark_pct,
                cbam_readiness_score, cbam_readiness_band,
                annual_eu_export_volume_kt, annual_eu_export_value_eur_mn,
                annual_cbam_cost_est_eur_mn, cets_covered,
                cets_free_allocation_pct, iso14064_certified, sbt_committed,
                key_export_markets, eu_customer_count
            ) VALUES (
                :entity_name, :entity_name_zh, :sector, :sub_sector,
                :listed_exchange, :ticker, :cbam_applicable, :hs_codes_cbam,
                :avg_embedded_carbon_tco2_per_tonne, :vs_eu_benchmark_pct,
                :cbam_readiness_score, :cbam_readiness_band,
                :annual_eu_export_volume_kt, :annual_eu_export_value_eur_mn,
                :annual_cbam_cost_est_eur_mn, :cets_covered,
                :cets_free_allocation_pct, :iso14064_certified, :sbt_committed,
                :key_export_markets, :eu_customer_count
            )
            ON CONFLICT (entity_name) DO UPDATE SET
                cbam_readiness_score = EXCLUDED.cbam_readiness_score,
                cbam_readiness_band  = EXCLUDED.cbam_readiness_band,
                avg_embedded_carbon_tco2_per_tonne = EXCLUDED.avg_embedded_carbon_tco2_per_tonne,
                annual_cbam_cost_est_eur_mn = EXCLUDED.annual_cbam_cost_est_eur_mn
        """), {
            **e,
            "hs_codes_cbam": json.dumps(e["hs_codes_cbam"]),
            "key_export_markets": json.dumps(e["key_export_markets"]),
        })
    db.commit()
    print(f"  {len(EXPORTERS)} entities seeded.")


def seed_ets_positions(db):
    print("Seeding ctp_ets_positions …")
    for p in ETS_POSITIONS:
        db.execute(text("""
            INSERT INTO ctp_ets_positions (
                entity_name, sector, year,
                covered_installations, annual_emissions_mtco2,
                allocated_allowances_mtco2, free_allocation_pct,
                purchased_allowances_mtco2, total_carbon_cost_cny_mn,
                cets_price_cny, compliance_status
            ) VALUES (
                :entity_name, :sector, :year,
                :covered_installations, :annual_emissions_mtco2,
                :allocated_allowances_mtco2, :free_allocation_pct,
                :purchased_allowances_mtco2, :total_carbon_cost_cny_mn,
                :cets_price_cny, :compliance_status
            )
            ON CONFLICT (sector, year) DO UPDATE SET
                annual_emissions_mtco2 = EXCLUDED.annual_emissions_mtco2,
                cets_price_cny         = EXCLUDED.cets_price_cny,
                compliance_status      = EXCLUDED.compliance_status
        """), p)
    db.commit()
    print(f"  {len(ETS_POSITIONS)} ETS sector positions seeded.")


def seed_marketplace_listings(db):
    print("Seeding ctp_marketplace_listings …")
    import json
    for l in LISTINGS:
        db.execute(text("""
            INSERT INTO ctp_marketplace_listings (
                listing_ref, seller_name, listing_type, standard, sector,
                project_name, volume_tco2, price_usd_per_tco2,
                vintage_year, expiry_date, cbam_art9_eligible, co_benefits,
                country_of_origin, status
            ) VALUES (
                :listing_ref, :seller_name, :listing_type, :standard, :sector,
                :project_name, :volume_tco2, :price_usd_per_tco2,
                :vintage_year, :expiry_date, :cbam_art9_eligible, :co_benefits,
                :country_of_origin, :status
            )
            ON CONFLICT (listing_ref) DO UPDATE SET
                price_usd_per_tco2 = EXCLUDED.price_usd_per_tco2,
                volume_tco2        = EXCLUDED.volume_tco2,
                status             = EXCLUDED.status
        """), {
            **l,
            "co_benefits": json.dumps(l["co_benefits"]),
            "expiry_date": datetime.date.fromisoformat(l["expiry_date"]),
        })
    db.commit()
    print(f"  {len(LISTINGS)} marketplace listings seeded.")


def seed_ndc_pathways(db):
    print("Seeding ctp_ndc_pathways …")
    NDC = [
        dict(sector="Power",         baseline_year=2025, baseline_emissions_mtco2=4280.0,
             target_2030_mtco2=4100.0, target_2050_mtco2=600.0,  target_2060_mtco2=0.0,
             reduction_pct_2030=4.2,  key_metric="Renewables >60% by 2030; Carbon neutrality by 2060"),
        dict(sector="Steel",         baseline_year=2025, baseline_emissions_mtco2=1820.0,
             target_2030_mtco2=1640.0, target_2050_mtco2=520.0,  target_2060_mtco2=40.0,
             reduction_pct_2030=9.9,  key_metric="Scrap EAF share 30% by 2030; H2-DRI pilot 2028"),
        dict(sector="Aluminium",     baseline_year=2025, baseline_emissions_mtco2=580.0,
             target_2030_mtco2=500.0, target_2050_mtco2=120.0,  target_2060_mtco2=10.0,
             reduction_pct_2030=13.8, key_metric="Hydro / renewable power mix 55% by 2030"),
        dict(sector="Cement",        baseline_year=2025, baseline_emissions_mtco2=1240.0,
             target_2030_mtco2=1100.0, target_2050_mtco2=340.0,  target_2060_mtco2=30.0,
             reduction_pct_2030=11.3, key_metric="Alternative fuels 20%; CCUS pilot 5 MtCO2/yr by 2030"),
        dict(sector="Transport",     baseline_year=2025, baseline_emissions_mtco2=1060.0,
             target_2030_mtco2=920.0, target_2050_mtco2=280.0,  target_2060_mtco2=15.0,
             reduction_pct_2030=13.2, key_metric="NEV >50% new vehicle sales by 2030"),
        dict(sector="Buildings",     baseline_year=2025, baseline_emissions_mtco2=620.0,
             target_2030_mtco2=540.0, target_2050_mtco2=120.0,  target_2060_mtco2=5.0,
             reduction_pct_2030=12.9, key_metric="Green building code nationwide by 2027"),
        dict(sector="Agriculture",   baseline_year=2025, baseline_emissions_mtco2=620.0,
             target_2030_mtco2=590.0, target_2050_mtco2=480.0,  target_2060_mtco2=380.0,
             reduction_pct_2030=4.8,  key_metric="Methane reduction 30% vs 2020 by 2030 (Global Pledge)"),
        dict(sector="Land Use / Forestry", baseline_year=2025, baseline_emissions_mtco2=-560.0,
             target_2030_mtco2=-680.0, target_2050_mtco2=-900.0, target_2060_mtco2=-1200.0,
             reduction_pct_2030=21.4, key_metric="Forest stock volume +6 bn m³ vs 2005 by 2030"),
    ]
    for p in NDC:
        db.execute(text("""
            INSERT INTO ctp_ndc_pathways (
                sector, baseline_year, baseline_emissions_mtco2,
                target_2030_mtco2, target_2050_mtco2, target_2060_mtco2,
                reduction_pct_2030, key_metric
            ) VALUES (
                :sector, :baseline_year, :baseline_emissions_mtco2,
                :target_2030_mtco2, :target_2050_mtco2, :target_2060_mtco2,
                :reduction_pct_2030, :key_metric
            )
            ON CONFLICT (sector) DO UPDATE SET
                target_2030_mtco2  = EXCLUDED.target_2030_mtco2,
                reduction_pct_2030 = EXCLUDED.reduction_pct_2030,
                key_metric         = EXCLUDED.key_metric
        """), p)
    db.commit()
    print(f"  {len(NDC)} NDC pathways seeded.")


def seed_supplier_requirements(db):
    print("Seeding ctp_supplier_requirements …")
    REQS = [
        dict(importer_name="Volkswagen AG", importer_country="DE", framework="CSDDD",
             product_category="Steel", hs_code_prefix="7208",
             max_carbon_intensity_tco2_per_tonne=1.10, target_year=2030,
             required_certifications=["ResponsibleSteel","ISO14064"], cbam_art9_eligible=True),
        dict(importer_name="ArcelorMittal", importer_country="LU", framework="CBAM",
             product_category="Steel", hs_code_prefix="7208",
             max_carbon_intensity_tco2_per_tonne=1.50, target_year=2030,
             required_certifications=["ResponsibleSteel"], cbam_art9_eligible=True),
        dict(importer_name="Airbus SE", importer_country="FR", framework="CSDDD",
             product_category="Aluminium", hs_code_prefix="7601",
             max_carbon_intensity_tco2_per_tonne=8.00, target_year=2030,
             required_certifications=["ASI","ISO14064"], cbam_art9_eligible=True),
        dict(importer_name="BASF SE", importer_country="DE", framework="CBAM",
             product_category="Chemicals", hs_code_prefix="3102",
             max_carbon_intensity_tco2_per_tonne=0.80, target_year=2025,
             required_certifications=["ISO14064"], cbam_art9_eligible=False),
        dict(importer_name="Stellantis NV", importer_country="NL", framework="CSDDD",
             product_category="Aluminium", hs_code_prefix="7604",
             max_carbon_intensity_tco2_per_tonne=6.50, target_year=2028,
             required_certifications=["ASI"], cbam_art9_eligible=True),
        dict(importer_name="Holcim AG", importer_country="CH", framework="SBTi",
             product_category="Cement", hs_code_prefix="2523",
             max_carbon_intensity_tco2_per_tonne=0.60, target_year=2030,
             required_certifications=["ISO14064"], cbam_art9_eligible=False),
    ]
    import json
    for r in REQS:
        db.execute(text("""
            INSERT INTO ctp_supplier_requirements (
                importer_name, importer_country, framework, product_category,
                hs_code_prefix, max_carbon_intensity_tco2_per_tonne,
                target_year, required_certifications, cbam_art9_eligible
            ) VALUES (
                :importer_name, :importer_country, :framework, :product_category,
                :hs_code_prefix, :max_carbon_intensity_tco2_per_tonne,
                :target_year, :required_certifications, :cbam_art9_eligible
            )
            ON CONFLICT (importer_name, product_category) DO UPDATE SET
                max_carbon_intensity_tco2_per_tonne = EXCLUDED.max_carbon_intensity_tco2_per_tonne,
                target_year = EXCLUDED.target_year
        """), {**r, "required_certifications": json.dumps(r["required_certifications"])})
    db.commit()
    print(f"  {len(REQS)} supplier requirements seeded.")


def seed_trade_corridors(db):
    print("Seeding ctp_trade_corridors …")
    CORRIDORS = [
        dict(corridor_name="China → EU",   origin_country="CN", destination_country="EU",
             trade_value_usd_bn=618.0, cbam_applicable=True,
             annual_cbam_liability_est_eur_mn=4280.0, arbitrage_eur_per_tco2=52.84,
             dominant_cbam_sector="Steel", top_sectors=["Steel","Aluminium","Chemicals","Solar","EV"],
             cets_deductible_pct=34.0),
        dict(corridor_name="China → GB",   origin_country="CN", destination_country="GB",
             trade_value_usd_bn=98.0,  cbam_applicable=False,
             annual_cbam_liability_est_eur_mn=0.0, arbitrage_eur_per_tco2=None,
             dominant_cbam_sector=None, top_sectors=["Electronics","EV","Solar","Chemicals"],
             cets_deductible_pct=None),
        dict(corridor_name="China → US",   origin_country="CN", destination_country="US",
             trade_value_usd_bn=428.0, cbam_applicable=False,
             annual_cbam_liability_est_eur_mn=0.0, arbitrage_eur_per_tco2=None,
             dominant_cbam_sector=None, top_sectors=["Electronics","Machinery","Chemicals","EV"],
             cets_deductible_pct=None),
        dict(corridor_name="China → JP",   origin_country="CN", destination_country="JP",
             trade_value_usd_bn=184.0, cbam_applicable=False,
             annual_cbam_liability_est_eur_mn=0.0, arbitrage_eur_per_tco2=None,
             dominant_cbam_sector=None, top_sectors=["Electronics","Steel","Chemicals","Machinery"],
             cets_deductible_pct=None),
        dict(corridor_name="China → KR",   origin_country="CN", destination_country="KR",
             trade_value_usd_bn=162.0, cbam_applicable=False,
             annual_cbam_liability_est_eur_mn=0.0, arbitrage_eur_per_tco2=None,
             dominant_cbam_sector=None, top_sectors=["Steel","Chemicals","Electronics"],
             cets_deductible_pct=None),
    ]
    import json
    for c in CORRIDORS:
        db.execute(text("""
            INSERT INTO ctp_trade_corridors (
                corridor_name, origin_country, destination_country,
                trade_value_usd_bn, cbam_applicable,
                annual_cbam_liability_est_eur_mn, arbitrage_eur_per_tco2,
                dominant_cbam_sector, top_sectors, cets_deductible_pct
            ) VALUES (
                :corridor_name, :origin_country, :destination_country,
                :trade_value_usd_bn, :cbam_applicable,
                :annual_cbam_liability_est_eur_mn, :arbitrage_eur_per_tco2,
                :dominant_cbam_sector, :top_sectors, :cets_deductible_pct
            )
            ON CONFLICT (origin_country, destination_country) DO UPDATE SET
                trade_value_usd_bn = EXCLUDED.trade_value_usd_bn,
                annual_cbam_liability_est_eur_mn = EXCLUDED.annual_cbam_liability_est_eur_mn
        """), {**c, "top_sectors": json.dumps(c["top_sectors"])})
    db.commit()
    print(f"  {len(CORRIDORS)} trade corridors seeded.")


def main():
    print("=" * 60)
    print("China Trade Platform — Reference Data Seeder")
    print("=" * 60)
    db = SessionLocal()
    try:
        seed_entities(db)
        seed_ets_positions(db)
        seed_marketplace_listings(db)
        seed_ndc_pathways(db)
        seed_supplier_requirements(db)
        seed_trade_corridors(db)
        print("\nAll seeding complete.")
    except Exception as exc:
        db.rollback()
        print(f"\nERROR: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
