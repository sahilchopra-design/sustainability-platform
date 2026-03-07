"""
Session 20 -- F6: Geothermal Assessment + F7: IRENA Five Pillars
Smoke tests for both new endpoints.
"""

import requests, json

BASE = "http://localhost:8001"
GEO = f"{BASE}/api/v1/geothermal"
IRENA = f"{BASE}/api/v1/irena-five-pillars"

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


# ============================================================
# F6: Geothermal
# ============================================================

def test_plant_types():
    """GET /plant-types returns all 5 geothermal plant types."""
    r = requests.get(f"{GEO}/plant-types")
    check("geo_plant_types_200", r.status_code == 200, f"got {r.status_code}")
    d = r.json()
    expected = {"dry_steam", "single_flash", "double_flash", "binary", "egs"}
    check("geo_5_plant_types", set(d.keys()) == expected, f"got {set(d.keys())}")
    # Each has required fields
    for k, v in d.items():
        for fld in ["label", "lcoe_low", "lcoe_high", "cf_typical", "lifetime", "co2_gkwh", "temp_min_c", "temp_optimal_c"]:
            check(f"geo_{k}_has_{fld}", fld in v, f"missing {fld} in {k}")


def test_geothermal_binary():
    """POST /assess with binary plant - typical Iceland scenario."""
    payload = {
        "project_name": "Iceland Binary",
        "country_iso2": "IS",
        "plant_type": "binary",
        "installed_capacity_mw": 50,
        "reservoir_temp_c": 160,
        "well_depth_m": 2500,
        "number_of_wells": 10,
        "drilling_cost_musd_per_well": 5.0,
        "surface_plant_cost_musd": 80,
        "annual_opex_musd": 6.0,
        "discount_rate_pct": 8.0,
        "project_lifetime_years": 25,
        "has_district_heating": True,
        "heating_revenue_musd_yr": 3.0,
        "carbon_price_usd_tco2": 50,
        "grid_emission_factor_gco2_kwh": 400,
    }
    r = requests.post(f"{GEO}/assess", json=payload)
    check("geo_binary_200", r.status_code == 200, f"got {r.status_code}")
    d = r.json()

    # Structure checks
    check("geo_has_lcoe", "lcoe_usd_mwh" in d)
    check("geo_has_npv", "npv_musd" in d)
    check("geo_has_irr", "equity_irr_pct" in d)
    check("geo_has_viability", "resource_viability" in d)
    check("geo_has_seismicity", "seismicity_risk" in d)
    check("geo_has_paris", "paris_aligned" in d)
    check("geo_has_benchmarks", "irena_benchmarks" in d)
    check("geo_has_dh_benefit", "district_heating_benefit" in d)

    # Value checks
    check("geo_capex_130", d["total_capex_musd"] == 130.0, f"got {d['total_capex_musd']}")
    check("geo_lcoe_positive", d["lcoe_usd_mwh"] > 0, f"got {d['lcoe_usd_mwh']}")
    check("geo_annual_gen_gt_0", d["annual_generation_gwh"] > 0)
    check("geo_binary_paris_aligned", d["paris_aligned"] is True, "binary should be Paris-aligned (0 gCO2)")
    check("geo_plant_co2_0", d["plant_co2_intensity_gco2_kwh"] == 0, "binary = 0 gCO2")

    # Viability: 160C for binary (min=100, optimal=150) -> Optimal
    check("geo_viability_optimal", d["temp_adequacy"] == "Optimal", f"got {d['temp_adequacy']}")
    check("geo_viability_high", d["resource_viability"] == "High", f"got {d['resource_viability']}")

    # Seismicity: 2500m depth -> medium
    check("geo_seismicity_medium", d["seismicity_risk"] == "medium", f"got {d['seismicity_risk']}")

    # District heating enabled
    check("geo_dh_enabled", d["district_heating_benefit"]["enabled"] is True)
    check("geo_dh_revenue", d["district_heating_benefit"]["annual_revenue_musd"] == 3.0)

    # LCOE within IRENA range for binary: 55-110
    check("geo_lcoe_in_range", 20 <= d["lcoe_usd_mwh"] <= 200, f"LCOE={d['lcoe_usd_mwh']}")

    return d


