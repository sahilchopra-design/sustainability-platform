"""
Narrative Templates — Semi-narrative boilerplate text for all report types.
===========================================================================
Each template is a Python f-string–ready dict with a `render(data: dict) -> str`
helper. Placeholders use `{key}` syntax; every key should be present in the `data`
dict passed to `render()`.  Missing keys fall back to "N/A".

Report types covered:
  1.  CLIMATE_RISK_IMPACT        — Climate scenario PD/EL portfolio analysis
  2.  TCFD_GOVERNANCE            — TCFD Pillar 1: Board & Management oversight
  3.  TCFD_STRATEGY              — TCFD Pillar 2: Risks/Opportunities & Resilience
  4.  TCFD_RISK_MANAGEMENT       — TCFD Pillar 3: Identification & Integration
  5.  TCFD_METRICS_TARGETS       — TCFD Pillar 4: GHG Metrics & Targets
  6.  SFDR_ART8                  — SFDR Art.8 Periodic Disclosure
  7.  SFDR_ART9                  — SFDR Art.9 Periodic Disclosure
  8.  CSRD_ESRS_E1               — ESRS E1 Climate Change narrative
  9.  CSRD_ESRS_GENERAL          — ESRS 2 General Disclosures (IRO process)
 10.  ISSB_S2_GOVERNANCE         — IFRS S2 §6-15 Governance
 11.  ISSB_S2_STRATEGY           — IFRS S2 §16-34 Strategy & Scenario Analysis
 12.  ISSB_S2_RISK_MGMT          — IFRS S2 §35-38 Risk Management
 13.  ISSB_S2_METRICS            — IFRS S2 §39-51 Metrics & Targets
 14.  SEC_REG_SK                 — SEC Reg S-K Items 1501-1505
 15.  GRI_305_EMISSIONS          — GRI 305 Emissions narrative
 16.  BRSR_PRINCIPLE_6           — BRSR Principle 6 (Environment)
 17.  CARBON_CALCULATOR          — Carbon Calculator executive summary
 18.  NATURE_RISK_LEAP           — TNFD LEAP nature risk narrative
 19.  STRANDED_ASSET             — Stranded Asset analysis narrative
 20.  GAR_ETS                    — EU ETS/GAR regulatory narrative

Usage:
    from services.narrative_templates import render_section
    text = render_section("TCFD_GOVERNANCE", {
        "entity_name": "FirstEuro Bank AG",
        "board_committee": "Risk & Sustainability Committee",
        ...
    })
"""
from __future__ import annotations

from string import Formatter
from typing import Any


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

class _SafeDict(dict):
    """Returns 'N/A' for missing keys instead of raising KeyError."""
    def __missing__(self, key: str) -> str:
        return "N/A"


def render_section(template_key: str, data: dict[str, Any]) -> str:
    """
    Render a named narrative template with the supplied data dict.
    Missing keys render as 'N/A'.

    Args:
        template_key:  One of the TEMPLATE_REGISTRY keys (e.g. 'TCFD_GOVERNANCE')
        data:          Dict of placeholder → value

    Returns:
        Rendered string.
    """
    if template_key not in TEMPLATE_REGISTRY:
        raise KeyError(f"Unknown template '{template_key}'. Available: {list(TEMPLATE_REGISTRY)}")
    tmpl = TEMPLATE_REGISTRY[template_key]
    return Formatter().vformat(tmpl, [], _SafeDict(data))


def render_all_tcfd(data: dict[str, Any]) -> dict[str, str]:
    """Return all four TCFD pillar narratives as a dict keyed by pillar name."""
    keys = ["TCFD_GOVERNANCE", "TCFD_STRATEGY", "TCFD_RISK_MANAGEMENT", "TCFD_METRICS_TARGETS"]
    return {k: render_section(k, data) for k in keys}


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

TEMPLATE_REGISTRY: dict[str, str] = {}

# 1 ─────────────────────────── CLIMATE RISK IMPACT ──────────────────────────

TEMPLATE_REGISTRY["CLIMATE_RISK_IMPACT"] = """\
EXECUTIVE SUMMARY — CLIMATE RISK IMPACT ANALYSIS

This report presents the results of a forward-looking climate scenario analysis conducted for \
{portfolio_name} ({num_assets} counterparties; total exposure {currency}{total_exposure:,.0f}). \
Analysis was performed across {num_scenarios} NGFS-aligned scenarios at horizons of \
{horizons}.

Under the most adverse scenario assessed ({worst_scenario}), the portfolio's Expected Loss (EL) \
reaches {currency}{worst_el:,.0f} by {worst_horizon}, equivalent to {worst_el_pct:.1f}% of \
total exposure and implying an average probability-of-default (PD) uplift of {worst_pd_change:+.1f}% \
relative to the baseline. The 95th-percentile climate Value-at-Risk (CVaR) under this scenario \
stands at {currency}{worst_var95:,.0f}.

Conversely, under an orderly net-zero pathway ({best_scenario}), the portfolio's climate EL \
remains contained at {currency}{best_el:,.0f} by {best_horizon} ({best_el_pct:.1f}% of exposure), \
illustrating that early and credible decarbonisation action substantially reduces long-run \
credit risk.

Sector concentration: {top_sector} accounts for {top_sector_pct:.0f}% of total exposure and \
exhibits above-average transition risk sensitivity owing to its reliance on carbon-intensive \
production processes. Geographic concentration: {top_country} represents {top_country_pct:.0f}% \
of exposure and faces elevated physical risk from {top_country_hazard}.

Methodology: Asset-level PD transition probabilities are derived from NGFS v4 carbon price \
and temperature pathways mapped via the platform's Climate Risk Engine. Physical risk scores \
follow IPCC AR6 representative concentration pathways (RCPs). ECL staging follows IFRS 9 \
three-stage model with climate scenario overlay applied at the counterparty level.
"""

# 2 ────────────────────────────── TCFD GOVERNANCE ───────────────────────────

