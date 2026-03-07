"""
Category C — Client Proprietary Data Intake
Routes: /api/v1/data-intake/*

Modules:
  C.1  Loan Portfolio Upload        /portfolio
  C.2  Counterparty Emissions       /counterparty
  C.3.1 Real Estate EUI Upload      /real-estate
  C.3.2 Shipping Fleet Upload       /shipping-fleet
  C.3.3 Steel Borrowers Entry       /steel-borrowers
  C.3.4 Project Finance Intake      /project-finance
  C.4  Internal Config              /internal-config
  C.5  Dashboard Status             /status
"""

import csv
import io
import math
from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import text

from db.base import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/data-intake", tags=["Data Intake"])


# ──────────────────────────────────────────────────────────────────────────────
# C.5  Dashboard Status
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/status")
def get_data_intake_status(db: Session = Depends(get_db)):
    """Return completion indicators for each data intake module + Data Hub reference counts."""
    try:
        # -- Client intake module counts --
        counts = {}
        tables = [
            ("loan_portfolio",    "di_loan_portfolio_uploads"),
            ("counterparty",      "di_counterparty_emissions"),
            ("real_estate",       "di_real_estate_assets"),
            ("shipping_fleet",    "di_shipping_fleet"),
            ("steel_borrowers",   "di_steel_borrowers"),
            ("project_finance",   "di_project_finance"),
            ("internal_config",   "di_internal_config"),
        ]
        for key, tbl in tables:
            row = db.execute(text(f"SELECT COUNT(*) FROM {tbl}")).fetchone()
            counts[key] = row[0] if row else 0

        modules = [
            {
                "id": "loan_portfolio",
                "label": "Loan Portfolio",
                "route": "/data-intake/portfolio",
                "count": counts["loan_portfolio"],
                "unit": "uploads",
                "status": "active" if counts["loan_portfolio"] > 0 else "empty",
                "priority": "P0",
            },
            {
                "id": "counterparty",
                "label": "Counterparty Emissions",
                "route": "/data-intake/counterparty",
                "count": counts["counterparty"],
                "unit": "counterparties",
                "status": "active" if counts["counterparty"] > 0 else "empty",
                "priority": "P0",
            },
            {
                "id": "real_estate",
                "label": "Real Estate EUI",
                "route": "/data-intake/real-estate",
                "count": counts["real_estate"],
                "unit": "assets",
                "status": "active" if counts["real_estate"] > 0 else "empty",
                "priority": "P1",
            },
            {
                "id": "shipping_fleet",
                "label": "Shipping Fleet",
                "route": "/data-intake/shipping-fleet",
                "count": counts["shipping_fleet"],
                "unit": "vessels",
                "status": "active" if counts["shipping_fleet"] > 0 else "empty",
                "priority": "P1",
            },
            {
                "id": "steel_borrowers",
                "label": "Steel Borrowers",
                "route": "/data-intake/steel-borrowers",
                "count": counts["steel_borrowers"],
                "unit": "borrowers",
                "status": "active" if counts["steel_borrowers"] > 0 else "empty",
                "priority": "P1",
            },
            {
                "id": "project_finance",
                "label": "Project Finance",
                "route": "/data-intake/project-finance",
                "count": counts["project_finance"],
                "unit": "projects",
                "status": "active" if counts["project_finance"] > 0 else "empty",
                "priority": "P1",
            },
            {
                "id": "internal_config",
                "label": "Internal Config",
                "route": "/data-intake/internal-config",
                "count": counts["internal_config"],
                "unit": "keys",
                "status": "configured" if counts["internal_config"] >= 8 else "empty",
                "priority": "P1",
            },
        ]

        # -- Data Hub reference data counts --
        dh_tables = [
            ("sbti_companies",        "dh_sbti_companies",        "SBTi Companies",            "companies",  "ESG"),
            ("ca100_assessments",     "dh_ca100_assessments",     "CA100+ Benchmark 2025",     "companies",  "ESG"),
            ("country_risk_indices",  "dh_country_risk_indices",  "Country Risk Indices",      "entries",    "Governance"),
            ("reference_data",        "dh_reference_data",        "Reference Data (Coal/Other)","entries",   "Energy"),
            ("crrem_pathways",        "dh_crrem_pathways",        "CRREM Pathways",            "pathways",   "Real Estate"),
            ("irena_lcoe",            "dh_irena_lcoe",            "IRENA LCOE",                "records",    "Energy"),
            ("grid_emission_factors", "dh_grid_emission_factors", "Grid Emission Factors",     "countries",  "Emissions"),
            ("controversy_scores",    "dh_controversy_scores",    "GDELT Controversy Scores",  "entities",   "ESG"),
            ("violation_tracker",     "dh_violation_tracker",     "Violation Tracker",         "violations", "Governance"),
            ("gdelt_events",          "dh_gdelt_events",          "GDELT Events",             "events",     "ESG"),
            ("application_kpis",      "dh_application_kpis",      "Application KPIs",         "kpis",       "Platform"),
        ]
        data_hub = []
        dh_total = 0
        for key, tbl, label, unit, category in dh_tables:
            try:
                row = db.execute(text(f"SELECT COUNT(*) FROM {tbl}")).fetchone()
                cnt = row[0] if row else 0
            except Exception:
                cnt = 0
            dh_total += cnt
            data_hub.append({
                "id": key,
                "label": label,
                "table": tbl,
                "count": cnt,
                "unit": unit,
                "category": category,
                "status": "active" if cnt > 0 else "empty",
            })

        # -- Country Risk breakdown (sub-indices) --
        cri_breakdown = []
        try:
            rows = db.execute(text(
                "SELECT index_name, COUNT(*) FROM dh_country_risk_indices GROUP BY index_name ORDER BY index_name"
            )).fetchall()
            cri_breakdown = [{"index": r[0], "count": r[1]} for r in rows]
        except Exception:
            pass

        # -- Summary stats --
        active_modules = [m for m in modules if m["status"] in ("active", "configured")]
        total_client = sum(m["count"] for m in modules)
        completion_pct = round(len(active_modules) / len(modules) * 100) if modules else 0
        dh_active = len([d for d in data_hub if d["status"] == "active"])

        return {
            "modules": modules,
            "data_hub": data_hub,
            "country_risk_breakdown": cri_breakdown,
            "summary": {
                "total_client_records": total_client,
                "total_reference_records": dh_total,
                "client_modules_active": len(active_modules),
                "client_modules_total": len(modules),
                "client_completion_pct": completion_pct,
                "dh_sources_active": dh_active,
                "dh_sources_total": len(data_hub),
                "dh_completion_pct": round(dh_active / len(data_hub) * 100) if data_hub else 0,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────────────────────────────────────
# C.1  Loan Portfolio Upload
# ──────────────────────────────────────────────────────────────────────────────

LOAN_CSV_COLUMNS = [
    "counterparty_id", "counterparty_name", "instrument_type",
    "outstanding_amount", "currency", "sector_gics", "country_iso2",
    "maturity_date", "stage_ifrs9", "pd_1yr", "lgd",
    "reported_emissions_tco2e", "pcaf_dqs", "data_year",
]

VALID_INSTRUMENT_TYPES = {"loan", "bond", "equity", "guarantee"}
VALID_STAGES = {"1", "2", "3"}
VALID_DQS = {"1", "2", "3", "4", "5"}


@router.get("/portfolio/template")
def download_portfolio_template():
    """Return a CSV template for loan portfolio upload."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(LOAN_CSV_COLUMNS)
    writer.writerow([
        "CP001", "Acme Corp", "loan", "5000000", "USD",
        "4010", "GB", "2028-12-31", "1", "0.012", "0.45",
        "125000", "2", "2024",
    ])
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=loan_portfolio_template.csv"},
    )


@router.get("/portfolio")
def list_portfolio_uploads(db: Session = Depends(get_db)):
    """List all portfolio upload jobs."""
    rows = db.execute(text(
        "SELECT id, upload_name, filename, status, total_rows, valid_rows, error_rows, "
        "uploaded_by, notes, created_at FROM di_loan_portfolio_uploads ORDER BY created_at DESC LIMIT 100"
    )).fetchall()
    return [dict(r._mapping) for r in rows]


@router.post("/portfolio/upload")
async def upload_portfolio_csv(
    file: UploadFile = File(...),
    upload_name: str = "Portfolio Upload",
    uploaded_by: str = "system",
    db: Session = Depends(get_db),
):
    """Parse and ingest a loan portfolio CSV file."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    content = await file.read()
    text_content = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text_content))

    # Create upload job
    result = db.execute(text(
        "INSERT INTO di_loan_portfolio_uploads "
        "(upload_name, filename, status, uploaded_by) "
        "VALUES (:name, :fname, 'processing', :by) RETURNING id"
    ), {"name": upload_name, "fname": file.filename, "by": uploaded_by})
    upload_id = result.fetchone()[0]
    db.commit()

    total, valid, errors = 0, 0, 0
    for row in reader:
        total += 1
        errs = []

        # Validate
        inst = (row.get("instrument_type") or "").strip().lower()
        if inst not in VALID_INSTRUMENT_TYPES:
            errs.append(f"Invalid instrument_type: {inst}")

        stage = (row.get("stage_ifrs9") or "").strip()
        if stage and stage not in VALID_STAGES:
            errs.append(f"Invalid stage_ifrs9: {stage}")

        dqs = (row.get("pcaf_dqs") or "").strip()
        if dqs and dqs not in VALID_DQS:
            errs.append(f"Invalid pcaf_dqs: {dqs}")

        try:
            outstanding = float(row.get("outstanding_amount") or 0)
        except ValueError:
            errs.append("outstanding_amount must be numeric")
            outstanding = None

        if errs:
            errors += 1
        else:
            valid += 1

        def safe_float(val):
            try:
                return float(val) if val and val.strip() else None
            except (ValueError, AttributeError):
                return None

        def safe_int(val):
            try:
                return int(val) if val and str(val).strip() else None
            except (ValueError, AttributeError):
                return None

        db.execute(text(
            "INSERT INTO di_loan_portfolio_rows "
            "(upload_id, counterparty_id, counterparty_name, instrument_type, "
            " outstanding_amount, currency, sector_gics, country_iso2, "
            " stage_ifrs9, pd_1yr, lgd, reported_emissions_tco2e, pcaf_dqs, "
            " data_year, is_valid, validation_errors) "
            "VALUES (:uid, :cp_id, :cp_name, :inst, :amt, :ccy, :sector, "
            " :cty, :stage, :pd, :lgd, :emi, :dqs, :yr, :valid, :errs::jsonb)"
        ), {
            "uid": upload_id,
            "cp_id": (row.get("counterparty_id") or "").strip(),
            "cp_name": (row.get("counterparty_name") or "").strip(),
            "inst": inst,
            "amt": outstanding,
            "ccy": (row.get("currency") or "USD").strip(),
            "sector": (row.get("sector_gics") or "").strip(),
            "cty": (row.get("country_iso2") or "").strip(),
            "stage": safe_int(stage) if stage else None,
            "pd": safe_float(row.get("pd_1yr")),
            "lgd": safe_float(row.get("lgd")),
            "emi": safe_float(row.get("reported_emissions_tco2e")),
            "dqs": safe_int(dqs) if dqs else None,
            "yr": safe_int(row.get("data_year")),
            "valid": len(errs) == 0,
            "errs": str(errs) if errs else "[]",
        })

    # Update job status
    db.execute(text(
        "UPDATE di_loan_portfolio_uploads SET status='complete', "
        "total_rows=:total, valid_rows=:valid, error_rows=:errs "
        "WHERE id=:id"
    ), {"total": total, "valid": valid, "errs": errors, "id": upload_id})
    db.commit()

    return {
        "upload_id": upload_id,
        "status": "complete",
        "total_rows": total,
        "valid_rows": valid,
        "error_rows": errors,
    }


