# 02 — Blue Council: Analytical & Scoring Lens
**Date:** 2026-03-16

---

## Module Scoring Matrix (1-10)

| Module | Functionality | Data Coverage | Calculation Engine | UX | Output Quality | Integration Quality | **Composite** |
|--------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **ECL Climate Engine** | 9 | 6 | 9 | 5 | 7 | 7 | **7.2** |
| **SFDR PAI Engine** | 9 | 6 | 8 | 6 | 6 | 6 | **6.8** |
| **EU Taxonomy Engine** | 9 | 7 | 8 | 6 | 7 | 7 | **7.3** |
| **CSRD / ESRS Auto-Populate** | 7 | 5 | 7 | 5 | 5 | 6 | **5.8** |
| **Double Materiality Engine** | 8 | 6 | 8 | 6 | 6 | 6 | **6.7** |
| **XBRL Export Engine** | 6 | 7 | 6 | 5 | 3 | 5 | **5.3** |
| **PCAF Unified Engine** | 8 | 5 | 8 | 5 | 6 | 6 | **6.3** |
| **Portfolio Analytics Engine v2** | 7 | 3 | 7 | 6 | 4 | 6 | **5.5** |
| **Carbon Calculator v2** | 9 | 7 | 9 | 6 | 7 | 8 | **7.7** |
| **Sovereign Climate Risk** | 8 | 6 | 8 | 6 | 7 | 7 | **7.0** |
| **Banking Risk Engine** | 9 | 6 | 9 | 6 | 7 | 7 | **7.3** |
| **AM Engine** | 8 | 5 | 8 | 6 | 6 | 6 | **6.5** |
| **Factor Overlay Engine** | 8 | 7 | 7 | 4 | 6 | 7 | **6.5** |
| **EUDR Engine** | 8 | 7 | 7 | 6 | 7 | 6 | **6.8** |
| **CSDDD Engine** | 8 | 6 | 7 | 5 | 7 | 6 | **6.5** |
| **Nature Risk (TNFD LEAP)** | 7 | 4 | 6 | 6 | 5 | 4 | **5.3** |
| **Facilitated Emissions** | 9 | 5 | 9 | 5 | 7 | 7 | **7.0** |
| **Supply Chain Scope 3** | 8 | 6 | 8 | 6 | 7 | 7 | **7.0** |
| **Scenario Analysis Engine** | 8 | 5 | 8 | 7 | 6 | 7 | **6.8** |
| **Data Lineage Service** | 9 | 8 | 8 | 4 | 7 | 8 | **7.3** |
| **Regulatory Report Compiler** | 8 | 8 | 6 | 5 | 3 | 6 | **6.0** |
| **Stress Testing Engine** | 8 | 5 | 8 | 6 | 6 | 6 | **6.5** |
| **DME / Dynamic Materiality** | 7 | 4 | 7 | 6 | 5 | 5 | **5.7** |
| **Auth / RBAC** | 2 | N/A | N/A | 3 | N/A | 1 | **2.0** |
| **Audit Trail** | 3 | N/A | N/A | 2 | N/A | 2 | **2.3** |
| **Data Hub / Ingestion** | 4 | 2 | N/A | 6 | 2 | 3 | **3.4** |

### Scoring Rubric
- **Functionality**: Does the module implement the full scope of its stated regulatory/analytical purpose?
- **Data Coverage**: Is real, current, externally-sourced data available to drive the calculations?
- **Calculation Engine**: Is the mathematical/methodological implementation correct and well-referenced?
- **UX**: Does the frontend surface the outputs accessibly and usably for the target persona?
- **Output Quality**: Are outputs formatted, validated, and suitable for the stated use (audit, filing, investment decision)?
- **Integration Quality**: Is the module well-connected to upstream data and downstream consumers?

---

## Top Critical Gaps with Solution Alternatives

### Gap 1: No Auth Enforcement Across APIs (Current Score: 2.0)

**Problem Statement:** 139 API routes lack authentication and authorization enforcement. `require_role()` exists in `api/dependencies.py` but is only applied to 2 routes.

| Alternative | Description | Effort | Recommended? |
|-------------|-------------|--------|:---:|
| A. Global FastAPI middleware | Add `AuthMiddleware` in `server.py` that validates session_token on all non-public routes | 2 days | Yes |
| B. Per-route dependency injection | Add `Depends(get_current_user)` to every router | 3-4 weeks, error-prone | No |
| C. API Gateway (Kong/nginx auth) | Offload auth to infrastructure layer | 2 weeks + infrastructure setup | Consider for scale |

**Recommended:** Option A — FastAPI middleware in `server.py` is the lowest-effort, highest-impact fix. Whitelist `/api/auth/`, `/api/v1/ref/` (public reference data), and `/health`.

---

### Gap 2: Portfolio Dashboard Empty State / Live Data (Current Score: 5.5)

