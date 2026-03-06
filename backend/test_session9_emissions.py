"""Smoke tests for Session 9 -- Emissions Ingesters (Climate TRACE + OWID)."""
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

token = get_token("emissions_test@a2intel.com", "SecurePass99", "Emissions Tester")
headers = {"Authorization": f"Bearer {token}"} if token else {}


# -- 1. Ingesters registered --------------------------------------------------

def t_ingesters():
    r = requests.get(f"{BASE}/api/v1/ingestion/ingesters", headers=headers)
    d = r.json()
    names = [i.get("display_name", "") for i in d.get("ingesters", [])]
    has_ct = any("Climate TRACE" in n for n in names)
    has_owid = any("OWID" in n for n in names)
    return (r.status_code == 200 and has_ct and has_owid,
            f"HTTP {r.status_code}, ingesters={names}")
test("GET /ingestion/ingesters (CT + OWID registered)", t_ingesters)


# -- 2. Emissions stats -------------------------------------------------------

def t_stats():
    r = requests.get(f"{BASE}/api/v1/emissions/stats", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "climate_trace" in d
            and "owid" in d), f"HTTP {r.status_code}, data={d}"
test("GET /emissions/stats", t_stats)


# -- 3. Climate TRACE search (empty is OK) ------------------------------------

def t_ct_search():
    r = requests.get(f"{BASE}/api/v1/emissions/climate-trace?limit=5", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "total" in d
            and "records" in d), f"HTTP {r.status_code}, total={d.get('total')}"
test("GET /emissions/climate-trace", t_ct_search)


# -- 4. Climate TRACE with country filter -------------------------------------

def t_ct_country():
    r = requests.get(f"{BASE}/api/v1/emissions/climate-trace?country=USA&limit=5", headers=headers)
    d = r.json()
    return (r.status_code == 200 and "records" in d), f"HTTP {r.status_code}, total={d.get('total')}"
test("GET /emissions/climate-trace?country=USA", t_ct_country)


# -- 5. Climate TRACE sectors -------------------------------------------------

def t_ct_sectors():
    r = requests.get(f"{BASE}/api/v1/emissions/climate-trace/sectors", headers=headers)
    d = r.json()
    return (r.status_code == 200 and "sectors" in d), f"HTTP {r.status_code}, sectors={len(d.get('sectors', []))}"
test("GET /emissions/climate-trace/sectors", t_ct_sectors)


# -- 6. Climate TRACE countries -----------------------------------------------

def t_ct_countries():
    r = requests.get(f"{BASE}/api/v1/emissions/climate-trace/countries", headers=headers)
    d = r.json()
    return (r.status_code == 200 and "countries" in d), f"HTTP {r.status_code}, countries={len(d.get('countries', []))}"
test("GET /emissions/climate-trace/countries", t_ct_countries)


# -- 7. OWID search (empty is OK) --------------------------------------------

def t_owid_search():
    r = requests.get(f"{BASE}/api/v1/emissions/owid?limit=5", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "total" in d
            and "records" in d), f"HTTP {r.status_code}, total={d.get('total')}"
test("GET /emissions/owid", t_owid_search)


# -- 8. OWID countries --------------------------------------------------------

def t_owid_countries():
    r = requests.get(f"{BASE}/api/v1/emissions/owid/countries", headers=headers)
    d = r.json()
    return (r.status_code == 200 and "countries" in d), f"HTTP {r.status_code}, countries={len(d.get('countries', []))}"
test("GET /emissions/owid/countries", t_owid_countries)


# -- 9. OWID country series (404 for non-existent) ---------------------------

def t_owid_404():
    r = requests.get(f"{BASE}/api/v1/emissions/owid/ZZZ", headers=headers)
    return r.status_code == 404, f"HTTP {r.status_code}"
test("GET /emissions/owid/ZZZ -> 404", t_owid_404)


# -- 10. No auth -> 401 -------------------------------------------------------

def t_noauth():
    r = requests.get(f"{BASE}/api/v1/emissions/stats")
    return r.status_code == 401, f"HTTP {r.status_code}"
test("GET /emissions/stats -> 401 without auth", t_noauth)


# -- Summary ------------------------------------------------------------------

print(f"\n{'='*60}")
passed = sum(1 for _, s, _ in results if s == "PASS")
total = len(results)
print(f"Session 9 Results: {passed}/{total} passed")
if passed < total:
    print("FAILURES:")
    for name, status, msg in results:
        if status == "FAIL":
            print(f"  - {name}: {msg}")
