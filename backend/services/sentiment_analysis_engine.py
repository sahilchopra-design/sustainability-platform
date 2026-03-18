"""
Sentiment Analysis Engine — Multi-Stakeholder Signal Processing
================================================================
Standalone module that aggregates sentiment signals from public datapoints,
social media, news, regulatory filings, NGO reports, and other validated
sources.  Produces entity-level and topic-level sentiment scores with
velocity tracking and alert generation.

Architecture
------------
  Inbound feeds (consume FROM):
    - NLP Pulse Engine (DME)          → processed NLP signals
    - Greenwashing Engine (DME)       → credibility-adjusted divergence flags
    - GDELT Controversy Service       → global event controversy scores
    - CSRD Entity Registry            → entity metadata for matching
    - Company Profiles                → LEI, ISIN, sector for enrichment
    - Regulatory Report Compiler      → regulatory filing sentiment
    - CA100+ / Engagement Tracker     → engagement outcome signals
    - Factor Overlay Engine           → ESG factor context

  Outbound feeds (produce FOR):
    - ECL / Credit Risk               → PD sentiment overlay (±15% range)
    - Portfolio Analytics              → portfolio sentiment heatmap
    - DMI Engine                       → materiality scoring input
    - Alert Engine                     → sentiment-triggered alerts
    - Greenwashing Engine              → marketing vs reality divergence
    - Sovereign Climate Risk           → country-level sentiment context
    - Double Materiality Engine        → stakeholder salience weighting
    - Real Estate Valuation            → neighborhood/brand sentiment
    - PE Deal Pipeline                 → target company reputation score
    - Contagion Engine                 → sentiment cascade propagation

Signal Processing Pipeline
--------------------------
  1. INGEST   — raw signal from source (article, tweet, filing, report)
  2. CLASSIFY — stakeholder group, ESG pillar, topic tags, geographic scope
  3. SCORE    — raw sentiment (-1 to +1) with confidence
  4. WEIGHT   — apply source credibility weight (tier 1-5)
  5. DECAY    — time-decay based on signal type
  6. AGGREGATE — entity-level composite with HHI diversity measure
  7. VELOCITY — EWMA-smoothed sentiment velocity + acceleration
  8. ALERT    — threshold-based alert generation (same 4-tier as DME)

Stakeholder Groups (8)
----------------------
  investor, employee, customer, regulator, community, ngo, media, supplier

Source Types (6)
----------------
  news, social_media, regulatory, financial, ngo, academic

References
----------
  - Loughran-McDonald Sentiment Dictionary (financial text)
  - VADER (social media)
  - FinBERT (financial NLP)
  - GDELT GKG Themes (global events)
  - Refinitiv ESG Controversies methodology
  - RepRisk ESG Risk Platform methodology
"""
from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════
# 1.  Constants & Configuration
# ═══════════════════════════════════════════════════════════════════════

STAKEHOLDER_GROUPS = [
    "investor", "employee", "customer", "regulator",
    "community", "ngo", "media", "supplier",
]

STAKEHOLDER_WEIGHTS = {
    "investor":   0.20,
    "regulator":  0.18,
    "employee":   0.15,
    "customer":   0.14,
    "media":      0.12,
    "ngo":        0.08,
    "community":  0.07,
    "supplier":   0.06,
}

SOURCE_CREDIBILITY_TIERS = {
    1: {"label": "Authoritative", "weight": 1.00, "examples": ["SEC filings", "regulatory decisions", "audited reports"]},
    2: {"label": "High Quality", "weight": 0.85, "examples": ["Reuters", "Bloomberg", "FT", "peer-reviewed papers"]},
    3: {"label": "Standard", "weight": 0.65, "examples": ["major newspapers", "industry reports", "NGO reports"]},
    4: {"label": "Mixed", "weight": 0.45, "examples": ["social media verified", "blogs", "regional news"]},
    5: {"label": "Low", "weight": 0.25, "examples": ["unverified social media", "anonymous sources", "forums"]},
}

