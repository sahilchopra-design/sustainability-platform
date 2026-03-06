"""Smoke tests for Session 10 -- NGFS + SBTi Scenario Data Ingesters."""
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

token = get_token("scenario_test@a2intel.com", "SecurePass99", "Scenario Tester")
headers = {"Authorization": f"Bearer {token}"} if token else {}


# -- 1. Ingesters registered --------------------------------------------------

def t_ingesters():
    r = requests.get(f"{BASE}/api/v1/ingestion/ingesters", headers=headers)
    d = r.json()
    names = [i.get("display_name", "") for i in d.get("ingesters", [])]
    has_ngfs = any("NGFS" in n for n in names)
    has_sbti = any("SBTi" in n for n in names)
    return (r.status_code == 200 and has_ngfs and has_sbti,
            f"HTTP {r.status_code}, ingesters={names}")
test("GET /ingestion/ingesters (NGFS + SBTi registered)", t_ingesters)


# -- 2. Combined stats -------------------------------------------------------

def t_stats():
    r = requests.get(f"{BASE}/api/v1/scenario-data/stats", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "ngfs" in d
            and "sbti" in d), f"HTTP {r.status_code}, data={d}"
test("GET /scenario-data/stats", t_stats)


# -- 3. NGFS search (empty is OK) -------------------------------------------

def t_ngfs_search():
    r = requests.get(f"{BASE}/api/v1/scenario-data/ngfs?limit=5", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "total" in d
            and "records" in d), f"HTTP {r.status_code}, total={d.get('total')}"
test("GET /scenario-data/ngfs", t_ngfs_search)


# -- 4. NGFS scenarios list --------------------------------------------------

def t_ngfs_scenarios():
    r = requests.get(f"{BASE}/api/v1/scenario-data/ngfs/scenarios", headers=headers)
    d = r.json()
    return (r.status_code == 200 and "scenarios" in d), f"HTTP {r.status_code}, count={len(d.get('scenarios', []))}"
test("GET /scenario-data/ngfs/scenarios", t_ngfs_scenarios)


# -- 5. NGFS variables list --------------------------------------------------

def t_ngfs_variables():
    r = requests.get(f"{BASE}/api/v1/scenario-data/ngfs/variables", headers=headers)
    d = r.json()
    return (r.status_code == 200 and "variables" in d), f"HTTP {r.status_code}, count={len(d.get('variables', []))}"
test("GET /scenario-data/ngfs/variables", t_ngfs_variables)


# -- 6. NGFS models list -----------------------------------------------------

def t_ngfs_models():
    r = requests.get(f"{BASE}/api/v1/scenario-data/ngfs/models", headers=headers)
    d = r.json()
    return (r.status_code == 200 and "models" in d), f"HTTP {r.status_code}, count={len(d.get('models', []))}"
test("GET /scenario-data/ngfs/models", t_ngfs_models)


# -- 7. NGFS compare (empty is OK) ------------------------------------------

def t_ngfs_compare():
    r = requests.get(f"{BASE}/api/v1/scenario-data/ngfs/compare?variable=Price|Carbon", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "variable" in d
            and "scenarios" in d), f"HTTP {r.status_code}, scenarios={len(d.get('scenarios', []))}"
test("GET /scenario-data/ngfs/compare?variable=Price|Carbon", t_ngfs_compare)


# -- 8. SBTi search (empty is OK) -------------------------------------------

def t_sbti_search():
    r = requests.get(f"{BASE}/api/v1/scenario-data/sbti?limit=5", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "total" in d
            and "records" in d), f"HTTP {r.status_code}, total={d.get('total')}"
test("GET /scenario-data/sbti", t_sbti_search)


# -- 9. SBTi sectors --------------------------------------------------------

def t_sbti_sectors():
    r = requests.get(f"{BASE}/api/v1/scenario-data/sbti/sectors", headers=headers)
    d = r.json()
    return (r.status_code == 200 and "sectors" in d), f"HTTP {r.status_code}, count={len(d.get('sectors', []))}"
test("GET /scenario-data/sbti/sectors", t_sbti_sectors)


# -- 10. SBTi countries ------------------------------------------------------

def t_sbti_countries():
    r = requests.get(f"{BASE}/api/v1/scenario-data/sbti/countries", headers=headers)
    d = r.json()
    return (r.status_code == 200 and "countries" in d), f"HTTP {r.status_code}, count={len(d.get('countries', []))}"
test("GET /scenario-data/sbti/countries", t_sbti_countries)


# -- 11. SBTi stats ----------------------------------------------------------

def t_sbti_stats():
    r = requests.get(f"{BASE}/api/v1/scenario-data/sbti/stats", headers=headers)
    d = r.json()
    return (r.status_code == 200 and "total_companies" in d), f"HTTP {r.status_code}, data={d}"
test("GET /scenario-data/sbti/stats", t_sbti_stats)


# -- 12. No auth -> 401 ------------------------------------------------------

def t_noauth():
    r = requests.get(f"{BASE}/api/v1/scenario-data/stats")
    return r.status_code == 401, f"HTTP {r.status_code}"
test("GET /scenario-data/stats -> 401 without auth", t_noauth)


# -- Summary ------------------------------------------------------------------

print(f"\n{'='*60}")
passed = sum(1 for _, s, _ in results if s == "PASS")
total = len(results)
print(f"Session 10 Results: {passed}/{total} passed")
if passed < total:
    print("FAILURES:")
    for name, status, msg in results:
        if status == "FAIL":
            print(f"  - {name}: {msg}")
