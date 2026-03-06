"""
Facilitated Emissions — PCAF Capital Markets Module
Routes: /api/v1/facilitated-emissions/*

PCAF Standard (2nd ed.) — Part C: Capital Markets
Covers underwriting of bonds and equity issuance.

Attribution factor differs from lending:
  Debt underwriting:   AF = underwritten_amount / (total_issuance × 3)   [÷3 = time-in-year]
  Equity underwriting: AF = shares_placed_value / (market_cap × 3)

Reference: PCAF Global GHG Accounting Standard for Financial Industry, Part C (2022)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from db.base import get_db

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/facilitated-emissions",
    tags=["Facilitated Emissions"],
)


# ── Models ────────────────────────────────────────────────────────────────────

class FacilitatedEmissionIn(BaseModel):
    transaction_ref: Optional[str] = None
    issuer_name: str
    issuer_id: Optional[str] = None                    # internal / LEI
    instrument_type: str = "bond"                      # bond | equity | convertible
    transaction_type: str = "underwriting"             # underwriting | placement
    # Deal economics
    underwritten_amount_musd: Optional[float] = None   # bank's book in the deal
    total_issuance_amount_musd: Optional[float] = None # total deal size
    shares_placed_value_musd: Optional[float] = None   # for equity
    market_cap_musd: Optional[float] = None            # for equity
    # Issuer emissions
    issuer_scope1_tco2e: Optional[float] = None
    issuer_scope2_tco2e: Optional[float] = None
    issuer_scope3_tco2e: Optional[float] = None        # include only if material
    include_scope3: bool = False
    pcaf_dqs: Optional[int] = None                     # 1-5
    data_source_type: Optional[str] = "self_reported"
    # Classification
    sector_gics: Optional[str] = None
    country_iso2: Optional[str] = None
    reporting_year: Optional[int] = None
    green_bond: bool = False
    use_of_proceeds: Optional[str] = None              # green | social | sustainability | general
    notes: Optional[str] = None


class FacilitatedEmissionUpdate(BaseModel):
    notes: Optional[str] = None
    pcaf_dqs: Optional[int] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

_DQS_MAP = {
    "direct_measurement": 1,
    "audited_report": 2,
    "self_reported": 3,
    "sector_average": 4,
    "estimated": 5,
}

# PCAF ÷3 factor: bond / equity underwriting attribution = 1/3 due to time-in-year
_PCAF_FACILITATED_FACTOR = 1 / 3


def _compute_facilitated(payload: FacilitatedEmissionIn) -> Dict[str, Any]:
    """
    Compute facilitated emissions and attribution factor.

    Debt underwriting:
      AF = (underwritten / total_issuance) × (1/3)
      Facilitated = AF × (scope1 + scope2 [+ scope3 if included])

    Equity underwriting:
      AF = (shares_placed / market_cap) × (1/3)
      Facilitated = AF × issuer_total_emissions
    """
    result: Dict[str, Any] = {
        "attribution_factor": None,
        "facilitated_tco2e": None,
        "scope1_facilitated": None,
        "scope2_facilitated": None,
        "scope3_facilitated": None,
        "pcaf_dqs_derived": None,
        "methodology_note": None,
    }

    # Resolve DQS
    dqs = payload.pcaf_dqs or _DQS_MAP.get(payload.data_source_type or "self_reported", 3)
    result["pcaf_dqs_derived"] = dqs

    total_issuer_s12 = (payload.issuer_scope1_tco2e or 0) + (payload.issuer_scope2_tco2e or 0)
    scope3 = (payload.issuer_scope3_tco2e or 0) if payload.include_scope3 else 0

    # Attribution factor
    af = None
    if payload.instrument_type in ("bond", "convertible") and payload.instrument_type != "equity":
        # Debt underwriting
        if payload.underwritten_amount_musd and payload.total_issuance_amount_musd:
            af = (
                payload.underwritten_amount_musd
                / payload.total_issuance_amount_musd
                * _PCAF_FACILITATED_FACTOR
            )
            result["methodology_note"] = (
                f"Debt AF = {payload.underwritten_amount_musd}M / "
                f"{payload.total_issuance_amount_musd}M × (1/3)"
            )
    elif payload.instrument_type == "equity":
        # Equity placement
        if payload.shares_placed_value_musd and payload.market_cap_musd:
            af = (
                payload.shares_placed_value_musd
                / payload.market_cap_musd
                * _PCAF_FACILITATED_FACTOR
            )
            result["methodology_note"] = (
                f"Equity AF = {payload.shares_placed_value_musd}M placed / "
                f"{payload.market_cap_musd}M market cap × (1/3)"
            )

    if af is not None:
        result["attribution_factor"] = round(af, 6)
        s1_fac = round(af * (payload.issuer_scope1_tco2e or 0), 2)
        s2_fac = round(af * (payload.issuer_scope2_tco2e or 0), 2)
        s3_fac = round(af * scope3, 2) if scope3 else None
        fac_total = round(af * (total_issuer_s12 + scope3), 2)
        result.update({
            "facilitated_tco2e": fac_total,
            "scope1_facilitated": s1_fac,
            "scope2_facilitated": s2_fac,
            "scope3_facilitated": s3_fac,
        })

    return result


def _ensure_table(db: Session) -> None:
    """Create facilitated_emissions table if absent (migration-free bootstrap)."""
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS facilitated_emissions (
            id SERIAL PRIMARY KEY,
            transaction_ref TEXT UNIQUE,
            issuer_name TEXT NOT NULL,
            issuer_id TEXT,
            instrument_type TEXT,
            transaction_type TEXT,
            underwritten_amount_musd NUMERIC(16,4),
            total_issuance_amount_musd NUMERIC(16,4),
            shares_placed_value_musd NUMERIC(16,4),
            market_cap_musd NUMERIC(16,4),
            issuer_scope1_tco2e NUMERIC(20,4),
            issuer_scope2_tco2e NUMERIC(20,4),
            issuer_scope3_tco2e NUMERIC(20,4),
            include_scope3 BOOLEAN DEFAULT FALSE,
            attribution_factor NUMERIC(10,6),
            facilitated_tco2e NUMERIC(20,4),
            scope1_facilitated NUMERIC(20,4),
            scope2_facilitated NUMERIC(20,4),
            scope3_facilitated NUMERIC(20,4),
            pcaf_dqs INTEGER,
            data_source_type TEXT,
            sector_gics TEXT,
            country_iso2 TEXT,
            reporting_year INTEGER,
            green_bond BOOLEAN DEFAULT FALSE,
            use_of_proceeds TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """))
    db.commit()


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/")
def list_facilitated_emissions(db: Session = Depends(get_db)):
    """Return all facilitated emissions transactions."""
    try:
        _ensure_table(db)
        rows = db.execute(text(
            "SELECT * FROM facilitated_emissions ORDER BY created_at DESC LIMIT 500"
        )).fetchall()
        return [dict(r._mapping) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
def create_facilitated_emission(payload: FacilitatedEmissionIn, db: Session = Depends(get_db)):
    """Record a new facilitated emissions transaction with PCAF computation."""
    _ensure_table(db)

    metrics = _compute_facilitated(payload)

    import uuid
    ref = payload.transaction_ref or f"FE-{uuid.uuid4().hex[:8].upper()}"

    try:
        result = db.execute(text("""
            INSERT INTO facilitated_emissions
              (transaction_ref, issuer_name, issuer_id, instrument_type, transaction_type,
               underwritten_amount_musd, total_issuance_amount_musd,
               shares_placed_value_musd, market_cap_musd,
               issuer_scope1_tco2e, issuer_scope2_tco2e, issuer_scope3_tco2e,
               include_scope3, attribution_factor, facilitated_tco2e,
               scope1_facilitated, scope2_facilitated, scope3_facilitated,
               pcaf_dqs, data_source_type, sector_gics, country_iso2,
               reporting_year, green_bond, use_of_proceeds, notes)
            VALUES
              (:ref, :issuer, :isid, :inst, :ttype,
               :und, :total_iss, :sp, :mcap,
               :s1, :s2, :s3, :inc_s3,
               :af, :fac, :s1f, :s2f, :s3f,
               :dqs, :dst, :sector, :cty,
               :yr, :green, :uop, :notes)
            ON CONFLICT (transaction_ref) DO UPDATE SET
               facilitated_tco2e = EXCLUDED.facilitated_tco2e,
               attribution_factor = EXCLUDED.attribution_factor,
               updated_at = NOW()
            RETURNING id
        """), {
            "ref": ref,
            "issuer": payload.issuer_name,
            "isid": payload.issuer_id,
            "inst": payload.instrument_type,
            "ttype": payload.transaction_type,
            "und": payload.underwritten_amount_musd,
            "total_iss": payload.total_issuance_amount_musd,
            "sp": payload.shares_placed_value_musd,
            "mcap": payload.market_cap_musd,
            "s1": payload.issuer_scope1_tco2e,
            "s2": payload.issuer_scope2_tco2e,
            "s3": payload.issuer_scope3_tco2e,
            "inc_s3": payload.include_scope3,
            "af": metrics["attribution_factor"],
            "fac": metrics["facilitated_tco2e"],
            "s1f": metrics["scope1_facilitated"],
            "s2f": metrics["scope2_facilitated"],
            "s3f": metrics["scope3_facilitated"],
            "dqs": metrics["pcaf_dqs_derived"],
            "dst": payload.data_source_type,
            "sector": payload.sector_gics,
            "cty": payload.country_iso2,
            "yr": payload.reporting_year,
            "green": payload.green_bond,
            "uop": payload.use_of_proceeds,
            "notes": payload.notes,
        })
        new_id = result.fetchone()[0]
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "id": new_id,
        "transaction_ref": ref,
        **metrics,
    }


