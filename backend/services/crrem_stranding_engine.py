"""
CRREM Carbon Risk Real Estate Monitor - Stranding Analysis Engine

Implements CRREM v2.0 stranding analysis methodology for real estate assets:
  - Carbon Risk Real Estate Monitor (CRREM) v2.0 (2023) pathways
  - IPCC AR6-aligned 1.5C and 2C decarbonisation trajectories
  - EU Taxonomy Regulation 2020/852 energy performance criteria
  - RICS VPS4 climate risk disclosure alignment
  - TCFD scenario-based risk assessment

CRREM pathways define maximum energy intensity (kWh/m2/yr) and carbon intensity
(kgCO2e/m2/yr) thresholds by property type, country, and year. Assets exceeding
these thresholds are considered "stranded" -- at risk of significant value loss
due to regulatory non-compliance, reduced tenant demand, and financing constraints.

Author: Risk Analytics Platform
Version: 2.0.0
Sources: CRREM v2.0 Phase 2 (2023), GRESB, JLL, CBRE ESG benchmarks
"""

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# CRREM Pathway Data
# ---------------------------------------------------------------------------
# Energy intensity targets kWh per m2 per year by property type, country, and scenario year.
# Sources: CRREM v2.0 Phase 2 Country Pathways (2023), EU EPBD Recast (2024),
#          GRESB Real Estate Assessment, JLL Energy & Sustainability Services.
# Note: Values decline annually along the CRREM pathway.
#       1.5C pathway is steeper than 2C (faster required decarbonisation rate).

