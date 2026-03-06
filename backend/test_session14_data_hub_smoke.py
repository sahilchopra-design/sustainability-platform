"""
Session 14 — Comprehensive Data Hub Smoke Tests (T4).

Validates every route group created in Sessions 7-13:
  - Ingestion framework (Session 7)
  - Entity resolution (Session 8)
  - Emissions data (Session 9)
  - Scenario data (Session 10)
  - Financial data (Session 11)
  - Serve-layer: catalog, glidepaths, carbon prices, benchmarks (Session 12)
  - DataHubClient wiring + PCAF DQS (Session 13)

Each test hits one endpoint and checks:
  1. HTTP 200 (or expected non-200)
  2. Expected top-level keys in response JSON
  3. Sensible response values where applicable
"""

import requests
import time
import sys

BASE = "http://127.0.0.1:8001"

# Wait for server
for _ in range(15):
    try:
        r = requests.get(f"{BASE}/api/health", timeout=3)
        if r.status_code == 200:
            break
    except Exception:
        time.sleep(2)

results = []


def test(name, fn):
    try:
        ok, msg = fn()
        status = "PASS" if ok else "FAIL"
    except Exception as e:
        status, msg = "FAIL", str(e)[:200]
    results.append((name, status, msg))
    print(f"  [{status}] {name}: {msg}")


# ── Auth setup ──────────────────────────────────────────────────────────────

def get_token(email, password, name):
    requests.post(f"{BASE}/api/auth/register", json={
        "email": email, "password": password, "name": name,
    })
    r = requests.post(f"{BASE}/api/auth/login", json={
        "email": email, "password": password,
    })
    if r.status_code == 200:
        return r.json().get("session_token")
    return None

token = get_token("session14_smoke@a2intel.com", "SmokeTest14!", "Smoke Tester")
headers = {"Authorization": f"Bearer {token}"} if token else {}

print("=" * 70)
print("SESSION 14 — Data Hub Comprehensive Smoke Tests")
print("=" * 70)

# ────────────────────────────────────────────────────────────────────────────
# GROUP 1: Ingestion Framework (Session 7)
# ────────────────────────────────────────────────────────────────────────────
print("\n--- Group 1: Ingestion Framework ---")


def t_ingesters_list():
    r = requests.get(f"{BASE}/api/v1/ingestion/ingesters", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "ingesters" in d), f"HTTP {r.status_code}, count={d.get('total', 'N/A')}"
test("GET /ingestion/ingesters", t_ingesters_list)


def t_ingestion_stats():
    r = requests.get(f"{BASE}/api/v1/ingestion/stats", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "total_sources" in d), f"HTTP {r.status_code}, keys={list(d.keys())[:5]}"
test("GET /ingestion/stats", t_ingestion_stats)


def t_ingestion_sources():
    r = requests.get(f"{BASE}/api/v1/ingestion/sources", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "sources" in d
            and len(d["sources"]) >= 6), f"HTTP {r.status_code}, sources={len(d.get('sources', []))}"
test("GET /ingestion/sources", t_ingestion_sources)


def t_ingestion_kpis():
    r = requests.get(f"{BASE}/api/v1/ingestion/kpis", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "kpis" in d), f"HTTP {r.status_code}, count={len(d.get('kpis', []))}"
test("GET /ingestion/kpis", t_ingestion_kpis)


def t_ingestion_scheduler():
    r = requests.get(f"{BASE}/api/v1/ingestion/scheduler", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "available" in d), f"HTTP {r.status_code}, available={d.get('available')}, running={d.get('running')}"
test("GET /ingestion/scheduler", t_ingestion_scheduler)


def t_ingestion_jobs():
    r = requests.get(f"{BASE}/api/v1/ingestion/jobs", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "jobs" in d), f"HTTP {r.status_code}, jobs={len(d.get('jobs', []))}"
test("GET /ingestion/jobs", t_ingestion_jobs)


def t_ingestion_module_coverage():
    r = requests.get(f"{BASE}/api/v1/ingestion/module-coverage", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "modules" in d), f"HTTP {r.status_code}, modules={len(d.get('modules', []))}"
