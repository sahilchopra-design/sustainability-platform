"""
esg_ma_engine.py — E79 ESG M&A Due Diligence
UNGP 31 Guiding Principles | CSDDD Art 3 Supply Chain Scope
OECD Due Diligence Guidance for RBC | ESG Valuation Adjustments
Post-Merger Integration | ILO 8 Core Conventions | SFDR/EU Taxonomy
"""
from __future__ import annotations
import random
from datetime import datetime, timezone, timedelta
from typing import Any

# ── Reference Data ─────────────────────────────────────────────────────────────

UNGP_PRINCIPLES = [
    # Pillar I — State Duty to Protect
    {"id": "UNGP-1", "pillar": "I", "category": "State_Protect", "principle": "States must protect against human rights abuse by business enterprises"},
    {"id": "UNGP-2", "pillar": "I", "category": "State_Protect", "principle": "States must set clear expectations for business HRs conduct in their territory"},
    {"id": "UNGP-3", "pillar": "I", "category": "State_Protect", "principle": "States should enforce laws requiring business to respect HRs"},
    {"id": "UNGP-4", "pillar": "I", "category": "State_Protect", "principle": "States must protect HRs when contracting with or legislating for business"},
    {"id": "UNGP-5", "pillar": "I", "category": "State_Protect", "principle": "States must exercise adequate oversight of business HRs in conflict-affected areas"},
    {"id": "UNGP-6", "pillar": "I", "category": "State_Protect", "principle": "States should promote HRs-compatible business practices through trade/investment agreements"},
    {"id": "UNGP-7", "pillar": "I", "category": "State_Protect", "principle": "States providing business support must consider HRs risks"},
    {"id": "UNGP-8", "pillar": "I", "category": "State_Protect", "principle": "Policy coherence required between trade, finance and HRs"},
    {"id": "UNGP-9", "pillar": "I", "category": "State_Protect", "principle": "Multinational enterprise home States must take appropriate steps on overseas operations"},
    {"id": "UNGP-10", "pillar": "I", "category": "State_Protect", "principle": "States should ensure effective guidance for businesses on HRs"},
    # Pillar II — Business Responsibility to Respect
    {"id": "UNGP-11", "pillar": "II", "category": "Business_Respect", "principle": "Business enterprises must respect internationally recognised human rights"},
    {"id": "UNGP-12", "pillar": "II", "category": "Business_Respect", "principle": "Business must respect all internationally recognised HRs per UDHR, ICCPR, ICESCR, ILO core conventions"},
    {"id": "UNGP-13", "pillar": "II", "category": "Business_Respect", "principle": "Responsibility to avoid causing or contributing to adverse HRs impacts"},
    {"id": "UNGP-14", "pillar": "II", "category": "Business_Respect", "principle": "Responsibility applies to all business regardless of size, sector or ownership"},
    {"id": "UNGP-15", "pillar": "II", "category": "Business_Respect", "principle": "Policy commitment, HRDD process, and remediation access required"},
    {"id": "UNGP-16", "pillar": "II", "category": "Business_Respect", "principle": "Policy commitment must be approved at senior level, inform internal functions and embed in supplier relations"},
    {"id": "UNGP-17", "pillar": "II", "category": "Business_Respect", "principle": "Human rights due diligence covers actual and potential impacts, tracking and communicating"},
    {"id": "UNGP-18", "pillar": "II", "category": "Business_Respect", "principle": "Impact assessment requires meaningful consultation with potentially affected groups"},
    {"id": "UNGP-19", "pillar": "II", "category": "Business_Respect", "principle": "Integration of impact findings and taking appropriate action"},
    {"id": "UNGP-20", "pillar": "II", "category": "Business_Respect", "principle": "Tracking effectiveness of response — qualitative and quantitative indicators"},
    {"id": "UNGP-21", "pillar": "II", "category": "Business_Respect", "principle": "Communication on HRs impacts — reporting obligation and form"},
    {"id": "UNGP-22", "pillar": "II", "category": "Business_Respect", "principle": "Where business caused or contributed, must provide or cooperate in remediation"},
    {"id": "UNGP-23", "pillar": "II", "category": "Business_Respect", "principle": "Business should treat HRs risk as a legal risk, especially in complex contexts"},
    {"id": "UNGP-24", "pillar": "II", "category": "Business_Respect", "principle": "Prioritisation of HRs impacts based on severity when all cannot be addressed simultaneously"},
    # Pillar III — Access to Remedy
    {"id": "UNGP-25", "pillar": "III", "category": "Access_Remedy", "principle": "States must take appropriate steps to ensure access to effective remedy"},
    {"id": "UNGP-26", "pillar": "III", "category": "Access_Remedy", "principle": "States must ensure judicial remedy through domestic courts is available"},
    {"id": "UNGP-27", "pillar": "III", "category": "Access_Remedy", "principle": "States should facilitate effective non-judicial grievance mechanisms"},
    {"id": "UNGP-28", "pillar": "III", "category": "Access_Remedy", "principle": "Business should cooperate in State-based non-judicial mechanisms"},
    {"id": "UNGP-29", "pillar": "III", "category": "Access_Remedy", "principle": "Business must establish effective operational-level grievance mechanisms"},
    {"id": "UNGP-30", "pillar": "III", "category": "Access_Remedy", "principle": "Industry/multi-stakeholder grievance mechanisms — collaborative approaches"},
    {"id": "UNGP-31", "pillar": "III", "category": "Access_Remedy", "principle": "Effectiveness criteria: legitimate, accessible, predictable, equitable, transparent, rights-compatible, source of learning"},
]