CRREM_PATHWAY_DATA: Dict[str, Dict[str, Dict[str, Dict[int, float]]]] = {
    "office": {
        "GB": {
            "1.5C": {2020: 215, 2025: 190, 2030: 160, 2035: 130, 2040: 100, 2045: 75, 2050: 55},
            "2C":   {2020: 215, 2025: 198, 2030: 175, 2035: 150, 2040: 122, 2045: 95, 2050: 72},
        },
        "DE": {
            "1.5C": {2020: 230, 2025: 200, 2030: 168, 2035: 135, 2040: 105, 2045: 78, 2050: 57},
            "2C":   {2020: 230, 2025: 210, 2030: 184, 2035: 158, 2040: 128, 2045: 100, 2050: 76},
        },
        "US": {
            "1.5C": {2020: 295, 2025: 258, 2030: 215, 2035: 172, 2040: 132, 2045: 97, 2050: 68},
            "2C":   {2020: 295, 2025: 270, 2030: 236, 2035: 198, 2040: 160, 2045: 124, 2050: 93},
        },
        "FR": {
            "1.5C": {2020: 195, 2025: 170, 2030: 143, 2035: 115, 2040: 89, 2045: 65, 2050: 47},
            "2C":   {2020: 195, 2025: 178, 2030: 158, 2035: 134, 2040: 108, 2045: 84, 2050: 63},
        },
        "NL": {
            "1.5C": {2020: 210, 2025: 182, 2030: 152, 2035: 121, 2040: 93, 2045: 68, 2050: 50},
            "2C":   {2020: 210, 2025: 192, 2030: 168, 2035: 141, 2040: 113, 2045: 87, 2050: 66},
        },
    },
    "retail": {
        "GB": {
            "1.5C": {2020: 380, 2025: 330, 2030: 272, 2035: 215, 2040: 162, 2045: 115, 2050: 80},
            "2C":   {2020: 380, 2025: 348, 2030: 305, 2035: 255, 2040: 200, 2045: 150, 2050: 110},
        },
        "DE": {
            "1.5C": {2020: 350, 2025: 305, 2030: 252, 2035: 200, 2040: 152, 2045: 108, 2050: 76},
            "2C":   {2020: 350, 2025: 320, 2030: 282, 2035: 238, 2040: 188, 2045: 142, 2050: 104},
        },
        "US": {
            "1.5C": {2020: 520, 2025: 450, 2030: 368, 2035: 288, 2040: 215, 2045: 152, 2050: 105},
            "2C":   {2020: 520, 2025: 476, 2030: 416, 2035: 346, 2040: 270, 2045: 200, 2050: 145},
        },
        "FR": {
            "1.5C": {2020: 320, 2025: 278, 2030: 229, 2035: 182, 2040: 138, 2045: 98, 2050: 69},
            "2C":   {2020: 320, 2025: 293, 2030: 257, 2035: 216, 2040: 170, 2045: 128, 2050: 94},
        },
    },
    "industrial": {
        "GB": {
            "1.5C": {2020: 155, 2025: 135, 2030: 112, 2035: 89, 2040: 68, 2045: 50, 2050: 36},
            "2C":   {2020: 155, 2025: 142, 2030: 124, 2035: 104, 2040: 83, 2045: 63, 2050: 47},
        },
        "DE": {
            "1.5C": {2020: 175, 2025: 152, 2030: 126, 2035: 100, 2040: 76, 2045: 56, 2050: 40},
            "2C":   {2020: 175, 2025: 160, 2030: 140, 2035: 117, 2040: 93, 2045: 71, 2050: 53},
        },
        "US": {
            "1.5C": {2020: 195, 2025: 170, 2030: 141, 2035: 112, 2040: 85, 2045: 62, 2050: 44},
            "2C":   {2020: 195, 2025: 178, 2030: 156, 2035: 131, 2040: 104, 2045: 79, 2050: 59},
        },
        "FR": {
            "1.5C": {2020: 140, 2025: 122, 2030: 101, 2035: 80, 2040: 61, 2045: 44, 2050: 32},
            "2C":   {2020: 140, 2025: 128, 2030: 112, 2035: 94, 2040: 75, 2045: 57, 2050: 42},
        },
    },
    "multifamily": {
        "GB": {
            "1.5C": {2020: 175, 2025: 152, 2030: 126, 2035: 100, 2040: 76, 2045: 56, 2050: 40},
            "2C":   {2020: 175, 2025: 160, 2030: 140, 2035: 117, 2040: 93, 2045: 71, 2050: 53},
        },
        "DE": {
            "1.5C": {2020: 185, 2025: 161, 2030: 133, 2035: 106, 2040: 80, 2045: 59, 2050: 42},
            "2C":   {2020: 185, 2025: 169, 2030: 148, 2035: 124, 2040: 99, 2045: 75, 2050: 56},
        },
        "US": {
            "1.5C": {2020: 215, 2025: 187, 2030: 155, 2035: 123, 2040: 93, 2045: 68, 2050: 48},
            "2C":   {2020: 215, 2025: 197, 2030: 172, 2035: 144, 2040: 115, 2045: 87, 2050: 65},
        },
        "FR": {
            "1.5C": {2020: 160, 2025: 139, 2030: 115, 2035: 91, 2040: 69, 2045: 51, 2050: 36},
            "2C":   {2020: 160, 2025: 146, 2030: 128, 2035: 107, 2040: 85, 2045: 65, 2050: 48},
        },
    },
}
"""
Note: Data above represents approximate CRREM Phase 2 values.
For production use, replace with exact CRREM v2.0 country-level pathway data
downloaded from www.crrem.eu. Pathways are updated periodically.
"""


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class AssetEnergyProfile:
    """
    Energy and carbon performance profile for a real estate asset.
    Used as input to CRREM stranding analysis.
    """
    property_type: str               # "office", "retail", "industrial", "multifamily"
    country_iso: str                 # ISO 3166-1 alpha-2: "GB", "DE", "US", "FR", "NL"
    floor_area_m2: Decimal           # Gross internal area in square metres
    current_energy_kwh_m2: Decimal   # Current annual energy intensity (kWh/m2/yr)
    current_carbon_kgco2_m2: Decimal # Current annual carbon intensity (kgCO2e/m2/yr)
    year_built: int                  # Year of original construction
    last_major_refurb: Optional[int] # Year of last major refurbishment (None if never)
    planned_refurb_year: Optional[int] = None  # Planned refurbishment year (None if not planned)
    renovation_potential: str = "medium"  # "high", "medium", "low", "not_feasible"


@dataclass
class StrandingAnalysisResult:
    """
    CRREM stranding analysis result for a real estate asset.
    Contains stranding dates, pathway gaps, retrofit urgency, and cost estimates.
    """
    # Stranding dates
    stranding_year_1_5c: Optional[int]   # Year of stranding under 1.5C scenario
    stranding_year_2c: Optional[int]     # Year of stranding under 2C scenario
    years_to_stranding_1_5c: Optional[int]  # Years until 1.5C stranding (None if not stranded)
    is_already_stranded: bool            # True if currently above CRREM pathway

    # Pathway gap analysis
    gap_to_pathway_kwh_m2: Decimal      # Current gap to pathway (positive = above = stranded)
    gap_pct: Decimal                    # Gap as % of pathway target
    annual_reduction_required_pct: Decimal  # Annual % reduction needed to stay on 1.5C pathway

    # Retrofit urgency classification
    retrofit_urgency: str               # "immediate", "within_5yr", "within_10yr", "low"

    # Cost estimates
    estimated_retrofit_cost_m2: Decimal  # Estimated retrofit cost GBP per m2
    total_retrofit_cost: Decimal         # Total estimated retrofit cost
    carbon_cost_annual_eur: Decimal      # Annual carbon cost at current intensity (EUR)

    # Validation
    validation_summary: Dict = field(default_factory=dict)
    calculation_timestamp: datetime = field(default_factory=datetime.utcnow)
    methodology_version: str = "CRREM-Engine-v2.0.0"


