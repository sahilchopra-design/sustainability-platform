"""
Steel Decarbonisation Calculator — BF-BOF / EAF / DRI emission intensity
Aligned with: IEA World Steel / NZBA Steel Glidepath / ResponsibleSteel

Production routes:
  BF-BOF  (Blast Furnace + Basic Oxygen Furnace)    — 1.8–2.2 tCO2/tSteel
  EAF     (Electric Arc Furnace — scrap-based)       — 0.4–0.8 tCO2/tSteel (grid-dependent)
  DRI-EAF (Direct Reduced Iron + EAF — gas-based)   — 1.0–1.4 tCO2/tSteel
  DRI-EAF-H2 (Hydrogen DRI)                         — 0.0–0.2 tCO2/tSteel

IEA NZE 2023 steel glidepath (tCO2/tSteel):
  2020: 1.85  2025: 1.60  2030: 1.20  2035: 0.80  2040: 0.40  2045: 0.15  2050: 0.05
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────
# Emission intensities (tCO2 / tonne steel) — world average
# Source: worldsteel 2023 LCA data
# ─────────────────────────────────────────────────────────
ROUTE_INTENSITIES: Dict[str, Decimal] = {
    "BF-BOF":           Decimal("1.90"),   # coal-intensive, includes coking coal
    "BF-BOF_CCUS":      Decimal("0.55"),   # BF-BOF with 70% carbon capture
    "EAF_grid":         Decimal("0.65"),   # EAF on average grid (OECD average 0.38 kgCO2/kWh)
    "EAF_renewable":    Decimal("0.05"),   # EAF on 100% renewable electricity
    "DRI_EAF_gas":      Decimal("1.15"),   # DRI via natural gas + EAF
    "DRI_EAF_H2":       Decimal("0.10"),   # DRI via green hydrogen + EAF
    "Scrap_EAF_grid":   Decimal("0.40"),   # secondary/scrap route, average grid
}

# IEA NZE 2023 Glidepath (tCO2/tSteel — weighted average)
IEA_NZE_GLIDEPATH: Dict[int, float] = {
    2020: 1.85, 2025: 1.60, 2030: 1.20, 2035: 0.80,
    2040: 0.40, 2045: 0.15, 2050: 0.05,
}

# ResponsibleSteel / SBTi Steel Pathway (slightly more ambitious)
SBTI_GLIDEPATH: Dict[int, float] = {
    2020: 1.75, 2025: 1.50, 2030: 1.00, 2035: 0.65,
    2040: 0.30, 2045: 0.10, 2050: 0.02,
}

# EAF grid carbon intensity vs steel emission intensity lookup
# grid_intensity kgCO2/kWh → EAF steel tCO2/tSteel
# Assumes 550 kWh/t electricity for EAF
EAF_ELECTRICITY_KWH_PER_TONNE = Decimal("550")


# ─────────────────────────────────────────────────────────
# Dataclasses
# ─────────────────────────────────────────────────────────
@dataclass
class SteelInputs:
    plant_name: str
    annual_production_mt: Decimal        # million tonnes per annum
    # Production route mix (must sum to 1.0)
    bf_bof_pct: Decimal                  # 0.0–1.0
    eaf_pct: Decimal
    dri_eaf_pct: Decimal                 # gas-based DRI
    dri_h2_pct: Decimal                  # hydrogen DRI
    bf_bof_ccus_pct: Decimal             # BF-BOF with CCUS

    # EAF electricity source
    eaf_grid_carbon_intensity_kgco2_kwh: Decimal  # e.g. 0.38 for OECD average

    reference_year: int = 2024


@dataclass
class SteelGlidepathPoint:
    year: int
    weighted_intensity: Optional[float]   # tCO2/tSteel (portfolio / plant mix)
    iea_nze_target: Optional[float]
    sbti_target: Optional[float]
    rag_status: str
    deviation_pct: Optional[float]


@dataclass
class SteelResult:
    plant_name: str
    annual_production_mt: Decimal

    # Current position
    weighted_emission_intensity: Decimal   # tCO2/tSteel
    annual_co2_mt: Decimal                 # million tCO2 pa
    route_breakdown: Dict[str, Decimal]    # route → intensity contribution

    # vs IEA NZE 2030 target
    iea_2030_target: Decimal
    pct_vs_iea_2030: Decimal               # positive = above = worse
    rag_2030: str

    # Full glidepath (2020–2050)
    glidepath_series: List[SteelGlidepathPoint] = field(default_factory=list)

    # Improvement pathway
    pathway_to_iea_2030: str = ""
    reduction_needed_tco2_per_t: Decimal = Decimal("0")

    # Future mix scenarios
    scenario_full_eaf_renewable_intensity: Decimal = Decimal("0.05")
    scenario_dri_h2_50pct_intensity: Decimal = Decimal("0")

    data_available: bool = True
    error_message: Optional[str] = None


# ─────────────────────────────────────────────────────────
# Calculator
# ─────────────────────────────────────────────────────────
class SteelCalculator:

    def calculate(self, inp: SteelInputs) -> SteelResult:
        try:
            return self._run(inp)
        except Exception as e:
            logger.exception("Steel calculation failed: %s", e)
            return SteelResult(
                plant_name=inp.plant_name,
                annual_production_mt=inp.annual_production_mt,
                weighted_emission_intensity=Decimal("0"),
                annual_co2_mt=Decimal("0"),
                route_breakdown={},
                iea_2030_target=Decimal("1.20"),
                pct_vs_iea_2030=Decimal("0"),
                rag_2030="GREY",
                data_available=False,
                error_message=str(e),
            )

    def _run(self, inp: SteelInputs) -> SteelResult:
        # EAF grid-adjusted emission intensity
        eaf_grid_intensity = (
            EAF_ELECTRICITY_KWH_PER_TONNE * inp.eaf_grid_carbon_intensity_kgco2_kwh / 1000
        ).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)

        # Route-by-route contributions
        route_breakdown: Dict[str, Decimal] = {}
        total_intensity = Decimal("0")

        weights_intensities = [
            ("BF-BOF",         inp.bf_bof_pct,       ROUTE_INTENSITIES["BF-BOF"]),
            ("BF-BOF + CCUS",  inp.bf_bof_ccus_pct,  ROUTE_INTENSITIES["BF-BOF_CCUS"]),
            ("EAF (grid)",     inp.eaf_pct,           eaf_grid_intensity),
            ("DRI-EAF (gas)",  inp.dri_eaf_pct,       ROUTE_INTENSITIES["DRI_EAF_gas"]),
            ("DRI-EAF (H2)",   inp.dri_h2_pct,        ROUTE_INTENSITIES["DRI_EAF_H2"]),
        ]

        for label, weight, intensity in weights_intensities:
            contribution = weight * intensity
            total_intensity += contribution
            route_breakdown[label] = contribution.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)

        total_intensity = total_intensity.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
        annual_co2 = (total_intensity * inp.annual_production_mt).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)

        # IEA NZE 2030 target
        iea_2030 = Decimal(str(IEA_NZE_GLIDEPATH[2030]))
        if iea_2030 > 0:
            pct_vs = ((total_intensity - iea_2030) / iea_2030 * 100).quantize(Decimal("0.1"))
        else:
            pct_vs = Decimal("0")

        rag_2030 = "GREEN" if total_intensity <= iea_2030 else ("AMBER" if total_intensity <= iea_2030 * Decimal("1.10") else "RED")

        # Glidepath series (plant mix held constant — shows trajectory needed)
        glidepath_series = self._build_glidepath(total_intensity, inp)

        # Improvement pathway
        reduction_needed = max(total_intensity - iea_2030, Decimal("0"))
        pathway = self._build_pathway(inp, total_intensity, iea_2030, eaf_grid_intensity)

        # Scenario: 100% EAF renewable
        scenario_full_eaf = ROUTE_INTENSITIES["EAF_renewable"]
        # Scenario: 50% DRI-H2
        scenario_50_h2 = (
            Decimal("0.5") * ROUTE_INTENSITIES["DRI_EAF_H2"]
            + Decimal("0.5") * total_intensity
        ).quantize(Decimal("0.001"))

        return SteelResult(
            plant_name=inp.plant_name,
            annual_production_mt=inp.annual_production_mt,
            weighted_emission_intensity=total_intensity,
            annual_co2_mt=annual_co2,
            route_breakdown=route_breakdown,
            iea_2030_target=iea_2030,
            pct_vs_iea_2030=pct_vs,
            rag_2030=rag_2030,
            glidepath_series=glidepath_series,
            pathway_to_iea_2030=pathway,
            reduction_needed_tco2_per_t=reduction_needed,
            scenario_full_eaf_renewable_intensity=scenario_full_eaf,
            scenario_dri_h2_50pct_intensity=scenario_50_h2,
            data_available=True,
        )

    def _build_glidepath(self, current_intensity: Decimal, inp: SteelInputs) -> List[SteelGlidepathPoint]:
        points = []
        years = [2020, 2025, 2030, 2035, 2040, 2045, 2050]
        for yr in years:
            iea = IEA_NZE_GLIDEPATH.get(yr)
            sbti = SBTI_GLIDEPATH.get(yr)
            actual = float(current_intensity) if yr == inp.reference_year else None
            if actual and iea:
                dev = (actual - iea) / iea * 100
                rag = "GREEN" if dev <= 0 else ("AMBER" if dev <= 10 else "RED")
            else:
                rag, dev = "GREY", None
            points.append(SteelGlidepathPoint(
                year=yr,
                weighted_intensity=actual,
                iea_nze_target=iea,
                sbti_target=sbti,
                rag_status=rag,
                deviation_pct=round(dev, 1) if dev is not None else None,
            ))
        return points

    def _build_pathway(
        self, inp: SteelInputs, current: Decimal, target: Decimal, eaf_intensity: Decimal
    ) -> str:
        if current <= target:
            return f"Current intensity {float(current):.2f} tCO2/t is already below IEA NZE 2030 target ({float(target):.2f})."
        gap = current - target
        lines = [
            f"Current intensity: {float(current):.2f} tCO2/t | IEA NZE 2030 target: {float(target):.2f} tCO2/t (gap: {float(gap):.2f}). "
        ]
        if inp.bf_bof_pct > Decimal("0.3"):
            lines.append("Reduce BF-BOF share — shifting 20% to scrap-EAF (renewable) would cut intensity by ~0.3 tCO2/t. ")
        if inp.eaf_grid_carbon_intensity_kgco2_kwh > Decimal("0.3"):
            target_intensity = EAF_ELECTRICITY_KWH_PER_TONNE * Decimal("0.05") / 1000
            lines.append(
                f"Procure renewable PPAs for EAF electricity — grid decarbonisation to 50 gCO2/kWh would save "
                f"{float(eaf_intensity - target_intensity):.2f} tCO2/t on EAF share. "
            )
        if inp.dri_h2_pct < Decimal("0.1"):
            lines.append("Piloting green hydrogen DRI (10% share) would reduce intensity by ~0.18 tCO2/t. ")
        return "".join(lines)


# Module-level singleton
steel_calculator = SteelCalculator()
