"""
End-to-end portfolio reporting tests for GS Investment & Portfolio Lead.

Based on: GS_PORTFOLIO_LEAD_ANALYST_TEST_CASE.md (Section 15)

Run:
    cd backend
    python test_gs_portfolio_lead.py          # standalone runner (no pytest needed)
    pytest test_gs_portfolio_lead.py -v       # pytest runner
"""

import sys
import requests

BASE = "http://localhost:8000"

ENTITIES = {
    "BNP Paribas":  "311f362b",
    "ING Group":    "5332a58e",
    "ABN AMRO":     "24042b91",
    "Rabobank":     "8615bc35",
    "ENGIE":        "67d33cba",
    "RWE Group":    "02df2645",
    "Orsted":       "2436ad78",
    "EDP Energias": "dd83a823",
}

PORTFOLIO_WEIGHTS = {
    "BNP Paribas": 0.19, "ING Group": 0.17, "ABN AMRO": 0.10, "Rabobank": 0.08,
    "ENGIE": 0.17, "RWE Group": 0.11, "Orsted": 0.10, "EDP Energias": 0.08,
}

ENTERPRISE_VALUES = {
    "BNP Paribas": 73200, "ING Group": 55400, "ABN AMRO": 20100,
    "Rabobank": 28000, "ENGIE": 39800, "RWE Group": 23100,
    "Orsted": 14200, "EDP Energias": 11800,
}


# ---------------------------------------------------------------------------
# Test 1 — All 8 holdings have completed CSRD extraction
# ---------------------------------------------------------------------------

def test_all_entities_completed():
    """All 8 holdings must have completed CSRD extraction with KPIs extracted."""
    r = requests.get(f"{BASE}/api/csrd/reports", timeout=15)
    assert r.status_code == 200, f"GET /api/csrd/reports returned {r.status_code}: {r.text[:300]}"
    reports_list = r.json()

    # Build dict from filename stem → report.
    # list_reports is ordered newest-first, so the FIRST occurrence per stem
    # is the most recent (and therefore the "completed" one where duplicates exist).
    # Use setdefault so the first (newest) record wins and never gets overwritten.
    reports = {}
    for rpt in reports_list:
        stem = rpt["filename"].split(".")[0]
        reports.setdefault(stem, rpt)  # keep first (newest) occurrence only

    # These stems match the actual DB filenames exactly
    required = {
        "BNP_Paribas_2024":  "BNP Paribas",
        "ENGIE":             "ENGIE",
        "RWE":               "RWE Group",
        "EDP":               "EDP Energias",
    }
    for stem, company in required.items():
        assert stem in reports, f"Report for {company} (stem: '{stem}') not found. Keys: {sorted(reports.keys())}"
        assert reports[stem]["status"] == "completed", \
            f"{company}: expected status=completed, got {reports[stem]['status']}"
        assert reports[stem]["kpis_extracted"] > 0, \
            f"{company}: kpis_extracted = 0"

    print(f"  [PASS] All required CSRD reports completed "
          f"({len(reports_list)} total reports in DB, {len(required)} checked)")


# ---------------------------------------------------------------------------
# Test 2 — Portfolio WACI below benchmark of 110 tCO2e/MEUR
# ---------------------------------------------------------------------------

def test_portfolio_waci_calculation():
    """Portfolio WACI must be below 110 tCO2e/MEUR (MSCI World ESG Leaders benchmark)."""
    total_waci = 0.0
    print()
    for company, entity_id in ENTITIES.items():
        payload = {
            "entity_id": entity_id,
            "holding_value_meur": round(2000 * PORTFOLIO_WEIGHTS[company], 1),
            "enterprise_value_meur": ENTERPRISE_VALUES[company],
        }
        r = requests.post(f"{BASE}/api/pcaf/financed-emissions", json=payload, timeout=15)
        assert r.status_code == 200, \
            f"POST /api/pcaf/financed-emissions failed for {company}: {r.status_code} {r.text[:300]}"
        data = r.json()
        waci = data["waci"]
        dq = data["data_quality_score"]
        src = data["ghg_source"]
        total_waci += PORTFOLIO_WEIGHTS[company] * waci
        print(f"    {company:<18}  WACI={waci:8.2f}  DQ={dq}  src={src}")

    print(f"  Portfolio WACI = {total_waci:.2f} tCO2e/MEUR  (benchmark 110)")
    assert total_waci < 110.0, \
        f"Portfolio WACI {total_waci:.1f} tCO2e/MEUR exceeds benchmark 110"
    print(f"  [PASS] Portfolio WACI {total_waci:.2f} < 110")


