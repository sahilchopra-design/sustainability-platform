# Phase 4: VC/PE Module — User Guide & Documentation

## Overview
Phase 4 delivers a complete Private Equity / Venture Capital ESG analytics suite covering the full deal lifecycle: sourcing and screening, portfolio monitoring, value creation planning, GP/LP reporting, impact measurement, and IRR sensitivity analysis with ESG adjustments.

**126 tests | 3 sessions | 9 service engines | 17 API endpoints**

---

## Session 4A: Deal Pipeline + ESG Screening

### Functionality
- **ESG Screening Scorecard**: 5 dimensions (Environmental, Social, Governance, Transition Risk, Physical Risk) x 4 sub-dimensions each = 20-point assessment matrix
- **Red Flag Detection**: 4 hard flags (deal-breakers) + 3 soft flags + score-based alerts
- **Sector ESG Risk Heatmap**: 11 GICS-style sectors with pre-loaded risk profiles
- **Deal Comparison**: Side-by-side IC-ready comparison of multiple deals
- **Pipeline Summary**: Aggregate analytics across the deal funnel

### Key Components
| Component | File | Tests |
|-----------|------|-------|
| PE Deal Engine | `services/pe_deal_engine.py` | 44 tests |
| Deal Routes | `api/v1/routes/pe_deals.py` | 5 endpoints |
| DB Migration | `alembic/versions/038_add_pe_tables.py` | 4 tables |

### API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/pe/deals/screen` | Screen a deal with ESG scorecard |
| POST | `/api/v1/pe/deals/compare` | Compare multiple deals side-by-side |
| POST | `/api/v1/pe/deals/pipeline-summary` | Pipeline funnel analytics |
| GET | `/api/v1/pe/deals/sector-heatmap` | Sector ESG risk reference data |
| GET | `/api/v1/pe/deals/sub-dimensions` | ESG sub-dimension reference |

### User Stories

#### Story 1: PE Deal Team Associate — Deal Screening
**Persona**: Junior deal team member screening inbound opportunities

**Input Data Required**:
- Deal metadata: company name, sector, stage, deal size (EUR), entry multiple
- ESG sub-dimension scores (1-5 scale per sub-dimension, optional)
- Binary flags: UNGC violations, sanctions exposure, controversial weapons, severe environmental incidents, child labor risk, tax haven structure
- Transition plan status (boolean)

**Data Lineage**:
- ESG scores sourced from: DD provider reports (ERM, EY Parthenon), RepRisk, Sustainalytics
- Red flag data from: OFAC/EU sanctions lists, UNGC participant database, controversial weapons databases (Oslo Convention), FATF grey/blacklists
- Sector risk profiles from: internal risk taxonomy aligned to GICS Level 1

**Reference Data**:
- 11-sector ESG risk heatmap (pre-loaded)
- 20 ESG sub-dimensions (4 per dimension)
- Red flag definitions with severity classification (hard/soft)
- Risk band thresholds: low (<=2.0), medium (2.0-3.0), high (3.0-4.0), critical (>4.0)

**Output & Insights**:
- Composite ESG score (1-5) with risk band classification
- Per-dimension breakdown with traffic light indicators
- Red flag report: hard flags (automatic reject) vs soft flags (proceed with conditions)
- Screening recommendation: proceed / proceed_with_conditions / reject
- Conditions list for proceed_with_conditions cases
- Sector-relative ESG positioning

#### Story 2: Investment Committee Member — Deal Comparison
**Persona**: IC member comparing 3-5 deals for capital allocation

**Input**: Multiple deal inputs (same schema as Story 1)

**Output & Insights**:
- Side-by-side comparison table: composite score, dimension breakdown, red flags, deal-breaker status
- Relative ranking by ESG risk
- Aggregate pipeline statistics: deals by stage, by sector, average deal size, red flag prevalence

#### Story 3: Head of ESG / Responsible Investment — Pipeline Monitoring
**Persona**: ESG team lead monitoring deal quality across the pipeline