@router.get("/summary")
def get_facilitated_summary(db: Session = Depends(get_db)):
    """Portfolio-level facilitated emissions summary."""
    try:
        _ensure_table(db)
        row = db.execute(text("""
            SELECT
                COUNT(*) AS transaction_count,
                SUM(facilitated_tco2e) AS total_facilitated_tco2e,
                SUM(scope1_facilitated) AS total_s1,
                SUM(scope2_facilitated) AS total_s2,
                SUM(scope3_facilitated) AS total_s3,
                AVG(pcaf_dqs) AS avg_dqs,
                COUNT(*) FILTER (WHERE green_bond = TRUE) AS green_bond_count,
                SUM(underwritten_amount_musd) AS total_underwritten_musd
            FROM facilitated_emissions
        """)).fetchone()

        # Breakdown by instrument type
        by_inst = db.execute(text("""
            SELECT instrument_type,
                   COUNT(*) AS count,
                   SUM(facilitated_tco2e) AS facilitated_tco2e,
                   SUM(underwritten_amount_musd) AS underwritten_musd
            FROM facilitated_emissions
            GROUP BY instrument_type
            ORDER BY facilitated_tco2e DESC NULLS LAST
        """)).fetchall()

        # Breakdown by sector
        by_sector = db.execute(text("""
            SELECT COALESCE(sector_gics, 'Unknown') AS sector,
                   COUNT(*) AS count,
                   SUM(facilitated_tco2e) AS facilitated_tco2e
            FROM facilitated_emissions
            GROUP BY sector_gics
            ORDER BY facilitated_tco2e DESC NULLS LAST
        """)).fetchall()

        return {
            "totals": {
                "transaction_count": row[0] or 0,
                "total_facilitated_tco2e": float(row[1] or 0),
                "scope1_tco2e": float(row[2] or 0),
                "scope2_tco2e": float(row[3] or 0),
                "scope3_tco2e": float(row[4] or 0),
                "avg_pcaf_dqs": round(float(row[5] or 0), 2),
                "green_bond_count": row[6] or 0,
                "total_underwritten_musd": float(row[7] or 0),
            },
            "by_instrument": [dict(r._mapping) for r in by_inst],
            "by_sector": [dict(r._mapping) for r in by_sector],
            "methodology": {
                "standard": "PCAF Global GHG Accounting Standard for Financial Industry — Part C: Capital Markets (2022)",
                "attribution_formula": "AF = (underwritten/total_issuance) × (1/3) for debt; (shares_placed/market_cap) × (1/3) for equity",
                "pcaf_factor_note": "÷3 reflects time-in-year attribution per PCAF Capital Markets standard",
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{record_id}")
def delete_facilitated_emission(record_id: int, db: Session = Depends(get_db)):
    db.execute(text("DELETE FROM facilitated_emissions WHERE id=:id"), {"id": record_id})
    db.commit()
    return {"status": "deleted"}