# 85-item ESG DD Checklist across 15 categories
ESG_DD_CHECKLIST = [
    # Category 1: GHG & Climate
    {"id": "DD-E01", "category": "GHG_Climate", "item": "Scope 1/2/3 GHG inventory and verification status", "weight": 3},
    {"id": "DD-E02", "category": "GHG_Climate", "item": "Science-based targets (SBTi) status and trajectory", "weight": 3},
    {"id": "DD-E03", "category": "GHG_Climate", "item": "Climate transition plan quality and credibility", "weight": 3},
    {"id": "DD-E04", "category": "GHG_Climate", "item": "Physical climate risk exposure (TCFD scenario analysis)", "weight": 2},
    {"id": "DD-E05", "category": "GHG_Climate", "item": "Stranded asset risk in fixed asset base", "weight": 2},
    {"id": "DD-E06", "category": "GHG_Climate", "item": "Carbon price exposure and CBAM sensitivity", "weight": 2},
    # Category 2: Biodiversity & Land Use
    {"id": "DD-E07", "category": "Biodiversity", "item": "TNFD/LEAP nature dependency assessment", "weight": 2},
    {"id": "DD-E08", "category": "Biodiversity", "item": "Deforestation-free supply chain verification (EUDR)", "weight": 3},
    {"id": "DD-E09", "category": "Biodiversity", "item": "Protected area / critical habitat exposure", "weight": 2},
    {"id": "DD-E10", "category": "Biodiversity", "item": "Biodiversity Net Gain obligations (DEFRA Metric 4.0)", "weight": 1},
    # Category 3: Water
    {"id": "DD-E11", "category": "Water", "item": "Water withdrawal volumes and stress area exposure", "weight": 2},
    {"id": "DD-E12", "category": "Water", "item": "Wastewater treatment and discharge compliance", "weight": 2},
    {"id": "DD-E13", "category": "Water", "item": "Water pricing and commodity risk", "weight": 1},
    # Category 4: Pollution & Circular Economy
    {"id": "DD-E14", "category": "Pollution_Circular", "item": "Air quality NOx/SOx/PM2.5 permits and violations history", "weight": 2},
    {"id": "DD-E15", "category": "Pollution_Circular", "item": "Hazardous waste liabilities and remediation obligations", "weight": 3},
    {"id": "DD-E16", "category": "Pollution_Circular", "item": "Circular economy strategy and recycled content metrics", "weight": 1},
    {"id": "DD-E17", "category": "Pollution_Circular", "item": "PFAS and substances of concern inventory", "weight": 2},
    # Category 5: Supply Chain (E)
    {"id": "DD-E18", "category": "Supply_Chain_E", "item": "Tier 1-3 supplier GHG quantification", "weight": 2},
    {"id": "DD-E19", "category": "Supply_Chain_E", "item": "CSDDD value chain adverse impact mapping", "weight": 3},
    {"id": "DD-E20", "category": "Supply_Chain_E", "item": "EUDR commodity supply chain geolocation proofs", "weight": 2},
    # Category 6: Human Rights
    {"id": "DD-S01", "category": "Human_Rights", "item": "Human Rights Due Diligence (HRDD) policy and process (UNGP P17)", "weight": 3},
    {"id": "DD-S02", "category": "Human_Rights", "item": "Salient human rights issues identification (UNGP P18)", "weight": 3},
    {"id": "DD-S03", "category": "Human_Rights", "item": "HRIA for high-risk geographies (conflict zones, SIDS)", "weight": 3},
    {"id": "DD-S04", "category": "Human_Rights", "item": "Modern slavery / forced labour audit (ILO C29/C105)", "weight": 3},
    {"id": "DD-S05", "category": "Human_Rights", "item": "Child labour compliance in supply chain (ILO C138/C182)", "weight": 3},
    # Category 7: Labour & Working Conditions
    {"id": "DD-S06", "category": "Labour", "item": "Freedom of association / collective bargaining (ILO C87/C98)", "weight": 2},
    {"id": "DD-S07", "category": "Labour", "item": "Equal remuneration and non-discrimination (ILO C100/C111)", "weight": 2},
    {"id": "DD-S08", "category": "Labour", "item": "H&S incident rate, OSHA compliance and fatality record", "weight": 3},
    {"id": "DD-S09", "category": "Labour", "item": "Gender pay gap and diversity metrics", "weight": 2},
    {"id": "DD-S10", "category": "Labour", "item": "Employee turnover rate and talent retention strategy", "weight": 1},
    # Category 8: Community & Indigenous Peoples
    {"id": "DD-S11", "category": "Community", "item": "FPIC (Free, Prior, Informed Consent) compliance for indigenous peoples", "weight": 3},
    {"id": "DD-S12", "category": "Community", "item": "Community grievance mechanism quality (UNGP P29/P31)", "weight": 2},
    {"id": "DD-S13", "category": "Community", "item": "Community investment and social licence to operate", "weight": 1},
    # Category 9: Product Safety & Consumer
    {"id": "DD-S14", "category": "Product_Safety", "item": "Product liability and recall history", "weight": 2},
    {"id": "DD-S15", "category": "Product_Safety", "item": "Data privacy and GDPR/CCPA compliance", "weight": 2},
    {"id": "DD-S16", "category": "Product_Safety", "item": "AI system risk classification (EU AI Act)", "weight": 2},
    # Category 10: Board & Governance
    {"id": "DD-G01", "category": "Board_Governance", "item": "Board independence and diversity (gender, skills, independence ratio)", "weight": 2},
    {"id": "DD-G02", "category": "Board_Governance", "item": "Sustainability committee and ESG board oversight", "weight": 2},
    {"id": "DD-G03", "category": "Board_Governance", "item": "ESG-linked executive remuneration (KPIs and stretch targets)", "weight": 2},
    {"id": "DD-G04", "category": "Board_Governance", "item": "Dual-class share structures and minority shareholder protections", "weight": 2},
    {"id": "DD-G05", "category": "Board_Governance", "item": "Poison pills, golden parachutes, anti-takeover provisions", "weight": 1},
    # Category 11: Anti-Corruption & Compliance
    {"id": "DD-G06", "category": "Anti_Corruption", "item": "Anti-bribery / anti-corruption (FCPA, UK Bribery Act) programme", "weight": 3},
    {"id": "DD-G07", "category": "Anti_Corruption", "item": "Sanctions and AML compliance screening", "weight": 3},
    {"id": "DD-G08", "category": "Anti_Corruption", "item": "Whistleblower protection and speak-up culture", "weight": 2},
    {"id": "DD-G09", "category": "Anti_Corruption", "item": "Regulatory fines and enforcement actions history", "weight": 2},
    # Category 12: Reporting & Disclosure
    {"id": "DD-G10", "category": "Reporting", "item": "CSRD/ESRS reporting status and assurance level", "weight": 2},
    {"id": "DD-G11", "category": "Reporting", "item": "TCFD disclosure completeness and quality", "weight": 2},
    {"id": "DD-G12", "category": "Reporting", "item": "SFDR classification (Art 6/8/9) where applicable", "weight": 1},
    {"id": "DD-G13", "category": "Reporting", "item": "EU Taxonomy alignment assessment and DNSH verification", "weight": 2},
    # Category 13: Tax & Financial Integrity
    {"id": "DD-G14", "category": "Tax_Finance", "item": "Tax transparency report (GRI 207) and CbCR disclosure", "weight": 2},
    {"id": "DD-G15", "category": "Tax_Finance", "item": "Tax haven exposure and beneficial ownership clarity", "weight": 2},
    {"id": "DD-G16", "category": "Tax_Finance", "item": "Related party transactions and conflicts of interest", "weight": 2},
    # Category 14: Regulatory & Legal Liabilities
    {"id": "DD-G17", "category": "Regulatory_Legal", "item": "CSDDD Art 29 civil liability exposure assessment", "weight": 3},
    {"id": "DD-G18", "category": "Regulatory_Legal", "item": "Climate litigation risk (Urgenda-type, securities disclosure suits)", "weight": 2},
    {"id": "DD-G19", "category": "Regulatory_Legal", "item": "EU ETS compliance and carbon liability quantification", "weight": 2},
    {"id": "DD-G20", "category": "Regulatory_Legal", "item": "Environmental remediation and contaminated land liabilities", "weight": 3},
    {"id": "DD-G21", "category": "Regulatory_Legal", "item": "Ongoing litigation, regulatory investigations and fines pipeline", "weight": 2},
    # Category 15: Integration Readiness
    {"id": "DD-I01", "category": "Integration", "item": "ESG reporting system compatibility (data gaps, software)", "weight": 1},
    {"id": "DD-I02", "category": "Integration", "item": "Supply chain ESG onboarding capacity", "weight": 1},
    {"id": "DD-I03", "category": "Integration", "item": "SBTi target consolidation requirements", "weight": 2},
    {"id": "DD-I04", "category": "Integration", "item": "CSRD entity boundary consolidation", "weight": 2},
    {"id": "DD-I05", "category": "Integration", "item": "Cultural ESG gap assessment", "weight": 1},
]