def test_geothermal_egs():
    """POST /assess with EGS - should flag high seismicity."""
    payload = {
        "project_name": "EGS Deep",
        "country_iso2": "US",
        "plant_type": "egs",
        "installed_capacity_mw": 30,
        "reservoir_temp_c": 200,
        "well_depth_m": 5000,
        "number_of_wells": 15,
        "drilling_cost_musd_per_well": 8.0,
        "surface_plant_cost_musd": 60,
        "annual_opex_musd": 5.0,
        "discount_rate_pct": 10.0,
        "project_lifetime_years": 25,
        "carbon_price_usd_tco2": 80,
        "grid_emission_factor_gco2_kwh": 500,
    }
    r = requests.post(f"{GEO}/assess", json=payload)
    check("geo_egs_200", r.status_code == 200, f"got {r.status_code}")
    d = r.json()

    check("geo_egs_seismicity_high", d["seismicity_risk"] == "high", f"got {d['seismicity_risk']}")
    check("geo_egs_paris_aligned", d["paris_aligned"] is True, "EGS = 0 gCO2")
    check("geo_egs_plant_type", d["plant_type"] == "egs")
    check("geo_egs_capex", d["total_capex_musd"] == 180.0, f"got {d['total_capex_musd']}")


def test_geothermal_flash_low_temp():
    """POST /assess with single flash but low temp - should flag Below minimum."""
    payload = {
        "project_name": "Low Temp Flash",
        "country_iso2": "KE",
        "plant_type": "single_flash",
        "installed_capacity_mw": 40,
        "reservoir_temp_c": 120,  # Below min 180
        "well_depth_m": 1800,
        "number_of_wells": 8,
        "drilling_cost_musd_per_well": 4.0,
        "surface_plant_cost_musd": 50,
        "annual_opex_musd": 4.0,
        "discount_rate_pct": 8.0,
        "project_lifetime_years": 30,
        "carbon_price_usd_tco2": 30,
        "grid_emission_factor_gco2_kwh": 600,
    }
    r = requests.post(f"{GEO}/assess", json=payload)
    check("geo_flash_low_200", r.status_code == 200)
    d = r.json()
    check("geo_flash_low_temp_below", d["temp_adequacy"] == "Below minimum", f"got {d['temp_adequacy']}")
    check("geo_flash_low_viability", d["resource_viability"] == "Low", f"got {d['resource_viability']}")
    check("geo_flash_low_seismicity", d["seismicity_risk"] == "low", f"got {d['seismicity_risk']}")


def test_geothermal_bad_type():
    """POST /assess with invalid plant type -> 400."""
    payload = {
        "project_name": "Bad",
        "plant_type": "nuclear",
        "installed_capacity_mw": 10,
        "reservoir_temp_c": 100,
        "well_depth_m": 1000,
        "number_of_wells": 2,
        "drilling_cost_musd_per_well": 3,
        "surface_plant_cost_musd": 20,
        "annual_opex_musd": 1,
    }
    r = requests.post(f"{GEO}/assess", json=payload)
    check("geo_bad_type_400", r.status_code == 400, f"got {r.status_code}")


# ============================================================
# F7: IRENA Five Pillars
# ============================================================

def test_framework():
    """GET /framework returns 5 pillars with criteria."""
    r = requests.get(f"{IRENA}/framework")
    check("irena_fw_200", r.status_code == 200, f"got {r.status_code}")
    d = r.json()
    check("irena_fw_has_pillars", "pillars" in d)
    check("irena_fw_5_pillars", len(d["pillars"]) == 5, f"got {len(d['pillars'])}")

    pids = [p["id"] for p in d["pillars"]]
    for pid in ["infrastructure", "policy", "financing", "human_capital", "technology"]:
        check(f"irena_fw_has_{pid}", pid in pids)

    # Each pillar has 5 criteria
    for p in d["pillars"]:
        check(f"irena_fw_{p['id']}_5_criteria", len(p["criteria"]) == 5, f"got {len(p['criteria'])}")
        check(f"irena_fw_{p['id']}_has_weight", "weight" in p)

    # Weights sum to 1.0
    total_w = sum(p["weight"] for p in d["pillars"])
    check("irena_fw_weights_sum_1", abs(total_w - 1.0) < 0.01, f"got {total_w}")

    return d


