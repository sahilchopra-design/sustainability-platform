# 05 — Gap Prioritization: Portfolio View
**Date:** 2026-03-16

---

## Top 10 Critical Gaps (P0 / P1)

### P0 Gaps — Block Institutional Deployment

| # | Gap | Affected Module(s) | Affected Personas | Blocking Condition |
|---|-----|-------------------|-------------------|-------------------|
| P0-1 | **Auth not enforced on any calculation endpoint** | All 139 routes | All | No FI will deploy an unauthenticated system |
| P0-2 | **Multi-tenant org data isolation absent** | `portfolio_analytics.py`, all CRUD routes | All | Org A sees Org B data in SaaS deployment |
| P0-3 | **Portfolio dashboard shows zeros for new orgs** | `portfolio_analytics_engine_v2.py` | Investment Lead | Demo / first-use failure |
| P0-4 | **All major frontend pages use seeded data** | 80%+ of frontend pages | Investment Lead, Analytics Lead | Cannot distinguish live from demo in a client meeting |
| P0-5 | **GAR/EU ETS compliance figures are entirely seeded** | `GarEtsPage.jsx` | Regulatory Lead (Banking) | Banks cannot file Art 449a Pillar 3 with seeded numbers |

---

### P1 Gaps — Block Regulatory Compliance Use Case

| # | Gap | Affected Module(s) | Affected Personas | Regulatory Framework |
|---|-----|-------------------|-------------------|---------------------|
| P1-1 | **XBRL scope 1 unit bug** | `xbrl_export_engine.py` | Regulatory Lead | ESRS ESEF filing |
| P1-2 | **No audit trail middleware on write operations** | All write endpoints | Regulatory Lead, Analytics Lead | BCBS 239, CSRD assurance |
| P1-3 | **No regulatory submission output format** (JSON only) | `regulatory_report_compiler.py` | Regulatory Lead | All frameworks |
| P1-4 | **ESRS S2/S3/S4 not in CSRD auto-populate** | `csrd_auto_populate.py` | Regulatory Lead | CSRD ESRS S2-S4 |
| P1-5 | **PCAF DQS portfolio aggregation not complete** | `pcaf_waci_engine.py` | Analytics Lead, Regulatory Lead | PCAF v2.0 DQS certification |
| P1-6 | **PCAF Listed Equity asset class absent** | `pcaf_asset_classes.py` | Investment Lead | PCAF Part A listed equity |
| P1-7 | **No live data ingestion (GLEIF, NGFS, SBTi, EDGAR)** | Data Hub | All | DQS tier 1-2 requires traceable external data |
| P1-8 | **PostGIS not enabled — nature risk spatial degraded** | `nature_risk_calculator.py`, `spatial_hazard_service.py` | Analytics Lead | TNFD LEAP Locate phase |
| P1-9 | **CSRD worker task import unconfirmed** | `csrd_reports.py` | Regulatory Lead | CSRD PDF extraction pipeline |
| P1-10 | **SEC climate engine reflects rescinded rule** | `sec_climate_engine.py` | Regulatory Lead (US) | SEC regulatory accuracy |

---

## Top 10 Enhancement Opportunities

| # | Opportunity | Value | Effort | Priority |
|---|-------------|-------|--------|----------|
| E1 | Unified ECL → GAR → Pillar 3 orchestration chain | Differentiator for bank sales | 2 weeks | Q1 |
| E2 | CSRD auto-populate → XBRL export pipeline (fix unit bug + wire) | Core product completion | 1 week | Q1 |
| E3 | Regulatory obligation calendar with deadline alerts | Stickiness driver for Regulatory Lead | 2 weeks | Q1 |
| E4 | WeasyPrint PDF output for regulatory reports | Last-mile deliverable | 1 week | Q1 |
| E5 | EUDR + CSDDD + ESRS E4 unified supply chain workflow | Supply chain market entry | 2 weeks | Q1 |
| E6 | Active stewardship module (Glidepath + PACTA + CA100+ + Engagement) | AM product differentiator | 3 weeks | Q2 |
| E7 | EIOPA climate stress test for insurance sector | Insurance market gap | 3 weeks | Q2 |
| E8 | ETS2 readiness assessment (extend eu_ets_engine.py) | First-mover in emerging market | 1 week | Q1 |
| E9 | SFDR Annex III/IV/V formatted output from sfdr_report_generator.py | SFDR filing completion | 2 weeks | Q2 |
| E10 | Assurance readiness dashboard (per-framework completeness + DQS) | Trust builder for Regulatory Lead | 2 weeks | Q2 |

---

## Quick Wins (Next 4 Weeks)