**Output & Insights**:
- Pipeline summary: total deals, deals by stage/sector, average ESG score
- Red flag deals count vs deal-breaker deals count
- Sector heatmap for portfolio construction risk

---

## Session 4B: Portfolio Company Monitoring + Value Creation

### Functionality
- **ILPA KPI Tracking**: 12 standardised ESG KPIs aligned to ILPA ESG Data Convergence Initiative
- **Traffic Light Dashboard**: Green/amber/red per KPI based on targets and YoY trends
- **YoY Improvement Tracking**: Absolute and percentage change with directional assessment
- **Portfolio Aggregation**: Ownership-weighted KPI averages across the fund
- **Value Creation Plans**: Sector-specific ESG improvement levers with CapEx/benefit estimation
- **Exit Impact Modelling**: Multiple expansion from ESG improvement (25bps per point)
- **Milestone Generation**: Auto-generated implementation timeline with deliverables

### Key Components
| Component | File | Tests |
|-----------|------|-------|
| Portfolio Monitor | `services/pe_portfolio_monitor.py` | 33 tests |
| Value Creation Engine | `services/pe_value_creation.py` | (shared tests) |
| Portfolio Routes | `api/v1/routes/pe_portfolio.py` | 5 endpoints |

### API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/pe/portfolio/monitor-company` | Monitor single company KPIs |
| POST | `/api/v1/pe/portfolio/monitor-portfolio` | Fund-wide portfolio monitoring |
| POST | `/api/v1/pe/portfolio/value-creation-plan` | Generate value creation plan |
| GET | `/api/v1/pe/portfolio/kpi-template` | ILPA KPI collection template |
| GET | `/api/v1/pe/portfolio/sector-levers` | Sector ESG lever reference |

### ILPA KPI Reference (12 KPIs)
| KPI ID | Name | Category | Direction |
|--------|------|----------|-----------|
| GHG-1 | Scope 1 GHG Emissions | Emissions | Lower is better |
| GHG-2 | Scope 2 GHG Emissions | Emissions | Lower is better |
| E-1 | Total Energy Consumption | Energy | Lower is better |
| E-2 | Renewable Energy Share | Energy | Higher is better |
| W-1 | Water Withdrawal | Water | Lower is better |
| WS-1 | Total Waste Generated | Waste | Lower is better |
| WS-2 | Waste Recycled | Waste | Higher is better |
| D-1 | Board Gender Diversity | Diversity | Higher is better |
| D-2 | Workforce Gender Diversity | Diversity | Higher is better |
| S-1 | Work-Related Injuries Rate | Safety | Lower is better |
| S-2 | Work-Related Fatalities | Safety | Lower is better |
| G-1 | Independent Board Members | Governance | Higher is better |

### User Stories

#### Story 4: Portfolio Manager — Quarterly KPI Review
**Persona**: PE portfolio manager reviewing portfolio company ESG performance

**Input Data Required**:
- Company metadata: ID, name, sector, fund ID, equity invested, ownership %
- Current period KPI values (up to 12 ILPA KPIs)
- Prior period KPI values (for YoY comparison)
- Target values per KPI (optional, for target-based traffic lights)

**Data Lineage**:
- KPI data sourced from: portfolio company quarterly reporting (CFO/sustainability team)
- Targets from: 100-day plan commitments, IC investment memo, sector benchmarks
- Ownership % from: fund admin / legal documentation

**Reference Data**:
- ILPA ESG Data Convergence Initiative KPI definitions (12 metrics)
- Direction indicators (lower_is_better / higher_is_better)
- Traffic light thresholds: green (on target or improved), amber (within 20% or no data), red (>20% off target or deteriorated)

