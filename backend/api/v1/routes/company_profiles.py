"""
Company Profiles API
Comprehensive entity identity, sector classification, prudential metrics (Basel III,
Solvency II, Pillar 3 ESG), and climate/ESG membership datapoints.

Endpoints:
  GET  /api/v1/company-profiles/                    — list with filters + search
  GET  /api/v1/company-profiles/{profile_id}        — single profile (full detail)
  POST /api/v1/company-profiles/extract-from-reports — populate from processed CSRD reports
  POST /api/v1/company-profiles/seed-from-engine    — seed from peer benchmark engine (analyst estimates)
  PUT  /api/v1/company-profiles/{profile_id}        — update one profile
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from db.base import get_db
from services.peer_benchmark_engine import peer_benchmark_engine

log = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/company-profiles",
    tags=["Company Profiles"],
)


# ─── Indicator → company profile column mapping ───────────────────────────────
# Maps csrd_kpi_values indicator_code → company_profiles column name
_KPI_TO_COLUMN: dict[str, str] = {
    # ESRS E1 — own GHG
    "E1-6.Scope1GHG":                 "scope1_tco2e",
    "E1-6.GHGIntensityRevenue":       "ghg_intensity_tco2e_meur_revenue",
    # ESRS E1 — energy
    "E1-5.EnergyConsumptionTotal":    "energy_consumption_mwh",
    "E1-5.EnergyConsumptionRenewable":"renewable_energy_pct",
    "E1-5.RenewableEnergyPct":        "renewable_energy_pct",
    # ESRS E1 — SBTi
    "E1-4.SBTiTarget":                "_sbti_flag",   # special: sets sbti_committed=True
    # ESRS E3
    "E3-4.WaterConsumption":          "water_consumption_m3",
    # ESRS E5
    "E5-5.WasteRecycledPct":          "waste_recycled_pct",
    # ESRS S1 — workforce
    "S1-7.TotalEmployeesHeadcount":   "employees_fte",
    "S1-7.FemaleEmployeesPct":        "employees_female_pct",
    "S1-7.FemaleManagementPct":       "employees_management_female_pct",
    # ESRS S1 — H&S
    "S1-11.Fatalities":               "fatalities",
    "S1-11.TRIR":                     "trir",
    "S1-11.LTIR":                     "ltir",
    # ESRS S1 — pay
    "S1-16.GenderPayGapPct":          "gender_pay_gap_pct",
    # ESRS G1
    "G1-4.CorruptionIncidents":       "corruption_incidents",
    # ESRS 2 (general)
    "ESRS2.BalanceSheetMEUR":         "_total_assets_meur",  # special: convert to eur_bn
    "ESRS2.TotalRevenueMEUR":         "annual_revenue_eur_mn",
    "ESRS2.EmployeeCountFTE":         "employees_fte",
    # EU Taxonomy
    "EUTaxonomy.AlignedRevenuePct":   "eu_taxonomy_aligned_revenue_pct",
    "EUTaxonomy.AlignedCapexPct":     "eu_taxonomy_aligned_capex_pct",
    "EUTaxonomy.AlignedOpexPct":      "eu_taxonomy_aligned_opex_pct",
    # Financed emissions
    "FI.WACI":                        "p3_waci_tco2e_meur",
}

# ─── Institution type from peer_benchmark_engine sector ───────────────────────
_PEER_SECTOR_TO_INST_TYPE: dict[str, str] = {
    "Universal Bank": "Bank",
    "Retail & Commercial Bank": "Bank",
    "Investment Bank": "Bank",
    "Cooperative Bank": "Bank",
    "Online Bank": "Bank",
    "Development Bank": "Bank",
    "State Bank": "Bank",
    "Insurance": "Insurance",
    "Life Insurance": "Insurance",
    "Reinsurance": "Insurance",
    "Asset Manager": "Asset Manager",
    "Passive Asset Manager": "Asset Manager",
    "PE / Infrastructure": "Private Equity",
    "PE / Infrastructure (Real Assets)": "Asset Manager",
    "Climate VC": "Venture Capital",
    "Energy Developer": "Energy",
    "Utility": "Energy",
    "Integrated Energy": "Energy",
    "Oil & Gas": "Energy",
    "Technology": "Technology",
    "Mining": "Mining",
    # Real estate
    "REIT (Industrial / Logistics)": "REIT",
    "REIT (Infrastructure / Towers)": "REIT",
    "REIT (Retail / Shopping Centres)": "REIT",
    "REIT (Diversified)": "REIT",
    "REIT (Diversified / Office & Industrial)": "REIT",
    "REIT (Diversified / UK)": "REIT",
    "Real Estate Services": "Real Estate",
    "Real Estate (Residential)": "Real Estate",
}


# ─── Country name / code → ISO 3166-1 alpha-3 ────────────────────────────────
_COUNTRY_TO_ISO3: dict[str, str] = {
    # Full country names
    "Australia": "AUS", "Austria": "AUT", "Belgium": "BEL", "Brazil": "BRA",
    "Canada": "CAN", "China": "CHN", "Denmark": "DNK", "Finland": "FIN",
    "France": "FRA", "Germany": "DEU", "Greece": "GRC", "Hong Kong": "HKG",
    "India": "IND", "Indonesia": "IDN", "Ireland": "IRL", "Italy": "ITA",
    "Japan": "JPN", "Luxembourg": "LUX", "Malaysia": "MYS", "Mexico": "MEX",
    "Netherlands": "NLD", "Norway": "NOR", "Philippines": "PHL",
    "Portugal": "PRT", "Saudi Arabia": "SAU", "Singapore": "SGP",
    "South Africa": "ZAF", "South Korea": "KOR", "Spain": "ESP",
    "Sweden": "SWE", "Switzerland": "CHE", "Taiwan": "TWN", "Thailand": "THA",
    "Turkey": "TUR", "UAE": "ARE", "UK": "GBR", "US": "USA",
    "United Kingdom": "GBR", "United States": "USA",
    # ISO 3166-1 alpha-2 → alpha-3
    "AU": "AUS", "AT": "AUT", "BE": "BEL", "BR": "BRA", "CA": "CAN",
    "CN": "CHN", "DK": "DNK", "FI": "FIN", "FR": "FRA", "DE": "DEU",
    "GR": "GRC", "HK": "HKG", "IN": "IND", "ID": "IDN", "IE": "IRL",
    "IT": "ITA", "JP": "JPN", "LU": "LUX", "MY": "MYS", "MX": "MEX",
    "NL": "NLD", "NO": "NOR", "PH": "PHL", "PT": "PRT", "SA": "SAU",
    "SG": "SGP", "ZA": "ZAF", "KR": "KOR", "ES": "ESP", "SE": "SWE",
    "CH": "CHE", "TW": "TWN", "TH": "THA", "TR": "TUR", "AE": "ARE",
    "GB": "GBR", "US": "USA",
    # ISO 3166-1 alpha-3 pass-through (already correct)
    "AUS": "AUS", "AUT": "AUT", "BEL": "BEL", "BRA": "BRA", "CAN": "CAN",
    "CHN": "CHN", "DNK": "DNK", "FIN": "FIN", "FRA": "FRA", "DEU": "DEU",
    "GRC": "GRC", "HKG": "HKG", "IND": "IND", "IDN": "IDN", "IRL": "IRL",
    "ITA": "ITA", "JPN": "JPN", "LUX": "LUX", "MYS": "MYS", "MEX": "MEX",
    "NLD": "NLD", "NOR": "NOR", "PHL": "PHL", "PRT": "PRT", "SAU": "SAU",
    "SGP": "SGP", "ZAF": "ZAF", "KOR": "KOR", "ESP": "ESP", "SWE": "SWE",
    "CHE": "CHE", "TWN": "TWN", "THA": "THA", "TUR": "TUR", "ARE": "ARE",
    "GBR": "GBR", "USA": "USA",
}


def _to_iso3(country_raw: str) -> str:
    """Convert any country name/code to ISO 3166-1 alpha-3. Falls back to XXX."""
    if not country_raw:
        return ""
    lookup = country_raw.strip()
    return _COUNTRY_TO_ISO3.get(lookup, lookup[:3].upper() if len(lookup) >= 3 else lookup.upper())


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _profile_row_to_dict(row, columns: list[str]) -> dict:
    """Convert a SQLAlchemy Row to a dict using the provided column list."""
    return {col: (val.isoformat() if isinstance(val, (date, datetime)) else val)
            for col, val in zip(columns, row)}


def _list_company_profiles_columns() -> list[str]:
    """Minimal columns for list view."""
    return [
        "id", "legal_name", "trading_name", "entity_lei", "isin_primary",
        "ticker_symbol", "primary_sector", "institution_type", "listing_status",
        "headquarters_country", "headquarters_city", "gics_sector",
        "total_assets_eur_bn", "annual_revenue_eur_mn", "employees_fte",
        "is_financial_institution", "systemic_importance",
        "cet1_ratio_pct", "lcr_pct", "nsfr_pct",
        "p3_gar_pct", "p3_waci_tco2e_meur",
        "scope1_tco2e", "ghg_intensity_tco2e_meur_revenue",
        "net_zero_target_year", "sbti_status", "cdp_score",
        "nzba_member", "pcaf_member", "tcfd_supporter",
        "reporting_year", "data_source", "created_at",
    ]


# ─── List ─────────────────────────────────────────────────────────────────────

@router.get("/", summary="List company profiles with search and filters")
def list_profiles(
    search:           Optional[str] = Query(None, description="Name, LEI, ISIN, or ticker"),
    sector:           Optional[str] = Query(None),
    institution_type: Optional[str] = Query(None),
    country:          Optional[str] = Query(None, description="ISO-3 country code"),
    systemic:         Optional[str] = Query(None, description="G-SIB, D-SIB, G-SII, None"),
    is_fi:            Optional[bool] = Query(None, description="Filter to financial institutions"),
    limit:            int = Query(100, ge=1, le=500),
    offset:           int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Return company profiles with optional filters. Includes summary financial + ESG fields."""
    cols = ", ".join(_list_company_profiles_columns())
    conditions = ["1=1"]
    params: dict = {"limit": limit, "offset": offset}

    if search:
        conditions.append(
            "(LOWER(legal_name) LIKE :search OR LOWER(trading_name) LIKE :search "
            "OR LOWER(entity_lei) LIKE :search OR LOWER(isin_primary) LIKE :search "
            "OR LOWER(ticker_symbol) LIKE :search)"
        )
        params["search"] = f"%{search.lower()}%"
    if sector:
        conditions.append("LOWER(primary_sector) LIKE :sector")
        params["sector"] = f"%{sector.lower()}%"
    if institution_type:
        conditions.append("LOWER(institution_type) = :inst_type")
        params["inst_type"] = institution_type.lower()
    if country:
        conditions.append("headquarters_country = :country")
        params["country"] = country.upper()
    if systemic:
        conditions.append("systemic_importance = :systemic")
        params["systemic"] = systemic
    if is_fi is not None:
        conditions.append("is_financial_institution = :is_fi")
        params["is_fi"] = is_fi

    where = " AND ".join(conditions)
    sql = f"""
        SELECT {cols} FROM company_profiles
        WHERE {where}
        ORDER BY legal_name
        LIMIT :limit OFFSET :offset
    """
    count_sql = f"SELECT COUNT(*) FROM company_profiles WHERE {where}"

    try:
        rows = db.execute(text(sql), params).fetchall()
        total = db.execute(text(count_sql), {k: v for k, v in params.items()
                                             if k not in ("limit", "offset")}).scalar()
        col_names = _list_company_profiles_columns()
        return {
            "profiles": [_profile_row_to_dict(r, col_names) for r in rows],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except Exception as exc:
        log.error("list_profiles failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


# ─── Single profile (full detail) ─────────────────────────────────────────────

@router.get("/{profile_id}", summary="Full company profile by ID")
def get_profile(profile_id: uuid.UUID, db: Session = Depends(get_db)):
    """Return all columns for a single company profile."""
    try:
        row = db.execute(
            text("SELECT * FROM company_profiles WHERE id = :id"),
            {"id": profile_id}
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Profile '{profile_id}' not found")

        # Get column names from cursor description
        col_names = list(db.execute(
            text("SELECT column_name FROM information_schema.columns "
                 "WHERE table_name='company_profiles' ORDER BY ordinal_position"),
        ).scalars())

        return {"profile": _profile_row_to_dict(row, col_names)}
    except HTTPException:
        raise
    except Exception as exc:
        log.error("get_profile failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


# ─── Extract from CSRD reports ────────────────────────────────────────────────

@router.post("/extract-from-reports",
             summary="Extract datapoints from processed CSRD reports into company_profiles")
def extract_from_reports(db: Session = Depends(get_db)):
    """
    For each entity in csrd_entity_registry that has processed CSRD data
    (csrd_kpi_values), extract all available datapoints and upsert a company
    profile row. Handles the indicator_code → column mapping defined in
    _KPI_TO_COLUMN. Returns a summary of records created/updated.
    """
    # Fetch all entities with at least one KPI value
    # Note: csrd_entity_registry uses 'lei' (not 'entity_lei') and has no 'reporting_frameworks'
    entity_sql = """
        SELECT DISTINCT
            er.id, er.legal_name, er.primary_sector, er.country_iso,
            er.lei,
            er.is_in_scope_csrd, er.is_in_scope_sfdr, er.is_in_scope_issb, er.is_in_scope_tcfd,
            er.gics_sector, er.sector_subtype,
            er.net_turnover_meur, er.balance_sheet_total_meur, er.employee_count
        FROM csrd_entity_registry er
        INNER JOIN csrd_kpi_values kv ON kv.entity_registry_id = er.id
        ORDER BY er.legal_name
    """
    try:
        entities = db.execute(text(entity_sql)).fetchall()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not fetch entities: {exc}")

    results = []

    for (er_id, legal_name, primary_sector, country_iso,
         entity_lei, is_csrd, is_sfdr, is_issb, is_tcfd,
         gics_sector, sector_subtype,
         net_turnover_meur, balance_sheet_meur, employee_count) in entities:

        # Fetch all KPI values for this entity (latest reporting year per indicator)
        kpi_sql = """
            SELECT indicator_code, numeric_value, text_value, reporting_year
            FROM csrd_kpi_values
            WHERE entity_registry_id = :eid
            ORDER BY reporting_year DESC, indicator_code
        """
        kpi_rows = db.execute(text(kpi_sql), {"eid": str(er_id)}).fetchall()

        # Map indicator_code → value (take first row = most recent year per code)
        kpi_map: dict[str, tuple] = {}
        for (code, num_val, text_val, rep_year) in kpi_rows:
            if code not in kpi_map:
                kpi_map[code] = (num_val, text_val, rep_year)

        # Determine reporting year (most common across extracted KPIs)
        years = [v[2] for v in kpi_map.values()]
        reporting_year = max(set(years), key=years.count) if years else None

        # Build profile update dict from mapped KPIs
        # Determine mandatory frameworks from registry flags
        mandatory_fw: list[str] = []
        if is_csrd:   mandatory_fw.append("CSRD")
        if is_sfdr:   mandatory_fw.append("SFDR")
        if is_issb:   mandatory_fw.append("ISSB S1/S2")
        if is_tcfd:   mandatory_fw.append("TCFD")

        # Map primary_sector → institution_type
        _SECTOR_TO_INST_MAP = {
            "financial_institution": "Bank",
            "insurance":             "Insurance",
            "asset_manager":         "Asset Manager",
            "energy_developer":      "Energy",
            "real_estate":           "Real Estate",
            "technology":            "Technology",
            "supply_chain":          "Corporate",
        }
        inst_type = _SECTOR_TO_INST_MAP.get(primary_sector or "", "Corporate")
        is_fi = primary_sector in ("financial_institution", "insurance", "asset_manager")

        profile_fields: dict = {
            "legal_name":              legal_name,
            "primary_sector":          primary_sector,
            "gics_sector":             gics_sector,
            "headquarters_country":    country_iso,
            "entity_lei":              entity_lei,
            "entity_registry_id":      str(er_id),
            "reporting_year":          reporting_year,
            "institution_type":        inst_type,
            "is_financial_institution": is_fi,
            "data_source":             "csrd_report",
            "updated_at":              datetime.now(timezone.utc),
            "extra_metadata": json.dumps({
                "mandatory_frameworks": mandatory_fw,
                "sector_subtype":       sector_subtype,
                "is_in_scope_csrd":     bool(is_csrd),
                "is_in_scope_sfdr":     bool(is_sfdr),
                "is_in_scope_issb":     bool(is_issb),
                "is_in_scope_tcfd":     bool(is_tcfd),
            }),
        }

        # Populate financials from csrd_entity_registry if available
        if net_turnover_meur is not None:
            profile_fields["annual_revenue_eur_mn"] = float(net_turnover_meur)
        if balance_sheet_meur is not None:
            profile_fields["total_assets_eur_bn"] = float(balance_sheet_meur) / 1000
        if employee_count is not None:
            profile_fields["employees_fte"] = int(employee_count)

        # Extract KPI values using the mapping
        for code, (num_val, text_val, _) in kpi_map.items():
            col = _KPI_TO_COLUMN.get(code)
            if col is None:
                continue

            if col == "_sbti_flag":
                # Presence of SBTi target indicator → mark committed
                profile_fields["sbti_committed"] = True
                profile_fields["sbti_status"] = "Committed"

            elif col == "_total_assets_meur":
                # ESRS2.BalanceSheetMEUR is in MEUR → convert to EUR bn
                if num_val is not None:
                    profile_fields["total_assets_eur_bn"] = float(num_val) / 1000

            elif col == "employees_fte":
                if num_val is not None:
                    profile_fields["employees_fte"] = int(num_val)

            elif col == "fatalities":
                if num_val is not None:
                    profile_fields["fatalities"] = int(num_val)

            elif col == "corruption_incidents":
                if num_val is not None:
                    profile_fields["corruption_incidents"] = int(num_val)

            else:
                if num_val is not None:
                    profile_fields[col] = float(num_val)
                elif text_val is not None:
                    profile_fields[col] = text_val

        # Upsert: check if profile already exists for this entity_registry_id
        existing = db.execute(
            text("SELECT id FROM company_profiles WHERE entity_registry_id = :eid"),
            {"eid": str(er_id)}
        ).fetchone()

        if existing:
            # UPDATE
            set_clauses = ", ".join(f"{k} = :{k}" for k in profile_fields)
            db.execute(
                text(f"UPDATE company_profiles SET {set_clauses} WHERE entity_registry_id = :entity_registry_id"),
                profile_fields
            )
            action = "updated"
            profile_id = str(existing[0])
        else:
            # INSERT — let DB generate UUID via gen_random_uuid() server_default
            cols_str = ", ".join(profile_fields.keys())
            vals_str = ", ".join(f":{k}" for k in profile_fields.keys())
            row = db.execute(
                text(f"INSERT INTO company_profiles ({cols_str}) VALUES ({vals_str}) RETURNING id"),
                profile_fields
            ).fetchone()
            action = "created"
            profile_id = str(row[0]) if row else "unknown"

        results.append({
            "legal_name":    legal_name,
            "profile_id":    profile_id,
            "action":        action,
            "kpis_mapped":   len([k for k in kpi_map if _KPI_TO_COLUMN.get(k)]),
            "reporting_year": reporting_year,
        })

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Commit failed: {exc}")

    return {
        "extracted_at":    datetime.now(timezone.utc).isoformat(),
        "entities_processed": len(entities),
        "profiles_created":   sum(1 for r in results if r["action"] == "created"),
        "profiles_updated":   sum(1 for r in results if r["action"] == "updated"),
        "results":            results,
    }


# ─── Seed from peer benchmark engine (analyst estimates) ──────────────────────

@router.post("/seed-from-engine",
             summary="Seed company profiles from the peer benchmark engine analyst estimates")
def seed_from_engine(db: Session = Depends(get_db)):
    """
    Create a company_profiles row for every institution in the peer benchmark
    engine that does not already have a profile. Uses analyst-estimated scores
    and institutional metadata. Does NOT overwrite rows already seeded from
    real CSRD reports.
    """
    institutions = peer_benchmark_engine.get_all_institutions()
    created = 0
    skipped = 0

    for inst in institutions:
        slug = inst.get("slug", "")
        legal_name = inst.get("name", slug)

        # Skip if already has a profile (by legal_name match)
        exists = db.execute(
            text("SELECT id FROM company_profiles WHERE LOWER(legal_name) = LOWER(:name)"),
            {"name": legal_name}
        ).fetchone()
        if exists:
            skipped += 1
            continue

        inst_type = _PEER_SECTOR_TO_INST_TYPE.get(
            inst.get("institution_type", ""), "Corporate"
        )
        is_fi = inst_type in ("Bank", "Insurance", "Asset Manager",
                              "Private Equity", "Venture Capital")

        # Normalise country: peer engine uses full names or alpha-2; DB column is VARCHAR(3) alpha-3
        raw_country = _to_iso3(inst.get("country") or "")

        profile = {
            "legal_name":            legal_name,
            "headquarters_country":  raw_country,
            "listing_status":        "Listed" if inst.get("listed") else "Unlisted",
            "institution_type":      inst_type,
            "is_financial_institution": is_fi,
            "total_assets_eur_bn":   inst.get("assets_usd_bn"),   # USD ≈ EUR for estimate
            "nzba_member":           bool(inst.get("nzba_member", False)),
            "pcaf_member":           bool(inst.get("pcaf_member", False)),
            "tnfd_supporter":        bool(inst.get("tnfd_supporter", False)),
            "net_zero_target_year":  inst.get("net_zero_target_year"),
            "sustainability_report_url": inst.get("report_url"),
            "data_source":           "analyst_estimate",
            "updated_at":            datetime.now(timezone.utc),
            "extra_metadata": json.dumps({
                "peer_slug":           slug,
                "mandatory_frameworks": inst.get("mandatory_frameworks", []),
                "voluntary_frameworks": inst.get("voluntary_frameworks", []),
                "peer_scores":         inst.get("scores", {}),
                "portfolio_details":   inst.get("portfolio_details", {}),
            }),
        }

        # Map voluntary_frameworks to flags (voluntary_frameworks not in _to_summary,
        # but nzba_member etc are included — use those directly)
        profile["gfanz_member"] = bool(inst.get("nzba_member", False))

        cols_str = ", ".join(profile.keys())
        vals_str = ", ".join(f":{k}" for k in profile.keys())
        try:
            # Use SAVEPOINT so a failed INSERT does not abort the entire transaction
            db.execute(text("SAVEPOINT sp_seed"))
            db.execute(
                text(f"INSERT INTO company_profiles ({cols_str}) VALUES ({vals_str})"),
                profile
            )
            db.execute(text("RELEASE SAVEPOINT sp_seed"))
            created += 1
        except Exception as exc:
            log.error("Failed to seed profile for %s: %s", legal_name, exc)
            db.execute(text("ROLLBACK TO SAVEPOINT sp_seed"))

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Commit failed: {exc}")

    return {
        "seeded_at": datetime.now(timezone.utc).isoformat(),
        "created":   created,
        "skipped":   skipped,
        "total_in_engine": len(institutions),
    }


# ─── Update ───────────────────────────────────────────────────────────────────

@router.put("/{profile_id}", summary="Update specific fields on a company profile")
def update_profile(
    profile_id: uuid.UUID,
    updates: dict,
    db: Session = Depends(get_db),
):
    """
    Partial update — pass only the fields you want to change.
    Protected fields (id, entity_registry_id, created_at) are ignored.
    """
    protected = {"id", "entity_registry_id", "created_at"}
    safe = {k: v for k, v in updates.items() if k not in protected}
    if not safe:
        raise HTTPException(status_code=400, detail="No updatable fields provided")

    safe["updated_at"] = datetime.now(timezone.utc)
    safe["profile_id"] = profile_id

    set_clause = ", ".join(f"{k} = :{k}" for k in safe if k != "profile_id")
    try:
        result = db.execute(
            text(f"UPDATE company_profiles SET {set_clause} WHERE id = :profile_id"),
            safe
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Profile '{profile_id}' not found")
        db.commit()
        return {"updated": True, "profile_id": profile_id, "fields_updated": len(safe) - 1}
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))
