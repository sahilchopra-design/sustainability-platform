"""
Ingest 7 reference datasets into PostgreSQL.

Datasets:
  1. SBTi Companies (14,034 companies)       → dh_sbti_companies
  2. CA100+ Benchmark 2025 (169 companies)   → dh_ca100_assessments
  3. Coal Plant Tracker by Country (112 rows) → dh_reference_data
  4. CPI 2023 Global Results (181 countries)  → dh_country_risk_indices
  5. Fragile States Index 2023 (179 countries)→ dh_country_risk_indices
  6. Freedom House FIW 2013-2024 (~2700 rows) → dh_country_risk_indices
  7. UNDP HDR GII (~195 countries)            → dh_country_risk_indices

Usage:
  python scripts/ingest_reference_datasets.py
"""

import hashlib
import json
import math
import os
import sys
from datetime import datetime, timezone

import pandas as pd
import sqlalchemy as sa

DB_URL = "postgresql://postgres.kytzcbipsghprsqoalvi:KimiaAImpact2026@aws-1-us-east-2.pooler.supabase.com:5432/postgres"

DATA_DIR = r"C:\Users\SahilChopra\Downloads\csv_data_downloads\csv_downloads"

engine = sa.create_engine(DB_URL)


def _id(prefix: str, key: str) -> str:
    return hashlib.sha256(f"{prefix}:{key.lower().strip()}".encode()).hexdigest()[:24]


def _safe(val):
    """Return None for NaN/NaT, else the value."""
    if val is None:
        return None
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    if pd.isna(val):
        return None
    return val


def _safe_int(val):
    v = _safe(val)
    if v is None:
        return None
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return None


def _safe_float(val):
    v = _safe(val)
    if v is None:
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def _safe_str(val):
    v = _safe(val)
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None


# =============================================================================
# 1. SBTi Companies
# =============================================================================

def ingest_sbti():
    print("\n-- 1. SBTi Companies --")
    path = os.path.join(DATA_DIR, "SBTi_Companies.xlsx")
    df = pd.read_excel(path, sheet_name="Data")
    print(f"   Loaded: {len(df)} rows")

    inserted = 0
    failed = 0
    sql = sa.text("""
        INSERT INTO dh_sbti_companies (
            id, source_id, company_name, isin, lei, country, region, sector,
            company_type, target_status, near_term_target_year, near_term_ambition,
            long_term_target_year, long_term_ambition, net_zero_committed, net_zero_year,
            raw_record, ingested_at, updated_at
        ) VALUES (
            :id, :source_id, :company_name, :isin, :lei, :country, :region, :sector,
            :company_type, :target_status, :near_term_target_year, :near_term_ambition,
            :long_term_target_year, :long_term_ambition, :net_zero_committed, :net_zero_year,
            :raw_record, now(), now()
        )
        ON CONFLICT (id) DO UPDATE SET
            company_name = EXCLUDED.company_name,
            isin = EXCLUDED.isin,
            lei = EXCLUDED.lei,
            country = EXCLUDED.country,
            region = EXCLUDED.region,
            sector = EXCLUDED.sector,
            company_type = EXCLUDED.company_type,
            target_status = EXCLUDED.target_status,
            near_term_target_year = EXCLUDED.near_term_target_year,
            near_term_ambition = EXCLUDED.near_term_ambition,
            long_term_target_year = EXCLUDED.long_term_target_year,
            long_term_ambition = EXCLUDED.long_term_ambition,
            net_zero_committed = EXCLUDED.net_zero_committed,
            net_zero_year = EXCLUDED.net_zero_year,
            raw_record = EXCLUDED.raw_record,
            updated_at = now()
    """)

    with engine.begin() as conn:
        for i in range(0, len(df), 500):
            batch = df.iloc[i:i+500]
            for _, row in batch.iterrows():
                try:
                    sbti_id = _safe_str(row.get("sbti_id")) or _safe_str(row.get("company_name"))
                    if not sbti_id:
                        continue
                    rid = _id("sbti", sbti_id)
                    nz_status = _safe_str(row.get("net_zero_status"))
                    nz_committed = nz_status is not None and "target" in str(nz_status).lower()

                    raw = {}
                    for c in df.columns:
                        v = _safe(row[c])
                        if v is not None:
                            raw[c] = str(v) if not isinstance(v, (int, float, bool)) else v

                    conn.execute(sql, {
                        "id": rid,
                        "source_id": "ds-sbti-companies-xlsx",
                        "company_name": _safe_str(row.get("company_name")),
                        "isin": _safe_str(row.get("isin")),
                        "lei": _safe_str(row.get("lei")),
                        "country": _safe_str(row.get("location")),
                        "region": _safe_str(row.get("region")),
                        "sector": _safe_str(row.get("sector")),
                        "company_type": _safe_str(row.get("organization_type")),
                        "target_status": _safe_str(row.get("near_term_status")),
                        "near_term_target_year": _safe_int(row.get("near_term_target_year")),
                        "near_term_ambition": _safe_str(row.get("near_term_target_classification")),
                        "long_term_target_year": _safe_int(row.get("long_term_target_year")),
                        "long_term_ambition": _safe_str(row.get("long_term_target_classification")),
                        "net_zero_committed": nz_committed,
                        "net_zero_year": _safe_int(row.get("net_zero_year")),
                        "raw_record": json.dumps(raw, default=str),
                    })
                    inserted += 1
                except Exception as e:
                    failed += 1
                    if failed <= 5:
                        print(f"   ERR: {e}")

    print(f"   Done: {inserted} inserted/updated, {failed} failed")
    return inserted


