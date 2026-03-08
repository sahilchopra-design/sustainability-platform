"""
Green Asset Ratio (GAR) Calculator -- EU Taxonomy Art. 449a CRR

Implements GAR calculation per:
  - CRR Art. 449a (Pillar 3 ESG disclosures, effective June 2024)
  - EU Taxonomy Regulation 2020/852 (6 environmental objectives)
  - EBA ITS on Pillar 3 ESG disclosures (EBA/ITS/2022/01)
  - CRR2 ITS Annex XI: Turnover / CapEx / OpEx KPI breakdowns
  - Commission Delegated Regulation 2021/2178 (Art. 10 disclosure)

Key formula:
  GAR = Taxonomy-Aligned Assets / Total Covered Assets

Numerator: Only TAXONOMY_ALIGNED assets (meeting SC + DNSH + MSS)
Denominator: Total on-balance-sheet assets EXCLUDING:
  - Sovereign exposures (CRR Art. 112(a))
  - Central bank exposures
  - Interbank lending (CRR Art. 112(e))
  - Derivatives held for hedging

Three KPI dimensions per CRR2 ITS:
  - TURNOVER: Revenue-based alignment
  - CAPEX: Capital expenditure-based alignment
  - OPEX: Operating expenditure-based alignment

Author: GAR Calculator Module
Version: 2.0.0
Date: 2026-03-08
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# CONSTANTS & ENUMERATIONS
# ---------------------------------------------------------------------------


class TaxonomyObjective(Enum):
    """EU Taxonomy environmental objectives (Regulation 2020/852 Art. 9)."""
    CLIMATE_MITIGATION = "CLIMATE_MITIGATION"
    CLIMATE_ADAPTATION = "CLIMATE_ADAPTATION"
    WATER = "WATER"
    CIRCULAR_ECONOMY = "CIRCULAR_ECONOMY"
    POLLUTION = "POLLUTION"
    BIODIVERSITY = "BIODIVERSITY"


class AlignmentClassification(Enum):
    """Asset taxonomy classification status."""
    TAXONOMY_ALIGNED = "TAXONOMY_ALIGNED"
    TAXONOMY_ELIGIBLE = "TAXONOMY_ELIGIBLE"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"


class KPIType(Enum):
    """CRR2 ITS KPI types for GAR alignment measurement."""
    TURNOVER = "TURNOVER"
    CAPEX = "CAPEX"
    OPEX = "OPEX"


# Exposure types excluded from GAR denominator per CRR Art. 449a
EXCLUDED_ASSET_TYPES = {"SOVEREIGN", "CENTRAL_BANK", "INTERBANK", "HEDGING_DERIVATIVE"}


# ---------------------------------------------------------------------------
# NACE TAXONOMY MAPPING
# ---------------------------------------------------------------------------
# Maps NACE Rev. 2 sector codes to eligible EU Taxonomy environmental
# objectives per Delegated Regulation 2021/2139 (Climate Delegated Act)
# and Delegated Regulation 2023/2486 (Environmental Delegated Act).

NACE_TAXONOMY_MAP: Dict[str, List[str]] = {
    # Energy
    "D35.11": ["CLIMATE_MITIGATION", "CLIMATE_ADAPTATION"],           # Electric power generation
    "D35.30": ["CLIMATE_MITIGATION"],                                 # Steam and air conditioning supply
    # Manufacturing
    "C20.11": ["CLIMATE_MITIGATION", "POLLUTION"],                    # Industrial gases
    "C20.13": ["CLIMATE_MITIGATION", "CIRCULAR_ECONOMY"],             # Other inorganic basic chemicals
    "C22.11": ["CIRCULAR_ECONOMY"],                                   # Rubber tyres and tubes
    "C23.51": ["CLIMATE_MITIGATION"],                                 # Cement
    "C24.10": ["CLIMATE_MITIGATION"],                                 # Basic iron and steel
    "C24.42": ["CLIMATE_MITIGATION"],                                 # Aluminium production
    "C25.11": ["CLIMATE_MITIGATION"],                                 # Metal structures
    "C27.40": ["CLIMATE_MITIGATION"],                                 # Electric lighting equipment
    "C29.10": ["CLIMATE_MITIGATION", "POLLUTION"],                    # Motor vehicles
    # Construction
    "F41.10": ["CLIMATE_MITIGATION", "CLIMATE_ADAPTATION"],           # Development of building projects
    "F41.20": ["CLIMATE_MITIGATION", "CLIMATE_ADAPTATION"],           # Construction of residential buildings
    "F42.11": ["CLIMATE_MITIGATION"],                                 # Roads and motorways
    "F43.21": ["CLIMATE_MITIGATION"],                                 # Electrical installation
    # Transport
    "H49.10": ["CLIMATE_MITIGATION"],                                 # Passenger rail transport
    "H49.20": ["CLIMATE_MITIGATION"],                                 # Freight rail transport
    "H49.31": ["CLIMATE_MITIGATION", "POLLUTION"],                    # Urban and suburban passenger transport
    "H50.10": ["CLIMATE_MITIGATION", "WATER"],                        # Sea and coastal passenger water transport
    "H50.40": ["CLIMATE_MITIGATION", "WATER"],                        # Inland freight water transport
    # Water & waste
    "E36.00": ["WATER", "CLIMATE_ADAPTATION"],                        # Water collection, treatment and supply
    "E37.00": ["WATER", "POLLUTION"],                                 # Sewerage
    "E38.11": ["CIRCULAR_ECONOMY"],                                   # Collection of non-hazardous waste
    "E38.21": ["CIRCULAR_ECONOMY", "POLLUTION"],                      # Treatment and disposal of non-hazardous waste
    "E38.32": ["CIRCULAR_ECONOMY"],                                   # Recovery of sorted materials
    # Forestry
    "A01.11": ["CLIMATE_MITIGATION", "BIODIVERSITY"],                 # Growing of cereals
    "A02.10": ["CLIMATE_MITIGATION", "BIODIVERSITY"],                 # Silviculture and other forestry activities
    "A02.20": ["CLIMATE_MITIGATION", "BIODIVERSITY"],                 # Logging
    # ICT
    "J62.01": ["CLIMATE_MITIGATION"],                                 # Computer programming activities
    "J63.11": ["CLIMATE_MITIGATION"],                                 # Data processing, hosting
    # Professional services
    "M71.11": ["CLIMATE_MITIGATION", "CLIMATE_ADAPTATION"],           # Architectural activities
    "M71.12": ["CLIMATE_MITIGATION", "CLIMATE_ADAPTATION"],           # Engineering activities
    "M72.19": ["CLIMATE_MITIGATION", "BIODIVERSITY"],                 # Other R&D on natural sciences
}


# ---------------------------------------------------------------------------
# DATACLASSES
# ---------------------------------------------------------------------------


@dataclass
class GARExposure:
    """Single exposure / asset for GAR calculation."""
    exposure_id: str
    counterparty_name: str
    asset_type: str                      # e.g. NFC_LOAN, HOUSEHOLD_MORTGAGE, SOVEREIGN
    gross_carrying_amount: float         # EUR
    classification: str                  # TAXONOMY_ALIGNED, TAXONOMY_ELIGIBLE, NOT_ELIGIBLE
    primary_objective: str = ""          # TaxonomyObjective value
    secondary_objectives: List[str] = field(default_factory=list)
    nace_code: str = ""                  # NACE Rev. 2 code
    sector: str = ""                     # Sector name
    country: str = ""                    # ISO 2-letter country code

    # Amounts by KPI type (CRR2 ITS)
    turnover_aligned: float = 0.0        # Turnover-based aligned amount
    turnover_eligible: float = 0.0
    capex_aligned: float = 0.0           # CapEx-based aligned amount
    capex_eligible: float = 0.0
    opex_aligned: float = 0.0            # OpEx-based aligned amount
    opex_eligible: float = 0.0

    # Household-specific fields
    epc_rating: str = ""                 # A-G for mortgages
    is_ev_loan: bool = False
    is_renovation_loan: bool = False


@dataclass
class GARObjectiveBreakdown:
    """GAR breakdown for a single environmental objective."""
    objective: str
    objective_label: str
    aligned_amount: float
    eligible_amount: float
    not_eligible_amount: float
    aligned_pct: float                   # aligned / covered_assets
    eligible_pct: float


@dataclass
class GARKPIBreakdown:
    """GAR by KPI type (Turnover / CapEx / OpEx)."""
    kpi_type: str                        # TURNOVER, CAPEX, OPEX
    aligned_amount: float
    eligible_amount: float
    covered_assets: float
    gar_ratio: float                     # aligned / covered


@dataclass
class GARAssetTypeBreakdown:
    """GAR breakdown by asset/exposure type."""
    asset_type: str
    total_amount: float
    aligned_amount: float
    eligible_amount: float
    alignment_ratio: float
    count: int


@dataclass
class GARResult:
    """Complete GAR calculation result."""
    # Headline GAR
    gar_ratio: float                     # Main: aligned / covered
    gar_eligible_ratio: float            # Eligible / covered
    gar_flow: float                      # GAR for new originations (if flow provided)

    # Amounts
    total_assets: float
    excluded_assets: float
    covered_assets: float                # Denominator
    aligned_assets: float                # Numerator
    eligible_assets: float
    not_eligible_assets: float

    # Breakdowns
    by_objective: List[GARObjectiveBreakdown]
    by_kpi_type: List[GARKPIBreakdown]
    by_asset_type: List[GARAssetTypeBreakdown]

    # Data quality
    assessed_pct: float
    not_assessed_count: int
    exposure_count: int

    methodology_notes: List[str]


# ---------------------------------------------------------------------------
# EPC ALIGNMENT (Residential mortgages)
# ---------------------------------------------------------------------------

EPC_ALIGNMENT_MAP: Dict[str, str] = {
    "A": "TAXONOMY_ALIGNED",
    "B": "TAXONOMY_ELIGIBLE",
    "C": "TAXONOMY_ELIGIBLE",
    "D": "NOT_ELIGIBLE",
    "E": "NOT_ELIGIBLE",
    "F": "NOT_ELIGIBLE",
    "G": "NOT_ELIGIBLE",
}

OBJECTIVE_LABELS: Dict[str, str] = {
    "CLIMATE_MITIGATION": "Climate change mitigation (Art. 10)",
    "CLIMATE_ADAPTATION": "Climate change adaptation (Art. 11)",
    "WATER": "Sustainable use of water and marine resources (Art. 12)",
    "CIRCULAR_ECONOMY": "Transition to a circular economy (Art. 13)",
    "POLLUTION": "Pollution prevention and control (Art. 14)",
    "BIODIVERSITY": "Protection of biodiversity and ecosystems (Art. 15)",
}


# ---------------------------------------------------------------------------
# UTILITY FUNCTION
# ---------------------------------------------------------------------------


def get_eligible_objectives(nace_code: str) -> List[str]:
    """
    Return list of eligible EU Taxonomy environmental objectives for a NACE code.

    Args:
        nace_code: NACE Rev. 2 activity code (e.g. "D35.11")

    Returns:
        List of objective codes (e.g. ["CLIMATE_MITIGATION", "CLIMATE_ADAPTATION"]).
        Empty list if the NACE code is not mapped.
    """
    return list(NACE_TAXONOMY_MAP.get(nace_code, []))


# ---------------------------------------------------------------------------
# MAIN CALCULATOR CLASS
# ---------------------------------------------------------------------------


class GARCalculator:
    """
    Green Asset Ratio calculator per CRR Art. 449a / EU Taxonomy.

    Processes a bank's loan book and calculates:
      1. GAR stock: aligned assets / covered assets
      2. GAR flow: aligned new originations / total new originations
      3. Breakdown by EU Taxonomy environmental objective
      4. Breakdown by KPI type (Turnover, CapEx, OpEx)
      5. Breakdown by asset/exposure type
      6. Data quality metrics (% assessed)

    Excluded from denominator:
      SOVEREIGN, CENTRAL_BANK, INTERBANK, HEDGING_DERIVATIVE
    """

    def __init__(self) -> None:
        """Initialize GAR calculator."""
        pass

    def calculate(
        self,
        exposures: List[GARExposure],
        flow_exposures: Optional[List[GARExposure]] = None,
    ) -> GARResult:
        """
        Calculate Green Asset Ratio from a set of exposures.

        Args:
            exposures: All on-balance-sheet exposures (stock).
            flow_exposures: New originations in period (flow), optional.

        Returns:
            GARResult with full breakdown.
        """
        notes: List[str] = []

        # --- 1. Classify and aggregate ---
        total_assets = 0.0
        excluded_assets = 0.0
        covered_assets = 0.0
        aligned_assets = 0.0
        eligible_assets = 0.0
        not_eligible_assets = 0.0
        not_assessed_count = 0

        # Objective tracking
        obj_aligned: Dict[str, float] = {o.value: 0.0 for o in TaxonomyObjective}
        obj_eligible: Dict[str, float] = {o.value: 0.0 for o in TaxonomyObjective}
        obj_not_eligible: Dict[str, float] = {o.value: 0.0 for o in TaxonomyObjective}

        # KPI type tracking
        kpi_aligned: Dict[str, float] = {"TURNOVER": 0.0, "CAPEX": 0.0, "OPEX": 0.0}
        kpi_eligible: Dict[str, float] = {"TURNOVER": 0.0, "CAPEX": 0.0, "OPEX": 0.0}

        # Asset type tracking
        type_totals: Dict[str, float] = {}
        type_aligned: Dict[str, float] = {}
        type_eligible: Dict[str, float] = {}
        type_counts: Dict[str, int] = {}

        for exp in exposures:
            amount = exp.gross_carrying_amount
            total_assets += amount

            # Check if excluded from GAR denominator
            if exp.asset_type in EXCLUDED_ASSET_TYPES:
                excluded_assets += amount
                continue

            # Covered asset (in denominator)
            covered_assets += amount
            at = exp.asset_type
            type_totals[at] = type_totals.get(at, 0.0) + amount
            type_counts[at] = type_counts.get(at, 0) + 1

            # Determine alignment via classification or auto-assess household
            classification = self._resolve_classification(exp)

            if classification == AlignmentClassification.TAXONOMY_ALIGNED.value:
                aligned_amt = amount
                eligible_amt = amount
                aligned_assets += aligned_amt
                eligible_assets += eligible_amt
            elif classification == AlignmentClassification.TAXONOMY_ELIGIBLE.value:
                aligned_amt = 0.0
                eligible_amt = amount
                eligible_assets += eligible_amt
            else:
                aligned_amt = 0.0
                eligible_amt = 0.0
                not_eligible_assets += amount

            type_aligned[at] = type_aligned.get(at, 0.0) + aligned_amt
            type_eligible[at] = type_eligible.get(at, 0.0) + eligible_amt

            # Track by objective
            if aligned_amt > 0 and exp.primary_objective:
                obj = exp.primary_objective
                obj_aligned[obj] = obj_aligned.get(obj, 0.0) + aligned_amt
                obj_eligible[obj] = obj_eligible.get(obj, 0.0) + eligible_amt
                for sec in exp.secondary_objectives:
                    if sec in obj_aligned:
                        obj_aligned[sec] = obj_aligned.get(sec, 0.0) + aligned_amt
            elif eligible_amt > 0 and exp.primary_objective:
                obj = exp.primary_objective
                obj_eligible[obj] = obj_eligible.get(obj, 0.0) + eligible_amt

            # KPI type aggregation
            kpi_aligned["TURNOVER"] += exp.turnover_aligned
            kpi_eligible["TURNOVER"] += exp.turnover_eligible
            kpi_aligned["CAPEX"] += exp.capex_aligned
            kpi_eligible["CAPEX"] += exp.capex_eligible
            kpi_aligned["OPEX"] += exp.opex_aligned
            kpi_eligible["OPEX"] += exp.opex_eligible

        # --- 2. Calculate ratios ---
        gar_ratio = aligned_assets / covered_assets if covered_assets > 0 else 0.0
        gar_eligible_ratio = eligible_assets / covered_assets if covered_assets > 0 else 0.0
        assessed_pct = (
            1.0 - (not_assessed_count / len(exposures))
            if len(exposures) > 0
            else 0.0
        )

        notes.append(f"Total assets: {total_assets:,.0f}")
        notes.append(f"Excluded assets: {excluded_assets:,.0f}")
        notes.append(f"Covered assets (denominator): {covered_assets:,.0f}")
        notes.append(f"Aligned assets (numerator): {aligned_assets:,.0f}")
        notes.append(f"GAR = {gar_ratio:.4%}")

        # --- 3. Flow GAR ---
        gar_flow = 0.0
        if flow_exposures:
            flow_covered = 0.0
            flow_aligned = 0.0
            for exp in flow_exposures:
                if exp.asset_type not in EXCLUDED_ASSET_TYPES:
                    flow_covered += exp.gross_carrying_amount
                    cls = self._resolve_classification(exp)
                    if cls == AlignmentClassification.TAXONOMY_ALIGNED.value:
                        flow_aligned += exp.gross_carrying_amount
            gar_flow = flow_aligned / flow_covered if flow_covered > 0 else 0.0
            notes.append(f"Flow GAR: {gar_flow:.4%} (new originations)")

        # --- 4. Objective breakdown ---
        by_objective: List[GARObjectiveBreakdown] = []
        for obj in TaxonomyObjective:
            ov = obj.value
            a = obj_aligned.get(ov, 0.0)
            e = obj_eligible.get(ov, 0.0)
            ne = max(covered_assets - e, 0.0)
            by_objective.append(
                GARObjectiveBreakdown(
                    objective=ov,
                    objective_label=OBJECTIVE_LABELS.get(ov, ov),
                    aligned_amount=round(a, 2),
                    eligible_amount=round(e, 2),
                    not_eligible_amount=round(ne, 2),
                    aligned_pct=round(a / covered_assets * 100, 2) if covered_assets > 0 else 0.0,
                    eligible_pct=round(e / covered_assets * 100, 2) if covered_assets > 0 else 0.0,
                )
            )

        # --- 5. KPI type breakdown ---
        by_kpi_type: List[GARKPIBreakdown] = []
        for kpi in KPIType:
            kv = kpi.value
            a = kpi_aligned.get(kv, 0.0)
            e = kpi_eligible.get(kv, 0.0)
            by_kpi_type.append(
                GARKPIBreakdown(
                    kpi_type=kv,
                    aligned_amount=round(a, 2),
                    eligible_amount=round(e, 2),
                    covered_assets=round(covered_assets, 2),
                    gar_ratio=round(a / covered_assets, 6) if covered_assets > 0 else 0.0,
                )
            )

        # --- 6. Asset type breakdown ---
        by_asset_type: List[GARAssetTypeBreakdown] = []
        for at, total in type_totals.items():
            a = type_aligned.get(at, 0.0)
            e = type_eligible.get(at, 0.0)
            by_asset_type.append(
                GARAssetTypeBreakdown(
                    asset_type=at,
                    total_amount=round(total, 2),
                    aligned_amount=round(a, 2),
                    eligible_amount=round(e, 2),
                    alignment_ratio=round(a / total, 4) if total > 0 else 0.0,
                    count=type_counts.get(at, 0),
                )
            )

        return GARResult(
            gar_ratio=round(gar_ratio, 6),
            gar_eligible_ratio=round(gar_eligible_ratio, 6),
            gar_flow=round(gar_flow, 6),
            total_assets=round(total_assets, 2),
            excluded_assets=round(excluded_assets, 2),
            covered_assets=round(covered_assets, 2),
            aligned_assets=round(aligned_assets, 2),
            eligible_assets=round(eligible_assets, 2),
            not_eligible_assets=round(not_eligible_assets, 2),
            by_objective=by_objective,
            by_kpi_type=by_kpi_type,
            by_asset_type=by_asset_type,
            assessed_pct=round(assessed_pct, 4),
            not_assessed_count=not_assessed_count,
            exposure_count=len([e for e in exposures if e.asset_type not in EXCLUDED_ASSET_TYPES]),
            methodology_notes=notes,
        )

    # -----------------------------------------------------------------------
    # CLASSIFICATION RESOLUTION
    # -----------------------------------------------------------------------

    def _resolve_classification(self, exp: GARExposure) -> str:
        """
        Resolve the taxonomy classification for an exposure.

        If a classification is explicitly provided and is not NOT_ELIGIBLE,
        use it.  Otherwise, auto-assess household exposures (mortgages,
        auto loans, renovation loans) using EPC / EV / renovation flags.

        Returns:
            AlignmentClassification value string.
        """
        # Explicitly classified
        if exp.classification in (
            AlignmentClassification.TAXONOMY_ALIGNED.value,
            AlignmentClassification.TAXONOMY_ELIGIBLE.value,
            AlignmentClassification.NOT_ELIGIBLE.value,
        ):
            return exp.classification

        # Auto-assess household mortgages by EPC
        if exp.asset_type == "HOUSEHOLD_MORTGAGE" and exp.epc_rating:
            epc = exp.epc_rating.upper()
            return EPC_ALIGNMENT_MAP.get(epc, "NOT_ELIGIBLE")

        # Auto-assess EV loans
        if exp.asset_type == "HOUSEHOLD_AUTO" and exp.is_ev_loan:
            return AlignmentClassification.TAXONOMY_ALIGNED.value

        # Auto-assess renovation loans
        if exp.asset_type == "HOUSEHOLD_RENOVATION" and exp.is_renovation_loan:
            return AlignmentClassification.TAXONOMY_ALIGNED.value

        # NACE-based eligibility check
        if exp.nace_code and exp.nace_code in NACE_TAXONOMY_MAP:
            return AlignmentClassification.TAXONOMY_ELIGIBLE.value

        return AlignmentClassification.NOT_ELIGIBLE.value

    # -----------------------------------------------------------------------
    # STATIC UTILITY METHODS
    # -----------------------------------------------------------------------

    @staticmethod
    def get_taxonomy_objectives() -> List[Dict[str, str]]:
        """Return the 6 EU Taxonomy environmental objectives."""
        return [
            {"code": obj.value, "description": OBJECTIVE_LABELS.get(obj.value, "")}
            for obj in TaxonomyObjective
        ]

    @staticmethod
    def get_excluded_asset_types() -> List[str]:
        """Return asset types excluded from the GAR denominator."""
        return sorted(EXCLUDED_ASSET_TYPES)

    @staticmethod
    def get_nace_taxonomy_map() -> Dict[str, List[str]]:
        """Return NACE code to taxonomy objective mapping."""
        return {k: list(v) for k, v in NACE_TAXONOMY_MAP.items()}

    @staticmethod
    def get_kpi_types() -> List[Dict[str, str]]:
        """Return CRR2 ITS KPI types."""
        return [
            {"code": "TURNOVER", "description": "Revenue / turnover-based alignment"},
            {"code": "CAPEX", "description": "Capital expenditure-based alignment"},
            {"code": "OPEX", "description": "Operating expenditure-based alignment"},
        ]

    @staticmethod
    def get_alignment_classifications() -> List[Dict[str, str]]:
        """Return possible alignment classification values."""
        return [
            {"code": "TAXONOMY_ALIGNED", "description": "Meets SC, DNSH, and MSS criteria"},
            {"code": "TAXONOMY_ELIGIBLE", "description": "Eligible activity but not fully aligned"},
            {"code": "NOT_ELIGIBLE", "description": "Not a taxonomy-eligible economic activity"},
        ]