TEMPLATE_REGISTRY["TCFD_GOVERNANCE"] = """\
GOVERNANCE (TCFD GOV-a, GOV-b)

Board Oversight (GOV-a)
{entity_name}'s {board_committee} has primary responsibility for climate-related risk oversight. \
The committee meets {board_frequency} and receives structured climate briefings covering physical \
hazard exposures, transition scenario sensitivities, and progress against the entity's net-zero \
commitments. Climate-related performance metrics are integrated into the Board's annual review \
of risk appetite, capital allocation, and executive remuneration.

The Board approved the entity's Climate Transition Plan on {transition_plan_approval_date} and \
reviews progress against milestones at each {board_frequency} meeting. Material climate risks and \
opportunities are disclosed in the Annual Report and Accounts in accordance with {disclosure_standard}.

Management's Role (GOV-b)
Day-to-day climate risk management is led by the {climate_role} reporting to {cro_title}. \
The {climate_committee} — comprising representatives from Risk, Finance, Treasury, Operations, \
and Sustainability — meets {mgmt_committee_frequency} to review the climate risk register, \
approve scenario parameter updates, and oversee remediation actions arising from assessments. \
Climate risk is embedded in the entity's {erm_framework} Enterprise Risk Management framework \
and is subject to Internal Audit review on a {audit_frequency} basis.
"""

# 3 ───────────────────────────── TCFD STRATEGY ───────────────────────────────

TEMPLATE_REGISTRY["TCFD_STRATEGY"] = """\
STRATEGY (TCFD STR-a, STR-b, STR-c)

Climate-Related Risks and Opportunities (STR-a)
{entity_name} has identified the following material climate-related risks and opportunities \
across short- ({short_horizon}), medium- ({medium_horizon}), and long-term ({long_horizon}) horizons.

Transition risks: Policy and regulatory risk is assessed as {transition_policy_rating} — driven \
primarily by the EU ETS, CBAM, CSRD mandatory disclosure obligations, and the anticipated \
tightening of climate-related capital requirements under CRR III / Basel IV. Technology risk \
is rated {transition_tech_rating}, reflecting the pace of electrification, green hydrogen \
adoption, and stranded-asset exposure in {top_transition_sector}. Market risk is {transition_market_rating}, \
with demand shifts toward low-carbon products creating both revenue risks for carbon-intensive \
counterparties and opportunities in green finance.

Physical risks: Chronic risks include rising mean temperatures increasing {chronic_risk_type} \
across {chronic_risk_geography}. Acute risks are led by {acute_hazard} events, with {acute_risk_country} \
identified as the highest-exposure jurisdiction (physical risk score: {top_physical_risk_score}/10).

Opportunities: Green lending / green bond underwriting presents a {green_opportunity_size} \
revenue opportunity by {green_opportunity_year}, consistent with the entity's \
{sustainable_finance_target} sustainable finance commitment. Advisory fees from transition \
planning services are also growing, representing {advisory_revenue_pct}% of wholesale \
fee income in {reporting_year}.

Impact on Business, Strategy, and Financial Planning (STR-b)
Transition scenario modelling indicates that a disorderly transition would increase \
credit provisions by {disorderly_provision_increase}% versus baseline by 2035, concentrated \
in {top_at_risk_sector}. The entity has responded by introducing climate-risk overlays in credit \
origination criteria and tightening sector exposure limits for carbon-intensive industries.

Capital planning incorporates a climate stress buffer of {climate_capital_buffer_bps} bps, \
calculated as the 2050 climate-adjusted CVaR (99th percentile) across the four NGFS scenarios, \
allocated proportionally across Business Units by sector and geography.

Scenario Resilience (STR-c)
{entity_name} tested portfolio resilience under four NGFS v4 scenarios: Net Zero 2050, \
Below 2°C, Delayed Transition, and Current Policies. Key findings:

  • Net Zero 2050: EL {nz_el_pct:.1f}% of exposure by 2050. Strategy is resilient; \
    green finance pipeline offsets higher provisions in carbon-intensive sectors.
  • Delayed Transition: EL peaks at {delayed_el_pct:.1f}% by 2040 before declining as \
    late policy action takes effect. Near-term capital adequacy remains above SREP requirements.
  • Current Policies: EL reaches {current_el_pct:.1f}% by 2050. Physical risk dominates \
    beyond 2040, requiring material repricing of real estate and agriculture exposures.
"""

# 4 ────────────────────────── TCFD RISK MANAGEMENT ──────────────────────────

TEMPLATE_REGISTRY["TCFD_RISK_MANAGEMENT"] = """\
RISK MANAGEMENT (TCFD RM-a, RM-b, RM-c)

Identification and Assessment Processes (RM-a)
{entity_name} identifies climate-related risks through a combination of (i) top-down \
scenario analysis using NGFS-aligned pathways; (ii) bottom-up counterparty-level physical \
and transition risk scoring via the platform's Climate Risk Engine; and (iii) sector-level \
heat-map assessments covering {num_sectors} NACE sectors.

Physical risk scores are derived from IPCC AR6 hazard data (flood, heat stress, drought, \
sea-level rise, windstorm) and assigned at the asset level where geolocation data is available \
({pct_geolocated}% of exposure by value). Transition risk scores incorporate carbon intensity \
(Scope 1+2 tCO₂e/€ revenue), regulatory exposure (EU ETS sector membership, CBAM commodity \
inclusion), and technology readiness indices.

Materiality is assessed using a probability × impact matrix calibrated to the entity's \
risk appetite framework. Risks scoring above {materiality_threshold} are classified as material \
and subject to enhanced monitoring, quarterly board reporting, and inclusion in the \
Individual Capital Adequacy Assessment Process (ICAAP).

Management Processes (RM-b)
Material climate risks are managed through sector exposure limits, enhanced due-diligence \
triggers for high-carbon counterparties (carbon intensity > {carbon_intensity_threshold} \
tCO₂e/€m revenue), ESG-linked covenants in new originations, and portfolio-level \
decarbonisation targets aligned with the {net_zero_framework} framework.

The Climate Risk Register is reviewed {risk_register_frequency} by {risk_register_owner} \
and escalated to the {board_committee} when aggregate exposures exceed defined thresholds. \
Transition plans submitted by counterparties are assessed against the Paris Agreement \
sectoral pathways using the platform's CSDDD and CSRD Auto-Populate engines.

Integration into ERM (RM-c)
Climate risk is formally embedded in {entity_name}'s Enterprise Risk Management framework \
as a cross-cutting risk driver affecting credit, market, liquidity, and operational risk \
categories. Climate scenario outputs feed directly into the annual ICAAP stress testing \
programme and the Recovery and Resolution Plan (RRP) where applicable. Internal capital models \
incorporate a climate PD multiplier derived from the platform's {climate_factor_model} \
Factor Overlay Engine.
"""

# 5 ──────────────────────── TCFD METRICS AND TARGETS ────────────────────────

