"""
Entity 360 Engine
===================
Provides a unified, cross-module view of any entity (counterparty, investee,
issuer, borrower). Aggregates outputs from all platform modules into a single
composite profile with risk scores, ESG metrics, regulatory status, and
data quality assessment.

References:
- CSRD double-materiality entity scope
- PCAF attribution methodology — counterparty-level
- EBA ITS on Pillar 3 — counterparty credit risk
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Reference Data — Module Registry
# ---------------------------------------------------------------------------

MODULE_REGISTRY: dict[str, dict] = {
    "carbon_calculator": {
        "label": "Carbon Calculator",
        "outputs": ["scope1_tco2e", "scope2_tco2e", "scope3_tco2e", "total_tco2e", "intensity_revenue"],
        "category": "emissions",
    },
    "climate_risk": {
        "label": "Climate Risk Engine",
        "outputs": ["transition_risk_eur", "physical_risk_eur", "combined_risk_score", "scenario_alignment"],
        "category": "risk",
    },
    "ecl_calculator": {
        "label": "ECL Calculator",
        "outputs": ["pd_1yr", "lgd_pct", "ead_eur", "ecl_eur", "ecl_stage", "climate_overlay_eur"],
        "category": "credit",
    },
    "pcaf_calculator": {
        "label": "PCAF Calculator",
        "outputs": ["financed_tco2e", "attribution_factor", "data_quality_score", "asset_class"],
        "category": "financed_emissions",
    },
    "nature_risk": {
        "label": "Nature Risk Engine",
        "outputs": ["nature_risk_score", "water_risk_score", "biodiversity_score", "tnfd_leap_priority"],
        "category": "nature",
    },
    "taxonomy_alignment": {
        "label": "EU Taxonomy Alignment",
        "outputs": ["taxonomy_eligible_pct", "taxonomy_aligned_pct", "dnsh_pass", "minimum_safeguards"],
        "category": "regulatory",
    },
    "scenario_analysis": {
        "label": "Scenario Analysis",
        "outputs": ["nze_alignment_score", "transition_pathway", "stranded_asset_risk", "carbon_price_impact"],
        "category": "scenarios",
    },
    "sfdr_pai": {
        "label": "SFDR PAI Calculator",
        "outputs": ["pai_1_ghg", "pai_2_footprint", "pai_3_intensity", "pai_4_fossil", "pai_count_flagged"],
        "category": "regulatory",
    },
    "real_estate": {
        "label": "Real Estate Valuation",
        "outputs": ["market_value", "green_premium_pct", "crrem_stranding_year", "epc_rating"],
        "category": "valuation",
    },
    "supply_chain": {
        "label": "Supply Chain / Scope 3",
        "outputs": ["scope3_cat_breakdown", "supplier_risk_score", "sbti_target_status"],
        "category": "supply_chain",
    },
}

# Entity types
ENTITY_TYPES: list[dict] = [
    {"id": "corporate", "label": "Corporate / Issuer"},
    {"id": "fi", "label": "Financial Institution"},
    {"id": "sovereign", "label": "Sovereign / Government"},
    {"id": "project", "label": "Project / SPV"},
    {"id": "real_estate", "label": "Real Estate Asset"},
    {"id": "fund", "label": "Fund / Collective Investment"},
    {"id": "sme", "label": "SME / Unlisted Company"},
]

# Sector classification
SECTOR_MAP: dict[str, str] = {
    "energy": "Energy (Oil & Gas / Utilities)",
    "financials": "Financial Institutions",
    "industrials": "Industrials & Manufacturing",
    "technology": "Technology",
    "healthcare": "Healthcare",
    "consumer": "Consumer Goods & Services",
    "real_estate": "Real Estate",
    "materials": "Basic Materials & Mining",
    "transport": "Transportation",
    "agriculture": "Agriculture & Food",
    "utilities": "Utilities (non-energy)",
    "telecom": "Telecommunications",
}


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class ModuleScore:
    """Score from a single platform module."""
    module_id: str
    module_label: str
    category: str
    data_available: bool
    values: dict[str, float]  # output_name: value
    data_quality: str  # "high" | "medium" | "low" | "none"
    last_updated: str  # ISO date


@dataclass
class RiskProfile:
    """Aggregated risk profile."""
    credit_risk_score: Optional[float]  # 0-100
    climate_risk_score: Optional[float]
    nature_risk_score: Optional[float]
    regulatory_risk_score: Optional[float]
    composite_risk_score: float  # Weighted average
    risk_band: str  # "low" | "medium" | "high" | "very_high"


@dataclass
class ESGProfile:
    """ESG metrics summary."""
    total_ghg_tco2e: Optional[float]
    ghg_intensity: Optional[float]
    renewable_share_pct: Optional[float]
    taxonomy_aligned_pct: Optional[float]
    pai_flags: int
    esg_rating: str  # "A" | "B" | "C" | "D" | "NR"


@dataclass
class Entity360Result:
    """Complete 360 view of an entity."""
    entity_name: str
    entity_id: str
    entity_type: str
    sector: str
    sector_label: str
    reporting_year: int
    modules_available: int
    modules_total: int
    data_completeness_pct: float
    module_scores: list[ModuleScore]
    risk_profile: RiskProfile
    esg_profile: ESGProfile
    regulatory_status: dict[str, str]  # {framework: status}
    data_gaps: list[str]
    recommendations: list[str]


# ---------------------------------------------------------------------------
# Counterparty Master
# ---------------------------------------------------------------------------

@dataclass
class CounterpartyRecord:
    """Master counterparty record with dedup and enrichment."""
    entity_id: str
    entity_name: str
    lei: str
    entity_type: str
    sector: str
    country: str
    parent_entity_id: Optional[str]
    group_name: Optional[str]
    exposure_eur: float
    modules_linked: list[str]
    last_assessment_date: str
    data_quality_score: float  # 0-100


@dataclass
class CounterpartyMasterResult:
    """Counterparty master output."""
    total_counterparties: int
    counterparties: list[CounterpartyRecord]
    duplicate_groups: list[dict]  # [{canonical_id, duplicates: [ids]}]
    sector_distribution: dict[str, int]
    entity_type_distribution: dict[str, int]
    data_quality_avg: float
    low_quality_count: int


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class Entity360Engine:
    """Unified entity profile engine."""

    def build_profile(
        self,
        entity_name: str,
        entity_id: str,
        entity_type: str = "corporate",
        sector: str = "financials",
        reporting_year: int = 2024,
        module_data: dict[str, dict[str, float]] = None,
    ) -> Entity360Result:
        """Build a 360 profile from module outputs."""
        module_data = module_data or {}

        module_scores = []
        modules_available = 0
        data_gaps = []

        for mod_id, mod_info in MODULE_REGISTRY.items():
            values = module_data.get(mod_id, {})
            has_data = len(values) > 0

            if has_data:
                modules_available += 1
                # Quality based on output coverage
                expected = len(mod_info["outputs"])
                provided = len(values)
                if provided >= expected * 0.8:
                    quality = "high"
                elif provided >= expected * 0.5:
                    quality = "medium"
                else:
                    quality = "low"
            else:
                quality = "none"
                data_gaps.append(f"{mod_info['label']}: No data available")

            module_scores.append(ModuleScore(
                module_id=mod_id,
                module_label=mod_info["label"],
                category=mod_info["category"],
                data_available=has_data,
                values=values,
                data_quality=quality,
                last_updated=f"{reporting_year}-12-31",
            ))

        total_modules = len(MODULE_REGISTRY)
        completeness = (modules_available / total_modules * 100) if total_modules > 0 else 0

        # Build risk profile
        risk_profile = self._build_risk_profile(module_data)

        # Build ESG profile
        esg_profile = self._build_esg_profile(module_data)

        # Regulatory status
        reg_status = self._assess_regulatory(module_data)

        # Recommendations
        recs = self._generate_recommendations(module_data, data_gaps, risk_profile)

        return Entity360Result(
            entity_name=entity_name,
            entity_id=entity_id,
            entity_type=entity_type,
            sector=sector,
            sector_label=SECTOR_MAP.get(sector, sector),
            reporting_year=reporting_year,
            modules_available=modules_available,
            modules_total=total_modules,
            data_completeness_pct=round(completeness, 1),
            module_scores=module_scores,
            risk_profile=risk_profile,
            esg_profile=esg_profile,
            regulatory_status=reg_status,
            data_gaps=data_gaps,
            recommendations=recs,
        )

    def _build_risk_profile(self, module_data: dict) -> RiskProfile:
        """Aggregate risk scores across modules."""
        credit = module_data.get("ecl_calculator", {})
        climate = module_data.get("climate_risk", {})
        nature = module_data.get("nature_risk", {})
        taxonomy = module_data.get("taxonomy_alignment", {})

        credit_score = credit.get("pd_1yr", None)
        if credit_score is not None:
            credit_score = min(credit_score * 1000, 100)  # PD to 0-100 scale

        climate_score = climate.get("combined_risk_score", None)
        nature_score = nature.get("nature_risk_score", None)

        # Regulatory risk from taxonomy misalignment
        tax_aligned = taxonomy.get("taxonomy_aligned_pct", None)
        reg_risk = (100 - tax_aligned) if tax_aligned is not None else None

        # Composite (weighted average of available scores)
        scores = []
        weights = []
        if credit_score is not None:
            scores.append(credit_score); weights.append(0.3)
        if climate_score is not None:
            scores.append(climate_score); weights.append(0.3)
        if nature_score is not None:
            scores.append(nature_score); weights.append(0.2)
        if reg_risk is not None:
            scores.append(reg_risk); weights.append(0.2)

        if scores:
            total_w = sum(weights)
            composite = sum(s * w for s, w in zip(scores, weights)) / total_w
        else:
            composite = 50  # Default moderate risk

        if composite <= 25:
            band = "low"
        elif composite <= 50:
            band = "medium"
        elif composite <= 75:
            band = "high"
        else:
            band = "very_high"

        return RiskProfile(
            credit_risk_score=round(credit_score, 1) if credit_score is not None else None,
            climate_risk_score=round(climate_score, 1) if climate_score is not None else None,
            nature_risk_score=round(nature_score, 1) if nature_score is not None else None,
            regulatory_risk_score=round(reg_risk, 1) if reg_risk is not None else None,
            composite_risk_score=round(composite, 1),
            risk_band=band,
        )

    def _build_esg_profile(self, module_data: dict) -> ESGProfile:
        """Build ESG summary from module outputs."""
        carbon = module_data.get("carbon_calculator", {})
        taxonomy = module_data.get("taxonomy_alignment", {})
        sfdr = module_data.get("sfdr_pai", {})

        total_ghg = carbon.get("total_tco2e")
        intensity = carbon.get("intensity_revenue")
        renew = carbon.get("renewable_share_pct", module_data.get("scenario_analysis", {}).get("renewable_share_pct"))
        tax_pct = taxonomy.get("taxonomy_aligned_pct")
        pai_flags = int(sfdr.get("pai_count_flagged", 0))

        # Simple ESG rating based on available data
        score = 50  # Baseline
        if total_ghg is not None and total_ghg < 100000:
            score += 10
        if intensity is not None and intensity < 100:
            score += 10
        if tax_pct is not None and tax_pct > 20:
            score += 10
        if pai_flags <= 2:
            score += 10

        if score >= 80:
            rating = "A"
        elif score >= 60:
            rating = "B"
        elif score >= 40:
            rating = "C"
        elif score >= 20:
            rating = "D"
        else:
            rating = "NR"

        return ESGProfile(
            total_ghg_tco2e=total_ghg,
            ghg_intensity=intensity,
            renewable_share_pct=renew,
            taxonomy_aligned_pct=tax_pct,
            pai_flags=pai_flags,
            esg_rating=rating,
        )

    def _assess_regulatory(self, module_data: dict) -> dict[str, str]:
        """Assess regulatory framework status."""
        status = {}

        if "taxonomy_alignment" in module_data:
            pct = module_data["taxonomy_alignment"].get("taxonomy_aligned_pct", 0)
            status["EU_Taxonomy"] = "aligned" if pct >= 20 else "partially_aligned" if pct > 0 else "not_assessed"
        else:
            status["EU_Taxonomy"] = "not_assessed"

        if "sfdr_pai" in module_data:
            flags = module_data["sfdr_pai"].get("pai_count_flagged", 0)
            status["SFDR_PAI"] = "compliant" if flags <= 3 else "review_needed"
        else:
            status["SFDR_PAI"] = "not_assessed"

        if "carbon_calculator" in module_data:
            status["CSRD_E1"] = "data_available"
        else:
            status["CSRD_E1"] = "not_assessed"

        if "climate_risk" in module_data:
            status["TCFD"] = "data_available"
        else:
            status["TCFD"] = "not_assessed"

        return status

    def _generate_recommendations(
        self, module_data: dict, gaps: list[str], risk: RiskProfile,
    ) -> list[str]:
        """Generate actionable recommendations."""
        recs = []
        if risk.risk_band in ("high", "very_high"):
            recs.append("High composite risk — initiate enhanced due diligence review")
        if "carbon_calculator" not in module_data:
            recs.append("Run Carbon Calculator to establish Scope 1/2/3 baseline")
        if "ecl_calculator" not in module_data:
            recs.append("Run ECL Calculator for credit risk quantification")
        if "taxonomy_alignment" not in module_data:
            recs.append("Assess EU Taxonomy alignment for regulatory reporting")
        if "nature_risk" not in module_data:
            recs.append("Assess nature-related risks (TNFD LEAP framework)")
        if len(gaps) > 5:
            recs.append(f"Data completeness low ({len(gaps)} module gaps) — prioritize data collection")
        return recs[:6]

    # Counterparty Master
    def build_counterparty_master(
        self,
        counterparties: list[dict],
    ) -> CounterpartyMasterResult:
        """Build a counterparty master from input records."""
        records = []
        name_groups: dict[str, list] = {}

        for cp in counterparties:
            eid = cp.get("entity_id", "")
            name = cp.get("entity_name", "")
            lei = cp.get("lei", "")
            etype = cp.get("entity_type", "corporate")
            sector = cp.get("sector", "")
            country = cp.get("country", "")
            parent = cp.get("parent_entity_id")
            group = cp.get("group_name")
            exposure = cp.get("exposure_eur", 0)
            modules = cp.get("modules_linked", [])
            last_date = cp.get("last_assessment_date", "2024-01-01")

            # Data quality score
            quality = 0
            if lei:
                quality += 30
            if sector:
                quality += 20
            if len(modules) >= 3:
                quality += 30
            elif len(modules) >= 1:
                quality += 15
            if country:
                quality += 10
            if parent or group:
                quality += 10

            records.append(CounterpartyRecord(
                entity_id=eid,
                entity_name=name,
                lei=lei,
                entity_type=etype,
                sector=sector,
                country=country,
                parent_entity_id=parent,
                group_name=group,
                exposure_eur=exposure,
                modules_linked=modules,
                last_assessment_date=last_date,
                data_quality_score=min(quality, 100),
            ))

            # Dedup by normalised name
            norm = name.strip().lower().replace(" ", "")
            if norm:
                name_groups.setdefault(norm, []).append(eid)

        # Identify duplicates
        dups = []
        for norm, ids in name_groups.items():
            if len(ids) > 1:
                dups.append({"canonical_id": ids[0], "duplicates": ids[1:]})

        # Distributions
        sector_dist: dict[str, int] = {}
        type_dist: dict[str, int] = {}
        for r in records:
            sector_dist[r.sector] = sector_dist.get(r.sector, 0) + 1
            type_dist[r.entity_type] = type_dist.get(r.entity_type, 0) + 1

        avg_quality = sum(r.data_quality_score for r in records) / len(records) if records else 0
        low_q = sum(1 for r in records if r.data_quality_score < 50)

        return CounterpartyMasterResult(
            total_counterparties=len(records),
            counterparties=records,
            duplicate_groups=dups,
            sector_distribution=sector_dist,
            entity_type_distribution=type_dist,
            data_quality_avg=round(avg_quality, 1),
            low_quality_count=low_q,
        )

    def get_module_registry(self) -> dict[str, dict]:
        return MODULE_REGISTRY

    def get_entity_types(self) -> list[dict]:
        return ENTITY_TYPES

    def get_sectors(self) -> dict[str, str]:
        return SECTOR_MAP
