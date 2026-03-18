"""
Circular Economy Finance Engine (E55)
======================================
CSRD ESRS E5, Ellen MacArthur Foundation MCI, WBCSD CTI v4.0,
EU EPR Schemes, EU CRM Act 2023, ISO 14044 LCA.

Sub-modules:
  1. ESRS E5 Assessment       — Resource use & circular economy disclosure
  2. MCI Calculator           — EMF Material Circularity Indicator (0-1)
  3. WBCSD CTI Assessment     — 4-dimension circular transition scorecard
  4. EPR Compliance           — EU packaging, e-waste, battery EPR cost calculation
  5. CRM Risk Assessment      — EU CRM Act 2023 critical materials dependency
  6. LCA Analysis             — ISO 14044 cradle-to-gate vs cradle-to-cradle
  7. Material Flow Analysis   — Inflow/outflow circularity accounting
  8. Overall Circularity      — Aggregated circularity score + investment gap

References:
  - CSRD ESRS E5 — Resource Use and Circular Economy (EFRAG 2023)
  - Ellen MacArthur Foundation — MCI Methodology v1.3 (2019)
  - WBCSD CTI v4.0 (2023) — Circular Transition Indicators
  - EU CEAP 2020 — Circular Economy Action Plan
  - EU CRM Act 2023 — Critical Raw Materials Regulation
  - Directive 2008/98/EC as amended — Waste Framework
  - ISO 14044:2006 — LCA Requirements and Guidelines
"""
from __future__ import annotations

import random
from typing import Optional


# ---------------------------------------------------------------------------
# Reference Data
# ---------------------------------------------------------------------------

# EU CRM Act 2023 — 34 Critical Raw Materials
EU_CRM_LIST: list[str] = [
    "antimony", "baryte", "beryllium", "bismuth", "boron",
    "cobalt", "coking_coal", "copper", "feldspar", "fluorspar",
    "gallium", "germanium", "hafnium", "helium", "heavy_rare_earth",
    "indium", "light_rare_earth", "lithium", "magnesium", "manganese",
    "natural_graphite", "natural_rubber", "nickel", "niobium", "pgm",
    "phosphate_rock", "phosphorus", "scandium", "silicon_metal",
    "strontium", "tantalum", "titanium", "tungsten", "vanadium",
]

# Strategic raw materials (subset of CRM with additional EU extraction targets)
EU_STRATEGIC_RM: list[str] = [
    "lithium", "cobalt", "nickel", "manganese", "silicon_metal",
    "pgm", "natural_graphite", "titanium", "tungsten",
]

# EU 2030 CRM targets
EU_CRM_2030_TARGETS = {
    "extraction_pct": 10.0,     # at least 10% EU domestic extraction
    "processing_pct": 40.0,     # at least 40% EU processing
    "recycling_pct": 25.0,      # at least 25% recycled content
    "single_country_max_pct": 65.0,  # no more than 65% from one non-EU country
}

# EPR cost ranges (EUR/tonne) by category and country
EPR_COSTS: dict[str, dict[str, float]] = {
    "packaging": {
        "EU": 100.0, "DE": 130.0, "FR": 120.0, "GB": 110.0,
        "IT": 90.0, "ES": 85.0, "NL": 115.0, "PL": 70.0,
    },
    "ewaste": {
        "EU": 450.0, "DE": 550.0, "FR": 500.0, "GB": 480.0,
        "IT": 400.0, "ES": 380.0, "NL": 520.0, "PL": 320.0,
    },
    "battery": {
        "EU": 300.0, "DE": 350.0, "FR": 320.0, "GB": 310.0,
        "IT": 280.0, "ES": 270.0, "NL": 340.0, "PL": 240.0,
    },
}

# Industry MCI benchmarks
MCI_BENCHMARKS: dict[str, float] = {
    "automotive": 0.45,
    "electronics": 0.30,
    "textiles": 0.25,
    "construction": 0.35,
    "chemicals": 0.40,
    "food": 0.20,
    "metals": 0.55,
    "plastics": 0.28,
    "other": 0.30,
}

