"""
Aviation Climate Engine
========================
CORSIA Phase 2 · SAF Blending Mandates (ReFuelEU + IRA 45Z) · EU ETS Aviation ·
IATA Net Zero 2050 · Aircraft Asset Stranding

Sub-modules:
  1. CORSIA Obligation      — Phase 1-3 offsetting requirement
  2. SAF Compliance         — ReFuelEU Aviation blending mandate
  3. IRA 45Z SAF Credit     — US SAF tax credit calculation
  4. EU ETS Aviation        — Intra-EEA allowance obligation
  5. IATA NZC Alignment     — Net Zero 2050 pathway scoring
  6. Aircraft Stranding     — Asset stranding under NZ2050
  7. Full Assessment        — Consolidated operator report

References:
  - ICAO CORSIA (Carbon Offsetting and Reduction Scheme for International Aviation)
  - EU ETS Directive 2003/87/EC as amended by EU 2023/958 (aviation chapter)
  - ReFuelEU Aviation Regulation (EU) 2023/2405
  - US IRA Section 40B/45Z SAF Credits (26 USC §40B, §45Z)
  - IATA Net Zero 2050 Roadmap (2021, updated 2023)
  - ICAO Annex 16 Volume IV — CORSIA SARPs
"""
from __future__ import annotations

import math
import uuid
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

# ---------------------------------------------------------------------------
# Reference Data
# ---------------------------------------------------------------------------

CORSIA_PHASES: dict[str, dict] = {
    "phase_1": {
        "years": list(range(2021, 2024)),
        "description": "Voluntary pilot phase",
        "baseline_year": 2019,
        "offset_factor": 0.0,  # voluntary
        "eligible_units": ["VERRA_VCS", "GOLD_STANDARD", "ACR", "CAR", "CDM"],
        "mandatory": False,
    },
    "phase_2": {
        "years": list(range(2024, 2027)),
        "description": "Mandatory for ICAO G20+ states",
        "baseline_year": 2019,
        "offset_factor": 0.85,
        "eligible_units": ["VERRA_VCS", "GOLD_STANDARD", "ACR", "CAR", "REDD+", "ARB", "SOCIALCARBON"],
        "mandatory": True,
    },
    "phase_3": {
        "years": list(range(2027, 2036)),
        "description": "All ICAO member states (excl. exemptions)",
        "baseline_year": 2019,
        "offset_factor": 1.00,
        "eligible_units": ["VERRA_VCS", "GOLD_STANDARD", "ACR", "CAR", "REDD+", "ARB", "SOCIALCARBON", "CDM_CER"],
        "mandatory": True,
    },
}

CORSIA_APPROVED_SCHEMES_P2: list[str] = [
    "VERRA_VCS",
    "GOLD_STANDARD",
    "ACR",
    "CAR",
    "REDD+",
    "ARB",
    "SOCIALCARBON",
    "CDM_CER",
]

# ReFuelEU Aviation SAF blending mandates (% of fuel uplifted, EU 2023/2405)
REFUELEU_SAF_MANDATES: dict[int, float] = {
    2025: 2.0,
    2030: 6.0,
    2035: 20.0,
    2040: 34.0,
    2045: 42.0,
    2050: 70.0,
}

# IRA 45Z SAF credits: lifecycle CI threshold → credit per gallon of gasoline equivalent
IRA_45Z_SAF_CREDITS: dict[str, dict] = {
    "50pct_reduction": {
        "max_lifecycle_ci_gco2eq_mj": 44.58,  # 50% below baseline 89.16
        "credit_usd_per_gge": 1.25,
    },
    "60pct_reduction": {
        "max_lifecycle_ci_gco2eq_mj": 35.66,
        "credit_usd_per_gge": 1.50,
    },
    "80pct_reduction": {
        "max_lifecycle_ci_gco2eq_mj": 17.83,
        "credit_usd_per_gge": 1.75,
    },
    "100pct_reduction": {
        "max_lifecycle_ci_gco2eq_mj": 0.0,
        "credit_usd_per_gge": 1.75,  # cap at $1.75
    },
}