@router.get("/portfolio/{upload_id}/rows")
def get_portfolio_rows(upload_id: int, db: Session = Depends(get_db)):
    """Return individual rows for a portfolio upload."""
    rows = db.execute(text(
        "SELECT * FROM di_loan_portfolio_rows WHERE upload_id=:id ORDER BY id LIMIT 500"
    ), {"id": upload_id}).fetchall()
    return [dict(r._mapping) for r in rows]


# ──────────────────────────────────────────────────────────────────────────────
# C.2  Counterparty Emissions Wizard
# ──────────────────────────────────────────────────────────────────────────────

DQS_MAP = {
    "direct_measurement": 1,
    "audited_report": 2,
    "self_reported": 3,
    "sector_average": 4,
    "estimated": 5,
}


class CounterpartyEmissionsIn(BaseModel):
    counterparty_id: str
    counterparty_name: Optional[str] = None
    reporting_year: int
    scope1_tco2e: Optional[float] = None
    scope2_market_tco2e: Optional[float] = None
    scope2_location_tco2e: Optional[float] = None
    scope3_total_tco2e: Optional[float] = None
    scope3_cat1_purchased_goods: Optional[float] = None
    scope3_cat11_use_of_sold_products: Optional[float] = None
    scope3_cat15_investments: Optional[float] = None
    data_source_type: str = "self_reported"
    evidence_url: Optional[str] = None
    assurance_level: Optional[str] = "none"
    notes: Optional[str] = None


