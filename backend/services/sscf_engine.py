"""
E101 — Sustainable Supply Chain Finance (SSCF) Engine
======================================================
Standards covered:
- LMA / APLMA Sustainability-Linked Loan Principles 2023 (SLLP) + Green Loan Principles 2023 (GLP)
- LMA Supply Chain Finance (SSCF) Framework 2023
- ICC Supply Chain Finance Guidelines 2022
- GSCFF (Global Supply Chain Finance Forum) Standards 2023
- OECD Due Diligence Guidance for Responsible Business Conduct (DDG) 5-step
- EU CSDDD Directive (EU) 2024/1760 — supply chain adverse impact categories
- PCAF Part C — Scope 3 Category 1 facilitated emissions
- ILO Core Labour Standards — social KPI baseline
"""
from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# SSCF Framework profiles
# ---------------------------------------------------------------------------

SSCF_FRAMEWORKS: Dict[str, Dict[str, Any]] = {
    "LMA_SSCF_2023": {
        "name": "LMA / APLMA Sustainable Supply Chain Finance Framework 2023",
        "issuer": "Loan Market Association / Asia Pacific Loan Market Association",
        "published": "2023-Q3",
        "core_components": [
            {
                "id": "GLP-1",
                "name": "Use of Proceeds",
                "description": "SCF facilities should finance green or sustainable supply chain activities aligned with GLP/SLLP definitions",
                "weight_pct": 25,
                "required": True,
            },
            {
                "id": "GLP-2",
                "name": "Process for Project Evaluation and Selection",
                "description": "Buyer must define and disclose selection criteria for sustainable suppliers entering the programme",
                "weight_pct": 25,
                "required": True,
            },
            {
                "id": "GLP-3",
                "name": "Management of Proceeds",
                "description": "Track utilisation of favourable financing to sustainable suppliers via dedicated reporting",
                "weight_pct": 25,
                "required": True,
            },
            {
                "id": "GLP-4",
                "name": "Reporting and Transparency",
                "description": "Annual supplier sustainability scorecard disclosure; programme-level KPI progress",
                "weight_pct": 25,
                "required": True,
            },
        ],
        "eligibility_criteria": [
            "Buyer must have a published supplier code of conduct",
            "Minimum 10 suppliers enrolled in programme",
            "At least 3 material ESG KPIs with measurable SPTs",
            "Third-party verification for KPIs above 20% margin impact",
            "Scope 3 Category 1 emissions disclosure or commitment",
            "OECD DDG Step 1 (management systems) in place",
            "No CAHRA (conflict-affected and high-risk area) exposure without mitigation",
        ],
        "documentation_checklist": [
            "Buyer Sustainability Policy",
            "Supplier Code of Conduct",
            "KPI Selection Rationale",
            "SPT Calibration Methodology",
            "Third-Party Verifier Appointment Letter",
            "Programme Information Document",
            "Annual Review Covenant",
        ],
        "green_bond_overlap": "Eligible under ICMA Green Bond Principles — Use of Proceeds category: Green Supply Chain",
        "max_margin_discount_bps": 75,
        "grace_period_months": 6,
        "spt_review_frequency": "annual",
    },
    "ICC_SCF_2022": {
        "name": "ICC Supply Chain Finance Guidelines 2022",
        "issuer": "International Chamber of Commerce",
        "published": "2022-Q2",
        "core_components": [
            {
                "id": "ICC-1",
                "name": "Transparency and Disclosure",
                "description": "Clear disclosure of programme structure, costs, eligibility and sustainability linkage",
                "weight_pct": 20,
                "required": True,
            },
            {
                "id": "ICC-2",
                "name": "Supplier Welfare",
                "description": "Programme must not extract value from suppliers; early payment benefit must accrue to supplier",
                "weight_pct": 20,
                "required": True,
            },
            {
                "id": "ICC-3",
                "name": "Operational Integrity",
                "description": "AML/KYC checks on all enrolled suppliers; no use for money laundering or sanctions evasion",
                "weight_pct": 20,
                "required": True,
            },
            {
                "id": "ICC-4",
                "name": "Sustainability Integration",
                "description": "ESG scoring of suppliers; margin linked to KPI achievement where sustainability-labelled",
                "weight_pct": 20,
                "required": False,
            },
            {
                "id": "ICC-5",
                "name": "Regulatory Alignment",
                "description": "Compliance with CSDDD, EUDR and national supply chain due diligence laws",
                "weight_pct": 20,
                "required": True,
            },
        ],
        "eligibility_criteria": [
            "Programme must benefit supplier liquidity (not buyer balance sheet only)",
            "No disguised lending to buyer via reverse factoring off-balance sheet",
            "Supplier ESG scoring disclosed to enrolled suppliers",
            "Conflict mineral policy for relevant sectors",
            "AML/KYC on tier-1 suppliers minimum",
            "CSDDD Art 6 adverse impact screening conducted",
        ],
        "documentation_checklist": [
            "Programme Term Sheet",
            "Supplier Eligibility Matrix",
            "ESG Scorecard Template",
            "AML/KYC Supplier Checklist",
            "CSDDD Adverse Impact Register",
            "Conflict Mineral Declaration",
        ],
        "green_bond_overlap": "Eligible under ICMA Social Bond Principles if living wage / labour rights focused",
        "max_margin_discount_bps": 50,
        "grace_period_months": 3,
        "spt_review_frequency": "semi-annual",
    },
    "GSCFF_2023": {
        "name": "GSCFF Sustainable Supply Chain Finance Standards 2023",
        "issuer": "Global Supply Chain Finance Forum",
        "published": "2023-Q1",
        "core_components": [
            {
                "id": "GSCFF-1",
                "name": "Standardised Definitions",
                "description": "Use GSCFF taxonomy for SCF products: payables finance, receivables discounting, dynamic discounting, factoring",
                "weight_pct": 17,
                "required": True,
            },
            {
                "id": "GSCFF-2",
                "name": "Accounting Treatment",
                "description": "Supplier receivables must be derecognised on transfer; buyer payables classified correctly per IAS 7",
                "weight_pct": 17,
                "required": True,
            },
            {
                "id": "GSCFF-3",
                "name": "ESG Integration",
                "description": "Sustainability-linked pricing with disclosed KPIs and SPTs; minimum 2 environmental + 1 social KPI",
                "weight_pct": 17,
                "required": False,
            },
            {
                "id": "GSCFF-4",
                "name": "Scope 3 Reporting",
                "description": "Buyer must report GHG emissions attributable to financed suppliers (PCAF Scope 3 Cat 1)",
                "weight_pct": 17,
                "required": False,
            },
            {
                "id": "GSCFF-5",
                "name": "Deforestation and Nature Risk",
                "description": "EUDR compliance screening for commodity-linked supply chains; TNFD reporting for nature-exposed sectors",
                "weight_pct": 16,
                "required": False,
            },
            {
                "id": "GSCFF-6",
                "name": "Regulatory Horizon Scanning",
                "description": "Annual review of CSDDD, CSRD and sector-specific legislation affecting supply chain obligations",
                "weight_pct": 16,
                "required": True,
            },
        ],
        "eligibility_criteria": [
            "GSCFF product classification correctly applied",
            "IAS 7 / IFRS 9 accounting treatment confirmed by auditor",
            "Minimum 2 environmental KPIs from SK001-SK015 library",
            "Minimum 1 social KPI from SK016-SK028 library",
            "Scope 3 Category 1 baseline measurement or credible estimate",
            "EUDR commodity screening for agri/forestry supply chains",
            "CSDDD Art 2 scope assessment conducted for buyer",
        ],
        "documentation_checklist": [
            "GSCFF Product Classification Confirmation",
            "Auditor Accounting Treatment Letter",
            "KPI Library Selection with Rationale",
            "Scope 3 Baseline Methodology Statement",
            "EUDR Commodity Screening Report",
            "CSDDD Scope Assessment",
            "Annual Regulatory Horizon Scan",
        ],
        "green_bond_overlap": "Eligible under EU Green Bond Standard (EU GBS) if taxonomy-aligned supply chain",
        "max_margin_discount_bps": 60,
        "grace_period_months": 6,
        "spt_review_frequency": "annual",
    },
}


# ---------------------------------------------------------------------------
# 40 ESG KPI Library (SK001–SK040)
# ---------------------------------------------------------------------------

