"""Quick smoke test for Session 2: Auth + RBAC + Audit wiring."""
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

# 1. Health
def t_health():
    r = requests.get(f"{BASE}/api/health")
    return r.status_code == 200, f"HTTP {r.status_code}"
test("Health check", t_health)

# 2. Register
def t_register():
    r = requests.post(f"{BASE}/api/auth/register", json={
        "email": "session2test@a2intel.com",
        "password": "SecurePass99",
        "name": "Session2 Test",
    })
    if r.status_code == 400:
        return True, "Already registered (OK)"
    d = r.json()
    has_role = "role" in d
    return r.status_code == 200 and has_role, f"HTTP {r.status_code}, role={d.get('role')}"
test("Register returns role", t_register)

# 3. Login returns role + org_id
def t_login():
    r = requests.post(f"{BASE}/api/auth/login", json={
        "email": "session2test@a2intel.com",
        "password": "SecurePass99",
    })
    d = r.json()
    return r.status_code == 200 and "role" in d, f"role={d.get('role')}, org_id={d.get('org_id')}"
test("Login returns role+org", t_login)

# Get token for subsequent tests
login_resp = requests.post(f"{BASE}/api/auth/login", json={
    "email": "session2test@a2intel.com",
    "password": "SecurePass99",
}).json()
token = login_resp.get("session_token", "")
headers = {"Authorization": f"Bearer {token}"}

# 4. /me returns role, org_id, is_active
def t_me():
    r = requests.get(f"{BASE}/api/auth/me", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "role" in d
            and "org_id" in d
            and "is_active" in d), f"role={d.get('role')}, is_active={d.get('is_active')}"
test("/me returns role+org+is_active", t_me)

# 5. Audit log requires auth
def t_audit_no_auth():
    r = requests.get(f"{BASE}/api/v1/audit-log/")
    return r.status_code == 401, f"HTTP {r.status_code}"
test("Audit log 401 without auth", t_audit_no_auth)

# 6. Audit log requires admin/compliance (viewer gets 403)
def t_audit_viewer():
    r = requests.get(f"{BASE}/api/v1/audit-log/", headers=headers)
    return r.status_code == 403, f"HTTP {r.status_code}"
test("Audit log 403 for viewer role", t_audit_viewer)

# 7. Organisations list requires admin
def t_orgs_viewer():
    r = requests.get(f"{BASE}/api/v1/organisations/", headers=headers)
    return r.status_code == 403, f"HTTP {r.status_code}"
test("Orgs list 403 for viewer role", t_orgs_viewer)

# 8. /organisations/mine works for any authenticated user
def t_my_org():
    r = requests.get(f"{BASE}/api/v1/organisations/mine", headers=headers)
    d = r.json()
    return r.status_code == 200, f"org={d.get('organisation')}"
test("/organisations/mine for authenticated user", t_my_org)

# 9. Deactivated user check (we won't actually deactivate, just verify field exists)
def t_is_active_field():
    r = requests.get(f"{BASE}/api/auth/me", headers=headers)
    d = r.json()
    return d.get("is_active") is True, f"is_active={d.get('is_active')}"
test("is_active field in /me", t_is_active_field)

# 10. Logout
def t_logout():
    r = requests.post(f"{BASE}/api/auth/logout", headers=headers)
    return r.status_code == 200, f"HTTP {r.status_code}"
test("Logout", t_logout)

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
