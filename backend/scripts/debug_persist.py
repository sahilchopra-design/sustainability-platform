"""
Diagnostic script: test each _persist_* helper directly (v2 - with CAST fixes)
Run from backend/ directory:
    python -m scripts.debug_persist
"""
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from db.base import SessionLocal

db = SessionLocal()

# ────────────────────────────────────────────────────
# 1) Test scope3_assessments INSERT (CAST fix)
# ────────────────────────────────────────────────────
print("\n=== TEST 1: scope3_assessments INSERT ===")
try:
    sql = """
        INSERT INTO scope3_assessments
        (entity_name, reporting_year, calculation_approach,
         total_scope3_tco2e, categories_included,
         hotspot_summary, validation_summary, status,
         cat1_purchased_goods_tco2e, cat6_business_travel_tco2e)
        VALUES
        (:entity_name, :reporting_year, :approach,
         :total_scope3, CAST(:categories_included AS jsonb),
         CAST(:hotspot_summary AS jsonb), CAST(:validation_summary AS jsonb), 'draft',
         :cat1_purchased_goods_tco2e, :cat6_business_travel_tco2e)
        RETURNING id::text
    """
    params = {
        "entity_name": "DEBUG_TEST_ENTITY",
        "reporting_year": 2024,
        "approach": "activity_based",
        "total_scope3": 1234.5678,
        "categories_included": json.dumps([1, 6]),
        "hotspot_summary": json.dumps([]),
        "validation_summary": json.dumps({"is_valid": True}),
        "cat1_purchased_goods_tco2e": 800.0,
        "cat6_business_travel_tco2e": 434.5678,
    }
    row = db.execute(text(sql), params).fetchone()
    assessment_id = row[0]
    print(f"  OK: scope3_assessments id = {assessment_id}")
    db.rollback()
except Exception as e:
    db.rollback()
    print(f"  FAIL: {type(e).__name__}: {e}")

# ────────────────────────────────────────────────────
# 2) Test sbti_targets INSERT (sbti_status fix + CAST fix)
# ────────────────────────────────────────────────────
print("\n=== TEST 2: sbti_targets INSERT ===")
try:
    row = db.execute(text("""
        INSERT INTO sbti_targets
        (entity_name, target_type, sbti_pathway,
         base_year, base_year_total_tco2e,
         near_term_target_year, near_term_reduction_pct,
         near_term_target_tco2e, near_term_annual_reduction_rate_pct,
         validation_summary, sbti_status)
        VALUES
        (:entity_name, 'near_term', :pathway,
         :base_year, :base_total,
         :target_year, :reduction_pct,
         :target_tco2e, :cagr,
         CAST(:validation AS jsonb), 'committed')
        RETURNING id::text
    """), {
        "entity_name": "DEBUG_SBTI_ENTITY",
        "pathway": "1.5C_absolute",
        "base_year": 2020,
        "base_total": 50000.0,
        "target_year": 2030,
        "reduction_pct": 42.0,
        "target_tco2e": 29000.0,
        "cagr": 4.2,
        "validation": json.dumps({"is_valid": True}),
    }).fetchone()
    target_id = row[0]
    print(f"  OK: sbti_targets id = {target_id}")
    db.rollback()
except Exception as e:
    db.rollback()
    print(f"  FAIL: {type(e).__name__}: {e}")

# ────────────────────────────────────────────────────
# 3) Test data_centre_assessments INSERT (CAST fix)
# ────────────────────────────────────────────────────
print("\n=== TEST 3: data_centre_assessments INSERT ===")
try:
    row = db.execute(text("""
        INSERT INTO data_centre_assessments
        (facility_name, assessment_year,
         total_it_load_mw, annual_energy_consumption_mwh,
         pue, wue, renewable_energy_pct,
         has_renewable_ppa,
         grid_emission_factor_kgco2e_kwh,
         carbon_intensity_kgco2e_kwh_it,
         annual_co2e_tco2e,
         efficiency_score, efficiency_rating,
         improvement_targets, recommended_actions,
         validation_summary, status)
        VALUES
        (:name, :yr,
         :it_load, :energy_mwh,
         :pue, :wue, :renewable_pct,
         :has_ppa,
         :grid_ef,
         :ci,
         :co2e,
         :score, :rating,
         CAST(:improvement AS jsonb), CAST(:recommended AS jsonb),
         CAST(:validation AS jsonb), 'draft')
        RETURNING id::text
    """), {
        "name": "DEBUG_DC_TEST",
        "yr": 2025,
        "it_load": 10.0,
        "energy_mwh": 50000.0,
        "pue": 1.35,
        "wue": 1.2,
        "renewable_pct": 60.0,
        "has_ppa": True,
        "grid_ef": 0.207,
        "ci": 0.112,
        "co2e": 4140.0,
        "score": 72.5,
        "rating": "B",
        "improvement": json.dumps([]),
        "recommended": json.dumps([]),
        "validation": json.dumps({"is_valid": True}),
    }).fetchone()
    print(f"  OK: data_centre_assessments id = {row[0]}")
    db.rollback()
except Exception as e:
    db.rollback()
    print(f"  FAIL: {type(e).__name__}: {e}")