# =============================================================================
# 2. Climate Action 100+ Benchmark 2025
# =============================================================================

def ingest_ca100():
    print("\n-- 2. CA100+ Benchmark 2025 --")
    path = os.path.join(DATA_DIR, "Climate_Action_100_Benchmark_2025.xlsx")
    df = pd.read_excel(path, sheet_name="Disclosure Assessments (TPI)", header=None)

    # Row 8 = headers, Row 11+ = data
    headers = [str(df.iloc[8, j]).strip() if pd.notna(df.iloc[8, j]) else f"col_{j}" for j in range(df.shape[1])]
    data_rows = df.iloc[11:].copy()
    data_rows.columns = headers
    data_rows = data_rows[data_rows["Company name"].notna()].reset_index(drop=True)
    print(f"   Loaded: {len(data_rows)} companies")

    # Find indicator columns
    ind_cols = {}
    for j, h in enumerate(headers):
        h_lower = h.lower() if isinstance(h, str) else ""
        for ind_num in range(1, 11):
            if f"indicator {ind_num} overall" in h_lower:
                ind_cols[ind_num] = h
                break

    inserted = 0
    failed = 0
    sql = sa.text("""
        INSERT INTO dh_ca100_assessments (
            id, source_id, company_name, isin, hq_location, hq_region,
            sector_cluster, sector, secondary_sector, scope3_category,
            indicator_1_score, indicator_2_score, indicator_3_score,
            indicator_4_score, indicator_5_score, indicator_6_score,
            indicator_7_score, indicator_8_score, indicator_9_score,
            indicator_10_score, assessment_year, raw_record, ingested_at, updated_at
        ) VALUES (
            :id, :source_id, :company_name, :isin, :hq_location, :hq_region,
            :sector_cluster, :sector, :secondary_sector, :scope3_category,
            :i1, :i2, :i3, :i4, :i5, :i6, :i7, :i8, :i9, :i10,
            2025, :raw_record, now(), now()
        )
        ON CONFLICT (id) DO UPDATE SET
            company_name = EXCLUDED.company_name,
            isin = EXCLUDED.isin,
            indicator_1_score = EXCLUDED.indicator_1_score,
            indicator_2_score = EXCLUDED.indicator_2_score,
            indicator_3_score = EXCLUDED.indicator_3_score,
            indicator_4_score = EXCLUDED.indicator_4_score,
            indicator_5_score = EXCLUDED.indicator_5_score,
            indicator_6_score = EXCLUDED.indicator_6_score,
            indicator_7_score = EXCLUDED.indicator_7_score,
            indicator_8_score = EXCLUDED.indicator_8_score,
            indicator_9_score = EXCLUDED.indicator_9_score,
            indicator_10_score = EXCLUDED.indicator_10_score,
            raw_record = EXCLUDED.raw_record,
            updated_at = now()
    """)

    with engine.begin() as conn:
        for _, row in data_rows.iterrows():
            try:
                name = _safe_str(row.get("Company name"))
                if not name:
                    continue
                rid = _id("ca100", name)

                raw = {}
                for c in data_rows.columns:
                    v = _safe(row[c])
                    if v is not None:
                        raw[str(c)[:80]] = str(v)[:500]

                conn.execute(sql, {
                    "id": rid,
                    "source_id": "ds-ca100-benchmark-2025",
                    "company_name": name,
                    "isin": _safe_str(row.get("ISIN")),
                    "hq_location": _safe_str(row.get("HQ location")),
                    "hq_region": _safe_str(row.get("HQ region")),
                    "sector_cluster": _safe_str(row.get("Sector cluster")),
                    "sector": _safe_str(row.get("Sector")),
                    "secondary_sector": _safe_str(row.get("Secondary sector")),
                    "scope3_category": _safe_str(row.get("Scope 3 category")),
                    "i1": _safe_str(row.get(ind_cols.get(1, ""))),
                    "i2": _safe_str(row.get(ind_cols.get(2, ""))),
                    "i3": _safe_str(row.get(ind_cols.get(3, ""))),
                    "i4": _safe_str(row.get(ind_cols.get(4, ""))),
                    "i5": _safe_str(row.get(ind_cols.get(5, ""))),
                    "i6": _safe_str(row.get(ind_cols.get(6, ""))),
                    "i7": _safe_str(row.get(ind_cols.get(7, ""))),
                    "i8": _safe_str(row.get(ind_cols.get(8, ""))),
                    "i9": _safe_str(row.get(ind_cols.get(9, ""))),
                    "i10": _safe_str(row.get(ind_cols.get(10, ""))),
                    "raw_record": json.dumps(raw, default=str),
                })
                inserted += 1
            except Exception as e:
                failed += 1
                if failed <= 5:
                    print(f"   ERR: {e}")

    print(f"   Done: {inserted} inserted/updated, {failed} failed")
    return inserted