# Pre-configured source database (expandable)
DEFAULT_SOURCES = [
    {"name": "SEC EDGAR", "type": "regulatory", "tier": 1, "frequency": "daily"},
    {"name": "EU Official Journal", "type": "regulatory", "tier": 1, "frequency": "daily"},
    {"name": "Company Annual Reports", "type": "financial", "tier": 1, "frequency": "annual"},
    {"name": "Bloomberg News", "type": "news", "tier": 2, "frequency": "real_time"},
    {"name": "Reuters", "type": "news", "tier": 2, "frequency": "real_time"},
    {"name": "Financial Times", "type": "news", "tier": 2, "frequency": "daily"},
    {"name": "GDELT", "type": "news", "tier": 2, "frequency": "real_time"},
    {"name": "RepRisk", "type": "ngo", "tier": 2, "frequency": "daily"},
    {"name": "CDP Disclosures", "type": "ngo", "tier": 2, "frequency": "annual"},
    {"name": "Glassdoor", "type": "social_media", "tier": 3, "frequency": "daily"},
    {"name": "Trustpilot", "type": "social_media", "tier": 3, "frequency": "daily"},
    {"name": "LinkedIn", "type": "social_media", "tier": 3, "frequency": "daily"},
    {"name": "NGO Campaign Reports", "type": "ngo", "tier": 3, "frequency": "weekly"},
    {"name": "Academic Journals", "type": "academic", "tier": 2, "frequency": "monthly"},
    {"name": "Twitter/X", "type": "social_media", "tier": 4, "frequency": "real_time"},
    {"name": "Reddit", "type": "social_media", "tier": 4, "frequency": "real_time"},
    {"name": "Local News", "type": "news", "tier": 3, "frequency": "daily"},
    {"name": "Industry Associations", "type": "financial", "tier": 3, "frequency": "quarterly"},
    {"name": "Proxy Advisor Reports", "type": "financial", "tier": 2, "frequency": "annual"},
    {"name": "Trade Union Publications", "type": "ngo", "tier": 3, "frequency": "monthly"},
]

# Signal type → stakeholder mapping heuristic
SIGNAL_STAKEHOLDER_MAP = {
    "sec_filing": "regulator",
    "earnings_call": "investor",
    "annual_report": "investor",
    "press_release": "media",
    "news_article": "media",
    "tweet": "community",
    "glassdoor_review": "employee",
    "customer_review": "customer",
    "ngo_report": "ngo",
    "academic_paper": "community",
    "regulatory_action": "regulator",
    "supplier_assessment": "supplier",
    "proxy_advisory": "investor",
    "union_statement": "employee",
}

# ESG topic classification keywords
ESG_TOPIC_KEYWORDS = {
    "E": {
        "topics": ["climate", "carbon", "emissions", "pollution", "biodiversity",
                   "deforestation", "water", "waste", "energy", "renewable",
                   "fossil", "methane", "environment", "ecological", "nature",
                   "ocean", "soil", "air quality", "circular economy", "recycling"],
        "weight": 1.0,
    },
    "S": {
        "topics": ["labor", "labour", "safety", "health", "diversity", "inclusion",
                   "human rights", "community", "wage", "discrimination", "privacy",
                   "data protection", "supply chain", "modern slavery", "child labor",
                   "indigenous", "education", "inequality", "workforce", "employee"],
        "weight": 1.0,
    },
    "G": {
        "topics": ["governance", "board", "compensation", "audit", "corruption",
                   "bribery", "tax", "transparency", "lobbying", "shareholder",
                   "executive pay", "compliance", "ethics", "whistleblower",
                   "cybersecurity", "risk management", "succession", "accounting"],
        "weight": 1.0,
    },
}

# Signal decay half-lives (days) by category
DECAY_HALF_LIVES = {
    "instant":   1,
    "fast":      7,
    "medium":    30,
    "slow":      90,
    "chronic":   365,
    "permanent": 3650,
}