DEAL_BREAKER_CRITERIA = [
    {"id": "DB-01", "criterion": "Active modern slavery / human trafficking in direct operations", "category": "Human_Rights"},
    {"id": "DB-02", "criterion": "Unmitigated child labour in Tier 1 supply chain (ILO C138/C182 breach)", "category": "Human_Rights"},
    {"id": "DB-03", "criterion": "Systematic indigenous peoples FPIC violations with ongoing displacement", "category": "Community"},
    {"id": "DB-04", "criterion": "Undisclosed environmental contamination with >$50M remediation liability", "category": "Environment"},
    {"id": "DB-05", "criterion": "Active FCPA or UK Bribery Act investigation / criminal prosecution", "category": "Anti_Corruption"},
    {"id": "DB-06", "criterion": "SDN or OFAC/EU sanctions list entity exposure (current)", "category": "Sanctions"},
    {"id": "DB-07", "criterion": "Stranded asset concentration >30% of fixed assets with no transition plan", "category": "Climate"},
    {"id": "DB-08", "criterion": "Fatality rate >industry 99th percentile in past 3 years", "category": "Labour"},
    {"id": "DB-09", "criterion": "Systematic GDPR material breaches with €20M+ exposure", "category": "Data_Privacy"},
    {"id": "DB-10", "criterion": "Greenwashing claims with regulatory investigation by ESMA/FCA/SEC", "category": "Governance"},
    {"id": "DB-11", "criterion": "Deforestation in primary/intact forest after Dec 2020 (EUDR cutoff)", "category": "Biodiversity"},
    {"id": "DB-12", "criterion": "Weapons manufacture for prohibited categories (cluster munitions, antipersonnel mines)", "category": "Arms"},
]

