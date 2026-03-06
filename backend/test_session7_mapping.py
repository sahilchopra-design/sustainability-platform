"""Smoke tests for Data Mapping API endpoints."""
import requests
import json
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

# Login to get token
def get_token():
    r = requests.post(f"{BASE}/api/auth/register", json={
        "email": "mappingtest@a2intel.com",
        "password": "SecurePass99",
        "name": "Mapping Test",
    })
    r = requests.post(f"{BASE}/api/auth/login", json={
        "email": "mappingtest@a2intel.com",
        "password": "SecurePass99",
    })
    if r.status_code == 200:
        return r.json().get("session_token")
    return None

token = get_token()
headers = {"Authorization": f"Bearer {token}"} if token else {}

# 1. List KPIs
def t_kpis():
    r = requests.get(f"{BASE}/api/v1/ingestion/kpis?limit=5", headers=headers)
    d = r.json()
    return r.status_code == 200 and "kpis" in d and len(d["kpis"]) > 0, f"HTTP {r.status_code}, total={d.get('total')}, returned={len(d.get('kpis', []))}"
test("GET /ingestion/kpis", t_kpis)

# 2. KPI categories
def t_kpi_cats():
    r = requests.get(f"{BASE}/api/v1/ingestion/kpi-categories", headers=headers)
    d = r.json()
    return r.status_code == 200 and "categories" in d and len(d["categories"]) > 0, f"HTTP {r.status_code}, categories={len(d.get('categories', []))}"
test("GET /ingestion/kpi-categories", t_kpi_cats)

# 3. KPI detail
def t_kpi_detail():
    r = requests.get(f"{BASE}/api/v1/ingestion/kpis?limit=1", headers=headers)
    kpis = r.json().get("kpis", [])
    if not kpis:
        return False, "No KPIs found"
    kid = kpis[0]["id"]
    r2 = requests.get(f"{BASE}/api/v1/ingestion/kpis/{kid}", headers=headers)
    d = r2.json()
    return r2.status_code == 200 and "mappings" in d, f"HTTP {r2.status_code}, name={d.get('name')}, mappings={len(d.get('mappings', []))}"
test("GET /ingestion/kpis/:id detail", t_kpi_detail)

# 4. Source fields (may be empty but endpoint works)
def t_source_fields():
    r = requests.get(f"{BASE}/api/v1/ingestion/source-fields?limit=5", headers=headers)
    d = r.json()
    return r.status_code == 200 and "fields" in d, f"HTTP {r.status_code}, total={d.get('total')}"
test("GET /ingestion/source-fields", t_source_fields)

# 5. List mappings (empty initially)
def t_mappings_list():
    r = requests.get(f"{BASE}/api/v1/ingestion/mappings", headers=headers)
    d = r.json()
    return r.status_code == 200 and "mappings" in d, f"HTTP {r.status_code}, total={d.get('total')}"
test("GET /ingestion/mappings", t_mappings_list)

# 6. Module coverage
def t_module_coverage():
    r = requests.get(f"{BASE}/api/v1/ingestion/module-coverage", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "modules" in d
            and len(d["modules"]) > 0), f"HTTP {r.status_code}, modules={len(d.get('modules', []))}, total_kpis={d.get('total_kpis')}"
test("GET /ingestion/module-coverage", t_module_coverage)

# 7. Cross-source (empty but endpoint works)
def t_cross_source():
    r = requests.get(f"{BASE}/api/v1/ingestion/cross-source", headers=headers)
    d = r.json()
    return r.status_code == 200 and "comparisons" in d, f"HTTP {r.status_code}, total={d.get('total')}"
test("GET /ingestion/cross-source", t_cross_source)

# 8. Create mapping (requires data_engineer role - our test user is viewer -> 403)
def t_create_mapping_forbidden():
    r = requests.get(f"{BASE}/api/v1/ingestion/kpis?limit=1", headers=headers)
    kpi = r.json()["kpis"][0]
    r2 = requests.get(f"{BASE}/api/v1/ingestion/sources?limit=1", headers=headers)
    source = r2.json()["sources"][0]
    r3 = requests.post(f"{BASE}/api/v1/ingestion/mappings",
                       json={"kpi_id": kpi["id"], "source_id": source["id"]},
                       headers=headers)
    return r3.status_code == 403, f"HTTP {r3.status_code}"
test("POST /ingestion/mappings 403 for viewer", t_create_mapping_forbidden)

# 9. Create source field (requires data_engineer - viewer gets 403)
def t_create_field_forbidden():
    r = requests.get(f"{BASE}/api/v1/ingestion/sources?limit=1", headers=headers)
    source = r.json()["sources"][0]
    r2 = requests.post(f"{BASE}/api/v1/ingestion/source-fields",
                       json={"source_id": source["id"], "field_name": "test_field"},
                       headers=headers)
    return r2.status_code == 403, f"HTTP {r2.status_code}"
test("POST /ingestion/source-fields 403 for viewer", t_create_field_forbidden)

# 10. KPI filter by module
def t_kpi_module_filter():
    r = requests.get(f"{BASE}/api/v1/ingestion/kpis?module=ecl&limit=5", headers=headers)
    d = r.json()
    return r.status_code == 200 and "kpis" in d, f"HTTP {r.status_code}, total={d.get('total')}"
test("GET /ingestion/kpis?module=ecl filter", t_kpi_module_filter)

# 11. No auth returns 401
def t_kpis_noauth():
    r = requests.get(f"{BASE}/api/v1/ingestion/kpis")
    return r.status_code == 401, f"HTTP {r.status_code}"
test("GET /ingestion/kpis 401 without auth", t_kpis_noauth)

# 12. Delete mapping 404 for non-existent
def t_delete_mapping_notfound():
    # This will be 403 since viewer can't delete, but let's test the endpoint exists
    r = requests.delete(f"{BASE}/api/v1/ingestion/mappings/nonexistent", headers=headers)
    # Viewer -> 403 (role check before 404)
    return r.status_code == 403, f"HTTP {r.status_code}"
test("DELETE /ingestion/mappings 403 for viewer", t_delete_mapping_notfound)

# Summary
print(f"\n{'='*50}")
passed = sum(1 for _, s, _ in results if s == "PASS")
total = len(results)
print(f"Results: {passed}/{total} passed")
if passed < total:
    print("FAILURES:")
    for name, status, msg in results:
        if status == "FAIL":
            print(f"  - {name}: {msg}")
