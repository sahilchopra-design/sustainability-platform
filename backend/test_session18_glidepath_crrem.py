"""
Session 18 Smoke Tests -- NZBA Glidepath + CRREM Pathway Wiring (F4 + F5)
Tests glidepath_serve.py and glidepath.py endpoints for live-data wiring.

Run: python test_session18_glidepath_crrem.py
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
    session_token = f"smoke18_{uuid.uuid4().hex[:16]}"
    with engine.begin() as conn:
        existing = conn.execute(sa.text("SELECT user_id FROM users_pg WHERE email='smoke18@test.local'")).first()
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
                VALUES (:uid, 'smoke18@test.local', 'Session 18 Smoke Test', 'admin', true, now())
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

def test(name, method, url, *, params=None, expect_status=200, expect_keys=None, allow_status=None, check_fn=None):
    global passed, failed
    try:
        if method == "GET":
            r = requests.get(url, headers=HEADERS, params=params, timeout=15)
        elif method == "POST":
            r = requests.post(url, headers=HEADERS, json=params, timeout=15)
        else:
            raise ValueError(f"Unknown method {method}")

        ok_statuses = allow_status or [expect_status]
        if r.status_code not in ok_statuses:
            failed += 1
            errors.append(f"FAIL {name}: expected {ok_statuses}, got {r.status_code}")
            print(f"  FAIL  {name}  (status={r.status_code})")
            return None

        if expect_keys and r.status_code == 200:
            body = r.json()
            missing = [k for k in expect_keys if k not in body]
            if missing:
                failed += 1
                errors.append(f"FAIL {name}: missing keys {missing} in {list(body.keys())[:10]}")
                print(f"  FAIL  {name}  (missing keys: {missing})")
                return None

        if check_fn and r.status_code == 200:
            body = r.json()
            result = check_fn(body)
            if result is not True:
                failed += 1
                errors.append(f"FAIL {name}: {result}")
                print(f"  FAIL  {name}  ({result})")
                return None

        passed += 1
        print(f"  PASS  {name}")
        return r.json() if r.status_code == 200 else None
    except Exception as e:
        failed += 1
        errors.append(f"ERROR {name}: {e}")
        print(f"  ERR   {name}  ({e})")
        return None


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Session 18 Smoke Tests: NZBA Glidepath + CRREM Pathway Wiring")
    print("=" * 60)

    if not wait_for_server():
        print("ERROR: Server not running on http://127.0.0.1:8001")
        sys.exit(1)
    print("Server is up.\n")

    token = setup_auth()
    HEADERS = {"Authorization": f"Bearer {token}"}
    print(f"Auth token created.\n")

    GP = f"{BASE}/api/v1/glidepath"
    GPS = f"{BASE}/api/v1/glidepaths"

    # ── Group 1: NZBA Glidepath (glidepath.py) ──
    print("--- Group 1: NZBA Glidepath (glidepath.py) ---")
    test("NZBA sectors list", "GET", f"{GP}/sectors",
         expect_keys=["sectors", "source"])
    test("NZBA glidepath Power", "GET", f"{GP}/nzba/Power",
         expect_keys=["sector", "glidepath"])
    test("NZBA glidepath Oil & Gas", "GET", f"{GP}/nzba/Oil %26 Gas",
         expect_keys=["sector", "glidepath"])
    test("NZBA glidepath Steel", "GET", f"{GP}/nzba/Steel",
         expect_keys=["sector", "glidepath"])

    # Check source label updated (no longer says "connect Data Hub")
    test("NZBA source label updated", "GET", f"{GP}/sectors",
         check_fn=lambda b: True if "connect Data Hub" not in b.get("source", "") else "Source still has stale 'connect Data Hub' text")

    # ── Group 2: CRREM via glidepath.py ──
    print("\n--- Group 2: CRREM via glidepath.py ---")
    test("CRREM pathway Office", "GET", f"{GP}/crrem/Office",
         expect_keys=["asset_type", "pathway", "source"])
    test("CRREM pathway Retail", "GET", f"{GP}/crrem/Retail",
         expect_keys=["asset_type", "pathway"])

    # Check CRREM source includes live or fallback
    test("CRREM pathway has source", "GET", f"{GP}/crrem/Office",
         check_fn=lambda b: True if b.get("source") else "Missing source label")

    # ── Group 3: Glidepaths Serve (glidepath_serve.py) ──
    print("\n--- Group 3: Glidepaths Serve (glidepath_serve.py) ---")
    test("NZE glidepath Energy", "GET", f"{GPS}/nze/Energy",
         expect_keys=["sector", "glidepath_series"])
    test("NZE glidepath Utilities", "GET", f"{GPS}/nze/Utilities",
         expect_keys=["sector", "glidepath_series"])

    # CRREM serve endpoint -- now DB-first with fallback
    test("CRREM serve office/DE", "GET", f"{GPS}/crrem/DE/office",
         expect_keys=["country", "asset_type", "pathway_series", "source"])
    test("CRREM serve office/GB", "GET", f"{GPS}/crrem/GB/office",
         expect_keys=["country", "asset_type", "pathway_series"])
    test("CRREM serve retail/US", "GET", f"{GPS}/crrem/US/retail",
         expect_keys=["pathway_series"])
    test("CRREM serve residential/DE", "GET", f"{GPS}/crrem/DE/residential",
         expect_keys=["pathway_series"])

    # CRREM serve returns pathway with data points
    test("CRREM serve has data points", "GET", f"{GPS}/crrem/DE/office",
         check_fn=lambda b: True if b.get("data_points", 0) > 0 else f"Expected data_points > 0, got {b.get('data_points')}")

    # CRREM serve returns new source field
    test("CRREM serve has source field", "GET", f"{GPS}/crrem/DE/office",
         check_fn=lambda b: True if "source" in b else "Missing 'source' field")

    # CRREM serve returns scenario field
    test("CRREM serve has scenario field", "GET", f"{GPS}/crrem/DE/office",
         check_fn=lambda b: True if "scenario" in b else "Missing 'scenario' field")

    # ── Group 4: Sectors + Stats ──
    print("\n--- Group 4: Sectors + Stats ---")
    test("Glidepaths sectors list", "GET", f"{GPS}/sectors",
         expect_keys=["ngfs_sectors", "crrem_asset_types", "crrem_countries"])
    test("Glidepaths sectors has crrem_source", "GET", f"{GPS}/sectors",
         check_fn=lambda b: True if "crrem_source" in b else "Missing crrem_source")

    test("Glidepaths stats", "GET", f"{GPS}/stats",
         expect_keys=["ngfs_emission_records", "crrem_asset_types", "crrem_countries"])
    test("Stats has crrem_records", "GET", f"{GPS}/stats",
         check_fn=lambda b: True if "crrem_records" in b else "Missing crrem_records")
    test("Stats has crrem_source", "GET", f"{GPS}/stats",
         check_fn=lambda b: True if "crrem_source" in b else "Missing crrem_source")

    # ── Group 5: CRREM Live Data Verification ──
    print("\n--- Group 5: CRREM Live Data Verification ---")
    # Verify live data is served (source should contain "live" not "reference")
    test("CRREM live data Office/DE", "GET", f"{GPS}/crrem/DE/office",
         check_fn=lambda b: True if "live" in b.get("source", "") else f"Expected live source, got: {b.get('source')}")
    test("CRREM live data Office/GB", "GET", f"{GPS}/crrem/GB/office",
         check_fn=lambda b: True if "live" in b.get("source", "") else f"Expected live source, got: {b.get('source')}")
    test("CRREM live data Retail/US", "GET", f"{GPS}/crrem/US/retail",
         check_fn=lambda b: True if "live" in b.get("source", "") else f"Expected live source, got: {b.get('source')}")
    test("CRREM live data has >5 points", "GET", f"{GPS}/crrem/DE/office",
         check_fn=lambda b: True if b.get("data_points", 0) > 5 else f"Expected >5 data points, got {b.get('data_points')}")

    # ── Group 6: Edge Cases ──
    print("\n--- Group 6: Edge Cases ---")
    test("CRREM serve bad asset type", "GET", f"{GPS}/crrem/DE/nonexistent",
         expect_status=400)
    # NZBA has an "Other" fallback sector, so unknown sectors return 200 with Other glidepath
    test("NZBA unknown sector returns Other fallback", "GET", f"{GP}/nzba/ZZZFAKE",
         expect_keys=["sector", "glidepath"],
         check_fn=lambda b: True if len(b.get("glidepath", [])) > 0 else "Expected fallback glidepath")

    # ── Summary ──
    total = passed + failed
    print(f"\n{'=' * 60}")
    print(f"Session 18 Results: {passed}/{total} passed, {failed} failed")
    if errors:
        print("\nFailures:")
        for e in errors:
            print(f"  - {e}")
    print(f"{'=' * 60}")

    sys.exit(0 if failed == 0 else 1)
