"""
Ingest EFRAG IG3 ESRS Data Points into csrd_esrs_catalog table.

Sources:
  1. EFRAG IG 3 List of ESRS Data Points (1) (1).xlsx  — 1,231 data points
  2. ESRS Set 1.txt  — Full ESRS text for AR/DR extraction

Populates all 42 columns of csrd_esrs_catalog including:
  - Core IG3 fields (ID, ESRS, DR, Paragraph, Related AR, Name, Data Type)
  - AR/DR full text from ESRS Set 1
  - Module mapping to platform modules
  - Phase-in, voluntary, conditional flags
  - Reporting area (GOV, SBM, IRO, MT)
  - Topic/sub-topic derived from standard code
  - SFDR/Pillar3/Benchmark cross-references
"""

import os
import re
import sys
import json
import hashlib
from datetime import datetime, timezone

import openpyxl
import psycopg2
from psycopg2.extras import execute_values

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
EXCEL_PATH = r"C:\Users\SahilChopra\Downloads\EFRAG IG 3 List of ESRS Data Points (1) (1).xlsx"
ESRS_TXT_PATH = r"C:\Users\SahilChopra\Downloads\ESRS Set 1.txt"
DB_URL = "postgresql://postgres.kytzcbipsghprsqoalvi:KimiaAImpact2026@aws-1-us-east-2.pooler.supabase.com:5432/postgres"

# Sheets to process (skip Index)
SHEETS = [
    "ESRS 2", "ESRS 2 MDR",
    "ESRS E1", "ESRS E2", "ESRS E3", "ESRS E4", "ESRS E5",
    "ESRS S1", "ESRS S2", "ESRS S3", "ESRS S4",
    "ESRS G1",
]

# ---------------------------------------------------------------------------
# Module mapping: standard_code -> platform module
# ---------------------------------------------------------------------------
MODULE_MAP = {
    "ESRS 2":  "regulatory_csrd",
    "E1":      "climate_risk",
    "E2":      "csrd_e2_pollution",
    "E3":      "nature_risk",
    "E4":      "nature_risk",
    "E5":      "csrd_e5_circular",
    "S1":      "csrd_s1_workforce",
    "S2":      "supply_chain",
    "S3":      "csrd_s3_communities",
    "S4":      "csrd_s4_consumers",
    "G1":      "governance",
}

# Topic / sub-topic derivation
TOPIC_MAP = {
    "ESRS 2": ("General Disclosures", "Cross-cutting"),
    "E1":     ("Climate Change", "Environmental"),
    "E2":     ("Pollution", "Environmental"),
    "E3":     ("Water and Marine Resources", "Environmental"),
    "E4":     ("Biodiversity and Ecosystems", "Environmental"),
    "E5":     ("Resource Use and Circular Economy", "Environmental"),
    "S1":     ("Own Workforce", "Social"),
    "S2":     ("Workers in the Value Chain", "Social"),
    "S3":     ("Affected Communities", "Social"),
    "S4":     ("Consumers and End-users", "Social"),
    "G1":     ("Business Conduct", "Governance"),
}

# Data type mapping from IG3 to our disclosure_type
DTYPE_MAP = {
    "narrative":      "qualitative",
    "semi-narrative":  "qualitative",
    "percent":        "quantitative",
    "monetary":       "quantitative",
    "integer":        "quantitative",
    "decimal":        "quantitative",
    "currency":       "quantitative",
    "date":           "quantitative",
    "boolean":        "quantitative",
    "table":          "quantitative",
    "enum":           "qualitative",
    "list":           "qualitative",
    "text block":     "qualitative",
    "mdr-p":          "policy",
    "mdr-a":          "action",
    "mdr-t":          "target",
    "mdr-m":          "metric",
}

# Unit of measure inference
UNIT_MAP = {
    "percent":   "%",
    "monetary":  "EUR",
    "currency":  "EUR",
    "integer":   "count",
    "decimal":   "ratio",
}