test("GET /ingestion/module-coverage", t_ingestion_module_coverage)


# ────────────────────────────────────────────────────────────────────────────
# GROUP 2: Entity Resolution (Session 8)
# ────────────────────────────────────────────────────────────────────────────
print("\n--- Group 2: Entity Resolution ---")


def t_lei_list():
    r = requests.get(f"{BASE}/api/v1/entity-resolution/lei",
                     params={"limit": 5}, headers=headers)
    d = r.json()
    # May return 0 records if ingesters haven't run -- that's OK
    return (r.status_code == 200), f"HTTP {r.status_code}, keys={list(d.keys())[:4]}"
test("GET /entity-resolution/lei?limit=5", t_lei_list)


def t_lei_lookup_fake():
    r = requests.get(f"{BASE}/api/v1/entity-resolution/lei/FAKE12345678901234",
                     headers=headers)
    return r.status_code in (200, 404), f"HTTP {r.status_code}"
test("GET /entity-resolution/lei/FAKE... -> 200|404", t_lei_lookup_fake)


def t_sanctions_list():
    r = requests.get(f"{BASE}/api/v1/entity-resolution/sanctions",
                     params={"limit": 5}, headers=headers)
    d = r.json()
    # May return 0 records if ingesters haven't run
    return (r.status_code == 200), f"HTTP {r.status_code}, keys={list(d.keys())[:4]}"
test("GET /entity-resolution/sanctions?limit=5", t_sanctions_list)


def t_screening_results():
    r = requests.get(f"{BASE}/api/v1/entity-resolution/screening-results",
                     headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "results" in d), f"HTTP {r.status_code}, count={len(d.get('results', []))}"
test("GET /entity-resolution/screening-results", t_screening_results)


def t_entity_res_stats():
    r = requests.get(f"{BASE}/api/v1/entity-resolution/stats", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "lei_records" in d), f"HTTP {r.status_code}, leis={d.get('lei_records')}, sanctions={d.get('sanctions_entities')}"
test("GET /entity-resolution/stats", t_entity_res_stats)


def t_screening_post():
    r = requests.post(f"{BASE}/api/v1/entity-resolution/screen",
                      json={"entity_name": "Test Corp", "entity_type": "company"},
                      headers=headers)
    d = r.json()
    # 200 = success, 403 = role insufficient (viewer can't screen)
    return r.status_code in (200, 403), f"HTTP {r.status_code}, keys={list(d.keys())[:5]}"
test("POST /entity-resolution/screen", t_screening_post)


# ────────────────────────────────────────────────────────────────────────────
# GROUP 3: Emissions Data (Session 9)
# ────────────────────────────────────────────────────────────────────────────
print("\n--- Group 3: Emissions Data ---")


def t_emissions_by_lei():
    r = requests.get(f"{BASE}/api/v1/emissions/by-lei/FAKE12345678901234",
                     headers=headers)
    # 400 = invalid LEI format (expected for fake LEI), 200 = found, 404 = not found
    return r.status_code in (200, 400, 404), f"HTTP {r.status_code}"
test("GET /emissions/by-lei/FAKE...", t_emissions_by_lei)


def t_climate_trace():
    r = requests.get(f"{BASE}/api/v1/emissions/climate-trace",
                     params={"limit": 5}, headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "records" in d), f"HTTP {r.status_code}, count={len(d.get('records', []))}"
test("GET /emissions/climate-trace?limit=5", t_climate_trace)


def t_climate_trace_sectors():
    r = requests.get(f"{BASE}/api/v1/emissions/climate-trace/sectors",
                     headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "sectors" in d), f"HTTP {r.status_code}, count={len(d.get('sectors', []))}"
test("GET /emissions/climate-trace/sectors", t_climate_trace_sectors)


def t_climate_trace_countries():
    r = requests.get(f"{BASE}/api/v1/emissions/climate-trace/countries",
                     headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "countries" in d), f"HTTP {r.status_code}, count={len(d.get('countries', []))}"
test("GET /emissions/climate-trace/countries", t_climate_trace_countries)