# =============================================================================
# 3. Coal Plant Tracker by Country
# =============================================================================

def ingest_coal_tracker():
    print("\n-- 3. Coal Plant Tracker by Country --")
    path = os.path.join(DATA_DIR, "Coal_Plant_Tracker_Capacity_by_Country.csv")
    df = pd.read_csv(path, skiprows=3)
    df = df.dropna(subset=["Country/Area"]).reset_index(drop=True)
    print(f"   Loaded: {len(df)} countries")

    status_cols = [c for c in df.columns if c != "Country/Area"]
    inserted = 0
    failed = 0

    sql = sa.text("""
        INSERT INTO dh_reference_data (
            id, source_id, entity_name, entity_type, kpi_name,
            value, value_numeric, unit, geography, source_name, ingested_at
        ) VALUES (
            :id, :source_id, :entity_name, 'country', :kpi_name,
            :value, :value_numeric, 'MW', :geography, 'GEM Coal Plant Tracker', now()
        )
        ON CONFLICT (id) DO UPDATE SET
            value = EXCLUDED.value,
            value_numeric = EXCLUDED.value_numeric,
            ingested_at = now()
    """)

    with engine.begin() as conn:
        for _, row in df.iterrows():
            country = _safe_str(row["Country/Area"])
            if not country:
                continue
            for col in status_cols:
                try:
                    raw_val = row[col]
                    # Handle comma-separated numbers
                    val_str = str(raw_val).replace(",", "").strip() if pd.notna(raw_val) else "0"
                    val_num = _safe_float(val_str)
                    kpi = f"coal_capacity_{col.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('+', 'plus')}"
                    rid = _id("coal", f"{country}:{kpi}")

                    conn.execute(sql, {
                        "id": rid,
                        "source_id": "ds-gem-coal-tracker-country",
                        "entity_name": country,
                        "kpi_name": kpi,
                        "value": val_str,
                        "value_numeric": val_num,
                        "geography": country,
                    })
                    inserted += 1
                except Exception as e:
                    failed += 1
                    if failed <= 5:
                        print(f"   ERR: {e}")

    print(f"   Done: {inserted} inserted/updated, {failed} failed")
    return inserted