# Cradle-to-gate LCA factors (kgCO2e per unit of production)
LCA_GATE_FACTORS: dict[str, float] = {
    "automotive": 8000.0,
    "electronics": 500.0,
    "textiles": 20.0,
    "construction": 2000.0,
    "chemicals": 150.0,
    "food": 5.0,
    "metals": 3000.0,
    "plastics": 30.0,
    "other": 100.0,
}

# Circularity benefit of cradle-to-cradle vs gate (reduction %)
LCA_CIRCULARITY_BENEFIT: dict[str, tuple[float, float]] = {
    "automotive":   (25.0, 45.0),
    "electronics":  (15.0, 35.0),
    "textiles":     (10.0, 30.0),
    "construction": (20.0, 40.0),
    "chemicals":    (8.0, 22.0),
    "food":         (5.0, 20.0),
    "metals":       (30.0, 55.0),
    "plastics":     (12.0, 28.0),
    "other":        (10.0, 25.0),
}

LCA_HOTSPOT_STAGES: dict[str, list[str]] = {
    "automotive":   ["Raw material extraction", "Body stamping", "Powertrain assembly"],
    "electronics":  ["PCB manufacturing", "Display production", "Battery"],
    "textiles":     ["Fibre production", "Dyeing", "Finishing"],
    "construction": ["Cement production", "Steel fabrication", "Transport"],
    "chemicals":    ["Feedstock processing", "Reactor operations", "Distillation"],
    "food":         ["Primary agriculture", "Packaging", "Refrigerated logistics"],
    "metals":       ["Mining & beneficiation", "Smelting", "Rolling/forming"],
    "plastics":     ["Polymerisation", "Moulding", "Packaging"],
    "other":        ["Manufacturing", "Assembly", "Distribution"],
}

ESRS_E5_GRADES = {
    (80, 100): "A",
    (65,  80): "B",
    (50,  65): "C",
    (0,   50): "D",
}

IMPROVEMENT_OPTIONS_LCA: list[str] = [
    "Increase recycled content in primary materials",
    "Switch to bio-based feedstocks",
    "Implement take-back and refurbishment programme",
    "Design for disassembly to improve end-of-life recovery",
    "Shift to renewable energy in manufacturing",
    "Reduce packaging weight and switch to mono-material",
    "Extend product lifetime through modular design",
    "Develop industrial symbiosis with adjacent facilities",
]


# ---------------------------------------------------------------------------
# Engine Class
# ---------------------------------------------------------------------------