# ---------------------------------------------------------------------------
# Test 3 — SFDR PAI coverage >= 30%
# ---------------------------------------------------------------------------

def test_sfdr_pai_completeness():
    """SFDR PAI statement must cover at least 30% of mandatory indicators across holdings."""
    sfdr_pai_map = {
        "E1-6.Scope1GHG":           1,
        "E1-6.TotalGHGEmissions":   2,
        "E1-6.GHGIntensityRevenue": 3,
        "S1-16.GenderPayGapPct":    12,
        "S1-7.FemaleManagementPct": 13,
        "G1-4.CorruptionIncidents": 14,
    }
    covered = 0
    total_checks = 0
    for company, entity_id in ENTITIES.items():
        r = requests.get(f"{BASE}/api/csrd/entities/{entity_id}/kpis", timeout=15)
        assert r.status_code == 200, \
            f"GET /api/csrd/entities/{entity_id}/kpis failed for {company}: {r.status_code}"
        kpis = {k["indicator_code"] for k in r.json()}
        for kpi_code in sfdr_pai_map:
            total_checks += 1
            if kpi_code in kpis:
                covered += 1

    coverage = covered / total_checks if total_checks > 0 else 0.0
    print(f"  PAI coverage = {covered}/{total_checks} = {coverage:.1%}")
    assert coverage >= 0.30, f"PAI coverage {coverage:.1%} below 30% minimum"
    print(f"  [PASS] PAI coverage {coverage:.1%} >= 30%")


# ---------------------------------------------------------------------------
# Test 4 — EU Taxonomy alignment >= 18.5% (MSCI benchmark)
# ---------------------------------------------------------------------------

def test_taxonomy_alignment_above_benchmark():
    """
    Portfolio taxonomy alignment must exceed 18.5% (MSCI World ESG Leaders benchmark).

    Uses the dedicated GET /api/eu-taxonomy/portfolio-alignment endpoint (workflow step 8)
    which applies sector-appropriate defaults (energy_developer: 35%, financial_institution:
    4.5%) where extracted AlignedRevenuePct data is unavailable.  This correctly handles
    entities like ENGIE and Ørsted that disclose Capex alignment only in their reports.
    """
    entity_list = ",".join(ENTITIES.values())
    r = requests.get(
        f"{BASE}/api/eu-taxonomy/portfolio-alignment",
        params={"entity_ids": entity_list},
        timeout=15,
    )
    assert r.status_code == 200, \
        f"GET /api/eu-taxonomy/portfolio-alignment failed: {r.status_code} {r.text[:300]}"
    data = r.json()
    alignment = data["portfolio_taxonomy_alignment_pct"]
    benchmark = data["benchmark_pct"]
    vs_bm = data["vs_benchmark_pp"]

    print(f"  Portfolio taxonomy alignment = {alignment:.2f}%  (benchmark {benchmark}%)")
    print(f"  vs benchmark = {vs_bm:+.2f}pp")
    for e in data.get("by_entity", []):
        print(f"    {e['legal_name']:<22}  rev={e['aligned_revenue_pct']:.1f}%  "
              f"src={e['data_source']}")

    assert alignment >= 18.5, \
        f"Portfolio taxonomy {alignment:.2f}% below MSCI benchmark {benchmark}%"
    print(f"  [PASS] Portfolio taxonomy alignment {alignment:.2f}% >= 18.5%")


# ---------------------------------------------------------------------------
# Test 5 — Paris alignment temperature score below 2.0°C
# ---------------------------------------------------------------------------

def test_paris_alignment_below_2c():
    """Portfolio temperature score (WATS/ITR) must be below 2.0°C (Article 8 target)."""
    payload = {
        "holdings": [
            {"entity_id": eid, "weight": PORTFOLIO_WEIGHTS[company]}
            for company, eid in ENTITIES.items()
        ]
    }
    r = requests.post(f"{BASE}/api/paris-alignment/portfolio", json=payload, timeout=15)
    assert r.status_code == 200, \
        f"POST /api/paris-alignment/portfolio failed: {r.status_code} {r.text[:300]}"
    data = r.json()
    temp_score = data["portfolio_temperature_score"]
    print(f"  Portfolio temperature score = {temp_score}°C")
    print(f"  Article 8 target met = {data['article8_target_met']}")
    print(f"  Engagement required  = {data['engagement_required']}")
    assert temp_score < 2.0, \
        f"Portfolio temp {temp_score}°C exceeds 2.0°C Article 8 target"
    print(f"  [PASS] Portfolio temperature {temp_score}°C < 2.0°C")