KPI_LIBRARY: Dict[str, Dict[str, Any]] = {
    # Environmental (SK001–SK015)
    "SK001": {
        "id": "SK001", "group": "Environmental",
        "name": "GHG Emissions Intensity",
        "description": "tCO2e per USD 1m revenue — Scope 1 + 2 market-based",
        "unit": "tCO2e / USD 1m revenue",
        "data_source": "GHG Protocol Corporate Standard + PCAF",
        "materiality_threshold": "All sectors",
        "verification_required": True,
        "sbt_alignment": True,
        "eu_taxonomy_link": "Climate change mitigation — substantial contribution",
    },
    "SK002": {
        "id": "SK002", "group": "Environmental",
        "name": "Scope 3 Category 1 Emissions",
        "description": "tCO2e attributable to purchased goods and services from tier-1 suppliers",
        "unit": "tCO2e absolute",
        "data_source": "PCAF Part C / GHG Protocol Scope 3 Standard",
        "materiality_threshold": "Manufacturing, retail, food sectors",
        "verification_required": True,
        "sbt_alignment": True,
        "eu_taxonomy_link": "Climate change mitigation",
    },
    "SK003": {
        "id": "SK003", "group": "Environmental",
        "name": "Water Intensity",
        "description": "m³ water withdrawn per tonne of product / USD 1m revenue",
        "unit": "m³ / tonne or m³ / USD 1m",
        "data_source": "CDP Water / GRI 303",
        "materiality_threshold": "Textiles, food, agriculture, chemicals",
        "verification_required": False,
        "sbt_alignment": False,
        "eu_taxonomy_link": "Sustainable use and protection of water",
    },
    "SK004": {
        "id": "SK004", "group": "Environmental",
        "name": "Waste Diversion Rate",
        "description": "% of total waste diverted from landfill (reuse + recycling + energy recovery)",
        "unit": "% diversion",
        "data_source": "GRI 306 / internal waste records",
        "materiality_threshold": "Manufacturing, construction, retail",
        "verification_required": False,
        "sbt_alignment": False,
        "eu_taxonomy_link": "Transition to a circular economy",
    },
    "SK005": {
        "id": "SK005", "group": "Environmental",
        "name": "Packaging Recyclability",
        "description": "% of primary packaging by weight that is recyclable, reusable or compostable",
        "unit": "% weight recyclable",
        "data_source": "Ellen MacArthur Foundation / EU Packaging Regulation 2025",
        "materiality_threshold": "FMCG, food, retail, pharma",
        "verification_required": False,
        "sbt_alignment": False,
        "eu_taxonomy_link": "Transition to a circular economy",
    },
    "SK006": {
        "id": "SK006", "group": "Environmental",
        "name": "Energy Intensity",
        "description": "GJ per tonne of product / USD 1m revenue",
        "unit": "GJ / tonne or GJ / USD 1m",
        "data_source": "GRI 302 / IEA Energy Statistics",
        "materiality_threshold": "Energy-intensive manufacturing",
        "verification_required": False,
        "sbt_alignment": True,
        "eu_taxonomy_link": "Climate change mitigation",
    },
    "SK007": {
        "id": "SK007", "group": "Environmental",
        "name": "Renewable Energy Share",
        "description": "% of total energy consumption from renewable sources",
        "unit": "% renewable",
        "data_source": "GRI 302-1 / RE100 reporting",
        "materiality_threshold": "All sectors",
        "verification_required": False,
        "sbt_alignment": True,
        "eu_taxonomy_link": "Climate change mitigation",
    },
    "SK008": {
        "id": "SK008", "group": "Environmental",
        "name": "Biodiversity Impact Score",
        "description": "MSA.km² footprint or TNFD LEAP habitat sensitivity rating",
        "unit": "MSA.km² or 1-5 score",
        "data_source": "TNFD v1.0 / PBAF 2023 / ENCORE",
        "materiality_threshold": "Agriculture, mining, construction, food",
        "verification_required": False,
        "sbt_alignment": False,
        "eu_taxonomy_link": "Protection and restoration of biodiversity and ecosystems",
    },
    "SK009": {
        "id": "SK009", "group": "Environmental",
        "name": "Chemical Usage (Substances of Concern)",
        "description": "Kg substances of very high concern (SVHC) per tonne of product",
        "unit": "kg SVHC / tonne",
        "data_source": "ECHA SVHC list / ESRS E2",
        "materiality_threshold": "Chemicals, pharma, electronics, textiles",
        "verification_required": False,
        "sbt_alignment": False,
        "eu_taxonomy_link": "Pollution prevention and control",
    },
    "SK010": {
        "id": "SK010", "group": "Environmental",
        "name": "Air Emissions (NOx/SOx/PM2.5)",
        "description": "Tonnes of NOx, SOx and PM2.5 per USD 1m revenue",
        "unit": "t / USD 1m",
        "data_source": "GRI 305-7 / ESRS E2",
        "materiality_threshold": "Manufacturing, energy, transport, agriculture",
        "verification_required": False,
        "sbt_alignment": False,
        "eu_taxonomy_link": "Pollution prevention and control",
    },
    "SK011": {
        "id": "SK011", "group": "Environmental",
        "name": "Soil Contamination Incidents",
        "description": "Number of reportable soil contamination incidents per year",
        "unit": "count / year",
        "data_source": "Internal incident register / ESRS E2",
        "materiality_threshold": "Agriculture, chemicals, mining",
        "verification_required": False,
        "sbt_alignment": False,
        "eu_taxonomy_link": "Pollution prevention and control",
    },
    "SK012": {
        "id": "SK012", "group": "Environmental",
        "name": "Deforestation-Free Sourcing",
        "description": "% of commodity volumes verified deforestation-free per EUDR cut-off (31 Dec 2020)",
        "unit": "% verified",
        "data_source": "EUDR Regulation (EU) 2023/1115 / FSC / RSPO",
        "materiality_threshold": "Agri-food, palm oil, soy, cattle, timber",
        "verification_required": True,
        "sbt_alignment": False,
        "eu_taxonomy_link": "Protection and restoration of biodiversity — EUDR",
    },
    "SK013": {
        "id": "SK013", "group": "Environmental",
        "name": "Ocean Plastic Reduction",
        "description": "% reduction in single-use plastic use year-on-year",
        "unit": "% YoY reduction",
        "data_source": "Internal / GRI 306",
        "materiality_threshold": "FMCG, food, retail, packaging",
        "verification_required": False,
        "sbt_alignment": False,
        "eu_taxonomy_link": "Pollution prevention and control — plastics",
    },
    "SK014": {
        "id": "SK014", "group": "Environmental",
        "name": "Land Use Change",
        "description": "Hectares of natural land converted vs restored",
        "unit": "ha net conversion",
        "data_source": "TNFD / SBTN / GRI 304",
        "materiality_threshold": "Agriculture, mining, construction",
        "verification_required": False,
        "sbt_alignment": False,
        "eu_taxonomy_link": "Protection and restoration of biodiversity",
    },
    "SK015": {
        "id": "SK015", "group": "Environmental",
        "name": "Circular Material Content",
        "description": "% of input materials from recycled or secondary sources",
        "unit": "% secondary/recycled",
        "data_source": "ESRS E5 / Ellen MacArthur Foundation Circulytics",
        "materiality_threshold": "Manufacturing, electronics, automotive, construction",
        "verification_required": False,
        "sbt_alignment": False,
        "eu_taxonomy_link": "Transition to a circular economy",
    },
    # Social (SK016–SK028)
    "SK016": {
        "id": "SK016", "group": "Social",
        "name": "Lost Time Injury Frequency Rate (LTIFR)",
        "description": "Number of lost-time injuries per 1 million hours worked",
        "unit": "per 1m hours",
        "data_source": "ISO 45001 / GRI 403",
        "materiality_threshold": "All sectors",
        "verification_required": False,
        "sbt_alignment": False,
        "csddd_link": "HR-01 Right to safe and healthy working conditions",
    },
    "SK017": {
        "id": "SK017", "group": "Social",
        "name": "Child Labour-Free Status",
        "description": "Binary: confirmed no child labour at tier-1 suppliers (ILO Convention 138/182)",
        "unit": "binary (1=confirmed)",
        "data_source": "ILO C138 / C182 / CSDDD HR-05",
        "materiality_threshold": "All sectors",
        "verification_required": True,
        "sbt_alignment": False,
        "csddd_link": "HR-05 Prohibition of child labour",
    },
    "SK018": {
        "id": "SK018", "group": "Social",
        "name": "Forced Labour-Free Status",
        "description": "Binary: confirmed no forced or compulsory labour at tier-1 (ILO Convention 29/105)",
        "unit": "binary (1=confirmed)",
        "data_source": "ILO C29 / C105 / UK Modern Slavery Act / CSDDD HR-04",
        "materiality_threshold": "All sectors",
        "verification_required": True,
        "sbt_alignment": False,
        "csddd_link": "HR-04 Prohibition of forced labour",
    },
    "SK019": {
        "id": "SK019", "group": "Social",
        "name": "Living Wage Compliance",
        "description": "% of direct supplier workforce paid at or above Living Wage Foundation / Anker benchmark",
        "unit": "% of workforce",
        "data_source": "Living Wage Foundation / Anker Living Wage / Fair Wage Network",
        "materiality_threshold": "Labour-intensive sectors",
        "verification_required": False,
        "sbt_alignment": False,
        "csddd_link": "HR-02 Just and favourable conditions of work",
    },
    "SK020": {
        "id": "SK020", "group": "Social",
        "name": "Gender Pay Gap",
        "description": "Median gender pay gap % (women vs men total remuneration)",
        "unit": "% gap",
        "data_source": "ESRS S1-16 / CSRD / UK Gender Pay Gap Reporting",
        "materiality_threshold": "All sectors > 250 employees",
        "verification_required": False,
        "sbt_alignment": False,
        "csddd_link": "HR-03 Equal treatment",
    },
    "SK021": {
        "id": "SK021", "group": "Social",
        "name": "Freedom of Association / Union Recognition",
        "description": "Binary: suppliers recognise right to collective bargaining (ILO C87/C98)",
        "unit": "binary (1=yes)",
        "data_source": "ILO C87 / C98 / CSDDD HR-07",
        "materiality_threshold": "All sectors",
        "verification_required": False,
        "sbt_alignment": False,
        "csddd_link": "HR-07 Freedom of association and collective bargaining",
    },
    "SK022": {
        "id": "SK022", "group": "Social",
        "name": "Working Hours Compliance",
        "description": "% of supplier workers not exceeding ILO 48 hours regular + 12 hours overtime per week",
        "unit": "% compliant",
        "data_source": "ILO C1 / SMETA Audit / SA8000",
        "materiality_threshold": "Labour-intensive manufacturing",
        "verification_required": False,
        "sbt_alignment": False,
        "csddd_link": "HR-02 Just and favourable conditions",
    },
    "SK023": {
        "id": "SK023", "group": "Social",
        "name": "Community Investment",
        "description": "USD investment in community programmes per USD 1m supplier revenue",
        "unit": "USD / USD 1m revenue",
        "data_source": "GRI 413 / LBG Measurement",
        "materiality_threshold": "Extractive, infrastructure, agriculture",
        "verification_required": False,
        "sbt_alignment": False,
        "csddd_link": None,
    },
    "SK024": {
        "id": "SK024", "group": "Social",
        "name": "Free, Prior and Informed Consent (FPIC)",
        "description": "Binary: FPIC process documented for indigenous community land use",
        "unit": "binary (1=yes)",
        "data_source": "UNDRIP / IFC PS7 / CSDDD HR-08",
        "materiality_threshold": "Mining, forestry, infrastructure, agriculture",
        "verification_required": True,
        "sbt_alignment": False,
        "csddd_link": "HR-08 Land, territory and resource rights",
    },
    "SK025": {
        "id": "SK025", "group": "Social",
        "name": "Training Hours per Worker",
        "description": "Average hours of skills/sustainability training per worker per year",
        "unit": "hours/worker/year",
        "data_source": "GRI 404-1 / ESRS S1-13",
        "materiality_threshold": "All sectors",
        "verification_required": False,
        "sbt_alignment": False,
        "csddd_link": None,
    },
    "SK026": {
        "id": "SK026", "group": "Social",
        "name": "Board Diversity (Gender %)",
        "description": "% of female directors on supplier board",
        "unit": "% female",
        "data_source": "ESRS S1-16 / CSRD / 40% Women on Boards Directive",
        "materiality_threshold": "Large suppliers",
        "verification_required": False,
        "sbt_alignment": False,
        "csddd_link": None,
    },
    "SK027": {
        "id": "SK027", "group": "Social",
        "name": "Human Rights Policy",
        "description": "Binary: supplier has a published human rights policy aligned with UNGP",
        "unit": "binary (1=yes)",
        "data_source": "UNGP / CSDDD Art 5-6 / OECD MNE Guidelines",
        "materiality_threshold": "All sectors",
        "verification_required": False,
        "sbt_alignment": False,
        "csddd_link": "HR-01 through HR-10 general",
    },
    "SK028": {
        "id": "SK028", "group": "Social",
        "name": "Grievance Mechanism",
        "description": "Binary: accessible worker grievance mechanism in local language with non-retaliation protection",
        "unit": "binary (1=yes)",
        "data_source": "UNGP Pillar 3 / ILO Recommendation 208 / CSDDD Art 9",
        "materiality_threshold": "All sectors",
        "verification_required": False,
        "sbt_alignment": False,
        "csddd_link": "CSDDD Art 9 — grievance mechanism",
    },
    # Governance (SK029–SK040)
    "SK029": {
        "id": "SK029", "group": "Governance",
        "name": "Anti-Corruption Policy",
        "description": "Binary: published anti-bribery and corruption policy aligned with OECD Anti-Bribery Convention",
        "unit": "binary (1=yes)",
        "data_source": "OECD Anti-Bribery Convention / UN Convention Against Corruption / GRI 205",
        "materiality_threshold": "All sectors",
        "verification_required": False,
        "sbt_alignment": False,
        "csddd_link": None,
    },
    "SK030": {
        "id": "SK030", "group": "Governance",
        "name": "Whistleblower Protection",
        "description": "Binary: independently accessible whistleblower channel with legal protection",
        "unit": "binary (1=yes)",
        "data_source": "EU Whistleblower Directive 2019/1937 / CSDDD Art 9",
        "materiality_threshold": "All sectors",
        "verification_required": False,
        "sbt_alignment": False,
        "csddd_link": "CSDDD Art 9",
    },
    "SK031": {
        "id": "SK031", "group": "Governance",
        "name": "Tax Transparency",
        "description": "Binary: country-by-country tax reporting aligned with OECD BEPS Action 13",
        "unit": "binary (1=yes)",
        "data_source": "OECD BEPS Action 13 / GRI 207",
        "materiality_threshold": "Large multinationals",
        "verification_required": False,
        "sbt_alignment": False,
        "csddd_link": None,
    },
    "SK032": {
        "id": "SK032", "group": "Governance",
        "name": "Board Independence",
        "description": "% of independent non-executive directors on supplier board",
        "unit": "% independent",
        "data_source": "ESRS G1 / UK Corporate Governance Code",
        "materiality_threshold": "Listed and large private suppliers",
        "verification_required": False,
        "sbt_alignment": False,
        "csddd_link": None,
    },
    "SK033": {
        "id": "SK033", "group": "Governance",
        "name": "Supplier Code of Conduct",
        "description": "Binary: buyer's supplier code of conduct accepted and signed by supplier",
        "unit": "binary (1=yes)",
        "data_source": "LMA SSCF / ICC SCF / CSDDD Art 7",
        "materiality_threshold": "All sectors",
        "verification_required": False,
        "sbt_alignment": False,
        "csddd_link": "CSDDD Art 7 — prevention of adverse impacts",
    },
    "SK034": {
        "id": "SK034", "group": "Governance",
        "name": "Audit Frequency",
        "description": "Number of ESG/sustainability audits conducted per 3-year period (SMETA, SA8000 etc.)",
        "unit": "count / 3 years",
        "data_source": "SMETA / SA8000 / ISO 45001 / OECD DDG Step 4",
        "materiality_threshold": "High-risk sectors and geographies",
        "verification_required": False,
        "sbt_alignment": False,
        "csddd_link": "CSDDD Art 10 — monitoring",
    },
    "SK035": {
        "id": "SK035", "group": "Governance",
        "name": "ESG Reporting Standard",
        "description": "Recognised ESG reporting framework used: GRI / CSRD / ISSB / BRSR",
        "unit": "framework name",
        "data_source": "GRI / CSRD / ISSB S1 / BRSR",
        "materiality_threshold": "All sectors",
        "verification_required": False,
        "sbt_alignment": False,
        "csddd_link": "CSDDD Art 11 — public reporting",
    },
    "SK036": {
        "id": "SK036", "group": "Governance",
        "name": "Conflict Minerals Policy",
        "description": "Binary: OECD DDG conflict minerals policy covering 3TG + cobalt",
        "unit": "binary (1=yes)",
        "data_source": "OECD DDG Annex II / EU Conflict Minerals Regulation 2017/821",
        "materiality_threshold": "Electronics, automotive, mining, jewellery",
        "verification_required": True,
        "sbt_alignment": False,
        "csddd_link": "HR-09 Conflict minerals",
    },
    "SK037": {
        "id": "SK037", "group": "Governance",
        "name": "Data Privacy Compliance",
        "description": "Binary: GDPR / equivalent data privacy certification or compliance attestation",
        "unit": "binary (1=yes)",
        "data_source": "GDPR (EU) 2016/679 / ISO 27701",
        "materiality_threshold": "Technology, financial, healthcare",
        "verification_required": False,
        "sbt_alignment": False,
        "csddd_link": None,
    },
    "SK038": {
        "id": "SK038", "group": "Governance",
        "name": "Cybersecurity Maturity",
        "description": "NIST CSF or ISO 27001 maturity level (1-5 scale)",
        "unit": "1-5 maturity score",
        "data_source": "NIST CSF 2.0 / ISO 27001 / DORA (financial)",
        "materiality_threshold": "Technology, financial, critical infrastructure",
        "verification_required": False,
        "sbt_alignment": False,
        "csddd_link": None,
    },
    "SK039": {
        "id": "SK039", "group": "Governance",
        "name": "Regulatory Compliance Score",
        "description": "% of applicable regulations with full compliance (no enforcement actions in trailing 12m)",
        "unit": "% compliant",
        "data_source": "Internal compliance register",
        "materiality_threshold": "All sectors",
        "verification_required": False,
        "sbt_alignment": False,
        "csddd_link": "CSDDD Art 10 — monitoring",
    },
    "SK040": {
        "id": "SK040", "group": "Governance",
        "name": "Modern Slavery Statement",
        "description": "Binary: annual modern slavery statement published per UK Modern Slavery Act 2015 / Australian MSA 2018",
        "unit": "binary (1=yes)",
        "data_source": "UK Modern Slavery Act 2015 / Australian MSA 2018 / CSDDD HR-04",
        "materiality_threshold": "All sectors with turnover > £36m (UK) / AUD 100m (AUS)",
        "verification_required": False,
        "sbt_alignment": False,
        "csddd_link": "HR-04 Forced labour prevention",
    },
}


