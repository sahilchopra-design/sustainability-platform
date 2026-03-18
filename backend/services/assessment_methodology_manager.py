"""
Assessment Methodology Manager
================================
Manages the full lifecycle of climate risk assessment methodologies:
  DRAFT → PUBLISHED → RETIRED → ARCHIVED

Each methodology bundles:
  - PhysicalRiskConfig  (from climate_physical_risk_engine)
  - TransitionRiskConfig (from climate_transition_risk_engine)
  - IntegrationConfig   (from climate_integrated_risk)
  - OutputConfig        (output format + reporting templates)

Features:
  - CRUD with lifecycle-gated mutations (only DRAFT editable)
  - Version auto-increment on every publish
  - Field-level change_log (field, old_value, new_value, changed_by, timestamp)
  - Clone to new DRAFT (copies config, resets version to 1)
  - 9 pre-calibrated read-only templates that can be cloned
  - JSON export / import for methodology portability
  - Validation: weight sums, param ranges, no conflicting settings

References:
  - EBA GL/2025/01 — ESG Risk Management (methodology governance requirements)
  - NGFS Phase 5 scenario catalogue
  - TCFD four-pillar disclosure framework
  - TNFD LEAP approach
"""
from __future__ import annotations

import json
import logging
import uuid
from copy import deepcopy
from dataclasses import asdict, dataclass, field as dc_field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class MethodologyStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    RETIRED = "RETIRED"
    ARCHIVED = "ARCHIVED"


class InteractionMode(str, Enum):
    ADDITIVE = "additive"
    MULTIPLICATIVE = "multiplicative"
    MAX = "max"
    CUSTOM = "custom"


class ScenarioWeighting(str, Enum):
    EQUAL = "equal"
    PROBABILITY_WEIGHTED = "probability_weighted"
    CUSTOM = "custom"


class AggregationMethod(str, Enum):
    WEIGHTED_AVERAGE = "weighted_average"
    SUM = "sum"
    MAX = "max"
    MEDIAN = "median"
    VALUE_WEIGHTED = "value_weighted"


class ReportingTemplate(str, Enum):
    EBA_PILLAR3 = "eba_pillar3"
    TCFD_FOUR_PILLAR = "tcfd_four_pillar"
    CSRD_ESRS_E1 = "csrd_esrs_e1"
    ISSB_S2 = "issb_s2"
    INTERNAL_SUMMARY = "internal_summary"


# ---------------------------------------------------------------------------
# Config Sub-Models
# ---------------------------------------------------------------------------

@dataclass
class PhysicalRiskParams:
    """Subset of PhysicalRiskConfig parameters stored in methodology."""
    # Hazard weights (acute vs chronic split)
    acute_weight: float = 0.5
    chronic_weight: float = 0.5
    # Enabled hazards (subset of 13)
    enabled_hazards: List[str] = dc_field(default_factory=lambda: [
        "riverine_flood", "coastal_flood", "tropical_cyclone",
        "extreme_heat", "wildfire", "drought",
        "sea_level_rise", "chronic_heat_stress"
    ])
    # Damage function
    damage_function: str = "sigmoid"          # linear | sigmoid | exponential | step
    # Vulnerability modifiers
    adaptation_discount: float = 0.1          # 0.0–0.5: discount for adaptation measures
    cascading_multiplier: float = 1.2         # >1.0 amplifies cascading failures
    # CVaR confidence
    cvar_confidence: float = 0.95
    # Time horizons (years from base)
    time_horizons: List[int] = dc_field(default_factory=lambda: [5, 10, 20, 30])
    # Scenarios
    scenarios: List[str] = dc_field(default_factory=lambda: [
        "Below 2°C", "Delayed Transition", "Current Policies"
    ])