def derive_reporting_area(dr_code: str) -> str:
    """Derive reporting area from DR code."""
    dr_upper = (dr_code or "").strip().upper()
    if "GOV" in dr_upper:
        return "GOV"
    if "SBM" in dr_upper:
        return "SBM"
    if "IRO" in dr_upper:
        return "IRO"
    if "MDR-P" in dr_upper:
        return "IRO"
    if "MDR-A" in dr_upper:
        return "IRO"
    if "MDR-T" in dr_upper:
        return "MT"
    if "MDR-M" in dr_upper:
        return "MT"
    # Numbered DRs (e.g., E1-1 through E1-9) are metrics/targets
    return "MT"


def make_indicator_code(dp_id: str, esrs: str) -> str:
    """
    Normalize IG3 ID to our indicator_code format.
    E.g. 'E1-1_01' stays as is, 'BP-1_01' -> 'ESRS2_BP-1_01'
    """
    dp_id = (dp_id or "").strip()
    esrs_clean = (esrs or "").strip().replace("ESRS ", "")
    # If ID already starts with E/S/G prefix, keep it
    if dp_id and dp_id[0] in ("E", "S", "G"):
        return dp_id
    # MDR prefixes
    if dp_id.startswith("MDR"):
        return f"ESRS2_{dp_id}"
    # BP, GOV, SBM, IRO prefixes (ESRS 2)
    return f"ESRS2_{dp_id}" if esrs_clean == "ESRS 2" or esrs_clean == "2" else dp_id


def make_uuid(indicator_code: str) -> str:
    """Deterministic UUID from indicator_code."""
    h = hashlib.sha256(f"esrs_catalog:{indicator_code}".encode()).hexdigest()
    return f"{h[:8]}-{h[8:12]}-4{h[13:16]}-a{h[17:20]}-{h[20:32]}"


def normalize_standard_code(esrs_val: str) -> str:
    """Normalize ESRS column to standard code."""
    v = (esrs_val or "").strip()
    if v in ("ESRS 2", "2"):
        return "ESRS 2"
    # Remove leading "ESRS " if present
    v = v.replace("ESRS ", "")
    return v


# ---------------------------------------------------------------------------
# ESRS Set 1 text parser — extract AR text per standard
# ---------------------------------------------------------------------------
def parse_esrs_text(filepath: str) -> dict:
    """
    Parse the ESRS Set 1 full text to extract:
      1. AR paragraphs grouped by standard
      2. DR full names and text grouped by standard

    Returns:
      {
        "ar": {
            "ESRS 1": {"AR 1": "text...", "AR 2": "text..."},
            "E1":     {"AR 1": "text...", ...},
            ...
        },
        "dr": {
            "E1": {
                "E1-1": {"name": "Transition plan...", "text": "paragraph text..."},
                ...
            }
        }
      }
    """
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    lines = text.split("\n")
    result = {"ar": {}, "dr": {}}

    # Detect standard boundaries
    # Standards appear as "ESRS 1", "ESRS 2", "ESRS E1" etc. as section headers
    standard_breaks = []
    std_pattern = re.compile(
        r"^(ESRS\s+(?:1|2|E[1-5]|S[1-4]|G1))\s*$"
    )
    for i, line in enumerate(lines):
        m = std_pattern.match(line.strip())
        if m:
            standard_breaks.append((i, m.group(1)))

    # Parse AR paragraphs per standard section
    ar_pattern = re.compile(r"^AR\s+(\d+)\.")
    for idx, (start_line, std_name) in enumerate(standard_breaks):
        end_line = standard_breaks[idx + 1][0] if idx + 1 < len(standard_breaks) else len(lines)
        section_lines = lines[start_line:end_line]

        std_key = std_name.replace("ESRS ", "")
        if std_key in ("1", "2"):
            std_key = f"ESRS {std_key}"

        ar_dict = {}
        current_ar = None
        current_text = []

        for sline in section_lines:
            m = ar_pattern.match(sline.strip())
            if m:
                # Save previous AR
                if current_ar:
                    ar_dict[current_ar] = " ".join(current_text).strip()
                current_ar = f"AR {m.group(1)}"
                # Start collecting text after "AR N."
                remainder = sline.strip()[len(f"AR {m.group(1)}."):].strip()
                current_text = [remainder] if remainder else []
            elif current_ar:
                stripped = sline.strip()
                if stripped:
                    current_text.append(stripped)
                # Stop on next numbered paragraph (e.g., "45." or next AR)
                if re.match(r"^\d+\.\s*$", stripped):
                    ar_dict[current_ar] = " ".join(current_text[:-1]).strip()
                    current_ar = None
                    current_text = []

        # Save last AR
        if current_ar:
            ar_dict[current_ar] = " ".join(current_text).strip()

        if ar_dict:
            result["ar"][std_key] = ar_dict

    # Parse DR names per standard
    dr_name_pattern = re.compile(
        r"Disclosure Requirement\s+((?:E[1-5]|S[1-4]|G1)[-.]\d+)\s*[-\u2013\u2014]\s*(.+)"
    )
    for i, line in enumerate(lines):
        m = dr_name_pattern.match(line.strip())
        if m:
            dr_code = m.group(1).strip()
            dr_name = m.group(2).strip()
            # Determine standard from DR code
            std_match = re.match(r"(E[1-5]|S[1-4]|G1)", dr_code)
            if std_match:
                std_key = std_match.group(1)
                if std_key not in result["dr"]:
                    result["dr"][std_key] = {}

                # Collect paragraph text (next ~20 lines)
                para_text = []
                for j in range(i + 1, min(i + 30, len(lines))):
                    pline = lines[j].strip()
                    if not pline:
                        continue
                    # Stop at next DR or section heading
                    if pline.startswith("Disclosure Requirement") or re.match(r"^\d+\.\d+\s", pline):
                        break
                    # Stop at paragraph numbers like "14."
                    if re.match(r"^\d+\.$", pline):
                        break
                    para_text.append(pline)

                result["dr"][std_key][dr_code] = {
                    "name": dr_name,
                    "text": " ".join(para_text[:5]).strip()[:2000],  # Cap at 2000 chars
                }

    return result


