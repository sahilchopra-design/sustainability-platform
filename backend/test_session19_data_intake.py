"""
Session 19 -- F3: Data Intake status dashboard wiring tests.

Tests that /api/v1/data-intake/status returns:
  1. Client intake modules (7) with correct structure
  2. Data Hub reference sources (11) with live DB counts
  3. Summary stats (completion %, totals)
  4. Country risk breakdown sub-indices
"""

import requests

BASE = "http://localhost:8001"
API = f"{BASE}/api/v1/data-intake"

passed = 0
failed = 0


def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name}  {detail}")


def test_status_endpoint():
    """GET /status returns 200 with expected top-level keys."""
    r = requests.get(f"{API}/status")
    check("status_200", r.status_code == 200, f"got {r.status_code}")
    d = r.json()
    check("has_modules", "modules" in d)
    check("has_data_hub", "data_hub" in d)
    check("has_summary", "summary" in d)
    check("has_cri_breakdown", "country_risk_breakdown" in d)
    return d


def test_client_modules(data):
    """7 client intake modules with required fields."""
    modules = data["modules"]
    check("7_client_modules", len(modules) == 7, f"got {len(modules)}")

    required_fields = {"id", "label", "route", "count", "unit", "status", "priority"}
    for m in modules:
        ok = required_fields.issubset(m.keys())
        check(f"module_{m['id']}_fields", ok, f"missing {required_fields - m.keys()}")

    # P0 modules
    p0 = [m for m in modules if m["priority"] == "P0"]
    check("2_p0_modules", len(p0) == 2, f"got {len(p0)}")
    p0_ids = {m["id"] for m in p0}
    check("p0_loan_portfolio", "loan_portfolio" in p0_ids)
    check("p0_counterparty", "counterparty" in p0_ids)

    # P1 modules
    p1 = [m for m in modules if m["priority"] == "P1"]
    check("5_p1_modules", len(p1) == 5, f"got {len(p1)}")

    # internal_config should be configured (has 8 rows)
    cfg = next((m for m in modules if m["id"] == "internal_config"), None)
    check("internal_config_found", cfg is not None)
    if cfg:
        check("internal_config_status", cfg["status"] == "configured", f"got {cfg['status']}")
        check("internal_config_count_ge_8", cfg["count"] >= 8, f"got {cfg['count']}")

    # status values are valid
    valid_statuses = {"active", "empty", "configured"}
    for m in modules:
        check(f"module_{m['id']}_status_valid", m["status"] in valid_statuses, f"got {m['status']}")


def test_data_hub(data):
    """11 Data Hub sources with live DB counts."""
    dh = data["data_hub"]
    check("11_dh_sources", len(dh) == 11, f"got {len(dh)}")

    required_fields = {"id", "label", "table", "count", "unit", "category", "status"}
    for d in dh:
        ok = required_fields.issubset(d.keys())
        check(f"dh_{d['id']}_fields", ok, f"missing {required_fields - d.keys()}")

    # Known populated sources
    sbti = next((d for d in dh if d["id"] == "sbti_companies"), None)
    check("sbti_found", sbti is not None)
    if sbti:
        check("sbti_count_gt_10000", sbti["count"] > 10000, f"got {sbti['count']}")
        check("sbti_active", sbti["status"] == "active")

    ca100 = next((d for d in dh if d["id"] == "ca100_assessments"), None)
    check("ca100_found", ca100 is not None)
    if ca100:
        check("ca100_count_gt_100", ca100["count"] > 100, f"got {ca100['count']}")

    cri = next((d for d in dh if d["id"] == "country_risk_indices"), None)
    check("cri_found", cri is not None)
    if cri:
        check("cri_count_gt_2000", cri["count"] > 2000, f"got {cri['count']}")

    crrem = next((d for d in dh if d["id"] == "crrem_pathways"), None)
    check("crrem_found", crrem is not None)
    if crrem:
        check("crrem_count_gt_1000", crrem["count"] > 1000, f"got {crrem['count']}")

    ref_data = next((d for d in dh if d["id"] == "reference_data"), None)
    check("ref_data_found", ref_data is not None)
    if ref_data:
        check("ref_data_count_gt_500", ref_data["count"] > 500, f"got {ref_data['count']}")

    # Categories are valid
    valid_cats = {"ESG", "Governance", "Energy", "Real Estate", "Emissions", "Platform"}
    for d in dh:
        check(f"dh_{d['id']}_cat_valid", d["category"] in valid_cats, f"got {d['category']}")


def test_country_risk_breakdown(data):
    """Country risk breakdown shows sub-indices."""
    cri = data["country_risk_breakdown"]
    check("cri_breakdown_has_entries", len(cri) >= 3, f"got {len(cri)}")

    idx_names = [b["index"] for b in cri]
    check("cri_has_CPI", "CPI" in idx_names)
    check("cri_has_FSI", "FSI" in idx_names)
    check("cri_has_FH_FIW", "FH_FIW" in idx_names)
    check("cri_has_UNDP_GII", "UNDP_GII" in idx_names)

    for b in cri:
        check(f"cri_{b['index']}_count_gt_0", b["count"] > 0, f"got {b['count']}")


def test_summary(data):
    """Summary stats are computed correctly."""
    s = data["summary"]
    required = {
        "total_client_records", "total_reference_records",
        "client_modules_active", "client_modules_total",
        "client_completion_pct", "dh_sources_active", "dh_sources_total",
        "dh_completion_pct",
    }
    check("summary_fields", required.issubset(s.keys()), f"missing {required - s.keys()}")

    check("client_modules_total_7", s["client_modules_total"] == 7, f"got {s['client_modules_total']}")
    check("dh_sources_total_11", s["dh_sources_total"] == 11, f"got {s['dh_sources_total']}")
    check("dh_sources_active_ge_5", s["dh_sources_active"] >= 5, f"got {s['dh_sources_active']}")
    check("total_ref_gt_20000", s["total_reference_records"] > 20000, f"got {s['total_reference_records']}")
    check("client_completion_pct_valid", 0 <= s["client_completion_pct"] <= 100)
    check("dh_completion_pct_valid", 0 <= s["dh_completion_pct"] <= 100)
    check("dh_completion_pct_gt_40", s["dh_completion_pct"] > 40, f"got {s['dh_completion_pct']}")

    # Cross-check: total_reference_records == sum of data_hub counts
    dh_sum = sum(d["count"] for d in data["data_hub"])
    check("ref_total_matches_dh_sum", s["total_reference_records"] == dh_sum,
          f"summary={s['total_reference_records']} vs dh_sum={dh_sum}")


if __name__ == "__main__":
    print("=" * 60)
    print("Session 19 -- Data Intake Status Dashboard Tests")
    print("=" * 60)

    print("\n-- GET /status endpoint --")
    data = test_status_endpoint()

    print("\n-- Client intake modules --")
    test_client_modules(data)

    print("\n-- Data Hub reference sources --")
    test_data_hub(data)

    print("\n-- Country risk breakdown --")
    test_country_risk_breakdown(data)

    print("\n-- Summary stats --")
    test_summary(data)

    print("\n" + "=" * 60)
    total = passed + failed
    print(f"Results: {passed}/{total} passed, {failed} failed")
    if failed:
        print("SOME TESTS FAILED")
        exit(1)
    else:
        print("ALL TESTS PASSED")