TEMPLATE_REGISTRY["TCFD_METRICS_TARGETS"] = """\
METRICS AND TARGETS (TCFD MT-a, MT-b, MT-c)

Climate-Related Metrics (MT-a)
{entity_name} reports the following climate metrics for {reporting_year}:

  • Financed Emissions (PCAF Part A): Scope 1+2 financed emissions total \
    {financed_emissions_s1s2:,.0f} tCO₂e (PCAF Data Quality Score: {pcaf_dqs_avg:.1f}/5). \
    Scope 3 (Category 15 — Investments) are {financed_emissions_s3:,.0f} tCO₂e.
  • WACI: Weighted Average Carbon Intensity of {waci:.1f} tCO₂e / €m revenue across the \
    lending portfolio, a {waci_change:+.1f}% change year-on-year.
  • Climate VaR: Portfolio climate VaR (95%, 2050, Delayed Transition) is \
    {currency}{climate_var:,.0f}, equivalent to {climate_var_pct:.1f}% of total exposure.
  • Green Finance Ratio: {green_finance_ratio:.1f}% of new originations in {reporting_year} \
    classified as taxonomy-aligned or sustainability-linked under EU Taxonomy Regulation \
    Articles 5–8 and the Green Asset Ratio (GAR) framework.
  • Physical Risk Exposure: {pct_high_physical_risk:.1f}% of counterparties by exposure value \
    are classified as high physical risk (score ≥ 7/10) under the platform's spatial hazard model.

GHG Emissions (MT-b)
Own operations (market-based):
  Scope 1: {own_scope1:,.0f} tCO₂e | Scope 2: {own_scope2:,.0f} tCO₂e | \
  Scope 3: {own_scope3:,.0f} tCO₂e
Intensity: {own_ghg_intensity:.2f} tCO₂e / FTE ({reporting_year})

Targets (MT-c)
{entity_name} has committed to the following science-aligned targets:
  1. Net zero financed emissions by {net_zero_year} (absolute Scope 1+2+3, versus {base_year} baseline).
  2. {interim_target_pct}% reduction in WACI by {interim_target_year} (base year {base_year}).
  3. {green_finance_target}% green/sustainable finance share of total new originations \
     by {green_finance_target_year}.
  4. {re_pct}% renewable electricity in own operations by {re_target_year} \
     ({current_re_pct}% achieved in {reporting_year}).

Progress against targets is tracked quarterly by {climate_role} and reported to the \
{board_committee} annually. External assurance is provided by {assurance_provider} \
at the {assurance_level} level in accordance with ISAE 3410.
"""

# 6 ───────────────────────────── SFDR ART.8 ──────────────────────────────────

TEMPLATE_REGISTRY["SFDR_ART8"] = """\
SFDR ARTICLE 8 PERIODIC DISCLOSURE — {fund_name}

This financial product promotes environmental and/or social characteristics within the \
meaning of Article 8 of Regulation (EU) 2019/2088 (SFDR). It does not have as its \
objective a sustainable investment.

Environmental and Social Characteristics Promoted
{fund_name} promotes the following characteristics: {promoted_characteristics}. \
These are measured and monitored through a combination of ESG screening, active engagement, \
and quarterly KPI tracking against the fund's Sustainability Indicators.

Investment Strategy
Investments are selected through a {screening_approach} approach combining \
{exclusion_list} exclusions and a best-in-class ESG integration methodology. \
ESG data is sourced from {esg_data_providers}. Engagement with investees on material \
ESG issues is conducted in accordance with the manager's Stewardship Code obligations.

Proportion of Investments
  • Taxonomy-aligned investments: {taxonomy_aligned_pct:.1f}%
  • Other sustainable investments (environmental): {other_env_pct:.1f}%
  • Other sustainable investments (social): {other_social_pct:.1f}%
  • Investments not meeting sustainable criteria: {not_sustainable_pct:.1f}%

Principal Adverse Impacts (PAI)
The fund considers {pai_count} of the 18 mandatory PAI indicators under SFDR RTS Annex I. \
The most material PAI for this fund is {top_pai_indicator}: \
{top_pai_value} ({top_pai_unit}), representing a {top_pai_change:+.1f}% change \
versus the prior reporting period.

EU Taxonomy Alignment
{taxonomy_aligned_pct:.1f}% of investments are aligned with the EU Taxonomy \
environmental objectives. The Do-No-Significant-Harm (DNSH) assessment was applied \
across all six environmental objectives. {taxonomy_caveat}

Sustainability Indicators
Performance against the fund's Sustainability Indicators in {reporting_year}:
  • {indicator_1_name}: {indicator_1_value} (target: {indicator_1_target})
  • {indicator_2_name}: {indicator_2_value} (target: {indicator_2_target})
  • {indicator_3_name}: {indicator_3_value} (target: {indicator_3_target})
"""

# 7 ───────────────────────────── SFDR ART.9 ──────────────────────────────────

TEMPLATE_REGISTRY["SFDR_ART9"] = """\
SFDR ARTICLE 9 PERIODIC DISCLOSURE — {fund_name}

This financial product has sustainable investment as its objective within the meaning of \
Article 9 of Regulation (EU) 2019/2088 (SFDR).

Sustainable Investment Objective
{fund_name} pursues the following sustainable investment objective: \
{sustainable_investment_objective}. The objective is measured through \
{objective_kpi_name} (current: {objective_kpi_value}; target: {objective_kpi_target} \
by {objective_target_year}).

No Significant Harm Assessment
All investments have been assessed against the Do-No-Significant-Harm (DNSH) criteria \
across all six EU Taxonomy environmental objectives and the UN Guiding Principles on \
Business and Human Rights. {num_holdings_failed_dnsh} holding(s) were found to breach \
DNSH criteria during the reporting period and were divested by {dnsh_remedy_date}.

EU Taxonomy Contribution
{taxonomy_contribution_pct:.1f}% of the fund's investments are directed towards \
EU Taxonomy-aligned economic activities contributing to {taxonomy_objectives}. \
The reference benchmark (where applicable) achieves {benchmark_taxonomy_pct:.1f}% alignment.

Sustainable Investment Proportion
  • Sustainable investments contributing to environmental objectives: {sustainable_env_pct:.1f}%
  • Sustainable investments contributing to social objectives: {sustainable_social_pct:.1f}%
  • Total sustainable investments: {total_sustainable_pct:.1f}%

Principal Adverse Impacts
The fund's investment process explicitly accounts for all 18 mandatory PAI indicators. \
Carbon footprint of the portfolio is {portfolio_carbon_footprint:,.0f} tCO₂e/€m invested, \
{footprint_vs_benchmark:+.1f}% versus the reference benchmark.
"""