# EU ETS Aviation free allocation phase-out schedule
EU_ETS_AVIATION: dict[int, dict] = {
    2024: {"free_allocation_pct": 85.0, "intra_eea_only": True},
    2025: {"free_allocation_pct": 85.0, "intra_eea_only": True},
    2026: {"free_allocation_pct": 75.0, "intra_eea_only": True},
    2027: {"free_allocation_pct": 50.0, "intra_eea_only": True},
    2028: {"free_allocation_pct": 25.0, "intra_eea_only": True},
    2029: {"free_allocation_pct": 0.0,  "intra_eea_only": True},
    2030: {"free_allocation_pct": 0.0,  "intra_eea_only": True},
}

# IATA Net Zero 2050 pathway breakdown per year
IATA_NZC_PATHWAY: dict[int, dict] = {
    2030: {"efficiency_pct": 3.0,  "saf_pct": 5.0,  "carbon_removal_pct": 0.0,  "offset_pct": 3.0},
    2040: {"efficiency_pct": 6.0,  "saf_pct": 28.0, "carbon_removal_pct": 2.0,  "offset_pct": 4.0},
    2050: {"efficiency_pct": 13.0, "saf_pct": 65.0, "carbon_removal_pct": 10.0, "offset_pct": 19.0},
}

# Aircraft CO2 intensity: gCO2/passenger-km (ICAO 2023)
AIRCRAFT_CO2_INTENSITY: dict[str, float] = {
    "A380":          75.0,
    "B777":          85.0,
    "B787":          65.0,
    "A350":          60.0,
    "B737MAX":       70.0,
    "A320neo":       68.0,
    "regional_jet":  110.0,
    "turboprop":     95.0,
    "B747_classic":  120.0,
    "A330":          90.0,
}

# Aircraft stranding year under NZ2050 scenario
AIRCRAFT_STRANDING_TIMELINE: dict[str, int] = {
    "A380":          2032,
    "B777_classic":  2030,
    "old_B737":      2035,
    "B747_classic":  2028,
    "regional_jet_old": 2033,
    "turboprop_old": 2038,
    "A330":          2034,
    "B767":          2031,
}

# SAF pathway cost premiums above conventional Jet A-1 (USD/tonne)
SAF_COST_PREMIUMS: dict[str, float] = {
    "HEFA":              800.0,   # Hydroprocessed Esters and Fatty Acids
    "PtL":              2500.0,   # Power-to-Liquid (e-fuel)
    "AtJ":              1200.0,   # Alcohol-to-Jet
    "Fischer_Tropsch":  1800.0,   # FT-SPK
    "co_processing":     600.0,   # Co-processing with fossil
    "DSHC":             1500.0,   # Direct Sugar-to-Hydrocarbon
}

# EUA aviation reference price EUR/tonne
EUA_AVIATION_PRICE = 65.0
# CORSIA credit price USD/tonne CO2
CORSIA_CREDIT_PRICE = 8.5

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class CORSIAResult:
    entity_id: str
    icao_designator: str
    phase: str
    baseline_tco2: float
    actual_tco2: float
    growth_tco2: float
    offset_factor: float
    offsetting_obligation_tco2: float
    eligible_units_breakdown: dict
    offset_cost_usd: float
    mandatory: bool

@dataclass
class SAFComplianceResult:
    entity_id: str
    year: int
    jurisdiction: str
    total_fuel_uplift_t: float
    saf_blended_t: float
    blend_pct: float
    mandate_pct: float
    compliance_gap_pct: float
    gap_volume_t: float
    compliant: bool
    penalty_usd: float

@dataclass
class IRA45ZResult:
    entity_id: str
    saf_volume_gge: float
    saf_pathway: str
    lifecycle_ci: float
    eligible: bool
    credit_tier: str
    credit_per_gge: float
    total_credit_usd: float

@dataclass
class EUETSAviationResult:
    entity_id: str
    year: int
    intra_eea_co2_t: float
    free_allocation_pct: float
    obligation_allowances: float
    free_allocation: float
    surrender_gap: float
    cost_eur: float

