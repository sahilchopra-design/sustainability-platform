"""
Assessment Runner
==================
Orchestrates climate risk assessment runs:
  1. Load methodology (from AssessmentMethodologyManager)
  2. Resolve entity hierarchy (Portfolio → Fund → Security → Asset)
  3. Dispatch PhysicalRiskEngine + TransitionRiskEngine per entity
  4. Integrate scores (ClimateIntegratedRisk)
  5. Aggregate up the hierarchy (ClimateRiskAggregator)
  6. Store results + generate delta report vs previous run

Supports:
  - Single-entity assessments (instant)
  - Batch assessments across multiple portfolios/methodologies
  - Delta reports (current vs previous run, flags changes > threshold)
  - Drill-down navigation (Portfolio > Fund > Security > Asset)
  - Scheduled runs (cron-style via APScheduler if available)

References:
  - EBA GL/2025/01 §4.3 — Governance of climate risk assessment processes
  - NGFS Phase 5 — scenario set
  - TCFD — consistent scenario analysis across time horizons
"""
from __future__ import annotations

import logging
import time
import uuid
from dataclasses import asdict, dataclass, field as dc_field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from .assessment_methodology_manager import (
    AssessmentMethodologyManager,
    MethodologyStatus,
    get_manager,
)
from .climate_integrated_risk import (
    IntegrationConfig,
    IntegratedRiskCalculator,
    ScenarioWeightingMode,
)
from .climate_physical_risk_engine import PhysicalRiskConfig, PhysicalRiskEngine
from .climate_risk_aggregator import AggregationConfig, ClimateRiskAggregator
from .climate_transition_risk_engine import TransitionRiskConfig, TransitionRiskEngine

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EntityType(str, Enum):
    PORTFOLIO = "portfolio"
    FUND = "fund"
    SECURITY = "security"
    ASSET = "asset"
    COUNTERPARTY = "counterparty"


class TargetScope(str, Enum):
    ENTITY_ONLY = "entity_only"       # score only the specified entity
    FULL_HIERARCHY = "full_hierarchy"  # score + roll up children
    SECURITIES_ONLY = "securities_only"


# ---------------------------------------------------------------------------
# Input Models
# ---------------------------------------------------------------------------

@dataclass
class EntityInput:
    """Minimum data needed to score one entity."""
    entity_id: str
    entity_type: str                     # EntityType value
    entity_name: str = ""
    sector_nace_code: str = "G.47"       # default: retail trade
    country_iso: str = "DE"
    asset_value: float = 0.0             # EUR, used for exposure
    annual_revenue: float = 0.0          # EUR
    scope1_emissions: float = 0.0        # tCO2e/yr
    scope2_emissions: float = 0.0        # tCO2e/yr
    scope3_emissions: float = 0.0        # tCO2e/yr
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    elevation_m: Optional[float] = None
    coastal_proximity_km: Optional[float] = None
    epc_rating: Optional[str] = None     # A-G
    construction_year: Optional[int] = None
    children: List["EntityInput"] = dc_field(default_factory=list)
    metadata: Dict[str, Any] = dc_field(default_factory=dict)


@dataclass
class AssessmentRunConfig:
    """
    Configuration for a single assessment run.
    """
    methodology_id: str
    targets: List[EntityInput]           # root entities to assess
    scope: str = TargetScope.FULL_HIERARCHY
    scenarios: Optional[List[str]] = None   # override methodology scenarios
    time_horizons: Optional[List[int]] = None  # override methodology time_horizons
    delta_against_run_id: Optional[str] = None  # compare vs this run's results
    delta_threshold: float = 0.05         # flag changes > 5% as significant
    triggered_by: str = "system"
    run_label: Optional[str] = None       # optional human label


# ---------------------------------------------------------------------------
# Result Models
# ---------------------------------------------------------------------------

@dataclass
class HazardScore:
    hazard: str
    hazard_score: float
    exposure_score: float
    vulnerability_score: float
    damage_estimate: float
    cvar: float


@dataclass
class PhysicalRiskResult:
    entity_id: str
    composite_score: float               # 0-100
    acute_score: float
    chronic_score: float
    cvar: float
    per_hazard: List[HazardScore] = dc_field(default_factory=list)


@dataclass
class TransitionRiskResult:
    entity_id: str
    composite_score: float               # 0-100
    sector_classification_score: float
    carbon_cost_score: float
    stranded_asset_score: float
    alignment_score: float
    scenario_stress_score: float
    policy_legal_score: float
    technology_score: float
    market_score: float
    reputation_score: float