# 8 ────────────────────────── CSRD / ESRS E1 ────────────────────────────────

TEMPLATE_REGISTRY["CSRD_ESRS_E1"] = """\
ESRS E1 — CLIMATE CHANGE

E1-1  Transition Plan for Climate Change Mitigation
{entity_name} has adopted a Climate Transition Plan consistent with the Paris Agreement \
1.5°C pathway. The plan covers the period {plan_period} and sets out science-based \
decarbonisation targets for Scope 1, 2 and 3 emissions aligned with the \
{sbti_sector_pathway} sectoral pathway. The plan was approved by the Board on \
{transition_plan_approval_date} and is subject to annual review.

Key milestones:
  • {milestone_1_year}: {milestone_1_description}
  • {milestone_2_year}: {milestone_2_description}
  • Net zero by {net_zero_year} (Scope 1+2+3, base year {base_year})

E1-2  Policies Related to Climate Change Mitigation and Adaptation
{entity_name} maintains a Climate Policy and an Energy Policy reviewed annually by \
{policy_owner}. The Climate Policy sets mandatory requirements for Scope 1 and 2 \
reduction across all owned/controlled operations and Scope 3 Category {top_scope3_category} \
engagement requirements for material suppliers and investees.

E1-3  Actions and Resources Related to Climate Change Policies
Capital expenditure allocated to climate mitigation and adaptation in {reporting_year}: \
{currency}{climate_capex:,.0f} ({climate_capex_pct:.1f}% of total CapEx). Key actions \
undertaken include: {key_actions_list}.

E1-4  Targets Related to Climate Change Mitigation and Adaptation
  Target 1: {target_1_description} — {target_1_progress}% progress (base: {base_year})
  Target 2: {target_2_description} — {target_2_progress}% progress
  Target 3 (adaptation): {target_3_description} — {target_3_progress}% progress

E1-5  Energy Consumption and Mix
Total energy consumption: {total_energy_mwh:,.0f} MWh ({reporting_year})
  Renewable electricity: {re_energy_mwh:,.0f} MWh ({re_pct:.1f}%)
  Fossil fuel consumption: {fossil_energy_mwh:,.0f} MWh ({fossil_pct:.1f}%)
  Energy intensity: {energy_intensity:.2f} MWh / {energy_intensity_denominator}

E1-6  Gross GHG Emissions (ESRS E1-6, GHG Protocol)
  Scope 1: {scope1_gross:,.0f} tCO₂e (biogenic: {scope1_biogenic:,.0f} tCO₂e)
  Scope 2 (market-based): {scope2_market:,.0f} tCO₂e
  Scope 2 (location-based): {scope2_location:,.0f} tCO₂e
  Scope 3 total: {scope3_total:,.0f} tCO₂e
    Category {top_scope3_category} (most material): {top_scope3_value:,.0f} tCO₂e
  GHG intensity: {ghg_intensity:.2f} tCO₂e / {ghg_intensity_denominator}

E1-7  GHG Removals and Carbon Credits
Carbon removals (biogenic/technical): {carbon_removals:,.0f} tCO₂e
Carbon credits used to meet targets: {carbon_credits_used:,.0f} tCO₂e \
(standard: {carbon_credit_standard}; vintage: {carbon_credit_vintage})
Net GHG position: {net_ghg:,.0f} tCO₂e

E1-8  Internal Carbon Pricing
Internal carbon price applied: {currency}{internal_carbon_price}/tCO₂e \
(methodology: {internal_carbon_price_methodology}; \
scope: {internal_carbon_price_scope}; applied since {internal_carbon_price_since})

E1-9  Financial Effects of Climate-Related Risks and Opportunities
Potential financial effects of material climate risks and opportunities:
  Physical risk (medium-term, {medium_horizon}): \
    {currency}{physical_risk_financial_effect:,.0f} \
    ({physical_risk_effect_type}, probability: {physical_risk_probability})
  Transition risk (short-term, {short_horizon}): \
    {currency}{transition_risk_financial_effect:,.0f} \
    ({transition_risk_effect_type})
  Climate opportunity (medium-term): \
    {currency}{climate_opportunity_value:,.0f} ({climate_opportunity_description})
"""

# 9 ─────────────────────── CSRD / ESRS 2 GENERAL ───────────────────────────

TEMPLATE_REGISTRY["CSRD_ESRS_GENERAL"] = """\
ESRS 2 — GENERAL DISCLOSURES

BP-1  General Basis for Preparation
These sustainability disclosures have been prepared in accordance with the European \
Sustainability Reporting Standards (ESRS) as adopted by the European Commission under \
Directive 2013/34/EU as amended by Directive (EU) 2022/2464 (CSRD). The reporting period \
is {reporting_period}. The sustainability statement covers {entity_name} and its \
controlled subsidiaries as defined in the consolidated financial statements. \
Comparative data is presented for {prior_year} where available.

GOV-1  Governance, Role of Administrative, Management and Supervisory Bodies
The {board_committee} has ultimate oversight responsibility for sustainability matters. \
Sustainability performance is a standing agenda item at each Board meeting. \
Executive responsibility rests with {sustainability_executive} ({sustainability_executive_role}), \
supported by the {sustainability_function} function comprising {sustainability_fte} FTEs.

SBM-1  Strategy, Business Model and Value Chain
{entity_name} operates as {business_description}. The entity's value chain encompasses \
{upstream_description} upstream and {downstream_description} downstream. \
Material sustainability impacts, risks and opportunities (IROs) along the value chain \
were identified through the Double Materiality Assessment (DMA) described in SBM-3.

SBM-3  Material IROs and Interaction with Strategy
The DMA was conducted in {dma_year} using a two-dimensional materiality approach: \
impact materiality (actual and potential impacts on people and environment) and \
financial materiality (risks and opportunities that may affect financial performance). \
{num_material_topics} topics were assessed as material. The {num_priority_topics} \
highest-priority topics are: {priority_topics_list}.

Engagement with affected stakeholders was conducted via {stakeholder_engagement_methods} \
covering {stakeholder_groups}. External specialist input was provided by {external_specialist}.
"""

# 10 ──────────────────────── ISSB S2 GOVERNANCE ──────────────────────────────