CSDDD_SCOPE_THRESHOLDS = {
    "EU_group_1": {"employees": 5000, "turnover_eur_m": 1500, "phased_application": "2027"},
    "EU_group_2": {"employees": 3000, "turnover_eur_m": 900, "phased_application": "2028"},
    "EU_group_3": {"employees": 1000, "turnover_eur_m": 450, "phased_application": "2029"},
    "non_EU_group_1": {"eu_net_turnover_eur_m": 1500, "phased_application": "2027"},
    "non_EU_group_2": {"eu_net_turnover_eur_m": 900, "phased_application": "2028"},
    "non_EU_group_3": {"eu_net_turnover_eur_m": 450, "phased_application": "2029"},
}

ESG_VALUATION_RANGES = {
    "climate_positive": {"range_pct": (2, 8), "typical_pct": 4, "driver": "Low stranded asset risk, strong transition plan"},
    "climate_negative": {"range_pct": (-15, -5), "typical_pct": -9, "driver": "High carbon liability, stranded assets, no transition"},
    "human_rights_positive": {"range_pct": (1, 4), "typical_pct": 2, "driver": "Strong HRDD, no violations, premium brand"},
    "human_rights_negative": {"range_pct": (-12, -3), "typical_pct": -6, "driver": "Modern slavery/child labour exposure, litigation"},
    "governance_positive": {"range_pct": (2, 7), "typical_pct": 3, "driver": "Strong board, no corruption, transparent reporting"},
    "governance_negative": {"range_pct": (-10, -3), "typical_pct": -5, "driver": "Corruption, related party exposure, poor oversight"},
    "biodiversity_negative": {"range_pct": (-8, -2), "typical_pct": -4, "driver": "EUDR breach, protected habitat impact, remediation"},
    "reporting_positive": {"range_pct": (1, 3), "typical_pct": 1.5, "driver": "CSRD/TCFD complete disclosure, third-party assured"},
    "labour_negative": {"range_pct": (-6, -2), "typical_pct": -3, "driver": "High fatality rate, systemic H&S violations"},
}

ILO_CORE_CONVENTIONS = [
    {"convention": "C29", "name": "Forced Labour Convention 1930", "subject": "Elimination of forced or compulsory labour"},
    {"convention": "C87", "name": "Freedom of Association 1948", "subject": "Right to organise and form trade unions"},
    {"convention": "C98", "name": "Right to Organise and Collective Bargaining 1949", "subject": "Collective bargaining rights"},
    {"convention": "C100", "name": "Equal Remuneration 1951", "subject": "Equal pay for work of equal value"},
    {"convention": "C105", "name": "Abolition of Forced Labour 1957", "subject": "Prohibition of forced labour as punishment"},
    {"convention": "C111", "name": "Discrimination (Employment) 1958", "subject": "Non-discrimination in employment"},
    {"convention": "C138", "name": "Minimum Age Convention 1973", "subject": "Minimum age for employment"},
    {"convention": "C182", "name": "Worst Forms of Child Labour 1999", "subject": "Elimination of worst forms of child labour"},
]


# ── Core Engine Functions ──────────────────────────────────────────────────────