def t_owid_list():
    r = requests.get(f"{BASE}/api/v1/emissions/owid",
                     params={"limit": 5}, headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "records" in d), f"HTTP {r.status_code}, count={len(d.get('records', []))}"
test("GET /emissions/owid?limit=5", t_owid_list)


def t_owid_countries():
    r = requests.get(f"{BASE}/api/v1/emissions/owid/countries", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "countries" in d), f"HTTP {r.status_code}, count={len(d.get('countries', []))}"
test("GET /emissions/owid/countries", t_owid_countries)


def t_owid_by_iso():
    r = requests.get(f"{BASE}/api/v1/emissions/owid/USA", headers=headers)
    # 200 = data found, 404 = no OWID data ingested for this country
    return r.status_code in (200, 404), f"HTTP {r.status_code}"
test("GET /emissions/owid/USA", t_owid_by_iso)


def t_emissions_stats():
    r = requests.get(f"{BASE}/api/v1/emissions/stats", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "climate_trace" in d
            and "owid" in d), f"HTTP {r.status_code}, ct={d.get('climate_trace')}, owid={d.get('owid')}"
test("GET /emissions/stats", t_emissions_stats)


# ────────────────────────────────────────────────────────────────────────────
# GROUP 4: Scenario Data (Session 10)
# ────────────────────────────────────────────────────────────────────────────
print("\n--- Group 4: Scenario Data ---")


def t_ngfs_list():
    r = requests.get(f"{BASE}/api/v1/scenario-data/ngfs",
                     params={"limit": 5}, headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "records" in d), f"HTTP {r.status_code}, count={len(d.get('records', []))}"
test("GET /scenario-data/ngfs?limit=5", t_ngfs_list)


def t_ngfs_scenarios():
    r = requests.get(f"{BASE}/api/v1/scenario-data/ngfs/scenarios", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "scenarios" in d), f"HTTP {r.status_code}, count={len(d.get('scenarios', []))}"
test("GET /scenario-data/ngfs/scenarios", t_ngfs_scenarios)


def t_ngfs_variables():
    r = requests.get(f"{BASE}/api/v1/scenario-data/ngfs/variables", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "variables" in d), f"HTTP {r.status_code}, count={len(d.get('variables', []))}"
test("GET /scenario-data/ngfs/variables", t_ngfs_variables)


def t_ngfs_models():
    r = requests.get(f"{BASE}/api/v1/scenario-data/ngfs/models", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "models" in d), f"HTTP {r.status_code}, count={len(d.get('models', []))}"
test("GET /scenario-data/ngfs/models", t_ngfs_models)


def t_sbti_list():
    r = requests.get(f"{BASE}/api/v1/scenario-data/sbti",
                     params={"limit": 5}, headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "records" in d), f"HTTP {r.status_code}, count={len(d.get('records', []))}"
test("GET /scenario-data/sbti?limit=5", t_sbti_list)


def t_sbti_sectors():
    r = requests.get(f"{BASE}/api/v1/scenario-data/sbti/sectors", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "sectors" in d), f"HTTP {r.status_code}, count={len(d.get('sectors', []))}"
test("GET /scenario-data/sbti/sectors", t_sbti_sectors)


def t_sbti_stats():
    r = requests.get(f"{BASE}/api/v1/scenario-data/sbti/stats", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "total_companies" in d), f"HTTP {r.status_code}, total={d.get('total_companies')}"
test("GET /scenario-data/sbti/stats", t_sbti_stats)


def t_scenario_stats():
    r = requests.get(f"{BASE}/api/v1/scenario-data/stats", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "ngfs" in d
            and "sbti" in d), f"HTTP {r.status_code}, ngfs={d.get('ngfs')}, sbti={d.get('sbti')}"
test("GET /scenario-data/stats", t_scenario_stats)


# ────────────────────────────────────────────────────────────────────────────
# GROUP 5: Financial Data (Session 11)
# ────────────────────────────────────────────────────────────────────────────
print("\n--- Group 5: Financial Data ---")


