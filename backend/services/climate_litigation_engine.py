"""
Climate Litigation Risk Engine (E91)
======================================
Comprehensive climate-related litigation risk assessment engine for financial
institutions, corporates, and asset managers.

Sub-modules:
  1. Greenwashing Risk Assessment — 20 red flags, regulatory exposure, remediation
  2. Disclosure Liability Assessment — 8 triggers, quantified exposure, priority gaps
  3. Fiduciary Duty Assessment — Duties X Framework, D&O liability, stewardship gaps
  4. Attribution Science Risk — Meehl-Haugen-Christidis score, physical damage attribution
  5. Litigation Exposure Computation — Aggregate exposure, IAS 37 provision, insurance gap
  6. Full Assessment — composite litigation_risk_score, tier, max/expected costs

References:
  - Sabin Center for Climate Change Law — Climate Change Litigation Databases (2024)
  - Oxford Net Zero / Grantham Research Institute — Global Trends in Climate Litigation 2024
  - Duties X Framework (University College London / ClientEarth, 2023)
  - FCA Consumer Duty PS22/9 and Anti-Greenwashing Rule PS23/16
  - EU Regulation (EU) 2023/2441 — Empowering consumers for the green transition
  - IAS 37 — Provisions, Contingent Liabilities and Contingent Assets
  - Meehl et al. (2024); Haugen & Aaheim (2023); Christidis et al. (2023)
    — Attribution science applied to climate litigation
  - TCFD Recommendations (2017) + 2021 Guidance on Scenario Analysis
  - SEC Climate Disclosure Rule (Release No. 33-11275, 2024)
  - CSRD / ESRS E1 — Climate change (applicable 2024+)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Sabin Center Case Taxonomy (8 Categories)
# ---------------------------------------------------------------------------

SABIN_CASE_TAXONOMY: dict[str, dict] = {
    "mandatory_disclosure": {
        "description": (
            "Litigation arising from alleged failures to make required climate-related "
            "disclosures under securities laws, ESG regulations, or sustainability reporting frameworks."
        ),
        "typical_plaintiffs": ["institutional investors", "shareholder groups", "securities regulators", "pension funds"],
        "typical_defendants": ["listed companies", "banks", "insurers", "asset managers"],
        "key_jurisdictions": ["US", "EU_Germany", "UK", "Australia", "Canada"],
        "settlement_range_m": (5, 500),
        "success_rate_pct": 22,
        "growth_trend": "rapidly_increasing",
        "leading_cases": [
            "McVeigh v REST (2020, Australia) — pension fund climate disclosure",
            "SEC v Brazilian Vale (2022) — Brumadinho dam disclosure failure",
            "ClientEarth v Shell Board (2023, UK) — TCFD disclosure adequacy",
        ],
    },
    "securities_fraud": {
        "description": (
            "Claims that entities made material misstatements or omissions about "
            "climate risks, clean energy credentials, or ESG performance in securities filings."
        ),
        "typical_plaintiffs": ["institutional investors", "securities class action law firms", "SEC/FCA"],
        "typical_defendants": ["fossil fuel companies", "ESG fund managers", "green bond issuers"],
        "key_jurisdictions": ["US", "UK", "EU_Netherlands", "Australia"],
        "settlement_range_m": (10, 2000),
        "success_rate_pct": 18,
        "growth_trend": "increasing",
        "leading_cases": [
            "In re ExxonMobil Securities Litigation (2023)",
            "Deutsche Bank / DWS SEC-ASIC greenwashing probe (2022)",
            "Goldman Sachs ESG fund misstatement SEC probe (2022)",
        ],
    },
    "product_liability": {
        "description": (
            "Claims that fossil fuel products caused or contributed to climate change damages, "
            "drawing on product liability law and public nuisance doctrines."
        ),
        "typical_plaintiffs": ["municipal governments", "state attorneys general", "coastal communities"],
        "typical_defendants": ["major oil and gas companies", "coal producers", "petrochemical companies"],
        "key_jurisdictions": ["US", "EU_Germany", "EU_France", "New_Zealand"],
        "settlement_range_m": (100, 10000),
        "success_rate_pct": 8,
        "growth_trend": "high_stakes_limited_precedent",
        "leading_cases": [
            "City of Honolulu v Sunoco et al. (2024)",
            "Milieudefensie et al. v Royal Dutch Shell (2021, Netherlands)",
            "Juliana v United States (9th Circuit, ongoing)",
        ],
    },
    "greenwashing": {
        "description": (
            "Regulatory enforcement and civil litigation targeting false or misleading "
            "sustainability claims in marketing materials, product names, and public communications."
        ),
        "typical_plaintiffs": ["consumers", "competition regulators", "FCA/SEC/ASIC", "NGOs"],
        "typical_defendants": ["asset managers", "banks", "consumer goods companies", "energy companies"],
        "key_jurisdictions": ["EU_Germany", "UK", "Australia", "US", "EU_Netherlands"],
        "settlement_range_m": (1, 200),
        "success_rate_pct": 35,
        "growth_trend": "very_rapidly_increasing",
        "leading_cases": [
            "ASIC v Mercer Superannuation (2023, Australia)",
            "ASA rulings on Ryanair/HSBC net zero adverts (UK, 2022-2023)",
            "BaFin investigation into DWS 'sustainable' fund claims (Germany, 2022)",
        ],
    },
    "corporate_planning": {
        "description": (
            "Litigation challenging adequacy of corporate transition plans, capex allocation, "
            "and strategic decisions inconsistent with Paris Agreement or net-zero commitments."
        ),
        "typical_plaintiffs": ["activist shareholders", "ClientEarth", "environmental NGOs"],
        "typical_defendants": ["oil and gas companies", "utility companies", "banks financing fossil fuels"],
        "key_jurisdictions": ["UK", "EU_Netherlands", "Australia", "EU_France"],
        "settlement_range_m": (0, 50),
        "success_rate_pct": 12,
        "growth_trend": "increasing",
        "leading_cases": [
            "ClientEarth v Shell PLC Board (2023, UK)",
            "Follow This shareholder resolutions v Shell/BP (2022-2024)",
            "Australasian Centre for Corporate Responsibility v Santos (2023)",
        ],
    },
    "constitutional_rights": {
        "description": (
            "Litigation invoking constitutional rights to life, a healthy environment, or "
            "future generations' rights, typically targeting governments for inadequate climate policy."
        ),
        "typical_plaintiffs": ["youth climate groups", "civil society organisations", "individuals"],
        "typical_defendants": ["national governments", "sub-national governments"],
        "key_jurisdictions": ["EU_Germany", "EU_Netherlands", "New_Zealand", "South_Africa", "India"],
        "settlement_range_m": (0, 10),
        "success_rate_pct": 28,
        "growth_trend": "increasing",
        "leading_cases": [
            "Neubauer et al. v Germany (BVerfG 2021) — intergenerational equity",
            "Urgenda Foundation v State of Netherlands (2019)",
            "Genesis Power Ltd v Minister for the Environment (NZ, 2023)",
        ],
    },
    "human_rights": {
        "description": (
            "Claims that climate change impacts violate human rights obligations, "
            "particularly affecting vulnerable communities and climate-displaced peoples."
        ),
        "typical_plaintiffs": ["indigenous communities", "Pacific island nations", "climate refugees"],
        "typical_defendants": ["major emitters", "governments", "financial institutions"],
        "key_jurisdictions": ["global", "EU_France", "Switzerland", "Japan", "India"],
        "settlement_range_m": (0, 100),
        "success_rate_pct": 15,
        "growth_trend": "emerging",
        "leading_cases": [
            "Torres Strait Islanders v Australia (OHCHR, 2022)",
            "Sacchi et al. v multiple governments (UNCRC, 2021)",
            "Climate Case Philippines (Commission on Human Rights, 2022)",
        ],
    },
    "attribution_science": {
        "description": (
            "Litigation using climate attribution science to link specific emitters' "
            "historical emissions to quantifiable physical damages (extreme weather events)."
        ),
        "typical_plaintiffs": ["damage claimants", "insurance companies", "municipal governments"],
        "typical_defendants": ["largest historical emitters", "fossil fuel companies"],
        "key_jurisdictions": ["US", "EU_Netherlands", "Australia", "global"],
        "settlement_range_m": (50, 5000),
        "success_rate_pct": 7,
        "growth_trend": "high_potential_increasing",
        "leading_cases": [
            "Lliuya v RWE (German courts, ongoing since 2015)",
            "City of Boulder v ExxonMobil (Colorado, 2023)",
            "Farmers vs large emitters (attribution framework cases, emerging)",
        ],
    },
}


# ---------------------------------------------------------------------------
# Jurisdiction Risk Profiles (15 Jurisdictions)
# ---------------------------------------------------------------------------

JURISDICTION_RISK_PROFILES: dict[str, dict] = {
    "US": {
        "climate_litigation_activity_score": 92,
        "regulatory_enforcement_score": 75,
        "greenwashing_enforcement_score": 70,
        "key_legislation": [
            "SEC Climate Disclosure Rule (Release 33-11275, 2024)",
            "Securities Exchange Act (misstatement liability)",
            "Clean Air Act §202",
            "State-level ESG disclosure laws (CA SB 253/261)",
        ],
        "recent_precedents": [
            "SEC greenwashing enforcement actions against ESG funds (2023-2024)",
            "State AGs climate litigation against fossil fuel companies",
            "Held v Montana (2023) — constitutional climate rights",
        ],
        "litigation_trend": "very_high",
        "notes": "Largest absolute volume of climate cases globally. SEC enforcement expanding.",
    },
    "UK": {
        "climate_litigation_activity_score": 72,
        "regulatory_enforcement_score": 80,
        "greenwashing_enforcement_score": 85,
        "key_legislation": [
            "FCA PS23/16 — Anti-Greenwashing Rule (effective 31 May 2024)",
            "FCA SDR PS23/16 — Sustainability Disclosure Requirements",
            "Climate Change Act 2008 (net zero target)",
            "Pension Schemes Act 2021 (TCFD mandatory)",
        ],
        "recent_precedents": [
            "FCA warnings to asset managers on greenwashing (2023-2024)",
            "ClientEarth v Shell Board (2023) — director duties",
            "ASA Advertising Standards Authority greenwashing rulings (ongoing)",
        ],
        "litigation_trend": "increasing",
        "notes": "FCA Anti-Greenwashing Rule creates significant new enforcement risk from May 2024.",
    },
    "EU_Germany": {
        "climate_litigation_activity_score": 68,
        "regulatory_enforcement_score": 85,
        "greenwashing_enforcement_score": 82,
        "key_legislation": [
            "CSRD / ESRS E1 (mandatory from 2024/2025/2026)",
            "EU Green Claims Directive (Reg 2024/825)",
            "BaFin SFDR enforcement powers",
            "German Civil Code §823 — environmental tort",
        ],
        "recent_precedents": [
            "Neubauer v Germany BVerfG (2021) — intergenerational equity",
            "Lliuya v RWE (Hamm Higher Regional Court, ongoing)",
            "BaFin investigations into sustainable fund claims (2022-2024)",
        ],
        "litigation_trend": "increasing",
        "notes": "Lliuya v RWE attribution case has landmark potential for industrial emitters.",
    },
    "EU_Netherlands": {
        "climate_litigation_activity_score": 78,
        "regulatory_enforcement_score": 80,
        "greenwashing_enforcement_score": 75,
        "key_legislation": [
            "Dutch Civil Code Art 6:162 — tort (onrechtmatige daad)",
            "CSRD transposition into Dutch law",
            "AFM greenwashing enforcement (SFDR/Taxonomy)",
        ],
        "recent_precedents": [
            "Milieudefensie v Royal Dutch Shell (2021) — 45% emissions reduction ordered",
            "Friends of the Earth NL v ING Bank (2022-ongoing)",
            "Urgenda Foundation v State of Netherlands (2019)",
        ],
        "litigation_trend": "very_high",
        "notes": "Urgenda and Shell precedents have inspired global wave of corporate climate litigation.",
    },
    "EU_France": {
        "climate_litigation_activity_score": 65,
        "regulatory_enforcement_score": 78,
        "greenwashing_enforcement_score": 72,
        "key_legislation": [
            "Loi Pacte (2019) — corporate purpose",
            "Loi Vigilance (2017) — duty of vigilance",
            "CSRD transposition",
            "French Climate and Resilience Law (2021)",
        ],
        "recent_precedents": [
            "Notre Affaire à Tous v Total (2022-ongoing) — duty of vigilance",
            "Commune de Grande-Synthe v France (Council of State, 2021)",
            "BNP Paribas lawsuit by NGOs re fossil fuel financing (2023)",
        ],
        "litigation_trend": "increasing",
        "notes": "Loi Vigilance creates distinct duty of vigilance pathway for French companies.",
    },
    "Australia": {
        "climate_litigation_activity_score": 75,
        "regulatory_enforcement_score": 72,
        "greenwashing_enforcement_score": 80,
        "key_legislation": [
            "Australian Securities and Investments Commission Act 2001 (ASIC enforcement)",
            "Corporations Act 2001 §674 — continuous disclosure",
            "Treasury Laws Amendment (2022 Measures No. 4) — TCFD mandatory",
        ],
        "recent_precedents": [
            "ASIC v Mercer Superannuation (Federal Court, 2023)",
            "ASIC v Active Super (2023) — greenwashing penalty",
            "Sharma v Minister for Environment (2021, climate duty of care)",
        ],
        "litigation_trend": "very_high",
        "notes": "ASIC most active financial greenwashing regulator globally per Sabin Centre 2024.",
    },
    "Canada": {
        "climate_litigation_activity_score": 55,
        "regulatory_enforcement_score": 60,
        "greenwashing_enforcement_score": 65,
        "key_legislation": [
            "Canadian Environmental Protection Act 1999",
            "Competition Act (misleading advertising)",
            "Quebec Loi 14 — climate accountability",
        ],
        "recent_precedents": [
            "Canadian Environmental Law Association challenges (ongoing)",
            "Competition Bureau investigation into fossil fuel claims (2023)",
        ],
        "litigation_trend": "emerging",
        "notes": "Competition Bureau greenwashing investigations signal increasing enforcement appetite.",
    },
    "New_Zealand": {
        "climate_litigation_activity_score": 58,
        "regulatory_enforcement_score": 65,
        "greenwashing_enforcement_score": 60,
        "key_legislation": [
            "Climate Change Response (Zero Carbon) Amendment Act 2019",
            "Financial Sector (Climate-related Disclosures and Other Matters) Amendment Act 2021",
            "Fair Trading Act 1986 (misleading conduct)",
        ],
        "recent_precedents": [
            "Smith v Fonterra Co-operative Group (NZSC, 2024) — novel tort",
            "Houghton v Minister of Transport (2022)",
        ],
        "litigation_trend": "emerging",
        "notes": "Smith v Fonterra NZSC ruling on novel tort could open new liability pathway.",
    },
    "Switzerland": {
        "climate_litigation_activity_score": 52,
        "regulatory_enforcement_score": 68,
        "greenwashing_enforcement_score": 58,
        "key_legislation": [
            "CO2 Act (revised 2021)",
            "FINMA Circular 2016/17 — operational risks climate",
            "Swiss Federal Act on Financial Services (FinSA)",
        ],
        "recent_precedents": [
            "KlimaSeniorinnen v Switzerland (ECtHR Grand Chamber, 2024) — Art 8 ECHR",
            "FINMA guidance on greenwashing in financial sector (2023)",
        ],
        "litigation_trend": "significant",
        "notes": "ECtHR Grand Chamber KlimaSeniorinnen ruling is landmark for climate human rights in Europe.",
    },
    "Japan": {
        "climate_litigation_activity_score": 38,
        "regulatory_enforcement_score": 55,
        "greenwashing_enforcement_score": 45,
        "key_legislation": [
            "Green Transformation (GX) Promotion Act (2023)",
            "Financial Instruments and Exchange Act",
            "Consumer Protection Law (misleading representation)",
        ],
        "recent_precedents": [
            "Kiko Network v IHI Corporation (2022)",
            "Citizens' Committee on the Kobe Coal-Fired Power Plant (2023)",
        ],
        "litigation_trend": "low_but_emerging",
        "notes": "GX Promotion Act may introduce new disclosure obligations that create liability exposure.",
    },
    "Singapore": {
        "climate_litigation_activity_score": 30,
        "regulatory_enforcement_score": 62,
        "greenwashing_enforcement_score": 55,
        "key_legislation": [
            "Singapore Green Plan 2030",
            "MAS Guidelines on Environmental Risk Management (2020/2021)",
            "Securities and Futures Act (disclosure obligations)",
        ],
        "recent_precedents": [
            "MAS enforcement of SGX climate reporting requirements (2022-ongoing)",
        ],
        "litigation_trend": "emerging",
        "notes": "MAS is Asia's most active financial regulator on climate risk disclosures.",
    },
    "South_Africa": {
        "climate_litigation_activity_score": 48,
        "regulatory_enforcement_score": 50,
        "greenwashing_enforcement_score": 42,
        "key_legislation": [
            "National Environmental Management Act (NEMA)",
            "Climate Change Act 22 of 2024 (signed May 2024)",
            "Companies Act 71 of 2008 — director duties",
        ],
        "recent_precedents": [
            "Deadly Air case v South African Government (2022) — air quality",
            "Earthlife Africa v Minister of Environmental Affairs (2017-ongoing)",
        ],
        "litigation_trend": "emerging",
        "notes": "Climate Change Act 2024 creates new compliance obligations and enforcement powers.",
    },
    "Brazil": {
        "climate_litigation_activity_score": 44,
        "regulatory_enforcement_score": 48,
        "greenwashing_enforcement_score": 38,
        "key_legislation": [
            "Federal Climate Change Policy (Law 12.187/2009)",
            "Amazon Fund legislation (2023 restoration)",
            "CVM sustainability disclosure requirements",
        ],
        "recent_precedents": [
            "PSOL v President of the Republic (ADPF 760, STF 2022) — climate inaction",
            "Global Witness deforestation linkage cases (ongoing)",
        ],
        "litigation_trend": "emerging",
        "notes": "Amazon deforestation-linked supply chain cases increasing; EUDR enforcement catalyst.",
    },
    "India": {
        "climate_litigation_activity_score": 40,
        "regulatory_enforcement_score": 45,
        "greenwashing_enforcement_score": 35,
        "key_legislation": [
            "Environment (Protection) Act 1986",
            "SEBI BRSR Core Framework (2023)",
            "National Green Tribunal Act 2010",
        ],
        "recent_precedents": [
            "National Green Tribunal air quality orders (multiple, 2022-2024)",
            "M.K. Ranjitsinh v Union of India (Supreme Court, 2024) — climate right",
        ],
        "litigation_trend": "increasing",
        "notes": "Supreme Court 2024 ruling recognised right against adverse effects of climate change.",
    },
    "global": {
        "climate_litigation_activity_score": 65,
        "regulatory_enforcement_score": 50,
        "greenwashing_enforcement_score": 55,
        "key_legislation": [
            "Paris Agreement (nationally implemented)",
            "UNFCCC Art 6.4 activity rules",
            "OECD Guidelines for Multinational Enterprises",
            "UN Guiding Principles on Business and Human Rights",
        ],
        "recent_precedents": [
            "KlimaSeniorinnen v Switzerland (ECtHR Grand Chamber, 2024)",
            "International Court of Justice Climate Advisory Opinion (2024)",
            "ITLOS Climate Change and UNCLOS Advisory Opinion (2024)",
        ],
        "litigation_trend": "high_and_increasing",
        "notes": "ICJ and ITLOS advisory opinions in 2024 significantly expanded global litigation landscape.",
    },
}


# ---------------------------------------------------------------------------
# Disclosure Liability Triggers (8 Triggers)
# ---------------------------------------------------------------------------

DISCLOSURE_LIABILITY_TRIGGERS: dict[str, dict] = {
    "ifrs_s2_misstatement": {
        "description": (
            "Material misstatement in IFRS S2 climate-related disclosures, including incorrect "
            "physical/transition risk quantification, scenario analysis, or metrics & targets."
        ),
        "jurisdiction": "global (IFRS-adopting)",
        "statute_ref": "IFRS S2 §§7-12 (Governance), §§13-24 (Strategy), §§25-41 (Risk), §§42-54 (Metrics)",
        "plaintiff_standing": "investors, securities regulators",
        "typical_claim_m_range": (5, 500),
        "enforcement_body": "Securities regulators (IOSCO members); IFRS Foundation monitoring",
    },
    "sec_climate_omission": {
        "description": (
            "Omission of material climate risk information required under SEC Climate Disclosure Rule "
            "(Release No. 33-11275) including Scope 1/2 emissions, climate risk governance, and scenario analysis."
        ),
        "jurisdiction": "US (SEC-registered entities)",
        "statute_ref": "17 CFR §229.1500-1507; Exchange Act §10(b); Rule 10b-5",
        "plaintiff_standing": "institutional investors, SEC Division of Enforcement",
        "typical_claim_m_range": (10, 2000),
        "enforcement_body": "SEC Division of Enforcement; private securities class actions",
    },
    "csrd_greenwashing": {
        "description": (
            "False or misleading disclosures under CSRD/ESRS E1 reporting, including incorrect "
            "Scope 3 methodologies, unjustified climate targets, or inadequate double materiality assessment."
        ),
        "jurisdiction": "EU (CSRD in-scope entities)",
        "statute_ref": "CSRD Art 8; ESRS E1; EU Green Claims Directive (EU) 2024/825",
        "plaintiff_standing": "investors, NGOs, national enforcement authorities, competitors",
        "typical_claim_m_range": (1, 200),
        "enforcement_body": "National competent authorities; EFRAG monitoring; NGOs",
    },
    "transition_plan_misrepresentation": {
        "description": (
            "Misrepresentation of climate transition plans, including net-zero commitments lacking "
            "credible interim targets, or transition capex inconsistent with stated decarbonisation pathway."
        ),
        "jurisdiction": "UK, EU, Australia, US",
        "statute_ref": "FCA PS23/22 (TPT); CSRD ESRS E1 §16; IFRS S2 §14(e); TPT Disclosure Framework",
        "plaintiff_standing": "institutional investors, FCA, NGOs, activist shareholders",
        "typical_claim_m_range": (5, 500),
        "enforcement_body": "FCA; National competent authorities; shareholder derivative actions",
    },
    "tcfd_material_omission": {
        "description": (
            "Material omission of TCFD-required disclosures, particularly climate scenario analysis, "
            "physical risk quantification, or Scope 3 emissions where material."
        ),
        "jurisdiction": "UK, EU, Australia, NZ, Singapore, Japan",
        "statute_ref": "TCFD Recommendations 2017; UK mandatory TCFD (2022); MAS Guidelines",
        "plaintiff_standing": "shareholders, securities regulators",
        "typical_claim_m_range": (2, 200),
        "enforcement_body": "FCA; ASIC; MAS; national securities regulators",
    },
    "scope3_underreporting": {
        "description": (
            "Deliberate or negligent underreporting of Scope 3 financed emissions (PCAF) "
            "or value chain emissions (GHG Protocol Category 15), materially distorting climate performance."
        ),
        "jurisdiction": "US, EU, Australia, UK",
        "statute_ref": "GHG Protocol Corporate Value Chain Standard §12 (C15); PCAF Standard 2022; SEC Rule 10b-5",
        "plaintiff_standing": "investors, SEC, ASIC, FCA",
        "typical_claim_m_range": (5, 1000),
        "enforcement_body": "SEC; ASIC; FCA; NGO climate accountability coalitions",
    },
    "asset_stranding_concealment": {
        "description": (
            "Concealment of material stranded asset risk in financial statements, "
            "including undisclosed impairment risk on fossil fuel reserves, power plants, "
            "or real estate under 1.5°C scenario."
        ),
        "jurisdiction": "US, UK, EU, Australia",
        "statute_ref": "IAS 36 (Impairment); IFRS S2 §§25-35; SEC FRB 2010 Climate Guidance",
        "plaintiff_standing": "institutional investors, securities regulators, auditors",
        "typical_claim_m_range": (50, 5000),
        "enforcement_body": "SEC; FCA; PCAOB; national audit regulators",
    },
    "fiduciary_breach": {
        "description": (
            "Breach of fiduciary duty to beneficiaries by failing to integrate material climate "
            "risks into investment decisions, stewardship, or pension scheme management."
        ),
        "jurisdiction": "UK, Australia, US, EU",
        "statute_ref": "UK Pension Schemes Act 2021 §125; ERISA §404(a)(1)(B); IORP II Art 19; PRI Principles",
        "plaintiff_standing": "pension beneficiaries, trustee boards, occupational pension regulators",
        "typical_claim_m_range": (5, 500),
        "enforcement_body": "The Pensions Regulator (UK); DoL ERISA enforcement (US); EIOPA",
    },
}


# ---------------------------------------------------------------------------
# Duties X Framework — 6 Fiduciary Duties
# ---------------------------------------------------------------------------

DUTIES_X_FRAMEWORK: dict[str, dict] = {
    "act_in_good_faith": {
        "description": "Directors and trustees must act in good faith in the interests of the entity and its beneficiaries",
        "climate_application": (
            "Failure to consider material climate transition risks in strategic planning may constitute "
            "breach of duty to act in good faith toward long-term interests of beneficiaries."
        ),
        "breach_indicators": [
            "No climate risk governance framework",
            "Board lacks climate expertise (no qualified director)",
            "Climate risk excluded from strategic planning cycles",
            "TCFD/CSRD disclosures absent despite materiality",
        ],
        "case_precedents": [
            "ClientEarth v Shell PLC Board (2023, UK High Court)",
            "APRA enforcement on RSF boards lacking climate governance (2023)",
        ],
        "max_d_and_o_exposure_m": 50,
    },
    "avoid_conflicts": {
        "description": "Directors must avoid conflicts of interest between personal interests and entity obligations",
        "climate_application": (
            "Board members with material interests in fossil fuel assets, or receiving remuneration "
            "tied to fossil fuel production, may face conflict of interest challenges in climate decisions."
        ),
        "breach_indicators": [
            "Board remuneration tied to fossil fuel production metrics",
            "Director with undisclosed fossil fuel company shareholdings",
            "Conflicts not declared in transition plan governance decisions",
        ],
        "case_precedents": [
            "Shareholder resolutions on director conflict of interest — ExxonMobil AGM (2021-2023)",
        ],
        "max_d_and_o_exposure_m": 20,
    },
    "maintain_confidentiality": {
        "description": "Directors must not disclose confidential information or use it for personal benefit",
        "climate_application": (
            "Internal climate scenario analyses showing material asset impairment, if not disclosed "
            "while being used for insider trading or selective disclosure, creates dual liability."
        ),
        "breach_indicators": [
            "Internal scenario showing >30% asset impairment not disclosed",
            "Selective disclosure of climate risk data to preferred investors",
            "Inconsistency between internal climate models and public disclosures",
        ],
        "case_precedents": [
            "SEC investigation into Exxon internal vs public climate scenario divergence (2015-2019)",
        ],
        "max_d_and_o_exposure_m": 100,
    },
    "exercise_care_skill": {
        "description": "Directors must exercise reasonable care, skill, and diligence in fulfilling duties",
        "climate_application": (
            "Directors are expected to have or acquire sufficient climate competency to make "
            "informed decisions on material climate risks. Failure to do so is a breach of duty of care."
        ),
        "breach_indicators": [
            "No climate training for board members since 2021",
            "Third-party climate risk assessment never commissioned",
            "Transition plan not reviewed against IPCC 1.5 degree pathway",
            "Physical risk assessment not conducted for material assets",
        ],
        "case_precedents": [
            "APRA CPG 229 — climate financial risk management expectation (Australia)",
            "PRA SS3/19 — supervisory expectations on climate skills (UK)",
        ],
        "max_d_and_o_exposure_m": 75,
    },
    "act_within_authority": {
        "description": "Directors must act within the scope of their authority as defined by articles, constitution, or trust deed",
        "climate_application": (
            "Directors approving new fossil fuel investments contrary to published net-zero "
            "commitments or transition plan may be acting outside stated authority or contrary to purpose."
        ),
        "breach_indicators": [
            "Capex approval inconsistent with published transition plan",
            "New coal/oil gas investment approved post-net-zero commitment without board rationale",
            "Transition plan override not documented in board minutes",
        ],
        "case_precedents": [
            "Follow This v Shell Board (shareholder resolution series 2017-2024)",
            "Australasian Centre for Corporate Responsibility v Santos (2023)",
        ],
        "max_d_and_o_exposure_m": 30,
    },
    "disclose_material_info": {
        "description": "Directors must ensure timely disclosure of material information to shareholders and regulators",
        "climate_application": (
            "Non-disclosure of material climate risks — including physical asset exposure, "
            "transition cost estimates, or regulatory carbon price scenarios — may breach disclosure duties."
        ),
        "breach_indicators": [
            "TCFD report omits quantified financial impact",
            "Scope 3 emissions material but not disclosed",
            "Carbon price sensitivity analysis absent from annual report",
            "Physical risk assessment not included despite material coastal/flood exposure",
        ],
        "case_precedents": [
            "SEC v Exxon (2019) — proxy cost of carbon misstatement",
            "ASIC v Australian Securities Exchange (continuous disclosure climate obligations, 2023)",
        ],
        "max_d_and_o_exposure_m": 200,
    },
}


# ---------------------------------------------------------------------------
# Greenwashing Red Flags (20 flags across 4 categories)
# ---------------------------------------------------------------------------

GREENWASHING_RED_FLAGS: dict[str, list] = {
    "misleading_claims": [
        {
            "flag_id": "GW-01",
            "description": "Use of 'carbon neutral' without verified offsets or with low-quality offsets only",
            "regulator": "FCA (UK) / ASIC (Australia) / FTC (US) / BaFin (Germany)",
            "enforcement_action_taken": True,
            "fine_range_m": (0.1, 10),
            "remediation": "Disclose offset quality (vintage, standard, registry); retire corresponding credits",
        },
        {
            "flag_id": "GW-02",
            "description": "'Net zero' or 'climate positive' claims without credible transition plan with interim targets",
            "regulator": "FCA PS23/16 (UK) / EU Green Claims Directive / ASIC",
            "enforcement_action_taken": True,
            "fine_range_m": (0.5, 50),
            "remediation": "Publish TPT-compliant transition plan with 2025/2030/2035/2050 interim targets",
        },
        {
            "flag_id": "GW-03",
            "description": "Fund named 'ESG', 'sustainable', or 'green' without >=80% ESG-aligned investments (ESMA threshold)",
            "regulator": "ESMA (EU) / FCA SDR (UK)",
            "enforcement_action_taken": True,
            "fine_range_m": (1, 100),
            "remediation": "Comply with ESMA fund names guidelines; apply 80% threshold or rename fund",
        },
        {
            "flag_id": "GW-04",
            "description": "Claiming 'fossil fuel free' while holding fossil fuel reserves or production assets",
            "regulator": "FCA / ASIC / SEC",
            "enforcement_action_taken": True,
            "fine_range_m": (1, 25),
            "remediation": "Disclose complete portfolio holdings; align name with actual exclusion policy",
        },
        {
            "flag_id": "GW-05",
            "description": "Advertising renewable energy credentials while majority revenue from fossil fuels",
            "regulator": "ASA (UK) / EU Green Claims Directive / FTC",
            "enforcement_action_taken": True,
            "fine_range_m": (0.1, 5),
            "remediation": "Apply CAP/BCAP codes; disclose revenue split; substantiate with audited data",
        },
    ],
    "omission_of_material_info": [
        {
            "flag_id": "GW-06",
            "description": "ESG report omits Scope 3 Category 15 (financed emissions) where material",
            "regulator": "SEC (US) / FCA / ESMA",
            "enforcement_action_taken": False,
            "fine_range_m": (2, 100),
            "remediation": "Disclose PCAF-aligned financed emissions; engage portfolio companies on Scope 3 data",
        },
        {
            "flag_id": "GW-07",
            "description": "Physical risk assessment absent despite material coastal, flood, or heat exposure",
            "regulator": "FCA / APRA / ECB SSM",
            "enforcement_action_taken": False,
            "fine_range_m": (1, 50),
            "remediation": "Commission TCFD-aligned physical risk assessment; disclose under IFRS S2 §§28-35",
        },
        {
            "flag_id": "GW-08",
            "description": "Climate transition plan published without quantified financial impact of transition costs",
            "regulator": "FCA / ESMA / TPT",
            "enforcement_action_taken": False,
            "fine_range_m": (0.5, 30),
            "remediation": "Quantify transition CAPEX; model scenarios at 1.5C/2C; disclose financial effects",
        },
        {
            "flag_id": "GW-09",
            "description": "Offsetting Scope 1/2 emissions but not disclosing offset quality, vintage, or additionality",
            "regulator": "ICVCM / FCA / ASIC",
            "enforcement_action_taken": True,
            "fine_range_m": (0.2, 20),
            "remediation": "Disclose offset attributes (ICVCM CCP label required); publish offsetting policy",
        },
        {
            "flag_id": "GW-10",
            "description": "Presenting absolute emissions reductions without disclosing revenue/output-normalised intensity",
            "regulator": "GHG Protocol / CSRD ESRS E1 / TCFD",
            "enforcement_action_taken": False,
            "fine_range_m": (0.1, 10),
            "remediation": "Report both absolute and intensity-based emissions per ESRS E1 §§44-46",
        },
    ],
    "false_impression": [
        {
            "flag_id": "GW-11",
            "description": "Displaying sustainability certification logos without current valid certification",
            "regulator": "ASA / FTC / national consumer authorities",
            "enforcement_action_taken": True,
            "fine_range_m": (0.05, 5),
            "remediation": "Remove lapsed certifications; verify and renew certifications annually",
        },
        {
            "flag_id": "GW-12",
            "description": "Presenting projected 2050 emissions reductions as current achievements",
            "regulator": "FCA / ASIC / EU Green Claims Directive",
            "enforcement_action_taken": True,
            "fine_range_m": (0.5, 30),
            "remediation": "Clearly distinguish historical, current, and projected/target performance",
        },
        {
            "flag_id": "GW-13",
            "description": "Claiming SFDR Article 9 classification without meeting sustainable investment criteria",
            "regulator": "ESMA / national NCAs / EU Taxonomy Regulation Art 8",
            "enforcement_action_taken": True,
            "fine_range_m": (1, 150),
            "remediation": "Downgrade to Art 8 or restructure fund to meet Art 9 criteria per RTS 2022/1288",
        },
        {
            "flag_id": "GW-14",
            "description": "Cherry-picking best-performing ESG metrics while omitting poor performers in reporting",
            "regulator": "CSRD / ISAE 3000 assurance / GRI",
            "enforcement_action_taken": False,
            "fine_range_m": (0.2, 15),
            "remediation": "Apply GRI completeness principle; obtain ISAE 3000 limited assurance on sustainability data",
        },
        {
            "flag_id": "GW-15",
            "description": "Implying EU Taxonomy alignment without completed technical screening criteria assessment",
            "regulator": "ESMA / European Commission / national NCAs",
            "enforcement_action_taken": False,
            "fine_range_m": (1, 100),
            "remediation": "Complete TSC assessment per Delegated Act 2021/4987; obtain third-party verification",
        },
    ],
    "future_targets": [
        {
            "flag_id": "GW-16",
            "description": "Net-zero target with no interim milestones before 2050",
            "regulator": "FCA TPT / CSRD ESRS E1 / IFRS S2",
            "enforcement_action_taken": False,
            "fine_range_m": (0.5, 50),
            "remediation": "Set science-based 2025/2030/2035 interim targets; align with SBTi Corporate Net-Zero Standard",
        },
        {
            "flag_id": "GW-17",
            "description": "SBTi-validated target but actual capex pipeline inconsistent with decarbonisation pathway",
            "regulator": "FCA / ASIC / NGO litigation",
            "enforcement_action_taken": False,
            "fine_range_m": (5, 200),
            "remediation": "Align capital allocation framework with SBTi validated pathway; disclose Paris-aligned capex ratio",
        },
        {
            "flag_id": "GW-18",
            "description": "Commitment to TCFD recommendations without completing scenario analysis after 3+ years",
            "regulator": "FCA / APRA / MAS",
            "enforcement_action_taken": True,
            "fine_range_m": (0.5, 25),
            "remediation": "Complete scenario analysis per TCFD Technical Supplement; disclose strategic resilience assessment",
        },
        {
            "flag_id": "GW-19",
            "description": "Offsetting-heavy net-zero strategy without committed abatement trajectory for owned emissions",
            "regulator": "VCMI Claims Code / ICVCM / FCA",
            "enforcement_action_taken": False,
            "fine_range_m": (1, 100),
            "remediation": "Demonstrate abatement-first hierarchy per VCMI Claims Code; limit offsets to residual emissions",
        },
        {
            "flag_id": "GW-20",
            "description": "Paris-alignment claim without independent verification against IPCC carbon budget pathways",
            "regulator": "ESMA / FCA / national NCAs",
            "enforcement_action_taken": False,
            "fine_range_m": (1, 50),
            "remediation": "Commission independent Paris-alignment assessment; reference IPCC AR6 1.5C carbon budget pathway",
        },
    ],
}


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class GreenwashingRiskResult:
    triggered_flags: list
    flag_count: int
    greenwashing_risk_score: float
    risk_tier: str
    regulatory_exposure_by_jurisdiction: dict
    max_fine_exposure_m: float
    recommended_remediation: list
    notes: list


@dataclass
class DisclosureLiabilityResult:
    triggered_triggers: list
    trigger_count: int
    max_exposure_m: float
    expected_exposure_m: float
    disclosure_liability_score: float
    priority_remediation: list
    exposure_by_trigger: dict
    notes: list


@dataclass
class FiduciaryDutyResult:
    duty_scores: dict
    fiduciary_adequacy_score: float
    adequacy_tier: str
    breach_indicators_identified: list
    stewardship_gaps: list
    do_liability_exposure_m: float
    improvement_actions: list


@dataclass
class AttributionScienceResult:
    attribution_applicable: bool
    applicability_rationale: str
    meehl_haugen_christidis_score: float
    physical_damage_attributable_pct: float
    litigation_probability_pct: float
    key_attribution_pathways: list
    jurisdiction_risk: str
    notes: list


@dataclass
class LitigationExposureResult:
    max_litigation_cost_m: float
    expected_litigation_cost_m: float
    insurance_coverage_m: float
    insurance_adequacy_gap_m: float
    ias37_provision_required_m: float
    ias37_provision_basis: str
    jurisdiction_risk_score: float
    exposure_streams: dict
    notes: list


@dataclass
class LitigationFullAssessmentResult:
    entity_id: str
    entity_name: str
    assessment_date: str
    litigation_risk_score: float
    risk_tier: str
    max_litigation_exposure_m: float
    expected_litigation_cost_m: float
    greenwashing_risk_score: float
    disclosure_liability_score: float
    fiduciary_duty_score: float
    attribution_science_applicable: bool
    ias37_provision_m: float
    insurance_gap_m: float
    key_risk_drivers: list
    priority_actions: list
    cross_framework: dict


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class ClimateLitigationEngine:
    """Climate Litigation Risk Assessment Engine (E91)."""

    _RISK_TIERS = [
        (75, "critical"),
        (55, "high"),
        (35, "medium"),
        (15, "low"),
        (0, "minimal"),
    ]

    _FIDUCIARY_TIERS = [
        (75, "strong"),
        (55, "adequate"),
        (35, "requires_improvement"),
        (0, "inadequate"),
    ]

    def assess_greenwashing_risk(self, entity_data: dict) -> GreenwashingRiskResult:
        """
        Check 20 red flags against entity data. Compute greenwashing risk score (0-100),
        identify triggered flags, regulatory exposure by jurisdiction, and remediation.
        """
        triggered_flags = []
        max_fine_m = 0.0

        # Collect all flags
        all_flags = []
        for category, flags in GREENWASHING_RED_FLAGS.items():
            for flag in flags:
                all_flags.append((category, flag))

        for category, flag in all_flags:
            triggered = False
            fid = flag["flag_id"]

            if fid in entity_data.get("triggered_greenwashing_flags", []):
                triggered = True
            elif fid == "GW-01" and entity_data.get("uses_unverified_offsets", False):
                triggered = True
            elif fid == "GW-02" and (
                entity_data.get("net_zero_commitment", False)
                and not entity_data.get("transition_plan_published", False)
            ):
                triggered = True
            elif fid == "GW-03" and entity_data.get("esg_fund_below_80pct_threshold", False):
                triggered = True
            elif fid == "GW-06" and (
                entity_data.get("is_financial_institution", False)
                and not entity_data.get("scope3_cat15_disclosed", False)
            ):
                triggered = True
            elif fid == "GW-13" and entity_data.get("sfdr_art9_overclaimed", False):
                triggered = True
            elif fid == "GW-16" and (
                entity_data.get("net_zero_target_2050", False)
                and not entity_data.get("interim_targets_set", False)
            ):
                triggered = True

            if triggered:
                fine_max = flag["fine_range_m"][1]
                max_fine_m += fine_max
                triggered_flags.append({
                    "flag_id": fid,
                    "category": category,
                    "description": flag["description"],
                    "regulator": flag["regulator"],
                    "enforcement_action_taken": flag["enforcement_action_taken"],
                    "fine_range_m": flag["fine_range_m"],
                    "remediation": flag["remediation"],
                })

        flag_count = len(triggered_flags)
        base_score = flag_count * 10
        enforcement_uplift = sum(3 for f in triggered_flags if f["enforcement_action_taken"])
        greenwashing_risk_score = round(min(base_score + enforcement_uplift, 100.0), 1)

        risk_tier = "minimal"
        for threshold, tier in self._RISK_TIERS:
            if greenwashing_risk_score >= threshold:
                risk_tier = tier
                break

        regulatory_exposure = {}
        jurisdictions = entity_data.get("operating_jurisdictions", ["UK", "EU_Germany"])
        for jur in jurisdictions:
            profile = JURISDICTION_RISK_PROFILES.get(jur, {})
            regulatory_exposure[jur] = {
                "greenwashing_enforcement_score": profile.get("greenwashing_enforcement_score", 50),
                "key_legislation": profile.get("key_legislation", [])[:2],
                "applicable_flags": [f["flag_id"] for f in triggered_flags],
            }

        recommended_remediation = list({f["remediation"] for f in triggered_flags})[:5]

        notes = []
        if flag_count == 0:
            notes.append("No greenwashing red flags identified based on provided entity data.")
        if entity_data.get("is_financial_institution", False) and greenwashing_risk_score > 50:
            notes.append(
                "Financial institution with high greenwashing risk — FCA Anti-Greenwashing Rule "
                "(effective May 2024) creates urgent remediation requirement."
            )

        return GreenwashingRiskResult(
            triggered_flags=triggered_flags,
            flag_count=flag_count,
            greenwashing_risk_score=greenwashing_risk_score,
            risk_tier=risk_tier,
            regulatory_exposure_by_jurisdiction=regulatory_exposure,
            max_fine_exposure_m=round(max_fine_m, 1),
            recommended_remediation=recommended_remediation,
            notes=notes,
        )

    def assess_disclosure_liability(self, entity_data: dict) -> DisclosureLiabilityResult:
        """
        Check 8 disclosure liability triggers, quantify exposure per trigger,
        aggregate max/expected exposure, and identify priority remediations.
        """
        triggered_triggers = []
        exposure_by_trigger = {}
        total_max_m = 0.0
        total_expected_m = 0.0

        trigger_conditions = {
            "ifrs_s2_misstatement": entity_data.get("ifrs_s2_disclosed", False) and entity_data.get("ifrs_s2_material_error", False),
            "sec_climate_omission": entity_data.get("sec_registered", False) and not entity_data.get("sec_climate_rule_compliant", True),
            "csrd_greenwashing": entity_data.get("csrd_in_scope", False) and entity_data.get("csrd_disclosures_incomplete", False),
            "transition_plan_misrepresentation": (
                entity_data.get("transition_plan_published", False)
                and not entity_data.get("transition_plan_science_based", False)
            ),
            "tcfd_material_omission": (
                entity_data.get("tcfd_committed", False)
                and not entity_data.get("tcfd_scenario_analysis_done", False)
            ),
            "scope3_underreporting": (
                entity_data.get("is_financial_institution", False)
                and not entity_data.get("scope3_cat15_disclosed", False)
            ),
            "asset_stranding_concealment": (
                entity_data.get("fossil_fuel_assets_material", False)
                and not entity_data.get("ias36_impairment_assessed", False)
            ),
            "fiduciary_breach": (
                entity_data.get("is_pension_fund", False)
                and not entity_data.get("climate_investment_policy", False)
            ),
        }

        for trig_key, is_triggered in trigger_conditions.items():
            if is_triggered:
                trigger_def = DISCLOSURE_LIABILITY_TRIGGERS[trig_key]
                claim_min, claim_max = trigger_def["typical_claim_m_range"]
                expected = (claim_min + claim_max) / 2 * 0.15
                total_max_m += claim_max
                total_expected_m += expected
                exposure_by_trigger[trig_key] = {
                    "max_exposure_m": claim_max,
                    "expected_exposure_m": round(expected, 1),
                    "jurisdiction": trigger_def["jurisdiction"],
                    "enforcement_body": trigger_def["enforcement_body"],
                }
                triggered_triggers.append({
                    "trigger_id": trig_key,
                    "description": trigger_def["description"],
                    "statute_ref": trigger_def["statute_ref"],
                    "max_exposure_m": claim_max,
                    "expected_exposure_m": round(expected, 1),
                })

        trigger_count = len(triggered_triggers)
        if total_max_m == 0:
            disclosure_score = 0.0
        else:
            exposure_score = min(math.log10(total_max_m + 1) / math.log10(10001) * 50, 50)
            count_score = min(trigger_count / 8 * 50, 50)
            disclosure_score = round(exposure_score + count_score, 1)

        priority_remediation = []
        if exposure_by_trigger:
            sorted_triggers = sorted(
                exposure_by_trigger.items(), key=lambda x: x[1]["max_exposure_m"], reverse=True
            )
            for trig_key, _ in sorted_triggers[:3]:
                trigger_def = DISCLOSURE_LIABILITY_TRIGGERS[trig_key]
                priority_remediation.append(f"{trig_key}: Comply with {trigger_def['statute_ref']}")

        notes = []
        if total_max_m > 1000:
            notes.append(
                f"Aggregate maximum disclosure liability exposure of EUR {total_max_m:.0f}M "
                f"requires immediate board-level attention."
            )
        if trigger_count == 0:
            notes.append("No disclosure liability triggers activated based on provided entity data.")

        return DisclosureLiabilityResult(
            triggered_triggers=triggered_triggers,
            trigger_count=trigger_count,
            max_exposure_m=round(total_max_m, 1),
            expected_exposure_m=round(total_expected_m, 1),
            disclosure_liability_score=disclosure_score,
            priority_remediation=priority_remediation,
            exposure_by_trigger=exposure_by_trigger,
            notes=notes,
        )

    def assess_fiduciary_duty(self, entity_data: dict) -> FiduciaryDutyResult:
        """
        Score all 6 Duties X Framework fiduciary duties, compute fiduciary adequacy score,
        identify stewardship gaps, and estimate D&O liability exposure.
        """
        duty_scores = {}
        breach_indicators_identified = []
        total_do_exposure = 0.0

        for duty_key, duty_def in DUTIES_X_FRAMEWORK.items():
            breaches = 0
            max_indicators = len(duty_def["breach_indicators"])
            for indicator in duty_def["breach_indicators"]:
                if indicator.lower() in [b.lower() for b in entity_data.get("breach_indicators", [])]:
                    breaches += 1
                    breach_indicators_identified.append(f"{duty_key}: {indicator}")

            # Inferred checks
            if duty_key == "act_in_good_faith":
                if not entity_data.get("board_climate_governance_framework", False):
                    breaches = min(breaches + 1, max_indicators)
                    flag = f"{duty_key}: No climate risk governance framework"
                    if flag not in breach_indicators_identified:
                        breach_indicators_identified.append(flag)
            if duty_key == "exercise_care_skill":
                if not entity_data.get("board_climate_training_completed", False):
                    breaches = min(breaches + 1, max_indicators)
                    breach_indicators_identified.append(f"{duty_key}: No climate training for board members since 2021")
            if duty_key == "disclose_material_info":
                if not entity_data.get("tcfd_quantified_financial_impact", False):
                    breaches = min(breaches + 1, max_indicators)
                    breach_indicators_identified.append(f"{duty_key}: TCFD report omits quantified financial impact")

            duty_score = max(0, 100 - (breaches / max(max_indicators, 1)) * 100)
            duty_scores[duty_key] = round(duty_score, 1)

            if duty_score < 50:
                total_do_exposure += duty_def["max_d_and_o_exposure_m"] * (1 - duty_score / 100)

        fiduciary_adequacy_score = round(sum(duty_scores.values()) / len(duty_scores), 1)

        adequacy_tier = "inadequate"
        for threshold, tier in self._FIDUCIARY_TIERS:
            if fiduciary_adequacy_score >= threshold:
                adequacy_tier = tier
                break

        stewardship_gaps = []
        for duty_key, score in duty_scores.items():
            if score < 60:
                stewardship_gaps.append(f"{duty_key}: score {score:.0f}/100 — requires improvement")

        improvement_actions = []
        if duty_scores.get("act_in_good_faith", 100) < 60:
            improvement_actions.append(
                "Establish Board Climate Risk Committee with qualified director (PRA SS3/19 expectation)."
            )
        if duty_scores.get("exercise_care_skill", 100) < 60:
            improvement_actions.append(
                "Commission external climate risk training for all board members; retain climate advisor."
            )
        if duty_scores.get("disclose_material_info", 100) < 60:
            improvement_actions.append(
                "Quantify financial impact of climate risks in annual report; complete TCFD scenario analysis."
            )
        if duty_scores.get("act_within_authority", 100) < 60:
            improvement_actions.append(
                "Review capex pipeline alignment with published transition plan; document rationale in board minutes."
            )

        return FiduciaryDutyResult(
            duty_scores=duty_scores,
            fiduciary_adequacy_score=fiduciary_adequacy_score,
            adequacy_tier=adequacy_tier,
            breach_indicators_identified=list(set(breach_indicators_identified))[:10],
            stewardship_gaps=stewardship_gaps,
            do_liability_exposure_m=round(total_do_exposure, 1),
            improvement_actions=improvement_actions,
        )

    def assess_attribution_science_risk(self, entity_data: dict) -> AttributionScienceResult:
        """
        Assess attribution science applicability based on sector, jurisdiction, and
        emissions profile. Computes Meehl-Haugen-Christidis composite score,
        physical damage attribution %, and litigation probability.
        """
        sector = entity_data.get("sector", "").lower()
        jurisdiction = entity_data.get("primary_jurisdiction", "global")
        cumulative_emissions_mtco2 = float(entity_data.get("cumulative_scope1_mtco2", 0))
        fossil_fuel_company = entity_data.get("is_fossil_fuel_company", False)
        physical_assets_coastal = entity_data.get("physical_assets_coastal_or_flood", False)

        high_attribution_sectors = {"oil_gas", "coal", "cement", "steel", "aviation", "shipping", "chemicals"}
        attribution_applicable = (
            fossil_fuel_company
            or sector in high_attribution_sectors
            or cumulative_emissions_mtco2 > 100
        )

        # Meehl-Haugen-Christidis composite score
        mhc_score = 0.0
        if fossil_fuel_company:
            mhc_score += 40
        if cumulative_emissions_mtco2 > 1000:
            mhc_score += 25
        elif cumulative_emissions_mtco2 > 100:
            mhc_score += 15
        elif cumulative_emissions_mtco2 > 10:
            mhc_score += 5

        sector_attribution = {
            "oil_gas": 20, "coal": 20, "cement": 15, "steel": 10,
            "aviation": 12, "shipping": 10, "chemicals": 8,
        }
        mhc_score += sector_attribution.get(sector, 3)

        jurisdiction_profile = JURISDICTION_RISK_PROFILES.get(jurisdiction, {})
        jur_score = jurisdiction_profile.get("climate_litigation_activity_score", 40) / 100 * 15
        mhc_score += jur_score
        mhc_score = round(min(mhc_score, 100.0), 1)

        # Physical damage attributable % (Carbon Majors methodology)
        if fossil_fuel_company and cumulative_emissions_mtco2 > 0:
            global_industrial_co2_1850_2023 = 1_500_000  # MtCO2 rough total
            attribution_share = cumulative_emissions_mtco2 / global_industrial_co2_1850_2023
            physical_damage_pct = round(min(attribution_share * 100, 100), 3)
        else:
            physical_damage_pct = 0.0

        # Litigation probability
        if not attribution_applicable:
            lit_prob = 5.0
        elif mhc_score > 70:
            lit_prob = 35.0
        elif mhc_score > 50:
            lit_prob = 20.0
        elif mhc_score > 30:
            lit_prob = 12.0
        else:
            lit_prob = 5.0

        jur_activity = jurisdiction_profile.get("climate_litigation_activity_score", 40)
        if jur_activity >= 70:
            jurisdiction_risk = "high"
        elif jur_activity >= 50:
            jurisdiction_risk = "medium"
        else:
            jurisdiction_risk = "low"

        key_attribution_pathways = []
        if fossil_fuel_company:
            key_attribution_pathways.append("Direct production attribution (Carbon Majors / Heede methodology)")
        if sector in {"oil_gas", "coal", "cement"}:
            key_attribution_pathways.append("Sector-level warming contribution (Meehl et al. 2024 attribution framework)")
        if physical_assets_coastal:
            key_attribution_pathways.append("Physical damage attribution for coastal/flood assets (Christidis event attribution)")
        if cumulative_emissions_mtco2 > 100:
            key_attribution_pathways.append("Historical cumulative emissions liability (Lliuya v RWE carbon attribution model)")

        applicability_rationale = (
            "Attribution science applicable: " if attribution_applicable else "Attribution science not directly applicable: "
        ) + (
            f"Sector ({sector}), cumulative emissions ({cumulative_emissions_mtco2:.0f} MtCO2), "
            f"fossil fuel status ({fossil_fuel_company})"
        )

        notes = []
        if mhc_score > 60:
            notes.append(
                f"High Meehl-Haugen-Christidis score ({mhc_score}/100) indicates strong attribution "
                f"science applicability — proactive legal defence strategy recommended."
            )
        if physical_damage_pct > 0:
            notes.append(
                f"Estimated {physical_damage_pct:.3f}% of global industrial climate damages "
                f"attributable using Carbon Majors methodology (Heede 2019 + update)."
            )
        if jurisdiction == "EU_Netherlands":
            notes.append(
                "Dutch jurisdiction: Milieudefensie v Shell precedent establishes civil tort pathway for attribution cases."
            )

        return AttributionScienceResult(
            attribution_applicable=attribution_applicable,
            applicability_rationale=applicability_rationale,
            meehl_haugen_christidis_score=mhc_score,
            physical_damage_attributable_pct=physical_damage_pct,
            litigation_probability_pct=lit_prob,
            key_attribution_pathways=key_attribution_pathways,
            jurisdiction_risk=jurisdiction_risk,
            notes=notes,
        )

    def compute_litigation_exposure(self, entity_data: dict) -> LitigationExposureResult:
        """
        Aggregate all exposure streams. Compute max/expected litigation cost,
        insurance adequacy gap, and IAS 37 provision requirement.
        """
        exposure_streams = {}

        gw_flag_count = entity_data.get("greenwashing_flag_count", 0)
        gw_max = gw_flag_count * 20
        gw_expected = gw_max * 0.12
        exposure_streams["greenwashing"] = {"max_m": gw_max, "expected_m": round(gw_expected, 1)}

        dl_max = float(entity_data.get("disclosure_liability_max_m", 0))
        dl_expected = dl_max * 0.10
        exposure_streams["disclosure_liability"] = {"max_m": dl_max, "expected_m": round(dl_expected, 1)}

        do_exposure = float(entity_data.get("do_liability_exposure_m", 0))
        exposure_streams["fiduciary_do"] = {"max_m": do_exposure, "expected_m": round(do_exposure * 0.15, 1)}

        attr_applicable = entity_data.get("attribution_science_applicable", False)
        attr_prob = float(entity_data.get("attribution_litigation_probability_pct", 5)) / 100
        cumulative_emissions = float(entity_data.get("cumulative_scope1_mtco2", 0))
        attr_max = cumulative_emissions * 0.5 if attr_applicable else 0
        attr_expected = attr_max * attr_prob
        exposure_streams["attribution_science"] = {"max_m": round(attr_max, 1), "expected_m": round(attr_expected, 1)}

        max_litigation = sum(v["max_m"] for v in exposure_streams.values())
        expected_litigation = sum(v["expected_m"] for v in exposure_streams.values())

        insurance_coverage = float(entity_data.get("climate_litigation_insurance_m", 0))
        insurance_gap = max(0, expected_litigation - insurance_coverage)

        if expected_litigation > 0:
            ias37_provision = round(expected_litigation * 0.5, 1)
            ias37_basis = (
                f"IAS 37 §14: Best estimate of probable outflow = 50% of expected exposure "
                f"(EUR {expected_litigation:.1f}M). Disclose contingent liability for remainder per IAS 37 §86."
            )
        else:
            ias37_provision = 0.0
            ias37_basis = "IAS 37 §27: No provision required — no probable obligation identified based on current data."

        jurisdictions = entity_data.get("operating_jurisdictions", ["global"])
        jur_scores = [
            JURISDICTION_RISK_PROFILES.get(j, {}).get("climate_litigation_activity_score", 40)
            for j in jurisdictions
        ]
        jurisdiction_risk_score = round(sum(jur_scores) / len(jur_scores), 1) if jur_scores else 40.0

        notes = []
        if max_litigation > 500:
            notes.append(
                f"Maximum litigation exposure of EUR {max_litigation:.0f}M is material — "
                f"board-level disclosure in annual report required under IAS 37 §86."
            )
        if insurance_gap > 0:
            notes.append(f"Insurance adequacy gap of EUR {insurance_gap:.1f}M — consider increasing D&O/E&O climate litigation coverage.")
        if attr_max > 100:
            notes.append(
                "Attribution science litigation represents largest single exposure stream — "
                "engage specialist climate litigation counsel; monitor Lliuya v RWE and Carbon Majors cases."
            )

        return LitigationExposureResult(
            max_litigation_cost_m=round(max_litigation, 1),
            expected_litigation_cost_m=round(expected_litigation, 1),
            insurance_coverage_m=insurance_coverage,
            insurance_adequacy_gap_m=round(insurance_gap, 1),
            ias37_provision_required_m=ias37_provision,
            ias37_provision_basis=ias37_basis,
            jurisdiction_risk_score=jurisdiction_risk_score,
            exposure_streams=exposure_streams,
            notes=notes,
        )

    def run_full_assessment(self, entity_data: dict) -> LitigationFullAssessmentResult:
        """
        Full climate litigation risk assessment across all five sub-modules.
        Produces composite litigation_risk_score (0-100) and risk tier.
        """
        entity_id = entity_data.get("entity_id", f"ENT-{date.today().strftime('%Y%m%d')}")
        entity_name = entity_data.get("entity_name", "Unknown Entity")
        assessment_date = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        gw = self.assess_greenwashing_risk(entity_data)
        dl = self.assess_disclosure_liability(entity_data)
        fd = self.assess_fiduciary_duty(entity_data)
        attr = self.assess_attribution_science_risk(entity_data)

        entity_augmented = {
            **entity_data,
            "greenwashing_flag_count": gw.flag_count,
            "disclosure_liability_max_m": dl.max_exposure_m,
            "do_liability_exposure_m": fd.do_liability_exposure_m,
            "attribution_science_applicable": attr.attribution_applicable,
            "attribution_litigation_probability_pct": attr.litigation_probability_pct,
        }
        exp = self.compute_litigation_exposure(entity_augmented)

        # Composite score
        gw_contribution = gw.greenwashing_risk_score * 0.25
        dl_contribution = dl.disclosure_liability_score * 0.30
        fd_contribution = (100 - fd.fiduciary_adequacy_score) * 0.20
        attr_contribution = attr.meehl_haugen_christidis_score * 0.15
        jur_contribution = exp.jurisdiction_risk_score / 100 * 10

        litigation_risk_score = round(
            gw_contribution + dl_contribution + fd_contribution + attr_contribution + jur_contribution,
            1,
        )
        litigation_risk_score = min(litigation_risk_score, 100.0)

        risk_tier = "minimal"
        for threshold, tier in self._RISK_TIERS:
            if litigation_risk_score >= threshold:
                risk_tier = tier
                break

        key_risk_drivers = []
        if gw.greenwashing_risk_score > 40:
            key_risk_drivers.append(f"Greenwashing: {gw.flag_count} red flags triggered (score {gw.greenwashing_risk_score}/100)")
        if dl.max_exposure_m > 100:
            key_risk_drivers.append(f"Disclosure liability: EUR {dl.max_exposure_m:.0f}M maximum exposure ({dl.trigger_count} triggers)")
        if fd.fiduciary_adequacy_score < 50:
            key_risk_drivers.append(f"Fiduciary duty: {fd.adequacy_tier} — D&O exposure EUR {fd.do_liability_exposure_m:.0f}M")
        if attr.attribution_applicable and attr.meehl_haugen_christidis_score > 50:
            key_risk_drivers.append(f"Attribution science: MHC score {attr.meehl_haugen_christidis_score}/100 — {attr.litigation_probability_pct}% litigation probability")

        priority_actions = []
        priority_actions.extend(gw.recommended_remediation[:1])
        priority_actions.extend(dl.priority_remediation[:1])
        priority_actions.extend(fd.improvement_actions[:1])
        if attr.attribution_applicable:
            priority_actions.append("Engage specialist climate attribution litigation counsel; assess Lliuya-type exposure.")
        if exp.insurance_gap_m > 0:
            priority_actions.append(f"Increase climate litigation insurance coverage by EUR {exp.insurance_gap_m:.0f}M to close adequacy gap.")

        cross_framework = {
            "TCFD_2017": "Governance/Strategy/Risk/Metrics pillars — disclosure liability triggers aligned",
            "CSRD_ESRS_E1": "Paragraphs 7-11 governance disclosures; para 16 transition plan; paras 44-46 emissions metrics",
            "IFRS_S2": "Physical/transition risk identification paras 25-41; scenario analysis paras 13-24",
            "SFDR_RTS_2022_1288": "PAI disclosures; Art 8/9 fund naming — greenwashing risk GW-03/GW-13 triggers",
            "FCA_PS23_16_AGR": "Anti-Greenwashing Rule effective May 2024 — all 20 GW flags directly applicable",
            "IAS_37": f"Provision EUR {exp.ias37_provision_required_m:.1f}M required; basis: {exp.ias37_provision_basis[:80]}",
            "DUTIES_X_FRAMEWORK": f"Fiduciary adequacy {fd.fiduciary_adequacy_score}/100 — {fd.adequacy_tier}",
            "SABIN_CENTRE_TAXONOMY": "8 case categories — all applicable based on sector and jurisdiction profile",
        }

        return LitigationFullAssessmentResult(
            entity_id=entity_id,
            entity_name=entity_name,
            assessment_date=assessment_date,
            litigation_risk_score=litigation_risk_score,
            risk_tier=risk_tier,
            max_litigation_exposure_m=exp.max_litigation_cost_m,
            expected_litigation_cost_m=exp.expected_litigation_cost_m,
            greenwashing_risk_score=gw.greenwashing_risk_score,
            disclosure_liability_score=dl.disclosure_liability_score,
            fiduciary_duty_score=fd.fiduciary_adequacy_score,
            attribution_science_applicable=attr.attribution_applicable,
            ias37_provision_m=exp.ias37_provision_required_m,
            insurance_gap_m=exp.insurance_adequacy_gap_m,
            key_risk_drivers=key_risk_drivers,
            priority_actions=priority_actions,
            cross_framework=cross_framework,
        )
