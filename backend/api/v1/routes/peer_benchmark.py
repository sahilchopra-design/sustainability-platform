"""
Peer Benchmark Gap Assessment API
Exposes the PeerBenchmarkEngine as REST endpoints and persists computed
benchmark statistics to the csrd_peer_benchmarks table so real CSRD report
data (from processed uploads) enriches analyst estimates over time.
"""
from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from db.base import get_db
from services.peer_benchmark_engine import peer_benchmark_engine, FRAMEWORK_CATEGORIES

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/peer-benchmark", tags=["Peer Benchmark"])


# ─── Indicator → category mapping (for real CSRD report data enrichment) ───────

# Prefix → framework category key
# NOTE: ESRS indicator codes in csrd_kpi_values use dash-number format (E1-6, S1-7, G1-4)
# NOT underscore format. Prefixes must match the actual DB codes exactly (case-insensitive).
_INDICATOR_PREFIXES: list[tuple[str, str]] = [
    # TCFD
    ("TCFD_GOV",    "tcfd_governance"),
    ("TCFD_STR",    "tcfd_strategy"),
    ("TCFD_RISK",   "tcfd_risk_mgmt"),
    ("TCFD_MET",    "tcfd_metrics"),
    # ISSB (must come before ESRS S1-/S2- to avoid conflict)
    ("ISSB_S1",     "issb_s1"),
    ("ISSB_S2",     "issb_s2"),
    ("S1_GEN",      "issb_s1"),
    ("S2_CLI",      "issb_s2"),
    # ESRS E-standards — dash-number format (E1-4, E1-5, E1-6, E3-4, E5-5, ...)
    ("E1-",         "esrs_e1"),
    ("E2-",         "esrs_env_other"),
    ("E3-",         "esrs_env_other"),
    ("E4-",         "esrs_env_other"),
    ("E5-",         "esrs_env_other"),
    # ESRS S-standards — dash-number format (S1-7, S1-11, S1-16, ...)
    ("S1-",         "esrs_social"),
    ("S2-",         "esrs_social"),
    ("S3-",         "esrs_social"),
    ("S4-",         "esrs_social"),
    # ESRS G-standards — dash-number format (G1-4, ...)
    ("G1-",         "esrs_governance"),
    # ESRS 2 General (cross-cutting strategy / double materiality)
    ("ESRS2.",      "double_materiality"),
    # Double materiality (legacy / manual codes)
    ("SBM",         "double_materiality"),
    ("IRO",         "double_materiality"),
    ("MDR",         "double_materiality"),
    # EU Taxonomy alignment (maps closest to Paris alignment / net-zero)
    ("EUTAXONOMY.", "paris_alignment"),
    # Financed emissions — FI. prefix used by csrd_ingest_service (FI.WACI)
    ("FI.",         "pcaf_financed"),
    ("FIN_",        "pcaf_financed"),
    ("PCAF",        "pcaf_financed"),
    ("CAT15",       "scope3_cat15"),
    ("S3_15",       "scope3_cat15"),
    # Net zero / transition
    ("PA_",         "paris_alignment"),
    ("NZBA",        "paris_alignment"),
    ("ITR",         "paris_alignment"),
    ("TP_",         "transition_plan"),
    ("TRANS",       "transition_plan"),
    # Climate risk
    ("PHY",         "physical_risk"),
    ("SCEN",        "scenario_analysis"),
    ("SA_",         "scenario_analysis"),
    # Nature
    ("TNFD",        "tnfd_nature"),
    ("BIO_",        "tnfd_nature"),
    ("NAT_",        "tnfd_nature"),
]