@router.get("/counterparty")
def list_counterparty_emissions(db: Session = Depends(get_db)):
    rows = db.execute(text(
        "SELECT id, counterparty_id, counterparty_name, reporting_year, "
        "scope1_tco2e, scope2_market_tco2e, scope3_total_tco2e, "
        "pcaf_dqs, data_source_type, assurance_level, created_at "
        "FROM di_counterparty_emissions ORDER BY created_at DESC LIMIT 500"
    )).fetchall()
    return [dict(r._mapping) for r in rows]


@router.post("/counterparty")
def upsert_counterparty_emissions(payload: CounterpartyEmissionsIn, db: Session = Depends(get_db)):
    """Upsert counterparty emissions. DQS is derived from data_source_type."""
    dqs = DQS_MAP.get(payload.data_source_type, 3)
    db.execute(text("""
        INSERT INTO di_counterparty_emissions
          (counterparty_id, counterparty_name, reporting_year,
           scope1_tco2e, scope2_market_tco2e, scope2_location_tco2e,
           scope3_total_tco2e, scope3_cat1_purchased_goods,
           scope3_cat11_use_of_sold_products, scope3_cat15_investments,
           data_source_type, pcaf_dqs, evidence_url, assurance_level, notes)
        VALUES
          (:cp_id, :cp_name, :yr,
           :s1, :s2m, :s2l, :s3, :s3c1, :s3c11, :s3c15,
           :dst, :dqs, :url, :assurance, :notes)
        ON CONFLICT (counterparty_id, reporting_year)
        DO UPDATE SET
          scope1_tco2e = EXCLUDED.scope1_tco2e,
          scope2_market_tco2e = EXCLUDED.scope2_market_tco2e,
          scope2_location_tco2e = EXCLUDED.scope2_location_tco2e,
          scope3_total_tco2e = EXCLUDED.scope3_total_tco2e,
          scope3_cat1_purchased_goods = EXCLUDED.scope3_cat1_purchased_goods,
          scope3_cat11_use_of_sold_products = EXCLUDED.scope3_cat11_use_of_sold_products,
          scope3_cat15_investments = EXCLUDED.scope3_cat15_investments,
          data_source_type = EXCLUDED.data_source_type,
          pcaf_dqs = EXCLUDED.pcaf_dqs,
          evidence_url = EXCLUDED.evidence_url,
          assurance_level = EXCLUDED.assurance_level,
          notes = EXCLUDED.notes,
          updated_at = NOW()
    """), {
        "cp_id": payload.counterparty_id,
        "cp_name": payload.counterparty_name,
        "yr": payload.reporting_year,
        "s1": payload.scope1_tco2e,
        "s2m": payload.scope2_market_tco2e,
        "s2l": payload.scope2_location_tco2e,
        "s3": payload.scope3_total_tco2e,
        "s3c1": payload.scope3_cat1_purchased_goods,
        "s3c11": payload.scope3_cat11_use_of_sold_products,
        "s3c15": payload.scope3_cat15_investments,
        "dst": payload.data_source_type,
        "dqs": dqs,
        "url": payload.evidence_url,
        "assurance": payload.assurance_level,
        "notes": payload.notes,
    })
    db.commit()
    return {"status": "ok", "pcaf_dqs": dqs}


@router.delete("/counterparty/{record_id}")
def delete_counterparty_emission(record_id: int, db: Session = Depends(get_db)):
    db.execute(text("DELETE FROM di_counterparty_emissions WHERE id=:id"), {"id": record_id})
    db.commit()
    return {"status": "deleted"}


# ──────────────────────────────────────────────────────────────────────────────
# C.3.1  Real Estate EUI Upload
# ──────────────────────────────────────────────────────────────────────────────

RE_CSV_COLUMNS = [
    "asset_ref", "property_name", "address_line1", "city", "country_iso2",
    "property_type", "gross_floor_area_m2", "eui_kwh_m2_yr",
    "crrem_pathway_2030", "crrem_pathway_2050", "stranding_year",
    "energy_star_score", "gresb_score", "data_year",
]


@router.get("/real-estate/template")
def download_real_estate_template():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(RE_CSV_COLUMNS)
    writer.writerow([
        "RE001", "Victoria Tower", "1 Victoria St", "London", "GB",
        "office", "12500", "185", "120", "60", "2031",
        "78", "72", "2024",
    ])
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=real_estate_eui_template.csv"},
    )


@router.get("/real-estate")
def list_real_estate_assets(db: Session = Depends(get_db)):
    rows = db.execute(text(
        "SELECT * FROM di_real_estate_assets ORDER BY created_at DESC LIMIT 1000"
    )).fetchall()
    return [dict(r._mapping) for r in rows]


@router.post("/real-estate/upload")
async def upload_real_estate_csv(
    file: UploadFile = File(...),
    upload_batch: str = "",
    db: Session = Depends(get_db),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))

    def sf(v):
        try:
            return float(v) if v and str(v).strip() else None
        except (ValueError, AttributeError):
            return None

    def si(v):
        try:
            return int(float(v)) if v and str(v).strip() else None
        except (ValueError, AttributeError):
            return None

    inserted, flagged = 0, 0
    for row in reader:
        eui = sf(row.get("eui_kwh_m2_yr"))
        if eui and eui > 800:
            flagged += 1  # high EUI flagged but still inserted

        db.execute(text("""
            INSERT INTO di_real_estate_assets
              (asset_ref, property_name, address_line1, city, country_iso2,
               property_type, gross_floor_area_m2, eui_kwh_m2_yr,
               crrem_pathway_2030, crrem_pathway_2050, stranding_year,
               energy_star_score, gresb_score, data_year, upload_batch)
            VALUES
              (:ref, :name, :addr, :city, :cty, :ptype, :gfa, :eui,
               :cr30, :cr50, :sy, :es, :gr, :yr, :batch)
        """), {
            "ref": row.get("asset_ref", ""),
            "name": row.get("property_name", ""),
            "addr": row.get("address_line1", ""),
            "city": row.get("city", ""),
            "cty": row.get("country_iso2", ""),
            "ptype": row.get("property_type", ""),
            "gfa": sf(row.get("gross_floor_area_m2")),
            "eui": eui,
            "cr30": sf(row.get("crrem_pathway_2030")),
            "cr50": sf(row.get("crrem_pathway_2050")),
            "sy": si(row.get("stranding_year")),
            "es": si(row.get("energy_star_score")),
            "gr": si(row.get("gresb_score")),
            "yr": si(row.get("data_year")),
            "batch": upload_batch,
        })
        inserted += 1

    db.commit()
    return {"inserted": inserted, "flagged_high_eui": flagged}