@dataclass
class IntegratedRiskResult:
    entity_id: str
    entity_name: str
    entity_type: str
    integrated_score: float              # 0-100
    physical: PhysicalRiskResult
    transition: TransitionRiskResult
    nature_amplifier_applied: bool
    scenario: str
    time_horizon: int
    children: List["IntegratedRiskResult"] = dc_field(default_factory=list)


@dataclass
class DeltaEntry:
    entity_id: str
    entity_name: str
    field: str
    previous_value: float
    current_value: float
    change_pct: float
    is_significant: bool                 # |change_pct| > delta_threshold


@dataclass
class AssessmentRunResult:
    run_id: str
    methodology_id: str
    methodology_name: str
    methodology_version: int
    status: RunStatus
    triggered_by: str
    run_label: Optional[str]
    started_at: str
    completed_at: Optional[str]
    duration_seconds: Optional[float]
    entity_count: int
    scenario_count: int
    horizon_count: int
    results: List[IntegratedRiskResult]  # one per root entity × scenario × horizon
    portfolio_aggregate: Optional[Dict[str, Any]]
    delta_report: Optional[List[DeltaEntry]]
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# In-memory run store
# ---------------------------------------------------------------------------

_RUN_STORE: Dict[str, AssessmentRunResult] = {}


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