# ---------------------------------------------------------------------------
# Excel parser
# ---------------------------------------------------------------------------
def parse_ig3_excel(filepath: str) -> list:
    """
    Parse all sheets from EFRAG IG3 Excel.
    Returns list of dicts, one per data point.
    """
    wb = openpyxl.load_workbook(filepath, read_only=True)
    rows = []

    for sheet_name in SHEETS:
        ws = wb[sheet_name]
        header_row = None
        header_map = {}

        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i == 0:
                # Instructions row — skip
                continue
            if i == 1:
                # Header row
                header_row = [str(c or "").strip() for c in row]
                for j, col_name in enumerate(header_row):
                    col_lower = col_name.lower()
                    if col_lower == "id":
                        header_map["id"] = j
                    elif col_lower == "esrs":
                        header_map["esrs"] = j
                    elif col_lower == "dr":
                        header_map["dr"] = j
                    elif col_lower == "paragraph":
                        header_map["paragraph"] = j
                    elif "related ar" in col_lower:
                        header_map["related_ar"] = j
                    elif col_lower == "name":
                        header_map["name"] = j
                    elif col_lower == "data type":
                        header_map["data_type"] = j
                    elif "conditional" in col_lower:
                        header_map["conditional"] = j
                    elif col_lower.startswith("may"):
                        header_map["may"] = j
                    elif "appendix b" in col_lower or "sfdr" in col_lower:
                        header_map["appendix_b"] = j
                    elif "less than 750" in col_lower or "less 750" in col_lower or "with less" in col_lower:
                        header_map["phase_in_750"] = j
                    elif "applicable to all" in col_lower or "all undertakings" in col_lower:
                        header_map["phase_in_all"] = j
                continue

            # Data rows
            vals = list(row)
            dp_id = str(vals[header_map.get("id", 0)] or "").strip()
            if not dp_id:
                continue
            # Skip section header rows (IDs must be short code-like patterns)
            if len(dp_id) > 40 or " " in dp_id[:5]:
                continue

            esrs_val = str(vals[header_map.get("esrs", 1)] or "").strip()
            dr_val = str(vals[header_map.get("dr", 2)] or "").strip()
            para_val = str(vals[header_map.get("paragraph", 3)] or "").strip()
            ar_val = str(vals[header_map.get("related_ar", 4)] or "").strip()
            name_val = str(vals[header_map.get("name", 5)] or "").strip()
            dtype_val = str(vals[header_map.get("data_type", 6)] or "").strip().lower()
            cond_val = str(vals[header_map.get("conditional", 7)] or "").strip()
            may_val = str(vals[header_map.get("may", 8)] or "").strip()

            # Optional columns — handle missing indices
            app_b_val = ""
            if "appendix_b" in header_map and header_map["appendix_b"] < len(vals):
                app_b_val = str(vals[header_map["appendix_b"]] or "").strip()
            p750_val = ""
            if "phase_in_750" in header_map and header_map["phase_in_750"] < len(vals):
                p750_val = str(vals[header_map["phase_in_750"]] or "").strip()
            pall_val = ""
            if "phase_in_all" in header_map and header_map["phase_in_all"] < len(vals):
                pall_val = str(vals[header_map["phase_in_all"]] or "").strip()

            rows.append({
                "dp_id": dp_id,
                "esrs": esrs_val,
                "dr": dr_val,
                "paragraph": para_val,
                "related_ar": ar_val if ar_val and ar_val.lower() != "none" else None,
                "name": name_val,
                "data_type": dtype_val,
                "conditional": cond_val if cond_val and cond_val.lower() != "none" else None,
                "may": may_val,
                "appendix_b": app_b_val if app_b_val and app_b_val.lower() != "none" else None,
                "phase_in_750": p750_val if p750_val and p750_val.lower() != "none" else None,
                "phase_in_all": pall_val if pall_val and pall_val.lower() != "none" else None,
                "sheet": sheet_name,
            })

    wb.close()
    return rows