# Expected number of disclosure points per category (denominator for coverage %)
_EXPECTED_DPS: dict[str, int] = {
    "tcfd_governance":    8,
    "tcfd_strategy":      10,
    "tcfd_risk_mgmt":     8,
    "tcfd_metrics":       12,
    "issb_s1":            15,
    "issb_s2":            20,
    "esrs_e1":            40,
    "esrs_env_other":     60,
    "esrs_social":        80,
    "esrs_governance":    20,
    "double_materiality": 15,
    "pcaf_financed":      25,
    "scope3_cat15":       10,
    "paris_alignment":    20,
    "transition_plan":    15,
    "physical_risk":      12,
    "scenario_analysis":  10,
    "tnfd_nature":        15,
}

# Slug → name fragments for fuzzy entity matching
_SLUG_NAME_FRAGMENTS: dict[str, list[str]] = {
    # Original 12 + Brookfield
    "ing":                   ["ing group", "ing bank", "ing groep"],
    "bnp_paribas":           ["bnp paribas"],
    "rabobank":              ["rabobank"],
    "abn_amro":              ["abn amro", "abn-amro"],
    "jpmorgan":              ["jpmorgan", "jp morgan", "j.p. morgan"],
    "goldman_sachs":         ["goldman sachs", "goldman"],
    "barclays":              ["barclays"],
    "soc_gen":               ["société générale", "societe generale", "soc gen"],
    "rbc":                   ["royal bank of canada", "rbc"],
    "icici":                 ["icici bank", "icici"],
    "smbc":                  ["sumitomo mitsui", "smbc"],
    "kb_financial":          ["kb financial", "kb국민", "kookmin"],
    "hsbc_hk":               ["hsbc", "hongkong and shanghai"],
    "cathay":                ["cathay financial", "cathay life"],
    "brookfield_renewable":  ["brookfield renewable", "brookfield"],
    # European Energy (CSRD processed reports)
    "orsted":                ["ørsted", "orsted", "dong energy"],
    "rwe":                   ["rwe ag", "rwe group"],
    "engie":                 ["engie", "engie sa", "gdf suez"],
    "edp":                   ["edp", "energias de portugal", "edp renovaveis"],
    # GCC
    "emirates_nbd":          ["emirates nbd", "emiratesnbd"],
    "al_rajhi_bank":         ["al rajhi", "alrajhi"],
    "adnoc":                 ["adnoc", "abu dhabi national oil"],
    "saudi_aramco":          ["saudi aramco", "aramco"],
    # LATAM
    "petrobras":             ["petrobras", "petroleo brasileiro"],
    "itau_unibanco":         ["itaú", "itau unibanco", "itau"],
    "vale":                  ["vale", "vale s.a.", "cvrd"],
    "ecopetrol":             ["ecopetrol"],
    "bancolombia":           ["bancolombia"],
    # India (BRSR)
    "reliance_industries":   ["reliance industries", "ril"],
    "tata_consultancy":      ["tata consultancy", "tcs"],
    "hdfc_bank":             ["hdfc bank", "hdfc"],
    "infosys":               ["infosys"],
    "larsen_toubro":         ["larsen & toubro", "larsen and toubro", "l&t"],
    # Asset Managers
    "blackrock":             ["blackrock"],
    "vanguard":              ["vanguard"],
    "pimco":                 ["pimco", "pacific investment management"],
    "schroders":             ["schroders", "schroder"],
    "amundi":                ["amundi"],
    # Private Equity
    "tpg_rise":              ["tpg rise", "tpg inc", "tpg"],
    "kkr":                   ["kkr", "kohlberg kravis"],
    "carlyle":               ["carlyle group", "carlyle"],
    "blackstone":            ["blackstone"],
    "partners_group":        ["partners group"],
    # Insurance
    "allianz":               ["allianz"],
    "munich_re":             ["munich re", "munichre"],
    "zurich_insurance":      ["zurich insurance", "zurich"],
    "swiss_re":              ["swiss re", "swissre"],
    "axa":                   ["axa"],
    # Climate VC
    "breakthrough_energy":   ["breakthrough energy ventures", "breakthrough energy"],
    "congruent_ventures":    ["congruent ventures"],
    "lowercarbon":           ["lowercarbon capital", "lowercarbon"],
    # Technology
    "microsoft":             ["microsoft"],
    "apple":                 ["apple inc", "apple"],
    "alphabet":              ["alphabet", "google", "googlellc"],
    "amazon":                ["amazon", "amazon.com", "aws"],
    "meta":                  ["meta platforms", "facebook", "meta"],
    "nvidia":                ["nvidia"],
    "samsung":               ["samsung electronics", "samsung"],
    "tsmc":                  ["tsmc", "taiwan semiconductor"],
    "sap":                   ["sap se", "sap"],
    "salesforce":            ["salesforce"],
}

