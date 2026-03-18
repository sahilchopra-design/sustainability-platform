"""
DME Policy Velocity Tracker — Rate of regulatory change across 4 component signals.

Components:
  1. Carbon Price velocity — d(ETS_Price)/dt × Embedded_Emissions_Volume
  2. Regulatory Pipeline velocity — stage-weighted bill activity (introduced × 0.2, committee × 0.3, enacted × 0.5)
  3. Enforcement velocity — sanctions + litigation + penalty magnitude
  4. Disclosure Mandate velocity — jurisdiction adoption rate × GDP coverage amplifier

Composite: v_policy = Σ(v_i × w_i) with sector-specific component weights (ISIC-based).

Ported from DME (Dynamic Materiality Engine) into Risk Analytics.
"""
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


# ── Enums & Constants ────────────────────────────────────────────────────────

class PolicyComponent(str, Enum):
    CARBON_PRICE = "carbon_price"
    REGULATORY_PIPELINE = "regulatory_pipeline"
    ENFORCEMENT = "enforcement"
    DISCLOSURE_MANDATE = "disclosure_mandate"


# Sector-specific component weights (ISIC 4-digit codes)
SECTOR_WEIGHTS: Dict[str, Dict[PolicyComponent, float]] = {
    "6419": {  # Banking / Other monetary intermediation
        PolicyComponent.CARBON_PRICE: 0.20,
        PolicyComponent.REGULATORY_PIPELINE: 0.35,
        PolicyComponent.ENFORCEMENT: 0.30,
        PolicyComponent.DISCLOSURE_MANDATE: 0.15,
    },
    "0610": {  # Crude petroleum extraction
        PolicyComponent.CARBON_PRICE: 0.40,
        PolicyComponent.REGULATORY_PIPELINE: 0.25,
        PolicyComponent.ENFORCEMENT: 0.15,
        PolicyComponent.DISCLOSURE_MANDATE: 0.20,
    },
    "3510": {  # Electric power generation
        PolicyComponent.CARBON_PRICE: 0.45,
        PolicyComponent.REGULATORY_PIPELINE: 0.25,
        PolicyComponent.ENFORCEMENT: 0.10,
        PolicyComponent.DISCLOSURE_MANDATE: 0.20,
    },
    "2410": {  # Iron & steel manufacturing
        PolicyComponent.CARBON_PRICE: 0.35,
        PolicyComponent.REGULATORY_PIPELINE: 0.25,
        PolicyComponent.ENFORCEMENT: 0.20,
        PolicyComponent.DISCLOSURE_MANDATE: 0.20,
    },
    "4100": {  # Real estate / construction
        PolicyComponent.CARBON_PRICE: 0.15,
        PolicyComponent.REGULATORY_PIPELINE: 0.30,
        PolicyComponent.ENFORCEMENT: 0.25,
        PolicyComponent.DISCLOSURE_MANDATE: 0.30,
    },
    "default": {
        PolicyComponent.CARBON_PRICE: 0.25,
        PolicyComponent.REGULATORY_PIPELINE: 0.25,
        PolicyComponent.ENFORCEMENT: 0.25,
        PolicyComponent.DISCLOSURE_MANDATE: 0.25,
    },
}


# ── Pydantic schemas ────────────────────────────────────────────────────────

class CarbonPriceInput(BaseModel):
    prices: List[Tuple[datetime, float]] = Field(description="(timestamp, price_usd) pairs")
    embedded_emissions_volume: float = Field(1.0, ge=0)


class RegulatoryPipelineInput(BaseModel):
    bills_introduced: int = Field(0, ge=0)
    bills_in_committee: int = Field(0, ge=0)
    bills_enacted: int = Field(0, ge=0)
    time_period_years: float = Field(1.0, gt=0)


class EnforcementInput(BaseModel):
    sanctions_per_month: float = Field(0, ge=0)
    litigation_filings_per_quarter: float = Field(0, ge=0)
    penalty_magnitude_log: float = Field(0, ge=0, description="log10(total penalties)")


class DisclosureMandateInput(BaseModel):
    new_adoptions_per_month: float = Field(0, ge=0)
    cumulative_coverage_fraction: float = Field(0, ge=0, le=1, description="GDP coverage [0,1]")


class CompositeVelocityRequest(BaseModel):
    jurisdiction: str
    sector_isic: str = "default"
    carbon: Optional[CarbonPriceInput] = None
    regulatory: Optional[RegulatoryPipelineInput] = None
    enforcement: Optional[EnforcementInput] = None
    disclosure: Optional[DisclosureMandateInput] = None


class PolicyEventInput(BaseModel):
    name: str
    jurisdiction: str
    component: PolicyComponent
    delta_policy: float = Field(ge=0, le=1)
    weight: float = Field(ge=0, le=1)
    direction: int = Field(ge=-1, le=1)
    confidence: float = Field(ge=0, le=1)
    effective_date: Optional[datetime] = None


class PolicyEventBatchRequest(BaseModel):
    jurisdiction: str
    sector_isic: str = "default"
    events: List[PolicyEventInput]
    time_period_years: float = Field(1.0, gt=0)


# ── Engine ───────────────────────────────────────────────────────────────────

