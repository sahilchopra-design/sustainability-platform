# Work Plan — Effort Estimates & Session Batching Strategy

**Date:** 2026-03-06
**Context:** Claude Code sessions have context window limits (~200K tokens). Large file reads/edits consume context fast. Plan optimises for completing work within session limits.

---

## Ground Rules for Session Efficiency

1. **One theme per session** -- don't mix backend engine work with frontend restyling
2. **Cap at ~8-10 file creates or ~5-6 large file edits per session** -- after that, context fills up
3. **Migrations are cheap** -- SQL files are small; batch multiple migrations together
4. **Frontend components are expensive** -- JSX files are 400-1000+ lines each; limit to 3-4 per session
5. **Always commit at end of session** -- never leave 100+ files uncommitted again
6. **Read only what you need** -- don't read entire 2000-line files if editing 20 lines

---

## Remaining Work — Effort Estimates

### Legend
- **S** = Small (< 30 min, < 200 lines new code, 1-3 files touched)
- **M** = Medium (30-90 min, 200-800 lines, 3-8 files)
- **L** = Large (90-180 min, 800-2000 lines, 8-15 files)
- **XL** = Extra Large (multi-session, 2000+ lines, 15+ files)

---

### TRACK 1: Database Migrations (Apply to Supabase)

| Task | Effort | Files | Notes |
|------|--------|-------|-------|
| Apply migrations 017-029 to Supabase | S | 0 (run SQL) | Just `alembic upgrade head` or manual SQL via Supabase MCP. Batch all 13 migrations in one run. May need to fix chain if revision IDs conflict (019 jumps to 021). |

**Risk:** PostGIS extension (017) may need Supabase dashboard toggle. Time-series (018) is straightforward DDL.

---

### TRACK 2: Data Hub Ingestion Pipelines

The Data Hub app scaffold exists (54 files, FastAPI + React). What's missing: **actual ingestion logic** (the `ingestion/` directory from the plan doesn't exist yet).

| # | Task | Effort | New Files | Dependencies |
|---|------|--------|-----------|--------------|
| A1 | Data Hub DB schema (ingestion tables) + Alembic setup | M | 3-4 | None |
| A2 | BaseIngester abstract class + scheduler (APScheduler) | M | 2-3 | A1 |
| A3 | GLEIF LEI bulk ingester | M | 1 + tests | A2 |
| A4 | Sanctions ingester (OFAC SDN + EU FSL + UN SC) | M | 1 + tests | A2 |
| A5 | Climate TRACE ingester | M | 1 | A2 |
| A6 | NGFS Scenarios Portal ingester | M | 1 | A2 |
| A7 | OWID CO2/energy ingester | S | 1 | A2 |
| A8 | SEC EDGAR XBRL ingester | L | 2 | A2 |
| A9 | yfinance/FMP EVIC fetcher | M | 1 | A2 |
| A10 | Violation Tracker scraper | M | 1 | A2 |
| A11 | WDPA + GFW nature spatial | L | 2 | A2, PostGIS |
| A12 | Global Energy Monitor GCPT | M | 1 | A2 |
| A13 | IRENA LCOE + CRREM + Grid EFs | M | 2 | A2 |
| A14 | SBTi Target Registry | S | 1 | A2 |
| A15 | GDELT BigQuery connector | L | 1 | A2 |
| A16 | Data Hub API endpoints (serve ingested data) | L | 8-10 route files | A1 |
| A17 | Wire DataHubClient in main platform to real endpoints | M | 1 (edit existing) | A16 |

**Total Data Hub effort: ~10-12 sessions**

---

### TRACK 3: Platform Backend Fixes