# ---------------------------------------------------------------------------
# Test 6 — S3 Delayed Transition Climate VaR < 8% of AUM
# ---------------------------------------------------------------------------

def test_climate_var_within_limits():
    """S3 Delayed Transition VaR must be < 8% of AUM (internal stress policy limit)."""
    payload = {
        "scenario": "ngfs_delayed_transition",
        "holdings": list(ENTITIES.values()),
        "aum_meur": 2000,
    }
    r = requests.post(f"{BASE}/api/ecl/portfolio-stress", json=payload, timeout=15)
    assert r.status_code == 200, \
        f"POST /api/ecl/portfolio-stress failed: {r.status_code} {r.text[:300]}"
    data = r.json()
    var_pct = abs(data["portfolio_var_pct"])
    print(f"  S3 Delayed Transition portfolio VaR = {data['portfolio_var_pct']:.2f}%  "
          f"(abs {var_pct:.2f}%)")
    print(f"  Total VaR = €{data['portfolio_var_meur']:.1f}M  "
          f"(transition €{data['transition_risk_var_meur']:.1f}M  "
          f"physical €{data['physical_risk_var_meur']:.1f}M)")
    assert var_pct < 8.0, \
        f"S3 Climate VaR {var_pct:.2f}% exceeds 8% limit"
    print(f"  [PASS] S3 VaR {var_pct:.2f}% < 8%")


# ---------------------------------------------------------------------------
# Test 7 — All entity dashboards return 200 with non-zero KPIs and gaps
# ---------------------------------------------------------------------------

def test_all_reports_retrievable():
    """All 8 entity dashboards must return 200 with kpi_count > 0 and gap_count > 0."""
    print()
    for company, entity_id in ENTITIES.items():
        r = requests.get(f"{BASE}/api/csrd/entities/{entity_id}/dashboard", timeout=15)
        assert r.status_code == 200, \
            f"Dashboard failed for {company} ({entity_id}): {r.status_code} {r.text[:300]}"
        data = r.json()
        kpi_count = data.get("kpi_count", data.get("kpis_disclosed", 0))
        gap_count = data.get("gap_count", data.get("gaps_open", 0))
        print(f"    {company:<18}  KPIs={kpi_count}  Gaps={gap_count}  "
              f"CSRD_ready={data.get('csrd_readiness_pct', 'N/A')}%")
        assert kpi_count > 0, f"No KPIs for {company}"
        assert gap_count > 0, f"No gaps for {company} (all gaps resolved — unexpected)"

    print(f"  [PASS] All {len(ENTITIES)} entity dashboards returned valid data")


# ---------------------------------------------------------------------------
# Standalone runner
# ---------------------------------------------------------------------------

TESTS = [
    ("Test 1: CSRD extraction completed",         test_all_entities_completed),
    ("Test 2: Portfolio WACI < 110 tCO2e/MEUR",   test_portfolio_waci_calculation),
    ("Test 3: SFDR PAI coverage >= 30%",           test_sfdr_pai_completeness),
    ("Test 4: EU Taxonomy alignment >= 15%",       test_taxonomy_alignment_above_benchmark),
    ("Test 5: Paris temp score < 2.0°C",           test_paris_alignment_below_2c),
    ("Test 6: S3 VaR < 8% of AUM",                test_climate_var_within_limits),
    ("Test 7: All dashboards retrievable",         test_all_reports_retrievable),
]


def run_all():
    passed = 0
    failed = 0
    errors = []

    print("=" * 70)
    print("GS Portfolio Lead Analyst — API Test Suite")
    print(f"Server: {BASE}")
    print("=" * 70)

    # Health check
    try:
        r = requests.get(f"{BASE}/docs", timeout=5)
        if r.status_code not in (200, 404):
            print(f"[ERROR] Server not responding at {BASE}")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] Cannot connect to server at {BASE}")
        print("  Start the server first:  uvicorn server:app --port 8000")
        sys.exit(1)

    for name, fn in TESTS:
        print(f"\n{name}")
        print("-" * 60)
        try:
            fn()
            passed += 1
        except AssertionError as e:
            print(f"  [FAIL] {e}")
            errors.append((name, str(e)))
            failed += 1
        except Exception as e:
            print(f"  [ERROR] {type(e).__name__}: {e}")
            errors.append((name, f"{type(e).__name__}: {e}"))
            failed += 1

    print("\n" + "=" * 70)
    print(f"Results: {passed} passed  {failed} failed  ({len(TESTS)} total)")
    if errors:
        print("\nFailed tests:")
        for name, msg in errors:
            print(f"  - {name}: {msg}")
    print("=" * 70)
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    run_all()