# Processed CSRD reports with entity_registry entries — 8 entities
PROCESSED_REPORT_INSTITUTIONS = {
    "rabobank", "bnp_paribas", "abn_amro", "ing",
    "orsted", "rwe", "engie", "edp",
}


def _code_to_category(indicator_code: str) -> str | None:
    """Map an ESRS/TCFD indicator code to a framework category key via prefix match."""
    upper = indicator_code.upper()
    for prefix, cat in _INDICATOR_PREFIXES:
        if upper.startswith(prefix.upper()):
            return cat
    return None


def _query_real_coverage(slug: str, reporting_year: int, db: Session) -> dict[str, float] | None:
    """
    For an institution slug, find its csrd_entity_registry entry(s), then compute
    per-category coverage % from csrd_kpi_values.
    Returns dict[category_key → coverage_0_100] or None if no entity found.
    """
    fragments = _SLUG_NAME_FRAGMENTS.get(slug, [])
    if not fragments:
        return None

    # Build ILIKE clause for each name fragment
    conditions = " OR ".join([
        f"LOWER(legal_name) LIKE :frag{i}"
        for i in range(len(fragments))
    ])
    params: dict = {f"frag{i}": f"%{f}%" for i, f in enumerate(fragments)}
    params["year"] = reporting_year

    entity_sql = f"""
        SELECT id FROM csrd_entity_registry
        WHERE {conditions}
        LIMIT 5
    """
    entity_rows = db.execute(text(entity_sql), params).fetchall()
    if not entity_rows:
        return None

    entity_ids = [str(r[0]) for r in entity_rows]

    # Fetch all kpi values for these entities × reporting year
    ids_placeholder = ", ".join([f":eid{i}" for i in range(len(entity_ids))])
    kpi_sql = f"""
        SELECT indicator_code
        FROM csrd_kpi_values
        WHERE entity_registry_id IN ({ids_placeholder})
          AND reporting_year = :year
    """
    kpi_params: dict = {f"eid{i}": eid for i, eid in enumerate(entity_ids)}
    kpi_params["year"] = reporting_year

    kpi_rows = db.execute(text(kpi_sql), kpi_params).fetchall()
    if not kpi_rows:
        return None

    # Count disclosures per category
    counts: dict[str, int] = {k: 0 for k in FRAMEWORK_CATEGORIES}
    for (code,) in kpi_rows:
        cat = _code_to_category(code)
        if cat and cat in counts:
            counts[cat] += 1

    # Convert to 0-100 coverage score
    coverage: dict[str, float] = {}
    for cat, count in counts.items():
        expected = _EXPECTED_DPS.get(cat, 10)
        coverage[cat] = min(round(count / expected * 100, 1), 100.0)

    return coverage if any(v > 0 for v in coverage.values()) else None


