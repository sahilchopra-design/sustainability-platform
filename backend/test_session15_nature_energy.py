"""
Session 15 Smoke Tests -- Nature Data (WDPA/GFW) + Energy Data (GEM Coal)
Tests all endpoints from nature_data.py and energy_data.py

Run: python test_session15_nature_energy.py
Requires server running on http://127.0.0.1:8001
"""

import requests
import time
import sys

BASE = "http://127.0.0.1:8001"

# Wait for server
def wait_for_server(max_wait=15):
    for _ in range(max_wait):
        try:
            r = requests.get(f"{BASE}/api/v1/ingestion/stats", timeout=2)
            # Any response means server is up (even 401)
            if r.status_code in (200, 401, 403):
                return True
        except:
            pass
        time.sleep(1)
    return False


# Create a session token for testing
def setup_auth():
    """Create test user + session via DB, return Bearer token."""
    import sqlalchemy as sa
    engine = sa.create_engine("postgresql://postgres.kytzcbipsghprsqoalvi:KimiaAImpact2026@aws-1-us-east-2.pooler.supabase.com:5432/postgres")
    import uuid
    from datetime import datetime, timedelta, timezone
    user_id = str(uuid.uuid4())
    session_token = f"smoke15_{uuid.uuid4().hex[:16]}"
    with engine.begin() as conn:
        # Check if test user already exists (table: users_pg, PK: user_id)
        existing = conn.execute(sa.text("SELECT user_id FROM users_pg WHERE email='smoke15@test.local'")).first()
        if existing:
            user_id = str(existing[0])
            # Upsert session
            conn.execute(sa.text("""
                INSERT INTO user_sessions_pg (id, user_id, session_token, expires_at, created_at)
                VALUES (:sid, :uid, :token, :exp, now())
                ON CONFLICT (session_token) DO UPDATE SET expires_at = :exp
            """), {"sid": str(uuid.uuid4()), "uid": user_id, "token": session_token, "exp": datetime.now(timezone.utc) + timedelta(hours=2)})
        else:
            conn.execute(sa.text("""
                INSERT INTO users_pg (user_id, email, name, role, is_active, created_at)
                VALUES (:uid, 'smoke15@test.local', 'Session 15 Smoke Test', 'admin', true, now())
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
    print("Session 15 Smoke Tests: Nature Data + Energy Data")
    print("=" * 60)

    if not wait_for_server():
        print("ERROR: Server not running on http://127.0.0.1:8001")
        sys.exit(1)
    print("Server is up.\n")

    token = setup_auth()
    HEADERS = {"Authorization": f"Bearer {token}"}
    print(f"Auth token created.\n")

    BN = f"{BASE}/api/v1/nature-data"
    BE = f"{BASE}/api/v1/energy-data"

    # ── Group 1: WDPA Protected Areas ──
    print("--- Group 1: WDPA Protected Areas ---")
    test("WDPA search (no filter)", "GET", f"{BN}/wdpa", expect_keys=["records", "total"])
    test("WDPA search (country=AUS)", "GET", f"{BN}/wdpa", params={"country": "AUS"}, expect_keys=["records"])
    test("WDPA search (iucn_cat=II)", "GET", f"{BN}/wdpa", params={"iucn_cat": "II"}, expect_keys=["records"])
    test("WDPA search (name search)", "GET", f"{BN}/wdpa", params={"search": "Park"}, expect_keys=["records"])
    test("WDPA countries", "GET", f"{BN}/wdpa/countries", expect_keys=["countries"])
    test("WDPA nearby (lat/lng)", "GET", f"{BN}/wdpa/nearby", params={"lat": -18.0, "lng": 147.0, "radius_km": 200}, expect_keys=["results", "center"])
    test("WDPA by ID (not found)", "GET", f"{BN}/wdpa/999999999", expect_status=404)
    test("WDPA pagination (limit=5)", "GET", f"{BN}/wdpa", params={"limit": 5})

    # ── Group 2: GFW Tree Cover Loss ──
    print("\n--- Group 2: GFW Tree Cover Loss ---")
    test("GFW search (no filter)", "GET", f"{BN}/gfw", expect_keys=["records", "total"])
    test("GFW search (country=BRA)", "GET", f"{BN}/gfw", params={"country": "BRA"}, expect_keys=["records"])
    test("GFW search (year range)", "GET", f"{BN}/gfw", params={"year_start": 2015, "year_end": 2020}, expect_keys=["records"])
    test("GFW countries", "GET", f"{BN}/gfw/countries", expect_keys=["countries"])
    test("GFW country timeseries (ZZZ)", "GET", f"{BN}/gfw/ZZZ", allow_status=[200, 404])

    # ── Group 3: Spatial Overlaps ──
    print("\n--- Group 3: Spatial Overlaps ---")
    test("Overlaps (no filter)", "GET", f"{BN}/overlaps", expect_keys=["overlaps"])
    test("Overlaps (by wdpa_id)", "GET", f"{BN}/overlaps", params={"wdpa_id": 1}, expect_keys=["overlaps"])

    # ── Group 4: Nature Stats ──
    print("\n--- Group 4: Nature Stats ---")
    test("Nature stats", "GET", f"{BN}/stats", expect_keys=["wdpa", "gfw", "overlaps"])

    # ── Group 5: Coal Plants ──
    print("\n--- Group 5: Coal Plants ---")
    test("Coal search (no filter)", "GET", f"{BE}/coal-plants", expect_keys=["records", "total"])
    test("Coal search (country=CHN)", "GET", f"{BE}/coal-plants", params={"country": "CHN"}, expect_keys=["records"])
    test("Coal search (status=Operating)", "GET", f"{BE}/coal-plants", params={"status": "Operating"}, expect_keys=["records"])
    test("Coal search (parent=Eskom)", "GET", f"{BE}/coal-plants", params={"parent_company": "Eskom"}, expect_keys=["records"])
    test("Coal search (min_capacity=3000)", "GET", f"{BE}/coal-plants", params={"min_capacity_mw": 3000}, expect_keys=["records"])
    test("Coal search (name=Power)", "GET", f"{BE}/coal-plants", params={"search": "Power"}, expect_keys=["records"])
    test("Coal countries", "GET", f"{BE}/coal-plants/countries", expect_keys=["countries"])
    test("Coal owners", "GET", f"{BE}/coal-plants/owners", expect_keys=["owners"])
    test("Coal nearby", "GET", f"{BE}/coal-plants/nearby", params={"lat": 33.0, "lng": -83.0, "radius_km": 200}, expect_keys=["results", "center"])
    test("Coal pipeline", "GET", f"{BE}/coal-plants/pipeline", expect_keys=["pipeline", "total"])
    test("Coal by GEM ID (not found)", "GET", f"{BE}/coal-plants/GFAKE999", expect_status=404)
    test("Coal pagination (limit=3)", "GET", f"{BE}/coal-plants", params={"limit": 3})

    # ── Group 6: Coal Units ──
    print("\n--- Group 6: Coal Units ---")
    test("Coal units (fake plant)", "GET", f"{BE}/coal-units/00000000-0000-0000-0000-000000000000", expect_keys=["units", "total"])

    # ── Group 7: Energy Stats ──
    print("\n--- Group 7: Energy Stats ---")
    test("Energy stats", "GET", f"{BE}/stats", expect_keys=["coal_plants", "coal_units"])

    # ── Group 8: Ingester Registration ──
    print("\n--- Group 8: Ingester Registration ---")
    test("Ingesters list", "GET", f"{BASE}/api/v1/ingestion/ingesters", expect_keys=["ingesters", "total"])

    # Check WDPA+GFW and GEM are registered
    r = requests.get(f"{BASE}/api/v1/ingestion/ingesters", headers=HEADERS, timeout=10)
    if r.status_code == 200:
        source_ids = [i.get("source_id") for i in r.json().get("ingesters", [])]
        if "wdpa-protected-areas" in source_ids:
            passed += 1
            print("  PASS  WDPA ingester registered")
        else:
            failed += 1
            errors.append("FAIL WDPA ingester not in source_ids")
            print(f"  FAIL  WDPA ingester not in source_ids: {source_ids}")

        if "gem-coal-plant-tracker" in source_ids:
            passed += 1
            print("  PASS  GEM ingester registered")
        else:
            failed += 1
            errors.append("FAIL GEM ingester not in source_ids")
            print(f"  FAIL  GEM ingester not in source_ids: {source_ids}")

        if len(source_ids) >= 10:
            passed += 1
            print(f"  PASS  Total ingesters: {len(source_ids)} >= 10")
        else:
            failed += 1
            errors.append(f"FAIL Expected >= 10 ingesters, got {len(source_ids)}")
            print(f"  FAIL  Expected >= 10 ingesters, got {len(source_ids)}")
    else:
        failed += 3
        print(f"  FAIL  Could not fetch ingesters list (status={r.status_code})")

    # ── Summary ──
    total = passed + failed
    print(f"\n{'=' * 60}")
    print(f"Session 15 Results: {passed}/{total} passed, {failed} failed")
    if errors:
        print("\nFailures:")
        for e in errors:
            print(f"  - {e}")
    print(f"{'=' * 60}")

    sys.exit(0 if failed == 0 else 1)