**Problem Statement:** Portfolio Analytics Engine v2 falls back to zeros. Users see a blank dashboard. The SECTOR_REFERENCE_DATA in `portfolio_analytics_engine_v2.py` is hardcoded from PCAF v2.0 Annex and IPCC AR6 estimates, not live market data.

| Alternative | Description | Effort | Recommended? |
|-------------|-------------|--------|:---:|
| A. Sample portfolio seed on first login | Auto-create a 10-holding sample portfolio for new orgs | 2 days | Yes (short term) |
| B. Wire yfinance EVIC feed (WORK_PLAN A9) | Live market cap data for PCAF DQS improvement | 1-2 weeks | Yes (medium term) |
| C. CSV import with guided mapping | Let users upload their portfolio CSV with column mapping wizard | 1 week | Yes (parallel) |

**Recommended:** Option A immediately (seed on first login), Option C within 4 weeks, Option B in Q2.

---

### Gap 3: XBRL Unit Mapping Bug

**Problem Statement:** `xbrl_export_engine.py` maps `E1-6_scope1_gross` (Scope 1 GHG emissions in tCO2e) to `"xbrl_unit": "iso4217:EUR"`. This is a unit type mismatch that will cause ESMA filing validation failure.

| Alternative | Description | Effort | Recommended? |
|-------------|-------------|--------|:---:|
| A. Fix unit to `xbrli:pure` with `decimals="-6"` | Standard XBRL approach for non-monetary environmental metrics | 30 minutes | Yes |
| B. Create custom ESRS unit registry | Define `esrs:tCO2e` as a custom unit in the taxonomy extension | 1 day | Not needed — pure + decimals is EFRAG standard |
| C. Add unit validation test | Add automated test comparing unit to ESRS taxonomy expected type | 2 hours | Yes (alongside A) |

**Recommended:** Option A + C. A single-line fix plus a unit validation test covering all 30+ taxonomy concepts.

---

### Gap 4: Output Format Gap (JSON → Regulatory Submission)

**Problem Statement:** All 10 regulatory frameworks in `regulatory_report_compiler.py` produce structured Python dicts/JSON. No framework produces a submission-ready output: no PDF, no XBRL, no ESMA-compliant HTML, no Word document.

| Alternative | Description | Effort | Recommended? |
|-------------|-------------|--------|:---:|
| A. WeasyPrint PDF renderer + Jinja2 templates | Python-native HTML→PDF; add CSRD, SFDR, TCFD templates | 2-3 weeks | Yes |
| B. XBRL linking (already have engine) | Wire `xbrl_export_engine.py` output to `regulatory_report_compiler.py` | 1 week | Yes |
| C. Third-party disclosure platform integration (Workiva, Rilatia) | API handshake to push structured data to filing platform | 4-6 weeks + commercial agreement | Consider for later |

**Recommended:** Option A + B in parallel. WeasyPrint PDF for SFDR/TCFD/BRSR; XBRL linkage for CSRD/ISSB. Option C is a strategic partnership to consider in Q3.

---

### Gap 5: Data Ingestion Pipeline Not Built

**Problem Statement:** WORK_PLAN.md lists 14-17 ingestion tasks. All are pending. `DataHubIngestionPage.jsx` shows FALLBACK_INGESTERS hardcoded arrays. Without live data, DQS tiers are artificially inflated.

| Alternative | Description | Effort | Recommended? |
|-------------|-------------|--------|:---:|
| A. Build tier-1 ingesters only (GLEIF, NGFS, SBTi, OWID) | 4 critical data sources, ~2 weeks | P0 tier | Yes |
| B. Build all 14 ingesters as planned | Full WORK_PLAN A1-A17 | ~10-12 sessions (~3 months) | Long-term roadmap |
| C. Use third-party data vendor (Refinitiv/Bloomberg BSIP, S&P Trucost) | Commercial data license covers EVIC, emissions, sovereign | 4-6 weeks + cost | Consider for DQS improvement |

**Recommended:** Option A immediately (highest DQS impact, lowest effort), Option C in parallel evaluation.

---

### Gap 6: No Compliance Assurance / Audit Readiness Dashboard

**Problem Statement:** Sustainability Regulatory Lead has no single view that tells them: "Your CSRD E1 disclosure is 73% complete, your SFDR PAI data is DQS 3.2, your EU Taxonomy alignment evidence has 3 missing DNSH documents."

| Alternative | Description | Effort | Recommended? |
|-------------|-------------|--------|:---:|
| A. Regulatory readiness dashboard (new page) | Aggregate completeness % per framework from existing DB tables | 2 weeks | Yes |
| B. Per-module completeness badges | Add completeness % badge to each existing module page | 1 week | Yes (parallel) |
| C. Weekly digest email | Backend job computing readiness scores + email | 1 week | Nice-to-have |

**Recommended:** Option A as a new `/regulatory-readiness` route consuming existing `csrd_gap_tracker`, `dma_assessments`, `sfdr_pai_assessments` tables.

---

### Gap 7: ESRS S2/S3/S4 Social Topics Missing from Auto-Populate