| # | Task | Effort | Files | Dependencies |
|---|------|--------|-------|--------------|
| B1 | Portfolio Analytics v2 -- wire to real DB (replace remaining mocks in v1, promote v2) | L | 3 (engine, routes, deps) | Migrations applied |
| B2 | Auth/RBAC middleware -- enforce org-scoped access from migration 025 | L | 4-5 (middleware, deps, auth_pg, server.py) | Migration 025 applied |
| B3 | Audit trail middleware -- wire audit_middleware.py to all write endpoints | M | 2-3 (middleware, server.py) | Migration 026 applied |
| B4 | PCAF DQS aggregation logic -- weighted avg computation in pcaf_waci_engine | M | 2 | B1 |
| B5 | SAT Coal Phase-Out criteria checker backend | S | 1 new route + service | None |
| B6 | PCAF Listed Equity asset class | M | 1-2 | B1 |
| B7 | Fix migration chain (019 → 021 gap, verify all `down_revision` links) | S | Edit 2-3 migration files | None |

**Total backend effort: ~5-6 sessions**

---

### TRACK 4: Frontend Completion

| # | Task | Effort | Files | Dependencies |
|---|------|--------|-------|--------------|
| F1 | Scenario Builder -- test and wire all 13 components (already built) | M | 3-4 edits (pages, App.js routing) | None |
| F2 | Portfolio Analytics page -- wire to real API (usePortfolioAnalytics hook exists) | M | 2-3 | B1 |
| F3 | Data Intake status dashboard -- wire completion % to real DB counts | M | 2 | Migrations applied |
| F4 | NZBA Glidepath Tracker -- wire to time-series API | M | 2 | B1, Track 2 |
| F5 | CRREM Pathway chart -- wire to Data Hub CRREM endpoint | M | 2 | A13 |
| F6 | Geothermal Panel (P3) | M | 2 new files | None |
| F7 | IRENA Five Pillars Assessment (P3) | M | 2 new files | None |

**Total frontend effort: ~4-5 sessions**

---

### TRACK 5: Testing & QA

| # | Task | Effort | Files | Dependencies |
|---|------|--------|-------|--------------|
| T1 | Backend startup test -- verify `uvicorn server:app` loads without import errors | S | 0 | All backend work |
| T2 | Frontend build test -- `npm run build` passes | S | 0 | All frontend work |
| T3 | API smoke tests -- hit each route group, verify 200/422 responses | M | 1 test file | T1 |
| T4 | Data Hub smoke tests | M | 1 test file | A16 |
| T5 | End-to-end: upload portfolio CSV → run analytics → verify real KPIs | L | Manual + 1 test | B1, F2 |

**Total testing effort: ~3 sessions**

---

## Batching Strategy — 25 Sessions

### Phase 1: Foundation (Sessions 1-6)

| Session | Theme | Tasks | Est. Time | Context Load |
|---------|-------|-------|-----------|--------------|
| **1** | DB migrations + chain fix | Apply 017-029 to Supabase, fix 019→021 gap (B7) | 30 min | Low -- SQL only |
| **2** | Auth + Audit wiring | B2 (RBAC middleware) + B3 (audit middleware) | 90 min | Medium -- 4-5 file edits |
| **3** | Portfolio engine promotion | B1 (wire v2, retire v1 mocks, update routes) | 120 min | High -- 3 large files |
| **4** | Portfolio frontend wiring | F2 (hook + page to real API) + F1 (scenario builder routing check) | 90 min | Medium -- 4-5 JSX files |
| **5** | Backend startup + smoke test | T1 + T2 + quick T3 | 60 min | Low -- run commands, fix imports |
| **6** | Commit + push + checkpoint | Clean up, commit, update MEMORY.md | 15 min | Low |

### Phase 2: Data Hub Core (Sessions 7-14)

| Session | Theme | Tasks | Est. Time | Context Load |
|---------|-------|-------|-----------|--------------|
| **7** | Data Hub DB + base ingester | A1 (schema) + A2 (BaseIngester + scheduler) | 90 min | Medium |
| **8** | Entity resolution ingesters | A3 (GLEIF LEI) + A4 (Sanctions) | 90 min | Medium -- 2 new files |
| **9** | Emissions ingesters | A5 (Climate TRACE) + A7 (OWID) | 60 min | Medium -- 2 new files |
| **10** | Scenario + carbon price ingesters | A6 (NGFS) + A14 (SBTi) | 60 min | Medium -- 2 new files |
| **11** | Financial data ingesters | A8 (SEC EDGAR) + A9 (yfinance) | 120 min | High -- XBRL parsing |
| **12** | Data Hub API endpoints (serve) | A16 (8-10 route files serving ingested data) | 120 min | High -- many files but small each |
| **13** | Wire main platform to Data Hub | A17 (update data_hub_client.py) + B4 (PCAF DQS) | 90 min | Medium |
| **14** | Commit + smoke test Data Hub | T4 + commit | 45 min | Low |