# ---------------------------------------------------------------------------
# AR text resolver
# ---------------------------------------------------------------------------
def resolve_ar_text(related_ar: str, standard_code: str, ar_data: dict) -> str:
    """
    Resolve AR references to full text.
    related_ar might be: "AR 1", "AR 1- AR 8", "AR 21", "AR 6 - AR7"
    """
    if not related_ar:
        return None

    # Normalize standard code for lookup
    std_key = standard_code
    if std_key in ("ESRS 2", "2"):
        std_key = "ESRS 2"

    std_ars = ar_data.get(std_key, {})
    if not std_ars:
        return None

    # Parse AR references
    # Handle range: "AR 1- AR 8", "AR 6 - AR7", "AR 1 - AR 5"
    range_match = re.match(r"AR\s*(\d+)\s*[-\u2013]\s*AR\s*(\d+)", related_ar)
    if range_match:
        start_ar = int(range_match.group(1))
        end_ar = int(range_match.group(2))
        texts = []
        for n in range(start_ar, end_ar + 1):
            key = f"AR {n}"
            if key in std_ars:
                texts.append(f"[{key}] {std_ars[key][:500]}")
        return "\n\n".join(texts) if texts else None

    # Single AR: "AR 1", "AR 21"
    single_match = re.match(r"AR\s*(\d+)", related_ar)
    if single_match:
        key = f"AR {single_match.group(1)}"
        if key in std_ars:
            return f"[{key}] {std_ars[key][:1500]}"

    return None


