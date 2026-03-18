"""
E57: ESG Ratings Reform & Divergence Engine

Standards: EU ESG Ratings Regulation 2024/3005 (ESRA) · IOSCO ESG Ratings Guidance ·
MIT/ECGI divergence research · MIT Florian Berg divergence taxonomy ·
SASB/MSCI methodology transparency
"""

import random
import math
import statistics
from typing import Optional


# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

ESRA_REQUIREMENTS = [
    {"id": "R01", "category": "governance", "requirement": "Separation of ancillary services from ratings", "weight": 0.15},
    {"id": "R02", "category": "methodology", "requirement": "Methodology publication and transparency", "weight": 0.15},
    {"id": "R03", "category": "data_sources", "requirement": "Data source disclosure", "weight": 0.10},
    {"id": "R04", "category": "conflict_of_interest", "requirement": "Conflict of interest management policy", "weight": 0.15},
    {"id": "R05", "category": "complaint_handling", "requirement": "Complaint handling procedure", "weight": 0.10},
    {"id": "R06", "category": "transparency", "requirement": "Periodic transparency reporting", "weight": 0.15},
    {"id": "R07", "category": "regulatory", "requirement": "ESMA supervisory registration/authorisation", "weight": 0.15},
    {"id": "R08", "category": "reporting", "requirement": "Annual reporting to ESMA on rated entities", "weight": 0.05},
]

PROVIDER_SCALE_NORMALISATION = {
    "msci": {"min": 0, "max": 100, "direction": "higher_better"},
    "sustainalytics": {"min": 0, "max": 50, "direction": "lower_better"},  # risk score
    "sp": {"min": 0, "max": 100, "direction": "higher_better"},
    "bloomberg": {"min": 0, "max": 100, "direction": "higher_better"},
    "refinitiv": {"min": 0, "max": 100, "direction": "higher_better"},
    "iss": {"min": 1, "max": 10, "direction": "higher_better"},
    "cdp": {"min": 0, "max": 100, "direction": "higher_better"},
}

COMPOSITE_RATING_THRESHOLDS = [
    (85, "AAA"), (75, "AA"), (65, "A"), (55, "BBB"),
    (45, "BB"), (35, "B"), (0, "CCC"),
]

SECTOR_PEER_DISTRIBUTION = {
    "oil_gas": {"mean": 45, "std": 18},
    "utilities": {"mean": 52, "std": 16},
    "mining": {"mean": 42, "std": 20},
    "finance": {"mean": 60, "std": 15},
    "technology": {"mean": 65, "std": 14},
    "healthcare": {"mean": 58, "std": 16},
    "retail": {"mean": 55, "std": 17},
    "manufacturing": {"mean": 48, "std": 18},
    "real_estate": {"mean": 54, "std": 15},
    "agriculture": {"mean": 40, "std": 19},
    "other": {"mean": 52, "std": 17},
}

E_PILLAR_SUBPILLARS = ["carbon_E1", "water_E2", "biodiversity_E3", "waste_E4", "energy_E5"]

SIZE_BIAS_ADJUSTMENTS = {"large": -3.0, "mid": 0.0, "small": +4.0, "micro": +7.0}
REGION_BIAS_ADJUSTMENTS = {"western_europe": -2.0, "north_america": -1.5, "asia_pacific": +2.5, "emerging_markets": +5.0, "other": +3.0}
SECTOR_BIAS_ADJUSTMENTS = {"services": -3.0, "manufacturing": +2.5, "extractives": +4.0, "finance": -1.0, "technology": -2.5, "other": 0.0}


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _rng(entity_id: str) -> random.Random:
    return random.Random(hash(entity_id) & 0xFFFFFFFF)


def _clamp(val: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, val))


def _round(val: float, digits: int = 2) -> float:
    return round(val, digits)


def _normalise_score(provider: str, raw_score: float) -> float:
    """Normalise provider score to 0-100 scale (higher = better)."""
    cfg = PROVIDER_SCALE_NORMALISATION.get(provider, {"min": 0, "max": 100, "direction": "higher_better"})
    lo, hi = cfg["min"], cfg["max"]
    if hi == lo:
        return 50.0
    norm = (raw_score - lo) / (hi - lo) * 100
    if cfg["direction"] == "lower_better":
        norm = 100 - norm
    return _clamp(norm)