### Phase 3: Remaining Ingesters + Frontend (Sessions 15-21)

| Session | Theme | Tasks | Est. Time | Context Load |
|---------|-------|-------|-----------|--------------|
| **15** | Nature + energy ingesters | A11 (WDPA/GFW) + A12 (GEM) | 90 min | Medium |
| **16** | Reference data ingesters | A13 (IRENA/CRREM/Grid EFs) + A10 (Violations) | 90 min | Medium |
| **17** | GDELT + controversy | A15 (GDELT BigQuery) | 90 min | High -- BigQuery setup |
| **18** | Frontend: glidepath + CRREM wiring | F4 (NZBA tracker) + F5 (CRREM chart) | 90 min | Medium -- 4 JSX edits |
| **19** | Frontend: data intake dashboard | F3 (completion % from real DB) | 60 min | Medium |
| **20** | Frontend: P3 features | F6 (Geothermal) + F7 (IRENA Five Pillars) | 90 min | Medium -- 4 new JSX |
| **21** | Backend: remaining P1/P3 | B5 (SAT checker) + B6 (PCAF listed equity) | 60 min | Low -- 2-3 files |

### Phase 4: QA + Polish (Sessions 22-25)

| Session | Theme | Tasks | Est. Time | Context Load |
|---------|-------|-------|-----------|--------------|
| **22** | E2E test: FI user story | T5 (upload CSV → analytics → verify) | 120 min | Medium |
| **23** | E2E test: Energy expert story | Upload project → DSCR → ETC → lender package | 120 min | Medium |
| **24** | Bug fixes from QA | Fix whatever broke in sessions 22-23 | 90 min | Variable |
| **25** | Final commit, update docs, push | GAP_ANALYSIS update, MEMORY.md, push to GitHub | 30 min | Low |

---

## Anti-Pattern Checklist (Avoid These)

| Anti-Pattern | Why It Fails | Do This Instead |
|---|---|---|
| Reading all 70+ JSX files to "understand the codebase" | Burns 80% of context on reads | Read only the 2-3 files you're editing |
| Editing server.py (1400 lines) + 5 large components in one session | server.py alone eats 15-20% of context | Dedicate a session to server.py changes; separate session for components |
| Creating 20+ new files in one session | Each Write burns context; 20 files = session over | Cap at 8-10 new file creates per session |
| Leaving 100+ files uncommitted across sessions | Lose work if session crashes; can't diff | Commit at end of every session |
| Mixing Data Hub work with main platform edits | Different codebases; context wasted on unrelated reads | Separate sessions per application |
| Running `npm install` or `pip install` mid-session | Long output floods context | Do dependency installs in dedicated short sessions |

---

## Quick Reference: Session Budget

| Action | Context Cost | Budget Per Session |
|--------|-------------|-------------------|
| Read a 500-line file | ~2-3% | 10-15 reads max |
| Read a 1500-line file | ~7-8% | 3-4 reads max |
| Write a new 400-line file | ~3-4% | 8-10 writes max |
| Edit (small diff) | ~1-2% | 20+ edits fine |
| Bash command + output | ~1-2% | Many are fine |
| Large bash output (npm install) | ~5-10% | Avoid or pipe to /dev/null |

**Target: use no more than 70% of context on reads/writes, leaving 30% for reasoning and tool calls.**

---

## Recommended Start: Session 1

Run this first -- it's the lowest risk, highest unblock:

```
1. alembic upgrade head (apply 017-029)
2. Fix migration chain if needed (019 → 021 gap)
3. Verify tables exist in Supabase
4. Commit migration chain fix if any files changed
```

This unblocks Tracks 2, 3, and 4.