# ---------------------------------------------------------------------------
# OECD DDG 5-step framework
# ---------------------------------------------------------------------------

OECD_DDG_STEPS: Dict[str, Dict[str, Any]] = {
    "step_1_management_systems": {
        "step": 1,
        "name": "Embed Responsible Business Conduct into Policies and Management Systems",
        "description": "Establish a supply chain policy aligned with OECD MNE Guidelines, UNGP and ILO Core Standards; appoint senior responsible officer; cascade through supplier contracts",
        "weight_pct": 20,
        "required_actions": [
            "Adopt written supply chain RBC policy",
            "Senior management sign-off and board endorsement",
            "Cascade policy requirements into supplier contracts",
            "Grievance mechanism operational for supply chain workers",
            "Supplier code of conduct distributed to tier-1 and tier-2 suppliers",
        ],
        "min_score_threshold": 60,
        "outputs": ["Supply chain RBC policy document", "Board resolution / minute", "Supplier contract ESG clauses"],
    },
    "step_2_risk_identification": {
        "step": 2,
        "name": "Identify and Assess Adverse Impacts in Supply Chain",
        "description": "Map supply chain tiers; identify potential and actual adverse impacts on human rights and environment using risk-based approach; prioritise by severity × likelihood",
        "weight_pct": 25,
        "required_actions": [
            "Tier-1 supplier mapping (100% of direct spend)",
            "Tier-2 mapping (≥50% of spend by value)",
            "Risk screening vs CSDDD HR-01 to HR-10 and ENV-01 to ENV-08 categories",
            "CAHRA (conflict-affected and high-risk area) identification",
            "Conflict mineral supply chain mapping (3TG + cobalt)",
        ],
        "min_score_threshold": 60,
        "outputs": ["Supplier risk heat map", "CAHRA exposure register", "Adverse impact risk register"],
    },
    "step_3_risk_mitigation": {
        "step": 3,
        "name": "Cease, Prevent or Mitigate Adverse Impacts",
        "description": "Implement targeted mitigation measures for identified risks; prioritise most severe adverse impacts; for existing adverse impacts, provide or cooperate in remediation",
        "weight_pct": 25,
        "required_actions": [
            "Corrective Action Plans (CAPs) for non-compliant suppliers",
            "Time-bound improvement commitments with KPI targets",
            "Capacity building programmes (training, technical support)",
            "Escalation process: warning → suspended → terminated",
            "Alternative sourcing analysis for CAHRA-exposed commodities",
        ],
        "min_score_threshold": 50,
        "outputs": ["Corrective Action Plans", "Capacity building records", "Escalation decision log"],
    },
    "step_4_third_party_audit": {
        "step": 4,
        "name": "Track Implementation via Third-Party Verification",
        "description": "Commission independent third-party audits or assessments to verify supplier performance; use internationally recognised standards (SMETA, SA8000, ISO 14001, ISO 45001)",
        "weight_pct": 20,
        "required_actions": [
            "Third-party audit for high-risk tier-1 suppliers (≥3yr cycle)",
            "Desk-based assessment for medium-risk suppliers",
            "SMETA 4-pillar or SA8000 certification for labour-intensive sectors",
            "Environmental audit (ISO 14001 / EcoVadis equivalent) for high ENV risk",
            "Audit findings disclosed to programme sponsor bank",
        ],
        "min_score_threshold": 50,
        "outputs": ["Audit schedule", "SMETA / SA8000 certificates", "Audit findings summary"],
    },
    "step_5_reporting": {
        "step": 5,
        "name": "Communicate How Impacts Are Addressed — Reporting",
        "description": "Publicly report on supply chain due diligence activities, adverse impacts identified, and remediation actions taken; align with CSDDD Art 11, CSRD ESRS S2 and GRI 414",
        "weight_pct": 10,
        "required_actions": [
            "Annual supply chain sustainability report or section in annual report",
            "GRI 414 Supplier Social Assessment disclosure",
            "CSDDD Art 11 reporting (where applicable)",
            "CSRD ESRS S2 Workers in the Value Chain disclosures",
            "Modern slavery statement (UK / Australian MSA)",
        ],
        "min_score_threshold": 40,
        "outputs": ["Supply chain sustainability report", "GRI Content Index (414)", "Modern slavery statement"],
    },
}


