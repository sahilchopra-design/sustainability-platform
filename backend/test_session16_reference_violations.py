"""
Session 16 Smoke Tests -- Reference Data (IRENA/CRREM/Grid EF) + Violations
Tests all endpoints from reference_data.py and violations.py

Run: python test_session16_reference_violations.py
Requires server running on http://127.0.0.1:8001
"""

import requests
import time
import sys

BASE = "http://127.0.0.1:8001"


def wait_for_server(max_wait=15):
    for _ in range(max_wait):
        try:
            r = requests.get(f"{BASE}/api/v1/ingestion/stats", timeout=2)
            if r.status_code in (200, 401, 403):
                return True
        except:
            pass
        time.sleep(1)
    return False


def setup_auth():
    """Create test user + session via DB, return Bearer token."""
    import sqlalchemy as sa
    engine = sa.create_engine("postgresql://postgres.kytzcbipsghprsqoalvi:KimiaAImpact2026@aws-1-us-east-2.pooler.supabase.com:5432/postgres")
    import uuid
    from datetime import datetime, timedelta, timezone
    user_id = str(uuid.uuid4())
    session_token = f"smoke16_{uuid.uuid4().hex[:16]}"
    with engine.begin() as conn:
        existing = conn.execute(sa.text("SELECT user_id FROM users_pg WHERE email='smoke16@test.local'")).first()
        if existing:
            user_id = str(existing[0])
            conn.execute(sa.text("""
                INSERT INTO user_sessions_pg (id, user_id, session_token, expires_at, created_at)
                VALUES (:sid, :uid, :token, :exp, now())
                ON CONFLICT (session_token) DO UPDATE SET expires_at = :exp
            """), {"sid": str(uuid.uuid4()), "uid": user_id, "token": session_token, "exp": datetime.now(timezone.utc) + timedelta(hours=2)})
        else:
            conn.execute(sa.text("""
                INSERT INTO users_pg (user_id, email, name, role, is_active, created_at)
                VALUES (:uid, 'smoke16@test.local', 'Session 16 Smoke Test', 'admin', true, now())
            """), {"uid": user_id})
            conn.execute(sa.text("""
                INSERT INTO user_sessions_pg (id, user_id, session_token, expires_at, created_at)
                VALUES (:sid, :uid, :token, :exp, now())
            """), {"sid": str(uuid.uuid4()), "uid": user_id, "token": session_token, "exp": datetime.now(timezone.utc) + timedelta(hours=2)})
    return session_token


# ── Test runner ──────────────────────────────────────────────────────────────

passed = 0
failed = 0
errors = []