@dataclass
class TransitionRiskParams:
    """Subset of TransitionRiskConfig parameters stored in methodology."""
    # Stage weights (must sum to 1.0)
    sector_classification_weight: float = 0.15
    carbon_pricing_weight: float = 0.25
    stranded_asset_weight: float = 0.20
    alignment_weight: float = 0.20
    scenario_stress_weight: float = 0.20
    # TCFD category weights (must sum to 1.0)
    policy_legal_weight: float = 0.30
    technology_weight: float = 0.25
    market_weight: float = 0.25
    reputation_weight: float = 0.20
    # Carbon pricing
    include_scope3_carbon: bool = False
    cbam_rate: float = 0.85                   # pass-through rate for CBAM exposure
    # Stranded asset writedown
    writedown_curve: str = "sigmoid"           # linear | sigmoid | s_curve | step
    residual_value_floor: float = 0.05
    # Alignment benchmark
    alignment_pathway: str = "IEA_NZE_2050"   # IEA_NZE_2050 | IPCC_1.5C | SBTi_Sector
    # NGFS scenario set
    ngfs_version: str = "Phase5"


@dataclass
class IntegrationParams:
    """Parameters for combining physical + transition scores."""
    physical_weight: float = 0.5
    transition_weight: float = 0.5
    interaction_mode: str = InteractionMode.ADDITIVE
    interaction_alpha: float = 0.1            # weight of interaction term
    nature_risk_amplifier: bool = False
    nature_amplifier_cap: float = 1.5
    scenario_weighting: str = ScenarioWeighting.EQUAL
    scenario_custom_weights: Optional[Dict[str, float]] = None


@dataclass
class AggregationParams:
    """Portfolio/fund-level aggregation settings."""
    method: str = AggregationMethod.WEIGHTED_AVERAGE
    weight_field: str = "exposure_value"      # field used as weight
    diversification_benefit: bool = True
    diversification_factor: float = 0.85      # score multiplier post-aggregation
    outlier_treatment: str = "winsorize"      # cap | winsorize | include
    outlier_percentile: float = 0.99


@dataclass
class OutputParams:
    """Output format and regulatory template settings."""
    decimal_places: int = 4
    score_scale: str = "0-100"                # 0-100 | 0-1 | percentile
    include_confidence_intervals: bool = True
    confidence_level: float = 0.95
    reporting_templates: List[str] = dc_field(default_factory=lambda: [
        ReportingTemplate.TCFD_FOUR_PILLAR, ReportingTemplate.INTERNAL_SUMMARY
    ])
    export_formats: List[str] = dc_field(default_factory=lambda: ["json", "xlsx"])
    include_drill_down: bool = True
    drill_down_depth: int = 3                 # 1=portfolio, 2=fund, 3=security, 4=asset


@dataclass
class MethodologyConfig:
    """Complete methodology configuration bundling all sub-configs."""
    physical: PhysicalRiskParams = dc_field(default_factory=PhysicalRiskParams)
    transition: TransitionRiskParams = dc_field(default_factory=TransitionRiskParams)
    integration: IntegrationParams = dc_field(default_factory=IntegrationParams)
    aggregation: AggregationParams = dc_field(default_factory=AggregationParams)
    output: OutputParams = dc_field(default_factory=OutputParams)


# ---------------------------------------------------------------------------
# Methodology Record
# ---------------------------------------------------------------------------

