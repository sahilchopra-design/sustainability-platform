"""
DME Contagion Engine — Hawkes Process Multi-Layer Systemic Risk.

Three layers with different time-bases and kernel functions:
  Layer 1: Entity-to-Entity (daily)  — exponential kernel
  Layer 2: Structural Cascade (monthly) — exponential (acute) + power-law (chronic)
  Layer 3: Capital Flight (weekly) — cross-sector herding with self-excitation

Systemic Risk Aggregator normalises to daily base and computes amplification factors.
Empirical targets: EL ×4.3, VaR ×4.5, ES ×3.2 (±10%).

Ported from DME (Dynamic Materiality Engine) into Risk Analytics.
"""
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pydantic import BaseModel, Field


# ── Pydantic schemas ────────────────────────────────────────────────────────

class EdgeWeightInput(BaseModel):
    ead_exposure: float = Field(ge=0)
    portfolio_total: float = Field(gt=0)
    hhi_concentration: float = Field(ge=0, le=1)
    revenue_share: float = Field(ge=0, le=1)
    substitutability: float = Field(ge=0, le=1)
    jurisdiction_overlap: float = Field(ge=0, le=1, description="Jaccard coefficient")
    gics_similarity: float = Field(ge=0, le=1)


class EdgeWeightOutput(BaseModel):
    financial: float
    supply_chain: float
    regulatory: float
    composite: float


class ContagionEvent(BaseModel):
    entity_id: str
    timestamp: datetime
    event_type: str
    severity: float = Field(ge=0, le=1)
    pillar: Optional[str] = None  # E/S/G/X


class L1IntensityRequest(BaseModel):
    target_entity_id: str
    mu_baseline: float = Field(0.05, ge=0)
    beta_decay: float = Field(0.5, gt=0)
    events: List[Tuple[datetime, float, float]]  # (timestamp, edge_weight, severity)
    current_time: datetime


class L2IntensityRequest(BaseModel):
    mu_current: float = Field(0.02, ge=0)
    events: List[Tuple[datetime, str, float]]  # (timestamp, event_type, magnitude)
    current_time: datetime
    beta_exponential: float = 0.15
    alpha_exponential: float = 0.6
    power_law_C: float = 1.0
    power_law_tau: float = 1.0
    power_law_gamma: float = 0.5


class L3IntensityRequest(BaseModel):
    target_sector: str
    events_by_sector: Dict[str, List[Tuple[datetime, float]]]
    current_time: datetime
    mu_baseline: float = Field(0.03, ge=0)
    beta_decay: float = Field(0.3, gt=0)


class AggregationRequest(BaseModel):
    lambda_L1_daily: float
    lambda_L2_monthly: float
    lambda_L3_weekly: float
    lambda_baseline: float = Field(0.05, gt=0)
    contagion_ratio: float = Field(0.0, ge=0)
    source_pillar: str = "E"
    target_pillar: str = "E"
    layer_weights: Optional[Dict[str, float]] = None


class StabilityCheckRequest(BaseModel):
    """Adjacency matrix for spectral radius check."""
    adjacency_matrix: List[List[float]]
    beta_decay: float = Field(0.5, gt=0)


class FullSimulationRequest(BaseModel):
    """End-to-end contagion simulation."""
    seed_entity_id: str
    seed_severity: float = Field(0.8, ge=0, le=1)
    seed_event_type: str = "REGULATORY_SHOCK"
    adjacency_matrix: List[List[float]]
    entity_ids: List[str]
    beta_decay: float = 0.5
    mu_baseline: float = 0.05
    cascade_steps: int = Field(5, ge=1, le=20)
    scenario: str = "base"


# ── Engine ───────────────────────────────────────────────────────────────────

CHANNEL_WEIGHTS = {"financial": 0.45, "supply_chain": 0.35, "regulatory": 0.20}

CROSS_PILLAR_AMP = {
    "G_to_E": 2.5, "X_to_EL": 4.3, "X_to_VaR": 4.5, "X_to_ES": 3.2,
    "S_to_P": 2.3, "same_pillar": 1.0,
}

