"""Smoke tests for Session 8 — Entity Resolution (GLEIF + Sanctions + Screening)."""
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


# ── Auth setup ───────────────────────────────────────────────────────────

def get_token(email, password, name, role="viewer"):
    """Register + login, return token."""
    requests.post(f"{BASE}/api/auth/register", json={
        "email": email, "password": password, "name": name,
    })
    r = requests.post(f"{BASE}/api/auth/login", json={
        "email": email, "password": password,
    })
    if r.status_code == 200:
        return r.json().get("session_token")
    return None


viewer_token = get_token("er_viewer@a2intel.com", "SecurePass99", "ER Viewer")
viewer_headers = {"Authorization": f"Bearer {viewer_token}"} if viewer_token else {}

# For compliance-level operations we need a compliance user
# (registration defaults to viewer; we test 403 for viewer on screen endpoint)


# ── 1. Ingesters registration check ─────────────────────────────────────

def t_ingesters_list():
    r = requests.get(f"{BASE}/api/v1/ingestion/ingesters", headers=viewer_headers)
    d = r.json()
    names = [i.get("display_name") or i.get("name", "") for i in d.get("ingesters", [])]
    has_gleif = any("GLEIF" in n for n in names)
    has_sanctions = any("Sanction" in n or "OFAC" in n for n in names)
    return (r.status_code == 200 and has_gleif and has_sanctions,
            f"HTTP {r.status_code}, ingesters={names}")
test("GET /ingestion/ingesters (GLEIF + Sanctions registered)", t_ingesters_list)


# ── 2. Entity Resolution Stats ──────────────────────────────────────────

def t_stats():
    r = requests.get(f"{BASE}/api/v1/entity-resolution/stats", headers=viewer_headers)
    d = r.json()
    return (r.status_code == 200
            and "lei_records" in d
            and "sanctions_entities" in d
            and "screening_results" in d), f"HTTP {r.status_code}, data={d}"
test("GET /entity-resolution/stats", t_stats)


# ── 3. LEI search (empty DB is OK — endpoint must work) ─────────────────

def t_lei_search():
    r = requests.get(f"{BASE}/api/v1/entity-resolution/lei?limit=5", headers=viewer_headers)
    d = r.json()
    return (r.status_code == 200
            and "total" in d
            and "records" in d), f"HTTP {r.status_code}, total={d.get('total')}"
test("GET /entity-resolution/lei (search)", t_lei_search)


# ── 4. LEI search with query ────────────────────────────────────────────

def t_lei_search_q():
    r = requests.get(f"{BASE}/api/v1/entity-resolution/lei?q=Deutsche&limit=5", headers=viewer_headers)
    d = r.json()
    return (r.status_code == 200 and "records" in d), f"HTTP {r.status_code}, total={d.get('total')}"
test("GET /entity-resolution/lei?q=Deutsche", t_lei_search_q)


# ── 5. LEI 404 for non-existent ─────────────────────────────────────────

def t_lei_404():
    r = requests.get(f"{BASE}/api/v1/entity-resolution/lei/XXXXXXXXXXXXXXXXXXXX", headers=viewer_headers)
    return r.status_code == 404, f"HTTP {r.status_code}"
test("GET /entity-resolution/lei/{bad} -> 404", t_lei_404)


# ── 6. Sanctions search ─────────────────────────────────────────────────

def t_sanctions_search():
    r = requests.get(f"{BASE}/api/v1/entity-resolution/sanctions?limit=5", headers=viewer_headers)
    d = r.json()
    return (r.status_code == 200
            and "total" in d
            and "records" in d), f"HTTP {r.status_code}, total={d.get('total')}"
test("GET /entity-resolution/sanctions (search)", t_sanctions_search)


# ── 7. Sanctions 404 ────────────────────────────────────────────────────

def t_sanctions_404():
    r = requests.get(f"{BASE}/api/v1/entity-resolution/sanctions/nonexistent-id", headers=viewer_headers)
    return r.status_code == 404, f"HTTP {r.status_code}"
test("GET /entity-resolution/sanctions/{bad} -> 404", t_sanctions_404)


# ── 8. Screen entity — 403 for viewer (needs compliance) ────────────────

def t_screen_403():
    r = requests.post(f"{BASE}/api/v1/entity-resolution/screen",
                      json={"entity_name": "Test Corp"},
                      headers=viewer_headers)
    return r.status_code == 403, f"HTTP {r.status_code}"
test("POST /entity-resolution/screen -> 403 for viewer", t_screen_403)


# ── 9. Screening results list ───────────────────────────────────────────

def t_screening_results():
    r = requests.get(f"{BASE}/api/v1/entity-resolution/screening-results?limit=5", headers=viewer_headers)
    d = r.json()
    return (r.status_code == 200
            and "total" in d
            and "results" in d), f"HTTP {r.status_code}, total={d.get('total')}"
test("GET /entity-resolution/screening-results", t_screening_results)


# ── 10. Screening result 404 ────────────────────────────────────────────

def t_screening_404():
    r = requests.get(f"{BASE}/api/v1/entity-resolution/screening-results/nonexistent", headers=viewer_headers)
    return r.status_code == 404, f"HTTP {r.status_code}"
test("GET /entity-resolution/screening-results/{bad} -> 404", t_screening_404)


# ── 11. Review endpoint — 403 for viewer ────────────────────────────────

def t_review_403():
    r = requests.put(f"{BASE}/api/v1/entity-resolution/screening-results/some-id/review",
                     json={"status": "confirmed_match"},
                     headers=viewer_headers)
    return r.status_code == 403, f"HTTP {r.status_code}"
test("PUT /screening-results/{id}/review -> 403 for viewer", t_review_403)


# ── 12. No auth -> 401 ───────────────────────────────────────────────────

def t_noauth():
    r = requests.get(f"{BASE}/api/v1/entity-resolution/stats")
    return r.status_code == 401, f"HTTP {r.status_code}"
test("GET /entity-resolution/stats -> 401 without auth", t_noauth)


# ── Summary ──────────────────────────────────────────────────────────────

print(f"\n{'='*60}")
passed = sum(1 for _, s, _ in results if s == "PASS")
total = len(results)
print(f"Session 8 Results: {passed}/{total} passed")
if passed < total:
    print("FAILURES:")
    for name, status, msg in results:
        if status == "FAIL":
            print(f"  - {name}: {msg}")