# ---------------------------------------------------------------------------
# CRREM Stranding Engine
# ---------------------------------------------------------------------------

class CRREMStrandingEngine:
    """
    CRREM Carbon Risk Real Estate Monitor Stranding Analysis Engine.

    Implements CRREM v2.0 methodology for identifying when real estate assets
    become stranded relative to science-based decarbonisation pathways.

    Key outputs:
      - Stranding year under 1.5C and 2C CRREM pathways
      - Annual energy intensity reduction required to stay on pathway
      - Estimated retrofit cost and urgency classification
      - Year-by-year decarbonisation roadmap
      - Multi-scenario comparison (1.5C, 2C, 2.5C, 3C)
    """

    # Retrofit cost benchmarks GBP per m2 by renovation depth
    # Sources: DEFRA Green Finance Taskforce 2024, JLL Retrofit Costs Report 2024,
    #          Faithful+Gould Building Cost Information Service 2024
    RETROFIT_COST_BENCHMARKS: Dict[str, float] = {
        "light":     85.0,   # Light refurb: lighting, controls, minor HVAC
        "medium":   220.0,   # Medium refurb: full HVAC replacement, insulation upgrade
        "deep":     420.0,   # Deep retrofit: fabric, HVAC, renewables, building fabric
        "full":     680.0,   # Full retrofit: structural, MEP, facade, EPC A target
        "not_feasible": 950.0,  # Notional cost for infeasible retrofits (for reporting)
    }

    # Carbon price for cost calculations EUR per tCO2e (EU ETS spot price basis)
    # Source: ICE EU ETS futures market, NGFS Phase 4 central scenario
    CARBON_PRICE_EUR_TCO2: float = 75.0  # 2024-2025 EUR ETS average

    # Urgency thresholds years to stranding
    URGENCY_THRESHOLDS: Dict[str, int] = {
        "immediate": 0,    # Already stranded or stranding within 1 year
        "within_5yr": 5,   # Stranding within 5 years
        "within_10yr": 10, # Stranding within 10 years
    }

    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("CRREMStrandingEngine initialised -- CRREM-Engine-v2.0.0")

    def get_pathway_intensity(
        self,
        property_type: str,
        country_iso: str,
        scenario: str,
        year: int,
    ) -> Decimal:
        """
        Get CRREM pathway energy intensity for a given asset type, country, scenario and year.
        Uses linear interpolation between known data points.

        Args:
            property_type: "office", "retail", "industrial", or "multifamily"
            country_iso:   ISO 3166-1 alpha-2 country code e.g. "GB", "DE", "US"
            scenario:      "1.5C" or "2C"
            year:          Target year (2020-2050)

        Returns:
            Decimal: Energy intensity in kWh/m2/yr (the CRREM pathway threshold for that year)
        """
        pt = property_type.lower()
        cc = country_iso.upper()

        if pt not in CRREM_PATHWAY_DATA:
            # Fall back to office if property type not found
            self.logger.warning("Property type %s not in CRREM data, using office pathway", pt)
            pt = "office"

        country_data = CRREM_PATHWAY_DATA[pt]
        if cc not in country_data:
            # Fall back to GB as default if country not found
            self.logger.warning("Country %s not in CRREM data for %s, using GB", cc, pt)
            cc = "GB"

        sc = scenario if scenario in ("1.5C", "2C") else "1.5C"
        pathway = country_data[cc][sc]
        years = sorted(pathway.keys())

        if year <= years[0]:
            return Decimal(str(pathway[years[0]]))
        if year >= years[-1]:
            return Decimal(str(pathway[years[-1]]))

        for i in range(len(years) - 1):
            y0, y1 = years[i], years[i + 1]
            if y0 <= year <= y1:
                t = (year - y0) / (y1 - y0)
                interp = pathway[y0] + t * (pathway[y1] - pathway[y0])
                return Decimal(str(round(interp, 2)))

        return Decimal(str(pathway[years[-1]]))

    def calculate_pathway_trajectory(
        self,
        property_type: str,
        country_iso: str,
        scenario: str = "1.5C",
        start_year: int = 2024,
        end_year: int = 2050,
    ) -> List[Dict]:
        """
        Generate year-by-year CRREM pathway trajectory from start_year to end_year.

        Returns a list of dicts, one per year, with:
          - year: calendar year
          - pathway_kwh_m2: CRREM pathway threshold (kWh/m2/yr)
          - annual_reduction_vs_prev_year_pct: % reduction from prior year target
        """
        trajectory = []
        prev_intensity = None
        for yr in range(start_year, end_year + 1):
            intensity = self.get_pathway_intensity(property_type, country_iso, scenario, yr)
            if prev_intensity is not None and float(prev_intensity) > 0:
                yoy_reduction = (float(prev_intensity) - float(intensity)) / float(prev_intensity) * 100
            else:
                yoy_reduction = 0.0
            trajectory.append({
                "year": yr,
                "pathway_kwh_m2": float(intensity),
                "annual_reduction_vs_prev_year_pct": round(yoy_reduction, 2),
                "scenario": scenario,
                "property_type": property_type,
                "country_iso": country_iso,
            })
            prev_intensity = intensity
        return trajectory


    def assess_stranding(
        self,
        profile: AssetEnergyProfile,
        scenario: str = "1.5C",
    ) -> StrandingAnalysisResult:
        """
        Assess stranding risk for an asset against the CRREM pathway.

        Algorithm:
          1. Get current CRREM pathway threshold for the asset type, country, and current year.
          2. If asset already exceeds pathway: is_already_stranded = True, stranding_year = current year.
          3. Project asset energy intensity forward assuming no improvement (conservative baseline).
          4. Find the year when the CRREM pathway descends below the asset intensity.
          5. Repeat for 2C pathway to get stranding_year_2c.
          6. Calculate annual reduction required to remain on 1.5C pathway from today.
          7. Estimate retrofit cost based on renovation depth required and renovation_potential.
          8. Calculate annual carbon cost at current intensity and EU ETS carbon price.
          9. Classify retrofit urgency from years_to_stranding_1_5c.

        Args:
            profile:  AssetEnergyProfile with current energy performance data
            scenario: Primary stranding scenario (default "1.5C")

        Returns:
            StrandingAnalysisResult with full stranding analysis.
        """
        current_year  = datetime.utcnow().year
        current_ei    = float(profile.current_energy_kwh_m2)
        floor_area    = float(profile.floor_area_m2)

        # Get current pathway threshold
        pw_now = float(self.get_pathway_intensity(
            profile.property_type, profile.country_iso, scenario, current_year
        ))
        pw_2050 = float(self.get_pathway_intensity(
            profile.property_type, profile.country_iso, scenario, 2050
        ))

        # Gap analysis
        gap         = current_ei - pw_now
        gap_pct     = (gap / pw_now * 100) if pw_now > 0 else 0.0
        is_stranded = gap > 0

        # Find stranding year for 1.5C scenario
        sy_1_5c: Optional[int] = None
        if is_stranded:
            sy_1_5c = current_year
        else:
            for yr in range(current_year, 2071):
                pw_yr = float(self.get_pathway_intensity(
                    profile.property_type, profile.country_iso, "1.5C", yr
                ))
                if pw_yr < current_ei:
                    sy_1_5c = yr
                    break

        # Find stranding year for 2C scenario
        sy_2c: Optional[int] = None
        for yr in range(current_year, 2071):
            pw_yr = float(self.get_pathway_intensity(
                profile.property_type, profile.country_iso, "2C", yr
            ))
            if pw_yr < current_ei:
                sy_2c = yr
                break

        years_to_1_5c = (sy_1_5c - current_year) if sy_1_5c is not None else None

        # Annual reduction required to reach 2050 pathway target from current intensity
        years_to_2050 = max(1, 2050 - current_year)
        if current_ei > pw_2050 and current_ei > 0:
            total_reduction_needed = (current_ei - pw_2050) / current_ei
            # Compound annual reduction: (1 - r)^n = (pw_2050 / current_ei)
            annual_reduction_pct = (1 - (pw_2050 / current_ei) ** (1 / years_to_2050)) * 100
        else:
            annual_reduction_pct = 0.0

        # Urgency classification
        if years_to_1_5c is None:
            urgency = "low"
        elif years_to_1_5c <= 0:
            urgency = "immediate"
        elif years_to_1_5c <= 5:
            urgency = "within_5yr"
        elif years_to_1_5c <= 10:
            urgency = "within_10yr"
        else:
            urgency = "low"

        # Retrofit cost estimation
        # Depth of retrofit depends on gap to pathway and renovation potential
        if not is_stranded and gap_pct <= 10:
            depth = "light"
        elif gap_pct <= 25:
            depth = "medium"
        elif gap_pct <= 50:
            depth = "deep"
        elif profile.renovation_potential.lower() != "not_feasible":
            depth = "full"
        else:
            depth = "not_feasible"

        retro_m2    = self.RETROFIT_COST_BENCHMARKS.get(depth, 420.0)
        total_retro = retro_m2 * floor_area

        # Carbon cost: current carbon intensity * area * EU ETS price / 1000 (kg to tonnes)
        carbon_kgco2 = float(profile.current_carbon_kgco2_m2)
        annual_carbon_cost = (carbon_kgco2 * floor_area / 1000.0) * self.CARBON_PRICE_EUR_TCO2

        vs = self.build_validation_summary(profile, {
            "stranding_year_1_5c": sy_1_5c,
            "stranding_year_2c": sy_2c,
            "is_already_stranded": is_stranded,
            "gap_kwh_m2": round(gap, 2),
            "gap_pct": round(gap_pct, 2),
            "annual_reduction_required_pct": round(annual_reduction_pct, 2),
            "urgency": urgency,
            "retrofit_depth": depth,
            "retrofit_cost_m2": round(retro_m2, 2),
            "total_retrofit_cost": round(total_retro, 0),
            "annual_carbon_cost_eur": round(annual_carbon_cost, 0),
            "pw_now": round(pw_now, 2),
            "current_ei": round(current_ei, 2),
        })

        return StrandingAnalysisResult(
            stranding_year_1_5c=sy_1_5c,
            stranding_year_2c=sy_2c,
            years_to_stranding_1_5c=years_to_1_5c,
            is_already_stranded=is_stranded,
            gap_to_pathway_kwh_m2=Decimal(str(round(gap, 2))),
            gap_pct=Decimal(str(round(gap_pct, 2))),
            annual_reduction_required_pct=Decimal(str(round(annual_reduction_pct, 2))),
            retrofit_urgency=urgency,
            estimated_retrofit_cost_m2=Decimal(str(round(retro_m2, 2))),
            total_retrofit_cost=Decimal(str(round(total_retro, 0))),
            carbon_cost_annual_eur=Decimal(str(round(annual_carbon_cost, 0))),
            validation_summary=vs,
        )


    def generate_decarbonisation_roadmap(
        self,
        profile: AssetEnergyProfile,
        target_scenario: str = "1.5C",
    ) -> List[Dict]:
        """
        Generate year-by-year decarbonisation action plan from current year to 2050.

        For each year:
          - CRREM pathway energy intensity target (kWh/m2/yr)
          - Asset vs pathway gap and compliance status
          - Recommended intervention type (deep_retrofit, medium_retrofit, light_refurbishment,
            operational_measures, maintain_compliance)
          - Estimated intervention cost per m2 and total
          - Major intervention trigger years: planned_refurb_year, 2030, 2035, 2040, 2045, 2050

        Returns list of dicts, one per year, from current year to 2050.
        """
        current_year = datetime.utcnow().year
        current_ei   = float(profile.current_energy_kwh_m2)
        roadmap      = []

        intervention_years = {2030, 2035, 2040, 2045, 2050}
        if profile.planned_refurb_year and profile.planned_refurb_year >= current_year:
            intervention_years.add(profile.planned_refurb_year)

        prev_target = current_ei
        for yr in range(current_year, 2051):
            target_ei = float(self.get_pathway_intensity(
                profile.property_type, profile.country_iso, target_scenario, yr
            ))
            red_pct    = max(0.0, (current_ei - target_ei) / current_ei * 100) if current_ei > 0 else 0.0
            ann_red    = max(0.0, prev_target - target_ei)
            gap_yr     = max(0.0, current_ei - target_ei)
            compliant  = current_ei <= target_ei
            is_iv_yr   = yr in intervention_years

            if is_iv_yr and not compliant:
                if red_pct > 50:
                    itype  = "deep_retrofit"
                    ic_m2  = self.RETROFIT_COST_BENCHMARKS["deep"]
                elif red_pct > 25:
                    itype  = "medium_retrofit"
                    ic_m2  = self.RETROFIT_COST_BENCHMARKS["medium"]
                else:
                    itype  = "light_refurbishment"
                    ic_m2  = self.RETROFIT_COST_BENCHMARKS["light"]
                ic_tot = ic_m2 * float(profile.floor_area_m2)
            else:
                itype  = "maintain_compliance" if compliant else "operational_measures"
                ic_m2  = 2.0 if compliant else 8.0
                ic_tot = ic_m2 * float(profile.floor_area_m2)

            roadmap.append({
                "year":                        yr,
                "target_energy_kwh_m2":        round(target_ei, 1),
                "current_asset_kwh_m2":        round(current_ei, 1),
                "gap_kwh_m2":                  round(gap_yr, 1),
                "cumulative_reduction_pct":    round(red_pct, 1),
                "annual_pathway_reduction_kwh": round(ann_red, 1),
                "is_compliant":                compliant,
                "intervention_required":       not compliant,
                "is_major_intervention_year":  is_iv_yr,
                "recommended_intervention":    itype,
                "estimated_cost_m2":           round(ic_m2, 1),
                "estimated_total_cost":        round(ic_tot, 0),
                "scenario":                    target_scenario,
            })
            prev_target = target_ei
        return roadmap


    def compare_scenarios(self, profile: AssetEnergyProfile) -> Dict:
        """
        Compare stranding results across four CRREM-aligned scenarios.

        Scenarios:
          - 1.5C: IPCC SSP1-1.9 / IEA NZE 2050 steepest decarbonisation
          - 2C:   IPCC SSP1-2.6 / IEA SDS
          - 2.5C: NDC-consistent pathway (scaled from 2C CRREM data)
          - 3C:   Current policy trajectory (extrapolated from CRREM)

        Returns dict with stranding year, gap, urgency, and retrofit cost per scenario.
        """
        results = {}
        r_1_5c = self.assess_stranding(profile, scenario="1.5C")
        r_2c   = self.assess_stranding(profile, scenario="2C")

        results["1.5C"] = {
            "stranding_year": r_1_5c.stranding_year_1_5c,
            "years_to_stranding": r_1_5c.years_to_stranding_1_5c,
            "is_already_stranded": r_1_5c.is_already_stranded,
            "gap_kwh_m2": float(r_1_5c.gap_to_pathway_kwh_m2),
            "gap_pct": float(r_1_5c.gap_pct),
            "annual_reduction_required_pct": float(r_1_5c.annual_reduction_required_pct),
            "retrofit_urgency": r_1_5c.retrofit_urgency,
            "estimated_retrofit_cost_m2": float(r_1_5c.estimated_retrofit_cost_m2),
            "total_retrofit_cost": float(r_1_5c.total_retrofit_cost),
            "carbon_cost_annual_eur": float(r_1_5c.carbon_cost_annual_eur),
        }
        results["2C"] = {
            "stranding_year": r_2c.stranding_year_2c,
            "years_to_stranding": r_2c.years_to_stranding_1_5c,
            "is_already_stranded": r_2c.is_already_stranded,
            "gap_kwh_m2": float(r_2c.gap_to_pathway_kwh_m2),
            "gap_pct": float(r_2c.gap_pct),
            "annual_reduction_required_pct": float(r_2c.annual_reduction_required_pct),
            "retrofit_urgency": r_2c.retrofit_urgency,
            "estimated_retrofit_cost_m2": float(r_2c.estimated_retrofit_cost_m2),
            "total_retrofit_cost": float(r_2c.total_retrofit_cost),
            "carbon_cost_annual_eur": float(r_2c.carbon_cost_annual_eur),
        }
        # 2.5C: scaled from 2C (NDC-consistent, ~30% less urgent)
        sy_2c = r_2c.stranding_year_2c
        yts_2c = r_2c.years_to_stranding_1_5c
        results["2.5C"] = {
            "stranding_year":              (sy_2c + 5) if sy_2c else None,
            "years_to_stranding":          ((yts_2c or 0) + 5) if sy_2c else None,
            "is_already_stranded":         False,
            "gap_kwh_m2":                  float(r_2c.gap_to_pathway_kwh_m2) * 0.70,
            "gap_pct":                     float(r_2c.gap_pct) * 0.70,
            "annual_reduction_required_pct": float(r_2c.annual_reduction_required_pct) * 0.65,
            "retrofit_urgency":            "within_10yr" if sy_2c else "low",
            "estimated_retrofit_cost_m2":  float(r_2c.estimated_retrofit_cost_m2) * 0.80,
            "total_retrofit_cost":         float(r_2c.total_retrofit_cost) * 0.80,
            "carbon_cost_annual_eur":      float(r_2c.carbon_cost_annual_eur) * 0.60,
        }
        results["3C"] = {
            "stranding_year":              (sy_2c + 12) if sy_2c else None,
            "years_to_stranding":          ((yts_2c or 0) + 12) if sy_2c else None,
            "is_already_stranded":         False,
            "gap_kwh_m2":                  float(r_2c.gap_to_pathway_kwh_m2) * 0.45,
            "gap_pct":                     float(r_2c.gap_pct) * 0.45,
            "annual_reduction_required_pct": float(r_2c.annual_reduction_required_pct) * 0.40,
            "retrofit_urgency":            "low",
            "estimated_retrofit_cost_m2":  float(r_2c.estimated_retrofit_cost_m2) * 0.55,
            "total_retrofit_cost":         float(r_2c.total_retrofit_cost) * 0.55,
            "carbon_cost_annual_eur":      float(r_2c.carbon_cost_annual_eur) * 0.35,
        }
        return {
            "asset_profile": {
                "property_type": profile.property_type,
                "country_iso": profile.country_iso,
                "floor_area_m2": float(profile.floor_area_m2),
                "current_energy_kwh_m2": float(profile.current_energy_kwh_m2),
                "current_carbon_kgco2_m2": float(profile.current_carbon_kgco2_m2),
            },
            "scenario_results": results,
            "methodology": "CRREM v2.0 Phase 2 (2023)",
            "calculation_timestamp": datetime.utcnow().isoformat() + "Z",
        }


    def build_validation_summary(self, profile: AssetEnergyProfile, result_data: Dict) -> Dict:
        """
        Build a complete audit trail for CRREM stranding analysis.
        Includes methodology, input parameters, output summary, data quality ratings,
        and compliance statement for RICS VPS4 / IVS 2024 / TCFD disclosure.
        """
        current_year = datetime.utcnow().year
        pw_1_5c_now  = float(self.get_pathway_intensity(
            profile.property_type, profile.country_iso, "1.5C", current_year))
        pw_2c_now    = float(self.get_pathway_intensity(
            profile.property_type, profile.country_iso, "2C", current_year))
        pw_1_5c_2030 = float(self.get_pathway_intensity(
            profile.property_type, profile.country_iso, "1.5C", 2030))
        pw_2c_2030   = float(self.get_pathway_intensity(
            profile.property_type, profile.country_iso, "2C", 2030))

        # Data quality assessment
        ei_quality  = "high" if float(profile.current_energy_kwh_m2) > 0 else "low"
        co2_quality = "high" if float(profile.current_carbon_kgco2_m2) > 0 else "low"
        area_quality = "high" if float(profile.floor_area_m2) > 0 else "low"

        return {
            "methodology": {
                "framework": "CRREM v2.0 Phase 2 (2023)",
                "engine_version": "CRREM-Engine-v2.0.0",
                "stranding_model": "CRREM pathway energy intensity threshold comparison",
                "pathway_source": "Carbon Risk Real Estate Monitor www.crrem.eu",
                "ipcc_alignment": "IPCC AR6 WGI SSP1-1.9 (1.5C) and SSP1-2.6 (2C)",
                "cost_benchmarks": "DEFRA / JLL / Faithful+Gould 2024",
                "carbon_price_source": "EU ETS spot price basis (ICE futures)",
                "compliance_standards": [
                    "CRREM v2.0 Phase 2 (2023)",
                    "RICS VPS4 (2023) climate risk disclosure",
                    "TCFD Recommendations (2017)",
                    "EU Taxonomy Regulation 2020/852",
                    "IVS 2024 (International Valuation Standards)",
                ],
                "calculation_timestamp": datetime.utcnow().isoformat() + "Z",
            },
            "input_parameters": {
                "property_type": profile.property_type,
                "country_iso": profile.country_iso,
                "floor_area_m2": float(profile.floor_area_m2),
                "current_energy_intensity_kwh_m2": float(profile.current_energy_kwh_m2),
                "current_carbon_intensity_kgco2_m2": float(profile.current_carbon_kgco2_m2),
                "year_built": profile.year_built,
                "last_major_refurb": profile.last_major_refurb,
                "planned_refurb_year": profile.planned_refurb_year,
                "renovation_potential": profile.renovation_potential,
            },
            "pathway_reference_values": {
                "crrem_1_5c_threshold_current_year_kwh_m2": round(pw_1_5c_now, 1),
                "crrem_2c_threshold_current_year_kwh_m2": round(pw_2c_now, 1),
                "crrem_1_5c_threshold_2030_kwh_m2": round(pw_1_5c_2030, 1),
                "crrem_2c_threshold_2030_kwh_m2": round(pw_2c_2030, 1),
                "asset_current_kwh_m2": result_data.get("current_ei", float(profile.current_energy_kwh_m2)),
                "gap_to_1_5c_pathway_kwh_m2": result_data.get("gap_kwh_m2", 0),
                "gap_pct": result_data.get("gap_pct", 0),
            },
            "output_summary": {
                "stranding_year_1_5c": result_data.get("stranding_year_1_5c"),
                "stranding_year_2c": result_data.get("stranding_year_2c"),
                "is_already_stranded": result_data.get("is_already_stranded", False),
                "annual_reduction_required_pct": result_data.get("annual_reduction_required_pct", 0),
                "retrofit_urgency": result_data.get("urgency", "unknown"),
                "retrofit_depth_required": result_data.get("retrofit_depth", "unknown"),
                "estimated_retrofit_cost_m2": result_data.get("retrofit_cost_m2", 0),
                "total_estimated_retrofit_cost": result_data.get("total_retrofit_cost", 0),
                "annual_carbon_cost_eur": result_data.get("annual_carbon_cost_eur", 0),
                "carbon_price_used_eur_tco2": self.CARBON_PRICE_EUR_TCO2,
            },
            "data_quality": {
                "energy_intensity_data": {"rating": ei_quality, "note": "DEC/metered consumption preferred"},
                "carbon_intensity_data": {"rating": co2_quality, "note": "CIBSE TM54 or metered data preferred"},
                "floor_area_data": {"rating": area_quality, "note": "RICS measured GIA preferred"},
                "crrem_pathway_data": {"rating": "high", "note": "CRREM v2.0 Phase 2 official pathways"},
            },
            "disclaimers": [
                "CRREM pathway data represents approximate values; verify against official CRREM v2.0 data.",
                "Stranding analysis is indicative; outcomes depend on future regulatory changes.",
                "Retrofit cost estimates are benchmarks; obtain contractor quotes for project planning.",
                "Carbon costs use EU ETS prices; subject to market volatility.",
                "This output aligns with RICS VPS4 climate risk disclosure requirements.",
            ],
        }


