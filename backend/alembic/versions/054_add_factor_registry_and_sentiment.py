"""Add factor registry and sentiment analysis tables.

Revision ID: 054
Revises: 053
Create Date: 2026-03-16
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "054"
down_revision = "053"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Factor Registry ──
    op.create_table(
        "dme_factor_definitions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("factor_id", sa.String(20), unique=True, nullable=False, index=True),
        sa.Column("factor_name", sa.String(200), nullable=False),
        sa.Column("pillar", sa.String(30), nullable=False, index=True),
        sa.Column("topic", sa.String(100), index=True),
        sa.Column("sub_topic", sa.String(150)),
        sa.Column("materiality_dimension", sa.String(20), index=True),
        sa.Column("source", sa.String(20), nullable=False, index=True),
        sa.Column("data_frequency", sa.String(20), server_default="monthly"),
        sa.Column("velocity_method", sa.String(20), server_default="z_score"),
        sa.Column("ewma_alpha", sa.Float, server_default="0.2"),
        sa.Column("signal_decay", sa.String(20), server_default="medium"),
        sa.Column("alert_watch", sa.Float, server_default="1.5"),
        sa.Column("alert_elevated", sa.Float, server_default="2.0"),
        sa.Column("alert_critical", sa.Float, server_default="3.0"),
        sa.Column("alert_extreme", sa.Float, server_default="4.0"),
        sa.Column("pcaf_dq", sa.Integer),
        sa.Column("overlay_registry_key", sa.String(60)),
        sa.Column("unit", sa.String(30)),
        sa.Column("description", sa.Text),
        sa.Column("regulatory_refs", JSONB, server_default="[]"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "dme_factor_values",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("factor_id", sa.String(20), sa.ForeignKey("dme_factor_definitions.factor_id"), nullable=False, index=True),
        sa.Column("entity_id", sa.String(50), nullable=False, index=True),
        sa.Column("value", sa.Float, nullable=False),
        sa.Column("data_quality_score", sa.Integer),
        sa.Column("as_of_date", sa.Date, nullable=False, index=True),
        sa.Column("source_description", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_factor_values_entity_date", "dme_factor_values", ["entity_id", "as_of_date"])

    # ── Sentiment Analysis Module ──
    op.create_table(
        "sentiment_sources",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("source_name", sa.String(100), unique=True, nullable=False),
        sa.Column("source_type", sa.String(30), nullable=False),  # news, social_media, regulatory, financial, ngo, academic
        sa.Column("credibility_tier", sa.Integer, nullable=False),  # 1 (highest) to 5 (lowest)
        sa.Column("base_weight", sa.Float, server_default="1.0"),
        sa.Column("update_frequency", sa.String(20)),  # real_time, hourly, daily, weekly
        sa.Column("language_coverage", JSONB, server_default='["en"]'),
        sa.Column("geographic_coverage", JSONB, server_default='["global"]'),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("api_endpoint", sa.Text),
        sa.Column("metadata", JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "sentiment_signals",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("signal_id", sa.String(32), unique=True, nullable=False, index=True),
        sa.Column("entity_id", sa.String(50), nullable=False, index=True),
        sa.Column("entity_name", sa.String(200)),
        sa.Column("source_id", sa.Integer, sa.ForeignKey("sentiment_sources.id")),
        sa.Column("source_name", sa.String(100)),
        sa.Column("signal_type", sa.String(30), nullable=False, index=True),  # article, tweet, filing, report, press_release, ngo_report
        sa.Column("title", sa.Text),
        sa.Column("content_snippet", sa.Text),
        sa.Column("url", sa.Text),
        sa.Column("published_at", sa.DateTime, nullable=False, index=True),
        sa.Column("ingested_at", sa.DateTime, server_default=sa.func.now()),
        # Sentiment scores
        sa.Column("raw_sentiment", sa.Float),  # -1.0 to +1.0
        sa.Column("confidence", sa.Float),  # 0.0 to 1.0
        sa.Column("credibility_weight", sa.Float),
        sa.Column("weighted_sentiment", sa.Float),  # raw_sentiment * credibility_weight
        # Classification
        sa.Column("stakeholder_group", sa.String(30), index=True),  # investor, employee, customer, regulator, community, ngo, media, supplier
        sa.Column("esg_pillar", sa.String(20)),  # E, S, G, or null
        sa.Column("topic_tags", JSONB, server_default="[]"),
        sa.Column("geographic_scope", sa.String(10)),  # ISO country code or "global"
        sa.Column("language", sa.String(5), server_default="en"),
        # Decay & lifecycle
        sa.Column("decay_category", sa.String(20), server_default="medium"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("superseded_by", sa.String(32)),  # signal_id of newer signal
        sa.Column("metadata", JSONB, server_default="{}"),
    )
    op.create_index("ix_sentiment_signals_entity_pub", "sentiment_signals", ["entity_id", "published_at"])

    op.create_table(
        "sentiment_entity_scores",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("entity_id", sa.String(50), nullable=False, index=True),
        sa.Column("entity_name", sa.String(200)),
        sa.Column("as_of_date", sa.Date, nullable=False, index=True),
        # Composite scores
        sa.Column("composite_score", sa.Float),  # -1.0 to +1.0 weighted average
        sa.Column("composite_confidence", sa.Float),
        sa.Column("signal_count", sa.Integer),
        sa.Column("source_diversity", sa.Float),  # 0-1 HHI-based measure
        # Stakeholder breakdown
        sa.Column("investor_sentiment", sa.Float),
        sa.Column("employee_sentiment", sa.Float),
        sa.Column("customer_sentiment", sa.Float),
        sa.Column("regulator_sentiment", sa.Float),
        sa.Column("community_sentiment", sa.Float),
        sa.Column("ngo_sentiment", sa.Float),
        sa.Column("media_sentiment", sa.Float),
        sa.Column("supplier_sentiment", sa.Float),
        # ESG breakdown
        sa.Column("environmental_sentiment", sa.Float),
        sa.Column("social_sentiment", sa.Float),
        sa.Column("governance_sentiment", sa.Float),
        # Velocity
        sa.Column("sentiment_velocity", sa.Float),  # rate of change
        sa.Column("sentiment_acceleration", sa.Float),
        sa.Column("regime", sa.String(20)),  # improving, stable, deteriorating, crisis
        sa.Column("z_score", sa.Float),
        # Alert
        sa.Column("alert_tier", sa.String(20)),
        sa.Column("alert_triggers", JSONB, server_default="[]"),
        sa.Column("metadata", JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_sentiment_entity_scores_date", "sentiment_entity_scores", ["entity_id", "as_of_date"])

    op.create_table(
        "sentiment_topic_trends",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("topic", sa.String(100), nullable=False, index=True),
        sa.Column("as_of_date", sa.Date, nullable=False, index=True),
        sa.Column("signal_count", sa.Integer),
        sa.Column("avg_sentiment", sa.Float),
        sa.Column("sentiment_std", sa.Float),
        sa.Column("top_entities", JSONB, server_default="[]"),
        sa.Column("top_sources", JSONB, server_default="[]"),
        sa.Column("velocity", sa.Float),
        sa.Column("regime", sa.String(20)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "sentiment_module_feeds",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("module_name", sa.String(60), nullable=False, index=True),
        sa.Column("feed_direction", sa.String(10), nullable=False),  # inbound or outbound
        sa.Column("entity_id", sa.String(50), index=True),
        sa.Column("signal_ids", JSONB, server_default="[]"),
        sa.Column("feed_type", sa.String(30)),  # score_input, alert_trigger, controversy_flag, adjustment_factor
        sa.Column("payload", JSONB, server_default="{}"),
        sa.Column("processed_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("sentiment_module_feeds")
    op.drop_table("sentiment_topic_trends")
    op.drop_table("sentiment_entity_scores")
    op.drop_table("sentiment_signals")
    op.drop_table("sentiment_sources")
    op.drop_table("dme_factor_values")
    op.drop_table("dme_factor_definitions")