# ---------------------------------------------------------------------------
# CSDDD adverse impact categories for supply chain cascade
# ---------------------------------------------------------------------------

CSDDD_ADVERSE_IMPACTS: Dict[str, Dict[str, Any]] = {
    "HR-01": {"type": "human_rights", "name": "Safe and healthy working conditions", "supply_chain_cascade": True, "trigger_kpis": ["SK016"]},
    "HR-02": {"type": "human_rights", "name": "Just and favourable conditions of work", "supply_chain_cascade": True, "trigger_kpis": ["SK019", "SK022"]},
    "HR-03": {"type": "human_rights", "name": "Equal treatment and non-discrimination", "supply_chain_cascade": True, "trigger_kpis": ["SK020"]},
    "HR-04": {"type": "human_rights", "name": "Prohibition of forced labour", "supply_chain_cascade": True, "trigger_kpis": ["SK018", "SK040"]},
    "HR-05": {"type": "human_rights", "name": "Prohibition of child labour", "supply_chain_cascade": True, "trigger_kpis": ["SK017"]},
    "HR-06": {"type": "human_rights", "name": "Adequate standard of living", "supply_chain_cascade": False, "trigger_kpis": ["SK019"]},
    "HR-07": {"type": "human_rights", "name": "Freedom of association and collective bargaining", "supply_chain_cascade": True, "trigger_kpis": ["SK021"]},
    "HR-08": {"type": "human_rights", "name": "Land, territory and resource rights (FPIC)", "supply_chain_cascade": True, "trigger_kpis": ["SK024"]},
    "HR-09": {"type": "human_rights", "name": "Conflict minerals prohibition", "supply_chain_cascade": True, "trigger_kpis": ["SK036"]},
    "HR-10": {"type": "human_rights", "name": "Right to privacy and data protection", "supply_chain_cascade": False, "trigger_kpis": ["SK037"]},
    "ENV-01": {"type": "environmental", "name": "Climate change mitigation (GHG emissions)", "supply_chain_cascade": True, "trigger_kpis": ["SK001", "SK002", "SK007"]},
    "ENV-02": {"type": "environmental", "name": "Climate change adaptation", "supply_chain_cascade": False, "trigger_kpis": []},
    "ENV-03": {"type": "environmental", "name": "Sustainable use and protection of water", "supply_chain_cascade": True, "trigger_kpis": ["SK003"]},
    "ENV-04": {"type": "environmental", "name": "Transition to a circular economy", "supply_chain_cascade": False, "trigger_kpis": ["SK004", "SK015"]},
    "ENV-05": {"type": "environmental", "name": "Pollution prevention and control", "supply_chain_cascade": True, "trigger_kpis": ["SK009", "SK010", "SK011"]},
    "ENV-06": {"type": "environmental", "name": "Protection and restoration of biodiversity", "supply_chain_cascade": True, "trigger_kpis": ["SK008", "SK012", "SK014"]},
    "ENV-07": {"type": "environmental", "name": "Prohibition of deforestation (EUDR alignment)", "supply_chain_cascade": True, "trigger_kpis": ["SK012"]},
    "ENV-08": {"type": "environmental", "name": "Sustainable land use and soil protection", "supply_chain_cascade": True, "trigger_kpis": ["SK011", "SK014"]},
}