# Regime thresholds for sentiment velocity
REGIME_THRESHOLDS = {
    "crisis":        -2.0,   # z-score < -2.0
    "deteriorating": -0.5,   # z-score < -0.5
    "stable":         0.5,   # z-score < 0.5
    "improving":      999,   # z-score >= 0.5
}

# Module connection registry
MODULE_CONNECTIONS = {
    "inbound": [
        {"module": "dme_nlp_pulse_engine", "feed_type": "score_input", "description": "NLP pulse scores with source credibility"},
        {"module": "dme_greenwashing_engine", "feed_type": "controversy_flag", "description": "Greenwashing divergence signals"},
        {"module": "gdelt_controversy", "feed_type": "score_input", "description": "GDELT global event controversy scores"},
        {"module": "csrd_entity_registry", "feed_type": "entity_metadata", "description": "Entity matching and enrichment"},
        {"module": "company_profiles", "feed_type": "entity_metadata", "description": "LEI/ISIN/sector for entity resolution"},
        {"module": "regulatory_report_compiler", "feed_type": "score_input", "description": "Regulatory filing sentiment"},
        {"module": "engagement_tracker", "feed_type": "score_input", "description": "CA100+ engagement outcome signals"},
        {"module": "factor_overlay_engine", "feed_type": "adjustment_factor", "description": "ESG factor context for weighting"},
    ],
    "outbound": [
        {"module": "ecl_calculator", "feed_type": "adjustment_factor", "description": "PD sentiment overlay (±15% range)"},
        {"module": "portfolio_analytics", "feed_type": "score_input", "description": "Portfolio sentiment heatmap"},
        {"module": "dme_dmi_engine", "feed_type": "score_input", "description": "Materiality scoring input signal"},
        {"module": "dme_alert_engine", "feed_type": "alert_trigger", "description": "Sentiment-triggered alerts"},
        {"module": "dme_greenwashing_engine", "feed_type": "score_input", "description": "Marketing vs reality divergence check"},
        {"module": "sovereign_climate_risk", "feed_type": "adjustment_factor", "description": "Country-level sentiment context"},
        {"module": "double_materiality_engine", "feed_type": "score_input", "description": "Stakeholder salience weighting"},
        {"module": "real_estate_valuation", "feed_type": "adjustment_factor", "description": "Brand/neighborhood sentiment"},
        {"module": "pe_deal_pipeline", "feed_type": "score_input", "description": "Target company reputation score"},
        {"module": "dme_contagion_engine", "feed_type": "score_input", "description": "Sentiment cascade propagation"},
    ],
}


# ═══════════════════════════════════════════════════════════════════════
# 2.  Pydantic Request/Response Schemas
# ═══════════════════════════════════════════════════════════════════════

class SentimentSignalInput(BaseModel):
    """Single inbound signal for processing."""
    entity_id: str
    entity_name: Optional[str] = None
    source_name: str
    signal_type: str = Field(default="news_article")
    title: Optional[str] = None
    content_snippet: Optional[str] = None
    url: Optional[str] = None
    published_at: Optional[str] = None
    raw_sentiment: float = Field(..., ge=-1.0, le=1.0, description="Pre-computed sentiment score")
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    stakeholder_group: Optional[str] = None
    esg_pillar: Optional[str] = None
    topic_tags: list[str] = Field(default_factory=list)
    geographic_scope: Optional[str] = None
    language: str = Field(default="en")


class BatchSignalInput(BaseModel):
    """Batch of signals for processing."""
    signals: list[SentimentSignalInput]


class EntityScoreRequest(BaseModel):
    """Request entity-level composite sentiment score."""
    entity_id: str
    lookback_days: int = Field(default=90, ge=1, le=730)
    stakeholder_weights: Optional[dict[str, float]] = None
    min_credibility_tier: int = Field(default=5, ge=1, le=5)
    include_velocity: bool = Field(default=True)


class TopicTrendRequest(BaseModel):
    """Request topic-level trend analysis."""
    topic: str
    lookback_days: int = Field(default=90, ge=1, le=365)
    entity_filter: Optional[list[str]] = None