TEMPLATE_REGISTRY["ISSB_S2_GOVERNANCE"] = """\
IFRS S2 — GOVERNANCE (§6-15)

Governance Body or Individual with Oversight Responsibilities (§6(a))
{entity_name}'s {board_committee} is the governance body responsible for oversight of \
climate-related risks and opportunities. The committee comprises {board_committee_composition}. \
It reviews climate risk reports {board_frequency} and is briefed on material \
developments as they arise. Board members' skills and competencies in relation to \
climate-related matters are assessed annually; {pct_board_climate_competent}% of \
non-executive directors have undertaken climate/sustainability competency training \
in the last two years.

How Climate Considerations are Reflected in Mandate (§6(b))
Climate-related risks and opportunities are addressed in:
  (i)   The entity's Risk Appetite Statement — climate is a standalone risk category \
        with quantitative tolerance limits reviewed annually;
  (ii)  Capital allocation decisions — the Investment Committee applies a mandatory \
        climate risk screen to transactions above {capital_screen_threshold};
  (iii) Remuneration — {remuneration_pct}% of executive variable pay is linked to \
        climate-related KPIs including Scope 1+2 reduction, green finance targets, and \
        WACI improvement.

Management Oversight (§6(c))
The {climate_role} is responsible for day-to-day management of climate risks. \
{climate_role} reports to {cro_title} and to the {board_committee} on a {board_frequency} basis. \
Escalation protocols ensure material climate events are reported to the Board within \
{escalation_timeframe} of identification.
"""

# 11 ──────────────────────── ISSB S2 STRATEGY ────────────────────────────────

TEMPLATE_REGISTRY["ISSB_S2_STRATEGY"] = """\
IFRS S2 — STRATEGY (§16-34)

Climate-Related Risks and Opportunities (§16-21)
{entity_name} identified the following material climate-related risks and opportunities \
for the reporting period, covering the entity's time horizons of \
{short_horizon} (short), {medium_horizon} (medium), and {long_horizon} (long).

Transition risks: {num_transition_risks} material transition risks were identified, \
including: {transition_risks_summary}. The most significant by potential financial \
impact is {top_transition_risk} with an estimated financial effect of \
{currency}{top_transition_risk_impact:,.0f}.

Physical risks: {num_physical_risks} material physical risks were identified across \
{num_jurisdictions} jurisdictions. Acute risk: {top_acute_risk} in {top_acute_risk_location} \
(return period: 1-in-{top_acute_risk_return_period} years; estimated asset damage: \
{currency}{top_acute_damage:,.0f}). Chronic risk: {top_chronic_risk} affecting \
{top_chronic_risk_pct:.0f}% of assets by value.

Climate-related opportunities: {num_opportunities} material opportunities identified, \
primarily in {top_opportunity_area}, with estimated revenue potential of \
{currency}{top_opportunity_revenue:,.0f} by {opportunity_year}.

Scenario Analysis (§22-27)
{entity_name} uses scenario analysis to assess strategy resilience, employing \
{num_scenarios} NGFS-aligned scenarios: {scenario_names}. \
The scenarios span temperature outcomes from {min_temp_scenario}°C to \
{max_temp_scenario}°C by 2100. Time horizons: 2030, 2040, 2050.

Key finding: Under the {most_severe_scenario} scenario, the entity would face additional \
credit provisions of {currency}{max_provision_increase:,.0f} by {provision_horizon} \
({provision_pct:.1f}% of current capital base). Strategy adaptations in response include: \
{strategy_adaptations}.

Transition Plan (§29-34)
See ESRS E1-1 / TCFD STR-c for the full transition plan narrative. \
The plan is consistent with a {temperature_target}°C pathway and covers \
{transition_plan_period}. Financial resources committed to the plan total \
{currency}{transition_plan_budget:,.0f} over the plan period.
"""

# 12 ──────────────────────── ISSB S2 RISK MANAGEMENT ─────────────────────────

TEMPLATE_REGISTRY["ISSB_S2_RISK_MGMT"] = """\
IFRS S2 — RISK MANAGEMENT (§35-38)

Processes to Identify, Assess, Prioritise, and Monitor Climate-Related Risks (§35-36)
{entity_name} applies a structured climate risk identification and assessment process:

  Step 1 — Identification: Climate risks are identified through (i) sector heat-map \
    analysis covering {num_sectors} NACE sectors; (ii) counterparty-level physical and \
    transition risk scoring via the Climate Risk Engine; and (iii) horizon-scanning \
    of regulatory, technology, and market developments.

  Step 2 — Assessment: Each risk is scored on a two-dimensional probability × impact matrix \
    calibrated to the risk appetite framework. Physical risk scores incorporate IPCC AR6 \
    hazard data; transition risk scores incorporate carbon price, technology readiness, \
    and regulatory exposure indices.

  Step 3 — Prioritisation: Risks with a combined score ≥ {materiality_threshold} are \
    classified as material and subject to enhanced monitoring. \
    {num_material_climate_risks} risks are currently classified as material.

  Step 4 — Monitoring: Material risks are reviewed {risk_review_frequency} by \
    {risk_review_body}. Key metrics are monitored in real-time via the platform dashboard. \
    Emerging risks are surfaced through the {horizon_scanning_mechanism} process.

Integration into Overall Risk Management (§37-38)
Climate risk is integrated into {entity_name}'s overall risk management framework as \
a cross-cutting driver of credit, market, operational, and liquidity risks. \
Climate scenario outputs are incorporated into the annual ICAAP stress-testing programme. \
The climate risk register is formally linked to the group-level Principal Risk Register, \
ensuring Board-level visibility.
"""

# 13 ──────────────────────── ISSB S2 METRICS ────────────────────────────────

TEMPLATE_REGISTRY["ISSB_S2_METRICS"] = """\
IFRS S2 — METRICS AND TARGETS (§39-51)

Cross-Industry Metric Categories (§39-44)
Metric Category 1 — GHG Emissions
  Scope 1: {scope1_mtco2e:.2f} MtCO₂e | Scope 2 (market-based): {scope2_mtco2e:.2f} MtCO₂e | \
  Scope 3: {scope3_mtco2e:.2f} MtCO₂e (methodological approach: {ghg_methodology}; \
  consolidation approach: {ghg_consolidation})

Metric Category 2 — Transition Risk
  Internal carbon price: {currency}{internal_carbon_price}/tCO₂e \
  (applied to {carbon_price_coverage}% of Scope 1+2 emissions)

Metric Category 3 — Physical Risk
  Percentage of assets exposed to acute physical risk: {pct_acute_physical_risk:.1f}%
  Percentage of assets exposed to chronic physical risk: {pct_chronic_physical_risk:.1f}%
  Most material hazard: {top_physical_hazard} ({top_hazard_location})

Metric Category 4 — Climate-Related Opportunities
  Climate-related revenue in {reporting_year}: {currency}{green_revenue:,.0f} \
  ({green_revenue_pct:.1f}% of total revenue)

Metric Category 5 — Capital Deployment
  CapEx aligned to climate opportunities: {currency}{climate_capex:,.0f} \
  ({climate_capex_pct:.1f}% of total CapEx)

Metric Category 6 — Internal Carbon Price
  See Metric Category 2.

Industry-Based Metrics (§45-48)
{industry_specific_metrics}

Targets (§49-51)
{entity_name} has set the following climate-related targets:
  Target 1: {target_1_name} — {target_1_value} by {target_1_year} \
    (base year {base_year}; {target_1_progress:.1f}% progress to date)
  Target 2: {target_2_name} — {target_2_value} by {target_2_year} \
    ({target_2_progress:.1f}% progress to date)
  Target 3: {target_3_name} — {target_3_value} by {target_3_year} \
    ({target_3_progress:.1f}% progress to date)

Methodology and assumptions for each target are disclosed in the entity's Climate Data \
Appendix and subject to external limited assurance by {assurance_provider}.
"""