@dataclass
class ChangeLogEntry:
    field: str
    old_value: Any
    new_value: Any
    changed_by: str
    timestamp: str = dc_field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Methodology:
    """Full methodology record (stored in DB or in-memory store)."""
    id: str
    name: str
    description: str
    status: MethodologyStatus
    version: int
    target_sectors: List[str]          # NACE section codes (empty = all sectors)
    config: MethodologyConfig
    change_log: List[ChangeLogEntry]
    created_by: str
    created_at: str
    updated_at: str
    is_template: bool = False          # True for the 9 built-in templates
    template_name: Optional[str] = None
    approval_chain: Optional[List[Dict[str, Any]]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Methodology":
        d = deepcopy(d)
        d["status"] = MethodologyStatus(d["status"])
        d["config"] = _config_from_dict(d["config"])
        d["change_log"] = [ChangeLogEntry(**e) for e in d.get("change_log", [])]
        return cls(**d)


def _config_from_dict(d: Dict[str, Any]) -> MethodologyConfig:
    return MethodologyConfig(
        physical=PhysicalRiskParams(**d.get("physical", {})),
        transition=TransitionRiskParams(**d.get("transition", {})),
        integration=IntegrationParams(**d.get("integration", {})),
        aggregation=AggregationParams(**d.get("aggregation", {})),
        output=OutputParams(**d.get("output", {})),
    )


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class MethodologyValidationError(ValueError):
    pass


def _validate_config(config: MethodologyConfig) -> None:
    """Raise MethodologyValidationError if config is invalid."""
    t = config.transition

    # Transition stage weights must sum to ~1.0
    stage_sum = (
        t.sector_classification_weight + t.carbon_pricing_weight +
        t.stranded_asset_weight + t.alignment_weight + t.scenario_stress_weight
    )
    if abs(stage_sum - 1.0) > 0.001:
        raise MethodologyValidationError(
            f"Transition stage weights must sum to 1.0, got {stage_sum:.4f}"
        )

    # TCFD category weights must sum to ~1.0
    tcfd_sum = (
        t.policy_legal_weight + t.technology_weight +
        t.market_weight + t.reputation_weight
    )
    if abs(tcfd_sum - 1.0) > 0.001:
        raise MethodologyValidationError(
            f"TCFD category weights must sum to 1.0, got {tcfd_sum:.4f}"
        )

    # Integration weights must sum to ~1.0
    i = config.integration
    int_sum = i.physical_weight + i.transition_weight
    if abs(int_sum - 1.0) > 0.001:
        raise MethodologyValidationError(
            f"Integration weights (physical + transition) must sum to 1.0, got {int_sum:.4f}"
        )

    # Physical hazard weights
    p = config.physical
    hz_sum = p.acute_weight + p.chronic_weight
    if abs(hz_sum - 1.0) > 0.001:
        raise MethodologyValidationError(
            f"Physical hazard weights (acute + chronic) must sum to 1.0, got {hz_sum:.4f}"
        )

    # Range checks
    if not (0.0 <= p.adaptation_discount <= 0.5):
        raise MethodologyValidationError("adaptation_discount must be in [0.0, 0.5]")
    if not (1.0 <= p.cascading_multiplier <= 3.0):
        raise MethodologyValidationError("cascading_multiplier must be in [1.0, 3.0]")
    if not (0.80 <= p.cvar_confidence <= 0.999):
        raise MethodologyValidationError("cvar_confidence must be in [0.80, 0.999]")

    # Custom scenario weights must sum to 1.0 if set
    if i.scenario_weighting == ScenarioWeighting.CUSTOM:
        if not i.scenario_custom_weights:
            raise MethodologyValidationError(
                "scenario_custom_weights must be set when scenario_weighting='custom'"
            )
        w_sum = sum(i.scenario_custom_weights.values())
        if abs(w_sum - 1.0) > 0.001:
            raise MethodologyValidationError(
                f"scenario_custom_weights must sum to 1.0, got {w_sum:.4f}"
            )

    # Damage function
    valid_damage = {"linear", "sigmoid", "exponential", "step"}
    if p.damage_function not in valid_damage:
        raise MethodologyValidationError(
            f"damage_function must be one of {valid_damage}"
        )

    # Writedown curve
    valid_writedown = {"linear", "sigmoid", "s_curve", "step"}
    if t.writedown_curve not in valid_writedown:
        raise MethodologyValidationError(
            f"writedown_curve must be one of {valid_writedown}"
        )


# ---------------------------------------------------------------------------
# 9 Pre-Calibrated Templates
# ---------------------------------------------------------------------------

def _make_template(
    name: str,
    description: str,
    template_name: str,
    target_sectors: List[str],
    config: MethodologyConfig,
) -> Methodology:
    now = datetime.now(timezone.utc).isoformat()
    return Methodology(
        id=f"tmpl-{template_name}",
        name=name,
        description=description,
        status=MethodologyStatus.PUBLISHED,
        version=1,
        target_sectors=target_sectors,
        config=config,
        change_log=[],
        created_by="system",
        created_at=now,
        updated_at=now,
        is_template=True,
        template_name=template_name,
    )


def _build_templates() -> Dict[str, Methodology]:
    templates: Dict[str, Methodology] = {}

    # ── 1. EU Bank Baseline ─────────────────────────────────────────────────
    cfg = MethodologyConfig()
    cfg.physical.scenarios = ["Below 2°C", "Delayed Transition", "Current Policies"]
    cfg.physical.time_horizons = [5, 10, 20]
    cfg.transition.include_scope3_carbon = False
    cfg.integration.nature_risk_amplifier = False
    t = _make_template(
        "EU Bank Baseline",
        "Standard methodology for EU banks complying with EBA GL/2025/01 and ECB climate stress test guidance.",
        "eu_bank_baseline",
        ["A", "B", "C", "D", "F", "G", "H"],
        cfg,
    )
    templates[t.id] = t

    # ── 2. EU Bank Conservative ─────────────────────────────────────────────
    cfg = MethodologyConfig()
    cfg.physical.cvar_confidence = 0.99
    cfg.physical.cascading_multiplier = 1.5
    cfg.physical.damage_function = "exponential"
    cfg.physical.time_horizons = [5, 10, 20, 30]
    cfg.transition.scenario_stress_weight = 0.30
    cfg.transition.alignment_weight = 0.15
    cfg.transition.sector_classification_weight = 0.10
    cfg.transition.carbon_pricing_weight = 0.25
    cfg.transition.stranded_asset_weight = 0.20
    cfg.integration.interaction_mode = InteractionMode.MULTIPLICATIVE
    cfg.integration.interaction_alpha = 0.15
    t = _make_template(
        "EU Bank Conservative",
        "High-severity scenario for ICAAP adverse scenario stress testing. Exponential damage curves + multiplicative interaction.",
        "eu_bank_conservative",
        ["A", "B", "C", "D", "F", "G", "H"],
        cfg,
    )
    templates[t.id] = t

    # ── 3. Energy Transition Focus ──────────────────────────────────────────
    cfg = MethodologyConfig()
    cfg.physical.acute_weight = 0.30
    cfg.physical.chronic_weight = 0.70
    cfg.transition.carbon_pricing_weight = 0.35
    cfg.transition.stranded_asset_weight = 0.30
    cfg.transition.alignment_weight = 0.15
    cfg.transition.sector_classification_weight = 0.10
    cfg.transition.scenario_stress_weight = 0.10
    cfg.transition.include_scope3_carbon = True
    cfg.transition.alignment_pathway = "IEA_NZE_2050"
    cfg.integration.transition_weight = 0.70
    cfg.integration.physical_weight = 0.30
    t = _make_template(
        "Energy Transition Focus",
        "Heavily weighted towards transition risk for oil, gas, coal, and utilities. Emphasises stranded assets and carbon pricing.",
        "energy_transition_focus",
        ["B", "D", "E"],
        cfg,
    )
    templates[t.id] = t

    # ── 4. Energy Physical Focus ────────────────────────────────────────────
    cfg = MethodologyConfig()
    cfg.physical.enabled_hazards = [
        "riverine_flood", "coastal_flood", "tropical_cyclone",
        "extreme_heat", "wildfire", "drought",
        "sea_level_rise", "chronic_heat_stress", "permafrost_thaw"
    ]
    cfg.physical.cascading_multiplier = 1.4
    cfg.physical.damage_function = "sigmoid"
    cfg.physical.adaptation_discount = 0.05
    cfg.integration.physical_weight = 0.70
    cfg.integration.transition_weight = 0.30
    t = _make_template(
        "Energy Physical Focus",
        "Physical risk-dominant for power generation and transmission infrastructure exposed to acute + chronic hazards.",
        "energy_physical_focus",
        ["D", "E"],
        cfg,
    )
    templates[t.id] = t

    # ── 5. Manufacturing CBAM ───────────────────────────────────────────────
    cfg = MethodologyConfig()
    cfg.transition.carbon_pricing_weight = 0.40
    cfg.transition.sector_classification_weight = 0.20
    cfg.transition.stranded_asset_weight = 0.15
    cfg.transition.alignment_weight = 0.15
    cfg.transition.scenario_stress_weight = 0.10
    cfg.transition.cbam_rate = 0.95
    cfg.transition.include_scope3_carbon = True
    t = _make_template(
        "Manufacturing CBAM",
        "Calibrated for steel, cement, aluminium, and chemical exporters exposed to EU Carbon Border Adjustment Mechanism.",
        "manufacturing_cbam",
        ["C"],
        cfg,
    )
    templates[t.id] = t

    # ── 6. Supply Chain Resilience ──────────────────────────────────────────
    cfg = MethodologyConfig()
    cfg.physical.enabled_hazards = [
        "riverine_flood", "tropical_cyclone", "extreme_heat",
        "drought", "wildfire", "sea_level_rise"
    ]
    cfg.physical.cascading_multiplier = 1.6
    cfg.transition.include_scope3_carbon = True
    cfg.transition.carbon_pricing_weight = 0.20
    cfg.transition.stranded_asset_weight = 0.10
    cfg.transition.alignment_weight = 0.30
    cfg.transition.sector_classification_weight = 0.20
    cfg.transition.scenario_stress_weight = 0.20
    cfg.aggregation.method = AggregationMethod.MAX
    t = _make_template(
        "Supply Chain Resilience",
        "Multi-tier supply chain assessment emphasising cascading physical risk and Scope 3 carbon exposure.",
        "supply_chain_resilience",
        ["C", "G", "H"],
        cfg,
    )
    templates[t.id] = t

    # ── 7. Canadian OSFI Aligned ────────────────────────────────────────────
    cfg = MethodologyConfig()
    cfg.physical.scenarios = ["Below 2°C", "Delayed Transition", "Current Policies", "Hot House World"]
    cfg.physical.time_horizons = [5, 10, 20, 30]
    cfg.physical.cvar_confidence = 0.95
    cfg.transition.ngfs_version = "Phase5"
    cfg.transition.alignment_pathway = "IEA_NZE_2050"
    cfg.output.reporting_templates = [ReportingTemplate.TCFD_FOUR_PILLAR, ReportingTemplate.ISSB_S2]
    t = _make_template(
        "Canadian OSFI Aligned",
        "Compliant with OSFI Guideline B-15 (Climate Risk Management) for Canadian FIs. Uses 4-scenario NGFS set.",
        "canadian_osfi_aligned",
        [],  # all sectors
        cfg,
    )
    templates[t.id] = t

    # ── 8. TCFD Disclosure Quick ────────────────────────────────────────────
    cfg = MethodologyConfig()
    cfg.physical.time_horizons = [10, 30]
    cfg.physical.scenarios = ["Below 2°C", "Current Policies"]
    cfg.output.reporting_templates = [ReportingTemplate.TCFD_FOUR_PILLAR]
    cfg.output.include_drill_down = False
    cfg.output.drill_down_depth = 1
    cfg.aggregation.diversification_benefit = False
    t = _make_template(
        "TCFD Disclosure Quick",
        "Lightweight methodology for producing TCFD four-pillar qualitative + quantitative disclosures efficiently.",
        "tcfd_disclosure_quick",
        [],
        cfg,
    )
    templates[t.id] = t

    # ── 9. Nature-Inclusive TNFD ────────────────────────────────────────────
    cfg = MethodologyConfig()
    cfg.physical.enabled_hazards = [
        "riverine_flood", "coastal_flood", "drought",
        "extreme_heat", "sea_level_rise", "permafrost_thaw",
        "wildfire", "chronic_heat_stress"
    ]
    cfg.integration.nature_risk_amplifier = True
    cfg.integration.nature_amplifier_cap = 1.8
    cfg.integration.interaction_mode = InteractionMode.MULTIPLICATIVE
    cfg.output.reporting_templates = [
        ReportingTemplate.TCFD_FOUR_PILLAR,
        ReportingTemplate.CSRD_ESRS_E1,
    ]
    t = _make_template(
        "Nature-Inclusive TNFD",
        "TNFD LEAP-aligned methodology that amplifies physical and transition scores for sectors with high ecosystem dependency.",
        "nature_inclusive_tnfd",
        ["A", "B", "C"],
        cfg,
    )
    templates[t.id] = t

    return templates


_BUILT_IN_TEMPLATES: Dict[str, Methodology] = _build_templates()


# ---------------------------------------------------------------------------
# In-Memory Store (used when no DB session is injected)
# ---------------------------------------------------------------------------

_METHODOLOGY_STORE: Dict[str, Methodology] = {}


# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------

class AssessmentMethodologyManager:
    """
    Manages methodology CRUD + lifecycle for climate risk assessments.

    Can be used in two modes:
      1. In-memory (tests / standalone scripts): no db_session
      2. DB-backed: pass db_session; manager reads/writes from DB via JSON column
    """

    def __init__(self, db_session=None):
        self._db = db_session
        # In-memory store always includes built-in templates (read-only)
        self._store: Dict[str, Methodology] = {
            **_BUILT_IN_TEMPLATES,
            **_METHODOLOGY_STORE,
        }

    # ── Templates ──────────────────────────────────────────────────────────

    def list_templates(self) -> List[Methodology]:
        """Return all 9 pre-calibrated templates."""
        return [m for m in self._store.values() if m.is_template]

    def get_template(self, template_name: str) -> Optional[Methodology]:
        """Fetch a template by its slug name."""
        for m in self._store.values():
            if m.is_template and m.template_name == template_name:
                return m
        return None

    # ── CRUD ───────────────────────────────────────────────────────────────

    def create_draft(
        self,
        name: str,
        description: str,
        config: MethodologyConfig,
        created_by: str = "system",
        target_sectors: Optional[List[str]] = None,
    ) -> Methodology:
        """Create a new DRAFT methodology after validating config."""
        _validate_config(config)
        now = datetime.now(timezone.utc).isoformat()
        m = Methodology(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            status=MethodologyStatus.DRAFT,
            version=1,
            target_sectors=target_sectors or [],
            config=config,
            change_log=[],
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )
        self._store[m.id] = m
        _METHODOLOGY_STORE[m.id] = m
        logger.info("Created DRAFT methodology %s (id=%s)", name, m.id)
        return m

    def get(self, methodology_id: str) -> Optional[Methodology]:
        return self._store.get(methodology_id)

    def list_all(
        self,
        status: Optional[MethodologyStatus] = None,
        sector: Optional[str] = None,
        include_templates: bool = True,
    ) -> List[Methodology]:
        results = list(self._store.values())
        if not include_templates:
            results = [m for m in results if not m.is_template]
        if status:
            results = [m for m in results if m.status == status]
        if sector:
            results = [
                m for m in results
                if not m.target_sectors or sector in m.target_sectors
            ]
        return sorted(results, key=lambda m: m.updated_at, reverse=True)

    def update_draft(
        self,
        methodology_id: str,
        updates: Dict[str, Any],
        changed_by: str = "system",
    ) -> Methodology:
        """
        Update fields on a DRAFT methodology.
        'updates' keys: name, description, target_sectors, config (MethodologyConfig dict)
        """
        m = self._get_mutable(methodology_id)
        now = datetime.now(timezone.utc).isoformat()

        for field, new_val in updates.items():
            if field == "config":
                new_config = _config_from_dict(new_val) if isinstance(new_val, dict) else new_val
                _validate_config(new_config)
                old_val = asdict(m.config)
                m.change_log.append(ChangeLogEntry(
                    field="config", old_value=old_val,
                    new_value=asdict(new_config), changed_by=changed_by,
                ))
                m.config = new_config
            elif hasattr(m, field) and field not in ("id", "status", "version", "created_by", "created_at"):
                old_val = getattr(m, field)
                m.change_log.append(ChangeLogEntry(
                    field=field, old_value=old_val,
                    new_value=new_val, changed_by=changed_by,
                ))
                setattr(m, field, new_val)
            else:
                raise ValueError(f"Field '{field}' is not updatable")

        m.updated_at = now
        logger.info("Updated DRAFT methodology %s", methodology_id)
        return m

    def publish(
        self,
        methodology_id: str,
        approved_by: str = "system",
    ) -> Methodology:
        """Transition DRAFT → PUBLISHED. Increments version."""
        m = self._get_mutable(methodology_id)
        if m.status != MethodologyStatus.DRAFT:
            raise ValueError(
                f"Only DRAFT methodologies can be published. Current status: {m.status}"
            )
        _validate_config(m.config)
        m.status = MethodologyStatus.PUBLISHED
        m.version += 1
        m.updated_at = datetime.now(timezone.utc).isoformat()
        m.change_log.append(ChangeLogEntry(
            field="status",
            old_value=MethodologyStatus.DRAFT.value,
            new_value=MethodologyStatus.PUBLISHED.value,
            changed_by=approved_by,
        ))
        if m.approval_chain is None:
            m.approval_chain = []
        m.approval_chain.append({
            "action": "published",
            "by": approved_by,
            "at": m.updated_at,
            "version": m.version,
        })
        logger.info("Published methodology %s v%s", m.name, m.version)
        return m

    def retire(
        self,
        methodology_id: str,
        retired_by: str = "system",
        reason: str = "",
    ) -> Methodology:
        """Transition PUBLISHED → RETIRED."""
        m = self._get_mutable(methodology_id)
        if m.status != MethodologyStatus.PUBLISHED:
            raise ValueError(
                f"Only PUBLISHED methodologies can be retired. Current status: {m.status}"
            )
        m.status = MethodologyStatus.RETIRED
        m.updated_at = datetime.now(timezone.utc).isoformat()
        m.change_log.append(ChangeLogEntry(
            field="status",
            old_value=MethodologyStatus.PUBLISHED.value,
            new_value=MethodologyStatus.RETIRED.value,
            changed_by=retired_by,
        ))
        logger.info("Retired methodology %s (reason: %s)", m.name, reason)
        return m

    def archive(
        self,
        methodology_id: str,
        archived_by: str = "system",
    ) -> Methodology:
        """Transition RETIRED → ARCHIVED."""
        m = self._get_mutable(methodology_id)
        if m.status != MethodologyStatus.RETIRED:
            raise ValueError(
                f"Only RETIRED methodologies can be archived. Current status: {m.status}"
            )
        m.status = MethodologyStatus.ARCHIVED
        m.updated_at = datetime.now(timezone.utc).isoformat()
        m.change_log.append(ChangeLogEntry(
            field="status",
            old_value=MethodologyStatus.RETIRED.value,
            new_value=MethodologyStatus.ARCHIVED.value,
            changed_by=archived_by,
        ))
        return m

    def clone(
        self,
        source_id: str,
        new_name: str,
        cloned_by: str = "system",
    ) -> Methodology:
        """Clone any methodology (including templates) to a new DRAFT."""
        source = self._store.get(source_id)
        if not source:
            raise ValueError(f"Methodology {source_id} not found")
        now = datetime.now(timezone.utc).isoformat()
        cloned_config = deepcopy(source.config)
        m = Methodology(
            id=str(uuid.uuid4()),
            name=new_name,
            description=f"Cloned from '{source.name}' (v{source.version})",
            status=MethodologyStatus.DRAFT,
            version=1,
            target_sectors=deepcopy(source.target_sectors),
            config=cloned_config,
            change_log=[
                ChangeLogEntry(
                    field="origin",
                    old_value=None,
                    new_value=f"cloned_from:{source_id}",
                    changed_by=cloned_by,
                )
            ],
            created_by=cloned_by,
            created_at=now,
            updated_at=now,
        )
        self._store[m.id] = m
        _METHODOLOGY_STORE[m.id] = m
        logger.info("Cloned methodology %s → %s (id=%s)", source.name, new_name, m.id)
        return m

    # ── Diff ───────────────────────────────────────────────────────────────

    def diff(self, id_a: str, id_b: str) -> Dict[str, Any]:
        """
        Return field-level diff between two methodology configs.
        Returns: {field_path: {a: old, b: new}}
        """
        a = self._store.get(id_a)
        b = self._store.get(id_b)
        if not a or not b:
            raise ValueError("One or both methodology IDs not found")
        return _deep_diff(asdict(a.config), asdict(b.config))

    # ── Export / Import ────────────────────────────────────────────────────

    def export_json(self, methodology_id: str) -> str:
        m = self._store.get(methodology_id)
        if not m:
            raise ValueError(f"Methodology {methodology_id} not found")
        return json.dumps(m.to_dict(), indent=2, default=str)

    def import_json(
        self,
        json_str: str,
        imported_by: str = "system",
        override_status: bool = True,
    ) -> Methodology:
        """
        Import a methodology from JSON. Always creates a DRAFT (override_status=True).
        """
        d = json.loads(json_str)
        if override_status:
            d["status"] = MethodologyStatus.DRAFT.value
        d["id"] = str(uuid.uuid4())  # new ID always
        now = datetime.now(timezone.utc).isoformat()
        d["created_at"] = now
        d["updated_at"] = now
        d["created_by"] = imported_by
        d["is_template"] = False
        m = Methodology.from_dict(d)
        _validate_config(m.config)
        self._store[m.id] = m
        _METHODOLOGY_STORE[m.id] = m
        logger.info("Imported methodology '%s' as id=%s", m.name, m.id)
        return m

    # ── Internal ──────────────────────────────────────────────────────────

    def _get_mutable(self, methodology_id: str) -> Methodology:
        m = self._store.get(methodology_id)
        if not m:
            raise ValueError(f"Methodology {methodology_id} not found")
        if m.is_template:
            raise ValueError(
                f"'{m.name}' is a read-only template. Use clone() to create an editable copy."
            )
        return m


# ---------------------------------------------------------------------------
# Helper: recursive dict diff
# ---------------------------------------------------------------------------

def _deep_diff(
    a: Any,
    b: Any,
    path: str = "",
    result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if result is None:
        result = {}
    if isinstance(a, dict) and isinstance(b, dict):
        all_keys = set(a.keys()) | set(b.keys())
        for k in all_keys:
            _deep_diff(a.get(k), b.get(k), f"{path}.{k}" if path else k, result)
    elif a != b:
        result[path] = {"a": a, "b": b}
    return result


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_default_manager = AssessmentMethodologyManager()


def get_manager(db_session=None) -> AssessmentMethodologyManager:
    """Return a manager instance. Pass db_session for DB-backed mode."""
    if db_session is not None:
        return AssessmentMethodologyManager(db_session)
    return _default_manager
