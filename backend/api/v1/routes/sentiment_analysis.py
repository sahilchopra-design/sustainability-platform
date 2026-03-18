"""
Sentiment Analysis Engine — API Routes.

Prefix: /api/v1/sentiment

Multi-stakeholder sentiment analysis with cross-module integration.
Ingests signals from news, social media, regulatory filings, NGO reports,
and produces entity-level scores that feed into 10+ downstream modules.
"""
from fastapi import APIRouter
from services.sentiment_analysis_engine import (
    SentimentAnalysisEngine,
    SentimentSignalInput,
    BatchSignalInput,
    EntityScoreRequest,
    TopicTrendRequest,
    ModuleFeedRequest,
    PortfolioSentimentRequest,
)

router = APIRouter(prefix="/api/v1/sentiment", tags=["Sentiment Analysis"])


# ── Signal Processing ──

@router.post("/process-signal")
def process_signal(req: SentimentSignalInput):
    """Process a single sentiment signal through the full pipeline."""
    return SentimentAnalysisEngine.process_signal(req)


@router.post("/process-batch")
def process_batch(req: BatchSignalInput):
    """Process a batch of sentiment signals with summary statistics."""
    return SentimentAnalysisEngine.process_batch(req)


# ── Entity Scoring ──

@router.post("/entity-score")
def entity_score(req: EntityScoreRequest):
    """
    Compute entity-level composite sentiment score with stakeholder
    breakdown, ESG split, velocity tracking, and alert status.
    """
    return SentimentAnalysisEngine.entity_score(req)


# ── Portfolio Aggregation ──

@router.post("/portfolio")
def portfolio_sentiment(req: PortfolioSentimentRequest):
    """
    Aggregate sentiment across a portfolio of entities with
    exposure-weighted composite and worst/best entity identification.
    """
    return SentimentAnalysisEngine.portfolio_sentiment(req)


# ── Module Feed Generation ──

@router.post("/module-feed")
def generate_module_feed(req: ModuleFeedRequest):
    """
    Generate tailored outbound sentiment feed for a specific
    downstream module (ecl_calculator, portfolio_analytics,
    dme_dmi_engine, pe_deal_pipeline, etc.).
    """
    return SentimentAnalysisEngine.generate_module_feed(req)


# ── Topic Trend Analysis ──

@router.post("/topic-trend")
def topic_trend(req: TopicTrendRequest):
    """Analyze sentiment trend for a specific topic across entities."""
    return SentimentAnalysisEngine.topic_trend(req)


# ── Reference Data ──

@router.get("/ref/config")
def get_reference_data():
    """Reference: stakeholder groups, weights, credibility tiers, decay rates, regime thresholds."""
    return SentimentAnalysisEngine.get_reference_data()


@router.get("/ref/sources")
def get_sources():
    """Reference: pre-configured signal sources (20 sources across 6 types)."""
    return SentimentAnalysisEngine.get_sources()


@router.get("/ref/module-connections")
def get_module_connections():
    """Reference: inbound (8) and outbound (10) module integration points."""
    return SentimentAnalysisEngine.get_module_connections()


@router.get("/ref/alert-config")
def get_alert_config():
    """Reference: sentiment alert thresholds and compound conditions."""
    return SentimentAnalysisEngine.get_alert_config()
