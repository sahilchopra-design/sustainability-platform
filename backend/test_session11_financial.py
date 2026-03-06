"""Smoke tests for Session 11 -- SEC EDGAR XBRL + yfinance/FMP Financial Data Ingesters."""
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

token = get_token("financial_test@a2intel.com", "SecurePass99", "Financial Tester")
headers = {"Authorization": f"Bearer {token}"} if token else {}


# -- 1. Ingesters registered --------------------------------------------------

def t_ingesters():
    r = requests.get(f"{BASE}/api/v1/ingestion/ingesters", headers=headers)
    d = r.json()
    names = [i.get("display_name", "") for i in d.get("ingesters", [])]
    has_edgar = any("EDGAR" in n for n in names)
    has_yf = any("yfinance" in n.lower() for n in names)
    return (r.status_code == 200 and has_edgar and has_yf,
            f"HTTP {r.status_code}, ingesters={names}")
test("GET /ingestion/ingesters (EDGAR + yfinance registered)", t_ingesters)


# -- 2. Combined stats -------------------------------------------------------

def t_stats():
    r = requests.get(f"{BASE}/api/v1/financial-data/stats", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "edgar" in d
            and "market" in d), f"HTTP {r.status_code}, data={d}"
test("GET /financial-data/stats", t_stats)


# -- 3. EDGAR search (empty is OK) -------------------------------------------

def t_edgar_search():
    r = requests.get(f"{BASE}/api/v1/financial-data/edgar?limit=5", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "total" in d
            and "records" in d), f"HTTP {r.status_code}, total={d.get('total')}"
test("GET /financial-data/edgar", t_edgar_search)


# -- 4. EDGAR companies list -------------------------------------------------

def t_edgar_companies():
    r = requests.get(f"{BASE}/api/v1/financial-data/edgar/companies", headers=headers)
    d = r.json()
    return (r.status_code == 200 and "companies" in d), f"HTTP {r.status_code}, count={len(d.get('companies', []))}"
test("GET /financial-data/edgar/companies", t_edgar_companies)


# -- 5. EDGAR filing types ---------------------------------------------------

def t_edgar_types():
    r = requests.get(f"{BASE}/api/v1/financial-data/edgar/filing-types", headers=headers)
    d = r.json()
    return (r.status_code == 200 and "filing_types" in d), f"HTTP {r.status_code}, count={len(d.get('filing_types', []))}"
test("GET /financial-data/edgar/filing-types", t_edgar_types)


# -- 6. EDGAR compare (empty is OK) -----------------------------------------

def t_edgar_compare():
    r = requests.get(f"{BASE}/api/v1/financial-data/edgar/compare?metric=revenue&tickers=AAPL,MSFT", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "metric" in d
            and "companies" in d), f"HTTP {r.status_code}, companies={len(d.get('companies', []))}"
test("GET /financial-data/edgar/compare?metric=revenue&tickers=AAPL,MSFT", t_edgar_compare)


# -- 7. Market search (empty is OK) -----------------------------------------

def t_market_search():
    r = requests.get(f"{BASE}/api/v1/financial-data/market?limit=5", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "total" in d
            and "records" in d), f"HTTP {r.status_code}, total={d.get('total')}"
test("GET /financial-data/market", t_market_search)


# -- 8. Market tickers -------------------------------------------------------

def t_market_tickers():
    r = requests.get(f"{BASE}/api/v1/financial-data/market/tickers", headers=headers)
    d = r.json()
    return (r.status_code == 200 and "tickers" in d), f"HTTP {r.status_code}, count={len(d.get('tickers', []))}"
test("GET /financial-data/market/tickers", t_market_tickers)


# -- 9. Market sectors -------------------------------------------------------

def t_market_sectors():
    r = requests.get(f"{BASE}/api/v1/financial-data/market/sectors", headers=headers)
    d = r.json()
    return (r.status_code == 200 and "sectors" in d), f"HTTP {r.status_code}, count={len(d.get('sectors', []))}"
test("GET /financial-data/market/sectors", t_market_sectors)


# -- 10. EVIC endpoint -------------------------------------------------------

def t_evic():
    r = requests.get(f"{BASE}/api/v1/financial-data/market/evic?limit=5", headers=headers)
    d = r.json()
    return (r.status_code == 200
            and "total" in d
            and "records" in d), f"HTTP {r.status_code}, total={d.get('total')}"
test("GET /financial-data/market/evic", t_evic)


# -- 11. No auth -> 401 ------------------------------------------------------

def t_noauth():
    r = requests.get(f"{BASE}/api/v1/financial-data/stats")
    return r.status_code == 401, f"HTTP {r.status_code}"
test("GET /financial-data/stats -> 401 without auth", t_noauth)


# -- Summary ------------------------------------------------------------------

print(f"\n{'='*60}")
passed = sum(1 for _, s, _ in results if s == "PASS")
total = len(results)
print(f"Session 11 Results: {passed}/{total} passed")
if passed < total:
    print("FAILURES:")
    for name, status, msg in results:
        if status == "FAIL":
            print(f"  - {name}: {msg}")