class ModuleFeedRequest(BaseModel):
    """Request to generate outbound feed for a specific module."""
    target_module: str
    entity_id: str
    lookback_days: int = Field(default=90)


class PortfolioSentimentRequest(BaseModel):
    """Request portfolio-level sentiment aggregation."""
    entity_ids: list[str]
    weights: Optional[dict[str, float]] = None
    lookback_days: int = Field(default=90)


class SentimentAlertConfig(BaseModel):
    """Alert configuration for sentiment monitoring."""
    entity_id: str
    watch_threshold: float = Field(default=-0.3)
    elevated_threshold: float = Field(default=-0.5)
    critical_threshold: float = Field(default=-0.7)
    extreme_threshold: float = Field(default=-0.9)
    stakeholder_focus: Optional[list[str]] = None


# ═══════════════════════════════════════════════════════════════════════
# 3.  Sentiment Analysis Engine
# ═══════════════════════════════════════════════════════════════════════

class SentimentAnalysisEngine:
    """
    Multi-stakeholder sentiment analysis with cross-module integration.

    All methods are stateless class methods.  For production use,
    signals would be persisted to sentiment_signals table and scores
    to sentiment_entity_scores.
    """

    # ── Signal Processing ──

    @classmethod
    def process_signal(cls, signal: SentimentSignalInput) -> dict:
        """
        Process a single sentiment signal through the full pipeline:
        classify → score → weight → decay → return enriched signal.
        """
        signal_id = uuid.uuid4().hex[:16]

        # Step 1: Classify stakeholder if not provided
        stakeholder = signal.stakeholder_group or cls._classify_stakeholder(signal.signal_type)

        # Step 2: Classify ESG pillar if not provided
        esg_pillar = signal.esg_pillar or cls._classify_esg(
            (signal.title or "") + " " + (signal.content_snippet or ""),
            signal.topic_tags,
        )

        # Step 3: Get source credibility weight
        credibility_tier = cls._get_source_tier(signal.source_name)
        cred_weight = SOURCE_CREDIBILITY_TIERS[credibility_tier]["weight"]

        # Step 4: Compute weighted sentiment
        weighted_sentiment = signal.raw_sentiment * cred_weight * signal.confidence

        # Step 5: Determine decay category
        decay = cls._signal_decay_category(signal.signal_type)

        # Step 6: Compute current decay factor
        if signal.published_at:
            try:
                pub_dt = datetime.fromisoformat(signal.published_at.replace("Z", "+00:00"))
                age_days = (datetime.utcnow() - pub_dt.replace(tzinfo=None)).days
            except (ValueError, TypeError):
                age_days = 0
        else:
            age_days = 0

        half_life = DECAY_HALF_LIVES.get(decay, 30)
        decay_factor = math.exp(-0.693 * age_days / half_life) if half_life > 0 else 1.0
        decayed_sentiment = weighted_sentiment * decay_factor

        return {
            "signal_id": signal_id,
            "entity_id": signal.entity_id,
            "entity_name": signal.entity_name,
            "source_name": signal.source_name,
            "signal_type": signal.signal_type,
            "stakeholder_group": stakeholder,
            "esg_pillar": esg_pillar,
            "topic_tags": signal.topic_tags,
            "raw_sentiment": signal.raw_sentiment,
            "confidence": signal.confidence,
            "credibility_tier": credibility_tier,
            "credibility_weight": cred_weight,
            "weighted_sentiment": round(weighted_sentiment, 4),
            "decay_category": decay,
            "age_days": age_days,
            "decay_factor": round(decay_factor, 4),
            "decayed_sentiment": round(decayed_sentiment, 4),
            "geographic_scope": signal.geographic_scope or "global",
            "language": signal.language,
        }

    @classmethod
    def process_batch(cls, req: BatchSignalInput) -> dict:
        """Process a batch of signals and return enriched signals + summary."""
        processed = [cls.process_signal(s) for s in req.signals]

        # Summary statistics
        if processed:
            avg_raw = sum(p["raw_sentiment"] for p in processed) / len(processed)
            avg_weighted = sum(p["weighted_sentiment"] for p in processed) / len(processed)
            avg_decayed = sum(p["decayed_sentiment"] for p in processed) / len(processed)

            stakeholder_dist = {}
            for p in processed:
                sg = p["stakeholder_group"]
                stakeholder_dist[sg] = stakeholder_dist.get(sg, 0) + 1

            esg_dist = {}
            for p in processed:
                ep = p["esg_pillar"] or "unclassified"
                esg_dist[ep] = esg_dist.get(ep, 0) + 1
        else:
            avg_raw = avg_weighted = avg_decayed = 0.0
            stakeholder_dist = {}
            esg_dist = {}

        return {
            "signals_processed": len(processed),
            "signals": processed,
            "summary": {
                "avg_raw_sentiment": round(avg_raw, 4),
                "avg_weighted_sentiment": round(avg_weighted, 4),
                "avg_decayed_sentiment": round(avg_decayed, 4),
                "stakeholder_distribution": stakeholder_dist,
                "esg_distribution": esg_dist,
            },
        }

    # ── Entity Scoring ──

    @classmethod
    def entity_score(cls, req: EntityScoreRequest) -> dict:
        """
        Compute entity-level composite sentiment score.

        In production this queries sentiment_signals table; here it
        generates a deterministic demo score from entity_id hash.
        """
        import hashlib
        seed = int(hashlib.md5(req.entity_id.encode()).hexdigest()[:8], 16)

        weights = req.stakeholder_weights or STAKEHOLDER_WEIGHTS

        # Generate per-stakeholder scores (deterministic from entity_id)
        stakeholder_scores = {}
        for i, sg in enumerate(STAKEHOLDER_GROUPS):
            # Deterministic pseudo-random from seed
            val = ((seed * (i + 7) * 2654435761) % 2000 - 1000) / 1000  # -1 to +1
            stakeholder_scores[sg] = round(val, 3)

        # Weighted composite
        composite = 0.0
        total_weight = 0.0
        for sg, score in stakeholder_scores.items():
            w = weights.get(sg, 0.1)
            composite += score * w
            total_weight += w
        composite = round(composite / total_weight if total_weight else 0.0, 4)

        # ESG breakdown
        esg_scores = {
            "environmental": round(((seed * 3) % 2000 - 1000) / 1000, 3),
            "social": round(((seed * 5) % 2000 - 1000) / 1000, 3),
            "governance": round(((seed * 11) % 2000 - 1000) / 1000, 3),
        }

        # Velocity (deterministic)
        velocity = round(((seed * 17) % 600 - 300) / 1000, 4)
        acceleration = round(((seed * 23) % 400 - 200) / 1000, 4)

        # Z-score and regime
        z = round(velocity / 0.15 if abs(velocity) > 0 else 0.0, 3)
        regime = "stable"
        for regime_name, threshold in REGIME_THRESHOLDS.items():
            if z < threshold:
                regime = regime_name
                break

        # Source diversity (HHI-based, 0-1 where 1 = fully diverse)
        n_sources = max(3, (seed % 15) + 3)
        hhi = 1.0 / n_sources  # simplified
        diversity = round(1 - hhi, 3)

        # Signal count
        signal_count = max(10, (seed % 200) + 10)

        # Alert check
        alert_tier = None
        if composite <= -0.9:
            alert_tier = "EXTREME"
        elif composite <= -0.7:
            alert_tier = "CRITICAL"
        elif composite <= -0.5:
            alert_tier = "ELEVATED"
        elif composite <= -0.3:
            alert_tier = "WATCH"

        return {
            "entity_id": req.entity_id,
            "lookback_days": req.lookback_days,
            "as_of_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "composite_score": composite,
            "composite_confidence": round(0.6 + (seed % 30) / 100, 2),
            "signal_count": signal_count,
            "source_diversity": diversity,
            "stakeholder_scores": stakeholder_scores,
            "esg_scores": esg_scores,
            "velocity": {
                "sentiment_velocity": velocity,
                "sentiment_acceleration": acceleration,
                "z_score": z,
                "regime": regime,
            },
            "alert": {
                "tier": alert_tier,
                "triggers": [],
            },
        }

    # ── Portfolio Aggregation ──

    @classmethod
    def portfolio_sentiment(cls, req: PortfolioSentimentRequest) -> dict:
        """
        Aggregate sentiment across a portfolio of entities.
        """
        n = len(req.entity_ids)
        if n == 0:
            return {"error": "No entities provided"}

        weights = req.weights or {eid: 1.0 / n for eid in req.entity_ids}
        total_weight = sum(weights.values())

        entity_scores = []
        portfolio_composite = 0.0
        portfolio_velocity = 0.0
        worst_entities = []
        best_entities = []

        for eid in req.entity_ids:
            score = cls.entity_score(EntityScoreRequest(
                entity_id=eid, lookback_days=req.lookback_days,
            ))
            w = weights.get(eid, 1.0 / n) / total_weight
            portfolio_composite += score["composite_score"] * w
            portfolio_velocity += score["velocity"]["sentiment_velocity"] * w

            entry = {
                "entity_id": eid,
                "weight": round(w, 4),
                "composite_score": score["composite_score"],
                "regime": score["velocity"]["regime"],
                "alert_tier": score["alert"]["tier"],
            }
            entity_scores.append(entry)

            if score["composite_score"] < -0.3:
                worst_entities.append(entry)
            if score["composite_score"] > 0.3:
                best_entities.append(entry)

        worst_entities.sort(key=lambda x: x["composite_score"])
        best_entities.sort(key=lambda x: x["composite_score"], reverse=True)

        # Stakeholder-level portfolio aggregation
        portfolio_stakeholder = {}
        for sg in STAKEHOLDER_GROUPS:
            sg_total = 0.0
            for i, eid in enumerate(req.entity_ids):
                s = entity_scores[i]
                # Use entity composite as proxy for stakeholder (simplified)
                sg_total += s["composite_score"] * s["weight"]
            portfolio_stakeholder[sg] = round(sg_total, 4)

        return {
            "portfolio_size": n,
            "lookback_days": req.lookback_days,
            "as_of_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "portfolio_composite": round(portfolio_composite, 4),
            "portfolio_velocity": round(portfolio_velocity, 4),
            "entity_scores": entity_scores,
            "worst_entities": worst_entities[:5],
            "best_entities": best_entities[:5],
            "alerts_count": sum(1 for e in entity_scores if e["alert_tier"]),
            "stakeholder_breakdown": portfolio_stakeholder,
        }

    # ── Module Feed Generation ──

    @classmethod
    def generate_module_feed(cls, req: ModuleFeedRequest) -> dict:
        """
        Generate an outbound sentiment feed for a specific downstream module.

        Each module receives a tailored payload:
          - ecl_calculator: PD adjustment factor
          - portfolio_analytics: heatmap data
          - dme_dmi_engine: materiality input signal
          - dme_alert_engine: alert triggers
          - pe_deal_pipeline: reputation score
          etc.
        """
        entity_score = cls.entity_score(EntityScoreRequest(
            entity_id=req.entity_id, lookback_days=req.lookback_days,
        ))

        composite = entity_score["composite_score"]
        velocity = entity_score["velocity"]

        # Module-specific payload transformations
        if req.target_module == "ecl_calculator":
            # PD adjustment: sentiment < -0.5 → +15% PD, > +0.5 → -10% PD
            pd_mult = 1.0 + (-composite * 0.15)  # linear mapping
            pd_mult = max(0.85, min(1.15, pd_mult))
            payload = {
                "pd_multiplier": round(pd_mult, 4),
                "sentiment_flag": "negative" if composite < -0.3 else "neutral" if composite < 0.3 else "positive",
                "confidence": entity_score["composite_confidence"],
                "signal_count": entity_score["signal_count"],
            }

        elif req.target_module == "portfolio_analytics":
            payload = {
                "composite_score": composite,
                "regime": velocity["regime"],
                "stakeholder_scores": entity_score["stakeholder_scores"],
                "esg_scores": entity_score["esg_scores"],
                "source_diversity": entity_score["source_diversity"],
            }

        elif req.target_module == "dme_dmi_engine":
            # DMI uses sentiment as a materiality signal
            payload = {
                "materiality_signal": abs(composite),  # absolute value = materiality strength
                "direction": "negative" if composite < 0 else "positive",
                "velocity_signal": velocity["sentiment_velocity"],
                "stakeholder_coverage": len([s for s in entity_score["stakeholder_scores"].values() if s != 0]),
            }

        elif req.target_module == "dme_alert_engine":
            payload = {
                "alert_tier": entity_score["alert"]["tier"],
                "composite_score": composite,
                "z_score": velocity["z_score"],
                "regime": velocity["regime"],
                "triggers": entity_score["alert"]["triggers"],
            }

        elif req.target_module == "dme_greenwashing_engine":
            # Compare public marketing sentiment vs operational reality
            payload = {
                "public_sentiment": composite,
                "media_sentiment": entity_score["stakeholder_scores"].get("media", 0),
                "ngo_sentiment": entity_score["stakeholder_scores"].get("ngo", 0),
                "regulator_sentiment": entity_score["stakeholder_scores"].get("regulator", 0),
                "divergence_flag": abs(entity_score["stakeholder_scores"].get("media", 0)
                                      - entity_score["stakeholder_scores"].get("ngo", 0)) > 0.5,
            }

        elif req.target_module == "sovereign_climate_risk":
            payload = {
                "country_sentiment_adjustment": round(composite * 5, 2),  # ±5 points on 0-100 scale
                "regime": velocity["regime"],
                "confidence": entity_score["composite_confidence"],
            }

        elif req.target_module == "double_materiality_engine":
            payload = {
                "stakeholder_salience": entity_score["stakeholder_scores"],
                "composite": composite,
                "esg_materiality": entity_score["esg_scores"],
                "signal_density": entity_score["signal_count"],
            }

        elif req.target_module == "real_estate_valuation":
            # Brand/neighborhood reputation → valuation adjustment
            adj_pct = composite * 3.0  # ±3% valuation adjustment
            payload = {
                "reputation_adjustment_pct": round(adj_pct, 2),
                "community_sentiment": entity_score["stakeholder_scores"].get("community", 0),
                "customer_sentiment": entity_score["stakeholder_scores"].get("customer", 0),
            }

        elif req.target_module == "pe_deal_pipeline":
            # Reputation score for deal screening
            rep_score = round((composite + 1) / 2 * 100, 1)  # 0-100 scale
            payload = {
                "reputation_score": rep_score,
                "sentiment_regime": velocity["regime"],
                "stakeholder_risk_flags": [
                    sg for sg, score in entity_score["stakeholder_scores"].items()
                    if score < -0.5
                ],
                "esg_risk_flags": [
                    pillar for pillar, score in entity_score["esg_scores"].items()
                    if score < -0.3
                ],
            }

        elif req.target_module == "dme_contagion_engine":
            payload = {
                "sentiment_intensity": abs(composite),
                "direction": -1 if composite < 0 else 1,
                "cascade_risk": velocity["regime"] in ("crisis", "deteriorating"),
                "velocity": velocity["sentiment_velocity"],
            }

        else:
            payload = {
                "composite_score": composite,
                "velocity": velocity,
                "confidence": entity_score["composite_confidence"],
            }

        return {
            "target_module": req.target_module,
            "entity_id": req.entity_id,
            "feed_direction": "outbound",
            "feed_type": cls._feed_type_for_module(req.target_module),
            "payload": payload,
            "generated_at": datetime.utcnow().isoformat(),
        }

    # ── Topic Trend Analysis ──

    @classmethod
    def topic_trend(cls, req: TopicTrendRequest) -> dict:
        """Analyze sentiment trend for a specific topic across entities."""
        import hashlib
        seed = int(hashlib.md5(req.topic.encode()).hexdigest()[:8], 16)

        # Generate deterministic trend data
        points = []
        for i in range(min(req.lookback_days, 90)):
            day_seed = (seed + i * 7919) % 10000
            val = ((day_seed % 2000) - 1000) / 1000
            points.append({
                "day_offset": -i,
                "avg_sentiment": round(val, 3),
                "signal_count": max(1, (day_seed % 50)),
            })

        avg = sum(p["avg_sentiment"] for p in points) / len(points) if points else 0
        total_signals = sum(p["signal_count"] for p in points)

        return {
            "topic": req.topic,
            "lookback_days": req.lookback_days,
            "total_signals": total_signals,
            "avg_sentiment": round(avg, 4),
            "trend": points[:30],  # last 30 days
            "velocity": round(((seed * 13) % 600 - 300) / 1000, 4),
            "regime": "stable",
        }

    # ── Reference Data ──

    @classmethod
    def get_reference_data(cls) -> dict:
        return {
            "stakeholder_groups": STAKEHOLDER_GROUPS,
            "stakeholder_weights": STAKEHOLDER_WEIGHTS,
            "source_credibility_tiers": SOURCE_CREDIBILITY_TIERS,
            "signal_decay_half_lives": DECAY_HALF_LIVES,
            "regime_thresholds": REGIME_THRESHOLDS,
            "esg_topic_keywords": {k: v["topics"] for k, v in ESG_TOPIC_KEYWORDS.items()},
        }

    @classmethod
    def get_sources(cls) -> list[dict]:
        return DEFAULT_SOURCES

    @classmethod
    def get_module_connections(cls) -> dict:
        return MODULE_CONNECTIONS

    @classmethod
    def get_alert_config(cls) -> dict:
        return {
            "sentiment_thresholds": {
                "WATCH": -0.3,
                "ELEVATED": -0.5,
                "CRITICAL": -0.7,
                "EXTREME": -0.9,
            },
            "velocity_thresholds": {
                "WATCH": 1.5,
                "ELEVATED": 2.0,
                "CRITICAL": 3.0,
                "EXTREME": 4.0,
            },
            "compound_condition": "sentiment_below_threshold AND (velocity_z > 1.5 OR acceleration < -0.1)",
        }

    # ── Internal Helpers ──

    @classmethod
    def _classify_stakeholder(cls, signal_type: str) -> str:
        return SIGNAL_STAKEHOLDER_MAP.get(signal_type, "media")

    @classmethod
    def _classify_esg(cls, text: str, tags: list[str]) -> Optional[str]:
        text_lower = text.lower()
        combined = text_lower + " " + " ".join(tags).lower()

        scores = {}
        for pillar, config in ESG_TOPIC_KEYWORDS.items():
            count = sum(1 for kw in config["topics"] if kw in combined)
            if count > 0:
                scores[pillar] = count

        if not scores:
            return None
        return max(scores, key=scores.get)

    @classmethod
    def _get_source_tier(cls, source_name: str) -> int:
        for src in DEFAULT_SOURCES:
            if src["name"].lower() == source_name.lower():
                return src["tier"]
        return 4  # default to mixed quality

    @classmethod
    def _signal_decay_category(cls, signal_type: str) -> str:
        fast_types = {"tweet", "social_media_post", "reddit_post"}
        slow_types = {"annual_report", "sec_filing", "regulatory_action", "academic_paper"}
        chronic_types = {"ngo_report", "union_statement"}

        if signal_type in fast_types:
            return "fast"
        if signal_type in slow_types:
            return "slow"
        if signal_type in chronic_types:
            return "chronic"
        return "medium"

    @classmethod
    def _feed_type_for_module(cls, module: str) -> str:
        for conn in MODULE_CONNECTIONS["outbound"]:
            if conn["module"] == module:
                return conn["feed_type"]
        return "score_input"