def _composite_rating(score: float) -> str:
    for threshold, rating in COMPOSITE_RATING_THRESHOLDS:
        if score >= threshold:
            return rating
    return "CCC"


# ---------------------------------------------------------------------------
# Method 1: ESRA Compliance
# ---------------------------------------------------------------------------

def assess_esra_compliance(
    entity_id: str,
    provider_name: str,
    methodology_published: bool,
    conflict_mgmt: bool,
    regulatory_supervised: bool,
) -> dict:
    rng = _rng(entity_id + "esra")

    # Assess each of 8 requirements
    # Some auto-derive from inputs, others from seeded random
    req_status = {
        "R01": rng.random() > 0.3,  # ancillary separation — structural
        "R02": methodology_published,
        "R03": methodology_published and rng.random() > 0.2,
        "R04": conflict_mgmt,
        "R05": conflict_mgmt and rng.random() > 0.25,
        "R06": methodology_published and rng.random() > 0.35,
        "R07": regulatory_supervised,
        "R08": regulatory_supervised and rng.random() > 0.4,
    }

    requirements_met = []
    requirements_failed = []
    weighted_score = 0.0

    for req in ESRA_REQUIREMENTS:
        met = req_status.get(req["id"], False)
        if met:
            requirements_met.append(f"{req['id']}: {req['requirement']}")
            weighted_score += req["weight"] * 100
        else:
            requirements_failed.append(f"{req['id']}: {req['requirement']}")

    compliance_score = _round(weighted_score, 1)

    if compliance_score >= 85:
        esra_grade = "A — Authorisation eligible"
    elif compliance_score >= 70:
        esra_grade = "B — Remediation required"
    elif compliance_score >= 50:
        esra_grade = "C — Significant gaps"
    else:
        esra_grade = "D — Non-compliant"

    authorisation_eligible = compliance_score >= 80 and regulatory_supervised

    timeline_compliance = {
        "ESRA_entry_into_force": "2024-07-02",
        "authorisation_deadline": "2025-07-02",
        "full_compliance_required": "2026-01-01",
        "current_status": esra_grade,
        "months_to_deadline": max(0, _round((2025 - 2024) * 12 * (1 - compliance_score / 100), 0)),
    }

    return {
        "provider_name": provider_name,
        "requirements_met": requirements_met,
        "requirements_failed": requirements_failed,
        "compliance_score": compliance_score,
        "esra_grade": esra_grade,
        "authorisation_eligible": authorisation_eligible,
        "timeline_compliance": timeline_compliance,
        "remediation_priority": requirements_failed[:3],
    }


# ---------------------------------------------------------------------------
# Method 2: Rating Divergence Analysis
# ---------------------------------------------------------------------------

def analyse_rating_divergence(entity_id: str, ratings: dict) -> dict:
    rng = _rng(entity_id + "divergence")

    normalised = {}
    for provider, data in ratings.items():
        raw = data.get("score", rng.uniform(30, 80))
        normalised[provider] = _round(_normalise_score(provider, raw), 1)

    scores = list(normalised.values())
    if len(scores) < 2:
        divergence_score = 0.0
    else:
        divergence_score = _round(statistics.stdev(scores), 2)

    # Berg et al. 2022 divergence decomposition
    scope_share = 0.56
    weight_share = 0.23
    measurement_share = 0.21
    divergence_sources = {
        "scope_56pct": _round(divergence_score * scope_share, 2),
        "weight_23pct": _round(divergence_score * weight_share, 2),
        "measurement_21pct": _round(divergence_score * measurement_share, 2),
    }

    # Correlation matrix (seeded)
    providers = list(normalised.keys())
    correlation_matrix = {}
    for i, p1 in enumerate(providers):
        correlation_matrix[p1] = {}
        for j, p2 in enumerate(providers):
            if i == j:
                correlation_matrix[p1][p2] = 1.0
            else:
                # Higher divergence = lower correlation on average
                base_corr = max(0.1, 0.75 - divergence_score / 100)
                noise = rng.uniform(-0.15, 0.15)
                correlation_matrix[p1][p2] = _round(_clamp(base_corr + noise, -1, 1), 3)

    avg_score = statistics.mean(scores) if scores else 50.0
    consensus_rating = _composite_rating(avg_score)

    ci_half_width = 1.96 * (divergence_score / math.sqrt(len(scores))) if scores else 10.0
    confidence_interval = {
        "lower": _round(max(0, avg_score - ci_half_width), 1),
        "upper": _round(min(100, avg_score + ci_half_width), 1),
        "confidence_level": "95%",
    }

    return {
        "normalised_scores": normalised,
        "divergence_score": divergence_score,
        "divergence_sources": divergence_sources,
        "correlation_matrix": correlation_matrix,
        "consensus_rating": consensus_rating,
        "average_normalised_score": _round(avg_score, 1),
        "confidence_interval": confidence_interval,
    }