# ──────────────────────────────────────────────────────────────────────────────
# C.3.2  Shipping Fleet Upload
# ──────────────────────────────────────────────────────────────────────────────

FLEET_CSV_COLUMNS = [
    "vessel_imo", "vessel_name", "vessel_type", "flag_state",
    "dwt_tonnes", "gross_tonnage", "build_year", "propulsion_type",
    "annual_fuel_consumption_mt", "annual_co2_tco2e",
    "annual_distance_nm", "cii_rating", "cii_score", "eexi_value", "data_year",
]


@router.get("/shipping-fleet/template")
def download_fleet_template():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(FLEET_CSV_COLUMNS)
    writer.writerow([
        "9000001", "MV Atlantic Star", "bulk_carrier", "PA",
        "75000", "42000", "2015", "HFO",
        "8200", "25800", "95000", "C", "8.2", "14.5", "2024",
    ])
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=shipping_fleet_template.csv"},
    )


@router.get("/shipping-fleet")
def list_fleet(db: Session = Depends(get_db)):
    rows = db.execute(text(
        "SELECT * FROM di_shipping_fleet ORDER BY vessel_imo LIMIT 2000"
    )).fetchall()
    return [dict(r._mapping) for r in rows]


@router.post("/shipping-fleet/upload")
async def upload_fleet_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))

    def sf(v):
        try:
            return float(v) if v and str(v).strip() else None
        except (ValueError, AttributeError):
            return None

    def si(v):
        try:
            return int(float(v)) if v and str(v).strip() else None
        except (ValueError, AttributeError):
            return None

    upserted = 0
    for row in reader:
        imo = (row.get("vessel_imo") or "").strip()
        if not imo:
            continue
        db.execute(text("""
            INSERT INTO di_shipping_fleet
              (vessel_imo, vessel_name, vessel_type, flag_state,
               dwt_tonnes, gross_tonnage, build_year, propulsion_type,
               annual_fuel_consumption_mt, annual_co2_tco2e,
               annual_distance_nm, cii_rating, cii_score, eexi_value, data_year)
            VALUES
              (:imo, :name, :vtype, :flag,
               :dwt, :gt, :yr_b, :prop,
               :fuel, :co2, :dist, :cii_r, :cii_s, :eexi, :yr)
            ON CONFLICT (vessel_imo) DO UPDATE SET
              vessel_name = EXCLUDED.vessel_name,
              annual_co2_tco2e = EXCLUDED.annual_co2_tco2e,
              cii_rating = EXCLUDED.cii_rating,
              cii_score = EXCLUDED.cii_score,
              data_year = EXCLUDED.data_year,
              updated_at = NOW()
        """), {
            "imo": imo,
            "name": row.get("vessel_name", ""),
            "vtype": row.get("vessel_type", ""),
            "flag": row.get("flag_state", ""),
            "dwt": sf(row.get("dwt_tonnes")),
            "gt": sf(row.get("gross_tonnage")),
            "yr_b": si(row.get("build_year")),
            "prop": row.get("propulsion_type", ""),
            "fuel": sf(row.get("annual_fuel_consumption_mt")),
            "co2": sf(row.get("annual_co2_tco2e")),
            "dist": sf(row.get("annual_distance_nm")),
            "cii_r": row.get("cii_rating", ""),
            "cii_s": sf(row.get("cii_score")),
            "eexi": sf(row.get("eexi_value")),
            "yr": si(row.get("data_year")),
        })
        upserted += 1

    db.commit()
    return {"upserted": upserted}


# ──────────────────────────────────────────────────────────────────────────────
# C.3.3  Steel Borrowers Entry
# ──────────────────────────────────────────────────────────────────────────────

# CO2 intensities tCO2/tCS by production route (GCCA / worldsteel)
CO2_INTENSITY_BF_BOF = 2.32   # blast furnace – basic oxygen furnace
CO2_INTENSITY_EAF = 0.67      # electric arc furnace (global average grid)
CO2_INTENSITY_DRI = 1.43      # direct reduced iron (gas-based)


class SteelBorrowerIn(BaseModel):
    borrower_id: str
    borrower_name: Optional[str] = None
    country_iso2: Optional[str] = None
    crude_steel_production_mt: Optional[float] = None
    bf_bof_share_pct: float = 0.0
    eaf_share_pct: float = 0.0
    dri_share_pct: float = 0.0
    energy_source_mix: Optional[Dict[str, Any]] = None
    sbti_committed: bool = False
    data_year: Optional[int] = None
    notes: Optional[str] = None


@router.get("/steel-borrowers")
def list_steel_borrowers(db: Session = Depends(get_db)):
    rows = db.execute(text(
        "SELECT * FROM di_steel_borrowers ORDER BY borrower_name LIMIT 500"
    )).fetchall()
    return [dict(r._mapping) for r in rows]