# ---------------------------------------------------------------------------
# Main ingestion
# ---------------------------------------------------------------------------
def main():
    print("=" * 70)
    print("ESRS Catalog Ingestion — EFRAG IG3 Data Points + ESRS Set 1 AR/DR")
    print("=" * 70)

    # 1. Parse ESRS Set 1 text for AR/DR
    print("\n[1/4] Parsing ESRS Set 1 text for AR/DR content...")
    esrs_text = parse_esrs_text(ESRS_TXT_PATH)
    total_ars = sum(len(v) for v in esrs_text["ar"].values())
    total_drs = sum(len(v) for v in esrs_text["dr"].values())
    print(f"  Extracted {total_ars} AR paragraphs across {len(esrs_text['ar'])} standards")
    print(f"  Extracted {total_drs} DR definitions across {len(esrs_text['dr'])} standards")
    for std, ars in sorted(esrs_text["ar"].items()):
        print(f"    {std}: {len(ars)} ARs")

    # 2. Parse IG3 Excel
    print("\n[2/4] Parsing EFRAG IG3 Excel data points...")
    dp_rows = parse_ig3_excel(EXCEL_PATH)
    print(f"  Parsed {len(dp_rows)} data points from {len(SHEETS)} sheets")

    # Count per sheet
    from collections import Counter
    sheet_counts = Counter(r["sheet"] for r in dp_rows)
    for sheet, count in sorted(sheet_counts.items()):
        print(f"    {sheet}: {count}")

    # 3. Build catalog records
    print("\n[3/4] Building catalog records with AR/DR text + module mapping...")
    records = []
    seen_codes = set()
    skipped = 0

    for dp in dp_rows:
        indicator_code = make_indicator_code(dp["dp_id"], dp["esrs"])
        if indicator_code in seen_codes:
            skipped += 1
            continue
        seen_codes.add(indicator_code)

        std_code = normalize_standard_code(dp["esrs"])
        topic_info = TOPIC_MAP.get(std_code, ("Other", "Other"))
        module = MODULE_MAP.get(std_code, "regulatory_csrd")

        # Derive reporting area
        reporting_area = derive_reporting_area(dp["dr"])

        # Resolve AR text
        ar_text = resolve_ar_text(dp["related_ar"], std_code, esrs_text["ar"])

        # Resolve DR name and text
        dr_code = dp["dr"].strip()
        # Extract base DR code (e.g., "E1-1" from " E1-1 ")
        dr_code_clean = re.sub(r"\s+", "", dr_code)
        dr_info = None
        if std_code in esrs_text["dr"]:
            dr_info = esrs_text["dr"][std_code].get(dr_code_clean)

        dr_full_name = dr_info["name"] if dr_info else None
        dr_text = dr_info["text"] if dr_info else None

        # Disclosure type mapping
        disclosure_type = DTYPE_MAP.get(dp["data_type"], "qualitative")

        # Unit of measure
        unit = UNIT_MAP.get(dp["data_type"])

        # Is voluntary? (May [V])
        is_voluntary = bool(dp["may"] and dp["may"].strip().upper() == "V")

        # Is mandatory? Conditional → not mandatory, voluntary → not mandatory
        is_mandatory = not dp["conditional"] and not is_voluntary

        # Phase-in status
        phase_in = "none"
        if dp["phase_in_750"]:
            p = dp["phase_in_750"].strip()
            if "1 year" in p:
                phase_in = "phase_in_year_1"
            elif "2 year" in p:
                phase_in = "phase_in_year_2"
            elif p:
                phase_in = "phase_in"
        if dp["phase_in_all"]:
            p = dp["phase_in_all"].strip()
            if "1 year" in p:
                phase_in = "phase_in_year_1"
            elif "2 year" in p:
                phase_in = "phase_in_year_2"
            elif p:
                phase_in = "phase_in"

        # SME exemption flag
        smei_exemption = bool(dp["phase_in_750"])

        # Always material? ESRS 2 + IRO-1 data points are always material
        always_material = std_code == "ESRS 2" and "MDR" not in dp["dp_id"]

        record = (
            make_uuid(indicator_code),         # id
            indicator_code,                     # indicator_code
            std_code,                           # standard_code
            dr_code_clean,                      # disclosure_requirement
            dp["dp_id"],                        # data_point_code
            dp["paragraph"],                    # paragraph_ref
            topic_info[0],                      # topic
            topic_info[1],                      # sub_topic
            dp["name"][:1000],                  # indicator_name
            dp["name"],                         # indicator_description
            disclosure_type,                    # disclosure_type
            is_mandatory,                       # is_mandatory
            False,                              # is_sector_specific
            None,                               # applicable_sectors (JSONB)
            phase_in,                           # esrs_phase_in
            smei_exemption,                     # smei_exemption
            unit,                               # unit_of_measure
            unit,                               # preferred_unit
            None,                               # allowed_units (JSONB)
            None,                               # calculation_method
            None,                               # reference_standard
            None,                               # xbrl_tag
            None,                               # gri_equivalent
            None,                               # tcfd_pillar
            None,                               # issb_equivalent
            None,                               # brsr_equivalent
            None,                               # sdg_alignment (JSONB)
            always_material,                    # always_material
            None,                               # materiality_assessment_guidance
            datetime.now(timezone.utc),         # created_at
            datetime.now(timezone.utc),         # updated_at
            dp["related_ar"],                   # related_ar
            ar_text,                            # ar_text
            dr_text,                            # dr_text
            dr_full_name,                       # dr_full_name
            dp["conditional"],                  # conditional_or_alternative
            is_voluntary,                       # is_voluntary
            dp["appendix_b"],                   # sfdr_pillar3_benchmark
            dp["phase_in_750"],                 # phase_in_less_750
            dp["phase_in_all"],                 # phase_in_all_undertakings
            module,                             # module_mapping
            reporting_area,                     # reporting_area
        )
        records.append(record)

    print(f"  Built {len(records)} unique records ({skipped} duplicates skipped)")

    # 4. Insert into database
    print(f"\n[4/4] Upserting {len(records)} records into csrd_esrs_catalog...")
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cur = conn.cursor()

    # Clear existing data
    cur.execute("DELETE FROM csrd_esrs_catalog")
    print(f"  Cleared existing rows")

    # Insert
    insert_sql = """
        INSERT INTO csrd_esrs_catalog (
            id, indicator_code, standard_code, disclosure_requirement,
            data_point_code, paragraph_ref, topic, sub_topic,
            indicator_name, indicator_description, disclosure_type,
            is_mandatory, is_sector_specific, applicable_sectors,
            esrs_phase_in, smei_exemption, unit_of_measure, preferred_unit,
            allowed_units, calculation_method, reference_standard, xbrl_tag,
            gri_equivalent, tcfd_pillar, issb_equivalent, brsr_equivalent,
            sdg_alignment, always_material, materiality_assessment_guidance,
            created_at, updated_at,
            related_ar, ar_text, dr_text, dr_full_name,
            conditional_or_alternative, is_voluntary, sfdr_pillar3_benchmark,
            phase_in_less_750, phase_in_all_undertakings,
            module_mapping, reporting_area
        ) VALUES %s
    """

    # Insert in batches of 200
    batch_size = 200
    inserted = 0
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        execute_values(cur, insert_sql, batch)
        inserted += len(batch)
        print(f"  Inserted batch {i // batch_size + 1}: {inserted}/{len(records)}")

    # Verify
    cur.execute("SELECT COUNT(*) FROM csrd_esrs_catalog")
    total = cur.fetchone()[0]
    print(f"\n  Total rows in csrd_esrs_catalog: {total}")

    # Summary by standard
    cur.execute("""
        SELECT standard_code, COUNT(*),
               COUNT(*) FILTER (WHERE related_ar IS NOT NULL) as with_ar,
               COUNT(*) FILTER (WHERE ar_text IS NOT NULL) as with_ar_text,
               COUNT(*) FILTER (WHERE dr_full_name IS NOT NULL) as with_dr_name
        FROM csrd_esrs_catalog
        GROUP BY standard_code
        ORDER BY standard_code
    """)
    print("\n  Summary by standard:")
    print(f"  {'Standard':<12} {'Total':>6} {'w/AR ref':>8} {'w/AR text':>9} {'w/DR name':>9}")
    print(f"  {'-'*44}")
    for row in cur.fetchall():
        print(f"  {row[0]:<12} {row[1]:>6} {row[2]:>8} {row[3]:>9} {row[4]:>9}")

    # Summary by module
    cur.execute("""
        SELECT module_mapping, COUNT(*)
        FROM csrd_esrs_catalog
        GROUP BY module_mapping
        ORDER BY COUNT(*) DESC
    """)
    print("\n  Summary by platform module:")
    for row in cur.fetchall():
        print(f"    {row[0]:<25} {row[1]:>5} data points")

    # Summary by reporting area
    cur.execute("""
        SELECT reporting_area, COUNT(*)
        FROM csrd_esrs_catalog
        GROUP BY reporting_area
        ORDER BY COUNT(*) DESC
    """)
    print("\n  Summary by reporting area:")
    for row in cur.fetchall():
        print(f"    {row[0]:<10} {row[1]:>5} data points")

    # Summary by disclosure type
    cur.execute("""
        SELECT disclosure_type, COUNT(*)
        FROM csrd_esrs_catalog
        GROUP BY disclosure_type
        ORDER BY COUNT(*) DESC
    """)
    print("\n  Summary by disclosure type:")
    for row in cur.fetchall():
        print(f"    {row[0]:<15} {row[1]:>5} data points")

    conn.close()
    print("\n" + "=" * 70)
    print("DONE — ESRS catalog fully populated")
    print("=" * 70)


if __name__ == "__main__":
    main()