# =============================================================================
# 4. CPI 2023
# =============================================================================

def ingest_cpi():
    print("\n-- 4. CPI 2023 --")
    path = os.path.join(DATA_DIR, "CPI_2023_Global_Results.xlsx")
    df = pd.read_excel(path, sheet_name="CPI 2023", header=None)

    # Find the header row (contains "Country / Territory")
    header_row = 3  # default
    for i in range(10):
        val = str(df.iloc[i, 0]).strip() if pd.notna(df.iloc[i, 0]) else ""
        if "Country" in val:
            header_row = i
            break

    headers = [str(df.iloc[header_row, j]).strip() if pd.notna(df.iloc[header_row, j]) else f"col_{j}" for j in range(df.shape[1])]
    data = df.iloc[header_row+1:].copy()
    data.columns = headers
    data = data[data["Country / Territory"].notna()].reset_index(drop=True)
    print(f"   Loaded: {len(data)} countries")

    inserted = 0
    failed = 0

    sql = sa.text("""
        INSERT INTO dh_country_risk_indices (
            id, source_id, country_name, country_iso3, index_name,
            year, score, rank, subcategories, source_name, ingested_at, updated_at
        ) VALUES (
            :id, :source_id, :country_name, :iso3, 'CPI',
            2023, :score, :rank, :subcategories, 'Transparency International', now(), now()
        )
        ON CONFLICT (country_iso3, index_name, year) DO UPDATE SET
            score = EXCLUDED.score,
            rank = EXCLUDED.rank,
            subcategories = EXCLUDED.subcategories,
            updated_at = now()
    """)

    # Source columns (indices 9-21)
    source_cols = [c for c in headers if c not in [
        "Country / Territory", "ISO3", "Region", "CPI score 2023",
        "Rank", "Standard error", "Number of sources", "Lower CI", "Upper CI",
    ] and not c.startswith("col_")]

    with engine.begin() as conn:
        for _, row in data.iterrows():
            try:
                name = _safe_str(row.get("Country / Territory"))
                iso3 = _safe_str(row.get("ISO3"))
                if not name or not iso3:
                    continue
                rid = _id("cpi", f"{iso3}:2023")

                subs = {}
                subs["region"] = _safe_str(row.get("Region"))
                subs["standard_error"] = _safe_float(row.get("Standard error"))
                subs["num_sources"] = _safe_int(row.get("Number of sources"))
                subs["lower_ci"] = _safe_float(row.get("Lower CI"))
                subs["upper_ci"] = _safe_float(row.get("Upper CI"))
                for sc in source_cols:
                    v = _safe_float(row.get(sc))
                    if v is not None:
                        key = sc[:60].replace(" ", "_").replace("/", "_").lower()
                        subs[key] = v

                conn.execute(sql, {
                    "id": rid,
                    "source_id": "ds-ti-cpi-2023",
                    "country_name": name,
                    "iso3": iso3,
                    "score": _safe_float(row.get("CPI score 2023")),
                    "rank": _safe_int(row.get("Rank")),
                    "subcategories": json.dumps({k: v for k, v in subs.items() if v is not None}, default=str),
                })
                inserted += 1
            except Exception as e:
                failed += 1
                if failed <= 5:
                    print(f"   ERR: {e}")

    print(f"   Done: {inserted} inserted/updated, {failed} failed")
    return inserted


