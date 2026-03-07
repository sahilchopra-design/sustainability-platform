"""
Session 17 Smoke Tests -- GDELT Events + GKG + Controversy Scores
Tests all endpoints from gdelt_controversy.py

Run: python test_session17_gdelt_controversy.py
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
    session_token = f"smoke17_{uuid.uuid4().hex[:16]}"
    with engine.begin() as conn:
        existing = conn.execute(sa.text("SELECT user_id FROM users_pg WHERE email='smoke17@test.local'")).first()
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
                VALUES (:uid, 'smoke17@test.local', 'Session 17 Smoke Test', 'admin', true, now())
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
    print("Session 17 Smoke Tests: GDELT Events + GKG + Controversy")
    print("=" * 60)

    if not wait_for_server():
        print("ERROR: Server not running on http://127.0.0.1:8001")
        sys.exit(1)
    print("Server is up.\n")

    token = setup_auth()
    HEADERS = {"Authorization": f"Bearer {token}"}
    print(f"Auth token created.\n")

    BG = f"{BASE}/api/v1/gdelt"

    # ── Group 1: GDELT Events Search ──
    print("--- Group 1: GDELT Events Search ---")
    test("Events search (no filter)", "GET", f"{BG}/events/search", expect_keys=["records", "total"])
    test("Events search (actor=Shell)", "GET", f"{BG}/events/search", params={"actor": "Shell"}, expect_keys=["records"])
    test("Events search (country=USA)", "GET", f"{BG}/events/search", params={"country": "USA"}, expect_keys=["records"])
    test("Events search (quad_class=3)", "GET", f"{BG}/events/search", params={"quad_class": 3}, expect_keys=["records"])
    test("Events search (min_mentions=200)", "GET", f"{BG}/events/search", params={"min_mentions": 200}, expect_keys=["records"])
    test("Events search (entity=BP)", "GET", f"{BG}/events/search", params={"entity": "BP"}, expect_keys=["records"])
    test("Events search (year=2023)", "GET", f"{BG}/events/search", params={"year": 2023}, expect_keys=["records"])

    # ── Group 2: GDELT Events Aggregations ──
    print("\n--- Group 2: GDELT Events Aggregations ---")
    test("Events top actors", "GET", f"{BG}/events/actors", expect_keys=["actors"])
    test("Events timeline (month)", "GET", f"{BG}/events/timeline", expect_keys=["timeline"])
    test("Events timeline (entity)", "GET", f"{BG}/events/timeline", params={"entity": "Shell"}, expect_keys=["timeline"])
    test("Events timeline (year)", "GET", f"{BG}/events/timeline", params={"granularity": "year"}, expect_keys=["timeline"])
    test("Events countries", "GET", f"{BG}/events/countries", expect_keys=["countries"])
    test("Events stats", "GET", f"{BG}/events/stats", expect_keys=["events"])

    # ── Group 3: GDELT GKG ──
    print("\n--- Group 3: GDELT GKG ---")
    test("GKG search (no filter)", "GET", f"{BG}/gkg/search", expect_keys=["records", "total"])
    test("GKG search (entity=Meta)", "GET", f"{BG}/gkg/search", params={"entity": "Meta"}, expect_keys=["records"])
    test("GKG search (esg_category=E)", "GET", f"{BG}/gkg/search", params={"esg_category": "E"}, expect_keys=["records"])
    test("GKG search (controversy_only)", "GET", f"{BG}/gkg/search", params={"controversy_only": True}, expect_keys=["records"])
    test("GKG themes", "GET", f"{BG}/gkg/themes", expect_keys=["themes"])

    # ── Group 4: Controversy Scores ──
    print("\n--- Group 4: Controversy Scores ---")
    test("Controversy search (no filter)", "GET", f"{BG}/controversy/search", expect_keys=["records", "total"])
    test("Controversy search (sector=Energy)", "GET", f"{BG}/controversy/search", params={"sector": "Energy"}, expect_keys=["records"])
    test("Controversy search (severity=Critical)", "GET", f"{BG}/controversy/search", params={"severity": "Critical"}, expect_keys=["records"])
    test("Controversy search (min_score=50)", "GET", f"{BG}/controversy/search", params={"min_score": 50}, expect_keys=["records"])
    test("Controversy entity detail (Shell)", "GET", f"{BG}/controversy/entity/Shell", expect_keys=["entity", "controversy", "recent_events"])
    test("Controversy entity (not found)", "GET", f"{BG}/controversy/entity/ZZZFAKECOMPANY", expect_status=404)
    test("Controversy rankings", "GET", f"{BG}/controversy/rankings", expect_keys=["rankings"])
    test("Controversy rankings (sector)", "GET", f"{BG}/controversy/rankings", params={"sector": "Energy"}, expect_keys=["rankings"])
    test("Controversy stats", "GET", f"{BG}/controversy/stats", expect_keys=["controversy"])

    # ── Group 5: Ingester Registration ──
    print("\n--- Group 5: Ingester Registration ---")
    test("Ingesters list", "GET", f"{BASE}/api/v1/ingestion/ingesters", expect_keys=["ingesters", "total"])

    r = requests.get(f"{BASE}/api/v1/ingestion/ingesters", headers=HEADERS, timeout=10)
    if r.status_code == 200:
        source_ids = [i.get("source_id") for i in r.json().get("ingesters", [])]
        if "gdelt-events" in source_ids:
            passed += 1
            print(f"  PASS  gdelt-events ingester registered")
        else:
            failed += 1
            errors.append(f"FAIL gdelt-events ingester not in source_ids")
            print(f"  FAIL  gdelt-events ingester not in source_ids: {source_ids}")

        if len(source_ids) >= 13:
            passed += 1
            print(f"  PASS  Total ingesters: {len(source_ids)} >= 13")
        else:
            failed += 1
            errors.append(f"FAIL Expected >= 13 ingesters, got {len(source_ids)}")
            print(f"  FAIL  Expected >= 13 ingesters, got {len(source_ids)}")
    else:
        failed += 2
        print(f"  FAIL  Could not fetch ingesters list (status={r.status_code})")

    # ── Summary ──
    total = passed + failed
    print(f"\n{'=' * 60}")
    print(f"Session 17 Results: {passed}/{total} passed, {failed} failed")
    if errors:
        print("\nFailures:")
        for e in errors:
            print(f"  - {e}")
    print(f"{'=' * 60}")

    sys.exit(0 if failed == 0 else 1)
