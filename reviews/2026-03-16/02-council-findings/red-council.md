# 02 — Red Council: Failure, Risk, and Compliance Lens
**Date:** 2026-03-16

---

## Top 10 Failure Scenarios

### F1. Anonymous API Access on All Calculation Endpoints
| Attribute | Assessment |
|-----------|-----------|
| **Failure** | 139 route files exist. `require_role()` is implemented in `api/dependencies.py` and is used in `audit_log.py` and `organisations.py`. But it is NOT applied to any calculation endpoint (ECL, PCAF, SFDR PAI, EU Taxonomy, Carbon, etc.) |
| **Evidence** | `audit_log.py` uses `Depends(require_role("admin", "compliance"))`. `banking_risk.py`, `ecl_climate.py`, `sfdr_pai.py` have no auth dependency at all |
| **Probability** | Certain in current state |
| **Severity** | Critical — institutional clients cannot deploy a system where any unauthenticated HTTP call can access proprietary portfolio data and regulatory calculations |
| **Recoverability** | Recoverable — requires auth middleware applied globally in `server.py`, not per-route |
| **Persona Impact** | All personas — violates every financial institution's information security policy |

---

### F2. Portfolio Dashboard Showing Zeros to New Users (Silent Failure)
| Attribute | Assessment |
|-----------|-----------|
| **Failure** | `portfolio_analytics_engine_v2.py` falls back to empty/zero values when tables are empty. No user-facing error or guidance. A new Investment Lead logs in and sees a portfolio dashboard full of zeros. |
| **Evidence** | Service docstring: "Falls back to empty / zero values when tables are missing or empty" |
| **Probability** | Certain for new deployments without pre-seeded data |
| **Severity** | High — destroys user trust on first use; a demo that shows zeros is worse than no demo |
| **Recoverability** | Recoverable — add empty-state UI component with data onboarding prompt |
| **Persona Impact** | Investment Lead, Analytics Lead |

---

### F3. XBRL Scope 1 Unit Mismatch Bug
| Attribute | Assessment |
|-----------|-----------|
| **Failure** | In `xbrl_export_engine.py`, the concept `esrs:GrossScope1GHGEmissions` is mapped with `"xbrl_unit": "iso4217:EUR"` — this means Scope 1 emissions tagged in tCO2e would be filed with a monetary unit. This is a hard validation error in ESMA ESEF filing. |
| **Evidence** | `xbrl_export_engine.py` lines 29-37: `"xbrl_unit": "iso4217:EUR"` for `E1-6_scope1_gross` |
| **Probability** | Certain if XBRL export is used for actual filing |
| **Severity** | Critical — a filed XBRL report with wrong unit type will be rejected by ESMA/national authority |
| **Recoverability** | Easy fix — change unit to a custom non-monetary unit or `xbrli:pure` with appropriate decimals attribute |
| **Persona Impact** | Sustainability Regulatory Lead |

---

### F4. CSRD Worker Task Dependency Not Confirmed
| Attribute | Assessment |
|-----------|-----------|
| **Failure** | `csrd_reports.py` imports `from workers.tasks.csrd_tasks import process_csrd_report_task` — but `workers/` directory was not found in the service file listing. If the worker module does not exist, PDF upload endpoint will crash with ImportError on startup |
| **Evidence** | Import statement in `csrd_reports.py` line 34; `workers/` not in the service directory listing |
| **Probability** | High if server.py includes this router and workers/ is absent |
| **Severity** | High — entire CSRD PDF ingestion pipeline broken at import |
| **Recoverability** | Recoverable — create minimal worker stub or make import conditional |
| **Persona Impact** | Sustainability Regulatory Lead |

---

### F5. NGFS Phase II vs Phase V Mismatch
| Attribute | Assessment |
|-----------|-----------|
| **Failure** | Platform uses NGFS Phase II scenarios (referenced in `ngfs_seeder.py`, MEMORY.md). NGFS released Phase V in September 2024 with materially different temperature pathways and carbon price trajectories. All scenario-linked calculations (ECL, sovereign risk, portfolio VaR, transition risk) may be based on outdated science. |
| **Probability** | High — Phase V explicitly exists and supersedes Phase II for financial institution reporting |
| **Severity** | High — EBA, ECB, and TCFD-aligned reporting requires use of current NGFS release |
| **Recoverability** | Recoverable but requires data pipeline work (WORK_PLAN A6) |
| **Persona Impact** | Analytics Lead (calculation accuracy), Sustainability Regulatory Lead (regulatory compliance) |

---