def assess_esg_due_diligence(
    entity_id: str,
    deal_name: str,
    target_sector: str,
    target_country: str,
    deal_value_usd: float,
) -> dict[str, Any]:
    rng = random.Random(hash(str(entity_id)) & 0xFFFFFFFF)

    checklist_results: list[dict] = []
    red_flags: list[dict] = []
    e_score_sum, s_score_sum, g_score_sum = 0.0, 0.0, 0.0
    e_count, s_count, g_count = 0, 0, 0

    for item in ESG_DD_CHECKLIST:
        item_rng = random.Random(hash(f"{entity_id}_{item['id']}") & 0xFFFFFFFF)
        status_val = item_rng.random()
        if status_val >= 0.75:
            status = "satisfactory"
            risk = "low"
        elif status_val >= 0.45:
            status = "requires_attention"
            risk = "medium"
        elif status_val >= 0.2:
            status = "material_gap"
            risk = "high"
        else:
            status = "critical_finding"
            risk = "critical"

        score = 1.0 if status == "satisfactory" else 0.65 if status == "requires_attention" else 0.3 if status == "material_gap" else 0.0
        cat = item["category"]

        if cat in ("GHG_Climate", "Biodiversity", "Water", "Pollution_Circular", "Supply_Chain_E"):
            e_score_sum += score * item["weight"]
            e_count += item["weight"]
        elif cat in ("Human_Rights", "Labour", "Community", "Product_Safety"):
            s_score_sum += score * item["weight"]
            s_count += item["weight"]
        else:
            g_score_sum += score * item["weight"]
            g_count += item["weight"]

        if status in ("material_gap", "critical_finding"):
            red_flags.append({"id": item["id"], "category": cat, "item": item["item"], "severity": risk})

        checklist_results.append({
            "id": item["id"],
            "category": cat,
            "item": item["item"],
            "status": status,
            "risk_level": risk,
            "score": score,
            "weight": item["weight"],
        })

    e_score = e_score_sum / e_count if e_count else 0
    s_score = s_score_sum / s_count if s_count else 0
    g_score = g_score_sum / g_count if g_count else 0
    overall_esg_score = (e_score * 0.35 + s_score * 0.35 + g_score * 0.30)

    # ESG premium/discount on deal value
    adj_pct = (overall_esg_score - 0.5) * 20  # -10% to +10% base
    esg_valuation_adjustment_pct = round(adj_pct, 2)
    esg_valuation_adjustment_usd = deal_value_usd * esg_valuation_adjustment_pct / 100

    # CSDDD Art 3 scope
    csddd_scope_group = "EU_group_2" if deal_value_usd > 500e6 else "EU_group_3"
    csddd_scope = CSDDD_SCOPE_THRESHOLDS.get(csddd_scope_group, {})

    return {
        "entity_id": entity_id,
        "deal_name": deal_name,
        "target_sector": target_sector,
        "target_country": target_country,
        "deal_value_usd": round(deal_value_usd, 0),
        "esg_score_breakdown": {
            "environmental": round(e_score, 3),
            "social": round(s_score, 3),
            "governance": round(g_score, 3),
            "overall": round(overall_esg_score, 3),
        },
        "esg_valuation_adjustment_pct": esg_valuation_adjustment_pct,
        "esg_valuation_adjustment_usd": round(esg_valuation_adjustment_usd, 0),
        "red_flags": red_flags,
        "red_flag_count": len(red_flags),
        "deal_breaker_check": any(f["severity"] == "critical" for f in red_flags),
        "checklist_items_assessed": len(checklist_results),
        "csddd_art3_scope": {"scope_group": csddd_scope_group, "thresholds": csddd_scope},
        "ungp_dd_required": any(f["category"] == "Human_Rights" for f in red_flags),
        "assessed_at": datetime.now(timezone.utc).isoformat(),
    }


