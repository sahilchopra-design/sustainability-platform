"""Smoke test for Session 7: Ingestion Framework wiring."""
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

# Login to get token (reuse session2 user or register)
def get_token():
    r = requests.post(f"{BASE}/api/auth/register", json={
        "email": "session7test@a2intel.com",
        "password": "SecurePass99",
        "name": "Session7 Test",
    })
    if r.status_code not in (200, 400):
        return None
    r = requests.post(f"{BASE}/api/auth/login", json={
        "email": "session7test@a2intel.com",
        "password": "SecurePass99",
    })
    if r.status_code == 200:
        return r.json().get("session_token")
    return None

token = get_token()
headers = {"Authorization": f"Bearer {token}"} if token else {}

# 1. Health
def t_health():
    r = requests.get(f"{BASE}/api/health")
    return r.status_code == 200, f"HTTP {r.status_code}"
test("Health check", t_health)

# 2. Login successful
def t_login():
    return token is not None, f"token={'present' if token else 'missing'}"
test("Login for auth", t_login)

# 3. Ingestion ingesters list (requires auth)
def t_ingesters():
    r = requests.get(f"{BASE}/api/v1/ingestion/ingesters", headers=headers)
    d = r.json()
    return r.status_code == 200 and "ingesters" in d, f"HTTP {r.status_code}, total={d.get('total')}"
test("GET /ingestion/ingesters", t_ingesters)

# 4. Ingestion stats
def t_stats():
    r = requests.get(f"{BASE}/api/v1/ingestion/stats", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "total_sources" in d
            and d["total_sources"] > 0), f"HTTP {r.status_code}, sources={d.get('total_sources')}"
test("GET /ingestion/stats (103 sources)", t_stats)

# 5. Ingestion sources list
def t_sources():
    r = requests.get(f"{BASE}/api/v1/ingestion/sources?limit=5", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "sources" in d
            and len(d["sources"]) > 0), f"HTTP {r.status_code}, total={d.get('total')}, returned={len(d.get('sources', []))}"
test("GET /ingestion/sources (list)", t_sources)

# 6. Ingestion sources detail (pick first from list)
def t_source_detail():
    r = requests.get(f"{BASE}/api/v1/ingestion/sources?limit=1", headers=headers)
    sources = r.json().get("sources", [])
    if not sources:
        return False, "No sources found"
    sid = sources[0]["id"]
    r2 = requests.get(f"{BASE}/api/v1/ingestion/sources/{sid}", headers=headers)
    d = r2.json()
    return r2.status_code == 200 and "name" in d, f"HTTP {r2.status_code}, name={d.get('name')}"
test("GET /ingestion/sources/:id (detail)", t_source_detail)

# 7. Ingestion jobs list (should be empty but endpoint works)
def t_jobs():
    r = requests.get(f"{BASE}/api/v1/ingestion/jobs", headers=headers)
    d = r.json()
    return r.status_code == 200 and "jobs" in d, f"HTTP {r.status_code}, total={d.get('total')}"
test("GET /ingestion/jobs (history)", t_jobs)

# 8. Running jobs
def t_running():
    r = requests.get(f"{BASE}/api/v1/ingestion/running", headers=headers)
    d = r.json()
    return r.status_code == 200 and "running" in d, f"HTTP {r.status_code}, count={d.get('count')}"
test("GET /ingestion/running", t_running)

# 9. Scheduler status
def t_scheduler():
    r = requests.get(f"{BASE}/api/v1/ingestion/scheduler", headers=headers)
    d = r.json()
    return r.status_code == 200 and "available" in d, f"HTTP {r.status_code}, available={d.get('available')}, running={d.get('running')}"
test("GET /ingestion/scheduler", t_scheduler)

# 10. Trigger requires admin/data_engineer role (viewer gets 403)
def t_trigger_forbidden():
    r = requests.post(f"{BASE}/api/v1/ingestion/trigger",
                      json={"source_id": "test", "async_mode": False},
                      headers=headers)
    return r.status_code == 403, f"HTTP {r.status_code}"
test("POST /ingestion/trigger 403 for viewer", t_trigger_forbidden)

# 11. Ingestion ingesters list - no auth returns 401
def t_ingesters_noauth():
    r = requests.get(f"{BASE}/api/v1/ingestion/ingesters")
    return r.status_code == 401, f"HTTP {r.status_code}"
test("GET /ingestion/ingesters 401 without auth", t_ingesters_noauth)

# 12. Source sync config update requires admin (viewer gets 403)
def t_sync_config_forbidden():
    r = requests.get(f"{BASE}/api/v1/ingestion/sources?limit=1", headers=headers)
    sources = r.json().get("sources", [])
    if not sources:
        return False, "No sources"
    sid = sources[0]["id"]
    r2 = requests.patch(f"{BASE}/api/v1/ingestion/sources/{sid}/sync-config",
                        params={"sync_enabled": True},
                        headers=headers)
    return r2.status_code == 403, f"HTTP {r2.status_code}"
test("PATCH sync-config 403 for viewer", t_sync_config_forbidden)

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