def _upsert_benchmark(
    slug: str, category: str, coverage_pct: float,
    reporting_year: int, db: Session,
) -> None:
    """
    Upsert one row into csrd_peer_benchmarks for slug × category × year.
    Uses the 'sector' column to store the institution slug (repurposing the field
    since this table is designed for sector-level aggregates; we use region='institution').
    """
    sql = """
        INSERT INTO csrd_peer_benchmarks (
            id, indicator_code, reporting_year, sector, region,
            entity_count, mean_value, median_value, unit,
            benchmark_methodology, computed_at
        ) VALUES (
            gen_random_uuid(), :indicator_code, :reporting_year, :sector, :region,
            1, :mean_value, :mean_value, 'coverage_pct',
            'peer_benchmark_gap_assessment_v1', NOW()
        )
        ON CONFLICT (indicator_code, reporting_year, sector, region)
        DO UPDATE SET
            mean_value   = EXCLUDED.mean_value,
            median_value = EXCLUDED.median_value,
            computed_at  = NOW()
    """
    db.execute(text(sql), {
        "indicator_code":  category,
        "reporting_year":  reporting_year,
        "sector":          slug,
        "region":          "institution",
        "mean_value":      coverage_pct,
    })


# ─── Institutions ─────────────────────────────────────────────────────────────