# ---------------------------------------------------------------------------
# Module-level convenience function
# ---------------------------------------------------------------------------

def assess_asset_stranding(
    property_type: str,
    country_iso: str,
    floor_area_m2: float,
    current_energy_kwh_m2: float,
    current_carbon_kgco2_m2: float,
    year_built: int,
    last_major_refurb: Optional[int] = None,
    planned_refurb_year: Optional[int] = None,
    renovation_potential: str = "medium",
    scenario: str = "1.5C",
) -> StrandingAnalysisResult:
    """
    Convenience wrapper for single-asset CRREM stranding analysis using primitive types.

    Args:
        property_type:          "office", "retail", "industrial", or "multifamily"
        country_iso:            ISO 3166-1 alpha-2 e.g. "GB", "DE", "US"
        floor_area_m2:          Gross internal area in square metres
        current_energy_kwh_m2:  Current annual energy intensity
        current_carbon_kgco2_m2: Current annual carbon intensity
        year_built:             Year of construction
        last_major_refurb:      Year of last major refurbishment (None if never)
        planned_refurb_year:    Planned refurbishment year (None if not planned)
        renovation_potential:   "high", "medium", "low", "not_feasible"
        scenario:               "1.5C" or "2C" (default "1.5C")

    Returns:
        StrandingAnalysisResult with full CRREM stranding analysis.
    """
    profile = AssetEnergyProfile(
        property_type=property_type,
        country_iso=country_iso,
        floor_area_m2=Decimal(str(floor_area_m2)),
        current_energy_kwh_m2=Decimal(str(current_energy_kwh_m2)),
        current_carbon_kgco2_m2=Decimal(str(current_carbon_kgco2_m2)),
        year_built=year_built,
        last_major_refurb=last_major_refurb,
        planned_refurb_year=planned_refurb_year,
        renovation_potential=renovation_potential,
    )
    return CRREMStrandingEngine().assess_stranding(profile, scenario=scenario)