# 14 ──────────────────────── SEC REG S-K ─────────────────────────────────────

TEMPLATE_REGISTRY["SEC_REG_SK"] = """\
SEC CLIMATE-RELATED DISCLOSURES (REGULATION S-K, ITEMS 1501-1505)

Item 1501 — Governance
{entity_name}'s {board_committee} oversees climate-related risks and opportunities. \
{board_climate_expertise_disclosure}. Management climate oversight is exercised by \
{climate_role}. Climate risk oversight is a component of the Board's oversight of \
material risks as described in the proxy statement.

Item 1502 — Strategy, Business Model, and Outlook
{entity_name} has identified climate-related risks that are reasonably likely to have \
a material impact on its business, financial condition, or results of operations. \
{climate_strategy_description}

Time horizons used: Short-term ({short_horizon}); Medium-term ({medium_horizon}); \
Long-term ({long_horizon}).

Material transition risks include: {transition_risks_summary}
Material physical risks include: {physical_risks_summary}

Scenario analysis disclosure: {entity_name} has used climate scenario analysis to assess \
the resilience of its business strategy. {scenario_analysis_disclosure}. \
The safe harbor provisions of Section 27A of the Securities Act and Section 21E of the \
Exchange Act apply to forward-looking statements in this section.

Item 1503 — Risk Management
{entity_name} has adopted processes for identifying, assessing, and managing \
climate-related risks. {risk_management_description}. These processes are integrated into \
the entity's overall enterprise risk management framework.

Item 1504 — Financial Statement Metrics (Reg S-X 14-02)
{financial_statement_climate_effects}

Severe weather and other natural conditions (§14-02(a)):
  Costs incurred in {reporting_year}: {currency}{severe_weather_costs:,.0f}
  (threshold applied: 1% of pre-tax income = {currency}{materiality_threshold_amount:,.0f})

Transition activities (§14-02(b)):
  {transition_activity_disclosure}

Estimates and assumptions (§14-02(c)):
  {climate_estimates_disclosure}

Item 1505 — GHG Emissions (Large Accelerated Filers / Accelerated Filers)
Disclosure requirement applies: {ghg_disclosure_requirement}

  Scope 1 (gross): {scope1_mtco2e:.4f} MtCO₂e
  Scope 2 (gross, market-based): {scope2_mtco2e:.4f} MtCO₂e
  Biogenic CO₂: {biogenic_co2_mtco2e:.4f} MtCO₂e (disclosed separately per §1505(e))

  Organisational boundary: {org_boundary_approach}
  Methodology: {ghg_methodology}
  Attestation: {attestation_level} assurance provided by {attestation_provider} \
    in accordance with {attestation_standard}
"""

# 15 ────────────────────────── GRI 305 EMISSIONS ─────────────────────────────

TEMPLATE_REGISTRY["GRI_305_EMISSIONS"] = """\
GRI 305: EMISSIONS

GRI 305-1  Direct (Scope 1) GHG Emissions
{entity_name} reports gross Scope 1 GHG emissions of {scope1_tco2e:,.0f} tCO₂e \
for {reporting_year} ({prior_year}: {prior_scope1_tco2e:,.0f} tCO₂e; \
change: {scope1_yoy_change:+.1f}%). \
GHGs included: {ghg_included}. \
Sources: {scope1_sources}. \
Biogenic CO₂: {biogenic_co2:,.0f} tCO₂e (reported separately per GRI 305-1(b)).
Consolidation approach: {consolidation_approach}. \
Base year: {base_year} ({base_year_scope1:,.0f} tCO₂e). \
Source of emission factors: {emission_factor_source}.

GRI 305-2  Energy Indirect (Scope 2) GHG Emissions
Market-based: {scope2_market_tco2e:,.0f} tCO₂e \
({prior_year}: {prior_scope2_market:,.0f} tCO₂e; change: {scope2_yoy_change:+.1f}%). \
Location-based: {scope2_location_tco2e:,.0f} tCO₂e. \
Emission factors: {scope2_emission_factor_source}.

GRI 305-3  Other Indirect (Scope 3) GHG Emissions
Scope 3 total: {scope3_total_tco2e:,.0f} tCO₂e.
Relevant categories reported: {scope3_categories_reported}.
Most material category: Category {top_scope3_cat} — {top_scope3_cat_name} \
({top_scope3_tco2e:,.0f} tCO₂e; {top_scope3_pct:.0f}% of Scope 3 total). \
Methodology: {scope3_methodology}. \
Exclusions: {scope3_exclusions}.

GRI 305-4  GHG Emissions Intensity
Ratio: {ghg_intensity_value:.2f} {ghg_intensity_unit}. \
Denominator: {ghg_intensity_denominator}. \
GHGs included: {ghg_included}.

GRI 305-5  Reduction of GHG Emissions
Reductions achieved in {reporting_year}: {scope12_reductions:,.0f} tCO₂e (Scope 1+2). \
Initiatives: {reduction_initiatives}. \
Base year for reductions: {reduction_base_year} ({reduction_base_year_emissions:,.0f} tCO₂e). \
Scope of reductions: {reduction_scope}. \
Calculation method: {reduction_calculation_method}.

GRI 305-6  Emissions of Ozone-Depleting Substances (ODS)
Total ODS: {ods_kg_cfc11eq:.2f} kg CFC-11 equivalent. \
Sources: {ods_sources}.

GRI 305-7  Nitrogen Oxides (NOx), Sulfur Oxides (SOx), and Other Significant Air Emissions
NOx: {nox_tonnes:.1f} tonnes | SOx: {sox_tonnes:.1f} tonnes | \
Persistent Organic Pollutants: {pop_kg:.2f} kg | \
Volatile Organic Compounds: {voc_tonnes:.1f} tonnes | \
Hazardous Air Pollutants: {hap_tonnes:.1f} tonnes.
Standards and methodologies: {air_emissions_methodology}.
"""