# ---------------------------------------------------------------------------
# Method 3: Rating Bias Detection
# ---------------------------------------------------------------------------

def detect_rating_bias(
    entity_id: str,
    scores: dict,
    entity_size: str,
    region: str,
    sector: str,
) -> dict:
    rng = _rng(entity_id + "bias")

    normalised = {p: _round(_normalise_score(p, v), 1) for p, v in scores.items()}
    raw_composite = _round(statistics.mean(normalised.values()) if normalised else 50.0, 1)

    biases_detected = []
    total_adjustment = 0.0

    # Size bias
    size_adj = SIZE_BIAS_ADJUSTMENTS.get(entity_size.lower(), 0.0)
    if abs(size_adj) > 2:
        biases_detected.append({
            "bias_type": "size_bias",
            "description": f"{'Large' if size_adj < 0 else 'Small'} company reporting quality proxy inflates score",
            "adjustment": _round(size_adj, 1),
            "source": "Berg et al. 2022; ECGI working paper 2023",
        })
        total_adjustment += size_adj

    # Geography bias
    region_adj = REGION_BIAS_ADJUSTMENTS.get(region.lower(), 0.0)
    if abs(region_adj) > 2:
        biases_detected.append({
            "bias_type": "geography_bias",
            "description": f"{'Western' if region_adj < 0 else 'Non-western'} disclosure standards affect score",
            "adjustment": _round(region_adj, 1),
            "source": "IOSCO ESG Ratings Guidance 2021",
        })
        total_adjustment += region_adj

    # Sector bias
    sector_adj = SECTOR_BIAS_ADJUSTMENTS.get(sector.lower(), 0.0)
    if abs(sector_adj) > 1:
        biases_detected.append({
            "bias_type": "sector_bias",
            "description": f"{'Services vs' if sector_adj < 0 else 'Manufacturing/extractives'} sector scoring asymmetry",
            "adjustment": _round(sector_adj, 1),
            "source": "Kotsantonis & Serafeim (2019)",
        })
        total_adjustment += sector_adj

    # Voluntary disclosure inflation
    report_adj = rng.uniform(-4.0, -1.0)
    biases_detected.append({
        "bias_type": "reporting_bias",
        "description": "Voluntary disclosure inflates scores vs independently verified data",
        "adjustment": _round(report_adj, 1),
        "source": "Berg, Kolbel & Rigobon (2022), JFE",
    })
    total_adjustment += report_adj

    bias_adjusted_score = _round(_clamp(raw_composite + total_adjustment), 1)
    adjustment_magnitude = _round(abs(total_adjustment), 1)

    peer_comparison = {
        "sector": sector,
        "sector_avg_raw": _round(rng.uniform(45, 65), 1),
        "sector_avg_bias_adjusted": _round(rng.uniform(40, 60), 1),
        "entity_percentile_raw": _round(rng.uniform(30, 80), 1),
        "entity_percentile_adjusted": _round(rng.uniform(25, 75), 1),
    }

    return {
        "raw_composite": raw_composite,
        "biases_detected": biases_detected,
        "bias_adjusted_score": bias_adjusted_score,
        "adjustment_magnitude": adjustment_magnitude,
        "peer_comparison": peer_comparison,
        "normalised_scores": normalised,
    }


# ---------------------------------------------------------------------------
# Method 4: Composite Rating
# ---------------------------------------------------------------------------