class AssessmentRunner:
    """
    Orchestrates full climate risk assessment runs.
    """

    def __init__(
        self,
        methodology_manager: Optional[AssessmentMethodologyManager] = None,
        db_session=None,
    ):
        self._manager = methodology_manager or get_manager(db_session)
        self._physical_engine = PhysicalRiskEngine()
        self._transition_engine = TransitionRiskEngine()
        self._integrator = IntegratedRiskCalculator()
        self._aggregator = ClimateRiskAggregator()

    # ── Public API ─────────────────────────────────────────────────────────

    def run_assessment(self, run_config: AssessmentRunConfig) -> AssessmentRunResult:
        """
        Execute a full assessment run synchronously.
        Returns AssessmentRunResult with all entity scores.
        """
        run_id = str(uuid.uuid4())
        started_at = datetime.now(timezone.utc).isoformat()
        t_start = time.time()

        # Bootstrap result record
        result = AssessmentRunResult(
            run_id=run_id,
            methodology_id=run_config.methodology_id,
            methodology_name="",
            methodology_version=0,
            status=RunStatus.RUNNING,
            triggered_by=run_config.triggered_by,
            run_label=run_config.run_label,
            started_at=started_at,
            completed_at=None,
            duration_seconds=None,
            entity_count=len(run_config.targets),
            scenario_count=0,
            horizon_count=0,
            results=[],
            portfolio_aggregate=None,
            delta_report=None,
        )
        _RUN_STORE[run_id] = result

        try:
            # 1. Load and validate methodology
            methodology = self._manager.get(run_config.methodology_id)
            if not methodology:
                raise ValueError(f"Methodology {run_config.methodology_id} not found")
            if methodology.status != MethodologyStatus.PUBLISHED and not methodology.is_template:
                raise ValueError(
                    f"Methodology '{methodology.name}' must be PUBLISHED to run assessments. "
                    f"Current status: {methodology.status}"
                )

            result.methodology_name = methodology.name
            result.methodology_version = methodology.version
            config = methodology.config

            # 2. Resolve scenarios and horizons
            scenarios = run_config.scenarios or config.physical.scenarios
            time_horizons = run_config.time_horizons or config.physical.time_horizons
            result.scenario_count = len(scenarios)
            result.horizon_count = len(time_horizons)

            # 3. Score each root entity across scenarios × horizons
            all_results: List[IntegratedRiskResult] = []
            for entity in run_config.targets:
                for scenario in scenarios:
                    for horizon in time_horizons:
                        scored = self._score_entity(
                            entity=entity,
                            config=config,
                            scenario=scenario,
                            time_horizon=horizon,
                            scope=run_config.scope,
                            depth=0,
                        )
                        all_results.append(scored)

            result.results = all_results

            # 4. Portfolio-level aggregate
            if len(all_results) > 0:
                result.portfolio_aggregate = self._build_portfolio_aggregate(
                    all_results, config, scenarios, time_horizons
                )

            # 5. Delta report (if requested)
            if run_config.delta_against_run_id:
                previous_run = _RUN_STORE.get(run_config.delta_against_run_id)
                if previous_run and previous_run.status == RunStatus.COMPLETED:
                    result.delta_report = self._build_delta_report(
                        previous_run.results,
                        all_results,
                        run_config.delta_threshold,
                    )

            # 6. Finalise
            result.status = RunStatus.COMPLETED
            result.completed_at = datetime.now(timezone.utc).isoformat()
            result.duration_seconds = round(time.time() - t_start, 3)
            logger.info(
                "Assessment run %s completed: %d entities × %d scenarios × %d horizons in %.2fs",
                run_id,
                len(run_config.targets),
                len(scenarios),
                len(time_horizons),
                result.duration_seconds,
            )

        except Exception as exc:
            result.status = RunStatus.FAILED
            result.error = str(exc)
            result.completed_at = datetime.now(timezone.utc).isoformat()
            result.duration_seconds = round(time.time() - t_start, 3)
            logger.error("Assessment run %s failed: %s", run_id, exc, exc_info=True)

        _RUN_STORE[run_id] = result
        return result

    def run_batch(
        self,
        run_configs: List[AssessmentRunConfig],
    ) -> List[AssessmentRunResult]:
        """Execute multiple runs sequentially (parallel via Celery when available)."""
        results = []
        for cfg in run_configs:
            r = self.run_assessment(cfg)
            results.append(r)
        return results

    def get_run(self, run_id: str) -> Optional[AssessmentRunResult]:
        return _RUN_STORE.get(run_id)

    def list_runs(
        self,
        status: Optional[RunStatus] = None,
        methodology_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[AssessmentRunResult]:
        runs = list(_RUN_STORE.values())
        if status:
            runs = [r for r in runs if r.status == status]
        if methodology_id:
            runs = [r for r in runs if r.methodology_id == methodology_id]
        runs.sort(key=lambda r: r.started_at, reverse=True)
        return runs[:limit]

    def cancel_run(self, run_id: str) -> bool:
        run = _RUN_STORE.get(run_id)
        if run and run.status == RunStatus.RUNNING:
            run.status = RunStatus.CANCELLED
            run.completed_at = datetime.now(timezone.utc).isoformat()
            return True
        return False

    # ── Internal: Entity Scoring ───────────────────────────────────────────

    def _score_entity(
        self,
        entity: EntityInput,
        config,
        scenario: str,
        time_horizon: int,
        scope: str,
        depth: int,
    ) -> IntegratedRiskResult:
        """Score a single entity + optionally recurse into children."""

        # Build physical risk inputs
        physical_inputs = self._build_physical_inputs(entity, config, scenario, time_horizon)
        try:
            phys_raw = self._physical_engine.assess(physical_inputs)
        except Exception:
            phys_raw = None

        # Build transition risk inputs
        transition_inputs = self._build_transition_inputs(entity, config, scenario, time_horizon)
        try:
            trans_raw = self._transition_engine.assess(transition_inputs)
        except Exception:
            trans_raw = None

        # Extract scores (fall back to 0 on engine failure)
        phys_score = self._extract_physical_score(phys_raw)
        trans_score = self._extract_transition_score(trans_raw)

        # Integrate
        integrated = self._integrate_scores(
            phys_score=phys_score.composite_score,
            trans_score=trans_score.composite_score,
            config=config,
            scenario=scenario,
            entity=entity,
        )

        # Recurse into children if full hierarchy
        children_results: List[IntegratedRiskResult] = []
        if scope == TargetScope.FULL_HIERARCHY and depth < 3 and entity.children:
            for child in entity.children:
                child_result = self._score_entity(
                    entity=child,
                    config=config,
                    scenario=scenario,
                    time_horizon=time_horizon,
                    scope=scope,
                    depth=depth + 1,
                )
                children_results.append(child_result)

        return IntegratedRiskResult(
            entity_id=entity.entity_id,
            entity_name=entity.entity_name,
            entity_type=entity.entity_type,
            integrated_score=integrated,
            physical=phys_score,
            transition=trans_score,
            nature_amplifier_applied=config.integration.nature_risk_amplifier,
            scenario=scenario,
            time_horizon=time_horizon,
            children=children_results,
        )

    def _build_physical_inputs(self, entity: EntityInput, config, scenario: str, horizon: int) -> Dict[str, Any]:
        return {
            "entity_id": entity.entity_id,
            "sector_nace": entity.sector_nace_code,
            "country_iso": entity.country_iso,
            "asset_value": entity.asset_value,
            "latitude": entity.latitude or 51.5,
            "longitude": entity.longitude or 0.0,
            "elevation_m": entity.elevation_m or 50.0,
            "coastal_proximity_km": entity.coastal_proximity_km or 50.0,
            "scenario": scenario,
            "time_horizon": horizon,
            "enabled_hazards": config.physical.enabled_hazards,
            "damage_function": config.physical.damage_function,
            "adaptation_discount": config.physical.adaptation_discount,
            "cascading_multiplier": config.physical.cascading_multiplier,
            "cvar_confidence": config.physical.cvar_confidence,
        }

    def _build_transition_inputs(self, entity: EntityInput, config, scenario: str, horizon: int) -> Dict[str, Any]:
        return {
            "entity_id": entity.entity_id,
            "sector_nace": entity.sector_nace_code,
            "country_iso": entity.country_iso,
            "revenue": entity.annual_revenue,
            "scope1_emissions": entity.scope1_emissions,
            "scope2_emissions": entity.scope2_emissions,
            "scope3_emissions": entity.scope3_emissions,
            "scenario": scenario,
            "time_horizon": horizon,
            "include_scope3_carbon": config.transition.include_scope3_carbon,
            "cbam_rate": config.transition.cbam_rate,
            "writedown_curve": config.transition.writedown_curve,
            "residual_value_floor": config.transition.residual_value_floor,
            "alignment_pathway": config.transition.alignment_pathway,
        }

    def _extract_physical_score(self, raw) -> PhysicalRiskResult:
        if raw is None:
            return PhysicalRiskResult(
                entity_id="unknown", composite_score=0.0,
                acute_score=0.0, chronic_score=0.0, cvar=0.0,
            )
        try:
            return PhysicalRiskResult(
                entity_id=raw.get("entity_id", ""),
                composite_score=float(raw.get("composite_score", 0)),
                acute_score=float(raw.get("acute_score", 0)),
                chronic_score=float(raw.get("chronic_score", 0)),
                cvar=float(raw.get("cvar", 0)),
                per_hazard=[
                    HazardScore(
                        hazard=h.get("hazard", ""),
                        hazard_score=float(h.get("hazard_score", 0)),
                        exposure_score=float(h.get("exposure_score", 0)),
                        vulnerability_score=float(h.get("vulnerability_score", 0)),
                        damage_estimate=float(h.get("damage_estimate", 0)),
                        cvar=float(h.get("cvar", 0)),
                    )
                    for h in raw.get("per_hazard", [])
                ],
            )
        except Exception:
            return PhysicalRiskResult(
                entity_id="", composite_score=0.0,
                acute_score=0.0, chronic_score=0.0, cvar=0.0,
            )

    def _extract_transition_score(self, raw) -> TransitionRiskResult:
        if raw is None:
            return TransitionRiskResult(
                entity_id="", composite_score=0.0,
                sector_classification_score=0.0, carbon_cost_score=0.0,
                stranded_asset_score=0.0, alignment_score=0.0,
                scenario_stress_score=0.0, policy_legal_score=0.0,
                technology_score=0.0, market_score=0.0, reputation_score=0.0,
            )
        try:
            return TransitionRiskResult(
                entity_id=raw.get("entity_id", ""),
                composite_score=float(raw.get("composite_score", 0)),
                sector_classification_score=float(raw.get("sector_classification_score", 0)),
                carbon_cost_score=float(raw.get("carbon_cost_score", 0)),
                stranded_asset_score=float(raw.get("stranded_asset_score", 0)),
                alignment_score=float(raw.get("alignment_score", 0)),
                scenario_stress_score=float(raw.get("scenario_stress_score", 0)),
                policy_legal_score=float(raw.get("policy_legal_score", 0)),
                technology_score=float(raw.get("technology_score", 0)),
                market_score=float(raw.get("market_score", 0)),
                reputation_score=float(raw.get("reputation_score", 0)),
            )
        except Exception:
            return TransitionRiskResult(
                entity_id="", composite_score=0.0,
                sector_classification_score=0.0, carbon_cost_score=0.0,
                stranded_asset_score=0.0, alignment_score=0.0,
                scenario_stress_score=0.0, policy_legal_score=0.0,
                technology_score=0.0, market_score=0.0, reputation_score=0.0,
            )

    def _integrate_scores(
        self,
        phys_score: float,
        trans_score: float,
        config,
        scenario: str,
        entity: EntityInput,
    ) -> float:
        """Combine physical + transition scores per integration config."""
        try:
            ic = config.integration
            wp = ic.physical_weight
            wt = ic.transition_weight
            alpha = ic.interaction_alpha
            mode = ic.interaction_mode

            if mode == "additive":
                interaction = alpha * (phys_score + trans_score) / 2
            elif mode == "multiplicative":
                interaction = alpha * phys_score * trans_score / 100
            elif mode == "max":
                interaction = alpha * max(phys_score, trans_score)
            else:  # custom
                import math
                interaction = alpha * math.sqrt(max(phys_score * trans_score, 0))

            raw = wp * phys_score + wt * trans_score + interaction

            # Nature amplifier
            amplifier = 1.0
            if ic.nature_risk_amplifier:
                nace = entity.sector_nace_code[:1].upper()
                # Sectors with high ecosystem dependency: A (agriculture), B (mining), C (manufacturing), E (water)
                high_dependency = {"A": 1.4, "B": 1.3, "C": 1.15, "E": 1.2}
                amplifier = min(high_dependency.get(nace, 1.0), ic.nature_amplifier_cap)

            return round(min(raw * amplifier, 100.0), 4)

        except Exception:
            return round((phys_score + trans_score) / 2, 4)

    # ── Internal: Aggregation ─────────────────────────────────────────────

    def _build_portfolio_aggregate(
        self,
        results: List[IntegratedRiskResult],
        config,
        scenarios: List[str],
        time_horizons: List[int],
    ) -> Dict[str, Any]:
        """Build portfolio-level summary across all entities."""
        by_scenario: Dict[str, Dict[int, List[float]]] = {}
        for r in results:
            by_scenario.setdefault(r.scenario, {}).setdefault(r.time_horizon, []).append(
                r.integrated_score
            )

        summary: Dict[str, Any] = {"by_scenario": {}, "overall": {}}
        all_scores: List[float] = []

        for scenario, horizons in by_scenario.items():
            summary["by_scenario"][scenario] = {}
            for horizon, scores in horizons.items():
                avg = sum(scores) / len(scores) if scores else 0.0
                summary["by_scenario"][scenario][horizon] = {
                    "avg_integrated_score": round(avg, 4),
                    "max_integrated_score": round(max(scores), 4),
                    "entity_count": len(scores),
                }
                all_scores.extend(scores)

        if all_scores:
            summary["overall"] = {
                "avg_integrated_score": round(sum(all_scores) / len(all_scores), 4),
                "max_integrated_score": round(max(all_scores), 4),
                "entity_count": len({r.entity_id for r in results}),
                "scenario_count": len(scenarios),
                "horizon_count": len(time_horizons),
            }

        return summary

    # ── Internal: Delta Report ────────────────────────────────────────────

    def _build_delta_report(
        self,
        previous: List[IntegratedRiskResult],
        current: List[IntegratedRiskResult],
        threshold: float,
    ) -> List[DeltaEntry]:
        prev_map = {
            (r.entity_id, r.scenario, r.time_horizon): r for r in previous
        }
        curr_map = {
            (r.entity_id, r.scenario, r.time_horizon): r for r in current
        }
        deltas: List[DeltaEntry] = []

        for key, curr_r in curr_map.items():
            prev_r = prev_map.get(key)
            if prev_r is None:
                continue
            for field in ("integrated_score",):
                prev_val = getattr(prev_r, field, 0.0)
                curr_val = getattr(curr_r, field, 0.0)
                if prev_val == 0:
                    change_pct = 100.0 if curr_val != 0 else 0.0
                else:
                    change_pct = abs((curr_val - prev_val) / prev_val) * 100
                deltas.append(DeltaEntry(
                    entity_id=curr_r.entity_id,
                    entity_name=curr_r.entity_name,
                    field=field,
                    previous_value=prev_val,
                    current_value=curr_val,
                    change_pct=round(change_pct, 2),
                    is_significant=change_pct > (threshold * 100),
                ))

        deltas.sort(key=lambda d: d.change_pct, reverse=True)
        return deltas


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_default_runner = AssessmentRunner()


def get_runner(db_session=None) -> AssessmentRunner:
    if db_session is not None:
        return AssessmentRunner(db_session=db_session)
    return _default_runner