**Output & Insights**:
- Per-KPI status: current value, prior value, YoY change (absolute + %), improved flag, target check, traffic light
- Company-level dashboard: green/amber/red counts, overall traffic light
- Fund-level aggregation: ownership-weighted average KPIs, portfolio green/amber/red percentages
- Worst-performing companies ranked by red KPI count
- Best-performing companies ranked by green KPI count

#### Story 5: Operating Partner — Value Creation Planning
**Persona**: PE operating partner designing ESG value creation plan for a portfolio company

**Input Data Required**:
- Company: ID, name, sector
- Financials: EBITDA (EUR), entry multiple, revenue (EUR, optional)
- Current ESG score (0-100, optional)

**Data Lineage**:
- EBITDA from: portfolio company financials (audited)
- Entry multiple from: deal closing documentation
- Sector classification from: internal taxonomy

**Reference Data**:
- Sector-specific ESG levers: Technology (4), Healthcare (3), Industrials (4), Consumer Staples (3), Energy (3)
- Default levers for unmapped sectors (3)
- CapEx ranges, annual savings %, EBITDA uplift % per lever
- ESG multiple expansion: 25bps per ESG score point improvement
- ESG improvement cap: 20 points maximum

**Output & Insights**:
- Lever-by-lever estimates: CapEx (low/mid/high), annual savings, EBITDA uplift, ROI multiple, implementation months
- Total plan CapEx, savings, and EBITDA uplift
- Implementation milestones with deliverables (auto-sorted by month)
- Exit impact: projected ESG score improvement, multiple expansion, exit multiple, exit EV, total value creation (EUR)
- Plan duration (longest lever implementation)

---

## Session 4C: GP/LP Reporting + Impact Framework + IRR Sensitivity

### Functionality
- **LP Report Generation**: Quarterly and annual reports with fund metrics, portfolio summaries, ESG annex
- **Fund Metrics**: TVPI, DPI, RVPI, net/gross IRR, called %, dry powder
- **SFDR ESG Annex**: Art.6/8/9 periodic disclosure with PAI indicators
- **Impact Measurement**: IMP 5-dimension framework (what, who, how much, contribution, risk)
- **SDG Alignment**: UN SDG mapping with fund-level contribution analysis
- **IRR/MOIC Sensitivity**: 3-scenario analysis (base/upside/downside)
- **ESG Return Impact**: Multiple expansion and risk discount modelling
- **Sensitivity Grid**: 5x5 exit multiple vs EBITDA growth matrix
- **IRR Calculator**: Newton-Raphson method from explicit quarterly cashflows

### Key Components
| Component | File | Tests |
|-----------|------|-------|
| Reporting Engine | `services/pe_reporting_engine.py` | 15 tests |
| Impact Framework | `services/pe_impact_framework.py` | 16 tests |
| IRR Sensitivity | `services/pe_irr_sensitivity.py` | 18 tests |
| Reporting Routes | `api/v1/routes/pe_reporting.py` | 7 endpoints |

### API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/pe/reporting/lp-report` | Generate LP report |
| POST | `/api/v1/pe/reporting/fund-impact` | Fund-level impact assessment |
| POST | `/api/v1/pe/reporting/irr-sensitivity` | IRR/MOIC sensitivity analysis |
| POST | `/api/v1/pe/reporting/compute-irr` | IRR from explicit cashflows |
| GET | `/api/v1/pe/reporting/pai-indicators` | SFDR PAI reference data |
| GET | `/api/v1/pe/reporting/sdg-definitions` | UN SDG reference data |
| GET | `/api/v1/pe/reporting/impact-dimensions` | IMP dimension reference |

### User Stories

#### Story 6: Investor Relations Manager — LP Quarterly Report
**Persona**: IR professional preparing quarterly LP communication

**Input Data Required**:
- Fund performance: fund ID/name, vintage year, fund size, committed/called/distributed capital, NAV, management fees, carried interest
- Portfolio companies: ID, name, sector, invested amount, current NAV, ownership %, entry date, ESG score, traffic light, carbon intensity
- Reporting period, report type (quarterly/annual)
- SFDR classification (Art.6/8/9)