def t_edgar_list():
    r = requests.get(f"{BASE}/api/v1/financial-data/edgar",
                     params={"limit": 5}, headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "records" in d), f"HTTP {r.status_code}, count={len(d.get('records', []))}"
test("GET /financial-data/edgar?limit=5", t_edgar_list)


def t_edgar_companies():
    r = requests.get(f"{BASE}/api/v1/financial-data/edgar/companies", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "companies" in d), f"HTTP {r.status_code}, count={len(d.get('companies', []))}"
test("GET /financial-data/edgar/companies", t_edgar_companies)


def t_edgar_filing_types():
    r = requests.get(f"{BASE}/api/v1/financial-data/edgar/filing-types", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "filing_types" in d), f"HTTP {r.status_code}, count={len(d.get('filing_types', []))}"
test("GET /financial-data/edgar/filing-types", t_edgar_filing_types)


def t_market_list():
    r = requests.get(f"{BASE}/api/v1/financial-data/market",
                     params={"limit": 5}, headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "records" in d), f"HTTP {r.status_code}, count={len(d.get('records', []))}"
test("GET /financial-data/market?limit=5", t_market_list)


def t_market_tickers():
    r = requests.get(f"{BASE}/api/v1/financial-data/market/tickers", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "tickers" in d), f"HTTP {r.status_code}, count={len(d.get('tickers', []))}"
test("GET /financial-data/market/tickers", t_market_tickers)


def t_market_sectors():
    r = requests.get(f"{BASE}/api/v1/financial-data/market/sectors", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "sectors" in d), f"HTTP {r.status_code}, count={len(d.get('sectors', []))}"
test("GET /financial-data/market/sectors", t_market_sectors)


def t_financial_stats():
    r = requests.get(f"{BASE}/api/v1/financial-data/stats", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "edgar" in d
            and "market" in d), f"HTTP {r.status_code}, edgar={d.get('edgar')}, market={d.get('market')}"
test("GET /financial-data/stats", t_financial_stats)


# ────────────────────────────────────────────────────────────────────────────
# GROUP 6: Data Hub Serve Layer (Session 12)
# ────────────────────────────────────────────────────────────────────────────
print("\n--- Group 6: Data Hub Serve Layer ---")


def t_catalog_sources():
    r = requests.get(f"{BASE}/api/v1/data-hub-catalog/sources", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "sources" in d
            and len(d["sources"]) >= 6), f"HTTP {r.status_code}, count={len(d.get('sources', []))}"
test("GET /data-hub-catalog/sources", t_catalog_sources)


def t_catalog_coverage():
    r = requests.get(f"{BASE}/api/v1/data-hub-catalog/coverage", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "coverage" in d), f"HTTP {r.status_code}, sources={len(d.get('coverage', []))}"
test("GET /data-hub-catalog/coverage", t_catalog_coverage)


def t_catalog_search():
    r = requests.get(f"{BASE}/api/v1/data-hub-catalog/search",
                     params={"q": "energy"}, headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "results" in d), f"HTTP {r.status_code}, count={len(d.get('results', []))}"
test("GET /data-hub-catalog/search?q=energy", t_catalog_search)


def t_catalog_freshness():
    r = requests.get(f"{BASE}/api/v1/data-hub-catalog/freshness", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "freshness" in d), f"HTTP {r.status_code}, sources={len(d.get('freshness', []))}"
test("GET /data-hub-catalog/freshness", t_catalog_freshness)


def t_glidepath_serve_nze():
    r = requests.get(f"{BASE}/api/v1/glidepaths/nze/Energy", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "sector" in d
            and d["sector"] == "Energy"), f"HTTP {r.status_code}, sector={d.get('sector')}, pts={d.get('data_points')}"
test("GET /glidepaths/nze/Energy", t_glidepath_serve_nze)


def t_glidepath_serve_crrem():
    r = requests.get(f"{BASE}/api/v1/glidepaths/crrem/DE/office", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "pathway_series" in d
            and len(d["pathway_series"]) > 0), f"HTTP {r.status_code}, pts={d.get('data_points')}"
test("GET /glidepaths/crrem/DE/office", t_glidepath_serve_crrem)