def test_assess_advanced():
    """POST /assess with high scores -> Advanced rating."""
    pillar_scores = []
    for pid in ["infrastructure", "policy", "financing", "human_capital", "technology"]:
        pillar_scores.append({
            "pillar_id": pid,
            "scores": {f"crit_{i}": 9 for i in range(5)},  # Will use criterion IDs
        })

    # Use real criterion IDs from framework
    fw = requests.get(f"{IRENA}/framework").json()
    pillar_scores = []
    for p in fw["pillars"]:
        scores = {c["id"]: 9.0 for c in p["criteria"]}
        pillar_scores.append({"pillar_id": p["id"], "scores": scores})

    payload = {
        "entity_name": "Germany",
        "entity_type": "country",
        "country_iso2": "DE",
        "assessment_year": 2025,
        "pillar_scores": pillar_scores,
    }
    r = requests.post(f"{IRENA}/assess", json=payload)
    check("irena_adv_200", r.status_code == 200, f"got {r.status_code}")
    d = r.json()

    # Structure
    check("irena_has_pillar_results", "pillar_results" in d)
    check("irena_has_overall_score", "overall_score" in d)
    check("irena_has_overall_pct", "overall_pct" in d)
    check("irena_has_overall_rating", "overall_rating" in d)
    check("irena_has_readiness", "transition_readiness" in d)
    check("irena_has_gap_analysis", "gap_analysis" in d)
    check("irena_has_recommendations", "recommendations" in d)
    check("irena_has_benchmarks", "country_benchmarks" in d)

    # 5 pillar results
    check("irena_5_pillar_results", len(d["pillar_results"]) == 5)

    # All pillars should be Advanced (90%)
    for pr in d["pillar_results"]:
        check(f"irena_adv_{pr['id']}_rating", pr["rating"] == "Advanced", f"got {pr['rating']}")
        check(f"irena_adv_{pr['id']}_pct_90", pr["pct"] == 90.0, f"got {pr['pct']}")

    check("irena_overall_rating_advanced", d["overall_rating"] == "Advanced", f"got {d['overall_rating']}")
    check("irena_overall_pct_90", d["overall_pct"] == 90.0, f"got {d['overall_pct']}")
    check("irena_readiness_ready", d["transition_readiness"] == "Transition-Ready", f"got {d['transition_readiness']}")

    # No gaps (all at 90%)
    check("irena_no_gaps", len(d["gap_analysis"]) == 0, f"got {len(d['gap_analysis'])} gaps")

    return d


def test_assess_early_stage():
    """POST /assess with low scores -> Early Stage rating."""
    fw = requests.get(f"{IRENA}/framework").json()
    pillar_scores = []
    for p in fw["pillars"]:
        scores = {c["id"]: 2.0 for c in p["criteria"]}
        pillar_scores.append({"pillar_id": p["id"], "scores": scores})

    payload = {
        "entity_name": "Emerging Country",
        "entity_type": "country",
        "country_iso2": "TD",
        "assessment_year": 2025,
        "pillar_scores": pillar_scores,
    }
    r = requests.post(f"{IRENA}/assess", json=payload)
    check("irena_early_200", r.status_code == 200)
    d = r.json()

    check("irena_early_rating", d["overall_rating"] == "Early Stage", f"got {d['overall_rating']}")
    check("irena_early_readiness", d["transition_readiness"] == "Significant Gaps", f"got {d['transition_readiness']}")
    check("irena_early_pct_20", d["overall_pct"] == 20.0, f"got {d['overall_pct']}")

    # All criteria should be in gap analysis (20% < 50%)
    check("irena_early_25_gaps", len(d["gap_analysis"]) == 25, f"got {len(d['gap_analysis'])}")

    # Should have recommendations
    check("irena_early_has_recs", len(d["recommendations"]) > 0)