**Data Lineage**:
- Fund performance from: fund administrator quarterly valuation report
- Company NAV from: quarterly fair value assessment (IPEV guidelines)
- ESG scores from: portfolio monitoring engine (Session 4B)
- Carbon intensity from: portfolio company GHG inventory

**Reference Data**:
- ILPA Reporting Template v3 structure
- SFDR Art.11 periodic disclosure requirements
- 10 mandatory PAI indicators (SFDR Annex I)
- SFDR classification thresholds: Art.9 (80% sustainable), Art.8 (30%), Art.6 (0%)

**Output & Insights**:
- Fund metrics dashboard: TVPI, DPI, RVPI, net/gross IRR, called %, dry powder
- Portfolio company table: MOIC per company, ESG score, traffic light
- Executive summary (auto-generated narrative)
- ESG Annex: sustainable investment %, taxonomy-aligned %, DNSH %, PAI indicators, weighted ESG score, carbon footprint, green revenue %
- Report sections: Fund Overview, Capital Account, Portfolio Companies, ESG Annex, Annual Review (annual only)

#### Story 7: Impact Fund Manager — SDG & Impact Reporting
**Persona**: Impact fund manager reporting to impact-first LPs

**Input Data Required**:
- Fund: ID, name, strategy (impact/esg_integrated/thematic), SFDR classification
- Per company: ID, name, sector, primary/secondary SDGs, IMP dimension scores (1-5), quantitative metrics (jobs, beneficiaries, CO2 avoided, renewable MWh), theory of change, additionality evidence, invested/NAV amounts

**Data Lineage**:
- Impact scores from: impact due diligence process (IMP framework)
- SDG mapping from: company business model analysis
- Quantitative metrics from: portfolio company impact reports
- Additionality evidence from: counterfactual analysis

**Reference Data**:
- 17 UN SDG definitions with categories
- 5 IMP dimensions (what, who, how much, contribution, risk)
- Impact rating thresholds: high (>=4.0), medium (>=3.0), low (>=2.0), neutral (<2.0)
- Additionality: strong (>=4.0), moderate (>=2.5), weak (<2.5)
- IMM formula: (beneficiaries x EUR100 + CO2 x EUR50) / invested

**Output & Insights**:
- Company-level: impact rating, composite score, dimension breakdown, SDG names, additionality rating, Impact Multiple of Money (IMM)
- Fund-level: weighted impact score, impact rating, high/medium/low counts
- SDG contribution matrix: which SDGs addressed, company count per SDG, invested capital per SDG, % of fund
- Aggregated metrics: total jobs created, total beneficiaries, total CO2 avoided, total renewable MWh
- Impact summary narrative

#### Story 8: Deal Team Principal — IRR Sensitivity & ESG Return Impact
**Persona**: Senior deal professional modelling returns and ESG value impact

**Input Data Required**:
- Deal: ID, company name, sector
- Financials: entry EV, entry EBITDA, entry multiple, equity invested, net debt
- Assumptions: hold period (years), EBITDA growth %, exit multiple (0 = same as entry)
- ESG: current ESG score (0-100), expected ESG improvement (points)

**Data Lineage**:
- Entry financials from: deal closing documentation
- Growth assumptions from: management case / DD model
- ESG score from: screening engine (Session 4A)
- ESG improvement targets from: value creation plan (Session 4B)

**Reference Data**:
- ESG multiple expansion: 15bps per ESG score point improvement
- ESG risk discount: 25bps per 10 points below ESG score of 50
- Scenario offsets: upside (+2x mult, +2% growth), downside (-2x mult, -2% growth)
- Sensitivity grid: 5x5 (exit multiple +/- 2x vs EBITDA growth +/- 2%)