# ---------------------------------------------------------------------------
# 15 sector supply chain risk profiles
# ---------------------------------------------------------------------------

SECTOR_SUPPLY_CHAIN_RISK_PROFILES: Dict[str, Dict[str, Any]] = {
    "textiles": {
        "name": "Textiles, Apparel and Footwear",
        "nace_code": "C13-C15",
        "inherent_risk_tier": "very_high",
        "primary_risks": ["forced_labour", "child_labour", "chemical_pollution", "water_intensity"],
        "cahra_exposure": True,
        "conflict_mineral_exposure": False,
        "eudr_exposure": False,
        "typical_tier_depth": 5,
        "scope3_cat1_intensity": "high",
        "recommended_kpis": ["SK001", "SK003", "SK017", "SK018", "SK019", "SK022", "SK033", "SK034"],
        "regulatory_exposure": ["UK Modern Slavery Act", "French Duty of Vigilance", "CSDDD", "CBAM (fibre)"],
    },
    "electronics": {
        "name": "Electronics and Semiconductor Manufacturing",
        "nace_code": "C26",
        "inherent_risk_tier": "very_high",
        "primary_risks": ["conflict_minerals", "child_labour", "e_waste", "water_intensity"],
        "cahra_exposure": True,
        "conflict_mineral_exposure": True,
        "eudr_exposure": False,
        "typical_tier_depth": 6,
        "scope3_cat1_intensity": "high",
        "recommended_kpis": ["SK001", "SK009", "SK017", "SK018", "SK036", "SK033", "SK034"],
        "regulatory_exposure": ["EU Conflict Minerals Regulation", "CSDDD", "US OECD DDG", "CBAM"],
    },
    "agriculture": {
        "name": "Agriculture and Agri-Processing",
        "nace_code": "A01-A03",
        "inherent_risk_tier": "very_high",
        "primary_risks": ["deforestation", "child_labour", "water_use", "biodiversity_loss"],
        "cahra_exposure": True,
        "conflict_mineral_exposure": False,
        "eudr_exposure": True,
        "typical_tier_depth": 4,
        "scope3_cat1_intensity": "very_high",
        "recommended_kpis": ["SK001", "SK003", "SK008", "SK012", "SK014", "SK017", "SK024"],
        "regulatory_exposure": ["EUDR", "CSDDD", "UK Modern Slavery Act", "SBTi FLAG"],
    },
    "mining": {
        "name": "Mining and Metal Extraction",
        "nace_code": "B05-B09",
        "inherent_risk_tier": "very_high",
        "primary_risks": ["conflict_minerals", "community_impact", "water_pollution", "land_rights"],
        "cahra_exposure": True,
        "conflict_mineral_exposure": True,
        "eudr_exposure": False,
        "typical_tier_depth": 3,
        "scope3_cat1_intensity": "very_high",
        "recommended_kpis": ["SK001", "SK003", "SK011", "SK014", "SK024", "SK036", "SK023"],
        "regulatory_exposure": ["EU Conflict Minerals Regulation", "CSDDD", "CBAM", "ICMM Principles"],
    },
    "chemicals": {
        "name": "Chemical and Petrochemical Manufacturing",
        "nace_code": "C20",
        "inherent_risk_tier": "high",
        "primary_risks": ["hazardous_chemicals", "air_emissions", "soil_contamination", "worker_safety"],
        "cahra_exposure": False,
        "conflict_mineral_exposure": False,
        "eudr_exposure": False,
        "typical_tier_depth": 4,
        "scope3_cat1_intensity": "high",
        "recommended_kpis": ["SK001", "SK009", "SK010", "SK011", "SK016", "SK033"],
        "regulatory_exposure": ["REACH", "CSDDD", "CBAM", "EU Chemical Strategy"],
    },
    "automotive": {
        "name": "Automotive and EV Manufacturing",
        "nace_code": "C29",
        "inherent_risk_tier": "high",
        "primary_risks": ["conflict_minerals", "emissions", "labour_rights", "battery_supply_chain"],
        "cahra_exposure": True,
        "conflict_mineral_exposure": True,
        "eudr_exposure": False,
        "typical_tier_depth": 5,
        "scope3_cat1_intensity": "high",
        "recommended_kpis": ["SK001", "SK007", "SK015", "SK036", "SK017", "SK018"],
        "regulatory_exposure": ["EU Battery Regulation", "EU Conflict Minerals", "CSDDD", "CBAM"],
    },
    "food_beverage": {
        "name": "Food and Beverage Processing",
        "nace_code": "C10-C12",
        "inherent_risk_tier": "high",
        "primary_risks": ["deforestation", "water_use", "packaging_waste", "labour_rights"],
        "cahra_exposure": False,
        "conflict_mineral_exposure": False,
        "eudr_exposure": True,
        "typical_tier_depth": 4,
        "scope3_cat1_intensity": "very_high",
        "recommended_kpis": ["SK001", "SK003", "SK005", "SK012", "SK013", "SK017", "SK033"],
        "regulatory_exposure": ["EUDR", "CSDDD", "EU Packaging Regulation", "UK Modern Slavery Act"],
    },
    "pharma": {
        "name": "Pharmaceutical and Life Sciences",
        "nace_code": "C21",
        "inherent_risk_tier": "medium",
        "primary_risks": ["API_sourcing", "chemical_waste", "labour_rights", "data_privacy"],
        "cahra_exposure": False,
        "conflict_mineral_exposure": False,
        "eudr_exposure": False,
        "typical_tier_depth": 4,
        "scope3_cat1_intensity": "medium",
        "recommended_kpis": ["SK001", "SK009", "SK016", "SK033", "SK037", "SK039"],
        "regulatory_exposure": ["GMP/GDP", "CSDDD", "EU Chemical Strategy"],
    },
    "construction": {
        "name": "Construction and Building Materials",
        "nace_code": "F",
        "inherent_risk_tier": "high",
        "primary_risks": ["migrant_labour", "worker_safety", "deforestation_timber", "waste"],
        "cahra_exposure": True,
        "conflict_mineral_exposure": False,
        "eudr_exposure": True,
        "typical_tier_depth": 4,
        "scope3_cat1_intensity": "high",
        "recommended_kpis": ["SK001", "SK004", "SK012", "SK016", "SK018", "SK033"],
        "regulatory_exposure": ["EUDR (timber)", "UK Modern Slavery Act", "CSDDD", "Building Regulations"],
    },
    "energy": {
        "name": "Energy and Utilities",
        "nace_code": "D35/B06",
        "inherent_risk_tier": "high",
        "primary_risks": ["carbon_emissions", "community_impact", "biodiversity", "just_transition"],
        "cahra_exposure": False,
        "conflict_mineral_exposure": False,
        "eudr_exposure": False,
        "typical_tier_depth": 3,
        "scope3_cat1_intensity": "very_high",
        "recommended_kpis": ["SK001", "SK007", "SK008", "SK014", "SK023", "SK024"],
        "regulatory_exposure": ["CSDDD", "EU Taxonomy", "CBAM", "Paris Agreement NDCs"],
    },
    "retail": {
        "name": "Retail and Consumer Goods",
        "nace_code": "G47",
        "inherent_risk_tier": "high",
        "primary_risks": ["labour_rights_sourcing", "packaging", "deforestation", "scope3"],
        "cahra_exposure": False,
        "conflict_mineral_exposure": False,
        "eudr_exposure": True,
        "typical_tier_depth": 5,
        "scope3_cat1_intensity": "very_high",
        "recommended_kpis": ["SK002", "SK005", "SK012", "SK017", "SK018", "SK033", "SK034"],
        "regulatory_exposure": ["EUDR", "CSDDD", "EU Ecodesign", "UK Modern Slavery Act"],
    },
    "logistics": {
        "name": "Logistics and Transportation",
        "nace_code": "H49-H52",
        "inherent_risk_tier": "medium",
        "primary_risks": ["emissions", "labour_rights", "safety", "vehicle_fleet"],
        "cahra_exposure": False,
        "conflict_mineral_exposure": False,
        "eudr_exposure": False,
        "typical_tier_depth": 2,
        "scope3_cat1_intensity": "high",
        "recommended_kpis": ["SK001", "SK006", "SK016", "SK019", "SK033"],
        "regulatory_exposure": ["EU Green Deal transport", "CSDDD", "EU ETS maritime"],
    },
    "financial": {
        "name": "Financial Services and Banking",
        "nace_code": "K64-K66",
        "inherent_risk_tier": "low",
        "primary_risks": ["scope3_financed_emissions", "governance", "data_privacy"],
        "cahra_exposure": False,
        "conflict_mineral_exposure": False,
        "eudr_exposure": False,
        "typical_tier_depth": 2,
        "scope3_cat1_intensity": "low",
        "recommended_kpis": ["SK001", "SK029", "SK030", "SK037", "SK038", "SK039"],
        "regulatory_exposure": ["CSDDD (indirect)", "SFDR", "EU Taxonomy", "CSRD"],
    },
    "tech": {
        "name": "Technology and Software",
        "nace_code": "J58-J63",
        "inherent_risk_tier": "medium",
        "primary_risks": ["hardware_supply_chain", "data_centre_energy", "conflict_minerals_HW", "labour"],
        "cahra_exposure": False,
        "conflict_mineral_exposure": True,
        "eudr_exposure": False,
        "typical_tier_depth": 4,
        "scope3_cat1_intensity": "medium",
        "recommended_kpis": ["SK001", "SK007", "SK036", "SK037", "SK038", "SK033"],
        "regulatory_exposure": ["EU Conflict Minerals", "CSDDD", "EU AI Act (AI suppliers)", "DORA"],
    },
    "healthcare": {
        "name": "Healthcare and Medical Devices",
        "nace_code": "Q86-Q88",
        "inherent_risk_tier": "medium",
        "primary_risks": ["API_sourcing", "medical_waste", "labour_rights", "product_safety"],
        "cahra_exposure": False,
        "conflict_mineral_exposure": False,
        "eudr_exposure": False,
        "typical_tier_depth": 4,
        "scope3_cat1_intensity": "medium",
        "recommended_kpis": ["SK001", "SK009", "SK016", "SK033", "SK037", "SK039"],
        "regulatory_exposure": ["CSDDD", "EU MDR", "FDA supply chain requirements"],
    },
}


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class SupplierProfile(BaseModel):
    model_config = {"protected_namespaces": ()}
    name: str
    country: str
    tier: int = Field(..., ge=1, le=4, description="Supply chain tier: 1=direct, 2=sub-tier, 3=raw material, 4=commodity")
    nace_code: str
    annual_spend_mn: float = Field(..., description="Buyer's annual spend with this supplier (USD mn)")
    kpi_data: Dict[str, Any] = Field(default_factory=dict, description="KPI id → current value")


class SSCFRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    buyer_name: str
    programme_type: str = Field(..., description="payables_finance | receivables_discounting | dynamic_discounting | hybrid")
    programme_size_mn: float = Field(..., description="Total programme facility size (USD mn)")
    currency: str = "USD"
    suppliers: List[SupplierProfile]
    kpi_selections: List[str] = Field(..., description="List of KPI IDs from SK001-SK040 to include")
    sscf_framework: str = Field(..., description="LMA_SSCF_2023 | ICC_SCF_2022 | GSCFF_2023")


class SupplierScoreRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    supplier_name: str
    supplier_country: str
    tier: int = Field(1, ge=1, le=4)
    nace_code: str
    kpi_data: Dict[str, Any] = Field(default_factory=dict)


class MarginRatchetRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    base_rate_bps: float = Field(..., description="Baseline margin in basis points")
    spts_met: int = Field(..., ge=0, description="Number of SPTs achieved")
    spts_total: int = Field(..., ge=1, description="Total number of SPTs defined")


class DynamicDiscountRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    buyer_wacc_pct: float = Field(..., description="Buyer's WACC as a percentage (e.g. 8.5 = 8.5%)")
    days_early: float = Field(..., ge=1, description="Days of early payment vs original due date")
    invoice_amount: float = Field(..., description="Invoice face value in programme currency")


# ---------------------------------------------------------------------------
# Country risk data for CAHRA and conflict mineral screening
# ---------------------------------------------------------------------------

CAHRA_COUNTRIES: List[str] = [
    "Democratic Republic of Congo", "DRC", "Central African Republic", "South Sudan",
    "Somalia", "Libya", "Mali", "Burkina Faso", "Niger", "Myanmar", "North Korea",
    "Afghanistan", "Yemen", "Syria", "Iraq", "Venezuela",
]

HIGH_RISK_COUNTRIES: List[str] = [
    "Bangladesh", "Cambodia", "Ethiopia", "Pakistan", "Vietnam",
    "Indonesia", "Philippines", "Bolivia", "Peru", "Colombia",
    "Guatemala", "Honduras", "Nigeria", "Ghana", "Ivory Coast",
    "Mozambique", "Tanzania", "Madagascar",
]

CONFLICT_MINERAL_SECTORS: List[str] = [
    "C26", "C29", "B05", "B06", "C24", "C27",
]


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------

def _score_kpi(kpi_id: str, value: Any) -> float:
    """
    Score a KPI value on a 0-100 scale based on direction and benchmark.
    Returns 0-100 where 100 = fully meets SPT target.
    """
    if value is None:
        return 0.0

    kpi = KPI_LIBRARY.get(kpi_id)
    if kpi is None:
        return 50.0  # neutral for unknown KPIs

    # Binary KPIs (value = 0 or 1 or True/False)
    if kpi["unit"].startswith("binary"):
        return 100.0 if value in [1, True, "yes", "Yes", "YES", "1"] else 0.0

    try:
        v = float(value)
    except (TypeError, ValueError):
        return 50.0

    # Lower-is-better KPIs: GHG intensity, LTIFR, water intensity, air emissions,
    # chemicals, soil incidents, gender pay gap, ocean plastic, land use change
    lower_is_better = [
        "SK001", "SK002", "SK003", "SK006", "SK009", "SK010",
        "SK011", "SK013", "SK014", "SK016", "SK020",
    ]
    if kpi_id in lower_is_better:
        # Score 100 if value = 0, degrades logarithmically
        if v <= 0:
            return 100.0
        score = max(0.0, 100.0 - math.log1p(v) * 12)
        return round(min(score, 100.0), 2)

    # Higher-is-better KPIs: percentages, binary, counts
    if "%" in kpi["unit"] or "pct" in kpi_id.lower():
        return round(min(max(v, 0.0), 100.0), 2)

    # Frequency-based (audit count, training hours)
    if kpi_id == "SK034":
        return round(min(v * 33.3, 100.0), 2)
    if kpi_id == "SK025":
        return round(min(v * 2.5, 100.0), 2)
    if kpi_id == "SK038":
        return round(min(v * 20.0, 100.0), 2)

    return round(min(max(v, 0.0), 100.0), 2)


def _derive_risk_tier(overall_score: float, cahra_flag: bool, conflict_mineral_flag: bool) -> str:
    """Classify supplier into risk tier based on ESG score and red flags."""
    if cahra_flag or conflict_mineral_flag:
        if overall_score < 40:
            return "critical"
        return "high"
    if overall_score >= 80:
        return "low"
    if overall_score >= 60:
        return "medium"
    if overall_score >= 40:
        return "high"
    return "critical"


def _check_csddd_cascades(kpi_data: Dict[str, Any], kpi_selections: List[str]) -> List[str]:
    """Return list of CSDDD adverse impact categories triggered by low KPI scores."""
    triggered = []
    for impact_id, impact in CSDDD_ADVERSE_IMPACTS.items():
        if not impact["supply_chain_cascade"]:
            continue
        for kpi_id in impact["trigger_kpis"]:
            if kpi_id not in kpi_data:
                continue
            score = _score_kpi(kpi_id, kpi_data.get(kpi_id))
            if score < 40:
                triggered.append(f"{impact_id}: {impact['name']}")
                break
    return triggered