# 16 ───────────────────────── BRSR PRINCIPLE 6 ───────────────────────────────

TEMPLATE_REGISTRY["BRSR_PRINCIPLE_6"] = """\
BRSR — PRINCIPLE 6: BUSINESSES SHOULD RESPECT AND MAKE EFFORTS TO PROTECT AND RESTORE
THE ENVIRONMENT

Essential Indicators

6-E-1  Energy Consumed and Intensity
Total energy consumption within the organisation: {total_energy_gj:,.0f} GJ
  Renewable sources: {renewable_energy_gj:,.0f} GJ ({re_pct:.1f}%)
  Non-renewable sources: {non_renewable_energy_gj:,.0f} GJ
Energy intensity per rupee of turnover: {energy_intensity_gj_cr:.4f} GJ/₹ Crore
Energy intensity per unit of physical output: {energy_intensity_per_unit}
External assessment: {energy_external_assessment}

6-E-2  Water Withdrawn and Consumed
Total water withdrawal: {water_withdrawal_kl:,.0f} KL (surface: {water_surface_kl:,.0f}; \
groundwater: {water_ground_kl:,.0f}; third-party: {water_third_party_kl:,.0f})
Total water consumption: {water_consumption_kl:,.0f} KL
Water intensity: {water_intensity:.4f} KL / ₹ Crore turnover
Water discharge: {water_discharge_kl:,.0f} KL (quality: {water_discharge_quality})
External assessment: {water_external_assessment}

6-E-3  Air Emissions (applicable to entities in manufacturing sectors)
NOx: {brsr_nox:.2f} MT | SOx: {brsr_sox:.2f} MT | \
Particulate matter: {brsr_pm:.2f} MT | \
Persistent organic pollutants: {brsr_pop:.4f} MT | \
Volatile organic compounds: {brsr_voc:.2f} MT | \
Hazardous air pollutants: {brsr_hap:.2f} MT | \
Others: {brsr_other_air:.2f} MT
External assessment: {air_external_assessment}

6-E-4  GHG Emissions and Intensity
Scope 1 (tCO₂e): {brsr_scope1:,.0f} | Scope 2 (tCO₂e): {brsr_scope2:,.0f} | \
Scope 3 (tCO₂e, optional): {brsr_scope3:,.0f}
Total Scope 1+2 intensity per rupee turnover: \
{brsr_ghg_intensity_cr:.6f} tCO₂e/₹ Crore
External assessment: {ghg_external_assessment}

BRSR Core — Key ESG Attributes (Annexure I, SEBI Circular 2023)
C7-P6-E1 (Water Intensity): {brsr_core_water_intensity} KL/₹ Crore
C8-P6-E2 (GHG Intensity, Scope 1+2): {brsr_core_ghg_intensity} tCO₂e/₹ Crore
C9-P6-E3 (Hazardous Waste Intensity): {brsr_core_hazwaste_intensity} MT/₹ Crore
Leadership Indicator L6-1 (Biodiversity Impact Assessment): \
{biodiversity_assessment_conducted}
"""

# 17 ──────────────────────── CARBON CALCULATOR ───────────────────────────────

TEMPLATE_REGISTRY["CARBON_CALCULATOR"] = """\
CARBON CALCULATOR — EXECUTIVE SUMMARY

Assessment Period: {reporting_year}
Entity / Portfolio: {entity_name}
Methodology: GHG Protocol Corporate Standard (2015 revision); Scope 3 per ISO 14064-3

Scope 1 — Direct Emissions
Total Scope 1: {scope1_tco2e:,.0f} tCO₂e
Primary sources: {scope1_primary_sources}
Year-on-year change: {scope1_yoy:+.1f}%

Scope 2 — Indirect Energy Emissions
Market-based: {scope2_market_tco2e:,.0f} tCO₂e | Location-based: {scope2_location_tco2e:,.0f} tCO₂e
Renewable energy certificates (RECs): {rec_mwh:,.0f} MWh
Power Purchase Agreements (PPAs): {ppa_mwh:,.0f} MWh

Scope 3 — Value Chain Emissions
Total Scope 3: {scope3_total_tco2e:,.0f} tCO₂e ({scope3_categories_count} categories)
Most material categories:
  {scope3_cat1_name} (Cat {scope3_cat1_num}): {scope3_cat1_tco2e:,.0f} tCO₂e
  {scope3_cat2_name} (Cat {scope3_cat2_num}): {scope3_cat2_tco2e:,.0f} tCO₂e
  {scope3_cat3_name} (Cat {scope3_cat3_num}): {scope3_cat3_tco2e:,.0f} tCO₂e

Total GHG Footprint: {total_tco2e:,.0f} tCO₂e
Carbon Intensity: {carbon_intensity:.2f} tCO₂e / {intensity_denominator}
SBTi Alignment Gap (vs. {sbti_pathway} pathway): {sbti_gap:+,.0f} tCO₂e \
({sbti_gap_pct:+.1f}% above/below target)

Reduction Actions Implemented in {reporting_year}:
{reduction_actions_list}

Verified by: {verification_body} | Standard: {verification_standard} | \
Level: {verification_level}
"""

# 18 ──────────────────────── NATURE RISK / TNFD LEAP ────────────────────────