def test(name, method, url, *, params=None, expect_status=200, expect_keys=None, allow_status=None):
    global passed, failed
    try:
        if method == "GET":
            r = requests.get(url, headers=HEADERS, params=params, timeout=10)
        elif method == "POST":
            r = requests.post(url, headers=HEADERS, json=params, timeout=10)
        else:
            raise ValueError(f"Unknown method {method}")

        ok_statuses = allow_status or [expect_status]
        if r.status_code not in ok_statuses:
            failed += 1
            errors.append(f"FAIL {name}: expected {ok_statuses}, got {r.status_code}")
            print(f"  FAIL  {name}  (status={r.status_code})")
            return

        if expect_keys and r.status_code == 200:
            body = r.json()
            missing = [k for k in expect_keys if k not in body]
            if missing:
                failed += 1
                errors.append(f"FAIL {name}: missing keys {missing} in {list(body.keys())[:10]}")
                print(f"  FAIL  {name}  (missing keys: {missing})")
                return

        passed += 1
        print(f"  PASS  {name}")
    except Exception as e:
        failed += 1
        errors.append(f"ERROR {name}: {e}")
        print(f"  ERR   {name}  ({e})")


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Session 16 Smoke Tests: Reference Data + Violations")
    print("=" * 60)

    if not wait_for_server():
        print("ERROR: Server not running on http://127.0.0.1:8001")
        sys.exit(1)
    print("Server is up.\n")

    token = setup_auth()
    HEADERS = {"Authorization": f"Bearer {token}"}
    print(f"Auth token created.\n")

    BR = f"{BASE}/api/v1/reference-data"
    BV = f"{BASE}/api/v1/violations"

    # ── Group 1: IRENA LCOE ──
    print("--- Group 1: IRENA LCOE ---")
    test("IRENA search (no filter)", "GET", f"{BR}/irena-lcoe", expect_keys=["records", "total"])
    test("IRENA search (tech=Solar)", "GET", f"{BR}/irena-lcoe", params={"technology": "Solar"}, expect_keys=["records"])
    test("IRENA search (year range)", "GET", f"{BR}/irena-lcoe", params={"year_start": 2018, "year_end": 2023}, expect_keys=["records"])
    test("IRENA technologies", "GET", f"{BR}/irena-lcoe/technologies", expect_keys=["technologies"])
    test("IRENA trend (Solar PV)", "GET", f"{BR}/irena-lcoe/trend/Solar PV", expect_keys=["technology", "trend"])
    test("IRENA trend (not found)", "GET", f"{BR}/irena-lcoe/trend/FakeEnergy", expect_status=404)

    # ── Group 2: CRREM Pathways ──
    print("\n--- Group 2: CRREM Pathways ---")
    test("CRREM search (no filter)", "GET", f"{BR}/crrem", expect_keys=["records", "total"])
    test("CRREM search (type=Office)", "GET", f"{BR}/crrem", params={"property_type": "Office"}, expect_keys=["records"])
    test("CRREM search (scenario=1.5C)", "GET", f"{BR}/crrem", params={"scenario": "1.5C"}, expect_keys=["records"])
    test("CRREM search (country=GBR)", "GET", f"{BR}/crrem", params={"country": "GBR"}, expect_keys=["records"])
    test("CRREM property types", "GET", f"{BR}/crrem/property-types", expect_keys=["property_types"])
    test("CRREM pathway (Office/1.5C/GBR)", "GET", f"{BR}/crrem/pathway", params={"property_type": "Office", "scenario": "1.5C", "country": "GBR"}, expect_keys=["pathway"])
    test("CRREM pathway (not found)", "GET", f"{BR}/crrem/pathway", params={"property_type": "Castle", "scenario": "5C"}, expect_status=404)

    # ── Group 3: Grid Emission Factors ──
    print("\n--- Group 3: Grid Emission Factors ---")
    test("Grid EF search (no filter)", "GET", f"{BR}/grid-ef", expect_keys=["records", "total"])
    test("Grid EF search (country=USA)", "GET", f"{BR}/grid-ef", params={"country": "USA"}, expect_keys=["records"])
    test("Grid EF search (year range)", "GET", f"{BR}/grid-ef", params={"year_start": 2020, "year_end": 2023}, expect_keys=["records"])
    test("Grid EF countries", "GET", f"{BR}/grid-ef/countries", expect_keys=["countries"])
    test("Grid EF country (GBR)", "GET", f"{BR}/grid-ef/GBR", expect_keys=["country", "records"])
    test("Grid EF country (not found)", "GET", f"{BR}/grid-ef/ZZZ", expect_status=404)

    # ── Group 4: Reference Stats ──
    print("\n--- Group 4: Reference Stats ---")
    test("Reference stats", "GET", f"{BR}/stats", expect_keys=["irena_lcoe", "crrem_pathways", "grid_emission_factors"])

    # ── Group 5: Violations Search ──
    print("\n--- Group 5: Violations Search ---")
    test("Violations search (no filter)", "GET", f"{BV}/search", expect_keys=["records", "total"])
    test("Violations search (type=Environmental)", "GET", f"{BV}/search", params={"violation_type": "Environmental"}, expect_keys=["records"])
    test("Violations search (agency=EPA)", "GET", f"{BV}/search", params={"agency": "EPA"}, expect_keys=["records"])
    test("Violations search (sector=Mining)", "GET", f"{BV}/search", params={"sector": "Mining"}, expect_keys=["records"])
    test("Violations search (min_penalty=1B)", "GET", f"{BV}/search", params={"min_penalty": 1000000000}, expect_keys=["records"])
    test("Violations search (company=BP)", "GET", f"{BV}/search", params={"company": "BP"}, expect_keys=["records"])
    test("Violations search (severity=Critical)", "GET", f"{BV}/search", params={"severity": "Critical"}, expect_keys=["records"])

    # ── Group 6: Violations Aggregations ──
    print("\n--- Group 6: Violations Aggregations ---")
    test("Violations companies", "GET", f"{BV}/companies", expect_keys=["companies"])
    test("Violations types", "GET", f"{BV}/types", expect_keys=["types"])
    test("Violations agencies", "GET", f"{BV}/agencies", expect_keys=["agencies"])
    test("Violations sectors", "GET", f"{BV}/sectors", expect_keys=["sectors"])
    test("Violations by company (BP)", "GET", f"{BV}/company/BP", expect_keys=["violations", "total"])
    test("Violations by company (not found)", "GET", f"{BV}/company/ZZZFAKECOMPANY", expect_status=404)

    # ── Group 7: Violations Stats ──
    print("\n--- Group 7: Violations Stats ---")
    test("Violations stats", "GET", f"{BV}/stats", expect_keys=["violations"])

    # ── Group 8: Ingester Registration ──
    print("\n--- Group 8: Ingester Registration ---")
    test("Ingesters list", "GET", f"{BASE}/api/v1/ingestion/ingesters", expect_keys=["ingesters", "total"])

    r = requests.get(f"{BASE}/api/v1/ingestion/ingesters", headers=HEADERS, timeout=10)
    if r.status_code == 200:
        source_ids = [i.get("source_id") for i in r.json().get("ingesters", [])]
        for sid in ["irena-lcoe-benchmarks", "violation-tracker"]:
            if sid in source_ids:
                passed += 1
                print(f"  PASS  {sid} ingester registered")
            else:
                failed += 1
                errors.append(f"FAIL {sid} ingester not in source_ids")
                print(f"  FAIL  {sid} ingester not in source_ids: {source_ids}")

        if len(source_ids) >= 12:
            passed += 1
            print(f"  PASS  Total ingesters: {len(source_ids)} >= 12")
        else:
            failed += 1
            errors.append(f"FAIL Expected >= 12 ingesters, got {len(source_ids)}")
            print(f"  FAIL  Expected >= 12 ingesters, got {len(source_ids)}")
    else:
        failed += 3
        print(f"  FAIL  Could not fetch ingesters list (status={r.status_code})")

    # ── Summary ──
    total = passed + failed
    print(f"\n{'=' * 60}")
    print(f"Session 16 Results: {passed}/{total} passed, {failed} failed")
    if errors:
        print("\nFailures:")
        for e in errors:
            print(f"  - {e}")
    print(f"{'=' * 60}")

    sys.exit(0 if failed == 0 else 1)