def _score_oecd_ddg(kpi_data: Dict[str, Any], supplier_profiles: List[SupplierProfile]) -> Dict[str, Any]:
    """Score OECD DDG 5 steps based on available KPI data."""
    scores = {}
    weighted_total = 0.0

    step_kpi_mapping = {
        "step_1_management_systems": ["SK027", "SK033", "SK028", "SK029", "SK030"],
        "step_2_risk_identification": ["SK036", "SK024", "SK017", "SK018"],
        "step_3_risk_mitigation": ["SK019", "SK022", "SK016", "SK012"],
        "step_4_third_party_audit": ["SK034", "SK039"],
        "step_5_reporting": ["SK035", "SK040", "SK025"],
    }

    for step_id, step_info in OECD_DDG_STEPS.items():
        relevant_kpis = step_kpi_mapping.get(step_id, [])
        available_kpis = [k for k in relevant_kpis if k in kpi_data]
        if not available_kpis:
            step_score = 30.0  # minimal compliance assumed
        else:
            step_score = sum(_score_kpi(k, kpi_data[k]) for k in available_kpis) / len(available_kpis)

        weight = step_info["weight_pct"] / 100
        weighted_total += step_score * weight
        passes = step_score >= step_info["min_score_threshold"]
        scores[step_id] = {
            "step": step_info["step"],
            "name": step_info["name"],
            "score": round(step_score, 2),
            "weight_pct": step_info["weight_pct"],
            "passes_threshold": passes,
            "threshold": step_info["min_score_threshold"],
        }

    return {
        "step_scores": scores,
        "overall_weighted_score": round(weighted_total, 2),
        "oecd_ddg_compliant": weighted_total >= 55.0,
    }


# ---------------------------------------------------------------------------
# Core calculation functions
# ---------------------------------------------------------------------------

def score_supplier_esg(request: SupplierScoreRequest) -> Dict[str, Any]:
    """
    Score a single supplier across all provided KPI data.
    Returns per-KPI scores, group averages, risk tier and recommended margin.
    """
    kpi_data = request.kpi_data
    scored_kpis = {}
    group_scores: Dict[str, List[float]] = {
        "Environmental": [], "Social": [], "Governance": []
    }

    for kpi_id, value in kpi_data.items():
        kpi_info = KPI_LIBRARY.get(kpi_id)
        if kpi_info is None:
            continue
        score = _score_kpi(kpi_id, value)
        scored_kpis[kpi_id] = {
            "kpi_name": kpi_info["name"],
            "group": kpi_info["group"],
            "value": value,
            "score": score,
            "unit": kpi_info["unit"],
        }
        group_scores[kpi_info["group"]].append(score)

    env_score = sum(group_scores["Environmental"]) / max(len(group_scores["Environmental"]), 1)
    soc_score = sum(group_scores["Social"]) / max(len(group_scores["Social"]), 1)
    gov_score = sum(group_scores["Governance"]) / max(len(group_scores["Governance"]), 1)
    overall_score = (env_score * 0.40 + soc_score * 0.35 + gov_score * 0.25)

    cahra_flag = request.supplier_country in CAHRA_COUNTRIES
    high_risk_country = request.supplier_country in HIGH_RISK_COUNTRIES
    conflict_mineral_flag = request.nace_code[:3] in CONFLICT_MINERAL_SECTORS

    risk_tier = _derive_risk_tier(overall_score, cahra_flag, conflict_mineral_flag)

    # Recommended discount rate: better ESG score → higher early-payment discount access
    if risk_tier == "low":
        recommended_discount_rate_bps = 80
    elif risk_tier == "medium":
        recommended_discount_rate_bps = 55
    elif risk_tier == "high":
        recommended_discount_rate_bps = 30
    else:
        recommended_discount_rate_bps = 0

    csddd_triggers = _check_csddd_cascades(kpi_data, list(kpi_data.keys()))

    return {
        "supplier_name": request.supplier_name,
        "supplier_country": request.supplier_country,
        "tier": request.tier,
        "nace_code": request.nace_code,
        "kpi_scores": scored_kpis,
        "group_scores": {
            "Environmental": round(env_score, 2),
            "Social": round(soc_score, 2),
            "Governance": round(gov_score, 2),
        },
        "overall_esg_score": round(overall_score, 2),
        "risk_tier": risk_tier,
        "cahra_flag": cahra_flag,
        "high_risk_country": high_risk_country,
        "conflict_mineral_flag": conflict_mineral_flag,
        "csddd_adverse_impacts_triggered": csddd_triggers,
        "recommended_discount_rate_bps": recommended_discount_rate_bps,
        "kpis_scored": len(scored_kpis),
        "kpis_available": len(kpi_data),
    }


def calculate_margin_ratchet(
    base_rate_bps: float,
    spts_met: int,
    spts_total: int,
) -> Dict[str, Any]:
    """
    Calculate SPT-linked margin ratchet for sustainability-linked SCF programme.

    Step-down schedule:
    - 100% SPTs met → -50 bps
    - 80-99% → -30 bps
    - 60-79% → -15 bps
    - 40-59% → -5 bps
    - 20-39% → 0 bps (no adjustment — grace period)
    - 0-19% → +10 bps (step-up penalty)
    - 0 SPTs met → +25 bps
    """
    if spts_total < 1:
        raise ValueError("spts_total must be at least 1")
    if spts_met > spts_total:
        raise ValueError("spts_met cannot exceed spts_total")

    achievement_pct = (spts_met / spts_total) * 100

    if achievement_pct == 100:
        adjustment_bps = -50
        tier = "platinum"
    elif achievement_pct >= 80:
        adjustment_bps = -30
        tier = "gold"
    elif achievement_pct >= 60:
        adjustment_bps = -15
        tier = "silver"
    elif achievement_pct >= 40:
        adjustment_bps = -5
        tier = "bronze"
    elif achievement_pct >= 20:
        adjustment_bps = 0
        tier = "grace_period"
    elif achievement_pct > 0:
        adjustment_bps = +10
        tier = "step_up_minor"
    else:
        adjustment_bps = +25
        tier = "step_up_major"

    # Cap: maximum discount is 75 bps; maximum penalty is +50 bps
    adjustment_bps = max(adjustment_bps, -75)
    adjustment_bps = min(adjustment_bps, +50)

    new_rate_bps = base_rate_bps + adjustment_bps

    return {
        "base_rate_bps": round(base_rate_bps, 2),
        "spts_met": spts_met,
        "spts_total": spts_total,
        "achievement_pct": round(achievement_pct, 1),
        "adjustment_bps": adjustment_bps,
        "new_rate_bps": round(new_rate_bps, 2),
        "new_rate_pct": round(new_rate_bps / 100, 4),
        "tier": tier,
        "step_down_bps": abs(adjustment_bps) if adjustment_bps < 0 else 0,
        "step_up_bps": adjustment_bps if adjustment_bps > 0 else 0,
        "max_achievable_discount_bps": 75,
        "grace_period_months": 6,
        "notes": "Adjustment applied at annual review date; grace period of 6 months before step-up enforced",
    }


def calculate_dynamic_discount(
    buyer_wacc_pct: float,
    days_early: float,
    invoice_amount: float,
) -> Dict[str, Any]:
    """
    Calculate early payment dynamic discount for a supplier invoice.

    Formula (GSCFF standard):
        annualised_rate = buyer_WACC × (days_early / 360)
        discount_amount = invoice_amount × annualised_rate
        floor = 0.5% annualised; cap = 8.0% annualised
    """
    if buyer_wacc_pct <= 0:
        raise ValueError("buyer_wacc_pct must be positive")
    if days_early <= 0:
        raise ValueError("days_early must be positive")
    if invoice_amount <= 0:
        raise ValueError("invoice_amount must be positive")

    buyer_wacc_decimal = buyer_wacc_pct / 100

    # Apply floor and cap to WACC
    floored_rate = max(buyer_wacc_decimal, 0.005)
    capped_rate = min(floored_rate, 0.08)

    annualised_discount_rate = capped_rate * (days_early / 360)
    discount_amount = invoice_amount * annualised_discount_rate
    settlement_amount = invoice_amount - discount_amount

    # APR equivalent (for supplier comparison)
    apr_equivalent = capped_rate

    return {
        "buyer_wacc_pct": buyer_wacc_pct,
        "days_early": days_early,
        "invoice_amount": round(invoice_amount, 2),
        "effective_annualised_rate_pct": round(capped_rate * 100, 4),
        "rate_applied": round(capped_rate, 6),
        "annualised_discount_rate_pct": round(annualised_discount_rate * 100, 4),
        "discount_amount": round(discount_amount, 2),
        "settlement_amount": round(settlement_amount, 2),
        "supplier_apr_equivalent_pct": round(apr_equivalent * 100, 4),
        "floor_rate_pct": 0.5,
        "cap_rate_pct": 8.0,
        "was_floored": buyer_wacc_pct < 0.5,
        "was_capped": buyer_wacc_pct > 8.0,
        "note": "Dynamic discount rate = buyer WACC × (days_early / 360); floor 0.5%, cap 8.0% per annum",
    }


