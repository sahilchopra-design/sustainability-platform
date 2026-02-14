"""
Portfolio file upload & parsing service.
Supports CSV and Excel files for portfolio creation.
"""

import csv
import io
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

REQUIRED_COLUMNS = {"name", "sector", "exposure"}

SECTOR_MAP = {
    "power": "Power Generation", "power generation": "Power Generation", "energy": "Power Generation",
    "utilities": "Power Generation", "oil": "Oil & Gas", "oil & gas": "Oil & Gas", "oil and gas": "Oil & Gas",
    "gas": "Oil & Gas", "petroleum": "Oil & Gas",
    "metals": "Metals & Mining", "metals & mining": "Metals & Mining", "mining": "Metals & Mining",
    "steel": "Metals & Mining",
    "automotive": "Automotive", "auto": "Automotive", "vehicles": "Automotive",
    "airlines": "Airlines", "aviation": "Airlines", "transport": "Airlines",
    "real estate": "Real Estate", "property": "Real Estate", "reit": "Real Estate",
}

ASSET_TYPE_MAP = {
    "bond": "Bond", "bonds": "Bond",
    "loan": "Loan", "loans": "Loan",
    "equity": "Equity", "stock": "Equity", "shares": "Equity",
}


def parse_portfolio_csv(content: str, column_mapping: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Parse CSV content into portfolio assets.

    Args:
        content: CSV file content as string
        column_mapping: Optional mapping of CSV columns to standard fields

    Returns:
        {"assets": [...], "errors": [...], "warnings": [...]}
    """
    reader = csv.DictReader(io.StringIO(content))
    raw_columns = reader.fieldnames or []

    # Auto-detect column mapping if not provided
    if not column_mapping:
        column_mapping = _auto_map_columns(raw_columns)

    assets = []
    errors = []
    warnings = []

    for i, row in enumerate(reader, start=2):
        try:
            asset = _parse_row(row, column_mapping, i)
            if asset:
                assets.append(asset)
        except ValueError as e:
            errors.append({"row": i, "error": str(e)})

    if not assets and not errors:
        errors.append({"row": 0, "error": "No data rows found in file"})

    return {
        "assets": assets,
        "errors": errors,
        "warnings": warnings,
        "raw_columns": raw_columns,
        "column_mapping": column_mapping,
        "total_rows": len(assets) + len(errors),
        "valid_rows": len(assets),
    }


def _auto_map_columns(columns: List[str]) -> Dict[str, str]:
    """Auto-detect column mapping from CSV headers."""
    mapping = {}
    col_lower = {c.lower().strip(): c for c in columns}

    name_candidates = ["name", "company", "company_name", "counterparty", "issuer"]
    for nc in name_candidates:
        if nc in col_lower:
            mapping["name"] = col_lower[nc]
            break

    sector_candidates = ["sector", "industry", "category", "segment"]
    for sc in sector_candidates:
        if sc in col_lower:
            mapping["sector"] = col_lower[sc]
            break

    exposure_candidates = ["exposure", "ead", "exposure_at_default", "notional", "amount", "value"]
    for ec in exposure_candidates:
        if ec in col_lower:
            mapping["exposure"] = col_lower[ec]
            break

    optional_maps = {
        "asset_type": ["asset_type", "type", "instrument", "instrument_type"],
        "rating": ["rating", "credit_rating", "grade"],
        "pd": ["pd", "probability_of_default", "base_pd", "default_probability"],
        "lgd": ["lgd", "loss_given_default", "base_lgd"],
        "maturity": ["maturity", "maturity_years", "term", "tenor"],
        "subsector": ["subsector", "sub_sector", "sub_industry"],
        "market_value": ["market_value", "mv", "market_price"],
    }
    for field, candidates in optional_maps.items():
        for c in candidates:
            if c in col_lower:
                mapping[field] = col_lower[c]
                break

    return mapping


def _parse_row(row: Dict, mapping: Dict[str, str], row_num: int) -> Optional[Dict]:
    """Parse a single CSV row into an asset dict."""
    name_col = mapping.get("name")
    sector_col = mapping.get("sector")
    exposure_col = mapping.get("exposure")

    if not name_col or not row.get(name_col, "").strip():
        raise ValueError(f"Missing company name")
    if not exposure_col or not row.get(exposure_col, "").strip():
        raise ValueError(f"Missing exposure value")

    name = row[name_col].strip()

    # Parse exposure
    exp_str = row[exposure_col].strip().replace(",", "").replace("$", "").replace("€", "")
    try:
        exposure = float(exp_str)
    except ValueError:
        raise ValueError(f"Invalid exposure value: {row[exposure_col]}")

    # Parse sector
    raw_sector = row.get(sector_col, "").strip().lower() if sector_col else ""
    sector = SECTOR_MAP.get(raw_sector, "Power Generation")

    # Parse optional fields
    asset_type_col = mapping.get("asset_type")
    raw_type = row.get(asset_type_col, "").strip().lower() if asset_type_col else ""
    asset_type = ASSET_TYPE_MAP.get(raw_type, "Bond")

    rating = row.get(mapping.get("rating", ""), "BBB").strip() or "BBB"
    subsector = row.get(mapping.get("subsector", ""), "").strip() or None

    pd_col = mapping.get("pd")
    try:
        base_pd = float(row.get(pd_col, "0.02").strip()) if pd_col and row.get(pd_col, "").strip() else 0.02
    except ValueError:
        base_pd = 0.02

    lgd_col = mapping.get("lgd")
    try:
        base_lgd = float(row.get(lgd_col, "0.45").strip()) if lgd_col and row.get(lgd_col, "").strip() else 0.45
    except ValueError:
        base_lgd = 0.45

    mat_col = mapping.get("maturity")
    try:
        maturity = int(float(row.get(mat_col, "5").strip())) if mat_col and row.get(mat_col, "").strip() else 5
    except ValueError:
        maturity = 5

    mv_col = mapping.get("market_value")
    try:
        market_value = float(row.get(mv_col, str(exposure)).strip().replace(",", "")) if mv_col and row.get(mv_col, "").strip() else exposure
    except ValueError:
        market_value = exposure

    return {
        "id": str(uuid.uuid4()),
        "asset_type": asset_type,
        "company": {"name": name, "sector": sector, "subsector": subsector},
        "exposure": exposure,
        "market_value": market_value,
        "base_pd": base_pd,
        "base_lgd": base_lgd,
        "rating": rating,
        "maturity_years": maturity,
    }
