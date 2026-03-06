"""Smoke tests for Session 13 -- Wire DataHubClient + PCAF DQS aggregation."""
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

token = get_token("session13_test@a2intel.com", "SecurePass99", "Session13 Tester")
headers = {"Authorization": f"Bearer {token}"} if token else {}


# -- 1. Data Hub health (same-process, always True) ---------------------------

def t_hub_health():
    """Import and call health_check directly."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
    from services.data_hub_client import health_check
    result = health_check()
    return result is True, f"health_check={result}"
test("DataHubClient.health_check() returns True", t_hub_health)


# -- 2. get_emissions with fake LEI (should return None gracefully) -----------

def t_emissions_missing():
    from services.data_hub_client import get_emissions
    result = get_emissions("12345678901234567890")
    return result is None, f"result={result}"
test("DataHubClient.get_emissions(fake LEI) -> None", t_emissions_missing)


# -- 3. get_glidepath (may return None if no NGFS data, but no crash) ---------

def t_glidepath():
    from services.data_hub_client import get_glidepath
    result = get_glidepath("Energy", "Net Zero 2050")
    # Either None (no data) or a list
    ok = result is None or isinstance(result, list)
    return ok, f"type={type(result).__name__}, len={len(result) if result else 0}"
test("DataHubClient.get_glidepath(Energy) -> list|None", t_glidepath)


# -- 4. get_crrem_pathway returns reference data ------------------------------

def t_crrem():
    from services.data_hub_client import get_crrem_pathway
    result = get_crrem_pathway("DE", "office")
    ok = isinstance(result, list) and len(result) > 0
    return ok, f"type={type(result).__name__}, len={len(result) if result else 0}"
test("DataHubClient.get_crrem_pathway(DE, office) -> list", t_crrem)


# -- 5. get_carbon_price (may return None if no NGFS data) --------------------

def t_carbon_price():
    from services.data_hub_client import get_carbon_price
    result = get_carbon_price("Net Zero 2050", 2030)
    # Either None (no data) or a float
    ok = result is None or isinstance(result, float)
    return ok, f"result={result}"
test("DataHubClient.get_carbon_price() -> float|None", t_carbon_price)


# -- 6. get_sector_benchmark returns a dict -----------------------------------

def t_benchmark():
    from services.data_hub_client import get_sector_benchmark
    result = get_sector_benchmark("Technology")
    ok = isinstance(result, dict) and "sector" in result
    return ok, f"keys={list(result.keys()) if result else []}"
test("DataHubClient.get_sector_benchmark(Technology) -> dict", t_benchmark)


# -- 7. Glidepath sector endpoint (via HTTP) ----------------------------------

def t_glidepath_api():
    r = requests.get(
        f"{BASE}/api/v1/glidepath/sector/Energy",
        params={"portfolio_id": "test-portfolio"},
        headers=headers,
    )
    d = r.json()
    return (r.status_code == 200
            and "glidepath_source" in d
            and "data_points" in d), f"HTTP {r.status_code}, source={d.get('glidepath_source')}"
test("GET /glidepath/sector/Energy?portfolio_id=test", t_glidepath_api)


# -- 8. Glidepath CRREM asset endpoint ----------------------------------------

def t_crrem_asset_api():
    r = requests.get(
        f"{BASE}/api/v1/glidepath/crrem/asset/test-asset",
        params={"asset_type": "Office", "country": "DE"},
        headers=headers,
    )
    d = r.json()
    return (r.status_code == 200
            and "pathway_source" in d), f"HTTP {r.status_code}, source={d.get('pathway_source')}"
test("GET /glidepath/crrem/asset/test-asset", t_crrem_asset_api)


# -- 9. DQS aggregation endpoint (portfolio not found -> empty response) ------

def t_dqs_api():
    r = requests.get(
        f"{BASE}/api/v1/glidepath/dqs/nonexistent-portfolio",
        headers=headers,
    )
    d = r.json()
    return (r.status_code == 200
            and "weighted_dqs" in d
            and "dqs_distribution" in d), f"HTTP {r.status_code}, dqs={d.get('weighted_dqs')}"
test("GET /glidepath/dqs/nonexistent-portfolio", t_dqs_api)


# -- 10. DQS improvement plan endpoint ----------------------------------------

def t_dqs_improve_api():
    r = requests.get(
        f"{BASE}/api/v1/glidepath/dqs/nonexistent-portfolio/improve",
        headers=headers,
    )
    d = r.json()
    return (r.status_code == 200
            and "improvement_plan" in d), f"HTTP {r.status_code}, keys={list(d.keys())}"
test("GET /glidepath/dqs/nonexistent-portfolio/improve", t_dqs_improve_api)


# -- 11. DQS with real demo portfolio (seeded) --------------------------------

def t_dqs_demo():
    # Try with a demo portfolio if available
    r = requests.get(
        f"{BASE}/api/v1/glidepath/dqs/demo-eu-banking-sfdr",
        headers=headers,
    )
    d = r.json()
    # Either has data or returns graceful empty
    return (r.status_code == 200
            and "weighted_dqs" in d), f"HTTP {r.status_code}, dqs={d.get('weighted_dqs')}, assets={d.get('total_assets')}"
test("GET /glidepath/dqs/demo-eu-banking-sfdr", t_dqs_demo)


# -- 12. get_dqs_summary direct call -----------------------------------------

def t_dqs_direct():
    from services.data_hub_client import get_dqs_summary
    result = get_dqs_summary("demo-eu-banking-sfdr")
    # Either None (no data) or a dict
    ok = result is None or (isinstance(result, dict) and "weighted_dqs" in result)
    return ok, f"type={type(result).__name__}, dqs={result.get('weighted_dqs') if result else None}"
test("DataHubClient.get_dqs_summary(demo) -> dict|None", t_dqs_direct)


# -- 13. No auth -> 401 for DQS endpoint -------------------------------------

def t_noauth():
    r = requests.get(f"{BASE}/api/v1/glidepath/dqs/any-portfolio")
    return r.status_code == 401, f"HTTP {r.status_code}"
test("GET /glidepath/dqs/any -> 401 without auth", t_noauth)


# -- Summary ------------------------------------------------------------------

print(f"\n{'='*60}")
passed = sum(1 for _, s, _ in results if s == "PASS")
total = len(results)
print(f"Session 13 Results: {passed}/{total} passed")
if passed < total:
    print("FAILURES:")
    for name, status, msg in results:
        if status == "FAIL":
            print(f"  - {name}: {msg}")