def score_ungp_alignment(
    entity_id: str,
    target_company: str,
    sector: str,
) -> dict[str, Any]:
    rng = random.Random(hash(str(entity_id)) & 0xFFFFFFFF)

    principle_scores: list[dict] = []
    pillar_sums: dict[str, float] = {"I": 0, "II": 0, "III": 0}
    pillar_counts: dict[str, int] = {"I": 0, "II": 0, "III": 0}

    for p in UNGP_PRINCIPLES:
        p_rng = random.Random(hash(f"{entity_id}_{p['id']}") & 0xFFFFFFFF)
        score = round(p_rng.uniform(0.2, 1.0), 2)
        pillar_sums[p["pillar"]] += score
        pillar_counts[p["pillar"]] += 1
        principle_scores.append({
            "id": p["id"],
            "pillar": p["pillar"],
            "category": p["category"],
            "principle": p["principle"],
            "alignment_score": score,
            "evidence_available": score >= 0.7,
            "gap_identified": score < 0.5,
        })

    pillar_averages = {
        "Pillar_I_State_Protect": round(pillar_sums["I"] / pillar_counts["I"], 3) if pillar_counts["I"] else 0,
        "Pillar_II_Business_Respect": round(pillar_sums["II"] / pillar_counts["II"], 3) if pillar_counts["II"] else 0,
        "Pillar_III_Access_Remedy": round(pillar_sums["III"] / pillar_counts["III"], 3) if pillar_counts["III"] else 0,
    }
    overall_ungp = sum(pillar_averages.values()) / 3

    # ILO core conventions check
    ilo_compliance: list[dict] = []
    for conv in ILO_CORE_CONVENTIONS:
        c_rng = random.Random(hash(f"{entity_id}_{conv['convention']}") & 0xFFFFFFFF)
        compliant = c_rng.random() > 0.25
        ilo_compliance.append({
            "convention": conv["convention"],
            "name": conv["name"],
            "subject": conv["subject"],
            "compliant": compliant,
            "evidence_type": "audit_certificate" if compliant else "none",
            "salient_issue": not compliant,
        })

    # HRIA requirement flag
    high_risk_sectors = ["mining", "agriculture", "garments", "construction", "electronics", "fishing"]
    hria_required = sector.lower() in high_risk_sectors or overall_ungp < 0.6

    # OECD Due Diligence Guidance 6 steps
    oecd_rbc_steps = {
        "step1_embed_rbc": round(rng.uniform(0.3, 1.0), 2),
        "step2_identify_impacts": round(rng.uniform(0.3, 1.0), 2),
        "step3_cease_prevent": round(rng.uniform(0.3, 1.0), 2),
        "step4_track_implementation": round(rng.uniform(0.2, 0.9), 2),
        "step5_communicate": round(rng.uniform(0.2, 0.9), 2),
        "step6_provide_remedy": round(rng.uniform(0.2, 0.85), 2),
    }
    oecd_overall = sum(oecd_rbc_steps.values()) / len(oecd_rbc_steps)

    return {
        "entity_id": entity_id,
        "target_company": target_company,
        "sector": sector,
        "overall_ungp_score": round(overall_ungp, 3),
        "pillar_scores": pillar_averages,
        "principle_scores": principle_scores,
        "ilo_core_conventions": ilo_compliance,
        "ilo_violations": [c for c in ilo_compliance if not c["compliant"]],
        "hria_required": hria_required,
        "oecd_rbc_6_steps": oecd_rbc_steps,
        "oecd_rbc_overall": round(oecd_overall, 3),
        "remedy_mechanism_adequate": pillar_averages["Pillar_III_Access_Remedy"] >= 0.65,
        "assessed_at": datetime.now(timezone.utc).isoformat(),
    }


def calculate_esg_valuation_impact(
    entity_id: str,
    base_valuation_usd: float,
    esg_findings: dict[str, Any],
) -> dict[str, Any]:
    rng = random.Random(hash(str(entity_id)) & 0xFFFFFFFF)

    adjustments: list[dict] = []
    total_adjustment_usd = 0.0

    for finding_key, finding_data in esg_findings.items():
        val_range = ESG_VALUATION_RANGES.get(finding_key, {"range_pct": (-5, 5), "typical_pct": 0, "driver": "Unknown"})
        adj_pct = float(finding_data) if isinstance(finding_data, (int, float)) else val_range["typical_pct"]
        adj_usd = base_valuation_usd * adj_pct / 100
        total_adjustment_usd += adj_usd
        adjustments.append({
            "finding": finding_key,
            "adjustment_pct": adj_pct,
            "adjustment_usd": round(adj_usd, 0),
            "driver": val_range["driver"],
        })

    # Climate liability quantification
    stranded_asset_pct = rng.uniform(0.05, 0.25)
    carbon_cost_usd = rng.uniform(1e6, 50e6)
    litigation_risk_usd = rng.uniform(0, 30e6)
    climate_liability_total = (base_valuation_usd * stranded_asset_pct + carbon_cost_usd + litigation_risk_usd)

    # S pillar adjustments
    wage_gap_adj_pct = rng.uniform(-3, 0)
    turnover_adj_pct = rng.uniform(-2, 0.5)
    s_adjustment_usd = base_valuation_usd * (wage_gap_adj_pct + turnover_adj_pct) / 100

    # G pillar adjustments
    board_score = rng.uniform(0.3, 1.0)
    ownership_conc = rng.uniform(0.1, 0.8)
    g_adj_pct = (board_score - 0.5) * 6 - (ownership_conc - 0.3) * 4
    g_adjustment_usd = base_valuation_usd * g_adj_pct / 100

    # W&I coverage
    wi_coverage_usd = rng.uniform(base_valuation_usd * 0.05, base_valuation_usd * 0.2)
    wi_esg_excluded = ["environmental_contamination", "modern_slavery", "sanctions"]

    # Integration costs
    integration_cost_usd = base_valuation_usd * rng.uniform(0.02, 0.08)

    adjusted_valuation = base_valuation_usd + total_adjustment_usd - climate_liability_total + s_adjustment_usd + g_adjustment_usd

    return {
        "entity_id": entity_id,
        "base_valuation_usd": round(base_valuation_usd, 0),
        "adjusted_valuation_usd": round(adjusted_valuation, 0),
        "total_esg_adjustment_pct": round((adjusted_valuation - base_valuation_usd) / base_valuation_usd * 100, 2),
        "esg_finding_adjustments": adjustments,
        "climate_liability": {
            "stranded_asset_exposure_usd": round(base_valuation_usd * stranded_asset_pct, 0),
            "carbon_cost_exposure_usd": round(carbon_cost_usd, 0),
            "climate_litigation_risk_usd": round(litigation_risk_usd, 0),
            "total_climate_liability_usd": round(climate_liability_total, 0),
        },
        "social_adjustments": {
            "wage_gap_adj_pct": round(wage_gap_adj_pct, 2),
            "turnover_adj_pct": round(turnover_adj_pct, 2),
            "s_total_usd": round(s_adjustment_usd, 0),
        },
        "governance_adjustments": {
            "board_composition_score": round(board_score, 3),
            "ownership_concentration": round(ownership_conc, 3),
            "g_total_usd": round(g_adjustment_usd, 0),
        },
        "warranty_indemnity": {
            "coverage_usd": round(wi_coverage_usd, 0),
            "esg_reps_excluded": wi_esg_excluded,
            "bespoke_esg_reps_recommended": True,
        },
        "integration_cost_estimate_usd": round(integration_cost_usd, 0),
        "assessed_at": datetime.now(timezone.utc).isoformat(),
    }


