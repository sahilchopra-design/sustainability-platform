"""
NACE-CPRS-IAM Sector Classification Mapper
=============================================
Maps NACE Rev.2 codes to Climate Policy Relevant Sectors (CPRS) and
Integrated Assessment Model (IAM) sectors for transition risk analysis.

References:
  - Battiston et al. (2017) "A climate stress-test of the financial system"
  - EBA Pilot Exercise on Climate Risk (2021)
  - NACE-CPRS-IAM mapping: Monasterolo et al. (2022)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field as dc_field
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Embedded Reference Data
# ---------------------------------------------------------------------------

CPRS_CATEGORIES: dict[str, dict] = {
    "Fossil Fuel": {
        "risk_weight": 1.0,
        "description": "Extraction, processing, and distribution of fossil fuels (coal, oil, gas).",
    },
    "Utility": {
        "risk_weight": 0.8,
        "description": "Electric power generation, gas distribution, steam and AC supply.",
    },
    "Energy-Intensive": {
        "risk_weight": 0.7,
        "description": "Heavy industry: chemicals, non-metallic minerals, basic metals, paper/pulp.",
    },
    "Housing": {
        "risk_weight": 0.4,
        "description": "Construction, real estate activities, and building materials.",
    },
    "Transport": {
        "risk_weight": 0.6,
        "description": "Land, water, and air transport; warehousing and logistics.",
    },
    "Agriculture": {
        "risk_weight": 0.5,
        "description": "Crop production, forestry, fishing, and food processing.",
    },
    "Finance (indirect)": {
        "risk_weight": 0.3,
        "description": "Banking, insurance, pension funds -- indirect exposure via financed emissions.",
    },
    "Other": {
        "risk_weight": 0.15,
        "description": "Low climate-policy sensitivity sectors (services, ICT, health, education, etc.).",
    },
}

# ---------------------------------------------------------------------------
# NACE Rev.2 -> CPRS mapping  (~85 entries)
# Keys are 2-digit divisions or 4-digit classes (with dot).
# Lookup order: 4-digit first, then 2-digit prefix, then "Other".
# ---------------------------------------------------------------------------

NACE_TO_CPRS: dict[str, str] = {
    # ---- Fossil Fuel ----
    "05": "Fossil Fuel",       # Mining of coal and lignite
    "06": "Fossil Fuel",       # Extraction of crude petroleum and natural gas
    "06.10": "Fossil Fuel",    # Extraction of crude petroleum
    "06.20": "Fossil Fuel",    # Extraction of natural gas
    "07": "Fossil Fuel",       # Mining of metal ores (upstream supply chain)
    "08": "Fossil Fuel",       # Other mining and quarrying
    "09": "Fossil Fuel",       # Mining support service activities
    "09.10": "Fossil Fuel",    # Support activities for petroleum/gas extraction
    "19": "Fossil Fuel",       # Manufacture of coke and refined petroleum products
    "19.10": "Fossil Fuel",    # Manufacture of coke oven products
    "19.20": "Fossil Fuel",    # Manufacture of refined petroleum products
    # ---- Utility ----
    "35": "Utility",           # Electricity, gas, steam and AC supply
    "35.1": "Utility",         # Electric power generation, transmission, distribution
    "35.11": "Utility",        # Production of electricity
    "35.12": "Utility",        # Transmission of electricity
    "35.13": "Utility",        # Distribution of electricity
    "35.14": "Utility",        # Trade of electricity
    "35.2": "Utility",         # Manufacture of gas; distribution of gaseous fuels
    "35.21": "Utility",        # Manufacture of gas
    "35.22": "Utility",        # Distribution of gaseous fuels through mains
    "35.23": "Utility",        # Trade of gas through mains
    "35.3": "Utility",         # Steam and air conditioning supply
    "35.30": "Utility",        # Steam and air conditioning supply
    "36": "Utility",           # Water collection, treatment and supply
    "37": "Utility",           # Sewerage
    "38": "Utility",           # Waste collection, treatment and disposal
    "39": "Utility",           # Remediation activities
    # ---- Energy-Intensive ----
    "17": "Energy-Intensive",  # Manufacture of paper and paper products
    "20": "Energy-Intensive",  # Manufacture of chemicals
    "20.11": "Energy-Intensive",
    "20.13": "Energy-Intensive",
    "20.14": "Energy-Intensive",
    "20.15": "Energy-Intensive",
    "20.16": "Energy-Intensive",
    "23": "Energy-Intensive",  # Manufacture of other non-metallic mineral products
    "23.11": "Energy-Intensive",  # Flat glass
    "23.13": "Energy-Intensive",  # Hollow glass
    "23.51": "Energy-Intensive",  # Cement
    "23.52": "Energy-Intensive",  # Lime and plaster
    "24": "Energy-Intensive",  # Manufacture of basic metals
    "24.10": "Energy-Intensive",  # Basic iron/steel
    "24.42": "Energy-Intensive",  # Aluminium production
    "24.43": "Energy-Intensive",  # Lead, zinc, tin production
    "25": "Energy-Intensive",  # Fabricated metal products
    # ---- Housing ----
    "41": "Housing",           # Construction of buildings
    "42": "Housing",           # Civil engineering
    "43": "Housing",           # Specialised construction activities
    "68": "Housing",           # Real estate activities
    "68.10": "Housing",        # Buying and selling of own real estate
    "68.20": "Housing",        # Renting and operating of own real estate
    "68.31": "Housing",        # Real estate agencies
    "68.32": "Housing",        # Management of real estate on a fee basis
    "16": "Housing",           # Manufacture of wood products (building materials)
    # ---- Transport ----
    "49": "Transport",         # Land transport and transport via pipelines
    "49.10": "Transport",      # Passenger rail transport
    "49.20": "Transport",      # Freight rail transport
    "49.31": "Transport",      # Urban/suburban passenger land transport
    "49.39": "Transport",      # Other passenger land transport
    "49.41": "Transport",      # Freight transport by road
    "49.50": "Transport",      # Transport via pipeline
    "50": "Transport",         # Water transport
    "50.10": "Transport",      # Sea and coastal passenger water transport
    "50.20": "Transport",      # Sea and coastal freight water transport
    "51": "Transport",         # Air transport
    "51.10": "Transport",      # Passenger air transport
    "51.21": "Transport",      # Freight air transport
    "52": "Transport",         # Warehousing and support activities for transportation
    "29": "Transport",         # Manufacture of motor vehicles
    "30": "Transport",         # Manufacture of other transport equipment
    # ---- Agriculture ----
    "01": "Agriculture",       # Crop and animal production
    "01.11": "Agriculture",    # Growing of cereals
    "01.41": "Agriculture",    # Raising of dairy cattle
    "01.46": "Agriculture",    # Raising of swine/pigs
    "01.47": "Agriculture",    # Raising of poultry
    "02": "Agriculture",       # Forestry and logging
    "03": "Agriculture",       # Fishing and aquaculture
    "10": "Agriculture",       # Manufacture of food products
    "11": "Agriculture",       # Manufacture of beverages
    "12": "Agriculture",       # Manufacture of tobacco products
    # ---- Finance (indirect) ----
    "64": "Finance (indirect)",  # Financial service activities
    "64.11": "Finance (indirect)",  # Central banking
    "64.19": "Finance (indirect)",  # Other monetary intermediation
    "65": "Finance (indirect)",  # Insurance, reinsurance, pension funding
    "66": "Finance (indirect)",  # Activities auxiliary to financial services
    # ---- Other (explicit overrides for clarity) ----
    "58": "Other",             # Publishing activities
    "61": "Other",             # Telecommunications
    "62": "Other",             # Computer programming
    "63": "Other",             # Information service activities
    "69": "Other",             # Legal and accounting
    "70": "Other",             # Head offices; management consultancy
    "72": "Other",             # Scientific research
    "75": "Other",             # Veterinary activities
    "85": "Other",             # Education
    "86": "Other",             # Human health activities
    "87": "Other",             # Residential care activities
}

# ---------------------------------------------------------------------------
# CPRS -> IAM sector mapping
# ---------------------------------------------------------------------------

CPRS_TO_IAM: dict[str, list[str]] = {
    "Fossil Fuel": ["Extraction", "Refining"],
    "Utility": ["Electricity", "Heat"],
    "Energy-Intensive": ["Industry"],
    "Housing": ["Buildings", "Construction"],
    "Transport": ["Transport"],
    "Agriculture": ["Agriculture", "Land Use"],
    "Finance (indirect)": ["Finance"],
    "Other": ["Services"],
}

# ---------------------------------------------------------------------------
# GHG Intensity Buckets (tCO2e per EUR million revenue)
# ---------------------------------------------------------------------------

GHG_INTENSITY_BUCKETS: list[tuple[str, float]] = [
    ("Very High", 1000.0),
    ("High", 500.0),
    ("Medium", 100.0),
    ("Low", 20.0),
]
# Anything <= 20 is "Very Low"

# ---------------------------------------------------------------------------
# Result Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class SectorClassification:
    """Classification result for a single NACE code."""
    nace_code: str
    nace_description: str
    cprs_category: str
    cprs_risk_weight: float
    iam_sectors: list[str]
    ghg_intensity_bucket: str


@dataclass
class CounterpartySectorScore:
    """Aggregated sector risk profile for a counterparty with one or more activities."""
    entity_name: str
    primary_nace: str
    classifications: list[SectorClassification]
    sector_risk_score: float
    dominant_cprs_category: str
    ghg_bucket: str
    multi_activity: bool


# ---------------------------------------------------------------------------
# Mapper
# ---------------------------------------------------------------------------


class NACECPRSMapper:
    """Maps NACE Rev.2 codes to CPRS categories, IAM sectors, and GHG buckets."""

    def __init__(
        self,
        cprs_risk_weight_overrides: Optional[dict[str, float]] = None,
        nace_overrides: Optional[dict[str, str]] = None,
    ) -> None:
        self._cprs = dict(CPRS_CATEGORIES)
        self._nace_map = dict(NACE_TO_CPRS)

        if cprs_risk_weight_overrides:
            for cat, weight in cprs_risk_weight_overrides.items():
                if cat in self._cprs:
                    self._cprs[cat]["risk_weight"] = max(0.0, min(1.0, weight))
                    logger.info("CPRS risk weight override: %s -> %.2f", cat, weight)

        if nace_overrides:
            self._nace_map.update(nace_overrides)
            logger.info("Applied %d NACE mapping overrides", len(nace_overrides))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def classify_nace(
        self,
        nace_code: str,
        nace_description: str = "",
        ghg_intensity_tco2e_per_eur_m: Optional[float] = None,
    ) -> SectorClassification:
        """Map a single NACE code to its CPRS category, IAM sectors, and GHG bucket.

        Lookup precedence: exact match -> 4-digit prefix -> 2-digit division -> "Other".
        """
        code = nace_code.strip()
        cprs_cat = self._resolve_cprs(code)
        risk_weight = self._cprs[cprs_cat]["risk_weight"]
        iam_sectors = CPRS_TO_IAM.get(cprs_cat, ["Services"])
        ghg_bucket = (
            self.classify_ghg_intensity(ghg_intensity_tco2e_per_eur_m)
            if ghg_intensity_tco2e_per_eur_m is not None
            else "N/A"
        )

        return SectorClassification(
            nace_code=code,
            nace_description=nace_description,
            cprs_category=cprs_cat,
            cprs_risk_weight=risk_weight,
            iam_sectors=iam_sectors,
            ghg_intensity_bucket=ghg_bucket,
        )

    def score_counterparty(
        self,
        entity_name: str,
        activities: list[dict],
    ) -> CounterpartySectorScore:
        """Compute revenue-weighted sector risk score for a counterparty.

        Parameters
        ----------
        entity_name : str
            Legal name of the counterparty.
        activities : list[dict]
            Each dict must contain ``nace_code`` (str) and ``revenue_share`` (float 0-1).
            Optional keys: ``nace_description``, ``ghg_intensity_tco2e_per_eur_m``.

        Returns
        -------
        CounterpartySectorScore
        """
        if not activities:
            raise ValueError("activities list must not be empty")

        classifications: list[SectorClassification] = []
        weighted_score = 0.0
        total_weight = 0.0
        weighted_ghg: float | None = None
        cprs_weight_accum: dict[str, float] = {}

        for act in activities:
            nace_code = act["nace_code"]
            revenue_share = float(act.get("revenue_share", 1.0 / len(activities)))
            nace_desc = act.get("nace_description", "")
            ghg_intensity = act.get("ghg_intensity_tco2e_per_eur_m")

            cls = self.classify_nace(nace_code, nace_desc, ghg_intensity)
            classifications.append(cls)

            weighted_score += revenue_share * cls.cprs_risk_weight
            total_weight += revenue_share
            cprs_weight_accum[cls.cprs_category] = (
                cprs_weight_accum.get(cls.cprs_category, 0.0) + revenue_share
            )

            if ghg_intensity is not None:
                if weighted_ghg is None:
                    weighted_ghg = 0.0
                weighted_ghg += revenue_share * ghg_intensity

        # Normalise in case revenue shares do not sum to 1
        sector_risk_score = weighted_score / total_weight if total_weight > 0 else 0.0

        dominant_cprs = max(cprs_weight_accum, key=cprs_weight_accum.get)
        primary_nace = activities[0]["nace_code"]

        ghg_bucket = (
            self.classify_ghg_intensity(weighted_ghg / total_weight)
            if weighted_ghg is not None and total_weight > 0
            else "N/A"
        )

        return CounterpartySectorScore(
            entity_name=entity_name,
            primary_nace=primary_nace,
            classifications=classifications,
            sector_risk_score=round(sector_risk_score, 4),
            dominant_cprs_category=dominant_cprs,
            ghg_bucket=ghg_bucket,
            multi_activity=len(activities) > 1,
        )

    @staticmethod
    def classify_ghg_intensity(tco2e_per_eur_m: float) -> str:
        """Return the GHG intensity bucket name for the given value.

        Thresholds (tCO2e / EUR million revenue):
          Very High > 1000, High > 500, Medium > 100, Low > 20, Very Low <= 20
        """
        for label, threshold in GHG_INTENSITY_BUCKETS:
            if tco2e_per_eur_m > threshold:
                return label
        return "Very Low"

    def get_all_cprs_categories(self) -> dict[str, dict]:
        """Return the full CPRS category table with risk weights and descriptions."""
        return {k: dict(v) for k, v in self._cprs.items()}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_cprs(self, code: str) -> str:
        """Resolve NACE code to CPRS category with cascading lookup."""
        # Exact match (e.g. "06.10" or "35")
        if code in self._nace_map:
            return self._nace_map[code]

        # Try stripping to 4-digit with dot (e.g. "06.10" from "06.10.1")
        if len(code) > 5 and "." in code:
            prefix4 = code[:5]
            if prefix4 in self._nace_map:
                return self._nace_map[prefix4]

        # Try 3-char key (e.g. "35.1")
        if len(code) >= 4 and "." in code:
            prefix3 = code[:4]
            if prefix3 in self._nace_map:
                return self._nace_map[prefix3]

        # 2-digit division
        div = code[:2]
        if div in self._nace_map:
            return self._nace_map[div]

        logger.debug("NACE code '%s' not mapped -- defaulting to 'Other'", code)
        return "Other"