def test_assess_mixed():
    """POST /assess with mixed scores -> verify weighted scoring."""
    fw = requests.get(f"{IRENA}/framework").json()
    pillar_scores = []
    # Infrastructure: 8 avg (80%) * 0.25 = 20
    # Policy: 7 avg (70%) * 0.25 = 17.5
    # Financing: 5 avg (50%) * 0.20 = 10
    # Human Capital: 3 avg (30%) * 0.15 = 4.5
    # Technology: 6 avg (60%) * 0.15 = 9
    score_map = {"infrastructure": 8, "policy": 7, "financing": 5, "human_capital": 3, "technology": 6}
    for p in fw["pillars"]:
        val = score_map.get(p["id"], 5)
        scores = {c["id"]: float(val) for c in p["criteria"]}
        pillar_scores.append({"pillar_id": p["id"], "scores": scores})

    payload = {
        "entity_name": "Mixed Country",
        "entity_type": "country",
        "country_iso2": "IN",
        "assessment_year": 2025,
        "pillar_scores": pillar_scores,
    }
    r = requests.post(f"{IRENA}/assess", json=payload)
    check("irena_mixed_200", r.status_code == 200)
    d = r.json()

    # Expected overall: (80*0.25 + 70*0.25 + 50*0.20 + 30*0.15 + 60*0.15) / 100 * 100 = 61.0
    check("irena_mixed_overall_61", d["overall_pct"] == 61.0, f"got {d['overall_pct']}")
    check("irena_mixed_rating_progressing", d["overall_rating"] == "Progressing", f"got {d['overall_rating']}")
    check("irena_mixed_readiness", d["transition_readiness"] == "On Track", f"got {d['transition_readiness']}")

    # Infrastructure should be Advanced, Human Capital Early Stage
    pr_map = {p["id"]: p for p in d["pillar_results"]}
    check("irena_mixed_infra_adv", pr_map["infrastructure"]["rating"] == "Advanced")
    check("irena_mixed_hc_early", pr_map["human_capital"]["rating"] == "Early Stage")

    # Gaps: human_capital (30%), financing (50% - boundary, not gap)
    # 30% -> all 5 criteria are gaps, 50% is exactly at boundary so not flagged
    hc_gaps = [g for g in d["gap_analysis"] if g["pillar"] == "Human Capital & Institutional Capacity"]
    check("irena_mixed_hc_5_gaps", len(hc_gaps) == 5, f"got {len(hc_gaps)}")


def test_pillar_detail_structure():
    """Each PillarResult has correct fields."""
    fw = requests.get(f"{IRENA}/framework").json()
    pillar_scores = []
    for p in fw["pillars"]:
        scores = {c["id"]: 5.0 for c in p["criteria"]}
        pillar_scores.append({"pillar_id": p["id"], "scores": scores})

    payload = {
        "entity_name": "Test",
        "entity_type": "country",
        "country_iso2": "US",
        "assessment_year": 2025,
        "pillar_scores": pillar_scores,
    }
    r = requests.post(f"{IRENA}/assess", json=payload)
    d = r.json()

    for pr in d["pillar_results"]:
        for fld in ["id", "name", "weight", "criteria", "raw_score", "max_score", "pct", "weighted_score", "rating"]:
            check(f"irena_pr_{pr['id']}_has_{fld}", fld in pr, f"missing {fld}")
        check(f"irena_pr_{pr['id']}_5_criteria", len(pr["criteria"]) == 5)
        for c in pr["criteria"]:
            for cf in ["id", "label", "score", "max_score", "pct"]:
                check(f"irena_cr_{c['id']}_has_{cf}", cf in c, f"missing {cf}")


if __name__ == "__main__":
    print("=" * 60)
    print("Session 20 -- Geothermal + IRENA Five Pillars Tests")
    print("=" * 60)

    print("\n-- Geothermal: Plant Types --")
    test_plant_types()

    print("\n-- Geothermal: Binary (Iceland) --")
    test_geothermal_binary()

    print("\n-- Geothermal: EGS (high seismicity) --")
    test_geothermal_egs()

    print("\n-- Geothermal: Flash (low temp) --")
    test_geothermal_flash_low_temp()

    print("\n-- Geothermal: Bad plant type --")
    test_geothermal_bad_type()

    print("\n-- IRENA: Framework --")
    test_framework()

    print("\n-- IRENA: Advanced (all 9s) --")
    test_assess_advanced()

    print("\n-- IRENA: Early Stage (all 2s) --")
    test_assess_early_stage()

    print("\n-- IRENA: Mixed scores --")
    test_assess_mixed()

    print("\n-- IRENA: Pillar detail structure --")
    test_pillar_detail_structure()

    print("\n" + "=" * 60)
    total = passed + failed
    print(f"Results: {passed}/{total} passed, {failed} failed")
    if failed:
        print("SOME TESTS FAILED")
        exit(1)
    else:
        print("ALL TESTS PASSED")