### F6. No Audit Trail Middleware on Write Operations
| Attribute | Assessment |
|-----------|-----------|
| **Failure** | Migration 026 created the `audit_log` table. `audit_log.py` routes provide read access. But WORK_PLAN.md B3 explicitly lists "Wire audit_middleware.py to all write endpoints" as pending. Without audit middleware, no CSRD assurance, BCBS 239, or SOC 2 compliance is achievable. |
| **Evidence** | WORK_PLAN.md Track 3 Task B3; `audit_log.py` has `require_role("admin", "compliance")` for reads but no write event logging confirmed |
| **Probability** | Certain — middleware wiring explicitly deferred |
| **Severity** | High — blocks SOC 2 Type II, CSRD assurance, BCBS 239 compliance |
| **Recoverability** | Recoverable — FastAPI middleware with SQLAlchemy write hooks |
| **Persona Impact** | Sustainability Regulatory Lead, Analytics Lead (model governance) |

---

### F7. Data Intake Completeness % Is Mocked
| Attribute | Assessment |
|-----------|-----------|
| **Failure** | `DataIntakeDashboard` shows completion percentages. WORK_PLAN.md F3 lists "Wire completion % to real DB counts" as pending. Users believe their data is 75% complete when the number is fabricated. |
| **Probability** | Certain |
| **Severity** | Medium-High — creates false confidence in data quality before running calculations |
| **Recoverability** | Easy — wire to DB COUNT queries |
| **Persona Impact** | Analytics Lead, Sustainability Regulatory Lead |

---

### F8. SEC Climate Disclosure Rule Stayed in Court
| Attribute | Assessment |
|-----------|-----------|
| **Failure** | `sec_climate_engine.py` implements SEC Release 33-11275 (March 2024). In March 2025, the SEC voluntarily stayed the rule pending judicial review. The SEC also rescinded the rule in February 2025 under the new administration. Using this engine to advise US-listed clients on mandatory compliance would be providing incorrect regulatory guidance. |
| **Probability** | Certain — the underlying rule's status has changed materially |
| **Severity** | High — legal and reputational risk if customers rely on this for US SEC compliance |
| **Recoverability** | Moderate — requires regulatory monitoring and status update in engine + UI |
| **Persona Impact** | Sustainability Regulatory Lead |

---

### F9. PostGIS Missing — Nature Risk Spatial Queries Broken
| Attribute | Assessment |
|-----------|-----------|
| **Failure** | Nature risk and TNFD calculations use lat/lng floats for all spatial operations. Migration 017 attempts to `CREATE EXTENSION postgis` but WORK_PLAN.md notes "PostGIS toggle needed in Supabase dashboard". Without PostGIS, all polygon-based biodiversity overlap calculations, WPA buffer queries, and spatial hazard assessments silently degrade to approximate distance calculations. |
| **Evidence** | MEMORY.md: "no PostGIS yet" for nature risk; `spatial_hazard_service.py` exists; `wdpa_gfw_gem_tables` (migration 030) exist |
| **Probability** | High — if PostGIS toggle was never enabled |
| **Severity** | High — TNFD LEAP Locate phase and biodiversity overlap assessments are materially inaccurate without polygon queries |
| **Recoverability** | Recoverable — single Supabase configuration change, then migration 017 runs |
| **Persona Impact** | Analytics Lead, Sustainability Regulatory Lead (TNFD, CSRD E4) |

---

### F10. No Multi-Tenancy Isolation Despite Org Schema
| Attribute | Assessment |
|-----------|-----------|
| **Failure** | `organisations` table and `portfolios_pg.org_id` FK exist (migration 025). But because RBAC middleware is not enforced (F1), Organisation A's portfolios are visible to Organisation B's users. The multi-tenant data model is built but the access control enforcement is absent. |
| **Evidence** | `portfolio_analytics.py` calls `list_portfolios()` with no org_id filter; no `current_user` dependency |
| **Probability** | Certain |
| **Severity** | Critical — catastrophic for any multi-institution SaaS deployment |
| **Recoverability** | Recoverable — requires WORK_PLAN B2 to complete |
| **Persona Impact** | All personas |

---

## Compliance Vulnerabilities by Regulatory Framework

### CSRD / ESRS
| Vulnerability | Root Cause | Risk Level |
|--------------|-----------|-----------|
| ESRS S2, S3, S4 (social topics: value chain workers, affected communities, consumers) absent from CSRD auto-populate ESRS_MAPPINGS | Source modules for social data points don't exist | High |
| No assurance-ready trail from KPI to source data | Audit middleware not wired | High |
| XBRL unit bug on scope 1 | Code defect in `xbrl_export_engine.py` | Critical |
| PDF extraction worker not confirmed | Worker import unverifiable | High |
| Double materiality lacks stakeholder engagement evidence | No IRO-1/IRO-2 structured capture | Medium |