**Problem Statement:** `csrd_auto_populate.py` ESRS_MAPPINGS only cover E1-E5 topics. ESRS S1 (own workforce) has partial coverage. S2 (workers in value chain), S3 (affected communities), S4 (consumers and end-users) have no source module mappings.

| Alternative | Description | Effort | Recommended? |
|-------------|-------------|--------|:---:|
| A. Extend ESRS_MAPPINGS for S2/S3/S4 | Add mappings to supply_chain_scope3_engine (for S2) and entity profiles (for S3/S4) | 1 week | Yes |
| B. Create dedicated HR/Social data engine | New `social_risk_engine.py` covering workforce KPIs, living wage, S2-S4 | 3-4 weeks | Yes (medium term) |
| C. Leave S2-S4 as manual entry only | Document limitation | None | No — blocks CSRD completeness |

**Recommended:** Option A short-term (manual entry with structured fields), Option B in current quarter.

---

### Gap 8: Insurance / Solvency II Climate Risk Missing

**Problem Statement:** Insurance sector is listed as a supported org type in `organisations` table and `insurance_risk_engine.py` exists, but Solvency II SCR climate stress testing and EIOPA climate opinion compliance are absent.

| Alternative | Description | Effort | Recommended? |
|-------------|-------------|--------|:---:|
| A. Add EIOPA Opinion climate stress test module | Implement EIOPA's 2023 climate stress scenario for insurers | 3-4 weeks | Yes |
| B. Map existing banking stress test to Solvency II | Reuse `stress_test_runner.py` with insurance-specific calibration | 1-2 weeks | Intermediate |
| C. Partner with actuarial software vendor | White-label integration | Commercial discussion | Longer term |

**Recommended:** Option B first, then Option A.

---

## Strongest Modules (Score ≥ 7.0)

| Module | Composite | Key Strength |
|--------|:---------:|-------------|
| Carbon Calculator v2 | 7.7 | GHG Protocol compliance, full scope 1/2/3, DEFRA/IEA/GWP references |
| EU Taxonomy Engine | 7.3 | Complete 6-objective, DNSH matrix, GAR/BTAR, 8 reference endpoints |
| Banking Risk Engine | 7.3 | Full Pillar 1 (SA/IRB/FRTB) + LCR/NSFR + AML + climate overlay |
| Data Lineage Service | 7.3 | 105 modules, 65+ edges, BCBS 239 compliance scoring |
| ECL Climate Engine | 7.2 | Full IFRS 9 §5.5, EBA GL/2022/16, BCBS 2022, proper stage classification |
| Sovereign Climate Risk | 7.0 | 51 country profiles, 5 NGFS scenarios, rating notch adjustment methodology |
| Facilitated Emissions | 7.0 | PCAF Parts B&C complete, all deal types including advisory disclosure |
| Supply Chain Scope 3 | 7.0 | Full 15 categories, SBTi targets, CSDDD value chain mapping |

---

## Weakest Areas (Score < 5.5)

| Area | Composite | Key Weakness |
|------|:---------:|-------------|
| Auth / RBAC | 2.0 | Not enforced on any calculation endpoint |
| Audit Trail | 2.3 | Middleware not wired despite DB table existing |
| Data Hub / Ingestion | 3.4 | Zero live ingesters; all frontend data is fallback arrays |
| XBRL Export | 5.3 | Unit bug, no filing workflow, no ESMA validation |
| Nature Risk | 5.3 | No PostGIS, float-based spatial queries, no live WDPA |
| CSRD Auto-Populate | 5.8 | S2-S4 absent, worker unconfirmed, assurance trail missing |

---

## Calculation Engine Deep-Dive Findings

### ECL Climate Engine — Methodology Quality
The `ecl_climate_engine.py` is the strongest individual calculation engine in the platform. It correctly references:
- IFRS 9 §5.5.9 (Stage 1: 12-month ECL)
- IFRS 9 §5.5.3 (Stage 2: Lifetime ECL on SICR)
- EBA GL/2022/16 §4.3 (climate as SICR driver)
- BCBS Principle 18 (forward-looking climate scenario analysis in provisioning)

The weakness is that LGD and EAD are function parameters, not drawn from the loan book database. This means the ECL output is methodologically sound but not data-integrated.

### PCAF Facilitated Emissions — Attribution Fractions
The `facilitated_emissions_engine.py` correctly implements:
- Bond underwriting AF = underwritten_amount / (total_issuance × 3) — PCAF Part C §3.2
- Equity placement AF = shares_placed / (market_cap × 3) — PCAF Part C §3.3
- Advisory = 0 (disclosure-only) — PCAF 2022 guidance

This is a differentiator — few platforms implement the facilitated emissions attribution correctly for all deal types.

### Factor Overlay Engine — Coverage vs. Depth
The overlay engine has 31 registries and 12 overlay methods. However, the registries use hardcoded lookup tables. For example, `sovereign risk (45 countries)` is a dict in Python code, not a live World Bank WGI pull. The engine's breadth (31 registries) masks the data depth limitation (all are static lookups).