| Task | File(s) | Effort | Impact |
|------|---------|--------|--------|
| Fix XBRL unit bug for scope 1 | `xbrl_export_engine.py` line ~34 | 30 min | Unblocks XBRL filing |
| Add sample portfolio seed on first org login | `portfolio_analytics_engine_v2.py` + org creation flow | 2 days | Fixes P0-3 empty dashboard |
| Add global auth middleware to server.py | `server.py` + `api/dependencies.py` | 2 days | Fixes P0-1 and P0-2 |
| Wire audit middleware to write endpoints | `audit_log_middleware.py` + `server.py` | 3 days | Fixes P1-2 |
| Mark seeded data with "Demo Data" badge in UI | All seeded JSX pages | 2 days | Fixes P0-4 perception issue |
| Enable PostGIS toggle in Supabase + run migration 017 | Supabase dashboard + alembic | 30 min | Fixes P1-8 spatial |
| Confirm/fix CSRD worker import | `csrd_reports.py` + workers/ directory | 1 day | Fixes P1-9 |
| Update SEC climate engine status banner | `sec_climate_engine.py` + frontend | 30 min | Fixes P1-10 accuracy risk |
| Add PCAF Listed Equity to pcaf_asset_classes.py | `pcaf_asset_classes.py` | 3 days | Closes WORK_PLAN B6 |
| Wire Data Intake completion % to real DB counts | `DataIntakeDashboard.jsx` | 2 days | Closes WORK_PLAN F3 |

**Total quick win effort: ~3-4 weeks for all items above**

---

## Current Quarter Builds (Weeks 5-12)

| Build | Modules | Effort | Deliverable |
|-------|---------|--------|-------------|
| **Tier-1 Data Ingestion** | GLEIF LEI, NGFS Phase V, SBTi, OWID CO2 | 3 weeks | Live DQS improvement for ECL, PCAF, CSRD |
| **PDF Output for Regulatory Reports** | `regulatory_report_compiler.py` + WeasyPrint templates | 2 weeks | Submission-ready SFDR PAI, TCFD, CSRD reports |
| **ESRS S2/S3/S4 Auto-Populate** | `csrd_auto_populate.py` + new social data fields | 2 weeks | Full ESRS topical coverage |
| **PCAF DQS Weighted Aggregation** | `pcaf_waci_engine.py` | 1 week | DQS-certified portfolio financed emissions |
| **Regulatory Obligation Calendar** | New `/regulatory-readiness` page | 2 weeks | Stickiness for Regulatory Lead |
| **ECL → GAR → Pillar 3 Orchestration** | New orchestration route | 2 weeks | Banking differentiator |
| **Assurance Readiness Dashboard** | New page aggregating gap_tracker, DQS, completeness | 2 weeks | Audit readiness score |

---

## What to Defer / Reject

| Item | Reason to Defer |
|------|----------------|
| Full 14-source data ingestion pipeline (WORK_PLAN A1-A17) | 10-12 sessions; do tier-1 only first (GLEIF, NGFS, SBTi, OWID) |
| CRREM pathway wiring (WORK_PLAN F5) | Requires A13 (IRENA/CRREM ingester) — defer until Q2 |
| GDELT BigQuery connector (WORK_PLAN A15) | High complexity, commercial BigQuery cost; defer to Q3 |
| TimescaleDB migration | Infrastructure cost and migration risk; defer unless time-series queries proven needed |
| Third-party regulatory filing integration (Workiva, Rilatia) | Commercial negotiation; consider only after PDF output proven |
| SEC climate detailed compliance module rebuild | SEC rule rescinded; maintain as informational resource only, not compliance tool |
| Full IMP/IRIS+ impact framework mapping | PE market is smaller; complete core finance modules first |

---

## Items to Reject Outright

| Item | Reason |
|------|--------|
| Adding more calculation modules before fixing Auth | Security > features |
| Adding more frontend pages before fixing seeded data labels | Trust > breadth |
| Expanding to new sectors (agriculture, mining) before closing banking/energy depth gaps | Depth > breadth |

---

## Single Strategic Theme for the Roadmap

**"From Calculation Engine to Assurance Platform"**

The platform already has the best calculation engine breadth in the market. The gap is the last mile: getting from a Python dict result to a regulatory-grade assurance deliverable. Every prioritized item in this roadmap — auth, audit trail, PDF output, DQS certification, XBRL unit fix, data ingestion — is in service of one goal: producing outputs that an external auditor, a regulator, or an investment committee can rely on without qualification.

The strategic bet is: **institutions will pay a premium for defensible outputs, not just for more calculations.**

The platform is 70% complete as a calculation engine and 20% complete as an assurance platform. Closing that gap is the single highest-leverage investment.