# ────────────────────────────────────────────────────
# 4) Test cat_risk_assessments INSERT (CAST fix)
# ────────────────────────────────────────────────────
print("\n=== TEST 4: cat_risk_assessments INSERT ===")
try:
    row = db.execute(text("""
        INSERT INTO cat_risk_assessments
        (property_reference, assessment_date, peril,
         property_value_gbp, aal_gbp,
         aal_pct_of_value, pml_gbp,
         return_period_curve,
         risk_score, risk_category,
         validation_summary, status)
        VALUES
        (:ref, CURRENT_DATE, :peril,
         :value, :aal,
         :aal_pct, :pml,
         CAST(:rp_curve AS jsonb),
         :risk_score, :risk_cat,
         CAST(:validation AS jsonb), 'draft')
        RETURNING id::text
    """), {
        "ref": "DEBUG_PROP_001",
        "peril": "flood",
        "value": 5000000.0,
        "aal": 17500.0,
        "aal_pct": 0.35,
        "pml": 250000.0,
        "rp_curve": json.dumps([{"return_period_yr": 100, "loss_gbp": 250000}]),
        "risk_score": 8.0,
        "risk_cat": "High",
        "validation": json.dumps({"is_valid": True}),
    }).fetchone()
    print(f"  OK: cat_risk_assessments id = {row[0]}")
    db.rollback()
except Exception as e:
    db.rollback()
    print(f"  FAIL: {type(e).__name__}: {e}")

# ────────────────────────────────────────────────────
# 5) Test power_plant_assessments INSERT (CAST fix)
# ────────────────────────────────────────────────────
print("\n=== TEST 5: power_plant_assessments INSERT ===")
try:
    row = db.execute(text("""
        INSERT INTO power_plant_assessments
        (plant_name, assessment_date,
         current_ci_gco2_kwh,
         iea_nze_2030_threshold_gco2_kwh,
         iea_nze_2050_threshold_gco2_kwh,
         implied_stranding_year,
         transition_capex_required_gbp,
         recommended_actions,
         validation_summary, status)
        VALUES
        (:name, CURRENT_DATE,
         :ci,
         :nze_2030, :nze_2050,
         :stranding_yr,
         :capex,
         CAST(:recommended AS jsonb),
         CAST(:validation AS jsonb), 'draft')
        RETURNING id::text
    """), {
        "name": "DEBUG_PLANT_TEST",
        "ci": 360.0,
        "nze_2030": 138.0,
        "nze_2050": 0.0,
        "stranding_yr": 2035,
        "capex": 180000000.0,
        "recommended": json.dumps([]),
        "validation": json.dumps({"is_valid": True}),
    }).fetchone()
    print(f"  OK: power_plant_assessments id = {row[0]}")
    db.rollback()
except Exception as e:
    db.rollback()
    print(f"  FAIL: {type(e).__name__}: {e}")

# ────────────────────────────────────────────────────
# 6) Test sbti_targets SELECT (sbti_status fix)
# ────────────────────────────────────────────────────
print("\n=== TEST 6: sbti_targets SELECT ===")
try:
    rows = db.execute(text("""
        SELECT id::text, entity_name, target_type, sbti_pathway,
               base_year, base_year_total_tco2e,
               near_term_target_year, near_term_reduction_pct,
               near_term_annual_reduction_rate_pct,
               sbti_status, created_at
        FROM sbti_targets
        ORDER BY created_at DESC
        LIMIT 5
    """)).fetchall()
    print(f"  OK: {len(rows)} rows returned")
    for r in rows:
        print(f"    {r[0][:8]}... entity={r[1]} type={r[2]} pathway={r[3]} status={r[9]}")
except Exception as e:
    db.rollback()
    print(f"  FAIL: {type(e).__name__}: {e}")

# ────────────────────────────────────────────────────
# 7) Test ecl_climate overlay INSERT (CAST fix)
# ────────────────────────────────────────────────────
print("\n=== TEST 7: ecl_climate_overlays INSERT ===")
try:
    row = db.execute(text("""
        INSERT INTO ecl_climate_overlays
        (assessment_id, exposure_id, sector, country_iso,
         exposure_type, pd_12m, pd_lifetime, pd_climate_adjusted,
         lgd, ead_gbp, ecl_12m_gbp, ecl_lifetime_gbp, ecl_recovery_adj_gbp,
         ifrs9_stage, sicr_triggered, SICR_triggers,
         physical_risk_score, transition_risk_score,
         climate_pd_uplift_bps, scenario_cashflows)
        VALUES
            (:aid, :iid, :sector, :country,
             'corporate_loan', :pd12, :pdlt, :pdcl,
             :lgd, :ead, :ecl12, :ecllt, :ecl_rec,
             :stage, :sicr, CAST(:triggers AS jsonb),
             :phys, :trans, :uplift_bps, CAST(:cashflows AS jsonb))
        RETURNING id::text
    """), {
        "aid": None,
        "iid": "TEST_EXP_001",
        "sector": "energy",
        "country": "GB",
        "pd12": 0.015,
        "pdlt": 0.08,
        "pdcl": 0.02,
        "lgd": 0.45,
        "ead": 1000000,
        "ecl12": 6750,
        "ecllt": 36000,
        "ecl_rec": 32000,
        "stage": 1,
        "sicr": False,
        "triggers": json.dumps([]),
        "phys": 3.5,
        "trans": 4.2,
        "uplift_bps": 50,
        "cashflows": json.dumps([]),
    }).fetchone()
    print(f"  OK: ecl_climate_overlays id = {row[0]}")
    db.rollback()
except Exception as e:
    db.rollback()
    print(f"  FAIL: {type(e).__name__}: {e}")

db.close()
print("\n=== ALL TESTS DONE ===")
