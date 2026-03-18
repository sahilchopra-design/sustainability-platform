# 00 — Session Setup: Default Detection & System State Audit
**Date:** 2026-03-16
**Council:** Red (Risk/Failure) | Blue (Analytical/Scoring) | Green (Upside/Strategic)
**Subject:** A2 Intelligence — Sustainability Analytics Platform

---

## 1. Default Detection Scan

### Emotional Defaults (Likely Distortions)
| Default | Risk | Mitigation Applied |
|---------|------|--------------------|
| **Recency bias** | 54 migration files and 139 routes look like completeness — they are not | Explicitly test each module's execution path, not just its existence |
| **Feature-count admiration** | Large module count creates illusion of coverage | Distinguish "engine exists" from "engine produces institution-grade outputs" |
| **Completion narrative** | MEMORY.md labels things "Completed" — this is a self-report, not an assurance | Independently verify via code evidence |
| **Scope creep comfort** | Breadth of coverage is reassuring but hides depth failures | Focus scoring on depth, not breadth |

### Social/Ego Defaults
| Default | Mitigation |
|---------|-----------|
| **Builder's pride** — 729+ commits suggests emotional investment | Separate appreciation for effort from assessment of institutional-grade fit |
| **Consultant's safety** — "it's a good start" framing | Be willing to assign P0 gaps that block product viability |

### Inertia Defaults
| Default | Mitigation |
|---------|-----------|
| **Existing architecture lock-in** | Challenge FastAPI-only approach for real-time needs |
| **PostgreSQL-only assumption** | Note that TimescaleDB, PostGIS, and vector search are called for but absent |

---

## 2. System State Audit

### What Is Confirmed Real (DB-backed, non-mocked)
Based on code inspection:
- Portfolio Analytics Engine v2 (`portfolio_analytics_engine_v2.py`) — reads from Supabase but falls back gracefully when tables are empty. SECTOR_REFERENCE_DATA uses hardcoded estimates.
- ECL Climate Engine (`ecl_climate_engine.py`) — full IFRS 9 implementation with real regulatory citations (EBA/GL/2022/16, BCBS 2022, Basel III/IV)
- SFDR PAI Engine (`sfdr_pai_engine.py`) — full PAI 1-18 calculation logic
- CSRD Auto-populate (`csrd_auto_populate.py`) — ESRS_MAPPINGS define source module → ESRS data point wiring
- EU Taxonomy Engine (`eu_taxonomy_engine.py`) — NACE activity assessment, DNSH matrix
- Double Materiality Engine (`double_materiality_engine.py`) — EFRAG IG1/IG3 methodology
- XBRL Export Engine (`xbrl_export_engine.py`) — iXBRL tagging with EFRAG taxonomy concepts
- Facilitated Emissions Engine (`facilitated_emissions_engine.py`) — PCAF Parts B & C
- Factor Overlay Engine (`factor_overlay_engine.py`) — 31 factor registries, 12 overlay methods

### What Is Confirmed Seeded/Synthetic
- **DataHubIngestionPage.jsx** — FALLBACK_INGESTERS and FALLBACK_JOBS are hardcoded deterministic arrays (line 35-48). The ingestion backend does NOT run live scrapers.
- **GarEtsPage.jsx** — uses `seededRand()` for all chart data
- **ProjectFinancePage.jsx** — uses `seededRand()` for all KPIs
- Most frontend pages follow the seededRand() pattern — data is deterministic but synthetic

### What Is Structurally Missing (Not Just Incomplete)
1. **Auth/RBAC not enforced** — `require_role()` exists in `audit_log.py` and `organisations.py` but WORK_PLAN.md explicitly lists B2 (RBAC middleware) as pending
2. **No live data ingestion** — WORK_PLAN.md lists 14 ingestion tasks (A1-A17) as unbuilt; frontend shows FALLBACK_ arrays
3. **PostGIS not enabled** — migration 017 exists but WORK_PLAN.md says PostGIS toggle needed; nature risk uses float lat/lng
4. **LGD/EAD/ECL pipeline incomplete** — PD Calculator exists but full ECL pipeline (PD → LGD → EAD → ECL) lacks production wiring
5. **Time-series architecture absent** — migration 018 adds tables but no TimescaleDB, no APScheduler live

---

## 3. Repository Map Summary

| Layer | Count | Notes |
|-------|-------|-------|
| Backend route files | 139 | Covers all major regulatory and analytics domains |
| Backend service files | ~145 | Mix of full engines and thin wrappers |
| DB migrations | 54 | 001–052 + initial schema; chain has 019→021 gap |
| Frontend feature directories | 45 | Most pages exist; many use seeded data |
| Frontend pages (App.js imports) | 89 | All wired to routes in NAV_GROUPS |
| Nav groups | 10 | Pulse, DME, Analytics, ESG Modules, Risk & Sector, Regulatory, Scenarios & Data, Portfolio, Data Intake, Platform |

### Route File Count by Domain
| Domain | Files | Key Modules |
|--------|-------|-------------|
| Regulatory | ~25 | SFDR PAI, EU Taxonomy, CSRD, ISSB, SEC, XBRL, BRSR, EUDR, CSDDD |
| Climate Risk | ~15 | ECL Climate, Physical Risk, Transition Risk, Sovereign, Stress Testing |
| Portfolio/Finance | ~20 | Portfolio Analytics, Banking Risk, Basel Capital, GAR, PE, AM |
| Carbon/Emissions | ~12 | Carbon v1/v2, CBAM, PCAF Unified, Facilitated, Insurance, Shipping |
| Nature/Supply Chain | ~8 | Nature Risk, TNFD, EUDR, Supply Chain Scope 3 |
| Platform/Integration | ~15 | Data Hub, Data Lineage, Audit Log, Entity360, XBRL Ingestion |

---

## 4. Key Assumptions Entering Review

1. **Target users are institutional** — banks, asset managers, PE firms, insurers, energy developers. Not retail.
2. **Regulatory assurance is the primary value proposition** — output quality must withstand external auditor scrutiny.
3. **Data quality (DQS) propagation is critical** — a platform that cannot certify its own data quality cannot serve PCAF/CSRD/SFDR mandates.
4. **Frontend synthetic data is a demo layer, not a product layer** — the review treats it as such unless API calls are confirmed live.
5. **The platform is pre-production** — no customers confirmed in production; review assesses readiness-to-ship, not production failure.
6. **Migration 015 is the confirmed Supabase head** per MEMORY.md — migrations 016-052 may not be applied to production.