@router.post("/steel-borrowers")
def upsert_steel_borrower(payload: SteelBorrowerIn, db: Session = Depends(get_db)):
    """Validate production route shares and compute blended CO2 intensity."""
    total_share = payload.bf_bof_share_pct + payload.eaf_share_pct + payload.dri_share_pct
    if total_share > 100.1:
        raise HTTPException(
            status_code=422,
            detail=f"BF-BOF + EAF + DRI shares sum to {total_share:.1f}% — must be ≤ 100%.",
        )

    # Blended CO2 intensity (weighted average)
    blended = (
        (payload.bf_bof_share_pct / 100) * CO2_INTENSITY_BF_BOF
        + (payload.eaf_share_pct / 100) * CO2_INTENSITY_EAF
        + (payload.dri_share_pct / 100) * CO2_INTENSITY_DRI
    )

    total_co2 = None
    if payload.crude_steel_production_mt:
        total_co2 = blended * payload.crude_steel_production_mt

    import json
    energy_json = json.dumps(payload.energy_source_mix) if payload.energy_source_mix else None

    db.execute(text("""
        INSERT INTO di_steel_borrowers
          (borrower_id, borrower_name, country_iso2, crude_steel_production_mt,
           bf_bof_share_pct, eaf_share_pct, dri_share_pct,
           blended_co2_intensity_tco2_tcs, total_co2_tco2e,
           energy_source_mix, sbti_committed, data_year, notes)
        VALUES
          (:bid, :bname, :cty, :prod,
           :bof, :eaf, :dri,
           :blended, :total,
           :emix::jsonb, :sbti, :yr, :notes)
        ON CONFLICT (borrower_id) DO UPDATE SET
          borrower_name = EXCLUDED.borrower_name,
          crude_steel_production_mt = EXCLUDED.crude_steel_production_mt,
          bf_bof_share_pct = EXCLUDED.bf_bof_share_pct,
          eaf_share_pct = EXCLUDED.eaf_share_pct,
          dri_share_pct = EXCLUDED.dri_share_pct,
          blended_co2_intensity_tco2_tcs = EXCLUDED.blended_co2_intensity_tco2_tcs,
          total_co2_tco2e = EXCLUDED.total_co2_tco2e,
          energy_source_mix = EXCLUDED.energy_source_mix,
          sbti_committed = EXCLUDED.sbti_committed,
          data_year = EXCLUDED.data_year,
          notes = EXCLUDED.notes,
          updated_at = NOW()
    """), {
        "bid": payload.borrower_id,
        "bname": payload.borrower_name,
        "cty": payload.country_iso2,
        "prod": payload.crude_steel_production_mt,
        "bof": payload.bf_bof_share_pct,
        "eaf": payload.eaf_share_pct,
        "dri": payload.dri_share_pct,
        "blended": round(blended, 4),
        "total": round(total_co2, 2) if total_co2 else None,
        "emix": energy_json,
        "sbti": payload.sbti_committed,
        "yr": payload.data_year,
        "notes": payload.notes,
    })
    db.commit()
    return {
        "status": "ok",
        "blended_co2_intensity_tco2_tcs": round(blended, 4),
        "total_co2_tco2e": round(total_co2, 2) if total_co2 else None,
    }


@router.delete("/steel-borrowers/{borrower_id}")
def delete_steel_borrower(borrower_id: str, db: Session = Depends(get_db)):
    db.execute(text("DELETE FROM di_steel_borrowers WHERE borrower_id=:id"), {"id": borrower_id})
    db.commit()
    return {"status": "deleted"}


# ──────────────────────────────────────────────────────────────────────────────
# C.3.4  Project Finance Intake
# ──────────────────────────────────────────────────────────────────────────────

class ProjectFinanceIn(BaseModel):
    project_ref: Optional[str] = None
    project_name: str
    project_type: Optional[str] = None
    country_iso2: Optional[str] = None
    capacity_mw: Optional[float] = None
    total_capex_musd: Optional[float] = None
    debt_musd: Optional[float] = None
    equity_musd: Optional[float] = None
    annual_revenue_musd: Optional[float] = None
    annual_opex_musd: Optional[float] = None
    annual_debt_service_musd: Optional[float] = None
    project_life_yrs: Optional[int] = 25
    capacity_factor_pct: Optional[float] = None
    include_carbon_credits: bool = False
    carbon_credit_price_usd: Optional[float] = None
    annual_co2_avoided_tco2e: Optional[float] = None
    discount_rate_pct: Optional[float] = 8.0
    equator_principles_category: Optional[str] = None
    paris_alignment_status: Optional[str] = "under_review"
    notes: Optional[str] = None


def _compute_project_metrics(p: ProjectFinanceIn):
    """Compute preliminary DSCR, LCOE, equity IRR."""
    dscr = None
    lcoe = None
    irr = None

    # DSCR = EBITDA / Debt Service
    if p.annual_revenue_musd and p.annual_opex_musd and p.annual_debt_service_musd:
        ebitda = p.annual_revenue_musd - p.annual_opex_musd
        if p.annual_debt_service_musd > 0:
            dscr = round(ebitda / p.annual_debt_service_musd, 3)

    # LCOE = (CapEx * FCR + OpEx) / AEP
    #   FCR = discount_rate / (1 - (1+r)^-n)
    if (p.total_capex_musd and p.annual_opex_musd and p.capacity_mw
            and p.capacity_factor_pct and p.project_life_yrs and p.discount_rate_pct):
        r = (p.discount_rate_pct or 8.0) / 100
        n = p.project_life_yrs
        if r > 0:
            fcr = r / (1 - (1 + r) ** -n)
        else:
            fcr = 1 / n
        annual_energy_gwh = p.capacity_mw * (p.capacity_factor_pct / 100) * 8760 / 1000
        if annual_energy_gwh > 0:
            annual_cost_musd = p.total_capex_musd * fcr + p.annual_opex_musd
            lcoe = round((annual_cost_musd * 1_000_000) / (annual_energy_gwh * 1000), 2)  # USD/MWh

    # Equity IRR: simplified NPV-based estimate using Newton's method
    if (p.equity_musd and p.annual_revenue_musd and p.annual_opex_musd
            and p.annual_debt_service_musd and p.project_life_yrs):
        annual_equity_cf = p.annual_revenue_musd - p.annual_opex_musd - p.annual_debt_service_musd
        if p.include_carbon_credits and p.annual_co2_avoided_tco2e and p.carbon_credit_price_usd:
            annual_equity_cf += (p.annual_co2_avoided_tco2e * p.carbon_credit_price_usd) / 1_000_000

        # Binary search for IRR
        lo, hi = -0.5, 5.0
        for _ in range(100):
            mid = (lo + hi) / 2
            npv = -p.equity_musd + sum(
                annual_equity_cf / ((1 + mid) ** t) for t in range(1, p.project_life_yrs + 1)
            )
            if abs(npv) < 0.0001:
                break
            if npv > 0:
                lo = mid
            else:
                hi = mid
        irr_val = (lo + hi) / 2
        if -0.5 < irr_val < 5.0:
            irr = round(irr_val * 100, 2)

    return dscr, lcoe, irr


@router.get("/project-finance")
def list_projects(db: Session = Depends(get_db)):
    rows = db.execute(text(
        "SELECT id, project_ref, project_name, project_type, country_iso2, "
        "capacity_mw, total_capex_musd, status, paris_alignment_status, "
        "preliminary_dscr, preliminary_lcoe_usd_mwh, preliminary_equity_irr_pct, "
        "created_at FROM di_project_finance ORDER BY created_at DESC LIMIT 200"
    )).fetchall()
    return [dict(r._mapping) for r in rows]