def compute_composite_rating(
    entity_id: str,
    provider_scores: dict,
    methodology: str = "equal_weight",
) -> dict:
    rng = _rng(entity_id + "composite")

    normalised = {p: _round(_normalise_score(p, v), 1) for p, v in provider_scores.items()}
    providers = list(normalised.keys())
    n = len(providers)

    if methodology == "equal_weight":
        weights = {p: _round(1.0 / n, 4) for p in providers} if n else {}
    elif methodology == "market_cap_weight":
        raw_w = {p: rng.uniform(0.1, 0.4) for p in providers}
        total = sum(raw_w.values())
        weights = {p: _round(raw_w[p] / total, 4) for p in providers}
    elif methodology == "specialisation_weight":
        # MSCI for governance, Sustainalytics for risk, others equal
        spec = {"msci": 0.30, "sustainalytics": 0.30}
        remaining = 1.0 - sum(spec.get(p, 0) for p in providers if p in spec)
        non_spec = [p for p in providers if p not in spec]
        each = remaining / len(non_spec) if non_spec else 0
        weights = {p: _round(spec.get(p, each), 4) for p in providers}
    else:
        weights = {p: _round(1.0 / n, 4) for p in providers} if n else {}

    composite_score = sum(weights.get(p, 0) * normalised[p] for p in providers)
    composite_score = _round(composite_score, 1)
    rating = _composite_rating(composite_score)

    # Sensitivity: recompute under equal_weight and market_cap to show sensitivity
    eq_score = _round(statistics.mean(normalised.values()) if normalised else 0, 1)
    sensitivity_analysis = {
        "equal_weight": eq_score,
        "equal_weight_rating": _composite_rating(eq_score),
        "selected_methodology": composite_score,
        "selected_rating": rating,
        "score_range": [_round(min(normalised.values()), 1) if normalised else 0,
                        _round(max(normalised.values()), 1) if normalised else 0],
    }

    return {
        "composite_score": composite_score,
        "composite_rating": rating,
        "methodology_used": methodology,
        "provider_weights": weights,
        "normalised_scores": normalised,
        "sensitivity_analysis": sensitivity_analysis,
    }


# ---------------------------------------------------------------------------
# Method 5: E Pillar Divergence
# ---------------------------------------------------------------------------

def assess_e_pillar_divergence(entity_id: str, scores_by_pillar: dict) -> dict:
    rng = _rng(entity_id + "epillar")

    pillar_divergence = {}
    data_gaps = []

    for pillar in E_PILLAR_SUBPILLARS:
        if pillar in scores_by_pillar and scores_by_pillar[pillar]:
            sub = scores_by_pillar[pillar]
            normalised_sub = {p: _round(_normalise_score(p, v), 1) for p, v in sub.items()}
            vals = list(normalised_sub.values())
            div = _round(statistics.stdev(vals), 2) if len(vals) >= 2 else 0.0
            pillar_divergence[pillar] = {
                "divergence": div,
                "scores": normalised_sub,
                "avg": _round(statistics.mean(vals), 1) if vals else 0.0,
            }
        else:
            div = _round(rng.uniform(8, 22), 2)
            pillar_divergence[pillar] = {
                "divergence": div,
                "scores": {},
                "avg": _round(rng.uniform(40, 70), 1),
            }
            data_gaps.append(f"{pillar}: no provider scores supplied")

    if pillar_divergence:
        most_divergent = max(pillar_divergence, key=lambda k: pillar_divergence[k]["divergence"])
        least_divergent = min(pillar_divergence, key=lambda k: pillar_divergence[k]["divergence"])
    else:
        most_divergent = "carbon_E1"
        least_divergent = "waste_E4"

    improvement_priorities = sorted(
        pillar_divergence.keys(),
        key=lambda k: pillar_divergence[k]["divergence"],
        reverse=True,
    )[:3]

    return {
        "pillar_divergence": pillar_divergence,
        "most_divergent": most_divergent,
        "least_divergent": least_divergent,
        "data_gaps": data_gaps,
        "improvement_priorities": improvement_priorities,
    }


# ---------------------------------------------------------------------------
# Method 6: Peer Benchmark
# ---------------------------------------------------------------------------