# =============================================================================
# 5. Fragile States Index 2023
# =============================================================================

# ISO3 lookup for FSI countries (no ISO column in the file)
_FSI_COUNTRY_ISO3 = {
    "Afghanistan": "AFG", "Albania": "ALB", "Algeria": "DZA", "Angola": "AGO",
    "Argentina": "ARG", "Armenia": "ARM", "Australia": "AUS", "Austria": "AUT",
    "Azerbaijan": "AZE", "Bahrain": "BHR", "Bangladesh": "BGD", "Belarus": "BLR",
    "Belgium": "BEL", "Benin": "BEN", "Bhutan": "BTN", "Bolivia": "BOL",
    "Bosnia and Herzegovina": "BIH", "Botswana": "BWA", "Brazil": "BRA",
    "Brunei Darussalam": "BRN", "Bulgaria": "BGR", "Burkina Faso": "BFA",
    "Burundi": "BDI", "Cambodia": "KHM", "Cameroon": "CMR", "Canada": "CAN",
    "Central African Republic": "CAF", "Chad": "TCD", "Chile": "CHL", "China": "CHN",
    "Colombia": "COL", "Comoros": "COM", "Congo Democratic Republic": "COD",
    "Congo Republic": "COG", "Costa Rica": "CRI", "Cote d'Ivoire": "CIV",
    "Croatia": "HRV", "Cuba": "CUB", "Cyprus": "CYP", "Czech Republic": "CZE",
    "Denmark": "DNK", "Djibouti": "DJI", "Dominican Republic": "DOM",
    "Ecuador": "ECU", "Egypt": "EGY", "El Salvador": "SLV",
    "Equatorial Guinea": "GNQ", "Eritrea": "ERI", "Estonia": "EST",
    "Eswatini": "SWZ", "Ethiopia": "ETH", "Fiji": "FJI", "Finland": "FIN",
    "France": "FRA", "Gabon": "GAB", "Gambia": "GMB", "Georgia": "GEO",
    "Germany": "DEU", "Ghana": "GHA", "Greece": "GRC", "Guatemala": "GTM",
    "Guinea": "GIN", "Guinea Bissau": "GNB", "Guyana": "GUY", "Haiti": "HTI",
    "Honduras": "HND", "Hungary": "HUN", "Iceland": "ISL", "India": "IND",
    "Indonesia": "IDN", "Iran": "IRN", "Iraq": "IRQ", "Ireland": "IRL",
    "Israel": "ISR", "Italy": "ITA", "Jamaica": "JAM", "Japan": "JPN",
    "Jordan": "JOR", "Kazakhstan": "KAZ", "Kenya": "KEN",
    "Korea Republic": "KOR", "Korea DPR": "PRK", "Kosovo": "XKX",
    "Kuwait": "KWT", "Kyrgyz Republic": "KGZ", "Laos": "LAO", "Latvia": "LVA",
    "Lebanon": "LBN", "Lesotho": "LSO", "Liberia": "LBR", "Libya": "LBY",
    "Lithuania": "LTU", "Luxembourg": "LUX", "Madagascar": "MDG",
    "Malawi": "MWI", "Malaysia": "MYS", "Mali": "MLI", "Mauritania": "MRT",
    "Mauritius": "MUS", "Mexico": "MEX", "Moldova": "MDA", "Mongolia": "MNG",
    "Montenegro": "MNE", "Morocco": "MAR", "Mozambique": "MOZ", "Myanmar": "MMR",
    "Namibia": "NAM", "Nepal": "NPL", "Netherlands": "NLD", "New Zealand": "NZL",
    "Nicaragua": "NIC", "Niger": "NER", "Nigeria": "NGA", "North Macedonia": "MKD",
    "Norway": "NOR", "Oman": "OMN", "Pakistan": "PAK", "Panama": "PAN",
    "Papua New Guinea": "PNG", "Paraguay": "PRY", "Peru": "PER",
    "Philippines": "PHL", "Poland": "POL", "Portugal": "PRT", "Qatar": "QAT",
    "Romania": "ROU", "Russia": "RUS", "Rwanda": "RWA", "Saudi Arabia": "SAU",
    "Senegal": "SEN", "Serbia": "SRB", "Sierra Leone": "SLE", "Singapore": "SGP",
    "Slovakia": "SVK", "Slovenia": "SVN", "Solomon Islands": "SLB",
    "Somalia": "SOM", "South Africa": "ZAF", "South Sudan": "SSD",
    "Spain": "ESP", "Sri Lanka": "LKA", "Sudan": "SDN", "Suriname": "SUR",
    "Sweden": "SWE", "Switzerland": "CHE", "Syria": "SYR", "Tajikistan": "TJK",
    "Tanzania": "TZA", "Thailand": "THA", "Timor-Leste": "TLS", "Togo": "TGO",
    "Trinidad and Tobago": "TTO", "Tunisia": "TUN", "Turkey": "TUR",
    "Turkmenistan": "TKM", "Uganda": "UGA", "Ukraine": "UKR",
    "United Arab Emirates": "ARE", "United Kingdom": "GBR",
    "United States": "USA", "Uruguay": "URY", "Uzbekistan": "UZB",
    "Venezuela": "VEN", "Vietnam": "VNM", "Yemen": "YEM", "Zambia": "ZMB",
    "Zimbabwe": "ZWE",
}