@router.post("/project-finance")
def create_project_finance(payload: ProjectFinanceIn, db: Session = Depends(get_db)):
    """Save project finance record. Computes preliminary DSCR, LCOE and equity IRR."""
    dscr, lcoe, irr = _compute_project_metrics(payload)

    import uuid
    ref = payload.project_ref or f"PF-{uuid.uuid4().hex[:8].upper()}"

    result = db.execute(text("""
        INSERT INTO di_project_finance
          (project_ref, project_name, project_type, country_iso2,
           capacity_mw, total_capex_musd, debt_musd, equity_musd,
           annual_revenue_musd, annual_opex_musd, annual_debt_service_musd,
           project_life_yrs, capacity_factor_pct,
           include_carbon_credits, carbon_credit_price_usd, annual_co2_avoided_tco2e,
           discount_rate_pct, equator_principles_category, paris_alignment_status,
           preliminary_dscr, preliminary_lcoe_usd_mwh, preliminary_equity_irr_pct,
           notes)
        VALUES
          (:ref, :name, :ptype, :cty,
           :cap, :capex, :debt, :eq,
           :rev, :opex, :ds,
           :life, :cf,
           :cc, :cc_price, :co2_avoid,
           :dr, :ep_cat, :paris,
           :dscr, :lcoe, :irr,
           :notes)
        RETURNING id
    """), {
        "ref": ref,
        "name": payload.project_name,
        "ptype": payload.project_type,
        "cty": payload.country_iso2,
        "cap": payload.capacity_mw,
        "capex": payload.total_capex_musd,
        "debt": payload.debt_musd,
        "eq": payload.equity_musd,
        "rev": payload.annual_revenue_musd,
        "opex": payload.annual_opex_musd,
        "ds": payload.annual_debt_service_musd,
        "life": payload.project_life_yrs,
        "cf": payload.capacity_factor_pct,
        "cc": payload.include_carbon_credits,
        "cc_price": payload.carbon_credit_price_usd,
        "co2_avoid": payload.annual_co2_avoided_tco2e,
        "dr": payload.discount_rate_pct,
        "ep_cat": payload.equator_principles_category,
        "paris": payload.paris_alignment_status,
        "dscr": dscr,
        "lcoe": lcoe,
        "irr": irr,
        "notes": payload.notes,
    })
    new_id = result.fetchone()[0]
    db.commit()

    return {
        "id": new_id,
        "project_ref": ref,
        "status": "ok",
        "preliminary_dscr": dscr,
        "preliminary_lcoe_usd_mwh": lcoe,
        "preliminary_equity_irr_pct": irr,
    }


