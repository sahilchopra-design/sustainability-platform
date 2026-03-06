"""Smoke tests for Session 12 -- Data Hub Serve Layer (A16)."""
import requests
import time

BASE = "http://127.0.0.1:8001"

# Wait for server
for _ in range(10):
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
        status, msg = "FAIL", str(e)
    results.append((name, status, msg))
    print(f"  [{status}] {name}: {msg}")


# -- Auth setup ---------------------------------------------------------------

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

token = get_token("datahub_serve@a2intel.com", "SecurePass99", "DataHub Tester")
headers = {"Authorization": f"Bearer {token}"} if token else {}


# -- 1. Data Hub Catalog: sources -------------------------------------------

def t_catalog_sources():
    r = requests.get(f"{BASE}/api/v1/data-hub-catalog/sources", headers=headers)
    d = r.json()
    sources = d.get("sources", [])
    keys = [s.get("key") for s in sources]
    has_all = all(k in keys for k in ["gleif", "sanctions", "climate_trace", "owid", "ngfs", "sbti", "sec_edgar", "yfinance"])
    return (r.status_code == 200 and has_all and d.get("total_sources") == 8,
            f"HTTP {r.status_code}, sources={len(sources)}, keys={keys}")
test("GET /data-hub-catalog/sources (8 sources)", t_catalog_sources)


# -- 2. Data Hub Catalog: coverage ------------------------------------------

def t_catalog_coverage():
    r = requests.get(f"{BASE}/api/v1/data-hub-catalog/coverage", headers=headers)
    d = r.json()
    cov = d.get("coverage", {})
    has_sections = all(k in cov for k in ["gleif", "sanctions", "climate_trace", "owid", "ngfs", "sbti", "sec_edgar", "yfinance"])
    return (r.status_code == 200 and has_sections,
            f"HTTP {r.status_code}, sections={list(cov.keys())}, total_records={d.get('total_records')}")
test("GET /data-hub-catalog/coverage", t_catalog_coverage)


# -- 3. Data Hub Catalog: cross-source search -------------------------------

def t_catalog_search():
    r = requests.get(f"{BASE}/api/v1/data-hub-catalog/search?q=Apple", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "total_hits" in d
            and "results" in d), f"HTTP {r.status_code}, hits={d.get('total_hits')}, sources={d.get('sources_matched')}"
test("GET /data-hub-catalog/search?q=Apple", t_catalog_search)


# -- 4. Data Hub Catalog: entity 360 view -----------------------------------

def t_entity_360():
    r = requests.get(f"{BASE}/api/v1/data-hub-catalog/entity/AAPL", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "sources" in d
            and "source_count" in d), f"HTTP {r.status_code}, sources_found={d.get('sources_found')}, count={d.get('source_count')}"
test("GET /data-hub-catalog/entity/AAPL (360 view)", t_entity_360)


# -- 5. Data Hub Catalog: freshness ----------------------------------------

def t_freshness():
    r = requests.get(f"{BASE}/api/v1/data-hub-catalog/freshness", headers=headers)
    d = r.json()
    return (r.status_code == 200 and "freshness" in d), f"HTTP {r.status_code}, sources={len(d.get('freshness', {}))}"
test("GET /data-hub-catalog/freshness", t_freshness)


# -- 6. Emissions by LEI ---------------------------------------------------

def t_emissions_lei():
    # Test with a placeholder LEI (won't match, but endpoint should return gracefully)
    r = requests.get(f"{BASE}/api/v1/emissions/by-lei/52990097DVJKY7AATU30", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "lei" in d
            and "source" in d), f"HTTP {r.status_code}, source={d.get('source')}"
test("GET /emissions/by-lei/{lei}", t_emissions_lei)


# -- 7. Glidepaths: NZBA sector -------------------------------------------

def t_glidepath_nze():
    r = requests.get(f"{BASE}/api/v1/glidepaths/nze/Energy?scenario=Net Zero 2050", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "sector" in d
            and "glidepath_series" in d), f"HTTP {r.status_code}, data_points={d.get('data_points')}"
test("GET /glidepaths/nze/Energy", t_glidepath_nze)


# -- 8. Glidepaths: CRREM pathway ------------------------------------------

def t_crrem_pathway():
    r = requests.get(f"{BASE}/api/v1/glidepaths/crrem/DE/office", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "pathway_series" in d
            and d.get("data_points", 0) > 0), f"HTTP {r.status_code}, data_points={d.get('data_points')}"
test("GET /glidepaths/crrem/DE/office", t_crrem_pathway)


# -- 9. Glidepaths: sectors list -------------------------------------------

def t_glidepath_sectors():
    r = requests.get(f"{BASE}/api/v1/glidepaths/sectors", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "ngfs_sectors" in d
            and "crrem_asset_types" in d), f"HTTP {r.status_code}, ngfs={len(d.get('ngfs_sectors',[]))}, crrem={len(d.get('crrem_asset_types',[]))}"
test("GET /glidepaths/sectors", t_glidepath_sectors)


# -- 10. Carbon prices: by scenario ----------------------------------------

def t_carbon_price():
    r = requests.get(f"{BASE}/api/v1/carbon-prices/Net Zero 2050?year=2030", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "scenario" in d
            and "price_usd" in d
            and "time_series" in d), f"HTTP {r.status_code}, price_usd={d.get('price_usd')}"
test("GET /carbon-prices/{scenario}?year=2030", t_carbon_price)


# -- 11. Carbon prices: scenarios list -------------------------------------

def t_carbon_price_scenarios():
    r = requests.get(f"{BASE}/api/v1/carbon-prices/scenarios", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "scenarios" in d
            and "total" in d), f"HTTP {r.status_code}, count={d.get('total')}, scenarios={len(d.get('scenarios', []))}"
test("GET /carbon-prices/scenarios", t_carbon_price_scenarios)


# -- 12. Benchmarks: sector ------------------------------------------------

def t_benchmark_sector():
    r = requests.get(f"{BASE}/api/v1/benchmarks/sector/Technology", headers=headers)
    d = r.json()
    return (r.status_code == 200 and "sector" in d), f"HTTP {r.status_code}, companies={d.get('companies')}"
test("GET /benchmarks/sector/Technology", t_benchmark_sector)


# -- 13. Benchmarks: all sectors -------------------------------------------

def t_benchmark_sectors():
    r = requests.get(f"{BASE}/api/v1/benchmarks/sectors", headers=headers)
    d = r.json()
    return (r.status_code == 200 and "sectors" in d), f"HTTP {r.status_code}, count={d.get('total_sectors')}"
test("GET /benchmarks/sectors", t_benchmark_sectors)


# -- 14. Benchmarks: stats -------------------------------------------------

def t_benchmark_stats():
    r = requests.get(f"{BASE}/api/v1/benchmarks/stats", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "market_data" in d
            and "edgar" in d
            and "sbti" in d), f"HTTP {r.status_code}, data={d}"
test("GET /benchmarks/stats", t_benchmark_stats)


# -- 15. No auth -> 401 ---------------------------------------------------

def t_noauth():
    r = requests.get(f"{BASE}/api/v1/data-hub-catalog/sources")
    return r.status_code == 401, f"HTTP {r.status_code}"
test("GET /data-hub-catalog/sources -> 401 without auth", t_noauth)


# -- Summary ----------------------------------------------------------------

print(f"\n{'='*60}")
passed = sum(1 for _, s, _ in results if s == "PASS")
total = len(results)
print(f"Session 12 Results: {passed}/{total} passed")
if passed < total:
    print("FAILURES:")
    for name, status, msg in results:
        if status == "FAIL":
            print(f"  - {name}: {msg}")
