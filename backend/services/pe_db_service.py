"""
PE/VC Database Service — Persistence layer for Private Equity module.

Wires existing PE engines (pe_deal_engine, pe_portfolio_monitor,
pe_value_creation, pe_reporting_engine, pe_impact_framework,
pe_irr_sensitivity) to the pe_* database tables from migration 038:
  - pe_deals
  - pe_screening_scores
  - pe_portfolio_companies
  - pe_sector_risk_heatmap

Provides:
  1. CRUD for deals (create from screening, read pipeline, update stage)
  2. Screening score persistence (per-dimension ratings)
  3. Portfolio company lifecycle (investment → monitoring → exit)
  4. Sector heatmap seeding from engine reference data
  5. DB-powered pipeline analytics and portfolio aggregation

Author: PE DB Service
Version: 1.0.0
Date: 2026-03-08
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, date
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


class PEDBService:
    """
    Database persistence layer for Private Equity module.

    Bridges the gap between the stateless PE engines and the pe_* tables.
    """

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    # ===================================================================
    # DEAL CRUD
    # ===================================================================

    def create_deal(self, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new PE deal record.

        Args:
            deal_data: Dict with keys matching pe_deals columns.

        Returns:
            Created deal record.
        """
        deal_id = deal_data.get("deal_id") or str(uuid.uuid4())
        with self._engine.connect() as conn:
            conn.execute(
                text("""
                    INSERT INTO pe_deals (
                        deal_id, company_name, sector, sub_sector, country,
                        stage, deal_type, deal_size_eur, equity_ticket_eur,
                        enterprise_value_eur, revenue_eur, ebitda_eur,
                        entry_multiple, source, lead_partner, fund_id,
                        esg_screening_status, red_flags, notes
                    ) VALUES (
                        :deal_id, :company_name, :sector, :sub_sector, :country,
                        :stage, :deal_type, :deal_size_eur, :equity_ticket_eur,
                        :enterprise_value_eur, :revenue_eur, :ebitda_eur,
                        :entry_multiple, :source, :lead_partner, :fund_id,
                        :esg_screening_status, :red_flags::jsonb, :notes
                    )
                """),
                {
                    "deal_id": deal_id,
                    "company_name": deal_data.get("company_name", ""),
                    "sector": deal_data.get("sector"),
                    "sub_sector": deal_data.get("sub_sector"),
                    "country": deal_data.get("country"),
                    "stage": deal_data.get("stage", "sourcing"),
                    "deal_type": deal_data.get("deal_type"),
                    "deal_size_eur": deal_data.get("deal_size_eur"),
                    "equity_ticket_eur": deal_data.get("equity_ticket_eur"),
                    "enterprise_value_eur": deal_data.get("enterprise_value_eur"),
                    "revenue_eur": deal_data.get("revenue_eur"),
                    "ebitda_eur": deal_data.get("ebitda_eur"),
                    "entry_multiple": deal_data.get("entry_multiple"),
                    "source": deal_data.get("source"),
                    "lead_partner": deal_data.get("lead_partner"),
                    "fund_id": deal_data.get("fund_id"),
                    "esg_screening_status": deal_data.get("esg_screening_status", "pending"),
                    "red_flags": _to_json(deal_data.get("red_flags", [])),
                    "notes": deal_data.get("notes"),
                },
            )
            conn.commit()

        return {"deal_id": deal_id, "status": "created"}

    def get_deal(self, deal_id: str) -> Optional[Dict[str, Any]]:
        """Get a single deal by ID."""
        with self._engine.connect() as conn:
            row = conn.execute(
                text("SELECT * FROM pe_deals WHERE deal_id = :did"),
                {"did": deal_id},
            ).mappings().first()
            return _row_to_dict(row) if row else None

    def list_deals(
        self,
        fund_id: Optional[str] = None,
        stage: Optional[str] = None,
        sector: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List deals with optional filters."""
        clauses = ["1=1"]
        params: Dict[str, Any] = {"lim": limit}
        if fund_id:
            clauses.append("fund_id = :fund_id")
            params["fund_id"] = fund_id
        if stage:
            clauses.append("stage = :stage")
            params["stage"] = stage
        if sector:
            clauses.append("sector = :sector")
            params["sector"] = sector

        where = " AND ".join(clauses)
        with self._engine.connect() as conn:
            rows = conn.execute(
                text(f"""
                    SELECT * FROM pe_deals
                    WHERE {where}
                    ORDER BY created_at DESC
                    LIMIT :lim
                """),
                params,
            ).mappings().all()
            return [_row_to_dict(r) for r in rows]

    def update_deal_stage(
        self, deal_id: str, new_stage: str, notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update deal pipeline stage."""
        with self._engine.connect() as conn:
            conn.execute(
                text("""
                    UPDATE pe_deals
                    SET stage = :stage,
                        notes = COALESCE(:notes, notes),
                        updated_at = NOW()
                    WHERE deal_id = :did
                """),
                {"did": deal_id, "stage": new_stage, "notes": notes},
            )
            conn.commit()
        return {"deal_id": deal_id, "stage": new_stage}

    # ===================================================================
    # SCREENING SCORES (ESG dimension ratings per deal)
    # ===================================================================

    def persist_screening(
        self,
        deal_id: str,
        screening_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Persist ESG screening scores from pe_deal_engine.screen_deal() output.

        Args:
            deal_id: UUID of the deal.
            screening_result: Output from PEDealEngine.screen_deal() serialised.

        Returns:
            Summary with score_ids created.
        """
        score_ids = []
        dimensions = screening_result.get("dimensions", [])

        with self._engine.connect() as conn:
            # Delete existing scores for this deal (re-screen)
            conn.execute(
                text("DELETE FROM pe_screening_scores WHERE deal_id = :did"),
                {"did": deal_id},
            )

            for dim in dimensions:
                score_id = str(uuid.uuid4())
                conn.execute(
                    text("""
                        INSERT INTO pe_screening_scores (
                            score_id, deal_id, dimension, sub_dimension,
                            rating, weight, rationale, data_source,
                            assessed_by
                        ) VALUES (
                            :sid, :did, :dim, :sub,
                            :rating, :weight, :rationale, :ds,
                            :assessed_by
                        )
                    """),
                    {
                        "sid": score_id,
                        "did": deal_id,
                        "dim": dim.get("dimension", ""),
                        "sub": dim.get("sub_dimension"),
                        "rating": dim.get("rating"),
                        "weight": dim.get("weight", 1.0),
                        "rationale": dim.get("rationale"),
                        "ds": dim.get("data_source"),
                        "assessed_by": dim.get("assessed_by"),
                    },
                )
                score_ids.append(score_id)

            # Update deal's screening status + red flags
            composite = screening_result.get("composite_score")
            red_flags = screening_result.get("red_flags", [])
            esg_status = "completed"
            if any(rf.get("severity") == "hard" for rf in red_flags):
                esg_status = "failed"
            elif composite and composite > 3.5:
                esg_status = "flagged"

            conn.execute(
                text("""
                    UPDATE pe_deals
                    SET esg_screening_status = :status,
                        red_flags = :flags::jsonb,
                        updated_at = NOW()
                    WHERE deal_id = :did
                """),
                {
                    "did": deal_id,
                    "status": esg_status,
                    "flags": _to_json(red_flags),
                },
            )
            conn.commit()

        return {
            "deal_id": deal_id,
            "scores_created": len(score_ids),
            "esg_screening_status": esg_status,
        }

    def get_screening_scores(self, deal_id: str) -> List[Dict[str, Any]]:
        """Get all screening scores for a deal."""
        with self._engine.connect() as conn:
            rows = conn.execute(
                text("""
                    SELECT * FROM pe_screening_scores
                    WHERE deal_id = :did
                    ORDER BY dimension, sub_dimension
                """),
                {"did": deal_id},
            ).mappings().all()
            return [_row_to_dict(r) for r in rows]

    # ===================================================================
    # PORTFOLIO COMPANIES
    # ===================================================================

    def create_portfolio_company(
        self, company_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a portfolio company record (typically after deal closes)."""
        company_id = company_data.get("company_id") or str(uuid.uuid4())
        with self._engine.connect() as conn:
            conn.execute(
                text("""
                    INSERT INTO pe_portfolio_companies (
                        company_id, deal_id, company_name, sector, country,
                        fund_id, investment_date, equity_invested_eur,
                        current_nav_eur, ownership_pct, board_seats,
                        status, esg_score_entry, sdg_alignment
                    ) VALUES (
                        :cid, :did, :name, :sector, :country,
                        :fund_id, :inv_date, :equity,
                        :nav, :own_pct, :boards,
                        :status, :esg_entry, :sdg::jsonb
                    )
                """),
                {
                    "cid": company_id,
                    "did": company_data.get("deal_id"),
                    "name": company_data.get("company_name", ""),
                    "sector": company_data.get("sector"),
                    "country": company_data.get("country"),
                    "fund_id": company_data.get("fund_id"),
                    "inv_date": company_data.get("investment_date"),
                    "equity": company_data.get("equity_invested_eur"),
                    "nav": company_data.get("current_nav_eur"),
                    "own_pct": company_data.get("ownership_pct"),
                    "boards": company_data.get("board_seats", 0),
                    "status": company_data.get("status", "active"),
                    "esg_entry": company_data.get("esg_score_entry"),
                    "sdg": _to_json(company_data.get("sdg_alignment", [])),
                },
            )
            conn.commit()
        return {"company_id": company_id, "status": "created"}

    def list_portfolio_companies(
        self,
        fund_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List portfolio companies with optional filters."""
        clauses = ["1=1"]
        params: Dict[str, Any] = {"lim": limit}
        if fund_id:
            clauses.append("fund_id = :fund_id")
            params["fund_id"] = fund_id
        if status:
            clauses.append("status = :status")
            params["status"] = status

        where = " AND ".join(clauses)
        with self._engine.connect() as conn:
            rows = conn.execute(
                text(f"""
                    SELECT * FROM pe_portfolio_companies
                    WHERE {where}
                    ORDER BY investment_date DESC NULLS LAST
                    LIMIT :lim
                """),
                params,
            ).mappings().all()
            return [_row_to_dict(r) for r in rows]

    def update_portfolio_company(
        self, company_id: str, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a portfolio company (NAV, ESG score, exit data, etc.).

        Only updates provided fields.
        """
        set_clauses = []
        params: Dict[str, Any] = {"cid": company_id}

        _ALLOWED = {
            "current_nav_eur", "ownership_pct", "board_seats", "status",
            "exit_date", "exit_proceeds_eur", "esg_score_current",
        }
        for key, val in updates.items():
            if key in _ALLOWED:
                set_clauses.append(f"{key} = :{key}")
                params[key] = val

        if "sdg_alignment" in updates:
            set_clauses.append("sdg_alignment = :sdg::jsonb")
            params["sdg"] = _to_json(updates["sdg_alignment"])

        if not set_clauses:
            return {"company_id": company_id, "status": "no_changes"}

        set_clauses.append("updated_at = NOW()")

        with self._engine.connect() as conn:
            conn.execute(
                text(f"""
                    UPDATE pe_portfolio_companies
                    SET {', '.join(set_clauses)}
                    WHERE company_id = :cid
                """),
                params,
            )
            conn.commit()

        return {"company_id": company_id, "status": "updated"}

    def record_exit(
        self, company_id: str, exit_date: str, exit_proceeds_eur: float
    ) -> Dict[str, Any]:
        """Record a portfolio company exit."""
        return self.update_portfolio_company(company_id, {
            "status": "exited",
            "exit_date": exit_date,
            "exit_proceeds_eur": exit_proceeds_eur,
        })

    # ===================================================================
    # SECTOR RISK HEATMAP
    # ===================================================================

    def seed_sector_heatmap(self) -> Dict[str, Any]:
        """
        Seed pe_sector_risk_heatmap from PEDealEngine's hardcoded data.

        Idempotent: skips sectors that already exist.
        """
        from services.pe_deal_engine import PEDealEngine
        engine = PEDealEngine()
        heatmap = engine.get_sector_heatmap()

        created = 0
        with self._engine.connect() as conn:
            for sector_row in heatmap:
                sector = sector_row.get("sector", "")
                existing = conn.execute(
                    text("SELECT 1 FROM pe_sector_risk_heatmap WHERE sector = :s"),
                    {"s": sector},
                ).first()
                if existing:
                    continue

                conn.execute(
                    text("""
                        INSERT INTO pe_sector_risk_heatmap (
                            sector_risk_id, sector,
                            environmental_risk, social_risk, governance_risk,
                            transition_risk, physical_risk, overall_risk,
                            rationale
                        ) VALUES (
                            :sid, :sector,
                            :env, :soc, :gov,
                            :trans, :phys, :overall,
                            :rationale
                        )
                    """),
                    {
                        "sid": str(uuid.uuid4()),
                        "sector": sector,
                        "env": sector_row.get("environmental_risk"),
                        "soc": sector_row.get("social_risk"),
                        "gov": sector_row.get("governance_risk"),
                        "trans": sector_row.get("transition_risk"),
                        "phys": sector_row.get("physical_risk"),
                        "overall": sector_row.get("overall_risk"),
                        "rationale": sector_row.get("rationale", ""),
                    },
                )
                created += 1

            conn.commit()

        return {"sectors_seeded": created}

    def get_sector_heatmap(self) -> List[Dict[str, Any]]:
        """Get sector risk heatmap from DB."""
        with self._engine.connect() as conn:
            rows = conn.execute(
                text("""
                    SELECT sector, environmental_risk, social_risk,
                           governance_risk, transition_risk, physical_risk,
                           overall_risk, rationale
                    FROM pe_sector_risk_heatmap
                    ORDER BY overall_risk DESC, sector
                """),
            ).mappings().all()
            return [_row_to_dict(r) for r in rows]

    # ===================================================================
    # PIPELINE ANALYTICS (DB-powered)
    # ===================================================================

    def pipeline_summary(
        self, fund_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate pipeline analytics from pe_deals table.

        Returns counts by stage, sector, screening status, and totals.
        """
        fund_clause = "AND fund_id = :fund_id" if fund_id else ""
        params = {"fund_id": fund_id} if fund_id else {}

        with self._engine.connect() as conn:
            # By stage
            by_stage = conn.execute(
                text(f"""
                    SELECT stage, COUNT(*) as count,
                           COALESCE(SUM(deal_size_eur), 0) as total_deal_size
                    FROM pe_deals
                    WHERE 1=1 {fund_clause}
                    GROUP BY stage
                    ORDER BY count DESC
                """),
                params,
            ).mappings().all()

            # By sector
            by_sector = conn.execute(
                text(f"""
                    SELECT sector, COUNT(*) as count,
                           COALESCE(SUM(deal_size_eur), 0) as total_deal_size
                    FROM pe_deals
                    WHERE 1=1 {fund_clause}
                    GROUP BY sector
                    ORDER BY count DESC
                """),
                params,
            ).mappings().all()

            # By screening status
            by_screening = conn.execute(
                text(f"""
                    SELECT esg_screening_status, COUNT(*) as count
                    FROM pe_deals
                    WHERE 1=1 {fund_clause}
                    GROUP BY esg_screening_status
                """),
                params,
            ).mappings().all()

            # Totals
            totals = conn.execute(
                text(f"""
                    SELECT COUNT(*) as total_deals,
                           COALESCE(SUM(deal_size_eur), 0) as total_pipeline_eur,
                           COALESCE(AVG(entry_multiple), 0) as avg_entry_multiple
                    FROM pe_deals
                    WHERE 1=1 {fund_clause}
                """),
                params,
            ).mappings().first()

            return {
                "totals": _row_to_dict(totals) if totals else {},
                "by_stage": [_row_to_dict(r) for r in by_stage],
                "by_sector": [_row_to_dict(r) for r in by_sector],
                "by_screening_status": [_row_to_dict(r) for r in by_screening],
            }

    def portfolio_summary(
        self, fund_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate portfolio company analytics from pe_portfolio_companies.
        """
        fund_clause = "AND fund_id = :fund_id" if fund_id else ""
        params = {"fund_id": fund_id} if fund_id else {}

        with self._engine.connect() as conn:
            summary = conn.execute(
                text(f"""
                    SELECT
                        COUNT(*) as total_companies,
                        COUNT(*) FILTER (WHERE status = 'active') as active_count,
                        COUNT(*) FILTER (WHERE status = 'exited') as exited_count,
                        COALESCE(SUM(equity_invested_eur), 0) as total_invested_eur,
                        COALESCE(SUM(current_nav_eur), 0) as total_nav_eur,
                        COALESCE(SUM(exit_proceeds_eur), 0) as total_exit_proceeds_eur,
                        COALESCE(AVG(esg_score_current), 0) as avg_esg_score,
                        COALESCE(AVG(esg_score_entry), 0) as avg_esg_entry_score
                    FROM pe_portfolio_companies
                    WHERE 1=1 {fund_clause}
                """),
                params,
            ).mappings().first()

            by_sector = conn.execute(
                text(f"""
                    SELECT sector, COUNT(*) as count,
                           COALESCE(SUM(equity_invested_eur), 0) as invested_eur,
                           COALESCE(AVG(esg_score_current), 0) as avg_esg
                    FROM pe_portfolio_companies
                    WHERE status = 'active' {fund_clause.replace('AND', 'AND' if fund_clause else '')}
                    GROUP BY sector
                    ORDER BY invested_eur DESC
                """),
                params,
            ).mappings().all()

            result = _row_to_dict(summary) if summary else {}
            result["by_sector"] = [_row_to_dict(r) for r in by_sector]

            # TVPI approximation
            total_invested = float(result.get("total_invested_eur", 0))
            total_nav = float(result.get("total_nav_eur", 0))
            total_exits = float(result.get("total_exit_proceeds_eur", 0))
            if total_invested > 0:
                result["tvpi"] = round((total_nav + total_exits) / total_invested, 2)
                result["dpi"] = round(total_exits / total_invested, 2)
                result["rvpi"] = round(total_nav / total_invested, 2)

            return result

    # ===================================================================
    # SCREEN-AND-PERSIST (combines engine + DB)
    # ===================================================================

    def screen_and_persist_deal(
        self, deal_data: Dict[str, Any], screening_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Full workflow: create deal record → run ESG screening → persist scores.

        Args:
            deal_data: Dict for pe_deals columns.
            screening_input: Dict for PEDealEngine.screen_deal() input.

        Returns:
            Combined result with deal_id, screening scores, and status.
        """
        from services.pe_deal_engine import PEDealEngine

        # 1. Create deal
        create_result = self.create_deal(deal_data)
        deal_id = create_result["deal_id"]

        # 2. Run ESG screening
        engine = PEDealEngine()
        screening_result = engine.screen_deal(screening_input)

        # Serialise screening result if it's a dataclass
        if hasattr(screening_result, "__dict__") and not isinstance(screening_result, dict):
            screening_dict = _dataclass_to_dict(screening_result)
        else:
            screening_dict = screening_result

        # 3. Persist screening scores
        persist_result = self.persist_screening(deal_id, screening_dict)

        return {
            "deal_id": deal_id,
            "screening": screening_dict,
            "persistence": persist_result,
        }


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _to_json(val: Any) -> str:
    """Convert a Python object to JSON string for JSONB columns."""
    import json
    if val is None:
        return "[]"
    return json.dumps(val, default=str)


def _row_to_dict(row) -> Dict[str, Any]:
    """Convert a SQLAlchemy row mapping to a JSON-safe dict."""
    if row is None:
        return {}
    d = dict(row)
    for k, v in d.items():
        if isinstance(v, (datetime, date)):
            d[k] = v.isoformat()
        elif isinstance(v, uuid.UUID):
            d[k] = str(v)
        elif hasattr(v, "is_integer"):  # Decimal
            d[k] = float(v)
    return d


def _dataclass_to_dict(obj: Any) -> Dict[str, Any]:
    """Recursively convert a dataclass to dict."""
    from dataclasses import fields, is_dataclass
    if not is_dataclass(obj):
        return obj
    result = {}
    for f in fields(obj):
        val = getattr(obj, f.name)
        if is_dataclass(val):
            result[f.name] = _dataclass_to_dict(val)
        elif isinstance(val, list):
            result[f.name] = [
                _dataclass_to_dict(item) if is_dataclass(item) else item
                for item in val
            ]
        else:
            result[f.name] = val
    return result
