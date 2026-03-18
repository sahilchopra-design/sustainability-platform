"""
Facilitated Emissions & Insurance-Associated Emissions API
Routes: /api/v1/facilitated-emissions/*

PCAF Global GHG Accounting Standard v2.0
  Part C — Capital Markets (bonds, equity, securitisation, syndicated, advisory)
  Part B — Insurance-Associated Emissions (motor, property, commercial, life/health)

All calculation logic lives in services/facilitated_emissions_engine.py;
this module provides the HTTP layer, request validation, and DB persistence.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from db.base import get_db

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/facilitated-emissions",
    tags=["Facilitated Emissions"],
)

# Lazy-import engine to avoid circular imports at module load
_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        from services.facilitated_emissions_engine import FacilitatedEmissionsEngine
        _engine = FacilitatedEmissionsEngine()
    return _engine


# ═══════════════════════════════════════════════════════════════════════════════
# Request / Response Models
# ═══════════════════════════════════════════════════════════════════════════════

class IssuerEmissionsIn(BaseModel):
    scope1_tco2e: float = 0.0
    scope2_tco2e: float = 0.0
    scope3_tco2e: float = 0.0
    include_scope3: bool = False
    data_source: str = "self_reported"
    reporting_year: int = 2024
    verification_status: str = "unverified"


class FacilitatedDealIn(BaseModel):
    """Comprehensive deal-level input for facilitated emissions calculation."""
    deal_id: Optional[str] = None
    deal_type: str = "bond_underwriting"
    # Issuer
    issuer_name: str
    issuer_id: Optional[str] = None
    issuer_sector_gics: str = "Unknown"
    issuer_country_iso2: str = "US"
    issuer_revenue_musd: Optional[float] = None
    # Deal economics
    underwritten_amount_musd: float = 0.0
    total_deal_size_musd: float = 0.0
    shares_placed_value_musd: float = 0.0
    market_cap_musd: float = 0.0
    tranche_held_musd: float = 0.0
    total_pool_musd: float = 0.0
    arranged_amount_musd: float = 0.0
    total_facility_musd: float = 0.0
    # Bond details
    bond_type: str = "corporate"
    coupon_rate_pct: Optional[float] = None
    maturity_years: Optional[int] = None
    credit_rating: Optional[str] = None
    # Equity details
    ipo_or_secondary: str = "secondary"
    offer_price: Optional[float] = None
    shares_offered: Optional[int] = None
    overallotment_pct: float = 0.0
    # Securitisation details
    securitisation_type: str = "rmbs"
    underlying_asset_count: Optional[int] = None
    weighted_avg_life_years: Optional[float] = None
    # Green / sustainable
    green_bond: bool = False
    use_of_proceeds: str = "general"
    eu_taxonomy_aligned_pct: float = 0.0
    # Emissions
    emissions: Optional[IssuerEmissionsIn] = None
    pcaf_dqs_override: Optional[int] = None
    # Metadata
    transaction_date: Optional[str] = None
    notes: Optional[str] = None


class InsurancePolicyIn(BaseModel):
    """Comprehensive policy-level input for insurance-associated emissions."""
    policy_id: Optional[str] = None
    line_of_business: str = "motor_personal"
    # Policyholder
    policyholder_name: str
    policyholder_id: Optional[str] = None
    policyholder_sector_gics: str = "Unknown"
    policyholder_country_iso2: str = "US"
    # Premium & claims
    gross_written_premium_musd: float = 0.0
    net_earned_premium_musd: float = 0.0
    claims_paid_musd: float = 0.0
    loss_ratio_pct: Optional[float] = None
    # Motor-specific
    vehicle_count: int = 0
    fuel_type: str = "petrol"
    annual_km_per_vehicle: Optional[float] = None
    avg_engine_cc: Optional[int] = None
    # Property-specific
    insured_property_area_m2: float = 0.0
    epc_rating: str = "D"
    building_type: str = "commercial"
    building_year: Optional[int] = None
    # Commercial-specific
    insured_revenue_musd: Optional[float] = None
    nace_sector: Optional[str] = None
    # Direct emissions
    policyholder_scope1_tco2e: Optional[float] = None
    policyholder_scope2_tco2e: Optional[float] = None
    # Data quality
    data_source: str = "sector_average"
    pcaf_dqs_override: Optional[int] = None
    # Metadata
    policy_inception_date: Optional[str] = None
    policy_expiry_date: Optional[str] = None
    reporting_year: int = 2024
    notes: Optional[str] = None


class BatchFacilitatedIn(BaseModel):
    deals: List[FacilitatedDealIn]


class BatchInsuranceIn(BaseModel):
    policies: List[InsurancePolicyIn]


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers — DB persistence
# ═══════════════════════════════════════════════════════════════════════════════

def _ensure_tables(db: Session) -> None:
    """Create facilitated_emissions_v2 and insurance_emissions tables if absent."""
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS facilitated_emissions_v2 (
            id SERIAL PRIMARY KEY,
            deal_id TEXT UNIQUE NOT NULL,
            deal_type TEXT NOT NULL,
            issuer_name TEXT NOT NULL,
            issuer_id TEXT,
            issuer_sector_gics TEXT,
            issuer_country_iso2 TEXT,
            issuer_revenue_musd NUMERIC(16,4),
            underwritten_amount_musd NUMERIC(16,4),
            total_deal_size_musd NUMERIC(16,4),
            shares_placed_value_musd NUMERIC(16,4),
            market_cap_musd NUMERIC(16,4),
            tranche_held_musd NUMERIC(16,4),
            total_pool_musd NUMERIC(16,4),
            arranged_amount_musd NUMERIC(16,4),
            total_facility_musd NUMERIC(16,4),
            bond_type TEXT,
            coupon_rate_pct NUMERIC(8,4),
            maturity_years INTEGER,
            credit_rating TEXT,
            ipo_or_secondary TEXT,
            offer_price NUMERIC(16,4),
            shares_offered BIGINT,
            overallotment_pct NUMERIC(8,4),
            securitisation_type TEXT,
            underlying_asset_count INTEGER,
            weighted_avg_life_years NUMERIC(8,2),
            green_bond BOOLEAN DEFAULT FALSE,
            use_of_proceeds TEXT,
            eu_taxonomy_aligned_pct NUMERIC(8,4),
            issuer_scope1_tco2e NUMERIC(20,4),
            issuer_scope2_tco2e NUMERIC(20,4),
            issuer_scope3_tco2e NUMERIC(20,4),
            include_scope3 BOOLEAN DEFAULT FALSE,
            attribution_factor NUMERIC(12,6),
            attribution_method TEXT,
            facilitated_scope1_tco2e NUMERIC(20,4),
            facilitated_scope2_tco2e NUMERIC(20,4),
            facilitated_scope3_tco2e NUMERIC(20,4),
            facilitated_total_tco2e NUMERIC(20,4),
            pcaf_dqs INTEGER,
            green_classification TEXT,
            methodology_note TEXT,
            warnings TEXT[],
            transaction_date DATE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """))
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS insurance_emissions (
            id SERIAL PRIMARY KEY,
            policy_id TEXT UNIQUE NOT NULL,
            line_of_business TEXT NOT NULL,
            policyholder_name TEXT NOT NULL,
            policyholder_id TEXT,
            policyholder_sector_gics TEXT,
            policyholder_country_iso2 TEXT,
            gross_written_premium_musd NUMERIC(16,4),
            net_earned_premium_musd NUMERIC(16,4),
            claims_paid_musd NUMERIC(16,4),
            loss_ratio_pct NUMERIC(8,4),
            vehicle_count INTEGER,
            fuel_type TEXT,
            annual_km_per_vehicle NUMERIC(12,2),
            insured_property_area_m2 NUMERIC(16,2),
            epc_rating TEXT,
            building_type TEXT,
            insured_revenue_musd NUMERIC(16,4),
            nace_sector TEXT,
            policyholder_scope1_tco2e NUMERIC(20,4),
            policyholder_scope2_tco2e NUMERIC(20,4),
            attribution_factor NUMERIC(12,6),
            attribution_method TEXT,
            insured_scope1_tco2e NUMERIC(20,4),
            insured_scope2_tco2e NUMERIC(20,4),
            insured_total_tco2e NUMERIC(20,4),
            emission_intensity_per_m_premium NUMERIC(12,4),
            pcaf_dqs INTEGER,
            methodology_note TEXT,
            warnings TEXT[],
            policy_inception_date DATE,
            policy_expiry_date DATE,
            reporting_year INTEGER,
            notes TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """))
    db.commit()


def _to_engine_deal(req: FacilitatedDealIn):
    """Convert Pydantic model to engine dataclass."""
    from services.facilitated_emissions_engine import FacilitatedDealInput, IssuerEmissions
    emissions = None
    if req.emissions:
        emissions = IssuerEmissions(
            scope1_tco2e=req.emissions.scope1_tco2e,
            scope2_tco2e=req.emissions.scope2_tco2e,
            scope3_tco2e=req.emissions.scope3_tco2e,
            include_scope3=req.emissions.include_scope3,
            data_source=req.emissions.data_source,
            reporting_year=req.emissions.reporting_year,
            verification_status=req.emissions.verification_status,
        )
    return FacilitatedDealInput(
        deal_id=req.deal_id or f"FE-{uuid.uuid4().hex[:8].upper()}",
        deal_type=req.deal_type,
        issuer_name=req.issuer_name,
        issuer_id=req.issuer_id,
        issuer_sector_gics=req.issuer_sector_gics,
        issuer_country_iso2=req.issuer_country_iso2,
        issuer_revenue_musd=req.issuer_revenue_musd,
        underwritten_amount_musd=req.underwritten_amount_musd,
        total_deal_size_musd=req.total_deal_size_musd,
        shares_placed_value_musd=req.shares_placed_value_musd,
        market_cap_musd=req.market_cap_musd,
        tranche_held_musd=req.tranche_held_musd,
        total_pool_musd=req.total_pool_musd,
        arranged_amount_musd=req.arranged_amount_musd,
        total_facility_musd=req.total_facility_musd,
        bond_type=req.bond_type,
        coupon_rate_pct=req.coupon_rate_pct,
        maturity_years=req.maturity_years,
        credit_rating=req.credit_rating,
        ipo_or_secondary=req.ipo_or_secondary,
        offer_price=req.offer_price,
        shares_offered=req.shares_offered,
        overallotment_pct=req.overallotment_pct,
        securitisation_type=req.securitisation_type,
        underlying_asset_count=req.underlying_asset_count,
        weighted_avg_life_years=req.weighted_avg_life_years,
        green_bond=req.green_bond,
        use_of_proceeds=req.use_of_proceeds,
        eu_taxonomy_aligned_pct=req.eu_taxonomy_aligned_pct,
        emissions=emissions,
        pcaf_dqs_override=req.pcaf_dqs_override,
        transaction_date=req.transaction_date,
        notes=req.notes,
    )


def _to_engine_policy(req: InsurancePolicyIn):
    """Convert Pydantic model to engine dataclass."""
    from services.facilitated_emissions_engine import InsurancePolicyInput
    return InsurancePolicyInput(
        policy_id=req.policy_id or f"INS-{uuid.uuid4().hex[:8].upper()}",
        line_of_business=req.line_of_business,
        policyholder_name=req.policyholder_name,
        policyholder_id=req.policyholder_id,
        policyholder_sector_gics=req.policyholder_sector_gics,
        policyholder_country_iso2=req.policyholder_country_iso2,
        gross_written_premium_musd=req.gross_written_premium_musd,
        net_earned_premium_musd=req.net_earned_premium_musd,
        claims_paid_musd=req.claims_paid_musd,
        loss_ratio_pct=req.loss_ratio_pct,
        vehicle_count=req.vehicle_count,
        fuel_type=req.fuel_type,
        annual_km_per_vehicle=req.annual_km_per_vehicle,
        insured_property_area_m2=req.insured_property_area_m2,
        epc_rating=req.epc_rating,
        building_type=req.building_type,
        insured_revenue_musd=req.insured_revenue_musd,
        nace_sector=req.nace_sector,
        policyholder_scope1_tco2e=req.policyholder_scope1_tco2e,
        policyholder_scope2_tco2e=req.policyholder_scope2_tco2e,
        data_source=req.data_source,
        pcaf_dqs_override=req.pcaf_dqs_override,
        policy_inception_date=req.policy_inception_date,
        policy_expiry_date=req.policy_expiry_date,
        reporting_year=req.reporting_year,
        notes=req.notes,
    )


def _persist_deal(db: Session, req: FacilitatedDealIn, result) -> int:
    """Insert facilitated deal + result into DB, return id."""
    row = db.execute(text("""
        INSERT INTO facilitated_emissions_v2
          (deal_id, deal_type, issuer_name, issuer_id, issuer_sector_gics,
           issuer_country_iso2, issuer_revenue_musd,
           underwritten_amount_musd, total_deal_size_musd,
           shares_placed_value_musd, market_cap_musd,
           tranche_held_musd, total_pool_musd,
           arranged_amount_musd, total_facility_musd,
           bond_type, coupon_rate_pct, maturity_years, credit_rating,
           ipo_or_secondary, offer_price, shares_offered, overallotment_pct,
           securitisation_type, underlying_asset_count, weighted_avg_life_years,
           green_bond, use_of_proceeds, eu_taxonomy_aligned_pct,
           issuer_scope1_tco2e, issuer_scope2_tco2e, issuer_scope3_tco2e,
           include_scope3, attribution_factor, attribution_method,
           facilitated_scope1_tco2e, facilitated_scope2_tco2e,
           facilitated_scope3_tco2e, facilitated_total_tco2e,
           pcaf_dqs, green_classification, methodology_note,
           transaction_date, notes)
        VALUES
          (:did, :dtype, :iname, :iid, :isec, :icty, :irev,
           :und, :tds, :spv, :mcap, :trh, :tpool, :arr, :tfac,
           :btype, :coup, :mat, :crat,
           :ipos, :oprice, :shares, :oa,
           :stype, :uac, :wal,
           :green, :uop, :euta,
           :s1, :s2, :s3, :incs3,
           :af, :am, :fs1, :fs2, :fs3, :ftot,
           :dqs, :gc, :mn, :tdate, :notes)
        ON CONFLICT (deal_id) DO UPDATE SET
           attribution_factor = EXCLUDED.attribution_factor,
           facilitated_total_tco2e = EXCLUDED.facilitated_total_tco2e,
           updated_at = NOW()
        RETURNING id
    """), {
        "did": result.deal_id, "dtype": req.deal_type,
        "iname": req.issuer_name, "iid": req.issuer_id,
        "isec": req.issuer_sector_gics, "icty": req.issuer_country_iso2,
        "irev": req.issuer_revenue_musd,
        "und": req.underwritten_amount_musd, "tds": req.total_deal_size_musd,
        "spv": req.shares_placed_value_musd, "mcap": req.market_cap_musd,
        "trh": req.tranche_held_musd, "tpool": req.total_pool_musd,
        "arr": req.arranged_amount_musd, "tfac": req.total_facility_musd,
        "btype": req.bond_type, "coup": req.coupon_rate_pct,
        "mat": req.maturity_years, "crat": req.credit_rating,
        "ipos": req.ipo_or_secondary, "oprice": req.offer_price,
        "shares": req.shares_offered, "oa": req.overallotment_pct,
        "stype": req.securitisation_type, "uac": req.underlying_asset_count,
        "wal": req.weighted_avg_life_years,
        "green": req.green_bond, "uop": req.use_of_proceeds,
        "euta": req.eu_taxonomy_aligned_pct,
        "s1": req.emissions.scope1_tco2e if req.emissions else None,
        "s2": req.emissions.scope2_tco2e if req.emissions else None,
        "s3": req.emissions.scope3_tco2e if req.emissions else None,
        "incs3": req.emissions.include_scope3 if req.emissions else False,
        "af": result.attribution_factor, "am": result.attribution_method,
        "fs1": result.facilitated_scope1_tco2e,
        "fs2": result.facilitated_scope2_tco2e,
        "fs3": result.facilitated_scope3_tco2e,
        "ftot": result.facilitated_total_tco2e,
        "dqs": result.pcaf_dqs, "gc": result.green_classification,
        "mn": result.methodology_note,
        "tdate": req.transaction_date, "notes": req.notes,
    })
    return row.fetchone()[0]


def _persist_policy(db: Session, req: InsurancePolicyIn, result) -> int:
    """Insert insurance policy + result into DB, return id."""
    row = db.execute(text("""
        INSERT INTO insurance_emissions
          (policy_id, line_of_business, policyholder_name, policyholder_id,
           policyholder_sector_gics, policyholder_country_iso2,
           gross_written_premium_musd, net_earned_premium_musd,
           claims_paid_musd, loss_ratio_pct,
           vehicle_count, fuel_type, annual_km_per_vehicle,
           insured_property_area_m2, epc_rating, building_type,
           insured_revenue_musd, nace_sector,
           policyholder_scope1_tco2e, policyholder_scope2_tco2e,
           attribution_factor, attribution_method,
           insured_scope1_tco2e, insured_scope2_tco2e, insured_total_tco2e,
           emission_intensity_per_m_premium,
           pcaf_dqs, methodology_note,
           policy_inception_date, policy_expiry_date,
           reporting_year, notes)
        VALUES
          (:pid, :lob, :pname, :phid, :psec, :pcty,
           :gwp, :nep, :claims, :lr,
           :vc, :ft, :akm,
           :area, :epc, :bt,
           :irev, :nace,
           :ps1, :ps2,
           :af, :am, :is1, :is2, :itot, :eipm,
           :dqs, :mn,
           :pstart, :pend, :ry, :notes)
        ON CONFLICT (policy_id) DO UPDATE SET
           insured_total_tco2e = EXCLUDED.insured_total_tco2e,
           attribution_factor = EXCLUDED.attribution_factor,
           updated_at = NOW()
        RETURNING id
    """), {
        "pid": result.policy_id, "lob": req.line_of_business,
        "pname": req.policyholder_name, "phid": req.policyholder_id,
        "psec": req.policyholder_sector_gics, "pcty": req.policyholder_country_iso2,
        "gwp": req.gross_written_premium_musd, "nep": req.net_earned_premium_musd,
        "claims": req.claims_paid_musd, "lr": req.loss_ratio_pct,
        "vc": req.vehicle_count, "ft": req.fuel_type,
        "akm": req.annual_km_per_vehicle,
        "area": req.insured_property_area_m2, "epc": req.epc_rating,
        "bt": req.building_type,
        "irev": req.insured_revenue_musd, "nace": req.nace_sector,
        "ps1": req.policyholder_scope1_tco2e, "ps2": req.policyholder_scope2_tco2e,
        "af": result.attribution_factor, "am": result.attribution_method,
        "is1": result.insured_scope1_tco2e, "is2": result.insured_scope2_tco2e,
        "itot": result.insured_total_tco2e,
        "eipm": result.emission_intensity_per_m_premium,
        "dqs": result.pcaf_dqs, "mn": result.methodology_note,
        "pstart": req.policy_inception_date, "pend": req.policy_expiry_date,
        "ry": req.reporting_year, "notes": req.notes,
    })
    return row.fetchone()[0]


def _result_to_dict(r) -> dict:
    """Serialise a FacilitatedEmissionsResult or InsuranceEmissionsResult."""
    return {k: v for k, v in r.__dict__.items()}


# ═══════════════════════════════════════════════════════════════════════════════
# FACILITATED EMISSIONS ENDPOINTS (PCAF Part C)
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/deals", summary="Calculate & record a facilitated emissions deal")
def create_facilitated_deal(req: FacilitatedDealIn, db: Session = Depends(get_db)):
    """Record a capital-markets deal and compute PCAF Part C facilitated emissions."""
    _ensure_tables(db)
    engine = _get_engine()
    deal_input = _to_engine_deal(req)
    result = engine.calculate_facilitated(deal_input)
    try:
        new_id = _persist_deal(db, req, result)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    return {"id": new_id, **_result_to_dict(result)}


@router.post("/deals/batch", summary="Calculate & record multiple facilitated deals")
def create_facilitated_batch(req: BatchFacilitatedIn, db: Session = Depends(get_db)):
    """Batch record capital-markets deals with PCAF Part C calculation."""
    _ensure_tables(db)
    engine = _get_engine()
    inputs = [_to_engine_deal(d) for d in req.deals]
    results, summary = engine.calculate_facilitated_batch(inputs)
    try:
        ids = [_persist_deal(db, d, r) for d, r in zip(req.deals, results)]
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    return {
        "ids": ids,
        "results": [_result_to_dict(r) for r in results],
        "summary": summary.__dict__,
    }


@router.get("/deals", summary="List all facilitated emissions deals")
def list_facilitated_deals(db: Session = Depends(get_db)):
    try:
        _ensure_tables(db)
        rows = db.execute(text(
            "SELECT * FROM facilitated_emissions_v2 ORDER BY created_at DESC LIMIT 500"
        )).fetchall()
        return [dict(r._mapping) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deals/summary", summary="Portfolio-level facilitated emissions summary")
def facilitated_summary(db: Session = Depends(get_db)):
    try:
        _ensure_tables(db)
        row = db.execute(text("""
            SELECT
                COUNT(*) AS deal_count,
                SUM(facilitated_total_tco2e) AS total_facilitated_tco2e,
                SUM(facilitated_scope1_tco2e) AS total_s1,
                SUM(facilitated_scope2_tco2e) AS total_s2,
                SUM(facilitated_scope3_tco2e) AS total_s3,
                AVG(pcaf_dqs) AS avg_dqs,
                COUNT(*) FILTER (WHERE green_bond = TRUE) AS green_count,
                SUM(underwritten_amount_musd) AS total_underwritten_musd,
                SUM(shares_placed_value_musd) AS total_placed_musd,
                SUM(tranche_held_musd) AS total_tranche_musd,
                SUM(arranged_amount_musd) AS total_arranged_musd
            FROM facilitated_emissions_v2
        """)).fetchone()
        by_type = db.execute(text("""
            SELECT deal_type, COUNT(*) AS count,
                   SUM(facilitated_total_tco2e) AS facilitated_tco2e
            FROM facilitated_emissions_v2
            GROUP BY deal_type ORDER BY facilitated_tco2e DESC NULLS LAST
        """)).fetchall()
        by_sector = db.execute(text("""
            SELECT COALESCE(issuer_sector_gics, 'Unknown') AS sector,
                   COUNT(*) AS count,
                   SUM(facilitated_total_tco2e) AS facilitated_tco2e
            FROM facilitated_emissions_v2
            GROUP BY issuer_sector_gics ORDER BY facilitated_tco2e DESC NULLS LAST
        """)).fetchall()
        return {
            "totals": {
                "deal_count": row[0] or 0,
                "total_facilitated_tco2e": float(row[1] or 0),
                "scope1_tco2e": float(row[2] or 0),
                "scope2_tco2e": float(row[3] or 0),
                "scope3_tco2e": float(row[4] or 0),
                "avg_pcaf_dqs": round(float(row[5] or 0), 2),
                "green_deal_count": row[6] or 0,
                "total_underwritten_musd": float(row[7] or 0),
                "total_placed_musd": float(row[8] or 0),
                "total_tranche_musd": float(row[9] or 0),
                "total_arranged_musd": float(row[10] or 0),
            },
            "by_deal_type": [dict(r._mapping) for r in by_type],
            "by_sector": [dict(r._mapping) for r in by_sector],
            "methodology": {
                "standard": "PCAF Global GHG Accounting Standard v2.0 — Part C: Capital Markets (2022)",
                "deal_types_supported": [
                    "bond_underwriting", "equity_placement", "convertible_underwriting",
                    "securitisation", "syndicated_loan", "ipo_underwriting",
                    "advisory_mna", "advisory_restructuring",
                ],
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/deals/{record_id}", summary="Delete a facilitated deal record")
def delete_facilitated_deal(record_id: int, db: Session = Depends(get_db)):
    db.execute(text("DELETE FROM facilitated_emissions_v2 WHERE id=:id"), {"id": record_id})
    db.commit()
    return {"status": "deleted"}


# ═══════════════════════════════════════════════════════════════════════════════
# INSURANCE-ASSOCIATED EMISSIONS ENDPOINTS (PCAF Part B)
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/insurance", summary="Calculate & record insurance-associated emissions")
def create_insurance_emission(req: InsurancePolicyIn, db: Session = Depends(get_db)):
    """Record an insurance policy and compute PCAF Part B emissions."""
    _ensure_tables(db)
    engine = _get_engine()
    policy_input = _to_engine_policy(req)
    result = engine.calculate_insurance(policy_input)
    try:
        new_id = _persist_policy(db, req, result)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    return {"id": new_id, **_result_to_dict(result)}


@router.post("/insurance/batch", summary="Calculate & record multiple insurance policies")
def create_insurance_batch(req: BatchInsuranceIn, db: Session = Depends(get_db)):
    """Batch record insurance policies with PCAF Part B calculation."""
    _ensure_tables(db)
    engine = _get_engine()
    inputs = [_to_engine_policy(p) for p in req.policies]
    results, summary = engine.calculate_insurance_batch(inputs)
    try:
        ids = [_persist_policy(db, p, r) for p, r in zip(req.policies, results)]
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    return {
        "ids": ids,
        "results": [_result_to_dict(r) for r in results],
        "summary": summary.__dict__,
    }


@router.get("/insurance", summary="List all insurance emission records")
def list_insurance_emissions(db: Session = Depends(get_db)):
    try:
        _ensure_tables(db)
        rows = db.execute(text(
            "SELECT * FROM insurance_emissions ORDER BY created_at DESC LIMIT 500"
        )).fetchall()
        return [dict(r._mapping) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insurance/summary", summary="Portfolio-level insurance emissions summary")
def insurance_summary(db: Session = Depends(get_db)):
    try:
        _ensure_tables(db)
        row = db.execute(text("""
            SELECT
                COUNT(*) AS policy_count,
                SUM(insured_total_tco2e) AS total_insured_tco2e,
                SUM(insured_scope1_tco2e) AS total_s1,
                SUM(insured_scope2_tco2e) AS total_s2,
                AVG(pcaf_dqs) AS avg_dqs,
                SUM(gross_written_premium_musd) AS total_gwp_musd
            FROM insurance_emissions
        """)).fetchone()
        by_lob = db.execute(text("""
            SELECT line_of_business, COUNT(*) AS count,
                   SUM(insured_total_tco2e) AS insured_tco2e,
                   SUM(gross_written_premium_musd) AS gwp_musd
            FROM insurance_emissions
            GROUP BY line_of_business ORDER BY insured_tco2e DESC NULLS LAST
        """)).fetchall()
        return {
            "totals": {
                "policy_count": row[0] or 0,
                "total_insured_tco2e": float(row[1] or 0),
                "scope1_tco2e": float(row[2] or 0),
                "scope2_tco2e": float(row[3] or 0),
                "avg_pcaf_dqs": round(float(row[4] or 0), 2),
                "total_gwp_musd": float(row[5] or 0),
            },
            "by_line_of_business": [dict(r._mapping) for r in by_lob],
            "methodology": {
                "standard": "PCAF Insurance-Associated Emissions Standard (2022)",
                "lines_supported": [
                    "motor_personal", "motor_commercial",
                    "property_residential", "property_commercial",
                    "commercial_liability", "commercial_marine",
                    "commercial_energy", "commercial_other",
                    "life", "health",
                ],
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/insurance/{record_id}", summary="Delete an insurance emission record")
def delete_insurance_emission(record_id: int, db: Session = Depends(get_db)):
    db.execute(text("DELETE FROM insurance_emissions WHERE id=:id"), {"id": record_id})
    db.commit()
    return {"status": "deleted"}


# ═══════════════════════════════════════════════════════════════════════════════
# REFERENCE DATA ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/reference/deal-types", summary="Available deal types")
def ref_deal_types():
    return _get_engine().get_deal_types()


@router.get("/reference/insurance-lobs", summary="Available insurance lines of business")
def ref_insurance_lobs():
    return _get_engine().get_insurance_lobs()


@router.get("/reference/sector-intensities", summary="Sector emission intensity registry")
def ref_sector_intensities():
    return _get_engine().get_sector_intensities()


@router.get("/reference/vehicle-factors", summary="Vehicle emission factor registry")
def ref_vehicle_factors():
    return _get_engine().get_vehicle_factors()


@router.get("/reference/building-factors", summary="Building emission factor registry")
def ref_building_factors():
    return _get_engine().get_building_factors()


@router.get("/reference/insurance-lob-factors", summary="Insurance LoB emission factors")
def ref_lob_factors():
    return _get_engine().get_insurance_lob_factors()


# ═══════════════════════════════════════════════════════════════════════════════
# LEGACY COMPATIBILITY — keep old /api/v1/facilitated-emissions/ root endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/", summary="List facilitated emissions (legacy + v2)")
def list_all(db: Session = Depends(get_db)):
    """Unified list combining legacy and v2 facilitated + insurance records."""
    try:
        _ensure_tables(db)
        deals = db.execute(text(
            "SELECT 'facilitated' AS record_type, deal_id AS ref, "
            "issuer_name AS entity_name, deal_type, "
            "facilitated_total_tco2e AS total_tco2e, pcaf_dqs, created_at "
            "FROM facilitated_emissions_v2 "
            "ORDER BY created_at DESC LIMIT 250"
        )).fetchall()
        policies = db.execute(text(
            "SELECT 'insurance' AS record_type, policy_id AS ref, "
            "policyholder_name AS entity_name, line_of_business AS deal_type, "
            "insured_total_tco2e AS total_tco2e, pcaf_dqs, created_at "
            "FROM insurance_emissions "
            "ORDER BY created_at DESC LIMIT 250"
        )).fetchall()
        combined = [dict(r._mapping) for r in deals] + [dict(r._mapping) for r in policies]
        combined.sort(key=lambda x: x.get("created_at") or "", reverse=True)
        return combined[:500]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