@router.get("/project-finance/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db)):
    row = db.execute(text(
        "SELECT * FROM di_project_finance WHERE id=:id"
    ), {"id": project_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found.")
    return dict(row._mapping)


@router.delete("/project-finance/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    db.execute(text("DELETE FROM di_project_finance WHERE id=:id"), {"id": project_id})
    db.commit()
    return {"status": "deleted"}


# ──────────────────────────────────────────────────────────────────────────────
# C.4  Internal Config
# ──────────────────────────────────────────────────────────────────────────────

class ConfigUpdateIn(BaseModel):
    config_value: str
    updated_by: Optional[str] = "system"


@router.get("/internal-config")
def get_all_config(db: Session = Depends(get_db)):
    rows = db.execute(text(
        "SELECT config_key, config_value, display_name, description, "
        "config_group, data_type, updated_by, updated_at "
        "FROM di_internal_config ORDER BY config_group, config_key"
    )).fetchall()
    return [dict(r._mapping) for r in rows]


@router.put("/internal-config/{key}")
def update_config(key: str, payload: ConfigUpdateIn, db: Session = Depends(get_db)):
    existing = db.execute(text(
        "SELECT id FROM di_internal_config WHERE config_key=:k"
    ), {"k": key}).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail=f"Config key '{key}' not found.")
    db.execute(text(
        "UPDATE di_internal_config SET config_value=:v, updated_by=:by, updated_at=NOW() "
        "WHERE config_key=:k"
    ), {"v": payload.config_value, "by": payload.updated_by, "k": key})
    db.commit()
    return {"status": "ok", "config_key": key, "config_value": payload.config_value}


# ──────────────────────────────────────────────────────────────────────────────
# C.COMPUTE  PCAF Financed Emissions — computed from di_ intake tables
# Resolves: Category C data → PCAF computation engine
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/pcaf-summary")
def get_pcaf_summary(data_year: Optional[int] = None, db: Session = Depends(get_db)):
    """
    Compute PCAF financed emissions from the loan portfolio rows and
    counterparty emissions tables.  Returns sector breakdown, DQS distribution,
    total financed emissions, and WACI.

    PCAF Attribution Factor (AF) = outstanding_amount / total_outstanding_by_cp
    Financed Emissions = AF × (scope1 + scope2_market) per counterparty
    WACI = Σ(outstanding_amount × emissions_intensity) / total_portfolio
    """
    year_filter = "AND r.data_year = :yr" if data_year else ""

    # 1. Load all valid loan rows (most-recent upload per counterparty)
    rows = db.execute(text(f"""
        SELECT
            r.counterparty_id,
            r.counterparty_name,
            r.sector_gics,
            r.outstanding_amount,
            r.pcaf_dqs,
            r.reported_emissions_tco2e,
            r.stage_ifrs9
        FROM di_loan_portfolio_rows r
        WHERE r.is_valid = TRUE {year_filter}
        ORDER BY r.counterparty_id, r.id DESC
    """), {"yr": data_year} if data_year else {}).fetchall()

    # 2. Load counterparty emissions (best available per counterparty)
    cp_emissions = db.execute(text(f"""
        SELECT
            counterparty_id,
            reporting_year,
            scope1_tco2e,
            scope2_market_tco2e,
            scope3_total_tco2e,
            pcaf_dqs,
            data_source_type
        FROM di_counterparty_emissions
        {("WHERE reporting_year = :yr" if data_year else "")}
        ORDER BY counterparty_id, pcaf_dqs ASC, reporting_year DESC
    """), {"yr": data_year} if data_year else {}).fetchall()

    # Build lookup: counterparty_id → best emissions record (lowest DQS = highest quality)
    cp_map: Dict[str, Any] = {}
    for ce in cp_emissions:
        cid = ce[0]
        if cid not in cp_map:
            cp_map[cid] = {
                "scope1": float(ce[2] or 0),
                "scope2_market": float(ce[3] or 0),
                "scope3": float(ce[4] or 0),
                "dqs": ce[5],
                "source": ce[6],
            }

    # 3. Compute total outstanding per counterparty (for AF denominator)
    cp_total: Dict[str, float] = {}
    for r in rows:
        cid = r[0]
        amt = float(r[3] or 0)
        cp_total[cid] = cp_total.get(cid, 0) + amt

    # 4. Compute financed emissions per row
    total_outstanding = sum(float(r[3] or 0) for r in rows)
    total_financed_tco2e = 0.0
    dqs_buckets: Dict[int, float] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    sector_breakdown: Dict[str, Dict] = {}
    waci_numerator = 0.0

    seen_counterparties = set()  # avoid double-counting multi-row counterparties

    for r in rows:
        cid, cp_name, sector, outstanding, row_dqs, row_emissions, stage = (
            r[0], r[1], r[2] or "Other", float(r[3] or 0),
            r[4], float(r[5] or 0) if r[5] else None, r[6],
        )
        if not outstanding:
            continue

        cp_total_outstanding = cp_total.get(cid, outstanding)
        af = outstanding / cp_total_outstanding if cp_total_outstanding > 0 else 0

        # Resolve emissions: DQS 1-3 from di_counterparty_emissions, DQS 4-5 from row
        if cid in cp_map and cp_map[cid]["dqs"] <= 3:
            em_rec = cp_map[cid]
            total_scope12 = em_rec["scope1"] + em_rec["scope2_market"]
            effective_dqs = em_rec["dqs"]
        elif row_emissions is not None:
            total_scope12 = row_emissions
            effective_dqs = int(row_dqs) if row_dqs else 4
        else:
            # DQS 5 fallback — no data
            total_scope12 = 0.0
            effective_dqs = 5

        financed_tco2e = af * total_scope12

        if cid not in seen_counterparties:
            total_financed_tco2e += financed_tco2e
            dqs_buckets[effective_dqs] = dqs_buckets.get(effective_dqs, 0) + financed_tco2e
            seen_counterparties.add(cid)

        # Sector aggregation
        if sector not in sector_breakdown:
            sector_breakdown[sector] = {"outstanding_usd": 0.0, "financed_tco2e": 0.0, "loan_count": 0}
        sector_breakdown[sector]["outstanding_usd"] += outstanding
        sector_breakdown[sector]["loan_count"] += 1
        if cid not in seen_counterparties or True:
            sector_breakdown[sector]["financed_tco2e"] += financed_tco2e

        # WACI = emissions_intensity × weight_in_portfolio
        if outstanding > 0 and total_scope12 > 0 and outstanding > 0:
            # intensity = tCO2e / USD million outstanding
            intensity = (total_scope12 / (outstanding / 1_000_000)) if outstanding else 0
            waci_numerator += (outstanding / total_outstanding) * intensity if total_outstanding > 0 else 0

    waci = round(waci_numerator, 2) if total_outstanding > 0 else None

    # DQS distribution percentages
    total_fe = total_financed_tco2e or 1  # avoid div-by-zero
    dqs_pct = {k: round(v / total_fe * 100, 1) for k, v in dqs_buckets.items()}
    weighted_dqs = (
        sum(k * v for k, v in dqs_buckets.items()) / total_fe
        if total_financed_tco2e > 0 else None
    )

    return {
        "summary": {
            "total_loans": len(rows),
            "unique_counterparties": len(seen_counterparties),
            "total_outstanding_usd": round(total_outstanding, 2),
            "total_financed_emissions_tco2e": round(total_financed_tco2e, 2),
            "waci_tco2e_per_musd": waci,
            "weighted_avg_dqs": round(weighted_dqs, 2) if weighted_dqs else None,
            "data_year": data_year,
        },
        "dqs_distribution": {
            "counts": dqs_buckets,
            "pct_of_financed_emissions": dqs_pct,
        },
        "sector_breakdown": [
            {
                "sector": k,
                "outstanding_usd": round(v["outstanding_usd"], 2),
                "financed_tco2e": round(v["financed_tco2e"], 2),
                "loan_count": v["loan_count"],
                "intensity_tco2e_musd": round(
                    v["financed_tco2e"] / (v["outstanding_usd"] / 1_000_000), 2
                ) if v["outstanding_usd"] else None,
            }
            for k, v in sorted(sector_breakdown.items(), key=lambda x: -x[1]["financed_tco2e"])
        ],
    }


# ──────────────────────────────────────────────────────────────────────────────
# C.COMPUTE  Shipping Fleet Analytics — computed from di_shipping_fleet
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/shipping-analytics")
def get_shipping_analytics(db: Session = Depends(get_db)):
    """
    Compute fleet-level CII analytics from di_shipping_fleet.
    Returns CII rating distribution, weighted average CII score, total CO2,
    and IMO 2030 / 2050 glidepath gap assessment.
    """
    rows = db.execute(text("""
        SELECT vessel_imo, vessel_name, vessel_type, dwt_tonnes, gross_tonnage,
               propulsion_type, annual_co2_tco2e, annual_distance_nm,
               cii_rating, cii_score, eexi_value, build_year, data_year
        FROM di_shipping_fleet
        ORDER BY vessel_imo
    """)).fetchall()

    if not rows:
        return {
            "summary": {"vessel_count": 0},
            "cii_distribution": {},
            "fleet_co2_tco2e": 0,
            "vessels": [],
        }

    cii_dist: Dict[str, int] = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0}
    total_co2 = 0.0
    vessels_out = []

    for r in rows:
        (imo, name, vtype, dwt, gt, prop, co2, dist, cii_r, cii_s,
         eexi, build_yr, yr) = r

        total_co2 += float(co2 or 0)
        rating = (cii_r or "").strip().upper()
        if rating in cii_dist:
            cii_dist[rating] += 1

        # IMO 2030 gap: required -40% CII vs 2008 reference
        # Using simplified: flag vessels rated D or E as "non-compliant 2030"
        compliant_2030 = rating in ("A", "B", "C")
        compliant_2050 = rating == "A"

        # AER (gCO2 / DWT·nm) from raw data if available
        aer = None
        dwt_f = float(dwt or 0)
        dist_f = float(dist or 0)
        co2_f = float(co2 or 0)
        if dwt_f > 0 and dist_f > 0 and co2_f > 0:
            aer = round((co2_f * 1_000_000) / (dwt_f * dist_f), 2)  # gCO2/DWT·nm

        vessels_out.append({
            "vessel_imo": imo,
            "vessel_name": name,
            "vessel_type": vtype,
            "propulsion_type": prop,
            "build_year": build_yr,
            "annual_co2_tco2e": float(co2 or 0),
            "cii_rating": rating or None,
            "cii_score": float(cii_s or 0) if cii_s else None,
            "eexi_value": float(eexi or 0) if eexi else None,
            "aer_gco2_dwtnm": aer,
            "compliant_imo_2030": compliant_2030,
            "compliant_imo_2050": compliant_2050,
        })

    total_vessels = len(rows)
    d_e_count = cii_dist.get("D", 0) + cii_dist.get("E", 0)

    return {
        "summary": {
            "vessel_count": total_vessels,
            "fleet_co2_tco2e": round(total_co2, 2),
            "non_compliant_2030_count": d_e_count,
            "non_compliant_2030_pct": round(d_e_count / total_vessels * 100, 1) if total_vessels else 0,
            "a_rated_pct": round(cii_dist["A"] / total_vessels * 100, 1) if total_vessels else 0,
        },
        "cii_distribution": cii_dist,
        "vessels": vessels_out,
    }


# ──────────────────────────────────────────────────────────────────────────────
# C.COMPUTE  Steel Portfolio Analytics — computed from di_steel_borrowers
# ──────────────────────────────────────────────────────────────────────────────

# IEA NZE glidepath: tCO2/tSteel by year (linear interpolation 2020→2050)
_STEEL_NZE_GLIDEPATH = {
    2020: 1.85, 2025: 1.60, 2030: 1.28, 2035: 0.95, 2040: 0.65, 2045: 0.38, 2050: 0.10,
}


@router.get("/steel-analytics")
def get_steel_analytics(db: Session = Depends(get_db)):
    """
    Compute portfolio-level steel sector analytics from di_steel_borrowers.
    Returns weighted average CO2 intensity vs. IEA NZE glidepath,
    production route breakdown, and SBTi commitment rate.
    """
    rows = db.execute(text("""
        SELECT borrower_id, borrower_name, country_iso2,
               crude_steel_production_mt, bf_bof_share_pct, eaf_share_pct, dri_share_pct,
               blended_co2_intensity_tco2_tcs, total_co2_tco2e, sbti_committed, data_year
        FROM di_steel_borrowers
        ORDER BY borrower_name
    """)).fetchall()

    if not rows:
        return {"summary": {"borrower_count": 0}, "borrowers": []}

    total_production_mt = 0.0
    total_co2_weighted = 0.0
    route_totals = {"bf_bof_mt": 0.0, "eaf_mt": 0.0, "dri_mt": 0.0}
    sbti_count = 0
    borrowers_out = []

    for r in rows:
        (bid, bname, cty, prod, bof, eaf, dri, blended, total_co2,
         sbti, yr) = r

        prod_f = float(prod or 0)
        blended_f = float(blended or 0)
        total_production_mt += prod_f
        total_co2_weighted += blended_f * prod_f

        if sbti:
            sbti_count += 1

        # Route allocation
        route_totals["bf_bof_mt"] += prod_f * (float(bof or 0) / 100)
        route_totals["eaf_mt"] += prod_f * (float(eaf or 0) / 100)
        route_totals["dri_mt"] += prod_f * (float(dri or 0) / 100)

        # NZE glidepath for current year
        cur_year = int(yr or 2024)
        # Linear interpolation between NZE waypoints
        years = sorted(_STEEL_NZE_GLIDEPATH.keys())
        nze_intensity = _STEEL_NZE_GLIDEPATH.get(cur_year)
        if nze_intensity is None:
            for i in range(len(years) - 1):
                if years[i] <= cur_year <= years[i + 1]:
                    t = (cur_year - years[i]) / (years[i + 1] - years[i])
                    nze_intensity = _STEEL_NZE_GLIDEPATH[years[i]] + t * (
                        _STEEL_NZE_GLIDEPATH[years[i + 1]] - _STEEL_NZE_GLIDEPATH[years[i]]
                    )
                    break
            else:
                nze_intensity = _STEEL_NZE_GLIDEPATH[years[-1]]

        gap_vs_nze = round(blended_f - nze_intensity, 3) if blended_f and nze_intensity else None

        borrowers_out.append({
            "borrower_id": bid,
            "borrower_name": bname,
            "country_iso2": cty,
            "crude_steel_production_mt": prod_f,
            "bf_bof_share_pct": float(bof or 0),
            "eaf_share_pct": float(eaf or 0),
            "dri_share_pct": float(dri or 0),
            "blended_intensity_tco2_tcs": blended_f,
            "total_co2_tco2e": float(total_co2 or 0),
            "sbti_committed": bool(sbti),
            "nze_2030_target_tco2_tcs": 1.28,
            "gap_vs_nze_tco2_tcs": gap_vs_nze,
            "on_track_2030": (blended_f <= 1.28) if blended_f else None,
            "data_year": yr,
        })

    # Portfolio weighted average intensity
    portfolio_intensity = (
        total_co2_weighted / total_production_mt if total_production_mt > 0 else None
    )
    nze_2030_gap = round(portfolio_intensity - 1.28, 3) if portfolio_intensity else None

    return {
        "summary": {
            "borrower_count": len(rows),
            "total_production_mt": round(total_production_mt, 2),
            "portfolio_avg_intensity_tco2_tcs": round(portfolio_intensity, 3) if portfolio_intensity else None,
            "nze_2030_target_tco2_tcs": 1.28,
            "gap_vs_nze_2030": nze_2030_gap,
            "on_track_portfolio": (portfolio_intensity <= 1.28) if portfolio_intensity else None,
            "sbti_committed_count": sbti_count,
            "sbti_committed_pct": round(sbti_count / len(rows) * 100, 1) if rows else 0,
        },
        "production_route_mix": {
            "bf_bof_mt": round(route_totals["bf_bof_mt"], 2),
            "eaf_mt": round(route_totals["eaf_mt"], 2),
            "dri_mt": round(route_totals["dri_mt"], 2),
            "bf_bof_pct": round(route_totals["bf_bof_mt"] / total_production_mt * 100, 1) if total_production_mt else 0,
            "eaf_pct": round(route_totals["eaf_mt"] / total_production_mt * 100, 1) if total_production_mt else 0,
            "dri_pct": round(route_totals["dri_mt"] / total_production_mt * 100, 1) if total_production_mt else 0,
        },
        "nze_glidepath": [
            {"year": yr, "target_tco2_tcs": val}
            for yr, val in sorted(_STEEL_NZE_GLIDEPATH.items())
        ],
        "borrowers": borrowers_out,
    }