def t_glidepath_serve_sectors():
    r = requests.get(f"{BASE}/api/v1/glidepaths/sectors", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "ngfs_sectors" in d
            and "crrem_asset_types" in d), f"HTTP {r.status_code}, ngfs={len(d.get('ngfs_sectors', []))}, crrem={len(d.get('crrem_asset_types', []))}"
test("GET /glidepaths/sectors", t_glidepath_serve_sectors)


def t_glidepath_serve_stats():
    r = requests.get(f"{BASE}/api/v1/glidepaths/stats", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "ngfs_emission_records" in d), f"HTTP {r.status_code}, emission_records={d.get('ngfs_emission_records')}"
test("GET /glidepaths/stats", t_glidepath_serve_stats)


def t_carbon_prices_scenario():
    r = requests.get(f"{BASE}/api/v1/carbon-prices/Net Zero 2050", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "scenario" in d
            and "time_series" in d), f"HTTP {r.status_code}, pts={len(d.get('time_series', []))}"
test("GET /carbon-prices/Net Zero 2050", t_carbon_prices_scenario)


def t_carbon_prices_scenarios_list():
    r = requests.get(f"{BASE}/api/v1/carbon-prices/scenarios", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "scenarios" in d), f"HTTP {r.status_code}, count={len(d.get('scenarios', []))}"
test("GET /carbon-prices/scenarios", t_carbon_prices_scenarios_list)


def t_carbon_prices_stats():
    r = requests.get(f"{BASE}/api/v1/carbon-prices/stats", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "total_data_points" in d), f"HTTP {r.status_code}, total={d.get('total_data_points')}"
test("GET /carbon-prices/stats", t_carbon_prices_stats)


def t_carbon_prices_compare():
    r = requests.get(f"{BASE}/api/v1/carbon-prices/compare",
                     params={"scenarios": "Net Zero 2050,Current Policies"},
                     headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "scenarios" in d), f"HTTP {r.status_code}, compared={len(d.get('scenarios', []))}"
test("GET /carbon-prices/compare", t_carbon_prices_compare)


def t_benchmarks_sector():
    r = requests.get(f"{BASE}/api/v1/benchmarks/sector/Technology", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "sector" in d), f"HTTP {r.status_code}, sector={d.get('sector')}"
test("GET /benchmarks/sector/Technology", t_benchmarks_sector)


def t_benchmarks_sectors():
    r = requests.get(f"{BASE}/api/v1/benchmarks/sectors", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "sectors" in d), f"HTTP {r.status_code}, count={len(d.get('sectors', []))}"
test("GET /benchmarks/sectors", t_benchmarks_sectors)


def t_benchmarks_stats():
    r = requests.get(f"{BASE}/api/v1/benchmarks/stats", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "market_data" in d), f"HTTP {r.status_code}, keys={list(d.keys())[:4]}"
test("GET /benchmarks/stats", t_benchmarks_stats)


# ────────────────────────────────────────────────────────────────────────────
# GROUP 7: Glidepath Consumer + DQS (Session 13)
# ────────────────────────────────────────────────────────────────────────────
print("\n--- Group 7: Glidepath Consumer + PCAF DQS ---")


def t_glidepath_sectors():
    r = requests.get(f"{BASE}/api/v1/glidepath/sectors", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "sectors" in d), f"HTTP {r.status_code}, sectors={len(d.get('sectors', []))}"
test("GET /glidepath/sectors", t_glidepath_sectors)


def t_glidepath_sector_energy():
    r = requests.get(f"{BASE}/api/v1/glidepath/sector/Energy",
                     params={"portfolio_id": "test-portfolio"},
                     headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "glidepath_source" in d
            and "data_points" in d), f"HTTP {r.status_code}, source={d.get('glidepath_source')}"
test("GET /glidepath/sector/Energy?portfolio_id=test", t_glidepath_sector_energy)


def t_glidepath_nzba_power():
    r = requests.get(f"{BASE}/api/v1/glidepath/nzba/Power", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "glidepath" in d
            and len(d["glidepath"]) > 0), f"HTTP {r.status_code}, pts={len(d.get('glidepath', []))}"
