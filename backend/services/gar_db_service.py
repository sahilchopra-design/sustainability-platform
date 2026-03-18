"""
GAR Database Service — Auto-calculate Green Asset Ratio from DB data.

Pulls from:
  - eu_taxonomy_assessments  (entity-level KPIs: turnover/capex/opex alignment %)
  - eu_taxonomy_activities   (per-activity SC/DNSH/MSS flags, NACE codes, amounts)
  - fi_loan_books            (sector breakdown with EAD amounts)
  - fi_eu_taxonomy_kpis      (stores computed GAR results)

Workflow:
  1. For a given entity_id or LEI, gather all taxonomy assessments + loan book data
  2. Transform loan book sectors into GARExposure objects using activity-level alignment
  3. Run GARCalculator.calculate()
  4. Persist results to fi_eu_taxonomy_kpis
  5. Return full GARResult

Author: GAR DB Service
Version: 1.0.0
Date: 2026-03-08
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.engine import Engine

from services.gar_calculator import (
    GARCalculator,
    GARExposure,
    GARResult,
    NACE_TAXONOMY_MAP,
    EXCLUDED_ASSET_TYPES,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# NACE → Asset type mapping (simplified for loan book sectors)
# ---------------------------------------------------------------------------

_NACE_TO_ASSET_TYPE: Dict[str, str] = {
    "A": "NFC_LOAN",       # Agriculture
    "B": "NFC_LOAN",       # Mining
    "C": "NFC_LOAN",       # Manufacturing
    "D": "NFC_LOAN",       # Electricity/gas
    "E": "NFC_LOAN",       # Water/waste
    "F": "NFC_LOAN",       # Construction
    "G": "NFC_LOAN",       # Wholesale/retail
    "H": "NFC_LOAN",       # Transport
    "I": "NFC_LOAN",       # Accommodation
    "J": "NFC_LOAN",       # Information/comms
    "K": "INTERBANK",      # Financial services (excluded from GAR)
    "L": "NFC_LOAN",       # Real estate
    "M": "NFC_LOAN",       # Professional services
    "N": "NFC_LOAN",       # Administrative
    "O": "SOVEREIGN",      # Public admin (excluded from GAR)
    "P": "NFC_LOAN",       # Education
    "Q": "NFC_LOAN",       # Health/social
    "R": "NFC_LOAN",       # Arts/entertainment
    "S": "NFC_LOAN",       # Other services
}

# Sector name → NACE section letter (best-effort mapping from GICS-like names)
_SECTOR_NAME_TO_NACE: Dict[str, str] = {
    "real_estate_commercial": "L",
    "real_estate_residential": "L",
    "energy_oil_gas": "B",
    "energy_renewables": "D",
    "utilities": "D",
    "chemicals": "C",
    "manufacturing": "C",
    "transport": "H",
    "construction": "F",
    "agriculture": "A",
    "technology": "J",
    "financial_services": "K",
    "government": "O",
    "healthcare": "Q",
    "retail": "G",
}

# SC objective number → objective code
_OBJ_MAP = {
    1: "CLIMATE_MITIGATION",
    2: "CLIMATE_ADAPTATION",
    3: "WATER",
    4: "CIRCULAR_ECONOMY",
    5: "POLLUTION",
    6: "BIODIVERSITY",
}


class GARDBService:
    """
    Auto-calculate GAR from database data for a financial institution entity.

    Uses eu_taxonomy_assessments + eu_taxonomy_activities for activity-level
    alignment data, and fi_loan_books for exposure amounts.
    """

    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._calc = GARCalculator()

    # -------------------------------------------------------------------
    # PUBLIC API
    # -------------------------------------------------------------------

    def calculate_gar_for_entity(
        self,
        entity_id: str,
        reporting_year: int = 2024,
        persist: bool = True,
    ) -> Dict[str, Any]:
        """
        Auto-calculate GAR for an FI entity from DB data.

        Args:
            entity_id: UUID of fi_entities row.
            reporting_year: Reporting year to filter assessments.
            persist: If True, write results to fi_eu_taxonomy_kpis.

        Returns:
            Dict with GAR results + metadata.
        """
        with self._engine.connect() as conn:
            # 1. Get entity info
            entity = self._get_entity(conn, entity_id)
            if not entity:
                return {"error": f"Entity {entity_id} not found in fi_entities"}

            # 2. Get taxonomy assessment for this entity's regulatory counterpart
            assessment, activities = self._get_taxonomy_data(
                conn, entity["legal_name"], reporting_year
            )

            # 3. Get loan book for exposure amounts
            loan_book = self._get_loan_book(conn, entity_id, reporting_year)

            # 4. Build GARExposure list
            exposures = self._build_exposures(
                entity, assessment, activities, loan_book
            )

            if not exposures:
                return {
                    "error": "No exposures could be assembled",
                    "entity_name": entity.get("legal_name", ""),
                    "detail": "Need eu_taxonomy_activities or fi_loan_books data",
                }

            # 5. Run calculator
            result = self._calc.calculate(exposures)

            # 6. Persist
            if persist:
                self._persist_result(conn, entity_id, reporting_year, result, assessment)
                conn.commit()

            # 7. Serialise
            return self._serialise(result, entity, reporting_year, len(activities))

    def calculate_gar_by_lei(
        self,
        lei: str,
        reporting_year: int = 2024,
        persist: bool = True,
    ) -> Dict[str, Any]:
        """
        Auto-calculate GAR by LEI (resolves to fi_entities + regulatory_entities).
        """
        with self._engine.connect() as conn:
            row = conn.execute(
                text("SELECT id FROM fi_entities WHERE lei = :lei LIMIT 1"),
                {"lei": lei},
            ).mappings().first()

            if not row:
                return {"error": f"No fi_entity found with LEI {lei}"}

            return self.calculate_gar_for_entity(
                entity_id=str(row["id"]),
                reporting_year=reporting_year,
                persist=persist,
            )

    # -------------------------------------------------------------------
    # DATA RETRIEVAL
    # -------------------------------------------------------------------

    def _get_entity(self, conn, entity_id: str) -> Optional[Dict]:
        try:
            row = conn.execute(
                text("""
                    SELECT id, legal_name, lei, institution_type, total_assets_meur
                    FROM fi_entities
                    WHERE id = :eid
                """),
                {"eid": entity_id},
            ).mappings().first()
            return dict(row) if row else None
        except Exception as e:
            logger.warning("fi_entities query failed: %s", e)
            return None

    def _get_taxonomy_data(
        self, conn, entity_name: str, year: int
    ) -> Tuple[Optional[Dict], List[Dict]]:
        """Get taxonomy assessment + activities for entity (matched by name)."""
        assessment = None
        activities: List[Dict] = []

        try:
            arow = conn.execute(
                text("""
                    SELECT *
                    FROM eu_taxonomy_assessments
                    WHERE entity_name ILIKE :name
                      AND reporting_year = :yr
                    ORDER BY updated_at DESC NULLS LAST
                    LIMIT 1
                """),
                {"name": f"%{entity_name[:50]}%", "yr": year},
            ).mappings().first()

            if arow:
                assessment = dict(arow)
                # Get activities
                acts = conn.execute(
                    text("""
                        SELECT *
                        FROM eu_taxonomy_activities
                        WHERE assessment_id = :aid
                        ORDER BY activity_code
                    """),
                    {"aid": assessment["id"]},
                ).mappings().all()
                activities = [dict(a) for a in acts]
        except Exception as e:
            logger.warning("Taxonomy assessment query failed: %s", e)

        return assessment, activities

    def _get_loan_book(
        self, conn, entity_id: str, year: int
    ) -> Optional[Dict]:
        """Get loan book sector breakdown."""
        try:
            row = conn.execute(
                text("""
                    SELECT *
                    FROM fi_loan_books
                    WHERE entity_id = :eid AND reporting_year = :yr
                    ORDER BY reporting_year DESC
                    LIMIT 1
                """),
                {"eid": entity_id, "yr": year},
            ).mappings().first()
            return dict(row) if row else None
        except Exception as e:
            logger.warning("fi_loan_books query failed: %s", e)
            return None

    # -------------------------------------------------------------------
    # EXPOSURE BUILDING
    # -------------------------------------------------------------------

    def _build_exposures(
        self,
        entity: Dict,
        assessment: Optional[Dict],
        activities: List[Dict],
        loan_book: Optional[Dict],
    ) -> List[GARExposure]:
        """
        Build GARExposure list from DB data.

        Strategy:
        1. If we have eu_taxonomy_activities, each activity becomes an exposure
           with its own alignment flags and amounts.
        2. If we have fi_loan_books sector_breakdown, each sector becomes an
           exposure. Alignment is inferred from taxonomy assessment KPIs.
        3. For denormalized loan book columns (real_estate_commercial_ead, etc.),
           create exposures from those.
        """
        exposures: List[GARExposure] = []
        entity_name = entity.get("legal_name", "Unknown")

        # --- Path A: Activity-level data (most granular) ---
        if activities:
            for act in activities:
                exp = self._activity_to_exposure(act, entity_name, assessment)
                if exp:
                    exposures.append(exp)

        # --- Path B: Loan book sector data ---
        if loan_book and not exposures:
            # Try JSONB sector_breakdown first
            sector_breakdown = loan_book.get("sector_breakdown")
            if sector_breakdown and isinstance(sector_breakdown, list):
                for sector_row in sector_breakdown:
                    exp = self._sector_to_exposure(
                        sector_row, entity_name, assessment
                    )
                    if exp:
                        exposures.append(exp)

            # Denormalized columns as fallback
            if not exposures:
                exposures.extend(
                    self._denormalized_loan_book_to_exposures(
                        loan_book, entity_name, assessment
                    )
                )

        return exposures

    def _activity_to_exposure(
        self,
        act: Dict,
        entity_name: str,
        assessment: Optional[Dict],
    ) -> Optional[GARExposure]:
        """Convert a single eu_taxonomy_activities row to GARExposure."""
        # Determine amounts (use turnover as primary, fallback to capex/opex)
        turnover = float(act.get("turnover_gbp") or 0)
        capex = float(act.get("capex_gbp") or 0)
        opex = float(act.get("opex_gbp") or 0)
        amount = turnover or capex or opex
        if amount <= 0:
            return None

        # NACE code
        nace_codes = act.get("nace_codes") or []
        primary_nace = ""
        if isinstance(nace_codes, list) and nace_codes:
            primary_nace = nace_codes[0].get("code", "") if isinstance(nace_codes[0], dict) else str(nace_codes[0])

        # Alignment classification
        is_aligned = act.get("is_aligned", False)
        is_eligible = act.get("is_eligible", False)
        if is_aligned:
            classification = "TAXONOMY_ALIGNED"
        elif is_eligible:
            classification = "TAXONOMY_ELIGIBLE"
        else:
            classification = "NOT_ELIGIBLE"

        # Primary objective
        sc_obj = act.get("sc_objective")
        primary_obj = _OBJ_MAP.get(sc_obj, "") if sc_obj else ""

        # Determine asset type from NACE
        nace_section = primary_nace[0] if primary_nace else ""
        asset_type = _NACE_TO_ASSET_TYPE.get(nace_section, "NFC_LOAN")

        # KPI-level aligned amounts
        turnover_aligned = turnover if is_aligned else 0.0
        turnover_eligible = turnover if is_eligible else 0.0
        capex_aligned = capex if is_aligned else 0.0
        capex_eligible = capex if is_eligible else 0.0
        opex_aligned = opex if is_aligned else 0.0
        opex_eligible = opex if is_eligible else 0.0

        return GARExposure(
            exposure_id=str(act.get("id", uuid.uuid4())),
            counterparty_name=entity_name,
            asset_type=asset_type,
            gross_carrying_amount=amount,
            classification=classification,
            primary_objective=primary_obj,
            nace_code=primary_nace,
            sector=act.get("sector", ""),
            turnover_aligned=turnover_aligned,
            turnover_eligible=turnover_eligible,
            capex_aligned=capex_aligned,
            capex_eligible=capex_eligible,
            opex_aligned=opex_aligned,
            opex_eligible=opex_eligible,
        )

    def _sector_to_exposure(
        self,
        sector_row: Dict,
        entity_name: str,
        assessment: Optional[Dict],
    ) -> Optional[GARExposure]:
        """Convert a loan book sector_breakdown JSONB entry to GARExposure."""
        ead = float(sector_row.get("ead_meur", 0)) * 1_000_000  # Convert MEUR to EUR
        if ead <= 0:
            return None

        nace_code = sector_row.get("sector_nace", "")
        sector_name = sector_row.get("sector_gics", "")

        # Determine asset type
        nace_section = nace_code[0] if nace_code else ""
        asset_type = _NACE_TO_ASSET_TYPE.get(nace_section, "NFC_LOAN")

        # Infer alignment from assessment-level KPIs if available
        classification = "NOT_ELIGIBLE"
        if nace_code and nace_code in NACE_TAXONOMY_MAP:
            classification = "TAXONOMY_ELIGIBLE"

        # If we have assessment-level aligned %, apply it proportionally
        aligned_pct = 0.0
        eligible_pct = 0.0
        if assessment:
            aligned_pct = float(assessment.get("taxonomy_aligned_turnover_pct") or 0) / 100
            eligible_pct = float(assessment.get("taxonomy_eligible_turnover_pct") or 0) / 100

        # For taxonomy-eligible sectors, use entity-level alignment rate
        if classification == "TAXONOMY_ELIGIBLE" and aligned_pct > 0:
            classification = "TAXONOMY_ALIGNED"

        return GARExposure(
            exposure_id=str(uuid.uuid4()),
            counterparty_name=entity_name,
            asset_type=asset_type,
            gross_carrying_amount=ead,
            classification=classification,
            nace_code=nace_code,
            sector=sector_name,
            turnover_aligned=ead * aligned_pct if classification != "NOT_ELIGIBLE" else 0,
            turnover_eligible=ead * eligible_pct if classification != "NOT_ELIGIBLE" else 0,
        )

    def _denormalized_loan_book_to_exposures(
        self,
        loan_book: Dict,
        entity_name: str,
        assessment: Optional[Dict],
    ) -> List[GARExposure]:
        """Build exposures from denormalized fi_loan_books columns."""
        exposures = []

        # Map of column → (sector_name, nace_section)
        _COLS = {
            "real_estate_commercial_ead": ("Real Estate Commercial", "L"),
            "real_estate_residential_ead": ("Real Estate Residential", "L"),
            "energy_oil_gas_ead": ("Oil & Gas", "B"),
            "energy_renewables_ead": ("Renewables", "D"),
            "utilities_ead": ("Utilities", "D"),
            "chemicals_ead": ("Chemicals", "C"),
            "manufacturing_ead": ("Manufacturing", "C"),
            "transport_ead": ("Transport", "H"),
            "construction_ead": ("Construction", "F"),
            "agriculture_ead": ("Agriculture", "A"),
            "technology_ead": ("Technology", "J"),
        }

        aligned_pct = 0.0
        if assessment:
            aligned_pct = float(assessment.get("taxonomy_aligned_turnover_pct") or 0) / 100

        for col, (sector_name, nace_sec) in _COLS.items():
            val = loan_book.get(col)
            if val is None:
                continue
            ead = float(val) * 1_000_000  # MEUR → EUR
            if ead <= 0:
                continue

            asset_type = _NACE_TO_ASSET_TYPE.get(nace_sec, "NFC_LOAN")

            # Check if any NACE code in this section is taxonomy-eligible
            has_eligible_nace = any(
                k.startswith(f"{nace_sec}") for k in NACE_TAXONOMY_MAP
            )
            classification = "TAXONOMY_ELIGIBLE" if has_eligible_nace else "NOT_ELIGIBLE"
            if classification == "TAXONOMY_ELIGIBLE" and aligned_pct > 0:
                classification = "TAXONOMY_ALIGNED"

            exposures.append(
                GARExposure(
                    exposure_id=str(uuid.uuid4()),
                    counterparty_name=entity_name,
                    asset_type=asset_type,
                    gross_carrying_amount=ead,
                    classification=classification,
                    sector=sector_name,
                    turnover_aligned=ead * aligned_pct if has_eligible_nace else 0,
                    turnover_eligible=ead * aligned_pct * 1.5 if has_eligible_nace else 0,
                )
            )

        return exposures

    # -------------------------------------------------------------------
    # PERSISTENCE
    # -------------------------------------------------------------------

    def _persist_result(
        self,
        conn,
        entity_id: str,
        reporting_year: int,
        result: GARResult,
        assessment: Optional[Dict],
    ) -> None:
        """Write GAR results to fi_eu_taxonomy_kpis."""
        try:
            # Check if row exists
            existing = conn.execute(
                text("""
                    SELECT id FROM fi_eu_taxonomy_kpis
                    WHERE entity_id = :eid AND reporting_year = :yr
                    LIMIT 1
                """),
                {"eid": entity_id, "yr": reporting_year},
            ).mappings().first()

            obj_map = {b.objective: b for b in result.by_objective}

            params = {
                "entity_id": entity_id,
                "reporting_year": reporting_year,
                "gar_total_pct": round(result.gar_ratio * 100, 2),
                "gar_flow_pct": round(result.gar_flow * 100, 2) if result.gar_flow else None,
                "gar_stock_numerator_meur": round(result.aligned_assets / 1_000_000, 2),
                "gar_denominator_meur": round(result.covered_assets / 1_000_000, 2),
                "gar_climate_mitigation_pct": obj_map.get("CLIMATE_MITIGATION", None) and round(obj_map["CLIMATE_MITIGATION"].aligned_pct, 2),
                "gar_climate_adaptation_pct": obj_map.get("CLIMATE_ADAPTATION", None) and round(obj_map["CLIMATE_ADAPTATION"].aligned_pct, 2),
                "gar_water_pct": obj_map.get("WATER", None) and round(obj_map["WATER"].aligned_pct, 2),
                "gar_circular_economy_pct": obj_map.get("CIRCULAR_ECONOMY", None) and round(obj_map["CIRCULAR_ECONOMY"].aligned_pct, 2),
                "gar_pollution_pct": obj_map.get("POLLUTION", None) and round(obj_map["POLLUTION"].aligned_pct, 2),
                "gar_biodiversity_pct": obj_map.get("BIODIVERSITY", None) and round(obj_map["BIODIVERSITY"].aligned_pct, 2),
            }

            if existing:
                conn.execute(
                    text("""
                        UPDATE fi_eu_taxonomy_kpis
                        SET gar_total_pct = :gar_total_pct,
                            gar_flow_pct = :gar_flow_pct,
                            gar_stock_numerator_meur = :gar_stock_numerator_meur,
                            gar_denominator_meur = :gar_denominator_meur,
                            gar_climate_mitigation_pct = :gar_climate_mitigation_pct,
                            gar_climate_adaptation_pct = :gar_climate_adaptation_pct,
                            gar_water_pct = :gar_water_pct,
                            gar_circular_economy_pct = :gar_circular_economy_pct,
                            gar_pollution_pct = :gar_pollution_pct,
                            gar_biodiversity_pct = :gar_biodiversity_pct
                        WHERE entity_id = :entity_id AND reporting_year = :reporting_year
                    """),
                    params,
                )
            else:
                params["id"] = str(uuid.uuid4())
                conn.execute(
                    text("""
                        INSERT INTO fi_eu_taxonomy_kpis (
                            id, entity_id, reporting_year,
                            gar_total_pct, gar_flow_pct,
                            gar_stock_numerator_meur, gar_denominator_meur,
                            gar_climate_mitigation_pct, gar_climate_adaptation_pct,
                            gar_water_pct, gar_circular_economy_pct,
                            gar_pollution_pct, gar_biodiversity_pct
                        ) VALUES (
                            :id, :entity_id, :reporting_year,
                            :gar_total_pct, :gar_flow_pct,
                            :gar_stock_numerator_meur, :gar_denominator_meur,
                            :gar_climate_mitigation_pct, :gar_climate_adaptation_pct,
                            :gar_water_pct, :gar_circular_economy_pct,
                            :gar_pollution_pct, :gar_biodiversity_pct
                        )
                    """),
                    params,
                )

            logger.info(
                "Persisted GAR results for entity %s year %d: GAR=%.2f%%",
                entity_id, reporting_year, result.gar_ratio * 100,
            )
        except Exception as e:
            logger.error("Failed to persist GAR results: %s", e)

    # -------------------------------------------------------------------
    # SERIALISATION
    # -------------------------------------------------------------------

    def _serialise(
        self,
        result: GARResult,
        entity: Dict,
        reporting_year: int,
        activity_count: int,
    ) -> Dict[str, Any]:
        """Serialise GARResult + metadata for API response."""
        return {
            "entity_id": str(entity.get("id", "")),
            "entity_name": entity.get("legal_name", ""),
            "reporting_year": reporting_year,
            "gar_ratio": result.gar_ratio,
            "gar_eligible_ratio": result.gar_eligible_ratio,
            "gar_flow": result.gar_flow,
            "total_assets": result.total_assets,
            "excluded_assets": result.excluded_assets,
            "covered_assets": result.covered_assets,
            "aligned_assets": result.aligned_assets,
            "eligible_assets": result.eligible_assets,
            "not_eligible_assets": result.not_eligible_assets,
            "by_objective": [
                {
                    "objective": o.objective,
                    "objective_label": o.objective_label,
                    "aligned_amount": o.aligned_amount,
                    "eligible_amount": o.eligible_amount,
                    "aligned_pct": o.aligned_pct,
                    "eligible_pct": o.eligible_pct,
                }
                for o in result.by_objective
            ],
            "by_kpi_type": [
                {
                    "kpi_type": k.kpi_type,
                    "aligned_amount": k.aligned_amount,
                    "eligible_amount": k.eligible_amount,
                    "gar_ratio": k.gar_ratio,
                }
                for k in result.by_kpi_type
            ],
            "by_asset_type": [
                {
                    "asset_type": a.asset_type,
                    "total_amount": a.total_amount,
                    "aligned_amount": a.aligned_amount,
                    "alignment_ratio": a.alignment_ratio,
                    "count": a.count,
                }
                for a in result.by_asset_type
            ],
            "assessed_pct": result.assessed_pct,
            "exposure_count": result.exposure_count,
            "methodology_notes": result.methodology_notes,
            "data_source": {
                "taxonomy_activities_used": activity_count,
                "loan_book_used": activity_count == 0,
                "auto_calculated": True,
            },
        }