### SFDR
| Vulnerability | Root Cause | Risk Level |
|--------------|-----------|-----------|
| Annex III/IV/V periodic disclosure format output not confirmed | `sfdr_report_generator.py` output format unclear | High |
| PAI inputs are manually provided — no automatic enrichment | No live entity data ingestion | High |
| DNSH check linkage between SFDR and EU Taxonomy not automated | Manual cross-reference required | Medium |

### ISSB (IFRS S1/S2)
| Vulnerability | Root Cause | Risk Level |
|--------------|-----------|-----------|
| NGFS Phase V not loaded | Scenario data is NGFS Phase II | High |
| Climate scenario analysis requires documented process | No process workflow documented | Medium |
| ISSB transition plan requirements (S2.14-22) not confirmed in `sec_climate_engine.py` | US-focused engine may miss ISSB | Medium |

### EU Taxonomy
| Vulnerability | Root Cause | Risk Level |
|--------------|-----------|-----------|
| Art 18 minimum safeguards only in reference data — not verified against entity records | No integration with UNGP/OECD compliance evidence | High |
| No fund-level taxonomy KPI aggregation confirmed | Portfolio-level GAR uses seeded data | Critical (for fund managers) |
| Delegated Act November 2023 extension (2023/2486) coverage unclear | Engine references original 2021/2139 | Medium |

### CBAM
| Vulnerability | Root Cause | Risk Level |
|--------------|-----------|-----------|
| Default values per Art 4 fallback missing | Not confirmed in `cbam_calculator.py` | Medium |
| No live CBAM registry for certificate pricing | Static EU ETS price path | Medium |

### EUDR
| Vulnerability | Root Cause | Risk Level |
|--------------|-----------|-----------|
| No live GFW deforestation alert integration | Static polygon validation only | High |
| Delayed applicability (EUDR postponed to Dec 2025) not reflected in UI | Engine assumes original timeline | Low |

---

## UX Failure Modes by Persona

### Analytics Lead
- **Silent calculation failure:** Engine falls back to zeros/estimates without a clear error message. Analyst runs ECL calculation, sees result, assumes it's based on real loan data when it's parameter-based estimates.
- **No model audit trail:** Analyst cannot reproduce a calculation result from 3 months ago if calculation inputs are not persisted.
- **No version control:** Two analysts running the same calculation with different assumptions produce different numbers — no way to reconcile.

### Investment Lead
- **First-use emptiness:** Dashboard shows zeros. Investment Lead has no path to populate data without technical knowledge of the API.
- **No actionable outputs:** All calculations end at a JSON or chart. No "add to portfolio model", no "generate memo", no "export to Excel with linked formulas".
- **Scenario confusion:** 5 NGFS scenarios with technical names (net_zero_2050, delayed_transition) with no plain-English impact summaries (e.g., "In this scenario, your portfolio loses €X in value by 2035").

### Sustainability Regulatory Lead
- **No filing readiness dashboard:** No consolidated view of "what needs to be filed, by when, in what format, and what's the current completion status".
- **JSON-only outputs:** Cannot submit a JSON file to ESMA, SEC, or any regulator. The last mile (PDF/XBRL/structured template) is entirely absent.
- **Scattered workflows:** SFDR PAI, EU Taxonomy, CSRD, XBRL, double materiality, and EUDR are on separate pages with no guided workflow connecting them.
- **No disclosure completeness indicator:** No per-framework completeness score shown alongside the data entry forms.

---

## Kill Conditions (Factors That Would Block Institutional Adoption)

| Condition | Currently True? | Blocking For |
|-----------|----------------|-------------|
| Auth is not enforced across APIs | Yes | All institutions |
| Multi-tenant data isolation absent | Yes | Any SaaS deployment |
| No audit trail on write operations | Yes | Banks, insurance (regulatory requirement) |
| Output formats not suitable for regulatory submission | Yes | Regulatory Lead primary use case |
| Demo data (seeded) indistinguishable from live data in UI | Yes | All professional demos |
| NGFS scenario data may be outdated | Likely | Any NGFS-aligned reporting |
| XBRL unit bug | Yes | Any XBRL filing customer |
| Workers module potentially absent | Likely | CSRD PDF customers |