TEMPLATE_REGISTRY["NATURE_RISK_LEAP"] = """\
TNFD LEAP ASSESSMENT — NATURE-RELATED RISKS AND OPPORTUNITIES

Entity: {entity_name} | Sector: {sector} | Reporting Period: {reporting_period}
TNFD Phase: {tnfd_leap_phase}

L — Locate: Interface with Nature
{entity_name}'s operations and supply chains interface with nature across {num_locations} \
locations in {num_countries} countries. Using the IBAT and ENCORE tools, \
{num_sensitive_locations} locations have been identified as adjacent to or within \
{sensitive_ecosystem_types} ecosystems. Key biomes represented: {key_biomes}. \
High-biodiversity value areas within 10km of operations: {hbv_areas_count} \
(covering approximately {hbv_total_area_km2:,.0f} km²).

E — Evaluate: Sensitivity and Current State of Nature
Material dependencies on nature: {material_dependencies}. \
Ecosystem services at risk: {ecosystem_services_at_risk}. \
Physical risk exposure score: {physical_risk_exposure}/100. \
Transition risk exposure score (regulatory, market, reputational): {transition_risk_exposure}/100.

Biodiversity Net Gain (BNG) position: {bng_position} habitat units \
({bng_direction} relative to {base_year} baseline). \
Key biodiversity indicators: species richness index {species_richness_index}; \
habitat connectivity {habitat_connectivity_score}/10.

A — Assess: Dependencies, Impacts, Risks and Opportunities
Material nature-related risks identified:
  • {risk_1_name}: {risk_1_description} (financial impact estimate: \
    {currency}{risk_1_impact:,.0f}; timeframe: {risk_1_timeframe})
  • {risk_2_name}: {risk_2_description} (financial impact estimate: \
    {currency}{risk_2_impact:,.0f}; timeframe: {risk_2_timeframe})
  • {risk_3_name}: {risk_3_description}

Material nature-related opportunities:
  • {opportunity_1_name}: {opportunity_1_description} \
    (estimated value: {currency}{opportunity_1_value:,.0f})

P — Prepare: Response Strategy and Reporting
Nature commitments: {nature_commitments}.
Biodiversity Action Plan: {bap_status} (target: {bap_target}).
Engagement with {engagement_bodies}: {engagement_description}.
External verification: {nature_verification}.
Alignment with: {nature_frameworks_alignment}.
"""

# 19 ──────────────────────── STRANDED ASSET ──────────────────────────────────

TEMPLATE_REGISTRY["STRANDED_ASSET"] = """\
STRANDED ASSET ANALYSIS — EXECUTIVE SUMMARY

Portfolio / Asset Class: {asset_class} | Analysis Date: {analysis_date}
Scenario: {scenario_name} | Temperature Pathway: {temperature_pathway}°C by 2100

Overview
{entity_name}'s {asset_class} portfolio contains {num_assets} assets with total book value \
of {currency}{total_book_value:,.0f}. Under the {scenario_name} scenario, \
{num_stranded_assets} assets ({stranded_pct:.1f}% of portfolio count; \
{currency}{stranded_book_value:,.0f} book value) are assessed as exposed to material \
stranding risk within the analysis horizon to {analysis_horizon}.

Key Stranding Drivers
  1. Carbon price exposure: {num_carbon_price_stranded} assets have \
     emissions-intensity above the shadow carbon price break-even threshold \
     of {shadow_carbon_price} {currency}/tCO₂e in 2035.
  2. Technology disruption: {num_tech_stranded} assets face >50% probability of \
     market share loss to {disrupting_technology} by {tech_disruption_year}.
  3. Policy risk: {num_policy_stranded} assets in sectors subject to \
     phase-out or mandatory retirement mandates ({policy_mandate_description}).
  4. Physical risk: {num_physical_stranded} assets face repair costs exceeding \
     {physical_threshold_pct:.0f}% of replacement value by {physical_risk_year} under \
     the {physical_scenario} physical scenario.

Financial Impact
Expected write-down under central scenario ({scenario_name}):
  {currency}{expected_writedown:,.0f} ({writedown_pct:.1f}% of total book value)
  Range across scenarios: {currency}{min_writedown:,.0f} to {currency}{max_writedown:,.0f}
Remaining useful life impact: weighted average remaining useful life reduced from \
{original_useful_life:.1f} to {adjusted_useful_life:.1f} years.

Recommended Actions
  • Prioritise transition planning for the {top_at_risk_sector} sector \
    ({top_sector_stranded_count} assets, {currency}{top_sector_writedown:,.0f} at risk).
  • Initiate carbon abatement retrofits for {retrofit_candidate_count} assets \
    where IRR of abatement exceeds {hurdle_rate:.1f}%.
  • Refinancing timeline: {refinancing_recommendation}.
"""

# 20 ────────────────────────── EU ETS / GAR ─────────────────────────────────

TEMPLATE_REGISTRY["GAR_ETS"] = """\
EU ETS / GREEN ASSET RATIO — REGULATORY DISCLOSURE

EU ETS Compliance Summary
Installation: {installation_id} | Operator: {operator_name} | Sector: {sector}
Reporting Period: {reporting_year} | Regulator: {competent_authority}

Free Allocation (Art. 10a, ETS Directive 2003/87/EC as amended)
Historical Activity Level (HAL): {hal:,.0f} t/yr product output
Benchmark: {benchmark_name} ({benchmark_value:.4f} tCO₂/t product)
Carbon Leakage Annex exposure: {carbon_leakage_factor:.2%}
Preliminary free allocation: {preliminary_allocation:,.0f} EUAs
Cross-Sectoral Correction Factor (CSCF) applied: {cscf_applied}
Final free allocation: {final_allocation:,.0f} EUAs

ETS Compliance
Verified emissions: {verified_emissions:,.0f} tCO₂e (verification body: {verifier})
Allocated EUAs: {allocated_euas:,.0f}
Purchased / Sold EUAs: {market_euas:,.0f}
Surrendered: {surrendered_euas:,.0f}
Surplus / (Deficit): {eua_balance:,.0f} EUAs \
({'SURPLUS' if {eua_balance} >= 0 else 'DEFICIT'})
Estimated compliance cost: {currency}{compliance_cost:,.0f} \
(EUA price assumption: {currency}{eua_price}/EUA)

ETS 2 Readiness Assessment
Phase-in eligibility: Fuel/building supplier — {ets2_eligible}
Projected ETS 2 obligation from {ets2_start_year}: {ets2_scope_description}
Preparedness score: {ets2_readiness_score}/100 ({ets2_readiness_category})
Key gaps: {ets2_gaps}

Green Asset Ratio (EBA Pillar 3 ESG Disclosures, Art. 449a CRR)
Taxonomy-eligible assets: {taxonomy_eligible_pct:.1f}% of total covered assets
Taxonomy-aligned assets: {taxonomy_aligned_pct:.1f}% of total covered assets
Green Asset Ratio (GAR): {gar_pct:.2f}%
Banking Book Taxonomy Alignment Ratio (BTAR): {btar_pct:.2f}%
KPI on fees and commissions (on-balance sheet): {kpi_fees_pct:.2f}%
"""


# ---------------------------------------------------------------------------
# Convenience: list of all available templates
# ---------------------------------------------------------------------------

ALL_TEMPLATE_KEYS: list[str] = list(TEMPLATE_REGISTRY.keys())