def plan_post_merger_integration(
    entity_id: str,
    acquirer_profile: dict[str, Any],
    target_profile: dict[str, Any],
    close_date: str,
) -> dict[str, Any]:
    rng = random.Random(hash(str(entity_id)) & 0xFFFFFFFF)

    try:
        close_dt = datetime.fromisoformat(close_date)
    except Exception:
        close_dt = datetime.now(timezone.utc)

    day30 = (close_dt + timedelta(days=30)).strftime("%Y-%m-%d")
    day60 = (close_dt + timedelta(days=60)).strftime("%Y-%m-%d")
    day100 = (close_dt + timedelta(days=100)).strftime("%Y-%m-%d")
    month6 = (close_dt + timedelta(days=180)).strftime("%Y-%m-%d")
    year1 = (close_dt + timedelta(days=365)).strftime("%Y-%m-%d")

    # Cultural ESG gap score
    acquirer_esg_maturity = acquirer_profile.get("esg_maturity", rng.uniform(0.4, 0.9))
    target_esg_maturity = target_profile.get("esg_maturity", rng.uniform(0.3, 0.8))
    cultural_esg_gap = round(abs(acquirer_esg_maturity - target_esg_maturity), 3)

    plan = {
        "days_1_30": {
            "deadline": day30,
            "workstream": "Governance Alignment",
            "actions": [
                "Appoint integration ESG steering committee with C-suite sponsor",
                "Assess target board ESG committee structure and mandate",
                "Map target ESG reporting calendar to acquirer CSRD/TCFD timelines",
                "Initial HR review: confirm no outstanding UNGP violations or investigations",
                "Sanctions re-screening of target entity, subsidiaries and key personnel",
            ],
        },
        "days_31_60": {
            "deadline": day60,
            "workstream": "Reporting Harmonisation",
            "actions": [
                "Gap analysis: target vs acquirer CSRD ESRS entity boundary",
                "GHG protocol consolidation approach (operational vs equity share control)",
                "SFDR entity-level PAI data collection protocol for combined entity",
                "Identify EU Taxonomy-aligned/eligible assets in target asset base",
                "Data room ESG disclosures comparison report and gap register",
            ],
        },
        "days_61_100": {
            "deadline": day100,
            "workstream": "Policy Adoption & Supply Chain",
            "actions": [
                "Target adopts acquirer Human Rights Policy and Code of Conduct",
                "CSDDD due diligence cascade: map new Tier 1-3 supplier additions",
                "SBTi target revision: re-submit combined entity Scope 1/2/3 for validation",
                "ESG KPI harmonisation: align metric definitions and data collection",
                "Cultural ESG integration assessment — employee pulse survey on ESG values alignment",
            ],
        },
        "months_6_12": {
            "deadline": year1,
            "workstream": "Systems Integration",
            "actions": [
                "Integrate target into ESG data platform (GHG accounting, water, waste)",
                "Combined entity first CSRD double materiality assessment",
                "ESRS disclosure consolidation in first integrated sustainability report",
                "ESG-linked financing terms review: SLL covenants, green bond allocation",
                f"Cultural gap closure plan: training for {round(cultural_esg_gap * 100, 0):.0f}% gap in ESG maturity",
            ],
        },
    }

    sbti_revision_required = (
        acquirer_profile.get("has_sbti", rng.random() > 0.4)
        and abs(target_profile.get("revenue_share", rng.uniform(0.1, 0.5))) > 0.1
    )

    return {
        "entity_id": entity_id,
        "close_date": close_date,
        "acquirer_esg_maturity": round(acquirer_esg_maturity, 3),
        "target_esg_maturity": round(target_esg_maturity, 3),
        "cultural_esg_gap_score": cultural_esg_gap,
        "integration_complexity": "high" if cultural_esg_gap > 0.3 else "medium" if cultural_esg_gap > 0.15 else "low",
        "sbti_revision_required": sbti_revision_required,
        "csrd_scope_expansion": True,
        "csddd_supply_chain_expansion": True,
        "100_day_plan": plan,
        "estimated_integration_cost_usd": round(rng.uniform(500_000, 5_000_000), 0),
        "assessed_at": datetime.now(timezone.utc).isoformat(),
    }