test("GET /glidepath/nzba/Power", t_glidepath_nzba_power)


def t_glidepath_crrem_office():
    r = requests.get(f"{BASE}/api/v1/glidepath/crrem/Office", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "pathway" in d
            and len(d["pathway"]) > 0), f"HTTP {r.status_code}, pts={len(d.get('pathway', []))}"
test("GET /glidepath/crrem/Office", t_glidepath_crrem_office)


def t_glidepath_crrem_asset():
    r = requests.get(f"{BASE}/api/v1/glidepath/crrem/asset/test-asset",
                     params={"asset_type": "Office", "country": "DE"},
                     headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "pathway_source" in d), f"HTTP {r.status_code}, source={d.get('pathway_source')}"
test("GET /glidepath/crrem/asset/test-asset", t_glidepath_crrem_asset)


def t_dqs_nonexistent():
    r = requests.get(f"{BASE}/api/v1/glidepath/dqs/nonexistent-portfolio",
                     headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "weighted_dqs" in d
            and "dqs_distribution" in d), f"HTTP {r.status_code}, dqs={d.get('weighted_dqs')}"
test("GET /glidepath/dqs/nonexistent-portfolio", t_dqs_nonexistent)


def t_dqs_demo():
    r = requests.get(f"{BASE}/api/v1/glidepath/dqs/demo-eu-banking-sfdr",
                     headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "weighted_dqs" in d), f"HTTP {r.status_code}, dqs={d.get('weighted_dqs')}, assets={d.get('total_assets')}"
test("GET /glidepath/dqs/demo-eu-banking-sfdr", t_dqs_demo)


def t_dqs_improve():
    r = requests.get(f"{BASE}/api/v1/glidepath/dqs/demo-eu-banking-sfdr/improve",
                     headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "improvement_plan" in d), f"HTTP {r.status_code}, current={d.get('current_weighted_dqs')}, improvable={d.get('improvable_assets')}"
test("GET /glidepath/dqs/demo/improve", t_dqs_improve)


def t_status_grid():
    r = requests.get(f"{BASE}/api/v1/glidepath/portfolio/test-portfolio/status-grid",
                     headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "grid" in d
            and "sectors" in d), f"HTTP {r.status_code}, sectors={d.get('sectors')}, grid_rows={len(d.get('grid', []))}"
test("GET /glidepath/portfolio/test/status-grid", t_status_grid)


# ────────────────────────────────────────────────────────────────────────────
# GROUP 8: Auth enforcement + error handling
# ────────────────────────────────────────────────────────────────────────────
print("\n--- Group 8: Auth Enforcement ---")


def t_noauth_dqs():
    r = requests.get(f"{BASE}/api/v1/glidepath/dqs/any-portfolio")
    return r.status_code == 401, f"HTTP {r.status_code}"
test("GET /glidepath/dqs/* no auth -> 401", t_noauth_dqs)


def t_noauth_glidepaths_serve():
    r = requests.get(f"{BASE}/api/v1/glidepaths/nze/Energy")
    return r.status_code == 401, f"HTTP {r.status_code}"
test("GET /glidepaths/nze/* no auth -> 401", t_noauth_glidepaths_serve)


def t_noauth_carbon_prices():
    r = requests.get(f"{BASE}/api/v1/carbon-prices/stats")
    return r.status_code == 401, f"HTTP {r.status_code}"
test("GET /carbon-prices/stats no auth -> 401", t_noauth_carbon_prices)


def t_noauth_benchmarks():
    r = requests.get(f"{BASE}/api/v1/benchmarks/stats")
    return r.status_code == 401, f"HTTP {r.status_code}"
test("GET /benchmarks/stats no auth -> 401", t_noauth_benchmarks)


def t_noauth_scenario_data():
    r = requests.get(f"{BASE}/api/v1/scenario-data/stats")
    return r.status_code == 401, f"HTTP {r.status_code}"
test("GET /scenario-data/stats no auth -> 401", t_noauth_scenario_data)


