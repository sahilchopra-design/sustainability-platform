"""
Regulatory Report Compiler
=============================
Generates structured regulatory report outputs from platform module data.
Each framework produces a compliance-ready disclosure document structure
that can be rendered to PDF, XBRL, or JSON.

Supported Frameworks:
  1. SFDR — Periodic Disclosure (Annex III / IV / V), PAI Statement
  2. TCFD — 11 Recommended Disclosures (Governance, Strategy, Risk Mgmt, Metrics & Targets)
  3. CSRD / ESRS — Double-materiality structured report (ESRS 2 + topical E1-E5, S1, G1)
  4. ISSB — IFRS S1 General + S2 Climate disclosures
  5. SEC — Climate-Related Disclosures (§§229.1500-1507, Reg S-K)
  6. GRI 305 — Emissions reporting (305-1 through 305-7)
  7. UK TCFD — FCA PS21/24 mandatory climate disclosures
  8. APRA CPG 229 — Prudential Practice Guide: Climate Change Financial Risks
  9. BRSR — SEBI Business Responsibility and Sustainability Report (NGRBC 9 Principles)
 10. BRSR Core — 9 Key ESG Attributes with quantitative KPIs (SEBI Annexure I)

References:
  - SFDR Delegated Regulation (EU) 2022/1288, RTS Annexes
  - TCFD Final Report (June 2017), Annex: Implementation Guidance
  - EFRAG ESRS Set 1 (2023), ESRS 2 General Disclosures
  - IFRS S1 (2023), IFRS S2 (2023) — ISSB Standards
  - SEC Release 33-11275 (March 2024) — Climate-Related Disclosures
  - GRI 305: Emissions 2016 (updated 2020)
  - FCA PS21/24 — Climate-related disclosure (TCFD-aligned)
  - APRA CPG 229 — Climate Change Financial Risks (Nov 2021)
  - SEBI Circular SEBI/HO/CFD/CMD-2/P/CIR/2023/18 (BRSR Core)
  - SEBI BRSR Framework (Annexure I: BRSR Core, Annexure II: Updated BRSR)
  - SEBI BRSR-GRI Linkage Document (2023)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Optional


# ---------------------------------------------------------------------------
# TCFD — 11 Recommended Disclosures Structure
# ---------------------------------------------------------------------------

TCFD_RECOMMENDATIONS: list[dict] = [
    # Governance
    {"id": "GOV-a", "pillar": "Governance",
     "recommendation": "Board oversight of climate-related risks and opportunities",
     "guidance": ["Processes by which the board is informed", "Frequency of board briefings",
                  "Whether board considers climate in strategy, risk policy, budgets"]},
    {"id": "GOV-b", "pillar": "Governance",
     "recommendation": "Management's role in assessing and managing climate risks",
     "guidance": ["Organisational structure for climate risk management",
                  "Processes by which management is informed", "How management monitors"]},
    # Strategy
    {"id": "STR-a", "pillar": "Strategy",
     "recommendation": "Climate-related risks and opportunities identified over short/medium/long term",
     "guidance": ["Description of risks and opportunities by time horizon",
                  "Specific climate risks: physical and transition"]},
    {"id": "STR-b", "pillar": "Strategy",
     "recommendation": "Impact on business, strategy, and financial planning",
     "guidance": ["How identified risks/opportunities impact business",
                  "Impact on products/services, supply chain, adaptation, R&D, operations"]},
    {"id": "STR-c", "pillar": "Strategy",
     "recommendation": "Resilience under different climate scenarios (including 2C or lower)",
     "guidance": ["Results of scenario analysis", "Scenarios used",
                  "Time horizons", "Resilience of strategy"]},
    # Risk Management
    {"id": "RM-a", "pillar": "Risk Management",
     "recommendation": "Processes for identifying and assessing climate-related risks",
     "guidance": ["Risk management processes for climate", "How materiality is determined",
                  "Existing/emerging regulatory requirements considered"]},
    {"id": "RM-b", "pillar": "Risk Management",
     "recommendation": "Processes for managing climate-related risks",
     "guidance": ["How decisions to mitigate, transfer, accept, or control are made",
                  "How risks are prioritised"]},
    {"id": "RM-c", "pillar": "Risk Management",
     "recommendation": "Integration into overall risk management",
     "guidance": ["How climate processes are integrated into overall ERM framework"]},
    # Metrics & Targets
    {"id": "MT-a", "pillar": "Metrics & Targets",
     "recommendation": "Metrics used to assess climate risks and opportunities",
     "guidance": ["Climate-related metrics aligned with strategy and risk mgmt",
                  "Scope 1, 2, 3 GHG emissions", "Related risks"]},
    {"id": "MT-b", "pillar": "Metrics & Targets",
     "recommendation": "Scope 1, Scope 2, and Scope 3 GHG emissions",
     "guidance": ["GHG emissions per GHG Protocol", "Methodologies used",
                  "Intensity metrics"]},
    {"id": "MT-c", "pillar": "Metrics & Targets",
     "recommendation": "Targets used to manage climate risks and performance against targets",
     "guidance": ["Climate targets including GHG", "Time frames",
                  "Base year", "Performance against targets"]},
]


# ---------------------------------------------------------------------------
# SFDR PAI — 14 Mandatory Indicators
# ---------------------------------------------------------------------------

SFDR_MANDATORY_PAI: list[dict] = [
    {"pai_id": 1,  "indicator": "GHG emissions",
     "metric": "Scope 1 GHG emissions", "unit": "tCO2e", "category": "climate"},
    {"pai_id": 1,  "indicator": "GHG emissions",
     "metric": "Scope 2 GHG emissions", "unit": "tCO2e", "category": "climate"},
    {"pai_id": 1,  "indicator": "GHG emissions",
     "metric": "Scope 3 GHG emissions", "unit": "tCO2e", "category": "climate"},
    {"pai_id": 1,  "indicator": "GHG emissions",
     "metric": "Total GHG emissions", "unit": "tCO2e", "category": "climate"},
    {"pai_id": 2,  "indicator": "Carbon footprint",
     "metric": "Carbon footprint", "unit": "tCO2e/EUR M invested", "category": "climate"},
    {"pai_id": 3,  "indicator": "GHG intensity of investee companies",
     "metric": "GHG intensity", "unit": "tCO2e/EUR M revenue", "category": "climate"},
    {"pai_id": 4,  "indicator": "Exposure to companies active in fossil fuel sector",
     "metric": "Share of investments in fossil fuels", "unit": "%", "category": "climate"},
    {"pai_id": 5,  "indicator": "Share of non-renewable energy consumption and production",
     "metric": "Non-renewable energy share", "unit": "%", "category": "climate"},
    {"pai_id": 6,  "indicator": "Energy consumption intensity per high impact climate sector",
     "metric": "Energy intensity (GWh/EUR M revenue)", "unit": "GWh/EUR M", "category": "climate"},
    {"pai_id": 7,  "indicator": "Activities negatively affecting biodiversity-sensitive areas",
     "metric": "Share of investments near or in biodiversity-sensitive areas", "unit": "%", "category": "biodiversity"},
    {"pai_id": 8,  "indicator": "Emissions to water",
     "metric": "Tonnes of emissions to water", "unit": "tonnes", "category": "water"},
    {"pai_id": 9,  "indicator": "Hazardous waste and radioactive waste ratio",
     "metric": "Tonnes of hazardous waste generated", "unit": "tonnes", "category": "waste"},
    {"pai_id": 10, "indicator": "Violations of UN Global Compact / OECD Guidelines",
     "metric": "Share of investments in violating companies", "unit": "%", "category": "social"},
    {"pai_id": 11, "indicator": "Lack of processes/compliance to monitor UNGC/OECD",
     "metric": "Share without monitoring mechanisms", "unit": "%", "category": "social"},
    {"pai_id": 12, "indicator": "Unadjusted gender pay gap",
     "metric": "Average unadjusted gender pay gap", "unit": "%", "category": "social"},
    {"pai_id": 13, "indicator": "Board gender diversity",
     "metric": "Average ratio of female to male board members", "unit": "%", "category": "governance"},
    {"pai_id": 14, "indicator": "Exposure to controversial weapons",
     "metric": "Share in controversial weapons (anti-personnel mines, cluster munitions, etc.)",
     "unit": "%", "category": "social"},
]


# ---------------------------------------------------------------------------
# GRI 305 — Emissions Disclosures
# ---------------------------------------------------------------------------

GRI_305_DISCLOSURES: list[dict] = [
    {"id": "305-1", "title": "Direct (Scope 1) GHG emissions",
     "required_fields": ["gross_scope1_tco2e", "gases_included", "biogenic_tco2e",
                         "base_year", "source_ef", "consolidation_approach", "standards_used"]},
    {"id": "305-2", "title": "Energy indirect (Scope 2) GHG emissions",
     "required_fields": ["gross_scope2_location_tco2e", "gross_scope2_market_tco2e",
                         "gases_included", "base_year", "source_ef", "standards_used"]},
    {"id": "305-3", "title": "Other indirect (Scope 3) GHG emissions",
     "required_fields": ["gross_scope3_tco2e", "categories_included", "biogenic_tco2e",
                         "gases_included", "base_year", "source_ef", "standards_used"]},
    {"id": "305-4", "title": "GHG emissions intensity",
     "required_fields": ["intensity_ratio", "denominator_metric", "gases_included",
                         "scopes_included"]},
    {"id": "305-5", "title": "Reduction of GHG emissions",
     "required_fields": ["reductions_tco2e", "gases_included", "base_year",
                         "scopes_included", "standards_used"]},
    {"id": "305-6", "title": "Emissions of ozone-depleting substances (ODS)",
     "required_fields": ["ods_tonnes_cfc11eq", "substances_included",
                         "source_ef", "standards_used"]},
    {"id": "305-7", "title": "Nitrogen oxides, sulphur oxides, and other significant air emissions",
     "required_fields": ["nox_tonnes", "sox_tonnes", "pops_tonnes",
                         "voc_tonnes", "hap_tonnes", "pm_tonnes", "standards_used"]},
]


# ---------------------------------------------------------------------------
# SEC Climate Disclosure — Reg S-K Subpart 1500
# ---------------------------------------------------------------------------

SEC_CLIMATE_ITEMS: list[dict] = [
    {"item": "1502", "title": "Governance — Board oversight and management role",
     "required": ["board_oversight_description", "management_role_description",
                  "relevant_expertise_description", "frequency_of_oversight"]},
    {"item": "1503", "title": "Strategy — Material climate-related risks",
     "required": ["identified_risks", "material_impact_description",
                  "time_horizons", "actual_material_expenditures"]},
    {"item": "1504", "title": "Strategy — Scenario analysis (if used)",
     "required": ["scenarios_description", "parameters_used",
                  "resilience_assessment", "financial_impacts_quantified"]},
    {"item": "1505", "title": "Risk management processes",
     "required": ["identification_assessment_process", "management_process",
                  "integration_with_overall_risk_mgmt"]},
    {"item": "1506", "title": "Metrics — Scope 1 and Scope 2 emissions",
     "required": ["scope1_tco2e", "scope2_tco2e", "methodology",
                  "intensity_metric", "assurance_status"]},
    {"item": "1507", "title": "Targets and transition plan (if adopted)",
     "required": ["target_description", "target_scope", "target_year",
                  "base_year", "progress_towards_target", "material_expenditures_planned"]},
]


# ---------------------------------------------------------------------------
# APRA CPG 229 Sections
# ---------------------------------------------------------------------------

APRA_CPG229_SECTIONS: list[dict] = [
    {"section": "Governance", "paragraphs": "14-21",
     "requirements": ["Board-level accountability for climate risk",
                      "Management reporting lines for climate risk",
                      "Integration into existing risk appetite framework"]},
    {"section": "Risk Management Framework", "paragraphs": "22-36",
     "requirements": ["Climate risk identification (physical + transition)",
                      "Scenario analysis across multiple warming pathways",
                      "Quantification of financial impacts"]},
    {"section": "Disclosure", "paragraphs": "37-45",
     "requirements": ["TCFD-aligned disclosures",
                      "Scenario analysis results disclosure",
                      "Metrics and targets for climate risk management"]},
    {"section": "Capital Adequacy (Pillar 2)", "paragraphs": "46-52",
     "requirements": ["Climate risk in ICAAP/ORSA",
                      "Stress testing under climate scenarios",
                      "Capital buffer considerations for climate risk"]},
]


# ---------------------------------------------------------------------------
# SEBI BRSR — 9 NGRBC Principles (Section C)
# ---------------------------------------------------------------------------

BRSR_PRINCIPLES: list[dict] = [
    {
        "id": "P1", "principle": "Businesses should conduct and govern themselves with integrity and in a manner that is ethical, transparent and accountable",
        "essential_indicators": [
            "Percentage coverage of training on ethics/values/anti-corruption by category",
            "Details of fines/penalties paid in proceedings with regulators/courts/tribunals",
            "Complaints on anti-competitive conduct or conflict of interest",
            "Details of disciplinary action taken against directors/KMPs for anti-corruption/bribery",
            "Number of days of accounts payable",
        ],
        "leadership_indicators": [
            "Awareness programmes conducted for value chain partners on ethical business conduct",
            "Details of conflict of interest disclosures by directors",
        ],
        "gri_mappings": ["GRI 2: General Disclosures 2021", "GRI 205: Anti-corruption 2016"],
        "esrs_mappings": ["ESRS G1: Business Conduct"],
    },
    {
        "id": "P2", "principle": "Businesses should provide goods and services in a manner that is sustainable and safe",
        "essential_indicators": [
            "Percentage of R&D and capex investments in specific technologies to improve ESG impacts",
            "Sustainable sourcing as a percentage of inputs",
            "Procedures to safely reclaim products for reuse/recycling/safe disposal",
            "EPR applicability and waste collection/recycling plan",
        ],
        "leadership_indicators": [
            "Percentage of recycled/reused input material to total material (by value)",
            "Products with reduced environmental/social impacts - reclaim percentage",
            "Lifecycle perspective / assessments for products",
        ],
        "gri_mappings": ["GRI 301: Materials 2016", "GRI 306: Waste 2020", "GRI 308: Supplier Environmental Assessment 2016", "GRI 414: Supplier Social Assessment 2016"],
        "esrs_mappings": ["ESRS E5: Resource Use and Circular Economy", "ESRS S2: Workers in the Value Chain"],
    },
    {
        "id": "P3", "principle": "Businesses should respect and promote the well-being of all employees, including those in their value chains",
        "essential_indicators": [
            "Details of measures for well-being of employees and workers (health insurance, maternity, PF, etc.)",
            "Details of retirement benefits (PF, gratuity, ESI) — coverage for employees and workers",
            "Accessibility of workplaces — accessible for differently abled employees and workers",
            "Equal Opportunity Policy disclosure",
            "Return to work and retention rates of permanent employees/workers after parental leave",
            "Grievance redressal mechanism — complaints filed and resolved (sexual harassment, discrimination, child labour, forced labour, wages, other)",
            "Membership of employees and workers in association(s) or union(s) recognised by management",
            "Training details — health and safety measures, skill upgradation (total hours, % of employees/workers)",
            "Performance and career development reviews",
            "Health and safety management system details, coverage, number of fatalities, reportable injuries/diseases",
        ],
        "leadership_indicators": [
            "Life insurance or disability cover for employees and workers with breakdown",
            "Measures to ensure safe and healthy workplace for value chain partners",
            "Transition assistance programmes to facilitate continued employability",
            "Assessment of value chain partners on health and safety practices",
        ],
        "gri_mappings": ["GRI 401: Employment 2016", "GRI 403: Occupational Health and Safety 2018", "GRI 404: Training and Education 2016"],
        "esrs_mappings": ["ESRS S1: Own Workforce"],
    },
    {
        "id": "P4", "principle": "Businesses should respect the interests of and be responsive to all its stakeholders",
        "essential_indicators": [
            "Describe the processes for identifying key stakeholder groups of the entity",
            "Key stakeholder groups and channels of communication",
            "Key topics and concerns raised by stakeholders and entity response",
        ],
        "leadership_indicators": [
            "Processes for consultation between stakeholders and board on ESG issues",
            "Whether stakeholder consultation is used to support decision-making on ESG topics",
        ],
        "gri_mappings": ["GRI 2: General Disclosures 2021", "GRI 3: Material Topics 2021"],
        "esrs_mappings": ["ESRS 2: General Disclosures", "ESRS S1: Own Workforce", "ESRS S2: Workers in the Value Chain", "ESRS S3: Affected Communities", "ESRS S4: Consumers and End-users"],
    },
    {
        "id": "P5", "principle": "Businesses should respect and promote human rights",
        "essential_indicators": [
            "Number of training and awareness programmes on human rights issues (employees, workers)",
            "Details of minimum wages paid — equal to or exceeding minimum wage requirements",
            "Details of remuneration/salary/wages — median remuneration and wage breakdowns",
            "Focal point or committee responsible for addressing human rights impacts",
            "Grievance redressal mechanism for human rights — sexual harassment, discrimination, child/forced labour",
            "Number of complaints on human rights issues filed, pending, resolved — POSH, discrimination, child/forced labour, wages",
            "Mechanisms to prevent adverse consequences to complainants (protection of whistle-blowers)",
            "Human rights requirements in business agreements and contracts",
            "Assessment results of plants/offices for child labour, forced/involuntary labour, sexual harassment, discrimination, wages",
        ],
        "leadership_indicators": [
            "Details of scope and coverage of human rights due diligence",
            "Is the premise/office of the entity accessible to differently abled visitors",
            "Assessment of value chain partners on human rights",
            "Corrective actions taken for any human rights issue by entity/value chain/other party",
        ],
        "gri_mappings": ["GRI 202: Market Presence 2016", "GRI 405: Diversity and Equal Opportunity 2016",
                         "GRI 406: Non-discrimination 2016", "GRI 410: Security Practices 2016",
                         "GRI 414: Supplier Social Assessment 2016"],
        "esrs_mappings": ["ESRS S1: Own Workforce", "ESRS S2: Workers in the Value Chain", "ESRS S3: Affected Communities"],
    },
    {
        "id": "P6", "principle": "Businesses should respect and make efforts to protect and restore the environment",
        "essential_indicators": [
            "Details of total energy consumption and energy intensity (total, from renewable, non-renewable sources)",
            "Does the entity have any sites/facilities identified as designated consumers under PAT Scheme?",
            "Details of disclosure of Scope 1 and Scope 2 emissions & intensity",
            "Details of Scope 1 and Scope 2 emissions intensity — base year, current year, reduction achieved",
            "Does the entity have any project related to reducing GHG emissions — if yes, details",
            "Details of total Scope 3 emissions & intensity — base year and current year",
            "Details of total water withdrawal by source (surface, groundwater, third party, seawater, other)",
            "Details of total water consumption, intensity, discharged (with treatment level and destination)",
            "Has the entity implemented a mechanism for Zero Liquid Discharge?",
            "Details of air emissions other than GHG (NOx, SOx, PM, others) and whether within permissible limits",
            "Details of greenhouse gas emissions (Scope 1 and Scope 2) and intensity",
            "Details of waste generated, recovered/recycled/reused, safely disposed (hazardous, non-hazardous, plastic, e-waste, bio-medical, construction, battery, radioactive, other)",
            "Waste intensity (total waste per unit of turnover)",
            "Is the entity compliant with applicable environmental laws? If not, corrective actions taken",
            "Details of EIA/EMP for any project — public hearing conducted and outcome",
            "Details of biodiversity-related disclosures — proximity to ecologically sensitive areas",
        ],
        "leadership_indicators": [
            "Details of energy conservation initiatives and their outcomes",
            "Lifecycle assessments for products undertaken — details and significant social/environmental concerns",
            "Percentage of value chain partners screened on environmental criteria",
            "Details of significant direct/indirect impact on biodiversity and steps taken to mitigate",
            "Breakdown of total energy consumed from renewable/non-renewable sources",
            "Water discharge by destination and treatment level",
            "Water withdrawn, consumed, discharged in areas of water stress",
            "Scope 3 emissions (upstream and downstream) — details of significant Scope 3 categories",
        ],
        "gri_mappings": ["GRI 302: Energy 2016", "GRI 303: Water and Effluents 2018",
                         "GRI 304: Biodiversity 2016", "GRI 305: Emissions 2016",
                         "GRI 306: Waste 2020", "GRI 308: Supplier Environmental Assessment 2016"],
        "esrs_mappings": ["ESRS E1: Climate Change", "ESRS E2: Pollution", "ESRS E3: Water and Marine Resources",
                          "ESRS E4: Biodiversity and Ecosystems", "ESRS E5: Resource Use and Circular Economy"],
    },
    {
        "id": "P7", "principle": "Businesses, when engaging in influencing public and regulatory policy, should do so in a manner that is responsible and transparent",
        "essential_indicators": [
            "Affiliations with trade and industry chambers/associations — top 10 by fees paid",
            "Details of corrective actions or policy advocacy undertaken on any unethical/corrupt practice",
            "Details of public policy positions advocated — topic, methods, frequency, proposed changes",
        ],
        "leadership_indicators": [
            "Details of public policy advocacy through trade associations — position supported by entity",
        ],
        "gri_mappings": ["GRI 206: Anti-competitive Behavior 2016", "GRI 415: Public Policy 2016"],
        "esrs_mappings": ["ESRS G1: Business Conduct"],
    },
    {
        "id": "P8", "principle": "Businesses should promote inclusive growth and equitable development",
        "essential_indicators": [
            "Details of Social Impact Assessments (SIA) and Rehabilitation & Resettlement",
            "Information on project(s) for which ongoing Rehabilitation and Resettlement (R&R) is being implemented",
            "Describe the mechanisms to receive and redress grievances of the community",
            "Percentage of input material sourced from MSMEs/small producers, with % from within the district/state",
            "Job creation in smaller towns — wages paid to persons employed in smaller towns as a % of total wages",
            "CSR details — % of net profit, amount spent, eligibility of CSR applicability",
            "Details of beneficiaries of CSR projects",
        ],
        "leadership_indicators": [
            "Details of actions taken to mitigate negative social impacts identified in SIA",
            "Details of CSR projects undertaken in aspirational districts — amount and beneficiaries",
            "Details of the preferential procurement policy from marginalized/vulnerable groups",
            "Details of corrective actions taken on adverse order from Intellectual Property Appellate Board or Competition Commission",
        ],
        "gri_mappings": ["GRI 204: Procurement Practices 2016", "GRI 413: Local Communities 2016"],
        "esrs_mappings": ["ESRS S3: Affected Communities"],
    },
    {
        "id": "P9", "principle": "Businesses should engage with and provide value to their consumers in a responsible manner",
        "essential_indicators": [
            "Describe mechanisms in place to receive and respond to consumer complaints",
            "Turnover of products/services as a percentage of turnover from all products/services that carry information about environmental/social parameters, safe/responsible usage, recycling",
            "Number of consumer complaints — data privacy, advertising, cyber-security, delivery of essential services, restrictive trade practices, unfair trade practices, other — filed, pending, resolved",
            "Details of instances of product recalls on safety/health/environment grounds",
            "Does the entity have a framework/policy on cyber security and data privacy — if yes, provide details",
            "Details of corrective actions taken or underway on issues relating to advertising, delivery of essential services — from regulatory authorities",
        ],
        "leadership_indicators": [
            "Channels/platforms/mechanisms for consumers to provide feedback",
            "Percentage of consumer satisfaction/NPS survey data",
            "Details of instances of data breaches along with impact and corrective actions",
        ],
        "gri_mappings": ["GRI 416: Customer Health and Safety 2016", "GRI 417: Marketing and Labeling 2016",
                         "GRI 418: Customer Privacy 2016"],
        "esrs_mappings": ["ESRS S4: Consumers and End-users"],
    },
]


# ---------------------------------------------------------------------------
# BRSR Core — 9 Key ESG Attributes (SEBI Annexure I)
# ---------------------------------------------------------------------------

BRSR_CORE_ATTRIBUTES: list[dict] = [
    {
        "id": "CORE-1", "attribute": "GHG Footprint",
        "parameters": ["scope1_tco2e", "scope2_tco2e", "total_scope1_scope2_tco2e",
                        "ghg_intensity_per_turnover", "ghg_intensity_per_output"],
        "measurement": "tCO2e; intensity ratios per INR Cr turnover or per unit output",
        "assurance": "Reasonable assurance on Scope 1 + 2; Limited assurance initially acceptable",
        "gri_mappings": ["GRI 305-1", "GRI 305-2", "GRI 305-4"],
        "esrs_mappings": ["ESRS E1-6 (Scope 1)", "ESRS E1-6 (Scope 2)", "ESRS E1-6 (GHG intensity)"],
        "brsr_principle": "P6",
    },
    {
        "id": "CORE-2", "attribute": "Water Footprint",
        "parameters": ["total_water_consumption_kl", "water_intensity_per_turnover",
                        "water_intensity_per_output", "water_discharge_kl", "water_recycled_pct"],
        "measurement": "KL; intensity ratios per INR Cr turnover or per unit output",
        "assurance": "Reasonable assurance required",
        "gri_mappings": ["GRI 303-3", "GRI 303-4", "GRI 303-5"],
        "esrs_mappings": ["ESRS E3-4 (Water consumption)", "ESRS E3-4 (Water intensity)"],
        "brsr_principle": "P6",
    },
    {
        "id": "CORE-3", "attribute": "Energy Footprint",
        "parameters": ["total_energy_consumed_gj", "pct_renewable_energy",
                        "energy_intensity_per_turnover", "energy_intensity_per_output"],
        "measurement": "GJ; percentage; intensity per INR Cr turnover or per unit output",
        "assurance": "Reasonable assurance required",
        "gri_mappings": ["GRI 302-1", "GRI 302-3"],
        "esrs_mappings": ["ESRS E1-5 (Energy consumption)", "ESRS E1-5 (Energy intensity)", "ESRS E1-5 (Renewable share)"],
        "brsr_principle": "P6",
    },
    {
        "id": "CORE-4", "attribute": "Embrace Circularity — Details of Waste Management",
        "parameters": ["plastic_waste_mt", "e_waste_mt", "bio_medical_waste_mt",
                        "construction_waste_mt", "battery_waste_mt", "radioactive_waste_mt",
                        "hazardous_waste_mt", "non_hazardous_waste_mt",
                        "waste_intensity_per_turnover", "waste_recycled_reused_pct"],
        "measurement": "Metric Tonnes; intensity per INR Cr turnover; percentage recycled/reused",
        "assurance": "Reasonable assurance on waste intensity and recycling %",
        "gri_mappings": ["GRI 306-3", "GRI 306-4", "GRI 306-5"],
        "esrs_mappings": ["ESRS E5-5 (Waste generation)", "ESRS E5-5 (Resource inflows/outflows)"],
        "brsr_principle": "P6",
    },
    {
        "id": "CORE-5", "attribute": "Enhancing Employee Wellbeing and Safety",
        "parameters": ["spending_on_wellbeing_pct_of_turnover", "spending_on_wellbeing_pct_of_pat",
                        "ltifr_employees", "ltifr_workers", "fatalities_employees",
                        "fatalities_workers", "total_recordable_work_related_injuries",
                        "high_consequence_injuries_employees", "high_consequence_injuries_workers"],
        "measurement": "Percentage of turnover/PAT; LTIFR; counts",
        "assurance": "Reasonable assurance on LTIFR and fatality data",
        "gri_mappings": ["GRI 403-9", "GRI 403-10"],
        "esrs_mappings": ["ESRS S1-14 (Health and safety metrics)"],
        "brsr_principle": "P3",
    },
    {
        "id": "CORE-6", "attribute": "Enabling Gender Diversity in Business",
        "parameters": ["gross_wages_paid_female_pct", "gross_wages_paid_male_pct",
                        "wage_gap_pct", "complaints_sexual_harassment_filed",
                        "complaints_sexual_harassment_resolved",
                        "women_in_board_pct", "women_in_workforce_pct"],
        "measurement": "Percentages; counts of complaints filed and resolved",
        "assurance": "Limited assurance initially; Reasonable over time",
        "gri_mappings": ["GRI 405-2 (Remuneration ratio)", "GRI 406-1"],
        "esrs_mappings": ["ESRS S1-16 (Pay gap)", "ESRS S1-9 (Diversity metrics)"],
        "brsr_principle": "P5",
    },
    {
        "id": "CORE-7", "attribute": "Enabling Inclusive Development",
        "parameters": ["input_from_msme_pct", "input_from_small_producers_pct",
                        "procurement_from_district_state_pct",
                        "job_creation_smaller_towns_wages_pct"],
        "measurement": "Percentage of total procurement; percentage of total wages in smaller towns",
        "assurance": "Limited assurance",
        "gri_mappings": ["GRI 204-1 (Local suppliers)", "GRI 413-1"],
        "esrs_mappings": ["ESRS S3 (Affected communities — local procurement)"],
        "brsr_principle": "P8",
    },
    {
        "id": "CORE-8", "attribute": "Fairness in Engaging with Customers and Suppliers",
        "parameters": ["instances_data_breaches", "instances_cyber_security_breaches",
                        "corrective_actions_data_breach",
                        "days_accounts_payable_msme", "days_accounts_payable_others"],
        "measurement": "Counts; Days payable outstanding (DPO)",
        "assurance": "Limited assurance",
        "gri_mappings": ["GRI 418-1 (Privacy complaints)", "GRI 417-2"],
        "esrs_mappings": ["ESRS S4 (Consumer data protection)", "ESRS G1 (Payment practices)"],
        "brsr_principle": "P9",
    },
    {
        "id": "CORE-9", "attribute": "Open-ness of Business",
        "parameters": ["concentration_purchases_top_10_pct", "concentration_sales_top_10_pct",
                        "concentration_purchases_trading_house_pct",
                        "concentration_sales_trading_house_pct",
                        "related_party_transactions_as_pct_turnover"],
        "measurement": "Percentage of total purchases/sales; RPT as % of turnover",
        "assurance": "Limited assurance",
        "gri_mappings": ["GRI 2-6 (Activities, value chain)", "GRI 2-15 (Conflicts of interest)"],
        "esrs_mappings": ["ESRS G1 (Business conduct — related party)", "ESRS 2 (General Disclosures)"],
        "brsr_principle": "P1",
    },
]


# ---------------------------------------------------------------------------
# BRSR Section A — General Disclosures
# ---------------------------------------------------------------------------

BRSR_SECTION_A: list[dict] = [
    {"id": "A-I", "title": "Details of the listed entity", "fields": [
        "cin", "name", "year_of_incorporation", "registered_office", "corporate_office",
        "email", "telephone", "website", "financial_year", "stock_exchanges", "paid_up_capital",
        "contact_person_name", "contact_person_designation", "contact_person_telephone",
        "contact_person_email", "reporting_boundary"]},
    {"id": "A-II", "title": "Products/Services", "fields": [
        "main_activity_description", "main_activity_group_code", "business_activity_nics",
        "products_services_sold_top5_turnover_pct"]},
    {"id": "A-III", "title": "Operations", "fields": [
        "number_locations_national_plants", "number_locations_national_offices",
        "number_locations_international_plants", "number_locations_international_offices",
        "markets_served"]},
    {"id": "A-IV", "title": "Employees", "fields": [
        "total_employees_permanent", "total_employees_other_than_permanent",
        "total_workers_permanent", "total_workers_other_than_permanent",
        "differently_abled_employees", "differently_abled_workers",
        "women_participation_board_of_directors", "turnover_rate_permanent_employees",
        "turnover_rate_permanent_workers"]},
    {"id": "A-V", "title": "Holding/Subsidiary/Associate/JV", "fields": [
        "names_of_holding_subsidiary_associate_jv",
        "pct_shares_held", "does_entity_participate_in_br_of_parent_subsidiary"]},
    {"id": "A-VI", "title": "CSR Details", "fields": [
        "csr_applicable_yes_no", "turnover_inr_crores", "net_worth_inr_crores"]},
    {"id": "A-VII", "title": "Transparency and Disclosures", "fields": [
        "complaints_grievances_on_any_of_9_principles",
        "overview_material_responsible_business_conduct_issues"]},
]


# ---------------------------------------------------------------------------
# BRSR Section B — Management and Process Disclosures
# ---------------------------------------------------------------------------

BRSR_SECTION_B: list[dict] = [
    {"id": "B-1", "question": "Policy and management processes (for each principle)",
     "fields": ["policy_exists", "policy_approved_by_board", "web_link_to_policy",
                "policy_translated_to_procedures", "grievance_redressal_mechanism",
                "overview_of_alignment_with_ngrbc"]},
    {"id": "B-2", "question": "Governance, leadership and oversight",
     "fields": ["head_of_department_for_each_principle", "director_responsible",
                "committee_of_board_composition", "frequency_of_review",
                "independent_assessment_evaluation", "sustainability_report_published",
                "hyperlink_to_sustainability_report"]},
    {"id": "B-3", "question": "Details of the highest authority responsible for implementation",
     "fields": ["designation_of_authority", "process_for_identification_of_material_topics",
                "external_stakeholder_engagement_on_material_topics"]},
]


# ---------------------------------------------------------------------------
# BRSR-GRI-ESRS Complete Cross-Reference Map
# ---------------------------------------------------------------------------

BRSR_GRI_ESRS_MAPPING: list[dict] = [
    # Section A mappings
    {"brsr_ref": "Section A", "brsr_item": "General Disclosures",
     "gri_standards": ["GRI 2-1 to 2-5"], "esrs_standards": ["ESRS 2 (BP-1, BP-2)"]},
    # Section B mappings
    {"brsr_ref": "Section B", "brsr_item": "Management and Process",
     "gri_standards": ["GRI 2-9 to 2-21", "GRI 3-1 to 3-3"], "esrs_standards": ["ESRS 2 (GOV-1 to GOV-5)", "ESRS 2 (SBM-1 to SBM-3)"]},
    # Principle mappings
    {"brsr_ref": "P1", "brsr_item": "Ethics, Transparency and Accountability",
     "gri_standards": ["GRI 2: General Disclosures 2021", "GRI 205: Anti-corruption 2016"],
     "esrs_standards": ["ESRS G1: Business Conduct (G1-1 to G1-6)"]},
    {"brsr_ref": "P2", "brsr_item": "Sustainable Goods and Services",
     "gri_standards": ["GRI 301: Materials 2016", "GRI 306: Waste 2020",
                       "GRI 308: Supplier Environmental Assessment 2016", "GRI 414: Supplier Social Assessment 2016"],
     "esrs_standards": ["ESRS E5: Resource Use and Circular Economy", "ESRS S2: Workers in the Value Chain"]},
    {"brsr_ref": "P3", "brsr_item": "Employee Well-being",
     "gri_standards": ["GRI 401: Employment 2016", "GRI 403: Occupational Health and Safety 2018",
                       "GRI 404: Training and Education 2016"],
     "esrs_standards": ["ESRS S1: Own Workforce (S1-1 to S1-17)"]},
    {"brsr_ref": "P4", "brsr_item": "Stakeholder Engagement",
     "gri_standards": ["GRI 2: General Disclosures 2021 (2-29)", "GRI 3: Material Topics 2021"],
     "esrs_standards": ["ESRS 2: General Disclosures (SBM-2)", "ESRS S1", "ESRS S2", "ESRS S3", "ESRS S4"]},
    {"brsr_ref": "P5", "brsr_item": "Human Rights",
     "gri_standards": ["GRI 202: Market Presence 2016", "GRI 405: Diversity and Equal Opportunity 2016",
                       "GRI 406: Non-discrimination 2016", "GRI 410: Security Practices 2016",
                       "GRI 414: Supplier Social Assessment 2016"],
     "esrs_standards": ["ESRS S1: Own Workforce", "ESRS S2: Workers in Value Chain", "ESRS S3: Affected Communities"]},
    {"brsr_ref": "P6", "brsr_item": "Environment",
     "gri_standards": ["GRI 302: Energy 2016", "GRI 303: Water and Effluents 2018",
                       "GRI 304: Biodiversity 2016", "GRI 305: Emissions 2016",
                       "GRI 306: Waste 2020", "GRI 308: Supplier Environmental Assessment 2016"],
     "esrs_standards": ["ESRS E1: Climate Change", "ESRS E2: Pollution",
                        "ESRS E3: Water and Marine Resources", "ESRS E4: Biodiversity and Ecosystems",
                        "ESRS E5: Resource Use and Circular Economy"]},
    {"brsr_ref": "P7", "brsr_item": "Policy Advocacy",
     "gri_standards": ["GRI 206: Anti-competitive Behavior 2016", "GRI 415: Public Policy 2016"],
     "esrs_standards": ["ESRS G1: Business Conduct (G1-5 Political engagement)"]},
    {"brsr_ref": "P8", "brsr_item": "Inclusive Growth",
     "gri_standards": ["GRI 204: Procurement Practices 2016", "GRI 413: Local Communities 2016"],
     "esrs_standards": ["ESRS S3: Affected Communities (S3-1 to S3-5)"]},
    {"brsr_ref": "P9", "brsr_item": "Consumer Responsibility",
     "gri_standards": ["GRI 416: Customer Health and Safety 2016", "GRI 417: Marketing and Labeling 2016",
                       "GRI 418: Customer Privacy 2016"],
     "esrs_standards": ["ESRS S4: Consumers and End-users (S4-1 to S4-5)"]},
]


# ---------------------------------------------------------------------------
# Result Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ReportSection:
    """Single section of a regulatory report."""
    section_id: str
    title: str
    framework: str
    status: str = "incomplete"      # incomplete | partial | complete | not_applicable
    completeness_pct: float = 0.0
    disclosures: list[dict] = field(default_factory=list)
    narrative: str = ""
    data_points: dict = field(default_factory=dict)
    gaps: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)


@dataclass
class CompiledReport:
    """Full compiled regulatory report."""
    report_id: str
    framework: str
    entity_name: str
    reporting_period_start: str
    reporting_period_end: str
    compilation_date: str
    overall_completeness_pct: float = 0.0
    overall_status: str = "draft"
    sections: list[ReportSection] = field(default_factory=list)
    summary: dict = field(default_factory=dict)
    gaps_summary: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Compiler
# ---------------------------------------------------------------------------

class RegulatoryReportCompiler:
    """
    Compiles structured regulatory reports from platform module outputs.

    Usage:
        compiler = RegulatoryReportCompiler()
        report = compiler.compile_tcfd(entity_data, period_start, period_end)
        report = compiler.compile_sfdr_periodic(fund_data, period_start, period_end)
        report = compiler.compile_gri305(entity_data, period_start, period_end)
    """

    # ── TCFD ──────────────────────────────────────────────────────────────

    def compile_tcfd(
        self,
        entity_data: dict,
        period_start: str,
        period_end: str,
    ) -> CompiledReport:
        """Compile TCFD 11-recommendation structured disclosure."""

        sections: list[ReportSection] = []
        total_disclosed = 0

        for rec in TCFD_RECOMMENDATIONS:
            rec_id = rec["id"]
            pillar = rec["pillar"]
            data_key = f"tcfd_{rec_id.lower().replace('-', '_')}"
            rec_data = entity_data.get(data_key, {})

            disclosures = []
            gaps = []
            sources = []

            # Map platform data to TCFD guidance points
            for gp in rec["guidance"]:
                gp_key = gp[:40].lower().replace(" ", "_").replace("/", "_")
                if rec_data.get(gp_key):
                    disclosures.append({"guidance": gp, "response": rec_data[gp_key], "status": "disclosed"})
                else:
                    disclosures.append({"guidance": gp, "response": None, "status": "gap"})
                    gaps.append(f"Missing: {gp}")

            disclosed = sum(1 for d in disclosures if d["status"] == "disclosed")
            total_guidance = len(disclosures)
            comp_pct = (disclosed / total_guidance * 100) if total_guidance else 0
            total_disclosed += disclosed

            # Auto-populate from platform engines
            auto_data = self._auto_populate_tcfd(rec_id, entity_data)
            if auto_data:
                sources.append("Platform auto-populated")

            status = "complete" if comp_pct >= 90 else ("partial" if comp_pct > 0 else "incomplete")

            sections.append(ReportSection(
                section_id=rec_id,
                title=f"{pillar}: {rec['recommendation'][:80]}",
                framework="TCFD",
                status=status,
                completeness_pct=round(comp_pct, 1),
                disclosures=disclosures,
                narrative=rec_data.get("narrative", ""),
                data_points=auto_data,
                gaps=gaps,
                sources=sources,
            ))

        total_guidance_points = sum(len(r["guidance"]) for r in TCFD_RECOMMENDATIONS)
        overall_pct = (total_disclosed / total_guidance_points * 100) if total_guidance_points else 0

        return CompiledReport(
            report_id=f"TCFD-{entity_data.get('entity_id', 'UNKNOWN')}-{period_end}",
            framework="TCFD",
            entity_name=entity_data.get("entity_name", ""),
            reporting_period_start=period_start,
            reporting_period_end=period_end,
            compilation_date=datetime.utcnow().isoformat(),
            overall_completeness_pct=round(overall_pct, 1),
            overall_status="complete" if overall_pct >= 90 else ("partial" if overall_pct > 0 else "draft"),
            sections=sections,
            summary={"pillars": {p: 0 for p in ["Governance", "Strategy", "Risk Management", "Metrics & Targets"]},
                     "total_recommendations": 11, "disclosed_count": sum(1 for s in sections if s.status == "complete")},
            gaps_summary=[g for s in sections for g in s.gaps],
            recommendations=self._tcfd_recommendations(sections),
        )

    def _auto_populate_tcfd(self, rec_id: str, data: dict) -> dict:
        """Auto-populate TCFD data points from platform engines."""
        auto = {}
        if rec_id == "MT-b":
            # GHG emissions — pull from carbon calculator
            for key in ["scope1_tco2e", "scope2_tco2e", "scope3_tco2e", "total_tco2e", "ghg_intensity"]:
                if data.get(key) is not None:
                    auto[key] = data[key]
        elif rec_id == "STR-c":
            # Scenario resilience — pull from scenario analysis
            for key in ["scenario_1_5c_impact", "scenario_2c_impact", "scenario_3c_impact",
                        "nze_alignment", "transition_risk_score", "physical_risk_score"]:
                if data.get(key) is not None:
                    auto[key] = data[key]
        elif rec_id == "MT-a":
            # Climate metrics
            for key in ["waci", "carbon_footprint", "climate_var", "implied_temperature_rise"]:
                if data.get(key) is not None:
                    auto[key] = data[key]
        return auto

    def _tcfd_recommendations(self, sections: list[ReportSection]) -> list[str]:
        recs = []
        incomplete = [s for s in sections if s.status == "incomplete"]
        if incomplete:
            recs.append(f"Priority: Complete {len(incomplete)} fully missing TCFD disclosures")
        partial = [s for s in sections if s.status == "partial"]
        if partial:
            recs.append(f"Enhance {len(partial)} partially complete disclosures to reach full compliance")
        if any(s.section_id == "STR-c" and s.status != "complete" for s in sections):
            recs.append("Critical: Scenario analysis disclosure (STR-c) required for TCFD compliance")
        if any(s.section_id == "MT-b" and s.status != "complete" for s in sections):
            recs.append("Critical: GHG emissions (MT-b) must include Scope 1, 2, and 3")
        return recs

    # ── SFDR Periodic Disclosure ──────────────────────────────────────────

    def compile_sfdr_periodic(
        self,
        fund_data: dict,
        period_start: str,
        period_end: str,
    ) -> CompiledReport:
        """Compile SFDR periodic disclosure (Annex III Art.8 / Annex IV Art.9)."""

        article = fund_data.get("sfdr_article", 8)
        annex = "III" if article == 8 else "IV"

        sections: list[ReportSection] = []

        # Section 1 — Sustainable investment objective / environmental characteristics
        s1_data = fund_data.get("sustainable_investment", {})
        sections.append(ReportSection(
            section_id="SFDR-1",
            title=f"{'Environmental/social characteristics' if article == 8 else 'Sustainable investment objective'}",
            framework=f"SFDR Annex {annex}",
            status="complete" if s1_data.get("description") else "incomplete",
            completeness_pct=100.0 if s1_data.get("description") else 0.0,
            narrative=s1_data.get("description", ""),
            data_points={"article": article, "annex": annex},
        ))

        # Section 2 — PAI indicators
        pai_section = self._compile_pai_indicators(fund_data)
        sections.append(pai_section)

        # Section 3 — Proportion of investments
        inv_data = fund_data.get("investment_proportions", {})
        fields = ["taxonomy_aligned_pct", "sustainable_pct", "other_environmental_pct", "social_pct", "other_pct"]
        inv_disclosed = sum(1 for f in fields if inv_data.get(f) is not None)
        sections.append(ReportSection(
            section_id="SFDR-3",
            title="Proportion of investments",
            framework=f"SFDR Annex {annex}",
            status="complete" if inv_disclosed >= 3 else ("partial" if inv_disclosed > 0 else "incomplete"),
            completeness_pct=round(inv_disclosed / len(fields) * 100, 1),
            data_points=inv_data,
        ))

        # Section 4 — EU Taxonomy alignment
        tax_data = fund_data.get("taxonomy_alignment", {})
        sections.append(ReportSection(
            section_id="SFDR-4",
            title="EU Taxonomy alignment of investments",
            framework=f"SFDR Annex {annex}",
            status="complete" if tax_data.get("turnover_aligned_pct") is not None else "incomplete",
            completeness_pct=100.0 if tax_data.get("turnover_aligned_pct") is not None else 0.0,
            data_points=tax_data,
        ))

        # Section 5 — Top investments
        top_inv = fund_data.get("top_investments", [])
        sections.append(ReportSection(
            section_id="SFDR-5",
            title="Top investments",
            framework=f"SFDR Annex {annex}",
            status="complete" if len(top_inv) >= 10 else ("partial" if top_inv else "incomplete"),
            completeness_pct=min(100.0, len(top_inv) / 15 * 100),
            data_points={"top_investments": top_inv[:15]},
        ))

        overall_pct = sum(s.completeness_pct for s in sections) / len(sections) if sections else 0

        return CompiledReport(
            report_id=f"SFDR-{fund_data.get('fund_id', 'UNKNOWN')}-{period_end}",
            framework=f"SFDR Article {article}",
            entity_name=fund_data.get("fund_name", ""),
            reporting_period_start=period_start,
            reporting_period_end=period_end,
            compilation_date=datetime.utcnow().isoformat(),
            overall_completeness_pct=round(overall_pct, 1),
            overall_status="complete" if overall_pct >= 90 else ("partial" if overall_pct > 0 else "draft"),
            sections=sections,
            summary={"article": article, "annex": annex,
                     "pai_indicators_reported": pai_section.data_points.get("reported_count", 0),
                     "taxonomy_aligned_pct": tax_data.get("turnover_aligned_pct")},
            gaps_summary=[g for s in sections for g in s.gaps],
            recommendations=self._sfdr_recommendations(sections, article),
        )

    def _compile_pai_indicators(self, fund_data: dict) -> ReportSection:
        """Compile SFDR PAI mandatory indicators."""
        pai_data = fund_data.get("pai_indicators", {})
        disclosures = []
        gaps = []
        reported = 0

        for pai in SFDR_MANDATORY_PAI:
            pai_key = f"pai_{pai['pai_id']}_{pai['metric'][:20].lower().replace(' ', '_')}"
            val = pai_data.get(pai_key) or pai_data.get(f"pai_{pai['pai_id']}")
            if val is not None:
                disclosures.append({
                    "pai_id": pai["pai_id"],
                    "indicator": pai["indicator"],
                    "metric": pai["metric"],
                    "value": val,
                    "unit": pai["unit"],
                    "status": "reported",
                })
                reported += 1
            else:
                disclosures.append({
                    "pai_id": pai["pai_id"],
                    "indicator": pai["indicator"],
                    "metric": pai["metric"],
                    "value": None,
                    "unit": pai["unit"],
                    "status": "gap",
                })
                gaps.append(f"PAI {pai['pai_id']}: {pai['indicator']} — not reported")

        unique_pais = len(set(p["pai_id"] for p in SFDR_MANDATORY_PAI))
        reported_unique = len(set(d["pai_id"] for d in disclosures if d["status"] == "reported"))

        return ReportSection(
            section_id="SFDR-2",
            title="Principal Adverse Impact (PAI) indicators",
            framework="SFDR",
            status="complete" if reported_unique >= 14 else ("partial" if reported_unique > 0 else "incomplete"),
            completeness_pct=round(reported_unique / unique_pais * 100, 1),
            disclosures=disclosures,
            data_points={"reported_count": reported_unique, "total_mandatory": unique_pais},
            gaps=gaps,
        )

    def _sfdr_recommendations(self, sections: list[ReportSection], article: int) -> list[str]:
        recs = []
        pai = next((s for s in sections if s.section_id == "SFDR-2"), None)
        if pai and pai.completeness_pct < 100:
            recs.append(f"Complete all 14 mandatory PAI indicators (currently {pai.data_points.get('reported_count', 0)}/14)")
        tax = next((s for s in sections if s.section_id == "SFDR-4"), None)
        if tax and tax.status != "complete":
            recs.append("Report EU Taxonomy alignment percentages (turnover, capex, opex)")
        if article == 9:
            recs.append("Article 9 funds must demonstrate sustainable investment objective — ensure 100% sustainable")
        return recs

    # ── GRI 305 ───────────────────────────────────────────────────────────

    def compile_gri305(
        self,
        entity_data: dict,
        period_start: str,
        period_end: str,
    ) -> CompiledReport:
        """Compile GRI 305 emissions disclosure."""

        sections: list[ReportSection] = []

        for disc in GRI_305_DISCLOSURES:
            disc_data = entity_data.get(disc["id"].replace("-", "_").lower(), {})
            gaps = []
            disclosed = 0

            for rf in disc["required_fields"]:
                if disc_data.get(rf) is not None:
                    disclosed += 1
                else:
                    gaps.append(f"{disc['id']}: Missing {rf}")

            comp = (disclosed / len(disc["required_fields"]) * 100) if disc["required_fields"] else 0

            sections.append(ReportSection(
                section_id=disc["id"],
                title=disc["title"],
                framework="GRI 305",
                status="complete" if comp >= 90 else ("partial" if comp > 0 else "incomplete"),
                completeness_pct=round(comp, 1),
                data_points=disc_data,
                gaps=gaps,
            ))

        overall = sum(s.completeness_pct for s in sections) / len(sections) if sections else 0

        return CompiledReport(
            report_id=f"GRI305-{entity_data.get('entity_id', 'UNKNOWN')}-{period_end}",
            framework="GRI 305",
            entity_name=entity_data.get("entity_name", ""),
            reporting_period_start=period_start,
            reporting_period_end=period_end,
            compilation_date=datetime.utcnow().isoformat(),
            overall_completeness_pct=round(overall, 1),
            overall_status="complete" if overall >= 90 else ("partial" if overall > 0 else "draft"),
            sections=sections,
            gaps_summary=[g for s in sections for g in s.gaps],
            recommendations=self._gri305_recommendations(sections),
        )

    def _gri305_recommendations(self, sections: list[ReportSection]) -> list[str]:
        recs = []
        s1 = next((s for s in sections if s.section_id == "305-1"), None)
        if s1 and s1.status != "complete":
            recs.append("305-1: Scope 1 disclosure is fundamental — complete all required fields")
        s3 = next((s for s in sections if s.section_id == "305-3"), None)
        if s3 and s3.status != "complete":
            recs.append("305-3: Scope 3 categories must specify which of the 15 categories are included")
        s5 = next((s for s in sections if s.section_id == "305-5"), None)
        if s5 and s5.status == "incomplete":
            recs.append("305-5: GHG reduction disclosure demonstrates climate action — high investor value")
        return recs

    # ── SEC Climate Disclosure ────────────────────────────────────────────

    def compile_sec_climate(
        self,
        entity_data: dict,
        period_start: str,
        period_end: str,
    ) -> CompiledReport:
        """Compile SEC Climate-Related Disclosures (Reg S-K Subpart 1500)."""

        sections: list[ReportSection] = []

        for item in SEC_CLIMATE_ITEMS:
            item_data = entity_data.get(f"sec_{item['item']}", {})
            gaps = []
            disclosed = 0

            for rf in item["required"]:
                if item_data.get(rf):
                    disclosed += 1
                else:
                    gaps.append(f"Item {item['item']}: Missing {rf}")

            comp = (disclosed / len(item["required"]) * 100) if item["required"] else 0

            sections.append(ReportSection(
                section_id=f"SEC-{item['item']}",
                title=item["title"],
                framework="SEC Climate",
                status="complete" if comp >= 90 else ("partial" if comp > 0 else "incomplete"),
                completeness_pct=round(comp, 1),
                data_points=item_data,
                gaps=gaps,
            ))

        overall = sum(s.completeness_pct for s in sections) / len(sections) if sections else 0

        return CompiledReport(
            report_id=f"SEC-{entity_data.get('entity_id', 'UNKNOWN')}-{period_end}",
            framework="SEC Climate",
            entity_name=entity_data.get("entity_name", ""),
            reporting_period_start=period_start,
            reporting_period_end=period_end,
            compilation_date=datetime.utcnow().isoformat(),
            overall_completeness_pct=round(overall, 1),
            overall_status="complete" if overall >= 90 else ("partial" if overall > 0 else "draft"),
            sections=sections,
            summary={"items_covered": len(SEC_CLIMATE_ITEMS),
                     "complete_count": sum(1 for s in sections if s.status == "complete")},
            gaps_summary=[g for s in sections for g in s.gaps],
            recommendations=self._sec_recommendations(sections),
        )

    def _sec_recommendations(self, sections: list[ReportSection]) -> list[str]:
        recs = []
        s1506 = next((s for s in sections if s.section_id == "SEC-1506"), None)
        if s1506 and s1506.status != "complete":
            recs.append("Item 1506 (Scope 1/2 emissions) is mandatory for large accelerated filers")
        s1502 = next((s for s in sections if s.section_id == "SEC-1502"), None)
        if s1502 and s1502.status != "complete":
            recs.append("Item 1502 (Governance) requires board oversight description")
        return recs

    # ── ISSB S1/S2 ────────────────────────────────────────────────────────

    def compile_issb(
        self,
        entity_data: dict,
        period_start: str,
        period_end: str,
    ) -> CompiledReport:
        """Compile IFRS S1 (General) + S2 (Climate) disclosure."""

        sections: list[ReportSection] = []

        # S1 core requirements
        s1_areas = [
            ("S1-GOV", "Governance", ["governance_body", "management_role", "skills_competencies"]),
            ("S1-STR", "Strategy", ["risks_opportunities", "business_model_impact",
                                    "strategy_decision_making", "financial_position_impact"]),
            ("S1-RM", "Risk Management", ["identification_process", "assessment_process",
                                          "management_process", "integration_overall_rm"]),
            ("S1-MT", "Metrics and Targets", ["metrics_used", "targets_set", "progress_against_targets"]),
        ]

        for sid, title, fields in s1_areas:
            area_data = entity_data.get(sid.lower().replace("-", "_"), {})
            disclosed = sum(1 for f in fields if area_data.get(f))
            comp = (disclosed / len(fields) * 100) if fields else 0
            gaps = [f"{sid}: Missing {f}" for f in fields if not area_data.get(f)]
            sections.append(ReportSection(
                section_id=sid, title=f"IFRS S1 — {title}", framework="ISSB S1",
                status="complete" if comp >= 90 else ("partial" if comp > 0 else "incomplete"),
                completeness_pct=round(comp, 1), data_points=area_data, gaps=gaps,
            ))

        # S2 climate-specific
        s2_areas = [
            ("S2-PHY", "Physical risks", ["acute_risks", "chronic_risks", "financial_effects",
                                           "location_concentration", "vulnerability_assessment"]),
            ("S2-TRA", "Transition risks", ["policy_legal_risks", "technology_risks",
                                             "market_risks", "reputation_risks", "financial_effects"]),
            ("S2-OPP", "Climate opportunities", ["resource_efficiency", "energy_source",
                                                   "products_services", "markets", "resilience"]),
            ("S2-GHG", "GHG emissions", ["scope1_tco2e", "scope2_tco2e", "scope3_tco2e",
                                          "methodology", "intensity_metric"]),
            ("S2-SCN", "Scenario analysis", ["scenarios_used", "time_horizons",
                                              "resilience_assessment", "financial_impacts"]),
        ]

        for sid, title, fields in s2_areas:
            area_data = entity_data.get(sid.lower().replace("-", "_"), {})
            disclosed = sum(1 for f in fields if area_data.get(f))
            comp = (disclosed / len(fields) * 100) if fields else 0
            gaps = [f"{sid}: Missing {f}" for f in fields if not area_data.get(f)]
            sections.append(ReportSection(
                section_id=sid, title=f"IFRS S2 — {title}", framework="ISSB S2",
                status="complete" if comp >= 90 else ("partial" if comp > 0 else "incomplete"),
                completeness_pct=round(comp, 1), data_points=area_data, gaps=gaps,
            ))

        overall = sum(s.completeness_pct for s in sections) / len(sections) if sections else 0

        return CompiledReport(
            report_id=f"ISSB-{entity_data.get('entity_id', 'UNKNOWN')}-{period_end}",
            framework="ISSB S1/S2",
            entity_name=entity_data.get("entity_name", ""),
            reporting_period_start=period_start,
            reporting_period_end=period_end,
            compilation_date=datetime.utcnow().isoformat(),
            overall_completeness_pct=round(overall, 1),
            overall_status="complete" if overall >= 90 else ("partial" if overall > 0 else "draft"),
            sections=sections,
            summary={"s1_sections": 4, "s2_sections": 5,
                     "complete_count": sum(1 for s in sections if s.status == "complete")},
            gaps_summary=[g for s in sections for g in s.gaps],
            recommendations=self._issb_recommendations(sections),
        )

    def _issb_recommendations(self, sections: list[ReportSection]) -> list[str]:
        recs = []
        ghg = next((s for s in sections if s.section_id == "S2-GHG"), None)
        if ghg and ghg.status != "complete":
            recs.append("IFRS S2 GHG emissions: Scope 1/2 mandatory; Scope 3 required if material")
        scn = next((s for s in sections if s.section_id == "S2-SCN"), None)
        if scn and scn.status != "complete":
            recs.append("IFRS S2 scenario analysis: Must include climate-related scenario consistent with latest international agreement")
        return recs

    # ── APRA CPG 229 ─────────────────────────────────────────────────────

    def compile_apra_cpg229(
        self,
        entity_data: dict,
        period_start: str,
        period_end: str,
    ) -> CompiledReport:
        """Compile APRA CPG 229 Climate Change Financial Risks assessment."""

        sections: list[ReportSection] = []

        for sec in APRA_CPG229_SECTIONS:
            sec_key = sec["section"].lower().replace(" ", "_").replace("(", "").replace(")", "")
            sec_data = entity_data.get(f"apra_{sec_key}", {})
            disclosed = sum(1 for r in sec["requirements"] if sec_data.get(r[:30].lower().replace(" ", "_")))
            total = len(sec["requirements"])
            comp = (disclosed / total * 100) if total else 0
            gaps = [f"{sec['section']}: {r}" for r in sec["requirements"]
                    if not sec_data.get(r[:30].lower().replace(" ", "_"))]

            sections.append(ReportSection(
                section_id=f"CPG229-{sec['paragraphs']}",
                title=f"CPG 229 — {sec['section']} (paras {sec['paragraphs']})",
                framework="APRA CPG 229",
                status="complete" if comp >= 90 else ("partial" if comp > 0 else "incomplete"),
                completeness_pct=round(comp, 1),
                data_points=sec_data,
                gaps=gaps,
            ))

        overall = sum(s.completeness_pct for s in sections) / len(sections) if sections else 0

        return CompiledReport(
            report_id=f"APRA-{entity_data.get('entity_id', 'UNKNOWN')}-{period_end}",
            framework="APRA CPG 229",
            entity_name=entity_data.get("entity_name", ""),
            reporting_period_start=period_start,
            reporting_period_end=period_end,
            compilation_date=datetime.utcnow().isoformat(),
            overall_completeness_pct=round(overall, 1),
            overall_status="complete" if overall >= 90 else ("partial" if overall > 0 else "draft"),
            sections=sections,
            gaps_summary=[g for s in sections for g in s.gaps],
            recommendations=["APRA expects TCFD-aligned disclosures as minimum",
                             "Scenario analysis must cover at least 1.5C and 3C+ pathways"],
        )

    # ── SEBI BRSR + BRSR Core ────────────────────────────────────────────

    def compile_brsr(
        self,
        entity_data: dict,
        period_start: str,
        period_end: str,
    ) -> CompiledReport:
        """
        Compile SEBI BRSR + BRSR Core with GRI and ESRS cross-reference.

        Assesses entity data against:
          - Section A: General Disclosures (26 fields)
          - Section B: Management and Process (3 blocks x 9 principles)
          - Section C: 9 NGRBC Principles (Essential + Leadership)
          - BRSR Core: 9 quantitative ESG attributes

        Returns CompiledReport with GRI + ESRS mappings embedded in each section.
        """
        sections: list[ReportSection] = []

        # ── Section A — General Disclosures ──
        sec_a_data = entity_data.get("section_a", {})
        a_total_fields = sum(len(item["fields"]) for item in BRSR_SECTION_A)
        a_disclosed = 0
        a_gaps: list[str] = []
        for item in BRSR_SECTION_A:
            item_data = sec_a_data.get(item["id"].lower().replace("-", "_"), {})
            for f in item["fields"]:
                if item_data.get(f):
                    a_disclosed += 1
                else:
                    a_gaps.append(f"Section A ({item['title']}): Missing {f}")

        a_pct = (a_disclosed / a_total_fields * 100) if a_total_fields else 0
        sections.append(ReportSection(
            section_id="BRSR-A",
            title="Section A: General Disclosures",
            framework="BRSR",
            status="complete" if a_pct >= 90 else ("partial" if a_pct > 0 else "incomplete"),
            completeness_pct=round(a_pct, 1),
            data_points={"total_fields": a_total_fields, "disclosed": a_disclosed,
                         "gri_mapping": ["GRI 2-1 to 2-5"], "esrs_mapping": ["ESRS 2 (BP-1, BP-2)"]},
            gaps=a_gaps,
        ))

        # ── Section B — Management and Process ──
        sec_b_data = entity_data.get("section_b", {})
        b_total = sum(len(block["fields"]) for block in BRSR_SECTION_B) * 9  # per principle
        b_disclosed = 0
        b_gaps: list[str] = []
        for block in BRSR_SECTION_B:
            for p_idx in range(1, 10):
                p_key = f"p{p_idx}"
                block_data = sec_b_data.get(f"{block['id'].lower().replace('-', '_')}_{p_key}", {})
                for f in block["fields"]:
                    if block_data.get(f):
                        b_disclosed += 1
                    else:
                        b_gaps.append(f"Section B ({block['question'][:40]}): P{p_idx} missing {f}")

        b_pct = (b_disclosed / b_total * 100) if b_total else 0
        sections.append(ReportSection(
            section_id="BRSR-B",
            title="Section B: Management and Process Disclosures",
            framework="BRSR",
            status="complete" if b_pct >= 90 else ("partial" if b_pct > 0 else "incomplete"),
            completeness_pct=round(b_pct, 1),
            data_points={"total_fields": b_total, "disclosed": b_disclosed,
                         "gri_mapping": ["GRI 2-9 to 2-21", "GRI 3-1 to 3-3"],
                         "esrs_mapping": ["ESRS 2 (GOV-1 to GOV-5)", "ESRS 2 (SBM-1 to SBM-3)"]},
            gaps=b_gaps[:20],  # Cap gap list
        ))

        # ── Section C — 9 NGRBC Principles ──
        total_principle_disclosed = 0
        total_principle_items = 0

        for princ in BRSR_PRINCIPLES:
            p_data = entity_data.get(princ["id"].lower(), {})
            p_disclosures: list[dict] = []
            p_gaps: list[str] = []
            p_sources: list[str] = []
            disclosed = 0

            # Essential indicators
            for ind in princ["essential_indicators"]:
                ind_key = ind[:40].lower().replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "").replace(",", "")
                if p_data.get(ind_key):
                    p_disclosures.append({"indicator": ind, "level": "Essential", "status": "disclosed"})
                    disclosed += 1
                else:
                    p_disclosures.append({"indicator": ind, "level": "Essential", "status": "gap"})
                    p_gaps.append(f"{princ['id']} Essential: {ind[:60]}")

            # Leadership indicators
            for ind in princ["leadership_indicators"]:
                ind_key = ind[:40].lower().replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "").replace(",", "")
                if p_data.get(ind_key):
                    p_disclosures.append({"indicator": ind, "level": "Leadership", "status": "disclosed"})
                    disclosed += 1
                else:
                    p_disclosures.append({"indicator": ind, "level": "Leadership", "status": "gap"})
                    p_gaps.append(f"{princ['id']} Leadership: {ind[:60]}")

            total_indicators = len(princ["essential_indicators"]) + len(princ["leadership_indicators"])
            total_principle_items += total_indicators
            total_principle_disclosed += disclosed
            comp = (disclosed / total_indicators * 100) if total_indicators else 0

            sections.append(ReportSection(
                section_id=f"BRSR-{princ['id']}",
                title=f"{princ['id']}: {princ['principle'][:80]}",
                framework="BRSR",
                status="complete" if comp >= 90 else ("partial" if comp > 0 else "incomplete"),
                completeness_pct=round(comp, 1),
                disclosures=p_disclosures,
                data_points={
                    "essential_count": len(princ["essential_indicators"]),
                    "leadership_count": len(princ["leadership_indicators"]),
                    "disclosed": disclosed,
                    "gri_mappings": princ["gri_mappings"],
                    "esrs_mappings": princ["esrs_mappings"],
                },
                gaps=p_gaps,
                sources=p_sources,
            ))

        # ── BRSR Core — 9 Quantitative ESG Attributes ──
        core_sections: list[ReportSection] = []
        total_core_params = 0
        total_core_disclosed = 0

        for attr in BRSR_CORE_ATTRIBUTES:
            attr_data = entity_data.get(f"brsr_core_{attr['id'].lower().replace('-', '_')}", {})
            c_gaps: list[str] = []
            c_disclosed = 0

            for param in attr["parameters"]:
                if attr_data.get(param) is not None:
                    c_disclosed += 1
                else:
                    c_gaps.append(f"BRSR Core {attr['attribute']}: Missing {param}")

            total_core_params += len(attr["parameters"])
            total_core_disclosed += c_disclosed
            comp = (c_disclosed / len(attr["parameters"]) * 100) if attr["parameters"] else 0

            core_sections.append(ReportSection(
                section_id=f"BRSR-{attr['id']}",
                title=f"BRSR Core: {attr['attribute']}",
                framework="BRSR Core",
                status="complete" if comp >= 90 else ("partial" if comp > 0 else "incomplete"),
                completeness_pct=round(comp, 1),
                data_points={
                    "parameters": attr["parameters"],
                    "values": {p: attr_data.get(p) for p in attr["parameters"]},
                    "measurement": attr["measurement"],
                    "assurance": attr["assurance"],
                    "gri_mappings": attr["gri_mappings"],
                    "esrs_mappings": attr["esrs_mappings"],
                    "brsr_principle": attr["brsr_principle"],
                },
                gaps=c_gaps,
            ))

        sections.extend(core_sections)

        # ── Overall Completeness ──
        all_sections = sections
        if all_sections:
            overall_pct = sum(s.completeness_pct for s in all_sections) / len(all_sections)
        else:
            overall_pct = 0

        core_pct = (total_core_disclosed / total_core_params * 100) if total_core_params else 0
        principle_pct = (total_principle_disclosed / total_principle_items * 100) if total_principle_items else 0

        return CompiledReport(
            report_id=f"BRSR-{entity_data.get('entity_id', 'UNKNOWN')}-{period_end}",
            framework="SEBI BRSR",
            entity_name=entity_data.get("entity_name", ""),
            reporting_period_start=period_start,
            reporting_period_end=period_end,
            compilation_date=datetime.utcnow().isoformat(),
            overall_completeness_pct=round(overall_pct, 1),
            overall_status="complete" if overall_pct >= 90 else ("partial" if overall_pct > 0 else "draft"),
            sections=all_sections,
            summary={
                "total_principles": 9,
                "principles_complete": sum(1 for s in sections if s.section_id.startswith("BRSR-P") and s.status == "complete"),
                "brsr_core_completeness_pct": round(core_pct, 1),
                "principle_completeness_pct": round(principle_pct, 1),
                "section_a_completeness_pct": round(a_pct, 1),
                "section_b_completeness_pct": round(b_pct, 1),
                "gri_esrs_cross_reference_count": len(BRSR_GRI_ESRS_MAPPING),
            },
            gaps_summary=[g for s in all_sections for g in s.gaps][:50],
            recommendations=self._brsr_recommendations(sections, core_pct, principle_pct),
            metadata={
                "brsr_version": "SEBI BRSR 2023 (Updated Annexure II)",
                "brsr_core_version": "SEBI Annexure I — BRSR Core (2023)",
                "gri_linkage": "SEBI BRSR-GRI Linkage Document (2023)",
                "esrs_cross_reference": "EFRAG ESRS Set 1 (2023)",
                "applicable_to": "Top 1000 listed entities by market capitalisation (mandatory)",
                "brsr_core_applicable_to": "Top 150 listed entities (mandatory from FY 2023-24)",
            },
        )

    def _brsr_recommendations(
        self, sections: list[ReportSection], core_pct: float, principle_pct: float
    ) -> list[str]:
        """Generate BRSR-specific recommendations."""
        recs = []

        if core_pct < 50:
            recs.append("Priority: BRSR Core attributes require quantitative data — complete GHG, water, energy, waste metrics for SEBI compliance")
        elif core_pct < 90:
            recs.append("Enhance BRSR Core: Fill remaining quantitative KPIs to achieve reasonable assurance readiness")

        if principle_pct < 30:
            recs.append("Critical: Majority of NGRBC Principle indicators are undisclosed — begin with Essential indicators for P3 (Employee), P5 (Human Rights), P6 (Environment)")

        # Check critical environmental principle
        p6 = next((s for s in sections if s.section_id == "BRSR-P6"), None)
        if p6 and p6.status != "complete":
            recs.append("P6 (Environment) is the most scrutinised principle — ensure Scope 1/2/3, water, waste, and biodiversity disclosures are complete")

        # Check employee safety
        core5 = next((s for s in sections if s.section_id == "BRSR-CORE-5"), None)
        if core5 and core5.status != "complete":
            recs.append("BRSR Core: Employee wellbeing and safety (LTIFR, fatalities) is a mandatory BRSR Core attribute — complete with reasonable assurance")

        # Check GHG footprint
        core1 = next((s for s in sections if s.section_id == "BRSR-CORE-1"), None)
        if core1 and core1.status != "complete":
            recs.append("BRSR Core: GHG footprint (Scope 1 + 2 + intensity) is the first BRSR Core attribute — requires reasonable assurance")

        # Gender diversity
        core6 = next((s for s in sections if s.section_id == "BRSR-CORE-6"), None)
        if core6 and core6.status == "incomplete":
            recs.append("BRSR Core: Gender diversity metrics (wage gap, POSH complaints) are mandatory — disclose with breakdown")

        # Section A gaps
        sec_a = next((s for s in sections if s.section_id == "BRSR-A"), None)
        if sec_a and sec_a.status != "complete":
            recs.append("Section A (General Disclosures) is foundational — ensure CIN, employee breakdown, and CSR details are complete")

        # Cross-reference recommendation
        recs.append("Leverage GRI-BRSR linkage: entities already reporting under GRI can map existing disclosures to BRSR sections (see SEBI linkage document)")
        recs.append("ESRS reporters: BRSR P6 maps directly to ESRS E1-E5; P3 maps to ESRS S1 — use CSRD disclosures to auto-populate BRSR")

        return recs

    # ── Output Rendering (P1-3 / E4) ──────────────────────────────────────

    @staticmethod
    def render_html(report: "CompiledReport") -> str:
        """Render a CompiledReport to a self-contained HTML string.

        Produces a submission-ready HTML document that can be:
        - Displayed in browser (no external assets — all CSS is inline)
        - Passed to render_pdf_bytes() for WeasyPrint PDF conversion
        - Embedded in an email or portal page

        E4: HTML is the intermediate format before PDF — structurally complete
        so WeasyPrint renders correctly with page breaks, headers, and footers.
        """
        status_colours = {
            "complete": "#16a34a",   # green-600
            "partial":  "#d97706",   # amber-600
            "incomplete": "#dc2626", # red-600
            "not_applicable": "#6b7280",
            "draft": "#6b7280",
        }

        def _colour(status: str) -> str:
            return status_colours.get(status, "#374151")

        def _pct_bar(pct: float) -> str:
            pct = max(0.0, min(100.0, pct))
            colour = "#16a34a" if pct >= 80 else ("#d97706" if pct >= 40 else "#dc2626")
            return (
                f'<div style="background:#e5e7eb;border-radius:4px;height:8px;width:100%;margin:4px 0">'
                f'<div style="background:{colour};width:{pct:.1f}%;height:8px;border-radius:4px"></div>'
                f'</div>'
            )

        lines: list[str] = [
            "<!DOCTYPE html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="UTF-8">',
            f'<title>{report.framework} — {report.entity_name}</title>',
            "<style>",
            "  body { font-family: Arial, Helvetica, sans-serif; font-size: 11pt;"
            "         color: #111827; margin: 0; padding: 0; }",
            "  .cover { background: #1e3a5f; color: white; padding: 48px 60px;"
            "           page-break-after: always; }",
            "  .cover h1 { font-size: 24pt; margin: 0 0 8px 0; }",
            "  .cover h2 { font-size: 14pt; font-weight: normal; margin: 0 0 24px 0;"
            "              opacity: 0.85; }",
            "  .cover .meta { font-size: 10pt; opacity: 0.75; }",
            "  .section { padding: 28px 60px; border-bottom: 1px solid #e5e7eb; }",
            "  .section:last-child { border-bottom: none; }",
            "  .section-header { display: flex; justify-content: space-between;"
            "                    align-items: flex-start; margin-bottom: 12px; }",
            "  .section-title { font-size: 13pt; font-weight: bold; color: #1e3a5f; }",
            "  .badge { display: inline-block; padding: 2px 10px; border-radius: 12px;"
            "           font-size: 9pt; font-weight: bold; color: white; }",
            "  table { width: 100%; border-collapse: collapse; margin: 12px 0;"
            "          font-size: 10pt; }",
            "  th { background: #f3f4f6; text-align: left; padding: 6px 10px;"
            "       border: 1px solid #d1d5db; }",
            "  td { padding: 5px 10px; border: 1px solid #e5e7eb; vertical-align: top; }",
            "  .gap-list { margin: 8px 0 0 0; padding-left: 18px; font-size: 9.5pt;"
            "              color: #dc2626; }",
            "  .gap-list li { margin: 2px 0; }",
            "  .summary-box { background: #f9fafb; border-left: 4px solid #1e3a5f;"
            "                 padding: 14px 20px; margin: 16px 0; border-radius: 4px; }",
            "  .rec-list { padding-left: 18px; font-size: 10pt; color: #1e3a5f; }",
            "  .rec-list li { margin: 4px 0; }",
            "  @page { margin: 20mm 18mm; @bottom-center { content: counter(page)"
            '          " / " counter(pages); font-size: 9pt; color: #6b7280; } }',
            "  @media print { .section { page-break-inside: avoid; } }",
            "</style>",
            "</head>",
            "<body>",
            # Cover page
            '<div class="cover">',
            f'  <h1>{report.framework}</h1>',
            f'  <h2>Disclosure Report — {report.entity_name}</h2>',
            f'  <div class="meta">',
            f'    Reporting period: {report.reporting_period_start} – {report.reporting_period_end}<br>',
            f'    Compiled: {report.compilation_date[:10]}<br>',
            f'    Overall completeness: <strong>{report.overall_completeness_pct:.1f}%</strong>',
            f'    &nbsp;|&nbsp; Status: <strong>{report.overall_status.upper()}</strong>',
            f'  </div>',
            '</div>',
            # Executive summary
            '<div class="section">',
            '  <div class="section-title">Executive Summary</div>',
            '  <div class="summary-box">',
            f'    <strong>Framework:</strong> {report.framework}<br>',
            f'    <strong>Entity:</strong> {report.entity_name}<br>',
            f'    <strong>Overall completeness:</strong> {report.overall_completeness_pct:.1f}%',
        ]
        lines.append(_pct_bar(report.overall_completeness_pct))
        if report.gaps_summary:
            lines.append(f'    <strong>Top gaps:</strong> {len(report.gaps_summary)} identified<br>')
        lines += [
            '  </div>',
        ]
        if report.recommendations:
            lines += [
                '  <div class="section-title" style="margin-top:16px">Recommendations</div>',
                '  <ol class="rec-list">',
            ]
            for rec in report.recommendations[:10]:
                lines.append(f'    <li>{rec}</li>')
            lines.append('  </ol>')
        lines.append('</div>')

        # Per-section detail
        for sec in report.sections:
            badge_colour = _colour(sec.status)
            lines += [
                '<div class="section">',
                '  <div class="section-header">',
                f'    <div class="section-title">{sec.section_id}: {sec.title}</div>',
                f'    <span class="badge" style="background:{badge_colour}">'
                f'{sec.status.replace("_", " ").title()}&nbsp;{sec.completeness_pct:.0f}%</span>',
                '  </div>',
            ]
            lines.append(_pct_bar(sec.completeness_pct))
            if sec.narrative:
                lines.append(f'  <p style="font-size:10pt">{sec.narrative}</p>')
            # Data points table
            if sec.data_points:
                lines += [
                    '  <table>',
                    '    <tr><th>Data Point</th><th>Value</th></tr>',
                ]
                for k, v in list(sec.data_points.items())[:20]:
                    lines.append(f'    <tr><td>{k}</td><td>{v}</td></tr>')
                lines.append('  </table>')
            # Gaps
            if sec.gaps:
                lines += [
                    '  <ul class="gap-list">',
                ]
                for g in sec.gaps[:15]:
                    lines.append(f'    <li>{g}</li>')
                lines.append('  </ul>')
            lines.append('</div>')

        lines += ['</body>', '</html>']
        return "\n".join(lines)

    @staticmethod
    def render_pdf_bytes(report: "CompiledReport") -> bytes:
        """Render a CompiledReport to PDF bytes via WeasyPrint.

        Requirements:
            pip install weasyprint   (not a hard dependency — graceful fallback)

        Returns:
            PDF bytes if WeasyPrint is available.
            Raises ImportError with installation hint if WeasyPrint is absent.

        Usage:
            compiler = RegulatoryReportCompiler()
            rpt = compiler.compile_tcfd(entity_data, "2024-01-01", "2024-12-31")
            pdf = RegulatoryReportCompiler.render_pdf_bytes(rpt)
            with open("tcfd_report.pdf", "wb") as f:
                f.write(pdf)
        """
        try:
            from weasyprint import HTML as _WPHtml  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "WeasyPrint is required for PDF rendering: pip install weasyprint\n"
                "For HTML-only output use RegulatoryReportCompiler.render_html(report)."
            ) from exc

        html_str = RegulatoryReportCompiler.render_html(report)
        return _WPHtml(string=html_str).write_pdf()

    # ── Utility Methods ───────────────────────────────────────────────────

    @staticmethod
    def get_supported_frameworks() -> list[dict]:
        """Return list of supported regulatory frameworks."""
        return [
            {"code": "TCFD", "name": "Task Force on Climate-related Financial Disclosures",
             "region": "Global", "sections": 11, "method": "compile_tcfd"},
            {"code": "SFDR", "name": "Sustainable Finance Disclosure Regulation",
             "region": "EU", "sections": 5, "method": "compile_sfdr_periodic"},
            {"code": "GRI_305", "name": "GRI 305: Emissions",
             "region": "Global", "sections": 7, "method": "compile_gri305"},
            {"code": "SEC_CLIMATE", "name": "SEC Climate-Related Disclosures",
             "region": "USA", "sections": 6, "method": "compile_sec_climate"},
            {"code": "ISSB", "name": "IFRS S1/S2 — Sustainability/Climate",
             "region": "Global", "sections": 9, "method": "compile_issb"},
            {"code": "APRA_CPG229", "name": "APRA CPG 229 — Climate Change Financial Risks",
             "region": "Australia", "sections": 4, "method": "compile_apra_cpg229"},
            {"code": "BRSR", "name": "SEBI BRSR — Business Responsibility and Sustainability Report",
             "region": "India", "sections": 20, "method": "compile_brsr",
             "sub_frameworks": ["BRSR Core (9 ESG Attributes)", "BRSR Full (9 NGRBC Principles)"],
             "cross_references": ["GRI Standards", "ESRS (CSRD)"],
             "applicability": "Top 1000 listed entities (BRSR); Top 150 (BRSR Core)"},
        ]

    @staticmethod
    def get_tcfd_structure() -> list[dict]:
        """Return TCFD 11 recommendations structure."""
        return TCFD_RECOMMENDATIONS

    @staticmethod
    def get_sfdr_pai_template() -> list[dict]:
        """Return SFDR 14 mandatory PAI indicator template."""
        return SFDR_MANDATORY_PAI

    @staticmethod
    def get_gri305_template() -> list[dict]:
        """Return GRI 305 disclosure template."""
        return GRI_305_DISCLOSURES

    @staticmethod
    def get_sec_climate_template() -> list[dict]:
        """Return SEC climate disclosure items."""
        return SEC_CLIMATE_ITEMS

    @staticmethod
    def get_brsr_framework() -> dict:
        """
        Return complete BRSR / BRSR Core framework structure with GRI + ESRS mappings.

        Includes:
          - BRSR Core 9 attributes (quantitative KPIs)
          - BRSR 9 NGRBC Principles (Essential + Leadership)
          - Section A (General Disclosures)
          - Section B (Management and Process)
          - Full GRI-BRSR-ESRS cross-reference map
        """
        return {
            "framework": "SEBI BRSR",
            "version": "2023 (Updated Annexure I + II)",
            "applicability": {
                "brsr_full": "Top 1000 listed entities by market capitalisation (mandatory from FY 2022-23)",
                "brsr_core": "Top 150 listed entities (mandatory from FY 2023-24); Top 250 (from FY 2024-25); Top 500 (from FY 2025-26); Top 1000 (from FY 2026-27)",
                "assurance": "BRSR Core requires reasonable assurance by registered valuers/sustainability auditors",
            },
            "structure": {
                "section_a": {
                    "title": "General Disclosures",
                    "subsections": [{"id": s["id"], "title": s["title"], "field_count": len(s["fields"])} for s in BRSR_SECTION_A],
                },
                "section_b": {
                    "title": "Management and Process Disclosures",
                    "subsections": [{"id": b["id"], "question": b["question"], "field_count": len(b["fields"])} for b in BRSR_SECTION_B],
                    "note": "Applied across all 9 NGRBC Principles",
                },
                "section_c": {
                    "title": "Principle-wise Performance Disclosures",
                    "principles": [
                        {
                            "id": p["id"],
                            "principle": p["principle"],
                            "essential_indicator_count": len(p["essential_indicators"]),
                            "leadership_indicator_count": len(p["leadership_indicators"]),
                            "gri_mappings": p["gri_mappings"],
                            "esrs_mappings": p["esrs_mappings"],
                        }
                        for p in BRSR_PRINCIPLES
                    ],
                },
            },
            "brsr_core_attributes": [
                {
                    "id": a["id"],
                    "attribute": a["attribute"],
                    "parameters": a["parameters"],
                    "measurement": a["measurement"],
                    "assurance": a["assurance"],
                    "gri_mappings": a["gri_mappings"],
                    "esrs_mappings": a["esrs_mappings"],
                    "brsr_principle": a["brsr_principle"],
                }
                for a in BRSR_CORE_ATTRIBUTES
            ],
            "cross_reference_map": BRSR_GRI_ESRS_MAPPING,
        }