def generate_dd_report(
    entity_id: str,
    deal_name: str,
) -> dict[str, Any]:
    rng = random.Random(hash(str(entity_id)) & 0xFFFFFFFF)

    # Simulate an assessment
    dd = assess_esg_due_diligence(entity_id, deal_name, "industrials", "DE", rng.uniform(200e6, 2e9))
    ungp = score_ungp_alignment(entity_id, deal_name, "manufacturing")

    # RAG status by category
    categories = list({item["category"] for item in ESG_DD_CHECKLIST})
    rag_status: list[dict] = []
    for cat in categories:
        cat_rng = random.Random(hash(f"{entity_id}_{cat}") & 0xFFFFFFFF)
        score = cat_rng.uniform(0.2, 0.95)
        rag = "green" if score >= 0.75 else "amber" if score >= 0.5 else "red"
        rag_status.append({"category": cat, "score": round(score, 3), "rag": rag})

    # Value creation opportunities
    value_creation = [
        {"opportunity": "Carbon credit monetisation from renewable energy assets", "value_usd": round(rng.uniform(1e6, 20e6), 0)},
        {"opportunity": "CBAM border adjustment savings from EU supply chain integration", "value_usd": round(rng.uniform(500_000, 5e6), 0)},
        {"opportunity": "Green bond issuance for EU Taxonomy-aligned capex", "value_usd": round(rng.uniform(50e6, 500e6), 0)},
        {"opportunity": "Premium ESG labelling for SFDR Art 9 product reclassification", "value_usd": round(rng.uniform(2e6, 15e6), 0)},
        {"opportunity": "Sustainability-linked loan repricing at lower coupon", "value_usd": round(rng.uniform(1e6, 8e6), 0)},
    ]

    # Regulatory risk flags
    regulatory_flags = []
    if dd["deal_breaker_check"]:
        regulatory_flags.append("DEAL-BREAKER: Critical ESG finding — deal requires remediation prior to close")
    if rng.random() > 0.6:
        regulatory_flags.append("CSDDD Art 29 civil liability exposure identified in supply chain")
    if rng.random() > 0.7:
        regulatory_flags.append("EUDR deforestation-free documentation incomplete — Regulation (EU) 2023/1115")
    if rng.random() > 0.65:
        regulatory_flags.append("SFDR Article reclassification risk post-acquisition (Art 8 → Art 6)")

    # Comparable benchmarks
    comparables = [
        {"deal": "Industrial Corp A - ESG DD 2023", "esg_score": round(rng.uniform(0.45, 0.85), 2), "adj_pct": round(rng.uniform(-8, 6), 1)},
        {"deal": "Manufacturing Ltd B - ESG DD 2024", "esg_score": round(rng.uniform(0.5, 0.9), 2), "adj_pct": round(rng.uniform(-5, 8), 1)},
        {"deal": "Sector Peer C - ESG DD 2024", "esg_score": round(rng.uniform(0.4, 0.8), 2), "adj_pct": round(rng.uniform(-10, 5), 1)},
    ]

    # Deal-breaker assessment
    db_assessment = []
    for db in DEAL_BREAKER_CRITERIA:
        db_rng = random.Random(hash(f"{entity_id}_{db['id']}") & 0xFFFFFFFF)
        triggered = db_rng.random() < 0.08  # 8% chance each
        db_assessment.append({
            "id": db["id"],
            "criterion": db["criterion"],
            "category": db["category"],
            "triggered": triggered,
            "evidence": "Audit finding ref: " + db["id"] if triggered else "No evidence found",
        })

    deal_breakers_triggered = [d for d in db_assessment if d["triggered"]]

    return {
        "entity_id": entity_id,
        "deal_name": deal_name,
        "report_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "investment_committee_summary": {
            "overall_esg_score": dd["esg_score_breakdown"]["overall"],
            "red_flags_count": dd["red_flag_count"],
            "deal_breakers_triggered": len(deal_breakers_triggered),
            "esg_valuation_adjustment_pct": dd["esg_valuation_adjustment_pct"],
            "ungp_score": ungp["overall_ungp_score"],
            "recommendation": "proceed_with_conditions" if not deal_breakers_triggered else "escalate_to_board",
        },
        "material_findings_rag": sorted(rag_status, key=lambda x: x["score"]),
        "value_creation_opportunities": value_creation,
        "total_value_creation_usd": sum(v["value_usd"] for v in value_creation),
        "regulatory_risk_flags": regulatory_flags,
        "deal_breaker_assessment": {
            "items": db_assessment,
            "triggered": deal_breakers_triggered,
            "any_triggered": bool(deal_breakers_triggered),
        },
        "comparable_deals": comparables,
        "esg_reps_warranties_recommended": [
            "Seller warrants: no undisclosed environmental contamination >$1M",
            "Seller warrants: no ongoing modern slavery in Tier 1 supply chain",
            "Seller warrants: GHG data materially complete per GHG Protocol",
            "Seller warrants: no active FCPA/Bribery Act investigation",
            "Seller warrants: EUDR commodity lots comply with deforestation cutoff Dec 2020",
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