@router.get("/institutions", summary="List all peer institutions")
def list_institutions(
    region: Optional[str] = Query(None),
    institution_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Return all 12 institutions with metadata and weighted_avg scores.
    Optionally filter by region or institution_type.
    For institutions that have processed CSRD reports in the DB, returns
    real_coverage_pct from csrd_kpi_values alongside the analyst score.
    """
    institutions = peer_benchmark_engine.get_all_institutions()
    if region and region != "All":
        institutions = [i for i in institutions if i.get("region", "").lower() == region.lower()]
    if institution_type and institution_type != "All":
        institutions = [i for i in institutions if i.get("institution_type", "").lower() == institution_type.lower()]

    # Enrich with DB presence flag
    try:
        for inst in institutions:
            slug = inst["slug"]
            has_db = slug in PROCESSED_REPORT_INSTITUTIONS
            inst["has_real_data"] = has_db
            if has_db:
                coverage = _query_real_coverage(slug, 2024, db)
                if coverage:
                    inst["real_coverage"] = coverage
    except Exception as exc:
        log.warning("DB enrichment failed: %s", exc)

    return {"institutions": institutions, "count": len(institutions)}


@router.get("/institution/{slug}", summary="Get single institution profile")
def get_institution(slug: str, db: Session = Depends(get_db)):
    """Return full InstitutionProfile for a given slug, enriched with real DB data."""
    inst = peer_benchmark_engine.get_institution(slug)
    if not inst:
        raise HTTPException(status_code=404, detail=f"Institution '{slug}' not found")

    inst["has_real_data"] = slug in PROCESSED_REPORT_INSTITUTIONS
    try:
        coverage = _query_real_coverage(slug, 2024, db)
        if coverage:
            inst["real_coverage"] = coverage
    except Exception as exc:
        log.warning("DB enrichment failed for %s: %s", slug, exc)

    return inst


@router.get("/institution/{slug}/top-gaps", summary="Top framework gaps for one institution")
def get_top_gaps(slug: str, top_n: int = Query(5, ge=1, le=18)):
    """Return the N lowest-scoring framework categories for this institution."""
    inst = peer_benchmark_engine.get_institution(slug)
    if not inst:
        raise HTTPException(status_code=404, detail=f"Institution '{slug}' not found")
    return {"slug": slug, "gaps": peer_benchmark_engine.get_top_gaps(slug, top_n)}


# ─── Comparison & Heatmap ──────────────────────────────────────────────────────

@router.get("/heatmap", summary="Score heatmap (institution × framework)")
def get_heatmap(
    slugs: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Return the N×18 score matrix for heatmap rendering.
    Institutions with real CSRD report data in the DB are flagged.
    """
    slug_list = [s.strip() for s in slugs.split(",")] if slugs else None
    result = peer_benchmark_engine.get_heatmap(slug_list)

    # Mark which rows have real data
    try:
        for row in result.get("rows", []):
            slug = row.get("slug", "")
            row["has_real_data"] = slug in PROCESSED_REPORT_INSTITUTIONS
    except Exception:
        pass

    return result


@router.get("/comparison", summary="Side-by-side comparison table")
def get_comparison(
    slugs: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    institution_type: Optional[str] = Query(None),
):
    """Return a flat comparison table suitable for a sortable grid."""
    slug_list = [s.strip() for s in slugs.split(",")] if slugs else None
    return {
        "comparison": peer_benchmark_engine.get_comparison_table(
            slugs=slug_list, region=region, institution_type=institution_type
        )
    }


# ─── Aggregates ───────────────────────────────────────────────────────────────

@router.get("/regional-averages", summary="Average scores by region")
def get_regional_averages():
    return {"regional_averages": peer_benchmark_engine.get_regional_averages()}


@router.get("/framework-coverage", summary="Framework coverage distribution")
def get_framework_coverage():
    return {"framework_coverage": peer_benchmark_engine.get_framework_coverage()}


@router.get("/categories", summary="Framework category definitions")
def get_categories():
    return {
        "categories": [{"key": k, **v} for k, v in FRAMEWORK_CATEGORIES.items()]
    }


@router.get("/processed-reports", summary="List CSRD reports used as data sources")
def get_processed_reports(db: Session = Depends(get_db)):
    """
    Return the 8 processed CSRD reports from csrd_report_uploads +
    their matched entity_registry entries. These are the real data sources
    enriching the peer benchmark.
    """
    try:
        sql = """
            SELECT
                ru.id,
                COALESCE(ru.entity_name_override, er.legal_name, ru.filename) AS entity_name,
                COALESCE(ru.reporting_year_override, 2024)                   AS reporting_year,
                ru.status,
                ru.kpis_extracted,
                ru.gaps_found,
                ru.created_at,
                er.legal_name                                                 AS registry_name,
                COALESCE(er.primary_sector, ru.primary_sector)               AS sector,
                COALESCE(er.country_iso, ru.country_iso)                     AS country_iso,
                ru.filename,
                COALESCE(er.is_in_scope_csrd,  true)  AS is_csrd,
                COALESCE(er.is_in_scope_sfdr,  false) AS is_sfdr,
                COALESCE(er.is_in_scope_issb,  false) AS is_issb,
                COALESCE(er.is_in_scope_tcfd,  false) AS is_tcfd,
                er.gics_sector,
                er.sector_subtype
            FROM csrd_report_uploads ru
            LEFT JOIN csrd_entity_registry er ON er.id::text = ru.entity_registry_id
            WHERE ru.status = 'completed'
            ORDER BY entity_name
        """
        rows = db.execute(text(sql)).fetchall()

        _SECTOR_LABEL = {
            "financial_institution": "Banks & Financial Institutions",
            "insurance":             "Insurance",
            "asset_manager":         "Asset Management",
            "energy_developer":      "Energy & Utilities",
            "real_estate":           "Real Estate",
            "technology":            "Technology",
        }

        def _infer_report_type(filename: str, sector: str) -> str:
            if not filename:
                return "Sustainability Report"
            fn = filename.lower()
            if "tcfd" in fn:           return "TCFD Report"
            if "integrated" in fn:     return "Integrated Report"
            if "annual" in fn:         return "Annual Report"
            if "sustainability" in fn or "esg" in fn or "non-financial" in fn:
                return "Sustainability Report"
            # Bank/FI annual reports are typically integrated
            if sector in ("financial_institution", "insurance"):
                return "Annual Report"
            return "Sustainability Report"

        return {
            "reports": [
                {
                    "id":             str(r[0]),
                    "entity_name":    r[1],
                    "reporting_year": r[2],
                    "status":         r[3],
                    "kpis_extracted": r[4] or 0,
                    "gaps_found":     r[5] or 0,
                    "processed_at":   r[6].isoformat() if r[6] else None,
                    "registry_name":  r[7],
                    "sector":         _SECTOR_LABEL.get(r[8] or "", r[8] or "Other"),
                    "sector_raw":     r[8] or "",
                    "country":        r[9],
                    "filename":       r[10],
                    # Regulation scope flags
                    "regulations": [
                        fw for fw, flag in [
                            ("CSRD",  bool(r[11])),
                            ("SFDR",  bool(r[12])),
                            ("ISSB",  bool(r[13])),
                            ("TCFD",  bool(r[14])),
                        ] if flag
                    ],
                    "gics_sector":    r[15],
                    "sector_subtype": r[16],
                    "report_type":    _infer_report_type(r[10] or "", r[8] or ""),
                }
                for r in rows
            ],
            "total": len(rows),
        }
    except Exception as exc:
        log.warning("Could not fetch processed reports: %s", exc)
        return {"reports": [], "total": 0, "error": str(exc)}


# ─── DB Persistence (compute & save) ──────────────────────────────────────────

@router.post("/compute", summary="Run benchmark computation and save results to DB")
def compute_benchmarks(
    reporting_year: int = Query(2024, ge=2020, le=2030),
    db: Session = Depends(get_db),
):
    """
    1. For each of the 12 peer institutions, attempt to match entity in
       csrd_entity_registry.
    2. For matched entities (those with processed CSRD reports), query
       csrd_kpi_values to compute real per-category coverage %.
    3. Save/upsert each coverage score to csrd_peer_benchmarks.
    4. Return enriched institution list showing which data points are
       real (from reports) vs. analyst estimates.
    """
    institutions = peer_benchmark_engine.get_all_institutions()
    enriched: list[dict] = []
    saved_count = 0

    for inst in institutions:
        slug = inst["slug"]
        has_real = False
        real_coverage: dict[str, float] = {}

        try:
            coverage = _query_real_coverage(slug, reporting_year, db)
            if coverage:
                has_real = True
                real_coverage = coverage
                # Persist each category to csrd_peer_benchmarks
                for cat, pct in coverage.items():
                    try:
                        _upsert_benchmark(slug, cat, pct, reporting_year, db)
                        saved_count += 1
                    except Exception as exc:
                        log.warning("Upsert failed for %s/%s: %s", slug, cat, exc)

        except Exception as exc:
            log.warning("Coverage query failed for %s: %s", slug, exc)

        enriched.append({
            **inst,
            "has_real_data": has_real,
            "real_coverage": real_coverage,
            "data_completeness_pct": round(
                len([v for v in real_coverage.values() if v > 0]) / 18 * 100, 1
            ) if real_coverage else 0.0,
        })

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        log.error("DB commit failed: %s", exc)

    return {
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "reporting_year": reporting_year,
        "institutions_processed": len(institutions),
        "db_records_saved": saved_count,
        "institutions": enriched,
    }


@router.get("/saved-benchmarks", summary="Retrieve previously saved benchmark stats from DB")
def get_saved_benchmarks(
    reporting_year: int = Query(2024),
    db: Session = Depends(get_db),
):
    """
    Return csrd_peer_benchmarks rows for region='institution' (our peer benchmark store).
    Returns a nested dict: slug → category → coverage_pct.
    """
    try:
        sql = """
            SELECT sector, indicator_code, mean_value, computed_at
            FROM csrd_peer_benchmarks
            WHERE region = 'institution' AND reporting_year = :year
            ORDER BY sector, indicator_code
        """
        rows = db.execute(text(sql), {"year": reporting_year}).fetchall()

        # Nest by slug → category
        result: dict[str, dict] = {}
        for row in rows:
            slug, cat, val, computed_at = row[0], row[1], float(row[2]), row[3]
            if slug not in result:
                result[slug] = {"categories": {}, "last_computed": None}
            result[slug]["categories"][cat] = val
            if computed_at:
                result[slug]["last_computed"] = computed_at.isoformat()

        return {
            "reporting_year": reporting_year,
            "institutions": result,
            "total_records": len(rows),
        }
    except Exception as exc:
        log.warning("Could not fetch saved benchmarks: %s", exc)
        return {"institutions": {}, "total_records": 0, "error": str(exc)}