def ingest_fsi():
    print("\n-- 5. Fragile States Index 2023 --")
    path = os.path.join(DATA_DIR, "Fragile_States_Index_2023.xlsx")
    df = pd.read_excel(path, sheet_name="Sheet1")
    print(f"   Loaded: {len(df)} countries")

    inserted = 0
    failed = 0
    dim_cols = [c for c in df.columns if c not in ["Country", "Year", "Rank", "Total"]]

    sql = sa.text("""
        INSERT INTO dh_country_risk_indices (
            id, source_id, country_name, country_iso3, index_name,
            year, score, rank, subcategories, source_name, ingested_at, updated_at
        ) VALUES (
            :id, :source_id, :country_name, :iso3, 'FSI',
            :year, :score, :rank, :subcategories, 'Fund for Peace', now(), now()
        )
        ON CONFLICT (country_iso3, index_name, year) DO UPDATE SET
            score = EXCLUDED.score,
            rank = EXCLUDED.rank,
            subcategories = EXCLUDED.subcategories,
            updated_at = now()
    """)

    with engine.begin() as conn:
        for _, row in df.iterrows():
            try:
                name = _safe_str(row.get("Country"))
                if not name:
                    continue
                iso3 = _FSI_COUNTRY_ISO3.get(name)
                if not iso3:
                    # Try partial match
                    for k, v in _FSI_COUNTRY_ISO3.items():
                        if name.lower() in k.lower() or k.lower() in name.lower():
                            iso3 = v
                            break
                if not iso3:
                    iso3 = name[:3].upper()
                year = _safe_int(row.get("Year")) or 2023
                rid = _id("fsi", f"{iso3}:{year}")

                subs = {}
                rank_str = _safe_str(row.get("Rank"))
                rank_int = None
                if rank_str:
                    # Extract numeric from "1st", "2nd", etc.
                    import re
                    m = re.search(r"(\d+)", rank_str)
                    if m:
                        rank_int = int(m.group(1))

                for dc in dim_cols:
                    v = _safe_float(row.get(dc))
                    if v is not None:
                        key = dc.split(":")[0].strip().lower().replace(" ", "_")
                        subs[key] = v

                conn.execute(sql, {
                    "id": rid,
                    "source_id": "ds-fsi-2023",
                    "country_name": name,
                    "iso3": iso3,
                    "year": year,
                    "score": _safe_float(row.get("Total")),
                    "rank": rank_int,
                    "subcategories": json.dumps(subs, default=str),
                })
                inserted += 1
            except Exception as e:
                failed += 1
                if failed <= 5:
                    print(f"   ERR: {e}")

    print(f"   Done: {inserted} inserted/updated, {failed} failed")
    return inserted