class PolicyTrackerEngine:
    """Stateless policy velocity calculation engine."""

    @staticmethod
    def get_sector_weights(isic_code: str) -> Dict[PolicyComponent, float]:
        return SECTOR_WEIGHTS.get(isic_code, SECTOR_WEIGHTS["default"])

    @staticmethod
    def carbon_price_velocity(inp: CarbonPriceInput) -> float:
        """d(ETS_Price)/dt × Embedded_Emissions_Volume"""
        if len(inp.prices) < 2:
            return 0.0
        pct_changes = []
        for i in range(1, len(inp.prices)):
            _, p_prev = inp.prices[i - 1]
            _, p_curr = inp.prices[i]
            if p_prev > 0:
                pct_changes.append((p_curr - p_prev) / p_prev)
        return float(np.mean(pct_changes)) * inp.embedded_emissions_volume if pct_changes else 0.0

    @staticmethod
    def regulatory_pipeline_velocity(inp: RegulatoryPipelineInput) -> float:
        """Stage-weighted: introduced × 0.2, committee × 0.3, enacted × 0.5"""
        weighted = inp.bills_introduced * 0.2 + inp.bills_in_committee * 0.3 + inp.bills_enacted * 0.5
        return weighted / inp.time_period_years

    @staticmethod
    def enforcement_velocity(inp: EnforcementInput) -> float:
        """sanctions(0.4) + litigation_monthly(0.4) + penalty_log(0.2)"""
        lit_monthly = inp.litigation_filings_per_quarter / 3.0
        return inp.sanctions_per_month * 0.4 + lit_monthly * 0.4 + inp.penalty_magnitude_log * 0.2

    @staticmethod
    def disclosure_mandate_velocity(inp: DisclosureMandateInput) -> float:
        """adoptions/month × (1 + coverage_fraction)"""
        return inp.new_adoptions_per_month * (1 + inp.cumulative_coverage_fraction)

    @staticmethod
    def composite_velocity(req: CompositeVelocityRequest) -> Dict:
        """Calculate full composite policy velocity index."""
        weights = PolicyTrackerEngine.get_sector_weights(req.sector_isic)

        v_carbon = PolicyTrackerEngine.carbon_price_velocity(req.carbon) if req.carbon else 0.0
        v_reg = PolicyTrackerEngine.regulatory_pipeline_velocity(req.regulatory) if req.regulatory else 0.0
        v_enf = PolicyTrackerEngine.enforcement_velocity(req.enforcement) if req.enforcement else 0.0
        v_disc = PolicyTrackerEngine.disclosure_mandate_velocity(req.disclosure) if req.disclosure else 0.0

        v_composite = (
            v_carbon * weights[PolicyComponent.CARBON_PRICE]
            + v_reg * weights[PolicyComponent.REGULATORY_PIPELINE]
            + v_enf * weights[PolicyComponent.ENFORCEMENT]
            + v_disc * weights[PolicyComponent.DISCLOSURE_MANDATE]
        )

        return {
            "jurisdiction": req.jurisdiction,
            "sector_isic": req.sector_isic,
            "carbon_price_velocity": round(v_carbon, 6),
            "regulatory_pipeline_velocity": round(v_reg, 4),
            "enforcement_velocity": round(v_enf, 4),
            "disclosure_mandate_velocity": round(v_disc, 4),
            "composite_velocity": round(v_composite, 6),
            "sector_weights": {k.value: v for k, v in weights.items()},
        }

    @staticmethod
    def from_events(req: PolicyEventBatchRequest) -> Dict:
        """Calculate composite velocity from discrete policy events."""
        weights = PolicyTrackerEngine.get_sector_weights(req.sector_isic)
        component_sums: Dict[PolicyComponent, float] = {c: 0.0 for c in PolicyComponent}

        for evt in req.events:
            component_sums[evt.component] += evt.delta_policy * evt.weight * evt.direction * evt.confidence

        # Normalise to annual velocity
        for c in component_sums:
            component_sums[c] /= req.time_period_years

        v_composite = sum(component_sums[c] * weights[c] for c in PolicyComponent)

        return {
            "jurisdiction": req.jurisdiction,
            "sector_isic": req.sector_isic,
            "event_count": len(req.events),
            "component_velocities": {c.value: round(v, 6) for c, v in component_sums.items()},
            "composite_velocity": round(v_composite, 6),
            "sector_weights": {k.value: v for k, v in weights.items()},
        }

    @staticmethod
    def get_reference_data() -> Dict:
        """Reference: sector weights and component descriptions."""
        return {
            "components": [
                {"id": c.value, "description": {
                    "carbon_price": "d(ETS_Price)/dt × Embedded_Emissions_Volume",
                    "regulatory_pipeline": "Stage-weighted bill activity (introduced 0.2, committee 0.3, enacted 0.5)",
                    "enforcement": "Sanctions + litigation + penalty magnitude",
                    "disclosure_mandate": "Jurisdiction adoptions × GDP coverage amplifier",
                }[c.value]} for c in PolicyComponent
            ],
            "sector_weights": {
                k: {c.value: w for c, w in v.items()} for k, v in SECTOR_WEIGHTS.items()
            },
        }