def t_noauth_financial_data():
    r = requests.get(f"{BASE}/api/v1/financial-data/stats")
    return r.status_code == 401, f"HTTP {r.status_code}"
test("GET /financial-data/stats no auth -> 401", t_noauth_financial_data)


# ────────────────────────────────────────────────────────────────────────────
# GROUP 9: DataHubClient direct functions (unit tests)
# ────────────────────────────────────────────────────────────────────────────
print("\n--- Group 9: DataHubClient Direct Calls ---")


def t_client_health():
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
    from services.data_hub_client import health_check
    result = health_check()
    return result is True, f"health_check={result}"
test("DataHubClient.health_check()", t_client_health)


def t_client_emissions_none():
    from services.data_hub_client import get_emissions
    result = get_emissions("12345678901234567890")
    return result is None, f"result={result}"
test("DataHubClient.get_emissions(fake LEI) -> None", t_client_emissions_none)


def t_client_glidepath():
    from services.data_hub_client import get_glidepath
    result = get_glidepath("Energy", "Net Zero 2050")
    ok = result is None or isinstance(result, list)
    return ok, f"type={type(result).__name__}, len={len(result) if result else 0}"
test("DataHubClient.get_glidepath(Energy)", t_client_glidepath)


def t_client_crrem():
    from services.data_hub_client import get_crrem_pathway
    result = get_crrem_pathway("DE", "office")
    ok = isinstance(result, list) and len(result) > 0
    return ok, f"type={type(result).__name__}, len={len(result) if result else 0}"
test("DataHubClient.get_crrem_pathway(DE, office)", t_client_crrem)


def t_client_carbon_price():
    from services.data_hub_client import get_carbon_price
    result = get_carbon_price("Net Zero 2050", 2030)
    ok = result is None or isinstance(result, float)
    return ok, f"result={result}"
test("DataHubClient.get_carbon_price()", t_client_carbon_price)


def t_client_benchmark():
    from services.data_hub_client import get_sector_benchmark
    result = get_sector_benchmark("Technology")
    ok = isinstance(result, dict) and "sector" in result
    return ok, f"keys={list(result.keys()) if result else []}"
test("DataHubClient.get_sector_benchmark(Technology)", t_client_benchmark)


def t_client_dqs():
    from services.data_hub_client import get_dqs_summary
    result = get_dqs_summary("demo-eu-banking-sfdr")
    ok = result is None or (isinstance(result, dict) and "weighted_dqs" in result)
    return ok, f"type={type(result).__name__}, dqs={result.get('weighted_dqs') if result else None}"
test("DataHubClient.get_dqs_summary(demo)", t_client_dqs)


# ── Summary ─────────────────────────────────────────────────────────────────

print(f"\n{'=' * 70}")
passed = sum(1 for _, s, _ in results if s == "PASS")
total = len(results)
failed = total - passed
print(f"Session 14 Data Hub Smoke Tests: {passed}/{total} passed, {failed} failed")

if failed > 0:
    print("\nFAILURES:")
    for name, status, msg in results:
        if status == "FAIL":
            print(f"  FAIL  {name}: {msg}")

# Group summary
groups = {}
current_group = None
for name, status, msg in results:
    # Heuristic: track which group we're in
    groups.setdefault(name, status)

print(f"\nGroup Results:")
group_names = [
    "Ingestion Framework", "Entity Resolution", "Emissions Data",
    "Scenario Data", "Financial Data", "Data Hub Serve Layer",
    "Glidepath + DQS", "Auth Enforcement", "DataHubClient Direct",
]
idx = 0
group_ranges = [
    (0, 7), (7, 13), (13, 21), (21, 29), (29, 36), (36, 50),
    (50, 59), (59, 65), (65, 72),
]
for gi, (start, end) in enumerate(group_ranges):
    group_results = results[start:end]
    gp = sum(1 for _, s, _ in group_results if s == "PASS")
    gt = len(group_results)
    marker = "OK" if gp == gt else "ISSUES"
    print(f"  [{marker}] {group_names[gi]}: {gp}/{gt}")

sys.exit(0 if failed == 0 else 1)