# =============================================================================
# 6. Freedom House FIW 2013-2024
# =============================================================================

def ingest_freedom_house():
    print("\n-- 6. Freedom House FIW 2013-2024 --")
    path = os.path.join(DATA_DIR, "Freedom_House_FIW_2013_2024.xlsx")
    df = pd.read_excel(path, sheet_name="FIW13-25", skiprows=1)
    print(f"   Loaded: {len(df)} rows")

    inserted = 0
    failed = 0

    sql = sa.text("""
        INSERT INTO dh_country_risk_indices (
            id, source_id, country_name, country_iso3, index_name,
            year, score, rank, subcategories, source_name, ingested_at, updated_at
        ) VALUES (
            :id, :source_id, :country_name, :iso3, 'FH_FIW',
            :year, :score, NULL, :subcategories, 'Freedom House', now(), now()
        )
        ON CONFLICT (country_iso3, index_name, year) DO UPDATE SET
            score = EXCLUDED.score,
            subcategories = EXCLUDED.subcategories,
            updated_at = now()
    """)

    # Build ISO3 lookup from name
    iso3_map = {v: k for k, v in _FSI_COUNTRY_ISO3.items()}
    # Reverse: name -> iso3
    name_to_iso3 = _FSI_COUNTRY_ISO3.copy()

    with engine.begin() as conn:
        for _, row in df.iterrows():
            try:
                name = _safe_str(row.get("Country/Territory"))
                if not name:
                    continue
                edition = _safe_int(row.get("Edition"))
                if not edition:
                    continue

                iso3 = name_to_iso3.get(name)
                if not iso3:
                    for k, v in name_to_iso3.items():
                        if name.lower() in k.lower() or k.lower() in name.lower():
                            iso3 = v
                            break
                if not iso3:
                    iso3 = name[:3].upper()

                rid = _id("fh", f"{iso3}:{edition}")

                pr = _safe_int(row.get("PR rating"))
                cl = _safe_int(row.get("CL rating"))
                # FH score = inverse of ratings (lower rating = better)
                # PR and CL are 1-7, so composite = 14 - (PR + CL) → scale 0-12
                score = None
                if pr is not None and cl is not None:
                    score = float(14 - pr - cl)

                subs = {
                    "status": _safe_str(row.get("Status")),
                    "pr_rating": pr,
                    "cl_rating": cl,
                    "region": _safe_str(row.get("Region")),
                    "c_t": _safe_str(row.get("C/T")),
                }
                # Add subcategory scores (A1, A2, A3, B1-B4, C1-C3, D1-D4, E1-E3, F1-F4, G)
                for col in df.columns:
                    if len(col) <= 4 and col not in ["C/T", "Year"]:
                        v = _safe_int(row.get(col))
                        if v is not None and col not in subs:
                            subs[col] = v

                conn.execute(sql, {
                    "id": rid,
                    "source_id": "ds-freedom-house-fiw",
                    "country_name": name,
                    "iso3": iso3,
                    "year": edition,
                    "score": score,
                    "subcategories": json.dumps({k: v for k, v in subs.items() if v is not None}, default=str),
                })
                inserted += 1
            except Exception as e:
                failed += 1
                if failed <= 5:
                    print(f"   ERR [{name}]: {e}")

    print(f"   Done: {inserted} inserted/updated, {failed} failed")
    return inserted


# =============================================================================
# 7. UNDP HDR Gender Inequality Index
# =============================================================================