**Output & Insights**:
- 3 scenarios: base case, upside, downside — each with IRR %, MOIC, exit EV, equity value
- ESG impact analysis: base vs ESG-adjusted IRR (bps delta), MOIC change, multiple expansion, valuation premium %, risk discount %
- 5x5 sensitivity grid: 25 cells showing IRR/MOIC at different exit multiple x growth combinations
- Base case coordinates highlighted in grid
- IRR calculator from explicit cashflows (Newton-Raphson)
- Summary narrative with key metrics

---

## Value Propositions

### For PE/VC Fund Managers
1. **Integrated deal-to-exit ESG workflow**: Screen deals, monitor portfolio, plan value creation, report to LPs — all in one platform
2. **Regulatory compliance**: SFDR Art.6/8/9 periodic disclosure, PAI indicators, ILPA data convergence
3. **Return attribution**: Quantify how ESG improvements translate to multiple expansion and IRR uplift
4. **Impact credibility**: IMP-aligned framework with SDG mapping and additionality assessment

### For Investment Teams
1. **Faster screening**: Automated red flag detection replaces manual checklist reviews
2. **IC-ready analytics**: Side-by-side deal comparison with ESG dimension breakdown
3. **Sector intelligence**: Pre-loaded ESG risk heatmap across 11 sectors
4. **Sensitivity analysis**: 25-cell IRR/MOIC grid with ESG overlay

### For Portfolio Operations / Operating Partners
1. **Standardised KPI tracking**: ILPA-aligned 12-KPI framework across all portfolio companies
2. **Traffic light dashboard**: Instant visual on which companies need attention
3. **Value creation playbook**: Sector-specific ESG levers with CapEx/benefit estimates
4. **Milestone planning**: Auto-generated implementation timeline

### For Investor Relations
1. **Automated LP reports**: Quarterly/annual reports with fund metrics and ESG annex
2. **SFDR compliance**: Classification-specific disclosure thresholds (Art.6/8/9)
3. **Impact narrative**: Auto-generated executive summary with key metrics
4. **PAI reporting**: 10 mandatory PAI indicators pre-structured

---

## Competitive Advantages
1. **Full lifecycle coverage**: Only platform covering screening → monitoring → value creation → reporting → impact in a single module
2. **ESG-return linkage**: Quantified relationship between ESG improvement and financial returns (IRR/MOIC)
3. **Regulatory alignment**: SFDR, ILPA, IMP, SDG frameworks built in — not bolted on
4. **Sector-specific intelligence**: Pre-loaded ESG levers for 5 sectors + defaults for unmapped sectors

## Target Market Segments
- Mid-market PE funds (EUR 200M-2B AUM)
- Impact funds (SFDR Art.9 classified)
- PE fund-of-funds requiring portfolio-level ESG aggregation
- GP operational teams seeking standardised ESG playbooks
- VC funds with ESG integration mandates

## Expansion Roadmap
- **Co-investment module**: LP co-invest ESG analytics
- **Secondary market**: ESG-adjusted NAV for secondary pricing
- **GP scoring**: ESG maturity assessment for GPs (PRI alignment)
- **Benchmark database**: PE ESG benchmark data (ILPA peer comparison)
- **Monte Carlo IRR**: Full stochastic simulation (currently deterministic scenarios)
- **Real-time KPI ingestion**: API connectors to portfolio company systems

---

## Technical Summary

| Metric | Value |
|--------|-------|
| Services created | 6 (pe_deal_engine, pe_portfolio_monitor, pe_value_creation, pe_reporting_engine, pe_impact_framework, pe_irr_sensitivity) |
| API endpoints | 17 |
| Test cases | 126 (44 + 33 + 49) |
| Test pass rate | 100% |
| DB tables | 4 (pe_deals, pe_screening_scores, pe_portfolio_companies, pe_sector_risk_heatmap) |
| Reference data sets | ILPA KPIs (12), Sector ESG Risk (11), ESG Sub-dimensions (20), Sector Levers (5 sectors), PAI Indicators (10), SDG Definitions (17), IMP Dimensions (5) |
