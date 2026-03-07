"""
Violations API routes -- Corporate Violation Tracker queries.

Endpoints:
  GET  /violations/search                     -- search violations with filters
  GET  /violations/companies                  -- top companies by penalties
  GET  /violations/types                      -- violation type breakdown
  GET  /violations/agencies                   -- enforcement agencies
  GET  /violations/sectors                    -- sector breakdown
  GET  /violations/company/{company_name}     -- violations for a company
  GET  /violations/stats                      -- summary statistics
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from db.base import get_db
from api.dependencies import require_min_role

router = APIRouter(prefix="/api/v1/violations", tags=["violations"])


@router.get("/search")
def search_violations(
    company: Optional[str] = Query(None, description="Company name search"),
    parent: Optional[str] = Query(None, description="Parent company filter"),
    violation_type: Optional[str] = Query(None, description="Violation type filter"),
    agency: Optional[str] = Query(None, description="Agency filter"),
    sector: Optional[str] = Query(None, description="Sector filter"),
    country: Optional[str] = Query(None, description="Country ISO3"),
    severity: Optional[str] = Query(None, description="Severity filter"),
    min_penalty: Optional[float] = Query(None, description="Minimum penalty USD"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Search corporate violations with filters."""
    conditions = []
    params = {"limit": limit, "offset": offset}

    if company:
        conditions.append("company_name ILIKE :company")
        params["company"] = f"%{company}%"
    if parent:
        conditions.append("parent_company ILIKE :parent")
        params["parent"] = f"%{parent}%"
    if violation_type:
        conditions.append("violation_type = :vtype")
        params["vtype"] = violation_type
    if agency:
        conditions.append("agency ILIKE :agency")
        params["agency"] = f"%{agency}%"
    if sector:
        conditions.append("sector ILIKE :sector")
        params["sector"] = f"%{sector}%"
    if country:
        conditions.append("country_iso3 = :country")
        params["country"] = country.upper()
    if severity:
        conditions.append("severity = :severity")
        params["severity"] = severity
    if min_penalty is not None:
        conditions.append("penalty_amount_usd >= :min_pen")
        params["min_pen"] = min_penalty

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    rows = db.execute(text(f"""
        SELECT id, company_name, parent_company, country_iso3, sector,
               violation_type, sub_type, agency, violation_date, resolution_date,
               penalty_amount_usd, description, case_id, severity, status,
               repeat_offender
        FROM dh_violation_tracker
        {where}
        ORDER BY penalty_amount_usd DESC NULLS LAST
        LIMIT :limit OFFSET :offset
    """), params).mappings().all()

    total = db.execute(text(f"SELECT COUNT(*) FROM dh_violation_tracker {where}"), params).scalar()
    return {"records": [dict(r) for r in rows], "total": total}


@router.get("/companies")
def violation_companies(
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Top companies by total penalties."""
    rows = db.execute(text("""
        SELECT parent_company, COUNT(*) AS violations,
               SUM(penalty_amount_usd) AS total_penalties_usd,
               MAX(penalty_amount_usd) AS largest_penalty_usd,
               COUNT(DISTINCT violation_type) AS violation_types,
               BOOL_OR(repeat_offender) AS is_repeat_offender
        FROM dh_violation_tracker
        WHERE parent_company IS NOT NULL
        GROUP BY parent_company
        ORDER BY total_penalties_usd DESC NULLS LAST
        LIMIT :limit
    """), {"limit": limit}).mappings().all()
    return {"companies": [dict(r) for r in rows]}


@router.get("/types")
def violation_types(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Violation type breakdown."""
    rows = db.execute(text("""
        SELECT violation_type, COUNT(*) AS count,
               SUM(penalty_amount_usd) AS total_penalties_usd,
               AVG(penalty_amount_usd) AS avg_penalty_usd
        FROM dh_violation_tracker
        GROUP BY violation_type
        ORDER BY total_penalties_usd DESC NULLS LAST
    """)).mappings().all()
    return {"types": [dict(r) for r in rows]}


@router.get("/agencies")
def violation_agencies(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Enforcement agency breakdown."""
    rows = db.execute(text("""
        SELECT agency, COUNT(*) AS count,
               SUM(penalty_amount_usd) AS total_penalties_usd,
               COUNT(DISTINCT company_name) AS companies_affected
        FROM dh_violation_tracker
        WHERE agency IS NOT NULL
        GROUP BY agency
        ORDER BY total_penalties_usd DESC NULLS LAST
    """)).mappings().all()
    return {"agencies": [dict(r) for r in rows]}


@router.get("/sectors")
def violation_sectors(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Sector breakdown."""
    rows = db.execute(text("""
        SELECT sector, COUNT(*) AS violations,
               SUM(penalty_amount_usd) AS total_penalties_usd,
               COUNT(DISTINCT parent_company) AS companies,
               COUNT(DISTINCT violation_type) AS violation_types
        FROM dh_violation_tracker
        WHERE sector IS NOT NULL
        GROUP BY sector
        ORDER BY total_penalties_usd DESC NULLS LAST
    """)).mappings().all()
    return {"sectors": [dict(r) for r in rows]}


@router.get("/company/{company_name}")
def violations_by_company(
    company_name: str,
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Get all violations for a specific company."""
    rows = db.execute(text("""
        SELECT id, company_name, parent_company, country_iso3, sector,
               violation_type, sub_type, agency, violation_date, resolution_date,
               penalty_amount_usd, description, case_id, severity, status
        FROM dh_violation_tracker
        WHERE company_name ILIKE :name OR parent_company ILIKE :name
        ORDER BY violation_date DESC NULLS LAST
    """), {"name": f"%{company_name}%"}).mappings().all()

    if not rows:
        raise HTTPException(status_code=404, detail=f"No violations for {company_name}")
    return {"company": company_name, "violations": [dict(r) for r in rows], "total": len(rows)}


@router.get("/stats")
def violation_stats(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Summary statistics for violations data."""
    total = db.execute(text("SELECT COUNT(*) FROM dh_violation_tracker")).scalar() or 0
    companies = db.execute(text("SELECT COUNT(DISTINCT parent_company) FROM dh_violation_tracker")).scalar() or 0
    total_pen = db.execute(text("SELECT COALESCE(SUM(penalty_amount_usd), 0) FROM dh_violation_tracker")).scalar() or 0
    types = db.execute(text("SELECT COUNT(DISTINCT violation_type) FROM dh_violation_tracker")).scalar() or 0
    agencies = db.execute(text("SELECT COUNT(DISTINCT agency) FROM dh_violation_tracker")).scalar() or 0
    repeat = db.execute(text("SELECT COUNT(*) FROM dh_violation_tracker WHERE repeat_offender = true")).scalar() or 0

    return {
        "violations": {
            "total": total,
            "companies": companies,
            "total_penalties_usd": float(total_pen),
            "violation_types": types,
            "agencies": agencies,
            "repeat_offenders": repeat,
        }
    }