def ingest_undp_gii():
    print("\n-- 7. UNDP HDR Gender Inequality Index --")
    path = os.path.join(DATA_DIR, "UNDP_HDR_GII.xlsx")
    df = pd.read_excel(path, sheet_name="Table 5. GII", header=None)

    # Find header row (contains "Country")
    header_row = None
    for i in range(10):
        for j in range(df.shape[1]):
            v = str(df.iloc[i, j]).strip() if pd.notna(df.iloc[i, j]) else ""
            if v == "Country":
                header_row = i
                break
        if header_row is not None:
            break

    if header_row is None:
        # Fallback: row 4 based on preview
        header_row = 4

    # Extract headers and subheaders
    # Main columns: HDI rank, Country, GII Value, GII Rank, Maternal mortality ratio,
    # Adolescent birth rate, Share of seats in parliament,
    # Population with at least some secondary education (Female, Male),
    # Labour force participation rate (Female, Male)
    data = df.iloc[header_row+2:].copy()
    print(f"   Raw rows: {len(data)}")

    inserted = 0
    failed = 0

    sql = sa.text("""
        INSERT INTO dh_country_risk_indices (
            id, source_id, country_name, country_iso3, index_name,
            year, score, rank, subcategories, source_name, ingested_at, updated_at
        ) VALUES (
            :id, :source_id, :country_name, :iso3, 'UNDP_GII',
            2023, :score, :rank, :subcategories, 'UNDP HDR', now(), now()
        )
        ON CONFLICT (country_iso3, index_name, year) DO UPDATE SET
            score = EXCLUDED.score,
            rank = EXCLUDED.rank,
            subcategories = EXCLUDED.subcategories,
            updated_at = now()
    """)

    with engine.begin() as conn:
        for idx in range(len(data)):
            try:
                row = data.iloc[idx]
                hdi_rank = _safe_int(row.iloc[0])
                country = _safe_str(row.iloc[1])
                if not country:
                    continue
                # Skip group headers like "Very high human development"
                if country.lower().startswith(("very high", "high human", "medium human", "low human", "developing", "least", "small island", "oecd", "world", "arab", "east asia", "europe", "latin", "south asia", "sub-saharan")):
                    continue

                gii_value = _safe_float(row.iloc[2])
                gii_rank = _safe_int(row.iloc[4])

                iso3 = _FSI_COUNTRY_ISO3.get(country)
                if not iso3:
                    for k, v in _FSI_COUNTRY_ISO3.items():
                        if country.lower() in k.lower() or k.lower() in country.lower():
                            iso3 = v
                            break
                if not iso3:
                    iso3 = country[:3].upper()

                rid = _id("gii", f"{iso3}:2023")

                subs = {
                    "hdi_rank": hdi_rank,
                    "maternal_mortality_ratio": _safe_float(row.iloc[6]),
                    "adolescent_birth_rate": _safe_float(row.iloc[8]),
                    "parliament_share_pct": _safe_float(row.iloc[10]),
                    "secondary_education_female_pct": _safe_float(row.iloc[12]),
                    "secondary_education_male_pct": _safe_float(row.iloc[14]),
                    "labour_force_female_pct": _safe_float(row.iloc[16]),
                    "labour_force_male_pct": _safe_float(row.iloc[18]),
                }

                conn.execute(sql, {
                    "id": rid,
                    "source_id": "ds-undp-hdr-gii",
                    "country_name": country,
                    "iso3": iso3,
                    "score": gii_value,
                    "rank": gii_rank,
                    "subcategories": json.dumps({k: v for k, v in subs.items() if v is not None}, default=str),
                })
                inserted += 1
            except Exception as e:
                failed += 1
                if failed <= 5:
                    print(f"   ERR: {e}")

    print(f"   Done: {inserted} inserted/updated, {failed} failed")
    return inserted


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Reference Dataset Ingestion")
    print("=" * 60)

    results = {}
    for name, fn in [
        ("sbti", ingest_sbti),
        ("ca100", ingest_ca100),
        ("coal", ingest_coal_tracker),
        ("cpi", ingest_cpi),
        ("fsi", ingest_fsi),
        ("fh", ingest_freedom_house),
        ("gii", ingest_undp_gii),
    ]:
        try:
            results[name] = fn()
        except Exception as e:
            print(f"   FAILED {name}: {e}")
            results[name] = 0

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    total = 0
    for k, v in results.items():
        print(f"  {k:20s}: {v:>6d} rows")
        total += v
    print(f"  {'TOTAL':20s}: {total:>6d} rows")
    print("=" * 60)
