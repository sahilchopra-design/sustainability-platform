"""
Climate Action 100+ Net Zero Company Benchmark Routes
Endpoints for searching, filtering and retrieving CA100+ assessment data.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from db.base import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/ca100", tags=["CA100+ Benchmark"])


# ─────────────────────────────────────────────────────────
# Pydantic models
# ─────────────────────────────────────────────────────────
class CA100CompanySummary(BaseModel):
    id: str
    company_name: str
    isin: Optional[str] = None
    hq_location: Optional[str] = None
    hq_region: Optional[str] = None
    sector_cluster: Optional[str] = None
    sector: Optional[str] = None
    overall_assessment: Optional[str] = None
    assessment_year: Optional[int] = None


class CA100CompanyDetail(BaseModel):
    id: str
    company_name: str
    isin: Optional[str] = None
    hq_location: Optional[str] = None
    hq_region: Optional[str] = None
    sector_cluster: Optional[str] = None
    sector: Optional[str] = None
    secondary_sector: Optional[str] = None
    scope3_category: Optional[str] = None
    indicator_1_score: Optional[str] = None
    indicator_2_score: Optional[str] = None
    indicator_3_score: Optional[str] = None
    indicator_4_score: Optional[str] = None
    indicator_5_score: Optional[str] = None
    indicator_6_score: Optional[str] = None
    indicator_7_score: Optional[str] = None
    indicator_8_score: Optional[str] = None
    indicator_9_score: Optional[str] = None
    indicator_10_score: Optional[str] = None
    overall_assessment: Optional[str] = None
    assessment_year: Optional[int] = None
    raw_record: Optional[dict] = None
    ingested_at: Optional[str] = None


class CA100SectorSummary(BaseModel):
    sector_cluster: str
    sector: Optional[str] = None
    company_count: int
    avg_indicator_scores: dict


# ─────────────────────────────────────────────────────────
# Indicator label mapping
# ─────────────────────────────────────────────────────────
INDICATOR_LABELS = {
    "indicator_1_score": "Net Zero GHG Emissions by 2050 Ambition",
    "indicator_2_score": "Long-term GHG Reduction Target",
    "indicator_3_score": "Medium-term GHG Reduction Target",
    "indicator_4_score": "Short-term GHG Reduction Target",
    "indicator_5_score": "Decarbonisation Strategy",
    "indicator_6_score": "Capital Allocation Alignment",
    "indicator_7_score": "Climate Policy Engagement",
    "indicator_8_score": "Climate Governance",
    "indicator_9_score": "Just Transition",
    "indicator_10_score": "TCFD Disclosure",
}


# ─────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────
@router.get("/companies")
def list_ca100_companies(
    q: Optional[str] = Query(None, description="Search company name or ISIN"),
    sector_cluster: Optional[str] = Query(None),
    sector: Optional[str] = Query(None),
    hq_region: Optional[str] = Query(None),
    overall_assessment: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List and search CA100+ companies with optional filters."""
    try:
        clauses = []
        params: dict = {}

        if q:
            clauses.append(
                "(LOWER(company_name) LIKE :q OR LOWER(isin) LIKE :q)"
            )
            params["q"] = f"%{q.lower()}%"
        if sector_cluster:
            clauses.append("sector_cluster = :sc")
            params["sc"] = sector_cluster
        if sector:
            clauses.append("sector = :sec")
            params["sec"] = sector
        if hq_region:
            clauses.append("hq_region = :reg")
            params["reg"] = hq_region
        if overall_assessment:
            clauses.append("overall_assessment = :oa")
            params["oa"] = overall_assessment

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""

        count_row = db.execute(
            text(f"SELECT COUNT(*) FROM dh_ca100_assessments {where}"), params
        ).fetchone()
        total = count_row[0]

        rows = db.execute(
            text(f"""
                SELECT id, company_name, isin, hq_location, hq_region,
                       sector_cluster, sector, overall_assessment, assessment_year
                FROM dh_ca100_assessments
                {where}
                ORDER BY company_name
                LIMIT :lim OFFSET :off
            """),
            {**params, "lim": limit, "off": offset},
        ).fetchall()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "companies": [
                {
                    "id": r[0], "company_name": r[1], "isin": r[2],
                    "hq_location": r[3], "hq_region": r[4],
                    "sector_cluster": r[5], "sector": r[6],
                    "overall_assessment": r[7], "assessment_year": r[8],
                }
                for r in rows
            ],
        }
    except Exception as exc:
        logger.exception("CA100 list error")
        raise HTTPException(500, f"CA100 list error: {exc}") from exc


