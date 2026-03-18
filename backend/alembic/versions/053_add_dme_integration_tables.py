"""Add DME (Dynamic Materiality Engine) integration tables

Velocity timeseries, contagion network, alert framework,
DMI scores, greenwashing detection, NLP pulse, policy tracker.

Revision ID: 053
Revises: 052
Create Date: 2026-03-16
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers
revision = "053"
down_revision = "052"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Velocity Engine ──────────────────────────────────────────────────────
    op.create_table(
        "dme_velocity_config",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("metric_key", sa.String(128), nullable=False, unique=True),
        sa.Column("description", sa.Text),
        sa.Column("ewma_alpha", sa.Float, nullable=False, server_default="0.2"),
        sa.Column("lookback_days", sa.Integer, nullable=False, server_default="252"),
        sa.Column("z_threshold_elevated", sa.Float, server_default="1.0"),
        sa.Column("z_threshold_critical", sa.Float, server_default="2.0"),
        sa.Column("z_threshold_extreme", sa.Float, server_default="3.0"),
        sa.Column("delta_t_days", sa.Float, server_default="1.0"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "dme_velocity_timeseries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("entity_id", sa.String(36), nullable=False, index=True),
        sa.Column("metric_key", sa.String(128), nullable=False, index=True),
        sa.Column("timestamp", sa.DateTime, nullable=False, index=True),
        sa.Column("raw_value", sa.Float, nullable=False),
        sa.Column("velocity_raw", sa.Float),
        sa.Column("velocity_pct", sa.Float),
        sa.Column("velocity_smoothed", sa.Float),
        sa.Column("acceleration", sa.Float),
        sa.Column("z_score", sa.Float),
        sa.Column("regime", sa.String(16)),  # NORMAL/ELEVATED/CRITICAL/EXTREME
        sa.Column("sigma_classification", sa.String(16)),
        sa.Column("smoothing_method", sa.String(64)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("entity_id", "metric_key", "timestamp", name="uq_velocity_entity_metric_ts"),
    )
    op.create_index("ix_velocity_regime", "dme_velocity_timeseries", ["regime"])

    # ── Contagion Engine ─────────────────────────────────────────────────────
    op.create_table(
        "dme_contagion_network",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source_entity_id", sa.String(36), nullable=False, index=True),
        sa.Column("target_entity_id", sa.String(36), nullable=False, index=True),
        sa.Column("layer", sa.String(32), nullable=False),  # L1_ENTITY/L2_STRUCTURAL/L3_CAPITAL
        sa.Column("w_financial", sa.Float, server_default="0"),
        sa.Column("w_supply_chain", sa.Float, server_default="0"),
        sa.Column("w_regulatory", sa.Float, server_default="0"),
        sa.Column("w_composite", sa.Float, nullable=False),
        sa.Column("kernel_type", sa.String(32), server_default="'exponential'"),
        sa.Column("decay_rate", sa.Float, nullable=False),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("source_entity_id", "target_entity_id", "layer", name="uq_contagion_edge"),
    )

    op.create_table(
        "dme_contagion_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("entity_id", sa.String(36), nullable=False, index=True),
        sa.Column("layer", sa.String(32), nullable=False),
        sa.Column("timestamp", sa.DateTime, nullable=False, index=True),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("severity", sa.Float, nullable=False),
        sa.Column("pillar", sa.String(8)),  # E/S/G/X
        sa.Column("trigger_entity_id", sa.String(36)),
        sa.Column("intensity_at_event", sa.Float),
        sa.Column("metadata", JSONB),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "dme_contagion_simulations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("scenario", sa.String(64), nullable=False),
        sa.Column("run_timestamp", sa.DateTime, nullable=False),
        sa.Column("seed_entity_id", sa.String(36)),
        sa.Column("seed_event_type", sa.String(64)),
        sa.Column("cascade_depth", sa.Integer),
        sa.Column("entities_affected", sa.Integer),
        sa.Column("total_intensity", sa.Float),
        sa.Column("el_amplification", sa.Float),
        sa.Column("var_amplification", sa.Float),
        sa.Column("es_amplification", sa.Float),
        sa.Column("spectral_radius", sa.Float),
        sa.Column("is_stable", sa.Boolean),
        sa.Column("results_json", JSONB),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # ── Alert Framework ──────────────────────────────────────────────────────
    op.create_table(
        "dme_alert_rules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("metric_key", sa.String(128), nullable=False),
        sa.Column("factor_id", sa.String(64)),
        sa.Column("watch_threshold", sa.Float, server_default="1.5"),
        sa.Column("elevated_threshold", sa.Float, server_default="2.0"),
        sa.Column("critical_threshold", sa.Float, server_default="3.0"),
        sa.Column("extreme_threshold", sa.Float, server_default="4.0"),
        sa.Column("threshold_type", sa.String(16), server_default="'z_score'"),
        sa.Column("suppression_hours_watch", sa.Integer, server_default="48"),
        sa.Column("suppression_hours_elevated", sa.Integer, server_default="24"),
        sa.Column("suppression_hours_critical", sa.Integer, server_default="4"),
        sa.Column("suppression_hours_extreme", sa.Integer, server_default="0"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "dme_alerts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("entity_id", sa.String(36), nullable=False, index=True),
        sa.Column("factor_id", sa.String(64), nullable=False),
        sa.Column("pillar", sa.String(8)),
        sa.Column("alert_tier", sa.String(16), nullable=False),  # WATCH/ELEVATED/CRITICAL/EXTREME
        sa.Column("trigger_type", sa.String(16)),  # Z_SCORE/COMPOUND/STRUCTURAL
        sa.Column("velocity_raw", sa.Float),
        sa.Column("velocity_z_score", sa.Float),
        sa.Column("acceleration", sa.Float),
        sa.Column("priority_score", sa.Integer),
        sa.Column("priority_band", sa.String(16)),  # LOW/MEDIUM/HIGH/CRITICAL
        sa.Column("response_sla_hours", sa.Integer),
        sa.Column("factor_override_applied", sa.Boolean, server_default="false"),
        sa.Column("contagion_active", sa.Boolean, server_default="false"),
        sa.Column("pd_adjustment", sa.Float),
        sa.Column("var_adjustment", sa.Float),
        sa.Column("acknowledged_at", sa.DateTime),
        sa.Column("acknowledged_by", sa.String(128)),
        sa.Column("resolved_at", sa.DateTime),
        sa.Column("resolution_note", sa.Text),
        sa.Column("triggered_at", sa.DateTime, nullable=False, index=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_alerts_tier", "dme_alerts", ["alert_tier"])
    op.create_index("ix_alerts_unresolved", "dme_alerts", ["entity_id", "alert_tier"],
                     postgresql_where=sa.text("resolved_at IS NULL"))

    # ── Dynamic Materiality Index (DMI) ──────────────────────────────────────
    op.create_table(
        "dme_dmi_config",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("topic", sa.String(128), nullable=False, unique=True),
        sa.Column("pillar", sa.String(8)),
        sa.Column("base_weight", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("velocity_coefficient", sa.Float, server_default="0.3"),
        sa.Column("concentration_threshold", sa.Float, server_default="0.05"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "dme_dmi_scores",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("entity_id", sa.String(36), nullable=False, index=True),
        sa.Column("topic", sa.String(128), nullable=False),
        sa.Column("timestamp", sa.DateTime, nullable=False),
        sa.Column("dmi_score_base", sa.Float, nullable=False),
        sa.Column("velocity_weight", sa.Float),
        sa.Column("concentration_penalty", sa.Float),
        sa.Column("dmi_score_adjusted", sa.Float, nullable=False),
        sa.Column("confidence", sa.Float),
        sa.Column("pcaf_quality", sa.Integer),
        sa.Column("component_scores", JSONB),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("entity_id", "topic", "timestamp", name="uq_dmi_entity_topic_ts"),
    )

    # ── Greenwashing Detector ────────────────────────────────────────────────
    op.create_table(
        "dme_greenwash_watchlist",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("entity_id", sa.String(36), nullable=False, unique=True),
        sa.Column("risk_level", sa.String(16), server_default="'NONE'"),  # NONE/WARNING/CRITICAL
        sa.Column("flags_count", sa.Integer, server_default="0"),
        sa.Column("last_scan_at", sa.DateTime),
        sa.Column("latest_divergence_z", sa.Float),
        sa.Column("latest_cusum_alert", sa.Boolean, server_default="false"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "dme_greenwash_signals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("entity_id", sa.String(36), nullable=False, index=True),
        sa.Column("detection_date", sa.DateTime, nullable=False),
        sa.Column("marketing_weighted_avg", sa.Float),
        sa.Column("operational_weighted_avg", sa.Float),
        sa.Column("divergence_raw", sa.Float),
        sa.Column("divergence_z_score", sa.Float),
        sa.Column("velocity_latest", sa.Float),
        sa.Column("acceleration_latest", sa.Float),
        sa.Column("cusum_alert", sa.Boolean, server_default="false"),
        sa.Column("severity", sa.String(32)),  # NONE/INSUFFICIENT_DATA/WARNING/CRITICAL
        sa.Column("condition_velocity", sa.Boolean),
        sa.Column("condition_acceleration", sa.Boolean),
        sa.Column("condition_z_score", sa.Boolean),
        sa.Column("status", sa.String(16), server_default="'OPEN'"),  # OPEN/REVIEWED/DISMISSED
        sa.Column("reviewed_by", sa.String(128)),
        sa.Column("reviewed_at", sa.DateTime),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # ── NLP Pulse Score ──────────────────────────────────────────────────────
    op.create_table(
        "dme_nlp_signals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("entity_id", sa.String(36), nullable=False, index=True),
        sa.Column("source", sa.String(64), nullable=False),  # bloomberg/reuters/gdelt/twitter/...
        sa.Column("source_tier", sa.Integer),  # 1-4
        sa.Column("source_credibility", sa.Float),
        sa.Column("event_type", sa.String(64)),
        sa.Column("sentiment_score", sa.Float),  # [-100, +100]
        sa.Column("information_density", sa.Float),
        sa.Column("pulse_raw", sa.Float),
        sa.Column("pulse_discounted", sa.Float),
        sa.Column("greenwash_discount", sa.Float, server_default="1.0"),
        sa.Column("decay_lambda", sa.Float),
        sa.Column("decay_half_life_hours", sa.Float),
        sa.Column("is_self_reported", sa.Boolean, server_default="false"),
        sa.Column("timestamp", sa.DateTime, nullable=False, index=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "dme_nlp_pulse",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("entity_id", sa.String(36), nullable=False, unique=True),
        sa.Column("pulse_score", sa.Float),
        sa.Column("signal_count", sa.Integer, server_default="0"),
        sa.Column("avg_credibility", sa.Float),
        sa.Column("positive_signals", sa.Integer, server_default="0"),
        sa.Column("negative_signals", sa.Integer, server_default="0"),
        sa.Column("last_signal_at", sa.DateTime),
        sa.Column("last_updated", sa.DateTime, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # ── Policy Tracker ───────────────────────────────────────────────────────
    op.create_table(
        "dme_policy_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("jurisdiction", sa.String(64), nullable=False, index=True),
        sa.Column("component", sa.String(32), nullable=False),  # carbon_price/regulatory_pipeline/enforcement/disclosure_mandate
        sa.Column("delta_policy", sa.Float),
        sa.Column("weight", sa.Float),
        sa.Column("direction", sa.Integer),  # -1/0/+1
        sa.Column("confidence", sa.Float),
        sa.Column("effective_date", sa.DateTime),
        sa.Column("carbon_price_impact_usd", sa.Float),
        sa.Column("disclosure_impact_score", sa.Float),
        sa.Column("enforcement_level", sa.String(16)),
        sa.Column("metadata", JSONB),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "dme_policy_velocity",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("jurisdiction", sa.String(64), nullable=False),
        sa.Column("sector_isic", sa.String(8)),
        sa.Column("timestamp", sa.DateTime, nullable=False),
        sa.Column("carbon_price_velocity", sa.Float),
        sa.Column("regulatory_pipeline_velocity", sa.Float),
        sa.Column("enforcement_velocity", sa.Float),
        sa.Column("disclosure_mandate_velocity", sa.Float),
        sa.Column("composite_velocity", sa.Float),
        sa.Column("sector_weights", JSONB),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("jurisdiction", "sector_isic", "timestamp", name="uq_policy_velocity_ts"),
    )


def downgrade() -> None:
    tables = [
        "dme_policy_velocity", "dme_policy_events",
        "dme_nlp_pulse", "dme_nlp_signals",
        "dme_greenwash_signals", "dme_greenwash_watchlist",
        "dme_dmi_scores", "dme_dmi_config",
        "dme_alerts", "dme_alert_rules",
        "dme_contagion_simulations", "dme_contagion_events", "dme_contagion_network",
        "dme_velocity_timeseries", "dme_velocity_config",
    ]
    for t in tables:
        op.drop_table(t)
