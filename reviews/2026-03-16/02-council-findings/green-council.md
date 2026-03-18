# 02 — Green Council: Upside, Strategic, and Differentiation Lens
**Date:** 2026-03-16

---

## Top Differentiation Opportunities by Sector

### Finance — Banking

**D1. Unified Climate-ECL-Capital Chain (Genuine Differentiator)**
No other publicly available platform integrates IFRS 9 ECL climate overlays → Basel IV RWA capital impact → EBA Pillar 3 GAR disclosure into a single traceable chain. The platform has all three engines built. The missing link is a workflow that runs them in sequence with shared inputs and a single audit-ready output.

What this unlocks:
- Banks can answer "What is our capital position under a 3°C delayed transition scenario?" in one session
- EBA and ECB supervisors are specifically requesting this linkage
- Regulatory differentiation: this satisfies EBA stress test (ST 2025) + ICAAP + GAR in one tool

Effort to close: Wire `ecl_climate_engine` → `gar_calculator` → `banking_risk_engine` Pillar 3 output via a new orchestration route. ~2 weeks.

---

**D2. PCAF Parts A + B + C in a Single Platform (Genuine Differentiator)**
PCAF Parts A (financed), B (insurance), and C (facilitated) are implemented. The combination in one platform is rare — most vendors cover Part A only. Investment banks (facilitated, Part C) and insurance groups (Part B) have almost no specialist tools. This is the clearest competitive moat.

What this unlocks:
- Bank holding companies covering commercial lending + insurance + capital markets can run all PCAF emissions in one workflow
- SFDR PAI #1 (GHG emissions) sourced from PCAF Parts A+B+C can be auto-populated
- Investor confidence in PCAF DQS certification (once DQS portfolio aggregation is fixed)

Effort to close: Complete PCAF DQS portfolio aggregation (WORK_PLAN B4, ~3 days) + PCAF Listed Equity (B6, ~1 week).

---

### Finance — Asset Management

**D3. CSRD Auto-Populate → XBRL Filing Pipeline**
The combination of `csrd_auto_populate.py` (ESRS_MAPPINGS from platform module outputs) + `xbrl_export_engine.py` (EFRAG taxonomy-compliant tagging) + `regulatory_report_compiler.py` is, in principle, a near-complete CSRD disclosure factory. No commercial tool currently offers this end-to-end for free-standing SaaS.

What this unlocks:
- Asset managers with CSRD obligations (>500 employee threshold from FY2025) can produce their first CSRD report entirely within the platform
- Potential to white-label as "CSRD Report Builder" — a separate product tier
- Integration path: ESRS data points auto-populated from module outputs → reviewed/edited in UI → exported as iXBRL for ESMA submission

Effort to close: Fix XBRL unit bug (30 min) + add WeasyPrint PDF renderer (1 week) + build CSRD review/approval workflow (2 weeks).

---

**D4. Glidepath + PACTA + Engagement Tracker = Active Stewardship Platform**
The platform has: `glidepath_tracker`, `am_engine.py` (PACTA temperature scoring), `engagement_tracker`, `ca100.py` (CA100+ benchmark). Together these form an active stewardship product — asset managers can track portfolio company Paris alignment, log engagement activities, and measure progress against targets.

What this unlocks:
- PRI-aligned active stewardship reporting (PRI strategy 6.1)
- UK Stewardship Code compliance (Principle 9: engagement)
- EU Shareholders Rights Directive II (SRD II) engagement documentation
- This is a B2B SaaS product add-on that asset managers currently buy from Ceres / CHRB separately

Effort to close: Wire CA100+ data to glidepath tracker + PACTA output; add engagement outcome tracking fields. ~2-3 weeks.

---

### Energy Sector

**D5. Integrated Energy Transition Risk → Project Finance → Green Bond Screening**
The platform covers: `energy_transition_risk`, `green_hydrogen_calculator`, `ppa_risk_scorer`, `project_finance_engine`, `green bond screening in am_engine`. An energy developer can:
1. Assess transition risk for existing assets (CRREM, stranding)
2. Model a new renewable project (DSCR/LCOE)
3. Structure green bond financing (ICMA GBS alignment)
4. Assess RFNBO compliance for green hydrogen

No other platform covers this energy developer → capital markets chain. This could be positioned as a "bankable sustainability case" tool for energy project developers raising green finance.

Effort to close: Wire CRREM real data (WORK_PLAN F5) + IRENA LCOE (A13) + PPA market data stub → ~3 weeks.

---

**D6. EU ETS2 Readiness Assessment (Time-Sensitive)**
EU ETS2 (buildings + road transport) starts in 2027 with first monitoring year 2025. The `GarEtsPage.jsx` has an "ETS2 Readiness" tab already built. Adding the actual ETS2 scope assessment backend (`eu_ets_engine.py` already partially covers this) could be a first-mover position.

Time sensitivity: ETS2 obliges energy distributors and fuel suppliers to start MRV in 2025. The market for ETS2 compliance tooling is open now.

Effort to close: Extend `eu_ets_engine.py` for ETS2 fuel distributors and buildings operators. ~1 week.

---

### Supply Chain

**D7. EUDR + CSDDD + ESRS E4 Unified Compliance Workflow**
The platform has `eudr_engine.py`, `csddd_engine.py`, and `csrd_auto_populate.py` covering ESRS E4 biodiversity. These three EU regulations have significant overlap (deforestation DD in EUDR = CSDDD ENV-02 = ESRS E4 DR E4-4). No tool currently presents this as a unified supply chain compliance workflow.