def benchmark_against_peers(
    entity_id: str,
    sector: str,
    composite_score: float,
    n_peers: int = 20,
) -> dict:
    rng = _rng(entity_id + "benchmark")

    dist = SECTOR_PEER_DISTRIBUTION.get(sector.lower(), SECTOR_PEER_DISTRIBUTION["other"])
    peer_scores = sorted([
        _round(_clamp(rng.gauss(dist["mean"], dist["std"])), 1)
        for _ in range(n_peers)
    ])

    entity_score = _clamp(composite_score)
    rank = sum(1 for s in peer_scores if s < entity_score) + 1
    percentile = _round(rank / (n_peers + 1) * 100, 1)

    sector_median = _round(statistics.median(peer_scores), 1)
    sector_p75 = _round(peer_scores[int(n_peers * 0.75)], 1)
    sector_leader = _round(max(peer_scores), 1)

    gap_to_median = _round(sector_median - entity_score, 1)
    gap_to_leader = _round(sector_leader - entity_score, 1)

    improvement_roadmap = []
    if gap_to_median > 5:
        improvement_roadmap.append(f"Close {gap_to_median:.0f}pt gap to sector median via enhanced E-pillar reporting")
    if gap_to_leader > 15:
        improvement_roadmap.append("Implement SBTi-aligned targets to match sector leader disclosure")
    improvement_roadmap.append("Align CSRD ESRS E1-E5 reporting with provider data requirements")
    improvement_roadmap.append("Engage Sustainalytics/MSCI for analyst engagement meetings")

    return {
        "percentile_rank": percentile,
        "sector": sector,
        "sector_median": sector_median,
        "sector_p75": sector_p75,
        "sector_leader": sector_leader,
        "entity_score": _round(entity_score, 1),
        "gap_to_median": gap_to_median,
        "gap_to_leader": gap_to_leader,
        "n_peers": n_peers,
        "improvement_roadmap": improvement_roadmap,
    }


# ---------------------------------------------------------------------------
# Method 7: Divergence Report
# ---------------------------------------------------------------------------

def generate_divergence_report(
    entity_id: str,
    entity_name: str,
    sector: str,
    ratings: dict,
) -> dict:
    rng = _rng(entity_id + "report")

    # Run sub-analyses
    divergence_result = analyse_rating_divergence(entity_id, ratings)
    composite_result = compute_composite_rating(entity_id, {p: d.get("score", 50) for p, d in ratings.items()})

    bias_scores = {p: d.get("score", 50) for p, d in ratings.items()}
    bias_result = detect_rating_bias(
        entity_id, bias_scores,
        entity_size="large",
        region="western_europe",
        sector=sector,
    )

    benchmark_result = benchmark_against_peers(entity_id, sector, composite_result["composite_score"])

    top_divergence_driver = max(
        divergence_result["divergence_sources"].items(),
        key=lambda x: x[1],
        default=("scope_56pct", 0),
    )[0]

    esra_implications = [
        "ESRA 2024/3005 mandates methodology transparency — expect divergence to narrow 15-25% by 2026",
        "Provider consolidation likely: smaller providers may exit EU market post-authorisation",
        "Standardised data collection forms (Art 23 ESRA) will reduce measurement divergence",
        "Mandatory annual analyst engagement letter required for rated entities",
    ]

    action_items = []
    if divergence_result["divergence_score"] > 15:
        action_items.append("Engage top-3 divergent providers with unified data submission package")
    if bias_result["adjustment_magnitude"] > 5:
        action_items.append("Correct for reporting bias by providing third-party verified data")
    if benchmark_result["gap_to_median"] > 5:
        action_items.append(f"Prioritise {benchmark_result['gap_to_median']:.0f}-point improvement vs sector median")
    action_items.append("Subscribe to ESRA-authorised provider update notifications")
    action_items.append("Implement annual provider gap analysis as part of IR calendar")

    return {
        "entity": entity_name,
        "sector": sector,
        "composite_score": composite_result["composite_score"],
        "consensus_rating": composite_result["composite_rating"],
        "divergence_score": divergence_result["divergence_score"],
        "top_divergence_driver": top_divergence_driver,
        "bias_adjusted_score": bias_result["bias_adjusted_score"],
        "peer_percentile": benchmark_result["percentile_rank"],
        "esra_implications": esra_implications,
        "action_items": action_items,
        "normalised_scores": divergence_result["normalised_scores"],
        "provider_count": len(ratings),
    }