CROSS_SECTOR_DEFAULTS = {
    ("Energy", "Energy"): 0.35, ("Energy", "Materials"): 0.25, ("Energy", "Industrials"): 0.15,
    ("Financials", "Financials"): 0.40, ("Financials", "RealEstate"): 0.20,
}


class ContagionEngine:
    """Stateless Hawkes-process contagion engine."""

    # ── Edge weight ──────────────────────────────────────────────────────────

    @staticmethod
    def compute_edge_weight(inp: EdgeWeightInput) -> EdgeWeightOutput:
        alpha, gamma, theta1, theta2 = 0.7, 0.3, 0.5, 0.5
        w_fin = alpha * (inp.ead_exposure / inp.portfolio_total) * (1 + gamma * inp.hhi_concentration)
        w_sc = inp.revenue_share * (1 - inp.substitutability)
        w_reg = theta1 * inp.jurisdiction_overlap + theta2 * inp.gics_similarity
        composite = (
            CHANNEL_WEIGHTS["financial"] * w_fin
            + CHANNEL_WEIGHTS["supply_chain"] * w_sc
            + CHANNEL_WEIGHTS["regulatory"] * w_reg
        )
        return EdgeWeightOutput(financial=w_fin, supply_chain=w_sc, regulatory=w_reg, composite=composite)

    # ── Layer 1: Entity-to-Entity ────────────────────────────────────────────

    @staticmethod
    def l1_intensity(req: L1IntensityRequest) -> Dict:
        excitation = 0.0
        for evt_time, edge_w, sev in req.events:
            if evt_time < req.current_time:
                dt_days = (req.current_time - evt_time).total_seconds() / 86400
                excitation += edge_w * sev * float(np.exp(-req.beta_decay * dt_days))
        intensity = req.mu_baseline + excitation
        return {
            "entity_id": req.target_entity_id,
            "layer": "L1_ENTITY",
            "intensity": round(intensity, 6),
            "baseline": req.mu_baseline,
            "excitation": round(excitation, 6),
            "events_considered": len(req.events),
        }

    # ── Layer 2: Structural Cascade ──────────────────────────────────────────

    @staticmethod
    def l2_intensity(req: L2IntensityRequest) -> Dict:
        intensity = req.mu_current
        for evt_time, evt_type, mag in req.events:
            if evt_time < req.current_time:
                dt_months = (req.current_time - evt_time).days / 30.0
                if evt_type in ("PHYSICAL_ACUTE", "SUPPLY_DISRUPTION"):
                    kernel = req.alpha_exponential * float(np.exp(-req.beta_exponential * dt_months))
                else:
                    kernel = req.power_law_C * ((dt_months + req.power_law_tau) ** (-(1 + req.power_law_gamma)))
                intensity += kernel * mag
        return {
            "layer": "L2_STRUCTURAL",
            "intensity": round(intensity, 6),
            "baseline": req.mu_current,
            "events_considered": len(req.events),
        }

    # ── Layer 3: Capital Flight ──────────────────────────────────────────────

    @staticmethod
    def l3_intensity(req: L3IntensityRequest) -> Dict:
        intensity = req.mu_baseline
        for src_sector, events in req.events_by_sector.items():
            alpha_kj = CROSS_SECTOR_DEFAULTS.get((src_sector, req.target_sector), 0.1)
            for evt_time, mag in events:
                if evt_time < req.current_time:
                    dt_weeks = (req.current_time - evt_time).days / 7.0
                    intensity += alpha_kj * float(np.exp(-req.beta_decay * dt_weeks)) * mag
        return {
            "target_sector": req.target_sector,
            "layer": "L3_CAPITAL_FLIGHT",
            "intensity": round(intensity, 6),
            "baseline": req.mu_baseline,
        }

    # ── Aggregation & Amplification ──────────────────────────────────────────

    @staticmethod
    def aggregate(req: AggregationRequest) -> Dict:
        lw = req.layer_weights or {"L1": 0.40, "L2": 0.35, "L3": 0.25}
        l2_daily = req.lambda_L2_monthly / 21.0
        l3_daily = req.lambda_L3_weekly / 5.0
        agg = lw["L1"] * req.lambda_L1_daily + lw["L2"] * l2_daily + lw["L3"] * l3_daily

        base_amp = 1 + (agg / req.lambda_baseline - 1) if req.lambda_baseline > 0 else 1.0
        contagion_comp = 1 + req.contagion_ratio

        # Cross-pillar
        sp, tp = req.source_pillar, req.target_pillar
        if sp == tp:
            xp = CROSS_PILLAR_AMP["same_pillar"]
        elif sp == "G" and tp == "E":
            xp = CROSS_PILLAR_AMP["G_to_E"]
        elif sp == "S" and tp == "P":
            xp = CROSS_PILLAR_AMP["S_to_P"]
        else:
            xp = 1.0

        el_amp = contagion_comp * (CROSS_PILLAR_AMP["X_to_EL"] if sp == "X" else xp)
        var_amp = contagion_comp * (CROSS_PILLAR_AMP["X_to_VaR"] if sp == "X" else xp)
        es_amp = contagion_comp * (CROSS_PILLAR_AMP["X_to_ES"] if sp == "X" else xp)

        return {
            "aggregated_daily_intensity": round(agg, 6),
            "base_amplification": round(base_amp, 4),
            "el_amplification": round(el_amp, 4),
            "var_amplification": round(var_amp, 4),
            "es_amplification": round(es_amp, 4),
            "layer_weights": lw,
        }

    # ── Stability Check ──────────────────────────────────────────────────────

    @staticmethod
    def check_stability(req: StabilityCheckRequest) -> Dict:
        W = np.array(req.adjacency_matrix)
        branching = W / req.beta_decay
        eigenvalues = np.linalg.eigvals(branching)
        sr = float(np.max(np.abs(eigenvalues)))
        return {"is_stable": sr < 1.0, "spectral_radius": round(sr, 6), "matrix_size": W.shape[0]}

    # ── Full Simulation ──────────────────────────────────────────────────────

    @staticmethod
    def simulate(req: FullSimulationRequest) -> Dict:
        """Simple cascade simulation: propagate from seed through adjacency."""
        W = np.array(req.adjacency_matrix)
        n = len(req.entity_ids)
        if W.shape != (n, n):
            return {"error": f"Matrix shape {W.shape} != entity count {n}"}

        seed_idx = req.entity_ids.index(req.seed_entity_id) if req.seed_entity_id in req.entity_ids else 0
        intensities = np.full(n, req.mu_baseline)
        intensities[seed_idx] += req.seed_severity

        affected = {seed_idx}
        cascade_log = []

        for step in range(req.cascade_steps):
            new_intensities = intensities.copy()
            for i in range(n):
                excitation = sum(W[j, i] * intensities[j] * float(np.exp(-req.beta_decay * (step + 1)))
                                 for j in affected)
                new_intensities[i] += excitation
                if excitation > 0.01:
                    affected.add(i)
            cascade_log.append({
                "step": step + 1,
                "entities_affected": len(affected),
                "max_intensity": round(float(np.max(new_intensities)), 6),
                "total_intensity": round(float(np.sum(new_intensities)), 6),
            })
            intensities = new_intensities

        # Stability
        branching = W / req.beta_decay
        sr = float(np.max(np.abs(np.linalg.eigvals(branching))))

        return {
            "scenario": req.scenario,
            "seed_entity_id": req.seed_entity_id,
            "seed_event_type": req.seed_event_type,
            "cascade_depth": req.cascade_steps,
            "entities_affected": len(affected),
            "total_intensity": round(float(np.sum(intensities)), 6),
            "spectral_radius": round(sr, 6),
            "is_stable": sr < 1.0,
            "cascade_log": cascade_log,
            "final_intensities": {req.entity_ids[i]: round(float(intensities[i]), 6) for i in range(n)},
        }

    @staticmethod
    def get_reference_data() -> Dict:
        return {
            "channel_weights": CHANNEL_WEIGHTS,
            "cross_pillar_amplifiers": CROSS_PILLAR_AMP,
            "cross_sector_defaults": {f"{k[0]}->{k[1]}": v for k, v in CROSS_SECTOR_DEFAULTS.items()},
            "empirical_targets": {"EL": 4.3, "VaR": 4.5, "ES": 3.2, "tolerance": "±10%"},
        }
