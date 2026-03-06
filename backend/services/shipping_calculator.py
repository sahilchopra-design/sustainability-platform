"""
Shipping Decarbonisation Calculator — IMO CII / EEXI / AER
Aligned with: IMO MARPOL Annex VI, CII Rating System (A-E), 2023 IMO GHG Strategy

References:
  - IMO Resolution MEPC.337(76) — CII operational carbon intensity
  - IMO Resolution MEPC.333(76) — EEXI energy efficiency index
  - IMO 2050 GHG target: net-zero by 2050 (revised 2023 Strategy)
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────
# CO2 Emission Factors (tCO2 / tonne fuel)  — IMO MARPOL
# ─────────────────────────────────────────────────────────
EMISSION_FACTORS: Dict[str, Decimal] = {
    "HFO": Decimal("3.114"),       # Heavy Fuel Oil
    "VLSFO": Decimal("3.151"),     # Very Low Sulphur Fuel Oil
    "MDO": Decimal("3.206"),       # Marine Diesel Oil
    "LNG": Decimal("2.750"),       # Liquefied Natural Gas
    "LPG_butane": Decimal("3.030"),
    "LPG_propane": Decimal("3.000"),
    "METHANOL": Decimal("1.375"),  # bio-methanol at 50% bio share
    "AMMONIA": Decimal("0.000"),   # green ammonia (zero combustion CO2)
    "HYDROGEN": Decimal("0.000"),  # green hydrogen
}

# Calorific values (GJ / tonne fuel)
CALORIFIC_VALUES: Dict[str, Decimal] = {
    "HFO": Decimal("40.20"),
    "VLSFO": Decimal("40.30"),
    "MDO": Decimal("42.70"),
    "LNG": Decimal("48.00"),
    "LPG_butane": Decimal("45.80"),
    "LPG_propane": Decimal("46.30"),
    "METHANOL": Decimal("19.90"),
    "AMMONIA": Decimal("18.60"),
    "HYDROGEN": Decimal("120.00"),
}

# CII reference line parameters by ship type  (a × W^-c)
# Source: IMO MEPC.338(76) Table 1
CII_REFERENCE_PARAMS: Dict[str, tuple] = {
    # ship_type: (a, c, capacity_metric)
    "bulker":     (961.79, 0.477, "DWT"),
    "tanker":     (1218.80, 0.488, "DWT"),
    "container":  (1984.60, 0.489, "GT"),
    "lng_carrier":(144.13, 0.183, "DWT"),
    "ro_ro":      (1967.68, 0.482, "GT"),
    "cruise":     (930.44, 0.383, "GT"),
    "general_cargo": (107.48, 0.216, "DWT"),
}

# CII rating boundaries (exp factor relative to reference line)
# Source: IMO MEPC.338(76)  — 2023 factors
CII_RATING_FACTORS: Dict[str, Dict[str, Decimal]] = {
    "bulker": {
        "A": Decimal("0.86"), "B": Decimal("0.94"), "C": Decimal("1.06"),
        "D": Decimal("1.18"),  # above D = E
    },
    "tanker": {
        "A": Decimal("0.82"), "B": Decimal("0.93"), "C": Decimal("1.08"),
        "D": Decimal("1.28"),
    },
    "container": {
        "A": Decimal("0.83"), "B": Decimal("0.94"), "C": Decimal("1.07"),
        "D": Decimal("1.19"),
    },
    "lng_carrier": {
        "A": Decimal("0.89"), "B": Decimal("0.98"), "C": Decimal("1.06"),
        "D": Decimal("1.13"),
    },
    "ro_ro": {
        "A": Decimal("0.86"), "B": Decimal("0.94"), "C": Decimal("1.06"),
        "D": Decimal("1.18"),
    },
    "cruise": {
        "A": Decimal("0.87"), "B": Decimal("0.95"), "C": Decimal("1.06"),
        "D": Decimal("1.16"),
    },
    "general_cargo": {
        "A": Decimal("0.83"), "B": Decimal("0.94"), "C": Decimal("1.07"),
        "D": Decimal("1.19"),
    },
}

# IMO 2050 strategy — required AER reduction vs 2008 baseline (% by year)
IMO_REQUIRED_REDUCTIONS = {
    2023: 0.11,  # 11% from 2008 baseline for EEXI
    2025: 0.20, 2030: 0.40, 2035: 0.55, 2040: 0.70, 2045: 0.85, 2050: 1.00,
}

# 2008 Average AER baseline by ship type (gCO2 / dwt-nm approx)
AER_2008_BASELINE: Dict[str, float] = {
    "bulker": 5.3, "tanker": 6.1, "container": 16.1,
    "lng_carrier": 9.8, "ro_ro": 28.0, "cruise": 250.0, "general_cargo": 12.0,
}


# ─────────────────────────────────────────────────────────
# Input / Output
# ─────────────────────────────────────────────────────────
@dataclass
class ShippingInputs:
    vessel_name: str
    vessel_type: str           # bulker | tanker | container | lng_carrier | ro_ro | cruise | general_cargo
    dwt: Decimal               # deadweight tonnage
    gross_tonnage: Decimal
    fuel_type: str             # HFO | VLSFO | LNG | METHANOL | AMMONIA | HYDROGEN | MDO
    annual_fuel_tonnes: Decimal
    annual_distance_nm: Decimal
    annual_cargo_tonnes: Decimal
    build_year: int
    reference_year: int = 2024


@dataclass
class ShippingResult:
    vessel_name: str
    vessel_type: str

    # Core metrics
    annual_co2_tonnes: Decimal
    aer: Decimal               # Annual Efficiency Ratio gCO2 / dwt-nm
    eexi: Optional[Decimal]    # Energy Efficiency eXisting ship Index gCO2 / t-nm

    # CII Rating
    cii_reference: Decimal     # reference CII value
    cii_actual: Decimal        # attained CII = AER
    cii_rating: str            # A / B / C / D / E

    # Alignment
    imo_2030_target_aer: Decimal
    imo_2050_target_aer: Decimal
    pct_vs_2030_target: Decimal   # positive = above target (worse)
    projected_stranding_year: Optional[int]

    # Improvement pathway
    required_fuel_switch_to_A: Optional[str]
    required_efficiency_improvement_pct: Optional[Decimal]
    narrative: str

    data_available: bool = True
    error_message: Optional[str] = None


# ─────────────────────────────────────────────────────────
# Calculator
# ─────────────────────────────────────────────────────────
class ShippingCalculator:

    def calculate(self, inp: ShippingInputs) -> ShippingResult:
        try:
            return self._run(inp)
        except Exception as e:
            logger.exception("Shipping calculation failed: %s", e)
            return ShippingResult(
                vessel_name=inp.vessel_name, vessel_type=inp.vessel_type,
                annual_co2_tonnes=Decimal("0"), aer=Decimal("0"), eexi=None,
                cii_reference=Decimal("0"), cii_actual=Decimal("0"), cii_rating="C",
                imo_2030_target_aer=Decimal("0"), imo_2050_target_aer=Decimal("0"),
                pct_vs_2030_target=Decimal("0"), projected_stranding_year=None,
                required_fuel_switch_to_A=None, required_efficiency_improvement_pct=None,
                narrative="Calculation failed.",
                data_available=False, error_message=str(e),
            )

    def _run(self, inp: ShippingInputs) -> ShippingResult:
        vtype = inp.vessel_type.lower().replace(" ", "_")
        if vtype not in CII_REFERENCE_PARAMS:
            vtype = "bulker"  # graceful fallback

        ef = EMISSION_FACTORS.get(inp.fuel_type.upper(), EMISSION_FACTORS["VLSFO"])

        # Annual CO2
        annual_co2 = (inp.annual_fuel_tonnes * ef).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

        # AER (gCO2 / dwt-nm) — using DWT as capacity denominator
        capacity = inp.dwt if CII_REFERENCE_PARAMS[vtype][2] == "DWT" else inp.gross_tonnage
        if inp.annual_distance_nm > 0 and capacity > 0:
            aer = (annual_co2 * 1_000_000 / (capacity * inp.annual_distance_nm)).quantize(
                Decimal("0.001"), rounding=ROUND_HALF_UP
            )
        else:
            aer = Decimal("0")

        # CII Reference line: a × capacity^-c
        a, c, _ = CII_REFERENCE_PARAMS[vtype]
        cii_ref = Decimal(str(a)) * (capacity ** Decimal(str(-c)))
        cii_ref = cii_ref.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)

        # CII Rating
        rating_factors = CII_RATING_FACTORS.get(vtype, CII_RATING_FACTORS["bulker"])
        cii_rating = self._compute_rating(aer, cii_ref, rating_factors)

        # EEXI (simplified: EEXI = AER × (baseline_speed / design_speed correction))
        # Full calculation requires SFOC and installed power; use approximation
        eexi = (aer * Decimal("0.95")).quantize(Decimal("0.001"))

        # IMO 2030 and 2050 targets
        baseline = AER_2008_BASELINE.get(vtype, 6.0)
        imo_2030 = Decimal(str(baseline * (1 - IMO_REQUIRED_REDUCTIONS[2030]))).quantize(Decimal("0.001"))
        imo_2050 = Decimal("0")  # net-zero

        # % vs 2030 target
        if imo_2030 > 0:
            pct_vs_2030 = ((aer - imo_2030) / imo_2030 * 100).quantize(Decimal("0.1"))
        else:
            pct_vs_2030 = Decimal("0")

        # Projected stranding year (when mandatory CII D/E triggers regulatory action)
        stranding_year = self._estimate_stranding(aer, cii_ref, vtype)

        # Improvement pathway
        fuel_switch, eff_improvement = self._improvement_pathway(inp, aer, cii_ref, rating_factors)

        narrative = self._build_narrative(inp.vessel_name, cii_rating, aer, imo_2030, pct_vs_2030, fuel_switch)

        return ShippingResult(
            vessel_name=inp.vessel_name,
            vessel_type=vtype,
            annual_co2_tonnes=annual_co2,
            aer=aer,
            eexi=eexi,
            cii_reference=cii_ref,
            cii_actual=aer,
            cii_rating=cii_rating,
            imo_2030_target_aer=imo_2030,
            imo_2050_target_aer=imo_2050,
            pct_vs_2030_target=pct_vs_2030,
            projected_stranding_year=stranding_year,
            required_fuel_switch_to_A=fuel_switch,
            required_efficiency_improvement_pct=eff_improvement,
            narrative=narrative,
            data_available=True,
        )

    def _compute_rating(self, aer: Decimal, cii_ref: Decimal, factors: Dict[str, Decimal]) -> str:
        ratio = aer / cii_ref if cii_ref > 0 else Decimal("1")
        if ratio <= factors["A"]:
            return "A"
        elif ratio <= factors["B"]:
            return "B"
        elif ratio <= factors["C"]:
            return "C"
        elif ratio <= factors["D"]:
            return "D"
        else:
            return "E"

    def _estimate_stranding(self, aer: Decimal, cii_ref: Decimal, vtype: str) -> Optional[int]:
        """Estimate year when vessel will be D/E if no improvements made."""
        # CII reference line tightens by ~2% per year from 2026 under IMO plans
        baseline = float(AER_2008_BASELINE.get(vtype, 6.0))
        for year in range(2024, 2051):
            # Reference tightens 2% pa post-2026
            factor = 1.0 + max(0, (year - 2026) * 0.02)
            effective_ref = float(cii_ref) / factor
            d_boundary = float(CII_RATING_FACTORS.get(vtype, {}).get("D", Decimal("1.18"))) * effective_ref
            if float(aer) > d_boundary:
                return year
        return None

    def _improvement_pathway(
        self, inp: ShippingInputs, aer: Decimal, cii_ref: Decimal, factors: Dict[str, Decimal]
    ):
        """What fuel switch or efficiency improvement achieves CII Rating A?"""
        a_threshold = cii_ref * factors["A"]
        if aer <= a_threshold:
            return None, None

        # Efficiency improvement needed (speed reduction, BWTS, hull cleaning, etc.)
        eff_needed = ((aer - a_threshold) / aer * 100).quantize(Decimal("0.1"))

        # Fuel switch impact — LNG reduces CO2 by ~20-25%
        fuel_switch = None
        if inp.fuel_type.upper() in ("HFO", "VLSFO"):
            lng_aer = aer * EMISSION_FACTORS["LNG"] / EMISSION_FACTORS.get(inp.fuel_type.upper(), EMISSION_FACTORS["VLSFO"])
            if lng_aer <= a_threshold:
                fuel_switch = "Switch to LNG achieves CII Rating A"
            else:
                methanol_aer = aer * EMISSION_FACTORS["METHANOL"] / EMISSION_FACTORS.get(inp.fuel_type.upper(), Decimal("3.151"))
                if methanol_aer <= a_threshold:
                    fuel_switch = "Switch to bio-methanol achieves CII Rating A"
                else:
                    fuel_switch = "Green ammonia or H2 required for CII Rating A"
        return fuel_switch, eff_needed

    def _build_narrative(self, name, rating, aer, imo_2030, pct_vs_2030, fuel_switch) -> str:
        colour = {"A": "strong", "B": "good", "C": "moderate", "D": "poor", "E": "critical"}
        status = colour.get(rating, "moderate")
        lines = [
            f"{name} attains CII Rating {rating} ({status} performance). ",
            f"Current AER: {float(aer):.2f} gCO2/dwt-nm vs IMO 2030 target: {float(imo_2030):.2f}. ",
        ]
        if float(pct_vs_2030) > 0:
            lines.append(f"Vessel is {float(pct_vs_2030):.1f}% above IMO 2030 target — action required. ")
        else:
            lines.append(f"Vessel is {abs(float(pct_vs_2030)):.1f}% below IMO 2030 target — on track. ")
        if fuel_switch:
            lines.append(fuel_switch)
        return "".join(lines)


# Module-level singleton
shipping_calculator = ShippingCalculator()