@router.get("/companies/{company_id}")
def get_ca100_company(company_id: str, db: Session = Depends(get_db)):
    """Get full CA100+ assessment detail for a single company."""
    try:
        r = db.execute(
            text("""
                SELECT id, company_name, isin, hq_location, hq_region,
                       sector_cluster, sector, secondary_sector, scope3_category,
                       indicator_1_score, indicator_2_score, indicator_3_score,
                       indicator_4_score, indicator_5_score, indicator_6_score,
                       indicator_7_score, indicator_8_score, indicator_9_score,
                       indicator_10_score, overall_assessment, assessment_year,
                       raw_record, ingested_at
                FROM dh_ca100_assessments WHERE id = :cid
            """),
            {"cid": company_id},
        ).fetchone()
        if not r:
            raise HTTPException(404, "CA100 company not found")
        return {
            "id": r[0], "company_name": r[1], "isin": r[2],
            "hq_location": r[3], "hq_region": r[4],
            "sector_cluster": r[5], "sector": r[6],
            "secondary_sector": r[7], "scope3_category": r[8],
            "indicators": {
                "indicator_1": {"label": INDICATOR_LABELS["indicator_1_score"], "score": r[9]},
                "indicator_2": {"label": INDICATOR_LABELS["indicator_2_score"], "score": r[10]},
                "indicator_3": {"label": INDICATOR_LABELS["indicator_3_score"], "score": r[11]},
                "indicator_4": {"label": INDICATOR_LABELS["indicator_4_score"], "score": r[12]},
                "indicator_5": {"label": INDICATOR_LABELS["indicator_5_score"], "score": r[13]},
                "indicator_6": {"label": INDICATOR_LABELS["indicator_6_score"], "score": r[14]},
                "indicator_7": {"label": INDICATOR_LABELS["indicator_7_score"], "score": r[15]},
                "indicator_8": {"label": INDICATOR_LABELS["indicator_8_score"], "score": r[16]},
                "indicator_9": {"label": INDICATOR_LABELS["indicator_9_score"], "score": r[17]},
                "indicator_10": {"label": INDICATOR_LABELS["indicator_10_score"], "score": r[18]},
            },
            "overall_assessment": r[19],
            "assessment_year": r[20],
            "raw_record": r[21],
            "ingested_at": str(r[22]) if r[22] else None,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("CA100 detail error: %s", company_id)
        raise HTTPException(500, f"CA100 detail error: {exc}") from exc


@router.get("/sectors")
def ca100_sector_summary(db: Session = Depends(get_db)):
    """Sector-level aggregation of CA100+ assessments."""
    try:
        rows = db.execute(text("""
            SELECT sector_cluster, sector, COUNT(*) as cnt,
                   overall_assessment
            FROM dh_ca100_assessments
            GROUP BY sector_cluster, sector, overall_assessment
            ORDER BY sector_cluster, sector, overall_assessment
        """)).fetchall()

        # Aggregate into sector_cluster -> { company_count, sectors, assessment_distribution }
        clusters: dict = {}
        for r in rows:
            sc = r[0] or "Unknown"
            sec = r[1] or "General"
            oa = r[3] or "Not Assessed"
            cnt = r[2]

            if sc not in clusters:
                clusters[sc] = {"sector_cluster": sc, "company_count": 0, "sectors": {}, "assessment_distribution": {}}
            clusters[sc]["company_count"] += cnt
            clusters[sc]["sectors"][sec] = clusters[sc]["sectors"].get(sec, 0) + cnt
            clusters[sc]["assessment_distribution"][oa] = clusters[sc]["assessment_distribution"].get(oa, 0) + cnt

        return {
            "total_companies": sum(c["company_count"] for c in clusters.values()),
            "sector_clusters": list(clusters.values()),
        }
    except Exception as exc:
        logger.exception("CA100 sector summary error")
        raise HTTPException(500, f"CA100 sector summary error: {exc}") from exc


@router.get("/filters")
def ca100_filter_options(db: Session = Depends(get_db)):
    """Return distinct filter values for the CA100+ dataset."""
    try:
        sc = db.execute(text("SELECT DISTINCT sector_cluster FROM dh_ca100_assessments WHERE sector_cluster IS NOT NULL ORDER BY 1")).fetchall()
        sec = db.execute(text("SELECT DISTINCT sector FROM dh_ca100_assessments WHERE sector IS NOT NULL ORDER BY 1")).fetchall()
        reg = db.execute(text("SELECT DISTINCT hq_region FROM dh_ca100_assessments WHERE hq_region IS NOT NULL ORDER BY 1")).fetchall()
        oa = db.execute(text("SELECT DISTINCT overall_assessment FROM dh_ca100_assessments WHERE overall_assessment IS NOT NULL ORDER BY 1")).fetchall()
        return {
            "sector_clusters": [r[0] for r in sc],
            "sectors": [r[0] for r in sec],
            "hq_regions": [r[0] for r in reg],
            "overall_assessments": [r[0] for r in oa],
        }
    except Exception as exc:
        logger.exception("CA100 filters error")
        raise HTTPException(500, f"CA100 filters error: {exc}") from exc