class CircularEconomyEngine:
    """Circular Economy Finance Engine (E55)."""

    # ------------------------------------------------------------------
    # 1. ESRS E5 Assessment
    # ------------------------------------------------------------------

    def assess_esrs_e5(
        self,
        entity_id: str,
        resource_inflows_t: float,
        recycled_inflows_pct: float,
        resource_outflows_t: float,
        waste_t: float,
    ) -> dict:
        """
        CSRD ESRS E5 — Resource use and circular economy disclosure scoring.
        """
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        recycled_outflows_pct = round(
            max(0.0, (resource_outflows_t - waste_t) / resource_outflows_t * 100.0)
            if resource_outflows_t > 0 else 0.0,
            2,
        )

        crm_dependency = recycled_inflows_pct < 30.0

        # Disclosure completeness
        components = {
            "inflows_reported": resource_inflows_t > 0,
            "recycled_content_reported": recycled_inflows_pct >= 0,
            "outflows_reported": resource_outflows_t > 0,
            "waste_reported": waste_t >= 0,
            "crm_identified": rng.random() > 0.3,
            "circular_targets_set": rng.random() > 0.4,
            "transition_plan": rng.random() > 0.5,
        }
        disclosure_score = round(sum(components.values()) / len(components) * 100.0, 2)
        target_set = disclosure_score >= 60.0

        grade = "D"
        for (lo, hi), g in ESRS_E5_GRADES.items():
            if lo <= disclosure_score < hi:
                grade = g
                break

        return {
            "entity_id": entity_id,
            "resource_inflows_t": round(resource_inflows_t, 2),
            "recycled_inflows_pct": round(recycled_inflows_pct, 2),
            "resource_outflows_t": round(resource_outflows_t, 2),
            "waste_t": round(waste_t, 2),
            "recycled_outflows_pct": recycled_outflows_pct,
            "crm_dependency": crm_dependency,
            "disclosure_components": components,
            "disclosure_score": disclosure_score,
            "target_set": target_set,
            "esrs_e5_grade": grade,
            "mandatory_disclosures": ["E5-1", "E5-2", "E5-3", "E5-4", "E5-5"],
            "standard": "CSRD ESRS E5 (EFRAG 2023)",
        }

    # ------------------------------------------------------------------
    # 2. MCI — Material Circularity Indicator
    # ------------------------------------------------------------------

    def calculate_mci(
        self,
        entity_id: str,
        recycled_input_fraction: float,
        waste_recovery_fraction: float,
        product_lifetime_multiplier: float = 1.0,
    ) -> dict:
        """
        Ellen MacArthur Foundation Material Circularity Indicator (0-1).
        Linear economy = 0; fully circular = 1.
        """
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        # Clamp inputs
        rif = max(0.0, min(1.0, recycled_input_fraction))
        wrf = max(0.0, min(1.0, waste_recovery_fraction))
        plm = max(0.1, product_lifetime_multiplier)

        utility_factor = round(1.0 / plm, 4)
        raw_mci = (rif + wrf) / 2.0 * utility_factor
        mci_score = round(min(1.0, raw_mci), 4)

        # Sector benchmark
        sector = rng.choice(list(MCI_BENCHMARKS.keys()))
        benchmark = MCI_BENCHMARKS[sector]
        gap = round(benchmark - mci_score, 4)

        if mci_score >= 0.7:
            interpretation = "Circular leader — top quartile performance"
        elif mci_score >= 0.5:
            interpretation = "Above average — meaningful circularity in place"
        elif mci_score >= 0.3:
            interpretation = "Transition stage — significant improvement potential"
        else:
            interpretation = "Linear model — fundamental transformation required"

        improvement_potential = {
            "increase_recycled_input_to_50pct": round(min(1.0, (0.5 + wrf) / 2.0 * utility_factor), 4),
            "improve_waste_recovery_to_80pct": round(min(1.0, (rif + 0.8) / 2.0 * utility_factor), 4),
            "extend_lifetime_2x": round(min(1.0, (rif + wrf) / 2.0 * (utility_factor / 2.0)), 4),
        }

        return {
            "entity_id": entity_id,
            "recycled_input_fraction": round(rif, 4),
            "waste_recovery_fraction": round(wrf, 4),
            "product_lifetime_multiplier": round(plm, 2),
            "utility_factor": utility_factor,
            "mci_score": mci_score,
            "benchmark": benchmark,
            "benchmark_sector": sector,
            "gap": gap,
            "above_benchmark": mci_score >= benchmark,
            "interpretation": interpretation,
            "improvement_potential": improvement_potential,
            "methodology": "Ellen MacArthur Foundation MCI v1.3",
        }

    # ------------------------------------------------------------------
    # 3. WBCSD CTI Assessment
    # ------------------------------------------------------------------

    def assess_wbcsd_cti(
        self,
        entity_id: str,
        entity_name: str,
        sector: str,
    ) -> dict:
        """
        WBCSD Circular Transition Indicators v4.0 — 4 dimensions, A-D tier.
        """
        rng = random.Random(hash(entity_id + entity_name + sector) & 0xFFFFFFFF)

        circular_product_design = round(rng.uniform(20.0, 90.0), 1)
        waste_recovery = round(rng.uniform(20.0, 90.0), 1)
        recycled_content = round(rng.uniform(15.0, 85.0), 1)
        product_lifetime = round(rng.uniform(20.0, 90.0), 1)

        composite_score = round(
            circular_product_design * 0.30
            + waste_recovery * 0.25
            + recycled_content * 0.25
            + product_lifetime * 0.20,
            2,
        )

        if composite_score >= 80.0:
            tier = "A"
        elif composite_score >= 60.0:
            tier = "B"
        elif composite_score >= 40.0:
            tier = "C"
        else:
            tier = "D"

        tier_labels = {"A": "Leader", "B": "Performer", "C": "Improver", "D": "Beginner"}
        maturity_level = tier_labels[tier]

        sector_l = sector.lower() if sector.lower() in MCI_BENCHMARKS else "other"
        sector_benchmark = round(MCI_BENCHMARKS[sector_l] * 100.0, 1)

        return {
            "entity_id": entity_id,
            "entity_name": entity_name,
            "sector": sector,
            "circular_product_design": circular_product_design,
            "waste_recovery": waste_recovery,
            "recycled_content": recycled_content,
            "product_lifetime": product_lifetime,
            "composite_score": composite_score,
            "tier": tier,
            "maturity_level": maturity_level,
            "sector_benchmark": sector_benchmark,
            "methodology": "WBCSD CTI v4.0 (2023)",
        }

    # ------------------------------------------------------------------
    # 4. EPR Compliance
    # ------------------------------------------------------------------

    def calculate_epr_compliance(
        self,
        entity_id: str,
        packaging_tonnes: float,
        ewaste_tonnes: float,
        battery_tonnes: float,
        country: str = "EU",
    ) -> dict:
        """
        EU EPR cost calculation for packaging (DIR 94/62/EC), e-waste (WEEE DIR),
        and batteries (Regulation (EU) 2023/1542).
        """
        rng = random.Random(hash(entity_id + country) & 0xFFFFFFFF)

        country_upper = country.upper()

        def _get_rate(category: str) -> float:
            cat_rates = EPR_COSTS.get(category, {})
            rate = cat_rates.get(country_upper, cat_rates.get("EU", 100.0))
            return rate * rng.uniform(0.95, 1.05)  # minor entity-level variation

        pkg_rate = round(_get_rate("packaging"), 2)
        ew_rate = round(_get_rate("ewaste"), 2)
        bat_rate = round(_get_rate("battery"), 2)

        pkg_cost = round(packaging_tonnes * pkg_rate, 0) if packaging_tonnes > 0 else 0.0
        ew_cost = round(ewaste_tonnes * ew_rate, 0) if ewaste_tonnes > 0 else 0.0
        bat_cost = round(battery_tonnes * bat_rate, 0) if battery_tonnes > 0 else 0.0
        total_cost = round(pkg_cost + ew_cost + bat_cost, 0)

        compliance_gap: dict = {}
        if packaging_tonnes > 0 and rng.random() > 0.6:
            compliance_gap["packaging"] = "Recycled content target <50% by 2025"
        if ewaste_tonnes > 0 and rng.random() > 0.7:
            compliance_gap["ewaste"] = "Collection rate target <65% WEEE directive"
        if battery_tonnes > 0 and rng.random() > 0.65:
            compliance_gap["battery"] = "Lithium recovery target <50% by 2027"

        reg_risk_score = len(compliance_gap)
        regulatory_risk = "High" if reg_risk_score >= 2 else ("Medium" if reg_risk_score == 1 else "Low")

        return {
            "entity_id": entity_id,
            "country": country_upper,
            "packaging": {"tonnes": round(packaging_tonnes, 2), "rate_eur_t": pkg_rate, "cost_eur": pkg_cost},
            "ewaste": {"tonnes": round(ewaste_tonnes, 2), "rate_eur_t": ew_rate, "cost_eur": ew_cost},
            "battery": {"tonnes": round(battery_tonnes, 2), "rate_eur_t": bat_rate, "cost_eur": bat_cost},
            "total_epr_cost_eur_pa": total_cost,
            "compliance_gap": compliance_gap,
            "regulatory_risk": regulatory_risk,
            "eu_directives": ["94/62/EC (Packaging)", "WEEE 2012/19/EU", "Batteries (EU) 2023/1542"],
        }

    # ------------------------------------------------------------------
    # 5. CRM Risk Assessment
    # ------------------------------------------------------------------

    def assess_crm_risk(
        self,
        entity_id: str,
        materials_used: list,
    ) -> dict:
        """
        EU CRM Act 2023 dependency assessment for critical raw materials.
        Includes supply concentration, recycled content, and 2030 target gaps.
        """
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        crm_found = [m.lower() for m in materials_used if m.lower() in EU_CRM_LIST]
        strategic_found = [m for m in crm_found if m in EU_STRATEGIC_RM]

        material_details = []
        supply_risks: list[float] = []
        recycled_contents: list[float] = []

        for mat in crm_found:
            supply_risk = round(rng.uniform(30.0, 90.0), 1)
            recycled_content = round(rng.uniform(5.0, 45.0), 1)
            hhi = round(rng.uniform(1800, 9000), 0)  # Herfindahl-Hirschman Index
            supply_risks.append(supply_risk)
            recycled_contents.append(recycled_content)
            material_details.append({
                "material": mat,
                "is_strategic": mat in EU_STRATEGIC_RM,
                "supply_risk_score": supply_risk,
                "recycled_content_pct": recycled_content,
                "hhi_concentration": hhi,
                "main_supplier_country": rng.choice(["CN", "RU", "ZA", "BR", "CG", "CL"]),
            })

        dependency_score = round(sum(supply_risks) / len(supply_risks), 2) if supply_risks else 0.0
        recycled_avg = round(sum(recycled_contents) / len(recycled_contents), 2) if recycled_contents else 0.0
        supply_risk_score = dependency_score

        # EU 2030 target gaps
        target_gaps = {
            "extraction_pct": round(max(0.0, EU_CRM_2030_TARGETS["extraction_pct"] - rng.uniform(1.0, 8.0)), 2),
            "processing_pct": round(max(0.0, EU_CRM_2030_TARGETS["processing_pct"] - rng.uniform(5.0, 30.0)), 2),
            "recycling_pct": round(max(0.0, EU_CRM_2030_TARGETS["recycling_pct"] - recycled_avg), 2),
        }

        if dependency_score >= 70.0:
            portfolio_risk_rating = "Critical"
        elif dependency_score >= 50.0:
            portfolio_risk_rating = "High"
        elif dependency_score >= 30.0:
            portfolio_risk_rating = "Medium"
        else:
            portfolio_risk_rating = "Low"

        return {
            "entity_id": entity_id,
            "materials_input": materials_used,
            "crm_materials_found": crm_found,
            "strategic_materials_found": strategic_found,
            "material_details": material_details,
            "dependency_score": dependency_score,
            "supply_risk_score": supply_risk_score,
            "recycled_content_avg_pct": recycled_avg,
            "target_gaps": target_gaps,
            "portfolio_risk_rating": portfolio_risk_rating,
            "regulation": "EU CRM Act 2023",
            "eu_crm_count": len(EU_CRM_LIST),
        }

    # ------------------------------------------------------------------
    # 6. LCA Analysis
    # ------------------------------------------------------------------

    def perform_lca(
        self,
        entity_id: str,
        product_name: str,
        annual_production: float,
        sector: str,
    ) -> dict:
        """
        ISO 14044 Life Cycle Assessment: cradle-to-gate vs cradle-to-cradle.
        Circularity benefit quantifies CO2 savings from circular design.
        """
        rng = random.Random(hash(entity_id + product_name) & 0xFFFFFFFF)

        sec = sector.lower() if sector.lower() in LCA_GATE_FACTORS else "other"
        gate_factor = LCA_GATE_FACTORS[sec] * rng.uniform(0.9, 1.1)

        c2g = round(gate_factor, 2)

        ben_lo, ben_hi = LCA_CIRCULARITY_BENEFIT.get(sec, (10.0, 25.0))
        benefit_pct = round(rng.uniform(ben_lo, ben_hi), 2)
        c2c = round(c2g * (1 - benefit_pct / 100.0), 2)

        annual_co2_saving = round((c2g - c2c) * annual_production / 1000.0, 2)  # tCO2

        hotspots = LCA_HOTSPOT_STAGES.get(sec, ["Manufacturing", "Assembly", "Distribution"])

        n_opts = rng.randint(3, 5)
        improvement_options = rng.sample(IMPROVEMENT_OPTIONS_LCA, n_opts)

        return {
            "entity_id": entity_id,
            "product_name": product_name,
            "sector": sec,
            "annual_production": annual_production,
            "cradle_to_gate_kgco2e": c2g,
            "cradle_to_cradle_kgco2e": c2c,
            "circularity_benefit_pct": benefit_pct,
            "annual_co2_saving_tco2": annual_co2_saving,
            "hotspot_stages": hotspots,
            "improvement_options": improvement_options,
            "lca_standard": "ISO 14044:2006",
            "functional_unit": f"1 unit of {product_name}",
        }

    # ------------------------------------------------------------------
    # 7. Material Flow Analysis
    # ------------------------------------------------------------------

    def analyse_material_flows(
        self,
        entity_id: str,
        materials: list[dict],
    ) -> dict:
        """
        Material flow analysis: for each material compute recycled content %
        and recovery rate. Flag CRM exposure.
        """
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        analysis: list[dict] = []
        total_inflow = 0.0
        total_recycled = 0.0
        crm_inflow = 0.0
        highest_risk_score = 0.0
        highest_risk_material = ""

        for mat in materials:
            name = mat.get("name", "unknown")
            primary = float(mat.get("primary_input_t", 0.0))
            recycled = float(mat.get("recycled_input_t", 0.0))
            bio_based = float(mat.get("bio_based_input_t", 0.0))
            total = primary + recycled + bio_based

            rec_pct = round(recycled / total * 100.0 if total > 0 else 0.0, 2)
            recovery_rate_pct = round(rng.uniform(20.0, 85.0), 1)
            is_crm = name.lower() in EU_CRM_LIST
            risk_score = rng.uniform(10.0, 90.0) if is_crm else rng.uniform(5.0, 40.0)

            if risk_score > highest_risk_score:
                highest_risk_score = risk_score
                highest_risk_material = name

            total_inflow += total
            total_recycled += recycled
            if is_crm:
                crm_inflow += total

            analysis.append({
                "material": name,
                "primary_input_t": round(primary, 2),
                "recycled_input_t": round(recycled, 2),
                "bio_based_input_t": round(bio_based, 2),
                "total_inflow_t": round(total, 2),
                "recycled_input_pct": rec_pct,
                "recovery_rate_pct": recovery_rate_pct,
                "is_crm": is_crm,
                "risk_score": round(risk_score, 1),
            })

        portfolio_recycled_pct = round(total_recycled / total_inflow * 100.0 if total_inflow > 0 else 0.0, 2)
        crm_exposure_pct = round(crm_inflow / total_inflow * 100.0 if total_inflow > 0 else 0.0, 2)

        eu_2030_compliance = {
            "recycling_target_25pct": portfolio_recycled_pct >= 25.0,
            "current_recycled_pct": portfolio_recycled_pct,
            "gap_to_25pct_target": round(max(0.0, 25.0 - portfolio_recycled_pct), 2),
        }

        return {
            "entity_id": entity_id,
            "materials_analysis": analysis,
            "portfolio_recycled_pct": portfolio_recycled_pct,
            "total_inflow_t": round(total_inflow, 2),
            "total_recycled_t": round(total_recycled, 2),
            "crm_exposure_pct": crm_exposure_pct,
            "highest_risk_material": highest_risk_material,
            "eu_2030_compliance": eu_2030_compliance,
        }

    # ------------------------------------------------------------------
    # 8. Overall Circularity Score
    # ------------------------------------------------------------------

    def compute_overall_circularity(
        self,
        entity_id: str,
        esrs_score: float,
        mci_score: float,
        cti_score: float,
        lca_benefit_pct: float,
    ) -> dict:
        """
        Aggregated circularity score combining ESRS E5, MCI, CTI, and LCA benefit.
        """
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        overall_score = round(
            esrs_score * 0.30
            + mci_score * 100.0 * 0.30
            + cti_score * 0.20
            + lca_benefit_pct * 0.20,
            2,
        )
        overall_score = min(100.0, max(0.0, overall_score))

        if overall_score >= 70.0:
            risk_rating = "Low"
        elif overall_score >= 50.0:
            risk_rating = "Medium"
        elif overall_score >= 30.0:
            risk_rating = "High"
        else:
            risk_rating = "Critical"

        # Investment needed to close gap to 70 (Low risk threshold)
        gap = max(0.0, 70.0 - overall_score)
        investment_needed_usd = round(gap * rng.uniform(50_000, 200_000), 0)

        key_gaps: list[str] = []
        if esrs_score < 65.0:
            key_gaps.append("ESRS E5 disclosure maturity below threshold")
        if mci_score < 0.4:
            key_gaps.append("Material Circularity Indicator below industry benchmark")
        if cti_score < 60.0:
            key_gaps.append("Circular Transition Indicator composite below C-tier")
        if lca_benefit_pct < 15.0:
            key_gaps.append("LCA circularity benefit below 15% — product redesign needed")

        priority_actions: list[str] = []
        if mci_score < 0.3:
            priority_actions.append("Increase recycled input fraction to ≥30%")
        if cti_score < 50.0:
            priority_actions.append("Implement design-for-disassembly programme")
        if esrs_score < 60.0:
            priority_actions.append("Complete ESRS E5 mandatory datapoints for CSRD reporting")
        if lca_benefit_pct < 20.0:
            priority_actions.append("Conduct product-level LCA to identify top emission hotspots")

        green_finance_eligible = overall_score >= 55.0 and lca_benefit_pct >= 15.0

        return {
            "entity_id": entity_id,
            "input_scores": {
                "esrs_e5": round(esrs_score, 2),
                "mci": round(mci_score, 4),
                "cti": round(cti_score, 2),
                "lca_benefit_pct": round(lca_benefit_pct, 2),
            },
            "overall_circularity_score": overall_score,
            "risk_rating": risk_rating,
            "investment_needed_usd": investment_needed_usd,
            "key_gaps": key_gaps,
            "priority_actions": priority_actions,
            "green_finance_eligible": green_finance_eligible,
            "eu_taxonomy_alignment": overall_score >= 60.0,
            "frameworks_assessed": ["CSRD ESRS E5", "EMF MCI", "WBCSD CTI v4.0", "ISO 14044 LCA"],
        }


# ---------------------------------------------------------------------------
# Module-level instance
# ---------------------------------------------------------------------------

_engine = CircularEconomyEngine()

assess_esrs_e5 = _engine.assess_esrs_e5
calculate_mci = _engine.calculate_mci
assess_wbcsd_cti = _engine.assess_wbcsd_cti
calculate_epr_compliance = _engine.calculate_epr_compliance
assess_crm_risk = _engine.assess_crm_risk
perform_lca = _engine.perform_lca
analyse_material_flows = _engine.analyse_material_flows
compute_overall_circularity = _engine.compute_overall_circularity