@dataclass
class IATANZCResult:
    entity_id: str
    year: int
    current_intensity: float
    pathway_target_intensity: float
    alignment_score: float
    efficiency_gap: float
    saf_gap: float
    offset_gap: float
    overall_aligned: bool

@dataclass
class AircraftStrandingResult:
    entity_id: str
    fleet_data: list[dict]
    stranding_events: list[dict]
    total_stranded_value_usd: float
    fleet_avg_age: float
    high_emission_pct: float
    earliest_stranding_year: Optional[int]

# ---------------------------------------------------------------------------
# Engine Class
# ---------------------------------------------------------------------------

class AviationClimateEngine:
    """Pure computation — no DB calls."""

    # ------------------------------------------------------------------
    # 1. CORSIA Obligation
    # ------------------------------------------------------------------
    def calculate_corsia_obligation(
        self,
        entity_id: str,
        icao_designator: str,
        baseline_tco2: float,
        actual_tco2: float,
        phase: str = "phase_2",
        eligible_routes_pct: float = 100.0,
    ) -> CORSIAResult:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)
        phase_data = CORSIA_PHASES.get(phase, CORSIA_PHASES["phase_2"])

        growth_tco2 = max(0.0, actual_tco2 - baseline_tco2)
        eligible_growth = growth_tco2 * eligible_routes_pct / 100.0
        offset_factor = phase_data["offset_factor"]
        offsetting_obligation = eligible_growth * offset_factor

        # Distribute across eligible units
        schemes = phase_data["eligible_units"]
        eligible_units_breakdown = {}
        remaining = offsetting_obligation
        for i, scheme in enumerate(schemes):
            if i == len(schemes) - 1:
                eligible_units_breakdown[scheme] = round(remaining, 2)
            else:
                share = rng.uniform(0.05, 0.25) * offsetting_obligation
                share = min(share, remaining)
                eligible_units_breakdown[scheme] = round(share, 2)
                remaining -= share

        offset_cost_usd = offsetting_obligation * CORSIA_CREDIT_PRICE

        return CORSIAResult(
            entity_id=entity_id,
            icao_designator=icao_designator,
            phase=phase,
            baseline_tco2=round(baseline_tco2, 2),
            actual_tco2=round(actual_tco2, 2),
            growth_tco2=round(growth_tco2, 2),
            offset_factor=offset_factor,
            offsetting_obligation_tco2=round(offsetting_obligation, 2),
            eligible_units_breakdown=eligible_units_breakdown,
            offset_cost_usd=round(offset_cost_usd, 2),
            mandatory=phase_data["mandatory"],
        )

    # ------------------------------------------------------------------
    # 2. SAF Compliance
    # ------------------------------------------------------------------
    def assess_saf_compliance(
        self,
        entity_id: str,
        total_fuel_uplift_t: float,
        saf_blended_t: float,
        year: int = 2025,
        jurisdiction: str = "EU",
    ) -> SAFComplianceResult:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        blend_pct = saf_blended_t / max(total_fuel_uplift_t, 1.0) * 100.0

        # Get applicable mandate
        if jurisdiction.upper() in ("EU", "EEA"):
            mandate_years = sorted(REFUELEU_SAF_MANDATES.keys())
            mandate_pct = REFUELEU_SAF_MANDATES[mandate_years[-1]]
            for my in mandate_years:
                if year <= my:
                    mandate_pct = REFUELEU_SAF_MANDATES[my]
                    break
        else:
            mandate_pct = 0.0  # No universal global mandate yet

        compliance_gap_pct = max(0.0, mandate_pct - blend_pct)
        gap_volume_t = compliance_gap_pct / 100.0 * total_fuel_uplift_t
        compliant = blend_pct >= mandate_pct

        # EU penalty: EUR 50/GJ gap + SAF shortfall surcharge (simplified)
        # Approx 44 MJ/kg for Jet-A, so 1 tonne ≈ 44,000 MJ ≈ 44 GJ
        penalty_per_tonne_gap = 50.0 * 44.0  # EUR/tonne gap
        penalty_usd = gap_volume_t * penalty_per_tonne_gap * 1.10  # EUR to USD ~1.10

        return SAFComplianceResult(
            entity_id=entity_id,
            year=year,
            jurisdiction=jurisdiction,
            total_fuel_uplift_t=round(total_fuel_uplift_t, 2),
            saf_blended_t=round(saf_blended_t, 2),
            blend_pct=round(blend_pct, 3),
            mandate_pct=round(mandate_pct, 1),
            compliance_gap_pct=round(compliance_gap_pct, 3),
            gap_volume_t=round(gap_volume_t, 2),
            compliant=compliant,
            penalty_usd=round(penalty_usd, 2),
        )

    # ------------------------------------------------------------------
    # 3. IRA 45Z SAF Credit
    # ------------------------------------------------------------------
    def calculate_ira_45z(
        self,
        entity_id: str,
        saf_volume_gge: float,
        saf_pathway: str,
        lifecycle_ci: float,
    ) -> IRA45ZResult:
        # GGE baseline CI for aviation fuel ≈ 89.16 gCO2eq/MJ
        baseline_ci = 89.16
        reduction_pct = max(0.0, (baseline_ci - lifecycle_ci) / baseline_ci * 100.0)

        eligible = reduction_pct >= 50.0

        credit_tier = "none"
        credit_per_gge = 0.0
        if reduction_pct >= 100.0:
            credit_tier = "100pct_reduction"
            credit_per_gge = 1.75
        elif reduction_pct >= 80.0:
            credit_tier = "80pct_reduction"
            credit_per_gge = 1.75
        elif reduction_pct >= 60.0:
            credit_tier = "60pct_reduction"
            credit_per_gge = 1.50
        elif reduction_pct >= 50.0:
            credit_tier = "50pct_reduction"
            credit_per_gge = 1.25

        total_credit_usd = saf_volume_gge * credit_per_gge if eligible else 0.0

        return IRA45ZResult(
            entity_id=entity_id,
            saf_volume_gge=round(saf_volume_gge, 2),
            saf_pathway=saf_pathway,
            lifecycle_ci=round(lifecycle_ci, 3),
            eligible=eligible,
            credit_tier=credit_tier,
            credit_per_gge=credit_per_gge,
            total_credit_usd=round(total_credit_usd, 2),
        )

    # ------------------------------------------------------------------
    # 4. EU ETS Aviation
    # ------------------------------------------------------------------
    def assess_eu_ets_aviation(
        self,
        entity_id: str,
        intra_eea_co2_t: float,
        year: int = 2025,
    ) -> EUETSAviationResult:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        year_data = EU_ETS_AVIATION.get(year, EU_ETS_AVIATION.get(max(EU_ETS_AVIATION.keys())))
        free_alloc_pct = year_data["free_allocation_pct"]

        obligation_allowances = intra_eea_co2_t
        free_allocation = intra_eea_co2_t * free_alloc_pct / 100.0
        surrender_gap = max(0.0, obligation_allowances - free_allocation)

        eua_price = rng.uniform(55.0, 80.0)
        cost_eur = surrender_gap * eua_price

        return EUETSAviationResult(
            entity_id=entity_id,
            year=year,
            intra_eea_co2_t=round(intra_eea_co2_t, 2),
            free_allocation_pct=free_alloc_pct,
            obligation_allowances=round(obligation_allowances, 2),
            free_allocation=round(free_allocation, 2),
            surrender_gap=round(surrender_gap, 2),
            cost_eur=round(cost_eur, 2),
        )

    # ------------------------------------------------------------------
    # 5. IATA NZC Alignment
    # ------------------------------------------------------------------
    def assess_iata_nzc(
        self,
        entity_id: str,
        current_intensity: float,
        fleet_mix: dict,
        saf_pct: float,
        year: int = 2030,
    ) -> IATANZCResult:
        # Find nearest pathway year
        path_years = sorted(IATA_NZC_PATHWAY.keys())
        pathway = IATA_NZC_PATHWAY[path_years[-1]]
        for py in path_years:
            if year <= py:
                pathway = IATA_NZC_PATHWAY[py]
                break

        # Baseline 2019 intensity ≈ 95 gCO2/pkm
        baseline_2019 = 95.0
        total_reduction_needed_pct = pathway["efficiency_pct"] + pathway["saf_pct"] + pathway["carbon_removal_pct"] + pathway["offset_pct"]
        pathway_target_intensity = baseline_2019 * (1.0 - total_reduction_needed_pct / 100.0)
        pathway_target_intensity = max(pathway_target_intensity, 1.0)

        delta = current_intensity - pathway_target_intensity
        alignment_score = max(0.0, min(100.0, (1.0 - delta / max(baseline_2019, 1.0)) * 100.0))

        # SAF gap
        saf_gap = max(0.0, pathway["saf_pct"] - saf_pct)

        # Efficiency gap: compare current intensity to efficiency-only target
        efficiency_target = baseline_2019 * (1.0 - pathway["efficiency_pct"] / 100.0)
        efficiency_gap = max(0.0, current_intensity - efficiency_target)

        # Offset gap (residual)
        offset_gap = max(0.0, delta - efficiency_gap - saf_gap * 0.5)

        return IATANZCResult(
            entity_id=entity_id,
            year=year,
            current_intensity=round(current_intensity, 3),
            pathway_target_intensity=round(pathway_target_intensity, 3),
            alignment_score=round(alignment_score, 2),
            efficiency_gap=round(efficiency_gap, 3),
            saf_gap=round(saf_gap, 1),
            offset_gap=round(offset_gap, 3),
            overall_aligned=alignment_score >= 75.0,
        )

    # ------------------------------------------------------------------
    # 6. Aircraft Asset Stranding
    # ------------------------------------------------------------------
    def model_aircraft_stranding(
        self,
        entity_id: str,
        fleet_data: list[dict],
    ) -> AircraftStrandingResult:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        stranding_events = []
        total_stranded_value = 0.0
        ages = []
        high_emission_count = 0
        earliest_stranding: Optional[int] = None

        for aircraft in fleet_data:
            atype = aircraft.get("aircraft_type", "B737MAX")
            build_year = aircraft.get("build_year", 2010)
            asset_value_usd = aircraft.get("asset_value_usd", 50_000_000.0)
            n_aircraft = aircraft.get("count", 1)

            age = 2025 - build_year
            ages.append(age)

            stranding_year = AIRCRAFT_STRANDING_TIMELINE.get(atype)
            intensity = AIRCRAFT_CO2_INTENSITY.get(atype, 80.0)

            if intensity > 95.0:
                high_emission_count += n_aircraft

            if stranding_year:
                years_to_stranding = max(0, stranding_year - 2025)
                # Residual value at stranding (straight-line depreciation, 25yr life)
                remaining_life_yrs = max(0, 25 - age)
                residual_value = asset_value_usd * (remaining_life_yrs - years_to_stranding) / max(25.0, 1.0) * n_aircraft
                stranded_value = max(0.0, residual_value)
                total_stranded_value += stranded_value

                if earliest_stranding is None or stranding_year < earliest_stranding:
                    earliest_stranding = stranding_year

                stranding_events.append({
                    "aircraft_type": atype,
                    "count": n_aircraft,
                    "build_year": build_year,
                    "asset_value_usd_per_unit": asset_value_usd,
                    "co2_intensity_gco2_pkm": intensity,
                    "stranding_year": stranding_year,
                    "years_to_stranding": years_to_stranding,
                    "stranded_value_usd": round(stranded_value, 0),
                })

        total_aircraft = sum(a.get("count", 1) for a in fleet_data)
        avg_age = sum(ages) / len(ages) if ages else 0.0
        high_emission_pct = high_emission_count / max(total_aircraft, 1) * 100.0

        return AircraftStrandingResult(
            entity_id=entity_id,
            fleet_data=fleet_data,
            stranding_events=stranding_events,
            total_stranded_value_usd=round(total_stranded_value, 0),
            fleet_avg_age=round(avg_age, 1),
            high_emission_pct=round(high_emission_pct, 1),
            earliest_stranding_year=earliest_stranding,
        )

    # ------------------------------------------------------------------
    # 7. Full Assessment
    # ------------------------------------------------------------------
    def generate_full_assessment(
        self,
        entity_id: str,
        operator_data: dict,
    ) -> dict:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        icao = operator_data.get("icao_designator", "XXX")
        baseline_tco2 = operator_data.get("baseline_tco2", 500_000.0)
        actual_tco2 = operator_data.get("actual_tco2", 550_000.0)
        total_fuel_t = operator_data.get("total_fuel_uplift_t", 200_000.0)
        saf_t = operator_data.get("saf_blended_t", 4_000.0)
        intra_eea_co2 = operator_data.get("intra_eea_co2_t", 120_000.0)
        current_intensity = operator_data.get("current_intensity_gco2_pkm", 78.0)
        fleet_mix = operator_data.get("fleet_mix", {})
        fleet_data = operator_data.get("fleet_data", [])
        saf_pct = saf_t / max(total_fuel_t, 1.0) * 100.0
        year = operator_data.get("year", 2025)

        corsia = self.calculate_corsia_obligation(entity_id, icao, baseline_tco2, actual_tco2, "phase_2", 100.0)
        saf_comp = self.assess_saf_compliance(entity_id, total_fuel_t, saf_t, year, "EU")
        eu_ets = self.assess_eu_ets_aviation(entity_id, intra_eea_co2, year)
        iata = self.assess_iata_nzc(entity_id, current_intensity, fleet_mix, saf_pct, 2030)
        stranding = self.model_aircraft_stranding(entity_id, fleet_data)

        # Example SAF credit calc
        saf_gge = saf_t * 1000.0 / 2.84  # approx kg → gge
        saf_pathway = operator_data.get("saf_pathway", "HEFA")
        lifecycle_ci = rng.uniform(20.0, 45.0)
        ira45z = self.calculate_ira_45z(entity_id, saf_gge, saf_pathway, lifecycle_ci)

        total_cost_exposure = (
            corsia.offset_cost_usd
            + saf_comp.penalty_usd
            + eu_ets.cost_eur * 1.10
        )

        return {
            "assessment_id": str(uuid.uuid4()),
            "entity_id": entity_id,
            "icao_designator": icao,
            "year": year,
            "corsia": {
                "phase": corsia.phase,
                "offsetting_obligation_tco2": corsia.offsetting_obligation_tco2,
                "offset_cost_usd": corsia.offset_cost_usd,
                "mandatory": corsia.mandatory,
            },
            "saf_compliance": {
                "blend_pct": saf_comp.blend_pct,
                "mandate_pct": saf_comp.mandate_pct,
                "compliant": saf_comp.compliant,
                "penalty_usd": saf_comp.penalty_usd,
            },
            "ira_45z": {
                "eligible": ira45z.eligible,
                "credit_per_gge": ira45z.credit_per_gge,
                "total_credit_usd": ira45z.total_credit_usd,
            },
            "eu_ets": {
                "obligation_allowances": eu_ets.obligation_allowances,
                "surrender_gap": eu_ets.surrender_gap,
                "cost_eur": eu_ets.cost_eur,
                "free_allocation_pct": eu_ets.free_allocation_pct,
            },
            "iata_nzc": {
                "alignment_score": iata.alignment_score,
                "saf_gap": iata.saf_gap,
                "efficiency_gap": iata.efficiency_gap,
                "overall_aligned": iata.overall_aligned,
            },
            "aircraft_stranding": {
                "total_stranded_value_usd": stranding.total_stranded_value_usd,
                "fleet_avg_age": stranding.fleet_avg_age,
                "high_emission_pct": stranding.high_emission_pct,
                "earliest_stranding_year": stranding.earliest_stranding_year,
                "stranding_events_count": len(stranding.stranding_events),
            },
            "total_cost_exposure_usd": round(total_cost_exposure, 2),
            "overall_compliance_score": round(
                (100.0 if corsia.offsetting_obligation_tco2 == 0 else 60.0) * 0.25
                + (100.0 if saf_comp.compliant else 40.0) * 0.25
                + iata.alignment_score * 0.25
                + (100.0 if eu_ets.surrender_gap == 0 else 50.0) * 0.25,
                2,
            ),
            "generated_at": datetime.utcnow().isoformat() + "Z",
        }