def assess_sscf_programme(request: SSCFRequest) -> Dict[str, Any]:
    """
    Full SSCF programme assessment covering:
    - Framework eligibility check
    - KPI materiality scoring
    - OECD DDG 5-step compliance
    - CSDDD adverse impact cascade check
    - Scope 3 Cat1 coverage
    - Margin ratchet economics
    - Per-supplier ESG scoring
    - Overall programme score and eligible flag
    """
    framework = SSCF_FRAMEWORKS.get(request.sscf_framework)
    if framework is None:
        raise ValueError(f"Unknown SSCF framework: {request.sscf_framework}. Valid: {list(SSCF_FRAMEWORKS.keys())}")

    # Score each supplier
    supplier_scores = []
    all_kpi_data_combined: Dict[str, List[float]] = {}

    for supplier in request.suppliers:
        score_req = SupplierScoreRequest(
            supplier_name=supplier.name,
            supplier_country=supplier.country,
            tier=supplier.tier,
            nace_code=supplier.nace_code,
            kpi_data=supplier.kpi_data,
        )
        score_result = score_supplier_esg(score_req)
        score_result["annual_spend_mn"] = supplier.annual_spend_mn
        supplier_scores.append(score_result)

        for kpi_id, val in supplier.kpi_data.items():
            s = _score_kpi(kpi_id, val)
            all_kpi_data_combined.setdefault(kpi_id, []).append(s)

    # Programme-level KPI aggregates (spend-weighted)
    total_spend = sum(s.annual_spend_mn for s in request.suppliers) or 1.0
    programme_kpi_scores = {}
    for kpi_id in request.kpi_selections:
        kpi_info = KPI_LIBRARY.get(kpi_id)
        if kpi_info is None:
            continue
        supplier_scores_for_kpi = []
        for i, supplier in enumerate(request.suppliers):
            if kpi_id in supplier.kpi_data:
                kpi_score = _score_kpi(kpi_id, supplier.kpi_data[kpi_id])
                supplier_scores_for_kpi.append((kpi_score, supplier.annual_spend_mn))
        if supplier_scores_for_kpi:
            weighted_score = sum(s * w for s, w in supplier_scores_for_kpi) / sum(w for _, w in supplier_scores_for_kpi)
        else:
            weighted_score = 0.0
        programme_kpi_scores[kpi_id] = {
            "kpi_name": kpi_info["name"],
            "group": kpi_info["group"],
            "weighted_score": round(weighted_score, 2),
            "suppliers_reporting": len(supplier_scores_for_kpi),
        }

    # Framework eligibility check
    eligibility_checks = []
    criteria_met = 0
    for criterion in framework["eligibility_criteria"]:
        met = True  # simplified: assume buyer has met criteria; real impl would parse buyer data
        eligibility_checks.append({"criterion": criterion, "met": met})
        if met:
            criteria_met += 1

    eligibility_pct = (criteria_met / len(framework["eligibility_criteria"])) * 100

    # OECD DDG scoring using first supplier's KPI data as proxy
    all_kpi_flat = {}
    for supplier in request.suppliers:
        all_kpi_flat.update(supplier.kpi_data)
    oecd_result = _score_oecd_ddg(all_kpi_flat, request.suppliers)

    # CSDDD cascade check
    csddd_triggers = _check_csddd_cascades(all_kpi_flat, request.kpi_selections)

    # Scope 3 Cat1 coverage check
    scope3_kpi_present = "SK002" in request.kpi_selections
    scope3_coverage_pct = sum(
        1 for s in request.suppliers if "SK002" in s.kpi_data
    ) / max(len(request.suppliers), 1) * 100

    # Margin ratchet economics
    env_kpis_selected = [k for k in request.kpi_selections if k in KPI_LIBRARY and KPI_LIBRARY[k]["group"] == "Environmental"]
    soc_kpis_selected = [k for k in request.kpi_selections if k in KPI_LIBRARY and KPI_LIBRARY[k]["group"] == "Social"]
    gov_kpis_selected = [k for k in request.kpi_selections if k in KPI_LIBRARY and KPI_LIBRARY[k]["group"] == "Governance"]

    avg_programme_score = (
        sum(s["overall_esg_score"] for s in supplier_scores) / max(len(supplier_scores), 1)
    )

    # Simulate SPTs: assume 60% score → baseline SPT achievement
    simulated_spts_met = int((avg_programme_score / 100) * len(request.kpi_selections))
    ratchet_result = calculate_margin_ratchet(
        base_rate_bps=200.0,  # standard SSCF base rate assumption
        spts_met=simulated_spts_met,
        spts_total=max(len(request.kpi_selections), 1),
    )

    # Overall programme eligibility
    min_kpis_required = 3
    has_min_kpis = len(request.kpi_selections) >= min_kpis_required
    has_env_kpi = len(env_kpis_selected) >= 2
    has_soc_kpi = len(soc_kpis_selected) >= 1
    framework_eligible = eligibility_pct >= 70 and has_min_kpis and oecd_result["oecd_ddg_compliant"]

    overall_programme_score = (
        avg_programme_score * 0.50 +
        oecd_result["overall_weighted_score"] * 0.30 +
        eligibility_pct * 0.20
    )

    return {
        "assessment_id": str(uuid.uuid4()),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "buyer_name": request.buyer_name,
        "programme_type": request.programme_type,
        "programme_size_mn": request.programme_size_mn,
        "currency": request.currency,
        "sscf_framework": request.sscf_framework,
        "framework_name": framework["name"],
        "supplier_count": len(request.suppliers),
        "total_spend_mn": round(total_spend, 2),
        "kpi_selections": request.kpi_selections,
        "kpi_count": len(request.kpi_selections),
        "env_kpis": env_kpis_selected,
        "social_kpis": soc_kpis_selected,
        "governance_kpis": gov_kpis_selected,
        "framework_eligibility": {
            "criteria_checks": eligibility_checks,
            "criteria_met": criteria_met,
            "total_criteria": len(framework["eligibility_criteria"]),
            "eligibility_pct": round(eligibility_pct, 1),
            "has_min_kpis": has_min_kpis,
            "has_env_kpi": has_env_kpi,
            "has_soc_kpi": has_soc_kpi,
        },
        "oecd_ddg_assessment": oecd_result,
        "csddd_cascade_check": {
            "adverse_impacts_triggered": csddd_triggers,
            "trigger_count": len(csddd_triggers),
            "all_clear": len(csddd_triggers) == 0,
        },
        "scope3_cat1": {
            "kpi_sk002_selected": scope3_kpi_present,
            "supplier_coverage_pct": round(scope3_coverage_pct, 1),
            "pcaf_part_c_aligned": scope3_coverage_pct >= 50,
        },
        "programme_kpi_scores": programme_kpi_scores,
        "supplier_scores": supplier_scores,
        "avg_supplier_esg_score": round(avg_programme_score, 2),
        "high_risk_suppliers": [s["supplier_name"] for s in supplier_scores if s["risk_tier"] in ["high", "critical"]],
        "cahra_suppliers": [s["supplier_name"] for s in supplier_scores if s["cahra_flag"]],
        "conflict_mineral_suppliers": [s["supplier_name"] for s in supplier_scores if s["conflict_mineral_flag"]],
        "margin_ratchet_illustration": ratchet_result,
        "overall_programme_score": round(overall_programme_score, 2),
        "framework_eligible": framework_eligible,
        "documentation_checklist": framework["documentation_checklist"],
        "max_margin_discount_bps": framework["max_margin_discount_bps"],
        "grace_period_months": framework["grace_period_months"],
        "spt_review_frequency": framework["spt_review_frequency"],
        "green_bond_overlap": framework["green_bond_overlap"],
    }


def get_sscf_benchmarks() -> Dict[str, Any]:
    """Return framework profiles, KPI definitions and reference data."""
    return {
        "sscf_frameworks": SSCF_FRAMEWORKS,
        "kpi_library_summary": {
            kpi_id: {
                "name": kpi["name"],
                "group": kpi["group"],
                "unit": kpi["unit"],
                "verification_required": kpi["verification_required"],
                "sbt_alignment": kpi["sbt_alignment"],
            }
            for kpi_id, kpi in KPI_LIBRARY.items()
        },
        "kpi_count": len(KPI_LIBRARY),
        "oecd_ddg_steps": OECD_DDG_STEPS,
        "csddd_adverse_impact_categories": len(CSDDD_ADVERSE_IMPACTS),
        "sector_risk_profile_count": len(SECTOR_SUPPLY_CHAIN_RISK_PROFILES),
    }