What this unlocks:
- Supply chain operators (food & beverage, retail, forestry) can complete EUDR DDS, CSDDD ENV-02 assessment, and CSRD ESRS E4 disclosure in a single workflow
- Cross-framework efficiency is genuinely valued: compliance teams spend significant time reconciling duplicate data requirements
- This is a direct competitor to Assent, Sourcemap, and EcoVadis for EUDR compliance

Effort to close: Build a unified "Supply Chain Sustainability Compliance" workflow page that sequences EUDR → CSDDD → ESRS E4. ~2 weeks.

---

## Compounding Value Plays

### Chain 1: Entity → Everything
The `entity_resolution_service.py` + `company_profiles` + `cross_module_entity_linkage` (migration 042) create a foundation where a single LEI lookup populates entity data across ECL, PCAF, CSRD, SFDR, CSDDD, and EU Taxonomy modules. Once GLEIF ingestion is live (WORK_PLAN A3), this becomes:

**LEI input → auto-populated entity data → pre-filled calculation inputs across all modules**

This would reduce data entry friction by ~70% for an analyst running a full counterparty assessment.

---

### Chain 2: Data Quality → Premium Tier
PCAF DQS tiers have a direct commercial implication: DQS 1-2 enables SFDR Article 8/9 claims; DQS 3-5 does not. Once live data ingestion (GLEIF, EDGAR, yfinance) is active, the platform can offer:

**"DQS Certified" tier** — platform-verified DQS scores backed by traceable data lineage (BCBS 239 compliance already in data_lineage_service.py)

This creates a premium product differentiation: DQS certification is a recurring service clients would pay for per assessment cycle.

---

### Chain 3: CSRD Auto-Populate → Reduced Disclosure Cost
If the CSRD auto-populate chain reaches 80% ESRS DP coverage (currently ~40% given missing S2-S4), the platform eliminates the core manual effort in a CSRD disclosure project (typically 200-400 person-hours for a large company). At £5-15K/day consulting rates, this unlocks:

**Value proposition: "Replace 3 weeks of CSRD consultant time with 3 hours in the platform"**

---

## Time-Sensitive Opportunities

| Opportunity | Deadline | Why Time-Sensitive |
|-------------|----------|-------------------|
| CSRD first wave compliance (NFRD-in-scope, FY2024 reporting) | June 2025 filing | Companies filing now need tooling today |
| EUDR full applicability | December 2025 | Operators need DDS workflows operational now |
| EU ETS2 monitoring year 1 | 2025 (retroactive) | ETS2 scope definition tooling needed |
| SFDR RTS Level 2 periodic disclosures (FY2025) | June 2026 | Asset managers need PAI data pipelines now |
| ISSB S1/S2 adoption (Australia mandatory from 2025, UK expected 2025) | 2025 | Non-EU markets adopting ISSB rapidly |
| CBAM definitive regime | January 2026 | CBAM declarant obligations go live |
| CSDDD first wave (10,000+ employees) | July 2027 | But DD processes must start now |

---

## Revenue / Cost Upside by Persona

### Analytics Lead (Buyer: Risk Analytics Head, CRO Office)
| Opportunity | Revenue Model |
|-------------|--------------|
| Climate-adjusted ECL as a service | Per-portfolio license, annual |
| Model validation as a service | Per-model certification fee |
| BCBS 239 data lineage reporting | Annual compliance subscription |

Estimated addressable buyer: 200+ banks with IFRS 9 obligations in UK/EU/APAC

---

### Investment Lead (Buyer: CIO, Head of Sustainability, Portfolio Manager)
| Opportunity | Revenue Model |
|-------------|--------------|
| SFDR PAI monitoring dashboard | Per-fund annual license |
| Portfolio Paris alignment tracker | AUM-based license |
| ESG-constrained optimisation | Per-portfolio calculation fee |
| PE deal ESG screening | Per-deal fee |

Estimated addressable buyer: 500+ SFDR-obligated fund managers in EU

---

### Sustainability Regulatory Lead (Buyer: Chief Sustainability Officer, General Counsel)
| Opportunity | Revenue Model |
|-------------|--------------|
| CSRD disclosure factory (auto-populate → XBRL) | Per-report license or SaaS subscription |
| EU Taxonomy alignment assessment | Per-entity annual license |
| EUDR DDS management | Per-operator subscription |
| Double Materiality Assessment workflow | Per-assessment fee |
| Regulatory obligation calendar + deadline alerts | Platform tier feature |

Estimated addressable buyer: All CSRD-in-scope companies (50,000+ in EU) — largest TAM

---

## Platform-Level Strategic Assets (Not Yet Exploited)

1. **Data Lineage Graph** — the `data_lineage_service.py` with 105 modules and 65+ edges is a publishable audit artifact. No competitor publishes their full data lineage graph. Making this user-visible would be a trust-building differentiator with institutional compliance teams.

2. **Cross-Framework Mappings** — the platform internally maps CSRD → SFDR → EU Taxonomy → ISSB → GRI → TCFD in multiple engines. This de-duplication intelligence has high commercial value to compliance teams who currently maintain these mappings manually in spreadsheets.

3. **PCAF Parts A+B+C Together** — as noted above, this combination is rare. Marketing this as a "Total Financed Emissions Platform" covering all PCAF categories positions the platform distinctly vs. single-category competitors.

4. **NGFS-Aligned Scenario Engine** — the custom scenario builder combined with NGFS trajectories is already a research-grade tool. Positioning it as "used for ICAAP stress testing" or "ECB supervisory scenario analysis" creates institutional credibility.
